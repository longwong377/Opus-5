# Station geometry — glTF handoff

Procedurally generated interior and exterior geometry for a large ring-and-spine
space station, as plain **glTF 2.0 (`.glb`)** — no code, no engine dependency,
no build step. **Use `draco/` unless you have a reason not to**: it is the same
42 models Draco-compressed from 205 MB to **11 MB** (`hull.glb` is 824 KB
rather than 31 MB), needing one extra line in three.js — a `DRACOLoader` with
`setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.7/')` —
and the uncompressed originals stay beside it. **Everything is in metres at 1:1,
Y-up**; `hull.glb` is the full exterior and measures 2421.7 × 1253.1 × **8046.9**,
so do not rescale it, and note that single-precision float on the GPU will swim
and z-fight that far from the origin — use a floating origin if the camera
travels more than about a kilometre. Interiors are each in their own local frame
near the origin, and `starfury.glb` is a 6.0 m single-seat fighter on a 9.26 m span in 16 named sections (canopy, glazing, four engine bells, RCS sponsons, gun pods) at 3,968 triangles and 18 KB compressed, with no placement because it is a vehicle rather than a room. Each interior also carries a `placement` block in `manifest.json` — sector, ring, deck, angle, z and a column-major matrix for `THREE.Matrix4.fromArray()` — that puts it where it belongs inside `hull.glb`; the station axis is +Z and a room's +y points INWARD toward that axis, because the station spins and a room's floor is its outer wall. The files carry geometry and **mesh names only**, so they render
grey until you bind materials: `materials.json` holds 245 materials whose `binds`
arrays are the mesh-name fragments each applies to, and `textures/` holds the 49
PNGs they reference as `<name>_albedo/_normal/_orm.png` (ORM is
occlusion/roughness/metallic in R/G/B). These are visual meshes, not colliders —
generate your own, and do not use the corridor floor directly as a walkable
surface, since it carries a 66 mm centre channel and 22 mm proud tiles that a
capsule wedges on. Beyond the rooms: `starfury.glb` is a 6.0 m fighter (18 KB compressed); the four `drum_*` files are a 1.8 km enclosed habitat — terrain with arable fields and avenues, a settlement, colonnades, and tram cars (925 KB compressed for all four); and `crowd_library.glb` is a **character library rather than placed people** — its bounding box is one body, and its 2,604 meshes are species × costume × part (`crowd_<species>_<n>_npc_skin` / `_hair` / `_cloth__<style>` / `_leather__<style>`), so you instance and recolour from it; `crowd_library_low.glb` is the cheap LOD at 724 KB. **`manifest.json` lists every file with its triangle count,
mesh count, byte size and bounding box in metres — read that first.**
