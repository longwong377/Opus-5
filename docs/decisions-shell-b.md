# SHELL B — the decision, what it generates, and what would overturn it

*Session 4u. Builder: `station/shell_b.py`. Gate: `python3 station/shell_b.py --selftest`
(11 claims), control: `--selftest --legacy` (4 of the 11 fail). Not a plan document — it
records one decision and its measurements. `docs/spec/PLACES.md` §2 stays the authority on
what Shell B IS; nothing here amends it.*

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

`python3 station/shell_b.py --plan`

| belt | decks | generated m² | annex m² | ratio | dwellings |
|---|---|---|---|---|---|
| SHB-01 Blue r0 crew country | 8 | 94,267 | 93,700 | 100.6% | 3,720 |
| SHB-02 Blue r1 dockers | 4 | 172,400 | 172,400 | 100.0% | 7,680 |
| SHB-03 Red r0 market back-of-house | 13 | 28,001 | 28,000 | 100.0% | 0 |
| SHB-04 Red r1–2 civilian mass | 32 | 3,747,126 | 3,706,900 | 101.1% | 184,020 |
| SHB-05 Red r3 plant support | 12 | 14,000 | 14,000 | 100.0% | 0 |
| SHB-06 Green r0 diplomatic/rosette | 8 | 369,700 | 369,700 | 100.0% | 14,160 |
| SHB-08 + 08.f Grey r0 industrial + refugee | 23 | 199,800 | 199,800 | 100.0% | 13,000 |
| SHB-09 Yellow worked nodes | 1 | 12,000 | 12,000 | 100.0% | 0 |
| **total** | **101** | **4,637,295** | **4,596,500** | **100.89%** | **222,580** |

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
warm, a deck is **0.1–0.4 s**. The whole 101-deck shell is under a minute of CPU.

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
  column and are PLC-028/089 places, not belts. Adding them to the 4,637,295 above gives
  **5,147,045 m² ≈ the §4 headline of ≈5.12 M m²**, which is the check that nothing is
  missing between the two tables.
- **101 of 251 decks.** The belts as specified do not reach Blue rings 2–3, Grey rings 1–3,
  or most of Yellow — 148 decks. That is the spec's own decision (SHC-05's plant-zone void,
  SHC-07's undecked aft flanks), not an omission here, and it is worth stating plainly
  because "Shell B covers the empty decks" is the sentence a future session will otherwise
  believe.
- **No NPCs, no dressing, no props, no audio, no signage, no lighting rig, no navmesh.**
  A Shell B deck is architecture. Everything that makes it inhabited is a later pass.
