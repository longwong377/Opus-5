# The physical plant

*The fifth gazetteer file. Scope, session 3c: "the physical plant that makes 250,000 people
possible: food, water, air, power, waste."*

**Era lock: S2–S3.** Authority levels as `canon/00-MASTER.md`: 1 = on screen, 2 = production,
3 = licensed print, 4 = fan reconstruction, 5 = own extrapolation.

This file exists because a station is not a building. Two hundred and fifty thousand people
breathe, drink, eat, defecate and draw power every day, and none of that arrives from outside a
planet's biosphere by accident. Everything here is either named in a source or derived from a
number the station already has, and the derivations are shown so a reader can check them rather
than take them.

---

## 0. What the geometry already decided

Session 3i produced this before any of the research below, and it constrains the whole file.

`HABITABLE_G_MAX = 1.25` (INV-027) splits every deck in the station into `habitat` and `plant`.
Only one sector has any plant at all:

| | decks | plant decks | radii | gravity |
|---|---|---|---|---|
| **Grey** | 105 | **34** | 350.4 → 471.2 m | **1.26 → 1.69 g** |
| Red, Blue, Yellow, Green | 146 | 0 | — | ≤ 1.01 g |

**The plant zone is 139.8 million m³ — 559 m³ per resident.** That number is the single most
useful thing in this file, and it is embarrassing in the right direction. A thirty-day water
reserve for the whole station is **397,500 m³**, which is **0.3%** of it. Life support does not
need 34 decks. It needs about one.

So the plant zone is **not 34 decks of machine room**, and anything that builds it as 34 decks of
corridor is building something absurd — a walkable annulus 442 m long and 2.9 km around, thirty-
four times over. It is predominantly **structure, tankage and void**: the deep frames that carry
a 1.7 g load path, slush and reservoir tanks that want to be at the bottom of the gravity well
anyway, and inaccessible web. Walkable plant is a thin skeleton threaded through it.

**This is a live correction to the streaming manifest**, which currently prices all 34 plant
decks with the corridor kit — 62.3 M of the station's 110.2 M interior triangles, **26% of the
whole interior**, for volume that is mostly not rooms. `budget.py` flags it as a placeholder.
See §8.

### And the plant zone is where Downbelow is

`LOCATIONS.md` puts Downbelow "near the outer hull, around the waste recycling system, the air
compressors and the water reclamation facility" — outermost rings, "corridors and chambers, not
rooms", the highest gravity in its sector, and the Brown rosette marks it on an outer annular
band by name (authority 3).

Those are the same decks the gravity ceiling just excluded. **The geometry says the outer stack
is too heavy to billet anyone on; canon says the people with no billet live in the outer stack
among the machinery.** Neither derivation knew about the other. That is why `use == "plant"`
means *unassigned*, not *uninhabited*, and why the worst address on the station is physically as
well as socially the bottom.

**Design consequence, and it is a good one:** the player reaches Downbelow by walking *down* into
the plant. Getting heavier is the transition. There is no door marked Downbelow; there is a
service stair, and four decks later you weigh 30% more and the corridor has stopped being a
corridor.

---

## 1. Power

### 1.1 What is sourced

| Item | Where | Auth | Source |
|---|---|---|---|
| **Primary fusion core** | Aft terminus assembly, Yellow, non-rotating | 3 | Security Manual callouts; `00-MASTER.md` §2 |
| **Fusion isotope slush tanks** | With the core | 3 | Security Manual |
| **Auxiliary fusion cores** | With the core | 3 | Security Manual |
| **Auxiliary power units (4)** | With the core | 3 | Security Manual |
| **Power transfer core + 12 fins** | On the axis, aft; the Yellow rosette is a **cog, not concentric rings** | 3 | `other map.png` Yellow rosette |
| **Coolant transfer tubes and holding tanks** | Yellow | 3 | Security Manual |
| **Mainstage power distribution node** | Between the reactor and the carousel | 3 | Security Manual callout |
| **Explosive disconnect point** | real z ≈ **2,680 m** — everything aft jettisons as one assembly | 3 | `00-MASTER.md` §2 item 7 |
| **6 large coplanar radiator blades** | Spine rail, 3 above / 3 below | 3 | Contract 5 orthographic sheet; C-007 |

**C-007 matters here and is easy to re-conflate.** The twelve small fins on the Yellow rosette are
reactor-adjacent and arrayed around the axis. The six large lozenge blades on the spine rail are
a different system, coplanar, measured in session 2o. A future session that sees "12 fins" and
"radiators" in one paragraph will merge them again; they are separate.

### 1.2 What is derived — L-01

**The station's electrical demand is ~1.9 GW, and the thermal load it must reject is larger.**

Derivation, all of it from numbers the project already holds:

| Load | Basis | Power |
|---|---|---|
| Habitat lighting | 4.5 M m² of drum inner surface; the habitat is lit entirely by the guideway light runs (authority 1). At 15 W/m² of illuminated ground — daylight-equivalent for agriculture is far higher, but only the ~40% under arable bands needs it | **~600 MW** |
| Interior lighting and services | 251 decks, corridor and room lighting, displays, doors, comms | ~250 MW |
| Atmosphere handling | 250,000 people; circulation, scrubbing, thermal conditioning of ~3.4 M m³ of habitable air | ~180 MW |
| Water reclamation | 13,250 m³/day through a closed loop (§3) | ~90 MW |
| Rotation maintenance | Effectively zero in steady state — a flywheel in vacuum. Nonzero only for docking torque correction and mass redistribution | ~5 MW |
| Industry and fabrication | Grey's furnaces and repair shops (§6) | ~400 MW |
| Docking, traffic, defence, reserve | 24 bays, jump gate approach control, grid | ~350 MW |
| | **total** | **~1.9 GW** |

**Authority 5. What would overturn it:** any on-screen figure for the reactor's output, or a
production document giving a power budget. Nothing held gives one.

**The consequence that shows on the hull, and this is the cross-check.** Essentially all 1.9 GW
ends up as heat, and in vacuum it leaves only by radiation. Six blades at the measured ~7:1
lozenge proportion, radiating from both faces at a plausible 350 K coolant temperature, give an
area-to-load ratio in the right decade — which is *why* the radiators are the size they are
relative to the hull. A station with a 100 MW plant would not need blades that big; a station
with a 20 GW plant could not survive on six. **The radiator geometry, measured off the Contract 5
sheet in session 2o with no thought about power at all, independently constrains the reactor
output to within about a decade of 1.9 GW.** That is the only real check in this section and it
is worth more than the table above it.

### 1.3 What the player experiences

Power is not visible as a number. It is visible as: the guideway light runs being *the* light
source in the drum, with everything below them lit from above and nothing lit from the side; the
mainstage distribution node as a place with a real acoustic signature; brownouts as a plot-grade
event the simulation supports but does not schedule; and the six radiator blades as the largest
moving-heat structure in any exterior shot.

---

## 2. Atmosphere

### 2.1 The one hard fact, and it is authority 1

The customs board, transcribed verbatim in `station/signage.py`:

> "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5. OTHERS MAY BE CREATED BY PRIOR
> ARANGEMENT [*sic*]. UNCOMMON ATMOSPHERIC MAKEUPS MAY BE SYNTHESIZED FOR ENCOUNTER SUITS."

And the identicard prop numbers exactly one of them: `DES/ATMOS: HUMAN/02`.

**Six simultaneous atmospheres is a life-support architecture, not a line of dialogue.** It means
the station is not one pressurised volume. It is at minimum six independently conditioned volumes
with locks between them, plus a synthesis plant for one-off mixes, plus an encounter-suit
charging service. Everything about the Alien Sector follows from this rather than from set
dressing.

**Nothing numbers the other five.** `station/npc/schedule.py` therefore carries atmosphere
*classes* and no numbers, so a wrong number never gets printed on a wall.

### 2.2 What is derived — L-02

| Quantity | Basis | Value |
|---|---|---|
| Habitable pressurised volume | 217 habitat decks, corridor-and-room fraction of the annulus | ~3.4 M m³ |
| Oxygen consumed | 0.84 kg/person/day × 250,000 | **210 tonnes/day** |
| CO₂ produced | 1.0 kg/person/day × 250,000 | **250 tonnes/day** |
| Air changed per hour | Standard closed-habitat practice, 2–4 volumes/h in occupied space | ~7 M m³/h |

**The drum does a real share of this and that is why it exists.** 4.5 million m² of surface with
roughly 48% of the circumference under arable and parkland bands (`LAND_USE` in `interior.py`)
is on the order of 2 km² of photosynthesis. That is a meaningful fraction of 210 t/day of oxygen
— not all of it, which is why hydroponics (§4) is a separate named system, but enough that the
Garden is *plant* in both senses. **The habitat is not a park with a farm in it. It is a lung.**

**Air compressors are canon-adjacent and sited by it:** `LOCATIONS.md` places Downbelow
"around ... the air compressors", so the compressors are in the outer stack, which is where §0
puts the plant. Consistent without adjustment.

### 2.3 What the player experiences

Different air. Crossing into the Alien Sector should change the ambience track, the fog colour,
the exposure and the sound of one's own breathing before any sign says so. Encounter suits are
common in transit corridors and rare in sector interiors. And the compressors are audible from
Downbelow — a low beat that is the reason nobody chooses to sleep there.

---

## 3. Water

### 3.1 What is sourced

| Item | Where | Auth | Source |
|---|---|---|---|
| **Water storage** | Named in an **inner ring** of the Red rosette | 3 | `other map.png` |
| **Water reclamation** | Brown, around the outer hull with waste | 3/4 | Rosette; Downbelow description |
| **Water recreation facilities** | Schematic band 4 / the drum floor | 3 | Security Manual |
| **Showers are for executive suites and command quarters only** | — | 4 | Downbelow fan sources |

That last row is the most useful line of fan reconstruction in the whole gazetteer, and it is
adopted as **L-03**. It says water is *rationed*, which converts an invisible utility into a
visible class distinction: sonic cleaners for everyone, running water as a privilege of rank.
It also explains why Downbelow sits next to reclamation — proximity to the loop is the only way
to get water without status.

### 3.2 What is derived — L-04

| Quantity | Basis | Value |
|---|---|---|
| Drinking and food preparation | 3 L/person/day | 750 m³/day |
| Hygiene, laundry, cleaning | 50 L/person/day, rationed | 12,500 m³/day |
| **Total throughput** | | **13,250 m³/day** |
| 30-day strategic reserve | | **397,500 m³** |
| Reserve as a share of the plant zone | §0 | **0.3%** |
| Loop closure required | Resupply of 13,250 m³/day is 13,250 t/day of shipping — the traffic file's arrival rates are two orders of magnitude short of it | **>98%** |

**The last row is a hard constraint and it is checkable against another gazetteer file.**
`TRAFFIC-AND-CUSTOMS.md`'s arrival schedule cannot deliver 13,250 tonnes of water a day. So the
water loop is necessarily near-closed, reclamation is not optional infrastructure but the thing
the station lives on, and the sentence "water reclamation" on a rosette is load-bearing.

**Authority 5 on the per-capita figures, 3 on the placement. Overturned by:** any dialogue giving
a water ration figure.

### 3.3 What the player experiences

A tap is a status symbol. The Zocalo sells water. Downbelow queues at a standpipe. The reflecting
pool and the waterfall in the Garden's townscape (authority 1, `garden.png`) read completely
differently once the player knows what water costs — **conspicuous consumption in an environment
where hygiene is rationed**, which is exactly what a civic centre would build to say so.

---

## 4. Food

### 4.1 What is sourced

| Item | Where | Auth | Source |
|---|---|---|---|
| **Hydroponics** | Named in the Green rosette and as a schematic callout | 3 | `other map.png`; Security Manual |
| **Open agriculture** | The drum floor: hedged fields and a road curving up and over | **1** | `04-sector-red/Earhart's.webp` |
| **Longitudinal land-use bands** | Greys, olive-greens, one broad orange-red band | **1** | `talia-winters in gorgeous office.webp` |

`LOCATIONS.md` P-07 already rules that hydroponics is *racked and enclosed* and therefore sits in
the sub-floor deck stack, while the drum floor is *open fields*. This file agrees and adds the
reason: they are different crops for different reasons. Open drum agriculture is bulk calories
and atmosphere; racked hydroponics is high-value, fast-cycle and, critically, **species-specific**
— fifteen species do not eat the same thing, and six atmospheres means some of it has to be grown
in an atmosphere humans cannot enter.

### 4.2 What is derived — L-05

| Quantity | Basis | Value |
|---|---|---|
| Wet food consumed | 1.8 kg/person/day × 250,000 | **450 t/day** |
| Arable area on the drum floor | `LAND_USE` gives 48% arable across 4.5 M m² | ~2.16 km² |
| Yield needed if the drum fed everyone | 450 t/day over 2.16 km² | ~76 t/ha/yr |

**That last number is the finding.** 76 t/ha/yr is achievable for intensive continuous-cycle
agriculture under permanent artificial light with no seasons and no weather — but only just, and
only for staples. **The drum cannot feed the station alone**, which is precisely why hydroponics
is a separately named system and why `TRAFFIC-AND-CUSTOMS.md` has agricultural freight arriving.

So the station's diet is **three-sourced**: drum staples, hydroponic specialty and imported
luxury. That is a fact with texture — it means the Zocalo's food stalls sell visibly different
classes of goods at visibly different prices, and it means a docking strike is a food story.

**Authority 5. Overturned by:** any statement of the station's self-sufficiency.

---

## 5. Waste

### 5.1 What is sourced, and the distribution is the point

**"Waste management systems (Down-Below)" is named in THREE rosettes — Red, Green and Brown —
and twice on the sectional schematic**, always with that parenthetical (authority 3). Plus
**Waste Management Control** in the Brown rosette.

That repetition is not redundancy in the source; it is the source telling us the system is
**distributed**. Every sector has its own plant. There is no single sewage works.

**And it means every sector has its own candidate slum**, because Downbelow is defined by
proximity to this system. `LAW-CRIME-DOWNBELOW.md` should be read against this: the underclass is
not one district, it is a *stratum* that exists wherever the outer stack meets a waste plant.

### 5.2 What is derived — L-06

| Stream | Basis | Value |
|---|---|---|
| Solid organic | 0.15 kg/person/day dry | 37.5 t/day |
| Greywater and blackwater | Effectively all of §3's throughput | 13,250 m³/day |
| Packaging, industrial and non-recyclable | | ~40 t/day |
| CO₂ to scrub | §2 | 250 t/day |

Everything organic returns to §4 as fertiliser, which is what closes the loop and what makes the
drum's soil viable at all. **Nothing is jettisoned**: mass thrown away is mass that must be
bought back, and the traffic file cannot carry it.

### 5.3 What the player experiences

Smell, expressed as everything except smell — haze, particulate in the light shafts, dripping,
stained decking, an ambience track with a wet mechanical rhythm to it. The waste plants are the
loudest places on the station and people live beside them because it is the only place nobody
charges rent.

---

## 6. Industry

`schedule.py` already carries `grey_industrial` as a rotating 24-hour workplace sourced to
FACTIONS.md §2.5 — "fabrication furnaces, power, repair ... 24 h, 3 shifts". That is the roster.
The physical plant behind it:

| Function | Why the station must have it | Auth |
|---|---|---|
| **Fabrication and machine shops** | A station 8 km from anywhere cannot order a spare part. Repair is manufacture | 4/5 |
| **Foundry / furnaces** | Named in FACTIONS.md; a heavy heat and power load, which is why it is in Grey next to the distribution node | 4 |
| **Starfury and shuttle maintenance** | 24 docking bays and a fighter wing | 3 |
| **Hull and structural repair** | Micrometeorite and docking damage on 8,047 m of hull | 5 |
| **Recycling and reclamation plant** | §5 | 3 |

**Why Grey.** Grey holds 105 of the station's 251 decks and all 34 of its plant decks; it sits at
the widest part of the hull, next to the mainstage power distribution node and immediately
forward of the reactor assembly. High gravity is an *advantage* for a foundry — settling,
casting, separation and drainage all want weight. **The one place on the station you would not
put a bedroom is the best place to put a furnace**, and the geometry put both facts there before
anyone chose.

---

## 7. Contradictions and open questions

| # | Issue | Status |
|---|---|---|
| **L-A** | The plant zone is 559 m³ per resident — ~100× what life support needs. Either the plant zone is mostly structure and void (adopted, §0), or `HABITABLE_G_MAX` is too low and Grey's middle decks are habitat after all | **Adopted the first reading.** The second is not refuted, but 1.25 g is already generous and lowering the ceiling makes Downbelow's canon gravity worse, not better |
| **L-B** | Waste is named in Red, Green **and** Brown rosettes, but only Grey has plant decks under the gravity model. Either those sectors have plant that is not gravity-excluded, or "outermost ring" means something different per sector | **Open.** Likely the former: a waste plant does not need 1.25 g to be a waste plant. The `use` tag is about *billeting*, not about what a deck contains — a plant can sit on a habitat deck |
| **L-C** | The 1.9 GW figure is authority 5 and the radiator cross-check only bounds it to within a decade | **Open, and probably permanently.** Recorded as a decade, not a number |
| **L-D** | Six atmospheres, five of them unnumbered | **Open.** Deliberately not invented — see §2.1 |

**L-B is the one to act on**, and it is a modelling gap rather than a research gap: the current
model conflates "what gravity is here" with "what is built here". A deck should carry a
`use` (billeting) and a *function* (what plant is on it), and those are orthogonal. Recorded for
the next structural increment rather than patched here.

---

## 8. What this file changes about what gets built

Ranked by how much work it redirects.

1. **Stop building 34 plant decks as corridor.** 62.3 M triangles — 26% of the station's interior
   — is currently budgeted for walkable annulus that should be structure, tankage and void with a
   thin walkable skeleton. This is the largest single piece of misdirected content in the project
   and it was invisible until the plant zone had a volume. `budget.py` already flags it as priced
   with the wrong kit; the kit itself does not exist yet.
2. **Build the plant kit.** Tank farm, deep frames, catwalks, pipe runs, pumps, heat exchangers.
   Cheap per cubic metre, visually dense, and it is Downbelow's architecture as well as the
   plant's — the same kit dresses both, which is exactly why they are the same place.
3. **Downbelow is reached by descending into the plant.** No door, a service stair, and four decks
   later you weigh 30% more. Build the transition, not a district boundary.
4. **Six atmospheres needs locks.** Independently conditioned volumes with airlocks between them
   is a traversal mechanic and a rendering boundary, and nothing in the interior kit has one yet.
5. **The Garden is a lung.** Whatever dresses the drum floor has to read as productive
   agriculture at 2 km², not as parkland with a farm feature.

---

## Cross-references

- `docs/gazetteer/LOCATIONS.md` — §294–310 are the power, water and waste rosette callouts this
  file expands; P-07 rules on hydroponics placement
- `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` — Downbelow's population; read §0 of this file against it
- `docs/gazetteer/TRAFFIC-AND-CUSTOMS.md` — the freight rates that force loop closure (§3.2, §4.2)
- `docs/gazetteer/FACTIONS.md` §2.5 — the industrial roster
- `canon/INVENTIONS.md` INV-027 — the habitable gravity ceiling and the plant/habitat split
- `station/signage.py` — the six-atmospheres board, verbatim
- `station/interior.py` — `habitable_radius()`, `decks_in_ring()`'s `use` tag
