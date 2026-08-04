# CAN A BODY GET INTO EVERY NAMED PLACE, AND STAND UP?

**Gate:** `python3 station/roomnav.py --station`
**Reproduction for one place:** `python3 station/roomnav.py --place <key> --map`
**Session:** 4k. **Status: 101 of 116 yes, 15 no, exit 1** — re-run against the tiled station (§9). The figures in §3 and §6 are superseded; read §9 first.

---

## 0. WHY THIS EXISTS

L3's commute stopped a named resident **5.59 m from their post**, and the cause was that the
last leg of the route — doorway to the register's centre — was a straight line laid before
rooms had furniture in them. `station/roomnav.py` replaced it with the way a person would
actually take, searched over the room's own collision.

**That fixed one room.** Whether the same defect sat in the other 127 is a different question,
and `CLAUDE.md`'s session-4h lesson is exactly that *a fix applied to an instance and not to
the rule is a fix that will be needed again*. So `--station` asks every named place the
question its own commute leg asks: **from this room's own doorway, over this room's own
collision, is there anywhere a capsule can stand — and can it get there?**

---

## 1. THE FIRST RUN PASSED 116 OF 116, AND FOURTEEN OF THEM WERE WRONG

This is the finding worth carrying, because it is about the gate rather than the station.

The first criterion was *"is anything standable reachable from the doorway"*. A 2×2 pocket
beside a door is something, so it passed. Fourteen places reported **`reach 4` — 0.16 m² of
standable floor** — and the gate called them fine.

**Read the shape before the size.** Fourteen unrelated places reporting *identically* `reach 4`
is one cause, not fourteen; and all fourteen sat at exactly `z_half − 0.1` from their own
centre, which is the topmost row of the grid — the doorway. `vorlon_berth`'s occupancy map
shows it in three lines:

```
z=7118.90 |....###############oDoo###############....|   the pocket, 4 cells
z=7118.70 |....##################################....|   SOLID, no aperture
z=7118.50 |....####......##......################....|   the room's own floor
```

The criterion is now **room-relative**: reaching neither the room's middle nor anything within
half its own half-depth of the middle is not the room. Deliberately *not* "is the exact centre
cell reachable", which would fail a genuine room with a table in the middle of it — the two
cases separate cleanly on distance, and the separation is measured rather than assumed (§3).
Two independent selftest controls hold it: an unbroken partition between the entry point and
the room reads as POCKET and falls back to the register's centre, and **the same wall with a
2 m doorway in it does not**.

---

## 2. TWO SIGN BUGS, BOTH MINE, AND THE SECOND ONE ONLY SHOWED UP IN AN A/B

**`--map` probed the room's FAR wall.** `side = 1 if z0 > cz else -1` is backwards: a door
faces its corridor. It reported `docking_bays` — a room a body demonstrably walks into in
`walkable.py --deck` — as sealed. Correctly, too: there is no door in that room's far wall.

**And `station()` had the same convention `agenda.room_legs` and `route_walk.legs_for` still
have.** Both compute the point half a metre inside the door as

```python
z_inner = place["z_m"] + D.room_interior_half_m(schema, profile, place)
```

— unconditionally `+`, which is the *far* wall for any room sitting on the other side of its
corridor. `roomnav` now derives the side from the cluster's own `meta["z_m"]`. **The two route
modules have not been fixed and nothing has yet counted how many places they affect.**

*The general form, and it is this module's own subject matter turned on itself: the entry
point arrives as a **declared** depth while everything else in `roomnav` is derived from the
mesh. `business_center`'s declared depth happened to coincide with its geometry, which is why
L3 went green and nothing else did.*

---

## 3. WHAT THE 21 LOOK LIKE, AND THEY ARE BIMODAL

Ratio is `distance from the centre of the nearest standable cell ÷ the room's own declared
half-depth`. **`docking_bays`, the control — a room a body verifiably walks into — sits at
0.32 with 19.76 m² reached.**

| place | deck | reached m² | off-centre m | half-depth m | ratio |
|---|---|---|---|---|---|
| `mooring_clamps` | blue/0/0 | 7.32 | 2.13 | 3.6 | 0.59 |
| `subfloor_stack` | green/0/7 | 2.40 | 3.26 | 4.8 | 0.68 |
| `bay_elevators` | blue/0/0 | 7.20 | 4.30 | 6.0 | 0.72 |
| `cnc` | blue/0/0 | 0.80 | 3.10 | 4.0 | 0.78 |
| `alien_worship` | green/0/4 | 0.40 | 2.70 | 3.0 | 0.90 |
| `domed_rotunda` | green/0/0 | 0.32 | 3.05 | 3.2 | 0.95 |
| `obs_dome_1` | blue/0/0 | 0.36 | 2.96 | 3.1 | 0.95 |
| `central_corridor` | red/0/0 | 0.16 | 2.90 | 3.0 | 0.97 |
| `obs_dome_2` | blue/0/0 | 0.16 | 2.90 | 3.0 | 0.97 |
| `obs_rotundas` | green/0/0 | 0.16 | 2.90 | 3.0 | 0.97 |
| `sanctuary_blue` | blue/1/5 | 0.16 | 2.90 | 3.0 | 0.97 |
| `vorlon_berth` | blue/0/0 | 0.16 | 3.90 | 4.0 | 0.97 |
| `casino` | red/1/1 | 0.16 | 5.40 | 5.5 | 0.98 |
| `ceremonial_rooms` | red/1/3 | 0.16 | 6.40 | 6.5 | 0.98 |
| `interfaith_chapel` | green/0/5 | 0.16 | 5.40 | 5.5 | 0.98 |
| `law_courts` | red/2/0 | 0.16 | 5.40 | 5.5 | 0.98 |
| `thieves_guild` | grey/0/24 | 0.16 | 4.90 | 5.0 | 0.98 |
| `admin_complex` | blue/1/1 | 0.16 | 6.90 | 7.0 | 0.99 |
| `dark_star` | red/1/2 | 0.16 | 6.90 | 7.0 | 0.99 |
| `outdoor_rec` | red/1/5 | 0.16 | 7.40 | 7.5 | 0.99 |
| `telepath_office` | green/0/2 | 0.16 | 7.90 | 8.0 | 0.99 |

**Seventeen sit at 0.90–0.99 with 0.16–0.40 m² — the doorway-pocket signature exactly.** Four
sit at 0.59–0.78 with 0.8–7.3 m²: those got part of the way in and are the ones the 0.5
threshold is least sure about. Nothing sits between 0.32 and 0.59, which is why the threshold
is where it is — it is placed in a measured gap, not chosen.

---

## 4. THE DISCRIMINATOR: A NARROW DOOR SHRINKS, A MISSING ONE GOES TO ZERO

`--map` prints the widest free run across a wall's row at four dilation radii. That separates
"the aperture is tight" from "there is no aperture", and it is the check that stops this
module blaming the station for its own conservatism. **Same wall, same cluster:**

| dilation | `docking_bays` corridor inner wall | `vorlon_berth` corridor inner wall |
|---|---|---|
| 0.00 m | 12.00 m | 12.00 m |
| 0.05 m | 6.60 m | 6.60 m |
| 0.20 m | **1.00 m** | **0.00 m** |
| 0.35 m (the capsule) | **0.80 m** | **0.00 m** |

`docking_bays` has 0.80 m of clear doorway at capsule radius. `vorlon_berth`, in the same wall
of the same cluster, has none — and none at 0.20 m either, so this is not a capsule that is
too fat. Two doorways in one wall, one clear and one not **as this module measures them** —
and §6 is why that sentence is no longer allowed to end "one passable and one not".

---

## 5. WHAT IS NOT KNOWN

- **Whether the 21 are unenterable in the engine.** Everything above is measured on the
  collision shell by this module. The engine is the authority — and **the obvious A/B cannot
  answer this, by construction**, which is worth knowing before somebody spends a session on
  it. `walkable.walk_deck(..., goto_key=<key>)` passes `--goto=<x,y,z>` to `walk.gd`, and
  `walk.gd:1882` steers **straight at the point**:

  ```gdscript
  if _have_goto:
      ... _goto - _player.global_position
  ```

  No path following. Driven at `docking_bays` on cluster `blue_0_0_z7126` it reports
  `goto_start_m=11.53 goto_best_m=5.17 goto_end_m=5.18`, `traverse_m=6.66`, `offfloor=0/1800`
  — a body that walked six metres toward the room and stopped at the first thing in the way.
  **That is a measurement of straight-line reachability, not of whether the room can be
  entered**, and it is exactly the limitation the L3 room leg turned out to have. Reporting
  5.17 m as evidence about `docking_bays` would be the same mistake as reading L3's 5.59 m as
  a lift defect.

  Driven at `vorlon_berth` — 40° round the ring from the spawn — the same harness proves it
  beyond argument: `goto_start_m=145.06 goto_best_m=96.69`, **`traverse_m=1661.65`** and
  **`offfloor=1084/1800`**. Steering straight at a point 145 m round a *curved* corridor walks
  the body off the deck; 1,661 m of "journey" with 60% of it in the air is the
  falling-body-reporting-a-journey signature `life.gd`'s own docstring records twice (11,712 m
  and 876,827 m). It is not a fact about `vorlon_berth`.

  The valid experiment is to **drive `roomnav`'s own waypoints** — which is what `agenda.py`
  and `route_walk.py` do, and what proved `business_center` at 0.05 m. Wiring the waypoint
  list into `walk_deck` would upgrade the W-track's deck gate from a straight-line steer into
  a real "can you get in", and is the obvious next increment.
- **Whether the four at ratio 0.59–0.78 are the same defect** as the seventeen at 0.90+, or a
  different one, or false positives of the threshold.
- **How many places `agenda.room_legs` / `route_walk.legs_for` aim at the wrong wall** (§2).
  Those two still use the unconditional `+`.
- **Six places are searched in part** — `infirmary`, `isolab`, `morgue`, `post_office`,
  `medlab_red`, `brig` — their reachable floor runs off the grid's arc half-span, so their
  answer is the best spot in a slice of the room. Reported on every run, never swallowed.
- **The drum is not asked at all** (`green/1/0`): it is a heightfield, not a corridor, and
  needs `drum_walk`'s question rather than this one. Printed as `not asked`, with the reason.


---

## 6. THE ENGINE OVERRULED THIS GATE, AND THE GATE WAS CHANGED

`walkable.deck_path` + `walk.gd --goto-path` now drive a body along a real route rather than
steering it straight (see the commit *"the deck gate follows a path now"*). That made the
experiment §5 called for possible, and it immediately falsified a claim in this document.

| room | this gate said | the engine did |
|---|---|---|
| `docking_bays` | fine, ratio 0.32 | arrived **0.05 m**, 5/5 waypoints, 0/1800 off the floor |
| `lowg_bays` | fine | walked **495 m**, arrived **0.91 m**, 71/72, 0/12000 off the floor |
| `mooring_clamps` | **CANNOT GET IN**, ratio 0.59 | walked **684 m**, arrived **1.18 m**, **93/93**, 0/15000 off the floor |

**`mooring_clamps` is enterable and this gate said it was not.** The engine is the authority;
a gate that contradicts it is a gate to fix, not a finding to defend.

Two changes follow. The two signals are **ANDed** rather than ORed — a place fails only when
its reachable floor is tiny *and* the nearest standable cell is nearly a whole half-depth from
the middle — and `POCKET_FRAC` is raised from 0.5 to **0.85**, past the case that was measured.
Reclassifying the same sweep: **21 → 17**, and the four dropped are exactly the borderline
band, `mooring_clamps` (0.60) among them:

| dropped | reached m² | ratio |
|---|---|---|
| `mooring_clamps` | 7.32 | 0.60 |
| `subfloor_stack` | 2.40 | 0.67 |
| `bay_elevators` | 7.20 | 0.72 |
| `cnc` | 0.80 | 0.78 |

**Three engine runs is a thin calibration and the code says so.** The 17 that remain all sit at
0.16–0.40 m² and 0.90–0.99, which is a different population from anything the engine has
walked — but *none of them has been walked either*. `vorlon_berth` is 1,181 m along the
corridor from the spawn and needs ~20,000 physics frames; that run has not been made.

**And the control had to be rebuilt, which is its own finding.** The selftest's synthetic
pocket was one full-width wall leaving a **28.8 m² strip** behind it — and it stopped firing
the moment the rule was tightened, correctly, because a 28.8 m² strip is not a pocket. *A
control that only fires against a loose rule is not a control.* It is now a doorway-sized
pocket — a sealing wall with returns either side of the door, 0.48 m² reachable — and it fires
against the strict rule.


---

## 7. HOW TO BUDGET ONE OF THESE RUNS, because I got it wrong twice

An engine walk to a far room costs frames in proportion to the corridor distance divided by
the speed the body **actually achieves**, and this project's stated speed is not that.

| room | corridor distance | frames given | frames needed at 1.46 m/s | outcome |
|---|---|---|---|---|
| `docking_bays` | 0.1 m | 1,800 | ~10 | arrived, 0.05 m |
| `lowg_bays` | 479.9 m | 12,000 | ~19,700 | arrived, 0.91 m (it had slack: it stops on arrival) |
| `mooring_clamps` | 664.5 m | 15,000 | ~27,300 | arrived, 1.18 m |
| `plantroom_bay` | 959.9 m | 20,000 | ~39,400 | **ran out** — 486 m of 960 |
| `vorlon_berth` | 1,181.3 m | 24,000 | ~48,500 | **abandoned, under-budgeted** |

`player.gd` exports `speed_m_s = 4.2`, and a body sustained **1.46 m/s** — so a budget computed
from the export is 2.9x short. Two runs were wasted on that. The likely cause is the corridor
crowd (`--deck` spawns it, `npc.gd` gives every walker a capsule, 963 of them over 1,329 m is
0.72 people per metre); the A/B is `walk_deck(..., no_npc_collision=True)` and it has not been
run. **Run that first**: it settles the crowd question *and* roughly halves the frame cost of
every subsequent far-room test.

*And the two that DID arrive had slack for the same reason a marathon time is not a pace: the
run stops when the body arrives, so `traverse_m / frames` understates the walking speed for
those and is only a true rate for the ones that ran out.*


---

## 8. AND THEN THE STATION GREW UNDER IT — the vestibule, and a likely answer for the 17

`rooms.tiling` landed after everything above was measured, and it moved the ground this gate
stands on. Rooms grow **symmetrically about `place["z_m"]`**, and `deck.corridor_z_m` puts the
ring corridor clear of the deepest room on the cluster — so a deck with one very deep room
gives every shallower room a long vestibule between its door and the ring.

Measured across the station: **794 m of vestibule, mean 14.7 m**, and it is *not* spread —
9 places exceed 20 m and four of those are on the drum (`green/1/0`), which is heightfield
ground with no ring corridor, so their figure is meaningless. The real cases are **one deck
plus one place**:

| place | deck | vestibule | own half | deepest on its deck |
|---|---|---|---|---|
| `shuttle_car` | yellow/0/30 | **232.0 m** | 20.2 | 252.2 |
| `mooring_clamps` | blue/0/0 | 66.4 m | 3.8 | 70.2 |
| `bay_elevators` | blue/0/0 | 58.0 m | 12.2 | 70.2 |
| `vorlon_berth` | blue/0/0 | 50.0 m | 20.2 | 70.2 |
| `plantroom_bay` | blue/0/0 | 50.0 m | 20.2 | 70.2 |
| `lowg_bays` | blue/0/0 | 40.0 m | 30.2 | 70.2 |

Five are on **blue/0/0 — the arrival deck, the player's front door** — because `docking_bays`
is 140 m now and pushes the corridor out for everyone else on the cluster.

**AND THREE OF THEM ARE ROOMS THIS DOCUMENT CALLS UNENTERABLE.** `mooring_clamps`,
`bay_elevators` and `vorlon_berth` are in §3's table. This gate places its doorway probe at
`place["z_m"] ± (z_half − 0.5)` — a point relative to the ROOM — while the actual door is
50–66 m away across a vestibule. That is the same defect §2 already names, one turn deeper:
**a point derived from the room's own extent is not the door when something else decides
where the door is.** It is the first single cause that would explain all seventeen, and
`mooring_clamps` — the one the engine proved enterable — is the largest of the three.

`deck.room_interior_half_m` now returns the built span rather than the one-bay clamp, so the
probe has moved. **The sweep must be re-run before any figure in §3 or §6 is quoted again.**
Neither the 17 nor the 21 before it should be repeated until it has been.

*The structural fix for the vestibule itself is to grow rooms toward their door instead of
symmetrically — keep the near face fixed and extend away from the corridor. That needs a
`deck.room_centre_z_m` read by `deck.build_deck`, `collision.room_shell`, `roomnav`,
`route_walk`, `agenda` and `walkable`, because `place["z_m"]` stops being the room's centre
the moment it is done. Not attempted: the station is verifiably green right now
(`deck.py --sweep`: 90/90 clusters, 128/128 locations, 0 floor holes) and a six-file refactor
whose verification cycle is twenty minutes is not something to start on a green build without
the time to finish it.*


---

## 9. RE-RUN AGAINST THE TILED STATION — half the hypothesis was right, and the rest is not what I said

§8 predicted the vestibule would explain all seventeen. Re-run: **101 of 116 yes, 15 no.**

**Right about four.** `mooring_clamps`, `bay_elevators`, `lowg_bays` and `plantroom_bay` — the
blue/0/0 rooms with 40–66 m vestibules — **all now pass**. `deck.room_interior_half_m` returning
the built span moved the probe onto the real door, exactly as §8 said it would.

**Wrong about the other fifteen**, and the reason is the most useful thing in this document.
Their signature is unchanged and **perfectly scale-invariant**:

| place | reached | off-centre | half-depth | ratio |
|---|---|---|---|---|
| `dark_star` | 0.16 m² | 6.90 | 7.0 | 0.986 |
| `telepath_office` | 0.16 m² | 7.90 | 8.0 | 0.988 |
| `casino` | 0.16 m² | 10.90 | 11.0 | 0.991 |
| `vorlon_berth` | 0.16 m² | 19.90 | 20.0 | 0.995 |
| `thieves_guild` | 0.16 m² | 49.90 | 50.0 | 0.998 |
| `generator_hall` | 0.16 m² | 74.90 | 75.0 | **0.999** |

**`off = z_half − 0.1` exactly, at every scale from 7 m to 75 m.** That is the topmost cell
centre of a 0.2 m grid spanning `z0 ± z_half` — an arithmetic identity, not a measurement. The
search is reaching a 2×2 pocket at the grid's own edge, which means **the entry point is landing
outside the built room and BFS is exploring the strip above its wall.** A defect in the geometry
could not be this exactly proportional to a number this module computes.

### Hypotheses eliminated, so nobody spends the time again

1. **"The doorway aperture is missing."** Refuted by the engine: `mooring_clamps` carried this
   exact signature and a body walked 684 m and entered it (§6).
2. **"A vestibule puts the real door far from the probe."** Explains 4 of 19; not the 15.
3. **"`bespoke.room_shell` translates rather than scales, so the span overshoots."** All 15
   failures have `module: None` — they are plain `rooms.py` builds — and so do several places
   that pass (`bay_elevators`, `lowg_bays`, `business_center`).

### What to test next, in order

The discriminator is between two sets of **generic** rooms, so it is not about which builder
runs. `python3 station/roomnav.py --place thieves_guild --map` draws the occupancy and scans the
door's own column; the row below the pocket will say what is sealing it. Check first whether
`built_span_m` overshoots the **emitted mesh's** z-extent for these fifteen — the `--footprint`
gate asserts mesh == plan for the places `rooms.py` tiles, and if these fifteen are outside that
assertion then the probe is being placed from a plan nothing built.

*Three corrections in one thread, each from measurement: the 21 became 17 when the engine
overruled the threshold, 17 became 15 when the station grew under the gate, and the single
cause I proposed for all of them explains four. The number has never been quoted without being
re-derived, which is the only reason it kept getting smaller.*
