# NPC silhouette — heads, hands and hair as geometry (session 4g)

Extrapolations made while giving the residents a face, a hand and a species-readable
head. Written in `canon/INVENTIONS.md` format — **what, why, what constrained it, what
would overturn it** — for the owner to merge. Nothing here is canon; everything here is
authority 5 unless it says otherwise, and each entry says which of its numbers is weak.

The measurements these entries were tuned against are printed by

```bash
python3 station/npc/body.py --silhouette      # the gate and its five controls
python3 station/npc/body.py                   # 1,362/1,362
```

## The frames

Godot 4.4 + Mesa lavapipe, `renderer: Vulkan 1.4.318 - Forward+` printed in the log on
**all four**, same command on each side of each pair, all four taken this session.
`render_godot.sh` deletes the PNG if Godot reports the OpenGL 3 fallback; it did not.

| pair | camera | pixels changed |
|---|---|---|
| `engine-4g-npc-lineup-{before,after}.png` | human / Centauri / Minbari / Narn, dressed, `lod1`, eye at **2.0 m**, fov 42, 1400×700 | **1.360%** |
| `engine-4g-npc-corridor-{before,after}.png` | the shipped player camera, `--shot deck --deck blue/0/0 --at docking_bays --fov 25 --res 1280x720` | **0.156%** |

**2.0 m is the rubric's HALF distance** for a person: a player meets somebody across a room
at about 4 m, and CRAFT is judged at that and at half of it. The corridor pair is the
shipped camera at **fov 25 against `player.gd`'s 50**, which is a 2× angular magnification
— optically what halving the distance does to the subject's pixel size — so it is the same
rule applied to the frame the owner was actually looking at.

**And the corridor pair barely moves, which is a finding and not a disappointment.**
`populace.corridor_lod` bakes the corridor crowd at **lod4**, a `no_detail` level, so the
eyes, brows, nose, ears, thumbs and fingers are all culled by tier before they reach that
frame. What changed in those 1,434 pixels is the neck root ring and the ankle overlap —
the only two 4g changes that survive to lod4. A corridor still is the wrong instrument for
this work, and the reason is `populace.py`'s own documented bake-time compromise: *"A
player standing next to one of these people sees a 372-triangle body where the budget
would give them 8,000. The fix is runtime LOD."* `crowd_ladder()` already draws a body
inside 18 m at **lod2** at runtime; the still render has no runtime and bakes one level.

---

## INV-4G-001 — the eye and the brow, as geometry, in the hair material

**What.** Every humanoid resident carries four small solids on the face that did not
exist before: two eyes and two brows. They are placed off the skull's own interpolated
section (`_face_point`, which reads `_head_profile`), not off a second table, so a Narn's
heavier braincase and every per-individual cranium jitter carry them.

Sizes, in fractions of the figure's own head height (`FIGURE["head_h"] × head_k × H`):

| | half-width | half-height | where |
|---|---|---|---|
| eye aperture | 0.061 | 0.024 | `t = 0.46`, `_head_profile`'s own eye-line row |
| brow | 0.078 | 0.013 | `t = 0.55`, on its brow-ridge row |

and across the face at **0.43 of the skull's half-width** at that ring.

**Both emit into the group `npc_hair`**, which is what makes them visible at all.

**Why.** The owner's words about the render were *"the npcs just being undetailed
featureless blobs"*. Session 4f gave the head nine landmark rings, a nose and a pair of
ears; at the distance a player actually talks to somebody the front of the face was still
blank, and a head with a nose and no eyes reads as a mannequin at every distance a
mannequin can be told from a person. Nothing else on a face reads below about 100 px of
head height.

**What constrained it.**

1. *Anthropometry, for the sizes.* Palpebral fissure 28 × 11 mm on a 231 mm head gives the
   half-extents above; interpupillary 63 mm on a 145 mm head width gives 0.43 of the
   half-width. This is the same class of source `FIGURE`'s own cross-check uses — a
   standard table that could not have copied the photograph.
2. *The material library, for the group.* A body in this project has **no UVs and no
   texture**: `materials.py` binds one material per group, so anything on a face that is
   not skin-coloured must be its own group, and the only groups a body may emit are the
   ones the library already binds. Inventing `npc_eye` would put every eye on the
   fallback — the defect CLAUDE.md records three times this week. `npc_hair` is also the
   *right* one and not merely the available one: an eyebrow **is** hair, and the eye's
   aperture is the darkest thing on a face at any crowd distance. `npc_hair` is measured
   as "matte, at the bottom of the human range", which is what both are.
3. *The draw-call merge, for where they are emitted.* `populace._by_material` merges a
   body's spans into one span per **run** of the same material and only ever joins spans
   already adjacent in the triangle list. Emitted with the nose they would cut the skin
   run in three, at two extra primitives per person against
   `budget.BUDGETS["deck_primitives"] = 600`. They are emitted **last**, beside the hair.
   Measured: a bare body is **2 merged runs at every level of every species**, and a
   dressed one at the corridor bake level is **12**, both unchanged by this work.
4. *Depth, by the rule `_face` already records for the nose.* A shallow blob on a curved
   surface crosses it at a grazing angle over its whole footprint. The first version
   buried the eye 42% of its depth, like the nose, and it emerged as two 3 mm slivers —
   present in the mesh, absent in the picture. It now stands 0.86 of its depth proud,
   which is where a real lid assembly sits relative to the orbital rim, and the crossing
   stays steep because the section is flat (`power` 2.4) rather than round.

**Weakest number.** The 0.86 protrusion. It was set by rendering and looking, not derived,
and it is the one value here that a frame could argue with.

**What would overturn it.** An `npc_eye` material in `materials.py` with a sclera and an
iris — then the eye stops being a dark bead and becomes an eye, and the geometry can be
recessed into a real orbit instead of standing proud of one. That is a `materials.py`
change and `body.py` does not own it.

---

## INV-4G-002 — four fingers, and what the palm gives up to pay for them

**What.** `_hand` was one closed lofted shell from the wrist to the fingertips — a mitten.
It is now a **palm** ending at the metacarpal head plus **four fingers**, each three rings
at its own segment count, with a slight curl toward the thigh and converging tips.

| finger | z across the knuckle ring | length | radius |
|---|---|---|---|
| index | +0.62 | 0.92 | 0.98 |
| middle | +0.21 | 1.00 | 1.00 |
| ring | −0.21 | 0.94 | 0.93 |
| little | −0.62 | 0.78 | 0.80 |

Lengths and radii are fractions of the middle finger's; z is a fraction of the knuckle
ring's own depth. The fingers run `0.045 → 0.100` of stature, which is **96 mm** on a
1.75 m human.

**Why.** A mitten and a hand have the same bounding box and the same front-view outline
and completely different ones from every other angle. The thing that reads as a hand is
the **4 mm of background showing between two fingers** — the same argument the project
already makes about holes: a hole shows the background, and here the background is the
point rather than the bug.

**What constrained it.**

- *Adult hand anthropometry.* Middle finger 85–100 mm; index and ring within 5% of each
  other; little ≈ 0.78 of middle; the four spanning about one palm depth at the knuckle.
  Two sources that could not have copied each other, as INV-4G-001.
- *The hand may not grow.* `FINGER_TIP_F = 0.100` is the old four-ring plan's last ring,
  so total hand length is unchanged and `costume.py`'s cuff and `animation.py`'s wrist
  band see the same object. When `fingers` is culled the palm runs the full length again
  and the mitt comes back — it is the coarse level of the same hand, not a second one.
- *Triangles.* `_small_seg` sizes a 9 mm finger by **its own** sagitta rather than the
  torso's: four fingers at the body's 64 segments would be 1,024 triangles a hand; at 6
  they are 128, and the sagitta is 1.2 mm. That derivation is the general form of the rule
  `costume._att_seg` records paying to learn on a 90 mm collar.

**Weakest number.** The `t²` curl toward the thigh (0.16 of the wrist radius). A hanging
hand's fingers do curl, but nothing in `reference/` shows one at a stated scale.

**What would overturn it.** Any full-figure frame with a hand in it at a stated scale;
`reference/14-characters-and-uniforms/` is twenty-four portraits framed at the shoulders.

---

## INV-4G-003 — the Minbari bone crest is 60% taller and 22% wider

**What.** `_f_minbari_crest` went from **0.46 → 0.74** of head height above where it leaves
the skull and from **1.18 → 1.44** of the skull's half-width across, with the sweep back
raised from 0.45 to 0.58 of head depth. **Zero triangles**: `_blade`'s ring and segment
counts are unchanged.

**Why.** `body.py`'s own note on the species has always read *"a broad upright bone fin
rising behind and above the crown, **WIDER than the skull**"*, sourced to
`reference/05-sector-green/rotunda.webp` (authority 1, ~60 px figures — the frame
establishes the shape and not the size). At 1.18 half-widths it was barely wider than the
skull, and the measurement said so: at the level the corridor crowd is baked at, a Minbari
and a human head band overlapped at **IoU 0.875 front / 0.651 side** — the front view, the
one a player walking a corridor gets, was 87.5% the same picture. After: **0.716 / 0.651**.

**What constrained it.** `_selftest` asserts every species — crest, helmet and all — clears
`interior_kit.PROVISIONAL["door_height_m"]`, and it imports that number rather than copying
it. The crest is measured into the bounding box the door check uses, so the ceiling on this
value is the station's own doors and not an opinion. A Minbari at the +2.5σ stature the
truncated deviate allows still passes.

**Weakest number.** Both of them. The shape is authority 1 and the dimensions are ours.

**What would overturn it.** One Minbari at a stated scale beside a human or a doorway.

---

## INV-4G-004 — the brow ridge is an identity feature, not a detail (and the keel that was thrown out)

**What.** `FEATURE_TIER["brow"]` moved from `detail` to `extremity`, so a Narn, a Drazi and
a Grome keep their supraorbital ridge out to **77 m** instead of losing it at **22 m** —
which includes the level `populace.corridor_lod` bakes the corridor crowd at. 20 triangles
at `seg` 8.

**Why.** The same defect hair had in session 4f, one tier down. An attachment that lies
strictly inside the figure's own bounding box is priced by a measurement that cannot see it,
and the consequence here was that every Narn in a corridor was a bald human with a slightly
heavier braincase. `G'Kar more.jpg` (authority 2) is what the ridge is built from, and
dropping it at the level the crowd actually ships at is dropping the species.

**What was tried and removed, recorded so it is not built again.** A medial crown keel — a
low fore-aft ridge over the crown, riding `_head_at` — was built to give the Narn something
the *front* view could see. It made the number **worse**: human vs Narn went 0.875 → 0.946
in the front head band and 0.816 → 0.832 in the side one, because a ridge standing proud of
the crown occupies exactly the outline region **a human's hair cap occupies**. It cost 32
triangles at the bake level to make a Narn look more like a person with a haircut. Removed.

**The honest residue.** Human vs Narn is the closest of the six pairs the gate measures, at
**0.832**, and that is reported rather than engineered away: a Narn's identity in the
reference is a spotted, reticulated crown — a **texture** on a skull this module already
builds wider, deeper and squarer-jawed than a human's — and not a silhouette.

**What would overturn it.** A Narn skin material with the crown pattern in it, at which
point the pair separates on colour rather than on outline and the gate's ceiling should be
re-derived.

---

## Two defects found by the new gate, in geometry that predates it

Not extrapolations. Recorded here because they were found while building the above and both
are fixed in `body.py`.

**Coincident capped discs at the ankle and at Kosh's collar.** `interior.boundary_edges`
keys edges on **position**; `body.edge_census` keys on **vertex index**. Every humanoid's
foot began at exactly the leg's last ring — same centre, same radii, same segment count,
both shells capped — so one disc carried four triangles per edge. Position-keyed: **2
non-manifold edges per figure**. Index-keyed: zero, since the two caps are different
indices, which is why it had been scored closed since the module was written. The Vorlon's
robe and yoke were the same mistake at a larger scale: **125 non-manifold edges**, 250
triangles of robe and 250 of yoke z-fighting over one disc. It is session 3x's `portal_frame`
finding — *coincident faces are geometry nobody can see* — in a second module. Both joints
now overlap the way every other joint in the file already did, and the gate reads **0 open,
0 non-manifold across 15 species × 9 mesh levels**.

**`npc_impostor` has no material.** The only group any body can emit that `materials.py`
does not bind. It is latent rather than shipped — `lod9` is the impostor card, nothing
outside `body.py` references the name, and `populace.crowd_ladder()` stops at `lod8` — but
the day the runtime starts drawing cards, every figure past 272 m lands on the fallback.
`_detail_gate` declares exactly this one name, so a **new** unbound group fails. Fixing it
needs an `npc_impostor` entry in `materials.py`, which `body.py` does not own.
