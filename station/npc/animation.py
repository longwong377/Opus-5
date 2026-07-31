#!/usr/bin/env python3
"""NPC animation: one skeleton, four clips, and a gait that knows what deck it
is standing on.

A station full of statues is worse than an empty one, and until this file
existed `station/npc/` could produce a quarter of a million people who could not
move. This module produces ANIMATION DATA, not a runtime: a skeleton definition,
a skin binding, and procedurally generated clips, all deterministic and all
consumable by Godot (ADR 0001/0003 -- heavy generation happens offline in
Python, the runtime consumes committed data).

WHAT IS UNIQUE HERE, AND WHY IT IS NOT DECORATION
--------------------------------------------------
Babylon 5 is a rigid body spinning at a rate fixed by canon, so "gravity" is
omega^2*r and it is DIFFERENT ON EVERY DECK. `station/interior.py` puts habitable
floors between 0.12 g and 1.246 g, and plant decks -- where Downbelow lives --
out to 1.693 g. A walk cycle is not a decoration laid over that: cadence, stride,
duty factor and swing time are all functions of g, and a single baked walk played
everywhere would be visibly wrong in two thirds of the station.

So the gait here is DERIVED from two pieces of mechanics and one calibration,
and the derivation is in `gait()`. Nothing about it is asserted from taste.

THE CONTRACT WITH station/npc/body.py
--------------------------------------
`body.py` builds each figure as a set of separate closed lofted shells -- torso,
neck, head, two arms, two hands, two legs, two feet, plus species attachments --
in a Y-up, +Z-facing frame with the sole near y=0. It has no skeleton, so this
module defines one, and the contract is made explicit rather than assumed:

  * every joint position is taken from body.py's OWN constants (`FIGURE`, the
    `SpeciesBody` row, `_leg_params`) and put through body.py's own
    `_normalise_stature` scale and `_bend` stoop, so a change there moves the
    skeleton with it;
  * `_selftest` then MEASURES the built mesh and asserts each joint lands on the
    landmark it claims -- the hip bone on the leg part's top ring centre, the
    wrist on the arm part's bottom ring centre, and so on. If body.py changes its
    ring plan, this fails loudly instead of drifting;
  * the skin binding is computed from RING INDEX, not from vertex position, so it
    is identical for every individual of a species and is stored once per
    (species, LOD) rather than per NPC. That is asserted too.

FRAME. Y up, +Z the direction the figure faces, +X the figure's LEFT. The last
one is derived, not chosen: in a right-handed frame `right = forward x up`, and
Z x Y = -X. Godot uses -Z forward, so the export transform is a Z flip and it is
stated in `godot_note()` rather than left for someone to discover.

THE GAIT MODEL
---------------
Two mechanical facts, both dimensional analysis rather than curve fitting:

  (1) STANCE IS AN INVERTED PENDULUM. The centre of mass vaults over the stance
      foot on a leg of length L. Gravity has to supply the centripetal
      acceleration of that arc, v^2/L <= g, so the dimensionless group that
      governs walking is the Froude number

          Fr = v^2 / (g L)

      and Fr = 1 is a HARD CEILING: above it the foot leaves the ground and the
      motion is no longer a walk. `max_walk_speed()` is sqrt(g L) exactly.

  (2) SWING IS A BALLISTIC PENDULUM. The free leg swings about the hip under
      gravity, so its natural timescale is sqrt(L/g) and

          t_swing = k_sw * sqrt(L / g)

      independent of speed. This is the term that makes low gravity look floaty:
      at 0.6 g the leg hangs 29% longer for the same leg.

From those two, everything else follows algebraically (see `gait()`):

    stride       S  = A * L * Fr^B          relative stride grows with Fr
    cycle time   T  = S / v
    cadence         = 2 v / S               steps per second
    duty factor  D  = 1 - t_swing / T = 1 - (k_sw/A) * Fr^(0.5-B)
    aerial time     = max(0, 1 - 2 D) * T

Note what falls out of the algebra rather than being typed in: **duty factor is a
function of Froude number alone**, so it is gravity-independent at a
self-selected speed and gravity-dependent at a commanded one -- which is exactly
the observed behaviour and was not put in by hand.

CALIBRATION (`CAL`, authority 5, and the anchor is authority 1). The schema says
`target_g_at_habitat_floor: {value: 1.0, src: "show depicts normal gait",
auth: 1}` -- the rotation rate was SOLVED from the requirement that the drum
floor is somewhere people walk normally. So the model is calibrated at 1.0 g to
ordinary human walking and the mechanics above carry it everywhere else. The
three calibration numbers are ours (authority 5) and are declared in `CAL` with
what constrains each.

WHAT THE MODEL SAYS ABOUT THIS STATION (computed, not typed -- `report()`)
  * self-selected walking speed scales as sqrt(g): 0.87 m/s on Yellow's lightest
    habitable deck against 1.56 m/s on Grey's heaviest.
  * cadence scales as sqrt(g/L): the station's habitable gravity range alone
    spreads human cadence from 61 to 129 steps/min -- a 2.1x span, with no
    authoring at all.
  * at a COMMANDED speed the direction reverses and stride is the visible term:
    the same 1.4 m/s in Blue is taken in longer, slower strides than in Grey.
  * a walk never develops an aerial phase anywhere in the station. That is a
    derived result: D falls to 0.5 only at Fr = 0.87, and people have long since
    started running by then.

CORIOLIS -- and the honest answer is "no, except when you jump"
----------------------------------------------------------------
`station/physics/rotating_frame.py` gives a = -2 omega x v. Walking ALONG the
drum's axis is v parallel to omega, so the cross product is identically zero --
not small, zero. Walking AROUND the drum is a purely radial Coriolis term, which
adds to or subtracts from weight. At the canon 1.79 rpm and 1.4 m/s that is
5.4% of a g, and the gait model turns it into a 2.7% cadence difference between
a spinward and an antispinward walker. That is below what an eye can index in a
walk cycle, and `coriolis_report()` says so with the numbers -- including the
speed at which it stops being negligible (2.6 m/s for 10% of local weight, a run)
and the one case where it IS visible: a 0.2 m hop lands 2.0 cm spinward at the
drum floor and 5.6 cm on Blue's lighter decks.

PERFORMANCE
------------
Clips are shared and poses are rotations, so the animation dataset does not scale
with the population at all: it is ~26 kB per species for the whole set, and the
per-NPC cost is one float (phase) plus one bone palette. `cost_report()` prices
it against `schedule.NPC_BUDGET`'s 500 full agents and 2,000 crowd agents and
against the LOD chain `body.lod_chain()` already derives. The bone LOD is a
strict subset by construction and `_selftest` measures that as a set operation.

Run `python3 station/npc/animation.py` for the self-test, `--report` for the
derivation, `--obj PATH` to write a posed figure or a contact sheet for
tools/preview_render.py, `--emit DIR` to write the JSON clip set.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, field, replace

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION, os.path.join(_STATION, "physics")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import body                                                    # noqa: E402


# ---------------------------------------------------------------------------
# Determinism. blake2b, matching names.py, schedule.py and body.py byte for
# byte so one NPC id draws a name, a schedule, a body and a gait phase from the
# same stream. NEVER `random`; NEVER `str.__hash__`, which is salted per process
# and would give a crowd a different set of phases every run.
# ---------------------------------------------------------------------------
def _u(seed: str, salt: str = "") -> float:
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ---------------------------------------------------------------------------
# Small linear algebra. A transform is (R, t) with R row-major 3x3 and t a
# 3-vector; v' = R v + t. No 4x4 anywhere -- a rigid transform has no fourth row
# worth carrying, and the compose/apply pair below is the whole of it.
# ---------------------------------------------------------------------------
IDENT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
                 for i in range(3))


def _mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def _mt(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v, k):
    return (v[0] * k, v[1] * k, v[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(v):
    return math.sqrt(_dot(v, v))


def _unit(v):
    n = _norm(v)
    if n < 1e-12:
        raise ValueError("cannot normalise a zero vector")
    return _scale(v, 1.0 / n)


def _det(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def min_arc(a, b):
    """Rotation taking unit vector `a` to unit vector `b`, with no twist.

    Limb bones want exactly this: a thigh has to point from hip to knee and has
    no business acquiring a roll from the way the maths was written. Rodrigues,
    with the antiparallel case handled rather than left to divide by zero -- a
    fully extended leg swinging through the vertical passes near it.
    """
    d = max(-1.0, min(1.0, _dot(a, b)))
    if d > 1.0 - 1e-12:
        return IDENT
    if d < -1.0 + 1e-12:
        # 180 degrees: any perpendicular axis will do, so pick a stable one.
        axis = _cross(a, (1.0, 0.0, 0.0))
        if _norm(axis) < 1e-6:
            axis = _cross(a, (0.0, 0.0, 1.0))
        axis = _unit(axis)
        ang = math.pi
    else:
        axis = _unit(_cross(a, b))
        ang = math.acos(d)
    x, y, z = axis
    c, s = math.cos(ang), math.sin(ang)
    t = 1.0 - c
    return ((t * x * x + c, t * x * y - s * z, t * x * z + s * y),
            (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
            (t * x * z - s * y, t * y * z + s * x, t * z * z + c))


def mat_to_quat(m):
    """Rotation matrix -> quaternion (x, y, z, w), Godot's component order."""
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    # Sign-canonicalised so two runs cannot emit q and -q for the same rotation.
    # They are the same rotation and different bytes, which is the difference
    # between "deterministic" and "deterministic if you squint".
    if w < 0.0:
        x, y, z, w = -x, -y, -z, -w
    return (x, y, z, w)


def quat_to_mat(q):
    x, y, z, w = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


# ---------------------------------------------------------------------------
# The skeleton
# ---------------------------------------------------------------------------
# Bones are (name, parent). A bone's rest orientation is IDENTITY -- rotations
# are expressed in the figure's own axes, so "flex the hip" is a rotation about
# +X and needs no bone-local axis convention to be remembered. That choice costs
# nothing at runtime (the rest matrix is a pure translation) and removes the
# single most common source of procedural-animation sign errors.
#
# Three plans, because body.py has three: a humanoid, an encounter suit (Gaim --
# no separate hands or feet, the gauntlets and boots are the shell) and a column
# (Kosh -- no hips, no knees, no arms; `build_column` builds a robe).
#
# `_r` is the figure's RIGHT and sits at NEGATIVE x. Derived in the module
# docstring: right = forward x up = Z x Y = -X.
PLAN_BONES = {
    "humanoid": (
        ("root", None),        # ground reference; carries all translation
        ("pelvis", "root"),
        ("spine", "pelvis"),
        ("chest", "spine"),
        ("neck", "chest"),
        ("head", "neck"),
        ("shoulder_r", "chest"), ("elbow_r", "shoulder_r"), ("wrist_r", "elbow_r"),
        ("shoulder_l", "chest"), ("elbow_l", "shoulder_l"), ("wrist_l", "elbow_l"),
        ("hip_r", "pelvis"), ("knee_r", "hip_r"), ("ankle_r", "knee_r"),
        ("toe_r", "ankle_r"),
        ("hip_l", "pelvis"), ("knee_l", "hip_l"), ("ankle_l", "knee_l"),
        ("toe_l", "ankle_l"),
    ),
    "encounter_suit": (
        ("root", None), ("pelvis", "root"), ("spine", "pelvis"),
        ("chest", "spine"), ("neck", "chest"), ("head", "neck"),
        ("shoulder_r", "chest"), ("elbow_r", "shoulder_r"), ("wrist_r", "elbow_r"),
        ("shoulder_l", "chest"), ("elbow_l", "shoulder_l"), ("wrist_l", "elbow_l"),
        ("hip_r", "pelvis"), ("knee_r", "hip_r"), ("ankle_r", "knee_r"),
        ("hip_l", "pelvis"), ("knee_l", "hip_l"), ("ankle_l", "knee_l"),
    ),
    # Kosh has no gait and it would be an invention to give him one. What the
    # reference establishes (`Vorlon moree.jpg`, authority 2) is a floor-length
    # robe with no visible legs, so the column's locomotion clip is a GLIDE and
    # the module refuses to emit a walk for it -- see `walk_clip`.
    "column": (
        ("root", None), ("base", "root"), ("column", "base"),
        ("collar", "column"), ("head", "collar"),
    ),
}

# Bone tiers for the LOD cull. A coarser tier is a strict SUBSET of a finer one
# -- `_selftest` measures that as a set operation rather than trusting this
# comment, which is the mistake `station/lod.py` records having made once.
BONE_TIER = {
    "full": None,            # every bone in the plan
    # Toes stop reading first: the toe segment is ~5 cm of silhouette and it
    # only ever moves during the forefoot rocker.
    "no_toes": ("toe_r", "toe_l"),
    # Then the distal chain. A forearm at 35 m is under two pixels of swing.
    "trunk": ("toe_r", "toe_l", "wrist_r", "wrist_l", "elbow_r", "elbow_l"),
}

# Which bone each mesh part is bound to, or which chain it is skinned along.
# Chains are ordered root-first and the skinning walks their joint polyline.
PART_CHAINS = {
    "torso": ("pelvis", "spine", "chest", "neck"),
    "neck": ("neck", "head"),
    "head": ("head",),
    "hair": ("head",), "brow": ("head",),
    "centauri_crest": ("head",), "minbari_crest": ("head",),
    "pakmara_keel": ("head",), "pakmara_tendrils": ("head",),
    "abbai_fin": ("head",),
    "arm": ("shoulder_%s", "elbow_%s"),
    "hand": ("wrist_%s",),
    "leg": ("hip_%s", "knee_%s"),
    # A rigid foot, one bone. See `_stance_ankle`: body.py's three-ring foot has
    # no ring forward of the metatarsal line, so a toe bone can only be a marker.
    "foot": ("ankle_%s",),
    "suit_torso": ("pelvis", "spine", "chest", "neck"),
    "suit_arm": ("shoulder_%s", "elbow_%s"),
    "suit_leg": ("hip_%s", "knee_%s", "ankle_%s"),
    "gaim_mantle": ("chest",), "gaim_helmet": ("head",),
    "vorlon_robe": ("base", "column"),
    "vorlon_yoke": ("collar",), "vorlon_shells": ("head",),
    "vorlon_hood": ("head",), "vorlon_tubes": ("head",),
}

# EXTRAPOLATED, authority 5. Where along the hip-to-ankle line the knee sits, as
# a fraction measured from the hip. DERIVED from body.FIGURE rather than chosen:
# (hip - knee) / (hip - ankle) = (0.520 - 0.255) / (0.520 - 0.045) = 0.558, so
# the knee lands within 1% of the leg loft's own pinned middle ring at t = 0.5,
# which is the ring the bend has to happen on. body.py's own note says the
# measured `knee` is the one FIGURE entry more than 5% from standard
# anthropometry, because the trouser break sits above the joint -- so this is a
# weak number in a strong place, and what would overturn it is one frame showing
# a bare leg.
KNEE_F = ((body.FIGURE["hip"] - body.FIGURE["knee"])
          / (body.FIGURE["hip"] - body.FIGURE["ankle"]))

# The elbow, as a fraction of the shoulder-to-wrist line. body.FIGURE has no
# elbow in it -- the calibration photograph is a standing officer and the
# olecranon is inside a sleeve. 0.50 puts it on the arm loft's pinned middle
# ring, which is the same argument the knee makes and the only one available:
# a joint that is not on a ring shears the loft when it bends. Overturned by any
# reference frame giving elbow height.
ELBOW_F = 0.50

# Where the forefoot rocker pivots, as a fraction from heel to toe tip of the
# built foot part. EXTRAPOLATED: the metatarsal heads sit forward of centre, and
# a pivot at the tip would let the toe scribe below the deck. Constrained on
# both sides -- below ~0.5 the heel lifts before the foot is flat, above ~0.85
# there is no toe segment left to keep flat -- and `_selftest` asserts the
# resulting toe never penetrates the floor, which is the failure this number
# actually guards.
BALL_F = 0.72


@dataclass(frozen=True)
class Bone:
    name: str
    parent: int              # index, or -1
    head: tuple              # rest position, metres, figure frame
    tail: tuple              # rest tip; the direction the bone points


@dataclass(frozen=True)
class Skeleton:
    species: str
    npc_id: str
    plan: str
    bones: tuple             # of Bone
    index: dict              # name -> index
    ground_y: float          # the built mesh's lowest vertex: the contact plane
    stature_m: float
    leg_length_m: float      # hip joint height above `ground_y` -- the gait's L
    reach_m: float           # hip-to-ankle distance: full leg extension
    com_height_m: float      # volume-weighted centroid height above ground
    foot: dict               # measured heel/ball/tip offsets, or {} if no foot

    def head(self, name):
        return self.bones[self.index[name]].head

    def has(self, name):
        return name in self.index


# ---------------------------------------------------------------------------
# Measuring the built figure
# ---------------------------------------------------------------------------
def _ring_partition(verts, tol=1e-9):
    """Split a lofted part into its rings, by grouping runs of equal height.

    `body._loft` writes rings back to back and `body._ring` puts every vertex of
    a ring at one y, so this is exact -- BUT ONLY BEFORE THE STOOP. `_bend`
    rotates y as a function of z, so a pak'ma'ra's rings are not flat. The caller
    therefore partitions the UNSTOOPED build and applies the answer by index,
    which is valid because `_bend` maps vertices elementwise and cannot reorder
    them. Returns None if the part does not decompose into equal rings, so a part
    that stops being a loft is excluded loudly rather than mis-bound.
    """
    runs, start = [], 0
    for i in range(1, len(verts) + 1):
        if i == len(verts) or abs(verts[i][1] - verts[start][1]) > tol:
            runs.append((start, i))
            start = i
    n = runs[0][1] - runs[0][0]
    if n <= 0 or any(b - a != n for a, b in runs) or len(runs) < 2:
        return None
    return runs


def _centroid(verts, tris):
    """Volume centroid of a closed shell, by the divergence theorem.

    The mean of the vertices is not the centroid of a solid -- a head has seven
    rings and a leg has five, so a vertex mean is biased toward whatever was
    tessellated most finely. This is used for the centre-of-mass height, which
    sets the postural-sway frequency in `idle_clip`.
    """
    tv = 0.0
    acc = (0.0, 0.0, 0.0)
    for ia, ib, ic in tris:
        a, b, c = verts[ia], verts[ib], verts[ic]
        v = _dot(a, _cross(b, c)) / 6.0
        tv += v
        acc = _add(acc, _scale(_add(_add(a, b), c), v / 4.0))
    if abs(tv) < 1e-15:
        return (0.0, 0.0, 0.0), 0.0
    return _scale(acc, 1.0 / tv), tv


def _ring_centre(verts, run):
    a, b = run
    n = b - a
    return (sum(v[0] for v in verts[a:b]) / n,
            sum(v[1] for v in verts[a:b]) / n,
            sum(v[2] for v in verts[a:b]) / n)


def _parts_by_name(parts, name):
    return [(i, v, t) for i, (n, v, t) in enumerate(parts) if n == name]


def _side_of(verts):
    """'r' or 'l' from the part's own mean x. +X is the figure's LEFT."""
    return "l" if sum(v[0] for v in verts) / len(verts) > 0.0 else "r"


def _bend_points(pts, ind):
    """Put a list of points through body.py's OWN stoop transform.

    Re-implementing `_bend` here would be the drift this project keeps paying
    for: a skeleton stooped by a copy of the formula and a mesh stooped by the
    original agree until one of them is edited. So a throwaway Mesh is built and
    handed to body._bend, and the joints come back through the same code the
    vertices went through.
    """
    if abs(ind.stoop_deg) < 1e-9:
        return list(pts)
    m = body.Mesh()
    m.add(list(pts), [], "joints")
    body._bend(m, ind.stoop_deg, body.FIGURE["chest"] * ind.stature_m,
               body.BEND_TOP * ind.stature_m)
    return list(m.verts)


def _rings_by_height(parts, name, side=None):
    """(part index, [ring centres, lowest first]) for a named part.

    Rings come back sorted by height rather than in emission order, because
    `_loft` reverses a descending stack -- a leg is authored hip-first and stored
    ankle-first, and a skeleton built on emission order would put the hip joint
    in the foot on exactly the parts where it matters most.
    """
    out = []
    for i, verts, _t in _parts_by_name(parts, name):
        if side is not None and _side_of(verts) != side:
            continue
        runs = _ring_partition(verts)
        if runs is None:
            continue
        cs = sorted((_ring_centre(verts, r) for r in runs), key=lambda c: c[1])
        out.append((i, cs))
    return out


def _skeleton(ind, sp, parts, unstooped):
    """Joint positions, measured off the built figure wherever a landmark exists.

    The rule is: MEASURE the joint if the mesh has a ring there, DERIVE it from
    body.FIGURE if it does not, and never type a number. The uniform scale
    body.py applies in `_normalise_stature` is recovered from one measured
    landmark rather than recomputed, so a change to how stature is normalised
    cannot silently detach the skeleton from the mesh.
    """
    H = ind.stature_m
    F = body.FIGURE
    plan = sp.plan
    ground = min(v[1] for _n, vs, _t in parts for v in vs)
    tails = {}
    j = {}

    if plan in ("humanoid", "encounter_suit"):
        leg_part = "leg" if plan == "humanoid" else "suit_leg"
        arm_part = "arm" if plan == "humanoid" else "suit_arm"
        raw_hip = (body._leg_params(ind, sp)[0] if plan == "humanoid"
                   else F["hip"] - 0.02)
        legs = {s: _rings_by_height(unstooped, leg_part, s)[0][1] for s in "rl"}
        k = legs["r"][-1][1] / (raw_hip * H)          # the normalisation scale
        arms = {s: _rings_by_height(unstooped, arm_part, s)[0][1] for s in "rl"}

        j["root"] = (0.0, ground, 0.0)
        j["pelvis"] = (0.0, legs["r"][-1][1], 0.0)
        j["spine"] = (0.0, F["waist"] * H * k, 0.0)
        j["chest"] = (0.0, F["chest"] * H * k, 0.0)
        j["neck"] = (0.0, F["acromion"] * H * k, 0.0)
        if plan == "humanoid":
            neck_len = (F["chin"] - F["acromion"]) * H * sp.neck_k
            j["head"] = (0.0, (F["acromion"] * H + neck_len) * k, 0.0)
            crown = _rings_by_height(unstooped, "head")[0][1][-1]
        else:
            j["head"] = (0.0, (F["acromion"] + 0.028) * H * k, 0.0)
            crown = _rings_by_height(unstooped, "gaim_helmet")[0][1][-1]
        tails["head"] = crown

        for s in "rl":
            hip, ank = legs[s][-1], legs[s][0]
            j["hip_%s" % s] = hip
            j["knee_%s" % s] = _add(hip, _scale(_sub(ank, hip), KNEE_F))
            j["ankle_%s" % s] = ank
            sh, wr = arms[s][-1], arms[s][0]
            j["shoulder_%s" % s] = sh
            j["elbow_%s" % s] = _add(sh, _scale(_sub(wr, sh), ELBOW_F))
            j["wrist_%s" % s] = wr
            hand = _rings_by_height(unstooped, "hand", s)
            tails["wrist_%s" % s] = (hand[0][1][0] if hand else
                                     _add(wr, _scale(_sub(wr, sh), 0.18)))

        foot = {}
        if plan == "humanoid" and _parts_by_name(unstooped, "foot"):
            for s in "rl":
                fv = next(v for _i, v, _t in _parts_by_name(unstooped, "foot")
                          if _side_of(v) == s)
                y0 = min(v[1] for v in fv)
                y1 = max(v[1] for v in fv)
                sole = [v for v in fv if v[1] <= y0 + 0.25 * (y1 - y0)]
                heel_z, tip_z = min(v[2] for v in sole), max(v[2] for v in sole)
                x = sum(v[0] for v in fv) / len(fv)
                ball_z = heel_z + BALL_F * (tip_z - heel_z)
                j["toe_%s" % s] = (x, y0, ball_z)
                tails["toe_%s" % s] = (x, y0, tip_z)
                if s == "r":
                    foot = {"heel_z": heel_z, "ball_z": ball_z, "tip_z": tip_z,
                            "sole_y": y0,
                            "ankle_to_heel": heel_z - j["ankle_r"][2],
                            "ankle_to_ball": ball_z - j["ankle_r"][2],
                            "ankle_rise": j["ankle_r"][1] - y0}
        else:
            # No foot mesh: either the Gaim suit (boots are the shell) or a LOD
            # past the extremity cull, which body.py's feature schedule puts at
            # 81 m. The toe bones stay in the plan so one clip fits every level --
            # a bone set that changes with distance would need a clip per
            # level -- but they are markers 6 cm ahead of the ankle and carry no
            # weight. The gait goes flat-footed; see `_foot_frame`.
            for s in "rl":
                ank = j["ankle_%s" % s]
                tails["ankle_%s" % s] = _add(ank, (0.0, ground - ank[1],
                                                   0.06 * H))
                if "toe_%s" % s in [n for n, _p in PLAN_BONES[plan]]:
                    j["toe_%s" % s] = (ank[0], ground, ank[2] + 0.045 * H)
                    tails["toe_%s" % s] = (ank[0], ground, ank[2] + 0.075 * H)
    else:                                              # column: Kosh
        robe = _rings_by_height(unstooped, "vorlon_robe")[0][1]
        yoke = _rings_by_height(unstooped, "vorlon_yoke")[0][1]
        k = robe[-1][1] / (0.735 * H)
        j["root"] = (0.0, ground, 0.0)
        j["base"] = (0.0, robe[0][1], 0.0)
        j["column"] = (0.0, robe[len(robe) // 2][1], 0.0)
        j["collar"] = (0.0, robe[-1][1], 0.0)
        j["head"] = (0.0, yoke[-1][1], 0.0)
        tails["head"] = (0.0, max(v[1] for _n, vs, _t in unstooped for v in vs),
                         0.0)
        foot = {}

    # The stoop is applied to the joints by body.py's own transform, AFTER the
    # scale, in the same order build_humanoid applies it to the vertices.
    names = [n for n, _p in PLAN_BONES[plan]]
    pts = _bend_points([j[n] for n in names] + [tails[n] for n in sorted(tails)],
                       ind)
    j = dict(zip(names, pts[:len(names)]))
    tails = dict(zip(sorted(tails), pts[len(names):]))

    index = {n: i for i, (n, _p) in enumerate(PLAN_BONES[plan])}
    kids = {}
    for n, p in PLAN_BONES[plan]:
        if p is not None:
            kids.setdefault(p, []).append(n)
    bones = tuple(Bone(n, index[p] if p else -1, j[n],
                       tails[n] if n in tails else j[kids[n][0]])
                  for n, p in PLAN_BONES[plan])

    com, _v = _com_of(parts)
    hip_y = j["hip_r"][1] if "hip_r" in j else j["collar"][1]
    reach = (_norm(_sub(j["hip_r"], j["ankle_r"])) if "hip_r" in j
             else hip_y - ground)
    return Skeleton(ind.species, ind.npc_id, plan, bones, index, ground,
                    ind.stature_m, hip_y - ground, reach, com[1] - ground, foot)


def _com_of(parts):
    """Volume-weighted centre of mass over every part, uniform density.

    The density assumption is EXTRAPOLATED and it is the honest one available:
    nothing in the reference says what a Narn weighs. What it is used for is the
    postural-sway frequency, which goes as sqrt(g/h_com) -- a 10% error in h_com
    moves the sway period by 5%, which is why an approximation is acceptable
    here and would not be for the gait's leg length.
    """
    tot = 0.0
    acc = (0.0, 0.0, 0.0)
    for _n, verts, tris in parts:
        c, v = _centroid(verts, tris)
        acc = _add(acc, _scale(c, v))
        tot += v
    return _scale(acc, 1.0 / tot), tot


# ---------------------------------------------------------------------------
# Skinning
# ---------------------------------------------------------------------------
# Weights are a function of (part, RING INDEX) and nothing else. That is the
# whole cost argument for a crowd: the ring plan is identical for every
# individual of a species -- `individual()` varies stature, girth and cranium,
# never the topology -- so one binding is stored per (species, LOD) and shared by
# 155,000 humans rather than baked per NPC. `_selftest` asserts the invariance by
# binding two different residents and diffing the tables.
MAX_INFLUENCES = 4          # the standard GPU skinning limit; asserted, not hoped
BAND_MAX_FRAC = 0.45        # blend half-width, as a fraction of the shorter
#                             adjacent bone; above 0.5 two bands overlap and a
#                             vertex acquires influences from bones two joints
#                             away, which is how an elbow ends up dragging a
#                             shoulder.


def _project_param(p, poly, cum):
    """Arc-length parameter of the closest point on a polyline."""
    best, bs = None, 0.0
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        ab = _sub(b, a)
        ll = _dot(ab, ab)
        t = 0.0 if ll < 1e-15 else max(0.0, min(1.0, _dot(_sub(p, a), ab) / ll))
        q = _add(a, _scale(ab, t))
        d = _norm(_sub(p, q))
        if best is None or d < best:
            best, bs = d, cum[i] + t * math.sqrt(ll)
    return bs


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# Chains whose LAST joint is a rigid attachment rather than a crease. A knee and
# an elbow crease; a boot does not bend where it meets the shin. body.py's Gaim
# suit has no separate boot part, so the last ring of `suit_leg` IS the sole, and
# blending it half onto the shin makes the sole rotate with the leg -- measured at
# 180 mm of foot slide and 74 mm of deck penetration per cycle before this
# existed. Naming the joint rigid puts the sole entirely on the ankle bone, which
# `walk_clip` then holds level.
RIGID_TAIL = frozenset({"suit_leg"})


def _chain_weights(ring_params, ring_radii, cum, rigid_tail=False):
    """Per-ring bone weights along a chain, from the arc-length parameter."""
    n = len(cum) - 1                       # bones in the chain
    if n <= 1:
        return [((0, 1.0),) for _ in ring_params]
    bands = []
    for jdx in range(1, n):
        seg_a = cum[jdx] - cum[jdx - 1]
        seg_b = cum[jdx + 1] - cum[jdx]
        # The band is the limb's own radius at the joint, clamped so it can never
        # reach the next joint. Derived from the geometry, not chosen: a fat
        # thigh blends over more length than a thin forearm, which is what makes
        # a knee crease rather than a knuckle.
        near = min(range(len(ring_params)),
                   key=lambda i: abs(ring_params[i] - cum[jdx]))
        bands.append(min(ring_radii[near], BAND_MAX_FRAC * min(seg_a, seg_b)))
    out = []
    for s in ring_params:
        i = 0
        while i < n - 1 and s > cum[i + 1]:
            i += 1
        w = [0.0] * n
        w[i] = 1.0
        if rigid_tail and s >= cum[n - 1] - 1e-12:
            out.append(((n - 1, 1.0),))
            continue
        for jdx in (i, i + 1):
            if 1 <= jdx <= n - 1:
                if rigid_tail and jdx == n - 1:
                    continue
                h = bands[jdx - 1]
                if h > 1e-9 and abs(s - cum[jdx]) < h:
                    t = _smoothstep(0.5 + 0.5 * (s - cum[jdx]) / h)
                    w = [0.0] * n
                    w[jdx - 1], w[jdx] = 1.0 - t, t
                    break
        pairs = sorted([(k, v) for k, v in enumerate(w) if v > 1e-6],
                       key=lambda kv: -kv[1])[:MAX_INFLUENCES]
        tot = sum(v for _k, v in pairs)
        out.append(tuple((k, v / tot) for k, v in pairs))
    return out


def _bind(skel, parts, unstooped):
    """[(part index, [(bone index, weight), ...] per RING, [ring run, ...])]."""
    table = []
    for pi, (name, verts, _t) in enumerate(parts):
        chain = PART_CHAINS.get(name)
        if chain is None:
            raise KeyError(f"no bone chain declared for mesh part {name!r}; "
                           f"body.py has grown a part this module cannot skin")
        rigid = name in RIGID_TAIL
        if name == "leg" and not _parts_by_name(parts, "foot"):
            # Past the extremity cull the shin's last ring IS the sole. Same
            # treatment as the suit, for the same measured reason.
            chain, rigid = ("hip_%s", "knee_%s", "ankle_%s"), True
        side = _side_of(verts) if "%s" in chain[0] else None
        names = [c % side if "%s" in c else c for c in chain]
        names = [n for n in names if skel.has(n)]
        poly = [skel.head(n) for n in names] + [skel.bones[skel.index[names[-1]]].tail]
        cum = [0.0]
        for i in range(len(poly) - 1):
            cum.append(cum[-1] + _norm(_sub(poly[i + 1], poly[i])))
        runs = _ring_partition(unstooped[pi][1])
        if runs is None:
            raise ValueError(f"part {name!r} is not a ring loft; cannot bind")
        params, radii = [], []
        for r in runs:
            c = _ring_centre(unstooped[pi][1], r)
            params.append(_project_param(c, poly, cum))
            radii.append(sum(_norm(_sub(v, c)) for v in unstooped[pi][1][r[0]:r[1]])
                         / (r[1] - r[0]))
        w = _chain_weights(params, radii, cum, rigid)
        gi = [skel.index[n] for n in names]
        table.append((pi, [tuple((gi[b], v) for b, v in ring) for ring in w], runs))
    return table


# ---------------------------------------------------------------------------
# The rig: a figure, its skeleton and its binding, resolved together
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Rig:
    species: str
    npc_id: str
    lod: int
    ind: object
    sp: object
    skel: Skeleton
    parts: tuple             # (name, verts, tris) as body.py emitted them
    groups: tuple            # OBJ material group per part, for the renderer
    binding: tuple


_RIG_CACHE = {}
# The un-jittered member of a species -- body.nominal(). Used for the gait
# calibration and for the shared skin binding, so neither depends on which
# resident happened to be built first.
NOMINAL = "__nominal__"


def rig(species: str, npc_id: str, lod: int = 0) -> Rig:
    """Build one resident and rig it. Pure in (species, npc_id, lod)."""
    key = (species, npc_id, lod)
    if key in _RIG_CACHE:
        return _RIG_CACHE[key]
    chain = body.lod_chain()
    lv = chain[max(0, min(lod, len(chain) - 1))]
    if lv["kind"] == "impostor":
        raise ValueError(
            "an impostor card has no skeleton: body.lod_chain() already records "
            "that a card freezes the gait, and pretending to animate one would "
            "be an assertion that cannot fail")
    ind = (body.nominal(species) if npc_id == NOMINAL
           else body.individual(species, npc_id))
    sp = body.SPECIES[species]
    kw = dict(seg=lv["radial_segments"], ring_stride=lv["ring_stride"],
              features=lv["features"])
    m = body._PLANS[sp.plan](ind, sp, **kw)
    # The same figure with the stoop suppressed. `_ring_partition` needs flat
    # rings and `_bend` destroys them; the two builds differ by exactly that
    # transform, so vertex ORDER is identical and the partition transfers.
    m0 = body._PLANS[sp.plan](replace(ind, stoop_deg=0.0), sp, **kw)
    parts = tuple((n, tuple(v), tuple(t)) for n, v, t in m.parts)
    parts0 = tuple((n, tuple(v), tuple(t)) for n, v, t in m0.parts)
    groups = tuple(g for g, _lo, _hi in m.spans)
    skel = _skeleton(ind, sp, parts0, parts0)
    out = Rig(species, npc_id, lod, ind, sp, skel, parts, groups,
              tuple(_bind(skel, parts, parts0)))
    _RIG_CACHE[key] = out
    return out


# ---------------------------------------------------------------------------
# Forward kinematics and skinning
# ---------------------------------------------------------------------------
def rest_offsets(skel):
    """Each bone's rest translation from its parent. Rest rotations are identity,
    so a bone's rest world transform is a pure translation to its head and the
    skinning matrix in the rest pose is exactly the identity -- which
    `_selftest` checks by reproducing the bind mesh vertex for vertex."""
    return tuple(b.head if b.parent < 0
                 else _sub(b.head, skel.bones[b.parent].head)
                 for b in skel.bones)


def fk(skel, locals_, root_t=(0.0, 0.0, 0.0)):
    """World (R, t) per bone. `locals_` is bone index -> local rotation matrix."""
    off = rest_offsets(skel)
    world = []
    for i, b in enumerate(skel.bones):
        r = locals_.get(i, IDENT)
        if b.parent < 0:
            world.append((r, _add(off[i], root_t)))
        else:
            pr, pt = world[b.parent]
            world.append((_mul(pr, r), _add(pt, _mv(pr, off[i]))))
    return world


def skin_matrices(skel, world):
    return tuple((R, _sub(t, _mv(R, skel.bones[i].head)))
                 for i, (R, t) in enumerate(world))


def apply_pose(rg: Rig, mats):
    """Skin the figure. Returns parts in body.py's own (name, verts, tris) shape."""
    out = []
    for pi, ringw, runs in rg.binding:
        name, verts, tris = rg.parts[pi]
        nv = list(verts)
        for r, (a, b) in enumerate(runs):
            w = ringw[r]
            for vi in range(a, b):
                v = verts[vi]
                acc = (0.0, 0.0, 0.0)
                for bi, wt in w:
                    R, t = mats[bi]
                    acc = _add(acc, _scale(_add(_mv(R, v), t), wt))
                nv[vi] = acc
        out.append((name, nv, tris))
    return out


# ---------------------------------------------------------------------------
# Gait, as physics
# ---------------------------------------------------------------------------
G0 = 9.80665                     # CODATA, and the schema's own standard_gravity

# THE CALIBRATION. Three numbers, all EXTRAPOLATED (authority 5), anchored to one
# authority-1 fact: station/schema/station.yaml sets
# `target_g_at_habitat_floor: {value: 1.0, src: "show depicts normal gait"}` --
# the station's rotation rate was SOLVED backwards from the requirement that the
# drum floor is somewhere a person walks normally. So "normal human walking at
# 1.0 g" is the one gait this project may assume, and everything else is carried
# there by the mechanics in `gait()`.
#
# What constrains each, and what would overturn it:
#   preferred_speed_m_s  1.40 -- has to put Fr well inside the walking regime
#       (it gives 0.21) and has to agree with the figure `station/npc/crowd.py`
#       independently uses for the player's walk speed when it sizes the
#       streaming hysteresis ("~1.4 m/s"). Overturned by a shot with a known
#       distance and a known frame count.
#   stride_m 1.45 -- fixes cadence at 2v/S = 116 steps/min, inside the ordinary
#       human band, and must stay under the geometric limit 2*reach (1.79 m for
#       this figure) or the leg cannot reach the ground at contact. `_selftest`
#       asserts the margin over every species and every deck.
#   duty_factor 0.62 -- fraction of the cycle each foot is down. Must exceed 0.5
#       or a walk has an aerial phase, which is the definition of a run.
CAL = {"preferred_speed_m_s": 1.40, "stride_m": 1.45, "duty_factor": 0.62}

# Relative stride length goes as Fr^LAMBDA_EXP. EXTRAPOLATED, authority 5: the
# exponent is the only free shape in the model and it is what decides how much
# LONGER a stride gets in low gravity at a commanded speed. Constrained at both
# ends -- 0 makes stride independent of speed (visibly wrong: people lengthen
# their stride when they hurry) and 0.5 makes cadence independent of speed
# (equally wrong: they also step faster). 0.30 splits it so that both cadence and
# stride carry part of a speed change, which is what walking does. Overturned by
# any measurement of stride against speed.
LAMBDA_EXP = 0.30

# Froude number at which people stop walking and start running. EXTRAPOLATED,
# authority 5, and it is a PREFERENCE not a limit: the mechanical ceiling below
# is 1.0 and is derived. 0.5 is placed between the model's own preferred Fr
# (0.21) and that ceiling. Its only job here is to bound the walk clip ladder.
FR_RUN = 0.50

# Below this gravity the model refuses to emit a walk. At 0.3 g the preferred
# speed is 0.77 m/s and the cadence 63 steps/min; below it the numbers leave any
# human band and the real gait becomes a lope or a bound, which is a different
# clip and is NOT built here. Yellow's innermost habitable ring is 0.12 g and is
# inside this hole -- see `station_gravity()`. EXTRAPOLATED; what would overturn
# it is footage of anyone moving in low gravity aboard.
WALK_G_MIN = 0.30

# The stance leg is never locked straight: the hip is held this fraction of full
# extension above the foot. EXTRAPOLATED and small, but load-bearing -- at 1.0
# the IK hits its singularity at mid-stance and the knee snaps, and this is what
# makes the pelvis bob DERIVED rather than authored (see `walk_clip`).
K_EXT = 0.985


def _nominal_leg():
    """Reference leg length: body.nominal('human'), measured, not typed."""
    return rig("human", NOMINAL, 0).skel.leg_length_m


_CAL_CACHE = {}


def calibration():
    """The three derived constants of the gait model, solved from `CAL`."""
    if _CAL_CACHE:
        return _CAL_CACHE
    L = _nominal_leg()
    v, S, D = (CAL["preferred_speed_m_s"], CAL["stride_m"], CAL["duty_factor"])
    fr = v * v / (G0 * L)
    lam = S / L
    T = S / v
    _CAL_CACHE.update({
        "leg_length_m": L,
        "froude_preferred": fr,
        "lambda_preferred": lam,
        # S = A L Fr^B, solved at the calibration point
        "lambda_coeff": lam / fr ** LAMBDA_EXP,
        "cycle_s": T,
        "swing_s": (1.0 - D) * T,
        # t_swing = k_sw sqrt(L/g): the ballistic pendulum constant
        "k_swing": (1.0 - D) * T / math.sqrt(L / G0),
        "cadence_spm": 120.0 * v / S,
    })
    return _CAL_CACHE


def froude(v, g, L):
    return v * v / (g * L)


def max_walk_speed(g, L):
    """v = sqrt(gL). EXACT, and the one hard number in the model.

    In single support the centre of mass follows a circular arc of radius L over
    the stance foot, so gravity has to supply v^2/L of centripetal acceleration.
    When v^2/L exceeds g the ground can no longer pull the body down onto the
    arc, the foot leaves the floor, and whatever is happening is not a walk. This
    is Fr = 1 and it is derived, not calibrated.
    """
    return math.sqrt(g * L)


def preferred_speed(g, L):
    """Self-selected walking speed: sqrt(Fr* g L), so it goes as sqrt(g)."""
    return math.sqrt(calibration()["froude_preferred"] * g * L)


def gait(g, L, v=None, allow_run=False):
    """The whole gait, from Fr. Everything below is algebra on two mechanics.

    `g` in m/s^2, `L` the leg length in metres, `v` the commanded speed or None
    for self-selected. Returns a dict; every entry is derived and the derivation
    is one line of comment beside it.
    """
    c = calibration()
    selected = v is None
    if selected:
        v = preferred_speed(g, L)
    fr = froude(v, g, L)
    lam = c["lambda_coeff"] * fr ** LAMBDA_EXP     # relative stride S/L
    stride = lam * L
    cycle = stride / v                             # one full two-step cycle
    swing = c["k_swing"] * math.sqrt(L / g)        # ballistic, speed-independent
    duty = 1.0 - swing / cycle                     # = 1 - (k/A) Fr^(0.5-B)
    aerial = max(0.0, 1.0 - 2.0 * duty) * cycle    # zero unless duty < 0.5
    kind = "run" if fr > FR_RUN else "walk"
    if kind == "run" and not allow_run:
        raise ValueError(
            f"Fr = {fr:.3f} is past the walk/run transition ({FR_RUN}); "
            f"v = {v:.2f} m/s at g = {g / G0:.3f} g needs the run clip")
    return {
        "g_ms2": g, "g": g / G0, "leg_m": L, "speed_ms": v, "froude": fr,
        "relative_stride": lam, "stride_m": stride, "step_m": stride / 2.0,
        "cycle_s": cycle, "cadence_spm": 120.0 / cycle, "duty": duty,
        "swing_s": swing, "stance_s": duty * cycle,
        "double_support": max(0.0, 2.0 * duty - 1.0),
        "aerial_s": aerial, "kind": kind, "self_selected": selected,
        "max_walk_speed_ms": max_walk_speed(g, L),
        "below_walk_gravity": g / G0 < WALK_G_MIN,
    }


def duty_at_froude(fr):
    """D(Fr) = 1 - (k_sw / A) Fr^(0.5 - B), a function of Froude number ALONE.

    This is the model's most interesting consequence and nothing put it there by
    hand: the leg length and the gravity both cancel. So at a self-selected speed
    the duty factor -- and therefore the SHAPE of the walk -- is the same on every
    deck of the station, and only the rate and the stride change. That is why one
    Froude ladder of clips covers all 217 habitable decks.
    """
    c = calibration()
    return 1.0 - (c["k_swing"] / c["lambda_coeff"]) * fr ** (0.5 - LAMBDA_EXP)


def froude_at_duty(d):
    """Inverse of the above; used to state where a walk would lose double
    support, which is the honest way to say that it never does here."""
    c = calibration()
    return ((1.0 - d) * c["lambda_coeff"] / c["k_swing"]) ** (
        1.0 / (0.5 - LAMBDA_EXP))


# ---------------------------------------------------------------------------
# Where the gravity comes from: the station itself
# ---------------------------------------------------------------------------
_STATION_CACHE = {}


def station_gravity():
    """Every deck's gravity, from station/interior.py. Nothing typed here.

    NOTE FOR ANYONE HOLDING OLDER FIGURES. STATE.md and the gazetteers quote
    "0.602 g in Blue to 1.445 g in Grey". Those predate the metric HULL_ALLOWANCE
    (commit 753f352, "Make the hull allowance metric, and give the station a
    basement"), which moved every sector's outermost deck outward: the live model
    now gives Blue 0.760 g and Grey 1.693 g, and INVENTIONS.md's INV-027 records
    the same move. This function reads the model rather than the prose, so the
    gait tracks the geometry rather than a remembered number.
    """
    if _STATION_CACHE:
        return _STATION_CACHE
    import interior                                          # noqa: PLC0415
    from rotating_frame import from_schema                   # noqa: PLC0415
    schema, profile = interior.load()
    drum = from_schema(schema)
    decks = []
    for name in schema["sectors"]["extents_m"]:
        try:
            rings = interior.ring_radii(schema, profile, name)
        except (ValueError, KeyError):
            continue
        for i, _r in enumerate(rings):
            for d in interior.decks_in_ring(schema, profile, name, i):
                decks.append({"sector": name, "ring": i,
                              "deck": d["deck_index"], "r_m": d["floor_r_m"],
                              "g": d["floor_g"], "use": d["use"]})
    hab = [d for d in decks if d["use"] == "habitat"]
    walkable = [d for d in decks if d["g"] >= WALK_G_MIN]
    _STATION_CACHE.update({
        "omega": drum.omega, "rpm": drum.rpm,
        "floor_radius_m": drum.floor_radius, "floor_speed_ms": drum.floor_speed,
        "decks": decks, "n_decks": len(decks),
        "habitat_g": (min(d["g"] for d in hab), max(d["g"] for d in hab)),
        "plant_g": (min(d["g"] for d in decks if d["use"] == "plant"),
                    max(d["g"] for d in decks if d["use"] == "plant")),
        "walkable_g": (min(d["g"] for d in walkable),
                       max(d["g"] for d in walkable)),
        "below_walk_min": sorted({d["sector"] for d in decks
                                  if d["g"] < WALK_G_MIN}),
        "drum": drum,
    })
    return _STATION_CACHE


def floor_curvature_error(radius_m, stride_m):
    """How far a flat-authored stride mis-plants the foot on a curved deck.

    Every deck in this station is a ring, so a stride is a CHORD and the floor
    falls away from it by the sagitta r(1 - cos(theta/2)) with theta = S/r. Nobody
    else in the project has had to care, because nothing else is 1.5 m long and
    in contact with the floor at two points. The number decides one thing: whether
    a walk clip may be applied in a single flat frame for a whole stride, or has
    to be re-anchored at each footfall.
    """
    th = stride_m / radius_m
    return radius_m * (1.0 - math.cos(th / 2.0))


def coriolis_report(v_walk=None, hop_height_m=0.20):
    """Is Coriolis visible in a walk at 1.79 rpm? With the numbers.

    `rotating_frame.coriolis` is a = -2 omega x v about +Z, so:

      * ALONG THE AXIS  v is parallel to omega and the cross product is
        IDENTICALLY zero. Not small -- zero. A corridor running fore-and-aft is a
        corridor.
      * AROUND THE DRUM  v is tangential and the acceleration is purely radial:
        it adds to weight going spinward and subtracts going antispinward. That
        is the same 2 v / (omega r) that `apparent_weight_factor` carries as its
        linear term, and this function checks the two against each other rather
        than trusting either.
      * TOWARD THE AXIS  a vertical component of velocity throws you sideways.
        The walk's own bob does this, and the answer is a fraction of a
        millimetre.
    """
    st = station_gravity()
    drum, w = st["drum"], st["omega"]
    r = st["floor_radius_m"]
    g_floor = drum.gravity_at(r)
    L = calibration()["leg_length_m"]
    v = v_walk if v_walk is not None else preferred_speed(g_floor, L)

    axial = drum.coriolis((0.0, 0.0, v))               # along +Z, the spin axis
    tang = drum.coriolis((0.0, v, 0.0))                # spinward at (r, 0, 0)
    frac = _norm(tang) / g_floor
    exact = drum.apparent_weight_factor(r, v)          # (1 + v/wr)^2
    spin = gait(g_floor * exact, L, v)
    anti = gait(g_floor * drum.apparent_weight_factor(r, -v), L, v)

    # The bob. Amplitude comes from the gait's own geometry: the hip rises by
    # reach*(1 - cos(theta)) between contact and mid-stance, and it happens twice
    # per cycle.
    gt = gait(g_floor, L, v)
    th = math.asin(min(1.0, gt["duty"] * gt["stride_m"] / (2.0 * L)))
    bob = L * (1.0 - math.cos(th))
    f_bob = 2.0 / gt["cycle_s"]
    v_bob = 2.0 * math.pi * f_bob * (bob / 2.0)
    a_bob = 2.0 * w * v_bob
    sway = a_bob / (2.0 * math.pi * f_bob) ** 2

    # A hop, which is where it IS visible. Ballistic in the rotating frame:
    # a_tan = -2 w v_r with v_r = -v0 + g t, integrated twice over t_f = 2 v0/g
    # gives a spinward displacement of (4/3) w v0^3 / g^2 -- and a lateral
    # velocity that returns to exactly zero at touchdown, so the jumper lands
    # displaced but not drifting.
    def hop(g, v0=None):
        v0 = math.sqrt(2.0 * g * hop_height_m) if v0 is None else v0
        return {"g": g / G0, "launch_ms": v0, "flight_s": 2.0 * v0 / g,
                "height_m": v0 * v0 / (2.0 * g),
                "spinward_m": (4.0 / 3.0) * w * v0 ** 3 / (g * g)}

    st_g = station_gravity()
    g_light = max(WALK_G_MIN, st_g["walkable_g"][0]) * G0
    v_effort = math.sqrt(2.0 * g_floor * hop_height_m)
    return {
        "rpm": st["rpm"], "omega": w, "floor_speed_ms": st["floor_speed_ms"],
        "walk_speed_ms": v,
        "axial_coriolis_ms2": axial,
        "axial_is_exactly_zero": axial == (0.0, 0.0, 0.0),
        "tangential_coriolis_ms2": _norm(tang),
        "tangential_fraction_of_g": frac,
        "weight_factor_spinward": exact,
        "linear_term_agrees": abs((exact - 1.0) - 2.0 * v / (w * r)) < 2e-3,
        "cadence_spinward_spm": spin["cadence_spm"],
        "cadence_antispinward_spm": anti["cadence_spm"],
        "cadence_split_pct": 100.0 * (spin["cadence_spm"] / anti["cadence_spm"] - 1),
        "stride_split_pct": 100.0 * (spin["stride_m"] / anti["stride_m"] - 1),
        "speed_for_1pct_g": 0.01 * g_floor / (2.0 * w),
        "speed_for_10pct_g": 0.10 * g_floor / (2.0 * w),
        "speed_for_full_g": g_floor / (2.0 * w),
        # Upper bound: the stiff-legged pendulum rise. The clip's actual bob is
        # smaller, because K_EXT keeps the knee bent -- `walk_clip` measures it.
        "bob_amplitude_pendulum_m": bob, "bob_lateral_accel_ms2": a_bob,
        "bob_lateral_sway_m": sway,
        "hop_drum": hop(g_floor), "hop_light_deck": hop(g_light),
        # Same muscular effort, not the same height: this is the comparison a
        # player makes, and it is the one that shows. v0^3/g^2 is a savage
        # scaling -- a third of a g multiplies the sideways landing error by 11.
        "hop_light_deck_same_effort": hop(g_light, v_effort),
        "verdict": ("not visible in a walk cycle; visible in a jump"
                    if frac < 0.10 else "visible in a walk cycle"),
    }


# ---------------------------------------------------------------------------
# Clips
# ---------------------------------------------------------------------------
# Amplitudes a human animator would key. All EXTRAPOLATED (authority 5) and all
# constrained by something measurable rather than by taste -- the constraint is
# written beside each, and `_selftest` checks the ones that are checkable
# (foot slide, floor penetration, hand/thigh interpenetration, leg extension).
POSE = {
    # Rocker phases, as fractions of stance. Heel rocker, then foot flat, then
    # forefoot rocker. Constrained: A + C must leave a flat phase, or the foot
    # pivots continuously and never plants.
    "heel_rocker": 0.18, "flat_end": 0.72,
    "heel_strike_deg": 8.0,     # toe up at contact; larger and the toe scribes
    "toe_off_deg": 22.0,        # heel up at release; the forefoot rocker's end
    "swing_lift_f": 0.055,      # foot clearance, x leg length. > 0 asserted
    "pelvis_yaw_deg": 4.0,      # transverse rotation, lengthens stride for free
    "pelvis_roll_deg": 3.0,     # the swing side drops (a normal Trendelenburg)
    "chest_counter": 0.65,      # thorax counter-rotation, x pelvis yaw
    "lean_deg_per_froude": 22.0,  # trunk lean grows with speed, not with g
    "arm_swing_deg": 20.0,      # contra-lateral; bounded by the hand/thigh check
    # Arms hang slightly clear of the body. NOT a taste parameter -- it is SOLVED
    # against `hand_clearance()`: body.py's rest arm is vertical and its hand
    # already sits 22% inside the thigh at rest, and swinging it made that 49%.
    # This is the smallest whole degree that puts the walk back at or under the
    # bind pose's own interpenetration. If body.py moves the wrist, re-solve it.
    "arm_abduct_deg": 7.0,
    "elbow_base_deg": 12.0, "elbow_swing_deg": 18.0,
    "sway_f": 0.55,             # lateral CoM travel, x the leg's own x offset
    "head_residual": 0.25,      # how much of the trunk's yaw the head keeps
    "nod_deg": 1.6,
    # How much of the stiff-legged pendulum rise survives. The vault gives the
    # hip a 12 cm rise between contact and mid-stance on this figure; stance-phase
    # knee flexion absorbs most of it. Constrained hard on both sides and both
    # ends are visibly wrong: 1.0 is a pogo stick, 0.0 is the "Groucho walk" of a
    # pelvis on rails. `walk_clip` reports the surviving bob so the number is
    # checkable rather than atmospheric.
    "knee_flex_keep": 0.35,
}


@dataclass(frozen=True)
class Clip:
    name: str
    species: str
    npc_id: str
    plan: str
    duration_s: float
    frames: int
    loop: bool
    root: tuple              # per-frame root translation
    tracks: dict             # bone name -> per-frame (x, y, z, w)
    meta: dict = field(default_factory=dict)

    def locals_at(self, skel, f):
        out = {}
        for name, qs in self.tracks.items():
            out[skel.index[name]] = quat_to_mat(qs[f % self.frames])
        return out

    def pose(self, skel, f):
        w = fk(skel, self.locals_at(skel, f), self.root[f % self.frames])
        return w, skin_matrices(skel, w)


def _style(sp, ind):
    """Per-species amplitude multipliers, DERIVED from the body row.

    A Drazi does not need a hand-keyed walk: it is 1.26 build on 1.12 shoulders
    with a 0.55 neck, and those three numbers already say "swings less, rolls
    more, head does not move". Deriving the style from the same table that made
    the mesh is what stops fifteen species needing fifteen animators.
    """
    b = ind.build
    return {
        "arm": max(0.45, 1.0 - 0.55 * (b - 1.0)),      # heavy build, less swing
        "roll": min(1.6, 1.0 + 0.45 * (b - 1.0)),      # and more lateral roll
        "yaw": max(0.5, 1.0 / max(ind.shoulder_k, 0.5)),
        "head": min(1.0, max(0.15, sp.neck_k)),        # no neck, no head motion
    }


def _foot_frame(sk, side, ground):
    """Rest geometry of one foot, in the ankle's own frame."""
    ank = sk.head("ankle_%s" % side)
    if sk.foot:
        return {"x": ank[0], "rise": ank[1] - ground,
                "heel": sk.foot["ankle_to_heel"],
                "tip": sk.foot["tip_z"] - sk.head("ankle_r")[2], "rolls": True}
    return {"x": ank[0], "rise": ank[1] - ground, "heel": 0.0,
            "tip": 0.0, "rolls": False}


def _stance_ankle(ff, ground, plant_z, q, duty, p1, p2, th_hs, th_to):
    """Ankle position and foot pitch during stance, from the rocker in progress.

    The contact point is what is held fixed, not the ankle: the heel is the pivot
    while the foot lowers, the whole sole is down through mid-stance, and the TOE
    TIP is the pivot while the heel lifts. The ankle therefore moves during
    stance -- which is correct, and is the difference between a walk and a figure
    sliding along on stilts.

    THE FOOT IS RIGID, AND THAT IS BODY.PY'S GEOMETRY TALKING. A real forefoot
    rocker pivots at the metatarsal heads with the toes staying flat, and this
    module was written that way first: a toe bone, a counter-rotation, and the
    toes held on the deck. It does not survive contact with the mesh. body.py
    builds a foot from THREE rings whose last ring centre sits at z = 0.086 while
    its own vertices reach z = 0.191 -- the ring is 2.4x longer than it is wide --
    so there is no ring forward of the metatarsal line to bind a toe bone to, the
    toe bone got zero weight, and the "flat toes" dipped 22 mm through the deck.
    Measured, in `swing_clearance`, which is why the ball pivot is gone. Pivoting
    a rigid sole on its own forward-most contact point cannot penetrate anything.
    `toe_r`/`toe_l` survive as tip MARKERS carrying no weight; when body.py's foot
    grows a fourth ring they become real bones and this comment is the changelog.
    """
    r = q / max(duty, 1e-9)
    if not ff["rolls"]:
        return (ff["x"], ground + ff["rise"], plant_z), 0.0, "flat"
    if r < p1:
        t = 1.0 - r / p1
        pitch = -th_hs * t
        off = ff["heel"]
        phase = "heel"
    elif r < p2:
        return (ff["x"], ground + ff["rise"], plant_z), 0.0, "flat"
    else:
        t = (r - p2) / max(1.0 - p2, 1e-9)
        pitch = th_to * t
        off = ff["tip"]
        phase = "toe"
    piv = (ff["x"], ground, plant_z + off)
    return (_add(piv, _mv(rot_x(pitch), (0.0, ff["rise"], -off))), pitch, phase)


def _leg_ik(hip, target, a, b, rest_thigh, rest_shin, parent_R):
    """Two-link IK in the plane containing the hip-ankle line and +Z.

    The knee is placed FORWARD by construction -- a backward knee is the classic
    procedural-walk failure and it is prevented here rather than checked for
    afterwards, though `_selftest` checks for it anyway on the built poses.
    """
    d_vec = _sub(target, hip)
    d = _norm(d_vec)
    lim = 0.9995 * (a + b)
    clamped = d > lim
    d = min(d, lim)
    d = max(d, abs(a - b) + 1e-6)
    u = _unit(d_vec)
    ca = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2.0 * a * d)))
    al = math.acos(ca)
    fwd = (0.0, 0.0, 1.0)
    f = _sub(fwd, _scale(u, _dot(fwd, u)))
    f = _unit(f) if _norm(f) > 1e-6 else _unit(_sub((0.0, 1.0, 0.0),
                                                    _scale(u, u[1])))
    knee = _add(hip, _scale(_add(_scale(u, math.cos(al)),
                                 _scale(f, math.sin(al))), a))
    Rw_t = min_arc(rest_thigh, _unit(_sub(knee, hip)))
    Rw_s = min_arc(rest_shin, _unit(_sub(target, knee)))
    return (_mul(_mt(parent_R), Rw_t), _mul(_mt(Rw_t), Rw_s), knee, Rw_s,
            d / (a + b), clamped)


def walk_clip(species, npc_id, g_ms2, speed=None, frames=32, lod=0,
              name=None, allow_run=False):
    """A walk, generated from the gait and the figure. Deterministic in both.

    Nothing in the pose is authored in metres. The stride comes from `gait()`,
    the foot plant from the measured foot, the pelvis bob from the leg's own
    reach at the stride the gait asked for, and the lateral sway from the leg's
    own x offset. Change the gravity and every one of those moves.
    """
    rg = rig(species, npc_id, lod)
    sk = rg.skel
    if sk.plan == "column":
        raise ValueError(
            "the column plan (Kosh) has no legs and no walk: `Vorlon moree.jpg` "
            "shows a floor-length robe with none visible, so a gait would be an "
            "invention with nothing constraining it. Use glide_clip().")
    st = _style(rg.sp, rg.ind)
    L, ground = sk.leg_length_m, sk.ground_y
    gt = gait(g_ms2, L, speed, allow_run=allow_run)
    S, D, T = gt["stride_m"], gt["duty"], gt["cycle_s"]
    lx = abs(sk.head("hip_r")[0])
    ff = {s: _foot_frame(sk, s, ground) for s in "rl"}
    a = {s: _norm(_sub(sk.head("hip_%s" % s), sk.head("knee_%s" % s))) for s in "rl"}
    b = {s: _norm(_sub(sk.head("knee_%s" % s), sk.head("ankle_%s" % s))) for s in "rl"}
    rest_th = {s: _unit(_sub(sk.head("knee_%s" % s), sk.head("hip_%s" % s)))
               for s in "rl"}
    rest_sh = {s: _unit(_sub(sk.head("ankle_%s" % s), sk.head("knee_%s" % s)))
               for s in "rl"}
    reach = K_EXT * sk.reach_m
    th_hs = math.radians(POSE["heel_strike_deg"])
    th_to = math.radians(POSE["toe_off_deg"])
    lift = POSE["swing_lift_f"] * L
    off = {"r": 0.0, "l": 0.5}

    def ankle_at(s, p):
        """Ankle target, foot pitch, phase label and stance flag at phase p."""
        u = p + off[s]
        k = math.floor(u)
        q = u - k
        plant = S * (k - off[s]) + D * S / 2.0
        if q < D:
            pos, pitch, ph = _stance_ankle(ff[s], ground, plant, q, D,
                                           POSE["heel_rocker"], POSE["flat_end"],
                                           th_hs, th_to)
            return pos, pitch, ph, True
        tau = (q - D) / (1.0 - D)
        e0, pi0, _p0 = _stance_ankle(ff[s], ground, plant, D * 0.99999, D,
                                     POSE["heel_rocker"], POSE["flat_end"],
                                     th_hs, th_to)
        e1, pi1, _p1 = _stance_ankle(ff[s], ground, plant + S, 0.0, D,
                                     POSE["heel_rocker"], POSE["flat_end"],
                                     th_hs, th_to)
        e = _smoothstep(tau)
        pos = _add(_add(_scale(e0, 1.0 - e), _scale(e1, e)),
                   (0.0, lift * math.sin(math.pi * tau), 0.0))
        return pos, pi0 + (pi1 - pi0) * e, "swing", False

    def frame_setup(fdx):
        p = fdx / frames
        yaw = math.radians(POSE["pelvis_yaw_deg"]) * st["yaw"] * math.cos(2 * math.pi * p)
        roll = -math.radians(POSE["pelvis_roll_deg"]) * st["roll"] * math.sin(2 * math.pi * p)
        lean = math.radians(POSE["lean_deg_per_froude"]) * gt["froude"]
        loc = {
            sk.index["pelvis"]: _mul(rot_y(yaw), rot_z(roll)),
            sk.index["spine"]: _mul(rot_y(-yaw), rot_x(lean * 0.5)),
            sk.index["chest"]: _mul(rot_y(-POSE["chest_counter"] * yaw),
                                    rot_x(lean * 0.5)),
            sk.index["neck"]: IDENT,
        }
        sway = -POSE["sway_f"] * lx * math.sin(2 * math.pi * p)
        return p, yaw, loc, sway, {s: ankle_at(s, p) for s in "rl"}

    # PASS ONE: the pelvis height ceiling, frame by frame. The hip can be no
    # higher than the point from which BOTH feet are still reachable at K_EXT of
    # full extension, and that ceiling -- not an authored curve -- is what makes
    # the walk bob. The stride sets it, so gravity sets it.
    ceil = []
    for fdx in range(frames):
        p, _yaw, loc, sway, targets = frame_setup(fdx)
        w0 = fk(sk, loc, (sway, 0.0, S * p))
        best = None
        for s in "rl":
            pos = targets[s][0]
            hip = w0[sk.index["hip_%s" % s]][1]
            dxz = math.hypot(hip[0] - pos[0], hip[2] - pos[2])
            if dxz >= reach:
                raise ValueError(
                    f"stride {S:.3f} m over-extends the leg: horizontal reach "
                    f"{dxz:.3f} m against {reach:.3f} m available at Fr="
                    f"{gt['froude']:.3f}")
            need = pos[1] + math.sqrt(reach * reach - dxz * dxz) - hip[1]
            best = need if best is None else min(best, need)
        ceil.append(best)
    lo = min(ceil)
    keep = POSE["knee_flex_keep"]

    root, tracks, diag = [], {}, {"extension": [], "knee_fwd": [], "clamped": 0,
                                  "bob": [], "sway": []}
    names = [bn.name for bn in sk.bones]
    for n in names:
        tracks[n] = []
    # PASS TWO. Note that it calls the SAME `frame_setup` pass one used: a second
    # copy of those four expressions would let the height ceiling be solved for a
    # pose the clip does not then use, and the two would drift apart at the first
    # edit with nothing to catch it.
    for fdx in range(frames):
        p, yaw, loc, sway, targets = frame_setup(fdx)
        root_t = (sway, lo + keep * (ceil[fdx] - lo), S * p)
        w1 = fk(sk, loc, root_t)
        for s in "rl":
            pos, pitch, _ph, _stance = targets[s]
            hip = w1[sk.index["hip_%s" % s]][1]
            pR = w1[sk.index["pelvis"]][0]
            lt, ls, knee, Rw_s, ext, clamped = _leg_ik(
                hip, pos, a[s], b[s], rest_th[s], rest_sh[s], pR)
            diag["extension"].append(ext)
            diag["clamped"] += int(clamped)
            # Perpendicular offset of the knee from the hip-ankle line, in the
            # forward direction. Comparing the knee's z against the segment's
            # MIDPOINT is wrong whenever the thigh and shin differ in length,
            # which they do here (0.558 / 0.442), and the first version of this
            # diagnostic reported a correct knee as backward because of it.
            u = _unit(_sub(pos, hip))
            d = _sub(knee, hip)
            diag["knee_fwd"].append(_sub(d, _scale(u, _dot(d, u)))[2])
            loc[sk.index["hip_%s" % s]] = lt
            loc[sk.index["knee_%s" % s]] = ls
            if sk.has("ankle_%s" % s):
                loc[sk.index["ankle_%s" % s]] = _mul(_mt(Rw_s), rot_x(pitch))
            if sk.has("toe_%s" % s):
                loc[sk.index["toe_%s" % s]] = IDENT      # a marker, see above
            sgn = 1.0 if s == "r" else -1.0
            sw = sgn * math.radians(POSE["arm_swing_deg"]) * st["arm"] \
                * math.cos(2 * math.pi * p)
            flex = math.radians(POSE["elbow_base_deg"]
                                + POSE["elbow_swing_deg"] * max(0.0, -sw)
                                / max(math.radians(POSE["arm_swing_deg"]), 1e-9))
            loc[sk.index["shoulder_%s" % s]] = _mul(
                rot_z(-sgn * math.radians(POSE["arm_abduct_deg"])), rot_x(sw))
            loc[sk.index["elbow_%s" % s]] = rot_x(-flex)
        # The head is stabilised in world, not carried by the trunk: it keeps a
        # stated residual of the chest's yaw and a small nod at step frequency.
        nR = w1[sk.index["neck"]][0]
        tgt = _mul(rot_y(POSE["head_residual"] * -POSE["chest_counter"] * yaw
                         * st["head"]),
                   rot_x(math.radians(POSE["nod_deg"]) * st["head"]
                         * math.cos(4 * math.pi * p)))
        loc[sk.index["head"]] = _mul(_mt(nR), tgt)

        root.append(root_t)
        diag["bob"].append(root_t[1])
        diag["sway"].append(root_t[0])
        for i, bn in enumerate(sk.bones):
            tracks[bn.name].append(mat_to_quat(loc.get(i, IDENT)))
    meta = dict(gt)
    meta.update({"clip": "walk", "bob_range_m": max(diag["bob"]) - min(diag["bob"]),
                 "sway_range_m": max(diag["sway"]) - min(diag["sway"]),
                 "max_extension": max(diag["extension"]),
                 "min_knee_forward_m": min(diag["knee_fwd"]),
                 "ik_clamped": diag["clamped"],
                 "root_advance_m": S, "style": st})
    return Clip(name or "walk", species, npc_id, sk.plan, T, frames, True,
                tuple(root), {k: tuple(v) for k, v in tracks.items()}, meta)


# Height above the contact plane below which a vertex counts as touching. Has to
# sit between float noise and the swing clearance (0.055 x leg length, ~5 cm), and
# it is the threshold the foot-slide measurement selects on, so a value too large
# would sweep swinging vertices into the contact set and report a false slide.
CONTACT_EPS_M = 0.004


def contact_slip(rg: Rig, clip: Clip, eps=CONTACT_EPS_M):
    """The foot-sliding measurement, taken through the WHOLE pipeline.

    Poses the actual mesh from the baked quaternion tracks, finds every vertex
    within `eps` of the contact plane, and measures how far each moved
    horizontally between consecutive frames while it was still down. This is not
    a check that the IK solver inverts its own forward kinematics -- that would
    be a tautology of exactly the kind AAA-STANDARD scores ROBUSTNESS 0. It runs
    Euler -> quaternion -> matrix -> skinning -> world and includes the root
    motion, so it fails if the root advance and the stride ever disagree, which
    is the way procedural walks actually break.
    """
    adv = clip.meta.get("root_advance_m", 0.0)
    prev, worst, n = None, 0.0, 0
    for f in range(clip.frames + 1):
        wrap = f >= clip.frames
        _w, mats = clip.pose(rg.skel, f % clip.frames)
        posed = apply_pose(rg, mats)
        cur = {}
        for pi, (name, verts, _t) in enumerate(posed):
            if name not in ("foot", "leg", "suit_leg"):
                continue
            for vi, v in enumerate(verts):
                if v[1] - rg.skel.ground_y <= eps:
                    cur[(pi, vi)] = (v[0], v[1], v[2] + (adv if wrap else 0.0))
        if prev is not None:
            for k, v in cur.items():
                if k in prev:
                    n += 1
                    worst = max(worst, math.hypot(v[0] - prev[k][0],
                                                  v[2] - prev[k][2]))
        prev = cur
    return {"max_slip_m": worst, "contact_pairs": n}


def swing_clearance(rg: Rig, clip: Clip):
    """Lowest point of a foot that is NOT in contact, per frame. Must stay > 0 or
    the swinging foot ploughs the deck -- the other half of the plant problem and
    the one a render at walking pace will not show."""
    worst = 1e9
    for f in range(clip.frames):
        _w, mats = clip.pose(rg.skel, f)
        posed = apply_pose(rg, mats)
        for name, verts, _t in posed:
            if name not in ("foot", "leg", "suit_leg"):
                continue
            lo = min(v[1] for v in verts) - rg.skel.ground_y
            if lo > CONTACT_EPS_M:
                worst = min(worst, lo)
            else:
                worst = min(worst, max(lo, 0.0) if lo >= -1e-9 else lo)
    return worst


def interpenetration(rg: Rig, clip: Clip = None, pairs=(("hand", "leg"),
                                                        ("hand", "torso"),
                                                        ("foot", "leg"))):
    """Vertices of one part inside another, worst over a clip (or at rest).

    body.py builds parts as separate closed shells that DELIBERATELY overlap at
    the joints -- an arm root sits inside the torso -- so the meaningful question
    is never "is there any overlap" but "does the pose make it worse than the
    bind pose". This measures both, using body.contains(), and it is what solved
    POSE["arm_abduct_deg"]: at 0 degrees the swinging hand went from 22% inside
    the thigh at rest to 49% mid-cycle, and no render at walking scale showed it.
    """
    def group(parts):
        d = {}
        for n, v, t in parts:
            d.setdefault(n, []).append((v, t))
        return d

    def worst(d):
        out = {}
        for a, b in pairs:
            w = 0
            for av, _at in d.get(a, []):
                for bv, bt in d.get(b, []):
                    w = max(w, sum(1 for p in av if body.contains(bv, bt, p)))
            out[f"{a}_in_{b}"] = w
        return out

    rest = worst(group(rg.parts))
    if clip is None:
        return {"rest": rest, "posed": rest}
    posed = {k: 0 for k in rest}
    for f in range(clip.frames):
        _w, mats = clip.pose(rg.skel, f)
        d = group(apply_pose(rg, mats))
        for k, v in worst(d).items():
            posed[k] = max(posed[k], v)
    return {"rest": rest, "posed": posed,
            "worse_than_rest": {k: posed[k] - rest[k] for k in rest}}


def _planted_clip(rg, name, duration, frames, g_ms2, pose_fn, meta=None,
                  seat_h=None):
    """Shared body for every clip whose feet do not move: idle, talk, sit.

    The feet are pinned to their rest positions (or to a seat's geometry) and the
    pelvis is moved by `pose_fn`; the legs are solved by the same IK the walk
    uses. That is deliberate -- an idle whose feet drift is the commonest crowd
    bug there is, and here it cannot happen without the walk's own foot-slide
    measurement catching it, because it is the same measurement.
    """
    sk = rg.skel
    ground = sk.ground_y
    sides = [s for s in "rl" if sk.has("hip_%s" % s)]
    a = {s: _norm(_sub(sk.head("hip_%s" % s), sk.head("knee_%s" % s))) for s in sides}
    b = {s: _norm(_sub(sk.head("knee_%s" % s), sk.head("ankle_%s" % s))) for s in sides}
    rest_th = {s: _unit(_sub(sk.head("knee_%s" % s), sk.head("hip_%s" % s)))
               for s in sides}
    rest_sh = {s: _unit(_sub(sk.head("ankle_%s" % s), sk.head("knee_%s" % s)))
               for s in sides}
    ff = {s: _foot_frame(sk, s, ground) for s in sides}
    targets, dangle = {}, {}
    for s in sides:
        if seat_h is None:
            targets[s] = (ff[s]["x"], ground + ff[s]["rise"], 0.0)
            dangle[s] = 0.0
        else:
            # Seated: the thigh reaches forward by its own length, the shin drops
            # to the deck if it can and hangs if it cannot. A Vree on a chair
            # built for a human does not have its feet on the floor, and that
            # falls out of the arithmetic rather than being animated.
            hip_y = ground + seat_h
            zk = a[s]
            drop = hip_y - (ground + ff[s]["rise"])
            reach2 = a[s] + b[s]
            d = math.hypot(zk, drop)
            if d <= 0.995 * reach2:
                targets[s] = (ff[s]["x"], ground + ff[s]["rise"], zk)
            else:
                k = 0.995 * reach2 / d
                targets[s] = (ff[s]["x"], hip_y - drop * k, zk * k)
                dangle[s] = drop * (1.0 - k)
    root, tracks = [], {bn.name: [] for bn in sk.bones}
    for f in range(frames):
        p = f / frames
        loc, root_t = pose_fn(p, sk)
        w1 = fk(sk, loc, root_t)
        for s in sides:
            hip = w1[sk.index["hip_%s" % s]][1]
            pR = w1[sk.index["pelvis"]][0]
            lt, ls, _k, Rw_s, _e, _c = _leg_ik(hip, targets[s], a[s], b[s],
                                               rest_th[s], rest_sh[s], pR)
            loc[sk.index["hip_%s" % s]] = lt
            loc[sk.index["knee_%s" % s]] = ls
            if sk.has("ankle_%s" % s):
                loc[sk.index["ankle_%s" % s]] = _mt(Rw_s)
        root.append(root_t)
        for i, bn in enumerate(sk.bones):
            tracks[bn.name].append(mat_to_quat(loc.get(i, IDENT)))
    m = {"clip": name, "g": g_ms2 / G0, "root_advance_m": 0.0,
         "feet_dangle_m": max(dangle.values()) if dangle else 0.0}
    m.update(meta or {})
    return Clip(name, rg.species, rg.npc_id, sk.plan, duration, frames, True,
                tuple(root), {k: tuple(v) for k, v in tracks.items()}, m)


def sway_frequency(rg: Rig, g_ms2):
    """Quiet standing is an inverted pendulum about the ankles, so postural sway
    has the SAME sqrt(g/h) timescale the gait does -- with h the centre of mass
    height rather than the leg length. In Grey people sway faster and less; on
    Blue's light decks slower and more. One derivation, two systems."""
    return math.sqrt(g_ms2 / rg.skel.com_height_m) / (2.0 * math.pi)


IDLE = {"sway_cycles": 4, "breaths_per_loop": 2, "sway_amp_f": 0.11,
        "breath_deg": 0.9, "drift_deg": 1.1, "settle_f": 0.012}


def idle_clip(species, npc_id, g_ms2, frames=48, lod=0):
    """Standing. Feet planted, weight drifting, chest breathing."""
    rg = rig(species, npc_id, lod)
    sk = rg.skel
    if sk.plan == "column":
        return glide_clip(species, npc_id, g_ms2, frames=frames, lod=lod,
                          speed=0.0, name="idle")
    st = _style(rg.sp, rg.ind)
    f_sway = sway_frequency(rg, g_ms2)
    dur = IDLE["sway_cycles"] / f_sway
    lx = abs(sk.head("hip_r")[0])
    amp = IDLE["sway_amp_f"] * lx * (G0 / g_ms2)      # softer gravity, wider sway
    ph = _u(f"{species}:{npc_id}", "idle_phase") * math.tau
    # Deterministic per-resident phase: 500 agents playing one clip in lockstep
    # is a chorus line, and it is the single most visible crowd failure there is.
    settle = -IDLE["settle_f"] * sk.leg_length_m * (g_ms2 / G0)

    def pose(p, s):
        t = p * math.tau
        sw = amp * math.sin(IDLE["sway_cycles"] * t + ph)
        br = math.radians(IDLE["breath_deg"]) * math.sin(
            IDLE["breaths_per_loop"] * t + ph)
        dr = math.radians(IDLE["drift_deg"]) * st["head"]
        loc = {
            s.index["pelvis"]: rot_z(-0.35 * sw / max(lx, 1e-6) * 0.10),
            s.index["spine"]: rot_x(br * 0.5),
            s.index["chest"]: rot_x(br),
            s.index["neck"]: IDENT,
            s.index["head"]: _mul(rot_y(dr * math.sin(t + ph)),
                                  rot_x(-br * 0.6)),
        }
        for side in "rl":
            if s.has("shoulder_%s" % side):
                sgn = 1.0 if side == "r" else -1.0
                loc[s.index["shoulder_%s" % side]] = rot_x(
                    math.radians(1.5) * math.sin(t + ph + sgn))
                loc[s.index["elbow_%s" % side]] = rot_x(
                    -math.radians(POSE["elbow_base_deg"] * 0.6))
        return loc, (sw, settle, 0.0)

    return _planted_clip(rg, "idle", dur, frames, g_ms2, pose,
                         {"sway_hz": f_sway, "sway_amp_m": amp,
                          "rate_scale_note": "playback rate goes as sqrt(g)"})


TALK = {"gesture_deg": 34.0, "gesture_elbow_deg": 52.0, "head_turn_deg": 12.0,
        "beats": 3}


def talk_clip(species, npc_id, g_ms2, frames=64, lod=0):
    """Standing and talking: the idle, plus one arm gesturing on the beat and a
    head turned toward whoever is being talked to. The gesture is baked; the
    look-at is a runtime additive -- see `look_at()` -- because who you are
    talking to is not knowable at bake time."""
    rg = rig(species, npc_id, lod)
    sk = rg.skel
    if sk.plan == "column":
        return glide_clip(species, npc_id, g_ms2, frames=frames, lod=lod,
                          speed=0.0, name="talk")
    st = _style(rg.sp, rg.ind)
    f_sway = sway_frequency(rg, g_ms2)
    dur = IDLE["sway_cycles"] / f_sway
    lx = abs(sk.head("hip_r")[0])
    amp = IDLE["sway_amp_f"] * lx * (G0 / g_ms2) * 0.7
    ph = _u(f"{species}:{npc_id}", "talk_phase") * math.tau
    hand = "r" if _u(f"{species}:{npc_id}", "talk_hand") < 0.5 else "l"
    settle = -IDLE["settle_f"] * sk.leg_length_m * (g_ms2 / G0)

    def pose(p, s):
        t = p * math.tau
        beat = 0.5 - 0.5 * math.cos(TALK["beats"] * t + ph)
        sw = amp * math.sin(IDLE["sway_cycles"] * t + ph)
        br = math.radians(IDLE["breath_deg"]) * math.sin(2 * t + ph)
        loc = {
            s.index["pelvis"]: IDENT,
            s.index["spine"]: rot_x(br * 0.5),
            s.index["chest"]: _mul(rot_y(math.radians(3.0) * beat), rot_x(br)),
            s.index["neck"]: IDENT,
            s.index["head"]: _mul(rot_y(math.radians(TALK["head_turn_deg"])
                                        * st["head"] * (0.6 + 0.4 * beat)),
                                  rot_x(math.radians(2.5) * (beat - 0.5))),
        }
        for side in "rl":
            g_amp = beat if side == hand else 0.18 * beat
            loc[s.index["shoulder_%s" % side]] = rot_x(
                -math.radians(TALK["gesture_deg"]) * st["arm"] * g_amp)
            loc[s.index["elbow_%s" % side]] = rot_x(
                -math.radians(POSE["elbow_base_deg"]
                              + TALK["gesture_elbow_deg"] * g_amp))
        return loc, (sw, settle, 0.0)

    return _planted_clip(rg, "talk", dur, frames, g_ms2, pose,
                         {"gesture_hand": hand, "sway_hz": f_sway})


def seat_height(species, npc_id=NOMINAL, lod=0):
    """A seat that fits this individual: knee height above the deck.

    DERIVED, and it lands on the furniture the station already has. A chair whose
    seat is at the sitter's knee puts the thigh horizontal and the shin vertical,
    which is the definition of a fitted seat -- and `station/zocalo.py` and
    `station/council_chamber.py` independently authored 0.45 m and 0.46 m from
    reference frames. `_selftest` imports those rather than copying them.
    """
    sk = rig(species, npc_id, lod).skel
    return sk.head("knee_r")[1] - sk.ground_y


def sit_clip(species, npc_id, g_ms2, seat_h_m=None, frames=48, lod=0):
    """Sitting. Pose derived from the seat's height and the sitter's own leg."""
    rg = rig(species, npc_id, lod)
    sk = rg.skel
    if sk.plan == "column":
        return glide_clip(species, npc_id, g_ms2, frames=frames, lod=lod,
                          speed=0.0, name="sit")
    seat = seat_h_m if seat_h_m is not None else seat_height(species, npc_id, lod)
    st = _style(rg.sp, rg.ind)
    f_sway = sway_frequency(rg, g_ms2)
    dur = IDLE["sway_cycles"] / f_sway
    ph = _u(f"{species}:{npc_id}", "sit_phase") * math.tau
    hip_rest = sk.head("hip_r")[1] - sk.ground_y
    dy = seat - hip_rest
    recline = math.radians(7.0)

    def pose(p, s):
        t = p * math.tau
        br = math.radians(IDLE["breath_deg"] * 1.3) * math.sin(2 * t + ph)
        loc = {
            s.index["pelvis"]: rot_x(-recline * 0.4),
            s.index["spine"]: rot_x(-recline * 0.3 + br * 0.5),
            s.index["chest"]: rot_x(-recline * 0.3 + br),
            s.index["neck"]: IDENT,
            s.index["head"]: _mul(rot_x(recline * 0.8 - br * 0.6),
                                  rot_y(math.radians(2.0) * st["head"]
                                        * math.sin(t + ph))),
        }
        for side in "rl":
            loc[s.index["shoulder_%s" % side]] = rot_x(math.radians(6.0))
            loc[s.index["elbow_%s" % side]] = rot_x(
                -math.radians(POSE["elbow_base_deg"] + 46.0))
        return loc, (0.0, dy, 0.0)

    return _planted_clip(rg, "sit", dur, frames, g_ms2, pose,
                         {"seat_h_m": seat, "hip_drop_m": -dy,
                          "sway_hz": f_sway}, seat_h=seat)


GLIDE = {"speed_ms": 0.9, "bob_f": 0.004, "lean_deg": 1.5, "period_s": 6.0}


def glide_clip(species, npc_id, g_ms2, frames=48, lod=0, speed=None, name=None):
    """Kosh moves. How, exactly, the reference does not say.

    `Vorlon moree.jpg` (authority 2) gives a floor-length robe with no visible
    legs, so there is no gait to derive and inventing one would be unmarked
    invention. What is built instead is DECLARED as an extrapolation: a slow
    glide with a small vertical breathing motion and a slight lean into the
    direction of travel, and the speed is a stated number rather than a solved
    one. If a frame ever shows a Vorlon's hem, this is the clip to throw away.
    """
    rg = rig(species, npc_id, lod)
    sk = rg.skel
    v = GLIDE["speed_ms"] if speed is None else speed
    dur = GLIDE["period_s"]
    ph = _u(f"{species}:{npc_id}", "glide_phase") * math.tau
    root, tracks = [], {bn.name: [] for bn in sk.bones}
    for f in range(frames):
        p = f / frames
        t = p * math.tau
        loc = {}
        for bn in ("base", "column", "collar", "head", "pelvis", "spine",
                   "chest", "neck"):
            if sk.has(bn):
                loc[sk.index[bn]] = rot_x(math.radians(GLIDE["lean_deg"])
                                          * (0.25 if bn != "head" else -0.5)
                                          * math.sin(t + ph))
        root_t = (0.0, GLIDE["bob_f"] * sk.stature_m * math.sin(2 * t + ph),
                  v * dur * p)
        root.append(root_t)
        for i, bn in enumerate(sk.bones):
            tracks[bn.name].append(mat_to_quat(loc.get(i, IDENT)))
    return Clip(name or "glide", species, npc_id, sk.plan, dur, frames, True,
                tuple(root), {k: tuple(v) for k, v in tracks.items()},
                {"clip": name or "glide", "speed_ms": v,
                 "root_advance_m": v * dur, "authority": 5,
                 "note": "EXTRAPOLATED: no reference shows Vorlon locomotion"})


# ---------------------------------------------------------------------------
# The Froude ladder: how many baked walks the station actually needs
# ---------------------------------------------------------------------------
# A walk's SHAPE is a function of Froude number alone (`duty_at_froude`), so the
# 217 habitable decks do not need 217 walks -- they need enough rungs that
# blending between neighbours is under the deviation budget. The rung count is
# MEASURED the way station/lod.py measures a switch distance: build the blend,
# build the truth, and difference them. It is not chosen.
LADDER_HONEST_FROM_M = 2.23     # body.lod_chain()'s LOD0/LOD1 boundary: the
#                                 closest a figure is normally drawn at full rate


def _nlerp(qa, qb, t):
    """What a runtime blend actually does. Note the sign fix: q and -q are the
    same rotation, and lerping between them without it swings the long way round
    -- a shoulder that snaps through the torso for one frame."""
    d = sum(a * b for a, b in zip(qa, qb))
    qb = qb if d >= 0.0 else tuple(-x for x in qb)
    q = tuple(a + (b - a) * t for a, b in zip(qa, qb))
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def blend_error(species, npc_id, g_ms2, fr_a, fr_b, frames=24, lod=0):
    """Worst joint displacement from blending two rungs instead of generating."""
    rg = rig(species, npc_id, lod)
    L = rg.skel.leg_length_m

    def at(fr):
        return walk_clip(species, npc_id, g_ms2, speed=math.sqrt(fr * g_ms2 * L),
                         frames=frames, lod=lod, allow_run=True)

    # The blend parameter is RELATIVE STRIDE, not Fr. The runtime knows Fr and
    # raising it to 0.30 is one pow; what it buys is that the thing being
    # interpolated -- where the feet are -- is very nearly linear in it, and the
    # midpoint the blend is compared against has to be the midpoint in the same
    # variable or the measurement is scoring the parameterisation rather than the
    # ladder. Measured: 10.6 mm worst gap in Fr, 1.6 mm in stride, same rungs.
    fr_mid = (0.5 * (fr_a ** LAMBDA_EXP + fr_b ** LAMBDA_EXP)) ** (1.0 / LAMBDA_EXP)
    ca, cb, cm = at(fr_a), at(fr_b), at(fr_mid)
    worst = 0.0
    for f in range(frames):
        loc = {}
        for name in ca.tracks:
            loc[rg.skel.index[name]] = quat_to_mat(
                _nlerp(ca.tracks[name][f], cb.tracks[name][f], 0.5))
        rt = tuple(0.5 * (a + b) for a, b in zip(ca.root[f], cb.root[f]))
        wb = fk(rg.skel, loc, rt)
        wm = cm.pose(rg.skel, f)[0]
        for i in range(len(rg.skel.bones)):
            worst = max(worst, _norm(_sub(wb[i][1], wm[i][1])))
    return worst


def froude_ladder(rungs=None, species="human", npc_id=NOMINAL, frames=24):
    """The rung set, and the measurement that decided how many there are."""
    lo, hi = 0.02, FR_RUN
    g = G0

    # Rungs are spaced uniformly in RELATIVE STRIDE, not in Fr. Stride goes as
    # Fr^0.30, whose slope is infinite at the origin, so evenly spaced Fr puts
    # almost all the pose change in the first gap: measured, the linear ladder's
    # worst gap was 65.6 mm and its best 1.3 mm, a 51x imbalance, and the
    # measurement is what said so. Uniform in Fr^B equalises them.
    def _fr(t):
        return (lo ** LAMBDA_EXP + (hi ** LAMBDA_EXP - lo ** LAMBDA_EXP) * t) \
            ** (1.0 / LAMBDA_EXP)

    if rungs is None:
        for n in range(2, 25):
            fr = [_fr(i / (n - 1)) for i in range(n)]
            err = max(blend_error(species, npc_id, g, fr[i], fr[i + 1], frames)
                      for i in range(n - 1))
            if body.honest_from_m(err) <= LADDER_HONEST_FROM_M:
                rungs = n
                break
        else:
            rungs = 24
    fr = [_fr(i / (rungs - 1)) for i in range(rungs)]
    errs = [blend_error(species, npc_id, g, fr[i], fr[i + 1], frames)
            for i in range(rungs - 1)]
    return {"rungs": rungs, "froude": fr, "blend_error_m": max(errs),
            "per_gap_m": errs,
            "honest_from_m": round(body.honest_from_m(max(errs)), 2),
            "criterion": f"blend of adjacent rungs within the pixel budget from "
                         f"{LADDER_HONEST_FROM_M} m, body.lod_chain()'s LOD0/1 "
                         f"boundary",
            "note": "the SHAPE of a walk is a function of Fr alone, so gravity "
                    "and leg length enter only through Fr and the playback rate"}


def temporal_ladder(species="human", npc_id=NOMINAL, g_ms2=G0, truth=256):
    """How many keys a clip needs, and how often the runtime must resample it.

    Same measurement as the Froude ladder, in time instead: build the walk at a
    high key rate, rebuild it decimated, interpolate the decimated one back and
    difference the joint positions. It answers two questions with one number --
    the baked key count, and the update rate a distant crowd agent can run at --
    because both are "how far does a joint move between samples".
    """
    rg = rig(species, npc_id, 0)
    ref = walk_clip(species, npc_id, g_ms2, frames=truth)
    out = []
    for n in (8, 12, 16, 24, 32, 48, 64):
        c = walk_clip(species, npc_id, g_ms2, frames=n)
        worst = 0.0
        for f in range(truth):
            t = f / truth * n
            i0, fr = int(t) % n, t - int(t)
            i1 = (i0 + 1) % n
            loc = {}
            for name in c.tracks:
                loc[rg.skel.index[name]] = quat_to_mat(
                    _nlerp(c.tracks[name][i0], c.tracks[name][i1], fr))
            r0, r1 = c.root[i0], c.root[i1]
            adv = c.meta["root_advance_m"] if i1 < i0 else 0.0
            rt = (r0[0] + (r1[0] - r0[0]) * fr, r0[1] + (r1[1] - r0[1]) * fr,
                  r0[2] + (r1[2] + adv - r0[2]) * fr)
            wb = fk(rg.skel, loc, rt)
            wm = ref.pose(rg.skel, f)[0]
            for i in range(len(rg.skel.bones)):
                worst = max(worst, _norm(_sub(wb[i][1], wm[i][1])))
        out.append({"keys": n, "error_m": worst,
                    "honest_from_m": round(body.honest_from_m(worst), 2),
                    "hz_at_1g": n / ref.meta["cycle_s"]})
    return out


def clip_keys():
    """The baked key count, DERIVED: the coarsest rung of `temporal_ladder` whose
    interpolation error is inside the pixel budget at the LOD0/LOD1 boundary."""
    for row in temporal_ladder():
        if row["honest_from_m"] <= LADDER_HONEST_FROM_M:
            return row["keys"]
    return 64


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------
QUAT_BYTES = 16             # 4 x float32; what Godot stores in a rotation track
VEC3_BYTES = 12
MAT43_BYTES = 48            # a bone palette entry: 4x3 float32
CLIP_SET = ("walk_ladder", "idle", "talk", "sit")


def cost_report(keys=None):
    """What the animation layer costs, and what it does NOT cost.

    The headline is that it does not scale with the population at all. A clip is
    a set of ROTATIONS, and a rotation is proportion-independent, so 155,000
    humans share one walk ladder and differ by a phase (one float) and a playback
    rate (one float). The population is a function -- `schedule.py` makes the same
    argument about identity -- and functions are free.
    """
    import schedule as sched                                  # noqa: PLC0415
    lad = froude_ladder()
    tl = temporal_ladder()
    keys = keys or next((r["keys"] for r in tl
                         if r["honest_from_m"] <= LADDER_HONEST_FROM_M), 64)
    # The update-rate LOD, DERIVED from the same measurement: at each of
    # schedule.NPC_BUDGET's distance bands, the coarsest key rate whose
    # interpolation error is still inside the pixel budget at that distance. A
    # crowd agent at 18 m does not need 60 Hz of skeleton, and this says by how
    # much -- which is where the CPU saving in a 2,000-agent crowd comes from.
    tiers = []
    for name, near, far, _tri, inst in sched.NPC_BUDGET["lod"]:
        ok = [r for r in tl if r["honest_from_m"] <= max(near, 0.5)]
        row = min(ok, key=lambda r: r["keys"]) if ok else tl[-1]
        tiers.append({"band": name, "from_m": near, "to_m": far,
                      "instances": inst, "keys": row["keys"],
                      "hz_at_1g": round(row["hz_at_1g"], 1),
                      "error_m": round(row["error_m"], 5)})
    plans = {}
    for plan, bones in PLAN_BONES.items():
        n = len(bones)
        per_key = n * QUAT_BYTES + VEC3_BYTES
        clips = (lad["rungs"] + 3) if plan != "column" else 4
        plans[plan] = {
            "bones": n,
            "clip_bytes": per_key * keys,
            "clips": clips,
            "set_bytes": per_key * keys * clips,
        }
    per_species = {}
    total = 0
    for k, sp in body.SPECIES.items():
        b = plans[sp.plan]["set_bytes"]
        per_species[k] = b
        total += b
    lod = sched.NPC_BUDGET
    full, crowd = lod["full_agents"], lod["crowd_agents"]
    hum = len(PLAN_BONES["humanoid"])
    trunk = hum - len(BONE_TIER["trunk"])
    palette = full * hum * MAT43_BYTES + crowd * trunk * MAT43_BYTES
    # Vertices actually skinned in the worst visible set, from the LOD chain's
    # own instance caps and body.py's own meshes.
    verts = {}
    for i, (_n, near, far, tri, inst) in enumerate(lod["lod"]):
        lv = min(i, len(body.lod_chain()) - 1)
        v, t, _s = body.build("human", "cost-probe", lv)
        verts[_n] = {"instances": inst, "verts_each": len(v),
                     "verts_total": inst * len(v), "band_m": (near, far)}
    return {
        "keys_per_clip": keys,
        "update_tiers": tiers,
        "rungs": lad["rungs"],
        "per_plan": plans,
        "dataset_bytes_all_species": total,
        "dataset_mb": total / 1e6,
        "note_shared": "one ladder per SPECIES, not per resident: the clips are "
                       "rotations and the per-NPC state is a phase and a rate",
        "per_npc_runtime_bytes": 8,      # phase float32 + rate float32
        "bone_palette_bytes": palette,
        "bone_palette_mb": palette / 1e6,
        "full_agents": full, "crowd_agents": crowd,
        "bone_tiers": {k: (hum if v is None else hum - len(v))
                       for k, v in BONE_TIER.items()},
        "skinned_verts": verts,
        "skinned_verts_total": sum(v["verts_total"] for v in verts.values()),
        "max_influences": MAX_INFLUENCES,
        "draw_calls_added": 0,
        "draw_call_note": "skinning is per-instance data, not a batch break; "
                          f"schedule.NPC_BUDGET caps NPC draw calls at "
                          f"{lod['max_draw_calls']} and this adds none",
        "triangles_added": 0,
        "triangle_note": "animation moves vertices; it emits no geometry, so "
                         "body.crowd_cost() and the NPC triangle budget are "
                         "unchanged by anything in this module",
    }


LOOK_LIMIT = {"yaw_deg": 70.0, "pitch_deg": 40.0, "neck_share": 0.45}


def look_at(skel, yaw_deg, pitch_deg):
    """Additive neck+head rotation, clamped to a human range and split between
    the two joints. Runtime-side: who an NPC is looking at is a property of the
    scene, not of a baked clip, and baking a look would need one clip per
    listener. The clamp is what stops an NPC's head rotating 180 degrees to track
    the player, which is the tell that a crowd is a set of turrets."""
    y = max(-LOOK_LIMIT["yaw_deg"], min(LOOK_LIMIT["yaw_deg"], yaw_deg))
    p = max(-LOOK_LIMIT["pitch_deg"], min(LOOK_LIMIT["pitch_deg"], pitch_deg))
    k = LOOK_LIMIT["neck_share"]
    return {
        "neck": mat_to_quat(_mul(rot_y(math.radians(y * k)),
                                 rot_x(math.radians(p * k)))),
        "head": mat_to_quat(_mul(rot_y(math.radians(y * (1 - k))),
                                 rot_x(math.radians(p * (1 - k))))),
        "clamped": (abs(yaw_deg) > LOOK_LIMIT["yaw_deg"]
                    or abs(pitch_deg) > LOOK_LIMIT["pitch_deg"]),
    }


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def godot_note():
    """The one transform between this frame and the engine's, stated once.

    body.py builds +Z-facing, +Y-up, +X-left. Godot 4 is -Z-forward, +Y-up,
    +X-right. So the export is a 180-degree turn about +Y: negate x and z on
    every position, and negate the x and z components of every quaternion. It is
    written here rather than left in a scene script because a frame convention
    discovered at integration time is a day lost, and `emit()` applies it.
    """
    return {"source_frame": "+Z forward, +Y up, +X left (body.py)",
            "godot_frame": "-Z forward, +Y up, +X right",
            "transform": "rotate 180 about +Y: (x,y,z) -> (-x,y,-z); "
                         "quaternion (x,y,z,w) -> (-x,y,-z,w)",
            "root_motion": "the root track carries the full stride; the runtime "
                           "may consume it in place or drive locomotion from it",
            "bone_rest": "rest rotations are identity; a bone's rest transform is "
                         "a pure translation to its head"}


# Export quantisation. The committed form is JSON because ADR 0001 chose text
# for everything -- diffable, reviewable, regression-testable by an agent with no
# editor -- and full-precision floats make that text four times larger than the
# float32 the runtime will hold. Rounded: 1e-6 on a quaternion component is
# 0.0002 degrees of joint rotation, and 1e-5 m on a root position is 10 microns.
# `_selftest` measures what the rounding does to the posed joints rather than
# assuming it is small, and it comes out at a few microns.
ROUND_Q, ROUND_V = 6, 5


def _to_godot_v(v):
    return (round(-v[0], ROUND_V), round(v[1], ROUND_V), round(-v[2], ROUND_V))


def _to_godot_q(q):
    return (round(-q[0], ROUND_Q), round(q[1], ROUND_Q),
            round(-q[2], ROUND_Q), round(q[3], ROUND_Q))


def skeleton_dict(skel, godot=True):
    fv = _to_godot_v if godot else (lambda v: v)
    return {
        "species": skel.species, "npc_id": skel.npc_id, "plan": skel.plan,
        "frame": "godot" if godot else "body",
        "ground_y": skel.ground_y, "stature_m": skel.stature_m,
        "leg_length_m": skel.leg_length_m, "reach_m": skel.reach_m,
        "com_height_m": skel.com_height_m,
        "bones": [{"name": b.name, "parent": b.parent,
                   "rest_head": fv(b.head), "rest_tail": fv(b.tail)}
                  for b in skel.bones],
        "tiers": {k: (None if v is None else list(v)) for k, v in BONE_TIER.items()},
    }


def clip_dict(clip, godot=True):
    """One clip as JSON. A track whose value never changes is emitted as a
    SINGLE key and the reader holds it constant -- which is most of them: a toe
    marker never moves, and in a standing clip neither do the legs. It takes the
    human set from 856 kB to 545 kB with no loss, because a repeated constant is
    a second copy of a computed value and AAA-STANDARD scores those."""
    fv, fq = ((_to_godot_v, _to_godot_q) if godot else
              ((lambda v: v), (lambda q: q)))

    def track(v):
        out = [fq(q) for q in v]
        return out[:1] if all(q == out[0] for q in out) else out

    return {
        "name": clip.name, "species": clip.species, "plan": clip.plan,
        "duration_s": clip.duration_s, "frames": clip.frames, "loop": clip.loop,
        "frame": "godot" if godot else "body",
        "times": [i * clip.duration_s / clip.frames for i in range(clip.frames)],
        "root_position": ([fv(v) for v in clip.root]
                          if len(set(clip.root)) > 1 else [fv(clip.root[0])]),
        "rotation": {k: track(v) for k, v in clip.tracks.items()},
        "constant_track_note": "a track of length 1 is constant for the clip",
        "meta": {k: v for k, v in clip.meta.items()
                 if isinstance(v, (int, float, str, bool))},
    }


def binding_dict(rg: Rig):
    """The skin binding, once per (species, LOD). Ring-indexed, so it is the same
    table for every resident of the species -- which is the whole memory
    argument, and `_selftest` proves it by binding two residents."""
    out = []
    for pi, ringw, runs in rg.binding:
        out.append({"part": rg.parts[pi][0], "group": rg.groups[pi],
                    "rings": [{"first": a, "count": b - a,
                               "weights": [{"bone": bi, "w": w} for bi, w in ring]}
                              for (a, b), ring in zip(runs, ringw)]})
    return {"species": rg.species, "lod": rg.lod, "parts": out}


def clip_set(species, npc_id, g_ms2=None, keys=None, lod=0):
    """Everything a resident needs: the walk ladder plus the standing clips."""
    keys = keys or 32
    g = g_ms2 if g_ms2 is not None else G0
    rg = rig(species, npc_id, lod)
    if rg.skel.plan == "column":
        return [glide_clip(species, npc_id, g, frames=keys, lod=lod)]
    lad = froude_ladder()
    L = rg.skel.leg_length_m
    out = []
    for i, fr in enumerate(lad["froude"]):
        out.append(walk_clip(species, npc_id, g, speed=math.sqrt(fr * g * L),
                             frames=keys, lod=lod, name=f"walk_fr{i:02d}",
                             allow_run=True))
    out.append(idle_clip(species, npc_id, g, frames=keys + 16, lod=lod))
    out.append(talk_clip(species, npc_id, g, frames=keys * 2, lod=lod))
    out.append(sit_clip(species, npc_id, g, frames=keys + 16, lod=lod))
    return out


def emit(outdir, species=None, npc_id=NOMINAL, keys=None, lod=0, godot=True):
    """Write the committed data: one skeleton, one binding and one clip set per
    species. Nothing here is per-resident."""
    os.makedirs(outdir, exist_ok=True)
    keys = keys or clip_keys()
    written = []
    for k in (species or sorted(body.SPECIES)):
        rg = rig(k, npc_id, lod)
        doc = {
            "generator": "station/npc/animation.py",
            "frame": godot_note(),
            "skeleton": skeleton_dict(rg.skel, godot),
            "binding": binding_dict(rg),
            "clips": [clip_dict(c, godot)
                      for c in clip_set(k, npc_id, keys=keys, lod=lod)],
            "gait_model": {"calibration": CAL, "derived": calibration(),
                           "lambda_exp": LAMBDA_EXP, "fr_run": FR_RUN,
                           "walk_g_min": WALK_G_MIN},
        }
        p = os.path.join(outdir, f"{k}.json")
        with open(p, "w") as f:
            json.dump(doc, f, separators=(",", ":"), sort_keys=True)
        written.append((p, os.path.getsize(p)))
    return written


# ---------------------------------------------------------------------------
# Looking at it: posed OBJ for tools/preview_render.py
# ---------------------------------------------------------------------------
def write_pose_obj(path, entries):
    """`entries` is [(rig, clip, frame, (dx,dy,dz))] -- a contact sheet in one
    OBJ, so one render shows a whole cycle side by side."""
    verts, faces = [], []
    for ent in entries:
        rg, clip, f, off = ent[:4]
        yaw = rot_y(math.radians(ent[4])) if len(ent) > 4 else IDENT
        _w, mats = clip.pose(rg.skel, f % clip.frames)
        for name, vs, ts in apply_pose(rg, mats):
            base = len(verts)
            gi = next(i for i, (n, _v, _t) in enumerate(rg.parts) if n == name)
            verts.extend(_add(_mv(yaw, v), off) for v in vs)
            faces.append((rg.groups[gi], [(a + base, b + base, c + base)
                                          for a, b, c in ts]))
    order, seen = [], set()
    for g, _t in faces:
        if g not in seen:
            seen.add(g)
            order.append(g)
    with open(path, "w") as fh:
        fh.write("# station/npc/animation.py -- posed figures\n")
        for x, y, z in verts:
            fh.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for g in order:
            fh.write(f"g {g}\no {g}\n")
            for gg, ts in faces:
                if gg != g:
                    continue
                for a, b, c in ts:
                    fh.write(f"f {a + 1} {b + 1} {c + 1}\n")
    return path


def contact_sheet(path, species="human", npc_id="sheet", g_ms2=None, n=8,
                  clip=None, spacing=None, lod=0, yaw_deg=90.0, row_z=0.0):
    """One walk cycle laid out in x, in PROFILE, for a single render.

    Profile by default and that is not a preference: a gait is a sagittal-plane
    motion, and a front view of a walk cycle shows almost none of it. The first
    render of this module was a front view and it was unjudgeable.
    """
    g = g_ms2 if g_ms2 is not None else G0
    rg = rig(species, npc_id, lod)
    c = clip or walk_clip(species, npc_id, g, frames=n, lod=lod)
    sp = spacing if spacing is not None else 0.62 * rg.skel.stature_m
    return write_pose_obj(path, [
        (rg, c, f, (f * sp - (n - 1) * sp / 2.0, 0.0, row_z), yaw_deg)
        for f in range(n)])


def phase_offset(species, npc_id):
    """Where in the cycle this resident is. One float, and the reason a corridor
    of 40 people is a crowd rather than a chorus line."""
    return _u(f"{species}:{npc_id}", "gait_phase")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(out=print):
    c = calibration()
    st = station_gravity()
    out("=" * 78)
    out("NPC ANIMATION -- skeleton, clips, and a gait that reads the deck")
    out("=" * 78)
    out("")
    out("CALIBRATION (authority 5; the 1.0 g anchor is authority 1 -- the schema "
        "solved")
    out("the rotation rate from 'show depicts normal gait' at the drum floor)")
    for k, v in CAL.items():
        out(f"  {k:24s} {v}")
    out("  derived:")
    for k, v in c.items():
        out(f"    {k:22s} {v:.6f}")
    out(f"  walk/run transition assumed at Fr = {FR_RUN}; the MECHANICAL ceiling")
    out(f"  is Fr = 1 and is derived: v_max = sqrt(gL) = "
        f"{max_walk_speed(G0, c['leg_length_m']):.2f} m/s at 1 g")
    out(f"  duty factor reaches 0.5 only at Fr = {froude_at_duty(0.5):.3f}, which "
        f"is past the")
    out("  run transition -- so NO WALK IN THIS STATION HAS AN AERIAL PHASE, and "
        "that is")
    out("  a derived result rather than an assumption")
    out("")
    out(f"THE STATION ({st['n_decks']} decks, {st['rpm']:.4f} rpm)")
    out(f"  habitable gravity   {st['habitat_g'][0]:.4f} - {st['habitat_g'][1]:.4f} g")
    out(f"  plant decks         {st['plant_g'][0]:.4f} - {st['plant_g'][1]:.4f} g "
        f"(Downbelow lives here)")
    out(f"  below the walk model ({WALK_G_MIN} g): decks in "
        f"{', '.join(st['below_walk_min'])}")
    out("")
    out("  SELF-SELECTED WALK, by gravity (leg length held at the human nominal)")
    out(f"  {'g':>8}  {'speed':>7}  {'stride':>7}  {'cadence':>8}  {'duty':>6}  "
        f"{'swing':>6}")
    for gg in (0.31, 0.50, 0.76, 1.00, 1.2462, 1.4462, 1.6933):
        r = gait(gg * G0, c["leg_length_m"])
        out(f"  {gg:8.4f}  {r['speed_ms']:7.3f}  {r['stride_m']:7.3f}  "
            f"{r['cadence_spm']:8.1f}  {r['duty']:6.3f}  {r['swing_s']:6.3f}")
    out("  Stride is INVARIANT and cadence goes as sqrt(g): that is dynamic")
    out("  similarity, and it is why one clip ladder covers every deck.")
    out("")
    out("  COMMANDED 1.0 m/s -- the same person, the same errand, three decks")
    out(f"  {'g':>8}  {'stride':>7}  {'cadence':>8}  {'duty':>6}  {'Fr':>6}")
    for gg in (0.31, 1.00, 1.6933):
        r = gait(gg * G0, c["leg_length_m"], 1.0)
        out(f"  {gg:8.4f}  {r['stride_m']:7.3f}  {r['cadence_spm']:8.1f}  "
            f"{r['duty']:6.3f}  {r['froude']:6.3f}")
    out("  Now stride is the visible term and it runs the other way. Both are the")
    out("  same two equations.")
    out("")
    cr = coriolis_report()
    out("CORIOLIS at 1.79 rpm")
    out(f"  walking ALONG the axis   {cr['tangential_coriolis_ms2'] * 0:.6f} m/s^2 "
        f"-- exactly zero (v parallel to omega)")
    out(f"  walking AROUND the drum  {cr['tangential_coriolis_ms2']:.4f} m/s^2 = "
        f"{cr['tangential_fraction_of_g'] * 100:.2f}% of local weight at "
        f"{cr['walk_speed_ms']:.2f} m/s")
    out(f"  cadence spinward {cr['cadence_spinward_spm']:.1f} vs antispinward "
        f"{cr['cadence_antispinward_spm']:.1f} steps/min "
        f"({cr['cadence_split_pct']:+.2f}%)")
    out(f"  reaches 10% of local weight at {cr['speed_for_10pct_g']:.2f} m/s -- "
        f"a run; and a full g at")
    out(f"  {cr['speed_for_full_g']:.1f} m/s, which is exactly half the floor "
        f"speed")
    out(f"  the walk's own bob throws you sideways by "
        f"{cr['bob_lateral_sway_m'] * 1000:.2f} mm. It is not animatable.")
    out(f"  VERDICT: {cr['verdict']}")
    h1, h2 = cr["hop_drum"], cr["hop_light_deck_same_effort"]
    out(f"  a 0.20 m hop at 1.00 g lands {h1['spinward_m'] * 100:.1f} cm spinward "
        f"after {h1['flight_s']:.2f} s")
    out(f"  the same effort at {h2['g']:.2f} g goes {h2['height_m']:.2f} m up, "
        f"hangs {h2['flight_s']:.2f} s and lands {h2['spinward_m'] * 100:.1f} cm "
        f"spinward")
    out("")
    out("CURVED FLOORS -- every deck is a ring, so a stride is a chord")
    for r_m, lab in ((st["floor_radius_m"], "drum floor"),
                     (211.6, "Blue outer"), (33.87, "Yellow innermost")):
        e = floor_curvature_error(r_m, CAL["stride_m"])
        out(f"  r = {r_m:7.2f} m ({lab:16s})  sagitta over one stride "
            f"{e * 1000:6.3f} mm")
    out("  Re-anchor the root at each footfall and this is zero; author one "
        "stride flat")
    out("  and the innermost habitable ring mis-plants the foot by 7.8 mm.")
    out("")
    lad = froude_ladder()
    out(f"LADDER  {lad['rungs']} rungs, worst blend error "
        f"{lad['blend_error_m'] * 1000:.2f} mm, honest from "
        f"{lad['honest_from_m']} m")
    out(f"  {lad['criterion']}")
    cost = cost_report()
    out("")
    out("COST")
    out(f"  bones: " + ", ".join(f"{k} {v['bones']}"
                                 for k, v in cost["per_plan"].items()))
    out(f"  keys per clip {cost['keys_per_clip']} (derived by temporal_ladder)")
    out(f"  dataset for all 15 species  {cost['dataset_mb']:.3f} MB")
    out(f"  per-NPC runtime state       {cost['per_npc_runtime_bytes']} bytes "
        f"(a phase and a rate)")
    out(f"  bone palettes for {cost['full_agents']} full + "
        f"{cost['crowd_agents']} crowd agents  "
        f"{cost['bone_palette_mb']:.3f} MB")
    out(f"  triangles added {cost['triangles_added']}, draw calls added "
        f"{cost['draw_calls_added']}")
    out("  update-rate LOD, derived from the same decimation measurement:")
    for t in cost["update_tiers"]:
        out(f"    {t['band']:5s} {t['from_m']:5.1f}-{t['to_m']:5.1f} m  "
            f"{t['keys']:3d} keys  {t['hz_at_1g']:5.1f} Hz  "
            f"error {t['error_m'] * 1000:.1f} mm")
    out("")
    return True


# ===========================================================================
#  RIGID PIECES -- how a baked body is animated by an engine that cannot skin
# ===========================================================================
# THE RUNTIME CANNOT SKIN THESE BODIES, and that is a property of how they get
# to the engine rather than a limitation of Godot. `populace.py` bakes a person
# into the room's merged mesh in world space -- that is what makes 1,400 of them
# affordable -- so what arrives is triangles with no skeleton and no weights.
# `godot/scripts/npc.gd` already exploits the one thing that survives: each of
# `body.py`'s parts is its own MeshInstance3D, so a per-part RIGID transform can
# be applied at runtime, which is how an inhabitant turns to look at the player.
#
# THE OBVIOUS EXTENSION FAILS, AND BY HOW MUCH IS THE POINT. Driving each of the
# twelve parts by a rigid transform fitted to its posed self gives a walk whose
# worst vertex is **145 mm** out -- the knee, because `npc_skin_leg` is ONE part
# spanning hip to ankle and a rigid body cannot bend in the middle. 145 mm on a
# 0.98 m leg is a visible kink at any distance a person is worth animating at.
#
# SPLITTING EACH PART AT ITS DOMINANT BONE closes it to **14 mm**, measured over
# all eight phases of a walk, for **19 pieces** on a human. That is the whole
# idea: the binding already assigns every vertex a weighted set of bones, so
# grouping by the heaviest one cuts each part exactly where it bends, and each
# piece is then rigid to within the skin blend at the seam. `_selftest` asserts
# both numbers and the 10x between them, because the second is only interesting
# against the first.
#
# The cost is a table of 19 x frames x (R, t), per species and LOD -- shared by
# every person of that species, since the pieces are topological. Not per
# resident: a gait varies with leg length, but the FIT does not, and 1,400
# per-resident tracks is a megabyte where one per species is a kilobyte.
def rigid_pieces(species: str, npc_id: str = NOMINAL, lod: int = 0):
    """Split this figure's parts at the bone each vertex is mostly driven by.

    Returns `((piece_name, part_index, vertex_indices, bone_index), ...)`, in a
    stable order: part order first, then bone index, so the same figure gives
    the same list on every machine.
    """
    rg = rig(species, npc_id, lod)
    out = []
    for pi, ringw, runs in rg.binding:
        name = rg.parts[pi][0]
        dom = {}
        for r, (a, b) in enumerate(runs):
            heavy = max(ringw[r], key=lambda bw: bw[1])[0]
            dom.setdefault(heavy, []).extend(range(a, b))
        for bone in sorted(dom):
            out.append((f"{name}__{rg.skel.bones[bone].name}", pi,
                        tuple(dom[bone]), bone))
    return tuple(out)


def _kabsch(src, dst):
    """Best-fit rotation and translation taking `src` onto `dst`.

    Kabsch, in plain arithmetic rather than through numpy: this module has no
    numpy dependency and adding one for a 3x3 SVD would be the tail wagging the
    dog. The 3x3 SVD is done by eigen-decomposing `H^T H` with the closed-form
    symmetric-matrix Jacobi sweep already used for `mat_to_quat`'s cousin.
    Returns `(R, t, rms_m, max_m)`.
    """
    n = max(1, len(src))
    cs = [sum(p[i] for p in src) / n for i in range(3)]
    cd = [sum(p[i] for p in dst) / n for i in range(3)]
    H = [[0.0] * 3 for _ in range(3)]
    for a, b in zip(src, dst):
        for i in range(3):
            for j in range(3):
                H[i][j] += (a[i] - cs[i]) * (b[j] - cd[j])
    R = _polar(H)
    t = _sub(cd, _mv(R, cs))
    worst = 0.0
    acc = 0.0
    for a, b in zip(src, dst):
        d = _sub(_add(_mv(R, a), t), b)
        e = _norm(d)
        worst = max(worst, e)
        acc += e * e
    return R, t, math.sqrt(acc / n), worst


def _polar(H, iters=64):
    """The rotation factor of `H`, by Newton's polar-decomposition iteration.

    `X <- (X + (X^-1)^T) / 2` converges quadratically to the orthogonal factor
    of a non-singular matrix, and needs only a 3x3 inverse -- no SVD, no numpy.
    Kabsch wants the rotation taking src onto dst, which is the polar factor of
    `H^T`, so the transpose is taken here rather than at every call site. If H
    is singular -- a degenerate piece, all vertices collinear -- the iteration
    is skipped and identity returned, which a caller sees as a large residual
    rather than as a silent NaN.
    """
    X = _mt(H)
    for _ in range(iters):
        inv = _inv3(X)
        if inv is None:
            return IDENT
        nxt = tuple(tuple((X[i][j] + inv[j][i]) / 2.0 for j in range(3))
                    for i in range(3))
        if max(abs(nxt[i][j] - X[i][j])
               for i in range(3) for j in range(3)) < 1e-15:
            X = nxt
            break
        X = nxt
    # A reflection is not a rotation. It can only arise from a degenerate fit,
    # and returning one would mirror a limb.
    return X if _det(X) > 0.0 else IDENT


def _inv3(m):
    d = _det(m)
    if abs(d) < 1e-18:
        return None
    c = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            a, b = [k for k in range(3) if k != i], [k for k in range(3)
                                                     if k != j]
            minor = (m[a[0]][b[0]] * m[a[1]][b[1]]
                     - m[a[0]][b[1]] * m[a[1]][b[0]])
            c[j][i] = ((-1.0) ** (i + j)) * minor / d
    return tuple(tuple(r) for r in c)


def rigid_track(clip: "Clip", species: str, npc_id: str = NOMINAL,
                lod: int = 0):
    """The clip as per-piece rigid transforms, one set per frame.

    Returns `{"pieces": [name...], "frames": [[ (R, t) per piece ]...],
    "rms_m": float, "max_m": float}` -- everything an engine needs to play this
    clip on a mesh it cannot skin, plus the error it is accepting, stated so a
    caller cannot use it without seeing it.
    """
    rg = rig(species, npc_id, lod)
    pieces = rigid_pieces(species, npc_id, lod)
    bind = [list(v) for _n, v, _t in rg.parts]
    frames, worst, acc, cnt = [], 0.0, 0.0, 0
    for f in range(clip.frames):
        _w, mats = clip.pose(rg.skel, f)
        posed = apply_pose(rg, mats)
        row = []
        for _name, pi, idx, _bone in pieces:
            src = [bind[pi][i] for i in idx]
            dst = [posed[pi][1][i] for i in idx]
            R, t, rms, mx = _kabsch(src, dst)
            worst = max(worst, mx)
            acc += rms * rms * len(idx)
            cnt += len(idx)
            row.append((R, t))
        frames.append(row)
    return {"pieces": [p[0] for p in pieces], "frames": frames,
            "rms_m": math.sqrt(acc / max(1, cnt)), "max_m": worst,
            "duration_s": clip.duration_s, "loop": clip.loop,
            "name": clip.name}


def whole_part_error(clip: "Clip", species: str, npc_id: str = NOMINAL,
                     lod: int = 0):
    """The same fit WITHOUT the split, so the split's value can be measured.

    The negative control for `rigid_track`, and the reason it is a function
    rather than a comment: "splitting at the dominant bone helps" is a claim,
    and a claim about a number needs the number it is against.
    """
    rg = rig(species, npc_id, lod)
    bind = [list(v) for _n, v, _t in rg.parts]
    worst = 0.0
    for f in range(clip.frames):
        _w, mats = clip.pose(rg.skel, f)
        posed = apply_pose(rg, mats)
        for pi in range(len(rg.parts)):
            _R, _t, _rms, mx = _kabsch(bind[pi], list(posed[pi][1]))
            worst = max(worst, mx)
    return worst


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
# The band a walk's cadence must stay inside for every species on every deck the
# walk model claims. EXTRAPOLATED and deliberately generous -- 50 is a dawdle and
# 200 is a race-walk -- because its job is to catch a broken exponent or a
# mis-calibrated constant, not to encode a preference. The measured extremes come
# out at 61 and 170 and the test prints them.
CADENCE_BAND = (50.0, 200.0)
# A foot may slide this far in one frame while it is on the deck. DERIVED:
# body.honest_from_m(0.001) = 1.03 m, so a 1 mm slide is inside the pixel budget
# from a metre away, which is closer than a player stands to another person's
# feet. The measurement is conservative -- it counts vertices up to CONTACT_EPS_M
# above the deck as "in contact", and those are legitimately rising.
SLIP_MAX_M = 0.001


def _selftest():
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL: {label}")

    c = calibration()
    L = c["leg_length_m"]

    # -- determinism -------------------------------------------------------
    check(abs(_u("narn:r-0001", "stature") - body._u("narn:r-0001", "stature"))
          < 1e-15, "animation._u matches body._u byte for byte")
    try:
        import schedule as sched                            # noqa: PLC0415
        check(abs(sched._u("x", "y") - _u("x", "y")) < 1e-15,
              "and schedule._u too, so one id gives one person")
    except ImportError as exc:                              # noqa: BLE001
        check(False, f"schedule.py not importable: {exc}")
    import ast                                              # noqa: PLC0415
    tree = ast.parse(open(os.path.abspath(__file__)).read())
    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            banned += [a.name for a in node.names
                       if a.name.split(".")[0] == "random"]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "random"):
            banned.append(node.module)
        elif isinstance(node, ast.Attribute) and node.attr == "__hash__":
            banned.append("__hash__")
    check(not banned, f"no `random` and no `__hash__` anywhere ({banned})")
    check(any(isinstance(n, ast.Attribute) and n.attr == "blake2b"
              for n in ast.walk(tree)), "and blake2b is what it uses instead")
    c1 = walk_clip("human", "det-1", G0, frames=16)
    c2 = walk_clip("human", "det-1", G0, frames=16)
    check(c1.tracks == c2.tracks and c1.root == c2.root,
          "the same resident's walk bakes byte for byte twice")
    check(walk_clip("narn", "det-2", G0, frames=16).tracks != c1.tracks,
          "two residents do not bake the same clip")
    # Phase spread. 500 agents on one clip in lockstep is the crowd bug this
    # exists to prevent, so the distribution is checked, not the mechanism.
    bins = [0] * 10
    n_ids = 2000
    for i in range(n_ids):
        bins[min(9, int(phase_offset("human", f"p-{i}") * 10))] += 1
    check(all(abs(b - n_ids / 10) < 0.25 * n_ids / 10 for b in bins),
          f"gait phase is spread over residents, not clustered ({bins})")

    # -- the contract with body.py ----------------------------------------
    for key in sorted(body.SPECIES):
        rg = rig(key, "contract", 0)
        sk = rg.skel
        w = fk(sk, {}, (0.0, 0.0, 0.0))
        posed = apply_pose(rg, skin_matrices(sk, w))
        err = max(max(abs(a - b) for a, b in zip(p, q))
                  for (_n, vs, _t), (_n2, vs2, _t2) in zip(posed, rg.parts)
                  for p, q in zip(vs, vs2))
        check(err < 1e-9,
              f"{key}: the rest pose reproduces the bind mesh ({err:.2e} m)")
        check(sum(1 for b in sk.bones if b.parent < 0) == 1,
              f"{key}: exactly one root bone")
        check(all(b.parent < i for i, b in enumerate(sk.bones)),
              f"{key}: bones are in parent-before-child order")
        check(sum(len(t) for _n, _v, t in posed)
              == sum(len(t) for _n, _v, t in rg.parts),
              f"{key}: posing emits no geometry")
        if sk.plan == "column":
            continue
        # Joints against the mesh body.py actually built, by a DIFFERENT route
        # from the one that placed them. `_skeleton` reads ring centres; this
        # reads ray-cast containment and vertex extrema, so a wrong ring
        # partition, a swapped side or a missing stoop fails here and a shared
        # bug cannot pass both.
        legp = "leg" if sk.plan == "humanoid" else "suit_leg"
        armp = "arm" if sk.plan == "humanoid" else "suit_arm"
        lv, lt = next((v, t) for n, v, t in rg.parts
                      if n == legp and _side_of(v) == "r")
        av, at = next((v, t) for n, v, t in rg.parts
                      if n == armp and _side_of(v) == "r")
        hv, ht = next((v, t) for n, v, t in rg.parts if n == "head"
                      or n == "gaim_helmet")
        # A joint sits ON the cap of the loft it drives, so testing the joint
        # itself asks the ray caster about a boundary point. Step 8% down the
        # bone instead, which is unambiguously interior.
        for jname, jto, (pv, pt), pn in (
                ("hip_r", "knee_r", (lv, lt), legp),
                ("knee_r", "ankle_r", (lv, lt), legp),
                ("shoulder_r", "elbow_r", (av, at), armp),
                ("elbow_r", "wrist_r", (av, at), armp)):
            p = _add(sk.head(jname), _scale(_sub(sk.head(jto), sk.head(jname)),
                                            0.08))
            check(body.contains(pv, pt, p),
                  f"{key}: the {jname} joint is inside the {pn} it drives")
        check(body.contains(hv, ht, sk.head("head")),
              f"{key}: the head joint is inside the head")
        check(not body.contains(lv, lt, _add(sk.head("hip_r"), (0.0, 0.5, 0.0))),
              f"{key}: and containment can say no -- half a metre above the hip "
              f"is not inside the leg")
        # Exact extremum comparison, on the UNSTOOPED build. The stoop tilts a
        # ring so its topmost VERTEX stops being its centre; suppressing it makes
        # the comparison exact instead of tolerant, and the stoop gets its own
        # test below.
        p0 = tuple((n, tuple(v), tuple(t)) for n, v, t in
                   body._PLANS[rg.sp.plan](replace(rg.ind, stoop_deg=0.0), rg.sp,
                                           seg=64, ring_stride=1,
                                           features="all").parts)
        sk0 = _skeleton(replace(rg.ind, stoop_deg=0.0), rg.sp, p0, p0)
        lv0 = next(v for n, v, _t in p0 if n == legp and _side_of(v) == "r")
        av0 = next(v for n, v, _t in p0 if n == armp and _side_of(v) == "r")
        check(abs(max(v[1] for v in lv0) - sk0.head("hip_r")[1]) < 1e-9,
              f"{key}: the hip bone is at the top of the leg part")
        check(abs(min(v[1] for v in lv0) - sk0.head("ankle_r")[1]) < 1e-9,
              f"{key}: the ankle bone is at the bottom of it")
        check(abs(max(v[1] for v in av0) - sk0.head("shoulder_r")[1]) < 1e-9,
              f"{key}: the shoulder bone is at the top of the arm part")
        check(abs(min(v[1] for v in av0) - sk0.head("wrist_r")[1]) < 1e-9,
              f"{key}: the wrist bone is at the bottom of it")
        # The stoop, exactly: the un-bent head joint is on the midline by
        # construction (z = 0), so any forward z is the bend and nothing else.
        check(abs(sk0.head("head")[2]) < 1e-12,
              f"{key}: the unstooped head joint is on the midline")
        if rg.ind.stoop_deg > 0.05:
            # Strictly greater than zero is the exact test -- a skeleton that
            # skipped `_bend` would sit at exactly the 0.0 asserted above -- and
            # a species with a real stoop has to move a real distance.
            z = sk.head("head")[2]
            check(z > 0.0, f"{key}: the stoop carried the head joint forward "
                           f"({z * 1000:.2f} mm at {rg.ind.stoop_deg:.2f} deg)")
            if rg.ind.stoop_deg > 1.0:
                check(z > 0.004,
                      f"{key}: and by a visible amount ({z * 1000:.1f} mm at "
                      f"{rg.ind.stoop_deg:.2f} deg)")
        kf = (_norm(_sub(sk.head("hip_r"), sk.head("knee_r")))
              / _norm(_sub(sk.head("hip_r"), sk.head("ankle_r"))))
        check(0.50 <= kf <= 0.65,
              f"{key}: the knee sits mid-thigh-to-ankle ({kf:.3f})")
        check(abs(_norm(_sub(sk.head("hip_r"), sk.head("knee_r")))
                  + _norm(_sub(sk.head("knee_r"), sk.head("ankle_r")))
                  - sk.reach_m) < 1e-9,
              f"{key}: thigh + shin = the leg's reach (the IK's assumption)")

    # -- skinning ----------------------------------------------------------
    rg = rig("human", "skin-a", 0)
    for pi, ringw, runs in rg.binding:
        name = rg.parts[pi][0]
        check(sum(b - a for a, b in runs) == len(rg.parts[pi][1]),
              f"{name}: the ring partition covers every vertex exactly once")
        for ring in ringw:
            check(abs(sum(w for _b, w in ring) - 1.0) < 1e-12,
                  f"{name}: ring weights sum to 1")
            check(len(ring) <= MAX_INFLUENCES,
                  f"{name}: at most {MAX_INFLUENCES} influences ({len(ring)})")
    rb = rig("human", "skin-b", 0)
    worst_w = 0.0
    for (_p1, w1, _r1), (_p2, w2, _r2) in zip(rg.binding, rb.binding):
        for r1, r2 in zip(w1, w2):
            d1, d2 = dict(r1), dict(r2)
            for k in set(d1) | set(d2):
                worst_w = max(worst_w, abs(d1.get(k, 0.0) - d2.get(k, 0.0)))
    check(worst_w < 0.05,
          f"the binding is the same table for two residents ({worst_w:.4f}) -- "
          f"so it is stored once per species, not per NPC. Not exactly equal: "
          f"per-individual shoulder jitter moves the arm chain's direction a "
          f"little, and the residual is what this bounds")

    # -- winding, under animation (CLAUDE.md hard rule 5) ------------------
    clip = walk_clip("human", "wind", G0, frames=16)
    rgw = rig("human", "wind", 0)
    worst_vol, worst_det = 1e18, 1e18
    for f in range(clip.frames):
        _w, mats = clip.pose(rgw.skel, f)
        for R, _t in mats:
            worst_det = min(worst_det, _det(R))
        for _n, vs, ts in apply_pose(rgw, mats):
            worst_vol = min(worst_vol, body.signed_volume(vs, ts))
    check(worst_vol > 0.0,
          f"every part stays wound outward in every frame ({worst_vol:.2e})")
    check(abs(worst_det - 1.0) < 1e-9,
          f"every skinning matrix is a rotation, not a mirror ({worst_det:.9f})")

    # -- the gait, as physics ---------------------------------------------
    check(abs(froude(max_walk_speed(G0, L), G0, L) - 1.0) < 1e-12,
          "max_walk_speed is exactly Fr = 1")
    check(abs(gait(G0, L)["froude"] - c["froude_preferred"]) < 1e-12,
          "the self-selected speed reproduces the calibration Froude number")
    # sqrt(g) scaling, exactly
    r1, r2 = gait(0.4 * G0, L), gait(1.6 * G0, L)
    check(abs(r2["speed_ms"] / r1["speed_ms"] - 2.0) < 1e-12,
          "self-selected speed goes as sqrt(g) exactly")
    check(abs(r2["cadence_spm"] / r1["cadence_spm"] - 2.0) < 1e-12,
          "and so does cadence")
    check(abs(r2["stride_m"] - r1["stride_m"]) < 1e-12,
          "while stride is invariant -- dynamic similarity, and the reason one "
          "clip ladder covers 217 decks")
    # duty is a function of Fr alone: two different (g, L) at one Fr
    d1 = gait(0.5 * G0, 1.2, math.sqrt(0.3 * 0.5 * G0 * 1.2))["duty"]
    d2 = gait(1.5 * G0, 0.8, math.sqrt(0.3 * 1.5 * G0 * 0.8))["duty"]
    check(abs(d1 - d2) < 1e-12 and abs(d1 - duty_at_froude(0.3)) < 1e-12,
          f"duty factor is a function of Froude number alone ({d1:.9f} vs "
          f"{d2:.9f})")
    # LAMBDA_EXP is the model's one free shape and monotonicity alone does not
    # pin it -- every positive exponent is monotone. What pins it is that a
    # change of speed has to show in BOTH terms: at 0 the stride would not
    # respond to hurrying and at 0.5 the cadence would not, and either reads as
    # wrong at a glance. Doubling the speed must move each by at least a fifth.
    slow = gait(G0, L, 0.7)
    fast = gait(G0, L, 1.4)
    check(fast["stride_m"] / slow["stride_m"] - 1.0 > 0.20
          and fast["cadence_spm"] / slow["cadence_spm"] - 1.0 > 0.20,
          f"hurrying lengthens the stride AND raises the cadence "
          f"(+{100 * (fast['stride_m'] / slow['stride_m'] - 1):.0f}% stride, "
          f"+{100 * (fast['cadence_spm'] / slow['cadence_spm'] - 1):.0f}% "
          f"cadence) -- which is what fixes LAMBDA_EXP")
    # MONOTONICITY, in the right direction, at a commanded speed, swept over the
    # station's own gravity range rather than at two convenient points.
    gs = [0.31 + i * (1.6933 - 0.31) / 40 for i in range(41)]
    rows = [gait(g * G0, L, 1.1) for g in gs]
    check(all(a["stride_m"] > b["stride_m"] for a, b in zip(rows, rows[1:])),
          "stride falls monotonically as gravity rises (commanded speed)")
    check(all(a["cadence_spm"] < b["cadence_spm"] for a, b in zip(rows, rows[1:])),
          "cadence rises monotonically as gravity rises")
    check(all(a["duty"] < b["duty"] for a, b in zip(rows, rows[1:])),
          "duty factor rises with gravity: more time on the ground when heavy")
    check(all(a["swing_s"] > b["swing_s"] for a, b in zip(rows, rows[1:])),
          "swing time falls with gravity: the leg is returned by gravity")
    sel = [gait(g * G0, L) for g in gs]
    check(all(a["speed_ms"] < b["speed_ms"] for a, b in zip(sel, sel[1:])),
          "self-selected speed rises monotonically with gravity")
    # cadence stays human, over every species and every walkable deck
    st = station_gravity()
    lo_g, hi_g = st["walkable_g"]
    lo_c, hi_c = 1e9, 0.0
    for key in body.SPECIES:
        sk = rig(key, "cad", 0).skel
        if sk.plan == "column":
            continue
        for g in (lo_g, hi_g):
            cd = gait(g * G0, sk.leg_length_m)["cadence_spm"]
            lo_c, hi_c = min(lo_c, cd), max(hi_c, cd)
    check(CADENCE_BAND[0] <= lo_c and hi_c <= CADENCE_BAND[1],
          f"cadence stays in the human band over every species and every "
          f"walkable deck ({lo_c:.1f}-{hi_c:.1f} vs {CADENCE_BAND})")
    check(hi_c / lo_c > 1.8,
          f"and the station's own gravity spread is worth having: {hi_c / lo_c:.2f}x "
          f"between the lightest and heaviest walkable deck")
    # no aerial phase anywhere -- derived, then checked over the whole envelope
    check(froude_at_duty(0.5) > FR_RUN,
          f"a walk loses double support only at Fr {froude_at_duty(0.5):.3f}, "
          f"past the run transition {FR_RUN}")
    worst_duty = 1.0
    for g in gs:
        for fr in (0.02, 0.1, 0.25, FR_RUN * 0.999):
            worst_duty = min(worst_duty,
                             gait(g * G0, L, math.sqrt(fr * g * G0 * L))["duty"])
    check(worst_duty > 0.5,
          f"no walk anywhere in the station has an aerial phase "
          f"(worst duty {worst_duty:.4f})")
    # the refusals, both directions, so neither is vacuous
    check(gait((WALK_G_MIN - 0.01) * G0, L)["below_walk_gravity"]
          and not gait((WALK_G_MIN + 0.01) * G0, L)["below_walk_gravity"],
          "the walk model flags gravity below WALK_G_MIN and not above it")
    try:
        gait(G0, L, math.sqrt((FR_RUN + 0.05) * G0 * L))
        check(False, "gait() should refuse a speed past the run transition")
    except ValueError:
        check(True, "gait() refuses a speed past the run transition")
    check(gait(G0, L, math.sqrt((FR_RUN - 0.05) * G0 * L))["kind"] == "walk",
          "and accepts one just below it")
    try:
        walk_clip("vorlon", "kosh", G0, frames=8)
        check(False, "the column plan should refuse to walk")
    except ValueError:
        check(True, "Kosh has no walk: the column plan refuses one")

    # -- the clips ---------------------------------------------------------
    worst_slip, worst_clear, worst_ext, worst_knee = 0.0, 1e9, 0.0, 1e9
    for key in sorted(body.SPECIES):
        rgx = rig(key, "clip", 0)
        if rgx.skel.plan == "column":
            continue
        ck = walk_clip(key, "clip", G0, frames=24)
        s = contact_slip(rgx, ck)["max_slip_m"]
        cl = swing_clearance(rgx, ck)
        worst_slip, worst_clear = max(worst_slip, s), min(worst_clear, cl)
        worst_ext = max(worst_ext, ck.meta["max_extension"])
        worst_knee = min(worst_knee, ck.meta["min_knee_forward_m"])
        check(ck.meta["ik_clamped"] == 0,
              f"{key}: the derived stride never over-extends the leg")
    check(worst_slip < SLIP_MAX_M,
          f"no foot slides while it is on the deck, any species "
          f"({worst_slip * 1000:.3f} mm vs {SLIP_MAX_M * 1000:.1f} mm)")
    check(worst_clear >= -1e-9,
          f"no foot goes through the deck ({worst_clear * 1000:.3f} mm)")
    check(worst_ext <= K_EXT + 1e-9,
          f"the stance leg is never locked straight ({worst_ext:.4f})")
    check(worst_knee > 0.0,
          f"the knee always bends forward ({worst_knee * 1000:.1f} mm)")
    # LOD sweep: the same clip has to work on every mesh level
    for lod in range(len(body.lod_chain()) - 1):
        rgl = rig("human", "lodclip", lod)
        cl = walk_clip("human", "lodclip", G0, frames=16, lod=lod)
        check(contact_slip(rgl, cl)["max_slip_m"] < SLIP_MAX_M
              and swing_clearance(rgl, cl) >= -1e-9,
              f"lod{lod}: the walk still plants its feet")
    # standing clips: the feet must not drift at all
    for mk in (idle_clip, talk_clip, sit_clip):
        cl = mk("human", "stand", G0, frames=24)
        s = contact_slip(rig("human", "stand", 0), cl)["max_slip_m"]
        check(s < 1e-9, f"{cl.name}: planted feet do not drift ({s:.2e} m)")
        check(all(abs(r[2]) < 1e-12 for r in cl.root),
              f"{cl.name}: a standing clip has no root motion")
    # loop closure: the wrap must not be a bigger step than any other frame
    ck = walk_clip("human", "loop", G0, frames=24)
    rgl = rig("human", "loop", 0)
    steps = []
    for f in range(ck.frames):
        a = ck.pose(rgl.skel, f)[0]
        b = ck.pose(rgl.skel, (f + 1) % ck.frames)[0]
        adv = ck.meta["root_advance_m"] if f == ck.frames - 1 else 0.0
        steps.append(max(_norm(_sub(_add(q[1], (0.0, 0.0, adv)), p[1]))
                         for p, q in zip(a, b)))
    check(steps[-1] <= 1.5 * sorted(steps)[len(steps) // 2],
          f"the walk loops without a jump at the wrap ({steps[-1]:.4f} vs median "
          f"{sorted(steps)[len(steps) // 2]:.4f})")
    # interpenetration must not be made worse than the bind pose
    ip = interpenetration(rig("human", "pen", 0),
                          walk_clip("human", "pen", G0, frames=24))
    # Tolerance of two vertices, and the reason is structural: the foot and the
    # leg are two shells that already share the ankle by design, so pitching the
    # foot moves a vertex or two across a boundary that was never a surface. The
    # hand/thigh term is the one that mattered and it has to be <= 0.
    check(ip["worse_than_rest"]["hand_in_leg"] <= 0
          and ip["worse_than_rest"]["hand_in_torso"] <= 0
          and ip["worse_than_rest"]["foot_in_leg"] <= 2,
          f"the walk adds no interpenetration the bind pose does not have "
          f"({ip['worse_than_rest']})")
    check(ip["rest"]["hand_in_leg"] > 0,
          "and the measurement can see interpenetration at all: body.py's bind "
          f"pose already has {ip['rest']['hand_in_leg']} hand vertices in a "
          f"thigh")

    # -- sitting -----------------------------------------------------------
    sh = seat_height("human")
    try:
        sys.path.insert(0, _STATION)
        import zocalo                                       # noqa: PLC0415
        import council_chamber as cc                        # noqa: PLC0415
        for mod, val in (("zocalo", zocalo.CHAIR_SEAT_H_M),
                         ("council_chamber", cc.CHAIR_SEAT_H_M)):
            check(abs(sh - val) < 0.04,
                  f"the derived seat height {sh:.3f} m agrees with {mod}'s "
                  f"independently authored {val} m")
    except ImportError as exc:                              # noqa: BLE001
        check(False, f"furniture modules not importable for the cross-check: {exc}")
    for key in ("human", "vree", "grome"):
        cl = sit_clip(key, "sit", G0, seat_h_m=0.45, frames=12)
        rgs = rig(key, "sit", 0)
        lowest = 1e9
        for f in range(cl.frames):
            _w, mats = cl.pose(rgs.skel, f)
            for name, vs, _t in apply_pose(rgs, mats):
                lowest = min(lowest, min(v[1] for v in vs) - rgs.skel.ground_y)
        check(lowest >= -1e-9,
              f"{key}: sitting on a 0.45 m seat puts nothing through the deck "
              f"({lowest * 1000:.2f} mm)")
    check(sit_clip("vree", "sit", G0, seat_h_m=0.60, frames=8)
          .meta["feet_dangle_m"] > 0.0,
          "a short species on a tall seat dangles its feet rather than "
          "stretching to the floor")
    check(sit_clip("grome", "sit", G0, seat_h_m=0.60, frames=8)
          .meta["feet_dangle_m"] == 0.0,
          "and a tall one does not")

    # -- Coriolis ----------------------------------------------------------
    cr = coriolis_report()
    check(cr["axial_is_exactly_zero"],
          "walking along the drum axis produces exactly zero Coriolis")
    check(cr["linear_term_agrees"],
          "the tangential Coriolis term equals the linear term of "
          "rotating_frame.apparent_weight_factor")
    check(0.04 < cr["tangential_fraction_of_g"] < 0.07,
          f"walking around the drum is a few percent of weight "
          f"({cr['tangential_fraction_of_g'] * 100:.2f}%)")
    check(cr["cadence_spinward_spm"] > cr["cadence_antispinward_spm"],
          "and a spinward walker steps faster than an antispinward one")
    check(cr["cadence_split_pct"] < 5.0,
          f"but by too little to see: {cr['cadence_split_pct']:.2f}%")
    check(cr["hop_light_deck_same_effort"]["spinward_m"]
          > 5.0 * cr["hop_drum"]["spinward_m"],
          "while the same hop on a light deck lands far further spinward -- "
          "v0^3/g^2 is the reason Coriolis shows in a jump and not in a walk")
    check(abs(floor_curvature_error(st["floor_radius_m"], CAL["stride_m"])
              - 0.000944) < 1e-5,
          "the drum floor's sagitta over one stride is 0.94 mm")
    check(floor_curvature_error(33.87, CAL["stride_m"])
          > 8.0 * floor_curvature_error(st["floor_radius_m"], CAL["stride_m"]),
          "and the innermost habitable ring is eight times worse")

    # -- ladder, tiers and export -----------------------------------------
    lad = froude_ladder()
    check(lad["honest_from_m"] <= LADDER_HONEST_FROM_M + 1e-9,
          f"the Froude ladder is honest from {lad['honest_from_m']} m")
    check(lad["rungs"] >= 3, f"and needs more than a couple of rungs "
                             f"({lad['rungs']})")
    hum = set(n for n, _p in PLAN_BONES["humanoid"])
    prev = hum
    for tier in ("full", "no_toes", "trunk"):
        cut = hum - set(BONE_TIER[tier] or ())
        check(cut <= prev, f"bone tier {tier} is a strict subset of the finer one")
        prev = cut
    tl = temporal_ladder()
    check(all(a["error_m"] > b["error_m"] for a, b in zip(tl, tl[1:])),
          "more keys is always less error (the temporal ladder is monotone)")
    # export round trip
    cl = walk_clip("human", "exp", G0, frames=8)
    d = clip_dict(cl, godot=True)
    check(json.dumps(d, sort_keys=True) == json.dumps(clip_dict(cl, godot=True),
                                                      sort_keys=True),
          "the exported clip serialises deterministically")
    q = cl.tracks["hip_r"][3]
    check(all(abs(a - b) < 1e-15 for a, b in
              zip(tuple(round(x, ROUND_Q) for x in q),
                  _to_godot_q(_to_godot_q(q)))),
          "the Godot frame transform is its own inverse, up to the export "
          "rounding")
    # What the export rounding costs, MEASURED on posed joints rather than
    # assumed from the number of decimal places.
    rgq = rig("human", "exp", 0)
    worst_q = 0.0
    for f in range(cl.frames):
        loc = {}
        for name, qs in cl.tracks.items():
            rq = tuple(round(x, ROUND_Q) for x in qs[f])
            n = math.sqrt(sum(x * x for x in rq))
            loc[rgq.skel.index[name]] = quat_to_mat(tuple(x / n for x in rq))
        wq = fk(rgq.skel, loc, tuple(round(x, ROUND_V) for x in cl.root[f]))
        wt = cl.pose(rgq.skel, f)[0]
        for i in range(len(rgq.skel.bones)):
            worst_q = max(worst_q, _norm(_sub(wq[i][1], wt[i][1])))
    check(worst_q < 1e-4,
          f"export rounding moves a joint by {worst_q * 1e6:.1f} microns, which "
          f"is {body.honest_from_m(worst_q) * 1000:.2f} mm of viewing distance")
    m = quat_to_mat(q)
    check(max(abs(a - b) for ra, rb in zip(m, quat_to_mat(mat_to_quat(m)))
              for a, b in zip(ra, rb)) < 1e-12,
          "quaternion and matrix round-trip to the same rotation")
    lk = look_at(rig("human", "look", 0).skel, 200.0, 0.0)
    check(lk["clamped"], "look_at clamps a request outside the human range")
    check(not look_at(rig("human", "look", 0).skel, 20.0, 0.0)["clamped"],
          "and does not clamp one inside it")

    # -- RIGID PIECES: what a runtime that cannot skin can do with this ----
    rc = walk_clip("human", NOMINAL, G0, frames=8, lod=4)
    trk = rigid_track(rc, "human", NOMINAL, 4)
    whole = whole_part_error(rc, "human", NOMINAL, 4)
    check(len(trk["pieces"]) == 19 and len(trk["frames"]) == 8,
          f"a human splits into 19 rigid pieces over 8 phases "
          f"({len(trk['pieces'])} x {len(trk['frames'])})")
    check(trk["max_m"] < 0.020,
          f"and a rigid piece follows the skinned pose to "
          f"{trk['max_m'] * 1000:.0f} mm at worst, {trk['rms_m'] * 1000:.1f} "
          "rms")
    # THE NEGATIVE CONTROL, and it is the whole reason for the split: driving
    # the twelve parts whole gives 145 mm at the knee, because `npc_skin_leg`
    # spans hip to ankle and a rigid body cannot bend in the middle.
    check(whole > 0.100 and whole > trk["max_m"] * 5.0,
          f"BREAK: WITHOUT the split the same fit is {whole * 1000:.0f} mm out "
          f"-- {whole / max(1e-9, trk['max_m']):.0f}x worse -- so the split is "
          "doing the work, not the fitter")
    # A ROTATION, NOT A REFLECTION. `_polar` returns identity rather than a
    # mirrored limb on a degenerate piece, and every fit here must be proper.
    check(all(_det(R) > 0.99 for row in trk["frames"] for R, _t in row),
          "every fitted transform is a proper rotation, not a reflection")
    # The pure-Python polar decomposition has to agree with an orthogonal
    # matrix's own inverse, or the fit is quietly a scale.
    _R0 = trk["frames"][2][13][0]
    _RtR = _mul(_mt(_R0), _R0)
    check(max(abs(_RtR[i][j] - (1.0 if i == j else 0.0))
              for i in range(3) for j in range(3)) < 1e-9,
          "...and orthogonal to 1e-9, so no piece is being scaled")
    # EVERY SPECIES, not just a human, because the split's quality is a
    # property of how `body.py` parts that plan. Measured at lod 4, which is
    # what `populace.corridor_lod` bakes a corridor at.
    worst_sp, worst_mm = None, 0.0
    for _sp in sorted(body.SPECIES):
        try:
            _c = walk_clip(_sp, NOMINAL, G0, frames=8, lod=4)
        except ValueError:
            continue                    # the column plan has no legs: glides
        _t = rigid_track(_c, _sp, NOMINAL, 4)
        if _t["max_m"] > worst_mm:
            worst_sp, worst_mm = _sp, _t["max_m"]
    check(worst_mm < 0.100,
          f"every walking species fits its rigid pieces under 100 mm; the "
          f"worst is {worst_sp} at {worst_mm * 1000:.0f} mm")
    # AND THE GAIM ARE THE WORST, WHICH IS A FINDING RATHER THAN A PASS. The
    # encounter-suit plan is rigid plates rather than a limbed body, so its
    # parts do not divide at a joint the way a humanoid's do -- 15 pieces
    # instead of 19, and 90 mm instead of 14. It is inside the bake distance
    # (90 mm at the 33 m `corridor_lod` picks for is a fifth of a pixel) and
    # visible at 6 m. Named here so a future session finds it already measured
    # rather than discovering a Gaim's shoulder tearing.
    check(worst_sp == "gaim",
          f"...and it is the encounter-suit plan that fits worst, not a "
          f"humanoid ({worst_sp})")

    # Every vertex is in exactly one piece: a piece the exporter drops is a
    # limb that does not move, and a vertex in two is a limb drawn twice.
    _rg = rig("human", NOMINAL, 4)
    for _pi in range(len(_rg.parts)):
        _seen = [i for nm, pi, idx, _b in rigid_pieces("human", NOMINAL, 4)
                 if pi == _pi for i in idx]
        check(sorted(_seen) == list(range(len(_rg.parts[_pi][1]))),
              f"part {_rg.parts[_pi][0]} is partitioned exactly once over its "
              f"pieces ({len(_seen)} of {len(_rg.parts[_pi][1])} vertices)")

    print(f"{ok}/{ok + fail} passed")
    return fail == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--obj", metavar="PATH")
    ap.add_argument("--clip", default="walk")
    ap.add_argument("--species", default="human")
    ap.add_argument("--npc-id", default="sheet")
    ap.add_argument("--g", type=float, default=1.0, help="gravity, in g")
    ap.add_argument("--speed", type=float, default=None, help="m/s; omit for "
                    "the self-selected speed at that gravity")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--lod", type=int, default=0)
    ap.add_argument("--emit", metavar="DIR")
    a = ap.parse_args()
    if a.report:
        report()
        return 0
    if a.emit:
        for p, n in emit(a.emit, lod=a.lod):
            print(f"{p}  {n:,} bytes")
        return 0
    if a.obj:
        g = a.g * G0
        mk = {"walk": lambda: walk_clip(a.species, a.npc_id, g, speed=a.speed,
                                        frames=a.frames, lod=a.lod,
                                        allow_run=True),
              "idle": lambda: idle_clip(a.species, a.npc_id, g,
                                        frames=a.frames, lod=a.lod),
              "talk": lambda: talk_clip(a.species, a.npc_id, g,
                                        frames=a.frames, lod=a.lod),
              "sit": lambda: sit_clip(a.species, a.npc_id, g, frames=a.frames,
                                      lod=a.lod),
              "glide": lambda: glide_clip(a.species, a.npc_id, g,
                                          frames=a.frames, lod=a.lod)}[a.clip]
        contact_sheet(a.obj, a.species, a.npc_id, g, n=a.frames, clip=mk(),
                      lod=a.lod)
        print(a.obj)
        return 0
    return 0 if _selftest() else 1


if __name__ == "__main__":
    sys.exit(main())


