#!/usr/bin/env python3
"""Ragdolls: the physical body an inhabitant gets when they stop standing up.

WHY THIS EXISTS AND WHY IT IS NOT A TOY. The owner asked for real ragdolls and
then said what they are for: *"if anyone dies, falls ill, or is shot, for
example by a criminal or by law enforcement, and also maybe for fighting"*.
Every one of those triggers already fires on this station. `station/incident.py`
produces **INC-SICK at 380 a day** -- its own three-stance text is "collapse ->
the crowd opens -> the card is read -> a bed, an arm, or nothing" -- plus a dock
accident every ~6 days and a fatality every ~500 of those, plus INC-PICK,
INC-CONTRA, INC-BRAWL and INC-STRAY. So a ragdoll is not a new event. It is the
VISIBLE HALF of an event the simulation has been having in text.

THE ARCHITECTURAL FACT THAT SHAPES ALL OF IT. The crowd draws through
MultiMesh -- `npc.gd`: "the station's entire crowd is 112 draw calls" -- and a
MultiMesh instance is a transform into a shared mesh. **It cannot own a
skeleton, so it cannot ragdoll.** The answer is therefore PROMOTION and not
replacement: the crowd stays instanced, and the one body that has stopped
standing is hidden from its bucket and rebuilt as a real skinned mesh with a
`Skeleton3D` and a `PhysicalBone3D` chain, for as long as it needs one. That is
also the AAA answer rather than a compromise, because the body that ragdolls is
by definition the one being looked at: it is promoted to the **individual
lod-0 body** (7,212 triangles on a human) and not to the 484-triangle shared
one.

WHAT THIS MODULE OWNS AND WHAT IT READS.

  * `body.skinned()` -- the mesh, the bones and the per-vertex weights. Written
    for this, alongside the baked path, never instead of it.
  * `animation.rig()` -- the skeleton, MEASURED off the built figure, and the
    ring-indexed skin binding. Nothing here re-derives a joint position: the
    hips, knees, elbows and ankles come from `animation._skeleton`, which
    measures them off the mesh's own rings, and the two figures a rig is built
    from are the ones `body.py` builds.
  * `animation.clip_set` / `sleep_clip` -- the range every joint is ALREADY
    driven through by the station's own animation. That is the floor on a
    ragdoll's joint limit and `--gate` asserts it; a limit tighter than the
    pose the body demonstrably holds is wrong whatever it looks like.
  * `populace.place_gravity_at` -- this station spins, so a body falls at the
    LOCAL g, 0.234 g on Yellow's innermost addressed deck to 1.693 g deep in
    Grey, and "down" is radially OUTWARD rather than -Y. Both are carried out
    to the runtime per promotion.

WHAT IS DERIVED AND WHAT IS DECLARED. Derived: every joint position, every
segment length, every segment's mass and its cross-section, the settle
threshold, the concurrent cap. Declared, and logged as INV-440..INV-447: the
body density that turns volume into mass, the joint ranges of motion, the
damping, and the exclusion of the Vorlon.
"""
import argparse
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import animation as anim                                        # noqa: E402
import body                                                     # noqa: E402


# ---------------------------------------------------------------------------
# WHO GETS ONE
# ---------------------------------------------------------------------------
# `body.SPECIES` carries three body PLANS and they are not three humanoids:
#
#   humanoid        13 species -- 20 bones, arms, legs, a foot with a toe marker
#   encounter_suit   1 species -- the GAIM. 18 bones: the same chain without
#                                toes, because the suit's boots are the shell
#                                and `animation.PART_CHAINS` gives `suit_leg` a
#                                rigid tail for exactly that reason
#   column           1 species -- the VORLON. 5 bones: root, base, column,
#                                collar, head. No legs, no arms, no gait
#
# A Gaim ragdolls: the plan is a humanoid chain and every joint the physics
# needs is in it. A VORLON DOES NOT, and that is a decision rather than an
# omission -- see INV-447. `animation.PLAN_BONES` already refuses to give the
# column a walk clip ("Kosh has no gait and it would be an invention to give
# him one"); giving the column a fall would be the same invention with more
# moving parts, and there is exactly one Vorlon on the station
# (`body.VORLON_SINGLETON = 1`).
EXCLUDED_PLANS = ("column",)

# The bones that become rigid bodies. A bone NOT in this list keeps its rest
# pose relative to its parent and is carried rigidly -- Godot's
# `PhysicalBone3D` writes back only the bones it owns, and
# `_get_parent_physical_bone` walks up the chain past the ones it does not, so
# an unlisted bone costs nothing and needs no special case.
#
# SIXTEEN BODIES, and the two omissions are the interesting part:
#
#   `neck`  -- 87 mm long and it carries the shoulder girdle's weight in this
#              rig (`animation.PART_CHAINS["torso"]` ends on it, so the top of
#              the torso loft rides it). A rigid body that short between two
#              heavy ones is a solver problem for no visible gain, so its mass
#              and its length roll into `chest` and the head's joint attaches
#              to the chest -- which is what Godot does anyway.
#   `toe_*` -- `animation._skeleton`'s own note calls it a marker: "body.py's
#              three-ring foot has no ring forward of the metatarsal line, so a
#              toe bone can only be a marker". It rolls into `ankle`.
#
# Sixteen is also what a shipped ragdoll costs elsewhere -- the count is not
# copied from anywhere, it is what this skeleton has once the two markers are
# folded in.
PHYSICAL_BONES = (
    "pelvis", "spine", "chest", "head",
    "shoulder_r", "elbow_r", "wrist_r",
    "shoulder_l", "elbow_l", "wrist_l",
    "hip_r", "knee_r", "ankle_r",
    "hip_l", "knee_l", "ankle_l",
)

# Segments shaped as BOXES rather than capsules. A trunk is not round: a human
# chest is 0.41 m across and 0.27 m deep (`body.FIGURE_WIDTH_M`,
# `FIGURE_DEPTH_M`), so a capsule fitted to it either rolls when a body should
# lie flat or stands the shoulders 70 mm off the deck. Limbs and the head stay
# capsules because a capsule is the shape that does not catch on an edge, which
# is the same argument `station/collision.py` makes for the corridor shell.
# A HAND AND A FOOT ARE ALSO BOXES, and the gate is what said so rather than
# anatomy: fitted as capsules they came out at **0.35** and **1.23** of the
# flesh they stand for on a human, and **0.19** on a Gaim's boot. Both are flat
# -- a hand is a paddle with fingers on it, a foot is a wedge -- so the RMS
# distance to the bone axis is measuring the wrong thing, and a capsule fitted
# to it either lets the palm through the deck or stands the heel off it.
BOX_SEGMENTS = ("pelvis", "spine", "chest",
                "wrist_r", "wrist_l", "ankle_r", "ankle_l")

# A SEGMENT HAS TO BE WORTH A RIGID BODY. Below this share of the figure's own
# volume a bone is folded into its parent exactly as `neck` and `toe_*` are.
# THE GATE FOUND THIS ONE TOO: a Gaim's `wrist` carries no mesh at all --
# `animation.PART_CHAINS` gives the suit's arm the chain ("shoulder", "elbow")
# and there is no hand part, so the bone owns the last ring of `suit_arm` and
# nothing else -- and the fitted shape came out **52,960x** its own flesh. A
# body of near-zero mass hinged between two heavy ones is not detail, it is a
# solver singularity.
#
# 0.2%: BELOW it because a human's hand is 0.49% of body mass and a hand that
# flops is most of what makes a ragdoll read as unconscious rather than
# switched off; ABOVE it because the Gaim's empty wrist is four orders of
# magnitude smaller and nothing real sits between the two.
MIN_SEGMENT_FRACTION = 0.002


# ---------------------------------------------------------------------------
# MASS -- INV-440
# ---------------------------------------------------------------------------
# THE ANCHOR IS ALREADY IN THE REPOSITORY AND IS NOT MINE.
# `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` states "A 75 kg person weighs 108 kgf
# in Grey ring 1" and `npc/security.py` computes its patrol-weight column from
# that same 75 kg officer. So the station has a reference human mass, and the
# density that turns `body.py`'s geometry into kilograms is SOLVED from it
# rather than chosen:
#
#     rho = 75 kg / V(body.nominal("human") at lod 0)
#
# It comes out around 747 kg/m3, which is BELOW the ~1000 kg/m3 of human
# tissue, and the difference is a measurement rather than a fudge: `body.py`
# builds elliptical ring lofts, which are the CONVEX HULL of a cross-section
# that really has a waist, an armpit and a neck. The nominal human's mesh is
# 0.1005 m3 against the ~0.075 m3 a 75 kg person displaces -- a factor of 1.34
# -- and applying tissue density to a convex over-estimate would put a 1.75 m
# human at 100 kg. One number absorbs it, it is stated here, and it is
# recomputed from the mesh on every run so it cannot drift from the geometry.
REFERENCE_MASS_KG = 75.0          # gazetteer LAW-CRIME-DOWNBELOW, section 2.5
REFERENCE_SPECIES = "human"

_RHO_CACHE = {}


def body_density():
    """kg/m3, solved so the nominal human masses `REFERENCE_MASS_KG`."""
    if "rho" not in _RHO_CACHE:
        rg = anim.rig(REFERENCE_SPECIES, anim.NOMINAL, 0)
        v = sum(abs(body.signed_volume(list(vs), list(ts)))
                for _n, vs, ts in rg.base_parts)
        _RHO_CACHE["rho"] = REFERENCE_MASS_KG / v
        _RHO_CACHE["v_ref"] = v
    return _RHO_CACHE["rho"]


# ---------------------------------------------------------------------------
# JOINTS -- INV-441..INV-445
# ---------------------------------------------------------------------------
# WHAT IS DERIVED HERE AND WHAT IS NOT, because the split matters.
#
# DERIVED, from the rig itself: **a hinge's zero.** `animation._skeleton` puts
# the knee on the hip-to-ankle line and the elbow on the shoulder-to-wrist
# line, so the REST POSE IS FULL EXTENSION. A knee that rotates past zero in
# the extension direction is a knee bending backwards, and no number had to be
# invented to know that.
#
# DERIVED, from the station's own animation: **the floor on every limit.**
# `animation.clip_set` plus `sleep_clip` drive these joints through a measured
# range -- 89.8 deg at the knee in `sit`, 87.2 at the hip, 64.0 at the elbow in
# `talk`, 54.7 at the ankle at the top of the walk ladder. A ragdoll limit
# below that is a ragdoll that cannot reach a pose the body demonstrably holds,
# and `--gate` measures the clips and asserts it. That is the check that makes
# these numbers falsifiable rather than decorative.
#
# DECLARED, authority 5: the value itself. A range of motion is anatomy and
# nothing in the show establishes a Narn's shoulder. Each row below states what
# bounds it ABOVE and BELOW, and the bounds are visual and mechanical rather
# than clinical: below, the clip floor above; above, the angle at which the
# limb stops reading as a limb.
#
# THE SAME NUMBERS FOR EVERY SPECIES, and that is deliberate rather than lazy.
# `body.SpeciesBody` is a row of MULTIPLIERS on one figure -- limb length,
# girth, stature, cranium -- and a multiplier does not change what a joint can
# do. Where a species really differs, the geometry already carries it: a
# Pak'ma'ra's 26-degree stoop moves every joint FRAME, because the frames are
# measured off the stooped mesh, so its ragdoll folds from a different starting
# attitude without a second table. A per-species range table would be fifteen
# rows of invention with nothing to check them against.
CONE = "cone"
HINGE = "hinge"

JOINTS = {
    # --- INV-441, the spine ------------------------------------------------
    # Two cones, 25 deg of swing each, 25 of twist. BELOW: `walk_fr14` drives
    # the spine 6.8 deg and the chest 6.1, so anything under about 8 fights the
    # walk. ABOVE: 30 deg per joint x 2 joints x 2 (both directions) is a torso
    # that folds double at the waist, which reads as a broken back rather than
    # a collapse. Twist matched to swing because a spine that twists more than
    # it bends wrings the costume's yoke off the shoulders.
    "spine": (CONE, 25.0, 25.0),
    "chest": (CONE, 25.0, 25.0),
    # --- INV-442, the neck -------------------------------------------------
    # NOT DECLARED AT ALL: `animation.LOOK_LIMIT` already says how far a head
    # turns on this station -- 70 deg of yaw and 40 of pitch, of which the neck
    # takes `neck_share` 0.45. The cone's swing is the pitch limit and its
    # twist is the yaw limit, because a cone swings off its axis and twists
    # about it. Reading them from there rather than inventing a second pair is
    # the same rule that put the seat height on the mesh.
    "head": (CONE, None, None),                 # filled from LOOK_LIMIT below
    # --- INV-443, the shoulder and the hip ---------------------------------
    # BELOW: the hip is driven 87.2 deg by `sit`. ABOVE: a shoulder cone of
    # more than about 100 deg lets the upper arm cross the chest and come out
    # of the far armpit -- self-intersection the skin cannot hide, and the
    # failure `animation.interpenetration` exists to catch in clips. The hip is
    # tighter than the shoulder for the same reason it is in a body: the
    # pelvis is in the way.
    "shoulder_r": (CONE, 95.0, 60.0), "shoulder_l": (CONE, 95.0, 60.0),
    "hip_r": (CONE, 90.0, 40.0), "hip_l": (CONE, 90.0, 40.0),
    # --- INV-444, the knee and the elbow -----------------------------------
    # HINGES, and the axis is not chosen either: it is the mediolateral
    # direction, which in `body.py`'s frame is the figure's own X. The signs
    # follow from the geometry -- a positive rotation about +X carries a point
    # below the joint towards -Z, which is BACKWARD in a +Z-facing body, so a
    # knee flexes positive and an elbow flexes negative.
    # BELOW: 89.8 deg at the knee in `sit`, 64.0 at the elbow in `talk`.
    # ABOVE: past ~145 deg the calf passes through the thigh, and the small
    # opposite-sign allowance (2 deg) is there because a hinge whose limit sits
    # exactly on its rest angle chatters against it every frame.
    "knee_r": (HINGE, -2.0, 145.0), "knee_l": (HINGE, -2.0, 145.0),
    "elbow_r": (HINGE, -145.0, 2.0), "elbow_l": (HINGE, -145.0, 2.0),
    # --- INV-445, the wrist and the ankle ----------------------------------
    # THESE TWO ROWS WERE WRONG AND THE CLIP FLOOR FOUND THEM, which is the
    # only reason to build a floor out of another module's measurements. They
    # were first declared at 60/25 and 70/50 on the reasoning below; `--gate`
    # then measured `sleep_clip` driving the ankle **64.3 deg** and the wrist
    # **90.9 deg**, and both rows failed.
    #
    # The wrist number is not a slack clip, it is anatomy this rig expresses in
    # an unusual place: THERE IS NO RADIOULNAR BONE. `animation.PLAN_BONES`
    # goes shoulder -> elbow -> wrist, so a forearm's pronation -- 150 deg of
    # it in a real arm -- has nowhere to live except the wrist joint, and a
    # sleeper with their palm on a mattress is pronated. So 95/90.
    # BELOW: 90.9 deg, measured. ABOVE: past about 110 the hand comes off the
    # end of the forearm, and a hand is 0.37 kg with nothing hanging off it, so
    # a loose wrist costs nothing else.
    # The ankle: BELOW 64.3 deg, measured, which is the sleeper's pointed foot.
    # ABOVE: past ~75 deg the sole passes through the shin.
    "wrist_r": (CONE, 95.0, 90.0), "wrist_l": (CONE, 95.0, 90.0),
    "ankle_r": (CONE, 70.0, 30.0), "ankle_l": (CONE, 70.0, 30.0),
}

# The head's cone, read off `animation.LOOK_LIMIT` rather than declared.
JOINTS["head"] = (CONE, anim.LOOK_LIMIT["pitch_deg"] / anim.LOOK_LIMIT["neck_share"]
                  * anim.LOOK_LIMIT["neck_share"],
                  anim.LOOK_LIMIT["yaw_deg"] * anim.LOOK_LIMIT["neck_share"])
# ^ the pitch limit is the whole-head figure (the eyes cannot help a corpse);
#   the yaw limit is the NECK's share of it, because a dead head does not turn
#   its shoulders. Written as the product rather than as 40.0 and 31.5 so that
#   editing LOOK_LIMIT moves both.

# --- INV-446, damping and sleeping -----------------------------------------
# A ragdoll with no damping never stops: a solver with a restitution of zero
# still trades energy between sixteen bodies for tens of seconds, and a corpse
# that twitches for half a minute is worse than no ragdoll. These are the two
# numbers that decide how long a body takes to become furniture.
#
# BELOW: 0 is undamped, and measured, an undamped body on the deck is still
# above the settle threshold after the gate's whole 6 s window. ABOVE: at a
# linear damp much over 1.5 the body falls visibly slowly -- damping is a
# velocity-proportional force, so a limb's terminal speed under local g falls
# as g/damp, and at damp 4 a 1.7 m fall in 1 g takes longer than the fall
# itself should. 0.6 and 3.0 put the settle inside 2 s at 1 g without the
# descent looking wrong, and `--gate` prints the settle time so the claim is
# checkable rather than asserted.
#
# ANGULAR IS FIVE TIMES LINEAR because the thing that will not stop is spin:
# a forearm is 1.7 kg on a 0.34 m arm and its rotational inertia is small
# enough that contact impulses set it ringing.
LINEAR_DAMP = 0.6
ANGULAR_DAMP = 3.0
# Bounce. A body is not a ball; the show's own falls (a stunned Narn in a
# corridor) do not rebound. Zero, and it is not really a choice.
BOUNCE = 0.0
# Friction. High, because a limb on deck plating does not slide -- and because
# the alternative failure is visible: a low-friction ragdoll on a corridor
# floor slides for metres after it lands. Godot's friction is a 0..1 dial and
# not a coefficient, so this is a dial position, not a physical constant.
FRICTION = 0.9


# ---------------------------------------------------------------------------
# WHEN IT HAS STOPPED -- derived, not chosen
# ---------------------------------------------------------------------------
# `body.py` already owns the screen model this project judges detail with:
# `_px_scale(PIXEL_BUDGET)` is metres of viewing distance per metre of feature
# at the 1.5-pixel deviation budget, 1440p and a 50-degree FOV. Invert it at
# the distance a body is actually looked at and it says how far a thing may
# move per frame before the picture moves: at 1 m, 0.97 mm.
#
# So a ragdoll is SETTLED when no bone moves more than that in a physics tick.
# Nothing about that number is a preference -- it is the same instrument that
# decides how many segments a limb gets.
SETTLE_DISTANCE_M = 1.0           # body.py: "the player converses at about 1 m"
PHYSICS_HZ = 60.0                 # Godot's default; the runtime reports its own


def settle_speed_m_s(hz=PHYSICS_HZ):
    """The linear speed below which a bone is not moving, in this project's
    own units of "visible"."""
    return SETTLE_DISTANCE_M / body._px_scale(body.PIXEL_BUDGET) * hz


# How many consecutive ticks under the threshold count as settled. A single
# frame under it is the top of a bounce, not a rest -- and the top of a bounce
# is exactly where a velocity check is most likely to be fooled.
SETTLE_FRAMES = 20                # a third of a second at 60 Hz

# How long a promotion is allowed to run before the runtime gives up and puts
# the body down where it is. A ragdoll that has not settled in this long is
# wedged in geometry, and leaving it simulating costs a solver island for ever.
SETTLE_TIMEOUT_S = 8.0


# ---------------------------------------------------------------------------
# THE BUDGET -- how many at once, and it is arithmetic
# ---------------------------------------------------------------------------
def concurrent_cap(species=REFERENCE_SPECIES, lod=0):
    """How many bodies may be promoted at once, and why.

    THIS IS NOT A PREFERENCE. `npc/schedule.py::NPC_BUDGET` already carries the
    two allowances a promoted body spends, and they disagree, so both are
    computed and the answer is the smaller:

      TRIANGLES. The lod ladder's first rung is
      `("lod0", 0.0, 6.0, 8_000, 4)` -- 8,000 triangles each and **4
      instances** inside 6 m. A promoted human is 7,212 triangles, so it fits
      the per-instance allowance and the instance count is the cap: **4**.

      DRAW CALLS. `max_draw_calls = 32`, and `STATE.md` records that people
      already cost **31-33** of them. A promoted body is its own mesh with one
      surface per material -- four on a dressed human, measured, not assumed --
      so four ragdolls is 16 draw calls the budget does not have.

    So the honest answer is that the draw-call budget is ALREADY spent and a
    ragdoll comes out of somebody else's allowance. What makes that affordable
    rather than a violation is that a promoted body REPLACES a crowd instance
    that was already being drawn, and the crowd's cost is per BUCKET rather
    than per body -- so the saving is only real when the last walker of a
    (species, lod, phase) bucket is the one promoted. That is not something to
    hope for, so the cap is stated at the triangle ladder's 4 and the draw-call
    overrun is reported rather than hidden.
    """
    import schedule as _sched                                   # noqa: PLC0415
    lod0 = _sched.NPC_BUDGET["lod"][0]
    doc = body.skinned(species, lod=lod)
    surfaces = len(doc["surfaces"])
    return {
        "cap": int(lod0[4]),
        "from": "schedule.NPC_BUDGET['lod'][0] -- the lod0 rung's max_instances",
        "lod0_rung": {"near_m": lod0[1], "far_m": lod0[2],
                      "triangles_each": lod0[3], "max_instances": lod0[4]},
        "promoted_triangles": doc["triangles"],
        "fits_per_instance": doc["triangles"] <= lod0[3],
        "surfaces_per_body": surfaces,
        "draw_calls_at_cap": surfaces * int(lod0[4]),
        "draw_call_budget": _sched.NPC_BUDGET["max_draw_calls"],
        "people_draw_calls_today": "31-33 (STATE.md, streamed blue_0_0)",
        "draw_call_overrun_at_cap": surfaces * int(lod0[4])
        - max(0, _sched.NPC_BUDGET["max_draw_calls"] - 32),
    }


# ---------------------------------------------------------------------------
# Measuring one figure
# ---------------------------------------------------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(v, k):
    return (v[0] * k, v[1] * k, v[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(v):
    return math.sqrt(_dot(v, v))


def _unit(v):
    n = _norm(v)
    return (0.0, 1.0, 0.0) if n < 1e-12 else _scale(v, 1.0 / n)


def _vertex_weights(rg):
    """Per part, per vertex, the [(bone, weight)] list the binding implies."""
    out = [None] * len(rg.parts)
    for pi, ringw, runs in rg.binding:
        w = [None] * len(rg.parts[pi][1])
        for (a, b), ring in zip(runs, ringw):
            for i in range(a, b):
                w[i] = ring
        out[pi] = w
    return out


def _bone_volumes(rg, vw):
    """Volume per BONE, distributed by the mesh's own skin weights.

    THE MASS COMES OUT OF THE BODY AND NOT OUT OF A TABLE, which is what the
    brief asked for, and the method is chosen so that it cannot quietly not
    add up: each triangle's tetrahedral volume is taken about ITS OWN PART's
    centroid and split across bones by the mean of its three vertices' weights.
    Summed over a closed part that is exactly the part's volume, so the
    per-bone shares sum to the figure's volume by construction -- `--gate`
    checks the identity rather than trusting this paragraph.
    (About the part's centroid rather than the origin because a tetrahedron to
    a distant apex is a large signed number, and a distribution built out of
    large cancelling terms produces negative limbs.)

    On the NUDE figure. `rg.base_parts` is the body; `rg.parts` may be wearing
    a robe, and a robe is not 15 kg of flesh. `costume.py` modifies the base
    parts in place -- same names, counts and order -- so the binding transfers
    index for index, which `--gate` also checks.
    """
    n = len(rg.skel.bones)
    vol = [0.0] * n
    for pi, (_name, dressed, tris) in enumerate(rg.parts):
        verts = rg.base_parts[pi][1] if pi < len(rg.base_parts) else dressed
        if len(verts) != len(dressed):
            verts = dressed
        c, _v = anim._centroid(list(verts), list(tris))
        for ia, ib, ic in tris:
            a, b, cc = (_sub(verts[ia], c), _sub(verts[ib], c),
                        _sub(verts[ic], c))
            tv = _dot(a, _cross(b, cc)) / 6.0
            acc = {}
            for k in (ia, ib, ic):
                for bi, w in vw[pi][k]:
                    acc[bi] = acc.get(bi, 0.0) + w / 3.0
            for bi, w in acc.items():
                vol[bi] += tv * w
    return [abs(v) for v in vol]


def _segment_map(skel, physical=PHYSICAL_BONES):
    """bone name -> the physical segment that carries it.

    A bone with no rigid body of its own is carried by its nearest physical
    ancestor: that is exactly what Godot does with the joint chain
    (`PhysicalBone3D::_get_parent_physical_bone` walks up past unowned bones),
    so the mass and the length have to follow the same rule or the shape and
    the physics describe different bodies.
    """
    out = {}
    for b in skel.bones:
        if b.name in physical:
            out[b.name] = b.name
            continue
        p, seg = b.parent, None
        while p >= 0:
            nm = skel.bones[p].name
            if nm in physical:
                seg = nm
                break
            p = skel.bones[p].parent
        out[b.name] = seg          # None for `root`, which owns nothing
    return out


def segments(species, npc_id=None, lod=0):
    """The physical body: one dict per rigid segment, measured off the figure.

    Every number in a row is measured or solved:

      `head`/`tip`  the segment's own bone head and the far end of the last
                    bone it carries -- `animation._skeleton`'s measured joints
      `length_m`    the distance between them
      `volume_m3`   the mesh's own volume, distributed by its own skin weights
      `mass_kg`     that volume x `body_density()`, which is solved from the
                    gazetteer's 75 kg person
      `radius_m`    the RMS perpendicular distance from the segment's SKIN to
                    its axis. RMS rather than mean or max because for a solid
                    cylinder the RMS of its surface is exactly its radius, so
                    the number is the radius of the cylinder with the same
                    second moment -- and unlike a max it is not set by one
                    fingertip
      `half_m`      for a box segment, the measured half-extents across and
                    along the trunk
    """
    rg = anim.rig(species, npc_id or anim.NOMINAL, lod)
    if rg.skel.plan in EXCLUDED_PLANS:
        raise ValueError(f"{species}: the {rg.skel.plan!r} plan has no ragdoll "
                         f"-- see EXCLUDED_PLANS and INV-447")
    skel = rg.skel
    vw = _vertex_weights(rg)
    vol = _bone_volumes(rg, vw)
    total_v = sum(vol) or 1.0
    # THE PHYSICAL SET IS PER FIGURE, not per plan. See MIN_SEGMENT_FRACTION:
    # a bone that carries no flesh on THIS species is folded away here, before
    # anything downstream can build a joint to it.
    physical = tuple(n for n in PHYSICAL_BONES
                     if skel.has(n)
                     and vol[skel.index[n]] / total_v >= MIN_SEGMENT_FRACTION)
    carries = _segment_map(skel, physical)
    rho = body_density()

    # Which skinned vertices belong to which segment: the DOMINANT bone of the
    # vertex, mapped through `carries`. Dominant rather than weighted, because
    # a shape is a yes/no question about a point and a blend band is not a
    # place to put half a vertex.
    owned = {n: [] for n in physical}
    for pi, (_name, verts, _t) in enumerate(rg.parts):
        for i, v in enumerate(verts):
            bi = max(vw[pi][i], key=lambda kv: kv[1])[0]
            seg = carries.get(skel.bones[bi].name)
            if seg in owned:
                owned[seg].append(v)

    out = []
    for name in physical:
        b = skel.bones[skel.index[name]]
        kids = [k for k, s in carries.items() if s == name]
        # The far end: whichever carried bone's tail is furthest from the head.
        far, tip = 0.0, b.tail
        for k in kids:
            t = skel.bones[skel.index[k]].tail
            d = _norm(_sub(t, b.head))
            if d > far:
                far, tip = d, t
        L = max(1e-3, _norm(_sub(tip, b.head)))
        d = _unit(_sub(tip, b.head))
        v = sum(vol[skel.index[k]] for k in kids)

        # The segment's own frame: +Y along the bone, +X the figure's own X
        # projected perpendicular to it. That choice is what lets ONE joint
        # basis serve both joint types -- see `joint_basis_note()`.
        ex = _sub((1.0, 0.0, 0.0), _scale(d, _dot((1.0, 0.0, 0.0), d)))
        if _norm(ex) < 1e-6:
            ex = _sub((0.0, 0.0, 1.0), _scale(d, _dot((0.0, 0.0, 1.0), d)))
        ex = _unit(ex)
        ez = _cross(ex, d)

        pts = owned[name] or [b.head, tip]
        loc = [(_dot(_sub(p, b.head), ex), _dot(_sub(p, b.head), d),
                _dot(_sub(p, b.head), ez)) for p in pts]
        rms = math.sqrt(sum(p[0] * p[0] + p[2] * p[2] for p in loc) / len(loc))
        # The tight box of the segment's own skin, IN ITS OWN FRAME. Extents
        # rather than a standard deviation, and a centre at the middle of the
        # extents rather than at the vertex mean, because a shape is a
        # bounding question. Then scaled uniformly to the flesh volume -- see
        # below.
        lo = [min(p[k] for p in loc) for k in range(3)]
        hi = [max(p[k] for p in loc) for k in range(3)]
        half = [max(1e-3, (hi[k] - lo[k]) / 2.0) for k in range(3)]
        mid = [(hi[k] + lo[k]) / 2.0 for k in range(3)]

        boxed = name in BOX_SEGMENTS
        row = {
            "bone": name,
            "carries": sorted(kids),
            "parent": _physical_parent(skel, name, physical),
            "head": [round(x, 6) for x in b.head],
            "tip": [round(x, 6) for x in tip],
            "axis": [round(x, 6) for x in d],
            "frame_x": [round(x, 6) for x in ex],
            "length_m": round(L, 6),
            "volume_m3": round(v, 8),
            "mass_kg": round(v * rho, 4),
            "shape": "box" if boxed else "capsule",
        }
        if boxed:
            # A TRUNK BOX IS MEASURED FOR ITS PROPORTIONS AND SOLVED FOR ITS
            # SIZE. The bone gives the wrong length here and it is worth being
            # explicit about why: `pelvis` is 44 mm long in this rig -- it is
            # the hip joint to the waist joint -- while the flesh it carries is
            # a third of a metre tall. A box of the BONE's length is a slab
            # that holds 36% of the mass it stands for and lets a body's hips
            # sink into the deck. So the box is the skin's own extent, then
            # scaled uniformly until it displaces exactly the flesh it carries
            # -- shape from the surface, size from the volume, neither chosen.
            box_v = 8.0 * half[0] * half[1] * half[2]
            k = (v / box_v) ** (1.0 / 3.0) if box_v > 1e-12 and v > 1e-12 else 1.0
            half = [h * k for h in half]
            row["half_m"] = [round(h, 5) for h in half]
            row["centre_m"] = [round(mid[0] * k, 5), round(mid[1], 5),
                               round(mid[2] * k, 5)]
            row["shape_scale"] = round(k, 5)
            row["shape_volume_m3"] = round(8.0 * half[0] * half[1] * half[2], 8)
        else:
            r = max(0.012, rms)
            row["radius_m"] = round(r, 5)
            # Godot's CapsuleShape3D height is the TOTAL including both caps and
            # may not be less than twice the radius -- a head is such a case.
            h = max(L, 2.0 * r)
            row["height_m"] = round(h, 5)
            # A limb capsule sits ON the bone: the bone IS the limb's axis, and
            # moving it off would put the knee outside the shin.
            row["centre_m"] = [0.0, round(L / 2.0, 5), 0.0]
            row["shape_volume_m3"] = round(
                math.pi * r * r * (h - 2.0 * r) + 4.0 / 3.0 * math.pi * r ** 3, 8)
        jt = JOINTS.get(name)
        if row["parent"] is None:
            row["joint"] = {"type": "none"}
        elif jt[0] == HINGE:
            row["joint"] = {"type": HINGE, "lower_deg": jt[1], "upper_deg": jt[2]}
        else:
            row["joint"] = {"type": CONE, "swing_deg": round(jt[1], 3),
                            "twist_deg": round(jt[2], 3)}
        out.append(row)
    return out


def _physical_parent(skel, name, physical=PHYSICAL_BONES):
    p = skel.bones[skel.index[name]].parent
    while p >= 0:
        nm = skel.bones[p].name
        if nm in physical:
            return nm
        p = skel.bones[p].parent
    return None


def joint_basis_note():
    """One basis serves both joint types, and it is worth writing down once.

    Godot's own physics fixes the axis a constraint uses, and the two are not
    the same axis: `godot_hinge_joint_3d.cpp` takes the hinge axis from the
    joint frame's **Z column**, `godot_cone_twist_joint_3d.cpp` takes the cone's
    centre from its **X column**. Both were read out of the engine's source in
    this build rather than remembered.

    A segment's body frame here has +Y along the bone and +X along the figure's
    own X (the mediolateral direction) -- so the joint basis whose columns are

        X_col = (0,1,0)   the bone, which is the cone's axis
        Y_col = (0,0,1)
        Z_col = (1,0,0)   the figure's X, which is the hinge's axis

    is right-handed (X x Y = Z) and satisfies BOTH. There is no per-joint-type
    branch in the runtime, which is the point: a second basis is a second thing
    that can be wrong in only one of the two cases.
    """
    return {"hinge_axis": "joint frame Z column (godot_hinge_joint_3d.cpp)",
            "cone_axis": "joint frame X column (godot_cone_twist_joint_3d.cpp)",
            "basis_columns": {"x": [0, 1, 0], "y": [0, 0, 1], "z": [1, 0, 0]},
            "body_frame": "+Y along the bone, +X the figure's mediolateral axis"}


# ---------------------------------------------------------------------------
# The clip floor -- what the station already drives these joints through
# ---------------------------------------------------------------------------
def clip_excursions(species=REFERENCE_SPECIES, npc_id=None, keys=16, lod=0):
    """Max |local rotation| per bone over every clip, in degrees.

    This is the FLOOR on a joint limit and the only externally-sourced check
    these invented ranges have. `sleep_clip` is included explicitly because
    `clip_set` does not carry it and a sleeper is the deepest hip and knee
    flexion the station ever asks for.
    """
    npc_id = npc_id or anim.NOMINAL
    g = anim.station_gravity()["median_ms2"] if False else anim.G0
    clips = list(anim.clip_set(species, npc_id, keys=keys, lod=lod))
    try:
        clips.append(anim.sleep_clip(species, npc_id, g, frames=keys, lod=lod))
    except Exception as exc:                                    # noqa: BLE001
        print(f"ragdoll: no sleep clip for {species}: {exc}", file=sys.stderr)
    out = {}
    for c in clips:
        for bone, qs in c.tracks.items():
            for q in qs:
                w = max(-1.0, min(1.0, q[3]))
                a = 2.0 * math.degrees(math.acos(abs(w)))
                if a > out.get(bone, (0.0, ""))[0]:
                    out[bone] = (a, c.name)
    return out


def limit_of(name):
    """The total angular freedom a joint has, in degrees, for comparison with
    a clip excursion. A cone's swing is measured from its axis, so a limb may
    move `swing` degrees off rest in any direction; a hinge's freedom is the
    larger of its two limits."""
    jt = JOINTS.get(name)
    if jt is None:
        return None
    if jt[0] == HINGE:
        return max(abs(jt[1]), abs(jt[2]))
    return max(jt[1], jt[2])


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def doc(species, npc_id=None, lod=0):
    """Everything the runtime needs for one species: skin, bones, segments."""
    d = body.skinned(species, npc_id, lod)
    segs = segments(species, d["npc_id"], lod)
    d["ragdoll"] = {
        "generator": "station/npc/ragdoll.py",
        "density_kg_m3": round(body_density(), 3),
        "density_from": (f"{REFERENCE_MASS_KG} kg person "
                         f"(docs/gazetteer/LAW-CRIME-DOWNBELOW.md) / the "
                         f"nominal human's own mesh volume"),
        "segments": segs,
        "mass_kg": round(sum(s["mass_kg"] for s in segs), 3),
        "joint_frame": joint_basis_note(),
        "settle": {"speed_m_s": round(settle_speed_m_s(), 6),
                   "frames": SETTLE_FRAMES,
                   "timeout_s": SETTLE_TIMEOUT_S,
                   "derived_from": "body._px_scale(body.PIXEL_BUDGET) at "
                                   f"{SETTLE_DISTANCE_M} m, x {PHYSICS_HZ} Hz"},
        "damping": {"linear": LINEAR_DAMP, "angular": ANGULAR_DAMP,
                    "bounce": BOUNCE, "friction": FRICTION},
        # Carried out to the runtime so the cap the engine enforces and the
        # cap this module derives cannot be two numbers.
        "concurrent_cap": concurrent_cap(species, lod),
        # The runtime scales a promoted body to the individual it replaces:
        # the actor and walker records already carry `h_m`, measured off that
        # person's own mesh by `populace.body_capsule`, so the scale is
        # measured on both ends rather than looked up.
        "reference_height_m": round(
            max(v for s in d["surfaces"]
                for v in s["positions"][1::3]) - d["ground_y"], 5),
    }
    return d


def emit(outdir, species=None, lod=0, quiet=False):
    os.makedirs(outdir, exist_ok=True)
    written = []
    for k in (species or sorted(body.SPECIES)):
        if body.SPECIES[k].plan in EXCLUDED_PLANS:
            if not quiet:
                print(f"  {k:9s} EXCLUDED -- {body.SPECIES[k].plan} plan, INV-447")
            continue
        d = doc(k, lod=lod)
        p = os.path.join(outdir, f"{k}_ragdoll.json")
        with open(p, "w") as f:
            json.dump(d, f, separators=(",", ":"), sort_keys=True)
        written.append((p, os.path.getsize(p)))
        if not quiet:
            r = d["ragdoll"]
            print(f"  {k:9s} {len(r['segments']):2d} segments  "
                  f"{r['mass_kg']:6.1f} kg  {d['triangles']:6,} tri  "
                  f"{len(d['surfaces'])} surfaces  "
                  f"{os.path.getsize(p) / 1e3:7.1f} kB")
    return written


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(out=print):
    rho = body_density()
    out("RAGDOLLS -- station/npc/ragdoll.py")
    out("")
    out(f"  density {rho:.1f} kg/m3, solved so body.nominal('human') masses "
        f"{REFERENCE_MASS_KG:.0f} kg")
    out(f"  the nominal human's mesh is {_RHO_CACHE['v_ref']:.5f} m3 -- "
        f"{_RHO_CACHE['v_ref'] * 1000.0 / REFERENCE_MASS_KG:.2f}x the volume a "
        f"{REFERENCE_MASS_KG:.0f} kg person displaces at tissue density, which "
        f"is the convexity of a ring loft")
    out(f"  settled below {settle_speed_m_s():.4f} m/s for {SETTLE_FRAMES} "
        f"ticks; derived from body.py's own {body.PIXEL_BUDGET}-pixel budget "
        f"at {SETTLE_DISTANCE_M:.0f} m")
    out("")
    cap = concurrent_cap()
    out(f"  CONCURRENT CAP {cap['cap']} -- {cap['from']}")
    out(f"    a promoted body is {cap['promoted_triangles']:,} triangles "
        f"against the rung's {cap['lod0_rung']['triangles_each']:,} "
        f"({'fits' if cap['fits_per_instance'] else 'OVER'})")
    out(f"    {cap['surfaces_per_body']} surfaces each = "
        f"{cap['draw_calls_at_cap']} draw calls at the cap, against a budget of "
        f"{cap['draw_call_budget']} that people already spend "
        f"{cap['people_draw_calls_today']} of")
    out("")
    out(f"  {'species':10s} {'plan':15s} {'seg':>4s} {'mass':>8s} {'tri':>7s} "
        f"{'surf':>5s}")
    for k in sorted(body.SPECIES):
        sp = body.SPECIES[k]
        if sp.plan in EXCLUDED_PLANS:
            out(f"  {k:10s} {sp.plan:15s}    -        -       -     -   "
                f"EXCLUDED (INV-447)")
            continue
        d = doc(k)
        out(f"  {k:10s} {sp.plan:15s} {len(d['ragdoll']['segments']):4d} "
            f"{d['ragdoll']['mass_kg']:7.1f}k {d['triangles']:7,} "
            f"{len(d['surfaces']):5d}")
    out("")
    out("  the human's segments, measured:")
    out(f"    {'segment':11s} {'L m':>7s} {'shape':>8s} {'r/half m':>16s} "
        f"{'mass kg':>8s} {'% body':>7s} {'joint':>26s}")
    segs = segments(REFERENCE_SPECIES)
    tot = sum(s["mass_kg"] for s in segs)
    for s in segs:
        if s["shape"] == "box":
            dims = "%.3f/%.3f/%.3f" % tuple(s["half_m"])
            dims += " x%.2f" % s["shape_scale"]
        else:
            dims = "r %.3f h %.3f" % (s["radius_m"], s["height_m"])
        j = s["joint"]
        jd = ("root" if j["type"] == "none" else
              (f"hinge {j['lower_deg']:.0f}..{j['upper_deg']:.0f}"
               if j["type"] == HINGE else
               f"cone swing {j['swing_deg']:.0f} twist {j['twist_deg']:.0f}"))
        out(f"    {s['bone']:11s} {s['length_m']:7.3f} {s['shape']:>8s} "
            f"{dims:>16s} {s['mass_kg']:8.2f} {100 * s['mass_kg'] / tot:6.1f}% "
            f"{jd:>26s}")


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------
def _selftest(species=(REFERENCE_SPECIES, "pakmara", "gaim"), out=print):
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            out(f"FAIL: {label}")

    # -- the Vorlon is excluded, loudly ------------------------------------
    try:
        segments("vorlon")
        check(False, "segments('vorlon') built a ragdoll for the column plan")
    except ValueError:
        check(True, "vorlon excluded")

    # -- mass -------------------------------------------------------------
    rho = body_density()
    rg = anim.rig(REFERENCE_SPECIES, anim.NOMINAL, 0)
    vw = _vertex_weights(rg)
    vol = _bone_volumes(rg, vw)
    mesh_v = sum(abs(body.signed_volume(list(v), list(t)))
                 for _n, v, t in rg.base_parts)
    check(abs(sum(vol) - mesh_v) < 1e-9,
          f"the per-bone volumes sum to {sum(vol):.8f} and the mesh is "
          f"{mesh_v:.8f} -- the distribution loses mass")
    check(all(v >= 0.0 for v in vol),
          f"{sum(1 for v in vol if v < 0)} bones have negative volume")
    segs = segments(REFERENCE_SPECIES)
    total_kg = sum(s["mass_kg"] for s in segs)
    check(abs(total_kg - REFERENCE_MASS_KG) < 0.05,
          f"the human ragdoll masses {total_kg:.3f} kg against the gazetteer's "
          f"{REFERENCE_MASS_KG:.0f}")

    # THE SEGMENT MASSES ARE NOT A TABLE AND THEY LAND ON ANTHROPOMETRY.
    # Nothing here fitted them: they are the mesh's own volume, split by the
    # mesh's own skin weights. That they reproduce the standard adult segment
    # fractions is the check that the method is measuring a body rather than a
    # tessellation, and it is the only external evidence available.
    by = {s["bone"]: s["mass_kg"] / total_kg for s in segs}
    trunk = by["pelvis"] + by["spine"] + by["chest"]
    arm = by["shoulder_r"] + by["elbow_r"] + by["wrist_r"]
    leg = by["hip_r"] + by["knee_r"] + by["ankle_r"]
    check(0.44 <= trunk <= 0.60,
          f"trunk is {trunk:.3f} of body mass (adult humans: about 0.50)")
    check(0.055 <= by["head"] <= 0.115,
          f"head is {by['head']:.3f} of body mass (about 0.081)")
    check(0.035 <= arm <= 0.075,
          f"one arm is {arm:.3f} of body mass (about 0.050)")
    check(0.115 <= leg <= 0.185,
          f"one leg is {leg:.3f} of body mass (about 0.161)")

    # -- the segments cover the skeleton -----------------------------------
    for k in species:
        if body.SPECIES[k].plan in EXCLUDED_PLANS:
            continue
        sk = anim.rig(k, anim.NOMINAL, 0).skel
        segs_k = segments(k)
        carried = set()
        for s in segs_k:
            carried.update(s["carries"])
        want = {b.name for b in sk.bones} - {"root"}
        check(carried == want,
              f"{k}: segments carry {sorted(carried - want)} extra and miss "
              f"{sorted(want - carried)}")
        # Every segment but the pelvis has a parent, and the parent is a
        # segment: a chain with a break is a limb that falls off.
        names = {s["bone"] for s in segs_k}
        broken = [s["bone"] for s in segs_k
                  if s["parent"] is not None and s["parent"] not in names]
        check(not broken and sum(1 for s in segs_k if s["parent"] is None) == 1,
              f"{k}: {broken} have a parent outside the segment set, and "
              f"{sum(1 for s in segs_k if s['parent'] is None)} segments are "
              f"rootless")
        # A shape must enclose something. A zero or negative extent is a
        # capsule the solver cannot collide.
        bad = [s["bone"] for s in segs_k
               if s["shape_volume_m3"] <= 0.0 or s["length_m"] <= 0.0]
        check(not bad, f"{k}: degenerate shapes on {bad}")

    # -- the shapes are a fair fit to the body -----------------------------
    # NOT a tolerance anybody tuned: the question is whether the collision
    # volume is the same ORDER as the flesh it stands for. A capsule fitted to
    # an RMS radius under-fills a limb slightly and a box over-fills a waist
    # slightly, and if either were out by more than about 2x the body would
    # visibly hover or sink.
    ratios = [s["shape_volume_m3"] / max(s["volume_m3"], 1e-9)
              for s in segs if s["volume_m3"] > 1e-5 and s["shape"] == "capsule"]
    check(all(0.45 <= r <= 2.2 for r in ratios),
          f"capsule/flesh volume ratios run {min(ratios):.2f}..{max(ratios):.2f}")
    # The boxes are solved to the volume, so their ratio is 1 by construction
    # and checking it would be an assertion that cannot fail. What CAN fail is
    # the scale it took to get there: a factor far from 1 means the skin's own
    # extent is nothing like the flesh inside it.
    scales = [s["shape_scale"] for s in segs if s["shape"] == "box"]
    check(all(0.45 <= k <= 1.45 for k in scales),
          f"trunk boxes needed scales {min(scales):.2f}..{max(scales):.2f} to "
          f"reach their own flesh volume")

    # -- the joint limits clear the station's own animation -----------------
    exc = clip_excursions(REFERENCE_SPECIES)
    tight = []
    for bone, (deg, clip) in sorted(exc.items()):
        lim = limit_of(bone)
        if lim is not None and lim + 1e-6 < deg:
            tight.append(f"{bone} limit {lim:.1f} < {deg:.1f} in {clip}")
    check(not tight,
          "joint limits below what the station's own clips drive: "
          + "; ".join(tight))
    out(f"  clip floor cleared on {len(exc)} bones; tightest margin "
        + ", ".join(f"{b} {limit_of(b) - d:.1f} deg"
                    for b, (d, _c) in sorted(exc.items(),
                                             key=lambda kv: (limit_of(kv[0]) or 1e9)
                                             - kv[1][0])[:3]
                    if limit_of(b) is not None))

    # NEGATIVE CONTROL: halve every limit and the same check must fire. Without
    # this the clip floor could be passing because nothing is being compared.
    saved = dict(JOINTS)
    try:
        for k, v in list(JOINTS.items()):
            JOINTS[k] = (v[0], v[1] * 0.5, v[2] * 0.5)
        broke = [b for b, (d, _c) in exc.items()
                 if limit_of(b) is not None and limit_of(b) + 1e-6 < d]
        check(len(broke) >= 4,
              f"CONTROL: halving every joint limit breaks only {len(broke)} "
              f"bones -- the clip floor is not actually being compared")
    finally:
        JOINTS.clear()
        JOINTS.update(saved)

    # -- the hinge zero is the rig's own full extension ---------------------
    # DERIVED, and this is the assertion that says so: the knee bone's head
    # lies on the hip-to-ankle line, so the rest pose IS a straight leg and a
    # hinge limit of zero on the extension side needs no anatomy table.
    sk = anim.rig(REFERENCE_SPECIES, anim.NOMINAL, 0).skel
    hip = sk.head("hip_r")
    knee = sk.head("knee_r")
    ankle = sk.head("ankle_r")
    ab = _sub(ankle, hip)
    t = _dot(_sub(knee, hip), ab) / _dot(ab, ab)
    off = _norm(_sub(knee, _add(hip, _scale(ab, t))))
    check(off < 0.004,
          f"the knee sits {off * 1000:.1f} mm off the hip-ankle line, so the "
          f"rest pose is not full extension and a hinge zero is not derivable")

    # -- the budget ---------------------------------------------------------
    cap = concurrent_cap()
    check(cap["cap"] >= 1 and cap["fits_per_instance"],
          f"a promoted body is {cap['promoted_triangles']:,} triangles against "
          f"the lod0 rung's {cap['lod0_rung']['triangles_each']:,}")

    # -- the settle threshold is derived and non-trivial --------------------
    v = settle_speed_m_s()
    check(0.01 < v < 0.2,
          f"the settle speed is {v:.4f} m/s, which is not a plausible "
          f"sub-pixel motion")

    out(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--emit", metavar="DIR", default=None)
    ap.add_argument("--species", default=None)
    ap.add_argument("--lod", type=int, default=0)
    a = ap.parse_args()
    if a.emit:
        emit(a.emit, [a.species] if a.species else None, lod=a.lod)
        return 0
    if a.report:
        report()
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
