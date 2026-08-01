# The lift — `station/lift.py`, session 4g

Written by the agent that built `station/lift.py`. It holds the declared extrapolations that
module rests on (hard rule 1), the defects it found in files it could only read, and the exact
patches it needs applied in files it does not own.

`canon/INVENTIONS.md` is owned by the main agent this session, so the entries below are staged
here in that file's format and numbered `LIFT-1 … LIFT-5` rather than `INV-nnn`, to be merged
with real numbers. Nothing here is canon; every entry is authority 5.

---

## 0. What was missing, measured

`station/routes.py --report`, before this module existed:

```
lift     0 buildable of 38   <- 38 edges with NO GENERATOR
```

and the edge's own reason string:

> *no lift, stair or shaft exists anywhere in the project — transit.py computes the ride,
> navigation.py routes NPCs through it, and there is nothing to walk into*

That was literally true. Four modules model a lift:

| module | what it already computed about lifts |
|---|---|
| `station/transit.py` | `spoke_line()` — a `spoke_lift` line with a Coriolis speed cap, a round trip, a headway and *"the worst wait on the station"*; `climb_leg()` |
| `station/npc/navigation.py` | `lift_ride_s()`, `SHAFT_TARGET_HEADWAY_S`, `_shaft_headway_s`, `lift:` nav nodes with boarding, dwell and per-deck rides |
| `station/directory.py` | `lifts`, `bay_elevators`, `radial_tubes`, `transfer_systems`, `drum_spokes` — five registered places whose declared interacts are `lift_call` / `lift_door` |
| `docs/gazetteer/LOCATIONS.md` | *"Transport tubes / lifts (between levels)"*, authority 3 |

None of them had a shaft to run in. `station/interior.py` stacks a dozen decks per ring at
`DECK_PITCH_M = 3.6 m` **in radius**, and there was no geometry joining two of them.

---

## LIFT-1 — The car's clear width is the corridor's, measured

**Invented:** in `station/lift.py::shaft_geometry` — `clear_w = 2 * corridor_profile()['half_w']`
= **2.1612 m**, and `clear_h = ceil_y − floor_y` = **2.8070 m**.

**Why necessary:** the reference set contains **no frame of a Babylon 5 lift car interior at all**.
`canon/00-MASTER.md` §3 says so in as many words — *"the lift-car display is still the single
highest-value gap in the reference set"* — and what it is missing there is the LEVEL numbering, not
the car. There is no width, no height, no plan and no photograph. The alternative to extrapolating
is a station whose decks cannot be walked between, which `routes.py` prices at 38 broken edges.

**Constrained by:** the only thing that has to be true of a lift is that it takes what reaches it.
The corridor's clear cross-section is already MEASURED off the kit by ray casting in
`collision.corridor_profile` — 1.0806 m half-width at the portal pinch, 2.807 m of headroom — and
anything that fits that pinch has to fit the car, or the lift is a bottleneck a player meets by
being unable to bring something through. Taking the same cast rather than a second number is hard
rule 4: if the kit's walls move, the car moves with them.

**What this rules out:** a car sized off a real-world lift standard. A 1.1 × 1.4 m domestic car
would be **narrower than the corridor that feeds it**, and a station moving 250,000 people does not
build one.

**What would overturn it:** one frame of a B5 lift interior with a person in it. It would replace
the value outright.

---

## LIFT-2 — The car is square in plan

**Invented:** `clear_d = clear_w`. The car is 2.1612 m in both horizontal directions.

**Why necessary:** LIFT-1 fixes the width from the corridor's own pinch. Nothing fixes the depth:
the corridor constrains what can be *presented* to the door, not how deep the box behind it is.

**Constrained by:** a lift lobby meets a car at 90 degrees. The longest rigid object that can be
brought to the door is set by the corridor's clear width, and a car shallower than it is wide
cannot accept what the corridor delivers — it fails on the diagonal. A square is the smallest plan
that can. It is also the plan that makes the shaft's two pairs of guide faces interchangeable,
which is why real shafts are close to square.

**What this rules out:** the shallow, wide car of a passenger lift in a tower, which is optimised
for a queue and not for freight; and the deep, narrow car of a service lift, which cannot turn a
stretcher. `directory.py` gives the `lifts` place the functions `("transit",)` with no cargo
qualifier, and `bay_elevators` — the only lift the sources describe at all — is explicitly a
**cargo** lift with a stated length limit, so the general case has to pass both people and goods.

**What would overturn it:** any frame showing a car's plan, or a production drawing.

---

## LIFT-3 — The car shell is two of the kit's own thicknesses

**Invented:** the car's floor and roof are `PROVISIONAL['ceiling_slab_m']` = **0.18 m**; its side
and back panels are `PROVISIONAL['door_leaf_t_m']` = **0.10 m**.

**Why necessary:** the external envelope decides whether the car fits the shaft and whether its
roof fouls the landing above, so it cannot be left unstated.

**Constrained by:** the split is structural rather than stylistic. The floor and roof carry the
car and its load and take the kit's only *slab* figure; the side panels carry nothing and take the
kit's only figure for a **moving** panel, the door leaf. Both are already `PROVISIONAL` and both
move if C-004 moves, so the car inherits whatever resolving that conflict does to the corridor
rather than needing a second correction.

**The consequence is checked, not assumed:** external height = 2.807 + 2 × 0.18 = **3.167 m** in a
**3.600 m** storey, leaving **433 mm** between the car roof and the next floor. If that number went
negative the shaft would be a one-storey lift with extra doors, and `_selftest` gates it.

**What would overturn it:** C-004 resolving to a deck pitch under 3.17 m, which would force a
lower car; or any frame of a car interior.

---

## LIFT-4 — The running clearance is the guideway's, reused

**Invented:** `RUN_CLEARANCE_M = interior.GUIDEWAY_SOFFIT_RELIEF_M` = **0.15 m** between the car
and every fixed surface of the shaft, and `SILL_GAP_M = PROVISIONAL['wall_seam_m']` = **0.038 m**
between the car's sill and the landing's.

**Why necessary:** a shaft with no stated clearance is a shaft whose car interferes with its own
walls, and the failure is invisible until something moves.

**Constrained by:** this project already states exactly one running clearance between a moving
vehicle and the fixed structure it passes — `GUIDEWAY_SOFFIT_RELIEF_M`, which is why the guideway
soffit sits inboard of the bottom chord's running face so *"a car meets the same surfaces inside
the portal that it meets everywhere else on the run"* (INV-050). A lift car in a shaft is the same
problem at a smaller scale. Taking a second figure would be two descriptions of one thing, which
this repository has now been bitten by twice — the door decision made in the render and again in
the shell, and the corridor profile written down instead of measured.

The sill is deliberately **not** given the running clearance: a sill is the plate a foot crosses
and is meant to run close. The kit already states how wide a gap between two plates that must not
touch is — `wall_seam_m`, the 38 mm recess between deck tiles and between wall plates. 38 mm is
also under `collision.floor_holes`' own 0.35 m sampling pitch, i.e. it is not a hole a body can
fall through, and the threshold walk gate measures the actual widest unsupported run at **40 mm**.

**What would overturn it:** a stated lift specification, or a frame showing the gap at a landing.

---

## LIFT-5 — The shaft is a rectangular box, and its local frame is orthonormal

**Invented:** the shaft is a straight-sided box of constant section, not a radial wedge; the guide
rails are `interior_kit.pilaster` at `pilaster_proj_m` = 0.17 m off each tangential wall.

**Why necessary:** `deck._place_local` maps room-local coordinates through `a = a0 + x / radius`,
which makes a room's walls **radial planes**. That is right for a room, whose floor follows the
ring. Applied to a shaft 10.7 m deep in radius it would taper the section by 10.7/211 = **5.1%**,
from 2.661 m at the bottom landing to 2.526 m at the top, and a lift car cannot run in a taper.

**Constrained by:** guide rails have to be parallel — that is what a guide rail is. So `place()`
in `lift.py` is a rigid rotation (tangential, inward-radial, axial), right-handed with determinant
+1 so every winding decision made in local coordinates survives the map into world space.

**The price is stated and measured.** The car's floor is then a PLANE and the deck's is a
CYLINDER, so they can agree at only one point. Over the car's own 2.1612 m width at r = 210.9 m the
divergence is **2.77 mm**, against `collision.STEP_TOLERANCE_M` of **5 mm** — the tolerance the
project certifies a floor smooth at, itself set below the 22 mm tile lip that stopped a body in
session 3u. The tangency point is the car's centreline, which is where the doorway is, so the
crossing itself is exact. `_selftest` gates the figure rather than asserting the argument.

The rails being `pilaster` is not a shortcut: it is the kit's own vertical member standing off a
wall, it is already a closed solid whose winding `interior_kit._selftest` asserts, and
`materials.py` already binds both `pilaster` and `light_pilaster_strip` — so a shaft needs no new
material and cannot land on the glTF fallback, which is session 4f's finding applied before the
fact rather than after.

**What would overturn it:** a frame showing a B5 shaft interior; a production note describing the
tubes as bores rather than boxes.

---

## 1. What the module is, in one table

Every dimension and where it came from. Nothing in this table was chosen.

| what | value | source |
|---|---|---|
| storey rise | 3.600 m | the DIFFERENCE of two landings' `floor_r_m` from `interior.decks_in_ring`, not `DECK_PITCH_M` restated |
| car clear | 2.1612 × 2.1612 × 2.8070 m | `collision.corridor_profile()`: `2 × half_w`, square (LIFT-2), `ceil_y − floor_y` |
| car external | 2.3612 × 2.3612 × 3.1670 m | + 2 × 0.10 panel, + 2 × 0.18 slab (LIFT-3) |
| shaft bore | 2.6612 × 2.6612 m | car external + 2 × 0.15 running clearance (LIFT-4) |
| landing aperture | 1.50 × 2.10 m | `interior_kit.PROVISIONAL['door_width_m'/'door_height_m']`, through `door_assembly` — the corridor's own door |
| pit / overhead | 0.330 m / 0.150 m | the car's own overhang plus one running clearance |
| shaft depth (3 landings) | 10.667 m | pit + rise + car + overhead, all of the above |
| storey headroom | 433 mm | 3.600 storey − 3.167 car; the number that decides whether the car can serve the landing above |
| ride, 7.2 m | 3.4455 s | `npc/navigation.lift_ride_s`, cross-checked against `transit.climb_leg` |
| Coriolis cap | 3.1345 m/s | `navigation.coriolis_speed_cap`, from `MAX_LATERAL_G = 0.12` |
| threshold divergence | 2.77 mm | measured; `collision.STEP_TOLERANCE_M` is 5 mm |
| widest unsupported run | 40 mm | measured across the threshold; a capsule is 350 mm |

Cost: **2,360 triangles** for a three-landing shaft, **788** for the car, **52** for the collision
shell — 1.7% of the render mesh, the same order as `collision.corridor_shell`'s 1.5%.

---

## 2. FINDINGS IN FILES I COULD ONLY READ

### 2.1 `interior_kit.door_leaf` at `open_fraction = 0.0` is non-manifold — every shut door on the station

`interior.boundary_edges` returns a **pair**, `(open, non-manifold)`, and its own docstring says so.
Nothing in this project gates the second element. Measured:

```
door_leaf bi_parting        open=0.00 : 120 tri, open=0, nonmanifold=4
door_leaf bi_parting        open=0.25 : 120 tri, open=0, nonmanifold=0
door_leaf bi_parting        open=1.00 : 120 tri, open=0, nonmanifold=0
door_leaf horizontal_split  open=0.00 : 120 tri, open=0, nonmanifold=4
```

The two leaves of a **shut** door meet on an exactly coincident face. That is precisely the defect
session 3x rebuilt `portal_frame` for — *"five prisms sharing coincident faces — 828 non-manifold
edges a deck, at the corner a player passes 414 times a lap"* — surviving in the one piece of the
door assembly 3x did not touch. It is four edges per door, at the closed state, which is the state
almost every door on the station is in almost all the time.

### 2.2 And it is not only the leaves. A doorless corridor section carries 268

3x fixed exactly the three pieces it was looking at and the audit was never re-run over the rest of
the kit. Per piece, `interior.boundary_edges` on the piece alone:

| piece | triangles | open | **non-manifold** |
|---|---|---|---|
| `ring_frame(3.0, 0.35, 0.28, segments=16)` | 192 | 0 | **64** |
| `wall_assembly(3.05, 3.0)` | 232 | 0 | **5** |
| `door_leaf(open_fraction=0.0)` | 120 | 0 | **4** |
| `deck_panel(2.6, 1.5)` | 36 | 0 | **2** |
| `portal_frame(2.6, 3.0)` | 56 | 0 | 0 |
| `door_frame()` | 228 | 0 | 0 |
| `bulkhead(chamfered_arch(2.6, 3.0, 0.5))` | 76 | 0 | 0 |
| `pilaster(2.5)` | 112 | 0 | 0 |
| `deck_grid(3.6, 2.6)` | 288 | 0 | 0 |
| `wall_panel(1.3, 2.0)` | 12 | 0 | 0 |
| `handrail(4.0)` | 60 | 0 | 0 |

and assembled:

```
corridor_section(21.6)                          7,096 tri  open=0  nonmanifold=268
corridor_section(21.6, 2 wall doors)            7,496 tri  open=0  nonmanifold=266
corridor_section(21.6, 2 doors, leaves=False)   7,256 tri  open=0  nonmanifold=258
```

The three pieces 3x rebuilt are all at zero and everything it did not look at is not. `ring_frame`
at 64 is the worst per-piece figure in the kit; it is currently unused by `corridor_section` but it
is what the tall volumes are meant to be built on, and `interior_kit._selftest` already instantiates
it — so it is one call away from shipping.

**Why no gate caught it:** `interior_kit._selftest` asserts `signed_volume > 0` and, since 3x, open
edges. A closed solid keeps its signed volume whatever it shares with its neighbour, and coincident
faces are open-edge-free by construction. The measurement was already in the file; only half its
return value is ever read.

### 2.5 `_shell_from_pieces` leaves an unwelded 42 nm crack — on EVERY door on the station

Found by building the case the first version of the gate did not: six landings instead of three.

```
blue ring 1, 140 deg, z 6880, interior.boundary_edges open count
   2 landings  0      5 landings  0
   3 landings  0      6 landings  6   <- appears here
   4 landings  0      7..12       6   <- and never grows
```

Not accumulation, and **not a hole**. The surface is closed; it is not welded. Two vertices stand
where there should be one, 4.2e-8 m apart:

```
local (0.9840000000, 1.8969260000)     <- exactly round(x, 7)
local (0.9840000000, 1.8969259736)     <- the real value
```

**Cause, exactly.** `interior_kit._shell_from_pieces` builds its T-junction point set as

```python
    pts = {_pkey(p) for q in pieces for p in q}      # _pkey rounds to 7 decimals
    pts |= {_pkey(p) for p in extra_points}
    pieces = [_insert_collinear(q, pts) for q in pieces]
```

— coordinates **rounded to 7 decimals** — and `_insert_collinear` appends them **verbatim** into
loops whose own vertices are not rounded, guarded only by

```python
    if math.dist(out[-1], q) > 1e-9:
        out.append(q)
```

`_pkey`'s granularity is 5e-8; that guard is 1e-9. **Fifty times tighter.** So any vertex further
than 1e-9 from its own 7-decimal rounding is inserted a second time, and the neighbouring piece
carries the rounded twin where this one carries the real value.

**Why it looked intermittent, and this is the part worth keeping.** `interior.boundary_edges` keys
on coordinates rounded to **4 decimals** — a deliberate weld, so that "coincident-but-duplicated
vertices" do not read as holes. A 42 nm pair therefore reads as a hole only when it straddles a
0.1 mm grid line, which depends on **where in the station the geometry sits and on nothing else.**
Measured, same code, same landing counts, unwelded:

| position | near-duplicate pairs | open edges |
|---|---|---|
| blue ring 1, 140°, z 6880 | 2,464 | **6, at heights 6–12** |
| grey ring 1, 40°, z 3618 | 2,464 | **0, at every height** |

Identical cracks; different answers. **A closure gate that answers differently for the same code
depending on position is worse than one that fails**, because it cannot be believed in either
direction.

**How widespread.** Near-duplicate vertices, measured per piece:

| piece | near-duplicate vertices |
|---|---|
| `bulkhead(any section)` | 16 |
| `door_frame()` | 16 |
| `corridor_section(21.6, 2 doors)` | 56 |
| one lift landing | 102 |

Every door on the station has it. It is invisible today because `boundary_edges` welds at 0.1 mm
and float32 export welds harder still — but it splits smoothing groups, and it is why the only
closure measurement this project has cannot be trusted at a new position.

**What `station/lift.py` does about it:** `weld()` merges vertices closer than `WELD_TOL_M = 1e-6`
in the shaft's own local frame, before the rigid map to world. One micrometre is 24× the 4.2e-8
divergence and 38,000× smaller than `wall_seam_m`, the smallest real feature in the kit — and the
gate is not the tolerance but the consequence: **the weld must drop zero triangles.** Merging two
genuinely distinct vertices has to collapse a triangle, so a dropped triangle is the tolerance
being too big, said by the data. Over the 2..28 sweep it drops none and merges 102 vertices a
landing.

Snapping to the first vertex within tolerance, not rounding: rounding has the identical failure one
decimal down.

### 2.6 `at_deck` is not a key once a shaft crosses a ring — six of eighteen landings

Found by building the coordinator's `stack=` case rather than by reading it. `deck_index` restarts
at 0 in every ring, so a column over blue rings 0 and 1 has eighteen landings numbered

```
[0, 1, 2, 3, 4, 5,  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
 ring 0 (6 decks)   ring 1 (12 decks)
```

`_landing` returned the first match. **Six of eighteen landings were unaddressable, and the car
parked 21.6 m from where it was asked to** — silently, and no gate could fail for it, because a car
at the wrong landing is a perfectly good car at a perfectly good landing. Measured: 12 of 18
landings had a floor under the car; the other 6 had the shaft.

**Fixed in `station/lift.py`,** and it is not a raise, because raising would have broken
`spoke_way.py`'s `at_deck=0` mid-build. A shaft's address space is its **landings**; a deck number
is only a *name* for one, and it stops being a name when it repeats. So `_landing` resolves:

* a landing dict from `g["landings"]` — always unambiguous, and what to pass across a ring;
* an int while `g["deck_keys_unique"]` — the deck number, **unchanged** for every caller that
  predates `stack=`, gated as a bijection on a single-ring shaft;
* an int when it is not — the landing `index` from the bottom, which is the only naming left.

`g["deck_keys_unique"]` states which reading is in force **before** the call and both builders
report `meta["at_landing"]` after it. `spoke_way.py` needed no change: `at_deck=0` still resolves to
the bottom landing, and its other seventeen now resolve to seventeen distinct landings instead of
eleven.

### 2.3 `corridor_section` turns its two wall doors opposite ways

Read while working out how to place `door_assembly` in a shaft wall, and not verified by rendering,
so it is offered as an observation rather than a finding.

`corridor_section` places a wall door with `_merge(..., _rot_y(90.0 * side), (side * (w/2 + setback), 0, c))`.
`_rot_y(90)` maps local `(x, y, z) → (z, y, −x)` and `_rot_y(−90)` maps it to `(−z, y, x)`. So the
door's local **+Z** — the face `door_frame` puts its head indicator and its control panel 50 mm
proud of — points **into** the corridor on one hand and **away from** it on the other. If that is
right, the door on the −1 hand shows its indicator and reader to the room rather than to the
corridor. A frame taken square-on at a doorway on each hand would settle it in one look.

### 2.4 What this cost me, and why the bore gate is written the way it is

The first version of `lift.py` placed the landing `door_assembly` the natural way up, and
`door_frame`'s head indicator and control panel — both 50 mm proud of its −z face — landed **inside
the shaft bore**, 12 vertices in the volume the car sweeps through, at every landing. Every
dimensional figure still read 150 mm clear, because the arithmetic never knew the fitting was there.

So the gate that catches it asks the question of the EMITTED VERTICES and not of the arithmetic:
`swept_intruders(g, verts)` counts how many points of the shaft stand inside the box the car body
sweeps. Its negative control is a shaft built with `relief_m = −0.20`, which puts 977 of 1,630
vertices in the car's path.

---

## 3. CHANGES I NEED IN FILES I DO NOT OWN

None are required for `station/lift.py` to work; it passes 37/37 against the files as they stand.
Both are defects in read-only files that the module's own gates uncovered.

### 3.1 `station/interior_kit.py` — separate the shut leaves so they do not share a face

The two leaves meet exactly at the aperture centreline at `open_fraction = 0.0`. The fix that
matches this kit's existing idiom is `door_frame`'s own — *"the outer band starts inside the reveal
rather than exactly on it, so the two rings overlap rather than meeting on a shared face"*. A shut
door should close on a **seal**, not on a coincident plane, and the kit already has a number for the
gap between two plates that must not touch.

In `door_leaf`, wherever the two leaves' meeting edges are computed, inset each leaf by half of
`p["wall_seam_m"]` (0.019 m) at the closing edge — or, equivalently, drive them from
`open_fraction` never quite reaching 0. I have deliberately **not** written the patch line-for-line
because I did not read `door_leaf`'s body closely enough to be sure which of its several bars is
the meeting one, and a patch I cannot test is worse than a described one.

**The test to add, in `interior_kit._selftest`, which is the part I am confident about:**

```python
    # NON-MANIFOLD IS THE OTHER HALF OF boundary_edges' RETURN VALUE AND
    # NOTHING READS IT. Session 3x rebuilt portal_frame for exactly this and
    # the audit was never run over the rest of the kit: ring_frame 64,
    # wall_assembly 5, door_leaf(shut) 4, deck_panel 2, corridor_section 268.
    # A coincident face is geometry nobody can see and a depth-sort coin toss.
    for name, piece in (
            ("ring_frame", ring_frame(3.0, 0.35, 0.28, segments=16)),
            ("deck_panel", deck_panel(2.6, 1.5)),
            ("wall_assembly", wall_assembly(3.05, 3.0)),
            ("door_leaf shut", door_leaf(open_fraction=0.0)),
            ("portal_frame", portal_frame(2.6, 3.0)),
            ("door_frame", door_frame()),
            ("bulkhead", bulkhead(chamfered_arch(2.6, 3.0, 0.5)))):
        _open, nonman = boundary_edges(*piece)
        assert not _open, f"{name} has {len(_open)} open edges"
        assert not nonman, f"{name} has {len(nonman)} non-manifold edges"
```

It fails today on the first four, which is the point.

### 3.2 `station/interior_kit.py` — close the 42 nm crack at the source

`station/lift.py` welds its own output, so it no longer carries §2.5. Every other door on the
station still does. The fix is one line, in `_shell_from_pieces`: put the loops on the same grid as
the point set they are being merged against, instead of only the point set.

```python
     pieces = [_ensure_ccw(q) for q in pieces]
+    # THE LOOPS GO ON THE SAME GRID AS THE POINTS INSERTED INTO THEM. `pts` is
+    # built with `_pkey`, i.e. rounded to 7 decimals, and `_insert_collinear`
+    # appends those rounded coordinates into loops whose own vertices are not
+    # rounded -- so a vertex further than the dedupe guard (1e-9) from its own
+    # rounding (5e-8) lands twice, 4.2e-8 apart, and the two pieces either side
+    # of that seam stop sharing an edge. 16 such pairs in every `bulkhead` and
+    # every `door_frame` on the station.
+    pieces = [[_pkey(pt) for pt in q] for q in pieces]
     pts = {_pkey(p) for q in pieces for p in q}
-    pts |= {_pkey(p) for p in extra_points}
+    pts |= {_pkey(p) for p in extra_points}
```

Equivalently, widen `_insert_collinear`'s guard from `1e-9` to `_pkey`'s own granularity — but
snapping the loops is the version that cannot drift, because it makes the two sources of a vertex
literally the same number rather than merely close.

**The test to add**, which fails today and passes after:

```python
    # NO TWO VERTICES OF ONE PIECE MAY STAND 42 nm APART PRETENDING TO BE ONE.
    # `boundary_edges` welds at 4 decimals, so it reports this as a hole only
    # when the pair straddles its grid -- which depends on where in the station
    # the geometry sits. Asked here in the piece's own frame, where the answer
    # does not depend on position.
    for name, piece in (("bulkhead", bulkhead(chamfered_arch(2.6, 3.0, 0.5))),
                        ("door_frame", door_frame()),
                        ("corridor_section", corridor_section(21.6,
                                                              doors=((5.0, -1),)))):
        v = piece[0]
        seen, bad = {}, 0
        for pt in v:
            k = tuple(round(c, 4) for c in pt)
            if k in seen and 1e-12 < math.dist(pt, seen[k]) < 1e-4:
                bad += 1
            else:
                seen.setdefault(k, pt)
        assert not bad, f"{name} has {bad} near-duplicate vertices"
```

### 3.3 `station/collision.py` — nothing

`corridor_profile`, `cast`, `write_obj` and `STEP_TOLERANCE_M` were all sufficient through the
public surface. `_quad` was **copied with attribution** rather than imported, so `collision.py`
needs no change and owes this module no promise.

---

## 4. What is NOT done

- **No engine frame.** Every craft claim in this project has to cite a Godot + lavapipe frame at
  the rubric's half distance (`CLAUDE.md`, layer-2 lesson). Rendering one needs
  `station/export_scene.py` and `station/materials.py`, which this agent does not own, and the
  session's rule was to stay off the cores while other agents ran. **So nothing here is a craft
  claim.** The shaft's articulation — plate courses at `wall_plate_l_m` with `wall_seam_m` joints,
  bullnose guide rails with segmented light strips, a landing sill, a lit car with handrails on
  three faces and a car operating panel — is *present and measured*, and has not been *looked at*.
- **Nothing calls it.** `station/deck.py` does not place a lift; `station/routes.py` names it as
  the lift edge's generator. Wiring it into deck assembly is the assembler's job and both files
  are owned elsewhere.
- **The car does not move.** It is emitted parked at a named landing and its travel axis is
  reported in `meta["travel_axis"]`; there is no runtime.
- **The kit's crack is closed here and not at the source.** `station/lift.py` welds; every other
  door on the station still carries §2.5. §3.2 has the one-line patch.
- **`density.py` has not scored it.** The shaft is 2,360 triangles over roughly 113 m² of visible
  surface; whether that clears layer 2b's line-density floor is not something this agent measured.
- **No stair.** `routes.py`'s `lift` edge kind is served; a stair is a different generator and a
  station that loses power needs one.
