# Craft review — session 3t panel

**Reviewer:** independent panel agent, worktree `agent-a24be412db94db019`, branch tip `c2c9c3e`.
**Method:** 18 engine frames through `tools/render_godot.sh` (Godot 4.4 double + lavapipe), every
subject at the rubric's **three distances**; `tools/measure_frame.py` distribution comparisons
against authority-1 references; `station/density.py`, `station/budget.py`, `station/directory.py`
and 25 module self-tests re-run from a clean checkout.

**This review may not fix anything. It is a judgement.**

Every frame below is reproducible with the command given. Frames live in
`$SCRATCH/frames/` for this session; the commands are the durable citation.

---

## 0. Headline

`station/directory.py` prints layers 1, 2, 3 and 4 **COMPLETE at 118/118**. That number is not
wrong about what it measures. It is wrong about what it is being read to mean, and it is wrong in
**exactly the way session 3r's post-mortem said the next criterion must not be**:

> *"A layer's exit criterion must be able to fail on the current content. If it cannot, it is
> measuring the wrong thing."* — CLAUDE.md

`station/density.py`'s floor **can** fail — a plain box scores λ 0.235 against the brig's 5.045.
But **a box with wallpaper passes.** Measured, not asserted:

```
brig floor (density.py --modules)                     λ = 5.045
featureless 13×3×13 m box + 0.4 m relief grid         λ = 6.531   → 129% of bar → PASS
the actual brig                                        λ = 5.186   → 102.8% of bar → PASS
plain box, no relief                                   λ = 0.235   → FAIL
```
*(`python3 -c` against `density._relief_box` / `density._box_mesh` / `density.score`, this session.)*

A rectangular room with a uniform grid of shallow raised panels — no door, no bunk, no cell, no
fixture, nothing that makes it a brig — clears the 2b gate by 29%. That is the same shape of hole
as "a cube passes every word of it", one level up: **2a could not distinguish a cube from a room;
2b cannot distinguish a wallpapered cube from a room.**

The frames agree with the arithmetic. See §2.

---

## 1. Scores

Scored per AAA-STANDARD's rule: *"Score to the lowest descriptor that is fully true."* The station
is scored as one artefact; the per-subsystem table below is where the unevenness lives, and the
unevenness is the important part.

| Dimension | Score | Descriptor it drops to |
|---|---|---|
| **CRAFT** | **1** | C1 — *"reads as a placeholder from any distance. A box primitive standing in for a named object."* True of the 68 procedural rooms (58% of the station) and of the drum ground (4.49 million m², the largest surface a player stands on). |
| **FIDELITY** | **3** | F3 — every dimension traces to a named file with a stated calibration; every extrapolation has all four `INVENTIONS.md` fields. Held at 3 because F4's cross-check does not exist for the bulk (the brig archetype has *no measured reference frame at all*, `materials.py:1141`) and because F5's *appearance* comparison has been done for **level only**, never for content or palette. |
| **PERFORMANCE** | **1** | P1 — *"a gate exists and does not measure the thing it names. Worse than 0, because it prints PASS."* `budget.py`'s drum gate measures a mesh the exporter throws away. |
| **ROBUSTNESS** | **3** | R3 — assertions cover classes of error, determinism verified across two `PYTHONHASHSEED`s in two processes. Held below R4 because *"interfaces between subsystems are asserted rather than assumed"* is false: `density.py` and `export_scene.py` disagree about what the drum is, by 14% of line density, and nothing checks. |

### Per subsystem, so the unevenness is visible

| Subsystem | Craft | Frame that decides it |
|---|---|---|
| corridor kit | 3 | `--shot interior --room corridor` — genuinely good; warm/cool contrast, deck grating, pilasters |
| `zocalo` | 3 | `--shot interior --room zocalo` — reads at 30 m, falls apart at 15 m, is a failure at 5 m |
| hull exterior | 3 | `--orbit 3200,15,208` — real size hierarchy, conduit runs; flat decal fittings, no cast shadows |
| `components` (arrays, radiators) | 2 | `--orbit 3200,15,208` — featureless flat plates, 800 m across, zero surface |
| `garden` townscape | 2 | `--shot drum --eye " -92.66,244.76,4928.0"` — boxes with a painted window band |
| `garden` tree | 1 | `--shot drum --eye " -72.2,251.9,4838.0"` — a black stick and six flat green discs |
| `rooms` (68 places, 58%) | 1 | `--shot interior --room casino` — a beige box with a mullion grid |
| drum ground | 1 | `--shot drum --stand 20,4700 --look 20,6300` — two flat polygons with a hard straight edge |

---

## 2. Ranked findings

### F-01 · BLOCKING · P1 / R4 — the drum's layer-2 pass is measured on a mesh that never renders

`station/density.py:_m_interior` measures `interior.drum_interior(...)`.
`tools/export_scene.py:drum_parts` (line 982) **replaces that shell with `drum_ground.visible_set()`**
— its own comment says so. Measured this session:

```
density.py measures      : tris 116,120   area 6,141,373 m²   λ = 0.1320   floor 0.128 → 103.4% PASS
what actually renders    : tris 116,120   area 5,760,100 m²   λ = 0.1105   floor 0.128 →  86.3% FAIL
  ground alone (renders) : tris  88,736   area 4,492,518 m²   λ = 0.0389            →  30.4% of floor
```

Five gazetteer rows — *The Garden (the drum interior)*, *The drum end caps*, *The three radial
spokes*, *Radial transport tubes*, *The sub-floor deck stack* — are certified layer 2b COMPLETE on
geometry that is discarded at export. STATE.md §"Session 3s (earlier)" **documents the
substitution, calls it "one caveat", quantifies it at 0.09% of the calibrated frame, and flips the
layer to COMPLETE anyway.**

This is AAA-STANDARD's `blocking` definition verbatim: *"a `PASS` on an unmeasured quantity"*.

### F-02 · BLOCKING · P1 — `budget.py`'s drum gate still measures the old shell, and now under-counts the scene by 31%

`station/budget.py:287`:

```python
check("ground surface density", shell / area, DRUM["surface_tris_per_m2"], ...)
```

`shell` is `interior.drum_interior(...)`. This is the **same finding the scorecard has carried as
`blocking P1` since session 2x** (`docs/aaa-scorecard.json`, `drum_ground`, round 1). It has not
moved. It has also got worse in a second way:

```
budget.py "drum visible set"   116,120 tri   (shell + caps + trusses + spokes)
scene.json for the same shot   168,832 tri
```

52,712 triangles — townscape (22,620), hard landscape, trams, core tube — render every frame and
are outside the gate. `budget.py` then prints *"headroom: 183,880 triangles for ground detail,
buildings, trams and vegetation"*, i.e. it offers as headroom a budget that is already partly spent
on content it does not count.

### F-03 · BLOCKING · C1 — the 68 procedural rooms are boxes with wallpaper. 58% of the station

**The Casino, at the three distances.**

```
tools/render_godot.sh --shot interior --room casino --res 960x540 --out casino_normal.png
tools/render_godot.sh --shot interior --room casino --eye " -0.6,1.7,0.16" --target 0,1.7,4.15 …
tools/render_godot.sh --shot interior --room casino --eye 0,1.7,3.15  --target 0,1.5,4.15 …
```

- **Normal (8 m):** a beige box. Two ceiling luminaires blown to pure white with hard polygonal
  edges. One flat blue slab (the `gaming_table`), one dark counter (`bar_counter`), one teal
  emissive rectangle. Nothing in frame says *casino*.
- **Half (4 m):** the far wall is a flat plane with a grid of thin dark lines. No relief. No reveal
  on anything. No wear, no signage, no fitting.
- **Arm's length (1 m):** a featureless dark blue-grey plane. `p95 = 0.0220` — **the entire frame
  sits below 2.2% luminance**. AAA-STANDARD C5 asks that *"the material still has something to say
  with the camera 1 m from the wall"*. It has nothing to say at all.

Measured: `clipped 4.78%`, `crushed 31.90%` at normal distance. `measure_frame.py --against
reference/04-sector-red/Casino.webp` returns **`FAIL clipped under cap 4.78% (max 3.69%)`** — the
frame exceeds the project's own show-derived clipping cap — and **`x0.94 of its 0.0631` against a
`x1.40 ±25%` target, i.e. OUT OF RANGE on the level test too.**

That last number matters more than it looks: `export_scene.ROOM_EXPOSURE` holds **11 archetype
entries for 118 places**. Layer 4a is recorded as *"every location has a rig and a measured
exposure"*. The Casino's exposure comes from the `commerce` archetype and is 33% under its
reference. It was never measured against a frame.

`rooms.articulate()` (session 3s) added bands, deck and soffit grids, mullions, panels and conduit.
That is the *line* the metric asks for. It is not the *content* the metric was written to stand in
for. The room went 18.0% → 100.7% of bar and is still a box.

The group census makes the ratio explicit. `rooms.build()` for `casino` emits **20 groups**:

```
13 trim/shell : deck, deck_joint, skirt, dado, panel, mullion, rib, cornice,
                soffit, soffit_tee, wall, conduit, rail
 2 lights     : light_pendant, light_bar_backlight
 4 props      : prop_gaming_table, prop_credit_terminal, prop_bar_counter, prop_door
 1 fixture    : fix_back_shelving
 0 signage
```

Thirteen groups of moulding, four boxes, and nothing a player can read. The 68 rooms differ from
each other only in footprint, archetype trim pitch and which four `prop_` boxes appear.

### F-04 · BLOCKING · C1 — the tree, at the distance a player stands next to it

```
tools/render_godot.sh --shot drum --eye " -72.2,251.9,4838.0" --target " -84.05,256.0,4838.5" --fov 45
```

At ~12 m: a black stick with a root flare, splitting into **two bare black poles that pass straight
through the canopy and end in mid-air**, crowned by **six flat faceted dark-green discs** floating
with visible gaps between them and the branches. One flat colour. No leaf detail, no translucency,
no cast shadow on the ground. The ground under it is a **uniform flat grey-green plane** — no grass,
no texture, no paving joints.

`garden.tree()` went 30 → 440 triangles and its docstring records why: *"Line comes from real
changes in direction: the root flare, the branch collars, the taper breaks."* Those are precisely
the features that raise λ and do not make a tree read as a tree. **The metric was satisfied by
adding creases. The owner's words were "a sad excuse for a tree" and at the distance he would see
it, they are still accurate.**

### F-05 · BLOCKING · C1 / F1 — the drum ground is two flat polygons, against an authority-1 frame of farmland

```
tools/render_godot.sh --shot drum --stand 20,4700 --look 20,6300 --res 960x540
```
vs `reference/03-sector-blue/Babylon_5_2-22_34b.jpg` and `reference/01-station-exterior/view.jpg`
(both authority 1).

Ours: two olive/tan regions meeting along a hard straight line, no texture, no field boundaries,
no hedgerows, no tracks, no watercourse, no trees, no settlement. It reads as a lasso fill.
Reference: irregular patchwork farmland with hedged boundaries, tracks, a stream, scattered trees
and a settlement, under a **dark open Warren truss**.

`budget.py` measures the ground at **0.020 tri/m² against an allowance of 0.500** — 3.9%. That is
not a budget constraint; it is 96% of an allowance never spent. This is CLAUDE.md's own rule 3
(*"the triangle budget is a TARGET, not a ceiling"*) unapplied to the largest surface in the
project.

Value inversion worth naming separately: in `34b` the truss is **near-black silhouetted against
bright ground**. In ours the guideways are the **brightest** thing in frame. That single inversion
is most of why the frame has `crushed 0.00%` where the reference has 2.66%.

### F-06 · MAJOR · C3 — every light fitting in the interior clips, and the clipping is the *material*, not the light

Measured, on the brig, by rendering the same frame twice:

```
brig, default                          clipped 1.33%   crushed 17.31%   median 0.0439
brig, --fixture-energy 0 (lights off)  clipped 1.25%   crushed 51.56%   median 0.0441
```

Turning every omni off removes **6% of the clipping and none of the median**. The blown highlights
are the luminaires' own emissive surfaces, not their light. `ROOM_EXPOSURE` scales the omnis, so no
exposure value in the project can fix it.

The energies are set on an internal ladder, and `materials.py` says so in its own words —
`light_cage_lamp` at 7.0: *"it clips harder than the bay floods do in their frame"*, on an archetype
that *"is the one archetype in `rooms.py` with no measured reference frame at all"*.

The Zocalo is the worst case. `interior_kit.downlight_pool()` is a **20-segment emissive disc** set
0.012 m into the deck, *and* `fixture_lights` puts an omni above it. At close range
(`--eye " -3.2,1.5,7.0" --fov 50`) the pools are **enormous pure-white clipped ellipses with
dithered, faceted edges**. They read as holes in the floor. In `more hallway.jpg`, the source they
are derived from, the pool has a soft ~0.4 m gradient and the deck grating reads through it.

This is the same `major C3` the scorecard already carries against `zocalo_interior`
(*"Floor light pools blow to pure white discs"*). Unresolved.

### F-07 · MAJOR · C3 — p5 is 1.7×–3.0× the show's on every frame measured. It is one defect, not seventeen

`tools/measure_frame.py --against`, this session, on freshly rendered frames:

| our frame | reference | p5 ×  | band | verdict |
|---|---|---|---|---|
| drum wide | `Babylon_5_2-22_34b.jpg` | **×1.69** | ×1.29 | FAIL (+ `crushed 0.00%` vs 2.66% — "OURS IS EMPTY") |
| garden | `garden.png` | **×2.97** | ×1.29 | FAIL |
| zocalo | `more zocalo.png` | **×2.61** | ×1.29 | FAIL (show crushes 48.5%, we crush 13.3%) |

Three different subjects, three different rigs, same direction, same magnitude. CLAUDE.md already
identified p5 as the discriminator across 17 recorded exposures; this confirms it holds on content
rendered fresh. **The station's shadows do not go dark.** Session 3t's own finding — that shadow
*count* is the lever and 32 casters passes while wrecking the level — is the right diagnosis, and
the default is still 2.

### F-08 · MAJOR · C3 — no hull-mounted fitting casts a shadow, at any sun angle I could produce

```
tools/render_godot.sh --shot exterior --orbit 2200,25,208 --sun-az 150 --sun-elev 6
tools/render_godot.sh --shot exterior --orbit 1500,8,208  --sun-az 128 --sun-elev 5
tools/render_godot.sh --shot exterior --orbit 3000,45,208 --sun-az 208 --sun-elev 3
```

`greeble._access_panel` builds raised slabs **3.5–7 m high**. At a 5° sun a 7 m box throws an 80 m
shadow. In all three frames the fittings show *self*-shading on their own side faces — the geometry
is real and has relief, and the barrel's terminator is correct — and **nothing casts onto the
plating**. In the third frame the dorsal cargo modules stand ~40 m proud at a 3° sun and lay down
no shadow at all. The result is that 1,976 fittings in
662 assemblies read as **decals painted on the hull**, which is AAA-STANDARD C1's second clause
(*"detail that reads as noise rather than machinery"*) applied to work that is otherwise C3.

`exterior.tscn:280` has `shadow_enabled = true` and `render_shot.gd:349` already scales
`directional_shadow_max_distance` to `d × 2.2` *because of this exact class of bug* — its comment
describes cargo modules throwing no shadow at a 10° sun. The fix taken then does not reach greeble
scale. Falsifiable: force `directional_shadow_max_distance` to 3000 on the 1,500 m frame and see
whether the shadows appear.

### F-09 · MAJOR · C3 — the ribs added for the density metric are now the station's dominant surface feature, and the eye indexes them instantly

```
tools/render_godot.sh --shot exterior --orbit 6400,15,208 --lighting night
```
Zoomed to the drum, the hull is **uniform vertical corduroy** — one rib pitch, one depth, running
the full circumference, unrelated to the plating, the greebles or the structural rings. It is the
first thing the eye finds and the last thing it can stop counting.

AAA-STANDARD, materials checklist: *"Tiling: on a flat-on render of the largest surface, count the
repeats. If the eye can index the period, it is CRAFT 3 at best."*

Session 3s added these ribs to close the exterior's density floor at 94.4% of budget. They did
close it. They also made the station look extruded.

### F-10 · MAJOR · F3 — the hull is the wrong colour, and nothing records it

Measured on lit pixels only (luminance > 0.03), linear RGB:

```
reference/01-station-exterior/exterior more.jpg, drum band (top view)   R/B 0.67
reference/01-station-exterior/exterior more.jpg, drum band (side view)  R/B 0.57
ours, same drum band, --orbit 3200,15,208                                R/B 1.36
```

The reference hull is **blue-grey**. Ours is **warm cream**, by a factor of ~2.2 in the red/blue
ratio, in the opposite direction. Qualified honestly: that sheet is authority 4 and
`CONFLICTS.md` C-004/C-007 already flag its provenance as unestablished — so this is not
automatically a defect. What *is* a defect is that **the difference is not written down anywhere**.
AAA-STANDARD F5 requires that *"every difference is enumerated and either fixed or logged"*.

Same pattern on the Garden, where the reference is authority 1:

```
reference/09-garden-core-and-transit/garden.png   linear RGB 0.178 0.140 0.109   R/B 1.64
ours (the frame calibrated against it)            linear RGB 0.230 0.221 0.179   R/B 1.28
```

`garden.png` is a **warm terracotta Wright-influenced civic building** with a reflecting pool, a
fountain, flagpoles, mature trees and two people for scale. Ours is **cold grey concrete boxes and
a finned cylinder**. The frame is photometrically calibrated against that reference to
`verified_median 0.2098` / `×1.492` — *the median of a frame whose content it does not match*.
`INV-044` logs one difference (tower height 16 m vs 25–30 m) and none of the others.

### F-11 · MAJOR · C2 — the exterior components are flat plates 800 m across

```
tools/render_godot.sh --shot exterior --orbit 3200,15,208
```
The swept arrays and radiator blades are **featureless quads** with a faint noise texture. No ribs,
no frame, no attachment structure, no differentiation between a solar array and a heat radiator —
AAA-STANDARD C2's own example: *"Two systems that do different jobs still read as the same kind of
object — solar arrays and cooling fins after session 2b."* Session 3s's note says ribs were added
to *"radiator blades, comms plate, cooling fins"*; the large swept plates carry none in this frame.
The scorecard already scores `exterior_components` craft **1** with a `blocking C1`; it has moved
to 2, not to 4.

### F-12 · MAJOR · C5 — at the third distance the silhouette is not Babylon 5

```
tools/render_godot.sh --shot exterior --orbit 175000,15,208     (≈46 px of silhouette)
tools/render_godot.sh --shot exterior --orbit 175000,35,120     (different azimuth, same result)
```
A featureless white spindle. The arrays, radiators, cobra-bay ring and docking sphere — everything
that makes B5's outline B5's outline — are gone. AAA-STANDARD C5: *"The silhouette is identifiable
at one pixel of screen height."* It is not identifiable at forty-six.

Rendered both with and without the LOD chain built; identical. Which surfaces a separate item:
**`station/generate_hull.py` does not build the LOD chain**, so a fresh checkout renders
`hull.obj` at every distance and logs `hull_lod6.obj missing -- fell back`. CI runs `lod.py`'s
self-test, not `--build`.

### F-13 · MAJOR · R4 — the render pipeline produces silently-wrong frames on a clean checkout

On first render in this worktree:

```
ERROR: res://scenes/exterior.tscn:265 - Parse Error: [ext_resource] referenced
       non-existent resource at: res://materials/habitat_windows.tres
… ×4 …
--- exterior finished in 13s (exit 0) ---
```

The `.tres` files exist. `godot/.godot/` is gitignored, so the texture import cache is absent, the
`Texture2D` ext_resources fail, the ShaderMaterials fail to load, and **eight hull groups render on
the fallback**. The script returns **0** and writes a PNG.

`render_godot.sh` was written specifically to prevent this class of outcome — it refuses on an
unparseable `.tres` (line 105) and on `SHADER ERROR` (line 165), each with a comment explaining
that the frame *"looks merely disappointing rather than broken"*. It does not check for
`Parse Error: [ext_resource]`, which produces the identical outcome. Nothing in
`build_and_render.sh` runs Godot's import pass.

Anyone reviewing from a fresh clone scores a frame that is not the frame.

**And the fix has a trap in it.** The repair is `godot --path godot --import` under xvfb. Running
it **rewrites `godot/project.godot` and deletes its header** — the three lines recording that the
engine must be the double-precision build, with the ADR reference — replacing them with Godot's
boilerplate. 16 insertions, 27 deletions, silently, on a file the project depends on being right.
I reverted it in this worktree. Whatever step ends up warming the import cache has to leave
`project.godot` alone, or the first person who runs it loses the note explaining why the binary is
what it is.

### F-14 · MAJOR · R3 — the project's own quality register is malformed and is not in CI

```
$ python3 tools/aaa_gate.py docs/aaa-scorecard.json
SCORECARD IS MALFORMED -- 52 problem(s)
$ echo $?
1
$ grep -c aaa_gate .github/workflows/validate.yml
0
```

`docs/AAA-STANDARD.md` says *"`tools/aaa_gate.py` enforces exactly this. Nothing below is
advisory."* It is not run by the build, its input has been malformed across at least three
sessions, and the gate itself is healthy (60/60 self-test) — so this is neglect, not breakage.

Worse than the malformation: **the scorecard is four sessions stale in the direction that
flatters.** It still records `generated_rooms` craft **1** and `garden_townscape` craft **1** from
session 3r, while `directory.py` reports the same content COMPLETE at layers 2b, 3 and 4. Two
registers disagree about the same artefact and the green one is the one being quoted in STATE.md
and CLAUDE.md.

### F-15 · MINOR · P3 — `%show` is computed, printed and never binds

`density.py --modules` prints a `%show` column: line density as a fraction of what a Babylon 5 set
actually carries, measured by Canny edge density on authority-1 frames with a human for scale.

```
Range 0.3% to 44.1%, median 24.3%.
binds = "budget" on all 118 rows.
```

The station carries **about a quarter of the show's visible line density**, by the project's own
measurement, and the only one of the three bounds tied to *what it should look like* never binds
once. The module is admirably honest about this in its own output. But a criterion that reports the
fidelity bound and gates on the budget bound is a budget gate wearing a fidelity name, and
`directory.py` reports its result as "geometry — articulation".

### F-16 · MINOR · C4 — eight exterior groups have no material rule

`render_shot: fallback material used by 8 group(s): aft_terminus, docking_sphere,
forward_deflector_spike, forward_taper, forward_waist, generator_torus_housing, hull_flare_aft,
primary_fusion_reactor`

Benign today — `render_shot.gd` notes the exterior's fallback *is* the hull material — but
`export_scene.py`'s own docstring claims *"it asserts that every group it emits has a rule, so
nothing lands on the fallback by accident."* Eight do. Among them the forward taper, forward waist
and docking sphere, which are three of the largest shapes in the silhouette.

### F-17 · NOTE — what is genuinely good, and should not be sacrificed to fix the above

Being harsh is cheap; this is the part that is expensive to rebuild if a rework breaks it.

- **The corridor kit is the best thing in the project.** Warm/cool fitting contrast, deck grating,
  pilaster strips, portal heads, a real cornice. It reads as a spaceship.
- **The Zocalo is a genuine 3** and the arcade/gallery composition is right.
- **Robustness is real.** 3,000+ assertions across 25 modules, all green, from a clean checkout.
  Both `blocking R0` findings on the scorecard (`drum_ground`'s vacuous periodicity check, `tram`'s
  algebraic identities) are **properly closed**, with the old check *proven* vacuous by
  monkeypatching a 3.295 m cliff past it — that is the R4 descriptor, done correctly.
  The tram/spoke interpenetration that AAA-STANDARD names as its standing R5 counter-example is
  now asserted from the spoke's own reported section.
- **`density.py` is a good instrument.** Subdivision-invariant, three independently derived bounds,
  a demonstrated failure mode, and it prints the number that indicts it. The problem is which bound
  is wired to the gate, not the module.
- **`measure_frame.py`'s derived bands are the right kind of rigour** — corpus-derived, validated
  against the show on itself, `--derive` refusing drift.

---

## 3. The four questions

### Q1 — Does it read as Babylon 5, or as generic sci-fi?

**Generic sci-fi, and the missing things are specific.**

1. **The circular structural hoop is absent.** It is B5's single strongest interior signature:
   `reference/10-interiors-generic-kit/central corridor.webp` and `more hallway.jpg` are both
   dominated by large elliptical ribs in blue and oxide red, and the Zocalo arcade in
   `04-sector-red/more zocalo.png` repeats the motif. Our corridor is a rectangular tube with a
   chamfer that `INV-007` admits is *"inferred, not observed"*. Nothing in the interior kit is
   round.
2. **It is far too bright.** Every B5 interior reference is dark with pooled practical light —
   `more zocalo.png` crushes **48.5%** of its frame; our Zocalo crushes **13.3%**. p5 runs
   1.7–3.0× the show's on everything measured (F-07).
3. **Signage exists as light boxes with nothing written on them.** `zocalo.webp`'s focal point is a
   cyan alien-script sign; `more zocalo.png`'s is the orange neon "Zocalo". Ours: `zoc_neon_face`
   is **one instance, twelve triangles, 1.8 m × 0.7 m**, and it renders as a **blank emissive
   rectangle blown to white with an orange fringe**
   (`--shot interior --room zocalo --eye " -2.5,4.6,5.4" --target " -6.3,5.17,5.4" --fov 45`).
   Credit where due, and I had this wrong on the first pass: `station/signage.py` **is** used —
   `customs.py` and `alien_sector.py` both build its transcribed authority-1 boards, and
   `customs.py:533` asserts the text is not retyped. That is exactly right. It reaches two modules.
   The Zocalo's neon carries no glyph and the 68 procedural rooms carry no signage at all, so a
   player cannot read a single word anywhere in 58% of the station.
4. **No crowd.** `zocalo.webp` is thirty humans and aliens filling frame. Ours is empty. Layer 6 —
   fair, but it is the thing that most defines the place.
5. **No clutter.** Fairy lights on a stall, a banner, foliage, a drinks shaker, chairs with a "5"
   on the back, litter on a Downbelow deck (`sleeping-in-light-05.jpg`). Every surface in our build
   is clean.
6. **The palettes are wrong in both directions** — hull warm where the reference is cool (R/B 1.36
   vs 0.57), Garden cool where the reference is warm (R/B 1.28 vs 1.64).

What *does* read as B5: the drum's blue-dashed end-cap rim ring, the white light tubes on the
guideway trusses (correctly derived from `34b`/`33a` rather than hand-placed), the red-brown cargo
modules on the dorsal rail, and the corridor's warm/cool fitting contrast.

### Q2 — The single highest-value thing to fix next

**Re-point the layer-2b gate at the mesh the exporter actually emits, and make the show bound
(`%show`) binding on the ten locations a viewer can catch us on.**

Not "articulate the 68 rooms", and not "rebuild the Garden". Both of those are the *output* of a
criterion, and this project has now twice built to a criterion that could not express what it was
named for. The cost of getting that wrong again is another three layers of work on top of the wrong
thing — which is the price CLAUDE.md already records for layer 2.

Concretely, in order:
1. `density.py:_m_interior` must measure `drum_ground.visible_set()` + the parts `drum_parts`
   emits, and an assertion must compare the module registry against `export_scene`'s part list so
   they cannot diverge again silently. Today they differ by 14% of λ and the difference decides
   five locations' layer status.
2. `budget.py`'s drum gate must total the scene, not the shell (F-02).
3. On the authority-1 subset — Zocalo, corridor, drum ground, Garden, Central Corridor, Downbelow,
   C&C, customs, alien sector, quarters — make `%show` the binding bound. The budget has the room:
   the drum is at 38.7% of its visible-set allowance and the ground at 3.9% of its density
   allowance.

Why this rather than the alternatives:
- *Fix the lighting first (p5)?* It is the most consistent numeric defect and the cheapest single
  win, and it should be done — but a correctly-lit flat polygon is still a flat polygon, and
  session 3t already established that fixing p5 by shadow count breaks the level. That is a rig
  redesign, and a rig should be designed against final geometry.
- *Start layer 5 (props)?* `MASTER-PLAN.md` §3.2 is right that props before the verb set builds the
  wrong 71 — and F-03 shows the props already built (a blue slab for a gaming table, a red slab for
  a bunk) are C1 boxes counted as layer-2 geometry.
- *Rebuild the rooms now?* One generator moves all 68, so it is tempting. But the criterion it
  would be rebuilt against is the one that just certified a wallpapered box, and 68 × the wrong
  target is the most expensive mistake available.

### Q3 — Is anything actively wrong, rather than merely unfinished?

Yes, five things:

1. **A gate that prints PASS on geometry that is thrown away** (F-01) and one that under-counts its
   own scene by 31% (F-02). AAA-STANDARD calls both blocking.
2. **Clipped emissive fixtures in every interior** (F-06) — 4.78% of the Casino frame and the
   Zocalo's floor pools are above the project's own show-derived clipping cap of 3.69%. Clipped
   highlights read as a *rendering error*, not as a bright light.
3. **The Zocalo chairs read as a drum with a hoop floating over it.** The geometry is *correct* —
   `zocalo.cafe_chair()` runs `_arc_panel` continuously from `seat` to `seat + bh` and the top rail
   sits on it — but at the room's own exposure the back panel (`zoc_chair_five`, which carries the
   "5" roundel and is the chair's whole identity), the top rail and the floor beyond all land
   within ~0.02 of each other in luma, so only the rail is legible and the chair looks broken.
   A correct mesh that renders as an error is a craft defect, not a geometry one, and it is the
   more expensive kind: nothing in the geometry gates can see it.
   (`--shot interior --room zocalo --eye " -3.2,1.5,7.0" --target " -5.0,0.9,9.0" --fov 50`.)
4. **A hard, straight, kilometre-long seam across the drum floor** where two land-use bands meet
   with no transition (`--shot drum --stand 20,4700`). Not a hole — a material discontinuity at a
   scale nothing in nature or engineering produces.
5. **A clean checkout renders the wrong frame and exits 0** (F-13).

I looked for and did **not** find: interpenetrating solids (the tram/spoke case is now asserted
closed), lights inside walls (`fixture_lights` derives every source from a tagged fitting centroid,
which is the right construction), or plastic-reading materials — the PBR values are conservative
and defensible. `interior.boundary_edges()` and the 449 interior assertions pass.

### Q4 — What would a player notice in the first thirty seconds?

Standing in the drum, looking down the axis: **the ground is a flat olive polygon with a straight
edge in it, there are no fields, no roads, no trees near enough to see, and the light rails
overhead are the brightest thing in the world.** In the show that same view is the most
awe-inspiring shot in the series.

Walking into a room: **it is empty, it is beige, and the ceiling lights are two white rectangles
with no shape.** They will not be able to tell the Casino from the brig from the Post Office
without reading a sign, and there are no signs.

Standing next to a tree: **it is a black stick with six green plates on it.**

The corridor is the one place they will believe. It is also the place they will spend the least
time, because there is nothing at either end of it.

---

## 4. What the builder has been fooling itself about

Said plainly, because that was asked for.

1. **"118/118 COMPLETE" is being read as a statement about quality and it is a statement about
   spending.** Every one of the 118 rows binds on `budget`, and the budget bound is derived from
   `budget.py`'s allotment. The gate says *"you have spent the triangles you allotted yourself, as
   relief"*. It does not say the place looks like anything. The `%bar` column proves the point on
   its own: 100.7, 100.8, 101.4, 101.4, 101.4, 101.4, 101.5, 102.1, 102.1, 102.8 — **ten
   consecutive locations within 2% of the line**. Content does not land within 2% of an arbitrary
   floor. That is the signature of tuning to a gate, and the gate is not the goal.

2. **STATE.md wrote down the disqualifying caveat and shipped the number anyway.** Session 3s's own
   words: *"'interior passes layer 2' and 'the drum looks better' are different claims, and only the
   first is true."* That is exactly right, and it is under a heading that reads *"layer 2 goes
   16/118 → 118/118"*. Recording an objection is not the same as honouring it. The next context
   inherits the heading.

3. **The scorecard was allowed to go stale in the flattering direction.** `generated_rooms` craft 1
   and `garden_townscape` craft 1 are still the newest rounds in `docs/aaa-scorecard.json`, from the
   session that found them. Three sessions of rework happened and no round was added. Meanwhile
   `directory.py` went green. When two registers disagree, the honest move is to update the harsh
   one first — and `aaa_gate.py` is not in CI to force it.

4. **Photometric calibration is being treated as evidence about appearance.** `DRUM_CALIBRATION`'s
   `garden` entry matches a median and a 3×4 signature grid against `garden.png`. The building in
   that reference is a warm terracotta Wright-influenced civic hall with a reflecting pool and a
   fountain; ours is grey concrete boxes and a finned cylinder. The median matched. CLAUDE.md's own
   layer-4b post-mortem says *"a median is a statistic a flat, washed-out frame matches perfectly"*
   — the same sentence applies to a frame whose subject is wrong.

5. **"Craft claims cite a HALF-distance frame" was adopted as a rule in 3r and has not been
   applied since.** No half-distance or arm's-length frame appears in `docs/` for any content built
   in 3s. The rooms, the Garden and the tree were all rebuilt and judged on the metric, not on a
   frame. Had one arm's-length render of the Casino wall or one 12 m render of the tree been taken,
   this review would have been unnecessary.

6. **`--fixture-energy 0` moves the median by 0.0002.** Nine of eleven `ROOM_EXPOSURE` values are
   already recorded as unverifiable. This adds a mechanism: for these rooms the *emissive surfaces*
   set the bright end and the exposure control cannot reach them. Any further exposure tuning
   before the emissive ladder is measured against a frame is tuning the wrong variable — which is
   the same shape as the `d(ln median)/d(ln gain)` finding already in CLAUDE.md.

---

## 5. Severity ledger

| # | Severity | Dim | Where |
|---|---|---|---|
| F-01 | blocking | P1 | `station/density.py:_m_interior` vs `tools/export_scene.py:982` |
| F-02 | blocking | P1 | `station/budget.py:287` |
| F-03 | blocking | C1 | `station/rooms.py` (68 places) |
| F-04 | blocking | C1 | `station/garden.py:tree` |
| F-05 | blocking | C1 | `station/drum_ground.py` |
| F-06 | major | C3 | `station/materials.py` emissive ladder, `interior_kit.downlight_pool` |
| F-07 | major | C3 | `tools/export_scene.py` light rigs (all shots) |
| F-08 | major | C3 | `godot/scenes/exterior.tscn:280`, `render_shot.gd:349` |
| F-09 | major | C3 | `station/greeble.py` / hull ribs |
| F-10 | major | F3 | `station/materials.py` hull albedo; `INV-044` |
| F-11 | major | C2 | `station/components.py` |
| F-12 | major | C5 | `station/lod.py`, `station/generate_hull.py` |
| F-13 | major | R4 | `tools/render_godot.sh`, `tools/build_and_render.sh` |
| F-14 | major | R3 | `docs/aaa-scorecard.json`, `.github/workflows/validate.yml` |
| F-15 | minor | P3 | `station/density.py` bound selection |
| F-16 | minor | C4 | `godot/scenes/exterior.tscn` material rules |
| F-17 | note | — | what is good |

**Round:** 1 (independent panel). Under AAA-STANDARD's stopping rule the subsystems carrying a
`blocking` finding are stopped and their clean-round counter resets to 0. Three remediation rounds
remain before a `capped` decision is owed to the owner.
