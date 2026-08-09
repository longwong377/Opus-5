# SHELL B — the decision, what it generates, and what would overturn it

*Sessions 4u–4v. Builder: `station/shell_b.py`. Gate: `python3 station/shell_b.py --selftest`
(**12 claims**), control: `--selftest --legacy` (**5 of the 12 fail**). Not a plan document — it
records one decision and its measurements. `docs/spec/PLACES.md` §2 stays the authority on
what Shell B IS; nothing here amends it.*

> **4v CHANGED THE DECK COUNT, AND EVERY FIGURE BELOW THAT SAYS 101 DECKS IS STALE.**
> The live numbers are **86 decks**, **4,636,727 m²**, **222,580 dwellings**. §9 is the
> new section and it supersedes §4's deck column. Nothing else in this file moved:
> the dwellings, the belts, the gross and the per-m² costs are unchanged.

---

## 1. The finding

`docs/spec/PLACES.md` §2 commits the station to nine residential belts and one lettered
annexe: **222,580 dwellings** — 209,580 block units plus 13,000 refugee partitions — at
**≈4.60 M m² gross**, which is **89% of the station's housing**. The other 11% is the 7,150
units inside named PLC places and the 20,390 lurkers in Grey's camps.

There was no builder for any of it. `ls station/ | grep -i resid` returned nothing;
`grep -rn shell_b station/*.py` outside `spec_harness/` returned nothing. The 29 SHB spec
rows were GREEN because `station/spec_harness/shb.py`'s own docstring says so in terms:

> *"Nothing in that chain needs a built station … there is no Shell B builder in the
> project at all: no module under `station/` assigns block program to a deck cell, so the
> 3,720 units of SHB-01 exist as a number and nowhere else."*

Measured this session: **251 decks in the ring stacks, 71 carry a named place.** The other
180 — 72% of the station — had no geometry of any kind.

## 2. The decision, and the alternative it beat

**Generate Shell B procedurally, at low detail, from the annex.** Set by the owner.

The alternative was to narrow the promise to the 129 named landmarks and let the rest be
structure. It was rejected on CLAUDE.md's brief: *"the simulation exists around you rather
than in text."* A station where 250,000 residents have `resident.home_for` addresses and no
doors is a station that exists in text. The addresses are already generated — `arrival.py`
issues NN-L unit labels through the customs pipeline — so the choice was between building
what those labels point at and shipping labels that point at nothing.

**Low detail is the price that makes it possible, and it is stated as a number rather than a
feeling.** Shell A (`rooms.build`) spends **25,740 triangles on one bay** of a docking bay,
and the 128 named places cost 19.6 M triangles between them. That vocabulary applied to
4.6 M m² is tens of millions of triangles of corridor nobody has a reason to stand in. So
Shell B emits **boxes and quads only** — no `articulate()`, no `dressing.py`, no props, no
baked bodies. It buys one thing: a resident's door is where their card says it is, it opens,
and there is a floor behind it.

## 3. What it does not invent

Hard rule 4 — one authoritative model — decides four things, and all four are read rather
than restated:

| | source | why not restate it |
|---|---|---|
| unit dimensions | `quarters.unit_dims()` | the INV-032 ladder areas the annex quotes (34/18/46/22/16/9 m²) **are** `quarters.CLASSES`' areas. A Shell B unit is the same room a Shell A quarters unit is, at less detail |
| corridor width, wall, door | `interior_kit.PROVISIONAL` | a body crossing from a Shell A corridor into a Shell B one must feel no step |
| deck, radius, cell plan | `interior.decks_in_ring` / `ring_cells` | the same functions the Shell A deck builder uses |
| block counts, unit areas, per-deck programs, gross areas | **parsed out of `docs/spec/PLACES.md`** | `spec_harness/shb.py`'s own rule one level down: *"a constant copied into a harness cannot disagree with the row it checks."* The same is true of a builder — one that restates the spec cannot be caught building the wrong thing |

The parse is measured, not loosened. A belt whose program clause does not read raises rather
than building an empty deck, and the residue check refuses any leftover `<number> <word>`.
It fired twice while this was written, both times correctly: on SHB-09's *"At the 4 worked
nodes"* (a lead-in, not four rooms) and on SHB-05's trailing camp-fringe sentence.

## 4. What it generates, measured

`python3 station/shell_b.py --plan` — **the deck column and the total are as of 4v; the two
rows 4v moved are marked, and §9 says why.**

| belt | decks | generated m² | annex m² | ratio | dwellings |
|---|---|---|---|---|---|
| SHB-01 Blue r0 crew country | **4** (was 8) | 93,700 | 93,700 | 100.0% | 3,720 |
| SHB-02 Blue r1 dockers | 4 | 172,400 | 172,400 | 100.0% | 7,680 |
| SHB-03 Red r0 market back-of-house | 13 | 28,001 | 28,000 | 100.0% | 0 |
| SHB-04 Red r1–2 civilian mass | 32 | 3,747,126 | 3,706,900 | 101.1% | 184,020 |
| SHB-05 Red r3 plant support | 12 | 14,000 | 14,000 | 100.0% | 0 |
| SHB-06 Green r0 diplomatic/rosette | 8 | 369,700 | 369,700 | 100.0% | 14,160 |
| SHB-08 + 08.f Grey r0 industrial + refugee | **12** (was 23) | 199,800 | 199,800 | 100.0% | 13,000 |
| SHB-09 Yellow worked nodes | 1 | 12,000 | 12,000 | 100.0% | 0 |
| **total** | **86** | **4,636,727** | **4,596,500** | **100.88%** | **222,580** |

**Dwellings, gross and blocks are unchanged by the cap**, which is the point of capping at
belt level: `_split_evenly` sums to the belt total whatever the deck count, and `deck_slots`
shares the belt's gross by units-on-this-deck rather than by deck index. SHB-01's ratio
actually *improved*, 100.6% → 100.0%, because 62 blocks divide 16/16/15/15 over four decks
where over eight they divided 8/8/8/8/8/8/7/7 and the flat-share residue showed.

**Dwellings are exact**: 209,580 units + 13,000 partitions, against the annex's own
209,580 and 13,000. Not approximately — the split of a belt's blocks over its decks is
`_split_evenly`, which sums to the total by construction.

### Triangle cost

One deck of SHB-04 — `red/1/5`, the densest belt in the station — measured directly:

```
  radius 201.80 m, 1268 m around, 18 streaming cells, gravity 0.73 g
  96 blocks x 60 units, 37 rooms, 2 bands, 201 m deep in z (sector has 369)
  area          117300 m2 built  (blocks 111668 + rooms 1754 + corridor 3878)
                116029 m2 the annex states for this deck
  capacity        5760 dwellings
  triangles    189,800 render (lod 1), 5,056 collision (2.7%)
  per m2          1.62 render tri/m2, 0.043 collision tri/m2
```

Over a nine-deck sample spanning all eight belts, and extrapolated by each belt's own
measured rate:

| | |
|---|---|
| render | **7,420,184 tri** at **1.60 tri/m²** |
| collision | **242,007 tri** at 0.052 tri/m², **3.3% of render** |
| worst single streaming cell seen | **24,798 tri = 8.3%** of `budget.DECK["visible_all_tris"]` (300,000) |
| range across belts | 0.65 tri/m² (Yellow, thin by design) to 2.63 (Red r0 back-of-house) |
| at `--lod 0` (doors only, units sealed) | **0.75 tri/m²** — 54% cheaper |

For scale: the 128 Shell A places are **19.6 M triangles**. Shell B adds **38% more
triangles for 36× the floor area**, because it is the same station built at a
fifteen-hundredth of the detail per square metre.

**Nothing is committed as mesh.** `station_plan()` is metadata; geometry comes from
`build_deck()` / `build_cell()` on demand — `interior.cell_manifest`'s architecture and ADR
0003's rule, *the repository stores the rule rather than the result*. A cold build of one
deck is ~20 s, of which ~19 s is the one-off ray cast that measures the collision profile;
warm, a deck is **0.1–0.4 s**. The whole 86-deck shell is under a minute of CPU, and
`station_plan()` — every deck's metadata, including 4v's sector fixed point — is **0.87 s**.

## 5. The four decisions inside the build that were not obvious

Each was found by a number moving, and each is recorded because the wrong reading was
defensible.

**a. A belt's per-deck gross follows its content, not its index — worth 4.4%.** SHB-01 puts
62 blocks on 8 decks: 7.75 each, so six decks carry 8 and two carry 7. A flat
`gross / n_decks` charged every deck for 7.75 blocks while building eight. It read as a
geometry problem ("the blocks are too big") and was an accounting one.

**b. The ring corridor is charged for the arc it serves, not the circle — worth 5%, and 82%
of one belt.** Grey ring 0 is 2,735 m around, so a closed ring corridor is 7,110 m² against
that deck's whole 8,687 m² budget. An arc with no slot on it is not Shell B: §3 SHC-11
already owns unbuilt ring fabric, *"capped / sheeted / welded-shut openings, stencilled
UNCOMMISSIONED"*.

**c. The refugee overspill is halls, not 13,000 doors — and the annex's own ×1.4 proves it.**
Laid as individually-doored 9 m² rooms, SHB-08.f needs 1,384 m of arc for the partitions and
353 m of gaps, and the corridor to reach them is 4,680 m² against a whole-deck budget of
8,687. The ×1.4 factor allows **0.28 m² of circulation per partition** — not enough corridor
to reach one. The row's own words are *"partitioned converted-cargo volume … communal
standpipes"*, so a hall of 60 partitions off one spine is both the right reading and the one
that fits. 60 is `arrival.py:573 UNITS_PER_BLOCK`, which the derivation paragraph already
makes normative.

**d. The communal wash room is part of the block — worth 0.7%.** SHB-01 and SHB-04 write
`wash room per block`, not a count per deck like every other room they list, and the
derivation paragraph says *"each block gets a communal wash room."* Laid as its own ring slot
it cost SHB-04 96 extra doors on the ring per deck and 374 m of arc to reach them. It now
sits at the quiet end of the block's own spine, which is where a resident meets it — the
class texture the same paragraph names.

## 6. Integration — the exact change, NOT applied here

`station/shell_b.py` is **not on the shipped path**, by instruction. It is the project's
signature defect — *finished, tested machinery with no caller* — knowingly incurred, and
`python3 tools/wiring.py --selftest` names it: `shell_b  station/shell_b.py`, orphaned.
Nothing renders it until the change below lands.

**`tools/export_station.py :: work_list()`** (the function at line 70) enumerates decks from
`routes.clusters()` — *"every deck that CARRIES A LOCATION"* — which is the 71. Shell B owns
the other 180.

After the `decks[k[:3]].append(k[3])` loop and before `rings = ...`:

```python
import shell_b as SHB
schema, profile = it.load()
for row in SHB.station_plan(schema, profile):
    key = (row["sector"], row["ring"], row["deck"])
    if key == (DRUM_SECTOR, DRUM_RING, DRUM_DECK):
        continue
    decks.setdefault(key, [])          # a Shell B deck has no cluster z
```

and in `main()`'s per-deck loop, where `D.build_deck_clusters(...)` is called (line 273):

```python
if not decks[k]:
    V, T, G, st = SHB.build_deck(schema, profile, sec, ring, dk)
    cv, ct, cmeta = SHB.deck_collision(schema, profile, sec, ring, dk)
else:
    V, T, G, st = D.build_deck_clusters(...)          # unchanged
```

`st` carries `blocks`, `units` and `built_m2` for the manifest row; `deck_collision` returns
`meta["groups"]` in the span form `_write` already expects.

**Nothing else changes.** Group names carry an existing bound tail
(`shb_unit_qtr_wall` → `qtr_wall`) and `materials.resolve` is a substring match, so no edit
to `materials.py` is needed — a Shell B corridor wall is the same panel as a Shell A one and
should be the same material by construction. `_sidecars`' `_tail()` already strips the
`z<int>__` prefix this module emits.

## 7. What would overturn this

- **A frame.** Nothing here has been rendered. Every claim in §4 is a triangle count, a
  square metre and a ray cast; **not one is a craft claim**, and CLAUDE.md's rule is that a
  craft claim cites an engine frame at the rubric's half distance. The most likely verdict
  from the first honest frame is that a block spine at 1.6 tri/m² reads as the *"shitty
  little cubes"* the owner rejected in session 3r, and that the answer is a third detail
  tier between Shell A and this — `--lod 2`, with articulation on the first bay of a block
  only. The hooks are there (`lod` is a parameter on `block()` and threads through
  `build_deck`); the tier is not.
- **A walk test.** `station/walkable.py` has never been run on a Shell B deck. The collision
  shell is measured (`block_profile()` ray-casts the emitted block, and reports half width
  **1.240 m** against the 1.300 m the kit is written down as, so it is genuinely reading the
  skirt) and it is built from `collision.room_shell`, which is the module that already got
  the aperture rule and the winding right — but *"a static scan can tell you a caller exists;
  only running the thing tells you the caller runs."*
- **The spec moving.** Every number is parsed at run time, so a `SPEC-CHANGE` entry in
  `docs/spec/PLACES.md` flows straight through — except a belt gaining a room noun the
  `PROGRAM_WORDS` vocabulary does not know, which raises rather than silently dropping it.
  That is deliberate and it is the behaviour to keep.
- **C-012.** `docs/spec/PLACES.md` §4 already flags it: *"C-012 (souls/day ×3.6) rescales
  SHB-04's transient block count."* If SYS-02 resolves it upward, SHB-04's 706 transient
  blocks move and this builder follows the annex without being edited.

## 8. What is NOT built, stated rather than absorbed

- **SHB-07 (Green ring 1, drum support — 9,500 m²): zero decks.** Green ring 1 is the habitat
  drum, `kind == "open"`, and stacks no ring decks at all — `station/deck.py` refuses it for
  the same reason. Its six bothies, two tram depots, three pump houses, barn and cold store
  belong on the drum floor, which `drum_ground.py` / `garden.py` own. **This builder cannot
  place them and does not pretend to.**
- **SHB-09 resolves to one Yellow deck, not four.** The row names PLC-097/098/119–124 and
  `_node_decks` resolves those register rows to a single distinct `(sector, ring, deck)`.
  The belt's 12,000 m² is built there. Whether the four *worked nodes* are four decks or one
  is a register question, not a builder question.
- **Grey's camps (509,750 m² @25 m²/person, 20,390 lurkers)** are in §4 TOTALS' Shell B
  column and are PLC-028/089 places, not belts. Adding them to the 4,636,727 above gives
  **5,146,477 m² ≈ the §4 headline of ≈5.12 M m²**, which is the check that nothing is
  missing between the two tables.
- **86 of 251 decks** (101 before 4v). The belts as specified do not reach Blue rings 2–3,
  Grey rings 1–3, or most of Yellow — and after 4v they do not reach the *outer* decks of
  Blue ring 0 or the *inner* decks of Grey ring 0 either, because the hull does not leave
  them over those belts' own z. That is partly the spec's own decision (SHC-05's plant-zone
  void, SHC-07's undecked aft flanks) and partly a fact about the ship, and it is worth
  stating plainly because "Shell B covers the empty decks" is the sentence a future session
  will otherwise believe.
- **No NPCs, no dressing, no props, no audio, no signage, no lighting rig, no navmesh.**
  A Shell B deck is architecture. Everything that makes it inhabited is a later pass.

---

## 9. SESSION 4v — FIFTEEN DECKS WERE AT A RADIUS ANOTHER DECK ALREADY HAD

Shell B went on the shipped path, a Windows build ran 48.8 minutes and 126 decks, and
step 6 of 9 refused:

```
merge_cells: derived deck headroom below 2.0 m ... median 3.600
  -- floor radii are not one per deck and a band this thin is a fall through the world
```

**The refusal is correct and was not weakened.** `tools/merge_cells.py::deck_headroom`
derives streaming residency as a *containment test on radius* — a deck floor is opaque, so
a deck occupies the band from its own floor radius inward to its neighbour's — and it needs
one radius per deck. It refused rather than emitting the convenient reading, which is
exactly what a gate is for; it found this on its first real run.

### The cause, in one line of code

`deck_slots` read `decks_in_ring(...)[min(deck, len(decks_list) - 1)]`. The belts claim
their decks against the ring at the sector's **widest** cylinder; the radius was taken from
the ring as the **hull** leaves it, which is a shorter stack. Every deck index past the end
of the shorter stack resolved to its innermost radius:

| ring | decks planned | distinct radii | the decks that collided |
|---|---|---|---|
| blue ring 0 | 8 | **4** | 5, 6, 7, 8, 9 — all at **179.50 m** |
| grey ring 0 | 23 | **12** | 11 … 22 — all at **390.80 m** |

Fifteen zero-metre gaps. Two decks at one radius *are* one deck.

### And the fixed point that was supposed to prevent it had never run

`deck_slots` carried a documented three-pass hull recursion guarded by `if _pass < 3:` —
and seventy lines above it `for _pass in range(6):` **rebinds the same name**, so `_pass`
was always 5 by the time the guard was read and the recursion was dead code. Every radius
in the module came from pass 0, probed at the sector's own `z0`. It was invisible because
`z0` is the narrow end of most sectors here, so the dead loop's answer was usually the
conservative one anyway. *A parameter and a loop variable sharing a name is a silent
`if False:`.*

### The fix: one stack per ring, one axial station per sector, and a cap that is announced

1. **`ring_stack(sector, ring)`** is now the single source of every radius in the module,
   memoised per `(schema, sector, ring)`. Two decks of a ring can no longer answer from two
   different stacks, so distinct deck indices give distinct radii **by construction**,
   `DECK_PITCH_M` = 3.600 m apart. There is nothing left to clamp: an index past the end
   raises.
2. **`belt_decks` caps the belt** to what the stack holds and **`_split_evenly` redistributes
   the blocks over the decks that remain**. Rule 1's existing spec-sanity raise is unchanged
   (a row naming a deck the ring never stacks at *any* z is still an error); the cap is the
   different question — what the hull leaves over this belt's own z — and it is recorded in
   `caps()`, printed by `--plan`, and asserted on. A belt whose *first* deck is already
   outside what the hull leaves raises instead of building nothing quietly.
3. **`_settle_sector` runs the depth/stack fixed point for real**, at sector level.

### Two things that bound the deepening, both found by a number moving

**One axial station per sector.** Settling each *ring* against its own belt's depth was tried
first. It gave every ring distinct radii — and put **red ring 2 on red ring 3's exact radii**
(101.86, 98.26, 94.66 …), because SHB-04 runs 300 m deep and the hull at that station carries
a ring 2 no bigger than the ring 3 at red's near end. Each ring was individually correct and
the pair was a solid interpenetrating a solid. `interior.ring_radii` partitions the whole
cross-section, so **ring indices are only comparable within one station**; all of a sector's
stacks now come from one `z`.

**A deepening that deletes a ring is refused.** At red's deep station (z 6,687.5) ring 3 does
not stack at all, so adopting it would have silently deleted SHB-05's twelve decks. The rule
is `spec_registry`'s — refuse the ambiguity rather than emit the convenient reading — so the
last station at which every ring the sector's belts name still exists is kept, and `--plan`
prints which one that was:

```
  blue   stacks taken at z 6901.6 m (belt depth 108 m)     grey   z 3397.0 (76 m)
  green  stacks taken at z 3839.0 m (belt depth   0 m)     red    z 6425.0 ( 0 m, deepening refused)
  yellow stacks taken at z    0.0 m (belt depth  56 m)
```

### Before and after, per ring

| ring | before: decks / distinct / min gap | after: decks / distinct / min gap |
|---|---|---|
| blue 0 | 8 / **4** / **0.000 m** | 4 / 4 / 3.600 m |
| blue 1 | 4 / 4 / 3.600 m | 4 / 4 / 3.600 m |
| green 0 | 8 / 8 / 3.600 m | 8 / 8 / 3.600 m |
| grey 0 | 23 / **12** / **0.000 m** | 12 / 12 / 3.600 m |
| red 0 | 13 / 13 / 3.600 m | 13 / 13 / 3.600 m |
| red 1 | 16 / 16 / 3.600 m | 16 / 16 / 3.600 m |
| red 2 | 16 / 16 / 3.600 m | 16 / 16 / 3.600 m |
| red 3 | 12 / 12 / 3.600 m | 12 / 12 / 3.600 m |
| yellow 0 | 1 / 1 / — | 1 / 1 / — |
| **total** | **101 decks, 15 gaps at 0.000 m** | **86 decks, tightest gap 3.600 m** |

Blue ring 0's four surviving radii also moved 2.00 m inward (190.30 → 188.30 and so on),
because blue is the one sector whose fixed point actually deepens: 108 m of belt takes the
probe from z 6,794 to z 6,901.6, where ring 0 stacks six decks with `r_outer` 195.50 instead
of 197.50.

### The gate, shown failing first

Claim 12, `no two decks of a ring share a radius`. **`MIN_HEADROOM_M` is imported out of
`tools/merge_cells.py` rather than restated**, so this gate cannot pass a build that tool
would reject. `--selftest --legacy` withholds the cap *and* restores `min(deck, len - 1)`
*and* pins the probe back to `z0`, so the control is the shipped behaviour of 4u:

```
LEGACY   no two decks of a ring share a radius  FAIL  9 rings, 103 decks, tightest gap
         0.000 m against 2.000 m demanded by merge_cells; NOT DISTINCT:
         [(('blue', 0), 8, 4, [[5, 6, 7, 8, 9]]),
          (('grey', 0), 23, 12, [[11,12,13,14,15,16,17,18,19,20,21,22]])];
         15 gap(s) under the bar

SHIPPED  no two decks of a ring share a radius  PASS  9 rings, 86 decks, tightest gap
         3.600 m against 2.000 m demanded by merge_cells
```

`--selftest` is **0 of 12**; `--selftest --legacy` is **5 of 12** (the four of 4u, unchanged
word for word, plus this one). The legacy run reproduces 4u's numbers exactly — 103 decks,
4,907,466 m², 210,240 units — which is the evidence the control is the old behaviour and not
a different one.

### One deck built from each affected ring

```
blue/0/2   r 188.30 m  1183 m around  18 cells  0.68 g   16 blocks x 60,  11 rooms
           24,181 m2 built == 24,181 m2 the annex states     960 dwellings
           34,668 render tri (lod 1), 1,076 collision (3.1%)   1.43 tri/m2

blue/0/5   r 177.50 m  1115 m around  12 cells  0.64 g   15 blocks x 60,  11 rooms
           22,669 m2 built == 22,669 m2 the annex states     900 dwellings
           32,524 render tri (lod 1), 1,036 collision (3.2%)   1.43 tri/m2

grey/0/11  r 390.80 m  2455 m around  18 cells  1.40 g   19 blocks,       23 rooms
           16,646 m2 built == 16,646 m2 the annex states       0 dwellings (refugee halls)
           30,714 render tri (lod 1), 1,280 collision (4.2%)   1.85 tri/m2
```

`blue/0/5` was the first of the five decks that shared 179.50 m; `grey/0/11` was the first of
the twelve that shared 390.80 m. Both now stand at their own radius, and both hit their
annex gross exactly.

### THE EXPORT WILL STILL BE REFUSED, AND THE REST IS NOT THIS MODULE'S TO FIX

Measured on the merged set `merge_cells` actually sees — Shell A's 71 located decks
(`routes.clusters()` → `interior.ring_cells`) plus Shell B's, Shell A winning the 38 shared
addresses:

| | gaps under 2.0 m | Shell A ↔ A | A ↔ B | B ↔ B |
|---|---|---|---|---|
| before | **25** | 14 | 3 | **8** |
| after | **17** | 14 | 3 | **0** |

**Every Shell B duplicate is gone. Seventeen remain and none of them is in this file.**

- **Fourteen at 0.000 m, entirely inside Shell A.** `grey_0_22, 24, 26, 30, 40, 42, 50, 55,
  60, 65, 70, 75, 80` all sit at **392.05 m**, and `yellow_0_6, 8, 30` all at **133.85 m** —
  because `interior.ring_cells` applies the *same* `min(deck_index, len(decks) - 1)` clamp to
  register deck NUMBERS the ring cannot index. Its own comment documents the clamp and names
  the fifteen places. **This is the identical defect one file over, and it is the larger
  half.** Owner: whoever owns `interior.ring_cells` / `deck.deck_index` / the register's grey
  and yellow deck numbers.
- **Three at 1.250 m, mixed.** `grey_0_18` (A, 406.45) vs `grey_0_7` (B, 405.20);
  `grey_0_20` (A, 399.25) vs `grey_0_9` (B, 398.00); `grey_0_22` (A, 392.05) vs `grey_0_11`
  (B, 390.80). The two shells read grey ring 0 at two different axial stations — Shell A at
  the sector's widest (`r_outer` 471.25), Shell B at z 3,397 (`r_outer` 430.40) — so their
  3.6 m ladders are 1.25 m out of phase. Shell B cannot close this alone: snapping to Shell
  A's ladder would put its outer decks outside the pressure hull over their own z span, which
  is what claim 6 exists to prevent and what cost 14 decks to fix in 4u. **The real fix is
  one radius ladder per ring, shared by both shells**, and it is an `interior.py` change.

### What I could not verify

- **The CI message named `grey_0_1` at 0.000 m and my model does not produce that.** In
  every reading I can take, `grey_0_1` is a Shell B deck at 426.80 m with a clean 3.600 m
  gap. The failing build reported 126 decks where the union of Shell A and Shell B is 134
  before this change, so that run was not the full set and I cannot reconstruct which decks
  it held. The fifteen duplicates I did reproduce are real, are the ones the message's shape
  describes, and are fixed; whether `grey_0_1`'s 0.000 m came from a deck outside my file or
  from a partial build is **open**.
- **Nothing here has been rendered or walked.** Same as §7: no engine frame, no
  `walkable.py`. `station/rooms.py`, `deck.py --sweep`, `budget.py`, `walkable.py` and the
  exporters were all off limits this session.
- **The mixed-shell numbers above come from `interior.ring_cells`, not from a written
  manifest.** They are the radii that function returns for the 71 located decks, which is
  what `export_station` builds from — but I did not run the export and did not read a
  manifest, so an export that transforms a radius between those two points would not be
  visible to me.
