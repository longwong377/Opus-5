# Babylon 5 — Master Canon Reference

Every number in this project traces back to this file. Nothing gets built from memory.

**Era lock: Season 2–3.** Sheridan in command, defence grid installed, Kosh present,
all League ambassadors resident, Zócalo at full operation, pre-secession, pre-war-damage.

**Authority levels** (from `reference/README.md`): 1 = on-screen footage · 2 = production
material · 3 = licensed print · 4 = fan reconstruction · 5 = our own extrapolation.

---

## 1. Station Master Dimensions

| Property | Value | Authority | Source |
|---|---|---|---|
| Overall length | **8,047 m** (5 miles) | 1 | S1 opening narration, "a self-contained world five miles long"; corroborated by `other map 2.jpg` ("5 miles (8.047 km)") and the Contract 5 scale bar (0–8 km) |
| Total mass | **2,500,000 tons** | 1 | S2 opening narration, "two million five hundred thousand tons of spinning metal" |
| Typical population | **250,000** | 1 | S1 opening narration, "a quarter of a million humans and aliens" |
| EarthForce crew | 6,500 | 4 | `other map 2.jpg` |
| Location | Mid-orbit, Epsilon Eridani III, Euphrates Sector | 1 | Show; corroborated `other map 2.jpg` |
| Constructed | 2254–56 | 4 | `other map 2.jpg` |
| Commissioned | Late 2256 | 4 | `other map 2.jpg` |
| Defences | Anti-fighter pulse cannons; two Starfury squadrons | 1 | Show (S2 defence grid); corroborated `other map 2.jpg` |

### 1.1 Section proportions

`other map 4.jpg` (Lawrence D. Miller, *Sheet 2: Top View*, authority 4) is the only source
giving a complete internally-consistent dimensional breakdown. **Its stated overall length of
3,108 m contradicts show canon by a factor of 2.589 and its stated mass of 246,000 tonnes
contradicts show canon by ~10×.** Show canon wins on both (see `CONFLICTS.md` §C-001).

Miller's *proportions* are retained and rescaled by **k = 8047 / 3108 = 2.5891**:

| Section | Miller (m) | **Rescaled (m)** | Notes |
|---|---|---|---|
| Blue Section diameter | 201 | **520.4** | Forward, rotating; docking sphere, C&C, crew quarters |
| Blue Section length | 356 | **921.7** | |
| Red Section diameter | 253 | **654.9** | Widest pressurised section |
| Red Section length | 172 | **445.3** | |
| Green Section outer diameter | 230 | **595.5** | |
| Green Section outer length | 1058 | **2739.3** | |
| Bio-Habitat interior diameter | 215 | **556.6** | The habitable drum interior |
| Bio-Habitat interior length | 1058 | **2739.3** | |
| Bio-Habitat interior radius | 107.5 | **278.3** | Derived |
| Bio-Habitat inner surface area | 714,256 m² | **4,787,500 m²** | Scales as k² = 6.7035 |
| Communications grid span | 819 | **2120.5** | |
| Width at communications grid | 345 | **893.2** | |

Cross-check: π × 556.6 × 2739.3 = 4,789,000 m². Consistent with the scaled surface area. ✔

### 1.2 Spin gravity — derived

At bio-habitat interior radius **r = 278.3 m**, for centripetal acceleration a = ω²r:

| Target | ω (rad/s) | Period | RPM |
|---|---|---|---|
| 1.00 g | **0.187717056** | **33.471574 s** | **1.792566** |
| 0.50 g | 0.132736 | 47.336 s | 1.268 |
| 0.30 g | 0.102807 | 61.117 s | 0.982 |

**Working value: 1.0 g at the habitat floor, period 33.4716 s, 1.7926 rpm.**
Standard gravity is 9.80665 m/s² throughout. Constants are carried to 9 places:
rounding ω to 5 places put floor gravity at 1.000351 g and moved the half-gravity
radius by 5 cm, which is negligible physically but fails exact-relation tests for
the wrong reason.

Derived consequences, all unit-tested in `station/physics/`:

| Quantity | Value |
|---|---|
| Floor tangential speed | **52.2 m/s** — inherited by anything launched from the drum |
| Half gravity at | 139.15 m radius (exactly half the floor radius) |
| Apparent weight, brisk walk spinward | 1.054× |
| Apparent weight, brisk walk anti-spinward | 0.947× |
| Coriolis climbing toward the axis | 1.13 m/s² lateral, deflecting spinward |

The show depicts normal human gait and unremarkable gravity throughout the habitation
sections. 1.7926 rpm sits comfortably below the ~2–3 rpm threshold at which Coriolis effects
become disorienting, so this is both canon-consistent and physically sound. Rotation rate is
not stated on screen — logged as invention `INV-002`.

Gravity falls linearly with radius toward the axis: **g(r) = ω²r**, reaching zero at the core
shuttle. This gradient is a first-class simulation feature, not set dressing.

**Consequence: rim-to-axis transit is slow, and the physics says so.** Coriolis on radial
motion is 2ωv, so peak lateral load scales inversely with transit duration:

| Rim → axis in | Peak lateral |
|---|---|
| 8 s | 2.00 g |
| 60 s | 0.27 g |
| 120 s | 0.13 g |
| 300 s | 0.05 g |

Holding peak lateral under 0.12 g needs **133 seconds**. A lift from the rim to the core
shuttle is therefore a two-minute-plus ride during which weight drains away and an
unexplained sideways push builds and fades. That is a felt journey, not a loading screen.

### 1.2b Numeric precision — measured

float32 carries ~7 significant decimal digits, so representable-value spacing grows with
distance from the origin. Measured in `station/physics/`:

| Distance | float32 spacing |
|---|---|
| 8,047 m (station nose) | **0.49 mm** |
| 16,384 m | 1.00 mm |
| 20,000 m | 1.95 mm |
| 50,000 m | 3.91 mm |

**The station alone is marginally survivable in float32** — 0.49 mm at the nose is close to
invisible. What is not survivable is the flight envelope: a Starfury 50 km out puts everything
on a ~4 mm grid, which reads as shimmer on stationary geometry.

So double precision is required by the *Starfury*, not by the station. Rendering still narrows
to float32 on the GPU regardless, so a floating origin is also mandatory: rebasing world
coordinates near the viewer reduces positional error by **over two orders of magnitude**
(1.09 mm → 4.9 µm at 40 km in the measured case).

### 1.3 Counts

| Item | Value | Authority | Source |
|---|---|---|---|
| Cobra bays | 24 *or* 28 — **unresolved**, see `CONFLICTS.md` §C-002 | 4 | Miller says 24 fighter storage; Contract 5 labels "COBRA BAYS (28)" |
| Cargo bays, rotating section | 28 | 4 | `other map 4.jpg` |
| Cargo bays, support structure | 14 | 4 | `other map 4.jpg` |
| Reactor cooling fins | 12 | 3 | Contract 5, `Exterior map.jpg` |
| Coolant manifolds | 8 | 3 | Contract 5, `Exterior map.jpg` |
| Heat exchange / emergency solar collectors | 12 | 3 | `Exterior map.jpg` |
| Observation domes | 2 (Dome 1 = Command & Control) | 3 | Contract 5 |
| Observation rotundas | 4 | 3 | Contract 5 |
| Sanctuaries | 4 | 3 | Contract 5 |
| Space traffic proximity arrays | 4 | 3 | Contract 5 |
| Micro-gravity maintenance bays | 2 | 3 | Contract 5 |
| Inert gases holding tanks | 4 | 3 | Contract 5 |
| Deep space communications grids | 2 | 3 | Contract 5 |
| Ionization vane support rings | 3 | 4 | `other map 4.jpg` |
| Fusion reactor ionization vanes | 6 | 4 | `other map 4.jpg` |
| Cobra launch bay support arms | 4 | 4 | `other map 4.jpg` |
| **Docking bays (Blue Sector)** | **24** | 3 | Security Manual sectional schematic. Cross-checks against on-screen "docking bay 17" (`Minbari Flyer 969 in docking bay 17.webp`, auth 1). **Distinct from cobra bays** — see `CONFLICTS.md` C-002 |
| **Bay elevators** | **2** | 3 | Security Manual sectional schematic |

### 1.4 Station operating facts — authority 1, from on-screen signage

Added session 2q from `reference/01-station-exterior/welcome to babylon 5.webp` (customs hall
information boards) and `reference/11-props-and-technology/identicard readout.webp`.

| Fact | Value | Source |
|---|---|---|
| **Station time** | **Earth Mean Time (EMT)** | "TIME ON B-5 IS EARTH MEAN TIME (EMT)" |
| **Standing atmospheres available** | **Six**, numbered; others by prior arrangement | "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5" |
| **Human atmosphere designation** | **02** | Identicard field `DES/ATMOS: HUMAN/02` |
| Uncommon atmospheres | Synthesised for encounter suits | Customs board |
| Currency exchange | Through the **Business Center** | Customs board; matches "Business District" in the Red Sector cross-section |
| Customs area label | **"Customs Sector"** — used alongside, not instead of, the six colour sectors | Customs boards |

EMT is the clock `station/npc/schedule.py` was already implicitly using; it is now sourced
rather than assumed. The numbered-atmosphere system is what the multi-environ alien sector and
every NPC record are built on.

**Identicard record schema** (authority 1, `identicard readout.webp`) — the canonical NPC
record: `NAME` (SURNAME, FORENAME) · `ORIGIN` · `DES/ATMOS` · `SEX` · `DOB` · `PHYS CHR` ·
`MEDICAL` · `LICENSED PSI` (flag) · `VISAS`.

---

## 2. Exterior Systems, Aft → Fore

From `Exterior map.jpg` (authority 3) and the Contract 5 profile/plan views:

1. Core fuel housing (aft terminus)
2. Coolant manifold (8)
3. Primary fusion reactor / reactor housing
4. Reactor coolant purge vents
5. Fuel delivery and emergency venting system
6. Reactor cooling fins (12)
7. Explosive disconnect point to jettison reactor
8. Generator torus housing
9. Heat exchange arrays and emergency solar collectors (12)
10. Secondary power distribution conduits
11. Raw material storage bays (5)
12. Habitat cylinder — the rotating section
13. Micro-gravity maintenance bay (2)
14. Hazardous liquid holding tank
15. Inert gases holding tank (4)
16. Cargo modules and magnetic attachment points
17. Deep space communications grid (2) on support pylons
18. Tachyon transmitter
19. Space traffic proximity arrays (4)
20. Cobra bays + cobra launch bay support arms (4)
21. Observation rotundas (4)
22. Observation domes 1 & 2 — Dome 1 is Command & Control
23. Hard docking mooring clamps (retractable)
24. Primary navigation beacon
25. Forward deflector array / instrument guidance array (fore terminus)

**North / South convention:** the Contract 5 cross-section labels the station's two lateral
halves **North** and **South**, with the Primary Docking Port and Service Docking Port on
opposite sides. This is the canonical lateral naming and will be used throughout.

---

## 3. Sector Model

Six sectors: **Blue, Red, Green, Brown, Grey, Yellow.**

On-screen location references take the form `<Colour> <number>` — Grey 17, Red 3, Blue 12,
Brown 2, Green 2 — i.e. **sector + level**. Level numbering is therefore a first-class part
of the address space, which directly serves the multi-level requirement.

### 3.1 Longitudinal order — **contested; do not build from this table**

> **Session 2q: partially reversed. Read `CONFLICTS.md` C-003 UPDATE 2 before using anything
> in this section.**
>
> `C-003 UPDATE` rejected the longitudinal model outright because the station is 50%
> structural and Grey and Brown would land on bare truss spine. **That argument refutes the
> *ordering* in the table below, not longitudinal slicing itself.** Two authority-3 sheets —
> the *Security Manual* sectional schematic, and a colour sector plate assigned to the same
> publication family by shared terminology rather than by a masthead — give a different
> ordering in which the aft structural half is **Yellow** (engineering / zero-G storage),
> which is exactly what belongs there. Under that ordering the geometric objection disappears,
> and three of six band boundaries agree with our independently-derived hull framework to
> within **2, 74 and 96 m** (`CONFLICTS.md` C-003 UPDATE 2 carries the measured table; the
> remaining three are out by 23 m, 210 m and 264 m).
>
> Best current reading, aft → fore: **Yellow · Grey · {Green, Brown in an order the two
> authority-3 sources disagree on} · Red · Blue.** Yellow spans the reactor, spine and truss
> to ~3,200 m; Red is `red_section`; Blue is the forward docking structure.
>
> **C-003 stays OPEN and BLOCKING** on the Green/Brown transposition alone.

The ordering below is `other map 2.jpg` (authority 4), now outranked twice over. Note also
that read off the label positions in that render, **Yellow sits between Green and Red**, not
after Red as transcribed here. Retained for the record and for the function column, which is
uncontested:

| Order (aft → fore) | Sector | Function |
|---|---|---|
| 1 | **Grey** | Industrial zones, manufacturing, construction facilities |
| 2 | **Brown** | Residential — "Downbelow" |
| 3 | **Green** | Diplomatic zones, **The Garden** |
| 4 | **Red** | Commercial zones, residential, **The Zócalo** |
| 5 | **Yellow** | Zero-G storage |
| 6 | **Blue** | Docking sphere, crew quarters, **C&C** |

`Interior map.jpg` disagrees, showing sectors as *nested radial layers* rather than
longitudinal slices — Yellow as an outer utility skin plus the core shuttle axis, Red as the
outer ring, Green inboard. **This conflict is open** — see `CONFLICTS.md` §C-003. The
longitudinal model is adopted provisionally because hull geometry must be built first and it
is the model that constrains hull geometry.

### 3.2 Level structure

**Still blocking, but the axis is now settled.** See `CONFLICTS.md` C-004 UPDATE for the full
evidence and the caveats.

**A level is a concentric radial deck.** Three independent lines agree and none dissents:

1. The six radial cross-sections in `reference/02-station-cutaways-and-plans/other map.png`
   (authority 3) draw every pressurised sector as **concentric annular rings about a central
   core**, with named facilities in specific rings and **radial transport tubes as spokes** to
   the axis. **Downbelow is marked, by name, on an OUTER ring** — which answers the standing
   objection above rather than arguing around it.
2. The Security Manual sectional schematic (authority 3) shows the same thing in longitudinal
   section — long horizontal lines the length of each section, symmetric about the centreline —
   and one of its own callouts is "CONCENTRIC PERSONNEL TRANSFER SYSTEMS".
3. **Authority-1 footage confirms it.** `reference/03-sector-blue/Babylon_5_2-22_34b.jpg` shows
   the habitat drum's end cap as a disc of concentric annular bands, a hollow drum with a racked
   axial truss carrying the core shuttle, and a radial transport spoke. That is the Green
   cross-section of the print sheet, in live action.

Since **sectors** index the longitudinal axis (§3.1), a longitudinal reading of **level** would
index the same axis twice — not an address scheme. `<Colour> <number>` is therefore
**longitudinal sector + radial deck**.

**What is still unknown, and why this still blocks:**

- **Which end is level 1** — outermost at full gravity, or innermost. No source numbers a ring.
  Getting it backwards inverts every address and puts Downbelow at the axis in zero gravity.
- **How many levels per sector.** "Grey 17" implies at least 17; no source states a count and
  the rosettes are too coarse to count rings from.
- **Radial spacing.** Unavailable. The sectional schematic's vertical scale is exaggerated ~2×
  (drum L/D reads 1.46 against our 3.1), so **no deck spacing, ring radius or ceiling height may
  be measured from it** — the same ruling as C-005, for the same reason.

Do not build level geometry until the numbering convention is sourced. **One lift-car display
would close it, and that is now the single highest-value gap in the reference set.**

---

## 4. Reference Coverage

| Area | Files | Sufficient to build? |
|---|---|---|
| Exterior hull, whole-station | 15 | **Yes** — proportions, systems layout, and two independent schematics |
| Blue Sector (C&C, docking) | 10 | Partial — good C&C and docking-bay interiors, no plans |
| Red Sector (Zócalo, commercial) | 10 | Partial — strong interior shots, no plans |
| Green Sector (council, diplomatic) | 4 | Thin — council chambers and rotunda only |
| Grey Sector | 1 | **Insufficient** |
| Brown Sector / Downbelow | 0 filed, **1 misfiled** | **Still insufficient.** `01-station-exterior/sleeping-in-light-05.jpg` is a wide Downbelow-class corridor — the only one in the set. S5, station derelict: set architecture in era, dressing not |
| Yellow Sector | 0 | **None** |
| Garden / core / transit | 5 filed, **+4 misfiled in `03-sector-blue/`** | **Upgraded to good.** `Babylon_5_2-22_33a/34b/35a` and `29a` give the drum interior along its axis, the axial truss and core shuttle, a **core shuttle car interior**, and a garden terrace |
| Starfury | 4 | Partial — exteriors plus **signed Steve Burg '93 concept art** (auth 2, *preliminary*); still **no cockpit reference**. `starfury even more detailed.jpeg` is a fan 3D model, auth 4 — do not measure from it |
| Characters / uniforms | 17 → **12** | **Marginal.** Five were AI-generated turnarounds and are quarantined (`reference/22-QUARANTINE-ai-generated/`). What remains is screencaps plus one authority-4 fan orthographic sheet whose colours are the **S1** pattern |
| Races / makeup | 16 → **12** | **Yes** — Vorlon, Narn, pak'ma'ra covered. Four AI turnarounds quarantined |
| Props / signage / typography | 17 | **Yes** — and now includes the identicard record schema and the customs-board canon in §1.4 |
| Station cutaways and plans | 8 | **The two Security Manual sheets are the most valuable files in the set.** They carry the sector bands and the per-sector radial cross-sections |

Gaps are recorded, not filled by guesswork. Anything built into a gap goes in `INVENTIONS.md`.

**Two quarantine folders. Neither may be modelled from.**
`reference/21-QUARANTINE-animated-film/` (8 files, 2023 animated feature) and
`reference/22-QUARANTINE-ai-generated/` (9 files, AI character turnarounds). Both were the
*highest-resolution* material in their categories — the 22- folder includes a 2528×1696 PNG
that is the largest "uniform reference" in the tree and is worth nothing.
**Resolution is not authority.**
