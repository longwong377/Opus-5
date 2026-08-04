# MASTER PLAN — Babylon 5, alive

**Session 4h. This replaces every previous plan as the ordering rule.** The session-3k document —
three tracks, twelve milestones M0–M11 — is preserved as `docs/MASTER-PLAN-3k.md` because its audit
is still the best analysis in the repository; it is no longer what decides what to work on.
`docs/SHIP-PLAN.md`'s audit of the four contradictory plans stands as the record of *why* this
rewrite happened, and its connectivity work is finished. Set by the owner after a strategic
reassessment, with two rulings recorded in §1.

---

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
bodies **2,504 of 250,000**; **`boot.py` emits one `.glb`, `main.gd` never sets
`cells_path` — the shipped scene loads ONE DECK and never streams**; streaming cells exist
for 1 z-cluster of ~96; **zero `Navigation*` in godot/**; **no day index**; crowd
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
CI wiring (`variety.py`, `--degeneracy`, `agenda.py --selftest`); ~~**verify L3**~~ **L3 IS
VERIFIED AND GREEN (4j)** — x1/x10/x60 all PASS at **0.05 m from the post**, all three controls
FIRE at 38–42 m short, exit 0; the dispute resolves to **0.05 m**, and the 5.59 m was a room leg
laid as a straight line through a desk rank, fixed by `station/roomnav.py` (evidence:
`docs/life-L3.md` §2.5 and §3); re-run `--life-test`; 60-min soak with RSS; CPU frame
time at stated NPC count ("GPU half unknown" in the same line); the playtest script.
**Visible deliverable:** the trailer re-cut from the real build after L3 is green.

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
Navigation graph into the engine (bigger than L2–L9 combined); **a day index in `Clock`**
threaded through the boot manifest; crowd-physics policy stated (non-colliding is a legal
cap, unstated it reads as a bug). **Gate:** an NPC paths across decks on the engine graph;
the clock says day 2; the policy is a sentence in this file.

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
1.46 m/s sustained, matching neither the 4.2 export nor the 1.22 derivation. That third number
is still unexplained and is the one genuine defect here.*

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
