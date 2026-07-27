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
| Coriolis climbing toward the axis | 1.13 m/s² lateral, deflecting spinward | The show depicts
normal human gait and unremarkable gravity throughout the habitation sections. 1.79 rpm sits
comfortably below the ~2–3 rpm threshold at which Coriolis effects become disorienting, so
this is both canon-consistent and physically sound. Rotation rate is not stated on screen —
logged as invention `INV-002`.

Gravity falls linearly with radius toward the axis: **g(r) = ω²r**, reaching zero at the core
shuttle. This gradient is a first-class simulation feature, not set dressing.

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

### 3.1 Working longitudinal order (provisional)

Adopted from `other map 2.jpg`, which ties sector names directly to visible hull positions and
is therefore the reading most easily reconciled with exterior geometry:

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

**Open question, blocking.** Whether a "level" is a concentric radial deck (level 1 outermost
at full gravity, numbering inward toward the axis) or a longitudinal slice is not yet
established from reference. In a spin-gravity cylinder "down" is outward, which argues for
radial decks. But *Downbelow* being described as the lower levels of Brown Sector would then
place it at the outer hull, which sits oddly with its depiction as disused interior space.

Do not build level geometry until this is resolved. See `CONFLICTS.md` §C-004.

---

## 4. Reference Coverage

| Area | Files | Sufficient to build? |
|---|---|---|
| Exterior hull, whole-station | 15 | **Yes** — proportions, systems layout, and two independent schematics |
| Blue Sector (C&C, docking) | 10 | Partial — good C&C and docking-bay interiors, no plans |
| Red Sector (Zócalo, commercial) | 10 | Partial — strong interior shots, no plans |
| Green Sector (council, diplomatic) | 4 | Thin — council chambers and rotunda only |
| Grey Sector | 1 | **Insufficient** |
| Brown Sector / Downbelow | 0 | **None** |
| Yellow Sector | 0 | **None** |
| Garden / core / transit | 5 | Partial — good garden views, one lift interior |
| Starfury | 4 | Partial — exteriors only, **no cockpit reference** |
| Characters / uniforms | 17 | **Yes** |
| Races / makeup | 16 | **Yes** — Vorlon, Narn, pak'ma'ra well covered |
| Props / signage / typography | 17 | **Yes** |

Gaps are recorded, not filled by guesswork. Anything built into a gap goes in `INVENTIONS.md`.
