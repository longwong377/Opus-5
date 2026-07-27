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
JOBS="$(nproc)"

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
scons platform=linuxbsd \
      target=editor \
      precision=double \
      production=yes \
      debug_symbols=no \
      -j"${JOBS}"

BIN="$(find bin -maxdepth 1 -type f -name 'godot.linuxbsd.editor.double.*' | head -1)"
echo "=== built: ${BUILD_ROOT}/godot-${GODOT_VERSION}/${BIN} ==="
"$BIN" --version
