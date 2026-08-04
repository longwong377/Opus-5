# CAN A BODY GET INTO EVERY NAMED PLACE, AND STAND UP?

**Gate:** `python3 station/roomnav.py --station`
**Reproduction for one place:** `python3 station/roomnav.py --place <key> --map`
**Session:** 4k. **Status: 95 of 116 yes, 21 no, exit 1.**

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
too fat. **Two doorways in one wall, one passable and one not.**

---

## 5. WHAT IS NOT KNOWN

- **Whether the 21 are unenterable in the engine.** Everything above is measured on the
  collision shell by this module. The engine is the authority and only `docking_bays` has been
  driven — the A/B that would settle it is `walkable.walk_deck(..., goto_key=<key>)` per place.
- **Whether the four at ratio 0.59–0.78 are the same defect** as the seventeen at 0.90+, or a
  different one, or false positives of the threshold.
- **How many places `agenda.room_legs` / `route_walk.legs_for` aim at the wrong wall** (§2).
  Those two still use the unconditional `+`.
- **Six places are searched in part** — `infirmary`, `isolab`, `morgue`, `post_office`,
  `medlab_red`, `brig` — their reachable floor runs off the grid's arc half-span, so their
  answer is the best spot in a slice of the room. Reported on every run, never swallowed.
- **The drum is not asked at all** (`green/1/0`): it is a heightfield, not a corridor, and
  needs `drum_walk`'s question rather than this one. Printed as `not asked`, with the reason.
