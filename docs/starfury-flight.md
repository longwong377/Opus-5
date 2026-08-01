# The flyable Starfury

Session 4e. The opening line of `CLAUDE.md` has always said *"Flyable Starfury with
seamless launch and dock"*, and session 4d's audit found **zero references to `starfury`
in any `.gd` or `.tscn`** — while `station/physics/starfury.py` had eighteen passing
tests, `station/starfury_geometry.py` had a 774-line airframe with an agreement test,
and `station/physics/rotating_frame.py` knew exactly what leaving a spinning hull does
to you. The physics was proven and unreachable.

This is the bridge, and it is three files:

| file | what it is |
|---|---|
| `station/starfury_scene.py` | builds the airframe `.glb`, **measures** the cobra bay off the hull mesh, derives the launch through `rotating_frame.py`, and records nine scenarios of the Python flight model as vectors the engine replays |
| `godot/scripts/starfury.gd` | a **checked port** of `station/physics/starfury.py` — 6-DOF Newtonian, quaternion attitude, Euler's gyroscopic term, the same thruster allocator — plus the pilot's controls, the chase and cockpit cameras, and the shot machinery |
| `godot/scenes/starfury.tscn` | minimal, like `walk.tscn`: geometry at runtime, and the **look borrowed live** from `exterior.tscn` |

Nothing under `station/physics/` was edited. It is the source of truth and it stays that way.

---

## What a pilot can actually do

Six axes, no coupling anywhere, and nothing that damps velocity.

```
W / S      main engines fore / aft          A / D   lateral RCS
R / F      vertical RCS                     arrows  pitch and yaw
SPACE      kill rotation                    X       kill velocity (a manoeuvre, not a brake)
TAB        chase view / cockpit
```

Measured by `--pilot-test`, which drives the **same mapping function the keyboard drives**
from a scripted key sequence, so the control scheme is tested rather than assumed:

```
  mains ahead               speed   55.14 m/s  spin   0.00 deg/s  nose    0.0 deg  off velocity   0.0
  yaw left, no thrust       speed   56.21 m/s  spin  59.99 deg/s  nose  112.7 deg  off velocity 112.6
  hands off                 speed   56.21 m/s  spin  59.99 deg/s  nose  120.0 deg  off velocity 127.4
  lateral RCS, starboard    speed   56.64 m/s  spin  59.99 deg/s  nose  120.0 deg  off velocity   7.6
  vertical RCS, up          speed   56.65 m/s  spin  59.99 deg/s  nose  120.0 deg  off velocity 112.4
  kill rotation             speed   56.19 m/s  spin   0.00 deg/s  nose    4.8 deg  off velocity 116.2
  kill velocity             speed    0.41 m/s  spin   5.01 deg/s  nose  113.5 deg  off velocity 164.2
  nose swept 591 deg in total; travelled 1006 m
```

Read the third row. **Hands off the controls, the craft keeps rotating at 59.99 deg/s and
keeps moving at 56.21 m/s**, and the nose is 127 degrees away from where the craft is
going. That is the whole premise of the machine and it is what the assertions test:
distance covered ≥ 300 m, velocity moved by the yaw leg ≤ 25 m/s, and the kill-velocity
manoeuvre ending under 2 m/s. Yawing moved the velocity by **1.08 m/s**, and even that is
not a coupling — it is the forward thrust the four mains unavoidably produce while
torquing, which is a property of the layout (below).

## The launch, and how it is checked

The bay is **not a number in a file**. `cobra_bay_geometry()` reads the vertices of the
`cobra_bay_well` group out of `station/generated/hull.obj` — the surface a fighter
actually sits in — so the launch point cannot drift from the hull the player is looking
at. Hard rule 4, applied a fourth time.

```
cobra bay measured off the hull mesh: r 293.78 m at z 7182.4 m, phase +12.86 deg
  protrusion: measured 25.2 m vs schema 26 m
exit velocity per rotating_frame: 55.1483 m/s   (-12.2665, 53.7668, 0.0)
```

The measured clocking of +12.857° recovers `components.cobra_bay_ring`'s
`ring * pi / per_ring` = 180/14 exactly, from geometry, without being told.

**THE BAY IS NOT THE HABITAT FLOOR.** The one tangential speed this project has written
down is **52.24 m/s**, the drum floor at r 278.3 m (`STATE.md`). The cobra bays stand
**15.5 m outboard of it**, so a fighter leaves at **55.15 m/s** and reaching for the
number already in the notes would have been wrong by 2.91 m/s. That is the shape of
mistake this whole file exists to make impossible.

### Three independent derivations of one number

The engine is never told the answer. It is given the bay — radius, axial station,
clocking, omega — and derives the exit velocity twice; `rotating_frame.py` derives it a
third time analytically. `station/starfury_scene.py --check` compares all three:

```
PASS  exit speed, engine vs rotating_frame        engine  55.148265   model  55.148265   d -3.6e-14
PASS  exit speed by finite difference of the ride engine  55.148259   model  55.148265   d -5.6e-06
PASS  release radius                              engine 293.783985   model 293.783985   d +2.3e-13
PASS  omega used by the engine                    engine   0.187717   model   0.187717   d  0
PASS  radial component of the exit velocity       engine   0.000000   model   0.000000   d +9.3e-14
--- negative control: the same check on a 1% wrong exit speed ---
  control FIRES (good)
```

The finite-difference row is the interesting one: the engine rides the bay round on the
rotating hull for a whole quarter-turn and recovers 55.148259 m/s by differencing its own
trajectory, against 55.148265 analytic. A port with the rotation backwards, the wrong
radius, or the drum floor's speed instead of the bay's moves exactly one of these rows.

The last row is the physical claim: **a craft at rest in the rotating frame leaves with no
radial component at all.** It is flung, not pushed. The cobra bay needs no catapult, which
is what the show depicts and what `starfury.launch_from_drum`'s docstring says.

## The port, and why it is safe to have two copies

`godot/scripts/starfury.gd` restates `station/physics/starfury.py` in GDScript because a
flyable ship responds to a key pressed 8 ms ago, and the alternative to a checked port is
a ship playing back a recording. Two copies can drift, so `--selftest` replays nine
scenarios recorded from the Python model and compares every component of every state:

```
PASS  layout                   9 thrusters agree with station/physics/starfury.py
PASS  coast                    worst |delta| 0
PASS  rotate_while_coasting    worst |delta| 1.110e-16
PASS  flip_and_burn            worst |delta| 5.684e-14
PASS  asymmetric_yaw           worst |delta| 1.110e-16
PASS  free_tumble              worst |delta| 1.110e-16
PASS  allocate_forward         worst |delta| 3.553e-15
PASS  allocate_lateral         worst |delta| 2.776e-17
PASS  allocate_mixed           worst |delta| 4.441e-16
PASS  cobra_release            worst |delta| 0
  worst scenario: flip_and_burn at 5.684e-14 (tolerance 1.000e-6)
```

Worst disagreement **5.7e-14 metres**, over positions that reach 1,650 m. That is bit-level,
and it is deliberate: the tolerance is not a physics tolerance. Both sides run the same
semi-implicit Euler in double precision over the same step count, so anything above ~1e-9
relative means a *different algorithm* rather than accumulated error. The port even
multiplies by reciprocals where the Python `unit()` does, because `v * (1/n)` and `v / n`
differ in the last bit of a double.

### The controls fire

| control | what it injects | result |
|---|---|---|
| `--drift=aero` | velocity lerps toward the nose, 2%/s — the aeroplane assumption | **6 of 9 red** |
| `--drift=nogyro` | Euler's gyroscopic term dropped | **1 of 9 red — `free_tumble`, and only that one** |

`nogyro` reddening exactly the scenario written for it is the decomposition working. The
three the `aero` control leaves green (`flip_and_burn`, `allocate_forward`, `free_tumble`)
are the three whose velocity is **collinear with the nose**, where lerping a vector toward
its own line and renormalising returns it unchanged. That is arithmetic, not a hole.

## A finding about the flight model itself

`aurora_thrusters()` produces **torque from the four mains only.** Every RCS thruster in
the layout fires through the centre of mass — `rcs_lat_r` sits at (3.4, 0, 0) and pushes
along −X, so its moment arm is parallel to its thrust and its torque is identically zero —
and the mains, on the aft centreline of each boom, give torque about body X and Y and
**none about Z**.

Two consequences a pilot feels:

* **there is no roll authority at all**, so the controls do not offer roll and the
  autopilot never commands it;
* **every rotation is also a shove**, because turning means running two of the four mains.
  This is why the yaw leg above moves the velocity by 1.08 m/s.

Recorded rather than fixed: `station/physics/` is tested, is not this session's to edit,
and the fix is a decision about the craft (add RCS couples off the centreline) rather than
a bug in a port. It is the one thing to change if the Starfury is ever to barrel-roll.

## The mission, and the frames

`--mission` flies the whole thing headlessly and writes `flight.json`. It is not a
cutscene: every metre of it comes out of the flight model through `allocate`.

```
released at 55.15 m/s from r 293.8 m; coasted unpowered to r 443 m in 6 s;
73 s under power (34 accelerating, 39 decelerating), peak 381 m/s;
ended 8,956 m from the station centre at 0.4 m/s with the nose 0.79 deg off it, after 113 s
```

**The station throws it 149 m clear in six seconds with the engines cold.** That is the
cobra bay working.

Guidance note worth keeping: the first version aimed at the waypoint and braked on closing
rate — pure pursuit with a brachistochrone — and *never converged*. It flew past, looped,
and was still orbiting at 240 s, 3.7 km out and doing 490 m/s. A closing-rate test cannot
see **lateral** velocity, and at 400 m/s with a four-second flip that is most of the miss.
Velocity matching — compute the velocity the craft should have and burn to null the
difference — converges in 73 s, because the lateral component is part of the error rather
than invisible to it.

### Evidence frames

All three through `tools/render_godot.sh`, all three confirmed
`Vulkan 1.4.318 - Forward+`, which the script now refuses to run without.

| frame | what it shows |
|---|---|
| `docs/engine-4e-fury-station.png` | the baseline exterior at the calibrated 9,200 m / 18° / az 214 framing, unchanged, as the control |
| `docs/engine-4e-fury-launch.png` | **the flyable scene rendering itself.** The fighter a twelfth of a second out of the bay mouth, sunlit, with the cobra bay well, its hazard lip and its marker lights beside it. Camera, ship pose and lighting all come from `scripts/starfury.gd` |
| `docs/engine-4e-fury-lookback.png` | **the deliverable.** The whole 8,047 m station from a Starfury at 8,956 m — the fighter's own flown pose, in the foreground, at the framing `exterior.tscn`'s measured exposure was derived at |
| `docs/engine-4e-fury-freeflight.png` | **the interactive build, running.** `--free=20` flies the real playable path — `_physics_process`, pilot input, chase camera, debug readout — for twenty seconds and photographs it |

The free-flight frame is the one that proves the playable path rather than a headless one,
and its readout is the evidence:

```
t   20.8 s
position     31.3   1183.7   7182.4 m
velocity    -12.3     53.8      0.0 m/s
speed        55.1 m/s
nose off velocity  90.0 deg   spin  0.00 deg/s
range to station centre   3374 m
floating origin 17,1039,7189  rebases 3  float32 spacing here 0.49 mm, after rebase 0.0153 mm
```

**`nose off velocity 90.0 deg`.** The craft left the tube pointing radially outward and is
travelling tangentially; twenty seconds later it is still pointing where it was and still
going where it was going, with the spin rate at exactly 0.00 deg/s because nothing has
touched it. That is the whole craft in one line of a live build.

The last line is `station/physics/floating_origin.py` doing its job with a number attached:
at 7.2 km from the station origin, float32 spacing is **0.49 mm** — above the module's own
1 mm jitter threshold's neighbourhood and visible on a stationary hull — and after three
rebases the render-space coordinates are small enough that it is **0.0153 mm**.

Two things about the look-back frame are deliberate. The ship is at its **flown** position,
not a position anyone chose — the camera is `_chase_eye()` of the state the mission ended
in, which is why the shot is evidence rather than a picture. And it is rendered by
`scenes/exterior.tscn` through `scripts/render_shot.gd`, with the posed airframe simply
added to the shot's `glb` list, so the station's exposure, tonemapper, three-point rig and
36 material rules are the project's own and not a second copy.

The ride time before release is derived from the shot's own key light: the bay comes round
once every 33.47 s and spends most of that lap on the anti-sun side, where a launching
fighter is a black shape against a black hull — which is exactly what the first launch
frame was. The clamps therefore let go as the bay swings into the sun. The launch physics
is identical either way; only the beat of the lap changes.

## Running it

```bash
# everything that can be checked without a render, one command
python3 station/starfury_scene.py --gate

# the three frames
bash tools/render_godot.sh --shot exterior --orbit 9200,18,214 --res 1280x720 \
    --out docs/engine-4e-fury-station.png
bash tools/render_godot.sh --shot starfury --no-export --res 1280x720 \
    --out docs/engine-4e-fury-launch.png
python3 station/starfury_scene.py --compose \
    station/generated/scene/starfury/flight.json --out docs/engine-4e-fury-lookback.png
bash tools/render_godot.sh --shot starfury_lookback --no-export --res 1280x720 \
    --out docs/engine-4e-fury-lookback.png

# fly it yourself
<godot> --path godot res://scenes/starfury.tscn -- \
    --scene-json=station/generated/scene/starfury/scene.json
```

`--gate` is **not** wired into CI. Session 4d's ruling is to keep the existing gates green
and not grow them, and this is one port's own test rather than a new scored dimension.

## What is not done

* **Docking.** `station/physics/docking.py` has `DockingBay`, `closing_rate`,
  `contact_is_safe` and `spin_match_velocity`, all tested, and none of it is wired. The
  return leg is the obvious next increment and the module it needs already exists.
* **No cockpit interior.** TAB switches to a cockpit eye point derived from
  `starfury_geometry.cockpit_volume()`, but there is no instrument panel to look at —
  the canopy and its glazing are modelled and the tub is empty.
* **The airframe renders on the hull's fallback material.** Its sixteen groups
  (`starfury_fuselage`, `starfury_engine_bell`, …) match no rule in `exterior.tscn`'s
  table, so they land on `hull_exterior`. Correct enough for a metal airframe at range and
  wrong for the canopy glazing, which should be glass and is not.
* **No engine plumes, no weapons, no sound.**
* **The readout is a debug readout**, not a HUD: eight lines of text with position,
  velocity, speed, nose-off-velocity, spin rate, range to the station, and the floating
  origin's rebase count with the float32 spacing it is buying.
