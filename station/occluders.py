#!/usr/bin/env python3
"""Occlusion geometry: the surfaces that are allowed to HIDE other surfaces.

WHY THIS EXISTS, in the words of the gate that has been red for four sessions.
`station/budget.py` measures a standing frame on an assembled deck and reports
structure at 2.05x its allowance. Its own diagnosis, written into `Frustum`'s
docstring before this module was thought of:

    NO OCCLUSION IS APPLIED, AND THAT IS NOT AN APPROXIMATION -- it is what
    ships. `godot/` contains no `OccluderInstance3D` and no
    `use_occlusion_culling`, and `walk.gd` loads one `.glb` whole. Everything
    inside the frustum is submitted, vertex-shaded and rasterised whether a wall
    is in front of it or not. On a ring corridor that matters: the far side of
    the ring is inside the frustum from most standing positions.

and, on the pitch sweep it prints but does not gate:

    What closes this is an occluder on the corridor's own walls, not fewer
    props.

So the red was never a content bound. It is the cost of rendering a room you
are standing outside of, five hundred metres away, through two solid walls.

THE RULE, and it is the exact dual of `station/collision.py`'s:

    a COLLISION shell takes the NARROWEST, HIGHEST, NEAREST surface, so a body
    can never pass through anything it can see;
    an OCCLUDER takes the WIDEST, LOWEST, FARTHEST surface, so nothing it can
    see is ever hidden.

Same cross-section, same kit, same ray casts, opposite reducer. `min` becomes
`max`. That is the whole of it, and stating it that way is what makes the second
one cheap: `occluder_shell` is `collision.corridor_shell` handed a deep profile
instead of a tight one, because the two are one construction.

WHY THE REDUCER HAS TO FLIP. The corridor's clear width is 1.0806 m to a portal
frame and 1.255 m between frames. Collision takes 1.0806 -- a body that fits the
pinch fits everywhere. An occluder at 1.0806 would stand 175 mm *inside* the
corridor void along most of the run and would hide the wall reveals, the
skirting return and the light coves that live in that 175 mm. Every one of them
is visible. An occluder that hides a visible surface is not a performance
optimisation, it is a hole in the world.

AND THE APERTURES HAVE TO GROW. A doorway cut at the door's own width is right
in the plane of the door and wrong at the plane of the occluder, which sits
further out: a player pressed against the far wall sees through the opening at a
slant and catches the room beyond outside the door's own footprint. The widening
is derived from the corridor's own geometry in `_parallax()` -- it is the worst
slant a body can achieve across the void -- not chosen.

Run: python3 station/occluders.py --selftest
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import collision as C                                           # noqa: E402
import interior_kit as K                                        # noqa: E402

# How far an occluder may stand proud of the surface it hides behind before the
# self-test calls it over-occlusion. This is a TOLERANCE ON THE MEASUREMENT, not
# a licence: the ray lattice samples a finite set of directions, so a surface
# whose nearest facet falls between two samples reads a millimetre late.
# Below the 5 mm this project already certifies a floor smooth at.
OVER_TOL_M = 0.002

# The narrowest feature a ray lattice here has to be able to land on. Not
# chosen: `station/collision.py` measured the deck's lighting channel at 66 mm
# and built a whole module around a capsule wedging in it. Anything narrower
# than this in the corridor's cross-section is a seam rather than a recess.
FEATURE_M = 0.066

INF = float("inf")

_DEEP = {}


def deep_profile(p=None, seg_len=9.205, force=False, invert=False):
    """The corridor's OUTERMOST cross-section, measured off the kit.

    The mirror of `collision.corridor_profile`, sample for sample, with every
    reducer flipped:

      floor_y  the LOWEST thing underfoot -- the 66 mm lighting channel, not the
               22 mm grid tile a boot rests on. An occluder at the tile hides
               the channel and its light strip, which is the brightest object in
               the corridor.
      half_w   the WIDEST the corridor gets anywhere, not the narrowest. 1.255 m
               between portal frames against collision's 1.0806 m at one.
      ceil_y   the HIGHEST the soffit goes, not where it first comes down.

    Returned in the kit's own frame, deck datum y = 0, so `occluder_shell` can
    hand it straight to `collision.corridor_shell` in place of a tight one.

    `invert=True` flips every reducer back and returns what the SAME ray lattice
    says when reduced collision's way. It exists to be checked against
    `collision.corridor_profile`: the claim in this module's docstring is that
    the two shells are one measurement with opposite reducers, and a claim like
    that should be executable rather than asserted in prose.
    """
    lo, hi = (max, min) if invert else (min, max)
    key = (id(p), round(seg_len, 4), invert)
    if key in _DEEP and not force:
        return _DEEP[key]
    tight = C.corridor_profile(p, seg_len)
    pv = p or K.PROVISIONAL
    wide = pv["corridor_width_m"] / 2.0

    # MEASURED ON A SECTION WITH DOORS IN IT, AND THE FIRST VERSION WAS NOT.
    # A bare `corridor_section` reads the ceiling at 3.000 m -- the kit's own
    # nominal -- and the containment test then found visible geometry at 3.064 m
    # near a doorway: the coffer the door head is let into, which does not exist
    # in a section that has no door. This is `interior_kit`'s lesson repeated
    # exactly. Its tag-coverage assertion ran on a corridor with no doors too,
    # and 1,248 unmaterialled triangles a deck came of it.
    #
    # THE HARD CASE IS THE ONE A GATE HAS TO BUILD.
    zc = seg_len / 2.0
    sections = [K.corridor_section(seg_len, p),
                K.corridor_section(seg_len, p, doors=((zc, -1), (zc, 1)),
                                   door_leaves=False)]

    # LATTICE PITCH IS SET BY THE NARROWEST FEATURE, NOT BY TASTE, and getting
    # that wrong is what this module's second bug was. `collision.py` records
    # that the deck carries a lighting channel 66 mm deep; the soffit carries
    # its own. A 21-column lattice across a 2.6 m corridor steps 130 mm and can
    # step straight over a 66 mm slot, which is how the first ceiling
    # measurement read 3.000 m -- the kit's nominal ceiling, to the millimetre,
    # a number that should have been suspicious on sight -- while the coffer
    # behind the light run reaches 3.065 m. The containment test found the 65 mm
    # the lattice could not.
    #
    # A ray lattice must resolve the smallest feature it is meant to see. This
    # one steps a third of the channel's own width.
    step = FEATURE_M / 3.0
    nx = int(2.0 * wide / step) + 1
    xs = [-wide + 2.0 * wide * i / (nx - 1) for i in range(nx)]
    nz = int(seg_len / step) + 1

    def sweep(origins, dirs):
        """Every variant's hits, as (distance, origin, direction) samples.

        NOT `min` PER RAY, and the first version was, which cost a whole run.
        Reducing the two section variants against each other before the profile
        reduces them is a reducer applied at the wrong level: the door-less
        section has a solid ceiling at 3.000 m, so taking the nearest hit threw
        away the door-bearing section's coffer at 3.065 m -- the exact surface
        the second variant was added to find. The variants are SAMPLES of one
        corridor. They join the same pool everything else does.
        """
        out = []
        for sv, st in sections:
            out.extend(zip(_cast_many(origins, dirs, sv, st), origins, dirs))
        return out

    org, dr = [], []
    for x in xs:
        for j in range(24):
            org.append((x, 2.0, seg_len * (j + 0.5) / 24.0))
            dr.append((0.0, -1.0, 0.0))
    tops = [2.0 - h for h, _o, _d in sweep(org, dr)
            if h != INF and 2.0 - h < 0.5]
    floor_y = lo(tops) if tops else 0.0

    # Sideways: the FARTHEST surface reachable from the centreline. A surface
    # deeper than this one is behind another surface and cannot be seen from
    # inside the corridor at all, so an occluder at this depth hides nothing.
    body_top = tight["floor_y"] + 1.8
    org, dr = [], []
    for i in range(60):
        y = tight["floor_y"] + 0.05 + (body_top - tight["floor_y"] - 0.05) * i / 59.0
        for j in range(nz):
            z = 0.2 + (seg_len - 0.4) * j / max(nz - 1, 1)
            for d in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)):
                org.append((0.0, y, z))
                dr.append(d)
    widths = [h for h, _o, _d in sweep(org, dr) if h != INF]
    half_w = hi(widths) if widths else wide

    # Overhead: the FARTHEST the soffit goes, across the corridor's own widest
    # width rather than down its centre.
    y0 = tight["floor_y"] + 0.1
    org, dr = [], []
    for x in xs:
        for j in range(nz):
            org.append((x, y0, seg_len * j / max(nz - 1, 1)))
            dr.append((0.0, 1.0, 0.0))
    heads = [y0 + h for h, _o, _d in sweep(org, dr) if h != INF]
    ceil_y = hi(heads) if heads else pv["ceiling_height_m"]

    # AND THEN THE SAME QUESTION ASKED WITHOUT AXES. Three axis-aligned lattices
    # cannot see an UNDERCUT, and the corridor has one: the soffit's light box
    # has a rim at 3.000 m with the coffer behind it reaching 3.065 m, so a ray
    # cast straight up stops on the rim and a ray cast at a slant goes under it.
    # The containment test found 65 mm of visible coffer behind the occluder and
    # the ceiling lattice, at 22 mm pitch, still read exactly 3.000 -- because
    # the pitch was never the problem. The DIRECTION was.
    #
    # So: eyes through the void, rays over the whole sphere, and the profile is
    # the bounding box of every point that answers. That is what an occluder is
    # -- the box around everything you can see -- and the axis-aligned lattices
    # above are kept because they are what `invert=True` compares against.
    if not invert:
        ex = [-tight["half_w"] * 0.9 + 1.8 * tight["half_w"] * i / 4 for i in range(5)]
        ey = [tight["floor_y"] + 0.15 + 1.75 * i / 4 for i in range(5)]
        ez = [seg_len * (i + 0.5) / 8 for i in range(8)]
        dirs = _dir_lattice(192)
        org, dr = [], []
        for x in ex:
            for y in ey:
                for z in ez:
                    for d in dirs:
                        org.append((x, y, z))
                        dr.append(d)
        for h, o, d in sweep(org, dr):
            if h == INF:
                continue
            n = math.sqrt(sum(c * c for c in d))
            px, py = o[0] + d[0] / n * h, o[1] + d[1] / n * h
            if py < tight["floor_y"] + 0.5:
                floor_y = min(floor_y, py)
            if py > tight["floor_y"] + 1.8:
                ceil_y = max(ceil_y, py)
            half_w = max(half_w, abs(px))

    out = {"floor_y": floor_y, "half_w": half_w, "ceil_y": ceil_y,
           "seg_len_m": seg_len, "samples": len(widths), "tight": tight,
           "inverted": invert}
    _DEEP[key] = out
    return out


_APERTURE = {}


def aperture_profile(p=None, seg_len=9.205, force=False):
    """How big the hole in the wall ACTUALLY is, measured off the kit.

    Not `p["door_width_m"]` and not `p["door_height_m"]`. A door aperture is cut
    through a wall assembly with a portal frame round it and a reveal behind it,
    and what a player can see through is the frame's inner edge -- which is not
    the door's own size and is not written down anywhere. The second breach the
    containment test found was exactly this: the occluder's header started at
    2.135 m and the reveal's head soffit is visible to 2.228 m.

    Measured by casting at the wall with the leaves suppressed and reading where
    the wall stops answering. Returns (half_z_m, top_y_m) in the kit frame --
    half the aperture's extent along the run, and how high it goes.
    """
    key = (id(p), round(seg_len, 4))
    if key in _APERTURE and not force:
        return _APERTURE[key]
    pv = p or K.PROVISIONAL
    zc = seg_len / 2.0
    v, t = K.corridor_section(seg_len, p, doors=((zc, -1),), door_leaves=False)
    tight = C.corridor_profile(p, seg_len)

    # An "open" sample is one where the wall does not answer within the width of
    # the corridor. Beyond that the ray has left through the hole.
    reach = pv["corridor_width_m"]
    n = int(3.2 / (FEATURE_M / 3.0)) + 1
    org, dr, at = [], [], []
    for i in range(n):
        y = tight["floor_y"] + 0.02 + 3.0 * i / (n - 1)
        for j in range(n):
            z = zc - 1.6 + 3.2 * j / (n - 1)
            org.append((0.0, y, z))
            dr.append((-1.0, 0.0, 0.0))
            at.append((z, y))
    open_z, open_y = [], []
    for h, (z, y) in zip(_cast_many(org, dr, v, t), at):
        if h == INF or h > reach:
            open_z.append(z)
            open_y.append(y)
    if not open_y:
        _APERTURE[key] = (pv["door_width_m"] / 2.0, pv["door_height_m"])
        return _APERTURE[key]
    half_z = max(abs(max(open_z) - zc), abs(zc - min(open_z)))
    _APERTURE[key] = (half_z, max(open_y))
    return _APERTURE[key]


def _parallax(deep, tight):
    """How much wider an aperture must be cut at the occluder plane than at the
    wall it stands behind.

    A body may stand anywhere in the corridor. The worst slant through a doorway
    is achieved from the far wall: the ray leaves x = -w, crosses the opening at
    the wall face x = +f and reaches the occluder plane at x = +d, so whatever
    half-width it spanned at the face it spans (d + w)/(f + w) of at the plane.
    Both hands of the corridor and both edges of the opening give the same
    factor, and it applies to the door head for the same reason it applies to the
    jambs.

    Returns a multiplier on the aperture's half-extent about its own centre.
    """
    w = d = deep["half_w"]
    f = tight["half_w"]
    return (d + w) / (f + w)


def occluder_shell(schema, profile, sector, ring_index, degrees=30.0,
                   start_deg=0.0, radius_m=None, z_offset=None, p=None,
                   doors=(), prof=None):
    """A conservative occluder for one arc of ring corridor.

    Same arguments and same frame as `interior.ring_arc` and
    `collision.corridor_shell`, and built BY the latter: this function's whole
    content is the deep profile and the widened apertures. There is no second
    construction to drift.

    Returns (verts, tris, meta). `meta` carries `aperture_scale`, which is the
    only number here that is neither measured off the kit nor inherited.
    """
    deep = prof or deep_profile(p)
    tight = deep["tight"]
    k = _parallax(deep, tight)

    # Widen each aperture about its own centre. `corridor_shell` cuts a door
    # half-width of `door_w/2/r` in angle either side of the door's angle and
    # opens the wall from the head upward, so scaling the two widths it is given
    # scales the opening -- there is no other place a door's size enters.
    pv = p or K.PROVISIONAL
    ap_half, ap_top = aperture_profile(p, deep["seg_len_m"])
    wide = dict(pv)
    wide["door_width_m"] = 2.0 * ap_half * k
    # The head rises toward the floor, ie the opening grows downward in radius
    # by the same slant. Measured from the eye rather than from the deck,
    # because that is where the slant is taken from.
    eye = tight["floor_y"] + 1.70
    wide["door_height_m"] = eye + (ap_top - eye) * k

    v, t, meta = C.corridor_shell(
        schema, profile, sector, ring_index, degrees=degrees,
        start_deg=start_deg, radius_m=radius_m, z_offset=z_offset,
        p=wide, prof=deep, doors=doors)
    meta["aperture_scale"] = round(k, 5)
    meta["door_width_m"] = wide["door_width_m"]
    meta["door_height_m"] = wide["door_height_m"]
    meta["kind"] = "occluder"
    return v, t, meta


# --------------------------------------------------------------------------
# Godot resources
# --------------------------------------------------------------------------
def gd_occluder(verts, tris, sub_id):
    """One `ArrayOccluder3D` sub-resource plus the `OccluderInstance3D` node
    that carries it, as `.tscn` text.

    THE INSTANCE IS NOT OPTIONAL AND NEITHER IS THE PROJECT SETTING. Godot only
    consults occluders when `rendering/occlusion_culling/use_occlusion_culling`
    is on; an `OccluderInstance3D` in a project without it is inert geometry
    that costs memory and culls nothing. `budget.py` refuses to apply its
    occlusion pass unless it can read BOTH out of `godot/`.
    """
    vs = ", ".join(f"{x:.4f}, {y:.4f}, {z:.4f}" for x, y, z in verts)
    ix = ", ".join(str(i) for tri in tris for i in tri)
    return (f'[sub_resource type="ArrayOccluder3D" id="Occ_{sub_id}"]\n'
            f"vertices = PackedVector3Array({vs})\n"
            f"indices = PackedInt32Array({ix})\n"), (
            f'[node name="Occluder_{sub_id}" type="OccluderInstance3D" '
            f'parent="."]\n'
            f'occluder = SubResource("Occ_{sub_id}")\n')


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------
def _cast_many(origins, dirs, verts, tris):
    """Nearest hit distance for many rays against many triangles, or inf.

    Moeller-Trumbore, vectorised over triangles for each ray. `collision.cast`
    is a scalar loop and is right for the fifteen hundred casts a profile takes;
    the containment test below takes tens of thousands against a bent arc.
    """
    import numpy as np                                        # noqa: PLC0415
    V = np.asarray(verts, float)
    T = np.asarray(tris, np.int32)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = b - a, c - a
    out = []
    for o, d in zip(origins, dirs):
        o = np.asarray(o, float)
        d = np.asarray(d, float)
        d = d / np.linalg.norm(d)
        pv = np.cross(d, e2)
        det = (e1 * pv).sum(1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - a
        u = (tv * pv).sum(1) * inv
        ok &= (u >= -1e-6) & (u <= 1 + 1e-6)
        qv = np.cross(tv, e1)
        vv = (d * qv).sum(1) * inv
        ok &= (vv >= -1e-6) & (u + vv <= 1 + 1e-6)
        dist = (e2 * qv).sum(1) * inv
        ok &= dist > 1e-5
        out.append(float(dist[ok].min()) if ok.any() else float("inf"))
    return out


def _eye_lattice(meta, n_ang=5, n_x=3, n_z=3, eye_m=1.70):
    """Standing eyes spread through the walkable void of an arc.

    Not one eye: the containment property is about every position a body can
    reach, and the worst slant through a doorway is from the wall opposite it.
    """
    tight = meta["profile"]["tight"]
    hw = tight["half_w"]
    out = []
    for i in range(n_ang):
        a = math.radians(meta["start_deg"]
                         + meta["arc_deg"] * (i + 0.5) / n_ang)
        for j in range(n_x):
            x = -hw * 0.9 + 1.8 * hw * j / max(n_x - 1, 1)
            for kk in range(n_z):
                rad = meta["floor_r_m"] - (0.4 + 1.4 * kk / max(n_z - 1, 1))
                out.append((rad * math.cos(a), rad * math.sin(a),
                            meta["z_m"] + x))
    return out


def _dir_lattice(n=64):
    """Directions on the sphere, near-uniform, deterministic."""
    out = []
    for i in range(n):
        y = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - y * y))
        th = math.pi * (1.0 + 5.0 ** 0.5) * i
        out.append((r * math.cos(th), y, r * math.sin(th)))
    return out


def containment(kit_v, kit_t, occ_v, occ_t, meta, n_dirs=64, eyes=None):
    """Does the occluder ever come between an eye and something it can see?

    THE ONE PROPERTY THAT MATTERS, and the only one whose failure is visible to
    a player. For every ray from every eye: if the occluder is hit at all, the
    kit must be hit at or before it. A ray that reaches the occluder without
    passing through the kit first is a surface the player is looking at that
    would be culled -- a hole in the world.

    Returns (rays, breaches, worst_m, escaped). `worst_m` is how far in front of
    the visible surface the occluder stood, at the worst ray.

    A ray that misses the kit entirely is ESCAPED, not a breach, and counting it
    as one was this test's first bug: an arc is a 6-degree slice of a 345-degree
    ring, so a ray down the corridor leaves the modelled geometry through a cut
    end that on the real deck is more corridor. The occluder's floor band curves
    up into that same ray and gets hit, which read as the occluder standing
    infinitely far in front of nothing at all. Escaped rays are reported so the
    number cannot quietly become most of the lattice.
    """
    eyes = eyes if eyes is not None else _eye_lattice(meta)
    dirs = _dir_lattice(n_dirs)
    origins, ds = [], []
    for e in eyes:
        for d in dirs:
            origins.append(e)
            ds.append(d)
    hk = _cast_many(origins, ds, kit_v, kit_t)
    ho = _cast_many(origins, ds, occ_v, occ_t)
    worst, breaches, escaped = 0.0, 0, 0
    for a, b in zip(hk, ho):
        if a == float("inf"):
            escaped += 1
            continue
        if b == float("inf"):
            continue
        gap = a - b                     # >0 means the occluder is in front
        if gap > OVER_TOL_M:
            breaches += 1
            worst = max(worst, gap)
    return len(origins), breaches, worst, escaped


def blocked_fraction(occ_v, occ_t, meta, n_dirs=256, eyes=None):
    """The share of the sphere an occluder closes off, from standing eyes.

    This is what the occluder BUYS, and it is reported next to `containment`
    because the two pull in opposite directions: an occluder that hides nothing
    visible is trivially satisfied by having no occluder at all.
    """
    eyes = eyes if eyes is not None else _eye_lattice(meta, 3, 2, 2)
    dirs = _dir_lattice(n_dirs)
    origins, ds = [], []
    for e in eyes:
        for d in dirs:
            origins.append(e)
            ds.append(d)
    ho = _cast_many(origins, ds, occ_v, occ_t)
    hit = sum(1 for h in ho if h != float("inf"))
    return hit / max(len(ho), 1)


# --------------------------------------------------------------------------
def _selftest():
    import interior as it                                    # noqa: PLC0415

    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name + (f"  {note}" if note else ""))

    schema, profile = it.load()
    seg = 9.205
    tight = C.corridor_profile(None, seg)
    deep = deep_profile(None, seg)

    print("\nthe two profiles, one kit, opposite reducers\n")
    print(f"  {'':10s}  {'collision':>10s}  {'occluder':>10s}   what moved")
    for k, why in (("floor_y", "the 66 mm lighting channel under the tile"),
                   ("half_w", "1.255 m between frames, 1.0806 m at one"),
                   ("ceil_y", "the soffit's deepest coffer")):
        print(f"  {k:10s}  {tight[k]:10.4f}  {deep[k]:10.4f}   {why}")

    check("the occluder is never inside the collision shell",
          deep["half_w"] > tight["half_w"] and deep["floor_y"] < tight["floor_y"]
          and deep["ceil_y"] > tight["ceil_y"],
          f"width +{(deep['half_w']-tight['half_w'])*1000:.0f} mm, floor "
          f"{(deep['floor_y']-tight['floor_y'])*1000:.0f} mm, ceiling "
          f"+{(deep['ceil_y']-tight['ceil_y'])*1000:.0f} mm")

    # THE CLAIM IN THE DOCSTRING, EXECUTED. "One measurement, opposite
    # reducers" is either true or it is a nice sentence, and the way to tell is
    # to run this lattice reduced collision's way and see whether collision's
    # own numbers come back out of it.
    inv = deep_profile(None, seg, invert=True)
    check("this lattice reduced collision's way lands on collision's profile",
          inv["half_w"] <= tight["half_w"] + 1e-9
          and inv["floor_y"] >= tight["floor_y"] - 1e-9,
          f"half_w {inv['half_w']:.4f} against collision's "
          f"{tight['half_w']:.4f}")
    # AND THE DIFFERENCE IS A FINDING, not a rounding error. This lattice steps
    # 22 mm and `collision.corridor_profile`'s steps 186 mm, so it lands on a
    # pinch collision's own sampling walks over. A collision half-width 19 mm
    # too generous is 19 mm of wall a shoulder can enter; it is not this
    # module's to change, and it is recorded here because this is where it
    # became visible.
    print(f"  finding   collision half_w {tight['half_w']:.4f} m, same cast at "
          f"{FEATURE_M/3*1000:.0f} mm pitch {inv['half_w']:.4f} m -- "
          f"{(tight['half_w']-inv['half_w'])*1000:.1f} mm of pinch its own "
          f"lattice steps over")

    # ---- the bent arc, with doors ----
    arc, start = 6.0, 0.0
    rings = it.ring_radii(schema, profile, "blue")
    r = rings[0]["r_mid"]
    kv, kt, kmeta = it.ring_arc(schema, profile, "blue", 0, degrees=arc,
                                start_deg=start, radius_m=r,
                                doors=((2.0, -1), (4.5, 1)))
    ov, ot, ometa = occluder_shell(schema, profile, "blue", 0, degrees=arc,
                                   start_deg=start, radius_m=r,
                                   doors=kmeta["doors_at"])
    print(f"\n  arc       {arc:.0f} deg at r = {r:.1f} m: kit {len(kt):,} tri, "
          f"occluder {len(ot):,} tri -- {len(ot)/max(len(kt),1)*100:.2f}% of it")
    print(f"  apertures {len(kmeta['doors_at'])} doors, cut "
          f"{ometa['aperture_scale']:.3f}x wide at the occluder plane "
          f"({ometa['door_width_m']:.3f} m against "
          f"{K.PROVISIONAL['door_width_m']:.3f} m at the wall)")

    ometa["profile"] = deep
    n, breach, worst, esc = containment(kv, kt, ov, ot, ometa)
    print(f"  contain   {n:,} rays from {len(_eye_lattice(ometa))} standing "
          f"eyes: {breach} breaches, worst {worst*1000:.1f} mm, {esc} escaped "
          f"through the cut ends of the arc")
    check("the occluder never stands in front of a visible surface",
          breach == 0, f"{breach} of {n:,} rays, worst {worst*1000:.1f} mm")

    frac = blocked_fraction(ov, ot, ometa)
    print(f"  blocks    {frac*100:.1f}% of the sphere from a standing eye")
    check("and it does close off most of the sphere", frac > 0.85,
          f"{frac*100:.1f}% -- a corridor is a tube with two ends and two doors")

    # ---- NEGATIVE CONTROL: the tight profile over-occludes ----
    bv, bt, bmeta = C.corridor_shell(schema, profile, "blue", 0, degrees=arc,
                                     start_deg=start, radius_m=r,
                                     doors=kmeta["doors_at"])
    bmeta["profile"] = deep
    _n, bbreach, bworst, _e = containment(kv, kt, bv, bt, bmeta)
    print(f"  control   the COLLISION shell used as an occluder: {bbreach} "
          f"breaches, worst {bworst*1000:.0f} mm")
    check("and the control fires -- collision geometry over-occludes",
          bbreach > 0 and bworst > 0.05,
          f"{bbreach} rays hidden, up to {bworst*1000:.0f} mm of visible "
          f"surface culled")

    # ---- NEGATIVE CONTROL: unwidened apertures ----
    uv, ut, umeta = C.corridor_shell(schema, profile, "blue", 0, degrees=arc,
                                     start_deg=start, radius_m=r,
                                     prof=deep, doors=kmeta["doors_at"])
    umeta["profile"] = deep
    _n, ubreach, uworst, _e = containment(kv, kt, uv, ut, umeta)
    print(f"  control   deep profile, aperture NOT widened: {ubreach} "
          f"breaches, worst {uworst*1000:.0f} mm")
    check("and the aperture widening is load-bearing",
          ubreach > 0,
          f"{ubreach} rays see the doorway at a slant the door's own width "
          f"does not cover")

    # ---- NEGATIVE CONTROL: no doors at all ----
    dv, dt, dmeta = occluder_shell(schema, profile, "blue", 0, degrees=arc,
                                   start_deg=start, radius_m=r, doors=())
    dmeta["profile"] = deep
    _n, dbreach, _w, _e = containment(kv, kt, dv, dt, dmeta)
    print(f"  control   apertures omitted entirely: {dbreach} breaches")
    check("and a sealed occluder hides the rooms behind the doors",
          dbreach > 0, f"{dbreach} rays end on a room the player can see into")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or True:
        return _selftest()


if __name__ == "__main__":
    sys.exit(main())
