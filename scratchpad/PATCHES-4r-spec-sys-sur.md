# PATCHES requested by the SYS/SUR harness — `docs/spec/SYSTEMS.md`

Written rather than applied, because `docs/spec/*` is not this agent's to edit and
because a harness that edits the spec it checks proves nothing. Every item below is
a **live failure** of `station/spec_harness/sys.py` or `sur.py`, reproducible with
`python3 station/spec_check.py --id <ID>`, and each one has a negative control in
the module's own `_selftest` that turns it off when the patch is applied.

Six of the seven patches are to the ANNEX (the spec is wrong about the code). One
is to a tool. **None of them should be applied to make a harness pass** — apply
them because the number is wrong.

| # | row | the annex says | the code/repo says | patch |
|---|---|---|---|---|
| 1 | SYS-04 | `CREDIT_MIN/MAX exist, player.py:140-174` | they are at **192-193**; 140-174 is INV-410's inventory-slot comment, inserted in session 4q | `player.py:186-196` |
| 2 | SYS-06 | *"the route's five stations"* (State) and *"the route's five stations when followed"* (CHECK) | `security.BLACK_MARKET_ROUTE` has **six**: cargo_bays, dock_workers_quarters, raw_material, alien_sector, black_market, zocalo | either write **six** in both places and add `black_market` (the margin stall) to the parenthesised list, or delete the sixth node from `security.py` — a decision, not a typo |
| 3 | SYS-10 | no **Tick:** field at all | the format law at SYSTEMS.md:5-7 says a field an item lacks is written `none`, never omitted. SYS-10 is the only one of the 25 SYS+SUR rows missing one, and its State declares exposure timers, a `drunk` condition that "decays by morning" and a therapy queue — all things that tick | add a real Tick line (not `none`) |
| 4 | SYS-14 | *"the **22-class union below**"* | the table is **30** rows, `incident.CLASSES` is **30**, and the row's own CHECK eight lines later says *"the 30-row union above"* | `22-class` → `30-class` |
| 5 | SUR-01 | *"corridor (already 4)"* | `docs/aaa-scorecard.json`: `interior_kit` 3, `concourse_central_corridor` 3, `walkable_deck` 3. Nothing corridor-shaped is filed at 4 | drop "(already 4)", or file the round that makes it true |
| 6 | SUR-05 | `harness: tools/measure_frame.py --gate-frames --rerender (exists)` | `measure_frame.py` has neither flag — it exits 2 with *"unrecognized arguments: --gate-frames"*. Both belong to **`tools/export_scene.py`** | `tools/export_scene.py --gate-frames --rerender`. CLAUDE.md's layer-4a/4b rows carry the same wrong tool name and want the same correction |
| 7 | SYS-02 | *"tanker 0.3 (… SPEC-CHANGE #3, **code pending**)"* | the code is no longer pending: `traffic.MANIFEST` carries `("tanker", 0.3, "standoff", …)` and sums to 55.0 with it | drop "code pending" |

## Not a patch — two definitions the spec owes a harness

* **SUR-07** asks for *"≥10 viewpoints"* and nothing defines a viewpoint. The register
  carries **4** places with an `observation`/`viewport` function, but `obs_rotundas` is a
  class row standing for four rotundas, so 4 register rows may well be ≥10 viewpoints.
  `sur.py` reports the count in its note and refuses to assert it. Define the term and the
  check becomes mechanical.
* **SYS-05**'s *"escalation ladder 7 rungs"*, **SYS-09**'s *"70 shafts"*, **SYS-12**'s
  `K=3` and **SYS-07**'s *"three rosettes"* / *">98% closure"* name no code object at all.
  They are unfalsifiable as written; each is listed in its row's note as NOT checked.
