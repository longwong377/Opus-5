# SHIP PLAN — one slice, played end to end

**Written session 4g, on the owner's instruction to override every plan in this repository, audit
them, and replace them.** This document supersedes the eight-layer plan in `CLAUDE.md`, the W-track
in `CLAUDE.md`, and `docs/MASTER-PLAN.md` §3's M0–M11 as the **ordering rule**. Those documents
remain as vocabulary and as the post-ship backlog. They are no longer what decides what to work on.

---

## PART 1 — THE AUDIT

### 1.0 The one fact that decides everything

    godot/project.godot:  run/main_scene = "res://scenes/exterior.tscn"
    exterior.tscn ext_resources:  render_shot.gd  +  9 materials  +  1 shader

`render_shot.gd` is a screenshot tool. **Every game script in the project — `walk.gd`,
`player.gd`, `hud.gd`, `dialogue.gd`, `npc.gd`, `interact.gd`, `door.gd`, `life.gd`, `ambience.gd`,
`arrival.gd`, `starfury.gd`, 7,534 lines — is unreachable from the scene the project ships.**
There is no build to hand anybody. Everything playable is launched by a developer typing a
`--glb=` path.

Not one of the four plan documents mentions this. That is the measure of how far the plans have
drifted from the thing being built.

### 1.1 There are four live plans and they contradict each other

| | plan | status |
|---|---|---|
| 1 | `CLAUDE.md` — layers 0–8, "one layer across all 118 before the next begins" | **demoted twice** (session 3u's W-track, session 4d's owner ruling) and still ~40% of `CLAUDE.md`, still reported on, still attracting work |
| 2 | `CLAUDE.md` — the W-track, W1–W6 | **W6 marked "THE WHOLE STATION"** on a coverage count that means 90 disconnected 40 m slices. Falsely green |
| 3 | `MASTER-PLAN` §3 — three tracks, M0–M11 | ordering **contradicts** plan 1, and `CLAUDE.md` records the contradiction as *"OPEN DECISION — the owner has not ruled"*. Never ruled. Both were followed at different times |
| 4 | `MASTER-PLAN` §0.5 — the two-day scope, five items | items **3 (environment & post) and 4 (NPC silhouette) not done**; and everything it explicitly excluded — arrival, dialogue, NPC schedules, Starfury, audio — **was built instead** |

A plan that is contradicted by the work done under it is not steering. It is commentary written
after the fact.

### 1.2 Eight defects, each with its measurement

**D1 — Every plan is a list of SUBSYSTEMS. None is a list of PLAYER MINUTES.**
Layers 0–8, W1–W6, M0–M11, the five-item two-day scope: all of them say *build X*. Not one says
*the player does A, then B, then C, for N minutes*. This is the root cause of D2 and D3 — nothing
in any plan ever required a path from a launch to a thing.

**D2 — There is no entry point.** §1.0. Two days from a deadline, the project cannot be started.

**D3 — "Done" has never meant "connected."** 2,630 of 8,113 GDScript lines have zero inbound
references from anywhere:

| script | lines | what it is | referenced by |
|---|---|---|---|
| `life.gd` | 917 | the station clock and the people who live by it — **and it `extends SceneTree`**, so it is a headless tool, not a runtime system | nothing |
| `ambience.gd` | 437 | all of layer 7's audio, 13 loop-exact WAVs, `audio.py` 100/100 | nothing |
| `starfury.gd` | 1,276 | the flyable Starfury | its own scene, which nothing references |

This is the **third** recurrence of a failure this repository has already written up twice —
`station/npc/`'s twelve modules with zero importers, and `npc/animation.py` with no importer. It
keeps happening because **every gate in the project is a module self-test, and a module self-test
passes whether or not anything calls it.**

**D4 — Coverage counts are the project's currency and every one is denominated wrong.**

| the number reported | what it actually means |
|---|---|
| 128 of 128 locations | 90 disconnected 40 m z-clusters; no build contains two of them |
| layer 2b: 123 / 128 | `--machinery` on the same content reads **74 / 78** |
| the station is walkable | one 40 m slice at a time, launched by command line |
| 250,000 residents | **2,028 bodies placed**; 250,000 is a density used to derive crowd counts |
| the whole station | **0.17%** of its own declared footprint — 73,635 bays wanted, 128 built |

Every one of those is technically true. Not one is the number a player experiences.

**D5 — The scope is arithmetically impossible and no document says so.** One 70-minute agent
session raised four landmarks from craft 1 to craft 2–3. At that rate the 12 "hero" locations of
`MASTER-PLAN` §3.4 alone are three sessions, the 30 "featured" are eight more, and 128 locations is
not a number that closes. The tiering in §3.4 is the only honest attempt at this arithmetic in the
repository and it still assumes all 126 get finished.

**D6 — Performance is planned LAST and is already failing.** `budget.py` is red at 2.05× its
structure allowance. The three remedies — occlusion culling, LOD, streaming — appear in **no
milestone of any plan**. M11 says *"performance measured on target hardware"* and it is the last
milestone. The plan discovers it cannot run on the final day.

**D7 — There is more prose about this project than there is game.** 100,349 lines of Python,
18,557 lines of markdown in `docs/` and `canon/`, **8,113 lines of GDScript**. The documentation is
2.3× the game code. The plan documents have themselves become a workload.

**D8 — Nothing anywhere defines what the player DOES.** `MASTER-PLAN` §4.11 is titled
*"The thing nobody plans for: what does the player DO?"* — a section that names the gap instead of
closing it, and has been in the document unanswered ever since.

### 1.3 What the audit does NOT say

The work is not bad and most of it is not wasted. The generators, the canon discipline, the
measured-not-authored rule, the negative controls, the material library, the audio derivation, the
NPC wardrobe — all of it is real and much of it is excellent. **The defect is entirely in the
ordering.** A very large amount of high-quality machinery has been built behind a door that was
never opened.

---

## PART 2 — THE NEW COURSE

### 2.1 The deliverable, and it is the only one

> **"First Night on Babylon 5" — one continuous playable slice, about twenty minutes, launched
> from a title screen with no command line.**

Chosen for one reason: **every beat of it already exists as a module.** The work is joining, not
building. It is the smallest number of moves that converts this repository from the owner's own
verdict — *"a world generator and not yet a game"* — into a game.

### 2.2 The slice, beat by beat

| # | Beat | What already exists | What is missing |
|---|---|---|---|
| **1** | Title → New Game | nothing | a main scene, ~60 lines |
| **2** | Arrival: the transport approaches, docks, you are processed at customs | `arrival.gd` 592 lines, `arrival.tscn`, `customs.py` 51/51, craft 3 | reachable from beat 1 |
| **3** | Walk the concourse into the Zocalo | `walk.gd` 832, `player.gd`, `interior.axial_run` + `collision.axial_shell` (4g), Zocalo at craft 3 | one continuous mesh along the path |
| **4** | The station is alive: clock runs, crowds move on their schedules | `life.gd` 917 lines, `populace`, `schedule` | **wire it** — it is a headless tool today |
| **5** | You can hear it | `ambience.gd` 437, 13 WAVs, `audio.py` 100/100, seven derived layers | **wire it** — zero references today |
| **6** | Someone talks back | `dialogue.gd` 912, already wired to `walk.gd` | dialogue content for the slice's cast |
| **7** | Use something that responds | `interact.gd` 574, **357/357** interactables resolve, 5 verbs respond | nothing |
| **8** | Your quarters — a door with your name on it | `rooms.py` quarters, `populace` residents with homes | a residence assignment for the player |
| **S** | *Stretch:* fly out of the bay you arrived in | `starfury.gd` 1,276 | a hand-off from walking to flight |

Beats 1–8 are the ship target. **S ships only if 1–8 are done and gated.**

### 2.3 Four new gates — and why this overrides "no new gates"

Session 4d's ruling was **"keep the existing gates green, do not grow them"**, and it was right,
because the gates being added then were *coverage* gates — counting things that exist. These four
are **integration** gates: they measure whether the parts are joined. They exist precisely because
36 module self-tests are green on a build nobody can start.

Every one of them **fails today**, which is the test of whether a gate is real.

| | gate | asserts | fails today because |
|---|---|---|---|
| **G1** | **COLD START** | launch the shipped `main_scene` with no arguments; a player is standing, in-game, with a HUD, inside N seconds | there is no main scene — `exterior.tscn` is a screenshot tool |
| **G2** | **THE SLICE RUNS** | a scripted headless playthrough executes all eight beats and asserts each one landed | it stops at beat 1 |
| **G3** | **NOTHING IS UNREACHABLE** | static reachability over `godot/scripts/*.gd` from `main_scene`; any game script with zero inbound references fails the gate | **11 scripts, 7,534 lines** |
| **G4** | **THE SLICE'S FRAME** | triangles, draw calls and instance counts measured at the eye positions the slice actually visits | never measured; `budget.py` sweeps a synthetic lattice on a deck the slice does not walk |

`budget.py`'s existing sweep stays, as a **report**. G4 is the gate.

### 2.4 The order of work, by risk

**Day 1, first half — the front door, and the resurrection of 1,354 dead lines.**
G1 and G3. A title scene; New Game; hand off to `arrival.gd`; hand off to `walk.gd`. Wire `life.gd`
(re-cast from `SceneTree` to a runtime node) and `ambience.gd`. **This is the highest value per hour
available anywhere in the project**: the station acquires a clock, a crowd that moves, and sound,
all of it already built and tested, and the project acquires a front door.

**Day 1, second half — G2: the slice runs end to end, headless.**
Beats 2, 3, 6, 7, 8. Where a beat cannot be made to run, **cut the beat and say which** — do not
fake it. A twenty-minute slice with six honest beats beats eight beats where two are a cutscene.

**Day 2, first half — the look, which is what the owner actually complained about.**
This is items 3 and 4 of the two-day scope that were written and never done:
* **Environment and post**, re-derived on the real renderer. The previous grading was tuned under
  OpenGL 3 Compatibility, where `adjustment_*`, SSIL, volumetric fog and glow **do not exist**.
  Every one of those numbers is unvalidated.
* **The people stop being blobs.** Heads, hands and hair as geometry. Skin, cloth and hair maps are
  already in; the failure is silhouette.

Scoped to the slice's path only. Nothing else is lit or dressed.

**Day 2, second half — G4, then the build.**
Occlusion is the lever and it is half built (`station/occluders.py`, red at 6/7, diagnosis in
`STATE.md` §18.3). **Two hours, hard stop.** If it does not close, cut the draw distance along the
slice instead and record that that is what was done. Then package, one final playthrough, record it.

### 2.5 What is explicitly OUT, in writing

Naming this is half the plan, because everything below is what has consumed the last ten sessions.

* streaming, and therefore the 8 km walk
* the ~120 locations the slice does not walk through
* layers 5–8 as coverage exercises; milestones M4, M6, M7, M9, M10, M11
* 250,000 NPCs; the economy; law and crime; ISN; the black market; the factions acting
* the drum, the garden, the alien sector, the Starfury's combat envelope
* every craft score on a location the slice does not visit
* `budget.py`'s whole-station red — it stays red, it is honest, and G4 replaces it as the gate

### 2.6 What will be true at the deadline — stated now so it cannot be spun later

* **A single build, launched from a title screen**, in which a player arrives on Babylon 5, is
  processed through customs, walks a corridor into the Zocalo, hears the station around them, talks
  to someone who answers, uses something that responds, and finds the door to their own quarters.
  About twenty minutes.
* **It will be one sector and one deck.** Not 8 km. Not 128 locations.
* **Craft will be 3 on the Zocalo and 2–3 along the path.** The rest of the station will be exactly
  as it is now.
* **The frame will be inside budget along the slice's path only**, measured by G4, and the
  whole-station number will still be red.

That is a demo, not a game, and it is the largest true thing available in the time. Everything else
in this repository is groundwork for the version after it.

### 2.7 The five permanent changes to how this project plans

1. **The eight-layer plan is struck as an ordering rule.** Its layer *definitions* survive as
   vocabulary for describing one location's state. The table of counts does not.
2. **The W-track is closed, and W6 is marked FALSE.** "Roll W3–W5 outward across the 128" was
   satisfied by a coverage count and is not true.
3. **`MASTER-PLAN` M0–M11 becomes the post-ship backlog.** It is a good document about the eventual
   game. It is not a two-day plan and pretending otherwise is what produced four contradictory plans.
4. **A plan item is a player minute, not a subsystem.** Anything phrased *"build X"* is rewritten as
   *"the player does Y"* or it does not go in the plan.
5. **A module is not done until something reachable from `main_scene` calls it.** G3 enforces this,
   and it is the single rule that would have prevented D3 all three times it has now happened.
