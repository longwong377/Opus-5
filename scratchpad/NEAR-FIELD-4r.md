# The drum near field — the gate, the INV entries, and the patches

Session 4r, agent-owned files: `station/drum_dressing.py`, `station/drum_ground.py`.
`canon/INVENTIONS.md` was being written by another agent (mtime 18:12, INV-500..503
landed while this work was in flight), so the entries below are **written out here in
that file's format and are NOT appended**. They must be appended by whoever integrates.

INV numbers 490–494 are used, as the brief directed. 495–499 are free; 500–503 are
taken by the concurrent budget work.

---

## INV-490 — The drum's near-field rung ends where the far field's guarantee begins

**What.** `drum_dressing.NEAR_R_M = NEAREST_FLOOR_M` = 90 m, and its own full/coarse
switch is `NEAR_R_M / LOD_RATIOS[1]` = 28.1 m.

**Why not a chosen radius.** `NEAREST_FLOOR_M` is already derived (INV-459) as the
distance inside which the far field guarantees something to look at — a little over
half a `drum_ground` patch diagonal, so that "there is always something in the patch
you are standing in" is true rather than average. The near rung's job is exactly the
ground *inside* that guarantee, so the two meet with no gap and no overlap. The
full/coarse ratio is the module's own `LOD_RATIOS[1]` = 3.2 rather than a fourth
ratio invented for this rung.

**Constrained by** cost: at the ground lattice's 15.79 m² cell, 90 m is 1,612 cells,
of which the stride-2 coarse rule keeps about 600. Measured worst near-rung cost over
36 standing positions is **19,116 triangles**.

**Overturned by** a change to `NEAREST_FLOOR_M`, which this follows by construction.

## INV-491 — Half of everything below the horizon is ground within 5.39 m of your feet

**What.** `drum_dressing.near_horizon_split()`. Standing at 1.70 m and looking at the
horizon through the player's own 70° vertical lens (`godot/scripts/player.gd` line 279,
Godot `Camera3D.fov` being vertical under the default `KEEP_HEIGHT`), the frame below
the horizon runs from depression 0 (infinitely far) to 35° at the bottom edge. Screen
area is linear in depression because the frame is a rectangle, so:

| | distance |
|---|---|
| bottom edge of the frame | `1.7 / tan(35°)` = **2.43 m** |
| MEDIAN below-horizon ground | `1.7 / tan(17.5°)` = **5.39 m** |
| upper quarter | `1.7 / tan(8.75°)` = **11.05 m** |

**Why it is the floor.** Measured at the eye of `docs/engine-4q-drum-dressed.png`
(`--stand 20,4700`), the nearest thing standing anywhere on the drum was a tree at
**44.3 m** and nothing at all was inside 35 m. The lower half of that frame could not
have been anything but bare ground, whatever else the drum carried. So the floor is
"something within `median_m`", and the companion area floor is
`NEAR_BARE_VIEW_MAX = 0.50` — 0.50 is not a taste parameter, it is what *median* means.

**Three fovs exist in this project and using the wrong one would make this look derived
and be wrong:** the player's 70, `export_scene.SHOT_FOV_DEG` = 46 (every committed
frame), and `drum_ground.FOV_DEG` = 50 (LOD pixel arithmetic only). 70 is both the
strictest — a wider lens puts more very-near ground in frame — and the one a player
looks through. At 46° the same median is 8.36 m, so every committed frame is a
*conservative* view of this defect.

**Overturned by** `player.gd` changing its fov, or by the project standing a person at
something other than 1.7 m.

## INV-492 — The near rung stands on the ground's own lattice, and takes the ground's own material

**What.** One stand of cover per `drum_ground` lattice cell — 3.903 × 4.044 m,
15.79 m². A crop stand in an `arable2` parcel emits the group `ground_arable_2`, taken
from `drum_ground._KIND_GROUP`, which is the group the ground under it is drawn with.

**Why that lattice.** `drum_ground` states its own limit above `HEDGE_W_M`: "the hedge
itself — 2 m tall, 1 m wide — is finer than lod0's 3.9 m cell and belongs in the
material, not the field. A 1 m-wide ridge in a 3.9 m lattice does not render as a hedge
at any level." That is correct, and it is a **delegation** that nothing took delivery of,
which is why the near field is flat. The near rung's resolution is therefore exactly the
resolution the heightfield admits it cannot represent. Worst distance from a standing
position to the nearest cell centre is half a cell diagonal, **2.81 m**, against the
5.39 m INV-491 asks for.

**Why the material comes from the ground.** Hard rule 4 — inside and outside from one
schema — applied to a third thing. A crop whose colour is authored separately would
drift from the parcel it stands in and the drift would be invisible until somebody
looked at a frame. Heights: crop 0.95 m (below a standing eye, so 34b's readable parcel
patchwork survives from above), tussock 0.42 m and scrub 0.85 m from `garden.TUSSOCK_R_M`
/ `SCRUB_R_M`, clipped hedge 0.82 m against 29a's "clipped hedges about head height"
which `garden.HEDGE_H_M` already reads as 1.05 m.

**Overturned by** `drum_ground` changing `CELLS_A`/`CELLS_Z`, which this follows.

## INV-493 — The near field's density is four times the Garden's, and it was solved rather than set

**What.** `drum_dressing.NEAR_DENSITY_GAIN = 4.0`, a multiple of
`garden.TUSSOCK_PER_100M2` = 4.4 and `SCRUB_PER_100M2` = 2.0, read from `garden.py`
rather than restated. The first entry of each recipe is a **primary** and is guaranteed
one per cell.

**Why solved.** `--derive-near` walks a ladder and reports the smallest gain at which
every land-use band passes both floors of INV-491:

```
gain 1.0  worst nearest 3.80 m   worst band water      60.5%  FAIL
gain 2.0  worst nearest 3.80 m   worst band water      55.6%  FAIL
gain 3.0  worst nearest 3.13 m   worst band settlement 50.7%  FAIL
gain 4.0  worst nearest 3.11 m   worst band settlement 48.6%  PASS
gain 8.0  worst nearest 3.11 m   worst band settlement 41.9%  PASS
```

**Two things worth reading off that table rather than just its answer.** The DISTANCE
floor passes at every gain including 1.0 — proximity is bought by the guaranteed
primary and density buys none of it; density buys COVER. And the binding band is never
arable: it is the town and the lake shore, which is exactly where a scatter-density
parameter is no use, and is what sent the settlement to a plot wall instead of more
grass (INV-494).

**Why it is not the Garden's own number.** 4.0 × 4.4 = 17.6 tussocks per 100 m², one
clump every 2.4 m — a meadow. The Garden's 1.0 describes a **mown civic terrace** that
also carries paving, a pool, benches, lamps and a colonnade inside the same 35 m. The
ratio between the two is the finding, not a fudge.

**Overturned by** any change to the floors in INV-491, or by `garden.ground_cover`
re-deriving its own densities — this is a multiple of them and follows.

## INV-494 — A town's near view is bounded by walls, not filled with objects

**What.** `drum_dressing.WALL_H_M = 1.25`, `WALL_W_M = 0.34`. A settlement lattice cell
whose neighbour is an avenue, a verge or a carriageway gets a plot wall along that
frontage instead of a clipped hedge, one lattice cell long plus 6% overlap so
consecutive cells join into a continuous run.

**Why, and it is arithmetic rather than taste.** Solved against the near gate, the
settlement band needed **eight times** the Garden's ground-cover density to get its
below-horizon view under 50% bare, and eight times the grass in a town centre is an
absurd answer to a real number. A 3.6 m clipped hedge at 5 m covers about 3% of the
below-horizon panorama, so seventeen of them are needed; ONE continuous 1.25 m wall
along a frontage at 8 m covers about a third of the band over half the azimuths. With
the wall the band passes at gain 4 and its bare view falls 71.6% → 43.9%.

**And it is what the reference asks for and nothing was building.**
`03-sector-blue/Babylon_5_2-22_33a.jpg` (authority 1) — "rectangular built parcels
carry a fine internal grid". `drum_ground` cuts that grid into the podium as avenues;
the plot boundary standing on it did not exist. 1.25 m is below a 1.7 m eye, so a
player sees over the wall down the street.

**The frontage is read off the ground's own kinds**, never a second street table, so the
wall follows whatever grid `drum_ground` cut.

**Overturned by** a ground-level authority-1 frame of the drum's built half showing open
plots rather than bounded ones. `2-22_33a` is a wide shot and cannot settle it at eye
level.
