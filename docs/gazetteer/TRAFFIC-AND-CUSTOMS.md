# TRAFFIC AND CUSTOMS — Babylon 5 as a port

What arrives, how it gets in, who checks it, and what it carries. **Era lock: Season 2–3.**
Sheridan commanding, Garibaldi Chief of Security, Ivanova XO, the defence grid installed, all
League ambassadors resident, Narn–Centauri war running through S2 into S3, pre-secession,
pre-war-damage.

This document is a *specification for simulation*, not a canon source. It is downstream of
`canon/00-MASTER.md` and `canon/CONFLICTS.md` and may not override either. It is a sibling of
`docs/gazetteer/LOCATIONS.md`, which places the rooms; this one drives the ships and the people
through them. Where the two touch — the customs hall, the docking bays, the jump gate — the
placement is LOCATIONS.md's and the process is this file's.

---

## 0. How to read this

### 0.1 Authority

| | |
|---|---|
| **1** | on-screen footage — a frame we hold in `reference/`, cited by path |
| **2** | production material — blueprints, production-model renders |
| **3** | licensed print — the two Security Manual sheets, Contract 5 |
| **4** | fan reconstruction — wikis, fan sites, forums, episode transcripts on fan sites |
| **5** | our own extrapolation, with the reasoning given |

> **Method caveat, stated once, applying to every authority-4 row in this file.**
> `WebFetch` returned **HTTP 403 from the proxy on every host tried** this session —
> `babylon5.fandom.com`, `b5tv.com`, `midwinter.com`, `b5tech.org`,
> `springfieldspringfield.co.uk`, `subslikescript.com`. Authority-4 content was therefore read
> through **WebSearch result summaries**, not by reading the pages. The URL cited is the page the
> summary was drawn from. This is the same constraint `LOCATIONS.md` §0.1 records, and it bites
> harder here: **§5.1's traffic figure and §7.4's garden figures both turn on a qualifier a
> summary can drop**, and one of them is demonstrably wrong as summarised. A future session with
> unrestricted egress should re-read those two pages first.

### 0.2 Confidence

| | |
|---|---|
| **STATED** | a source states it outright. *Check the authority column* — an authority-4 STATED is a fan wiki asserting a thing, not the show saying it. |
| **DERIVED** | computed here from something already in this repository. The computation is shown. |
| **PROPOSED** | our reasoning, keyed `T-nn`, given in full in §10. Authority 5. |

### 0.3 The numbers this file inherits

From `canon/00-MASTER.md`, `station/schema/station.yaml` and `station/physics/`:

| | value | why it matters to the port |
|---|---|---|
| Station length | 8,047 m (auth 1) | a 1,600 m warship is a fifth of the station; it cannot berth |
| Population | 250,000 (auth 1) | sets the passenger flow |
| ω | 0.187717056 rad/s | every rotating berth |
| Rotation period | **33.4716 s** | the roll rate an arriving ship must match |
| Drum floor speed | 52.2 m/s at r = 278.3 m | the *drum* rim, not the docking bays — see §4.6 |
| Docking bays | **24**, Blue Sector (auth 3) | the berth count that sets throughput |
| Bay elevators | **2** (auth 3) | the bottleneck between bay mouth and interior |
| Cobra bays | 28 (auth 3) or 24 (auth 4) — C-002 open | Starfury launch and recovery |
| Cargo bays | 42 = 28 rotating + 14 support (auth 4) | internal volumes, *not* the 6 external modules |
| Customs halls | **2**, north and south (auth 3) | the two chokepoints every visitor passes |
| Atmospheres | **six** standing, humans are **02** (auth 1) | a customs check, not decoration |
| Station clock | **Earth Mean Time** (auth 1) | schedules, boards, announcements |

---

## 1. CONTRADICTIONS AND CORRECTIONS

Reported, not smoothed over. Nothing here is resolved in this file.

| # | The claim | Conflicts with | Assessment |
|---|---|---|---|
| **T-X1** | *"Liner White Star arriving from Earth is now docking in bay 5. Passengers will disembark through **customs area 7**."* — station announcement, "TKO" (S1E14), auth 4 via transcript summary, http://a1bert.kapsi.fi/Quotes/NoRobots/B5/014.html | Security Manual sectional schematic (auth 3): **customs ×2**, north and south. `LOCATIONS.md` §4 carries the two. | **Probably not a contradiction — probably the resolution.** Two customs *halls* (the architectural units the schematic counts), each containing numbered processing *areas* (the desks a passenger is sent to). Seven areas across two halls is ~4 per hall, which matches a hall with a bank of desks. **Adopted as the working model in §6.3, marked PROPOSED, because the reconciliation is ours.** Overturned by any frame showing "customs area" signage with a number above 8, or a third hall. |
| **T-X2** | *"On a daily basis, over 50 to 60 ships used it as a waypoint, nearly 95% of this traffic was purely civilian and **over 200,000 individuals arrived and departed** Babylon 5."* — auth 4, https://babylon5.fandom.com/wiki/Babylon_5 | Itself, and `00-MASTER.md`'s population of 250,000 (auth 1) | **Internally impossible as summarised.** 200,000 people across 55 ships is **3,636 per ship**, and it moves 80% of the station's entire population every day. Either the sentence's "daily" governs only the ship count and the 200,000 is annual, or the summary has dropped a period qualifier. **The ship count is retained (§5.1) because it cross-checks independently against the berth count; the 200,000 is not used.** §5.3 reasons the passenger flow from first principles instead. *This is exactly the qualifier-loss the §0.1 caveat warns about.* |
| **T-X3** | The Garden's vegetative area *"covers **12 square miles**"* with *"twenty meters of dirt"* and *"**four levels** of hydrobays"* beneath — auth 4, https://www.oocities.org/davesb5page/xplor.htm | `00-MASTER.md` §1.1: bio-habitat inner surface **4,787,500 m² = 1.85 sq mi**. `station/interior.py`: **9** sub-floor decks. | **Two real contradictions and authority beats both.** 12 sq mi is **31.08 km², 6.49× the whole drum's inner surface** — computed here; the drum cannot contain it at 8,047 m station length. The four levels vs our nine is a softer disagreement (a "level" need not be a deck — `LOCATIONS.md` §1). **Consequence for this file: B5 cannot feed itself from the Garden at the implied intensity, so the import tonnage in §7 must be reasoned from the real area, not the fan area.** |
| **T-X4** | *"about 100,000 humans"* and *"approximately **42%** of the station population, including visitors, is alien"* — auth 4, https://babylon5.fandom.com/wiki/Babylon_5 | Each other | 100,000/250,000 = **40% human**; 42% alien = 105,000. **The two sum to 82%** and leave 45,000 people unclassified. **This is the same failure mode `station/npc/schedule.py` already shipped once** (session 2m: the species mix summed to 0.94 and silently dropped 120 in every 2,000). Do not seed the traffic model's species mix from these two numbers without normalising, and assert the normalisation. |
| **T-X5** | `station/physics/test_starfury.py:114` and `test_docking.py:26` both build their example bay at **`drum.floor_radius` (278.3 m), z = 5400** | `station/schema/station.yaml`: `cobra_bay` is `z0: 6980, z1: 7250`; `docking_sphere` is `z 6939–7286`. z = 5400 is inside `habitat_cylinder` (4826–6035). | **Not a bug — a fixture that reads as a fact.** Both suites are *correct as tests*; neither claims to place a bay. But STATE.md reports the result as "cobra bay launch works… carries 52.2 m/s", and a builder will inherit that number. **Measured from `radius_profile.json` at the schema's own cobra-bay band, the hull radius is 190–260 m, so the launch fling is 35.5–48.7 m/s and the local gravity 0.68–0.93 g** — the headline figure is overstated by **7–32%**. §4.6 carries the corrected table. Cheap to fix; expensive to discover after a launch animation is tuned. |
| **T-X6** | Fan sources give the Minbari **Sharlin** 1,600 m and the EA **Omega** 1,714 m (auth 4, §3) | `Minbari Flyer 969 in docking bay 17.webp` (auth 1): a Minbari *flyer* "spans most of the bay width" | Not a contradiction, but the consequence is load-bearing and no source states it: **capital ships cannot enter a bay.** A 1,600 m hull is 20% of the station's total length. §4.7 makes external mooring the rule for anything above the bay limit, and derives the limit. |
| **T-X7** | "White Star" as a **liner arriving from Earth** ("TKO", auth 4) | The **White Star** class Minbari/Ranger warship of S4–5 | **Name collision, not a contradiction — and an era trap.** In S2–3 "White Star" is a civilian liner name and nothing else. An implementer who has seen S4 will build the wrong ship. Flagged here because it is the kind of error that survives review. |

---

## 2. THE JUMP GATE

### 2.1 What is established

| # | Fact | Conf. | Auth | Source |
|---|---|---|---|---|
| JG-1 | B5 lies in the **L5 point in orbit around Epsilon III**, Epsilon Eridani, **positioned near the local jumpgate**; the system's primary jumpgate is in high orbit above Epsilon III | STATED | 1 (location) / 4 (the gate's placement) | `00-MASTER.md` §1; https://babylon5.fandom.com/wiki/Babylon_5 |
| JG-2 | A jumpgate is a **spaceborne structure of three or four separate but aligned struts** that generates a spatial vortex — a **jump point** — into hyperspace | STATED | 4 | https://babylon5.fandom.com/wiki/Jumpgate |
| JG-3 | **Each strut: 3.2 km long (2 miles), 60 m high (200 ft), 180 m wide (600 ft)** | STATED | 4 | same |
| JG-4 | The struts each generate **four stable energetic forces of opposing polarity**; worked against each other these create a vacuum effect, forming an unstable vortex that tears the spacetime continuum | STATED | 4 | same |
| JG-5 | The gate **supplies the energy for ships that have no jump engine of their own**, and **large ships often use gates in preference** to opening their own point | STATED | 4 | same |
| JG-6 | **Fighters cannot create their own jump points.** This is part of the vessel classification, not a property of one class | STATED | 4 | https://babylon5.fandom.com/wiki/Space_Vessel_Classifications |
| JG-7 | The gate **holds the jump point open until the vessel has completed transit** — duration is transit-bound, not a fixed interval | STATED | 4 | http://www.thefullwiki.org/Jumpgate_(Babylon_5) |
| JG-8 | A **ship-generated** jump point is a heavy continuous power draw; the ship is effectively **blind for a few seconds** on opening, so the practice is to open and transit immediately | STATED | 4 (forum — the weakest source in this file, flagged as such) | https://www.b5tv.com/threads/jump-gate-question.1998/ |
| JG-9 | **Hyperspace is featureless with no points of reference.** Navigation is by a **beacon network** at known realspace points, usually the gates themselves; a ship without a jump engine finds its exit gate by beacon | STATED | 4 | https://babylon5.fandom.com/wiki/Hyperspace |
| JG-10 | Hyperspace is **red-hued** | STATED | 4 | same |
| JG-11 | B5's gate is a **junction of hyperspace routes between the Earth Alliance, the Narn Regime and several non-aligned worlds** — the reason the station is commercially viable | STATED | 4 | https://babylon5.fandom.com/wiki/Babylon_5 |
| JG-12 | The gate sits **far enough out that a hostile arrival can be identified and intercepted, close enough that gate-to-station transit is quick** | STATED (qualitatively only) | 4 | https://thewertzone.blogspot.com/2017/06/babylon-5-rewatch-setting-scene-babylon.html |
| JG-13 | Station-side, the arrival is met by a **primary navigation beacon** (1) and **space traffic proximity arrays** (4), both already generated as exterior components | STATED | 3 | Contract 5; `00-MASTER.md` §2 items 19, 24; `station/schema/station.yaml` |
| JG-14 | A ship on approach **locks on to a named beacon**: *"Transport Von Braun, lock on to beacon Alpha 5"* | STATED | 4 (transcript summary, "Grail" S1E15) | https://subslikescript.com/series/Babylon_5-105946/season-1/episode-15-Grail |

### 2.2 What is NOT established, and what we propose

**The reference set contains no jump gate and no jump point.** `reference/01-station-exterior/`
holds five files, `13-other-ships/` holds one, and none is a gate, a vortex or an arrival. Every
visual claim below is authority 5. **This is the single largest reference gap this document
opens** — see §11.

| # | Unknown | Proposal | Tag |
|---|---|---|---|
| JG-P1 | **Distance from station to gate.** Never stated in any source found. | **65 km**, gate centre to station centre, on the station's forward (+Z) side, offset ~15° off the long axis so the gate is visible from C&C's window without sitting behind the deflector spike. | **T-01** |
| JG-P2 | **Jump point diameter and duration.** | Aperture **500 m** for a gate-formed point; **open 20 s** nominal per transit, extended while a hull is still inside. A ship-formed point is **1.2× the beam of the ship forming it** and closes 4 s after the stern clears. | **T-02** |
| JG-P3 | **Gate cadence.** | One transit at a time; **~110 s minimum between transits** in the same direction to clear the exit volume. | **T-02** |
| JG-P4 | **The gate's own appearance.** | Four struts (JG-2 permits three or four; four gives the symmetry the aperture needs), each 3.2 km × 180 m × 60 m per JG-3, arranged on a 3.5 km circle about a common axis, tips inboard. **The struts are the only sourced dimensions in the whole gate and they should be honoured exactly.** | **T-02** |

**Why the distance matters more than it looks.** It sets the whole rhythm of the port. At 65 km,
a transport flying accelerate-flip-decelerate at a comfortable 0.3 g runs gate-to-station in
**5.0 minutes** (6.1 min at 0.2 g, 8.6 min at 0.1 g); a Starfury at the Aurora's measured
**18.38 m/s² on the mains** (`station/physics/starfury.py`, STATE.md session 2f) does it in
**2.0 minutes** flat-out. Both are short enough to watch and long
enough to be a journey. It also puts the gate at **8× the station's own length**, so from the
station the gate is a structure you can see and not read — which is the right visual relationship.
The `station/physics/floating_origin.py` work already measured float32 at 50 km as **3.91 mm** of
positional error, so 65 km is inside the range double precision was adopted for and outside the
range float32 survives. That is a *constraint satisfied*, not a coincidence.

### 2.3 What a transit looks like, for the simulation

Authority 5 throughout, built on JG-2, JG-4, JG-7 and JG-10.

1. **Formation.** A point of light at the gate's focus; the four struts' discharge arcs converge
   on it. 2–3 s.
2. **Iris.** The point opens into a vortex — the tear of JG-4 — reaching full aperture in ~2 s.
   Realspace side reads blue-white; the throat reads **red** (JG-10).
3. **Hold.** The gate feeds it (JG-7). The vortex is not static: it should churn.
4. **Transit.** The hull emerges nose-first, lit by the vortex, and the vortex light is the
   dominant key on it for the 3–6 s it takes a 60 m transport to clear.
5. **Collapse.** 4 s after the stern clears, in reverse.

**Two visual rules that follow and are worth writing down.** A jump point is a *light source* —
for those seconds it is the brightest thing in the exterior scene and it should key the station's
forward hull, not just the ship. And the arriving hull is **backlit against the vortex before it
is front-lit by the station**, which is what makes an arrival read as an arrival.

---

## 3. SHIP CLASSES THAT VISIT

Lengths are what the project needs; adjectives are not. **Every dimension in this table is
authority 4** and most come from role-playing and technical-manual reconstructions that the
Babylon 5 wiki itself flags as varying widely between sources. They are good enough to build a
size *hierarchy* from, which is what matters; they are not good enough to assert as canon.

### 3.1 The classification scheme

Five classes, authority 4, https://babylon5.fandom.com/wiki/Space_Vessel_Classifications:
**fighters** (small, one or two crew, *cannot* open their own jump points) · **warships** ·
**freighters** (cargo; *Achilles-type* named as the commonest Earth Alliance and independent
freighter) · **liners** (passengers; *Asimov class* named) · **shuttles**.
This is the taxonomy the traffic generator should use, because it is the show's own.

### 3.2 The table

| # | Ship | Class | Length | Other | Auth | Source / note |
|---|---|---|---|---|---|---|
| S-1 | **SA-23E Aurora Starfury** | fighter | **10.7 m** | width **18.6 m**, height **4.4 m**; our model masses it 14,800 kg loaded and gives 18.38 m/s² on the mains | 4 (dims) / 5 (mass, thrust) | https://babylon5.fandom.com/wiki/SA-23E_Mitchell-Hyundyne_Starfury; `station/physics/starfury.py` |
| S-2 | **EA crew shuttle** | shuttle | **18.6 m** | the small personnel runabout | 4 | https://babylon5.fandom.com/wiki/Earth_Alliance_Crew_Shuttle |
| S-3 | **EA atmospheric shuttle** (Kestrel class) | shuttle | **29 m** | atmosphere-capable | 4 | https://babylon5.fandom.com/wiki/Kestrel_Class_Atmospheric_Shuttle |
| S-4 | **EA standard shuttle** | shuttle | **50 m** | the large shuttle; upper end of what a bay elevator should take easily | 4 | https://kitsunesden.xyz/SF-Conversions/Rifts-B5-Ships/Earth_Standard_Shuttle.htm |
| S-5 | **Centauri Brezebel** freighter/transport | freighter | **60 m** | the smallest named freighter figure found | 4 | https://www.meshweaver.com/b5-craft-comparison-study2.html |
| S-6 | **"Delta Gamma 9" type transport** | transport | **not stated** | commercial, operated by **United Spaceways**; the type named in the pilot's docking sequence. **A named in-universe operator is worth more to this project than a length** — it gives hull livery, ticketing and a company to blame | 4 | https://babylon5.fandom.com/wiki/%22Delta_Gamma_9%22_Type_Transport |
| S-7 | **Achilles-type freighter** | freighter | not stated | named as the **commonest** EA/independent freighter — so this is the ship the port sees most | 4 | https://babylon5.fandom.com/wiki/Space_Vessel_Classifications |
| S-8 | **Asimov class liner** | liner | not stated | named as the type example for passenger liners | 4 | same; https://babylon5.fandom.com/wiki/Asimov_class |
| S-9 | **Narn freighter** | freighter | not stated | cargo *and* passengers; a Narn cargo vessel is the ship in the S1 docking accident (§9) | 4 | https://babylon5.fandom.com/wiki/Narn_freighter |
| S-10 | **Minbari flyer** | shuttle/transport | not stated | **authority 1, and the only in-bay scale we hold**: it "spans most of the bay width" and dwarfs two crew on the upper gantry | 1 | `reference/03-sector-blue/Minbari Flyer 969 in docking bay 17.webp` |
| S-11 | **Vorlon transport (Kosh's)** | diplomatic | not stated | **authority 1.** Organic: hard-edged chartreuse blotches on matte black, iridescent blue-violet accents, an eye and an open bore at the nose, six tapering tentacles and 3–4 blade-fins astern | 1 | `reference/13-other-ships/kosh's transport.webp` |
| S-12 | **Centauri Haven patrol boat** | warship | **370 m** | | 4 | https://www.meshweaver.com/b5-craft-comparison-study2.html |
| S-13 | **Brakiri Avioki cruiser** | warship | **550 m** long, **710 m tall** | taller than it is long — a distinctive silhouette at a standoff berth | 4 | same |
| S-14 | **Drazi Warbird** destroyer / **Stormfalcon** cruiser | warship | **565 m** / **665 m** | | 4 | same |
| S-15 | **Vree saucers** — Vaarl scout / Xorr war saucer / Xill battle saucer | scout, warship | **420 / 460 / 645 m** diameter | discs, not hulls; they need a different mooring solution | 4 | same |
| S-16 | **EA Hyperion class heavy cruiser** | warship | **1,025.4 m** | mass 8,400,000 t, crew 356 + 200 troops. The EarthForce workhorse of the era | 4 | https://babylon5.fandom.com/wiki/Hyperion_class_heavy_cruiser |
| S-17 | **Narn G'Quan class heavy cruiser** | warship | **1,100–1,400 m** (sources disagree) | the wiki states outright that specifications "vary widely in non-canon sources" | 4 | https://babylon5.fandom.com/wiki/G'Quan_class_heavy_cruiser |
| S-18 | **Minbari Sharlin warcruiser** | warship | **1,600 m** long, **~1,900 m tall** | the figure Mongoose adopted for the **licensed** B5 RPG — so the underlying source is authority **3** and would upgrade if read directly. Read here via a fan summary, so recorded as 4 | 4 (as read) | https://infogalactic.com/info/Sharlin_Class_Warcruiser |
| S-19 | **EA Omega class destroyer** | warship | **1,714 m** | **has its own rotating section** for gravity, so it is the one visiting ship that spins. Front-and-rear armament, fewer guns than the Nova because the rotating section eats the power | 4 | https://en.everybodywiki.com/Omega-class_destroyer |
| S-20 | **Tugs and station service craft** | — | **not established by any source found** | Nothing in canon, in the reference set or in any web source consulted describes a Babylon 5 tug, lighter or bay tender. **The station cannot work without them** — 42 cargo bays and a zero-g spinal transfer facility imply powered movers. PROPOSED, **T-11** | 5 | — |

### 3.3 What the size hierarchy means for geometry

Three tiers, and they are the reason the station has three different kinds of berth.

| tier | length | berths where | why |
|---|---|---|---|
| **Bay-class** | up to ~**100 m** (T-03) | one of the **24 rotating docking bays**, via the axial mouth and a bay elevator | fits the elevator; can be spun up by station machinery |
| **Standoff-class** | ~100 m to ~**400 m** | the **low-g / zero-g bays** on the non-rotating spine, or the **primary and service docking ports** (north and south, auth 3) | too long for a bay elevator (auth 4, https://www.oocities.org/davesb5page/xplor.htm), but small enough to make hull contact |
| **Moored-class** | above ~400 m | **hard docking mooring clamps** (auth 3), or free station-keeping with lighters running the gap | a 1,600 m hull cannot contact an 8,047 m station without becoming a structural load case |

The ~100 m bay limit is **PROPOSED (T-03)** and derived in §10, not stated anywhere.

---

## 4. DOCKING, END TO END

### 4.1 The procedure, as the show gives it

Every step below is dialogue or a fan reconstruction of it. This is the strongest evidence in the
whole document, because it is procedure spoken aloud on screen.

| # | Step | Evidence | Auth |
|---|---|---|---|
| D-1 | **Request clearance by name.** *"Transport Von Braun requesting clearance."* | "Grail" (S1E15), transcript summary | 4 |
| D-2 | **Bay assigned by number.** *"Transport Von Braun, you're cleared for Bay 7."* Elsewhere *"Final approach to Docking Bay 12B"* — so bays carry **letter suffixes as well as numbers** | "Grail"; *The Gathering* | 4 |
| D-3 | **Lock to a named beacon.** *"…lock on to beacon Alpha 5."* | "Grail" | 4 |
| D-4 | **Approach vector issued.** *"Approach vector 557."* | *The Gathering* | 4 |
| D-5 | **Surrender control.** *"Please surrender control of your vessel to central computer, on my mark. Mark…"* | *The Gathering* | 4 |
| D-6 | **C&C spins the ship to match the station.** C&C runs a program that rotates the arriving hull at the station's rate, so that on entry the ship's "down" is the station's "down" | https://www.oocities.org/davesb5page/xplor.htm | 4 |
| D-7 | **All ships enter dead centre**, on the zero-g axis, then are transferred out to the assigned bay. A second facility handles craft that stay in freefall | same | 4 |
| D-8 | **Bay elevators (2)** move craft between the axial mouth and the bay | Security Manual, "BAY ELEVATORS (2)" | 3 |
| D-9 | **Berthing is a two-stage park.** *"…we will bring you to landing pad four, and then take you down to the parking level."* — so a bay has a **landing pad** and a **parking level below it** | *The Gathering*, Narn cargo ship *Tal'Quith* | 4 |
| D-10 | **Bays offer a choice of gravity from 0 g to 1 g**; higher-gravity bays nearer the hull, lower nearer the axis | https://www.oocities.org/davesb5page/xplor.htm | 4 |
| D-11 | **The public announcement follows.** *"Liner White Star arriving from Earth is now docking in bay 5. Passengers will disembark through customs area 7."* | "TKO" (S1E14) | 4 |

### 4.2 The rotating-station problem — and the fact that the show already solved it

The brief poses this as *"the docking bay is in the rotating section, so ships must match spin."*
That is true, and **D-6/D-7 say the match is a roll, not a chase.** The distinction is the single
most important structural finding in this document, so it is set out explicitly:

- A ship that flew at a bay mouth **on the rim** would have to match the bay's **tangential
  velocity** — tens of metres per second, on a heading that sweeps a full turn every 33.47 s. Our
  own model measures the failure: a craft that gets the closing rate right but does not spin-match
  arrives with **52.2 m/s of lateral drift** and scrapes along the hull
  (`test_docking.py`, "failing to spin-match is rejected on lateral drift").
- A ship that enters **on the axis** has **no tangential velocity to match at all** —
  `docking.axial_approach_is_trivial()` exists in the module for precisely this reason, and
  `test_docking.py` asserts an axial port's velocity is zero to 1e-12. All it must match is
  **angular rate about the axis: 1.7926 rpm, one turn per 33.4716 s.**

So the canon procedure is: fly the axis, roll to 1.79 rpm, hand over to C&C, be carried outward
by a bay elevator into a berth that is already turning with you. **Civilian traffic never solves
the hard docking problem.** The station solves it for them, with machinery.

**This is enormously good news for the simulation.** Fifty-five arrivals a day do not need
fifty-five AI pilots running interception guidance; they need one traffic-control system driving
hulls along precomputed axial tracks with a roll ramp. The expensive solver is needed **only for
the player's Starfury and the cobra bays**, which is exactly where the fun is.

And it is visually distinctive in the way the brief asks for: a 60 m transport **rolling on its
long axis at 1.79 rpm** as it slides into the station's mouth is an image that no other space
station gives you, and it is a direct consequence of geometry we have already built.

### 4.3 The eight phases, as a state machine

Authority 4 for the sequence (§4.1), authority 5 for the numbers. This is what the traffic actor
should implement.

| phase | what happens | duration | notes |
|---|---|---|---|
| **1 · Gate transit** | jump point forms, hull emerges | 20 s at the gate | §2.3 |
| **2 · Beacon acquisition** | lock to a named beacon (D-3) | — | beacon names are `<Greek letter> <digit>`, e.g. Alpha 5 |
| **3 · Inbound run** | 65 km (T-01) under the ship's own power | **4–7 min** for a transport at 0.2–0.3 g | this is the window in which C&C hails, argues, or refuses |
| **4 · Clearance and hold** | request by name, bay assigned, vector issued (D-1, D-2, D-4) | variable | **holds happen here**, and a hold is content: a queue of parked hulls off the nose |
| **5 · Handover** | *"surrender control … on my mark"* (D-5) | instant, but ceremonial | the moment the player, if flying, loses the stick |
| **6 · Roll match and axial entry** | C&C spins the hull to **1.7926 rpm** and flies it down the centreline into the mouth (D-6, D-7) | roll ramp **~30 s**, entry **~60 s** | one full station revolution is 33.47 s, so the ramp is about one turn |
| **7 · Elevator transfer** | bay elevator carries the craft outboard to the assigned bay (D-8) | **~90 s** (T-04) | **the bottleneck: there are two elevators for 24 bays** |
| **8 · Berth** | landing pad, then down to the parking level (D-9); shutdown, ramp out | — | announcement fires here (D-11) |

**The two-elevator bottleneck is a genuine simulation constraint, not colour.** At 90 s out, 90 s
back and ~120 s of loading and securing, one elevator does **12 movements an hour** and the pair
does **24**. Against §5's traffic — ~110 movements a day, peaking at ~15 an hour — that is
**62% utilisation at the peak and about 20% on average.** So the port has spare capacity that is
usually invisible and occasionally not: a liner disgorging while freight is still turning round, or
**one elevator out of service**, and the queue becomes real. That is precisely the texture the
brief asks for, and it falls out of an authority-3 count of two rather than being designed in.
**"One elevator down" is the cheapest high-value event in this whole document.**

### 4.4 Traffic control

| | | Auth |
|---|---|---|
| Controlling authority | **C&C**, inside Observation Dome 1 on the forward docking structure | 3 (Contract 5 names Dome 1 = C&C); 1 (the room, `reference/03-sector-blue/comand and contorl.webp`) |
| Why C&C's window faces where it does | it looks out along **the approach vector for the docking bays** | 4, https://www.oocities.org/davesb5page/xplor.htm |
| Sensors | **space traffic proximity arrays (4)** and the **traffic control sensor array** inside the docking sphere | 3, Contract 5; `station/schema/station.yaml` |
| Overflow / approach-control annexe | **Observation Dome 2** — counted by Contract 5, function never stated. `LOCATIONS.md` P-11 proposes exactly this | 3 (exists) / 5 (function) |
| Comms discipline | ship addressed **by name and type** ("Transport Von Braun", "Narn cargo ship Tal'Quith"), never by registry alone | 4 |

### 4.5 Departure

No source found describes a departure sequence. **Reversal of §4.3 is the proposal (T-10)**, with
three asymmetries that are not merely the arrival backwards:

1. **Departure clearance is a customs act, not a traffic act.** Outbound manifests and exit visas
   are checked before the ship is released (§6.5). A ship can be cleared to *fly* and held on
   *paperwork*.
2. **The station gives the hull back its spin for free.** Released from a bay at the hull radius,
   a departing ship inherits the local tangential velocity — the same effect
   `station/physics/starfury.py::launch_from_drum` already models. At the docking sphere's
   190–260 m radius that is **35.5–48.7 m/s** of free outbound velocity, aimed tangentially.
3. **The gate is the queue, not the station.** §2.2 proposes one transit at a time with a ~110 s
   spacing, so departures stack at the gate, not at the bay. Outbound hold points belong at
   the gate end of the corridor.

### 4.6 Corrected berth-speed table — DERIVED

`test_docking.py` and `test_starfury.py` both use `drum.floor_radius` (278.3 m) at z = 5400 as
their example berth. That z is inside the **habitat cylinder**, not the docking structure. The
real bays are forward. Radii read from `station/schema/radius_profile.json` at the schema's own
component z-ranges; v = ωr and g = ω²r with ω = 0.187717056 rad/s:

| berth | z (m) | hull radius | **tangential speed** | **local gravity** |
|---|---|---|---|---|
| Docking sphere, aft end | 6,939 | 193.3 m | **36.3 m/s** | 0.695 g |
| Cobra bay band, forward | 7,000 | 189.3 m | **35.5 m/s** | 0.680 g |
| Cobra bay band, mid | 7,100 | 227.9 m | **42.8 m/s** | 0.819 g |
| Cobra bay band, aft | 7,200 | 259.6 m | **48.7 m/s** | 0.933 g |
| Docking sphere, fore end | 7,286 | 215.7 m | **40.5 m/s** | 0.775 g |
| *(drum floor, for comparison)* | *5,400* | *278.3 m* | *52.2 m/s* | *1.000 g* |
| **Axial port / low-g bay** | any | **0 m** | **0.0 m/s** | **0.000 g** |

**Every rotating berth turns once per 33.4716 s regardless of radius** — that is the one number
an approaching pilot can rely on, and it is why the roll match works at any berth.

### 4.7 Ships too big to berth

Nothing in canon states a bay's dimensions. What we hold:

- **Authority 1:** a Minbari flyer "spans most of the bay width" and dwarfs two crew
  (`Minbari Flyer 969 in docking bay 17.webp`).
- **Authority 1, measured:** the red deck disc in `dock.webp` is **9–11 m across**, sized against
  eleven dock workers at 1.75 m (`reference/00-INDEX.md`). Deck markings at that scale imply a
  bay measured in tens of metres, not hundreds.
- **Authority 3:** the bay ceiling is the **ribbed inner wall of the rotating drum** — the bay is
  cut into the hull, so bay depth is bounded by the ring stack beneath it.
- **Authority 4:** large transports are **too long for the bay elevators** and use the low-g bays.

**T-03 proposes a bay envelope of 110 m long × 40 m wide × 18 m clear**, and therefore a
**~100 m practical ship limit**, derived in §10. Above that: low-g bays, then the north and south
docking ports, then mooring clamps, then free standoff with lighters. A **Sharlin at 1,600 m or
an Omega at 1,714 m never touches the station** — it parks off the hull, and everything and
everyone that comes off it arrives by shuttle. That is a whole category of traffic on its own,
and it is *more* interesting than a berth: it puts a warship in the window.

---

## 5. ARRIVAL RATES

### 5.1 The one sourced figure, and its cross-check

> *"On a daily basis, over 50 to 60 ships used it as a waypoint, nearly 95% of this traffic was
> purely civilian…"* — authority 4, https://babylon5.fandom.com/wiki/Babylon_5

**Retained**, because it survives an independent check the source knows nothing about.

The Security Manual (authority 3) counts **24 docking bays**. A berth turned round in a mean of
10 hours gives 24 × 24 / 10 = **57.6 ship movements a day**. The sourced figure is 50–60. Two
numbers from unrelated sources, agreeing to within a couple of percent, on a quantity neither was
computed to match. Full sensitivity:

| mean berth occupancy | movements/day from 24 bays |
|---|---|
| 6 h | 96 |
| 8 h | 72 |
| **10 h** | **57.6** ← agrees with the sourced 50–60 |
| 12 h | 48 |
| 24 h | 24 |

**Working figure: 55 ship arrivals and 55 departures per day**, i.e. **one movement every
13 minutes** around the clock. That is the tempo of the port: something is always moving, nothing
is ever crowded.

The 95% civilian split gives **~52 civilian and ~3 military movements a day**, which puts an
EarthForce hull at the station most days and a *capital* ship — the interesting kind — perhaps
weekly.

### 5.2 The daily manifest — PROPOSED (T-05)

Authority 5. Reasoned to hit 55 arrivals/day, the 95/5 split, and the §3.3 size tiers. Percentages
are of arrivals.

| ship type | arrivals/day | % | berth | souls aboard | typical stay |
|---|---|---|---|---|---|
| Freighter, bay-class (Achilles-type, Narn, Brakiri) | **20** | 36% | docking bay | 6–15 crew | 8–14 h |
| Transport, small/medium (Delta Gamma 9 type) | **14** | 25% | docking bay | 20–80 pax + 6 crew | 6–12 h |
| Shuttle, in-system and ship-to-station | **12** | 22% | docking bay, low-g | 2–20 | 1–4 h |
| Freighter, standoff-class | **4** | 7% | low-g bay / docking port | 10–30 crew | 12–36 h |
| Diplomatic vessel | **2** | 4% | docking port; Vorlon transport gets its own bay | 1–12 | days |
| **Liner (Asimov class)** | **0.5** | 1% | docking bay or port | **400–800 pax** | 4–8 h |
| EarthForce transport / personnel | **2** | 4% | docking bay | 20–200 | varies |
| EarthForce warship | **0.3** | <1% | **moored or standing off** | crew stays aboard; liberty parties by shuttle | 1–3 days |
| Alien warship / patrol | **0.2** | <1% | standing off | as above | 1–2 days |
| **Total** | **≈55** | | | | |

**The liner is the event.** Every other row is a trickle; a liner is 400–800 people through one
customs hall in a couple of hours. **Build the day around it.**

### 5.3 Passenger flow — PROPOSED (T-06)

The sourced 200,000 figure is unusable (T-X2), so this is reasoned from the manifest.

Arrivals per day from §5.2: 14 transports × ~50 pax = 700 · 12 shuttles × ~10 = 120 ·
0.5 liners × ~600 = 300 · freighter and warship crew ashore ≈ 300 · diplomatic and EarthForce
≈ 100. **≈ 1,500 people a day inbound**, and the same outbound.

Cross-check against the standing population. At 1,500 arrivals a day and a mean stay of **9 days**,
the transient population settles at **13,500 — 5.4% of 250,000**. That is a defensible figure for
a port: enough to keep the Zócalo full of strangers, not so many that the residents are a minority
in their own corridors. Longer mean stays scale it linearly (14 days → 21,000, 8.4%).

**Annualised: ~550,000 arrivals a year.** If the wiki's 200,000 is annual, we are 2.7× above it;
if it is daily, it is 133× above us. **We are much closer to the annual reading**, which is a
third reason to treat "daily" as a summary artefact.

### 5.4 Peaks — the shape of the day

**The station runs on Earth Mean Time (authority 1, customs board).** So the peaks are EMT peaks,
and they are what make the port feel alive rather than uniform.

| EMT | traffic | customs load | character |
|---|---|---|---|
| 00:00–05:00 | ~1 movement/25 min | trickle | freight window — cargo turns round while the concourse sleeps |
| 05:00–08:00 | rising | first shift | dock crews change; `station/npc/schedule.py` already has rotating shifts |
| 08:00–12:00 | **peak, ~1 per 8 min** | **heavy** | scheduled passenger arrivals; the liner berths here if it berths at all |
| 12:00–17:00 | steady | moderate | mixed |
| 17:00–21:00 | **second peak** | **heavy, outbound** | departures; the Zócalo is busiest at station-evening and the port empties into it |
| 21:00–24:00 | falling | light | |

**Peak-to-trough is about 3:1.** Deliberately not more: the gate runs continuously and freight has
no reason to prefer daylight, which is itself a nice alien-ness — a port that never closes, laid
over a human working day.

**A liner arrival is a separate axis.** The background is **~1 person a minute across both halls**
(1,500/day), i.e. about **0.5 a minute per hall**. A liner puts **600 passengers through one hall
in 90 minutes — 6.7 a minute**, which is **13× the per-hall background.** The customs hall must
therefore be built to look **absurdly over-scaled most of the time and barely adequate twice a
week.** That contrast is the design, not a compromise, and it is the same "crowdedness and
isolation" axis the owner named.

---

## 6. CUSTOMS AND IMMIGRATION

### 6.1 Where, and who

| | | Auth | Source |
|---|---|---|---|
| **Two customs halls**, north and south | the Contract 5 lateral convention | 3 | Security Manual sectional schematic |
| **Adjacent to the main docking bays**, in Blue Sector | first stop for every visitor | 4 | https://babylon5.fandom.com/wiki/Blue_Sector |
| **Signed "Customs Sector"** — an area label used *alongside* the six colour sectors | wayfinding carries both naming systems | 1 | `reference/01-station-exterior/welcome to babylon 5.webp`; `00-MASTER.md` §1.4 |
| Numbered **customs areas** within the halls | *"…disembark through customs area 7"* | 4 | "TKO"; see T-X1 |
| **Run by EarthForce station security**, Chief **Michael Garibaldi** in S2–3 | **era-critical** | 4 | https://babylon5.fandom.com/wiki/Michael_Garibaldi |
| **Zack Allan is a sergeant** in this era, not the chief | he takes over in **S5** — out of era | 4 | https://babylon5.fandom.com/wiki/Zack_Allan |
| **Lou Welch** — security officer, in era | a named face for the checkpoint | 4 | https://babylon5.fandom.com/wiki/Lou_Welch |

### 6.2 What the hall says — authority 1, verbatim

From `reference/01-station-exterior/welcome to babylon 5.webp` and
`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg`, as
extracted in `reference/00-INDEX.md`. **This is the highest-authority material in the document and
it should be reproduced letter-exact in the geometry.**

- *"Welcome to Babylon 5 · [CUSTOMS SECTOR] · **ATMOSPHERE CAUTION** — SIX DIFFERENT ATMOSPHERES
  ARE CURRENTLY AVAILABLE ON B-5"*, with uncommon atmospheres synthesised for encounter suits and
  *"FOR SPECIFIC ATMOCHEMICAL BREAKDOWNS SEE MONITOR BELOW"*
- *"Welcome to Babylon 5 · [CUSTOMS SECTOR] · FOLLOW ALL CUSTOMS PROCEDURES. SEE MONITORS FOR
  DETAILS"*, and *"TIME ON B-5 IS EARTH MEAN TIME (EMT). MONETARY EXCHANGE RATES THROUGH BUSINESS
  CENTER"*
- The **"WELCOME TO BABYLON 5"** sign: *"WELCOME TO"* in pale cream letterspaced serif capitals;
  *"BABYLON 5"* in white serif capitals on a solid royal-blue bar; a thin olive rule; then
  **`REMEMBER` / `Smoking permitted in` / `designated areas only`** in bold yellow sans.
- **Two ceiling-suspended boards canted down toward the concourse**, carrying amber-and-green text
  in a multi-column tabular grid — **the arrivals and departures boards.** These are the port's
  information layer and they should be **live**, driven by the traffic model.

Three things follow that are process, not decoration. **Currency exchange is off-site** — customs
sends you to the Business Center in Red, so a new arrival's second destination is fixed by canon.
**The atmosphere system is administrative** — "six standing, others by prior arrangement" means an
unusual species must have *pre-notified*, which is a customs record. And **the boards themselves
tell visitors to consult monitors**, so monitors are a signed, canonical part of the station's own
wayfinding rather than set dressing.

### 6.3 The process a visitor goes through — PROPOSED (T-07)

Sequence authority 5; every *check* in it is sourced.

| # | Station | What happens | Sourced? |
|---|---|---|---|
| 1 | **Disembark** | ramp from the parking level to the bay concourse; the announcement has already named the hall and area (D-11) | 4 |
| 2 | **Queue** | routed by ship, not by species; the boards show hall and area | 5 |
| 3 | **Identicard presented** | inserted into a handheld or desk reader | 1 (the prop) |
| 4 | **Genetic match** | the card is matched to the bearer's genetic code — this is what makes it forgery-proof | 4 |
| 5 | **Record pulled** | the nine-field record of §6.4 appears on the officer's screen | 1 |
| 6 | **Visa checked** | `VISAS` is a first-class field on the record | 1 |
| 7 | **Atmosphere declared** | `DES/ATMOS` — humans are `HUMAN/02`; anything outside the six standing atmospheres needs prior arrangement | 1 |
| 8 | **Telepath status** | `LICENSED PSI` is a first-class field. An unregistered telepath is a Psi Corps matter, and Psi Corps is present in era | 1 (the field) |
| 9 | **Scan** | person and baggage scanned for concealed weapons, restricted substances such as **Dust**, "or anything suspicious" | 4 |
| 10 | **Admit / refer / refuse** | three outcomes: through to the arrival concourse; secondary inspection; or refused and held | 5 |

**Working model for the hall (T-07):** each of the two halls is a **wide shallow room facing the
bay concourse**, with a bank of **three or four numbered processing areas** across it — giving the
seven of T-X1 across the pair — plus a **secondary inspection room** off to one side and a
**detention holding area** behind that. The arrival concourse (authority 1: the welcome sign, the
wall monitor with a talking head, the green vector station schematic, the two boards, the crowd)
is **beyond** the barrier and is the player's first room.

**A refusal must go somewhere, and it currently has nowhere to go.** `LOCATIONS.md` P-04 proposes
the brig in Red beside Security Central. That is a long walk from Blue. **This document proposes a
customs holding area *in* the hall** — a refusal is not an arrest, it is a wait for the next ship
out, and it wants a bench and a locked door, not a cell across the station.

### 6.4 The identicard — authority 1, and it is the customs mechanic

**Record schema** (`reference/11-props-and-technology/identicard readout.webp`, auth 1,
`00-MASTER.md` §1.4). Every field is something a customs officer checks:

`NAME` (SURNAME, FORENAME) · `ORIGIN` · `DES/ATMOS` · `SEX` · `DOB` · `PHYS CHR` · `MEDICAL` ·
`LICENSED PSI` · `VISAS`

The record panel is set in a **Eurostile/Microgramma squared-oval grotesque**, labels bold and
values regular, on a **measurable grid: 17 px horizontal by ~15–16 px vertical pitch on the
800×600 capture, ~19 columns by ~37 rows** — enough to author the UI on the module rather than by
eye. The three red rows (`PHYS CHR`, `LICENSED PSI`, `VISAS`) are set in a **lighter stroke** than
the black labels, so they read as header or inactive rows.

**The card** (auth 1): an array of **round hemispherical beads in staggered hex-packed rows**,
iridescent blue-green-violet, ~8–9 across by 9–10 rows, in a **maroon inner border** inside a
**gold/brass outer frame**.

**The reader** (auth 1): matte mid-grey plastic, top-left corner chamfered at 45°; a narrow
vertical **card throat**; a portrait screen showing **salmon-pink ground with dark red two-column
text**; and **one tall red-orange backlit window containing exactly two black icon glyphs** —
blocky abstract ideograms, not Latin letters — with a separate pale grey-white rounded-square
button below left.

**Function, authority 4** (https://babylon5.fandom.com/wiki/Identicard): the identicard is
simultaneously **driver's licence, credit card, passport and medical file**, on a crystalline
memory module holding medical information, account balances and immigration status.

**Why that combination is a gift to this project.** One prop is the interaction verb for customs,
for buying a drink in the Zócalo, for opening a quarters door and for Medlab. It gives the NPC
population one record format — the same nine fields `station/npc/` already models — and it makes
*losing* it a complete character arc. **It should be built once, at the highest quality in the
project, and reused everywhere.**

### 6.5 What is checked, and what is contraband

| category | detail | Auth | Source |
|---|---|---|---|
| **Identicard, visas, travel papers** | all three named; approval required before passage | 4 | https://babylon5.fandom.com/wiki/Blue_Sector |
| **Concealed weapons** | named explicitly as a scan target. The station's own sidearm is the **PPG** — we hold both the EarthForce issue Auricon with removable sight and a civilian pattern | 4 (the check) / 1 (the props) | same; `reference/11-props-and-technology/` |
| **Dust** | named explicitly as a restricted substance. A drug giving temporary telepathy; the S3 episode "Dust to Dust" is built on its supply chain, and **Bester and Garibaldi tracking a Dust supplier is in-era plot** | 4 | https://babylon5.fandom.com/wiki/Dust_to_Dust |
| **"Anything suspicious"** on person or in luggage | the catch-all, and it is the discretionary power that makes customs a *character* | 4 | https://babylon5.fandom.com/wiki/Blue_Sector |
| **Atmosphere declaration** | outside the six standing atmospheres, prior arrangement required | 1 | customs board |
| **Telepath registration** | `LICENSED PSI` on the record | 1 | identicard readout |
| **Medical** | `MEDICAL` on the record; quarantine authority is implied and never stated | 1 (field) / 5 (quarantine) | — |
| **Outbound manifests** | not sourced. **PROPOSED (T-10)** — a port that checks nothing on the way out cannot have a black market worth running | 5 | — |

**Proposed contraband schedule (T-08), authority 5**, extrapolated in the style of the two sourced
items and constrained by what is dramatically live in S2–3: Dust and other telepath-affecting
compounds · unlicensed weapons above personal-defence PPG class · military-grade weapons for the
Narn–Centauri war (the defining smuggling pressure of the era) · unregistered telepaths ·
forged or cloned identicards · restricted technology · undeclared biologicals · goods evading the
station's own duties. **Each wants a detection probability, a penalty and a Downbelow fence**, and
that trio is what turns customs from a gate into a system.

### 6.6 Immigration, and the failure loop that produced Downbelow

This is the most important paragraph in the document for the brief's *"slums"* requirement,
because it explains **where Downbelow's population comes from** and makes it a live process rather
than a set.

Authority 4, https://babylon5.fandom.com/wiki/Lurker and /Downbelow: B5 was the first Babylon
station open to public residency, and **people came in numbers looking for a better life.** Many
did not find it, ran out of money, and **could not afford a ticket home.** They squatted in the
parts of the station that budget cuts and a rushed completion had left unfinished — corridors and
chambers around the **waste recycling system, the air compressors and the water reclamation
facility**, especially in Brown and Grey.

For the simulation this is a **flow with a leak**:

```
gate → customs → admitted → seeking work
                                 ├── succeeds → resident, quarters, job, schedule
                                 └── fails → cannot afford passage out → Downbelow
```

**Every day a small number of arrivals never leave.** If 1% of ~1,500 daily arrivals falls out of
the bottom, that is **15 people a day, ~5,500 a year**, which is the right order for a Downbelow
population inside a 250,000-person station. The number is authority 5 and belongs in
`canon/INVENTIONS.md` if built — but the *mechanism* is authority 4 and it is what makes the
underclass legible rather than decorative. **Downbelow is not where poor people live; it is where
the port's failures accumulate.**

---

## 7. CARGO

### 7.1 The infrastructure

| # | Item | Auth | Source |
|---|---|---|---|
| C-1 | **42 cargo bays** — 28 in the rotating section, 14 in the support structure. Internal volumes | 4 | `00-MASTER.md` §1.3 |
| C-2 | **6 external cargo modules** on a continuous raised dorsal rail with plinths between them. **Distinct from the 42** — a station with 42 bays and 6 modules attached is not full | 2 | `station/schema/station.yaml`; session 2t |
| C-3 | **Spinal cargo facility** — zero-g cargo transfer, holding "the bulk of the station's supplies", running the non-rotating spine | 4 | https://babylon5.fandom.com/wiki/Babylon_5 |
| C-4 | **Raw material storage bays (5)** on the exterior systems list | 3 | `00-MASTER.md` §2 item 11 |
| C-5 | **Hazardous liquid holding tank**, **inert gases holding tanks (4)** | 3 | `00-MASTER.md` §2 items 14–15 |
| C-6 | **Guild dockworkers: 1,500** | 4 | https://babylon5.fandom.com/wiki/Babylon_5 |
| C-7 | **A dockers' union**, led in S1 by **Neeoma Connally**; struck over **worn equipment and overworked crews** after a fatal bay accident; Earth Central's budget funded weapons but not staff or equipment | 4 | https://babylon5.fandom.com/wiki/By_Any_Means_Necessary |

**C-7 is era-adjacent (S1) and it should still shape S2–3 ambience.** The strike was settled by
reallocating military money, so by our era the equipment is *newer* and the grievance is
*remembered*. Dock crews that are visibly a **union with a history** — and not interchangeable
crowd agents — is a cheap, specific, sourced piece of characterisation for the busiest working
space on the station.

### 7.2 What the station imports

| what | why | Auth |
|---|---|---|
| **Food that cannot be grown or is impractical to grow** | the Garden covers staples; other foods are imported and some are synthesised | 4, https://www.oocities.org/davesb5page/xplor.htm |
| **Alien foodstuffs** | some alien food is grown on station, but a 42%-alien population across many species cannot be fed from one biosphere | 4 (grown on station) / 5 (the volume) |
| **Manufactured goods, spares, machinery** | the station fabricates (Grey has fabrication furnaces and machine shops, `other map.png`) but does not make its own ships or reactors | 3 (the facilities) / 5 (the import) |
| **Fuel** | `spacecraft_fuel_storage` sits inside the docking sphere; **fuel stores** are named in the Blue rosette | 3 |
| **Consumer goods for the Zócalo** | the market is the station's commercial core | 3 (the Zócalo) / 5 |
| **Raw materials** | 5 raw material storage bays exist as a hull system | 3 (the bays) / 5 (the traffic) |
| **Medical supplies** | Medlab One is in Blue | 3 (the facility) / 5 |

### 7.3 What the station exports

**Nothing produced. This is the finding, and it is worth stating plainly.**

No source consulted names a Babylon 5 export. What the sources describe instead is a station that
**generates almost all its own revenue** and covers operating expenses from it, with a substantial
part coming from **rent — paid by individuals for quarters and by businesses for commercial space**
(authority 4, https://babylon5.fandom.com/wiki/Babylon_5). And the gate is described as the
**junction of hyperspace routes between the Earth Alliance, the Narn Regime and several
non-aligned worlds** (JG-11), with the station **managing the gate traffic**.

So B5's export is **passage, brokerage and neutral ground.** For the cargo simulation that means
the dominant flow is **transshipment**: cargo arrives on one hull, sits in a bay, and leaves on
another. Outbound tonnage ≈ inbound tonnage minus what the station consumes, and the visible
activity is **transfer**, not loading. That is a different animation, a different dock-crew
behaviour and a different bay dressing from a port that ships things out.

**Genuinely exported (authority 5, small volumes):** repaired and refitted hardware from Grey's
maintenance facilities; recycled and reclaimed materials; and outbound mail through the Post
Office named in the Blue rosette.

### 7.4 How much — DERIVED and PROPOSED (T-09)

Sourced tonnages do not exist. Reasoned from population and manifest:

- 250,000 people at a conservative **8 kg/person/day** of all consumables (food, packaging,
  supplies, spares) is **2,000 t/day**.
- The Garden covers oxygen and staple food. **T-X3 matters here:** the fan figure of 12 sq mi is
  6.49× the drum's actual 4.79 km², so the Garden's real capacity is far below the fan
  description and **the import fraction must be higher than a reader of that source would assume.**
  Taking the Garden as covering **half** of food by mass leaves **~1,200 t/day** to import.
- Across 20 bay-class freighters a day that is **~60 t each**, which is a small ship — consistent
  with a 60 m Centauri Brezebel-class hull (S-5) and with a port of frequent small movements
  rather than rare bulk carriers.
- **Transshipment on top**, not consumed by the station: propose **2–3× the consumed tonnage**,
  because JG-11 makes the station a route junction rather than a destination. Total throughput
  **~4,000–5,000 t/day**.

Every number in that chain is authority 5. It is reported because **a cargo system with no
tonnage cannot be tuned**, and a stated-and-overturnable figure is worth more than a gap.

---

## 8. THE PORT AS A LIVING SYSTEM — what to actually simulate

Consolidated from the above. Authority as marked per row elsewhere.

| system | the rule | cadence |
|---|---|---|
| **Gate** | one transit at a time, ~110 s spacing (T-02) | ~110 movements a day through one aperture = **3.4 h of gate time in 24, a 14% duty cycle** — so the gate is never the constraint, which is why the *station* can be |
| **Inbound corridor** | 65 km (T-01), 4–7 min under power | 1 hull inbound at any moment on average |
| **Traffic control** | C&C hails by name and type, assigns bay and vector, takes control (D-1…D-5) | continuous radio texture in Blue |
| **Roll match** | **1.7926 rpm, one turn per 33.4716 s** (D-6) | the signature visual of an arrival |
| **Axial entry** | dead centre, zero tangential velocity (D-7; `axial_approach_is_trivial`) | ~60 s |
| **Bay elevators** | **2 for 24 bays**, ~90 s each way, ~5 min full cycle (D-8, T-04) | **24 movements/hour capacity, 62% used at peak — the bottleneck, and where the queue lives** |
| **Berthing** | landing pad, then down to the parking level (D-9) | |
| **Announcement** | ship name, bay number, customs area (D-11) | every arrival; the station's voice |
| **Customs** | 2 halls, ~7 numbered areas, 10-step process (§6.3) | ~1,500 people/day; **7/min during a liner** |
| **Immigration failure** | ~1% of arrivals never leave → Downbelow (§6.6) | ~15/day |
| **Cargo** | ~4,000–5,000 t/day, mostly transshipped (§7.4) | 1,500 guild dockworkers on rotating shifts |
| **Cobra bays** | 24 fighters in 28 bays; **the only berths needing real spin-matched guidance** | patrols, alerts, escorts |
| **Failure modes** | §9 | rare, and they are the stories |

---

## 9. FAILURE MODES — sourced, and better than invented ones

The show hands us a docking accident with a full causal chain, and it is more useful than anything
we could design.

**The S1 accident** (authority 4, https://babylon5.fandom.com/wiki/By_Any_Means_Necessary): a
**computer glitch** cleared a departing ship at the same time as an arriving **Narn cargo vessel**;
they collided; a **dock worker was killed** in the explosion and fire. Root cause: **substandard
microchips from a subcontractor** produced the mistaken clearance. Contributing: **overworked crews
and worn equipment**, per the union.

Four things a simulation can take straight from that:

1. **Clearance conflicts are the canonical accident.** Two hulls cleared into the same volume. That
   is a state-machine bug in-fiction, which means it can be a *deliberate, tunable* rare event.
2. **The dock is dangerous and people die there.** Bay-side safety is real. The yellow/black hazard
   chevrons on **every step nosing** (authority 1, `Minbari Flyer 969…`) are applied by rule for a
   reason.
3. **Understaffing is a systemic input**, not colour. Crew fatigue raises accident probability;
   budget determines crew.
4. **The consequence is industrial, not military.** A strike — "blue flu" — cripples the port
   without a shot fired. **A port that can stop is a port that is alive.**

Other events worth carrying, all authority 5 but constrained by the above: a hold stack when the
elevators back up · a contraband find in a scanned container · a refused entry waiting in the hall
for the next outbound hull · a diplomatic vessel demanding priority berthing · a warship arriving
unannounced · a ship arriving with a medical case and triggering quarantine · a gate transit
aborted with a hull half through.

---

## 10. PROPOSED — the reasoning

**Every one of these is authority 5.** If built, each goes in `canon/INVENTIONS.md` with what
would overturn it. None may be recorded as canon.

**T-01 — The gate sits 65 km forward of the station, ~15° off the long axis.**
Constrained from four directions. It must be far enough to identify and intercept a hostile
arrival (JG-12) — at 65 km a hostile under hard burn needs minutes, which is an interception
window. It must be near enough that transit is "fast and smooth" (JG-12) — 4–7 min for a
transport, 2.7 min for a Starfury at its measured 18.38 m/s². It must be **8× the station's own
length**, so the gate reads as a separate structure and not as an appendage. And it must lie inside
the precision envelope the project already chose: `floating_origin.py` measures float32 at 50 km as
**3.91 mm**, which is why double precision was adopted, and 65 km is on the right side of that
decision rather than beyond it. The 15° offset keeps the gate out from behind the forward deflector
spike so C&C can see arrivals through its window, which authority 4 says is what that window is
for. *Overturned by:* any stated distance, or any frame showing the gate and the station together
at a legible relative scale.

**T-02 — Jump point: 500 m aperture, 20 s nominal, ~110 s between transits; the gate is four
struts on a 3.5 km circle.**
The aperture must pass the largest hull that uses the gate. A Sharlin is 1,600 m long but ~1,900 m
*tall* (S-18), which would demand a 2 km aperture — so either capital ships do not use this gate,
or they open their own points (JG-5 says large ships often do). **500 m is sized for the traffic B5
actually sees**: liners, transports and freighters, all comfortably under 400 m. The 20 s duration
follows from JG-7 — the gate holds the point until transit completes — plus the observation that
JG-8's ship-formed points are opened and cleared as fast as possible, so a gate point should not
loiter either. The 110 s spacing is the exit volume clearing at a walking-pace closing speed. The
four struts and the 3.5 km circle are the **only part of the gate with a sourced dimension**
(JG-3: 3.2 km × 180 m × 60 m each); everything else is arrangement. *Overturned by:* any frame
showing a gate with a ship for scale, or dialogue timing a transit.

**T-03 — Bay envelope 110 m × 40 m × 18 m clear; practical ship limit ~100 m.**
Four constraints, and they converge. **The deck disc measures 9–11 m** across (authority 1,
measured against eleven dock workers) and reads as a bay-centre marker, so the bay is a small
multiple of it, not a large one. **The Minbari flyer spans most of the bay width** (authority 1),
and a flyer is a shuttle-class hull. **The bay ceiling is the ribbed inner wall of the rotating
drum** (authority 1), so the bay is cut into the hull and its depth is bounded by the ring stack —
and at the docking sphere the hull radius is only **189–260 m** (§4.6), of which the pressurised
ring stack must have most. **Large transports are too long for the bay elevators** (authority 4),
which puts a hard ceiling on what the elevator can carry. 110 m long accommodates the 50 m EA
standard shuttle and the 60 m Brezebel with room to manoeuvre, and excludes anything approaching
a warship. *Overturned by:* any bay frame with a full ship and a person in it, or any stated bay
dimension.

**T-04 — The bay elevator cycle is ~90 s each way (~5 min full cycle), and it is the port's
bottleneck.**
The elevator carries a craft from the axial mouth out to a bay. In the docking sphere that is a
radial run of roughly 190–260 m (§4.6). The core-shuttle work already measured the constraint on
radial motion in a rotating frame: Coriolis is 2ωv, so a fast radial run throws its load sideways —
**8 s rim-to-axis is 2.00 g; 120 s is 0.13 g** (`00-MASTER.md` §1.2). A bay elevator's run is a
fraction of the rim-to-axis distance but carries an unrestrained *spacecraft* on a cradle, so it
wants the same gentleness. 90 s over ~230 m is a mean 2.6 m/s, which is a slow industrial lift.
A full cycle is 90 s out + 90 s back + ~120 s of loading and securing = **5 min**, so one elevator
does **12 movements/hour** and the pair does **24**, against ~110 movements a day peaking at ~15 an
hour. *Overturned by:* any frame timing an elevator, or a third elevator appearing in a source.

**T-05 / T-06 — The daily manifest and the passenger flow.** Reasoning is in §5.2 and §5.3 rather
than repeated here. The load-bearing choices: 55 movements a day comes from an authority-4 figure
that **independently cross-checks against an authority-3 berth count** at a 10-hour turnaround; the
95/5 civilian split is sourced; the mix within the 95% is ours, tuned so that **a liner is rare
enough to be an event and freight is common enough to be the background**. *Overturned by:* the
200,000 figure resolving to a real period (T-X2), or any manifest in a licensed source.

**T-07 — Two customs halls, three or four numbered processing areas each, plus secondary
inspection and a holding area.** Reconciles authority 3's count of two halls with authority 4's
"customs area 7" (T-X1). A refusal needs somewhere to wait that is **not** a cell across the
station in Red — a refused passenger is not a prisoner, they are someone waiting for the next ship
out. *Overturned by:* a frame showing a customs area numbered above 8, or a third hall on an
uncropped Security Manual sheet.

**T-08 — The contraband schedule.** Two items are sourced — **weapons** and **Dust** — plus an
explicit discretionary catch-all. Everything else in §6.5 is extrapolated *in the style of those
two* and constrained to what is dramatically live in S2–3, above all the **Narn–Centauri war**,
which is the era's engine and makes military-grade weapons the smuggling pressure that matters.
*Overturned by:* any list of prohibited goods in a licensed source.

**T-09 — ~4,000–5,000 t/day throughput, of which ~1,200 t/day is consumed.** Chain of reasoning in
§7.4. The weak link is the 8 kg/person/day figure, which is a terrestrial logistics rule of thumb
and not sourced to anything; it is stated so it can be argued with. The strong part is the
*structure* — most tonnage is **transshipped, not consumed**, because JG-11 makes the station a
route junction. *Overturned by:* any stated cargo figure; more usefully, by resolving T-X3, since
the Garden's real capacity sets the import fraction directly.

**T-10 — Departure is not arrival reversed.** Three asymmetries, given in §4.5: clearance is a
customs act as well as a traffic act; the station returns the hull's spin for free (35.5–48.7 m/s
at the docking sphere, §4.6); and the queue forms at the gate rather than at the bay. *Overturned
by:* any departure dialogue.

**T-11 — Tugs, lighters and bay tenders exist and are station-owned.**
**Nothing in canon, in the reference set, or in any web source consulted describes one.** They are
proposed because the station cannot function without them: 42 cargo bays, a zero-g spinal transfer
facility, **six external cargo modules that must be exchanged**, and moored capital ships that
never touch the hull all require powered movement of unpowered mass. Propose three types — a
**bay tender** (small, in-bay, arms and grapples), a **lighter** (30–50 m, pressurised, ferries
crew and cargo between moored ships and the station), and a **module tug** (heavy, handles the
dorsal cargo modules). All in station livery, all under C&C control, none jump-capable.
*Overturned by:* any frame showing a B5 service craft — which would also be very welcome.

**T-12 — Failure events are tunable and rare.** §9. The point is that the canonical accident has a
canonical **root cause** — a bad part from a subcontractor — so the failure model can be built as
component reliability rather than as scripted drama.

---

## 11. UNPLACED, AND UNKNOWN

### 11.1 Things the show establishes but never places

| item | what is missing |
|---|---|
| **The jump gate itself** | exists (JG-1), never dimensioned relative to the station, never shown in our reference set |
| **The hyperspace beacon network** | named (JG-9); no beacon is ever placed, drawn or described physically |
| **"Beacon Alpha 5"** | a named beacon a ship locks on to (JG-14); we do not know whether it is on the station, on the gate, or free-floating |
| **"Approach vector 557"** | vectors are numbered in the hundreds (D-4); the numbering scheme is unknown |
| **"Docking Bay 12B"** | bays carry letter suffixes (D-2); we do not know whether 24 bays means 24 numbers or 12 pairs. **12 × {A,B} = 24 is arithmetically exact and would reconcile the Security Manual count with the observed suffix** — recorded as an observation, not a ruling |
| **Customs area numbering** | at least 7 (T-X1); the total is unknown |
| **The low-g / zero-g bays** | existence is authority 3, the count of four is authority 4, and the sources disagree on whether they are Blue or Yellow (`LOCATIONS.md` §4) |
| **The parking level** | named in dialogue (D-9); never shown |
| **Tugs and service craft** | never mentioned anywhere (T-11) |
| **Where a refused arrival waits** | the outcome exists; the room does not |
| **Where cargo actually goes** after the bay | 42 bays and a spinal facility are named; the route between them is not |
| **The arrivals/departures boards' content** | the fixture is authority 1; nothing legible was ever shown on one |

### 11.2 Things this document could not determine

- **Gate-to-station distance.** No source found states it. T-01 proposes.
- **Whether the 200,000 traffic figure is daily or annual.** T-X2. One page read directly would
  settle it, and it is the single cheapest open question here.
- **Bay dimensions.** Never stated; T-03 derives them from an authority-1 deck marking and a
  ceiling constraint.
- **Passenger numbers per ship class.** No source gives a liner's capacity.
- **Cargo tonnage.** No source gives any figure.
- **Whether customs is EarthForce security or a separate civil service.** Sources put it under
  station security, which in S2–3 is Garibaldi; nothing found describes a distinct customs branch
  with its own uniform. **If it has one, that is a whole NPC costume we would be missing.**
- **Departure procedure.** Entirely unsourced.
- **What the station charges.** Rent is sourced as the revenue base; docking fees, duties and
  landing charges are not mentioned anywhere, which is odd for a port and may simply be a gap in
  what was searchable.

---

## 12. WHAT TO BUILD NEXT, RANKED

Ranked by value per unit of risk — how much of the owner's *"transports and visitors constantly
arriving, the jump gate working, customs"* each unlocks, against how much of it could be
invalidated later.

1. **The arriving hull rolling on the axis.** The highest-value, lowest-risk thing in this
   document. It is **sourced** (D-6, D-7), it is **already supported by built physics**
   (`axial_approach_is_trivial`, and `test_docking.py` asserts an axial port's velocity is zero to
   1e-12), it needs **no new geometry** beyond one transport hull, and it is the image that says
   *"this station spins"* better than anything else in the project. **1.7926 rpm, one turn per
   33.4716 s.**
2. **The traffic model as a clock.** 55 arrivals and 55 departures a day, one movement every
   13 minutes, with the §5.4 peaks on Earth Mean Time. Pure data, no art, and it is what makes
   every window and every announcement in the station stop being static.
3. **Customs, end to end.** `LOCATIONS.md` already ranks the hall second overall to build; this
   document supplies the **process** to put in it — ten steps, nine identicard fields, three
   outcomes. The signage is authority 1 and verbatim. Together they are the player's first ten
   minutes.
4. **The identicard and its reader.** One prop, authority 1 down to the bead count and the type
   grid, that is the interaction verb for customs, commerce, quarters and Medlab. **Build it once
   at the highest quality in the project.**
5. **The bay elevator.** It is the bottleneck (T-04), it is authority 3, it is the only piece of
   the docking chain that is a *machine the player rides or watches*, and it converts an
   abstract queue into a physical one.
6. **The jump gate.** Enormous value — the brief names it explicitly — and the **highest reference
   risk in this document**, because we hold no frame of one. Build it to JG-3's strut dimensions,
   which are the only sourced numbers, and treat everything else as replaceable. **Ask for
   reference first** (§11).
7. **The immigration failure loop.** §6.6. Cheap — it is a probability and a destination — and it
   is what makes Downbelow a consequence of the port rather than a themed corridor.
8. **Cargo transshipment.** The dock-crew behaviour, the 1,500 guild dockworkers, the union with a
   history. Lowest visual return per unit of work, highest return for *inhabitedness*.

**Three decisions worth making before any of it is dressed:**

- **Fix the berth-radius figures (T-X5) before a launch or dock animation is tuned.** 52.2 m/s is
  the *drum floor*; the docking structure is 35.5–48.7 m/s. Cheap now, and it silently corrupts
  every timing that is built on it later.
- **Decide bay numbering now.** 24 bays as `1–24` or as `1A–12B` changes every sign, every
  announcement and every dialogue line in the port. The evidence for the second is one line of
  dialogue and one exact arithmetic coincidence — thin, but it is what there is.
- **Re-read two web pages the moment egress allows it**: the Babylon 5 wiki's traffic paragraph
  (T-X2) and the station-exploration page's Garden figures (T-X3). Both are load-bearing, both are
  currently known only through a summary, and one of them is provably wrong as summarised.
