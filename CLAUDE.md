# Babylon 5 Station Simulation — Working Agreement

Read this first, every session. The owner is hands-off until ship; nobody else is checking
this work. The repository is the only memory that survives a context reset.

## What this is

A 1:1-scale, canon-accurate, real-time simulation of the Babylon 5 station. 8,047 m.
First and third person. Interior and exterior generated from **one** authoritative model so
they can never disagree. Flyable Starfury with seamless launch and dock. NPCs with names,
species, roles and schedules. Era lock: **Season 2–3**.

## Scope — what "the whole station" means

Set by the owner in session 3c and binding on everything below. The simulation must contain
**every point of interest and location from the show, in the right place**, and must be a living
thing rather than a building:

- NPCs with quarters, jobs, schedules and events — not crowds, *residents*
- transports and visitors arriving and departing continuously; the jump gate working
- customs and immigration, law enforcement, crime, the black market, Downbelow's underclass
- every major faction present, with the friction between them visible in a corridor
- the physical plant that makes 250,000 people possible: food, water, air, power, waste
- an information layer the player can use — comms, ISN, propaganda, signage, announcements
- *"the simulation exists around you rather than in text"*

`docs/gazetteer/` is where that scope is enumerated and sourced. Nothing is considered complete
while a gazetteer entry for it is unbuilt.

## The standard

The owner set it explicitly in session 2y: *"utterly perfect, visually beautiful, with every
single thing done at AAA quality — from textures to physics to detail to the npcs to the
crowdedness/isolation to the mood to the ambiance to the alienness to the sound to the scale to
the interactability to the accuracy vs the real thing. This is your magnus opus."*

That is a feeling, and a feeling cannot be reviewed by an agent. `docs/AAA-STANDARD.md` turns it
into four scored dimensions with written descriptors — **craft, fidelity, performance,
robustness** — and defines the bar. Nothing is "done" because it was built; it is done when it
clears the bar and stops regressing.

## START HERE — THE READ ORDER, AND WHAT SUPERSEDES WHAT (session 4j)

**Everything below this section is HISTORY. Its lessons still bind; its orderings do
not.** This project has accumulated five plan documents across many sessions, and a
future context that reads them in file order will act on a ruling that was replaced three
sessions ago. So the hierarchy is stated once, here, in the file every session reads
first:

| # | read | it decides | status |
|---|---|---|---|
| 1 | **`docs/THE-STATION.md`** + its annexes `docs/spec/{PLACES,PEOPLE,SYSTEMS}.md` | **WHAT gets built** — 291 enumerated, checkable items with acceptance checks that name content | **CURRENT — the content authority** |
| 2 | **`docs/MASTER-PLAN.md`** § "SESSION 4i — FINAL" | **WHAT ORDER** it gets built in — phases, gates, the enforcement rules | **CURRENT — the ordering authority** |
| 2b | **`docs/MASTER-PLAN.md`** § "SESSION 4r — THE OPEN DEFECT LIST" (**R1–R6**, immediately above the 4i section) | **WHAT IS BROKEN RIGHT NOW** — five defects, each with an owner, a gate that can fail, and an acceptance test that names content | **CURRENT — read before choosing a session's work** |
| 3 | `docs/AAA-STANDARD.md` | the quality bar and **the hard stop** (3 rounds, then CAPPED in writing) | **CURRENT — the quality authority** |
| 4 | `STATE.md` | where the last session stopped and what is half-finished | **CURRENT — the handoff** |
| 5 | `canon/00-MASTER.md`, `INVENTIONS.md`, `CONFLICTS.md` | what is true, what is extrapolated, what is blocked | **CURRENT — the fact authority** |

**The spec is the gate input.** `python3 tools/spec_registry.py` regenerates
`docs/spec/completion.yaml` from the annexes and refuses to emit around any ambiguity;
`python3 station/spec_check.py --smoke` reports the honest GREEN/RED ledger. Both run in
CI as `sspec_gate`. **No statistic may substitute for a spec item.**

### THE LIVE NUMBERS — everything below the START HERE section is history, including its figures

**Read these before quoting any number from further down this file.** The sections below are
kept as history deliberately and their numbers were true when written; several are not true now,
and a session that acts on a historic figure acts on a stale one. Measured as of session 4o:

| | live | where a stale one appears below |
|---|---|---|
| places in the register | **129** (`markab_quarter` added, PLC-129) | "118 locations", "126 locations", "128 of 128" |
| gazetteer rows | **137** | "126 locations" |
| bay tiling total | **51,475** (blue 7,692 / red 1,644 / green 7,062 / grey 16,487 / yellow 18,590) | "49,265", "73,635" |
| spec registry | **300 rows**, PLC 129 · INC 30 | "291 rows", "193 registry rows", "22 classes" |
| `canon/INVENTIONS.md` | reaches **INV-384** | — |
| frame structure vs budget | **4.34×** (260,243 tri against a 60,000 allowance) — **NEEDS RE-MEASURING as of 4r, see below** | **"2.05×" — stale by two sessions**; it predates 4k's footprint tiling, which multiplied deck triangles 3.34× |
| incident classes | **30**, 2,011 incidents a station-day | "22 classes" |
| places outside the pressure hull | **0** of 129 (was 34; control `--hull-fit --legacy` fails at 41) | — |
| spec ledger | **0 GREEN / 300 RED**, of which 129 have a verified address and 171 nothing at all | — |
| craft, 22 scored subsystems | one at **4**, thirteen at **3**, five at **2**, three at **1** | — |
| Python : GDScript | **166,034 : 23,823 ≈ 7:1** (was 26:1 at the 4d ruling) | "26:1" |

**A CONSEQUENCE OWED FROM 4r, NAMED RATHER THAN GUESSED.** The z-aware rebuild took the station's
deck geometry from **29.4 M triangles to 13.1 M** (2,616 → **1,150 per built metre**) because 59
places resolved to the radius the hull actually leaves them. Every triangle-budget figure measured
before that is therefore suspect, including the **4.34×** in the row above. I have NOT substituted
a new number: the honest one comes from `python3 station/budget.py`, which is minutes of full CPU
and must not run while agents do. **Re-measure it before quoting it** — and note that the direction
is favourable, which is exactly when a stale figure survives longest, because nobody re-checks a
number that is only going to improve.

**And one live claim that is easy to misread as a win:** the corridor occluder is built, provably
contained (0 breaches of 2,880 rays) and reaches the engine — and it is worth **7.8% of the frame
and 0.2% of structure**, because Godot culls per instance AABB and the corridor's OBJ groups span
the whole 345° ring. The 58.2% figure in its own report is the per-triangle ceiling and **no
renderer here does that**. What actually closes the budget red is spatial submission — per-cell
instances, measured at **39% before any occluder**.

### THE DEFECT THIS PROJECT KEEPS PRODUCING — nine instances, and now a gate

**Finished, tested machinery with no caller on the shipped path.** It has happened nine times:
L3's room leg, `stream.gd` moving nobody, a circulation graph nothing but its own selftest saw,
`dialogue.gd`'s node that had never been built on any path, the Starfury's un-rebuilt data,
`--mode=transit`'s manifest that nothing wrote, `Director.route_between` with `nav` unset,
`occluders.py` with no importer, and — created **while closing the eighth** — the occluder load
placed in `walk.gd::_load_level`, **which the shipped build never runs**, because the shipped
scene is STREAMED and `_load_level` is the monolithic path.

Every one passed every gate at the time, and they had to: **every gate here scores a PART against
a standard, and a part with no caller still meets its standard.**

`python3 tools/wiring.py --selftest` asks the rule's question instead — does every
`station/generated/…` path an engine script reads exist and get rebuilt by CI, and does anything
import each tested module. Seconds, no build, no GPU, safe to run while agents work. CI step
`swiring`. **Run it before claiming anything is wired.**

**But know its ceiling, because the ninth instance slipped under it.**
`budget.occlusion_chain` reported `applied=True` while the shipped build loaded nothing, because
it looks for a **reference in the source** and cannot see which branch runs. One level lower,
`boot.json` had no key and `main.gd` passed none, so the export var would have stayed empty even
on the path that did call it. **A static scan can tell you a caller exists; only running the thing
tells you the caller runs.** Launch the scene and grep for the line the loader prints.

### The supersession ledger — nothing is lost, everything is placed

| document | status | what STILL binds from it |
|---|---|---|
| `docs/THE-STATION.md` + `docs/spec/*` | **CURRENT** | all of it — the content spec |
| `docs/MASTER-PLAN.md` (4i FINAL section) | **CURRENT** | all of it — phases, gates, the four anti-failure mechanisms |
| `docs/MASTER-PLAN.md` (4h body, below the 4i section) | superseded as ordering | the **LIFE-FIRST ruling** and its reasoning; the 60/30/10 effort split **within** tracks; "a generator is finished when its output is VARIOUS, not when it is correct" |
| `docs/MASTER-PLAN-3k.md` | superseded | its **audit** is still the best analysis in the repo — read it for diagnosis, never for ordering |
| `docs/SHIP-PLAN.md` | superseded, work finished | the record of *why* four contradictory plans had to be collapsed; its connectivity work is done |
| `docs/PLAN-3u-populated.md` | superseded | **"the build is always walkable"** — still a hard rule |
| `docs/MASTER-PLAN-DRAFT-4i.md` | **REJECTED, kept deliberately** | nothing binds. It exists only so `docs/reviews/bible-panel-4j.md`'s critique is legible against its target. **Do not build from it.** |
| the eight-layer table (in this file, below) | superseded as ordering | the **lessons**: layer 2's "a cube passes every word of a topological test", layer 4's "a median cannot express mood" |
| the W-track (in this file, below) | superseded as ordering | collision ≠ render geometry; a walk gate reports **distance covered** |
| the 4d ruling (in this file, below) | superseded by 4i | "the project optimises what can be counted, because counts go green and a game cannot be expressed as a count" |

**If you are about to act on a ruling from a section below and it is not in the "still
binds" column, stop and read §1–2 above instead.**

**A new plan document may not be created.** Amend `docs/MASTER-PLAN.md` with a dated
section, as 4i did. A fifth plan this file does not point at would be read *after* the
old rulings by every future context — which is the same defect as a gate that does not
run, at plan scale. `tools/doc_chain.py` asserts in CI that every plan-shaped document in
`docs/` appears in the ledger above, so a new one cannot appear unplaced.

## THE OWNER'S RULING, SESSION 4d — IT IS A WORLD GENERATOR AND NOT YET A GAME

**Read this before the plan below. It changes what to work on.**

The owner asked what actually works. The answer, measured rather than summarised: NPCs have
lives, jobs and species-specific sleep and meals **as data** and none of it runs at runtime;
there is **no dialogue system anywhere**; **no HUD, menu, map or inventory** — the only UI in
the project is the text `[E] operate the …`; **no flyable Starfury** (zero references in any
`.gd` or `.tscn`, though a flight model and a mesh both exist); **no audio at all**; no player
residence, no arrival sequence, no character creation; factions decide who is in a room and
what they wear and otherwise do not act. There are **~2,028 bodies** placed, not 250,000 —
that figure is a *density* used to derive crowd counts.

**One number explains it: 85,940 lines of Python against 3,291 of GDScript.** 26:1. This is not
shallow work, it is very deep work in one dimension. **The project has been optimising what can
be counted, because counts go green and a game cannot be expressed as a count.** Every gate in
this file measures coverage of a thing that already exists; none of them can fail for "there is
no reason to be here".

**The ruling:**

1. **Build the player's experience, not more coverage.** Arrival and processing, a residence, a
   HUD, someone who talks back, ambient sound, a flyable Starfury. In that spirit, not that
   exact order.
2. **Keep the existing gates green. Do not grow them.** No new coverage gates, no new layer
   numbers, no new scored dimensions. The ones that exist stay passing so nothing rots.
3. The layer table and the W-track below remain accurate descriptions of the shell. They are
   **no longer the priority ordering.**

## THE PLAN — A PLAYABLE BUILD AT ALL TIMES

**Set by the owner, session 3u, and it REPLACES the layer plan below as the ordering rule.**

The owner's words: *"how is it possible that we've come this far and we still do not have a walkable
ship? that's the entire fucking point."* They are right, and the cause was structural rather than
careless, so the fix has to be structural too.

### Why the layer plan produced nothing playable, mechanically

The layer rule was "one layer at a time across all 118 locations, finished before the next begins".
That is **eight horizontal slices**. A horizontal slice cannot be walked in. Under that rule the
first moment a player could stand up is *after the last layer of the last location* — so at every
point before the very end, and by construction, there is no build. Four layers came back COMPLETE
and the result was an empty shell nobody could enter.

It was adopted for a good reason — session 3k's "layers but complete, rather than small slices which
do not add up together" — and applied too literally. The cure for slices that do not add up is
**slices that DO add up**, not the abolition of slices.

### Why no gate caught it

Every gate in this repository measures **a part in isolation**: `density.py` scores one module's line
density, `measure_frame.py` scores one image, `directory.py` counts locations per layer,
`budget.py` counts triangles. **Not one of them asks whether a player can walk from A to B.** 118
locations could each pass all eight layers and still be 118 disconnected boxes with no floor
collision — which is exactly what they were. As of session 3u the string `CollisionShape` appeared
**nowhere in the project**. There was no floor to stand on, and no assertion could fail for its
absence.

### The rule that replaces the layer rule

1. **THE BUILD IS ALWAYS WALKABLE.** Every session ends with a build a player can launch and walk
   in. If a change would break that, it is not landed until it does not.
2. **Integration is a gate, not a phase.** `station/walkable.py` asserts the player can spawn, stand,
   walk, and reach the neighbouring location. It runs in CI. It must be able to fail — and when it
   was written it *did* fail, on everything.
3. **Depth before breadth, in the places the player actually goes.** One corridor furnished to
   Starfield density beats 118 articulated empty rooms. Breadth is what generators are for and it
   comes after the loop closes.
4. **A layer number is not progress.** Progress is what a player can do. "Layers 1-4 complete"
   described an empty shell and read like half a game. Report what works, not what scores.
5. **Props and inhabitants are not polish.** They are most of the remaining product. Measured in 3u:
   across the 68 procedural rooms the split is **95.9% architecture, 1.7% fixtures, 2.5% props** --
   311 prop instances in the whole station, about 4.5 per room, and zero NPCs anywhere.

### The order of work, and it is vertical

| # | Milestone | Done when | Status |
|---|---|---|---|
| **W1** | **Stand up** | Collision on the station mesh, a character controller, per-deck gravity. A player spawns in the corridor kit and walks. Asserted headlessly | **DONE** (3v) |
| **W2** | **Go somewhere** | Two named locations joined by real walkable geometry; the player walks between them without leaving the floor | **DONE** (3v) — 126 m of corridor walked, `offfloor=0/1800`, and a body walks through a door into a named room |
| **W3** | **A furnished room** | ONE location at true prop density -- the reference is the owner's Starfield frames, not our own past work -- with a stated props/m2 | **DONE** (3z) -- and on every room, not one: `dressing.py` measures **4.00 props/m2** in an office and quarters, **6.68** in commerce, **6.37** in hospitality. 3u measured the station at **4.5 prop instances per room** total. **THOSE THREE BRACKETS ARE STALE AS OF 4k** -- re-running `dressing.stats` today gives office **9.88**, commerce **7.71**, hospitality **5.92**, so a room judged against the old numbers is judged against a bar the station has already passed. Re-measure before quoting them |
| **W4** | **A populated room** | NPCs standing, sitting and walking in it. `station/npc/` already has twelve tested modules with zero importers; wire them | **DONE** (3z) -- all three poses, and they are POSES: `npc/animation.py` finally has an importer, so a sitter is `sit_clip` on the seat's own measured height rather than a standing body dropped 0.42 m, and a corridor walker is `walk_clip` at a per-resident phase. **963 walking in corridors, 449 in rooms** across the sweep |
| **W5** | **The loop** | Spawn -> walk -> use something -> an NPC reacts. The smallest complete experience | **DONE** (3z) -- and `walkable.py --deck blue/0/0` reports all four in one line: *"a body spawns in the corridor and WALKS INTO docking_bays (6.3 m -> 0.04 m), never leaving the floor, **7 of the room look up** (123 deg turned, 4 deg off)"*, with the control *"with the doors inert the body is stopped 5.26 m short"* |
| **W6+** | **Breadth** | Roll W3-W5 outward by generator across the 128, in the order a player meets them | **THE WHOLE STATION** (3z) -- `deck.py --sweep`: **90 z-clusters assemble, 0 fail, 128 of 128 locations on an assembled cluster, 128 with a door or on ground, 0 floor holes.** 58,660 collision triangles across the ring decks + 573,440 in the drum's ground = **632,100** for the walkable station. What remains is DEPTH: 49 module-owned places still assemble as generic bays, 18 with a builder that exists |

**AND IT ANSWERS IT PER LOCATION, NOT PER SQUARE METRE.** Session 4e measured the other half:
`rooms.bay_span_m` builds ONE REPRESENTATIVE BAY and its own docstring says *"the full location is
then that bay instanced along its footprint"* -- and **nothing instanced it**. The sweep's 128 of
128 was true and it was a count of locations REACHED, not of location BUILT.

**CLOSED IN 4k, AND THE NUMBERS BELOW SUPERSEDE 4e's AND STATE.md section 13's.** `rooms.tiling`
instances the bay along the footprint, gated by `python3 station/rooms.py --footprint` (CI step
`sfootprint`):

| | before | after |
|---|---|---|
| the 91 places `rooms.py` builds | **926 m of 14,868 m (6.2%)** | **8,014 m (53.9%)**, 77 at full footprint, 14 capped by budget |
| `docking_bays` | **10.77 m** of its 140 m | **140.0 m**, render and collision agreeing, 70/70 floor probes |
| triangles over the 128 | 5,883,720 | 19,633,996 -- **3.34x for 8.7x the metres** |
| **triangles per built metre** | 6,354 | **2,450** |

Three of 4e's own figures were wrong and are corrected here: **the wanted total is 51,465, not
73,635** (`bays_in` truncates `13.000000000000002` to 12, so it under-counts a whole bay on most of
the station -- left alone because that total is frozen normative in `docs/spec/PLACES.md` §TILING,
and `bays_along()` is the new one that rounds); `docking_bays` built **10.77 m, not 15.5 m** (15.5
predated `_fit_bay`); and the one clamp that caused all of it was a single `min(l_full, bl)` --
every loop below it already scaled correctly.

**The gate can fail and is shown failing:** `--footprint --legacy` rebuilds one bay per place and
reports **84 of 128 mesh short of plan, 926 m of 14,868 m**. It also asserts that **no two bays of
a place hash identically** -- `deck.py --degeneracy`'s question one level down -- so a tiled room
cannot pass by being a tile pattern.

**AND IT COST BUILD TIME, WHICH IS NOT FREE:** `rooms.py` is now 13m03s and `--footprint` is
**23m06s**. A twenty-minute CI gate is a liability; profile before adding to it.

**IT WAS PROFILED, AND IT IS CONTENT COST RATHER THAN A BUG** — which this file's own rule
("a slow suite is a bug until profiled") demands be checked and which it is worth recording as
a NEGATIVE result. One `docking_bays` build is **~9.3 s** for 269,688 triangles, and 128 places
at that rate is the twenty minutes. There is no cache-key defect of the session-4c kind here.

**AND THE PROFILE LIED ABOUT WHERE THE TIME WENT, which is the transferable part.** `cProfile`
reported the same build at **34.4 s** with `interior.ring_radii` at 6.5 s over 539 calls — but
the workload makes **28 million function calls**, and cProfile's per-call overhead is most of
the difference. Acting on that attribution, an `id()`-keyed cache on `ring_radii` measured
**×3.8 faster**, then **×1.92**, then — run in a *fresh process each way, alternating* —
**nothing at all: 9.2/9.3 s without it against 9.3/9.7 s with it.** The first number was
profiler overhead; the second was a second run riding caches the first had warmed. The cache
was reverted.

*On a call-heavy workload, use wall-clock in a cold process as the arbiter and `cProfile` only
to generate hypotheses. And an A/B of two runs in one process is not an A/B: the second one
inherits every memo the first one filled.*

**`python3 station/deck.py --sweep` is the answer to "how much of the station can I walk in".**
It is the only gate here that asks a whole-station question; every other one measures a part.
Run it before claiming coverage. As of 3z it is **128 of 128** — every location in the register
is on an assembled cluster and every one has a door or stands on the drum's ground. It also
reports **how many people are in the corridors** (963, against 449 in the rooms), which is the
only place the derived crowd density can be checked against the 250,000 it comes from.

The two things that used to make this number a lie are both closed and worth remembering. It
once read **99 of 118** because it built `z_clusters(...)[0]` alone — a "deck" in the gazetteer
is not a z-slice, and Blue ring 0 deck 0 holds sixteen locations over 1,100 m of axis. And in 3z
every **single-room** cluster on the station turned out to be sealed: `deck_plan` stopped its
phase sweep at the first arrangement with no unopened room, which on a one-room cluster is the
first one tried, leaving the door up to 1.33 m off centre where a body walking straight at it
meets the jamb. The sweep said 118/118 throughout. **A coverage count is not a walk test.**

**THE DRUM INVERTS THE COLLISION RULE, and that is not an exception to it.** A corridor needs a
*smooth* shell because its 66 mm channel and 22 mm tiles are decoration a foot should not feel.
The drum needs the *shape of its own ground*, because there the relief IS the content —
flattening a 7 m settlement podium onto a 4 m lake bed leaves a player hovering over the fields
and buried in the town. `station/drum_walk.py` therefore authors no terrain: it calls
`drum_ground.ground_patch`, the same function the render ground is built from. **And its gate is
SLOPE, not lip** — `collision.floor_steps` is right on a flat corridor and would fail a correct
hill, because the drum rises 0.24 m between lattice points, which is 3.5°, which is a field.
What a character controller actually tests is rise over run against `floor_max_angle`.

**Props are solid** as of 3v — `collision.prop_boxes` derives them from the room's own emitted
mesh, so there is no second list to drift. A player no longer walks through tables.

**A DOORWAY IS THE PLACE A PLAYER LOOKS CLOSEST, AND IT CARRIED FOUR DEFECTS AT ONCE.** Session
3x, and the pattern is worth more than the fix. `judge-3w` measured 1,470 open boundary edges in
one deck's corridor and called every door aperture an unclosed cut; it was right about the count
and the cause was four things stacked:

1. `door_assembly` merged its three pieces with **no `tag()` block**, so 1,248 triangles a deck
   matched no material rule and took no light — the surface you look straight at, unmaterialled.
2. `_plate_with_hole` rimmed the **loops the caller passed in**, which know nothing about the
   split points `_polygon_difference` lands partway along an edge. It now rims from the pieces'
   own boundary, so the rim inherits whatever subdivision the peel produced.
3. `portal_frame` was five prisms **sharing coincident faces** — 828 non-manifold edges a deck,
   at the corner a player passes 414 times a lap. Rebuilt through the same machinery: 8,832
   *fewer* triangles, because coincident faces are geometry nobody can see.
4. `dressing._cyl` was open at the bottom **and wound 0/24 outward** — an object you look
   straight through.

**Deck open edges: 1,572 → 0.** Every fix has a negative control that fires.

**And the reason none of it was caught is one sentence: every gate measured the case without the
defect in it.** `interior_kit`'s tag-coverage assertion ran on a corridor with **no doors**. Its
closure gate **cast rays upward**, which cannot see a hole in a vertical surface beside the
corridor. `boundary_edges` — the only measurement that finds this at all, because a hole shows
the background and the background is black — lived in `interior`, which *imports* the kit, so the
module that builds the pieces had no way to measure them. It now lives in `interior_kit`.

**A gate belongs in the module that builds the thing, and it must build the hard case.**

**A NAME BUILT BY STRING INTERPOLATION IS INVISIBLE TO A REGEX OVER SOURCE.** Session 4f, and it is
mine. `materials._scan_generator_groups` finds every mesh group a builder emits by scanning source
for string LITERALS -- which works for the 68 generic rooms and misses anything named at run time.
`station/corridor_dressing.py` names its clutter `f"dress_{kind}"` from `SCHEMES` x
`dressing.MACHINES`, so **45 groups were on the fallback material and the coverage scan could not
see one of them**: 19 of the 22 `dressing.MACHINES` kinds had no bind at all, plus 26 of
`rooms.PROPS`' 99 names, reachable only since 4d let bespoke rooms place their declared props.

The fix is not a better regex. `check_material_coverage()` now runs in `export_scene.build()` --
**one call site every shot passes through** -- and also against a 193-name vocabulary DERIVED from
`rooms.FIXTURES`/`PLACE_FIXTURES`/`PROPS` x `dressing.MACHINES`, so it can fail without a built
deck. A gate that needs `scene/deck/*` would be a gate reading an artefact it cannot rebuild.

**AND THE FRAME THE DEFECT WAS FOUND IN DID NOT SHOW IT.** At the judge's own `--at docking_bays`
camera the before/after is **0.000% different** -- `render_shot.gd` reports every group in the
SCENE, not the SHOT, and the nearest affected cluster was 7.4 m behind that eye. Which is exactly
why the gate has to be about the group list and not about a picture.

**A DEFAULT NOBODY CHOSE IS NOT THE SAME AS A DEFECT, and the reviewer got one of these wrong.**
judge-4e reported 9 hull groups rendering as "smooth plastic". Binding them produced a
**byte-identical** exterior frame -- md5 unchanged -- because `exterior.tscn` sets
`fallback_material = m_hull`. The real fault was subtler and still worth fixing: nine surfaces
followed a default nobody had chosen, and `materials._selftest` asserted that default AS a
decision (`hull_exterior.binds == ()`), so the check could only fail if somebody fixed it.

**A GATE THAT DOES NOT RUN IS NOT A GATE, AND A RED BUILD CAN HIDE THIRTY-FOUR OF THEM.** Session
4e's judge found it: `.github/workflows/validate.yml` was 41 sequential steps with no
`continue-on-error` anywhere, and step 4 -- `Performance budgets` -- fails BY DESIGN, because
`budget.py` is honestly over budget. **So the 34 steps after it never executed**, including *The
station is walkable*, *How much of the station can be walked in*, *The habitat drum is walkable*,
*Canon assertions* and *NPC bodies*. All 30 most recent runs were red and none had ever reported
those answers. This file said `walkable.py` "runs in CI"; it had not, for thirty pushes.

The fix is NOT to make the failing gate pass -- that is picking the convenient reading. It is that
one failing gate must not blind every gate behind it: each step records its own outcome and a
final step fails the job if any did. The build stays exactly as red and the other 34 answers
become visible. **When a suite is a chain, its length is a liability; check what your CI actually
executed, not what it contains.**

**A REVIEWER MUST OWN ITS OWN FILES, AND `git add -A` IS NOT DISJOINT.** The same session: while a
judge agent was working, the main agent ran `git add -A` and swept all 25 of its untracked files
into an unrelated commit mid-write -- including a scorecard that still had four gate errors. File
lists were disjoint; the staging command was not. **Stage the paths you changed.**

**A TOOL THAT SILENTLY DEGRADES AND EXITS 0 IS WORSE THAN ONE THAT FAILS — IT MANUFACTURES
EVIDENCE.** Session 4e, and it cost a session of visual judgement. The container had no Vulkan
ICD, so every `render_godot.sh` run fell back to **OpenGL 3 Compatibility** — which has no
Forward+, therefore no SSAO, glow, SSIL, volumetric fog or colour grading — printed a warning
inside several hundred lines of ALSA noise, and **exited 0 with a PNG**. Ten frames were judged
through it, two were shown to the owner, and an A/B of `ssil_enabled` came back byte-identical
and was written down as *"Mesa lavapipe does not run it"*. On the real renderer SSIL moves **86%
of the pixels**.

This is the same defect as the stale committed frames that `--gate-frames` could not rebuild, one
level down: the frame was fresh and the **renderer** was stale. The fix has two ends because
either alone can be defeated — check the precondition before, and grep the tool's own report of
what it did after, and destroy the artefact if it disagrees. **Any tool that can substitute a
lesser mode for the one asked for must say which one it used, in its output, on every run.**

**A GATE THAT SCORES N THINGS MUST ALSO ASK WHETHER THE N THINGS ARE THE SAME THING.** Session
4h, and it is the most expensive blind spot this project has had, because it is the one the owner
found rather than a gate. Every gate here measures **a part against a standard**: articulation asks
"is this room's line density above its floor", materials asks "does every group carry PBR",
lighting compares a histogram to a reference, props asks "do the declared interactables exist".
**Two identical rooms pass all four, and a layer-completion count therefore goes green on a station
of 128 identical rooms.** The only pairwise comparison that existed anywhere before 4h was
`npc/body.py --silhouette`, and it compares **species**, not places.

`deck.py --degeneracy` is the cheap universal form and it asks **identity, not similarity** — no
raster, no threshold, no cache, nothing to tune, and therefore nothing to argue with. Two places
whose geometry hashes the same *are* one place. `variety.py` measures the *degree*; this catches the
degenerate case for the price of a hash and can run whenever the station builds.

**And it immediately falsified a claim its own author had just made, which is what a real gate is
for.** Two places had been reported as "the same room" on the evidence of two byte-identical
renders (same md5, 0 of 360,000 pixels different). The gate said **128 places, 128 distinct
geometries**. Both were true: the places differ on the deck a player walks, and the **interior
render path** collapsed them, because `bespoke.BESPOKE_GEOMETRY[module]` is handed the place as
`q` and several entries drop it — `"customs": lambda s, p, q: customs.hall(s, p)`. A frame showed
the module's one generic hall. **A thing is built more than once in this project, and a gate on one
build path says nothing about the other.**

**The deepest part of it: that exact bug had already been found and fixed TWICE**, for `quarters`
(*"rendering one class seven times would be seven frames of one room"*) and for `plant` (INV-231) —
and both fixes were applied **to their own table entry** rather than to the shape of the table. The
other seven entries kept the defect, and `plant` is now the only module in the group that passes.
**A fix applied to an instance and not to the rule is a fix that will be needed again.** When a
defect is found in one entry of a table, check every entry and gate the table.

**NO GATE HERE ASKS A TRANSFORM WHETHER IT IS A ROTATION, AND THE WHOLE CROWD WAS MIRRORED FOR SIX
SESSIONS.** Session 4q. `npc.gd::_walker_xform` built `Basis(fwd.cross(up), up, fwd)`.
`Basis(x, y, z)` takes **columns** and is right-handed only when x × y = z; with `right = fwd × up`
that product is **minus** fwd, so the determinant is exactly **−1**. Every walker in the corridor
was drawn as their own reflection, in all three places that file builds one — while the **baked**
half of the same crowd used `populace._place_body`'s plain yaw, which is always right-handed. **The
two halves of one crowd disagreed about which way round a person is.**

It survived because a roughly symmetric body reads the same either way at corridor distance, and
every visual gate here scores a *picture*. What found it was `ragdoll.gd::promote` **refusing to
promote into a transform with determinant −1.0000** — a one-line precondition written for a bug
the *gate* had hit, which turned out to be sitting in the shipped crowd. A precondition is cheaper
than a render and can fail for a reason a render cannot express.

**And the fix was applied to the RULE:** `player.gd` and `dialogue.gd` use the identical
`fwd.cross(up)` idiom and are **both correct**, because they pass `Basis(right, up, -fwd)` and the
two negations cancel to +1. All five sites in the project were checked; only `npc.gd`'s three
needed the other sign. *Check every site of an idiom before deciding which one is wrong.*

**A DEFAULT THAT IS ONLY EVER SET BY THE GATE IT WAS WRITTEN IN IS AN UNSET DEFAULT.** Same
session. `ragdoll.gd` defaulted gravity to **9.81 m/s²** and up to **+Y**, and the only caller
that supplied the real values was `--ragdoll-gate`, where they were authored. The path a player's
session actually goes through — `npc.gd::promote_walker` — set neither, so a real collapse would
have fallen at Earth gravity straight down on a station whose deck delivers **7.454 m/s² along a
radius**. The cure is to move the derivation into the thing that needs it (`ragdoll.gd` now works
both out from the body's own world position) and to give it a control that withholds the stated
values: `--derive-g` is **byte-identical** to the run that states them. INV-451.

**A RESCUE SNAPSHOT IS NOT FREE, AND IT CAN POISON AN AGENT'S OWN BASELINE.** Session 4r, and
it is the counterweight to the `git add -A` rule above rather than a contradiction of it. This
container was recycled **three times in one session**; each recycle rolled the checkout back
and took everything uncommitted, so the main agent began committing labelled
`WIP SNAPSHOT n — NOTHING HERE IS VERIFIED` restore points that deliberately captured running
agents' mid-flight files. Staged by an explicit list every time — **never `git add -A`** — and
that distinction matters, because three separate agents reported the hazard as *"`git add -A`
swept my files"* and **all three were wrong about the mechanism**. It was a deliberate rescue.

But the cost is real and one of them named it exactly: *"had the snapshot landed 20 minutes
earlier my baseline would have been my own 'after'."* **An agent that computes a BEFORE from
`git show HEAD:` can get a HEAD that already contains its own half-finished work**, and the
resulting A/B is a diff of a thing against itself. That is the vacuous-A/B defect this file
already records from 4d, arriving by a new route.

So: rescue snapshots are right when a container is being recycled, and they need two things
said out loud. **Label them so nobody reads them as reviewed** — the label is what stops a WIP
commit being cited as evidence later. And **an agent that needs a baseline must take it from a
`git worktree` at a NAMED commit it chose, not from live `HEAD`**, because HEAD is a moving
target while anyone is snapshotting.

**READ THE SHAPE OF A FAILING NUMBER BEFORE READING ITS SIZE.** Session 4d, and it is the cheapest
lesson in this file. `interact.py --audit` failed on 84 of 357 declared interactables and 4c wrote
the work up as two lists of props to go and build. The number that mattered was the split:
`built generic 273/275, built bespoke 0/82`. **Every** generic room resolved its declared
interactables and **no** bespoke room resolved any — which is not 23 modules each forgetting the
same thing, it is one function with one caller. Extracting `rooms.place_interacts` and adding one
mesh-derived alias rule closed all 84, and a stub-out control decomposed it exactly: 26 of the 98
were never missing, only misnamed.

*A number that fails evenly is a list of jobs. A number that fails 100% on one side of a line and
1% on the other is a structural fact.*

**AND A DIFF OF TWO FAILED RUNS IS NOT A PASS.** The A/B that proved the extraction changed nothing
said IDENTICAL on its first run because both halves had died on the same `IndexError` and written
empty files. Any harness that compares two outputs must assert both were produced.

### COLLISION IS NOT RENDER GEOMETRY, and that rule was learned expensively

Session 3v, and it is the W-track's equivalent of the layer-2 lesson. A body stood on the assembled
deck reporting `on_floor=true` and moved **1 mm** in all four headings. The cause was not the rooms,
the arc size, double precision, or 7 km from the origin. It was that the corridor deck carries a
**66 mm lighting channel down its centreline and 22 mm proud grid tiles either side of it**, and a
capsule dropped on that wedges on an internal edge.

`station/collision.py` sweeps a smooth shell instead, at **1.5%** of the render mesh's triangles,
and the body walks 126 m. Two things follow and both are binding:

1. **A player walks on a surface built for walking on.** Any new walkable geometry needs a shell.
   The shell's profile is **measured off the kit by ray casting**, never written down, so it cannot
   drift from what it stands in for — hard rule 4 applied to a third mesh.
2. **A walk gate must report DISTANCE COVERED, not "did it move".** Four one-second nudges prove a
   body is not wedged; they do not prove you can go anywhere. `walkable.py --deck` asserts metres
   traversed and frames spent off the floor, and it **fails on the pre-shell content** — that A/B is
   in `STATE.md` and is the evidence the gate is real.

The layer material below is still the right description of the PLACES track and its lessons are
real. It is no longer the ordering rule.

## The layer plan — still the right description of the shell, no longer the order

> **`docs/MASTER-PLAN.md` is the full plan** — three tracks (places, systems, player), twelve
> milestones, every system enumerated with its status, and an audit that found this section
> incomplete in two blocking ways: the eight layers below describe *a set of places, not a
> simulation*, and *there is no player*. Read it before planning a session. What follows is the
> PLACES track only.

**Set by the owner, session 3k, and it supersedes the phase plan that came before it:**
*"I'd rather do something in layers but complete, rather than small slices which do not add up
together."*

That is a decision about how work is *finished*, and it is binding. The previous plan was six
overlapping phases, which sounds like an order and is not one: with phases running in parallel,
every session picks whatever seems plausible, nothing is ever completed, and progress becomes a
feeling rather than a number. That is exactly what happened between sessions 3h and 3k — fifteen
modules of geometry, of which twelve did not know where they were on the station.

**So: one layer at a time, across ALL 126 locations, finished before the next begins.**

A completed layer is a state the next context inherits cleanly. A half-finished vertical slice
plus 125 grey boxes is not, and this project loses its context regularly.

### The layers

`docs/gazetteer/LOCATIONS.md` holds the **126 locations**. `station/directory.py` is the register,
parses that file, and **prints per-layer completion in CI** — so the answer to "how far are we" is
a number this repository computes, never a summary anyone writes.

The denominator is **118 places** — the 126 gazetteer rows less 8 that are not locations (a prop
type, a broadcast, an area label, the off-station jump gate). `directory.py` prints both numbers
and asserts every row is addressed *or* deferred with a reason, so the deferral list cannot be
grown to make a number go green.

| # | Layer | Done when | Status |
|---|---|---|---|
| **0** | **Engine path** | A materialled, lit frame comes out of Godot + lavapipe and can be scored against `docs/AAA-STANDARD.md`. Infrastructure, not per-location | **DONE** |
| **1** | **Addressed** | All have `(sector, ring, deck, angle, z)`, footprints that do not collide, declared functions and interactions | **118 / 118 COMPLETE** |
| **2a** | **Geometry — topology** | Every addressed location has mesh, closed, correctly wound, inside its own footprint | **118 / 118 COMPLETE** |
| **2b** | **Geometry — articulation** | Visible line density at or above its floor, derived from budget / Nyquist / the show's own frames — `station/density.py`, INV-070. **This is the layer the register now reports** | **123 / 128** (3z). And a whole-location gate hides a flat surface inside its own average, which is how every machine in the station stayed a box while 123 passed — `density.py --machinery` scores `fix_*`/`prop_*` alone against the room's OWN shell and reads **74 / 78** |
| **3** | **Materials** | Every mesh carries PBR materials from `materials.py`. No flat colour anywhere | **COMPLETE** — `test_materials_layer3.py` reads **503 / 503 interior groups**, including the 53-material wardrobe imported from `npc/costume.py` |
| **4a** | **Lighting — level** | Every location has a rig and a measured exposure, median-matched to its reference | **`docking_bays` NOW PASSES 7/7** (4m): median x0.30 -> **x1.48**, crushed 92.25% -> **9.86%**, every distribution statistic inside band. THE DIAGNOSIS WAS ARITHMETIC, NOT A RENDER -- summing Godot's own attenuation over every source on the working plane, the corridor anchor delivers mean E **4.2641** and this room delivered **0.0722**: its forty floodlights supplied **1.7%** of the anchor's floor irradiance, while the flat ambient supplied 3.1x what they did. **RE-MEASURE A ROOM'S IRRADIANCE BEFORE TOUCHING ITS EXPOSURE** -- three sessions of knob-turning could not have found that. **AND THE MEASUREMENT ITSELF HAS A TRAP:** `measure_frame` censors at `FLOOR = 0.010`, so every statistic except `level_p25` is taken over the MEASURABLE pixels -- at the old exposure that was **7.7% of the frame**, almost all lamp glow. The old row passed its level test on 7.7% of its own pixels, and the p95 'collapse' recorded earlier in 4l was that population changing, not light. Always read `measurable %` beside any statistic from this tool. Ambient-alone, finally run as a single variable: x5 gets the level right and collapses the distribution into a 0.026-0.049 band -- **ambient buys level and spends contrast**. `ambient_energy` takes the `place["module"]` branch for a bespoke place and NEVER consults `AMBIENT_BY_ARCHETYPE`, which is why this room's default was 0.351 and not the 0.089 an earlier note in this file computed. Previously: **20 / 21** in window (3z).
| **4b** | **Lighting — mood** | Every location matches its reference's *distribution*, not just its median — p5, p95, crushed, clipped | **13 / 23, 0 unverifiable** (3z, was 3 / 11 with 9 unverifiable). **Eleven of the fourteen failures were STALE FRAMES rather than lighting defects** — see below |
| **5** | **Props & function** | The declared interactable types exist and do what `directory.py` says they do | **They EXIST: 357 / 357** (4d) — `interact.py --audit`. It was 273/357, and the shape of the failure was the finding: `built generic 273/275, built bespoke 0/82`, because the placement rule lived inside `rooms.build` where only one caller could reach it. `density.py --machinery` gates their articulation at 74/78. What they DO is `interact.py`'s eight verbs, four of which have a prop that responds |
| **6** | **Inhabitants** | NPCs placed, scheduled and animated in every location, at real density | **963 walking in the corridors and 1,065 in the rooms** (3z), each a named resident with a home, a job and a schedule, posed from `npc/animation.py`'s clips and DRESSED from `npc/costume.py`'s measured wardrobe. Not animated at runtime: the corridor crowd moves (5,966 m measured over a walk test), the room occupants do not |
| **7** | **Audio** | Ambience and event audio per location | **AMBIENCE DONE** (4e) — `station/audio.py`, 100/100. Seven layers per location, each with a level in dBA **and the reason it is that level**, derived rather than authored: air from the design occupancy ladder, structure from `interior.SPOKE_COUNT` and the 33.4716 s spin period, machinery from `rooms.FIXTURES`, crowd from `populace.occupancy` × `schedule.awake_fraction` weighted by the place's own species mix, traffic from `traffic.berths_in_use`, PA from `broadcast.audible_at` era-locked through `costume.ERA_EVENTS`. **The Zocalo swings 62.1 → 67.6 dBA between 03:00 and 13:00** and the reactor hall swings +0.05, which is the control. 13 loop-exact WAVs, 5.7 MB. NOT done: reverb zones, occlusion (a shut door does not muffle), event audio beyond the chime, and no absolute level is referenced to anything — all authority 5, INV-260..264 |
| **8** | **Judged** | Every location scored against the rubric in an engine frame, and passing | 0 |

**Layer 0 is done.** `tools/render_godot.sh` renders exterior *and* interior offscreen through
Godot 4.4 double + Mesa lavapipe, and frames are scored in `docs/aaa-scorecard.json`. It had never
been missing — it was built in session 2j and then not run again, so every render from 2j to 3k
came from the flat-shaded rasteriser, which judges structure and says nothing about craft.
Reviving it took one command. **Do not let it rot a second time: any craft claim cites an engine
frame, or it is not a craft claim.**

**Layer 2 is done**, and the thing that finished it is worth carrying forward: `interacts` in
`directory.py` is *what a player can use*, and a room built from it alone is controls without
machinery — "Fabrication furnaces" was a grey box holding two control podiums and no furnace.
`rooms.FIXTURES` supplies what a room is named for. Expect the same gap in every later layer:
**the declared list is never the whole room.**

**Layer 3 is done.** The emissive-window finding it inherited is closed (`INV-036`,
`hull_window.gdshader`).

### LAYER 2 WAS UNDER-SPECIFIED, AND IT COST THREE LAYERS OF WORK

Session 3r, and it is the most expensive lesson in this file. The owner looked at the renders and
said the buildings are *"shitty little cubes"* and the trees a *"sad excuse for a tree"*. Both are
literally accurate descriptions of the generators. **Every gate was green when they said it.**

The cause is one sentence — layer 2's old exit criterion, *"mesh, closed, correctly wound, inside
its own footprint"*. That is a **topological** test and **a cube passes every word of it**. So 118
locations of blockout passed layer 2 legitimately, and layers 3 and 4 dutifully put materials and
lighting on blockout. `station/garden.py`'s `block_building()` docstring says **"Cheap by design"** —
an explicit placeholder, correctly labelled, and nobody ever came back for it.

**`docs/AAA-STANDARD.md` would have caught this on day one.** Its craft section has always said to
judge *"at three distances: the distance the player normally sees it from, half that, and the
distance at which it is one pixel of silhouette"*, and C1 is defined as *"a box primitive standing
in for a named object"*. **Only the first distance was ever rendered.** At 200 m a box reads as a
building. The standard did not fail; applying it did — and the rubric was never run against a single
one of the 118 interior locations until 3r.

So layer 2 is split. **2a is what was actually tested and it is genuinely complete** — the closure
and winding work is real and hard-won. **2b is the bar that was missing.** The first honest
close-range scores are in `docs/aaa-scorecard.json`:

| subject | craft | what the frame shows |
|---|---|---|
| `zocalo_interior` | **3** | arches, gallery, stalls, tables, tiling — reads as the place, falls apart at half distance |
| `generated_rooms` | **1** | flat panels, blown-out lights, a counter slab. **58% of the station** |
| `garden_townscape` | **1** | box + cylinder trees, box buildings, 2,228 tri for a whole settlement |

**The quality is uneven, and that matters:** the Zocalo is genuinely a 3 and the 68 generated rooms
are a 1. This is not "everything is bad", it is "the bulk was never articulated".

**Rules that follow, and they are binding:**

1. **Every craft claim cites a frame at the rubric's HALF distance, not the normal one.** A wide
   shot is not evidence about craft. This is the rule that would have prevented all of it.
2. **A layer's exit criterion must be able to fail on the current content.** If it cannot, it is
   measuring the wrong thing — the same defect as an assertion that cannot fail, at plan scale.
3. **The triangle budget is a TARGET, not a ceiling.** `station/budget.py` reports the drum visible
   set at 17% of budget and the ground at 0.05 tri/m². 83% headroom sat unspent for sessions
   because the gate only ever said "under budget, pass".

### LAYER 4 SPLIT FOR THE SAME REASON LAYER 2 DID: the criterion could not fail

Session 3r. Layer 4's criterion said *"lit to its reference's mood"* and the test was a **median**
within x1.40 +/-25%. A median is a statistic a flat, washed-out frame matches perfectly, so the
criterion could not express the thing it was named for.

`tools/measure_frame.py` now compares the whole distribution — p5, p95, p5/p95, crushed (as a ratio
*and* an absolute envelope) and a one-sided clipped cap. The tolerances are **derived, not chosen**:
33 deduplicated authority-1 frames, paired by the interchangeability rule this project already used
(`DRUM_CALIBRATION` accepts two references whose medians agree within `TOL`), 124 qualifying pairs,
band = p95 of |ln(a/b)|. Validated by running the gate on the show against itself — 248 trials,
combined pass 77.4%, stated rather than tuned to look better. `--derive` recomputes every band from
the corpus and fails if a recorded value has drifted.

**The result when this was written: 17 of 17 passed the median test and 1 of 17 the distribution
test.** `p5` was the discriminator, failing 13 of 17, bright on 11 — including the corridor anchor
that defines 1.00 for the entire project (p5 x1.64).

**AND ELEVEN OF THOSE FOURTEEN FAILURES WERE STALE FRAMES, NOT LIGHTING DEFECTS.** Session 3z.
Every failing frame had been committed on 07-29 or 07-30; every frame committed on 07-31 passed;
the lens fix and the corridor soft fill landed in between and **nobody re-took the older ones**.
`--gate-frames` re-measured a committed PNG, so it could say whether the **file** passed and never
whether the file still described the **code**.

The anchor was the worst case, and it is the frame `RENDER_OFFSET = 1.40` is *defined* against.
Re-rendered from its own recorded command, nothing else changed:

| | committed | re-rendered | show |
|---|---|---|---|
| p5 (band x1.29) | **x1.64 FAIL** | **x0.80 PASS** | — |
| soffit / wall | **x1.82** | **x0.214** | 0.23–0.32 |
| deck / wall | **x0.29** | **x2.59** | 2.49 |

The committed frame had the show's own ladder **upside down**, and this file's headline for the
layer was measured on it. **13 of 23 pass now, with 0 unverifiable.** `EXPOSURE_FRAMES` carries the
shot per row and `--gate-frames --rerender` re-takes it, so a frame cannot go stale silently again.

**A GATE THAT READS A COMMITTED ARTEFACT MUST BE ABLE TO REBUILD IT.** That is the general form,
and it is the same defect as `budget.py`'s cached collision total — which at least printed loudly
when it drifted, because a cache that can go stale silently is a second copy of a computed number.

Two negative results worth keeping: `p95` (band x3.27) and `p5/p95` (x3.38) are nearly inert. The
ratio is the statistic that *sounds* like it measures mood and measures least, because it inherits
p95's variance.

**And the derivation formula behind every room exposure is invalid.** Every value came from
`gain *= 1.40 * ref_median / our_median`, which assumes the median scales with exposure. Measured
over the corpus, `d(ln median)/d(ln gain)` ranges from **0.97 to 0.01** and goes **negative** on
four frames — including `customs`' own reference — because raising exposure recruits sub-floor
pixels into the measurable set from the bottom. STATE.md had recorded the symptom on `plant` ("sits
at 1.59x either way") and blamed that room's geometry. It is a property of the statistic.

**Nine of eleven `ROOM_EXPOSURE` values have no committed frame at all** and are therefore not
verifiable in either direction. They were set by rendering, measuring, and not keeping the render.

**Layer 4 is therefore split.** 4a — a rig and a measured level — is genuinely complete and the work
is real; 20 of 21 rooms are in window, and the one that is not (`plant`) fails on **quantisation**
rather than geometry: 85% of its frame sits at sRGB byte 0–1, under the eight-bit floor, so its
level is not derivable from a PNG at all. 4b is the bar that was missing and stands at **13 / 23**.

**`ROOM_EXPOSURE` is re-derived from `level_p25`**, the *uncensored* 25th percentile, and the
reason is the one recorded above: over our own 21 rooms at three gains, the censored median is
monotonic in exposure on only **15 of 21** and goes DOWN when the lights go up on six of them,
while `level_p25` is monotonic on **20 of 21**. It responds because its population is fixed —
censoring at `FLOOR` recruits sub-floor pixels into the set as gain rises, and they arrive at the
bottom. It is the **control variable, not the target**: `p25_ours/p25_ref` is dominated by black
fraction, and solving against it directly gave gains of 0.15 on four rooms. The target is still the
censored median at x1.40.

**What the shadows actually are, measured rather than argued:** fixture energy is **inert** (0 → 2.0
moves p5 by x1.0000), the soft fill nearly so (6 → 24 moves it x1.11), and **ambient owns p5**
(1.30 → 2.60 moves it x2.35). The tonemapper is **not** the cause of the flatness — AgX gives the
*lowest* p5 of the five available, so that hypothesis is refuted. And **the blown pools and vitrines
are EMISSION**: over x5.7 of gain the lit wall moved x3.48 and a deck light strip moved **x1.007**,
because `room_exposure` scales fittings and ambient while `emission_energy` is a material property
neither touches.

**Layer 4's older lesson still stands, and it is about MEASUREMENT, not
light: `docs/layer4-lighting/*.json` records a per-space `ambient.ratio` taken from two hand-picked
regions of a balanced frame, and a whole-frame percentile of the same frame gives a different
number (0.300 vs 0.086 on `grey level 1.webp`). Tuning a render against the wrong one of those
lands it two and a half stops hot. **The only valid comparison is our frame against the show's
frame, measured by the same code** — `tools/measure_frame.py --against`. Every room exposure in
`export_scene.ROOM_EXPOSURE` was obtained that way and the derivation is in `INV-037`.

### OPEN DECISION — layer 5 may be the wrong next thing, and the plan says so

The two planning documents contradict each other at exactly the next step, and this section is
where the next context will look first, so it is recorded here rather than left to be rediscovered.

- **This section's rule** says finish a layer across all 118 before starting the next. That makes
  layer 5, props & function, the next work.
- **`docs/MASTER-PLAN.md` §3.2** says *"S1–S3 before P5–P6. Props and inhabitants should be placed
  against what the simulation needs, not guessed. A bar needs a till because the economy has
  money."* and *"L1–L2 early. Building 71 prop behaviours before knowing the verb set is how you
  build the wrong 71."*

Both were set deliberately and they cannot both be followed. The layer rule exists because parallel
phases meant nothing ever finished; §3.2 exists because props built with no economy and no verb set
are props built twice.

**Recommendation, not a decision — the owner has not ruled.** Follow §3.2: when layer 4 closes, go
to the SYSTEMS and PLAYER tracks (S1–S3, L1–L2) before layer 5. The layer rule's purpose is that
work *completes*, and completing the places track first still leaves a station nobody can stand in.
`MASTER-PLAN.md` §1.3 is titled *"FINDING 2 — there is no player"*, and it is still true: every
script in `godot/scripts/` is a screenshot tool, and `station/npc/` and `station/physics/` are
twelve tested modules with **zero importers outside their own directories**.

Whoever picks this up: it is a real fork, it is cheap to raise with the owner, and guessing wrong
costs a track's worth of rework.

### Rules that follow from working in layers

1. **Do not start a layer before the one above it is complete.** The exception is layer 0, which
   is infrastructure and must finish first regardless.
2. **Within a layer, order by the gazetteer's ranked list, then by authority.** Authority-1
   locations first — they are the ones a viewer can catch us on.
3. **A layer is complete when `directory.py` says so**, not when it feels done.
4. **Nothing is "done" at a layer it has not reached.** A room with geometry and no materials is
   at layer 2. Saying it is built is true; saying it is finished is not.

### The loop

Every subsystem goes through the same cycle, and the cycle is what produces quality — not a
single careful build:

**build → harsh panel review → rework → re-judge → stop.**

- The reviewer is a **panel, not an aesthete**: craft, fidelity, performance and robustness are
  different questions, and a visual critic cannot answer the last two. Renders validate nothing
  about framerate.
- The reviewer's job is to be **the reason this is good**, not to be agreeable. It assumes a
  defect is present and goes looking. Every finding cites what was run or read.
- **It has to be able to stop.** A sufficiently harsh critic always finds something, so
  "keep going until it's AAA" without a defined bar never terminates and one item eats unbounded
  budget. The bar is in `docs/AAA-STANDARD.md`; the stopping rule is part of it.
- A reviewer may be **wrong**. A builder may decline a finding with evidence. A disagreement
  that cannot be supported is not a disagreement.

## Hard rules

1. **Nothing is built from memory — but everything gets built.** Every dimension, layout and
   name either traces to `canon/00-MASTER.md` **or is a declared extrapolation** logged in
   `canon/INVENTIONS.md`. What is forbidden is *unmarked* invention: a number that looks sourced
   and is not. Owner's instruction, session 3c: *"you extrapolate to the best of your ability
   based on your research"* and *"I don't have perfect photo references."*

   So the answer to "the show never establishes this" is **never** to leave a hole. It is to
   extrapolate in style, reason it out on the page, mark it authority 5, and record what would
   overturn it. A station with a declared-invented corridor width is finishable; a station with
   a missing corridor is not.

   The bar for an extrapolation is that a reader can see *why* it is that value: what constrained
   it, what it was derived from, what it would break if wrong. `INV-020`'s concourse width is a
   good example of the standard — it says plainly which of its three numbers is weak and what one
   frame would close it.
2. **Log every invention** in `canon/INVENTIONS.md` — what, why, what constrained it, what
   would overturn it. Canon and extrapolation must never blur.
3. **Blocking conflicts block.** `canon/CONFLICTS.md` entries marked BLOCKING stop the
   affected work. Do not resolve one by picking whichever reading is convenient today.
4. **Inside and outside come from the same schema.** Never hand-author hull geometry that
   duplicates interior geometry. Consistency is by construction, not by discipline.
5. **Double precision everywhere in world space.** The station is 8 km long; float32 jitters
   visibly at that scale.
6. **Update `STATE.md` before ending any session.** It is the handoff to the next context.

## Verification — how to see without a GPU

There is no GPU in the build container, and the owner does not review intermediate work.
Rendering is therefore done in software and inspected directly:

```bash
# Mesa lavapipe provides Vulkan 1.4 on CPU. Already proven working.
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json <godot> --rendering-driver vulkan ...
```

Render offscreen to PNG, then **read the PNG** — image reading is available and is the
aesthetic feedback loop. Slow (seconds to tens of seconds a frame at 960×540) and entirely
adequate for judging composition, proportion, silhouette, layout, lighting and material.

It validates **nothing** about framerate. Performance is enforced separately by numeric budget
gates in CI: triangle counts, draw calls, instance counts, VRAM and texture memory measured
against the target hardware budget. Target: RTX 4070 / RX 7800 XT class, 1440p60, 12 GB VRAM.

**Two render paths, and they answer different questions.** Do not confuse them:

| | `tools/preview_render.py` | Godot + lavapipe |
|---|---|---|
| what it is | flat-shaded software rasteriser, seconds a frame | the actual engine, offscreen, minutes a frame |
| honest about | silhouette, proportion, composition, layout, whether geometry is present and facing the right way | materials, lighting, shadows, exposure, what the thing will actually look like |
| says nothing about | material, light, mood — everything phase C and D exist to produce | framerate, still |

Judging AAA visuals from the preview rasteriser is judging the wrong artefact. Craft scores come
from the engine path; structural scores can come from either.

**A hole in geometry shows the background through it, and the background is black.** Two
surfaces shipped open for four sessions because of this. Render against magenta when checking
closure — better, use `interior.boundary_edges()`, which measures what no render can.

## Tools

| Tool | Purpose |
|---|---|
| `tools/refzoom.py` | Crop and magnify regions of reference images so fine detail is legible |
| `tools/measure_schematic.py` | Calibrate a schematic against its scale bar and measure real dimensions |
| `tools/sort_references.py` | File the reference dump into subject folders |

## Layout

```
canon/        Sourced facts. 00-MASTER.md, CONFLICTS.md, INVENTIONS.md
reference/    Show reference material, sorted; 00-INDEX.md catalogues it
docs/adr/     Architecture decisions, numbered, with reasoning
station/      The parametric station schema and its generators
tools/        Analysis and pipeline utilities
STATE.md      Where we are, what is next, what is half-finished
```

## Engine

Godot 4, C#, built from source with `precision=double`. Chosen because every file is text and
therefore authorable, diffable and regression-testable across many sessions by an agent
working without an editor GUI. See `docs/adr/0001-engine-choice.md`.

Heavy content generation happens **offline in Python** — schema → meshes, collision, navmesh —
deterministic and unit-testable without an engine at all. The runtime consumes committed data.

## Scope and cost discipline

This project runs partly on a **6-hourly trigger** (`trig_01JS1VWf6yada5x6maPMAzza`, fires at
:45) and on background workflows, so an unbounded session compounds. Bounds, in order of importance:

1. **Stop when the next-session list is empty.** If `STATE.md` has no actionable item — because
   everything remaining is blocked by `canon/CONFLICTS.md` — then say so and stop. Do not
   invent work to fill the time. An hourly trigger finding nothing to do should cost almost
   nothing.
2. **One coherent increment per firing.** Build the next thing, test it, look at it, commit,
   update `STATE.md`, stop. Do not chain five subsystems because there is context left.
3. **Workflows are for genuine fan-out**, not for work one agent can do serially. A workflow
   costs roughly its agent count times a normal turn. Five agents to build five independent
   subsystems is worth it; five agents to write one file is not.

   **DO NOT ASK BEFORE LAUNCHING AGENTS. Use them, and use them smartly.** Set by the owner in
   session 4e and it REPLACES session 3q's "ask before setting any of them in motion". The 3q
   rule existed because a 12-agent fan-out had just burned an hour writing nothing; the cure for
   that is the width cap and the discipline below, not a permission gate. Waiting to be asked
   cost session 4e most of a session of parallel work — the owner's words were *"why have we not
   used agents to build?"*

   **"Smartly" is the four rules that follow, and they are what the permission gate was standing
   in for.** Width is capped by the hardware. File lists must be disjoint, and checked for
   hidden artefact collisions. The main agent must stay off the cores while they run. And their
   output is not done until it has been verified and integrated.

   **Cap: 2–3 agents, and that is the HARDWARE, not a preference.** The owner set 2–3 in session
   3q and it matches the machine exactly: `nproc` is 4, the workflow runtime caps concurrency at
   `min(16, nproc - 2)`, so **two agents run and everything else queues**. The old guidance here
   said ~10–14 and it was measured wrong in session 3o: a 12-agent fan-out became a six-deep
   queue, ran fifteen minutes with two agents still on their first pass, wrote nothing, and was
   killed. The work was then done serially from the same committed data the agents were being
   asked to read.

   Two agents *is* the useful width. The session-3p run cost 596k subagent tokens over 66
   minutes, both finished, and it caught two of this agent's own factual claims as wrong plus a
   camera defect this agent had introduced. Width beyond two buys nothing on this box.

   **Give agents disjoint file lists and check for hidden collisions.** `materials.py --export`
   rewrites the `.tscn` files, so an agent owning `materials.py` and an agent owning
   `exterior.tscn` collide even though their file lists look separate. Have the second report
   what to apply and apply it at integration.

   **DISJOINT SOURCE FILES ARE NOT DISJOINT IMPORTS EITHER.** Session 4e: the NPC agent owned
   `station/npc/body.py` and the main agent owned `station/deck.py` — genuinely disjoint. Then a
   render came back with **913 mesh instances down to 62** and every room reporting
   `name '_hand' is not defined`, because `rooms.build` imports `populace`, which imports
   `npc/body.py`, and the agent had written the CALL before the function. Nothing was broken;
   the frame was taken against a file mid-edit. **Before believing a render taken while an agent
   is running, check whether it imports anything that agent owns.** The cheap fix is to render
   from a `git worktree` at your own HEAD, and the cheap tell is a mesh-instance count that has
   collapsed.

   **DISJOINT SOURCE FILES ARE NOT DISJOINT ARTEFACTS.** Session 3w: two agents and the main
   agent all had separate source files and all three ran `station/walkable.py`, which rebuilds
   `station/generated/scene/deck/*` before every run. They stomped each other's meshes
   mid-test. One run **timed out at 1800 s** and another failed on a half-written `populace.py`
   — neither was a defect in anything being tested, and the first looked exactly like a
   performance regression from the change that had just landed. Measured alone the same gate
   takes **38 s**. Before believing a slow or failing gate, check whether something else is
   writing its inputs; an agent that needs to run a build should do it in `git worktree`.

   **DO NOT RUN THE WHOLE-STATION GATES WHILE AGENTS ARE RUNNING.** Session 4c: two agents
   both died at ~70 minutes, three minutes apart, with no crash signature and nothing in the
   kernel log -- one produced zero commits and the other was cut off mid-flight. The cause was
   contention from the MAIN agent: `rooms.py` pinned at 99% CPU for 24 minutes, plus
   `--gate-frames --rerender` and deck renders, on a four-core box, while they were trying to run
   `walkable.py` and `deck.py --sweep`. `deck.py --sweep`, `walkable.py`, `rooms.py` and
   `--gate-frames --rerender` are each minutes of 100% CPU and are exactly what an agent needs to
   verify itself. While agents run, do cheap work: read, profile one unit, write. The rule is not
   "use fewer agents".

   **A SLOW SUITE IS A BUG UNTIL PROFILED, NOT A CONTENT COST.** Same session: `rooms.py` went
   from 2 minutes to 24 and it looked like the wall-plating merge had tripled the geometry. It was
   one cache key -- `interior.load()` returns a fresh dict every call, so an `id(schema)`-keyed
   memo missed every time and every room paid 11.2 s rebuilding the station's 3,414 cells.
   Profiling ONE room build found it in a minute. Two sessions have now lost time to a slow gate
   that read as a regression in the thing it was testing.

   **Their work is not done when they return it.** In three runs: one agent's output was left
   uncommitted at a session boundary, one wrote entries into a module that did nothing until
   four lines were added to `export_scene`, and one shipped gates that had to be replaced.
   Verify against the gates, render, and integrate — the review is the main agent's job.

   Keep the adversarial verify pattern. It has now caught a door interpenetrating a portal
   frame, a greeble signature mismatch, tram cars passing 6.43 m through a structural spoke, an
   end cap with 4,064 open edges, and two assertions that could not fail. It is the single
   highest-yield thing in this project's process.
4. **Never spawn a workflow from inside a triggered firing** unless the work genuinely needs
   it. The trigger already repeats; the multiplication is what gets expensive.
5. **Blocked applies to *labels*, almost never to *building*.** C-003 and C-004 decide which
   *name* attaches to a volume, not what shape it is — `drum_sector()` identifies the drum by
   geometry precisely so that construction never waits on the naming. Before reporting anything
   as blocked, check whether it is the label or the thing that is actually stuck. It is nearly
   always the label, and the thing can be built and named later.

   A real block is when proceeding would make the work *wrong* rather than merely *provisional*.
   Those are rare. Say what would unblock it and go build something else.

## Git

Branch: `claude/babylon5-station-sim-discussion-kgp4by`. Commit at every meaningful step;
push with `git push -u origin <branch>`. Do not open a PR unless asked.
