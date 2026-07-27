# Canon Conflicts

Reference disagreements. Each carries a ruling or is marked open. Open conflicts touching
geometry **block** the affected build work — they are not resolved by picking whichever is
convenient at the time.

---

## C-001 — Overall station length · **RESOLVED**

| Source | Claim | Authority |
|---|---|---|
| S1 opening narration | "a self-contained world **five miles** long" | 1 |
| `other map 2.jpg` | 5 miles (8.047 km) | 4 |
| Contract 5 schematic | Scale bar 0–8 km, station spans it | 3 |
| `other map 4.jpg` (Miller) | **3,108 m** | 4 |

**Ruling: 8,047 m.** Three sources including on-screen dialogue agree; Miller is the sole
dissenter at the lowest authority level. Miller's *proportions* are internally consistent and
far more detailed than any other source, so they are retained and rescaled by k = 2.5891.

Same ruling applies to mass: show canon **2,500,000 tons** over Miller's 246,000 tonnes.
Note that Miller's mass rescaled by k³ gives 4.29 M tonnes — same order as show canon, which
is a mild independent check that his proportions are sane even though his absolute scale is not.

---

## C-002 — Cobra bay count · **OPEN**

| Source | Claim | Authority |
|---|---|---|
| Contract 5 schematic | "COBRA BAYS (28)" | 3 |
| `other map 4.jpg` | "Cobra-Bay Fighter Storage ... 24" | 4 |

Plausibly not a contradiction: 28 physical bays with 24 fighters stored, or two squadrons of
12 plus spares. `other map 2.jpg` states "two Starfury fighter squadrons", and an EarthForce
squadron is conventionally 12 craft → 24 fighters. That reading reconciles both.

**Provisional: 28 bays, 24 fighters.** Needs a frame count from exterior footage to confirm.
Non-blocking — bay count affects hull detail, not layout.

---

## C-003 — Sector arrangement · **OPEN, BLOCKING**

| Source | Model | Authority |
|---|---|---|
| `other map 2.jpg` | **Longitudinal slices**, aft→fore: Grey, Brown, Green, Red, Yellow, Blue | 4 |
| `Interior map.jpg` | **Nested radial layers** — Yellow as outer utility skin + core shuttle axis, Red as outer ring, Green inboard, Brown as a full-diameter block, Blue forward | 4 |

Both are authority 4 and they describe fundamentally different topologies. This is not a
detail — it determines whether a sector is a length of the station or a depth within it, and
therefore what "walking from Red to Green" physically means.

The two may be partially reconcilable: sectors could occupy longitudinal ranges *and* have
characteristic radial depths, with `Interior map.jpg` being a functional-zoning diagram rather
than a spatial one. Its yellow tracing both the outer skin and the centreline supports this —
the centreline yellow is the **core shuttle**, not Yellow Sector.

**Provisionally adopting the longitudinal model** because hull geometry must be built first
and only the longitudinal model constrains it. Revisit before any interior layout work.

**Resolution needs:** on-screen wayfinding signage, or a lift/transit display showing sector
adjacency, or dialogue establishing travel time between sectors.

---

## C-004 — Level numbering · **OPEN, BLOCKING**

On-screen addresses are `<Colour> <number>`: Grey 17, Red 3, Blue 12, Brown 2, Green 2.
What the number indexes is unestablished.

- **Radial decks** — level 1 outermost at full gravity, numbering inward toward the axis.
  Physically natural: in a spin-gravity cylinder "down" *is* outward.
- **Longitudinal slices** — levels as stations along the station's length.

Against the radial reading: *Downbelow* is described as the lower levels of Brown Sector,
which under radial numbering would place it against the outer hull — an odd home for disused
interior space, though not impossible (outer hull = furthest from the core shuttle = least
accessible = most neglected, which actually argues *for* it).

**Blocking all interior level geometry.** Resolution needs a lift display, a deck plan, or
dialogue tying a level number to a gravity or a location we can place radially.

---

## C-005 — Contract 5 schematic internal scale · **RESOLVED, SOURCE DEGRADED**

Measured tick positions on the Contract 5 scale bar (numeral centres, px):

```
0=32  1=161  2=287  3=415  [4 hidden behind fin assembly]  5=626  6=751  7=876  8=1003
```

Spacings: left group 0→3 averages **127.7 px/km**; right group 5→8 averages **125.7 px/km**
(consistent within 1.6%). But 3→5 spans 211 px = **105.5 px/km**, a 17% compression.

The reproduction is spliced or non-uniformly scaled across the middle. **This sheet cannot be
used for precise dimensional extraction.** It remains authoritative for *topology* — what
components exist, their order, their counts, and the North/South convention — all of which
survive a horizontal squeeze.

---

## C-006 — Miller's drawing disagrees with Miller's own table · **RESOLVED**

Measured off `other map 4.jpg` at 3× against a calibrated 50 m grid, in Miller-metres:

| Section | Table states | Drawing reads | Agreement |
|---|---|---|---|
| Red Section length | 172 m | ~166 m | **3.5%** — good |
| Green Section outer length | 1058 m | ~1058 m as the whole rotating assembly (1200→2258) | good |
| Bio-habitat cylinder alone | 1058 m | **~467 m** | **poor** |

The habitat *cylinder* as drawn is less than half the length the table gives for the
bio-habitat. The reconciliation: the table's 1058 m describes the **entire rotating assembly**
— wide aft hull block, bearing neck and habitat cylinder together — not the visibly cylindrical
portion alone. Green Section outer length and bio-habitat interior length being *the same
number* in the table supports this: they are one envelope measured once.

**Ruling: the table wins on dimensions, the drawing wins on ordering and identity.** The
schema records both under `table_*` and `drawn_*` so the distinction survives. Drawing-derived
z-positions carry ±75 m real uncertainty and must not be treated as precise.

Red Section is the one place where an independent table figure and an independent drawing
measurement agree closely. That agreement is the main evidence that the k = 2.5891 rescale and
the 0.6361 px/m calibration are both sound.

---

## C-007 — Radiator arrangement · **RESOLVED, corrects an earlier build**

`Exterior map.jpg` states "Reactor Cooling Fins (12)" and gives no arrangement. I built them
as 12 plates arrayed around the axis. **That was wrong.**

`reference/01-station-exterior/exterior more.jpg` is an orthographic sheet showing top view,
side view and two end views of the production model. It settles the arrangement directly:
the radiators appear **edge-on as thin lines in the top view and full-face as tall blades in
the side view** — which is only possible if they are **coplanar**, not radially arrayed.
Three blades above the spine, three below.

**Ruling: 6 coplanar blades, authority 2 (production material), overriding my radial-array
reading of the authority-3 count.** The count of 12 in the Exterior map most likely counts
radiating faces (6 blades × 2 sides) or panels per blade; it is not a count of radial positions.

Coplanar is also the physically correct arrangement — blades in a single plane never radiate
into each other, which is exactly what a radial array of 12 on a thin spine would do.

Implemented as the `planar_blades` component kind. Blade pitch must stay well above chord
length or the blades merge visually; at 6 blades over 730 m the pitch is 243 m, so chord is
held at 150 m.

**Lesson for the rest of the build:** a bare count in a labelled diagram does not imply an
arrangement. Where an orthographic sheet exists, it outranks inference from a count.
