# Working on this project

For an agent picking this up cold. Read `CLAUDE.md` first — this is the operational companion
to it.

## The loop

```bash
# 1. Edit the schema, never the geometry
$EDITOR station/schema/station.yaml

# 2. Regenerate and gate
cd station && python3 generate_hull.py && cd ..
python3 station/validate.py      # 20 canon assertions
python3 station/budget.py        #  4 performance budgets

# 3. Look at it. This is not optional.
python3 tools/preview_render.py station/generated/hull.obj \
  --out /tmp/look.png --eye 0 -5000 4023 --target 0 0 4023 \
  --width 1700 --height 620 --fov 38
# then Read /tmp/look.png

# 4. Physics, if touched
for t in station/physics/test_*.py; do python3 "$t" | tail -1; done

# 5. Full engine render, when material or lighting matters (minutes, not seconds)
bash tools/build_and_render.sh
# then Read renders/engine_view.png
```

## What has gone wrong before

Every one of these cost real time and every one was caught by *looking at the output* rather
than by reading the code. That is the argument for step 3.

| Symptom | Cause |
|---|---|
| Radius of 763 m in the narrow reactor spine | The extractor was reading an inset **photograph** on the schematic as if it were hull |
| Hull trace wandering off into the label row | It was following **label leader lines**. Outlier rejection cannot fix this — across wide stretches the leaders outnumber the hull and *become* the local median. A horizontal run-length filter separates them |
| Visible rings on the habitat drum | Radius profile flipped gradient sign on 20% of samples. A plain low-pass would have fixed it *and destroyed the real section transitions* — smoothing has to detect step edges first |
| Communications pylons invisible | Placed on the North/South axis, which is edge-on to a side view *and* where docking traffic approaches from |
| Radiators as a shuttlecock | Built 12 arrayed around the axis from a bare count of "12". The orthographic sheet shows them **coplanar**, 3 up and 3 below |
| LOD popping | Switch distances sized against facet *width*. What causes a pop on a body of revolution is the **sagitta**, `r(1-cos(π/n))` — 92 m for an 8-gon at r=1211 |
| Mangled corridor deck | Axis remapping done with inline tuple comprehensions, which silently transposed the wrong pair |
| Nearly modelled from the wrong show | Eight reference frames are from the **2023 animated film**. They are the *highest resolution* files in the set. **Resolution is not authority** |

## Rules that are not negotiable

1. **Nothing from memory.** Every dimension traces to `canon/00-MASTER.md`.
2. **Log every invention** in `canon/INVENTIONS.md` — what, why, what constrained it, what
   would overturn it. INV-003 was overturned by geometry it produced; that is the system working.
3. **BLOCKING conflicts block.** `canon/CONFLICTS.md`. C-003 and C-004 currently stop all
   interior *layout*. Interior *pieces* are fine — that distinction is why the kit exists.
4. **Never hand-author geometry that duplicates the schema.** Inside and outside are consistent
   by construction or not at all.
5. **Provisional numbers go in a `PROVISIONAL` dict**, never inline. Resolving a conflict should
   change one table, not a hundred call sites.
6. **Update `STATE.md` before finishing.** It is the only handoff.

## Layout

```
canon/        Sourced facts, conflicts, invention log
reference/    Show material. 21-QUARANTINE-animated-film/ is NOT show material
docs/         ADRs, specs, this
station/      Schema, generators, physics, validation
  physics/    Rotating frame, precision, Starfury, docking, core shuttle -- 86 tests
godot/        Engine project. Materials belong here, not in the glTF export
tools/        Analysis, rendering, build
```
