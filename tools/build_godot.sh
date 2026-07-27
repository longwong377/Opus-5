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
#   2. If GODOT_URL (or tools/godot-binary.url) names a prebuilt archive,
#      fetch and verify it against tools/godot-binary.sha256 and stop. This is
#      the path that makes the cost go away permanently, and it is wired up and
#      waiting: see "Publishing" below for why no URL is recorded yet.
#   3. Otherwise build from source.
#
#   bash tools/build_godot.sh              # get a binary by whatever means
#   bash tools/build_godot.sh --check      # report only, exit 1 if absent
#   bash tools/build_godot.sh --package    # strip + xz the binary for upload
#   FORCE=1 bash tools/build_godot.sh      # rebuild even if one exists
#
# Publishing. The right home for the artifact is a GitHub Release asset. As of
# this writing that cannot be done from inside a session: api.github.com
# answers 403 "GitHub access is not enabled for this session. An org admin must
# connect the Claude GitHub App for this organization.", there is no `gh` CLI,
# and the GitHub MCP tools expose no release-creation call. --package therefore
# produces exactly the file that needs uploading, plus its checksum, and prints
# the two commands that finish the job. Once the asset exists, write its URL
# into tools/godot-binary.url and its sha256 into tools/godot-binary.sha256 and
# every future session gets the binary in seconds with no code change.
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

# --- 2. prebuilt archive? -------------------------------------------------
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

# --- 3. build -------------------------------------------------------------
echo "=== Godot ${GODOT_VERSION}, double precision, ${JOBS} jobs ==="
echo "    expect roughly 60 minutes; the script is resumable, scons picks up"
echo "    from existing object files if it is interrupted."

echo "--- deps ---"
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq \
  scons pkg-config gcc g++ \
  libx11-dev libxcursor-dev libxinerama-dev libxi-dev libxrandr-dev \
  libgl1-mesa-dev libglu1-mesa-dev \
  libasound2-dev libpulse-dev libudev-dev \
  libwayland-dev wayland-protocols libdbus-1-dev \
  >/dev/null 2>&1

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
