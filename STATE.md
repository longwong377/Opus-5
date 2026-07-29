# Project State

**Last updated:** 2026-07-28 · **Session 3k** — the Alien Sector; ranked build list finished

## Where we are

**Exterior structure complete. The habitat drum is now built, inside and out, from the same
schema.** The volume where you look up and see ground overhead exists: banded ground, both end
caps, three guideway trusses carrying the habitat's lighting, and the three radial spokes —
42,696 triangles, all generated. See *Session 2u*.

**The station's core hull exists and is canon-verified.** 253,184 triangles, 8,046.9 m long
against canon's 8,047, generated entirely from `station/schema/station.yaml` and gated by 17
passing canon assertions. It renders and it is recognisably Babylon 5.

What remains on the exterior is refinement of the crude components — cobra bays, docking
ports, observation domes, rotundas are still box primitives.

**Interiors are not blocked.** C-003 and C-004 decide which *name* attaches to a volume, not
what shape it is; geometry is generated against `(sector, ring_index)` and labelled afterwards
by `bind_labels()`. When the conflicts close, the mapping changes and the geometry does not.

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

## Session 2t — exterior corrections from the reference sweep

- **Cargo modules: 42 → 6.** The 42 conflated two different things. Miller's table gives
  28 + 14 = 42 cargo **bays**, which are internal volumes; the orthographic sheet shows **six
  external modules** docked on a continuous raised dorsal rail with plinths between them. A
  station with 42 bays and 6 modules attached is not a contradiction — it is a station that is
  not full. The exterior systems list now says `cargo_bay` for the 42.
- **Forward "swept arrays" were wrong.** Built as four swept wings from a *top view alone*; the
  side view shows a single **flat plate-like communications array on a short pylon, blading
  forward** — a plane, not a wing pair. Four wings and one plate look alike in plan and nothing
  alike in silhouette, which is exactly how a plan-only read goes wrong. New `plate_array` kind.
- **CONFLICTS.md status header added.** The file is append-only, 1,378 lines, with eight C-003
  entries — one headed RESOLVED followed by four later notes narrowing it. A reader could act
  on a heading and be wrong. There is now a CURRENT STATUS table at the top, and the schema
  carries `assignment_status: OPEN_BLOCKING` with an assertion keeping it there.

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

## Session 2u — the habitat drum, built

The drum is the payoff of the structure phase: the volume where you look up and see ground
overhead. It is also the only surface in the project seen from its **concave** side, so every
convention built on the hull inverts there, and both times that mattered it failed silently
rather than loudly.

**Built** (`station/interior.py`, all of it generated, none hand-authored):

| Piece | What it is | Triangles |
|---|---|---|
| `drum_interior()` | inner shell as longitudinal land-use bands | 23,040 |
| `drum_end_cap()` | concentric ribbed dished bulkhead, both ends | 3,768 each |
| `guideway_truss()` / `drum_guideways()` | 3 Warren trusses with light runs | 11,796 |
| `drum_spokes()` | the 3 radial spokes at 120° | 324 |
| | **complete drum** | **42,696** |

**The "two end caps" open item was a misreading and is closed.** `Babylon_5_2-22_35a` is shot
forward through a drum tram's windscreen; the red-orange triangulated lattice converges to a
vanishing point with regular transverse ribs. It is the **tram guideway truss**, not a bulkhead.
There is one end cap, already measured in 2r, and it is now built. Full note in `CONFLICTS.md`.

**Newly sourced, and it settles a question that had no answer at all:** the habitat is lit from
**longitudinal light runs on the guideway trusses** — not an axial sun-strip, not the end caps.
`34b` shows the tubes alongside the truss, `33a` the rectangular fixtures on its underside.
Authority 1.

**Corroboration worth keeping.** The measured hub cone fills the inner ~20% of the cap. The
schema's core ring, read off an unrelated authority-3 print diagram, sits at r/R = 0.18. Two
independent sources 2% apart, so the cap is built to the schema's radius rather than a new
number, and the self-test asserts they stay within 0.03.

**Two silent failures caught, both from the concave side:**

1. The drum's faces were wound outward while the comment above them claimed inward. 95% were
   backface-culled and the render came out black — which reads as a badly placed camera, not as
   a bug. `_inward_fraction()` now measures it and the builder refuses to return geometry that
   would vanish.
2. The first viewpoint was hand-placed at the nominal 278.3 m floor while the band underneath
   was a 7 m settlement terrace at 271.3 m — five metres **inside the ground**. `stand_point()`
   now derives eye position from the land-use table.

**`tools/preview_render.py` gained what interiors need**: near-plane clipping (straddling
triangles were dropped whole, so everything nearer than one tessellation step vanished — a
black band that looked like missing geometry), `--pointlight` on the spin axis, `--headlamp`,
`--fog`, and `--tint` for judging composition by group.

**`SPOKE_COUNT` is now the single source of truth** for the drum's 3-fold radial structure.
Placement used to live in whichever script was rendering, so the trusses could silently stop
matching the spokes that carry them. `TRUSS_COUNT` derives from it and the self-test asserts it.

New inventions: **INV-011** (end-cap dish depth, rib sizes, per-course plate segmentation) and
**INV-012** (truss scale, height, count). `station/interior.py` self-tests at **62 assertions**
and runs in CI.

Renders: `docs/render-drum-interior.png`, `render-drum-endcap.png`,
`render-drum-endcap-detail.png`, `render-drum-standing.png`.

## Session 2v — the drum was hollow everywhere except in the ring model

Building the drum exposed a contradiction that had been in `ring_radii()` since it was written,
and that no test could have caught because no test asserted the thing it got wrong.

`ring_radii()` applied the same five concentric rings to every sector. In the drum that put
habitable decks at **228, 167 and 106 m radius** — which is the open air you look up through,
the volume whose existence is the entire point of the drum and is authority 1. It also put the
guideway trusses at 236.6 m **inside** one of those decks. Two subsystems built in the same
session disagreed about whether the same cubic kilometre was air or floor.

**The fix, and the reason it is more than a bug fix:** in the drum the habitable volume is the
stack **beneath** the ground, and beneath means radially **outward** — in spin gravity you stand
on the outside of the volume looking in. So the drum's decks run from the canon 278.3 m floor
out to the pressure hull, and everything inboard of the floor is air.

| | radius | gravity |
|---|---|---|
| pressure hull (inner face) | 310.8 m | 1.117 g |
| **sub-floor deck stack** | 278.3 → 310.8 m, **9 decks** | 1.013 → 1.117 g |
| habitat floor — the Garden | **278.3 m** | **1.000 g** |
| open air | 50.1 → 278.3 m | — |
| guideway trusses | 236.6 m | free flight |
| core / shuttle axis | 0 → 50.1 m | 0.18 g → 0 |

**Downbelow is heavier than the Garden.** That falls straight out of the geometry once the
direction is right, and it is the first thing the corrected model says that the wrong one could
not have.

**Derived result worth carrying forward — gravity is a property of sector, not of station.**
Because the station is rigid, everything at radius r feels ω²r, and the sectors have very
different radii:

| sector | outermost deck | gravity |
|---|---|---|
| Grey | 402.2 m | **1.445 g** |
| Green (sub-floor) | 310.8 m | 1.117 g |
| Green (Garden floor) | 278.3 m | 1.000 g |
| Red | 214.9 m | 0.771 g |
| Blue | 167.7 m | **0.602 g** |
| Yellow | — | see `sector_report()` |

Walking from Blue to Grey is a **2.4×** change in weight. That is the "real gravity changes"
the project set out to have, and it is free — no authoring, it is what the shape implies.

**Flagged, not resolved:** 1.445 g at Grey's outermost deck is high for somewhere people work.
That is a signal about either the disputed sector extents (C-003) or the fractional
`HULL_ALLOWANCE`, not about the physics. Recorded in INV-013 as a known weakness.

`drum_spokes()` now finds its own endpoints by ring *kind* rather than by index, since the drum
has three rings where every other sector has five. New assertions cover the whole failure class:
no deck stack may intrude on the open volume, the trusses must fly in open air, sub-floor
gravity must rise with depth, and non-drum sectors must still stack inward. **71 assertions.**

New invention: **INV-013** (6.0 m pressure hull skin).

## Session 2v (cont.) — the drum had no performance gate

`budget.py` gated the exterior and the corridor kit. The corridor gate is built on a **50 m
sight line**, because a wall stops you seeing further. That describes nothing about the drum:
standing in the Garden the far end cap is 2.6 km away, the ground overhead is 556 m up, and
every triangle in the volume is in the frustum at once. It is the **worst visibility case in
the project** and it had no gate at all.

Three gates added, and the third is the one that matters for what comes next:

| gate | now | budget |
|---|---|---|
| drum visible set | 42,696 tri | 300,000 tri |
| drum share of frame | 4% | 25% |
| ground surface density | 0.005 tri/m² | 0.5 tri/m² |

The drum earns a quarter of the frame rather than a corridor's twentieth — this is the view the
whole structure phase exists to produce — and it has to hold that with LOD, since the far half
of the drum is over a kilometre away.

**The number that constrains everything not yet built:** 257,304 triangles of headroom across
**4.5 million m²** of inner surface is **0.06 triangles per square metre**. That is the design
constraint for filling the drum, and it is emphatic: the ground is a **heightfield with
aggressive distance LOD**, not per-object geometry. Fields, roads and settlements are texture
and displacement; only what a person can walk up to gets mesh. Better to know that before
anything is authored than after.

## Session 2v (cont.) — the sight line was assumed; it is derivable

`budget.py` has gated interior cost on a **50 m sight line** since it was written, with the
comment "how far down a corridor before it curves or a door blocks". That is an assumption, and
it did not need to be one.

A ring corridor is occluded by **its own curvature**. Standing against the outer wall, the
furthest you can see is the chord tangent to the inner wall:

```
d = 2 * sqrt(r_outer^2 - r_inner^2)
```

Across every ring in every sector that gives:

| | sight line |
|---|---|
| Grey ring 1 (r = 402.2 m) | **91.3 m** — the worst case |
| Green sub-floor (r = 310.8 m) | 80.2 m |
| Blue ring 1 (r = 167.7 m) | 58.8 m |
| Yellow ring 4 (r = 52.1 m) | 32.5 m — the tightest |

So the gate was measuring against a view **1.8× shorter** than the station actually affords.
Corrected, the visible structure set is **28,791 triangles against 60,000** — still comfortable,
now honestly. `budget.py` computes it from the geometry rather than carrying a constant, and
the 50 m figure survives only as a fallback if the import fails.

**This also sizes the streaming cell**, which had no principled size before: a cell must be
wider than the view out of it or the player sees into territory that is not resident. At
1.5 sight lines of margin the drum's sub-floor ring wants **120 m cells (22.2°)** and Grey's
outermost ring wants **137 m (19.5°)**. That follows from the station's radius rather than from
a guess, and it is asserted per ring.

`interior.py` self-test: **96 assertions.**

## Session 2w — streaming cells, and "seamless" as a test

A ring corridor cannot be emitted whole. One deck of Grey's outermost ring is 2,527 m around
and would be **866,304 triangles** — fourteen times the entire interior frame budget, for one
deck of one ring of one sector. So the cell is the unit that gets built and streamed, and until
now nothing defined it.

`ring_cells()` divides a deck's circumference into an **integer** number of cells, so they tile
the circle exactly and there is no runt cell at 360° carrying a different amount of geometry
from all its neighbours. The size comes from `streaming_cell_deg()` — 1.5 sight lines — rounded
**down** in count so the actual cell is never smaller than asked for.

| sector / ring | cells | cell | sight line | triangles |
|---|---|---|---|---|
| Grey ring 1 | 18 × 20.0° | 140 m | 91 m | **48,128** |
| Green sub-floor | 15 × 24.0° | 118 m | 76 m | 38,720 |

**"Seamless" is the project's word, so it is a test rather than a claim.** Touching bounding
boxes do not prove two cells meet — a crack in a ring corridor is a hole a player falls through
at 1 g. `cell_seam_report()` compares the **shared edge itself**, vertex for vertex, in the
radial plane the cells were cut on: 22 vertices each side, identical to 0.1 mm, in every sector.
The **wrap-around** seam is asserted separately, because it is the one a `range(n)` loop never
reaches and the one where a rounding error in 360/n would surface.

`docs/render-cell-seam.png` shows it from inside, with the two cells tinted orange and blue: the
second cell only appears at the very end of the visible run, where the curve takes over. **The
player never sees a cell boundary as a boundary** — which is what sizing cells against the
sight line was for, now confirmed by eye as well as by assertion.

**Three findings worth carrying:**

- A **bent** corridor costs **+20%** per metre over the straight kit — 343 tri/m against
  285 — because each 2.5° section of the bend carries its own end caps. Gated, so the overhead
  stays visible rather than quietly growing. Welding sections is the fix if it does.
- Grey ring 1's cells are at **80% of the cell budget with structure alone**, before any
  dressing, props, signage or NPCs. Grey is the sector where the interior kit will have to get
  cheaper, and it is the widest ring in the station that is also the reason.
- `ring_arc()` now takes an explicit radius. It previously placed corridors at the ring's
  *mid-radius*, but a ring is a zone of a dozen decks and a corridor sits on **one deck's
  floor**.

`interior.py` self-test: **112 assertions.** `budget.py`: **14 gates.**

## Session 2w (cont.) — the whole interior, counted

`cell_manifest()` enumerates every streaming cell in the station. The headline:

> **210 decks · 2,330 cells · 80.6 million triangles** of interior corridor structure.

That number is ADR 0003's argument restated as a quantity. An interior this size **cannot be
committed as mesh files and cannot be hand-authored**. It is generated from the schema,
deterministically, and the repository stores the rule rather than the result. The manifest is
metadata only — 71 KB describing 80.6 M triangles.

| sector | decks | cells | outermost floor | gravity | cell cost |
|---|---|---|---|---|---|
| **Grey** | 90 | 1,210 | 402.2 m | 1.445 g | 48,128 tri |
| Red | 45 | 438 | 211.8 m | 0.761 g | 36,520 tri |
| Blue | 37 | 318 | 167.7 m | 0.603 g | 34,372 tri |
| Yellow | 29 | 226 | 137.1 m | 0.492 g | 32,480 tri |
| Green (sub-floor) | 9 | 138 | 281.9 m | 1.013 g | 38,720 tri |

**Grey is more than half the station's interior** — 90 of 210 decks. That is a consequence of it
sitting at the widest part of the hull, and it is quietly corroborating: the on-screen "Grey 17"
needs a sector with a lot of decks, and this one has ninety.

**Committed metadata is non-derivable metadata.** The first version serialised all 2,330 cell
records, every field of which follows from its deck's `cells` and `cell_deg`. That is the same
fact stored twice, and two copies eventually disagree. The file now carries the 210 deck records
and the rule for expanding them: 537 KB → 71 KB. CI regenerates it and fails on a diff, so a
schema change that moves deck radii or cell costs shows up as a change rather than as a stale
file nobody reran.

## Session 2x — the drum ground and the tram (IN FLIGHT, verification pending)

**Read this before starting anything.** Two modules from a 5-agent workflow are committed and
their self-tests pass, but the **adversarial verification pass had not reported when this was
written**. Treat them as sound-but-unreviewed. A third module (`station/core_tube.py`) was still
building.

| module | self-test | what it is |
|---|---|---|
| `station/drum_ground.py` | 69/69 | the drum's ground as a deterministic heightfield with a 5-level LOD chain |
| `station/tram.py` | 36/36 | the guideway tram — exterior car and a saloon authored for the `35a` passenger view |

Existing suites unaffected: validate 28/28, interior 117/117, budget 14/14, kit OK.

**Ground:** 448 × 640 cells (3.90 × 4.04 m), 280 patches. Uniform finest LOD would be 573,440
triangles — **2.2× the entire drum allowance**, which is the argument for the chain existing.
LOD-resolved and swept over 36 standing positions, the worst visible set is **105,920 triangles
(0.023 tri/m²)**, 41% of the headroom. Switch distances 245 / 550 / 1,270 / 4,668 m are *derived*
from measured height error against curvature sagitta — and the sagitta is asserted so a future
retune cannot silently fall back to facet width, which is the mistake `CONTRIBUTING.md` records.

**Tram:** car length stored as **4.0 truss bays**, not as metres, so it re-derives if INV-012 is
ever corrected. One car 1,252 triangles exterior, 4,158 with the saloon. Being literal about `35a`
made it 2.5× cheaper: the long bench has *continuous* cushions, and modelling one cushion per
seated person had cost 6,432 of the first build's 10,106 triangles.

New inventions logged: **INV-014** (the `LAND_USE` band table, logged retroactively — it had
driven the drum's appearance since the shell was first generated and was never written up),
**INV-015** (terrain spectrum), **INV-016** (parcels and roads), **INV-017** (tram dimensions and
suspension). **INV-012's wording was corrected**: "bay to depth roughly 1.2–1.5" was actually the
*zigzag* pitch, and a Warren triangle's base spans two bays, so the next reader to trust it would
have halved the truss.

### Defects these modules found in code they were forbidden to touch

All four are mine to fix and none is fixed yet. They are the next increment.

1. **`interior.drum_interior()` emits no risers between land-use bands.** Only the top surface of
   each band, so there are **six longitudinal slots the full length of the drum** wherever the
   relief changes. Invisible against a dark background, which is why four sessions of renders
   never showed it. Needs geometry and an assertion.
2. **`budget.py`'s ground-density gate is a gate in name only.** It measures the old flat shell
   (0.005 tri/m²) and will keep passing whatever the ground costs. It must call the ground's own
   worst-case, and the drum visible-set line must swap the 23,040-triangle shell for 105,920.
3. **Nothing in CI runs either new module.** `.github/**` was off-limits to the agents.
4. **The heightfield replaces `drum_interior()`'s shell but does not delete it**, and nothing stops
   both being emitted into one scene — they would z-fight across most of the drum. No assertion
   catches it.

### Also newly established

`29a` shows a **second, different transit system** — a green-and-yellow car on an elevated track
at garden ground level with its own station canopy, sharing nothing with the white/maroon guideway
tram. Not modelled. Recorded so a future session does not assume the guideway tram serves the
ground.

## Session 2y — the drum leaked, and the tests said it did not

The 5-agent verification pass reported. It ran the modules, computed clearances rather than
eyeballing them, and deliberately broke each self-test to see whether it failed. It confirmed
the builds were sound and found the defects were mostly in **my** code, in exactly the places
nothing was measuring.

### The drum was open in two places, for four sessions

`drum_end_cap()` was **4,064 boundary edges out of 7,684** — 3,744 of them nowhere near the rim
or the aperture. From inside the habitat you saw straight through the bulkhead in dozens of
places. Three independent causes, all fixed by one decision:

- per-course segment counts put a T-junction at every course boundary, because a coarse course's
  edge vertices are not a subset of a fine course's;
- the checker offset moved alternate plates 0.35 m in z with nothing bridging the step;
- the axial course walls were built at a third segment count again.

The cap is now **one continuous lathe** at a single fine segment count, with the plating as
material groups and the ribs and rim lights as closed boxes laid on top. The measured
"roughly square plates" character survives untouched, because the tessellation never carried it —
the **rib spacing** does, and that is still per-course. Checker-plating became a group rather than
0.35 m of relief, which is what it always was: a plating pattern, and 0.35 m on a 278 m radius was
never going to read as relief.

`drum_interior()` emitted only the **top surface** of each land-use band. Neighbouring bands differ
by up to 9.5 m (settlement +7.0 against water −2.5), so there were **six longitudinal slots running
the full 2,586 m of the drum**, straight through the ground into the sub-floor decks. Now closed by
riser walls — and the risers face the *low* side, because a cliff is seen from below and below here
means the larger radius.

**Neither was visible in four sessions of renders, because a hole shows the background through it
and the background is black.** An agent found them by rendering against magenta.

### The fix that matters more than the geometry

`boundary_edges()` now measures what no render could: edges used by exactly one triangle, welded on
rounded coordinates because the generators emit coincident duplicates. Six new assertions:

| | |
|---|---|
| drum shell closed except at its two ends | 374 boundary edges, all at z 3839 / 6425 |
| drum shell has no non-manifold edges | 0 |
| every land-use step closed by a riser | 6 steps |
| each cap closed except at rim and aperture | 192 edges, 0 stray |
| each cap has no non-manifold edges | 0 |
| ribs and rim lights are solids, not flat patches | opposing-face test |

**All three verified by deliberately breaking them**: removing the risers reopens 324 edges at
eleven z values; flipping the cap winding gives 0/1536 facing correctly; making a rim light flat
again gives 192 non-manifold edges.

That last assertion replaced a genuinely vacuous one. The old cap test put ribs and rim lights in an
`else` branch that scored **every one of 768 triangles as passing** — a test that could not fail, on
20% of the cap.

### Also this session

- **INV-018 / INV-019** log the core shuttle tube (radius 19.5 m, measured as a *ratio* so the
  sheet's 2× vertical exaggeration cancels) and its hub. `core_tube.py`, 65/65, now committed.
- **A wrong canon citation corrected in `core_tube.py`**: it defended its one measured dimension
  against **C-005**, which is a horizontal splice in the Contract 5 scale bar — a different defect
  entirely. The applicable ruling is `00-MASTER` "Radial spacing" / C-004 UPDATE item 3. The
  argument was always aimed at the right ruling; a reader checking the citation would have verified
  the wrong thing and concluded the defence held.
- **CI now runs `drum_ground.py`, `tram.py` and `core_tube.py`.** None of the three was wired into
  anything when it landed.

Drum visible set is now 51,128 / 300,000 (17%). `interior.py` self-test: **128 assertions**.

### Still open from the verification — next increment

1. **BLOCKING: tram cars pass through the radial spokes.** Confirmed independently by both
   verifiers — one by point-in-box over 3,144 car vertices (168 inside, 6.43 m deep), one by
   rendering it. The guideways are *deliberately* in the spoke planes (INV-012: the spokes are what
   hold a 2.6 km truss up), so this is structural, not a placement accident — and sweeping `phase`
   walks every car through its spoke whatever the static offset. Needs an aperture in the spoke
   where the guideway crosses, plus a spoke-clearance assertion in `tram.py`.
2. **`drum_ground`'s periodicity assertion is vacuous.** It compares `sample(0.0, w)` against
   `sample(1.0, w)`, but every consumer applies `u % 1.0` first, so it is a value compared against
   itself. Proved by monkeypatching in a real 3.295 m seam cliff — the test still reported 0.000
   and passed.
3. **`tram`'s "measured proportion" assertions are algebraic identities** that never touch the
   built geometry. They hold for `CAR_BAYS = -3.0`, `CAR_DEPTH_FRAC = 99.0`.
4. **Car length disputed between two authority-1 frames.** `34b`'s rectification gives 3.9 bays
   (96 m); `33a` shows a whole car with ~5 window bays and a length:height near 1.8:1 against the
   model's 21 bays and ~9:1, i.e. **3–4× shorter**. This needs recording as a conflict, not
   resolving silently in `34b`'s favour.
5. **Ground does not meet the end caps** — a 1.2 m axial mismatch, because the ground fades to the
   sector extent and the cap's outermost course stands 1.2 m proud of it.
6. **Ground tagging widths are bound to the LOD ramp width**, so avenues render 31.2 m wide and
   trunk roads 51 m instead of 20 m; the settlement band comes out 62% street.
7. **`budget.py`'s drum gate still measures the old flat shell**, so the ground's real cost is
   ungated.

## Session 2z — IN FLIGHT AT THE SESSION LIMIT. Read this before anything else.

The owner raised the standard to **AAA across every dimension** (see `CLAUDE.md`, "The standard"
and "The plan, in order"). A 5-agent workflow was launched to build phase A — the ability to
*see* AAA — and the session hit its time limit mid-run. Everything on disk at that moment is
committed and pushed. **Nothing was lost. Nothing here has been panel-reviewed.**

### How to resume

```
Workflow({scriptPath: "/root/.claude/projects/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/workflows/scripts/b5-aaa-foundation-wf_e8d85485-09b.js",
          resumeFromRunId: "wf_e8d85485-09b"})
```

Resume is **same-session only**. If that fails — which it will in a fresh session — do not try
to recover the run. The builders' output is already committed; what is missing is the *critique*
and *rework* rounds. Re-run those directly against what is on disk, using the four dimensions in
`docs/AAA-STANDARD.md`. The script is the template; the per-item prompts are in it.

### What landed, unreviewed

| | |
|---|---|
| `docs/AAA-STANDARD.md`, `tools/aaa_gate.py` | the scored rubric and the gate that catches **regression**, which a one-shot critic cannot see |
| `station/materials.py` + ~50 `.tres` + 4.7 MB textures | material system, exported to Godot from one Python source so the two cannot diverge |
| `tools/render_godot.sh`, `tools/export_scene.py`, `godot/scripts/render_shot.gd`, `godot/scenes/{exterior,drum}.tscn` | the engine render path, rebuilt around current geometry |
| `docs/engine-exterior.png`, `-detail`, `engine-drum-interior.png` | **the first engine frames of the drum interior** |
| `station/interior.py`, `station/tram.py` | the blocking spoke fix |

Self-tests at snapshot: **interior 141/141** (was 128), **tram 44/44** (was 36).

### The blocking defect is fixed

Tram cars were passing **6.43 m through the radial spokes** — structural, not a placement
accident: the guideways sit in the spoke planes because the spokes are the only thing that can
carry a 2,586 m truss, so moving the cars could never fix it. The spoke now has an aperture.
Both verifiers found this independently, one by point-in-box over 3,144 vertices, one by
rendering it.

### First job next session

1. **Run the critique rounds** that did not happen. Judge against `docs/AAA-STANDARD.md`; every
   dimension must reach 4. Be as harsh as the last panel was — it caught an end cap with 4,064
   open edges and two assertions that could not fail.
2. **Check `docs/REFERENCE-GAPS.md` exists.** The reference-audit agent may not have finished. If
   it did not, that document still needs writing: the owner has offered to supply more reference
   and is otherwise hands-off, so it is the only channel for asking, and a vague ask wastes it.
3. **Verify the Godot binary situation.** It is container-local and a ~61 minute rebuild, so it
   is gone with this container. Whether the agent found a way to make it survive is unknown; if
   not, that is a tax on every future session and worth solving properly.

## Session 3a — the engine renders the interior, and it is not AAA yet

Phase A's goal was **the ability to see**, and it is met. `tools/render_godot.sh` drives Godot
4.4 double-precision on Mesa lavapipe through Xvfb and produces real Forward+ frames — shadows,
real lights, materials, exposure. `docs/engine-drum-interior.png` is the first engine frame of
the habitat drum. The binary was rebuilt and is at `/home/user/godot-build/dist/` with a
`.tar.xz` beside it.

The critique round never ran (the session hit its limit), so this is my own panel pass over what
landed. It is not a substitute for the adversarial pass and that still needs doing.

### CORRECTED: the speckle is sub-pixel RELIEF, not a misapplied LOD

**My first diagnosis of this was wrong and is corrected here.** I claimed the frame drew lod0
where lod1 was due, computing "a 20 m fitting spans 2.7 px" from a framing assumption I had
guessed rather than derived. Computing it properly: the exterior orbit is 9,200 m from the aim
point, but the **nearest hull point is 5,163 m**, which is *inside* lod1's 6,000 m switch. lod0
was the correct level. The LOD was not misapplied.

The real cause is sharper, and it is a gap in the switch criterion itself:

- `lod.py` derives switch distances from **silhouette deviation** — the outline error from a
  coarser radial segment count.
- Greeble fittings stand **3–11 m proud** (INV-006). Their **relief** stops resolving at
  **3,088 m** (a 3 m fitting) to **11,323 m** (an 11 m one), against the 1.5 px budget.
- So from roughly **3 km to 6 km** the hull draws greeble relief nobody can resolve, while still
  legitimately needing lod0's outline. That is a band ~3 km wide where the mesh is guaranteed to
  produce high-frequency shading noise, and the silhouette criterion cannot see it.

The greebles were never sub-pixel in **footprint** — at 5,163 m a 20 m fitting is about 5.8 px.
They are sub-pixel in **relief**, which is a different measurement and the one that governs
whether a bump reads as form or as noise.

**The proper fix is to decouple the two schedules.** `LEVELS` steps `radial_segments` and
`greeble_detail` together, so the chain cannot express "lod0 outline, lod1 greebles" — which is
exactly what 3–6 km wants. That needs its own change and is recorded as the next visual increment.

**Done this session:** `lod.py` now computes and reports the relief-resolution distances beside
the silhouette ones, so the gap is visible in the manifest rather than latent. And
`tools/export_scene.py` gained `pick_hull_lod()` — the chain genuinely was never connected to the
renderer, so a 120 km shot would have drawn all 327,898 lod0 triangles to cover a few hundred
pixels. Selection is by distance to the **nearest** point of the hull bounds, not to the aim
point, because an 8 km station seen from 9 km has its near end at 5 km and choosing on centre
distance would decimate geometry twice as close as the number justifying it.

### Other findings from the same two frames

| | |
|---|---|
| **Scale does not read** | No aerial perspective in a 2.6 km volume. Everything is equally crisp, so the drum reads about 50 m across rather than 556. The owner named "scale" as an AAA dimension; haze is the fix and it is cheap. |
| **The ground is flat colour** | Large unbroken areas of olive-green. The heightfield's parcels, hedge banks and roads are not reading at all in the engine — worth checking whether the material is bound and whether the detail is simply below the LOD in use. |
| **Light runs blow out** | Pure white with no falloff structure; they read as blown highlight rather than as fittings. |
| **Black gap at the cap/ground junction** | Right of frame in the interior shot. Consistent with the 1.2 m axial mismatch the verifier reported between the ground rim and the cap's outermost course, which is still open. |

Honest scores against `docs/AAA-STANDARD.md`: **craft 2, fidelity 3**, performance not measured
this session, robustness good (self-tests green — interior 141/141, tram 44/44).

That is the right result for phase A. The point was never that the first engine frame would be
AAA; it was that we could finally *tell*.

### `docs/REFERENCE-GAPS.md` written — and the finding in it is worse than expected

Ranked ask for the owner, verified against the actual folders rather than assumed. The headline:

- **`reference/10-interiors-generic-kit/` is EMPTY.** The corridor kit is 210 decks and 2,330
  cells — the large majority of walkable space — and every dimension in `interior_kit.py` is
  extrapolated from proportions in a *single frame of one sector*. This is now the top ask.
- `18-audio-notes/` and `19-video-clips/` are empty; no audio work exists at all.
- `12-starfury/` has four files, **all exterior**; the cockpit was an explicit opening-brief
  requirement and has zero coverage.
- `16-signage-typography-ui/` has three files and all three are **logos** — so C-004 has nothing
  to close on.
- Grey has **one** interior frame and is **90 of the station's 210 decks**.

## Session 3b — the corridor reference landed, and the kit was modelling one space

The uploads arrived in `reference/10-interiors-generic-kit/` (8 files, of which
`central corridor.webp` and `grey level 1.webp` duplicate ones we already held). They
contradict a core assumption immediately.

**The kit modelled ONE corridor. The reference shows at least three**, and they are not
variations on a width — they are different kinds of space:

| class | frame | character |
|---|---|---|
| **residential** | `grey level 1.webp` | pale grey-tan, pilasters, horizontal banding, vertical light strips, chequered deck, portal frames. Narrow, quiet, finished. |
| **concourse** | `central corridor.webp`, `more hallway.jpg` | tall volume framed by large **elliptical ribs**, lit strip down the deck centre, downlight pools, wall screens, **upper walkway** over the lower deck |
| **service** | `more hallways.jpg` | overhead truss instead of a soffit, vertical light tubes, chequered lit strip in deck grating, warm backlit panels, litter on the deck |

Building 210 decks out of one profile would have made the whole interior read as a single endless
hallway, which is the opposite of what the footage shows.

**The elliptical rib arch is the signature of a B5 interior and the kit did not have it.**
`ring_frame_spacing_m` existed as a constant with a comment pointing at `central corridor.webp`,
and nothing ever built one. `rib_arch()` does now — see `docs/render-concourse.png`.

**Two figures are measured, not chosen:**

- An EarthForce officer stands in a circular downlight pool in `more hallway.jpg`. At 1.75 m he
  is 261 px → **149 px/m**; the pool spans 234 px → **1.57 m**. That is the only absolute length
  these frames yield directly, and `DOWNLIGHT_POOL_M` is it.
- The concourse is **two decks** tall because `central corridor.webp` shows an upper walkway with
  people on it above people on the lower deck. At INV-010's 3.6 m pitch that is **7.2 m**, and the
  self-test asserts it stays a whole multiple — a fractional height lands the walkway between decks.

The **9.0 m concourse width is the weak figure** and INV-020 says so plainly. No frame gives a
concourse width against a known length, because the officer stands mid-space rather than against
a wall. *One frame with a person against a concourse wall would close it.*

**Third winding bug of the same family.** `downlight_pool` and `deck_strip` lie flat and must face
up; ascending angle in XZ with +Y up gives a downward normal, so both were invisible from the only
place they are ever seen. Found by rendering and seeing 836 of 2,100 triangles survive culling.
The self-test now checks every flat deck element, and both new assertions were verified by
breaking them and watching them fail.

### Still to do on the new reference

`more zocalo.png`, `transport.jpg`, `garden more.jpg` and `gardens or greenery.jpg` have **not
been mined yet** — the Zocalo is the station's social centre and has no geometry at all, and
`transport.jpg` may bear on the tram car-length conflict.

## Session 3d — the Zocalo reviewed, and its bay seams welded

**Both workflows died.** Last write 01:09; the container restarted under them and nothing moved
for 5h38m. Of workflow 1's four builders, **two landed** (`zocalo.py`, `lod.py`); the
drum_ground repair and the metric hull skin did not. Of the gazetteer's six researchers, **four
landed**. **No critique round ran on anything.** All output was committed as it appeared.

So this session did the review step the loop was missing, on the largest unjudged thing:
`station/zocalo.py`, 75 KB and 90/90 self-tested, that nobody had ever looked at.

### It is good work

The module solved a **photogrammetric scale** off `more zocalo.png` rather than guessing —
horizon at 370.5 px and a seated eye height of 1.265 m solved from two 0.75 m features at two
depths, and a focal length of 2,517 px from the table-top ellipse aspect. Bay dimensions are
whole multiples of `DECK_PITCH_M`: a 21.6 m bay, a 12.6 m well against a measured 12.7 m arch
span, tiles at 0.45 m. `docs/render-zocalo.png` shows ribs arching over a two-level volume with
galleries, shopfronts, a staircase, pedestal tables and the "5" chairs.

### The defect the review found

**Every bay seam carried doubled geometry.** Non-manifold edge count by run length was 10, 162,
314, 466 for one to four bays — **+152 per seam**, all of valence exactly 4, with 106 of them
lying precisely on the seam plane. Two independent mechanisms:

1. Every longitudinal member — walls, rails, purlins, gallery slab and beams — is emitted per bay
   as a **closed solid**, so adjacent bays meet face to face and each edge around that face is
   shared by four triangles instead of two.
2. The **rail is emitted twice** at each shared boundary: 24 triangles in identical position and
   winding. A duplicate is not a touching face, so the plane test cannot see it — the rail
   straddles the seam rather than lying in it.

Both are invisible in a render and both z-fight in the engine.

**Fixed in `zocalo_run()`**: a face lying entirely in an interior seam plane is sandwiched between
two bays by definition and is dropped; then exact duplicates are removed on a winding-preserving
key, so an oppositely-wound twin (a genuine touching face) survives. The ribs also sit on seam
planes but are 0.55 m deep, so their flanks are never coplanar with one.

**Result: 10, 20, 30, 40** — exactly 10 per bay, **nothing per seam**. Boundary edges go
312 → 524 → 736 → 948, a constant +212 per bay, which is *less* than a standalone bay's 312
because each seam retires 100 open edges. The weld closes rather than opens, confirmed against a
magenta background.

Three new assertions, and **both fixes verified load-bearing** by disabling each independently:
the seam-plane weld alone leaves 162/314/466, duplicate removal alone leaves 56/102/148.

### Still open

- **10 non-manifold edges inside a single bay** — a separate, smaller mechanism, not the seams.
- The drum_ground repair and metric hull skin never ran; their specs are in the dead workflow
  script at `.../workflows/scripts/b5-zocalo-and-debt-wf_03274a8a-d9c.js` and the findings they
  were to fix are listed in session 2y.
- Gazetteer is missing `LIFE-SUPPORT-AND-INDUSTRY.md`, `MEDIA-AND-COMMS.md` and the synthesis
  pass that cross-checks every proposed location against the 210 built decks.

Suites: validate 28/28, budget 14/14, export_scene 24/24, zocalo 96/96, lod 94/94,
interior 141/141, drum_ground 69/69, tram 44/44, kit OK.

## Session 3e — drum_ground: a test that could not fail, and a slot round both ends

Two of the four review findings against `station/drum_ground.py` fixed. Its repair agent never
ran (its workflow died), so the findings were sitting in session 2y with evidence and nobody had
acted on them.

**1. The headline seam assertion could not fail.** It compared `sample(0.0, w)` against
`sample(1.0, w)`, but every consumer inside `sample()` applies `u % 1.0` first — so the two calls
are *the same call*, and the check was a value against itself. Confirmed by removing the angular
wrap from `_value_noise`: that puts a genuine **3.295 m cliff** the full 2,586 m length of the
drum at one angle, and the old metric still reported `0.000e+00` and still passed.

Replaced with a **continuity** test across the seam — `sample(1-eps, w)` against `sample(eps, w)`
— bounded at 5 cm rather than 1e-12, because two samples a real distance apart differ by however
much the terrain legitimately varies over that distance, and demanding exact equality would be
asserting the terrain is flat there. The new test catches the 3.295 m cliff, and catches a band
boundary defect the old one missed too.

**2. The ground did not reach the end caps.** It ran to the sector's z extent, but the cap's
outermost course stands `ENDCAP_STEP_M` proud, so at the floor radius the cap plate sits beyond
where the ground stopped — an annular slot **0.6 m** wide right round the drum at *both* ends.
(The review measured 1.2 m; the session-2y cap rebuild, which made checker-plating a material
group rather than 0.35 m of relief, had already halved it.)

The old assertion could not see this **because it measured only one of the two surfaces**: it
checked that the ground's *relief* faded to zero at z0/z1 and never looked at `drum_end_cap()`.
A surface can arrive perfectly flat and still stop short.

Fixed by deriving the ground's extent from `cap_plane_z()`, which reads the cap's own constants
rather than restating them — so a change to the cap's course depth moves the ground with it
instead of silently reopening the slot. Ground now spans **3837.8 … 6426.2** against the sector's
3839 … 6425, and the measured gap at the floor-radius ring is **0.0000 m** at both ends.

Both fixes verified load-bearing by reverting each: the extent revert reports "0.600 m short of
the cap plate" at both ends.

**Still open on this module** — findings 3 and 4 from the same review, both about tag widths
being bound to the LOD ramp width rather than to the real feature width:

- `sample()` tags a settlement cell "avenue" within `_step_ramp_m()/2` = 15.6 m of a block edge,
  giving a **31.2 m avenue** on 62.4 × 64.6 m blocks — point-sampled, avenue is 16.17% of the
  drum against settlement's 4.67%, so the settlement band is **62% street**.
- `_road_mask` ramps over 31.2 m beyond the 10 m half-width, so trunk roads tag **51.2 m** wide
  against a stated `TRUNK_ROAD_W_M = 20`.

The ramp is a constraint the LOD imposes on how sharply the surface may step; the *kind tag*
should follow the real feature width, with a separate verge kind for the ramp.

Suites: validate 28/28, budget 14/14, drum_ground 71/71, zocalo 96/96, interior 141/141,
lod 94/94, tram 44/44.

## Session 3f — the LOD ramp was being used as a street width

The last two `drum_ground` review findings, and they turned out to share one root cause worth
stating plainly: **`_step_ramp_m()` is not a width.** It is one stride-8 cell, 31.2 m, and it
exists to constrain how sharply the heightfield may step so the LOD chain stays honest. It was
being used as the size of a street and as the extent of a road's kind tag.

| | was | now |
|---|---|---|
| street on a 62.5 × 64.7 m block | 31.2 m → **~74% of the band was street** | 10 m → **29%**, asserted against the area its own width implies |
| trunk road tagged width | 51.2 m against a stated 20 | **4.51%** of the drum measured against **4.58%** predicted |

The geometry still ramps over the full 31.2 m, because it must. What changed is that the **kind
tag** stops at the made width: a carriageway is flat at its own width, then a verge (`VERGE_W_M`,
4 m, its own new group), then untouched band. `docs/render-drum-settlement.png` shows the result
— pale block plateaux, streets at a believable width, a verge strip along each edge and a wider
trunk road crossing. Logged as **INV-021**.

### Two measurement traps, both of which produced confident wrong numbers

1. **The block grid is 40 cells along the drum, so `w = 0.5` lands exactly on a block boundary**,
   where `d_edge` is 0 by construction — sampling there reports *every* settlement cell as
   street. The original review's "62% street" figure and my own first re-measurement both hit
   this. Measure off-lattice.
2. **A width must be a width at both ends of the fix.** My first attempt set the *verge* tag to
   one full LOD ramp; since that is half a block, it tagged every settlement cell as either
   avenue or verge and plain settlement disappeared. Caught only because the coverage numbers
   still looked wrong after the "fix".

New assertions derive the expected coverage from `AVENUE_W_M` and the block pitch rather than
comparing against a remembered number, and are verified load-bearing: reinstating the ramp-width
tag reports **76.9% against 29.0% predicted**.

`drum_ground.py`: **74/74**.

## Session 3g — a third reading of C-004, and cell counts aligned to it for free

Read the gazetteer's `LOCATIONS.md` (580 lines, 212 rows, era-locked, every authority-4 row
labelled and the blocked-egress caveat stated up front). Its §1 is the most consequential thing
the research turned up.

**C-004 may have been asking the wrong question for four sessions.** It has been framed as "which
ring is level 1". One source says the number in `Grey 17` is not a radial level at all but one of
**36 angular regions of 10° each**. That would explain C-004's standing puzzle — *no source we
hold numbers a ring* — by the simplest available route: because rings are not what the numbers
index.

**Not adopted, and C-004 stays OPEN.** Authority 4 cannot close what two authority-3 sheets could
not; the same wiki contradicts itself on the same page; and `Brown-57` breaks *both* readings
(57 > 36 regions, and > the 30 levels the same wiki gives Grey). Recorded in `CONFLICTS.md` so a
future session finds it already weighed rather than rediscovering it.

**But the option was taken, because it turned out to be free.** `ring_cells()` now snaps every
cell count **up** to a divisor of 36, so a cell always spans a whole number of 10° regions.

| | snap down | snap up |
|---|---|---|
| worst cell | **59,040** tri — 98% of the gate, structure alone | **48,128**, unchanged |
| Grey ring 2 | 59,040 | **39,360** |
| cells under their own sight line | none | none |

Down was affordable but left nothing for props, signage or NPCs. Up gives *smaller* cells, so it
is strictly cheaper. Station total: **2,330 → 2,646 cells**, 80.6 → **80.5 M triangles**. If the
angular reading is wrong, nothing has to be undone.

Cost: the cell-length-over-sight-line margin falls from a designed 1.5 to **1.12–1.68**. That is
slack rather than the guarantee; the guarantee is that a cell exceeds its own sight line, and it
is now asserted per ring. `interior.py`: **175/175** (34 new), and removing the snap fails 24.

### The gazetteer's other findings, recorded but not yet acted on

- **X-1** may *reconcile* C-002 rather than contradict it: "four cobra bay support arms" × 7 bays
  = the 28 of Contract 5. Does not close 24-vs-28.
- **X-2** a fan source puts the Alien Sector between the docking bays and Red; the authority-3
  schematic puts it aft of the drum. Authority 3 wins.
- **X-3** a fan sector ordering agrees with `other map.png` *exactly*, including Yellow as the
  non-rotating aft half — **but it is very likely an echo of the same print sources, not an
  independent witness.** C-003 stays open.
- **X-6** is a rare authority-3/4 cross-check that *holds*: medical distributed across Red, Green
  and Blue with the primary Medlab in Blue; law and security in Red.

## Session 3h — three rooms built, from the gazetteer's ranked list

Working straight down `docs/gazetteer/LOCATIONS.md` §19. #1 Zocalo was already built; this
session did **#3 the docking bay, #2 the customs signage, and #4 C&C**.

| module | what | assertions |
|---|---|---|
| `docking_bay.py` | the room the launch-and-dock requirement lands in | 18/18 |
| `signage.py` | backlit boards **and the only readable sign we hold, verbatim** | 15/15 |
| `command_control.py` | the bridge, in Observation Dome 1 | 25/25 |

### The docking bay

Width is not a free number: **42 m is the schema's own `cobra_bay` width**, authority 3 off
Contract 5 — the width that document gives *this station* for *this class of structure*. The
self-test asserts it fits: 24 bays at a 254.2 m deck radius get **66.5 m of arc** each. Deck is
at **0.913 g**. One measured length, the deck disc at 10.6 m, from an 11-worker file at 16 px/m.

**A bay is not a hangar, and the geometry says so.** The first placement mapped the width along a
*tangent* and pushed both walls 0.9 m *outside* the pressure hull. A bay is cut into a **rotating**
hull, so its deck follows an arc — corrected, it cambers **0.87 m** across 42 m.

### Signage — the project had none

`16-signage-typography-ui/` is three logos. The module is deliberately two things: board geometry,
and **the text verbatim as canon data**, because what a sign says is a fact about the station, not
a decoration, and belongs in version control rather than baked into a texture nobody can grep.

Transcribed exactly, **including the prop's own spelling** — `ARANGEMENT` with one R,
`ATMOCHEMICAL`. Asserted, because a well-meaning correction is how a transcription rots.

**Three facts these boards establish that are not signage at all:** six atmospheres available
simultaneously with more to order (a life-support number, and the mechanic behind the alien
sector); the station runs on **Earth Mean Time**, which names the clock every NPC schedule was
implicitly on; and there is a **Business Center** handling currency exchange — a sourced location.

### C&C, and a measurement error worth remembering

Dome dimensions are **read from the schema rather than restated** (46 m radius, 34 m high,
Contract 5), and the window is asserted to fit inside it.

The window measurement needed a correction I first omitted. The officer is 175 px → 100 px/m
*at his depth*; the window's fitted arc is 306 px across. Dividing directly gives **3.1 m and is
wrong** — the window is in the bulkhead *behind* him and px/m falls with distance. At ~5 m to him
and ~4 m more to the bulkhead, the scale there is 56 px/m and the window is **5.5 m**. A factor
of **1.8**, and the same trap that put the tram car length in dispute (C-008).

**Five defects the assertions caught while building C&C**, every one invisible in a render:
the glazing laid flat (XZ disc where an XY one was needed, so the glass was on the ceiling); the
uncorrected measurement; full-diameter mullions piling into a solid starburst with no glass
between them; a bulkhead with **no aperture**, so the glass was sealed inside 0.30 m of steel;
and glazing wound to face *out* through the bulkhead. The aperture assertion was itself wrong
first time — it demanded the glass stand *proud of* the wall, which fails a correctly glazed
window. Glass sits **in** an opening.

All three wired into CI. **INV-022, INV-023, INV-024** logged.

## Session 3i — the hull allowance went metric, and the prediction attached to it was wrong

`HULL_ALLOWANCE = 0.86` is gone. Every non-drum sector now takes its outermost deck floor from
an **extracted core hull less a metric `HULL_SKIN_M`**, the same 6 m the drum already used.

The fraction was the wrong kind of quantity twice over. It removed **65 m** of notional
structure in Grey and **22 m** in Yellow — pressure hull and frames do not scale with distance
from the spin axis. And it multiplied the **mean of a sector band**, which describes no surface:
Yellow's band ranges 18–440 m, Blue's 116–268 m, and neither sector has a point where the hull
is at its own mean.

**Extracting the shell.** The radius profile traces the *outline*, so it reports whatever stands
proud at each z. Session 2b's technique — a wide running minimum — is right in principle and
**erodes at a step**: it reported 428.7 m in Grey, below Grey's own narrowest real sample of
436.4 m, a radius no point in the sector has. The operator is a morphological **opening**,
erosion then dilation, which strips protrusions and restores step edges. Asserted per sector.

**The cross-check is what justifies applying it where nothing can be measured.** Run against the
band holding the habitat cylinder it returns **314.3 m**; `habitat_hull_radius()` — written four
sessions earlier, a plain mean over one *named schema feature* — gives **316.8 m**. **2.5 m
apart on a 315 m radius, from two methods that share no arithmetic.**

### The prediction was wrong, and finding that out was the point

`STATE.md` had Grey's **1.445 g** outermost deck recorded as "the visible symptom" of the
fraction, to be fixed when the allowance went metric. **It got worse: 1.693 g.** The 0.86 had
been quietly deleting 65 m of hull that is really there. Grey sits on the aft hull block — the
station's widest structure, identified in session 1, which Miller's table never names — and a
rigid body spinning at a rate fixed by the habitat floor puts 1.7 g on anything 471 m out. No
honest allowance moves it inboard.

So the premise was wrong rather than the arithmetic, and the design answer is the one a real
station would give: **you do not put quarters at the bottom of a gravity well, you put mass
there.** `HABITABLE_G_MAX = 1.25` (**347.9 m**) declares the heaviest deck a person may be
housed on. Every deck now carries a `use` tag.

| | decks | plant | outermost floor | gravity |
|---|---|---|---|---|
| **Grey** | 105 | **34** | 471.2 m | **1.693 g** |
| Red | 59 | 0 | 268.1 m | 0.963 g |
| Blue | 45 | 0 | 211.6 m | 0.760 g |
| Yellow | 33 | 0 | 155.4 m | 0.559 g |
| Green (sub-floor) | 9 | 0 | 278.3 m | 1.000 g |

**Grey's outer 123 m is the station's basement** — tankage, reservoirs, waste processing, reactor
auxiliaries. 26% of the station's interior structure, and a thing the scope asks for by name:
*"the physical plant that makes 250,000 people possible: food, water, air, power, waste."* The
fraction was concealing it behind a plausible number.

The ceiling's **lower bound is not taste**: the drum's own sub-floor stack reaches 1.117 g at the
pressure hull and is occupied, so a ceiling below that would contradict geometry already built.
That is the assertion that fails first if anyone lowers the constant. Logged as **INV-026** and
**INV-027**.

### Three defects the change exposed, none of them the thing being changed

- **`drum_sector()` was comparing a hull radius to a floor radius** — a category error, a surface
  against something 32 m inside it. On corrected shell radii that comparison picks **red**, whose
  shell sits four metres from where the Garden's ground is. Matched hull-to-hull the drum wins by
  **17×**. The old code got the right answer for the wrong reason: the drum band's mean was
  inflated by the aft hull block it happens to contain. The self-test now asserts the **margin**
  — a test that only checks who won cannot tell 17× from a coin toss, and this decides which band
  the entire habitat is built in.
- **The divisor-of-36 cell snap has a 2× gap between 18 and 36.** Grey's widened ring asks for 19
  cells, snaps up to 36, and halves the cell to 82.2 m against a **98.9 m sight line** — the
  player sees 17 m into a cell that is not resident. Snapping up now runs only as far as the
  guarantee holds, then falls back down.
- **The cell gate was pricing tankage as corridor.** It measured deck 0 of the outermost ring,
  which in Grey is plant, at the kit's 285 tri/m — **94.8% of budget**, implying habitat
  corridors had 5% of headroom for props, signage and NPCs. Split by `use`, the worst *habitat*
  cell is Grey ring 2 deck 11 at 1.246 g and **66.2%**. They have 34%.

**Station total: 210 → 251 decks, 2,646 → 3,414 cells, 80.5 M → 110.2 M triangles.** Red, Blue
and Yellow were all being cut short. `interior.py` **175 → 448 assertions**, `budget.py` 15/15,
and every new assertion was verified load-bearing by reintroducing its defect — the plain running
minimum, the floor-matched drum test, a 1.10 g ceiling, the unconditional snap-up, and the
fraction itself.

## Session 3j — phase D opens, and the assertion suites got audited

**`station/npc/` gains `body.py`, `costume.py` and `crowd.py`** — 648 assertions between them,
all green and all wired into CI, which is the only place their gates run.

| module | lines | assertions | what |
|---|---|---|---|
| `body.py` | 2,654 | **501** | fifteen species as parametric bodies, per-individual variation seeded off the npc id |
| `costume.py` | 2,715 | 80 | fabrics, decals, silhouettes, attachments, era-gated |
| `crowd.py` | 2,146 | 67 | placement and density |

Three construction paths — humanoid, encounter suit (**the Vorlon is a robe with no body in
it**, which is the point) and column. Statures span **1.53 m (Vree) to 2.05 m (Vorlon)**.

**`body.py` carries its own closure gates because nothing in the project could see this class of
defect.** The first lineup render showed limbs detached from the torso; signed volume and the
edge census both passed it, because a detached arm is still a closed solid. So it has a
ray-parity `contains()`, and the ray direction is deliberately **not** axis-aligned: the torso's
rings and the leg's root ring both put vertices at exactly z = 0, and an axis-aligned ray grazes
that shared edge and reports inside-or-outside on floating-point luck. **The only vertices it
ever rejected were the ones at z = 0 exactly.**

### Rendered and read — `docs/render-npc-lineup.png`, `render-npc-detail.png`

Against magenta. Fifteen figures, **all closed** — no background bleeds through any of them, and
26,734 of 57,412 triangles draw, which is the backface-cull ratio a solid gives. The Minbari bone
crest reads at 12 m. The Vorlon encounter suit reads.

**What the render shows that the assertions do not, and it is the first rework item for phase D:
the joints are unwelded.** Limb roots *are* inside the torso — that is asserted and passing — but
the lofts **interpenetrate rather than blend**, so a hard crease sits where a deltoid should be
and the shoulders read as a shelf the arms hang off. Craft, not closure. A gate that asks "is the
root inside" cannot ask "does the surface flow", and only looking caught it.

### The assertion suites were audited, and the result is worse than expected

`tools/mutation_sweep.py` (session 3i) perturbs every module-level numeric constant, re-runs that
module's suite in a fresh subprocess, and asks whether anything noticed. Full sweep: **192
mutants in 1,172 s**.

> **Only 41 of 192 constants — 21% — are noticed by their own module's assertions.**

| module | noticed |
|---|---|
| `signage` | **0%** |
| `council_chamber` | 4% |
| `core_tube` | 17% |
| `drum_ground` | 18% |
| `interior` | 25% |
| `command_control` | 28% |
| `zocalo` / `docking_bay` | 29% |
| `tram` | **43%** — the best in the project |

The tool is explicit that it cannot tell an unguarded constant from a deliberately loose one:
`council_chamber.SEATS` 5→6 passes **correctly**, because INV-025 asserts a lower bound on
purpose. So 21% is a floor on the real figure, not the figure. But 0% for `signage` and 4% for
`council_chamber` are not explicable that way, and those two are where the next audit increment
should go.

**Do not read this as "the suites are worthless".** They have caught a door interpenetrating a
portal frame, tram cars passing 6.43 m through a spoke, an end cap with 4,064 open edges and a
drum wound inside out. What the sweep measures is *coverage of the constants*, and it says the
assertions are strong on **relationships** and weak on **values** — which is exactly the shape
you would predict from how they were written.

## Session 3j (cont.) — animation, navigation, and a repeat defect

The six-builder NPC workflow (`wnbmuyt81`, 12 agents) completed. Two more modules landed after
the first three were committed:

| module | lines | assertions |
|---|---|---|
| `body.py` | 2,654 | 501 |
| `animation.py` | 3,022 | **467** |
| `costume.py` | 2,715 | 80 |
| `crowd.py` | 2,146 | 67 |
| `navigation.py` | 2,751 | 86 |
| `schedule.py` + `test_schedule.py` | — | 100 |
| | | **1,201 across the layer** |

All six are wired into CI. `animation.py` (~24 s) and `navigation.py` (~77 s) are now the
slowest gates in the project; they are also the two that touch station geometry, so they are the
two a schema change can silently break.

### The night watch was asleep, again

**Rotating roles declared `work_start = 0.0`, so the first watch ran 00:00–08:00 while the human
sleep block ran 23:00–06:30. The night watch spent 7.5 of its 8 hours asleep.**

That is the *exact* defect `INV-005` records as fixed in session 2m. It survived two sessions
because the assertion guarding it asked only whether `on_duty > 0`, and sampling jitter always
satisfied that. **A threshold of "more than nobody" is not a threshold** — this is the same
family as the vacuous assertions the mutation sweep exists to find, and it is the strongest
argument yet for that tool.

Fixed by anchoring sleep to the holder's own shift as an algebraic identity. **Verified from
outside the code rather than from the report:** sampled across 20,000 ids, coverage is continuous
at every hour, and station-wide on-duty security measures **138–193** against `FACTIONS.md`
§2.2's separately-stated *"roughly 150"* — a figure the module does not read.

### The Starfury cockpit is unblocked, catalogued, and the pilot stands

Owner upload `c5873e5`, four files, all opened and written up in `reference/00-INDEX.md`.
**"Sitting position" is a misnomer**: the authority-2 tub shows a ribbed couch running the full
height of the centreline with a chest yoke and a headrest recess. The pilot is braced against a
near-vertical board, arms forward onto two angled console banks.

**The resolution trap fired for the third time.** The two authority-2 production photos are
**0.23 MP**; the two authority-4 fan models are **3.05 MP** — 13× the pixels, one authority level
worse, and the best-lit material in the folder. Not quarantined (a fan model of the real prop is
legitimate corroboration and says "model" in its own filename), but they are the files that must
not be measured from.

**No absolute dimension is recorded, deliberately.** See the index entry for the failed
segmentation and why no number was published from it.

## Session 3j (cont.) — the plant kit, and four defects only a render found

`station/plant.py`, **24 assertions**, wired into CI. The 62.3 M-triangle corridor placeholder
over Grey's 34 plant decks is gone.

**The structural decision:** plant space is **not decked at `DECK_PITCH_M`**. A 3.6 m pitch is a
corridor's pitch and a tank farm wants height, so the 34 decks regroup into **7 bays of ~17.7 m**
and the *bay* is the unit built. The 4-deck remainder is kept as a shallower top bay, not dropped.

| | |
|---|---|
| whole zone | **453,528 tri** against the 62,273,664 placeholder — **0.7%** |
| tankage laid out | 1,232,508 m³, **3.1×** the 397,500 m³ reserve, **0.88%** of the zone |

**Why the reserve assertion is not circular:** tank *count* is not derived from the volume it must
hold. It falls out of a fixed farm lattice, and the test then asserts the result clears L-04's
reserve — a sparser lattice would fail. A **second assertion brackets it from the other side**
(tankage < 10% of plant volume), and that pair is what caught the first implementation, which
tiled the annulus and produced **65.1 M m³ — 164× the reserve and 46.6% of the zone**.

### Four defects, three found only by rendering it — the self-test passed 21/21 while they were live

1. **`_place()` reverses winding**, Jacobian determinant **−1**. Everything through it was
   inside-out. Found by standing on the catwalk and **seeing magenta through the floor**. Third
   instance of this family in the project. The gate now asserts on a **placed** solid, because
   the local test passes either way — which is exactly what let it ship.
2. **The pipes were 457 m in radius** — radial *position* passed as *radius*.
3. **The frame rings spanned 360°**, so every cell carried a ring round the whole station.
4. **The catwalk was a 158 × 120 m plate** spanning the full arc *and* z, with `CATWALK_W_M` used
   as a radial offset rather than a width.

**Two lessons worth more than the fixes.** A new gate checking that no piece is radially larger
than its bay **missed** the 360° ring, because it measures **vertex** radii and every vertex of a
coarse polygon sits at the same radius while its chords cut far inside — *gates that sample
vertices cannot see chords*. And `CATWALK_CLEAR_M` was 1.8 m, a crawl space giving a 1.7 m person
100 mm, guarded by `CATWALK_CLEAR_M >= 1.8` — the value itself, so it could not object.

`docs/render-plant-bay.png` is the corrected view. It reads flat grey because there is no
lighting or material yet; that is phase C, not a geometry defect.

Logged as **INV-028**.

## IN FLIGHT — read this before starting anything

**An adversarial review panel is running over the five new NPC modules and had NOT reported when
this was written.** Nobody independent has reviewed 13,300 lines of agent-written code.

- Workflow run ID **`wf_e7c370a1-f14`**, task `wreyj01ho`.
- Script: `~/.claude/projects/.../workflows/scripts/npc-layer-review-wf_e7c370a1-f14.js`
- Journal: `~/.claude/projects/.../subagents/workflows/wf_e7c370a1-f14/journal.jsonl` — **read
  this first**; it carries one `{"type":"result"}` line per completed agent with its full return
  value, and it survives a context reset when the notification does not.
- Shape: five harsh reviewers, one per module with a lens matched to it (body → mesh closure and
  LOD; costume → canon and era lock; crowd → population conservation and the `use` deck tag;
  animation → kinematics in a rotating frame; navigation → topology and reachability), each
  non-minor finding then handed to a skeptic **told to refute it**.
- **Treat the NPC modules as sound-but-unreviewed until that report is read**, exactly as session
  2x's modules were treated.

If the container is gone, the modules are committed and pushed and nothing is lost but the
review; re-run it from the script path above, or re-launch the same panel.

### Session 3j (cont.) — drum_ground had one assertion doing all the damage

The sweep said 33 of `drum_ground`'s 40 constants were unguarded. The cause was a single
assertion:

```python
check("FNV-1a is stable across processes",
      _fnv1a("drum", 7, "ground") == _fnv1a("drum", 7, "ground") and ...)
```

**The first clause is `x == x`, computed in one process.** It says nothing about stability across
processes — the property it is named for, and the property the entire determinism argument rests
on. Perturbing `_FNV_OFFSET` or `_FNV_PRIME` changed every height in the drum and none of 74
assertions noticed, because *"run it twice and compare" is satisfied by any pair of constants*.

Replaced by three checks that each test what the others cannot: the constants are the **published**
FNV-1a 64-bit values (an external fact, so a typo is caught against the standard rather than
against ourselves); the delimiter test, which was the only real clause in the original; and **an
actual cross-process run under two PYTHONHASHSEEDs**, which cannot be satisfied inside one
interpreter.

Plus a **golden digest** over a 16×16 sample of the heightfield — one assertion pinning every
terrain constant at once. Guarding ~20 constants by hand would be twenty assertions restating
twenty constants, which is how the module got here. It is *meant* to be brittle: a terrain change
should fail it, be looked at, and have `GROUND_DIGEST` updated deliberately. Same argument as the
committed `cell_manifest.json` diff gate — a silent terrain change is the failure mode.

**74 → 77 assertions**, verified load-bearing (`_FNV_PRIME` now fails two).

**And the sweep produced a false positive on its own first run, now documented in the tool.**
`FLOOR_R`, `Z0` and `Z1` came back UNGUARDED because `configure()` overwrites them from the
schema before anything reads them — the mutation is neutralised, not caught. Those three are
correctness-by-construction and "fixing" them would have undone that. **Before acting on an
UNGUARDED verdict, check whether anything assigns the name at runtime.**

### Also outstanding from this session

- **The NPC sweep IS RUNNING**, detached, writing to `docs/audits/mutation-sweep-npc.log` —
  100 constants across the five modules. The committed copy of that log may be **partial**; check
  whether the process is still alive (`pgrep -f mutation_sweep`) and re-commit the finished file.
  Read its UNGUARDED list against the false-positive note above before acting on any of it.
- The full session-3i sweep report is preserved at **`docs/audits/mutation-sweep-3i.log`**. It was
  only in `/tmp` and would have been lost.

## Session 3k — the Alien Sector, and the ranked build list is finished

`station/alien_sector.py`, **22 assertions**, in CI. **This closes the gazetteer's ranked
build list of eight.**

| # | location | status |
|---|---|---|
| 1 | Zocalo | built |
| 2 | Customs hall / arrival concourse | built, session 3j |
| 3 | Docking bay | built |
| 4 | C&C | built |
| 5 | Garden townscape | built, session 3j |
| 6 | Council Chamber | built |
| 7 | Downbelow's architecture | built as `plant.py`, session 3j |
| 8 | **Alien Sector** | **built, this session** |

**The mechanic is canon, not invented.** The customs board is authority 1 — *"SIX DIFFERENT
ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5"* — and six simultaneous atmospheres is a life-support
architecture: six independently conditioned volumes **with locks between them**. This module is
those locks. Atmosphere classes are read from `npc/schedule.py`, which deliberately carries **no
numbers** for five of the six, and an assertion checks that no class here carries a digit.

**The lock depth is derived:** a lock must hold one occupant clear of both leaves at once, and
that occupant wears an encounter suit, so depth = suit + clearance fore and aft + two reveals =
**2.75 m**. Asserted: *every quarter has two doors, because one door is not a lock.*

### Three defects, each caught by a different gate

1. **The barred screen was invisible** — placed inside the inner portal's own 0.55 m reveal, so
   the jambs occluded it entirely and the render showed an empty aperture where the frame's
   headline feature belongs. *A screen inside a jamb is not a screen.*
2. **The containment assertion then failed by 20 mm**, because its limit was a padded magic
   `0.25`. The assertion worked; the magic number meant it could not say *why*. Now derived from
   what is actually placed outboard.
3. **The bars opened onto void.** With the screen visible, the render showed magenta *through*
   it — the quarter interiors are a separate increment, so there was genuinely nothing behind the
   grille. **Real void behind a grille is indistinguishable from a defect** to the next session
   that renders it, so a closed `alien_quarter_shell` now backs every screen, asserted one per
   screen.

Renders: `docs/render-alien-sector.png`, `docs/render-alien-lock.png`. Logged as **INV-031**.

## Next session — start here

The drum's **structure** is complete: shell, both end caps, three guideway trusses with the
habitat's lighting, three spokes, a correct hollow ring model, and its own performance gate.
What follows is in rough priority order.

0. **Read the in-flight review panel's report** — see the IN FLIGHT section above. It is the only
   thing standing between 13,300 lines of agent-written NPC code and the project's own rule that
   nothing is done until it clears a harsh panel. Then **sweep the NPC modules**, which has not
   been done.

0b. **The unwelded NPC joints.** Limb roots are inside the torso (asserted, passing) but the lofts
   interpenetrate rather than blend, so a hard crease sits where a deltoid should be and the
   shoulders read as a shelf. Craft, not closure — no gate can see it and only looking caught it.
   `docs/render-npc-detail.png`.

0c. ~~**The plant kit.**~~ — **built, session 3j.** `station/plant.py`. What remains is the
   PHASE C pass on it: lighting, material and dressing. Old note kept for the numbers:
   **The plant kit.** `LIFE-SUPPORT-AND-INDUSTRY.md` §8: 62.3 M triangles — **26% of the whole
   station interior** — is currently budgeted for Grey's 34 plant decks as walkable corridor, and
   the plant zone is 559 m³ per resident, ~100× what life support needs. It is structure, tankage
   and void with a thin walkable skeleton, and that kit does not exist. Largest piece of
   misdirected content in the project.

0d. **The Starfury cockpit** — now unblocked and catalogued. Size the tub from the airframe and a
   standing 1.75 m pilot; log as an invention. See `reference/00-INDEX.md`, session 3j upload.

1. ~~**The drum's ground**~~ — **built and its four review findings all closed**
   (`drum_ground.py`, 74/74). Sessions 3e and 3f.
2. ~~**The tram**~~ — **built** (`tram.py`, 44/44). Two things remain: its "measured proportion"
   assertions are algebraic identities that never touch the built mesh, and the car length is
   disputed between two authority-1 frames — see **C-008**.
3. ~~**Streaming cells**~~ — **done, session 2w.** `ring_cells()` / `deck_cell()` emit them and
   the seam is asserted vertex-for-vertex, wrap-around included. What is *not* done: a cell
   **manifest** the engine can stream from, and cell-to-cell **junction** placement (a cell is
   currently pure corridor with no doors off it).
4. **Remaining crude components.** Cobra bays, docking ports, observation domes and rotundas
   are still box primitives. Radiators (2o), cargo modules and the forward comms plate (2t)
   are reference-corrected.
5. **Deck tile phase across junctions** — the grid is not driven from a shared origin, so there
   is a visible seam at each crossing mouth.
6. ~~**`HULL_ALLOWANCE` should become metric.**~~ — **done, session 3i.** See below; the
   prediction attached to it was wrong and the correction is the interesting part.
7. **Publish the Godot binary** as a Release asset — container-local, 61 minutes to rebuild.
8. **C-003 assignment** and **C-004 numbering.** These block *labelling*, not building — see the
   note below.

**On what C-003 and C-004 actually block.** They decide which *name* attaches to a volume, not
what shape it is. Geometry is generated against `(sector, ring_index)` and labelled afterwards
by `bind_labels()`; when the conflicts close, the mapping changes and the geometry does not.
The "Blocked" table below is kept for the record but its first two rows are **no longer true of
geometry** — only of the names on it.

## Blocked

| Item | Blocked by | Needs |
|---|---|---|
| ~~All interior level geometry~~ → **interior level *numbering*** | C-004 — **numbering convention** unresolved. The axis is settled: levels are concentric radial decks | A lift-car display, a numbered deck plan, or dialogue tying a level number to a gravity. Nothing else will do — the deck plans themselves have now been found and they number nothing |
| ~~Interior sector layout~~ → **sector *naming*** | C-003 — **Green/Brown transposition**. Sectors are longitudinal bands; the two authority-3 sheets disagree on which band is the habitat drum. `drum_sector()` identifies the drum by **geometry**, so building proceeds; only the label waits | Any source placing the Garden or Downbelow in a *named* sector at a longitudinal position |
| Deck spacing, ring radii, corridor width, ceiling height | Unavailable from any held source | The one sheet that draws decks has its vertical scale exaggerated ~2× (C-004 UPDATE item 3, same ruling as C-005) |
| Grey / Brown / Yellow interiors | Near-zero reference coverage | Grey has one frame; Brown has one misfiled frame; Yellow has none |
| ~~Starfury cockpit~~ | ~~Zero reference coverage~~ | **UNBLOCKED and catalogued, session 3j.** Four references in `reference/12-starfury/`, all four opened and written up in `reference/00-INDEX.md`. **The pilot stands** — braced against a near-vertical ribbed couch with a chest yoke, not seated. Tub is an elongated hexagon widest 35–40% down, green throughout, two angled console banks. **No absolute dimension is available**: the two authority-2 photos contain no human and no scale bar, and the two files that do contain a figure are authority 4 fan models at toy scale. Size the tub from the airframe and a standing 1.75 m pilot, and log it as an invention |

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
5. ~~**Starfury cockpit interior**~~ — **closed, session 3j.** Four files uploaded by the owner; see the Blocked table. Uncatalogued.
6. **Grey Sector** — one file, and it is the most useful interior frame in the set.

## Uncatalogued reference, and misfiled reference

`reference/00-INDEX.md` ends with two lists a future session should read before re-deriving
them: **Still uncatalogued** (~25 files, mostly single-character portraits and race-makeup
shots) and **Misfiled — recommended moves** (nine files whose folder is wrong, deliberately
*not* moved because the schema and specs cite some by path).
