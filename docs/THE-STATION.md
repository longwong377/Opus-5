# THE STATION AT COMPLETION — the content bible

This document exists because the owner ruled it: *"I want exact specifics of all the things
we're going to do and all the features we'll have and all the things we're going to build in
detail so that the system cannot be rigged. Go through what this station needs to be at
completion and build the plan around that."* The plan derives from this file, not the other
way round. Nothing in this file is a goal statement; everything is an enumerated, checkable
item or it does not belong here.

---

## 1. THE ANTI-RIG MECHANISM — read first, because it is the reason this file works

Every previous failure mode of this project was a **proxy standing in for content**: a
density number instead of a furnace, a coverage count instead of a walk, a median instead of
a mood. The rule that ends it:

> **THE SPEC IS THE GATE INPUT.** Every item in this file and its annexes carries an ID and
> a binary acceptance check naming the *enumerated thing itself*. CI iterates the registry
> (`docs/spec/completion.yaml`, generated from this file and the three annexes — **341 rows =
> 193 places (128 PLC + 9 SHB + 20 SHB annex letters + 13 SHC + 22 INC + GDS-01) + 102
> people (52 items + 50 cast rows) + 38 systems/surface (16 SYS + 9 SUR + 13 VRB) + 8
> player (PLY)**): every item is GREEN (its named content exists and functions), CAPPED
> (owner-signed, with reason — and **CAPPED is reported as NOT-GREEN in every completion
> figure**), or RED. There is no fourth state, and **no statistic may substitute for an
> item**. Statistics (variety IoU, density floors, distinct-line counts) remain as *floors
> on top* — they catch sameness — but passing them completes nothing.

**THE MACHINERY IS THE FIRST DELIVERABLE, AND UNTIL IT RUNS AGAINST THESE DOCS, THIS
SECTION IS RED.** `tools/spec_registry.py` (parses the four docs, emits the registry,
asserts every cross-reference), `station/spec_check.py` (executes checks by harness
class, refuses GREEN for any harness it does not implement) and the `sspec_gate` step in
`validate.yml` **exist as of commit c5e82f6** — built against the pre-adoption 313-row
skeleton, before this edit set. **SPEC-CHANGE #4 (pending, adoption-blocking)** in §9 is
their re-derivation against the adopted census (VRB/GDS ID classes, 341 rows, the
registry path), and **both files are inside the adoption digest** (§9) — the code that
decides what GREEN means cannot itself be edited without a SPEC-CHANGE. A gate that has
not run against the adopted docs has not run, and until its first clean run is recorded
here, every anti-rig clause below is prose.

Three subrules that close the remaining rigging routes:

1. **The spec freezes before the build.** Changing an item after adoption requires a dated
   `SPEC-CHANGE` entry (what, why, owner-visible, **and a `recomputes:` field listing
   every downstream number the change touches** — the couplings are real: a tanker class
   moves a dialogue floor; a passage-home ruling reruns a wage table; an entry without
   its recomputes list is invalid), exactly as `INVENTIONS.md` treats canon. An agent
   cannot quietly redefine success mid-session. The frozen denominators (49,265 bays and
   every per-place target, the 79 voice cells, the 6,544-line floor, the 341-row census)
   are normative: ANY recompute divergence, in either direction, fails the gate until a
   SPEC-CHANGE shows the re-derivation.
2. **Acceptance checks name content, not counts.** Wrong: "≥5 bars exist." Right: "BAR-02
   Earhart's: the room at its full 12.3×16.0 m footprint; its named staff on shift per
   their schedules; ≥12 patron seats occupiable by NPCs and the player; stock list live
   (orders deplete it); the dartboard playable." A check like that cannot be satisfied by
   anything except Earhart's existing.
3. **Randomised human-shaped audit, rigged against its own author.** Each session that
   closes spec items ends by walking ONE item — **pool = the items closed THIS session;
   seed = the PREVIOUS session's final commit hash** (the closer cannot choose the draw)
   — rendered, screenshotted, filed as `docs/audits/<commit>-<item>.png`, whose
   **existence the gate checks**. The filing **quotes the renderer's self-reported mode
   line** — session 4e proved a silent OpenGL fallback manufactures evidence, so a frame
   without its mode line is not an artifact. **The verdict is written by the NEXT
   session's adversarial reviewer, never by the closer.** An item that passed its check
   but looks like a grey box fails the audit and reopens with a defect note. This is the
   anti-"technically present" valve.

**CAPPED, made unriggable:** a cap's signature is a **dated verbatim owner quote in §9** —
nothing else signs one. Agents may **PROPOSE-CAP** (the row stays RED, the proposal is
just text awaiting the quote). Ceiling: **≤5% of all rows (17 of 341) may ever be
CAPPED**, and **zero caps exist for SUR-02 landmark rows below craft 3** — the floor of
the owner's standard is not negotiable by anyone, including the owner's own tooling.

### 1.1 THE GRAMMAR — how a row is read (normative appendix)

1. `ACCEPT` ≡ `ACCEPT-shape` ≡ `Check` ≡ `CHECK` — one meaning, four historical spellings;
   an item without one **fails the generator** (there is no checkless row).
2. Every row carries a **`harness:`** — one of **{existing-tool** (a named file that runs
   today) **| tool-to-build ⇒ the row is RED** until the tool exists AND has run **|
   AUDIT** (a human-shaped walk filed per §1.3)**}**. Never self-certified: a harness may
   not be prose written by the session claiming the GREEN.
3. Rows without an explicit harness get one **derived by the generator from the check's
   own tool citations**; a check citing no tool derives AUDIT. The derived field lands in
   `completion.yaml`, never back into prose.
4. Tier tags `[T1]..[T4]` per §2; compound tags ("T3/T4", "stock loop T4") declare both
   tiers; a T4 satisfies a T3 slot.
5. **Multiplicity counts**: `console ×14 (T3)` is fourteen T3s; residence classes count
   once per UNIT (a 270-unit block holds 270 T3 babcom terminals).
6. **Umbrella rows green only when ALL children green** — CAST-02 needs all 50 cast rows;
   an SHB row needs its lettered annexes; the VRB set needs all thirteen.
7. **A number in a check is a floor bound to named content in the same sentence**
   (PLC-010's "≥60% of the 96 seats with named EF residents whose schedule says lunch"
   is the template; a bare count is the rig).
8. TILING reads `built → target`; the target is normative (frozen); the four
   sealed-fabric rows state gross AND net-by-SHC.
9. Link types: `within`/`adjacent` (register geometry) · `couples-to` (system) · `cites`
   (source) · pointer `SHB-nn.x` (**generator-resolved against the annex tables** — a
   pointer to a letter that does not exist fails the gate).
10. Address forms: register key + `sector/ring/deck angle° zN`; "Brown" = Grey ring 0
    outer converted-cargo margin (PLACES §1.4 ruling); **cross-doc pointers are row IDs,
    never line numbers**.
11. **Perceptual phrasings carry operational proxies**: a check stated in felt terms
    ("audible", "felt lean", "reads patience") either names an assert on state
    (class-exclusive emitter lists, acceleration sign-flip, crowd wait-state) or is
    AUDIT. Feel is judged; nothing greens on feel alone.
12. Statistics are floors on top; passing them completes nothing (§1's rule, restated
    here because it is the grammar's first axiom).

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

**Floors:** every named place carries ≥1 T4, ≥3 T3, and no interactable below T1.
**"≥1 T4" means ≥1 LISTED interactable tagged T4 with its loop named and its SYS coupling
cited in the same row** — a bare "T4 = the loop" sentence with no listed prop fails the
generator (PLC-007/008/019/056/117 each carry their listed T4 organ for exactly this
reason). The station-wide floor: ≥60% of all interactables at T2+, ≥25% at T3+ —
**computed EXCLUDING residence-unit class tags** (the 60-unit blocks' per-unit sets would
swamp any denominator), **with the denominator stored in the registry**, so the floor
cannot be moved by re-deciding what to count. (Floors, not goals — the per-item spec rows
are the goals.)

**The player's verbs at completion** (the closed set every T-tier maps onto — **one
registry row per verb, VRB-01..13 in SYSTEMS.md**): LOOK, USE, TAKE/PLACE (inventory
exists), SIT, BUY/SELL, TALK (real dialogue with choices), WORK (role shifts),
SHOW-PAPERS, FIGHT/RESTRAIN (minimal — this is not a combat game, but security must be
able to restrain YOU), PILOT, RIDE, SLEEP, EAT/DRINK.

## 2b. THE PLAYER — PLY-01..08 (the chapter that was missing)

The annexes describe a station; these eight rows put a person in it. Format per §1.1.

### PLY-01 — Arrival and processing
The player arrives aboard a named manifest ship at a real berth (SYS-02), disembarks
through the arrival concourse (PLC-005), is processed through the full 10-station customs
pipeline (PLC-003, SHOW-PAPERS inverted — the machine reads YOU), receives their
identicard state, and spends their first night in a numbered `qtr_transient` unit
(PLC-020) that stays theirs. MASTER-PLAN P2's arrival content lands here.
**CHECK:** a new game runs ship → berth → concourse → customs → (admit path playable;
refer path playable) → a numbered unit that persists across save; the arrival ship exists
in that day's berth map; the player's card renders all 9 fields.
harness: `coldstart --g1` (exists, named by MASTER-PLAN's P-table) + save-delta gate
(tool-to-build ⇒ RED).

### PLY-02 — Origin and species, ruled
**Ruling (auth 5, SPEC-CHANGE to widen): the V1 player is human, EA-origin.** The
**per-ROLE visa-gating table is normative NOW regardless**: each of the 12 ROLE rows
names the card state it requires (ROLE-01/02 EA sponsorship · ROLE-06's cert branch ·
ROLE-11's EA path · ROLE-12 EA_CITIZEN — the five a SANCTUARY-visa character cannot
hold), so the day the origin ruling widens, the gates are already content: a Narn start
is ROLE-08/03-casual first, and every locked role **says so in dialogue** ("EA sponsorship
— your visa class doesn't qualify"), never silently.
**CHECK:** the gating table exists in the registry with all 12 rows filled; a forced
SANCTUARY-visa test character is refused each of the five EA-gated roles with an in-world
refusal line, and can still stand the muster (ROLE-03) and live ROLE-08.
harness: registry table assert + scripted refusals (tool-to-build ⇒ RED).

### PLY-03 — Quarters as home
The first-night unit persists as the player's address; rent runs against it (SYS-04).
**Placed props persist** — TAKE/PLACE anywhere in the player's unit survives save/reload
as a SYS-13 delta class (`player_placements`). A **household-goods vendor** exists (a
named keeper among PLC-052's shops). The **rent-tier ladder is climbable**: transient
4–8 cr/wk → civilian 10–15 → hotel/business class, filed at PLC-032, and the top tier
plus furnishing it is one of SYS-04's three late-game sinks.
**CHECK:** buy an object, PLACE it on the unit's shelf, reload — still there; miss rent —
the arrears path fires on the player's own door (notice → SYS-05 docket); upgrade tier —
the new address admits the player and the old unit is reassigned to a real resident
within days.
harness: SYS-13 save-delta gate + scripted rent cycle (tool-to-build ⇒ RED).

### PLY-04 — Wardrobe, and being marked out
The player has a wardrobe drawn from `costume.py`'s era catalogue, bought at **the named
clothier among PLC-011's 44 stalls**. **What the player wears is the marked-out input** —
SYS-05's clothing/gait/light mechanic reads it (Downbelow reads a business coat the way
security reads a lurker's), and role garb is real: security grey twill, docker's rig, the
Nightwatch armband (a wearable with FAC-04 consequences).
**CHECK:** buy dock-hand wear at the clothier and walk Downbelow — INC-CONTACT events run
at the unmarked rate; return in business wear — the marked-out rate applies (both
measured against security.py's model); putting on the armband changes merchant greeting
bands (SYS-12).
harness: security.py contact model + costume.py (exist); the wiring tool-to-build
⇒ RED.

### PLY-05 — SLEEP and WAIT
SLEEP in any bunk/bed the player holds (their unit, a 1 cr doss bunk, a medlab bed);
WAIT on any sittable seat. Both advance the station clock at compressed rate **through
the running simulation** — events still fire, stocks still move, the world does not
pause. Interruptions are real: PA emergencies, a sweep reaching the player's camp, rent
day, a booked appointment (SYS-15) each wake the player with the cause stated.
**CHECK:** sleep at 22:00 with a 05:15 intent and wake at 05:15 — in time to make the
05:40 muster (ROLE-03); the night's incident log is non-empty and vendor stocks moved
overnight (the world ran); a scripted 03:00 sweep event wakes the player camping below.
harness: headless time-compression run (tool-to-build ⇒ RED).

### PLY-06 — Needs, ruled {none | light}
**Ruling proposed (auth 5): LIGHT.** Hunger and fatigue exist as a gentle rhythm, not a
survival game: eating and sleeping on a species-normal pattern grants small, stated
effects (dialogue warmth band, work pay stub bonus); skipping both for days costs the
same small effects and nothing else — no death spiral, no nagging HUD. This gives
EAT/DRINK and SLEEP mechanical meaning at B5's register (meals are social fabric).
**The owner signs one branch — {none} is equally signable** and reverts the verbs to
economy/flavour only. **RED until signed either way.**
**CHECK (for LIGHT):** two station-days without food or sleep produce exactly the
declared gentle set (measurably, nothing else); normal rhythm produces the bonuses; the
whole effect set is enumerated in the registry row.
harness: condition-model selftest (tool-to-build ⇒ RED) + owner signature in §9.

### PLY-07 — The journal
A diegetic journal (identicard-adjacent screen, SUR-09) auto-records **SYS-16 knowledge
items**: names given (CAST-05's name-given flag), learned tells (FAC-28's brooch), route
times (the porter's craft), open jobs and debts, appointments, incident-log entries the
player witnessed. It is the player's memory with the same honesty rules as the world's.
**CHECK:** learn Delgado's name, the brooch tell, and one porter shortcut — all three
appear as journal entries whose text names the source event; a fact NOT learned is
absent (the control); reload — the journal is intact.
harness: SYS-16 (tool-to-build ⇒ RED).

### PLY-08 — Dialogue modality, ruled
**Ruling (auth 5): alien speech renders as alien AUDIO (per-species phoneme beds over
audio.py's voice layer) under an English subtitle; human NPC dialogue is text-first over
diegetic murmur; full voice acting exists ONLY for the broadcast layers canon itself
voices — PA, ISN, MiniPax — plus Kosh's ≤12 treated lines.** Written so the 6,544-line
floor stays shippable by one agent with no cast: the floor is text, the texture is audio,
and no rule requires 6,544 recorded performances.
**CHECK:** a Narn line plays Narn phonemes under an English subtitle; the PA port call is
voiced; no human NPC line requires recorded VO to render; Kosh's lines are audio events;
DLG-06's office-designate rule holds in every subtitle (no Brakiri personal name ever
renders).
harness: audio.py + dialogue.py (exist) + subtitle-render audit (AUDIT).

## 3. THE VOLUME RULING — "build out the rest of the station," made exact

The measured hole: 128 places built one-bay-deep = 16,194 m² of distinct interior against
**5,086,374 m²** the register declares for named places alone (recomputed at adjudication;
the registry generator pins the radius convention and re-emits this number — divergence is
a SPEC-CHANGE), inside 1.977 km³ of hull. **The one-bay build is 0.32% of the declared
named-place footprint.** The completion state, in three shells:

- **SHELL A — named places at full footprint.** All 128, tiled to their declared extent
  with interior variation (not one bay repeated): `docking_bays` is 140 m of bays with
  individual berths, cargo handling, crew doors; the Zocalo is its full multi-bay run.
  **Itemised per place: PLC-001..PLC-128, PLACES §1** — 49,265 bays gross, of which
  25,549 (51.9%) sit in the four sealed-fabric rows (PLC-027/028/029/102) that build
  walkable skeletons plus stencilled closures; net fully-dressed target 23,716 bays plus
  the four skeletons.
- **SHELL B — the connective tissue, fully enterable.** Between named places on every
  populated deck: residential blocks sized to house the deck's actual residents (the
  roster names who lives where — the blocks must exist at the density the roster implies),
  mess rooms, sanitation, storage, maintenance ways, local plant rooms. Generated with
  full variation machinery, faction- and species-flavoured by the deck's mix. **Nothing a
  resident's daily path crosses may be sealed.** **Quantified per sector: SHB-01..09 plus
  20 lettered annexes, PLACES §2** — Blue 62+128 blocks · Red 2,361+706 over the
  manifest's 32 decks · Green 236 · Grey camps + partitions (no units by design) ·
  Yellow none; **capacity 250,120 vs 250,001 housed, ≈5.12 M m² gross**, every breather
  housed in Green's zone extensions (the species×role×sector matrix, PLACES §2).
- **SHELL C — the honest fabric.** Volume no resident's schedule ever enters (bulk
  tankage, dead shafts, structural voids): present as geometry, enterable where a
  maintenance role goes, sealed with *reasoned, visible* closures elsewhere (a real
  bulkhead with a stencil, not missing space). **The C-list is written down and
  owner-signed: SHC-01..SHC-13, PLACES §3 — thirteen rows with verbatim stencils, and it
  is the ONLY sealed volume on the station.**

**The build-out's physical rules (normative — the full text lives at PLACES §TILING and
binds both):** per-bay triangles ≤ `budget.py cell_tris` = 60,000; "distinct" = seeded
parametric variation generated at stream time from the committed schema, never stored
(ADR 0003 — the 4.5 GB payload does not grow with the tiling); full dressing only within
sight depth, per STATE.md §13's own specification — *"tile the bay along Z to the
location's real length, dress only the bays within sight, and state the cap loudly"*;
incremental rebuild by per-cell dependency hash; Shell B per-unit interactables
instantiate at stream time with behaviour-LOD.

## 4. THE PLACES — normative annex: `docs/spec/PLACES.md`
All 128 places (PLC-001..128) with tiling targets recomputed live — **49,265 bays gross**
(blue 7,692 / red 1,644 / green 7,052 / grey 16,487 / yellow 16,390; net-of-seals 23,716
+ four skeletons; 49,265 supersedes 73,635 via V1 `_fit_bay`, c4f989b) — plus Shell B
(SHB-01..09 + 20 lettered named annexes: Franklin's clinic, the guild hall, refugee
reception, the monastery, four station houses…), sized from the species×role×sector
ledger which sums **250,001 exactly with no cancellation**, ≈5.12 M m² gross, capacity
250,120. Shell C: 13 reasoned seals with verbatim stencils. The 22-class INC vocabulary
(mechanics in SYS-14, union asserted both ways) and GDS-01, the named-goods vocabulary.
**193 addressable rows.**

## 5–6. THE PEOPLE AND THE ROLES — normative annex: `docs/spec/PEOPLE.md`
28 factions with cited headcounts and verbatim observable frictions; the show-character
policy (institution-in / character-out, Kosh the sole instantiation); a pinned 50-row
Tier-1 named cast with homes, schedules and a woven debt/relationship graph; **12 roles**,
each seated on named data with verb-by-verb loops and the WORK-fidelity clause (every
role names its decision loop and per-shift variation); wages derived (not chosen) from
the passage-home anchor (**300–800 cr, floor 300 — SPEC-CHANGE #1**); dialogue floors as
arithmetic: **6,544 distinct lines (+ ≤32 scarce-voice ceiling)** vs 57 today.
**102 checkable rows.**

## 7–8. THE SYSTEMS AND THE SURFACE — normative annex: `docs/spec/SYSTEMS.md`
SYS-01..16 (era clock → incident generator → **civic calendar → knowledge items**),
SUR-01..09 (five-field, with SUR-06's enumerated event→sound table and SUR-03's ten-hull
union), and VRB-01..13 (one registry row per player verb) — each with state, tick,
couplings, player surface, an end-to-end named-content check, and a harness.
**38 items.**

## 9. ADOPTION AND THE SPEC-CHANGE LOG

**ADOPTED 2026-08-04.** The owner's standing instruction, verbatim (session 4i): *"all
the stated goals and more, in detail, AAA, tens of hours"* — and the commissioning ruling
at the head of this file. The bible supersedes MASTER-PLAN A5's tiling/dialogue scope
readings (A5 carries the dated supersession note; its "73,507 unnamed bays" misread
STATE §13 — those ARE the named places' footprint bays, and STATE §13 carries the
73,635→49,265 correction); P4/L4 re-derive from this file.

**Adoption digest** — the freeze covers the four documents AND the machinery that judges
them; the registry generator re-verifies these hashes every run and any drift without a
SPEC-CHANGE entry fails the gate:

| file | sha256 at adoption |
|---|---|
| docs/THE-STATION.md | pinned by the adoption commit itself (a file cannot carry its own hash; the commit object is this row's digest) |
| docs/spec/PLACES.md | `f23e89215e506e8947c599a6f1348cb1ca7d3f213b9bd6bf6db49c494d7d30b5` |
| docs/spec/PEOPLE.md | `1280f613edb5c08efbfcc6c71d71aff52aeb498b13637131af58bb7fa483c116` |
| docs/spec/SYSTEMS.md | `fd301707cc4de7e8aac4c0da2ac5cf882ea7ed9ffe0854e873e30f76654e27f6` |
| station/directory.py | `b8a74aa5d6ebed00d1a672dbb3514fe64b1cc77ba7ecdfda354fcbed58bd16ac` |
| tools/spec_registry.py | `40992ac08c0f2a26643959115214fc45a04747c6f021a9122556c740cfe96ec5` (exists, c5e82f6 — re-derivation pending, SPEC-CHANGE #4) |
| station/spec_check.py | `94cbebeb29602200376de4b34717444f6740dedf44f6122b1f6c90bd7beee503` (exists, c5e82f6 — re-derivation pending, SPEC-CHANGE #4) |

### SPEC-CHANGE LOG (master)
Entry format: dated · what · why · owner-visible · **recomputes: every downstream number
touched** (an entry without its recomputes list is invalid). Annex logs hold the
per-annex halves of the same entries; this log is the index.

- **SPEC-CHANGE #1 pending (adoption-blocking, RED) — the passage-home floor.** 300–800
  cr adopted (LAW-CRIME:748); leak = P(credits < 300); code half:
  `station/player.py:164` `PASSAGE_HOME_CR = 250.0 → 300.0` (CREDIT_SKEW self-derives to
  ln 0.06/ln 0.01 ≈ 0.6111; fix the derivation comment) + `arrival.py::_selftest`
  negative-control expectation 5% → 6%. Full entry + recomputes: SYSTEMS.md log; annex
  halves in PLACES/PEOPLE logs.
- **SPEC-CHANGE #2 pending (adoption-blocking, RED) — the core-shuttle register row.**
  `station/directory.py` core_shuttle z 1700→5722, footprint (20, 3000)→(20, 4650);
  shuttle_car z 1700→5722. Full entry + recomputes: PLACES.md log.
- **SPEC-CHANGE #3 pending (adoption-blocking, RED) — the tanker manifest class.**
  `station/traffic.py` MANIFEST: freighter_standoff 4.0→3.7 + new
  `("tanker", 0.3, "standoff", 3, 8, 12.0, 24.0)` (55.0/day preserved). Full entry +
  recomputes (DLG-04 27→30, floor 6,573→6,544, SUR-03 union): SYSTEMS.md log.
- **SPEC-CHANGE #4 pending (adoption-blocking, RED) — re-derive the registry machinery
  against the adopted docs.** The machinery exists (c5e82f6: `tools/spec_registry.py`,
  `station/spec_check.py`, validate.yml step `sspec_gate`) but was written against the
  pre-adoption 313-row skeleton. Pending code half: extend its ID grammar to **VRB and
  GDS** classes (PLY is already in its regex); parse the unbolded `harness:` field
  everywhere (the docs now write it parser-compatible); reconcile its OUT path
  (`spec/completion.yaml` in code today) with this file's `docs/spec/completion.yaml` —
  one line, either direction, stated; add the PLC↔key assert against directory.py, the
  INC 22-union both-ways assert, the SUR-03 hull-union extraction and the adoption-digest
  verification this file now specifies; then **record its first clean run against the
  341-row census here**. Until that run, §1 is RED and every "generator asserts" clause
  in the four docs is a promise.
  recomputes: the census itself (313 → 341, decomposition in §1) — the first clean run
  re-emits every frozen denominator and files any divergence as its own SPEC-CHANGE
  entry.

*(Post-adoption edits to any item land here, dated, with reason and recomputes, or the
registry gate fails.)*

## 10. FEASIBILITY — the cost arithmetic, stated before the work

**The measured rate (MASTER-PLAN:210-212, verbatim):** *"Measured rate is four landmarks
from craft 1 to craft 3 in a 70-minute agent session. 128 places at that rate is roughly
thirty sessions for one pass, and they would still be craft 3. Hand-authoring our way to
AAA surface is not reachable — not slowly, not at all."* This file is therefore costed on
the LIFE-FIRST ruling's terms: hand-craft closes only the SUR-02 eight; everything else
closes by generator, wiring, or data — the things one agent is actually good at.

**Per-annex session budgets (order-of-magnitude, declared so overrun is visible, not so
the numbers look precise):**

| annex | rows | how they close | budget (70-min sessions) |
|---|---|---|---|
| PLACES (193) | tiling + Shell B generators, utility trios, seal register — generator passes that move dozens of rows each | ~30–40 generator/wiring + ~10 for SUR-02's eight landmarks (panel loops included) |
| PEOPLE (102) | cast/role wiring on existing NPC data + the 6,544-line floor (text, per PLY-08 — no VO) | ~25–35 (dialogue is the bulk: ~15–20 sessions at 300–500 spec-grade lines/session) |
| SYSTEMS (38) | each SYS is a wiring milestone on mostly-existing models; SUR/VRB ride the same work | ~30–50 |
| PLY (8) | MASTER-PLAN P1–P2 scope | ~10–15 |
| **total** | **341** | | **~105–150 sessions ≈ 120–175 agent-hours** — tens of hours of PLAY costs hundreds of hours of build; stated so nobody discovers it in month three |

**The CAPPED strategy, declared up front:** ≤5% of rows (≤17 of 341) may end CAPPED,
owner-signed per §1, and the caps are expected to concentrate where surface is hard-capped
by having no artists (SUR-02 landmarks stuck at craft 3–4, fringe SUR-08 fidelity) —
**never on simulation-depth rows, and never below craft 3 anywhere.** A cap budget spent
early is a warning sign the gate reports.

**The gate's own runtime (smoke/full tiering — declared here because a gate that cannot
afford to run is a gate that does not run, session 4e):**

- **SMOKE — every commit, seconds, no geometry:** registry parse; every ID and pointer
  resolves (PLC↔key, SHB letters, INC union both ways, hull union, PLY/VRB presence);
  the frozen arithmetic identities re-add (ledger 250,001, block sums, capacity 250,120,
  dialogue floor 6,544, tiling 49,265, census 341); unknown-token check; harness-field
  presence; adoption-digest verification. Failure here blocks merge.
- **FULL — scheduled, serial, never concurrent with agent work** (the 4-core box kills
  concurrent heavy runs — CLAUDE.md's contention lesson): the end-to-end walks, headless
  days and renders, batched ≤20 rows a night on a rolling schedule, plus the §1.3 audit
  item; every row is full-checked at least once per milestone, and `completion.yaml`
  records each row's last-full-check commit so staleness is visible. A row whose full
  check has never run is RED regardless of its smoke status.
