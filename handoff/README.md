# Station geometry — glTF handoff

Procedurally generated interior and exterior geometry for a large ring-and-spine
space station, as plain **glTF 2.0 (`.glb`)** — no code, no engine dependency,
no build step. **Use `draco/` unless you have a reason not to**: it is the same
35 models Draco-compressed from 166 MB to **3.6 MB** (`hull.glb` is 824 KB
rather than 31 MB), needing one extra line in three.js — a `DRACOLoader` with
`setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.7/')` —
and the uncompressed originals stay beside it. **Everything is in metres at 1:1,
Y-up**; `hull.glb` is the full exterior and measures 2421.7 × 1253.1 × **8046.9**,
so do not rescale it, and note that single-precision float on the GPU will swim
and z-fight that far from the origin — use a floating origin if the camera
travels more than about a kilometre. Interiors are each in their own local frame
near the origin. The files carry geometry and **mesh names only**, so they render
grey until you bind materials: `materials.json` holds 245 materials whose `binds`
arrays are the mesh-name fragments each applies to, and `textures/` holds the 49
PNGs they reference as `<name>_albedo/_normal/_orm.png` (ORM is
occlusion/roughness/metallic in R/G/B). These are visual meshes, not colliders —
generate your own, and do not use the corridor floor directly as a walkable
surface, since it carries a 66 mm centre channel and 22 mm proud tiles that a
capsule wedges on. **`manifest.json` lists every file with its triangle count,
mesh count, byte size and bounding box in metres — read that first.**
