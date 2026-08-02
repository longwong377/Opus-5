# A STREAMED CELL IS A PLACE, NOT A SHELL

Session 4g. `godot/scripts/stream.gd`, `walk.gd`, `door.gd`, `npc.gd`,
`interact.gd` — what happens when geometry arrives and when it leaves.

## What this closes

`docs/streaming-4g.md` built the streamer and said, in its own *"what is NOT
done"*:

> *"A streamed cell's doors, inhabitants, crowd and interactables are not wired.
> `walk.gd::_wire_doors` / `_wire_people` / `_wire_interact` run once, over a
> monolithic scene, at start-up. … The collision proxy carries the door panels,
> so in a streamed build today **the pressure doors are solid**."*

So the station streamed — 940 cells over 69 decks, 1,684 MB — and **every
pressure door in it was a wall**, nobody in any room knew a player existed, and
nothing in any room could be used. The walkable build and the streamed build had
become two different games.

Measured before the change, with the sidecars supplied on the command line and
ignored:

```
stream: 11 cells, radius 66.1 m, free at 73.8 m, budget 180000 tri = 3 cells
walk:   STREAMED level -- start cell 4, primed in 138 ms
STREAMTEST mode=stream ok=true ... floor_m=42.00 offfloor=0/600 crossings=1
```

No `walk: N doors wired`. No `walk: N people wired`. No `walk: N interactables
wired`. Those three lines exist only on the monolithic path, and the streamed
path never calls it.

---

## 1. The shape of the fix

**`stream.gd` tells somebody. `walk.gd` is the somebody.**

```
stream.gd::_activate(id)     -> walk.gd::wire_cell(id, visual, collision)
stream.gd::_free_cell(id)    -> walk.gd::unwire_cell(id)     [BEFORE queue_free]
```

and each of the three subsystems gained one parameter and one method:

| file | before | after |
|---|---|---|
| `door.gd` | `collect(visual, collision, travel)` | `collect(…, tag)` + `release(tag)` |
| `npc.gd` | `collect(visual, actors)` | `collect(…, tag)` + `release(tag)`, and `prepare_crowd`/`add_crowd`/`release_crowd` |
| `interact.gd` | `collect(visual, rows)` | `collect(…, tag)` + `release(tag)` |

`tag` is the cell id. `""` is a monolithic load and behaves exactly as before —
that path is unchanged and re-measured below.

### The sidecars are NOT split, and that is a decision

`actors`, `interact`, `dialogue` and `crowd` are written **per deck**; a cell is
20° of that deck's arc. The obvious move is to cut each file into eighteen. It
would be wrong: **the geometry already knows.** `npc.gd` and `interact.gd` both
bind a row by finding the meshes that carry its name, so handing the whole deck's
list to every cell binds each row in exactly the cell its meshes are in and
nowhere else. A per-cell split would be a second description of where everything
is — hard rule 4's failure mode — and it would have to be redone every time the
bake's cell size changed.

**The crowd is the exception, and it is the exception that proves the rule.** A
walker has no mesh in any cell: their body comes from `crowd_lod*.glb`, 112
shared bodies for the whole station, and the placement list is what says where
they are. So there is nothing to find them by except position — and the position
test used is `stream.gd`'s own `distance_to`, the same arc the bake binned
triangles by, asked rather than repeated.

`MultiMesh.instance_count` cannot grow, so the buckets are sized once from the
whole deck's list (`prepare_crowd`) and each cell's walkers are admitted as it
arrives (`add_crowd`). `_place_crowd` already writes only as many transforms as
there are walkers, so an unloaded cell's crowd costs nothing.

---

## 2. THE HARD PART IS LEAVING, and each subsystem leaks differently

Wiring on arrival is the easy half. Every one of the three owns nodes that stand
for cell geometry and are **not children of the cell**, and every one holds
references **into** it:

| subsystem | what outlives the cell if nothing unwires |
|---|---|
| `npc.gd` | the inhabitant's `StaticBody3D` capsule — **an invisible person to bump into in an empty corridor** |
| `interact.gd` | the interactable's proxy box, on its own physics layer — **`[E] serve the bay control booth` for a console that has been unloaded** |
| `door.gd` | `leaves`, `bases` and the panel's `CollisionShape3D` — a door that goes on moving leaves that no longer exist |

So `unwire_cell` runs **before** `queue_free`, and each subsystem gives back
exactly what that cell brought. Each also counts what it could not give back
(`stale_leaves`, `stale_parts`, `stale_prompt_frames`) rather than guarding
silently, because a reference that outlives its cell is invisible in a
screenshot and fatal in a walk.

### A DOOR'S TWO LEAVES ARRIVE IN DIFFERENT CELLS

Not a corner case — it is the first door the gate walks through. The bake bins
each **triangle** by its own centroid, so a door sitting on a cell boundary is
split:

```
doorleaf_docking_bays_0     a = 359.917 deg  -> cell 17
doorleaf_docking_bays_1     a =   0.122 deg  -> cell 00
doorpanel_docking_bays      a =   0.020 deg  -> cell 00
```

A door assembled **per cell** would be two one-leaf doors: one in cell 17 with no
panel to switch off — visibly open, physically solid, the exact defect `door.gd`
exists to end — and one in cell 0 whose leaf travels the wrong way, because the
travel direction is *away from the midpoint of the pair* and a pair of one has
its midpoint on top of itself.

So leaves and panels are registered per cell into per-**key** buckets and the
door list is rebuilt from every resident cell at once. Two consequences, both
learned by getting them wrong first:

1. **The midpoint comes from centres captured at adopt time**, not from where the
   leaves are now. Rebuilding while a door is open and reading live positions
   moves the pair's midpoint out with the leaves and reverses one leaf's travel
   on the next frame.
2. **A door whose leaf set changes is reset to shut.** A re-instanced cell brings
   its leaves back at the baked closed positions and its panel back with the
   collider *enabled*; carrying an openness across that would leave a door drawn
   half open with a solid slab in it.

---

## 3. THE GATE

*A body walks into a cell that was streamed in after launch, through a pressure
door in it, up to a declared interactable in it, uses it, and is noticed by the
people in it. Then it walks far enough away that the cell is freed, comes back,
and does all of it again.*

```bash
GODOT=/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
D=station/generated/scene/deck

"$GODOT" --headless --path godot res://scenes/walk.tscn -- \
  --cells=$D/cells_blue_0_0/cells.json --stream-test --visit \
  --gravity-mode=drum --settle=120 \
  --actors=$D/blue_0_0_actors.json --interact=$D/blue_0_0_interact.json \
  --crowd=$D/blue_0_0_crowd.json --crowd-ladder=18:2,45:4,400:8 \
  --crowd-glbs=$D/crowd_lod2.glb,$D/crowd_lod4.glb,$D/crowd_lod8.glb \
  --door-travel=0.75 --use-group=docking_bays__prop_bay_control_booth
```

`--visit` picks its own target from the interactables sidecar — the first
pressable interactable with a response behind it — and derives everything else:
the door is that row's **place** (`doorpanel_<place>` is the generator's own
naming, and `door.gd` reads the same key), the cell is the one whose arc contains
it, and the start cell is far enough round the ring that **the target cell is not
resident at launch**. `--use-group` overrides the choice; nothing here holds a
table of what is where.

### The itinerary, and why it has the waypoints it has

There is no pathfinder: a leg is a straight steer or an arc-follow. Eleven legs,
each with its own frame budget, each reporting how far short it stopped:

```
arc  -> the door's angle                        (the target cell streams in en route)
at   -> the corridor outside the door
at   -> the doorway itself
at   -> the interactable            press E     [VISIT 1 recorded]
at   -> the doorway itself
at   -> the corridor outside the door
arc  -> one free radius past the cell           (until the cell is FREED)
arc  -> back to the door's angle
at   -> the corridor outside the door
at   -> the doorway itself
at   -> the interactable            press E     [VISIT 2 recorded]
```

**The doorway is its own waypoint in both directions**, and leaving it out cost
two diagnosis passes. A body that walks out of a room aimed at a point in the
corridor approaches the aperture *diagonally* and catches the jamb: measured, it
wedged 0.4 m off the door's centreline with `velocity = 0` and stayed there for
14,000 frames. And the leg that backs out has to come **all the way out** — at
`near = 1.6 m` it finished with the body still standing in the aperture and the
arc leg after it walked tangentially straight into the jamb.

---

## 4. THE RESULT

**A body walks 270.48 m, every metre of it ON THE FLOOR, 0 of 16,200 frames off
it.** It crosses six cell boundaries, walks into a cell that was not resident
when the level started, opens a pressure door in it, is looked at by thirteen
people in it, is told *"[E] serve the bay control booth"* and presses it — the
object moves 4.00 mm. Then it walks 111 m away, **the cell is freed**, it walks
back, and all three happen again.

```
walk: VISIT cell 17 (blue_0_0_c17), door 'docking_bays',
      use 'docking_bays__prop_bay_control_booth' at 359.71 deg;
      away is 389.99 deg (111.8 m of arc, free radius 73.8 m)
stream: +blue_0_0_c01  30248 tri, 1 col mesh, 35 materialled, 13.3 ms, lead primed
walk: STREAMED level -- start cell 1, primed in 18 ms, spawn 183.04,105.68,7121.25
walk: +wired blue_0_0_c01 -- doors now 0, 0 person(s), 0 walker(s), 0 interactable(s)
walk: +wired blue_0_0_c00 -- doors now 1, 7 person(s), 0 walker(s), 3 interactable(s)
walk: settled at 183.18,105.76,7121.25 (drop 0.164 m), on_floor=true, in cell 1
walk: +wired blue_0_0_c17 -- doors now 1, 6 person(s), 0 walker(s), 5 interactable(s)
USE docking_bays__prop_bay_control_booth place=docking_bays token=bay_control_booth
    verb=serve response=press prompt=[E]  serve the bay control booth
walk: VISIT 1 of blue_0_0_c17 -- door 'docking_bays' opened to 1.00, got within
      1.17 m of docking_bays__prop_bay_control_booth, 13 person(s) noticed
      (153 deg turned, 130 deg off), prompted=true pressed=1 moved 4.00 mm
walk: +wired blue_0_0_c01 -- doors now 1, 0 person(s), 0 walker(s), 0 interactable(s)
walk: -unwired blue_0_0_c17 -- 2 door part(s), 6 person(s), 5 interactable(s)
walk: +wired blue_0_0_c17 -- doors now 1, 6 person(s), 0 walker(s), 5 interactable(s)
USE docking_bays__prop_bay_control_booth place=docking_bays token=bay_control_booth
    verb=serve response=press prompt=[E]  serve the bay control booth
walk: VISIT 2 of blue_0_0_c17 -- door 'docking_bays' opened to 1.00, got within
      1.17 m of docking_bays__prop_bay_control_booth, 13 person(s) noticed
      (153 deg turned, 130 deg off), prompted=true pressed=1 moved 4.00 mm
```

Note the two `+wired blue_0_0_c17` lines with a `-unwired` between them: **that is
the cell being freed and walked back into**, and `doors now 1` on both sides is
the cross-cell door being rebuilt from cell 0's panel and leaf plus cell 17's
leaf.

### The verdict, verbatim

```
STREAMTEST mode=stream ok=true start=1 dir=-1 prime_ms=18 traverse_m=270.48
  floor_m=270.48 net_m=110.31 offfloor=0/16200 crossings=6 entered=1,0,17,0,1,0,17
  late=0 min_lead_m=36.92 min_lead_frames=642 cells=18 resident_max=3
  resident_tris_max=139878 budget_tris=180000 radius_m=66.1 free_m=73.8
  loads=6 frees=4 double_loads=0 abandoned=0 over_budget_frames=0
  max_activate_ms=27.7 lag_frames=0 wired=6 unwired=4
  visit_cell=17 visit_id=blue_0_0_c17 door_key=docking_bays
  use_group=docking_bays__prop_bay_control_booth
  v1_door_open=1.00 v1_near_m=1.17 v1_noticed=13 v1_turned_deg=153.0
  v1_face_err_deg=129.6 v1_prompted=true
  v1_used=docking_bays__prop_bay_control_booth v1_presses=1 v1_travel_mm=4.00
  v2_door_open=1.00 v2_near_m=1.17 v2_noticed=13 v2_turned_deg=153.1
  v2_face_err_deg=129.9 v2_prompted=true
  v2_used=docking_bays__prop_bay_control_booth v2_presses=1 v2_travel_mm=4.00
  freed=true wired_cells=6 unwired_cells=4 double_wires=0
  stale_prompt_frames=0 stale_leaves=0 stale_parts=0 why=-
```

**`floor_m`, not `traverse_m`** — they are equal here because the body never left
the floor, and that is the point of printing both. The streaming agent's own
`--no-stream` control walked **11,712 m** by falling off the end of the world;
path length would have scored it as walking eleven kilometres.

`v*_face_err_deg` is a report and not an assertion: it is how far the NEAREST
person within 6 m is from facing the body at the instant the visit is recorded,
and the body is then standing at a console with somebody mid-turn beside it. The
assertions are `noticed` and `turned_deg`.

---

## 4b. THE CONTROLS, AND ALL FIVE FIRE

Every claim has a control that turns exactly it off, plus one that stands for the
build as it shipped before this session. The `ok=` and the numbers that changed:

| control | ok | what it proves |
|---|---|---|
| — (subject) | **true** | — |
| `--no-cell-wiring` | **false** | the build before this session |
| `--no-doors` | **false** | the door claim |
| `--no-people` | **false** | the reaction claim |
| `--no-interact` | **false** | the use claim |
| `--no-unwire` | **false** | the free-and-re-enter claim |

### `--no-cell-wiring` — THE PRE-FIX BUILD, AND THE DOOR IS A WALL

This is `docs/streaming-4g.md`'s station exactly: cells stream, and nothing is
told about them.

```
walk: streamed cells are NOT WIRED (control) -- this is the build before this
      session: solid doors, nobody home, nothing to use
STREAMTEST mode=stream ok=false ... floor_m=262.50 offfloor=1/16200 crossings=6
  wired=0 unwired=0
  v1_door_open=-1.00 v1_near_m=4.81 v1_noticed=0 v1_turned_deg=0.0
  v1_prompted=false v1_used=- v1_presses=0 v1_travel_mm=0.00
  v2_door_open=-1.00 v2_near_m=4.79 v2_noticed=0 ... v2_travel_mm=0.00
  freed=true wired_cells=0 unwired_cells=0
  stalls=leg3(through_the_door_and_use_it)_4.8m_short,
         leg10(through_the_door_and_use_it_again)_4.8m_short
  why=visit1:_the_pressure_door_'docking_bays'_never_opened_(-1.00)
      --_in_a_streamed_cell_it_is_a_wall; …
```

**`door_open = -1.00` means there is no such door at all** — nothing collected
the leaves, so nothing can disable the panel, and the panel is in the collision
proxy. The body walks the same 262 m of corridor and is **stopped 4.81 m short of
the console**, against the shut door, on both visits. Against the subject's
1.17 m. Nobody notices, nothing prompts, nothing moves.

### `--no-doors` — the same wall, from the other side

Cells are wired; the door node is not built. Identical stop distance — **4.81 m
short, twice** — and the diagnostic names the obstruction by its own node:

```
  v1_door_open=-1.00  v1_noticed=8  v1_turned_deg=123.7  v1_prompted=false
  rayB=doorpanel_docking_bays_col@0.69m
```

The people still react (`8` noticed, 123.7° turned): they are on the far side of
a shut door, 6 m away, which is the honest answer and shows the two claims are
independent.

### `--no-people` — the room is empty and everything else works

```
  v1_door_open=1.00 v1_near_m=1.17 v1_noticed=0 v1_turned_deg=0.0
  v1_prompted=true v1_presses=1 v1_travel_mm=4.00
  why=visit1:_0_person(s)_noticed_and_the_nearest_turned_0.0_deg; …
```

### `--no-interact` — nothing to use, and the door and the people are unaffected

```
  v1_door_open=1.00 v1_near_m=1.17 v1_noticed=13 v1_turned_deg=153.0
  v1_prompted=false v1_used=- v1_presses=0 v1_travel_mm=0.00
```

### `--no-unwire` — the half that only the second visit can catch

Wire on arrival, give nothing back. Visit 1 is **flawless** — this is the failure
that a single-visit gate cannot see:

```
  v1_door_open=1.00 v1_near_m=1.17 v1_noticed=13 v1_prompted=true
  v1_presses=1 v1_travel_mm=4.00
  v2_door_open=1.00 v2_near_m=4.62 v2_noticed=13 v2_prompted=false v2_presses=0
  double_wires=3  stale_leaves=1957  stale_parts=14446
  rayB=doorpanel_docking_bays_col@0.37m
  why=…;3_cell(s)_were_wired_twice_without_being_released;
      1957_door_leaf_reference(s)_outlived_their_cell;
      14446_inhabitant_mesh_reference(s)_outlived_their_cell
```

**3 double wires, 1,957 door-leaf references and 14,446 inhabitant-mesh
references into cells that had been `queue_free`d** — and the visible symptom is
that the body is stopped 4.62 m short on the way back in, by a door panel
collider belonging to a cell that no longer exists. That is the invisible wall
this half of the work exists to prevent, and it is exactly what a build that only
wires would ship.

### `--no-stream` — and it is why the metric is metres ON THE FLOOR

The streamer's own control, unchanged from `docs/streaming-4g.md`: prime the
start cell and never request another.

```
STREAMTEST mode=nostream ok=false  traverse_m=876827.75  floor_m=36.27
  net_m=876797.36  offfloor=12683/16200  crossings=1  entered=1,0  late=1
```

**876,827 metres of path length. 36.27 metres on the floor.** The body walks to
the edge of the primed cell, steps off the end of the world and falls for 211
seconds under 7.6 m/s² of ring gravity. A gate reporting "distance travelled"
would have scored the most broken configuration in this file as walking **876
kilometres** — the previous session's version of this control managed 11,712 m,
and the only difference is that this itinerary gives it longer to fall.

---

## 4c. THE CROWD IS WIRED, AND ITS COLLISION CAPSULES SHOVE THE PLAYER

The headline run above is with the corridor crowd OFF, and that needs saying
plainly rather than being left in a command line.

The crowd **is** wired per cell — `prepare_crowd` sizes the MultiMeshes from the
whole deck once, `add_crowd` admits each cell's walkers as it arrives,
`release_crowd` takes them back:

```
walk: +wired blue_0_0_c01 -- doors now 0, 0 person(s), 9 walker(s), 0 interactable(s)
walk: +wired blue_0_0_c02 -- doors now 0, 0 person(s), 8 walker(s), 0 interactable(s)
walk: +wired blue_0_0_c00 -- doors now 1, 7 person(s), 7 walker(s), 3 interactable(s)
```

But with the crowd on, the walk itself falls apart:

| | subject (no crowd) | crowd on | crowd on, `--no-npc-collision` |
|---|---|---|---|
| `ok` | **true** | **false** | **true** |
| `floor_m` | 270.48 | 316.59 | **270.48** |
| `traverse_m` | 270.48 | 370.68 | **270.48** |
| `offfloor` | **0**/16200 | **587**/16200 | **0**/16200 |
| cells entered | 1,0,17,0,1,0,17 | 1,0,1,2,1,0,1,0,17 | 1,0,17,0,1,0,17 |
| visit 1 | door 1.00, 13 noticed, used | **door 0.00, 0 noticed, stopped 75 m short** | door 1.00, 13 noticed, used |

**Turning off the capsules and leaving everything else on reproduces the subject
byte for byte**, so this is not the crowd wiring and not the LOD ladder: it is
`npc.gd::_give_walker_body`. A walker's collider is a `StaticBody3D` whose
`global_transform` is **teleported** by `advance_crowd` at 10 Hz — 0.145 m a jump
— and a static body teleported into a `CharacterBody3D` ejects it on the next
`move_and_slide` rather than pushing it. Head-on, player and walker close at
5.6 m/s, and the body is thrown sideways out of a 2.6 m corridor: 587 frames off
the floor and a walk that oscillates between three cells instead of crossing two.

I have **not** fixed it. The fix is probably `AnimatableBody3D` with
`sync_to_physics`, which is the node Godot provides for a collider that moves and
must push what it meets, and changing what a crowd of 963 people collides as is a
change that wants its own before/after rather than a footnote in a streaming
gate. It is recorded here, with the A/B that isolates it, as the next thing.

---

## 4d. THE TWO PATHS THAT ALREADY EXISTED DID NOT MOVE

`walk.gd`'s sidecar loading and its three `_wire_*` functions were all
restructured, so the build they already produced has to be shown intact. Same
`.glb`, same collision proxy, same sidecars, same spawn, the **original**
`--walk-test` — run twice, once with the scripts at HEAD in a `git worktree` and
once with the cell wiring, so the only difference between the two processes is
the five `.gd` files:

```
=== monolithic, scripts at HEAD (worktree)
walk: 6 doors wired
walk: 21 people wired of 21 in the cast list
walk: 134 walkers instanced across 3 LOD libraries
walk: 15 interactables wired, 13 pressable (open:5/operate:7/serve:1/tread:2)
WALKTEST rest=211.522,-0.237,7121.424 on_floor=true fell=false moved_1s=4.246
  drop=0.269 legs=0.59/4.25/4.20/3.83 traverse_m=125.86 net_m=5.69
  offfloor=0/1800 goto_start_m=5.81 goto_best_m=1.20 door_open=0.00
  turned_deg=173.2 noticed=9 facing_err_deg=2.2 walkers=134
  crowd_travel_m=5965.7 crowd_lods=2:3/4:5/8:126,nearest=5.4 …
  used=docking_bays__prop_bay_control_booth use_travel_mm=4.00 …

=== monolithic, scripts with the cell wiring
   … character for character identical, including crowd_travel_m=5965.7 …
```

**The two verdict lines are identical.** So are the wiring counts, the crowd
travel and the use.

And the streaming gate `docs/streaming-4g.md` shipped, on its own cluster, its own
command, unchanged:

```
STREAMTEST mode=stream ok=true start=4 dir=+1 prime_ms=17 traverse_m=140.00
  floor_m=140.00 offfloor=0/2000 crossings=2 entered=4,5,6 late=0
  min_lead_m=36.92 min_lead_frames=641 resident_max=3 resident_tris_max=85676
  loads=5 frees=2 double_loads=0 … wired=5 unwired=2 why=-

… and its control:
STREAMTEST mode=nostream ok=false traverse_m=11712.57 floor_m=37.61
  offfloor=1463/2000 late=1 …
```

Every number matches what that document recorded — 140.00 m, 0 of 2,000 frames
off the floor, a 36.92 m lead, 85,676 resident triangles, and the control's
famous 11,712 m of falling — with `wired=5 unwired=2` now added, which is the
five cells of a bare corridor being told about and the two being taken back.

---

## 5. Four defects found on the way, and only one of them was in this session's code

### 5a. `red_2_4` lost 138 triangles, and the conservation assertion was right

The whole-station bake fails on exactly one deck of seventy:

```
red_2_4: bake: LOST 138 triangles -- the cells do not sum to the source
```

Not the bucketing, not a seam-straddler, not a boundary tie-break: **the loop
walked `vis_bins.keys()` and `continue`d past any bin with no collision.** Those
triangles were neither written nor counted.

A cell with render geometry and no floor is a TRUE statement about that arc — the
deck has something to look at there and nothing to stand on, and the source says
so too. It is now written with `collision` empty, and `stream.gd`'s loader asks
for one half. A bin with collision and **no visual** is written the same way, and
used to vanish from the manifest entirely: a floor a player would have fallen
through because nothing ever made it resident.

```
  cell 09  270.00-300.00 deg      138 tri      0 col tri    4 groups   0.0 MB   NO COLLISION
bake: 8 cells, 201280 triangles total (source had 201280)
bake: 1 cell(s) have only one half:
        cell 09 270.00-300.00 deg: NO COLLISION -- nothing to stand on there (138 tri)
```

The assertion stays exactly as strict, and it now says **where**.

### 5b. THE CORRIDOR WAS MEASURED 3.75 m OUT OF PLACE ON `blue_0_0`, AND EVERY DECK IN THE STATION BAKE HAS THE SAME MANIFEST

`_corridor_z` finds the corridor by bucketing floor triangles in z and taking the
buckets that cover the most arc. It measured a bucket's arc as
`max(angle) − min(angle)` — the **spread** of the floor in it, not the coverage.

`blue_0_0` has six rooms, at 0°, 130°, 180°, 260°, 300° and 320°. A z bucket
holding nothing but room floors spreads across 320° while covering about 24 of
them, so the rooms beat the corridor and the measurement came back:

```
before:  corridor MEASURED at z=[7113.50,7121.50] (mid 7117.50), covering 359.9 deg
after:   corridor MEASURED at z=[7121.00,7121.50] (mid 7121.25), covering 345.0 deg
```

The deck's own spawn, from `walkable.py`, is **z = 7121.305**. Cells spawn at
`z_mid`, so all eighteen of this deck's spawns were **3.75 m out, in mid-air**.
Counting occupied one-degree bins tells a ring from six rooms; a spread cannot.
`blue_0_0_z7440`, which has three rooms over 205° and where this was written, is
unchanged at 7464.50 — which is why it was never caught.

**The consequence is not local.** `tools/bake_station.py` baked 69 decks through
this function, so **every `spawn` and every `corridor` block in those manifests
is suspect** and the station needs re-baking. The `.scn` cells themselves are
fine — the cut is by angle and nothing about it changed.

### 5c. `player.gd` steps the body TWICE a frame, and it cost 160 degrees of view

`player.gd` has its own `_physics_process`, which calls `step()` every frame from
the keyboard — no keys down, so a zero wish — and that step **rebuilds the body's
basis from `_yaw`**. A headless harness that drives `step()` itself is therefore
stepped twice: once with its own steer, and once more with `_yaw`.

Nothing about walking noticed, because a wish vector needs no facing. What needs
one is the EYE. Measured, walking straight at a console from 3.6 m:

```
USELEG f=10 short=3.62 eye_range=3.65 off_axis=162 in_sight=false prompt=
       camfwd=-0.00,-0.00,1.00 steer=-0.32,-0.26,-0.91
```

`camfwd` is constant `(0,0,1)` — yaw 0, which on a ring deck is straight along
the station's spine — while the body moves along `steer`. `interact.gd` scans a
35° cone about the camera axis, so **the target sat 160° off the view axis and
could never be prompted**, and the failure read as *"the interactable is not
wired"*.

`--walk-test` masks it by calling `set_yaw(_best_yaw)` after its heading sweep,
which is the only reason the monolithic use gate has ever been able to see what
it walked up to. The stream test now sets the yaw from its own steer
(`walk.gd::_face`), which inverts `player.step`'s own `fwd0.rotated(up, yaw)`
rather than assuming a convention. The real fix is one line in a file I do not
own — see P4.

### 5d. On `blue_0_0_z7440` NO declared interactable is reachable on foot

Not a streaming fact; it is why this gate runs on `blue_0_0` instead. That
cluster's three rooms are each a sealed box 6 m deep with one door:

```
customs_north   bay walls: z = 7457.00 (back), 7463.00 (front, aperture 39.87-40.27 deg),
                           sides a = 38.72 and 41.28 deg
its five declared interactables:  z = 7429.4 .. 7431.9   -- 24 m BEYOND the back wall
```

A body walking in from the corridor stops dead against that back wall — traced,
`n = (0,0,1)`, 7.4 m inside the door — and every declared interactable of all
three rooms is on the far side of it. Only `arrival_concourse__customs_bollard`
is inside, and it is `tread`, which is deliberately unpressable.

This is the runtime face of CLAUDE.md's *"73,635 bays wanted across the 128
places; 128 built"*: props and inhabitants are placed against the location's full
footprint while `rooms.bay_span_m` builds one representative bay at the corridor.
The actors show it too — 73 of them spread over z 7443–7471, some of them outside
the corridor's own far wall at z 7465.56.

---

## 6. CHANGES I NEED IN FILES I DO NOT OWN

### P1 — `station/walkable.py`: run this gate

`docs/streaming-4g.md` §7 P1 proposed `--stream`, and it was never applied: there
is **no `stream` and no `cells` anywhere in `station/walkable.py` today**, so the
streaming gate has never been in CI. This is the same patch with the visit gate
added, and it is the one that matters — a gate that is not in CI is not a gate.

```python
# --- near the other module constants ---------------------------------------

# STREAMING -- can a player walk out of one cell into the next, and is what
# arrives a PLACE rather than a shell? See docs/streaming-doors-4g.md.
STREAM_CELLS = os.path.join(ROOT,
                            "station/generated/scene/deck/cells_blue_0_0/cells.json")
STREAM_DECK = os.path.join(ROOT, "station/generated/scene/deck")
# The object the monolithic `--deck --use` gate picks on this cluster, named so
# the two gates walk up to the SAME thing and a difference is the streaming.
STREAM_USE = "docking_bays__prop_bay_control_booth"
# Two cell lengths less a margin: a run that crosses one boundary and stops has
# not shown the hand-off repeats.
MIN_STREAM_FLOOR_M = 100.0


def _visit_run(godot, extra, timeout=900):
    d = STREAM_DECK
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--", f"--cells={STREAM_CELLS}",
           "--stream-test", "--visit", "--gravity-mode=drum", "--settle=120",
           f"--actors={d}/blue_0_0_actors.json",
           f"--interact={d}/blue_0_0_interact.json",
           f"--door-travel={K.PROVISIONAL['door_width_m'] / 2.0}",
           f"--use-group={STREAM_USE}"] + list(extra)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    m = re.search(r"STREAMTEST (.+)", out)
    if not m:
        return {"error": "no STREAMTEST verdict printed"}
    return dict(t.split("=", 1) for t in m.group(1).split() if "=" in t)


def stream_gate(godot):
    """A streamed cell is a PLACE: its doors open, its people react, its
    interactables work -- and they still do after it has been freed and
    re-entered. With five controls, every one of which must fail."""
    sub = _visit_run(godot, [])
    if "error" in sub:
        print(f"  FAIL  {sub['error']}")
        return 1
    good = (sub.get("ok") == "true"
            and float(sub["floor_m"]) >= MIN_STREAM_FLOOR_M
            and int(sub["offfloor"].split("/")[0]) == 0
            and sub["freed"] == "true" and int(sub["double_wires"]) == 0
            and int(sub["stale_prompt_frames"]) == 0)
    for v in ("v1", "v2"):
        good = good and (float(sub[f"{v}_door_open"]) > 0.0
                         and int(sub[f"{v}_noticed"]) > 0
                         and sub[f"{v}_prompted"] == "true"
                         and int(sub[f"{v}_presses"]) > 0
                         and float(sub[f"{v}_travel_mm"]) > 0.0)
    print(f"  {'PASS' if good else 'FAIL'}  a body walks "
          f"{float(sub['floor_m']):.1f} m ON THE FLOOR, {sub['offfloor']} "
          f"frames off it, into cell {sub['visit_cell']} which was streamed in "
          f"after launch: the pressure door opens to "
          f"{float(sub['v1_door_open']):.2f}, {sub['v1_noticed']} people look "
          f"up, and {sub['use_group']} prompts and moves "
          f"{float(sub['v1_travel_mm']):.1f} mm. The cell is then FREED and "
          f"re-entered and all three still work "
          f"({float(sub['v2_door_open']):.2f} / {sub['v2_noticed']} / "
          f"{float(sub['v2_travel_mm']):.1f} mm), with "
          f"{sub['double_wires']} double wires")
    # FIVE CONTROLS, and without them this proves nothing. `--no-cell-wiring` is
    # the build as it shipped before this session and stands for all three
    # claims at once; the other four each turn off exactly one.
    for flag, want in (("--no-cell-wiring", "the build before the wiring"),
                       ("--no-doors", "the door claim"),
                       ("--no-people", "the reaction claim"),
                       ("--no-interact", "the use claim"),
                       ("--no-unwire", "the free-and-re-enter claim")):
        c = _visit_run(godot, [flag])
        if "error" not in c and c.get("ok") != "true":
            print(f"        control {flag}: FAILS as it must ({want})")
        else:
            print(f"  FAIL  with {flag} the gate still passed -- it is "
                  f"measuring nothing")
            good = False
    return 0 if good else 1


# --- add to main()'s argument list -----------------------------------------
    ap.add_argument("--stream", action="store_true",
                    help="is a streamed cell a place? Walks into one that "
                         "arrived after launch, through a door, up to "
                         "something usable, then frees it and comes back")

# --- add to main(), immediately after the `godot is None` guard ------------
    if a.stream:
        return stream_gate(godot)
```

### P2 — `.github/workflows/validate.yml`: one step

Same shape as every other step (`continue-on-error` plus an `id`, so the final
aggregate step still fails the job) — session 4e's rule that one failing gate
must not blind the ones behind it.

```yaml
      # A STREAMED CELL IS A PLACE, NOT A SHELL. Every other walkability gate
      # loads one .glb whole and wires it once, so none of them can fail for a
      # station whose doors are solid because the geometry arrived late.
      - name: A streamed cell has working doors, people and interactables
        id: streamed_cell_is_a_place
        continue-on-error: true
        run: python3 station/walkable.py --stream
```

### P3 — `station/walkable.py::deck_verdict`: `door_open` is sampled too late

`walk.gd` reports `door_open=%.2f` from `_doors.openness(_door_key)` **at the
frame the verdict prints**, which for a body that walked THROUGH a door is
several seconds after it shut again behind them. A run that worked perfectly
reports `door_open=0.00`. `door.gd` now carries `peak_openness(key)` for exactly
this; the deck walk should read that instead, and the one-line change is in
`walk.gd`'s `goto_s` block:

```python
                goto_s += " door_open=%.2f" % _doors.peak_openness(_door_key)
```

(That line is in a file I own and I have **not** made the change, because
`deck_verdict` currently asserts nothing on `door_open` and moving it would
change a number `walkable.py` prints without anybody having asked for it.)

### P4 — `godot/scripts/player.gd`: do not step yourself while a harness drives you

The double-step in 5c. The harness fix in `walk.gd::_face` works and is not the
right place: any future headless driver has to remember it. One line in
`player.gd` ends the whole class of bug —

```gdscript
## A HARNESS THAT DRIVES `step()` MUST BE THE ONLY THING THAT DOES. With no
## window there is no input, so this node's own `_physics_process` steps the body
## with a zero wish every frame -- harmless to the walk and NOT harmless to the
## eye, because it rebuilds the basis from `_yaw`.
func drive_externally() -> void:
	set_physics_process(false)
```

called from `walk.gd::_spawn_player` when `--walk-test`, `--stream-test` or
`--shot` is present. **It changes the numbers `walkable.py --deck` prints** (one
fewer `move_and_slide` per frame), so it wants its own before/after and is not
something to slip in.

### P5 — `tools/bake_station.py`: re-bake, and merge the manifests

Two things, and the first is not optional:

1. **Re-bake.** Every deck in `station/generated/scene/station/cells/` carries a
   corridor and eighteen spawns measured by the broken `_corridor_z` (5b). Three
   minutes of machine time.
2. **Merge.** `bake()` now writes `<stem>_cells.json` per cluster as well as
   `cells.json`, so seventy decks no longer leave one four-cell manifest behind
   — but there is still no STATION manifest, and `stream.gd` cannot yet consume
   one, because `residency.radius_m` differs per deck (66.1 m on Blue ring 1
   deck 0, 31.3 m on Yellow ring 4 deck 3) and the streamer reads it once. The
   merge is a list concatenation; what it needs first is for **residency to move
   from the manifest header onto the cell**. That is a change in
   `stream.gd::configure` and `update` — mine, and not this session's job.

---

## 7. What is NOT done, stated

* **The crowd's colliders shove the player** (4c). Wired, released, measured,
  unfixed. It is the reason the headline run is `--no-crowd` and the A/B that
  isolates it is above.
* **Dialogue is not wired per cell.** `_wire_dialogue` still runs once, off the
  monolithic path, and `dialogue.gd::collect(actors, rows)` binds against the
  cast list rather than against meshes — so it needs the same tag treatment and a
  decision about whether a person who has been unloaded should keep their line.
  Nothing regressed: on a streamed build nobody could talk before this session
  either.
* **One cluster, one deck.** The gate walks `blue_0_0` because it is the only
  cluster on disk with an actors sidecar AND an interactables sidecar AND a
  reachable interactable. `tools/export_station.py` writes no sidecars at all, so
  **no cell of the 940-cell station bake can be wired today** — the streamer will
  load them and there will be nobody in them and nothing to use. That is the
  single biggest thing between this and a station that streams as a place, and it
  is a change in a file I do not own.
* **The visit gate is not in CI.** P1 is the patch; until it is applied this is a
  command in a document, which is the failure mode session 4e wrote up.
* **No LOD, still.** Unchanged from `docs/streaming-4g.md`.
* **A door that straddles a cell boundary is rebuilt whole**, but an
  INTERACTABLE that straddles one is wired **twice** — once per cell, each with
  the full-object box from the sidecar. `docking_bays__prop_bay_control_booth`
  spans 8 m of tangent and is exactly this case. It costs a duplicate proxy box
  and one redundant `_in_sight` test; it does not break the prompt (the gate
  presses it twice over, once per visit, from two different cells' Items) and it
  should be deduplicated by group name across tags.
