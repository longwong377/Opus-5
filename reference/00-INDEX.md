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
