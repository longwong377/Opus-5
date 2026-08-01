# STREAMING — the station stops being one file

Session 4g. `godot/scripts/stream.gd`, and the changes in `godot/scripts/walk.gd`
that use it.

## What this closes

`walk.gd` took ONE `--glb` and loaded it whole. So the largest continuously
walkable piece of Babylon 5 was one z-cluster of one deck — 773,172 triangles,
65 MB, loaded synchronously — and at its edge there was nothing. `station/budget.py`
already said so, in the `when=` clause of its own resident-triangle check:

> *"walk.gd loads one .glb whole -- there is no streaming and no LOD"*

When this session started, `station/routes.py --report` put the station in **85
foot-connected pieces**. By the time the gate below ran, the connective geometry
had landed in the same tree and it reads:

```
  places      128 located, in 96 z-clusters over 71 decks and 5 sectors
  COMPONENTS, with only what can be built today: 1
     largest piece holds 172 cluster(s), 0 pieces hold one
```

**That makes this more necessary, not less.** One walkable component of 96
z-clusters, at the 773,172 triangles and 65 MB this cluster measures, is on the
order of **74 million triangles and 6 GB** — **412x**
`budget.CELLS["resident_tris"]`. The corridors that join the station are exactly
what makes loading it whole impossible. This is the second file, and the
ninety-sixth.

---

## 1. The residency numbers, and where each came from

**Neither is written down in either `.gd` file.** Both are read at run time and
the manifest records the file each came from, so a residency radius cannot drift
away from the geometry it is derived from.

| number | value | source |
|---|---|---|
| **radius** — inside this a cell MUST be resident | **66.1 m** | `station/generated/cell_manifest.json` → `deck_table[blue.ring_1.d0].sight_line_m`, which `station/interior.sight_line(r_floor, corridor_width)` computes as `2*sqrt(r_o² − r_i²)` — the chord tangent to the inner wall, past which the ring's own curvature occludes |
| **ceiling** — how much may be resident | **180,000 tri** | `station/budget.py` → `CELLS["resident_tris"]`, annotated there as *"the cell you are in plus both neighbours"* |
| **nominal cell count** | **3** | `CELLS["resident_tris"] / CELLS["cell_tris"]` = 180,000 / 60,000 |
| **free radius** (hysteresis) | **73.8 m** | `cell_length_m` for this deck — derived below |
| **cells in flight at once** | **2** | `nominal − 1`: walking forward one cell at a time, at most two cells can need loading simultaneously. More in flight would not make the third cell arrive sooner, it would make the second arrive later |

### They agree, and that is the check

A canonical cell on Blue ring_1 deck 0 is **20.0°** = **73.8 m** of run, and
73.8 > 66.1. So *"everything within a sight line"* and *"the cell you are in plus
both neighbours"* — one derived from curvature, one from triangles — land on the
**same three cells**. Worked through explicitly, with `u` the player's offset into
their cell and `L` = 73.8, `S` = 66.1:

```
d(i)   = 0                    always resident
d(i+1) = L − u ≤ S            resident once u ≥ 7.7 m
d(i−1) = u     ≤ S            resident while u ≤ 66.1 m
d(i+2) = 2L − u ≤ S           needs u ≥ 81.5 m — impossible
d(i−2) = u + L  ≤ S           impossible
```

Maximum want set: **3**.

### Where the free radius comes from, and what it cost to get wrong

The deadband exists so a body standing on a boundary cannot make a cell load and
unload on alternate frames. **It is bounded above by one cell length**, because
`d(i±2)` is never less than `L`: any free radius above `L` holds a cell the player
has walked past and can no longer see. So the free radius is the largest deadband
that cannot admit a fourth cell — **`max(sight_line, cell_length)` = 73.8 m** —
leaving **7.7 m** of hysteresis, which at `player.gd`'s `sprint_m_s = 8.0` is
**0.96 s**, two orders of magnitude more than the measured 10.8 ms activation.

The first version of this file used `radius + one cell = 139.9 m` with the
plausible-sounding justification *"one cell is the granularity of the thing being
freed"*. The gate caught it immediately:

```
free_m=139.9   resident_max=4   resident_tris_max=113,619   frees=1
free_m=73.8    resident_max=3   resident_tris_max= 85,676   frees=3
```

A fourth cell, resident for most of every cell traversal, that the want set never
asked for and the budget still pays for. **A rationalisation that sounds like a
derivation is not one; the number that decided it was `resident_max`.**

### When they disagree, correctness wins and it says so

If the sight line demands more triangles than the budget allows, `stream.gd` keeps
the cells and counts `over_budget_frames`, because dropping a cell the player can
see is a pop and going over budget is a frame cost. **On the real deck it does
disagree** — see §6.

---

## 2. Asynchronous, and verified asynchronous

`ResourceLoader.load_threaded_request` does the read and the mesh construction on a
worker thread; `load_threaded_get_status` is polled once per physics frame and
`load_threaded_get` takes the result. On the main thread there is only instancing,
`create_trimesh_collision`, the material bind and the fittings — and **at most one
cell is activated per frame**, so the hand-off cannot stack. Measured worst
activation: **10.8 ms**.

### It cannot be done with a `.glb`, and that is why cells are `.scn`

`ResourceLoader` has no runtime glTF format loader. A `.glb` outside `res://` is
not a Resource to it, and one inside `res://` needs the editor import step.
`walk.gd::_load_glb` uses `GLTFDocument.append_from_file`, which is **synchronous**
and is the hitch. So a cell is baked to a `.scn`, which `ResourceLoader` loads from
an **absolute path off `res://`** — verified with a throwaway probe before any of
this was written, not assumed:

```
probe: save rc=0 -> /home/user/Opus-5/station/generated/scene/deck/cells/probe.scn
probe: ResourceLoader.exists=true
probe: LOADED after 1 polls
probe: instantiate -> Cell child=deck_panel
PROBE OK
```

---

## 3. What a streamed cell keeps

`walk.gd` must not be able to tell the difference between a streamed cell and a
monolithic `.glb`, so the bake preserves the two things that matter:

* **Every mesh keeps its SOURCE GROUP NAME.** `dress_scene.gd` matches material
  rules against `mi.name`; renaming anything would put every streamed surface on
  the glTF fallback. Verified in the run log: `23 materialled` of 23 groups per
  corridor cell, `0 group(s) on the glTF fallback`.
* **The collision proxy gets the trimesh colliders and the visual mesh gets
  none**, exactly as `_load_level` does it, for the reason `station/collision.py`
  states: the render corridor carries a 66 mm lighting channel down its centreline
  and a capsule dropped on that wedges on an internal edge.

The dresser is **kept alive** across cells rather than released after one bind —
it holds the instantiated `interior.tscn` that owns the material table, and a cell
arrives every few seconds. `walk.gd::_prepare_dress` is split out of `_dress_level`
for exactly this; the monolithic path still releases immediately.

---

## 4. The cell manifest

`station/generated/scene/deck/cells/cells.json`. JSON, GDScript-readable, paths
relative to the manifest's own directory so the set can move.

```json
{
  "version": 1, "kind": "ring",
  "source": {"glb": "...", "collision": "...", "sector": "blue",
             "ring_index": 0, "deck_index": 0, "label": "Blue 1 deck 0"},
  "cell_deg": 20.0, "floor_r_m": 211.55,
  "corridor": {"r_floor_m": 211.558, "z0": 7464.0, "z1": 7465.0,
               "z_mid": 7464.5, "arc_deg": 204.9, "width_m": 2.598},
  "residency": {"radius_m": 66.1, "radius_from": "...",
                "free_radius_m": 73.8, "free_from": "...",
                "resident_tris": 180000, "cell_tris": 60000,
                "cells_resident_nominal": 3, "cell_length_m": 73.8},
  "cells": [
    {"id": "blue_0_0_z7440_c04", "index": 4,
     "mesh": "blue_0_0_z7440_c04.scn", "collision": "blue_0_0_z7440_c04_col.scn",
     "arc": {"r_m": 211.55, "a0_deg": 80.0, "a1_deg": 100.0,
             "z0": 7429.43, "z1": 7466.56},
     "aabb": {"pos": [...], "size": [...]},
     "tris": 28468, "col_tris": 204, "groups": 23,
     "spawn": [0.0, 211.36, 7464.5]}
  ]
}
```

**The distance metric is the arc, not the AABB.** A 20° cell's world AABB is a
145 × 145 m box whose nearest corner is nothing a player can walk to; the number
that decides residency is how far they would have to WALK. Cells carrying an `arc`
block use exact arc distance; anything else (an axial run, a z-cluster) falls back
to AABB distance, so the format already covers what R1's connective corridors will
produce.

**The corridor position is MEASURED, not asserted.** A ring corridor sweeps in
angle at fixed z and its width lies along the station's z axis, so on this cluster
the corridor is a 2.5 m strip at z ≈ 7464.5 and everything from z 7429 to 7463 is
the *rooms* hanging off it. The bake finds it by bucketing the collision shell's
floor triangles by z and taking the buckets that cover the whole arc:

```
bake: corridor MEASURED at r=211.56 m, z=[7464.00,7465.00] (mid 7464.50),
      covering 204.9 deg of arc -- the only floor that runs the whole run
```

The mid-z of a cell's bounding box would have been **7447**, which is inside a
docking bay. A body spawned there is a body spawned in the wrong place.

The corridor **width** (2.598 m) is recovered from the deck row's own two numbers
rather than restated — `sight = 2*sqrt(r² − (r−w)²)` inverts to `w` exactly — and
is what sets the steering lookahead in the gate: `sqrt(r·w)` = 23.4 m, the length
whose chord sags exactly `w/8` = 0.32 m off the arc. Aim further and a body walking
a curved corridor walks the chord and grinds the inner wall.

---

## 5. The bake

Cells are cut on **the station's own cell grid**: `interior.deck_cell` defines cell
`i` of a deck as the arc `[i·cell_deg, (i+1)·cell_deg]` from 0°, and `cell_deg`
is read from `cell_manifest.json`, never passed in. So a cell baked out of a
cluster carries the same id and the same arc as a cell a generator will one day
emit directly.

**Triangles are assigned, never cut.** Each goes whole to the cell its centroid
falls in, so the union of the cells is the source mesh *exactly* — the bake cannot
introduce a gap at a boundary, and a hole in the floor at a cell edge can only mean
the neighbour is not resident. That is the property the gate depends on, and it is
asserted: the bake fails if the cells do not sum to the source.

```
bake: Blue 1 deck 0 -- cell_deg=20.000 (18 cells round the ring), floor_r=211.55 m,
      sight_line=66.1 m, kit cell=26560 tri  [../station/generated/cell_manifest.json]
bake: budget cell_tris=60000 resident_tris=180000 -> 3 cells resident  [../station/budget.py]
bake: loaded in 924 ms -- 509 visual meshes, 4 collision meshes
bake: split in 2433 ms -- 11 visual cell(s), 11 collision cell(s)
  cell 01   20.00- 40.00 deg   115412 tri    510 col tri  144 groups    6.7 MB
  cell 02   40.00- 60.00 deg   246920 tri   1390 col tri  264 groups   14.3 MB
  cell 03   60.00- 80.00 deg    28492 tri    204 col tri   23 groups    1.7 MB
  cell 04   80.00-100.00 deg    28468 tri    204 col tri   23 groups    1.7 MB
  cell 05  100.00-120.00 deg    28716 tri    202 col tri   23 groups    1.7 MB
  cell 06  120.00-140.00 deg    27943 tri    206 col tri   23 groups    1.6 MB
  cell 07  140.00-160.00 deg    27473 tri    202 col tri   24 groups    1.6 MB
  cell 08  160.00-180.00 deg    28576 tri    206 col tri   24 groups    1.7 MB
  cell 09  180.00-200.00 deg    28928 tri    202 col tri   24 groups    1.7 MB
  cell 10  200.00-220.00 deg   107714 tri    601 col tri  144 groups    6.3 MB
  cell 11  220.00-240.00 deg   104530 tri    493 col tri  141 groups    6.1 MB
bake: 11 cells, 773172 triangles total (source had 773172), 44.8 MB, 2909 ms
```

Command:

```bash
GODOT=/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
"$GODOT" --headless --path godot res://scenes/walk.tscn -- --bake-cells \
  --glb=station/generated/scene/deck/blue_0_0_z7440.glb \
  --collision=station/generated/scene/deck/blue_0_0_z7440_col.glb \
  --sector=blue --ring-index=0 --deck-index=0 --cell-id=blue_0_0_z7440 \
  --cells-out=station/generated/scene/deck/cells
```

**This is a bridge and it says so.** In production a cell should be written by the
generator that knows what is in it; the exact patch is in §7. Until then this is
how real station geometry becomes streamable cells without a second description of
the station. The bake takes **2.9 s** and needs no Python.

---

## 6. THE GATE

*A body walks from one cell into the next, the next cell is resident before the
body reaches it, and the body never leaves the floor.*

Headless, on real physics frames, driven by the same `player.gd::step` a keyboard
drives — in the style of `walk.gd`'s existing `--walk-test` and of
`station/walkable.py`. It reports **metres traversed and frames spent off the
floor**, not "did it move".

```bash
GODOT=/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
CELLS=station/generated/scene/deck/cells/cells.json

# the gate
"$GODOT" --headless --path godot res://scenes/walk.tscn -- --cells=$CELLS \
  --stream-test --gravity-mode=drum --settle=120 \
  --start-cell=4 --dir=+1 --traverse=2000

# the control -- MUST fail
... --start-cell=4 --dir=+1 --traverse=2000 --no-stream

# the second control -- turn round with a load in flight
... --start-cell=4 --dir=+1 --traverse=2000 --turnaround=700 --stream-lag=360
```

### The run, as it happens

```
stream: 11 cells, radius 66.1 m (cell_manifest.json deck_table[blue.ring_1.d0].si),
        free at 73.8 m, budget 180000 tri = 3 cells, 2 in flight
stream: +blue_0_0_z7440_c04  28468 tri, 1 col mesh, 23 materialled, 11.3 ms, lead primed,  resident 1 (28468 tri)
walk:   STREAMED level -- start cell 4, primed in 15 ms, spawn 0.00,211.36,7464.50,
        corridor r=211.56 z=7464.50 w=2.60, lookahead 23.4 m (chord sag 0.32 m)
stream: +blue_0_0_z7440_c03  28492 tri, 1 col mesh, 23 materialled,  7.7 ms, lead 36.9 m, resident 2 (56960 tri)
stream: +blue_0_0_z7440_c05  28716 tri, 1 col mesh, 23 materialled,  8.7 ms, lead 36.9 m, resident 3 (85676 tri)
walk:   settled at 0.00,211.53,7464.50 (drop 0.168 m), on_floor=true, in cell 4, walking +angle
stream: -blue_0_0_z7440_c03  resident 2 (57184 tri)
stream: +blue_0_0_z7440_c06  27943 tri, 1 col mesh, 23 materialled, 12.5 ms, lead 66.0 m, resident 3 (85127 tri)
stream: -blue_0_0_z7440_c04  resident 2 (56659 tri)
stream: +blue_0_0_z7440_c07  27473 tri, 1 col mesh, 24 materialled,  8.8 ms, lead 66.0 m, resident 3 (84132 tri)
```

### The verdicts, verbatim

**THE GATE** — bare corridor, cell 4 → 5 → 6:

```
STREAMTEST mode=stream ok=true start=4 dir=+1 prime_ms=15 traverse_m=140.00
  floor_m=140.00 net_m=137.46 offfloor=0/2000 crossings=2 entered=4,5,6 late=0
  min_lead_m=36.92 min_lead_frames=641 cells=11 resident_max=3
  resident_tris_max=85676 budget_tris=180000 radius_m=66.1 free_m=73.8
  loads=5 frees=2 double_loads=0 abandoned=0 over_budget_frames=0
  max_activate_ms=12.5 lag_frames=0 why=-
```

**140.00 m walked, 140.00 m of it on the floor, 0 of 2,000 frames off it, two
cell boundaries crossed, and every cell was resident 36.9 m — 641 frames, 10.7
seconds — before the body reached it.** Three cells resident at 85,676 triangles
against the 180,000 budget. Five loads, two frees, no cell loaded twice.

**THE CONTROL — `--no-stream`. It fails, and it must:**

```
STREAMTEST mode=nostream ok=false start=4 dir=+1 prime_ms=16 traverse_m=11712.57
  floor_m=37.61 net_m=11681.40 offfloor=1463/2000 crossings=1 entered=4,5 late=1
  min_lead_m=-1 min_lead_frames=-1 cells=11 resident_max=1
  resident_tris_max=28468 ... loads=1 frees=0
  why=1_cell(s)_entered_before_resident;1463_frame(s)_off_the_floor;
      streaming_disabled_(this_is_the_control_and_MUST_fail)
```

The body walks **37.61 m**, reaches the edge of cell 4, and falls off the end of
the world — 1,463 of 2,000 frames off the floor, and the log says why in words:

```
walk: ENTERED blue_0_0_z7440_c05 AND IT WAS NOT RESIDENT
      -- the body is standing where the floor has not arrived
```

**AND THIS CONTROL JUSTIFIES THE METRIC.** Its path length is **11,712 m**. A gate
reporting "metres travelled" would have scored the broken configuration as walking
eleven kilometres — it is *falling*, at 7.6 m/s² of ring gravity, for twenty-four
seconds. `floor_m` — 140.00 against 37.61 — is the number that separates them.

**THE SECOND CONTROL — turn round with a load in flight:**

```
walk: TURNED ROUND at frame 820, 1 cell(s) in flight
STREAMTEST mode=stream ok=true start=4 dir=-1 ... floor_m=140.00 net_m=42.07
  offfloor=0/2000 crossings=3 entered=4,5,4,3 late=0 min_lead_m=19.98
  resident_max=3 loads=4 frees=2 double_loads=0 abandoned=1 lag_frames=360
```

The body walks out into cell 5, reverses while cell 6's load is in flight, and
comes back through cell 4 into cell 3. **`double_loads=0`** — nothing was requested
twice, including cell 3, which had been freed on the way out and was legitimately
re-requested on the way back. **`abandoned=1`** — cell 6 finished loading after the
body had left its sight line and was dropped rather than instanced.
`ResourceLoader` has no cancel; this is what "survives" means.

*Note the lead: **19.98 m**, against 36.92 m unlagged. The 6-second artificial load
lag ate 17 m of the margin and the gate still passes — which is roughly the honest
size of the headroom.*

### And a run through the heavy cells, because the bare corridor is the easy case

Cells 1 → 2 → 3, where cell 2 is the docking-bay bulk at 246,920 triangles:

```
STREAMTEST mode=stream ok=true start=1 dir=+1 prime_ms=53 traverse_m=140.00
  floor_m=140.00 net_m=137.46 offfloor=0/2000 crossings=2 entered=1,2,3 late=0
  min_lead_m=36.92 resident_max=3 resident_tris_max=390824 budget_tris=180000
  loads=4 frees=1 double_loads=0 over_budget_frames=2110 max_activate_ms=122.9
```

It still passes the walkability claims — 140 m on the floor, nothing late, nothing
off the floor — and it reports two real problems, which is the point of not hiding
them:

1. **`resident_tris_max = 390,824` against a 180,000 budget: 2.17x, for 2,110 of
   2,110 frames.** The streamer refuses to drop a cell the player can see, so this
   surfaces as a number instead of as a pop. It is a **content** fact, not a
   streaming one: an assembled 20° cell here is 28,500 tri of bare corridor and
   115,000–247,000 tri where there are rooms, against `CELLS["cell_tris"] = 60,000`.
   The bare-corridor cells land at 28,500 against `interior.ring_cells`' own
   prediction of **26,560** — 7% out, which is the props and the door leaves — so
   the *model* is right and the *rooms* are four times their allowance.
2. **`max_activate_ms = 122.9`** (122.9–135.2 over four runs). Instancing,
   colliding, materialling and lighting the 247,000-triangle cell costs ~130 ms on
   the main thread — eight frames at 60 Hz, a visible hitch. The bare corridor
   cells cost **8–15 ms**, which is fine. The threaded half is fine at both sizes;
   the hand-off is not, for cells this big. See "not done" below.

### What is NOT done, stated

* **A streamed cell's doors, inhabitants, crowd and interactables are not wired.**
  `walk.gd::_wire_doors` / `_wire_people` / `_wire_interact` run once, over a
  monolithic scene, at start-up. For streaming they have to run per cell as it
  arrives and be torn down with it. The collision proxy carries the door panels, so
  in a streamed build today **the pressure doors are solid** — the busy run walked
  the corridor past them without being blocked, but it could not have gone through
  one.
* **No LOD.** `station/generated/lod_manifest.json` exists and nothing reads it. A
  cell is loaded at full density or not at all, so the sight line is doing the work
  a LOD ladder should share.
* **The 135 ms activation is not amortised.** One cell per frame is the right
  granularity for 28,000 triangles and the wrong one for 247,000; the fix is to
  spread instancing, collision and lighting across frames within a cell, which
  needs the activate step to become a resumable job.
* **One cluster is baked.** The manifest format and the streamer are cluster-count
  agnostic — `cells.json` is a flat list keyed by id — but there is exactly one
  built `.glb` pair in `station/generated/scene/deck/` today, so the gate walks 11
  cells of one deck. §7 P4 is how that becomes 90.

---

### The monolithic path still works

`walk.gd` was changed, so the build it already produced has to be shown intact.
Same `.glb` and collision proxy the cells were cut from, same spawn, the
**original** `--walk-test`, nothing streamed:

```
dress: 509/509 meshes MATERIALLED, 0 group(s) on the glTF fallback
dress: 561 light sources at energy 3.00 from {"customs_light_strip": 3,
       "light_downlight": 489}, 2 casting shadows
walk:  4 collision meshes (proxy), 509 visual meshes (no collision)
walk:  3 doors wired
walk:  73 people wired of 73 in the cast list
walk:  12 interactables wired, 11 pressable (operate:5/read:4/serve:2/tread:1)
WALKTEST rest=0.000,211.526,7464.500 on_floor=true fell=false moved_1s=4.200
  drop=0.166 legs=0.70/4.20/0.73/4.20 traverse_m=41.93 net_m=41.86 offfloor=0/600
```

Materials, lights, doors, cast, interactables and the walk itself: unchanged. The
only structural edit on that path is that `_dress_level` now calls the extracted
`_prepare_dress()` instead of building the dresser inline.

---

## 6b. What I found in files I could only read

1. **`station/budget.py`'s streaming sentence is now false**, and its
   resident-triangle check measures the wrong subject. See P3.
2. **`station/export_gltf.py::load_obj_groups` merges every span of one group NAME
   into a single mesh.** `blue_0_0_z7440.obj` has **7,870 `g` spans and 509
   distinct names**, so the `.glb` arrives as 509 nodes each spanning the whole
   759 m of corridor. This is why the bake splits at **triangle** level and not at
   instance level: binning by node would have put the entire corridor in one cell.
   The collision proxy is worse — **4 nodes for 4,420 triangles**, one of them the
   whole shell. `dress_scene.gd` already records the same finding from the other
   end (832 downlights arriving as one mesh).
3. **The built cluster is 5.9x longer than the walk that tests it.** Blue 0/0
   z7440's corridor runs **204.9° = 759 m** (measured off the collision proxy);
   `walkable.TRAVERSE_FRAMES = 1800` at 4.2 m/s walks **126 m** of it, and always
   the same 126 m from the same spawn. 83% of the built corridor has never had a
   body on it. Streaming does not fix that — a longer traverse or several spawns
   would.
4. **`interior.ring_cells`' triangle model is good.** It predicts **26,560 tri** for
   a bare 20° cell of this deck; the assembled bare cells measure **27,473–28,928**,
   7% out, the difference being props and door leaves. The model is not what is
   over budget; the rooms are.
5. **`station/routes.py`'s docstring restates a number the module computes**, and
   during this session it went stale twice: the prose said *"128 locations → 96
   FOOT-CONNECTED COMPONENTS ... the largest walkable piece of Babylon 5 holds
   six"* while `--report` was already printing **1 component holding 172
   clusters**. Prose that repeats a computed number will always drift — the same
   defect as the cached collision total and the committed frames. It should read
   the number it prints, or not state one.

---

## 7. CHANGES I NEED IN FILES I DO NOT OWN

### P1 — `station/walkable.py`: run the gate

**This is the one that matters.** A gate that is not in CI is not a gate — session
4e's own finding, one workflow file down. `walk.gd --stream-test` is the mechanism;
this is the command that drives it and its controls and decides pass or fail.

```python
# --- add near the other module constants -----------------------------------

# STREAMING -- can a player walk OUT of one cell and INTO the next.
# Everything else in this file measures one piece of the station in isolation;
# this measures the join. See docs/streaming-4g.md.
STREAM_CELLS = os.path.join(ROOT, "station/generated/scene/deck/cells/cells.json")
# Where the gate walks: cell 4 is bare corridor, so a failure is streaming
# rather than a doorway. --traverse 2000 frames at 4.2 m/s is 140 m, which
# crosses two cell boundaries at this deck's 73.8 m cell.
STREAM_ARGS = ["--start-cell=4", "--dir=+1", "--traverse=2000"]
# Two cell lengths less a margin. A run that crosses one boundary and stops has
# not shown the hand-off repeats.
MIN_STREAM_FLOOR_M = 100.0


def _stream_run(godot, extra, timeout=900):
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--", f"--cells={STREAM_CELLS}",
           "--stream-test", "--gravity-mode=drum", "--settle=120"] + list(extra)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    m = re.search(r"STREAMTEST (.+)", out)
    if not m:
        return {"error": "no STREAMTEST verdict printed"}
    d = {}
    for tok in m.group(1).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d


def bake_cells(godot, sector="blue", ring=0, deck=0, z_m=7440, timeout=900):
    """Cut a built cluster into streaming cells -- godot/scripts/stream.gd.

    THE SPLIT LIVES IN THE ENGINE AND MUST NOT BE COPIED HERE. A cell has to be
    a resource `ResourceLoader` can load on a worker thread, which is a .scn,
    which nothing outside Godot writes -- so a Python re-implementation would be
    a second description of one cut, which is hard rule 4's failure mode.
    """
    if os.path.exists(STREAM_CELLS):
        return 0
    stem = f"{sector}_{ring}_{deck}_z{int(z_m)}"
    src = os.path.join(ROOT, "station/generated/scene/deck")
    if not os.path.exists(os.path.join(src, stem + ".glb")):
        print(f"  no built cluster at {stem}.glb -- run "
              f"`python3 station/walkable.py --deck {sector}/{ring}/{deck}` first")
        return 2
    return subprocess.run(
        [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
         "res://scenes/walk.tscn", "--", "--bake-cells",
         f"--glb={os.path.join(src, stem + '.glb')}",
         f"--collision={os.path.join(src, stem + '_col.glb')}",
         f"--sector={sector}", f"--ring-index={ring}", f"--deck-index={deck}",
         f"--cell-id={stem}", f"--cells-out={os.path.dirname(STREAM_CELLS)}"],
        timeout=timeout).returncode


def stream_gate(godot):
    """A body walks out of one cell and into the next, and the next one is
    THERE BEFORE IT ARRIVES. With the control that must fail."""
    if bake_cells(godot) != 0:
        print("  FAIL  could not bake streaming cells")
        return 1
    sub = _stream_run(godot, STREAM_ARGS)
    if "error" in sub:
        print(f"  FAIL  {sub['error']}")
        return 1
    good = (sub.get("ok") == "true"
            and float(sub["floor_m"]) >= MIN_STREAM_FLOOR_M
            and int(sub["crossings"]) >= 2
            and int(sub["late"]) == 0 and int(sub["offfloor"].split("/")[0]) == 0
            and float(sub["min_lead_m"]) > 0.0
            and int(sub["double_loads"]) == 0)
    print(f"  {'PASS' if good else 'FAIL'}  a body walks "
          f"{float(sub['floor_m']):.1f} m ON THE FLOOR across "
          f"{sub['crossings']} cell boundaries, {sub['offfloor']} frames off "
          f"it; every cell was resident {float(sub['min_lead_m']):.1f} m before "
          f"the body reached it; {sub['resident_max']} cells resident, "
          f"{int(sub['resident_tris_max']):,}/{int(sub['budget_tris']):,} tri")

    # THE CONTROL, and without it this proves nothing. With streaming off the
    # start cell is primed and no other cell is ever requested: the body must
    # reach the boundary and fall off the end of the world.
    ctl = _stream_run(godot, STREAM_ARGS + ["--no-stream"])
    fell = ("error" not in ctl and (int(ctl["late"]) > 0
            or int(ctl["offfloor"].split("/")[0]) > 0))
    if not fell:
        print("  FAIL  with streaming DISABLED the body walked just as far -- "
              "this test is measuring nothing")
        good = False
    else:
        print(f"        control: with streaming off the body walks "
              f"{float(ctl['floor_m']):.1f} m and spends {ctl['offfloor']} "
              f"frames off the floor. (Its path length is "
              f"{float(ctl['traverse_m']):,.0f} m -- it is FALLING, which is "
              f"why the metric is metres on the floor and not metres.)")

    # AND THE PLAYER TURNS ROUND MID-LOAD. Lagged on purpose: at this box's
    # natural speed a cell finishes inside one physics frame, so the in-flight
    # window is never open when the body reverses and the requirement cannot
    # fail. No cell may be requested twice.
    trn = _stream_run(godot, STREAM_ARGS
                      + ["--turnaround=700", "--stream-lag=360"])
    if "error" in trn or int(trn["double_loads"]) > 0:
        print(f"  FAIL  turning round mid-load double-loaded "
              f"{trn.get('double_loads', '?')} cell(s)")
        good = False
    else:
        print(f"        control: the body turns round with a load in flight -- "
              f"{trn['abandoned']} cell(s) abandoned, {trn['double_loads']} "
              f"double loads, {trn['offfloor']} frames off the floor")
    return 0 if good else 1


# --- add to main()'s argument list -----------------------------------------
    ap.add_argument("--stream", action="store_true",
                    help="can a player walk out of one cell and into the "
                         "next? Bakes cells if they are missing, then runs "
                         "the gate and its two controls")

# --- add to main(), immediately after the `godot is None` guard ------------
    if a.stream:
        return stream_gate(godot)
```

### P2 — `.github/workflows/validate.yml`: one step

Same shape as every other step (`continue-on-error: true` plus an `id`, so the
final aggregate step still fails the job) — the 4e rule that one failing gate must
not blind the ones behind it.

```yaml
      # THE STATION IS BIGGER THAN ONE FILE. Every walkability gate above loads
      # ONE .glb whole and measures inside it, so none of them can fail for the
      # station being 85 disconnected pieces. This one walks a body OUT of a
      # cell and INTO the next and checks the next one arrived first, with a
      # control that turns streaming off and must fail.
      - name: The station streams
        id: sthe_station_streams
        continue-on-error: true
        run: python3 station/walkable.py --stream
```

### P3 — `station/budget.py`: the sentence is now false, and so is the subject

`CELLS`'s resident-triangle check currently reads:

```python
    check("resident triangles", len(tris), CELLS["resident_tris"], " tri",
          "walk.gd loads one .glb whole -- there is no streaming and no LOD",
```

Two things:

1. **The `when=` string is out of date.** There is streaming now (there is still
   no LOD). Suggested: `"the resident set is now streamed -- godot/scripts/stream.gd
   keeps three cells; there is still no LOD"`.
2. **`len(tris)` is the wrong subject.** It is the whole cluster, which is no longer
   what is resident. The honest measurement is the worst RESIDENT SET, which the
   cell manifest now makes computable without an engine:

```python
def worst_resident(manifest="station/generated/scene/deck/cells/cells.json"):
    """The heaviest three consecutive cells -- what a player actually holds."""
    import json
    cells = json.load(open(manifest))["cells"]
    by_i = {c["index"]: c["tris"] for c in cells}
    return max((sum(by_i.get(i + k, 0) for k in (-1, 0, 1)), i)
               for i in by_i)
```

On the current bake that returns **390,824 tri at cell 2**, against the 180,000
budget — 2.17x, and see §6 for why that is a content fact rather than a streaming
one.

### P4 — `station/deck.py`: nothing, deliberately

The obvious patch is "make `deck.py --sweep` write the cells". **Do not copy the
split into Python.** A cell has to be a resource `ResourceLoader` can load on a
worker thread — a `.scn` — and nothing outside Godot writes one, so a Python
re-implementation would be a second description of one cut and would drift.

What `deck.py --sweep` *should* gain is a call OUT to the existing bake, once per
z-cluster, after it writes that cluster's `.glb` and `_col.glb`:

```python
        # after the cluster's glb pair is written
        if args.cells:
            walkable.bake_cells(godot, sector, ring, deck, z_m=z)
```

with the 90 per-cluster `cells.json` files merged into one station manifest. The
merge is a list concatenation — cell ids are already unique because they carry
their cluster's stem — and `stream.gd` needs no change to consume it: it already
keys everything by `id` and falls back to AABB distance for any cell that carries
no `arc` block, which is what an axial connecting run will produce.
