# PATCHES — spec harnesses for ROLE / CAST / DLG (session 4r)

Changes wanted in files this agent does not own. Nothing here has been applied.
Each item says what, where, and why, with both numbers where there are two.

---

## 1. `station/spec_harness/__init__.py` — `SUFFICIENT` is per MODULE and a family is not homogeneous

**The contract today:** one `SUFFICIENT: bool` per family module.

**Where it breaks:** the CAST family holds six rows that are not the same kind of
question. **CAST-04**'s acceptance is *entirely* headless — *"render the identicard
of npc_id 0, 124,999 and 249,999: all 9 fields; a Gaim draw shows SEX=HIVE …;
STATION_HEADCOUNT still sums 250,001 with Kosh outside the statistical draw"* — every
clause is a function call, and `spec_harness/cast.py` runs all of them. **CAST-05**'s
is *"save, reload, return next day"* against a memory system the row's own text says
does not exist. One boolean has to cover both.

`cast.py` resolves it by setting `SUFFICIENT = True` **and** writing every one of the
six checks so a `True` return means that row's own ACCEPT was met — five of the six
therefore fail today with a measured number, and none has a branch that passes on
absence. That works, but it puts the honesty contract in a docstring instead of in the
dispatcher.

**Suggested:** let a module optionally export

    def sufficient(row) -> bool

and have `spec_check.harness_for()` prefer it over the module constant when present.
Two lines in the dispatcher; it lets a family say *"this row is settled, that one is
address-only"*, which is the true state of at least CAST and probably SHB.

---

## 2. `docs/spec/PEOPLE.md` ROLE-04 — two stale code citations (do NOT apply without an owner/spec-change call)

`ROLE-04`'s Seated-by line reads:

> serve_response already puts named staff behind 29 counters (**dialogue.py:1314**,
> **interact.py:120–126**)

Measured:

| cited | actual |
|---|---|
| `dialogue.py:1314` | `serve_response` is defined at **dialogue.py:1704**; line 1314 is inside `SAY`, the player-utterance table |
| `interact.py:120–126` | the "29 counters across 27 register places" sentence is at **interact.py:131**; 120–126 is the `sit`/`rest` note |

`spec_harness/role.py` fails ROLE-004 on exactly this. The fix is a spec edit and this
agent is forbidden from making it (rule 5: do not edit the spec to make the harness
pass). It is one line of the annex and wants an owner or the annex's author.

---

## 3. `docs/spec/PEOPLE.md` DLG-03 — the counter arithmetic is one counter and one place stale

> serve_response's **29 counters across 27 places** (interact.py:120–126) each add ≥6
> place-specific trade lines … = **174**

Measured from `dialogue.serve_places()` / `serve_tokens()`:
**30 counters across 28 places**, so the derived floor is **180**, not 174.
(`zocalo` and `shops_kiosks` each carry two tokens — `market_stall` + `shopfront`.)

This is a *recomputes* edit under the SPEC-CHANGE discipline, not a typo fix: the
annex's grand floor 6,544 moves with it.

---

## 4. `docs/spec/PEOPLE.md` CAST-04 vs `station/npc/resident.py` — the Gaim card's DES/ATMOS

The row's ACCEPT wants *"a Gaim draw shows SEX=HIVE and **DES-ATMOS methane**"*.

`resident.ATMOS_NUMBER` is `{'standard_oxygen': '02', 'humid_oxygen': '',
'methane': '', 'undisclosed': ''}` and the comment above it is a decision, not an
omission: *"`schedule.py` already refuses to number the other five of the six standing
atmospheres … nothing numbers them, and a wrong number printed on a wall is worse than
a blank."* So a Gaim card renders **DES/ATMOS empty**; the methane fact is carried by
`atmos_class='methane'`, `MEDICAL='NON-STD ATMOS REQ'` and `PHYS CHR='ENCOUNTER SUIT'`.

Two defensible resolutions, and the choice is the owner's:

* **spec moves** — the ACCEPT asks for `MEDICAL NON-STD ATMOS REQ` / `atmos_class
  methane` instead of a DES/ATMOS string, which is what the prop can honestly show;
* **code moves** — a methane designation is invented and logged (authority 5), against
  the standing reason not to.

**This one clause is the only thing between CAST-04 and the registry's first GREEN.**
With the clause removed the harness returns
`True, "CAST-04: 3 cards, 9 fields, reproducible; STATION_HEADCOUNT 250,001 with Kosh
outside the draw"` — verified by a positive control.

---

## 5. `docs/spec/PEOPLE.md` §3 preamble vs ROLE-07 — `READ` is not one of the thirteen verbs

The preamble is normative: *"Every loop below is written in the closed player verb set
(THE-STATION §2 … SYSTEMS.md VRB-01..13): LOOK, USE, TAKE/PLACE, SIT, BUY/SELL, TALK,
WORK, SHOW-PAPERS, FIGHT/RESTRAIN, PILOT, RIDE, SLEEP, EAT/DRINK."*

ROLE-07's shift reads *"→ **READ** gauges [T1→T2] → USE valve/breaker [T2]"*. `READ`
is not in the set. Either the shift means `LOOK`, or the verb set is fourteen and
SYSTEMS.md needs a VRB row.

Not gated by `role.py`, deliberately, and the measurement is in that module's
docstring: extracting shift verbs by ALL-CAPS token yields 41 distinct non-verb tokens
across the twelve rows and would report 10 of 12 as malformed. This one was found by
reading.

---

## 6. `station/npc/names.py` vs CAST-01's ACCEPT — the show-cast pair is drawable

CAST-01's ACCEPT: *"a grep of the shipped cast registry finds **no show-cast
given+surname pair**"*. CAST-01 rule 4 separately permits canon surnames in the generic
pool.

Measured: **8** canon given+surname pairs are constructible from `HUMAN_GIVEN` ×
`HUMAN_SURNAME`, and **28 of the first 2,000 human npc_ids draw one** —
`resident._split_name("human", "19")` is **Susan Ivanova**. Extrapolated over the
155,000 humans in `STATION_COUNTS` that is a four-figure number of collisions.

The pools are deliberate and well-argued (`names.py:100–124`: sexes had to agree with
given names, and *"NOTHING IS INVENTED HERE"*). The conflict is real anyway. Cheapest
fix that keeps both: a rejection rule inside `_split_name` — redraw the surname when
`(forename, surname)` is one of the pairs the module's own comment lists. Costs one
`while`, keeps every name in the pool, and makes CAST-01's ACCEPT true.

---

## 7. Not a patch — three content gaps CAST-01's ACCEPT names and nothing supplies

The row requires the offscreen senior offices to be *reachable as content*:

* a name-plate at `cnc` — no name-plate content exists in the command modules
  (`council_chamber.py` has delegate nameplates; that is a different room);
* a PA order in the CO's name — `broadcast.py` has no CO/station-commander voice;
* *"the Ambassador is not receiving"* — the string exists nowhere in `station/`.

All three are small authored content and would move CAST-01 most of the way.
