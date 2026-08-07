# PATCHES owed by shell_fit (session 4t) — files this agent does not own

The shell-fit work owns `station/collision.py` and `station/deck.py` only. Two real defects
sit outside those files. Neither blocks the gate — `--shell-fit` reports both as `note`
lines and asserts their *consequences* through SPAN and OVERLAP — but both should land.

---

## P1 — `bespoke.axial_plan` answers for the axis and not for the width (`station/bespoke.py`)

**The defect.** `rooms.tiling()`'s composed branch is

```python
    if composed:
        plan.update(_BSP.axial_plan(schema, profile, place))
```

and `plan["bay_w"]` was set two lines earlier to `min(w_full, bw)` — the width of one
*generic representative bay*, which for a composed place is a room nobody builds.
`axial_plan` returns no `bay_w`, so the `update()` never replaces it. `rooms.built_span_m`
therefore reports, for 20 of the 33 composed places that have a composed form, a width that
is not the width of anything:

| place | `built_span_m` says | the module builds |
|---|---|---|
| ambassadorial_suites | 10.49 m | **100.81 m** |
| alien_resident_qtr | 11.08 m | 103.53 m |
| qtr_personnel | 10.54 m | 95.22 m |
| qtr_civilian | 11.05 m | 90.07 m |
| qtr_command | 11.63 m | 72.83 m |
| qtr_transient | 11.66 m | 69.68 m |
| league_delegations | 11.39 m | 50.14 m |
| council_chamber | 11.81 m | 22.74 m |
| zocalo / shops_kiosks | 12.79 / 14.05 m | 22.04 m |
| arrival_concourse | 11.08 m | 20.90 m |
| customs_north / _south | 12.31 m | 17.50 m |
| cnc | 11.52 m | 14.33 m |
| obs_rotundas | 8.43 m | 14.36 m |
| alien_sector | 9.68 m | 14.11 m |
| obs_dome_1 | 8.32 m | 12.97 m |
| kosh_quarters | 10.22 m | 10.66 m |
| core_shuttle | 5.77 m | 9.61 m |
| central_corridor | 6.98 m | 9.36 m |

This is exactly the shape session 4l fixed for the AXIS — `axial_span_m`'s own docstring
says it exists because "any second description of it would be free to drift" — applied to
one axis and not to the rule.

**Reproduce.**

    python3 station/deck.py --shell-fit        # the `note STALE` lines at the end

**The patch.** In `bespoke.axial_span_m`'s neighbourhood, add the same measurement across
x and return it from `axial_plan`. `room_shell` is the call that already recentres a module
into the assembler's frame, so it is the one that gives an x range comparable with
`bay_w`:

```python
_WIDTH = {}


def lateral_span_m(schema, profile, place):
    """The width across the ring a composed place's module ACTUALLY builds.

    The other half of `axial_span_m`, and it exists for the same reason: a
    second description of a module's size is free to drift, and this one did.
    Measured after `room_shell`'s recentring, because that is the frame
    `deck._place_local` maps onto the station.
    """
    key = place["key"]
    if key not in _WIDTH:
        v = room_shell(schema, profile, place, 0.0)[0]
        xs = [p[0] for p in v]
        _WIDTH[key] = (max(xs) - min(xs)) if xs else 0.0
    return _WIDTH[key]
```

then in `axial_plan`, in both the `LEGACY_AXIAL` and the live return, add

```python
        "bay_w": lateral_span_m(schema, profile, place),
```

guarded so a module with no composed form (the six `components` structures, `docking_bay`,
`standard_corridor`) keeps the generic answer — those raise out of `room_shell` and
`composable()` is already False for them, so in practice the branch is not reached, but
`_selftest` should assert that rather than assume it.

**What it fixes and what it costs.** `rooms.built_span_m` becomes true for composed places,
which is what `docs/spec/PLACES.md`, `rooms.py --footprint` and `navgraph_export` all read.
`deck.room_box_m` would then collapse to `built_span_m` for every place and its `module`
branch could go. **Check `--footprint` after landing it**: `tiling()` derives `n_want` from
`bays_along`, which is axial, so the bay count should not move — but the printed
"built to its footprint" percentages will, because the width in them changes.

**Do not do the obvious cheaper thing.** Setting `bay_w = w_full` (the footprint) for
composed places would make `built_span_m` agree with nothing measured, and 12 of the 33 —
`plant_zone` at 13.77 m in a 2,704 m footprint — would be reported 200× too wide.

---

## P2 — `qtr_transient` builds 69.68 m of module inside a 58.28 m footprint (gazetteer / `station/quarters.py`)

**The defect.** Every other composed place's mesh is inside its own declared footprint;
this one is 11.40 m wider than its own arc — 31.09° of geometry in a 26.00° footprint.
`directory.collisions()` asserts *footprints* do not overlap, so up to session 4t the
collision shells inherited non-overlap by construction. Widening the shells to the meshes
spends that inheritance, and this place is the one that escapes.

**It is not currently interpenetrating anything** and that is now asserted rather than
assumed: `--shell-fit`'s new OVERLAP leg tests every pair of shells on a shared
sector/ring/deck with overlapping z bands, pairwise, on the arcs the shells actually span.
It reports 0. `qtr_transient` has no neighbour in its z band today.

**Reproduce.**

    python3 station/deck.py --shell-fit        # `note OVERFOOT qtr_transient`

**The fix, either way round.**

* grow the gazetteer footprint for `qtr_transient` from 26.00° to at least 31.09° + the
  register's own pad, then re-run `python3 station/directory.py` so `collisions()` re-checks
  non-overlap against its neighbours; **or**
* narrow `quarters.py`'s unit count for the transient class so the module builds inside
  26.00°. The other six quarters classes are all inside their footprints, so this is one
  class's row and not the module's shape.

The first is cheaper and is probably right — 69.68 m of transient quarters is a defensible
amount of room and the footprint was never measured against the module.

**Until one of them lands, OVERLAP is the thing standing between this and a body walking
out of one room into the solid wall of the next.** It is cheap (arithmetic, no build) and
it runs on every `--shell-fit`.

---

## P3 — `navgraph_export` still models a room as symmetric about its bearing (`station/navgraph_export.py`)

`navgraph_export.py:485` does

```python
        half_deg = (math.degrees(D.room_half_w_m(schema, profile, q) / radius_m)
```

`room_half_w_m` now returns half of the room's true span, so the node is the right SIZE —
but it is still centred on the place's bearing, and a composed room is centred on its
DOORWAY. `arrival_concourse` runs −17.37..+3.53 m about that bearing, so its nav node is
now 10.45 m each way where the room is 17.37 m one way and 3.53 m the other.

**The patch** is one line, using the accessor added in 4t beside the one it already calls:

```python
        mid_deg = math.degrees(D.room_x_off_m(schema, profile, q) / radius_m)
```

and centring the node's arc on `q["angle_deg"] + mid_deg` instead of `q["angle_deg"]`.

Before 4t this file was wrong in both size and centre; it is now wrong only in centre, and
on the 13 composed places whose module is not symmetric about its own doorway.
