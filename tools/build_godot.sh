#!/usr/bin/env bash
# Build Godot 4 from source with double precision.
#
# No official double-precision binaries exist, and float32 jitters visibly at
# 8 km. This is a one-time ~40 minute cost on 4 cores; the resulting binary
# should be published as a GitHub Release asset so later sessions fetch it in
# seconds instead of rebuilding.
#
# Runs headless -- we render via Mesa lavapipe (Vulkan 1.4 on CPU), so no GPU
# and no display server is required at runtime.
set -euo pipefail

GODOT_VERSION="${GODOT_VERSION:-4.4-stable}"
BUILD_ROOT="${BUILD_ROOT:-/home/user/godot-build}"
# Godot's thirdparty C++ peaks at multiple GB per compiler process. With 4
# cores and 15 GB the build was killed part-way through with no error in the
# log -- the signature of the OOM killer, not a compile failure. Leave a core
# free and cap parallelism.
JOBS="${JOBS:-2}"

echo "=== Godot ${GODOT_VERSION}, double precision, ${JOBS} jobs ==="

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
# tarball cannot be fetched with curl. git is proxied correctly, so clone instead.
if [ ! -d "godot-${GODOT_VERSION}" ]; then
  echo "--- fetching source (shallow clone; archive URLs are proxy-blocked) ---"
  git clone --depth 1 --branch "${GODOT_VERSION}" --quiet \
    https://github.com/godotengine/godot.git "godot-${GODOT_VERSION}"
fi

cd "godot-${GODOT_VERSION}"

# target=editor gives us a binary that can also run projects headlessly and
# import resources, which the offline pipeline needs.
echo "--- building (this is the slow part) ---"
# production=yes turns on LTO, whose link step needs far more memory than this
# container has. We need a correct double-precision binary for offscreen
# rendering, not a fast one, so LTO is off.
scons platform=linuxbsd \
      target=editor \
      precision=double \
      lto=none \
      debug_symbols=no \
      optimize=speed \
      -j"${JOBS}"

BIN="$(find bin -maxdepth 1 -type f -name 'godot.linuxbsd.editor.double.*' | head -1)"
echo "=== built: ${BUILD_ROOT}/godot-${GODOT_VERSION}/${BIN} ==="
"$BIN" --version
