# Session 4r — the drum's triangle budget. 105.2% FAIL → 96.7% PASS, content intact.

Working notes, written as I went because this container has been recycled three times today.
Companion files: `scratchpad/INV-drumbudget.md` (INV-540..542),
`scratchpad/PATCHES-4r-drumbudget.md` (files I do not own).

## The result

| | before | after |
|---|---|---|
| drum visible set, worst eye (270°, 5132 m) | 315,604 = **105.2% FAIL** | **290,164 = 96.7% PASS** |
| drum share of frame | 26.3% FAIL | 24.2% PASS |
| `station/budget.py` | 21/28 | **23/28** |
| ground at the worst eye | 96,320 | **70,880** |
| dressing | 114,910 | 114,910 — untouched |
| fixed parts | 104,374 | 104,374 — untouched |
| `drum_dressing.py` selftest | 276/277 (the drum budget red) | **277/277** |
| `drum_ground.py` selftest | 82/82 (50 checks) | **88/88** (56 checks) |
| `drum_walk.py` selftest | 23/23 | **23/23**, `max -97.8 mm` both, rms 20.5 → 20.1 |

Nothing was removed. `DRESSING_TRIS` is unchanged at 120,000 and `budget.DRUM` is unchanged at
300,000. Verified through the BUILDING path, not the counting path:
`export_scene.drum_parts` at the worst eye returns 290,164, and the counting path agrees exactly.

## The negative result, which was the brief's headline question

**Occlusion cannot help the drum. The ceiling is 5.29%** — `python3 station/occluders.py --drum`,
~17 s, INV-541. The drum's inner surface is the boundary of a convex region; every point of it
is visible from every point inside it. Perfect, free, per-feature culling removes 15,336 of
290,164 triangles and leaves the drum at 91.6%.

* control: flatten the heightfield to the mean cylinder → **0 of 1,440 targets blocked**
* ground: 6 of 280 patches fully hidden = 864 tri of 70,880 = **1.22%**
* dressing: 179 of 1,945 features hidden = 14,472 tri of 114,910 = **12.59%**
* fixed parts (104,374, 36.0% of the frame): not cullable at any granularity
* and Godot culls per **instance AABB** — `render_shot.gd` prints *147 mesh instances over 9
  files* for the whole drum, split by MATERIAL GROUP, `ground.glb` being 13 nodes spanning
  4.5 million m². Not one of those boxes can be behind anything.

## What worked instead — the error is a property of the PATCH

`lod_error_report()` measures whole patches at full resolution, one per land-use band, then
takes `max()` and applies it to all 280. The lake pays the settlement podium's error. Same
1.5 px criterion, measured on the patch actually being drawn: stride-4 switches at 554 m
drum-wide and at **113–713 m** per patch.

Floored inside `drum_walk`'s collision tile (449.7 m, read from `drum_walk` not restated) so
nothing a player can stand on is coarsened — asserted over 24,920 patch-distance samples, and
the walk gate's deviation is byte-identical.

**It is also a correction:** the representative sample UNDERSTATES some patches (stride-8 to
1.974 m against a representative max of 1.048 m), so 360 sampled positions inside the tile are
drawn FINER than before.

## Levers measured and NOT taken

| lever | worth at the worst eye | why not |
|---|---|---|
| `lod.py FOV_DEG` 50 → the shipped 70 | 290,164 → **263,612** | `lod.py` is not mine and it moves every LOD ladder in the project. Full patch + blast radius in `PATCHES-4r-drumbudget.md` §2 |
| `garden.townscape` LOD ladder | up to −51,026 | `garden.py`/`export_scene.py` are not mine. §3 |
| ground `PIXEL_BUDGET` 1.5 → 3.0 | −33,696 | that IS a quality cut. Declined |
| `drum_dressing.LOD_SCALE_M` 113 → 90 | −12,336 | pulls detail off the near field, which the brief protects. Declined |
| band-keyed error (free, no pin) | 315,604 → 297,940 = 99.3% | passes by 0.7%; too thin to be a fix |
| per-patch with no collision floor | 269,812 = 89.9% | breaks `drum_walk`'s "stand on the ground you can see". Declined |

## Frames — all Forward+ / Vulkan 1.4.318, grepped from each render log

Before rendered from a `git worktree` at `4877736` (verified: no `PATCH_LOD_ERR_MM`), after from
the working tree. Only `station/drum_ground.py` differs on the drum's geometry path;
`render_shot.gd` also differs but only in `_mount_vista`, which returns immediately for a shot
with no `room` key — "vista" appears 0 times in both logs.

| | before | after | pixels moved >2/255 |
|---|---|---|---|
| wide, down the axis | `docs/budget-4r-drum-before-axis.png` | `docs/budget-4r-drum-after-axis.png` | 12.29%, mean \|Δ\| 1.06/255 |
| **half distance** (`--fov 24`) | `docs/budget-4r-drum-before-half.png` | `docs/budget-4r-drum-after-half.png` | 13.38%, mean \|Δ\| 1.09/255 |
| **the near field** (4 m, the 4r camera) | `docs/budget-4r-drum-before-near.png` | `docs/budget-4r-drum-after-near.png` | 10.59%, **max Δ 35/255, only 0.245% move >8** |
| **THE WORST EYE ITSELF** (270°, 5132 m) | `docs/budget-4r-drum-before-worst.png` | `docs/budget-4r-drum-after-worst.png` | 14.44%, 2.19% move >8 |

**The worst-eye pair is the strongest evidence in this session** and it was rendered last, to
close the gap that the other two framings look down the axis from arable ground while the gate's
worst eye is a street in the drum's town. Godot's own `scene.json` reports
**`"triangles": 315604`** for the before frame and **`"triangles": 290164`** for the after —
the budget number, confirmed by the engine rather than by a Python count. The terraced blocks,
their lit window bands, the lamp posts, the hedge line, the tree scatter, the core tube, the
guideway truss and its light run, and the settlement climbing the far wall are all unchanged.
The only visible difference is the far side of the barrel at 600 m+, where the arable patchwork
shades very slightly flatter.

## Other gates, checked because a change that fixes one gate by breaking another has fixed nothing

* `station/density.py` — **127/129 locations at or above the floor**, unchanged, and the drum's
  own row *improves*: `the_garden` (module `interior`, scored from `drum_parts` at
  `DRUM_EYE`) goes **gdi 1.857 → 1.878 PASS**, 300,012 → 276,396 triangles. Fewer, larger far
  triangles cost the assemblage almost no visible line length. All five places on module
  `interior` and all six drum rows PASS.
* `station/drum_walk.py --selftest` — **23/23**, `max -97.8 mm` identically before and after,
  `within the render's own lod0 radius (198 m, 92 casts): 0.000 um`.
* `station/occluders.py` — **9/9**, plus the new `--drum` measurement.
* `station/drum_dressing.py` — **277/277**, up from 276/277.

Every feature survives at both framings: the near tree, the copse scatter, the crop rows and
furrows, the hedgerow, the settlement blocks climbing both walls, the guideway light runs, the
core, the end cap. The diff map at ×8 gain is black except faint texture noise on the ploughed
field beyond ~450 m.

Geometric proof for the near field, which is stronger than the picture: at both the near eye and
the budget gate's worst eye, **every patch whose nearest point is inside 449.7 m keeps its
level exactly** (0 coarser, 0 finer), and inside the 198 m lod0 radius `drum_walk` measures
**0.000 µm** between collision and render.

## What I found wrong in the repo, and in the brief

1. **`station/lod.py`'s screen model is a camera nobody ships** — `FOV_DEG = 50.0`, no
   provenance, while `player.gd:279` sets `_cam.fov = 70.0` and `budget.DECK` states 70.0 with
   `shipped_camera()` re-reading player.gd so it *cannot* drift. Every LOD ladder in the project
   is therefore resolving to **1.00 px** of deviation against a stated **1.5 px** budget. Worth
   **26,552 triangles** on the drum alone. Patch in `PATCHES-4r-drumbudget.md` §2, deliberately
   not applied — the blast radius is every LOD chain in the project and I cannot measure it here.
2. **`garden.townscape` is the only thing standing on the drum floor with no LOD ladder** —
   51,026 triangles, 17.6% of the drum frame, drawn at full detail from **526–629 m**, where
   `drum_dressing` draws an equivalent object at its third rung. §3.
3. **`_representative_patches()` understates as well as overstates.** Per-patch stride-8 error
   reaches 1.974 m where the representative maximum is 1.048 m — so the "one sample per band,
   take the max" pattern was wrong in *both* directions, and the correction adds triangles to
   the roughest patches while removing them from the smoothest.
4. **`station/generated/scene/drum/scene.json` was on disk in the `--omit dressing` state** —
   167,680 tri, 8 parts, no dressing, and an `out_png` pointing into another session's
   scratchpad. That is precisely the trap `export_scene.omit_parts`' own docstring warns about
   ("it leaves the scene in the omitted state, which the selftest reads"), still sitting there
   from 4q. My renders rebuilt it; it now reports 9 parts, `omitted []`.
5. **`drum_walk.py:998`'s comment says "the tile reaches 250 m".** 250 m is the nearest edge;
   the tile is 5 × 5 patches and its corner is at **449.7 m**. I used the corner, which is the
   conservative reading, but a future change sized against the comment would coarsen ground a
   player can stand on.
6. **`budget.py` prints "headroom: 9,836 triangles"** beside a stated **13.6% lattice error**.
   The margin is smaller than the stated error, which reads as a comfortable pass and is not
   obviously one. INV-542 settles it with a 168-eye sweep (0 eyes over 300,000) — but the
   printout should point at that rather than leave the reader to notice.
7. **INV-501's own numbers do not reconcile.** It states the lattice error as *"256,144 against
   305,536 — 16.2%"*, and the drum's worst eye at the time was recorded as 315,604 in STATE.md
   §24.9 and 315,364 by the agent that measured it. Three totals for one measurement. The brief
   quotes a fourth figure, **15.8%**, for the same lattice error.
8. **The brief says `station/occluders.py` is "630 lines"; it is 955** (1,114 after this
   session). It grew in 4o when the occluder reached the engine.
9. **My in-progress `station/drum_ground.py` and `station/occluders.py` were both swept into
   commits by another agent's staging** (`0d9e94a`, `d3acc9a` — "WIP SNAPSHOT … NOTHING HERE IS
   VERIFIED"). Nothing broke, and I checked: the worktree I took the "before" frames from was
   created *before* the first of those and provably had no `PATCH_LOD_ERR_MM` in it. But had
   the snapshot landed twenty minutes earlier, my "before" baseline would silently have been my
   own "after". This is CLAUDE.md's session-4e finding recurring: **`git add -A` is not
   disjoint**, and the cost lands on whoever is holding the A/B.
10. **An unmeasured lever, flagged rather than taken:** `drum_ground.sample()` costs
    **172.7 µs/call** and `_fnv1a` is **60%** of it; `_unit(*key)` is a pure function of an
    integer lattice key and is not memoised. That is the cost centre behind the 51 s
    `--derive-patch-lod`, the 10 s-per-eye LOD resolution, and every drum build in the project.
    Not touched, because CLAUDE.md's `ring_radii` lesson says a `cProfile` attribution on a
    call-heavy workload has to be arbitrated by wall clock in a **cold** process before anyone
    believes it, and that measurement was not in this session's budget.
