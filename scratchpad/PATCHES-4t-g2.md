# PATCHES owed by g2_progression (session 4t, round 2) — files I do not own

I own `station/enforcement.py` and `godot/scripts/enforcement.gd` only. Everything below is a
change in somebody else's file, written out rather than applied.

---

## P1 — `station/economy.py`: no restricted good is sellable in any shipped room

**Severity: this is the whole reach gap for G2.** `enforcement.gd::_contraband()` reads
`_player.carrying` and matches it against `economy.GOODS`' own `contraband` class, so the search
branch — the *only* branch that demotes anybody, because grade 3 is the one
`REVOKE_ON_SERIOUS = 1` acts on — needs a contraband good in the player's bag. Measured from
`station/generated/economy.json::stock` against `station/generated/scene/boot.json::rooms`:

| good | stocked at | in the shipped rooms? |
|---|---|---|
| identicard blanks | `black_market` | no |
| Dust | `downbelow` | no |
| forged transit visas | `downbelow` | no |
| weapons parts | `ngrath` | no |

`boot.json::rooms` is `['arrival_concourse', 'customs_north', 'customs_south']`. So **0 of 4**,
and the only route into a search is the harness flag `--arrest-contraband`, which is a test
fixture and not a place. `enforcement.py::restricted_sources()` bakes this table into
`enforcement.json::restricted_from` and `enforcement.gd::_load` prints it on every run, so the
gap is now visible from inside the game — but it is not closed.

**Two ways to close it, and the first is better because it is a place rather than a shop:**

1. **Add a fence to the arrival deck.** `security.BLACK_MARKET_ROUTE` and `dialogue.py`'s Broker
   pool already exist; `downbelow` or `black_market` reaching `boot.json::rooms` would make the
   whole thing reachable with no change to any stock table. This is a `boot.py` scope change.

2. **Seize-and-plant at customs.** Give `arrival_concourse` a baked `holds` entry that puts a
   `contraband`-class good into the player's bag on a declared route (the courier job that pays
   too well). This is an `economy.py`/`interact.gd` change.

Until one of them lands, `--arrest-contraband` is honest as a *harness*, and the claim
"a player can walk into a search" is NOT true and is not claimed anywhere in my output.

---

## P2 — `godot/scripts/interact.gd`: `_led` is read by capability-less `get()`

`enforcement.gd::_day()` needs the LEDGER's day, because `interact.gd::convict` writes
`"day %d: ..."` into the record from `_led.day` and `enforcement.py::bookings` reads that note
back to recover the day it re-derives the brig cell from. If the two disagree the record names a
different cell from the one the player was held in — which is a real failure, and
`enforcement.py::_prog_money`'s fourth check fires on it (shown failing: engine cell 11,
`bookings()` cell 22).

I read it as `_interact.get("_led")`, which works but is a name lookup, and this file's own rule
is *find a node by capability, not by name*. **The one-line patch:**

```gdscript
## The ledger's day, for anything that has to agree with what `convict` writes
## into a record note.
func ledger_day() -> int:
	return int(_led.get("day", 0))
```

then `enforcement.gd::_day()` becomes `_interact.has_method("ledger_day")`. I have left the
`get()` in place with a fallback to the baked day, so nothing breaks either way.

---

## P3 — `station/boot.py`: the shipped deck is three rooms and one selftest reads it as a defect

Not mine and not caused by me, recorded because it is red at `origin` right now.
`enforcement.py --selftest` check 3, *"response time VARIES across the deck"*, reads
**0 s at the nearest, 1 s at the furthest** and fails. It read `0 s .. 227 s` and passed in
round 1. Nothing in the arrest chain changed; `boot.json::rooms` did — it now holds only
`arrival_concourse`, `customs_north`, `customs_south`, which are metres apart, so the routed
spread is genuinely 1 s and the check is correctly reporting a scope that no longer contains the
contrast LAW-CRIME 2.6 is about. It is a **scope** finding, not a routing defect: with
`--all` the same function still spans the station. Either widen the boot deck or scope the check
to `checked_places()` rather than `boot_rooms()`.

---

## ROUND 4 — what is owed to files g2 does not own

Nothing is owed to the **wf-aaa-4t** workflow's list (`economy.py`, `consequence.py`,
`player.py`, `dialogue.py`, `broadcast.py`, `boot.py`, `stream.gd`, `bake_station.py`,
`bootstrap.py`, `collision.py`, `deck.py`, `npc/body.py`, `npc/costume.py`, `export_scene.py`,
`observation.py`, `drum_ground.py`, `drum_dressing.py`, `spec_harness/*`). Round 4 touched only
`station/enforcement.py`, `godot/scripts/enforcement.gd`, `godot/scripts/interact.gd` and
`godot/scripts/player.gd`, and `station/player.py`'s rule — *"a stored tier would be a second
description of what the card already says"* — is now obeyed by both of `player.gd`'s loaders
rather than by one of them.

## One item, for whoever owns `godot/scripts/main.gd`

The round-3 verifier proposed adding `body.tier` to `main.gd::_save_gate`'s perturbed-and-compared
set, so that the save gate can fail for a stored rung. **I did not apply it and I think it is the
weaker of the two available checks**, for a reason worth recording rather than a preference:

`_save_gate` perturbs a field, restores, and asserts the field came back. After round 4 the rung is
**not restored** — `player.gd::load_state` re-derives it through `set_purse`/`rung_of`. So a
perturbed `body.tier` comes back correct *because the derivation is right*, and it also came back
correct in the pre-fix build *because the stored copy was right*. **The check passes either way**,
which is the shape of an assertion that cannot fail.

The distinguishing evidence is the **artefact**, and that is where
`station/enforcement.py::_prog_save` now asserts: the player section of `user://saves/gate.json`
must carry no `tier` key at all. It is run by
`python3 station/enforcement.py --ensure --gate --progression`, with two controls
(`--player-saved-rung`, `--player-stale-save`) that make it go red.

If `main.gd`'s owner still wants a rung row in the save gate, the one that can fail is:
**perturb the LEDGER's record between capture and restore** (add a conviction to
`_interact`'s purse after `save_to("gate")`), then assert the rung after `load_from("gate")` is the
one the *new* record implies. That is the case where a stored rung and a derived rung genuinely
disagree, and it is the only one inside a single process that does.
