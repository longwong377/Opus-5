# PATCHES owed by g3_incidents (session 4t, round 3) — files I do not own

I own `station/incident.py` and `station/journal.py` only. These are changes in other people's
files that my work implies. None of them is required for `python3 station/incident.py --accept`
to pass; each makes the join harder to lose later.

## 1. `.github/workflows/validate.yml`, step `sincident` — run the acceptance, not only the gate

The step currently runs `--selftest` and `--gate`. Both now cover the whole class table (I
tightened `gate()`'s `len(three) >= 20` to `== len(CLASSES) - len(STANCE_EXEMPT)`), but the two
new joins have their own flags and CI does not execute them:

```yaml
          python3 station/incident.py --selftest
          python3 station/incident.py --gate
          python3 station/incident.py --ledger        # ~30 s + one 5 s Godot launch
          python3 station/incident.py --stance-table  # ~15 s, all 30 classes
```

`--stance-sweep` (1,557 combinations, 1m40s) and `--accept` (1m24s) are deliberately NOT proposed
for CI: the two above cover the same defects at a tenth of the cost, and CI here is already a
liability at its current length.

`--ledger`'s last check launches Godot and reads `journal.gd`'s own `journal: N kinds, M ledgers`
line. It **skips with a printed reason** when there is no `boot.json` or no binary; it never
builds a deck and never substitutes a number.

## 2. `station/generated/journal.json` is TRACKED and must be re-emitted when `STANDING_BLOCKS` changes

This is the join that would have been silently lost. `journal.gd` initialises one standing
accumulator per key it finds in that file. I added five blocks to `journal.STANDING_BLOCKS`, and
until `python3 station/journal.py --emit` was run and the result committed, **the engine reported
`journal: 8 kinds, 8 ledgers` while the station moved 13** — verified by reverting the file and
re-launching. I have committed the regenerated manifest. Anyone touching `STANDING_BLOCKS` must do
the same; `incident.py --ledger` is the gate that catches it.

## 3. `station/boot.py` — nothing is required, and here is why, so nobody builds it twice

The brief offered a second route for getting standing into the engine: bake the day's deltas into
`boot.json` beside `collapses`. I did **not** take it and I do not recommend it. Standing is
per-save player state, not per-deck world state: `journal.Journal` already round-trips through
`player.Player.state()`, and `journal.gd::load_state` already restores a standing dictionary. A
copy in `boot.json` would be a second source for a number that has an owner — the same shape as
the cached collision total this repository already regrets.

What `boot.py` *could* usefully carry is the **counterparty vocabulary** for a first run, but
`journal.json` is already that file and already reaches the engine.

---

# ROUND 4 ADDENDUM — one new patch, and one correction to §1 above

## 4. `station/incident.py --accept` NOW REQUIRES A DECK, and §1's CI proposal must account for it

`ledger_gate`'s engine check used to be skipped — **and skipped without counting**, because
`n += 1` sat inside the `else` of `if got_n is None`. A worktree with no
`station/generated/scene/boot.json` therefore printed `45/45 passed` and a checkout with a deck
printed `46/46`, and both read as a clean pass. That is a gate that vanishes rather than fails,
and it is why round 3's report and round 3's reviewer disagreed about the denominator without
either of them being wrong.

The denominator is now a constant **47** and a missing engine is a FAILED check whose message
names the fix. Consequence for CI: the `sincident` step's `--ledger` line (proposed in §1 above)
still works, but if the runner has no deck it will now go RED rather than printing a skip. Either
give the step a deck, or run `--gate`/`--stance-table` only, which need none. I have NOT changed
`.github/workflows/validate.yml` — it is not mine.

In this container the deck was made reachable without building one, and it is the cheapest route
for a reviewer too:

```bash
ln -sfn /home/user/Opus-5/station/generated/scene <worktree>/station/generated/scene
```

## Correction to §3 — `boot.py` is still not needed, and now there is a second reason

§3 argued that standing belongs on the player's save rather than in `boot.json`. That still holds.
The round-4 addition is that `ledger_gate` now carries the SAME `journal.Journal` through three
days and asserts `clamp(previous + today)` per row against `journal.STANDING_MIN/MAX` — a
statement about accumulation over time, which a per-deck manifest could not carry at all.
