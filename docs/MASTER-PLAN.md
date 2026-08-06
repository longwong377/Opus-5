# MASTER PLAN — Babylon 5, alive

**Session 4h. This replaces every previous plan as the ordering rule.** The session-3k document —
three tracks, twelve milestones M0–M11 — is preserved as `docs/MASTER-PLAN-3k.md` because its audit
is still the best analysis in the repository; it is no longer what decides what to work on.
`docs/SHIP-PLAN.md`'s audit of the four contradictory plans stands as the record of *why* this
rewrite happened, and its connectivity work is finished. Set by the owner after a strategic
reassessment, with two rulings recorded in §1.

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
