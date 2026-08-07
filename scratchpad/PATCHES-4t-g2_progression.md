# Patches owed by g2_progression to files it does not own

Written rather than applied, per the batch rule: `station/player.py`,
`station/interact.py`, `station/directory.py` and `godot/scripts/interact.gd` belong to other
agents in this workflow, and two agents in one file is the stomped-artefact defect
`CLAUDE.md` records three times. Each item below states what it costs to leave undone.

---

## P1 — VRB-09 is still RED and it is **two lines in two files I do not own**

`station/spec_harness/vrb.py::_v_fight` asks:

```
PLC-017 `brig` holds a readable booking record
  -> declares ('cell_door', 'bunk', 'intercom'); 0 of them answer LOOK with anything
```

It needs (a) a declared interact whose name matches `record|booking|charge|log`, and (b)
`interact.read_text("brig", <that token>)` returning something non-empty. **The record itself is
built and readable** — `station/enforcement.py::booking_lines(purse)` returns it, derived from the
purse, and `--progression-gate` prints it:

```
BABYLON 5 SECURITY -- CUSTODY DESK, BRIG
  BOOKED   IVANOVA, AMIS (player:g2c)
  1. CONTRABAND, day 3 -- grade 3, escalation rung 4
     CELL 22 of 32   FINE 206.63 cr
     6.5 names Dust and concealed weapons; arrival.checks station 9 refers on
  STANDING TRANSIT WITHDRAWN -- rung 0 no_status
  PAID     206.63 cr; OUTSTANDING 0.00 cr; 19.0 h in custody
```

**`station/directory.py`** — PLC-017's row (line ~186), add the fourth interact:

```python
    _P("brig", "The brig / holding cells", "red", 2, 1, 206.0, 6600.0,
       ...
       interacts=("cell_door", "bunk", "intercom", "booking_record"),
```

**`station/interact.py`** — in whatever table `read_text` dispatches on, route that token to the
record rather than to a new string, so there is one booking record and not two:

```python
    if place_key == "brig" and token in ("booking_record", "custody_log"):
        import enforcement as EN                              # noqa: PLC0415
        import economy as ec                                  # noqa: PLC0415
        try:
            led = ec.Ledger.load()
        except Exception:
            return "CUSTODY DESK -- no ledger; nobody has been booked"
        purse = next((v for k, v in sorted(led.purses.items())
                      if k.startswith("player:")), {})
        return "\n".join(EN.booking_lines(purse))
```

Note the shape deliberately: `booking_lines` takes the **purse dict**, not a path and not a
Player, so it works against whatever ledger the caller already has open. It is a pure reading —
it writes nothing and stores nothing.

**Cost of leaving it:** VRB-09 stays RED, and a player standing in the cell cannot LOOK at the
thing that says why they are in it. The loop closes without it; the *legibility* does not.

---

## P2 — the purse's stored `tier` goes stale after a demotion (`godot/scripts/interact.gd`)

Observed, in the passing run:

```
ARREST ledger cr 2402.00 -> 1839.02 (-562.98), convictions 0 -> 3, tier 2 -> 2.0
ARREST reload rung=0(no_status) from a clean card at rung 2(transit); revoked=True from=transit
```

The **derived** rung is 0 and correct — `player.py` deliberately does not store the rung as a
fact, and `Player.tier` is `consequence.tier_of(card, record)`. But `interact.gd::convict` sets
`_player.tier = tier_after` and does **not** refresh the purse's `tier`/`tier_name` report fields,
so the document carries `tier: 2` beside a record that reads 0.

Nothing in this session depends on it — `_reload_line` re-derives rather than trusting the field,
and says so. But any consumer that reads `purse["tier"]` directly gets the pre-arrest rung, and
`player.from_state` **raises** on a stored/rebuilt mismatch:

```
ValueError: the purse says rung 2 and the rebuilt card says 0
```

which means a save written by the engine after a demotion can make a Python reload throw. That is
the sharp end of it and it is worth closing.

**Fix** — one line in `convict`, after `_put_record(rec)`:

```gdscript
	if revoked:
		var st := _my_purse()
		st["tier"] = tier_after
		st["tier_name"] = tier_after_name
		_led_dirty = true
```

*(The float `2.0` in the printed line is Godot's JSON writing an int as a double; harmless, but it
is why the delta line reads `tier 2 -> 2.0`.)*

---

## P3 — `station/player.py`: nothing is owed, and that is worth recording

Checked, because the brief asked. `Player.take` respects `bag_full()`, `state()` emits `record`
only when the record is not clean, `restore()` reads it back, and `tier` is derived. **Every part
of the persistence half of G2 worked without a change to this file.** The reason the loop did not
close was never here.

---

## P4 — a defect this session found and fixed inside its own file, flagged because it is a pattern

`godot/scripts/enforcement.gd` read `hud.gd::_boxes` for every place lookup. `hud.gd::bind` fills
`_boxes` from the interact sidecar **only if** `_place_boxes` (the mesh extents, via
`places.gd::boxes`) came back empty. So on any build where the deck geometry loads, `_boxes` is
`{}` and the gate printed

```
ARREST gate=FAIL -- nothing on this deck refuses a tier-0 card
```

— a sentence about the **card**, on a run where the real cause was an empty dictionary. Fixed
here by `_box_of()`, which prefers the geometry and falls back to the sidecar.

**And the pattern is the interesting half, because the fix already existed one file away.**
`main.gd::_check_boxes` (line 1885) does exactly the right thing — `_place_boxes` first, the
sidecar padded 1.5 m as a fallback — and has done all along. `enforcement.gd` was written against
the raw dictionary instead of against that function, so a solved problem was re-introduced by a
second reader who did not know it had been solved. That is `CLAUDE.md`'s *"a fix applied to an
instance and not to the rule is a fix that will be needed again"*, with the roles reversed: the
rule was right and the new instance took the old shape.

**No patch is owed** — `grep -n '_boxes' godot/scripts/*.gd` shows the only other user is
`arrival.gd`, whose `_boxes` is its own unrelated group→centre map. The action, if anyone wants
one, is to make `_check_boxes` reachable (it is private to `main.gd`) so a third reader cannot
make the same mistake a third time.

---

## ROUND 3 — nothing is owed by another owner, and two findings are reported here

**No patch is needed from the wf-aaa-4t workflow.** The round-3 defect (a demotion that did not
survive a quit) lived entirely in `godot/scripts/player.gd` and `godot/scripts/interact.gd`, which
that workflow does not own, and the fix is consistent with `station/player.py`'s existing rule
rather than a change to it: `state()` still writes `tier`/`tier_name` as a REPORT, `restore()`
still refuses to load them back, and the engine now re-derives the rung the same way
`Player.tier` does. If anything, `player.py`'s comment at `state()` — *"Restoring them would be a
second copy of a derivation, which is how a saved tier survives a conviction"* — is now true of the
engine too, and was not before.

**Finding 1, pre-existing and NOT mine.** `python3 station/enforcement.py --selftest` fails one of
its 21 checks on `origin/claude/aaa-game-development-j6y2ml` untouched:

    FAIL response time VARIES across the deck -- 0 s at the nearest, 1 s at the furthest
    enforcement selftest FAIL -- 21 checked, 1 failed

Verified by running the same command against the unmodified file in a second checkout. The three
boot-deck places are close enough together that the turn-out spread rounds to one second, so the
check is asking a whole-station question of a three-place table. It is a real gate on a real
claim; it just cannot be answered on this deck. Whoever owns it should either widen the subject to
`--all` or state the deck's own span as the bar.

**Finding 2, already recorded in code and still open.** `restricted_sources()` reports *4 places
sell a restricted good, 0 of them in this build's rooms* — so `--arrest-contraband` remains the
only route into a search, and a player cannot reach the grade-3 branch by playing. `economy.py` is
not mine; the stock entry that would close it is the one this file already carried above.
