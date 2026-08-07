# Patches g3_incidents needs in files it does not own

Written rather than applied: `station/boot.py` and `godot/scripts/main.gd` belong to the
wf-aaa-4t workflow / are outside this agent's ownership (`station/incident.py`,
`station/friction.py`). Two agents in one file is the stomped-artefact defect CLAUDE.md records
three times.

## What is already wired, and needs no patch

`station/boot.py::_collapses` -> `incident.visible_bodies(rooms, day, seed)` -> `boot.json`
`"collapses"` -> `godot/scripts/main.gd::_fire_collapses`. That chain runs today and this session
did not change its shape. `visible_bodies` now prints, on stderr, on every call:

    incident.visible_bodies: N collapse row(s) over M place(s), observer=none (absent)

and every row gained two additive keys, `"stance"` (what the day was resolved in — `"absent"`
until an observer is passed) and `"if_helped"` (whether this body would still be on the deck had
the player helped, resolved through the class's own HELPS branch, not tabulated).

## What is NOT wired, and the patch for it

The player's *choice* does not reach the engine. Nothing in `godot/scripts/` reads `if_helped`.

### 1. `station/boot.py`, in `_collapses`

Nothing is required for correctness — the ABSENT bake is the right default, because at bake time
the player has chosen nothing. If a live player is wanted at bake time:

```python
        import incident as ic                                   # noqa: PLC0415
        obs = ic.Observer(rooms[0], policy="citizen") if rooms else None
        return ic.visible_bodies(rooms, day=day, seed=seed, observer=obs)
```

**Do not apply this without deciding it deliberately.** It changes a shipped artefact's contents
for every deck, and "the player helped everyone all day" is as much a lie as "the player was never
there". The honest runtime version is 2.

### 2. `godot/scripts/main.gd`, in `_fire_collapses`

The row already says whether helping would have stopped the body hitting the deck. The runtime
piece is: when the player is inside `COLLAPSE_SIGHT_M` of the place at the row's hour AND presses
the interact verb before the promotion fires, skip the promotion and log the assist:

```gdscript
	if bool(row.get("if_helped", false)) and _player_assisted(row):
		_helped += 1
		continue
```

`_player_assisted` does not exist and is the actual work; it wants `interact.gd`'s verb set to
carry HELP/REPORT, which is G2's surface rather than G3's.

### 3. The measurement that should follow it

`incident.absence()` already answers the question a runtime fork would need to be judged against
— same seed, same stream, two worlds — so the engine side needs no second model, only a call.

### 4. `station/compress.py` — the cheapest live runtime hook in the project, and it is 2 lines

This is the one worth doing first. `godot/scripts/interact.gd`'s SLEEP/WAIT verb calls
`compress.advance(now_h, wake_h, at_place=...)`, which runs `incident.simulate(..., scope=[at_place])`
one station-hour at a time — **the player is demonstrably standing (lying) in `at_place` and every
incident during the night still resolves ABSENT.** `simulate` now takes `observer=`:

```python
    obs = inc.Observer(at_place, policy="absent")   # asleep: present, cannot act
    ...
        world, f = inc.simulate(ctx, world, start_h=prev, window_min=window,
                                scope=[at_place], observer=obs)
```

`policy="absent"` is the correct policy for a sleeping player and is byte-identical to today, which
is the point: it makes the observer *present in the call graph* with no behaviour change, so the
day WAIT (`interruptible=True`, awake) can then pass `policy="citizen"` and the change is one
argument rather than a new code path. `incident.absence()` is the A/B that judges it.
