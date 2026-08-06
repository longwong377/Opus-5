# PATCHES — session 4r, docking bay (craft agent)

Owner of `station/docking_bay.py`. Nothing below is applied to the main tree. Each item names the
file, the measurement that justifies it, and — for the two lighting ones — the frames it was
verified in, taken in `git worktree` at commit `e6b0ec8` so no other agent's artefacts were touched.

Every render cited confirmed `Vulkan 1.4.318 - Forward+ - llvmpipe` in its own stdout. No run
reported `OpenGL 3 Compatibility`. Camera on every one:
`tools/render_godot.sh --shot interior --room docking_bays --eye 0.0,1.70,7.17
--target 0.0,9.0,35.0 --res 1280x720`, fov 46.0° vertical (`export_scene.SHOT_FOV_DEG`).

---

## #1 — `godot/scenes/interior.tscn`: the fog is set for a corridor and applied to a 140 m hangar

**THIS IS THE ONE THAT MATTERS. It is also the one I am least entitled to apply**, because
`volumetric_fog_density` is a single global for every interior in the project and changing it
re-judges the corridor anchor, layer 4b's thirteen passing rows and every committed frame at once.

**What it is.** `interior.tscn` line 286: `volumetric_fog_density = 0.014`, with
`volumetric_fog_albedo = Color(0.78, 0.81, 0.88)` — a cool medium at a density set on a 21.6 m
corridor. A docking bay's sight line is 140 m, and the slant from a standing eye to the truss is
about 30 m: `exp(-0.014 × 30) = 0.66`, so a third of every truss pixel is blue fog.

**The measurement.** Fraction of visible pixels with R > 1.15·B, and the truss band's own R/B,
against `dock.webp` measured by the same code (`scratchpad/db/measure.py`):

| run | truss R/B | truss/deck lum | warm px | frame |
|---|---|---|---|---|
| **shipped, fog 0.014** | 0.574 | 0.266 | **3.1%** | `docs/craft-4r-dockingbay-after-normal.png` |
| fog 0.005 | 0.787 | 0.177 | **18.8%** | (worktree, not kept) |
| fog 0.0025 | 0.834 | 0.168 | **28.7%** | `docs/craft-4r-dockingbay-CONTROL-fog-0.0025.png` |
| fog off | 0.849 | 0.167 | **32.0%** | `docs/craft-4r-dockingbay-CONTROL-fog-off.png` |
| **`dock.webp`** | **1.157–3.191** | **0.120–0.262** | **39.5%** |

Monotone in one variable, everything else held. The deck also gets BRIGHTER as the fog comes down
(0.0886 → 0.1045), so this is not a trade against level.

**What I am proposing, and it is not "turn the fog down".** The fog is a property of the VOLUME and
the engine is being handed one number for a corridor, a chapel and a hangar. The right shape is a
per-shot density, the way `ambient` and the fixture energy already are:

- `tools/export_scene.py::build_interior` / `build_deck_shot` emit `"fog_density"` in `scene.json`,
  derived from the room's own longest sight line rather than authored — e.g. hold the optical
  depth over that sight line at the corridor's own value, `0.014 × 21.6 / sight_m`, which gives
  0.0022 for a 140 m bay and leaves the corridor at exactly 0.014 by construction;
- `godot/scripts/render_shot.gd` reads it onto the Environment, defaulting to the `.tscn` value so
  every existing shot is byte-identical when the key is absent.

**Caution.** `--gate-frames` should be re-run after; rooms shorter than the corridor would get MORE
fog under that formula, so it wants a clamp at the authored value until each is re-judged.

---

## #2 — `tools/export_scene.py` + `station/materials.py`: `bay_uplight`. BUILT, MEASURED, AND I DO NOT RECOMMEND IT

Session 4m's note on this room prescribes exactly this: "giving it light needs an uplight component
on the fitting, which is a new emitted group in `docking_bay.py` and a new FIXTURE_LIGHTING row,
not a gain." I built both halves and they do not do what the note expects.

| run | truss R/B | truss/deck lum | warm px |
|---|---|---|---|
| shipped, no uplight | 0.574 | **0.266** | 3.1% |
| uplight `energy_rel` 0.15 | 0.618 | 0.538 | 3.5% |
| uplight `energy_rel` 0.30 | 0.648 | 0.816 | 3.8% |
| uplight `energy_rel` 0.55 | 0.676 | 1.263 | 3.9% |
| `dock.webp` | 1.157–3.191 | **0.120–0.262** | 39.5% |

**+0.7 points of warm, and it breaks the one statistic the room had right.** `dock.webp` is a bright
deck under a dark warm roof — truss/deck 0.12–0.26 — and the uplight takes ours to 0.82, i.e. it
lights the ceiling to the level of the floor. The cause is #1: adding light to a blue medium adds
blue in-scatter as fast as it adds warm surface. Cross-checked with fog off, where uplight 0.30
still only moves warm 32.0% → 34.5%.

**So: land #1 first. If #1 lands and the truss is still short, #2 is ready and the diff is below.**
`station/docking_bay.py` already builds the crown aperture as real geometry and already tags it
through one constant, `UPLIGHT_GROUP`, so this module's whole share of the change is
`UPLIGHT_GROUP = "bay_uplight"`. Applying #2 also requires `python3 station/materials.py --export`.

---

## #3 — `tools/export_scene.py`: `check(len(_bay) == 39, ...)` is a pinned copy of a computed number

`export_scene._selftest` line ~5234. This is the same defect the Zocalo assertion immediately below
it was fixed for and documents at length — "Re-pinning to 60 would go stale the day `bays_for`'s cap
moves" — and it was not applied to the line above. It is **not stale today**; it is a landmine.
`docking_bay.py` cannot add ANY light to its own room without turning it red, which is how #2 came
to be a patch rather than a change. The replacement derives the count from
`docking_bay.LAMPS_PER_BAY_GIRDER` and the girder count, and keeps what the assertion is actually
for (a span is not a fitting) by still multiplying the module's own two numbers.

---

## #4 — `tools/export_scene.py`: `FIXTURE_LIGHTING["bay_lamp"]["angle_deg"]` 35 → 28. NOT ATTEMPTED, and why

The 4m note names this as "the next single-variable experiment". I did not run it, because I could
not do it honestly in the time: a narrower cone lights less floor, so it needs a re-solve of
`ROOM_EXPOSURE`/`BESPOKE_EXPOSURE` for this room by the four-render procedure recorded above
`ROOM_EXPOSURE`, and a half-solved exposure is worse than none. What I did establish is the target
it should be solved against — summing Godot's own attenuation over the shipped rig on the clear
deck (`scratchpad/db/pools.py`, no render):

| cone | mean E | p5 | p95 | p95/p5 | longitudinal modulation |
|---|---|---|---|---|---|
| **35° (shipped)** | 0.6733 | 0.2061 | 1.2665 | 6.14 | **44.6%** |
| 28° | 0.3899 | 0.0000 | 1.1771 | ∞ | **84.5%** |
| 22° | 0.2151 | 0.0000 | 1.0489 | ∞ | 100.0% |

28° scallops (84.5% modulation) and leaves 5% of the deck at exactly zero fitting light, which is
what "discrete cones with dark between them" is. It also costs 42% of the mean, which is the
re-solve. Run `python3 scratchpad/db/pools.py` to reproduce; it takes seconds and needs no GPU.

---

## The verified diff for #2 and #3

```diff
diff --git a/station/materials.py b/station/materials.py
index 9d5e1c6..50e7c87 100644
--- a/station/materials.py
+++ b/station/materials.py
@@ -4122,7 +4122,12 @@ def _build():
         albedo=(0.620, 0.620, 0.610), roughness=0.35, metallic=0,
         specular=0.25,
         emission=(0.942, 0.929, 1.000), emission_energy=6,
-        binds=("bay_lamp", "light_highbay", "light_plant_flood"),
+        binds=("bay_lamp",
+               # The SAME FITTING seen from above: `docking_bay.floodlight`
+               # builds the shade's open crown as its own collar so the truss
+               # it hangs from is lit by it, and a crown aperture is the lamp,
+               # not the steel round it.
+               "bay_uplight", "light_highbay", "light_plant_flood"),
         scenes=("interior",),
         source="reference/03-sector-blue/dock.webp (authority 1). Measured RAW, because a source keeps its own colour and balancing it would remove exactly the thing being read — the same treatment materials.py gives the Zocalo shopfront and the rotunda altar. The two unoccluded flood cores read rgb 0.408/0.400/0.435 (H 253 S 0.081) at (0.368,0.092)-(0.386,0.108) and rgb 0.539/0.524/0.565 (H 263 S 0.073) at (0.527,0.070)-(0.545,0.088); k-means over the pool at (0.360,0.085)-(0.395,0.115) puts 11.8% on rgb 0.585/0.577/0.621 (H 250 S 0.071). Near-neutral at every reading, faintly cool, S never above 0.081 — normalised to its peak channel that is (0.942, 0.929, 1.000). docking_bay.py's docstring records the fitting itself from this frame: pendant floodlights hanging at regular spacing off the lattice gantry, 'the bay's whole lighting scheme and the first thing that reads'.",
         extrapolated="emission_energy 6.0 and the housing albedo. Energy: matched to materials.py's light_pilaster_strip (6.0), which is a corridor's principal wall light, on the argument that this is the bay's principal light and the fitting is far larger — docking_bay.py builds it as a 1.5 m box against the strip's ~0.1 m tube, so at equal energy this delivers roughly fifteen times the flux, which is the right order for a 42 x 140 m hangar against a 3 m corridor. The visible beam shafts in the frame are haze, not intensity, and were not used to argue it up. Housing 0.62: the geometry is the whole fitting, so it must not read as a hole when unlit; 0.62 is a painted steel lamp body, darker than materials.py's truss_lamp tube at 0.95 because that is glass and this is not. Overturned by any frame showing a dark bay bay with the floods off.",
diff --git a/tools/export_scene.py b/tools/export_scene.py
index 1fbc941..a409681 100755
--- a/tools/export_scene.py
+++ b/tools/export_scene.py
@@ -1522,6 +1522,7 @@ LIGHT_GROUP_PREFIX = "light_"
 # Two tagged spans of the same fitting closer than this are one lamp. 0.9 m
 # spans a pilaster strip's seven bars (0.12 m pitch) without reaching the next
 # pilaster, which the kit puts a portal bay apart.
+UPLIGHT_REL = 0.30
 FIXTURE_MERGE_M = 0.9
 
 # A FITTING IS A CONNECTED BODY, AND A TAGGED SPAN IS NOT ONE. `to_spans` cuts
@@ -1844,6 +1845,27 @@ FIXTURE_LIGHTING = {
     # right here and would be wrong anywhere else: docking_bay.py's BAY_H_M
     # really is 18 m. 35 deg is the top of the measured range and is taken
     # rather than opened further.
+    # THE UPLIGHT COMPONENT OF THE SAME PENDANT -- session 4r. See the
+    # `docking_bay.floodlight` block. An industrial high bay has an open crown
+    # and the structure it hangs from is lit by it; ours did not, and the truss
+    # -- 58% of the module's triangles and the one saturated colour the
+    # reference frame has -- was lit by the flat ambient alone.
+    #
+    # OMNI AND NOT A SPOT, because `fixture_lights` aims every spot in this
+    # table DOWN (`down(c)` or -Y) and an uplight is the one fitting in the
+    # station that does not point at a floor. An omni at the aperture is the
+    # nearest thing this table can express and it is not a fudge: what leaves an
+    # open crown IS roughly hemispherical, and the shade below it occludes the
+    # downward half in the geometry.
+    #
+    # RANGE 8.7 m is derived, not chosen: the aperture sits at y 13.54 in an
+    # 18 m bay whose ceiling crowns at 22.2, so 8.66 m is aperture-to-crown --
+    # the furthest surface it has to reach. `room_reach` then scales it x1.45
+    # to 12.6 m, which is still SHORT of the 13.5 m deck below, so this fitting
+    # cannot add light to the floor and cannot disturb ROOM_EXPOSURE's solve.
+    "bay_uplight": {"kind": "omni", "colour": (0.850, 0.830, 1.000),
+                    "energy_rel": UPLIGHT_REL, "range_m": 8.7,
+                    "shadow": False},
     "bay_lamp": {"kind": "spot", "colour": (0.850, 0.830, 1.000),
                  "energy_rel": 1.00, "range_m": 30.0, "shadow": True,
                  "angle_deg": 35.0},
@@ -5231,9 +5253,24 @@ def _selftest():
         v, t, g, _e = interior_geometry(room)
         return fixture_lights(v, t, g, 3.0 * room_exposure(room), 7.0)
 
+    # DERIVED FROM THE MODULE, NOT PINNED -- the correction the Zocalo line
+    # below already carries, applied to the line above it. `== 39` was 3 floods
+    # x 13 girders and it went red the moment `docking_bay.py` gave the same
+    # fitting its uplight aperture, which is a second BODY of a second tagged
+    # group on the same lamp. What the assertion is FOR is that a span is not a
+    # fitting; that survives, because the expression still multiplies the
+    # module's own two numbers and still counts one light per flood.
+    import docking_bay as _DB                                    # noqa: PLC0415
+    _n_g = max(1, int(_DB.BAY_LEN_M / _DB.GIRDER_PITCH_M)) + 1
+    _want_bay = _DB.LAMPS_PER_BAY_GIRDER * _n_g
     _bay = _lamps("docking_bays")
-    check(len(_bay) == 39,
-          f"the docking bay recovers its three floods a girder ({len(_bay)})")
+    _floods = [x for x in _bay if x["group"] == "bay_lamp"]
+    check(len(_floods) == _want_bay,
+          f"the docking bay recovers its {_DB.LAMPS_PER_BAY_GIRDER} floods on "
+          f"each of {_n_g} girders ({len(_floods)} of {_want_bay})")
+    check(len([x for x in _bay if x["group"] == "bay_uplight"])
+          in (0, _want_bay),
+          "every flood has an uplight aperture, or none of them does")
     # DERIVED FROM THE MODULE, NOT PINNED. This read `== 30` and had been wrong
     # since 27d32d7 (2026-08-02) -- the commit that gave the Zocalo its own
     # footprint and took it from three bays to six. That commit touched
```

Plus, in `station/docking_bay.py` (mine, one line):

```diff
-UPLIGHT_GROUP = "bay_girder"     # -> "bay_uplight" when the patch lands
+UPLIGHT_GROUP = "bay_uplight"
```

Verified together in the worktree: `station/docking_bay.py --selftest` 53/53, and the rig comes
back `Counter({'bay_uplight': 39, 'bay_lamp': 39})` at reach ×1.45, uplight range 12.62 m — short
of the 13.56 m drop to the deck, so the uplight adds nothing to the floor and cannot disturb the
exposure solve. Confirmed: the deck band's luminance is 0.08857 without it and 0.08806 with it.
