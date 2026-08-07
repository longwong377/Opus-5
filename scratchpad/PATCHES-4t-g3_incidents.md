# PATCHES owed by g3_incidents to files another workflow owns

Written, not applied. `station/boot.py` and `godot/scripts/main.gd` belong to wf-aaa-4t this
session. Everything below is verified against `station/incident.py` at the commit that carries
`collapse_gate`, and each one is a one- or two-line change.

---

## P1 — `station/boot.py:295` — the baked collapses are unconditionally the ABSENT day

**Now:**

```python
        import incident as ic                                   # noqa: PLC0415
        return ic.visible_bodies(rooms, day=day, seed=seed)
```

**Wanted:**

```python
        import incident as ic                                   # noqa: PLC0415
        # THE PLAYER IS IN THE ROOM. `visible_bodies` resolves every row under
        # the ABSENT stance when no observer is passed, which is what the deck
        # does when nobody intervenes -- correct for a bake that runs before the
        # player has chosen anything, and wrong the moment the deck it is baking
        # is the deck the player spawns on. The observer is built from the
        # deck's own spawn room, so a row's `stance` is what a player standing
        # there would have produced.
        obs = None
        try:
            obs = ic.Observer(rooms[0], policy="citizen")
        except Exception:                                       # noqa: BLE001
            pass
        return ic.visible_bodies(rooms, day=day, seed=seed, observer=obs)
```

`visible_bodies` already takes `observer=` and already prints which one it used
(`observer=none (absent)` today). Nothing else changes.

**Caveat, and it is why this is P1 and not P0.** On the shipped deck the array is empty either
way — see P2. The patch stops the rows being *unconditionally* absent; it does not by itself put
a body on the deck.

---

## P2 — `station/boot.py` — the shipped bake asks for day 1, and day 1 is empty

**The finding, measured by running the shipped bake** (`python3 station/boot.py --bake`) and
reading its own stderr:

```
incident.visible_bodies: 0 collapse row(s) over 3 place(s), observer=none (absent);
  0.232 expected a day from 1 ragdoll class(es) here, so P(a day like this one is empty) = 0.79
incident.visible_bodies: EMPTY -- and it is a RATE, not a break: INC-SICK 0.2323/day.
  The first day in 1..10 that puts a body on this deck is day 5
```

The committed `station/generated/scene/boot.json` carries `"collapses": []`. So
`main.gd::_fire_collapses` has never fired on the shipped build, and `_collapse_gate` has nothing
to pick from. It is not a break — the shipped deck is `arrival_concourse`, `customs_north`,
`customs_south`, the only ragdoll class reachable in those three is INC-SICK at 0.2323/day, and
`_collapses(rooms)` asks for **day 1 only**.

Three ways out, in order of honesty. **Do not raise INC-SICK's rate** — that is tuning content
until a number goes green.

1. **Bake a horizon, not a day.** `_collapses` gains `days=` and concatenates, tagging each row
   with its day; `main.gd` already carries a clock and could fire only the current day's rows.
   `incident.collapse_first_day(rooms, seed="b5", max_days=10)` returns **5** for this deck, so a
   five-day horizon is the smallest one that is not empty and a ten-day one has P(empty) = 0.098.
2. **Widen the baked scope to the deck's PROBE rather than its rooms.**
   `incident.Probe("customs_north").places` reaches `docking_bays`, where INC-SICK and INC-STRAY
   are common: **49.620 expected a day, first day 1**. The cost is that some rows land in a place
   this deck has no geometry for, which `main.gd:1193` already guards against.
3. **Leave it and say so.** `incident.py --collapses` now prints both numbers on every run, so
   the emptiness is legible rather than silent. This is what shipped.

---

## P3 — `godot/scripts/main.gd` — nothing reads `if_helped` or `stance`

`visible_bodies` bakes two fields no GDScript reads:

* `stance` — `"absent"` / `"helps"` / `"reports"`, what the row was resolved under.
* `if_helped` — whether this body would still be on the deck had the player helped, resolved
  through the class's own HELPS branch rather than guessed.

`_fire_collapses` (main.gd:1065) drops the body and ignores both. The smallest thing that makes
the fork live at runtime: when the player is within `COLLAPSE_SIGHT_M` and presses the interact
verb before the ragdoll settles, re-fire the row with `if_helped == true` meaning the body gets
up. That is the runtime half of P1/G3's *"absent / helps / reports produces 3 distinct world
states"*; the simulation half is done and provable —
`python3 station/incident.py --three-outcomes INC-CONTRA --at cargo_bays` gives three distinct
fingerprints with the diffs named.

---

## Not a patch — a note for whoever owns `docs/spec`

`spec_check --red`'s INC-CONTRA finding is **closed and the spec was not edited to close it**.
`--selftest` asserts the class covers every place `docs/spec/PLACES.md` names for it including
`cargo_bays`, that the `stock` write into `black_market` actually happens there, and the control
that at a hall which SCANS the same class still ends in a seizure and a custody row with nothing
reaching the black market. Run:

```
python3 station/incident.py --three-outcomes INC-CONTRA --at cargo_bays
```
