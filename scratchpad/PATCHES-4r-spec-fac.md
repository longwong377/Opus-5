# PATCHES wanted by `station/spec_harness/fac.py` (FAC family, 28 rows)

Written rather than applied: the FAC harness owns `station/spec_harness/fac.py` and
nothing else, and every item below is a change in a file another agent may be holding.
Each is a **disagreement between `docs/spec/PEOPLE.md` §1 and the code**, with both
numbers, so whoever applies it can decide which side is wrong. The harness is NOT
weakened to hide any of them — all three are live RED rows today.

---

## 1. FAC-01 — `minipax` is faction territory in the spec and not in the register

* spec (`docs/spec/PEOPLE.md:63`): **Territory:** `law_courts`, `customs_north`/`customs_south`,
  `quartermaster`, `post_office`, `business_center`, **`minipax`**, `admin_complex` — **8 keys**
* code (`station/npc/faction.py`, FAC-01 entry): the same list **less `minipax`** — **7 keys**
* `minipax` **is** a live place: `directory.PLACES` carries it, so this is not a
  pending-address case (it is not in `faction.PENDING` either).

The row also names a MiniPax political officer and MiniPax notice postings among its
incidents, so the omission is not a deliberate narrowing — it reads as a dropped entry.

**Suggested fix:** add `"minipax"` to FAC-01's territory tuple in `npc/faction.py`.

## 2. FAC-21 — `garden_town` likewise

* spec (`PEOPLE.md:434`): **Territory:** `hydroponics`, `garden_town` labour — **2 keys**
* code: `("hydroponics",)` — **1 key**
* `garden_town` is in `directory.PLACES`.

The Grome's second friction row (*"Grome↔Drazi ... the recurring quality dispute at the
transfer deck"*) and their ACCEPT are hydroponics-side, but the row's own labour claim is
the drum town.

**Suggested fix:** add `"garden_town"` to FAC-21's territory tuple.

## 3. FAC-04 — the Nightwatch head-count is the VISIBLE share, and the spec's is membership

This one is a modelling disagreement rather than a typo, and it should be ruled on rather
than patched blind.

| | number | where |
|---|---|---|
| spec, armbanded officers | **150–200** | `PEOPLE.md:119`, quoting `NIGHTWATCH_SHARE=175/500` |
| code, armbanded officers | **175** | `security.NIGHTWATCH_SHARE × role_headcount("security")` — **agrees** |
| spec, civilian informers | **1,500–3,000** ("1–2% of 155,000 humans") | `PEOPLE.md:120–121` |
| code, civilian informers | **2,325** = 155,000 × `costume.NIGHTWATCH_CIVILIAN_INFORMER_RATE` (0.015) — **agrees** |
| code, informers COUNTED into the faction | **697** = 2,325 × `NIGHTWATCH_CIVILIAN_VISIBLE_FRACTION` (0.3) | `faction._flag_population("armband")` |
| **`faction.head_count("FAC-04")`** | **872** | 175 + 697 |
| what the spec's two numbers imply | **1,675 – 3,175** | |

`head_count`'s own docstring is *"How many people this faction has aboard"*, and an
informer is a member whether or not they are visibly wearing anything today. The visible
fraction belongs to the RENDER question (who is identifiable in a corridor), not to the
census question.

`npc/faction.py::_selftest` cannot see this: its assertion is `150 <= nw <= 3200`, which is
wide enough to pass on either reading — the band contains both 872 and 3,175.

**Suggested fix, whichever is ruled correct:**
* if `head_count` means membership — drop `NIGHTWATCH_CIVILIAN_VISIBLE_FRACTION` from
  `_flag_population("armband")` (it stays in `costume` for the sleeve), giving 2,500; or
* if it means visible-in-a-corridor — say so in `PEOPLE.md` FAC-04's Numbers clause and
  give the visible number beside the membership one, so the row states what the code
  computes.

---

## 4. `spec_check.py`'s summary line counts a DISAGREEMENT as "nothing checked at all"

Not mine to edit (`spec_check.py` is shared), and it misreports exactly the rows this
harness exists to produce:

```python
red += 1                       # harness ran, returned False
...
print(f"... which is a different kind of red from the {red - partial} that nothing "
      f"checked at all.")
```

`red - partial` is *unimplemented* + *ran and failed*, and the message calls all of it
"nothing checked at all". Today that hides three FAC rows (FAC-001, FAC-004, FAC-021) whose
harness ran, disagreed with the code, and said why — the most informative state a row can
be in, reported as the least.

**Suggested fix:** count a third bucket, e.g. `disagreed`, incremented in the
`if not ok:` branch, and print `"{red - partial - disagreed} that nothing checked at all,
{disagreed} where a harness RAN AND DISAGREED"`.

---

## Minor, no action required, recorded so it is not rediscovered

* `NIGHTWATCH_SHARE` is defined **twice** — `npc/crowd.py:1103` (`0.35`) and
  `npc/security.py:105` (`175.0/500.0`). Same value, two definitions; the FAC-04 row cites
  the security one. A second copy of a computed number is the shape CLAUDE.md warns about,
  but nothing disagrees today.
* `faction.head_count("FAC-06")` is **10,050**, which is no number FAC-06 states: the row's
  three denominators are 9,650 dockworker heads / 1,500 guild-carded / ~1,200 EA payroll,
  and the register adds the 400 `traffic` heads to the Guild. The harness does not fail the
  row for it — all three stated numbers check out and the extra clause is a defensible
  modelling choice — but if the Guild is meant to be dockers only, the `("role","traffic")`
  clause is the thing to remove.
