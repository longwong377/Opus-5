# Session 4q — patches for files this agent does not own

Three patches. Each states what it fixes, the evidence, and the control.

---

## PATCH 1 — `tools/export_scene.py`: the Zocalo's rib-lamp expectation is stale by exactly one doubling of its bay count

**The finding, and it is NOT what the brief guessed.** `rooms.tiling` did not double the
ribs. **The Zocalo has never gone through `rooms.tiling`** — it is a bespoke `"grow"` module
(`bespoke.AXIAL["zocalo"]`), built by `_by_footprint("zocalo")`. Session 4k's tiling commits
(`ed8d363`, `0217e2e`, `d649166`) only changed *how* the same answer is reached: the entry it
replaced,

```python
"zocalo": lambda s, p, q: (lambda Z, b: Z.zocalo_run(
    b[0], seed=b[1], cap_ends=True))(
        __import__("zocalo"), __import__("zocalo").bays_for(q)),
```

already called `bays_for(q)` and already produced six bays.

**The commit that made 30 wrong is `27d32d7`, 2026-08-02** — *"quarters, zocalo: the count was
a default — all six modules now distinct"*. That is the commit that wrote `zocalo.bays_for`
and stopped `BESPOKE_GEOMETRY["zocalo"]` calling `zocalo_run(3, cap_ends=True)` with no place.
It touched `canon/INVENTIONS.md`, `station/bespoke.py`, `station/quarters.py`,
`station/zocalo.py` — **and not `tools/export_scene.py`**. So the self-test kept describing the
three-bay Zocalo that had just stopped existing.

**60 is correct, measured five ways:**

| | measured |
|---|---|
| `zocalo.bays_for(directory.by_key("zocalo"))` | `(6, 'zocalo')` = `min(cap 6, ⌊120 m / 10.8 m⌋ = 11)` |
| `zoc_rib_lamp` spans in the built mesh | **12** |
| bodies per span (`fitting_bodies`) | **5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5** |
| distinct rib z | 0, 5.34, 10.71, 16.11, 21.51, 26.91, 32.31, 37.71, 43.11, 48.51, 53.91, 59.31 — 12 ribs at `rib_spacing_m` 5.4 over 6 bays of `bay_length_m` 10.8 |
| the module's own loops | `for k in range(2)` ribs × `for f in (0.16, 0.32, 0.50, 0.68, 0.84)` lamps |

5 × 2 × 6 = 60. **Nothing doubled; the room got twice as long.** The docking-bay assertion
beside it (`len(_bay) == 39`) still measures 39 and is untouched.

**Do not re-pin to 60.** `drum_dressing`'s `GARDEN_OPEN_EDGES` comment names this exact failure
mode, and a second re-pin would go stale the day the budget cap in `bays_for` moves. Derive it.

### The patch

In `tools/export_scene.py`, in `_selftest`, replace:

```python
    #   zocalo       5 rib lamps per rib, measured, x 6 ribs = 30
```

with:

```python
    #   zocalo       5 rib lamps per rib x RIBS_PER_BAY x bays_for(place)
```

and replace:

```python
    _zoc = [x for x in _lamps("zocalo") if x["group"] == "zoc_rib_lamp"]
    check(len(_zoc) == 30,
          f"the Zocalo recovers its five rib lamps a rib ({len(_zoc)})")
```

with:

```python
    # DERIVED FROM THE MODULE, NOT PINNED. This read `== 30` and had been wrong
    # since 27d32d7 (2026-08-02) -- the commit that gave the Zocalo its own
    # footprint and took it from three bays to six. That commit touched
    # bespoke.py, quarters.py and zocalo.py and not this file, so the assertion
    # went on describing a three-bay room that had stopped existing, and printed
    # `(60)` against `30` for four sessions. Re-pinning to 60 would go stale the
    # day `bays_for`'s cap moves, which is the failure `drum_dressing`'s
    # GARDEN_OPEN_EDGES comment is named after.
    #
    # WHAT THIS STILL CATCHES is the thing it was written for: a span is not a
    # fitting. If `to_spans` were let loose on the whole run again the count
    # would be the RIB count and not the LAMP count, which this expression can
    # tell apart because it multiplies the two.
    import zocalo as _Z                                          # noqa: PLC0415
    import directory as _dr                                      # noqa: PLC0415
    _zbays = _Z.bays_for(_dr.by_key("zocalo"))[0]
    _want_zoc = len(_Z.RIB_LAMP_F) * _Z.RIBS_PER_BAY * _zbays
    _zoc = [x for x in _lamps("zocalo") if x["group"] == "zoc_rib_lamp"]
    check(len(_zoc) == _want_zoc,
          f"the Zocalo recovers its {len(_Z.RIB_LAMP_F)} rib lamps on each of "
          f"{_Z.RIBS_PER_BAY * _zbays} ribs over {_zbays} bays "
          f"({len(_zoc)} of {_want_zoc})")
```

This needs PATCH 2. Without it, substitute `10 * _zbays` for `_want_zoc` and accept that the
10 stays pinned.

---

## PATCH 2 — `station/zocalo.py`: name the two counts the assertion has to derive from

Add beside the other bay constants (they belong with `bay_length_m` / `rib_spacing_m`):

```python
## THE RIBS IN ONE BAY, AND THE LAMPS SET INTO EACH RIB'S INTRADOS. Named
## because `tools/export_scene.py`'s self-test has to derive its expected lamp
## count from this module instead of pinning it: the pinned 30 was written when
## `BESPOKE_GEOMETRY` called `zocalo_run(3)` and survived unchanged when
## `bays_for` took the room to six bays, so the assertion said 30 against a
## measured 60 for four sessions.
RIBS_PER_BAY = 2
RIB_LAMP_F = (0.16, 0.32, 0.50, 0.68, 0.84)
```

and in `zocalo_bay`, replace

```python
    for k in range(2):
        z_rib = k * p["rib_spacing_m"]
```

with

```python
    for k in range(RIBS_PER_BAY):
        z_rib = k * p["rib_spacing_m"]
```

and

```python
        for f in (0.16, 0.32, 0.50, 0.68, 0.84):
```

with

```python
        for f in RIB_LAMP_F:
```

Pure rename — the emitted mesh is byte-identical, which is the point: the assertion gains a
source and the geometry does not move.

---

## PATCH 3 — `STATE.md` §24.5: `--ragdoll-solid` does not reproduce a floor-loss hazard, and now that it works we can say so

§24.5 says the flag *"removes the exception and reproduces the pre-4h floor-loss hazard"*.
Both halves are wrong, and the second stays wrong after the flag is fixed.

**Before this session** (`godot/scripts/{walk,ragdoll}.gd` at `fdc27bf`), four runs of
`--corpse-gate` on one build:

```
(subject)                          PASS  clearance_min -0.0000  walked  1.03 m  offfloor 0/150
--ragdoll-solid                    PASS  clearance_min -0.0000  walked  1.03 m  offfloor 0/150
--no-ragdoll-push                  FAIL  clearance_min -0.4200  walked 10.50 m  offfloor 0/150
--no-ragdoll-push --ragdoll-solid  FAIL  clearance_min -0.4822  walked  8.98 m  offfloor 0/150
```

`--ragdoll-solid` was identical to the subject in every statistic. Cause, probed in the engine
(`scratchpad/layer_probe.gd`, both controls firing): Godot 4.4's `move_and_collide` consults
**the mover's mask only**, the bones are on `RAGDOLL_LAYER` (16), and `walk.gd::_spawn_player`
never set the player's `collision_mask`, so it was the default 1. The RID exception was
removing a collision the mask had already removed.

**After** (player mask `1 | RAGDOLL_LAYER` under the flag, plus a `solidhits` counter in the
gate's verdict):

```
(subject)                          PASS  clearance_min -0.0000  walked  1.03 m  solidhits   0/150  offfloor 0/150
--ragdoll-solid                    PASS  clearance_min -0.0000  walked  1.03 m  solidhits   0/150  offfloor 0/150
--no-ragdoll-push                  FAIL  clearance_min -0.4200  walked 10.50 m  solidhits   0/150  offfloor 0/150
--no-ragdoll-push --ragdoll-solid  FAIL  clearance_min -0.1752  walked  0.62 m  solidhits 142/150  offfloor 0/150
```

**Suggested replacement text for §24.5's claim:**

> `--ragdoll-solid` puts the corpse's sixteen colliders back on the player, and it needs
> `--no-ragdoll-push` beside it to be observable at all: with `push_off` working the player is
> separated before the solver ever touches a bone, so the flag alone is 0 solid hits and a
> statistic-for-statistic match with the subject. Paired, it is decisive — **142 of 150 frames
> resolved against a bone, and the player is stopped after 0.62 m instead of walking 8.98 m
> through the body.** It does **not** reproduce the pre-4h floor-loss hazard: `offfloor` is
> 0/150 in all four runs. The body lies on the deck beside the player rather than under them,
> so the floor contact that would be lost is never in question; reproducing floor loss needs a
> scenario that walks the player *over* a body, which no gate here does.

---

## Measurements taken in 4q, kept here so a recycled container does not lose them

**Drum, at the exporter's own eye (205°, mid-length), `export_scene.drum_parts`:**
ground 94,592 · endcap_fore 7,536 · endcap_aft 7,536 · guideways 11,796 · spokes 516 ·
core 13,340 · trams 12,624 · townscape 51,026 · dressing 89,094 — **288,060**.
`budget.py` before 4q: shell 88,736 + caps 15,072 + trusses 11,796 + spokes 516 = **116,120**.

**Drum, 10 angles × 3 axial stations (exploratory, 30 eyes), ground + dressing only:**
min 144,256 (45°, z 4226) → max **201,162** (270°, z 5132). Static parts 104,374.
Worst total **305,536 = 101.8% of DRUM["visible_set_tris"]**.

**`blue/0/0`, every z-cluster built (`budget.py` builds only the first):**

| # | z | rooms | triangles | places |
|---|---|---|---|---|
| 0 | 7120 | 6 | **1,264,432** | docking_bays, lowg_bays, mooring_clamps, plantroom_bay, bay_elevators, vorlon_berth |
| 1 | 7960 | 4 | 608,548 | cnc, obs_dome_1, obs_dome_2, nav_beacon |
| 2 | 7440 | 3 | **484,440** | customs_north, arrival_concourse, customs_south |
| 3 | 7920 | 5 | 596,346 | cnc, obs_dome_1, obs_dome_2, comms_grid, proximity_arrays |
| 4 | 6880 | 1 | 247,194 | cobra_bays |
| 5 | 8000 | 4 | 608,548 | cnc, obs_dome_1, obs_dome_2, nav_beacon |

Station coverage: **1 of 96 z-clusters over 71 addressed decks; 6 of 129 places (4.7%)**.
Two of the 96 repeat a place-set already covered on the same deck (94 distinct room-sets).

**`density.score(the_garden)`:** pre-4q 121,976 tri / λ 0.1122 / floor 0.1317 / gdi 0.852 FAIL
→ 4q 305,244 tri / λ 0.2079 / floor 0.1120 / gdi **1.857 PASS**.
The four `module="garden"` places (`garden_town`, `zen_garden`, `garden_terrace`, `water_rec`)
were and are measured on `garden.townscape` — 51,026 tri, λ 0.9960, floor 0.9151, PASS, **all
four identical**.

**Zocalo:** `bays_for` 6 · `bay_length_m` 10.8 · `rib_spacing_m` 5.4 · 12 rib-lamp spans ·
5 bodies each · 60 lamps. `docking_bays` 39, unchanged.

---

## PATCH 4 — `station/coldstart.py::g7`: `--ragdoll-solid` is not in any gate's case list, which is why nobody noticed it was inert

`g7`'s cases are exactly two:

```python
    return _walk_gate(verbose, "CORPSE", "--corpse-gate", (
        ((), True, "the shipped build"),
        (("--no-ragdoll-push",), False,
         "the corpse is a hologram -> the player ends 0.42 m inside it"),
    ), extra_probes=(built_deck, ragdoll_bodies), echo=("CORPSE gate:",))
```

`--ragdoll-solid` appears in `ragdoll.gd::apply_controls`, in `STATE.md` §24.5 and in
`ragdoll.gd`'s comments, and **in no gate**. A control nothing runs cannot be discovered to be
inert, which is how it stayed inert for four sessions. Suggested third case:

```python
        (("--no-ragdoll-push", "--ragdoll-solid"), False,
         "and solid as well -> stopped after 0.62 m by the bones themselves; "
         "read `solidhits` in the echoed line, 142/150 against 0/150"),
```

**Its limitation, stated:** `_walk_gate` parses PASS/FAIL only, and `--no-ragdoll-push` alone
already fails, so this case's *verdict* proves nothing new. What it buys is that the flag is
exercised on every run and its `solidhits` figure is echoed, so the next time it goes inert the
number is on screen. A verdict-level assertion would need `_walk_gate` to compare a named
statistic between cases, which is a bigger change than this session should make to a file it
does not own.
