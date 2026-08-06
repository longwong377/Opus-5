# Session 4r — patches for files the C&C craft agent does not own

Owned and edited: `station/command_control.py`, `canon/INVENTIONS.md` (INV-620…623),
`docs/craft-4r-cnc-r*.png`, `docs/engine-cnc.png` (re-taken from its own recorded
`--gate-frames` command — see §1), `scratchpad/craft-4r-command_control.json`.

Everything below is a change to a file this agent does not own, ordered by how much it
matters. Every number here was measured this session.

---

## 0. `docs/aaa-scorecard.json` — merge two rounds

`scratchpad/craft-4r-command_control.json` holds rounds 2 and 3 for `command_control`, in
the shape the scorecard's existing rounds use. **Round 2 carries a `regression_waiver`**
(robustness 2 → 1) and the reason is written into it: the module went from 0 assertions to
65 in the same period, and the score falls because round 2 looked for enclosure and round 1
did not. `tools/aaa_gate.py` will reject the round without that field.

Neither round should advance the clean-round counter — same author as the build, which
`docs/AAA-STANDARD.md` excludes explicitly.

---

## 1. `docs/engine-cnc.png` was re-taken, and `--gate-frames` should be re-run

I changed this room's light rig (INV-621, the pit soffit), which makes the committed
layer-4 frame stale — the exact defect `CLAUDE.md` records as *eleven of the fourteen
distribution failures were stale frames*. So it was re-taken with
`export_scene.rerender_frame`'s own command, verbatim:

```
tools/render_godot.sh --shot interior --room cnc --res 640x360 --out docs/engine-cnc.png
```

Measured against its reference by `tools/measure_frame.py --against`, before and after:

| | before | after | band |
|---|---|---|---|
| median vs show | ×1.06 | **×1.72** | ×1.40 ±25% → 1.05–1.75 **OK, near the top** |
| p5 | ×1.06 | ×1.19 | ×1.29 |
| p95 | ×0.93 | ×1.27 | ×3.27 |
| p99 | ×0.69 | **×1.03** | ×2.58 |
| p5/p95 | ×1.14 | **×0.94** | ×3.38 |
| crushed | 32.07% | **11.05%** | 0.22–63.92% |
| clipped | 0.08% | 0.09% | ≤3.69% |
| **measurable** | **67.9%** | **88.9%** | — |

Distribution passes 7/7 both ways and four of the seven statistics move *toward* the show.
The level test now sits at the top of its band rather than the bottom. **Read the
`measurable %` beside it**: a fifth of the frame was under the 0.010 floor before and is
not now, so part of the median move is its population changing, which is this project's own
recorded trap with this tool.

**No other row was touched** and `--gate-frames` was not run — it is minutes of CPU and
other agents were working. It should be run before the next release gate.

**If somebody wants the level nearer ×1.40** the lever is
`tools/export_scene.py::BESPOKE_EXPOSURE["command_control"]`, currently **4.08**. ×1.40 /
×1.72 = 0.814, so **3.32** is the arithmetic — but this file's own notes say that
derivation is invalid (`d(ln median)/d(ln gain)` ranges 0.97 to 0.01 over the corpus), so
it needs a render either side rather than a division. I did not change it because the row
passes.

---

## 2. `station/materials.py` — the console binds the plant kit and renders as furniture

**The single largest remaining craft finding on this room, and it is a material one.**
`docs/craft-4r-cnc-r3-console-arm.png` at 1.3 m: the console's legs, valance, apron, side
cheeks, bed banks and key rows all bind `dressing._Parts`' nine plant-kit surfaces
(`plant_valve_metal`, `steel_gantry_oxide`, `plant_switchgear`, …) because those are the
only bound machine surfaces available. They render **tan and brown**. C&C's palette is
cool blue-white and its principal object is wood-coloured; the leg frame reads as a
trestle.

`station/command_control.py` says so itself, twice, in comments that predate this session:
*"none of them is new, because `station/materials.py` is not this module's to edit"*.

What would close it is a **console family** — four entries, and they are the same four
every bespoke room with a control surface will want:

* `console_carcass` — dark cool grey, roughness ~0.45, the pedestal and legs;
* `console_bezel` — near-black, low roughness, the surround a cell is set into;
* `console_key` — mid grey with a slight sheen, the unlit key rows;
* `indicator_green` — a **saturated** green emissive. The module's own comment names this
  gap: the reference's green is saturated and `device_screen_glass` is a green-WHITE, and
  the only saturated alternative in the library is `alien_status_lamp` at six times the
  energy and under a name that would be a lie in C&C.

Until those exist this subsystem cannot pass C4's *"materials … vary across the surface
rather than being uniform"*, and the finding is logged as `major C3` in round 3.

---

## 3. `station/vista.py` — what the window looks out at is a grey card

Recorded rather than actioned, and it is the largest remaining item in the half-distance
frame after §2. In `docs/craft-4r-cnc-r3-half.png` the glass shows a **flat pale-grey field
with no legible hull structure** — no plating, no shape, nothing that says "the station".
The manifest reports `station_frac 0.740` against the show's `0.852`, so the lower quarter
of the aperture is empty starfield, which reads as a bite taken out of the window.

The room's own side is now done: the frame in front of that view is lit (§ INV-621) and
measures ×0.341 frame/glass against ×0.104. Anything further is on the other side of the
glass.

---

## 4. `scratchpad/PATCHES-4r-windows.md` §6 — NOT applied, and it still stands

That patch turns C&C to face aft (`station_frac` 0.000 as built, 0.740 half-turned) and it
**moves the room's door**, so it belongs with whoever runs `deck.py --degeneracy` and
`walkable.py` after it. Nothing in this session's work conflicts with it: `side_wall` is
symmetric about x and the pit soffit is symmetric about x, so the half-turn `(x, y, z) →
(−x, y, −z)` leaves both unchanged.

---

## 5. `.github/workflows/validate.yml` — the enclosure gate is free and is not in CI

`python3 station/command_control.py` now runs the enclosure gate as part of its own
self-test (72/72, ~40 s, no engine, no GPU). If the module is not already a CI step it
should be one. The general form of the gate — project the mesh down each axis and count
cross-section cells covered by no triangle — is **cheap enough to run on every bespoke
module** and is the only test in this repository that can fail for "this room has no
walls". `station/command_control.py::enclosure_gaps` takes `(verts, tris, axis, bounds,
cell, inside)` and nothing else, so lifting it into `station/interior_kit.py` and calling
it from the other twenty-two bespoke modules is a small change with a large blast radius.
**I did not do it because `interior_kit.py` is not mine and because it should be run on all
of them at once by somebody who can watch what it finds.**
