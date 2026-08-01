# G2 ROUTE WALKED — a body walks from one deck to another

Session 4g. `station/route_walk.py`, `godot/scripts/route_test.gd`,
`godot/scenes/route_test.tscn`.

    python3 station/route_walk.py --report     the route and its legs, no engine
    python3 station/route_walk.py --selftest   everything answerable offline (12 checks)
    python3 station/route_walk.py --walk       THE GATE: the walk and both controls

---

## 1. What was missing

`station/routes.py` reports the station as **1 foot-connected component**. That is a claim about
a graph. Every walk test in this repository walks inside **one z-cluster**:

| gate | what it walks |
|---|---|
| `walkable.py --deck blue/0/0` | 126 m of one 40 m slice of one deck |
| `drum_walk.py` | the drum's ground, one place |
| `transit_runtime.py --ride` | the lift alone — landing 3 to landing 0, with a 9.2 m lobby either side |

**No body had ever walked from one deck to another.** The graph said you could; nothing had.

This gate takes a route **out of `routes.py`** — shortest path over the station's own circulation
graph, printed as legs with their kind — and walks it end to end: a named room on one deck, its
ring corridor, the deck's **axial spine**, the transit column's lobby, into the car, the ride, out
on a different deck, that deck's spine and ring corridor, and **into a named room**. It reports
metres covered **on the floor**, frames spent off it, and where it stopped.

`floor_m` and not path length, and the reason is on the record: the streaming work on this same
codebase found a body reporting **11,712 m of "distance travelled"** while falling. A gate that
adds up displacement without asking whether the body was standing on anything scores a fall as a
journey.

---

## 2. THREE THINGS THE GRAPH GRANTS AND THE GEOMETRY DOES NOT

These are the findings. They are not incidental to building the gate — they are what building it
found, and each one is a way in which `routes.py`'s **1 component** is larger than the station.

`routes.py` grants a `lift` edge from **every** deck's spine to its ring's column, and the
condition on that edge is `built=_LIFT_EXISTS`, which asks the filesystem whether `station/lift.py`
exists and nothing else. Measured against the column `tools/export_station.py` actually builds:

### 2.1 — 19 of 71 located decks have NO LANDING on their sector's column

`export_station` puts one column per sector at the **lowest z any of that sector's clusters sits
at**, and `interior.decks_in_ring(z_m=)` returns a **different number of decks at different z**.

    blue ring 0 at z=6880 (where the column stands)   6 decks
    blue ring 0 at z=7120 (where the docking bays are) 10 decks

So blue's column has no landing for ring-0 decks 6, 7, 8 or 9 — the morgue, cryo storage, the fuel
stores and `standard_corridor`. Per sector:

| sector | column z | landings | decks carrying locations | with no landing |
|---|---|---|---|---|
| blue | 6880 | 18 | 16 | **4** |
| green | 4000 | 9 | 10 | **1** |
| grey | 3600 | 23 | 19 | **12** |
| red | 6600 | 58 | 17 | 0 |
| yellow | 160 | 24 | 9 | **2** |

**52 of 71.** Red is clean; grey is more than half unreachable.

### 2.2 — 26 of the 72 clusters that DO have a landing meet it at a different radius

`deck.deck_plan` takes its corridor radius from `deck._ring_cells`, **which does not take a z**.
`lift.shaft_geometry` takes its landings from `interior.decks_in_ring(z_m=)`, **which does**. Where
they disagree the lift's doors open onto a lobby at one radius and the deck's corridor is at
another, and no body can cross:

    grey/0/22  corridor r=449.65   landing r=392.05   57.60 m apart
    blue/0/0   corridor r=211.55   landing r=197.50   14.05 m apart   (docking_bays, cnc, customs…)

14.05 m is four deck pitches. Every `blue/0/*` cluster in the register is on the wrong side of it,
including every location a player meets on arrival.

### 2.3 — the collision shell has a WALL where the render has a DOORWAY

`deck.build_deck_clusters` cuts a junction door where an axial run meets a ring corridor:
`extra_doors`, threaded through `deck_plan` into `interior.ring_arc`. **The collision path has no
such thread.** `deck.build_collision` calls

```python
d = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms)      # no extra_doors
v, t, meta = C.corridor_shell(..., doors=[x[1] for x in d["rooms"]])    # room doors only
```

so the shell a body stands on is sealed exactly where the render is open, and it stops at the
rooms-only arc rather than reaching the transit angle. Nothing had ever noticed, because **no
collision has ever been built for a joined deck** — `tools/export_station.py` writes render meshes
only, and `walkable.py` never joins two clusters.

`--selftest` measures it both ways: a ray along the spine at the transit angle passes through the
shell this module builds and is **stopped at 1.0 m** by the same corridor without the junction
door.

---

## 3. CHANGES I NEED IN FILES I DO NOT OWN

Both are small, both retire a duplication in `station/route_walk.py`, and the module works without
them today.

### 3.1 `station/deck.py` — `build_collision` should take the junction doors

`route_walk.cluster_collision` currently rebuilds `build_collision`'s corridor and splices the
rooms back on, asserting triangle-for-triangle that what it replaced was the corridor. That whole
function collapses to one call if `build_collision` gains the two arguments the RENDER path already
has:

```python
 def build_collision(schema, profile, sector, ring, deck, z_m=None,
-                    max_rooms=None, props=False):
-    d = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms)
+                    max_rooms=None, props=False, extra_doors=(),
+                    must_cover=None):
+    d = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms,
+                  extra_doors=extra_doors, must_cover=must_cover)
     v, t, meta = C.corridor_shell(schema, profile, sector, ring,
                                   degrees=d["span"], start_deg=d["lo"],
                                   radius_m=d["radius"], z_offset=d["cz"],
-                                  doors=[x[1] for x in d["rooms"]])
+                                  doors=([x[1] for x in d["rooms"]]
+                                         + [{"angle_deg": float(a),
+                                             "side": float(s)}
+                                            for a, s in extra_doors]))
```

`deck_plan` already accepts both and already appends `extra_doors` to its `doors` key **after** the
room doors, and neither argument touches its phase sweep — so the room doors do not move and no
existing caller changes behaviour. This is the same defect class as the five decks that once had
"a room whose collision carried a doorway and whose render was a sealed box", one level out: the
door decision is made once for the rooms and twice for the junctions.

**A caution that belongs with the patch:** `must_cover` DOES change the arc, and extending an arc
re-runs the phase sweep, which on **7 of 72** clusters lands the room doors somewhere else.
`route_walk.endpoints` rejects those seven rather than building a shell whose vestibules and
corridor disagree. If `build_collision` grows `must_cover`, that interaction needs its own
assertion inside `deck.py`, not a comment.

### 3.2 `station/transit_runtime.py` — `static_collision` should take `landings=`

`lift.lift_collision(landings=False)` seals every landing aperture — the generator's own negative
control, and exactly what "the column's landing doors sealed" needs. `transit_runtime.static_collision`
hard-codes it:

```python
-def static_collision(schema, profile, g):
-    sv, st, sm = L.lift_collision(schema, profile, g=g, car=False)
+def static_collision(schema, profile, g, landings=True):
+    sv, st, sm = L.lift_collision(schema, profile, g=g, car=False,
+                                  landings=landings)
```

`route_walk.column_collision` is that function with the argument threaded, and its self-test
asserts the two are triangle-for-triangle identical at `landings=True` so the copy cannot drift.
With the patch, `column_collision` deletes.

---

## 4. What the gate does

### The route is chosen from data, not written down

`routes.clusters()` → `routes.edges()` → breadth-first between two cluster nodes → the legs, with
each leg's own `kind` and the `why` string `routes.py` attaches to it. The endpoints are filtered by
the four conditions in §2 (has a landing; the landing is at the deck's own radius; extending the
corridor does not move its room doors; the deck's `.glb` was exported), and among the surviving
pairs on different decks of one sector the gate takes the one with the **shortest total walk** —
arc plus spine — so it crosses every leg kind in the fewest frames it can.

**39 of 96 clusters** qualify. The ranking counts the arc because the first version did not, and
picked `red/1/6` — whose rooms sit at 280° while red's transit spine stands at 90°, **657 m of ring
corridor before a single metre of spine**.

### The geometry is the station's own, and only the collision is rebuilt

| piece | generator |
|---|---|
| cluster shell, rooms, vestibules, prop boxes | `deck.build_collision(props=True)` |
| its corridor, with the junction aperture | `collision.corridor_shell` from `deck.deck_plan` |
| the axial spine | `collision.axial_shell` at `routes.transit_angle` |
| the column, its landings and lobbies | `lift.shaft_geometry` + `transit_runtime.build_lift` |
| the car, split so the moving piece is its own node | `transit_runtime.car_render` / `car_collision` |
| the ride | the motion table `transit_runtime` writes — `navigation.lift_ride_s`, peak asserted against the Coriolis cap |

**The column is not a test rig.** It is built at the sector's own transit angle, at the z
`tools/export_station.py` puts it at, from the same `spoke_way.ring_stack` — so the shaft this body
rides is the shaft in `column_<sector>.glb`, and its landings are that column's landings.

**The built `.glb` files are used and not rebuilt.** `station/generated/scene/station/` holds render
meshes only (2.2 GB, 70 decks, 5 columns); a body walks on the **smooth shell**, which is
`station/collision.py`'s whole finding and is why a route cannot be walked on a render mesh. So the
gate rebuilds **collision only** — 3,104 triangles for the whole route, about a minute — checks each
route deck against `station_manifest.json` and refuses a deck that was never exported, and
`--render=on` loads the built deck and column glbs as visuals over the same shells.

### The metric

    floor_m     metres covered while standing on something
    air_m       metres covered while not
    offfloor    physics frames not on a floor
    leg / wp    which leg and which waypoint it was on when it stopped

Every leg carries its own frame budget — 2.5× its length at the player's 4.2 m/s — so "it stopped"
names **where**. A single run-long budget reports a body that walked 400 m and stuck in the last
doorway identically to one that never left the spawn.

The settle frames are excluded from `offfloor` and reported separately, because
`collision.stand_at` spawns a body 50 mm above the floor **on purpose**; the drop is asserted at
≤ 100 mm instead, which is the claim actually worth making about a spawn.

---

## 5. THE JAMB, and why a waypoint in a doorway is tight

The first run of this gate walked the ring corridor, stopped **0.8 m short of the junction**, and
stood against the wall beside a 1.5 m opening for **7,093 frames**:

    ROUTELEG kind=ring  floor_m=18.974 frames=271  reached=true
    ROUTELEG kind=axial floor_m=0.799  frames=7093 reached=false

A body is steered straight at its next waypoint. The waypoint tolerance was 0.8 m — right for a
2.16 m corridor — and a door aperture is `door_width_m` = 1.5 m, half that. So the body "reached"
the junction 0.8 m off its centre line, turned for the next waypoint 199 m down the spine, and met
the jamb.

This is `deck.deck_plan`'s own documented failure, arriving from a different direction: *"A body
steering straight at the room from the corridor crosses the corridor wall 0.14 m along that line
and meets the jamb… 0.70–0.74 m of progress into every such cluster."* That was fixed by moving the
door; here the door is where it should be and the **approach** was wrong.

Two changes, both derived rather than tuned:

* a waypoint **inside** a doorway has tolerance `(door_w/2 − capsule_r) / 2` = **0.20 m** — half the
  clearance the capsule has in the aperture, leaving the same margin again;
* every doorway gets an **aim point** `AIM_M` beyond it on the same centre line, so the body walks a
  straight line through instead of turning inside it.

---

## 5b. A GDSCRIPT THAT DOES NOT PARSE DOES NOT FAIL — IT IDLES

This cost fifteen minutes of a session twice and it is worth more than the fix.

`_r_max` survived one edit and its declaration did not. Godot loaded
`scenes/route_test.tscn`, failed to attach the script, and then **ran the main loop at 60 fps
forever with nothing in it** — sleeping in `hrtimer_nanosleep`, using **1.25% of one core**,
printing nothing, exiting never. From outside, that is indistinguishable from a body walking a long
route slowly. The only tell was arithmetic: every state in the machine has its own timeout and they
sum to 18,511 frames — 308 seconds — and the process was fifteen minutes in.

It is the same shape as session 4e's renderer silently falling back to OpenGL 3 and exiting 0: the
tool did something other than what was asked, said so in one line among hundreds, and produced an
artefact (there, a PNG; here, a running process) that looked like the real thing.

Three guards, because either end alone can be defeated:

1. `route_walk.check_script()` runs `godot --check-only --script res://scripts/route_test.gd`
   **before the first launch** — three seconds, and it turns a 40-minute hang into a parse error.
2. `route_walk.run()` greps the run's own output for `Parse Error` / `Failed to load script` and
   returns that instead of "no verdict printed".
3. `route_test.gd` carries a **hard frame cap**, derived from the sum of every state's own timeout
   plus a half, and reports `stopped_why=the run's own N frame cap -- a state never ended`. Every
   state already has a timeout; a run that reaches the cap is a run whose state machine has a hole,
   and it says so instead of hanging.

And `route_walk.main()` sets `sys.stdout.reconfigure(line_buffering=True)`, because the first
diagnosis was slowed by Python's 4 KB block buffering: with output redirected to a file, a gate that
was working looked identical to one that had hung.

---

## 6. The controls

Both are required by the milestone, both **fire**, and neither is implemented in the runtime as a
switch on itself — each is a different piece of geometry, from the generator's own control
parameter.

**(a) the car parked at another landing.** The lobby, the spine and the landing aperture are exactly
as they are in the subject; the only difference is that there is **no car floor behind the
doorway**. The car is parked at the landing **furthest in radius from where the body boards,
excluding both ends of the ride** — not at the destination, because a body that falls into a car
standing at its own destination has arrived by falling, an outcome the control was meant to exclude
and cannot distinguish. `scripts/transit.gd` parks at the far end of the ride and guards it with a
state-machine rule instead; this removes the ambiguity from the setup.

**(b) every landing aperture on the column sealed.** `lift.lift_collision(landings=False)` — that
module's own negative control, walling up the landing wall — written to a second glb and swapped in
by path. A control implemented by disabling a shape in the runtime would be a control against the
runtime rather than against the geometry that ships. The body must be **stopped at the threshold**,
on the floor: not arriving, and not falling.

A third control ships with the gate and is not required by G2: `--no-doors` leaves every room's
`doorpanel_*` solid, so the body cannot enter the room at the far end. It is `walkable.py`'s own
control, one route longer.

---

## 7. THE RESULT — `python3 station/route_walk.py --walk`, verbatim

```
THE ROUTE, out of station/routes.py

  from  obs_rotundas             green/0/0 z=4204 r=281.90 landing 8
  to    earthforce_office        green/0/2 z=4104 r=289.10 landing 6

     1. ring   green/0/0 z=4200 -> spine green/0/0
        the cluster's corridor covers the transit angle 100.0 deg
     2. axial  spine green/0/0
        interior.axial_run, written this session
     3. lift   spine green/0/0 -> column green/0
        station/lift.py
     4. lift   column green/0 -> spine green/0/2
        station/lift.py
     5. axial  spine green/0/2
        interior.axial_run, written this session
     6. ring   spine green/0/2 -> green/0/2 z=4080
        the cluster's corridor covers the transit angle 100.0 deg
  wrote station/generated/scene/route/route.json -- 473 m of walking, 3,104 collision triangles

  the walk, leg by leg:
     ring       19.7 m  the ring corridor of green/0/0, obs_rotundas's door to the spine at 100 deg
     axial     198.6 m  the deck's axial spine at 100 deg, 4204 m -> the column's lobby at 4011 m
     lift        7.2 m  landing 8 -> 6, 3.4 s at up to 3.13 m/s (navigation.lift_ride_s, capped by the Coriolis limit)
     axial      98.5 m  the deck's axial spine at 100 deg, the column's lobby -> 4104 m
     ring      151.3 m  the ring corridor of green/0/2, the spine to earthforce_office's door
     room        4.5 m  through the door into earthforce_office

  PASS  THE ROUTE   491.0 m on the floor (0.00 m in the air), offfloor 0/7148, deck 8 -> 6, 0.78 m from earthforce_office
        ring       19.6 m on the floor in 280 frames  (the_ring_corridor_of_green/0/0,_obs_rotundas's_door_to_the_spine_at_100_deg)
        axial     197.8 m on the floor in 2826 frames  (the_deck's_axial_spine_at_100_deg,_4204_m_->_the_column's_lobby_at_4011_m)
        axial     101.7 m on the floor in 1453 frames  (the_deck's_axial_spine_at_100_deg,_the_column's_lobby_->_4104_m)
        ring      151.3 m on the floor in 2161 frames  (the_ring_corridor_of_green/0/2,_the_spine_to_earthforce_office's_door)
        room        3.8 m on the floor in 54 frames  (through_the_door_into_earthforce_office)

  FIRED  control: the car parked at landing 0 instead of 8
        the body walked the spine, reached the doorway and fell 28.80 m into the shaft (boarded=false,
        completed=false, stopped in `board`, 228.5 m on the floor, 28.98 m in the air, offfloor 455/3706)

  FIRED  control: every landing aperture on the column sealed
        the body walked 222.5 m and was stopped at the landing wall 1.68 m from the car's own floor,
        still on the floor (0.00 m in the air, offfloor 0/3706, completed=false, stopped in `board`:
        600 frames at the landing and the body never got into the car -- 1.68 m from where it stands)

ALL GREEN

real	5m7.529s
```

**491.0 m on the floor, 0.00 m in the air, 0 of 7,148 physics frames off it**, from a room on
`green/0/0` to a room on `green/0/2` — 200 m of axial spine, a lift ride of 7.2 m of radius across
two decks, 100 m of spine on the far side, 151 m of ring corridor and through a pressure door. The
walking distance measured (491.0 m) exceeds the route's own length (472.6 m) by 3.9%, which is the
arc a body steered at a waypoint cuts round each corner.

Both controls fire, and they fail in **different ways**, which is what makes them two controls
rather than one:

| | completed | boarded | floor_m | air_m | offfloor | where |
|---|---|---|---|---|---|---|
| the route | **true** | true | **491.0** | 0.00 | **0/7148** | arrived, 0.78 m from `earthforce_office` |
| car parked at landing 0 | false | false | 228.5 | **28.98** | 455/3706 | fell **28.80 m** down the shaft |
| landing apertures sealed | false | false | 222.5 | **0.00** | **0/3706** | **stopped at the wall**, 1.68 m from the car floor |

The parked car is a **fall**; the sealed landing is a **wall**. A single control could not tell those
apart, and a body that fell into a car parked at its own destination would look like neither.

### And it runs on the built station, not on a rebuild of it

    --render=on
    route: 1076 visual meshes from 3 built station glb(s)
    ROUTETEST completed=true ... floor_m=491.040 air_m=0.000 offfloor=0/7148
    real 2m3.208s

`green_0_0.glb` (66 MB, 782,146 tri), `green_0_2.glb` (57 MB, 680,162 tri) and `column_green.glb`
— the artefacts `tools/export_station.py` wrote, loaded unchanged over the same shells, with the
walk **identical to the digit**. The 8-minute whole-station rebuild is never run: what this module
builds is collision, 3,104 triangles, about a minute.

---

## 8. What this does NOT show

* **One route, not the station.** 39 of 96 clusters can host an endpoint at all, for the reasons in
  §2, and this walks between two of them. The gate is `--from`/`--to`-addressable and the filter
  list is printed by `--report`; rolling it over every pair is a different (and much longer) job.
* **The render is not walked.** The body stands on collision shells. The decks' render meshes exist
  and `--render=on` loads them, but nothing here judges what the route looks like.
* **There is no streaming.** The whole route's collision is resident at once — 3,104 triangles, which
  it can afford to be. A route across a sector could not be.
* **The junction aperture is this module's, not the station's.** Until §3.1 lands,
  `tools/export_station.py`'s decks still have no collision at all, and the shell that a body could
  stand on is built only here.
