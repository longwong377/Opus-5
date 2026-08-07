# PATCH TO APPLY AT INTEGRATION — `.github/workflows/validate.yml`

I do not own this file (my list is `godot/scripts/stream.gd`, `station/boot.py`,
`tools/bake_station.py`, `tools/bootstrap.py`), and CLAUDE.md's rule is that a second agent
reports what to apply rather than applying it. This is the review's fix #2, first half.

Add after the existing `Performance budgets` step (it is `continue-on-error` like every other
step, so it obeys the 4e aggregator):

```yaml
      # CAN A BODY GET OUT OF THE CLUSTER IT SPAWNS IN. MASTER-PLAN R5.
      #
      # READ `--allow-unbaked` BEFORE READING THE GREEN TICK. This gate needs a
      # Godot binary and a baked cell set; `station/generated/` is gitignored,
      # so on a hosted runner it has neither and prints
      # `AXIALGATE state=CANNOT-RUN reason=no deck on disk has a cell set`.
      # That state exits 2, `--allow-unbaked` maps ONLY it to 0, and a walk that
      # RAN and FAILED still exits 1 under the flag. Grep the log for
      # `AXIALGATE state=` before believing this step said anything at all —
      # `tools/bootstrap.py --check` is the step that reports the missing bake.
      - name: Can a body walk out of its spawn cluster and back
        id: saxial
        continue-on-error: true
        run: python3 station/boot.py --axial-gate --strict-budget --allow-unbaked
```

## Why `--strict-budget` is on the CI invocation and not on the zero-arg one

The review's charge was fair: an assertion that used to fail was moved behind a flag, and the
zero-arg run's exit 0 depends on that move. Both halves of the answer are now visible without
reading source:

* `AXIALGATE verdict=… handoff=… arrival=… budget=…` is printed on **every** run, red or green,
  with the ratio and the frame count, and it names `exit_driven_by=walk` or `walk+budget`.
* CI passes `--strict-budget`, so the overage **is** in an exit code somewhere.

The zero-arg driver keeps the streaming question separable from the content-cost question
because they have different owners — `station/budget.py` owns the triangle number — and welding
them means the streaming acceptance can never report green while the station is over budget.
That is the 4e shape this repository has already paid for once.

## The honest state of it, measured

| | |
|---|---|
| decks with a cell set on this container | **1** (`blue_0_0`) |
| `cell_manifest.json` deck table | **251** |
| decks the register addresses (`directory.PLACES`) | **71** |
| last full bake recorded in `STATE.md` | **70 decks / 955 cells** |
| which denominator is intended | **nothing in the repository states it** — `bootstrap.py --check` prints all of them and deliberately fails on none |

`axial_gate` now runs **every** deck with a cell set rather than breaking on the first, and
prints `axial gate over N deck(s) with a cell set, of M candidate deck stem(s) on disk`. On this
container that is `1 of 1` and the sentence is the same either way; it stops being the same the
moment a full bake lands, which is exactly when a gate quietly testing 1/71 would be read as
testing the station.
