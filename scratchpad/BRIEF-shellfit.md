# The collision shell is not the room — brief for the shell-fit agent

## What is wrong, measured

`station/deck.py` sizes a room's collision shell with the pre-4k expression
`min(rooms.room_extent_m, rooms.bay_span_m) / 2`, in TWO places:

* `deck.room_shell_for` (~line 762) — the shell a body collides with
* `deck.room_half_w_m` (~line 246) — used by `deck_plan`'s door-fit test and by
  `navgraph_export`

Session 4k fixed exactly this for the AXIS and left the WIDTH. `deck.room_interior_half_m`'s
own docstring says why the axis mattered — *"a shell sized on the old expression would put an
INVISIBLE wall 10.8 m into a 140 m room a player can see the whole length of"* — and
`rooms.built_span_m` was extracted to be **"THE ONE FUNCTION EVERYTHING THAT PLACES A ROOM
MUST ASK"**. One of its two return values never reaches either site. *A fix applied to one
axis and not to the rule.*

### The numbers (measured this session, `scratchpad/shellfit.log`, `scratchpad/shellfit2.log`)

`shell_w` = what collision gets. `mesh_w` = the x-extent of what `bespoke.room_shell` emits.

| place | shell_w | mesh_w | % | shell ceil | mesh height |
|---|---|---|---|---|---|
| ambassadorial_suites | 10.49 | 100.81 | **10.4%** | 3.40 | 3.04 |
| alien_resident_qtr | 11.08 | 103.53 | 10.7% | 2.70 | 3.04 |
| qtr_personnel | 10.54 | 95.22 | 11.1% | 2.70 | 3.04 |
| qtr_civilian | 11.05 | 90.07 | 12.3% | 2.70 | 3.04 |
| qtr_command | 11.63 | 72.83 | 16.0% | 2.70 | 3.04 |
| qtr_transient | 11.66 | 69.68 | 16.7% | 2.70 | 3.04 |
| league_delegations | 11.39 | 50.14 | 22.7% | 3.40 | 3.04 |
| council_chamber | 11.81 | 22.74 | 51.9% | 3.60 | **7.42** |
| arrival_concourse | 11.08 | 20.90 | 53.0% | 3.60 | 7.65 |
| zocalo | 12.79 | 22.04 | 58.0% | 3.60 | 7.48 |
| obs_rotundas | 8.43 | 14.36 | 58.7% | 3.60 | 7.40 |
| core_shuttle | 5.77 | 9.61 | 60.1% | 3.40 | 8.68 |
| shops_kiosks | 14.05 | 22.04 | 63.7% | 3.40 | 7.48 |
| obs_dome_1 | 8.32 | 12.97 | 64.2% | 3.50 | 8.76 |
| alien_sector | 9.68 | 14.11 | 68.6% | 2.60 | 3.80 |
| customs_north / _south | 12.31 | 17.50 | 70.3% | 3.50 | 7.65 |
| central_corridor | 6.98 | 9.36 | 74.6% | 3.55 | 7.58 |
| cnc | 11.52 | 14.33 | 80.4% | 3.45 | 9.90 |

**19 of 32 composed places are short. Two are the other way** and let a player walk out
through a wall: `obs_dome_2` 9.60 against 8.76 (109.5%) and `shuttle_car` 6.40 against 4.78
(133.8%). **The axis is 100.0% on every single one** — that is the signature of one axis
fixed and the other left, not of thirty separate bugs.

## The gate already exists. Run it first and see it fail.

    python3 station/deck.py --shell-fit             # the gate
    python3 station/deck.py --shell-fit --legacy    # negative control

It asks three questions and CONTAIN is the one a player feels:

1. **CONTAIN** — no vertex of the room's render mesh lies outside the arc its collision shell
   spans. Not width: *containment*.
2. **SPAN** — the shell's width is what `rooms.built_span_m` reports.
3. **FOOT** — no room claims more arc than its declared footprint.

## THE TRAP, and it is why CONTAIN is not the same question as width

`bespoke.room_shell` recentres a module's x **on the DOORWAY, not on the bounding box**. Its
own comment: *"local x = 0 is not a centre, it is a DOORWAY, and the bounding box only
coincides with it when a module happens to be symmetric. Two are not: alien_sector bbox cx
-4.66 vs opening 0.00; quarters bbox cx 12.32."*

`collision.room_shell(meta, angle_deg, hw_m, hl_m, ceil_m, z_m, door_angle_deg)` takes ONE
half-width, symmetric about the place's bearing. **So giving it the right width is not enough
— a room whose door is off-centre will hang out one side and over-reach the other.** Expect to
give `collision.room_shell` an asymmetric x range (or a centre offset plus a half-width) and
to keep `door_angle_deg` landing where it lands today.

## What makes the widening SAFE, and it is checkable rather than hoped for

`scratchpad/shellfit2.log`: **31 of 32 composed meshes are inside their own declared
footprint** — `zocalo` builds 5.74° of a 70° footprint, `plant_zone` 1.83° of 360°.
`directory.collisions()` already asserts footprints do not overlap, so **a shell that stays
inside its footprint inherits non-overlap by construction** and no pairwise shell test is
needed. Assert that, do not assume it.

**The one exception is `qtr_transient`:** its mesh is 31.09° against a 26.00° footprint —
5.09° of geometry outside its own declared arc. I checked its ring/deck/z band and it has no
neighbour today, so nothing is currently interpenetrating; it is a latent hazard and a
separate finding. Either grow the footprint (and re-run `directory.collisions()`) or shrink
the module. Do not let it block the other 31.

## Also wrong, and smaller: the ceiling

`R.ceiling_m(place)` gives `council_chamber` 3.60 m against a 7.42 m mesh and
`downbelow_arch` 3.40 m against 23.57 m. Not a hole a player falls through, so treat it as a
second, smaller item — but a shell ceiling 3.4 m below the built one cuts the room in half for
physics and for anything that ray-casts upward.

## Rules for this job

* **Work in `git worktree`.** `deck.py --sweep`, `walkable.py` and `rooms.py --footprint` all
  rebuild `station/generated/scene/deck/*`; another agent and the main agent are live.
* **Do not write to `docs/aaa-scorecard.json`.** Put any review rounds in
  `scratchpad/craft-4r-<key>.json` and I will merge them.
* **Stage paths by name.** Never `git add -A`.
* **`deck_plan`'s arc allocation must be RE-RUN, not assumed.** Its door-fit test uses
  `room_half_w_m`; widening it changes which corridor phase wins, which changes which rooms
  get a door. `--sweep` reports `unopened` — it must not go up.
* Verify with, in this order: `deck.py --shell-fit`, `deck.py --selftest`, `deck.py --sweep`,
  `station/walkable.py --deck blue/0/0`. Quote the before and after of each.
* Findings in files you do not own go in `scratchpad/PATCHES-4r-shellfit.md` with the
  measurement and the command that reproduces it.
