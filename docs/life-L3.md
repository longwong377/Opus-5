# L3 — THEY USE THE TRANSIT

**Milestone:** `docs/MASTER-PLAN.md` L3 — *"a resident takes the lift to another deck, or the
tram along the drum, and arrives. The vehicles already move."*

**Gate:** `python3 station/agenda.py --commute` — three clock rates, three controls.
**Offline:** `--report3` (who, and the journey), `--selftest3` (13 checks, no engine),
`--census` (how many of the station's residents can do it, and why the rest cannot).

**Why it is a prerequisite rather than a later rung.** L1 measured it: of the residents baked
into the shipped `<deck>_actors.json` with both a home and a job, **not one has them on the same
deck**. Ashir walks to work because they are one of exactly two people on the station who can.
Everything else on the L-track — meals, shifts, factions in a corridor — is a schedule nobody can
execute until the lift carries somebody.

---

## 0. WHO RODE

> **Londo Tirenne**, 66, Centauri — **financier**.
> Lives in **`qtr_civilian`**, red/1/6, landing 18. Works in **`business_center`**, red/1/0,
> landing 12. Shift **14.07 EMT** for 8 h; leaves **13.57**, the start of their own
> `schedule.activity_at` TRANSIT window.
> `res:b5:business_center:centauri:1` — affiliate 1 of `business_center`, the same id stream
> `populace.roster` casts that room from.

The journey, and every leg is somebody else's geometry:

| leg | metres | what it is |
|---|---|---|
| room | 4.5 | out of `qtr_civilian` through its door at 280° |
| ring | 657.1 | the ring corridor of red/1/6, 280° → the spine at 90° |
| axial | 48.5 | the deck's spine, z 6654 → the column's lobby at 6611 |
| board | 5.9 | across the landing and into the car |
| **ride** | **21.6 of RADIUS** | landing 18 → 12 in **10.337 s** |
| alight | 1.4 | out of the car onto the landing |
| axial | 3.1 | (trimmed — see §2.2) |
| ring | 38.4 | the ring corridor of red/1/0, the spine to `business_center`'s door |
| room | 4.5 | through the door into `business_center` |
| **total** | **763.4 m of walking plus a 21.6 m ride** | |

Nothing there was chosen by hand: the person is `npc/resident.py`'s, the hours are
`npc/schedule.py`'s, the gait is `populace._walk_speed`, the corridors and their doors are
`deck.deck_plan`'s, the column is the one `tools/export_station.py` puts in `column_red.glb`, and
the ride's seconds are `npc/navigation.lift_ride_s`.

---

## 1. THE HAND-OFF, WHICH IS THE PART THE RIDE GATE DOES NOT TEST

`transit_runtime.py --ride` walks a body at a car that is **already waiting with its doors open**.
A commuter arrives at a landing where the car is somewhere else. So the machinery this milestone
adds is a **timetable**:

```
depart      120.0 s    their own TRANSIT hour
landing     716.0 s    they reach the landing and call the car
car_here    784.5 s    it arrives -- 68.5 s, because it was parked 143 m of shaft away
doors_open  785.0 s    0.47 s, the leaves' MEASURED travel over door.gd's own speed
aboard      789.9 s    they walk in
doors_shut  805.4 s    after navigation.TRANSIT_DWELL_S = 20 s of dwell
alight      815.8 s    10.337 s of ride
arrive      856.0 s    and 47 m of walking on the other deck
```

**The timetable is pure in the station clock, exactly as L1's `s(h)` is**, and for the same
reason: at ×60 nothing physical can be "run faster" and stay itself, so what is fast-forwarded is
the clock and what plays is a function of it. The car's height, the doors' opening and how far
along their route the resident should be are all read off `t`.

**And the body is still physics.** It is carried by the car's floor or it is not; it fits through
the landing aperture or it does not. That is what lets the controls fire.

**The lift is `godot/scripts/transit.gd` instantiated, not reimplemented.** That script owns the
AnimatableBody3D car, the leaves whose travel was measured off the mesh, and the carry — including
the one-frame lag between what a kinematic body is commanded and what the physics server is
holding. `life.gd` calls `embed_lift`, `lift_command` and `carry_body`; `transit_runtime.py --ride`
remains the test of the mechanism.

### Against `station/transit.py`'s own costing

| | ours | `transit.py` | delta |
|---|---|---|---|
| the ride | 10.337 s | `climb_leg` 10.337 s | **+0.000 s** |
| the walk | 636 s over 763 m of real corridor | `walk_leg` 545 s over 799 m | +91 s |
| the whole journey | 736 s | 575 s | **+161 s** |

The ride agreeing to the microsecond is the meaningful one: `navigation.lift_ride_s` and
`transit.climb_leg` share no code, and the motion table the engine plays is asserted against the
Coriolis cap before it is written.

The walk differs because `walk_leg` is a **Manhattan distance between two room centres at the
rim's gravity** and ours is the corridor a body actually walks — shorter in metres (763 against
799) and slower per metre, because `populace._walk_speed` is the gait the walk clip is animated at
and `transit.walk_speed` is the Froude speed. The remaining **69 s is waiting for a car**, which
`transit.py` never waits for: it has no `wait_leg` for a shaft.

---

## 2. FOUR DEFECTS, AND EVERY ONE OF THEM WAS A RULE THAT IS TRUE UNTIL IT IS NOT

Each was found by the gate, each is measured, and each has a negative control.

### 2.1 A ring corridor runs one way round, and the short way is often not it

`route_walk._arc_points` sweeps between two angles by the **signed shortest arc**. That is right on
a full ring and wrong on an arc. `qtr_civilian` stands at 280° and red's transit angle is 90°; the
corridor `deck_plan(must_cover=90)` builds spans **78° → 292°**, so the way round is *downward*,
−190°. The shortest way is +170°, through 0°, and **every metre of it is outside the shell**.

> Measured: the body walked **46.3 m of a 588 m arc, fell off the end of the corridor and was
> still falling 46,031 frames later**, at r = 20,188 m, with a lag of 9.7 × 10¹²³ m.

`agenda.arc_in_corridor` tries both ways and takes the shorter one that lies wholly inside the
corridor that was built, and raises if neither does. `route_walk.legs_for` has the same defect and
its own chosen route does not expose it.

**Why no gate caught it:** `route_walk.endpoints` asks whether the corridor **reaches** the transit
angle. A corridor can reach it in one direction while the route is laid in the other.

### 2.2 A spine leg must not double back through its own junction

`legs_for` walks the inbound leg *lobby → aim point at `cz − hw − AIM_M` → the junction at `cz`*,
which assumes the lobby is on the far side of the aim point. `business_center` sits at z = 6604.48,
the column at 6600, and the lobby's stand point at 6605.93 — so **the ring corridor lies between
the car and the lobby**, and that leg walks +5.9 m, back −4.5 m, then +3.1 m, crossing its own
junction twice.

> The polyline visits z = 6604.5 **three times**, so `Route.advance` — which takes the nearest
> point within a 12 m window — matched the body to a point **9 m further along than it had
> walked**, the carrot went *behind* the body, and it stalled **37.85 m short of its post**.
> 756.4 m on the floor, 0 frames off it, and no arrival.

`agenda.trim_axial` drops any axial waypoint that overshoots the junction, and `journey_for` now
asserts that **no two non-adjacent waypoints of a route are closer than a capsule radius** — a
polyline that revisits a place has two answers to "how far along is this body".

`route_walk.choose` never meets this because it **skips** any pair whose spine is shorter than two
lobby lengths. The test excluded the case; the station still has it.

### 2.3 The column's own lobby seals every ring corridor it crosses

Every landing gets one `interior.AXIAL_SECTION_M` of lobby — 9.2 m of axial corridor running away
from the shaft. A ring corridor is an arc with walls at ±1.08 m of z. Where a cluster sits within a
lobby's length of the column **the two overlap at right angles and neither generator cuts an
aperture for the other**: the lobby's side walls stand across the ring corridor, and a body that
walks out of the lift into the crossing is in a 2.16 m box.

This is not rare. Measured across the register's route-capable clusters, **13 of red's 17 sit
inside their column's lobby** — `business_center`, `casino`, `dark_star`, `medlab_red`,
`medlab_others`, `ceremonial_rooms`, `security_central`, `law_courts`, `security_posts`, `brig`,
`nightwatch`, `minipax`, `waste_red`, `water_storage`. Red's column stands at z = 6600 and those
clusters are all at z ≈ 6604–6606.

`agenda.column_collision` cuts the doorway with `collision.axial_shell`'s **own `doors` argument** —
the same generator that cuts every other door in the station, at the crossing the geometry already
has. Neither `transit_runtime.static_collision` nor `route_walk.column_collision` passes it one.

### 2.4 …and so does the spine that was built across the same corridor

Cutting 2.3's doorway changed the verdict **by nothing at all** — the same 744.2 m, the same
37.85 m short. `route_walk.build` runs a spine from the lobby's far end to the cluster's corridor
wall; on a deck that sits *on top of* the column those two are the wrong way round (6610.53 down to
6603.40), so the "spine" is a 7 m axial corridor laid **backwards, straight through the ring
corridor**, sealing it exactly as the lobby did.

There is nothing to build there: the lobby already covers that z. `build3` skips it and says so.

> **A fix that changes a failing number by zero has not been tested — it has been assumed.**
> The right response was not to keep the fix and look elsewhere; it was to ask what else could
> produce *exactly* the same stall, and there was a second tube standing in the same place.

---

### 2.5 A ROOM LEG LAID BEFORE ROOMS HAD FURNITURE IN THEM — the 5.59 m (session 4j)

**This is the defect that held L3 red for a session, and it was never the lift.** The gate
reported, deterministically at ×1, ×10 and ×60:

```
stopped 5.59 m from business_center on leg None (None) -- 788.9 m on the floor
```

It was written up twice as a lift or tracking defect and it is neither. The tell was in the phase
table rather than the verdict: **`walk_b` covered 50.7 m of a 56.41 m segment**, and the 5.71 m
missing is the length of the room leg. Then `after` covered 0.0 m in 7,201 frames — a body that
has stopped, not a body that is late.

`agenda.room_legs` built that leg as three points — the door, half a metre inside it, and the
register's centre — and the last hop is a **straight line**, laid when a room was an empty box.
Measured against the cluster's own collision shell with point-to-triangle distance (centroid
distance misses a large triangle entirely, and the first probe that used it found nothing):

| what | where | height above the deck |
|---|---|---|
| desk tops | `r=219.06`, 0.8 m of arc, z 6600.7–6605.2 | 0.72 m |
| a partition | `r=219.80 → 217.63` at fixed z | floor to head |

Clearance along the leg **never exceeds 0.53 m and is under the 0.35 m capsule for 4.5 of its
5.5 m**. The body walked to the desks and stopped. **It had arrived. There was nowhere further
to go**, and the verdict measured the distance to a post inside a desk rank.

**Two readings this corrects, and both were the investigator's.** The *target* was never the
problem — `roomnav.clear_at` puts a full capsule of room at the register's centre point. And an
endpoint disagreement was not it either: the route's last waypoint and the manifest's `post_at`
already named the same point, to 0.000 m. It was the **approach**.

`station/roomnav.py` replaces the hop with the way a person would take, searched over the room's
own collision and nothing else — no second list of where the furniture was meant to go. Height
above the deck is `floor_r − r`; a triangle is the deck, over your head, or an obstacle dilated by
the capsule; and **a `doorpanel_*` group is not a wall**, because `life.gd::_open_doors` switches
it off for a body standing at it. On `business_center`: 416 obstacle triangles, 1,394 reachable
cells, and the way in goes 0.7 m along the arc out of the doorway, 5 m down the room, then in to
the centre — 3 points / 7.50 m → 5 points / 8.54 m.

**A room whose middle is clear still gets exactly one waypoint**, at the register's own centre
point to the metre it was written at. `qtr_civilian`'s leg is byte-identical. A change that moves
what it was not asked to move cannot be reviewed.

*And the generalisation, which is the part worth carrying: a gate that reports only its verdict
hides the phase that failed. `stopped 5.59 m` named the lift's destination and said nothing; the
per-phase floor metres printed two lines below it identified the leg in one glance.*

---

## 3. THE GATE

### What it asserts

| | claim | how |
|---|---|---|
| 1 | a **named** resident leaves at **their own hour** and reaches the landing | `home_before`, `left`, and the walk_a phase's own floor metres |
| 2 | the car **comes**, they **board**, they are **carried**, they **alight on the right deck** | `boarded` at the first frame of the ride with the doors already shut; `ride_radial_floor_m` against the shaft's own rise; `end_landing` against the manifest's `to_landing` |
| 3 | the journey time agrees with `transit.py`'s costing | printed per leg, `+0.000 s` on the ride |
| 4 | **metres on the floor and frames off it**, never path length | `floor_m` accumulates only while `is_on_floor()`; the ride is measured in **radius**, because a lift on a spun ring goes radially and nothing else |
| 5 | at **×1, ×10 and ×60** | three runs off ONE manifest, differing only in `--rate` |

### THE RESULT — `ALL GREEN`, session 4j

`python3 station/agenda.py --commute`, one manifest, three rates, three controls, exit 0:

| run | on the floor | in the air | offfloor | ride | alighted | **from the post** | worst lag |
|---|---|---|---|---|---|---|---|
| ×1 | 795.5 m | 0.00 m | 0/59,068 | 21.60 m of radius | deck 12 | **0.05 m** | 0.57 m |
| ×10 | 796.5 m | 0.00 m | 0/59,068 | 21.60 m of radius | deck 12 | **0.05 m** | 0.57 m |
| ×60 | 796.0 m | 0.00 m | 0/59,068 | 21.60 m of radius | deck 12 | **0.05 m** | 0.57 m |

**`MASTER-PLAN.md` P0a's "resolve 0.05 vs 5.59 m" resolves to 0.05 m.** The before/after that
decides it is the walking phase, not the verdict line:

| | before (session 4h) | after (§2.5) |
|---|---|---|
| `walk_b` covered | **50.7 m** of a 56.41 m segment | **57.3 m** of a 57.45 m segment |
| distance from the post | 5.59 m | **0.05 m** |
| worst lag | 5.59 m | 0.57 m |

The 0.05 m is the 50 mm `roomnav` stands a body above the shell so its settle drop can be
asserted rather than excluded — i.e. the body is **on** its post, and the residue is the spawn
offset, not a miss.

### The controls

| control | what it does | why it must fire |
|---|---|---|
| `--lift=parked` | the car stays at its parking landing and is never called; the resident's timetable is unchanged | the agenda completes and the person does not — L1's second control, one vehicle along |
| `--landings=sealed` | `lift.lift_collision(landings=False)`, the generator's own negative control: every landing aperture solid | they are stopped at the door |
| `--lift=off` | no car in the shaft at all — the build before this session | nobody rides |

And all three **FIRED** on the same green run, which is what makes the three passes evidence
rather than a gate that stopped discriminating:

| control | result |
|---|---|
| `--lift=parked` | 719.23 m walked, `boarded=false`, 0.00 m of radius ridden, **41.0 m** from `business_center`, and the car moved 211.4 m without them |
| `--landings=sealed` | 719.74 m walked, `boarded=false`, **42.3 m** from the post, 0 frames off the floor — stopped at a wall, not falling through one |
| `--lift=off` | 721.45 m walked, **38.2 m** from the post, **2,917/59,068 frames off the floor** — with no car the aperture is a hole |

*The three controls end 38–42 m short while the subject ends 0.05 m short. A 5.59 m failure sat
inside that spread and read as "nearly arrived"; it was a body stopped at a desk. Distances alone
do not separate "blocked at the last metre" from "blocked at the last leg" — the phase table
does.*

---

## 4. HOW MANY OF THE STATION'S RESIDENTS CAN COMMUTE

`python3 station/agenda.py --census`.

**First, a correction to a number L1 published.** The shipped `<deck>_actors.json` carry **861
baked bodies with a home and a job — and they are 470 distinct people.** The same resident is
baked into more than one room. L1's "857 residents" is a count of bodies, not of people.

```
470 distinct residents with a home and a job
 72 can complete their commute with what exists today -- 15.3%

 209  different sectors -- needs the trunk between columns (no walkable runtime)
 135  different rings   -- needs the spoke between columns (no walkable runtime)
  35  reaching the spine moves that cluster's own room doors
  15  the landing and the deck's corridor are at different radii
   4  home and post are the same place (three live at their workplace)

 and the commutes they make, which are all one column:
  54  qtr_civilian -> business_center   red_1_6 -> red_1_0
  12  qtr_civilian -> dark_star         red_1_6 -> red_1_2
   6  qtr_civilian -> casino            red_1_6 -> red_1_1
```

**Read the shape before the size.** 344 of the 398 failures — 86% — are the same two facts:
*there is no walkable spoke between two rings and no walkable trunk between two sectors.* Both
edges exist in `routes.py` and both are marked `built`; neither has ever been walked. That is the
next milestone's work and it is one piece of geometry each, not 344 pieces.

The other 50 are per-cluster geometry: `deck_plan`'s phase sweep moves a cluster's room doors when
its corridor is extended to the transit angle (35), and the column's landing radius disagrees with
the deck's corridor radius (15). Both are `route_walk.endpoints`' own refusals and both are
fixable in the generator rather than per place.

**And all 72 depend on a doorway this session cuts** (§2.3) that the shipped station does not have.

---

## 5. CHANGES NEEDED IN FILES THIS SESSION DOES NOT OWN

1. **`station/transit_runtime.py::static_collision`** should take the crossing doorways
   `agenda.column_collision` cuts. Without it every deck within a lobby length of its column is
   reachable by lift and sealed on arrival — 13 of red's 17 route-capable clusters.
2. **`station/route_walk.py::legs_for`** should lay its ring arc inside the corridor that was
   built (§2.1) and place its spine aim point on the lobby's side of the junction (§2.2). Both are
   latent there; its own chosen route does not expose either.
3. **`station/route_walk.py --report` currently prints `NO PATH`** for the pair it chooses
   (`obs_rotundas` → `earthforce_office`), while `path_between` answers correctly for the same two
   decks' other clusters. Its `choose` picks a cluster whose ring edge is not built.
4. **`tools/export_station.py`** still welds every pressure door into one collision group — L1's
   §5.1, unchanged and still blocking.

---

## 6. WHAT L3 DOES NOT DO

* **No spoke and no trunk**, so 344 of the 470 residents still cannot get to work. The lift is one
  of three vehicles the station needs and the only one a body has now ridden to a schedule.
* **One commuter.** The runtime takes any number — the plan is per resident and the crowd buckets
  are sized from the placement list — but N > 1 has not been measured and is not claimed.
* **No return journey**, no meal, no sleep. The plan has one journey in it.
* **The car serves one passenger.** There is no queue, no call button anyone else can press, and
  the car is not shared. `SHAFT_TARGET_HEADWAY_S` exists in `navigation.py` and nothing uses it.
* **Nothing else on either deck reacts.** The corridor crowd still runs its fixed arc loop.

## 7. FILES

| file | what changed |
|---|---|
| `station/agenda.py` | the L3 half: who commutes across decks, the journey, the timetable, the crossing doorway, the gate, the census |
| `godot/scripts/life.gd` | `Agenda` is now a **plan player** — segments, car, doors, aboard — and L1's single-corridor commute is its degenerate case; the `Commuter` rides |
| `godot/scripts/transit.gd` | `embed_lift`, `lift_command`, `carry_body` and the rest of the embedded API; the ride test now calls the same carry |
| `docs/life-L3.md` | this |

**L1 is the regression test for the generalisation** — `--walk` runs the same three rates and three
controls through the new plan player and reports the same 888.0 / 889.1 / 888.5 m, `offfloor
0/50,669`, worst lag 0.57 m as it did before.
