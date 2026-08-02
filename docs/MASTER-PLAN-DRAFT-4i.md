# DRAFT — MASTER PLAN 4i. NOT ADOPTED. This document exists to be attacked.

## 0. GROUND TRUTH — every number here was measured this session, not recalled

| | |
|---|---|
| hull | 8,047 m, max radius 480.3 m, envelope 1.977 km3 |
| sectors / rings | 5 sectors, 4 concentric rings + core, 3 spokes in Green |
| named places | **128**, over **71** distinct decks |
| circulation | **249 edges** — 96 ring, 71 axial, 70 lift, 8 spoke, 4 trunk |
| connectivity | **1 component**. Remove spines -> 96 pieces; remove lifts -> 71 |
| canon adjacency | **46 declared, 46 reachable, 0 not** |
| geometry distinctness | **128 places, 128 distinct** (deck path); **6/6 modules distinct** (render path) |
| bays | **73,635 implied, 128 built = 0.17%** |
| named floor | 1,130,026 m2 declared; 16,194 m2 built as distinct rooms = 1.43% |
| code | **115,874 lines Python**, 14,718 GDScript, **0 C#** |
| runtime | **27 file-load sites in GDScript, 0 geometry-generation sites** |
| shipped data | 2.39 GB for 70 decks |
| L-track | L1 done (1 resident walks to work). L3 disputed. **L2, L4-L9 = 0** |
| dialogue | **0 lines** in a 912-line system |
| residents | 857 baked with home+job; **0 of 857 have both on one deck** |
| audio | ambience 100/100. No event audio, no occlusion, no reverb |
| craft | corridor 4, Zocalo 3, generated rooms 1, garden 1 |
| viewpoints | **6 places** can see outside |
| performance | **never measured on a GPU. Not once.** `budget.py` is a proxy and is over budget |
| playtest | **never. By anyone. Not once.** |

## 1. WHAT WE HAVE COMPLETELY MISSED

Not "not done yet" — *never considered*. This list is the reason this document exists.

1. **THERE IS NO GAME.** No goal, no stakes, no progression, no failure, no reason to play.
   The 4h plan says "life first", but life without stakes is a screensaver. A perfectly
   simulated station nobody has a reason to be in is a tech demo.
2. **NO SAVE/LOAD.** Zero references anywhere. A simulation that cannot persist is a demo.
3. **NO PERFORMANCE MEASUREMENT ON REAL HARDWARE, EVER.** No GPU has ever run this.
   Framerate is completely unknown. `budget.py` counts triangles, which is a proxy.
4. **NO HUMAN HAS EVER PLAYED IT.** The owner is hands-off until ship. Every quality
   judgement in this repo is an agent scoring its own work.
5. **NO PLAYER IDENTITY.** Who are you? No character creation, no role, no arrival reason.
6. **NO BUILD OR DISTRIBUTION.** No packaging, no installer, no way for a person to run it
   except cloning a repo and compiling an engine for 61 minutes.
7. **NO TRAVERSAL DESIGN.** The station is 8 km. Walking it at 1.47 m/s is 91 minutes.
   Is that fun? No fast travel design, no transit-as-gameplay.
8. **NO IP POSITION.** This is a Babylon 5 fan reconstruction. It cannot be sold. That
   constrains what "finish" means and has never been stated.
9. **NO STOPPING RULE FOR "PERFECTION."** The owner said perfection. Undefined = never done.

## 2. THE DEFINITION OF DONE

**Done = a person who has never seen this repo can download one file, run it, arrive at
Babylon 5, live a day there, and want to come back.**

Six clauses, each independently gateable:
- **download one file** — packaged build
- **run it** — 60 fps on target hardware, measured
- **arrive** — an arrival sequence with an identity
- **live a day** — schedules, meals, sleep, work, transit all running
- **there** — the place is recognisably Babylon 5 to a fan
- **want to come back** — stakes, consequence, persistence

## 3. PHASES

### P0 — PROVE IT RUNS (blocking everything)
- Package a build. One artefact, one command.
- Measure fps on real hardware. If nobody has a GPU, this is the first thing to buy or rent.
- One human plays it for 20 minutes and writes down what happened.
**Gate:** a stranger runs it and reports a framerate and three sentences.

### P1 — THE PLAYER EXISTS
- Character: name, species, role, reason to be aboard.
- Arrival: dock, customs, identicard, quarters assigned.
- Save/load: the station's clock, the player's state, resident state deltas.
**Gate:** quit mid-corridor, reload, everything is where it was.

### P2 — LIFE (the 4h L-track, unchanged in substance)
- L2 eat/sleep, L3 transit (finish), L4 dialogue, L5 react, L6 factions,
  L7 economy, L8 crime, L9 information.
**Gate per rung:** headless assertion + one engine frame + one human sentence.

### P3 — VARIETY AT SCALE
- Port `rooms.build` + `dressing.dress` to run in-engine.
- Generate anonymous bays on approach; keep named places baked.
**Gate:** `--degeneracy` over a 1,000-bay sample; memory ceiling held.

### P4 — SURFACE, KIT-LEVEL ONLY
- Corridor, lift, transit car, drum ground, tree/building generators.
**Gate:** craft >= 4 at the rubric's half distance.

### P5 — SHIP
- Onboarding, controls config, accessibility, credits, IP statement.

## 4. RULES THAT SURVIVE
All of `CLAUDE.md`'s hard rules. Plus: every gate must be able to fail; a gate belongs
in the module that builds the thing; a fix applied to an instance and not the rule will
be needed again; a diff of two failed runs is not a pass.

## 5. THE NEW RULE THIS DRAFT PROPOSES
**NOTHING IS DONE UNTIL A HUMAN HAS SEEN IT RUN.** Every gate in this repository is an
agent marking its own homework. The single highest-value change available is a human
playing the build for twenty minutes, once per phase.
