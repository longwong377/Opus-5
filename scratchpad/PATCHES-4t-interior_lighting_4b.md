# interior_lighting_4b, round 2 — what other owners are owed

Everything below is outside `tools/export_scene.py` and was therefore NOT applied.

## 1. CI — one step, and it is cheap (`.github/workflows/validate.yml`)

```yaml
- name: The emission headroom reaches the frame
  continue-on-error: true
  run: python3 tools/export_scene.py --gate-emissive zocalo
```

Two 640x360 interior renders, about 90 s. It exits non-zero on failure and prints
`CANNOT-RUN` and exits non-zero if there is no engine — it never reports success for a
run that did not happen. Its two negative controls are `--control none` and
`--control uncompensated`; both are run in the module comment above `gate_emissive`
with their numbers, so a reviewer can check the gate can fail without spending a render.

## 2. `station/materials.py` — two items, one of them a live hazard

**(a) `light_market_pool` binds a group nothing emits.** The material is titled *"Market
Downlight — the Zocalo's overhead"* and its `source=` carries the whole layer-4
measurement, but `station/zocalo.py` emits no `light_market_pool` group, so the material
has never been on a surface. As of this round the *light* it describes is emitted, from
`FIXTURE_LIGHTING["zoc_downlight"]` with `mount_m = 7.2`. **If a lens group is ever added,
the light must move onto it and `mount_m` must go** — otherwise the room gets its key
twice. Nothing asserts that today; it is finding R4 on the round-2 scorecard.

**(b) `zoc_deck_light` merges two fittings its own source separates.** It binds
`zoc_deck_strip` and `zoc_downlight` at one `emission_energy = 3.5`, and its
`extrapolated=` field already says this is the weak part: *"A lit strip behind a lens and
a lit patch of deck under a downlight are not physically the same fitting, and if a later
pass wants the pool dimmer than the channel it should split them — the fragments are
already separate."* `docs/layer4-lighting/public_social.json` **does** separate them:
`zoc_downlight_overhead` at `energy_rel` 1.00 and `zoc_deck_strip` at 0.25, a factor of
four. The centreline strip being the brightest object in every Zocalo frame is that merge.
Splitting the material and putting the strip at a quarter of the pool's energy is the one
edit that closes the second round-2 craft finding, and it is a one-line change in the file
that owns it.

## 3. `station/zocalo.py` — the reference's saturated practicals have no geometry

`reference/04-sector-red/more zocalo.png` (authority 1) shows domed table lamps with a
saturated green-cyan ring band — measured at the ring's peak rows, sRGB (0.504, 0.728,
0.737), linear normalised (0.437, 0.971, 1.000), against a pale blue-white body at
(0.692, 0.678, 1.000). There is no group for them: the module emits `zoc_table_top`,
`zoc_table_col`, `zoc_table_edge` and `zoc_table_foot` and no lamp. They are the frame's
only saturated accent at table height and the critic's colour note cannot be closed
without them. One per table, on the table, at the measured ring colour.

## 4. `godot/scenes/interior.tscn` — the runtime does not get any of this

`main.gd` and `walk.gd` mount `interior.tscn` and never read a `scene.json`, so
everything here is the RENDER path only. The runtime equivalent of the compensated pair is
`tonemap_exposure = 1.0 / K` with every shipped light energy times K, and of the key light
is real fixtures in the scene. Recorded as a job on INV-880 and still open.

## 5. A trap worth propagating, and it is not about lighting

`--fixture-energy` **defaults to 3.0**, and `build_interior` passes
`args.fixture_energy * room_exposure(room)`. A sweep run with an explicit
`--fixture-energy` and a solved value written back into `BESPOKE_EXPOSURE` as if it were
the whole quantity is off by the ratio of the two. It cost this round three 1280x720
frames. Anyone solving `ROOM_EXPOSURE` or `BESPOKE_EXPOSURE` should solve the PRODUCT and
divide at the end.

And its companion, which is not written down anywhere else in `export_scene.py`: **a level
solved at one resolution is not valid at another.** The same scene at the same settings
measures median 0.1197 at 640x360 and 0.0362 at 1280x720 — x3.3 apart — while at 2.1x the
light the two agree to 1%. The screen-space effects have pixel-sized kernels, so at half
resolution they cover four times the world area, and that matters most when a small bright
population is doing the smearing. Several rows of `BESPOKE_EXPOSURE` were solved on
640x360 gate shots and are not comparable to a 1280x720 judgement frame.
