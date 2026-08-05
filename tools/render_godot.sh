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
#   # THE BUILD A PLAYER STANDS IN: one assembled deck, lit by its own tagged
#   # fittings, from the shipped player camera. `--at` is a gazetteer place key
#   # and the eye stands at its angle on the corridor floor; `--face` aims at
#   # another one. There are no world coordinates in a deck command.
#   tools/render_godot.sh --shot deck --deck blue/0/0 --at docking_bays \
#       --res 1280x720 --out docs/engine-deck-corridor.png
#   tools/render_godot.sh --shot deck --at docking_bays --at-offset 6,0 \
#       --face docking_bays --res 1280x720 --out docs/engine-deck-door.png
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
# Flags that belong to `render_shot.gd` rather than to the exporter. Anything
# unrecognised below falls through to `export_scene.py`, whose argparse rejects
# it -- so a renderer-side flag that is not named here cannot be reached at all.
# The vista negative control had to be run by moving
# `station/generated/scene/vista/cnc.json` aside instead, which works and is
# clumsy, and a control that awkward is a control that stops being run.
VISTA_ARGS=()
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
    --no-vista)   VISTA_ARGS+=("--no-vista"); shift ;;
    --vista-gain) VISTA_ARGS+=("--vista-gain=$2"); shift 2 ;;
    --vista-phase) VISTA_ARGS+=("--vista-phase=$2"); shift 2 ;;
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
USER_ARGS+=(${VISTA_ARGS[@]+"${VISTA_ARGS[@]}"})
# The screen-space passes are the expensive part on a CPU rasteriser and they
# are the first thing to drop when the question is "did the geometry arrive",
# not "does it look right".
[ "$QUALITY" = "low" ] && USER_ARGS+=("--no-ssao")

export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json

# THE SILENT FALLBACK THAT INVALIDATED A WHOLE SESSION'S VISUAL WORK.
#
# Session 4e ran in a container with NO `/usr/share/vulkan/icd.d` at all --
# `mesa-vulkan-drivers` is not in the base image and nothing installs it. Godot
# does not stop for that. It prints
#
#     ERROR: Required extension VK_KHR_surface not found.
#     WARNING: Your video card drivers seem not to support the required Vulkan
#              version, switching to OpenGL 3.
#
# in the middle of several hundred lines of ALSA noise, renders in **OpenGL 3
# Compatibility**, and exits 0 with a PNG. Compatibility has no Forward+: no
# SSAO, no glow, no SSIL, no volumetric fog, no adjustment. So every frame
# looked flat and grey, and A/B tests of ssil_enabled and
# volumetric_fog_enabled came back BYTE-IDENTICAL -- which was recorded as
# "lavapipe does not run it" and was nothing of the kind. The features were not
# off; the renderer was.
#
# So the ICD is checked BEFORE the run, and the fallback warning is treated as
# fatal AFTER it. A render that quietly changes renderer is worse than a render
# that fails, because it produces evidence.
if [ ! -r "$VK_ICD_FILENAMES" ]; then
  cat >&2 <<EOF
render_godot.sh: no Vulkan ICD at $VK_ICD_FILENAMES

  Godot would fall back to OpenGL 3 Compatibility, which has NO Forward+ --
  no SSAO, glow, SSIL, volumetric fog or colour adjustment -- render a flat
  grey frame, and exit 0. Every craft judgement taken from it would be wrong.

  Fix:  apt-get update && apt-get install -y mesa-vulkan-drivers
EOF
  exit 2
fi

# A CLEAN CHECKOUT RENDERS A DIFFERENT PICTURE, AND RETURNS 0. This is F-13 in
# docs/craft-review-3t.md, closed here. `godot/.godot/` is gitignored, so on a
# fresh clone or a fresh `git worktree` the TEXTURE IMPORT CACHE is absent;
# every Texture2D ext_resource fails, every .tres that references one fails with
# it, and Godot reports "Parse Error: [ext_resource] referenced non-existent
# resource". It then renders the scene with those groups on the fallback
# material and writes a perfectly good PNG. Measured in this worktree: the deck
# shot came back with the corridor's wall plate, deck plate and every textured
# surface flat -- a frame anyone would have scored, and not the frame.
#
# THE REPAIR HAS A TRAP IN IT and that is why this is eight lines rather than
# one. `godot --path godot --import` REWRITES project.godot, replacing its
# header -- the three lines recording that the engine must be the
# double-precision build, with the ADR reference -- with Godot's own
# boilerplate: 16 insertions, 27 deletions, silently. So the file is saved and
# put back. Verified by `git diff --stat godot/project.godot` returning empty
# afterwards.
if [ ! -d "$ROOT/godot/.godot/imported" ]; then
  echo "--- warming the texture import cache (first render in this checkout) ---"
  SAVED_PROJECT="$(mktemp)"
  cp "$ROOT/godot/project.godot" "$SAVED_PROJECT"
  xvfb-run -a --server-args="-screen 0 640x360x24" \
    "$GODOT" --path "$ROOT/godot" --import >/dev/null 2>&1 || true
  cp "$SAVED_PROJECT" "$ROOT/godot/project.godot"
  rm -f "$SAVED_PROJECT"
  if [ ! -d "$ROOT/godot/.godot/imported" ]; then
    echo "IMPORT PASS PRODUCED NO CACHE -- every textured material would render" >&2
    echo "on the fallback and the frame would look merely disappointing." >&2
    exit 4
  fi
fi

echo "--- render $SHOT $RES -> $OUT ---"
# Software rasterisation of a 250k-triangle scene with shadow maps is memory
# hungry and llvmpipe defaults its thread count to nproc; leaving it alone has
# been fine, but the frame budget is time, not framerate, so nothing here is
# tuned for speed at the cost of correctness.
START=$(date +%s)
LOGFILE="$(mktemp)"
trap 'rm -f "$LOGFILE"' EXIT
set +e
timeout "$TIMEOUT" xvfb-run -a --server-args="-screen 0 ${RES}x24" \
  "$GODOT" --path "$ROOT/godot" \
  --rendering-driver vulkan \
  --resolution "$RES" \
  "$SCENE_PATH" \
  -- "${USER_ARGS[@]}" 2>&1 \
  | tee "$LOGFILE" \
  | grep -Ev '^(WARNING: Leaked|     at: ~Dependency|ERROR: [0-9]+ RID alloc|WARNING: ObjectDB|     at: cleanup)'
RC=${PIPESTATUS[0]}
set -e
echo "--- ${SHOT} finished in $(( $(date +%s) - START ))s (exit ${RC}) ---"

# ...AND THE SAME CHECK FROM THE OTHER END. The ICD can be present and Godot
# can still fall back -- a broken driver, a missing extension, an ICD for
# hardware that is not here. The only authority on which renderer ran is what
# Godot itself printed, so that is what is read. Session 4e drew every one of
# its visual conclusions from ten frames carrying this warning.
if grep -q "switching to OpenGL 3" "$LOGFILE"; then
  echo >&2
  echo "RENDERER FELL BACK TO OPENGL 3 COMPATIBILITY -- this frame is NOT" >&2
  echo "evidence about craft. Compatibility has no Forward+: no SSAO, glow," >&2
  echo "SSIL, volumetric fog or colour adjustment. Godot said:" >&2
  grep -E "Required extension|switching to OpenGL 3" "$LOGFILE" | sed 's/^/  /' >&2
  echo "  fix: apt-get install -y mesa-vulkan-drivers" >&2
  rm -f "$OUT"
  exit 3
fi
# And the positive form, so a passing run SAYS which renderer it used rather
# than leaving it to be inferred from an absence.
grep -m1 -E "Vulkan [0-9.]+ - Forward\+" "$LOGFILE" | sed 's/^/renderer: /' \
  || { echo "renderer: could not confirm Forward+ from the log" >&2; exit 3; }

if [ ! -f "$OUT" ]; then
  echo "NO PNG WRITTEN -- the render failed. Do not report a render." >&2
  exit 1
fi

# A SHADER THAT FAILS TO COMPILE STILL RENDERS. Godot logs "SHADER ERROR",
# falls back, and hands back a perfectly valid PNG of the wrong thing -- the
# frame looks merely disappointing rather than broken, and the disappointment
# gets attributed to the material instead of to a typo. It cost one render
# round here: `const float TAU` redefined a Godot built-in, the run reported
# `exit 0`, and the PNG was the fallback material.
#
# There is no way to compile-check a shader without the engine, so the engine's
# own complaint is the check.
if grep -qE '^(SHADER ERROR|ERROR: Shader compilation failed)' "$LOGFILE"; then
  echo "SHADER FAILED TO COMPILE -- the PNG is the fallback material, not the" >&2
  echo "material you meant. Do not score this frame." >&2
  grep -E '^(SHADER ERROR|ERROR: Shader compilation failed)' "$LOGFILE" >&2
  exit 3
fi

# AND THE SAME OUTCOME BY THE OTHER ROUTE. The two checks above exist because
# "the frame looks merely disappointing rather than broken" and the
# disappointment gets blamed on the material. A .tres that PARSES but whose
# textures failed to import produces exactly that, and neither check sees it:
# the file's first byte is "[", and no shader is involved. The warm-up above
# handles the empty-cache case; this catches a cache that is present and STALE,
# which is what a newly generated texture looks like until the next import.
if grep -q 'Parse Error: \[ext_resource\]' "$LOGFILE"; then
  echo "MATERIALS FAILED TO LOAD -- their textures are not imported, so those" >&2
  echo "surfaces rendered on the fallback. The PNG is not the frame. Fix with" >&2
  echo "  rm -rf godot/.godot/imported   # then re-run; this script re-imports" >&2
  echo "and note that a bare 'godot --import' REWRITES godot/project.godot." >&2
  grep 'Parse Error: \[ext_resource\]' "$LOGFILE" | head -5 >&2
  exit 4
fi
ls -l "$OUT"
