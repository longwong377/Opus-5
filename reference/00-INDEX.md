# Reference Index

Maintained by Claude. Every reference file that lands in this tree gets catalogued here with
what was extracted from it and what it authorises us to build.

Status: **empty — awaiting first upload.**

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

### 09-garden-core-and-transit/delen and sheridan in elevator.jpeg
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
- Extracted, Zócalo commercial language:
  - **Neon signage in alien script** — cyan, curvilinear, mounted high above stalls. Signage is
    a primary light source, not decoration.
  - **Market stalls** with fabric awnings, string lighting and hanging goods, built as
    lightweight structures inside a hard architectural shell.
  - **Vertical structural columns** with panelled detail; **red-orange handrails** on the
    stairs and ramps, a strong recurring accent against otherwise desaturated grey.
  - **Crowd density is high and species-mixed** — this is the busiest public space on the
    station and its NPC density target should reflect that.
  - Lighting: warm practicals at stall level, cyan neon accents above, low ambient fill. The
    space reads dim overall with bright local pools.
- Feeds: interior kit spec, `16-signage-typography-ui`, NPC density targets for Red Sector
