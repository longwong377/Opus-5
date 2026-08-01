# Working transport — session 4g

**A body boards a lift on one deck, rides it, and alights on a different deck.**
It is the first vehicle in this project that moves at runtime and the first one a player
can be inside of.

    RIDETEST from_landing=3 from_deck=3 to_landing=0 to_deck=0 start_deck=3 end_deck=0
             start_miss_mm=1 end_miss_mm=4 boarded=true alighted=true
             r_start=200.0771 r_end=210.8744 fell_m=10.7973 want_rise_m=10.8000
             radial_floor_m=10.8341 radial_air_m=0.0294 floor_m=19.707 air_m=0.029
             offfloor=3/557 ride_offfloor=0/311 standoff_max_mm=0.89 carry_frames=311
             car_moved_m=10.8000 ride_frames=311 door_z_m=0.7137
             ride_off_first=-1 ride_off_last=-1 doors_shut_before_move=true
             door_open_end=1.00 ride_s=5.1683 ride_t=5.1833
             carry=on snap=on platform=off collider=animatable snap_m=0.100 park=-1

Run it:

```bash
python3 station/transit_runtime.py --selftest   # 21/21, no engine needed
python3 station/transit_runtime.py --ride       # THE GATE: the ride and two controls
python3 station/transit_runtime.py --tram       # the guideway train, moved by phase
```

## 1. What was there before

Measured at the start of the session, not summarised:

| module | what it has | what it does |
|---|---|---|
| `station/transit.py` | every journey costed, by every mode | **times only** |
| `station/npc/navigation.py` | `lift_ride_s`, `axial_ride_s`, `ground_tram_ride_s`, the Coriolis cap | **times only** |
| `station/core_tube.py` | the core shuttle tube | its own docstring: *"with no motion in them at all"* |
| `station/tram.py` | `guideway_cars(phase=)`, which walks a whole train along the run | **nothing ever called it with a changing phase** |
| `station/lift.py` | a shaft, a car, a floor under it, 37 gates | `lift_car(at_deck=)` **parks** it |

Five modules model transport. Every mode is fully costed and none of them moves — the same
shape as everything else this project has been caught on: a number computed about a thing
that does not exist.

## 2. The shaft that ships

`blue` ring 0, 80°, z = 7500 — `station/lift.py`'s own self-test address, with one more
landing (four decks, not three) because the control needs a body falling **past** a landing
and a two-storey shaft cannot show one.

```
4 landings over 10.800 m of radius     decks 0..3, walk radius 210.878 -> 200.078 m
16,076 render triangles                shaft + four lobbies
   140 static collision triangles      the smooth shell -- 0.87% of the render mesh
    28 collision triangles on the car  the box + the solid its shut door is
   788 render triangles on the car     of which 120 are the two door leaves
```

**The lobby is not new geometry.** `lift.py` builds a landing sill 0.44 m deep — a ledge,
not a floor — so a lift you can only be *inside* is not a lift you can *board*. Every
landing therefore gets **one section of `interior.axial_run` / `collision.axial_shell` at
that landing's own `floor_r_m`**: the station's own corridor generator, at the landing's own
radius. Its walking surface comes out at `floor_r_m - floor_y`, which is exactly where
`lift.py` asserts the car's floor lands, so a body crosses the threshold without a step.
`LOBBY_M = interior.AXIAL_SECTION_M` — one section, the unit `axial_run` subdivides into,
not a length chosen to make the test work.

## 3. Where every timing number comes from

Not one is chosen in either new file. Each is read from the module that owns it and
cross-checked against a second module that computed it a different way.

| number | value | source | cross-check |
|---|---|---|---|
| ride time, 4 landings | **5.1683 s** | `npc/navigation.lift_ride_s(schema, rise)` | `transit.climb_leg` agrees to 1e-9, through code that shares nothing |
| the rise it is computed from | **10.800 m** | the difference of two landings' own `walk_r_m`, off the mesh `lift.shaft_geometry` emitted | never `interior.DECK_PITCH_M` restated |
| motion curve | smoothstep, tabulated at 64 samples | the profile **both** of those functions derive their answer from | the table's own peak is asserted to be `coriolis_speed_cap` |
| peak speed | **3.1345 m/s** | `navigation.coriolis_speed_cap` | table peaks at 3.1335 m/s (0.03% under, which is the sampling) |
| dwell | 20 s | `navigation.TRANSIT_DWELL_S` | — |
| door leaf travel | **750 mm** | **measured**: the car built at `open_fraction` 0 and 1, per-triangle difference | equals `PROVISIONAL["door_width_m"]/2`, and that comparison is the only place the two meet |
| door time | 0.469 s | leaf travel ÷ `godot/scripts/door.gd`'s own `speed_m_s`, **read out of that script** by instancing it | — |
| gravity | **7.431 m/s²** | the deck's own `floor_g` (0.7578) × the schema's `standard_gravity_m_s2` | `interior.gravity_at` agrees to its own rounding |
| tram cycle | **136.9 s** per car spacing | `transit.line_report` — 2 legs of 48.5 s plus 20 s dwell each | — |
| tram within-leg profile | jerk-limited, tabulated | `transit.ride_profile` + `transit._ramp` | integrates to 646.50 m against `transit._integrate_profile`'s 646.50 m |

**The control on the profile check.** A constant-speed table covers the same distance in the
same time and peaks at 2.0897 m/s — 0.67× the cap. So the assertion "the table's peak IS the
Coriolis cap" can fail, and `_selftest` proves it can by measuring the linear case.

**The leaf travel is the pattern worth carrying.** `walk.gd` takes a `--door-travel` number
and `walkable.py` hands it `PROVISIONAL["door_width_m"] / 2` — a second description of a
decision `interior_kit.door_leaf` already makes. Here the car is built twice and subtracted,
so the runtime slides a leaf exactly as far as the generator would have drawn it, and *which*
leaf goes which way is a fact about the mesh rather than an argument about left and right.
The difference is taken **per triangle, not per vertex**: `lift.weld` fuses the two shut
leaves to each other (they share an exactly coincident face — `lift.py`'s own documented four
non-manifold edges), so the vertex lists are not comparable and the triangle lists are.

## 4. The gate, and it can fail

`station/transit_runtime.py --ride` launches Godot headless six times.

### The ride — PASS

```
start deck 3 -> end deck 0, radial 10.834 m on the floor (0.029 m in the air),
offfloor 3/557 overall / 0/311 during the ride
standoff 0.89 mm, car moved 10.8000 m, doors shut before it moved: true,
ride 5.1683 s over 311 frames, standing 0.7137 m clear of the shut door
```

Three separate claims, because one number cannot carry them:

* **net** — the body ended 10.797 m of radius from where it started, against a 10.800 m shaft;
* **on the floor** — 10.834 m of radial travel was covered standing on something;
* **in the air** — 29 mm was not, over 3 of 557 frames.

`radial_floor_m` is a *total variation* and can only grow — a body that wobbles 30 mm crossing
a sill adds 30 mm to it — so it is asserted as a floor, and the net displacement carries the
"did it actually go there" claim.

**Why on-floor distance is reported separately.** A recent broken run in the streaming work on
this codebase reported a path length of 11,712 m because the body was falling. On this gate the
no-carry control covers **10.813 m in the air and 0.049 m on the floor**; a plain path length
would read 10.86 m and score a 10.8 m free fall as a successful ride.

### Control 1 — the car is parked at another landing — FIRED

```
the body walked into the doorway and fell 10.802 m down the shaft, 9.490 m of it off the
floor (boarded=false, offfloor=295/570, ended at r=210.8771 m against landing 0 at 210.878 m)
```

`station/lift.py`'s own self-test measures a 2,315 mm fall for this on a three-landing shaft;
on the full shaft it is 10.8 m, and the body ends up standing on the floor of the car it was
trying to board, one deck's worth of shaft below.

**This control found a defect in my own verdict logic first.** The first run reported
`boarded=true` and a fall of −3 mm: the body fell straight through the car's ceiling — which
faces outward and is therefore a *back face* to something arriving from above, and Godot's
`ConcavePolygonShape3D` has `backface_collision` off — landed on the car's floor, and satisfied
"is the body inside the car". Being inside the car is not boarding. **Boarding is the car being
at your landing and you walking into it**, and that is what the test now requires.

### Control 2 — nothing carries the body — FIRED

```
start deck 3 -> end deck 0, radial 0.049 m on the floor (10.813 m in the air),
offfloor 305/557 overall / 301/311 during the ride
lost the floor from ride frame 6 to 306, standing 191.07 mm off the car floor at worst
```

## 5. FOUR THINGS CAN CARRY A BODY, AND THREE OF THEM WORK HERE

This is the finding of the session and it is the reason control 2 turns off more than one
switch. Godot will take a `CharacterBody3D` along with the floor it is standing on in more
ways than one, so `godot/scripts/transit.gd` keeps them as four independent switches and the
gate measures each **alone**, with the explicit carry off:

| mechanism | `ride_offfloor` | stand-off | radial on the floor |
|---|---|---|---|
| floor snap only (`floor_snap_length` at its 0.1 m default) | **0 / 311** | 1.12 mm | 10.835 m |
| platform velocity only (`platform_floor_layers` default) | **0 / 311** | 0.90 mm | 10.832 m |
| a teleported `StaticBody3D`, nothing else | **301 / 311** | 191.07 mm | 0.049 m |
| **the shipped carry** (explicit translation) | **0 / 311** | 0.89 mm | 10.834 m |

**Why three of them work: this lift is slow.** The ride is Coriolis-capped at 3.1345 m/s,
which at 60 Hz is **52.2 mm a frame** — and `floor_snap_length` defaults to **100 mm**, so
snap alone re-attaches the body every frame with 48 mm to spare. That is a property of *this
vehicle*, not of the engine: the guideway tram's own line report gives a peak of **26.679 m/s**,
which is **444.6 mm a frame — 4.4× the snap window**. The explicit carry is redundant on the
lift and will not be on the tram, and it is what makes the ride not depend on a coincidence
between two unrelated numbers.

**The negative result is worth as much:** `AnimatableBody3D` + `sync_to_physics` does **not**
carry a rider by itself. With carry, snap and platform velocity all off it scores 301/311
off the floor — identical to the teleported `StaticBody3D`. What `sync_to_physics` buys is
that the body is *resolved against a floor that is going somewhere*; it does not move the
rider.

### THE COLLIDER IS ONE FRAME BEHIND THE COMMAND

Measured, not assumed. The first working ride reported a **51.83 mm** stand-off at peak speed.
3.1345 m/s at 60 Hz is **52.2 mm a frame** — the whole of the error, and it names the cause:
Godot delivers `_physics_process` in tree order and an `AnimatableBody3D`'s `sync_to_physics`
sync afterwards, so when `move_and_slide()` runs inside this script the physics server still
holds the position commanded *last* frame. The body rides the floor's previous position, which
is inherent to kinematic physics and is what the engine's own moving-platform path does too.

Carrying by the delta the server has **already applied** — one frame back — took the stand-off
from 51.83 mm to **6.56 mm**, and the stand-off is measured against the same lagged position,
because measuring against the command reports one frame of travel as an error on every frame.

### AND THEN TWO FRAMES OF LOST FLOOR TURNED OUT TO BE THE DOOR

The remaining `ride_offfloor=2/311` was at ride frames 24–25 and it was not the carry at all.
`_in_car` becomes true the instant the capsule crosses the door plane, so the body stopped
**0.670 m** from the car's centre — and with a 0.35 m capsule radius that put its shell
**0.6 mm** from the inner face of the door panel at the moment the panel went solid. The
depenetration between the two broke floor contact.

The fix is that the body keeps walking to the middle of the car while the doors close, which
is also simply what a passenger does. `door_z_m` — how much clearance it ends up with — is now
in the verdict: **0.7137 m**. Stand-off 6.56 → **0.89 mm**, ride off-floor 2 → **0**.

## 6. Doors

`godot/scripts/door.gd` is followed, not duplicated:

* the leaves are their own mesh groups (`liftleaf_0`, `liftleaf_1`) because the piece that
  moves has to be, and their travel is measured off the generator's own two states;
* the shut door is **solid**. `lift_collision`'s shell leaves the car's door face permanently
  open, so a body could walk out of a moving car into the shaft — the same defect `door.gd`
  was written to end, one vehicle along. `transit_runtime.car_collision` adds one
  `liftdoorpanel` box, built to `collision.door_panel`'s own 0.12 m thickness and 0.02 m
  margins ("a collider that exactly matches an opening leaves a hairline a capsule can catch
  on"), and `_selftest` casts a ray through it **and through the car without it** as the
  control;
* the panel is disabled at `open > 0.15`, `door.gd`'s rule and its reason: disabling it the
  instant a body is in range lets a player walk through a door that is still visibly shut;
* `doors_shut_before_move=true` is asserted on the state transition, not assumed.

## 7. The tram

`station/transit_runtime.py --tram`. `tram.guideway_cars` is called **once**, at phase 0, and
its cars are sliced apart by its own reported `car_triangles`, so the mesh the runtime moves
is the mesh that function emits. The runtime's only job is to reproduce that function's
placement rule as a function of time — and **that reproduction is the gate**:

```
2 cars of 96 m on one guideway of green, 1,293 m apart; a car covers that spacing in
136.9 s (2 legs of 48.5 s plus 20 s dwell each, transit.line_report), peak 26.7 m/s

  t=   22.8 s  phase= 0.2212  car0   4771.45 m (python   4771.45)  car1   6064.45 m (python   6064.45)
  t=   68.5 s  phase= 0.5000  car0   5132.00 m (python   5132.00)  car1   3887.00 m (python   3887.00)
  t=  273.9 s  phase= 2.0000  car0   4485.50 m (python   4485.50)  car1   5778.50 m (python   5778.50)

  PASS  every car is where tram.guideway_cars(phase=) puts it -- worst disagreement
        3.600 mm over 12 samples, against the 5 mm that function's own 2-decimal
        placement report allows
  PASS  and they actually moved -- 1,891.5 m from where they were baked
```

The test is a **time lapse and says so** in its own output (`x27 time lapse`): one cycle of
this line is 137 s and the test runs two of them, and a car's position is a function of the
clock with no physics body involved. The motion law still executes once per physics frame;
what is compressed is the clock, not the number of steps.

**The wrap is `guideway_cars`'s, not ours.** At t = 68.5 s car 1 goes from 6377 m to 3887 m in
one sample — the modulo in that function's placement rule, faithfully reproduced. A real line
would turn a car round at the end of the run and this one teleports it. Recorded as a
limitation rather than fixed, because fixing it means changing `tram.guideway_cars`, which
this session does not own.

**Nothing rides the tram yet**, and the reason is stated rather than glossed: `tram.py` builds
a saloon with a floor but **no collision shell**, and `station/collision.py` has no generator
for a vehicle. A body cannot stand in something that has no walkable surface. The patch is
in §9.

## 8. What is NOT done

* **Nothing rides the tram** — no collision shell for the car (§9).
* **The landing doors never open.** `lift.lift_shaft` has no `open_fraction`, so the shaft's
  landing leaves are drawn shut at every deck for ever, and the car's own doors are the only
  ones that move. The aperture in the collision shell is permanently open either way — which
  is what makes control 1 fire — so a landing with no car at it is an open hole a player can
  walk into at any time. In a station it would be shut. §9 has the patch.
* **The core shuttle does not move** (`core_tube.py`), and the ground tram does not
  (`transit.ground_line`). Both are costed and neither is built to move.
* **One shaft.** `station/lift.py`'s docstring records `station/routes.py --report` reading
  `lift 0 buildable of 38` before that module existed, and the last build put five transit
  columns on disk. This moves **one** of them. Rolling it out is a manifest per column, which
  is `build_lift(**address)` — the address is the only thing that changes.
* **No call buttons, no schedule, no NPC ever rides.** The car goes where the test tells it.
  `navigation.SHAFT_TARGET_HEADWAY_S` and `shaft_cars` already size a fleet.
* **No frame.** This session made no craft claim and rendered nothing; the deliverable is the
  gate. A frame of the car at a landing would need a shot mode in `transit.gd` and a camera.
* **144 of the car's 788 triangles carry no material** — see §9, and it is `lift.py`'s.

## 9. CHANGES I NEED IN FILES I DO NOT OWN

Three, all small, none of them blocking what shipped.

### 9.1 `station/lift.py` — the car's handrails are unmaterialled

`lift_car` merges `interior_kit.handrail` three times with **no `tag()` block** around them, so
**144 triangles** (3 × 48) export as `liftcar__untagged` and take the glTF fallback. This is
session 3x's finding (`door_assembly` merged 1,248 triangles a deck with no tag, and it was the
surface a player looks straight at) arriving through a third door. The handrail is described in
`lift.py`'s own comment as "the dominant warm accent in every interior frame in the reference
set". `materials.py` line 974 already binds the name — `binds=("rail_band", "handrail")` — so
nothing has to be authored.

`station/transit_runtime.py --selftest` asserts this as a **ceiling** (`untagged <= 3 ×
len(handrail)`), so it fails if the number grows and goes green when this lands.

```python
--- a/station/lift.py
+++ b/station/lift.py
@@ lift_car, the handrail block
-    K._merge(verts, tris, *K.handrail(2.0 * (hw - ret)), back_map,
-             (back_x, 0.0, -ls * (hd - 0.03)))
-    for sx, smap in ((-1.0, lambda x, y, z: (y, z, x)),
-                     (1.0, lambda x, y, z: (-y, z, -x))):
-        rv, rt = K.handrail(2.0 * (hd - ret))
-        K._merge(verts, tris, rv, rt, smap,
-                 (sx * (hw - 0.03), 0.0, sx * (hd - ret)))
+    with K.tag('handrail'):
+        K._merge(verts, tris, *K.handrail(2.0 * (hw - ret)), back_map,
+                 (back_x, 0.0, -ls * (hd - 0.03)))
+        for sx, smap in ((-1.0, lambda x, y, z: (y, z, x)),
+                         (1.0, lambda x, y, z: (-y, z, -x))):
+            rv, rt = K.handrail(2.0 * (hd - ret))
+            K._merge(verts, tris, rv, rt, smap,
+                     (sx * (hw - 0.03), 0.0, sx * (hd - ret)))
```

The shaft has **0** untagged triangles of 3,052, because its guide rails come from
`interior_kit.pilaster`, which tags internally. Only the car is affected.

### 9.2 `station/lift.py` — `lift_shaft` cannot open a landing door

`lift_car` takes `open_fraction` and passes it to `door_assembly`; `lift_shaft` takes
`door_leaves=True|False` and never passes one, so every landing's leaves are drawn shut at
every deck for ever. A car arriving at a landing should open both doors.

```python
--- a/station/lift.py
+++ b/station/lift.py
@@ def lift_shaft(..., door_leaves=True, landings=True, stack=None, weld_mesh=True):
+                 open_fraction=0.0,
@@ the landing loop
-            v, tt = K.door_assembly(p, section=rect, depth=(0.0, t),
-                                    leaves=door_leaves)
+            v, tt = K.door_assembly(p, section=rect, depth=(0.0, t),
+                                    leaves=door_leaves,
+                                    open_fraction=open_fraction)
```

With that, `transit_runtime.car_render`'s two-build difference works unchanged on the shaft:
build it at 0 and 1, subtract per triangle, emit each landing's leaves as their own group.
Until then the landing doors are scenery.

### 9.3 `station/tram.py` — a car nobody can stand in

`tram.tram_car(interior=True)` builds a saloon with a floor, seats and a ceiling, and there is
no collision for any of it, so a body cannot ride the tram the way it now rides the lift. What
is needed is `collision.py`'s rule applied to a vehicle: a **smooth shell**, not the render
mesh, derived from the saloon's own measured levels rather than written down —

```python
def car_shell_collision(interior=True):
    """The smooth box a passenger stands in. NOT the render mesh: the saloon
    carries seat pitch, a cant rail and a valance, and a capsule catches on all
    three -- `station/collision.py`'s subject, applied to a vehicle.

    Every dimension off this module's own `level_y`/`level_w`/`_saloon_span`, so
    it cannot drift from the saloon it stands in for.
    """
```

with a floor at `level_y("floor")`, a ceiling at `level_y("cant")`, sides at
`level_w("sill") - WALL_T` and ends at `_saloon_span()`, wound inward. Then
`transit_runtime.build_tram` emits it per car exactly as it emits the lift's, and `transit.gd`
carries a rider with the switch that already exists — which at 444.6 mm a frame is the case
where the explicit carry stops being redundant.

### 9.4 `.github/workflows/validate.yml` — the gate does not run in CI

`--ride` takes about four minutes (six headless engine launches) and asserts something no
other gate in this repository does: that a player can be *inside a vehicle that moves*. It
belongs in the workflow, after `The station is walkable`, with its own `continue-on-error`
and outcome record — the arrangement session 4e installed so one failing step cannot blind
the ones behind it.

```yaml
      - name: A body rides the lift
        id: ride
        continue-on-error: true
        run: python3 station/transit_runtime.py --ride --quick
```

`--quick` skips the four-way decomposition of the carry, which is a measurement rather than a
gate and costs three of the six launches.

## 10. Files

| file | what |
|---|---|
| `station/transit_runtime.py` | the offline half — meshes split so the piece that moves is its own node, motion tables, the manifest, and the gate. `--selftest` is 21/21 with no engine |
| `godot/scripts/transit.gd` | the runtime — the lift's state machine, the carry, the doors, the tram's phase, and the headless verdict |
| `godot/scenes/transit.tscn` | four lines; everything arrives in the manifest |
| `station/generated/scene/transit/` | `lift.json`, `lift_static{,_col}.glb`, `lift_car{,_col}.glb`, `tram.json`, `tram_cars.glb`. Gitignored — rebuilt by `--build` |
