# MASTER PLAN — Babylon 5, alive

**Session 4h. This replaces every previous plan as the ordering rule.** The session-3k document —
three tracks, twelve milestones M0–M11 — is preserved as `docs/MASTER-PLAN-3k.md` because its audit
is still the best analysis in the repository; it is no longer what decides what to work on.
`docs/SHIP-PLAN.md`'s audit of the four contradictory plans stands as the record of *why* this
rewrite happened, and its connectivity work is finished. Set by the owner after a strategic
reassessment, with two rulings recorded in §1.

---

# SESSION 4i AMENDMENT — THE ORDERING RULE, SUPERSEDING §2–§5 BELOW

**Status: PROPOSED, awaiting the owner. Nothing below §1 of this amendment is adopted until
the owner assents to A1 and A2, because both reverse an owner ruling made one day earlier.**

This is an amendment rather than a fifth document, and that is the most important structural
decision in it. `CLAUDE.md` is the file every session reads first and its contents override
default behaviour; it points here. **A new document `CLAUDE.md` does not name would be read
*after* the 4d ruling and the eight-layer table by every future context** — a plan that cannot
take effect, which is this repository's own "a gate that does not run is not a gate" one level
up. The adoption commit edits `CLAUDE.md`'s plan section or this amendment is void.

## A0. GROUND TRUTH — every row carries the command, and four rows were WRONG

The 4i draft's ground truth was presented as measurement and was partly recall. Corrected:

| | | how |
|---|---|---|
| hull | 8,047 m, r_max 480.3 m, envelope 1.977 km3 | `radius_profile.json`, 1,978 samples |
| places / decks | **128** over **71** | `directory.PLACES` |
| circulation | **249 edges**, **1 component** | `routes.py` — 96 ring, 71 axial, 70 lift, 8 spoke, 4 trunk |
| canon adjacency | **46 declared, 46 reachable, 0 not** | `routes.py` |
| distinctness | **128/128 distinct**; **6/6 modules distinct** | `deck.py --degeneracy` |
| **variety** | **18 clusters, largest 5, covering 45 of 128 — STILL RED** | `variety.py`, V1 (`c4f989b`) |
| bays | 73,635 implied, **128 built = 0.17%**; named places are **one bay deep** | `docking_bays` is 140 m; a player walks 15.5 m |
| code | 115,874 Python / 14,718 GDScript / **0 C#** | contradicts `adr/0001` — see A7 |
| runtime | **27 load sites, 0 geometry-generation sites** | grep |
| **dialogue** | ~~0 lines~~ **2,139-line module; 73 conversations, 168 speech, 57 DISTINCT, 38/73 close on one string, ZERO player utterances, on 1 of 71 decks** | the draft's "0 lines" was 22.6 h stale when written |
| **payload** | ~~2.39 GB~~ **4.5 G total / 3.9 G station** | `du` |
| **bodies** | ~~857~~ **2,504 in the built world** (1,060 actors + 1,444 crowd) against 250,000 | counted over 70 decks |
| **streaming** | **24 cells exist, all on ONE z-cluster of ~96. `boot.py` emits a `glb`, never a `cells_path`, so the shipped scene never streams** | `boot.py:239`, `main.gd:181`, `walk.gd:128` |
| **navigation** | **zero `Navigation*` references in `godot/`.** `npc/navigation.py` (3,010 lines) is consumed only by Python | grep |
| clock | **no day index.** `life.gd` `hour()` is `fposmod` — there is no second day | `life.gd:88,107` |
| crowd | **non-colliding by design** (`npc.gd:367` `collision_mask = 0`) | undiscussed policy |
| L-track | L1 done (N=1). **L3 DISPUTED — passes in a worktree at 0.05 m, fails in the main tree at 5.59 m** | `agenda.py --commute` |
| performance | **never measured on a GPU.** `streaming-4g.md:26` puts one component at 74 M tri / 6 GB | 412x the cell budget |
| playtest | **never, by anyone** | — |

**Four of the draft's nine "completely missed" items were false and are struck:** a stopping
rule exists (`AAA-STANDARD.md` "The hard stop", never exercised); player identity exists
(`player.py` 677 lines, `arrival.py` 1,401) but **has no runtime reader in any `.gd`**;
performance was named in three planning documents; and the owner — not an agent — caught the
two largest defects this project has had, so "every judgement is an agent marking its own
homework" is false.

## A1. THE TWO REVERSALS THAT NEED THE OWNER'S ASSENT

1. **Sequencing before the 60/30/10 split.** The 4h ruling allocated 60% life / 30% variety /
   10% surface. This amendment puts streaming, a day index, navigation and a game premise
   *ahead of and blocking* the L-track. That is a re-ordering, not a re-weighting — the split
   still governs effort **within** the tracks — but it must be said out loud.
2. **The unnamed bays stay out.** 4h §6 explicitly excluded instancing the 73,507 unnamed
   bays; the draft quietly reversed it. **This amendment keeps them out** and instead states
   the shortfall it does own: **named places are one bay deep and that is the ship**, unless
   the owner wants a tiling milestone.

## A2. THE DEFINITION OF DONE, AND IT MAY NOT NARROW THE BINDING SCOPE

`CLAUDE.md`'s session-3c scope statement is binding on everything: customs and immigration,
law enforcement, crime, the black market, Downbelow's underclass, every faction with its
friction visible in a corridor, the physical plant, an information layer, a flyable Starfury.
**A Definition of Done narrower than that lets scope evaporate item by item with no gate able
to notice** — which is exactly how the Starfury and the jump gate vanished from the draft.

> **DONE = a stranger downloads one file, runs it, arrives at Babylon 5, is drawn into
> something that would have happened without them, changes how it ends, and finds the station
> different when they come back — and the 3c scope list is either built or written on the
> EXPLICITLY OUT list with a reason.**

**EXPLICITLY OUT until the owner says otherwise:** instancing 73,507 unnamed bays; hand-authored
interiors for all 128; multiplayer; localisation; modding; commercial release (this is a fan
reconstruction and cannot be sold — stated once, here).

**EXPLICITLY IN and currently ownerless — the draft's worst omission:** the **flyable Starfury**
and the exterior. Built, reachable at HEAD (`--mode=starfury`), in `CLAUDE.md`'s headline, and
in no phase of the draft. It is owned by P4 below.

## A3. THE PHASES

Ordered by *what the next phase would otherwise be built on top of wrongly*.

### P0a — WHAT AN AGENT CAN DISCHARGE ALONE (blocking)
Nothing here needs a human, because a phase whose gate needs a human must never block one
that does not.
- **Wire the gates that exist into CI.** `variety.py`, `deck.py --degeneracy`,
  `agenda.py --selftest` as `validate.yml` steps, using the existing `continue-on-error` +
  final-outcome pattern. **A gate is not adopted until it is a step in `validate.yml`.**
- **Verify L3.** Re-run `--commute` at x1/x10/x60 with its three controls and resolve the
  0.05 m / 5.59 m disagreement. Re-run `--life-test`, which has not run since `life.gd` gained
  405 lines.
- **Headless 60-minute soak** with RSS sampled, and a CPU-side frame time through lavapipe at
  a stated NPC count — reported *with* "the GPU half is unknown" in the same output.
- **Write the 20-minute playtest script** the human will follow.
**Gate:** CI reports every gate's own outcome; L3 is green or its failure is characterised.

### P0.5 — THE STATION STREAMS, OR EVERY PHASE AFTER IS BUILT ON ONE DECK
**This is the highest-ranked finding and it is not optional.** `boot.py` emits one `.glb` and
`main.gd` never sets `cells_path`, so the shipped build loads a single deck. Every player
system built before this is validated on a topology the shipped world does not have — and
**residents commute across decks**, so L1–L3 are exactly the systems that would be wrong.
- `boot.py` emits a cell set; `_configure_walk` sets `cells_path`; all ~96 z-clusters baked.
- Per-cell triangle and memory budget; a **streaming-failure policy with a negative control
  that forces a load failure**.
**Gate:** the shipped scene boots streamed, a body walks across three cluster boundaries,
RSS holds under a stated ceiling, and the forced-failure control fires.

### P0.6 — THE THREE PRECONDITIONS NOTHING OWNS
Each is a prerequisite of the L-track and each is currently invisible.
- **The navigation graph reaches the engine.** Bigger than L2–L9 combined and assumed by all of them.
- **A day index in `Clock`,** threaded through the boot manifest — *before* save/load is
  designed. There is currently no second day to come back to.
- **A crowd-physics policy, stated.** Non-colliding is a legitimate cap; an unstated cap reads
  as a bug.
**Gate:** an NPC paths between two decks using the engine's graph; the clock reports day 2.

### P1 — THE GAME EXISTS (G-track)
The draft named "there is no game" and gave it no phase, no gate and no budget. That is the 4d
failure repeated one level up.
- **G0 — `docs/THE-GAME.md`:** what does the player want, who can stop them, what does failure
  cost. Answered in writing before anything is built.
- **L0 — AN INCIDENT** (below L1, not above it): a person who wants something, a rule
  forbidding it, an officer whose beat passes, an outcome that differs by what you do. Every
  input already exists — `npc/friction.py`, `npc/security.py`, `resident.identicard`,
  `traffic.arrivals`.
**Gate:** the same incident run **player-absent / player-helps / player-reports** produces
three different world states. A session can end in a state the player would not have chosen.

### P2 — THE PLAYER PERSISTS
- Wire `player.py` to a runtime reader and a character UI (it has neither).
- **Arrival begins at customs, not in the bay,** until C-010 closes.
- Save/load — designed **after** P0.6's day index, and gated on a **delta**.
**Gate:** buy something, quit, reload, **the stock is still down.** This fails today and keeps
failing until L7, which is the point — `life.gd`'s state is a pure function of the clock, so a
save gate written now would pass on day one and forbid the economy later.

### P3 — LIFE (the 4h L-track, with denominators)
L2 eat/sleep · L3 transit · L4 dialogue · L5 react · L6 factions · L7 economy · L8 crime ·
L9 information.
**Gate per rung — never "it happened once".** L1 passed with one resident, *"one of exactly
two people on the station who can"*. Every rung states **a population denominator and a
variety denominator**: "N of the deck's residents", "M distinct lines heard in a 20-minute
walk". L4's denominator starts at 57 distinct lines, 38/73 duplicated, zero player utterances.

### P4 — VARIETY, SURFACE AND THE EXTERIOR
- **Variety scoped to the places a route passes through** (V3's own wording), gated by
  **`variety.py` IoU with a stated ceiling** — `--degeneracy` is the cheap precondition and
  **cannot fail on a seeded generator**.
- Kit-level surface: **5 of 5 kits at craft ≥4**, each with its own half-distance frame and an
  A/B control.
- **The Starfury, launch, dock and the exterior** — owned here, or moved to EXPLICITLY OUT.
- Generation stays **offline in Python → `.scn` → streamed.** The draft's "port the generators
  in-engine" is 85,455 lines across 55 modules and would create a second description of one
  decision — hard rule 4. If it is ever needed, **the agreement gate between the two
  implementations is the deliverable**, not the port.

### P5 — SHIP
Onboarding, controls, accessibility, packaging, credits, IP statement.
**Gate:** each clause of A2's Definition of Done, cited to the gate that proves it.

### P0h — THE HUMAN (non-blocking, scheduled once, with a date)
fps on target hardware, and the 20-minute playtest against P0a's script.

## A4. THE BRANCH NOBODY WROTE

**P0h can invalidate P3, P4 and the payload, and the plan must say so in advance.** With no
structure LOD, occluders at 6 of 7, and one component measured at 74 M triangles / 6 GB, a
15 fps result is plausible. Recorded now:
- **comfortably over** → proceed as written.
- **marginal** → LOD and cell-budget work displaces P4's surface half.
- **far under** → LOD, occlusion and payload reduction displace P4 entirely and P3's
  denominators are re-derived against the new body cap.

## A5. THE SHORTFALLS, STATED AS DECISIONS RATHER THAN LEFT TO BE FOUND
- **2,504 bodies against 250,000.** The mechanism is near-field instantiation from the offline
  day; the cap is a design position, not a gap.
- **Named places are one bay deep.** `docking_bays` is 140 m and you walk 15.5 m. The 4h
  ruling covered *unnamed* bays; it does not cover this, and this amendment does not fix it.

## A6. THE BLOCKING CONFLICTS THIS PLAN MUST NOT WALK PAST
**C-003 and C-004 are open and BLOCKING** — which longitudinal band is the habitat drum, and
which ring is level 1. Both reduce to one piece of evidence each.
- Player-facing level numbering is **provisional pending C-004** and read from **one register
  field**, so it can be re-stamped in one place.
- Player-facing sector naming is provisional pending C-003 — the Green/Brown transposition,
  which is also why our fifth sector is "Yellow" and the show's is "Brown".

## A7. THE FREE FIX NOBODY OWNS
`adr/0001-engine-choice.md` and `CLAUDE.md` both say **"Godot 4, C#"**. There are **zero C#
files**. A decision that exists in two descriptions will have to be made again. Amend ADR-0001
with a dated note — GDScript in practice, C# not adopted, and why. One paragraph, free.

## A8. THE RULES THIS AMENDMENT ADDS
1. **A gate is not adopted until it is a step in `validate.yml`.**
2. **A phase whose gate requires a human must never block a phase whose gate does not.**
3. **Every ground-truth row carries the command that produced it and is re-run, not recalled.**
   Four rows in the 4i draft were stale, including one repeated to the owner all session.
4. **A rung passes with a denominator, never with an existence proof.**
5. **A plan that `CLAUDE.md` does not point at is not the plan.**

---

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
