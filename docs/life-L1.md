# L1 — SOMEONE GOES TO WORK

**Milestone:** `docs/MASTER-PLAN.md` L1 — *"one named resident leaves their quarters at their own
start hour, walks a `routes.py` path, and is at their post. Asserted headlessly."*

**Status: DONE.** `python3 station/agenda.py --walk` is the gate. Three clock rates, three
controls, and every control fires.

---

## 0. WHO WALKED

> **Ashir**, 111, Minbari, from Minbar — **diplomat**.
> Lives in the **ambassadorial suites**, green/0/1, at 24°.
> Works in the **League delegations**, green/0/1, at 200°.
> Shift **06:39 EMT** for 7 hours. Leaves **06:09** — the start of *their own*
> `schedule.activity_at` TRANSIT window, not a departure this file invented.
> `res:b5:league_delegations:minbari:33` — affiliate 33 of `league_delegations`, which is the
> same id stream `populace.roster` casts that room from.

They walk **887.9 m** of ring corridor at **1.469 m/s** — `populace._walk_speed`, the gait their
own walk clip is animated at, at the deck's own 10.061 m/s² — taking **604 s = 10.1 min**, which
fits inside the schedule's 30-minute transit window with 19.9 min to spare, and puts them at their
desk **20 minutes before the shift starts**.

Nothing in that paragraph was chosen here. The person comes out of `npc/resident.py`, the hours out
of `npc/schedule.py`, the gait out of `populace.py`, the gravity out of `interior.gravity_at`, the
corridor radius and both door angles out of `deck.deck_plan`, and the connectivity claim out of
`routes.py`.

---

## 1. THE ARCHITECTURAL DECISION, AND THE NUMBER THAT SETTLES IT

People exist two ways on this station and only one of them can commute:

| | what it is | where the body lives | cost in the deck `.glb` |
|---|---|---|---|
| **baked actor** | welded into the merged room mesh at one hour | `<deck>.glb` | **primitives** |
| **instanced walker** | a transform against `populace.station_crowd_library` | `crowd_lod*.glb` | **none** |

A resident who goes to work must be a **walker all day**. They cannot wink out of their quarters
and wink in at their post, and a baked body is *only* capable of being shown or hidden — which is
exactly what `life.gd`'s `Director` did, and exactly what its own comment admitted: *"the runtime
cannot create a person, so a room busier than its bake hour is capped."*

**So a commuter is instanced.** The brief asked whether moving N residents onto that path breaks
`budget.BUDGETS["deck_primitives"] = 600`, and the answer is the opposite of the one it expects.
Measured off the 70 shipped `.glb`s with `budget._glb_primitives` (`agenda.py --primitives`):

| deck | primitives | of which people | baked actors | instanced walkers | per baked actor | per walker |
|---|---|---|---|---|---|---|
| `red_0_0` | **3,488** | 2,850 | 566 | 238 | 5.04 | **0.00** |
| `blue_0_0` | **1,824** | 547 | 118 | 444 | 4.64 | **0.00** |
| `green_0_0` | **713** | 396 | 81 | 39 | 4.89 | **0.00** |
| `green_0_1` (this one) | 150 | 35 | 7 | 11 | 5.00 | **0.00** |
| **70 decks** | **14,213** | **5,034** | **1,060** | **1,444** | **4.75** | **0.00** |

**A baked actor costs 4.75 primitives. An instanced walker costs zero.** 1,444 walkers are already
shipped across the station and contribute nothing to any deck's primitive count, because every
walker of one `(species, lod, phase)` shares one MultiMesh — 112 for the whole station.

**Three of the 70 shipped decks are already over the 600 bound, and the crowd is not why.**
`red_0_0` ships 3,488 primitives with 2,850 of them people, from 566 *baked* actors. Moving
residents to the instanced path is the only lever that gives those primitives back; it does not
spend any.

**Before and after, for this milestone:** `green_0_1` ships 150 primitives, 35 of them people.
Ashir is not among them — they are the 34th affiliate of `league_delegations`, not one of the seven
baked bodies — and after this change they still are not: the deck `.glb` is **unchanged, byte for
byte**, and Ashir is one transform in the `crowd_human_*` bucket. **150 → 150.** The commuter is
free at the deck level and costs one row in `<deck>_crowd.json`.

The measured runtime cost of the drawn body is in `crowd_m` in the verdict: with `--crowd=on` the
instanced walker covered **888.5 m**, which is `floor_m` to three figures, because it is *slaved to
the physics capsule* rather than integrating a second copy of the journey. One answer to "where is
this person", not two.

---

## 2. WHAT MOVES, AND WHAT DOES THE MOVING

`life.gd`'s design rule is *"an inhabitant's state is a PURE FUNCTION of the station clock"*, and it
is right. It is also the **only** design that survives requirement 5 — a schedule that works at 1×
and not at 60× is not a schedule, and no character controller walks 88 m/s under its own steam. So
the milestone splits in two:

```
THE AGENDA IS PURE IN THE HOUR.   Agenda.s_at(h) -- how far along the route the resident
                                  should be. It teleports freely, and it is identical at
                                  x1, x10 and x60 by construction.

THE BODY IS PHYSICS.              A CharacterBody3D on the station's own collision shell,
                                  steered at a carrot on the route ahead of min(s_agenda,
                                  s_body). It cannot walk through anything.
```

**That split is what makes the second control able to fire at all.** With the pressure doors sealed
the *agenda* still completes all 887.9 m and the *body* is still in the bedroom, 570 m from its
post. A runtime that placed people from `s(h)` would have reported a successful commute through a
locked door and no gate in this repository could have caught it.

### A faster clock needs more physics, not bigger steps

This is the finding the milestone cost, and it is stated rather than hidden.

At ×60 a resident covers 88 m of station per real second. At 60 Hz that is **1.9 m a physics tick** —
wider than the 1.5 m pressure door they have to walk through and four times their own capsule. The
first run of this gate did exactly that: it walked **6.09 m**, wedged its capsule against the
bedroom wall exactly one capsule radius short of it, and reported `on_floor=true` for 604
consecutive frames.

So `life.gd` raises `Engine.physics_ticks_per_second` **with** the clock rate — 60, 600, 3,600 —
and the body's step in *station* time is then **24 mm at every rate**. That is what makes the three
runs comparable rather than merely all green.

**The cost is that the run takes the same number of physics ticks at every rate: ×60 buys station
time, not wall time.** All three runs are ~50,700 ticks. Any claim that a simulation "runs 60×
faster" without saying what happened to its tick rate is a claim that something was skipped.

### The two follower defects, both found by measurement

1. **A carrot on the AGENDA is not a carrot on the ROUTE.** Steering at `point_at(s_agenda +
   lookahead)` at ×60 aims at a point 44 m further along — and 44 m along a ring corridor from a
   bedroom doorway is a point through two walls. The carrot is now placed ahead of
   `min(s_agenda, s_body)`, where `s_body` is the body's *own* monotone progress along the polyline.
2. **A target 50 mm above the floor is a target a standing body can never reach.**
   `walkable.room_target` sits 50 mm above the shell on purpose, and `player.step` flattens its
   steer onto the floor plane — so a body 58 mm from that point walks at full speed in an
   essentially arbitrary direction, for ever. Measured: **229 m of dither in the 7,195 ticks after
   Ashir had reached their desk**, scored as commuting. `room_target`'s own docstring records the
   same defect one order up ("an irreducible 0.85 m … a body standing on the deck can never close a
   radial offset"). The dead zone is now measured on the floor plane.

The lookahead itself is **derived, not chosen**: a right-angle turn taken with a carrot `d` metres
along the route is cut by at most `d/√2`, and the only right angles on this route are where the ring
corridor meets a doorway, where a capsule has `door_w/2 − r` of clearance. So the largest carrot
that cannot put a shoulder into a jamb is `√2 ×` that clearance — **0.566 m**, both numbers the
kit's.

---

## 3. THE GATE

```
python3 station/agenda.py --report      who commutes where, no engine
python3 station/agenda.py --primitives  the baked/instanced cost table
python3 station/agenda.py --selftest    everything answerable offline (13/13)
python3 station/agenda.py --walk        THE GATE: three rates, three controls
```

### What it asserts

| | claim | how |
|---|---|---|
| 1 | a **named** resident is **at home before** their start hour | `home_start_m ≤ 1.5 m` and `pre_floor_m < 0.5 m` over the 120 station-seconds before departure |
| 2 | at their departure hour they **leave**, along a route `routes.py` produced | `walk_floor > half the route`, and the route is `routes.py`'s own claim about the two places |
| 3 | they **arrive at their post** and **are there after** | `arrive_m ≤ walkable.ARRIVED_M`, and `post_end_m ≤` the same 120 station-seconds later |
| 4 | **metres on the floor** and **frames off it**, never path length | `floor_m` accumulates only while `is_on_floor()`; `air_m` and `offfloor` take the rest |
| 5 | it works at **1×, 10× and 60×** | three runs off ONE manifest, differing only in `--rate` |

Plus the two that keep 4 honest: `settle_drop_m` (the body really did land on the shell it was
spawned 50 mm above) and `lag_m` (the body **tracked** the agenda rather than being placed by it —
a placed body reads 0.00 for ever and a shut-in body reads the whole route).

### Results — `python3 station/agenda.py --walk`, 2 min 28 s, ALL GREEN

| clock | on the floor | in the air | off-floor frames | from the post | worst lag | ticks | drawn body |
|---|---|---|---|---|---|---|---|
| **×1** | **888.0 m** | 0.00 m | **0 / 50,669** | **0.07 m** | 0.57 m | 50,759 | 888.0 m |
| **×10** | **889.2 m** | 0.00 m | **0 / 50,669** | **0.06 m** | 0.57 m | 51,569 | 889.2 m |
| **×60** | **888.5 m** | 0.00 m | **0 / 50,669** | **0.06 m** | 0.57 m | 56,069 | 888.5 m |

Route length is 887.9 m, so the walk is **+0.1 m to +1.3 m** on it — the lookahead. The spread
across the three clock rates is **1.2 m in 888, or 0.14%**, and the phase frame counts are
*identical* at all three: 7,204 before, 36,270 commuting, 7,195 after. That is the property the
milestone asks for, and it is the same simulation three times rather than three that all happened
to pass.

`settle_drop_m = 0.041` — the body landed on the shell it was spawned 50 mm above.
`crowd_m` equals `floor_m` to three figures at every rate, because the drawn instanced walker is
**slaved to the physics capsule** rather than integrating a second copy of the journey.

Per phase, at ×1:

```
before         0.0 m on the floor in 7,204 frames    at home, standing still, 120 station s
commute      888.0 m on the floor in 36,270 frames   06:09 -> 06:19, the whole route
after          0.0 m on the floor in 7,195 frames    at the desk, standing still, 120 station s
```

### The controls — all three fire

| control | what it does | result |
|---|---|---|
| **the clock stopped** (`--rate=0`) | the scene, the body and the route are identical; the clock does not advance | **FIRED** — `floor_m = 0.00`, the agenda got **0.0 m of 888**, `left=false`, `arrived=false`. They never leave. |
| **the route unavailable** (`--doors=sealed`) | every `doorpanel_*` in the shell stays solid — `deck.build_collision`'s own geometry, with the runtime's door-opening off | **FIRED** — the **agenda completed all 887.9 m** and the **body walked 3.66 m**, inside its own quarters, and finished **570.5 m from its post**. `arrived=false`, `air_m=0.00`. **They do not teleport.** |
| **the pre-fix build** (`--agenda=off`) | `life.gd` as it was: the Director shows and hides baked bodies, the commuter is placed where they were baked and never steered | **FIRED** — `floor_m = 0.00` over all 50,669 ticks. **Nobody moves at all.** |

The second one is the load-bearing control and it is worth reading twice: **the agenda finished the
commute and the resident did not.** That is only possible because the body is physics and the
agenda is arithmetic; a runtime that placed people from `s(h)` would have walked Ashir through a
locked pressure door and reported a green commute.

---

## 4. WHAT THE ROUTE IS, AND WHY IT IS ONE CORRIDOR

`routes.py` reports the station as **one foot-connected component of 171 clusters**, and Ashir's
quarters and post are both in it. Their two places sit in the *same z-cluster*, `green/0/1 z=4080`,
which `routes.clusters` says in as many words is a connection: *"two places in one cluster are
already joined by the ring corridor that serves them."* The route is laid **on that corridor** —
the arc faceting is `route_walk.RING_STEP_DEG`'s sagitta rule, the doorway waypoints and their
tolerances are `route_walk.door_tol_m`'s, and the radius and both door angles come out of the
`deck.deck_plan` call `tools/export_station.py` made to write the shell that is on disk.

**L1 is not L3.** A commute that crosses decks needs the lift, and *"they use the transit"* is the
milestone after next. What L1 asks for is a resident who **walks**.

And there is a finding in that constraint, below.

---

## 5. CHANGES I NEED IN FILES I DO NOT OWN

### 5.1 BLOCKING — `tools/export_station.py` welds every pressure door shut

`deck.build_collision` emits each closed pressure door as its own span — `doorpanel_<place>` —
*precisely* so a runtime can switch exactly that off when the door opens. `walk.gd` and
`route_test.gd` both depend on the name. `tools/export_station.py` then writes the whole shell as
one group:

```python
cgroups = [("collision", 0, len(ct))]
```

so **every `<deck>_collision.glb` on disk has its pressure doors welded into the shell and no way to
address one**. Verified by reading the artefact: `green_0_1_collision.glb` contains exactly one
mesh, named `collision`. A body cannot leave a room on the shipped collision, on any of the 70
decks. Nothing caught it because no gate has ever walked on `<deck>_collision.glb` — `walkable.py`
and `route_walk.py` both rebuild their own shells.

`agenda.py` works around it by re-emitting the same `build_collision_clusters` output with its spans
kept, and **asserts triangle-for-triangle against the manifest's own `collision_tris`** so the
shell it walks on cannot drift from the one that shipped. The patch that retires the workaround:

```python
# tools/export_station.py, in main(), replacing:
#     cgroups = [("collision", 0, len(ct))]
# THE PRESSURE DOORS MUST STAY ADDRESSABLE. `deck.build_collision` emits each
# closed door as its own span so a runtime can disable exactly that shape; one
# group welds them into the shell and seals every room on the deck.
cgroups = [("collision", 0, len(ct))]
_base = 0
for _m in cmeta["clusters"]:
    for _nm, _lo, _hi in _m.get("groups", ()):
        cgroups.append((_nm, _base + _lo, _base + _hi))
    _base += _m["triangles"]
```

(`collision.write_obj` resolves last-span-wins per triangle, so the wide `collision` span keeps
everything the named spans do not claim. This is the same shape as
`station/agenda.py::write_collision`, which is where it was tested.)

It requires a re-export of the 70 decks, which is why it is written here rather than applied.

### 5.2 `station/walkable.py` and `station/route_walk.py` — every headless gate runs 100× slower than it needs to

Neither passes `--fixed-fps` to Godot, so the headless main loop is throttled to real time.
Measured on this box with an empty `SceneTree`:

| | frames/s |
|---|---|
| `godot --headless` | **145** |
| `godot --headless --fixed-fps 60` | **≈300,000** |

That is a fixed 6.9 ms of *waiting* per iteration. `walkable.py --stream`'s visit gate runs 16,200
frames — **112 s of pure throttle**; `route_walk.py --walk`'s route was 7,093 frames — 49 s; the
×1 run of this gate would have been **350 s** of it. The fix is one argument in each
`subprocess.run` command list:

```python
cmd = [godot, "--headless", "--fixed-fps", "60", "--path", engine_root, ...]
```

`--fixed-fps N` makes the main loop use a fixed frame time instead of syncing to real time; the
physics tick rate and every delta are unchanged, so no measurement moves.

### 5.3 `station/npc/navigation.py` — a unit trap between two modules that are used together

`navigation.walk_speed(g, species)`'s `g` is **in multiples of g** (its own docstring says so, and
`interior.gravity_at` returns that). `populace.place_gravity()` returns **m/s²**. Calling
`walk_speed(place_gravity(k))` gives 4.78 m/s for a Minbari instead of 1.57 — a plausible-looking
number that is 3× wrong, with no error anywhere. Nothing in the repo currently makes the mistake
(`transit.py` and `npc/security.py` both pass `gravity_g`/`floor_g`), but the two modules are
adjacent in every NPC path and the parameter is a bare `g: float`. Suggested: rename to `g_rel` and
assert `g < 5.0` with a message naming the unit.

### 5.4 `station/npc/resident.py` — a commuting resident is "at" a transit place

`where_at` maps `Activity.TRANSIT` to `res.commutes_via`, so for the whole half hour Ashir is
commuting, the register says they are at `radial_tubes`. That is the right answer for a system that
has no journeys and the wrong one now that there is one. L1's agenda replaces it for the resident
it drives, but nothing else knows. Suggested for L2/L3: `where_at` gains an optional agenda, or
returns `(place, fraction)` for TRANSIT so a caller can ask *between which two*.

---

## 6. FINDINGS

### 6.1 Only two residents on the whole station can walk to work

`agenda.py --report` enumerates every resident whose quarters and post are on **one assembled
deck**, with a name, and with a transit window their own schedule actually shows them commuting in.
The list is **two people**, both diplomats on `green/0/1`:

```
Ashir        minbari  diplomat  green_0_1  ambassadorial_suites -> league_delegations  shift 06.65
Ko Keffer    human    diplomat  green_0_1  league_delegations   -> ambassadorial_suites shift 10.01
```

The pre-filter behind it is cheap and exact — `resident.home_for` and `resident.workplace_places`
are pure functions of `(species, role)`, so 19 roles × 14 species is 266 questions rather than
2.7 million `Resident` records. It finds **six** `(species, role, home, job)` pairings whose two
ends share a deck; all six are diplomats and all six are `green/0/1`.

Across the 857 residents actually baked into the shipped `<deck>_actors.json` sidecars who have both
a home and a job, **not one** has them on the same deck. The commonest commutes on the station are

```
112  qtr_personnel (blue/0/4) -> security_posts (red/2/2)
112  qtr_civilian  (red/1/6)  -> zocalo         (red/0/0)
 93  qtr_civilian  (red/1/6)  -> shops_kiosks   (red/0/0)
 83  qtr_civilian  (red/1/6)  -> business_center(red/1/0)
```

**Every one of them needs a lift, and most need a spoke as well.** That is a fact about the station
rather than a defect — quarters and workplaces *should* be in different sectors — but it means
**L3 is not optional**: without transit, 99.8% of the station's residents cannot execute their own
schedule at all. L2 (meals and sleep) is reachable without it, because `eats_at`/`plays_at` are
locally biased; L1 was reachable by exactly two people.

### 6.2 The pressure doors on disk (see 5.1)

Every room on all 70 shipped `<deck>_collision.glb` is sealed. The station is walkable in its
corridors and no body can enter a room on the collision that ships. This is the largest thing found
this session.

### 6.3 `life.gd --life-test`'s frame-budget check was already red

Not caused by this session, and verified as such: `git show HEAD:godot/scripts/life.gd` run from a
temporary path fails the same check.

```
FAIL 2,000 bodies update inside the crowd's borrowed frame share
     HEAD           3,540 us worst of 24 hours against 3,167 us
     with L1        3,332 us / 5,215 us on two runs of the same binary
```

Nothing in this session touches `Director.apply` — `Clock.hours_abs` is a new method the Director
never calls. The three numbers above also span **57%** on one machine with one build, so the check
is a wall-clock measurement on a contended four-core container and its verdict depends on what else
is running. (The 5,215 µs run was uncontended and the 3,332 µs run was not, which is the wrong way
round.) It is measuring the box, not the code. Left alone; `life.gd`'s *other* nine checks all pass,
including the purity gate and its integrator control.

### 6.4 `budget.py`'s deck-primitive bound is a bound on a file nobody ships any more

`budget.py` reads `station/generated/scene/deck/blue_0_0.glb` — a single-cluster build in the old
`deck/` directory. The station that ships is `station/generated/scene/station/*.glb`, and measured
there, **3 of 70 decks are over the 600 bound**, worst `red_0_0` at 3,488. The gate is green because
it is looking at the wrong artefact. (Not fixed here: `budget.py` is not mine.)

---

## 7. WHAT L1 DOES NOT DO

Stated plainly so nobody reads more into it than is there.

* **Two people can do this and 249,998 cannot** — see 6.1. L1 is the mechanism, not the coverage.
* **The commute is one corridor.** No lift, no spoke, no tram. That is L3.
* **There is no return journey**, no meal, no sleep. The agenda has one leg. That is L2.
* **Nothing else on the deck reacts.** The 11 corridor walkers on `green/0/1` still run their fixed
  arc loop; `npc.gd::advance_crowd` is untouched.
* **The gate runs one commuter.** `npc.gd::add_commuter` and `drive_commuter` are written to take
  any number, and the MultiMesh buckets are sized by `prepare_crowd` from the whole placement list,
  so N commuters is N transforms — but N > 1 has not been measured and is not claimed.
* **`life.gd`'s `Director` is untouched** and still shows and hides the baked cast. A commuter is a
  different kind of person from a room occupant, and this milestone did not merge them.

---

## 8. FILES

| file | what changed |
|---|---|
| `station/agenda.py` | **new** — chooses the commuter, lays the route, writes the shell and the manifest, runs the gate, reports |
| `godot/scripts/life.gd` | `Clock.hours_abs`, `Route`, `Agenda`, `Commuter`, `--agenda-test` |
| `godot/scripts/npc.gd` | `Walker.free`/`pos`/`fwd_free`/`speed_ms`, `add_commuter`, `drive_commuter`, and `_walker_xform` honouring a free transform |
| `docs/life-L1.md` | this |

Read-only and unchanged: everything in `station/` except `agenda.py`, every other `.gd`, and every
generated artefact under `station/generated/scene/station/`. `agenda.py` writes only to
`station/generated/scene/agenda/` (gitignored). Neither `tools/export_station.py` nor
`tools/bake_station.py` was run.

`station/npc/agenda.py` was offered and is **not** written: everything the Python side needed was
already in `resident.py`, `schedule.py`, `navigation.py` and `populace.py`, and a fifth module
between them would have been a place for a second copy of the shift, the gait or the home to live.

**CI:** the gate is not added to `.github/workflows/validate.yml`. `CLAUDE.md`'s session-4d ruling
is *"keep the existing gates green, do not grow them"*, and the workflow is not this session's file.
It is a 2.5-minute run when the box is quiet; the step, if it is ever wanted, is
`python3 station/agenda.py --walk` with the same `continue-on-error` + recorded-outcome pattern the
other 41 steps now use.
