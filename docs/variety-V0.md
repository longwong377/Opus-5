# V0 — the variety gate exists, and it is red

**Session 4h. `station/variety.py`.** `docs/MASTER-PLAN.md` §4: *"V0 — the gate exists and is red:
pairwise place distinguishability measured and reported, with the one-parameter-block control that
must read 1.000."*

This is the measurement, its controls, what it found, and what V1's grammar should key on.

> **The verdict, before the method.** Every gate in this repository measures COVERAGE or
> CORRECTNESS, and both are perfectly satisfied by one generic thing repeated seventy-eight times.
> Asked the missing question — *is this place different from that place?* — the station answers:
>
> **27 clusters of mutually indistinguishable places, covering 82 of the 128.** On FORM alone —
> the plan and the section, which is what a generator has to produce — **21 clusters covering 90 of
> 128, the largest of them 18 places.** The station's six medlabs are one room. Its eight offices
> are one room. Its five bars are one room. Its four places of worship are one room. **47.6% of all
> 8,128 pairs have a cross-section and a longitudinal section that cannot be told apart at all.**

---

## 1. Why a new instrument, and why this one

`station/npc/body.py --silhouette` already proves the shape of the answer. It rasterises four
species from a fixed camera, reports pairwise IoU in a head band, and carries the control that
makes the number mean anything: **four bodies built from ONE parameter block read 1.000 and FAIL
the ceiling the four real species pass.** `variety.py` is that instrument pointed at rooms.

It also inherits `body.py`'s most expensive lesson. That module once rasterised a head **five
pixels wide**, and a "regression" everyone was reading turned out to be one pixel of a five-pixel
shape. So the spans are stated up front:

| | |
|---|---|
| cell, vertical | 0.08 m |
| plan raster | 240 × 240 columns |
| section raster | 240 × 120 cells, 9.6 m tall |
| a 0.6 m prop | **7.5 px** |
| a 0.9 m walking aisle | **11 px** |
| a 4.5 m fixture pitch | **56 px** |

### The three channels

A player walking into a room answers three questions in order, and each gets a channel:

1. **What shape is this volume?** → **SECTION** — the room's cross-section and its longitudinal
   section, the harsher of the two, IoU.
2. **What is standing in it, and where?** → **PLAN** — solid occupancy in the band a body
   occupies, IoU.
3. **What *are* those things?** → **CONTENT** — cosine over a canonicalised object vocabulary
   weighted by surface area.

Plan and section are **two views of one solid**, so `form = min(plan, sect)` — `body.py`'s own
rule, that a pair scores at the view it differs *most* in. Content is a different property, the
way stature is not a third view of a species. The pair's score is `min(form, content)`: two places
are the same place only if they are the same shape **and** the same layout **and** the same stuff.
That makes the gate deliberately hard to fail and therefore credible when it does — a flagged pair
cannot be argued away with *"but the props are different"*, because the props were checked.

### How occupancy is measured

A **winding walk down each column**. For every triangle with non-zero projected area in plan, the
plane's height is evaluated at each cell centre it covers and recorded with the sign of the face;
sorting by height and walking a depth counter gives the solid intervals exactly, for any closed
mesh, including coincident faces. Plan, cross-section and longitudinal section are then three
marginals of that one field, so they cannot be taken off different geometry.

Neither a vertex splat nor a filled triangle projection would work, and the reason is worth
keeping: **a vertical wall projects to a line in plan.** A filled projection of a closed room draws
its walls one pixel wide, and an IoU of one-pixel lines moves by half its value when a wall shifts
by 8 cm.

Rooms are built through **`deck.room_geometry`**, which is the single decision the deck assembler
and the collision builder both use — bespoke where a module owns the place and its doorway is
clear, `rooms.build` otherwise. Measuring anything else would be measuring a room nobody enters.
Under that dispatcher the station is **102 generic builds and 26 bespoke**.

**Nothing about material, light or people is in the measurement.** `npc_` groups are excluded
through `rooms.is_solid`'s own rule — a room's crowd is not the room's form, and including it would
have broken the seed control, since two clones differing only in seed get different bodies.

### Three defects found while building the instrument

Each was found by a control, and each is recorded in the module.

**1. The fill was not watertight.** The obvious nearest-integer scanline (`floor(x+0.5) ..
ceil(x-0.5)`) lets two triangles sharing a quad's diagonal both claim the boundary cell, so a box's
top face contributes two crossings there and its bottom face one. **2,877 of ~4,500 occupied
columns in `medlab_one` came back unbalanced** — the mesh reported open where it is closed. A
half-open `[x0, x1)` centre rule takes it to zero.

**2. Plain even-odd parity broke on `command_control`.** Its floor, dais and pit are `_disc` and
`_ring` fans — single-sided plates, which is the right way to model a floor plate and not a closed
solid — so **51,178 of its 51,284 columns** had no matching face. The room is not the defect; the
measurement was. An unmatched face now becomes a one-cell slab, which is what a single-sided plate
physically is, and the count is reported per place rather than swallowed. (123 of the 128 places
have at least one such column, which is a fact about the meshes worth someone's attention on its
own.)

**3. THE PLAN BAND WAS THROWING AWAY THE TABLES.** The first version compared occupancy from
**0.90 m** upward — "above the knee", which sounds like the right description of what a player
walks among and is not. `dressing.SCHEMES`' entire vocabulary is eight objects, and their heights
are table 0.74, chair 0.95, crate 0.50–0.80, can 0.90, bin 0.60–0.80, console 1.10, locker 1.90,
shelf 1.80–2.40. **A 0.90 m floor discarded every table and every crate** — half the vocabulary,
and in a bar or a mess hall most of the furniture. The band is now 0.30–2.00 m, above the deck's
own decoration (`SKIRT_H_M` 0.14, tiles 22 mm proud, the corridor's lighting channel 66 mm) and
below the head. Correcting it moved the derived ceiling from 0.85 to 0.73 and the flagged-pair
count from 74 to 101, so it was not a cosmetic fix.

That third one is this repository's own recurring defect in a new place: **the band was chosen to
exclude the floor and happened to exclude the furniture.** It is the same shape as a tag-coverage
assertion run on a corridor with no doors in it.

---

## 2. The one real design decision: what to normalise

Three horizontal mappings were built, and all three are still runnable, because the difference
between them is itself a finding:

| `--mode` | mapping | measures |
|---|---|---|
| `fit` *(default)* | each axis stretched to the room's own footprint | **pure layout** |
| `uniform` | one scale, the room's longest extent | layout + aspect |
| `metric` | a fixed 19.2 m window | layout + aspect + absolute size |

`metric` was the first version, on the reasoning that a 4.5 m fixture pitch is the same 4.5 m in
any room. Run, it scored **`medlab_one` against `morgue` at 0.306**, and `uniform` scored the same
pair at **0.221**, against **0.503** under `fit` — two rooms out of the same generic kit, the same
archetype, the same fixture list, the same props, called *substantially different places* because
one is 10.5 m long and the other 8.3 m. Under both, the channel doing the work was **wall
position**.

A player cannot tell a 6 × 8 m room from a 6 × 10 m one. A gate that can is not measuring
distinguishability, it is **manufacturing variety out of a footprint number** — the same defect as
a coverage count satisfied by one generic thing repeated seventy-eight times. So the default fits
both axes and reports size on its own axis, following `body.py`, which divides stature out of the
silhouette and asserts it separately.

**The section's vertical axis stays in metres**, and that is not an inconsistency. A metre of
height is measured against the observer's own body — a player reads a 7.5 m foundry and a 2.9 m
office instantly — and a metre of plan is not. Normalising height too would have scored a 13.6 m
foundry (7.6/13.6 = 0.56) and an 8.3 m medlab (3.1/8.3 = 0.38) by their *proportion*, and
proportion is not what a ceiling is.

**How much of the station's apparent variety was only the box dimensions**, measured over the same
8,128 pairs:

```
  fit      median score 0.209    101 pairs over the ceiling
  uniform  median score 0.092     77
  metric   median score 0.073     80
```

Two thirds of the median difference between two places under a metric window is the fact that the
boxes are different sizes. That is not variety a player experiences.

---

## 3. The ceiling is derived, not chosen

`python3 station/variety.py --derive` recomputes it and fails if the recorded value drifted —
`tools/measure_frame.py --derive`'s idiom, for the same reason: a tolerance somebody typed is a
tolerance somebody can retype when it becomes inconvenient.

The derivation is one sentence. **Two places are indistinguishable when they are no more different
than the same room built twice.** `clone_place` builds a place under a second key, which changes
every random stream in `rooms.build` and `dressing.dress` and nothing else — same archetype, same
footprint, same declared fixtures, same props. Done once per archetype:

```
  archetype    probe                score    plan    sect  content
  industrial   fabrication          0.736   0.736   1.000    0.996
  store        cargo_bays           0.880   0.880   1.000    0.998
  commerce     business_center      0.912   0.912   1.000    0.995
  hospitality  mess_hall            0.913   0.913   1.000    0.995
  generic      obs_dome_1           0.924   0.924   1.000    0.999
  research     research_labs        0.928   0.928   1.000    0.998
  office       war_room             0.929   0.929   1.000    1.000
  detention    brig                 0.948   0.948   1.000    1.000
  worship      sanctuary_blue       0.951   0.951   1.000    0.999
  medical      medlab_one           0.963   0.963   1.000    1.000
  transit      central_corridor     0.966   0.966   1.000    0.996

  the weakest re-seed pair is industrial at 0.736
  ceiling = floor(that, 0.01) = 0.73
```

The weakest is `industrial`, and the reason is legible: its dressing scheme is four kinds of small
movable object at the second-highest density on the station, so a re-seed has the most to move.
Every one of the eleven re-seeds at **1.000 in the section channel** — a channel-level control in
its own right, since the shell does not depend on the seed.

**The minimum rather than the median, and the direction is the opposite of what it sounds like: a
higher ceiling flags fewer pairs.** Measured over the same 8,128:

| ceiling | pairs | clusters | places covered |
|---|---|---|---|
| 0.963 (best re-seed) | 0 | 0 | 0 |
| 0.913 | 33 | 11 | 31 |
| 0.880 | 46 | 17 | 46 |
| 0.800 | 76 | 24 | 69 |
| **0.736 (worst re-seed)** | **99** | **27** | **82** |
| 0.700 | 120 | 26 | 85 |

So the minimum is the sensitive end, and the logical statement it supports is the strict one: a
pair above 0.736 is *at least as similar as two builds of one industrial room*, which is a thing a
player calls the same room. The check on it is that its output is verifiable by eye rather than on
trust. The 35 pairs the move from 0.85 to 0.736 adds include `arrival_concourse` vs
`customs_north`, `qtr_civilian` vs `qtr_personnel`, `cargo_bays` vs `spinal_cargo` and
`bar_unnamed` vs `fresh_air`. Every one of those is one room twice.

*Recorded rather than built:* the re-seed score is archetype-dependent — 0.736 to 0.966 is a wide
spread — so a pair's honest ceiling is `min(reseed[arch(a)], reseed[arch(b)])` rather than one
number for the station. That is a better instrument and it needs the table above to become a gate
input rather than a comment.

---

## 4. The controls, and whether they fired

`python3 station/variety.py`, verbatim. **Five controls pass; the gate fails; exit 1.**

```
CONTROL 1  a place against itself                       1.000
  ok   a place measured against itself reads IoU 1.000
CONTROL 2  one room, only the seed changed              0.924   plan 0.924  sect 1.000  content 0.999
  ok   two builds of one place differing ONLY in seed read 0.924, no worse than the worst
       re-seed the ceiling was derived from (0.736)
  ok   and the seed clone FAILS the 0.73 ceiling (0.924) -- the ceiling sits below a re-seed,
       so the gate cannot be passed by shuffling random numbers
CONTROL 3  zocalo vs cargo_bays                 0.166   plan 0.166  sect 0.883  content 0.200
CONTROL 3  zocalo vs medlab_one                 0.144   plan 0.161  sect 0.436  content 0.144
CONTROL 3  cnc vs qtr_transient                 0.180   plan 0.180  sect 0.419  content 0.250
CONTROL 3  fabrication vs sanctuary_blue        0.263   plan 0.267  sect 0.571  content 0.263
  ok   places a human would obviously call different read LOW (worst of 4 such pairs 0.263) --
       the metric is not a constant and the ceiling is reachable from below
CONTROL 4  medlab_one vs fabrication, furnished  0.173  -> stripped to bare shell 0.337
                                                       (form 0.173 -> 0.349)
  ok   MUTATION: taking the furniture out of two rooms moves their FORM toward each other
       (0.173 -> 0.349) -- the metric responds to contents, and what these two already share
       is the shell

THE STATION: 128 places, 8,128 pairs, median score 0.209, median form 0.267
  101 pairs (1.2%) score above the 0.73 ceiling
  164 pairs (2.0%) have the same FORM -- same plan and same section, told apart only by their props
  27 clusters of mutually indistinguishable places, largest 8, covering 82 of 128 places
      8  admin_complex, ceremonial_rooms, conference_5, conference_rooms, drum_office,
         earthforce_office, minipax, telepath_office
      8  alpha_substation, atmos_monitor, mainstage_node, maintenance, power_transfer,
         primary_breaker, rotation_drivers, waste_control
      6  infirmary, isolab, medlab_green, medlab_one, medlab_others, medlab_red
      5  bar_unnamed, earharts, eclipse_cafe, fresh_air, happy_daze
  the seed clone (0.924) against the station's p99 (0.779)
  ok   one room built twice (0.924) is more alike than 99% of pairs of different rooms (p99 0.779)
  FAIL no two of the 128 places are indistinguishable (101 of 8,128 pairs score above 0.73;
       the largest cluster nothing can tell apart is 8 places)

1 failing
```

**The two the brief names, and both fired.**

* **The one-parameter-block control reads near-1.000 and fails the ceiling.** 0.924 with the
  section at 1.000 and content at 0.999. It is the exact analogue of `body.py`'s four species from
  one parameter block.
* **The obviously-different control reads low.** The Zocalo against a cargo bay is **0.166**; the
  worst of the four such pairs is 0.263, well under the ceiling and well under the p95 of the whole
  matrix.

Two further controls that were not asked for and are worth keeping. **CONTROL 4** builds the
mutation rather than asserting it: strip `dressing`, the props and the fixtures out of two rooms
and their form has to move *toward* each other, which it does, 0.173 → 0.349 — so the metric
responds to contents, and what two rooms out of one kit already share is the shell. And the last
check is the strongest single statement about the instrument: **one room built twice is more alike
than 99 out of 100 pairs of different rooms** (0.924 against p99 0.779).

### An exhibit, because the number is not the persuasive part

`--plan interfaith_chapel` and `--plan sanctuary_blue` — solid matter in the walking band, the
room's own footprint stretched to the raster. The Zocalo is beside them as the control:

```
interfaith_chapel                         sanctuary_blue                            zocalo
.######################################.  .######################################.  .######################################.
.######################################.  .######################################.  .#####....####.#.........#####....#####.
.####......................##.........#.  .####......................##.........#.  .#####........##.........###......#####.
.####.#......#.............##.....##..#.  .####.#....................##.....##..#.  .####...#####..........###..####.....##.
.####.#..........######.##.##........##.  .####............######....##.....##.##.  .#####...###................###...#####.
.####............######....##........##.  .####............######....##........##.  .#####..####...........####.####..#####.
.####............######....##.........#.  .####............######....##.........#.  .#####..##..##...........###..##..###.#.
.####............######....##.........#.  .####............######....##.........#.  .#####.....####..........###......###.#.
.####............######....##....#....#.  .####............######....##....#....#.  .##.....##.##...........#.###.##.....##.
.#...............######..##......#....#.  .#...##..........######..........#....#.  .#####.......####.......###.##....#####.
.#...............######...............#.  .#...............######...............#.  .#.###.....###.............####...###.#.
.#...............######...............#.  .#...............######...............#.  .#.###..##....#.........#..#####..#####.
.##..............######....##........##.  .##..............######....##........##.  .#####......###........####.##....###.#.
.##..............######....##........##.  .##..........#...######....##........##.  .#####..##....##..........###.##..#####.
.#....#..................####........##.  .#..###......#...........####........##.  .#####..####.###.......###.#####..#####.
.#....................................#.  .#....#...............................#.  .#####...###..##.........####.....###.#.
.######################################.  .######################################.  .#......####..............#.####......#.
.######################################.  .######################################.  .##################..##################.

interfaith_chapel   10.94 x  6.36 m, 4.34 m tall, 15,236 tri     score 0.950
sanctuary_blue      10.94 x  6.36 m, 4.34 m tall, 15,100 tri     (plan 0.950, section 1.000, content 1.000)
zocalo              22.04 x 35.03 m, 7.34 m tall, 1,207,248 tri
```

The interfaith chapel and the Blue Sector sanctuary are **authority 5 and authority 3, in different
sectors, with different footprints declared in the register**, and they are the same drawing. There
is a committed pair of engine frames that says the same thing without any of this machinery:
`docs/engine-4a-generic.png` and `docs/engine-4a-office.png` are two different archetypes and the
same room.

---

## 5. The matrix over all 128 places

```
128 places, 8,128 pairs, 'fit' mapping
  built by: 102 generic, 26 bespoke

  PAIRWISE SCORE = min(form, content),  form = min(plan, section)
             score    form    plan    sect  content
    p5       0.076   0.097   0.097   0.282    0.099
    p25      0.144   0.177   0.177   0.436    0.192
    p50      0.209   0.267   0.269   0.699    0.300
    p75      0.285   0.386   0.386   0.904    0.490
    p95      0.497   0.620   0.620   0.995    0.812
    p100     0.958   0.958   0.958   1.000    1.000

  ABOVE THE 0.73 CEILING
    score       101 of 8,128 pairs  (  1.2%)
    form        164 of 8,128 pairs  (  2.0%)
    plan        164 of 8,128 pairs  (  2.0%)
    sect      3,869 of 8,128 pairs  ( 47.6%)   <-- the number that matters
    content     603 of 8,128 pairs  (  7.4%)
```

**The section channel is the finding.** Nearly half of all pairs of places on this station have a
cross-section and a longitudinal section that cannot be told apart — same clear height, same wall
thickness, same rib rhythm, same overhead. Its median is **0.699** against 0.269 for plan and 0.300
for content, and it is the only channel whose p75 is over 0.9. **A player walking from one place to
another is walking into the same volume 47.6% of the time**, and everything else the measurement
finds follows from that.

### The clusters — the same room wearing different names

27 of them, covering **82 of the 128 places**. Single linkage, because if A cannot be told from B
and B cannot be told from C, a player walking A→B→C has seen one room three times.

| n | archetype | places |
|---|---|---|
| **8** | office | `admin_complex`, `ceremonial_rooms`, `conference_5`, `conference_rooms`, `drum_office`, `earthforce_office`, `minipax`, `telepath_office` |
| **8** | industrial | `alpha_substation`, `atmos_monitor`, `mainstage_node`, `maintenance`, `power_transfer`, `primary_breaker`, `rotation_drivers`, `waste_control` |
| **6** | medical | `infirmary`, `isolab`, `medlab_green`, `medlab_one`, `medlab_others`, `medlab_red` |
| **5** | hospitality | `bar_unnamed`, `earharts`, `eclipse_cafe`, `fresh_air`, `happy_daze` |
| **4** | worship | `alien_worship`, `interfaith_chapel`, `sanctuaries`, `sanctuary_blue` |
| **4** | transit | `drum_spokes`, `lifts`, `radial_tubes`, `transfer_systems` |
| 3 | generic | `arrival_concourse`, `customs_north`, `customs_south` |
| 3 | store | `bay_elevators`, `fuel_stores`, `hazard_tanks` |
| 3 | store | `cargo_bays`, `raw_material`, `spinal_cargo` |
| 3 | generic | `comms_grid`, `nav_beacon`, `thieves_guild` |
| 3 | industrial | `waste_green`, `waste_red`, `water_storage` |
| 2 | generic | **`alien_sector`, `kosh_quarters`** |
| 2 | generic | `ambassadorial_suites`, `league_delegations` |
| 2 | commerce | `business_center`, `ngrath` |
| 2 | transit | `central_corridor`, `standard_corridor` |
| 2 | transit | `core_shuttle`, `shuttle_car` |
| 2 | generic | `domed_rotunda`, `obs_rotundas` |
| 2 | transit | `drum_tram`, `ground_tram` |
| 2 | research | `gravity_torus`, `research_labs` |
| 2 | industrial | `micro_g_bays`, `zerog_maint` |
| 2 | generic | `obs_dome_1`, `obs_dome_2` |
| 2 | industrial | `plant_zone`, `water_reclamation` |
| 2 | store | `plantroom_bay`, `subfloor_stack` |
| 2 | commerce | `post_office`, `quartermaster` |
| 2 | generic | `qtr_civilian`, `qtr_personnel` |
| 2 | detention | `security_central`, `security_posts` |
| 2 | commerce | `shops_kiosks`, `zocalo` |

Two of those deserve to be read twice. **`alien_sector` vs `kosh_quarters` scores 0.954** — a 36° ×
120 m multi-atmosphere gallery for fifteen species and a **Vorlon's sealed methane suite** are the
same box, and the register says one is authority 3 and the other authority 1. And the eight-place office
cluster holds **the Ministry of Peace office** (`minipax`), **the resident commercial telepath's
office** (`telepath_office`), the **Earthforce** office and a **civil administration** office as one
room — which is exactly the faction friction `MASTER-PLAN.md` §3 L6 says has to be *"visible in a
corridor"*, currently rendered as four identical offices.

And on **FORM ALONE — 21 clusters covering 90 of 128, the largest of them 18 places.** Those 18 are
one shape; only their props keep them apart in the combined score.

The worst ten pairs:

```
0.958  drum_spokes  vs  radial_tubes         (plan 0.958  sect 1.000  content 1.000)
0.957  infirmary  vs  medlab_red             (plan 0.957  sect 1.000  content 1.000)
0.954  bar_unnamed  vs  eclipse_cafe         (plan 0.954  sect 1.000  content 1.000)
0.954  alien_sector  vs  kosh_quarters       (plan 0.954  sect 1.000  content 0.999)
0.952  medlab_green  vs  medlab_red          (plan 0.952  sect 1.000  content 1.000)
0.952  radial_tubes  vs  transfer_systems    (plan 0.952  sect 1.000  content 0.999)
0.951  medlab_others  vs  medlab_red         (plan 0.951  sect 1.000  content 0.999)
0.951  infirmary  vs  medlab_green           (plan 0.951  sect 1.000  content 0.999)
0.950  interfaith_chapel  vs  sanctuary_blue (plan 0.950  sect 1.000  content 1.000)
0.949  drum_spokes  vs  transfer_systems     (plan 0.949  sect 1.000  content 1.000)
```

---

## 6. What drives the variance

Median pair score when two places share a fact, against when they do not.

```
                             share it            do not              separation
  same archetype             0.262 (n= 1,050)    0.204 (n= 7,078)      +0.058
  same module owner          0.269 (n= 3,103)    0.181 (n= 5,025)      +0.089
  both built generic         0.246 (n= 5,151)    0.137 (n= 2,977)      +0.109
  same sector                0.213 (n= 1,751)    0.209 (n= 6,377)      +0.004
  shared function            0.355 (n=   354)    0.206 (n= 7,774)      +0.149
  shared interactable        0.273 (n= 1,137)    0.204 (n= 6,991)      +0.068
  same authority             0.204 (n= 2,669)    0.211 (n= 5,459)      -0.007
  same ring                  0.205 (n= 4,369)    0.215 (n= 3,759)      -0.010
  same dominant species      0.208 (n= 5,540)    0.213 (n= 2,588)      -0.005
  human share within 10 pts  0.218 (n= 2,646)    0.204 (n= 5,482)      +0.014

ON FORM ALONE -- what a form grammar has to fix
  same archetype             0.287               0.266                 +0.021
  both built generic         0.351               0.157                 +0.195
  shared function            0.424               0.262                 +0.162
```

**Read the shape before the size.** Four facts the register carries per place separate **nothing**:
sector (+0.004), authority (−0.007), ring (−0.010) and **the species mix (−0.005 on dominant
species, +0.014 on human share)**. Those are not weak predictors, they are inert — which is the
correct measurement of a fact the geometry has never been shown.

**The one thing that does predict sameness is being built by the same generator.** `both built
generic` separates **+0.195 on form**, nearly ten times what `same archetype` manages (+0.021). The
places are not alike because they are similar kinds of place. **They are alike because they come out
of the same function.** That is a structural fact, not a list of jobs — the same distinction
session 4d's `interact.py` audit turned on.

**`shared function` is the second driver, and its sign is backwards from what V1 wants.** Two places
that declare a function in common are *more* alike (+0.162 on form), because sharing a function
means sharing an archetype means sharing a shell. The register's own statement of what a place is
*for* is currently a similarity driver. Making it a differentiator is V1's whole job.

### Is it size?

```
  score  x1-x2: 0.252 (n=4,707)   x2-x4: 0.183   x4-x8: 0.127   x8-x16: 0.093   x16+: 0.058
  form   x1-x2: 0.363             x2-x4: 0.218   x4-x8: 0.134   x8-x16: 0.108   x16+: 0.165
```

Partly, and honestly. Under a mapping that has already normalised footprint away, a bigger size gap
still predicts a lower score — because on this station a very differently sized place is usually a
*bespoke* place, and bespoke is the only thing on the station that makes a different shape. Size is
a proxy for "somebody hand-built it", not a driver in its own right.

### And the number that says what a room actually is

```
  canonical object names  median 0.300   above ceiling   603
  raw group names         median 0.168   above ceiling   530
  including the shell     median 0.894   above ceiling 6,757     <-- 83% of all pairs
```

The content channel compares **objects** — `rooms.is_solid`'s own definition, the same one the
walkability trial and `collision.prop_boxes` use. Compare *whole surface area* instead, shell
included, and the median goes to **0.894 and 6,757 of 8,128 pairs (83%) are indistinguishable**,
because a room is mostly its shell and every shell on this station is the same shell. A 7.9 × 6.0 m
box is roughly 120 m² of wall and soffit against 30 m² of furniture.

*(The `raw group names` row is a control on the canonicalisation: comparing `medical_wall` against
`office_wall` as different objects would manufacture variety out of a string prefix. Stripping the
room's own shell token moves the median from 0.168 to 0.300 — so 0.13 of the apparent content
difference on this station was the prefix.)*

---

## 7. What the register already knows and the generator ignores

This is the part that decides V1, and it is a measurement rather than an opinion.

### The generator reads six fields, and one of them is a random seed

Every `place[...]` access in `rooms.py` and `dressing.py` — which between them decide the form of
the 102 places built generic and the furniture of all 128:

| field | reads | what it does |
|---|---|---|
| `key` | 14 | **the random seed**, and nothing else |
| `interacts` | 6 | which declared props get placed, and via `bay_span_m` how big the bay is |
| `sector` | 3 | ring radius, for the arc-to-metres conversion |
| `footprint` | 2 | the room's extent |
| `ring`, `deck` | 1 each | which deck's floor radius |
| `functions` | **1** | `archetype()` — and this is the whole of form |

Never read by any form generator: **`auth`, `adjacent`, `within`, `note`**, and every per-place
fact in `npc/schedule.PLACES` and `populace.SECTOR_MIX`.

### The whole of form is one funnel, and it is eleven wide

```
128 places  ->  functions  ->  11 archetypes  ->  11 ceiling heights
                                                  11 fixture sets   (+10 per-place overrides)
                                                  11 dressing schemes over 8 object kinds
                                                  11 prop densities
                                                  11 light fittings  (+1 per-place override)
```

* **25 distinct `(archetype, ceiling, fixture-set)` triples for 128 places.**
* **48 of 128 places share a 2.90 m ceiling.** Eleven distinct ceiling heights exist on the whole
  station. That is the section channel's 47.6% in one line.
* `dressing.SCHEMES` is **8 object kinds** — shelf, crate, locker, table, chair, console, bin,
  can — dealt out per archetype.
* The corridors are one generator and **five schemes**, and `corridor_dressing.scheme_for` picks
  one by *the commonest archetype among the places on that deck*. So the corridor's variety is a
  function of the same eleven-wide funnel — which is why `central_corridor` and `standard_corridor`
  are in a cluster together.

### 122 declared functions go in; 66 are claimed by any archetype

`directory.PLACES` declares **122 distinct functions** across the 128 places.
`rooms.ARCHETYPES` claims **66** of them. **31 places match none and fall through to `generic`**,
and the list of what falls through is the point:

| function | places falling through |
|---|---|
| `residence` | 9 |
| `recreation` | 5 |
| `structure`, `agriculture`, `observation` | 3 each |
| `immigration`, `identicard_check`, `diplomatic_mission`, `atmosphere_plant`, `sport`, `public_social` | 2 each |
| `arrival`, `wayfinding`, `crime`, `organised_crime`, `communications`, `power_generation`, `starfury_launch`, `multi_environ`, `sealed_environment`, `oxygen_production`, `food_production`, `viewport`, … | 1 each |

**Every residence on the station has no archetype of its own.** So does the drum's farmland, every
observation space, immigration, and organised crime. `garden_town` is authority **1**, its footprint
is 50° × 300 m, it declares `agriculture / recreation / civic / atmosphere_plant`, and it builds as
a generic box because no archetype claims any of those four words.

### And what nobody has ever asked the geometry for

`npc/schedule.PLACES` carries **25 `PlaceCrowd` rows**, each with `human_share`, a ranked list of
dominant non-human species, `peak_per_100m2`, busy hours, dead hours, and `flat` / `waves` /
`sealed` flags. `populace._mix_for` resolves one for **every** place, giving **18 distinct human
shares across the 128, from 0.05 to 0.95** — Green Sector is 46% human with minbari/centauri/abbai
dominant, Yellow is 95%, Grey is 90% with drazi and gaim.

Measured in §6, sharing that fact separates **−0.005**. It decides who stands in the room and what
they wear, and it has never touched a wall. **An alien resident's quarters against a human
civilian's — `alien_resident_qtr` vs `qtr_civilian` — score 0.572, with the section at 0.999 and the
contents at 0.974.** Identical volume, all but identical furniture; what little separates them comes
from `quarters.py`'s housing classes, not from the species living there.

---

## 8. What V1's grammar should key on

Ordered by measured leverage, not by appeal.

**1. Ceiling and section, keyed on function rather than on the eleven-way archetype.** The section
channel is the worst number in this report — **47.6% of pairs over the ceiling, median 0.699** —
and it is also the cheapest to move, because it is currently *one number per archetype* and 48
places share a ceiling. A medlab's section differs from an office's because a medlab needs a clear
service zone over a bed, a lifting gantry track and a 3.6 m soffit, and an office needs none of
those. That is a rule about `functions`, and `functions` already exists, is authored per place, and
is read exactly once in the whole generator.

**2. Give the 56 unclaimed functions a shape.** `residence`, `agriculture`, `observation`,
`immigration`, `diplomatic_mission`, `crime` are not decoration words — each implies a plan. A
residence is **cellular**: a corridor with unit doors off it, which is a different plan *topology*
from a hall, not a differently furnished one. Farmland is a field with service tracks. An
observation space is a room whose whole plan is oriented at one wall. **None of those are props;
all of them are form**, and all six are in the register today. This is what would break the
`ambassadorial_suites` / `league_delegations` and `qtr_civilian` / `qtr_personnel` clusters.

**3. Make plan topology a generated thing rather than one rectangle.** Every one of the 102 generic
places is a rectangle with fixtures ranked down its centreline or its flanks and dressing against
its walls; the only variables are length, width and a seed. **`both built generic` separating
+0.195 on form is the measurement of that.** A grammar with even four topologies — hall, cellular,
gallery-with-aisle, cluster-around-a-core — chosen by the function rules above would break every
cluster in §5 that is held together by both places being the same rectangle, which is all of them.

**4. Species and faction, which the register knows per place and the geometry has never seen.**
18 distinct human shares, fifteen species, every faction dressed by `costume.py`. The same data can
drive door height and width, seat height, ceiling for a Minbari versus a Drazi space, light
temperature, signage script, atmosphere plant in the room, and the proportions of a residential
unit. Unlike a prop, all of those read from across the room — and this is the single cheapest route
to the owner's own test, *the friction between factions visible in a corridor*.

**5. Wear, age and traffic on the corridor kit — the S-track's one multiplying lever.**
`corridor_dressing` has five schemes chosen by the commonest archetype on the deck. Sector, deck age
and measured foot traffic are all derivable today (`traffic.py`, `populace.corridor_headcount`) and
none of them reaches the kit. One pass here multiplies across all 70 ring decks at once.

**What NOT to do: add more props.** Content is already the *least* bad channel at 7.4% over the
ceiling, and §6 shows that when the shell is included the median goes to 0.894 with 83% of pairs
indistinguishable. Rooms are not the same because they lack objects. **They are the same because
they are the same box**, and a box with more things in it is still that box. The AAA rubric's own
craft-5 descriptor is *"nothing in frame repeats in a way the eye can index"*; this measurement is
that clause, and props are not what fails it.

---

## 9. CHANGES I NEED IN FILES I DO NOT OWN

None are required for V0 to stand — `variety.py` is self-contained and runs from a clean tree.
Two are proposed.

### 9.1 `.github/workflows/validate.yml` — wire the gate in as a *reporting* step

V0 is red by design, and session 4e's fix means one failing step no longer blinds the ones behind
it. Add after *NPC animation and navigation*, and add the matching line to the final
*Every gate ran* block:

```yaml
      # V0 (docs/MASTER-PLAN.md §4). EXPECTED RED, like the performance budget
      # above: it measures whether any two of the 128 places are
      # indistinguishable, and 128 places out of 11 archetypes are. The remedy
      # is V1, not a looser ceiling -- and the ceiling is derived from the
      # generator's own repeatability, so it cannot quietly be loosened.
      - name: No two places are the same room
        id: sno_two_places_are_the_same_room
        continue-on-error: true
        run: python3 station/variety.py
```

```yaml
          if [ "${{ steps.sno_two_places_are_the_same_room.outcome }}" != "success" ]; then
            echo "FAILED: sno_two_places_are_the_same_room"; fail=1; fi
```

**Caveat, and it is why this is a proposal rather than a patch.** A cold run rebuilds all 128 rooms
and takes roughly **sixteen minutes** on this box — longer than any existing step. Wiring it in
unconditionally trades a real answer for a much slower build. The cheaper options are
`python3 station/variety.py --derive` alone (~3 minutes, and it still fails on drift in the
generator's repeatability), or a scheduled rather than per-push run.

### 9.2 `STATE.md` and `docs/MASTER-PLAN.md` — V0 status, and a threshold for V1

`MASTER-PLAN.md` §4's **V0** row can be marked done: the gate exists, it is red, both required
controls fire.

**V1's *"done when"* would be better as numbers than as prose.** It currently reads *"a medlab's
plan differs from an office's because a medlab is not an office"*, which has no threshold in it.
The two numbers that say the same thing and can fail are:

* the **section** channel below 25% of pairs over the ceiling (it is 47.6%), and
* the **largest form cluster** below 4 places (it is 18).

**V3** — *"no two visited places are indistinguishable"* — is `variety.py` returning 0.

---

## 10. How to re-run any of this

```bash
python3 station/variety.py                     # the gate and every control
python3 station/variety.py --matrix            # all 8,128 pairs, summarised, with clusters
python3 station/variety.py --drivers           # what the variance is made of
python3 station/variety.py --derive            # recompute the ceiling; fails on drift
python3 station/variety.py --pair a b          # one pair, per channel, with the content diff
python3 station/variety.py --plan medlab_one   # an ASCII plan of the walking band
python3 station/variety.py --verify-cache 5    # rebuild sampled rooms and diff against the cache
python3 station/variety.py --mode metric ...   # any of the above under a different mapping
```

The cache lives in `.variety-cache/` (or `$VARIETY_CACHE`) and is keyed on a hash of every builder
module plus the source of `occupancy` itself, so a change to any generator invalidates every entry.
`--verify-cache` rebuilds sampled rooms and diffs them, because a hash is a claim and this
repository has been burned by a gate that read a committed artefact it could not rebuild. It read
**5 of 5 sampled rooms rebuild identically** at the time of writing.

That invalidation fired for real while this was being measured, and it is worth recording as
evidence the key works. `c50dc50` changed `station/deck.py` — which is this measurement's build
dispatcher — halfway through the session. The stamp changed, the cache missed, all 128 rooms were
rebuilt against the new file, and **the two cache files are byte-identical** (`md5
0eb533d353b18d526439d90edd7153c7`). The commit touches `build_collision_clusters` and not
`room_geometry`, so it is geometry-neutral for this gate, and that is now a measured fact rather
than a reading of the diff. `--derive` re-run at HEAD reports `ok: recorded 0.73 / 0.736, derived
0.73 / 0.736`, and the gate reproduces every number in §4 and §5.
