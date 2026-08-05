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

---

# The measurement, and it fails on the content it was written against

`python3 station/drum_dressing.py --near` / `--near --bare`. 209 standing
positions — a uniform 16-angle sweep **plus three angles inside every land-use
band**, because a uniform sweep of this drum lands no position in the 36°-wide
water band and the first version of this gate reported PASS with the shore
unmeasured.

| | control (`--near --bare`, the drum as 4q left it) | after |
|---|---|---|
| nearest thing standing, median | **32.42 m** | **2.32 m** |
| nearest thing standing, worst | **99.34 m** (parkland) | **3.28 m** (arable) |
| features per hectare within 11.05 m, median | **0** | **1,278** |
| below-horizon view that is bare, drum-wide | **95.2%** | **34.5%** |
| worst band | arable **97.2%** | settlement **43.9%** |
| verdict | **FAIL** | **PASS** |

The control is not a stub: it is the drum exactly as session 4q left it, all
1,945 far-field features present, with only the near rung withheld.

Both floors are in INV-491 and neither was chosen. `drum_dressing._selftest`
carries the gate, the control, and a check that the control fails *for the right
reason* — `nb.nearest_worst_m > 10 × n.nearest_worst_m`, i.e. for having nothing
NEAR rather than nothing at all.

**Self-tests:** `station/drum_dressing.py` **276/277** (the one failure is the
honest drum-budget red below); `station/drum_ground.py` **82/82**.

# Frames — all Forward+ / Vulkan 1.4.318, checked in the render log

| | path |
|---|---|
| before, down the axis (`--stand 20,4700 --look 20,6300`) | `docs/near-4q-before-axis.png` |
| after, same camera | `docs/near-4r-after-axis.png` |
| **before, HALF distance** (eye 262.197,95.432,4700 → target 263.802,96.016,4704, 23.1° down) | `docs/near-4q-before-half.png` |
| **after, same camera** | `docs/near-4r-after-half.png` |

The before frames were rendered from a `git worktree` holding `fdc27bf`'s
`drum_dressing.py` against the *current* `garden.py`, so the only difference
between the pair is this session's module.

**My own craft score at the rubric's half distance: 1 → 2.**

*Before* is `AAA-STANDARD`'s C1 verbatim — two flat colour fields meeting along a
straight-edged polygon boundary, nothing standing on either, and the green
parcel carries no texture at all.

*After* has real relief, row structure that converges on the vanishing point,
a scatter with silhouette, a bank between the two parcels, and four materials
where there were two. It is **not a 3**, and the three reasons are:

1. the near tufts are 6-sided 3-stack domes and read as faceted at 1–2 m;
2. the crop takes its parcel's own `ground_arable_*` material, whose normal map
   is **cracked earth** — so a standing crop reads as ploughed soil at 2 m;
3. the green parcel still has no ground texture between the tufts at all.

(2) and (3) are `materials.py`, not this module — see the patches below.

# Findings — things that are WRONG in the repo or in the brief

**1. `drum_dressing.worst_case_cost` is 104,842, not 119,868.** STATE.md §24.6,
INV-452 and `docs/aaa-scorecard.json` all say it is "**unchanged** at
119,868 / 120,000" after the 4q garden rebuild. Measured on the **committed**
module (`git show fdc27bf:station/drum_dressing.py`) against the **current**
`garden.py`, it is **104,842**. Level 0 of this module's tree and town block IS
`garden.tree()` / `garden.block_building()`, so rebuilding them moved it. The
brief inherits the stale figure ("currently 119,868 used"). The practical
consequence is good news: the whole near rung fits inside the existing
`DRESSING_TRIS` with 5,090 to spare, and `--derive` even offers a *longer*
level-0 reach (118.4 m), which is declined for the reason below.

**2. `drum_dressing._selftest` was asserting the drum's budget with a hard-coded
`fixed = 75_968`, and the true figure is 104,374.** That constant is a copy of
another module's cost: it contains `garden.townscape` at 22,620, which is
**51,026** since 4q. The assertion was passing with 28,406 triangles it could not
see. Now measured from the same parts `export_scene.drum_parts` emits, pinned as
`DRUM_FIXED_TRIS`, and asserted.

**3. The drum is over its own allowance, and it was before this session.**
Priced the way a renderer prices it — one eye at a time, not three worst cases at
three different places — the worst standing position is **315,604** against
`budget.DRUM["visible_set_tris"]` = 300,000: fixed 104,374 + ground 96,320 +
dressing 114,910. Without the near rung the same eye is ~305,700. **`budget.py`
is not this module's file** and another agent is editing it (INV-500..503), so
this is left as an honest RED in `drum_dressing._selftest` with the cause named
in the failure message, rather than absorbed by quietly cutting `DRESSING_TRIS`.

**4. The brief's third bullet is not correct, and being wrong about it is
useful.** *"`drum_ground`'s own half of that boundary is a drawn line rather than
a change in the ground."* Measured over 140 tagged boundaries against a paired
control window in open field at the same z, the boundary carries **0.231 m more
relief than open field (median), 0.536 m at p75**, and at the finding's own eye
it is **1.05 m over 28 m**. The ground does change. What it does not do is change
*visibly*: 0.49 m over a 32 m window is **0.88°**, while the MATERIAL changes
instantaneously at the cell boundary. A hard tonal step on a surface with no
visible geometric step is exactly what "a drawn line" describes — and the cure
is an object on the line, not a sharper heightfield, because `drum_ground`'s step
rule forbids anything under one 31.2 m stride-8 cell and its own history records
what a 3.5 m step cost (a 3.28 m lod1 error, a 3,379 m switch distance, and the
entire 573,440-triangle field at lod0). `drum_ground._selftest` now carries both
halves of that as assertions, and both controls fire.

**5. My own first version of that measurement could not fail.** Written as an
absolute — "the 32 m window across a boundary changes by 0.581 m" — it survives
`PARCEL_RELIEF_M = 0` almost intact (0.269 m), because a 32 m window anywhere on
a six-octave fbm field changes by about that much. It is now a paired
differential and the control drives it to **0.011 m**.

**6. A keep-out radius has to be the footprint, not the circumscribed disc.**
The first version kept near cover out of a disc around every standing thing and
included `gantry`, whose boom is 87.4 m of pipe on two legs — clearing a 44 m
disc of crop and taking the arable band's worst nearest-object distance from
3.30 m to 24.01 m in one run. An irrigation boom is a frame you stand a crop
under. Fixed to oriented rectangles from `prototype_dims` turned through each
block's own placed yaw, and `_KEEPOUT_KINDS` cut to things with a solid footprint.

**7. Three fovs exist in this project.** The player's **70** (`player.gd:279`),
the render shot's **46** (`export_scene.SHOT_FOV_DEG`), and this module's LOD
constant **50** (`drum_ground.FOV_DEG`). A near-field floor derived from the
wrong one looks derived and is wrong. Every committed drum frame is composed at
46, whose below-horizon median is 8.36 m — so the frames are a *conservative*
view of this defect, not an exaggerated one.

# Patches for files I do not own

## `tools/export_scene.py` — DRUM_CALIBRATION's `dressing` rows must be re-measured

**This is the one the brief asked me to flag.** The `dressing` part now contains
the near rung, so its measured pixel contribution has changed. The affected
entries are `DRUM_CALIBRATION["wide"|"garden"|"tram"]["contribution"]["dressing"]`
(39.08 / 32.30 / 47.26) and the matching `["largest_region"]["dressing"]`
(32.08 / 20.56 / …). No part was added or renamed, so `drum_parts`' own
name-coverage assertion still passes — the numbers are simply stale. Method is
that file's own: render each framing at `contribution_res` whole and with
`--omit dressing`, count the pixels that move. Every framing will go UP; at the
`wide` framing the near rung occupies most of the lower third of the frame.

## `station/materials.py` — the arable ground groups

Two things the half-distance frames show and no gate can:

1. `ground_arable_*` carries a **cracked-earth normal map**. The near crop takes
   the parcel's own group by construction (INV-492) and therefore inherits it, so
   a standing crop reads as ploughed soil at 2 m. Either the arable groups want a
   row/foliage normal, or `drum_dressing` wants a `ground_crop_*` family that
   keeps each parcel's albedo and changes the normal. I would rather it were the
   second, and it needs a material author to decide.
2. At the `--stand 20,4700` eye the **green** parcel (`ground_arable_2`) shows no
   surface texture at all at 2 m while its tan neighbour shows a full normal map.
   `docs/near-4q-before-half.png` is the clearest evidence — the left half of that
   frame is a single flat colour across 500 px.

## `station/budget.py` — nothing to apply, one number to know

See finding 3: the drum's worst one-eye total is **315,604 / 300,000**.
`drum_dressing.drum_worst_eye()` computes it and `drum_fixed_cost()` breaks it
down, if that file wants to call them rather than keep its own list.

## `STATE.md` / `docs/aaa-scorecard.json` — one figure to correct

"`drum_dressing.worst_case_cost` unchanged at 119,868 / 120,000" (§24.6, INV-452,
scorecard `garden_townscape` performance note) should read **104,842**.

**8. And one of my own, found by re-reading rather than by a gate.**
`_lattice_sample`'s docstring said its memo was "invalidated by
`reset_near_cache()`, which `field(rebuild=True)` calls". `field()` did not call
it. A caller asserted in prose and absent from the code is the exact defect
CLAUDE.md's START HERE section counts nine instances of, written down inside my
own comment. Wired; verified output-neutral (near cost 11,972 and 630 stands
before and after a rebuild, `FIELD_DIGEST` unchanged).

# What the near rung is, in one paragraph

`near_field(eye)` places one stand of cover per `drum_ground` lattice cell —
3.90 × 4.04 m, the resolution the heightfield's own comment says it cannot carry
— within 90 m of the eye, deterministic in WORLD space so walking toward a
tussock does not regenerate it somewhere else. Three rungs at the module's own
`LOD_RATIOS[1]` = 3.2: fine inside 8.8 m, full to 28.1 m, one stand per 2×2 cells
beyond. Eight items: `crop` (ridges along the furrow direction, which
`drum_ground` says runs along the axis, so they converge on the vanishing point
when the drum is framed down its length), `tussock`, `scrub`, `margin` (rough
grass on a hedge bank), `stone`, `reedtuft`, `boxhedge`, and `wall` (INV-494).
Recipes are keyed on the ground's own kind and take the ground's own material
group. It reaches the engine through `dressing_set()`, the one call
`export_scene.drum_parts` makes, so there is no second path to forget. Worst
standing position **19,236 triangles**; combined with the far field, **114,910 of
the 120,000 allowance**.
