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
