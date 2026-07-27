# Babylon 5 Station Simulation — Working Agreement

Read this first, every session. The owner is hands-off until ship; nobody else is checking
this work. The repository is the only memory that survives a context reset.

## What this is

A 1:1-scale, canon-accurate, real-time simulation of the Babylon 5 station. 8,047 m.
First and third person. Interior and exterior generated from **one** authoritative model so
they can never disagree. Flyable Starfury with seamless launch and dock. NPCs with names,
species, roles and schedules. Era lock: **Season 2–3**.

## Current phase

**Structure first.** The complete station — inside and out, all levels, seamless and correct —
is designed and built before any content fill. Detail, NPCs, audio and life come after the
shell is right. Do not start filling rooms while the shell is provisional.

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

This project runs partly on an hourly trigger and on background workflows, so an unbounded
session compounds. Bounds, in order of importance:

1. **Stop when the next-session list is empty.** If `STATE.md` has no actionable item — because
   everything remaining is blocked by `canon/CONFLICTS.md` — then say so and stop. Do not
   invent work to fill the time. An hourly trigger finding nothing to do should cost almost
   nothing.
2. **One coherent increment per firing.** Build the next thing, test it, look at it, commit,
   update `STATE.md`, stop. Do not chain five subsystems because there is context left.
3. **Workflows are for genuine fan-out**, not for work one agent can do serially. A workflow
   costs roughly its agent count times a normal turn. Five agents to build five independent
   subsystems is worth it; five agents to write one file is not.
4. **Never spawn a workflow from inside a triggered firing** unless the work genuinely needs
   it. The trigger already repeats; the multiplication is what gets expensive.
5. **Blocked is a valid outcome.** C-003 and C-004 gate all interior layout. Reporting "still
   blocked, here is what would unblock it" is the correct result, not a failure to try hard
   enough.

## Git

Branch: `claude/babylon5-station-sim-discussion-kgp4by`. Commit at every meaningful step;
push with `git push -u origin <branch>`. Do not open a PR unless asked.
