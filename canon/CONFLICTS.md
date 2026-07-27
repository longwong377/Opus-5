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

### Session 2q note — a possible origin for the 24, and a caution

The Security Manual sectional schematic
(`reference/02-station-cutaways-and-plans/b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp`,
authority 3) carries the callout **"DOCKING BAYS (24)"** in the Blue Sector, alongside
**"BAY ELEVATORS (2)"** and "LOW-G DOCKING BAYS".

**These are the large docking bays of the forward docking structure, not cobra bays**, and
this does *not* resolve C-002. It is recorded for two reasons:

1. It is a new sourced count for a system `00-MASTER.md` did not have one for, and it
   cross-checks against authority-1 footage: `03-sector-blue/Minbari Flyer 969 in docking
   bay 17.webp` requires at least 17 bays, and 24 accommodates it.
2. It raises the possibility that Miller's "Cobra-Bay Fighter Storage … 24" in
   `other map 4.jpg` is a **transcription of the docking-bay figure onto the wrong system**.
   If so, the Contract 5 figure of 28 cobra bays stands unopposed. That is a hypothesis with
   one coincidence behind it, not a ruling — **C-002 stays OPEN.**

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

> **Superseded in part. Read `C-003 UPDATE` and then `C-003 UPDATE 2` at the foot of this file
> before acting on anything above.** UPDATE 2 introduces two authority-3 sources that were not
> available when this entry or UPDATE 1 was written, and it partially reverses UPDATE 1.

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

### Evidence accumulated so far — both favour the radial reading

1. **Geometric (strong).** C-003 UPDATE showed the station is 50% structural and its habitable
   volume is four separated regions, so sectors must nest inside the rotating assembly rather
   than slice the length of the station. If sectors nest, levels almost certainly stack
   radially — there is not enough longitudinal room for them to do otherwise.

2. **On-screen (weak but authority 1).** The arrival-concourse wall display in
   `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg` shows
   an in-universe cutaway of the forward section with **multiple parallel longitudinal lines**,
   which in a side cutaway of a cylinder reads as decks stacked radially. The screencap is too
   low-resolution to count them or measure spacing, so this corroborates rather than resolves.

3. **On-screen, structural (authority 1).** `09-garden-core-and-transit/central corridor.webp`
   shows **two occupied levels within a single volume** — a catwalk above a main floor, with
   people on both. So a "level" is not necessarily a full-height deck: it can be a mezzanine
   inside a taller space. **The level count and the deck count need not be equal**, which means
   an address like "Grey 17" does not by itself imply seventeen decks of hull.

   The same frame shows the hull's **circular structural ribs exposed rather than clad**, which
   is a primary motif for the interior kit whatever the level topology turns out to be.

**Radial numbering is now the working hypothesis, but C-004 stays BLOCKING** — a hypothesis
with two supporting arguments is still not a sourced fact, and building 8 km of interior on it
would be exactly the kind of guesswork this project forbids. What would close it: a lift-car
display, a deck plan, or dialogue tying a level number to a gravity or a placeable location.

> **Substantially advanced. See `C-004 UPDATE` at the foot of this file.** Session 2q found the
> deck plans this entry was asking for, plus the authority-1 footage that validates them. The
> *axis* question is now answered; the *numbering convention* is not, and C-004 stays BLOCKING
> on narrower grounds than before.

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

---

## C-003 UPDATE — the longitudinal sector model fails on geometry

Deriving Grey / Brown / Yellow extents (OW-002) exposed a contradiction that settles this.

With the longitudinal framework complete, the station divides as:

| | Length | Share |
|---|---|---|
| Pressurised / habitable | 3,997 m | 50% |
| Structural (truss, spine, flares, spike, reactor) | 4,050 m | 50% |

The habitable volume is **not contiguous**. It is four separated regions:
`primary_fusion_reactor` 292 m (a reactor, not living space), `green_section` 2,928 m,
`red_section` 430 m, `docking_sphere` 347 m. **The Green section alone is 73% of all
habitable volume**, and the entire aft 3,107 m is bare truss spine and reactor.

**Six sectors cannot be laid out as longitudinal slices across this.** Grey (industrial and
manufacturing) and Brown (residential, Downbelow) have nowhere to go — there is no pressurised
volume aft of the rotating assembly to put them in. Laying them along the truss spine would
put a residential district on an unpressurised structural member.

**This is decisive against the longitudinal model** and correspondingly strong support for
`Interior map.jpg`, which shows sectors as **nested layers within the pressurised volume**
rather than slices of the whole 8 km. Under that reading Grey and Brown are radial or
longitudinal subdivisions *inside* the rotating assembly, which has ample room at 2,928 m
long and up to 957 m across.

**Ruling: the longitudinal model is rejected for interiors.** It stays only as the labelling
that ties sector names to visible hull positions on the exterior, which is all
`other map 2.jpg` ever actually demonstrated.

C-003 remains **OPEN** — the exact nesting is still unestablished, and C-004 (level numbering)
is still required before interior geometry. But one of the two candidate topologies is now
eliminated on geometric grounds rather than by preference, which is real progress.

**Consequence for C-004:** if sectors nest inside the rotating assembly, then level numbering
is far more likely radial (decks at decreasing radius, decreasing gravity) than longitudinal.
That does not close C-004, but it makes the radial reading the leading hypothesis.

---
---

# Session 2q — two Security Manual sheets change the picture

Two files in `reference/02-station-cutaways-and-plans/` had never been catalogued. Both are
authority 3 (licensed print — the *Babylon 5 Security Manual*, per the filename of the first
and confirmed by shared terminology). Both bear directly on the two blocking conflicts, and one
of them partially reverses `C-003 UPDATE`.

- `b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp` — the **"Sectional
  Schematic"**: a full-length longitudinal cutaway with a **sector bracket dividing the station
  into six named longitudinal bands.**
- `other map.png` — a **colour sector plate**: a colour-coded longitudinal strip plus **six
  radial cross-section rosettes**, one per sector.

Full extraction, including measured band positions, is in `reference/00-INDEX.md`.

---

## C-003 UPDATE 2 — the longitudinal model is not dead; `other map 2.jpg`'s *ordering* is

`C-003 UPDATE` rejected the longitudinal sector model on geometric grounds. The argument was:

> Grey (industrial and manufacturing) and Brown (residential, Downbelow) have nowhere to go —
> there is no pressurised volume aft of the rotating assembly to put them in.

**That argument was correct, and it was aimed at the wrong target.** It refutes the *ordering*
in `other map 2.jpg` (authority 4), which places Grey aftmost. It does not refute longitudinal
slicing as such. Two authority-3 sources give a different ordering, and under theirs the
geometric objection disappears.

### What the Security Manual sectional schematic actually says

Sector bracket, aft → fore. Boundaries measured from tick centres against the drawn station
extent (px 6→1075 of an 1080-px-wide image). **Scale 7.53 m/px; tick centres are readable to
about ±3 px, so every figure below carries ±23 m** and nothing finer than that is claimed.

| Band boundary | px | → m | nearest boundary in `station.yaml` | Δ |
|---|---|---|---|---|
| bracket start | 9 | 23 | aft terminus **0** | 23 m |
| **Yellow \| Grey** | 431.5 | 3203 | `hull_flare_aft` ends **3107** | 96 m |
| **Grey \| Green** | 486 | 3613 | — (inside `aft_hull_block`) | — |
| **Green \| [Brown]** | 537 | 3997 | `aft_hull_block` ends **4207** | 210 m |
| **[Brown] \| Red** | 808 | 6037 | `green_section` ends **6035** | **2 m** |
| **Red \| Blue** | 855 | 6391 | `red_section` ends **6465** | 74 m |
| bracket end | 1009 | 7550 | `docking_sphere` ends **7286** | 264 m |

Read this correctly: **the Brown/Red and Red/Blue boundaries are indistinguishable from ours at
the resolution of the measurement.** The nominal 2 m on Brown/Red is not a claim of two-metre
precision — it is a coincidence inside a ±23 m window — but the *agreement* is real and it is
the point. Those two derivations share nothing: ours came from Miller's top view rescaled by
k = 2.5891; this one is a different draughtsman's side cutaway in a different book.

The Yellow/Grey boundary is 96 m out, four times the reading uncertainty but inside our own
declared ±75 m framework uncertainty when the two are combined. The Green/Brown boundary is
210 m out and the fore bracket end 264 m — the bracket end is expected to disagree, since the
sectors stop before the deflector spike, which is structure.

That agreement is the reason this sheet is being trusted at all — **but it is weak evidence,
and an earlier draft of this entry oversold it.** Tested against the null hypothesis that the
bracket is unrelated to our framework, the six scored boundaries have a mean miss of **110 m**
where random positions against the same 16 candidate boundaries in `station.yaml` average
**212 m**. Only **6%** of random alignments do as well, so the agreement is real; it is a
p ≈ 0.06 result, not proof. Two specific framings carry less weight than they look:

- the headline **2 m** on Brown/Red is a coincidence *inside* the ±23 m reading window, and
  some boundary landing within 2 m happens by chance **4%** of the time across six draws;
- "three of six inside 100 m" happens by chance **31%** of the time and means almost nothing.

The sheet is worth using. It is not "a stronger cross-check than anything else in the reference
set", and no later work should lean on it as though it were.

The sixth band carries **no label in this reproduction**. **Brown** is the only sector name
absent and the band contains the callout "WASTE MANAGEMENT SYSTEMS ('DOWN-BELOW')". That is an
inference by elimination, and it is recorded as one.

**Do not expect an uncropped scan to supply the missing label.** The sheet *is* cropped — three
expansion leaders descend from the Grey, Green and sixth bands to a second row of detail
brackets that is cut off at y = 334 of 339, and two more rise off the top edge. But the sector
**label row is intact**: measured, the five labels sit in a single text band at y 271–285
(x 16–89, 436–461, 496–520, 815–834, 863–926) and there is no ink at all between x 521 and 814,
where the sixth band's label would go. The band is unlabelled *within a complete row*, not
labelled in a row we have lost.

### Why this ordering survives the geometric objection that killed the other one

| Band | What the sheet puts there | Our hull there | Coherent? |
|---|---|---|---|
| Yellow | fusion cores, coolant, aux power, fuel | reactor + spine + truss — **the entire structural half** | yes: Yellow is engineering / zero-G storage |
| Grey | fabrication furnaces, zero-G maintenance, alpha power substation, variable-gravity research torus | aft hull block, at the rotating/non-rotating interface | yes: Grey is industrial |
| Green | multi-environ 'alien' sector | aft hull block | yes: Green is the alien / diplomatic sector |
| [Brown] | waste management ("Down-Below") ×2, water recreation, hydroponics, core transfer shuttle, **zen garden**, **ambassadorial suites**, **station commander's administration complex** | bearing neck + habitat drum | **partly** — see below |
| Red | 'Zocalo' and commercial sector | `red_section` | yes: Red is the Zocalo |
| Blue | docking bays, customs, bay elevators, ob. dome | forward taper + docking sphere | yes: Blue is docking and C&C |

**Four of six bands match their sector's on-screen function cleanly, and the sixth band does
not.** The 50%-structural / 50%-pressurised split that killed the old ordering is *satisfied* by
this one, because the sector that lands on the bare truss spine is **Yellow — zero-G storage and
engineering**, which is precisely what belongs there. That part of the argument holds.

**The band-4 mismatch is evidence against the elimination, and it is recorded here rather than
left out.** Callout dots were located in the drawing: the **zen garden** terminates at px 742
and the **ambassadorial suites** at px 744, both inside band 4 (541–807), and both are **Green
Sector** on screen. The **station commander's administration complex** is also in band 4 and is
Blue on screen. So band 4 carries Brown, Green *and* Blue facilities, which means either the
sheet's band assignment is loose at this granularity or band 4 is not Brown. It is the second
independent pointer toward `other map.png`'s ordering — see the note under the residual
disagreement below. Neither pointer is a reading of a label, so neither closes C-003.

### The residual disagreement, stated plainly

The two authority-3 sources **do not agree with each other** on the middle two bands.

| Source | aft → fore |
|---|---|
| Security Manual sectional schematic | Yellow, Grey, **Green, Brown**, Red, Blue |
| `other map.png` colour strip | Yellow, Grey, **Brown, Green**, Red, Blue |
| `other map 2.jpg` (auth 4) | Grey, Brown, Green, **Yellow**, Red, Blue |

Green and Brown are transposed between the two authority-3 sources. Caveats on the second:
its "Grey" band is *uncoloured* structure, which may be the rotating/non-rotating interface
rather than a sector at all; and its band fractions do not match the sectional schematic's, so
the two are different artwork rather than one being a colourisation of the other.

**The two readings are not evenly supported, and it would be dishonest to present them as a
symmetric standoff.** Two independent pointers favour `other map.png` — drum = Green:

1. **The drum is hollow, and only the Green rosette is drawn hollow.** `other map.png` draws
   Green as a thick habitable outer annulus around a large empty volume crossed by **three**
   radial spokes, and draws Brown as concentric rings filled to the axis.
   `03-sector-blue/Babylon_5_2-22_34b.jpg` — **authority 1** — shows the habitat drum hollow,
   with three-spoke radial transport and the core shuttle on the axis. The footage matches the
   Green rosette and does not match the Brown one.
2. **The sectional schematic's own band 4 carries the zen garden and the ambassadorial suites**,
   both Green Sector on screen (measured above).

Against that: the sectional schematic's narrow band 3 *is* labelled Green and *does* carry the
multi-environ 'alien' sector (callout dot at px 503, inside 489–531), which is equally Green on
screen. So the sheet spreads Green-sector facilities across two bands, and one of them is the
one it labels Green.

**This is why C-003 is not being closed on the strength of it.** A hollow-versus-filled cartoon
and a callout dot are inferences about a draughtsman's intent; the label is the only reading.
The honest statement is: `other map.png`'s ordering is the better-supported hypothesis, and it
is still a hypothesis. Do not build the Garden or Downbelow on it.

Note also that `00-MASTER.md` §3.1 records `other map 2.jpg`'s order as
"Grey, Brown, Green, Red, Yellow, Blue". Read off the label positions in the render itself,
**Yellow sits between Green and Red**, not after Red. `00-MASTER.md` should be corrected either
way, since that ordering is now outranked twice over.

### Ruling

**Partial. This does not close C-003 and C-003 stays OPEN and BLOCKING.**

What it *does* settle, at authority 3 and consistent with our own geometry:

1. **Sectors are longitudinal bands spanning the full diameter**, not nested radial layers.
   `C-003 UPDATE`'s conclusion that "the longitudinal model is rejected for interiors" is
   **overturned**; what is rejected is `other map 2.jpg`'s *ordering*.
2. **Yellow is the aft structural half; Blue is the forward docking structure; Red is
   `red_section`.** Three of six bands now have sourced longitudinal extents that agree with
   the hull we have already built.
3. `Interior map.jpg`'s nested-radial reading is better understood as **the per-sector radial
   deck structure** (see C-004 UPDATE) rather than as a competing sector topology. The two
   models were never actually in competition: sectors run along the axis, levels run across it.

What is still open, and why it still blocks:

- **Green and Brown are transposed between two equal-authority sources.** Building the Garden
  and Downbelow requires knowing which of the two is the habitat drum. Guessing would put a
  2,000 m error into the largest pressurised volume on the station.
- The Yellow/Grey and Grey/Green boundaries are read off a drawing whose vertical scale is
  demonstrably exaggerated ~2×; the longitudinal fractions cross-check but the internal
  boundaries within the aft hull block do not have an independent check.

**Resolution needs, narrowed:** any source placing the Garden or Downbelow in a *named* sector
with a longitudinal position — an uncropped scan of the Security Manual sheet (the missing
Brown label and the cut-off detail row would likely settle it outright), a deck plan, or
on-screen dialogue tying the Garden to a sector name.

---

## C-004 UPDATE — the deck plans this entry asked for, and the footage that validates them

C-004 asked for "a lift display, a deck plan, or dialogue tying a level number to a gravity or
a location we can place radially". **The deck plans exist and were sitting uncatalogued.**

### 1. The rosettes (`other map.png`, authority 3)

Six radial cross-sections, one per sector. **All five habitable sectors are drawn as concentric
annular rings about a central core**, with named facilities assigned to specific rings and
**radial "transport tubes" as spokes** connecting the outer rings to the axis. The sixth,
Yellow, is machinery and is drawn differently. There is no longitudinal subdivision drawn
anywhere in any of them.

- **Red**: outermost ring carries Zocalo, Earharts, Central Corridor, Waste Management. Inner
  rings carry Casino, Dark Star, Law Courts, Security Central, Business District, Water
  Storage. Power Core / Core Shuttle on the axis.
- **Green**: a thick habitable outer annulus and a **large hollow interior**, crossed by only
  **three radial spokes**. Alien Sector, Council Chamber, Fresh Air Restaurant, Earthforce
  Office, Zen Garden, Hydroponics in the outer ring.
- **Brown**: concentric rings, and **"DOWNBELOW" is marked with a double-headed arrow spanning
  an OUTER annular band**, with Happy Daze beside it.
- **Blue**: concentric rings around a **central docking hub** on the axis.
- **Grey**: concentric rings — atmosphere monitoring, research labs, fabrication furnaces,
  maintenance, primary breaker.
- **Yellow**: not concentric — a cog of 12 radial cooling fins around a power transfer core.
  It is machinery, not habitation, which is itself consistent with Yellow being the structural
  half.

### 2. The same sheet's longitudinal section agrees

In a longitudinal cutaway, a cylindrical deck at radius r appears as a pair of horizontal lines
at ±r. The Security Manual sectional schematic shows exactly that: **long horizontal lines
running the length of each pressurised section, symmetric above and below the centreline**,
crossed by sparser vertical frames. The core transfer shuttle runs on the axis. One of its own
callouts is **"CONCENTRIC PERSONNEL TRANSFER SYSTEMS"** — the draughtsman's word, not ours.

### 3. Authority-1 footage independently confirms the cross-section

This is the part that matters, because a print diagram alone would be authority 3 asserting
something the show never showed.

`reference/03-sector-blue/Babylon_5_2-22_34b.jpg` (S2E22, on-screen, also duplicated as
`01-station-exterior/view.jpg`) shows the habitat drum interior along its axis:

- the **end cap is a disc of concentric annular bands** — decks seen end-on;
- a **lattice truss runs the length of the axis** carrying illuminator tubes, with a **serrated
  rack** on its lower edge;
- **core shuttle cars hang beneath it**;
- a **radial transport tube** runs from the axis out to the drum wall;
- the drum's inner surface is landscape, and the interior is **hollow**.

That is the **Green rosette, in live action** — thick habitable outer annulus, hollow interior,
radial spokes, core shuttle on the axis. `09-garden-core-and-transit/The Gardens.webp` and
`garden.png` show the same structure from the ground.

A print diagram and a broadcast frame, produced independently, agree on the cross-section of
the largest volume on the station. That licenses reading the other five rosettes as topology.

### What this settles

**The axis question is answered. A "level" is a concentric radial deck, not a longitudinal
slice.** Three independent lines now say so and none says otherwise:

- authority 3 print, twice (rosettes; longitudinal section showing radial decking);
- authority 1 footage (drum end cap, hollow drum, radial spokes, axial shuttle);
- the structural argument from C-003 UPDATE 2 — if **sectors** already index the longitudinal
  axis, a longitudinal reading of **level** would make the address `<Colour> <number>` index
  the same axis twice, which is not an address scheme.

It also **removes the standing objection recorded in this entry.** C-004 worried that radial
numbering "would place Downbelow against the outer hull — an odd home for disused interior
space". The Brown rosette says Downbelow **is** the outer ring, explicitly and by name. The
objection is answered by the source rather than argued away.

### What this does **not** settle — and why C-004 stays BLOCKING

1. **Direction and origin of numbering.** Nothing labels a ring with a number. Whether level 1
   is the outermost (full gravity) or the innermost is still unsourced. Getting this backwards
   inverts every address on the station and puts Downbelow at the axis in zero gravity.
2. **How many levels per sector.** The rosettes are a stylised graphic at 660×414 with JPEG
   artefacts; counting rings off them is not sound, and no source states a count. "Grey 17"
   implies at least 17 of *something* in Grey Sector, which the rosettes cannot confirm.
3. **Radial spacing.** Explicitly unavailable. The sectional schematic's vertical scale is
   exaggerated roughly 2× (the drum reads L/D 1.46 where our framework gives ~3.1), so **no
   deck spacing, ring radius or ceiling height may be measured from it.** This is the same
   ruling as C-005 and for the same reason.
4. `09-garden-core-and-transit/central corridor.webp` still shows **two occupied levels inside
   one volume**. Mezzanines exist, so level count and deck count still need not be equal.

**C-004 remains OPEN and BLOCKING**, but on a much narrower question than before: not *what
axis*, but *which end is 1, and how many*. That is now the single highest-value gap in the
whole reference set — one lift-car display would close it.

### Consequences that can be acted on before C-004 closes

These follow from the axis alone and do not depend on the numbering convention:

- **Radial transport spokes are canon, not invention.** `station/physics/core_shuttle.py`
  already models rim-to-axis transit; the rosettes and the footage both show the spokes it
  assumes. The 133-second minimum comfortable transit is a property of a structure the sources
  actually depict.
- **The core shuttle runs on the axis** through the rotating assembly, driven along a **racked
  lattice truss**, with cars **suspended below** it.
- **Green's cross-section is hollow; Red's, Brown's, Blue's and Grey's are filled with
  concentric decks.** Whichever of Green/Brown turns out to be the drum, one large sector is a
  hollow landscaped volume and the others are decked.
- `docs/interior-kit-spec.md` §6 can stay as it is. It withholds corridor width, ceiling height
  and deck spacing pending C-004, and item 3 above confirms those numbers are still not
  available from any source we hold.

---

## C-007 — additional evidence, ruling unchanged

The **Yellow Sector rosette** in `other map.png` (authority 3) is an end-on view of the reactor
section labelled **"COOLING FINS (12)"**, and it draws them as **12 fins radially arrayed**
around a power transfer core, cog-fashion.

This is a third source and it appears to contradict C-007's ruling of **6 coplanar blades**.
**The ruling stands**, for two reasons:

1. C-007 rests on `reference/01-station-exterior/exterior more.jpg`, an **authority-2
   orthographic production sheet** showing the radiators edge-on in top view and full-face in
   side view. Authority 2 outranks authority 3, and an orthographic sheet outranks a
   diagrammatic rosette.
2. They may not be the same system. The rosette's fins are **small and numerous, immediately
   around the reactor core**, alongside "coolant transfer tubes and holding tanks"; the
   Contract 5 / production-sheet radiators are **large blades standing off the spine on a
   rail**. `00-MASTER.md` §1.3 already lists *Reactor cooling fins (12)* and *Coolant manifolds
   (8)* as separate items.

Recorded because it explains where the radial-array reading came from, and because a future
session that finds this rosette should not reopen a settled conflict. **C-007's lesson holds:
a bare count in a labelled diagram does not imply an arrangement.**

---

## C-003 RESOLVED — both readings were right, about different axes

The file that settles this had been passed over twice.
`02-station-cutaways-and-plans/b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp`
is a **Sectional Schematic** from the Security Manual (authority 3), 1080×339. It was skipped
on resolution — the same mistake, in the opposite direction, as nearly trusting the
animated-film frames because they were the *highest* resolution in the set.

**It draws sector boundaries as labelled brackets along the station's length**, and
simultaneously draws decks as long horizontal lines symmetric about the axis. That is the
whole conflict resolved in one drawing:

> **Sectors are longitudinal ranges. Levels within them are concentric radial rings.**

`other map 2.jpg` was right that sectors run along the length. The rosettes in `other map.png`
were right that decks are concentric rings. Neither was wrong; they were describing different
axes, and C-003 existed because I had read them as competing.

### Sector extents, measured

Bracket tick columns read at px 8, 431, 486, 808, 854, 1010; the rule spans px 10–1007. As
fractions of station length, and at 8,047 m:

| Sector | Fraction | z (m) | Length |
|---|---|---|---|
| Yellow | 0.000–0.422 | 0 – 3,397 | 3,397 |
| Grey | 0.422–0.477 | 3,397 – 3,839 | 442 |
| Green | 0.477–0.798 | 3,839 – 6,425 | 2,586 |
| Red | 0.798–0.844 | 6,425 – 6,794 | 369 |
| Blue | 0.844–1.000 | 6,794 – 8,047 | 1,253 |

**Independent cross-check.** The longitudinal framework was derived months earlier from an
entirely different sheet (Miller's top view, by pixel calibration against his own stated
length). It agrees: Green 2,586 m here against 2,928 m there (11.7%), Red 369 m against
430 m (14.1%). Two unrelated sources, two unrelated methods, agreement inside 15% — that is
what makes this trustworthy rather than merely legible.

This sheet has **no scale bar**, so only proportions are read from it. Absolute positions come
from applying those proportions to the canon 8,047 m.

### Brown is not a longitudinal sector on this sheet

Only five brackets are drawn: Yellow, Grey, Green, Red, Blue. **Brown is absent**, and
"Down-Below" appears instead as a label on the **outer band** in the Green region
("WASTE MANAGEMENT SYSTEMS ('DOWN-BELOW')").

The natural reading is that **Brown is a radial designation — the outermost ring — rather than
a longitudinal one**, which would explain why it can be spoken of as a place without appearing
as a length of station. That is consistent with the Brown rosette in `other map.png`, which
marks DOWNBELOW with a double-headed arrow spanning an **outer annular band**.

**This is inference, not what the sheet says**, and is logged as INV-009. It does not affect
the five bracketed extents above, which are read directly.

### What this does and does not close

- **C-003 is RESOLVED.** Sectors are longitudinal; levels are radial rings.
- **C-004 remains OPEN and BLOCKING**, on the single narrow question it was reduced to:
  which ring is level 1. This sheet numbers nothing.
