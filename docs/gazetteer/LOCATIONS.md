# LOCATIONS — the Babylon 5 Gazetteer

Every named or shown place aboard Babylon 5, with what it is, where it goes, and how confident
we are about that. **Era lock: Season 2–3.** Sheridan commanding, Kosh present, defence grid
installed, Nightwatch active, pre-secession, pre-war-damage.

This document is a *placement* register, not a canon source. It is downstream of
`canon/00-MASTER.md` and `canon/CONFLICTS.md` and may not override either. Where it disagrees
with them, the disagreement is flagged in §2 rather than resolved here.

---

## 0. How to read this

### 0.1 Authority

| | |
|---|---|
| **1** | on-screen footage — a frame we hold in `reference/`, cited by path |
| **2** | production material — blueprints, production-model renders |
| **3** | licensed print — the two Security Manual sheets, Contract 5 |
| **4** | fan reconstruction — wikis, fan sites, forums |
| **5** | our own extrapolation, with the reasoning given |

**Every authority-4 row in this file came from a web source and is labelled so.** No web claim
is presented as canon and none silently overrides `canon/00-MASTER.md`.

> **Method caveat, stated once and applying to every authority-4 row.** This session's egress
> policy blocked direct page fetches (`403` from the proxy on `babylon5.fandom.com`,
> `midwinter.com`, `oocities.org`, `en.wikipedia.org`, `sites.google.com` and every other host
> tried). Authority-4 content was therefore read through **WebSearch result summaries**, not by
> reading the pages. The URL cited is the page the summary was drawn from. A future session with
> unrestricted egress should re-read these pages directly; a summary can drop a qualifier, and
> two of the contradictions in §2 turn on exactly that kind of qualifier.

### 0.2 Placement confidence

| | |
|---|---|
| **STATED** | a source states the placement outright. *Check the authority column for how good that source is* — an authority-4 STATED is a fan wiki asserting a thing, not the show saying it. |
| **IMPLIED** | not stated, but deducible from what is shown (e.g. the ceiling is the far side of the drum, so the room is on the drum floor) |
| **PROPOSED** | our reasoning. The reasoning is given in §9, keyed by the row's `P-nn` tag. |

### 0.3 The placement vocabulary — the project's own model

From `canon/CONFLICTS.md` C-003 UPDATE 2 and C-004 UPDATE:

- **Sector** — a **longitudinal band** spanning the full diameter. Six: Blue, Red, Green, Brown,
  Grey, Yellow.
- **Ring** — a **concentric radial zone**. Ring 1 is outermost and heaviest. `station/interior.py`
  carries five per sector (ring 1–4 plus core) as `provisional_rings`.
- **Deck** — one floor inside a ring, 3.6 m floor-to-floor (`DECK_PITCH_M`, INV-010, provisional).
  A ring is 38–61 m deep, so a ring is a dozen or more decks.
- **Cell** — the streaming unit, an angular slice of one deck. 18–20° in the current model
  (`station/interior.py::ring_cells`).
- **The drum is different.** Its habitable stack runs **outward** from the 278.3 m habitat floor
  to the 310.8 m pressure hull — 9 decks, 1.013 g to 1.117 g — and everything inboard of the
  floor is open air. Downbelow, in the drum, is *heavier* than the Garden.

**Two conflicts remain OPEN and BLOCKING and they constrain every row below:**

- **C-003** — which longitudinal band is the ~2,000 m habitat drum. The two authority-3 sheets
  transpose **Green and Brown**. So a drum row here says *"the drum sector (Green or Brown —
  C-003)"*, and that is the correct precision, not a hedge.
- **C-004** — which ring is level 1, and how many levels a sector has. So no row asserts an
  absolute level number of our own. Where an authority-4 source gives one (`Blue 2`, `Red 5`,
  `Green 23`) it is recorded **as that source's claim**, in the source's own words.

Relative placement is the house style. *"Outermost habitable ring of the drum sector, on the
drum floor"* is buildable. *"Green 3"* is false precision until C-003 and C-004 close.

### 0.4 Sector radii and gravity — for sizing, from `station/interior.py`

| sector | outermost deck | gravity | decks | cells/ring 1 |
|---|---|---|---|---|
| Grey | 402.2 m | **1.445 g** | 90 | 18 × 20.0° (140 m) |
| Green sub-floor (drum) | 281.9 m | 1.013 g | 9 | 15 × 24.0° (118 m) |
| Green habitat floor (drum) | **278.3 m** | **1.000 g** | — | — |
| Red | 211.8 m | 0.761 g | 45 | — |
| Blue | 167.7 m | **0.603 g** | 37 | — |
| Yellow | 137.1 m | 0.492 g | 29 | — |

Walking Blue → Grey is a **2.4× change in weight**. That is free and it is a headline feature;
it should drive where things are *placed*, not just how they look.

### 0.5 The "built?" column

| value | meaning |
|---|---|
| `no` | nothing exists |
| `shell` | the enclosing volume is generated but the place is not distinguished inside it |
| `kit` | the generic corridor/room kit would build it; nothing specific authored |
| `ext-crude` | a box primitive exists on the exterior hull |
| `physics` | the *behaviour* is simulated (`station/physics/`) but there is no geometry |

---

## 1. THE HEADLINE FINDING — the address scheme may not be a level at all

This is the most consequential thing this research turned up and it goes first because it bears
directly on **C-004**, which is blocking all interior level geometry.

The Babylon 5 Wiki states, of the rotating sectors:

> "These sectors were divided up into **36 regions, each region consisting of a 10-degree arc**
> and were numbered; **Blue 01 to Blue 36 and Red 01 to Red 36** for example."
> — authority 4, https://babylon5.fandom.com/wiki/Babylon_5

**If that is right, the number in `Grey 17` is an angular segment around the circumference, not a
radial deck.** C-004 has been framed as "which ring is level 1" for four sessions. This source
says the number may not index rings at all.

It is not a clean finding, and the mess is itself informative:

1. **The same wiki contradicts itself.** It also describes the placards as
   "applying a **level** / area name to the location (i.e. `Blue-3`, `Red-5`, `Green-2`,
   `Brown-57`, `Grey-16`)" (authority 4, same URL), and a second fan source gives
   "a colour denotes the sector, … a number denoting a **level** … **lower numbers are closer to
   the central axis**", with the main corridor at `Blue 15`
   (authority 4, https://www.oocities.org/davesb5page/xplor.htm — attribution uncertain, see §0.1).
2. **`Brown-57` breaks both readings.** 57 > 36 regions, and 57 > the 30 levels the same wiki
   gives Grey Sector. Whatever the scheme is, one of these placards does not obey it.
3. **"Lower numbers closer to the central axis" is a direct answer to C-004's question** — level 1
   innermost, numbering outward — and it is *authority 4 from a fan site*, which cannot close a
   conflict that two authority-3 sheets could not.

**Ruling for this document: C-004 stays OPEN. Nothing here is used to number a ring.** But three
things follow that are worth acting on:

- **A third possibility now exists** and should be added to C-004's list of readings: `<Colour>
  <number>` may be **sector + angular segment**, with the deck addressed separately or not at all.
  That would explain the standing puzzle in C-004 — *no source numbers a ring* — by the simplest
  route available: because rings are not what the numbers index.
- **It is consistent with our own geometry in a way the radial reading is not.** 36 × 10° is
  exactly the streaming-cell axis `station/interior.py::ring_cells` already divides. Grey ring 1
  is **18 cells × 20°** — precisely **two regions per cell**. Green sub-floor is 15 × 24°, which
  is **not** a divisor of 36. If the 10° scheme is ever adopted, cell counts must be drawn from
  {36, 18, 12, 9, 6, 4, 3, 2}, and 15 has to go. That is a concrete, cheap change to make later
  and an expensive one to retrofit after cells carry authored content.
- **The number of levels may be far smaller than the number of decks.** The wiki gives Grey
  **30 levels** (authority 4, https://babylon5.fandom.com/wiki/Grey_Sector); our model gives Grey
  **90 decks** at 3.6 m. 90 / 30 = 3 exactly. A "level" being ~3 decks (10.8 m) is arithmetically
  tidy and is consistent with session 2k's authority-1 finding that a level can contain a
  mezzanine. **Authority 5, speculative, recorded so it can be tested rather than rediscovered.**

---

## 2. CONTRADICTIONS WITH THE PROJECT'S CANON

Reported, not smoothed over. None of these is resolved here.

| # | The claim | Conflicts with | Assessment |
|---|---|---|---|
| **X-1** | "There are **four cobra bays** on the station, one on each of the four structural elements of the forward sphere" — auth 4, https://www.oocities.org/davesb5page/xplor.htm | `00-MASTER.md` §1.3: **28** (Contract 5, auth 3) or 24 (Miller, auth 4); C-002 | **Probably not a contradiction — probably the reconciliation.** `00-MASTER.md` §2 item 20 already lists "cobra launch bay support arms **(4)**". Four *arms* each carrying seven *bays* gives 28. This does not close C-002 (which is 24 vs 28) but it removes the appearance of a third figure. |
| **X-2** | The **Alien Sector** is "located between the docking bays and Red Sector" — auth 4, https://babylon5.fandom.com/wiki/Green_Sector | The Security Manual sectional schematic (auth 3) puts "multi-environ 'alien' sector" in **band 3, the band it labels Green**, at ~3,613–3,997 m — i.e. *aft* of the drum, nowhere near the docking bays | **Real contradiction, authority 3 wins.** But note the fan claim would put the Alien Sector between Blue and Red, which under the schematic's own ordering is a ~370 m band. Unresolvable without C-003. |
| **X-3** | Sector order aft→fore is **Yellow (non-rotating) · Grey · Brown · Green · Red · Blue** — auth 4, https://babylon5.fandom.com/wiki/Babylon_5 and /Grey_Sector ("Grey … the furthest section of the carousel aftward, just aft of Brown Sector") | The Security Manual sectional schematic (auth 3) gives Yellow · Grey · **Green · Brown** · Red · Blue | **A sixth pointer for `other map.png`, and the first that is a reading of an ordering rather than an inference about a draughtsman's intent.** It agrees with `other map.png` exactly, *including* Yellow as the non-rotating aft half — the point on which `other map 2.jpg` was outranked. **But it is very likely an echo, not a witness**: a fan wiki compiling the same licensed print sources is not independent of them. Authority 4 cannot break a tie between two authority-3 sheets. **C-003 stays OPEN.** Recorded in full because a future session will find this and must find it already weighed. |
| **X-4** | Grey Sector has **30 levels** — auth 4, https://babylon5.fandom.com/wiki/Grey_Sector | `station/interior.py` `cell_manifest()`: Grey has **90 decks** | Not a contradiction if a level ≠ a deck. See §1. It *is* a contradiction if anything downstream assumes level count = deck count. Nothing currently does. |
| **X-5** | The Zócalo is "located in **Red 5**" — auth 4, https://babylon5.fandom.com/wiki/Z%C3%B3calo | Nothing directly. But `other map.png` (auth 3) puts Zocalo in Red's **outermost** ring | Compatible under the angular reading of §1 (Red 5 = a 10° wedge of the outer ring). Incompatible under the radial reading unless ring 5 is outermost, which would invert C-004. **A test case: whichever reading of C-004 makes `Red 5` land on the outer ring is the right one.** |
| **X-6** | "**Medlab**, Security headquarters, and the Judiciary were … located in **Red Sector**" — auth 4, https://babylon5.fandom.com/wiki/Ombudsmen; and "Medlabs … located in **Red, Green and Blue** Sectors" — auth 4, https://babylon5.fandom.com/wiki/Medlab | `other map.png` (auth 3): Law Courts and Security Central are in **Red's inner rings**; Medlab One is in the **Blue** rosette | **These agree**, and that is worth recording as a rare authority-3/authority-4 cross-check that holds. Medical is distributed across three sectors; the primary Medlab is in Blue; law and security are Red. |
| **X-7** | The **Sanctuary** is "a large circular room in **Blue 3** that looks out onto the stars"; the **Chapel** is in **Blue 4** — auth 4, https://babylon5.fandom.com/wiki/Blue_Sector | Contract 5 (auth 3) counts **Sanctuaries (4)** — a plural exterior system | Consistent in kind (a sanctuary is a real named facility) but the count differs: one named room vs four systems. The Blue 4 chapel citation is dated **2271**, which is S5/post-series — **out of era, excluded from the tables below**. |

---

## 3. COMMAND AND ADMINISTRATION

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Command & Control (C&C)** | The station's bridge. A raised circular command dais on a stepped plinth, a lower forward pit of red-lit consoles, stairs down to a third level at right; wedge-shaped angled console desks on slim legs; two courses of long horizontal cyan-white light strips at high and mid level. **Two occupied levels in one volume.** | Blue | Inside **Observation Dome 1**, forward docking structure | STATED | 1 | `reference/03-sector-blue/comand and contorl.webp`; Contract 5 (auth 3) names Dome 1 = C&C, `00-MASTER.md` §1.3 | `ext-crude` (dome is a box) |
| **Observation Dome 1 glazing** | The window C&C looks through: a large circle on **radial spoke mullions** with a broad concentric ring band, set in a flat-panelled bulkhead with angled bracing. Seen from inside in the same frame; must match the exterior `domes` component. | Blue | forward docking structure | STATED | 1 | same frame | `ext-crude` |
| **Observation Dome 2** | The second dome. Function unestablished by any source we hold. | Blue | forward docking structure | STATED (exists) / **unplaced by function** | 3 | Contract 5, `00-MASTER.md` §1.3 | `ext-crude` |
| **The War Room** | Strategic briefing room. A large backlit **galactic map mural** — spiral galaxy in blues under a red rectilinear sector grid with small yellow labels; a **circular holo table** with a pale blue volumetric projection; moulded swivel chairs; a curved console rail with a vertical white light ladder; an arched structural frame continuing the corridor chamfer language. | **unplaced** — no source assigns it | — | **PROPOSED — P-01** | 1 (the room) | `reference/03-sector-blue/war room.webp` | `no` |
| **Station commander's administration complex** | The command office suite. Named as a callout on the sectional schematic; its dot falls in **band 4**, which that sheet's own bracket does not label. | **unplaced — contested.** Blue on screen per C-003 UPDATE 2; the callout lands in band 4 | — | STATED (by an auth-3 sheet, in a band it does not label) | 3 | Security Manual sectional schematic; `canon/CONFLICTS.md` C-003 UPDATE 2 | `no` |
| **Babylon 5 Advisory Council chamber** | The council chamber. A **curved raised bench** with an angled slab top and a **perforated gold mesh front panel lit from within** — the furniture is the light source; high-backed chairs with open black lattice backs, one per delegation; back wall a **radiating fan of angled fins** under a large **circular spoked medallion** on deep blue; floor a **pale blue-green polygonal mosaic**. A fan of blue-and-white radiating panels on the bench marks the speaking position. | Green | Named in the **Green rosette** | STATED | 1 (the room), 3 (the sector) | `reference/05-sector-green/council chambers.webp`; `other map.png` Green rosette | `no` |
| **Conference / lounge area with the "5" floor roundel** | A lounge and observation area: the **Babylon 5 "5" roundel inlaid at large scale into a terrazzo floor** on a raised circular dais with a stepped kerb, a **cyan neon hexagon inlaid flush in the floor** around it, curved walls of tall narrow illuminated slots, cafe tables with red-glowing tops. | Green (folder attribution only) | — | IMPLIED | 1 | `reference/05-sector-green/conference aerea.webp` | `no` |
| **Conference rooms (general)** | Rentable meeting rooms in the diplomatic zone. | Green | with the ambassadorial suites | STATED | 4 | https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **Rooms for ceremonial and festive hire** | Several large rooms rentable for ceremonies, furnished by the **station quartermaster**. Direct support for the religious-festival and diplomatic-reception content the show runs on. | Red | — | STATED | 4 | https://babylon5.fandom.com/wiki/Red_Sector | `no` |
| **Earthforce Office** | An EarthForce administrative office in the diplomatic sector. | Green | Named in the **Green rosette**, outer ring | STATED | 3 | `other map.png` Green rosette | `no` |
| **Defence grid fire control** | The watch floor that points the defence grid. `00-MASTER.md` §1 lists **anti-fighter pulse cannons** at **authority 1**, and four documents state the era lock as *"defence grid installed"* — yet `pulse cannon` and `defence grid` appear in **no `.py`, no `.yaml` and no `exterior_systems` entry**. There are no emplacements outside and there was no gunnery control inside; `cnc` and `war_room` declare `defence_command` and command nothing. Sited at the cobra bays' own z so the fighters and the guns share a deck. | Blue | ring 1, deck 4 — 0.572 g | **PROPOSED — volume audit §5.1** | 1 (the cannons exist) / 5 (the room) | `canon/00-MASTER.md` §1; `docs/volume-audit.md` §5.1; INV-100 | `rooms` |

---

## 4. DOCKS, TRAFFIC AND CUSTOMS

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Docking bays (24)** | The main rotating docking bays. Interior is a **long low slot, not a hangar box**: very wide flat-topped mouth with the far side visible beyond; **red-orange painted structural steel** overhead in deep box girders and a lattice gantry carrying pendant floodlights at regular spacing; yellow/black hazard chevrons on ramp edges; a **large red disc with a white oval emblem** on the deck, many times a person tall. Bay walls are **stepped ledges** with chevrons on every step nosing; the ceiling is the **ribbed inner wall of the rotating drum**, curving. | Blue | Named in the **Blue rosette**; the Blue rosette has a **central docking hub on the axis** | STATED | 1 (interiors), 3 (count and sector) | `reference/03-sector-blue/dock.webp`; `.../Minbari Flyer 969 in docking bay 17.webp`; Security Manual "DOCKING BAYS (24)" | `no` |
| **Bay elevators (2)** | The lifts that move craft between the bay mouth and the interior. Large transports are explicitly **too long to use them** and berth in the low-g bays instead. | Blue | Named in the Blue rosette and on the sectional schematic | STATED | 3 | Security Manual "BAY ELEVATORS (2)"; auth 4 for the length limit, https://www.oocities.org/davesb5page/xplor.htm | `no` |
| **Low-g / zero-g docking bays** | Non-rotating bays for craft too large for the rotating section. Fan sources give **four**. This is where the axial-docking result in `station/physics/docking.py` applies: **an axial port has no tangential velocity to match at all.** | Blue (schematic) / Yellow (fan) | forward, on the non-rotating structure | STATED | 3 (existence), 4 (count of four) | Security Manual "LOW-G DOCKING BAYS"; https://www.oocities.org/davesb5page/xplor.htm | `physics` |
| **Customs (×2, north and south)** | Arrival and departure processing. Two of them, on the **North** and **South** sides — the Contract 5 lateral convention. The hall carries **backlit blue information boards**: *"Welcome to Babylon 5 · [CUSTOMS SECTOR] · ATMOSPHERE CAUTION — SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5…"* and *"…TIME ON B-5 IS EARTH MEAN TIME (EMT). MONETARY EXCHANGE RATES THROUGH BUSINESS CENTER"*. Identicards, visas and travel papers are checked here. | Blue | adjacent to the main docking bays | STATED | 1 (the hall and its boards), 3 (the count and sides) | `reference/01-station-exterior/welcome to babylon 5.webp`; Security Manual "customs (×2)"; `00-MASTER.md` §1.4 | `no` |
| **Arrival concourse** | The public space beyond customs: an illuminated **"WELCOME TO BABYLON 5"** sign, a wall monitor with a talking head, a **green vector wireframe station schematic** on the wall, two suspended information boards, and a crowd. This is the player's first room. | Blue | with customs | STATED | 1 | `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg` | `no` |
| **"Customs Sector"** | An **area label used alongside, not instead of, the six colour sectors** — signed on the customs boards themselves. Wayfinding must carry both naming systems. | — | — | STATED | 1 | same; `00-MASTER.md` §1.4 | `no` |
| **Cobra bays (28)** | Starfury launch bays on the rotating rim. The bay is framed by **heavy vertical structural columns**; the fighter is carried nose-out on a **lattice truss arm with a cradle**, not on a rail in a tube; yellow/black chevrons on every deck edge; orange-banded cylindrical tanks racked alongside. **No catapult is depicted and none is needed** — the drum's 52.2 m/s does it. | Blue | on the four **cobra launch bay support arms** | STATED (existence), count OPEN (C-002) | 1 (the bay), 3 (count 28) | `reference/01-station-exterior/Cobra Bays with starfurries.webp`; Contract 5 | `ext-crude`, `physics` |
| **Cargo bays (42)** | Internal cargo volumes — 28 in the rotating section, 14 in the support structure. **Distinct from the six external cargo modules** on the dorsal rail (session 2t). | Blue / Yellow | 28 rotating + 14 support | STATED | 4 (`other map 4.jpg`), 3 (the "cargo bay" callout) | `00-MASTER.md` §1.3; Security Manual | `ext-crude` (the 6 modules) |
| **Spinal cargo facility** | The bulk store: zero-g cargo transfer and "the bulk of the station's supplies", running the non-rotating spine. | Yellow | the non-rotating aft half | STATED | 4 | https://babylon5.fandom.com/wiki/Babylon_5 | `shell` |
| **Micro-gravity maintenance bays (2)** | Zero-g maintenance docks. | Yellow / Grey | on the spine | STATED | 3 | Contract 5; `00-MASTER.md` §1.3; the schematic's "zero-G maintenance fac." | `no` |
| **Quartermaster's Office** | Stores and issue. Also supplies furnishings for the rentable ceremonial rooms. | Blue | Named in the **Blue rosette** | STATED | 3 | `other map.png` Blue rosette | `no` |
| **Post Office** | Mail and parcels. | Blue | Named in the **Blue rosette** | STATED | 3 | `other map.png` Blue rosette | `no` |
| **Fuel stores** | Ship fuel bunkerage adjacent to the docks. | Blue | Named in the **Blue rosette** | STATED | 3 | `other map.png` Blue rosette | `no` |
| **Hard docking mooring clamps** | Retractable clamps for ships moored to the exterior rather than berthed. | Blue | forward docking structure | STATED | 3 | `00-MASTER.md` §2 item 23 | `no` |
| **A docking bay dressed as a plant room** | The bay in which the **Vorlon transport** berths, and the best-lit bay interior we hold: overhead **space-frame of square-section black tubes** with boxy nodes; **bulbous grey fittings on short stalks** hanging from the nodes, each with a stepped collar and a downward cluster of ~3 barrels; a **long flat pale gangway** on angled struts with a studded edge; a floor of **dense pale-grey greeble** — tanks, boxes, elbowed pipe runs, gratings, ladders. Effectively **unlit except by practicals**. | Blue | a docking bay | IMPLIED | 1 | `reference/13-other-ships/kosh's transport.webp` | `no` |
| **The jump gate** | **Off-station.** The local jumpgate near which B5 sits, at the L5 point of Epsilon III. Every arriving and departing ship transits it. It is the reason the station exists economically and it is the single most important piece of *off-hull* content for making the place feel alive. | off-station | — | STATED | 1 (the station's location, `00-MASTER.md` §1) / 4 (the L5 and gate detail) | `00-MASTER.md` §1; https://babylon5.fandom.com/wiki/Babylon_5 | `no` |
| **Space traffic proximity arrays (4)** | Traffic control sensors. C&C in Dome 1 handles all ship movement. | Blue | forward structure | STATED | 3 | Contract 5; `00-MASTER.md` §1.3 | `ext-crude` |
| **Primary navigation beacon** | The station's nav beacon, fore terminus. | Blue | fore terminus | STATED | 3 | `00-MASTER.md` §2 item 24 | `no` |
| **Cargo transfer deck** | The hold under the **six external cargo modules** on the dorsal magnetic rail. `components.cargo_module` builds them at z 4,870–6,010 — **1,140 m of magnetic rail and 0.3601 km³ of envelope with no hold, no handling deck and no manifest office behind it**, and no cargo place anywhere in Green. Racking down one flank, the rail's transfer carriage down the other, a hoist over the aisle. On the drum's sub-floor stack, so it is under the Garden and a player can reach it. | Green | ring 0 (sub-floor), deck 5 — 1.078 g | **PROPOSED — volume audit §4** | 5 | `docs/volume-audit.md` §2.3, §4; `station/components.py` `cargo_module`; INV-100 | `rooms` |
| **Mooring clamp gallery** | The gallery behind the hard docking mooring clamps: umbilical reels on one flank, clamp actuator housings on the other. `00-MASTER.md` §2 item 23 puts the clamps on the hull and the register's `mooring_clamps` is **a label with one interact and no geometry** — nothing a person could stand in to work them. | Blue | ring 0, deck 2 — 0.734 g | **PROPOSED — volume audit §2.4** | 5 | `00-MASTER.md` §2 item 23; `docs/volume-audit.md` §2.4; INV-100 | `rooms` |
| **EVA airlock and suit room** | Where B5's EVA crews suit up. `FACTIONS.md`'s EarthForce branch table allots **630** of the 6,500 crew to *"maintenance, repair, EVA"* — 630 people whose job includes vacuum work — and **there is no airlock on 8,047 m of hull and none in the register**: `airlock_door` appears in exactly two places' `interacts`, both of them Alien Sector *atmosphere* locks. A suit rack bank and a charging manifold either side of the lane to the lock. | Blue | ring 0, deck 1 — 0.747 g, beside the docking bays | **PROPOSED — volume audit §5.2** | 5 | `canon/FACTIONS.md` EarthForce branch table; `docs/volume-audit.md` §5.2; INV-100 | `rooms` |

---

## 5. COMMERCIAL AND SOCIAL

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **The Zócalo** | The station's main commercial concourse and its principal social space. **Two-storey**: an upper gallery with a **vertical-bar balustrade** where people stand and look down over a lower cafe floor, carried on **large tubular grey arch ribs with cross-bracing** — the exposed-rib motif at concourse scale. Beneath the gallery runs a strip of **shopfronts with blue and red backlit panels**. Deck is **large pale square tiles on a darker grout grid** with a band of yellow/red/blue diagonal chevron striping. Stall canopies are **fabric on radiating tan spars, parasol-fashion**, on a single mast; stall frames are **post-and-beam hung with strings of warm fairy lights on every member**. **Live planting in tubs**, including a mass of orange-red foliage tall enough to read as a small tree. Crowd is **dense and species-mixed**. | Red | Named in the **outermost ring** of the Red rosette. Fan sources say "**Red 5**" | STATED | 1 (the space), 3 (the ring), 4 (the "Red 5") | `reference/04-sector-red/more zocalo.png`; `.../zocalo.webp`; `other map.png` Red rosette; https://babylon5.fandom.com/wiki/Z%C3%B3calo | `no` |
| **The Zócalo neon wordmark** | **"Zocalo" in Latin letterforms**, a rounded single-stroke tube script with a dot in the counter of each 'o', a swashed Z and a triangular counter in the 'a'. **Orange-red** hung under the gallery deck in one frame, **cyan** over a portal in another — glyph-for-glyph the same wordmark. | Red | — | STATED | 1 | `reference/04-sector-red/more zocalo.png`; `reference/11-props-and-technology/Zocalo neon signage in background.jpg` | `no` |
| **The "5" roundel as furniture branding** | A **bold slab numeral with a black outer keyline and a white inline**, applied large to **cream drum panels** forming chair backs and table pedestals. The same glyph as the shield patch and the floor inlay — **one decal asset, three applications.** | Red (and everywhere) | — | STATED | 1 | `reference/04-sector-red/more zocalo.png`; `reference/16-signage-typography-ui/babylon 5 shield.webp` | `no` |
| **The Casino** | Gambling hall. A **monumental monochrome industrial mural** fills the back wall, Rivera-like, machinery and labouring figures — the largest flat art surface in the whole reference set and the defining piece. Lit by **two large backlit grid panels**, one at each end of the mural; the mural itself is unlit and reads by spill. A **wheel of fortune with a ring of ~24 filament lamps** and a cyan-and-dark-blue petal face, **wall-mounted**. A **blue-felt kidney gaming table with a padded red-brown rail on a raised plinth with a kerb**. A **long green-illuminated bar counter** across the full width at waist height. Cube pendant lights with grid faces, one white spherical pendant, vertical magenta neon on the left wall. Dense mixed-species crowd. | Red | Named in an **inner ring** of the Red rosette | STATED | 1 (the room), 3 (the sector and ring) | `reference/04-sector-red/Casino.webp`; `other map.png` Red rosette | `no` |
| **Dark Star** | A named venue. Sign: **"DARK" + a sunburst glyph substituting for the S + "TAR"**, in irregular hand-drawn splayed angular caps with pointed apexes — **a third distinct typographic register** on the station, unlike the Zocalo tube script or the customs grotesque. Letters glow **acid green**, the sunburst **warm amber/copper**, ~12 principal rays. On a dark **vesica/almond plaque** on a grey-green wall, **flanked by bamboo-like foliage** — so the entrance is planted, which places it in or beside a landscaped area. | Red | Named in an **inner ring** of the Red rosette | STATED | 1 (the sign), 3 (the sector) | `reference/04-sector-red/Darkstar_logo.webp`; `other map.png` Red rosette | `no` |
| **Earhart's** | The officers' club. A **free-standing lenticular building raised on a single central pedestal column** above the drum floor — a saucer with a **continuous glazed equatorial band** through which the bar, tables, wood-slat screens, cyan backlit panels and patrons read; a shallow domed upper shell **clad in large square tiles with six countable roof vents**; a deep unlit under-flare to one broad tapered pedestal with a flared foot. The equator is divided by piers into ~8–9 bays alternating **three-slat timber screens** and **cyan backlit panels**. | **the drum sector** (Green or Brown — C-003), **standing on the drum floor**. Named in the **Red** rosette | outermost / habitat floor, 278.3 m, 1.000 g | STATED (Red, by auth 3) but **IMPLIED to be on the drum floor by auth 1**, which is the contradiction driving C-003's session-2r note | 1 (the building and its setting), 3 (the Red assignment) | `reference/04-sector-red/Earhart's.webp`; `canon/CONFLICTS.md` C-003 session-2r note | `no` |
| **The Fresh Air Restaurant** | An **open terrace inside the drum** — the ceiling *is* the far side of the drum, a dark mottled expanse of terrain, not a soffit. Sign: an **oval plaque, "The FRESH AIR Restaurant"**, serif caps for FRESH AIR and script for "Restaurant", red on pale, under a **teal neon double swoosh** on a canopy fascia; a second smaller swoosh repeats nearby, so the swoosh is a motif. Lighting hangs from **red-painted service pipes** carrying ~8 rectangular downlights at even pitch plus one white strip. Walls are **backlit blue-green translucent panels forming a raked screen, densely planted over**. **Four tall thin illuminated posts** stand in the middle distance like torchères. White cloths, candles, mixed crowd. | **the drum sector** (Green or Brown — C-003), on the drum floor. Named in the **Green** rosette | habitat floor | STATED (Green, auth 3) + IMPLIED (drum floor, auth 1) | 1, 3 | `reference/11-props-and-technology/fresh air resturant signage with view.webp`; `other map.png` Green rosette | `no` |
| **Eclipse Cafe** | A lower-budget quick-meal cafe on the Zócalo promenade. Menu named on fan sources as including **Flarn** and **Centauri Roopo balls**. | Red | on the Zócalo | STATED | 4 | https://babylon5.fandom.com/wiki/Z%C3%B3calo | `no` |
| **An unnamed bar / diner** (uploader caption "Doug's Dugout" — **treat the name as unsourced**) | The best **small enclosed hospitality interior** we hold, and utterly unlike the Zocalo concourse. **Lit entirely by low pendant cones** — large shallow polished-metal shades on slim stems hung low over each table, bright rim, hot pool beneath; ambient fill near zero, so the room is a field of separate pools. Left wall: a **cyan neon glyph in the curvilinear alien script family** beside a **vertical cyan neon tube in four segments split by three clamp bands**. Centre: a **large orange-red backlit matrix of small square cells** in a stepped irregular silhouette, ~12 cells across. Back wall: a **correctly laid out standard 20-segment dartboard** (numerals verified) and an **amber alphanumeric display reading "209"**. **Ordinary human pub fittings persist on the station.** | Red (folder attribution only) | — | IMPLIED | 1 | `reference/04-sector-red/Doug's Dugout.webp` | `no` |
| **Happy Daze Bar** | "A very low key bar", named beside DOWNBELOW on the Brown rosette. | Brown | Named in the **Brown rosette beside the DOWNBELOW band** | STATED | 3 (the rosette), 4 (the description) | `other map.png` Brown rosette; https://babylon5.fandom.com/wiki/Happy_Daze_Bar | `no` |
| **Business District / Business Center** | Commerce and **currency exchange** — the customs boards direct visitors here for exchange rates, which ties an authority-1 sign to an authority-3 rosette label. | Red | Named in an **inner ring** of the Red rosette | STATED | 1 (the referral), 3 (the location) | `reference/01-station-exterior/welcome to babylon 5.webp`; `other map.png` Red rosette | `no` |
| **Hotels and transient habitation** | Paid short-stay accommodation for the constant flow of visitors. | Red | — | STATED | 4 | https://babylon5.fandom.com/wiki/Red_Sector | `no` |
| **Shops, kiosks and cart vendors** | The Zócalo's retail grain: shopfronts under the gallery, free-standing stalls, carts. One shopfront in frame is signed **"…STORE"** with a display case; another has a **maroon banner with red-orange alien characters**. | Red | on and around the Zócalo | STATED | 1 | `reference/11-props-and-technology/Zocalo neon signage in background.jpg`; `reference/04-sector-red/zocalo.webp` | `no` |
| **"Outdoor" recreation — lake pool, ball diamond** | Recreation grounds. The sectional schematic independently carries **"water recreation facilities"**, which is the same thing from a different sheet. | Red (auth 4) / the drum (auth 3 callout) | — | STATED, two sources agreeing on the *kind* and not the place | 3 + 4 | Security Manual "water recreation facilities"; https://babylon5.fandom.com/wiki/Red_Sector | `no` |

---

## 6. DIPLOMATIC AND ALIEN

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Ambassadorial suites** | The ambassadors' residences, in a high-security zone. The sectional schematic's callout dot for them lands in **band 4** (see X-3). | Green | "wrapped around the Garden" per auth 4; fan sources give "**Green 2**" for the Diplomatic Quarters | STATED | 3 (the callout), 4 (Green 2 and the wrapping) | Security Manual "ambassadorial suites"; https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **The Alien Sector** | The **multi-environ** quarter: rooms whose atmosphere is changed to suit the resident. Fan sources put **14 species** here and say access is through **a series of airlocks with breather-mask dispensers**. **This is where the "six standing atmospheres" of the customs board are actually consumed** — humans are atmosphere **02**. | Green | Named in the **Green rosette**, outer ring; the schematic's "multi-environ 'alien' sector" dot is in **band 3, the band it labels Green** | STATED | 3 | `other map.png` Green rosette; Security Manual; auth 4 for the 14 species and airlocks, https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **Alien sector corridor** | The corridor architecture of the alien quarter: a **chamfered aperture** with vertical jambs, flat head and raised threshold. Note the standing caveat — the *aperture* is chamfered; nothing establishes the passage behind it is. | Green | in the Alien Sector | STATED | 1 | `reference/05-sector-green/corridor in alien sector.webp`; INV-007 | `kit` |
| **Kosh's quarters (Vorlon ambassador)** | Sealed non-oxygen environment. Its wall treatment is visible behind Kosh: a **frosted grid wall with backlit panels**, in vapour. Fan sources give the address as **"Compartment 8 in Green 23"** and the atmosphere as unbreathable to humans. **A player cannot enter without a suit** — a hard interaction rule that falls out of the atmosphere system, not out of scripting. | Green | auth 4: "Compartment 8, Green 23" | STATED (the environment, auth 1) / STATED (the address, auth 4) | 1 (the environment), 4 (the address) | `reference/15-races-and-makeup/more vorlon.png`; https://babylon5.fandom.com/wiki/Kosh | `no` |
| **The Vorlon transport berth** | Where Kosh's ship docks. The ship is **hard-edged irregular chartreuse blotches on black**, matte. The bay is the plant-room bay in §4. | Blue | a docking bay | IMPLIED | 1 | `reference/13-other-ships/kosh's transport.webp` | `no` |
| **The domed rotunda** | A domed circular chamber ringed with windows that **look INWARD onto the drum interior** — green fields, a rising horizon, white terraced structures, no sky band. Window ring divided by **stubby columns carrying three ring bands near the top** with flared capitals; **stepped coffered dome** in gold and grey; floor a **circular mosaic with a radiating sunburst**; **hanging banners with alien sigils** between the columns; wall panels of vertical blue light slots; a **blue illuminated altar table**; steps up to a portal opposite. | Green (folder attribution only — see C-003 note 2r) | in the drum's outer wall if the reading holds | IMPLIED | 1 | `reference/05-sector-green/rotunda.webp` | `no` |
| **Observation rotundas (4)** | Exterior rotunda structures. **Open question, flagged not resolved:** if the domed rotunda above is one of these, they face **inward across the drum**, not outward at space. | Blue (Contract 5) / Green (the interior frame) | — | STATED (existence) / **unresolved (which way they face)** | 3 | Contract 5; `00-MASTER.md` §1.3; `other map.png` Blue rosette | `ext-crude` |
| **A drum-facing office with a large multi-pane window** | An interior room with a **large multi-pane window looking directly into the rotating drum** — the clearest view of the drum interior in the reference set, showing the **two segmented axial support struts** with four pale barrel sections, three or four dark collar joints and a **salmon collar at each joint**. Filed under characters; the window is why it matters. | the drum sector | in the drum's outer wall | IMPLIED | 1 | `reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp` | `no` |
| **The resident commercial telepath's office** | The station's Psi Corps-licensed commercial telepath monitors business deals for clients. **`LICENSED PSI` is a field on the identicard record**, so telepath status is part of the station's own data model. | **unplaced** | — | **PROPOSED — P-02** | 1 (the identicard field), 4 (the role) | `reference/11-props-and-technology/identicard readout.webp`; https://babylon5.fandom.com/wiki/Talia_Winters | `no` |
| **League of Non-Aligned Worlds delegations** | The smaller member worlds' representatives, resident and present in the council chamber. Their emblem — **orange triangle in a ring of teal stars** — is in era; the Interstellar Alliance and Army of Light emblems are **S4–5 and must not appear**. | Green | with the ambassadorial suites | IMPLIED | 4 | `reference/16-signage-typography-ui/faction symbols.png` | `no` |

---

## 7. MEDICAL

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Medlab One** | The station's primary medical facility, under the Chief Medical Officer. | Blue | Named in the **Blue rosette**; fan sources give "**Blue 2**" | STATED | 3 (the sector), 4 (the level) | `other map.png` Blue rosette; https://babylon5.fandom.com/wiki/Medlab | `no` |
| **The other Medlabs** | Medlabs are **distributed across Red, Green and Blue Sectors**; Medlab 2 and Medlab 5 are named. **No source gives a total count.** For a 250,000-population station this is the right shape — several district facilities plus one primary — but the number is a gap. | Red, Green, Blue | — | STATED (distribution) / **count unknown** | 4 | https://babylon5.fandom.com/wiki/Medlab; https://babylon5.fandom.com/wiki/Ombudsmen | `no` |
| **Isolab** | A **pressurised, hermetically sealed compartment inside a Medlab with a self-contained air supply tunable to the patient's species** — the medical arm of the six-atmosphere system. **Each Medlab has one.** | with each Medlab | — | STATED | 4 | https://babylon5.fandom.com/wiki/Medlab | `no` |
| **The infirmary** | A medical care facility **adjacent to Medlab One**. | Blue | next to Medlab One | STATED | 4 | https://babylon5.fandom.com/wiki/Medlab | `no` |
| **Morgue / mortuary** | **No source we hold places one.** A station of 250,000 with a 90%-crime district and a war on has one, and the show uses one. | **unplaced** | — | **PROPOSED — P-03** | 5 | — | `no` |
| **Cryo storage** | Cryogenic storage for bodies and for cryo-transported passengers. **No source we hold places one.** | **unplaced** | — | **PROPOSED — P-03** | 5 | — | `no` |

---

## 8. SECURITY, LAW AND ORDER

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Security Central** | Station security headquarters. | Red | Named in an **inner ring** of the Red rosette | STATED | 3, corroborated 4 | `other map.png` Red rosette; https://babylon5.fandom.com/wiki/Ombudsmen | `no` |
| **Law Courts / the Judiciary** | The **Ombuds** courtroom. Ombudsmen are Earth Alliance judges appointed by the higher courts, ruling on crimes in station jurisdiction and hearing appeals under Earth Alliance law. **At least two sit on B5** (named on fan sources as Wellington and Zimmerman). | Red | Named in an **inner ring** of the Red rosette | STATED | 3, corroborated 4 | `other map.png` Red rosette; https://babylon5.fandom.com/wiki/Ombudsmen | `no` |
| **The brig / holding cells** | Detention. **No source we hold places it.** It must be walkable from Security Central and from the courtroom, and it is where a customs refusal ends. | **unplaced** | — | **PROPOSED — P-04** | 5 | — | `no` |
| **Security posts / checkpoints** | Distributed presence. The corridor kit already carries the wall plaques; a checkpoint is a door plus a scanner plus two officers. The **identicard reader** is the prop: a dark grey wedge on a pistol grip with a portrait screen and three amber indicator lenses. | all sectors | at sector and level boundaries | **PROPOSED — P-05** | 1 (the prop) | `reference/11-props-and-technology/Identicard reader.webp` | `no` |
| **Nightwatch** | The Ministry of Peace's political-loyalist auxiliary, **formed 2259 and therefore squarely in era for S2–3**. Members are ordinary station personnel wearing **black armbands**; they report on speech, not crime. **This is an NPC faction with no building** — it is an overlay on security and civilian NPCs alike, and the armband is the whole visual. | all sectors | — | STATED (existence and era) | 4 | https://babylon5.fandom.com/wiki/Nightwatch; https://babylon5.fandom.com/wiki/Ministry_of_Peace | `no` |
| **The Ministry of Peace office** | Whether MiniPax held a physical office aboard is **not established by any source found**. Nightwatch recruitment happens in the show, so a meeting room is needed even if a permanent office is not. | **unplaced** | — | **PROPOSED — P-06** | 5 | — | `no` |

---

## 9. THE DRUM — GARDEN, AGRICULTURE, RECREATION

Everything here is inside the **hollow habitat drum**, on or above the **habitat floor at
r = 278.3 m, exactly 1.000 g**. The drum sector is **Green or Brown — C-003 open.**

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **The Garden (the drum interior)** | The 2,739 m agricultural and civic volume: the inner surface is **fields, hedgerows and roads curving up and over**, lit from **longitudinal light runs on the guideway trusses** — not an axial sun-strip and not the end caps. Standing on the floor, the ground overhead is 556 m up and the far end cap is 2.6 km away. | the drum sector | habitat floor, 278.3 m, **1.000 g** | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`, `33a`; `reference/09-garden-core-and-transit/The Gardens.webp` | **`shell` + ground heightfield built** |
| **The Garden's townscape** | The Garden is **a townscape, not a park.** A civic building of **stacked cylindrical drums** with colonnaded upper storeys, cantilevered slab terraces and a glazed ground floor, ~6 storeys; a **rectangular reflecting pool**; a tall thin **waterfall on a planted bank**; paved terraces, mown lawn strips, **flagpoles with white banners**, **red-orange painted external stairs**. Elsewhere: low blockish buildings with lit window bands, roads, **palm trees**, lawns. | the drum sector | on the floor | STATED | 1 | `reference/09-garden-core-and-transit/garden.png`; `.../The Gardens.webp` | `no` (buildings) |
| **A landscaped garden terrace** | Paved winding paths in small setts; clipped hedges; a **water feature / cascade** against a planted bank; a timber bench; a circular raised planter with **red-brown coping**; **orange sail canopies on masts**; a **multi-storey glazed building** behind; a **tunnel portal with an arched roof** into the terrace. | the drum sector | on the floor | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_29a.jpg` | `no` |
| **The Zen Garden** | A **small enclosed area within the main garden** — sand with several embedded stones and wave-like raked markings, a Japanese dry garden, used for meditation. Set aside on the station commander's initiative. | the drum sector; named in the **Green rosette**, and the schematic's callout dot lands in **band 4** | on the floor | STATED | 3, described 4 | Security Manual "zen garden"; `other map.png` Green rosette; https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **Hydroponics** | Crop growing under light, producing **food and oxygen**. Distinct from the open drum agriculture: hydroponics is racked and enclosed, the drum floor is fields. | Named in the **Green rosette** and as a schematic callout | **PROPOSED**: sub-floor decks, not the open floor — P-07 | STATED (existence) / PROPOSED (which deck) | 3 | `other map.png` Green rosette; Security Manual "hydroponics" | `no` |
| **Water recreation facilities** | Named on the sectional schematic. Fan sources independently describe a **lake pool** and a **ball diamond**. | schematic **band 4** | on the drum floor | STATED | 3, corroborated 4 | Security Manual; https://babylon5.fandom.com/wiki/Red_Sector | `no` |
| **The drum end caps** | Two dished bulkheads, each a **disc of concentric annular bands** — alternating light and dark panelled rings, checker-plated in the outer bands, resolving into a radially segmented inner zone, with a **blue light strip set into one ring**. The hub cone fills the inner ~20%. | the drum sector | at z 3839 and 6425 | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`; `reference/09-garden-core-and-transit/The Gardens.webp` | **built** |
| **The three radial spokes** | Structural spokes at 120°, carrying the guideway trusses and a **radial transport tube** from the axis out to the drum wall — banded in segments with **coloured band markings at intervals** and a conical collar at the hub. | the drum sector | 278.3 m → axis | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`, `33a` | **built** |
| **The sub-floor deck stack ("under the Garden")** | **9 decks from the 278.3 m floor outward to the 310.8 m pressure hull, 1.013 g → 1.117 g.** In spin gravity "beneath the ground" means *outward*. This is where the drum's plant, services and — under the Brown reading — Downbelow actually live. | the drum sector | 9 decks, ring "subfloor" | IMPLIED (from the geometry, session 2v) | 5 (the derivation), 1 (the hollow drum it derives from) | `station/interior.py::ring_radii`; `STATE.md` session 2v | `kit` |
| **A second, ground-level transit system** | A **green-and-yellow streamlined car on an elevated track at garden ground level, with its own station canopy** — sharing nothing with the white/maroon guideway tram. **Two transit systems in the drum, not one.** | the drum sector | on the floor | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_29a.jpg`; `STATE.md` session 2x | `no` |

---

## 10. INDUSTRIAL, ENGINEERING AND LIFE SUPPORT

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Primary fusion core** | The main reactor. Aft terminus assembly, with **fusion isotope slush tanks**, **auxiliary fusion cores**, coolant systems and maintenance, and **auxiliary power units (4)**. | Yellow | the non-rotating aft half | STATED | 3 | Security Manual callouts; `00-MASTER.md` §2 | `ext-crude` |
| **Explosive disconnect point** | The structural boundary at real **z = 2,680 m** where the whole reactor assembly detaches. Everything aft of it jettisons as one. | Yellow | z ≈ 2,680 m | STATED | 3 | `00-MASTER.md` §2 item 7; `STATE.md` OW-001 | `shell` |
| **Power transfer core + 12 cooling fins** | The Yellow rosette is **not concentric** — it is a cog: a power transfer core with 12 fins radially arrayed, plus **inspection access** and **coolant transfer tubes and holding tanks**. Note C-007: these small reactor-adjacent fins are **a different system** from the six large coplanar radiator blades on the spine rail. | Yellow | on the axis, aft | STATED | 3 | `other map.png` Yellow rosette; `canon/CONFLICTS.md` C-007 | `ext-crude` |
| **Alpha power substation** | Power distribution. | Grey | Named in the **Grey rosette** and as a schematic callout | STATED | 3 | `other map.png` Grey rosette; Security Manual | `no` |
| **Mainstage power distribution node** | The main distribution node. | Yellow/Grey | on the schematic between the reactor and the carousel | STATED | 3 | Security Manual callout | `no` |
| **Primary breaker** | The main breaker. | Grey | Named in the **Grey rosette** | STATED | 3 | `other map.png` Grey rosette | `no` |
| **Fabrication furnaces** | Heavy manufacturing. | Grey | Named in the **Grey rosette** and as a schematic callout | STATED | 3 | `other map.png` Grey rosette; Security Manual | `no` |
| **Maintenance and repair facilities** | Workshops. Also named in the Blue rosette, so there are dockside shops as well as industrial ones. | Grey (and Blue) | Named in both rosettes | STATED | 3 | `other map.png` Grey and Blue rosettes | `no` |
| **Commercial research laboratories** | Rentable lab space — the reason corporations have a presence aboard. | Grey | Named in the **Grey rosette** | STATED | 3 | `other map.png` Grey rosette | `no` |
| **Variable gravity research torus** | A research facility exploiting the radius/gravity gradient. **The single most interesting piece of set-dressing the schematic names**, because the project already simulates exactly the physics it exists to study. | Grey | schematic band 2 | STATED | 3 | Security Manual callout | `no` |
| **Zero-G maintenance facility** | Maintenance in free fall. | Grey / Yellow | at the rotating/non-rotating interface | STATED | 3 | Security Manual callout | `no` |
| **Atmosphere monitoring station** | Monitors the six standing atmospheres and the general air. | Grey | Named in the **Grey rosette** | STATED | 3 | `other map.png` Grey rosette | `no` |
| **Rotation drivers and mag-lev bearing points** | The machinery that spins the carousel and the bearing it spins on. **A named, sourced, enormous piece of machinery at the rotating/non-rotating interface** and an obvious set-piece volume. Also "mag-lev bearing and transfer systems" forward. | at both ends of the rotating assembly | — | STATED | 3 | Security Manual callouts | `no` |
| **Water storage** | Bulk water. | Red | Named in an **inner ring** of the Red rosette | STATED | 3 | `other map.png` Red rosette | `no` |
| **Water reclamation** | Recycling. Fan sources add a detail worth building on: **showers are for the executive suites and command quarters only** — so water is rationed, and that is a felt class distinction. | Brown | around the outer hull with waste | STATED | 4 | https://babylon5.fandom.com/wiki/Downbelow | `no` |
| **Waste management systems ("Down-Below")** | Waste processing. Named in **three** rosettes (Red, Green, Brown) plus **twice** on the sectional schematic, always with the parenthetical "Down-Below". So it is a **distributed system**, not one plant — every sector has one, and each is a candidate slum. | Red, Green, Brown | **outermost rings**, against the hull | STATED | 3 | `other map.png` Red/Green/Brown rosettes; Security Manual | `no` |
| **Waste Management Control** | The control room for the above. | Brown | Named in the **Brown rosette** beside DOWNBELOW | STATED | 3 | `other map.png` Brown rosette | `no` |
| **Air compressors** | Named by fan sources as one of the systems Downbelow's chambers cluster around. | Brown | outer hull | STATED | 4 | https://babylon5.fandom.com/wiki/Downbelow | `no` |
| **Raw material storage bays (5)** | Feedstock for the fabrication furnaces. | Yellow/Grey | on the spine | STATED | 3 | `00-MASTER.md` §2 item 11 | `no` |
| **Hazardous liquid holding tank; inert gases holding tanks (4)** | Bulk chemical storage. The inert gas tanks are plausibly the feedstock for the six-atmosphere system. | Yellow | on the spine | STATED | 3 | `00-MASTER.md` §2 items 14–15 | `ext-crude` |
| **Sanctuaries (4)** | A counted exterior system whose function is not stated by Contract 5. See §12 and X-7. | — | — | STATED (existence) / **unplaced by function** | 3 | Contract 5; `00-MASTER.md` §1.3 | `no` |
| **Primary reactor hall and control room** | The room inside `primary_fusion_reactor`. The feature is **z 39–331 m of hull, 0.0299 km³**, and it held **zero addressed places**: `fusion_core` covers the z and declares only `power_generation` with two interacts. A fusion containment drum on the centreline, the biological shield either side, the refuelling crane over it. The Security Manual also names **fusion isotope slush tanks**, **auxiliary fusion cores** and **auxiliary power units (4)** in this assembly and none of those is addressed either. | Yellow | ring 0, deck 0 — 0.559 g, inside `fusion_core` | **PROPOSED — volume audit §2.1, §4** | 5 | `00-MASTER.md` §2 item 3; `docs/volume-audit.md` §2.1; INV-100 | `rooms` |
| **Core fuel housing and transfer gallery** | The bunkerage behind `core_fuel_housing`, the aft terminus of the station. Slush tanks against both flanks with a bund kerb, a transfer crane over the aisle. The register's only fuel place is **`fuel_stores`, which is SHIP fuel at the docks 7 km fore**. | Yellow | ring 0, deck 2 — 0.533 g, inside `fusion_core` | **PROPOSED — volume audit §2.4** | 5 | `00-MASTER.md` §2 item 1; `docs/volume-audit.md` §2.4; INV-100 | `rooms` |
| **Coolant manifold gallery** | The gallery serving the **8 coolant manifolds** and the radiator fin roots. `power_transfer` carries the station's **only** `cooling` function and its footprint ends 265 m aft of the blades; no pump room, no manifold hall, no reservoir was addressed anywhere. At 48.3 m radius this is **0.173 g — a crawlway, not a corridor**: both flanks carry pipework and the centre is the only floor. | Yellow | ring 3, deck 3 — 0.173 g, wrapping the reactor | **PROPOSED — volume audit §2.3** | 5 | `00-MASTER.md` §2 item 2; `docs/volume-audit.md` §2.3; INV-100 | `rooms` |
| **Generator torus hall** | The hall inside `generator_torus_housing` — **z 1,095–1,295, 0.0176 km³ of hull, zero addressed places**. The generator torus in section, switchgear cubicles against one flank, the bus duct overhead. | Yellow | ring 1, deck 4 — 0.406 g | **PROPOSED — volume audit §2.4** | 5 | `docs/volume-audit.md` §2.4; `station/schema/station.yaml` `generator_torus_housing`; INV-100 | `rooms` |
| **Heat exchanger hall** | The hall behind the **12 heat exchange / emergency solar arrays** at z 2,020–2,537. `LIFE-SUPPORT-AND-INDUSTRY.md` L-01 derives **~1.9 GW of rejected heat** through that system and **no place on the station carried a thermal or heat-rejection function at all**. Exchanger drums on the centreline, coolant headers full height against a flank, the condensate main overhead. | Yellow | ring 0, deck 4 — 0.507 g | **PROPOSED — volume audit §2.4** | 5 | `docs/LIFE-SUPPORT-AND-INDUSTRY.md` §1.2 L-01; `docs/volume-audit.md` §2.4; INV-100 | `rooms` |

---

## 11. RESIDENTIAL, BY CLASS

The class gradient is the point. **Gravity does the work for free**: command quarters in Blue at
0.603 g, Downbelow in Grey or the drum sub-floor at 1.117–1.445 g. The people with the least
power live where they weigh the most.

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Command staff quarters** | Senior officers' quarters. Fan sources add: **showers** are for these and the executive suites only. | Blue | — | STATED | 4 | https://babylon5.fandom.com/wiki/Blue_Sector; https://babylon5.fandom.com/wiki/Downbelow | `no` |
| **Station personnel quarters** | Support workers, station services, pilots, **dock workers** (the Blue rosette names "Dock Workers' Quarters" separately), and **visiting VIPs from Earth**. Access to Blue is restricted to personnel and official Earth Alliance guests. | Blue | "Dock Workers' Quarters" named in the **Blue rosette** | STATED | 3 (dock workers), 4 (the rest) | `other map.png` Blue rosette; https://babylon5.fandom.com/wiki/Blue_Sector | `no` |
| **Mess hall** | Crew catering. | Blue | Named in the **Blue rosette** | STATED | 3 | `other map.png` Blue rosette | `no` |
| **Ambassadorial / diplomatic quarters** | See §6. High security, wrapped around the Garden. | Green | fan sources: "Green 2" | STATED | 3, 4 | Security Manual; https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **Alien residential quarters** | Homes for the **non-human population who are not ambassadors** — the majority of the station's aliens. Distinct from both the ambassadorial suites and the sealed Alien Sector. | Green | — | STATED | 4 | https://babylon5.fandom.com/wiki/Green_Sector | `no` |
| **The sealed Markab quarter** | The Markab community's quarter, **sealed after the plague of "Confessions and Lamentations" (S2E18) killed the entire species**. Powered, unlit, still furnished; nobody at any hour. The station's only monument to an extinction, and the reason the S2–3 datum is worth its two costs. **The extinction is authority 1; the room's placement is authority 5** — no source places it, and it sits beside the Alien Sector because that is where a non-human community's quarter is. It is not enterable: a welded door, an atmosphere lamp reading nothing, and a level plaque. `npc/schedule.py` has carried it as a sealed `PlaceCrowd` at density 0.0 since it was written, `npc/crowd.py` asserts it is **the one place empty at every hour**, and `npc/navigation.py` names it a deliberate island in the walk graph — three modules modelled it and the register did not, so until now there was nothing to stand in front of. | Green | ring 0, deck 3, beside the Alien Sector | **PROPOSED — P-14** | 1 (the extinction), 5 (the placement) | S2E18; `station/npc/schedule.py::PLACES`; `station/npc/crowd.py::EXTENTS` (12.0 × 58.32 m, 699.84 m²) | `rooms` |
| **Civilian residential (commercial)** | Paid residential for people who live and work aboard. | Red | — | STATED | 4 | https://babylon5.fandom.com/wiki/Red_Sector | `no` |
| **Transient habitation** | Short-stay rooms for the constant flow of arrivals — the layer between a hotel and Downbelow. | Brown (and Red) | — | STATED | 4 | https://babylon5.fandom.com/wiki/Babylon_5 | `no` |
| **Downbelow** | The slums. **"Various undeveloped areas, mostly in the lower levels, near the outer hull, around the waste recycling system, the air compressors and the water reclamation facility"** — corridors and chambers, not rooms. **The Brown rosette marks "DOWNBELOW" with a double-headed arrow spanning an OUTER annular band**, which is the source answering C-004's own standing objection. Home to the **Lurkers**, the station's homeless underclass — people who came for a new life, ran out of money and cannot buy passage home. **Accounts for as much as 90% of the station's crime.** | Brown (a **radial** designation in our schema — INV-009) | **outermost ring**, against the hull, at the **highest gravity in the sector** | STATED | 3 (the rosette band), 4 (the description) | `other map.png` Brown rosette; https://babylon5.fandom.com/wiki/Downbelow | `no` |
| **Downbelow's architecture** | The only Downbelow-class frame we hold: a wide industrial corridor/street receding to a vanishing point. A **continuous illuminated grating strip runs down the centre of the deck** — open metal grating over a light box, lit in a **checkerboard of live and dead cells** — organising the whole perspective; deck either side in **large recessed panels with raised borders**; **vertical white light bars** on wall pilasters; overhead **exposed girder truss with pipes and cable runs, no ceiling**; a **green-yellow neon sign in alien script over a shopfront**; a steel stair with a plain handrail; banks of equipment panels with blue backlit displays. **ERA CAVEAT: S5, station derelict. The set architecture is in era; the debris, darkness and dead panels are not.** | Brown | outer hull | STATED (architecture) | 1, with era caveat | `reference/01-station-exterior/sleeping-in-light-05.jpg` | `no` |
| **Sections welded shut** | Brown Sector contains sections that have been **welded shut** — unfinished or abandoned volume. A gift for level design: sealed doors with a reason. | Brown | — | STATED | 4 | https://babylon5.fandom.com/wiki/Babylon_5 | `no` |

---

## 12. WORSHIP AND CONTEMPLATION

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **The Sanctuary** | "A **large circular room** that **looks out onto the stars**, open to the public as a favoured place for contemplation, and **rentable for private ceremonies**." Note the contrast with the domed rotunda, whose windows look *inward* at the drum. | Blue | fan sources: "**Blue 3**" | STATED | 4 | https://babylon5.fandom.com/wiki/Blue_Sector | `no` |
| **Sanctuaries (4)** | Contract 5 counts four as an exterior system. If the Sanctuary above is one of them, **the count is four and they are hull-facing rooms with star views** — which reconciles the two sources and is worth testing against the observation-rotunda question in §6. | — | — | STATED (count) / **PROPOSED (that these are the same thing) — P-08** | 3 | Contract 5; `00-MASTER.md` §1.3 | `no` |
| **The interfaith chapel** | A dedicated multi-faith worship space. **Not established in era by any source found.** The one chapel citation found (Blue 4) is dated **2271 — out of era and excluded.** The station demonstrably hosts a week-long **festival of the dominant religious beliefs of every resident species**, so *large hireable ceremonial space* is canon even where a permanent chapel is not — and §5 records exactly that, in Red. | **unplaced** | — | **PROPOSED — P-09** | 4 (the festival), 5 (the placement) | https://babylon5.fandom.com/wiki/The_Parliament_of_Dreams; https://babylon5.fandom.com/wiki/Red_Sector | `no` |
| **Alien worship spaces** | Each resident species holds its own observances. The **rotunda's blue illuminated altar table and hanging banners with alien sigils** is the only such room we hold a frame of. | Green | — | IMPLIED | 1 | `reference/05-sector-green/rotunda.webp` | `no` |

---

## 13. TRANSIT

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **The core shuttle** | The axial transit spine. A **lattice-girder truss runs the length of the axis** carrying long cylindrical **illuminator tubes**; its lower edge is **serrated — a rack** — which is how the cars are driven; **cars hang beneath it**, blunt-ended and windowed. Fan sources: a high-speed monorail running **Blue to Grey** just under the axis, in **low gravity**, with **13 stops**. | axis, all sectors | on the axis, 0–50.1 m, **0.18 g → 0** | STATED | 1 (the structure), 4 (the 13 stops and the run) | `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`; https://www.oocities.org/davesb5page/xplor.htm | `physics`, `core_tube` built |
| **Core shuttle car interior** | Bench and individual seating in **red-maroon upholstery on moulded grey bases**; **grey panelled walls with recessed seams**; **amber/yellow illuminated panels set low in the seat plinths**; a continuous **window band at seated eye height** onto the drum landscape; vertical **grab poles** floor to ceiling; a raked **windscreen** through which the tube's **red structural ribs** recede. | — | — | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_35a.jpg` | `no` |
| **Radial transport tubes (the spokes)** | Rim-to-axis transit. Named as "transport tubes" in **five rosettes**; the Green rosette shows only **three**, consistent with the drum. **The physics makes this a felt journey, not a loading screen**: holding Coriolis under 0.12 g needs **133 seconds**, so it is a **two-minute-plus ride** during which weight drains away and a sideways push builds and fades, plus **52.2 m/s of tangential speed to shed**. | all sectors | 278.3 m → axis | STATED | 3 (the spokes), 1 (one in footage) | `other map.png` rosettes; `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`; `station/physics/core_shuttle.py` | `physics` |
| **"Concentric personnel transfer systems"** | The draughtsman's own name for the transit system, drawn as **a diagonal chain of cars climbing from the non-rotating spine into the rotating assembly** — i.e. the spin-up/spin-down transfer, which is a distinct problem from either the axial run or the radial climb. | at the rotating interface | — | STATED | 3 | Security Manual callout | `no` |
| **Transport tubes / lifts (between levels)** | Short and mid-distance vertical transit between decks. **The lift-car display is the single highest-value missing reference in the project** — it would close C-004 outright. | all sectors | — | STATED | 3, 4 | `other map.png` rosettes; https://www.oocities.org/davesb5page/xplor.htm | `no` |
| **The drum guideway tram** | Three Warren trusses at r = 236.6 m in the spoke planes, carrying light runs and a white/maroon tram. **Flying in open air, above the ground and below the axis.** | the drum sector | 236.6 m — free flight | STATED (the trusses and lights) | 1 | `reference/03-sector-blue/Babylon_5_2-22_34b.jpg`, `33a`; INV-012, INV-017 | **built** |
| **Ground-level tram** | The second, different system at garden ground level. See §9. | the drum sector | on the floor | STATED | 1 | `reference/03-sector-blue/Babylon_5_2-22_29a.jpg` | `no` |
| **The Central Corridor** | A wide **two-level public concourse** — a catwalk above a main floor in one volume — in which **the hull's circular structural ribs are exposed and unclad, crossing the whole space**. In a concentrically decked cylinder **only the outermost deck sits against the hull ribs**, so this is outer-ring construction. Named in the **outermost ring of the Red rosette**. *(The frame-to-name link is a filename, not a reading — see C-004 note 2r.)* | Red | **outermost ring** | STATED (auth 3) / IMPLIED (auth 1, via a filename) | 1, 3 | `reference/09-garden-core-and-transit/central corridor.webp`; `other map.png` Red rosette | `kit` |
| **Standard corridor** | The station's default passage, and the most-used asset in the project. Square-on: **projecting skirt, set-back dado, heavy rail band at hip height throwing a deep shadow reveal, then courses of large plates with recessed seams; bullnose pilasters at the portal jambs carrying segmented vertical light strips; warm downlights low on the wall; a fine deck tile grid.** A landscape **`LEVEL` plaque** — white uppercase on black, in a recessed dark field at high level — is signed on the wall. | all sectors | — | STATED | 1 | `reference/07-sector-grey/grey level 1.webp`; INV-007 | **built** |

---

## 14. MEDIA, COMMS AND PROPAGANDA

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **Deep space communications grids (2)** | The station's long-range comms, on support pylons; span 2,120.5 m, width at the grid 893.2 m. Plus a **tachyon transmitter**. | Blue/Red | on the two pylons | STATED | 3 | `00-MASTER.md` §1.3, §2 | `ext-crude` |
| **Deep space comms operations** | The room that works the grids: signal racks and patch panels on both flanks, the waveguide run leaving overhead for the pylon. Placed at the root of `comms_grid_pylon` **as the schema builds it** (z 2,515–2,988) — the register's own `comms_grid` row is at **z 7,900, 5,148 m away**, with an **empty `interacts` tuple**. **Position contested**: `00-MASTER.md` §2 orders the grid item 17 (forward of z 5,974), the schema builds it at z 2,515–2,988, and Miller's table width of 893.2 m puts it at z 3,472–3,549 or 4,339–4,437. One frame of the pylons against a recognisable hull section would close it. | Yellow | ring 1, deck 5 — 0.393 g | **PROPOSED — volume audit §2.2, §6** | 5 | `docs/volume-audit.md` §2.2, §6; `station/components.py` `comms_grid_pylon`; INV-100 | `rooms` |
| **Babcom terminals** | The station's public and private comms interface. Wall monitors are already visible in the arrival concourse and at Zocalo gallery level. **A terminal in every quarters, every corridor junction and every bar is how news and propaganda physically reach people.** | all sectors | — | IMPLIED | 1 (the screens) | `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg`; `reference/04-sector-red/more zocalo.png` | `no` |
| **ISN — Interstellar Network News** | The news service. In era it is **turning from a legitimate outlet into a propaganda arm of EarthGov** — which is the S2–3 political arc in one sentence and should be audible on every public screen. **Whether ISN held a station bureau in S2–3 is not established by any source found**; the on-station ISN crew story is S4 and out of era. | **unplaced — and possibly should not exist yet** | — | **PROPOSED — P-10** | 4 | https://babylon5.fandom.com/wiki/Nightwatch and related | `no` |
| **Public information monitors** | The customs boards direct visitors to **"SEE MONITORS FOR DETAILS"** and "FOR SPECIFIC ATMOCHEMICAL BREAKDOWNS SEE MONITOR BELOW". So monitors are an established, signed part of the station's own wayfinding. | Blue, and everywhere | — | STATED | 1 | `reference/01-station-exterior/welcome to babylon 5.webp` | `no` |
| **Alien signage systems** | Three letterform families for procedural signage: **lunate** (crescents, half-moons, filled discs, round terminals, gold on black), **rectilinear** (right-angle strokes, blocky counters, stepped forms), and **curvilinear** (bowls, hooks, open counters, single stroke) — the last being the same family as the Zocalo wordmark. | all | — | STATED | 1 (the screencaps) / 4 (the transcribed alphabets) | `reference/11-props-and-technology/Vorlon, Narn,and Centauri script examples.jpg` | `no` |

---

## 15. CRIME AND THE BLACK MARKET

| location | what it is | sector | level/deck | placement | auth | source | built? |
|---|---|---|---|---|---|---|---|
| **The Downbelow black market** | The station's illicit economy, geographically coincident with Downbelow and its 90% crime share. **Needs no dedicated room** — it is stalls, back corridors, sealed sections and NPC behaviour in the volume §11 already describes. | Brown | outer ring | IMPLIED | 4 | https://babylon5.fandom.com/wiki/Downbelow | `no` |
| **N'Grath's premises** | The criminal kingpin's base — a **non-oxygen-breathing bipedal insectoid** who **rarely leaves his quarters in the alien sector**, dealing in weapons, hitmen and bodyguards, and who **operates out of Down Below**. In era for S2–3. **Note the placement tension**: his quarters are in the *alien sector* (Green) and his operation is in *Down Below* (Brown). That is a two-room character, and both rooms are canon-shaped. | Green (quarters) + Brown (operation) | — | STATED | 4 | https://babylon5.fandom.com/wiki/N%27Grath | `no` |
| **Thieves Guild presence** | An organised criminal network with branches "practically everywhere", including B5. A faction, not a building. | Brown | — | STATED | 4 | https://babylon5.fandom.com/wiki/Thieves_Guild | `no` |

---

## 16. UNPLACED — known, wanted, and the show never says where

An unplaced location we know about is far more useful than a gap we do not. These are real
places with no sourced position. Each carries a proposal in §17.

| location | why it is unplaced | proposal |
|---|---|---|
| The War Room | No source assigns it. Set is S3 (late in era). | P-01 |
| The resident commercial telepath's office | Role is canon; room is not placed. | P-02 |
| Morgue / mortuary; cryo storage | No source we hold names either. | P-03 |
| The brig / holding cells | Security Central is placed; its cells are not. | P-04 |
| Security checkpoints | Distributed; no source enumerates them. | P-05 |
| Ministry of Peace / Nightwatch meeting space | Faction is canon; premises are not. | P-06 |
| Hydroponics — which deck | Named in a rosette and on the schematic, but the *ring* is not resolvable. | P-07 |
| Sanctuaries (4) — what they are | Counted by Contract 5, function never stated. | P-08 |
| The interfaith chapel | No in-era placement found. | P-09 |
| ISN bureau | Possibly should not exist in S2–3 at all. | P-10 |
| Observation Dome 2's function | Counted; function never stated. | P-11 |
| Gymnasium / training facilities | Not found in any source consulted. Security and Starfury pilots train somewhere. | P-12 |
| Machine shops (small-scale) | "Maintenance and repair facilities" is placed; a workshop a player can walk into is not. | P-13 |
| Schools, crèche | 250,000 residents implies children. **No source found mentions either.** Recorded as a genuine unknown rather than assumed. | — |
| The garden's civic building's *function* | We have six storeys of authority-1 architecture and no idea what happens inside it. | — |

---

## 17. PROPOSED PLACEMENTS — the reasoning

**Every one of these is authority 5.** If any is built, it goes in `canon/INVENTIONS.md` with
what would overturn it. None may be recorded as canon.

**P-01 — The War Room: adjacent to C&C, one deck inboard, in Blue.**
It is a command function requiring the same security perimeter and the same personnel as C&C,
and the frame shows an **arched structural frame continuing the corridor chamfer language**, so
it is a normal station volume rather than a dome. Putting it behind C&C keeps the walk short,
which the show's blocking requires. *Overturned by:* any source placing it elsewhere; note the
set is S3, so it may not exist early in the era.

**P-02 — The commercial telepath's office: Red, on the Business District ring.**
The role is commercial — monitoring business negotiations for fees — so it belongs beside the
clients. `LICENSED PSI` being a first-class identicard field means the station tracks telepaths
administratively, which argues for a registered, findable office rather than a private room.
*Overturned by:* any source placing it in Blue with the command staff.

**P-03 — Morgue and cryo storage: Blue, on the Medlab One deck, hull-side of the medlab.**
Both are cold, both are low-traffic, both are legally part of the medical chain of custody, and
both need discreet routing to a docking bay for repatriating remains. Hull-side because
refrigeration next to vacuum is the cheap answer and because it keeps them off the public route.
*Overturned by:* any source placing a morgue in Downbelow, which would be equally plausible
dramatically and would change the tone completely.

**P-04 — The brig: Red, immediately adjacent to Security Central, one deck inboard of it.**
Security Central and the Law Courts are both placed in Red's inner rings by the Red rosette. A
brig that is not walkable from both is a brig that generates prisoner transport every scene.
Inboard means lower gravity than the concourse, which is a small mercy and an easy stair.
*Overturned by:* any source placing detention in Blue with EarthForce.

**P-05 — Security checkpoints: at every sector boundary and at every lift lobby serving a
restricted ring.** Blue is explicitly access-restricted, and the Alien Sector is airlocked.
Those two facts alone require a controlled boundary; making it uniform across sector boundaries
is the cheapest consistent rule and it gives the identicard reader a job everywhere. *Overturned
by:* footage showing free movement across a sector boundary.

**P-06 — Nightwatch: no premises. A room they borrow.**
Nightwatch is a network of ordinary personnel with armbands, not a garrison. Giving it a
headquarters would make it look like a rival police force, which is the opposite of what makes
it frightening. **Propose that it meets in one of Red's rentable ceremonial rooms** — a
propaganda organisation using the civic function room is exactly right and costs nothing to
build. *Overturned by:* any source giving MiniPax a station office.

**P-07 — Hydroponics: the drum's sub-floor deck stack, not the drum floor.**
Racked hydroponics under lights is a *building*, and the drum floor is open agriculture — the
authority-1 frames show **fields and hedgerows**, which is a different agricultural technology.
The sub-floor stack is 9 decks of enclosed volume immediately under the fields, at 1.013–1.117 g,
which is where a plant room goes. It also puts the oxygen plant next to the largest air volume
on the station. *Overturned by:* footage of hydroponics with the drum curve visible.

**P-08 — The four Sanctuaries are the four hull-facing contemplation rooms, one per quadrant of
the forward structure.** Contract 5 counts four; the fan description of "the Sanctuary" is a
large circular room looking out at the stars, open to the public and rentable. Four of them, one
per quadrant, gives every part of the forward structure a quiet room with a star view and
explains why the count is four rather than one. **This also proposes that the observation
rotundas are the drum-facing equivalents** — rotundas look in at the Garden, sanctuaries look
out at space. That is a satisfying symmetry and it is *our invention*, resting on one interior
frame whose sector attribution is a folder name. *Overturned by:* Contract 5's uncropped detail
row, which would say what a sanctuary is.

**P-09 — The interfaith chapel: one of Red's rentable ceremonial rooms, permanently allocated.**
The station demonstrably hosts every species' observances and demonstrably has large hireable
rooms in Red. Making one of them the standing chapel needs no new geometry and no new canon; it
is a signage and scheduling decision. *Overturned by:* an in-era source placing a dedicated
chapel.

**P-10 — ISN: broadcast presence only, no bureau, for S2–3.**
The station-based ISN crew story is **S4 and out of era**. What *is* in era is ISN as a
watchable channel turning propagandist. **Propose ISN as content on every Babcom screen and
public monitor and no ISN office at all.** This is the cheapest possible way to deliver the
single most era-defining piece of ambience the station has, and building an office would import
S4 into an S2–3 station. *Overturned by:* an in-era frame showing an ISN office aboard.

**P-11 — Observation Dome 2: the traffic and approach-control annexe.**
Dome 1 is C&C and handles all ship movement. A second dome on the forward structure with no
stated function, on a station with 24 docking bays, 28 cobra bays and constant traffic, is most
plausibly the overflow: approach control, docking control, or the defence-grid control centre
that fan sources place in Blue. *Overturned by:* Contract 5's uncropped detail row.

**P-12 — Gymnasium and training: Blue, on the personnel-quarters ring.**
Two Starfury squadrons and a security force train somewhere, and Blue's **0.603 g** makes it the
worst place on the station to build strength — which is itself an argument for a *deliberate*
high-gravity training facility. **Propose the gym in Grey instead, at 1.445 g**, as EarthForce
conditioning: the heaviest habitable deck in the station, used on purpose. That turns a
throwaway room into a place that could only exist on this station. *Overturned by:* anything.
This is the most speculative proposal in the document and it is flagged as such.

**P-13 — Walk-in machine shop: Grey, ring 1, beside the fabrication furnaces.**
"Maintenance and repair facilities" and "fabrication furnaces" are both placed in Grey by the
rosette. A player-scale workshop is the human-sized end of the same function and belongs at the
same address. *Overturned by:* nothing likely; this is low-risk.

**P-14 — The sealed Markab quarter: Green, ring 0, deck 3, immediately beside the Alien
Sector.** The extinction is authority 1 — the Markab die of the plague in "Confessions and
Lamentations", S2E18, squarely inside the S2–3 datum — and nothing places their quarter. Green's
outer ring already holds the Alien Sector and the alien residential quarters, so a non-human
community's quarter belongs there and nowhere else; putting it next door to the airlocked
multi-environ sector also means a player who walks the alien quarter meets it without going
looking. **Its footprint is not proposed at all: 12.0 × 58.32 m is `npc/crowd.py::EXTENTS`
verbatim**, so the register and the crowd model agree by construction rather than by discipline.

The reason to build a room nobody can enter is that **its emptiness is the content**. It is a
measured zero over a real floor rather than a missing entry, which is the distinction
`npc/crowd.py`'s own comment draws, and it is the one place on the station where the era lock
pays for itself: a station set in S2–3 and not showing this is a station that has not noticed
its own history. *Overturned by:* any source placing the Markab elsewhere aboard, or showing
their quarter reopened or repurposed within the era.

*Not proposed, and deliberately: `refugee_reception`.* It appears in `npc/schedule.py`'s
`Role("refugee", …)` as a workplace and reads like a missing register row. It is not one.
`npc/resident.py::WORKPLACE_FUNCTIONS` resolves a workplace to **every place carrying a set of
functions** — for refugees, `residence` + `short_stay` + `arrival` — and that table's own header
says why: *"the join is by function, not by a second list of keys, because a table of keys is a
copy of a decision and every time this project has kept two copies of one decision they have
drifted."* **Fourteen of its nineteen keys are aliases rather than places** — `concourse`,
`engineering`, `medlab`, `hospitality`, `sanctuary`, `customs_hall`, `docking_bay`, `patrol`,
`traffic_control`, `business_district`, `green_sector`, `grey_industrial`, `waste_management`
and `refugee_reception`; only five (`cnc`, `council_chamber`, `downbelow`, `hydroponics`,
`zocalo`) happen to share a name with a register row. Adding `refugee_reception` to the register
would create exactly the duplicate the table exists to prevent, and would single out one alias
of fourteen for no reason but that somebody grepped for it.

---

## 18. WHAT THIS DOCUMENT COULD NOT DETERMINE

1. **Which sector the drum is.** C-003. Every drum-floor row above — Earhart's, Fresh Air, the
   Zen Garden, the Garden itself — is placed *relative to the drum* for this reason. The
   authority-4 sector ordering found this session (X-3) agrees with `other map.png` exactly but
   is very likely an echo of the same print source, so it does not close it.
2. **Which ring is level 1, and how many levels.** C-004 — and this research found a *third*
   possible reading (§1) rather than narrowing the existing two. **The lift-car display is still
   the single highest-value acquisition for this project.**
3. **How many Medlabs.** Three sectors are named; no count exists.
4. **The count of anything in Downbelow.** Population, extent, how many decks. The reference set
   holds exactly one Downbelow-class frame and it is S5.
5. **Whether the observation rotundas face in or out.** §6, P-08.
6. **What a "Sanctuary" is.** Counted four times by Contract 5, never defined.
7. **Whether the number in `Grey 17` is a deck, a level of several decks, or a 10° wedge.** §1.
8. **Anything about schools, children, or families**, on a station of 250,000. No source
   consulted mentions them. This is a real hole in the "living thing" brief.
9. **The interior of Yellow Sector.** The reference folder is empty, the rosette is machinery,
   and no interior frame exists. Yellow is 42% of the station's length.

**What would settle the big ones, in order of value:**

| Gap | What closes it |
|---|---|
| C-004 | **One lift-car display.** Or an uncropped Security Manual sheet. |
| C-003 | Any source placing the Garden or Downbelow in a *named sector at a longitudinal position*. |
| §1's third reading | A corridor placard frame legible enough to read the number, in a location we can identify radially or angularly. |
| Medlab count | Any station-services directory. |
| Downbelow | Any in-era Downbelow frame. Currently **zero**. |

---

## 19. WHAT TO BUILD NEXT, RANKED

Ranked by *value per unit of risk* — how much of the owner's request each unlocks, divided by
how much of it C-003 and C-004 could invalidate.

1. **The Zócalo.** Highest value, lowest risk. It is the station's main social space, we hold
   **three authority-1 frames** including a 1440×1080 one, its two-storey form and its whole
   material palette are already extracted, and **nothing about it depends on either blocking
   conflict** — it is an outer-ring concourse either way. It is also where crowd density, alien
   signage, commerce and NPC schedules all become visible at once.
2. **The customs hall and arrival concourse.** The player's first room, and the only place the
   station explains itself — six atmospheres, Earth Mean Time, identicards, the Business Center.
   Authority-1 signage, verbatim. Placement is uncontested (Blue, adjacent to the docking bays).
3. **A docking bay interior.** Two authority-1 frames plus a third in the Vorlon bay; the
   dock-worker scale anchor is measured; and it is the hinge of the seamless launch-and-dock
   requirement the flight and docking physics already support. Note the deck markings must be
   sized against the **eleven dock workers**, not against the Starfuries.
4. **C&C.** The most-seen room on the show, an authority-1 frame, and it forces the exterior
   `domes` component to become real geometry rather than a box — so it pays a structural debt.
5. **The Garden's ground-level architecture.** The drum shell and heightfield exist; what is
   missing is the townscape. We hold four authority-1 frames of it. Budget is the constraint:
   **0.06 tri/m²**, so buildings are the only thing that gets mesh.
6. **The Council Chamber.** One strong authority-1 frame, an unmistakable silhouette, and it is
   the room that makes the diplomatic layer legible.
7. **Downbelow.** Enormous value for the brief — slums, lurkers, crime, waste — and the **highest
   risk in the list**, because C-003 decides whether it is in the drum sub-floor or in Grey, and
   the only frame we hold is out of era. **Build the corridor character, not the address.**
8. **The Alien Sector and Kosh's quarters.** The alienness the brief asks for, and it is where
   the six-atmosphere system becomes a game mechanic rather than a sign. Blocked less by C-003
   than by having only one frame of a corridor and one of a wall.

**Three things that should be decided before any of it is dressed:**

- **Cell counts should be drawn from divisors of 36** if the 10°-region reading is ever adopted
  (§1). Grey's 18 is already compliant; Green's 15 is not. Cheap now, expensive later.
- **The `LEVEL` plaque is signed on corridor walls at authority 1.** Whatever C-004 resolves to,
  the wayfinding asset exists and its typography is known. It can be authored now with the
  number as a parameter.
- **Gravity should drive placement, not just physics.** 0.603 g in Blue against 1.445 g in Grey
  is the strongest characterisation tool the station has and it is free. Anything placed without
  regard to it is a wasted opportunity — see P-12.
