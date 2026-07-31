# Volume audit — does everything on the outside have a function on the inside?

*Written to answer the owner's question, session 3y: "how much of it's volume will we have filled
out by the end of this? … I want to make sure we're using up the total volume right, like
everything on the outside has a function on the inside … nothing needs to be fake you know like
everything needs an interior it can't be a facade."*

This is an **audit**, not a build. It changes no generator. Every number below is computed from
`station/schema/station.yaml`, `station/schema/radius_profile.json`, `station/interior.py`,
`station/components.py` and `station/directory.py`, or cited to `canon/00-MASTER.md`. Where a
source establishes nothing, it says so and marks the inference.

---

## 0. The answer, before the detail

**No. Twenty-one of the station's twenty-eight enumerated exterior systems are a facade today.**

Three findings, in order of how much they cost:

1. **Only 7 of the 28 `exterior_systems` have an interior that matches them in function *and*
   position.** Of the other 21: **11 have no interior at all**, **5 are addressed hundreds or
   thousands of metres from the geometry the same schema builds**, and **5 have a function
   somewhere in the register but nothing placed against the system**.

2. **The hull is 1.977 km³ and 46.6% of it is modelled as pressurised deck — but 22.6% of the
   hull (0.446 km³) is inside the pressure hull, is not deck, is not open air, is not the core,
   and nothing in the project says what it is.** 92.6% of that is one annulus: the aft hull
   block, the widest structure on the station, straddled by a sector boundary that leaves it
   undecked on both sides.

3. **The volume is not the problem. The addressing is.** 259 km² of walkable floor for 250,000
   people is 880 m² of habitat floor per resident — 12–20× a dense city. The honest reading is
   **not** that the hull should be filled; it is that **the deck model claims floor it should
   not** (45.8 km² of it is outside the hull), and the 118 places sit on 37 distinct z values with
   **27 of their 118 addresses silently clamped** to decks and rings that do not exist.

**A truthful summary: 38.7% of this hull can never be walked in — drum sky, pressure hull, core
bore, the skin the components stand on — and that is correct for a 2.5-million-tonne station.
38.7% is deck. The remaining 22.6% is undescribed and most of it should end up structure too.
The volume does not need filling; it needs stating.** What is *not* correct is that the systems
the show puts on the outside have nothing behind them.

---

## 1. The exterior inventory

`schema["exterior_systems"]` enumerates 28 systems, transcribed from `canon/00-MASTER.md` §2
(aft → fore, from `Exterior map.jpg` and the Contract 5 profile/plan views, authority 3) and §1.3
(the counts table). `schema["components"]` is the buildable subset: **10 specs, 17 emitted mesh
groups, 53,568 triangles, 0.0384 km³ of solid.**

### 1.1 What is built, with measured position and size

Measured by `components.build_all()` then `components.signed_volume()`; `z` is the mesh's own
bounding extent, not the spec's.

| group | kind | n (per `components`) | z0 | z1 | max radius | tris | solid volume |
|---|---|---|---|---|---|---|---|
| `reactor_cooling_fin` | planar_blades | 6 | 1315 | 1655 | 635.1 m | 20,040 | 8,635,035 m³ |
| `heat_exchange_solar_array` | swept_fins | 6 | 2020 | 2537 | 626.6 m | 8,352 | 5,648,206 m³ |
| `comms_grid_pylon` | pylon_pair | 2 | 2305 | 3198 | 1210.9 m | 48 | 12,743,453 m³ |
| `cargo_module` | dorsal_line | 6 | 4906 | 5974 | 377.3 m | 72 | 3,969,389 m³ |
| `docking_port` (+frame) | domes | 2 | 5143 | 5337 | 369.9 m | 1,920 | 1,754,524 m³ |
| `observation_rotunda` (+frame) | domes | 4 | 6202 | 6338 | 372.3 m | 3,840 | 1,339,365 m³ |
| `forward_comms_plate` | plate_array | 1 | 6620 | 7300 | 383.9 m | 1,392 | 1,763,902 m³ |
| `observation_dome` (+frame) | domes | 2 | 7009 | 7231 | 294.5 m | 1,920 | 313,186 m³ |
| `cobra_bay` (+well, markings) | radial_band | 28 | 7026 | 7204 | 298.8 m | 10,416 | 1,884,279 m³ |
| `space_traffic_prox_array` | swept_fins | 4 | 7320 | 7648 | 394.5 m | 5,568 | 302,176 m³ |

### 1.2 What the hull lathe supplies instead of a component

Three `exterior_systems` entries are longitudinal features of the hull itself
(`generate_hull.py` lathes `radius_profile` as a closed surface of revolution grouped by
feature):

| id | z0 | z1 | length | swept envelope |
|---|---|---|---|---|
| `primary_fusion_reactor` | 39 | 331 | 292 m | 0.0299 km³ |
| `generator_torus_housing` | 1095 | 1295 | 200 m | 0.0176 km³ |
| `habitat_cylinder` | 4826 | 6035 | 1209 m | 0.3814 km³ |

### 1.3 What has neither

**Nineteen of the 28 `exterior_systems` have no geometry at all** — not a component, not a
feature:

`core_fuel_housing` · `coolant_manifold` (8) · `reactor_coolant_purge_vent` ·
`fuel_delivery_venting` · `explosive_disconnect_point` · `secondary_power_conduit` ·
`raw_material_storage_bay` (5) · `micro_gravity_maint_bay` (2) · `hazardous_liquid_tank` ·
`inert_gases_tank` (4) · `cargo_bay` (42) · `deep_space_comms_grid` (2, *see below*) ·
`tachyon_transmitter` · `cobra_launch_support_arm` (4) · `sanctuary` (4) ·
`hard_docking_mooring_clamp` · `primary_navigation_beacon` · `forward_deflector_array` ·
`instrument_guidance_array`

Three notes on that list, because all three are transcription rather than absence.
`canon/00-MASTER.md` §2 has **25 numbered items**; items 20 and 25 each name two systems, which
gives 27, and `exterior_systems` holds 28:

- **`deep_space_comms_grid` is built, under a different id** — `comms_grid_pylon`. `validate.py`
  asserts every *component* appears in the hull manifest, and nothing asserts that every
  *exterior system* is either built or explicitly deferred. That is the gate that would have
  caught the other eighteen.
- **`sanctuary` (4) is the 28th entry, and it is not an exterior system.** It is not in §2's
  aft→fore list; it comes from §1.3's counts table, which mixes interior and exterior fittings.
  It is an interior room and it is correctly addressed as one (`sanctuaries`, `sanctuary_blue`,
  `interfaith_chapel`, `alien_worship`).
- **§2 item 16 is "Cargo modules and magnetic attachment points" — the EXTERNAL modules — and
  `exterior_systems` transcribes it as `cargo_bay`, count 42, authority 4.** 42 is §1.3's
  *internal* count (28 rotating + 14 support structure), a different fact from a different table.
  One item of the exterior list was replaced by an interior one, which is exactly why the six
  dorsal modules on the rail have no schema entry and no interior (§2.3).

Conversely, **three built systems are not named in `exterior_systems` at all**:

- **`cargo_module`** — the 6 dorsal modules on the magnetic rail, z 4870–6010. `LOCATIONS.md`
  line 192 is explicit that the 42 internal cargo bays are *"distinct from the six external cargo
  modules on the dorsal rail"*, so `exterior_systems.cargo_bay` (42) is the internal system and
  **the external six have no schema entry at all**.
- **`docking_port`** — the Primary (north) and Service (south) Docking Ports from the Contract 5
  cross-section, z 5143–5337, which `schema.docking` names and `exterior_systems` does not.
- **`forward_comms_plate`** — z 6620–7300, read off `exterior more.jpg` at authority 2.

(The remaining unnamed groups — `cobra_bay_well`, `cobra_beacon_red`, `cobra_marker_white`,
`hazard_stripe_cobra`, `observation_dome_frame`, `observation_rotunda_frame`,
`docking_port_frame` — are material sub-groups of a named component, not systems.)

---

## 2. For each exterior system: what interior it implies, and whether it exists

Matched against `directory.PLACES` **by function**, then by whether the place's declared
footprint overlaps the exterior system's own z extent. Name similarity is not evidence: the
register contains `comms_grid` and the schema contains `comms_grid_pylon`, and they are 5,148 m
apart.

**Tally, over the 28 `exterior_systems` entries: 7 matched · 5 addressed in the wrong place ·
5 ambiguous · 11 unmatched.** (§2.2's table counts *places*, of which there are 7 mismatched
across those 5 systems, because two observation domes share one component.)

### 2.1 Matched — an interior exists, its function fits, and it is where the exterior is

| exterior system | implied interior | the register's answer | verdict |
|---|---|---|---|
| `primary_fusion_reactor` z 39–331 | reactor hall, control room, radiation boundary, aux cores, APUs | `fusion_core` (yellow r0 d0, z 400, footprint 360°×800 m → spans z 0–800), `power_generation`, interacts `reactor_console`+`blast_door` | **MATCHED, thin.** One room, one function. `LIFE-SUPPORT-AND-INDUSTRY.md` §1.1 names *fusion isotope slush tanks, auxiliary fusion cores, auxiliary power units (4)* from the Security Manual and none of them is addressed |
| `explosive_disconnect_point` z 2680 | arming station, severed-services gallery, structural bulkhead | `disconnect_point` (yellow r0 d0, z 2680, 30°×60 m), `structure`+`emergency`, one interact | **MATCHED as a label.** There is no room; the only interact is `blast_door` |
| `raw_material_storage_bay` (5) | bulk store, handling deck, feed to the furnaces | `raw_material` (grey r0 **d75**, z 3618), `storage` | **MATCHED, but see §3.4** — deck 75 does not exist and resolves to deck 22 |
| `habitat_cylinder` z 4826–6035 | the Garden, its sub-floor stack, spokes, end caps, trams | 13 places: `the_garden`, `garden_town`, `zen_garden`, `garden_terrace`, `water_rec`, `subfloor_stack`, `drum_endcaps`, `drum_spokes`, `radial_tubes`, `ground_tram`, `drum_tram`, `earharts`, `fresh_air` | **MATCHED, richly.** This is the one exterior system whose interior is genuinely built out |
| `hazardous_liquid_tank` | tank farm, valve gallery, spill containment | `hazard_tanks` (yellow r0 d6, z 1400, 40°×300 m), `hazardous_storage`+`atmosphere_feedstock`, interacts `valve`/`tank_gauge`/`blast_door` | **MATCHED** |
| `inert_gases_tank` (4) | as above; feedstock for the six-atmosphere system | same row | **MATCHED** |
| `sanctuary` (4) | worship spaces | `sanctuaries`, `sanctuary_blue`, `interfaith_chapel`, `alien_worship` | **MATCHED** (and it is not an exterior system — §1.3) |

### 2.2 Addressed in the wrong place — the register and the generator disagree

**This is the hard-rule-4 violation and it is the sharpest finding in the audit.** Nine places
declare `module="components"`. Seven of them are addressed at a `z` the schema does not build
that component at. Nothing checks this: `directory.collisions()` compares places against *other
places*, and no gate compares a place against the geometry its own module emits.

| place | register z / sector | built at z (mid) | Δ | consequence |
|---|---|---|---|---|
| `comms_grid` | 7900, **blue** | `comms_grid_pylon` 2305–3198 (2752), **yellow** | **5,148 m** | The deep space comms array is addressed at the opposite end of the station from the pylons that carry it. Its `interacts` tuple is **empty** |
| `obs_rotundas` | 4200, green | `observation_rotunda` 6208–6332 (6270) | **2,070 m** | Four rotundas built on the Red/Green boundary, addressed 2 km aft |
| `obs_dome_1`, `obs_dome_2` | 7960, blue | `observation_dome` 7014–7226 (7120) | **840 m** | **`cnc` declares `within="obs_dome_1"`.** Command & Control — the most-seen room in the show — is addressed 840 m from the dome it is declared to be inside |
| `power_transfer` | 900, yellow | `reactor_cooling_fin` 1315–1655 (1485) | **585 m** | The row is named "Power transfer core + 12 cooling fins" and the fins are 585 m fore of it |
| `proximity_arrays` | 7900, blue | `space_traffic_prox_array` 7320–7648 (7484) | **416 m** | Footprints (30°×60 m vs the array's 328 m span) do not overlap at all |
| `cobra_bays` | 6900, blue | `cobra_bay` 7026–7204 (7115) | **215 m** | The register's footprint spans z 6840–6960; the bays start at 7026. **66 m of clear air between the room and its own doors** |

Two more carry `module="components"` and **no component is built for them**:
`mooring_clamps` (`hard_docking_mooring_clamp`) and `nav_beacon`
(`primary_navigation_beacon`).

### 2.3 Ambiguous — a function exists somewhere, but nothing is placed against the system

| exterior system | what exists | why it is not a match |
|---|---|---|
| `coolant_manifold` (8) | `power_transfer` carries the station's **only** `cooling` function (yellow, z 900, spans 750–1050) | §2 orders the manifolds second, aft of the reactor (z ≲ 150). No pump room, no manifold hall, no reservoir is addressed anywhere |
| `reactor_cooling_fin` (12) | same row | The blades are built at z 1315–1655; the row's footprint ends at 1050. **And the counts disagree inside one file**: `exterior_systems` says 12, `components` says 6. C-007 is RESOLVED — *six coplanar blades* — and `LIFE-SUPPORT-AND-INDUSTRY.md` §1.1 warns the twelve small rosette fins are a **different system**. That different system is built nowhere |
| `secondary_power_conduit` | 5 places carry `power_distribution` (`plant_zone`, `alpha_substation`, `primary_breaker`, `power_transfer`, `mainstage_node`) | `interior_topology.sector_facilities.green` lists `power_conduits`; no place implements it. A conduit is a *run* between two places and the register has no way to express one |
| `micro_gravity_maint_bay` (2) | `micro_g_bays` (grey r0 **d80**) and `zerog_maint` (grey r0 **d70**), both `microgravity_handling` | **Both resolve to 1.409 g.** A micro-gravity maintenance bay at 1.4 g is the most self-contradictory address in the register. See §3.4 |
| `cargo_bay` (42) / `cargo_module` (6) | `cargo_bays` (blue r1 d3, z 7000, spans 6900–7100) and `spinal_cargo` (yellow, z 2200, spans 2000–2400) | The **six external cargo modules are built at z 4870–6010, on the dorsal rail over the drum**, and there is no cargo place anywhere in Green. 1,140 m of magnetic cargo rail with no hold, no handling deck and no manifest office behind it |

### 2.4 Unmatched — no interior exists

| exterior system | implied interior | nearest thing in the register |
|---|---|---|
| `core_fuel_housing` (aft terminus, z 0–39) | reactor fuel bunkerage, transfer gallery, fuelling control, radiation boundary | `fuel_stores` is **ship** fuel at the docks, z 7000 — 7 km away. `fusion_core`'s footprint covers the z but declares only `power_generation` |
| `reactor_coolant_purge_vent` | purge control, vent gallery, interlock | nothing. No place carries a purge, vent or interlock function |
| `fuel_delivery_venting` | fuel transfer gallery, emergency vent control | nothing |
| `generator_torus_housing` (z 1095–1295, **0.0176 km³**) | generator hall, switchgear, turbine/MHD gallery | **zero addressed places in the feature** |
| `heat_exchange_solar_array` (12, z 2020–2537) | heat-exchanger hall, coolant loop, emergency-power switchover | nothing. **No place on the station carries a thermal or heat-rejection function**, for a system `LIFE-SUPPORT-AND-INDUSTRY.md` §1.2 derives ~1.9 GW of rejected heat through |
| `tachyon_transmitter` | transmitter hall, waveguide run, transmit control | nothing. No geometry either |
| `cobra_launch_support_arm` (4) | access crawlway, arm actuator bay | nothing |
| `hard_docking_mooring_clamp` | clamp control, umbilical gallery | `mooring_clamps` is a label with one interact and no geometry |
| `primary_navigation_beacon` | beacon equipment bay, service access | `nav_beacon` is a label with **no interacts** and no geometry |
| `forward_deflector_array` | deflector control, emitter gallery, power feed | nothing |
| `instrument_guidance_array` | instrument bay, calibration room | nothing |

---

## 3. The volume budget — where 1.977 km³ actually goes

### 3.1 The envelope

Integrated as a solid of revolution over all 1,978 `radius_profile` samples (frustum rule, so it
is exact for a linear-interpolated profile):

| | value |
|---|---|
| **swept envelope volume** | **1.9765 km³** |
| core hull (protrusions stripped by `interior.core_hull_profile`) | 1.9417 km³ (98.2%) |
| protrusion band (envelope − core hull) | 0.0348 km³ |
| exterior components, measured solid | 0.0384 km³ |

The last two agreeing to 10% is a real cross-check: the profile traces the *outline*, so the
band it leaves above the core hull should be about the size of the hardware standing in it, and
it is.

### 3.2 The budget

Every point inside the lathed envelope classified by what the model says is there. Integrated at
1,977 z-slices × 400 radial shells; the total reproduces the analytic integral to 0.005%.

| category | km³ | % of hull | what it is |
|---|---|---|---|
| **`deck_habitat`** | **0.6373** | **32.2%** | modelled pressurised deck at ≤ 1.25 g |
| **`drum_open_air`** | **0.6095** | **30.8%** | the hollow of the habitat drum. **Volume nobody walks in, by design and correctly** |
| **`unmodelled_interior`** | **0.4458** | **22.6%** | inside the pressure hull, not deck, not open air, not core. **Nothing in the project describes it** |
| `deck_plant` | 0.1196 | 6.1% | deck above 1.25 g — Grey's 34 plant decks |
| `hull_skin` | 0.0742 | 3.8% | `HULL_SKIN_M = 6.0` pressure hull, frames and services |
| `core_column` | 0.0470 | 2.4% | the axis: power core and core shuttle |
| `protrusion_band` | 0.0347 | 1.8% | the envelope above the core hull — where the components live |
| `deck_partial` | 0.0083 | 0.4% | the inboard sliver of decks whose floor is outside the hull |

That is a true partition — the eight rows sum to 1.9764 km³. Rolled up three ways:

| | km³ | % of hull |
|---|---|---|
| **deck inside the pressure hull** | **0.7652** | **38.7%** |
| **never walkable by construction** (drum air + hull skin + core bore + protrusion band) | **0.7654** | **38.7%** |
| **undescribed** | **0.4458** | **22.6%** |

**Read honestly:**

- **Pressurised deck is 0.765 km³, 38.7% of the hull, not 46.6%.** The 0.922 km³ figure is the
  *modelled* stack; **0.1632 km³ of it — 17.7% — is projected where the hull is too narrow to
  contain it**, because `decks_in_ring()` extrudes a constant-radius stack across a sector's whole
  z band and the hull tapers. Per sector the fit is Yellow 69.4%, Blue 74.7%, Red 77.6%, Green
  90.6%, Grey 93.7%. This is the radial form of the same defect `tools/cutaway.py` found
  longitudinally in session 3x ("14 of 118 locations are addressed OUTSIDE THE HULL").
- **Walkable floor is 259.0 km² modelled, 213.2 km² fitted.**

  | | habitat | plant | total | habitat m²/resident |
  |---|---|---|---|---|
  | modelled | 220.2 km² | 38.8 km² | 259.0 km² | **880.6** |
  | fitted inside the hull | 179.5 km² | 33.7 km² | 213.2 km² | **717.9** |

  Either figure is 12–20× what a dense city gives a person, so **the number is too big, not too
  small**, and no part of this audit's recommendation is "add floor".
- **38.7% of this hull can never be walked in and that is correct** — it is drum sky, pressure
  hull, the core bore and the skin the components stand on. For a 2.5-million-tonne station that
  is the right answer and it should be *stated*, not filled.
- **Even if every cubic metre of the undescribed 22.6% became deck, the ceiling would be 61.3%**,
  and it should not: most of it is the deep frame carrying a 1.7 g load path through the widest
  section of the station.

### 3.3 The 0.446 km³ nobody has described — and it is two structures

By radial position:

| where | km³ | share |
|---|---|---|
| green, **outboard of the outermost deck** | 0.2770 | 62.1% |
| yellow, **outboard of the outermost deck** | 0.1360 | 30.5% |
| ring gaps inside the stacks (all sectors) | 0.0226 | 5.1% |
| grey / red / blue, outboard | 0.0062 | 1.4% |
| inboard of the innermost deck, around the core | 0.0027 | 0.6% |

By longitudinal feature — which says *what* it is:

| feature | z | km³ | share |
|---|---|---|---|
| **`aft_hull_block`** | 3107–4207 | **0.2785** | **62.5%** |
| **`bearing_neck`** | 4207–4826 | **0.1084** | **24.3%** |
| `red_section` | 6035–6465 | 0.0176 | 4.0% |
| everything else (12 features) | — | 0.0413 | 9.2% |

**86.8% of it is two structures, and the cause is a boundary, not an omission.**

`aft_hull_block` is z 3107–4207, up to **480.3 m** of radius — the widest structure on the
station, **0.7163 km³** of envelope, 36.2% of the hull on its own. Grey's band (3397–3839, 442 m)
decks it out to 471.2 m and does so properly, leaving only 0.0070 km³. The other 658 m of it
falls in **Yellow** (3107–3397, 0.1273 km³ left over) and **Green** (3839–4207, 0.1442 km³),
whose principal shells are 161.4 m and 314.3 m — so their deck stacks stop 130–310 m short of a
hull that is really there. `bearing_neck` (4207–4826, hull 401–474 m) is entirely inside Green's
band and Green's stack ends at 310.7 m, so 619 m of 400 m-radius hull has nothing in its outer
90–160 m.

That is the sector-band / longitudinal-feature mismatch made physical:
`sectors.extents_m` (Security Manual bands) and `longitudinal.features` (Miller's drawing) cut
the station at different places, and nothing reconciles them. It shows up twice more:

- **`red_section` (z 6035–6465, 430 m, 0.1498 km³) holds ZERO addressed places.** The sector
  named `red` runs 6425–6794, so the Zocalo at z 6600 is in the `forward_taper` cone, not in the
  hull section named for it. Miller's own strongest cross-check (drawn and table lengths agree to
  3.5%) describes 430 m of the second-widest pressurised hull on the station and the register puts
  nothing in it.
- **`drum_open_air` is over-claimed.** The model applies the drum's hollow structure across the
  whole `green` band (2,586 m); the `habitat_cylinder` feature is 1,209 m. Open air over the
  habitat cylinder alone is **0.2846 km³**; the model reports 0.6095 km³. The extra 0.325 km³ is
  hollow claimed through the aft hull block and the bearing neck, which the profile says are
  solid sections 411–478 m in radius.

### 3.4 Six more things the deck model is doing that a reader should know

1. **27 of 118 addresses are silently clamped.** `gravity_of()` and every consumer resolve
   `decks[min(place["deck"], len(decks) - 1)]`. **Twelve Grey places all land on the same deck**
   — floor radius 392.05 m, 1.409 g: `alpha_substation` (d40), `primary_breaker` (d42),
   `fabrication` (d50), `maintenance` (d55), `research_labs` (d60), `gravity_torus` (d65),
   `zerog_maint` (d70), `atmos_monitor` (d30), `raw_material` (d75), `micro_g_bays` (d80),
   `thieves_guild` (d24), `welded_shut` (d26). Three Yellow places clamp to deck 6
   (`rotation_drivers` d8, `core_shuttle` d30, `shuttle_car` d30). Twelve Green places clamp
   ring 1 → ring 0 (the whole Garden, both trams, the spokes, the end caps).
   **`collisions()` compares the declared indices, so it cannot see any of this** — the same
   class of defect as an assertion that cannot fail.
2. **The Garden's addressed floor is 281.9 m, not the canon 278.3 m.** The drum's sub-floor stack
   grows outward from 278.3 and deck 0's floor is one pitch out. 3.6 m, but it is the one radius
   the entire rotation rate was solved from.
3. **20 of 118 places share z = 3618.0** — every Grey location. Combined with (1), twelve of
   them are one address.
4. **The register uses 37 distinct z values for 118 places.** 8 of the 118 sit aft of z = 3107,
   i.e. in the entire structural aft third of the station.
5. **22 places are addressed inside `forward_deflector_spike` (z 7286–8047)**, which
   `materials.py` explicitly excludes from the lit-window material because *"the truss spine, the
   reactor and the deflector spike have nobody in them and stay dark"*. C&C, the war room, the
   admin complex, both observation domes, the comms grid, the proximity arrays and the nav beacon
   are all in it. The exterior says that volume is empty; the register says it holds 22 places.
6. **`directory._arc_overlap` is blind to a 360° footprint, and four places have one.**
   `norm(0 - 360/2)` and `norm(0 + 360/2)` both give 180, so a full circle collapses to a
   zero-width arc at 180° and the test returns True only if the *other* place's arc happens to
   contain 180°. Verified: `_arc_overlap(20, 60, 0, 360) → False`, `_arc_overlap(0, 360, 180, 10)
   → True`. The affected places are `docking_bays`, `plant_zone`, `fusion_core` and `cobra_bays`,
   all at angle 0.0. **`collisions()` returns `[]` today and misses five real same-deck z
   overlaps**: `docking_bays` against `bay_elevators`, `lowg_bays`, `plantroom_bay` and
   `vorlon_berth`, and `fusion_core` against `power_transfer`. Four of the five are probably
   legitimate nesting that should declare `within=`; the point is that **the gate cannot tell,
   and cannot fail.** Fix: clamp `span` to `< 360` before normalising, or special-case a full
   circle as "overlaps everything".

### 3.5 The volume that is genuinely, correctly empty — say so

The 38.7% "never walkable" roll-up in §3.2, itemised:

| region | km³ | % of hull | why it stays empty |
|---|---|---|---|
| drum open air | 0.6095 | 30.8% | it is the sky. Authority 1 (`Babylon_5_2-22_34b.jpg`). **Over-claimed** — see §3.3; over the `habitat_cylinder` feature alone it is 0.2846 km³ and the other 0.3249 km³ is hollow claimed through solid hull |
| hull skin | 0.0742 | 3.8% | `HULL_SKIN_M = 6.0` — pressure hull, frames, services |
| core column | 0.0470 | 2.4% | power core and core shuttle bore |
| protrusion band | 0.0347 | 1.8% | the shell the components stand on |

Two regions cut across the partition and are worth stating separately, because they are volume
the envelope integral counts and the source says is not enclosed at all:

- **0.1492 km³ (7.6%) is lathed over open truss.** `reactor_spine` and `main_truss_spine` are
  `kind: truss` in the schema — an open lattice carrying, per `00-MASTER.md` §1.3, three
  ionization vane support rings and six vanes. **`generate_hull.py` lathes them as closed drums
  of 85 m and 164 m radius**, so the integral counts vacuum between girders as volume, and the
  deck model puts 0.115 km³ of pressurised deck inside them.
- **0.0825 km³ (4.2%) is the `forward_deflector_spike`**, which `materials.py` already excludes
  from the inhabited-window material and the register fills with 22 places (§3.4 item 5).

---

## 4. The missing interiors, ranked

Ranked by (a) the envelope volume the interior would make legible and (b) how likely a player is
to reach it. **Every row below has been validated**: its floor radius fits inside
`core_hull_profile(z) − HULL_SKIN_M` **across the whole footprint span**, its ring and deck
indices exist (no clamping), and it collides with no existing place under
`directory.collisions()`'s own arc/z test. Areas are `interior.arc_length(floor_r, deg) × z_m`;
volume assumes 3.0 m clear under the 3.6 m pitch.

Copy the rows into `PLACES` as-is. `auth=5` throughout — these are extrapolations under hard
rule 1 and each needs an `INVENTIONS.md` entry before it is built.

| # | interior | explains | floor r | g | area | reach |
|---|---|---|---|---|---|---|
| 1 | cargo transfer deck | the 6 dorsal modules, z 4870–6010, **0.3601 km³** | 299.9 m | 1.078 | 141,325 m² | **high** — under the Garden, on the drum sub-floor |
| 2 | heat exchanger hall | 12 arrays, ~1.9 GW rejected, `main_truss_spine` **0.1141 km³** | 144.7 m | 0.520 | 60,591 m² | medium |
| 3 | coolant gallery | 8 manifolds + fin roots, `reactor_spine` **0.0150 km³** | 48.3 m | 0.173 | 37,911 m² | medium |
| 4 | reactor hall | `primary_fusion_reactor` **0.0299 km³**, zero places | 155.4 m | 0.559 | 19,534 m² | medium |
| 5 | fuel bunkerage | `core_fuel_housing`, the aft terminus | 148.2 m | 0.533 | 34,154 m² | low |
| 6 | generator hall | `generator_torus_housing` **0.0176 km³**, zero places | 113.1 m | 0.406 | 21,313 m² | low |
| 7 | mooring gallery | `hard_docking_mooring_clamp` | 204.3 m | 0.734 | 4,280 m² | **high** — beside the docking bays |
| 8 | EVA lock, Blue | 630 EVA-rated staff (`FACTIONS.md`) with nowhere to suit up | 207.9 m | 0.747 | 1,089 m² | **high** |
| 9 | comms operations | `deep_space_comms_grid`, at the pylon root as built | 109.5 m | 0.393 | 4,585 m² | low |
| 10 | gunnery control | the S2 defence grid — see §5 | 159.1 m | 0.572 | 1,555 m² | **high** |
| 11 | deflector control | `forward_deflector_array` / `instrument_guidance_array` | 193.6 m | 0.696 | 1,892 m² | medium |
| 12 | tachyon transmitter room | `tachyon_transmitter` | 105.9 m | 0.380 | 2,365 m² | low |
| 13 | micro-g bay, re-addressed | fixes `micro_g_bays` at 1.409 g | 33.9 m | **0.122** | 2,837 m² | medium |
| 14 | raw material handling deck | un-clamps `raw_material` off Grey deck 22 | 372.0 m | 1.337 | 24,933 m² | medium |

### 4.1 The rows

```python
    _P("cargo_transfer_deck", "Cargo transfer deck", "green", 0, 5, 90.0, 5400.0,
       (30.0, 900.0), auth=5,
       functions=("cargo_handling", "storage", "manifest"),
       interacts=("cargo_crane", "container", "manifest_terminal", "bay_door",
                  "magnetic_clamp"),
       adjacent=("subfloor_stack",),
       note="Under the six dorsal cargo modules (schema components.cargo_module, "
            "z 4870-6010). 1,140 m of magnetic rail outside with nothing behind "
            "it. INV-xxx."),
    _P("heat_exchanger_hall", "Heat exchanger hall", "yellow", 0, 3, 60.0, 2250.0,
       (60.0, 400.0), auth=5,
       functions=("heat_rejection", "coolant_loop", "emergency_power"),
       interacts=("valve", "pump_control", "tank_gauge", "catwalk", "console"),
       note="Behind the 12 heat exchange / emergency solar arrays, z 2020-2537. "
            "~1.9 GW of rejected heat (LIFE-SUPPORT-AND-INDUSTRY.md L-01) and no "
            "thermal function existed anywhere. INV-xxx."),
    _P("coolant_gallery", "Coolant manifold gallery", "yellow", 3, 3, 120.0, 700.0,
       (90.0, 500.0), auth=5,
       functions=("cooling", "coolant_transfer", "maintenance_access"),
       interacts=("valve", "pump_control", "tank_gauge", "catwalk",
                  "service_ladder"),
       adjacent=("reactor_hall",),
       note="The 8 coolant manifolds and the radiator fin roots. 0.173 g on the "
            "spine -- a crawlway, not a corridor. INV-xxx."),
    _P("reactor_hall", "Primary reactor hall and control room", "yellow", 0, 0,
       20.0, 240.0, (60.0, 120.0), auth=5,
       functions=("power_generation", "reactor_control", "radiation_boundary"),
       interacts=("reactor_console", "blast_door", "breaker_lever",
                  "radiation_monitor", "catwalk"),
       adjacent=("fuel_bunkerage", "coolant_gallery"), within="fusion_core",
       note="primary_fusion_reactor is z 39-331 and held zero addressed places. "
            "Security Manual also names aux fusion cores and 4 APUs, unaddressed. "
            "INV-xxx."),
    _P("fuel_bunkerage", "Core fuel housing and transfer gallery", "yellow", 0, 2,
       200.0, 150.0, (60.0, 220.0), auth=5,
       functions=("fuel_storage", "hazardous_storage", "fuel_transfer"),
       interacts=("valve", "tank_gauge", "blast_door", "cargo_crane"),
       adjacent=("reactor_hall",), within="fusion_core",
       note="00-MASTER.md §2 item 1, the aft terminus. `fuel_stores` is SHIP fuel "
            "at the docks 7 km fore. INV-xxx."),
    _P("generator_hall", "Generator torus hall", "yellow", 1, 4, 250.0, 1195.0,
       (60.0, 180.0), auth=5,
       functions=("power_generation", "power_distribution"),
       interacts=("console", "breaker_lever", "catwalk", "blast_door"),
       note="generator_torus_housing z 1095-1295, 0.0176 km^3, zero places. "
            "INV-xxx."),
    _P("mooring_gallery", "Mooring clamp gallery", "blue", 0, 2, 180.0, 7250.0,
       (20.0, 60.0), auth=5,
       functions=("ship_mooring", "umbilical_service"),
       interacts=("docking_clamp", "console", "airlock_door", "handhold"),
       adjacent=("docking_bays", "mooring_clamps"),
       note="Behind 00-MASTER.md §2 item 23. `mooring_clamps` is a label with one "
            "interact and no geometry. INV-xxx."),
    _P("eva_lock_blue", "EVA airlock and suit room, Blue", "blue", 0, 1, 100.0,
       7250.0, (10.0, 30.0), auth=5,
       functions=("eva_egress", "suit_service"),
       interacts=("airlock_door", "locker", "handhold", "console",
                  "atmosphere_status_lamp"),
       adjacent=("docking_bays",),
       note="FACTIONS.md rosters 630 in 'maintenance, repair, EVA' and the station "
            "has no EVA lock, inside or out. INV-xxx."),
    _P("comms_operations", "Deep space comms operations", "yellow", 1, 5, 300.0,
       2800.0, (24.0, 100.0), auth=5,
       functions=("communications", "signal_ops"),
       interacts=("console", "monitor_wall", "comms_channel", "babcom_terminal"),
       adjacent=("tachyon_room",),
       note="At the root of comms_grid_pylon as BUILT (z 2515-2988). The register's "
            "`comms_grid` is at z 7900, 5,148 m away, with an empty interacts "
            "tuple. Position contested -- see §6. INV-xxx."),
    _P("gunnery_control", "Defence grid fire control", "blue", 1, 4, 340.0, 7050.0,
       (14.0, 40.0), auth=5,
       functions=("defence_command", "fire_control"),
       interacts=("console", "tactical_display", "blast_door"),
       adjacent=("cnc", "war_room"),
       note="00-MASTER.md §1 lists anti-fighter pulse cannons at AUTHORITY 1 and "
            "the era lock is 'defence grid installed'. Neither the hull nor the "
            "register has one. INV-xxx."),
    _P("deflector_control", "Forward deflector and guidance control", "blue", 0, 5,
       20.0, 7550.0, (14.0, 40.0), auth=5,
       functions=("navigation", "sensors", "deflector_control"),
       interacts=("console", "monitor_wall", "service_ladder"),
       adjacent=("nav_beacon",),
       note="00-MASTER.md §2 items 24-25, the fore terminus. Nothing addressed. "
            "INV-xxx."),
    _P("tachyon_room", "Tachyon transmitter hall", "yellow", 1, 6, 330.0, 2800.0,
       (16.0, 80.0), auth=5,
       functions=("communications", "signal_ops"),
       interacts=("console", "blast_door", "catwalk"),
       adjacent=("comms_operations",),
       note="00-MASTER.md §2 item 18. No geometry and no interior. INV-xxx."),
```

Two of the fourteen are **corrections to existing rows rather than new rows** — report only, the
edit belongs to whoever owns `directory.py`:

- `micro_g_bays`: `"grey", 0, 80` → `"yellow", 3, 7, 350.0, 3300.0, (40.0, 120.0)`. Grey deck 80
  does not exist and resolves to 1.409 g. Yellow ring 3 deck 7 is 33.9 m and **0.122 g** — the
  lowest-gravity deck the model contains. **True micro-gravity is not available at all**: the
  core ring carries no decks (`decks_in_ring` returns `[]` for `kind != "deck_stack"`), so the
  axis is a bore with nothing in it. That is a modelling gap, not an address error.
- `raw_material`: `"grey", 0, 75` → `"grey", 1, 4` (floor 372.0 m, 1.337 g). Same fix pattern for
  the other eleven clamped Grey rows; **all twelve currently resolve to one deck.**

---

## 5. What the exterior itself is missing

### 5.1 Authority-1 canon that is on neither the hull nor the register

- **The defence grid.** `canon/00-MASTER.md` §1: *"Defences | Anti-fighter pulse cannons; two
  Starfury squadrons | authority 1 | Show (S2 defence grid)"*, and the era lock is stated as
  *"defence grid installed"* in `00-MASTER.md`, `LOCATIONS.md`, `FACTIONS.md` and
  `TRAFFIC-AND-CUSTOMS.md`. **Grepped: `pulse cannon` and `defence grid` appear in no `.py`, no
  `.yaml` and in no `exterior_systems` entry.** There are no emplacements outside and no gunnery
  control inside; `cnc` and `war_room` declare `defence_command` and command nothing. This is the
  single largest canon-vs-build gap in the exterior and it is authority 1.
- **Docking bay apertures.** `generate_hull.py::build()` lathes a closed surface of revolution
  and caps both ends; there is no subtraction anywhere in the file. The cobra bays get a modelled
  recess (`cobra_bay_well`, 2,352 tris) — **the 24 docking bays get nothing.** The interior
  (`docking_bay.py`, built off `dock.webp` authority 1) has a mouth *"with the far side of the
  station visible beyond it"* and the hull it opens through is solid. **This is the owner's rule
  running the other way: an interior with no exterior.**
- **Ionization vane support rings (3) and fusion reactor ionization vanes (6).**
  `00-MASTER.md` §1.3 counts both. `schema.longitudinal.features[main_truss_spine].contains`
  names both. **No builder exists** — grep for `ionization`/`vane` in `station/` returns only
  Starfury geometry. 1,385 m of spine that the source says carries six vanes on three rings is
  lathed as a bare 164 m cylinder.

### 5.2 Systems a 250,000-person station must have, marked as inference

Authority 5 throughout. The show establishes none of these directly; each is derived from a
number the project already holds.

- **EVA egress.** `FACTIONS.md`'s EarthForce branch table (line 196) allots *"Maintenance,
  repair, EVA | 630"* of the 6,500 crew. 630 people whose job includes vacuum work, and there is
  no airlock on 8,047 m of hull and none in the register — `airlock_door` appears in exactly two
  places' `interacts`, both of them Alien Sector atmosphere locks. Overturned by any frame
  showing where B5's EVA crews suit up.
- **Atmosphere lock boundaries.** `LIFE-SUPPORT-AND-INDUSTRY.md` §8 item 4 already says it:
  *"Six atmospheres needs locks … nothing in the interior kit has one yet."* Six independently
  conditioned volumes require locks on the hull too, for suit charging and for venting.
- **Waste heat from the habitat, separate from the reactor.** The 12 heat exchange arrays are on
  the *spine*, aft of the disconnect point. The drum's ~600 MW of lighting load
  (`LIFE-SUPPORT-AND-INDUSTRY.md` L-01) is 3,000 m forward of them and there is no radiator on
  the rotating section. Either the coolant crosses the rotating bearing — which is a real
  engineering feature the schema does not model — or the drum has its own rejection surface and
  it is missing. **Neither is established; this is a live question, not a defect.**
- **Escape and evacuation.** Not raised because the show establishes nothing about it. Recording
  the gap rather than inventing a lifeboat ring.

### 5.3 A consistency observation, offered without a ruling

`comms_grid_pylon` is built at z 2305–3198. The `explosive_disconnect_point` is at z 2680, and
the schema's own note reads *"everything aft of here detaches as one assembly."* **The deep space
communications array straddles the jettison boundary by 375 m aft and 518 m fore.** Jettisoning
the reactor would tear the station's long-range comms in half. That may be intentional in the
source and it may be a placement artefact; nothing held decides it.

---

## 6. What could not be established

- **Where the deep space communications grid actually is.** Three sources give three answers.
  (a) `canon/00-MASTER.md` §2 orders it item 17, *after* the cargo modules — so forward of
  z 5974. (b) `schema.components.comms_grid_pylon` puts it at z 2515–2988, derived from a
  radius-profile excess zone. (c) Miller's own table gives *"width at communications grid =
  893.2 m"*, i.e. hull radius 446.6 m, and the envelope crosses 446.6 m at **z 3472–3549** and
  **z 4339–4437** and nowhere else. The register adds a fourth at z 7900. **Not resolved here.**
  One frame showing the pylons against a recognisable hull section would close it.
- **Whether the 12 reactor cooling fins of `00-MASTER.md` §1.3 exist as a separate system.**
  C-007 is RESOLVED for the *six coplanar blades*. `LIFE-SUPPORT-AND-INDUSTRY.md` §1.1 insists
  the twelve fins on the Yellow rosette are a different, reactor-adjacent system. If it is right,
  twelve fins are missing from the hull. If it is wrong, `exterior_systems` carries a duplicate.
  Nothing held decides it.
- **Which sector boundary is correct.** §3.3's 0.413 km³ hole exists because `sectors.extents_m`
  and `longitudinal.features` cut the station differently. **C-003 is OPEN and BLOCKING**, so
  this audit does not propose a re-cut. Per `CLAUDE.md` §5 the *label* is blocked and the
  *building* is not: the aft hull block can be decked out under whatever name, and named later.
- **Deck and ring counts.** **C-004 is OPEN and BLOCKING** on level numbering. The clamping in
  §3.4 is not caused by C-004 — Grey deck 80 does not exist under any numbering — but the fix for
  it needs a convention C-004 has not supplied.
- **Any absolute size for the missing interiors.** No source gives a room dimension for a reactor
  hall, a coolant gallery or a heat exchanger hall. §4's footprints are chosen to fit the hull at
  their z and to carry the plant that is derived, not measured from anything.

---

## 7. How to reproduce

Nothing here is stored; all of it is computed. In order:

| quantity | how |
|---|---|
| envelope / core-hull / per-feature volume | frustum integral of `radius_profile["profile"]`, and of `interior.core_hull_profile(profile)` |
| deck volume, floor area, use split | `interior.ring_radii` → `interior.decks_in_ring` per sector, annulus × sector band length |
| the fit test | compare each deck's `floor_r_m` against `core_hull_profile(z) − interior.HULL_SKIN_M` at every z sample in the band |
| the budget table | classify every (z, r) shell: deck / open / core / skin / protrusion / unmodelled |
| component position and size | `components.build_all(schema["components"], profile)` then `components.signed_volume` |
| the z-mismatch table | compare `directory.PLACES[*]["z_m"]` against the bounding z of the group its `module` builds |
| clamping | `min(place["deck"], len(decks) - 1)` vs `place["deck"]`, per place |
| candidate row validation | ring/deck exist unclamped; `floor_r_m ≤ min(core_hull) − HULL_SKIN_M` over the footprint span; `directory._arc_overlap` + z overlap against all 118 |

### 7.1 The three gates this audit says are missing

**`python3 station/directory.py` passes 747/747 today, and `collisions()` returns `[]`.** That is
the evidence these gates are needed rather than an opinion: every defect in §2.2, §3.3 and §3.4
is present in a register that is fully green. Each gate below can fail on the content that exists
right now, which is the test `CLAUDE.md` sets for whether an exit criterion measures the right
thing.

1. **Exterior/interior correspondence.** *Every `exterior_systems` entry is either built, or
   addressed by a place whose function matches, or deferred with a reason — and every place whose
   `module` names a component is addressed within that component's own z extent.*
   **Fails today on 21 of 28 systems and 7 of 9 component-backed places.** This is hard rule 4
   made checkable; nothing in the repository currently compares the register to the generator.
2. **Address resolvability.** *No place's ring or deck index may be clamped.*
   **Fails today on 27 of 118.** One line: assert `place["deck"] < len(decks)` and
   `place["ring"] < len(stacks)` in `directory._selftest`.
3. **Full-circle overlap.** *`_arc_overlap` must return True for a 360° span against any other
   arc.* **Fails today** — `_arc_overlap(20, 60, 0, 360)` is `False`, which is why `collisions()`
   returns `[]` while five real same-deck overlaps exist (§3.4 item 6).

A fourth is worth considering and is bigger than this audit: **the deck stack should be clipped
to the hull it sits in.** `decks_in_ring()` takes a sector and returns a constant-radius stack;
it has no z argument, so it cannot know the hull tapers. Giving it one would delete 0.163 km³ of
deck and 45.8 km² of floor that do not exist, and would make `tools/cutaway.py`'s
"14 locations outside the hull" impossible to write rather than merely visible.
