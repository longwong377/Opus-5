#!/usr/bin/env bash
# PLAY THE STATION. Build a piece of Babylon 5 and stand in it.
#
# THIS IS THE THING THAT DID NOT EXIST. As of session 4d the station had 128
# walkable locations, 632,100 triangles of collision, 963 people walking in the
# corridors and a doorway a body opens by pressing a key -- and no way for a
# person to get in. `run/main_scene` pointed at a screenshot rig; the walkable
# build was reachable only from the headless gate, with six command-line
# arguments naming files that a fresh clone does not have because
# `station/generated/scene/` is gitignored. Walkable is not playable. This is
# the difference.
#
#   tools/play.sh                     # blue/0/0 -- the docking bays
#   tools/play.sh red/1/0             # somewhere else
#   tools/play.sh --z 6300 blue/0/0   # a particular z-cluster of that deck
#   tools/play.sh --shot out.png      # photograph it through the player's eye
#   tools/play.sh --verify            # the gate: is it actually playable?
#
# WASD or the arrows to walk, mouse to look, Shift to run, Space to jump, E to
# use what you are standing in front of, Esc to free the mouse, click to
# recapture it.
#
# Two environment facts, the same two tools/render_godot.sh is built on:
#
#   * Godot's --headless DISABLES rendering, so there are no frames at all
#     without a display. In this container that means xvfb-run.
#   * There is no GPU. Mesa lavapipe gives Vulkan 1.4 on the CPU -- correct
#     Forward+ with shadows and SSAO, at seconds per frame. Playable here means
#     "the build runs and a body stands in it", not "it runs at 60 fps here".
#     Framerate is gated numerically by station/budget.py against the target
#     hardware, never by this script.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DECK=""
Z=""
SHOT=""
VERIFY=0
RES="1280x720"
YAW=""
FRAMES="900"
FORCE_BUILD=0

while [ $# -gt 0 ]; do
  case "$1" in
    --z)      Z="$2"; shift 2 ;;
    --shot)   SHOT="$2"; shift 2 ;;
    --res)    RES="$2"; shift 2 ;;
    --yaw)    YAW="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    --verify) VERIFY=1; shift ;;
    --build)  FORCE_BUILD=1; shift ;;
    -h|--help) sed -n '2,31p' "$0"; exit 0 ;;
    *)        DECK="$1"; shift ;;
  esac
done

# WHERE THE ENGINE IS, asked of the code that already knows. `walkable.py` has
# resolved this since session 3v and a second copy here would be a second answer
# to drift from.
GODOT="${GODOT:-$(python3 -c 'import sys; sys.path.insert(0, "'"$ROOT"'/station"); import walkable; print(walkable.godot_binary() or "")')}"
if [ -z "$GODOT" ] || [ ! -x "$GODOT" ]; then
  echo "No double-precision Godot binary found." >&2
  echo "  bash tools/build_godot.sh     # ~61 min, see docs/godot-binary.md" >&2
  exit 1
fi

MANIFEST="$ROOT/godot/play.json"

# -- BUILD THE PIECE OF STATION --------------------------------------------
# Skipped when the manifest already describes the deck asked for AND its meshes
# are on disk, because assembling blue/0/0 is 36 s and a person launching the
# same deck twice should not pay it twice.
NEED_BUILD=$FORCE_BUILD
if [ ! -f "$MANIFEST" ]; then
  NEED_BUILD=1
else
  HAVE="$(python3 - "$MANIFEST" <<'PY'
import json, os, sys
try:
    m = json.load(open(sys.argv[1]))
except Exception:
    print("")
    raise SystemExit
glb = next((a.split("=", 1)[1] for a in m["args"] if a.startswith("--glb=")), "")
col = next((a.split("=", 1)[1] for a in m["args"] if a.startswith("--collision=")), "")
print(m.get("deck", "") if glb and col
      and os.path.exists(glb) and os.path.exists(col) else "")
PY
)"
  if [ -z "$HAVE" ]; then NEED_BUILD=1
  elif [ -n "$DECK" ] && [ "$HAVE" != "$DECK" ]; then NEED_BUILD=1
  fi
fi

if [ "$NEED_BUILD" = "1" ]; then
  echo "--- assembling ${DECK:-blue/0/0} ---"
  python3 "$ROOT/station/walkable.py" --build-only \
    ${DECK:+--deck "$DECK"} ${Z:+--z "$Z"} | tail -2
fi

export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json

# A CLEAN CHECKOUT PLAYS A DIFFERENT STATION, AND RETURNS 0. `godot/.godot/` is
# gitignored, so without an import pass every Texture2D ext_resource fails, every
# .tres that references one fails with it, and the build runs perfectly with
# every textured surface on the glTF fallback. Same trap tools/render_godot.sh
# documents, including that `--import` REWRITES project.godot -- so it is saved
# and put back.
if [ ! -d "$ROOT/godot/.godot/imported" ]; then
  echo "--- warming the texture import cache (first run in this checkout) ---"
  SAVED="$(mktemp)"
  cp "$ROOT/godot/project.godot" "$SAVED"
  xvfb-run -a --server-args="-screen 0 640x360x24" \
    "$GODOT" --path "$ROOT/godot" --import >/dev/null 2>&1 || true
  cp "$SAVED" "$ROOT/godot/project.godot"
  rm -f "$SAVED"
fi

# -- A PHOTOGRAPH THROUGH THE PLAYER'S OWN EYE ------------------------------
if [ -n "$SHOT" ]; then
  case "$SHOT" in /*) ;; *) SHOT="$ROOT/$SHOT" ;; esac
  echo "--- shot $RES -> $SHOT ---"
  xvfb-run -a --server-args="-screen 0 ${RES}x24" \
    "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan \
    --resolution "$RES" -- "--shot=$SHOT" ${YAW:+"--yaw=$YAW"} 2>&1 \
    | grep -Ev '^(WARNING: Leaked|     at: ~Dependency|ERROR: [0-9]+ RID alloc|WARNING: ObjectDB|     at: cleanup)'
  [ -f "$SHOT" ] || { echo "NO PNG WRITTEN -- the shot failed." >&2; exit 1; }
  exit 0
fi

# -- THE GATE: IS IT ACTUALLY PLAYABLE? -------------------------------------
#
# NO COMMAND-LINE ARGUMENTS AT ALL, which is exactly what pressing Play does.
# Everything the build needs has to come from `run/main_scene` and the manifest,
# because that is the configuration a person is in and every other one is a
# configuration only this repository is ever in.
#
# The claim is not "it started". `walk.gd::_play_report` prints where the body
# ended up, whether it is on a floor and how far the crowd has travelled, and
# all three are asserted -- a build that loads and drops the player through the
# deck prints exactly as much as one that works.
if [ "$VERIFY" = "1" ]; then
  LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
  echo "--- verify: launching with NO arguments, as a person would ---"
  set +e
  timeout 420 xvfb-run -a --server-args="-screen 0 640x360x24" \
    "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan \
    --resolution 640x360 >"$LOG" 2>&1
  set -e
  python3 "$ROOT/tools/play_verdict.py" "$LOG" || exit 1

  # THE NEGATIVE CONTROL. Take the manifest away and the same command must NOT
  # report a standing body -- otherwise the verdict above is being produced by
  # something other than the thing it claims to test, and the gate cannot fail.
  echo "--- control: the same launch with no manifest ---"
  mv "$MANIFEST" "$MANIFEST.held"
  set +e
  timeout 180 xvfb-run -a --server-args="-screen 0 640x360x24" \
    "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan \
    --resolution 640x360 >"$LOG.ctl" 2>&1
  set -e
  mv "$MANIFEST.held" "$MANIFEST"
  if python3 "$ROOT/tools/play_verdict.py" "$LOG.ctl" >/dev/null 2>&1; then
    echo "  FAIL  control PASSED -- the build stands somebody up with no" >&2
    echo "        manifest, so the verdict is not measuring the manifest." >&2
    rm -f "$LOG.ctl"; exit 1
  fi
  echo "        control: with no manifest there is nothing to play and no body."
  rm -f "$LOG.ctl"
  exit 0
fi

# -- PLAY IT ----------------------------------------------------------------
# On a machine with a display this opens a window. In this container it does
# not, so the run is bounded and its heartbeat is printed -- which is what
# --verify reads. A person on real hardware runs the same command without the
# timeout and closes the window when they are done.
echo "--- play ---"
if [ -n "${DISPLAY:-}" ]; then
  exec "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan --resolution "$RES"
fi
echo "(no DISPLAY: running under xvfb for $FRAMES frames, ~$((FRAMES / 60))s of station time)"
timeout 600 xvfb-run -a --server-args="-screen 0 ${RES}x24" \
  "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan --resolution "$RES" 2>&1 \
  | grep -Ev '^(WARNING: Leaked|     at: ~Dependency|ERROR: [0-9]+ RID alloc|WARNING: ObjectDB|     at: cleanup)' || true
