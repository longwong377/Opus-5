# Project State

**Last updated:** 2026-07-27 · **Session 1**

## Where we are

Foundation laid. Reference sorted, canon established, the dimensional conflict that would have
poisoned everything downstream found and resolved, project memory and the parametric schema
framework in place. No geometry generated yet.

## Done this session

- **Verification loop proven.** Mesa lavapipe installed, enumerates **Vulkan 1.4 on CPU**
  (`llvmpipe`). Godot renders on Vulkan, so offscreen render → PNG → direct image inspection
  is a working aesthetic feedback loop with no GPU and no human. This was the single largest
  risk to the project and it is closed.
- **102 reference files sorted** from the dump into 13 subject/sector folders.
- **Canon codex written** — `canon/00-MASTER.md`, `CONFLICTS.md`, `INVENTIONS.md`.
- **C-001 resolved.** `other map 4.jpg` (Miller) states 3,108 m overall length; show canon says
  five miles. Show canon wins at 8,047 m; Miller's proportions rescaled by k = 2.5891.
  Had this gone unnoticed, the entire station would have been built at 39% scale.
- **C-005 found.** The Contract 5 schematic's scale bar is internally inconsistent — left group
  127.7 px/km, right group 125.7, but the 3→5 km span reads 105.5. The reproduction is spliced.
  That sheet is authoritative for topology only, never for dimensions.
- **Spin gravity derived.** 1.0 g at r = 278.3 m → ω = 0.18775 rad/s, period 33.5 s, 1.79 rpm.
  Sits below the human Coriolis tolerance threshold, which is a meaningful cross-check.
- **Project memory** — `CLAUDE.md`, ADRs 0001–0003, this file.
- **Schema v0** — `station/schema/station.yaml`: coordinate convention, global properties,
  section dimensions, exterior system manifest, sector model.
- **Tools** — `refzoom.py`, `measure_schematic.py`, `sort_references.py`.

## Next session — start here

1. **OW-001.** Pixel-measure `reference/02-station-cutaways-and-plans/other map 4.jpg` against
   Miller's own 3,108 m, extract longitudinal boundaries and the radius profile for every
   section and exterior system, rescale by k = 2.5891. Use that sheet — it is high resolution
   (2100×1275) and internally consistent. **Do not use the Contract 5 sheet for dimensions.**
2. **OW-002.** Derive Grey / Brown / Yellow extents as the remainder of the 8,047 m budget.
3. Build Godot from source with `precision=double`, publish as a GitHub Release asset so later
   sessions pull it in seconds rather than rebuilding for ~40 minutes.
4. First hull generation pass from the completed schema, rendered via lavapipe and inspected.

## Blocked

| Item | Blocked by | Needs |
|---|---|---|
| All interior level geometry | C-004 — level numbering unresolved | Lift display, deck plan, or dialogue tying a level number to a location placeable radially |
| Interior sector layout | C-003 — sector topology unresolved | Wayfinding signage or transit display showing sector adjacency |
| Grey / Brown / Yellow interiors | Zero reference coverage | Any material at all for these sectors |
| Starfury cockpit | Zero reference coverage | Cockpit interior stills |

## Reference gaps worth filling

Ranked by how much they unblock. Nothing here stops progress on the hull, but all of it
becomes blocking once interiors start:

1. **Deck plans or lift displays** — would resolve both blocking conflicts at once.
2. **Brown Sector / Downbelow** — zero files.
3. **Yellow Sector** — zero files.
4. **Starfury cockpit interior** — zero files; needed for Act III.
5. **Grey Sector** — one file.
