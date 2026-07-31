# The machinery was a box, and no gate could say so

Twelve pairs of engine frames — Godot 4.4 double + Mesa lavapipe, `tools/render_godot.sh
--shot interior` — at **identical cameras before and after**, so the only variable is the mesh.
Four rooms from four archetypes; three distances each.

The cameras are frozen literals derived from the PRE-change geometry, so the after frame cannot
have been framed to flatter itself.

| distance | what it is | why |
|---|---|---|
| `normal` | a body standing on the walkable grid at the near end of the bay, looking at the fixture — 5.6 to 10.6 m | the distance a player sees it from, because it is a distance a player can stand at |
| `half` | the same sight line, halved — 2.8 to 5.5 m | `CLAUDE.md`: *"Every craft claim cites a frame at the rubric's HALF distance, not the normal one."* |
| `arm` | 1.0 m clear of the object's own bounding box, same bearing | indoors the one-pixel-of-silhouette distance is kilometres away and outside the room. `docs/AAA-STANDARD.md`'s geometry checklist asks for the silhouette *"at one pixel, at normal distance, and at arm's length"*; arm's length is the third reading a room can actually give |

## What the pairs show

| room | archetype | before | after |
|---|---|---|---|
| `fabrication` | industrial | two black boxes 2.4 × 2.4 × 4.6 m on the centreline | furnace stacks on standoff legs: charge doors with lifting frames, flues through the ceiling, hazard bands at the foot, pipe stubs, a full-height clad column with a ladder |
| `reactor_hall` | industrial (plant) | a flat grey rectangular pier 4 m across | a clad barrel: girth flanges, lagging strakes, a bolted manway with its cover and bolt circle, a ladder, an access platform bracket, gauges |
| `medlab_one` | medical | a 2.3 m pale slab, and a bigger pale slab of furniture behind it | a column gantry on a base plate with joint collars, a swung arm, a lit head, a control pad; the casework behind it has corner posts, a capping course and a plinth |
| `business_center` | commerce | a solid black column | a stall frame: posts, head and foot rails, infill panels and a glazed upper light |

## The honest reading

**CRAFT 3.** The lowest descriptor that is fully true. It reads as the intended object at its
normal distance *and* at half of it — which is the improvement — and `after-fabrication-arm.png`
is where it stops: the furnace charge door at 1.0 m is a flat orange plate with no bolt pattern,
no wear and no scale, and `after-reactor_hall-arm.png` is a plain plate between two flange lines.
C3's second clause is what caps it: *"The tertiary tier is generic … Materials exist as groups
but carry one flat value each."* C4 wants wear, grime and lighting response varying across the
surface, and that is a layer-3 property this pass did not touch.

## The measurement behind it

`python3 station/density.py --machinery` — visible line density on the FIXTURE AND PROP geometry
alone, against the same room's own shell as the floor. Nothing is chosen: the bar is whatever
that room's architecture already carries, so a coarse hall gets a coarse bar.

|  | before | after |
|---|---|---|
| locations at or above their own shell | **0 / 78** | **74 / 78** |
| machinery line density, median | 1.669 m⁻¹ | **7.012 m⁻¹** |
| machinery / shell ratio, median | 0.31 | **1.29** |
| effective distinct normals, median | 5.70 (**a box reads ~6**) | 6.55 |
| machinery triangles, all 78 rooms | 6,156 | 192,680 |

The whole-room gate — `python3 station/density.py`, layer 2b — read **123 / 128 before and
123 / 128 after**, because it was already passing on rooms whose every machine was a box. That
is the finding, not a footnote: the shell is 95%+ of a room's surface, so a machine at a sixth of
the shell's line density moves the room average by less than the gate's own margin.
`%show`, the fraction of what a Babylon 5 set carries, went from a median of 27.3% to **29.0%**
and a maximum of 50.0% to **65.0%**.
