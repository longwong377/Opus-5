# THE STATION AT COMPLETION — the content bible

**Status: SKELETON while the research fan-out returns. Sections marked ◐ are being filled
from the four domain inventories. Nothing in this file is a goal statement; everything is an
enumerated, checkable item or it does not belong here.**

This document exists because the owner ruled it: *"I want exact specifics of all the things
we're going to do and all the features we'll have and all the things we're going to build in
detail so that the system cannot be rigged. Go through what this station needs to be at
completion and build the plan around that."* The plan derives from this file, not the other
way round.

---

## 1. THE ANTI-RIG MECHANISM — read first, because it is the reason this file works

Every previous failure mode of this project was a **proxy standing in for content**: a
density number instead of a furnace, a coverage count instead of a walk, a median instead of
a mood. The rule that ends it:

> **THE SPEC IS THE GATE INPUT.** Every item in this file carries an ID and a binary
> acceptance check naming the *enumerated thing itself*. CI iterates the registry
> (`spec/completion.yaml`, generated from this file): every item is GREEN (its named content
> exists and functions), CAPPED (owner-signed, with reason), or RED. There is no fourth
> state, and **no statistic may substitute for an item**. Statistics (variety IoU, density
> floors, distinct-line counts) remain as *floors on top* — they catch sameness — but
> passing them completes nothing.

Three subrules that close the remaining rigging routes:

1. **The spec freezes before the build.** Changing an item after adoption requires a dated
   `SPEC-CHANGE` entry (what, why, owner-visible), exactly as `INVENTIONS.md` treats canon.
   An agent cannot quietly redefine success mid-session.
2. **Acceptance checks name content, not counts.** Wrong: "≥5 bars exist." Right: "BAR-02
   Earhart's: the room at its full 12.3×16.0 m footprint; its named staff on shift per
   their schedules; ≥12 patron seats occupiable by NPCs and the player; stock list live
   (orders deplete it); the dartboard playable." A check like that cannot be satisfied by
   anything except Earhart's existing.
3. **Randomised human-shaped audit.** Each session that closes spec items ends by walking
   ONE item chosen by hash of the commit — rendered, screenshotted, filed. An item that
   passed its check but looks like a grey box fails the audit and reopens with a defect
   note. This is the anti-"technically present" valve.

## 2. THE DEPTH STANDARD — what "deep interactability" means, per class

"Not stuff to pass a checkmark" made precise. Every object class in the station belongs to
one of these tiers, and the spec assigns the tier item by item. **Tier is part of the item's
acceptance check.**

| tier | name | the bar, exactly |
|---|---|---|
| **T1** | inspectable | look at it and it says something true and specific about itself (no two identical strings within a room class) |
| **T2** | operable | it changes its own state visibly: doors open, screens page, valves turn, lamps toggle — and NPCs operate it too |
| **T3** | transactional | using it moves something elsewhere: a till takes credits and stock drops; a terminal files a report security later acts on; a food slot debits and feeds |
| **T4** | systemic | it participates in a simulation loop that runs without the player: the till's stock is replenished by a delivery that arrived on a real ship through the real dock; breaking it creates a maintenance job somebody walks to |

**Floors:** every named place carries ≥1 T4, ≥3 T3, and no interactable below T1. The
station-wide floor: ≥60% of all interactables at T2+, ≥25% at T3+. (Floors, not goals — the
per-item spec rows are the goals.)

**The player's verbs at completion** (the closed set every T-tier maps onto): LOOK, USE,
TAKE/PLACE (inventory exists), SIT, BUY/SELL, TALK (real dialogue with choices), WORK
(role shifts), SHOW-PAPERS, FIGHT/RESTRAIN (minimal — this is not a combat game, but
security must be able to restrain YOU), PILOT, RIDE, SLEEP, EAT/DRINK.

## 3. THE VOLUME RULING — "build out the rest of the station," made exact ◐

The measured hole: 128 places built one-bay-deep = 16,194 m² of distinct interior against
1,130,026 m² the register declares for named places alone, inside 1.977 km³ of hull. The
completion state, in three shells:

- **SHELL A — named places at full footprint.** All 128, tiled to their declared extent
  with interior variation (not one bay repeated): `docking_bays` is 140 m of bays with
  individual berths, cargo handling, crew doors; the Zocalo is its full multi-bay run.
  ◐ *itemised per place from the places inventory.*
- **SHELL B — the connective tissue, fully enterable.** Between named places on every
  populated deck: residential blocks sized to house the deck's actual residents (the
  roster names who lives where — the blocks must exist at the density the roster implies),
  mess rooms, sanitation, storage, maintenance ways, local plant rooms. Generated with
  full variation machinery, faction- and species-flavoured by the deck's mix. **Nothing a
  resident's daily path crosses may be sealed.** ◐ *quantified per sector from the volume
  inventory: N blocks, M m², K residents housed.*
- **SHELL C — the honest fabric.** Volume no resident's schedule ever enters (bulk
  tankage, dead shafts, structural voids): present as geometry, enterable where a
  maintenance role goes, sealed with *reasoned, visible* closures elsewhere (a real
  bulkhead with a stencil, not missing space). The C-list is written down and owner-signed
  — it is the ONLY sealed volume on the station.

## 4. THE PLACES — normative annex: `docs/spec/PLACES.md` (1,848 lines)
All 128 places (PLC-001..128) with tiling targets recomputed live — **49,265 bays total**
(blue 7,692 / red 1,644 / green 7,052 / grey 16,487 / yellow 16,390) — plus Shell B
(SHB-01..09 + 20 lettered named annexes: Franklin's clinic, the guild hall, refugee
reception, the monastery, four station houses…), sized from the role ledger which sums
**250,001 exactly**, ~5.04 M m² gross, capacity 250,120. Shell C: 13 reasoned seals with
verbatim stencils. 188 addressable items.

## 5–6. THE PEOPLE AND THE ROLES — normative annex: `docs/spec/PEOPLE.md` (1,044 lines)
28 factions with cited headcounts and verbatim observable frictions; the show-character
policy (institution-in / character-out, Kosh the sole instantiation); a pinned 50-row
Tier-1 named cast with homes, schedules and a woven debt/relationship graph; **12 roles**,
each seated on named data with verb-by-verb loops; wages derived (not chosen) from the
passage-home anchor; dialogue floors as arithmetic: **6,573 distinct lines** vs 57 today.
102 checkable rows.

## 7–8. THE SYSTEMS AND THE SURFACE — normative annex: `docs/spec/SYSTEMS.md`
SYS-01..14 (era clock → incident generator) and SUR-01..09, each with state, tick,
couplings, player surface and an end-to-end named-content check. 23 items.

## 9. SPEC-CHANGE LOG
*(empty at adoption — post-adoption edits to any item land here, dated, with reason, or
the registry gate fails)*
