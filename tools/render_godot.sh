#!/usr/bin/env bash
# Render one shot in Godot, offscreen, with no GPU and no display, to a PNG.
#
# This is the engine half of the verification loop. tools/preview_render.py is
# the fast path and answers questions about proportion and silhouette;
# this answers questions about material, light, exposure and mood, which are
# the questions a software rasteriser written in Python cannot.
#
# Two environment facts drive the whole script and both are counter-intuitive:
#
#   * Godot's --headless DISABLES rendering. It is a null rendering driver, so
#     a headless run produces no frames at all. A virtual display is required,
#     hence xvfb-run. This cost a session to discover once; it is written down
#     here so it does not cost another.
#   * There is no GPU. Mesa lavapipe provides Vulkan 1.4 on the CPU, selected
#     by pointing VK_ICD_FILENAMES at its ICD. Godot then reports
#     "Vulkan 1.4.x - Forward+ - llvmpipe" and does real Forward+ rendering,
#     including shadows, SSAO and glow, at seconds to minutes per frame.
#
# Examples:
#
#   tools/render_godot.sh --shot exterior --orbit 9200,18,214 --res 1280x720 \
#       --out docs/engine-exterior.png
#
#   tools/render_godot.sh --shot drum --stand 20,4700 --look 20,6300 \
#       --res 1280x720 --out docs/engine-drum.png
#
# Everything after --shot is passed through to tools/export_scene.py, which
# decides what geometry the shot contains and where the lights go. Run
# `python3 tools/export_scene.py --help` for the full set.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Binary location, in order of preference: explicit override, the standard
# build path, then anything a rebuild left lying around. Missing it is a
# hard error with the one command that fixes it, because the failure mode
# otherwise is xvfb-run reporting a missing file and burying the cause.
GODOT="${GODOT:-}"
if [ -z "$GODOT" ]; then
  for cand in \
    "/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64" \
    "$(ls -1 /home/user/godot-build/*/bin/godot.linuxbsd.*.double.* 2>/dev/null | head -1)"
  do
    if [ -n "$cand" ] && [ -x "$cand" ]; then GODOT="$cand"; break; fi
  done
fi
if [ -z "$GODOT" ] || [ ! -x "$GODOT" ]; then
  echo "No double-precision Godot binary found." >&2
  echo "  bash tools/build_godot.sh     # ~61 min, see docs/godot-binary.md" >&2
  exit 1
fi

RES="1280x720"
OUT=""
SHOT="exterior"
EXPORT=1
QUALITY="high"
WARMUP=""
LIGHT_GAIN=""
TIMEOUT="${TIMEOUT:-3600}"
PASS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --shot)       SHOT="$2"; shift 2 ;;
    --res)        RES="$2"; shift 2 ;;
    --out)        OUT="$2"; shift 2 ;;
    --quality)    QUALITY="$2"; shift 2 ;;
    --warmup)     WARMUP="$2"; shift 2 ;;
    --light-gain) LIGHT_GAIN="$2"; shift 2 ;;
    --no-export)  EXPORT=0; shift ;;
    -h|--help)    sed -n '2,32p' "$0"; exit 0 ;;
    # Anything else belongs to the exporter: --eye, --target, --stand, --look,
    # --orbit, --fov, --lights-per-run, --shadow-lights, --trams, ...
    *)            PASS+=("$1"); shift ;;
  esac
done

if [ -z "$OUT" ]; then
  echo "--out PATH is required" >&2
  exit 1
fi
case "$OUT" in /*) ;; *) OUT="$ROOT/$OUT" ;; esac

SCENE_JSON="$ROOT/station/generated/scene/${SHOT}/scene.json"

if [ "$EXPORT" = "1" ]; then
  echo "--- assemble ---"
  python3 "$ROOT/tools/export_scene.py" --shot "$SHOT" --out "$OUT" \
    ${PASS[@]+"${PASS[@]}"}
elif [ ! -f "$SCENE_JSON" ]; then
  echo "--no-export given but $SCENE_JSON does not exist" >&2
  exit 1
fi

SCENE_PATH="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["scene"])' "$SCENE_JSON")"

# A .tres whose first line is not "[" does not parse, and Godot's failure mode
# is quiet: the resource fails to load, the ExtResource in the scene resolves
# to null, every surface falls back to the glTF default, and the render comes
# out plain white. That is indistinguishable from an exposure mistake, and one
# 8 km hull was rendered as a featureless white shape before the cause was
# found in the engine log rather than in the picture. Godot's text resource
# format has no comment syntax -- a leading "#" is parsed as an HTML colour --
# so a generator that writes a provenance header produces a file that silently
# does nothing.
BAD_TRES=""
for f in "$ROOT"/godot/materials/*.tres; do
  [ -e "$f" ] || continue
  case "$(head -c 1 "$f")" in
    "[") ;;
    *) BAD_TRES="${BAD_TRES} $(basename "$f")" ;;
  esac
done
if [ -n "$BAD_TRES" ]; then
  echo "REFUSING TO RENDER -- these materials do not parse (first line must" >&2
  echo "be the [gd_resource] header; .tres has no comment syntax):" >&2
  echo "  ${BAD_TRES}" >&2
  echo "Rendering anyway would produce a white frame that looks like a" >&2
  echo "lighting bug. Fix the generator that writes them." >&2
  exit 2
fi

USER_ARGS=("--scene-json=$SCENE_JSON" "--out=$OUT")
[ -n "$WARMUP" ] && USER_ARGS+=("--warmup=$WARMUP")
[ -n "$LIGHT_GAIN" ] && USER_ARGS+=("--light-gain=$LIGHT_GAIN")
# The screen-space passes are the expensive part on a CPU rasteriser and they
# are the first thing to drop when the question is "did the geometry arrive",
# not "does it look right".
[ "$QUALITY" = "low" ] && USER_ARGS+=("--no-ssao")

echo "--- render $SHOT $RES -> $OUT ---"
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json
# Software rasterisation of a 250k-triangle scene with shadow maps is memory
# hungry and llvmpipe defaults its thread count to nproc; leaving it alone has
# been fine, but the frame budget is time, not framerate, so nothing here is
# tuned for speed at the cost of correctness.
START=$(date +%s)
set +e
timeout "$TIMEOUT" xvfb-run -a --server-args="-screen 0 ${RES}x24" \
  "$GODOT" --path "$ROOT/godot" \
  --rendering-driver vulkan \
  --resolution "$RES" \
  "$SCENE_PATH" \
  -- "${USER_ARGS[@]}" 2>&1 \
  | grep -Ev '^(WARNING: Leaked|     at: ~Dependency|ERROR: [0-9]+ RID alloc|WARNING: ObjectDB|     at: cleanup)'
RC=${PIPESTATUS[0]}
set -e
echo "--- ${SHOT} finished in $(( $(date +%s) - START ))s (exit ${RC}) ---"

if [ ! -f "$OUT" ]; then
  echo "NO PNG WRITTEN -- the render failed. Do not report a render." >&2
  exit 1
fi
ls -l "$OUT"
