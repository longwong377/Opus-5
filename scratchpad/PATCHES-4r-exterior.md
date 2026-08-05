# PATCHES — session 4r, exterior components

Changes wanted in files this agent does not own. **Nothing here is applied.**
`station/components.py` is the only file the exterior-components work touched.

---

## 1. `station/materials.py` — bind the cargo rail, or it renders red

**Owner:** the materials agent (this file was being edited in the main tree and in
`scratchpad/mat4r/head` while this work ran; the coordinator asked for it as a patch).

**Why it is needed.** `station/components.py::dorsal_line` now builds the sourced dorsal
rail, the five grey plinths, the module feet and the loader gantry. The sheet shows those
GREY and the modules DARK RED — two materials, therefore two groups, because a group is the
finest thing the engine binds a material to.

**And the group must not be called `cargo_module_rail`.** `render_shot.gd::_material_for`
binds by longest substring (`mesh_name.contains(frag)`), so any name containing
`cargo_module` inherits the red container skin. It was built that way once and the frame
came back with a red rail against a sheet that says grey; nothing failed and no gate fired.
The group is `cargo_rail`.

**What is shipping meanwhile.** `components.SPLIT_RAIL_GROUP = False`, which merges the rail
into the `cargo_module` group. That is deliberate: `export_scene.check_material_coverage` is
STRICT on the exterior — an emitted group matching no rule RAISES — so shipping the split
group without this material would not render a grey rail, it would stop the exterior
exporting at all.

**The A/B, both frames at the same camera, both `Vulkan 1.4.318 - Forward+`:**

| | frame |
|---|---|
| with this patch | `docs/craft-4r-ext-cargo-after-railmat.png` — the rail reads as a grey band under the containers with a grey plinth between them, as the sheet shows |
| without it (what ships today) | `docs/craft-4r-ext-cargo-after.png` — the same geometry in the red container skin |

What is lost without it is a **hue, not a shape**. The rail, plinths, feet and gantry are
built either way.

**The measurement behind the colour** — a same-frame ratio, not an absolute, because
`exterior more.jpg` carries the render's grade and INV-010 records that only differences
within the sheet are trustworthy. Rail band (x 639–827, rows 195–201) **65.64/65.08/84.22**
against two independent hull patches **83.65/84.24/88.44** and **82.98/83.11/97.02** →
ratios 0.785/0.773/0.952 and 0.791/0.783/0.868, agreeing to 1% in R and G. Mean
**0.788/0.778/0.910** on `hull_exterior`'s 0.600/0.582/0.564 → **(0.473, 0.453, 0.513)**.
Full derivation in `canon/INVENTIONS.md` INV-585.

### The diff

```python
# station/materials.py, immediately after the `cargo_module` Material
    a(Material(
        "cargo_rail", "Cargo Rail — dorsal loader rail, plinths and gantry",
        # DERIVED FROM `hull_exterior` BY A SAME-FRAME RATIO, not measured
        # absolutely, because `exterior more.jpg` carries the render's own grade
        # and only differences within it are trustworthy (INV-010). On the
        # native sheet the rail band under the module row (x 639-827, rows
        # 195-201) reads 65.64/65.08/84.22 against two independent hull patches
        # at 83.65/84.24/88.44 and 82.98/83.11/97.02 -- ratios 0.785/0.773/0.952
        # and 0.791/0.783/0.868, which agree to 1% in R and G. Mean ratio
        # 0.788/0.778/0.910 on hull_exterior's 0.600/0.582/0.564 gives the
        # albedo below: the same plated grey as the hull, DARKER and slightly
        # cooler, which is what an unpainted structural rail against a
        # weathered painted hull should be. INV-585.
        albedo=(0.473, 0.453, 0.513), roughness=0.74, metallic=0.38,
        specular=0.45, texture="hull_plate", uv_scale=1.0 / 12.0,
        normal_scale=1.0,
        # The group is `cargo_rail` and NOT `cargo_module_rail` deliberately:
        # `render_shot.gd::_material_for` binds by longest substring, so any
        # name containing `cargo_module` would inherit the red container skin
        # above and the rail would render red. `station/components.py`'s
        # `dorsal_line` docstring records that this was built the wrong way
        # round once and that only the picture showed it.
        binds=("cargo_rail",), scenes=("exterior",),
        source="exterior more.jpg dorsal rail band, measured as a ratio to the same sheet's hull plate; 'a continuous raised dorsal rail with small grey plinths between them' (00-INDEX), corroborated by other map 4.jpg's 'dorsal row of ~6 small square modules on a rail' under the heading AUTO LOADERS SEQUENCE"))
```

and one name in `KNOWN_GROUPS`:

```diff
-     "comms_grid_pylon", "reactor_cooling_fin", "cargo_module",
+     "comms_grid_pylon", "reactor_cooling_fin", "cargo_module", "cargo_rail",
```

**Then, in `station/components.py` (mine, one line):**

```diff
-SPLIT_RAIL_GROUP = False
+SPLIT_RAIL_GROUP = True
```

`components._selftest` builds BOTH branches on every run and asserts they are closed,
outward-wound and identical in triangle count, so the branch that is off cannot rot while it
waits. Applied, it needs `python3 station/materials.py --export` and a hull rebuild.

**Verified before reverting:** with the patch applied, `python3 station/materials.py --export`
ran clean (2342/2344, the two failures pre-existing and unrelated — `drum_endcaps`/`ground_*`
literals and `alien_status_lamp_dark`), the exterior stayed at **16 materials of a 64
draw-call budget (25.0%)**, and the frame above was rendered from it.

---

## 2. `station/schema/station.yaml` — two dead keys and one measured proportion

**Owner:** whoever owns the schema.

### 2a. Delete `root_taper` from `reactor_cooling_fin`

```diff
-{'id': 'reactor_cooling_fin', ..., 'root_taper': 0.5, ...}
+{'id': 'reactor_cooling_fin', ..., ...}
```

Superseded in session 3s, and by something better sourced: `planar_blades` replaced the
root-to-tip taper this key sets with `PLANFORM`, a seven-point lozenge read off
`exterior more.jpg` — 00-INDEX, "tapered lozenges, wide at mid-height and narrowing at both
root and tip". A single taper factor cannot express that shape. It is currently held open by
name in `components.SUPERSEDED_SPEC_KEYS`; deleting the key lets that entry go too.

### 2b. `cargo_module.fill` — measured 0.537, schema says 0.62

```diff
-  fill: 0.62
+  fill: 0.537        # measured, INV-580
```

The modules occupy **18.33 of 34.13 px of their own pitch = 0.537** on the orthographic
sheet. 0.62 makes each container 15% longer than the sheet shows and shrinks the gaps the
plinths sit in.

**Not urgent and not free.** `dorsal_line` now RAISES if `fill` leaves the terminal gantry
less than `pitch / CARGO_SLEEPERS / 2.5` = 19 m; 0.537 gives it 63 m, so this direction is
safe. It changes the silhouette slightly, so it wants its own before/after frame.

### 2c. `cargo_module.protrusion_m` — measured 0.873 of module length, built 0.390

**Recorded, NOT recommended without a frame.** The side view gives a module height of 16.0 px
against a length of 18.33 px, i.e. **0.873** of its own length. The schema's 46 m against a
built length of 117.8 m is **0.390** — less than half. Building to the measurement roughly
doubles how far the train stands off the hull, moves the station's silhouette, and interacts
with `validate.py`'s radius envelope and `lod.max_radius`. `station/components.py` builds
strictly inside the schema for that reason: the module's top is still exactly
`r0 + protrusion_m`, unchanged.

Whoever takes this should render the before/after at `docs/craft-4r-ext-cargo-after-row.png`'s
camera first.

---

## 3. `canon/00-MASTER.md` / `canon/CONFLICTS.md` — "Width at communications grid" is ambiguous

**Not a patch — a conflict that wants an entry, and it is not this agent's to resolve.**

§1.1's rescaled table gives `Communications grid span | 819 | 2120.5` and
`Width at communications grid | 345 | 893.2`. `station.yaml` uses the second as the grid
panel's own width. Every *other* row in that table is a section dimension ("Blue Section
diameter", "Bio-Habitat interior length") and "width **at** X" reads naturally as the
station's width at X. Against that, "span" and "width" together are also one panel's two
dimensions.

The measurement does not settle it: the hull profile gives a diameter of **301.2 m** at the
grid's placed z and **329.6 m** at z 2,515, nowhere near 893.2, so the location reading is
not satisfied by the current placement either.

`station/components.py` uses `grid_width_m` exactly as handed over and changed only the
grid's construction (INV-583), so the component's extent is unmoved whichever reading wins.
Full statement in `canon/INVENTIONS.md` INV-584.

---

## 4. `station/lod.py` — noted, not requested

The coordinator's `PATCHES-4r-drumbudget.md` §2 (FOV_DEG 50.0 → 70.0) is not blocked by
anything here. Every craft frame in this session forces `--lod lod0`, so the ladder does not
enter the exterior craft judgement and these scores survive that constant moving. The
exterior ladder's triangle counts WILL move and are quoted in
`docs/aaa-scorecard.json::exterior_components` round 3 at the 50° calibration; re-check them
after the flip.

---

## 5. `station/schema/station.yaml` — TWO COMPONENTS INTERPENETRATE, and this is blocking

**`python3 station/components.py` now exits 1 on this, deliberately.** It is 55/56, the CI
step carries `continue-on-error` so it blinds nothing behind it, and `budget.py` is the
precedent: a gate that is honestly red stays red and the fix is a decision somebody makes
rather than a threshold somebody tunes.

`components.dome_intrusions` tests other components' vertices against a dome's exact
half-ellipsoid interior. It reports:

| dome | at | intruder | vertices inside | deepest |
|---|---|---|---|---|
| `observation_dome` (Dome 2) | 90.0° / z 7180 | `cobra_bay` | 70 | **32.3 m** |
| | | `cobra_bay_well` | 48 | 25.5 m |
| `observation_dome` (Dome 1 — **Command & Control**) | 90.0° / z 7060 | `cobra_bay` | 6 | 7.3 m |
| | | `cobra_bay_well` | 17 | 5.5 m |
| `docking_port` (Primary) | 90.0° / z 5240 | `cargo_module` | 290 | **49.8 m** |

**Both clashes are PRE-EXISTING.** Measured against `git show 1982be0:station/components.py`,
the dome/cobra rows are identical and the docking-port row read 2 vertices at 29.7 m. **My
rework deepened the second one** — 29.7 → 49.8 m and 2 → 290 vertices — because the cargo
rail is now *continuous* through z 4870–6010, as both authority-2 sources say it is, where
before there was empty hull between modules 1 and 2. The clash is not mine; that part of its
depth is.

**Why it cannot be fixed in `station/components.py`.**

*Cobra bays vs domes:* re-clocking the ring does not help. At r = 167 m the 28-bay ring has a
25.71° pitch of which a bay envelope eats 14.8°, leaving a **10.9° gap**; a 46 m dome needs
**31.6°**. The dome does not fit between two bays at any phase. Cobra ring 1 #3 currently sits
at exactly 90.00° / z 7182.5 against a dome at exactly 90.0° / z 7180.0.

*Cargo train vs docking port:* both are on the 90° meridian, the port is 88 m in radius and
52 m tall against modules 46 m proud, and the train spans z 4870–6010 across the port's
z 5150–5330. A 176 m diameter port and a cargo train on the same meridian cannot coexist.

Both are PLACEMENT decisions and placement lives in the schema.

**Corroborated from two directions this file cannot see**, which is why the domes are the
likelier thing to move: `interior.hull_fit()` independently lists `obs_dome_1` and
`obs_dome_2` among 34 located places built outside the pressure hull, and `--vista-gate`
reports both domes authored facing forward past the nose. Three unrelated measurements now
say the domes are in the wrong place.

### The options, in the order I would try them

1. **Move the observation domes off the cobra ring's z band.** They are placed z 7000–7240
   against a cobra ring at z 6980–7250 — the same band. Contract 5 puts both "on the forward
   docking structure", which is a region and not a coordinate. This is the change the
   `hull_fit` and `vista-gate` findings point at anyway, so it is one fix for three symptoms.
2. **Give `cobra_bay` a `phase_deg`** and move the domes to a meridian a bay gap can hold —
   only viable together with a smaller dome or a shorter ring, per the 10.9° vs 31.6° above.
3. **Move the cargo train's meridian off the primary docking port's.** `plane_deg: 90` on
   both. The sheet establishes the train is *dorsal* and on one meridian; it does not
   establish which meridian relative to the port.

Whichever is chosen, `components.dome_intrusions` is the check that says it worked, and its
control (withhold one intruding group, assert exactly that group's rows disappear) is what
stops it going vacuous.
