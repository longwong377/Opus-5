# Project State

**Last updated:** 2026-08-02 · **Session 4j** — **the 21 exposure frames describe the code again, and the verdict did not move** · **4i** — **every curved surface in the project was flat-shaded, and the crease angle is measured off the station** · **4h** — **IT IS PLAYABLE: press Play and you are standing in Blue Sector** · **4g** — **the Babcom terminal is a built device, and it shipped a logged mistake once before the log caught it** · **4f** — a per-token verb override · **4e** — **the naming-mismatch class is CLOSED: built-but-misnamed 26 → 0, resolving 302/357** · **4d** — **the bespoke rooms' interactables were never unbuilt, they were unnamed: 259/357 → 284/357** · **4c** — **the station is INTERACTABLE, the port is on a wall, and the 24-minute suites were one bad cache key** · **4b** — a police force, friction in metres, the plated shell, the fitting-reach fix

## Session 4j — THE 21 EXPOSURE FRAMES NOW DESCRIBE THE CODE AGAIN, AND THE VERDICT DID NOT MOVE

### 1. What was stale and why

4i gave the glTF exporter crease-angle normals, which changed the shading of every curved surface
in the project. **Every committed frame `--gate-frames` reads was rendered before that**, so the
layer-4b gate was measuring code that no longer existed — the exact defect 3z recorded, where
eleven of fourteen distribution failures turned out to be stale frames rather than lighting.

`--gate-frames --rerender` re-took all 21 re-takeable rows from their own recorded shots. 20 files
changed on disk; the frames moved a long way:

| frame | pixels changed | max channel delta |
|---|---|---|
| `engine-medlab.png` | **89.7%** | 177 |
| `engine-corridor.png` (the anchor) | 24.7% | 27 |
| `engine-4a-worship.png` | 17.3% | 123 |

### 2. AND THE GATE CAME BACK IDENTICAL. 14 pass, 9 fail, THE SAME NINE

Not "about the same" — the same rows failing on the same statistics:

| row | before | after |
|---|---|---|
| medical p5 | ×1.46 | ×1.45 |
| office p5 | ×1.39 | ×1.39 |
| research p5 | ×1.79 | ×1.78 |
| worship p5 / p5·p95 | ×1.46 / ×3.53 | ×1.41 / ×3.92 |
| zocalo p5 | ×1.56 | ×1.57 |
| bespoke hospitality p5 | ×1.88 | ×1.88 |
| industrial p99 | ×0.31 | ×0.31 |
| alien_sector crushed | ×42.70 | ×42.70 |
| plant p5/p95 | ×27.21 | ×27.34 |

**This is a clean negative result and it is worth as much as a fix.** The p5-bright failures survive
re-shading 90% of a frame's pixels, so they are **not a shading-model artefact** — the flatness is
in the light, exactly where 3z's measurement said it was (ambient owns p5: 1.30 → 2.60 moves it
×2.35; fixture energy is inert at ×1.0000). Nobody needs to wonder again whether the normals were
hiding it.

It also re-establishes the frames as evidence: they now describe the build a player is standing in.

### 3. ONE FRAME RE-RENDERED BYTE-IDENTICAL, AND THAT IS THE RIGHT ANSWER

`docs/engine-alien-sector.png` came back bit-for-bit the same — a 640×360 frame with 17,990
distinct colours, so not a black frame hiding the difference. `--dihedral` on that room says why:

```
17,400 shared edges
  coplanar             0-  5 deg   5,856   33.66%
  curve tessellation   6- 45 deg      40    0.23%
  THE TROUGH          46- 84 deg       0    0.00%
  real corners        85-180 deg  11,504   66.11%
```

**It is built entirely from flat panels and square corners.** There is nothing in it to smooth, so
smoothing it is a no-op. The change does exactly nothing where nothing is curved and 89.7% of the
pixels where something is, which is the strongest statement of correctness available here.

### 4. WHAT IS STILL STALE, STATED RATHER THAN LEFT

- **The two `DECK` rows record no shot** (`deck_corridor`, `deck_door`) and could not be re-taken.
  Their frames are still flat-shaded. They are the only stale rows left, and the fix is to give
  them a shot in `EXPOSURE_FRAMES` the way every other row has one.
- **`docs/aaa-scorecard.json` is untouched.** Its craft scores were taken from frames that are now
  regenerated, but re-scoring is a judgement exercise and the file says of itself that it is a
  *"SEED, NOT A REVIEW … provisional until a reviewer other than the builder has scored it."*
  Re-scoring it from this session's frames would make that worse, not better.

### 5. A CORRECTION TO 4i's NEXT LIST

"The heads are bare" was too broad. The **baked cast** has hair — visible in `engine-medlab.png`,
two figures with dark hair and uniforms. It is the **instanced crowd LOD bodies** that are
featureless: `populace.station_crowd_library` builds them at LOD 2/4/8 and the near rung is what a
player sees a metre away.

### 6. NEXT

- Give the two `DECK` rows a recorded shot so `--rerender` can reach them.
- The crowd's near LOD has no face and no hair; the baked cast does.
- `tools/play.sh` still builds one cluster.

## Session 4i — EVERY CURVED SURFACE IN THE PROJECT WAS FLAT-SHADED

### 1. `station/generated/**.obj` carried ZERO `vn` lines, and it was on purpose once

`export_gltf.build_group`'s docstring said why, and it was true when it was written:

> *"Un-index into flat-shaded triangles with per-face normals. The hull is faceted deliberately --
> plating steps and section transitions should read as hard edges, not be smoothed away by shared
> vertex normals."*

**That was a decision about the exterior hull, taken when the hull was the only subject.** It then
applied, unexamined, to everything built since: the drum's 8 km barrel, 345 degrees of ring
corridor, every lathed cylinder in `dressing`, the observation domes, and every human head in the
crowd. `write_obj` emits `v` and `f` only, so nothing downstream could disagree — Godot receives
whatever `export_gltf` computes and there was no second opinion anywhere in the pipeline.

Same shape as the layer-2 lesson: **a criterion correct for one subject, applied to all of them
because nothing re-asked the question.**

### 2. THE CREASE ANGLE IS MEASURED OFF THE STATION, NOT CHOSEN

`export_gltf.py --dihedral` reports the distribution of dihedral angles across a mesh's shared
edges and re-derives the threshold. On the assembled blue/0/0 deck, 760,952 shared edges:

| band | edges | share |
|---|---|---|
| coplanar 0–5° | 279,455 | 36.72% |
| curve tessellation 6–45° | 38,041 | 5.00% |
| **THE TROUGH 46–84°** | **7,073** | **0.93%** |
| real corners 85–180° | 436,383 | 57.35% |

Bimodal, with a trough three orders of magnitude below either peak — so the threshold is *well
determined* rather than picked: anywhere in 46–84 shades at most 0.93% of edges the wrong way.
**`CREASE_DEG = 57`** is the least dense degree of it (1,509 edges within ±5).

**It agrees on geometry it was not derived from.** The 8 km hull, from a different generator,
puts its crossing at **50°** — 7° away. The drum's ground has **zero** edges above 85°, because a
heightfield is not architecture; the report says so in those words rather than crying wolf, and
checks only that 57 clears the terrain's steepest fold (7°).

My first attempt at the derivation was wrong in a way worth keeping: at 5-degree bins the trough
looked *empty*, and I nearly wrote "there is a clean gap from 50 to 70". At 1-degree resolution it
is 100–200 edges a degree. **The bin width was doing the arguing.**

### 3. AREA WEIGHTING WAS WRONG AND THE SELF-TEST CAUGHT IT

First implementation weighted each face normal by its area. A 24-segment barrel came back with
**48** distinct normals instead of 24: a quad split into two triangles gives one endpoint two faces
of the quad and the other endpoint one, so the two ends of the same lathe column got different
answers. **Angle-weighted normals are provably invariant to how a surface was triangulated**
(Thürmer & Wüthrich), which is the whole claim — the smoothed normal is a property of the surface,
not of the mesher.

Then the assertions themselves were wrong. *Counting distinct normals cannot tell smooth from
flat*: a flat-shaded barrel has 24 too, one per planar quad. What can, and what the gate measures
now: **on a smooth cylinder the vertex normal points out through its own vertex; on a flat-shaded
one it points through the middle of the facet, half a segment away.** Every check has a control
that fires:

| claim | control |
|---|---|
| barrel normals are radial to <1e-6° | crease 0 gives **exactly 7.5°** = 360/24/2 |
| a lathe seam smooths across duplicated vertices | index keying would leave both seam columns 7.5° out |
| a cube keeps 6 axis-aligned normals | crease 180 gives 8 diagonal ones, none axis-aligned |
| a capped cylinder keeps its rim | — barrel stays radial, caps stay axial |

Welding is **by position, not by index** — the same rule `interior.boundary_edges` uses, and the
difference between a smooth cylinder and a hard line down every barrel in the project.

### 4. AND THE A/B LOOKED LIKE IT HAD DONE NOTHING, BECAUSE OF A CACHE

The first re-render after the change was **bit-identical on the crowd**. `walkable.py` cached the
three crowd LOD libraries on `os.path.exists` and nothing else, so they survived every change to
the code that writes them — they were hours old and still flat. The deck itself had rebuilt and
10.7% of the frame had changed; the people had not.

`_stale()` now compares a generated file's mtime against the newest of `station/*.py` and
`station/npc/*.py`. Keyed on *every* station module rather than a hand-listed few, because the list
is exactly the thing that goes out of date. **A cache that can go stale silently is a second copy
of a computed number** — the same defect as `budget.py`'s cached collision total and
`--gate-frames` reading a committed PNG.

With everything rebuilt: **14.1%** of the frame differs from the flat build, `crowd 968/968
MATERIALLED` (was 728 — the library itself changed), and at 4× the near figure's head has lost the
hard facet ridge down its left side. The silhouette is unchanged, which is correct: smoothing
changes shading, not outline.

### 5. GATES

| gate | result |
|---|---|
| `export_gltf.py --selftest` | **9/9**, both controls firing |
| `--dihedral` on blue/0/0 | crossing **57°**, AGREES (0° away) |
| `--dihedral` on hull.obj | crossing **50°**, AGREES (7° away) |
| `--dihedral` on the drum ground | no corners; 57 clears its 7° steepest fold |
| `walkable.py --deck blue/0/0 --use` | **PASS** + PASS, both controls firing |
| `tools/play.sh --verify` | **PLAYABLE**, control firing |

Deck build cost 36 s → 63 s: ~19 s of smoothing on 657,880 triangles, plus the crowd libraries now
rebuilding when the code changes.

### 6. NEXT

- **`docs/aaa-scorecard.json`'s frames are now stale.** Every committed craft frame was rendered
  flat-shaded. They need re-taking before any craft score is quoted again — this is the
  `--gate-frames --rerender` lesson, and it applies to the scorecard the same way.
- The heads are still bare: dressed and smooth, but no features and no hair.
- `tools/play.sh` still builds one cluster; walk off the end of blue/0/0 and you walk off the
  built world.

## Session 4h — READ THIS FIRST: IT IS PLAYABLE. PRESS PLAY AND YOU ARE STANDING IN BLUE SECTOR

```
tools/play.sh            # build blue/0/0 and stand in it
tools/play.sh --verify   # the gate, with its negative control
tools/play.sh --shot p.png   # a frame through the player's own eye
```

`docs/engine-playable-eye.png` is the first frame ever taken from this project's playable build:
the residential corridor at eye height, deck lights running to the vanishing point, and a person
stopped a metre in front of the camera because the player is standing in their way.

### 1. WALKABLE WAS NOT PLAYABLE, AND THE WHOLE DISTANCE WAS THREE THINGS

The station has been walkable since 3v and 128/128 since 3z. It was not playable, and nothing in
the repository could say so, because **every route into the walkable build went through the
headless gate's command line**:

1. `godot/project.godot` had `run/main_scene="res://scenes/exterior.tscn"` — a screenshot rig with
   a flying camera and no body. Pressing Play gave a photograph of the outside of a building you
   could not enter.
2. `walk.gd`'s five paths (`glb`, `collision`, `actors`, `crowd`, `interact`) all defaulted to `""`.
   They only ever arrived as six command-line arguments written by `station/walkable.py`.
3. `station/generated/scene/` is gitignored, so a fresh clone has **no deck data at all**.

Closed by:

- **`walkable.py --build-only`** — assembles a cluster and writes `godot/play.json`, then stops.
  No Godot binary needed, so the content pipeline does not require the engine.
- **`walkable.engine_args()`** — ONE list of flags, shared by the headless gate and the human
  launch. Hard rule 4 applied to a command line: the build a person walks in and the build the gate
  measures cannot be assembled differently, because there is one function that assembles them.
  `drum_walk.walk` uses it too and adds only `--gravity`, which is the drum's alone.
- **`walk.gd::_play_manifest`** — reads `res://play.json` when nothing is on the command line. The
  file's `args` array IS `engine_args`'s output, verbatim. Anything actually typed WINS, so
  `--no-dress` and `--no-doors` still work as controls.
- **`run/main_scene = "res://scenes/walk.tscn"`**, and `_run_play()` as the third branch beside
  `--walk-test` and `--shot`.
- **WASD**, by *physical* keycode in `player.gd::_wish()`, so the same four keys sit under the same
  four fingers on AZERTY and Dvorak. Not by redefining `ui_up` in project.godot: overriding a
  built-in action REPLACES its defaults, so the arrows and the gamepad stick would have had to be
  re-listed by hand in a serialised resource format to add a letter. Click recaptures the mouse
  after Esc — before this, the first Esc ended looking around for the rest of the session.

### 2. THE GATE FAILED ON ITS FIRST RUN AND FOUND SOMETHING NO EXISTING GATE COULD

`tools/play.sh --verify` launches with **no arguments at all** — the configuration a person is
actually in — and reads `walk.gd::_play_report`'s heartbeat. First run:

```
  FAIL  the body is NOT on a floor at frame 12240 -- it is falling or wedged
  FAIL  it is 66294.115 m from the spawn the generator claimed (bar 0.3 m)
```

**The player was bulldozed 66 km out of the station by the crowd.** A walker's path is a fixed
circular orbit and their capsule is a `StaticBody3D` teleported onto it every step, so a body
standing on that orbit is shoved along at a walking pace, 0.6 m at a time, eventually through the
trimesh floor and into permanent free fall.

**Why 3z's walk gate reported `offfloor=0/1800` throughout: it runs 30 seconds and DRIVES the
body.** Every frame it measures is one where being moved is correct. **Standing still is the case
nothing tested** — and standing still is most of what a person does.

Fixed in `npc.gd::advance_crowd`: **the crowd yields.** A walker whose next step would put them
within `r + 0.35 + 0.15` m of the player does not take it, and their stride freezes with them, so
the pose is a person halted mid-step rather than moonwalking. Stopping rather than steering around
is both the smaller change and the more honest one — a person whose way you are standing in stops.
11 of 134 were stopped at the busiest moment of the passing verify run.

`play_verdict.py` now asserts on **every** report, not the last: the failure was intermittent
(shoved off, fall, land, shoved again), so a body sampled at the wrong instant looks fine. It also
asserts **peak speed with nobody at the keyboard** ≤ 0.05 m/s — "on the floor" cannot tell standing
from sliding.

### 3. 728 CROWD INSTANCES WERE ON THE glTF FALLBACK AND THE RUN SAID `382/382 MATERIALLED`

Found by **looking at the frame**, not by a gate. The first playable shot had a featureless white
mannequin a metre from the eye.

`dress_scene.bind()` walked `MeshInstance3D` only, and a **`MultiMeshInstance3D` is not one**, so
it stepped straight past the entire crowd. Worse, `walk.gd::_dress_level` called `_dress.release()`
immediately after binding the deck — and `_wire_people` loads the crowd libraries *after that*, so
the material table was already freed by the time the people existed. `npc.gd::build_crowd` names
each MultiMesh after its source mesh in as many words *"because material binding is by name"*.
Nothing had ever bound them.

Now: `bind()` handles `MultiMeshInstance3D` via `material_override`, `_dress_late()` binds the crowd
after it is wired and releases afterwards. **`dress: crowd 728/728 MATERIALLED, 0 on the glTF
fallback`**, and the near figure is in dark EarthForce twill with pale hands instead of white.

**The summary was true about the part it measured.** That is the shape of every defect this project
has hidden, and it is now three for three: a tag-coverage assertion that ran on a corridor with no
doors (3x), a coverage count that was not a walk test (3z), and a materialled count that was about
the deck while the people were blank.

### 4. GATES, ALL GREEN AFTER THE CHANGES

| gate | result |
|---|---|
| `tools/play.sh --verify` | **PLAYABLE** — stood for all 50 reports to frame 6000 (100 s), never further than **0.043 m** from the spawn, peak speed **0.000 m/s**, 15,611 m covered by the crowd |
| control: manifest removed | fires — *"with no manifest there is nothing to play and no body"* |
| `walkable.py --deck blue/0/0` | **PASS** — walks into `docking_bays` 6.3 m → 0.04 m, 9 of the room look up, 5,965 m of crowd travel |
| control: `--no-doors` | fires — stopped 5.26 m short |
| `walkable.py --deck blue/0/0 --use` | **PASS** — *"[E] operate the docking clamp"*, used from 1.26 m, the object moved 4.0 mm |
| control: clamp stripped | fires — 14 interactables instead of 15, prompt `-`, `use_count` 0 |

### 5. NEXT

- **The heads are bare.** The crowd is dressed but the faces are untextured skin — no features, no
  hair. At a metre from the eye that is the most visible thing in the frame.
- **`tools/play.sh` only builds one cluster.** Walking off the end of `blue/0/0` walks off the
  built world; there is no streaming and no way to travel between clusters in the playable build.
- **Nothing carried over from earlier sessions is closed by this one**: `device_screen_glass` blows
  out on 7 binds, no screen has content, `--gate-frames` is 14/9, `dressable_extent` is wrong on 4
  of 9 composed places, the OBJ carries **0 `vn` lines** so every curved surface is flat-shaded, and
  `dress()` emits 2,234 non-manifold edges on a 4,428-triangle office.

## Session 4b — THE STATION HAS A POLICE FORCE, AND THE WALL STOPPED BEING ONE FLAT PANEL

### 1. A 1,181-LINE GAZETTEER FILE HAD ZERO READERS

`grep -rl LAW-CRIME-DOWNBELOW station/ tools/` returned **nothing**, while `FACTIONS.md`,
`LIFE-SUPPORT-AND-INDUSTRY.md` and `TRAFFIC-AND-CUSTOMS.md` had 23 readers be## Session 4c — READ THIS FIRST: THE TIMEOUTS WERE ONE LINE, AND TWO AGENTS DIED OF ME

### 1. `rooms.py` took 24 MINUTES and the cause was a cache key I wrote

`interior.load()` **reads and parses the schema afresh on every call** — `load()[0] is load()[0]`
is `False`. `security.outermost_decks` memoised on `id(schema)`, so it **missed every time**;
`populace.populate` calls `security.presence_at` once per room; `presence_at` calls
`outermost_decks`; and that calls `navigation.cell_plan`, which walks every sector, ring and deck to
build the station's 3,414 streaming cells.

**Profiled on one generic room build: 11.2 seconds of 11.3 were `outermost_decks → cell_plan`.**

| | before | after |
|---|---|---|
| one room build | 4.88 s | **1.79 s first, 0.02 s after** |
| `station/rooms.py` | **24 min** (killed at every timeout) | **61 s**, 755/755 |

**And the gate I wrote for that memo passed the whole time.** It calls `presence_at` fifty times
with the *same schema object*, so the `id` key hit; it could not see the real caller, which passes
`None`. **A memo gate has to be exercised through the path production uses**, not through a
convenient one. This is the same defect class as an assertion that cannot fail, one level down.

If a suite in this project suddenly takes minutes instead of seconds, **profile one unit of work
before believing anything about the content**. Two sessions have now lost time to a slow gate that
looked like a regression in what it was testing.

### 2. TWO AGENTS DIED AND IT WAS CONTENTION I CAUSED

Both stopped at **00:40 and 00:43**, three minutes apart, ~70 minutes after launch. No OOM in the
kernel log, no crash signature. The dome agent produced **0 commits**; the interaction agent
committed once at 00:14 and was cut off mid-flight at 00:43 with 207 files touched.

The cause is in CLAUDE.md already and I did it anyway: **two agents plus the main agent, all running
the same heavy gates on four cores.** I had `rooms.py` pinned at 99% CPU for 24 minutes (see §1),
plus full `--gate-frames --rerender` sweeps and deck renders, while they were trying to run
`walkable.py` and `deck.py --sweep`. Their gates would have taken several times their normal
wall-clock, and ~70 minutes of budget bought them almost nothing.

**The rule, and it is not "use fewer agents":** while agents are running, **do not run the whole-
station gates**. Do small, cheap work — reading, single-room profiling, writing — and leave the
cores to them. `deck.py --sweep`, `walkable.py`, `rooms.py` and `--gate-frames --rerender` are all
minutes of 100% CPU and they are exactly what an agent needs to verify itself.

### 3. NOTHING IS INTERACTABLE EXCEPT THE DOOR — CLOSED

Salvaged from the agent that was cut off; it was its one committed increment and it is complete.

`directory.PLACES["interacts"]` has said what a player can use in every room since layer 1 — **357
declarations over 125 places** — and had two readers, both of which used it to decide where to stand
a box. `station/interact.py` derives a **bounded verb set from that data rather than inventing one**:
a row per value of `rooms.PROP_KIND`, overridden on the register's own head noun where name beats
shape. Both tables are asserted **total** (all 99 tokens resolve) and **minimal** (delete any
override and at least one token changes verb). **Eight verbs** fall out. `tread` is declared
unpressable — a catwalk is something you walk on.

**The gate, and it is the W-track's next milestone in one line:**

> **PASS use** — a body walks up to the docking clamp in `docking_bays`, is told
> **"[E] operate the docking clamp"** and USES it: `operate` from 1.26 m after 9 prompted frames,
> and the object moved 4.0 mm. 15 interactables wired on this deck, 13 pressable
> (open 5 / operate 7 / serve 1 / tread 2).
>
> *control:* with 800 triangles of `docking_bays__prop_docking_clamp` deleted **from the render mesh
> only** — the collision box stays, so the body walks the identical route to the identical place —
> the engine wires 14 instead of 15, the prompt reads `-`, and `use_count` is 0.

**`interact.py --audit` FAILS on current content, and that is the finding:** 259 of 357 declared
uses resolve to a group the place actually emits, and **the split is total** —
`built generic 259/259, built bespoke 0/98`. Of the 98, **26 are built under the module's own name**
(`bar_stool` for `stool`, `cc_console_face` for `console`) and **72 were never built at all** —
`babcom_terminal` is declared in nine places and built in none. INV-247.

### 4. The port is on a wall, and the era is with it

`traffic.py` modelled 55 movements a day and **nothing rendered any of it**. `signage.arrivals_board`
reads `traffic.arrivals` directly, so the board cannot say something the port is not doing; at 10:00
it lists **1048 ASIMOV-CLASS LINER BAY**, the liner the manifest actually scheduled.
`signage.notice_board` carries `broadcast`'s ISN and Ministry of Peace surfaces.

**The sharpest gate of the two sessions, because it is about CONTENT and not geometry:** render the
same corridor at **S2E01 and the Ministry of Peace is not on it** — and it does not go blank either,
it falls back to the authority-1 civic text, because a dark panel in a customs hall reads as a broken
prop. `deck.py` 32/32 → **40/40**.

**A defect the render caught and no assertion would have:** `signage.board()` builds with its own
`MOUNT_H_M` already in it, and I added it a second time — the board hung at **4.18 m**, over
everyone's head. A board on a wall at the wrong height still looks like a board on a wall.

### 5. `qtr_command` could light 10.3% of its own floor

`quarters.py` declared it *"takes the corridor's own MEASURED fittings … and takes the split with
them"* and was taking half of it: `interior_kit.corridor_section` lights **both** wall faces, and a
unit lit one. Plus `int(run / pitch)` truncated **1.9 into one lamp** for a 7.5 m depth.

**6 → 14 fittings, 10.3% → 100.0%**, `--gate-lighting` **18/21 → 19/21**, 1,224 triangles.
It blew the blacks out (`crushed` ×0.03) and the fill absorbed it: swept 1.521 → 0.150, **1.050 is
the only value that passes both** level and shape. `--gate-frames` back to **14 pass / 9 fail**.
INV-246.

### 6. THE BESPOKE INTERACTABLES WERE NEVER UNBUILT — THEY WERE UNNAMED

`--audit` read **`built generic 259/259, built bespoke 0/98`**. A ratio that clean is never
per-object; it is a convention. `rooms._fixture` writes `prop_<token>` and `provides()` recognised
only that, while `quarters.py` writes `qtr_locker`, `customs.py` writes `customs_desk`,
`command_control.py` writes `cc_console_face`. **The objects were there and the names had no
`prop_` in them.**

**The cure is not a prefix rule**, and that is the design decision: stripping `qtr_` off everything
makes `qtr_wall` a `wall` a player can press. Each module **declares** what it provides, in a table
that lives in the module, and **every row is verified against the module's own comment on the span
it names** — *"A Babcom terminal in every quarters"*, *"breather-mask dispenser beside the outer
door"*. `_selftest` builds one representative place per module through `deck.room_geometry` and
fails if a row names a span that place does not emit; **the control, an invented `qtr_not_a_thing`,
fires.**

| | before | after |
|---|---|---|
| declared uses resolving | 259 / 357 | **284 / 357** |
| `built bespoke` | **0 / 98** | **25 / 98** |
| places resolving NONE | 26 | **13** |

**The runtime had to be wired separately and nearly was not.** `sidecar()` took only names, so the
audit saw four interactables in a crew cabin and **the engine saw none** — the same
two-descriptions failure one layer further out. `_module_of` derives the module from the deck
group's own `<place>__` prefix. Verified: the sidecar returns `babcom_terminal`, `bunk`, `locker`,
`shower` for `qtr_command` and **rejects `qtr_wall` and `light_downlight`**. INV-248.

**Two corrections to this file's own next-list, both found by doing the work.** *"`babcom_terminal`
declared in nine places and built in none"* was **wrong** — `quarters.py` emits `qtr_babcom` in
every unit. And the near/absent split moves with the tables: *"26 built under another name, 72 never
built"* is now **14 and 59**.

### 7. THE NAMING-MISMATCH CLASS IS CLOSED — near-miss 26 → 0

Six more `PROVIDES` rows, in `customs.py` and `hospitality.py`, each verified against the module's
own code for the span.

| | 4c | 4d | **4e** |
|---|---|---|---|
| declared uses resolving | 259 / 357 | 284 / 357 | **302 / 357** |
| `built bespoke` | 0 / 98 | 25 / 98 | **43 / 98** |
| places resolving NONE | 26 | 13 | **5** |
| **built but misnamed** | **26** | 14 | **0** |

**`near` reaching zero is the finding.** Every one of the 55 declared uses still unresolved is
**genuinely absent** rather than merely misnamed — a different and far more expensive kind of work.
`--gate` fails if that number comes back.

**The row a mechanical search could not have proposed**, and it shows `near_miss`'s limit:
`bar_servery` → `bar_counter` share no underscore segment. The module's own comment states the
identity — *"`bar_servery`, not `bar_counter`: `rooms.py` emits `prop_bar_counter` … and
`bar_counter` is a SUFFIX of it"*. The rename was deliberate and written down at the time.
**Reading the module beat searching it.**

**Two deliberately NOT mapped**, and the reasons are the point. `bar_display` → `menu_display`: it
is *"the amber display, on the far wall"* beside a dartboard, as likely a scoreboard as a menu, and
mapping it would move the audit number **on a guess**. `council_chair_seat` → `delegate_bench`: the
module builds a **chair** where the register declares a **bench** — that disagreement belongs to
whoever owns the register. INV-249.

### 8. THE TERMINAL IS BUILT, AND THE LOG CAUGHT ME SHIPPING A LOGGED MISTAKE

INV-248 made the Babcom terminal usable; the render showed a **flat coloured rectangle**. It is now
a framed device with a recessed screen and a control shelf, on `signage.board()`'s own measured
ratios (bezel 6.8% of width, recess 0.035 m) rather than two new numbers.

**The first version built the bezel as four rails and `boundary_edges` read 5 non-manifold against
a plain box's 0.** That is the `portal_frame` defect session 3x paid to remove, and
`interior_kit._plate_with_hole` exists because of it — its docstring says the tiled construction
*"is the obvious construction and it is wrong"*. Rebuilt through it: 5 → **1**, because the shelf
and the face still ended on the same plane. **A shared plane is a shared plane whether it is two
rails or two panels.** Overlapping them → **0**, at no cost, because `boundary_edges` pairs edges by
vertex POSITION and interpenetrating solids share nothing. **72 triangles, open 0, non-manifold 0.**

**The screen blows out and it is measured, not felt:** the face is **×1.77 the wall beside it**
(V 0.713 against 0.515) on a material whose albedo is (0.052, 0.054, 0.062) and whose own name is
*"dark panel with lit content"*. `device_screen_glass` has **seven binds**, so its energy is a
station-wide change and is left for its own round. INV-251.

### NEXT SESSION — in priority order

1. **`device_screen_glass` blows out, on seven binds.** Measured in 4g: a cabin terminal's face is
   **×1.77 the wall beside it** where its own albedo (0.052, 0.054, 0.062) and its own name — *"dark
   panel with lit content"* — say it should be darker. It binds `prop_babcom_terminal`,
   `prop_monitor_wall`, `prop_tactical_display`, `customs_screen`, `bar_display`, `dress_screen` and
   `qtr_babcom_face`, so every screen on the station reads as a white slab. One value, seven places,
   and it needs a render round per family — which is why 4g measured it and stopped.
2. **NO SCREEN ON THE STATION HAS CONTENT.** The terminal is a lit blank.
   `reference/11-props-and-technology/identicard readout.webp` is authority 1 for what a station
   screen looks like — 4:3, portrait panel left at ~48% of width, ruled data field right, blue
   values, magenta for flagged fields — and `resident.identicard()` **already produces every one of
   those fields**. `signage.letter_mesh` already draws letterforms. The parts exist; nothing joins
   them. Note the format bridge: `signage` emits per-TRIANGLE group names and the room modules emit
   `(name, lo, hi)` spans — `deck._runs` is the existing converter.
3. **`walkable.py --deck blue/0/2 --use` FAILS**, and it is new information rather than a
   regression: before session 4d the runtime saw zero interactables in a crew cabin so there was
   nothing to fail on. The body ends **2.20 m from `qtr_command__qtr_locker`** and the eye ray finds
   nothing — almost certainly because the locker is inside a cabin and the body is in the corridor.
   `--deck blue/0/0 --use` still passes with its control.
4. **The 59 genuinely never built.** The long tail: `door` (7 places), `bunk` outside quarters,
   `valve`, `tank_gauge`, `identicard_reader`, `baggage_scanner`.
5. **The three observation dome interiors.** `station/bespoke.py` carries a full spec written by a
   previous agent, including the trap: `dressable_extent` returns a bounding box, which is right for
   every rectangular plan and **wrong for a circle** (corners at 1.41 R, through the window ring).
   Dome 1 **is** C&C's dome and `comand and contorl.webp` is authority 1 **from inside it**.
6. **`--gate-frames` 14/9.** `zocalo` (`crushed` ×0.01) and bespoke `hospitality` (p5 ×1.88) are the
   two closest. `plant` is a lighting-design problem, not an exposure one — leave it.
7. **`customs_north` at 59.7% floor coverage is NOT a defect** — `customs.py` asserts its own state
   and records the withdrawn experiment (*"210 coffers given lights put the frame at 18.9× its
   reference"*). The gate and the module disagree and someone has to rule.

tween them. The file
holds the force's size and shape, what an officer wears and carries, where the posts are, patrol
patterns, response times, the escalation ladder, the brig, law, the black market and Downbelow —
and the owner's scope brief names *"customs and immigration, law enforcement, crime, the black
market, Downbelow's underclass"* in the same breath as the NPCs.

`station/npc/security.py` — **43/43**, every negative control run and printed.

**It is deliberately not a second copy of the gazetteer.** Every number the gazetteer asserts about
geometry or timing is **recomputed from the built station**, and three came out different — INV-241:

| | gazetteer | recomputed | why |
|---|---|---|---|
| Grey outermost ring | r 402.2 m, 2,527 m round | **r 471.2 m, 2,961 m** (×1.17) | the addresses became hull-correct in 3z; the station moved under the number |
| beat walk speed | 1.3 m/s flat | **1.94 m/s** Grey, **1.12** Yellow | `walk_speed(g)` is a Froude gait model, v ∝ √(gL) |
| a 75 kg officer there | 108 kgf | **127 kgf** | 1.69 g, not 1.44 |
| response to a distant outer ring | 12–20 min | **22.3 min** worst | §2.6 priced three vehicle legs and added the walk in prose; this routes the whole journey on the same graph a resident commutes on |

**The two speed effects point opposite ways and both are real.** The gazetteer's instinct — foot
patrol in the heavy outer rings is punishing — is right, and the recomputation says the penalty is
in the officer's **weight**, not the clock. A Grey beat is *faster* and *harder*.

**§2.6's headline SURVIVES the recomputation, which is the point of doing it.** *"Response to the
outer ring of a distant sector is 12–20 minutes. To the Zócalo, from the standing post already
there, it is seconds."* Computed: the Zócalo answers **0 s** from its own post; Grey's
`atmos_monitor` is **22.3 min** from the nearest — which is **Green's council post**, not Security
Central, because Green is the sector adjacent to Grey on the axis.

**And the gazetteer contradicts itself one line apart** — §2.5 says *"~35 pairs"* and, in the same
row, *"the remaining 90"*, which is 45. **C-011**: `roving_pairs()` derives it and `report()` prints
the gap rather than picking the convenient reading.

### 2. NO ROSTER COULD EVER HAVE PUT A UNIFORM IN THE ZÓCALO

`resident.roster` casts a place's regulars from each resident's job, and it does that well — ask for
twelve at `security_central` and **seven** come back `role == "security"`; at `customs_north`,
**six** customs officers. **Ask at the Zócalo and none do** — merchants, financiers, visitors,
service — because an officer standing that post is employed *on patrol*, not *at the Zócalo*. In the
space the gazetteer calls "the most-policed civilian space on the station".

Asking deeper does not help: a place has a capacity, so `roster(security_central, ..., 300)` still
returns four. So `officer_pool` **searches the id space** on `schedule.role_for` — security is 500
of 155,000 humans, **one officer in ~270 ids** — and `role_for` is the cheap half of `resident()`:
**120 officers out of 32,406 candidate ids in 0.06 s**, measured.

**The fixed/roving split was forced by a render.** `populate` adds the **fixed** post to the
headcount and draws the **roving** share from the ambient crowd. `occupancy` is a crowd density and
knows nothing about duty, so folding a four-officer watch into the brig's headcount left room for
**zero** — the brig at 18:00 holds one person. The render proved it: **one League civilian, in a
detention block, no uniform.** After the split the same room exports four
`npc_cloth__ef_security_twill` bodies, one carrying `npc_cloth_trim__nightwatch_black`.
`docs/engine-brig-security.png` — grey twill, black leather standing collar and yoke, exactly the
service dress the two authority-1/2 reference frames describe.

### 3. THE ARMBAND WAS DECIDED TWICE AND THE RENDER USED THE OTHER ONE

`wears_armband` rolled `_u("security/nightwatch", id) < NIGHTWATCH_SHARE` and **passed every test in
the module** — while `costume.py` was independently rolling `_u(seed, "nw") <
NIGHTWATCH_SECURITY_RATE` to decide whether to hang the decal on the sleeve. Two descriptions of one
fact, agreeing only by luck, and **the render is driven by the other one**: a player would have seen
the band on a different officer from the one this module called banded. Hard rule 4, applied to a
boolean.

It now delegates to `costume.costume_for(...).nightwatch`, which gets the era right for free
(`era_active("nightwatch_visible")` — no armband before *The Fall of Night*). **The negative control
patches `costume.NIGHTWATCH_SECURITY_RATE`, a constant this module does not own**, and both the
share gate and the one-band-one-sleeve gate move with it — which is what proves the delegation is
live rather than decorative. Realised share over 300 officers: **36%**, inside FACTIONS.md §5.2's
150–200 of 500.

### 4. THE WALL WAS ONE 4 m PANEL AND NO GATE COULD SAY SO (merged from a background agent)

`density.py --shell` is the mirror of the machinery gate: it splits a room's shell into
**deck / soffit / wall** and scores each on **two** numbers — λ, and the **area-weighted median
unbroken run of surface** (`facet p50`) — both floored by the corridor kit built and measured on
every run.

**λ alone cannot say it, and that is the finding.** `articulate` ran a skirt, dado, rail, cornice,
six mullions a bay and four conduits round every wall — continuous elements, enormous line,
negligible area — carrying the wall to **×1.51 of the corridor's λ** while the field between them
stayed one 4 m rectangle. The *trim* hid the *field*.

| | wall facet p50 | deck facet p50 |
|---|---|---|
| before | 3.94 – 9.51 m | 5.26 – 12.80 m |
| after, all 78 | **0.83 – 1.21 m** | **0.53 – 0.85 m** |
| corridor as built | 0.99 m | 0.57 m |

**77/78 locations, 233/234 surfaces.** `density.py`'s old whole-station gate went **122/128 →
122/128** and an A/B moved no location by more than 0.5% of its bar — the gate that has been green
throughout is blind to this change, which is exactly why the new one exists. Three defects the
single panel box was hiding: the mullions were **buried** (0.035 inside a 0.045 panel), the deck had
the construction **inverted**, and the **end walls were never panelled at all** — and the end wall is
the one you walk in facing. INV-210. Craft **2 → 3**, honestly not 4: every plate still carries one
flat value, which is craft 3's own wording.

Cost: 1,206,552 → **1,607,208** triangles over the 78 rooms (+33%).

### 4b. THE PORT, AND THE STATION'S OWN VOICE

`docs/gazetteer/TRAFFIC-AND-CUSTOMS.md` is 910 lines including a section titled *"THE PORT AS A
LIVING SYSTEM — what to actually simulate"*, and **one file read it** — `station/aperture.py`, for
a hull cut. `station/traffic.py` now does. **27/27, and both negative controls caught a real bug in
my own gates before they fired.**

**The one thing that is not extrapolation.** 24 docking bays (authority 3, read from the schema and
not restated) × 24 h ÷ a 10 h mean occupancy = **57.6 movements a day**, against an unrelated
authority-4 source's *"over 50 to 60 ships"*. Two sources that know nothing about each other,
agreeing to within a couple of percent on a quantity neither was computed to match. The control
moves the turnaround to 24 h, gets 24.0, and the band gate **fires** — the agreement is evidence,
not an identity.

**Three things the arrival stream did not have**, measured against `schedule.arrival_times`, which
is what the crowd actually uses:

1. **It was flat.** 52 arrivals spread uniformly; §5.4 gives peak-to-trough **3:1**. `day_curve`
   measures **3.12:1** off the section's own stated intervals rather than a curve fitted to the
   words "about 3:1".
2. **It had one peak and the day has two.** `schedule.wave_pulse` reads 1.0 at 10:00 and **0.0 at
   18:00**. The evening peak is the outbound one — *"the Zócalo is busiest at station-evening and
   the port empties into it"*.
3. **There was no liner.** *"The liner is the event … build the day around it."* Measured: **689
   aboard at 10.8 h, 8.5 people a minute through one hall against a 0.28/min background.** That
   contrast is the crowdedness-and-isolation axis the owner named and a uniform stream cannot make
   it.

**AND THE PROJECT DISAGREES WITH ITSELF BY 3.6× ON SOULS A DAY — C-012.** `schedule.py` says 52 × 120
= **6,240**; the gazetteer's own manifest computes **1,739**. Neither is canon, and the sourced
figure constrains *movements*, not souls — both sit inside it there. The whole disagreement is
souls per arrival, 120 against 32, and a manifest whose commonest row is a freighter with 6–15 crew
cannot average 120. The transient-population cross-check **does not settle it in the expected
direction**: at a 9-day stay the manifest gives 15,651 against `FACTIONS.md`'s 45,000 and
`schedule.py` gives 56,160, so the manifest is *low* on that test. Recorded, not picked.

**Two bugs the controls found in my own gates**, both worth keeping:
`movements_per_day(berth_h=MEAN_BERTH_HOURS)` bound the default **at def time**, so the control
could set the module global to 24.0 and the function went on returning 57.6 — it printed **DOES NOT
FIRE** and was right to. And the flat-day control compared raw counts over two four-hour windows on
a 55-arrival sample, which is noise; it compares the ratio's collapse now, 3.50 shaped against 1.22
flat.

### 4c. THE INFORMATION LAYER — derived from the simulation, not written

CLAUDE.md's scope asks for *"an information layer the player can use — comms, ISN, propaganda,
signage, announcements"*. **Four of those five did not exist.** `station/broadcast.py`, **27/27**.

**An announcement is a view of a simulation, not a line of dialogue.** An arrival call names the
ship `traffic.py` actually berthed, in the tier it berthed in, at the hour it berthed, with the
passenger count it carried. A customs advisory fires a quarter-hour ahead of a liner and names its
real 689 passengers — **and a day with no liner gets no advisory, which is the control for it.** A
watch call names how many security `schedule.role_on_duty` says are on. **A different day says
different things**, asserted, because there is no script to drift from.

**The era lock is the sharpest part.** Every ISN bulletin and Ministry of Peace notice is tied to an
event in `costume.ERA_EVENTS`, so the same station renders three ways:

| datum | ISN bulletins | MiniPax notices |
|---|---|---|
| S2E01 | **0** | **0** |
| S2E22 (*The Fall of Night*) | 3 | 3 |
| S3E05, the datum | **4** | **3** |

`FACTIONS.md` §5.1 says *"any armband before The Fall of Night is an error"*; a Ministry of Peace
poster in a Season 1 customs hall is the same mistake, and it is now impossible. The era check
**delegates** to `costume.era_active` for the reason INV-240 records about the armband — a second
era clock is a second description of one fact, and the one that reaches a frame wins.

Written to `FACTIONS.md` §11.5's own build note, quoted in the docstring: the propaganda *"should
read as OFFICIAL AND REASONABLE … because that is what makes them sinister. Do not make them look
like villain posters."* Asserted: no exclamation marks, no villain vocabulary, and the tuning fork
is the authority-1 customs board carried verbatim. **And the tannoy does not reach your quarters**,
asserted — a station-wide public address is one a player cannot get away from.

118 timed announcements a day, 7 standing surfaces.

### 5. Gates, after the merge and the security work

`bespoke` 149/149 · `deck --selftest` 32/32 · `rooms` 755/755 · `test_materials_layer3` 34/34 ·
`interior_kit` OK · `density --shell` 77/78 · `populace` 67/67 · `resident` 44/44 · `costume` 90/90 ·
`security` 43/43.

### 6. WHAT IS STILL WRONG, MEASURED THIS SESSION

**`--gate-frames` is 13 pass / 10 fail / 0 unverifiable, and the frames are NOT stale** — every one
was re-rendered in `54534d7`. Six fail `p5` (shadows too bright), one the other way, three on
`crushed`. Measured here before handing it to an agent:

* **`glow_bloom` is INERT and is not the cause.** A/B on four rooms, 0.05 vs 0.0: p5 moved ≤5% and
  **twice in the wrong direction**. The obvious hypothesis is dead; recorded so nobody re-runs it.
* **A room is lit by a flat ambient, not by its fittings.** On `council_chamber`,
  `--fixture-energy 3.0 → 0` moves the median 0.129 → 0.091 (the fittings supply **29%**);
  `--ambient 2.951 → 0` moves it 0.129 → 0.040. A flat ambient gives every surface the same
  irradiance whichever way it faces, so **nothing in the room is in shadow**.
* **The rooms have almost no light fittings.** Counted from the exporter's own line:
  `brig` 4, `medlab_one` 4, `cargo_bays` 4, `transfer_systems` 4, `fabrication` 6 (28,472 tri),
  `mess_hall` 8 (25,236 tri) … against the assembled corridor deck's **850**. Independently,
  `docs/reference-values.md` §6.4 says our fittings are 3.6–5× too dim and the show's ceiling strip
  is 7.72× its wall where ours is 1.46×. **Two routes to the same conclusion.**
* **It does not generalise room to room.** The same 2-D grid on `cnc` behaves oppositely — raising
  the ambient *lowers* the median, because pixels recruited from below the floor arrive at the
  bottom of the measurable set. That is the non-invertible-median pathology `export_scene` already
  documents.

## Session 3z (last) — FOUR THINGS THE STATION COULD NOT DO, AND NOW CAN

### 1. TWO VOCABULARIES DESCRIBED ONE STATION AND ONLY ONE COULD BE ROUTED TO

`navigation.place_nodes` walked `schedule.PLACES` — 25 crowd regions, of which 17 are also
register keys — so **101 of `directory.PLACES`' 118 rows had no node in the navigation graph
at all**. A resident's `home` and `job` are register keys (`npc/resident.py` resolves them by
function), so for most of the station "walk to work" had no destination to walk to.

**Nothing caught it and nothing could.** The island report was clean throughout, because a node
that was never added cannot be stranded. `register_nodes` attaches all 118 at their own
`(sector, ring, deck, angle_deg, z_m)` — which is also a strictly better address than
`place_nodes`' `_u("nav/place", key) * 360.0`, a deterministic but arbitrary bearing it has to
invent because a schedule entry carries no angle.

118/118 register places now have a node. The gate has a negative control that computes what the
schedule vocabulary alone would give: **101 missing**.

### 2. A LIFT IS A VEHICLE, NOT A STAIRCASE — and this was the expensive one

Every scheduled line joined **adjacent stops directly**, and `add_transit` charges one wait and
one dwell per link. So the router made a passenger **get out, queue and get back in at every
intermediate stop**. Grey's shaft has 105 decks: **72.9 minutes to ride 382 m that takes 3.0.**

Nothing was wrong with any speed, distance or headway in the module — the ride times were right
the whole time. What was wrong is that the graph **had no way to express being aboard**.

`_car_layer` gives each line a parallel chain of nodes that live inside the car. `add_board`
joins platform to car for **half a wait and half a dwell in each direction**; `add_ride` joins
car to car for **ride time alone**. Any one-way journey traverses the boarding link exactly
twice, so it pays one whole wait and one whole dwell however many stops it passes.

The half-and-half split is arithmetic, not a fudge: it is the only division that leaves a
**one-stop hop costing exactly what it cost before**, so the change cannot be a general speed-up
hiding a modelling error. And `lift_ride_s` is linear in distance (1.5·dr/v_cap), so summing
per-deck rides along the chain equals one express ride **exactly**.

Applied to all four lines: radial shafts, core shuttle, guideway trams, ground trams.

**Commutes over 120 sampled residents, home to work:**

| | before | after |
|---|---|---|
| median | 44.1 min | **13.5 min** |
| p95 | 107.6 min | **23.9 min** |
| worst | 110.5 min | **24.8 min** (4.7 km, Blue quarters → zero-g maintenance) |

INV-100 records the derived lift fleet — round trip / two dwells, so Grey's 382 m shaft gets 10
cars and Green's 29 m gets 2, and the mean wait lands at 17–20 s everywhere. INV-101 records the
car layer.

### 3. A SEATED PERSON WAS A STANDING BODY DROPPED 0.42 m

`npc/animation.py` is 2,400 lines — a skeleton, a Froude-number gait ladder, walk/idle/sit/glide
clips — and CLAUDE.md names it among the twelve tested modules with **zero importers**. What
reached a frame was `body.build`'s bind pose for everybody, translated down for sitters. A
1.829 m figure with its feet 0.42 m through the deck and its knees inside the chair.

`populace._posed` is that importer. Seated → `sit_clip`, handed the seat's **own measured
height**: hips on the pan, feet at y = 0.011, figure 1.332 m against 1.829 standing, origin at
deck level like every other placement. A 0.62 m stool seats the same person exactly 0.22 m
higher than a 0.40 m bench. Standing → `idle_clip`, which carries a per-resident phase, so a room
of twelve is twelve weights and twelve breaths rather than a chorus line.

`docs/npc-seated-pose.png` is the side-on silhouette: hips at 90°, thighs horizontal, shins
vertical, feet flat, arms along the thighs.

**And the deck's gravity reaches the pose.** `place_gravity_at` resolves all 118 places —
**105 from a deck, 12 from the drum floor, 1 from the spine core**, 0.234 g to 1.693 g. It
returns its **source**, because a silent fallback is indistinguishable from a correct answer:
the drum floor is 278.3 m, which is 1.0000 g to ten figures, so twelve drum places came back at
Earth gravity and looked perfectly resolved while nothing had resolved them.

**INV-102 — a figure has a measured minimum standing gravity.** `idle_clip`'s sway scales by
`G0/g` with **no lower bound at all**; at 0.04 g it leans a human 0.52 m off centre and lifts
their feet off the deck. The bound is where the sway equals the **base of support** — hip offset
and outermost foot vertex, both read off the rig, never written down — which is 0.075 g for a
nominal human. Below it the figure glides, using the clip Kosh already needed. One place is
below it: the Mainstage power node, in the 18.3 m spine at z = 3000, at 0.022 g.

### 4. THE DOCKING BAYS HAVE AN OUTSIDE (agent, merged)

24 apertures cut into the hull **lathe** rather than subtracted afterwards, at the bays'
**fore-facing** mouths — which is a finding, not a choice: aft, the hull at the mouth plane is
already inboard of the whole bay band. 608 open edges, **every one on a bay rim**, 0 stray,
24/24 rims closed, 0 non-manifold, three negative controls that all fire, and
`--no-apertures` reproducing the old hull **byte for byte**. INV-103. Exterior 381,210 tri
(95.3% of budget), 41 draw calls.

### 5. MATERIALS ARE 100% FOR THE FIRST TIME

Interior coverage **353/368 → 368/368**, and `materials.py` **1467/1467**.

- `npc_suit*` had **no material at all** — every Vorlon rendered on the fallback. Value imported
  from `costume.PAKMARA_COWL_ANCHOR`, the one measured large rigid non-human shell in the corpus.
- The per-person wrapper span is renamed `<person>_npc_body`, and **the resolver is why**:
  fragments match by substring and longest wins, so binding the bare `npc_seated` would have been
  10 characters against `npc_hair`'s 8 and **every seated person's hair would have resolved to
  skin**. The gate caught exactly that — 18 competing claims.
- `prop_locker`, `prop_weapons_locker` → `furn_casework`, where `qtr_locker` already lives.
- `materials.py --export` was run. Without it the bindings exist in Python and the engine renders
  the glTF fallback, which is the trap this file records twice.

### 6. THE CORRIDOR SOFT FILL (agent, merged)

The corridor's key light had been **measured six sessions ago and never built**. A run of
shadowless spots on the deck's own centreline at 10 m, one every 1.8 m of arc, aimed radially
outward. The deck field goes **×0.65 → ×2.59** of the lit wall against the show's **×2.49**.
Six negative controls, all fire. Two of them did not fire on the first pass and both were real
defects in the gates. `docs/engine-deck-corridor.png` was **two content commits stale** — it
showed a blown-lens state that no longer reproduces — and is refreshed.

### 7. THE CORRIDOR HAS PEOPLE IN IT, AND THE DENSITY IS DERIVED

Every person this project had ever placed was placed in a **room**. A player spawned in the
corridor, walked its 126 m and met **nobody** — on a station of 250,000, in the one space the
scope names twice.

The density is derived from three things this repository can recompute:

1. `schedule.RESIDENT_TOTAL` = **250,000** (authority 1, the opening narration)
2. **50.8 min/day** — the mean time a resident spends walking in corridors, measured by walking
   each resident's **own** 24-hour schedule (`resident.where_at` hour by hour) and pricing every
   change of place through the nav graph, counting only `walk`/`stair`/`door` links. Not the
   commute: the whole day, meals and recreation included, which is why it is five times the
   5.0 min a one-way commute spends on foot.
3. **825,066 m²** of corridor — 317,333 m of ring at `PROVISIONAL`'s own width, over 251 decks.

250,000 × 50.8/1440 = **8,812 walking at any instant**, over 825,066 m², is **1.07 per 100 m²**
— one person every 36 m. **That is sparse and it is supposed to be.**
`FALLBACK_PER_100M2["transit"]` is 12.0, eleven times this, which would put 914 people on one
Blue deck. The station simply has 0.83 km² of corridor. What makes a corridor feel busy is the
**distribution**, which `corridor_headcount` takes from the occupancy of the places each deck
serves: 134 on Blue's six-room docking cluster, 4 on a plant deck.

Everyone is **walking** — `walk_clip` at a per-resident phase, the first use of the Froude gait
ladder for anything — and half go each way round the ring.

Two measured defects found while building it, both caught by gates written alongside:

- **The stride advance comes off; the bob and the sway do not.** `walk_clip`'s root moves in
  three axes and they are not the same kind of motion. Taking all three off lifted all eight
  phases 0.104–0.143 m: eighty people hovering 12 cm over the deck.
- **A body's half-width is measured, not `BODY_R_M`.** That constant is a nominal human's 0.32 m
  and this station has fifteen species; a wide shoulder went 0.10 m through the end wall.

`docs/engine-corridor-populated.png` is the frame, and it is the first here where a player would
meet somebody. **Honest craft read at 6 m:** the near figure is LOD 4 at 484 triangles and its
shoulders and head show it. That is the documented bake-time compromise — `corridor_lod` picks
for the 33 m **mean** distance down a 66 m sight line — and the fix for the close encounter is
runtime LOD in `npc.gd`, not a bigger bake.

### 8. EVERY SINGLE-ROOM Z-CLUSTER ON THE STATION WAS SEALED (agent, merged)

`deck_plan` swept 24 phases of the structural grid and **`break`ed on the first phase with no
unopened room**. On a one-room cluster that is the first phase tried — so the door stayed
wherever the bay division put it. The fit test asks only whether the leaf lands inside the
room's **wall**, which a door 1.33 m off centre does in a 7 m room. A body steering straight at
the room crosses the corridor wall 0.14 m along that line and meets the jamb.

`walkable.py --deck` measured **0.70–0.74 m of progress** into every single-room cluster —
corridor half-width less the capsule radius — including `grey/0/24 → thieves_guild`, **which
this file records PASSING in 3v**. A silent regression on everything except `blue/0/0`, whose
goto target happens to sit at `dx = 0.00`.

Fixed by ranking all 24 phases instead of stopping: rooms opened first, then doors nearest their
room's centre. `grey/0/24` now walks 4.3 m → 0.05 m, matching its 3v record exactly.

The agent also added **ten locations** — reactor hall, fuel bunkerage, coolant gallery, generator
hall, heat exchanger hall, comms operations, cargo transfer deck, mooring gallery, EVA lock,
gunnery control — with **six of the audit's ten addresses corrected** after re-verification at
401 samples per span. `coolant_gallery` was the bad one: at the audit's z 450–950 Yellow carries
**one** deck stack, so ring 3 does not exist anywhere in that band. INV-104.

### WHERE THE STATION IS, as of the end of 3z

`python3 station/deck.py --sweep`, which is the only gate here that asks a whole-station question:

```
71 decks in the gazetteer, 90 z-clusters assembled across them
  90 assemble, 0 fail, 0 deferred, 1 on heightfield ground
  128 of 128 locations on an assembled cluster, 128 with a door or on ground, 0 without
  0 decks with a hole in the floor
  963 people walking in the corridors and 449 in the rooms, over 45,179 m2 of assembled
  corridor: 2.13 per 100 m2 against the station-wide 1.07 the derivation gives
  49 module-owned places assembled as GENERIC bays (18 have a bespoke builder unused)
  58,660 collision triangles across the ring decks — the walkable station is 632,100
```

Suites: navigation 93/93, populace 50/50, deck 28/28, rooms 673/673, bespoke 79/79,
directory **830/830**, validate 32/32, materials **1467/1467**, layer3 **34/34** (interior
material coverage **406/406**), aperture 22/22, transit 85/85, resident 44/44, schedule 100/100,
crowd 67/67, body 501/501, export_scene 243/243.

### 9. THE INHABITANTS ARE SOLID, AND THE ENGINE IS HANDED A THIRD OF WHAT IT WAS

**A player walked through all 147 of them.** Measured, not assumed: `walkable.py --deck blue/0/0
--bump` steers the body straight at a named resident, and it reached **0.03 m** — through them.

**Why they were not solid is the part worth keeping.** `rooms.is_solid` excludes every `npc_` group
deliberately, and the exclusion is right: static collision is generated **once**, so an inhabitant
baked into it is a permanent statue. That function's comment ends *"NPCs get their own capsules when
they get their own movement"*. `populace.body_capsule` measures the capsule off the individual's own
posed mesh — the **widest** horizontal extent, 0.269 m for a human against 0.206 at the chest, and
the difference is the arms — and `npc.gd::_give_body` builds it at runtime on a node that follows
them, upright along the body's **own** up, which on a spun ring points at the axis and not at
world +Y.

The gate and its control are both CI steps now:

> *a person is SOLID: walking straight at Amis Keffer (r 0.36 m) the body is stopped 0.71 m away;
> control: with their capsule off it reaches 0.03 m and walks through them.*

**And the draw-call gate measured the wrong artefact.** It counts feature groups in the hull
manifest — 41 of 64 — which is right for the exterior. It is not what `export_gltf` writes: **one
mesh, one node and one primitive per OBJ group**. Measured on the shipped `.glb` the first time
anybody looked: **1,262 primitives, 1,052 of them people** — twelve per inhabitant, because
`body.py` tags twelve parts. `NPC_BUDGET["max_draw_calls"]` is 32.

The twelve names exist so each part binds its own material, and the materials are only ever two or
three. `populace._by_material` merges the **runs** — never reordering, so no triangle moves:
**1,262 → 376, and 1,052 people → 166.** Negative control run: patched out and rebuilt, the new gate
reads 1,262 / 600 FAIL; restored, 376 / 600 PASS. INV-105, INV-106.

### 10. WHY NPCs STILL DO NOT MOVE, AND EXACTLY WHAT WOULD FIX IT

This is the one thing left in the "living station" column and it is now a **specified** task rather
than an open problem. Three measurements settle the design:

1. **A rigid per-part transform cannot walk.** `npc.gd` already transforms each person's parts every
   physics frame, so the obvious extension is to drive the twelve parts from a clip. Measured: the
   worst vertex is **145 mm** out, at the knee, because `npc_skin_leg` is ONE part spanning hip to
   ankle and a rigid body cannot bend in the middle.
2. **Splitting each part at its dominant bone closes it to 14 mm**, in **19 pieces**, over all eight
   phases (`animation.rigid_track`, gated, with the 145 mm figure as its negative control). Every
   walking species is under 100 mm; the Gaim are worst at 90 mm because the encounter-suit plan is
   rigid plates rather than a limbed body.
3. **But 19 pieces a person does not ship.** At twelve it was already 1,262 primitives on one deck.
   19 would be worse than the state the merge just fixed.

**So the answer is not more pieces, it is instancing, and the arithmetic is favourable.** Emit the
eight walk phases ONCE per (species, LOD) as shared meshes, and make each corridor walker a glTF
**node referencing** one of them — which the format supports natively and `export_gltf` already
half does, since it writes one node per mesh. On `blue/0/0`:

| | today | shared phase set |
|---|---|---|
| walker geometry | 134 unique bodies × 484 tri = **64,856** | 8 species × 8 phases × 484 = **30,976**, shared |
| walker primitives | 134 | **64**, instanced |
| animation | none | free — swap the node's mesh index per frame |

It is a net **triangle saving and a 2× primitive saving**, and it animates. The cost is that walkers
become their species' nominal body rather than their own — which is what every real crowd system
does, and room occupants keep their unique meshes. The work is in `populace` (emit walkers as
instance references rather than baked triangles), `export_gltf` (nodes sharing a mesh index) and
`npc.gd` (advance along the ring, swap the phase).

### 11. THE CROWD WORKS, AND THE 80x REGRESSION WAS A TYPO

**Verified end to end.** `walkable.py --deck blue/0/0` now reports, in one line:

> *134 walkers instanced from the shared crowd library and they WALK: **5,966 m** covered between
> them, 0 triangles of their own in the deck*

The derivation predicted 5,800 m — 134 walkers at their own gaits' 1.45 m/s over 1,800 frames.
Measured 5,966. Confirmed to 3%. `docs/engine-crowd-instanced.png` is the frame.

**And the 80x regression was not what I said it was, three times.** The gate had gone from 10.2 s
to over 200 s for 120 physics frames. Blamed in order — the instanced crowd (an A/B timed out
identically with the crowd **off**), the collision capsules (`--no-npc-collision` changed nothing),
and `npc.gd`'s per-frame transform loop (an early-out changed nothing). All three wrong.

It was a **parse error**. `for w in _walkers` over an untyped `Array` makes `w` a Variant, so
`var d := w.omega * delta` could not infer its type, the whole script failed to load, and every
call from `walk.gd` threw — **23,933 stack traces to stdout**. With `_walkers: Array[Walker]` the
gate is **10.2 s with people on, identical to people off**; the full two-pass run is 110 s.

Found by running Godot **unbuffered to a file** instead of capturing its output. Three rounds of
guessing against one look at what it actually printed. That is the lesson worth keeping.

**THE GATE THAT LET IT HIDE, and this is the reusable half.** Every NPC assertion in
`deck_verdict` was guarded by `if "noticed" in d`. When `npc.gd` stopped loading, the tokens
simply stopped appearing and **every deck went on passing** — for six runs, while nobody on the
station existed at runtime. *A gate that disappears when the thing it tests is broken is worse
than no gate, because it prints PASS.* It now fails, and its control runs at unit level in a
second rather than through a Godot session the defect itself makes too slow to finish. INV-133.

### 11b. (superseded — kept because the measurement is still true)

Measured this session, cleanly, one Godot process at a time, on `blue/0/0`:

| | 120 physics frames |
|---|---|
| bare deck, no people | **10.2 s** (startup 8.2 s, so **0.017 s/frame** — 1,800 frames is 30 s, which matches CLAUDE.md's 38 s) |
| `--no-people` | **10.2 s** |
| `--no-npc-collision` | **> 200 s** |
| people on | **> 200 s** |

So the cost is **`npc.gd::_physics_process`**, which writes `m.global_transform`
for every part of every person every frame — and it is **not** the capsules (disabling them
changes nothing) and **not** the instanced crowd (the A/B timed out identically with the crowd
off). I attributed it to the crowd earlier in the session and that was wrong.

It has been there since `npc.gd` was written; CLAUDE.md's 38 s predates decks having people on
them. **This is the first thing to fix**, because a gate that takes half an hour stops being run,
and CI runs it on every push. The obvious shape: only transform a person whose yaw actually
changed — `notice_m` is 6 m, so on a 134-person deck that is a handful, not all of them.

### 12. WHAT THE TWO AGENTS LANDED

**23 more module-owned places assemble as themselves** — 49 generic bays → **26**, and people in
rooms **449 → 1,053**. Three causes, none of them what the reason string said: furniture in the
doorway rather than the wall; `room_shell` centring on the **bounding box** so `alien_sector`'s
door had **no floor under it at all** (and `_mouth_clear` called that OPEN, because nothing
obstructs a probe cast into a void); and three modules with no doorway at all. INV-110–112.

**The machinery stopped being boxes** — `density.py --machinery`, the gate that was missing,
reads **0/78 → 74/78** locations at or above their own shell's line density, machinery λ
**1.669 → 7.012**, for **+0.3%** on the deck. `density.py` scored a whole location and 123 of 128
passed with every machine a box, because the shell is 95% of the surface. INV-130–132.

**Two closure ledgers are now on the record and ratcheted, and both should shrink:**
`bespoke.SHELL_OPEN_EDGES` — **3,693 open edges across 8 composed shells** (council_chamber 1,592,
hospitality 824, zocalo 736, command_control 342, docking_bay 151, customs 48). `docking_bay` was
attempted and **reverted rather than ship 160 holes**, 80 of them mid-bay on a deck emblem laid
with no rim — `dressing._cyl`'s defect in a second costume.

**And the correctness note that will bite next:** *collision does not follow the composition*.
`build_collision` still builds a generic box shell and derives solid props from `rooms.build`, so
a player now **sees** the Zocalo and **stands in** a generic bay. Every `walkable.py` PASS is real
but is testing the generic shell; the bespoke geometry is render-only.

### 13. THE WARDROBE, AND A DEFECT THE ROUND TEST WAS HIDING

`npc/costume.py` is 2,800 lines of measured wardrobe — an albedo, roughness, metallic, authority
and source frame per fabric — and its only importer was `materials.py`, for **two constants**.
Everybody was naked. It exports **53 materials** now, 32 at authority 1, and clothing the station
costs **2.7%**: the cloth replaces the skin it covers.

Reaching a **posed** body took three separations, each real:

- `animation.rig` built its own mesh from `body.py`, so posed people stayed nude while the
  rest-pose probe was clothed — populace's own gate caught the 64-vertex mismatch.
- **Bones from the body, skin from the wardrobe.** Passing the dressed mesh to `_skeleton` killed
  the Minbari: a robe replaces the legs with a skirt, so the leg-ring search returned nothing.
- `_bind` refused four accessories with *"body.py has grown a part this module cannot skin"*. It
  had not; costume.py had. Belt, skirt, collar and cowl declare their chains now.

**And every seated person on the station was sitting backwards.** `_place_body` maps local +Z to
`(−sin, cos)`, so facing `(fx, fz)` needs `atan2(−fx, fz)`; the seat used `atan2(−sx, −sz)` —
correct in z and **mirrored in x**. On a bench at x = −2.61 the sitter faced the wall with 0.33 m
of their back through it. It survived because the placement test was a **symmetric circle**, which
cannot tell forwards from backwards; it is the body's real placed bounds now, and the desk
placement had the same inversion.

Three more, all caught by gates rather than by looking: `_by_material` truncated
`npc_cloth__civ_dark_warm` to `npc_cloth`, which nothing binds; the mirror-smooth gate tested a
NAME word list and rejected `npc_metal__psi_chrome`, whose metallic is 1.00; and `material_specs`
needed a **third** source, because the Nightwatch armband is written by the mesh builder as a
literal and is in neither `SETS` nor any sample.

### What is next, in order

1. ~~**The walk gate's 80x regression**~~ — **FIXED (§11): a parse error, not the people loop.**
   10.2 s with people on, the same as off. The crowd is verified at 5,966 m.
2. ~~**Collision must follow the composition**~~ — **DONE (3z).** `deck.room_geometry` is the single
   answer to "what is in this room" and both `build_deck` and `build_collision` call it. The trap it
   nearly walked into is worth keeping: a composed room's module geometry is ONE WELDED MESH, so
   `prop_boxes`' connected-component rule collapsed the Zocalo's 702,840 triangles into **one solid
   filling the room** — 1 box against the generic build's 39. Taking the `dress_*` spans alone gives
   41, and the shell stays the smooth shell. INV-134.
3. ~~**The shared phase-mesh crowd**~~ — **DONE and verified (§11).** 5,966 m covered, 0
   triangles of their own in the deck, 112 shared bodies for the whole station.
4. ~~**W5, the loop**~~ — **DONE**, and `walkable.py --deck blue/0/0` has been reporting all four
   steps for a while. Routing exists and is gated (118/118 places,
   every sampled resident's home and job mutually reachable). Poses exist and reach a frame,
   including a walk cycle. What does not exist: nobody **moves**. `npc.gd` already transforms each
   person rigidly about their own pivot every physics frame, so **translation along a route is
   available today** — what it lacks is the route in the actor JSON and the clip sampled at more
   than one frame. Emit `route` (a list of world points from `NavGraph.path`) and the eight
   `walk_clip` phases per person, and the corridor walks.
5. ~~**Runtime LOD for people**~~ — **DONE (3z).** Three rungs derived from `NPC_BUDGET`'s own
   bands: `18 m → chain lod 2, 45 m → lod 4, 400 m → lod 8`, 307,456 triangles of library shared by
   the whole station. Measured on `blue/0/0`: **LOD 2:3/4:5/8:126, nearest 6.2 m** — the figure a
   player looks at gained 4.3× its triangles and the other 126 got cheaper; deck primitives went
   376 → 341. The near 0–6 m band is **capped** at the 6–18 m level and says so: shipping chain
   level 0 would mean 510,720 triangles resident to draw the four agents that band ever holds.
   INV-230. `docs/engine-crowd-lod.png` is the frame, and it is still not AAA at 6 m — chain lod 2
   is `features='no_detail'`, so the hands are mitts and the face has none.
6. **`bespoke.compose` for the last 26.** 20 have no builder at all (`components` x14,
   `interior_kit` x3, `core_tube` x2, `interior` x1); of the 6 that do, 5 are `plant` — whose
   walkable band is 82.2 x 1.80 m against a 92 x 442 m bay, so it needs a placement decision
   rather than a near-end declaration — and 1 is `docking_bay`, blocked on its 151 open edges.
7. **`directory.py`'s `docking_bays` footprint — now C-010.** The register puts a 140 m bay at z 7115 and the
   sphere is only wide enough for a 254.2 m deck over **58 m of that**. Either the bay is 140 m
   and mis-addressed or INV-022 is wrong. `docking_bay._selftest` ratchets it at ≥40% so it
   cannot get worse. **A real fork, not mine to rule on.**
8. ~~**Props are still not solid.**~~ **WRONG — they have been solid since 3v.**
   `collision.prop_boxes` derives them from the room's own emitted mesh and `deck.py --selftest`
   prints *"114 furniture boxes, 1,368 collision triangles for them"*. This entry was inherited
   from an older list and is left here struck through rather than deleted, because a next-session
   list that quietly loses items is how a real one gets distrusted.
9. **The ionization vanes.** Three support rings measured off `other map 4.jpg` (z 1620/1907/2198,
   agreeing to 1.4% in spacing); the six vanes do not resolve in any frame. The agent recorded the
   measurement and did **not** build them, because the counts live only in `00-MASTER.md` §1.3 and
   writing them as literals would put a canon count in a second place.

## Session 3x (last) — EVERY DOORWAY ON THE STATION WAS AN OPEN SURFACE, AND NOW NONE IS

`judge-3w` measured **1,470 open boundary edges in the corridor** of `blue/0/0`, 245 at
each of six doorways, and called every door aperture an unclosed cut. It was right about
the count. The cause turned out to be four separate defects stacked at the same place,
and finding them needed one thing done first.

### 0. The tagging, which is what made the rest findable

`door_assembly` merged `bulkhead`, `door_frame` and `door_leaf` with **no `tag()` block**
while every other piece in `interior_kit` has had one for sessions. So 1,248 triangles a
deck — six gaps of 208 — were inside `ring_arc`'s returned range and outside every span
it returned. They exported as `deck_untagged`, matched no material rule, took no light,
and Godot gave them the glTF fallback: **the surface a player looks straight at while
walking through a doorway was the one surface in the corridor with no material on it.**

Nothing had to be authored. `materials.py` already binds `bulkhead` → `kit_wall_plate`
and `door_frame` → `kit_pilaster`. The geometry simply never said what it was.
**Whole-deck coverage: 1,248 untagged → 0.** And with the pieces named, the open edges
attribute cleanly — `door_frame` 1,056, `bulkhead` 414 — instead of vanishing into an
anonymous `corridor` blob.

**Why no gate caught it, which is the more useful half.** `interior_kit._selftest` has
always asserted that every triangle carries a tag, and it asserted it against
`corridor_section(21.6)` — **no doors**. A coverage check that never builds the case with
the gap is a coverage check of the easy half. It now runs four configurations: plain,
wall door, bulkhead door, both.

### 1. `_plate_with_hole` rimmed the wrong loops

The caps come from `_polygon_difference`, which peels the outline one aperture edge at a
time and lands split points partway along an outline edge. The rims were built from the
loops the **caller** passed in, which know nothing about those splits, and two short
edges do not weld to one long one at any tolerance.

It now **rims from the pieces' own boundary** — an edge walked backwards by the piece
beside it is interior and gets no wall; an edge used once is real silhouette wherever it
came from — so the rim inherits whatever subdivision the peel produced. That also closes
the slivers the peel drops for being under 4 mm²: their neighbours' edges become boundary
and get rimmed, leaving a notch rather than a hole.

`_insert_collinear` is the second half and it does **not** affect closure — measured both
ways, not reasoned about. Disabling it leaves `door_frame` at 0 open edges and **16
non-manifold** ones. Non-manifold is a face buried in the solid or two faces coincident,
which is a depth-sort coin toss, which is judge-3w's "ragged sawtooths" and the
parallelogram it photographed floating in front of a wall.

### 2. `portal_frame` was five prisms sharing coincident faces

Found **by the new gate, immediately**, which is how you know the gate is real. Adjacent
prisms share a quad: 16 edges with four faces on them per frame, **828 on one deck**, at
the corner a player walks past 414 times a lap. Rebuilt through the same machinery, now
factored out as `_shell_from_pieces`: 16 → 0, **and 8,832 fewer triangles**, because the
coincident faces were geometry nobody could ever see.

### 3. `dressing._cyl` was open at the bottom AND inside-out

The last 102 open edges on the deck were all here — conduit drops, pipe bands, bollards,
six an object over seventeen objects. Measuring that found the worse one beside it:
**`_cyl` wound every one of its 24 faces INWARD.** `_box` next to it is 12/12 outward and
`interior_kit._prism` is 12/12; this was **0/24**. With backface culling on that is an
object you look straight through — the failure CLAUDE.md records `_box` having had for
several sessions of exterior work, where it only changed the shading, now found indoors
where it does not.

### 4. Every vestibule stood 0.219 m proud inside the corridor

The other half of judge-3w's door finding: *"the dark jamb pieces are the neighbouring
room's wall panelling standing proud through the corridor's white wall."* Literally what
it is. `build_deck` ended each **render** vestibule at the **measured collision** plane
(1.0806 m) while the corridor's **render** wall is at `corridor_width_m / 2` = 1.30 m, so
a 2.1 m passage projected 0.219 m into a 3.0 m corridor at all six doors, showing its top
face and both flanks. Same 0.219 m as the collision hole earlier in the session,
**inherited**: the shell was correctly moved onto the measured plane and this expression
was copied along with it.

**The render passage stops at the render wall; the collision passage stops at the
collision wall.** They are different planes and one number cannot serve both.

### The score

| | judge-3w | now |
|---|---|---|
| open boundary edges, `blue/0/0` | **1,572** | **0** |
| untagged triangles | 1,248 | **0** |
| `portal_frame` non-manifold edges | 16 each, 828 a deck | **0** |
| deck render triangles | 597,418 | **589,216** (−1.4%) |
| ring-deck collision, whole station | 75,642 | **35,746** (−53%) |

### The gates, and every one has a negative control that fires

* `interior_kit._selftest` — closure **and** manifoldness on `door_frame`, `door_leaf`,
  both bulkhead sections, `portal_frame`; tag coverage in four door configurations;
  `door_frame` and `bulkhead` added to the signed-volume winding list. Control: disabling
  `_insert_collinear` → *"door_frame has 16 non-manifold edges against a bar of 0"*.
* `dressing._selftest` — `_box` and `_cyl` each closed, manifold, 100% outward, plus a
  whole dressed room with no open edges. Control: restoring the shipped cylinder fails
  three of them — *6 open edges, 0/18 outward, 24 open edges over the room*.
* `deck._selftest` — no vestibule stands proud of the corridor wall, measured on the
  **shipped mesh** via a new `stats["vestibule_spans"]`. The first version of this gate
  built a probe by passing the correct plane in, which is an assertion that cannot fail;
  a vestibule cannot be found by group name either, because its groups are the corridor
  kit's own **on purpose** — that is what makes it take the same materials. Control:
  restoring the shipped plane → *"a vestibule reaches z=7120.224, 0.219 m past the render
  wall face"*.

`boundary_edges` **moved from `interior` into `interior_kit`** and is re-exported. It had
to: the kit builds the pieces and `interior` imports the kit, so the module that could
measure closure was the one that could not be called from the module that needed it.
That is why the kit's closure gate was a **ray cast upward** — a test that cannot see an
open edge in a vertical surface beside the corridor, and did not, for as long as every
door on the station had 176 of them.

### The budget work from 3w, integrated

* `player.gd` sets `_cam.fov = 70.0`. Godot's default is 75 **vertical** (verified against
  the engine), so the build was rendering 5° more than anything measured it — 6,774
  triangles the budget never saw. **INV-083 closed.**
* `collision.MAX_SAG_M = STEP_TOLERANCE_M`. The shell sized its angular step from a 1 mm
  sag while `floor_steps` certifies a floor at 5 mm, and sag scales as the square of the
  step: 977 steps built where 437 suffice. Tying the constants together means nobody can
  edit one and leave the other. **Ring decks 75,642 → 35,746 collision triangles, −53%,
  and the deck re-walks to the same numbers** — `traverse_m 125.94`, `offfloor 0/1800`.
  The shell's floor lip rose 0.72 mm → 1.85 mm against a 5 mm bar. **INV-085 updated.**
* `deck.py --sweep`'s headline said *"75,642 collision triangles for the whole walkable
  station"* and summed ring decks only — the drum takes the `continue` above that sum.
  **Wrong by 8.6×.** It now prints per-tile, lod0 and the station: 35,746 + 573,440 =
  **609,186**, and the drum is 94% of it.
* `budget.py`'s cached `RING_DECK_COLLISION_TRIS` drifted **by design** and its
  `--station` gate caught it, which is what a cached number is for. The regex that reads
  the sweep's prose also broke on the new wording, and a parse failure was reporting as an
  off-by-one drift; the two now print differently.
* CI gets a **separate always-green step** for the drift check. `Performance budgets` is
  **expected red** until the content moves — three content bounds went over the moment
  3w measured them honestly — and a step that must stay green cannot share a run with one
  that must not.

### The frames, rendered through Godot + lavapipe on the assembled deck and READ

| frame | what it shows |
|---|---|
| `docs/judge3x-door-2m2.png` | the doorway at the rubric's **half** distance, judge-3w's own subject. The aperture reads as one continuous chamfered pressure-door reveal, two leaves with a centre seam, a control plate that is now a single clean box rather than two slivers |
| `docs/judge3x-door-4m-vestibule-proud.png` | the vestibule defect, **before** |
| `docs/judge3x-door-4m.png` | the same camera, **after** |
| `docs/judge3x-corridor-5m.png` | the corridor down the arc: portal rhythm, pilaster strips, downlights, deck grid, chamfered soffit. It reads as a Babylon 5 corridor |

## NEXT SESSION — START HERE

**The geometry at a doorway is now correct and the CRAFT there is not.** Both statements
come from looking at `docs/judge3x-door-2m2.png`, and the second is the whole of what is
left at that subject.

### 1. THE ALBEDOS ARE NOT THE DEFECT — I REPORTED THIS WRONG AND IT IS CORRECTED

Earlier in this session I recorded that the door frame sitting 2% from the wall it is set into
was the craft problem. **It is the show's own number.** `docs/reference-values.md` measures
`grey level 1.webp`'s pilaster face at **×1.016 of its wall plate**, so `materials.kit_pilaster`
is right and copying it was right.

What separates a door from its wall in the show is a **profile, not a pigment**. Cut across the
corridor's own jamb at y 0.400–0.460 the assembly runs shadow groove **×0.64** → proud nosing
**×1.27** → bullnose **×1.22** → deep reveal **×0.27** — a **×4.7 spread inside 0.077 of frame
width at flat albedo**. `Vorlon and captain.webp`, the only frame in the set that shows a door
leaf in a wall, gives the same shape harder: pale frame band ×2.43–2.47, jamb edge ×2.68–2.82,
reveals ×0.16–0.32, **local contrast ×8.5–17** — while the leaf itself is only ×1.30–1.76 of its
wall and most of that is the room's light gradient.

**So the work is relief and shadow, not repainting.** A frame band at ~9.5% of leaf width and a
reveal deep enough to go dark is what makes a door read.

### 2. THE p5 ×11.09 FIGURE WAS MY RIG, NOT THE BUILD — ALSO CORRECTED

I reported the walkable corridor as "too bright, no shadow, p5 ×11.09 against a ×1.29 band, zero
crushed pixels", with a caveat that the frame was lit by a hand-written rig. **The caveat was the
whole story.** Two independent measurements:

| frame | rig | p5 |
|---|---|---|
| `docs/judge3x-corridor-5m.png` | ad-hoc, 4 omnis + ambient 0.34 | **×11.09 FAIL** |
| `docs/engine-deck-corridor.png` | the deck's own 850 fittings | **×1.45** |
| `docs/judge3w-corridor-wall-1m.png` | shipped fittings | **×1.03, passes every band** |

**The rig was 7.6× hot in the shadows.** `tools/export_scene.py --shot deck` now exists, so the
walkable build can be rendered under its own fixtures and this cannot happen again by accident.

What IS still wrong, measured on the shipped-rig frame: **4.64% clipped against a 3.69% cap**, and
p5 ×1.45 against a ×1.29 band. Both real, both small, both the opposite sign from what I said.

### 2b. The ladder, which is the real craft gap and is measured

`docs/reference-values.md` §6.4, ratios to each frame's own lit wall plate:

| element | SHOW × wall | OURS × wall |
|---|---|---|
| ceiling / soffit | 0.23 – 0.32 | **1.12** |
| dark horizontal band | 0.23 – 0.30 | **0.86 – 1.05** |
| floor field | **2.49** | **0.69** |
| wall light fitting | **4.70** | 1.30 |
| ceiling light strip | **7.72** | 1.46 |

**Four rungs wrong in a consistent direction: ceiling ~4× too bright, dark bands ~4× too bright,
floor ~3.6× too dark, fittings ~3.6–5× too dim. Everything is pulled toward the wall.** And the
dark horizontals in the show are **shielded recesses, not dark paint** — an affine fit
`Y = 0.054·wall + 0.0054` beats a through-origin fit 2.8×, so the recess takes about 5% of the key.

**THE UNITS TRAP, and it invalidates a comparison anyone would make next:** every ratio in
`materials.PROVENANCE` is balanced-V, and a render matches in **linear luminance**. `kit_deck`'s
recorded "1.6× the wall" is **2.49×** in luminance. Convert before acting.

### 3. THE MODULE-OWNED PLACES — MEASURED IN 3y, AND THE ANSWER IS *COMPOSE*, NOT SWAP

3x recorded that `deck.build_deck` never consults `place["module"]`, so module-owned places are
assembled as generic `rooms.py` bays, and called it the largest fidelity gap on the station. 3y set
out to wire the dispatch. **Measuring first inverted the conclusion twice.**

**The first comparison was against the wrong thing.** Bespoke extent against `rooms.bay_span_m`
says not one of the 25 fits — `plant` is 92 × 442 m against a 13.5 × 9.6 bay. Meaningless:
`bay_span_m` sizes a representative *generic* bay and is not a constraint the ring imposes. The
ring's real constraint is the arc between consecutive doors, and on `blue/0/0` those are 480, 185,
295, 148, 74 and 148 m against a widest bespoke width of 42 m. **Zero collisions.**

**The second comparison is the one that decides.** Built both ways for all 25 places with a
builder: **generic 390,432 triangles against bespoke 210,702 — ×0.54.**

**THE BESPOKE MODULES ARE SHELLS.** `rooms.build` runs `dressing` and `populace` inside itself, so
a generic bay arrives furnished and inhabited; `docking_bay.docking_bay` is 3,740 triangles of bay
and *nothing in it*, against the generic 38,728. **A wholesale swap would take 46% of the station's
detail off.** The 3x finding is right about shape and identity and wrong about richness.

It is not uniform, which is the useful part:

| bespoke is RICHER | ratio | bespoke is POORER | ratio |
|---|---|---|---|
| `alien_sector` | ×3.69 | `docking_bay` | ×0.10 |
| `zocalo` / `shops_kiosks` | ×1.45 | `command_control` | ×0.12 |
| `customs` | ×0.94–1.41 | `council_chamber` | ×0.12 |
| `plant` / `air_compressors` | ×1.13 | `hospitality` | ×0.19 |

**THE NEXT INCREMENT, and it is now a decision with numbers behind it: bespoke shell PLUS generic
dressing.** The module gives a place its true shape, scale and identity; `dressing.dress()` and
`populace` fill it. Both already take a room's dimensions rather than a `rooms.build` internal, so
the composition is available without restructuring either.

Two facts a builder will need and should not have to rediscover:

* **The frames differ.** `rooms.build` centres a room on its origin (x ±5.96, z ±4.06 for
  `docking_bays`) with the floor at y = −0.14. `docking_bay.docking_bay` puts its floor at y = 0
  and runs z from −0.75 to +140.75. Bespoke geometry must be recentred before placement or the room
  lands 70 m up the station's axis.
* **`R.build(door_at=)` is what connects a room to the corridor**, and no bespoke builder takes it.
  A composed room needs its near face opened by the assembler, not by the module.

**What 3y actually landed:** the registry moved from `tools/export_scene.py` to
`station/bespoke.py` (unchanged; export_scene imports it, 233/233 still green) because `station/`
may not import from `tools/`. It gains `compare()` — the measurement above, kept runnable — and
nine assertions. And **the substitution is no longer silent**: `--sweep` prints *"27 module-owned
places assembled as GENERIC bays (21 of them have a bespoke builder that was not used)"*, and
`deck._selftest` asserts the reporting is present with a stated reason. Negative control: dropping
the record fails with *"0 reported against 2 module-owned places"*. Geometry is byte-identical —
591,352 triangles, same vertex hash. This changed what the build says about itself, not what it is.

### 4. Still open from judge-3w, unchanged

* `fixture_lights` cannot see `<room>__`-prefixed fittings and aims every spot at world
  −Y. On a spun ring −Y is not down.
* `docking_bays__prop_bay_control_booth` and `docking_bays__prop_deck_marking` match no
  material rule — the last two fallback groups on the deck. 13 more unresolved names are
  `<room>__npc_standing_N`, the person's **own** group, which ends with zero faces after
  the part split and is therefore harmless.
* `godot/.godot/` is gitignored, so a fresh clone renders the fallback material.
* The drum mounts the interior environment inside a 556 m cavity.
* One corridor class on 66/66 decks — `concourse` at 9.0 m is never asked for.
* 19 of 118 locations sit in secondary z-clusters the sweep does not build.
* **Nothing is interactable except the door.**

### 5. Where the walkable station stands

`python3 station/deck.py --sweep`:

```
66 assemble, 0 fail, 1 on heightfield ground
99 locations on an assembled cluster, 87 with a door, 0 without
0 decks with a hole in the floor
35,746 collision triangles across the ring decks, 51,200 more in the drum's ground
per tile (573,440 for the whole drum at lod0) -- the walkable station is 609,186
```

`20/23` performance budgets within bound. The three reds — frustum structure, structure
share of frame, resident triangles — are **content**, and the remedy is to move the
content, not the limit. `resident triangles` at 327% is one `.glb` loaded whole: there is
no streaming, no LOD and no occlusion culling in `godot/` at all, and that is a system,
not a texture.

---

## Session 3v — the furniture is solid, and HALF THE STATION IS STARVED OF IT

**Props and fixtures now collide.** `collision.prop_boxes` derives the boxes from the
room's own emitted mesh — connected components of shared vertices are the primitives
`_box`/`_cyl` wrote, and primitives that touch are one object, so a chair's seat, back
and legs merge into a chair. `docking_bays`: **1,632 primitives → 10 objects**, largest
6.25 m. Not a second list recorded by the builders: this project has been bitten twice
by two descriptions of one thing drifting apart, so it reads the mesh.

`rooms.is_solid` is now the **one** definition of "a thing standing in the room, as
opposed to the room" — used by `build`'s density trial *and* by the collision builder.
They were different sets for as long as it took to notice: collision took only `dress_`
furniture, so a player walked through every **fixture** — a bar's till, a medlab's
scanner — while the walkability guarantee had been computed as though they were solid.
55 boxes → **88**. A guarantee computed against a different world than the one that
ships is not a guarantee.

**And people are not furniture.** The first version of `is_solid` counted `npc_` groups,
which baked all 134 inhabitants into the station's **static** collision as immovable
obstacles. A person you bump into and who never moves is worse than one you walk
through: it is a statue where a resident should be, and it is *permanent*, because
static collision is generated once. Measured with them solid, `mess_hall` and
`happy_daze` read **unwalkable** — they are not, and the rooms were never the problem.
Excluding them also *raised* the box count 88 → 97, because bodies had been merging with
nearby furniture into single blobs. Gated, because the failure is invisible: everything
still assembles, walks and renders.

### THE FINDING, and it is a content finding, not a bug

`rooms.build` picks the highest dressing density at which a body can still cross the
room, falling 1.0 → 0.75 → 0.5 → 0.3 → 0.15 → 0.0. Measured over all 87 walkable rooms
for the first time (`build(..., report=)`):

| density | rooms (before) | after the services fix below |
|---|---|---|
| **1.0** | 43 | 43 |
| 0.75 | 16 | 16 |
| 0.5 | 15 | 15 |
| 0.3 | 7 | **10** |
| 0.15 | 3 | 3 |
| **0.0 — empty** | **3** | **0** |

**No room on the station is empty any more**, and the fix was one `max()`. Services —
wall panels and conduit drops — were placed as `n = max(2, int(run / 2.2 * density))`, so
**two went up at every density above zero**. The ladder therefore had no rung on which the
furniture survived and the services did not. In a marginal room it is the services that
close the path, because `rooms.walkable` dilates every obstacle by the walker's radius
and a 0.14 m panel becomes a 1.04 m block: `bay_elevators` measured unwalkable with
**four** extra objects and walkable with none, so its entire dressing was discarded to
remove two shallow panels. **A floor under a scale factor is a scale factor that does not
reach zero** — the same defect this module's own comment had already caught once, at
`density=0.0`, and fixed only for that one value.

The station now carries **109,200 triangles of furniture**.

### And then the real fix: bays sized for the furniture that goes in them

`bay_span_m` derived a bay from the props ranked along its walls and took the **larger** of
that and the fixture width. A fixture and a shelf stand on the same floor, so their needs
**add**. It now asks `dressing.wall_band_m(arch)` — the module that does the placing — for
the depth its scheme takes off each wall, and sizes for `fixtures + 2 × band + a lane`.

| density | before | services fix | **bays sized for furniture** |
|---|---|---|---|
| **1.0** | 43 | 43 | **71** |
| 0.75 | 16 | 16 | 9 |
| 0.5 | 15 | 15 | 7 |
| 0.3 | 7 | 10 | 0 |
| 0.15 | 3 | 3 | 0 |
| 0.0 | 3 | 0 | 0 |

**43 → 71 of 87 rooms at full density, and 109,200 → 363,354 triangles of furniture.** The
blast radius is bounded because `build` clamps to `w = min(w_full, bay)`: a bay can only
grow into the footprint the gazetteer already gave it. `budget` 15/15, `directory` 747/747.

### Which broke two things, and both were caught rather than noticed

**`_solid` was reading the wrong list, and looked exactly like a working guard.** The new
"is this NPC standing inside a fitting" check read `v, t, g` — which in `populate` are the
**bodies being built**, empty at that point — instead of `room_v, room_t, room_g`. An
obstacle list that is always empty rejects nothing. This is the project's most-repeated
defect and the reason `rooms.py`'s counter-check exists: it kept failing while the guard
"passed". Placement is now also verified **on the emitted body**, not on the point it was
asked for, because a standing figure's bounding box is not centred on its origin.

**`floor_holes` called five tabletops a hole in the deck.** It demanded the first surface
under a ray be the floor itself, which was fine until the furniture became solid — a ray
cast down through a table hits the table. Standing on a table is not falling through the
deck. It now reports a hole only for **nothing underfoot, or something below the floor**.
Verified still able to fail: 70 holes with the vestibules deliberately broken.

### The people, fixed: 96 → 278 placed, 32 empty rooms → 0

`occupancy` wanted **320** people across the 87 walkable rooms at 1300 and **96** arrived,
with 32 rooms holding nobody. Two causes, and the first one hid the second:

**A seat that did not work out deleted the person.** Every failure path in the seat and
desk branches was a bare `continue`, so an occupant whose assigned seat was taken or out of
bounds was dropped rather than falling through to stand somewhere. Once the bays were sized
to hold their furniture there were seats everywhere, so most people were *assigned* one —
and the standing placement underneath was never reached at all. **Assignment is a
preference, not a filter.**

**Sample-and-reject cannot find a small target.** The standing placement drew random points
and tested them, which works in an empty room and stops working when the room is full: a
room with machinery down its spine has its clear floor in two narrow strips, and a dart is
a poor way to find a strip. Adding tries did not help and neither did biasing the draw,
because the problem was never where the darts landed. `_free_spots` now **enumerates** the
free floor the way `rooms.walkable` finds a path — grid the room, keep the cells a body's
width clear of everything solid, order by hash with the reserved lane first. `lowg_bays`
has **343 of 640 cells free**; it was getting nobody.

**278 of 320 placed, every room occupied.** The 42 short are people for whom no clear spot
remained after the others took theirs, which is a room being full rather than a bug.

### The doors open — the first thing on this station a player uses

```
PASS  deck blue/0/0 -- a body spawns in the corridor and WALKS INTO docking_bays
      (6.3 m -> 0.04 m), never leaving the floor
      control: with the doors inert the body is stopped 5.26 m short.
               The door is what opens the way.
```

Until now a pressure door was a **picture of a door**: the collision shell cut a permanent
hole at every doorway — which is what let a body walk from the corridor into a room — and
the leaves the player could see were a shut slab baked into the corridor mesh. So you
walked through a closed door. Same defect as the vestibule with no floor and the room wall
with no aperture, arriving a third time: **physics and pixels disagreeing about whether
there is a wall.**

| piece | what it is |
|---|---|
| `doorleaf_<key>_0/_1` | the two moving leaves, each its **own** mesh, because they travel in opposite directions. `kit.door_leaf(which=)` |
| `doorpanel_<key>` | the solid a closed door **is**, its own group in the collision shell so exactly it can be switched off |
| `godot/scripts/door.gd` | opens on proximity, slides the leaves, disables the panel once they have actually started moving |

**Which way a leaf travels is read off the geometry** — away from the midpoint of the pair,
flattened onto the plane the door stands in. Nothing has to say "left" and "right", so
nothing can say it wrong.

**THE NEGATIVE CONTROL IS THE POINT.** A body reaching the room proves the route is open;
it does **not** prove the door opened it, because a door-shaped hole gives the same number.
`walkable.py --deck` now runs the same walk twice — once with the doors live, once with
them inert — and **fails if both pass**. Doors live: 0.04 m. Doors inert: stopped 5.26 m
short.

Two things fixed on the way, both found by measuring rather than looking:

* `place_doors` reported the door plane as the **wall face**, but `corridor_section` sets
  its assembly back by `fd/2 − 0.06` so the frame stands proud of the wall. The
  separately-placed leaves were therefore **0.16 m out of their own frame** — close enough
  to look right in a wide shot and wrong at the distance you open a door from.
* The verdict line assembled `door_open` and then **overwrote it** with `=` instead of
  appending, so the number never printed.

Frame: `scratchpad/door_open.png` — the leaves parted into the jambs, three people standing
in the bay beyond.

### Still open

### W5 — THE LOOP CLOSES. Spawn → walk → the door opens → five people look up

```
PASS  deck blue/0/0 -- a body spawns in the corridor and WALKS INTO docking_bays
      (6.3 m -> 0.04 m), never leaving the floor,
      5 of the room look up (123 deg turned, 4 deg off)
      control: with the doors inert the body is stopped 5.26 m short.
```

278 people stood in 87 rooms and not one knew a player existed: they were geometry baked
into the merged room mesh, the same reason a pressure door was a picture of a door. A room
whose people never react is a diorama.

| piece | what it does |
|---|---|
| `populace._place_body(actors=)` | **records the yaw it baked**, per person, with species and pose |
| `<deck>_actors.json` | the cast list, written beside the mesh by `walkable.py` |
| `godot/scripts/npc.gd` | turns each body about **its own axis** toward the player inside 6 m, at 2.2 rad/s |

**Why a sidecar and not the geometry.** A body is baked into world-space triangles, so
nothing downstream can recover which way somebody faces by looking at them — and a person
who turns towards you has to be turned *from* somewhere. Asking the geometry to give back
what the generator already knew is how the door leaves ended up 0.16 m out of their frame.

**"Did they turn" is not the question, and asking it would have shipped a bug.** A body
rotated by a *wrong* yaw convention turns exactly as far as one rotated correctly and
reports the same number. So the gate reports **`facing_err_deg`** — the angle between where
the nearest inhabitant ends up looking and the direction to the player. It reads **3.8°**.

And it caught one on the way: `deck.py` first added the room's angle to each actor's yaw,
which would have turned every inhabitant by however far round the ring their room sits.
`_place_local` is **not** a rotation in the room's (x, z) plane — it wraps room x onto an
arc and leaves room z as the station axis, so a body's heading relative to
(axial, tangential) is preserved and the ring angle enters through `npc.gd` deriving those
two directions from the body's own position.

Turning about the body's own axis needs `translate(pivot) · rotate · translate(−pivot)`,
because the vertices are already at world positions — a plain node rotation swings the
person round the station's axis instead of their heels.

Frame: `scratchpad/w5b.png`, the bay from where the player arrives — three figures, one
visibly non-human, which is `npc/body.py`'s species mix reaching a frame for the first
time. **The turn itself is measured, not pictured:** the preview bakes the generated pose,
so the evidence for it is the headless number.

### 77% OF THE DECK HAD NO MATERIAL AND THE CORRIDOR EMITTED NO LIGHT — my bug

An agent judging the build against the AAA rubric found it, and it traces to one line I wrote
two commits ago. `deck.py` labelled all 458,400 corridor triangles `corridor` — a single group.
That "fixed" untagged geometry by replacing **fourteen real names with one fake one**:

* `materials.py` resolves by **substring**, and its 429 rules match `corridor` **zero** times, so
  77% of a deck rendered with the glTF fallback material;
* `FIXTURE_LIGHTING` is an **exact-name** table, so the corridor's `light_downlight`,
  `light_pilaster_strip` and `light_portal_head` fittings were invisible to it and **the deck
  emitted no light sources at all** while 850 fittings sat in the mesh.

`interior_kit` had recorded the spans the whole time — **741 of them over 14 names** in an 8°
arc — and `ring_arc` simply never returned them. It does now, and the deck OBJ carries **198
distinct group names** including all three `light_*` groups.

The deck selftest's own check missed it and had to be replaced: `sum(hi−lo) <= len(t)` was a
proxy that held only while the corridor was one flat group. The kit's tags **nest** —
`wall_assembly` contains `skirt`, `rail_band` and the rest — so real spans legitimately sum to
more than the mesh. It now asserts every span is in range and that >99% of triangles are named.

### The drum walks — 99 of 118 locations are on a walkable surface

```
PASS  drum green/1/0  a body spawns on hedge at the_garden, walks 126.0 m over
      25 ground patches and never leaves the floor
python3 station/deck.py --sweep
  66 assemble, 0 fail, 0 deferred, 1 on heightfield ground
  99 locations on an assembled cluster, 87 with a door, 0 without
```

`station/drum_walk.py` (agent-built, verified here: 23/23, and `--sabotage lift` genuinely fails
at 21/23 with +0.581 m). **It inverts `collision.py`'s rule and that is the point** — a corridor
needs a *smooth* shell because its millimetre relief is decoration; the drum needs the *shape of
its own ground*, because there the relief is the content. It authors no terrain: it calls
`drum_ground.ground_patch`, the function the render ground is built from. **Its gate is SLOPE,
not lip** — the drum rises 0.24 m between lattice points, which is 3.5°, which is a field.

CI now runs `deck.py --sweep` and `drum_walk.py --selftest` as well.

### Still open

* **Nothing else is interactable.** `directory.interacts` declares verbs for all 118
  locations — `bay_door`, `cargo_crane`, `till`, `comms_channel` — and the door is the only
  one that does anything.
* **The drum is not walkable** — `green/1`, an open 8 km barrel whose floor is
  `drum_ground`'s heightfield. Deferred by name in `deck.NOT_RING_DECKS`, not forgotten.
* **19 of 106 non-drum locations are in secondary z-clusters** and are not on an assembled
  deck. `build_deck` takes a `z_m`; the sweep only walks the busiest cluster per deck.
* **W5, the loop** — nothing is interactable and no NPC reacts. `directory.interacts`
  declares the verbs; none of them do anything.

**44 of 87 rooms are furniture-starved, and the worst of them are the ones that should
be fullest:** `mess_hall`, `happy_daze` and `bar_unnamed` at **0.15**, `casino` and
`brig` at **0.3**. `bay_elevators`, `fuel_stores` and `hazard_tanks` come out **empty** —
and not because dressing has nothing for them: `dressing.stats` offers `bay_elevators`
**533 objects at 21.2 per m²**. The trial rejects every density and falls to zero.

**The diagnosis, and it is two rules disagreeing.** `bay_span_m` sizes a bay from *the
props ranked along its walls* — that is its whole design, "a bay is exactly the room its
contents need". The walkability trial then *removes* props until a path exists. So the
sizing says "this room holds N things" and the trial says "then nobody can walk in it",
and the loser is the furniture. A bar at 15% density is the exact gap the owner named
when they sent the Starfield frames.

The fix is not to lower the walkability bar — a room you cannot cross is worse. It is
that **`bay_span_m` must size for its contents *plus* a lane**, so full density passes by
construction. That is the next thing, and it is worth more than any other single change
to how the station reads: it is 44 rooms.

## Session 3v (later) — the station, not a deck

```
python3 station/deck.py --sweep
  67 decks in the gazetteer
  66 assemble, 0 fail, 1 deferred
     deferred green/1/0: the habitat drum -- an open 8 km barrel, not a corridor
     deck; its walkable surface is drum_ground's heightfield
  87 locations on an assembled cluster, 87 with a door, 0 without
  0 decks with a hole in the floor
  74,044 collision triangles for the whole walkable station
```

Verified in the engine on a deck never tested before, in another sector at another
radius: `PASS deck grey/0/24 -- a body spawns in the corridor and WALKS INTO thieves_guild
(4.3 m -> 0.05 m), never leaving the floor`.

### Three bugs between "one deck works" and "the station works"

**1. A deck NUMBER is not a deck INDEX.** 14 of 67 decks died on `IndexError`. Grey
Sector's locations carry the deck numbers the show uses — 40, 55, **80** — and the
generated stack for Grey ring 0 has 23 decks; Yellow reaches deck 30 with 7. Same
mistake as placing a corridor at a z-cluster's bucket label: **a name used as an
index.** `deck_index` decides per ring — if every number the gazetteer uses is a valid
index they *are* the indices (Blue, Red, Green ring 0), otherwise the distinct numbers
are ranked and the rank is the index, which preserves which deck is above which.

**2. Green ring 1 is not a failure, it is the drum.** The Garden, the townscape, the
tram, the spokes. `NOT_RING_DECKS` names it and says why, so the sweep's numbers stay
honest instead of counting it as broken.

**3. The corridor's phase decided who got a door, and it was set by accident.** A door
takes over a whole bay and must clear the portal frames at both ends, so it can only sit
in the middle ~1.0 m of a 3.07 m bay. 16 rooms came out **sealed** — and the offending
offset was **identically 1.32 m on unrelated decks**, which is what gave it away: an arc
of `angle ± 12°` divided into 2.5° sections puts every room *exactly on a section
boundary*, so every door was shoved to the same edge of its window. `lifts` is 3.0 m
across; 1.32 m is further than the room is wide.

The arc's start is padding, not a measurement — a free choice. `deck_plan` now sweeps
the phase and keeps the one that opens the most rooms, extending the span to keep
coverage. **16 sealed rooms → 0.** That is what an architect does with a structural
grid: slide it until the doors land where the rooms are.

### And one design rule the five broken decks taught

**A door decision cannot be made twice.** It is made from the corridor's bay division,
and a door that does not fit has to be left out of the corridor, the vestibule, the
room's aperture *and* the collision opening together. Made separately in two places it
went one way in the render and the other in the shell: five decks had a room whose
collision carried a doorway and a vestibule out in the wall next door, and whose render
was a sealed box. `deck_plan` decides once and both assemblies read it.

`interior.arc_sections`/`place_doors` exist so that decision can be made **without
building 458,000 triangles of corridor to find out where the doors would go.**

### Scale, honestly

87 locations sit on an assembled cluster. The gazetteer has 118, of which 12 are the
drum's. The rest are in **secondary z-clusters** on decks whose primary cluster is what
gets assembled — reachable by passing `z_m`, not yet swept. So: the walkable station is
87 rooms across 66 decks, not 118.

## Session 3v — the body walks, and what stopped it was millimetres

**W1 IS DONE AND W2 IS HALF DONE.** A body spawns in Blue ring 0 deck 0, stands, and walks
**125.93 m** round the ring corridor in thirty seconds without once leaving the floor
(`offfloor=0/1800`). It cannot yet get *into* anything — see the bottom of this section.

### What stopped it, and it was none of the things it looked like

Session 3u left a body that stood on the assembled deck reporting `on_floor=true` and moved
**1 mm** in all four headings. The candidates were the rooms, the arc size, double precision, and
7 km from the origin. **It was none of them.** Casting rays into the corridor's own cross-section
gave the answer in one pass:

| surface | kit y | what it is |
|---|---|---|
| grid tiles | **+0.022** | `deck_grid`, proud, 38 mm seams between them |
| deck panel | 0.000 | `deck_panel`'s plates |
| lighting channel | **−0.066** | 0.18 m wide, down the exact centreline |

A 0.35 m capsule dropped on the centreline straddles a 66 mm slot; Godot returns an internal-edge
normal tilted 18° across the corridor and `move_and_slide` spends all six iterations sliding
against a lip it cannot climb. Moving the spawn off the channel does not help — 0.62 m along there
is a 22 mm step at every tile seam.

**The proof, before writing anything:** a smooth shell at the same radius, same distance from the
origin, same 344°, walked at **4.200 m/s** on the first try. It is the millimetres.

### `station/collision.py` — a player walks on a surface built for walking on

The fix every shipping game uses, and it was needed here for two independent reasons: the physical
one above, and that trimesh collision over 458,160 corridor triangles is not affordable at runtime.

**The profile is not written down — it is MEASURED** off `interior_kit.corridor_section` by ray
casting, so if the kit's floor or walls move the shell moves with them. Hard rule 4 applied to the
third thing that has to agree.

| | value | why that one |
|---|---|---|
| floor | +0.022 m | the top of the proud tiles — what a boot rests on, not the panel under them |
| half width | 1.080 m | the pinch **at a portal frame**, not the 1.255 m between them |
| cost | 7,816 tri | **1.5%** of the corridor's 458,160 render triangles |

### The gate, and it fails on the content it was written for

`walkable.py --deck` assembles a deck, walks it, and asserts distance covered and frames off the
floor. Same deck, same spawn, collision taken from the render mesh as before:

| | moved_1s | legs | traverse |
|---|---|---|---|
| **without the shell** | 0.000 | 0.00 / 0.00 / 0.00 / 0.00 | 0.00 m |
| **with it** | 4.200 | 0.73 / 4.20 / 0.73 / 4.20 | 41.93 m |

`on_floor=true` in **both**. That is what this project has been shipping: a body that reports it is
standing on the floor and cannot move a millimetre. The axial legs stop at 0.73 m because the
corridor is 2.16 m clear and the capsule is 0.35 m — correct, not a snag.

### Two more defects, both found by reading the trace rather than the code

* **The heading frame degenerated at two points on every ring.** `player.gd` derived forward from
  `up.cross(Vector3.RIGHT)`, which is **zero** wherever `up` is parallel to world X — ring angles 0
  and 180, one of which is where this deck's own spawn sits. On a spun habitat `up` is radial and
  therefore always perpendicular to the spin axis, so +Z can never degenerate. Use the axis the
  geometry guarantees, not the one that usually works.
* **The four heading legs were not independent.** Leg 0 walked the body into the axial wall and
  left it there, so leg 1 measured a body already jammed and scored a clear corridor as zero.

### Two gates were wrong on the way, and that is the recurring lesson

* `floor_steps` first walked **the centreline alone** and called the render corridor smooth to
  0.6 mm — the centreline is the inside of the channel, the one continuous lane on the deck. Nine
  lanes now: **shell 0.72 mm, render 22.20 mm**, which is the tile height exactly. Same species of
  error as rendering at one distance only.
* The shell-agrees-with-render check first compared triangle-radius statistics, and **I caught
  myself widening its tolerances to make it pass.** Replaced with a cast: the shell floor must equal
  the median surface a body meets over the width and length it can occupy. Bumping the shell 10 mm
  moves it 0.13 → 9.87 mm and fails, demonstrated.

### WHAT DOES NOT WORK YET — there is no door, and the corridor is in the wrong place

`ring_arc` is called with `doors=()`, so the corridor is a closed tube. A player walks 126 m of
station and cannot get into any of it. **W2 is half done: "go a long way" yes, "go somewhere" no.**

And the reason is not just a missing hole — it is measured, and it is a placement bug:

```
corridor   world z 7118.70 .. 7121.30   (placed at the cluster label, 7120)
rooms      world z 7109.99 .. 7120.01   (actually centred at z_m = 7115)
```

`z_clusters` returns `round(z/40)*40`, a **bucket label**, and `build_deck` places the corridor at
it. So the corridor tube passes through the far end of every room — 0.36 m into `docking_bays`,
**1.31 m into `plantroom_bay`**. Per-room overlap, measured:

| room | angle | far end z | overlap with corridor |
|---|---|---|---|
| `plantroom_bay` | 260° | 7120.01 | 1.31 m |
| `docking_bays` | 0° | 7119.06 | 0.36 m |
| `lowg_bays`, `vorlon_berth` | 130°, 320° | 7118.78 | 0.08 m |
| `mooring_clamps` | 180° | 7118.18 | — (0.5 m short) |
| `bay_elevators` | 300° | 7118.03 | — (0.7 m short) |

**The first of those three is now done** (see below). What remains is the doors and the vestibules.

### The corridor no longer runs through the rooms — `corridor_z_m`

A bucket label is a name for a group, not a position. The corridor is now placed just beyond the
furthest room's outer wall, from `rooms.build`'s own sizing (`room_extent_m` clamped by
`bay_span_m`, plus `WALL_T_M`) — **not** from the gazetteer footprint, which is a location's full
extent and an order of magnitude too big (`docking_bays` is 360° × 140 m).

| | corridor z | near face | rooms cut |
|---|---|---|---|
| **old** — rounded cluster label | 7120.00 | 7118.70 | **4 of 6** — `plantroom_bay` 1.31 m, `docking_bays` 0.36 m, `lowg_bays` and `vorlon_berth` 0.08 m |
| **new** — derived from the rooms | 7121.31 | 7120.01 | **0 of 6**, and flush with the deepest |

Asserted both ways: the corridor must clear every room *and* its near face must be flush with the
deepest one, so the check cannot be satisfied by parking the corridor a kilometre away. **Nothing
could have failed for this before** — the walk test only asks whether a body moves, and
interpenetrating geometry is perfectly walkable. It was visible in a render and wrong in a
simulation: two reasons and no gate.

### What is left of W2, precisely

Rooms now fall **0.00 to 1.98 m** short of the corridor wall (`bay_elevators` is the widest,
`plantroom_bay` is flush). So:

1. **Cut the doors.** `corridor_section` **already takes `doors=((z, side), ...)`** — `courses=False`
   omits that bay's wall body entirely and `door_assembly` fills it with a bulkhead, frame and leaf.
   `ring_arc` simply never passes them. In the corridor's kit frame +x maps to world +z, so a room
   at lower z is **`side = -1`**, and kit z maps to angle, so the door's `dz` is the room's angle
   converted to arc length.
2. **Vestibules** for the 0–1.98 m shortfall, which is what a station has anyway.
3. **An opening in the room's far wall.** `rooms.build` emits each wall as a single `_box`; an
   aperture means four boxes around it. Contained, but it is a real change to a shared generator.
4. **Matching openings and vestibule floors in the collision shell** — otherwise the player walks up
   to a door they can see through and cannot pass.

## Session 3t — what shadow coverage buys, and why the level then fights the shape

**`--ambient` did nothing on the drum shot.** Documented, honoured by the exterior and interior
shots, silently dropped by `build_drum` — three renders at 0.55, 0.30 and 0.15 came back with an
identical p5 of 0.0458. Same defect as `--light-gain` on the exterior, found the same way: by
disbelieving a number that would not move. Fixed.

**The hypothesis was wrong and the measurement said so.** Ambient does *not* set the shadow floor:
0.15 → 0.02 moves p5 only 0.0458 → 0.0427. Shadow **count** is the lever.

| shadow lights | p5 | crushed | render |
|---|---|---|---|
| 2 (current default) | 0.0560 | 0.20% | 11 s |
| 6 | 0.0470 | 1.23% | 14 s |
| 20 | 0.0337 | 1.84% | 31 s |
| **32** | **0.0207** | **3.86%** | 47 s |
| *reference `garden.png`* | *0.0180* | *5.63%* | |

**At 32 lights the frame passes all six distribution checks** — p5 ×1.16 inside the ×1.29 band —
and it is the first frame in this project to do so besides the one that already did.
`docs/engine-drum-garden-shadows.png`.

**And then the level cannot be recovered.** Its median is ×0.49 instead of ×1.40, and gain
2.0/3.0/4.0 give medians ×0.98/×1.42/×1.82 with p5 0.0298/0.0467/0.0653 — the same lights light the
shadows, so every stop that fixes the level undoes the shape. **Getting both needs light that is
brighter where it lands and no brighter where it does not**: tighter falloff, more directional
fittings. That is a rig change rather than a number, and it is the real content of layer 4b.

The default stays at 2 deliberately: all three `DRUM_CALIBRATION` framings recorded their exposures
at 2, and raising it silently would invalidate every one without re-deriving anything.

## Session 3s — layer 2 goes 16/118 -> 118/118, and layers 3 and 4 follow it

Every one of the 118 locations clears its derived detail floor. Layers 1, 2, 3 and 4 all read
COMPLETE; layer 5 (props & function) is the current layer at 0/118.

**The exterior "fork" was not a fork.** It looked like one because meeting the components' floor
was priced with panel relief at 0.17 m of line per triangle, which would indeed have cost the whole
400,000 allotment. Ribs on the plates that already exist -- radiator blades, comms plate, cooling
fins -- deliver the same line for a fraction of it. Exterior sits at **377,530 / 400,000 (94.4%)**
with the hull untouched and no budget raised. Nothing needed deciding.

**The tram exposed a real defect in the metric.** Its floor was 3.030 while its own cost rule allows
15,000 triangles, which buy 0.678 -- the metric demanded four and a half times what the budget it
cites will fund, because `scene_budget` hands every module the whole scene's allotment as though it
were the only thing in it. Close enough for `interior` (6.1 of the drum's 6.2 million m2), badly
wrong for a 10,892 m2 vehicle. `density.MODULE_ALLOTMENT` now reads a module's own declared cap
where it has one.

**Components now decimate.** The ribs took them from 46% of lod7 to 93%, and `lod.py`'s "coarsest
under a tenth of finest" refused the chain -- correctly, since a 1.5 m stiffener is invisible at the
distance lod7 is drawn from. Rib count rides `--greeble-detail`, the knob that already means "how
much small surface decoration does this level carry", so the two cannot disagree about what far away
means. `lod.py`'s "the model matches what the generator wrote" then caught that I had taught the
model to decimate and not the generator.

**And the density gate's headline assertion had to be retired.** It read "THE GATE FAILS ON THE
CONTENT AS IT STANDS", which was right when 102 of 118 were blockout and became a demand that the
content stay broken. Replaced by the property that does not expire: a plain box must still fail at
every location's floor. Demonstrated failing -- inflate the box's line density and it fires on 90
locations.

## Session 3s (earlier) — layer 2 goes 16/118 -> 108/118

Ten places remain, and nine of them are `components` — the exterior fittings behind the budget
fork the owner has not ruled on. Every interior module now clears its derived detail floor.

### One caveat, stated because it is the defect this session keeps finding

**`interior`'s pass is geometry the drum shot does not show.** The ring frames were added to
`interior.drum_interior()`'s band shell, and `export_scene.drum_parts` **replaces that shell with
`drum_ground.visible_set()`** — its own comment says so, because emitting both would z-fight across
four and a half million square metres. Measured: the frames change **0.09%** of the calibrated drum
frame.

The geometry is real and the module is legitimately articulated; `density.py` measures a module's
geometry, which is what a geometry metric should do. But "interior passes layer 2" and "the drum
looks better" are different claims, and only the first is true. The frames will show in any shot
that uses the shell rather than the ground.

### The vocabulary, and where it did not fit

`rooms.articulate()` covers every box-shaped interior. The others needed their own:

| module | what earned the line |
|---|---|
| `plant` | longitudinal service runs, cable tray, secondary ties at a 7 m working pitch against the 36 m structural one |
| `core_tube` | longitudinal stringers on the facet creases — one runs 2.6 km, laying kilometres of arris for twelve triangles |
| `interior` | circumferential ring frames, ~49 m of line per triangle, the best yield in the project |
| `garden` | paving bay joints; the ground is most of the area and carried no line at all |

## Session 3s (earlier) — layer 2 goes 16/118 -> 93/118

`rooms.articulate()` is the shared vocabulary — bands, deck and soffit grids, mullions, panels,
conduit — extracted from the procedural generator so the BESPOKE modules use the same one. Nine
copies of this would have drifted apart; it is the same station, built by the same people. Applied
to `hospitality` (23.9% -> 102.1%), `quarters` (53.6% -> 110.4%) and `customs` (32.3% -> 111.0%),
each with `scale` and per-element flags so a 3 m cabin is not given a 12 m ward's pitch.

**Every flag on the quarters call was forced by an assertion, not chosen.** Bands off because the
unit's own `light_downlight` sits at dado height and `light_portal_head` at cornice height, so a
continuous band there buries a lamp in solid trim — quarters' own check caught it. Mullions off
because the diplomatic unit's downlight lands inside one. What is left is the deck and the wall
panels, which no fitting occupies, at a finer pitch to make up the line.

**One bug worth remembering: I named a parameter `zc` and the mullion loop already bound `zc`.**
The shift block then translated every band by the last mullion's z, and all 68 rooms left their own
footprint. The footprint assertion caught it immediately. Renamed to `z_off`.

**Not applicable to `plant`, `alien_sector` or `command_control`** — they build arc bands and
circular galleries in cylindrical space, not boxes. Those need their own pass.

## Session 3s (earlier) — layer 2 goes 16/118 -> 78/118

The Garden **and** the 68 procedural rooms now pass their derived detail floor. `rooms.py` was
18.0% of bar at 336 triangles over 384 m² — deck, soffit, four walls, ribs, fixtures, and a flat
field of wall between them. It is now **100.7%** at 2,592 a bay, inside a habitat cell budget still
at 66%. One generator, so one pass moved all 68 (INV-073).

`docs/engine-room-articulated.png` is the frame: jointed deck, skirting, dado, panelled walls with
mullions, cornice, and a serviced soffit with its tee grid.

**The trim check is the part worth keeping.** Adding the new trim broke the walkability flood fill
on all 68 rooms, because it treats any non-shell group as an obstacle. The tempting fix is to add
the trim to the ignore list — a gate found something, so change the gate. Instead the exemption is
earned: every trim group must be thinner than a step (0.10 m) or above head height (2.0 m). That
immediately caught a **0.11 m conduit at chest height in the brig and security_central**, whose
soffits are low. Conduits now stop rather than drop.

## Session 3s (cont.) — the Garden, rebuilt first

**`directory.py` layer 2: 16/118 -> 20/118.** The four Garden places pass at **101.4%** of their
derived detail floor, from 16.3%. `garden.tree()` 30 -> 440 triangles, `block_building()` 48 ->
~1,600, the townscape 2,228 -> 22,620. Every object added is one `reference/00-INDEX.md` already
extracted from `29a` and `33a` and that nobody had built: setted paths, clipped hedges, bench,
circular planter with red-brown coping, orange sail canopies, the transit track, field boundaries.
Only the dimensions are invention (INV-072).

**THE DESIGN RULE, and it generalises to the other 98 places.** Line density is metres of visible
line per m², so **LENGTH earns it, not triangle count**. Measured in this module:

| element | m of line per triangle |
|---|---|
| dwarf boundary wall | ~20 |
| continuous cill band | 5.3 |
| downpipe | 2.0 |
| **panel relief — what the budget bound is derived from** | **0.17** |

Long thin prisms and continuous bands are how a *landscape* reaches its floor; panel relief is how
a *wall* does. Choosing wrong wastes the budget by thirty times. The last 20% came entirely from
paving bay joints — the ground is most of the area and was carrying no line at all.

**TWO DEFECTS THE METRIC COULD NOT SEE AND THE RENDER COULD**, which is the argument for still
looking at every frame:
1. The limbs were built with the ring-based taper helper, which shares one axis for all rings — so
   they were vertical stubs at the trunk while the foliage sat offset. **The canopy floated in
   three disconnected pieces and the line density was fine.** `_limb()` sweeps between arbitrary
   points; collars now crease against the trunk.
2. 23 new group names took the fallback material and the whole townscape rendered **magenta**.
   Caught by the layer-3 gate dropping 34/34 -> 33/34 — the gate working. All 23 bind to
   already-measured materials; no new colour was introduced. It happened a second time with the
   ground groups, and the gate caught that too.

**Next, and it is now a known quantity:** 98 places remain below the floor. The 68 procedural rooms
in `rooms.py` are 58% of the station and share one generator, so one rebuild moves all of them —
that is the highest-leverage target, and the cill-band/pilaster vocabulary built here is directly
what a room interior needs.

## READ THIS FIRST — session 3r found the project was measuring the wrong things

The owner looked at the renders and said the buildings are *"shitty little cubes"* and the trees a
*"sad excuse for a tree"*, and asked where they went wrong. **Every gate was green when they said
it.** Three things were true at once, and the third is the answer:

1. Materials on 118/118, lighting on 118/118, all measured and all real work.
2. Both were applied to **blockout**, and nothing in the repository could say so.
3. `station/garden.py` contained `check(..., dens < 0.06)` — **an assertion that the Garden must
   stay BELOW 0.06 tri/m².** A ceiling on detail, in the module the owner complained about, which
   would have failed any attempt to fix it. Green for three sessions.

Two metrics were built to close that gap, and both are deliberately failing right now:

| | before | after | what it measures |
|---|---|---|---|
| `station/density.py` (INV-070) | — | **16/118 pass** | visible line density vs a floor derived from budget, Nyquist and B5 frames |
| `tools/measure_frame.py` distribution | 17/17 pass | **1/17 pass** | p5, p95, crushed, clipped — not just the median |

**Layer 2 is 16/118 and layers 3 and 4 cascade to 16/118 behind it**, because a place cannot be at
layer 3 while it fails layer 2. `directory.py` prints it. Nothing was retuned to make a number move;
the point was to learn the distance.

**The numbers that answer "how bad":** on fidelity alone every one of the 118 locations sits between
**0.20% and 19.7%** of a Babylon 5 set's line density, median **5.0%**. `garden.tree()` is 30
triangles — a hexagonal prism, one line every 113 cm on a 7 m tree, **2.2% of its floor**.
`block_building()` is 48 triangles, one line every 3.8 m on a 15 m building, **3.2%**.

**A DECISION IS WAITING FOR THE OWNER** (see the end of this section): the exterior's detail floor
and its triangle budget are the same number by construction. Either the 400,000 allotment rises or
the hull's 253,184 comes down through LOD. That is upstream of any rebuild.

## Where we are

**Exterior structure complete. The habitat drum is now built, inside and out, from the same
schema.** The volume where you look up and see ground overhead exists: banded ground, both end
caps, three guideway trusses carrying the habitat's lighting, and the three radial spokes —
42,696 triangles, all generated. See *Session 2u*.

**The station's core hull exists and is canon-verified.** 253,184 triangles, 8,046.9 m long
against canon's 8,047, generated entirely from `station/schema/station.yaml` and gated by 17
passing canon assertions. It renders and it is recognisably Babylon 5.

What remains on the exterior is refinement of the crude components — cobra bays, docking
ports, observation domes, rotundas are still box primitives.

**Interiors are not blocked.** C-003 and C-004 decide which *name* attaches to a volume, not
what shape it is; geometry is generated against `(sector, ring_index)` and labelled afterwards
by `bind_labels()`. When the conflicts close, the mapping changes and the geometry does not.

## Session 1 — foundation

- **Verification loop proven.** Mesa lavapipe installed, enumerates **Vulkan 1.4 on CPU**
  (`llvmpipe`). Godot renders on Vulkan, so offscreen render → PNG → direct image inspection
  is a working aesthetic feedback loop with no GPU and no human. This was the single largest
  risk to the project and it is closed.
- **102 reference files sorted** from the dump into 13 subject/sector folders.
- **Canon codex written** — `canon/00-MASTER.md`, `CONFLICTS.md`, `INVENTIONS.md`.
- **C-001 resolved.** `other map 4.jpg` (Miller) states 3,108 m overall length; show canon says
  five miles. Show canon wins at 8,047 m; Miller's proportions rescaled by k = 2.5891.
  Had this gone unnoticed, the entire station would have been built at 39% scale.
- **C-005 found.** The Contract 5 schematic's scale bar is internally inconsistent — left group
  127.7 px/km, right group 125.7, but the 3→5 km span reads 105.5. The reproduction is spliced.
  That sheet is authoritative for topology only, never for dimensions.
- **Spin gravity derived.** 1.0 g at r = 278.3 m → ω = 0.18775 rad/s, period 33.5 s, 1.79 rpm.
  Sits below the human Coriolis tolerance threshold, which is a meaningful cross-check.
- **Project memory** — `CLAUDE.md`, ADRs 0001–0003, this file.
- **Schema v0** — `station/schema/station.yaml`: coordinate convention, global properties,
  section dimensions, exterior system manifest, sector model.
- **Tools** — `refzoom.py`, `measure_schematic.py`, `sort_references.py`.

- **OW-001 calibration established.** `other map 4.jpg` calibrated: station spans px 71→2048,
  centreline at y=388, giving **0.6361 px per Miller-metre** (1.572 Miller-m/px, 4.070 real
  m/px after k). Confirmed that Miller's Green Section outer length and Bio-Habitat interior
  length are both 1058 m and correspond to one continuous envelope — **the Green Section is
  the habitat drum**, 2,739.3 m at real scale.

- **OW-001 COMPLETE.** Longitudinal framework read segment-by-segment at 3× against a
  calibrated 50 m grid: fourteen features with z-extents from aft terminus to forward
  deflector spike. Logged C-006 (Miller's drawing vs his own table) and identified the
  explosive disconnect point at real z = 2,680 m as a structural boundary — everything aft
  of it detaches as one assembly.
- **Radius profile extracted.** 1,978 samples at 4.07 m spacing, `station/schema/radius_profile.json`.
  Hull is now fully defined as a surface of revolution. Two extraction failures found and
  fixed (inset photograph read as hull; leader lines followed instead of the outline —
  solved by a horizontal run-length filter, since leaders outnumber the hull locally and
  defeat outlier rejection). Verified by overlaying the trace back onto the drawing.
- **Independent cross-check passed.** Measured envelope vs table diameters: Red agrees to
  5.7%, Green to 3.9%. The two are derived independently, so this validates both the
  0.6361 px/m calibration and the k = 2.5891 rescale.
- **Finding:** the station's widest structure is the **aft hull block at ~957 m envelope
  diameter**, which Miller's table never names. Not the Red Section.

## Session 2 — the hull exists

- **Hull generator built.** `station/generate_hull.py` lathes the longitudinal framework and
  radius profile into a closed surface of revolution grouped by feature.
  **253,184 triangles, 8,046.9 m long** against canon's 8,047.
- **Canon assertions built.** `station/validate.py`, **17/17 passing**: gapless and
  non-overlapping features, subfeature containment, profile spans canon length, cross-check
  agreement, hull length, no unassigned or degenerate geometry, closed at both ends, triangle
  budget, max radius agreement, spin gravity exactly 1.000 g, period consistency, rpm below
  the Coriolis threshold. Runs in CI on every commit.
- **The generator caught a schema gap on first run** — 189 m and 5,888 triangles unassigned
  between green_section's table-derived end (5846) and its own habitat_cylinder subfeature
  (6035). That is C-006 surfacing as geometry. Fixed, and validate.py now blocks recurrence.
- **Software renderer built.** `tools/preview_render.py` — schema edit to inspectable image in
  ~5 seconds, no Godot and no GPU. First render is recognisably Babylon 5.
- **Ring artifacts diagnosed and fixed.** The raw profile flipped gradient sign on 20% of
  samples, which lathed into visible rings. A plain low-pass would have rounded off the real
  section transitions, so smoothing detects step edges (>4 px) and smooths only between them.
  **Sign flips 396 → 73, max radius unchanged at 480.3 m.** Verified by re-render.
- **Godot build fixed and running.** The proxy 403s GitHub archive and codeload paths;
  switched to a shallow clone.

## Session 2b — components

- **Component system built.** `station/components.py` with three placement kinds --
  `radial_array` (fins, solar arrays), `pylon_pair` (communications grid), `radial_band`
  (cobra bays, cargo modules). Driven entirely from a new `components:` block in the schema.
  **96 instances across 5 component types.**
- Components attach at the hull radius the profile reports for their z, so they stay welded
  automatically when the profile changes. No second source of truth to drift.
- Placements are cross-referenced three ways: Exterior map ordering, Miller's lettered
  callouts, and an envelope-excess analysis (a wide running minimum of the radius profile
  approximates the core hull; where the envelope exceeds it by >25 m, something protrudes).
  Agreement between a callout and an independent excess zone is what justifies each position.
- **Validator extended to 19 assertions**, including that every schema component actually
  produced geometry, and separate hull-vs-model max radius checks now that the comms grid
  tip (1,210 m) exceeds the hull.

## Component quality — honest assessment

The pipeline is correct; **the geometry is crude.** Components are box primitives placed by
rule. Specifically still wrong:

**Fixed after inspection:**

- Cooling fins clustered into a shuttlecock at one z. Contract 5 shows the radiators as a
  small number of discrete assemblies along the spine, and with a total of 12 that reconciles
  to **3 assemblies of 4** -- which is also why 12 appears in the Exterior map as one figure
  covering the whole system. `radial_array` now takes a `rings` parameter and clocks
  successive assemblies so they do not line up down the spine.
- The communications grid rendered as a thin I-beam because the panel had 893 m of length but
  only 90 m of radial depth. Now 300 m deep, so it reads as an array.

**Still wrong:**

- Components are box primitives throughout. No taper, no truss structure, no articulation.
- Solar arrays and cooling fins still read as the same kind of object.
- ~~No greebling, no panel lines, no surface detail anywhere.~~ Done in session 2n.
- Observation domes, rotundas, docking ports, sensor and deflector arrays not yet placed.

These need reference-driven refinement against `01-station-exterior/` before they are
believable. The value delivered so far is the *pipeline*, not the shapes.

## Known limitations of the current hull

The lathe produces the **core hull only**. A surface of revolution cannot represent the
non-axisymmetric structures, all of which remain to be added as separate components:
reactor cooling fins (12), heat exchange / solar arrays (12), communications grid pylons (2),
cobra bays (28), cargo modules (42), observation domes and rotundas, docking ports, and the
sensor and deflector arrays.

## Session 2c — reference correction and a topology elimination

- **CI added** (`.github/workflows/validate.yml`) — regenerates geometry and runs the canon
  assertions on every push, plus checks the invention log is intact.
- **C-007: radiators corrected.** The orthographic production sheet shows them **coplanar** —
  3 blades above the spine, 3 below, edge-on in top view and full-face in side view. I had
  built 12 arrayed around the axis from a bare count. Added the `planar_blades` kind.
  *Lesson recorded: a count in a labelled diagram does not imply an arrangement.*
- **Cargo modules moved to dorsal rows** (`dorsal_line` kind) — the sheet shows them as rows
  along meridians, not wrapped around the circumference.
- **C-003 half-resolved, by geometry rather than preference.** Deriving the Grey/Brown/Yellow
  extents showed the station is **50% pressurised, 50% structural**, with habitable volume in
  **four separated regions** and **Green alone at 73%** of it. Six sectors cannot be
  longitudinal slices — Grey and Brown would land on bare truss spine. The longitudinal model
  is rejected for interiors and INV-003 is marked overturned.
- **Godot build:** running but slow — ~1,155 of ~9,500 translation units at `-j2` after the
  first attempt was killed (OOM signature: log stops mid-compile, no error). LTO disabled and
  parallelism capped. This is hours of background work and blocks nothing, since
  `tools/preview_render.py` covers the visual loop for the structure-first phase.

## Session 2d — component set completed

- **Observation domes (2)** placed on the forward docking structure. Dome 1 is Command &
  Control — a place the player will stand, so its position has to survive into the interior
  layout rather than being treated as hull decoration.
- **Observation rotundas (4)**, **docking ports (2)** — primary north and service south per the
  Contract 5 cross-section — **forward swept arrays (4)** and **space traffic proximity
  arrays (4)** placed.
- New component kinds: `domes` (half-ellipsoid blisters on an arbitrary outward normal, with a
  properly constructed orthonormal frame so they sit flush at any hull angle) and `swept_fins`.
- **255,800 triangles**, 2,616 of them components. 19/19 assertions still passing.

## Session 2e — plating and the physics foundation

- **Hull plating.** Lathe radius modulated per plate cell, deterministic in (row, col) so
  regeneration stays byte-identical. Tuned by inspection: 37 m plates read as scales, 65 m
  plates read as plating. Depth 1.3 m.
- **Swept structures reshaped** — built from spanwise segments so the planform tapers and the
  trailing edge sweeps, instead of reading as flat planks. Heat-exchange collectors moved from
  a radial pinwheel to the swept form the top view shows.
- **Rotating-frame physics** (`station/physics/rotating_frame.py`, **25 tests passing**) —
  gravity gradient, centrifugal, Coriolis, apparent weight, frame transforms, launch velocity
  inheritance. Pure Python, no engine, no GPU.
- **Floating origin and precision** (`station/physics/floating_origin.py`, **10 tests
  passing**).
- **Constants tightened to 9 places.** Rounding ω to 5 places put floor gravity at 1.000351 g;
  the canon assertion for floor gravity is now 1e-6 rather than 0.5%, since it is derived and
  any drift means the schema has stopped agreeing with itself.
- **CI runs all three suites** — 20 canon assertions, 25 physics, 10 precision.

## Physics results worth carrying forward

| Quantity | Value | Why it matters |
|---|---|---|
| Drum floor speed | **52.2 m/s** | Inherited by anything launched — a cobra bay launch is a fling, not a drop |
| Apparent weight, walking | **0.947× to 1.054×** | Direction of travel changes your weight. A felt characteristic of a spun habitat |
| Coriolis climbing to axis | **1.13 m/s² spinward** | Ladders and lifts push you sideways |
| float32 at station nose | 0.49 mm | Station alone is marginally survivable in float32 |
| float32 at 50 km | 3.91 mm | **Starfury range is not.** Double precision is required by the flight envelope, not the station |
| Floating origin gain | 224× | 1.09 mm naive → 4.9 µm rebased at 40 km |

## Session 2f — Starfury flight model

- **`station/physics/starfury.py`, 18 tests passing.** Newtonian 6-DOF, quaternion attitude,
  discrete thrusters with position and direction rather than an abstract force vector, and
  Euler's equations including the gyroscopic term so a tumbling Starfury precesses.
- Thrust is **allocated** across thrusters, so a demand the layout cannot satisfy comes out
  partially satisfied instead of silently exact. Pretending otherwise would make the craft
  feel like it has thrusters it does not.
- **The defining property is proven, not assumed:** the craft rotates 344° with velocity
  drift of exactly 0.000e+00 m/s. Flip-and-burn decelerates at thrust/mass to 0.01 m/s.
- **Cobra bay launch works from the physics alone.** Released at rest in the drum, the craft
  carries 52.2 m/s of inherited tangential velocity and coasts **1,313 m clear in 30 s and
  4,710 m in 90 s with no thrust at all.** The station throws it — which is exactly what the
  show depicts and why cobra bays need no catapult.
- `tools/plot_trajectory.py` plots flight paths over the real hull silhouette.
- **Aurora performance:** 18.38 m/s² on the mains, 1.87 g.

## Session 2g — docking

- **`station/physics/docking.py`, 15 tests passing.** A bay on the rotating hull is not a
  fixed target: it travels at 52.2 m/s on a circle whose normal sweeps a full turn every
  33.5 s, so guidance is *interception of a known trajectory*, not pursuit.
- **Station-keeping is not zero velocity.** Holding position 200 m off a bay requires
  **89.8 m/s** — more than the bay itself, because the standoff point orbits at a larger
  radius. A craft that stops dead relative to the station centre is **772 m off the bay
  within 10 seconds.**
- Contact is gated on three independent conditions — closing rate, lateral drift, and
  attitude alignment. Failing to spin-match passes the closing-rate check and fails on
  **52.2 m/s of lateral drift**, which is a scrape along the hull rather than a dock.
- **Axial ports have no tangential velocity to match at all.** That is the design rationale
  for the forward docking sphere and why large ships use it rather than a rim bay.

## Session 2h — core shuttle and radial transit

- **`station/physics/core_shuttle.py`, 18 tests passing.** Rim-to-axis transit through the
  gravity gradient, plus the axial run itself.
- **The headline result, measured not assumed.** Coriolis on radial motion is 2ωv, so peak
  lateral load scales inversely with transit duration:

  | Rim → axis in | Peak lateral |
  |---|---|
  | 8 s | **2.00 g** |
  | 60 s | 0.27 g |
  | 120 s | 0.13 g |
  | 300 s | 0.05 g |

  Holding it under 0.12 g needs **133 seconds**. A lift from the rim to the core shuttle is a
  **two-minute-plus ride** during which weight drains away and an unexplained sideways push
  builds and fades. That is a felt journey, and it falls out of the geometry rather than being
  a design choice.
- The car also has to shed **52.2 m/s of tangential speed**, costing 0.13 g along the direction
  of rotation. Axial run across the rotating assembly: 99 s at 1.2 m/s².
- `tools/plot_transit.py` plots the ride profile.

## Test suites — all green

| Suite | Tests |
|---|---|
| Canon assertions | 20 |
| Rotating frame | 25 |
| Precision / floating origin | 10 |
| Starfury flight | 18 |
| Docking | 15 |
| Core shuttle | 18 |
| **Total** | **106** |

## Session 2i — engine pipeline and budgets

- **glTF export** (`station/export_gltf.py`) — 23 meshes, 256,232 triangles, 21.5 MB. OBJ has
  no normals, no material bindings and no hierarchy; glTF is what Godot imports natively and
  it preserves per-feature grouping, so hull sections stay individually addressable for
  streaming and damage states. Normals are per-face because the hull is faceted by design.
- CI **structurally validates the glb** — magic, version, declared vs actual length, chunk
  types, buffer agreement, and every accessor fitting inside its bufferView. A malformed
  export that Godot silently half-imports would be miserable to debug later.
- **Performance budget gates** (`station/budget.py`) — the promised numeric enforcement, since
  framerate cannot be measured without target hardware. Currently **4/4 within budget**:

  | Metric | Now | Budget |
  |---|---|---|
  | Triangles | 256,232 | 400,000 (64%) |
  | Draw calls | 23 | 64 (36%) |
  | Vertex bandwidth | 18 MB | 32 MB (58%) |
  | glb on disk | 22 MB | 64 MB (34%) |

  The exterior gets a deliberately small slice — ~2% of frame budget — because it is
  always-visible background competing with interiors, NPCs and effects.

- **Two references catalogued.** The elevator still is from the 2023 animated film, not the
  original series — marked do-not-model-from. The arrival-concourse frame is authority 1 and
  its in-universe cutaway shows parallel longitudinal lines consistent with **radially stacked
  decks**, which corroborates the radial reading of C-004 without resolving it.

## Session 2o — radiators measured, not guessed

- **Radiator blades rebuilt from the production sheet.** They are **lozenges**, not tapered
  plates: narrow at the bolted root, widest ~28% out, long slow taper to a capped tip. A
  root-to-tip taper gives a wedge and loses the silhouette entirely.
- Measured proportions off the sheet: **~7:1 span to max width**, three per side sitting close
  together with gaps about equal to their own width. The previous values were 3:1 spread over
  730 m, which read as three separate paddles rather than one radiator bank.
- Added the structural frame around the panel, root mount blocks, tip caps, and the spine rail
  the blades stand on — on the sheet the blades never touch the hull directly, and that
  horizontal base line is a large part of the read.

## Session 2r — interior triangle budget

- **`budget.py` now gates the interior**, which previously had no gate at all. 8/8 passing.
- Gated on **what is visible at once, not total built geometry**. Totalling the interior is
  meaningless under the concentric-ring topology: ring 1 alone is 2π×278.3 = **1,749 m of
  circumference per sector**, and five rings across six sectors run to millions of triangles
  that are never simultaneously in frame. Occlusion culling means the cost that matters is the
  current cell plus what is visible through its portals.
- Measured against a deliberately pessimistic visible set — a 50 m sight line with a crossing
  at each end:

  | Metric | Now | Budget |
  |---|---|---|
  | Corridor rate | 285 tri/m | 400 (71%) |
  | Junction | 1,400 tri | 2,000 (70%) |
  | Visible structure set | 17,032 tri | 60,000 (28%) |
  | Share of frame | 1% | 5% (28%) |

- The corridor rate is measured **marginally** (20 m minus 1 m, over 19), because a run's fixed
  end caps would otherwise make a short sample look far more expensive per metre than a long one.
- 60,000 is structure only: the same view has to carry props, fittings, signage, NPCs and
  whatever is through the windows. If structure alone reaches 60 k the kit has become too
  expensive to dress.

## Session 2t — exterior corrections from the reference sweep

- **Cargo modules: 42 → 6.** The 42 conflated two different things. Miller's table gives
  28 + 14 = 42 cargo **bays**, which are internal volumes; the orthographic sheet shows **six
  external modules** docked on a continuous raised dorsal rail with plinths between them. A
  station with 42 bays and 6 modules attached is not a contradiction — it is a station that is
  not full. The exterior systems list now says `cargo_bay` for the 42.
- **Forward "swept arrays" were wrong.** Built as four swept wings from a *top view alone*; the
  side view shows a single **flat plate-like communications array on a short pylon, blading
  forward** — a plane, not a wing pair. Four wings and one plate look alike in plan and nothing
  alike in silhouette, which is exactly how a plan-only read goes wrong. New `plate_array` kind.
- **CONFLICTS.md status header added.** The file is append-only, 1,378 lines, with eight C-003
  entries — one headed RESOLVED followed by four later notes narrowing it. A reader could act
  on a heading and be wrong. There is now a CURRENT STATUS table at the top, and the schema
  carries `assignment_status: OPEN_BLOCKING` with an assertion keeping it there.

## Autonomous continuation

A **6-hourly** trigger (`trig_01JS1VWf6yada5x6maPMAzza`, fires at :45) continues the plan
without prompting. It reads CLAUDE.md and this file, and:

- **Stops immediately and cheaply if everything on the next-session list is blocked.** It is
  told explicitly not to invent work to fill the time.
- Does **exactly one coherent increment** per firing — build, test, look at it, commit, update
  this file, stop.
- Does not spawn a workflow unless the work genuinely needs parallel fan-out.

Workflows are capped at **~5 agents** by owner decision. The adversarial verify pattern stays —
it caught a door interpenetrating a portal frame and a greeble call-signature mismatch.

To change cadence or stop it: `update_trigger` / `delete_trigger` with that id.

## Session 2j — THE ENGINE RENDERS THE STATION

**The full pipeline works end to end, with no GPU anywhere in it:**

```
station.yaml -> generate_hull.py -> station.glb -> Godot 4.4 (precision=double)
             -> Vulkan 1.4 on CPU (Mesa lavapipe) -> PNG -> read directly
```

- **Godot double-precision build finished** — 61 minutes, 147 MB,
  `godot.linuxbsd.editor.double.x86_64`. Binary lives at
  `/home/user/godot-build/godot-4.4-stable/bin/` (container-local; publish as a Release asset
  so future sessions do not rebuild).
- **`tools/build_and_render.sh`** runs the whole chain in one command.
- **Headless needed Xvfb.** Godot's `--headless` disables rendering entirely, so a virtual
  display plus the lavapipe ICD is what actually produces frames. Godot reports
  `Vulkan 1.4.318 - Forward+ - llvmpipe` — the software rasteriser doing real Forward+.
- **glTF export** (23 meshes, 256k triangles, 21.5 MB) with CI structural validation.
- **LOD chain** with switch distances derived from silhouette deviation, not facet width.
- **Budget gates** — 4/4 within budget, 64% of the triangle allowance.

Three visual corrections, each caught by looking: blown-out lighting, then missing material,
then framing. Materials live in the engine, not the export.

## Session 2k — reference audit

- **Eight animated-film frames quarantined.** They are from the 2023 animated feature, not
  live-action Babylon 5: wrong source against a brief that says original design in the show,
  wrong era (later blue uniforms against the S2–3 lock), and reinterpreted rather than
  reproduced sets. Moved to `reference/21-QUARANTINE-animated-film/` with a README, not
  deleted, so a future session does not rediscover and use them.
- **The trap is worth remembering.** These were the *highest-resolution interior references in
  the whole set* — ~2260×1180 against genuine screencaps at 800×600 or less. The pull toward
  them is exactly backwards. **Resolution is not authority.** They form an identifiable cluster
  by resolution and aspect ratio, which is how the remaining six were found after the first two.
- **New C-004 evidence, authority 1.** `central corridor.webp` shows **two occupied levels in a
  single volume** — a catwalk above a main floor. So a "level" need not be a full-height deck;
  it can be a mezzanine. **Level count and deck count need not be equal**, which means "Grey 17"
  does not imply seventeen decks of hull. Any interior layout assuming that would have been wrong.
- Same frame: the hull's **circular structural ribs are exposed rather than clad** — a primary
  motif for the interior kit regardless of how C-004 resolves.

- **Interior kit spec written** (`docs/interior-kit-spec.md`) from authority-1 footage only.
  Deliberately takes no position on level topology, so it is **buildable now** despite C-003
  and C-004. Corridor width, ceiling height, door size and deck spacing are left unspecified
  precisely because they follow from level topology — putting a guess there would seed a
  number later work silently builds on.

## Session 2l — interior kit built

- **`station/interior_kit.py`** — ring frames, deck panels with recessed light channels,
  handrails, wall plates. Rendered as a 20 m corridor it reads immediately as Babylon 5:
  receding exposed ribs framing the view down the passage.
- Dimensions that depend on level topology live in a `PROVISIONAL` dict, **not** as constants,
  so resolving C-004 changes one table rather than a hundred call sites.
- The first assembly produced a mangled deck: each piece is authored in its own natural frame
  and I was remapping axes with inline tuple comprehensions, which silently transposed the
  wrong pair. Merging now takes an explicit remap function per piece.

## Session 2m — NPC foundation

- **`station/npc/names.py`, 20 tests.** Per-species name grammars fitted to names actually
  spoken on screen, with the evidence recorded beside each pattern. Narn apostrophe structure
  from G'Kar and Na'Toth; Centauri house names established by Londo and Carn *sharing* Mollari;
  human surnames spanning several traditions because Earth Alliance is explicitly multinational.
  **Vorlon is a closed list, not a generator** — two attested names is not enough to generate
  from, and a test asserts it stays closed.
- **`station/npc/schedule.py`, 18 tests.** Species rhythms, roles, rotating shifts, and the
  statistical population layer. **A corridor at 03:00 is not empty** — it holds Minbari (broken
  sleep is canon) and Centauri (still in the bars), which is a specific and different crowd
  from 13:00.
- Two bugs caught, both design failure modes rather than typos:
  - Sleep resolving before work against an unshifted rhythm **put the entire night watch to
    bed** — security showed *zero on duty at 02:00*. Sleep now follows the shift offset.
  - The species mix summed to 0.94, so the aggregate layer **silently dropped 120 of every
    2,000 residents**. Exactly the quiet population leak the statistical layer exists to prevent.
- Logged as INV-004 and INV-005.
- **`CONTRIBUTING.md`** added — the loop, plus a table of every mistake made so far and its
  cause. All of them were caught by looking at output, not by reading code.
- **`docs/godot-binary.md`** — reproduction, the two build pitfalls (OOM at `-j4`, proxy 403 on
  archive URLs), and why a 52 MB build artifact is deliberately not in git history.

## Session 2n — exterior greebling

- **`station/greeble.py`** — procedural surface detail scattered by rule over the whole hull.
  Access panels, louvred vent banks, octagonal hatches, sensor blisters, antenna stubs,
  magnetic cleats, marker lights, and clamped conduit runs following the long axis.
  **70,778 triangles, 1,976 fittings in 662 assemblies plus 52 conduit runs** — 18% of the
  exterior triangle budget, taking the model to 82% with 73k spare.
- Driven from a new `greebles:` block in the schema: five density tiers assigned per
  longitudinal feature, from `clean` on the habitat drum to `industrial` on the reactor spine,
  a 13× spread. Logged as **INV-006**.
- **Determinism is asserted, not assumed.** Every instance is keyed on
  (seed, zone, cell indices) through a written-out FNV-1a, because Python's `str.__hash__` is
  salted per process and would have produced a different hull every run. Verified two ways:
  a new canon assertion that builds the pass twice and compares, and a byte-for-byte `cmp` of
  the OBJ across `PYTHONHASHSEED=1` and `PYTHONHASHSEED=99999`.
- **The first attempt was wrong and looking at it is what caught it.** 10–20 m fittings on an
  even lattice rendered as confetti — noise, not machinery. Two changes fixed it: fittings
  scaled up to 15–50 m, and single objects replaced by *assemblies* (one full-size primary plus
  small satellites) so there is a size hierarchy that reads at 200 m and at 20 km.
- **The conduit runs do most of the work.** A clamped line running 900 m down the flank of the
  drum is the most legible surface feature on the reference sheet, and one run is worth fifty
  scattered boxes.
- **Caught a real LOD regression.** Scattered detail does not decimate the way the lathe does,
  so greebles were a fixed 71k floor — **91% of lod3**. `lod.py` now drives a per-level greeble
  detail fraction (1.0 / 0.45 / 0.12 / 0.0) and lod3 is back to 7,016 triangles. Culling is a
  stable subset — verified that every lod1 greeble vertex exists in lod0 — so a switch removes
  fittings rather than rearranging them.

## Test suites — 151 tests green

| Suite | Tests |
|---|---|
| Canon assertions | 23 |
| Performance budgets | 4 |
| Rotating frame | 25 |
| Precision / floating origin | 10 |
| Starfury flight | 18 |
| Docking | 15 |
| Core shuttle | 18 |
| NPC names | 20 |
| NPC schedules | 18 |

## Session 2p — interior kit: walls, doors, junctions

The corridor had ribs and a deck and no walls, so it read as a skeleton. It now reads as a
corridor. `station/interior_kit.py` gains `wall_assembly`, `portal_frame`, `pilaster`,
`door_frame`, `door_leaf`, `bulkhead`, `deck_grid`, `junction` and
`corridor_junction_section`, and `corridor_section` assembles all of it.

**The section was wrong and the reference says so.** Both authority-1 corridor frames --
`07-sector-grey/grey level 1.webp` and `05-sector-green/corridor in alien sector.webp` -- show
a **chamfered box**: flat deck, upright walls, ~45 deg chamfers into a flat soffit. The first
assembly used `ring_frame` and read as a pipe. `ring_frame` stays in the kit, because
`central corridor.webp` does show circular ribs -- of a two-storey volume, not a corridor. The
two are different elements and were being conflated.

**`grey level 1.webp` is the most useful interior frame in the set** and had never been
catalogued. Square-on it gives the whole wall build-up: projecting skirt, set-back dado, heavy
rail band at hip height throwing a deep shadow reveal, then courses of large plates with
recessed seams; bullnose pilasters at the portal jambs carrying segmented vertical light
strips; warm downlights low on the wall; a fine deck tile grid. All of it is now modelled and
all of it is logged as proportions, not metres -- `INV-007`.

**Doors: the aperture is sourced, the mechanism is not.** No frame in the reference set shows a
door leaf, open, closed or moving. The aperture is fixed -- a chamfered polygon with vertical
jambs, a flat head and a raised threshold -- and that **rules out an iris on geometry rather
than taste**: an iris sweeps a disc and leaves the four chamfered corners unswept. The
remaining two readings are both built and selected by one entry in `PROVISIONAL`, so
overturning the guess is a one-word edit. `INV-008`.

**Found while building: `_box` was producing inside-out solids.** Given corners in the obvious
order it emitted every face wound inward -- verified numerically, 12 of 12 triangles facing the
wrong way on a unit cube. Outdoors that only changes the shading, which is why it survived
several sessions of exterior work: a closed solid keeps its silhouette either way, so
proportions judged from those renders were still right and the lighting was not. Indoors it is
not subtle -- the camera is inside the geometry, so an inside-out wall is one you see straight
through. Fixed in `components.py` in the same window; the interior kit's `_selftest` asserts
its primitives face outward so it cannot come back unnoticed. (It did come back unnoticed, in
two functions the gate did not reach — see the verification note below.)

**Two more bugs, both found by looking:**
- The old `corridor_section` laid its deck with a negative-determinant remap and no winding
  reversal, so the floor was inside-out too. `_merge` now carries an explicit `flip`.
- A closure tiled into convex blocks shares internal faces, and a depth-sorted renderer draws
  them over the plate in front -- the bulkhead read as separate panels with joints radiating
  off every door corner. `_plate_with_hole` decomposes only the caps and rims the two loops, so
  there is no internal face to draw. It is also cheaper.

Verified by rendering from a 1.65 m eye height and reading the PNGs: a 21.6 m corridor with a
wall door and a bulkhead door, a four-arm crossing, and a tee. **7,656 triangles for 21.6 m**
(354/m); a crossing with four 7.2 m stubs is 10,644. Canon assertions 23/23, budget gates 4/4.

### Adversarial verification of 2p — three defects the render pass missed

**The corridor was open to space down both sides, its full length.** `wall_assembly` built its
chamfer leaning *outboard*, away from the corridor, so it roofed nothing and left a 0.5 m slot
between the soffit and each wall head in every bay. **7.9% of rays cast from head height
escaped straight out through the ceiling; none escaped sideways or down.**

It survived a seven-iteration render pass because **the preview background is black and so is
an unlit ceiling** — a hole and a shadow are the same pixels. The session read the symptom
correctly ("the ceiling was rendering as a void") and treated it as lighting, adding soffit
ribs to give the eye something to land on. Re-rendered against a magenta background it is
unmissable. *Lesson: render interiors against a colour that cannot occur in the model. A black
void is the one background that hides the failure interiors are most prone to.*

**`ring_frame` and `wall_panel` were both inside-out** — signed volume negative, every face of
every segment wound inward — at the same time as the note above claiming `_selftest` had made
that class of bug un-repeatable. The gate only covered `_slab` and `_prism`. Both functions are
unused today, which is why nothing rendered wrong; `ring_frame` is the piece explicitly kept
for the two-storey volumes in `central corridor.webp`, so the next session to build one would
have inherited it.

**Nothing in the kit ran in CI.** `.github/workflows/validate.yml` never invoked
`interior_kit.py`, so neither gate protected anything between sessions.

All three fixed: the chamfer leans inboard, both primitives are rewound, `_selftest` now gates
**every** primitive on signed volume plus a coverage test that a corridor is closed overhead
(each assertion was confirmed to fail on the reintroduced bug), and CI runs the module.

Still open, and reported rather than fixed:

- **A door bay has no wall build-up.** `corridor_section` passes `courses=False` for the bay a
  wall door takes over, so the skirt, dado, rail band and plate courses stop dead at the door
  and resume after it, leaving the door set in a blank plate. `grey level 1.webp` shows the
  build-up running continuously past portals. Needs the courses cut round the aperture.
- **INV-007's chamfered section is inferred, not observed.** `corridor in alien sector.webp`
  shows a chamfered *aperture*; nothing establishes the passage behind it has that profile, and
  `grey level 1.webp` shows a rectangular portal header. INV-007 and the spec now say so.
- The junction's cross-corridor deck tile pitch is 0.57 m against the arms' 0.605 m, because
  `deck_grid` divides a different width into a whole number of tiles. Along the run they align.

## Session 2q — reference mining: the two sheets that had never been opened

**No code changed. Documentation and reference filing only** — `reference/00-INDEX.md`,
`canon/00-MASTER.md`, `canon/CONFLICTS.md`, `docs/interior-kit-spec.md`, and nine files moved
into a new quarantine folder.

- **Two authority-3 files in `02-station-cutaways-and-plans/` had never been read.** Both bear
  directly on the blocking conflicts:
  - `b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp` — a **"Sectional Schematic"**
    carrying a **sector bracket that divides the station into six longitudinal bands**, five of
    them named. Band boundaries were measured from breaks and ticks on the bracket line and
    converted at 7.53 m/px.
  - `other map.png` — a **colour sector plate** carrying a colour-coded longitudinal strip and
    **six radial cross-section rosettes**, one per sector.
- **C-003 UPDATE 2.** `C-003 UPDATE`'s geometric refutation was aimed at the wrong target: it
  kills `other map 2.jpg`'s *ordering*, not longitudinal slicing. Under the authority-3
  ordering the aft structural half is **Yellow** (engineering), which is what belongs there.
  **Longitudinal slicing is back**; INV-003's overturn is itself overturned.
- **C-004's axis is settled: a level is a concentric radial deck.** Three independent lines —
  the rosettes, the sectional schematic's longitudinal decking (its own callout reads
  "CONCENTRIC PERSONNEL TRANSFER SYSTEMS"), and authority-1 footage
  (`03-sector-blue/Babylon_5_2-22_34b.jpg`, filed as an exterior shot and actually the drum
  interior along its axis). The Brown rosette also marks **"DOWNBELOW" on an outer ring by
  name**, which answers C-004's own standing objection from the source rather than by argument.
- **New authority-1 canon from signage** — station runs on **Earth Mean Time**, **six
  atmospheres** are available, humans are **atmosphere 02**, the identicard record schema, and
  **docking bays (24)**, which is a different system from the cobra bays of C-002.
- **Nine AI-generated character turnarounds quarantined** to
  `reference/22-QUARANTINE-ai-generated/`. Same lesson as folder 21 in a new costume: the
  largest "uniform reference" in the tree is a 2528×1696 PNG with its own generation prompt
  burned in. **Resolution is not authority.**

**Both conflicts stay OPEN and BLOCKING.** C-003 on the Green/Brown transposition — the two
authority-3 sheets disagree about which band is the 2,000 m habitat drum. C-004 on the
numbering convention — nothing numbers a ring, and getting the direction backwards inverts
every address on the station.

### Adversarial verification of 2q

Measurements re-derived independently and confirmed: the bracket boundaries (531/541 gap
midpoint 536 against the reported 537, every other within 1 px), the colour-strip hue bands
(Green 335–400, Red 401–538 — exact), all five duplicate claims, the file counts (100 / 83 live
/ 17 quarantined), and every cited reference path. The hull is untouched: 23/23 assertions,
4/4 budgets, 106+ physics tests, and the render is unchanged. Four corrections applied:

- `00-MASTER.md` carried a **stale "17–95 m"** for the boundary agreement that the measured
  table in `CONFLICTS.md` gives as 2, 74 and 96 m.
- **"Every band's contents match that sector's on-screen function" was not true**, and the
  exception matters. Band 4 — the one inferred to be Brown — also carries the **zen garden**
  and the **ambassadorial suites**, which are Green on screen. The table had listed only the
  three callouts that fit Brown. Corrected, and the omitted evidence is now weighed in C-003.
- **The missing sixth-band label is not a cropping artefact.** The sheet is cropped, but the
  sector-label row is intact (five labels in one band at y 271–285, no ink between x 521 and
  814). An uncropped scan will give the detail row; it may well not give the label. Chasing a
  better scan is therefore a weaker lead than it looked.
- The **Zocalo neon is `ZoCaLo`, six Latin glyphs** — the zigzag at the head is the Z, which the
  spec had described as a flourish beside the word.
- **The boundary agreement was oversold, and it is the load-bearing claim.** It was written up
  as "a stronger cross-check than anything else in the reference set". Tested against a null:
  mean miss 110 m over the six scored boundaries where random positions against the same 16
  candidate boundaries average 212 m — **p ≈ 0.06**. Real, weak, not proof. The headline "2 m"
  is a 4%-by-chance event and "three of six inside 100 m" is a 31%-by-chance event. Both
  `CONFLICTS.md` and the index now say so. *Lesson: "nearest boundary in our own schema" over a
  framework with sixteen boundaries is a generous test, and it needs a null before it counts.*
- Three live files — the **Contract 5 sheet**, `Exterior map.jpg` and `Interior map.jpg` — were
  neither index entries nor on the *Still uncatalogued* list, so the index's claim to list the
  whole remainder was false. Now listed.

Also flagged, not changed: the drum-is-Green reading is **better supported than the standoff
implied** — the drum is hollow in authority-1 footage and only the Green rosette is drawn
hollow — but a cartoon's fill is not a label, so C-003 correctly stays open.

## Session 2u — the habitat drum, built

The drum is the payoff of the structure phase: the volume where you look up and see ground
overhead. It is also the only surface in the project seen from its **concave** side, so every
convention built on the hull inverts there, and both times that mattered it failed silently
rather than loudly.

**Built** (`station/interior.py`, all of it generated, none hand-authored):

| Piece | What it is | Triangles |
|---|---|---|
| `drum_interior()` | inner shell as longitudinal land-use bands | 23,040 |
| `drum_end_cap()` | concentric ribbed dished bulkhead, both ends | 3,768 each |
| `guideway_truss()` / `drum_guideways()` | 3 Warren trusses with light runs | 11,796 |
| `drum_spokes()` | the 3 radial spokes at 120° | 324 |
| | **complete drum** | **42,696** |

**The "two end caps" open item was a misreading and is closed.** `Babylon_5_2-22_35a` is shot
forward through a drum tram's windscreen; the red-orange triangulated lattice converges to a
vanishing point with regular transverse ribs. It is the **tram guideway truss**, not a bulkhead.
There is one end cap, already measured in 2r, and it is now built. Full note in `CONFLICTS.md`.

**Newly sourced, and it settles a question that had no answer at all:** the habitat is lit from
**longitudinal light runs on the guideway trusses** — not an axial sun-strip, not the end caps.
`34b` shows the tubes alongside the truss, `33a` the rectangular fixtures on its underside.
Authority 1.

**Corroboration worth keeping.** The measured hub cone fills the inner ~20% of the cap. The
schema's core ring, read off an unrelated authority-3 print diagram, sits at r/R = 0.18. Two
independent sources 2% apart, so the cap is built to the schema's radius rather than a new
number, and the self-test asserts they stay within 0.03.

**Two silent failures caught, both from the concave side:**

1. The drum's faces were wound outward while the comment above them claimed inward. 95% were
   backface-culled and the render came out black — which reads as a badly placed camera, not as
   a bug. `_inward_fraction()` now measures it and the builder refuses to return geometry that
   would vanish.
2. The first viewpoint was hand-placed at the nominal 278.3 m floor while the band underneath
   was a 7 m settlement terrace at 271.3 m — five metres **inside the ground**. `stand_point()`
   now derives eye position from the land-use table.

**`tools/preview_render.py` gained what interiors need**: near-plane clipping (straddling
triangles were dropped whole, so everything nearer than one tessellation step vanished — a
black band that looked like missing geometry), `--pointlight` on the spin axis, `--headlamp`,
`--fog`, and `--tint` for judging composition by group.

**`SPOKE_COUNT` is now the single source of truth** for the drum's 3-fold radial structure.
Placement used to live in whichever script was rendering, so the trusses could silently stop
matching the spokes that carry them. `TRUSS_COUNT` derives from it and the self-test asserts it.

New inventions: **INV-011** (end-cap dish depth, rib sizes, per-course plate segmentation) and
**INV-012** (truss scale, height, count). `station/interior.py` self-tests at **62 assertions**
and runs in CI.

Renders: `docs/render-drum-interior.png`, `render-drum-endcap.png`,
`render-drum-endcap-detail.png`, `render-drum-standing.png`.

## Session 2v — the drum was hollow everywhere except in the ring model

Building the drum exposed a contradiction that had been in `ring_radii()` since it was written,
and that no test could have caught because no test asserted the thing it got wrong.

`ring_radii()` applied the same five concentric rings to every sector. In the drum that put
habitable decks at **228, 167 and 106 m radius** — which is the open air you look up through,
the volume whose existence is the entire point of the drum and is authority 1. It also put the
guideway trusses at 236.6 m **inside** one of those decks. Two subsystems built in the same
session disagreed about whether the same cubic kilometre was air or floor.

**The fix, and the reason it is more than a bug fix:** in the drum the habitable volume is the
stack **beneath** the ground, and beneath means radially **outward** — in spin gravity you stand
on the outside of the volume looking in. So the drum's decks run from the canon 278.3 m floor
out to the pressure hull, and everything inboard of the floor is air.

| | radius | gravity |
|---|---|---|
| pressure hull (inner face) | 310.8 m | 1.117 g |
| **sub-floor deck stack** | 278.3 → 310.8 m, **9 decks** | 1.013 → 1.117 g |
| habitat floor — the Garden | **278.3 m** | **1.000 g** |
| open air | 50.1 → 278.3 m | — |
| guideway trusses | 236.6 m | free flight |
| core / shuttle axis | 0 → 50.1 m | 0.18 g → 0 |

**Downbelow is heavier than the Garden.** That falls straight out of the geometry once the
direction is right, and it is the first thing the corrected model says that the wrong one could
not have.

**Derived result worth carrying forward — gravity is a property of sector, not of station.**
Because the station is rigid, everything at radius r feels ω²r, and the sectors have very
different radii:

| sector | outermost deck | gravity |
|---|---|---|
| Grey | 402.2 m | **1.445 g** |
| Green (sub-floor) | 310.8 m | 1.117 g |
| Green (Garden floor) | 278.3 m | 1.000 g |
| Red | 214.9 m | 0.771 g |
| Blue | 167.7 m | **0.602 g** |
| Yellow | — | see `sector_report()` |

Walking from Blue to Grey is a **2.4×** change in weight. That is the "real gravity changes"
the project set out to have, and it is free — no authoring, it is what the shape implies.

**Flagged, not resolved:** 1.445 g at Grey's outermost deck is high for somewhere people work.
That is a signal about either the disputed sector extents (C-003) or the fractional
`HULL_ALLOWANCE`, not about the physics. Recorded in INV-013 as a known weakness.

`drum_spokes()` now finds its own endpoints by ring *kind* rather than by index, since the drum
has three rings where every other sector has five. New assertions cover the whole failure class:
no deck stack may intrude on the open volume, the trusses must fly in open air, sub-floor
gravity must rise with depth, and non-drum sectors must still stack inward. **71 assertions.**

New invention: **INV-013** (6.0 m pressure hull skin).

## Session 2v (cont.) — the drum had no performance gate

`budget.py` gated the exterior and the corridor kit. The corridor gate is built on a **50 m
sight line**, because a wall stops you seeing further. That describes nothing about the drum:
standing in the Garden the far end cap is 2.6 km away, the ground overhead is 556 m up, and
every triangle in the volume is in the frustum at once. It is the **worst visibility case in
the project** and it had no gate at all.

Three gates added, and the third is the one that matters for what comes next:

| gate | now | budget |
|---|---|---|
| drum visible set | 42,696 tri | 300,000 tri |
| drum share of frame | 4% | 25% |
| ground surface density | 0.005 tri/m² | 0.5 tri/m² |

The drum earns a quarter of the frame rather than a corridor's twentieth — this is the view the
whole structure phase exists to produce — and it has to hold that with LOD, since the far half
of the drum is over a kilometre away.

**The number that constrains everything not yet built:** 257,304 triangles of headroom across
**4.5 million m²** of inner surface is **0.06 triangles per square metre**. That is the design
constraint for filling the drum, and it is emphatic: the ground is a **heightfield with
aggressive distance LOD**, not per-object geometry. Fields, roads and settlements are texture
and displacement; only what a person can walk up to gets mesh. Better to know that before
anything is authored than after.

## Session 2v (cont.) — the sight line was assumed; it is derivable

`budget.py` has gated interior cost on a **50 m sight line** since it was written, with the
comment "how far down a corridor before it curves or a door blocks". That is an assumption, and
it did not need to be one.

A ring corridor is occluded by **its own curvature**. Standing against the outer wall, the
furthest you can see is the chord tangent to the inner wall:

```
d = 2 * sqrt(r_outer^2 - r_inner^2)
```

Across every ring in every sector that gives:

| | sight line |
|---|---|
| Grey ring 1 (r = 402.2 m) | **91.3 m** — the worst case |
| Green sub-floor (r = 310.8 m) | 80.2 m |
| Blue ring 1 (r = 167.7 m) | 58.8 m |
| Yellow ring 4 (r = 52.1 m) | 32.5 m — the tightest |

So the gate was measuring against a view **1.8× shorter** than the station actually affords.
Corrected, the visible structure set is **28,791 triangles against 60,000** — still comfortable,
now honestly. `budget.py` computes it from the geometry rather than carrying a constant, and
the 50 m figure survives only as a fallback if the import fails.

**This also sizes the streaming cell**, which had no principled size before: a cell must be
wider than the view out of it or the player sees into territory that is not resident. At
1.5 sight lines of margin the drum's sub-floor ring wants **120 m cells (22.2°)** and Grey's
outermost ring wants **137 m (19.5°)**. That follows from the station's radius rather than from
a guess, and it is asserted per ring.

`interior.py` self-test: **96 assertions.**

## Session 2w — streaming cells, and "seamless" as a test

A ring corridor cannot be emitted whole. One deck of Grey's outermost ring is 2,527 m around
and would be **866,304 triangles** — fourteen times the entire interior frame budget, for one
deck of one ring of one sector. So the cell is the unit that gets built and streamed, and until
now nothing defined it.

`ring_cells()` divides a deck's circumference into an **integer** number of cells, so they tile
the circle exactly and there is no runt cell at 360° carrying a different amount of geometry
from all its neighbours. The size comes from `streaming_cell_deg()` — 1.5 sight lines — rounded
**down** in count so the actual cell is never smaller than asked for.

| sector / ring | cells | cell | sight line | triangles |
|---|---|---|---|---|
| Grey ring 1 | 18 × 20.0° | 140 m | 91 m | **48,128** |
| Green sub-floor | 15 × 24.0° | 118 m | 76 m | 38,720 |

**"Seamless" is the project's word, so it is a test rather than a claim.** Touching bounding
boxes do not prove two cells meet — a crack in a ring corridor is a hole a player falls through
at 1 g. `cell_seam_report()` compares the **shared edge itself**, vertex for vertex, in the
radial plane the cells were cut on: 22 vertices each side, identical to 0.1 mm, in every sector.
The **wrap-around** seam is asserted separately, because it is the one a `range(n)` loop never
reaches and the one where a rounding error in 360/n would surface.

`docs/render-cell-seam.png` shows it from inside, with the two cells tinted orange and blue: the
second cell only appears at the very end of the visible run, where the curve takes over. **The
player never sees a cell boundary as a boundary** — which is what sizing cells against the
sight line was for, now confirmed by eye as well as by assertion.

**Three findings worth carrying:**

- A **bent** corridor costs **+20%** per metre over the straight kit — 343 tri/m against
  285 — because each 2.5° section of the bend carries its own end caps. Gated, so the overhead
  stays visible rather than quietly growing. Welding sections is the fix if it does.
- Grey ring 1's cells are at **80% of the cell budget with structure alone**, before any
  dressing, props, signage or NPCs. Grey is the sector where the interior kit will have to get
  cheaper, and it is the widest ring in the station that is also the reason.
- `ring_arc()` now takes an explicit radius. It previously placed corridors at the ring's
  *mid-radius*, but a ring is a zone of a dozen decks and a corridor sits on **one deck's
  floor**.

`interior.py` self-test: **112 assertions.** `budget.py`: **14 gates.**

## Session 2w (cont.) — the whole interior, counted

`cell_manifest()` enumerates every streaming cell in the station. The headline:

> **210 decks · 2,330 cells · 80.6 million triangles** of interior corridor structure.

That number is ADR 0003's argument restated as a quantity. An interior this size **cannot be
committed as mesh files and cannot be hand-authored**. It is generated from the schema,
deterministically, and the repository stores the rule rather than the result. The manifest is
metadata only — 71 KB describing 80.6 M triangles.

| sector | decks | cells | outermost floor | gravity | cell cost |
|---|---|---|---|---|---|
| **Grey** | 90 | 1,210 | 402.2 m | 1.445 g | 48,128 tri |
| Red | 45 | 438 | 211.8 m | 0.761 g | 36,520 tri |
| Blue | 37 | 318 | 167.7 m | 0.603 g | 34,372 tri |
| Yellow | 29 | 226 | 137.1 m | 0.492 g | 32,480 tri |
| Green (sub-floor) | 9 | 138 | 281.9 m | 1.013 g | 38,720 tri |

**Grey is more than half the station's interior** — 90 of 210 decks. That is a consequence of it
sitting at the widest part of the hull, and it is quietly corroborating: the on-screen "Grey 17"
needs a sector with a lot of decks, and this one has ninety.

**Committed metadata is non-derivable metadata.** The first version serialised all 2,330 cell
records, every field of which follows from its deck's `cells` and `cell_deg`. That is the same
fact stored twice, and two copies eventually disagree. The file now carries the 210 deck records
and the rule for expanding them: 537 KB → 71 KB. CI regenerates it and fails on a diff, so a
schema change that moves deck radii or cell costs shows up as a change rather than as a stale
file nobody reran.

## Session 2x — the drum ground and the tram (IN FLIGHT, verification pending)

**Read this before starting anything.** Two modules from a 5-agent workflow are committed and
their self-tests pass, but the **adversarial verification pass had not reported when this was
written**. Treat them as sound-but-unreviewed. A third module (`station/core_tube.py`) was still
building.

| module | self-test | what it is |
|---|---|---|
| `station/drum_ground.py` | 69/69 | the drum's ground as a deterministic heightfield with a 5-level LOD chain |
| `station/tram.py` | 36/36 | the guideway tram — exterior car and a saloon authored for the `35a` passenger view |

Existing suites unaffected: validate 28/28, interior 117/117, budget 14/14, kit OK.

**Ground:** 448 × 640 cells (3.90 × 4.04 m), 280 patches. Uniform finest LOD would be 573,440
triangles — **2.2× the entire drum allowance**, which is the argument for the chain existing.
LOD-resolved and swept over 36 standing positions, the worst visible set is **105,920 triangles
(0.023 tri/m²)**, 41% of the headroom. Switch distances 245 / 550 / 1,270 / 4,668 m are *derived*
from measured height error against curvature sagitta — and the sagitta is asserted so a future
retune cannot silently fall back to facet width, which is the mistake `CONTRIBUTING.md` records.

**Tram:** car length stored as **4.0 truss bays**, not as metres, so it re-derives if INV-012 is
ever corrected. One car 1,252 triangles exterior, 4,158 with the saloon. Being literal about `35a`
made it 2.5× cheaper: the long bench has *continuous* cushions, and modelling one cushion per
seated person had cost 6,432 of the first build's 10,106 triangles.

New inventions logged: **INV-014** (the `LAND_USE` band table, logged retroactively — it had
driven the drum's appearance since the shell was first generated and was never written up),
**INV-015** (terrain spectrum), **INV-016** (parcels and roads), **INV-017** (tram dimensions and
suspension). **INV-012's wording was corrected**: "bay to depth roughly 1.2–1.5" was actually the
*zigzag* pitch, and a Warren triangle's base spans two bays, so the next reader to trust it would
have halved the truss.

### Defects these modules found in code they were forbidden to touch

All four are mine to fix and none is fixed yet. They are the next increment.

1. **`interior.drum_interior()` emits no risers between land-use bands.** Only the top surface of
   each band, so there are **six longitudinal slots the full length of the drum** wherever the
   relief changes. Invisible against a dark background, which is why four sessions of renders
   never showed it. Needs geometry and an assertion.
2. **`budget.py`'s ground-density gate is a gate in name only.** It measures the old flat shell
   (0.005 tri/m²) and will keep passing whatever the ground costs. It must call the ground's own
   worst-case, and the drum visible-set line must swap the 23,040-triangle shell for 105,920.
3. **Nothing in CI runs either new module.** `.github/**` was off-limits to the agents.
4. **The heightfield replaces `drum_interior()`'s shell but does not delete it**, and nothing stops
   both being emitted into one scene — they would z-fight across most of the drum. No assertion
   catches it.

### Also newly established

`29a` shows a **second, different transit system** — a green-and-yellow car on an elevated track
at garden ground level with its own station canopy, sharing nothing with the white/maroon guideway
tram. Not modelled. Recorded so a future session does not assume the guideway tram serves the
ground.

## Session 2y — the drum leaked, and the tests said it did not

The 5-agent verification pass reported. It ran the modules, computed clearances rather than
eyeballing them, and deliberately broke each self-test to see whether it failed. It confirmed
the builds were sound and found the defects were mostly in **my** code, in exactly the places
nothing was measuring.

### The drum was open in two places, for four sessions

`drum_end_cap()` was **4,064 boundary edges out of 7,684** — 3,744 of them nowhere near the rim
or the aperture. From inside the habitat you saw straight through the bulkhead in dozens of
places. Three independent causes, all fixed by one decision:

- per-course segment counts put a T-junction at every course boundary, because a coarse course's
  edge vertices are not a subset of a fine course's;
- the checker offset moved alternate plates 0.35 m in z with nothing bridging the step;
- the axial course walls were built at a third segment count again.

The cap is now **one continuous lathe** at a single fine segment count, with the plating as
material groups and the ribs and rim lights as closed boxes laid on top. The measured
"roughly square plates" character survives untouched, because the tessellation never carried it —
the **rib spacing** does, and that is still per-course. Checker-plating became a group rather than
0.35 m of relief, which is what it always was: a plating pattern, and 0.35 m on a 278 m radius was
never going to read as relief.

`drum_interior()` emitted only the **top surface** of each land-use band. Neighbouring bands differ
by up to 9.5 m (settlement +7.0 against water −2.5), so there were **six longitudinal slots running
the full 2,586 m of the drum**, straight through the ground into the sub-floor decks. Now closed by
riser walls — and the risers face the *low* side, because a cliff is seen from below and below here
means the larger radius.

**Neither was visible in four sessions of renders, because a hole shows the background through it
and the background is black.** An agent found them by rendering against magenta.

### The fix that matters more than the geometry

`boundary_edges()` now measures what no render could: edges used by exactly one triangle, welded on
rounded coordinates because the generators emit coincident duplicates. Six new assertions:

| | |
|---|---|
| drum shell closed except at its two ends | 374 boundary edges, all at z 3839 / 6425 |
| drum shell has no non-manifold edges | 0 |
| every land-use step closed by a riser | 6 steps |
| each cap closed except at rim and aperture | 192 edges, 0 stray |
| each cap has no non-manifold edges | 0 |
| ribs and rim lights are solids, not flat patches | opposing-face test |

**All three verified by deliberately breaking them**: removing the risers reopens 324 edges at
eleven z values; flipping the cap winding gives 0/1536 facing correctly; making a rim light flat
again gives 192 non-manifold edges.

That last assertion replaced a genuinely vacuous one. The old cap test put ribs and rim lights in an
`else` branch that scored **every one of 768 triangles as passing** — a test that could not fail, on
20% of the cap.

### Also this session

- **INV-018 / INV-019** log the core shuttle tube (radius 19.5 m, measured as a *ratio* so the
  sheet's 2× vertical exaggeration cancels) and its hub. `core_tube.py`, 65/65, now committed.
- **A wrong canon citation corrected in `core_tube.py`**: it defended its one measured dimension
  against **C-005**, which is a horizontal splice in the Contract 5 scale bar — a different defect
  entirely. The applicable ruling is `00-MASTER` "Radial spacing" / C-004 UPDATE item 3. The
  argument was always aimed at the right ruling; a reader checking the citation would have verified
  the wrong thing and concluded the defence held.
- **CI now runs `drum_ground.py`, `tram.py` and `core_tube.py`.** None of the three was wired into
  anything when it landed.

Drum visible set is now 51,128 / 300,000 (17%). `interior.py` self-test: **128 assertions**.

### The task list had three stale session-1 entries, and one of them cost a bad brief

Audited every pending task against the code in 3q, after a brief went out claiming two defects had
been open since session 1 and the agent receiving it found both closed. The list is not a record of
what is undone:

| # | claimed | actual |
|---|---------|--------|
| 10 | crude exterior components | done in 3q — cobra bays and all three dome-based components |
| 12 | tram cars pass through the spokes | **closed in 2y**, `interior.spoke()`'s framed portal |
| 13 | vacuous assertions in drum_ground and tram | **the two named ones closed in 2y/3e** |
| 14 | record the car-length conflict | **already recorded**, `CONFLICTS.md` C-008, and thoroughly |
| 11 | junctions and doors on streaming cells | **genuinely open** — verified below |

Only #11 survived the audit. `interior.deck_cell()` is four lines: it calls `ring_arc()` for one
deck over one arc and updates metadata, so a cell is a plain corridor run — 29,920 tri, 8 sections,
no junction and no door groups in it. The kit has both; they are simply not placed on the rings.

**The lesson is the one this repository already knows and keeps paying for: the register has to
compute its answer.** `directory.py` does, which is why its number can be trusted and argued with.
The task list does not, so it drifted into a source of false premises — and a false premise handed
to an agent is a whole agent-run spent on a closed defect. Check any task against the code before
briefing anyone on it, including yourself.

### The layer-4 count is coupled to `tools/export_scene.py` — read this before believing a number

`directory.py`'s layer-4 figure is not computed from `directory.py` alone. `_lit_keys()` imports
`export_scene`, reads `EXTERIOR_CALIBRATION`, `DRUM_FRAME_CONTRIBUTION` and `drum_parts()`, and
reads `godot/scenes/exterior.tscn` back off disk. **Its number is only meaningful against a
committed copy of those files.** A session that runs `directory.py` while anything is mid-edit gets
a number that describes a tree nobody will ever commit — which happened in 3q, where a concurrent
agent read 745/747 against a half-rewritten `export_scene.py` and correctly declined to treat it as
a regression.

This coupling is deliberate and worth keeping: it is what makes the count falsifiable rather than a
field somebody types. But it means **the number is a property of the tree, not of the register**.

### Still open from the verification — next increment

1. ~~**BLOCKING: tram cars pass through the radial spokes.**~~ **CLOSED in 2y** by
   `interior.spoke()`'s framed portal, and re-verified in 3q by an independent surface test:
   0.500 m at the portal header, 0.350 m at the truss bottom chord, with 0 of 200 spoke vertices
   and 0 of 2,632 truss vertices outside the obstacle models used to measure it. **The guard was
   the problem, not the geometry** — see below.
2. **`drum_ground`'s periodicity assertion is vacuous.** It compares `sample(0.0, w)` against
   `sample(1.0, w)`, but every consumer applies `u % 1.0` first, so it is a value compared against
   itself. Proved by monkeypatching in a real 3.295 m seam cliff — the test still reported 0.000
   and passed.
3. ~~**`tram`'s "measured proportion" assertions are algebraic identities**~~ **CLOSED in 3e**,
   and nine MORE vacuous assertions were found in `tram` and `drum_ground` in 3q and replaced,
   each demonstrated failing. Assume more exist: every one so far was found by someone
   deliberately breaking the thing an assertion guarded, never by reading it.
4. **Car length disputed between two authority-1 frames.** `34b`'s rectification gives 3.9 bays
   (96 m); `33a` shows a whole car with ~5 window bays and a length:height near 1.8:1 against the
   model's 21 bays and ~9:1, i.e. **3–4× shorter**. This needs recording as a conflict, not
   resolving silently in `34b`'s favour.
5. **Ground does not meet the end caps** — a 1.2 m axial mismatch, because the ground fades to the
   sector extent and the cap's outermost course stands 1.2 m proud of it.
6. **Ground tagging widths are bound to the LOD ramp width**, so avenues render 31.2 m wide and
   trunk roads 51 m instead of 20 m; the settlement band comes out 62% street.
7. **`budget.py`'s drum gate still measures the old flat shell**, so the ground's real cost is
   ungated.

## Session 2z — IN FLIGHT AT THE SESSION LIMIT. Read this before anything else.

The owner raised the standard to **AAA across every dimension** (see `CLAUDE.md`, "The standard"
and "The plan, in order"). A 5-agent workflow was launched to build phase A — the ability to
*see* AAA — and the session hit its time limit mid-run. Everything on disk at that moment is
committed and pushed. **Nothing was lost. Nothing here has been panel-reviewed.**

### How to resume

```
Workflow({scriptPath: "/root/.claude/projects/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/workflows/scripts/b5-aaa-foundation-wf_e8d85485-09b.js",
          resumeFromRunId: "wf_e8d85485-09b"})
```

Resume is **same-session only**. If that fails — which it will in a fresh session — do not try
to recover the run. The builders' output is already committed; what is missing is the *critique*
and *rework* rounds. Re-run those directly against what is on disk, using the four dimensions in
`docs/AAA-STANDARD.md`. The script is the template; the per-item prompts are in it.

### What landed, unreviewed

| | |
|---|---|
| `docs/AAA-STANDARD.md`, `tools/aaa_gate.py` | the scored rubric and the gate that catches **regression**, which a one-shot critic cannot see |
| `station/materials.py` + ~50 `.tres` + 4.7 MB textures | material system, exported to Godot from one Python source so the two cannot diverge |
| `tools/render_godot.sh`, `tools/export_scene.py`, `godot/scripts/render_shot.gd`, `godot/scenes/{exterior,drum}.tscn` | the engine render path, rebuilt around current geometry |
| `docs/engine-exterior.png`, `-detail`, `engine-drum-interior.png` | **the first engine frames of the drum interior** |
| `station/interior.py`, `station/tram.py` | the blocking spoke fix |

Self-tests at snapshot: **interior 141/141** (was 128), **tram 44/44** (was 36).

### The blocking defect is fixed

Tram cars were passing **6.43 m through the radial spokes** — structural, not a placement
accident: the guideways sit in the spoke planes because the spokes are the only thing that can
carry a 2,586 m truss, so moving the cars could never fix it. The spoke now has an aperture.
Both verifiers found this independently, one by point-in-box over 3,144 vertices, one by
rendering it.

### First job next session

1. **Run the critique rounds** that did not happen. Judge against `docs/AAA-STANDARD.md`; every
   dimension must reach 4. Be as harsh as the last panel was — it caught an end cap with 4,064
   open edges and two assertions that could not fail.
2. **Check `docs/REFERENCE-GAPS.md` exists.** The reference-audit agent may not have finished. If
   it did not, that document still needs writing: the owner has offered to supply more reference
   and is otherwise hands-off, so it is the only channel for asking, and a vague ask wastes it.
3. **Verify the Godot binary situation.** It is container-local and a ~61 minute rebuild, so it
   is gone with this container. Whether the agent found a way to make it survive is unknown; if
   not, that is a tax on every future session and worth solving properly.

## Session 3a — the engine renders the interior, and it is not AAA yet

Phase A's goal was **the ability to see**, and it is met. `tools/render_godot.sh` drives Godot
4.4 double-precision on Mesa lavapipe through Xvfb and produces real Forward+ frames — shadows,
real lights, materials, exposure. `docs/engine-drum-interior.png` is the first engine frame of
the habitat drum. The binary was rebuilt and is at `/home/user/godot-build/dist/` with a
`.tar.xz` beside it.

The critique round never ran (the session hit its limit), so this is my own panel pass over what
landed. It is not a substitute for the adversarial pass and that still needs doing.

### CORRECTED: the speckle is sub-pixel RELIEF, not a misapplied LOD

**My first diagnosis of this was wrong and is corrected here.** I claimed the frame drew lod0
where lod1 was due, computing "a 20 m fitting spans 2.7 px" from a framing assumption I had
guessed rather than derived. Computing it properly: the exterior orbit is 9,200 m from the aim
point, but the **nearest hull point is 5,163 m**, which is *inside* lod1's 6,000 m switch. lod0
was the correct level. The LOD was not misapplied.

The real cause is sharper, and it is a gap in the switch criterion itself:

- `lod.py` derives switch distances from **silhouette deviation** — the outline error from a
  coarser radial segment count.
- Greeble fittings stand **3–11 m proud** (INV-006). Their **relief** stops resolving at
  **3,088 m** (a 3 m fitting) to **11,323 m** (an 11 m one), against the 1.5 px budget.
- So from roughly **3 km to 6 km** the hull draws greeble relief nobody can resolve, while still
  legitimately needing lod0's outline. That is a band ~3 km wide where the mesh is guaranteed to
  produce high-frequency shading noise, and the silhouette criterion cannot see it.

The greebles were never sub-pixel in **footprint** — at 5,163 m a 20 m fitting is about 5.8 px.
They are sub-pixel in **relief**, which is a different measurement and the one that governs
whether a bump reads as form or as noise.

**The proper fix is to decouple the two schedules.** `LEVELS` steps `radial_segments` and
`greeble_detail` together, so the chain cannot express "lod0 outline, lod1 greebles" — which is
exactly what 3–6 km wants. That needs its own change and is recorded as the next visual increment.

**Done this session:** `lod.py` now computes and reports the relief-resolution distances beside
the silhouette ones, so the gap is visible in the manifest rather than latent. And
`tools/export_scene.py` gained `pick_hull_lod()` — the chain genuinely was never connected to the
renderer, so a 120 km shot would have drawn all 327,898 lod0 triangles to cover a few hundred
pixels. Selection is by distance to the **nearest** point of the hull bounds, not to the aim
point, because an 8 km station seen from 9 km has its near end at 5 km and choosing on centre
distance would decimate geometry twice as close as the number justifying it.

### Other findings from the same two frames

| | |
|---|---|
| **Scale does not read** | No aerial perspective in a 2.6 km volume. Everything is equally crisp, so the drum reads about 50 m across rather than 556. The owner named "scale" as an AAA dimension; haze is the fix and it is cheap. |
| **The ground is flat colour** | Large unbroken areas of olive-green. The heightfield's parcels, hedge banks and roads are not reading at all in the engine — worth checking whether the material is bound and whether the detail is simply below the LOD in use. |
| **Light runs blow out** | Pure white with no falloff structure; they read as blown highlight rather than as fittings. |
| **Black gap at the cap/ground junction** | Right of frame in the interior shot. Consistent with the 1.2 m axial mismatch the verifier reported between the ground rim and the cap's outermost course, which is still open. |

Honest scores against `docs/AAA-STANDARD.md`: **craft 2, fidelity 3**, performance not measured
this session, robustness good (self-tests green — interior 141/141, tram 44/44).

That is the right result for phase A. The point was never that the first engine frame would be
AAA; it was that we could finally *tell*.

### `docs/REFERENCE-GAPS.md` written — and the finding in it is worse than expected

Ranked ask for the owner, verified against the actual folders rather than assumed. The headline:

- **`reference/10-interiors-generic-kit/` is EMPTY.** The corridor kit is 210 decks and 2,330
  cells — the large majority of walkable space — and every dimension in `interior_kit.py` is
  extrapolated from proportions in a *single frame of one sector*. This is now the top ask.
- `18-audio-notes/` and `19-video-clips/` are empty; no audio work exists at all.
- `12-starfury/` has four files, **all exterior**; the cockpit was an explicit opening-brief
  requirement and has zero coverage.
- `16-signage-typography-ui/` has three files and all three are **logos** — so C-004 has nothing
  to close on.
- Grey has **one** interior frame and is **90 of the station's 210 decks**.

## Session 3b — the corridor reference landed, and the kit was modelling one space

The uploads arrived in `reference/10-interiors-generic-kit/` (8 files, of which
`central corridor.webp` and `grey level 1.webp` duplicate ones we already held). They
contradict a core assumption immediately.

**The kit modelled ONE corridor. The reference shows at least three**, and they are not
variations on a width — they are different kinds of space:

| class | frame | character |
|---|---|---|
| **residential** | `grey level 1.webp` | pale grey-tan, pilasters, horizontal banding, vertical light strips, chequered deck, portal frames. Narrow, quiet, finished. |
| **concourse** | `central corridor.webp`, `more hallway.jpg` | tall volume framed by large **elliptical ribs**, lit strip down the deck centre, downlight pools, wall screens, **upper walkway** over the lower deck |
| **service** | `more hallways.jpg` | overhead truss instead of a soffit, vertical light tubes, chequered lit strip in deck grating, warm backlit panels, litter on the deck |

Building 210 decks out of one profile would have made the whole interior read as a single endless
hallway, which is the opposite of what the footage shows.

**The elliptical rib arch is the signature of a B5 interior and the kit did not have it.**
`ring_frame_spacing_m` existed as a constant with a comment pointing at `central corridor.webp`,
and nothing ever built one. `rib_arch()` does now — see `docs/render-concourse.png`.

**Two figures are measured, not chosen:**

- An EarthForce officer stands in a circular downlight pool in `more hallway.jpg`. At 1.75 m he
  is 261 px → **149 px/m**; the pool spans 234 px → **1.57 m**. That is the only absolute length
  these frames yield directly, and `DOWNLIGHT_POOL_M` is it.
- The concourse is **two decks** tall because `central corridor.webp` shows an upper walkway with
  people on it above people on the lower deck. At INV-010's 3.6 m pitch that is **7.2 m**, and the
  self-test asserts it stays a whole multiple — a fractional height lands the walkway between decks.

The **9.0 m concourse width is the weak figure** and INV-020 says so plainly. No frame gives a
concourse width against a known length, because the officer stands mid-space rather than against
a wall. *One frame with a person against a concourse wall would close it.*

**Third winding bug of the same family.** `downlight_pool` and `deck_strip` lie flat and must face
up; ascending angle in XZ with +Y up gives a downward normal, so both were invisible from the only
place they are ever seen. Found by rendering and seeing 836 of 2,100 triangles survive culling.
The self-test now checks every flat deck element, and both new assertions were verified by
breaking them and watching them fail.

### Still to do on the new reference

`more zocalo.png`, `transport.jpg`, `garden more.jpg` and `gardens or greenery.jpg` have **not
been mined yet** — the Zocalo is the station's social centre and has no geometry at all, and
`transport.jpg` may bear on the tram car-length conflict.

## Session 3d — the Zocalo reviewed, and its bay seams welded

**Both workflows died.** Last write 01:09; the container restarted under them and nothing moved
for 5h38m. Of workflow 1's four builders, **two landed** (`zocalo.py`, `lod.py`); the
drum_ground repair and the metric hull skin did not. Of the gazetteer's six researchers, **four
landed**. **No critique round ran on anything.** All output was committed as it appeared.

So this session did the review step the loop was missing, on the largest unjudged thing:
`station/zocalo.py`, 75 KB and 90/90 self-tested, that nobody had ever looked at.

### It is good work

The module solved a **photogrammetric scale** off `more zocalo.png` rather than guessing —
horizon at 370.5 px and a seated eye height of 1.265 m solved from two 0.75 m features at two
depths, and a focal length of 2,517 px from the table-top ellipse aspect. Bay dimensions are
whole multiples of `DECK_PITCH_M`: a 21.6 m bay, a 12.6 m well against a measured 12.7 m arch
span, tiles at 0.45 m. `docs/render-zocalo.png` shows ribs arching over a two-level volume with
galleries, shopfronts, a staircase, pedestal tables and the "5" chairs.

### The defect the review found

**Every bay seam carried doubled geometry.** Non-manifold edge count by run length was 10, 162,
314, 466 for one to four bays — **+152 per seam**, all of valence exactly 4, with 106 of them
lying precisely on the seam plane. Two independent mechanisms:

1. Every longitudinal member — walls, rails, purlins, gallery slab and beams — is emitted per bay
   as a **closed solid**, so adjacent bays meet face to face and each edge around that face is
   shared by four triangles instead of two.
2. The **rail is emitted twice** at each shared boundary: 24 triangles in identical position and
   winding. A duplicate is not a touching face, so the plane test cannot see it — the rail
   straddles the seam rather than lying in it.

Both are invisible in a render and both z-fight in the engine.

**Fixed in `zocalo_run()`**: a face lying entirely in an interior seam plane is sandwiched between
two bays by definition and is dropped; then exact duplicates are removed on a winding-preserving
key, so an oppositely-wound twin (a genuine touching face) survives. The ribs also sit on seam
planes but are 0.55 m deep, so their flanks are never coplanar with one.

**Result: 10, 20, 30, 40** — exactly 10 per bay, **nothing per seam**. Boundary edges go
312 → 524 → 736 → 948, a constant +212 per bay, which is *less* than a standalone bay's 312
because each seam retires 100 open edges. The weld closes rather than opens, confirmed against a
magenta background.

Three new assertions, and **both fixes verified load-bearing** by disabling each independently:
the seam-plane weld alone leaves 162/314/466, duplicate removal alone leaves 56/102/148.

### Still open

- **10 non-manifold edges inside a single bay** — a separate, smaller mechanism, not the seams.
- The drum_ground repair and metric hull skin never ran; their specs are in the dead workflow
  script at `.../workflows/scripts/b5-zocalo-and-debt-wf_03274a8a-d9c.js` and the findings they
  were to fix are listed in session 2y.
- Gazetteer is missing `LIFE-SUPPORT-AND-INDUSTRY.md`, `MEDIA-AND-COMMS.md` and the synthesis
  pass that cross-checks every proposed location against the 210 built decks.

Suites: validate 28/28, budget 14/14, export_scene 24/24, zocalo 96/96, lod 94/94,
interior 141/141, drum_ground 69/69, tram 44/44, kit OK.

## Session 3e — drum_ground: a test that could not fail, and a slot round both ends

Two of the four review findings against `station/drum_ground.py` fixed. Its repair agent never
ran (its workflow died), so the findings were sitting in session 2y with evidence and nobody had
acted on them.

**1. The headline seam assertion could not fail.** It compared `sample(0.0, w)` against
`sample(1.0, w)`, but every consumer inside `sample()` applies `u % 1.0` first — so the two calls
are *the same call*, and the check was a value against itself. Confirmed by removing the angular
wrap from `_value_noise`: that puts a genuine **3.295 m cliff** the full 2,586 m length of the
drum at one angle, and the old metric still reported `0.000e+00` and still passed.

Replaced with a **continuity** test across the seam — `sample(1-eps, w)` against `sample(eps, w)`
— bounded at 5 cm rather than 1e-12, because two samples a real distance apart differ by however
much the terrain legitimately varies over that distance, and demanding exact equality would be
asserting the terrain is flat there. The new test catches the 3.295 m cliff, and catches a band
boundary defect the old one missed too.

**2. The ground did not reach the end caps.** It ran to the sector's z extent, but the cap's
outermost course stands `ENDCAP_STEP_M` proud, so at the floor radius the cap plate sits beyond
where the ground stopped — an annular slot **0.6 m** wide right round the drum at *both* ends.
(The review measured 1.2 m; the session-2y cap rebuild, which made checker-plating a material
group rather than 0.35 m of relief, had already halved it.)

The old assertion could not see this **because it measured only one of the two surfaces**: it
checked that the ground's *relief* faded to zero at z0/z1 and never looked at `drum_end_cap()`.
A surface can arrive perfectly flat and still stop short.

Fixed by deriving the ground's extent from `cap_plane_z()`, which reads the cap's own constants
rather than restating them — so a change to the cap's course depth moves the ground with it
instead of silently reopening the slot. Ground now spans **3837.8 … 6426.2** against the sector's
3839 … 6425, and the measured gap at the floor-radius ring is **0.0000 m** at both ends.

Both fixes verified load-bearing by reverting each: the extent revert reports "0.600 m short of
the cap plate" at both ends.

**Still open on this module** — findings 3 and 4 from the same review, both about tag widths
being bound to the LOD ramp width rather than to the real feature width:

- `sample()` tags a settlement cell "avenue" within `_step_ramp_m()/2` = 15.6 m of a block edge,
  giving a **31.2 m avenue** on 62.4 × 64.6 m blocks — point-sampled, avenue is 16.17% of the
  drum against settlement's 4.67%, so the settlement band is **62% street**.
- `_road_mask` ramps over 31.2 m beyond the 10 m half-width, so trunk roads tag **51.2 m** wide
  against a stated `TRUNK_ROAD_W_M = 20`.

The ramp is a constraint the LOD imposes on how sharply the surface may step; the *kind tag*
should follow the real feature width, with a separate verge kind for the ramp.

Suites: validate 28/28, budget 14/14, drum_ground 71/71, zocalo 96/96, interior 141/141,
lod 94/94, tram 44/44.

## Session 3f — the LOD ramp was being used as a street width

The last two `drum_ground` review findings, and they turned out to share one root cause worth
stating plainly: **`_step_ramp_m()` is not a width.** It is one stride-8 cell, 31.2 m, and it
exists to constrain how sharply the heightfield may step so the LOD chain stays honest. It was
being used as the size of a street and as the extent of a road's kind tag.

| | was | now |
|---|---|---|
| street on a 62.5 × 64.7 m block | 31.2 m → **~74% of the band was street** | 10 m → **29%**, asserted against the area its own width implies |
| trunk road tagged width | 51.2 m against a stated 20 | **4.51%** of the drum measured against **4.58%** predicted |

The geometry still ramps over the full 31.2 m, because it must. What changed is that the **kind
tag** stops at the made width: a carriageway is flat at its own width, then a verge (`VERGE_W_M`,
4 m, its own new group), then untouched band. `docs/render-drum-settlement.png` shows the result
— pale block plateaux, streets at a believable width, a verge strip along each edge and a wider
trunk road crossing. Logged as **INV-021**.

### Two measurement traps, both of which produced confident wrong numbers

1. **The block grid is 40 cells along the drum, so `w = 0.5` lands exactly on a block boundary**,
   where `d_edge` is 0 by construction — sampling there reports *every* settlement cell as
   street. The original review's "62% street" figure and my own first re-measurement both hit
   this. Measure off-lattice.
2. **A width must be a width at both ends of the fix.** My first attempt set the *verge* tag to
   one full LOD ramp; since that is half a block, it tagged every settlement cell as either
   avenue or verge and plain settlement disappeared. Caught only because the coverage numbers
   still looked wrong after the "fix".

New assertions derive the expected coverage from `AVENUE_W_M` and the block pitch rather than
comparing against a remembered number, and are verified load-bearing: reinstating the ramp-width
tag reports **76.9% against 29.0% predicted**.

`drum_ground.py`: **74/74**.

## Session 3g — a third reading of C-004, and cell counts aligned to it for free

Read the gazetteer's `LOCATIONS.md` (580 lines, 212 rows, era-locked, every authority-4 row
labelled and the blocked-egress caveat stated up front). Its §1 is the most consequential thing
the research turned up.

**C-004 may have been asking the wrong question for four sessions.** It has been framed as "which
ring is level 1". One source says the number in `Grey 17` is not a radial level at all but one of
**36 angular regions of 10° each**. That would explain C-004's standing puzzle — *no source we
hold numbers a ring* — by the simplest available route: because rings are not what the numbers
index.

**Not adopted, and C-004 stays OPEN.** Authority 4 cannot close what two authority-3 sheets could
not; the same wiki contradicts itself on the same page; and `Brown-57` breaks *both* readings
(57 > 36 regions, and > the 30 levels the same wiki gives Grey). Recorded in `CONFLICTS.md` so a
future session finds it already weighed rather than rediscovering it.

**But the option was taken, because it turned out to be free.** `ring_cells()` now snaps every
cell count **up** to a divisor of 36, so a cell always spans a whole number of 10° regions.

| | snap down | snap up |
|---|---|---|
| worst cell | **59,040** tri — 98% of the gate, structure alone | **48,128**, unchanged |
| Grey ring 2 | 59,040 | **39,360** |
| cells under their own sight line | none | none |

Down was affordable but left nothing for props, signage or NPCs. Up gives *smaller* cells, so it
is strictly cheaper. Station total: **2,330 → 2,646 cells**, 80.6 → **80.5 M triangles**. If the
angular reading is wrong, nothing has to be undone.

Cost: the cell-length-over-sight-line margin falls from a designed 1.5 to **1.12–1.68**. That is
slack rather than the guarantee; the guarantee is that a cell exceeds its own sight line, and it
is now asserted per ring. `interior.py`: **175/175** (34 new), and removing the snap fails 24.

### The gazetteer's other findings, recorded but not yet acted on

- **X-1** may *reconcile* C-002 rather than contradict it: "four cobra bay support arms" × 7 bays
  = the 28 of Contract 5. Does not close 24-vs-28.
- **X-2** a fan source puts the Alien Sector between the docking bays and Red; the authority-3
  schematic puts it aft of the drum. Authority 3 wins.
- **X-3** a fan sector ordering agrees with `other map.png` *exactly*, including Yellow as the
  non-rotating aft half — **but it is very likely an echo of the same print sources, not an
  independent witness.** C-003 stays open.
- **X-6** is a rare authority-3/4 cross-check that *holds*: medical distributed across Red, Green
  and Blue with the primary Medlab in Blue; law and security in Red.

## Session 3h — three rooms built, from the gazetteer's ranked list

Working straight down `docs/gazetteer/LOCATIONS.md` §19. #1 Zocalo was already built; this
session did **#3 the docking bay, #2 the customs signage, and #4 C&C**.

| module | what | assertions |
|---|---|---|
| `docking_bay.py` | the room the launch-and-dock requirement lands in | 18/18 |
| `signage.py` | backlit boards **and the only readable sign we hold, verbatim** | 15/15 |
| `command_control.py` | the bridge, in Observation Dome 1 | 25/25 |

### The docking bay

Width is not a free number: **42 m is the schema's own `cobra_bay` width**, authority 3 off
Contract 5 — the width that document gives *this station* for *this class of structure*. The
self-test asserts it fits: 24 bays at a 254.2 m deck radius get **66.5 m of arc** each. Deck is
at **0.913 g**. One measured length, the deck disc at 10.6 m, from an 11-worker file at 16 px/m.

**A bay is not a hangar, and the geometry says so.** The first placement mapped the width along a
*tangent* and pushed both walls 0.9 m *outside* the pressure hull. A bay is cut into a **rotating**
hull, so its deck follows an arc — corrected, it cambers **0.87 m** across 42 m.

### Signage — the project had none

`16-signage-typography-ui/` is three logos. The module is deliberately two things: board geometry,
and **the text verbatim as canon data**, because what a sign says is a fact about the station, not
a decoration, and belongs in version control rather than baked into a texture nobody can grep.

Transcribed exactly, **including the prop's own spelling** — `ARANGEMENT` with one R,
`ATMOCHEMICAL`. Asserted, because a well-meaning correction is how a transcription rots.

**Three facts these boards establish that are not signage at all:** six atmospheres available
simultaneously with more to order (a life-support number, and the mechanic behind the alien
sector); the station runs on **Earth Mean Time**, which names the clock every NPC schedule was
implicitly on; and there is a **Business Center** handling currency exchange — a sourced location.

### C&C, and a measurement error worth remembering

Dome dimensions are **read from the schema rather than restated** (46 m radius, 34 m high,
Contract 5), and the window is asserted to fit inside it.

The window measurement needed a correction I first omitted. The officer is 175 px → 100 px/m
*at his depth*; the window's fitted arc is 306 px across. Dividing directly gives **3.1 m and is
wrong** — the window is in the bulkhead *behind* him and px/m falls with distance. At ~5 m to him
and ~4 m more to the bulkhead, the scale there is 56 px/m and the window is **5.5 m**. A factor
of **1.8**, and the same trap that put the tram car length in dispute (C-008).

**Five defects the assertions caught while building C&C**, every one invisible in a render:
the glazing laid flat (XZ disc where an XY one was needed, so the glass was on the ceiling); the
uncorrected measurement; full-diameter mullions piling into a solid starburst with no glass
between them; a bulkhead with **no aperture**, so the glass was sealed inside 0.30 m of steel;
and glazing wound to face *out* through the bulkhead. The aperture assertion was itself wrong
first time — it demanded the glass stand *proud of* the wall, which fails a correctly glazed
window. Glass sits **in** an opening.

All three wired into CI. **INV-022, INV-023, INV-024** logged.

## Session 3i — the hull allowance went metric, and the prediction attached to it was wrong

`HULL_ALLOWANCE = 0.86` is gone. Every non-drum sector now takes its outermost deck floor from
an **extracted core hull less a metric `HULL_SKIN_M`**, the same 6 m the drum already used.

The fraction was the wrong kind of quantity twice over. It removed **65 m** of notional
structure in Grey and **22 m** in Yellow — pressure hull and frames do not scale with distance
from the spin axis. And it multiplied the **mean of a sector band**, which describes no surface:
Yellow's band ranges 18–440 m, Blue's 116–268 m, and neither sector has a point where the hull
is at its own mean.

**Extracting the shell.** The radius profile traces the *outline*, so it reports whatever stands
proud at each z. Session 2b's technique — a wide running minimum — is right in principle and
**erodes at a step**: it reported 428.7 m in Grey, below Grey's own narrowest real sample of
436.4 m, a radius no point in the sector has. The operator is a morphological **opening**,
erosion then dilation, which strips protrusions and restores step edges. Asserted per sector.

**The cross-check is what justifies applying it where nothing can be measured.** Run against the
band holding the habitat cylinder it returns **314.3 m**; `habitat_hull_radius()` — written four
sessions earlier, a plain mean over one *named schema feature* — gives **316.8 m**. **2.5 m
apart on a 315 m radius, from two methods that share no arithmetic.**

### The prediction was wrong, and finding that out was the point

`STATE.md` had Grey's **1.445 g** outermost deck recorded as "the visible symptom" of the
fraction, to be fixed when the allowance went metric. **It got worse: 1.693 g.** The 0.86 had
been quietly deleting 65 m of hull that is really there. Grey sits on the aft hull block — the
station's widest structure, identified in session 1, which Miller's table never names — and a
rigid body spinning at a rate fixed by the habitat floor puts 1.7 g on anything 471 m out. No
honest allowance moves it inboard.

So the premise was wrong rather than the arithmetic, and the design answer is the one a real
station would give: **you do not put quarters at the bottom of a gravity well, you put mass
there.** `HABITABLE_G_MAX = 1.25` (**347.9 m**) declares the heaviest deck a person may be
housed on. Every deck now carries a `use` tag.

| | decks | plant | outermost floor | gravity |
|---|---|---|---|---|
| **Grey** | 105 | **34** | 471.2 m | **1.693 g** |
| Red | 59 | 0 | 268.1 m | 0.963 g |
| Blue | 45 | 0 | 211.6 m | 0.760 g |
| Yellow | 33 | 0 | 155.4 m | 0.559 g |
| Green (sub-floor) | 9 | 0 | 278.3 m | 1.000 g |

**Grey's outer 123 m is the station's basement** — tankage, reservoirs, waste processing, reactor
auxiliaries. 26% of the station's interior structure, and a thing the scope asks for by name:
*"the physical plant that makes 250,000 people possible: food, water, air, power, waste."* The
fraction was concealing it behind a plausible number.

The ceiling's **lower bound is not taste**: the drum's own sub-floor stack reaches 1.117 g at the
pressure hull and is occupied, so a ceiling below that would contradict geometry already built.
That is the assertion that fails first if anyone lowers the constant. Logged as **INV-026** and
**INV-027**.

### Three defects the change exposed, none of them the thing being changed

- **`drum_sector()` was comparing a hull radius to a floor radius** — a category error, a surface
  against something 32 m inside it. On corrected shell radii that comparison picks **red**, whose
  shell sits four metres from where the Garden's ground is. Matched hull-to-hull the drum wins by
  **17×**. The old code got the right answer for the wrong reason: the drum band's mean was
  inflated by the aft hull block it happens to contain. The self-test now asserts the **margin**
  — a test that only checks who won cannot tell 17× from a coin toss, and this decides which band
  the entire habitat is built in.
- **The divisor-of-36 cell snap has a 2× gap between 18 and 36.** Grey's widened ring asks for 19
  cells, snaps up to 36, and halves the cell to 82.2 m against a **98.9 m sight line** — the
  player sees 17 m into a cell that is not resident. Snapping up now runs only as far as the
  guarantee holds, then falls back down.
- **The cell gate was pricing tankage as corridor.** It measured deck 0 of the outermost ring,
  which in Grey is plant, at the kit's 285 tri/m — **94.8% of budget**, implying habitat
  corridors had 5% of headroom for props, signage and NPCs. Split by `use`, the worst *habitat*
  cell is Grey ring 2 deck 11 at 1.246 g and **66.2%**. They have 34%.

**Station total: 210 → 251 decks, 2,646 → 3,414 cells, 80.5 M → 110.2 M triangles.** Red, Blue
and Yellow were all being cut short. `interior.py` **175 → 448 assertions**, `budget.py` 15/15,
and every new assertion was verified load-bearing by reintroducing its defect — the plain running
minimum, the floor-matched drum test, a 1.10 g ceiling, the unconditional snap-up, and the
fraction itself.

## Session 3j — phase D opens, and the assertion suites got audited

**`station/npc/` gains `body.py`, `costume.py` and `crowd.py`** — 648 assertions between them,
all green and all wired into CI, which is the only place their gates run.

| module | lines | assertions | what |
|---|---|---|---|
| `body.py` | 2,654 | **501** | fifteen species as parametric bodies, per-individual variation seeded off the npc id |
| `costume.py` | 2,715 | 80 | fabrics, decals, silhouettes, attachments, era-gated |
| `crowd.py` | 2,146 | 67 | placement and density |

Three construction paths — humanoid, encounter suit (**the Vorlon is a robe with no body in
it**, which is the point) and column. Statures span **1.53 m (Vree) to 2.05 m (Vorlon)**.

**`body.py` carries its own closure gates because nothing in the project could see this class of
defect.** The first lineup render showed limbs detached from the torso; signed volume and the
edge census both passed it, because a detached arm is still a closed solid. So it has a
ray-parity `contains()`, and the ray direction is deliberately **not** axis-aligned: the torso's
rings and the leg's root ring both put vertices at exactly z = 0, and an axis-aligned ray grazes
that shared edge and reports inside-or-outside on floating-point luck. **The only vertices it
ever rejected were the ones at z = 0 exactly.**

### Rendered and read — `docs/render-npc-lineup.png`, `render-npc-detail.png`

Against magenta. Fifteen figures, **all closed** — no background bleeds through any of them, and
26,734 of 57,412 triangles draw, which is the backface-cull ratio a solid gives. The Minbari bone
crest reads at 12 m. The Vorlon encounter suit reads.

**What the render shows that the assertions do not, and it is the first rework item for phase D:
the joints are unwelded.** Limb roots *are* inside the torso — that is asserted and passing — but
the lofts **interpenetrate rather than blend**, so a hard crease sits where a deltoid should be
and the shoulders read as a shelf the arms hang off. Craft, not closure. A gate that asks "is the
root inside" cannot ask "does the surface flow", and only looking caught it.

### The assertion suites were audited, and the result is worse than expected

`tools/mutation_sweep.py` (session 3i) perturbs every module-level numeric constant, re-runs that
module's suite in a fresh subprocess, and asks whether anything noticed. Full sweep: **192
mutants in 1,172 s**.

> **Only 41 of 192 constants — 21% — are noticed by their own module's assertions.**

| module | noticed |
|---|---|
| `signage` | **0%** |
| `council_chamber` | 4% |
| `core_tube` | 17% |
| `drum_ground` | 18% |
| `interior` | 25% |
| `command_control` | 28% |
| `zocalo` / `docking_bay` | 29% |
| `tram` | **43%** — the best in the project |

The tool is explicit that it cannot tell an unguarded constant from a deliberately loose one:
`council_chamber.SEATS` 5→6 passes **correctly**, because INV-025 asserts a lower bound on
purpose. So 21% is a floor on the real figure, not the figure. But 0% for `signage` and 4% for
`council_chamber` are not explicable that way, and those two are where the next audit increment
should go.

**Do not read this as "the suites are worthless".** They have caught a door interpenetrating a
portal frame, tram cars passing 6.43 m through a spoke, an end cap with 4,064 open edges and a
drum wound inside out. What the sweep measures is *coverage of the constants*, and it says the
assertions are strong on **relationships** and weak on **values** — which is exactly the shape
you would predict from how they were written.

## Session 3j (cont.) — animation, navigation, and a repeat defect

The six-builder NPC workflow (`wnbmuyt81`, 12 agents) completed. Two more modules landed after
the first three were committed:

| module | lines | assertions |
|---|---|---|
| `body.py` | 2,654 | 501 |
| `animation.py` | 3,022 | **467** |
| `costume.py` | 2,715 | 80 |
| `crowd.py` | 2,146 | 67 |
| `navigation.py` | 2,751 | 86 |
| `schedule.py` + `test_schedule.py` | — | 100 |
| | | **1,201 across the layer** |

All six are wired into CI. `animation.py` (~24 s) and `navigation.py` (~77 s) are now the
slowest gates in the project; they are also the two that touch station geometry, so they are the
two a schema change can silently break.

### The night watch was asleep, again

**Rotating roles declared `work_start = 0.0`, so the first watch ran 00:00–08:00 while the human
sleep block ran 23:00–06:30. The night watch spent 7.5 of its 8 hours asleep.**

That is the *exact* defect `INV-005` records as fixed in session 2m. It survived two sessions
because the assertion guarding it asked only whether `on_duty > 0`, and sampling jitter always
satisfied that. **A threshold of "more than nobody" is not a threshold** — this is the same
family as the vacuous assertions the mutation sweep exists to find, and it is the strongest
argument yet for that tool.

Fixed by anchoring sleep to the holder's own shift as an algebraic identity. **Verified from
outside the code rather than from the report:** sampled across 20,000 ids, coverage is continuous
at every hour, and station-wide on-duty security measures **138–193** against `FACTIONS.md`
§2.2's separately-stated *"roughly 150"* — a figure the module does not read.

### The Starfury cockpit is unblocked, catalogued, and the pilot stands

Owner upload `c5873e5`, four files, all opened and written up in `reference/00-INDEX.md`.
**"Sitting position" is a misnomer**: the authority-2 tub shows a ribbed couch running the full
height of the centreline with a chest yoke and a headrest recess. The pilot is braced against a
near-vertical board, arms forward onto two angled console banks.

**The resolution trap fired for the third time.** The two authority-2 production photos are
**0.23 MP**; the two authority-4 fan models are **3.05 MP** — 13× the pixels, one authority level
worse, and the best-lit material in the folder. Not quarantined (a fan model of the real prop is
legitimate corroboration and says "model" in its own filename), but they are the files that must
not be measured from.

**No absolute dimension is recorded, deliberately.** See the index entry for the failed
segmentation and why no number was published from it.

## Session 3j (cont.) — the plant kit, and four defects only a render found

`station/plant.py`, **24 assertions**, wired into CI. The 62.3 M-triangle corridor placeholder
over Grey's 34 plant decks is gone.

**The structural decision:** plant space is **not decked at `DECK_PITCH_M`**. A 3.6 m pitch is a
corridor's pitch and a tank farm wants height, so the 34 decks regroup into **7 bays of ~17.7 m**
and the *bay* is the unit built. The 4-deck remainder is kept as a shallower top bay, not dropped.

| | |
|---|---|
| whole zone | **453,528 tri** against the 62,273,664 placeholder — **0.7%** |
| tankage laid out | 1,232,508 m³, **3.1×** the 397,500 m³ reserve, **0.88%** of the zone |

**Why the reserve assertion is not circular:** tank *count* is not derived from the volume it must
hold. It falls out of a fixed farm lattice, and the test then asserts the result clears L-04's
reserve — a sparser lattice would fail. A **second assertion brackets it from the other side**
(tankage < 10% of plant volume), and that pair is what caught the first implementation, which
tiled the annulus and produced **65.1 M m³ — 164× the reserve and 46.6% of the zone**.

### Four defects, three found only by rendering it — the self-test passed 21/21 while they were live

1. **`_place()` reverses winding**, Jacobian determinant **−1**. Everything through it was
   inside-out. Found by standing on the catwalk and **seeing magenta through the floor**. Third
   instance of this family in the project. The gate now asserts on a **placed** solid, because
   the local test passes either way — which is exactly what let it ship.
2. **The pipes were 457 m in radius** — radial *position* passed as *radius*.
3. **The frame rings spanned 360°**, so every cell carried a ring round the whole station.
4. **The catwalk was a 158 × 120 m plate** spanning the full arc *and* z, with `CATWALK_W_M` used
   as a radial offset rather than a width.

**Two lessons worth more than the fixes.** A new gate checking that no piece is radially larger
than its bay **missed** the 360° ring, because it measures **vertex** radii and every vertex of a
coarse polygon sits at the same radius while its chords cut far inside — *gates that sample
vertices cannot see chords*. And `CATWALK_CLEAR_M` was 1.8 m, a crawl space giving a 1.7 m person
100 mm, guarded by `CATWALK_CLEAR_M >= 1.8` — the value itself, so it could not object.

`docs/render-plant-bay.png` is the corrected view. It reads flat grey because there is no
lighting or material yet; that is phase C, not a geometry defect.

Logged as **INV-028**.

## Session 3k (cont.) — residential quarters, and the class gradient as a test

`station/quarters.py`, **48 assertions**, in CI. The most-repeated interior on the station;
`npc/crowd.py` previously had nowhere to send 250,000 residents home to.

`LOCATIONS.md` §11 states the spine in one line — *"Gravity does the work for free… the people
with the least power live where they weigh the most"* — and this asserts it against **live**
geometry rather than restating it.

| rank | class | sector | gravity | unit |
|---|---|---|---|---|
| 0 | command | Blue | 0.760 g | 34 m², **shower** |
| 1 | personnel | Blue | 0.760 g | 18 m² |
| 2 | diplomatic | Green | 1.000 g | 46 m², **shower** |
| 3 | alien_resident | Green | 1.000 g | 22 m² |
| 4 | civilian | Red | 0.963 g | 16 m² |
| 5 | transient | Red | 0.963 g | 9 m² |
| 6 | **lurker** | Grey | **1.693 g** | **no rooms** |

**2.23× body weight** and **5.1× floor area** between an ambassador and a transient.

**Two claims I had to make honest.** My docstring said rank and gravity were monotonic across
every pair — they are not (Green's 1.000 g outranks Red's 0.963 g), and that is a docstring lying
about its own code. And the first area assertion failed correctly: **rank is social order, not
floor area** — ambassadorial suites outrank command quarters here. What holds is that rank orders
area *within a sector*, asserted per sector.

**`lurker` emits nothing, deliberately.** §11 says Downbelow is "corridors and chambers, not
rooms" and `plant.py` already builds it. `unit_dims()` returns `(0, 0)` rather than a fake cell —
handing back a 1 × 1 m room is how Downbelow quietly becomes an apartment block.

**A stale canon figure is flagged, not copied.** §11 quotes Blue at **0.603 g**, which predates
INV-026; it is now **0.760 g**. The module reads gravity live and *asserts the divergence*, so
nobody re-copies the old number. **§11 needs refreshing.**

Logged as **INV-032**. `docs/render-quarters.png`.

## Session 3k (cont.) — the bar, and the largest workplace on the station

`station/hospitality.py`, **27 assertions**, in CI. `npc/schedule.py` makes hospitality the
**largest single workplace on the station** — 734 of 3,000 sampled residents, ahead of the
concourse (556) and the Zocalo (488) — and it had no geometry. Every one of those NPCs was
clocking on to nowhere.

It is deliberately **not** the Zocalo, and that is asserted: under half a concourse's ceiling
height, under 120 m² of floor. A low, dark, tight room lit **entirely by pendant cones over the
tables**, so it reads as a field of separate pools with near-zero ambient. Social life built out
of concourse alone would have been one note.

**The lighting design is asserted, not described:** one pendant per table one-to-one, a source
inside every shade, hung **below standing eye height** so it pools instead of lighting the room,
and clear of a seated diner's head. A pendant 200 mm higher stops being this room.

**The dartboard is a real dartboard.** `DART_SEQUENCE` is the regulation clockwise order, and the
test checks the sequence, that 1–20 each appear once, and that the **mean adjacent difference
exceeds 5** — the defining property of the real layout is that high numbers neighbour low ones, so
a naive 1..20 ring would score ~1. A plausible-looking ring is wrong in a way a player can catch.

**A real-world trademark is excluded by assertion.** The frame's lit **ZIMA** panel is genuine
1990s product placement, recorded as observed and reproduced nowhere. The self-test **reads its
own source** and asserts the string appears at most once, in the note explaining the exclusion.
*"I remembered not to" is not a guarantee, and the next session will not have seen the frame.*

**One defect, and a better way of checking for it.** Deck and soffit spanned only the inner wall
face while the walls sit outboard, leaving an open corner at every wall/soffit junction — a few
magenta pixels where the ceiling met the far wall. Fixed, and closure verified by **counting
magenta pixels in the render (0)** rather than by eye. A hole a few pixels across is exactly what
an eye skips; this check scales and should be used on every interior from here.

Logged as **INV-033**.

## Session 3k (cont.) — THE MASTER PLAN CHANGED. Read this before anything else.

**Owner decision, session 3k:** *"I'd rather do something in layers but complete, rather than
small slices which do not add up together."*

`CLAUDE.md`'s six overlapping phases are **superseded**. They sounded like an order and were not
one: with phases running in parallel, every session picked whatever seemed plausible, nothing was
ever completed, and progress became a feeling. That is precisely what happened between 3h and 3k —
**fifteen modules of geometry, twelve of which did not know where they were on the station.**

**The plan is now one layer at a time, across all 126 locations, finished before the next begins.**

`station/directory.py` computes and prints completion per layer in CI, so "how far are we" is a
number this repository calculates rather than a summary anyone writes:

```
    1 addressed    [####                ]  29/126  <- CURRENT
    2 geometry     [###                 ]  19/126
    3 materials    [                    ]   0/126
    4 lighting     [                    ]   0/126
    5 props        [                    ]   0/126
    6 inhabitants  [                    ]   0/126
    7 audio        [                    ]   0/126
    8 judged       [                    ]   0/126
```

**LAYER 0 IS BLOCKING AND IS NOT DONE.** The Godot 4.4 double-precision binary exists at
`/home/user/godot-build/godot-4.4-stable/bin/` and **runs** (verified session 3k), and
`godot/` holds the project. But **all 27 renders in session 3k came from
`tools/preview_render.py`** — the flat-shaded rasteriser, which by CLAUDE.md's own rule judges
structure and says nothing about craft. **No frame in this project has ever been scored against
`docs/AAA-STANDARD.md`.** Finish layer 0 before layers 3–8 or the craft layers cannot be completed
*or* checked.

**Order of work from here:**

1. **Layer 0** — wire `materials.py` → Godot → lavapipe → PNG, and score one frame against the
   rubric. Infrastructure; blocking.
2. **Layer 1** — address the remaining **97** locations in `directory.py`.
3. **Layer 2** — geometry for all 126.
4. Then 3 → 8 in order.

**Rules that now bind** (in `CLAUDE.md`): do not start a layer before the one above is complete;
within a layer, order by the gazetteer's ranked list then by authority, authority-1 first; a layer
is complete when `directory.py` says so; and **nothing is "done" at a layer it has not reached** —
a room with geometry and no materials is at layer 2, and calling it finished is false.

## Session 3k (cont.) — M0 IS DONE. The engine path is alive and the first frame is scored.

**The owner set the opening**, and it is now a design decision in `docs/MASTER-PLAN.md` §4.10:
arrive on a transport, watch the station come into view, dock, be processed through customs, pick
(or be dealt) a species/name/occupation, and live as **1 of 250,000**. That makes the first five
minutes the tutorial using only authority-1 signage the project already holds, and it makes
character creation diegetic — the identicard *is* the character sheet.

**The engine path was not missing. It had rotted from disuse.** `tools/render_godot.sh` was built
in session 2j and never run again; every render from 2j to 3k came from the flat-shaded
rasteriser. Reviving it took one command.

| frame | distance | time |
|---|---|---|
| `docs/engine-approach-far.png` | 14 km | 34 s |
| `docs/engine-approach-near.png` | 3.4 km | 27 s |

200,754 triangles, Godot 4.4 double + Mesa lavapipe, Forward+, 1280×720.

**First craft score in the project's history** — `docs/aaa-scorecard.json`, subsystem
`exterior_approach`: **craft 3, fidelity 4, performance 3, robustness 4.**

### The one blocking finding, and it is the right one to have found first

> **NO EMISSIVE WINDOWS ANYWHERE.** A station housing 250,000 people renders completely unlit from
> within. It reads as a derelict, not a city. The owner's opening beat is the station coming into
> view — and what comes into view has nobody home.

Three majors behind it: the hull is one pale beige note with no material variation or sector
identity; a single hard key with no fill or bounce flattens an 8 km object into a cutout; and
**scale does not read** — nothing in frame gives size, so 8,047 m photographs like a 2 m model.

What is genuinely good: the silhouette is unmistakable at both ranges, and the plating, greebling
and conduit runs read at 3.4 km then resolve away cleanly at 14 km — the LOD and greeble-relief
work from 2n and 3k is paying off.

**Next: the emissive pass.** Window lights are the difference between a model and a city, and they
are the first thing the owner's opening shot shows.

## Session 3k (cont.) — LAYER 1 IS COMPLETE

**All 126 gazetteer rows are resolved: 118 addressed, 8 formally deferred with a reason.** No
third state, and `directory.py` asserts it — the check parses `LOCATIONS.md` and fails if any row
is neither in `PLACES` nor in `NOT_A_PLACE`.

```
    1 addressed    [##################  ] 118/126   COMPLETE (+8 deferred)
    2 geometry     [#######             ]  50/126   <- CURRENT
    3-8                                     0/126
```

**740 assertions in `directory.py`**, up from 222. Every place carries an address, a footprint,
declared functions, declared interactions, adjacency, and containment where it nests.

**The 8 deferred rows are not places**, and each says why: `"Customs Sector"` is an area label
used *alongside* the six colour sectors rather than a room; the jump gate is off-station; the
Zocalo wordmark and the "5" roundel are props and motifs; Babcom terminals and public monitors are
prop *types* already declared in 20 places' `interacts`, so registering them as locations would
double-count; alien signage spans every place; and ISN is a broadcast — world system W8, not a room.

### Five defects the assertions caught during the batch

1. **Four collisions that were really containment** — mooring clamps in the docking bays, shops in
   the Zocalo, the garden terrace in the townscape. Then a fifth pair after the fix: **Earhart's
   and the Fresh Air were nested in the Garden when they are really in the *townscape***. Siblings
   inside one container still collide, so nesting has to be the *true* nesting rather than the
   nearest convenient one.
2. **My own false claim.** I had asserted that *every* informal-residence place sits above the
   habitable ceiling. `subfloor_stack` failed it at 1.103 g — **correctly**, because
   `LOCATIONS.md` puts Downbelow in "Grey **or** the drum sub-floor" and the sub-floor is below
   the ceiling. Replaced with what the sources actually support: the *worst* of it is above the
   ceiling and heavier than any formal residence.
3. **Three places with no interactions** — the proximity arrays, nav beacon and comms grid. Those
   are hull systems a player cannot enter, so the check now exempts a named set of unenterable
   *functions* rather than a hardcoded list of keys.
4. **Fuzzy matching is the wrong tool for aliases.** Seven long rows failed to resolve; the
   unnamed bar's 60-character parenthetical drags its similarity ratio to 0.64. Lowering the
   threshold would have started matching unrelated rows to each other, so aliases match by
   **prefix**, which is exact.
5. **`Customs (×2…)` uses U+00D7**, not the letter x. A prefix match is exact about codepoints,
   which is how that surfaced at all.

**Next: layer 2 — geometry for the 76 addressed locations that do not have it.**

## IN FLIGHT — read this before starting anything

**An adversarial review panel is running over the five new NPC modules and had NOT reported when
this was written.** Nobody independent has reviewed 13,300 lines of agent-written code.

- Workflow run ID **`wf_e7c370a1-f14`**, task `wreyj01ho`.
- Script: `~/.claude/projects/.../workflows/scripts/npc-layer-review-wf_e7c370a1-f14.js`
- Journal: `~/.claude/projects/.../subagents/workflows/wf_e7c370a1-f14/journal.jsonl` — **read
  this first**; it carries one `{"type":"result"}` line per completed agent with its full return
  value, and it survives a context reset when the notification does not.
- Shape: five harsh reviewers, one per module with a lens matched to it (body → mesh closure and
  LOD; costume → canon and era lock; crowd → population conservation and the `use` deck tag;
  animation → kinematics in a rotating frame; navigation → topology and reachability), each
  non-minor finding then handed to a skeptic **told to refute it**.
- **Treat the NPC modules as sound-but-unreviewed until that report is read**, exactly as session
  2x's modules were treated.

If the container is gone, the modules are committed and pushed and nothing is lost but the
review; re-run it from the script path above, or re-launch the same panel.

### Session 3j (cont.) — drum_ground had one assertion doing all the damage

The sweep said 33 of `drum_ground`'s 40 constants were unguarded. The cause was a single
assertion:

```python
check("FNV-1a is stable across processes",
      _fnv1a("drum", 7, "ground") == _fnv1a("drum", 7, "ground") and ...)
```

**The first clause is `x == x`, computed in one process.** It says nothing about stability across
processes — the property it is named for, and the property the entire determinism argument rests
on. Perturbing `_FNV_OFFSET` or `_FNV_PRIME` changed every height in the drum and none of 74
assertions noticed, because *"run it twice and compare" is satisfied by any pair of constants*.

Replaced by three checks that each test what the others cannot: the constants are the **published**
FNV-1a 64-bit values (an external fact, so a typo is caught against the standard rather than
against ourselves); the delimiter test, which was the only real clause in the original; and **an
actual cross-process run under two PYTHONHASHSEEDs**, which cannot be satisfied inside one
interpreter.

Plus a **golden digest** over a 16×16 sample of the heightfield — one assertion pinning every
terrain constant at once. Guarding ~20 constants by hand would be twenty assertions restating
twenty constants, which is how the module got here. It is *meant* to be brittle: a terrain change
should fail it, be looked at, and have `GROUND_DIGEST` updated deliberately. Same argument as the
committed `cell_manifest.json` diff gate — a silent terrain change is the failure mode.

**74 → 77 assertions**, verified load-bearing (`_FNV_PRIME` now fails two).

**And the sweep produced a false positive on its own first run, now documented in the tool.**
`FLOOR_R`, `Z0` and `Z1` came back UNGUARDED because `configure()` overwrites them from the
schema before anything reads them — the mutation is neutralised, not caught. Those three are
correctness-by-construction and "fixing" them would have undone that. **Before acting on an
UNGUARDED verdict, check whether anything assigns the name at runtime.**

### Also outstanding from this session

- **The NPC sweep IS RUNNING**, detached, writing to `docs/audits/mutation-sweep-npc.log` —
  100 constants across the five modules. The committed copy of that log may be **partial**; check
  whether the process is still alive (`pgrep -f mutation_sweep`) and re-commit the finished file.
  Read its UNGUARDED list against the false-positive note above before acting on any of it.
- The full session-3i sweep report is preserved at **`docs/audits/mutation-sweep-3i.log`**. It was
  only in `/tmp` and would have been lost.

## Session 3k — the Alien Sector, and the ranked build list is finished

`station/alien_sector.py`, **22 assertions**, in CI. **This closes the gazetteer's ranked
build list of eight.**

| # | location | status |
|---|---|---|
| 1 | Zocalo | built |
| 2 | Customs hall / arrival concourse | built, session 3j |
| 3 | Docking bay | built |
| 4 | C&C | built |
| 5 | Garden townscape | built, session 3j |
| 6 | Council Chamber | built |
| 7 | Downbelow's architecture | built as `plant.py`, session 3j |
| 8 | **Alien Sector** | **built, this session** |

**The mechanic is canon, not invented.** The customs board is authority 1 — *"SIX DIFFERENT
ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5"* — and six simultaneous atmospheres is a life-support
architecture: six independently conditioned volumes **with locks between them**. This module is
those locks. Atmosphere classes are read from `npc/schedule.py`, which deliberately carries **no
numbers** for five of the six, and an assertion checks that no class here carries a digit.

**The lock depth is derived:** a lock must hold one occupant clear of both leaves at once, and
that occupant wears an encounter suit, so depth = suit + clearance fore and aft + two reveals =
**2.75 m**. Asserted: *every quarter has two doors, because one door is not a lock.*

### Three defects, each caught by a different gate

1. **The barred screen was invisible** — placed inside the inner portal's own 0.55 m reveal, so
   the jambs occluded it entirely and the render showed an empty aperture where the frame's
   headline feature belongs. *A screen inside a jamb is not a screen.*
2. **The containment assertion then failed by 20 mm**, because its limit was a padded magic
   `0.25`. The assertion worked; the magic number meant it could not say *why*. Now derived from
   what is actually placed outboard.
3. **The bars opened onto void.** With the screen visible, the render showed magenta *through*
   it — the quarter interiors are a separate increment, so there was genuinely nothing behind the
   grille. **Real void behind a grille is indistinguishable from a defect** to the next session
   that renders it, so a closed `alien_quarter_shell` now backs every screen, asserted one per
   screen.

Renders: `docs/render-alien-sector.png`, `docs/render-alien-lock.png`. Logged as **INV-031**.

## Next session — start here

The drum's **structure** is complete: shell, both end caps, three guideway trusses with the
habitat's lighting, three spokes, a correct hollow ring model, and its own performance gate.
What follows is in rough priority order.

0. **Read the in-flight review panel's report** — see the IN FLIGHT section above. It is the only
   thing standing between 13,300 lines of agent-written NPC code and the project's own rule that
   nothing is done until it clears a harsh panel. Then **sweep the NPC modules**, which has not
   been done.

0b. **The unwelded NPC joints.** Limb roots are inside the torso (asserted, passing) but the lofts
   interpenetrate rather than blend, so a hard crease sits where a deltoid should be and the
   shoulders read as a shelf. Craft, not closure — no gate can see it and only looking caught it.
   `docs/render-npc-detail.png`.

0c. ~~**The plant kit.**~~ — **built, session 3j.** `station/plant.py`. What remains is the
   PHASE C pass on it: lighting, material and dressing. Old note kept for the numbers:
   **The plant kit.** `LIFE-SUPPORT-AND-INDUSTRY.md` §8: 62.3 M triangles — **26% of the whole
   station interior** — is currently budgeted for Grey's 34 plant decks as walkable corridor, and
   the plant zone is 559 m³ per resident, ~100× what life support needs. It is structure, tankage
   and void with a thin walkable skeleton, and that kit does not exist. Largest piece of
   misdirected content in the project.

0d. **The Starfury cockpit** — now unblocked and catalogued. Size the tub from the airframe and a
   standing 1.75 m pilot; log as an invention. See `reference/00-INDEX.md`, session 3j upload.

1. ~~**The drum's ground**~~ — **built and its four review findings all closed**
   (`drum_ground.py`, 74/74). Sessions 3e and 3f.
2. ~~**The tram**~~ — **built** (`tram.py`, 44/44). Two things remain: its "measured proportion"
   assertions are algebraic identities that never touch the built mesh, and the car length is
   disputed between two authority-1 frames — see **C-008**.
3. ~~**Streaming cells**~~ — **done, session 2w.** `ring_cells()` / `deck_cell()` emit them and
   the seam is asserted vertex-for-vertex, wrap-around included. What is *not* done: a cell
   **manifest** the engine can stream from, and cell-to-cell **junction** placement (a cell is
   currently pure corridor with no doors off it).
4. **Remaining crude components.** Cobra bays, docking ports, observation domes and rotundas
   are still box primitives. Radiators (2o), cargo modules and the forward comms plate (2t)
   are reference-corrected.
5. **Deck tile phase across junctions** — the grid is not driven from a shared origin, so there
   is a visible seam at each crossing mouth.
6. ~~**`HULL_ALLOWANCE` should become metric.**~~ — **done, session 3i.** See below; the
   prediction attached to it was wrong and the correction is the interesting part.
7. **Publish the Godot binary** as a Release asset — container-local, 61 minutes to rebuild.
8. **C-003 assignment** and **C-004 numbering.** These block *labelling*, not building — see the
   note below.

**On what C-003 and C-004 actually block.** They decide which *name* attaches to a volume, not
what shape it is. Geometry is generated against `(sector, ring_index)` and labelled afterwards
by `bind_labels()`; when the conflicts close, the mapping changes and the geometry does not.
The "Blocked" table below is kept for the record but its first two rows are **no longer true of
geometry** — only of the names on it.

## Blocked

| Item | Blocked by | Needs |
|---|---|---|
| ~~All interior level geometry~~ → **interior level *numbering*** | C-004 — **numbering convention** unresolved. The axis is settled: levels are concentric radial decks | A lift-car display, a numbered deck plan, or dialogue tying a level number to a gravity. Nothing else will do — the deck plans themselves have now been found and they number nothing |
| ~~Interior sector layout~~ → **sector *naming*** | C-003 — **Green/Brown transposition**. Sectors are longitudinal bands; the two authority-3 sheets disagree on which band is the habitat drum. `drum_sector()` identifies the drum by **geometry**, so building proceeds; only the label waits | Any source placing the Garden or Downbelow in a *named* sector at a longitudinal position |
| Deck spacing, ring radii, corridor width, ceiling height | Unavailable from any held source | The one sheet that draws decks has its vertical scale exaggerated ~2× (C-004 UPDATE item 3, same ruling as C-005) |
| Grey / Brown / Yellow interiors | Near-zero reference coverage | Grey has one frame; Brown has one misfiled frame; Yellow has none |
| ~~Starfury cockpit~~ | ~~Zero reference coverage~~ | **UNBLOCKED and catalogued, session 3j.** Four references in `reference/12-starfury/`, all four opened and written up in `reference/00-INDEX.md`. **The pilot stands** — braced against a near-vertical ribbed couch with a chest yoke, not seated. Tub is an elongated hexagon widest 35–40% down, green throughout, two angled console banks. **No absolute dimension is available**: the two authority-2 photos contain no human and no scale bar, and the two files that do contain a figure are authority 4 fan models at toy scale. Size the tub from the airframe and a standing 1.75 m pilot, and log it as an invention |

## Reference gaps worth filling

Ranked by how much they unblock. Nothing here stops progress on the hull, but all of it
becomes blocking once interiors start:

1. **A lift-car display, or any numbered deck plan** — the single highest-value gap in the set.
   It is the only thing that closes C-004. *Deck plans as such are no longer the gap: session 2q
   found six radial cross-sections. They name facilities and number nothing.*
2. **An uncropped scan of the Security Manual sectional schematic** — would supply the cut-off
   detail row. Note it is **not** likely to supply the missing sixth-band label, which is absent
   from an intact label row; this lead is weaker than it first looked.
3. **Brown Sector / Downbelow** — one misfiled frame
   (`01-station-exterior/sleeping-in-light-05.jpg`, S5, station derelict).
4. **Yellow Sector** — zero files.
5. ~~**Starfury cockpit interior**~~ — **closed, session 3j.** Four files uploaded by the owner; see the Blocked table. Uncatalogued.
6. **Grey Sector** — one file, and it is the most useful interior frame in the set.

## Uncatalogued reference, and misfiled reference

`reference/00-INDEX.md` ends with two lists a future session should read before re-deriving
them: **Still uncatalogued** (~25 files, mostly single-character portraits and race-makeup
shots) and **Misfiled — recommended moves** (nine files whose folder is wrong, deliberately
*not* moved because the schema and specs cite some by path).

## Session 3k (cont.) — LAYER 2 IS COMPLETE. Every place on the station has geometry.

```
  LAYER COMPLETION across 118 places (126 gazetteer rows less 8 that are not locations)
    1 addressed    [####################] 118/118  COMPLETE
    2 geometry     [####################] 118/118  COMPLETE
    3 materials    [                    ]   0/118  <- CURRENT
```

`station/rooms.py` — **567 assertions**, 68 locations, 11 archetypes, 12,516 triangles — generates
every addressed location that has no bespoke module, from the specification `directory.py` already
held. The hero and featured rooms keep their own modules; this is the ~84-location procedural tier
`docs/MASTER-PLAN.md` §3.4 called for, and it is the reason the arithmetic closes.

### The defect the first verification render found, and it is the transferable one

**`interacts` is what a PLAYER CAN USE. It is not an inventory of what is in the room.** Built from
it alone, *"Fabrication furnaces"* came out a grey box containing two control podiums, a catwalk
and a crane — **the controls for a furnace, and no furnace.** *"Primary fusion core"* declared two
interactables and no reactor. A furnace is correctly absent from `interacts`, because you do not
walk up to one and operate it; it is just as correctly required in the geometry.

No material and no light makes an absent object present, so it is a **layer 2** defect. `FIXTURES`
adds per-archetype scenery — furnace stacks, plant columns, racking runs, equipment gantries, a
sanctuary dais, market stall frames, overhead service runs — plus structural wall ribs at a pitch
derived from room height, because a flat run of wall to a 7.5 m soffit is the strongest tell that a
volume is a placeholder. INV-035.

**Expect the same shape of gap in every later layer.** The declared list is never the whole room.

### Three gates that caught things on their first run

1. **No two solids in a room may occupy the same cubic metre.** Caught a 3.2 m monitor wall
   swallowing a cell door, and a medcabinet inside a babcom terminal — *both present in the version
   this module was about to be committed at*. Root cause: the wall-prop lattice stepped `(i * 2.1)
   % (ln - 2.4)` regardless of how wide each prop was, and wrapped back over itself. It is a cursor
   now, and moves to the end walls when a wall fills — which also means doors land on end walls,
   where you would actually enter.
2. **A 0.9 m walker must cross the floor end to end.** A flood fill on a 0.15 m grid. The first
   version measured a single clear x-span and read a furnace stack you walk *around* as impassable,
   reporting 0.00 m clear in a 10 m hall.
3. **Every declared prop must exist as geometry, and no geometry may exist that nothing declares.**
   Both directions. This is the check that stops the module being a box generator with a good
   docstring.

Each is asserted to be **able to fail** — a disjoint pair, touching faces, an open bay, a bay walled
across, an island to route around, a gap narrower than the walker, something hanging overhead.
Three assertions in this project have been vacuous, one of them named *"FNV-1a is stable across
processes"* and comparing a value to itself.

### Two structural lessons

**`lateral_stack()` exists because two halves of the same module disagreed.** `bay_span_m()` derived
the bay width from one formula and `build()` laid objects out with another; a fusion core was sized
for a 1.25 m aisle and built with 0.99 m. There is now one description of the cross-section and both
callers use it. *Any time a size is computed in one place and consumed in another, expect this.*

**`directory.py`'s layer-2 predicate is a membership test**, not `module or GENERATOR`. The lazy
form returns True for every row in the table — a completion counter that cannot go down, which is
the same class of defect as an assertion that cannot fail. It asks `rooms.unbuilt()` what it
actually emits, and the self-test hands it a synthetic place to prove it still says no.

**The layer denominator changed from 126 to 118, and that needed care.** 8 gazetteer rows are not
locations — a prop type declared in 20 rooms, a broadcast, an area label, the off-station jump gate.
Left in the denominator they hold every layer at 118/126 forever and CLAUDE.md rule 3 ("a layer is
complete when `directory.py` says so") can never fire. Both numbers are now printed, and the
existing assertion that every row is addressed *or* deferred with a reason is what stops the
deferral list being grown to make a number go green.

### Camera bugs, three in a row, all from picking a standpoint by arithmetic

A hand-typed `--eye` from a previous, larger version of the bay put the camera outside the end wall
(flat grey frame that looked like a lighting bug). A third of the way in put it past the first rank
of props, so the shot meant to prove the room is furnished showed the half that is empty. A fixed
1.1 m off-centre put it inside a 2.4 m furnace stack. `standpoint()` now searches the same walkable
grid the gate uses, so the camera stands where a player could stand and cannot go stale.

Five rooms rendered against magenta — fabrication, cargo bays, sanctuary, N'Grath's lair, medlab.
**Zero magenta pixels: all closed, all correctly wound.** `docs/render-rooms.png` is the fabrication
bay. Those are preview-rasteriser frames and say nothing about craft, per this file's own rule.

## NEXT SESSION — layer 3, materials

Layer 2 is complete, so layer 3 is legitimately open. Order:

1. **The emissive pass.** The standing blocking finding against `exterior_approach`: *no emissive
   windows anywhere* — 250,000 people and the station renders unlit from within, reading as a
   derelict. It is the first thing the owner's opening beat shows. Fix it, re-render through
   `tools/render_godot.sh`, re-score.
2. **The magenta guideway light runs** in `drum_interior_engine` — the other standing blocking
   finding, and also a materials defect.
3. **Then materials across the 118**, hero and featured first by authority, procedural rooms from
   `rooms.py` archetype by archetype — the archetype is already the right granularity for a
   material set.

Craft claims cite an **engine** frame. `tools/render_godot.sh`, not `tools/preview_render.py`.

## Session 3k (cont.) — LAYER 3 BEGINS: the station is lit from within

`docs/engine-windows-nightside.png` — Godot 4.4 double + lavapipe, 3.4 km, anti-sun side — shows
warm window bands running the length of both habitat sections with a scatter of marker lights.
**The station reads as inhabited.** The sunlit frame (`docs/engine-windows-near.png`) correctly
shows the same bands as texture rather than as light, which is what a lit hull does.

That answers the standing blocking finding: *"NO EMISSIVE WINDOWS ANYWHERE. A station housing
250,000 people renders completely unlit from within. It reads as a derelict, not a city."*
Scorecard `exterior_approach` round 2: **craft 3 → 4**, recorded as a *builder* round, not an
independent review.

### The failure that mattered more than the feature

**The material exported cleanly, passed 594 assertions, and did not reach the render.**

Material rules were emitted to `material_rules.gen.txt` for a human to paste into
`godot/scenes/*.tscn` — the stated reasoning being that a generator rewriting another agent's file
is how two sources of truth start. That reasoning is *backwards*: the `.txt` and the `.tscn` **were**
the two sources, and nobody is doing the paste. Godot printed `fallback material used by 21
group(s)` and nothing was reading it. `greeble_fitting` and `hazard_chevron` had been missing from
the exterior scene for longer than this session.

- `patch_scene_rules()` writes the `material_rules` block and the `ext_resource` lines it needs, and
  fixes `load_steps`. The lights, environment and tonemapper are judgements and stay owned by
  whoever wrote them.
- A gate asserts the file on disk matches what the library would write. **Proven able to fail** by
  deleting one rule and watching it fire.
- **`materials.py` was not in CI at all.** It is now.

*Any generator whose output needs a manual step to take effect has no effect. Look for others.*

### Two bakes, and the first one was the wrong building

Version one glazed **every** deck of both habitat sections. The engine frame came back as
rust-coloured static: the drum is 500 m across, so a 2.4 m pitch puts ~650 apertures round the
circumference and they alias into noise long before they resolve into windows. Worse, the white
speckle was the window **frames** — metallic 0.55 standing 0.25 proud, so every aperture threw a
sunlit specular highlight.

Neither was a tuning problem. A window surround is a shadowed recess, not a bright ridge; the
reference hull is mostly plate with window strips in it. The sheet is now eight decks tall with two
glazed, and the frame is a dark rebate. INV-036 records both bakes, because the first is the more
useful record.

Row pitch is `interior.DECK_PITCH_M`, **imported, not restated** — hard rule 4. The repeat is square
*by derivation*, because `.tres` writes one scalar `uv1_scale` and a non-square sheet would be
silently stretched with nothing to catch it.

### Also fixed: a pre-existing failing gate that was mostly false positives

*"Every group literal found in the generators resolves"* listed 8 names. Six were `directory.py`
place keys and `rooms.py` prop types the regex began matching when those files landed; one was an
`lod.py` manifest statistic; **exactly one — `ground_verge` — was a real surface with no material.**
A *specification* names places and props; a *generator* names surfaces. Only the second kind needs a
material, and the scanner now skips the first kind.

## NEXT SESSION — layer 3 continues

Layer 3 is 0/118 by the register's count: the exterior is not one of the 118 places. What is done is
the exterior's blocking finding. Order:

1. **The two standing majors on `exterior_approach`, both craft:**
   - *Triplanar cross-projection.* World triplanar samples the sheet on two axes across the drum's
     barrel and the second projection shows as a crosshatch over the window rows. Needs cylindrical
     UVs on the drum mesh or a shader projecting about the spin axis — **not a material change**,
     which is why it was not fixed with the material.
   - *The band pattern tiles visibly.* One 28.8 m repeat over a 1,209 m drum is 42 identical
     courses. Wants a long-period variation: blocks of dark hull where a section has no quarters.
2. **The magenta guideway light runs** in `drum_interior_engine` — the other standing blocking
   finding, and also a materials defect.
3. **Then materials across the 118 places.** The archetype in `rooms.py` is already the right
   granularity for a material set — 11 archetypes, not 68 rooms. Hero and featured rooms first, by
   authority.

One minor worth folding into (1): the habitat sections now sit darker than the rest of the hull, so
they read as a different material rather than the same hull with windows in it. The plate value
between windows should match `hull_exterior`'s 0.60.

Craft claims cite an **engine** frame — `tools/render_godot.sh`, not `tools/preview_render.py`.

## Session 3k (cont.) — the window mapping is cylindrical, and two tools were lying

Round 2's two majors and one minor against `exterior_approach` are all reworked and verified in
engine frames. `docs/engine-windows-nightside.png` (3.4 km, anti-sun, `--light-gain 0.04`) shows
the station as a dark silhouette lit from within: window bands running **around** the barrel, with
visible unlit blocks along its length.

**The crosshatch was triplanar, and triplanar is not optional here.** `export_gltf.py` writes
POSITION and NORMAL and nothing else, so **no mesh in this project has UVs** and every material
relies on world triplanar. That is right for plating and greebles and wrong for any pattern with an
orientation, because it blends two grids across the drum's barrel.
`godot/materials/hull_window.gdshader` projects about the spin axis. Two details in it are
load-bearing and neither is obvious:

- the seam closes because the repeat count around the circumference is snapped to a whole number
  **at a reference radius**. Snapping per-fragment radius would close it everywhere and put a ring
  wherever the whole number steps — the tapered aft block would show a stack of bands;
- mip selection uses derivatives from the **smooth tangent frame**, not from the uv. `dFdx` of a
  seam-discontinuous uv is the width of the station and picks the coarsest mip, drawing the seam as
  a blurred stripe — the artefact the mapping exists to remove, reintroduced by how it is sampled.

**The darkness minor was found by arithmetic, not by eye.** Material albedo 0.18 against a sheet
plate value of 0.60 rendered the hull *between* windows at 0.15 against `hull_exterior`'s 0.60 —
four times darker. Now asserted from the values that ship.

### Two tools that reported success while doing nothing

1. **`--light-gain` was a no-op on the exterior.** It scaled only the lights carried in the shot
   JSON, and the exterior shot has `"lights": 0` because its key, fill and rim are nodes in
   `exterior.tscn`. Two renders an order of magnitude apart in gain came back **byte-identical**.
   Without it there is no way to turn the rig down and therefore no way to see whether an emissive
   material emits.
2. **A shader that fails to compile still renders.** Godot logs `SHADER ERROR`, falls back, and
   hands out a valid PNG of the wrong thing at **exit 0**. A redefinition of the built-in `TAU`
   cost one round exactly that way. `render_godot.sh` now exits 3 on it.

*Both belong to the same family as the paste step earlier this session: a step that appears to work
and does not. When a change does not show up in the output, suspect the pipe before the change.*

### The .tres gates had been testing a file that is never written

`ShaderMaterial` export is a separate writer, not a branch in `tres()` — the two resources share
almost nothing. Adding it meant the self-test loop's `text = tres(m)` was checking a
StandardMaterial3D that no longer ships for `habitat_windows`; nine assertions would have gone on
passing about it. The loop tests `exported_tres` now.

Its own gate is the shader analogue of `STANDARD_MATERIAL_KEYS`: Godot silently **drops** an
unrecognised `shader_parameter` and runs the shader at its declared default, so every parameter is
checked against the uniforms the `.gdshader` actually declares, and a uniform nobody sets has to be
on an explicit list.

## NEXT SESSION

**New blocking finding, and it is layer 4 rather than layer 3:**

> **The lighting rig has no night side.** The rim kicker sits at `sun_az + 175` and the fill is
> mirrored through the camera axis, so whatever azimuth the camera takes, the camera-facing edge is
> lit. That is a correct rig for showing a model's silhouette and the wrong one for a city at
> night — the anti-sun frame needed `--light-gain 0.04` to show the windows at all. **The owner's
> opening beat is the station coming into view, so that shot cannot be composed until the rig
> changes.**

Order:

1. **The rig.** A shot flag that composes the arrival: key behind the station, rim reduced to a
   true edge, fill off. It is a lighting judgement, so it belongs to layer 4 — but the opening beat
   depends on it and nothing else does, so it is worth doing before the other 117 places are lit.
2. **The magenta guideway light runs** in `drum_interior_engine` — the remaining standing blocking
   finding, and a materials defect.
3. **Materials across the 118 places.** `rooms.py`'s 11 archetypes are the right granularity for a
   material set, not 68 rooms. Hero and featured first, by authority.

Layer 3 still reads **0/118** in the register, and that is correct: the exterior is not one of the
118 places. What is finished is the exterior's blocking finding and the two majors behind it.

Craft claims cite an **engine** frame — `tools/render_godot.sh`, not `tools/preview_render.py`.

## Session 3k (cont.) — LAYER 3 AT 68/118. The procedural interior is materialled.

```
    1 addressed    [####################] 118/118  COMPLETE
    2 geometry     [####################] 118/118  COMPLETE
    3 materials    [###########         ]  68/118  <- CURRENT
```

**41 materials across four families**, covering all 124 groups `rooms.py` emits for the 68
procedural locations. `materials.py` 920 assertions; `test_materials_layer3.py` 30/30 with coverage
at 124/124.

The layer-3 predicate is **computed, not flagged**. It asks the material library whether it covers
each place's actual emitted geometry, so the number falls the moment a room grows a surface nobody
has painted. The fifteen bespoke modules cannot be answered without running them, so they report as
NOT at layer 3 rather than being assumed to be — an unknown is not a pass.

### How this was built, and what it changes about using agents here

Four agents, one per surface family, proposing structured specs. **No reviewer agents**, and the
reason matters: this machine runs **two agents at a time** (`min(16, cores-2)` on four cores), so
the first design — seven proposers each shadowed by a skeptic — was a queue seven deep, ~105
minutes. More importantly, most of the reviewer's checklist is *computable*, and a reviewer is the
wrong instrument for a computable question.

So the checklist was split. `station/test_materials_layer3.py` holds everything mechanical:
coverage, fragment ambiguity, the measured neutral band, physical ranges, deck-against-wall, and
whether a cited file exists. It runs on every push instead of once.

**Writing that gate against the reviewed library first is what made it right.** Three of its rules
were wrong and 60 already-reviewed materials proved it:
- a bimodal-metallic rule failed **nineteen** of them including `hull_exterior` at 0.34, a measured
  value — this project authors metallic as a blend for painted metal, deliberately;
- the saturation rule swept in radiators, cargo modules and hazard chevrons, all meant to be
  saturated;
- a source-*length* rule failed `core_band`, whose source is `"34b"` — a real authority-1 frame ID.

And the fragment check as first written **could not fire**: `frag in g and len(frag) > len(g)`,
which no pair of strings satisfies. *A gate that fails the reviewed corpus is wrong about the
corpus.* Run new rules against known-good data before trusting them against new data.

`apply_proposals.py` renders the committed JSON into source rather than anyone retyping it: 41
materials × 11 fields is 450 chances to transpose a digit, and a wrong roughness passes every gate
here — in range, plausible, and not what was measured.

### Findings from the proposals that are CANON work, not material work

Not yet folded into `materials.py`'s PROVENANCE / NEGATIVE_RESULTS. **Do this next; it is the most
valuable thing in the proposals.**

1. **`ALBEDO_ANCHOR` is independently corroborated.** Lit structural walls across **six frames the
   anchor was not derived from** give 0.365 / 0.390 / 0.418 / 0.421 / 0.446 / 0.494 / 0.511 — mean
   0.435 against the anchor's 0.46. The one number setting the station's absolute level survives
   evidence it did not come from.
2. **The heavy structural steel is PAINTED warm, not lit warm.** In `dock.webp`, R/G holds
   1.69–2.12 across a 2.5× value range while R−B does not: a multiplicative signature, i.e. pigment
   — and the *opposite* of the hull's additive blue. Corroborated in `central corridor.webp`.
3. **`Doug's Dugout.webp` must never be measured for albedo.** Grey-world gains 0.723/1.279/1.196
   and the balanced result is nonsense (a wall at S 1.000): the room is lit entirely by isolated
   pendant cones with near-zero ambient, so its mid-tone population is not neutral and the method
   has nothing to work with.
4. **Five new `GREY_WORLD_GAINS`**: dock.webp 0.968/1.027/1.007; central corridor.webp
   1.044/1.085/0.892; more zocalo.png 0.936/1.137/0.950; more hallway.jpg 1.118/1.196/0.788; more
   hallways.jpg 0.794/1.145/1.154. The method was validated by reproducing two existing gains
   exactly.
5. **Two new NEGATIVE_RESULTS instances.** In `more hallways.jpg` the *same* deck plate balances
   H 36–37 under warm panels and H 179–200 under cool tubes — one surface, two lights, two colours.

Also declared openly by a proposer rather than hidden: `shell_rib_oxide` sits at S 0.301, above the
neutrality line, with a fallback at S 0.200 that preserves the finding — *"do not fall back to
neutral grey, which two authority-1 frames contradict."*

## Session 3l — the five findings are folded in, and the gains table now checks itself

Item 1 of the previous list, done. All five went into `materials.py`, and **every number was
reproduced from the frames before being written down** rather than taken on the proposers' word:

- **Three existing gains recomputed exactly** (council chambers, war room, grey level 1 — dmax
  0.0000). That is the method's own control, and it is what makes the five new ones trustworthy.
- **Five new `GREY_WORLD_GAINS`** — all reproduced to ≤0.002 of the claimed values.
- **`ALBEDO_ANCHOR_CORROBORATION`**, a new block. Three of the seven readings were recomputed
  independently and came back at 0.365 / 0.418 / 0.446 — the proposal's figures exactly. Recorded
  with the honest caveat: same balance method throughout, so it rules out a one-frame fluke rather
  than a systematic error.
- **Two new `NEGATIVE_RESULTS` instances** — the same deck plate at H 36–37 under warm panels and
  H 179–200 under cool tubes. Five times now this project has found a colour that belonged to the
  light.
- **`Doug's Dugout.webp` excluded from albedo measurement**, with the numbers: balanced mid-tone
  saturation median 0.370, p90 0.870, a third of pixels above S 0.5 — against the anchor frame's
  0.105 / 0.194 / 0.000 measured identically.

**The gains table now verifies itself.** It was nine numbers nobody re-derived, and every interior
albedo in the library is a ratio against a balance computed with them — so a re-sorted, re-encoded
or replaced frame would move every measurement downstream and no gate would notice. `materials.py`
recomputes all fourteen from the images on every run, and the check is proven able to fire by
perturbing an entry.

923 assertions (was 920). No material value and no geometry changed, so the exported `.tres` are
byte-identical — which is the correct outcome for a provenance increment and was verified rather
than assumed.

One trap worth carrying: the new block first bound `import numpy as _np` inside `_selftest`, and
this module already has a module-level `_np()` helper. Python scopes per function, not per line, so
every later call to it raised `UnboundLocalError`.

## Session 3l (cont.) — the bespoke fan-out. 5 of 6 clusters home; layer 3 is much further along than "50 places" suggested

`materials.py` **1,205 assertions**, up from 924. Applied this session: the Zocalo (24 materials,
39 groups), the drum landscape (17, 33), signage (2, 3), plus the corridor kit tagged.

### Real coverage, measured rather than estimated

| tier | groups | resolved |
|---|---|---|
| procedural, `rooms.py` 68 rooms | 124 | **124** |
| `zocalo` | 39 | **39** |
| `core_tube` + `tram` | 41 | **41 — already were, before the fan-out** |
| `garden` + `drum_ground` | 33 | **33** |
| `signage` | 3 | **3** |
| `command_control`+`council_chamber`+`customs`+`docking_bay` | 55 | 6 — **proposal in hand, not applied** |
| `plant`+`alien_sector`+`hospitality`+`quarters` | ? | **agent hit the session limit; never ran** |

### Findings, in order of how much they cost to miss

1. **80% of every corridor was ONE untagged material.** `tag()` had four call sites, all light
   fittings; every structural surface fell into the default. Six reviewed materials —
   `kit_deck`, `kit_pilaster`, `kit_reveal`, `kit_skirt`, `kit_rail_band` — were bound to
   fragments nothing emitted. Fixed: 13 groups, 0% untagged, **no new material authored**.
   `interior_kit` now asserts zero untagged triangles and ≥12 groups.
2. **`KNOWN_GROUPS` could not see the bespoke modules at all.** Its scan is a regex restricted to
   `drum|endcap|truss|tram|core|ground|greeble|light`, so all 124 rooms.py groups and all 42 from
   command_control/council_chamber/docking_bay/signage were invisible. The gate passed over a
   short list. `test_materials_layer3.py` now RUNS the generators.
3. **THE SAME DEFECT TWICE, one level apart:** `interior_kit` tagged the light strip and not the
   pilaster it sits in; `zocalo` claimed `zoc_rib_cap` and `zoc_rib_lamp` and not the arch they
   sit on. **The fitting gets named, the thing it is mounted on does not.** Look for it again.
4. **Three of my own gates were wrong about the corpus**, and running them against known-good data
   is what showed it: bimodal metallic failed 19 reviewed materials; the draw-call budget counted
   the LIBRARY when a draw call is paid per material DRAWN (worst single view is 9, not 80); and
   the ambiguity gate failed six deliberate general/specific overrides. **Run a new rule against
   known-good data before trusting it against new data.**
5. **`transit` needed nothing.** I sized the bespoke work from a regex upper bound of 499 string
   literals instead of measuring per-module coverage, and spent an agent on a cluster already
   finished. Establish entry points first, then measure, then decide what to propose.

### Entry points, which were the expensive part

Recorded in `docs/layer3-proposals/bespoke/*.json` under `entry_points`. Only 3 of 15 modules have
`write_obj()`. Notably **`zocalo` does NOT** — it has `write_run(path, bays=3, ...)` and
`write_bay(path, ...)`, so `test_materials_layer3._via_write_obj("zocalo")` would fail. Its full
group set needs `zocalo_run(3, cap_ends=True)` (38) plus the `table_pedestal_five` variant (39);
`write_run` defaults `cap_ends=False` and emits only 37.

## NEXT SESSION

1. **APPLIED.** `blue_public` landed: **9 new materials for 55 groups**, because EIGHTEEN of its
   surfaces were ones this library already had. The proposal rebound them — `bay_deck` onto
   `shell_deck_industrial`, `cc_floor` and `customs_deck` onto `shell_deck_public`, `council_top`
   onto `furn_casework` — instead of authoring near-duplicates, which is what keeps a docking
   bay's deck and a fabrication bay's deck the same deck. The `council_medallion_spoke`
   "competition" was my validation ignoring scene filtering: `drum_structure` is a drum-scene
   material and cannot compete inside `interior`. **Bespoke coverage 4/42 → 42/42** for the four
   modules the gate can build; 1,269 assertions.
2. **DONE, without re-running the agent.** `plant`, `alien_sector`, `hospitality` and `quarters`
   were enumerated by hand -- entry points read out of each `_selftest` -- and materialled. **Of
   46 unresolved groups, FORTY were surfaces this library already had**: a cabin floor is the
   kit's deck panel, a bunk and a bar stool are the same soft goods, a grab bar and a plant
   handrail are one extrusion. Only six were new, all in Doug's Dugout or an airlock. Measuring
   first is what turned a whole agent's work into an afternoon's rebinding.
3. **Layer 3's other 50 places** — the bespoke modules. Same shape: enumerate each module's emitted
   groups, propose, gate. `zocalo`, `interior_kit`, `core_tube` and `tram` are the big ones.
2. **The lighting rig has no night side** (layer 4, blocking) — the arrival shot cannot be composed
   until it changes, and the owner's opening beat depends on it.
3. **The magenta guideway light runs** in `drum_interior_engine`.

**On agents here: the concurrency cap is 2.** Size fan-out for two lanes, not sixteen. Prefer a
mechanical gate to a reviewer agent wherever the question is computable, and capture each agent's
result into the repo as it lands — the workflow journal lives in `/root/.claude` and dies with the
container.


## Session 3m — LAYER 3 IS COMPLETE. 118/118.

```
    1 addressed    [####################] 118/118  COMPLETE
    2 geometry     [####################] 118/118  COMPLETE
    3 materials    [####################] 118/118  COMPLETE
    4 lighting     [                    ]   0/118  <- CURRENT
```

No material value changed this session and the exported `.tres` are byte-identical. What changed is
that the **register can now see what was already true**: it counted 68 because its layer-3
predicate only knew how to measure `rooms.py` places, and the 50 bespoke ones were materialled but
uncounted. 68 → 90 → 104 → **118** as each group of modules became buildable.

`test_materials_layer3.py` now builds **all 16 modules**: 256/256 groups. Every entry point came
out of a module's own `_selftest`, and they are recorded in the file so nobody rediscovers them.

### Four shapes of return value, and each one failed differently

There is no uniform builder interface, and normalising eleven generators to satisfy a test would
have been the wrong repair. `_names()` handles all four:

- `(name, lo, hi)` **spans** — `rooms`, `interior_kit`
- a flat **per-triangle name list** — `zocalo`, `alien_sector`
- a **metadata dict with a `groups` key** — `core_tube`, `tram`. Indexing `[2]` on it raises
  `unhashable type: slice`, which reads as a data bug rather than a shape mismatch.
- a **dict keyed BY group name** — `components`. There is no third element at all; `[2]` raises
  `KeyError(2)`, which looks like a missing datum rather than a wrong assumption.

### Three scene errors, each found by the gate, each the same mistake one step further

`garden`+`drum_ground`, then `core_tube`+`tram`, then `interior` — all **drum**-scene, all checked
against `interior`, each round reporting correctly-bound materials as unresolved (42, then 39).
Resolution is scene-filtered and my checks kept forgetting it.

### The exterior fallback is not a failure mode

Four components — `cobra_bay`, `docking_port`, `forward_comms_plate`, `observation_dome` — have no
explicit bind and land on `hull_exterior`, which is **deliberately unbound** (materials.py asserts
it) because most of an 8 km hull is hull, and `exterior.tscn` sets it as `fallback_material`.
`resolve_any` returning None there means "no rule matched", not "no material". Counting them as
unresolved would have held the number below 118 for ever over surfaces that render correctly — and
the fix a reader would reach for, binding `hull_exterior`, is the one thing that must not happen,
because a bound fallback stops being a fallback. The gate reports them separately and asserts the
named fallback is real and unbound.

### One self-inflicted regression, caught immediately

Adding `BESPOKE_SCENE` put the module name `"drum_ground"` into a file `_scan_generator_groups()`
reads, and the literal scan took it for a group. `test_materials_layer3.py` and
`apply_proposals.py` join `NOT_GENERATORS`: **a file that talks ABOUT the generators is not a
generator.**

## NEXT SESSION — layer 4, lighting

Layer 3 is complete, so layer 4 is legitimately open. `directory.py` says so.

1. **The lighting rig has no night side** — standing blocking finding, and the owner's opening beat
   is the station coming into view. The rim kicker sits at `sun_az + 175` and the fill is mirrored
   through the camera axis, so whatever azimuth the camera takes the camera-facing edge is lit. The
   anti-sun frame needed `--light-gain 0.04` to show the windows at all. Needs a shot flag that
   composes the arrival: key behind the station, rim reduced to a true edge, fill off.
2. **The magenta guideway light runs** in `drum_interior_engine` — the other standing blocking
   finding.
3. **There is still no corridor shot.** `tools/export_scene.py` has `exterior` and `drum` only, so
   the most-seen surface in the station has never been rendered in the engine. Layer 4 needs one to
   judge interior lighting at all.


## Session 3n — LAYER 4 HAS AN EYE. The first interior frame in the project's history.

`docs/engine-corridor.png` — Godot 4.4 double + lavapipe, 1280×720, 24 s. Segmented pilaster
strips, warm downlight pools low on the wall, portal heads receding overhead, studded deck plate
with the specular run the frames show, rail band and skirt reading as articulation.

**Layer 4 could not start without this.** The material library declares three scenes; two had a
`.tscn`. The interior scene has **96 materials and 265 rules — the largest of the three, 40% of
the library — and not one had ever been rendered**, because there was nowhere to render it. Layer 3
was declared complete over surfaces nobody had ever seen. This is layer 4's equivalent of layer 0.

### The light IS the fitting

`fixture_lights()` puts an omni at the centroid of every tagged `light_*` span, so lighting follows
geometry and cannot drift from it — CLAUDE.md hard rule 4 applied to light. The alternative is a
table of lamp positions, which is a second description of where the fittings are; the moment the
kit moves a downlight the table is wrong and nothing says so.

Colour and relative energy come from **each fitting's own material**. The four kit fittings are not
one colour: `light_downlight` is warm at (1.00, 0.68, 0.40) and the pilaster strip, portal head and
deck channel are cool blue-white near (0.88, 0.93, 1.00). Passing one lamp colour would have thrown
away the warm/cool contrast that is most of what a B5 corridor looks like — **and it would have
looked deliberate.**

### THE FINDING, and the shot produced it on first use

> **ZERO of the 68 procedural rooms have a light fitting.** `medlab_one` renders BLACK. The only
> things that glow in a `rooms.py` room are seventeen terminal screens.

That is the `FIXTURES` lesson one layer up. At layer 2 the room contained its controls and not the
machine they controlled; here the room contains everything except the means to see it. A room with
no lamp is a room nobody can be in.

The black frame is the shot behaving correctly, not failing — `fixture_lights` is documented to
return nothing when nothing is tagged, precisely so that an unlit room is legible instead of being
quietly filled by ambient.

### Two calibration errors, both mine, both caught by looking

The first frame came back **pure white**: I left `--light-range` at the drum's **1100 m** default
inside a 21.6 m corridor, so all 117 sources reached every surface with no falloff. And 117 was
itself wrong — a pilaster strip is seven tagged bars 120 mm apart, which is one lamp. Merging by
proximity within a group took it to 33 and kept the segmentation where it belongs, in the geometry.

### Also

`interior.tscn` has **no scene lights at all**, deliberately. Ambient is 0.015 — a tenth of the
drum's — because a corridor is a closed box whose only light is its fittings. SSAO radius 0.6 m
against the drum's 2.5, because the subject here is a skirting board, not a landscape.

## NEXT SESSION — layer 4

1. **Give `rooms.py` light fittings.** 68 rooms, zero lamps. Archetype-driven, the same shape as
   `FIXTURES`: a medlab has a ceiling grid, an industrial bay has high bays, a chapel has something
   else. Until this exists, 68 of 118 locations cannot be lit at all.
2. **The corridor is too bright and too even.** It reads as a clean modern hospital rather than
   `grey level 1.webp`'s mood. The fitting-to-fill ratio is the number that fixes it, and a
   three-agent measurement pass over the reference frames was running when this was written —
   its results land in `docs/` and should be applied before tuning by eye.
3. **The lighting rig still has no night side** (exterior, blocking) — the arrival shot.
4. **The magenta guideway light runs** in `drum_interior_engine`.


## Session 3n (cont.) — the corridor is lit to a MEASURED number, not to taste

`docs/engine-corridor.png`. Three agents measured the reference frames; 58 fixtures, **32 of them
emissive-only**, and three ambient ratios. Applying it changed the frame completely.

### The finding that fixed the render

> **Of the four fittings `interior_kit` builds, exactly ONE lights anything.**
> `light_downlight` is an omni at 2650 K, range 1.2 m, no shadow. `light_pilaster_strip` and
> `light_portal_head` are **emissive only** — the strip is the brightest thing on the wall and it
> illuminates nothing.

Two independent tests in `grey level 1.webp`: the deck directly beneath the strip reads balanced
L 0.29–0.35 against a mid-corridor deck field of 0.446, i.e. **darker**; and `materials.py`'s own
PROVENANCE already had the pilaster face at V 0.301 against a wall plate three metres away at
V 0.295. So a corridor is lit by a few weak warm downlights and *read* by a lot of cool emissive
trim — and treating the trim as lighting floods the fill and destroys exactly that contrast. That
is why the first frame looked like a clean modern hospital. 33 sources → 12.

### Calibrated against the measurement, not by eye

The discriminating number is the agents' **between-fittings ratio on one surface: trough/peak
0.52–0.55**, and it is trustworthy because they ran a control — an *unfitted* wall scanned the same
way varies only 0.83–0.92, so the 0.52 is the fittings and not a lens vignette.

Measured on my own render and swept: ambient 0.55 → 0.383, 0.90 → 0.462, **1.30 → 0.526**, inside
the band. `interior.tscn` ambient is 1.30.

**Two traps in that calibration, both worth carrying:**

1. **The metric is resolution-dependent.** A 640×360 sweep said ambient 0.55 gave 0.465; at
   1280×720 the same scene gives 0.383. Different pixels, different AA, different bloom. *Calibrate
   at the resolution you judge at.*
2. **Whole-frame p10/p90 and the wall scan disagreed** — they pointed at ambient 1.05 and 0.56.
   That gap is a real difference between my shot and the reference: my corridor section ends in an
   open black aperture and the reference frame is closed, which depresses the global percentile.
   The wall metric has a control; the global one does not. Trust the one that was designed against
   a null.

### Still open on this frame

The agents also found **two corrections to `interior_kit`'s own geometry and one to `materials.py`**,
neither applied yet:
- the pilaster strip is built 0.50→0.86 of wall height (0.90 m, 7 bars at 0.129 m pitch) and
  measures **0.56→0.75 (0.48 m, 3 cells at 0.196 m pitch)** — roughly 1.9× too long with cells 1.5×
  too small;
- the strip's library colour is linear (0.748, 0.848, 1.000), a decided blue; measured balanced it
  is (0.956, 1.000, 0.895) at 6200 K. The agent states the circularity honestly — grey-world forces
  the dominant illuminant to neutral — and gives the constraint that survives it: the unfitted wall
  balances to linear (0.738, 0.955, 1.000), so *some* blue bias is defensible and one that strong
  is not.

## Session 3o — the 68 dark rooms are lit, and the exposure is a measured number

**`directory.py` now reports layer 4 at 68/118, and that number is computed.** The predicate it
replaced was `bool(place.get("lights"))` — a field nobody sets, so the counter read 0 whatever the
geometry did and would have read 118 the moment someone typed the field in. It now asks the
generator whether the place emits a tagged `light_*` group, which is the only thing that becomes a
real source in the renderer.

**`rooms.LIGHTS`: eleven archetypes, two fittings each, sixteen distinct types, 1,184 fittings
over 68 rooms.** Same shape as `FIXTURES` and for the same reason. Nothing in it is a new lamp
colour: every fitting is one the three measurement agents recorded in `docs/layer4-lighting/*.json`,
and what is invented is *which measured fitting each kind of room uses* — `INV-037`, with the
argument for each of the eleven rows. Eight new materials carry them; three existing materials took
an extra bind where the layer-4 measurement and the layer-3 material turned out to be the same
object (`bay_floodlight`, `bar_pendant_lamp`, `sign_neon_venue` — the last corroborated from a
different frame to within 0.04 in every channel).

**Placement had to go through the gaps, not around the collisions.** The first version put fittings
at nominal centres and dropped whatever collided, and produced *zero* wall courses in every room in
the station. `rib_pitch_m` and the fitting pitch are both derived from the room, so the two lattices
coincide and every course landed on a rib. `_lay()` now measures the free intervals first and lays
the fitting into them at its own measured pitch — which is also where the reference frames put a
light course, in the recessed bay between two ribs.

**The renderer grew spots.** Five of the eleven fittings were measured as spots and every one was
identified *by its shape* — a hard-edged pool with a body-shaped hole in it, a 1.57 m disc on a
deck, a cone shade over a table. `render_shot.gd` was omni-only, so rendering them would have
thrown the measurement away.

**`ROOM_EXPOSURE`, and why it exists.** Every fixture in the measured JSON carries an `energy_rel`
that is relative *within its own family*; no reference frame contains two families, so nothing in
the measurement says how a war room's 1.0 compares to a docking bay's. That missing number is now
measured from our own renders: render one room per archetype, measure it and its mapped reference
frame with the same code, scale until the render sits at the multiple of its reference the corridor
already sits at. Two passes took the spread from **0.53–7.75 to 1.32–1.52** against a 1.40 target.

**`tools/measure_frame.py` — and it was wrong on its first day, in a way worth recording.** It
reproduces the reference measurement on a PNG. Used naively against the JSON's `ambient.ratio` it
drove the corridor to an ambient of 5.6 and a frame two and a half stops hotter than the show —
because the JSON's ratio is two hand-picked regions of a *balanced* frame and this is a whole-frame
percentile of a raw one. Running `grey level 1.webp` through the same code settled it: the frame
whose entry says 0.300 measures 0.086, and across eleven spaces the two statistics correlate at
Pearson 0.65. **The only valid comparison is our frame against the show's frame, measured by the
same code**, which is what `--against` does and what the docstring now says at length. The
corridor's existing 1.30 ambient was vindicated by that test: reference 0.086/0.053, ours
0.081/0.074.

**A finding I recorded and then had to withdraw, which is the point of measuring.** I wrote down
that 23% of the market frame being crushed below the measurable floor was a defect against
`grey level 1.webp`'s 2.25%. Running the *other ten* reference frames through the same code refutes
it flatly: the show's interiors crush **far harder** than ours — the Zocalo reference 54.9% against
our market's 19.2%, the C&C reference 49.8% against our brig's 13.2%, `more hallways.jpg` 61.5%
against our fabrication's 54.4%. `grey level 1.webp` is the outlier, because it is the one *bright*
residential corridor in the set, and I had generalised from it. The rooms are not too black; if
anything the generic archetype at 10.7% is the only one over its reference. **Same lesson as the
ratio, twice in one session: run the new statistic against the whole corpus before trusting it
against one frame.**

**The finding that fell out of it.** Scaling only the fittings moved medical from 7.5× to 3.1× and
moved transit, worship and generic by *nothing at all*. In those rooms the fittings contribute
almost nothing to the frame — a corridor downlight reaches 1.2 m — and what fills the room is
ambient and the emissive surfaces. An exposure that cannot move the dominant term is not an
exposure, so it scales both.

Frames: `docs/engine-medlab.png`, `docs/engine-market.png`. Suites: rooms 579, materials 1364,
layer-3 gate 34, directory 744, export_scene 80, measure_frame 9.

## Session 3o (cont.) — the bespoke modules can be seen, and four of them are lit

**The interior shot could assemble exactly two things**: the corridor kit and a rooms.py bay.
All fifty locations built by a bespoke module raised SystemExit — so the Zocalo, the docking bay,
command and control, the council chamber, seven classes of quarters, the alien sector and the
plant rooms had materials, had lamps in several cases, and **had never been rendered from the
inside**. `BESPOKE_GEOMETRY` records the entry point for each of the nine interior-scene modules;
`to_spans` normalises the four shapes their third return value comes in.

**Three defects between that and a frame worth looking at, all found by looking:**

1. **The archetype exposures leaked onto bespoke rooms.** `rooms.archetype()` reads a place's
   `functions`, so it classifies a bespoke place happily — C&C came out "office" and took office's
   0.14, calibrated against a rooms.py bay with rooms.py fittings. The frame came back **100% below
   the measurable floor**. A bespoke module now falls back to the corridor anchor.
2. **`open_standpoint` measured distance to VERTICES.** A 30 m end cap is two triangles with four
   corners, so its middle scored as the most open spot in the room and the Zocalo camera stood
   outside the concourse with a bulkhead filling the frame. It now rasterises triangle footprints
   (`rooms.walkable`'s method) and scores by **the clear run ahead** — `zoc_bulkhead` caps both ends
   and the stall awnings overhang past them, so "nearest free cell" was worth nothing.
3. **The light rig gated on SPELLING.** `fixture_lights` skipped any group not named `light_*`,
   which locked out every bespoke module: `zoc_rib_lamp`, `bay_lamp`, `bar_pendant_lamp` are all
   recorded in the measurements as real sources, two shadow-casting, and none could ever cast.
   Membership of `FIXTURE_LIGHTING` is the gate now. Renaming nine modules' groups would have
   broken their material binds, scene rules and layer-3 count to satisfy a convention.

**Five bespoke fittings now cast, and no value in them is new.** `bay_lamp`, `zoc_rib_lamp`,
`zoc_stall_light`, `bar_pendant_lamp`, `cc_light_strip` — every one is a fitting its module already
builds and the committed JSON already measures, and unlike the room fittings **not one range needed
scaling**: each was measured in the very volume its module builds. `BESPOKE_EXPOSURE` calibrates
four modules to 1.38–1.46× their reference frames against a 1.40 target. The corrections were small
(0.90–1.34), which is the informative part: what those modules lacked was not exposure but sources.

Frames: `docs/engine-zocalo.png` — the station's social centre, elliptical rib arches, gallery and
stairs both sides, stalls under awnings, warm rib lamps against the cool deck strip.
`docs/engine-cnc.png`, `docs/engine-dugout.png`, `docs/engine-docking-bay.png`.

**A workflow that cost time and produced nothing.** Six proposal agents plus six adversarial
verifiers were launched for the bespoke modules. The machine's concurrency cap is 2, so after
fifteen minutes two agents were still on their first pass and none had written its output. It was
stopped and the work done serially from the same committed JSON the agents were being asked to
read. **The lesson is about this machine, not about the pattern**: at 2 concurrent, a 12-agent
fan-out is a 6-deep queue, and the useful width here is 2–4.

## Session 3o (cont. 2) — LAYER 4 IS 89 / 118

**`plant` and `quarters` have light, and the counter is a two-part test now.** A bespoke module
counts toward layer 4 when it emits a group the rig will actually turn into a source — membership
of `FIXTURE_LIGHTING`, which is what `fixture_lights` tests — **and** it has a calibrated exposure.
Fittings without an exposure is a lit room at an unmeasured brightness, and the layer is "lit to its
reference's mood", not "lit". That takes it from 68 to **89 of 118**.

**plant** built no light of any kind and rendered 85% black. It now carries the measured SERVICE
register: `light_service_tube` (emissive only — the thing you see, not the thing that lets you see)
and `light_plant_flood`, which is the docking bay's flood and **the one range in this project that
transferred with no arithmetic at all** — measured at 30 m in an 18 m bay, and a five-deck plant bay
is 5 × `DECK_PITCH_M` = 18.0 m exactly.

**quarters** had only a Babcom screen. It now takes the residential corridor's own kit, and the
measured height transfers **as a ratio, not a length**: "0.35 ± 0.02 of clear deck-to-soffit height"
is 0.88 m in a corridor and 0.98 m under a 2.8 m quarters ceiling. No per-class lighting — nothing
in the reference distinguishes an ambassador's suite from a transient cell by its fittings, and what
does differ is how many fittings a unit gets, because the spacing is fixed and the unit sizes are
not. `docs/engine-quarters.png`.

**Three camera defects, each found by looking at the frame it produced.** `plant.py` builds in
STATION coordinates, and rightly — its subject is a bay spanning five decks of a spinning ring. But
"up" there is radially *inward* and the shot assumes +Y, so `unroll_to_local` flattens the arc into
a standing frame. `open_standpoint` assumed the floor was the bottom of the model, and the plant
catwalk is 15.6 m up — it now finds standing levels by histogramming near-horizontal triangle area,
and uses the module's *declared* walkway where there is one. And the aim was always +Z, while the
catwalk runs along the arc — so the camera looked across a 1.8 m walkway into unlit void. **Asking
the module beats inferring**, the same way `light_` tagging beats guessing which material glows.

**A negative result.** `BESPOKE_EXPOSURE["plant"]` barely moves the measurement: the frame is mostly
below the measurable floor, so dimming pushes more pixels under 0.01 and *raises* the median of what
remains. The two cancel and it sits at 1.59× either way. In 139.8 million m³ of void with seven
floods in it, the median of the lit pixels is not an exposure measurement.

## Session 3o (cont. 3) — the council chamber, and a fitting that is never in frame

**90 / 118.** The chamber's measured lighting scheme, `cc_house_wash`, is *the whole room* —
directional, 6300 K, range 18 m, shadow, "a broad soft near-neutral wash" — and the measurement
states the difficulty in the same line: **"fitting never in frame"**. That is a real problem for a
rig where every light is derived from tagged geometry. Adding a lamp where the frames show none is
invention; adding nothing leaves the chamber on ambient, and its ratio of 0.210 makes it one of the
two brightest measured spaces on the station, so "no source" is wrong too. `house_cove()` is the
smallest thing that can carry a light and still be concealed: a cove high on the rear wall, above
the fin fan, facing away from the room. Declared, in `INV-037` and on the material.

**A value that was wrong, and the render said so within one frame.** The cove's `emission_energy`
was set at `light_downlight`'s 4.0 on the argument that the reference shows a wash and not a source
— and 4.0 drew a bright white bar across the top of the chamber, which is the exact failure that
argument was made to avoid. Now 1.2, below `light_ceiling_grid`'s 2.6.

**Customs was tried and withdrawn, and the withdrawal is the finding.** The arrival hall's ceiling
coffer looked like the obvious next entry: its colour was measured on the fitting itself and the
same frame ranks its three source families by balanced peak (screens 0.99, wall strips 0.82, grid
0.55 → an energy_rel of 0.56). Given a light, `customs.hall()` emits **210 separate coffers**, the
frame came back at **18.9× its reference with 14% clipped**, and the exposure needed to rescue it
was 0.07. The real answer was already written in that material's own source note — the grid is
*"ambient decoration rather than a task light"*, ranked last of the three. It is emissive-only for
the same reason the pilaster strip is, and **customs therefore has no measured cast source and is
not at layer 4** — the honest count rather than a rescued one.

## Session 3p — a span is not a fitting, and a fitting is not always a point

Both defects from the previous list are closed, and the numbers say what they were worth. A tagged
span was cut into contiguous runs and each run became ONE lamp at its centroid — so a module that
emitted all of one fitting family in one go got one lamp however many it had built. Measured across
every lit room, that lost three quarters of the station's lamps and put several survivors in mid-air.

`fitting_bodies()` cuts a span into connected bodies, welded **by position rather than by vertex
index** — `council_chamber._M.quad` appends four fresh vertices per quad, so index connectivity
would have called one continuous cove twelve fittings and multiplied its flux by twelve.
`sample_body()` then samples any body longer than its own throw, sharing its energy **by area**, so
sampling changes where the light comes from and never how much there is.

**The recovered counts are the evidence, because they are numbers the MODULES chose and this code
had to rediscover independently:**

| room | fitting | before | after | what the module says |
|---|---|---|---|---|
| docking_bays | `bay_lamp` | 13 | **39** | `LAMPS_PER_BAY_GIRDER = 3` × 13 girders |
| zocalo | `zoc_rib_lamp` | 6 | **30** | five per rib, measured, × 6 ribs |
| cnc | `cc_light_strip` | 1 | **36** | four wall courses, sampled |
| council_chamber | `light_house_cove` | 1 | **6** | a 33.6 m continuous cove |

The single `cc_light_strip` lamp had been sitting **6.92 m from the nearest strip with a measured
range of 3.5 m** — twice its own reach away from the fitting it stood for, in the middle of a room
the measurement says stays dark.

**The corridor is byte-identical**: 12 lamps, 36.00 total energy, before and after. That mattered
because it is the anchor every exposure in the file was calibrated against, and it is now asserted
rather than hoped for.

**One gate I wrote was vacuous and had to be replaced.** "Every light is inside its fitting's
bounding box" passes the old rig trivially — the centroid of a set of points is always inside their
bounding box. The version that ships probes the fitting's *surface* and fires on the old rig at
exactly the distances its comment claims (cove 0.216 of its reach, `cc_light_strip` 1.976,
`zoc_rib_lamp` 0.288). A first attempt at *that* measured distance to the nearest **vertex** and
failed a correctly-placed sample 4.32 m from the corner of an 8.64 m box — the same lesson
`open_standpoint` already carries: **coarse architecture is what this project is made of and vertex
distance is never the question.**

**A measurement caveat worth carrying.** The corridor reads x1.64 of its reference at 640×360 and
x1.41 at 1280×720 — resolution dependence, not regression. The exposure tables were calibrated at
640×360 against a 1.40 anchor derived at 1280×720, so they are internally consistent but the anchor
and the calibrations were taken at different resolutions.

### Two generated-artefact holes, both found by the stop hook

**A truncated texture was committed, and nothing could see it.** `deck_stud_orm.png` was in the
repository at 196,673 bytes against the 613,211 it regenerates to — PIL refuses to load it. It is
the occlusion/roughness/metallic map for `kit_deck`, the deck of every corridor on the station.
Every existing gate passed on it: the material resolves, the size is declared, the slope is
declared, and the VRAM budget is computed from `TEX_SIZE` rather than from the file.

**The cause was my own timeouts.** A full `materials.py --export` takes 51 s and I had been running
it under 2-minute `timeout` calls that also had a render queued behind them; a killed export leaves
a half-written PNG. Two more textures were caught mid-write during this very session, a different
one each run, which is what identified it.

**Two `.tres` files the ENGINE READS had drifted from the library.** Three emission energies were
re-tuned against engine frames and `light_arrival_strip` still said 5 against the library's 3,
`light_deck_grating` 3.5 against 1.2. This is the scene-rules defect one file down — material rules
used to be emitted to a `.txt` for a human to paste in, and `patch_scene_rules` exists because the
first material added after that never reached the render. The `.tres` had no equivalent gate.

Both now gated in `materials.py`, and both gates were shown to fire on the exact artefacts that
were in HEAD.

### The second agent's work, and a bookkeeping note

The alien/customs agent from the previous firing did complete real work, and my `git add -A`
swept part of it into the commit before this one, which was titled for the light rig. The rest was
in the working tree. It is all here now and it is good — every change is driven by an engine frame:

* **`light_ceiling_grid` 2.6 → 0.8**, and the argument is one this project had only ever made in
  the other direction: **the energy ladder is blind to AREA.** `customs.hall()` coffers 64% of a
  34 × 17 m soffit — roughly 370 m² against `light_pilaster_strip`'s ~0.2 m², a factor of 1,800 the
  ladder says nothing about. `bay_floodlight` already argues *upward* from size ("the fitting is far
  larger … roughly fifteen times the flux"); nobody had argued downward. Customs' clipping went from
  **14.42% to 0.00%** and the ceiling now reads as an amber lattice with dark ribs.
* **`light_arrival_strip` 5.0 → 3.0**, because at 5.0 that one band accounted for 2,054 clipped
  pixels — 100% of the frame's clipping — and the reference's own cells do not clip (raw sRGB V p99
  0.927). A value that blows is refuted by the frame it came from.

### The alien sector is lit — 92 / 118

The agent's `alien_sector.py` work was already committed; what was missing was the one line that
makes a fitting cast, and it had left the exact dict in `CAST_FITTINGS` with the measurement behind
it. Colour read RAW off the descending shafts and **corroborated by the floor grating — the same
source seen twice, agreeing in R:G to 0.7%**. Range 4.0 m derived from the module's own dimensions:
the grille hangs at `GALLERY_H_M` 3.4 m and the deck's far corner is √(3.4² + 2.1²) = 4.00 m away.
Cone 30° against the 31.7° that covers wall to wall, so the skirtings stay dark — the frame's
darkest surfaces are the pier feet.

**The light hangs on the trough and not on the grille**, which cost that agent a render to learn:
`alien_lattice` is fifty-six separate bars and `fitting_bodies` correctly reads each as its own
luminaire, so the frame came back with 126 lamps at 7.10× its reference. A grille is a *diffuser*;
the source is behind it. Eight troughs where there were fifty-six bars. `docs/engine-alien-sector.png`
— amber floor grating and ceiling lattice against cold grey walls, which is the frame's own
(1.000, 0.796, 0.273).

`BESPOKE_EXPOSURE["alien_sector"] = 1.00` is an entry rather than an omission: rendered and measured
at the anchor, correction none, and saying so explicitly is what makes it count as measured.

### The workflow's report, and a correction to my own claim — 95 / 118

Both agents finished after the session boundary. Their module work was already committed; what was
missing was the four lines in `export_scene` that make a fitting cast, and applying them takes
layer 4 from 92 to **95**. `customs_north` lands at x1.36 of its reference and `alien_sector` at
x1.31, both against the x1.40 target.

**I attributed the council chamber's bright arc to the wrong thing.** The previous next-session item
said it was the cove's own omni washing it point-blank. It is not: rendering with
`--fixture-energy 0` — every fixture light removed — leaves the arc *unchanged*. It is the cove's
**emissive face**, seen directly, because `house_cove()` builds the lit strip with no concealing lip
although its own docstring says "its housing hidden behind the lip". The fix belongs in
`council_chamber.py`, not in the rig.

**Two exposures I set were worse-founded than I thought.** `alien_sector` was 1.00 because I set it
by eye against the *corridor's* median, not having found a reference frame for the sector —
`reference/05-sector-green/corridor in alien sector.webp` exists, is authority 1, and is the frame
the module's fitting was measured from. Against it the correction is 0.47. And `zocalo` needed
0.92 → 0.84 because recovering the five-lamps-per-rib the module actually builds multiplied its flux.

## Session 3q — the camera stands on a floor

**Three defects in `open_standpoint`, and the first was mine from session 3o.** The eye in command
and control sat at **y = −0.20 m** — in the 1.9 m instrument pit with its eyes at deck level,
looking down the pit and away from the wall courses that light the room.

1. **The level was reported at its histogram bin's LEFT EDGE**, up to 0.5 m below the surface it
   stood for. It is now the area-weighted mean Y of the surfaces in the bin — exact, and one line.
2. **The search preferred a long view over a large floor.** The pit is real floor and a person can
   be in it; it is 17% of the room's horizontal area against the main deck's 47%, and that is what
   makes one of them *the* floor. The level score is now multiplied by its area share.
3. **"Nothing blocks the body" and "something holds the body up" are different questions**, and
   only the first was being asked. With 1 and 2 fixed the eye was at a standing height — and in
   three rooms out of eight it was standing over a hole: the pit's open mouth, off the near end of
   the docking bay's deck, and outside the council chamber's raised floor. A level's histogram says
   the floor *exists*; it does not say it is under this particular cell. The occupancy grid now
   carries a floor mask.

**Every eye now lands at exactly 1.70 m above its own floor** (1.60 where the ceiling forces a
crouch), across all nine bespoke rooms.

**The gate cost three attempts and the failure was the same one three times.** Asking for a nearby
*vertex* failed customs and the docking bay — the two rooms with the biggest floors, whose decks are
single quads with their corners twenty metres away. That is the third time this session vertex
distance has been the wrong question about coarse architecture; `open_standpoint` itself and the
light-placement gate both carry the same lesson now.

**Two exposures re-measured, both because a correction moved the frame rather than because a number
looked wrong.** `command_control` 0.93 → **1.10** (the old value was calibrated against a shot of
the underside of a floor) and `council_chamber` 2.84 → **2.27** (the cove became six lamps round the
arc, and the camera moved onto the chamber floor; at the old value the corrected frame read x1.75,
the very edge of tolerance). Both now land at x1.46 and x1.41 against the x1.40 target.

`docs/engine-cnc.png` is the station's bridge from its own deck: the blue wall courses casting along
the wall, the command dais and its rails, a console's lit fascia, the radial viewport.

## Session 3q (cont.) — the drum is calibrated, 109 / 118

**The counter was excluding the anchor.** `interior_kit` builds the corridor and the junction — the
two places every exposure in the project is calibrated against, whose fittings were the first ever
measured and whose frame is what x1.40 *means*. It has no `BESPOKE_EXPOSURE` entry because it **is**
the 1.0 the others are measured in, so a membership test on that dict reported the best-calibrated
room on the station as unlit. 95 → 97.

**The drum was the last lit volume in the project with no measured exposure.** Its rig has been
rendering since session 2j and `RUN_ENERGY` was set by eye. Measured against
`reference/03-sector-blue/Babylon_5_2-22_34b.jpg` with the same code as every room, the standard
drum shot read **x1.03 of its reference against the x1.40 target** — under-exposed by a third. The
response is very nearly linear (gain 1.36 gave x1.35), so `DRUM_EXPOSURE = 1.41`, verified at
**x1.39**.

`DRUM_EXPOSURE` is kept separate from `RUN_ENERGY` on purpose. `RUN_ENERGY` is the physical claim —
the total flux one 2.6 km light run contributes, normalised so sampling density stays a cost
decision — and this is the exposure that claim is viewed at. Keeping them apart is what let the
sampling density change in session 3p without anyone re-arguing the flux.

**The drum is one lit volume with one rig**, and that rig is not `FIXTURE_LIGHTING`:
`light_runs()` derives sixty sources from the guideway trusses' own placement arithmetic. The
modules inside the drum are lit by the drum, exactly as the corridor kit's two places are lit by the
corridor's fittings — so with a real rig and a measured exposure, the same two-part test the
interior modules face, they count. 97 → **109**.

`docs/engine-drum.png`: the ground curving up and over, the core tube and its spoke node, the
guideway trusses blazing along the crown, the end cap's concentric rings.

### Correction — the drum branch was counting to green, 109 → 105

I wrote the drum branch of `_lit_keys` and it was the weakest predicate in the project. It counted
**every** drum-scene module because the *drum* had a measured exposure. `drum_parts()` is the one
list of what the drum shot holds — ground, two end caps, guideways, spokes, core, trams — and
`garden.townscape()` is not among them. Four locations were being counted on the strength of a frame
their geometry does not appear in.

Now computed by intersecting each module's own group names with the shot's, rather than by listing
modules, because a list would be a second copy of `drum_parts` and two copies of a mapping with one
of them updated is this project's recurring failure. `interior`, `core_tube` and `tram` survive —
they really are in that frame. `garden` does not. **105/118.**

Pinned by an assertion that fails both if the predicate is re-broadened *and* once the garden really
does enter a frame — which is the right moment to be made to look at this again.

**The wider point, from the critique this came out of:** about twenty measured frames justify 105
places. Fifteen have a frame of their own, 68 inherit an archetype's (11 frames), 8 come from the
drum shot, 2 are the anchor. That is documented and defensible, but "105 lit" reads as "105 were
looked at" and roughly twenty were.

### Layer 4 is 113/118, and the five that remain have a measured reason

**The nine `components` places now count.** They are hull fittings — cobra bays, the observation
domes and rotundas, mooring clamps, proximity arrays, nav beacon, comms grids, power transfer core
— and they fell through every branch: not in `BESPOKE_EXPOSURE` (which holds *room* exposures) and
not in the drum. The exterior is a lit volume like any other and now has a measured day exposure,
so they reach layer 4 on the same two-part condition as everything else. What makes it falsifiable:
`directory.py` reads `exterior.tscn` back and the nine only count while the scene is still at the
exposure the calibration was verified at. Setting it to the old 1.00 drops the count to 105 and
fails an `export_scene` check — demonstrated, both.

**`garden.townscape()` was missing from `drum_parts` entirely.** Added: it stands on the drum floor
inside the settlement arc, 2,228 tri. That is a real hole closed — the drum shot was not building
geometry that exists.

**But adding it to the list is not the same as it being in the frame, and this is the finding.**
The calibrated drum shot was re-rendered with and without the townscape: **zero pixels changed.**
I had looked at the frame first and thought I could see the settlement overhead; those were the
ground's own band, and the diff caught me. So every drum part was then measured the same way, one
omission per render, percent of frame moving by more than 8/255:

| ground | guideways | endcap_fore | spokes | core | trams | endcap_aft | townscape |
|--------|-----------|-------------|--------|------|-------|------------|-----------|
| 89.53 | 34.60 | 5.43 | 1.38 | 1.28 | **0.01** | **0.00** | **0.00** |

That caught a second one I was not looking for: **`trams` moves thirteen pixels**. The tram's place
was being counted off a frame it is not meaningfully in, exactly as the garden's four were.
`DRUM_FRAME_CONTRIBUTION` and a stated 0.5% threshold now gate the branch, and both exclusions are
pinned by assertions. **113/118.**

### The garden reads 2.5x hot, and the cause is not exposure

A terrace-level frame matched to `Babylon_5_2-22_29a.jpg` — the authority-1 garden reference the
townscape was built from — measures **x3.49 against the x1.40 target**. Do not fix this with
exposure. `DRUM_EXPOSURE` scales light *energy*, so lowering it darkens the wide drum shot that
currently measures x1.40 correctly against `34b`. One volume, one rig, one number; the two
references differ by 2.7x in median because the show lit those scenes differently.

**The real cause: 58 of the drum's 60 lights cast no shadows** (`--shadow-lights` defaults to 2).
29a's darkness is *occlusion* — canopy, building, planting — and our garden has none, so it receives
unshadowed light from every source. That is a shadow-coverage problem with a real CPU cost, since an
omni shadow is a cube map.

Also noted while there: at terrace range the townscape's 2,228 triangles read as boxes on sticks.
Layer 2 passed it because nothing had looked at it up close. That is layer-2 debt this layer-4 pass
surfaced, not a lighting fault.

## NEXT SESSION — layer 4, the last 5

0. **The garden (4) and the tram (1).** Neither is a tuning job. The garden needs shadow coverage in
   the drum before any exposure claim about it means anything; the tram needs a framing that
   actually shows a car. Both are named above with their measurements.

0. **The garden has never been rendered.** Four locations. It needs a `BESPOKE_GEOMETRY` entry or a
   place in `drum_parts`, then a frame and an exposure like every other module.

**Every remaining place is `components` — the exterior fittings**: cobra bays, docking ports,
observation domes, rotundas. They are lit by the exterior rig (key, fill and rim as
`DirectionalLight3D` nodes in `exterior.tscn`) and that rig has never been measured against a
reference either. It is the same job the drum just had. Note the standing blocking finding while
you are there: **the exterior rig has no night side**, which the arrival shot needs.

Then, in the order they were found:

1. **`house_cove()` has no concealing lip**

1. **`house_cove()` has no concealing lip** — see above. Build it, or drop
   `light_house_cove`'s emission.
3. **Our frames crush far LESS than the show's**: customs 0.28% against the reference's 50.34%,
   alien 6.63% against 14.51%. The p5/p95 ratios are respectable, so this is the deep end of the
   curve rather than contrast — a global tonemapping question, not a per-room one.
4. **`00-INDEX.md` has been asking for `light_grating` in `interior_kit.py` since session 2q.** It
   was built inside `alien_sector.py` because that was the agent's file. It is one station-wide part
   with a tint parameter appearing in four frames; when it moves into the kit,
   `light_deck_grating` and `light_deck_channel` become one material with two tints.
5. **The alien sector's walls are the wrong colour and it is a LAYER-3 problem.** The reference is
   dark olive-green throughout; `alien_wall` binds the shared shell material and renders pale
   blue-grey. What the frame supports is a per-sector tint on the shell wall — the same idea
   `SECTOR_ACCENT` already carries for accents.
6. **The pilaster strip's measured colour is still unapplied**, and `light_arrival_strip` now
   disagrees with it on purpose: `corridor_kit.json` measures the family at linear
   (0.956, 1.000, 0.895) and calls `light_pilaster_strip`'s (0.880, 0.930, 1.000) "a decided blue"
   its own measurement does not support. Changing it moves the residential corridor, which is the
   anchor every exposure is calibrated against.
7. **A stray `struct.py` in the scratchpad shadows the standard library** and makes every numpy
   import fail for anything run with that directory as cwd. Not ours; know about it.
8. **The remaining bespoke modules.**

1. **The council chamber's right half is black** (`docs/engine-council.png`, crushed 52%) because
   `house_cove()` only sweeps the rear half-arc, 0 to π. Its measured ambient ratio of 0.210 makes
   it one of the two brightest spaces on the station — a room with no dark corners. Either the cove
   goes all the way round or a second one does.
2. **The remaining bespoke modules.** Layer 4 stands at 68/118; the other 50 are the module-built places, and
   several already build lamps (`zoc_rib_lamp`, `bay_lamp`, `cc_light_strip`). What they do not have
   is a calibrated exposure and a frame measured against its reference, which is what layer 4 *is*.
   The measured fixtures for them are already committed in `docs/layer4-lighting/public_social.json`
   and `command_working.json`. Five are now applied; the rest need GEOMETRY before they can be
   lit, which is layer-2 work reached from layer 4:
   * **`plant` (5 places) has no light fitting of any kind** and renders 85% black — two tanks in
     the dark. It is the `rooms.py` industrial problem in a module that was not covered by
     `rooms.LIGHTS`.
   * **`quarters` (7 places)** has only `qtr_babcom`, a comms panel. No lamp.
   * **`council_chamber`**: `cc_house_wash` is measured as the chamber's whole lighting scheme and
     its "fitting is never in frame" — there is no geometry to hang a light on. Needs either an
     invisible tagged proxy or a different mechanism; decide and argue it.
   * **`docking_bay`**: `bay_mouth` — "NOT PRESENT IN docking_bay.py, which builds the mouth as an
     opening and lights nothing."
   * **`command_control`**: two more wall courses, `cc_console_skirt`, `cc_pit_indicator`.
   * **`zocalo`**: the measurement says 60–100 bulbs a stall against the 6–9 zocalo.py places, and
     that the overhead downlight's cone must be ≥50°— but zocalo.py has no ceiling fitting geometry
     at all; `zoc_downlight` is the lit patch ON THE DECK.
2. **Our lamps clip where the show's do not.** Measured across the eleven calibration renders and
   their reference frames: ours clip 0.00–3.13% of the frame, the references 0.00–0.54%. The
   Zocalo reference clips 0.00% and our market frame 3.13%; the war room 0.00% and our medlab
   2.48%. It is the lamp *lens geometry* blowing, so the fix is `emission_energy` on the fittings
   rather than the exposure — with the caveat that a graded screencap rolls off and a render does
   not, so some of the gap is the medium.
3. **Apply the two `interior_kit` geometry corrections and the strip colour** — measured, in
   `docs/layer4-lighting/corridor_kit.json`, still not applied: the pilaster strip is built
   0.50→0.86 of wall height and measures 0.56→0.75, ~1.9× too long with cells 1.5× too small.
4. **The exterior rig still has no night side** (blocking, the arrival shot); **the magenta
   guideway runs** in the drum.

---

## Agent report — drum walkable

**Session 3w, agent task: "make the habitat drum walkable, and nothing else."**

**IT WALKS.** A body spawns on the drum ground and covers **126.0 m in thirty seconds at 4.20 m/s,
`offfloor=0/1800`**, in the real engine, headless. Four locations, four different land uses:

```
PASS  drum the_garden    spawns on hedge,      walks 126.0 m over 25 ground patches, offfloor=0/1800
PASS  drum garden_town   spawns on settlement, walks 125.8 m over 25 ground patches, offfloor=0/1800
PASS  drum zen_garden    spawns on shore,      walks 125.9 m over 25 ground patches, offfloor=0/1800
PASS  drum drum_endcaps  spawns on parkland,   walks 125.9 m over 20 ground patches, offfloor=0/1800
```

All four legs at full speed (`legs 4.20/4.20/4.20/4.20`), so nothing snags in any heading. The last
one is the tile that touches the aft end cap and is therefore clamped to 20 patches instead of 25.

New file: **`station/drum_walk.py`**. `python3 station/drum_walk.py --selftest` is **24/24**
(23 without `--full`). Existing suites re-run and green: `station/interior.py --selftest` **449/449**,
`station/rooms.py` **581/581**. Nothing outside `station/drum_walk.py` and `canon/INVENTIONS.md`
(new **INV-081**) was touched.

### The design, and the one sentence that matters

`collision.py`'s rule survives and **inverts**. The corridor needed a *smooth* shell because its
render deck's 66 mm channel and 22 mm tiles are decoration a foot should not feel. **On the drum a
smooth shell would be the bug**: the relief is the content, and flattening a 7 m settlement podium
onto a 4 m lake bed would leave a player hovering over the fields and buried in the town — the same
error that put session 2u's first drum camera five metres underground. So:

> the corridor's collision floor must be FLAT where the render mesh is not;
> the drum's collision ground must be the SAME SHAPE the render ground is, cheaper, and free of
> anything a capsule can catch on.

This module therefore authors **no terrain**. It calls `drum_ground.ground_patch` — the function the
*render* ground is built from — on the same lattice, at a stride it derives. Not "measured off the
kit by ray casting" as the corridor profile is: one step stronger, the same source function, so
there is nothing to drift.

### THE GATE IS SLOPE, NOT LIP, and that is the substantive change

`collision.floor_steps` reports the largest step between neighbouring samples. That is exactly right
on a corridor, where the deck is flat by design and any lip is a defect. **Run it on terrain and a
correct hill fails it** — the drum rises 0.24 m between adjacent lattice points in places, which is
3.5 degrees, which is a field. What a character controller actually tests is rise over run against
its own `floor_max_angle`, so that is what `slope_report` measures: per emitted triangle, against
the inward radial at its own centroid, on the mesh rather than on whatever produced it.

### Numbers

| | value | where from |
|---|---|---|
| collision stride | **1** (3.90 m cell) | derived: the coarsest whose measured error stays inside a step. **Stride 2 measures 0.193 m against a 0.100 m step** and fails |
| step tolerance | 0.100 m | `rooms.TRIM_MAX_PROUD_M`, imported not restated — one definition of a step on this station |
| floor angle | 45.0 deg | Godot `CharacterBody3D.floor_max_angle` default, an engine fact |
| tile | **5 x 5 patches, 51,200 tri** | derived: the walk gate asks 126 m (1800 frames x 4.2 m/s), a patch is 124.9 x 129.4 m, a spawn can sit on a corner, so 2 rings. **One ring reaches 125 m and fails by a metre** |
| nearest tile edge | 250 m | |
| slope over the Garden's tile | max **12.70 deg**, 0 of 51,200 triangles over 45 | |
| slope over the **whole drum** | circumferential max **16.61 deg** (a lake shore at 146.25 deg), axial max **10.90 deg** (a cap ring road), **0 of 286,720 lattice steps over 45 deg** | `--terrain`, ~70 s |
| height range | -3.90 .. +8.90 m about the datum | |
| collision vs the render tile | max **-97.8 mm**, rms 20.5 mm | and that is the RENDER's own LOD: `lod_table` switches to lod1 at 198 m and the tile reaches 250 m |
| collision vs render **inside the lod0 radius** | **0.000 um over 92 casts** | identical lattice calls, so identical surface |
| patch seam, uniform stride | **0.0000 mm** | |
| patch seam, stride 1 against unclamped stride 4 | **266.6 mm** | why collision is uniform and needs no `clamp_edge` |
| spawn | cast against the MESH, not the field | at the Garden they are **39.2 mm apart** — four times the curvature sagitta, because the heightfield bends inside a cell too |
| render tile | 38,912 tri | **cheaper than its own collision**, because the render coarsens with distance and collision cannot |

### The whole-drum answer

Union of the 12 locations' tiles: **105 of 280 patches, 37.5% of the drum, 215,040 collision
triangles.** Whole drum at stride 1 would be 573,440. The rest of the walkable station is 74,044
between 66 decks, so the drum is expensive *in the right way* — it is 4.5 million m2 of open
country against a 2.6 m tube, and the tile is the streaming unit that difference forces.

The twelve locations, with the ground each stands on (`--places`):

```
drum_spokes      0.0 deg z=5200 h=+2.87 patch (0,10)  road
radial_tubes    20.0 deg z=5200 h=+2.08 patch (0,10)  arable0
the_garden      60.0 deg z=5100 h=+2.06 patch (2, 9)  hedge
garden_town    112.0 deg z=4900 h=+6.07 patch (4, 8)  settlement
earharts       120.0 deg z=4800 h=+7.28 patch (4, 7)  verge
fresh_air      128.0 deg z=4800 h=+6.64 patch (4, 7)  avenue
garden_terrace 130.0 deg z=4900 h=+6.71 patch (5, 8)  verge
zen_garden     150.0 deg z=5000 h=-1.79 patch (5, 8)  shore
water_rec      175.0 deg z=5100 h=-1.02 patch (6, 9)  shore
ground_tram    210.0 deg z=5000 h=+1.13 patch (8, 8)  hedge
drum_tram      240.0 deg z=5000 h=+0.05 patch (9, 8)  arable3
drum_endcaps   340.0 deg z=4000 h=+2.59 patch (13,1)  parkland
```

Every one has ground under it and none stands on `water_surface` — `zen_garden` and `water_rec` are
both on `shore`, at the water's edge, which is where they should be. The tiles *contain* water and
the collision follows the render exactly there, so **a body can walk out onto the lake**. That is a
content gap, not a collision one, and it is stated rather than gated.

### THE GATES CAN FAIL, and here they are failing

Three of the checks are inverted assertions on real geometry, in the style of
`collision._selftest`'s "and the render floor is NOT smooth" — if any stops failing, the thing it
argues about has gone away:

* **`interior.drum_interior`'s band shell is NOT a floor.** Over the same ground it has
  **10,820 of 15,700 triangles steeper than 45 deg** (max 179.7 — faces wound outward) and sits
  **+3.64 m** from the heightfield, rms 1.28 m. That is the drum's ground as it was before the
  heightfield, and it is a perfectly good thing to look at from 500 m.
* **A stride-4 tile sits +0.402 m off the render ground**, so the deviation criterion bites.
* **Stride 1 against an unclamped stride 4 leaves 266.6 mm of T-junction**, so the seam criterion
  bites.

And `--sabotage` runs the *same suite* against a tile with a known defect, so the rig is
demonstrated rather than claimed. All five produce real FAIL lines and a nonzero exit:

```
--sabotage lift     (raise the collision 0.5 m off what you can see)
  FAIL  a body stands on the ground it can see  -- +0.581 m at (22.95, 5313.2)
  FAIL  and inside the lod0 radius they are the identical surface  -- 499.9986 mm
  21/23
--sabotage winding  (reverse every triangle)
  FAIL  every collision triangle faces the player, not the void  -- worst 180.0 deg
  FAIL  the ground is walkable at the controller's own floor angle  -- 51200 triangles over 45
  21/23
--sabotage cliff    (a 6 m step one lattice cell wide)
  FAIL  the ground is walkable at the controller's own floor angle  -- 13130 triangles over 45
  FAIL  a body stands on the ground it can see  -- -3.040 m
  FAIL  and inside the lod0 radius they are the identical surface  -- 2264.5 mm
  20/23
--sabotage tiny     (one ring of patches instead of the derived two)
  FAIL  the tile is bigger than the walk the gate asks for  -- nearest edge 125 m against a 126 m walk
  22/23
--sabotage stride   (stride 4 instead of the derived 1)
  FAIL  a body stands on the ground it can see  -- -0.402 m
  FAIL  and inside the lod0 radius they are the identical surface  -- 345.1 mm
  21/23
```

### Two defects found in my own measurements, both of which looked like passes

Recording them because they are the same species this repository keeps catching:

1. **The seam test compared the things that coincide.** A coarse patch's border vertices are a
   *subset* of a fine patch's — every fourth vertex of a stride-4 edge is exactly a stride-1 vertex
   — so vertex-to-vertex comparison reported **0.0 mm for a seam full of holes**. The hole is the
   fine vertex sitting off the coarse patch's straight edge *segment*, which is what a T-junction
   is. Measured point-to-segment it is 266.6 mm. A crack test that passes on a cracked mesh is the
   `x == x` determinism check in a new costume.
2. **The spawn was computed from the terrain function and the body stands on the mesh.** They are
   not the same surface between lattice points: at the Garden the field says r = 276.2441 and the
   triangle a foot rests on is at 276.2049, **39.2 mm apart** — more than the 6.8 mm curvature
   sagitta, because the heightfield bends inside a cell as well. It happened to land on the safe
   side; with the sign the other way a body spawns embedded in its own floor. `stand_at` now casts,
   as a foot does.

### Verified visually

`tools/preview_render.py`, read directly, against **magenta** so a hole shows as magenta rather than
as black:

* From a standing eye (1.7 m) at the Garden looking down the axis: an unbroken ground plane curving
  up and away on both sides. No magenta inside the surface — magenta appears only past the tile's
  own angular edge, which is where the tile ends.
* From 176 m "up" (r = 110 m), the collision tile and the render tile from the identical camera are
  **visually indistinguishable** — the same folds, the same road and hedge lines, the same
  curvature. That is the claim ("the collision ground is the same shape as the render ground")
  shown rather than asserted. Difference is in the far field, where the render is at lod1.
* The frames were written to a session scratchpad and are not committed; the commands that make
  them again are, which is the more useful artefact:

  ```bash
  python3 station/drum_walk.py --at the_garden \
      --obj /tmp/drum_col.obj --render-obj /tmp/drum_ren.obj
  # standing eye, looking down the axis
  python3 tools/preview_render.py /tmp/drum_col.obj --out /tmp/eye.png \
      --eye 137.2721 237.7622 5100 --target 137.2721 237.7622 5350 \
      --up -0.5 -0.866 0 --fov 55 --headlamp --fog 400
  # 176 m up, against MAGENTA so a hole is not black -- run for both OBJs
  python3 tools/preview_render.py /tmp/drum_col.obj --out /tmp/wide.png \
      --eye 55.0 95.2628 4780 --target 138.077 239.157 5150 \
      --up -0.5 -0.866 0 --fov 62 --light -0.35 -0.55 0.6 --bg 255 0 255
  ```

  These are **structural** evidence from the flat-shaded rasteriser, not craft evidence — no craft
  claim is made here.

### WHAT DOES NOT WORK, precisely

1. **`walkable.py --deck green/1/0` still raises.** It calls `deck.build_deck`, which calls
   `deck._ring_cells`, which raises `ValueError: green ring 1 is not a ring deck` by design. Wiring
   it needs edits to two files this task did not own — the exact patch is below.
2. **Nothing on the drum is solid except the ground.** `garden.townscape()` puts 22,620 triangles
   of civic landmark, blocks, trees, hedges, benches and planters at 112 deg / z 4900 and a body
   walks through all of it. I tested the obvious fix — `collision.prop_boxes` with a garden-specific
   solid predicate — and **it is not safe to ship**: 18 boxes, and the largest is **58.15 m** across
   against a real block building's 9–22 m, because a townscape's buildings share a paved podium and
   the touch-merge chains them together. Rooms merge correctly (a chair's legs, seat and back are
   one chair); a town does not. That needs per-instance boxes from `townscape`'s own placement loop,
   which is a change to `garden.py`, and it is the next thing a person would notice.
3. **The tile has open edges.** Walk past 250 m and there is no ground. The tile has to follow the
   player, which is streaming and is not built. `drum_endcaps`' tile also has an **open axial edge**
   (`meta["open_axial_edge"]`) because it is clamped at `pz = 0`: past the aft cap there is no
   ground, and `interior.drum_end_cap`'s dish is not in the collision.
4. **A body can walk out onto the lake.** 6.4% of the drum lattice is `water_surface` and the
   collision follows the render exactly there. Correct behaviour for a collision module, wrong
   behaviour for a habitat.
5. **The player can walk up the wall of the barrel.** `player.gd`'s drum gravity is the radial
   direction at the body's own position with no speed condition, so a body walking circumferentially
   is pinned to the inside of the barrel at any speed. That is the existing controller, not
   something this module introduced, and the walk gate cannot see it because the body is genuinely
   on the floor the whole time.
6. **Not in CI.** `drum_walk.py --selftest` should run there; `deck.py --selftest` and `--sweep` are
   not there either.

### EXACT CHANGES I NEED APPLIED, in files I do not own

**(a) `station/walkable.py`** — route the drum to `drum_walk`. Two lines, at the top of
`walk_deck` (currently line ~158, immediately after the docstring, before `schema, profile = it.load()`):

```python
    # THE DRUM IS NOT A RING DECK. `deck.build_deck` raises on green/1 by name,
    # and the drum's floor is a heightfield rather than a corridor -- see
    # `station/drum_walk.py`.
    if (sector, ring) in D.NOT_RING_DECKS:
        import drum_walk as DW
        return DW.walk(key=goto_key or "the_garden", traverse=traverse,
                       timeout=timeout, godot=godot)
```

and in `main()`, where the verdict is taken (currently `good, why = deck_verdict(d)`):

```python
        if (sector, int(ring)) in D.NOT_RING_DECKS:
            import drum_walk as DW
            good, why = DW.walk_verdict(d)
        else:
            good, why = deck_verdict(d)
```

The negative-control block that follows must be skipped for the drum: there are no doors on it, so
`--no-doors` is not a control there. Guard it with the same `NOT_RING_DECKS` test.

`drum_walk.walk_verdict` imports `walkable`'s own `MIN_TRAVERSE_M`, `MAX_DECK_DROP_M` and
`MIN_WALK_M` rather than restating them, so the drum cannot be certified against an easier bar than
the corridor.

**(b) `station/deck.py`** — make `--sweep` count the drum instead of only deferring it. In `_sweep`,
replace the `continue` in the `NOT_RING_DECKS` branch with a call into `drum_walk`, so the
whole-station number includes it:

```python
        if (s, r) in NOT_RING_DECKS:
            import drum_walk as DW
            n = 0
            for row in DW.places():
                v, t, g, m = DW.build(key=row["key"])
                if DW.holes(v, t, m, n_a=8, n_z=8):
                    holes.append((s, r, dk))
                n += len(t)
            deferred.append((s, r, dk))
            print(f"     drum: {len(DW.places())} locations on collision "
                  f"ground, {n:,} triangles")
            continue
```

That is 12 tile builds and about a minute; if that is too slow for a sweep, build one tile and
report the union figure (105 of 280 patches, 215,040 triangles) instead.

**(c) `.github/workflows/validate.yml`** — add, next to the other self-tests:

```yaml
      - name: The habitat drum is walkable
        run: python3 station/drum_walk.py --selftest
```

`--full` adds the whole-drum slope sweep and costs ~70 s; the 23 checks without it cover the tile,
the derivation, the seams, the controls and all twelve locations.

### Anything I could not verify, stated bluntly

* **Framerate: nothing.** 51,200 triangles of trimesh collision per tile is 6.6x the corridor
  shell's 7,816 and there is no GPU here. `budget.py` has no gate for collision cost at all, on any
  deck, so this number is unbudgeted rather than under budget.
* **The walk is 126 m in a straight line from four spawns.** It is not a traversal of the drum, and
  no pathfinder or streaming exists, so "the drum is walkable" means "a body stands and walks
  anywhere within 250 m of one of twelve points".
* **No craft claim.** Every frame here is the flat-shaded rasteriser, which is honest about
  silhouette and geometry and says nothing about material, light or mood. The drum's engine frames
  and their scores are session 3t/3u's and are untouched.
* **`drum_ground.py --selftest` was not re-run** — nothing in it was modified, and it is already in
  CI at line 82.

## Agent report — AAA judgement

**Session 3w. Task #18, open for several sessions, now closed.** The WALKABLE station was
judged against `docs/AAA-STANDARD.md` through the ENGINE path — Godot 4.4 double + Mesa
lavapipe, `godot/scenes/interior.tscn`, 1280×720 — at the rubric's three distances, on four
subjects: the corridor from 1.7 m eye height, a doorway close up, a furnished room, and a
person at conversational range. **Fifteen frames, all committed under `docs/judge3w-*.png`.**
Full report with every number in **`docs/judge-3w.md`**; scores in `docs/aaa-scorecard.json`
under two new subsystems, `walkable_deck` and `npc_bodies`, both gate-clean.

Subject: `python3 station/deck.py --sector blue --ring 0 --deck 0` — 344° of corridor at
r = 211.55 m, six rooms with doors, 597,418 render triangles, 9,588 collision, 13 people.
Nothing under `station/` or `godot/` was edited to produce any of it.

| | craft | fidelity | performance | robustness |
|---|---|---|---|---|
| **`walkable_deck`** | **1** | **1** | **1** | **1** |
| **`npc_bodies`** | **1** | **2** | **0** | **2** |

### THE FINDING, and it is one line of code

**`station/deck.py:484` writes `G.append(("corridor", 0, len(ct)))` — all 458,400 corridor
triangles, 77% of the deck, as ONE anonymous group — and `interior_kit` had already recorded
14 material spans for them while building.** `interior.ring_arc` still holds those spans when
it returns (`interior_kit.tagged_spans(tris)` gives `deck_grid`, `wall_panel`,
`light_pilaster_strip`, `light_downlight`, `light_portal_head`, `skirt`, `dado`, `rail_band`,
`portal_frame`, `pilaster`, `soffit`, `ceiling_slab`, `wall_reveal`, `wall_assembly`); it just
does not return them. Two consequences, both measured, neither previously known:

1. **No material.** `interior.tscn`'s 429 substring rules match `corridor` zero times and the
   scene declares no `fallback_material`, so 458,400 triangles take the glTF default. The
   engine prints it on every run: `fallback material used by 15 group(s): corridor,
   doorleaf_…` — the corridor **and all twelve door leaves**.
2. **No light.** `export_scene.FIXTURE_LIGHTING` is an **exact-name** table. The corridor's
   822 `light_downlight` fittings are inside the blob, and `deck.py`'s `<key>__` room prefix
   breaks the rooms' names too. **The shipped deck emits 0 light sources. 850 are available
   from the geometry's own tags.**

| | frame | median | p5/p95 | vs `grey level 1.webp` |
|---|---|---|---|---|
| **as shipped** | `docs/judge3w-corridor-20m.png` | 0.3074 | **0.695** | **×5.77 — level test OUT OF RANGE, 4 of 6 distribution tests FAIL** |
| spans recovered | `docs/judge3w-corridor-20m-materials.png` | 0.0903 | 0.057 | ×1.68 — level OK, 5 of 6 pass |

*(the show's own corridor is 0.083)*. **99.5% of the pixels change**, mean |Δ| 75/255. Same
geometry, same camera, same exposure. Fixing this is `return kit.tagged_spans(tris)` from
`ring_arc` and using it in `build_deck`, and it is worth more than any other change available.

**And the playable scene is worse than that frame.** `godot/scripts/walk.gd` applies **no
material rules at all** and creates **no lights** — just `ambient_light_energy = 0.6`
(lines 182–190). The frames above at least bind the room materials through `interior.tscn`.

### Every person on the station is a black silhouette, and the cause is one binding

`interior.tscn` binds `npc_standing` and `npc_seated` to **`plant_valve_metal`** — albedo
0.545, **metallic 0.95** — in a scene with `reflected_light_source = 1`
(`REFLECTION_SOURCE_DISABLED`). At metallic 0.95 diffuse is scaled to ~5% and there is no
environment to reflect, so a person is black by construction. `docs/judge3w-person-2m.png`
at conversational range is **43.59% crushed**. The bodies underneath are better than that —
at 1 m the outline shows head, shoulders, coat, separate legs, and the Vree is a distinct
non-human form. None of it is visible.

### Four things nothing in this repository was measuring

* **Every doorway is an unclosed cut.** 1,572 boundary edges on the assembled deck; **1,470 in
  `corridor` and every one within 2 m of a door — 245 at each of six — with ZERO at the two
  arc ends**, which are correctly capped. Visible at 2.5 m as torn jambs and floating
  fragments (`docs/judge3w-door-2m5-shipped.png`). `--selftest` never counts an edge; `--sweep`
  counts floor holes by ray cast, which cannot see a hole in a wall. *(Checked and NOT wrong:
  point-in-volume returns 0 corridor triangles inside the closed-leaf box at all six doors —
  3v's leaf fix held.)*
* **`deck.py`, `collision.py`, `dressing.py` and `populace.py` do not run in CI at all**, and
  the walk step is `walkable.py --rooms 6`. **`--deck` never runs**, so the door negative
  control and the distance assertion are unguarded, and neither does `--sweep`. CLAUDE.md
  states as binding that this gate "runs in CI". It does not. *(Run by hand this session it
  PASSES — 6.3 m → 0.04 m, doors inert stops 5.26 m short — and generation is byte-identical
  across five `PYTHONHASHSEED` values. The work is real; nothing protects it.)*
* **`budget.py` prints PASS on a quantity that is not what ships.** It reports "visible
  structure set 30,941 / 60,000 (51.6%)" from the corridor kit in isolation. Measured in the
  frustum of the standing camera of `judge3w-corridor-20m.png`: **82,478 triangles — 137% of
  that allowance.** Ungated besides: 597,418 resident per deck, **188 draw calls with no
  interior draw-call budget in existence**, 97,590 triangles of furniture, 28,636 of people.
* **The rooms do not light themselves.** `interior.tscn`'s header argues a room lighting itself
  from nowhere is what the fixture rig exists to prevent. Turn ambient down to 0.05 and
  `docking_bays` is **black** (`docs/judge3w-room-6m-fittings-only.png`); adding all its
  fittings to a deck with zero lights moves **5.9% of the frame by 0.6/255**. Flat ambient is
  doing all the work, which is why no frame taken in a room has a shadow, a falloff or a
  direction.

### Content findings, ranked

1. **One corridor class on 66 of 66 decks.** `ring_arc` calls `corridor_section` with no `p=`,
   so the whole walkable station is the default **2.6 m × 3.0 m** residential passage.
   `interior_kit.CORRIDOR_CLASSES` defines `concourse` at **9.0 m** and `service` at 4.2 m,
   sourced in INV-840, and nothing ever asks for either.
2. **Signage: one group, 24 triangles, on the entire deck.** `grey level 1.webp` carries a
   placard, a lit sign and floor markings within 10 m of the camera. `signage.py` runs in CI
   and puts nothing on the walkable station.
3. **Nobody is in the corridor.** All 13 actors are in rooms behind closed doors; a player can
   walk 1,270 m of ring and never see a person.
4. **Repetition is indexable.** 138 identical kit sections / ~414 identical bays over 1,270 m,
   mirror-symmetric, one door per 210 m of walking.
5. **Blank at half distance.** At 1.12 m (`docs/judge3w-corridor-wall-1m.png`) the wall panels
   carry no bolt, seam, vent, wear or fixing; the joints are black lines; the downlight is a
   glowing white box. 2.5% of the corridor frames is *clipped* — battens and strips blow to
   white, `light_pilaster_strip` aliases into notched blocks, and the sight line gets
   **brighter** with distance from accumulated bloom.
6. **The door is the only usable thing on the station and it is blank** — no handle, control
   plate, release, chevron, name or number, and `doorleaf_*` matches no material rule.
7. **Prop collision has no stated tolerance.** `docking_bays`' 26,268 triangles / 2,189
   primitives of furniture become **15 AABBs up to 7.41 m across**, 209 m³ in a 655 m³ room.
   Deck-wide 8,175 primitives → 114 boxes. A player collides with air and walks through gaps.
8. **Six constants from the walkable layer are unlogged** — `ARC_PAD_DEG`, `Z_CLUSTER_M`,
   `deck_index`'s rule, the arc-phase sweep, `corridor_z_m`, the vestibule, `prop_boxes`'
   `min_m`/`gap`. `INVENTIONS.md` stops at INV-081.

### What is genuinely good, so it is not lost

With the spans recovered, `docs/judge3w-corridor-10m.png` is **the best interior frame this
project has produced**. Warm `light_downlight` against cool `light_pilaster_strip` is a
*measured* relationship and is the most Babylon-5 thing in the build; the deck plate, skirt,
dado, rail band, mullioned panels, cornice and serviced soffit all read — session 3s's
layer-2b work is real and it shows. The walk gate's negative control (fail if the doors-inert
run also passes) is the best piece of engineering in the subsystem. `--sweep` re-run: 66 of 67
decks assemble, 87 locations with a door, 0 floor holes, 75,642 collision triangles.

### Not judged, stated so silence is not read as a pass

Framerate, stutter and shader cost (no GPU). Whether the door *animation* reads —
`render_shot.gd` does not run `door.gd`, so every door in every frame is closed. Whether the
void over a door head is a hole or an unlit surface — that needs a two-background diff in a
scene file this agent does not own, and the 245 open edges per door supersede the question.
The habitat drum. And 31 of the 118 gazetteer locations, which are in secondary z-clusters
and cannot be walked to at all.

**One process finding:** `docs/aaa-scorecard.json` does not pass its own gate — 52 structural
errors, **every one in a round written before this session** (`severity: "resolved"` is not a
valid severity; evidence keyed by `frames`/`path`/`shader`; `what_is_good` is not a schema
key; dimensions below the bar with no finding). The two rounds added here are clean. The rest
are left as found, because editing past rounds to make a gate green is precisely the failure
that file exists to catch.

---

## Agent report — lighting the playable build

**Session 3w, one agent, scope: `godot/scripts/walk.gd`, `godot/scripts/dress_scene.gd`
(new), `godot/scenes/walk.tscn`, four PNGs under `docs/`, this section. Nothing under
`station/` or `tools/` was touched, and `player.gd`, `door.gd` and `npc.gd` were read but
not edited.**

### What was wrong

`docs/judge-3w.md` finding 5: `walk.tscn` is the only scene a player can stand in — it is
what `station/walkable.py` launches and what CI runs — and it **applied no material rules and
created no lights**. It loaded a `.glb`, gave it collision, stood a body on it, and lit the
whole thing with a hand-written `ambient_light_energy = 0.6`. Meanwhile `tools/export_scene.py`
carried 429 material rules and sixteen measured light fittings that were used **only to take
screenshots**. The playable build and the beautiful build were two different builds.

### What was built

`godot/scripts/dress_scene.gd`, called from `walk.gd::_dress_level()` immediately after the
`.glb` is added to the tree. **It contains no material table and no lighting table.** Both are
read from the definitions that already ship:

| what | where it is read from | how |
|---|---|---|
| 429 material rules | `godot/scenes/interior.tscn` (`station/materials.py --export` writes it) | the scene is `instantiate()`d and **never added to the tree**, so `render_shot.gd::_ready` never fires; its own `_material_for()` does the matching, so the table *and* the matcher are the shipping ones |
| the interior look | the same scene's `WorldEnvironment` | ACES, exposure 1.0, white 4.0, ambient **1.30** (`AMBIENT_CALIBRATED_ENERGY`), SSAO 0.6 m, low glow — mounted verbatim, replacing the hand-written 0.6 flat fill |
| 16 fitting measurements | `tools/export_scene.py::FIXTURE_LIGHTING` | **parsed out of the Python source** at load, together with `FIXTURE_MERGE_M`, `INTERIOR_LIGHT_RANGE_M`, `INTERIOR_SHADOW_LIGHTS`, `EXTENDED_SAMPLES_PER_RANGE`, `EXTENDED_SAMPLE_CAP` and the `--fixture-energy` argparse default |

Parsing Python from GDScript is a wart and it is deliberate. The alternative was retyping
sixteen *measured* fittings — colours, ranges, cone angles, shadow flags — into a second
table, which is correct on the day it is written and silently wrong afterwards. **The exact
change that removes the wart is written out below and needs a file this agent does not own.**

### The gate, run and reported

```
  PASS  deck blue/0/0  6 rooms over 344 deg, 6 doors; a body spawns in the corridor and
        WALKS INTO docking_bays (6.3 m -> 0.04 m), never leaving the floor, 5 of the room
        look up (123 deg turned, 4 deg off)
        control: with the doors inert the body is stopped 5.26 m short. The door is what
        opens the way.
        597,418 render triangles, 9,588 collision (1.6%)
```

Run three times: twice in a `git worktree` at HEAD (isolated, because a concurrent session
was rewriting `station/generated/scene/deck/*` mid-test and the first baseline run failed on
*its* half-finished `populace.py`), once in the working tree. `exit=0` every time. **Dressing
runs in the headless walk test too, on purpose** — a step that only ever runs in the
configuration nobody checks is a step that rots, and this file has that scar twice already.
Its summary lines appear in the CI log:

```
dress: 271/286 meshes MATERIALLED, 15 group(s) on the glTF fallback: deck_untagged, ...
dress: 850 light sources at energy 3.00 from { "light_highbay": 18, "light_downlight": 832 },
       2 casting shadows
dress: emissive-only (measured, not missing): light_pilaster_strip, light_portal_head, ...
```

### The frames, and the measured difference

Rendered through Godot 4.4 double + Mesa lavapipe under Xvfb at 1280x720, from the
**player's own camera** — `player.gd` already carries a Camera3D at `eye_height_m` = 1.7 m
parented to the body, so the eye is where the physics actually put a standing person, not
where a camera was told to go. The body is settled for 120 physics frames first; the log
records `eye 209.823,0.000,7121.305 (r=211.523, 0.045 m below spawn), on_floor=true`.
`--no-dress` is the control and produces the build exactly as it shipped before this change.

| frame | what |
|---|---|
| `docs/walk3w-sightline-before.png` | control, corridor sight line |
| `docs/walk3w-sightline-after.png` | dressed, same camera |
| `docs/walk3w-wall-before.png` | control, wall at 1.3 m — the rubric's half distance |
| `docs/walk3w-wall-after.png` | dressed, same camera |

`tools/measure_frame.py --against reference/07-sector-grey/grey level 1.webp`:

| | before (`--no-dress`) | after | the show |
|---|---|---|---|
| **sight line** median vs ref | **x3.61 — OUT OF RANGE** | **x1.68 — OK** (target x1.40 +/-25%) | 0.0533 |
| p5 / p95 | **1.000** | 0.056 | 0.083 |
| distribution tests passed | **1 of 6** | **5 of 6** | — |
| clipped / crushed | 0.00% / 0.02% | 2.52% / 1.53% | cap 3.69% / 0.22–63.92% |
| **wall at 1.3 m** median vs ref | **x3.61 — OUT OF RANGE** | **x1.12 — OK** | |
| p5 / p95 | **1.000** | 0.096 | 0.083 |
| distribution tests passed | **2 of 6** | **5 of 6** | — |

`p5/p95 = 1.000` is not a rounding: the control frame's 5th and 95th percentiles are the same
number. The whole 1280x720 frame contains **84 unique colours**; the dressed frame contains
**61,505**. 100.00% of pixels differ, mean |delta| 54.5/255, max 145/255.

**The playable build now measures the same as the best frame the screenshot path can produce.**
`docs/judge-3w.md`'s "groups recovered" row is x1.68, p5 x1.41 (band x1.29), 5 of 6 — this
frame is x1.68, p5 x1.39, 5 of 6. The one remaining failure is `p5` at x1.39 against a x1.29
band, i.e. **the shadows are 8% too bright**, and it is inherited rather than introduced:
CLAUDE.md already records the corridor anchor that defines 1.00 for the whole project as
sitting at p5 x1.64. Tuning it here would be a second exposure judged against nothing.

### The lamp positions were checked against the Python, not asserted

`export_scene.fixture_lights` needs the generator's `(name, lo, hi)` spans and a `.glb` has
lost them — `export_gltf.load_obj_groups` keys on the group NAME, so the deck's 832 corridor
downlights arrive as **one mesh of 9,984 triangles**. `dress_scene._fittings` recovers them by
single-linkage clustering at `FIXTURE_MERGE_M`, which is the same constant for the same
purpose. Verified against the Python by running `fixture_lights` on the same assembled deck:

```
Python  850 lamps: light_downlight 832, light_highbay 18
GDScript 850 lamps: light_downlight 832, light_highbay 18
worst position disagreement 0.32 mm; 0 lamps unmatched within 50 mm
```

Extended-fitting sampling is implemented but **never fires on a ring deck** and is therefore
untested against the Python: the widest body here is a 1.371 m high bay against a 12.5 m
range. It prints when it fires, because that means a fitting has changed shape.

### Two assertions that were made to fail before they were believed

* **the lighting parse.** Run from a project directory with no sibling `tools/`:
  `dress: FAILED -- no such file: .../tools/export_scene.py`, then `dress: 0 light sources`.
  The walk test still passes, which is the design — walkability must not depend on the look.
* **the material counter.** Its first version printed `271/286 meshes on a material rule` in a
  worktree where **every `[ext_resource]` in interior.tscn had resolved to null** and not one
  material existed. It counted rules matched, not materials applied. Now: with the import
  cache, `271/286 MATERIALLED`; without it, `169/286 MATERIALLED` plus
  `dress: 102 group(s) MATCHED A RULE THAT IS NULL`. Reproduced both ways.

### Findings in files this agent does not own — with the exact changes

1. **`godot/.godot/` is gitignored, so a fresh clone renders on the glTF fallback and says so
   only in a wall of parse errors.** `git worktree add` + `render_godot.sh` produced 40 lines
   of `Parse Error: [ext_resource] referenced non-existent resource` and then a perfectly
   valid PNG of the wrong thing. `cp -a godot/.godot <worktree>/godot/` fixes it. This is the
   same class as the `.tres` header check `render_godot.sh` already carries; suggest that
   script gain a check that `godot/.godot/` exists before rendering.

2. **`export_scene.fixture_lights` cannot see a room fitting on an assembled deck.**
   `deck.py` prefixes a room's groups with its place key (`f"{q['key']}__{n}"`), and
   `FIXTURE_LIGHTING` is an exact-name table, so `docking_bays__light_highbay` matches
   nothing. On blue/0/0 that is **18 of the 850 lamps, and all four rooms with high bays**.
   The corridor kit's unprefixed `light_downlight` is the only thing that matches today.
   *Exact change,* `tools/export_scene.py`, in `fixture_lights`' span loop:
   ```python
   -        if name not in FIXTURE_LIGHTING:
   +        # A ring deck prefixes a room's groups with its place key; deck.py
   +        # splits on the same separator itself (deck.py:702).
   +        name = name.split("__")[-1]
   +        if name not in FIXTURE_LIGHTING:
   ```

3. **`fixture_lights` aims every spot at world -Y, which is wrong on a ring.** `lt["aim"] =
   [0.0, -1.0, 0.0]` is right for one room in its own frame and wrong the moment the room is
   rotated into the ring: at ring angle 90 deg "down" is +Y, and a bay flood would fire along
   a wall. `dress_scene.gd` uses the radial direction, the same rule as `export_scene.radial_aim`.
   *Exact change,* same function:
   ```python
   -                    lt["aim"] = [0.0, -1.0, 0.0]
   +                    # Down is radially OUTWARD on a spun ring. Same rule as
   +                    # radial_aim(); [0,-1,0] is only right in a room's own frame.
   +                    r = math.hypot(c[0], c[1])
   +                    lt["aim"] = ([c[0] / r, c[1] / r, 0.0] if r > 1e-3
   +                                 else [0.0, -1.0, 0.0])
   ```

4. **The Python parse should not be necessary.** *Exact change,* `tools/export_scene.py`, in
   `main()`:
   ```python
   ap.add_argument("--dump-lighting", default="",
                   help="write FIXTURE_LIGHTING and the interior light "
                        "constants to JSON, so the runtime reads one "
                        "definition instead of re-typing it")
   ...
   if a.dump_lighting:
       json.dump({"fixtures": FIXTURE_LIGHTING,
                  "merge_m": FIXTURE_MERGE_M,
                  "range_m": INTERIOR_LIGHT_RANGE_M,
                  "shadow_n": INTERIOR_SHADOW_LIGHTS,
                  "samples_per_range": EXTENDED_SAMPLES_PER_RANGE,
                  "sample_cap": EXTENDED_SAMPLE_CAP,
                  "fixture_energy": a.fixture_energy},
                 open(a.dump_lighting, "w"), indent=1)
       return 0
   ```
   and one line in `station/walkable.py::walk_deck` to emit it beside the mesh. Then
   `dress_scene._read_lighting()` reads the JSON and `_py_block`/`_strip_comments`/`_py_number`
   delete. **Leave the parse in as the fallback** until the JSON is proven to exist in CI.

5. **15 of 198 deck groups have no material rule at all** (unchanged by this work, listed so
   it is not read as a regression): `deck_untagged`, `docking_bays__prop_bay_control_booth`,
   `docking_bays__prop_deck_marking`, and **all twelve `doorleaf_<room>_<n>`**. The door
   leaves are the ones that matter — they are the thing a player walks up to and touches, and
   they render as untextured glTF white. `station/materials.py` needs a rule for `doorleaf`
   (`kit_portal_frame` or a new leaf material) and `deck.py` needs to stop emitting
   `deck_untagged`.

6. **`walk.gd` creates all 850 lights at load with no streaming or distance cull.** It renders
   (26 s a frame on lavapipe against 13 s undressed) and the walk gate is unaffected, but
   Godot's `rendering/limits/cluster_builder/max_clustered_elements` defaults to **512** and
   this deck puts 850 lights in one scene. No dropped-light warning appeared in any log here,
   so it is not currently biting; it will on a deck with more rooms. This belongs with
   judge-3w finding 6 (nothing gates the deck) rather than with the look.

### Not verified, stated so silence is not read as a pass

* **Framerate.** No GPU. 26 s a frame on a CPU rasteriser says nothing about 1440p60, and the
  850 lights are the obvious suspect for the first real profiling pass.
* **Rendering anything but `blue/0/0`.** The other 65 ring decks were not rendered with
  dressing on. The **drum was walked** and passes — `drum_walk.py` launches the same
  `walk.tscn`, so it inherits the dressing, and
  `walkable.py --deck green/1/0` gives `PASS drum green/1/0 a body spawns on hedge at
  the_garden, walks 126.0 m over 25 ground patches and never leaves the floor`, exit 0. It was
  **not rendered**, and it should be before anyone trusts it: the drum has its own
  environment in `drum.tscn` that `dress_scene.gd` does **not** read, and mounting the
  *interior* environment — ambient 1.30, white point 4.0, SSAO at 0.6 m — inside a 556 m
  cavity with a sun-tube is almost certainly wrong. The right shape is for `dress_scene`
  to take the scene name to harvest from, `walk.gd` to pass `drum.tscn` when
  `gravity-mode=drum`; it is deliberately not guessed at here.
* **Whether the doors read.** `door.gd` runs, but the shot is taken from the spawn and no door
  is in frame.
* **The p5 debt.** Inherited from the corridor anchor and not re-derived here.

## Agent report — budget

**Session 3x. `station/budget.py` now measures the frame a player renders, and five of its
bounds are RED.** Judge-3w finding 6 ("nothing gates the deck") is closed. `budget.py` returns
1, so **the `Performance budgets` step in CI will go red on the next push** — that is the
intended outcome of the brief ("if the content is over budget, SAY SO and leave it failing"),
and every red line prints what would make it green. Nothing was tuned in either direction.

Files touched: **`station/budget.py`**, **`canon/INVENTIONS.md`** (INV-082..INV-085 appended),
this section. Nothing else.

### What it measures now

`blue/0/0` **assembled** by `deck.build_deck` — 6 rooms over 344 deg at r = 211.55 m, 597,418
render triangles, 286 groups, 9,588 collision triangles — with a real frustum swept over
**48 stations x 24 headings = 1,152 standing poses**, worst case gated. Camera: eye **1.70 m
above the collision floor**, **70 deg vertical / 102.4 deg horizontal at 16:9**, `near = 0.15`,
`far = 12000` — near, far and eye height are *read out of `godot/scripts/player.gd` at run time*
by `budget.shipped_camera()` so they cannot drift. Cost: **62 s** (13 s build, 26 s sweep, the
rest collision and the drum tile). `--no-deck` skips it and says so loudly; `--station` adds a
`deck.py --sweep` (+60 s); `--prove` feeds every new bound the regression it exists to catch.

### The numbers

| bound | measured | limit | | derivation |
|---|---|---|---|---|
| frustum **structure** | **99,716 tri** | 60,000 | **FAIL 166%** | the limit is UNCHANGED; only the measurement moved |
| structure share of frame | **8.3%** | 5% | **FAIL 166%** | same quantity, as a share of 1.2 M |
| frustum, **everything** | 155,018 tri | 300,000 | PASS 52% | the drum's own 25% frame share, as a ceiling |
| frustum draw calls | 139 | 1,041 | PASS 13% | CPU: 16.67 ms x 0.25 / 4 us (INV-084) |
| draw calls, whole frame | 325 | 1,041 | PASS 31% | 286 interior resident + 39 exterior |
| **resident triangles** | **597,418 tri** | 180,000 | **FAIL 332%** | this file's own three-cell resident budget |
| **shipped camera not wider** | **75 deg** | 70 deg | **FAIL** | `player.gd` sets no fov (INV-083) |
| **corridor shell tessellation** | **2.236x** | 1.000x | **FAIL 224%** | `MAX_SAG_M` vs `STEP_TOLERANCE_M` (INV-085) |
| drum tile stride | 1 | 1 | PASS | `collision_stride()`'s own derivation |
| station collision resident | 649,082 tri | 800,000 | PASS 81% | 130 MB at 200 B/tri, 1% of 16 GB |

`17/22 within budget` on a plain run; `18/23` with `--prove`.

### Seven things nothing was measuring

1. **The judge's 82,478 was one camera at 55 deg.** Swept at the budgeted 70 deg the worst
   standing pose is **155,018 triangles total, 99,716 of them structure**, at 324.8 deg looking
   back down the arc into two dressed rooms. The synthetic estimate this replaces read **30,941**
   — it was not conservative, it was **3.2x wrong**, and it printed 51.6%.
2. **`deck.py --sweep`'s headline collision figure omits the drum.** It prints *"75,642 collision
   triangles for the whole walkable station"* and sums ring decks only (`sum(x[4] for x in ok)`,
   and the drum takes the `continue` above it). The drum's ground at lod0 is **573,440
   triangles — 88% of the station's real total of 649,082.**
3. **The corridor collision shell is 2.24x finer than the project's own certified tolerance.**
   `MAX_SAG_M = 1 mm` sizes its angular step; `STEP_TOLERANCE_M = 5 mm` is what `floor_steps`
   certifies a floor against, and sag scales as the square of the step. 977 steps built, **437
   needed. 4,325 triangles a deck** bought at a tolerance five times tighter than anything asserts
   — while the props next to them are 114 axis-aligned boxes.
4. **`FRAME_TRIANGLES` contradicts the same file by 16.7x.** `BUDGETS`' comment derives the
   exterior's 400,000 as *"2% of frame budget"*, which implies a **20 M** frame; `FRAME_TRIANGLES`
   says **1.2 M**, against which that same 400,000 is **33%** of frame. `docs/AAA-STANDARD.md`
   quotes the 2% sentence approvingly, so it is wrong in two documents. **Neither number was
   changed** — everything is gated against the tighter one. INV-082. One frame capture on target
   settles it, and if 20 M is right, three of the five reds become passes.
5. **The group spans are not a partition.** On `blue/0/0` they cover **882,134 triangle-slots over
   597,418 triangles** (`wall_assembly` wraps `wall_panel`, `wall_reveal` and the mullions) and
   leave **1,248 triangles with no span at all**, which `deck.write_obj` emits as `deck_untagged`.
   Last-span-wins gives **286 distinct owning names = 286 draw calls**, not the 188 judge-3w
   recorded — that number predates 9da90c8, which gave the corridor its 14 material spans back.
6. **Looking up costs 1.61x.** Level gaze 155,018; **+45 deg pitch is 249,856 — 83% of the
   allowance** — because a ring corridor with no occlusion culling puts the far side of the ring
   in the frustum. `godot/` contains no `OccluderInstance3D` and no `use_occlusion_culling`.
   Pitch is printed in full and deliberately **not** gated: the remedy is a system, not content,
   and a content budget that fails for a missing system points at the wrong thing.
7. **Godot's `Camera3D` default is 75 deg and it is VERTICAL** — verified against the engine
   (Godot 4.4 double, headless, `Camera3D.new()` prints `fov=75.0 keep_aspect=1`,
   `KEEP_HEIGHT == 1`), not remembered. `player.gd` sets no fov, so **a player renders wider than
   this budget measures**: 161,792 triangles at the same pose, +6,774.

### What was REMOVED, so the removal is auditable

* **`visible_set_tris` as a synthetic estimate** — per-metre rate x sight line + two junctions.
  It read `30,941 / 60,000 (51.6%)`. Replaced by the frustum measurement above.
* **The `junction` bound** — it read `1,400 / 2,000 (70.0%)` and gated `interior_kit.junction`,
  which appears in **no walkable geometry anywhere**: `interior.ring_arc` sweeps a continuous arc
  with door apertures and never places a crossing. Only `interior_kit`'s own self-test builds one.
* Kept: **`corridor_tris_per_m`** (285/400), because `ring_arc` builds every walkable metre of the
  station from that exact call, so it is shipped geometry rather than a proxy for it.

### EXACT CHANGES I NEED APPLIED, in files I do not own

**(a) `godot/scripts/player.gd`** — one line, immediately after `_cam.near = 0.15` (~line 49):

```gdscript
	# 70 deg VERTICAL, 102.4 deg horizontal at 16:9. Godot's default is 75, which
	# is wider than station/budget.py measures -- INV-083. If this changes, the
	# budget's DECK["fov_v_deg"] changes with it, and `budget.py` fails until it does.
	_cam.fov = 70.0
```

That turns `shipped camera not wider` green. The alternative is to move
`DECK["fov_v_deg"]` to 75.0 and re-measure — the budget then rises to ~161,792 in the worst pose
and `frustum structure` gets worse, not better. Either is defensible; guessing is not.

**(b) `station/collision.py`** — `MAX_SAG_M = 0.001` -> `0.005`, and the comment updated:

```python
# How much a facet of the swept shell may sag inside the true cylinder. THE SAME
# TOLERANCE THE FLOOR IS CERTIFIED AGAINST -- `STEP_TOLERANCE_M` below -- because
# a shell tessellated finer than the gate that certifies it is triangles nobody
# can feel. At 1 mm this shell was 977 steps where 437 suffice, 2.24x
# (station/budget.py, INV-085).
MAX_SAG_M = STEP_TOLERANCE_M
```

(`STEP_TOLERANCE_M` has to move above it.) Corridor shell 7,824 -> ~3,500 triangles a deck.
**Re-run `collision.py --selftest` and `walkable.py --deck` afterwards** — `floor_steps` is
sampled at 240 points over 344 deg, which is coarser than either step count, so it should be
unchanged, but a collision change that is not re-walked is a collision change nobody checked.

**(c) `station/deck.py`** — `_sweep`'s headline line is wrong by 8.6x on the station total:

```python
    print(f"  {sum(x[4] for x in ok):,} collision triangles across the ring "
          f"decks, {sum(x[4] for x in drum):,} more in the drum's ground per "
          f"tile ({DW_LOD0:,} for the whole drum at lod0) -- the walkable "
          f"station is {sum(x[4] for x in ok) + DW_LOD0:,}")
```

where `DW_LOD0` is `dm["drum_lod0_triangles"]` off the tile it already builds. `budget.py` caches
the ring-deck figure as `RING_DECK_COLLISION_TRIS = 75_642` and `--station` rebuilds and fails on
any drift, so the two cannot silently diverge.

**(d) `.github/workflows/validate.yml`** — the `Performance budgets` step already runs
`python3 station/budget.py` and will now **fail**. It also now costs 62 s rather than 2 s. Leave
it failing until the content moves; if the build has to be green for an unrelated reason, the
honest lever is `--no-deck`, which prints a banner saying the only gate that measures what a
player renders was skipped. Do **not** raise a limit to clear it. Consider adding, separately:

```yaml
      - name: Whole-station collision total has not drifted
        run: python3 station/budget.py --station --no-deck
```

**(e) `station/interior.py` / `station/interior_kit.py`** — 1,248 triangles on `blue/0/0` are
inside `ring_arc`'s returned range and outside every span it returns, in **six gaps of 208, one
at each door**. They export as `deck_untagged`, match no material rule and take no light. This
is the same class of defect as judge-3w's headline and the last 0.2% of it.

### What I could not verify, stated bluntly

* **Framerate: nothing.** No GPU, no target hardware. Every number here is a proxy and
  `docs/AAA-STANDARD.md` says so first.
* **Three of the four new constants are declared, not measured.** `per_draw_us = 4.0` and
  `render_thread_share = 0.25` (INV-084) and `bytes_per_tri = 200` (INV-085) come from struct
  arithmetic and planning convention. The draw-call figure has a genuine independent cross-check
  — the break-even batch it implies, 4,800 triangles, lands within 30% of this file's own
  exterior ratio of 6,250 — and `bytes_per_tri` has none. One RSS reading and one frame capture
  on target close all three.
* **`FRAME_TRIANGLES` is inherited and self-contradicting.** See finding 4. Every interior
  percentage in this file rests on it.
* **One deck of sixty-six.** `blue/0/0` is measured because it is the deck judge-3w judged and
  the deck `walkable.py --deck` walks. The worst deck on the station may be worse; the sweep
  costs 62 s a deck, so measuring all 66 is an hour and was not done.
* **No occluders, no LOD, no streaming in the count, because there are none in the build.**
  Established by grep over `godot/` (`OccluderInstance3D`, `use_occlusion_culling`: no hits) and
  by `walk.gd` loading one `.glb` whole. If occlusion culling is added, every frustum number
  here falls and the gate should be re-derived, not re-tuned.
* **The frustum test is conservative and its error is measured, not assumed.** Sphere-bound
  sweep over-accepts **0.34%** against the exact per-vertex test at the same pose; the
  half-resolution lattice finds 147,416 against 155,552, so the **lattice's own sampling error is
  5.2%**. Both are printed every run.
* **A concurrent session was committing to this repository while these numbers were taken.**
  Everything above is at **9f13dbf**. An earlier build in the same session produced a different
  group set because `9f13dbf` (npc skin/hair groups) landed between two runs — that is not a
  determinism bug: three consecutive builds at 9f13dbf are md5-identical.
