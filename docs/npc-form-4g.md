# NPC form — a modelled skull and a shoulder that is not a shelf (session 4h)

Extrapolations made while rebuilding what an NPC *is* rather than what is bolted to
it. Written in `canon/INVENTIONS.md` format — **what, why, what constrained it, what
would overturn it** — for the owner to merge. Nothing here is canon; everything is
authority 5 unless it says otherwise, and each entry says which of its numbers is weak.

The measurements every entry was tuned against are printed by

```bash
python3 station/npc/body.py                 # 1,426 / 1,426
python3 station/npc/body.py --silhouette    # the gate, its tables and its controls
python3 station/npc/body.py --report        # the four LOD schedules and the chain
```

## The problem, stated as geometry

The owner, on a frame: the NPCs are *"undetailed featureless blobs"*. Session 4g added
eyes, brows and fingers and scored itself **craft 3**, honestly. The reason more parts
could not fix it is that the underlying form was wrong:

* a head was **nine horizontal rings of superellipse**, 26 mm of vertical resolution on
  a 231 mm skull. A lip is 9 mm, an orbital rim is 6 mm, a mentolabial sulcus is 4 mm.
  **None of them can exist**, however many lobes the rings carry;
* every landmark that did exist was a **radial lobe about the ring's one centre**, a
  displacement that can only make a head rounder or narrower. There was no way to say
  *"this part of the face is further back"* at all — so no orbit, no nasal root, no
  submalar hollow, no oral fissure;
* the torso ended on a ring at the acromion at `sw × 1.00` and a ring 42 mm above it at
  `sw × 0.40`. That is 71 mm of horizontal travel over 42 mm of rise, **all the way
  round**: a plate with a corner. The arm was supposed to carry the deltoid and,
  measured, never reached the silhouette — its widest point is 0.99 of the biacromial
  half-width against the torso's 1.00, so the deltoid was inside the torso at every
  height and the widest point of the figure was the flat corner.

## The frames

Godot 4.4 + Mesa lavapipe, `Vulkan 1.4.318 - Forward+` printed in the log on **all
four** (2 occurrences each; 0 occurrences of the OpenGL 3 fallback string).
`render_godot.sh` deletes the PNG if Godot reports the fallback; it did not. Both sides
of each pair were rendered this session, from two `git worktree` checkouts, same
command per pair.

| pair | camera | pixels changed |
|---|---|---|
| `engine-4h-npc-lineup-{before,after}.png` | human / Centauri / Minbari / Narn, dressed, **lod1**, eye at **2.0 m**, target 1.40 m, fov 42, 1400×700 — session 4g's own lineup camera, reused unchanged | **6.787%** |
| `engine-4h-npc-close-{before,after}.png` | the human alone, dressed, **lod0**, eye at **1.00 m**, fov 34, 1400×700 | **10.320%** |

**2.0 m is the rubric's half distance** for somebody met across a room; 1.0 m is half of
that again, and is inside `lod0`'s own quality floor of 2.23 m — the distance the player
converses at, and the only one at which a mouth is more than two pixels.

---

## INV-4H-001 — the skull as a displacement field, not a stack of discs

**What.** `_head_profile` goes from 9 rows to **15**, and `_ring` gains a second kind of
displacement. A row now carries a `zoff` list as well as a `lobes` list:

* **`lobes`** scale the radius about the ring's centre — a **width**;
* **`zoff`** displaces **z alone**, by `amount × rz`, after the front squash — a
  **relief**.

The split is the anatomy and it is the whole of why a face is now a face:

| t | landmark | tier | carried by |
|---|---|---|---|
| −0.07 | submental triangle | base | `squash_front` 0.92, `zo` −0.008 (was +0.020) |
| 0.06 | mental protuberance | base | radial lobe, midline |
| 0.115 | mentolabial sulcus | face | `zoff` −0.075, sharp 2.2 |
| 0.165 | lower vermilion | face | `zoff` +0.070 |
| 0.20 | oral fissure + gonial angle | base | `zoff` −0.055 sharp 2.0, lobes at 32.7° |
| 0.255 | upper vermilion + philtrum + nasolabial | face | three `zoff` windows |
| 0.34 | zygomatic arch + submalar hollow | base | lobes at 45.9°, `zoff` −0.035 |
| 0.405 | infraorbital rim | face | `zoff` +0.030 |
| 0.46 | orbit + temporal fossa + nasion | base | `zoff` −0.105 at the eye, lobes −0.045 at the temple |
| 0.515 | supraorbital rim + glabella | face | `zoff` +0.055, −0.070 at the midline |
| 0.57 | supraorbital torus | base | lobe +0.045, `zoff` −0.045 |
| 0.635 | frontal eminences | face | `zoff` +0.022, paired |
| 0.70 | frontal squama | base | slope |
| 0.86 | parietal + occiput | base | lobe at 270° |
| 1.00 | crown | base | — |

**Why the two mechanisms are not interchangeable.** The orbit is the case that proves
it. Built as a negative *lobe* at the eye's azimuth, an 8 mm socket also pulls ~3 mm out
of the temple, because a lobe scales the distance from the ring's single centre. Built
as a `zoff` it is 8 mm straight back and the head is exactly as wide as it was. That is
what lets the eye be **recessed** rather than a bead stuck on a ball, which is what the
owner was looking at. Measured on the built mesh: the eye's front sits at 76.9 mm, the
skull around it at 68.9–71.6 mm and the brow at 83.8 mm — **6 mm proud of a socket
floor, 7 mm behind the brow**, which is where a lid assembly sits relative to an
orbital rim.

**What constrained it.**

1. *Standard adult craniofacial proportion*, the same class of source `FIGURE`'s own
   cross-check uses and the same authority-5 status: eyes at half the head height,
   widest point at the parietal, chin ≈ 0.6 of the parietal width, stomion ≈ 0.19 of
   chin-to-crown, interpupillary 63 mm on a 145 mm head width.
2. *The azimuths are DERIVED, not typed.* `_face_az(xf)` inverts the ring's own
   superellipse: a landmark at fraction `xf` of the half-width lies at
   `acos(xf^(p/2))` from +X. The eye (`EYE_X_F = 0.43`) comes out at 65.7°, the
   zygomatic arch (0.72) at 45.9°, the gonial angle (0.86) at 32.7°. So `EYE_X_F` and
   the orbit cannot drift apart, and the cheekbone lobe is on the cheekbone rather than
   8° off it — which the previous table's 52° was.
3. *One authoritative surface.* `_face_point` used to reconstruct the superellipse by
   hand and knew nothing about the lobes, so cutting an orbit would have moved the skull
   and left the eye floating in front of it. It now solves the azimuth and returns
   `_ring_point`, **the function the ring itself is lofted from**. Hard rule 4 at the
   scale of an eye socket.
4. *`_small_seg` and the sharpness exponent.* A crease and a swell need different window
   shapes, so `lobes`/`zoff` entries take an optional `sharp`: the raised cosine to a
   power narrows the support without narrowing `half`, and `half` has to stay wide
   enough to be SAMPLED — a feature narrower than one azimuth step vanishes rather than
   softens.

**Weakest number.** The orbit's −0.105. It is the one value here set by rendering and
measuring rather than derived, and it is the one a frame could argue with.

**What would overturn it.** An `npc_eye` material in `materials.py` with a sclera and an
iris — then the eye stops being a dark bead and the socket can be cut deeper still.
That is a `materials.py` change and `body.py` does not own it. Also: one square-on
portrait of any species at a stated scale.

---

## INV-4H-002 — the nose is measured from the skull, not from the origin

**What.** Every nose ring's centre used to be an absolute fraction of head depth
(`hd × 0.74`). It is now `_face_point(ind, sp, t, 0.0, ...)` — the midline of the
skull's own surface at that height — plus a stated projection.

| t | ring | projection, in head depths |
|---|---|---|
| 0.235 | buried root | −0.100 |
| 0.290 | alar base (nostril wings, a lobe at ±62°) | +0.150 |
| 0.330 | pronasale — the tip | **+0.240** |
| 0.400 | rhinion | +0.150 |
| 0.480 | nasion | +0.045 |
| 0.560 | buried in the brow | −0.060 |

**Why.** An absolute depth is a second copy of the face's shape. The moment INV-4H-001
gave the maxilla a lip standing 4.4 mm proud, the face plane came out to meet the nose
and the nose lost a fifth of its projection **without a number changing**. Measured on
the built mesh, the tip now stands **24 mm** past the face plane, against an adult nasal
projection of ~20 mm on a 231 mm head.

**What constrained it.** Standard nasal proportion — nasal length (nasion to subnasale)
≈ 0.22 of head height, projection ≈ 20 mm — and the nasion notch cut into the skull by
INV-4H-001, which is what gives the bridge a *root* to emerge from. Before that notch
the skull's face plane at the bridge was 0.871 `hd` and the nose's own bridge 0.860:
the nose had no root at all.

**Weakest number.** The alar lobe amplitude (0.34 of the nose's own radius over ±62°).
Nostril width is not visible in any reference frame in this repository.

**What would overturn it.** Any authority-1 or -2 portrait in profile at a stated scale.

---

## INV-4H-003 — the shoulder is a deltoid over a ribcage, and it is four rings

**What.** `_torso_profile` gains three rows and re-numbers two. Reading up the figure:

| ring | height (of stature) | half-width at the SIDES, in biacromial half-widths | tier |
|---|---|---|---|
| upper_chest | 0.772 | 0.96 | base |
| **deltoid** | **0.798** | **1.01** — the widest ring on the whole figure | body |
| shoulder (acromion) | 0.818 | 0.95 | base |
| **supraspinous** | **0.831** | **0.83** | body |
| trapezius | 0.842 | 0.64 (was 0.44) | base |

and the arm's `bulge_at` moves 0.16 → 0.19 with a lateral lobe blended around the belly.

**Why.** A real shoulder's widest point is the **deltoid**, about 25 mm *below* the
acromion; from there the outline runs up and in over the acromion, then down and in
along the trapezius to the neck. That is an S, and three rings is the fewest that can
carry one. The note that used to stand in the source said *"there is no deltoid lobe
here on purpose: the deltoid belongs to the ARM, whose own bulge already carries it"* —
measured, it did not, for the reason in "the problem" above.

**What constrained it, and this is the entry's real content.**

1. **The biacromial measurement already contains the muscle.** `FIGURE["shoulder_w"] =
   0.235` was read off a standing officer in `more hallway.jpg` — across his shoulders,
   in a uniform, deltoids and all. The first version of this put the deltoid **6.5%
   outside** that number, which double-counts. `populace.py`'s idle-sway control is what
   said so: a dressed figure went 0.549 m across the shoulders to **0.601 m**, through a
   0.58 m bound that exists so a body comes back inside its own shoulders. The group is
   scaled to land the widest ring at **1.012** of biacromial; the S-curve is unchanged.
2. **`contains()`**, which asserts every arm-root vertex is inside the torso solid, is
   the ceiling on the deltoid lobe.
3. **`animation.rigid_track`**, and it caught a second one — see INV-4H-004.

**Weakest number.** The 0.34 lateral lobe on the trapezius. It is what stops the top of
the torso being a small round post, and its amplitude is chosen to make the top ring a
ridge running out toward the joint rather than derived from anything.

**What would overturn it.** One full-figure frame of an S2–3 uniform from the front at a
stated scale. `reference/14-characters-and-uniforms/` is twenty-four portraits framed at
the shoulders.

---

## INV-4H-004 — a muscle belly gets a ring, and it must not be a joint

**What.** `_limb`'s ring plan was `k / (rings - 1)` — five evenly spaced values — and
**no `bulge_at` this module uses is one of them**. An arm authored with a 1.30 deltoid at
t = 0.16 was sampled at 0.25, where the bulge envelope has already fallen to 0.33 of its
peak, so the built bulge was **1.098**. A leg authored with a 1.10 calf at 0.55 was
sampled at 0.50 and built **1.034**. Both muscles existed in the parameters and in no
vertex, for as long as the function has existed — and the docstring claimed the opposite
(*"the joint ring is pinned at bulge_at"*).

`_limb_ts` now snaps the ring nearest the belly onto it. **Nothing is added**: five rings
stay five rings, so no level's triangle count moves.

**And the belly must not land on a joint.** `FIGURE` puts the knee at 0.527–0.572 of the
hip-to-ankle span depending on `leg_k`, so a calf at 0.55 pulled a ring onto the knee.
`animation.rigid_track` — a different module's gate, which fits one rigid transform per
piece for a runtime that cannot skin — went **10.7 mm → 30.3 mm** against a 20 mm bar,
because a piece straddling a joint has to follow one bone while its vertices interpolate
two. The gastrocnemius belly is **below** the knee, at 0.62 of the span: both where the
muscle is and clear of the joint. Back to 10.7 mm.

**What constrained it.** `FIGURE`'s own knee height, and `animation.py`'s 20 mm bar.

**Weakest number.** 0.62. Adult gastrocnemius belly is usually quoted as 0.60–0.65 of
hip-to-ankle; any value in that band clears the knee.

**What would overturn it.** Nothing in `reference/`; this is anatomy, not Babylon 5.

---

## INV-4H-005 — the ring tiers, and the 4.5 m the face tier costs

**What.** A profile row carries a tier: `base`, `face` or `body`. `base` is built at
every level and is **exactly** the ring set that existed before this session, so lod3 and
below do not move by a triangle. `face` and `body` are dropped at their own measured
distances.

`form_schedule()` is a fourth LOD schedule beside silhouette, profile and feature, and it
exists for the reason those three are separate: **two knobs stop being visible at two
distances.** A lip is 13.0 mm of chord error and a deltoid roll-over is 30.7 mm.

| step | error | honest from | dropped at | px at the drop |
|---|---|---|---|---|
| `face_and_body` | 0 | — | — | — |
| `body` (face rings gone) | 13.0 mm | 13.39 m | **8.9 m** | 2.26 |
| `none` | 30.7 mm | 31.59 m | **28.1 m** | 1.69 |

**Neither of the other instruments can see this cull**, and that is the finding worth
more than the feature. `feature_schedule` compares **part names** — a head with fewer
rings is the same part, so it scores zero. The figure's **bounding box** does not move
either: the crown, the soles and the fingertips are all base geometry. That is the exact
blindness session 4e paid for with a bald corridor crowd, one currency along.
`_detail_gate` part 5 (d) constructs both instruments on the two meshes and shows them
both returning zero while the chord error is 30.7 mm.

**The 4.5 m, stated rather than absorbed.** The face tier is dropped at 8.9 m although
its own error is honest only from 13.4 m. Two reasons, in order:

* **Nyquist.** The face tier's whole content is `zoff` windows on the front of the head.
  The narrowest that has to read is the lip vermilion at half 24°, so 48° of arc; at
  seg 16 the azimuth step is 22.5°, which is two samples across a lip and **one** across
  the philtrum. A ring bought to carry a feature the ring cannot sample is a ring bought
  for nothing.
* **Budget, and it is the harder constraint.** Carrying the face rings through seg 16 —
  the 8.9–28.1 m band, which holds most of a busy Zocalo — makes a figure 1,929
  triangles instead of 1,739, and `npc/crowd.py` answered by moving the Zocalo's
  impostor swap from **51.1 m to 33.4 m**, inside the 36 m floor that module sets so
  that "fix the overrun" can never mean "put cards on the people the player is talking
  to".

Between 8.9 m and 13.4 m a figure therefore carries **2.26 px** of deviation against a
1.5 px budget. `_detail_gate` part 5 (c) asserts that number against a declared 2.5 px
ceiling **and asserts it is over the 1.5 px budget**, so the compromise cannot be
quietly removed or quietly grown. It is the same kind of stated compromise
`populace.crowd_ladder` records for its near band.

**Weakest number.** `FACE_FORM_MIN_SEG = 32`. The Nyquist argument gives 15 for the lip
and 40 for the philtrum; 32 is inside that spread and the budget is what actually picks
it.

**What would overturn it.** A larger NPC frame share, or a runtime that can skin a body
per frame (which would remove `populace`'s shared-library constraint and with it the
whole reason the crowd is baked at one level).

---

## Two defects found in geometry older than this session

Not extrapolations. Recorded because they were found while building the above, and both
are fixed.

**`profile_schedule` measured a stride on the wrong mesh.** It built every figure at
`features="all"` and measured what a ring stride costs there. `lod_chain` composes the
schedules independently, so a stride is applied at levels whose ring plan is the **base**
tier — a stack with six fewer rings in it. The moment the form tier landed, the grome
torso's stride-4 error fell 0.1227 → 0.0749 purely because the measured torso had eleven
rings instead of eight, stride 2 and stride 4 became equally honest, and **the chain
silently dropped a level on the strength of geometry that level does not contain**. It
now sweeps every feature level and quotes the worst. Same shape as every gate this
repository has had to fix: it built the case without the defect in it.

**The species head-IoU gate rasterised a head five pixels wide.**
`silhouette_raster`'s default span is 0.75 of a stature either side, sized for a whole
figure with its arms out; a head is 0.048 of a stature to the side, so on the 64-column
grid the head band came out **3 to 13 columns across** and every pair score was quantised
to about a fifth of a head. Rebuilding the face moved human-vs-Narn from 0.875 to 0.911
in the front view and **the entire move was one pixel of a five-pixel shape** — measured
at a span that fits a head, the same pair reads 0.881 before and 0.884 after. The head
band now has its own raster: `HEAD_BAND_SPAN = 0.14`, derived from the widest head band
on the four gate species (a Narn's, at 0.1288 of its own height) with 9% of margin, and
`_detail_gate` asserts no species touches the raster edge, because a clipped silhouette
scores two different heads as identical at the clip.

**And a third, introduced this session and caught by a render.** `costume.py`'s standing
collar was sized by `_axis_at(torso_verts, 0.985)` because the torso's topmost ring
happened to be neck-sized. Giving the trapezius its lateral ridge made that measurement
46% larger and the close frame showed an EarthForce officer inside a bowl wider than his
own shoulders. A collar wraps the **neck**; it is measured off the neck part now, at 0.50
of its height × 1.15, which is 0.094 m against the 0.091 m the torso-derived measurement
used to give — the garment is the size it has always rendered at, and now for a reason.
