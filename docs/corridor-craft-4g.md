# The corridor — a craft pass on the one piece the whole station is made of

Session 4g. Written by the agent that owns `station/interior_kit.py` and
`station/corridor_dressing.py`.

`interior_kit.corridor_section` is called by `interior.ring_arc` (every ring corridor on 251
decks), by `interior.axial_run` (every axial spine), and its measured profile is what
`station/lift.py` sizes its car from. It is the surface a player looks at for most of any
journey. The owner's verdict on it was *"bare and colorless and undetailed"*.

Every craft claim below cites a frame at the rubric's **half** distance, because session 3r's
lesson is that only the normal distance was ever rendered and 118 locations of blockout passed
layer 2 on it.

---

## 0. The frames the scores are read from

All through `tools/render_godot.sh`, all reporting `renderer: Vulkan 1.4.318 - Forward+ -
llvmpipe`, all on the assembled deck `blue/0/0` with the shipped player camera and lighting.
Nothing differs between a before and an after frame but `station/interior_kit.py`.

| | camera | what it judges |
|---|---|---|
| **normal** | `--at docking_bays` | the corridor as a place: composition, rhythm, depth |
| **half** | `--eye 209.828,0.0,7121.305 --target 210.268,2.2047,7122.60` | the wall build-up as an object, at **2.59 m** |
| **door** | `--at docking_bays --at-offset 6,0 --face docking_bays` | the doorway, which is where a player looks closest |

The half camera is derived rather than chosen. The eye is the `--at docking_bays` standpoint; the
target is a point on the far wall face 2.20 m along the arc, 1.08 m across and 0.45 m down —
eye-to-surface **2.59 m** against the ~5 m at which the same wall reads in the walking view. It is
the band `docs/materials-4f.md` used for its bollard A/B (3.7 m), and it is inside the rubric's
*half*.

---

## 1. The score

Read off the frames, against `docs/AAA-STANDARD.md`'s written descriptors.

| | before | after |
|---|---|---|
| **CRAFT** | **3** | **4** |

**Before — CRAFT 3.** *"Reads as the intended object at its normal distance and falls apart at
half of it. There is a size hierarchy — a primary form, secondary structure, tertiary fittings …
The tertiary tier is generic: the same panel, the same hatch, the same light, repeated without
regard to what the part does."* Every clause is literally true of
`docs/engine-4g-corridor-before-half.png`. The size hierarchy is real and earned — chamfered
section, portal rhythm, skirt / dado / reveal / rail / plate courses, deck grid, light strips — so
it is not a 2. What it is not is a 4: at 2.59 m the wall plates are flat rectangles with square
arrises, the rail band is a white shelf returning one hard specular line, and **there is not one
fitting on the wall in the entire frame**. Three colours in shot: grey, pale green-grey deck,
orange downlight.

**After — CRAFT 4.** *"Holds at every distance the player can reach it from, and the detail is
functional. A fitting is where a fitting would be needed … Wear, grime and lighting response vary
across the surface rather than being uniform. The composition holds."* The clamped services bank
is the descriptor's own example run indoors; the fittings are hatches, junction boxes and
wayfinding rather than scattered greebles; the plates and tiles are drafted so an edge grades
instead of returning a line; the floor strip that gives a corridor its perspective read is lit for
the first time.

**It is not a 5, and the reason is one sentence: the pattern still repeats every 9.205 m.**
`interior.ring_arc` calls `corridor_section` with identical arguments for every section of an arc,
so the fitting schedule cannot vary between them — see §5, which is a one-line patch in a file
this session does not own. CRAFT 5 requires *"nothing in frame repeats in a way the eye can
index"*, and over a 66 m sight line seven repeats are indexable. Before this session the period
was **3.07 m**; it is now 9.205 m, and with §5 applied it becomes the whole arc.

---

## 2. Triangles — the budget is the point, and it went the right way

`station/budget.py` gates `corridor_tris_per_m` at **400**, measured as the marginal rate
`(t20 − t1) / 19` on `corridor_section`.

| | tri/m | % of the 400 bound |
|---|---|---|
| before (4f) | **280.4** | 70.1% |
| after (4g) | **293.9** | **73.5%** |

**+13.5 tri/m, 4.8%, for eleven changes** — and that is the headline, because the pass pays for
itself. Two of the changes are *negative*:

| change | tri/m |
|---|---|
| everything added (services bank, four wall fittings, hazard nosing, recessed lens) | **+43.8** |
| merging the deck run (§4.2) | **−30.3** |
| net | **+13.5** |

Three of the eleven changes cost **exactly zero triangles**: the two lost tags (§4.1), the drafted
plates (§3.1 — a frustum is six quads, so is a box), and the wall-band laps (§4.3).

`ring_frame` also went **192 → 128** triangles for a 16-segment ring, because the coincident faces
it was built from are geometry nobody can see.

---

## 3. What changed, and the measured effect of each

Every row is an A/B: the same camera, the same lights, the same deck, one variable, through
`CORRIDOR_NO_4G=<part>`. **The control is byte-exact** — `CORRIDOR_NO_4G=all` reproduces the
committed before-frame with *0.0000% of pixels differing, max channel delta 0*, so the harness is
not measuring its own noise.

Sixteen renders, one variable each. Diffed against the all-on frame at the **half** camera unless
the row says otherwise.

| part | what it is | % of pixels | mean Δ/255 | max Δ |
|---|---|---:|---:|---:|
| **all** | the corridor exactly as 4f left it | **75.645%** | 11.609 | 218 |
| `draft` | bevelled plates and deck tiles (§3.1) | 37.069% | 0.803 | 103 |
| `stations` | the four wall fittings (§3.6) | 36.488% | 4.009 | 180 |
| `channel` | the floor light, and its recessed lens (§3.2) | 28.578% | 5.110 | 199 |
| `deckjoin` | one deck panel per run (§4.2) | 18.839% | 0.425 | 106 |
| `soffit` | the lost chamfer tag (§3.3) | 14.904% | 2.059 | 57 |
| `bands` | 3 mm lap between wall bands (§4.3) | 14.753% | 0.256 | 88 |
| `plaque` | the amber legend plate (§3.4) | 11.155% | 0.440 | 180 |
| `services` | the clamped pipe bank (§3.5) | 8.532% | 0.486 | 90 |
| `seam` | the 6 mm door-leaf seal (§6.1) | **0.000%** | 0.000 | 0 |
| **all**, *door camera* | | **79.573%** | 14.825 | 213 |
| `kerb`, *door camera* | hazard nosing on the threshold (§3.7) | 0.654% | 0.024 | 119 |
| `seam`, *door camera* | | 0.127% | 0.0007 | **5** |

**Two rows read 0.000% and both are real negatives, not passes.** `kerb` and `seam` are both
attached to a doorway and there is no doorway in the half frame, so at that camera the control
cannot move — which is exactly the failure mode `CLAUDE.md` records as *"a diff of two failed runs
is not a pass"*, one level up. Both were therefore re-run at a camera where the thing exists, and
the honest reading is in the last two rows: the hazard nosing moves 0.654% of pixels by up to 119
levels, and **the door seam moves 0.127% of pixels by at most 5** — it is a manifold fix that
happens to add a shadow line, not a craft change, and §6.1 says so.

**Two rows I predicted would be byte-identical are not, and the reason is better than the
prediction.** See §4.2 and §4.3.

### 3.1 `draft` — a bevelled plate costs the same as a square one

`_drafted_slab` insets the four corners of a plate's **proud** face. Six quads either way: **12
triangles, one draw call, the same vertex count.** Applied to all 16 wall plates and 20 deck tiles
in a bay, and at double strength to the rail band.

The rail band is the one that mattered. A square-topped band 0.10 m proud and 0.19 m deep returns
one hard specular line down its whole length and reads as a white *shelf* bolted to the wall —
which is exactly what it looked like at 2.59 m before. The reference calls it a nosing over a
shadow reveal, and a nosing has a draft on it.

### 3.2 `channel` — the corridor's floor light has never been a light

`deck_panel` opened `with tag('light_deck_channel')` around a call to **`_box`** — the raw import
from `components`, which is not one of the `@_tagging` wrappers. `tag()` records what those
wrappers append, so **the block recorded zero triangles in every corridor this project has ever
built.** The 12 triangles fell through to the enclosing `deck_panel` tag and took `kit_deck`, grey
plate. `materials.py` has carried a `light_deck_channel` material — emission (0.86, 0.91, 1.00) at
energy 3.5 — since it was written, bound to a group nothing emitted.

Nothing could fail for it. `_tag_coverage` asks whether every triangle carries *a* tag; these
carried their parent's.

Fixed, and then split: the trough floor stays deck plate and a lens 62% of the width sits 30 mm
above it, so there is 34 mm of dark rebate either side that a standing eye actually sees. Without
the split the lamp is exactly as wide as the recess and the strip reads as a painted white line.

### 3.3 `soffit` — a nested tag lost a tie to its parent

`_merge` carried a sub-piece's tags into the parent's index space and *then* recorded the
caller's own tag. `tagged_spans` sorts by start index and `write_obj` is last-span-wins, so on a
**tie** the span appended later wins — and a sub-piece whose first tag opens on its very first
triangle ties with the outer tag exactly. `wall_assembly`'s `soffit` is that tag. 224 triangles a
section — the chamfer a player sees overhead down the whole run — were silently repainted
`wall_assembly` and took `kit_wall_plate` at albedo 0.46 instead of `kit_soffit` at 0.253.

`_merge`'s own docstring already *claimed* the correct behaviour: *"this outer tag only claims
whatever the assembly left untagged"*. It was true of every nested tag except the one a builder
writes first. The fix is swapping two lines.

### 3.4 `plaque` — the only saturated surface in the reference corridor, rendering as grey wall

`materials.py`'s balanced reading of `grey level 1.webp` lists eight corridor regions. Exactly one
is saturated: *"amber sign plaque (0.084,0.309)-(0.111,0.360) V 0.247 **S 0.184**"*.
`wall_assembly` has built that plate since it was written — `plaque_at`, one bay, one side — and
emitted it **with no `tag()` at all**, so it took the wall's own `kit_wall_plate` and the single
piece of colour the authority-1 corridor has rendered grey. It is now a `sign_frame` surround with
a `sign_text` face (`sign_text_lit`, emission (1.00, 0.97, 0.62) — amber), on the fitting
schedule rather than on bay 0 alone.

### 3.5 `services` — the descriptor this project names for CRAFT 4, run indoors

`AAA-STANDARD.md`: *"a fitting is where a fitting would be needed: … a clamped line running 900 m
down the flank of the drum is something the structure would actually have."* A pressurised
corridor is where a station's air, water, power and data physically go, and this kit ran none of
them.

`service_run` is a trunking tray, three hexagonal pipes at three diameters, and oxide-steel
stanchions every 1.5 m, on **one hand only** — `AAA-STANDARD` CRAFT 5 reads *"nothing is symmetric
that would not be built symmetric"*, and nothing makes a corridor's two walls mirror images.

It sits entirely above y = 2.02 m **on purpose**: `collision.corridor_profile` measures `half_w` as
the narrowest clearance between `floor_y + 0.05` and `floor_y + 1.8`, and `station/lift.py` sizes
its car off that number. `_selftest` asserts the height clause, with a counted control so the
clause cannot go vacuous.

### 3.6 `stations` — hatches, junction boxes and wayfinding, on a schedule

Four fittings, each built from group names `materials.py` **already binds** — `dress_duct`
(clad_services, metallic 0.90 against the wall's 0.10), `dress_metal` / `dress_wallbox`
(plant_valve_metal), `accent_warning` (0.70, 0.32, 0.23 — the corridor's only warm non-emissive),
`light_indicator_red` (emissive-only by measurement, so it adds a red point and not a light),
`sign_frame` / `sign_text`. That constraint is not decoration: session 4f's finding is that an
unbound interior group does not fall back to grey — `interior.tscn` declares no
`fallback_material`, so it keeps the glTF default and renders as **white plastic**.

**And the schedule was a hash, and the hash lost two of the four fittings.** With
`interior.ring_arc` unable to pass a section index, every section on the station draws the same
six slots — three bays by two hands. A blake2b over six samples of a sixteen-row table is a random
sample of six, and the one it drew contained no `hatch`: **`dress_duct` and `accent_warning`
appeared in none of the assembled deck's 291 corridor groups.** Two fittings existed only in their
own unit test. Walking the table at a stride co-prime with its length guarantees the window covers
distinct rows, and `_selftest` now asserts that every fitting kind reaches a **default** section.

### 3.7 `kerb` — hazard nosing where a hazard is

`door_frame`'s threshold is a 0.10 m step in a corridor whose reference median is value 0.30.
Both its edges now carry `dress_kerb` → `edge_chevron_nosing`, albedo **(0.90, 0.72, 0.06)**: the
most saturated material in the interior library and the only strong yellow in the walkable
station. It goes there rather than being scattered, because a nosing that marks nothing is
decoration.

### 3.8 `seam` — the shut door, which is defect 1 (see §6)

### 3.9 `deckjoin` and `bands` — I predicted byte-identical and I was wrong

Both are pure coincident-face removals that move no visible surface, so I wrote down that both
must render byte-identical and that a moved pixel would mean the reasoning was wrong. `deckjoin`
moves **18.839%** of pixels and `bands` **14.753%**.

The reasoning was not wrong; the prediction was, and the difference maps say why. **A coincident
face is not invisible — it is a depth-sort coin toss, and the toss draws a line.** Removing it
removes the line.

* `deckjoin`'s difference is confined to the **deck**, and it is a grid of hairlines: one across
  the deck at each of the thirteen panel joints, plus banding down the central lit strip where the
  emissive lens had an end cap at every joint facing straight up the corridor at the camera.
* `bands`' difference is thin bright lines along **every boundary of the wall build-up** — skirt
  to dado, dado to reveal, reveal to rail band, rail band to upper course — running the whole
  length of the corridor, plus the 20 mm strip under the chamfer (§4.4).

So the correct statement is not "invisible by construction". It is: **these two changes delete
visible z-fighting seams that had been drawn down the entire length of every corridor on the
station, and one of them also saves 30.3 tri/m.** The prediction is left in this document rather
than quietly corrected, because being wrong in this direction is the whole argument for rendering
the control.

---

## 4. Robustness — an assembled section went from 271 non-manifold edges to 0

### 4.1 the two lost tags

Covered in §3.2 and §3.3. Neither costs a triangle; between them they were **392 triangles a
section on the wrong material**, including the corridor's only floor light and the surface
overhead.

### 4.2 the deck was thirteen abutting panels and nobody could see a joint

`corridor_section` laid the deck as one `deck_panel` every 1.5 m. The plates butt with **no
modelled seam**, so a joint between two of them is two coincident quads a player cannot see from
any angle — the deck's visible articulation comes entirely from `deck_grid`'s proud tiles, which
are laid on their own pitch and know nothing about that loop.

What the subdivision *did* produce was **468 wasted triangles and 184 of the 271 non-manifold
edges in an assembled section**. One panel for the run: **−30.3 tri/m** (324.2 → 293.9) and
**−208 non-manifold**.

And it is not invisible, which I got wrong (§3.9): it deletes a hairline across the deck at each
of the thirteen joints and the transverse banding down the lit strip where the emissive lens had
an end cap at every one of them.

### 4.3 the wall build-up butted its own bands

Skirt against dado substrate, substrate against reveal, reveal against rail band, rail band
against the upper substrate: **55 more non-manifold edges**. Every band extends back to `-th`,
inside the wall, so 3 mm of lap moves no visible surface and costs **0 tri/m** (293.9 either way).

It is not invisible either (§3.9): it deletes a z-fighting hairline at every band boundary, down
the whole length of the run.

### 4.4 the chamfer was coplanar with the plate substrate

The soffit prism sprang from x = 0 exactly, coplanar with the substrate over the 20 mm band
between the top plate course and the wall head — a band that **is** visible, directly under the
chamfer, and z-fights. 11 edges. Set back 3 mm.

### 4.5 the totals

| | 4f | 4g |
|---|---|---|
| assembled 21.6 m section, **open** edges | 0 | 0 |
| assembled 21.6 m section, **non-manifold** edges | **271** | **0** |
| `ring_frame` (16 segments) | 64 | 0 |
| `door_leaf` shut | 4 | 0 |
| `wall_assembly` | 5 | 0 |
| `deck_panel` | 2 | 0 |
| tagged groups in a section with doors | 16 | 28 |
| `collision.corridor_profile` `half_w` / `ceil_y` | 1.08061006025654 / 2.829 | **identical** |

The per-piece bar in `_selftest` used to read `("door_leaf", door_leaf(), 4)` — the count that
piece was known to have, written down as a permitted maximum. **That is an assertion which can
only fail if somebody fixes the defect**, the same shape `CLAUDE.md` records against
`materials._selftest` asserting `hull_exterior.binds == ()`. The bar is now zero everywhere, with
no exemptions, and a negative control (duplicating one triangle) proves the assembled gate can
fire.

---

## 5. CHANGES I NEED IN FILES I DO NOT OWN

### 5.1 `station/interior.py` — pass the section index, so a corridor stops repeating

**This is the single change that would take the corridor from CRAFT 4 to a candidate 5**, and it
is one argument in two places. `corridor_section` now takes `seed=0` and keys every fitting on
`(seed, bay, side)`; without a varying seed the fitting schedule repeats every 9.205 m for 8 km of
station.

```diff
@@ interior.ring_arc @@
     for i in range(n):
         a = math.radians(start_deg + degrees * (i + 0.5) / n)
         here = per_section.get(i, ())
         v, t = kit.corridor_section(seg_len, doors=here,
-                                    door_leaves=door_leaves)
+                                    door_leaves=door_leaves,
+                                    seed=i)
```

```diff
@@ interior.axial_run @@
-        v, t = kit.corridor_section(seg, doors=here, door_leaves=door_leaves)
+        v, t = kit.corridor_section(seg, doors=here, door_leaves=door_leaves,
+                                    seed=i)
```

`seed` changes **which fitting stands in which bay and which hand the services run down**. It
changes no dimension, no profile and no collision shell, and `corridor_section` is deterministic
in it (no `random`, no `str.__hash__` — the stride is arithmetic and `_pick` is blake2b). The
default `seed=0` is what is shipped today, so applying the patch is strictly additive.

A caller that wants the arc's absolute position rather than the section index — better, because
two arcs of the same deck would otherwise repeat each other — can pass
`seed=int(start_deg * 4) + i`.

### 5.1b `station/interior.py` — every ring corridor draws 6.3% of itself twice

**The largest single finding of this session, and it is not in a file I own.** `ring_arc` sweeps an
arc as *n* abutting calls to `corridor_section`, and never passes `start_portal`. That parameter
exists, and its docstring in `interior_kit` says exactly why:

> *"`start_portal=False` hands the portal at z = 0 to whatever the run butts onto. A junction
> already frames its own arm mouths, and two frames in the same plane is both wasted geometry and
> a visible double edge."*

Every section builds a portal at z = 0 **and** at z = length, so at each of the *n* − 1 joints a
portal frame, its head light, two pilasters and their fourteen light-strip bars are built **twice,
at exactly the same coordinates**. Measured on a 12.5° arc of blue ring 0 (5 sections, 4 joints):

| | as `ring_arc` is | with `start_portal=(i == 0)` |
|---|---:|---:|
| triangles | 17,640 | **16,520** (−6.3%) |
| **exact-duplicate triangles** | **1,120** | **0** |
| non-manifold edges | 1,760 | **80** (−95%) |
| open edges | 0 | 0 |

The 1,120 break down as `light_pilaster_strip` 672, `pilaster` 224, `portal_frame` 176,
`light_portal_head` 48 — i.e. **280 triangles per joint**, and 720 of them are emissive.

**And it is not only geometry.** `export_scene.fixture_lights` makes *"one light per tagged light
fitting, at its centroid"*. The duplicated spans are duplicated fittings: **14 pilaster-strip spans
and one portal-head span per joint**, so a 30° arc (12 sections, 11 joints) carries roughly **165
coincident duplicate light sources**. Two lights at one point is twice the illuminance, at every
section boundary, all the way round every ring on the station.

```diff
@@ interior.ring_arc @@
     for i in range(n):
         a = math.radians(start_deg + degrees * (i + 0.5) / n)
         here = per_section.get(i, ())
         v, t = kit.corridor_section(seg_len, doors=here,
-                                    door_leaves=door_leaves)
+                                    door_leaves=door_leaves,
+                                    start_portal=(i == 0),
+                                    seed=i)
```

`axial_run` should take the same treatment. Verified by rebuilding the arc both ways through
`ring_arc`'s own remap: closure is unchanged at 0 open edges either way, so this removes geometry
without opening the surface. **Not landed here** for the same reason as §5.4 — it changes the
triangle count and the light count of every deck on the station, and this session cannot run
`walkable.py` or `deck.py --sweep` to confirm it.

### 5.2 `tools/export_scene.py` — the corridor anchor's exposure was derived against the wrong soffit

Not a patch, a re-derivation, and it is a consequence of §3.3. The corridor anchor's exposure was
measured on frames in which `wall_assembly`'s chamfer — 224 triangles a section, the surface a
player sees overhead down the whole run — carried `kit_wall_plate` at albedo 0.46 instead of the
`kit_soffit` at 0.253 that its own `tag()` had always asked for. That is 82% too bright on a large
surface feeding SSIL bounce into the walls.

With the tag restored, whole-frame `crushed` roughly doubles (§7). Nothing in `ROOM_EXPOSURE` is
*wrong* in the sense of having been mis-measured; it was measured correctly against geometry that
was mis-materialled. `--gate-frames --rerender` over the corridor rows is the check.

### 5.3 `station/materials.py` — `light_deck_channel`'s energy has never been seen in a corridor

`light_deck_channel` carries `emission_energy = 3.5`. That number was set against a room's floor
grating, and **this session is the first time the group has ever been emitted by a corridor**
(§3.2), so it has never been rendered on the surface it is named for. In the corridor it is a
continuous strip 0.11 m wide running the length of the deck, and it is the brightest thing in the
frame by a wide margin: the whole-frame **p99 moves ×1.19 → ×1.78** of the show reference when the
strip is switched on.

**And my eye was wrong about it, which is the point of measuring.** It reads as blown white in the
near field and it is not: the after frame contains **0 pure-white pixels**, the strip's own peak is
**250 of 255**, and whole-frame `clipped` is 0.03% against `measure_frame`'s `CLIPPED_CAP` of
3.69%. So this is a *note*, not a finding, and 3.5 ships.

It is still worth writing down, because `materials.py` makes exactly this argument in the other
direction for `light_ceiling_grid`, which went from 2.6 to 0.8 once it turned out to cover 370 m²
instead of a lamp's worth. A corridor strip is the same case — **area, not ladder position** — and
the number has now moved from "never rendered" to "rendered once, at one exposure, on one deck".
What would settle it is `tools/measure_frame.py --against "reference/10-interiors-generic-kit/
central corridor.webp"` boxed to the deck strip alone, against a frame matched to that reference's
camera, which this session did not have.

### 5.4 `station/interior_kit.py` — a defect I own, verified, and deliberately NOT landed

**`corridor_section` rotates its pilasters 90° from the orientation `pilaster()` documents.**

`pilaster()` builds a D-section: flat back at x = 0, bulging to `pilaster_proj_m` = 0.17, width
`pilaster_w_m` = 0.46 running along z. Its docstring says *"bulging toward +X, its width running
along Z"* and *"the rounded face … is what every corridor corner and portal jamb in the reference
does, and a square arris there immediately reads as a different show."* `corridor_section` places
it with `_rot_y(90.0 * side)`, which maps local +x to world ∓z. Measured, for side +1 at the
corridor wall face x = 1.300:

| | as placed, `_rot_y(90)` | as documented, `_rot_y(180)` |
|---|---|---|
| world x span | 1.0600 … 1.5200 | 1.1234 … 1.2900 |
| intrudes into the corridor | **0.2400 m** | 0.1766 m |
| length along the corridor | **0.1666 m** | 0.4600 m |

So the column is **lying on its side in plan**: 0.46 m across the corridor and 0.17 m along it,
presenting a flat face to the portal instead of a bullnose to the player, with the light strip
landing at x ≈ 1.29 — flush with the wall — instead of on the curve facing the corridor. 0.22 m of
the column is buried in the wall and 0.24 m sticks into the corridor.

**Why it is not fixed here.** That 0.24 m intrusion *is* `collision.corridor_profile`'s `half_w` =
1.08061: the pilaster is the pinch. Correcting the rotation widens the corridor's clear half-width
to ≈ 1.123 m, which changes the collision shell `walkable.py` walks and, through `LIFT-1`,
`station/lift.py`'s car width from 2.1612 m to ≈ 2.246 m — a module another agent owns and is
editing this session, whose declared extrapolations quote that figure to four decimal places. This
session was told not to run `walkable.py`, so it cannot verify the shell it would be moving.
Landing it blind would be the "disjoint source files are not disjoint imports" failure with a
measured constant attached.

The patch is one character:

```diff
@@ interior_kit.corridor_section, the pilaster loop @@
     for i in range(first, n_bays + 1):
         for side in (-1, 1):
             v, t = pilaster(h - chamf, p)
-            _merge(verts, tris, v, t, _rot_y(90.0 * side),
+            _merge(verts, tris, v, t, _rot_y(90.0 * side + 90.0),
                    (side * (w / 2.0 - 0.01), 0.0, bay * i))
```

Whoever applies it must re-run `collision.corridor_profile`, `station/walkable.py --deck
blue/0/0`, and `station/lift.py --selftest`, and update `docs/lift-4g.md`'s LIFT-1/LIFT-2 tables.

---

## 6. Verdict on the two defects this session was handed

### 6.1 `door_leaf` at `open_fraction = 0.0` is non-manifold — CONFIRMED, and fixed

Measured: `door_leaf(open_fraction=0.0)` → 4 non-manifold edges; `door_leaf(open_fraction=0.35)` →
0. So it is exactly the closing plane, on every shut door on the station, and it is session 3x's
`portal_frame` defect surviving in the one piece 3x did not touch.

**`docs/lift-4g.md` §3.1's fix is right in kind and too large in degree.** It proposes insetting
each leaf by half of `wall_seam_m`, i.e. 19 mm a side. That opens a **38 mm slot between two 100 mm
leaves**, which a player can see the far side of within ±11° of straight on — a hole where there
was a coincident face. 3 mm a side is used instead: a 6 mm seam, see-through only within ±2°,
which is what a door seam is.

**The craft gain is real and it is small, and the A/B is what says so.** Each leaf carries a
100 mm flat border around its raised centre panel, so two shut leaves presented a **200 mm flat
band down the middle of the door with no line in it** — a shut door read as one slab. It now
closes on a shadow line. Measured at the door camera, that shadow line moves **0.127% of pixels by
at most 5 of 255**. So this is a manifold fix that happens to be slightly prettier, and claiming
more would be claiming more than the frame shows.

The proposed `_selftest` block from `lift-4g.md` §3.1 is in, widened: the bar is zero for eleven
pieces with no exemptions, plus the assembled section, plus a control.

### 6.2 "`boundary_edges` returns a PAIR and nothing reads the second element" — three corrections

**(a) The numbers quoted are non-manifold, not open.** `boundary_edges` returns `(open,
non-manifold)`. Measured on 4f's kit: `ring_frame` 64, `wall_assembly` 5, `door_leaf(shut)` 4,
`deck_panel` 2 — all **non-manifold**, and the **open** count is **0 for every one of them**.
`docs/lift-4g.md` says "non-manifold" correctly; the brief transposed it.

**(b) "Nothing reads the second element" is false, and the truth is worse.** Fourteen modules read
it — `aperture`, `bespoke`, `dressing`, `signage`, `docking_bay`, `command_control`, `plant`,
`council_chamber`, `customs`, `interior`, `generate_hull`, and `interior_kit._selftest` itself.
`_selftest` read `door_leaf`'s count and wrote it down as `max_nm = 4`, a permitted maximum. That
is not "nobody looked"; it is **an assertion that could only fail if somebody fixed the defect**,
and it reported PASS for four sessions.

**(c) The per-piece count is the wrong question, but not for the suggested reason.** Open edges do
close against neighbours — a section reads 0 open. Non-manifold edges do the **opposite**:
assembly *creates* them. A plain 21.6 m section carried **271**, against 11 across all the
per-piece counts inside it, because every repeated piece butting its neighbour along the run
shares a full quad face:

| source | edges | fix |
|---|---|---|
| abutting deck panels | **184** | build the run as one panel (§4.2) — also −30.3 tri/m |
| the wall build-up's own bands | 55 | 3 mm lap (§4.3) |
| soffit meeting a portal frame | 24 | absorbed by §4.3/§4.4 |
| the pieces themselves | 8 | `door_leaf` seam (§6.1) |

**So: ask the assembled thing.** `_selftest` now does, at a hard zero, with a negative control.
The general form is the one this repository already knows — *a gate belongs in the module that
builds the thing, and it must build the hard case* — with one clause added: **and it must build
the thing at the scale it ships at.** A corridor never ships as one 3 m piece.

---

## 7. What is NOT done

* **The pattern repeats every 9.205 m** until §5.1 is applied. That is the gap between CRAFT 4 and
  a candidate 5, and it is one line in a file this session does not own.
* **Every ring corridor draws 6.3% of itself twice** (§5.1b). Verified, one line, not landed.
* **The pilaster is rotated 90°** (§5.4). Verified, patch written, not landed, because it moves
  `half_w` and `lift.py`'s car mid-session.
* **`light_deck_channel`'s energy is unmeasured in a corridor** (§5.3), and **the corridor
  anchor's exposure needs re-deriving** now the soffit is right (§5.2).
* **The kit's new wall fittings are not solid either**, for the same reason the clutter is not:
  `collision.corridor_shell` sweeps a smooth profile and does not read them. Nothing is in the
  walking lane — `_selftest` asserts every fitting projects less far than the pilaster, which is
  the pinch `half_w` is measured at — so a player never meets one head-on, but they can be walked
  through.
* **The corridor's clutter is still not solid.** `station/deck.py` records
  `stats["clutter_solid"] = False`; `collision.prop_boxes` derives room props from the room's own
  mesh and does not read `corridor_dressing`'s output. A player walks through the crates. Not this
  session's file.
* **`station/corridor_dressing.py` was reviewed and not changed**, and that is a measured decision
  rather than an omission: its five schemes place 8–27 pieces per 111 m of arc (freight 16, lurker
  27, public 8) across 22 machine kinds and 13 distinct materials, its density was already tuned
  against a render in session 4e, and all three of its corridor groups (`dress_crate`,
  `dress_post`, `dress_skid`) reach the assembled deck. The corridor's flatness was in the **kit**,
  which had 20 mm of relief and nothing on its walls — which is what `corridor_dressing`'s own
  module docstring says, and it was right.
* **The frame is contrastier than the show, and the pass made that worse.** Measured with
  `tools/measure_frame.py --against "reference/10-interiors-generic-kit/grey level 1.webp"`:

  | | normal before → after | half before → after |
  |---|---|---|
  | median vs reference (target ×1.40 ±25%) | ×0.80 → **×0.94** | ×1.39 → **×1.47** (in window) |
  | p5 (band ×1.29) | ×0.72 → ×0.68 FAIL | ×0.74 → ×0.74 FAIL |
  | p99 (band ×2.58) | ×1.19 → ×1.25 OK | ×1.27 → **×2.13** OK |
  | crushed (band ×11.42) | ×16.92 → **×38.83** FAIL | ×11.83 → **×22.37** FAIL |
  | clipped (cap 3.69%) | 0.00% → 0.00% | 0.03% → 0.03% |

  The **level moves the right way** on both cameras and the half camera stays in the ×1.40 window.
  **p5 is unchanged**, which matters because layer 4b identified p5 as the discriminator. `p99`
  moves because the floor strip is now the brightest thing in the frame, and stays inside its band.
  **`crushed` roughly doubles on both cameras** — still inside the derived absolute envelope
  (0.22%–63.92%) but further from the reference's 0.52%. It was already failing by 12–17×.

  Most of it is the soffit correctly going from albedo 0.46 to 0.253 over a large surface, which
  removes the SSIL bounce that had been lighting the walls off a chamfer wearing the wrong
  material. That is a *consequence of a fix*, not a new defect — but it means the corridor
  anchor's exposure in `tools/export_scene.py` was derived against a frame in which 224 triangles a
  section were 82% too bright, and should be re-derived. Layer 4b's open problem (13/23); this pass
  moved it and says so.
