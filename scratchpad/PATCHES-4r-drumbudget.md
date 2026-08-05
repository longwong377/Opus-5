# Session 4r — the drum's triangle budget: patches for files I do not own

I own `station/occluders.py`, `station/drum_ground.py`, `station/drum_dressing.py` and new
files under `station/`. Everything below is in a file I do not own. Each item states what to
change, what it is worth **measured**, and what would break.

Nothing here is required for the drum to pass its gate — it already does, at
**290,164 / 300,000 = 96.7%**, on `station/drum_ground.py` alone. These are the next levers,
with the measurements already taken so the next session does not have to repeat them.

---

## 1. `tools/export_scene.py` — `DRUM_CALIBRATION`'s measured pixel contributions are now stale

**MANDATORY, and it is a consequence of my change rather than a suggestion.**
`DRUM_CALIBRATION[...]["contribution"]` records the fraction of pixels each drum part
contributes, obtained by rendering a framing twice and diffing — measured in 4q as
**39.08 / 32.30 / 47.26%** for `dressing` across the three drum framings.

**The drum's ground now renders 26.4% fewer triangles at the worst eye** (96,320 → 70,880) and
6.6% fewer at `--stand 20,4700` (280,874 → 262,442 for the whole shot). The dressing and the
fixed parts are untouched, so every `contribution` row's *denominator* moved and the ground's
own row moved most.

**What to do:** re-run the contribution measurement with `omit_parts` for each row. **Do not
hand-edit the numbers.** Note `omit_parts`' own recorded trap: it leaves the scene on disk in
the omitted state, so the last export must be a whole one or the calibration check reports
`gone [...]`.

**What it is worth:** nothing in triangles. It is a correctness debt: those rows are cited as
measurements and would otherwise be measurements of a build that no longer exists.

---

## 2. `station/lod.py` — the LOD chain resolves detail for a camera nobody ships

**The single biggest remaining lever on the drum, and it is a correctness fix, not a quality
cut.**

`station/lod.py:158` sets `FOV_DEG = 50.0` under the heading "The screen model", with no
provenance. `station/drum_ground.py:203` mirrors it and says so; `station/drum_dressing.py`
takes it from `drum_ground`. Meanwhile:

| where | vertical FOV | authority |
|---|---|---|
| `godot/scripts/player.gd:279` | **70.0** | the camera a player is actually given |
| `station/budget.py` `DECK["fov_v_deg"]` | **70.0** | stated, INV-083, and `shipped_camera()` re-reads player.gd so it cannot drift |
| `station/lod.py` `FOV_DEG` | **50.0** | — |

`budget.shipped_camera()` returns `{'fov_deg': 70.0, 'fov_src': 'player.gd'}` today. Godot's
`Camera3D.fov` is vertical at the default `keep_aspect = KEEP_HEIGHT`, verified in the engine
and recorded in `budget.py`'s own docstring.

**Why the direction matters.** `switch_distance(e) = e · SCREEN_H / (2·tan(fov/2)·PIXEL_BUDGET)`.
A narrower calibration FOV means more pixels per degree, means a larger switch distance, means
**more triangles**. Calibrating at 50° while shipping 70° delivers
`1.5 × tan(25°)/tan(35°) = 1.00 px` of deviation where the project's stated budget is **1.5 px**.
The chain is spending triangles on error nobody asked for and nobody can see. Correcting it
preserves the stated invariant exactly, by definition.

**Measured worth, on the drum, on top of everything that landed this session:**

| | worst-eye frame | ground |
|---|---|---|
| shipped today | 290,164 (96.7%) | 70,880 |
| + screen model at 70° | **263,612 (87.9%)** | **45,344** |

**The patch** — one constant, and a citation instead of a bare number:

```python
# station/lod.py, replacing line 158
# FOV IS READ OFF THE SHIPPED CAMERA, not chosen. `godot/scripts/player.gd`
# line 279 sets `_cam.fov = 70.0`, and Godot's Camera3D.fov is VERTICAL at the
# default keep_aspect = KEEP_HEIGHT. `station/budget.py::shipped_camera()`
# already re-reads that file for exactly this reason; this is the same value
# from the same place. It was 50.0, with no provenance, which resolved every
# LOD ladder in the project for a longer lens than ships and therefore
# delivered 1.5 x tan(25)/tan(35) = 1.00 px of deviation against a stated
# 1.5 px budget.
FOV_DEG = 70.0
```

and, in `station/drum_ground.py` (mine, and I will apply it the moment `lod.py` moves —
I have deliberately NOT applied it alone, because `lod.py`'s own comment says
*"drum_ground.py mirrors the value and says so, so changing it here silently would
desynchronise two chains"*, and desynchronising them from the drum end is the same defect
from the other side):

```python
FOV_DEG = lod.FOV_DEG          # not 50.0 restated
```

**What would break, stated honestly.** Three things, none of them the drum:

1. **Every other LOD ladder in the project** switches ~33% closer — hull LODs, greebles,
   `station/lod.py`'s own schedules. That is *correct* at the shipped camera and it is not
   measured here. It needs its own before/after frames; do not land this on the drum's
   evidence.
2. **The drum SCREENSHOT lens is 46°** (`scene.json`'s camera) and the rubric's half-distance
   frame is rendered at **24°**. At those lenses a chain calibrated for 70° shows
   `1.5 × 70/24 = 4.4 px` of deviation rather than 1.5. That is inherent to a static offline
   chain plus a zoom lens, and the right resolution is that the *game* camera is the authority
   and screenshot lenses are a separate judgement — but it should be said out loud in the
   entry, not discovered in a judge's frame.
3. `station/drum_walk.py:998` reads `dg.lod_table()[1]["switch_distance_m"]` as its lod0
   radius. At 70° that drops 198 m → 132 m, which **shrinks** the radius its strong check
   covers. Harmless (a smaller identical-surface claim), but the number in its comment goes
   stale.

---

## 3. `station/garden.py` + `tools/export_scene.py` — the townscape has no LOD ladder at all

**The structural finding of this session, and it is where the remaining money is.**

At the budget gate's worst eye the drum's **fixed** parts are **104,374 triangles — 36.0% of the
frame — and not one of them has an LOD ladder.** `drum_ground` resolves the ground per patch,
`drum_dressing` resolves 1,945 features across four rungs and solves its own switch scale by
bisection, and then:

| part | tri | LOD | distance from the worst eye |
|---|---|---|---|
| **townscape** (`garden.townscape`) | **51,026** | **none** | **526–629 m, median 575 m** |
| core | 13,340 | none | — |
| trams | 12,624 | none | — |
| guideways | 11,796 | none | — |
| endcaps | 15,072 | none | — |
| spokes | 516 | none | — |

The townscape is twelve buildings and ten trees in one 300 m stretch of one settlement band
(`garden.settlement_arcs()` → 93.6–144° and 259.2–302.4°). From (270°, 5132 m) it is a median
**575 m** away, and `drum_dressing.switch_distances()` is `[113, 362, 1017] m` — an object of
that kind at 575 m is drawn by `drum_dressing` at **level 2**, its third rung. The townscape is
drawn at level 0 from anywhere in the drum.

**Measured worth:** deleting the townscape entirely takes the worst eye from 290,164 to
**239,138 (79.7%)**. A three-rung ladder of `drum_dressing`'s own ratios would recover most of
that gap without removing a building.

**The patch, in shape rather than in full** (it is a real piece of work, not a one-liner):

```python
# station/garden.py
def townscape(schema, profile, sector=None, angle_deg=112.0, z_m=4900.0,
              blocks=12, trees=10, seed="garden", near=True, level=0):
    """...  `level` indexes drum_dressing.LOD_RATIOS' rungs; 0 is what ships today."""
```

and in `tools/export_scene.py::drum_parts`, replacing the unconditional call:

```python
    # The townscape stands on the drum floor like everything else and is
    # LOD-resolved against the same eye, for the same reason.
    import drum_dressing as dd
    tc_centre = <world point of (angle_deg, z_m)>
    lvl = dd._level(math.dist(tc_centre, eye), dd.switch_distances())
    v, t, spans = gd.townscape(schema, profile, sector, level=lvl)
```

**Two things to get right, both of which this project has been bitten by:**

* `garden.townscape` returns `(verts, tris, SPANS)` where every other part returns
  per-triangle groups, and `drum_parts` expands the spans and **asserts no triangle is in no
  span**. A level parameter must keep that assertion true, or triangles silently take the
  fallback material (session 4f).
* `drum_dressing.TOWNSCAPE_KEEPOUT_DEG/M` keeps the dressing out of the townscape's footprint.
  If the townscape gets a coarse rung, the keep-out must not — a coarse town with no dressing
  in it is a hole, not a saving.

**What would break:** `docs/engine-4q-drum-dressed.png` and every drum frame that has the
townscape in it, at distance. Take before/after at the wide framing *and* at the rubric's half
distance with the town in frame, which the two framings used this session do not have
(`--stand 20,4700 --look 20,6300` looks down the axis away from both settlement arcs).

---

## 4. `station/budget.py` — nothing needs changing, and two comments are now stale

The gate passes as written. Two lines will read oddly to the next person:

* `drum_section`'s docstring ledger quotes **288,060** as "what the shot builds"; it is now
  **290,164** at the worst eye (it grew during 4q and shrank in 4r). It is history and marked as
  such, but worth a dated line.
* the printed headroom line now reads *"headroom: 9,836 triangles across 4.5 million m² — for
  ground detail, buildings, trams and vegetation"*. That is a **9,836-triangle** margin against
  a **13.6%** stated lattice error, which reads as comfortable and is not. INV-542 measures the
  true margin with a 168-eye sweep (0 eyes over) — the sentence should point at it.
