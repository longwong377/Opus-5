# PATCHES wanted in files this agent does not own — SHB / PLY / GDS harnesses

Written per the session-4r spec-harness brief's rule 4. **Nothing below was applied.**
Each is a disagreement the harness found between two things that both claim to be
authoritative; the harness reports both numbers and does not pick a winner.

---

## 1. `docs/spec/PLACES.md` §4 TOTALS — Blue's Shell B gross disagrees with its own belts

| where | figure |
|---|---|
| §4 TOTALS, Blue row, "Shell B gross m²" | **265,800 (SHB-01/02)** |
| SHB-01's own row | ≈93,700 m² gross |
| SHB-02's own row | ≈172,400 m² gross (incl. annexes) |
| sum of the two | **266,100** |

A 300 m² disagreement. The other four sectors reconcile exactly
(Red 28,000 + 3,706,900 + 14,000 = 3,748,900; Green 369,700 + 9,500 = 379,200;
Grey's three components sum to 709,550; Yellow 12,000).

The likely cause, from re-deriving both: SHB-02's net is 128 × 60 × 16 m² × 1.4 =
**172,032**, and the row rounds that up to 172,400 with the words "(incl. annexes)".
TOTALS appears to have taken the unrounded 93,744 + 172,032 = 265,776 → 265,800. So the
two tables differ over whether SHB-02's annexe allowance is inside the sector total.
**Either is defensible; they cannot both be stated.** Reported by `spec_harness/shb.py`'s
`totals` claim on SHB-001 and SHB-002.

## 2. `docs/spec/PLACES.md` §4 TOTALS — Green is one place short of the register

TOTALS says Green holds **35** places and the total is **128**. `directory.PLACES` holds
**36** in Green and **129** overall. The extra is `markab_quarter` (PLC-129), added in
session 4o; CLAUDE.md's live-numbers table already records 129, and §4 was not
recomputed. Note SHC-01 makes the Markab quarter a *sealed* volume, so there is a real
argument for it not counting as a place — but the register counts it, and the two must
agree. Reported on SHB-006 and SHB-007 (the two Green belts).

## 3. `station/economy.py` — GDS-01's floor, its supply enumeration, and one missing ware

* **Floor:** GDS-01 says "**≥60 named goods at completion**". `economy.GOODS` holds
  **34**. 26 short. Not a defect — a distance-to-done — but it is the row's own gate.
* **Supply enumeration:** the row declares `{drum | hydroponics | import | route}`.
  `economy.py` uses a fifth, **`station`**, on four lines (Jovian Sunspot, water
  containers, salvage lots, Nightwatch pamphlets). Station-made *is* a real fifth source
  and the code is arguably right; the annex should either name it or the code should fold
  those four into an existing source. A one-word SPEC-CHANGE closes it.
* **`pitch-fee scrip`** is named in GDS-01's seed set and has no `GOODS` row. It is the
  only one of the 23 seed items that does not resolve (the other 22 all do, including the
  three that are spelled differently on the two sides).
* **"every one placed behind at least one named counter"**: 7 wares declare
  `sold_by = ()` deliberately — `fusion slush` ("pumped, never craned -- no counter sells
  it"), `Nightwatch pamphlets`, and the five plant/fabrication imports. The code's reasons
  are good; the row's floor forbids them. **The row is what needs the amendment here, not
  the code.** A further 3 (`Abbai wet-farm greens`, `Vree instrument optics`,
  `untaxed brivari`) *do* declare a selling function and still reach no counter's derived
  list, because `goods_list` caps a counter at `MAX_LINES` and ranks by species weight —
  that one is a coverage hole in the code, not in the spec.
* **spoo's price band:** GDS-01 says "spoo sits on a Narn row at **1–2 cr**". Live, 7
  counters carry spoo and **2 quote outside the band** — `fresh_air` 2.31 (Green venue
  ×1.71) and `happy_daze` 0.66 (Grey ×0.5503). The venue multiplier is applied after the
  class band, so a band stated without a venue cannot hold across five sectors. Either the
  row states the band at a Red venue, or `CLASS_BAND["staple"]` needs to be the
  post-multiplier envelope.
* Separately: `zocalo` — the 44-stall market the annex makes the home of "G'Dral's row" —
  does **not** carry spoo in its derived stock (it carries `treel`, the other Narn line).
  Not asserted by the harness, because the row does not say the Zocalo specifically; noted
  because it is the one place a player would look for it.

## 4. `docs/spec/PEOPLE.md` — 5 of the 12 ROLE rows carry no card/visa state

PLY-02's CHECK: "the gating table exists in the registry with **all 12 rows filled**".
Filled: ROLE-01, 02, 03, 06, 08, 09, 12. Empty: **ROLE-04, 05, 07, 10, 11**.

**ROLE-11 is the one that matters**, because PLY-02 itself names it as one of the five
EA-gated roles ("ROLE-11's EA path") — so the gate the row calls "normative NOW" has no
card state in its own row to gate on. The other four are ordinary holes.

## 5. `station/npc/security.py` — the marked-out mechanic has no clothing input

PLY-04's entire mechanic is *"**What the player wears is the marked-out input** — SYS-05's
clothing/gait/light mechanic reads it"*. `security.hostility(place_key, hour, schema,
profile)` takes no costume, wearer or set-key argument; it is a function of place and hour
only. `costume.costume_for(...).set_key` exists and is what would be passed. This is a
wiring gap, and it is the shape this project calls instance ten.

## 6. `station/economy.py` — PLY-03's rent ladder has two of its three tiers

`room_transient` = 4–8 cr ✓ and `quarters_personnel` = 10–15 ✓ match the row exactly. The
row's third tier, "hotel/business class", has **no `LADDER` row** — and PLY-03 makes it
"one of SYS-04's three late-game sinks". SHB-04.a's four hotels are the content it would
price.

## 7. `station/npc/faction.py` — `PENDING` is stale by one

`PENDING = ("markab_quarter", "refugee_reception")`. `markab_quarter` is now a register
row (PLC-129, session 4o), so it is no longer a faction standing on unbuilt ground. Not an
SHB/PLY/GDS row's business — found while checking SHB-02.d, which `refugee_reception`
correctly still is. Flagged for whoever owns FAC.

## 8. `station/interior.py` — `cell_manifest`'s docstring is stale

It opens *"2,330 cells across 210 decks"*; the live return is **3,414 cells / 251 decks**,
which is also what PLACES.md §2's derivation paragraph quotes. The 251 recomputes exactly
from `decks_in_ring` summed over the twenty (sector, ring) pairs — that is now checked by
`shb.py`'s `manifest` claim. The 3,414 is **not** checked, because `cell_manifest()` is
**16.8 s** and `--smoke` is a sub-second tier.
