# Project State

**Last updated:** 2026-07-27 · **Session 2**

## Where we are

**Exterior structure complete; the two hardest physics problems are solved and unit-tested.**

**The station's core hull exists and is canon-verified.** 253,184 triangles, 8,046.9 m long
against canon's 8,047, generated entirely from `station/schema/station.yaml` and gated by 17
passing canon assertions. It renders and it is recognisably Babylon 5.

What remains on the exterior is every non-axisymmetric structure — fins, solar arrays, comms
pylons, cobra bays, cargo modules, domes. Interiors stay blocked on C-003 and C-004.

## Session 1 — foundation

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

- **OW-001 calibration established.** `other map 4.jpg` calibrated: station spans px 71→2048,
  centreline at y=388, giving **0.6361 px per Miller-metre** (1.572 Miller-m/px, 4.070 real
  m/px after k). Confirmed that Miller's Green Section outer length and Bio-Habitat interior
  length are both 1058 m and correspond to one continuous envelope — **the Green Section is
  the habitat drum**, 2,739.3 m at real scale.

- **OW-001 COMPLETE.** Longitudinal framework read segment-by-segment at 3× against a
  calibrated 50 m grid: fourteen features with z-extents from aft terminus to forward
  deflector spike. Logged C-006 (Miller's drawing vs his own table) and identified the
  explosive disconnect point at real z = 2,680 m as a structural boundary — everything aft
  of it detaches as one assembly.
- **Radius profile extracted.** 1,978 samples at 4.07 m spacing, `station/schema/radius_profile.json`.
  Hull is now fully defined as a surface of revolution. Two extraction failures found and
  fixed (inset photograph read as hull; leader lines followed instead of the outline —
  solved by a horizontal run-length filter, since leaders outnumber the hull locally and
  defeat outlier rejection). Verified by overlaying the trace back onto the drawing.
- **Independent cross-check passed.** Measured envelope vs table diameters: Red agrees to
  5.7%, Green to 3.9%. The two are derived independently, so this validates both the
  0.6361 px/m calibration and the k = 2.5891 rescale.
- **Finding:** the station's widest structure is the **aft hull block at ~957 m envelope
  diameter**, which Miller's table never names. Not the Red Section.

## Session 2 — the hull exists

- **Hull generator built.** `station/generate_hull.py` lathes the longitudinal framework and
  radius profile into a closed surface of revolution grouped by feature.
  **253,184 triangles, 8,046.9 m long** against canon's 8,047.
- **Canon assertions built.** `station/validate.py`, **17/17 passing**: gapless and
  non-overlapping features, subfeature containment, profile spans canon length, cross-check
  agreement, hull length, no unassigned or degenerate geometry, closed at both ends, triangle
  budget, max radius agreement, spin gravity exactly 1.000 g, period consistency, rpm below
  the Coriolis threshold. Runs in CI on every commit.
- **The generator caught a schema gap on first run** — 189 m and 5,888 triangles unassigned
  between green_section's table-derived end (5846) and its own habitat_cylinder subfeature
  (6035). That is C-006 surfacing as geometry. Fixed, and validate.py now blocks recurrence.
- **Software renderer built.** `tools/preview_render.py` — schema edit to inspectable image in
  ~5 seconds, no Godot and no GPU. First render is recognisably Babylon 5.
- **Ring artifacts diagnosed and fixed.** The raw profile flipped gradient sign on 20% of
  samples, which lathed into visible rings. A plain low-pass would have rounded off the real
  section transitions, so smoothing detects step edges (>4 px) and smooths only between them.
  **Sign flips 396 → 73, max radius unchanged at 480.3 m.** Verified by re-render.
- **Godot build fixed and running.** The proxy 403s GitHub archive and codeload paths;
  switched to a shallow clone.

## Session 2b — components

- **Component system built.** `station/components.py` with three placement kinds --
  `radial_array` (fins, solar arrays), `pylon_pair` (communications grid), `radial_band`
  (cobra bays, cargo modules). Driven entirely from a new `components:` block in the schema.
  **96 instances across 5 component types.**
- Components attach at the hull radius the profile reports for their z, so they stay welded
  automatically when the profile changes. No second source of truth to drift.
- Placements are cross-referenced three ways: Exterior map ordering, Miller's lettered
  callouts, and an envelope-excess analysis (a wide running minimum of the radius profile
  approximates the core hull; where the envelope exceeds it by >25 m, something protrudes).
  Agreement between a callout and an independent excess zone is what justifies each position.
- **Validator extended to 19 assertions**, including that every schema component actually
  produced geometry, and separate hull-vs-model max radius checks now that the comms grid
  tip (1,210 m) exceeds the hull.

## Component quality — honest assessment

The pipeline is correct; **the geometry is crude.** Components are box primitives placed by
rule. Specifically still wrong:

**Fixed after inspection:**

- Cooling fins clustered into a shuttlecock at one z. Contract 5 shows the radiators as a
  small number of discrete assemblies along the spine, and with a total of 12 that reconciles
  to **3 assemblies of 4** -- which is also why 12 appears in the Exterior map as one figure
  covering the whole system. `radial_array` now takes a `rings` parameter and clocks
  successive assemblies so they do not line up down the spine.
- The communications grid rendered as a thin I-beam because the panel had 893 m of length but
  only 90 m of radial depth. Now 300 m deep, so it reads as an array.

**Still wrong:**

- Components are box primitives throughout. No taper, no truss structure, no articulation.
- Solar arrays and cooling fins still read as the same kind of object.
- No greebling, no panel lines, no surface detail anywhere.
- Observation domes, rotundas, docking ports, sensor and deflector arrays not yet placed.

These need reference-driven refinement against `01-station-exterior/` before they are
believable. The value delivered so far is the *pipeline*, not the shapes.

## Known limitations of the current hull

The lathe produces the **core hull only**. A surface of revolution cannot represent the
non-axisymmetric structures, all of which remain to be added as separate components:
reactor cooling fins (12), heat exchange / solar arrays (12), communications grid pylons (2),
cobra bays (28), cargo modules (42), observation domes and rotundas, docking ports, and the
sensor and deflector arrays.

## Session 2c — reference correction and a topology elimination

- **CI added** (`.github/workflows/validate.yml`) — regenerates geometry and runs the canon
  assertions on every push, plus checks the invention log is intact.
- **C-007: radiators corrected.** The orthographic production sheet shows them **coplanar** —
  3 blades above the spine, 3 below, edge-on in top view and full-face in side view. I had
  built 12 arrayed around the axis from a bare count. Added the `planar_blades` kind.
  *Lesson recorded: a count in a labelled diagram does not imply an arrangement.*
- **Cargo modules moved to dorsal rows** (`dorsal_line` kind) — the sheet shows them as rows
  along meridians, not wrapped around the circumference.
- **C-003 half-resolved, by geometry rather than preference.** Deriving the Grey/Brown/Yellow
  extents showed the station is **50% pressurised, 50% structural**, with habitable volume in
  **four separated regions** and **Green alone at 73%** of it. Six sectors cannot be
  longitudinal slices — Grey and Brown would land on bare truss spine. The longitudinal model
  is rejected for interiors and INV-003 is marked overturned.
- **Godot build:** running but slow — ~1,155 of ~9,500 translation units at `-j2` after the
  first attempt was killed (OOM signature: log stops mid-compile, no error). LTO disabled and
  parallelism capped. This is hours of background work and blocks nothing, since
  `tools/preview_render.py` covers the visual loop for the structure-first phase.

## Session 2d — component set completed

- **Observation domes (2)** placed on the forward docking structure. Dome 1 is Command &
  Control — a place the player will stand, so its position has to survive into the interior
  layout rather than being treated as hull decoration.
- **Observation rotundas (4)**, **docking ports (2)** — primary north and service south per the
  Contract 5 cross-section — **forward swept arrays (4)** and **space traffic proximity
  arrays (4)** placed.
- New component kinds: `domes` (half-ellipsoid blisters on an arbitrary outward normal, with a
  properly constructed orthonormal frame so they sit flush at any hull angle) and `swept_fins`.
- **255,800 triangles**, 2,616 of them components. 19/19 assertions still passing.

## Session 2e — plating and the physics foundation

- **Hull plating.** Lathe radius modulated per plate cell, deterministic in (row, col) so
  regeneration stays byte-identical. Tuned by inspection: 37 m plates read as scales, 65 m
  plates read as plating. Depth 1.3 m.
- **Swept structures reshaped** — built from spanwise segments so the planform tapers and the
  trailing edge sweeps, instead of reading as flat planks. Heat-exchange collectors moved from
  a radial pinwheel to the swept form the top view shows.
- **Rotating-frame physics** (`station/physics/rotating_frame.py`, **25 tests passing**) —
  gravity gradient, centrifugal, Coriolis, apparent weight, frame transforms, launch velocity
  inheritance. Pure Python, no engine, no GPU.
- **Floating origin and precision** (`station/physics/floating_origin.py`, **10 tests
  passing**).
- **Constants tightened to 9 places.** Rounding ω to 5 places put floor gravity at 1.000351 g;
  the canon assertion for floor gravity is now 1e-6 rather than 0.5%, since it is derived and
  any drift means the schema has stopped agreeing with itself.
- **CI runs all three suites** — 20 canon assertions, 25 physics, 10 precision.

## Physics results worth carrying forward

| Quantity | Value | Why it matters |
|---|---|---|
| Drum floor speed | **52.2 m/s** | Inherited by anything launched — a cobra bay launch is a fling, not a drop |
| Apparent weight, walking | **0.947× to 1.054×** | Direction of travel changes your weight. A felt characteristic of a spun habitat |
| Coriolis climbing to axis | **1.13 m/s² spinward** | Ladders and lifts push you sideways |
| float32 at station nose | 0.49 mm | Station alone is marginally survivable in float32 |
| float32 at 50 km | 3.91 mm | **Starfury range is not.** Double precision is required by the flight envelope, not the station |
| Floating origin gain | 224× | 1.09 mm naive → 4.9 µm rebased at 40 km |

## Next session — start here

1. **Component refinement.** Placed but crude: the forward swept arrays read as flat planks
   rather than swept blades, and the heat-exchange collectors are still a radial pinwheel where
   the top view shows a swept form. Both need shaping, not repositioning.
2. **Surface articulation.** No greebling, panel lines or hull plating anywhere yet. This is
   where the procedural-detail approach from ADR 0002 starts earning its keep.
3. **Finish the Godot build** (~1,960 of ~9,500 objects) and publish the double-precision
   binary as a Release asset. Not blocking: `tools/preview_render.py` covers the visual loop.
4. **Starfury flight model** — Newtonian 6-DOF, RCS allocation, rotate-independent-of-velocity.
   Unblocked, and the same pure-Python-then-engine approach as the rotating frame.
4. **C-003 / C-004.** Still blocking interiors. Radial level numbering is now the leading
   hypothesis (see C-003 UPDATE), but needs a lift display or deck plan to confirm.

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
