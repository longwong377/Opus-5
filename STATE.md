# Project State

**Last updated:** 2026-07-27 · **Session 2q** (+ adversarial verification)

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
- ~~No greebling, no panel lines, no surface detail anywhere.~~ Done in session 2n.
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

## Session 2f — Starfury flight model

- **`station/physics/starfury.py`, 18 tests passing.** Newtonian 6-DOF, quaternion attitude,
  discrete thrusters with position and direction rather than an abstract force vector, and
  Euler's equations including the gyroscopic term so a tumbling Starfury precesses.
- Thrust is **allocated** across thrusters, so a demand the layout cannot satisfy comes out
  partially satisfied instead of silently exact. Pretending otherwise would make the craft
  feel like it has thrusters it does not.
- **The defining property is proven, not assumed:** the craft rotates 344° with velocity
  drift of exactly 0.000e+00 m/s. Flip-and-burn decelerates at thrust/mass to 0.01 m/s.
- **Cobra bay launch works from the physics alone.** Released at rest in the drum, the craft
  carries 52.2 m/s of inherited tangential velocity and coasts **1,313 m clear in 30 s and
  4,710 m in 90 s with no thrust at all.** The station throws it — which is exactly what the
  show depicts and why cobra bays need no catapult.
- `tools/plot_trajectory.py` plots flight paths over the real hull silhouette.
- **Aurora performance:** 18.38 m/s² on the mains, 1.87 g.

## Session 2g — docking

- **`station/physics/docking.py`, 15 tests passing.** A bay on the rotating hull is not a
  fixed target: it travels at 52.2 m/s on a circle whose normal sweeps a full turn every
  33.5 s, so guidance is *interception of a known trajectory*, not pursuit.
- **Station-keeping is not zero velocity.** Holding position 200 m off a bay requires
  **89.8 m/s** — more than the bay itself, because the standoff point orbits at a larger
  radius. A craft that stops dead relative to the station centre is **772 m off the bay
  within 10 seconds.**
- Contact is gated on three independent conditions — closing rate, lateral drift, and
  attitude alignment. Failing to spin-match passes the closing-rate check and fails on
  **52.2 m/s of lateral drift**, which is a scrape along the hull rather than a dock.
- **Axial ports have no tangential velocity to match at all.** That is the design rationale
  for the forward docking sphere and why large ships use it rather than a rim bay.

## Session 2h — core shuttle and radial transit

- **`station/physics/core_shuttle.py`, 18 tests passing.** Rim-to-axis transit through the
  gravity gradient, plus the axial run itself.
- **The headline result, measured not assumed.** Coriolis on radial motion is 2ωv, so peak
  lateral load scales inversely with transit duration:

  | Rim → axis in | Peak lateral |
  |---|---|
  | 8 s | **2.00 g** |
  | 60 s | 0.27 g |
  | 120 s | 0.13 g |
  | 300 s | 0.05 g |

  Holding it under 0.12 g needs **133 seconds**. A lift from the rim to the core shuttle is a
  **two-minute-plus ride** during which weight drains away and an unexplained sideways push
  builds and fades. That is a felt journey, and it falls out of the geometry rather than being
  a design choice.
- The car also has to shed **52.2 m/s of tangential speed**, costing 0.13 g along the direction
  of rotation. Axial run across the rotating assembly: 99 s at 1.2 m/s².
- `tools/plot_transit.py` plots the ride profile.

## Test suites — all green

| Suite | Tests |
|---|---|
| Canon assertions | 20 |
| Rotating frame | 25 |
| Precision / floating origin | 10 |
| Starfury flight | 18 |
| Docking | 15 |
| Core shuttle | 18 |
| **Total** | **106** |

## Session 2i — engine pipeline and budgets

- **glTF export** (`station/export_gltf.py`) — 23 meshes, 256,232 triangles, 21.5 MB. OBJ has
  no normals, no material bindings and no hierarchy; glTF is what Godot imports natively and
  it preserves per-feature grouping, so hull sections stay individually addressable for
  streaming and damage states. Normals are per-face because the hull is faceted by design.
- CI **structurally validates the glb** — magic, version, declared vs actual length, chunk
  types, buffer agreement, and every accessor fitting inside its bufferView. A malformed
  export that Godot silently half-imports would be miserable to debug later.
- **Performance budget gates** (`station/budget.py`) — the promised numeric enforcement, since
  framerate cannot be measured without target hardware. Currently **4/4 within budget**:

  | Metric | Now | Budget |
  |---|---|---|
  | Triangles | 256,232 | 400,000 (64%) |
  | Draw calls | 23 | 64 (36%) |
  | Vertex bandwidth | 18 MB | 32 MB (58%) |
  | glb on disk | 22 MB | 64 MB (34%) |

  The exterior gets a deliberately small slice — ~2% of frame budget — because it is
  always-visible background competing with interiors, NPCs and effects.

- **Two references catalogued.** The elevator still is from the 2023 animated film, not the
  original series — marked do-not-model-from. The arrival-concourse frame is authority 1 and
  its in-universe cutaway shows parallel longitudinal lines consistent with **radially stacked
  decks**, which corroborates the radial reading of C-004 without resolving it.

## Session 2o — radiators measured, not guessed

- **Radiator blades rebuilt from the production sheet.** They are **lozenges**, not tapered
  plates: narrow at the bolted root, widest ~28% out, long slow taper to a capped tip. A
  root-to-tip taper gives a wedge and loses the silhouette entirely.
- Measured proportions off the sheet: **~7:1 span to max width**, three per side sitting close
  together with gaps about equal to their own width. The previous values were 3:1 spread over
  730 m, which read as three separate paddles rather than one radiator bank.
- Added the structural frame around the panel, root mount blocks, tip caps, and the spine rail
  the blades stand on — on the sheet the blades never touch the hull directly, and that
  horizontal base line is a large part of the read.

## Session 2r — interior triangle budget

- **`budget.py` now gates the interior**, which previously had no gate at all. 8/8 passing.
- Gated on **what is visible at once, not total built geometry**. Totalling the interior is
  meaningless under the concentric-ring topology: ring 1 alone is 2π×278.3 = **1,749 m of
  circumference per sector**, and five rings across six sectors run to millions of triangles
  that are never simultaneously in frame. Occlusion culling means the cost that matters is the
  current cell plus what is visible through its portals.
- Measured against a deliberately pessimistic visible set — a 50 m sight line with a crossing
  at each end:

  | Metric | Now | Budget |
  |---|---|---|
  | Corridor rate | 285 tri/m | 400 (71%) |
  | Junction | 1,400 tri | 2,000 (70%) |
  | Visible structure set | 17,032 tri | 60,000 (28%) |
  | Share of frame | 1% | 5% (28%) |

- The corridor rate is measured **marginally** (20 m minus 1 m, over 19), because a run's fixed
  end caps would otherwise make a short sample look far more expensive per metre than a long one.
- 60,000 is structure only: the same view has to carry props, fittings, signage, NPCs and
  whatever is through the windows. If structure alone reaches 60 k the kit has become too
  expensive to dress.

## Autonomous continuation

A **6-hourly** trigger (`trig_01JS1VWf6yada5x6maPMAzza`, fires at :45) continues the plan
without prompting. It reads CLAUDE.md and this file, and:

- **Stops immediately and cheaply if everything on the next-session list is blocked.** It is
  told explicitly not to invent work to fill the time.
- Does **exactly one coherent increment** per firing — build, test, look at it, commit, update
  this file, stop.
- Does not spawn a workflow unless the work genuinely needs parallel fan-out.

Workflows are capped at **~5 agents** by owner decision. The adversarial verify pattern stays —
it caught a door interpenetrating a portal frame and a greeble call-signature mismatch.

To change cadence or stop it: `update_trigger` / `delete_trigger` with that id.

## Session 2j — THE ENGINE RENDERS THE STATION

**The full pipeline works end to end, with no GPU anywhere in it:**

```
station.yaml -> generate_hull.py -> station.glb -> Godot 4.4 (precision=double)
             -> Vulkan 1.4 on CPU (Mesa lavapipe) -> PNG -> read directly
```

- **Godot double-precision build finished** — 61 minutes, 147 MB,
  `godot.linuxbsd.editor.double.x86_64`. Binary lives at
  `/home/user/godot-build/godot-4.4-stable/bin/` (container-local; publish as a Release asset
  so future sessions do not rebuild).
- **`tools/build_and_render.sh`** runs the whole chain in one command.
- **Headless needed Xvfb.** Godot's `--headless` disables rendering entirely, so a virtual
  display plus the lavapipe ICD is what actually produces frames. Godot reports
  `Vulkan 1.4.318 - Forward+ - llvmpipe` — the software rasteriser doing real Forward+.
- **glTF export** (23 meshes, 256k triangles, 21.5 MB) with CI structural validation.
- **LOD chain** with switch distances derived from silhouette deviation, not facet width.
- **Budget gates** — 4/4 within budget, 64% of the triangle allowance.

Three visual corrections, each caught by looking: blown-out lighting, then missing material,
then framing. Materials live in the engine, not the export.

## Session 2k — reference audit

- **Eight animated-film frames quarantined.** They are from the 2023 animated feature, not
  live-action Babylon 5: wrong source against a brief that says original design in the show,
  wrong era (later blue uniforms against the S2–3 lock), and reinterpreted rather than
  reproduced sets. Moved to `reference/21-QUARANTINE-animated-film/` with a README, not
  deleted, so a future session does not rediscover and use them.
- **The trap is worth remembering.** These were the *highest-resolution interior references in
  the whole set* — ~2260×1180 against genuine screencaps at 800×600 or less. The pull toward
  them is exactly backwards. **Resolution is not authority.** They form an identifiable cluster
  by resolution and aspect ratio, which is how the remaining six were found after the first two.
- **New C-004 evidence, authority 1.** `central corridor.webp` shows **two occupied levels in a
  single volume** — a catwalk above a main floor. So a "level" need not be a full-height deck;
  it can be a mezzanine. **Level count and deck count need not be equal**, which means "Grey 17"
  does not imply seventeen decks of hull. Any interior layout assuming that would have been wrong.
- Same frame: the hull's **circular structural ribs are exposed rather than clad** — a primary
  motif for the interior kit regardless of how C-004 resolves.

- **Interior kit spec written** (`docs/interior-kit-spec.md`) from authority-1 footage only.
  Deliberately takes no position on level topology, so it is **buildable now** despite C-003
  and C-004. Corridor width, ceiling height, door size and deck spacing are left unspecified
  precisely because they follow from level topology — putting a guess there would seed a
  number later work silently builds on.

## Session 2l — interior kit built

- **`station/interior_kit.py`** — ring frames, deck panels with recessed light channels,
  handrails, wall plates. Rendered as a 20 m corridor it reads immediately as Babylon 5:
  receding exposed ribs framing the view down the passage.
- Dimensions that depend on level topology live in a `PROVISIONAL` dict, **not** as constants,
  so resolving C-004 changes one table rather than a hundred call sites.
- The first assembly produced a mangled deck: each piece is authored in its own natural frame
  and I was remapping axes with inline tuple comprehensions, which silently transposed the
  wrong pair. Merging now takes an explicit remap function per piece.

## Session 2m — NPC foundation

- **`station/npc/names.py`, 20 tests.** Per-species name grammars fitted to names actually
  spoken on screen, with the evidence recorded beside each pattern. Narn apostrophe structure
  from G'Kar and Na'Toth; Centauri house names established by Londo and Carn *sharing* Mollari;
  human surnames spanning several traditions because Earth Alliance is explicitly multinational.
  **Vorlon is a closed list, not a generator** — two attested names is not enough to generate
  from, and a test asserts it stays closed.
- **`station/npc/schedule.py`, 18 tests.** Species rhythms, roles, rotating shifts, and the
  statistical population layer. **A corridor at 03:00 is not empty** — it holds Minbari (broken
  sleep is canon) and Centauri (still in the bars), which is a specific and different crowd
  from 13:00.
- Two bugs caught, both design failure modes rather than typos:
  - Sleep resolving before work against an unshifted rhythm **put the entire night watch to
    bed** — security showed *zero on duty at 02:00*. Sleep now follows the shift offset.
  - The species mix summed to 0.94, so the aggregate layer **silently dropped 120 of every
    2,000 residents**. Exactly the quiet population leak the statistical layer exists to prevent.
- Logged as INV-004 and INV-005.
- **`CONTRIBUTING.md`** added — the loop, plus a table of every mistake made so far and its
  cause. All of them were caught by looking at output, not by reading code.
- **`docs/godot-binary.md`** — reproduction, the two build pitfalls (OOM at `-j4`, proxy 403 on
  archive URLs), and why a 52 MB build artifact is deliberately not in git history.

## Session 2n — exterior greebling

- **`station/greeble.py`** — procedural surface detail scattered by rule over the whole hull.
  Access panels, louvred vent banks, octagonal hatches, sensor blisters, antenna stubs,
  magnetic cleats, marker lights, and clamped conduit runs following the long axis.
  **70,778 triangles, 1,976 fittings in 662 assemblies plus 52 conduit runs** — 18% of the
  exterior triangle budget, taking the model to 82% with 73k spare.
- Driven from a new `greebles:` block in the schema: five density tiers assigned per
  longitudinal feature, from `clean` on the habitat drum to `industrial` on the reactor spine,
  a 13× spread. Logged as **INV-006**.
- **Determinism is asserted, not assumed.** Every instance is keyed on
  (seed, zone, cell indices) through a written-out FNV-1a, because Python's `str.__hash__` is
  salted per process and would have produced a different hull every run. Verified two ways:
  a new canon assertion that builds the pass twice and compares, and a byte-for-byte `cmp` of
  the OBJ across `PYTHONHASHSEED=1` and `PYTHONHASHSEED=99999`.
- **The first attempt was wrong and looking at it is what caught it.** 10–20 m fittings on an
  even lattice rendered as confetti — noise, not machinery. Two changes fixed it: fittings
  scaled up to 15–50 m, and single objects replaced by *assemblies* (one full-size primary plus
  small satellites) so there is a size hierarchy that reads at 200 m and at 20 km.
- **The conduit runs do most of the work.** A clamped line running 900 m down the flank of the
  drum is the most legible surface feature on the reference sheet, and one run is worth fifty
  scattered boxes.
- **Caught a real LOD regression.** Scattered detail does not decimate the way the lathe does,
  so greebles were a fixed 71k floor — **91% of lod3**. `lod.py` now drives a per-level greeble
  detail fraction (1.0 / 0.45 / 0.12 / 0.0) and lod3 is back to 7,016 triangles. Culling is a
  stable subset — verified that every lod1 greeble vertex exists in lod0 — so a switch removes
  fittings rather than rearranging them.

## Test suites — 151 tests green

| Suite | Tests |
|---|---|
| Canon assertions | 23 |
| Performance budgets | 4 |
| Rotating frame | 25 |
| Precision / floating origin | 10 |
| Starfury flight | 18 |
| Docking | 15 |
| Core shuttle | 18 |
| NPC names | 20 |
| NPC schedules | 18 |

## Session 2p — interior kit: walls, doors, junctions

The corridor had ribs and a deck and no walls, so it read as a skeleton. It now reads as a
corridor. `station/interior_kit.py` gains `wall_assembly`, `portal_frame`, `pilaster`,
`door_frame`, `door_leaf`, `bulkhead`, `deck_grid`, `junction` and
`corridor_junction_section`, and `corridor_section` assembles all of it.

**The section was wrong and the reference says so.** Both authority-1 corridor frames --
`07-sector-grey/grey level 1.webp` and `05-sector-green/corridor in alien sector.webp` -- show
a **chamfered box**: flat deck, upright walls, ~45 deg chamfers into a flat soffit. The first
assembly used `ring_frame` and read as a pipe. `ring_frame` stays in the kit, because
`central corridor.webp` does show circular ribs -- of a two-storey volume, not a corridor. The
two are different elements and were being conflated.

**`grey level 1.webp` is the most useful interior frame in the set** and had never been
catalogued. Square-on it gives the whole wall build-up: projecting skirt, set-back dado, heavy
rail band at hip height throwing a deep shadow reveal, then courses of large plates with
recessed seams; bullnose pilasters at the portal jambs carrying segmented vertical light
strips; warm downlights low on the wall; a fine deck tile grid. All of it is now modelled and
all of it is logged as proportions, not metres -- `INV-007`.

**Doors: the aperture is sourced, the mechanism is not.** No frame in the reference set shows a
door leaf, open, closed or moving. The aperture is fixed -- a chamfered polygon with vertical
jambs, a flat head and a raised threshold -- and that **rules out an iris on geometry rather
than taste**: an iris sweeps a disc and leaves the four chamfered corners unswept. The
remaining two readings are both built and selected by one entry in `PROVISIONAL`, so
overturning the guess is a one-word edit. `INV-008`.

**Found while building: `_box` was producing inside-out solids.** Given corners in the obvious
order it emitted every face wound inward -- verified numerically, 12 of 12 triangles facing the
wrong way on a unit cube. Outdoors that only changes the shading, which is why it survived
several sessions of exterior work: a closed solid keeps its silhouette either way, so
proportions judged from those renders were still right and the lighting was not. Indoors it is
not subtle -- the camera is inside the geometry, so an inside-out wall is one you see straight
through. Fixed in `components.py` in the same window; the interior kit's `_selftest` asserts
its primitives face outward so it cannot come back unnoticed. (It did come back unnoticed, in
two functions the gate did not reach — see the verification note below.)

**Two more bugs, both found by looking:**
- The old `corridor_section` laid its deck with a negative-determinant remap and no winding
  reversal, so the floor was inside-out too. `_merge` now carries an explicit `flip`.
- A closure tiled into convex blocks shares internal faces, and a depth-sorted renderer draws
  them over the plate in front -- the bulkhead read as separate panels with joints radiating
  off every door corner. `_plate_with_hole` decomposes only the caps and rims the two loops, so
  there is no internal face to draw. It is also cheaper.

Verified by rendering from a 1.65 m eye height and reading the PNGs: a 21.6 m corridor with a
wall door and a bulkhead door, a four-arm crossing, and a tee. **7,656 triangles for 21.6 m**
(354/m); a crossing with four 7.2 m stubs is 10,644. Canon assertions 23/23, budget gates 4/4.

### Adversarial verification of 2p — three defects the render pass missed

**The corridor was open to space down both sides, its full length.** `wall_assembly` built its
chamfer leaning *outboard*, away from the corridor, so it roofed nothing and left a 0.5 m slot
between the soffit and each wall head in every bay. **7.9% of rays cast from head height
escaped straight out through the ceiling; none escaped sideways or down.**

It survived a seven-iteration render pass because **the preview background is black and so is
an unlit ceiling** — a hole and a shadow are the same pixels. The session read the symptom
correctly ("the ceiling was rendering as a void") and treated it as lighting, adding soffit
ribs to give the eye something to land on. Re-rendered against a magenta background it is
unmissable. *Lesson: render interiors against a colour that cannot occur in the model. A black
void is the one background that hides the failure interiors are most prone to.*

**`ring_frame` and `wall_panel` were both inside-out** — signed volume negative, every face of
every segment wound inward — at the same time as the note above claiming `_selftest` had made
that class of bug un-repeatable. The gate only covered `_slab` and `_prism`. Both functions are
unused today, which is why nothing rendered wrong; `ring_frame` is the piece explicitly kept
for the two-storey volumes in `central corridor.webp`, so the next session to build one would
have inherited it.

**Nothing in the kit ran in CI.** `.github/workflows/validate.yml` never invoked
`interior_kit.py`, so neither gate protected anything between sessions.

All three fixed: the chamfer leans inboard, both primitives are rewound, `_selftest` now gates
**every** primitive on signed volume plus a coverage test that a corridor is closed overhead
(each assertion was confirmed to fail on the reintroduced bug), and CI runs the module.

Still open, and reported rather than fixed:

- **A door bay has no wall build-up.** `corridor_section` passes `courses=False` for the bay a
  wall door takes over, so the skirt, dado, rail band and plate courses stop dead at the door
  and resume after it, leaving the door set in a blank plate. `grey level 1.webp` shows the
  build-up running continuously past portals. Needs the courses cut round the aperture.
- **INV-007's chamfered section is inferred, not observed.** `corridor in alien sector.webp`
  shows a chamfered *aperture*; nothing establishes the passage behind it has that profile, and
  `grey level 1.webp` shows a rectangular portal header. INV-007 and the spec now say so.
- The junction's cross-corridor deck tile pitch is 0.57 m against the arms' 0.605 m, because
  `deck_grid` divides a different width into a whole number of tiles. Along the run they align.

## Session 2q — reference mining: the two sheets that had never been opened

**No code changed. Documentation and reference filing only** — `reference/00-INDEX.md`,
`canon/00-MASTER.md`, `canon/CONFLICTS.md`, `docs/interior-kit-spec.md`, and nine files moved
into a new quarantine folder.

- **Two authority-3 files in `02-station-cutaways-and-plans/` had never been read.** Both bear
  directly on the blocking conflicts:
  - `b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp` — a **"Sectional Schematic"**
    carrying a **sector bracket that divides the station into six longitudinal bands**, five of
    them named. Band boundaries were measured from breaks and ticks on the bracket line and
    converted at 7.53 m/px.
  - `other map.png` — a **colour sector plate** carrying a colour-coded longitudinal strip and
    **six radial cross-section rosettes**, one per sector.
- **C-003 UPDATE 2.** `C-003 UPDATE`'s geometric refutation was aimed at the wrong target: it
  kills `other map 2.jpg`'s *ordering*, not longitudinal slicing. Under the authority-3
  ordering the aft structural half is **Yellow** (engineering), which is what belongs there.
  **Longitudinal slicing is back**; INV-003's overturn is itself overturned.
- **C-004's axis is settled: a level is a concentric radial deck.** Three independent lines —
  the rosettes, the sectional schematic's longitudinal decking (its own callout reads
  "CONCENTRIC PERSONNEL TRANSFER SYSTEMS"), and authority-1 footage
  (`03-sector-blue/Babylon_5_2-22_34b.jpg`, filed as an exterior shot and actually the drum
  interior along its axis). The Brown rosette also marks **"DOWNBELOW" on an outer ring by
  name**, which answers C-004's own standing objection from the source rather than by argument.
- **New authority-1 canon from signage** — station runs on **Earth Mean Time**, **six
  atmospheres** are available, humans are **atmosphere 02**, the identicard record schema, and
  **docking bays (24)**, which is a different system from the cobra bays of C-002.
- **Nine AI-generated character turnarounds quarantined** to
  `reference/22-QUARANTINE-ai-generated/`. Same lesson as folder 21 in a new costume: the
  largest "uniform reference" in the tree is a 2528×1696 PNG with its own generation prompt
  burned in. **Resolution is not authority.**

**Both conflicts stay OPEN and BLOCKING.** C-003 on the Green/Brown transposition — the two
authority-3 sheets disagree about which band is the 2,000 m habitat drum. C-004 on the
numbering convention — nothing numbers a ring, and getting the direction backwards inverts
every address on the station.

### Adversarial verification of 2q

Measurements re-derived independently and confirmed: the bracket boundaries (531/541 gap
midpoint 536 against the reported 537, every other within 1 px), the colour-strip hue bands
(Green 335–400, Red 401–538 — exact), all five duplicate claims, the file counts (100 / 83 live
/ 17 quarantined), and every cited reference path. The hull is untouched: 23/23 assertions,
4/4 budgets, 106+ physics tests, and the render is unchanged. Four corrections applied:

- `00-MASTER.md` carried a **stale "17–95 m"** for the boundary agreement that the measured
  table in `CONFLICTS.md` gives as 2, 74 and 96 m.
- **"Every band's contents match that sector's on-screen function" was not true**, and the
  exception matters. Band 4 — the one inferred to be Brown — also carries the **zen garden**
  and the **ambassadorial suites**, which are Green on screen. The table had listed only the
  three callouts that fit Brown. Corrected, and the omitted evidence is now weighed in C-003.
- **The missing sixth-band label is not a cropping artefact.** The sheet is cropped, but the
  sector-label row is intact (five labels in one band at y 271–285, no ink between x 521 and
  814). An uncropped scan will give the detail row; it may well not give the label. Chasing a
  better scan is therefore a weaker lead than it looked.
- The **Zocalo neon is `ZoCaLo`, six Latin glyphs** — the zigzag at the head is the Z, which the
  spec had described as a flourish beside the word.
- **The boundary agreement was oversold, and it is the load-bearing claim.** It was written up
  as "a stronger cross-check than anything else in the reference set". Tested against a null:
  mean miss 110 m over the six scored boundaries where random positions against the same 16
  candidate boundaries average 212 m — **p ≈ 0.06**. Real, weak, not proof. The headline "2 m"
  is a 4%-by-chance event and "three of six inside 100 m" is a 31%-by-chance event. Both
  `CONFLICTS.md` and the index now say so. *Lesson: "nearest boundary in our own schema" over a
  framework with sixteen boundaries is a generous test, and it needs a null before it counts.*
- Three live files — the **Contract 5 sheet**, `Exterior map.jpg` and `Interior map.jpg` — were
  neither index entries nor on the *Still uncatalogued* list, so the index's claim to list the
  whole remainder was false. Now listed.

Also flagged, not changed: the drum-is-Green reading is **better supported than the standoff
implied** — the drum is hollow in authority-1 footage and only the Green rosette is drawn
hollow — but a cartoon's fill is not a label, so C-003 correctly stays open.

## Next session — start here

1. **Refine the remaining crude components.** Radiators are measured (2o); still box
   primitives with no articulation: forward swept arrays, cobra bays, docking ports,
   observation domes and rotundas. Greebles cannot rescue a wrong silhouette.
2. **Emissive materials in the preview renderer.** `godot/materials/` has the `.tres`
   resources, but `tools/preview_render.py` has no concept of emission, so every deck light
   channel, pilaster strip and door indicator renders as grey plastic. The kit's whole lighting
   premise is currently untestable on the fast path.
3. **Deck tile phase across junctions** — the grid is not driven from a shared origin, so
   there is a visible seam at each crossing mouth.
4. **Publish the Godot binary** as a Release asset — container-local, 61 minutes to rebuild.
   See `docs/godot-binary.md`.
5. **C-003 / C-004** still block interior *layout*, on one narrow question: radial decks are
   established, but **which ring is level 1** is not.

## Blocked

| Item | Blocked by | Needs |
|---|---|---|
| All interior level geometry | C-004 — **numbering convention** unresolved. The axis is settled: levels are concentric radial decks | A lift-car display, a numbered deck plan, or dialogue tying a level number to a gravity. Nothing else will do — the deck plans themselves have now been found and they number nothing |
| Interior sector layout | C-003 — **Green/Brown transposition**. Sectors are longitudinal bands; the two authority-3 sheets disagree on which band is the habitat drum | Any source placing the Garden or Downbelow in a *named* sector at a longitudinal position |
| Deck spacing, ring radii, corridor width, ceiling height | Unavailable from any held source | The one sheet that draws decks has its vertical scale exaggerated ~2× (C-004 UPDATE item 3, same ruling as C-005) |
| Grey / Brown / Yellow interiors | Near-zero reference coverage | Grey has one frame; Brown has one misfiled frame; Yellow has none |
| Starfury cockpit | Zero reference coverage | Cockpit interior stills |

## Reference gaps worth filling

Ranked by how much they unblock. Nothing here stops progress on the hull, but all of it
becomes blocking once interiors start:

1. **A lift-car display, or any numbered deck plan** — the single highest-value gap in the set.
   It is the only thing that closes C-004. *Deck plans as such are no longer the gap: session 2q
   found six radial cross-sections. They name facilities and number nothing.*
2. **An uncropped scan of the Security Manual sectional schematic** — would supply the cut-off
   detail row. Note it is **not** likely to supply the missing sixth-band label, which is absent
   from an intact label row; this lead is weaker than it first looked.
3. **Brown Sector / Downbelow** — one misfiled frame
   (`01-station-exterior/sleeping-in-light-05.jpg`, S5, station derelict).
4. **Yellow Sector** — zero files.
5. **Starfury cockpit interior** — zero files; needed for Act III.
6. **Grey Sector** — one file, and it is the most useful interior frame in the set.

## Uncatalogued reference, and misfiled reference

`reference/00-INDEX.md` ends with two lists a future session should read before re-deriving
them: **Still uncatalogued** (~25 files, mostly single-character portraits and race-makeup
shots) and **Misfiled — recommended moves** (nine files whose folder is wrong, deliberately
*not* moved because the schema and specs cite some by path).
