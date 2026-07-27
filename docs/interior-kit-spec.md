# Interior Kit — Specification

Derived only from authority-1 on-screen footage. **This spec is unblocked by C-003 and C-004**:
it describes what surfaces and fittings look like, not where levels sit or how sectors nest.
Building the kit now is safe; placing it is not.

Sources: `reference/09-garden-core-and-transit/central corridor.webp`,
`reference/04-sector-red/zocalo.webp`, `reference/11-props-and-technology/*`.
**Not** sourced from `reference/21-QUARANTINE-animated-film/`.

## 1. Structural language

| Element | Observation | Source |
|---|---|---|
| **Ring frames** | The hull's circular structural ribs are **exposed, not clad**. They arch overhead and frame views down corridors. The single most identifiable interior motif. | central corridor |
| **Corridor section** | A **chamfered box** — flat deck, upright walls, ~45° chamfers into a flat soffit. Circular ribs belong to tall volumes; a corridor built on them reads as a pipe. | grey level 1, corridor in alien sector |
| **Portals** | The section's ribs resolve as **heavy portal frames** at close spacing, with a **long linear light fitting in the soffit** and **bullnose pilasters** at the jambs carrying **segmented vertical light strips**. | grey level 1 |
| **Wall build-up** | Bottom to top: projecting skirt · set-back dado · **heavy rail band at hip height throwing a deep shadow reveal** · courses of large plates with recessed seams. | grey level 1 |
| **Door apertures** | A **chamfered polygon** — vertical jambs, ~45° corners, flat head, **raised threshold**. Set in a heavy frame with a pronounced reveal. Not a rectangle, not a circle. | corridor in alien sector |
| **Mezzanines** | Volumes carry a catwalk level above the main floor, with both occupied. Levels are not uniformly full-height decks. | central corridor |
| **Columns** | Vertical structural columns with panelled facing, spaced along open volumes. | zocalo |
| **Overhead truss** | Girder and truss structure visible above the ceiling line in service areas. | central corridor |

## 2. Surfaces

- Base palette is **desaturated grey**, warm-neutral rather than blue-grey.
- **Illuminated floor panels** set flush into a dark deck — a light source, not a texture.
- Wall surfaces are panelled in large flat plates with recessed seams, matching the exterior
  plating language (they should, being the same hull).

## 3. Colour accents

| Accent | Use |
|---|---|
| **Red-orange** | Handrails, stair edges, hazard framing. The dominant warm accent. |
| **Cyan / blue-white** | Neon signage, screen glow, panel indicators. |
| **Amber** | Practical lighting in commercial areas. |

## 4. Lighting

Low ambient, high local contrast. **Light comes from things that are objects in the world** —
signage, floor panels, stall practicals, screens — rather than from a general fill. Any lighting
solution that starts by raising ambient will read as wrong immediately.

## 5. Commercial fit-out (Red Sector / Zócalo)

Lightweight structures inside a hard shell: fabric awnings, string lights, hanging goods,
temporary-looking stalls against permanent architecture. **Alien-script neon** mounted high.
Crowd density high and species-mixed.

## 6. Deliberately not specified yet

Corridor width, ceiling height, door dimensions and deck spacing. All of these follow from
level topology, which is blocked on C-004. Guessing them would put a number in the schema that
later work would silently build on.

The kit still has to be built and looked at, so those numbers exist in `PROVISIONAL` in
`station/interior_kit.py` — flagged, in one table, and logged as `INV-007`. Everything the
footage actually establishes is recorded there as a **proportion** rather than as a metre
value: the proportions are sourced, the absolute size they multiply is not. Resolving C-004
should change the table and nothing that reads it.

**Not established at all: how a door opens.** No frame in the reference set shows a door leaf,
open, closed or moving. The aperture rules out an iris on geometry — an iris sweeps a disc and
leaves the four chamfered corners unswept — but the choice between a bi-parting pair and a
horizontally-splitting pair is a guess. Both are built; one entry in `PROVISIONAL` selects.
See `INV-008`.
