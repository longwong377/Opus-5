# Before re-deriving `garden_bark` — read the statistic, not just its size

Written by a build agent in session 4r that was **blocked by a harness fault and produced no
work**. This is the one thing it got right, and it is worth more than the build would have been.

## The trap in the brief I was given

The brief said to re-derive `garden_bark` / `garden_foliage` because *"its own overturning
condition has been met"* — the entry's text says *"Overturned by: any near-field frame of a tree in
the drum, which would settle it in one measurement"*, and `docs/garden-4q-after-tree.png` now
exists. **That framing is right.** The evidence cited with it is where the care is needed.

The frame is cited as **crushed 25.49%** — the worst in the drum set. But `tools/measure_frame.py`
**censors at `FLOOR = 0.010`**, and `CLAUDE.md`'s own session-4l note records exactly this trap one
statistic over:

> at the old exposure that was **7.7% of the frame**, almost all lamp glow. The old row passed its
> level test on 7.7% of its own pixels, and the p95 'collapse' recorded earlier in 4l **was that
> population changing, not light**. Always read `measurable %` beside any statistic from this tool.

`crushed` is *precisely* the statistic that moves when the measurable population changes. And the
frame in question changed enormously for a reason that has nothing to do with the material: the
tree went from a lollipop to **1,244 triangles of trunk** with three orders of branching. More dark
silhouette against a dark drum raises `crushed` whether or not the bark value is wrong.

## Two readings, two different fixes, and only one belongs in `materials.py`

| reading | fix | whose file |
|---|---|---|
| the bark's value 0.135 is too dark to show a fluted section | re-derive the material | `materials.py` |
| the tree is correctly dark and the DRUM has no fill on it | a drum fill light / exposure | `drum_ground`, `export_scene.ROOM_EXPOSURE` |

**So read `measurable %` beside the 25.49% first.** If the measurable fraction collapsed between
the before and after frames, the crushed figure is reporting the tree's new silhouette area, not
the bark's response — and re-deriving the material would be tuning the wrong knob against a
statistic that moved for another reason.

The A/B that settles it is the one this project already knows how to run: change the material
alone, re-render the identical camera, and measure. If it comes back byte-identical, that is a
finding about the hypothesis — session 4e produced a nine-surface "unbound material" finding whose
fix rendered a byte-identical frame because the scene's `fallback_material` was already correct.

## The harness fault itself, recorded in case it recurs

Every tool call from all six workflow agents was rejected before execution:

```
The permission handler returned updatedInput for <TOOL> that failed schema validation:
The required parameter `<param>` is missing
... The tool input from the model was valid.
```

The `canUseTool` callback returned `updatedInput` with **every field stripped**, and the SDK
correctly rejected it. Fail-closed and total, which is the good kind — it cost tokens and produced
no false artefacts. **The dangerous variant to watch for is a partial strip**: a `Bash` whose
`command` survives but whose `timeout` is dropped, or a `Read` that loses only `offset`/`limit`,
would run and return plausible-looking wrong output. If a future agent reports odd truncations,
partial reads, or a gate that ran on the wrong slice of a file, suspect this handler before
suspecting their code.

The `Agent` tool was unaffected in the same session — six agents delivered through it — so the
fault is in the workflow runtime's spawn path, not in subagents generally.
