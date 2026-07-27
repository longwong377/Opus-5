#!/usr/bin/env bash
# Full pipeline: schema -> geometry -> gates -> engine -> PNGs.
#
# One command from a schema edit to inspectable engine renders. There is no GPU
# and no human reviewer, so this loop is the whole verification story: Mesa
# lavapipe rasterises Forward+ on the CPU, Godot renders offscreen under Xvfb,
# and the resulting PNGs are read back directly.
#
# What changed from the version that only ever produced one exterior frame:
# the interior now exists, and an exterior-only pipeline was checking half the
# project. This renders both, because the drum is the view the entire
# structure-first phase exists to produce.
#
# Slow -- minutes. tools/preview_render.py is the fast path for proportion and
# silhouette; this one is for material, light, exposure and mood.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RES="${RES:-1280x720}"
OUTDIR="${OUTDIR:-$ROOT/docs}"

echo "--- generate ---"
(cd "$ROOT/station" && python3 generate_hull.py >/dev/null)
python3 "$ROOT/station/validate.py" | tail -1
python3 "$ROOT/station/budget.py" | tail -1

echo "--- self-tests that gate what gets rendered ---"
python3 "$ROOT/tools/export_scene.py" | tail -1

# The two shots are chosen, not arbitrary. The exterior proves the hull still
# reads as Babylon 5 at 8 km; the drum proves the volume the structure phase
# exists to produce. Camera parameters are here rather than in the render
# script so that a regression shows up as the same frame looking different,
# which is the only way a still comparison means anything.
echo "--- exterior ---"
bash "$ROOT/tools/render_godot.sh" --shot exterior \
  --orbit 6400,15,208 --fov 42 --sun-az 238 --sun-elev 24 \
  --res "$RES" --out "$OUTDIR/engine-exterior.png"

echo "--- drum interior ---"
bash "$ROOT/tools/render_godot.sh" --shot drum \
  --stand 205,4400 --target 0,0,6425 --fov 55 \
  --lights-per-run 24 --shadow-lights 3 \
  --res "$RES" --out "$OUTDIR/engine-drum-interior.png"

echo "--- done ---"
ls -l "$OUTDIR/engine-exterior.png" "$OUTDIR/engine-drum-interior.png"
