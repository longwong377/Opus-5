# Station materials

Godot `StandardMaterial3D` resources in text form, one file each, so they diff and so a
future session can change a colour without an editor GUI. The glTF export carries **POSITION
and NORMAL only** — no UVs, no vertex colours, no material bindings — so everything about how
a surface looks lives here, and anything textured has to be triplanar.

Bound to geometry by `material_rules` in `scenes/station_view.tscn`: a table of mesh-name
fragment → material, longest match wins. Matching is by substring rather than prefix because
the glTF importer decorates names (`cargo_module` comes back as `BabylonStation_cargo_module`).

Check them without rendering. This asserts more than "it parsed": every key in each
`[resource]` block has to be a real property of the class, because Godot **silently drops keys
it does not recognise** and hands back a material sitting at its defaults — which reads as a
plausible surface rather than as an error.

```bash
godot --headless --path godot --script res://scripts/verify_materials.gd
```

## Bound in the exterior scene

| Mesh-name fragment | Material | Reads as |
|---|---|---|
| *(fallback)* | `hull_exterior` | plated warm-neutral grey, mottled |
| `main_truss_spine`, `reactor_spine`, `explosive_disconnect_neck`, `comms_grid_pylon` | `structural_truss` | dark unpainted framework |
| `reactor_cooling_fin` | `radiator` | deep blue matte blades |
| `cargo_module` | `cargo_module` | red-brown containers |
| `cobra_bay` | `hull_banding_red` | red structural banding |
| `heat_exchange_solar_array`, `forward_swept_array`, `space_traffic_prox_array` | `swept_array` | mid-grey collector panels |
| `greeble_nav_light` | `marker_light_white` | warm-white beacon |
| `greeble_hazard_light` | `marker_light_red` | red hazard beacon |

## Not bound yet — interior set

`hull_interior`, `accent_warning`, `emissive_floor` and `emissive_signage` are the palette of
`docs/interior-kit-spec.md`. `station/interior_kit.py` builds the geometry they belong on but
does not export glTF yet, so nothing in the engine references them and **they have been
verified as loading, not as looking right.** Whoever exports the interior kit should render a
corridor and judge them the same way the exterior set was judged.

The two `emissive_*` materials are built exactly like the marker lights, which *are* bound and
*do* read correctly in `renders/engine_view.png` — same `emission_enabled` + energy
construction, higher energy. That is evidence the mechanism works, not that the values are right.

**An emissive material is not a light.** In Forward+ an emissive surface glows but illuminates
nothing around it unless global illumination is on, and the spec is explicit that the deck
channels are *"a light source, not a texture"* and that raising ambient will read as wrong
immediately. So `emissive_floor` and `emissive_signage` each need a real `OmniLight3D` or
`SpotLight3D` alongside them when the interior kit is placed. The material is the visible
fitting; the light is a separate object. Getting a corridor that is lit only by its own floor
channels is an interior-lighting job, and it is not done here.

## Provenance

Every colour is measured off reference, not chosen. The measurements, the two accents that
turned out to be different registers, and the one property that is extrapolated are recorded
in `canon/INVENTIONS.md` under **INV-010**.
