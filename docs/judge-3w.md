# AAA judgement of the WALKABLE station — session 3w

**Subject:** one assembled ring deck, `blue/0/0`, built by
`python3 station/deck.py --sector blue --ring 0 --deck 0`. 344° of corridor at radius
211.55 m, six rooms with pressure doors, vestibules, 97,590 triangles of furniture,
13 people. **597,418 render triangles, 9,588 collision triangles, 188 mesh groups.**

**Path:** Godot 4.4 double + Mesa lavapipe, Forward+, 1280×720, `godot/scenes/interior.tscn`,
15 frames, 9–21 s each. Every craft claim below cites a frame that was rendered and read.
Nothing under `station/` or `godot/` was edited to produce them.

**Revision judged:** `bc41bf7`, plus uncommitted work in `station/deck.py::_sweep` and
`station/walkable.py::walk_deck` that another session was writing concurrently. That work
adds the habitat drum to the sweep and routes `--deck green/1/0` to `drum_walk`; it does not
touch `build_deck`, the corridor, materials, lights, doors or CI, so nothing below is stale
because of it. The drum is out of scope here either way — it is not a ring deck.

| dimension | score | one-line reason |
|---|---|---|
| **CRAFT** | **1** | the corridor — 77% of the deck — arrives in the engine as one untextured group with zero light sources, and every person on the station renders as a pure-black silhouette |
| **FIDELITY** | **1** | the whole walkable station is one 2.6 m corridor class where the kit's own taxonomy says the show has three; the section itself is a declared single-source inference the one corridor reference contradicts; one signage group of 24 triangles on the entire deck |
| **PERFORMANCE** | **1** | a gate exists, prints PASS at 30,941/60,000 visible triangles, and does not measure what ships: 82,478 triangles in the standing frustum, 597,418 resident, 188 draw calls, none of it gated |
| **ROBUSTNESS** | **1** | 1,470 open boundary edges, 245 at every one of the six doorways, and nothing measures closure on an assembled deck; `deck.py`, `collision.py`, `dressing.py` and `populace.py` are not in CI at all |

None of the four reaches the bar. The subsystem is **not done** and the failures are
mostly not where the last two sessions thought they were.

Scored separately in `docs/aaa-scorecard.json` as `npc_bodies`, because bodies-in-a-room is a
different subsystem from `npc_foundation`'s names, schedules and statistics:
**craft 1, fidelity 2, performance 0, robustness 2.**

---

## THE HEADLINE, and it is the cheapest fix in the project

**The walkable build throws away the material and lighting information it already has.**

`station/deck.py:484` writes

```python
G.append(("corridor", 0, len(ct)))
```

— all 458,400 corridor triangles as **one anonymous group**. But `interior_kit` records
per-material spans as it builds, and `interior.ring_arc` still has them at the moment it
returns; it simply does not return them. Recovered with `interior_kit.tagged_spans()`, the
same mesh carries **14 named material spans**: `deck_grid`, `wall_panel`, `light_pilaster_strip`,
`light_downlight`, `light_portal_head`, `skirt`, `dado`, `rail_band`, `portal_frame`, `pilaster`,
`soffit`, `ceiling_slab`, `wall_reveal`, `wall_assembly`.

Two consequences, both measured:

1. **No material.** `interior.tscn` has 429 material rules, matched by substring. `corridor`
   matches none of them and `interior.tscn` declares no `fallback_material`, so the engine
   leaves the glTF default on 458,400 triangles. The engine says so on every run:
   `render_shot: fallback material used by 15 group(s): corridor, doorleaf_…` — the corridor
   **and all twelve door leaves**.
2. **No light.** `export_scene.FIXTURE_LIGHTING` is an **exact-name** table. The corridor's
   822 `light_downlight` fittings are inside the anonymous blob, and every room group is
   renamed `<key>__light_highbay` by `deck.py`, which no longer matches. Measured:

   | group naming | light sources placed on the deck |
   |---|---|
   | **as shipped** | **0** |
   | room prefix stripped | 28 |
   | corridor spans also restored | **850** |

Same geometry, same camera, same exposure, two renders:

| | frame | median | p5 | p95 | clipped | crushed |
|---|---|---|---|---|---|---|
| **as shipped** | `docs/judge3w-corridor-20m.png` | 0.3074 | 0.2359 | 0.3394 | 0.00% | 0.01% |
| groups recovered | `docs/judge3w-corridor-20m-materials.png` | 0.0903 | 0.0273 | 0.4758 | 2.49% | 3.20% |

**99.5% of the pixels change** (mean |Δ| 75/255). Against the show's own corridor,
`reference/07-sector-grey/grey level 1.webp`, measured by `tools/measure_frame.py --against`:

| | level | p5 | p5/p95 | crushed | verdict |
|---|---|---|---|---|---|
| **as shipped** | **×5.77** (target ×1.40 ±25%) | ×12.58, band ×1.29 | ×8.38, band ×3.38 | ×0.02 and outside the show's range | **fails the level test and 4 of 6 distribution tests** |
| groups recovered | ×1.68 — passes | ×1.41, band ×1.29 — fails | ×0.68 — passes | ×3.69 — passes | passes 5 of 6 |

The shipped corridor's p5/p95 is **0.695**: the entire frame lives in a 0.24–0.34 band.
It is a flat grey tube. The show's is 0.083.

**And the playable build is worse than that frame.** `godot/scripts/walk.gd` — the scene a
player actually stands in — loads the `.glb` through `GLTFDocument` and applies **no material
rules at all** (`_load_level()`), and its `WorldEnvironment` has **no lights**, only
`ambient_light_energy = 0.6` (lines 182–190). The frames above at least bind the room
materials through `interior.tscn`. What a player walks in has neither.

---

## Subject 1 — the corridor, from standing eye height (1.7 m)

Rendered at the three distances. Note first that **an interior corridor has no 200 m
"normal distance"**: the walls are 1.08 m from a walking player's shoulder, so the rubric's
half-distance test is where a player *lives*, not an edge case.

| distance | frame |
|---|---|
| normal — 20 m down the arc | `docs/judge3w-corridor-20m.png` (shipped) / `-materials.png` (recovered) |
| half — 10 m | `docs/judge3w-corridor-10m.png` |
| arm's length — wall at 1.12 m | `docs/judge3w-corridor-wall-1m.png` |
| sight line — 90 m | `docs/judge3w-corridor-sightline.png` |

**What is genuinely good, and it is not nothing.** With the groups recovered, this is the
best interior frame in the project. Warm `light_downlight` against cool `light_pilaster_strip`
is the single most Babylon-5 thing here and it is a *measured* relationship, not a choice.
The deck plate, skirt, dado, rail band, mullioned panels, cornice and serviced soffit all
read; the layer-2b articulation work from session 3s is real and it shows.

**At 1.12 m it falls apart, which is the C3 descriptor verbatim** (`judge3w-corridor-wall-1m.png`):

* the wall panels are **completely blank** — no bolt, no seam, no vent, no wear, no grime,
  no fixing. One flat value across a 2 m × 2 m field.
* the joints between panels are **pure black lines**, not recesses with light in them.
* the downlight is **a glowing white box**. No lens, no bezel, no housing, no reflector.
* 4.01% of that frame is crushed and there is nothing in the mid-tones to look at.

**Repetition is indexable at every distance.** The corridor is **138 identical kit sections
over 1,270 m**, subdivided into 3.07 m bays — roughly **414 identical bays**, and nothing
varies between any two of them. AAA-STANDARD C5 requires "nothing in frame repeats in a way
the eye can index"; `judge3w-corridor-sightline.png` is ten identical ceiling battens in a row.
The frame is also perfectly mirror-symmetric about the centreline, which C5 also names.

**The far end gets brighter, not darker.** In both the 10 m and 90 m frames the vanishing
point is a white bloom blob from accumulated ceiling battens. A corridor should recede into
dark. 2.5% of those frames is clipped.

**`light_pilaster_strip` aliases badly.** In `judge3w-corridor-10m.png` and
`-sightline.png` the vertical strips read as chunky notched blocks with ⌐ and L shaped
corners — a repeating emissive pattern sampled at a grazing angle with no filtering. It
reads as a corrupted texture rather than as a light.

**One corridor class for the whole station.** `interior.ring_arc` calls
`kit.corridor_section(seg_len)` with no `p=`, so every section is the default `PROVISIONAL`
**2.6 m wide, 3.0 m high** residential passage. `interior_kit.CORRIDOR_CLASSES` defines
`concourse` at **9.0 m** and `service` at **4.2 m**, sourced in INV-840 to `central corridor.webp`
and `more hallway.jpg` — and **nothing on the walkable station ever asks for either**.
All 66 assembled decks are the narrow one. Side by side with `grey level 1.webp` the show's
corridor is visibly wider and lower with an open cross-corridor; ours is a service passage.

---

## Subject 2 — a doorway, close up

| distance | frame |
|---|---|
| normal — 5 m | `docs/judge3w-door-5m.png` |
| half — 2.5 m | `docs/judge3w-door-2m5.png`, `docs/judge3w-door-2m5-shipped.png` |
| arm's length — 1.0 m | `docs/judge3w-door-1m.png` |

The door is **the only thing on this station a player can use.** At 5 m it does not read
as a door — a pale slab in the wall with a thin seam. At 1 m it is a **blank chamfered
panel**: no handle, no control plate, no emergency release, no hazard chevrons, no room
name, no bay number, no gasket, no rebate. `doorleaf_*` matches no material rule, so both
leaves take the glTF default.

**At 2.5 m the assembly is visibly broken** (`judge3w-door-2m5-shipped.png`, magnified):
the dark jamb pieces are the *neighbouring room's* wall panelling standing proud through the
corridor's white wall; their top and bottom edges are ragged sawtooths; a detached
parallelogram floats in front of the wall at lower left and a second slab hangs free below
the right jamb; and there is a black wedge above the door head.

That is not an impression — it is measured. Over the whole assembled deck:

```
welded verts 302,160   edges 742,095   BOUNDARY (1 face) 1,572
  1,470 of them in `corridor`, and EVERY ONE is at a doorway:
     docking_bays  (  0.000 deg): 245 open edges within 2 m
     lowg_bays     (129.728 deg): 245
     mooring_clamps(180.301 deg): 245
     plantroom_bay (260.069 deg): 245
     bay_elevators (300.000 deg): 245
     vorlon_berth  (320.000 deg): 245
  remainder at the two arc ends: 0    (the arc ends are correctly capped)
```

**Every door aperture on the walkable station is an unclosed cut, 245 open edges each.**
The two arc ends — which *are* legitimate openings — are closed. Nothing measures this:
`interior_kit`'s closure gate runs on one straight section, `deck.py --selftest` never
asks, and `deck.py --sweep` counts floor holes rather than edges.

What is **not** wrong, checked because it looked wrong: the leaves do not interpenetrate
anything. A point-in-volume test over the closed-leaf box at all six doors returns **0**
corridor triangles inside. The 3v fix held.

A further 96 open edges are in the furniture — `dress_conduit` and `dress_band` are
open-ended prisms in four of the six rooms.

---

## Subject 3 — a furnished room interior (`docking_bays`)

| distance | frame |
|---|---|
| normal — 6 m across the bay | `docs/judge3w-room-6m.png`, `-shipped.png` |
| half — 3 m | `docs/judge3w-room-3m.png` |
| fittings only, ambient 0.05 | `docs/judge3w-room-6m-fittings-only.png` |

**The room does not light itself.** This is the sharpest lighting finding of the session.
`interior.tscn`'s own header argues that "a room with no tagged fitting renders BLACK, and
that is the correct answer… a room that lights itself from nowhere is what this arrangement
exists to prevent." The docking bay has fittings — four `light_highbay` spots and four
`light_deck_channel` runs — and:

* turning the scene ambient down to 0.05 renders the room **essentially black**
  (`judge3w-room-6m-fittings-only.png`); the only bright things left are emissive prop faces.
* adding those fittings to a deck that had **zero** lights changes **5.9% of the frame by a
  mean of 0.6/255** (`judge3w-room-6m-shipped.png` vs `judge3w-room-6m.png`).

So the room's visible level is essentially all flat ambient fill. That is why the 3 m frame
has no shadow under the standing figure, no falloff, no direction and no form from shading.

**It is a docking bay with no docking in it.** The far wall is a flat grid of blank
rectangles with faint noise-texture smudges. No bay door, no ship, no gantry, no umbilical,
no clamp, no hazard striping, no bay number. This is the `generated_rooms` C1 finding from
session 3r — "the room is named for a function it does not contain" — still true, now with
furniture in front of it.

**Prop density is high and prop collision is coarse**, and both matter:

| room | separate solid primitives | per m² | merged collision boxes | largest box |
|---|---|---|---|---|
| `docking_bays` | 2,189 | 24.4 | **15** | 7.41 m |
| `lowg_bays` | 2,184 | 28.2 | 21 | 6.86 m |
| `plantroom_bay` | 2,198 | 20.4 | 20 | 9.31 m |
| `bay_elevators` | 1,363 | 33.2 | 12 | 5.36 m |
| `mooring_clamps` | 120 | 2.4 | 22 | 2.90 m |
| `vorlon_berth` | 121 | 1.9 | 24 | 6.00 m |
| **deck** | **8,175** | **19.1** | **114** | — |

`collision.prop_boxes` merges any two boxes within 40 mm, repeatedly, so a rack and its
contents become one slab. In `docking_bays` that is 209 m³ of collision box in a 655 m³
room — **32% of the room's volume is solid to the player** and 26,268 triangles of furniture
are represented by 15 axis-aligned boxes up to 7.4 m across. AAA-STANDARD's interaction
checklist requires that "collision geometry matches render geometry within a **stated**
tolerance, and the tolerance is asserted". No tolerance is stated or asserted anywhere.
A player will collide with air next to a crate and walk through the gap between two.

**The people are not solid at all** — `rooms.is_solid` excludes `npc_` deliberately and for
a good reason (they would be permanent statues in static collision), so today a player walks
through all 13 of them.

---

## Subject 4 — a person at conversational range

| distance | frame |
|---|---|
| conversational — 2.04 m | `docs/judge3w-person-2m.png` |
| half — 1.07 m | `docs/judge3w-person-1m.png` |
| across the room — 6 m | `docs/judge3w-room-6m.png` |

**Every inhabitant of Babylon 5 renders as a featureless pure-black silhouette.** No face,
no hands, no skin, no eyes, no fabric, no colour, at any distance. `judge3w-person-2m.png`
is **43.59% crushed** — nearly half the frame at conversational range is below the
measurable floor. `judge3w-room-6m.png` is 10.58%.

**The cause is exact and is one line.** `godot/scenes/interior.tscn` binds both
`npc_standing` and `npc_seated` to `m_plant_valve_metal`, which is

```
albedo 0.545  metallic 0.95  roughness 0.42     ("Valve — bare metal handwheel and stem")
```

At metallic 0.95 the diffuse response is scaled to ~5%, so almost all of a person's light
has to come back as specular — and the same scene sets `reflected_light_source = 1`, which
is `REFLECTION_SOURCE_DISABLED`. There is no environment for a metal to reflect. A
95%-metallic material in a scene with reflections disabled is black by construction, and
every human, Drazi and Vree on the station is wearing it.

**The bodies underneath are better than that.** At 1 m the outline shows a head, shoulders,
a coat, separate legs and arms; the Vree is a distinct non-human stack. `station/npc/body.py`
has real closure gates. None of it is visible.

**"One pixel of silhouette" is unreachable indoors, and saying so is part of the answer.**
At 55° vertical FOV and 720 px, one pixel subtends 0.076°, so a 1.8 m person is one pixel
of silhouette at **1,350 m**. The longest sight line in this build is the corridor's ~91 m,
where a person would be ~13 px — and there are **no people in the corridor at all**. All 13
actors on the deck are inside rooms behind closed doors. A player can walk the full 1,270 m
of ring and never see anybody.

---

## PERFORMANCE — the gate exists and measures the wrong thing

`station/budget.py` reports **15/15 within budget**, including

```
PASS  visible structure set   30,941 tri / 60,000 tri (51.6%)  99 m sight line + 2 crossings
PASS  interior share of frame      3% / 5%    structure only -- props, NPCs and
                                              signage come out of the rest
```

Measured on what actually ships, from the standing camera of `judge3w-corridor-20m.png`
(55° FOV, 16:9, near 0.06, far 400, a triangle counted if any vertex is in the frustum):

| quantity | shipped `blue/0/0` | gate |
|---|---|---|
| triangles in the standing frustum | **82,478** | 60,000 "visible structure" — **137%** |
| triangles resident in one deck | **597,418** | not gated |
| mesh groups = draw calls | **188** | no interior draw-call budget exists (`exterior_draw_calls: 64` is the only one) |
| collision triangles | 9,588 (1.6%) | not gated |
| whole walkable station, collision | 75,642 (`--sweep`) | not gated |

"props, NPCs and signage come out of the rest" names a budget that does not exist. The deck
carries **97,590 triangles of furniture and 28,636 of people** in six rooms and nothing
measures either. There is no LOD and no streaming in the walkable build: `walk.gd` loads
one `.glb` whole and gives the collision proxy trimesh shapes at startup.

This is the P1 descriptor exactly — "a gate exists and does not measure the thing it names.
Worse than 0, because it prints PASS."

---

## ROBUSTNESS — the good part first

**The walk gate is real and it passes.** Independently re-run this session:

```
PASS  deck blue/0/0  6 rooms over 344 deg, 6 doors; a body spawns in the corridor and
      WALKS INTO docking_bays (6.3 m -> 0.04 m), never leaving the floor
      control: with the doors inert the body is stopped 5.26 m short.
```

The negative control is the single best piece of engineering in this subsystem: it fails if
both configurations pass, so a door-shaped hole cannot masquerade as a door. `deck.py --sweep`
re-run: **66 of 67 decks assemble, 0 fail, 1 deferred, 87 locations with a door, 0 floor
holes.** Generation is **byte-identical across `PYTHONHASHSEED` 0, 1, 7, 12345 and 99999**.

**And then it is undone by two things.**

**1. Nothing measures closure on an assembled deck.** 1,470 open boundary edges, 245 at
every door, is the R1 descriptor — "the self-test asserts real properties and the geometry
is not closed". `deck.py --selftest` checks that rooms are in different places, that
everything is near the deck radius, that up is inward, and that the spawn is on the floor.
It never counts an edge. `--sweep` counts *floor holes* by ray cast, which is a different
question and cannot see a hole in a wall or a soffit.

**2. Four of the five modules that make the station walkable are not in CI.**
`.github/workflows/validate.yml` contains no reference to `deck.py`, `collision.py`,
`dressing.py` or `populace.py`. Its walk step is

```yaml
- name: The station is walkable
  run: python3 station/walkable.py --rooms 6
```

— six isolated rooms. **`--deck` never runs in CI**, so the door negative control, the
distance-covered assertion and the whole-deck assembly are all unguarded. `CLAUDE.md` states
as a binding rule: *"`station/walkable.py` asserts the player can spawn, stand, walk, and
reach the neighbouring location. **It runs in CI.**"* That sentence is not true of the mode
that makes the claim. A gate that does not run is a gate that cannot fail — the one defect
this repository has written down more times than any other.

---

## FIDELITY

**What traces.** The corridor section, door width and height, deck pitch and course heights
are in `interior_kit.PROVISIONAL` rather than inline, and INV-007 states plainly which of
its numbers is weak. Species mix, names and the identicard schema are sourced. This is real
work and it is why the score is 1 rather than 0.

**What is wrong about the object.**

* **The section is a declared inference the one relevant reference contradicts.** INV-007's
  own words: *"Carrying the chamfer from the aperture to the corridor's own section is an
  inference, not an observation"*, and *"the one frame that does show a corridor's head —
  `grey level 1.webp` — shows a **rectangular** portal header."* Single source, no
  cross-check, and the cross-check that exists disagrees. That is F1 verbatim.
* **One corridor class on 66 of 66 decks**, where the kit's own INV-840 taxonomy — derived
  from `central corridor.webp` and `more hallway.jpg` — says the show has at least three,
  and the concourse is 3.5× wider than what ships.
* **Signage: one group, 24 triangles, on the entire deck** (`docking_bays__prop_deck_marking`).
  `grey level 1.webp` at matched framing carries a wall placard, a lit sign panel with
  lettering, and painted floor markings, all within 10 m of the camera. `station/signage.py`
  exists and runs in CI and puts nothing on the walkable station. `CLAUDE.md`'s scope names
  "an information layer the player can use — comms, ISN, propaganda, **signage**, announcements"
  as part of what "the whole station" means.
* **Palette.** The show's corridor is warm sand/olive with cool blue-white strips and amber
  wall lamps over a patterned tile floor with an inlaid path. Ours is neutral grey-white over
  dark plate. The warm/cool *relationship* is right and measured; the ground colour is not.

**And six constants introduced by the walkable layer are unlogged.** `canon/INVENTIONS.md`
stops at INV-081 (session 3u). Nothing covers `deck.ARC_PAD_DEG = 12.0`, `deck.Z_CLUSTER_M
= 40.0`, `deck_index`'s name-or-rank rule, the corridor's arc-phase sweep, `corridor_z_m`,
the vestibule's existence and depth, or `prop_boxes`' `min_m = 0.18` / `gap = 0.04`. Each
carries a reasoned inline docstring — which is why I have not scored FIDELITY 0 — but
CLAUDE.md's first hard rule and the F0 descriptor both ask for an `INVENTIONS.md` entry,
and a reader six sessions from now will not be able to tell these from memory.

---

## The defects, ranked by what they cost

1. **BLOCKING · CRAFT · `station/deck.py:484` + `interior.ring_arc`.** The corridor's 14
   material spans are recorded during the build and discarded on return, so 458,400 triangles
   — 77% of the deck — reach the engine with no material and no light. **0 light sources on
   the whole deck; 850 available from the geometry's own tags.** 99.5% of the corridor frame
   changes when they are restored, and the frame goes from failing the project's own layer-4
   level test at ×5.77 to passing at ×1.68. *Fix:* return `interior_kit.tagged_spans(tris)`
   from `ring_arc` and let `build_deck` use them instead of the hardcoded `("corridor", 0, n)`.
   Nothing else in this list is close to this ratio of payoff to change.

2. **BLOCKING · CRAFT · `godot/scenes/interior.tscn`, rules `npc_standing` / `npc_seated`.**
   Both bind to `plant_valve_metal` (metallic 0.95) in a scene with
   `reflected_light_source = 1` (reflections disabled). Every person on the station is a
   pure-black silhouette; the conversational-range frame is 43.6% crushed. *Fix:* a
   non-metallic skin/costume material, or `station/npc/costume.py`'s own groups bound
   separately. One material, and the station gets inhabitants.

3. **BLOCKING · ROBUSTNESS · CI.** `deck.py`, `collision.py`, `dressing.py` and `populace.py`
   do not run in CI, and `walkable.py` runs only `--rooms 6`. The deck gate — the one with
   the door negative control, the one CLAUDE.md says runs in CI — is unguarded. Every
   walkability claim in `STATE.md` rests on a gate that no push executes.

4. **BLOCKING · ROBUSTNESS · the doorways.** 1,470 open boundary edges, 245 at each of six
   doors, zero at the arc ends, and no assertion anywhere counts them. Visible at 2.5 m as
   torn jambs, floating fragments and a void over the head. *Fix:* a `boundary_edges()`
   census in `deck.py --selftest` with the arc ends as the only declared openings — it will
   fail immediately, which is the point.

5. **MAJOR · CRAFT · lighting, `walk.gd` and the rooms.** The playable scene has no lights
   and no materials at all. The rooms that do have fittings are not lit by them: adding all
   of `docking_bays`' fittings moves 5.9% of the frame by 0.6/255, and with ambient at 0.05
   the room is black. Flat ambient is doing the work, which is why no frame in a room has a
   shadow, a falloff or a direction.

6. **MAJOR · PERFORMANCE · nothing gates the deck.** 82,478 triangles in the standing
   frustum against a 60,000 allowance the gate reports as 51.6% used; 597,418 resident; 188
   draw calls with no interior draw-call budget in existence; 126,226 triangles of props and
   people entirely ungated. Add a `deck` section to `budget.py` measuring a real assembled
   deck rather than the kit in isolation.

7. **MAJOR · FIDELITY · one corridor class, no signage.** 66 of 66 decks are the 2.6 m
   residential passage; `concourse` (9.0 m) and `service` (4.2 m) exist in the kit and are
   never requested. One 24-triangle signage group on the whole deck against a reference
   frame carrying three legible signs within 10 m.

8. **MAJOR · CRAFT · repetition and symmetry.** 138 identical kit sections / ~414 identical
   bays over 1,270 m, mirror-symmetric about the centreline, one door per 210 m of walking.
   C5 forbids exactly this; C3 is the ceiling until it varies.

9. **MAJOR · CRAFT · blown fittings and an aliased strip.** 2.5% of the corridor frames is
   clipped; ceiling battens and pilaster strips read as pure white shapes with no housing,
   and the strips' emissive pattern aliases into notched blocks at grazing angles. The
   sight line gets *brighter* with distance because of accumulated bloom.

10. **MAJOR · ROBUSTNESS · prop collision has no stated tolerance.** 26,268 triangles of
    furniture in `docking_bays` become 15 AABBs up to 7.41 m across, 32% of the room's
    volume. The 40 mm merge is unbounded and unasserted.

11. **MINOR · FIDELITY · six unlogged constants** in the walkable layer; `INVENTIONS.md`
    stops at INV-081.

12. **MINOR · ROBUSTNESS · `docs/aaa-scorecard.json` does not pass its own gate.**
    `python3 tools/aaa_gate.py docs/aaa-scorecard.json` reports **52 structural errors,
    every one of them in a round written before this session** — `severity: "resolved"` is
    not a valid severity, evidence keyed by `frames`/`path`/`shader` instead of by
    dimension, `what_is_good` is not a key the schema knows, and several dimensions sit
    below the bar with no finding explaining them. The two rounds added here are
    gate-clean. The rest are left as found: editing past rounds to make a gate green is
    precisely the failure this file exists to catch.

---

## What I could not judge, and why

* **Framerate, stutter, shader cost.** No GPU, no target hardware. Unchanged from
  AAA-STANDARD's own list.
* **Whether the door *animation* reads.** `door.gd` opens on proximity in the walk scene;
  `render_shot.gd` does not run it, so every door in every frame here is closed. A moving
  door is video, and there is none.
* **Whether the black wedge over the door head is a hole or an unlit surface.** The proper
  test is a two-background diff, which needs a scene file I do not own. The geometry
  measurement supersedes it anyway: 245 open edges per door says the aperture is not closed
  regardless of what any one camera shows.
* **The drum.** `green/1` is deferred by name in `deck.NOT_RING_DECKS` and is not a ring
  deck; nothing here judges it.
* **31 of 118 locations.** The sweep puts 87 on an assembled cluster. The rest are in
  secondary z-clusters and cannot currently be walked to.
