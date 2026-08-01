#!/usr/bin/env bash
# Obtain Godot 4 with double precision: fetch a prebuilt one if we can, and
# build from source if we cannot.
#
# No official double-precision binaries exist -- see docs/adr/0001-engine-choice.md
# -- and float32 spacing reaches 3.9 mm at the Starfury's 50 km flight range, so
# the engine has to be built. That build is ~60 minutes, and the container it
# lands in is ephemeral. Paying an hour every session is the largest fixed cost
# in the project, so this script now does three things in order:
#
#   1. If a working double-precision binary is already here, do NOTHING. The
#      previous version rebuilt unconditionally, which meant a session that
#      already had the binary could still lose an hour to it.
#   2. If `vendor/godot/` in this repository carries the archive, unpack it.
#      This is the path that actually makes the cost go away today: the
#      container clones this repo at session start, so the artifact arrives
#      with the code and unpacking it takes seconds.
#   3. If GODOT_URL (or tools/godot-binary.url) names a prebuilt archive, fetch
#      and verify it against tools/godot-binary.sha256. Preferred over 2 if
#      both exist, because a release asset costs the repository nothing.
#   4. Otherwise build from source.
#
#   bash tools/build_godot.sh              # get a binary by whatever means
#   bash tools/build_godot.sh --check      # report only, exit 1 if absent
#   bash tools/build_godot.sh --package    # strip + xz the binary for upload
#   FORCE=1 bash tools/build_godot.sh      # rebuild even if one exists
#
# Publishing. The right home for the artifact is still a GitHub Release asset,
# and a session still cannot create one -- re-measured in 4d: api.github.com is
# 403, there is no `gh` CLI, and the GitHub MCP server's release calls are all
# reads. What 4d DID establish is the half that matters: **downloading a
# release asset through the agent proxy works** (HTTP 200 on a 102 MB Godot
# asset, via release-assets.githubusercontent.com). The earlier note that
# GitHub downloads were proxy-blocked is true only of archive/codeload paths.
#
# So the fetch path is proven and only the upload is missing. Until somebody
# with GitHub access runs the two commands --package prints, the artifact is
# vendored in this repository instead, which needs no external permission at
# all. See step 2.
set -euo pipefail

GODOT_VERSION="${GODOT_VERSION:-4.4-stable}"
BUILD_ROOT="${BUILD_ROOT:-/home/user/godot-build}"
SRC="${BUILD_ROOT}/godot-${GODOT_VERSION}"
BIN_DIR="${SRC}/bin"
DIST="${BUILD_ROOT}/dist"
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="godot-${GODOT_VERSION}-double-linuxbsd-x86_64.tar.xz"

# Godot's thirdparty C++ peaks at multiple GB per compiler process. With 4
# cores and 15 GB the first attempt at -j4 was killed part-way through with no
# error in the log at all -- the OOM killer's signature, not a compile failure.
# Leave cores free and cap parallelism.
JOBS="${JOBS:-2}"

find_binary() {
  # Any double-precision binary under the build root will do. The name carries
  # `double` only when precision=double was actually used, so this doubles as a
  # check that the binary is the right kind.
  ls -1 "${BUILD_ROOT}"/*/bin/godot.linuxbsd.*.double.* 2>/dev/null | head -1
}

verify_binary() {
  # Runs it. A binary that exists and does not execute -- half-written by an
  # interrupted link, or built for the wrong libc -- is worse than none,
  # because everything downstream reports a confusing failure instead of a
  # missing prerequisite.
  local b="$1"
  [ -x "$b" ] || return 1
  "$b" --version >/dev/null 2>&1 || return 1
  return 0
}

case "${1:-}" in
  --check)
    B="$(find_binary || true)"
    if [ -n "$B" ] && verify_binary "$B"; then
      echo "ok: $B  ($("$B" --version))"
      exit 0
    fi
    echo "absent: no working double-precision Godot under ${BUILD_ROOT}"
    exit 1
    ;;
  --package)
    B="$(find_binary || true)"
    if [ -z "$B" ] || ! verify_binary "$B"; then
      echo "nothing to package -- build first" >&2
      exit 1
    fi
    mkdir -p "$DIST"
    cp "$B" "$DIST/$(basename "$B")"
    # Debug symbols are already off in the build, but the editor binary still
    # carries a large symbol table; stripping is worth roughly a third.
    strip --strip-unneeded "$DIST/$(basename "$B")"
    (cd "$DIST" && tar -cf - "$(basename "$B")" | xz -9 -T0 > "$ARCHIVE"
     sha256sum "$ARCHIVE" > "${ARCHIVE}.sha256")
    echo "packaged: ${DIST}/${ARCHIVE}"
    ls -l "${DIST}/${ARCHIVE}"
    cat "${DIST}/${ARCHIVE}.sha256"
    cat <<EOF

To finish publishing (needs GitHub access this session does not have):

  gh release create godot-${GODOT_VERSION}-double \\
     "${DIST}/${ARCHIVE}" --notes "Godot ${GODOT_VERSION}, precision=double, linuxbsd x86_64"
  # then record the asset URL and checksum so this script stops building:
  echo '<asset url>' > ${TOOLS}/godot-binary.url
  cut -d' ' -f1 "${DIST}/${ARCHIVE}.sha256" > ${TOOLS}/godot-binary.sha256
EOF
    exit 0
    ;;
  --vendor)
    # Package, then put the archive where step 2 will find it. This is the
    # command that actually ends the 60-minute tax, because its output goes
    # into the repository and the repository is what the next container gets.
    "$0" --package
    V="$(cd "${TOOLS}/.." && pwd)/vendor/godot"
    mkdir -p "$V"
    cp "${DIST}/${ARCHIVE}" "${DIST}/${ARCHIVE}.sha256" "$V/"
    echo
    echo "vendored into ${V}:"
    ls -l "$V"
    echo "commit it, and the next container unpacks in seconds."
    exit 0
    ;;
esac

# --- 1. already have one? -------------------------------------------------
if [ -z "${FORCE:-}" ]; then
  B="$(find_binary || true)"
  if [ -n "$B" ] && verify_binary "$B"; then
    echo "=== already present: $B ==="
    "$B" --version
    exit 0
  fi
fi

# --- 2. a copy vendored in this repository? -------------------------------
# THE ONLY DURABLE STORE A SESSION CAN ACTUALLY WRITE TO. The right home for
# this artifact is a GitHub Release asset and that has not changed -- but
# measured in session 4d, nothing in a session can create one: api.github.com
# answers 403 ("GitHub access is not enabled for this session"), there is no
# `gh` CLI, and the GitHub MCP server exposes `get_latest_release`,
# `get_release_by_tag` and `list_releases` and no call that writes. The git
# remote, by contrast, is proxied and writable -- it is how every commit gets
# out.
#
# So the artifact lives in the repository until somebody with GitHub access
# moves it. The container clones this repo at session start, so a vendored copy
# costs NOTHING extra to fetch: it arrives with the code, and this step is a
# local `tar -xJf`. That is the whole 60 minutes, gone, with no manual step.
#
# The cost is honest and worth stating: ~50 MB in git history, permanently,
# because history cannot be rewritten. It buys back an hour per container on a
# project whose container is reclaimed regularly. If the asset is ever
# published properly, write its URL into tools/godot-binary.url -- step 3 runs
# first and wins -- and delete `vendor/godot/`; the history cost is already
# paid either way.
#
# NOTE the checksum is checked here too. A truncated 50 MB blob that extracts
# to a broken ELF is the failure that would otherwise present as "the renderer
# is mysteriously wrong".
VENDORED="$(cd "${TOOLS}/.." && pwd)/vendor/godot/${ARCHIVE}"
if [ -f "$VENDORED" ]; then
  echo "=== using the copy vendored in this repository ==="
  if [ -f "${VENDORED}.sha256" ]; then
    want="$(cut -d' ' -f1 < "${VENDORED}.sha256" | tr -d '[:space:]')"
    got="$(sha256sum "$VENDORED" | cut -d' ' -f1)"
    if [ "$want" != "$got" ]; then
      echo "vendored archive checksum mismatch: want $want got $got" >&2
      VENDORED=""
    fi
  fi
  if [ -n "$VENDORED" ]; then
    mkdir -p "$BIN_DIR"
    tar -xJf "$VENDORED" -C "$BIN_DIR"
    chmod +x "${BIN_DIR}"/godot.linuxbsd.*.double.* || true
    B="$(find_binary || true)"
    if [ -n "$B" ] && verify_binary "$B"; then
      echo "=== unpacked: $B ==="
      "$B" --version
      exit 0
    fi
    echo "vendored archive did not yield a working binary -- continuing" >&2
  fi
fi

# --- 3. prebuilt archive at a URL? ----------------------------------------
URL="${GODOT_URL:-}"
if [ -z "$URL" ] && [ -f "${TOOLS}/godot-binary.url" ]; then
  URL="$(tr -d '[:space:]' < "${TOOLS}/godot-binary.url")"
fi
if [ -n "$URL" ]; then
  echo "=== fetching prebuilt: $URL ==="
  mkdir -p "$DIST" "$BIN_DIR"
  if curl -fsSL "$URL" -o "${DIST}/${ARCHIVE}"; then
    if [ -f "${TOOLS}/godot-binary.sha256" ]; then
      want="$(tr -d '[:space:]' < "${TOOLS}/godot-binary.sha256")"
      got="$(sha256sum "${DIST}/${ARCHIVE}" | cut -d' ' -f1)"
      if [ "$want" != "$got" ]; then
        echo "checksum mismatch: want $want got $got -- falling through to build" >&2
        rm -f "${DIST}/${ARCHIVE}"
      fi
    fi
    if [ -f "${DIST}/${ARCHIVE}" ]; then
      tar -xJf "${DIST}/${ARCHIVE}" -C "$BIN_DIR"
      chmod +x "${BIN_DIR}"/godot.linuxbsd.*.double.* || true
      B="$(find_binary || true)"
      if [ -n "$B" ] && verify_binary "$B"; then
        echo "=== fetched: $B ==="
        "$B" --version
        exit 0
      fi
      echo "fetched archive did not yield a working binary -- building" >&2
    fi
  else
    echo "fetch failed -- building from source" >&2
  fi
fi

# --- 4. build -------------------------------------------------------------
echo "=== Godot ${GODOT_VERSION}, double precision, ${JOBS} jobs ==="
echo "    expect roughly 60 minutes; the script is resumable, scons picks up"
echo "    from existing object files if it is interrupted."

echo "--- deps ---"
export DEBIAN_FRONTEND=noninteractive
# `apt-get update` FIRST, and its failure is not fatal. A fresh container has no
# package lists at all, so `install` exits 100 before fetching anything -- which
# is how this script died 8 seconds into a 60-minute job with its own output
# redirected to /dev/null and no diagnosis in the log. And `update` itself
# partially fails here every time: two third-party PPAs in the image
# (deadsnakes, ondrej/php) are 403 through the agent proxy, which is a warning
# about repositories this build needs nothing from.
apt-get update -qq >/dev/null 2>&1 || true
if ! apt-get install -y -qq \
    scons pkg-config gcc g++ \
    libx11-dev libxcursor-dev libxinerama-dev libxi-dev libxrandr-dev \
    libgl1-mesa-dev libglu1-mesa-dev \
    libasound2-dev libpulse-dev libudev-dev \
    libwayland-dev wayland-protocols libdbus-1-dev; then
  echo "dependency install failed -- see the apt output above" >&2
  exit 1
fi

mkdir -p "$BUILD_ROOT"
cd "$BUILD_ROOT"

# The agent proxy returns 403 for GitHub archive/codeload paths, so the source
# tarball cannot be fetched with curl. git is proxied correctly, so clone.
if [ ! -d "$SRC" ]; then
  echo "--- fetching source (shallow clone; archive URLs are proxy-blocked) ---"
  git clone --depth 1 --branch "${GODOT_VERSION}" --quiet \
    https://github.com/godotengine/godot.git "$SRC"
fi

cd "$SRC"

# target=editor gives a binary that can also run a project from loose files.
# That matters: an export-template build cannot, and the whole render pipeline
# runs project directories rather than exported .pck files.
echo "--- building (this is the slow part) ---"
# production=yes turns on LTO, whose link step needs far more memory than this
# container has. We need a correct double-precision binary for offscreen
# rendering, not a fast one, so LTO is off.
#
# A SCons cache makes an interrupted-and-resumed build cheap within one
# container. It does nothing across containers -- nothing does, which is what
# the fetch path above is for.
scons platform=linuxbsd \
      target=editor \
      precision=double \
      lto=none \
      debug_symbols=no \
      optimize=speed \
      cache_path="${BUILD_ROOT}/.scons-cache" \
      -j"${JOBS}"

B="$(find_binary || true)"
if [ -z "$B" ] || ! verify_binary "$B"; then
  echo "build finished but produced no working binary" >&2
  exit 1
fi
echo "=== built: $B ==="
"$B" --version
echo
echo "This binary is container-local. Run 'bash tools/build_godot.sh --package'"
echo "and publish the result so the next session does not rebuild it."
