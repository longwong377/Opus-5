# Reference Index

Maintained by Claude. Every reference file that lands in this tree gets catalogued here with
what was extracted from it and what it authorises us to build.

**Status:** 100 image files in the tree — **83 live, 17 quarantined** across two folders
(`21-QUARANTINE-animated-film`, `22-QUARANTINE-ai-generated`), neither of which may be
modelled from. **79 of the 83 live files carry their own entry. The remaining four are all in
`02-station-cutaways-and-plans/`** and are listed at the foot of this file under
*Still uncatalogued* — that section was rewritten in session 2t against an actual file-vs-heading
count, because it had gone stale.

**Session 2t verified the 2r/2s sweep** rather than adding to it: file count, a twelve-entry
re-open at magnification, an authority audit and a check on the blocking conflicts. Findings at the
foot under *Session 2t*. The sweep holds up; two corrections were applied in place and one
authority rating — `01-station-exterior/exterior more.jpg`, which turns out to be rendered from
the **same 3D model as the authority-4 Lawrence D. Miller sheets** — is flagged as unestablished,
with the consequences written into `canon/CONFLICTS.md` under C-004 and C-007.

**Session 2r closed three folders completely.** Every file in `01-station-exterior` (5),
`03-sector-blue` (8) and `04-sector-red` (7) — **20 files** — has now been opened and looked at,
including the ones catalogued earlier, and each has an entry in the *Session 2r* section at the
foot of this file. Nothing in those three folders is uncatalogued and nothing was skipped for
being low-resolution: the 240×160 `Darkstar_logo.webp` turned out to carry a named venue sign
and a third distinct typographic register. **No new quarantine candidates were found.**

**Session 2s closed three more folders completely** — `12-starfury` (4), `14-characters-and-uniforms`
(12) and `15-races-and-makeup` (12), **28 files**, every one opened and looked at. Entries are in
the *Session 2s* section at the foot. Two of them changed things outside costume: `Sheridan.jpg`
carries an **in-universe wireframe profile of the whole station** that corroborates C-007, and
`talia-winters in gorgeous office.webp` is the **clearest view of the habitat drum interior** we
hold. Both are written up in `canon/CONFLICTS.md`. **No new quarantine candidates matching either
existing signature**, but **`14-characters-and-uniforms/Galen.jpg` is from *Crusade*, not Babylon 5**
— out of scope, flagged in its entry, not moved. Six folders are now complete.

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

**Rewritten in the session-2t verification pass**, which counted the files on disk against the
`###` headings in this file. The list below is now the *actual* remainder; everything that was
listed here before and has since been done has been removed rather than struck, because the
struck list had grown longer than the live one.

**Count on disk: 100 image files — 83 live, 17 quarantined.** Of the 83 live files, **79 carry
their own `###` entry** (two headings deliberately pair a duplicate or a matched pair, per the
convention at the head of this file).

**Four files remain uncatalogued. All four are in `02-station-cutaways-and-plans/`, which was
not assigned to any agent in the 2r/2s sweep.** All four are already load-bearing in `canon/` —
they need entries, not discovery:

- `02-station-cutaways-and-plans/b5-schematics-from-the-security-manual-v0-m4rs80drf36h1 more.webp`
  — the **Contract 5 sheet** (plan view, profile view, two end views, North/South convention,
  0–8 km scale bar), the source behind C-005 and much of `00-MASTER.md` §1.3. The *companion* to
  the sectional schematic, not a second copy of it.
- `02-station-cutaways-and-plans/Exterior map.jpg` — the labelled exterior silhouette; source of
  the exterior system counts in `00-MASTER.md` §2, including the "Reactor Cooling Fins (12)" that
  C-007 turns on. Opened in the 2t pass: authority **4** (fan-labelled diagram, purple starfield
  border, callout leaders). It draws the cooling fins as blades **above and below** the spine in a
  side view, consistent with C-007.
- `02-station-cutaways-and-plans/Interior map.jpg` — the nested-radial diagram of C-003.
- `02-station-cutaways-and-plans/other map 4.jpg` — **the Lawrence D. Miller "SHEET 2: TOP VIEW"
  plate, © 2004, 2014 Lawrence D. Miller.** Authority **4**, and the single most-cited
  uncatalogued file in the repository: `00-MASTER.md`'s specification table and the k = 2.5891
  rescale both come from this sheet family. Opened in the 2t pass; see the session-2t entry below
  for what it carries and why it changes the authority of `01-station-exterior/exterior more.jpg`.

**Cataloguing `02-station-cutaways-and-plans/` is the highest-value remaining index work**, both
because it is the last gap and because it is the folder the README ranks first.

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

---
---

# Session 2r — deep re-examination pass: Green, Grey, Garden

Every file in `05-sector-green/`, `07-sector-grey/` and `09-garden-core-and-transit/` was
re-opened and magnified region by region. All nine files already had entries; **none is
superseded, but every one of them was thin, and two contained claims that do not survive
magnification.** The entries below are additive — read them together with the originals above.

Nine files, eight unique images (`The Gardens.webp` and `The_Gardens01.webp` are byte-identical,
md5 `06cb982bf7222a7566bc89675754f00e`).

**Quarantine check: clean.** All eight images carry the 1990s broadcast/period-CGI signature —
4:3 framing, interlace softening, chroma bleed, blown highlights, and in the CGI frames flat
Gouraud shading with visibly low-resolution painted textures. Nothing here matches the 2023
animated feature or an AI generator. `garden.png` was checked specifically because it is the
largest and cleanest file in the three folders: its alpha channel is uniformly 255 (a plain
screencap saved to RGBA, not a composited render), and its drum interior is a painted texture
on a cylinder, exactly the technique of the period. It is genuine.

---

## 07 — Sector Grey (re-examination)

### 07-sector-grey/grey level 1.webp  ·  **re-examined at 14×; one claim corrected, three added**
- Source authority: **1** (on-screen footage)
- Depicts: as the original entry. Still the best corridor frame in the set.
- **New — the wall plaque is legible enough to read the word, and it reads `LEVE…`.**
  Magnifying the right-hand wall (box 0.50–1.00 × 0.00–0.75) resolves the dark plaque as a
  **black ground carrying white uppercase sans-serif letters**, and the first four are clearly
  **L, E, V, E**. The word is `LEVEL`. **The number is off-frame** — the plaque runs off the
  right edge of the image and no amount of stretching recovers it, so the original entry's
  transcription "Le…l …" was reading a number that is not in the picture.
  What this does establish, at authority 1: **`LEVEL` is a wayfinding word physically signed on
  station corridor walls**, in white-on-black uppercase, on a landscape plaque set in a recessed
  dark field at high level. That is a typography and placement fact we did not have.
  Bears on C-004 — see `canon/CONFLICTS.md`, C-004 note 2r.
- **New — the far end proves the section is a full octagon, not a chamfered-top box.**
  The corridor terminates in a brightly backlit opening (box 0.27–0.45 × 0.28–0.50). Against
  that backlight the frame silhouettes **dark diagonal wedges at all four corners** — upper
  left, upper right, lower left and lower right. A chamfer at the *floor* corners is not
  visible anywhere else in the set and it changes the profile: the section is an **elongated
  octagon**, flat deck, upright walls, 45° chamfers top *and* bottom, flat soffit.
  `station/interior_kit.py`'s `wall_assembly` currently chamfers only the head.
- **New — the plate seams jog, they do not run straight.** At 3× the right-hand wall shows
  horizontal recessed seams that run level for a few metres, then **step up by one course over
  a short diagonal and continue level again**. The articulation is a staggered/stepped seam, not
  a running band. This is the single most characteristic thing about the wall and it is
  currently modelled as straight courses.
- **New — the vertical light strip is a fitting, not a slot.** It resolves into a **tall narrow
  recessed channel containing a stack of short luminous bars**, with a **fine perforated ladder
  strip running up one side** of the channel. Three components, not one.
- **Correction — the "deck is a fine tile grid, roughly 0.5–0.7 m module" claim is not
  supported.** An intensity profile across the deck at four heights (y = 430, 460, 490, 520)
  returns peak spacings of 4–47 px with means wandering from 10.5 to 18.1 px and no stable
  periodicity at any row. What the eye reads as a tile grid is a **dapple of specular
  highlights** thrown onto a semi-gloss deck by the overhead fittings. There may well be a tile
  module; this frame cannot measure it. **No deck module may be cited to this file.**
- **New — the deck carries painted line markings.** Bottom left (box 0.00–0.30 × 0.78–1.00)
  shows a **pale outlined circle** inlaid or painted in the deck and a **long straight pale line**
  running diagonally across it. Deck graphics are a kit element we have not accounted for.
- Feeds: `station/interior_kit.py` (`wall_assembly` — add bottom chamfer and stepped seams;
  `light_strip` — three-part fitting; new `deck_marking`), `16-signage-typography-ui`
  (LEVEL plaque), `canon/CONFLICTS.md` C-004
- Conflicts: corroborates C-004 (levels are signed and are a real addressing unit); does not
  resolve it. Contradicts nothing.

---

## 05 — Sector Green (re-examination)

### 05-sector-green/corridor in alien sector.webp  ·  **re-examined; the original entry described only the frame and missed the room**
- Source authority: **1** (on-screen footage). Sector attribution is **from the folder, not from
  the image** — nothing in frame names a sector.
- Depicts: a standard station pressure aperture looking into a **large, hazy, multi-level caged
  volume**. The original entry stopped at the aperture. The volume beyond is the more useful half.
- Extracted — the aperture (confirms and refines the original):
  - Elongated **octagonal** opening: vertical jambs, ~45° chamfers at all four corners, flat
    head, **raised threshold**. Independently corroborates the octagon now read off
    `grey level 1.webp`'s far end.
  - The jamb is a **deep battered pier** — the reveal is roughly as deep as it is wide.
  - **Amber segmented light bars are set into the chamfer of the frame itself** (box 0.70–1.00
    × 0.30–0.90 resolves three or four short bars). Same fitting family as the grey corridor's
    white vertical strips, **tinted amber here**. The frame is a lighting element, not just a
    structural one.
- Extracted — the volume beyond:
  - A **cage of continuous horizontal rails at regular vertical spacing** (at least five
    courses) crossed by vertical posts, spanning the full width and full height. Multi-level
    and open — you can see through several storeys.
  - **A large black open hoop**, roughly human height, gapped at the top like a `C`, standing
    between two short posts at mid-level. An unidentified fixture; distinctive enough to be
    worth reproducing.
  - **The floor is an illuminated grating in saturated yellow** — magnified (box 0.15–0.70 ×
    0.70–1.00) it resolves into a grid of roughly square cells, **each cell containing about
    three short horizontal louvre bars over a light box**. Roughly 7 cells across × 3–4 deep in
    view.
  - **Volumetric haze throughout**, with hard vertical light shafts descending from a source
    high above. The haze is the defining quality of the space and it is not present in any
    oxygen-environment frame in the set.
  - Colour is **yellow-green overall with one cold blue pocket** at right (a louvred panel and a
    blue-lit bay). Two-temperature lighting in one volume.
- **Generalisation worth acting on: the illuminated floor grating is a station-wide element,
  colour-tinted per environment.** It now appears in four frames — white/blue in
  `09-garden-core-and-transit/central corridor.webp`, dead-and-live checkerboard white in
  `01-station-exterior/sleeping-in-light-05.jpg`, saturated yellow here, and as pooled uplight
  in `grey level 1.webp`. That is one kit part with a tint parameter, not four set dressings.
- Feeds: `station/interior_kit.py` (`chamfered_aperture` — add chamfer-mounted light bars;
  new `light_grating` with tint), `docs/interior-kit-spec.md`, `17-lighting-and-color`
- Conflicts: none. Supports the octagonal section.

### 05-sector-green/council chambers.webp  ·  **re-examined; one shape claim corrected**
- Source authority: **1** (on-screen footage)
- **Correction — the bench is faceted, not curved.** Magnifying the bench (box 0.10–0.75 ×
  0.55–1.00) shows a **straight run meeting a mitred corner**, not an arc. The council bench is
  a **polygonal ring of straight segments**, which is a different mesh and a different set of
  seat positions from a swept curve. The original entry's "curved raised bench" should not be
  built from.
- Extracted, new detail:
  - **The bench nosing is studded with regularly spaced round rivets** along its full length —
    a bullnose capping rail, riveted at roughly one rivet per hand's breadth. Clearly visible
    and easy to miss at 1×.
  - The lit front panel is **very fine square-hole perforated sheet** — hundreds of holes across
    the panel's width, warm gold, evenly backlit with no visible lamp hotspots. Set in a plain
    grey frame with a bottom kick rail.
  - Above the bench, a **grey slab top with a chamfered edge**; below the mesh, a **recessed
    plinth** holding the whole bench off the floor.
  - **Chairs: a black square-section frame with an open lattice back of 3 columns × 6 rows** of
    square openings, under a solid top rail. Countable and consistent between the two chairs
    visible square-on.
  - **The back-wall medallion is not a plain spoked disc.** Concentric zones from the centre out:
    plain hub button · ring of fine radial flutes · plain annulus · and then a **broad white arc
    that does not close** — it thins and terminates rather than meeting itself, reading as a
    spiral or an open ring. That asymmetry is the whole character of the emblem.
  - The **fan behind it is flat rectangular slabs of varying length radiating outward**, stepped
    in depth so they overlap in layers. Pale grey-white against a deep blue field.
  - **The chamber is lit asymmetrically** — the fan-and-medallion side is bright, the opposite
    wall (box 0.55–1.00 × 0.00–0.45) is a dark grey panel with a band of vertical slats at high
    level and almost no fill. Do not light this room evenly.
  - Floor: large irregular polygonal slabs, pale blue-green and cream, with visible joints —
    crazy paving at roughly 0.4–0.6 m per slab judged against the bench height.
- Era: EarthForce officer in the S2–3 dark uniform. In era.
- Feeds: Green Sector interiors; `16-signage-typography-ui` (the medallion is a station emblem
  candidate); NPC species mix
- Conflicts: none.

### 05-sector-green/rotunda.webp  ·  **re-examined; the drum-view claim was tested, not assumed**
- Source authority: **1** (on-screen footage)
- Depicts: a domed circular chamber ringed with windows, in ceremonial use by robed figures.
- **The original entry asserted the windows look inward onto the drum. That assertion was
  tested and it survives, but as corroboration and not as proof.** The test: in a spin habitat
  terrain fills the window from sill to head, because there is no sky; on a planet a window at
  this height shows a sky band unless it faces a hillside. Magnifying the right-hand windows
  (crop 430–716 × 215–330) shows **green and khaki terrain reaching the window head with no sky
  band at all**. Against that: the left-hand windows are blown out white and could be sky, and
  the window heads are deeply recessed, so a sky band could be hidden. **Reading: drum interior,
  with the caveat stated.**
- Extracted, new and countable:
  - **At least eight columns are visible across the far arc of the window ring**, evenly spaced.
    A closed ring at that spacing implies roughly sixteen bays. Recorded as a count read off one
    viewpoint, not a canon figure.
  - **Column order: a plain slightly tapered cylindrical shaft carrying a group of THREE narrow
    ring collars**, then a longer plain shaft, then a short stepped capital under the
    entablature. **This same order appears on the Garden's civic building in `garden.png`** —
    see the cross-reference note below, and `canon/CONFLICTS.md` C-003 note 2r.
  - Through the windows: **sloping green fields, a pale causeway running diagonally, a slender
    tower with a broad flared dish cap** (left of centre) and **white terraced building masses**
    (right of centre). Terrain rises steeply to the right.
  - Above the columns, a **corbel course of stepped rectangular blocks** in layered tiers, then
    a **smooth warm gold-bronze dome with broad radial ribs**. Two pale **conical elements**
    stand on the cornice at upper left.
  - Wall below: **warm bronze-brown mottled surface**, with a **continuous band of narrow pale
    vertical slats at about waist height** running right around the room, lit so it reads as a
    bright horizontal ribbon.
  - **Four hanging banners**: deep indigo with a pale blue-white sigil low down; dark grey-blue
    plain; **pale lavender with a large dark navy sigil low down**; and one dark with an amber
    sigil at the right edge. Each is a long vertical cloth, sigil in the lower third.
  - **Tall blue backlit lattice panels** flank the room at far left and far right.
  - Centre: a **flight of about ten pale steps** rising to a dark portal, flanked by piers whose
    lower ends carry a **comb of vertical slots**; a handrail on the left.
  - Foreground: a **dark plinth lectern with a sloping cyan-glowing top**, the glow divided by
    **dark bars into a symmetrical chevron figure**, with a pale cloth draped over its head edge.
  - Floor: **radiating sunburst mosaic** — cream and tan ground, **triangular radial wedges**
    about a centre, and a **broad concentric band of chevrons** at larger radius.
  - Occupants: roughly ten to twelve figures in **cream and pale-gold layered robes** and three
    in **long black robes with a metal-buckled belt**. Minbari ceremonial dress.
- Feeds: drum interior (glazed rooms in the drum wall); Green Sector interiors;
  `canon/CONFLICTS.md` C-003 note 2r
- Conflicts: bears on C-003 — see the note added there. Does not resolve it.

### 05-sector-green/conference aerea.webp  ·  **re-examined; the roundel is now specified well enough to author**
- Source authority: **1** (on-screen footage, high overhead angle)
- Depicts: a circular lounge / café with a Babylon 5 roundel inlaid in the floor.
- Extracted, new:
  - **The "5" is a DARK glyph on a PALE disc**, not the reverse. Construction, magnified
    (box 0.25–0.85 × 0.30–0.95): a **thick horizontal top bar with a slanted left end**, a
    **vertical stem descending at the left**, and a **large near-circular bowl containing a
    separate small round dark counter at its centre**. The bowl is an annulus with an
    independent dot in the middle — that dot is the signature of the mark and it is what
    distinguishes it from an ordinary numeral 5.
  - The pale disc is bordered at its lower edge by a **ring of triangular teeth**; about seven
    are visible across the near arc, implying roughly 24–32 around.
  - The disc sits on a **raised circular dais with two or three concentric steps**, the step
    nosings visible as curved bands.
  - **The cyan floor light is a flush-set luminous band of finite width, not a hairline** — it
    has a bright core and a cyan halo, and it reads as slightly proud of the floor. Segments
    meet at obtuse vertices consistent with a **hexagon**.
  - **Left and right walls each carry a curved arc of tall narrow rounded-corner light slots** —
    about fifteen countable in the left arc, pale blue-white.
  - **Two coarse backlit grid panels in salmon-pink**, upper left and upper right: roughly 5 × 3
    large square cells, each cell carrying a smaller square inset.
  - **A bank of screens** at upper centre-left, roughly 3 rows × 4–5 columns, at least one
    carrying a figure — a monitor wall or departure board.
  - **A serving counter with two illuminated glass-topped vitrines** on dark pedestal legs,
    upper centre, staffed.
  - **Five or six round café tables ring the dais.** Each has a dark top carrying a **bright
    orange-red illuminated inset panel**; chairs are **bentwood-style with a round back hoop**.
  - Outer floor is dark speckled terrazzo carrying a **repeating wave/scallop border**.
  - Rough scale, stated as rough: at café-table diameter ≈ 0.8 m the pale disc is about **4–5 m
    across**, so the "5" glyph is roughly 2.5 m tall. The lens is wide and the angle steep;
    treat as an order of magnitude, not a dimension.
- Feeds: `16-signage-typography-ui` (the roundel is now authorable); interior kit (floor light
  channels, backlit grid panel, light-slot arc); Green Sector interiors
- Conflicts: none.

---

## 09 — Garden, core and transit (re-examination)

### 09-garden-core-and-transit/garden.png  ·  **re-examined; the radial transport spoke is in this frame and had been missed**
- Source authority: **1** (on-screen footage, period CGI)
- Depicts: a civic building and reflecting pool inside the habitat drum, with the drum's far
  side overhead.
- **The most important thing in this file is overhead and the original entry called it "the
  axial spine truss on splayed support struts". It is more specific than that.** Magnified
  (box 0.50–1.00 × 0.00–0.50) it resolves into a **radial transport assembly**:
  - a **long open lattice girder of triangular section with diagonal web members**, running
    from the axis down toward the drum wall;
  - a **junction node** part-way along where several members converge;
  - **tubular arms radiating from that node** — at least three — each a **segmented cylinder
    with ring collars between barrel sections**, tapering, reading as pressurised transfer tubes;
  - the whole assembly **spanning the drum's diameter in mid-air**, silhouetted against the far
    inner surface.
  This is the **radial transport spoke** that `canon/CONFLICTS.md` C-004 UPDATE says the
  rosettes and `Babylon_5_2-22_34b.jpg` depict — here at authority 1, in daylight, with its
  construction legible. `station/physics/core_shuttle.py` assumes rim-to-axis transit; this is
  the picture of the thing it assumes.
- Extracted — the drum's inner surface, which is buildable content:
  - **Patchwork agricultural plots** — irregular quadrilaterals in olive, khaki and ochre with
    pale boundary lines, tessellating across the surface.
  - **Rocky pale broken terrain** interleaved with the farmland.
  - **At least one pale blue body of water** (a lake), visible above and left of the truss.
  - **Blocky pale built-up areas** on the far side.
  - **Two concentric circumferential ring-bands cross the surface** — one a wide pale
    terrace-or-roadway, one a darker band carrying **regular transverse ticks** like a rail or
    ladder. These follow the drum's circumference and are the largest man-made features on it.
- Extracted — architecture, and a cross-reference that matters:
  - **The building's colonnade uses the same triple-collar column order as `rotunda.webp`** —
    stubby shaft, three fine ring collars, plain shaft above, flat entablature. Two Green-filed
    interiors sharing an architectural order. See `canon/CONFLICTS.md` C-003 note 2r for what
    that is and is not worth.
  - Massing: a **tall central cylinder with an open colonnaded loggia at its top storey**
    (about seven or eight columns across the visible half, so ~14–16 around), capped by a plain
    drum band and a flat roof with a projecting rim; a **secondary lower cylinder** at right
    with **plain narrow piers, no collars** — a second, simpler order; **cantilevered horizontal
    slab canopies with rounded ends** wrapping the base in layered tiers.
  - Ground floor: a **deeply recessed arcade of tall narrow bronze-framed windows**, grouped in
    threes and fours by mullions, warmly lit from within.
  - A **tall terracotta slab pylon** stands proud at the right — the red-orange accent again,
    here as primary architecture rather than trim.
  - Materials: **warm pinkish-grey sandstone or render**, dark bronze joinery, terracotta
    accents, pale concrete paving. The idiom is Frank Lloyd Wright — stacked cylinders and
    banded horizontals.
  - Landscape furniture: **rectangular reflecting pool with a dark stone coping**, a tall thin
    **waterfall** on a planted bank, **large pale flagstone paving**, **low white slab benches**,
    **at least four slender white flagpoles**, **striped mown lawn**, deciduous trees and shrubs.
  - The terrace balustrade is a **five-bar horizontal railing** on slender posts, pale blue-grey.
- **Scale, with its method stated.** Two walking figures give the only calibration:
  at their depth 1.75 m ≈ 70 px, so **≈ 40 px per metre there**. That figure cannot be carried to
  the building, which is much further away. Using the ground-floor window band as ~2.4 m gives
  ≈ 11 px/m at the building, and on that the central tower is **roughly 25–30 m, seven to eight
  storeys**. The original entry's "perhaps six storeys" is close and slightly low. Both are
  estimates; neither belongs in `00-MASTER.md` as a dimension.
- Feeds: drum interior surface content; `station/physics/core_shuttle.py`; drum architecture;
  `canon/CONFLICTS.md` C-003 note 2r, C-004
- Conflicts: supports C-004's settled finding that the drum is hollow with habitable surface on
  the inside of the outer wall, and puts the radial spoke at authority 1.

### 09-garden-core-and-transit/The Gardens.webp  ·  (= The_Gardens01.webp, byte-identical)  ·  **re-examined; the axial column's construction is legible**
- Source authority: **1** (on-screen footage, period CGI)
- Depicts: the drum interior looking along the axis toward the forward end cap, from ground level.
- Extracted — the end cap (box 0.15–0.85 × 0.00–0.45):
  - **Radially segmented into wedge bays** by long ribs converging on the hub.
  - **Each bay is stepped in tiers toward the centre** — a regular pattern of rectangular blocks
    diminishing inward, so the cap is a terraced dish rather than a smooth one.
  - A **crown of boxy protruding elements rings the hub** at the base of the spine, several
    casting hard shadows.
  - A **bright light source sits at the hub**.
- Extracted — the axial column, which is the find here:
  - It **alternates closed and open sections along its length**. From the cap downward:
    a **closely-banded collar of six or seven ring flutes**; a **flared collar**; then an
    **OPEN section — a rectangular lattice cage with two vertical members and horizontal rungs,
    showing a darker inner core through it**; then a **plain cylinder** continuing toward camera,
    tapering to a blunt nose.
  - That open rung section is the **racked lattice truss** `canon/CONFLICTS.md` C-004 UPDATE
    describes from `Babylon_5_2-22_34b.jpg`. Seen here from the opposite end and in daylight it
    is unambiguous, and it adds the alternation: **the axis is not one uniform tube, it is
    banded cylinder sections spliced to open trussed sections.**
  - **Splayed struts descend from a collar on the spine to the drum floor** — two clearly
    visible, symmetric, slender tapering tubes, with more fanning behind. The axis is braced
    radially at intervals, not free-floating.
  - A **brilliant white flare sits where the spine meets the strut collar** — the axial
    illuminator, and the drum's day-cycle light source.
- Extracted — the settlement, which the original entry compressed into one line:
  - **Low-rise flat-roofed blocky buildings, two to four storeys, in a dense orthogonal street
    grid.** Pale warm stone.
  - **Continuous horizontal window banding** — rows of small bright rectangles in dark recessed
    bands, giving strong horizontal striping. One large building at right (box 0.55–1.00 ×
    0.50–1.00) shows **exactly three stacked glazed bands over a solid battered base**.
  - **A cylindrical silo or drum with a domed top** at centre-left.
  - **Long low linear blocks** with unbroken window strips — terraces or sheds.
  - **Street lighting**: bright point sources on posts along the streets.
  - **Palm trees** lining streets and open ground, plus dark rounded broadleaf trees and clipped
    hedges in the foreground.
  - **A dark rectangular body of water** with a paved margin, right of centre.
  - **Rolling mown green hills** rising behind the town, with tree lines and further terraces.
- Colour: the whole frame carries a heavy **pink-magenta cast** (tape colour shift). Greens read
  olive. **Do not colour-match this file** — match `garden.png`, which is clean.
- Feeds: drum interior; core shuttle spine geometry; drum settlement content
- Conflicts: none. Corroborates C-004's axis findings.

### 09-garden-core-and-transit/central corridor.webp  ·  **re-examined; the filename may place this frame radially, and if so the file is misfiled**
- Source authority: **1** (on-screen footage)
- Depicts: a wide two-level public concourse, dim, structural, busy with civilians.
- **The identification matters more than the dressing.** `other map.png` (authority 3) lists
  **"Central Corridor" as a named facility in the OUTERMOST ring of the Red Sector rosette**,
  alongside Zocalo, Earharts and Waste Management — see `canon/CONFLICTS.md` C-004 UPDATE §1.
  This file is named `central corridor`. **A filename is the uploader's label, not a source**,
  so this is not proof of anything. But if the label is right, then:
  1. the frame depicts an **outermost-ring** space, and
  2. the file belongs in `04-sector-red/`, not `09-garden-core-and-transit/`, and
  3. the original entry's guess that it "reads as Downbelow or a service area of Brown Sector"
     is probably wrong — it is a **Red Sector public concourse**.
  The frame's own content is consistent with reading 1: **the hull's circular ring frames are
  exposed here**, and in a concentrically decked cylinder only the outermost deck sits against
  the hull ribs. Recorded in `canon/CONFLICTS.md` under C-004 as corroboration.
- Extracted, new structural detail:
  - **Two or three concentric circular ring frames** cross the view, **dark oxide red** — thick
    tubular ribs, the largest passing in front of everything at the frame edge. The colour is
    consistent and strong enough to be a deliberate note, not grime.
  - The **catwalk is narrow — about two people wide** — with a **two-bar railing on slender
    vertical posts** and a **solid fascia beam carrying a light line along its edge**.
  - **The ceiling is a raked panelled soffit**: long rectangular panels in canted rows with dark
    joints, running away from camera in trapezoidal bays. Not open truss, and not flat.
  - **Diagonal bracing** and **canted planar bulkhead panels** fill the upper volume, catching a
    hard blue-white shaft from above.
  - **The centre-line light is a ladder of PAIRED square cells** — two columns of small square
    lights side by side in a raised dark kerb, running the corridor's length.
  - **The floor either side is large pale-blue emitting panels** in a running-bond grid with dark
    joints. (They could be light cast through the grating catwalk above; the regular bond
    pattern and the absence of cast shadows on them favour emitting panels, and that reading
    agrees with `sleeping-in-light-05.jpg` and the alien-sector floor.)
  - **Wall-mounted vertical white light blades** set in chamfered dark surrounds, with **small
    red indicator lamps** above them.
  - Left: a **vendor front** — backlit orange-red panels behind vertical mullions over a counter.
  - A **small wheeled trolley with a magenta-lit top** is being pushed at bottom centre; a good
    prop for street-level life.
  - Crowd is **dense, civilian, mixed dress** — a public space, not a service corridor.
- Feeds: `docs/interior-kit-spec.md`; Red Sector (probable); `canon/CONFLICTS.md` C-004
- Conflicts: corroborates C-004's radial-deck reading; does not resolve the numbering direction.

### 09-garden-core-and-transit/The_Gardens01.webp
- **Byte-identical duplicate of `The Gardens.webp`** (md5 `06cb982bf7222a7566bc89675754f00e`).
  No separate content. Listed so the file count reconciles.

---

## Misfiled — additions from this pass

| File | Currently in | Belongs in | Confidence |
|---|---|---|---|
| `central corridor.webp` | `09-garden-core-and-transit/` | `04-sector-red/` | **low** — rests on the filename matching a facility named in `other map.png`'s Red rosette. Do not move until the identification is confirmed on screen. |

---
---

# Session 2r (Blue / Red / Exterior) — exhaustive pass over `01-station-exterior`, `03-sector-blue`, `04-sector-red`

<!-- A sibling pass in the same session covered Green, Grey and the Garden; its section is
     above. The two are independent and neither supersedes the other. -->


Every file in those three folders was opened and looked at, including the ones already
catalogued in earlier sessions. **20 image files, 20 entries below.** Where an entry already
existed it is superseded or supplemented here rather than duplicated, and the supplement says
which. Two findings were written into `canon/CONFLICTS.md`: a quantified end-cap measurement
under C-004, and a facility/topology tension under C-003 that makes C-003 *harder*, not easier.

**No new quarantine candidates.** Nothing in these three folders matches the 2023 animated-film
signature (stylised reinterpretation, later blue uniforms) or the AI-generated signature
(incoherent panel lines, invented typography, impossible structure). All twenty are broadcast
frames, CGI shots from the show, or renders of the production model.

---

## 01 — Station exterior

### 01-station-exterior/exterior more.jpg
**Supplements the session-2c entry above; that entry stands, this adds the end views and
refines the authority.**
- Source authority: **2, with a caveat that was not previously recorded.** 1280×960. The
  *projections* are orthographic renders of the production CGI model and are trustworthy as
  geometry. The *sheet* is not a production document — it is a fan-assembled desktop wallpaper:
  rounded-rectangle bevelled border, marbled backdrop, drop shadows under each view, a large
  glassy embossed "5" in the lower right, and a ghosted three-quarter render bleeding through
  the middle. **Treat the geometry as authority 2 and the sheet itself as authority 4
  packaging.** It is not AI-generated: panel lines are continuous, the four views agree with
  each other, and the texture tiling is period-correct mid-90s CGI.
- Depicts: top view (upper), side view (middle), **aft end view (lower left) and fore end view
  (lower right)**. The two end views were not previously extracted.
- Extracted — **fore end view (the Blue Sector face), and this is the valuable one:**
  - The forward docking structure seen end-on is **a disc of concentric annular bands**, exactly
    the same organising idea as the drum end cap in `03-sector-blue/Babylon_5_2-22_34b.jpg`.
    Outward from the axis: a **dark cruciform hub with a single red lamp at its centre**; a
    ring of **fine radial teeth** (a cog-like band); a **bright silver-white annulus**; a broad
    **blue panelled annulus** subdivided by radial and circumferential seams; and an outermost
    **finely toothed rim**. Four to five distinct concentric bands.
  - This is authority-2 corroboration for `other map.png`'s **Blue rosette** — "concentric rings
    around a central docking hub on the axis". A print diagram and a production render agree.
    See the note appended to C-004.
  - Two **very long thin masts** run vertically far beyond the hull silhouette in *both* end
    views, and two shorter stub arms project laterally at the equator. The masts' span is
    consistent with the 2,120 m communications grid in the specification table.
- Extracted — **aft end view:** a dark rust/brown disc (the reactor end) with a **grey polygonal
  hub**, black radial voids, and a **horizontal lit spar** crossing it with a bright segmented
  strip on its starboard half. Far less structured than the fore face — the aft end is
  machinery, not decks. Consistent with the Yellow rosette being drawn as a cog rather than
  concentric rings.
- Extracted — **radiator mounting, new detail relevant to C-007:** in the side view the three
  upper and three lower blades are not attached to the hull. They stand off a **long horizontal
  spar/rail running fore-aft**, each on a **short root fitting**, and the spar itself carries a
  row of dark slots. Blades are **tapered lozenges, wide at mid-height and narrowing at both
  root and tip**, with a **segmented blue panel face inside a pale structural border and a cap
  at the tip**. Pitch between blades is close to one blade width.
- Extracted — **cargo modules:** six dark-red rectangular modules are countable along the dorsal
  line of the mid-section in the top view, sitting on a continuous **raised dorsal rail** with
  small grey plinths between them. Six, not "5–6".
- Extracted — **fore section, previously "unmodelled swept structures":** in the side view the
  forward assembly reads as a *stack*, aft to fore: large panelled cylinder with **vertical
  fluting at its aft shoulder** → barrel drum → narrow waist crossed by **red structural
  members** → rounded terminal dome → **deflector spike**. The "swept structures" of the top
  view are a **flat plate-like communications array carried above the forward hull on a short
  pylon**, extending forward as a thin blade — it is a plane, not a wing pair.
- Feeds: `station/schema/station.yaml` components block; `canon/CONFLICTS.md` C-004, C-007
- Conflicts: none new; strengthens C-007's ruling (the spar mounting is only buildable coplanar)

### 01-station-exterior/view.jpg
- Source authority: **1** (on-screen footage, S2E22)
- **Byte-identical duplicate of `03-sector-blue/Babylon_5_2-22_34b.jpg`** (md5 e2bf2216d5 for
  both, 1014×576). Confirmed this pass. See that entry, which was extended below with
  measurements. Misfiled: it is an interior, not an exterior.
- Feeds: nothing of its own.

### 01-station-exterior/Cobra Bays with starfurries.webp
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, CGI). 843×474.
- Extracted, added this pass:
  - The launch arm is a **triangulated open lattice truss with a pentagonal cradle ring** at its
    outboard end, hinged at a heavy root block — the fighter is held **nose-out in the ring**,
    clear of structure on all sides. Three further arms are visible at other angles, so the
    bays are **arrayed around a curved face** and the arms swing rather than translate.
  - The framing columns are **rectangular-section box columns with a heavy chamfer**, carrying
    **red beacons at their heads** and **amber/white marker lights in vertical files** down
    their inner faces.
  - **Orange-and-white banded cylindrical tanks** are racked in pairs against the right-hand
    column, behind a chevron-striped kerb — consumables storage at the bay face.
  - Deck edges are **yellow/black chevrons on every nosing**, and there are at least three
    stepped deck levels within the bay volume.
- Feeds: `cobra_bay` component
- Conflicts: no bay count is legible in frame, so this does **not** bear on C-002.

### 01-station-exterior/sleeping-in-light-05.jpg
**Supplements the session-2q entry above; era caveat there still applies (S5, abandoned).**
- Source authority: **1** (on-screen footage, S5). 1024×576. Misfiled — an interior.
- Extracted, added this pass:
  - **Overhead framing is a repeating portal truss** — an inverted-U of paired chords with
    diagonal webbing — at a regular pitch; **five frames are countable** before the run goes
    dark. There is no ceiling plane at all: pipes and cable runs pass over the top chord.
  - The deck either side of the light strip is **three courses of large recessed panels with
    raised borders**, panels roughly 1.5 long to 1 wide, laid in a running bond.
  - **Vertical white light bars** on the wall pilasters: four countable on the right wall, two
    on the left, at a pitch matching the truss frames. They run from about waist height to the
    top of the wall — they are bars, not the short segmented strips of `grey level 1.webp`.
  - Right-hand equipment bank, itemised: a **blue backlit display with vertical bar-graph
    columns**, **two circular analogue gauges** stacked, a **rack of black rectangular modules**
    in a 3×5-ish grid, and a pale blank panel. This is the "equipment wall" kit piece.
  - **There is no figure in frame, so this image supplies no scale anchor.** The corridor reads
    as street-width but that is an impression, not a measurement. Do not size Downbelow from it.
- Feeds: `docs/interior-kit-spec.md`; Brown Sector

### 01-station-exterior/welcome to babylon 5.webp
**Supplements the session-2q entry above; the transcription there is correct and was
re-verified this pass at 1000×750.**
- Source authority: **1** (on-screen footage, customs hall). Misfiled — signage.
- Extracted, added this pass — **the typography is two faces, not one**:
  - "Welcome to / Babylon 5" is set in a **rounded-terminal humanist sans, mixed case**, warm
    and civic. The body copy and all sub-headings are a **condensed oblique grotesque, all
    caps**. The two do not mix within a block.
  - Panel construction: **double keyline border** (outer frame plus inner frame); **four thin
    horizontal rules** separating the title block from the body; area name in a
    **rounded-rectangle pill outline**, centred; headings **underlined**; body copy centred and
    ragged on both sides.
  - The station is written **"B-5"** in body copy, hyphenated, while the title uses
    "Babylon 5". Both forms are canon.
  - Setting: the boards are **backlit blue panels tilted off a dark structural fascia**, under a
    soffit carrying a **white horizontal louvre grille**, with a red-lit volume behind.
- **Bearing on C-003:** this is the only on-screen *wayfinding* sign in these three folders, and
  C-003's stated resolution need is "on-screen wayfinding signage". It names an area
  ("CUSTOMS SECTOR") but gives **no adjacency, no ordering and no colour sector**, so it does
  not advance C-003. Recorded so a future session does not re-check it hoping otherwise.
- Feeds: `16-signage-typography-ui`; `station/npc/schedule.py` (EMT)

---

## 03 — Sector Blue

### 03-sector-blue/Babylon_5_2-22_34b.jpg  ·  (= 01-station-exterior/view.jpg)
**Supplements the session-2q entry above with measurements. The qualitative reading there is
confirmed; what follows is new and quantitative.**
- Source authority: **1** (on-screen footage, S2E22). 1014×576.
- **Measured, drum end cap.** Six of the blue rim lights were located, converted to source
  pixels and fitted with an algebraic circle:
  - fitted centre **(934.7, 165.9) px**, fitted radius **R = 371.6 px**, radial residuals
    **all under 0.9 px** — the arc is a very clean circle over the 37° sampled.
  - the lights sit at a mean angular pitch of **7.40°**, individual deltas 7.09–7.59°.
    Because the disc is seen obliquely the fitted centre is slightly displaced, which biases
    the pitch; the honest figure is **7.4° ± 0.3°, i.e. 46–50 lights around the full
    circumference, most plausibly 48** (48 → exactly 7.5° and is a natural modelling division).
  - **This is the first hard count anyone has taken off this frame.**
- **Measured, concentric band structure.** A radial intensity profile about the fitted centre,
  averaged over 103°–146°, puts dark circumferential ribs at normalised radius
  **r/R ≈ 0.25, 0.28, 0.32, 0.51, 0.71, 0.80, 0.98 and 1.03**, with bright band centres at
  **0.21, 0.36, 0.62, 0.75 and 0.84**. That is **eight or nine concentric annular courses**
  between r/R 0.2 and the rim, outboard of a **dished, radially ribbed hub cone** occupying the
  inner ~20% of the radius.
  - **These are panelling courses on a bulkhead, not proven decks.** Angular averaging across an
    obliquely viewed disc smears the profile, and the index already records that level count and
    deck count need not be equal. See the note appended to C-004: this **corroborates and
    quantifies** the radial reading; it does not resolve it.
- Extracted, added qualitatively:
  - The plates within each course are **roughly square** — radial depth ≈ circumferential width
    — so the end cap is a grid, not a set of thin rings. Two of the courses are
    **checker-plated** in alternating light and dark squares; the rest are plain.
  - The rim band carrying the blue lights is the **outermost** element and is **dark**, with the
    lights recessed into it as small rectangles.
  - The axial truss's **serrated lower edge (the rack)** and the **cylindrical illuminator
    tubes** slung below it are both confirmed at higher magnification; the tubes are bright
    enough to clip.
  - The near drum wall (left of frame) shows the same language: **courses of pale plates with a
    dark recessed channel**, and a **recessed rectangular panel containing two parallel blue
    illuminated bars** — the blue light is a *fitting in a panel*, not a continuous strip.
  - The drum's landscape is **arable** — hedged fields, tracks, a wooded belt.
- Feeds: `canon/CONFLICTS.md` C-004 (see appended note); drum end-cap geometry;
  `station/physics/core_shuttle.py`

### 03-sector-blue/Babylon_5_2-22_33a.jpg
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, S2E22). 1001×576.
- Extracted, added this pass:
  - **Two structurally different end caps exist.** 34b's is a **panelled grey disc of concentric
    courses**; this frame's far end is a **deep red-orange open lattice of triangulated bays**.
    Either the drum's two ends are built differently, or the red-orange is a conical inner
    structure inboard of the panelled cap. **Flagged, not resolved** — it changes what the drum
    generator has to emit at each end.
  - The axial truss carries, on its underside, a **row of large bright rectangular light boxes**
    at regular pitch, plus **small white point lights** between them. The illuminators are
    **discrete fittings in a row**, not a continuous tube.
  - **Core shuttle car, described properly for the first time:** a **maroon/red roof and skirt
    with a white body band**, a **dark continuous window band**, a **rounded nose**, and small
    square panels on the underside. It hangs from a **short bogie hanger** with visible
    articulation. Matches the red-maroon interior of `35a` — one vehicle, inside and out.
  - **The spoke tube's structure changes along its length:** a smooth pale cylinder for most of
    its run, interrupted by **two collar groups of six to eight fine coloured rings**
    (red/orange/green/white micro-stripes) at segment joints, then, near the drum wall, an
    **open black square-lattice section** ending in a **pale ring collar** at the wall. The tube
    is not uniform and should not be generated as one extrusion.
  - The hub plate where the tube leaves the axis is a **grey polygonal casting with
    rounded-rectangle recessed panels, a dark oval port, and gold/brass collar rings** at the
    tube joint.
  - The drum floor here is **not agricultural** — it is a **dense settlement grid** with a
    **broad road carrying a dashed white centre line** running circumferentially, and a large
    **red-brown leaf-shaped feature** (lake or pad). The drum floor has at least two distinct
    land uses.
- Feeds: transport-tube and core-shuttle geometry; drum floor land-use zoning

### 03-sector-blue/Babylon_5_2-22_35a.jpg  ·  (= 02-station-cutaways-and-plans/inside.jpg)
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, S2E22). 1001×576. Era: S2, in era.
- Extracted, added this pass:
  - **Seating layout, which the earlier entry only gestured at:** a **pair of transverse
    forward-facing seats** on a moulded plinth, and a **longitudinal bench** along the side wall
    — two arrangements in one car. Cushions are **separate seat and back squabs in red-maroon**
    on **pale grey moulded bases** with **rectangular recessed voids** beneath (footwell or
    stowage).
  - **Amber panels counted: four along the right-hand bench plinth and one on the left**, evenly
    spaced, each a wide rectangle with a bright yellow face flush in the plinth. They are set
    **below seat level**, which is why they read as floor-wash rather than as signage.
  - Windows are **large squares with generously rounded corners**, separated by grey mullions,
    with a **continuous red band at the window head** running the length of the car and around
    the ceiling ribs.
  - Ceiling is **transverse arched ribs** with the same red banding — the car's shell is a
    barrel, matching the tube it runs in.
  - Through the raked windscreen, the tube reads as **red structural ribs receding to a
    vanishing point** with a **dark triangular keel structure overhead** — the running rail.
  - Two **polished vertical grab poles**, floor to ceiling, at roughly one seat-bay pitch.
- Feeds: interior kit (transit car); `station/physics/core_shuttle.py` presentation

### 03-sector-blue/Babylon_5_2-22_29a.jpg  ·  **misfiled — this is the Garden, not Blue Sector**
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, S2E22). 1001×576.
- Extracted, added this pass:
  - **Four to five tall orange-vermilion tapered cones** stand on the upper terrace — slender,
    ground-mounted, of decreasing height. They are the strongest colour accent in the frame and
    are a repeating civic element, not a one-off canopy.
  - The **surface transit vehicle** at upper right is **green with a cream band**, running on an
    **elevated guideway behind a railing** at terrace level — so the drum has **street-level
    rail transit** in addition to the axial shuttle and the radial spokes. Third transport mode.
  - A **grey streamlined pod** sits at mid-right carrying **three vertical illuminated slots**
    on its flank — a kiosk or a parked vehicle; either way a repeating lit-slot motif.
  - The tunnel portal is a **segmented barrel-vault mouth with dark grille gates**, set into a
    planted bank — the drum's ground level is **cut and covered**, not flat.
  - Terracing is retained by **horizontal red-brown timber-slat walls**; paths are **small setts
    laid in fan courses**; the cascade is **lit blue from within**.
  - Behind: a **long glazed multi-storey building with a continuous window band and a flat
    roof**, and mature broadleaf trees overhanging the frame.
- Should be moved to `09-garden-core-and-transit/`.

### 03-sector-blue/comand and contorl.webp
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage). 814×610.
- Extracted, added this pass:
  - **The window is not a plain circle.** It is a **circular light divided by radial spoke
    mullions into trapezoidal panes**, with a **concentric ring rib at roughly 0.75 radius**,
    and a **large inverted-U (horseshoe) mullion** springing inside the ring — so the glazing
    reads as a rose window with an arch inside it, not as a wheel.
  - A **file of small circular studs follows the ring rib** on the right-hand side — rivet or
    lamp detail on the ring, at close pitch.
  - The surrounding bulkhead is a **flat white-grey panelled frame with heavy diagonal braces**
    forming a hexagonal outline around the circle, and carries **two plain circular discs**
    (blanked ports) at upper left and upper right, one each side.
  - Beyond the glass: **haze, and a dark gantry-like structure**, not open starfield.
  - **Three console desks** in a shallow arc, each a **wedge with a warm-lit control face above
    and a cyan-lit glass fascia below**, carried on **slim tubular legs with cross-bracing**
    clear of the deck.
  - **Three occupied levels are visible in one volume**: the raised circular dais, the deck
    around it, and a lower level reached by the stair at right — the "two levels in one volume"
    motif recorded elsewhere is here a three-level section.
- Feeds: interior kit (C&C set); `domes` component cross-check

### 03-sector-blue/dock.webp
**Supplements the session-2q entry above, and adds the scale number that entry asked for.**
- Source authority: **1** (on-screen footage, CGI). 1000×750.
- **Measured scale anchor.** The file of dock workers crossing the deck is **eleven figures**.
  A figure stands **≈29 px** tall in the source; the red deck disc measures **≈156 px** across
  its horizontal (major) axis. At 1.75 m per figure that makes the **red disc ≈ 9.4 m across**,
  and since the disc is foreshortened this is a **lower bound** — call it **9–11 m**. Deck
  markings at this scale are the right way to size the bay, and they are far larger than a
  hangar-floor intuition suggests.
- Extracted, added this pass:
  - The disc's device is a **white rounded-rectangle outline containing three white bars**, not
    an oval emblem.
  - A **signage pylon** stands at the deck edge carrying **four rectangular plaques in a
    horizontal row** at head height, with a **green-lit display panel** on its lower flank. A
    dock worker beside it gives the height. Signage on this deck comes in **fours**.
  - Starfury fin markings are **pale numerals inside a warm tan/orange circular roundel**
    ("29" legible), roundel diameter ≈ 2.5× the numeral height.
  - Overhead: **red-orange box girders** with a lattice gantry carrying **five to six pendant
    floodlights** at even pitch; the light is entirely top-down and hard.
  - A row of roughly twenty **small white bollards** runs along the bay edge beyond the ramp.
  - The bay mouth is a **very wide, very low flat-topped slot** with more parked craft and haze
    beyond — the volume is a long slot, and the "far side" is another parking apron, not a wall.
- Feeds: docking bay interior kit; NPC dock-worker population; deck-marking scale

### 03-sector-blue/Minbari Flyer 969 in docking bay 17.webp
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, CGI). 1000×563.
- Extracted, added this pass:
  - The bay wall is a **stepped ziggurat of ledges**, and **every step nosing carries yellow/
    black hazard chevrons** — the chevron is applied by rule to all step edges, which makes it a
    generator rule rather than a decal placement.
  - The **bay ceiling is the ribbed inner wall of the rotating drum**, curving across the top
    left of frame with **deep circumferential ribs** — the bay is cut into the drum, so bay
    geometry and drum geometry must come from the same schema surface.
  - **Two crew figures are visible on the upper gantry**, giving the only scale in frame: the
    Minbari flyer spans most of the bay width and dwarfs them.
  - A **red warning beacon** at high level right; **blue-white deck lighting** in strips; service
    gantries with plain tubular railings.
  - **No bay number is legible in frame.** The "17" is from the filename, i.e. the uploader's
    caption, not a reading. The index previously treated bay 17 as established from this file
    and used it to cross-check "DOCKING BAYS (24)". **That cross-check rests on a filename, not
    on the image.** Recording the correction; it does not change C-002, which was already open.
- Feeds: docking bay kit; `canon/00-MASTER.md` counts (with the caveat above)

### 03-sector-blue/war room.webp
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage, S3+; late end of the S2–3 lock). 1000×556.
- Extracted, added this pass:
  - **The red overlay on the galactic map is not a regular grid.** It is a set of **irregular
    quadrilateral cells of varying size** whose edges follow the galaxy's curvature — a
    **territory partition**, not a coordinate mesh. Roughly 20–25 cells are visible. Several
    cells carry **small yellow highlighted patches** and yellow micro-labels.
  - The galaxy itself is painted: **bright elliptical core, blue-white spiral arms, dark dust
    lanes**, on a deep blue field. It is a **backlit mural**, not a screen.
  - The console rail carries a **row of about ten vertical white light bars** at close even
    pitch along its inner face.
  - An **alphanumeric readout** sits on the console at right: a **blue text block** beside a
    **boxed three-glyph pale numeric display**. **Illegible even at 10×** — do not transcribe it;
    a future session should not spend time on it.
  - The arch at left is the **chamfered structural language of the corridors at room scale** —
    a broad flat arch with a stepped soffit — against a **dark grid wall** with a slim vertical
    white light ladder.
- Feeds: `16-signage-typography-ui` (territory-map graphic language)

---

## 04 — Sector Red

### 04-sector-red/more zocalo.png
**Supplements the session-2q entry above and independently confirms its central correction.**
- Source authority: **1** (on-screen footage). 1440×1080, the best frame in the folder.
- **Confirmed independently this pass:** the neon **reads "Zocalo" in Latin letterforms** —
  Z, o, c, a, l, o, in a **rounded single-stroke tube script**, with a **dot inside the counter
  of each 'o'**, a **swashed Z**, and a **triangular counter in the 'a'**. Here it is
  **orange-red on a black backing plate**, hung from the underside of the upper gallery deck.
  - **And the cyan sign in `zocalo.webp` is the same wordmark, not a second design.** Glyph for
    glyph the two match; the cyan one is simply seen at an oblique angle, which is what made it
    look like alien script. **One sign, two colour states or two installations of one design.**
    The session-2q correction is therefore right, and this pass corroborates it from the image
    rather than accepting it.
- Extracted, added this pass:
  - **The "5" furniture decal, described precisely:** a **bold slab numeral with a black
    outer keyline and a white inline**, i.e. an outlined-and-inlined varsity 5, applied large on
    **cream drum panels** forming chair backs and table pedestals. One decal asset, three
    applications (patch, floor inlay, furniture).
  - Chairs are **black tubular hoop backs on splayed black tubular legs** with the cream drum
    panel set inside the hoop. Tables are **round tops with a dark rim** on a **cream cylindrical
    pedestal with a dark base and a small circular port** near the foot.
  - The upper gallery is carried on **large tubular grey arch ribs** with cross-bracing; people
    stand at a **vertical-bar balustrade** looking down. Beneath the gallery runs a strip of
    **shopfronts with blue and red backlit panels**.
  - The stall canopy at centre-right is **fabric on radiating tan spars, parasol-fashion**, on a
    single mast.
  - Deck is **large pale square tiles on a darker grout grid**, about six to seven tiles across
    the visible foreground, with a **band of yellow/red/blue diagonal chevron striping** at right.
  - Tableware: a **chrome domed-top shaker** and **stacked chrome tumblers**.
  - A **large pale circular sign disc on a thin post** stands at the upper right carrying dark
    glyphs and a circular emblem — **cropped and illegible**; not worth re-examining.
- Feeds: `docs/interior-kit-spec.md`; Red Sector fit-out; `16-signage-typography-ui`

### 04-sector-red/zocalo.webp
**Replaces the "Still uncatalogued" line for this file and applies the correction the index
asked for.**
- Source authority: **1** (on-screen footage). 985×576.
- Era caveat unchanged: **Season 1 EarthForce uniforms** (grey/tan with the gold sunburst) — the
  set is valid architectural reference, the costumes are out of era.
- **Correction applied.** The neon over the stall is the **"Zocalo" wordmark in cyan**, not alien
  script. Verified glyph-for-glyph against `more zocalo.png` at 9× this pass. The earlier
  "alien script" reading came from the oblique viewing angle.
- Extracted, added this pass:
  - The stall beneath the sign is a **rectangular post-and-beam frame hung with strings of small
    warm fairy lights** along every member — the string lighting is *structural decoration on
    the stall frame*, not ambient dressing.
  - A **hanging fabric banner in maroon with red-orange alien characters** flanks the stall.
  - **Real vegetation in planters**: a mass of **orange-red autumn foliage** at mid-right, tall
    enough to read as a small tree. The Zocalo has live planting.
  - A **blue display screen showing a scattered particle/starfield graphic** is set into the
    stall back.
  - A **red-orange tubular handrail on plain stanchions** runs down the right-hand side — the
    recurring accent, here as a barrier along a change of level.
  - Wall treatment behind: **grey panelled cladding with a dark square-mesh grille panel** at
    high level; a **large dark chamfered arch** frames the top left.
  - Crowd is **dense and species-mixed** — Narn, humans, several bald humanoids, a robed alien.
- Feeds: Red Sector fit-out; `16-signage-typography-ui`; NPC density targets

### 04-sector-red/Casino.webp
**Supplements the session-2q entry above.**
- Source authority: **1** (on-screen footage). 814×610.
- Extracted, added this pass:
  - **The room's light comes from two large backlit grid panels**, one at each end of the mural,
    each a rectangle of bright square cells — plus a **white spherical pendant** and **vertical
    magenta neon strips** on the left wall. The mural itself is unlit; it reads by spill.
  - The **wheel of fortune** carries a **ring of about twenty-four filament lamps** around its
    rim, with a **cyan and dark-blue petal face** inside. It is **wall-mounted**, not free-standing.
  - The gaming table is a **blue-felt kidney** with a **padded red-brown rail**, set on a
    **raised plinth with a kerb** — a step up, which is a floor-level change to model.
  - A **long green-illuminated counter** runs horizontally across the full width behind the
    crowd at waist height — the bar, and the strongest horizontal in the composition.
  - Foreground tables are **pale wedge-shaped tops**; chairs are dark with **round black bases**.
  - The mural's subject is machinery, retorts, pipework and labouring figures in monochrome —
    an **industrial allegory**, and the single largest flat art surface anywhere in the set.
- Corroborates `other map.png`'s Red rosette, which names both Casino and Dark Star.
- Feeds: Red Sector fit-out; NPC density

### 04-sector-red/Darkstar_logo.webp  ·  **not previously catalogued**
- Source authority: **1** (on-screen footage). Only **240×160** — the smallest file in the three
  folders, and exactly the sort of file the brief warns against skipping. It is legible at 8×
  and it is a **named-venue sign**, which makes it worth more than its pixel count.
- Depicts: the **"DARK STAR"** venue sign.
- Extracted:
  - The wordmark is **"DARK"** + a **sunburst glyph substituting for the S** + **"TAR"**, so the
    sun *is* the S. Letterforms are **irregular, hand-drawn, splayed angular caps** with pointed
    apexes and flared strokes — deliberately crude, nothing like the Zocalo's smooth tube script
    or the customs boards' clean grotesque. **A third distinct typographic register in the
    station's signage.**
  - Colour: letters glow **acid green**; the sunburst is **warm amber/copper**. The sun has
    roughly **twelve principal rays with shorter rays between them**, around a solid disc.
  - The sign sits on a **dark lens-shaped (vesica/almond) plaque** applied to a **grey-green
    wall**, with **bamboo-like foliage flanking it on both sides** — the venue entrance is
    planted, which places it in or beside a landscaped area.
- **Bearing on C-003:** "Dark Star" is named in the **Red rosette** of `other map.png`
  (authority 3). This is the on-screen article, and it is the fourth Red-rosette facility for
  which we now hold authority-1 footage (with Zocalo, Earharts and the Casino). See the note
  appended to C-003 — the tie is real but weaker than it looks, and the note says why.
- Feeds: `16-signage-typography-ui`; Red Sector venues

### 04-sector-red/Doug's Dugout.webp  ·  **not previously catalogued**
- Source authority: **1** (on-screen footage). 1000×557. The name is the uploader's caption; no
  sign in frame gives it, so treat the venue name as unsourced.
- Depicts: a dark bar/diner interior with two men eating at a table, crowd behind.
- Extracted — this is the best **small enclosed hospitality interior** in the set, and it is
  quite different in character from the Zocalo concourse:
  - **Lighting is by low pendant cones.** Large **shallow polished-metal cone shades on slim
    stems**, hung low over each table, with a bright rim and a hot pool beneath. Two are in
    frame. Ambient fill is near zero; the room is a field of separate table pools.
  - **Wall signage, left:** a **cyan neon glyph in the curvilinear single-stroke alien family**
    — the same family as the Zocalo wordmark and as row 3 of
    `11-props-and-technology/Vorlon, Narn,and  Centauri script examples.jpg` — mounted on a dark
    panel beside a **vertical cyan neon tube divided into four segments by three clamp bands**,
    with a small **blank cyan light box** below.
  - **Wall panel, centre:** a **large orange-red backlit matrix of small square cells** in a
    stepped irregular silhouette — a pixel-grid light wall, roughly twelve cells across.
  - **A standard twenty-segment Earth dartboard** hangs on the back wall, numbered ring legible.
    **Verification pass correction:** the numerals read **14, 11, 8, 16, 7** down the left,
    **19, 3, 17** across the bottom and **13, 6, 10, 15, 2** down the right — the original entry
    transcribed the second as "21", which is not a number that appears on a dartboard at all.
    The corrected reading is worth more than the original claim: 14-11-8-16-7 and 13-6-10-15-2
    are **exactly the real board's sequence**, so this is not a dartboard-like prop, it is a
    correctly laid out standard board. Ordinary human pub fittings persist on the station — a
    useful licence for prop selection.
  - An **amber alphanumeric display** below the dartboard shows "209" in orange digits with
    further characters above — a scoreboard or menu board.
  - **A backlit blue panel reads "ZIMA"** in white caps with a diagonal light streak. This is a
    **real-world 1990s product placement** (a Coors malt beverage). It is genuine on-screen
    content and is recorded as observed, but it is **third-party trade dress and must not be
    reproduced** in this project's signage — invent an in-universe brand in the same slot.
  - Table dressing: **round pale tops**; a **chrome cylinder with a glowing blue cap**; a **red
    conical sauce bottle**; **cut-glass tumblers**; plates of bread-and-filling food and salad;
    and a **spiky red alien fruit** on one plate. Mixed-species crowd, civilian dress with
    mandarin collars in olive, brown and grey.
- Feeds: Red Sector fit-out (enclosed venue kit); `16-signage-typography-ui`; prop set

### 04-sector-red/Earhart's.webp
**Supplements the session-2q entry above, and this is where the C-003 finding came from.**
- Source authority: **1** (on-screen footage, CGI). 720×408.
- **The finding.** Zoomed to 5×, the "sky" above and behind Earhart's is unambiguously the
  **inside of the rotating habitat drum**: olive and tan **hedged agricultural fields**, a broad
  **grey road**, and terrain **curving up on both sides and over the top of frame**; and across
  the top centre, **two splayed support struts banded with orange rings** meeting a hanging
  structure on the **axial spine**. Earhart's stands on the floor of the hollow drum, under the
  far side of the drum, with the axis visible. There is no ambiguity in this frame.
  - `other map.png` assigns **"Earharts" to the RED rosette**, which it draws as **concentric
    rings filled to the axis** — not hollow. `04-sector-red/Fresh air.webp` shows the **Fresh
    Air Restaurant** likewise open to the drum's far side, and that is named in the **GREEN**
    rosette. **Two facilities in the same hollow volume, assigned to two different rosettes.**
  - Written up under C-003. It **complicates** C-003 rather than advancing it.
- Extracted, added this pass:
  - The upper shell is a **shallow dome clad in large square tiles** carrying **six rectangular
    roof vents/hatches** countable across the crown.
  - The equatorial glazing is divided by **piers into roughly eight to nine bays**; bays alternate
    between **horizontal timber-slat screens (three slats)** and **cyan backlit panels**, with the
    bar and seated patrons visible through the clear bays.
  - The under-shell is a **deep unlit flare** down to a **single broad tapered pedestal with a
    flared foot** — the whole building is cantilevered off one column.
  - Bottom right of frame: **two large tan domed structures** at smaller apparent size, and a
    low **green-lit facade** bottom left — the drum floor is built up around it.
- Feeds: drum-interior architecture; Red Sector venues; `canon/CONFLICTS.md` C-003

### 04-sector-red/Fresh air.webp  ·  (duplicate, lower resolution)
- Source authority: **1** (on-screen footage). 1000×871.
- **Same frame as `11-props-and-technology/fresh air resturant signage with view.webp`
  (1200×1046), at lower resolution.** Not byte-identical; the 11-props copy is the better one
  and carries the full entry. Confirmed side by side this pass.
- Extracted here only what bears on the C-003 note:
  - **The ceiling is the far side of the drum** — a dark blue-green mottled expanse of terrain
    above the red service pipes, not a built soffit. The restaurant is an **open terrace inside
    the drum**, which is what its name says and what the frame shows.
  - The **red ceiling pipes carry about eight rectangular downlight fittings** at even pitch,
    plus one suspended white strip — the lighting is hung from services, in the open air.
  - **Four tall thin illuminated posts** stand in the middle distance like torchères.
  - A **second, smaller teal neon swoosh** repeats at mid-left, so the swoosh is a motif rather
    than part of the one sign.
- Feeds: `canon/CONFLICTS.md` C-003; Green Sector fit-out (via the 11-props copy)

---

## Corrections to the index made in this pass

1. **`Minbari Flyer 969 in docking bay 17.webp` does not show a bay number.** "17" is the
   filename. The index and C-002's session-2q note both treated it as an in-frame reading and
   used it to cross-check the Security Manual's "DOCKING BAYS (24)". The cross-check rests on
   a caption. C-002 was already OPEN; this does not change its status but the supporting
   argument is weaker than written.
2. **`exterior more.jpg` is a fan-assembled wallpaper containing production-model orthographic
   renders.** The geometry is authority 2; the sheet is not a production document. The earlier
   entry called the whole file authority 2 without qualification.
3. **The Zocalo neon correction is confirmed**, from the images, not by deference — and the
   cyan sign and the orange sign are established as **the same wordmark**, which the earlier
   entry left open ("two signs, or one sign in two states").

---

# Session 2s — folders 11, 16 and 13, exhaustive pass

Every file in `11-props-and-technology` (14), `16-signage-typography-ui` (3) and
`13-other-ships` (1) was opened and magnified. **Two files had no entry at all**
(`16-signage-typography-ui/earthforce logo.webp`, `13-other-ships/kosh's transport.webp`); they
are catalogued below for the first time. The other sixteen had entries, and are re-entered here
only where magnification **added a measurement, changed a claim, or corrected an error**. Three
corrections are load-bearing and are flagged **CORRECTION** in place.

**No quarantine candidates found.** Nothing in these three folders is cel-shaded (the 2023
animated film's signature) and nothing shows AI artefacting. Two files are clean vector
reconstructions (`earthforce logo.webp`, `babylon 5 shield.webp`) — those are fan-authored
derivative artwork, authority 4, but they are hand-drawn vector, not generated, and both hold up
under a flat-colour histogram (two and six exact flat colours respectively, with only
antialiasing between them).

---

## 11 — Props and technology (re-examined; the schematic was measured rather than described)

### 11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg  ·  **the wall schematic was measured; its value to C-004 goes DOWN, not up**
- Source authority: **1** (on-screen footage, arrival concourse / customs)
- Depicts: the arrival concourse. Left, a wall monitor showing a talking head; centre, the
  illuminated "WELCOME TO BABYLON 5" sign; right, a green vector wireframe of a station
  structure; overhead, two suspended information boards; beyond, the concourse and its crowd.
- **Extracted — the wireframe schematic, measured.** The frame is 1262×634 and the display
  occupies only ~320×190 px of it, so it was isolated on the green channel, median-filtered,
  autocontrasted and resampled 8× before any claim was made. Line positions were then taken from
  intensity profiles, not by eye:
  - **Silhouette:** a rounded/domed cap at the left; a deep, densely-gridded main body across the
    left two-thirds; then the section **steps shallower** and runs on to the right as a tapering
    tail; below the body, a **fan of four or five long straight members** sweeping down and to
    the left.
  - **Longitudinal lines, main body:** interior lines at a **regular 23 px pitch** (peaks at px
    rows 60, 83, 106 in the isolated crop), plus the top and bottom edges. **Three interior
    lines → four bands.**
  - **Longitudinal lines, shallow tail:** peaks at px rows 42, 56, 69, 84 and 93 — **five lines,
    spacing 14, 13, 15, 9 px**, converging as expected under perspective. **Four bands again.**
  - **Transverse lines:** peaks at px cols 40/49, 71/77, 92/98, 139/143, 153/157 — i.e. **paired
    lines ~6 px apart repeating at a ~21–23 px pitch**. The pairing reads as ribs drawn with
    thickness. **The transverse pitch and the longitudinal band depth are the same number
    (~23 px), so the structural grid this diagram shows is roughly isotropic — bay length equals
    deck depth.**
  - **CORRECTION, and it cuts against the current C-004 argument.** `canon/CONFLICTS.md` C-004
    evidence item 2 cites this display as "multiple parallel longitudinal lines … reads as decks
    stacked radially", and calls it weak because the lines "cannot be counted". **They can now be
    counted, and there are four bands.** Four bands cannot be four decks in a station that
    addresses `Grey 17`. So either the lines are hull plating and frames rather than decks, or
    the diagram shows only top-level structural divisions. Either way this frame **stops being
    evidence for radial decking**. Written into `canon/CONFLICTS.md` under C-004.
- Extracted — the sign, which is the best-preserved public-signage artefact in the set:
  - **"WELCOME TO"** — pale cream **serif** capitals, high stroke contrast (Didone/Bodoni class),
    generously letterspaced, on black.
  - **"BABYLON 5"** — **white serif capitals on a solid saturated royal-blue bar** that is inset
    from the sign edges and runs its full width. Same serif class, larger.
  - A **thin olive/dark-yellow horizontal rule** separates the title block from the notice.
  - Notice, verbatim: **`REMEMBER` / `Smoking permitted in` / `designated areas only`** — three
    centred lines in a **bold yellow sans**, `REMEMBER` letterspaced on its own line.
  - The whole panel carries a **thin pale-green keyline** inset from the black field, running
    down the left, across the bottom and up the right — **three-sided, open at the top**.
- Extracted — the display hardware, which is a reusable kit part:
  - Both large wall displays share one bezel: a **rounded-corner rectangle with a thin
    bright white-cyan edge-light**, and both are **canted out from the wall** rather than flush.
  - The left display shows a **talking head on a flat teal ground** — a broadcast, not a readout.
    A smaller adjacent panel shows a **landscape photograph with a pale sky**.
- Extracted — overhead: **two ceiling-suspended flat boards, canted down toward the concourse**,
  carrying **amber-and-green text in a multi-column tabular grid**. These read unambiguously as
  arrivals/departures boards. First sighting of that fixture type in the set.
- Extracted — mid-ground: a **long horizontal backlit strip sign reading "WELCOME TO BABYLON…"**
  in pale letterspaced sans caps, mounted high on a **warm brown panelled wall** whose panels are
  a coarse horizontal grid. A second small plaque sits over the far doorway; at 16× it is
  **four short words and a numeral and it does not resolve** — do not transcribe it.
- Extracted — structure: a **dark steel gantry with diagonal bracing** crosses the foreground in
  front of the displays, and heavy **cylindrical bollard-like masses** stand either side.
- Feeds: `canon/CONFLICTS.md` C-004 (now as a *retraction* of evidence item 2);
  `16-signage-typography-ui`; `docs/interior-kit-spec.md` display-bezel and signage families
- Conflicts: **weakens** C-004 evidence item 2. Bears on nothing else.

### 11-props-and-technology/identicard readout.webp  ·  **re-examined; the "barred zero" claim is wrong, and the layout grid is now measurable**
- Source authority: **1** (on-screen footage)
- Depicts: an identicard database record filling the screen. 800×600.
- Extracted — **CORRECTION to the existing entry.** The earlier entry says the typeface has a
  **"barred zero"**. At 4× the zeros in `HUMAN/02`, `12/10/25` and `NO DISTG` are all **plain
  squared ovals with no bar, no slash and no dot**. Struck.
- Extracted — the typeface, now identifiable: a **squared-oval grotesque of the
  Eurostile/Microgramma family**. Diagnostics visible at 4×: `O` and `0` are **rectangles with
  large corner radii**; `S` has **flat horizontal terminals**; `G` carries a **horizontal bar on
  a vertical stem**; `M`'s vertex descends only part-way; `2` is **flat-topped with a straight
  diagonal and a flat foot**. Labels are set in the **bold** weight, values in the **regular**.
- Extracted — **the record panel is laid out on a measurable grid.** The white field carries a
  fine graph rule at **17 px horizontal pitch and ~15–16 px vertical pitch** on the 800×600
  capture — near-square cells, about **19 columns across the record panel and ~37 rows down**.
  Type baselines sit on grid lines. This is enough to author the UI on the same module rather
  than eyeballing it.
- Extracted — the red rows (`PHYS CHR`, `LICENSED PSI`, `VISAS`) are not merely red: they are set
  in a **visibly lighter stroke weight than the black labels**, so they read as inactive or
  header rows, not as data.
- Extracted — the portrait sits in a **pale grey-lavender frame with a 1 px black inner margin**;
  its content is a **blue-violet duotone**; and a **white-on-black alphanumeric code of eight or
  nine characters** sits top-left inside the portrait. At 8× it does not resolve. Do not
  transcribe it.
- Extracted — the scroll control is a **solid black left-pointing triangle** butted against the
  right edge of the grid field, vertically centred, and it **sits on a grid line**.
- Feeds: `station/npc/` record model; `16-signage-typography-ui` UI grid and type spec
- Conflicts: none. The `DES/ATMOS: HUMAN/02` finding in the earlier entry stands unchanged.

### 11-props-and-technology/Identicard reader.webp and Identicard inserted into reader.webp  ·  **re-examined; the indicator description was wrong**
- Source authority: **1** (on-screen footage). Both 800×451; same prop, card out and card in.
- Extracted — **CORRECTION.** The earlier entry describes "a vertical stack of **three amber
  indicator lenses** carrying icon glyphs". At 8× it is **one tall rounded-rectangle backlit
  window glowing red-orange, containing exactly TWO black icon glyphs** — one near the top, one
  near the bottom, with an unlit red gap between them. The third element counted was the
  **separate pale grey-white rounded-square button** below and left of the window, which is not a
  lens and is not lit.
- Extracted — the glyphs are **blocky abstract ideograms**, each an irregular filled polygon
  inside a squared black field. Neither is a Latin letter.
- Extracted — body: **matte mid-grey plastic**, top-left corner **chamfered at 45°**. Right of the
  button, **three horizontal moulded slots** in a stepped arrangement. Between the indicator
  window and the screen, a **narrow vertical slot** — the card throat. The screen is portrait
  format in a recessed bezel and shows a **salmon-pink ground with dark red two-column text**.
- Extracted — the identicard face, magnified 8×: not a flat pattern but **an array of round
  hemispherical beads in staggered (hex-packed) rows**, iridescent blue-green-violet, roughly
  **8–9 beads across and 9–10 rows**. The bead field is recessed inside a **maroon inner border**
  and a **gold/brass outer frame**. "Honeycomb matrix" in the earlier entry is right in spirit;
  the beads are domed, not cells.
- Feeds: prop set; security/customs NPC behaviour
- Conflicts: none.

### 11-props-and-technology/credit chit.jpg  ·  **re-examined; proportions and reader form added**
- Source authority: **1** (on-screen footage; watermarked `yourprops.com/user/docholl`)
- Depicts: a credit chit inserted into a counter-top reader.
- Extracted: the chit is a **tall narrow plate, about 2.4 : 1 portrait**, in dull brushed metal,
  with a **plain flat margin strip down its left edge** and a **rebate down its right**. The
  engraved field carries, top to bottom, a **circular boss**, a plain band, an **S-scroll wave**,
  then further banding — a stacked vertical ornament, not a scatter pattern.
- Extracted: the reader is a **black wedge plinth with a chamfered top face**, the slot cut in
  that sloping top, and a **short vertical red LED bar low on the front face, right of centre**.
  A separate **pale grey cylindrical post with a flanged cap** stands immediately to its right on
  the same counter. Counter top is **brushed metal**; background lighting is magenta-violet.
- Feeds: prop set; commerce interactions
- Conflicts: none.

### 11-props-and-technology/communicator link.jpg  ·  **re-examined; the cuff does not hold the plate, and the paperwork is a graphic system**
- Source authority: **1** (on-screen footage, S1E16 "Eyes" — subtitle title card in frame)
- Depicts: the link worn on the back of the hand, over a desk of documents.
- Extracted — **CORRECTION.** The earlier entry says the plate is "**held by** a wide brown
  leather wrist cuff". At 12× the plate sits **directly on the skin over the metacarpals** and the
  leather cuff is a **separate item further back at the wrist that does not reach it**. They are
  two objects, not one assembly.
- Extracted — the plate: **matte silver-grey**, roughly square with a **raised stepped lip along
  its near edge**, and **two small bright round studs at diagonally opposite corners**. It carries
  a **dark inset device of angular strokes, bilaterally symmetric about a diagonal**, filling the
  outer two-thirds of the face. The "winged chevron" reading is at the edge of legibility here —
  it is consistent with the EarthForce mark but not independently readable from this frame.
- Extracted — the paperwork, and this is a reusable graphic system: sheets carry **broad solid
  colour block bars in black, blue, magenta and yellow ranged along the head of the sheet**, over
  a body of **fine grey linework**. A separate glossy plate shows a **rust-ochre planetary
  surface with dark crater features**, overprinted with **white vector callout lines, small ring
  symbols and white label strips**. Desk top is **pale grey matte**.
- **Era caveat: S1.** The wide leather cuff is the Season 1 mount. The plate persists into S2–3.
- Feeds: prop set; EarthForce printed-matter graphic language
- Conflicts: none.

### 11-props-and-technology/Vorlon, Narn,and  Centauri script examples.jpg  ·  **re-examined; the three scripts are now specified well enough to generate from**
<!-- filename is verbatim: "Narn,and" has no space, and there are two spaces before "Centauri" -->
- Source authority: **1** for the three inset screencaps; **4** for the transcribed alphabets
  beside them (a fan compilation). Only 480×307 — magnified 6× per row.
- Depicts: three writing systems, each as an in-situ screencap (left column) plus a transcribed
  sample (right).
- Extracted — **row 1, gold on black (filename: Vorlon).** A closed kit of four primitives:
  (a) **tapering crescent hooks**, thick-to-thin sickles in several rotations; (b) **small square
  dots** set in columns of two or three and in 2×2 clusters; (c) **larger filled discs**, used
  sparingly; (d) **straight tapered flame strokes** — four of them, each with a dot beneath,
  close line 1 like a terminal group. A "word" is a dot cluster plus one or two crescents. Three
  lines, roughly 7 / 8 / 8 groups. Rendered warm gold with a metallic top-to-bottom gradient.
- Extracted — **row 2, tan on black (filename: Narn).** **Strictly rectilinear and monoline** —
  no curve anywhere, one constant stroke weight, square end caps, strict cap-height and baseline.
  It is built on a **unit-square module grid**, which makes it the easiest of the three to
  generate procedurally. Recurrent primitives: a **bracket/staple (⊐, ⊔)**, a **stepped Z**, a
  **square O with a centred dot**, a **stack of three or four parallel horizontal bars**, a
  **comb of three verticals**. A **single small square dot inside an enclosure** recurs as a
  consistent diacritic. Four lines.
- Extracted — **row 3, blue on black (filename: Centauri).** Curvilinear and **calligraphically
  modulated** — thick at the bend, tapering at the terminals. Primitives: a **broad C opening
  right**, a **fishhook J**, a **spiral/eye (circle with an inward hook)**, a **tilde with a dot
  beneath**, a **bracket enclosing a dot**. Three lines of about nine groups.
  **Caution:** these glyphs are drawn with a **bevelled chrome 3-D treatment** — highlight above,
  shadow below. That is the transcriber's rendering, a period graphics-program effect, **not**
  evidence that the show's letterforms are extruded. Generate them flat.
- Extracted — the left column screencaps, which establish that alien paperwork is its own prop
  category with distinct stocks:
  1. **Green:** dark script on a **curved mid-green casing** with lighter highlights.
  2. **Narn:** dark impressed script in a block at the lower-left of a **pale pinkish-tan
     leathery sheet** with coarse dark veining across it.
  3. **Centauri:** a **pale blue-white printed document with a photograph of a face**, dense blue
     script in paragraph blocks and a boxed inset of larger glyphs — an identity document —
     lying on **magenta and lilac sheets**.
- Filename assigns the rows Vorlon / Narn / Centauri in order; recorded as the uploader's
  attribution, not as a reading.
- Feeds: `16-signage-typography-ui`; procedural alien signage; alien printed matter
- Conflicts: none.

### 11-props-and-technology/Zocalo neon signage in background.jpg  ·  **re-examined; the "chevron flourish" is not a chevron**
- Source authority: **1** (on-screen footage). 1024×576.
- Depicts: the Zocalo concourse seen over a bar counter, three diners in the foreground.
- Extracted — **CORRECTION.** The earlier entry describes "a **zigzag chevron** neon flourish
  either side" of the wordmark. At 6× the flanking element is a **band of straight parallel raked
  blades** — eight or nine of them each side, dark teal, hung from a common top rail on the
  lintel beam and all leaning the same way. It is a fin/louvre band, not a zigzag, and it is
  **unlit** (dark), not neon. Corrected.
- Extracted — the flanking architecture, at 6×: a **parapet of square open frames with rounded-
  corner apertures, each crossed by a single diagonal brace**, with a **small round boss at each
  junction on the lower rail**; below it, a **two-tier close-set vertical-slat screen** over a
  pale lilac backlit ground. Four full frames legible in the crop. This is a strong, repeatable
  Red Sector motif and nothing else in the set shows it this clearly.
- Extracted: the bar counter is **black and glossy**, with a **red-orange edge rail along its far
  side** — the recurring red-orange accent, here as counter trim. Flanking the portal are **pale
  fluted cylindrical columns**. A shopfront at the left is signed **"…STORE"** over a display case.
- Feeds: Red Sector fit-out; `docs/interior-kit-spec.md` balustrade family
- Conflicts: none.

### 11-props-and-technology/more zocalo signage.webp  ·  **CORRECTION — the earlier entry dismissed this file, and it is the best view of the wordmark in the set**
- Source authority: **1** (content). The capture is a **photograph of a CRT** — scanlines,
  bloom, and a burned-in subtitle — but it is **1280×960 and the sign fills the top third**,
  which makes it the **largest and most legible rendering of the Zocalo wordmark available**.
  The earlier entry reads "Adds nothing beyond the two better frames; catalogued so it is not
  re-examined." **That is wrong and it cost this pass a file that should have been examined
  first.** Struck.
- Depicts: the Zocalo wordmark over a lit portal, crowd beneath.
- Extracted — the wordmark, letter by letter, at 3×:
  - **Z** — broad and angular, top bar with a **rounded left terminal**, steep diagonal, bottom
    bar with a **rounded right terminal that curls upward**. Two ornaments attach to it: a
    **small ring at mid-height inside the angle**, and a **small spiral curl at the lower left**.
    Together they read as a stylised acute accent — the mark is **Zócalo**, not Zocalo.
  - then **c** (a closed rounded form with an internal horizontal bar), **a** (a bowl with a
    **triangular counter**), **L** (long foot curving up at its right end), and a terminal
    **o rendered as a concentric bullseye — an outer ring with an inner ring/dot and a short
    vertical tick descending from the centre**.
  - **The neon is drawn as a hollow tube, not a solid stroke:** every stroke shows two parallel
    bright contours with a slightly dimmer interior. Reproduce it as an outlined tube.
  - The letters are **connected or near-connected** into one continuous run.
  - Colour here is **electric cyan-blue**. A soft cyan field fills the sign's rounded-rectangle
    outline behind the letters; that may be a luminous backing panel or it may be bloom from an
    over-exposed CRT photograph, and this frame cannot separate the two.
- Extracted — the flanking element appears again as **three or four parallel diagonal blades**,
  confirming the raked-fin reading above and independently disconfirming "zigzag".
- Extracted — the subtitle is a **broadcast/DVD caption with a parenthetical speaker tag**:
  `(Bester)` / `'So...obviously things back home have been a little tense'`. That places the
  frame in a Bester scene and confirms the capture is off a legitimate broadcast source.
- Feeds: `16-signage-typography-ui` — this is the file to author the Zocalo decal from
- Conflicts: none.

### 11-props-and-technology/fresh air resturant signage with view.webp  ·  (= 04-sector-red/Fresh air.webp)  ·  **re-examined; the sign's colour scheme was stated backwards, and the frame is a C-003 pointer**
- Source authority: **1** (on-screen footage). 1200×1046 — one of the largest frames in the set.
- Depicts: the Fresh Air Restaurant, from the floor, looking up past the ceiling services to the
  volume above.
- Extracted — **CORRECTION to the sign.** The earlier entry gives the plaque as "red on a pale
  ground". At 8× it is **three colours in two roles**: the wordmark **`FRESH AIR` is dark navy
  high-contrast serif capitals**; only **`The` (upper left) and `Restaurant` (arcing across the
  lower third) are red-orange italic script**. The ground is a **backlit pale blue-white ellipse**
  inside a **dark navy rim**. So: dark type on light, with red script accents — not red on pale.
- Extracted — above the plaque, **two or three parallel curved aqua-teal neon tubes** sweeping
  down from upper left. A second identical double-swoosh appears lower left on a wall panel.
- Extracted — ceiling services: **at least five parallel runs of oxide-red round tube** crossing
  the space, each carrying **rectangular downlight fittings at a regular pitch**, plus one
  suspended white strip fitting. A **red-orange handrail** runs across at balcony level.
- Extracted — **and this is the part that matters beyond dressing.** At 5× the upper-left of the
  frame resolves as a **dark convex (curving) multi-storey tower face carrying a regular grid of
  pale mint-lit rectangular windows, two panes per bay, in stacked rows** — a **cylindrical
  glazed building standing beside the restaurant**. Above and beyond it the frame is a **dark
  mottled expanse with an orange-tan patch**, consistent with the far side of the drum. Together
  these put the restaurant **inside a large open landscaped volume containing multi-storey
  buildings** — the habitat drum.
- **C-003 relevance, and it is stronger than it looks.** `other map.png` (authority 3) names
  **Fresh Air in the Green rosette**. This frame shows the named facility **inside the drum**,
  and the identification runs through **the restaurant's own on-screen sign**, not through a
  filename or a folder. That is a materially better link than either pointer in
  `canon/CONFLICTS.md` C-003 note 2r, both of which rest on folder attribution. Written into
  `canon/CONFLICTS.md` under C-003 as **corroboration, not resolution**.
- Extracted — fit-out: round tables with **patterned gold brocade cloths**, candle lamps, bentwood
  chairs; walls of **backlit blue-green translucent panels in a raked screen**, densely planted;
  **vertical backlit blue-white light columns** at the bar.
- Feeds: Green Sector fit-out; signage; `canon/CONFLICTS.md` C-003
- Conflicts: corroborates the `other map.png` ordering in which the drum is Green.

### 11-props-and-technology/civilian PPG.webp  ·  **re-examined; it is two-tone, not one finish**
- Source authority: **1** (on-screen footage). 650×526.
- Depicts: a civilian PPG being loaded, held in two hands.
- Extracted — **CORRECTION.** The earlier entry gives a single "matte olive-bronze finish". At 5×
  the weapon is clearly **two-tone**: a **pale olive/khaki polymer frame, rear body and underside
  block** against a **dark blued-steel slide and barrel assembly**. The tonal split is the
  strongest read on the prop and must be modelled.
- Extracted: a **cylindrical barrel shroud with a large open, slightly counterbored muzzle**; a
  **long raised slide rib with a bright polished top edge** running most of the slide's length,
  and a **rear sight block**; a **vertical pair of round-headed bolts** on an olive block under
  the barrel; an **angular faceted olive wedge** forming the rear of the frame; a **round pivot
  boss** low on the right side.
- Feeds: prop set
- Conflicts: none. Still clearly a different weapon from the EarthForce sidearm.

### 11-props-and-technology/Earthforce issue Auricon PPG Pistol with removable sight.webp  ·  **re-examined at 8×; countable detail added**
- Source authority: **2** (prop/production photography — flat blue-grey studio paper backdrop,
  not a frame). Only 304×231.
- Depicts: the EarthForce PPG, main view, plus an inset at lower right with the sight detached.
- Extracted, main view at 8×:
  - **A plain polished cylindrical emitter projects forward**, entering the body through a
    **collar step ring**.
  - The slab side carries **five parallel diagonal slots raked forward-and-up**, with **four round
    studs in a row along the lower edge of that panel**. Both counts are legible.
  - Rear receiver is a boxy block with dark inset details and a dorsal rail.
  - Grip: **black rubber in the revolver pattern** — finger grooves, stippled field, and a
    **circular medallion boss** carrying a device.
  - A **thin curved blade trigger** set well back in a squared guard.
- Extracted, inset at 10×: the detached sight is a **long polished cylindrical tube** with a
  **ribbed top rail at the front** (five or six ribs), a **large knurled circular turret** on top
  at mid-length, and a **stepped rear collar**. It is a tube-scope with a top turret, not a
  simple blade.
- Feeds: prop set; security NPC loadout
- Conflicts: none.

### 11-props-and-technology/blue datacrystal.webp and clear datacrystal.jpg  ·  **re-examined; a dimension, with its method**
- Source authority: **1** (on-screen footage; the second watermarked `yourprops.com/user/nexus6`)
- Depicts: data crystals held up to camera. 576×432 and 600×600.
- Extracted — shape, corrected: an **elongated prism with FOUR or more longitudinal facets and
  chamfers at BOTH ends** — the top corners cut at roughly 45°, the bottom tapering to a narrower
  flat. The earlier entry's "tapered tip" implies one pointed end; both ends are cut.
- Extracted — **scale, method stated.** In `blue datacrystal.webp` the crystal is pinched between
  index fingertip and thumb at the same depth. The index finger's distal phalanx measures 240 px
  across; taking an adult male finger at ~19 mm gives **≈ 12.6 px/mm**. The crystal measures
  **550 × 245 px → ≈ 44 mm long × 19 mm wide, aspect 2.2 : 1.** Call it **4.5 cm × 2 cm, ±20%.**
  This is an estimate from one frame and does not belong in `00-MASTER.md` as a dimension, but it
  is a usable prop size.
- Extracted — colour: **deep cobalt/sapphire, translucent**, with a **green internal reflection
  band** and **hard specular highlights running the facet edges**. Two colours attested across
  the pair: deep blue and colourless.
- Extracted — the S2–3 dress uniform in `clear datacrystal.jpg`, at 4×, is worth taking from this
  frame: **dark navy tunic**; **oxblood standing collar** wrapping the throat; a **gunmetal
  V-yoke at the front of the collar with gold piping down both edges converging to a point at the
  sternum and a small gold tip at the apex**; a **dark epaulette strap with a bright metal rank
  device at the shoulder end**. Background is a soft-focus interior of **vertical amber and blue
  backlit panel bands**.
- Feeds: prop set; `14-characters-and-uniforms` (S2–3 dress uniform detail)
- Conflicts: none.

---

## 16 — Signage, typography and UI

### 16-signage-typography-ui/earthforce logo.webp  ·  **NEW — this file had no entry**
- Source authority: **4** (clean vector reconstruction — 600×191 RGBA with a transparent
  background and exactly two flat colours; hand-drawn vector, not a frame and not generated).
  The *design* it encodes is canon and appears on screen; the *file* is derivative artwork.
- Depicts: the EarthForce winged insignia, isolated.
- Extracted — **exact palette**, measured over the opaque pixels:
  - Blue **`#083994`** — 60.3% of opaque area
  - Yellow **`#FFCE00`** — 36.8%
  - Everything else is antialiasing, each under 0.5%. **Two flat colours, no gradients, no
    shading.** Redraw it as flat vector.
- Extracted — construction, at 5×: **flat blue shapes carrying a uniform-weight golden-yellow
  outline**, the same stroke weight on the silhouette and on the internal bars.
  - **Left:** two blue quadrilateral "wings", one above and one below the horizontal axis, whose
    inner ends **cross in an X** and whose outer ends converge to a single yellow point at the far
    left.
  - **Centre:** a large blue **hexagonal slab** running to the right.
  - **Right:** **two horizontal yellow bars with rounded ends project leftward into the slab** —
    these are the arms that make the whole read as a left-facing **E**.
  - **Top centre:** a small blue **trapezoidal cap** outlined in yellow, sitting proud of the
    slab's top edge.
  - Overall aspect **600 : 191 ≈ 3.14 : 1**.
- **Cross-file link worth building once and reusing.** The same winged mark appears in at least
  three places in this reference set: as this standalone logo; **at the centre of the Earth
  Alliance seal in `faction symbols.png`**, in grey over the torch; and **inset on the
  communicator-link plate in `communicator link.jpg`**. One decal asset, three applications.
- Feeds: `16-signage-typography-ui`; EarthForce set dressing, uniform patches, prop decals
- Conflicts: none.

### 16-signage-typography-ui/babylon 5 shield.webp  ·  **CORRECTION — the star count is wrong, and the geometry is now specified**
- Source authority: **4** (vector reconstruction of the on-screen station patch). 600×886 RGBA.
- Depicts: the Babylon 5 station shield.
- Extracted — **CORRECTION, and it is a hard count.** The earlier entry gives **"seven white
  five-pointed stars (four on grey, three on blue)"**. Connected-component analysis of the white
  pixels returns **exactly six blobs**, all identical in size (≈1290 px, 54×54 px bounding box),
  and nothing is occluded by the numeral. The count is **six — three and three**:
  - **Blue column**, centres at x = **516**, y = **97, 287, 463**
  - **Grey column**, centres at x = **73**, y = **331, 521, 697**
  - The two columns are **the same pitch (≈190 then ≈176 px)** and the grey column is offset
    **234 px lower** than the blue. Verified stable at white thresholds of 240, 230, 220 and 200.
- Extracted — **the division, measured.** A straight diagonal from the **top-left corner** to the
  **right-hand edge at ≈87% of the height** (y ≈ 769 of 886), slope **dx/dy ≈ 0.75–0.77** (about
  37° from vertical). **Blue above and right, grey below and left.** Traced at y = 60/120/180 and
  again at y = 600/660/720 — the slope is the same at both ends, so it is one straight line.
- Extracted — **exact palette**, by area over the opaque pixels:
  grey **`#9C9C9C`** 34.0% · blue **`#00319C`** 27.3% · gold **`#FFCE00`** 12.9% ·
  black **`#000000`** 11.5% · red **`#CE3129`** 7.4% · white **`#FFFFFF`** 1.5% ·
  blade highlight **`#ECEBF0`** 0.8%. Six flat colours plus one highlight tint.
  **The gold `#FFCE00` is byte-identical to the yellow in `earthforce logo.webp`** — the two
  files share a palette, so they are one artist's pair and are **not** two independent sources.
- Extracted — outline: **600 × 886 ≈ 1 : 1.48**; straight top, straight sides to ≈87% height, then
  a **smooth continuous curve to a rounded base** (not a point). **Red border ≈15 px on a 600 px
  width = 2.5%**, constant all the way round.
- Extracted — the numeral, at 3×: a **four-layer stack** from outside in — **black keyline, gold
  offset outline, black, then the gold numeral**. The glyph is **flat-topped with a squared upper
  arm, a stepped diagonal shoulder, and a full round bowl**, with a **solid gold disc floating in
  the black counter**. The black surround carries **deliberate stepped notches at the left waist**.
- Extracted — the sword: **grey blade with a pointed tip**, a **plain grey ricasso block** shaded
  light-left/dark-right, a **gold crossguard whose two arms sweep shallowly upward** on a grey
  collar, a **grey waisted (hourglass) grip**, and a **gold ellipse pommel wider than it is tall**.
  Every part is black-keylined.
- The "5" glyph is the same one used as **floor inlay** (`conference aerea.webp`) and **furniture
  branding** (`more zocalo.png`). One mark, three applications — build it once as a decal.
- Feeds: `16-signage-typography-ui`; NPC uniform patches; set dressing
- Conflicts: none, but the earlier seven-star claim in this index is superseded.

### 16-signage-typography-ui/faction symbols.png  ·  **re-examined; counts and construction added**
- Source authority: **4** (period vector/web reconstruction, 625×290, 66% white ground; consistent
  with on-screen use)
- Depicts: eight faction emblems, captioned in **navy bold sans** — five on the top row, three on
  the bottom.
- Extracted, at 8× per emblem:
  - **Earth Alliance** — a **navy outer ring** carrying `SEAL OF THE EARTH ALLIANCE` in white sans
    caps around the lower arc and **about eight small white five-pointed stars filling the upper
    arc**; inside it an **orange ring bearing a laurel wreath of dark leaves in two sprays meeting
    at the bottom**; inside that a **pale periwinkle disc** carrying a **torch with a yellow flame**
    whose shaft runs to the bottom, with the **grey EarthForce winged mark laid horizontally
    across it** — the same device as `earthforce logo.webp`.
  - **Minbari Federation** — an **inverted mid-blue triangle, point down**, overlapping a **dark
    navy sphere**; superimposed a **dark hooked crescent** with a **pale gold flame-like streak**
    running through it.
  - **Centauri Republic** — a **fan/plume of about eleven tapered rays** radiating from a central
    boss, alternating **purple-blue and orange-red**, every ray outlined in cream; two **outer
    C-lobes curve down and terminate in eye-spots** (white ring, dark red centre); **two small
    dark-red discs** float above the plume; the **central boss is a dark ring with a red star**.
  - **Narn Regime** — **two mirrored wing-blades**, each carrying **five or six barbs on its inner
    edge** in a gold-to-black gradient, each rising from a **dark red half-disc base**; between
    them a **group of three tapering black spikes**, one long and two flanking.
  - **Vorlon Empire** — **two nested crescents opening downward**, dark mottled green-black with
    **gold-bronze flecking concentrated at the flared tips and along the outer edge**, over a
    **dark sphere with a single bright specular point at its centre**.
  - **Interstellar Alliance** — an **inverted triangle with a blue keyline** on a black starfield,
    a **white-blue spiral galaxy** at centre, and a **ribbon sweeping around it** from orange-red
    at the left through gold and white at the top to violet at the right, studded with white stars.
  - **League of Non-Aligned Worlds** — an **orange annulus** around a **red-to-orange triangle with
    a bright glowing sphere at its centre**, ringed by **twelve teal four-pointed stars, each with
    an orange centre dot** — counted, at roughly one per clock hour.
  - **Army of Light** — an **oval mandorla with a gold rope/sunburst border**, upper half a
    **golden sunburst of rays**, lower half **black with a spiral galaxy**, a **vertical sword**
    overlaid, and a **red-orange gem at the upper left**.
- **Era: only EA, Minbari, Centauri, Narn, Vorlon and the League are S2–3.** The Interstellar
  Alliance and the Army of Light are S4–5 and **must not appear on S2–3 signage**.
- Feeds: `16-signage-typography-ui`; NPC faction identity
- Conflicts: none.

---

## 13 — Other ships

### 13-other-ships/kosh's transport.webp  ·  **NEW — this file had no entry, and its real value is the docking bay, not the ship**
- Source authority: **1** (on-screen footage, period Foundation-era CGI). 800×600.
- Depicts: the Vorlon transport sitting in a station docking bay, seen from above and to one side.
  The ship fills the upper right; the bay's overhead structure, gantry and floor machinery fill
  the rest.
- Extracted — **the bay, which is the part that constrains what we build:**
  - **Overhead: a space-frame of square-section black tubes** — verticals and diagonals meeting at
    boxy nodes, with bright pale edge highlights on the far members. Open truss, not a clad soffit.
  - **Hanging from the frame nodes on short stalks: bulbous dark-grey fittings**, each a rounded
    body with a **stepped collar and a downward-pointing cluster of about three cylindrical
    barrels**. Three or four are visible, one in close-up. They read as bay floodlights or
    grapple/thruster heads; the frame cannot decide which. Either way they are a **distinctive,
    countable, repeating overhead fixture** and nothing else in the reference set shows one.
  - **A long flat pale-grey gangway** extends toward the ship from the right, with a **row of studs
    along its edge** and a **stepped end**, carried on **angled struts**.
  - **The bay floor is dense pale-grey greeble** — cylindrical tanks, boxes, elbowed pipe runs,
    small gratings and ladders, laid out like a plant room. A **large smooth pale cylinder** (duct
    or tank) curves away at the upper left. A **red-brown mottled region** occupies the far right.
  - **Lighting is very low-key and cool grey-blue**, with the ship keyed from the upper right. The
    bay reads as effectively unlit except by practicals — consistent with `03-sector-blue/dock.webp`.
- Extracted — the ship, for completeness:
  - **Hull pattern: hard-edged irregular chartreuse blotches on a black ground**, matte, like a
    poison-dart frog rather than a painted camouflage.
  - **Iridescent blue-violet strips** run along the dorsal ridge above the eye, along the lower jaw
    and on the flank — a third accent colour, wet-looking and distinct from the mottle.
  - **The nose carries two large round ports of different character**: one is an **eye — a bright
    yellow-green annular rim around a glossy black hemisphere with a specular highlight**; the
    other is an **open bore with a visible inner tube**. They are not a symmetric pair of eyes.
  - **A smooth pale-grey curved spar** runs down the flank, non-organic and clearly structural
    against the organic skin.
  - **The stern is a bundle of two limb types**: about **six round-section tapering tentacles**,
    mottled, some interrupted by **smooth grey collar bands carrying small dark rectangular
    decals**; and **three or four flat grey lance-shaped blade-fins** with sharp points, smooth and
    unmottled, lying between the tentacles.
- Feeds: docking-bay interior spec; `03-sector-blue` bay fit-out; Vorlon vessel model
- Conflicts: none. Adds no dimension and does not bear on C-003 or C-004.

---

# Session 2s (folders 12 / 14 / 15) — Starfury, characters and uniforms, races and makeup

*A sibling agent in the same workflow is also labelling its work "session 2s" (folders 11, 16, 13),
in the section above. The folder list in each heading disambiguates them.*

**All 28 image files in `12-starfury`, `14-characters-and-uniforms` and `15-races-and-makeup`
were opened and looked at in this pass, including the four that already had entries.** Nothing
was skipped for being small: the 250×350 `Pak'ma'ra even more.jpg` turned out to be a **licensed
trading card** carrying a canonical species spelling and a season stamp, which is a higher
authority than anything else in that folder.

Three things came out of it that matter beyond costume:

1. **`14-characters-and-uniforms/Sheridan.jpg` contains an in-universe wireframe profile of the
   whole station** on a C&C wall graphic. It independently corroborates C-007 (six coplanar
   radiator blades, three above the spine and three below) and offers a reconciliation with the
   "12" counts in `00-MASTER.md` §2. Written up under C-007.
2. **`14-characters-and-uniforms/talia-winters in gorgeous office.webp` is a large, clear,
   authority-1 view into the habitat drum**, showing the banded axial support struts that the
   Earhart's frame showed indistinctly. Written up under C-003. It corroborates; it does not
   resolve.
3. **`15-races-and-makeup` contains two *different* Vorlon encounter suits**, and the existing
   index entry for `more vorlon.png` calls the wrong one "Kosh's". See the corrections at the
   foot of this section — this one has era consequences.

**No new quarantine candidates matching either existing signature** (2023 animated film,
AI-generated) were found. **One new out-of-scope flag** is raised: `Galen.jpg` is *Crusade*, not
Babylon 5 — see its entry.

**No level number, no lift-car display and no sector name appears in any of these 28 files.**
C-004's specific ask is not answered here.

---

## 12 — Starfury (all four files, re-examined)

### 12-starfury/Starfury more.jpg  ·  **correction to the existing entry**
- Source authority: **2** (production concept art — signed **"STEVE BURG '93"**, two drawings on
  one sheet: *"EARTH ALLIANCE FIGHTER (PRELIMINARY CONCEPT)"* and *"BABYLON-5 / EARTH ALLIENCE
  FIGHTER"* [sic]).
- **Correction.** The existing entry calls this "= `earth alliance fighter.jpeg`, duplicate at a
  different size". Both files are **900×1350 — the same pixel dimensions**. They are the same
  scan at two JPEG quality settings (max per-channel difference 102, mean 5.6; not byte- or
  pixel-identical). "Different size" is wrong and would mislead anyone choosing which to work
  from. Prefer `Starfury more.jpg`: it is the larger file (196 KB vs 184 KB) and therefore the
  less compressed of the two.
- Extracted, added this pass at 4–8× on the cockpit and nacelle:
  - **The canopy is a single large hexagonal window in a heavy chamfered frame**, set into the
    forward face of a flattened hexagonal-prism pod. The **pilot is drawn seated and upright**,
    head near the top of the glass — not prone or reclined. Confirms the posture the flown
    Aurora footage shows.
  - **Nacelle ends** carry, in this order outboard: a **recessed thruster bell in a ring collar**,
    then **two narrow banding rings**, then a **domed sensor/gimbal ball on a short stalk mounted
    on the nacelle's upper face**, then small **rectangular louvre vents**.
  - Each arm carries a **secondary thruster barrel mounted on its inboard face**, angled
    outward — the manoeuvring set, distinct from the main bells.
  - Separate slim **swept blades** (canard-like, banded near the root) are drawn detached beside
    the aircraft on the sheet, as component studies.
  - The pod's underside has a **wedge-shaped fairing** with a chin thruster nozzle.
- **Caveat unchanged and still binding: it says "preliminary".** Thruster positions come from
  `station/physics/starfury.py::aurora_thrusters()`, not from this sheet.
- Feeds: `station/starfury_geometry.py`

### 12-starfury/earth alliance fighter.jpeg
- Source authority: **2**. **Same image as `Starfury more.jpg`, same 900×1350, more compressed.**
- No independent content. Retained as a duplicate; do not catalogue findings against it
  separately. Extraction lives in the entry above.

### 12-starfury/Starfury.jpg  ·  **supplements the existing entry**
- Source authority: **1** (on-screen footage, CGI). 640×420.
- The existing entry is right about the four lit nacelles, the non-coplanar arms and the faceted
  pod. Added this pass, from 4–12× crops:
  - **The frame is a braking manoeuvre, not a burn.** Every lit nozzle faces the camera: the four
    **arm-end bells** and a **ventral cluster of four plumes** splaying forward from beneath the
    pod. The Aurora decelerates on forward-facing thrusters, which is what
    `station/physics/starfury.py` assumes.
  - **A nacelle-head attitude thruster fires perpendicular to the arm** — the upper-right nacelle
    has a discrete blue plume shooting radially away from the arm axis, from a nozzle on the
    **top of the nacelle barrel**, not from its end. So the nacelle heads carry **end thrusters
    and radial attitude thrusters as separate fittings**.
  - **Nacelle head construction:** a barrel with a **raised collar ring**, a **boxy dorsal
    fairing** on top of it, and the end bell recessed behind a ring lip.
  - **The arm is a slab, not a tube** — chamfered top edge, flat outer face, a **black
    longitudinal stripe** running its full length along the lower edge, and a row of **dark
    rectangular panels/vents** (4–5 visible per arm) set into the outer face.
  - **Large dark stencil markings** are painted on the arms' upper surfaces. They are blown out
    by the thruster glow at this resolution and **cannot be transcribed**; recorded so a better
    frame is known to be worth looking for.
  - Hull is **white-grey with dark inset panels**; the cockpit interior shows **amber and green
    instrument glow** around the silhouetted pilot.
- Feeds: `station/starfury_geometry.py`; `station/physics/starfury.py`

### 12-starfury/starfury even more detailed.jpeg  ·  **supplements the existing entry**
- Source authority: **4 — third-party fan 3D model.** 1920×1080 studio-gradient turntable render.
  The existing warning stands and this pass sharpens it.
- Looked at 4× on the cockpit. **Concrete list of what this model invents**, so nobody mistakes
  any of it for canon: an **exposed exoskeletal canopy frame** with a triangular strut across the
  glass; a **blue MFD screen** set in the frame; **gun barrels slung under the pod**; **yellow
  painted wing panels** on the upper arms; **modern PBR wear and grime**; **fluted engine bells
  with a bright iris and radial spokes**. None of that is in the concept art or the footage.
- Still useful for one thing only: the **overall X-frame proportion at a clean camera angle**.
- Not quarantined — it is a fan reconstruction of the right subject, the same class as
  `other map 2.jpg`.

---

## 14 — Characters and uniforms (all twelve files)

### 14-characters-and-uniforms/Sheridan.jpg  ·  **the most valuable file in these three folders**
- Source authority: **2** (production/publicity still, studio-lit, shot on the C&C set).
  1414×1418 — by a wide margin the highest genuine detail in the folder.
- Depicts: Sheridan in the Season 2 EarthForce command uniform, standing in front of **two large
  backlit C&C graphic panels and a wall monitor**.
- **Extracted — the station wireframe.** The upper panel carries a **cyan wireframe side
  elevation of the whole of Babylon 5**, drawn as an in-universe technical readout. At 7–9× it
  is legible, and it is the only in-universe full-station orthographic we hold at authority 2.
  Reading it against `00-MASTER.md` §2 fixes its orientation as **aft at the left, fore at the
  right** (the finned reactor barrel is at the left end; the long thin communications masts and
  the fore cap are at the right):
  - **Six radiator blades — three above the spine, three below, all in the plane of the drawing.**
    A pure side elevation would show edge-on blades as lines; these are drawn full-face, so the
    blades lie in one plane containing the long axis. **Independent authority-2 corroboration of
    C-007.** See the C-007 note in `canon/CONFLICTS.md`.
  - **Each blade is a two-limbed fork**: two long limbs splayed at the hull root, converging to a
    **small rectangular end pad** at the tip. Six forks × two limbs = **twelve limbs**, which is a
    candidate reconciliation with the "Reactor cooling fins (12)" and "Heat exchange arrays (12)"
    counts in `00-MASTER.md` §2. Logged as a hypothesis under C-007, not as a fact.
  - **A dorsal row of ~6 small square modules on a rail** runs aft-of-centre along the spine,
    with **six blue leader arrows** taking them to six callout boxes under the heading
    **"AUTO LOADERS SEQUENCE"**. Corroborates the "cargo modules run along a dorsal line, not
    around the circumference" correction from `01-station-exterior/exterior more.jpg`, and
    suggests those dorsal modules are **auto-loader positions**.
  - **Four ventral callouts on the fore drum are labelled "ATMOSPHERIC LIFE SUPPORT REGULATORS"**
    (three leadered arrows, four boxes). A named subsystem with a count and a face of the hull.
  - **The habitat drum** is the long, densely **longitudinally-ribbed** cylinder of largest
    diameter, with a **distinct narrower inner tube running its length** — an axial core inside a
    hollow drum, consistent with the core shuttle. Bears on C-004 only weakly; **no deck lines,
    level numbers or sector divisions are drawn**, so it does not touch the numbering question.
  - **Long thin masts extend beyond the hull at spine level toward the fore end** — the deep space
    communications grid on pylons (`00-MASTER.md` §2 item 17).
  - Three white **callout balloons shaped as truncated cones** magnify three dorsal features; a
    fourth callout is a **disc quartered by an X into four petal segments**, most plausibly an
    aperture/iris detail. **Not read as a sector diagram** — the leader goes to a single point on
    the hull, not to the whole cross-section. Recorded, not used.
- **Extracted — the lower panel.** Headings **"GRAVITATIONAL INERTIA"** and **"[G]RID STATUS"**.
  Contains a **four-quadrant annulus diagram with a radiation trefoil at its hub** and curved
  rotation arrows, a **column of stacked yellow bars**, and a cyan schematic of a structure with
  **four red-headed arms on angled stalks**. "Gravitational inertia" as a monitored quantity is
  a nice in-universe label for the drum spin-up/spin-down readout.
- **Extracted — the monitor.** A wall screen in a black bezel with a **notched top-left corner
  carrying a red triangular tally** and a **round boss at the bottom-right**, showing a **large
  squared "5" glyph, dark red on red, in a violet surround**. Same glyph as the station shield,
  the conference-area floor inlay and the Zocalo furniture branding — **one mark, now four
  applications.** Below it a **dark angled console with a white light strip along its leading
  edge**, its glass top reflecting the "5".
- **Extracted — the uniform. This is the definitive S2–3 EarthForce command reference.**
  - Body: **slate blue-grey wool**. **Brown leather plastron/bib** covering the whole centre
    front from the standing leather collar down, its outer edge finished with **crimson piping**.
  - **Crimson piping** also along both collar edges and as a welt along the **top of each
    shoulder** from neck to sleeve head.
  - **Leather epaulette straps** over both shoulders, each carrying a **flat gold trapezoidal
    wedge** near the neck; a matching **gold wedge on a black collar tab** at the throat.
  - **Left upper sleeve:** embroidered **EarthForce wings badge** — gold outspread wings flanking
    a red-and-white central device on a blue ground, black field, red top edge.
  - **Right chest:** a **plain gold horizontal bar** (name tape) beneath a **dark blue rectangular
    device with gold detail**, over a welted breast pocket.
  - **Discriminator against the Season 1 pattern, and it is a clean one:** S2–3 has **crimson
    piping and a leather bib**; the Season 1 pattern in `Chief of security Garibaldi.webp` and in
    the two vector sheets has **neither** — cloth panels, no piping.
- Feeds: `canon/CONFLICTS.md` C-007 · `station/schema/station.yaml` components ·
  `16-signage-typography-ui` (C&C display language) · NPC costume model (S2–3 command)

### 14-characters-and-uniforms/talia-winters in gorgeous office.webp
- Source authority: **1** (on-screen footage). 1080×817.
- Depicts: Talia Winters in a room with **a large multi-pane window looking directly into the
  rotating habitat drum**. The drum view is the reason this file matters; the costume is
  secondary.
- **Extracted — the drum interior, and this is the clearest view of it we hold:**
  - **Two axial support struts** rise from the drum wall and splay toward the centreline. Each is
    a **segmented cylinder** — roughly **four pale grey barrel sections separated by three or
    four dark collar joints**, with a **salmon/pale-orange collar** at each joint and a **fatter
    capsule swelling** near the wall end. This is the same structure the Earhart's frame showed
    as "splayed struts banded with orange rings"; here it is resolved. **The bands are joints,
    not decoration**, and the colour is salmon rather than orange.
  - **The far side of the drum arches overhead and fills the top of frame.** Its surface is
    divided into **long continuous longitudinal bands** running parallel to the axis — greys and
    olive-greens, with one broad **orange-red band** on the right. The bands run the whole visible
    length; they are strips, not tiles. Rows of **small blue rectangular lights** and thin pale
    lines (roads or lighting runs) are scattered along them.
  - **On the near floor: a low-rise built district** — large flat-roofed grey rectangular
    buildings, paved plazas and a stepped terrace edge in the foreground. **Buildings stand on
    open ground.** The innermost surface of the drum is not a deck soffit.
  - Written up under C-003 in `canon/CONFLICTS.md`. It corroborates the drum architecture; it
    **names no sector and shows no level number**, so it resolves nothing.
- **Extracted — the room** (a good, unusual interior, worth building):
  - Dark panelled walls; **blue backlit slots** high on the left wall; a **diamond-plate deck**.
  - A **tall carved dark-green alien totem** standing free at the left, and a **green stepped
    bamboo-like sculpture** at the right — both floor-standing art pieces.
  - Low **dark blue-grey upholstered armchairs and a sofa** with a **maroon cushion**.
  - A **conical orange lamp** — a triangular translucent shade glowing amber, on a dark stepped
    base with a ring of small light points around its lower rim, standing on a console table
    against the window.
- **Costume:** Talia in the **Psi Corps gold/ochre suit** — structured jacket and pencil skirt in
  a warm mustard-tan, with **black inset panels** forming a deep V at the front and running down
  the sides and sleeves; **strong squared shoulders**; the **Psi Corps badge** at the left
  shoulder. In era for S2 (Talia leaves at the end of Season 2).
- Feeds: `canon/CONFLICTS.md` C-003 · drum-interior architecture · Green/Red Sector fit-out

### 14-characters-and-uniforms/Talia Winters in uniform.webp
- Source authority: **1** (on-screen footage). 1000×750. Close-up.
- Extracted:
  - **Psi Corps badge, resolved at 8×:** a **downward-pointing cut-diamond/pentagon in polished
    silver-chrome**, bearing a **raised Greek Ψ (psi)** — three tines rising from a stem. Worn on
    the black shoulder panel, high on the left chest. Buildable as a single small decal/mesh.
  - Jacket: **dark olive-green/black**, with a **shawl-style asymmetric wrap collar** crossing
    right over left, and a **black inset panel** over the right shoulder. Gold hoop earring.
  - **Wall behind — a good interior-kit find:** a chain of **large elongated hexagons in relief**
    in pale grey-blue, with **recessed darker hexagonal fields between raised hexagonal ribs**,
    and a **bright blue backlit rounded-rectangle light panel** set into the recess at low level.
    A **large circular disc with dark radial marks** part-visible at the upper left. Lighting is
    entirely blue.
- Feeds: `10-interiors-generic-kit` (elongated-hexagon relief panelling) · NPC costume (Psi Corps)

### 14-characters-and-uniforms/Zach Allan in security uniform.jpg
- Source authority: **2** (publicity still, studio-lit on a set). 787×1000.
- **In era, and it dates itself.** Zack wears the **NIGHT WATCH armband**, which places the still
  in the late-Season-2 / Season-3 window. Valid S2–3 costume reference for station security.
- Extracted, at 6–8×:
  - **Uniform:** medium grey twill jacket; **black leather standing collar and yoke**; **black
    leather epaulettes** on both shoulders; **two flapless breast pockets** with horizontal welt
    seams; a **gold triangular pin at the throat** (the same throat device as the command
    uniform).
  - **Security badge, right chest:** a **gold-outlined diamond with slightly convex sides** on a
    black field, containing a **gold circle** crossed by **four tapered spokes** that run outward
    through the ring toward the diamond's four points, with a **small gold-outlined square ring at
    the exact centre**. A crosshair in a diamond. Confirmed identical to the badge in
    `security in uniform.jpg`, so this is *the* EarthForce Security device, not a one-off.
  - **NIGHT WATCH armband, left forearm:** black band, gold embroidery — a **stylised eye inside
    a swept almond/wing outline with a small triangle above the pupil**, over the words
    **"NIGHT WATCH"** in gold caps (visible: "…GHT WATC…").
  - **The link, left wrist, resolved at 8×:** a small **shield-shaped plate** — flat top, straight
    sides, chamfered lower corners to a shallow point — in **polished white metal**, on a dark
    strap, worn on the **back of the wrist**. Its face carries a **dark inlaid glyph of nested
    angle brackets with horizontal bars and dots between them**. Best link reference we hold.
  - **Background display:** a black panel carrying a **yellow flat-silhouette diagram of a tall
    tapering tower over a base of horizontal bars**, and a **cyan/teal flow diagram** with chevron
    arrowheads and rounded terminal nodes, plus yellow-green legend blocks (body copy illegible).
    Graphic language is **flat colour silhouettes with no outlines**, yellow/cyan/green on black.
- Feeds: NPC costume (S2–3 security) · `11-props-and-technology` (link) ·
  `16-signage-typography-ui`

### 14-characters-and-uniforms/security in uniform.jpg
- Source authority: **1** (on-screen footage). 638×960.
- Depicts: Zack Allan seated among a **row of security officers**, in the same grey uniform.
- Extracted:
  - **Confirms the security badge** independently at 8×: the same gold circle, four tapered
    spokes and central ring, here on a rectangular-reading lozenge because it is seen at an angle.
  - **Background officers wear the grey jacket with a black tactical vest over it** — a second,
    heavier security rig for duty wear. Two distinct security silhouettes to model.
  - Collar/yoke here reads **dark navy leather** rather than pure black; the gold throat triangle
    is present.
- Feeds: NPC costume (S2–3 security, two rigs)

### 14-characters-and-uniforms/Chief of security Garibaldi.webp
- Source authority: **1** (on-screen footage). 322×480.
- **Era caveat: this is the Season 1 pattern.** Grey-blue jacket, **dark near-black vertical front
  panel**, standing collar, **no piping**, **cloth not leather**. Valid as *set* reference,
  invalid as S2–3 costume reference. (Same rule already recorded for `04-sector-red/zocalo.webp`.)
- Extracted:
  - **Wide black leather waist belt with a large gold-brass buckle** — an angular chevron/arrowhead
    plate. A **holster** at the right hip with a **white cylindrical fitting** visible at its top.
  - A **white/silver band on the right wrist** — the link, worn on the outer wrist, consistent
    with Zack's.
  - **The pistol.** A compact sidearm with a **bright polished-metal slide over a dark frame and
    grip**. At 322×480 and heavily backlit it **cannot be confidently identified as the standard
    PPG**; recorded as observed and flagged. Do not model a PPG from this file.
  - Background: a **dark hexagonally-panelled wall** with a large hexagonal recess at the upper
    left, and a bright-edged angled bulkhead/door frame. Corroborates the hexagon-panel motif seen
    behind Talia.
- Feeds: `10-interiors-generic-kit`; NPC costume (S1, flagged out of era)

### 14-characters-and-uniforms/Marcus Cole in uniform.jpeg
- Source authority: **1** (on-screen footage). 501×953.
- **In era for Season 3.** Marcus is introduced in S3, so the Ranger costume is inside the lock —
  but only for S3, not S2. Flagged so a season-accurate NPC set can honour the distinction.
- Extracted:
  - **Ranger dress:** brown/tan **sleeveless tabard-tunic** over a **black long-sleeved undershirt
    with quilted leather sleeves**; a **black high roll-neck**; a **broad dark diagonal baldric**
    across the chest with a braided/embroidered edge; a **wide black waist belt with a large
    ornate gold-bronze buckle** in a stylised bird/leaf form with scrollwork; a long thin dark
    cord hanging from the belt; black trousers.
  - **The badge on the baldric, at 3×:** an **oval pale blue-green cabochon** (aquamarine or jade)
    in an **ornate gold bezel**, mounted high on the left chest on an embossed dark strap.
  - **The room** is worth building: a **tall arched alcove** — a pale panel with a rounded-top arch
    outline set in a **deep dark reveal with rounded corners**, fronted by a **dark cylindrical
    pilaster**; a small **3×4 slot vent grille** low on the pale panel; soft warm uplight from
    below. A **ribbed mauve/lavender upholstered bench on a chrome frame** stands at the left.
    Violet and warm light mixed — reads as Minbari-styled quarters or an alien-sector room, not
    the standard EA corridor kit.
- Feeds: NPC costume (Rangers, S3 only) · alien-sector / Minbari interior variation

### 14-characters-and-uniforms/Marcus Cole with Minbari denn'bok.jpg
- Source authority: **2** (publicity still). 608×634.
- Extracted:
  - **The denn'bok (Minbari fighting pike), extended:** a **plain polished-metal cylindrical
    staff of uniform diameter**, roughly 5–6 ft, with a **knurled/ribbed grip band about a third
    down from the top** and a **narrow dark collar band** below it — the telescoping joint. No
    taper, no head, no ornament. A simple and exactly specifiable prop.
  - **Ranger cloak:** long, **black outer with a bright yellow-gold lining**, seen where it is
    flipped back over the left shoulder.
  - Under it: **grey-brown windowpane-check fabric panels**, a leather bib, the **same oval
    jewelled brooch** (green cabochon, gold oval bezel) high on the left chest, a **dark braided
    scarf**, the **same ornate gold belt buckle** as the frame above, and **black fingerless
    gloves**.
  - **Background:** a large **backlit wall graphic** — concentric magenta ring/vortex artwork
    overlaid with **red grid lines** and small annotations, with a **row of labelled boxes along
    the bottom edge** in magenta on blue. The typographic register matches the customs boards.
    **The text is not legible at this resolution and is not transcribed.**
- Feeds: `11-props-and-technology` (denn'bok) · NPC costume (Rangers, S3) ·
  `16-signage-typography-ui`

### 14-characters-and-uniforms/earth_force_command uniforms.jpg  ·  **supplements + corrects**
- Source authority: **4** (fan vector reconstruction, flat colour, three views, titled
  **"EARTH FORCE UNIFORMS"**). 1025×713.
- The existing entry's **era call is correct and this pass confirms it**: the sheet has **no
  piping and a cloth bib**, so it is the **Season 1** pattern, not S2–3. The discriminator is now
  stated explicitly under `Sheridan.jpg`.
- **Correction to the existing entry's emblem description.** It calls the EarthForce emblem "a
  blue and gold winged chevron in a hexagonal outline". At 8× it is not that. It is a
  **horizontally elongated, gold-outlined device with pointed wings at both ends** (a bowtie or
  flattened-X outer profile) on a **navy blue field**, with a **small gold trapezoidal tab on the
  top edge at centre** and, filling the right half of the field, **three stacked horizontal gold
  bars** forming a stylised **"E"**. Gold on navy throughout.
- Extracted, added this pass:
  - Body **slate blue-grey**; **maroon-brown** standing collar, asymmetric front yoke, **very deep
    cuffs** (about a quarter of the forearm) and waistband; **small gold rectangular buckle**;
    **small gold triangular pin at the throat** — the throat triangle is therefore common to S1
    and S2–3 and to both command and security.
  - Left chest: a **small blue-and-gold patch above a plain gold horizontal bar** (name tape).
  - Trousers slate blue-grey with a front crease and slash pockets, into **black ankle boots**.
- Feeds: NPC costume model — **cut and seam topology only**, with the era flag.

### 14-characters-and-uniforms/earthforce security uniforms.jpg
- Source authority: **4**. 1025×713. **The same vector drawing as the file above, in the grey
  colourway** — medium neutral grey body, same maroon-brown collar/yoke/cuffs/waistband, same
  emblem.
- One difference worth recording: **the back view on this sheet carries the EarthForce emblem
  across the upper back**; the blue sheet's back view does not. At authority 4 this is as likely
  to be the artist's inconsistency as a real distinction — recorded, not adopted.
- Feeds: NPC costume model (topology only)

### 14-characters-and-uniforms/uniform-army-of-light.jpg
- Source authority: **4** (fan vector reconstruction, titled **"BABYLON 5 UNIFORM ARMY OF LIGHT"**).
  1001×686.
- **Out of era.** The Army of Light is a Season 4 formation. Do not dress any NPC in it.
- Retained for one thing, which is genuinely useful:
  - **It corroborates the station shield's star split at a second source.** Red-outlined shield,
    divided diagonally — **blue upper right, grey lower left**; a **vertical point-up sword**; a
    **gold "5"** over the sword; **seven white five-pointed stars, four on the grey and three on
    the blue.** That is exactly the count and placement recorded for
    `16-signage-typography-ui/babylon 5 shield.webp`. Two independent authority-4
    reconstructions agreeing on 4/3 makes the decal safe to build.
  - Also carries a **service cap** graphic: dark blue oval crown, **red band bearing white stars**,
    gold edge trim. Out of era; recorded only.
  - Uniform shown: all-black, grey shoulder yoke inset, dark navy chequered collar insert, a
    diagonal seam from the left shoulder, gold oval belt buckle.
- Feeds: `16-signage-typography-ui` (shield decal, corroboration only)

### 14-characters-and-uniforms/Galen.jpg  ·  **FLAGGED — wrong series**
- Source authority: **would be 2 (publicity still), but the subject is out of scope.** 399×489.
- **This is Galen the technomage, from *Crusade* (set 2267/2199-era spin-off), not from Babylon 5
  and not on the station.** The corridor behind him is the *Excalibur* set: grey wall ribs with
  **vertical blue-white light strips** between them, a dark red horizontal band at high level,
  and haze. It is a different production design from the B5 station kit.
- **Does not match either existing quarantine signature** (it is neither the 2023 animated film
  nor AI-generated), so it is not moved. But it is **out of the era lock and out of the subject**,
  and it should not be used for costume, prop or interior reference. Flagged here loudly rather
  than silently catalogued.
  - Recommend a third quarantine folder, or a `zz-out-of-scope-spinoff/` folder, if more
    *Crusade* / *Legend of the Rangers* material turns up. **One file does not justify creating
    one yet** — recorded so the next session can decide with a count.
- The only thing recorded from it: the **staff** — a black shaft with a **knurled/ribbed grip
  section** and a **pale metal ferrule at the top**. Not a B5 prop; do not model it.

---

## 15 — Races and makeup (all twelve files)

### 15-races-and-makeup/G'Kar more.jpg
- Source authority: **2** (production/publicity still, studio-lit on a set). 800×800.
- Depicts: G'Kar in full Narn ambassadorial dress against a **red relief wall covered in Narn
  script**.
- **Extracted — the script, and this is the real find:**
  - A **deep red-orange panel carrying large incised glyphs**, organised into **rectangular
    cartouche cells framed by raised borders** — a compartmented, grid-based layout.
  - Glyph forms seen at 5×: a **"D"-shaped bowl**, a **chevron/arrowhead**, a **triangle with an
    internal bar**, **paired vertical strokes**, an **"L"/"⌐" bracket**, **closed "P"-like
    forms**, and **short horizontal bars**. Strictly **rectilinear and angular**.
  - **This is a distinct alien typographic register.** It is not the curvilinear single-stroke
    family recorded for the Zocalo wordmark, Doug's Dugout and row 3 of
    `11-props-and-technology/Vorlon, Narn, and Centauri script examples.jpg`. Cross-check against
    that sheet's Narn row before assigning either to the Narn.
  - Caveat: this is a publicity backdrop and may be the Narn homeworld or a temple rather than the
    station's Narn quarters. Treat as Narn *cultural* reference, not as station signage.
- **Extracted — makeup:** hairless; **tan/ochre skin with dark brown leopard spotting** over the
  crown and temples, plainer on the face; **deep vertical brow furrows**; **red irises with dark
  pupils**; a **broad flat nose bridge**; **reptilian scaling on the neck**; small pointed chin.
- **Extracted — costume:** layered **tan/ochre suede panels with fringed edges**; **vertical dark
  strap bands with brass studs**; a **tall stiff fluted standing collar**; a **chainmail-mesh bib**
  at the throat; **iridescent purple-blue trim** on the shoulder yokes and the front apron edge;
  a **large pebbled reptile-hide apron panel** at the front; **black leather gloves with
  gold-edged studded cuffs**; **quilted studded pauldrons** and a **studded upper-arm band**.
- Feeds: NPC species model (Narn) · `16-signage-typography-ui` (Narn script) · Narn quarters

### 15-races-and-makeup/vorlon.webp  ·  **the best Vorlon reference in the folder**
- Source authority: **2** (production/publicity photograph — it carries a burned-in studio slate,
  **"BAB5-06 / BABYLON 5 1997"**, bottom left). 960×1200. Shot against a blue set flat.
- Depicts: **Kosh's encounter suit**, evenly lit, in the clearest detail we hold.
- Extracted:
  - **Head assembly = two lateral shells + one central hood.** The lateral shells sweep forward
    and inward like curved mandibles; the hood rises over the face between them. Each lateral
    shell carries a **scalloped, fluted crest comb** (~10 ribs) at its top rear.
  - **Shell finish:** **mottled tan / olive / amber, with a dark net of veining separating rounded
    cells** — a cobblestone or turtle-shell pattern — under **wet high-gloss lacquer** with
    iridescent green and purple in the highlights.
  - **Inside each lateral shell: a dark blue fan of fine radial ribbing**, like a pleated gill.
  - **Face:** a flattened **chevron/heart-shaped plate** carrying a **single round dark eye lens
    in a metallic rim**, a small stud beside it, and a thin dark slot across the top.
    **No red lamp.**
  - **A bright green, ridged, segmented chitinous tube** (~15 segments, tapering) lies in a cradle
    on the shoulder. **`More Vorlon.jpg` shows one on each side, so they are a symmetric pair.**
  - **Tapered horn/wood rods with hollow cut ends** protrude at both shoulders — three on one
    side, two on the other in `Vorlon moree.jpg`.
  - **A small oval port with a raised lip** low-centre on the collar shell, and a second oval
    socket on the lower right shell.
  - **Breast:** a broad **mosaic bib of irregular flat stones** — blue-grey, tan, white and rust,
    laid crazy-paving — with a **white crackle-glaze half-collar** behind at the right.
  - **Robe:** long vertical panels of **black coarse fabric flecked with white/silver**, alternating
    with **mosaic-tiled vertical straps** and a **carved tan leather strap with a repeating
    knotwork relief** down the centre right. Beneath the bib, a **dark blue-green crazed leather
    panel**.
- Feeds: NPC species model (Vorlon) · alien sector environment

### 15-races-and-makeup/Vorlon moree.jpg
- Source authority: **2** (behind-the-scenes set photograph — grey studio flats, blue-taped floor,
  set pieces in shot). 646×960.
- **The only full-height view of the suit we hold**, and that is its value.
- Extracted:
  - **Silhouette:** a **tall tapering column**, widest at the shoulders, **floor-length with no
    visible legs**. It stands like a monolith. The robe hangs in a slight A-line.
  - Confirms the **green segmented tube**, the **horn rods (3 left, 2 right)**, the **mosaic bib as
    a downward-pointing triangular apron**, **two long vertical mosaic straps** flanking it, and
    the **embossed tan leather strap with a repeating knotwork/vine relief**.
  - Bottom-front centre: a **plain dark blue-black panel** forming the body front.
- Feeds: NPC species model (Vorlon) — proportions and standing silhouette

### 15-races-and-makeup/Kosh.webp
- Source authority: **1** (on-screen footage). 1200×900. Close-up of the head assembly.
- Extracted, adding to the two production photographs above:
  - Under **white station lighting** the shell reads **warm tan and olive-brown** with the same
    marbled veining. Confirms the material colour independently of the publicity lighting.
  - **A dark socketed opening** on the inner face of each lateral shell; **ribbed dark fluting** in
    the recesses behind them.
  - The **eye socket carries a glossy green-gold iris** when catching light.
  - **Background:** a pale grey wall with **blue vertical edge strips** and a light panel — station
    interior, not a set flat.
- Feeds: NPC species model (Vorlon)

### 15-races-and-makeup/Vorlon and captain.webp
- Source authority: **1** (on-screen footage). 1440×1080.
- **Era caveat: the human is in the Season 1 command uniform** — **teal blue-green** jacket with a
  dark leather bib and **pale silver shoulder boards**, which is the S1 pattern, not the S2–3
  slate-blue-with-crimson-piping. Valid set reference, invalid costume reference.
- Extracted — **the room, which is the useful part**:
  - **Left wall: a lavender-lit wall of fine horizontal slat panelling**, carrying a **large
    portal/door frame** with a **chamfered dark outline** and an **angular hooked graphic motif**
    applied to it.
  - **Behind Kosh: a wall of large frosted white panels in a dark grid** — the same "frosted grid
    wall with backlit panels" recorded for `more vorlon.png`. **Cross-link: these two files show
    the same location**, which is useful because they show two different suits in it.
  - A **black flexible vertical conduit** runs up the wall beside Kosh.
  - Foreground: a grey table with **two clear glass decanters** — a taller one with a **faceted ball
    stopper** and an amber neck band, and a shorter **dimpled/bubbled** one — plus a small
    **mosaic-tiled vessel**. Good prop set for an ambassadorial reception.
  - Kosh full upper body: the encounter suit's **vertical mosaic strips and two thick woven brown
    cords** run down the front and sides; floor-length, no legs.
- Feeds: alien sector / ambassadorial interiors · `11-props-and-technology` (glassware)

### 15-races-and-makeup/More Vorlon.jpg
- Source authority: **1** (on-screen footage). 1100×825.
- Depicts: Kosh's head in a **magenta/violet-lit environment**.
- Extracted:
  - **The shell's on-screen colour is lighting-dependent.** Here it reads **cool purple-brown**;
    under white light (`vorlon.webp`, `Kosh.webp`) the same shell reads **warm tan/olive**. Build
    the material warm and let lighting do the rest — do not bake a purple albedo.
  - **Both shoulders carry a green segmented tube.** They stay teal-green even under magenta,
    which is how we know they are green and not a lighting artefact. **Symmetric pair, confirmed.**
  - The **fluted comb crests** are at their clearest here — a scalloped fan of about ten ribs at
    the top rear of each lateral shell.
  - The **inner face plate glows dark teal-green** with a small green point of light.
  - **Background — a strong environment motif:** a vertical panel of **irregular polygonal pastel
    cells outlined in dark leading** (pale green, blue, cream, lilac) — a stained-glass or
    cell-mosaic wall — against **crumpled purple drapery**.
  - **Design insight worth keeping:** the same **cellular tessellation** appears on the encounter
    suit's mosaic bib and on the wall behind it. Vorlon design language is cellular at both prop
    and architecture scale. That is a rule the alien-sector kit can be built on.
- Feeds: alien sector environment · NPC species model (Vorlon)

### 15-races-and-makeup/more vorlon.png  ·  **CORRECTS the existing entry**
- Source authority: **1** (on-screen footage). 2737×1955, but that size is an **upscale** — the
  real detail is broadcast resolution. The existing entry is right about that.
- **Correction, and it matters.** The existing entry calls this **"Kosh's encounter suit"**. It is
  **not**. Compared side by side with `vorlon.webp`, `Kosh.webp`, `Vorlon moree.jpg`,
  `Vorlon and captain.webp` and `More Vorlon.jpg`, this is a **structurally different suit**:
  | | Kosh's suit (five files above) | This suit (this file + `even more vorlon.jpg`) |
  |---|---|---|
  | Head | two lateral shells + central hood | **boxy central face plate + four upswept horn blades** |
  | Eye | dark lens in a metallic rim, no lamp | **single bright RED lamp in a raised bezel** |
  | Texture | marbled tan/olive, rounded cells | **hexagonal scale cells, purple-blue** |
  | Shoulders | **green segmented tubes**, horn rods | none |
  | Crest | scalloped fluted combs | smooth swept blades |
  - The standard identification of the second suit is **Kosh's successor (Kosh II / Ulkesh)**, who
    arrives in **Season 4**. I cannot confirm the episode from the frame alone, so this is stated
    as the strong reading rather than as certainty.
  - **Consequence: treat this file as out of era pending confirmation.** Do not use it for an
    S2–3 Vorlon NPC. Use Kosh's suit — `vorlon.webp` is the reference of record.
- Extracted (the descriptions in the existing entry are accurate *for this suit*):
  **iridescent purple-blue shell with a hexagonal scale texture**; **curved horn blades sweeping
  back over the crown**; a **single red eye lamp in a recessed socket**; a layered mantle over a
  dark robe; a **hanging pendant plate with an ornamented lozenge** at chest height.
  Background: the **frosted grid wall with backlit panels**, in vapour — the same wall as
  `Vorlon and captain.webp`.
- Feeds: alien sector environment (the wall) · NPC species model **only if the era flag is cleared**

### 15-races-and-makeup/even more vorlon.jpg
- Source authority: **1** (on-screen footage). 1100×825. **The same second suit as
  `more vorlon.png`** — see the correction above. Same era flag.
- Extracted at 4–5×, and this is the clearest view of that suit's head:
  - **Central face:** a **rounded rectangular plate** mottled with **hexagonal/rounded cells** —
    dark grey-purple with **dusky rose cell centres** — surmounted by a **C-shaped horseshoe rim
    opening forward**, and flanked by **two large smooth upswept blades**.
  - **A single bright red circular lamp** low-centre on the face plate, in a raised bezel.
  - **Pale ribbed fan structures** (3–4 curved ribs each) below and to each side of the face,
    like fingers or gills.
  - **The pendant, at 5×:** a **trapezoidal plaque in a raised gold-brass frame**, its field a
    **dark crazed stone texture of irregular polygonal cells**, with a **pale triangular inclusion**
    at the bottom centre. Above it sits an **oval port with a raised lip** — the same fitting as on
    Kosh's suit. **So the oval port and the cellular crazing carry across both suits**; the
    lineage is real even though the suits differ.
  - Two humans in the foreground; one wears a dark uniform with a **round red/white/gold shoulder
    patch**. Too dark to identify at this resolution, so it does not date the frame.
  - Background is a flat saturated blue.
- Feeds: alien sector environment · **not** S2–3 NPC costume

### 15-races-and-makeup/Pak'ma'ra even more.jpg  ·  **the highest-authority file in this folder**
- Source authority: **3 (licensed print)** — and this is exactly the file that "looks unpromising"
  at 250×350. At 5× it resolves as a **Babylon 5 licensed trading card**: a **teal vertical caption
  bar reading "Pak'ma'ra"** down the left edge, and bottom left the **BABYLON 5 logo with a large
  chrome "5"** over a **red banner reading "SEASON FOUR"**.
- **What it gives us that nothing else does:**
  - The **canonical spelling of the species name, "Pak'ma'ra"**, apostrophes and all, at authority
    3. Worth having before any NPC or signage names it.
  - A **licensed card layout**: teal name bar, chrome-5 logo lockup, red season banner.
  - **Season stamp: FOUR.** The *card set* is Season 4; the pak'ma'ra makeup and costume are
    unchanged across seasons, so the subject remains valid S2–3 species reference. The stamp dates
    the print, not the design.
- Extracted from the photograph at 5×:
  - **Fine dark speckling over the crown**; **deep radial wrinkles** around the single visible eye;
    the eye has a **heavy hooded lid and a dark brown iris**; a **pronounced fore-aft keel ridge**
    runs along the crown.
  - **Four thick tapering tendrils** hang from below eye level past the chin, the outer two
    longest; **fleshy, ringed with fine transverse creases**.
  - Costume: a **coarse open-work crocheted/macramé mantle in rust-brown**, a **gold crescent clasp**
    at the throat, and a **vertically striped underrobe** alternating cream-lace and dark bands.
- **Same costume, same shoot as `more Pak'ma'ra.webp`** — same clasp, same mantle, same striped
  underrobe. The head angle and colour grade differ, so it is a different frame from the same
  session rather than the same frame. Stated as probable, not certain.
- Feeds: NPC species model (pak'ma'ra) · species naming · `16-signage-typography-ui` (licensed
  logo lockup)

### 15-races-and-makeup/more Pak'ma'ra.webp
- Source authority: **2** (production photograph — it carries a hand-written red **"222"**
  annotation bottom left, which reads as a continuity or catalogue number). 757×1237. The
  largest and cleanest pak'ma'ra reference we hold.
- Extracted:
  - **Head:** large, smooth, **domed hairless cranium** in **pale blue-grey/green**, with fine
    wrinkling radiating from the eye socket. Skin is **matte**, fading to **bone-cream** at the
    tendrils, heavily creased at the neck.
  - **A single large dark eye** in profile — round, dark brown iris, heavy wrinkled lids, deep-set
    in a bony socket. The eyes sit **far apart on the sides of a narrow head**.
  - **Four pale tendrils** droop from the lower face where a mouth would be — two long outer ones
    reaching mid-chest, two shorter inner. **No visible nose or mouth aperture**; the tendrils
    replace both.
  - **Costume:** a hooded/cowled **dusty mauve-brown robe** in a **dense raised paisley/scroll
    brocade**; a **grey-green ribbed undergarment** at the chest; a **small gold crescent clasp**
    at the throat holding the mantle.
  - **Background: dense green foliage.** Either shot in the garden/drum planting or against a
    greenery set — worth knowing if pak'ma'ra NPCs are to be placed.
- **Skin tone varies between individuals.** This one is pale blue-grey; `Pak'ma'ra example.webp` is
  mottled tan and olive. Build the species with a tone-variation parameter rather than one skin.
- Feeds: NPC species model (pak'ma'ra)

### 15-races-and-makeup/Pak'ma'ra example.webp
- Source authority: **2** (makeup close-up, reads as a production or reference-book photograph).
  319×507.
- Extracted:
  - **Mottled tan / ochre / olive blotching** over a wrinkled pale ground — a markedly different
    colourway from `more Pak'ma'ra.webp`. Confirms the tone-variation point above.
  - **Small deep-set dark eye**, hooded; **four to five tapering tendrils** from the lower face,
    the central pair longest.
  - Dark hooded garment, no ornament visible.
- Feeds: NPC species model (pak'ma'ra) — skin variation

### 15-races-and-makeup/Pak'ma'ra.webp  ·  **carries an in-frame named sign**
- Source authority: **1** (on-screen footage). 679×644.
- Depicts: a pak'ma'ra seated at a curved desk among **other alien delegates** — this reads as the
  **League of Non-Aligned Worlds assembly / Council seating**, which makes it Green Sector
  reference as much as species reference.
- **Extracted — the sign.** Set into the front edge of the desk, in a **dark recessed panel under a
  pale desk lip**, is a **species name-plate in white sans-serif caps**. Zoomed to 12× it reads
  **"HYAC…"**, the remainder occluded by the delegate's robe. Near-certainly **HYACH**, a League
  member species — stated as the reading, flagged as partial.
  - **This establishes that the assembly desks carry per-delegation name-plates**, their style
    (white caps, dark recessed panel, below the desk lip) and their position. That is a concrete,
    buildable set-dressing fact for the Council Chamber, at authority 1.
- Extracted — the room:
  - Pale wall of **vertical light strips** — alternating warm-white bars and darker gaps — over a
    **horizontal base band carrying small blue rectangular inserts**.
  - **A backlit white desk surface** in the foreground: the delegate desks are lit from within.
  - Delegates in frame: two pak'ma'ra, an alien in a **dark green reticulated/scaled garment**, and
    a **red-skinned bald humanoid** behind. A dense, mixed-species seated crowd.
- Extracted — costume: the pak'ma'ra wears a **cream/bone quilted or basket-woven mantle** with a
  high collar and a **magenta sash with a gold chain-link ornament** down the front; the second
  pak'ma'ra wears a **red-and-cream patterned robe with a gold chain**. So pak'ma'ra formal dress
  is individually varied, not a uniform.
- Feeds: Green Sector / Council Chamber fit-out · `16-signage-typography-ui` (delegation
  name-plates) · NPC species model (pak'ma'ra)

---

## Corrections to the index made in session 2s

1. **`Starfury more.jpg` and `earth alliance fighter.jpeg` are the same 900×1350 image**, not "a
   duplicate at a different size". They differ only in JPEG compression. `Starfury more.jpg` is
   the better copy.
2. **`more vorlon.png` is not Kosh.** It is a second, structurally different Vorlon encounter suit
   — red eye lamp, hexagonal scaling, horn blades, no green shoulder tubes — almost certainly
   Kosh's Season 4 successor. The existing entry attributes it to Kosh and offers it for NPC
   modelling; both are now flagged. `vorlon.webp` is the Vorlon reference of record.
3. **The EarthForce emblem on the two vector sheets is not "a winged chevron in a hexagonal
   outline".** It is a wide gold-outlined bowtie/flattened-X device on navy, with a small gold tab
   on the top edge and a three-bar stylised "E" filling the right half.
4. **The Season-1-vs-S2–3 uniform discriminator is now explicit:** S2–3 has **crimson piping and a
   leather bib**; Season 1 has **neither**. Previous entries flagged the era without saying how to
   tell.
5. **`Galen.jpg` is *Crusade*, not Babylon 5.** Out of scope entirely, not merely out of era. It
   matches neither existing quarantine signature, so it has not been moved — but it must not be
   used, and a `zz-out-of-scope-spinoff/` folder is recommended if more such files appear.

---
---

# Session 2t — verification pass over the 2r / 2s sweep

Four agents catalogued seven folders in sessions 2r and 2s (75 of the 83 live files). This pass
did **not** re-catalogue them. It did four things: counted the files on disk against the `###`
headings; re-opened a sample of entries and compared them against the frame; checked the
authority ratings for crisp modern renders passed off as footage; and checked whether anything
claimed to resolve C-003 or C-004 without the evidence.

**Headline: the sweep holds up.** Twelve entries were re-opened at magnification and eleven were
accurate to what is in the frame, including every measurement that was offered with a method.
The four measured/computed claims that could be re-run — the shield's six stars and its palette,
the EarthForce logo's two-colour split, the drum end-cap circle fit's method, and the `LEVE…`
plaque — all reproduced. Nobody catalogued a quarantine file as show reference. Nobody claimed to
resolve C-003 or C-004; every note in `canon/CONFLICTS.md` states the opposite explicitly, and two
of them **retract** earlier supporting arguments, which is the right direction of travel.

**Files re-opened in this pass:** `Sheridan.jpg`, `babylon 5 shield.webp`, `earthforce logo.webp`,
`grey level 1.webp`, `Doug's Dugout.webp`, `Pak'ma'ra.webp`, `exterior more.jpg`, `garden.png`,
`talia-winters in gorgeous office.webp`, `more zocalo signage.webp`, `kosh's transport.webp`,
`starfury even more detailed.jpeg`, `identicard readout.webp`, `council chambers.webp`, plus
`02-station-cutaways-and-plans/Exterior map.jpg` and `other map 4.jpg` from the uncatalogued
remainder.

---

## The one finding that changes an authority rating

### `01-station-exterior/exterior more.jpg` is rendered from the same 3D model as the Lawrence D. Miller sheets — it is **not independent** of them

The session-2r entry above rates this file **authority 2**, on the stated grounds that "the
*projections* are orthographic renders of the production CGI model and are trustworthy as
geometry", while conceding the *sheet* is fan-assembled wallpaper. **The provenance of the model
was asserted, not shown.** This pass tested it, by opening the uncatalogued
`02-station-cutaways-and-plans/other map 4.jpg` — the **Lawrence D. Miller "SHEET 2: TOP VIEW"**
plate, © 2004, 2014 Lawrence D. Miller, an acknowledged **authority-4** fan technical-drawing
series that `00-MASTER.md` already draws its specification table from.

Miller's sheet carries two small renders of the station, one at the top left and one along the
bottom rule. **They are the same model as `exterior more.jpg`, on four independently checkable
features:**

1. **Radiator blades:** royal-blue tapered lozenges with a pale structural border, three above the
   spine — same colour, same taper, same root fitting.
2. **Dorsal cargo modules:** a row of **brick-red** rectangular modules on a raised dorsal rail.
   Counted in `exterior more.jpg`'s top view at 6×: **exactly six** (this confirms the 2r entry's
   "six, not 5–6"). Miller's bottom render shows the same red row.
3. **Fore end structure:** a disc of concentric bands with a **red lamp at the dead centre** —
   visible in Miller's top-left three-quarter thumbnail and in `exterior more.jpg`'s fore end view.
4. **Hull palette:** lavender/indigo panel bands over pale grey, which is not the grey-blue the
   station reads as in broadcast footage.

**What this does and does not establish.** It does *not* prove the model is fan-built — Miller's
sheet carries a "Selected images and screenshots © 1993, 1994 PTN Consortium and Warner Bros.
Television" credit, so he may be using licensed renders. What it *does* establish, and this is the
part that matters, is that **`exterior more.jpg` and the Miller sheets are one source, not two.**
Any argument that treats them as independent corroboration of each other is circular.

**Recommended rating: `2, provisional — provenance unestablished; same model as the authority-4
Miller sheets`.** Not changed in the 2r entry above, because the geometry may well be sound and
downgrading it would silently invalidate applied schema work; recorded here and in
`canon/CONFLICTS.md` so the independence claim is not reused.

---

## Corrections made directly in this pass

1. **`04-sector-red/Doug's Dugout.webp` — dartboard numerals.** The 2r entry transcribed
   "14, 21, 8, …". **21 is not a number on a dartboard.** Re-read at 8×: **14, 11, 8, 16, 7** down
   the left, **19, 3, 17** across the bottom, **13, 6, 10, 15, 2** down the right. Corrected in
   place. The corrected reading is the *stronger* claim — those are exactly the real board's
   sequences, so the prop is a correctly laid out standard board, not a dartboard-like dressing.
2. **The *Still uncatalogued* section was stale** and listed four files that had since been
   catalogued while omitting `other map 4.jpg`, which never had an entry at all. Rewritten against
   an actual file-vs-heading count.

---

## Confirmed at magnification, so a later session need not re-check

- **`Sheridan.jpg`'s station wireframe is real and reads as described.** Six two-limbed forked
  blades, three above the spine and three below, each converging to a small rectangular end pad;
  six blue leaders from a dorsal row of small square modules to six indicator boxes headed
  **AUTO LOADERS SEQUENCE**; three truncated-cone callout balloons and an X-quartered disc; the
  ribbed drum with an inner axial tube. **One qualification:** the view is not a *pure*
  orthographic side elevation — the dorsal modules show their top faces, so there is a few degrees
  of elevation in it. That does not damage the coplanar reading (a 60°-spaced radial array would
  still foreshorten visibly from this angle) but the entry's "a pure side elevation would show
  edge-on blades as lines" is a slightly stronger premise than the drawing supports.
- **The ATMOSPHERIC LIFE SUPPORT REGULATORS callout is four boxes and three leaders**, exactly as
  the index entry discloses. The boxes are drawn in the *same graphic language as the AUTO LOADERS
  boxes* — chevron indicator lamps, one of the set in a different state — so they read as **status
  channels on a monitoring board**, not as four hull fittings. `canon/CONFLICTS.md` states the
  count without that qualification; a note has been added there.
- **`grey level 1.webp`:** at 16× with a contrast stretch, the plaque is pale uppercase on a dark
  ground reading **L-E-V-E**, and it **runs off the right frame edge**. The 2r correction is right
  and the number genuinely is not in the picture. The far-end backlit aperture does show dark
  diagonal wedges at **all four corners** — the octagon reading is confirmed.
- **`babylon 5 shield.webp`:** connected-component analysis reproduced independently — six white
  blobs of ~1290 px in 55–57 px boxes, three at x≈517 (y 98/288/464) and three at x≈73
  (y 331/521/697). Palette within 0.4 pp of the figures in the entry. **Six stars, three and
  three.** The `#FFCE00` / `earthforce logo.webp` palette identity also reproduces.
- **`garden.png`:** the overhead structure is a **long open lattice girder with diagonal web
  members**, with a **junction node** carrying **three tubular arms**, each a segmented cylinder
  with ring collars. The 2r re-reading (radial transport spoke, not the axial spine truss) is
  supported by the frame.
- **`talia-winters in gorgeous office.webp`:** the window does look into the drum. Segmented axial
  struts with salmon collar joints, the far side arching overhead in longitudinal bands with one
  broad orange-red band, low-rise flat-roofed buildings on open ground. As described.
- **`more zocalo signage.webp`:** the wordmark is the largest and most legible in the set, the
  neon is drawn as a **hollow tube** (two bright contours, dimmer interior), and the caption reads
  verbatim `(Bester) 'So...obviously things back home have been a little tense'`.
- **`identicard readout.webp`:** the zeros in `12/10/25` are **plain rounded rectangles** — no bar,
  no slash, no dot. The 2s strike of the "barred zero" claim is correct, and the Eurostile /
  Microgramma identification holds (flat-topped 2, rounded-rectangle O, flat-terminal S).
- **`council chambers.webp`:** the bench is a **straight run meeting a mitred corner**, not a swept
  curve. The 2r correction is right. Its front face is a fine perforated grille, which is the same
  backlit-from-within construction the `Pak'ma'ra.webp` nameplate sits in.
- **`Pak'ma'ra.webp`:** the desk-edge nameplate reads **`HYAC…`** at 12×, pale caps in a dark
  recessed panel under a pale desk lip, remainder occluded. As described.
- **`kosh's transport.webp`:** period CGI, authority 1 correct. The overhead space-frame, the
  stalk-hung fittings with stepped collars and downward barrel clusters, the studded gangway and
  the plant-room bay floor are all in the frame.
- **Authority ratings spot-checked and correct**, including the one that most invites the mistake:
  **`12-starfury/starfury even more detailed.jpeg` is a modern PBR turntable render on a studio
  gradient and is rated 4**, not 1. `Pak'ma'ra even more.jpg` really is a licensed trading card
  (teal caption bar, chrome-5 logo, "SEASON FOUR" banner) and 3 is right — though note the card is
  **Season Four**, outside the S2–3 era lock, and it is the *photograph on* an authority-3 artefact,
  which is nearer authority 2 content in an authority-3 wrapper.

## Quarantine check: clean

Every one of the 83 live files was checked for the two quarantine signatures. **No file in any of
the seven swept folders matches the 2023 animated feature or an AI generator**, confirming the
2r and 2s findings. The only `###` heading pointing into a quarantine folder is
`21-QUARANTINE-animated-film/delen and sheridan in elevator.jpeg`, and that entry exists precisely
to record the downgrade — it says "do not model from it" and explicitly notes it does not bear on
C-004. That is correct handling, not a miscatalogue.

Two files already flagged elsewhere and repeated here so they are not lost: **`Galen.jpg` is
*Crusade*** (out of scope, not merely out of era) and **`Doug's Dugout.webp` contains a real ZIMA
product placement** which must not be reproduced.

## Session 3b upload — `10-interiors-generic-kit/`

Eight files. **Three are duplicates of material already held** and are flagged here so no session
re-mines them expecting new information:

| file | status |
|---|---|
| `more hallway.jpg` | **NEW**, authority 1. Concourse-class volume: large elliptical ribs, an EarthForce officer standing in a circular downlight pool (the project's only direct absolute length in an interior — 1.57 m), wall screens, dark blue-grey palette |
| `more hallways.jpg` | **NEW**, authority 1. Service-class corridor: overhead truss, vertical light tubes, chequered lit strip in deck grating running to the vanishing point, warm backlit panels, litter on the deck |
| `more zocalo.png` | **NEW**, authority 1. The Zocalo — neon sign, upper gallery with pedestrians, pale tiled deck, pedestal café tables, tubular "5" chairs, vendor stalls with awnings, mixed-species crowd |
| `garden more.jpg` | **NEW**, authority 1 |
| `gardens or greenery.jpg` | **NEW**, authority 1 |
| `transport.jpg` | **DUPLICATE** of `03-sector-blue/Babylon_5_2-22_34b.jpg`, MD5 `e2bf2216d53aa9ba89342267db3f92f6`. Looked like it might break C-008 and cannot — same evidence, different filename |
| `central corridor.webp` | **DUPLICATE** of `09-garden-core-and-transit/central corridor.webp` |
| `grey level 1.webp` | **DUPLICATE** of `07-sector-grey/grey level 1.webp` |

This upload closed the project's largest reference gap. Before it,
`10-interiors-generic-kit/` was **empty**, and the corridor kit — 210 decks and 2,330 streaming
cells, the large majority of walkable space — was extrapolated from proportions in a single frame
of one sector. The three new interior frames establish that there are **at least three corridor
classes**, not one; see INV-020.
