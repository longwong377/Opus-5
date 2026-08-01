# 4f — the coverage assertion that ran on two shots out of four

**Finding it closes:** `judge-4e` F-2, *blocking* — *"`tools/export_scene.py:19` advertises a
material-coverage assertion the `deck` shot never runs; 2 groups / 2,208 tri on the fallback in
every deck frame"* — and F-8, *"9 of 41 hull groups unbound"*.

Every frame in this document was produced by `Vulkan 1.4.318 - Forward+ - llvmpipe`. The line is
grepped out of each run's log and quoted below, because session 4e's whole visual pass was
invalidated for want of it.

---

## 1 — What was actually wrong, and it is not what the frames looked like

The header of `tools/export_scene.py` has said since session 3k that it asserts *"every group it
emits has a rule, so nothing lands on the fallback by accident"*. `unmatched_groups()` had exactly
two call sites: `drum` (asserted in `_selftest`) and `exterior` (**printed as a note**). The `deck`
and `interior` shots — the two a player's camera actually uses, and the one the same file calls
*"the build"* — reached neither.

**The two shots differ in what an unbound group looks like, and that is why this survived.**

| scene | `fallback_material` | an unbound group renders as |
|---|---|---|
| `drum.tscn` | `m_unbound` | deliberately impossible magenta — **loud** |
| `exterior.tscn` | `m_hull` (= `hull_exterior`) | correct hull plate — **invisible** |
| `interior.tscn` | **none declared** | `render_shot.gd` sets a null override, so the glTF's own default survives: **white plastic** |

So the deck's two groups were not on a grey fallback. They were on **no material at all**.

**One correction to the finding's wording, and it matters for how the evidence was taken.**
judge-4e says *"2,208 tri on the fallback in every deck frame"*, and the count is exact — it is
`dress_post` 608 + `dress_skid` 1,600, counted off `shot_blue_0_0.obj`. But
`render_shot.gd` reports every group in the **scene**, not every group in the **shot**, and at the
`--at docking_bays` camera those instances are behind the eye: re-rendered with and without the 45
new rules, `docs/engine-4f-mat-deck-corridor.png` is **0.000% different, max channel delta 0**.
The nearest of the twenty `dress_post` clusters is 7.4 m from that eye at azimuth −2.0°, and the
camera looks the other way. So the frame the defect was found in does not show it, which is
precisely why the assertion had to be about the shot's group list and not about a picture. The
frame that does show it is §2.1.

---

## 2 — The deck: `dress_post` and `dress_skid` were 2 of 22, not 2 of 2

The two names the engine reported are the two that a *freight* corridor happens to emit. The
vocabulary is larger, and the reason none of it was caught is one sentence:

> `corridor_dressing.run` names its clutter `f"dress_{kind}"` at run time, out of
> `SCHEMES` × `dressing.MACHINES`. **No source-literal scan can see a name that is built by string
> interpolation** — and `materials._scan_generator_groups` is a regex over the generators' source.

`dressing.machine`'s own docstring explains why the name reaches a render at all: the outer span is
appended first and covers every triangle, and the part spans override it. Whatever a builder
leaves un-parted therefore keeps the outer name — and every builder leaves something:

```
kind        residual triangles on the OUTER span (1.0 x 1.6 x 1.0 m box)
vessel        564 / 1488   the tank barrel, its domes and flanges
furnace       532 / 1412   the stack shell
drum          252 /  584   the barrel
skid           64 /  400   the motor and the volute
console        48 /  284   the desk mass
gantry         44 /  196   the column
post           32 /  128   the shaft, between its own steel base collar and dome cap
reel           32 /  288   the reel drum
bed block cabinet counter crate crane duct kerb leaf screen seat wallpanel
               12 each     the body: mattress, mass, carcase, leaf, plate, pan
rack pipe_bank  0          fully parted
```

Measured before the change: **19 of the 22 machine kinds had no `dress_*` bind**, and separately
**26 of `rooms.PROPS`' 99 names had no `prop_*` bind**. The 26 are all declared in *bespoke*
rooms — customs, the Zócalo, the Council chamber, hospitality, quarters, the alien sector, plant,
garden, components, the core tube — and they became reachable in session **4d**, when
`rooms.place_interacts` was extracted so bespoke rooms could place their declared interactables at
all. Before 4d they were emitted by nobody, so nothing could miss them.

### 2.1 — The frame that shows it

**`docs/engine-4f-mat-post-ab.png`** — a corridor bollard at **3.7 m**, which is inside the
rubric's half distance for an object a player walks past. Same geometry, same camera, same lights:
the deck was exported once and rendered twice with `--no-export`, so the only difference between
the halves is the 45 rules.

```
after   tools/render_godot.sh --shot deck --deck blue/0/0 \
            --eye 209.559,-10.616,7121.305 --target 210.889,-7.275,7122.286 \
            --res 1280x720 --out docs/engine-4f-mat-deck-post.png
        renderer: Vulkan 1.4.318 - Forward+ - llvmpipe
        (no "fallback material used by" line)

before  --no-export, the 45 rules deleted from interior.tscn
        renderer: Vulkan 1.4.318 - Forward+ - llvmpipe
        render_shot: fallback material used by 2 group(s): dress_post, dress_skid

diff    3.382% of pixels differ, mean 0.230/255, max channel delta 143
        the changed pixels go from sRGB (88.7, 80.2, 81.1) to (84.3, 74.6, 74.7)
```

Before, the bollard's **shaft is bright white plastic** between a dark steel base collar and a dark
steel dome cap — the machine's own `P.frame` parts were materialled and the body between them was
not, which is what "the outer span carries the body" means when nothing binds the outer span.
After, the shaft is the same oxide steel as its collar and cap, and the hazard band reads as a band
rather than as the only thing on a white stick.

Also rendered for the record, at the judge's own corridor camera:
`docs/engine-4f-mat-deck-corridor.png` (816,188 triangles, 897 mesh instances, 1,557 lights, no
fallback line).

### The 45 groups, and what each now takes

Nothing new was measured and no material was added. Every bind takes the material the library
already gives to the same object under another name — the room's copy of the corridor's clutter,
or the neighbour of the same machine kind.

| group | material | sheet | why this one |
|---|---|---|---|
| `dress_post` `dress_skid` `dress_gantry` `dress_block` | `steel_gantry_oxide` | truss_steel | the machine's own `P.frame` parts — base collar, dome cap, baseplate, cooling fins, legs, courses — are already this |
| `dress_duct` `dress_drum` `dress_pipe_bank` `dress_reel` `dress_vessel` | `clad_services` | wall_plate | every room object of those five kinds lands here (`fix_service_duct`, `fix_generator_plant_tank`, `fix_*_plant_pipe`, `fix_umbilical_plant_pipe`, `fix_plant_column`) |
| `dress_cabinet` `dress_counter` `dress_wallpanel` | `furn_casework` | composite_matte | `prop_locker`, `prop_counter`, `prop_desk` — same kinds, painted steel bodies |
| `dress_console` | `device_console_bed` | composite_matte | `prop_console`, same kind |
| `dress_seat` | `furn_pale_composite` | composite_matte | `prop_bench`, same kind; the material's own title says "slab benches" |
| `dress_bed` | `furn_upholstery` | cloth_weave | `prop_bunk`, same kind |
| `dress_rack` | `furn_shop_steel` | truss_steel | `prop_tool_rack`, same kind |
| `dress_leaf` | `door_leaf_painted` | wall_plate | `prop_door`, same kind |
| `dress_furnace` | `steel_furnace_scorched` | truss_steel | `fix_furnace_stack` — literally the same machine, `_m_vessel(furnace=True)` |
| `dress_kerb` | `edge_chevron_nosing` | hazard_chevron | the corridor `works` barrier; `_m_kerb` already parts 48 of its 132 triangles into `accent_warning` |
| `prop_bollard` | `furn_casework` | composite_matte | `customs_bollard` is the same object in the same hall |
| `prop_shower` | `furn_clinical` | composite_matte | `qtr_shower` is the shower this material was bound for |
| `prop_dartboard` | `bar_dartboard` | composite_matte | `hospitality` builds `bar_dartboard`; `directory` declares `dartboard` |
| `prop_shopfront` | `zoc_screen` | composite_matte | the material is *named* "Colonnade Shopfront" |
| `prop_pendant_lamp` | `bar_pendant_shade` | composite_matte | the shade, **not** `bar_pendant_lamp` (emission 9.0) — the source is a separate group and binding the body to it would light the room twice |
| `prop_info_board` `prop_welcome_board` | `signage_panel` | signage_panel | the backlit board the customs hall is about |
| `prop_station_schematic_screen` `prop_menu_display` | `device_screen_glass` | — | `prop_monitor_wall` / `bar_display` |
| `prop_speaking_position` | `device_console_bed` | composite_matte | `prop_console`, same kind |
| `prop_delegate_bench` | `furn_casework` | composite_matte | the chamber's own `council_top` / `council_frame` |
| `prop_cafe_table` | `furn_pale_composite` | composite_matte | the material's own title says "café tables" |
| `prop_reception` `prop_breather_dispenser` | `furn_casework` | composite_matte | `prop_counter`; a dispenser is a wall cabinet |
| `prop_baggage_scanner` | `furn_clinical` | composite_matte | `fix_equipment_gantry`, same `gantry` machine; the title says "equipment gantries" |
| `prop_barred_screen` | `furn_shop_steel` | truss_steel | `fix_cell_divider` — bars over an opening, same `screen` machine |
| `prop_gallery_rail` | `grab_rail_bare` | metal_grain | `cc_rail`, `bar_footrail`. **Not** `zoc_rail`: `gallery_rail` is declared in `interior_kit` too, and a room-specific accent would paint every gallery on the station Zócalo red |
| `prop_market_stall` | `furn_stall_canvas` | cloth_weave | `prop_stall` under the gazetteer's longer name |
| `prop_planter` | `furn_dark_stone` | stone_agg | this material's own "pool copings". **Not** `garden_coping_stone`, which measures the same surface and is scoped to the `drum` scene, so it cannot serve an interior group |
| `prop_launch_tube` | `clad_services` | wall_plate | every `vessel`-kind object |
| `prop_clamp` | `steel_gantry_oxide` | truss_steel | `prop_docking_clamp` at a smaller size |
| `prop_building_door` `prop_gallery_door` | `door_leaf_painted` | wall_plate | painted panel leaves — neither is a blast plate nor welded scrap |
| `prop_shuttle_door` | `door_blast_plate` | deck_plate | a pressure door on a bore open to vacuum, i.e. `prop_airlock_door` |
| `prop_stool` | `furn_upholstery` | cloth_weave | `bar_stool` |
| `prop_brazier` | `steel_furnace_scorched` | truss_steel | the only heat-scorched surface the library measures |

**Textures, session 4e's question:** 43 of the 45 groups take one of the 16 trim sheets, inherited
from the material they bind to — no new sheet, no new binding rule, no change to `TEX_SIZE` or to
texture memory (97.3 MB, 3.17% of budget, unchanged). The two that stay bare are
`prop_station_schematic_screen` and `prop_menu_display` on `device_screen_glass`, which is in
`UNTEXTURED_BY_DESIGN["glass"]` — *"a lit screen's content is not a microstructure map"*.
`UNTEXTURED_BY_DESIGN` is unchanged: this session added no material, so it had no new decision to
record.

---

## 3 — The exterior: the count was right and the reading was wrong

judge-4e: *"nine of 41 hull groups render on the glTF fallback… visible as smooth untextured
plastic against the greebled cylinders beside them."* The first half is exact. The second does not
survive its own control.

`exterior.tscn` sets `fallback_material = ExtResource("m_hull")`, and `m_hull` **is**
`godot/materials/hull_exterior.tres` — the same triplanar `hull_plate` material the bound sections
take. So the nine already rendered as hull.

**A/B, same camera, same geometry, the nine rules removed from `exterior.tscn` for the "before"
half:**

```
after   tools/render_godot.sh --shot exterior --orbit 4600,18,214 --res 1280x720
        renderer: Vulkan 1.4.318 - Forward+ - llvmpipe
        (no "fallback material used by" line at all)
        docs/engine-4f-mat-exterior-half.png        314,338 bytes
        md5 ec52e40c22ab585b1c934d9cd8449cb4

before  same command + --allow-unbound, nine rules deleted
        renderer: Vulkan 1.4.318 - Forward+ - llvmpipe
        render_shot: fallback material used by 9 group(s): aft_terminus,
          docking_bay_throat, docking_sphere, forward_deflector_spike,
          forward_taper, forward_waist, generator_torus_housing,
          hull_flare_aft, primary_fusion_reactor
        314,338 bytes
        md5 ec52e40c22ab585b1c934d9cd8449cb4

        BYTE-IDENTICAL. Both halves were produced and both were Forward+ --
        CLAUDE.md: "any harness that compares two outputs must assert both
        were produced", after an A/B once said IDENTICAL because both halves
        had died.
```

And a third identity worth recording: that md5 is also `docs/judge-4e-exterior-half.png`'s, so the
exterior render is reproducible from the judge's own committed command at this head.

**So what WAS wrong.** Nine surfaces on an 8 km hull had no binding anybody had chosen. They
followed `fallback_material`, and would have followed it anywhere it went. The old assertion in
`materials.py` made that worse by writing the default down as a decision —

```python
check("the exterior hull material is deliberately unbound (it is the fallback)",
      BY_NAME["hull_exterior"].binds == ())
```

— which is an assertion that could only fail if somebody *fixed* the thing. It is now
`"the exterior hull material binds the plated sections by name"`. `hull_exterior` is still the
fallback; the fallback is a safety net, not an answer.

The eight are the `longitudinal.features` ids from `station/schema/station.yaml` whose `kind` is
plating — `hull`, `cone`, `neck`, `flare`, `spike`, `terminus`. The ninth,
`aperture.GROUP_THROAT`, goes to `bay_well`: an unpainted lining inside a hole cut in the hull is
what the cobra bay well was measured as, and its lip already resolved through `hazard_chevron`'s
`bay_lip`.

---

## 4 — Where the check runs now, and how it can fail

**One call site, not four.** `check_material_coverage()` runs inside `export_scene.build()`, which
every shot passes through and which reads the `.tscn` each shot names for itself. The defect was
never "somebody wrote the wrong check" — it was "three of four call sites do not have one", and a
per-builder check is three chances to forget plus a fourth the next time a shot is added. It
**raises**; `--allow-unbound` downgrades it to a note and is recorded in the command a frame is
taken with.

**And a check that needs a built deck is a check that cannot run.** Building `blue/0/0` is minutes
of CPU, and a self-test that reads `station/generated/scene/deck/*` would be a gate that reads an
artefact it cannot rebuild — the defect CLAUDE.md records against `--gate-frames`. So
`export_scene._selftest` and `materials._selftest` both ask the same question of a **derived**
vocabulary instead, built the way the generators build it:

```
dress_<kind>   every dressing.MACHINES kind — because SCHEMES may name any of
               them, so adding a row to a scheme cannot produce an unbound group
fix_<name>     every rooms.FIXTURES and rooms.PLACE_FIXTURES entry
prop_<name>    every rooms.PROPS entry
<prefix>mp_*   dressing._Parts, for all three prefixes
```

193 names, resolved against `interior.tscn`'s exported table by the same substring/longest-wins
rule `render_shot.gd::_material_for` uses.

**Every one of them has a negative control that fires:**

| control | result |
|---|---|
| strip `dress_*` from the rule table, re-run the vocabulary check | fails — so the check is not passing on an empty vocabulary |
| `check_material_coverage` on a group no rule can match, `strict=False` | returns it |
| the same, `strict=True` | raises `ValueError` |
| delete the nine hull rules and export the exterior | the check reports 9 of 41 (see §3) |
| the whole change, run against the code as it was | 19 `dress_*` + 26 `prop_*` + 9 hull = **54 unbound**, which is how they were found |

---

## 5 — Numbers

| | before | after |
|---|---|---|
| deck shot, groups on the fallback | **2** (`dress_post`, `dress_skid`) | **0** |
| deck shot, triangles on the fallback | **2,208** (608 + 1,600, counted off `shot_blue_0_0.obj`) | **0** |
| exterior, hull groups with no rule of their own | **9 of 41** | **0 of 41** |
| interior group names a room or corridor can emit, unbound | **45** of 193 | **0** |
| `interior.tscn` material rules | 505 | **550** |
| `exterior.tscn` material rules | 35 | **44** |
| materials in the library | 168 | **168** (none added) |
| trim sheets / texture memory | 16 / 97.3 MB | **16 / 97.3 MB** |
| `python3 station/materials.py` | 2,315 / 2,319 | **2,323 / 2,323** |
| `python3 tools/export_scene.py` | 264 / 265 | **268 / 269** |

**The four `materials.py` failures that are now closed** were: the two `.tscn` rule tables out of
date with the library (both fixed by `--export`); the `hull_exterior.binds == ()` assertion
described in §3; and `"every group literal found in the generators resolves"` on **`drum_office`**,
which is a `directory` PLACE KEY that arrived in `populace.py` when session 4e's office-hours
regression landed. The scan's own comment names that exact string as its example of a
specification-not-a-surface, so it is excluded in `NOT_GROUPS` rather than by excluding
`populace.py`, which does emit geometry.

**The one `export_scene.py` failure that remains is pre-existing and environmental:**
`every chain level has a built mesh: missing ['lod0'...'lod7']`. `station/generated/*.obj` is
gitignored and this container has only `hull.obj`; the hull LOD chain has never been built here.
Nothing in this change touches LOD selection.

---

## 6 — Reproducing

```bash
python3 station/materials.py                 # the library's own assertions
python3 station/materials.py --export        # .tres + textures + both rule tables
python3 tools/export_scene.py                # the shot assertions, incl. the derived vocabulary

tools/render_godot.sh --shot exterior --orbit 4600,18,214 --res 1280x720 \
    --out docs/engine-4f-mat-exterior-half.png
tools/render_godot.sh --shot deck --deck blue/0/0 --at docking_bays --res 1280x720 \
    --out docs/engine-4f-mat-deck-corridor.png
```

Grep every run for `renderer:` and confirm `Forward+`. A Compatibility frame is not evidence.
