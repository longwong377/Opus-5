# Babylon 5 — geometry handoff

Procedurally generated geometry from a 1:1 simulation of the Babylon 5 station.
Everything here is **plain glTF 2.0 (`.glb`)**. There is no code, no engine
dependency and nothing to install — `GLTFLoader.load()` and it is in your scene.

---

## Read this first: scale

**The files are in metres, at true scale, Y-up.** Measured out of the accessor
bounds rather than assumed:

```
hull.glb bounding box:  2421.7 × 1253.1 × 8046.9
```

The real Babylon 5 is **8,047 m** long. The station runs along **+Z from 0**,
the rotation axis is Z, and Y is up. **Do not rescale anything.** Every interior
is authored in the same space, so if you place two of them by their own
coordinates they line up the way they do on the station.

Interiors are exported **in their own local frame** (each starts near the
origin), so you position them yourself — they are room-sized objects, not
station-sized ones.

## What is in the box

**35 models · 132.7 MB · 1,650,061 triangles · 245 materials · 49 textures.**
Every file was parsed after export: all 35 are valid glTF 2.0 with a default
scene and spec-required accessor bounds.

`manifest.json` lists every file with its triangle count, mesh count, byte size
and bounding box in metres. Read that rather than trusting this paragraph.

- **`hull.glb`** — 31.1 MB, 387,630 tri. The entire exterior of the station,
  8 km. This is the one for the space scene.
- **`central_corridor.glb`** — the connective tissue. Every deck is this in a
  345° ring, so it is the piece to repeat if you want to walk anywhere.
- **34 interiors**, largest first: the Garden (hydroponics), the Zocalo and its
  shops and kiosks, civilian and personnel and alien and ambassadorial
  quarters, transient habitation, Downbelow, the alien sector, Kosh's quarters,
  Command & Control, the council chamber, the customs halls and arrival
  concourse, the docking bays, the core shuttle and its car, the observation
  domes and rotundas, the bars and restaurants — Earhart's, the Eclipse Cafe,
  the Fresh Air Restaurant, Happy Daze — the plant, air compressors and water
  reclamation.

**`textures/`** — 49 PNGs in albedo / normal / ORM triples, 33 MB.
**`materials.json`** — 245 materials, 243 of which carry `binds`: the mesh-name
fragments that material applies to. That is your recipe for turning grey
geometry into the source look.

## Four things that will bite you

**1. The `.glb` files carry no materials.** `materials: 0` inside every one —
a property of the exporter, not an omission. They carry positions, normals and
**mesh names**, and the look lives in `materials.json` beside them. So a file
renders **grey** until you bind materials yourself.

Doing that is the one piece of real work in this handoff, and it is mechanical:

```js
// materials.json entries look like:
//   "corridor_wall_plate": { "albedo":[0.29,0.29,0.30], "roughness":0.55,
//                            "metallic":0.1, "texture":"wall_plate",
//                            "binds":["wall_plate","corridor_wall"] }
// Bind by substring against the mesh name -- that is how the source engine
// does it, and why `binds` is a list of fragments rather than exact names.
scene.traverse(o => { if (o.isMesh) o.material = pickByBinds(o.name); });
```

Textures are in `textures/`, named `<texture>_albedo.png`, `_normal.png` and
`_orm.png` (occlusion / roughness / metallic packed into R / G / B — feed it to
`aoMap`, `roughnessMap` and `metalnessMap` on the same `MeshStandardMaterial`).
Mesh-name prefixes are meaningful on their own if you would rather invent a
look: `hull_*`, `deck_*`, `wall_*`, `fix_*` (fixtures), `prop_*`, `dress_*`.

**2. It is 8 km long and three.js is float32 on the GPU.** At that distance
from the origin, single-precision resolution is around a millimetre, so you
will see vertex swim and z-fighting far out. The station's own engine is built
double-precision specifically for this. If your player can get more than ~1 km
from the origin, use a **floating origin** — recentre the scene on the player
periodically. Interiors placed near the origin are unaffected.

**3. These are visual meshes, not colliders.** Generate a collider from the
mesh (Rapier's trimesh is fine at these triangle counts) or build a simplified
box/plane floor. Do not use the render mesh as a character-controller floor
without checking it: the corridor decks carry a 66 mm lighting channel down the
centreline and 22 mm proud floor tiles, and a capsule dropped on that wedges on
an internal edge. That is a measured failure in the source project, not a
guess — it walks on a separate smooth shell for exactly this reason.

**4. They are uncompressed.** Nothing here has been through Draco or meshopt.
Run `gltf-transform draco` (or `gltfpack`) over them before shipping to a
browser; expect a large reduction, though the exact ratio has not been measured
on this geometry.

## What is deliberately not here

- **No people.** The crowd, the dialogue, the schedules, the economy — none of
  it is in these files.
- **No lighting.** Light rigs live in the source engine's scene files.
- **Not the whole interior.** The station has 129 places; these are the ones
  built by hand-written, place-specific code. The other ~89 are assembled by a
  shared room generator — all geometrically distinct, but variations of one
  system, and the weakest part of the source project by its own scoring. They
  are also only available baked into whole-deck files of 30–445 MB each.
- **Seven of the 42 hand-built places are deliberately absent.** The cobra
  bays, comms grids, mooring clamps, nav beacon, power transfer core and
  proximity arrays are **exterior structures** with no interior builder —
  they are already part of `hull.glb`. `standard_corridor` is the kit itself
  rather than a place; `central_corridor` is the built form of it and is here.
  (`manifest.json`'s `failed` list is only populated on a full build, so it
  reads empty after a re-stage. This paragraph is the record.)

## Attribution

Babylon 5 is the property of Warner Bros. Discovery. This geometry is
fan-made, generated from published references and declared extrapolations. Fine
for personal and portfolio work; not for commercial release.
