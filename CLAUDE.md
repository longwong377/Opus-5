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
| **W2** | **Go somewhere** | Two named locations joined by real walkable geometry; the player walks between them without leaving the floor | **HALF** — 126 m of ring corridor walked, `offfloor=0/1800`; **no door into any room** |
| **W3** | **A furnished room** | ONE location at true prop density -- the reference is the owner's Starfield frames, not our own past work -- with a stated props/m2 | `dressing.py` built (3u) |
| **W4** | **A populated room** | NPCs standing, sitting and walking in it. `station/npc/` already has twelve tested modules with zero importers; wire them | `populace.py` built (3u) |
| **W5** | **The loop** | Spawn -> walk -> use something -> an NPC reacts. The smallest complete experience | |
| **W6+** | **Breadth** | Roll W3-W5 outward by generator across the 118, in the order a player meets them | |

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
| **2b** | **Geometry — articulation** | Visible line density at or above its floor, derived from budget / Nyquist / the show's own frames — `station/density.py`, INV-070. **This is the layer the register now reports** | **16 / 118 — CURRENT** |
| **3** | **Materials** | Every mesh carries PBR materials from `materials.py`. No flat colour anywhere | **16 / 118** — materials are done on all 118, but a place cannot be at layer 3 while it fails 2b |
| **4a** | **Lighting — level** | Every location has a rig and a measured exposure, median-matched to its reference | **16 / 118** — done on all 118, gated behind 2b for the same reason |
| **4b** | **Lighting — mood** | Every location matches its reference's *distribution*, not just its median — p5, p95, crushed, clipped | **1 / 17 measurable — see below** |
| **5** | **Props & function** | The declared interactable types exist and do what `directory.py` says they do | 0 |
| **6** | **Inhabitants** | NPCs placed, scheduled and animated in every location, at real density | 0 |
| **7** | **Audio** | Ambience and event audio per location | 0 |
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

**The result: 17 of 17 exposures pass the median test. 1 of 17 passes the distribution test.**
`p5` is the discriminator and fails 13 of 17, bright on 11 — **including the corridor anchor that
defines 1.00 for the entire project** (p5 x1.64). Two rooms fail the opposite way, crushing far
*more* than their references (`quarters` x38.1, `alien_sector` x29.5).

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
is real. 4b is the bar that was missing, and it is 1/17 on the frames that exist.

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

   **ASK THE OWNER BEFORE STARTING ANY AGENT.** Set in session 3q and standing. Not "ask before
   a big fan-out" — ask before setting any of them in motion, and propose the pairing so it can
   be chosen.

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
