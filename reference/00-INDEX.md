# Reference Index

Maintained by Claude. Every reference file that lands in this tree gets catalogued here with
what was extracted from it and what it authorises us to build.

**Status:** 100 image files in the tree — **83 live, 17 quarantined** across two folders
(`21-QUARANTINE-animated-film`, `22-QUARANTINE-ai-generated`), neither of which may be
modelled from. **48 entries below** (one is the format example; several cover confirmed
duplicates). The uncatalogued remainder is listed at the foot of this file under
*Still uncatalogued*, so the next session knows exactly what is left and does not have to
re-derive the gap.

---

## Format

Each entry, once populated, looks like this:

```
### 02-station-cutaways-and-plans/plan_bluesector_deck7.jpg
- Source authority: 3 (licensed print)
- Depicts: Blue Sector deck 7 corridor ring, 4 radial spokes, lift bank at 0°/180°
- Extracted: corridor width ≈ 2.4 m, ceiling ≈ 2.9 m, door pitch ≈ 8 m
- Feeds: station-schema/sectors/blue.yaml
- Conflicts: contradicts s01e03 wide shot (corridor reads wider) → resolved in favour of
  footage per authority ranking; plan value retained as annotation
```

---

## Canon Invention Log

Anything I build that has **no** reference backing gets logged here, permanently, so that
"what the show established" and "what we extrapolated" never blur together.

Status: empty.

---

## Open Conflicts

Reference disagreements not yet resolved. Each needs a ruling before the affected geometry
is built.

Status: empty.

---

### 01-station-exterior/exterior more.jpg
- Source authority: **2** (production material — orthographic renders of the CGI model)
- Depicts: top view, side view, and two end views of the station
- Extracted:
  - Radiators are **coplanar blades**, 3 above the spine and 3 below — edge-on in top view,
    full-face in side view. Overturns the radial-array reading. See `CONFLICTS.md` C-007.
  - Communications grid reads in the end views as **very long thin masts** extending far
    beyond the hull radius, consistent with the 2,120 m span from the specification table.
  - A row of ~5–6 **cargo modules runs along a dorsal line** on the mid-section, not
    distributed around the circumference as currently generated. **Not yet fixed.**
  - Fore section carries long **swept structures** in the top view, currently unmodelled.
- Feeds: `station/schema/station.yaml` components block
- Status: applied — radiators corrected (C-007), cargo modules moved to dorsal rows.
  Still outstanding: the fore swept structures, and the heat-exchange collectors are
  still a crude radial pinwheel rather than the swept form the top view shows.

---

### 21-QUARANTINE-animated-film/delen and sheridan in elevator.jpeg
<!-- catalogued in session 2i under its old path 09-garden-core-and-transit/; moved to
     quarantine in session 2k. Path corrected in 2q. -->
- Source authority: **DOWNGRADED — not the original series.**
- This is the 2023 animated film, not live-action Babylon 5. Different design language,
  stylised reinterpretation, and the uniforms are the later blue pattern rather than the
  Season 2–3 lock. Cannot be used as design reference under the era lock without violating
  it. Retained for reference only; **do not model from it.**
- Contains no lift display, so it does not bear on C-004.

### 11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg
- Source authority: **1** (on-screen footage, customs / arrival area)
- Depicts: the arrival concourse — "WELCOME TO BABYLON 5", a public information sign, and an
  **in-universe wireframe schematic of the station's forward section** on a wall display.
- Extracted:
  - The schematic is a cutaway of the forward docking region and shows **multiple parallel
    longitudinal lines** running through the structure, which in a side cutaway of a
    cylindrical station reads as **decks stacked radially**.
  - This is **supporting evidence for the radial reading of C-004**, but weak: the source is a
    low-resolution screencap and the lines cannot be counted or measured. It does not resolve
    C-004 on its own.
  - Also establishes public signage style: white-on-blue title bar, yellow warning text on
    black, and green vector-wireframe displays for technical readouts.
- Feeds: `CONFLICTS.md` C-004; signage and UI language for `16-signage-typography-ui`

---

### 09-garden-core-and-transit/central corridor.webp
- Source authority: **1** (on-screen footage)
- Depicts: a two-level concourse/corridor volume, dim and industrial — reads as Downbelow or
  a service area of Brown Sector.
- Extracted, and all of it bears on interior structure:
  - **Large circular structural ribs** frame the volume — ring frames of the cylindrical hull,
    exposed rather than clad. A primary architectural motif for the interior kit.
  - **Two occupied levels in one volume**: a catwalk with people on it above the main floor.
    Levels are therefore not only stacked decks; a "level" can be a mezzanine within a taller
    space. Relevant to C-004 — it means the level count and the deck count need not be equal.
  - Illuminated floor panels set into a dark deck; overhead truss and girder structure.
  - Lighting is low-key and practical-driven, with light coming from panels and signage
    rather than from any ambient fill.
- Feeds: interior kit spec, `CONFLICTS.md` C-004

### 04-sector-red/zocalo.webp
- Source authority: **1** (on-screen footage)
- **Era caveat:** the EarthForce uniforms in frame are the Season 1 grey/tan pattern with the
  gold sunburst, not the S2–3 dark pattern. The *set* is unchanged across seasons, so this is
  valid architectural reference and invalid costume reference. Recording the distinction
  because it generalises: a frame can be canon for one subject and out-of-era for another.
- **Correction, session 2q.** This entry originally read "neon signage in alien script". Two
  better frames — `04-sector-red/more zocalo.png` (1440×1080) and
  `11-props-and-technology/Zocalo neon signage in background.jpg` — show the same sign square
  on, and **it reads "Zocalo" in stylised Latin letterforms, not alien script**: a rounded
  single-stroke tube face with a dotted counter in the 'o'. It appears **cyan** in one frame
  and **orange-red** in the other. There *is* genuine alien-script neon in the Zocalo, but it
  is other signs, not this one. Corrected here and in `docs/interior-kit-spec.md` §5.
- Extracted, Zócalo commercial language:
  - **Neon signage, cyan, curvilinear**, mounted high above stalls. Signage is a primary light
    source, not decoration.
  - **Market stalls** with fabric awnings, string lighting and hanging goods, built as
    lightweight structures inside a hard architectural shell.
  - **Vertical structural columns** with panelled detail; **red-orange handrails** on the
    stairs and ramps, a strong recurring accent against otherwise desaturated grey.
  - **Crowd density is high and species-mixed** — this is the busiest public space on the
    station and its NPC density target should reflect that.
  - Lighting: warm practicals at stall level, cyan neon accents above, low ambient fill. The
    space reads dim overall with bright local pools.
- Feeds: interior kit spec, `16-signage-typography-ui`, NPC density targets for Red Sector

---

### 07-sector-grey/grey level 1.webp
- Source authority: **1** (on-screen footage, Grey Sector corridor)
- Depicts: a corridor looking down its length, wall square-on on both sides. The single most
  useful interior frame in the set for building corridors, and the only one that shows a wall
  flat enough to read its build-up.
- Extracted:
  - **The cross-section is a chamfered box, not a bore** — flat deck, upright walls, a chamfer
    into a flat soffit. This overturns the first interior assembly, which used circular ring
    frames and read as a pipe.
  - **Wall build-up, bottom to top:** projecting skirt · set-back dado · **heavy rail band at
    roughly hip height throwing a deep shadow reveal** · courses of large plates with recessed
    seams. The seams are the dominant articulation and they are recessed, not drawn.
  - **Portals punctuate the run** at close spacing, with heavy jambs and a **long linear light
    fitting in the soffit** — the brightest thing in frame and the reason the portals read as a
    receding rhythm rather than a row of holes.
  - **Bullnose pilasters** at the portal jambs, carrying **segmented vertical light strips**
    (short bars with gaps, not a continuous tube).
  - **Warm downlights low on the wall**, pooling the deck rather than filling the space.
  - **Deck is a fine tile grid**, roughly 0.5–0.7 m module.
  - A dark **signage plaque** at high level ("Le…l …") — level identification in the corridor.
- Feeds: `station/interior_kit.py` (`portal_frame`, `wall_assembly`, `pilaster`, `deck_grid`),
  `canon/INVENTIONS.md` INV-007

### 05-sector-green/corridor in alien sector.webp
- Source authority: **1** (on-screen footage, alien sector doorway)
- Depicts: a corridor looking through a doorway into a taller volume beyond.
- Extracted:
  - **The aperture is a chamfered polygon** — vertical jambs, sloping corners at roughly 45°,
    a flat head and a **raised threshold you step over**. Not a rectangle and not a circle.
  - The frame is **heavy and deep**, with a pronounced reveal. It is the depth, more than the
    outline, that makes the opening read as a pressure boundary.
  - Corroborates `grey level 1.webp` on the chamfered section independently.
- **Does not show a door leaf** — open, closed or moving. Nor does any other frame in the set.
  The leaf mechanism is therefore invented; see `canon/INVENTIONS.md` INV-008.
- Feeds: `station/interior_kit.py` (`chamfered_aperture`, `door_frame`, `door_leaf`),
  `canon/INVENTIONS.md` INV-008

---
---

# Session 2q — reference mining pass

Forty entries added. The two most important are the Security Manual sheets, which bear
directly on **C-003** and **C-004** and are written up in `canon/CONFLICTS.md`.

---

## 02 — Cutaways and plans

### 02-station-cutaways-and-plans/b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp
- Source authority: **3** (licensed print — the *Babylon 5 Security Manual*, per the filename
  and confirmed by shared terminology with the Contract 5 sheet in the same folder)
- Depicts: **"Sectional Schematic"** — a full-length longitudinal cutaway of the station, aft
  (left) to fore (right), captioned throughout, with a **sector bracket running along the
  bottom edge dividing the station into six named longitudinal bands.**
- **This is the highest-value single file in the reference set.** It is the only source that
  states sector *extents* rather than sector *names*.
- Extracted — sector bands, measured from tick centres on the bracket line (image is
  1080 px wide; the drawn station spans px 6→1075):

  | Band | px | fraction of length | × 8047 m | our framework says |
  |---|---|---|---|---|
  | **Yellow Sector** | 9–431 | 0.003–0.398 | 24–3202 | reactor + spine + truss; boundary at 3107 |
  | **Grey** | 431–486 | 0.398–0.449 | 3202–3613 | inside `aft_hull_block` |
  | **Green** | 486–537 * | 0.449–0.497 | 3613–3997 | inside `aft_hull_block`; boundary at 4207 |
  | **[unlabelled — Brown by elimination]** | 537–808 | 0.497–0.750 | 3997–6037 | `bearing_neck` + `habitat_cylinder` |
  | **Red** | 808–855 | 0.750–0.794 | 6037–6391 | `red_section` **6035–6465** |
  | **Blue Sector** | 855–1009 | 0.794–0.938 | 6391–7550 | taper + waist + `docking_sphere` |

  \* The Green/Brown boundary is a **clean break in the bracket line with no tick**, spanning
  px 533–541; 537 is its midpoint. Every other boundary has a drawn tick.

  - **Scale is 7.53 m/px and tick centres read to about ±3 px, so every figure above carries
    ±23 m.** Nothing finer is claimed.
  - **The Brown/Red boundary is indistinguishable from our Miller-derived
    `green_section`/`red_section` boundary**: 6037 m against 6035 m, i.e. well inside the
    ±23 m window. Red/Blue is 74 m out, inside our own declared ±75 m framework uncertainty.
    The two derivations share nothing — ours is Miller's top view rescaled by k = 2.5891, this
    is a different draughtsman's side cutaway in a different book.
  - **How strong that agreement actually is.** Mean miss over the six scored boundaries is
    110 m; random positions against the same 16 candidate boundaries in `station.yaml` average
    212 m, and 6% of random alignments do as well. Real, but **p ≈ 0.06, not proof** — and a
    2 m hit somewhere among six draws arises by chance 4% of the time. Use the sheet; do not
    treat it as verified. See C-003 UPDATE 2.
  - The sixth band carries no label in this reproduction. **Brown** is the only sector name
    absent, and the band contains the callout "WASTE MANAGEMENT SYSTEMS ('DOWN-BELOW')",
    which is Brown Sector on screen. Recorded as an inference, not a reading.
  - **The same band also carries "ZEN GARDEN" (callout dot at px 742) and "AMBASSADORIAL
    SUITES" (px 744), which are Green Sector on screen**, plus the station commander's
    administration complex, which is Blue. The elimination therefore does not produce a
    functionally clean band — see C-003 UPDATE 2, where this is weighed against the label.
  - **The interior is drawn as concentric cylindrical decks about the long axis.** In a
    longitudinal section a cylindrical deck at radius r appears as a pair of horizontal lines
    at ±r; that is exactly what the Red, Blue, Grey and Green bands show — long horizontal
    lines running the length of each section, symmetric above and below the centreline, with
    sparser vertical members (frames) crossing them. **Radial decks, drawn.**
  - The **core transfer shuttle runs on the axis** through the whole rotating assembly.
  - Callout **"CONCENTRIC PERSONNEL TRANSFER SYSTEMS"** — the word *concentric* is the
    draughtsman's own, applied to the transit system. Drawn as a diagonal chain of cars
    climbing from the non-rotating spine into the rotating assembly.
  - Callouts, aft→fore: fusion isotope slush tanks · primary fusion core · auxiliary fusion
    cores · coolant systems and maintenance · auxiliary power units (4) · zero-G maintenance
    fac. · variable gravity research torus · alpha power substation · mainstage power
    distribution node · concentric personnel transfer systems · rotation drivers and mag-lev
    bearing points · fabrication furnaces · multi-environ 'alien' sector · waste management
    systems ('Down-Below') · water recreation facilities · zen garden · core transfer shuttle ·
    hydroponics · station commander's administration complex · ambassadorial suites · 'Zocalo'
    and commercial sector · mag-lev bearing and transfer systems · cargo bay · **bay elevators
    (2)** · **docking bays (24)** · customs (×2, north and south) · low-g docking bays · ob. dome
  - **"DOCKING BAYS (24)"** is a new count, not previously in `00-MASTER.md`. It cross-checks
    against `03-sector-blue/Minbari Flyer 969 in docking bay 17.webp` — bay 17 exists, and 24
    bays accommodates it. Note this is *docking* bays, a different system from the 24-vs-28
    **cobra** bays of C-002; it does not resolve C-002 and may be where the "24" in
    `other map 4.jpg` originated.
- **Dimensional caveat.** The vertical scale is exaggerated: the drum reads ~183 px across
  against 267 px long (L/D 1.46), where our framework gives ~3.1 for the same span. Roughly 2×
  vertical stretch. **Do not measure deck spacing or diameters off this sheet.** Longitudinal
  band boundaries are usable because they were cross-checked against an independent framework
  and agree; nothing else here is.
- The reproduction is **cropped top and bottom** — three expansion leaders descend from the
  Grey, Green and sixth bands to a second row of detail brackets, cut off at y = 334 of 339,
  and two more rise off the top edge. A complete scan would carry that per-sector detail.
  **It would not necessarily carry the missing label**: the sector-label row itself is intact
  (all five labels sit in one band at y 271–285) and there is no ink between x 521 and 814,
  where the sixth band's label belongs. The band is unlabelled in a complete row.
- Feeds: `canon/CONFLICTS.md` C-003, C-004; `station/schema/station.yaml` sectors block
- Conflicts: contradicts `other map 2.jpg` on sector *ordering* (see C-003 write-up)

### 02-station-cutaways-and-plans/other map.png
- Source authority: **3, provisionally** — a colour sector plate sharing exact terminology with
  the Security Manual sheet above ("concentric personnel transfer system", "mainstage power
  distribution node", "variable gravity research torus", "alpha power substation", "fusion
  isotope slush tanks"). Same publication family. **Could be a colourisation of that plate
  rather than a separate page; a future session should confirm the publication.** Only 660×414.
- Depicts: a colour-coded longitudinal strip of the whole station **plus six radial
  cross-section rosettes**, one per sector, each annotated with named facilities.
- **The rosettes are the direct answer to what C-004's "level" indexes.** Every one of the six
  is drawn as **concentric annular rings about a central core**, with facilities assigned to
  specific rings and **radial "transport tubes" as spokes** connecting the outer rings to the
  axis. There is no longitudinal subdivision anywhere in them.
- Extracted, per rosette:
  - **Red** — outermost ring: Zocalo, Earharts, Central Corridor, Waste Management Systems.
    Inner rings: Casino, Dark Star, Law Courts, Security Central, Business District, Water
    Storage. Axis: Power Core / Core Shuttle. Spokes: Transport Tubes.
  - **Green** — a **thick outer annulus and a large hollow interior**, with only **three radial
    spokes** crossing to the axis. Outer ring: Alien Sector, Council Chamber, Fresh Air
    Restaurant, Earthforce Office, Zen Garden, Hydroponics, Waste Management Systems. This is
    the habitat drum, and it is drawn hollow — see the cross-check below.
  - **Brown** — concentric rings; **"DOWNBELOW" is marked with a double-headed arrow spanning
    an OUTER annular band**, with Happy Daze and Waste Management Control alongside it. This
    answers the objection recorded in C-004 head-on: the source says Downbelow *is* the outer
    ring.
  - **Blue** — concentric rings around a **central docking hub** on the axis, with an
    octagonal inner structure. Medlab One, Observation Rotundas, Fuel Stores, Mess Hall, Bay
    Elevators, Dock Workers' Quarters, Maintenance Facilities, Quartermaster's Office, Docking
    Bays, Post Office, Transport Tubes.
  - **Grey** — concentric rings: Atmosphere Monitoring Station, Commercial Research
    Laboratories, Alpha Power Substation, Fabrication Furnaces, Maintenance and Repair
    Facilities, Primary Breaker, Transport Tubes.
  - **Yellow** — **not** concentric. Drawn as a cog: a Power Transfer Core with **12 cooling
    fins radially arrayed**, plus Inspection Access and Coolant Transfer Tubes and Holding
    Tanks. Bears on C-007 — see the note appended there.
- **The strongest cross-check in the whole set.** The Green rosette (thick habitable outer
  annulus, hollow interior, three radial spokes, core shuttle on the axis) is what
  `03-sector-blue/Babylon_5_2-22_34b.jpg` — **authority-1 on-screen footage** — actually shows.
  A print diagram and a broadcast frame, derived independently, agree on the cross-section.
  That is what licenses using the other five rosettes for topology.
- Extracted, colour strip (bands measured by hue classification across the station body):
  **Yellow 36–238 px · Grey/uncoloured 238–270 · Brown 270–334 · Green 335–401 · Red 401–539 ·
  Blue (teal) 540–592.** Order aft→fore **Yellow, Grey, Brown, Green, Red, Blue** — which
  **swaps Green and Brown relative to the Security Manual sectional schematic.** Recorded as an
  unresolved residual disagreement in C-003; note also that the "Grey" band here is
  *uncoloured* structure and may simply be the rotating/non-rotating interface rather than a
  sector.
- Feeds: `canon/CONFLICTS.md` C-003, C-004, C-007
- Conflicts: with the Security Manual sectional on the Green/Brown order; with
  `other map 2.jpg` on the whole ordering

### 02-station-cutaways-and-plans/inside.jpg
- Source authority: **1** (on-screen footage) — **duplicate of
  `03-sector-blue/Babylon_5_2-22_35a.jpg`**, misfiled here. See that entry.

### 02-station-cutaways-and-plans/other map 2.jpg
- Source authority: **4** (fan reconstruction — a labelled CGI render with a data panel).
  Already the source of several `00-MASTER.md` figures; catalogued here for completeness
  because its sector claim is now contested.
- Extracted: the data panel (length 5 miles / 8.047 km, crew 6,500, population 250,000,
  constructed 2254–56, commissioned late 2256, Epsilon Eridani III, anti-fighter pulse cannons
  and two Starfury squadrons) — all already in `00-MASTER.md`.
- **Sector labels, read off the render:** Grey (industrial) aft near the radiator fins, then
  Brown (residential, "Downbelow"), then Green (diplomatic, The Garden), then cargo bays, then
  **Yellow (Zero-G storage) sitting between Green and Red**, then Red (commercial, The Zocalo),
  then the docking sphere / Blue.
  - Note this differs from the order recorded in `00-MASTER.md` §3.1, which has Yellow *after*
    Red. Read from the label positions, Yellow is between Green and Red.
  - Either way it is **contradicted by two authority-3 sources** which both put Yellow at the
    aft reactor end. See C-003.
- Feeds: `canon/CONFLICTS.md` C-003

---

## 03 — Sector Blue

### 03-sector-blue/Babylon_5_2-22_34b.jpg  ·  (= 01-station-exterior/view.jpg, duplicate, misfiled)
- Source authority: **1** (on-screen footage, S2E22)
- Depicts: the **interior of the habitat drum, looking along the axis** — the single most
  informative frame in the set for how the drum is built.
- Extracted:
  - The drum's **end cap is a disc of concentric annular bands** — alternating light and dark
    panelled rings, checker-plated in the outer bands, resolving into a radially segmented
    inner zone. Seen end-on, this is what a stack of concentric decks looks like.
  - A **lattice-girder truss runs the length of the axis**, carrying long cylindrical
    **illuminator tubes** below it. Its lower edge is **serrated — a rack**, which is how the
    core shuttle cars are driven along it.
  - **Core shuttle cars hang beneath the axial truss** — two visible, blunt-ended, windowed.
  - A **radial transport tube** runs from the axis out to the drum wall, banded in segments,
    with a conical collar where it meets a hub. This is the "transport tubes" spoke of the
    rosettes, in live action.
  - The drum's inner surface is **agricultural landscape** — fields, hedgerows, roads — curving
    up and over.
  - A blue light strip is set into one of the end-cap rings.
- **This frame is what validates `other map.png`'s rosettes.** It matches the Green rosette's
  cross-section independently.
- Feeds: `canon/CONFLICTS.md` C-004; core-shuttle and transport-tube geometry;
  `station/physics/core_shuttle.py` (confirms rim-to-axis transit is spoke-based)

### 03-sector-blue/Babylon_5_2-22_33a.jpg
- Source authority: **1** (on-screen footage, S2E22)
- Depicts: the same drum interior from a different angle, closer to the wall.
- Extracted: the **axial truss seen from below**, with a **single core shuttle car** hanging
  from it; a **radial transport tube in the foreground with coloured band markings** at
  intervals along its length; the far end cap in **red-orange lattice**; drum wall landscape
  with roads and field boundaries. Confirms the coloured banding is a repeating marking on the
  spoke tubes, not a one-off.
- Feeds: transport-tube and core-shuttle geometry

### 03-sector-blue/Babylon_5_2-22_35a.jpg  ·  (= 02-station-cutaways-and-plans/inside.jpg)
- Source authority: **1** (on-screen footage, S2E22)
- Depicts: the **interior of a core shuttle car**. Fills a gap `STATE.md` listed as covered
  only by the quarantined animated-film lift.
- Extracted: bench and individual seating in **red-maroon upholstery** on moulded grey bases;
  **grey panelled walls with recessed seams**; **amber/yellow illuminated panels** set low in
  the seat plinths (the interior kit's low-level light channel, applied to furniture); a
  continuous **window band** at seated eye height looking out onto the drum landscape; vertical
  **grab poles** floor to ceiling; a raked **windscreen** forward through which the tube's
  **red structural ribs** recede to a vanishing point.
- Era: S2, in era. The passenger is in Centauri court dress.
- Feeds: interior kit (transit car), `station/physics/core_shuttle.py` presentation

### 03-sector-blue/Babylon_5_2-22_29a.jpg  ·  **misfiled — this is the Garden, not Blue Sector**
- Source authority: **1** (on-screen footage, S2E22)
- Depicts: a landscaped garden terrace inside the drum.
- Extracted: paved winding paths in small setts; clipped hedges; a **water feature / cascade**
  against a planted bank; a timber bench; a circular raised planter with a **red-brown coping**;
  **orange sail canopies** on masts; a **multi-storey glazed building** behind; a **streamlined
  green-and-white transit car** on a track at the upper right; a **tunnel portal with an arched
  roof** into the terrace. Robed Minbari present.
- Note: the Garden has **buildings, surface transit and civic landscaping** — it is a
  townscape, not a park. Relevant to the eventual Green/Brown drum fit-out.
- Should be moved to `09-garden-core-and-transit/`.

### 03-sector-blue/comand and contorl.webp
- Source authority: **1** (on-screen footage)
- Depicts: Command & Control, looking forward at the main window.
- Extracted:
  - The **observation dome glazing** is a large circle carried on **radial spoke mullions**
    with a broad concentric ring band, set in a flat-panelled bulkhead with angled bracing.
    This is Dome 1 seen from inside — it should match the exterior `domes` component.
  - **Two occupied levels in one volume again**: a raised circular command dais with a
    stepped-up plinth, and a lower pit forward of it with red-lit consoles. **Stairs** with
    tubular handrails descend to a further level at the right.
  - Wall treatment: **two courses of long horizontal cyan-white light strips** at high and mid
    level, separated by dark panel bands — brighter and cooler than the Grey Sector corridor's
    warm downlights.
  - Consoles are **wedge-shaped angled desks on slim legs**, glowing from above.
  - Guardrails are **flat-topped bars on plain stanchions**, not the red-orange Zocalo type.
- Feeds: interior kit (C&C set), `domes` component cross-check

### 03-sector-blue/dock.webp
- Source authority: **1** (on-screen footage, CGI)
- Depicts: the interior of a rotating docking bay, Starfuries parked in rows.
- Extracted:
  - **Red-orange painted structural steel** overhead — deep box girders and a lattice gantry
    carrying **floodlights on pendant mounts** at regular spacing. The dominant colour of the
    volume.
  - Bay mouth is a **very wide, low, flat-topped opening** with the far side visible beyond;
    the volume reads as a long slot, not a hangar box.
  - Deck markings: **yellow/black hazard chevrons** on ramp edges, a **large red disc with a
    white oval emblem**, and a broad marked lane.
  - **Scale anchor:** a file of about eleven dock workers crosses the deck. They are tiny
    against the markings — the red disc is many times a person tall. Any docking-bay geometry
    must be sized against this, not against the Starfuries alone.
  - Starfuries carry **two-digit tail numbers** (29 legible).
  - Small **wall-mounted signage plaques** at head height on the bay walls.
- Feeds: docking bay interior kit; NPC dock-worker population

### 03-sector-blue/Minbari Flyer 969 in docking bay 17.webp
- Source authority: **1** (on-screen footage, CGI)
- Depicts: a Minbari flyer inside docking bay 17.
- Extracted: bay wall built as **stepped ledges with yellow/black hazard chevrons** on every
  step nosing; the bay ceiling is the **ribbed inner wall of the rotating drum**, curving; red
  warning beacons; service gantries with railings; blue-white deck lighting.
- **Establishes docking bay numbering reaches at least 17**, which cross-checks the Security
  Manual's "DOCKING BAYS (24)".
- Feeds: docking bay kit; `canon/00-MASTER.md` counts

### 03-sector-blue/war room.webp
- Source authority: **1** (on-screen footage, S3+)
- Depicts: the War Room.
- Extracted: a **large backlit galactic map mural** — spiral galaxy in blues, overlaid with a
  **red rectilinear sector grid** and small yellow labels; a **circular holo table** with a
  pale blue volumetric projection; moulded swivel chairs; a curved console rail with a
  **vertical white light ladder**; an arched structural frame at left continuing the chamfer
  language of the corridors; a small alphanumeric readout panel on the console.
- Era caveat: the set is S3+; within the S2–3 lock at its late end. Costumes are the black
  S3 pattern.
- Feeds: `16-signage-typography-ui` (galactic map / sector grid graphic language)

---

## 04 — Sector Red

### 04-sector-red/more zocalo.png
- Source authority: **1** (on-screen footage) — **1440×1080, the best Zocalo frame in the set**
  and materially better than the already-catalogued `zocalo.webp`.
- Extracted:
  - **The Zocalo neon reads "Zocalo" in stylised Latin letterforms, not alien script.** The
    already-catalogued entry for `zocalo.webp` describes it as alien script; that is a
    misreading and this frame corrects it. The face is a rounded single-stroke tube script with
    a dotted counter in the 'o'. **Here it is orange-red**; in
    `11-props-and-technology/Zocalo neon signage in background.jpg` the same wordmark is
    **cyan**. Two signs, or one sign in two states — record both, do not pick.
  - **The Babylon 5 "5" roundel is applied as furniture branding** — chair backs and table
    pedestals are white drums carrying a large outlined 5. Same glyph as the shield patch and
    the floor inlay. This is the strongest single piece of set-dressing identity in the sector.
  - **The Zocalo is two-storey**: an upper gallery with a railing where people stand and look
    down over a lower cafe floor.
  - The structure overhead is **large curved ribs / arches** springing from the gallery — the
    exposed-rib motif at concourse scale.
  - Deck is **large pale square tiles** on a darker grid, with a band of coloured chevron
    striping.
  - Stall canopies are **fabric on radiating spars**, parasol-fashion.
  - Backlit wall panels carrying alien script; wall-mounted screens at gallery level.
  - Tableware: **chrome domed-top shaker and stacked tumblers**.
- Feeds: `docs/interior-kit-spec.md` (correction), Red Sector fit-out, prop set

### 04-sector-red/Casino.webp
- Source authority: **1** (on-screen footage)
- Depicts: the casino, from a high angle.
- Extracted: a **monumental monochrome industrial mural** filling the back wall, Rivera-like,
  full of machinery and figures — the defining set piece; a **long green-illuminated bar
  counter**; a **wheel of fortune with a ring of filament lamps** at left; a **blue-felt gaming
  table** on a raised kerb; scattered small round tables; **cube pendant lights with grid
  faces** and a **white spherical pendant**; dense mixed-species crowd.
- Corroborates `other map.png`'s Red rosette, which names both Casino and Dark Star.
- Feeds: Red Sector fit-out; NPC density

### 04-sector-red/Earhart's.webp
- Source authority: **1** (on-screen footage, CGI)
- Depicts: **Earhart's** — a free-standing lenticular building **raised on a single central
  pedestal column** above the drum floor.
- Extracted: a saucer body with a **continuous glazed band around its equator** through which
  the interior reads (bar, tables, wood-slat screens, cyan backlit panels, patrons); flat
  tiled upper shell with rectangular roof hatches; a heavy shadowed under-shell. Beyond and
  above it, **the drum interior curving up** — fields, roads, and further domed structures.
- Named in the Red rosette of `other map.png`, which is a useful print-to-footage tie.
- Feeds: drum-interior architecture; Red Sector venues

---

## 05 — Sector Green

### 05-sector-green/council chambers.webp
- Source authority: **1** (on-screen footage)
- Depicts: the Babylon 5 Advisory Council chamber.
- Extracted:
  - A **curved raised bench** with an angled slab top and a **fine perforated gold mesh front
    panel lit from within** — the light source is the furniture.
  - **High-backed chairs with an open black lattice back**, one per delegation.
  - Back wall: a **radiating fan of angled fins** rising from behind the bench, with a large
    **circular spoked medallion** above it; deep blue field behind.
  - Floor: **pale blue-green polygonal mosaic**, large irregular tiles.
  - A fan of blue-and-white radiating panels laid on the bench top marks the speaking position.
- Era: EarthForce officer in the S2–3 dark uniform. In era.
- Species present: Narn, Minbari, human, Centauri, plus a robed ambassador in layered gauze.
- Feeds: Green Sector interiors; NPC species mix for council scenes

### 05-sector-green/rotunda.webp
- Source authority: **1** (on-screen footage)
- Depicts: a domed circular chamber ringed with windows.
- Extracted:
  - **The window ring looks INWARD onto the habitat drum interior** — green fields, a rising
    horizon, and white terraced structures. Not onto space. If the exterior
    `observation_rotunda` components are the same thing, they are drum-facing, not hull-facing;
    if not, this is a distinct interior element. **Flagged, not resolved.**
  - Window ring divided by **stubby columns carrying three ring bands near the top**, with
    flared capitals.
  - Ceiling is a **stepped, coffered dome** in gold and grey.
  - Floor: **circular mosaic with a radiating sunburst** in cream and grey.
  - Hanging **banners with alien sigils** between the columns; wall panels of vertical blue
    light slots; a **blue illuminated altar table**; a flight of steps up to a portal on the
    far side.
- Feeds: Green Sector interiors; observation rotunda cross-check

### 05-sector-green/conference aerea.webp
- Source authority: **1** (on-screen footage)
- Depicts: a lounge / observation area from above.
- Extracted:
  - **The Babylon 5 "5" roundel inlaid at large scale into the terrazzo floor**, on a raised
    circular dais with a stepped kerb.
  - A **cyan neon hexagon inlaid flush in the floor** running around the dais — light as floor
    geometry, matching the interior kit's light channels.
  - Curved walls carrying **arrays of tall narrow illuminated slots**, and a **backlit grid
    panel** at right.
  - Cafe tables with **red-glowing tops**; bentwood-style chairs.
- Feeds: interior kit (floor light channels), signage identity

---

## 07 / 06 — Grey and Brown

### 01-station-exterior/sleeping-in-light-05.jpg  ·  **misfiled — this is an interior, and it is the only Downbelow-class reference in the set**
- Source authority: **1** (on-screen footage, S5 "Sleeping in Light")
- Depicts: a wide industrial corridor / street receding to a vanishing point, derelict.
- **Era caveat, important.** S5 is outside the S2–3 lock, and in this episode the station is
  abandoned — the debris, the darkness and the dead panels are the finale state, not normal
  operation. **The set architecture is in-era; the dressing is not.** Same distinction already
  recorded for `zocalo.webp`.
- Extracted, all architectural:
  - A **continuous illuminated grating strip runs down the centre of the deck** — open metal
    grating over a light box, lit in a **checkerboard of live and dead cells**. This is the
    "illuminated floor panels" motif at full length and it organises the whole perspective.
  - Deck either side is **large recessed panels with raised borders**.
  - **Vertical white light bars** on wall pilasters at regular spacing — the segmented vertical
    strips of `grey level 1.webp`, here as continuous bars.
  - Overhead is **exposed girder truss with pipes and cable runs**, no ceiling.
  - Left: a **green-yellow neon sign in alien script** over a shopfront, orange-lit windows, a
    steel stair with a plain handrail.
  - Right: **banks of equipment panels with blue backlit displays**, a circular gauge, and a
    rack of black rectangular modules.
- STATE.md lists Brown Sector / Downbelow as **zero files**. This is the closest thing the set
  has: a wide commercial-industrial corridor of exactly the character Downbelow is described
  with. It should be **moved to `06-sector-brown-downbelow/`** with the era caveat attached.
  It does not remove the Brown reference gap but it materially reduces it.
- Feeds: `docs/interior-kit-spec.md`; Brown Sector

---

## 09 — Garden, core and transit

### 09-garden-core-and-transit/garden.png
- Source authority: **1** (on-screen footage, CGI)
- Depicts: a civic building and reflecting pool inside the habitat drum.
- Extracted:
  - **The drum's far side is visible overhead** — agricultural fields and terrain curving up
    both sides and over, with the **axial spine truss running across the top of frame** on
    splayed support struts. The canonical spin-habitat view.
  - Architecture: a **stone-coloured building of stacked cylindrical drums** with colonnaded
    upper storeys, cantilevered slab terraces, and a glazed ground floor.
  - Landscape: **rectangular reflecting pool**, a tall thin **waterfall** on a planted bank,
    paved terraces, mown lawn strips, **flagpoles with white banners**, **red-orange painted
    external stairs** (the accent again, outdoors).
  - Two figures give scale: the building is perhaps six storeys.
- Feeds: drum interior architecture; `canon/CONFLICTS.md` C-004 (drum is hollow, habitable
  surface on the inside of the outer wall)

### 09-garden-core-and-transit/The Gardens.webp  ·  (= The_Gardens01.webp, duplicate)
- Source authority: **1** (on-screen footage, CGI)
- Depicts: the drum interior looking along the axis from ground level.
- Extracted:
  - The **end cap as a huge radially segmented dish with concentric rings**, seen from within —
    the same structure as `Babylon_5_2-22_34b.jpg` from the other direction.
  - The **axial spine tube** is thick and **banded in segments**, running to the end cap, held
    by **struts fanning out from the spine to the drum wall**, with a bright light source at
    the spine.
  - Ground level: low blockish buildings with lit window bands, roads, **palm trees**, lawns.
  - Everything curves.
- Feeds: drum interior; core shuttle spine geometry

---

## 11 — Props and technology

### 11-props-and-technology/identicard readout.webp
- Source authority: **1** (on-screen footage)
- Depicts: an identicard database record on screen.
- Extracted, verbatim — **this is the canonical NPC record schema**:
  ```
  NAME:      ALEXANDER, LYTA        (SURNAME, FORENAME)
  ORIGIN:    EARTH
  DES/ATMOS: HUMAN/02
  SEX:       FEMALE
  DOB:       12/10/25
  PHYS CHR   (label only, unfilled)
  MEDICAL:   NO DISTG
  LICENSED PSI  (flag)
  VISAS      (label only, unfilled)
  ```
  - **`DES/ATMOS: HUMAN/02` means atmospheres are numbered, and humans breathe atmosphere 02.**
    This ties directly to `01-station-exterior/welcome to babylon 5.webp`, which states six
    atmospheres are available. Together they give a numbered environment system that the
    multi-environ alien sector and every NPC record can be built on. **New canon, authority 1.**
  - DOB is a two-digit year; day/month order is ambiguous from one sample.
  - Layout: portrait at left in a **blue-violet duotone** with a small header code; record at
    right on white over a **fine graph-paper grid**; labels black caps, values blue, **unfilled
    or pending fields in red**; a solid black triangular scroll pointer at the right margin.
  - Typeface is a squared techno sans with a **barred zero**.
- Feeds: `station/npc/` record model; `16-signage-typography-ui`; the alien sector environment
  model

### 11-props-and-technology/Identicard reader.webp and Identicard inserted into reader.webp
- Source authority: **1** (on-screen footage)
- Depicts: the handheld identicard reader, with and without a card inserted.
- Extracted:
  - Reader: a **dark grey wedge body on a pistol grip**, with a **portrait-format screen**
    showing a two-column record; a **vertical stack of three amber indicator lenses carrying
    icon glyphs** on the left face; a grey square button below them; three moulded slots each
    side; a raised guide rail on the right face.
  - **Identicard: a gold/brass card whose face is a dense honeycomb matrix of iridescent
    contacts**, inserted edge-on into the top slot.
- Feeds: prop set; security/customs NPC behaviour

### 11-props-and-technology/credit chit.jpg
- Source authority: **1** (on-screen footage; watermarked by a prop-collector site)
- Depicts: a credit chit being inserted into a counter reader.
- Extracted: the chit is a **brushed-metal rectangle with an engraved scroll pattern and a
  small circular emblem** near the top edge. The reader is a **small black wedge plinth with a
  top slot and a red LED line** on its front face.
- Feeds: prop set; commerce interactions

### 11-props-and-technology/communicator link.jpg
- Source authority: **1** (on-screen footage, S1E16 "Eyes" — title card in frame)
- Depicts: the communicator link worn on the hand.
- Extracted: a **chrome rectangular plate with a black inset carrying the EarthForce winged
  chevron**, worn on the **back of the hand** and held by a **wide brown leather wrist cuff**.
  Also on the desk: a **glossy photographic plate** with planetary surface imagery and callout
  labels, and printed documents with **colour bar-code strips**.
- **Era caveat: S1.** The wide leather cuff is the Season 1 mount. Do not take the strap form
  as S2–3; the plate itself persists.
- Feeds: prop set; NPC costume detail (with era flag)

### 11-props-and-technology/Vorlon, Narn,and  Centauri script examples.jpg
<!-- filename is verbatim: "Narn,and" has no space, and there are two spaces before "Centauri" -->
- Source authority: **1** for the three inset screencaps; **4** for the transcribed alphabets
  beside them (a fan compilation)
- Depicts: three writing systems, each as an in-situ screencap plus a transcribed sample.
- Extracted, as letterform families for procedural signage:
  - **Row 1 (gold on black):** lunate — crescents, half-moons and filled discs, no straight
    strokes. Terminals are round.
  - **Row 2 (orange/tan):** rectilinear — right-angle strokes, blocky counters, stepped forms.
  - **Row 3 (blue):** curvilinear — bowls, hooks and open counters, single-stroke weight.
    **This is the same family as the Zocalo neon**, which supports generating Zocalo-area
    signage from it.
- Filename assigns the rows Vorlon / Narn / Centauri in order; recorded as the uploader's
  attribution, not as a reading.
- Feeds: `16-signage-typography-ui`; procedural alien signage

### 11-props-and-technology/Zocalo neon signage in background.jpg
- Source authority: **1** (on-screen footage)
- Depicts: the Zocalo concourse over a bar counter.
- Extracted: the **cyan "Zocalo" neon** with a **zigzag chevron neon flourish either side**,
  mounted on a beam over a portal; **fluted cylindrical columns** flanking the portal; a
  repeating band of **rectangular louvre panels with diagonal blades** above; a **dark stone
  bar counter inlaid with small pale rectangles**; metal plates and drinking vessels; a
  shopfront at left signed "…STORE" with a display case.
- Feeds: Red Sector fit-out; signage

### 11-props-and-technology/more zocalo signage.webp
- Source authority: **1** (content) but **poor capture** — a photograph of a CRT, with
  scanlines and a burned-in subtitle.
- Extracted: the Zocalo wordmark again, cyan, above a lit portal on a dark soffit. Adds nothing
  beyond the two better frames; catalogued so it is not re-examined.

### 11-props-and-technology/civilian PPG.webp
- Source authority: **1** (on-screen footage)
- Depicts: a civilian PPG being loaded.
- Extracted: matte olive-bronze finish, **angular slab slide with a long top rib**, squared
  trigger guard, a magazine inserted from below the grip. Clearly a different weapon from the
  EarthForce sidearm.
- Feeds: prop set

### 11-props-and-technology/Earthforce issue Auricon PPG Pistol with removable sight.webp
- Source authority: **2** (production / prop photography — studio backdrop, not a frame)
- Depicts: the EarthForce PPG, main view plus an inset with the sight removed.
- Extracted: **polished nickel body**, **slotted barrel shroud**, cylindrical emitter block,
  **black rubber revolver-pattern grip with a medallion**, detachable optical sight on a dorsal
  rail. Only 304×231 — use `refzoom` before modelling.
- Feeds: prop set; security NPC loadout

### 11-props-and-technology/blue datacrystal.webp and clear datacrystal.jpg
- Source authority: **1** (on-screen footage; the second watermarked by a prop site)
- Depicts: data crystals held up to camera.
- Extracted: a **thumb-sized faceted rod of elongated hexagonal cross-section with a tapered
  tip**. **Two colours attested: deep blue and colourless.** The clear one is held by an
  officer in the **S2–3 dark dress uniform with a red-trimmed high collar and a gold gorget
  clasp** — useful in-era uniform detail.
- Feeds: prop set

### 11-props-and-technology/fresh air resturant signage with view.webp  ·  (= 04-sector-red/Fresh air.webp, duplicate)
- Source authority: **1** (on-screen footage)
- Depicts: the Fresh Air Restaurant in the Garden.
- Extracted:
  - Sign: an **oval plaque, "The FRESH AIR Restaurant"** — serif caps for FRESH AIR, script for
    "Restaurant", red on a pale ground — with a **teal neon double swoosh** arcing above it,
    mounted on a canopy fascia.
  - Ceiling structure: **red-painted tubes running across the space** carrying **downlight
    fittings at regular intervals**, plus a single suspended white strip.
  - Walls: **backlit blue-green translucent panels forming a raked screen**, densely planted
    over.
  - **Above and beyond, the far side of the drum is visible** as a dark mottled expanse.
  - Tables: white cloths, candles, mixed crowd.
- Note the restaurant is named in the **Green** rosette of `other map.png` and appears in the
  Garden — a print-to-footage tie that supports the Green rosette's facility list.
- Feeds: Green Sector fit-out; signage

---

## 12 — Starfury

### 12-starfury/Starfury more.jpg  ·  (= earth alliance fighter.jpeg, duplicate at a different size)
- Source authority: **2** (production concept art — **signed "STEVE BURG '93"**)
- Depicts: two pencil concept drawings on one sheet, captioned
  **"EARTH ALLIANCE FIGHTER (PRELIMINARY CONCEPT)"** and **"BABYLON-5 / EARTH ALLIENCE FIGHTER"**
  [sic].
- Extracted: the four-nacelle X-frame with the pilot pod at the intersection; nacelle end
  detail — recessed thruster bells, ring collars, side-mounted secondary thrusters, forward
  gun stubs; the **faceted, multi-panel canopy**; the ventral thruster cluster.
- **Caveat: explicitly "preliminary".** The flown Aurora differs. Use for surface detail and
  proportion intuition; do not derive thruster positions from it —
  `station/physics/starfury.py::aurora_thrusters()` is the authority the mesh must match.
- Feeds: `station/starfury_geometry.py`

### 12-starfury/Starfury.jpg
- Source authority: **1** (on-screen footage, CGI)
- Depicts: an Aurora Starfury front-quarter, thrusters lit.
- Extracted: **four nacelles firing cyan-white**; the **arms are not coplanar** — the forward
  pair sweep up and out, the aft pair down and back; a central **faceted canopy pod** with the
  pilot visible standing/upright; a ventral cluster of manoeuvring jets glowing; panelled
  white-grey hull with dark inset panels.
- Feeds: `station/starfury_geometry.py`

### 12-starfury/starfury even more detailed.jpeg
- Source authority: **4 — third-party fan 3D model**, not show reference. A studio-gradient
  turntable render (Sketchfab-style), 1920×1080, modern PBR materials.
- Useful as a shape reminder only. **Do not measure from it**: every panel line and greeble is
  the modeller's invention, and it is not distinguishable from canon by looking at it.
- Not quarantined — it is a fan reconstruction of the right subject, the same class as
  `other map 2.jpg`. Flagged here so it is never mistaken for authority 1 or 2.

---

## 14 / 15 — Characters, uniforms, races

### 14-characters-and-uniforms/earth_force_command uniforms.jpg and earthforce security uniforms.jpg
- Source authority: **4** (fan vector reconstruction — flat colour, three-view, titled
  "EARTH FORCE UNIFORMS")
- Depicts: front, side and back of the EarthForce uniform, in two colourways, plus the
  EarthForce emblem.
- Extracted, useful precisely because it is orthographic and flat:
  - Cut: **standing collar**; an **asymmetric dark front panel running diagonally from the left
    shoulder** across the chest; **deep contrasting cuffs**; a **wide waist belt with a gold
    rectangular buckle**; matching trousers into black boots.
  - Command colourway **blue-grey body**; security colourway **light grey body**; both with
    maroon-brown panels.
  - Insignia: small winged chevron on the left breast. The full emblem is a **blue and gold
    winged chevron in a hexagonal outline**.
- **Era caveat: this is the Season 1 pattern.** The S2–3 uniform is the darker one seen in
  `05-sector-green/council chambers.webp` and `11-props-and-technology/clear datacrystal.jpg`.
  Use this sheet for **cut and seam topology only**, not for colour.
- Feeds: NPC costume model (with era flag)

### 15-races-and-makeup/more vorlon.png
- Source authority: **1** (on-screen footage) — but the 2737×1955 pixel size is an **upscale**;
  the real detail is broadcast resolution. Resolution is not authority.
- Depicts: Kosh's encounter suit in profile, in vapour.
- Extracted: an iridescent **purple-blue shell with a hexagonal scale texture**; **curved
  dorsal horns/fins** sweeping back over the crown; a **single red eye lamp** in a recessed
  socket; a layered mantle over a dark robe; a **hanging pendant plate with an ornamented
  lozenge** at chest height. Background: a **frosted grid wall with backlit panels** — the
  Vorlon quarters / alien sector environment.
- Feeds: NPC species models; alien sector environment

### 16-signage-typography-ui/faction symbols.png
- Source authority: **4** (clean vector reconstruction, consistent with on-screen use)
- Depicts: eight faction emblems, captioned.
- Extracted: **Earth Alliance** (blue/orange roundel, torch and winged chevron, ringed
  "SEAL OF THE EARTH ALLIANCE") · **Minbari Federation** (blue triangle, hooked crescent) ·
  **Centauri Republic** (coral/purple plume of tapered rays with two eye-spots) · **Narn
  Regime** (twin black wing-blades on red-tan bases) · **Vorlon Empire** (two nested mottled
  crescents and a sphere) · Interstellar Alliance · League of Non-Aligned Worlds (orange
  triangle in a ring of teal stars) · Army of Light.
- **Era: only EA, Minbari, Centauri, Narn, Vorlon and the League are S2–3.** The Interstellar
  Alliance and the Army of Light are S4–5 and must not appear on S2–3 signage.
- Feeds: `16-signage-typography-ui`; NPC faction identity

### 16-signage-typography-ui/babylon 5 shield.webp
- Source authority: **4** (vector reconstruction of the on-screen station patch)
- Depicts: the Babylon 5 station shield.
- Extracted: a **red-outlined shield split diagonally**, grey lower-left and blue upper-right,
  with **seven white five-pointed stars** (four on grey, three on blue), over which sits a
  **yellow-and-black "5"** on a **vertical sword** with a yellow-tipped crossguard and pommel.
- The "5" glyph is the same one used as the **floor inlay** (`conference aerea.webp`) and as
  **furniture branding** (`more zocalo.png`). One mark, three applications — worth building as
  a single decal asset.
- Feeds: `16-signage-typography-ui`; NPC uniform patches; set dressing

### 01-station-exterior/welcome to babylon 5.webp  ·  **misfiled — this is signage, not exterior**
- Source authority: **1** (on-screen footage, customs area)
- Depicts: two backlit blue information boards in the customs hall.
- Extracted, verbatim — **two new authority-1 canon facts**:
  - Board 1: *"Welcome to Babylon 5 · [CUSTOMS SECTOR] · **ATMOSPHERE CAUTION** — SIX DIFFERENT
    ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5. OTHERS MAY BE CREATED BY PRIOR ARANGEMENT [sic].
    UNCOMMON ATMOSPHERIC MAKEUPS MAY BE SYNTHESIZED FOR ENCOUNTER SUITS. FOR SPECIFIC
    ATMOCHEMICAL BREAKDOWNS SEE MONITOR BELOW. REMEMBER…"*
  - Board 2: *"Welcome to Babylon 5 · [CUSTOMS SECTOR] · FOLLOW ALL CUSTOMS PROCEDURES. SEE
    MONITORS FOR DETAILS. **TIME ON B-5 IS EARTH MEAN TIME (EMT).** MONETARY EXCHANGE RATES
    [thro]UGH BUSINESS CENTER"*
  - **Six atmospheres** — with `identicard readout.webp`'s `DES/ATMOS: HUMAN/02`, this gives a
    numbered atmosphere system, humans on 02, six standing environments plus bespoke.
  - **Station time is Earth Mean Time.** This is the clock `station/npc/schedule.py` is
    implicitly using; it is now sourced rather than assumed.
  - **"Business Center"** is a named facility handling currency exchange — matches the
    "Business District" of the Red rosette in `other map.png`.
  - **"Customs Sector"** is used as an area label distinct from the six colour sectors.
  - Typography: white condensed oblique sans on blue; multiple thin horizontal rules under the
    title; a **rounded-rectangle "pill"** enclosing the area name; body copy centred, headings
    underlined.
- Should be moved to `16-signage-typography-ui/` or `11-props-and-technology/`.
- Feeds: `station/npc/schedule.py` (EMT), alien sector environment model,
  `16-signage-typography-ui`

### 01-station-exterior/Cobra Bays with starfurries.webp
- Source authority: **1** (on-screen footage, CGI)
- Depicts: a Starfury on a launch arm at a cobra bay.
- Extracted: the bay is framed by **heavy vertical structural columns**; the fighter is carried
  nose-out on a **lattice truss arm with a cradle**, not on a rail in a tube; **yellow/black
  hazard chevrons** on every deck edge; red and white marker lights on the columns;
  **orange-banded cylindrical tanks** racked at the right; open space beyond.
- Supports the physics result in `station/physics/starfury.py` — the bay presents the craft to
  vacuum and releases it; the drum's 52.2 m/s does the rest. **No catapult is depicted, and
  none is needed.**
- Feeds: `cobra_bay` component (listed as still crude in `STATE.md`)

---

## Still uncatalogued

Everything below has **not** been examined. Listed so the next session does not have to
re-derive the gap.

- `04-sector-red/`: `Doug's Dugout.webp`, `Darkstar_logo.webp`, `zocalo.webp` *(catalogued
  earlier; entry needs the alien-script correction applied)*
- `09-garden-core-and-transit/The_Gardens01.webp` *(byte-identical duplicate of `The Gardens.webp`)*
- `13-other-ships/kosh's transport.webp`
- `14-characters-and-uniforms/`: `Chief of security Garibaldi.webp`, `Galen.jpg`,
  `Marcus Cole in uniform.jpeg`, `Marcus Cole with Minbari denn'bok.jpg`, `Sheridan.jpg`,
  `Talia Winters in uniform.webp`, `Zach Allan in security uniform.jpg`,
  `security in uniform.jpg`, `talia-winters in gorgeous office.webp`,
  `uniform-army-of-light.jpg` *(S4–5, out of era)*
- `15-races-and-makeup/`: `G'Kar more.jpg`, `Kosh.webp`, `More Vorlon.jpg`,
  `Pak'ma'ra even more.jpg`, `Pak'ma'ra example.webp`, `Pak'ma'ra.webp`,
  `Vorlon and captain.webp`, `Vorlon moree.jpg`, `even more vorlon.jpg`,
  `more Pak'ma'ra.webp`, `more vorlon.png` *(catalogued above)*, `vorlon.webp`
- `16-signage-typography-ui/earthforce logo.webp`
- `01-station-exterior/exterior more.jpg` *(catalogued in session 2c)*

**No entry here, but heavily used in `canon/`** — these three predate the index and were
missed by the count above. They need entries, not examination:

- `02-station-cutaways-and-plans/b5-schematics-from-the-security-manual-v0-m4rs80drf36h1 more.webp`
  — this is the **Contract 5 sheet** (plan view, profile view, two end views, North/South
  convention, 0–8 km scale bar), the source behind C-005 and much of `00-MASTER.md` §1.3. It is
  the *companion* to the sectional schematic above, not a second copy of it.
- `02-station-cutaways-and-plans/Exterior map.jpg` — source of the exterior system counts.
- `02-station-cutaways-and-plans/Interior map.jpg` — the nested-radial diagram of C-003.

## Misfiled — recommended moves

Not moved in this pass, because moving a file changes every path that references it and the
schema and specs cite some of these by path. Recorded so it is a deliberate decision later.

| File | Currently in | Belongs in |
|---|---|---|
| `sleeping-in-light-05.jpg` | `01-station-exterior/` | `06-sector-brown-downbelow/` |
| `welcome to babylon 5.webp` | `01-station-exterior/` | `16-signage-typography-ui/` |
| `view.jpg` | `01-station-exterior/` | duplicate of `03-sector-blue/Babylon_5_2-22_34b.jpg` |
| `Babylon_5_2-22_29a.jpg` | `03-sector-blue/` | `09-garden-core-and-transit/` |
| `Babylon_5_2-22_33a/34b/35a` | `03-sector-blue/` | `09-garden-core-and-transit/` |
| `inside.jpg` | `02-station-cutaways-and-plans/` | duplicate of `Babylon_5_2-22_35a.jpg` |
| `Fresh air.webp` | `04-sector-red/` | duplicate of the `11-props-and-technology/` frame |
