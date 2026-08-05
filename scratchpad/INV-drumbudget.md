# INV-540..549 — the drum's triangle budget, session 4r

**NOT YET IN `canon/INVENTIONS.md`.** Written here because two agents wrote to that
register on the same day and two numbers ended up meaning two things each; the block
INV-540..549 is reserved for this work and `tools/inv_check.py` gates the merge.
Entries are in the register's own format and can be moved across unchanged.

Block used: **INV-540, INV-541, INV-542**. INV-543..549 are unused and free.

---

## INV-540 — The drum ground's LOD error is a property of the PATCH, not of the drum

**What.** `station/drum_ground.py` gains `PATCH_LOD_ERR_MM` — the deviation of each of the
five decimation strides from lod0, measured on each of the 280 ground patches separately, in
millimetres — plus `patch_lod_table()` and `patch_level()`, which `visible_set` and
`visible_cost` now use in place of `level_for_distance`.

**Why it is not a change of standard.** The switch criterion is untouched: still
`_switch_distance(err)`, still 1.5 px of deviation, still the same screen model, still the
same five strides and the same triangle counts per level. Only the DOMAIN of the error
measurement changes. `lod_error_report()` measures whole patches at full resolution — one per
land-use band — and then takes the `max()` and applies it to every patch on the drum, so the
lake pays the settlement podium's error and the parkland pays the arable's finest noise
octave. Measured over all 280 patches, the stride-4 switch distance the drum-wide table
imposes is **554 m** and the per-patch answer ranges **113 to 713 m** — a factor of 6.3.

**What constrained it — the collision contract, not a preference.** `station/drum_walk.py`
builds its collision tile at a uniform stride 1 and then asserts two things against the render
ground: that a body stands on the ground it can see (within `STEP_M` = 0.100 m), and that
inside the render's own lod0 radius the two are the IDENTICAL surface. Both are statements
about the mesh inside that tile, so inside the tile the per-patch table is floored by the
drum-wide one:

    switch[i] = max(per_patch[i], min(drum_wide[i], collision_reach_m()))

`collision_reach_m()` is read from `drum_walk.patch_span_m()` and `rings_for(walk_distance_m())`
— **449.7 m**, the corner of the 5 × 5 patch tile — never restated. Asserted over every patch
at 5 m intervals inside that radius: **0 of 24,920 patch-distance samples go coarser.**
Verified end to end: `drum_walk.py --selftest` reports `max -97.8 mm` before and `max -97.8 mm`
after, and `within the render's own lod0 radius (198 m, 92 casts): 0.000 um` in both. The rms
*improves*, 20.5 → 20.1 mm, because of the second half of this entry.

**AND IT IS ALSO A CORRECTION, WHICH IS WHY THIS IS NOT A BUDGET TRICK.** The representative
sample is one patch per band at mid-length and it MISSES the worst patch: per-patch stride-8
error reaches **1.974 m** where the representative maximum is **1.048 m**. Those patches now
switch LATER — they are drawn FINER than they are today. **360 of the sampled positions inside
the collision tile get more triangles than they have now, not fewer**, and `_selftest` asserts
that count is non-zero, because if the per-patch measurement found nothing the `max()` had
hidden there would be no reason to keep 1,400 numbers.

**Measured worth**, on `budget.DRUM`'s own 4 × 3 lattice, verified through
`export_scene.drum_parts` at the worst eye (270°, 5132 m) rather than through the counting path
alone:

| | before | after |
|---|---|---|
| ground | 96,320 | **70,880** |
| drum visible set | 315,604 = **105.2% FAIL** | 290,164 = **96.7% PASS** |
| drum share of frame | 26.3% FAIL | 24.2% PASS |
| `budget.py` | 21/28 | **23/28** |
| patches per level at the worst eye | 16 / 88 / 134 / 42 / 0 | 16 / 47 / 74 / 143 / 0 |

**Pinned rather than derived at import**, for the reason `drum_dressing.DRUM_FIXED_TRIS` is
pinned: the derivation is 305,000 `sample()` calls and costs **51 s**, and no gate should pay
that to answer a question about a committed terrain. `python3 station/drum_ground.py
--derive-patch-lod` rebuilds it, prints the replacement table and fails on drift;
`_selftest` re-measures four patches (one per land-use band) on **every** run at 0.8 s, so the
pin cannot rot silently, and carries a control that perturbs one pinned value by 40 mm and
requires the check to fire. `PATCH_LOD_DIGEST = "3b42b398bcc5242e"`, blake2b over the table,
the same instrument as `GROUND_DIGEST`.

**Overturned by** any change to `sample()` — which is what the digest and the per-run
re-measurement exist to catch — or by a streaming budget for the drum, which would make the
whole visible-set question a different one.

---

## INV-541 — The habitat drum cannot be occlusion-culled, and the ceiling is 5.3%

**What.** `station/occluders.py --drum` measures what an occluder could buy inside the drum and
the answer is **15,336 of 290,164 triangles — 5.29%**, leaving the drum at 91.6% of its
allowance. No occluder geometry is built for the drum and none should be.

**Why it is geometry rather than engineering.** The drum's inner surface is the boundary of a
CONVEX region, and every point of the boundary of a convex region is visible from every point
inside it. `godot/scenes/drum.tscn`'s own lighting note already states the physical form of
this — *"a closed cavity of 4.5 million m² … every surface can see most of the others"* — and
`budget.DRUM`'s comment states the consequence: *"no occlusion — there is no wall to hide
behind"*. Nothing can hide anything except relief and the objects standing on it, and both are
now measured instead of asserted.

**The control is the convexity itself, and it fires.** Flatten the heightfield to the mean
cylinder and re-cast: **0 of 1,440 targets blocked**. A single blocked target there would mean
the measurement is reading its own arithmetic rather than the terrain.

**What the ceiling is a ceiling OF**, stated because every term is generous: it culls a target
the moment it is hidden, charges nothing for the occluder geometry, nothing for the depth
rasterisation, and tests at a per-feature granularity no renderer in this project works at. It
is weighted by the triangles each hidden thing would have contributed **at the level the LOD
chain would have drawn it** — a copse hidden at 1,200 m is 30 triangles and a farmstead hidden
at 30 m is 800, so a percentage of *features* would have said nothing about a budget.

| | hidden | of | ceiling |
|---|---|---|---|
| ground patches | 6 | 280 | 864 tri of 70,880 = 1.22% |
| dressing features | 179 | 1,945 | 14,472 tri of 114,910 = 12.59% |
| the fixed parts | — | — | 104,374 tri, **not cullable at any granularity** |

**And one level down it is worse than the ceiling.** Godot tests an INSTANCE's axis-aligned
bounding box against a rasterised depth buffer, not a triangle. `render_shot.gd` reports
**147 mesh instances over 9 files** for the whole drum, split by MATERIAL GROUP rather than by
place — `ground.glb` is 13 nodes spanning 4.5 million square metres, and not one of those AABBs
can ever be behind anything. This is CLAUDE.md's own corridor finding (*"Godot culls per
instance AABB and the corridor's OBJ groups span the whole 345° ring"*) one environment along,
with the same conclusion: what would close a drum budget is **spatial submission**, and there is
nothing for an occluder to do until that exists.

**Overturned by** the drum being submitted per patch or per cell rather than per material
group — at which point this measurement should be re-run, because the ground's 1.22% is a
number about *patches*, and a per-cell dressing submission is where the 12.59% would start to
be reachable.

---

## INV-542 — The drum gate's worst eye is a town street, and a 168-eye sweep confirms it

**What.** `budget.DRUM`'s 4 × 3 lattice puts its worst standing eye at **(270.0°, 5132 m)**.
That is inside the second settlement band (`interior.LAND_USE` puts settlement at 259.2–302.4°),
on terrain `drum_ground.sample` tags **`avenue`** at **+6.75 m** — a street in the drum's town,
which is about as unambiguously a standing position as anywhere on the drum.

**Why this needed checking at all.** INV-501 states the lattice's own error as **16.2%**
(13.6% after INV-540), measured against its half-resolution sub-lattice, and the drum now passes
with a margin of **9,836 triangles** — *smaller* than that stated error. A verdict inside its
own sampling error is not a verdict, so the question "is the 4 × 3 worst eye the drum's worst
eye" stopped being academic the moment the gate went green.

**Measured, not argued.** A **24 × 7 = 168-eye** sweep through the same counting paths
(`drum_ground.visible_cost` + `drum_dressing.dressing_cost` + `DRUM_FIXED_TRIS`, 39 s):

| | |
|---|---|
| worst eye of 168 | **(270.0°, 5132 m), 290,164** — the same eye the 4 × 3 lattice finds |
| eyes over the 300,000 bound | **0 of 168** |
| next four | 287,220 (330°, parkland) · 286,960 (285°, avenue) · 286,906 (120°, avenue) · 286,674 (135°, avenue) |
| best eye | 215,830 |

So the 13.6% figure is the sub-lattice's disagreement, not the true uncertainty: **every eye
within 3.3% of the worst is at z = 5132 m**, mid-length, which is where the whole barrel is in
view, and the circumferential station barely matters. The gate's lattice is coarse in the axis
that matters least.

**What constrained the answer.** `budget.py` is not this session's file and the 4d ruling
forbids growing gates, so nothing was added to `drum_eyes`; this is a property of an existing
gate, measured and recorded, and the coarse lattice is left alone precisely because it was
*stated rather than placed on the answer* and it found the answer anyway.

**Overturned by** any change to `interior.LAND_USE`'s band positions or to `drum_dressing`'s
placement, either of which moves where the expensive standing positions are and makes this
sweep stale. Re-run it before quoting the margin.
