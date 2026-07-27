# Canon Conflicts

Reference disagreements. Each carries a ruling or is marked open. Open conflicts touching
geometry **block** the affected build work — they are not resolved by picking whichever is
convenient at the time.

---

## CURRENT STATUS — read this first

This file is append-only and chronological, which means the newest note on a conflict is not
always the one nearest its heading. C-003 in particular now has eight entries spanning several
sessions, one of which is headed "RESOLVED" and is followed by four later notes that narrow it
further. **Do not act on a heading without checking here.**

| Conflict | Status | What is actually still open |
|---|---|---|
| C-001 overall length | **RESOLVED** | — 8,047 m, show canon over Miller |
| C-002 cobra bay count | Open, non-blocking | 24 vs 28; provisionally 28 bays / 24 fighters |
| **C-003 sector arrangement** | **Model resolved, assignment OPEN and BLOCKING** | Sectors are longitudinal bands; levels are radial rings. **Which band is the ~2,000 m habitat drum** is disputed — the Green/Brown transposition |
| **C-004 level numbering** | **OPEN and BLOCKING** | Radial axis established. **Which ring is level 1** is not |
| C-005 Contract 5 scale | Resolved, source degraded | Topology only, never dimensions |
| C-006 Miller drawing vs table | **RESOLVED** | Table wins on dimensions, drawing on ordering |
| C-007 radiator arrangement | **RESOLVED** | Six coplanar blades, not a radial array |

**Both blocking conflicts have been reduced to a single question each.** Neither is a broad
unknown any more; each needs one specific piece of evidence:

- **C-003** — any source placing the Garden or Downbelow in a *named sector at a longitudinal
  position*.
- **C-004** — any source numbering a ring, or tying a level number to a gravity or a placeable
  location.

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

> **Superseded in part. Read `C-003 UPDATE`, then `C-003 UPDATE 2`, then the
> `session 2r note` — all at the foot of this file — before acting on anything above.**
> UPDATE 2 introduces two authority-3 sources that were not available when this entry or
> UPDATE 1 was written, and it partially reverses UPDATE 1. The session 2r note then **discounts
> UPDATE 2's pointer 1**: authority-1 footage shows the hollow drum containing facilities from
> two different rosettes, so "only Green is drawn hollow" no longer identifies the drum's sector.
> The **session 2s note** at the very foot then secures the drum-interior reading that both of
> those observations depend on, from a much clearer authority-1 frame
> (`reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp`) — but adds
> nothing at all to the sector question.

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

> **Substantially advanced. See `C-004 UPDATE` and then the `session 2r note`, both at the foot
> of this file.** Session 2q found the deck plans this entry was asking for, plus the
> authority-1 footage that validates them. The *axis* question is now answered; the *numbering
> convention* is not, and C-004 stays BLOCKING on narrower grounds than before. Session 2r
> measured the drum end cap (≈48 rim lights at 7.4° pitch; 8–9 concentric courses) and found
> ~~authority-2 corroboration of the Blue rosette~~ — and confirmed that **no lift display and no
> level number appears in any file in Blue, Red or the exterior folder.**
> **The Blue-rosette corroboration is struck by the `session 2t note` at the very foot of this
> file**: it was an *exterior* end-on view of a body of revolution, which cannot be evidence about
> interior deck topology, and its source is not independent of the authority-4 Miller sheets. One
> rosette has independent corroboration, not two.
> **Session 2s adds a negative result and one constraint** (note at the very foot of this file):
> the 28 files in `12-starfury`, `14-characters-and-uniforms` and `15-races-and-makeup` contain
> **no level number, lift display, deck plan or sector name either** — six folders are now cleared
> — and authority-1 footage shows the **drum's inner surface is open ground with buildings standing
> on it**, so any radial deck stack must terminate at the drum floor rather than continue to the
> axis.

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

> **See also `C-007 — additional evidence` and the `session 2s note`, both at the foot of this
> file.** Session 2s found a **second, independent authority-2 production source** — an in-universe
> station wireframe on a C&C set graphic in
> `reference/14-characters-and-uniforms/Sheridan.jpg` — that shows the same three-above /
> three-below coplanar arrangement. C-007 is no longer a single-source ruling. That note also
> records that each blade is a **two-limbed fork**, and offers "six forks = twelve limbs" as a
> third candidate explanation of the count of 12.
>
> **Read the `session 2t note` at the very foot of this file with it.** The Sheridan wireframe was
> re-opened and shows what the 2s note says it shows. But `exterior more.jpg` — the source C-007
> originally rested on — is rendered from the **same 3D model as the authority-4 Lawrence D. Miller
> sheets**, so its authority-2 rating is unestablished. C-007 stays **RESOLVED at 6 coplanar
> blades**; `Sheridan.jpg` is now the *firmer* of the two sources rather than the second one. The 2t
> note also qualifies the "atmospheric life support regulators (4)" count before it reaches
> `00-MASTER.md` §2 — four indicator boxes, three hull leaders.

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

## C-003 — MODEL RESOLVED, SECTOR ASSIGNMENT STILL OPEN
### (was headed "RESOLVED"; corrected in session 2t — see the head entry)

**This entry settles the *model*, not the *assignment*.** Later notes (2r, 2s) show that which
longitudinal band is the habitat drum is still disputed between the two authority-3 sheets.
Read this for the model; read the head entry for current status.

Both readings were right, about different axes

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

---
---

# Session 2r — three notes from the Green / Grey / Garden re-examination pass

Every image in `05-sector-green/`, `07-sector-grey/` and `09-garden-core-and-transit/` was
re-opened and magnified. Full extraction is in `reference/00-INDEX.md` under "Session 2r".
Three findings touch the blocking conflicts. **None of them closes either one.** They are
recorded here because C-003 and C-004 gate all interior work and the evidence for each should
accumulate in one place.

---

## C-003 note 2r — two weak pointers, both in the same direction as the existing three

C-003 UPDATE 2 records two pointers favouring `other map.png`'s ordering, in which **the habitat
drum is Green Sector**: the hollow Green rosette matching the drum footage, and the sectional
schematic's band 4 carrying the zen garden and the ambassadorial suites. This pass adds two more.
**Both are weaker than the two already recorded, and both depend on an attribution that is not
itself sourced.** They are set down with that stated plainly rather than folded in as though
they were equivalent.

**1. `05-sector-green/rotunda.webp` is a glazed room whose windows look inward across the drum.**

The original index entry asserted this. It was tested this pass rather than repeated. The test:
in a spin habitat, terrain fills a window from sill to head because there is no sky; on a planet
a window at that height shows a sky band unless it faces a hillside. Magnified, the right-hand
windows show **green and khaki terrain reaching the window head with no sky band**. Against it:
the left-hand windows are blown out and could be sky, and the heads are deeply recessed. The
reading holds as corroboration.

If that room is in Green Sector, then Green Sector contains rooms in the drum's outer wall, and
Green abuts or is the drum. **The only thing placing the room in Green Sector is the folder it
was filed in.** Nothing in the frame names a sector. That is a filing decision by the uploader,
not a source, and it cannot be allowed to do load-bearing work in a conflict this expensive to
get wrong.

**2. The Green rotunda and the Garden's civic building share a column order.**

`rotunda.webp`'s window columns and `09-garden-core-and-transit/garden.png`'s colonnade are the
same design: a plain slightly tapered cylindrical shaft carrying **a group of three narrow ring
collars**, a longer plain shaft above, a short stepped capital under a flat entablature. Two
independent frames, same order.

**This is the weakest pointer in the whole C-003 file and it should be treated as such.** A
single production design department reused vocabulary across every set on the show; a shared
column motif is at least as well explained by one art director as by shared sector membership.
It is recorded only because it points the same way as the other four and because a future session
that notices the match should find it already assessed rather than re-derive it and overrate it.

**Ruling: unchanged. C-003 stays OPEN and BLOCKING.** The count of pointers favouring
`other map.png`'s ordering is now five, but three of the five are inferences about intent and
two of those three rest on folder attribution. Adding weak evidence to weak evidence does not
make strong evidence. What would still close it is what C-003 UPDATE 2 already asked for: an
uncropped scan of the Security Manual sheet, a deck plan, or on-screen dialogue tying the Garden
to a sector name.

---

## C-004 note 2r — the word `LEVEL` is signed on corridor walls, at authority 1

`reference/07-sector-grey/grey level 1.webp`, magnified 14× on the right-hand wall, resolves the
dark plaque high on the wall as **white uppercase sans-serif letters on a black ground**, and the
first four read **L, E, V, E**. The word is `LEVEL`.

**The number is not in the picture.** The plaque runs off the right edge of the frame. The
existing index entry transcribed it as "Le…l …", which was reading a number that is not there;
that has been corrected in `reference/00-INDEX.md`.

What this establishes and what it does not:

- **Establishes**, at authority 1: `LEVEL` is a wayfinding word physically signed in station
  corridors, on a landscape plaque set in a recessed dark field at high level, white-on-black
  uppercase. Levels are an addressing unit the station itself signs, not only something
  characters say. That is a small fact and it is a real one, and it is the first on-screen
  sighting of the word in the reference set.
- **Does not establish** the numbering direction, the origin, or the count. C-004's narrowed
  question — *which end is 1, and how many* — is untouched.

**C-004 stays OPEN and BLOCKING.**

---

## C-004 note 2r (second) — a named location that may be placeable radially, and why it still is not enough

C-004 asked for "a deck plan, or dialogue tying a level number to a gravity or a location we can
place radially". This is the nearest thing this pass found, and it falls short in a specific way
worth recording.

`other map.png` (authority 3) lists **"Central Corridor" in the OUTERMOST ring of the Red Sector
rosette**, alongside Zocalo, Earharts and Waste Management — already recorded in C-004 UPDATE §1.
`reference/09-garden-core-and-transit/central corridor.webp` is an authority-1 frame of a wide
two-level public concourse, and **the hull's circular ring frames are exposed in it**, unclad,
crossing the whole volume. In a concentrically decked cylinder only the outermost deck sits
against the hull ribs.

So an authority-3 diagram puts a named facility in the outermost ring, and an authority-1 frame
of a space bearing that name shows outermost-ring construction. Those agree.

**Why this does not resolve anything:**

1. **The link between the frame and the name is the filename.** A filename is the uploader's
   label. Nothing in the frame names the location, and no dialogue or signage is legible in it.
2. **Even granting the identification, it gives a ring, not a number.** It would say "this space
   is on the outer ring of Red Sector". It would not say whether that ring is Red 1 or Red 12.
   C-004's remaining question is the numbering convention, and a ring without a number does not
   touch it.

What it does do is **corroborate the radial-deck model** — a fourth independent line agreeing
that decks are concentric — and it makes `central corridor.webp` a probable **Red Sector**
reference rather than the Brown/Downbelow space the index originally guessed. Both are recorded
in `reference/00-INDEX.md`. The file has **not** been moved.

**C-004 stays OPEN and BLOCKING.** One lift-car display would still close it, and this pass did
not find one.

---
---

# Session 2r (Blue / Red / Exterior) — an exhaustive look at Blue, Red and the exterior folder

<!-- A sibling pass in the same session covered Green, Grey and the Garden; its notes are
     above under "Session 2r — three notes from the Green / Grey / Garden re-examination pass".
     The two are independent. -->


Twenty image files in `reference/01-station-exterior`, `03-sector-blue` and `04-sector-red`
were each opened and examined, including the ones already catalogued. Full extraction is in
`reference/00-INDEX.md` under *Session 2r*. Two things bear on the blocking conflicts. One
adds numbers to C-004 without closing it. The other makes C-003 **harder**, and is recorded
here for that reason rather than left out.

---

## C-003 — session 2r note: the drum contains facilities from two different rosettes

**Status: does not resolve. Complicates. C-003 stays OPEN and BLOCKING.**

### The observation

`reference/04-sector-red/Earhart's.webp` (**authority 1**, on-screen CGI) shows Earhart's — a
lenticular building on a single pedestal — standing on the **floor of the hollow rotating
habitat drum**. Examined at 5×, the frame shows, unambiguously:

- olive and tan **hedged agricultural fields and a broad road curving up both sides and over
  the top of frame** — the far side of the drum, seen as sky;
- across the top centre, **two splayed support struts banded with orange rings** meeting a
  hanging structure on the **axial spine**.

`reference/04-sector-red/Fresh air.webp` (and its better copy
`11-props-and-technology/fresh air resturant signage with view.webp`, **authority 1**) shows the
**Fresh Air Restaurant** as an open terrace with the **far side of the drum overhead** as a dark
mottled expanse of terrain, its lighting hung from exposed service pipes with no soffit above.

Both are therefore in the same hollow volume: the habitat drum.

Now compare `other map.png` (**authority 3**, the colour sector plate whose six rosettes
C-004 UPDATE relies on):

| Facility | Rosette that names it | Where the footage puts it |
|---|---|---|
| **Earharts** | **Red** — outermost ring | floor of the hollow drum |
| **Fresh Air Restaurant** | **Green** — outer annulus | floor of the hollow drum |
| Zen Garden | Green | drum (`Babylon_5_2-22_29a.jpg`) |

### Why it matters

C-003 UPDATE 2 records two pointers favouring `other map.png`'s ordering over the Security
Manual sectional schematic's, and **pointer 1 is the load-bearing one**:

> **The drum is hollow, and only the Green rosette is drawn hollow.** … The footage matches the
> Green rosette and does not match the Brown one.

That argument requires the hollow drum to belong to **one** sector. The footage now shows the
drum containing a facility from the **Red** list *and* a facility from the **Green** list. So
either:

1. **the drum spans more than one longitudinal sector band** — entirely plausible, since the
   habitat cylinder is ~2,928 m long and the Red band is only ~430 m, in which case Red, Green
   and Brown could all be bands *of the same drum* and **all three rosettes ought to be drawn
   hollow**, and only one is; or
2. **the rosettes' facility lists are assigned loosely**, at a granularity finer than the sheet
   actually supports.

**Reading 1 is independently supported by the sibling pass recorded immediately above.** Its
second C-004 note observes that `other map.png` puts **"Central Corridor" in the Red rosette's
OUTERMOST ring**, and that `09-garden-core-and-transit/central corridor.webp` shows **the hull's
circular ring frames exposed and unclad** — outermost-ring construction, against the hull. Put
that beside this note: **Earharts is also in the Red rosette's outermost ring, and Earhart's
stands on the floor of the hollow drum.** In a spin habitat the drum floor *is* the outermost
ring — against the hull, at full gravity. So both of the Red rosette's outer-ring facilities for
which we hold footage are consistent with that ring being **drum floor**. That points at reading
1, not reading 2: the drum is crossed by more than one sector band, and Red's outer ring is a
length of it.

Reading 2 is the same failure mode C-003 UPDATE 2 already found in the *other* authority-3
source — the sectional schematic's band 4 carrying the zen garden, the ambassadorial suites and
the station commander's administration complex, which are Green, Green and Blue on screen. **We
now have the identical problem in both authority-3 sources.** Neither sheet's facility labels
survive contact with the footage at sector granularity.

Either way, **pointer 1 is weaker than C-003 UPDATE 2 presents it.** "Only Green is drawn
hollow" is evidence about the draughtsman's shading convention, and the shading convention is
demonstrably not tracking which volume is hollow — if it were, Red would be hollow too, because
Earhart's is standing in it.

### What this changes, stated plainly

- **Nothing is resolved.** The Green/Brown transposition that blocks C-003 is untouched.
- **This partly disagrees with the sibling C-003 note above**, which counts five pointers
  favouring `other map.png`'s ordering and lets pointer 1 stand among them. It should be **four,
  not five**: pointer 1 (only Green is drawn hollow) is discounted here on authority-1 evidence.
  Both notes reach the same ruling — C-003 stays OPEN and BLOCKING — so nothing downstream
  changes, but a future session should not add the two counts together.
- **C-003 UPDATE 2's conclusion that `other map.png`'s ordering is "the better-supported
  hypothesis" now rests mainly on pointer 2** (the sectional schematic's own band 4 carrying
  Green facilities), which is itself an inference about a callout dot. Pointer 1 should be
  discounted, not deleted — the Green rosette *is* drawn hollow and the drum *is* hollow; it is
  the exclusivity of that match that fails.
- **A new hypothesis is now on the table and should be tested before either ordering is
  adopted:** that the drum is not one sector but is *crossed* by several sector bands, and that
  the rosettes are per-band cross-sections of a partly-shared volume drawn with inconsistent
  care. If that is right, the Green/Brown question is less important than it looks, because both
  would be bands of the same cylinder — but it is a hypothesis with no source behind it and it
  is **not** licence to start building.
- **Resolution needs, unchanged and still narrow:** a source placing the Garden or Downbelow in
  a *named* sector with a longitudinal position. An uncropped scan of the Security Manual
  sectional sheet remains the highest-value single acquisition for this project.

### One further, weaker tie, recorded with its own caveat

`reference/04-sector-red/Darkstar_logo.webp` (authority 1, previously uncatalogued) is the
on-screen **"DARK STAR"** venue sign. Dark Star is named in the **Red** rosette. With Zocalo,
Earharts and the Casino, that is **four Red-rosette facilities for which we now hold authority-1
footage**.

**This is worth less than it appears and must not be cited as corroboration of the Red
rosette.** The frames confirm that these four *exist*; they do not independently confirm that
the four are *co-located in Red*. Their assignment to `04-sector-red/` is our own filing, and
the rosette is the only source for the co-location — so treating the folder as evidence for the
rosette would be circular. It is recorded so that a future session does not rediscover the tie
and over-read it.

---

## C-004 — session 2r note: the drum end cap, measured

**Status: corroborates and quantifies. Does not resolve. C-004 stays OPEN and BLOCKING.**

C-004 UPDATE settled the *axis* question — a level is a concentric radial deck — and left two
gaps: **which end is 1**, and **how many**. This note puts numbers on the second gap's raw
material without closing it, and adds an authority-2 corroboration of the Blue rosette.

### 1. The drum end cap, measured off authority-1 footage

`reference/03-sector-blue/Babylon_5_2-22_34b.jpg` (S2E22, 1014×576; duplicated as
`01-station-exterior/view.jpg`).

Six of the blue rim lights on the outermost band were located and fitted with an algebraic
circle:

- fitted centre **(934.7, 165.9) px**, fitted radius **R = 371.6 px**;
- **radial residuals all under 0.9 px** — the arc is a clean circle over the 37° sampled;
- mean angular pitch of the lights **7.40°**, individual deltas 7.09°–7.59°.

The disc is viewed obliquely, so the fitted centre is slightly displaced and the pitch is
biased; the defensible figure is **7.4° ± 0.3°**, i.e. **46–50 lights around the full
circumference, most plausibly 48** (48 gives exactly 7.5°).

A radial intensity profile about the same centre, averaged over 103°–146°, places dark
circumferential ribs at normalised radius:

```
r/R ≈ 0.25  0.28  0.32  0.51  0.71  0.80  0.98  1.03
```

with bright band centres at r/R ≈ 0.21, 0.36, 0.62, 0.75, 0.84. That is **eight or nine
concentric annular courses** between r/R 0.2 and the rim, outboard of a **dished, radially
ribbed hub cone** filling the inner ~20% of the radius. The plates within each course are
roughly square — radial depth ≈ circumferential width — so the cap is a grid, not a set of thin
rings; two courses are checker-plated.

### 2. Authority-2 corroboration of the Blue rosette

`reference/01-station-exterior/exterior more.jpg` — the orthographic production-model renders —
contains a **fore end view** that had never been extracted. The forward docking structure seen
end-on is **a disc of concentric annular bands**: dark cruciform hub with a red lamp at the
centre, a cog-like ring of fine radial teeth, a bright silver annulus, a broad blue panelled
annulus with radial and circumferential seams, and a finely toothed outer rim.

That is `other map.png`'s **Blue rosette** — "concentric rings around a central docking hub on
the axis" — rendered from the production model. A print diagram (authority 3) and a production
render (authority 2), produced independently, agree on the Blue cross-section, exactly as they
already do on the Green one via the drum footage. **Two of the six rosettes now have
independent corroboration.** That further licenses reading the rosettes as topology.

The **aft end view** on the same sheet is correspondingly *unstructured* — a rust-brown disc
with a grey polygonal hub, radial voids and a lit spar, with no concentric decking. Consistent
with the Yellow rosette being drawn as a cog of machinery rather than as habitable rings.

### 3. What this does **not** settle

- **The ring count is not a deck count.** These are panelling courses on a transverse bulkhead.
  Angular averaging across an obliquely viewed disc smears the profile; and the index already
  records that a "level" can be a mezzanine, so level count and deck count need not be equal.
  Eight or nine courses is the *raw material* for a deck count, not a deck count.
- **Nothing is numbered.** No ring, no wall, no fitting in any of the twenty files carries a
  level number, and **no lift-car display appears in any of them.** The four S2E22 frames, C&C,
  the War Room, both docking-bay frames and every Red Sector frame were checked specifically for
  one. There is none.
- **The 48-light count constrains the drum's circumferential module, not its radial one.** It is
  a real number and it should be built to, but it says nothing about which ring is Level 1.

**C-004 remains OPEN and BLOCKING on exactly the question C-004 UPDATE left it on: which end is
1, and how many.** These three folders do not contain the answer. The highest-value acquisition
is still a lift-car display or a numbered deck plan.

### 4. One correction to a supporting argument

C-002's session-2q note and the index both state that
`03-sector-blue/Minbari Flyer 969 in docking bay 17.webp` establishes that docking-bay numbering
reaches at least 17, and use it to cross-check the Security Manual's "DOCKING BAYS (24)".

**No bay number is legible anywhere in that frame.** The "17" is from the filename — the
uploader's caption. The cross-check rests on a caption, not on a reading. C-002 was already OPEN
and stays OPEN; the argument supporting the provisional reading is weaker than written.

---

## C-004 note 2s — evidence item 2 is RETRACTED: the schematic's lines were counted, and there are four

C-004's "Evidence accumulated so far" lists as **item 2** the arrival-concourse wall display in
`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg`, on the
grounds that it shows "**multiple parallel longitudinal lines**, which in a side cutaway of a
cylinder reads as decks stacked radially". It is qualified there as weak "because the screencap
is too low-resolution to count them or measure spacing".

**They can be counted now, and the count goes the wrong way for the argument.**

Method, stated so it can be re-run or disputed: the display occupies only about 320×190 px of a
1262×634 frame. It was isolated on the green channel (the vector graphic is green on black),
median-filtered at radius 3 to kill JPEG mosquito noise, autocontrasted, and resampled 8×. Line
positions were then taken from **row and column intensity profiles**, not by eye.

- **Main body, longitudinal lines:** interior peaks at rows 60, 83, 106 of the isolated crop — a
  **regular 23 px pitch** — plus the top and bottom edges. **Three interior lines, four bands.**
- **Shallow tail section, longitudinal lines:** peaks at rows 42, 56, 69, 84, 93 — spacings 14,
  13, 15, 9 px, converging as perspective requires. **Five lines, four bands.**
- **Transverse lines:** peaks at columns 40/49, 71/77, 92/98, 139/143, 153/157 — **paired lines
  about 6 px apart, the pairs repeating at a 21–23 px pitch**. The pairing reads as ribs drawn
  with thickness rather than as separate members.
- Incidentally: **the transverse pitch and the longitudinal band depth are the same number**
  (~23 px), so whatever this diagram depicts has a roughly isotropic structural grid — bay length
  equal to band depth.

**Why this retracts rather than strengthens.** Four bands cannot be four decks in a station whose
on-screen addresses run to **Grey 17**. Two readings survive and neither helps C-004:

1. the lines are **hull plating seams and primary frames**, not decks, in which case the frame
   says nothing about deck stacking at all; or
2. the diagram shows **only top-level structural divisions** of one region, in which case the
   band count is not a deck count and still cannot be used as one.

Either way the frame stops being evidence for radial decking. **C-004 evidence item 2 is
retracted.** The radial reading still rests on item 1 (the geometric argument from C-003 UPDATE),
item 3 (`central corridor.webp`'s two occupied levels in one volume), and the C-004 UPDATE rosettes
and sectional schematic — which are the strong ones and are untouched by this.

A second point worth recording so it is not re-derived: **the schematic is not identified.** The
index entry that introduced it calls it "a cutaway of the forward docking region". Nothing in the
frame names it, and the silhouette — domed cap, deep gridded body, a step down to a shallow
tapering tail, and a fan of long members below — does not match the station's own 30:1 profile at
any plausible viewing angle. Treat the subject as **unidentified** until something else places it.

**This resolves nothing. It removes a supporting argument. C-004 stays OPEN and BLOCKING**, and
what would close it is unchanged: a lift-car display, a deck plan, or dialogue tying a level number
to a gravity or a placeable location. This pass did not find one.

---

## C-003 note 2s — a sixth pointer for the drum being Green, and it is the first one not resting on folder attribution

C-003 UPDATE 2 and C-003 note 2r together record five pointers favouring `other map.png`'s
ordering, in which **the habitat drum is Green Sector**. Note 2r is explicit that three of the five
are inferences about intent and that two of those three rest on **folder attribution** — a file was
filed in `05-sector-green/`, and that filing is the uploader's decision, not a source. That is the
weakness this note addresses.

**The pointer.** `other map.png` (authority 3) names **"Fresh Air" as a facility in the Green
rosette**. `reference/11-props-and-technology/fresh air resturant signage with view.webp`
(authority 1, 1200×1046, duplicated at `04-sector-red/Fresh air.webp`) is a frame of that
restaurant, and:

1. **The identification runs through the restaurant's own sign, in shot.** The oval plaque reads
   `The` / `FRESH AIR` / `Restaurant` and is legible at 8×. It is not a filename, not a folder, and
   not an uploader's label. This is the specific failure mode that sank the `central corridor.webp`
   pointer in C-004 note 2r (second), and it does not apply here.
2. **The frame places the named facility inside the drum.** Magnified 5×, the upper left of the
   frame resolves as a **convex, curving multi-storey tower face carrying a regular grid of pale
   lit windows in stacked rows** — a cylindrical glazed building standing beside the restaurant.
   Above and beyond it the frame is a dark mottled expanse with an orange-tan patch. The
   restaurant is therefore in a **large open landscaped volume containing multi-storey
   buildings**, which on this station is the habitat drum and nothing else.

So an authority-3 sheet puts Fresh Air in Green, and an authority-1 frame — identified by its own
signage — puts Fresh Air in the drum. **If both hold, Green contains the drum.**

**What it is not.** Two limits, stated rather than glossed:

- The drum reading in point 2 leans hardest on the **glazed tower**, which is well resolved. The
  "far side of the drum overhead" is a **dark, low-contrast field** and on its own would be a weak
  read — it could be a painted backdrop of anything. The tower is what carries the claim.
- `other map.png` is authority 3 and C-003 UPDATE 2 already asks for **an uncropped scan of the
  Security Manual sheet** before its rosettes are leaned on. Nothing here supplies that.

**Ruling: unchanged. C-003 stays OPEN and BLOCKING.** The count of pointers favouring the
`other map.png` ordering is now six, and this one is **better than the two added in note 2r**
because it does not depend on where a file was filed. It is still corroboration, not proof: six
pointers of which one is a print-to-footage tie is not a sourced fact about sector topology. What
would close C-003 is what C-003 UPDATE 2 already asked for — an uncropped scan of the Security
Manual sheet, a deck plan, or on-screen dialogue tying the Garden to a sector name.

---

# Session 2s (folders 12 / 14 / 15) — from the Starfury, uniform and race reference pass

*A sibling agent in the same workflow is also labelling its work "session 2s" (folders 11, 16, 13).
The folder list in each heading disambiguates them.*

Three folders were catalogued exhaustively. Costume material dominates and bears on nothing here,
but two files carry structural content and one negative result is worth recording.

---

## C-007 — session 2s note: independent authority-2 corroboration, and a candidate reconciliation of "12"

### The source

`reference/14-characters-and-uniforms/Sheridan.jpg` is a production/publicity still of Sheridan on
the C&C set (1414×1418). Behind him, a **backlit C&C graphic panel carries a cyan wireframe side
elevation of the whole station** — an in-universe technical readout, drawn by the art department.
Its authority is **2**: it is production material, and it is a *different* production document from
`01-station-exterior/exterior more.jpg`, on which C-007's ruling currently rests alone.

Orientation is fixed by reading it against `00-MASTER.md` §2: the finned reactor barrel is at the
**left**, the long thin communications masts and the fore cap at the **right**. Aft left, fore right.

### What it shows

1. **Six radiator blades — three above the spine, three below.** In a pure side elevation, blades
   lying edge-on would draw as lines. These are drawn **full-face**. That is only possible if the
   blades lie in a single plane containing the long axis.

   This is exactly the C-007 ruling — **6 coplanar blades** — reproduced independently, in an
   in-universe diagram, from a different production artefact. C-007 was a single-source ruling
   until now. It no longer is.

2. **Each blade is a two-limbed fork.** Two long limbs splay apart at the hull root and converge
   outboard to a **small rectangular end pad**. This is new geometry: the current
   `planar_blades` component is a plain plate.

### The candidate reconciliation of the count of 12

C-007 already argues that `Exterior map.jpg`'s "Reactor Cooling Fins (12)" counts faces or panels,
not radial positions, and the session-2q note adds that the rosette's fins may be a *different*
system from the blades. The fork geometry offers a third, simpler possibility:

> **Six two-limbed forks = twelve limbs.** A draughtsman counting limbs off this profile would
> write 12 and be describing exactly the arrangement C-007 ruled for.

**This is logged as a hypothesis, not adopted.** It is attractive because it needs no reinterpretation
of the word "fins" and no second system, but a wireframe on a set graphic is a stylised readout, and
"12 limbs" is a count I derived by multiplying, not one anybody wrote down. It would be adopted if a
production orthographic or the uncropped Security Manual sheet showed the fork geometry with the
limbs labelled or numbered.

**Ruling: unchanged. C-007 stays RESOLVED at 6 coplanar blades.** Two changes are authorised by
this note, neither of which touches the ruling:

- The `planar_blades` component may be given the **fork profile** — two limbs from a splayed root
  converging to an end pad — since that is now sourced at authority 2 and the current plain plate
  is not sourced at all.
- The "12" reconciliation in C-007's text may cite this as a third candidate alongside the two
  already there.

### Two further exterior facts from the same wireframe, recorded here because they have nowhere else to go

- **A dorsal row of about six small square modules on a rail** runs aft-of-centre along the spine,
  with six leader arrows taking them to callout boxes headed **"AUTO LOADERS SEQUENCE"**. This
  corroborates the "cargo modules run along a **dorsal line**, not around the circumference"
  correction already applied from `exterior more.jpg`, and it suggests those dorsal modules are
  **auto-loader positions** — a function for a component we currently place without one.
- **Four ventral callouts on the fore drum are labelled "ATMOSPHERIC LIFE SUPPORT REGULATORS."**
  A named subsystem, with a count of four and a face of the hull. Not currently in
  `00-MASTER.md` §2's aft→fore list; it belongs between items 12 and 16 if it is added.

---

## C-003 — session 2s note: the drum interior, resolved properly for the first time

### The source

`reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp` (1080×817,
**authority 1**, on-screen footage). A room with a **large multi-pane window looking directly into
the rotating habitat drum**. It is filed under characters because of who is standing in it; the
window is the reason it matters.

### What it settles about the drum, independently of any sector question

The session-2r note on `04-sector-red/Earhart's.webp` reported "two splayed support struts banded
with orange rings meeting a hanging structure on the axial spine", and flagged that the drum-side
read there was low-contrast and leaned on the glazed tower. **This frame resolves that structure
directly, at much higher contrast:**

- **Two axial support struts** rise from the drum wall and splay toward the centreline. Each is a
  **segmented cylinder** — about **four pale grey barrel sections separated by three or four dark
  collar joints**, with a **salmon / pale-orange collar at each joint** and a **fatter capsule
  swelling near the wall end**.
- **The bands are joints, not decoration**, and the colour is **salmon**, not orange. Both of those
  correct the 2r description in detail while confirming it in substance.
- **The far side of the drum arches overhead and fills the top of frame.** Its surface is divided
  into **long continuous longitudinal bands running parallel to the axis** — greys and
  olive-greens with one broad orange-red band — carrying rows of **small blue rectangular lights**
  and thin pale lines. The bands run the whole visible length: **strips, not tiles.**
- **On the near floor, a low-rise built district**: large flat-roofed grey rectangular buildings,
  paved plazas, a stepped terrace edge. **Buildings stand on open ground.**

### What it does and does not do for C-003

**It corroborates.** The 2r note's weakest link was that the "far side of the drum overhead" was a
dark, low-contrast field that "could be a painted backdrop of anything". Here it is not dark, it is
not low-contrast, and it is unmistakably the interior of a rotating cylinder with terrain wrapping
overhead and axial struts crossing the view. **The drum-interior reading that both the Earhart's
and Fresh Air frames depend on is now independently secure.** That strengthens the pointers on
both sides of the 2r observation — the one that put Earhart's (Red rosette) in the drum and the one
that put Fresh Air (Green rosette) in the drum. It does not break the tie between them; it makes
the tie firmer.

**It does not resolve.** No sector name, no colour coding, no signage of any kind appears in the
window or the room. It adds one more pointer to the drum's *architecture* and **zero** to the
question of which sector the drum belongs to.

**Ruling: unchanged. C-003 stays OPEN and BLOCKING** on the narrow question it has been reduced
to — the **Green/Brown transposition**: sectors are longitudinal bands, and the two authority-3
sheets disagree about which band is the ~2,000 m habitat drum. This frame shows the drum's
*interior* beautifully and says nothing whatever about its *longitudinal position or sector name*,
which is the only thing still in dispute. What would close it is unchanged: **any source placing
the Garden or Downbelow in a named sector at a longitudinal position** — an uncropped scan of the
Security Manual sheet, a numbered deck plan, or dialogue.

---

## C-004 — session 2s note: a negative result, and one structural constraint

### The negative result, stated plainly so it is not re-derived

**No level number, no lift-car display, no deck plan and no sector name appears in any of the 28
files in `12-starfury`, `14-characters-and-uniforms` or `15-races-and-makeup`.** Every file was
opened. C-004's specific ask — a lift display, a deck plan, or dialogue tying a level number to a
gravity or a placeable location — is not answered anywhere in these folders.

Together with the same finding from session 2r for `01-station-exterior`, `03-sector-blue` and
`04-sector-red`, **six of the twenty-two reference folders are now known to contain no level
indicator at all.** The remaining candidates are `02-station-cutaways-and-plans`,
`09-garden-core-and-transit`, `10-interiors-generic-kit`, `16-signage-typography-ui` and the
unsorted dump.

### The one structural constraint this pass does add

From `talia-winters in gorgeous office.webp` (authority 1, described in the C-003 note above):

> **The innermost surface of the drum is open ground.** Multi-storey buildings stand *on* it, with
> paved plazas and a stepped terrace between them, and the far side of the drum is visible directly
> overhead with nothing between. There is **no deck soffit, no ceiling plane and no stacked
> structure above the drum floor** — the volume is open to the axis.

C-004's *axis* is already settled — a level is a concentric radial deck. This constrains that
settled axis rather than reopening it:

- The radial stack **terminates at the drum floor**; it does not continue to the axis. The
  innermost deck's ceiling is the **open drum volume**, not another deck. So the number of radial
  levels is bounded by the **wall thickness between the outer hull and the drum floor**, not by the
  drum radius. That is a hard upper bound on any level count, from footage, and it is worth having
  before deck spacing is ever chosen.
- It says nothing at all about **which end of that stack is numbered 1**, which is the one question
  C-004 has been reduced to.

**Ruling: unchanged. C-004 stays OPEN and BLOCKING** on the numbering convention. The constraint
above may be used when the radial stack is eventually parameterised; it does not license building
it, and it does not substitute for the lift-car display, numbered deck plan or dialogue that C-004
actually needs.

---
---

# Session 2t — verification pass: two corroborations are weaker than written

This session did not catalogue anything. It re-opened a sample of the 2r/2s entries and checked
them against the frames. **The sweep holds up and nothing below reopens a settled question.**
Two supporting arguments are weaker than the notes above state, and one count needs a
qualification. All three are recorded here rather than edited into the notes, so the reasoning
that produced them stays visible.

**Nothing here changes a ruling. C-003 and C-004 stay OPEN and BLOCKING. C-007 stays RESOLVED.**

---

## C-004 — the "authority-2 corroboration of the Blue rosette" should be discounted, on two grounds

`C-004 — session 2r note`, §2 above, offers `01-station-exterior/exterior more.jpg`'s **fore end
view** as authority-2 corroboration of `other map.png`'s **Blue rosette**, and concludes "**two of
the six rosettes now have independent corroboration**", which "further licenses reading the
rosettes as topology". Both halves of that fail.

**Ground 1 — an exterior end-on view is not evidence about interior topology.** The fore end view
was re-opened at 8× in this pass and the description in the index is accurate: concentric bands,
dark cruciform hub, red centre lamp, cog-toothed ring, silver annulus, blue panelled annulus,
toothed rim. But that is the **outside of the docking structure, seen along its axis.** *Any* body
of revolution photographed end-on presents concentric bands, because hull panelling on a
rotationally symmetric surface projects to rings. The Blue rosette is an **interior
cross-section** asserting that habitable decks are concentric annuli. The end view constrains hull
panelling, not deck arrangement. It cannot corroborate the rosette because it is not evidence
about the thing the rosette claims.

Contrast this with the Green case, which is sound and is untouched: there the corroborating source
(`Babylon_5_2-22_34b.jpg`) is a view **down the inside** of the drum, so it is evidence about the
same quantity the rosette describes.

**Ground 2 — the source is not independent of `other map.png`'s family, and may not be
authority 2 at all.** `exterior more.jpg` is rated 2 on the stated grounds that its projections
are "orthographic renders of the production CGI model". That provenance was asserted, never shown.
This pass tested it against `02-station-cutaways-and-plans/other map 4.jpg` — the **Lawrence D.
Miller "SHEET 2: TOP VIEW"** plate, © 2004, 2014 Lawrence D. Miller, **authority 4**, and the sheet
family `00-MASTER.md`'s specification table and the k = 2.5891 rescale both come from. Miller's two
inset renders are **the same 3D model** as `exterior more.jpg`, on four checkable features:
royal-blue tapered-lozenge blades with pale borders; a dorsal row of brick-red cargo modules
(six, counted); a fore end disc of concentric bands with a red centre lamp; and the same
lavender-over-grey hull palette. Full working in `reference/00-INDEX.md`, session 2t.

That does not prove the model is fan-built — Miller credits licensed Warner/PTN imagery on the
sheet. It does prove **`exterior more.jpg` and the Miller sheets are one source, not two.**

**Ruling: the count in `C-004 — session 2r note` §2 should read "one of the six rosettes has
independent corroboration", not two.** Everything else in that note stands, including the drum
end-cap circle fit (which this pass did not re-run but which is offered with its method and its
residuals, and is checkable). **C-004 stays OPEN and BLOCKING** on the question it has been reduced
to: which ring is Level 1.

---

## C-007 — the ruling stands, and `Sheridan.jpg` is now the *better* of its two sources, not the second

`C-007 — session 2s note` says C-007 "was a single-source ruling until now" and that
`reference/14-characters-and-uniforms/Sheridan.jpg` supplies "a **second, independent
authority-2 source**".

The Sheridan wireframe was re-opened at 5–7× in this pass and **it shows what the note says it
shows**: three two-limbed forked blades above the spine and three below, each splayed at the root
and converging to a small rectangular end pad. That is confirmed, and it is genuinely independent
of `exterior more.jpg` — it is a set graphic photographed on a studio stage, nothing to do with the
Miller sheet family.

What changes is the relative weight of the two. Given the finding above, **`exterior more.jpg`'s
provenance is unestablished and may be authority 4**, so C-007's original ruling rested on a source
weaker than it was rated. `Sheridan.jpg` is the firmer of the pair: a production still, on a
production set, of an art-department drawing. **C-007's evidence is not two authority-2 sources; it
is one reasonably firm authority-2 source and one of contested provenance that happens to agree.**

That is still enough. **C-007 stays RESOLVED at 6 coplanar blades**, and the fork profile remains
authorised for `planar_blades`, because it is now the *only* radiator geometry sourced from
anything whose provenance we can name.

**Two caveats on the coplanarity inference, so it is not over-read later:**

- The wireframe is **not a pure orthographic side elevation.** The dorsal auto-loader modules show
  their top faces, so the view carries a few degrees of elevation. The coplanar reading survives
  this — a 60°-spaced radial array of six blades would foreshorten visibly from that angle and none
  of the six does — but the note's premise "in a pure side elevation, blades lying edge-on would
  draw as lines" is stronger than the drawing supports.
- `02-station-cutaways-and-plans/Exterior map.jpg` (authority 4, uncatalogued until now) draws the
  cooling fins as blades above **and** below the spine in a side view. Same arrangement, lower
  authority, and it is the source of the "(12)" that C-007 has to reconcile — so it is a
  consistency check, not new evidence.

---

## C-007 / `00-MASTER.md` §2 — the "ATMOSPHERIC LIFE SUPPORT REGULATORS" count needs a qualification before it is written into the master

`C-007 — session 2s note` closes with: "**Four ventral callouts on the fore drum are labelled
'ATMOSPHERIC LIFE SUPPORT REGULATORS.'** A named subsystem, with a count of four and a face of the
hull. … it belongs between items 12 and 16 if it is added."

The index entry for `Sheridan.jpg` discloses the discrepancy — "(three leadered arrows, four
boxes)" — but this note does not, and this note is the one that authorises writing a count into
`00-MASTER.md`. Re-read at 7× in this pass:

- There are **four boxes** and **three pink leaders** reaching the ventral hull. The second box has
  a pale chevron and no leader.
- The four boxes are drawn in the **same graphic language as the six AUTO LOADERS boxes** — small
  rectangles carrying chevron glyphs, one of each set shown in a different state. They are
  **indicator lamps on a status board**, not callouts to four counted hull fittings. The AUTO
  LOADERS set gets away with it because its six boxes have six leaders landing on six visible
  dorsal modules; this set does not.
- The three leaders land on the ventral surface at the **fore end of the ribbed drum**, not on a
  separate "fore drum".

**Do not write "Atmospheric life support regulators (4)" into `00-MASTER.md` §2 as a component
count.** What is sourced is: *a named subsystem, "atmospheric life support regulators", monitored
on the C&C board in four channels, with three of them leadered to the ventral hull at the fore end
of the habitat drum.* If it goes into §2 it should go in with that wording, and it should be
logged in `canon/INVENTIONS.md` if the count of four is ever used as a geometry count.

---

## C-004 — a structural consequence of the ring radii, bearing on the numbering

Generating the ring geometry (session 2u) produced a fact the rosettes do not state and that
narrows what "level 1" can mean.

With ring 1's floor anchored at the canon **278.3 m** and the rosette ring fractions applied,
the rings in the habitat drum come out **38–61 m deep**:

| Ring | Floor radius | Depth | Floor gravity |
|---|---|---|---|
| 1 | 278.3 m | 50.1 m | **1.000 g** |
| 2 | 228.2 m | 61.2 m | 0.820 g |
| 3 | 167.0 m | 61.2 m | 0.600 g |
| 4 | 105.8 m | 55.7 m | 0.380 g |
| 5 (core) | 50.1 m | 50.1 m | 0.180 g |

**A 50 m ceiling is not a deck.** So the rosette rings are not individual decks — each is a
**zone containing many decks**. At a 3–4 m deck pitch a ring holds roughly 12–17 of them.

This matters for C-004 because it removes an objection. "Grey 17" seemed to imply seventeen
concentric shells, which looked implausible against five drawn rings. Under this reading
seventeen is an ordinary deck number **inside** a zone, and five rings and seventeen levels
stop being in tension.

**It does not resolve C-004.** Whether numbering runs outward-in or inward-out is untouched.
But it does mean the numbering, once known, indexes **decks within rings**, not rings.

Also worth recording: **ring 1's floor gravity comes out at exactly 1.000 g** without being
fitted to. The radius came from canon and the rotation rate was solved from it in session 1;
the ring fractions came independently from the rosettes. That they agree is a genuine
cross-check rather than a construction.

---

## Note — the "two drum end caps" was a misreading, not a conflict

**Status: withdrawn. Never assigned a C-number; recorded here so it cannot be re-raised.**

The 2r reference sweep flagged that two structurally different drum end caps appeared across
frames: `03-sector-blue/Babylon_5_2-22_34b.jpg` showing a panelled grey disc of concentric
annular courses, and `Babylon_5_2-22_33a.jpg` showing a deep red-orange open triangulated
lattice. It sat in STATE.md as blocking work on the drum's ends.

They are two different **structures**, not two versions of one.

`Babylon_5_2-22_35a.jpg` — from the same sequence, and never examined until now — is shot
**forward through the windscreen of a drum tram**, past a seated passenger. Through the glass
the red-orange triangulated lattice recedes to a vanishing point with regularly spaced
transverse ribs and a pale conduit running along it. That is the geometry of a **guideway**, not
of a bulkhead: a bulkhead does not have a vanishing point.

Read back into `33a`, the lattice is overhead and close, and the frame also contains the
concentric ribbed disc — lower right, lit warm and dark rather than grey, which is why it was
not matched to `34b` on first pass. Magnifying that region shows the same radially ribbed,
concentrically banded dished cap, with the drum's ground running up to its rim and a
circumferential road following the boundary.

So:

- the **end cap** is the concentric ribbed dished bulkhead, and it is the only one. Its
  measurements are already recorded above under "C-004 — session 2r note: the drum end cap,
  measured", and it is now built by `station/interior.py:drum_end_cap()`.
- the **red-orange triangulated lattice** is the longitudinal **tram guideway truss** running
  the drum's length, carrying the tram cars visible slung beneath it in both `33a` and `34b`,
  with the drum's lighting mounted along its underside. Not yet built.

**Lesson, and the reason this is written down rather than quietly deleted:** the flag came from
comparing two frames without looking for a third. `35a` was filed, catalogued and indexed the
whole time. Two references disagreeing is evidence that a third is needed, not evidence of a
contradiction — the same shape of error as reading a label leader line as hull, or a count of
twelve radiators as a radial arrangement.

**One thing this does newly establish:** the drum is lit from **longitudinal light runs mounted
on the guideway trusses**, not from an axial sun-strip and not from the end caps. `34b` shows
the bright tubes running alongside the truss; `33a` shows a row of rectangular fixtures on the
truss's underside. That is authority 1, and it is the first sourced answer to what lights the
habitat.
