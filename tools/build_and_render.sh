#!/usr/bin/env bash
# Full pipeline: schema -> geometry -> glTF -> Godot -> PNG.
#
# One command from a schema edit to an inspectable engine render. There is no
# GPU and no human reviewer, so this loop is the whole verification story:
# Mesa lavapipe provides Vulkan 1.4 on CPU, Godot renders offscreen under Xvfb,
# and the resulting PNG is read back directly.
#
# Slow -- minutes, not seconds. tools/preview_render.py is the fast path for
# judging proportion and silhouette; this one is for material and lighting.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64}"
SHOT="${1:-engine_view}"

export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json

echo "--- generate ---"
(cd "$ROOT/station" && python3 generate_hull.py >/dev/null)
python3 "$ROOT/station/validate.py" | tail -1
python3 "$ROOT/station/budget.py" | tail -1

echo "--- export ---"
python3 "$ROOT/station/export_gltf.py" | grep -E 'triangles|size_mb'
cp "$ROOT/station/generated/station.glb" "$ROOT/godot/station.glb"

echo "--- import ---"
timeout 900 "$GODOT" --headless --path "$ROOT/godot" --import >/dev/null 2>&1 || true

echo "--- render ---"
timeout 1800 xvfb-run -a --server-args="-screen 0 1600x900x24" \
  "$GODOT" --path "$ROOT/godot" --rendering-driver vulkan \
  --resolution 1600x900 --quit-after 150 2>&1 | grep -E 'captured|Vulkan|materials:|ERROR|SCRIPT'
