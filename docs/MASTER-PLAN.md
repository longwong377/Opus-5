# MASTER PLAN — Babylon 5, alive

**THE ORDERING RULE IS §4v — THE FINAL PLAN, immediately below. Adopted 2026-08-10.** It is the
last plan this project gets: the owner's instruction is that after it the game is *"completely
finished to perfection"*. **It is logged and NOT started.**

Everything after §4v in this file is history, kept deliberately, and read for its diagnoses rather
than for its ordering:

| section | status |
|---|---|
| **§4v — THE FINAL PLAN** | **CURRENT. The ordering authority.** Six exit conditions, phases 0–6 |
| §4r — the open defect list | **folded into §4v.** R1 → 0.1/0.1b · R4 → *already met, never marked* · R5 → Phase 1 · R7 → 2.4 and 3.5 |
| §4i — FINAL | superseded as ordering. Its **§T scope matrix**, its four anti-failure mechanisms and its "rung passes with a denominator, never an existence proof" rule all still bind, and §4v carries §T forward in full |
| §4h body, §2–§5 | superseded. The LIFE-FIRST ruling and *"a generator is finished when its output is VARIOUS, not when it is correct"* still bind |

The session-3k document is preserved as `docs/MASTER-PLAN-3k.md` because its audit is still the
best analysis in the repository. `docs/SHIP-PLAN.md` stands as the record of *why* four
contradictory plans had to be collapsed.

---

# SESSION 4v — THE FINAL PLAN. THIS SUPERSEDES §4i AS THE ORDERING RULE

**Adopted 2026-08-10. The owner's instruction: after this plan the game is "completely
finished to perfection". This is the last plan the project gets; everything after it is
execution.**

**It is logged here and NOT started.** The owner's words: *"dont start anything just log the
plan and we'll start it later"*. Nothing below has been executed. Every measurement in it was
taken on 2026-08-09/10 and carries the command that produced it.

It supersedes §4i's phase ordering. §4r's open defect list is folded in: R1 becomes 0.1/0.1b,
R4 is **already met and was never marked**, R5 is Phase 1, R7's SELL is 2.4 and its PLY-05 is
3.5. §T's scope matrix is carried forward in full, with the three items §4i left unowned now
assigned.

*Draft 3. Written against three independent audits, then **rejected twice by a blind adversarial
panel** briefed to assume the author was padding and gaming the metrics. Both reviews are folded
in below, including the places where a critic was wrong and I say so with the command.*

**Review status, stated plainly: both critics returned REJECT on draft 2.** Between them they
raised **nine blocking findings and seven major ones**. Draft 3 applies every one — including the
three that proved I had made the plan easier for myself, and one where the critic was wrong and I
refute it with the command. **It has not been put back to the panel**, so this is a plan that has
answered its review, not one that has passed it.

**How to read this.** Every claim carries the command that produced it. Where a number in
`CLAUDE.md`, `STATE.md` or `MASTER-PLAN.md` disagrees with what I measured, **the measurement is
here and the stale figure is named** — there are about a dozen such disagreements and they are the
reason Phase 0 exists. Where I got something wrong while writing this, the error is left in the document
with the correction beside it, because a plan that hides its own mistakes is the exact artefact
this project keeps producing.


## Context

The owner's instruction is that after this plan the game is **completely finished to
perfection**. This is the last plan the project gets; everything after it is execution.

Three audits ran tonight against the repository, plus seven earlier today. They converge on one
diagnosis, and it changes what this plan is:

> **The station has an extraordinary derivation layer and a thin actuation layer.** Almost every
> missing system already has its numbers computed in Python; its GDScript is absent or
> unreachable. **Much of the remaining work is wiring and reachability rather than invention.**

That is not a consolation and it is not the whole story. It means the distance to "finished" is
shorter than the defect lists suggest — **and there are four things that genuinely do not exist in
either language**, which no amount of wiring reaches:

| genuinely absent | where |
|---|---|
| **tier promotion** — the ladder can be lost, never climbed | 2.2, and it is the spine of the design |
| **the Broker** — the antagonist whose shortcut works | 3.2 |
| **the plant as a system** with load and failure | 3.3 |
| **a hue instrument**, without which the colour finding cannot be closed | 4, Batch D |

Everything else on the missing list is connection work. Those four are builds, and the plan says
so where they appear rather than letting the headline diagnosis cover them.

### What is actually built, and reachable

A player on `NEW GAME` today gets an **11-step customs arrival** with a nine-field identicard,
**3,957 people who speak** (1,513 distinct NPC lines, 662 player lines, 11 topics, 3 stances,
refusals derived from real faction friction), buying at 14 counters with a purse and a bag,
sitting, **arrest → brig cell → Ombuds → fine → tier drop → release**, and **save/continue
across 10 subsystems** with a four-panel journal of things that actually happened to them.

> **PANEL, BLOCKING — two of those were overstated and are corrected here.** Draft 2 wrote
> *"sleeping that steps the world forward hour by hour"*. `interact.gd::_sleep()`'s own docstring
> says the opposite — *"a jump is indistinguishable from having waited"* — and **PLY-05 demands
> compression *through the running simulation*, where events still fire and the world does not
> pause.** So a previously-scheduled spec item was dropped **and its absence counted as a
> delivery**. It is now item 3.5. And **save/continue's own gate is failing right now**
> (`journal.py --persist-gate`), which 0.4 records.

That is a real game. It is further along than any document in the repository says.

### What is built, tested, self-gated, and unreachable

| system | size | why a player never meets it |
|---|---|---|
| **Starfury flight + docking** | **4,101 lines** over 4 files | no menu entry; `starfury/{launch.json,starfury.glb,vectors.json}` **do not exist**; `build_world.py` has no step that makes them |
| **SELL / the fence / the Broker** | `economy.py` is 2,885 lines; the sell half is ~600 of them | **zero GDScript.** A player cannot earn or sell anything |
| **11 of 12 player roles** | — | 1 has a Python work loop; **0 have an engine loop** |
| `agenda.py` "someone goes to work" | 2,599 lines | no GDScript caller |
| `condition.py` hunger/fatigue | 441 lines | zero engine references |
| `transit_runtime.py` lifts and trams | ~1,200 lines | `scene/transit/lift.json` missing |
| the PA — 174 timed lines a day | — | **the engine plays a chime** |
| 56 ship movements a day | — | nothing visible ever moves in space |
| 90 of 93 identicard checkpoints | — | a text plate with nothing behind it |

**And the ladder — the spine of `docs/THE-GAME.md` — can be lost but never climbed.** Arrest
demotes you and it persists. **No tier promotion exists anywhere in the engine.**

### The two measures of distance, both the project's own

| gate | today |
|---|---|
| `tools/aaa_gate.py docs/aaa-scorecard.json` | **0 of 22 subsystems at the bar; 94 dimension-points below it.** Craft below 4 on **21 of 22**, fidelity on 18, robustness on 14, performance on 12. **Nothing scores 5 on any dimension anywhere.** The scorecard is **malformed in 59 places**, so the gate cannot score it honestly |
| `station/spec_check.py --smoke` | **0 GREEN / 300 RED** — 121 pass a harness declared insufficient, 177 run and fail, 2 crash. **294 of 300 rows dispatch to a harness that declares `SUFFICIENT = False`, so GREEN is unreachable by construction** — a row cannot go green even if it is perfect |

**And the second measure is worse than it reads, because failures grew while nobody was
looking.** At session 4t the ledger recorded *"224 pass-not-sufficient, 39 failed, 37 crashed"*.
Today it is **121 / 177 / 2**. The 37 crashes were fixed — and **138 rows that passed their
harness then, fail it now**. Almost all of it is the PLC family, which was 128-pass/1-fail at 4r
and is **129 RED of 129 today**. *Something moved the register out from under the spec across two
sessions and no document records it.* That is 0.2, and it is one ruling rather than 129 jobs.

---

## The exit condition

Five conditions. **Draft 2's version was rejected by the adversarial panel and it deserved to
be** — one leg was unreachable, one was satisfiable by editing a JSON file, one was blind to two
thirds of this plan's own work, and one downgraded an owner signature to a note the executing
agent writes itself. The findings and the repairs are below each leg.

1. `tools/aaa_gate.py docs/aaa-scorecard.json --strict` **exits 0**.

   > **PANEL, BLOCKING: all 94 dimension-points are cappable by 22 JSON edits.** `aaa_gate.py:503`
   > accepts `capped` on the single condition that `cap_reason` is a non-empty string
   > (`:170`). Nothing checks *which* dimension was capped, or that any rounds were spent. Fix the
   > 59 malformed entries and write 22 cap strings and **`--strict` exits 0 with Phases 1, 4 and 5
   > unexecuted.** Confirmed by reading the source.
   >
   > **REPAIR — Phase 0.0a, and it is the most load-bearing change in this plan.** `aaa_gate.py`
   > accepts a cap only when **`cap_reason` names one of R-1's five categories** *and*
   > **`rounds_used == max_rounds`**. **Craft and fidelity below 4 are never cappable** — the
   > rubric judges both from stills and citations, which this container can do.

2. `station/spec_check.py --smoke` reports **300 GREEN or CAPPED of 300**.

   > **PANEL, BLOCKING: `CAPPED` does not exist.** `grep -n capped station/spec_check.py` returns
   > three lines — the docstring, `:216` `green = red = capped = 0`, and `:283` which prints it.
   > **It is never assigned.** `completion.yaml` has no `capped` field and is generated, not
   > hand-editable. So this leg silently reduces to **300 GREEN of 300**. Verified myself.
   >
   > **REPAIR — Phase 0.0b:** build the mechanism (registry field, a `spec_check` branch, a gate
   > that refuses an empty reason), under the same category rules as 0.0a. Until it exists, this
   > condition is **300 GREEN**, and Phase 0.1 is the critical path of the entire plan.
3. `tools/build_world.py` **exits 0**, and the Windows artefact launches and survives a
   **30-minute soak** — run **on the GitHub Windows runner, not by the owner**. *An earlier draft
   said "on a clean machine", which quietly required a human that R-1 says will not be there. The
   runner is the clean machine and the only one this plan may assume.*
   **`tools/soak.py` exists and must be ported first:** it samples RSS by reading `VmRSS:` out of
   `/proc/<pid>/status`, which is Linux-only, so **it cannot run on the Windows runner as
   written.** Its docstring records a real Linux run — *274 samples, peak 6 MB, drift +0.0%* — and
   its design is right (drift, not peak, because a leak is a rising floor). The port is small and
   it is a Phase 0 item, not an assumption.
4. Every `MASTER-PLAN.md` §T scope item is green or **EXPLICITLY OUT with the owner's signature**.

   > **PANEL, BLOCKING: three §T items are in this plan's diagnosis and in no phase** — the
   > mechanism §T exists to prevent, with the receipt pre-written. **The crosswalk is therefore in
   > the plan**, all twelve rows, rather than left to exit:
   >
   > | §T scope item | phase |
   > |---|---|
   > | every POI from the show, in the right place | done · 0.2 keeps it honest |
   > | NPCs as residents — quarters, jobs, schedules | done · 3.1 gives them memory |
   > | transports + visitors arriving; **jump gate working** | **2.10 — NEW.** Nothing visible moves in space today |
   > | customs and immigration | done — the strongest thing in the build |
   > | law enforcement, crime, black market | 2.3 · 3.2 |
   > | **Downbelow's underclass** | **2.11 — NEW.** The word did not appear in draft 2 |
   > | every faction, **friction visible in a corridor** | 3.2, and its done-condition is *without the player* |
   > | physical plant for 250,000 | 3.3 |
   > | information layer — comms, ISN, propaganda, signage | 2.7 |
   > | "the simulation exists around you rather than in text" | 3.4, the absence gate |
   > | flyable Starfury, seamless launch and dock | 2.6 |
   > | era lock Season 2–3 | standing · Phase 5 |
   >
   > **Nothing on that list is now unowned.** If any of the three new items is to go OUT, the
   > owner signs it **here**, not at the end.

   > **PANEL, MAJOR: draft 2 wrote "with a written reason" and dropped the signature.** §T's own
   > clause says *"with the owner's reason"*; §A2's DONE clause says *"with the owner's
   > signature"*. §T's preamble calls itself *"the mechanism that would have stopped the Starfury
   > vanishing"* — and §T still carries **"jump gate working"**, which appears nowhere in this
   > plan. An exit condition the executor can satisfy unilaterally is not an exit condition.
   >
   > **REPAIR:** signature restored. **The jump gate is added to Phase 2 or goes OUT with that
   > signature** — it does not get to vanish twice.

5. **`docs/THE-GAME.md` §7's six gates are green — all six, no caps.** This is the design's own
   definition of the game working, and the plan's capping rules already forbid capping it, so it
   belongs in the exit condition rather than being implied by it:

| the design's gate | today |
|---|---|
| the ladder is real — five tiers reachable in one run, each rung refuses tier−1 | **red.** No promotion exists in the engine (2.2) |
| failure demotes rather than ends | **GREEN in 3 rooms of 129** — the chain closes; the table lists three places (2.3). *THE-GAME.md still records this as red, which is one more stale document* |
| the antagonists act without you | **red.** No faction-initiated event exists in any `.gd` (3.2) |
| the station remembers — day N ≠ day N+1 in derived facts | **partial.** Journal, purse, convictions and standing persist; NPC lines are baked at `stranger` (3.1) |
| shortcuts cost standing | **half.** 13 ledgers move; nothing reads them back; no Broker (3.2) |
| ≥3 roles pay — work → pay → spend closes | **red.** 1 of 12, Python-only (2.4) |

6. **The scorecard scores the game, not only the geometry.**

   > **PANEL, BLOCKING: all 22 scored subsystems are meshes.** There is no `dialogue`, no
   > `economy`, no `enforcement`, no `arrival`, no `progression`, no `incident`, no `save_load`,
   > no `audio`, no `hud`, no `transit`, no `starfury`. **So conditions 1, 3 and 4 can all be met
   > with Phases 2 and 3 entirely unbuilt** — the panel's words: *"it can terminate having built
   > nothing a player experiences."* That is the plan's real failure mode, and draft 2 did not see
   > it.
   >
   > **REPAIR — Phase 0.0c:** those eleven subsystems are added to `docs/aaa-scorecard.json` with
   > honest round-1 scores **before Phase 1 starts**. Otherwise the release gate is a geometry gate
   > wearing a game's name.

**What condition 3 still cannot tell you:** whether it ran at a playable framerate. The soak
proves it does not crash and does not leak. Per R-1 that is the ceiling, and the release notes say
so.

**An honest cap is a pass.** `AAA-STANDARD.md`'s own rule: a capped subsystem is *"not a failure
and not a retry — a decision owed to the owner"*. A plan that forbids caps cannot terminate.

### The tension in the brief, named rather than smoothed over

The owner asked for **"completely finished to perfection"** and separately ruled that the
unjudgeable dimensions are **capped** rather than measured on their hardware. Those pull against
each other and the plan does not get to pretend otherwise.

**Resolution:** *perfection* means every dimension this project **can** measure is at the bar, and
every dimension it **cannot** is capped in writing with the experiment that would close it. That
is a complete, honest artefact. What this plan will never claim is that anyone has verified the
game **runs well, animates well, sounds right, or is enjoyable** — no instrument here can see any
of those.

---

## Three rulings taken from the owner tonight

**R-1 — the unjudgeable dimensions are CAPPED.** Framerate, motion, audio mix and "how it feels"
cannot be measured here and the owner will not run passes. Each is capped in the scorecard with
its reason. **The release notes may never claim a framerate.**

**R-2 — the player walks at the derived 1.22 m/s**, not the 4.2 literal. **This makes transit a
hard prerequisite** — one lap of the blue ring is 18 minutes on foot, and `scene/transit/lift.json`
does not exist. The two land together or not at all.

**R-3 — "release" means finished to the bar**, not a distribution exercise.

---

## PHASE 0 — THE INSTRUMENTS ARE LYING, AND THEY LIE IN BOTH DIRECTIONS

*No content. This phase exists because **five** of tonight's findings were measurement errors,
two of them mine, and each would have cost a phase of work.*

**The evidence that this phase is not bureaucracy:**

- I built a phase around `interior 179 materials, budget 64 draw calls, **279.7%**`, printed on
  every export run — **and then corrected it wrongly, which the panel caught.** The 64 is
  `materials.DRAW_CALL_BUDGET["interior"]`, not `budget.BUDGETS["exterior_draw_calls"]`. Both are
  64, which is how I conflated them, and `materials.py:7062` says of its own constant
  *"EXTRAPOLATED … `budget.py` gates neither."* My "~14%" was 9/64 — **the same denominator I had
  just condemned.** Against the real per-frame budget of **1,041 draws**, the worst interior
  view's 9 materials is **0.9%**. *An inventory line that reads as a 2.8× overage and is actually
  nine parts in a thousand.*
- Then I made the opposite error with the same tool. I ran `budget.py --no-drum`, read the
  passing half, and wrote that the performance phase had evaporated. **The full run is 16 PASS
  and 8 FAIL**, including residency at **195.6%**. Draft 2 corrects it. *Both errors were mine,
  both were in the direction that made the plan easier to write, and neither needed new
  information to catch — only reading the whole output.*
- `CLAUDE.md`'s LIVE NUMBERS table is **wrong on two of its own rows**: *"171 have nothing at
  all"* (measured: **0 rows have no harness**) and *"three subsystems at craft 1"* (measured:
  **zero** — all three were re-scored to craft 3 on 2026-08-06; the same row's "thirteen at 3" is
  really **sixteen**).
  **Draft 2 said four rows and one of them was manufactured.** I listed "291 spec items" as an
  error. `CLAUDE.md:75` reads `| spec registry | **300 rows** … | "291 rows", … |`, and the third
  column's header is *"where a stale one appears below"* — **the table was flagging 291 as the
  stale figure, which is the table doing its job.** A plan whose thesis is *the instruments are
  lying* cannot afford a manufactured instrument error. The panel was right and the finding is
  withdrawn.
- **`STATE.md` is 66 commits stale** — two entire sessions with no handoff, including every
  lesson from tonight. `CLAUDE.md` names STATE.md as item 4 of its own read order.
- **R4 in the open-defect list is a solved defect that still reads as open**, and its own `note`
  warns about exactly that: *"re-score before reworking, or the rework is aimed at a stale
  number."*

**0.0a — CLOSE THE CAP LOOPHOLE IN `aaa_gate.py`. It runs first, and it is the single most
load-bearing change in this plan.** Stated above under exit condition 1, and promoted here because
an item that lives only inside a quote block is an item a future session will not pick up. Today
`aaa_gate.py:503` accepts `capped` on the sole condition that `cap_reason` is a non-empty string
(`:170`) — so **all 94 dimension-points below the bar are cappable by 22 JSON edits**, and
`--strict` exits 0 with Phases 1, 4 and 5 unexecuted.
**Done when:** a cap is accepted only if `cap_reason` names one of R-1's five categories **and**
`rounds_used == max_rounds`; **craft and fidelity below 4 are never cappable**, because the rubric
judges both from stills and citations, which this container can do.
**Control:** a scorecard with 22 free-text cap strings must make `--strict` exit non-zero.

**0.0b — BUILD `CAPPED` IN `spec_check.py`. It does not exist.** `grep -n capped
station/spec_check.py` returns three lines — the docstring, `:216` `green = red = capped = 0`, and
`:283` which prints it. **It is never assigned**, and `completion.yaml` has no `capped` field and
is generated rather than hand-edited. So exit condition 2 silently reduces to **300 GREEN of 300**
until this lands.
**Done when:** the registry carries a cap field, `spec_check` has a branch that sets it, and an
empty or non-category reason is refused under 0.0a's rules.
**Control:** a row capped with a blank reason must not count toward the 300.

**0.0c — PUT THE GAME ON THE SCORECARD. Eleven subsystems, added before Phase 1 starts.** All 22
currently scored subsystems are meshes: there is no `dialogue`, `economy`, `enforcement`,
`arrival`, `progression`, `incident`, `save_load`, `audio`, `hud`, `transit` or `starfury`. **So
exit conditions 1, 3 and 4 can all be met with Phases 2, 2A and 3 entirely unbuilt** — the release
gate would be a geometry gate wearing a game's name.
**Done when:** those eleven carry honest round-1 scores with evidence, and `aaa_gate.py` reports
33 subsystems.
**Control:** the gate must go red the moment one of the eleven is added without evidence.

**0.1 — Make the spec ledger able to report progress. This is the biggest unknown in the plan and
it is named as one.**

**Thirteen harness families exist** — one per class, `station/spec_harness/{cast,dlg,fac,gds,inc,
plc,ply,role,shb,shc,sur,sys,vrb}.py`. **Exactly one declares `SUFFICIENT = True`:** `cast`,
covering **6 rows**. The other twelve, covering **294 rows, declare `False`** — so those rows
**cannot go GREEN even if the content is perfect.** `spec_check.py:112` reads the flag directly;
there is no override.

Each `False` is a *reasoned* refusal, not an oversight, and that is what makes this expensive.
`dlg.py` refuses because the annex demands *"one evening at Milo's counter exhausts no pool"*;
`fac.py` refuses because every FAC row ends in an ACCEPT that is a **scene** — *"stand at the
muster point 05:50–06:10: the caller works the board, names gangs against that day's actual
labour"*. Raising a family to `True` means building a harness that can watch that scene happen.

**So this is not a checkbox. It is twelve harnesses, each verifying a scene, and it is the item
most likely to overrun.** It is scheduled first anyway, because until it lands **no other progress
in this plan can be reported honestly** — the ledger will read 0 GREEN whatever gets built.

**Done when:** `--dispatch` shows 0 rows reaching an insufficient harness.
**Control:** a deliberately broken station turns a named row RED.

> **PANEL, BLOCKING — and this is the finding that reframes the whole ledger.** Draft 2 presented
> *0 GREEN / 300 RED* as a reporting defect closed by 0.1. **It is not.** `spec_check.py` splits
> its own red three ways and warns at `:284` that *"CONFLATING THEM IS HOW A LEDGER LIES"*:
>
> | | rows | what it means |
> |---|---|---|
> | pass-but-insufficient | **121** | blocked by the flag. **0.1 owns these** |
> | **ran a harness and FAILED** | **177** | *"findings about the station or the spec, not gaps"* — **the station is wrong, and draft 2 gave them no owner at all** |
> | crashed | **2** | 0.8 |
>
> **0.1 could close in full and 177 rows would still be RED**, while exit condition 2 demands 300.

**0.1b — THE 177. A new item, because the panel was right that nothing owned them.** Broken down
by family with a denominator each, every one deciding *is the spec wrong, or the station?* The
PLC family (129) is 0.2. The remainder — VRB 9, SHB 9, CAST 6, INC 5, SYS 5, FAC 3, PLY 3, SUR 3,
DLG 2, ROLE 2, SHC 2, GDS 1 — resolve against the phase that builds the thing they check.

**And name the families that will be CAPPED rather than raised, now rather than at the end.**
`ply.py:16` says its flag *"is not a formality"* — a PLY row *"is not decidable without a running
game, and `--smoke` is by definition a tier with no engine in it"*. `plc.py:14` says the same for
the 129 places. **Expect PLY and PLC to cap. That is 137 of 300 rows, and it is a number the owner
should see in this document rather than discover at exit.**

**0.2 — Settle the PLC ruling. One decision for the bulk, THIRTEEN substantive residuals.**

All 129 place rows are RED and the bulk is one ruling. Draft 2 said *"127 z-only, 5 sector"* —
**which sums to 132 of 129 and was therefore impossible on its own arithmetic.** Re-classified:

**116 z-only · 12 with deck/ring/footprint disagreements alongside z · 1 (`PLC-029 fusion_core`)
with NO z disagreement at all** — which falsifies draft 2's *"every one of the 129 is RED on the
same thing"*.

> **PANEL, MAJOR: thirteen rows carry a NON-z disagreement** — 9 deck, 6 ring, 5 sector, 1
> footprint — not five. Named: `docking_bays` · `fusion_core` · `lowg_bays` · `cobra_bays` ·
> `comms_grid` · `obs_rotundas` · `research_labs` · `gravity_torus` · `zerog_maint` ·
> `micro_g_bays` · `black_market` · `core_shuttle` · `happy_daze`.
>
> **And six of them disagree on `ring_index` itself**, which is the field `AAA-STANDARD`'s
> interaction checklist relies on being correct while C-004 stays open: *"No interaction may
> assume a level number. Address by `(sector, ring_index)`."* A ring index is not a label.

`MASTER-PLAN.md` forbids editing either side to make the other pass, so each is a ruling.
**Done when:** the bulk ruling is written and applied once, and each of the thirteen is
individually decided — *is the spec wrong, or the station?*

**0.3 — Repair the scorecard, and face the eight that are nearly out of rounds.** 59 malformed
entries: findings with no descriptor, 4s with no evidence, below-bar scores with no explaining
finding, one finding whose `dimension` is not one of the four.

**And the round budget is nearly spent without anyone noticing.** `max_rounds` is 4; the round
histogram is **10 subsystems at 1 round, 4 at 2, and 8 at 3** — so eight have **one round left
before the stopping rule forces a written cap**, and **0 are capped with no `cap_reason` anywhere
in the file**:

`command_control` · `council_chamber` · `docking_bay_interior` · `exterior_approach` ·
`exterior_components` · `garden_townscape` · `generated_rooms` · `zocalo_interior`

That last round is the only one they get, so it must be spent on the dimension that is actually
below the bar rather than on a re-look. **`exterior_approach` needs one dimension (P3) and would
be the project's first subsystem ever to clear the bar** — it should be the first round spent.
**Done when:** the gate reports 0 malformed, and every one of the eight either passes or carries a
`cap_reason` naming the dimension, the score, and what would raise it.

**0.4 — Fix the six failing gates. Re-measured after the panel disputed four of them, and the
adjudication went both ways:**

| gate | state, measured | note |
|---|---|---|
| `wiring.py --selftest` | **FAIL** — 4 missing engine paths | `scene/transit/lift.json`, `starfury/{launch,starfury.glb,vectors}` |
| `column_site.py --gate` | **FAIL** — 1 of 5 columns joins nothing, **102 dead doors** | |
| `bake_columns.py --check-mesh` | **FAIL — 5 of 5 columns stale**, worst 480 m | *panel correct; draft 2 said 4 of 5* |
| `bake_station.py --shell-audit` | **FAIL — 5 of 119, worst 291.56 m** | ***panel WRONG.*** It quoted 82/119 and 292.56 m from `build_world.py:133`'s comment, which is a historical record. I re-ran the gate: **5 of 119, 291.56 m.** A comment is not a measurement — which is this plan's own thesis, aimed back at me and missing |
| `journal.py --persist-gate` | **FAIL** — *"no sidecar row for `customs_north__prop_identicard_reader`"* | ***panel correct, and it is the worse half of that finding:*** draft 2 listed save/continue under **what is actually built and reachable** while its gate was red |
| `bootstrap.py --check` | **FAIL** — `station.glb` and the LOD chain missing | |
| ~~`materials.py --check-textures`~~ | **not broken** | *panel correct.* Its own help says *"Regenerates and compares. **Minutes.**"* and commit `8f6b306` demonstrated it failing and passing. Draft 2 called a deliberately slow gate broken **because I did not wait for it** — inside the phase written to stop exactly that |

**Plus 0.8's two crashing INC harnesses.** Seven items, and the heading now counts them.

**0.5 — Port `tools/soak.py` to Windows.** It reads `VmRSS:` from `/proc/<pid>/status`. Exit
condition 3 depends on it and it cannot run where that condition has to be met.

**0.6 — Move the three instrument failures out of the craft phase.** `npc_foundation` P0,
`drum_ground` P1/R0, `tram` R0. A performance 1 *"prints PASS on a quantity it does not measure"*
and a robustness 0 *"cannot fail"* — neither is fixed by a craft round, and putting them in one is
why they have sat at 0 through four rounds.

**0.7 — Write the caps (R-1)**, and **rewrite `STATE.md` and `CLAUDE.md`'s LIVE NUMBERS from
measurement.** Every figure in this document is a candidate; none should be trusted at its age —
including the ones I measured tonight, once a session has passed.

**0.8 — The two harnesses that crash.** `INC-NEIGHBOUR` and `INC-STOCKOUT` both die with
`UnknownFaction: 'spec-inc-0-3' is not a counterparty this station can credit`. `spec_check.py`
counts them separately and correctly calls them *"a bug in the harness, not a verdict about the
row"* — **two of 300 rows are undecidable today and draft 2's gate list missed them.**

**0.9 — The `SLOW` trap, before it is sprung.** `spec_check.py:193` filters families on a `SLOW`
flag and **nothing sets it**, so `--smoke` runs all 300 rows. **The moment 0.1 writes a harness
that needs a built station and sets `SLOW = True`, exit condition 2 silently stops checking the
expensive families** — and condition 2 is written in terms of `--smoke`. State which families may
be SLOW and assert that a SLOW family still runs somewhere before release.

*(Panel findings 12 and 13. Both are small; both are the shape this project keeps producing — a
mechanism that will quietly stop measuring the thing it names.)*

---

## PHASE 1 — PERFORMANCE. IT RUNS *AFTER* 2.1, AND THE PANEL FOUND OUT WHY

> **PANEL, BLOCKING — the best finding in either review.** Phase 1's green readings hold only on
> the `ship` cull unit, and `budget.py:1744` selects that unit **only when the boot manifest names
> a cell set**. The file states the consequence itself at `:1740`: *"**WHEN THE BOOT MANIFEST NAMES
> NO CELL SET this falls back to `inst`, and the bound goes back to being 4.34× red.** The saving
> is a property of the build, so it has to disappear when the build loses it."*
>
> **And §2.1 of this plan establishes that `NEW GAME` is exactly that case** — it loads the 445 MB
> monolith and never sets `cells_path`. So **the 4.34× is not stale. It is the live figure for the
> path a first-time player takes**, and draft 2 presented Phase 1 as an independent discovery that
> deleted a phase while §2.1 sat three pages away as an unrelated item.

**So Phase 1 is re-ordered after 2.1, and 2.1's done-condition now includes re-running
`budget.py` and showing the cull unit switch from `inst` to `ship`.** Until that lands, the
readings below describe a mode most players will never select.

> **PANEL, BLOCKING — and the command I verified with was rigged.** Draft 2's verification line was
> `python3 station/budget.py --no-drum   # the real budget`. That flag suppresses exactly three
> gates — `drum visible set`, `drum share of frame`, `surface density` — and `budget.py:2312`
> prints *"the drum is the widest-open view in the project and the only gate that prices it is
> this one."* **`drum_ground` is the subsystem scoring P1/R0 that my own Phase 4 lists first,
> worst.** A flag whose effect is to hide the gates most likely to be red, annotated "the real
> budget", is the blocking definition in the severity ladder. **The `--no-drum` is removed from
> the verification block.**

With those two corrections stated, the measurement itself: `CLAUDE.md` has carried **4.34×** for
three sessions flagged "NEEDS RE-MEASURING". Re-measured tonight on the streamed unit:
**16 PASS, 8 FAIL** — and draft 1 quoted only the passing half and called the phase evaporated.

| gate | measured tonight |
|---|---|
| draw calls, whole frame | **458 / 1,041 — 44.0% PASS** |
| frustum, everything | **250,042 / 300,000 — 83.3% PASS** |
| exterior triangles / bandwidth / glb | **96.9% / 87.2% / 50.9% PASS** |
| station collision resident | **632,100 / 800,000 — 79.0% PASS** |
| occluder: doorway resolved, hides nothing visible, reaches the engine | **PASS** |
| **resident triangles** | **352,084 / 180,000 — 195.6% FAIL** |
| **plant cell** | **73,580 / 60,000 — 122.6% FAIL** |
| **bent corridor rate** | **454 / 400 tri/m — 113.6% FAIL** |
| **frustum structure** | **67,550 / 60,000 — 112.6% FAIL** |
| **structure share of frame** | **5.6% / 5.0% — 112.6% FAIL** |
| **corridor rate** | **418 / 400 tri/m — 104.5% FAIL** |
| **baked cells match the generator** | **FAIL — "manifest 907 × 0.0 deg"** |
| **stream.gd still says what this file measures** | **FAIL — 2 clauses** |

**Two things are now settled that were not:**

**The draw-call ceiling genuinely does not exist**, and the budget's own run proves it rather than
my reasoning: **458 of 1,041 whole-frame, 44%**; 67 in the frustum at 3,732 triangles a draw
against a 4,800 break-even batch. The `279.7%` printed on every export run compares a library
inventory to `exterior_draw_calls`, which `budget.py` says *"gates a manifest, not a frame"*.
**Re-label that line** — it is the phantom ceiling I built a phase on for an hour.

**Residency is the real failure and one defect explains three of the eight.** The budget models
three resident cells and measures **six of eighteen** at the worst standing position — 352,084
triangles, **95.6% over**. Beside it, `baked cells match the generator` fails with
**"manifest 907 × 0.0 deg"**, and `boot.py` prints the same thing on every launch:
*"ONE-DIMENSIONAL GRID — every cell runs 0.0 m of z, so walking along the station loads and frees
nothing."* **The cell grid is degenerate along the axis**, so residency cannot shed cells, so six
are held where three were budgeted.

**Phase 1, in dependency order. Numbered, because a bare list is not something a later session can
tick off or fail:**

**1.1 — Re-bake the cell grid with a real axial band** (INV-610). The one that matters: it is
upstream of the residency failure, the *"stream.gd still says what this file measures"* failure,
and PLAY.md's *"242 of 907 cells over the triangle budget, worst by 5.3×"*.
**Done when:** `budget.py`'s `baked cells match the generator` stops printing `907 × 0.0 deg`, and
`boot.py` stops printing ONE-DIMENSIONAL GRID on launch.

**1.2 — Re-measure residency.** **If it does not fall inside 180,000, spatial submission is Phase
1b** — per-cell instances were measured at 39% before any occluder, and the corridor occluder is
worth 7.8% because Godot culls per instance AABB while the corridor's groups span the whole 345°
ring.
**Done when:** `resident triangles` reads under 180,000 at the worst standing position, or 1b is
opened with the measured figure written down.

**1.3 — The corridor rate (+4.5%) and the bent section's end caps (+9%).** These set `structure
share of frame` at 5.6% against 5.0%, so closing them closes two gates.
**Done when:** `corridor rate`, `bent corridor rate`, `frustum structure` and `structure share of
frame` all read PASS.

**1.4 — The plant cell**, *"priced with the corridor kit as a placeholder"*.
**Done when:** it is established whether 122.6% is a pricing artefact or real geometry — and the
answer is written down **before** anything is rebuilt.

**1.5 — Re-label the draw-call inventory line.** The `279.7%` printed on every export run compares
a library inventory to `exterior_draw_calls`, which `budget.py` says *"gates a manifest, not a
frame"*.
**Done when:** the line names the manifest it actually gates and no longer reads as a frame
overage.

*The lesson is recorded rather than hidden: I ran the command, read the part that suited the plan
I wanted to write, and had to be corrected by the same command run properly. The tool did not
change between the two readings.*

---

## PHASE 2 — REACHABILITY: THE GAME THAT EXISTS, CONNECTED

*The largest phase by value. **Eight of its nine items are wiring; one is not**, and the one that
is not is the most important thing in this plan — so the phase is not "cheap", and an earlier
draft that called it that was smoothing.*

**The honest split, corrected by the panel — draft 2 called eight of nine items wiring and three
of them are not:**

| item | wiring? |
|---|---|
| 2.1 NEW GAME streams · 2.3 checkpoints · 2.6 Starfury · 2.7 the PA · 2.9 agenda/condition | **yes** — the answer is computed and the caller is missing |
| **2.4 SELL** | **NO.** `interact.gd`'s six `sell` hits are all `counter.sells` — *the counter sells to you*. There is no player-side sell verb in the eight-verb set, no fence surface, no Broker actor. **A new verb, a new counter class and a new NPC** |
| **2.5 transit** | **NO.** `transit.gd` is a top-level *mode* — `main.gd:166` dispatches `station \| arrival \| starfury \| transit` as mutually exclusive worlds. Writing `lift.json` is wiring; **handing a walking body from a streamed cell into a lift car and out onto another deck's cells is a new integration** between `walk.gd`, `stream.gd` and `transit.gd` |
| **2.2 the ladder** | **NO** — and it is promoted out to Phase 2A |

**2.1 — NEW GAME must be the streamed station.** Today `NEW GAME` builds the **monolithic**
`blue_0_0.glb` — **445 MB, one file, verified on disk** — and does not set `cells_path`; the
907-cell station is menu row 3. **The path a first-time player takes is not the path that
streams**, so PLAY.md's own *"242 of 907 cells over the triangle budget"* warning describes a mode
most players will never select.
**Done when:** one world, one path, arrival included.
**Control:** the streamed launch and the NEW GAME launch report the same cell manifest.

**2.2 — MOVED OUT. It is its own phase: PHASE 2A, below.**

> **PANEL, BLOCKING: draft 2 gave the ladder a paragraph, and the two ladders are not the same
> ladder.** `consequence.py:180` defines **six** rungs — `accredited / citizen / resident /
> transit / sanctuary / no_status` — and `THE-GAME.md` §3 defines **five** — undocumented →
> visitor visa → resident → licensed trader/deputy → docking privileges. **They share exactly one
> word.** Verified myself.
>
> Worse: `citizen` is *"ORIGIN=EARTH, VISAS empty"* — **a fact of birth** — and `accredited` is
> `card.role in {"diplomat","envoy"}`. Both carry `REVOCABLE = None`, *"this rung cannot be
> demoted"*. **So the engine's top two rungs cannot be climbed to by construction**, and draft
> 2's "all five tiers reachable in one run" was false as written.

**2.3 — 90 of 93 checkpoints get the consequence the other 3 have.** `enforcement.gd::_chain()`
already closes all seven legs — seizure, escort, booking in a numbered cell, the Ombuds sitting,
the fine, the tier drop, release — and `scene/enforcement.json` lists **three places**.
**Done when:** the checkpoint table and the enforcement table are one table.

**2.4 — SELL, and a way to earn.** `economy.py` has `bid()`, `fence_places()`, `spread()`,
`BUY_BACK`; GDScript has **zero hits for sell**. The only wage in the ledger was written by a
headless Python run.
**Done when:** work → pay → spend closes for **three roles** in the engine.

**2.5 — Transit, then the walk speed (R-2).** `transit_runtime.py` is ~1,200 lines and
`lift.json` does not exist.
**Done when:** a player boards a lift and arrives; then `player.gd`'s 4.2 literal is derived from
the same `sqrt(g)` law the NPCs use, and `walkable.py`'s `MIN_TRAVERSE_M`/`MIN_WALK_M` move with
it.

**2.6 — The Starfury reaches the build.** ~3,500 lines, a full flight model, spin-matched docking,
floating origin — and three missing files and no menu entry. It is **the top of the designed
ladder**.
**Done when:** `build_world.py` emits the bundle, a menu row exists, and launch → fly → dock runs
headlessly.

**2.7 — Give the station its voice.** 174 timed lines a day, 4 ISN bulletins, 3 Ministry notices,
8 denunciations — **the engine plays a chime.** `monitor_wall` and `tactical_display` are `read`
tokens with no text bound.
**Done when:** the PA speaks and the screens carry the day's news.

**2.8 — 119 of 120 `operate` props return *"the control moves under your hand"*.**
**Done when:** every `operate` token either does something or is honestly re-tagged.

**2.9 — Wire `agenda.py` (2,599 lines) and `condition.py` (441).** Both have zero engine callers.
*Panel: nine words for 3,040 lines, and condition has no engine surface at all — `hunger`/
`fatigue` appear in `godot/scripts/` only inside a **comment** in `save.gd`. This is not "add a
caller"; it is a HUD surface, a decay model bound to the clock, and a consumption loop against
2.4's economy.*

**2.10 — Ships arrive, and the jump gate works.** §T carries it; draft 2 did not. `traffic.py`
computes ~55 arrivals a day and **nothing visible has ever moved in space**. `vista.gd` mounts
hull, stars and sun only.
**Done when:** a ship the schedule names enters via the gate and docks, watchable from a viewpoint.

**2.11 — Downbelow's underclass.** §T carries it; the word did not appear in draft 2. The place
exists and is dressed; what is missing is the *population* the scope clause names.
**Done when:** faction presence measured in Downbelow differs from the concourse, with a
denominator.

---

## PHASE 2A — THE LADDER. THE ONE PHASE THAT IS THE GAME

*Promoted out of Phase 2 on the panel's blocking finding. `THE-GAME.md` **rejects a quest
chain**, so the ladder is the only source of direction the design permits. A player's answer to
"why am I still playing" is* **"because I am trying to stop being nobody"** *— and today that
sentence has no mechanism behind it. Four of `THE-GAME.md` §7's six gates are this phase.*

**2A.0 — THE RULING, FIRST, BECAUSE EVERYTHING BELOW DEPENDS ON IT.** Which ladder is canonical:
`consequence.TIERS`' six rungs, or `THE-GAME.md` §3's five? They share one word, and two of the
engine's rungs are facts of birth and role that cannot be climbed to. **Nothing else in this phase
can be specified until this is decided**, and it is a design decision, not a defect.

**2A.1–2A.7 — one gated sub-item per mechanism**, taken from §3's own "how you climb" column
rather than invented:

| # | mechanism | notes |
|---|---|---|
| 2A.1 | **a visa clock** — 30 days, and it expires | `resident._visa` writes the card; nothing counts down |
| 2A.2 | **a sponsorship relation** that persists between an NPC and the player | needs 3.1's memory |
| 2A.3 | **employment continuity** — "a job that lasts" | needs 2.4's roles |
| 2A.4 | **an arrest-free record window** | `player.state()["record"]` exists and persists |
| 2A.5 | **a purchasable licence** | needs 2.4's economy |
| 2A.6 | **flight hours logged** | needs 2.6's Starfury |
| 2A.7 | **an authority who signs** | an NPC with the power to promote |

**Each of 2A.1–2A.7 is an item, not a row, and each carries the same done-condition shape:** the
mechanism advances in a headless run, the advance is visible to the player, and it **persists
across a save**. A mechanism that only moves a counter in Python is 2A's own version of the
defect this project keeps producing.

**2A.8 — the surface.** A player must see what tier they hold, what it permits, and what would
raise it, **without a wiki**. `hud.gd` draws the tier name today and nothing else.

**Done when:** every rung the 2A.0 ruling keeps is reachable in one run, each refuses tier−1, and
a player who takes a shortcut can see what it cost.
**Control:** `--tier=N` already forces a tier for debugging (`enforcement.gd:1460`) — the gate must
fail when promotion is withheld but the debug flag is available, or it is testing the flag.

*There is **no writer for tier anywhere in `godot/scripts/`** — it is only ever read, forced by the
debug flag, or dropped by `_chain()`. This phase builds the writer.*

---

## PHASE 3 — DEPTH: THE FOUR THINGS THAT ARE GENUINELY MISSING

*Everything else was wiring. These four require building. Each states what is measured today, a
done-condition that is a number or a command, and **the control that must fail** — an item whose
gate cannot go red is not in this plan.*

**3.1 — NPC memory must reach the mouth.** Dialogue has a 3×3 memory axis in the derivation
(`stranger`/`acquainted`/`known`) and **every sidecar row on disk is baked at `stranger`**.
`journal.gd` tracks talks, favour, last topic and outcome per person and it survives a reload —
**and the lines never change when you come back.**
**Done when:** the same resident, met twice across a save, produces measurably different text, and
the difference traces to journal state rather than to a die.
**Control:** clearing the journal's `people` map returns the stranger greeting. If it does not,
the change was cosmetic.

**3.2 — Nothing reads standing back.** 13 standing ledgers move on dialogue stance; `grep` finds
**no consumer** outside the journal's own display panel. Nightwatch never approaches. **The Broker
does not exist** — and he is the antagonist whose shortcut *works*, which is what makes the honest
path a choice rather than the only road.
**Done when:** standing gates at least one outcome a player can hit, and taking the Broker's offer
marks the card in a way a checkpoint reads.
**Control:** freezing every ledger at 0 must change what the player can do.

**3.3 — The plant simulation.** Power, air, water, waste and rotation are **geometry plus a
staffing roster**. There is no state in which power drops and lights go out; C&C has a watch
roster and controls nothing that can break; `INC-BROWNOUT` is an event with a rate, not a system
with a load.
**Recommendation: the resource simulation** — capacity, load and a degradation curve feeding the
existing incident generator. **No rate in `incident.py` is authored**, and a scripted-failure
layer would be the first thing in this project that was.
**Done when:** a load excursion browns out a named sector, the lights in it change, C&C reads it,
and a resident's schedule responds.
**Control:** clamping the degradation curve to zero makes the brownout unreachable — and the
lights must then never change.

**3.5 — PLY-05: time compression THROUGH the running simulation.** *Panel, blocking: draft 2
listed "sleeping that steps the world forward" as built and it is the opposite.*
`interact.gd::_sleep()` says *"a jump is indistinguishable from having waited"*; `THE-STATION.md`
demands *"events still fire, stocks still move, **the world does not pause**"*. §R7 already caught
this once and wrote the rule — *"check the plan against the spec's row IDs rather than against
itself"* — and draft 2 dropped it anyway.
**Done when:** sleep 22:00 → wake 05:15, the night incident log is non-empty, and vendor stocks
have moved.

**3.4 — The absence gate, which is the test of the whole phase.** A player-absent station-day and
a player-present one must differ in derived facts, and day N must differ from day N+1.
*"The simulation exists around you rather than in text"* is the scope clause and this is its only
test.
**Control:** running the same day twice with the same seed must produce the same facts — otherwise
the gate is measuring noise and would pass on a station where nothing happens.

---

## PHASE 4 — CRAFT: 18 SUBSYSTEMS, BOUNDED BY THE ROUND CAP

*21 are below the craft bar; **three of them leave this phase** in 0.6 because their problem is a
missing instrument, not geometry.*

Ordered by cost-to-value from tonight's generator audit. **Three remediation rounds each, then
capped in writing.** That cap is the entire budget of this phase and it is fixed before it starts.

**PHASE 4 IS FULLY PARALLEL WITH 1, 2 AND 3, and draft 2's dependency claim was decorative.**

> **PANEL, MAJOR:** every Batch A–D item is an **offline generator edit** — `populace.py:1186`,
> `zocalo.bays_for(cap=6)`, `articulate(scale=1.7)`, `drum_dressing.NEAR_COVER`, a histogram tool.
> **None needs NEW GAME wired, a tier promoted, a lift boarded or a Starfury flown.** The plan
> should say so rather than dress a preference as logic.

**One genuine dependency survives, and the panel found it by catching a contradiction I wrote.**

> **PANEL, MAJOR:** Phase 1 reports *"resident set, 3 cells: 164,628 / 180,000 — 91.5% PASS"*
> against `budget.CELLS["resident_tris"] = 180_000`. Batch A then proposes an NPC library at
> **456,064** resident triangles and calls it *"the best value on the board"*. **456,064 against
> 180,000 is 2.53×.** The scorecard already records the smaller version of this collision:
> `concourse_central_corridor` composes to 127,472 against a 60,000 cell budget, *"~104k of that
> is 14 populace bodies at ~7k each"*.

**So Batch A's NPC item is gated on Phase 1 and on nothing else, and it is gated on a number
rather than on a phase:** the combined resident figure — cell geometry **plus** crowd library —
must be inside `resident_tris` before it lands. Draft 2 said "verify it", which was a note to
self rather than a gate. It is now the condition.

**Batch A — hours each, and they are the best value on the board**

- **NPCs have no face at 2 m — and it is ONE LINE.** `populace.py:1186` does `out = out[1:]`,
  deleting the 0–6 m band, so everything from 0 to 18 m is drawn at the 6–18 m body. `body.py`'s
  `FACE_FORM_MIN_SEG = 32` culls the face below segment 32 **by construction**, so "no face" is
  guaranteed rather than overlooked.
  The docstring calls the deletion *"a stated compromise rather than a derivation"* and rejects
  chain level 0 at **510,720** resident triangles. **Two things have moved since.** Level 0 is
  actually **857,472** today — so the docstring's own rejection figure was already wrong, in the
  direction that made the compromise look cheaper. And **nobody ever costed level 1**, which
  carries a face at 4,072 tri for **456,064 resident** — *below the number used to reject level 0
  in the first place*, and half the 8,000-per-agent the budget band allows.
  Full harness already exists (`body.py --silhouette`, `populace --lod-gate --legacy`).
  **Verify the 456,064 against Phase 1's closed residency figure before landing it**, because this
  is exactly the kind of number that was stale last time somebody trusted it.
- **The corridor wall's 1 m tier.** Zero triangles — it is texture, and texture VRAM is at
  **1.3% of budget**. `_fastener_field()` was written for this exact finding. Two attempts
  tonight failed and are recorded so they are not repeated: fixings moved the statistic **1.6%**,
  and nine-fold grain moved the flat fraction **not at all**. Needs a frame-space Laplacian leg on
  `measure_frame.py` — about a day.

**Batch B — days each**

- **Civilian housing.** 360 dwellings, **1 distinct shape**, a **12-triangle bed**, and floor
  joint lines costing **2.25× all the furniture in 360 homes combined**. The joint spend is one
  constant (`articulate(scale=1.7)`); the variety test is a port of `garden.lobe_shapes()`, which
  already exists with a working negative control.
- **The Zocalo's 26 bare metres.** `cap=6` in `zocalo.bays_for()`. Six bays already cost
  **2.29 M triangles**; a seventh is ~381 k. The gate already prints the shortfall. **This is a
  budget decision, not an engineering one.**

**Batch C — a week**

- **The Garden's near field.** The six-kind ground table exists and is sourced — and
  `drum_dressing.NEAR_COVER` **does not use it**, resolving three of seven items to one material.
  A trunk within 5 m is arithmetically impossible against `HEDGE_STANDARD_M = 85` and
  `CLUMP_SPACING_M = 118`, so it needs a third lattice, which lands on the 0.5 tri/m² heightfield
  ruling.

**Batch D — weeks, and blocked on a missing instrument**

- **Colour.** 98.1% of coloured pixels in one 30° hue bin. **There is no hue gate anywhere in the
  repository.** The second and third hues are already sourced from authority-1 frames — H 173–183
  against H 13 against H 207–214, **110–150° apart, all measured**. The histogram must be written
  first; then every new hue needs a sourced reading. **This is the one finding that cannot be
  short-cut.**

**Batch E — the remaining subsystems, and THREE OF THEM ARE NOT CRAFT WORK AT ALL.**

Scoring the board by dimension rather than by subsystem changes what this batch is. Per the
rubric, **performance 0 means "the quantity is not measured"**, **performance 1 means "a gate
exists and does not measure the thing it names — worse than 0, because it prints PASS"**, and
**robustness 0 means "no self-test, or a self-test that cannot fail"**. Those are missing
instruments, not ugly geometry:

| subsystem | the dimension at 0 or 1 | what it actually is |
|---|---|---|
| `npc_foundation` | **P0** | no performance gate exists at all |
| `drum_ground` | **P1, R0** | a gate that prints PASS on the wrong quantity, and a self-test that cannot fail |
| `tram` | **R0** | *"assertions that are algebraic identities and hold for `CAR_BAYS = −3.0"`* — the rubric's own named example |

**These three move to Phase 0 and Phase 5**, where instrument work belongs. Putting them in a
craft batch is how they stayed at 0 through four rounds — a craft round cannot raise a dimension
whose problem is that nothing measures it.

**What remains genuinely in Batch E**, worst first by points below the bar: `walkable_deck` (7) ·
`npc_bodies` (8, and its LOD half is Batch A) · `interior_lighting_4b` (4 — and note six rooms
are **not reachable by exposure at all**; they need darker surfaces or occluders, so this is
geometry work wearing a lighting label) · `generated_rooms` (3, and **58% of the station**) · the
landmark set · and `exterior_approach`.

> **PANEL, MAJOR: draft 2 called `exterior_approach` "one dimension short of the bar and the
> closest thing on the station to done".** **22 of the scorecard's 59 malformed entries are that
> one subsystem**, including `craft scored 4 with no evidence`, `fidelity scored 4 with no
> evidence` and `robustness scored 4 with no evidence` — twice over. `AAA-STANDARD:49`: *"A 4 with
> no evidence is a claim, and `tools/aaa_gate.py` rejects it."* **Strip the unevidenced 4s and it
> is not one dimension short; it is unscored** — and it has burned 3 of its 4 rounds.
>
> It is still the right subsystem to spend a first round on, for exactly the reason draft 2 gave.
> The sentence describing its state was wrong, and the correction changes what that round is for:
> **evidence, not polish.**

---

## PHASE 5 — FIDELITY AND ROBUSTNESS

Fidelity below the bar on 18 of 22, robustness on 14. **Four blocking conflicts**, checked entry
by entry rather than by counting the word (which gives 27 and is wrong):

| conflict | blocks |
|---|---|
| **C-003** sector arrangement | fully — which *name* attaches to a volume |
| **C-004** level numbering | fully — *"no interaction may assume a level number"* |
| **C-009** out-of-era exposure | `plant` and `corridor_service` only |
| **C-010** the bay is 140 m, the hull holds 77 m | the bay's interior geometry only |

**5.1 — Isolate C-003 and C-004 behind one register field.** Both decide **labels, not shapes**, so
the work is to make a future answer re-stampable in one place — **not** to resolve them.
**Done when:** no generator, no interaction and no gate reads a sector name or a level number
except through that field.
**Control:** re-stamping the field with the opposite reading must change every affected label and
no geometry at all.

**5.2 — C-009 and C-010, scoped.** C-009 blocks `plant` and `corridor_service` only; C-010 blocks
the bay's interior geometry only.
**Done when:** each is either resolved from canon or recorded as blocking exactly those subsystems
and nothing wider — a blocking conflict whose blast radius is unstated blocks everything by
default.

**5.3 — Break every assertion.** Robustness 4 requires **every assertion deliberately broken and
observed to fail**, with the report saying what the failure looked like. Mechanical, not creative,
and it is most of the robustness gap.
**Done when:** every subsystem below robustness 4 has a recorded negative control that fired, with
the observed failure quoted.
**Control:** an assertion that cannot be made to fail is the finding, and it is logged as one
rather than counted as passing.

**5.4 — Fidelity, 18 of 22 below the bar.** Fidelity 4 requires a citation per claim — a canon
reference or a logged `INV-` extrapolation — not a resemblance.
**Done when:** each of the 18 either reaches 4 with its citations, or carries a cap under 0.0a's
rules. **Fidelity is not cappable for effort**, only for a missing instrument, and no instrument
is missing here: the references are on disk.

---

## PHASE 6 — THE FIRST HOUR

> **PANEL, MAJOR — the single most important finding in the review:** *"What ships is a 1:1
> Babylon 5 with an outstanding customs sequence, a deep offline simulation, and **no game loop
> presented to the player**. The plan's own resolution paragraph concedes this and then adds not
> one item to change it."*
>
> Draft 2 called this section "what a stranger meets" and listed legibility, direction and sound
> as three bullets after the release pass. **That was the wrong size and the wrong place.** It is
> promoted here as a phase with the same standing as the others.

*The things a player needs that no audit measured, because no gate looks for them.*

A player today has **seven keys** — WASD, E, T, 1/2/3, J, ESC — **no map**, no objectives, no
music, no tutorial, and no designed first hour beyond the customs sequence. `hud.gd` has zero hits
for `map`; the only wayfinding on an 8,047 m station is one READ prop saying *"YOU ARE HERE —
Arrival concourse / adjacent: customs_north"*. **At R-2's 1.22 m/s, one lap of the blue ring is 18
minutes.** A map is not a nicety at that pace; it is the difference between a station and a maze.

**And the music gap is a cap standing in for a missing subsystem.** `station/generated/audio/`
holds 13 WAVs — room tone and a tannoy. `ambience.gd` has zero hits for `music`, `score` or
`theme`. **R-1 caps "audio mix" — and you cannot mix a score that does not exist.** Per the
capping rules in this plan, that makes it ineligible for a cap: either a music pass is scheduled,
or it goes **EXPLICITLY OUT with the owner's signature**.

**6.1 — Legibility.** A player must be able to find out where they are, what they hold, what tier
they are, and what would raise it. `signage.py` already generates real 3D address plates and
`address_of()`/`door_text()` exist — **the wayfinding data is built; the player-facing surface is
not**.

**6.2 — Direction without a quest chain. THE LADDER IS THE OBJECTIVE SYSTEM AND NOTHING SURFACES
IT.** The design forbids a plot campaign, so direction comes from Phase 2A plus the journal's own
facts. **2A builds the state; this builds the surface, and neither is worth anything alone.**
**Done when:** a player who has finished the arrival knows what to do next without reading a
document, and can find out at any later moment what would raise their tier.

**6.2b — A designed first hour.** There is no tutorialisation past the arrival script and no
pacing structure anywhere. **Done when:** the hour after customs is authored — not scripted
content, but a stated sequence of what the player is expected to discover and in what order,
gated by whether a headless run can reach each discovery.

**6.3 — Sound.** `audio.py` derives seven layers per place per hour with a reason for each level;
the PA has 174 timed lines; **the engine plays a chime and no music exists.** Music is capped
under R-1 for *mix*, not for *presence* — a station with no score is a decision, and it should be
a stated one.

**6.4 — The release pass.** Clean-machine launch; 30 minutes without a crash; the scope matrix
green or explicitly out; the capped list presented to the owner as the decisions they are.

---

## EFFORT AND SEQUENCE — stated, because a plan without one is a wish

Sized from tonight's generator audit, which costed each craft item directly, and from the
Python-exists/GDScript-missing split for everything else. **These are relative sizes, not dates**
— nothing in this container can calibrate a session to wall-clock.

| phase | size | why |
|---|---|---|
| **0 instruments** | **medium** | 0.1 (spec harnesses, 294 rows) is the bulk and is unknown-large; everything else is hours |
| **1 performance** | **small–medium** | one re-bake upstream of three failures, two rate fixes, one re-label. Phase 1b only if residency stays red |
| **2 reachability** | **large, and the highest value** | 2.2 is a genuine subsystem; the rest is connecting Python that already computes the answer |
| **3 depth** | **large** | four real builds — memory to the mouth, standing consumed, the plant sim, the absence gate |
| **4 craft** | **bounded by the round cap** | 21 subsystems × ≤4 rounds. Batch A is hours; Batch D is weeks and blocked on an instrument |
| **5 fidelity/robustness** | **medium, mechanical** | breaking every assertion is tedious and not hard |
| **6 stranger** | **small–medium** | mostly surfacing data that exists |

**R-2 IS THE BIGGEST FEEL CHANGE IN THE PLAN AND NOBODY CAN JUDGE IT.** *Panel, note, and it is
owed to the owner rather than buried:* slowing the player from 4.2 to 1.22 m/s is a **3.4x**
change to how the whole station reads, and R-1 caps *"how it feels to play"* as unmeasurable here.
**The plan will execute a change whose only judge has been ruled out.** That is the owner's
decision, already taken, recorded here so it is not mistaken for something the plan verified.

**The rule when a phase overruns:** it does not silently expand. The subsystem is capped in
writing with what remains, and the plan moves on — the same stopping rule that governs craft,
applied to the plan itself. *An unbounded phase is how forty other items never get built.*

---

## THE LIMITS ON CAPPING — because otherwise this plan finishes by giving up

The exit condition accepts a cap in place of the bar. **94 dimension-points sit below the bar, and
without a constraint every one of them could be capped and the plan would report itself
complete.** That is the loophole in the mechanism this plan leans on, and it is closed here rather
than discovered later.

**A cap is only legitimate under one of three conditions:**

1. **The instrument does not exist in this container** — framerate, motion, audio mix, feel. These
   are R-1's five, they are enumerated below, and **nothing may be added to that list without the
   owner.**
2. **Three remediation rounds have run and been recorded**, each with evidence, per
   `AAA-STANDARD.md`'s stopping rule. A cap before round 3 is not a cap, it is a skip.
3. **The work would violate a canon constraint or a stated budget**, named, with the number. The
   Zocalo's seventh bay is the honest example: +381 k triangles on a room already at 2.29 M.

**A cap may never be used for:** anything on the `MASTER-PLAN.md` §T scope matrix (those go green
or **EXPLICITLY OUT with the owner's reason** — a different and louder thing); anything in
`THE-GAME.md` §7's six gates, which are the design's own definition of the game working; or a
subsystem whose only problem is that the work is large.

**And the count is reported.** The release gate prints how many subsystems passed and how many
were capped, and **a build where more subsystems are capped than passed is not a finished game, it
is a written record of what was not done.** That sentence is the honest failure mode of this
plan and it belongs in the plan.

---

## WHAT GETS CAPPED, IN WRITING (R-1)

| capped | why it cannot be closed here | what would close it |
|---|---|---|
| framerate, frame time, stutter | no GPU in the container; no target hardware in the loop | the target card running the real build at 1440p with a capture harness |
| motion, animation, gait, crowd flow | every render is one frame | video capture and a person watching it |
| audio mix | numeric properties only past "not clipping, not silent" | ears |
| how it feels to play | a still cannot show that a 2 km walk is boring | a human at the controls |
| whether an alien reads as alien | no numeric proxy exists | a human, and a decision about the target |

---

## ENFORCEMENT — how this plan cannot quietly fail

1. **It amends `docs/MASTER-PLAN.md` as a dated section.** `CLAUDE.md` forbids a fifth plan
   document and `tools/doc_chain.py` asserts placement in CI.
2. **A gate is not adopted until it is a step in CI**, using the per-step-outcome pattern.
3. **The scope traceability matrix is itself a gate.**
4. **Every session lands something a player can see or do.**
5. **No statistic substitutes for a spec item.**
6. **New:** every session ends with `STATE.md` updated. Tonight's audit found it **66 commits
   stale**, which is how R4 stayed open after it was solved and how four LIVE NUMBERS rows went
   wrong. *The repository is the only memory that survives a context reset, and it failed.*

---

## WHAT THE GAME IS WHEN THIS IS DONE — and where it still will not match Starfield

The owner's bar is *"Starfield level in look and depth and feel"*. Taking that seriously means
saying where this lands and where it does not, rather than asserting it clears.

**What a stranger gets, if every item above completes:**

They arrive on a transport as a named person with a nine-field identicard, go through a
ten-station customs hall, and are turned loose on an **8,047 m station at 1:1 with 3,904 residents
who have homes, jobs, shifts and species-specific sleep**. They can talk to any of them — real
branching conversation on eleven topics, three stances, refusals that come from faction friction
rather than a flag — and the people they have met remember them. They can work a shift, get paid,
buy a drink at a bar whose till and shelf actually move, and be arrested, tried, fined and
demoted for carrying the wrong thing. They can climb from undocumented to docking privileges and
fly a Starfury out of a cobra bay and back into it. The station runs whether they are there or
not, and the day they come back is not the day they left.

**Where it beats Starfield:** the simulation underneath. Nothing here is a set dressed for the
player — the crowd density comes from an occupancy model, the dialogue quotes numbers the station
actually computed, the incident rates are derived rather than authored, and the whole thing is
one 8 km object at true scale rather than a set of cells behind loading screens.

**Where it will not match it, and these are the honest three:**

1. **Hand-authored art.** Starfield's interiors are dressed by people, prop by prop. This is
   generated, and the plan's craft ceiling is *"holds at every distance and the detail is
   functional"* — rubric 4, not 5. **The plan does not claim 5 anywhere**, and nothing in the
   project has ever scored one.
2. **Motion and animation.** No instrument here can see a gait, a crowd flow or a door timing.
   Capped under R-1. This is the gap a player would feel first.
3. **Faces and performance.** Bodies get a face at 2 m; they do not get acting, lip sync, or a
   voice. There is no recorded dialogue and the plan does not add any.

**The blunt version:** at the end of this plan it is a **deep, honest, living simulation with
generated art at rubric 4 and no performances in it** — closer to Dwarf Fortress rendered in 3D
than to Starfield, and better than Starfield at the thing Starfield is worst at. If the owner's
bar is specifically *visual* parity with a hand-authored AAA title, **this plan does not reach it
and no plan bounded by generation would** — that is worth knowing now rather than at the end.

---

## VERIFICATION — run, not asserted

> **PANEL, MINOR: "a plan whose first phase is *the instruments are lying* did not run its own
> verification block."** Fair. Run now; output pasted verbatim so the starting line is on the
> record and the first execution session can diff against it.

```bash
python3 tools/aaa_gate.py docs/aaa-scorecard.json --strict   # the release gate
python3 station/spec_check.py --smoke                        # 300 rows
python3 tools/wiring.py --selftest                           # nothing orphaned
python3 station/budget.py                                    # ALL of it -- no --no-drum
python3 tools/build_world.py                                 # the world + every gate
```

**The starting line, measured while writing this:**

```
spec_check --smoke      0 GREEN / 300 RED / 0 CAPPED of 300
                        121 pass-but-insufficient · 177 ran and FAILED · 2 CRASHED
aaa_gate                SCORECARD IS MALFORMED -- 59 problem(s); 0 of 22 at the bar
wiring --selftest       exit 1 -- 4 missing: scene/transit/lift.json,
                        starfury/{launch.json,starfury.glb,vectors.json}
budget --no-drum        16 PASS / 8 FAIL; worst = resident triangles 352,084 / 180,000
```

**Every one of those four commands fails today.** That is the honest starting position, and any
future session that finds a different one should suspect the tree moved rather than the plan.


---

# SESSION 4r — THE OPEN DEFECT LIST, WITH A GATE AND AN ACCEPTANCE TEST EACH

**This section adds to §4i-FINAL; it supersedes nothing.** It exists because five
defects were found in one session and a session's task list dies with the session.
`STATE.md` narrates them; this is where the *work* is committed to, in the form
§4i's enforcement demands: **an owner, a gate that can fail, and an acceptance test
that names content.** Ordered by how much they cost if left.

## R1. THE SPEC HARNESS — 300 rows, 0 reachable checks. **The denominator problem.**

`docs/spec/completion.yaml` is 300 enumerated, checkable items and `CLAUDE.md` §1 calls
it *the content authority*. `station/spec_check.py --smoke` reports **0 GREEN / 300 RED**
— and the reason is not that 298 things are unbuilt. It is that until 4r **no row could
reach a harness at all**: `HARNESSES` was keyed on the row's free-text `harness:` field
with two entries, and **zero of the 300 rows carried either key**. Instance eleven of this
project's signature defect, inside the file whose header calls the project *"a museum of
gates that were prose"*.

Fixed in 4r to dispatch on the row's ID prefix, and `--dispatch` now names any harness
that reaches nothing. The reachable check was also vacuous — it resolved `PLC-nnn` to
`PLACES[nnn-1]` and never read the key the spec names — and now matches on identity with
three failure branches shown firing.

**Still 0 GREEN, correctly**: address-agreement is explicitly not sufficient. 129 rows now
have a verified address; **171 have nothing checking them at all.**

| | |
|---|---|
| **why it is first** | every other progress number in this project is a proxy. Without this, "how far are we" is answered by whichever gate someone happens to run — which is how a station 12.5% too large and a dead notice-loop coexisted |
| **gate** | `station/spec_check.py --smoke`, CI `sspec_gate` |
| **acceptance** | a content harness for each of the four largest row families (PLC, SYS, INC, PLY), so a GREEN count means "these named things exist and were checked", not "somebody ran something" |
| **honesty rule** | GREEN moves ONLY by implementing a harness and building what it checks. Never by re-reading a row |

**PROGRESS, 4r.** The dispatch bug is fixed and the architecture is in:
`station/spec_harness/`, **one module per family**, dispatched by ID prefix, contract
`check(row) -> (ok, note)` plus `SUFFICIENT: bool`. One module per family is not tidiness — 300
rows in 13 families ask 13 different questions, and one shared file guarantees several agents
editing it at once, which in this repository has produced stomped artefacts, half-written imports
and a swept commit.

`plc.py` is the worked example and it is a real check: every PLC row opens with an address line
the spec authored independently of the register (`blue/0/0 0° z7115 · 360°×140 m ·
docking_bay/generic* · auth 3`), which is **nine checkable facts**. The harness it replaced
compared none of them. **128 pass, 1 FAIL — `PLC-098 mainstage_node: z spec=3000 register=3250`**,
which is the move made hours earlier the same session. The register is the authority; the spec now
follows, with the reasoning quoted in `PLACES.md`.

Two mistakes worth carrying: the first regex reported **79 of 129 rows as MALFORMED** because `-`
is a real value in the module slot and the commonest one — *"I cannot parse this" and "this
disagrees" are opposite findings and only one is about the station*, so count the shapes rather
than loosen the pattern. And `--dispatch` exists precisely so an entry that reaches nothing is
visible on demand; it now prints none.

**ALL 300 ROWS NOW REACH A HARNESS.** Six family groups written in parallel, each with an
adversary whose only job was to prove the harness vacuous. **None was.**

```
0 GREEN / 300 RED / 0 CAPPED of 300
  236 passed their harness but it is not sufficient for GREEN on its own
   64 RAN a harness and FAILED it -- findings about the station or the spec, not gaps
    0 have no harness at all
```

**Still 0 GREEN, and that is correct**: every family set `SUFFICIENT = False`, the honest answer
while the checks verify addresses, citations and arithmetic rather than built content. **What
changed is that the number is now earned.** Before, 0 GREEN and "every harness is perfect" were
indistinguishable outputs.

**The 64 failures are the deliverable.** A sample, each with both numbers:

- **INC-CONTRA** — a declared write that *cannot happen*: `response_s` is 0.0 at both customs
  halls at all 48 half-hours against a 300 s window, so the `_stock(w, "black_market", …)` write
  at `incident.py:2308` is **unreachable**.
- **FAC-04** — spec states 1,675–3,175 armbanded officers plus informers; `faction.head_count`
  gives **872**.
- **SHC** — **0 of 12 quoted stencil strings exist as a literal anywhere** in `station/`,
  `godot/` or `tools/`, against §3's whole-shell CHECK that every stencil is rendered.
- **PLACES.md §4 TOTALS** — disagrees with **its own belts** twice (Blue shell B: 265,800 m²
  stated, 266,100 m² summed), and counts 128 places where the register has 129 (`markab_quarter`).
- **GDS-01** — `economy.GOODS` holds **34** named goods against a floor of ≥60. 26 short.
- **SYS-04, ROLE-04** — code citations that have gone stale: `CREDIT_MIN/MAX` cited at
  `player.py:140-174`, actually at 192–193; `serve_response` cited at `dialogue.py:1314`,
  actually 1704.
- **SYS-14** — the annex contradicts **itself eight lines apart**: "the 22-class union" and "the
  30-row union above".

**And the adversaries found three bugs in `spec_check.py` itself**, two while reviewing other
files: `--smoke` was declared and never read (CI had always run the full tier); a raising harness
took the whole ledger down with no output at all; and the summary line had aged into a false
statement the moment thirteen families had harnesses. All three fixed, the crash guard shown
firing and restored.

**NEXT for R1:** the 64 are a work-list, and each needs deciding — *is the spec wrong or the
station?* Neither may be edited to make the other pass. Then raise `SUFFICIENT` per family as
content harnesses land, which is the only path to a GREEN that means anything.

## R2. ~~W5 IS RED~~ — **CLOSED IN 4r: 20 of the room look up, 0 deg off**

`walkable.py --deck blue/0/0` → *"reached docking_bays and NOBODY noticed — 0.0 deg turned"*.
W5 is **the loop** — spawn → walk → use something → an NPC reacts — and `CLAUDE.md`'s own row
still quotes its passing form (*"7 of the room look up"*).

**Diagnosed and confirmed in 4r.** `populace.ROOM_INSTANCED = True` (4p) moved room occupants
into `MultiMesh` buckets; `npc.gd::collect()` builds its `Person` records **by matching actor
group names against `MeshInstance3D` names**, so an instanced occupant has no parts, no
`Person`, and nothing to turn. A/B: `ROOM_INSTANCED = False` gets **past** the notice
assertion and fails later on a different defect.

| | |
|---|---|
| **do NOT** | revert `ROOM_INSTANCED`. The instancing is the right trade and the corridor already made it |
| **fix** | `MultiMesh.set_instance_transform`; `add_crowd` already knows which instance index belongs to which placement. The notice loop writes into the bucket instead of a node's `global_transform` |
| **bonus** | it makes the **corridor walkers** able to notice you, which they never have been |
| **gate** | CI `swalkloop`, added 4r, red today |
| **acceptance** | `noticed >= 1` with `facing_err_deg` inside tolerance, on the instanced path |
| **RESULT** | `PASS deck blue/0/0 -- a body spawns in the corridor and WALKS INTO docking_bays (48.8 m -> 0.36 m), never leaving the floor, through a door that opened to 1.00, **20 of the room look up (29 deg turned, 0 deg off)**` |
| **what it took** | `Walker.notice_yaw` applied in `_walker_xform` **before** `right` is derived from `fwd`, so the basis cannot lose its handedness; `_notice_walkers()` mirroring the `_people` loop's `notice_m`, `turn_rate` and shortest-way-round rule; and **`noticed_count`, `turned_deg` and `facing_error_deg` all reading BOTH crowds** |
| **the second half was the interesting one** | after the turn worked, the gate went from `NOBODY noticed` to `20 noticed but the nearest is -1 deg off -- the yaw convention is wrong`, because `facing_error_deg` still read `_people` alone and -1 is its "nobody in range" sentinel. **The same defect, one function over.** A fix applied to the turn and not to the three functions that report on it would have looked like a regression |
| **still open, pre-existing** | `vorlon_berth: the body never reached a floor` -- the 0.00 m doorway clearance 4k identified, unrelated to noticing |

## R3. ~~21 OF 84 CAN SPEAK~~ — **CLOSED IN 4r, AND THE DIAGNOSIS WAS WRONG**

The shipped build printed `dialogue: 21 people can speak, of 84 in the cast`, and this entry
originally read *"the cast grew and the dialogue did not"*. **That was wrong, and the way it
was wrong is the lesson.** `dialogue.sidecar()` emits a row for every actor carrying a
`who.id`, and all 84 carry one — including the "silent" ones, who turn out to be fully formed
residents with names, roles and jobs (*Anna Rossi, dockworker, lowg_bays*). The baked
`blue_0_0_dialogue.json` was written **2026-08-04** against an actors file dated **2026-08-05**.

Re-baked: **336 rows, 84 of 84**. Nobody was ever mute. The artefact was old.

**Third staleness defect in one family**, after `bootstrap._boot_has` (a `boot.json` that parses
and lacks the keys the gates read) and `bootstrap._sidecars_carry` (interact sidecars predating
four verb fields). *An absence in an artefact is not an absence in the content, and this project
has now mistaken one for the other three times in three files.*

| | |
|---|---|
| **fixed** | all four decks re-baked: 84/84, 84/84, 84/84, 73/73 |
| **gate** | `python3 station/dialogue.py --coverage`, CI `sdialoguecoverage`, in the roll-up |
| **why two checks** | coverage alone passes on a stale pair that happen to agree; freshness alone passes on a current file covering half the deck. **Neither can see the other's failure**, so it asserts both |
| **controls** | both shown firing — a sidecar older than its actors file, and a cast member with every row removed |
| **the bar** | **100%, and reachable rather than aspirational** — every deck on disk meets it today. A resident you can walk up to with nothing to say is one the scope document forbids |

## R4. THREE SUBSYSTEMS AT CRAFT 1 — including Command & Control

`docs/aaa-scorecard.json`, 22 subsystems scored in engine frames: one at craft 4, thirteen at
3, five at 2, and **three at 1 — `command_control`, `council_chamber`, `docking_bay_interior`**.
C&C is *"the most-seen room in the show"* by the register's own note.

| | |
|---|---|
| **gate** | the AAA rubric at the **half distance**, per `docs/AAA-STANDARD.md` — a wide shot is not evidence about craft |
| **acceptance** | craft 3 or better at half distance, scored by a round in the scorecard with the frame committed beside it |
| **stopping rule** | `AAA-STANDARD.md`'s three rounds, then CAPPED in writing. This is not open-ended |
| **note** | `command_control` shows one scored round while work has landed on it since; re-score before reworking, or the rework is aimed at a stale number |

## R5. THE STREAMED BUILD REACHES ONE z-CLUSTER

`cells_blue_0_0` is 18 cells spanning **12.9 m of z** of an 8,047 m station; 8 of 129 places
overlap it and **121 are unreachable from the spawn**. `--vista-gate` reports the concrete
consequence: the nearest window is **838 m along the axis**, so the vista mount landed in 4r
is correct and cannot fire.

**Two causes, and they must not be conflated.** *(a)* `cell_manifest.json`'s deck table lists
**251 decks** and this container has **one** baked — a recycled-container artefact, now
reported as `PARTIAL 1 of 251` by `tools/bootstrap.py` instead of `present`. *(b)*
cluster-to-cluster hand-off is genuinely untested, which `MASTER-PLAN` P0.5 already records.

| | |
|---|---|
| **gate** | `tools/bootstrap.py --check` for (a); a new walk gate for (b) |
| **acceptance** | a body walks from the spawn cluster into an adjacent one and back, with cells loading and freeing, and arrives at a place in the far cluster |
| **open question** | the intended denominator — 251 decks in the manifest against 70 recorded as baked. **Nothing in the repository states which**, which is why `bootstrap.py` prints the fraction and deliberately does NOT fail on it |

## R7. FOUR THINGS THE SPEC ENUMERATES AND NO PHASE SCHEDULES

**Found by testing this plan against a list rather than reading it.** The owner asked whether
the plan accounts for what stops the build being a game. Most of it does, and better than I had
implied: **P2 — THE PLAYER PERSISTS** owns save/load and its gate is well shaped (*"buy
something, quit, reload, stock still down — fails today, keeps failing until G1's economy seed
lands, which is the point"*), and **P3** owns eat/sleep (L2), transit (L3), dialogue (L4) and the
economy and till (L7).

**Four are in the spec and in NO phase.** Counted, not felt — occurrences in the annexes against
occurrences in this document:

| item | spec | this plan | row |
|---|---|---|---|
| journal / knowledge items | 10 | **0** | PLY-07, SYS-16 |
| condition model (hunger, rest as *state*) | 4 | **0** | PLY-06 |
| time compression through the running sim | — | **0** | PLY-05 |
| SELL as a verb distinct from BUY | 21 | **0** | VRB-05 |

**THIS IS THE GAP BETWEEN THE TWO AUTHORITIES, AND IT IS STRUCTURAL.** `CLAUDE.md` §1–2 make the
spec decide **what** and this plan decide **what order**. An item in one and not the other has no
phase, so no session picks it up — it is enumerated, checkable, red in the ledger for ever, and
scheduled by nobody. That is a quieter failure than an unbuilt thing, because the ledger keeps
reporting it and the plan keeps not containing it.

| | |
|---|---|
| **gate** | `station/spec_check.py --red` already reports all four. What was missing is a phase that owns them |
| **acceptance** | each lands inside P2 or P3 with the phase's own denominator: SELL in P3-L7 beside the till, condition + journal + time compression in P2 beside save, since all three are player STATE and share its persistence question |
| **why P2 and not later** | a condition model with no save is a hunger bar that resets, and a journal with no save is a notebook that forgets. They are the same problem as persistence and should be built where it is |
| **the rule** | when this plan is amended, check it against the spec's row IDs rather than against itself. Four items hid for however long because nobody asked the plan a question it could fail |

**AND THE POSITIONAL ANSWER MATTERS MORE THAN THE COVERAGE ONE.** P2 and P3 **have not started**.
The phase order is P0a → P0.5 → P0.6 → P0.7 → P1 → **P2** → **P3** → P4 → P5, and session 4r
worked in P0.5 (streaming hand-off), P1 and P4 (craft) simultaneously. That is the drift §4i was
written to stop, and it is worth naming here rather than only in a retrospective: the phase that
makes the player persist is two phases out, and nothing will make it closer except doing it.

### R7 UPDATE, same session — P2 HAS STARTED, at its keystone

**The save system exists**: `godot/scripts/save.gd`, gate `python3 station/coldstart.py --g8`,
CI step `ssave`. Written the same session this section was, because the section's own argument
made it the next thing to build: *"a condition model with no save is a hunger bar that resets,
and a journal with no save is a notebook that forgets."* Both of those, and SELL's till, and
time compression, are worth strictly less than they look until this exists — so it went first.

Measured, subject and control: position back **0.000 m** after a 12.01 m walk away, clock back
**0.00000 h** after +5.0028 h, purse back **0.00 CR** after spending 137.00, bag **+0** after an
item. The `--no-restore` control fails on all four.

**The number to carry forward is not "4 of 9 subsystems save", it is "4 of 4 savable, 5 exempt
with written reasons, 0 silent."** `save.gd::audit` has four buckets rather than two, and the
third is the one that makes P2's remaining work legible: a subsystem with nothing to save
declares `save_exempt()` with a **non-empty reason**, so a permanent "missing" list cannot
accumulate around the genuine gaps. What is genuinely outstanding is now one item rather than
five — **a stable id for a crowd body across a reload** — and it is what blocks resuming a
conversation, keeping a body on the deck, and remembering which line was said to whom.

**P2's remaining items are unchanged and now have somewhere to persist to**: the condition model
(PLY-06), the journal (PLY-07, SYS-16) and time compression (PLY-05). Each is a `save_state` on
a subsystem that does not exist yet, which is a much smaller statement than it was this morning.

## R6. THE RULE THAT PRODUCED FOUR OF THESE FIVE

R1, R2 and R5 are all one shape: **a thing was built, a consumer read a different
representation, and no gate compared them.** R3 is its sibling — a ratio nobody gated.
`tools/wiring.py` catches the static form; none of these were static. The transferable rule
is in `CLAUDE.md` and is repeated here because this section is where the work is chosen:

> A static scan can tell you a caller exists; only running the thing tells you the caller runs.

**Every acceptance test above runs the thing.**

# SESSION 4i — FINAL. THE ORDERING RULE, SUPERSEDING §2–§5 BELOW

**Adopted direction: the owner directed "all the stated goals of this project and more,
completed in detail and in AAA execution — a fully functional living 1:1 simulation you can
lose tens and tens of hours in." This document is that instruction turned into phases, gates
and enforcement.** It survived two adversarial rounds: a three-critic panel + synthesis judge
(28 confirmed findings, 3 rejected — the 4i draft was not adopted), then a final pass against
the tens-of-hours / AAA / all-goals test, which found ten more (F1–F10 below, folded in).

## WHY THIS PLAN CANNOT QUIETLY FAIL — the enforcement, before the content

Plans here have failed four ways: they could not take effect (a document nothing pointed at);
their gates could not fail; their scope evaporated item by item; and progress was reported as
counts. One mechanism against each, all four in force from adoption:

1. **`CLAUDE.md` points here first.** A plan it does not name is not the plan.
2. **A gate is not adopted until it is a step in `validate.yml`**, using the
   per-step-outcome pattern so one red gate cannot blind the rest.
3. **The scope traceability matrix (§T) is itself a gate.** Every 3c scope item maps to a
   phase and a gate, or sits on EXPLICITLY OUT with the owner's reason. An item in neither
   place fails CI. This is the mechanism that would have stopped the Starfury vanishing.
4. **A rung passes with a denominator, never an existence proof** — "N of the deck's
   residents", never "it happened once". And **every session lands something a player can
   see or do**, even in infrastructure phases: the owner's own history says pure-gate
   sessions read as nothing happening, because they are.

## T. SCOPE TRACEABILITY — the 3c binding list, item by item

| 3c scope item | phase | gate |
|---|---|---|
| every POI from the show, in the right place | done | `directory.py` 128/128 · `routes.py` 46/46 adjacency |
| NPCs as *residents* — quarters, jobs, schedules | P3-L2/L3 | denominator gates below |
| transports + visitors arriving continuously; **jump gate working** | P3-L9 + P4 | a ship the schedule names enters via the gate and docks, watchable from a viewpoint |
| customs and immigration | P2 arrival | `coldstart --g1` + the customs incident class |
| law enforcement, crime, black market | P1-G3 + P3-L8 | incident generator gates |
| Downbelow's underclass | P3-L6 | faction presence gate, measured in Downbelow |
| every faction, friction **visible in a corridor** | P3-L6 | two factions' members pass; a measurable interaction occurs without the player |
| physical plant for 250,000 | done as places | its *function* surfaces via L9 + one plant incident class |
| information layer — comms, ISN, propaganda, signage | P3-L9 | "the week has news" gate |
| "the simulation exists around you rather than in text" | P1+P3 | the absence gate: player-absent vs player-present days differ |
| flyable Starfury, seamless launch and dock | P4 | launch → fly → dock, headless, plus one piloted playtest |
| era lock Season 2–3 | standing | `costume.ERA_EVENTS` guards; C-009 contamination noted |

## A0. GROUND TRUTH — corrected; every row carries its command

(unchanged from the adjudicated table — dialogue **2,139-line module, 57 distinct lines,
38/73 close on one string, zero player utterances, 1 of 71 decks**; payload **4.5 GB**;
bodies **2,504 of 250,000**; ~~`boot.py` emits one `.glb`, `main.gd` never sets `cells_path`
— the shipped scene loads ONE DECK and never streams; streaming cells exist for 1 z-cluster of
~96~~ **ALL THREE OF THOSE ARE FALSE AS OF 4k**: the shipped scene STREAMS (`godot --headless
--path godot` → *"main: STREAMED — 18 cells, starting in cell 13"*, 3 resident, neighbours at
+17.8 m and +56.1 m of lead, boot 8.9 s → 3.7 s, gate `python3 station/boot.py --gate` 10/10,
CI step `sthe_shipped_scene_streams`); cells exist for **70 decks / 955 cells / 1.7 GB**, not
one z-cluster; and the deeper half was that **`walk.gd` only called `_stream.update()` inside
`--stream-test`**, so even with a path the build primed one cell and never loaded a second;
**zero `Navigation*` in godot/**; **no day index**; crowd
non-colliding by design; ~~L3 disputed 0.05 m vs 5.59 m~~ **L3 SETTLED 4j: 0.05 m, green at
x1/x10/x60 with all three controls firing — `python3 station/agenda.py --commute`**;
performance never measured on a GPU;
`variety.py` red at 18 clusters / 45 of 128; craft: corridor 4, Zocalo 3, generated rooms 1,
garden 1; **0 C#** against an ADR that says C#.)

## A1. WHAT "AAA EXECUTION" MEANS HERE, PER DIMENSION — so it can be gated, not wished

`AAA-STANDARD.md` is the bar and its **hard stop** (3 remediation rounds, then CAPPED with a
written reason) is finally exercised rather than admired. Per dimension:

- **Craft** — everything the player sees closest is ≥4 at the rubric's half distance: all
  5 kits (corridor, lift, tram car, doorway, drum ground), plus the landmark set (Zocalo,
  customs, garden vista, C&C, a bar interior) driven to 4 by the panel loop. Generated rooms
  reach "unidentifiable as generic" (V-track), not hand-crafted beauty. **Anything capped is
  listed with its reason — an honest cap is AAA practice; a silent 1 is not.**
- **Fidelity** — canon gates stay green; every extrapolation logged; the two blocking
  conflicts (C-003, C-004) isolated behind single register fields so a future answer
  re-stamps them in one place.
- **Performance** — measured on target hardware (P0h), with the three-outcome branch
  pre-written (§A4). Until then: CPU frame time + soak in CI, labelled as the half it is.
- **Robustness** — the negative-control discipline, the soak, streaming-failure policy,
  save/load delta gates. Nothing ships that cannot fail visibly.

## A2. THE TARGET, QUANTIFIED — "tens and tens of hours" needs an engine, not a wish

**DONE = a stranger downloads one file, runs it at 60 fps, arrives at Babylon 5 as a person
with papers, is drawn into events that would have happened without them, changes how they
end, finds the station different when they return — and every 3c item in §T is green or
EXPLICITLY OUT with the owner's signature.**

The hours come from four sources, each with a measurable proxy (headless, in CI):

| source | mechanism | proxy gate |
|---|---|---|
| **the place** | 128 places, viewpoints, the drum, the exterior | route coverage: every place reachable and lit; ≥10 places with a view out (today 6) |
| **the day** | 250,000-person schedule field, 52 ship movements/day, era clock | the **absence gate** (player-absent day ≠ player-present day) and the **second-day gate** (day N ≠ day N+1 in derived facts, not scripts) |
| **the role** | the player IS someone: jobs, shifts, pay | ≥3 playable roles with complete loops (work → pay → spend) |
| **the stakes** | incidents + progression + consequence | generator rate ≥2 meaningful incidents/station-hour near the player; 5 access tiers all reachable; arrest → brig → fine → release loop closes |

**The progression spine is the identicard — and it already exists** (`player.py`: identicard,
visas, credits; customs enforces it; the brig is a built place). Tiers: undocumented →
visitor visa → resident → licensed trader / deputy → docking privileges (the Starfury cert).
Losing the card is canon-catastrophic, which makes it the perfect stakes object.

## A3. THE PHASES

### P0a — agent-dischargeable, blocking

**DONE (4j/4k), each with the evidence:**

| item | state |
|---|---|
| **verify L3** | **GREEN** — x1/x10/x60 all PASS at **0.05 m from the post**, three controls FIRE at 38–42 m short, exit 0. The 0.05-vs-5.59 dispute resolves to **0.05 m**; the 5.59 was a room leg laid as a straight line through a desk rank (`docs/life-L3.md` §2.5, §3) |
| **CI wiring** | `svariety`, `sdegeneracy`, `sagenda_selftest` in `validate.yml`, plus `sroomnav`, `sfootprint`, `sthe_shipped_scene_streams`, `sspec_gate`, `sdoc_chain`. **47 step ids, 0 unaggregated, every one `continue-on-error`** so no failure blinds the steps behind it |

**ALSO DONE (4l):**

| item | evidence |
|---|---|
| **CPU frame time at a stated NPC count** | **5.48 ms/frame** on blue/0/0 z7120 — 1,542,960 tri, 657 meshes, **84 baked bodies** — against `budget.DRAW["frame_ms"]` 16.667, so **3.0× headroom**. Measured as a DIFFERENCE (1,800 vs 5,400 frames) so the two-minute build and engine start-up cancel rather than being averaged in. `tools/frametime.py`. **The GPU half is unknown and the tool says so in its own docstring**: `--headless` is a null rendering driver, so nothing here touches rasterisation, shadows, SSAO or glow |
| **the playtest script** | `docs/PLAYTEST.md` — opens with what is measurably *missing* so a tester does not spend the session rediscovering it, names the five minutes that matter, and asks only for what a gate structurally cannot answer |

**STILL OPEN:**

| item | state |
|---|---|
| **60-minute soak with RSS sampling** | `tools/soak.py` written and committed; **first run in flight** at 660,000 frames, sized off the 5.48 ms measurement. Samples RSS from `/proc` *outside* the engine and reports **drift, not peak** — a leak is a rising floor |
| re-run `--life-test` | **not started.** Not run since the station grew 12× |

**Visible deliverable — the trailer re-cut from the real build — is now UNBLOCKED**, and it is
the first thing worth doing when the cores are free: L3 is green, the shipped scene streams, the
station is 53.9% built by length against 6.2% when the last trailer was cut, and the interior
camera has been fixed (`export_scene` framed tiled rooms at one bay of their length — every
frame in the previous cut was a close-up of a room 13× longer than it looked).

### P0.5 — the station streams, or everything after is built on one deck

**THE SHIPPED SCENE STREAMS AS OF 4j/4k.** `godot --headless --path godot`, no arguments:
`main: STREAMED -- 18 cells, starting in cell 13`, three cells resident (154,454 tri against
a 180,000 budget) with the neighbours arriving at **+17.8 m and +56.1 m of lead**,
`drop_m=0.053`, `cells=18 cell_resident=3`, boot **8.9 s → 3.7 s**. Gate: `python3
station/boot.py --gate`, hermetic, 10/10 with three controls; CI step
`sthe_shipped_scene_streams`. `coldstart.py` G3 PASS, G1 PASS, controls pass.

*And the finding was bigger than this section stated: `main.gd` not setting `cells_path` was
only half. **`walk.gd` called `_stream.update()` only inside `--stream-test`**, so even with a
path the shipped build primed one cell and never loaded a second. `stream.gd` scored a green
gate and moved nobody — finished, tested machinery with no caller on the shipped path.*

*Three record corrections: the cell baker is GDScript (`stream.gd::bake`), not Python; CI's
"Streaming cell manifest" step is about the sight-line table the baker READS, not the cell
set; and cells exist for **70 decks / 955 cells / 1.7 GB**, not "1 z-cluster of ~96".*

| still open in P0.5 | why it is not done |
|---|---|
| a body crosses **three cluster boundaries** | the shipped run crosses **cell** boundaries inside one cluster; cluster-to-cluster hand-off is untested |
| **RSS under a stated ceiling** | no ceiling has been stated and no soak has been run |
| **payload ceiling stated up front** | 1.7 GB of cells for 70 decks is measured; the figure has not been turned into a budget with a consequence |
| the shipped cell set is **stale** | cells sum to 735,732 render tri against the deck's 741,040 (−5,308); reported by `--gate` and by the engine banner on every run, fixed by `boot.py --bake` |
| `present_0300`/`present_1300` now measures **the primed cell's cast alone** (0 vs 1, was 4 vs 21) | `_start_clock` measures once before the viewer attaches, deliberately; re-measuring per transition would teleport people in front of the player |
| systems `main.gd` binds **once** may still read the cell set they booted with | `life.gd`'s Director is fixed (`_rebind_on_stream`); `ambience.gd::bind` takes `_world` at start-up and has not been audited |

**Visible deliverable:** a walk video across a sector seam.

### P0.6 — the three unowned preconditions

**DONE — a day index in `Clock` (4m).** `Clock.day()` counts midnights crossed, derived from
`hours_abs()` rather than stored, so a clock started at 13:00 is on day 0 until it reaches
**24.0 — its first midnight, not its first 24 hours**. Threaded to the shipped boot verdict as
`day=`. `--life-test`: *"THE CLOCK SAYS DAY 2 — P0.6's own gate"*, plus *"a jump does not send
it back to day 0"* and a control that fires (discard `day_offset` and the same jump takes day
2 → 0). `coldstart.py`'s `--no-clock` control now fails on `[bodies, clock, day]`.

**DONE — the crowd-physics policy, and it is THREE populations rather than one (4m).** Stated
here because unstated it reads as a bug, and each answer is deliberate with a measurement
behind it:

| population | solid? | why |
|---|---|---|
| **baked static geometry** | **NO — excluded by construction** | `rooms.is_solid` drops every `npc_` group. Static collision is generated once, so a person baked into it is a **permanent statue** standing where somebody stood at bake time |
| **named residents at runtime** | **YES** | `npc.gd::_give_body` gives each a `StaticBody3D` on `PEOPLE_LAYER` with `collision_mask = 0` — *a person is something that gets bumped INTO and has never needed to collide with anything itself*. The player is separated from them across the floor plane only, because putting them on the world layer costs the body its floor. Gated by `walkable.py --bump` with `--npc-solid=mask` as the control that must fail |
| **the corridor crowd (MultiMesh LOD)** | **NO — and this is the accepted cap** | It is instanced geometry with no bodies at all. **A player walks through it.** The number that justifies it: `--life-test` measures **1.93 µs per body**, and the crowd's borrowed frame share is 3,167 µs, so the ceiling is **~1,640 bodies** — against a corridor crowd derived from a 250,000-resident density. Giving the crowd bodies does not fit and no tuning makes it fit |

*The consequence a player sees: named people are solid, background crowd is not. That is a
legal cap, it is stated, and the number that sets it is measured rather than assumed.*

**STILL OPEN — the navigation graph into the engine.** The plan's own estimate: bigger than
L2–L9 combined. **Gate:** an NPC paths across decks on the engine graph.

### P0.7 — AN OWNER DECISION: THE PLAYER MOVES 3.4x FASTER THAN THE STATION DOES

**This is a decision to take, not a defect to fix, and the distinction matters.**
`godot/scripts/player.gd:23` says so in as many words — *"A person walks at 1.4 m/s; this is a
game, so it is faster."* Somebody knew the real figure and chose 4.2 deliberately. What is new
is the measurement of what that choice costs, now that the station is 1:1 and its NPCs are
Froude-scaled.

| who | speed | one lap of the blue ring corridor (1,329 m) |
|---|---|---|
| an NPC, derived by Froude scaling at the deck's own 0.760 g | **1.22–1.29 m/s** | **~18 min** |
| the player — `godot/scripts/player.gd:24`, a hardcoded literal | **4.2 m/s** | 5.3 min |
| the player sprinting — `player.gd:25` | **8.0 m/s** | 2.8 min |

`life.gd:1435` sets a commuter's `speed_m_s` from `populace._walk_speed`, so the NPCs *are*
physically right for the spin gravity while the player is a literal. The costs of the choice,
measured rather than argued:

- every inhabitant appears to wade — the player overtakes the whole station at 3.4x
- a 1:1 station traversed at 3.4x **feels a third of its size**, which is in direct tension
  with the reason this project is 1:1 at all
- every distance the simulation derives — commute times, schedules, `transit.py`'s costing —
  is calibrated against a pace the player never experiences

And the cost of *changing* it, which is why it is a decision and not a patch: **at the derived
1.22 m/s, one lap of the blue ring corridor is 18 minutes on foot.** The lifts, trams and core
shuttle exist precisely so a player does not walk it — but if they are not finished, deriving
the player's gait makes the station tedious before it makes it convincing.

**Three options, and the owner picks:**

| | player walk | one lap | what it costs |
|---|---|---|---|
| **A** keep 4.2 m/s | 4.2 | 5.3 min | the station keeps feeling ~1:3; NPCs keep wading |
| **B** derive it | 1.22 | 18 min | correct, and unusable until transit is finished |
| **C** derive it and declare a multiplier | e.g. 2.0x = 2.44 | 9 min | honest about being a game concession, logged as an invention with a number that can be tuned |

*If B or C: derive from the same function the NPCs use — the sqrt(g) law reproduces
`populace._walk_speed` to **0.00% across the whole gravity range**, so one reference pair plus
the law is the same authority, not a second opinion. Then `walkable.py`'s `MIN_TRAVERSE_M=63`
and `MIN_WALK_M` must move with it: both are derived from the 4.2 literal in their own
comments, so a speed change silently turns those gates red.*

*Found because a body walking to `plantroom_bay` covered 486 m in 20,000 physics frames —
**1.46 m/s sustained**, matching neither the 4.2 export nor the 1.22 derivation. Read
`player.step`: given a steer it sets `wish = Vector2(0, 1)` and moves at the full
`speed_m_s`, so the body was asking for 4.2. The likely answer is that it did not get it —
`--deck` spawns the corridor crowd and `npc.gd` gives every one of them a capsule, and 963
walkers over 1,329 m of corridor is **0.72 people per metre**. If that is the cause, 1.46 m/s
is not a defect at all but the first measurement this project has of what its own crowd
density costs a body trying to cross it — a 65% tax. **A/B to settle it:
`walk_deck(..., no_npc_collision=True)` against the same run; the flag already exists.** Not
yet run.*

### P1 — THE GAME EXISTS (G-track, expanded from the rejected draft)
- **G0** `docs/THE-GAME.md`: what the player wants, who can stop them, what failure costs.
- **G1 — A ROLE:** one complete job loop (dock work is the canon-obvious first: shifts exist,
  the port exists, pay exists). Work a shift → credits change → spend them at a bar the
  economy debits (the L7 seed, pulled early because the role needs it).
- **G2 — PROGRESSION & CONSEQUENCE:** the identicard tier ladder; arrest → brig → fine →
  release closes; visa revocation exists and can actually happen to you.
- **G3 — THE INCIDENT GENERATOR** (not one incident): classes seeded from `friction.py`,
  `security.py`, customs contraband, dock accidents; rate denominator ≥2/station-hour near
  the player; each class run **absent / helps / reports** produces 3 distinct world states.
**Gate:** a 60-minute headless day at x1 logs N incidents, M reachable, ≥1 consequence that
persists to day N+1. A session can end in a state the player would not have chosen.

### P2 — THE PLAYER PERSISTS
`player.py` gets its runtime reader + character UI (species, name, origin — the fields the
identicard already carries). Arrival begins at customs (C-010). Save/load **after** the day
index, gated on a **delta**: buy something, quit, reload, **stock still down** — fails today,
keeps failing until G1's economy seed lands, which is the point.

### P3 — LIFE, with denominators (the 4h L-track, effort split 60/30/10 within P3–P4)
L2 eat/sleep · L3 transit (verified in P0a, scaled here: **≥60% of the 857 can complete
their commute**) · L4 dialogue (**≥300 distinct lines; duplicate closer ≤10%; every
conversation offers ≥1 player utterance** — from today's 57/38-dupes/zero) · L5 react ·
L6 factions (friction visible in a corridor, measured without the player) · L7 economy
(stock, prices, the till) · L8 crime (feeds G3) · L9 information — **"the week has news"**:
two consecutive days' ISN/PA content differ, derived from traffic + incidents + the era
clock (`ERA_EVENTS` — the Narn–Centauri war is *rising* in S2–3, and the station should
feel it without a cutscene).

### P4 — VARIETY, SURFACE, THE EXTERIOR, AND DEPTH
- V-track to green **on every place a route passes through** (`variety.py` IoU ceiling;
  `--degeneracy` as precondition).
- 5 kits to craft ≥4 (A/B controls); landmark set to 4 by panel loop; **viewpoints 6 → ≥10**
  including the garden vista — the show's signature image.
- **The Starfury**: launch → fly → dock, seamless, headless-gated + piloted once.
- **Named-place depth: the tiling milestone.** `docking_bays` at 140 m walkable, not 15.5.
  `bay_span_m`'s own docstring says instancing along the footprint was always the design.
  **The owner's "in detail, fully" instruction settles A5's open question: depth is IN.**
- Generation stays offline → `.scn` → streamed. No in-engine port (85,455 lines, hard rule 4).

### STATUS OF THE AUDIT GAPS, AS OF SESSION 4q — read this before the entries below

The seven entries in §P4a and §P4b were written in 4p and are kept VERBATIM below, because their
diagnoses are the record of what was actually wrong. This table is what has moved since. Where a
row says HALF, the honest remainder is stated rather than rounded up.

| | gap | state after 4q |
|---|---|---|
| A4a-1 | the drum floor is empty at 4.5 M m² | **HALF.** `station/drum_dressing.py` (189/189) puts **1,945 features in 12 kinds** on it — 708 town blocks, 265 trees, 100 copses, 79 hedgerows, silos, sheds, jetties, reeds, spires, lamps, gantries — LOD-resolved, 92,848 tri at z=5400, inside the 183,880 of headroom judge-4e measured as unspent. Rendered end to end (`docs/engine-4q-drum-dressed.png`, Forward+, 53 s). **What is NOT closed: the scatter reads at 500 m and not at 20 m.** The near field is bare, the near tree is a lollipop, the parcel boundary underfoot is a hard straight edge. The ladder resolves DETAIL by distance; it does not place more things near the eye, and nothing measures features per m² at walking distance. See STATE.md §24.4b |
| A4a-2 | six subsystems at craft 1 | **5 of 6 rebuilt and scored 3, and THE LIST ITSELF WAS PARTLY STALE.** `council_chamber` 42/42, `docking_bay` 36/36, `garden` 44/44 (craft 1→3), `command_control` 65/65 + `cnc_ops` 22/22 (craft 1→3), `customs` 55/55. **`customs` was never craft 1 by 4q** — 4f had already rebuilt it and scored it 3 in `docs/craft-4f.md`, and nobody entered that round, so the count of six was reading a stale scorecard. *A scorecard with one round in it reads as a current score.* Remaining genuinely unmeasured: **exterior components** |
| A4a-3 | the plant layer cannot fail | **DONE on the simulation side, OPEN on the surface.** `station/plant_systems.py` (19/19) gives it `shed_factor()`, `wear_at()` and `state_key()`; 61 places shed load and wear feeds `incident.py`. **C&C reading any of it is the open half** |
| A4a-4 | room occupants are dioramas | **DONE** (4p) — 66 of 66 change state over a station-day, they sleep, verified on the streamed path |
| A4b-1 | the interaction layer is a wiggle, not a verb | **DONE.** `interact.RESPONDS` has 7 entries **including `sit` and `rest`**, the verb set is open/operate/read/rest/serve/sit/store/tread, and `interact.gd::use()` dispatches on `match it.verb`. `read` was the first verb with a consequence; it is no longer the only one |
| A4b-2 | there is no inventory, anywhere | **DONE** (4p) — the identicard and kit bag are drawn and `store` moves things in and out |
| A4b-3 | the economy is read-only in the game | **HALF.** The bar's till debits and the purse survives the process; most counters are still read-only |

**AND TWO GAPS THE AUDIT DID NOT NAME, both closed in 4q**, recorded here because they are the
same class — a rule the simulation enforced and the game could not reach:

* **Nobody checked your identicard.** `consequence.certain_check` had decided who may enter a
  place since P1-G2 and had NO RUNTIME CALLER — a player could walk into the command deck of a
  military station unchallenged. **98 of 129 places now read the card on the way in**, gated by
  `coldstart.py --g4` with four controls. The arrest chain behind a refusal is still Python: you
  are told, not detained.
* **Nobody ever fell over.** `incident.py` decided who collapses, where and at what hour, into a
  ledger nothing read; `ragdoll.gd` could drop a body only when its own gate flag asked.
  **45 incidents are baked per station-day for the boot deck** and a walker is pulled out of the
  crowd when the clock passes one. `coldstart.py --g5`, two controls.

### P4a — THE OWNER'S AUDIT, SESSION 4p — four gaps the phase list did not cover

**Raised by the owner directly, checked against the repository rather than answered from
memory, and placed here so they cannot be lost with a session's task list.** Each is real,
each is measured, and none of them was adequately in this plan before.

**A4a-1 — THE DRUM FLOOR IS EMPTY AT 4.5 MILLION m².** `garden.block_building()` and
`garden.tree()` *were* rebuilt to their density floor after the owner's "shitty little cubes"
and "sad excuse for a tree" — both docstrings now quote him. **The scorecard still reads
craft 1** because the last review found the ground rather than the buildings:
*"the habitat floor is two flat colour fields meeting along a straight-edged polygon boundary
with the terrain lattice visible in the zigzag. No vegetation, no props, no people, no relief,
**nothing standing anywhere on 4.5 million m²**."* And five distinct gazetteer rows — drum end
caps, three radial spokes, the sub-floor stack, the Garden, the radial tubes — **report the
IDENTICAL measurement** (121,976 tri, 5,764,561 m², λ 0.112), which is `--degeneracy`'s defect
at drum scale. Carried from round 1 and still open: *"the townscape traces to four authority-1
frames by subject and nothing in it is measured against them."*
**Two jobs:** populate the floor at a stated density, and **re-score** — the craft 1 predates
the generator rework and may now be stale in the other direction. Reference is the owner's
Starfield bar, not our own past work.

**A4a-2 — SIX SUBSYSTEMS ARE CRAFT 1**, and only ONE thing on the station is craft 4
(`exterior_approach`). The 1s: `garden_townscape`, `command_control`, `council_chamber`,
`customs_arrival`, `docking_bay_interior`, `exterior_components`.
**Two facts that change the priority.** `command_control` and `council_chamber` are **bespoke
modules** and still score 1 — *having a hand-written builder is not the same as clearing the
bar*, which is the layer-2b lesson again one level up. And `customs_arrival` +
`docking_bay_interior` are **the player's first ten minutes** (`arrival.py --report` walks
twelve legs through them), so they are the highest-value craft targets on the station.
Each runs CLAUDE.md's loop — build → harsh panel → rework → re-judge → stop — with every craft
claim citing a frame at the rubric's **half** distance, and AAA-STANDARD's 3-round cap.

**A4a-3 — THE PLANT LAYER CANNOT FAIL, and this is the sharpest of the four.** The owner's
requirement is that the station *"needs to be functional and working meaning all the stuff needs
to be real and function ie. can be messed up and have real effects."*
**What is real:** shifts are genuine data (command 08:00×8 h at `cnc`, traffic 08:00×8,
dockworker 06:00×9, medical 08:00×12, hydroponics 05:00×8, cleric 06:00×8; round-the-clock
posts rotate three watches at +0/+8/+16, with a recorded fix for a version that put the night
watch to bed), and 30 incident classes write 2,011 persistent events a station-day.
**What is not:** power, air, water, waste and rotation exist as **geometry plus a staffing
roster**. There is no state in which power drops and lights go out. **C&C has a watch roster and
controls nothing that can break.** `INC-BROWNOUT` is an event with a rate, not a system with a
load.
That is precisely the scope clause — *"the physical plant that makes 250,000 people possible:
food, water, air, power, waste"* — unbuilt as a *system*.
**SETTLE THE FORK BEFORE BUILDING:** a resource simulation (each system carries capacity, load
and a degradation curve, feeding the incident generator) or a scripted-failure layer. The
former is in the spirit of everything else here — **no rate in `incident.py` is authored** —
and is the larger build. Recommend deriving from the existing occupancy and roster models the
way `incident.py` already does.

**A4a-4 — ROOM OCCUPANTS ARE THE WRONG KIND OF OBJECT, and this is the largest of the four.**
The owner's reaction on being told is the correct one: *"they're just dioramas? how the fuck did
this happen"*. **It was not an oversight. It was a deliberate trade, and it was made for the
wrong case.** The diagnosis, from the source's own words:

There are **TWO crowd systems** aboard, and `walk.gd`'s header states the split outright:
*"an actor is **baked into the deck mesh**, a walker is an instance"*, and *"a baked walker had
one LOD because **a static mesh has no other option**"*.

| | ACTORS — room occupants | WALKERS — corridor crowd, commuters |
|---|---|---|
| what they are | geometry **welded into the deck `.glb`** | instances against `populace.station_crowd_library` |
| body | **their own individual** body, face, build, costume | their species' **nominal** body |
| can move | **no** — `life.gd`: *"a baked actor … can only be shown or hidden"* | yes, `add_commuter` / `drive_commuter` |
| animation | a pose chosen at bake time | free — swap the clip index |
| at runtime | `npc.gd::_physics_process` changes **their yaw only** — they turn to look at you within `notice_m` = 6 m, and that is the entire behaviour |
| LOD | one, forced | a ladder, picked per person per frame |

**`populace.py` records the trade and its own justification:** converting the corridor crowd to
instanced took walker geometry from 64,856 tri to ~23,000 shared, primitives 134 → ~48, and
animation from none to free — *"A net triangle saving, a primitive saving, **and it moves**.
What it costs is that a WALKER is their species' nominal body rather than their own — which is
what every real crowd system does, **and which room occupants do not pay**: they keep
`body.individual` and their own identicard either way."*

**So the axis was individuality versus motion, and rooms were given individuality.** The forcing
constraint was draw calls: *"a deck of 134 corridor walkers and 13 room occupants shipped
**1,262 primitives, 1,052 of them people**"* against `schedule.NPC_BUDGET["max_draw_calls"] = 32`.

**THE TRADE IS BACKWARDS FOR THE CASE IT WAS APPLIED TO.** A person two metres away who has a
unique face and never stands up reads worse than one with a shared face who gets up and leaves —
because at two metres *behaviour* is the thing being judged, not bone structure. Individuality
buys most at conversational range only if the person is otherwise alive. **Distance wants
silhouette; proximity wants behaviour.** The station currently has it the other way round.

**THE FIX EXISTS AND IS PARTLY BUILT.** The instanced path already works — 963 corridor walkers
move 5,966 m in a walk test, commuters route across decks on the nav graph. Room occupants must
migrate to it and gain a behaviour loop (arrive, sit, eat, work, stand, leave) driven by
`schedule.RHYTHMS`, which already knows every Narn is asleep at 03:00. **The constraint that
forced the baked path is draw calls and primitives — which is precisely what P4's spatial
submission work addresses**, so these two are the same project and should be sequenced together.

**And the missing clip.** `npc/animation.py`'s `CLIP_SET` is `("walk_ladder", "idle", "talk",
"sit")` — **no sleep or recline clip at all** — so even once occupants can move, a residential
corridor at 03:00 has nobody lying down.

*Related, and it bounds how much of this is visible today:* **262 bodies are baked into scene
data across 4 decks** against 250,001 modelled, so the named-resident layer and the visible-body
layer meet only where a deck has been baked.

### P4b — THE SECOND AUDIT, SESSION 4p — the owner asked "what ELSE am I missing"

Asked after A4a-4, and the answer is three more of the same class. **They share one root cause
and it is stated at the end; read that before the three.**

**A4b-1 — THE INTERACTION LAYER IS A WIGGLE, NOT A VERB.** `interact.py` reports 357 of 357
declared interactables built and `RESPONDS` covers 5 of the 8 verbs — and what "responds" means
is the whole finding. `interact.gd::_press` increments a counter, sets `press_left` so the prop
**visually depresses for a few frames**, resolves a push direction, and prints a log line.
**There is no verb dispatch anywhere.** `open`, `operate`, `read`, `store` and `serve` all do the
identical thing. **`read` displays no text. `store` has no inventory to move anything into.
`serve` runs no transaction.** And `sit` and `rest` are in `PRESSABLE` but NOT in `RESPONDS` — so
a player can press E on a chair and **not sit down**.
The file's own header says it set out to end *"357 declarations, 0 verbs"*. It ended the
*declaration* gap. **The verb gap is still open**, and the module's success statistic measures the
half that was closed.

**A4b-2 — THERE IS NO INVENTORY. ANYWHERE.** Zero references in all 16,865 lines of
`godot/scripts/`. The identicard, the kit bag and credits exist in `player.py`; nothing carries
anything.

**A4b-3 — THE ECONOMY IS READ-ONLY IN THE GAME.** `economy.py` (25/25) and `dockwork.py` (23/23)
are working simulations — stock, prices, tills, wages, rent tiers, a fourteen-day trace in which
a lurker crosses the passage-home line on day 4 — and **the only runtime consumer of any of it
is `hud.gd` drawing a NUMBER out of a JSON file Python wrote.** The player cannot buy anything.
The bar, the market, the kiosks and the black market all exist as geometry and **not one of them
will take your money.** P1-G1's gate is honest about what it proved — that the ledger persists
and the engine can *read* it — and that is not the same as a shop.

**THE ROOT CAUSE, AND IT IS ONE SENTENCE.** *The simulation is Python and the game is GDScript,
and the bridge is one-way: Python bakes, the engine reads.* Everything that works in a `--gate`
and not in the game is this. It is **the owner's own session-4d ruling, still true**: 85,940
lines of Python against ~17,000 of GDScript, and the ruling then was *"the project has been
optimising what can be counted, because counts go green and a game cannot be expressed as a
count."* The counts are now much better and the ratio has barely moved.

**So the fix for A4a-4, A4b-1, A4b-2 and A4b-3 is the same fix**, and they should be sequenced as
one track rather than four: **the runtime needs to ACT on the simulation, not render a snapshot
of it.** A person who can stand up, a chair you can sit in, a counter that takes credits and an
inventory to put the thing in are four faces of one missing layer.

**Sequencing note:** this outranks P4's variety and surface work. A craft-4 room full of dioramas
you cannot interact with is worth less than a craft-3 room where people live and the shop works.

### P5 — SHIP
Packaging, onboarding, controls, accessibility, credits, IP statement (fan work, non-
commercial, stated once). **Gate: §T all green or signed OUT; every A2 clause cited to its gate.**

### P0h — the human (non-blocking, now TWO sittings)
20 minutes after P2 (arrival + save), 20 after P3 (a living day), fps on target hardware
whenever hardware exists. One sitting at the end was too thin for a tens-of-hours claim.

## A4. THE PERFORMANCE BRANCH (pre-written)
Comfortably over → proceed. Marginal → LOD/cell-budget displaces P4 surface. Far under →
LOD + occlusion + payload displace P4 entirely; P3 denominators re-derived under the new cap.

## A5. DECISIONS RESOLVED BY THE OWNER'S LATEST INSTRUCTION
- **Named-place depth: IN** (P4 tiling). "One bay deep" is dead.
- **The vertical-slice alternative: DEAD.** The full 3c scope is the target.
- **73,507 unnamed bays: still OUT** (4h ruling stands — sealed or generic-but-varied;
  nothing in 3c requires entering them; 1:1 is scale, and scale is real).
- **2026-08-04: SUPERSEDED on tiling and dialogue scope by docs/THE-STATION.md** — the
  "73,507 unnamed bays" line misread STATE §13: those ARE the named places' footprint
  bays (corrected 73,635→49,265 by V1 `_fit_bay`, c4f989b; STATE §13 carries the note);
  P4/L4 re-derive from the bible (49,265 gross / 23,716 net-of-seals tiling, 6,544-line
  dialogue floor).

## A6. BLOCKING CONFLICTS — unchanged: C-003/C-004 isolated behind single register fields.
## A7. ADR-0001 gets its dated GDScript note. Free, owed, done in P0a.

## A8. THE STANDING RULES (all previous, plus)
6. **The absence gate is permanent:** any life system's CI check runs the day player-absent
   and player-present and asserts they differ. A world that only moves when watched is a set.
7. **Content denominators only ratchet up.** A distinct-line count or incident rate that
   drops fails CI, like a craft regression.

## 0. WHAT THIS IS AT THE END

A 1:1, canon-accurate Babylon 5 you can walk end to end and fly out of, era-locked to Season 2–3,
in which **250,000 people live by their own schedules** — and you can watch them do it. The owner's
words, still binding: *"a living thing rather than a building"*, *"the simulation exists around you
rather than in text"*, and the friction between factions **visible in a corridor**.

## 1. THE STRATEGIC RULING — LIFE FIRST

### The fact that decides it

**We reinvented Starfield's worst feature and were trying to beat Starfield with it.** Starfield's
hand-built cities are its best work — hundreds of artists, years — and its *procedurally generated*
content is the single most criticised thing in the game: the same lab, over and over. That is
exactly our **78 of 128 places built from one generic kit**, and it has the same cause.

And the constraint that settles the argument: **one agent authors everything, with no artists.**
Measured rate is four landmarks from craft 1 to craft 3 in a 70-minute agent session. 128 places at
that rate is roughly thirty sessions for **one pass**, and they would still be craft 3.
**Hand-authoring our way to AAA surface is not reachable — not slowly, not at all.**

### The two rulings

> **1. LIFE FIRST.** Roughly **60% life, 30% variety, 10% surface**. Surface quality is hard-capped
> by having no artists; **simulation depth has no ceiling**, and it is the thing an agent is
> actually good at building. Babylon 5 is a story setting: what people love is Downbelow and the
> Zocalo being *alive with factions*, not the polygon count. **A living craft-3 station is far more
> like Babylon 5 than a beautiful empty one.** Compete where Starfield failed, not where it won.
>
> **2. THE SHELL STAYS 1:1; ONLY THE NAMED PLACES GET INTERIORS.** The 8,047 m hull, its 70 ring
> decks, the drum and the whole circulation network remain exactly 1:1 and walkable end to end. The
> ~128 named places plus their connective corridors get real interiors. The other 73,507 bays are
> sealed or generic-but-varied, and **that is stated rather than counted as a shortfall**. 0.17% of
> footprint was never the blocker; identical rooms were.

### What this does NOT mean

It is not an abandonment of AAA. It is a decision about *where* the quality goes: into a station
that is **consistent, characterful and alive** rather than one that is beautiful in twelve rooms
and empty everywhere. Surface work continues — but only at the **kit** level, where one pass
multiplies across all 70 decks at once, which is how the corridor went 3 → 4 in a single session.

---

## 2. THE THREE TRACKS, AND THEIR SHARE

| | track | why this share | measured by |
|---|---|---|---|
| **60%** | **L — LIFE** | uncapped, differentiating, and code rather than art | **AGENCY**: residents executing a schedule *by moving*; verbs with world-state consequence; lines of dialogue heard |
| **30%** | **V — VARIETY** | the credibility floor. Fixes "every corridor looks the same" at its root | **VARIETY**: pairwise distinguishability between places, using the instrument `body.py --silhouette` already proves works |
| **10%** | **S — SURFACE** | capped, but kit work multiplies across everything | the existing craft rubric, at the half distance, **kit-level only** |

**Both new gates fail today and neither is a coverage count.** That is the point: every gate this
project has ever had measures *coverage* or *correctness*, and both are perfectly satisfied by one
generic thing repeated seventy-eight times.

---

## 3. THE L-TRACK — the ladder, and every rung is player-visible

Today: **zero** residents move, **zero** verbs change world state, **zero** lines of dialogue. All
the *data* exists — `populace` knows every resident's name, species, home, job, role, faction and
species-specific meal and sleep times; `npc/schedule.py` derives the day; `transit.py` costs every
journey; `routes.py` can path between any two places. **None of it runs.** `life.gd`'s own comment:
*"the runtime cannot create a person, so a room busier than its bake hour is capped"* — it shows and
hides pre-baked bodies by the hour.

| L | milestone | done when | today |
|---|---|---|---|
| **L1** | **Someone goes to work** | one named resident leaves their quarters at their own start hour, walks a `routes.py` path, and is at their post. Asserted headlessly | 0 |
| **L2** | **They eat and they sleep** | the species-specific meal and sleep times in `schedule.py` move bodies to a mess, a bar, a bunk | 0 |
| **L3** | **They use the transit** | a resident takes the lift to another deck, or the tram along the drum, and arrives. The vehicles already move | 0 |
| **L4** | **They talk** | `dialogue.gd` is 912 lines with **no content**. Lines keyed on who they are, what they are doing, their faction and the era | 0 lines |
| **L5** | **They react to you** | `npc.gd` already notices. Make it mean something: they move aside, they greet, they refuse | partial |
| **L6** | **The factions act** | Psi Corps, Narn–Centauri friction, security patrols, Downbelow's underclass. **The friction visible in a corridor**, which is the owner's own test | 0 |
| **L7** | **The economy turns** | a bar's stock falls when somebody buys. Money exists — a till is a till because there is money | 0 |
| **L8** | **Crime and law** | a theft happens, is reported, security responds, the brig fills | 0 |
| **L9** | **The information layer** | ISN, PA and signage report **what actually happened**, not a script | ambience only |

**L1 is the whole track in miniature and is the next thing built.** Everything above it is the same
machinery with more verbs.

## 4. THE V-TRACK — variety, generated rather than hand-authored

The register already knows what every place **is**: its functions, its declared interactables, its
fixtures, its faction, its species mix, its authority. **That has never driven form — only which
props get dropped in.** A generic room is generic because one generator with ten archetypes serves
seventy-eight places.

| V | milestone | done when |
|---|---|---|
| **V0** | **The gate exists and is red** | pairwise place distinguishability measured and reported, with the one-parameter-block control that must read 1.000 |
| **V1** | **Form follows function** | a medlab's *plan* differs from an office's because a medlab is not an office — bay rhythm, ceiling height, servicing, circulation, all keyed on the register |
| **V2** | **A corridor is not one corridor** | sector palette, deck age, traffic wear, faction presence. One kit, many readings |
| **V3** | **No two visited places are indistinguishable** | the gate goes green on everything a route passes through |

## 5. THE S-TRACK — surface, kit-level only

**A craft pass on a kit multiplies; a craft pass on a room does not.** `interior_kit.corridor_section`
is every one of the 70 decks at once — that is how the corridor went craft 3 → 4 in one session.
The lift interior and the transit car are the same lever: they are what a player looks at for most
of any journey.

Per-location craft passes are **not** in the 10%. They come after L and V, ordered by the routes,
authority-1 first — and a *generic* place still has to be **unidentifiable as generic**, which is
V's job, not S's.

---

## 6. WHAT IS EXPLICITLY OUT

* instancing the 73,507 unnamed bays
* hand-authored AAA interiors for all 128 places
* beating Starfield on surface fidelity — stated plainly so nobody spends a session trying
* the old M0–M11 milestones, layer numbers 0–8 as an ordering rule, and the W-track

## 7. THE RULES THAT SURVIVE, AND ONE THAT IS NEW

All of `CLAUDE.md`'s hard rules stand — nothing from memory, log every invention, blocking
conflicts block, inside and outside from one schema, double precision, update `STATE.md`. So does
the negative-control discipline, which is the highest-yield thing in this project.

**New, and it is what this session cost to learn:**

> **A GENERATOR IS FINISHED WHEN ITS OUTPUT IS VARIOUS, NOT WHEN ITS OUTPUT IS CORRECT.**
> One kit passing every closure, winding, budget and material gate while producing seventy
> identical decks is the disease, not the cure. And **do not send agents at defects** — defects are
> what gates find, so gates are what keep getting fed. Point them at content and behaviour.
