# Babylon 5 Station Simulation — Working Agreement

Read this first, every session. The owner is hands-off until ship; nobody else is checking
this work. The repository is the only memory that survives a context reset.

## What this is

A 1:1-scale, canon-accurate, real-time simulation of the Babylon 5 station. 8,047 m.
First and third person. Interior and exterior generated from **one** authoritative model so
they can never disagree. Flyable Starfury with seamless launch and dock. NPCs with names,
species, roles and schedules. Era lock: **Season 2–3**.

## The standard

The owner set it explicitly in session 2y: *"utterly perfect, visually beautiful, with every
single thing done at AAA quality — from textures to physics to detail to the npcs to the
crowdedness/isolation to the mood to the ambiance to the alienness to the sound to the scale to
the interactability to the accuracy vs the real thing. This is your magnus opus."*

That is a feeling, and a feeling cannot be reviewed by an agent. `docs/AAA-STANDARD.md` turns it
into four scored dimensions with written descriptors — **craft, fidelity, performance,
robustness** — and defines the bar. Nothing is "done" because it was built; it is done when it
clears the bar and stops regressing.

## Current phase

**Structure first, where structure carries structure.** Geometry that other geometry depends on
is built and made correct before anything is dressed. Polishing a surface that later moves is
waste, and this project has paid that bill: the drum end cap was "done" for four sessions and
was 4,064 open edges.

That rule binds *dependencies*, not the calendar. The interfaces are now settled enough that
materials, lighting, audio and NPC work run in parallel with the remaining structure.

### The plan, in order

| Phase | What | Done when |
|---|---|---|
| **A. See** | The rubric, the Godot/lavapipe PBR render path, the material and lighting systems | A frame can be rendered that is worth judging, and there is a written bar to judge it against |
| **B. Complete the shell** | Crude exterior components, metric `HULL_ALLOWANCE`, cell junctions and doors, the docking bay, the Starfury cockpit | Every volume a player can reach exists and is watertight |
| **C. Dress it** | Textures, decals, signage, wear, greebling at close range, per-sector identity | Each subsystem clears the bar |
| **D. Life** | NPCs at population scale, crowd density and isolation, schedules, species behaviour, audio and ambience | The station feels inhabited, and empty where it should be |
| **E. Play** | First and third person, flight, seamless launch and dock, doors, interaction | Hours can be lost in it |
| **F. Ship** | Integration, performance on target hardware, the owner's first look | — |

Phases overlap where they do not depend on each other. A is a hard prerequisite for C, D and E,
because none of those can be *judged* without it.

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

1. **Nothing is built from memory.** Every dimension, layout and name traces to
   `canon/00-MASTER.md`. If it is not sourced there, it does not get modelled.
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

   **Cap: ~10–14 agents per workflow, one workflow per increment.** Raised from ~5 by the owner
   in session 2y, together with the AAA standard. The multiplication that gets expensive is
   *many workflows at once across a repeating trigger*, not the width of a single fan-out — so
   run one wide workflow and wait for it, rather than three narrow ones in parallel.

   Keep the adversarial verify pattern. It has now caught a door interpenetrating a portal
   frame, a greeble signature mismatch, tram cars passing 6.43 m through a structural spoke, an
   end cap with 4,064 open edges, and two assertions that could not fail. It is the single
   highest-yield thing in this project's process.
4. **Never spawn a workflow from inside a triggered firing** unless the work genuinely needs
   it. The trigger already repeats; the multiplication is what gets expensive.
5. **Blocked is a valid outcome.** C-003 and C-004 gate all interior layout. Reporting "still
   blocked, here is what would unblock it" is the correct result, not a failure to try hard
   enough.

## Git

Branch: `claude/babylon5-station-sim-discussion-kgp4by`. Commit at every meaningful step;
push with `git push -u origin <branch>`. Do not open a PR unless asked.
