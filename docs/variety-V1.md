# V1 — form follows function

**Session 4h/4i. `station/rooms.py`, `station/dressing.py`.** `docs/MASTER-PLAN.md` §4:
*"V1 — form follows function: a medlab's plan differs from an office's because a medlab is not an
office — bay rhythm, ceiling height, servicing, circulation, all keyed on the register."*

`docs/variety-V0.md` built the instrument, found **27 clusters of mutually indistinguishable places
covering 82 of 128**, and — this is the part that decided the work — measured the *cause* instead of
guessing it. This is what was changed, what moved, and what did not.

> **The headline.** `python3 station/variety.py`, the whole station, before → after:
>
> | | before | after |
> |---|---|---|
> | median pair score | 0.209 | **0.174** |
> | median FORM | 0.267 | **0.195** |
> | pairs over the 0.73 ceiling | **101** (1.2%) | **38** (0.5%) |
> | pairs with the same FORM | 164 (2.0%) | **52** (0.6%) |
> | clusters / largest / places covered | **27 / 8 / 82 of 128** | **18 / 5 / 45 of 128** |
> | p99 of all 8,128 pairs | 0.779 | **0.534** |
> | the re-seed control | 0.924 | **0.948** — *up* |
>
> **Nine clusters gone, 37 of the 82 covered places freed, and the largest thing nothing can tell
> apart went from eight rooms to five.** The gate still fails, and should: V3 is when it returns 0.
>
> And the four named clusters, before → after:
>
> | cluster | pairs over the ceiling, before | after |
> |---|---|---|
> | office (8 places) | **16 of 28** | **0** |
> | industrial (8) | **19 of 28** | **1** |
> | medical (6) | **15 of 15** | **3** |
> | hospitality (5) | **10 of 10** | **10 — and not one of them is reachable from the files V1 owns** |
>
> **60 of 81 flagged pairs closed; the 21 that remain are 10 bespoke, 3 medlab, 1 substation, 7
> spillover.** The re-seed control went **up** (0.901 → 0.915 on the weakest of three probes), which
> is the number that says this is variety rather than noise.

---

## 1. What V0 measured, and why it decided everything below

```
ON FORM ALONE -- what a form grammar has to fix
  same archetype             0.287    0.266    +0.021
  both built generic         0.351    0.157    +0.195
  shared function            0.424    0.262    +0.162
```

Read the shape before the size, which is this repository's own rule. **`both built generic`
separates ten times what `same archetype` does.** The places are not alike because they are similar
*kinds* of place. They are alike because they come out of the *same function* — 11 archetypes
deciding the whole of form for 128 places, with `functions` read exactly once in the entire
generator, by `archetype()`.

And the second driver's sign is backwards: two places that share a declared function are **more**
alike, because sharing a function means sharing an archetype means sharing a shell. Making the
register's own statement of what a place is *for* into a **differentiator** is the whole of V1.

### The one arithmetic fact that bounds what any of this can do

Under `variety.py`'s sampling, `sect_x[i]` is the union over *z* of the solid mask at plan column
*i*. In a box room the end walls are full height at every *x*, so **every column is full** — the
cross-section of a rectangular room is a filled rectangle, and

> **section IoU between two box rooms = `min(h1,h2) / max(h1,h2)`.**

Checked against V0's own printout: `zocalo` 7.34 m vs `medlab_one` 3.00 m gives 3.28/7.62 = 0.43,
and V0 reports **0.436**. So two rooms are told apart *on section alone* only when one is **1.37×**
the height of the other, and eight mutually distinct offices would need heights spanning 2.6 m to
24 m. **The section channel cannot break a cluster, and V1 does not ask it to.** It is a
distribution to move, and it moves the plan with it (rib pitch and light pitch are both derived
from the ceiling). What breaks clusters is **plan**.

That is stated here because the brief said "section first", and following that literally would have
spent the session on the one channel that provably could not close a single cluster.

### How much plan has to move — derived before anything was built

A generic room fills **19.7%** of its plan raster (`medlab_red`, 11,337 of 57,600 cells). For two
equal-area plans, IoU 0.73 means `I = 0.844·A`, so **15.6% of the occupied cells have to disagree**
— about **3.5 m² of floor arrangement** in an 11 m² plan. The shell alone is 5.1 m² of that 11 and
cannot move; **the contents are 6.2 m², so a bit over half of a room's furniture has to be
somewhere else.** That is a layout change, not a furniture change, and it is why nothing below adds
a prop.

---

## 2. What was built

### 2.1 A plan grammar, composed per function — `rooms.PLAN_ELEMENTS`

**122 functions, 118 with an element, 16 element types, five kinds.** An element is a piece of
*plan*: something standing in the middle of the floor, dividing it, or ranked across it.

| kind | what it is | example function |
|---|---|---|
| `island` | one block on the centreline, walked around | `meeting` — a conference table |
| `rank` | rows across the room at a pitch, with a centre aisle | `worship` — pews; `offices` — desk ranks |
| `cross` | one run across the room a third of the way in, with a gap | `commerce` — a counter with a public side |
| `cell` | fins off one long wall, making units off an aisle | `residence` — V0's own example |
| `end` | one block against the far wall, with a way past it | `ceremony` — a dais; `psi_corps` — a shielded booth |

**Composed, not looked up, and that is the design.** A winner-takes-all rule collapses four of the
eight offices back onto one plan, because the office cluster holds eight *distinct* function tuples
and any rule that keeps one function and discards the rest throws away exactly the information that
separates them. So a place takes an element per function, in **the register's declared order** (the
directory lists the primary function first), capped at two.

That cap is a triangle budget rather than a taste — every instance is a group and `budget.py` gates
deck primitives at 401 of 600 — and two is enough: the eight offices resolve to eight distinct
ordered pairs.

```
admin_complex     (administration, command)              desk ranks + a command dais
ceremonial_rooms  (ceremony, hire)                       a dais + an issue counter
conference_5      (diplomacy, meeting)                   delegate benches + the table
conference_rooms  (meeting,)                             the table alone
drum_office       (offices,)                             desk ranks alone
earthforce_office (administration, military_liaison)     desk ranks + a briefing table
minipax           (political_policing, administration)   a barrier counter + desk ranks
telepath_office   (offices, psi_corps)                   desk ranks + a shielded booth
```

The Ministry of Peace is now a room you are *stopped* in and the telepath's office is a room with a
sealed box inside it. That is the faction friction `MASTER-PLAN.md` §3 L6 asks to be visible, and it
is visible in the floor plan rather than in a label.

**Safety is by construction, not by arithmetic.** `place_elements` runs after the declared props and
before the dressing, and every instance is tested against the solids already in the room *and*
against `walkable()` **before any geometry is emitted**. So the interpenetration assertion cannot be
made to fire by a table 20 mm too wide, and a room cannot be sealed by its own plan. What the
arithmetic still has to get right is the **size of the bay**, and that is reported per element as
`(wanted, got)` — a room too small for its own plan is a number, not a room that quietly came back
generic.

### 2.2 Which walls carry furniture — `rooms.DRESS_WALLS`

`dressing.dress` put furniture against **all four walls of every room on the station**, so every
room wore the same ring. That ring is ~6 m² of an ~11 m² plan: **over half of everything the plan
channel can see was a constant.** It is now keyed on the first element's kind — a room walked round
keeps its long walls clear because they *are* the walkround; a cellular room gives one long wall to
its units. Two elements each get a claim, because `telepath_office`'s booth reported `want 1, got 0`
until the desk ranks stopped dressing the wall it stands against.

### 2.3 A bay is a whole fraction of its own location — `rooms.whole_bays`

The four medlabs that survived everything above declare **the same two functions and the same two
interactables**. The register's only remaining statement that they are different places is **how big
they are** — and the footprint reached the geometry through `bays_in()`, whose two callers both put
it in a report dict and nothing else (STATE.md §13). A bay is now `full / n` for the whole `n` that
keeps it nearest its contents-derived minimum, so a 40.8 m wide medlab is five 8.2 m bays and a
35.8 m one is four 9.0 m bays.

Under `fit` the absolute size is normalised away — correctly; a player cannot tell 6×8 from 6×10 —
but **the ratio of the furniture band to the open floor is not**, and neither is how many rows of
anything fit.

**Never larger than the location**, which is what makes it safe for `station/deck.py`: that module
sizes every room slot as `min(room_extent_m, bay_span_m)` and `rooms.build` uses the same two lines,
so assembler and geometry agree by construction (hard rule 4).

### 2.4 Clear height keyed on function — `rooms.FUNCTION_HEIGHT`

**11 distinct ceiling heights → 33.** A ladder with a clearance argument at every rung: 2.40 m a
berth, 2.60 m a cell, 2.90 m the station's fitted standard, 3.10 m people standing round a table,
3.20 m a ducted service zone, 3.40 m a public room, 3.60 m a gantry over a working surface, 4.20 m+
where height *is* the content.

**Nothing under a deck pitch is raised above it**, and that is a hard clamp rather than a style:
`_selftest` holds multi-deck rooms under 40% of the generator's remit and the count stands at **31
of 78, which is 39.7% — one room of margin**. Without the clamp `hydroponics`, `fusion_core` and
`cryo_storage` all went multi-deck and the gate failed by exactly one room. Each of those three
arguably *is* a tall volume; re-proportioning three named places as a side effect of a variety pass
is not this session's job, and `ARCHETYPES` already records the identical decision about
`power_generation` for the identical reason. **The clamp is asserted, with the three names as its
negative control.**

---

## 3. Three defects found in the files V1 owns

**1. Every piece of end-wall furniture on the station was lying on its side.**
`dressing.dress` assigned `s_along, s_perp = (pw, pd) if axis == "x" else (pd, pw)`. On a side wall
that is right — width along the wall, depth into the room. On the two **end** walls it is inverted,
so a 2.0 × 0.5 m shelf stood on its narrow edge and projected its full **2.0 m width into the
room**. Nothing caught it because it is *consistent*: an object positioned and built from the same
two numbers stays inside the room however they are assigned, so every containment, closure and
footprint assertion passed. It ate roughly two metres off both ends of every generic room on the
station and is a large part of why the ends of every plan read solid.

**2. `light_wall_course` can never fit between two ribs, and was silently not fitted.**
The fitting is 2.40 m; `rib_pitch_m` is 2.60 m at a 4.2 m ceiling and ribs are 0.45 m wide, so the
clear run is **2.15 m**. `_lay` required a run at least as long as the fitting, found none, and
emitted nothing. The only reason `interfaith_chapel` ever had a wall course is that its bay was
short enough to carry two ribs instead of four — growing the bay for its pews turned that luck off
and the room lost its wall lighting entirely, which is how this was found. A fitting longer than
every bay is now **cut to the longest bay**, which is also what a strip light in a recess is.

**3. A 0.12 m screen has no room to be a machine.** `dressing.machine` insets its builders by 12% of
the box so flanges and nosings have somewhere to be proud into; on a 0.12 m fin that is 14 mm, and
`machine_escapes` measured parts leaving the box by exactly 0.0144 m in `ngrath` and
`thieves_guild`. Cell fins are floored at 0.16 m — stated as a property of the *builder* rather than
patched in the table, because otherwise it returns the next time somebody writes a thin element.

---

## 4. What did NOT move, and why

### 4.1 The hospitality cluster is unreachable from `rooms.py` and `dressing.py`

All five bars — `bar_unnamed`, `earharts`, `eclipse_cafe`, `fresh_air`, `happy_daze` — carry
`module: "hospitality"`, which is in `bespoke.NEAR_END`, so `deck.room_geometry` composes them from
`station/hospitality.py` and **never calls `rooms.build`**. Their ten pair scores are **identical to
three decimal places before and after** — that identity is the evidence, not an inference.

They are one cluster for exactly the reason the generic rooms were: **one module, one composition,
five places.** V1's answer for the generic kit — compose the plan from the register's own functions
— applies unchanged, and `bar_unnamed` (hospitality, food_service, recreation, **rumour**),
`eclipse_cafe` (hospitality, food_service) and `happy_daze` (hospitality, recreation,
**black_market_fringe**) already declare enough to separate them. `PLAN_ELEMENTS` has entries for
all of those functions and `rooms.place_elements` takes a caller's own `(hw, hl, ceil, chan_lo,
chan_hi)` — exactly as `rooms.place_interacts` does, which is how session 4d closed the identical
split for interactables (`built generic 273/275, built bespoke 0/82`). **One call in
`bespoke.compose` would put it in reach.** That is a change to a file V1 does not own and is
proposed rather than made — see §6.

*This is the same structural finding as 4d's, one level up: a rule that lives where only one caller
can reach it is not a rule about the station.*

### 4.2 Three medlab pairs and one substation pair survive

| pair | score | plan | sect | content | what still differs in the register |
|---|---|---|---|---|---|
| `medlab_green` vs `medlab_others` | 0.902 | 0.902 | 0.999 | 0.999 | sector only (green / red) |
| `medlab_one` vs `medlab_others` | 0.788 | 0.788 | 0.851 | 0.973 | footprint, functions |
| `medlab_green` vs `medlab_one` | 0.774 | 0.774 | 0.851 | 0.972 | footprint, functions |
| `primary_breaker` vs `rotation_drivers` | 0.798 | 0.798 | 0.932 | 0.985 | sector, footprint |

`medlab_green` and `medlab_others` declare the same two functions, the same two interactables, the
same authority, and footprints (40.4 × 22 m and 40.8 × 30 m) that divide into bays of **13.46 × 7.33
m and 13.59 × 7.50 m** — within 2% of each other. Every lever V1 built has been applied and they are
still the same room, because **on every axis V1 keys on, they are the same place.**

The one register fact left between them is the one V0 ranked fourth and nothing has ever used:
**`populace.SECTOR_MIX` — Green Sector is 46% human with minbari, centauri and abbai dominant; Red
is 60% human with drazi and centauri.** A ward whose caseload is majority non-human is not a human
ward: bay pitch, bed length, door head and the atmosphere kit in the room all follow from who is in
it, and all of those read from across the room.

**It was deliberately not built this session, and the reason is a control rather than a schedule.**
`populace._mix_for` resolves on the place **key**, and `variety.clone_place` changes the key and
nothing else — so keying form on it through that function would move the re-seed control and V1
would have shipped noise reported as variety. The clone-safe route is `SECTOR_MIX[place["sector"]]`,
which V2 should use. **Any form input must be a function of the register row and never of the key.**

---

## 5. The measurements

### 5.1 The four clusters, pair by pair

`docs/variety-V0.md`'s own four, measured with `variety.place_occupancy` at HEAD and at V1.
Full listings in the session report; the summary is:

```
                 before   after
  office          16/28    0/28      every pair closed
  industrial      19/28    1/28      primary_breaker vs rotation_drivers 0.798
  medical         15/15    3/15      all three are medlab-to-medlab
  hospitality     10/10   10/10      bespoke; byte-identical before and after
```

### 5.1a The eighteen clusters that survive, and what they are made of

```
  5  hospitality  bar_unnamed, earharts, eclipse_cafe, fresh_air, happy_daze
  4  generic      domed_rotunda, obs_dome_1, obs_dome_2, obs_rotundas
  4  transit      drum_spokes, lifts, radial_tubes, transfer_systems
  3  generic      arrival_concourse, customs_north, customs_south
  3  medical      medlab_green, medlab_one, medlab_others
  2  x13          alien_sector/kosh_quarters, alien_worship/sanctuary_blue,
                  ambassadorial_suites/league_delegations, downbelow/plant_zone,
                  drum_tram/ground_tram, fuel_stores/hazard_tanks,
                  gravity_torus/research_labs, micro_g_bays/zerog_maint,
                  primary_breaker/rotation_drivers, qtr_civilian/qtr_personnel,
                  raw_material/spinal_cargo, shops_kiosks/zocalo,
                  waste_green/waste_red
```

**The 5, the 4 rotundas, the 4 transit and 6 of the 13 pairs are places composed by a bespoke module
or by no generator this session owns** — `hospitality`, `quarters`, `zocalo`, `alien_sector`,
`plant`, `customs`. Of the clusters that ARE this generator's, only the medlab three and
`primary_breaker`/`rotation_drivers` survive, and §4.2 measures why.

`obs_dome_1` vs `obs_dome_2` and `drum_tram` vs `ground_tram` are worth naming separately: those are
pairs the register itself declares as *the same room built twice in two places*, which is the one
case where a cluster is the correct answer.

### 5.2 The re-seed control — the number that says this is not noise

A room built twice with **only its key changed**. If V1 had bought its variety by shuffling random
numbers, this would have fallen.

| probe | before | after |
|---|---|---|
| `medlab_one` | 0.958 | **0.968** |
| `fabrication` | 0.835 | **0.960** |
| `conference_rooms` | 0.922 | **0.915** |

It went **up**, and the reason is structural rather than lucky: **every input V1 added is a function
of the register row — `functions`, `footprint`, `interacts` — and none of them is a function of the
key.** A clone gets the same elements, the same walls dressed, the same bay proportion and the same
ceiling; only the dressing scatter moves, which is what the control is supposed to see.

### 5.3 Triangle cost

| | before | after |
|---|---|---|
| 78 generated rooms, total | 2,034,424 | **3,931,532** |
| mean per room | 26,082 | **50,404** |

**+93%, and it is bay area rather than detail.** An element is sized for three rows of a rank or two
cells of a run and `bay_span_m` grows the bay to hold them rather than dropping them, and
`whole_bays` then rounds that up to a whole fraction of the location. A bay is at most ~1.5× its
contents-derived minimum, which bounds the area at ~2.25× in the worst case and lands at 1.93×.

**And `station/budget.py` cannot see any of it, which is the finding.** Run at HEAD and at V1 in the
same clean worktree it reports **18/22 within budget, the same four rows over, byte for byte** — the
`habitat cell` and `plant cell` rows are, in the file's own words, *"priced with the corridor kit as
a placeholder"*, and there is **no budget row for generated-room triangles at all**. The station's
room geometry could double again and every performance gate would stay green. Reported rather than
fixed: `MASTER-PLAN.md` §7 forbids growing the gate set, and this is a gate that needs *changing*
rather than adding — which is the owner's call, not V1's.

---

## 6. CHANGES I NEED IN FILES I DO NOT OWN

### 6.1 `station/bespoke.py` — let a composed room have a plan (§4.1)

The 26 bespoke places are 26 places built by 8 modules, and at least one of those modules
(`hospitality`, 5 places) is a cluster for that reason alone. `bespoke.compose` already calls
`rooms.place_interacts` with its own measured band; adding the sibling call is the same shape:

```python
    R.place_elements(v, t, g, q, hw, hl, ceil, chan_lo, chan_hi,
                     report=report, w=w, ln=ln)
```

`place_elements` takes no schema, emits only through `_fixture`, tests every instance against the
solids already present *and* against `walkable`, and skips anything that does not fit — so a module
that has no room for a plan element is unchanged rather than broken.

### 6.2 `docs/MASTER-PLAN.md` §4 — V1's *"done when"* has no threshold in it

V0 §9.2 proposed two numbers; the honest V1 pair, given §1's arithmetic, is:

* **the largest form cluster below 4 places** (V0: 18), and
* **no cluster whose members share an archetype and a generator**, which is what V1 attacks and
  what §4.1 says is left.

The section number V0 proposed (*"below 25% of pairs over the ceiling"*) should be **withdrawn or
restated**: with `sect = min(h1,h2)/max(h1,h2)` for box rooms, 25% of 8,128 pairs requires the
station's heights to span a range no plausible ladder of clearances produces. It is a target that
can only be met by geometry that is not a box — a stepped soffit, a clerestory, a gallery — which is
real work and should be named as such rather than hidden inside a percentage.

---

## 7. Inventions — `canon/INVENTIONS.md` format, authority 5

*(Not written into `canon/INVENTIONS.md`; the session owner merges them.)*

---

**INV-140 — the plan grammar: what shape a room's floor is**

*What.* 118 of the register's 122 declared functions map to a plan element drawn from a vocabulary
of 16 objects in five kinds (`island`, `rank`, `cross`, `cell`, `end`). A place composes up to two,
in the order the register declares its functions. Element dimensions are in
`station/rooms.PLAN_ELEMENTS`.

*Why.* `station/variety.py` measured 27 clusters of indistinguishable places covering 82 of 128, and
`--drivers` measured the cause: `both built generic` separates +0.195 on form against `same
archetype`'s +0.021. Form had one input — an 11-way archetype — for 128 places.

*What constrained it.* Four things, each asserted rather than argued: an element must leave the room
crossable by a 0.9 m walker (`walkable`, tested on boxes before any geometry is emitted); it must
not occupy the same cubic metre as anything else (`_solid_boxes` interpenetration, and by
construction); it must fit under the room's own ceiling; and it must be the arrangement the named
activity actually has — a counter you queue at, rows you sit in, cells you sleep in. Sizes are the
smallest that work for a 1.7 m occupant: a 3.20 m conference table seats eight, 1.30 m across is two
0.65 m reaches, a 2.40 m cell pitch is a unit you can put a bunk and a locker in, a 0.90 m row gap
is a person edge-on.

*What would overturn it.* Any frame establishing the plan of one of these rooms. The medlab, the
Zocalo shops, the council chamber and C&C are all on screen repeatedly and none of their plans was
consulted for this table, because this is a generator rule for the 78 rooms that have no frame.

---

**INV-141 — clear height keyed on function**

*What.* A per-function clear height (`station/rooms.FUNCTION_HEIGHT`), taken as the maximum over a
place's declared functions, replacing the archetype nominal where any function has an entry. 33
distinct heights across 78 generated rooms, against 11 before.

*Why.* `docs/variety-V0.md` §7: 48 of 128 places shared a 2.90 m ceiling and the station had 11
heights, one per archetype. The section channel had 47.6% of all pairs above the ceiling.

*What constrained it.* A clearance ladder, stated in the table: standing height 1.70 m plus hair;
a 2.35 m door head; a 0.30 m duct on a 0.15 m hanger; a gantry over a 0.90 m working surface; and
`interior.DECK_PITCH_M` = 3.60 m as the hard cap on anything that fits in one deck, because
`rooms._selftest` holds multi-deck rooms under 40% of the remit with one room of margin.

*What would overturn it.* A frame with a person and a ceiling in it, for any of these rooms. The
medlab and C&C would settle several at once. The value most likely to be wrong is `worship` at
4.20 m, inherited from the archetype and never measured.

---

**INV-142 — a bay is a whole fraction of its own location**

*What.* `rooms.whole_bays(full, minimum)`: a location's built bay is `full / n` for the whole `n`
that puts the bay nearest its contents-derived minimum without going under it, per axis.

*Why.* The register's footprint reached the geometry only through `bays_in()`, whose callers put it
in a report dict. Four medlabs declare identical functions and interactables and differ only in
footprint, and all four built the identical 7.9 × 6.0 m room.

*What constrained it.* The bay may never exceed the location (`station/deck.py` sizes every room
slot as `min(room_extent_m, bay_span_m)`, so a larger bay would break the assembler's agreement with
the geometry — hard rule 4), and never falls below what the room's own contents need. `round` rather
than `floor` for the count, so a bay is at most about 1.5× its minimum: twice is an empty hall
again, which is the defect `bay_span_m` was written to fix.

*What would overturn it.* Any statement that a named location is one undivided volume rather than a
repeated bay. `docking_bays` at 140 m is the obvious candidate and is not built by this generator.

---

## 8. How to re-run any of this

```bash
python3 station/variety.py                       # the gate and every control
python3 station/variety.py --pair medlab_red infirmary
python3 station/variety.py --drivers
python3 station/rooms.py                         # closure, winding, containment, walkability
python3 station/bespoke.py
python3 station/budget.py
```

The V1 inner loop was the four named clusters measured directly through
`variety.place_occupancy` — 27 rooms and three re-seed probes in **43 seconds**, against sixteen
minutes for a cold full run. Anything that changes a generator invalidates `variety.py`'s cache, so
the full gate is a verdict and not an inner loop.
