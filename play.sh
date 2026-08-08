#!/usr/bin/env bash
# PLAY IT. One command, from a fresh clone to standing on the transport deck.
#
#     ./play.sh
#
# There are three things between a clone and a title screen, and this script
# does all three so nobody has to know them:
#
#   1. THE ENGINE. Stock Godot 4.4 runs this -- see the correction in PLAY.md;
#      the double-precision claim this project carried for months was never
#      tested and is wrong. A double build is vendored for linux x86_64 and is
#      what this script uses because it is already here, not because it is
#      needed. On any other platform: install Godot 4.4 normally and run
#      `python tools/build_world.py`, then open `godot/` and press play.
#
#   2. THE WORLD IS GENERATED, NOT COMMITTED. 6.2 GB of meshes, collision,
#      streaming cells, crowd bodies and audio come out of `station/*.py`.
#      They are far too large for git, so the first run builds them -- call it
#      45 minutes -- and every run after that skips it.
#
#   3. THE WORLD LIVES OUTSIDE THE PACK. The engine reads it from disk at
#      runtime, so `game/` and `station/` have to stay together.
#
# Flags:
#   --rebuild    rebuild the world even if it is already on disk
#   --check      do everything except launch, then report (used by CI)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

ENGINE_DIR="$HERE/.engine"
ARCHIVE="godot-4.4-stable-double-linuxbsd-x86_64.tar.xz"
WORLD_MARK="station/generated/scene/station/cells/station_cells.json"
REBUILD=0; CHECK=0
for a in "$@"; do
  case "$a" in
    --rebuild) REBUILD=1 ;;
    --check)   CHECK=1 ;;
    *) echo "unknown flag: $a"; exit 2 ;;
  esac
done

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- 1. platform
say "1/4  platform"
OS="$(uname -s)"; ARCH="$(uname -m)"
echo "    $OS $ARCH"
if [ "$OS" != "Linux" ] || [ "$ARCH" != "x86_64" ]; then
  cat <<PLATFORMS

    The engine vendored here is linux x86_64 and this is not that -- but you
    do NOT need to compile anything. Stock Godot 4.4 runs this project; the
    double-precision requirement was never tested and is wrong (PLAY.md).

        1. install Godot 4.4 from godotengine.org  (the normal build)
        2. pip install -r requirements.txt
        3. python tools/build_world.py            (~45 min, once)
        4. open the `godot/` folder in Godot and press play

    Or, if you would rather this script drove it:

        GODOT=/path/to/godot ./play.sh

PLATFORMS
  if [ -z "${GODOT:-}" ]; then exit 1; fi
  echo "    using GODOT=$GODOT"
fi

# ------------------------------------------------------------------ 2. engine
say "2/4  engine"
if [ -n "${GODOT:-}" ] && [ -x "${GODOT:-}" ]; then
  ENGINE="$GODOT"
  echo "    supplied: $ENGINE"
else
  ENGINE="$(find "$ENGINE_DIR" -maxdepth 1 -type f -executable 2>/dev/null | head -1 || true)"
  if [ -z "$ENGINE" ]; then
    echo "    extracting $ARCHIVE"
    ( cd vendor/godot && sha256sum -c "$ARCHIVE.sha256" ) || {
      echo "    CHECKSUM FAILED -- the vendored engine is not what it should be"; exit 1; }
    mkdir -p "$ENGINE_DIR"
    tar -xJf "vendor/godot/$ARCHIVE" -C "$ENGINE_DIR"
    ENGINE="$(find "$ENGINE_DIR" -maxdepth 1 -type f -executable | head -1)"
  fi
  echo "    $ENGINE"
fi
"$ENGINE" --version 2>/dev/null | tail -1 | sed 's/^/    /'

# ------------------------------------------------------------------- 3. world
say "3/4  world"
if [ "$REBUILD" = 1 ] || [ ! -f "$WORLD_MARK" ]; then
  echo "    building -- this is the 45 minutes, and only the first run pays it"
  GODOT="$ENGINE" bash tools/build_world.sh
else
  cells="$(python3 -c "import json;print(len(json.load(open('$WORLD_MARK'))['cells']))" 2>/dev/null || echo '?')"
  echo "    already built: $cells streaming cells"
  echo "    (--rebuild to redo it)"
fi

# ------------------------------------------------------------------ 4. launch
say "4/4  launch"
if [ "$CHECK" = 1 ]; then
  echo "    --check: everything is in place, not launching"
  exit 0
fi
echo "    NEW GAME puts you on the transport deck at customs."
echo
exec "$ENGINE" --path godot
