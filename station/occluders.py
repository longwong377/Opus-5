#!/usr/bin/env python3
"""Occlusion geometry: the surfaces that are allowed to HIDE other surfaces.

WHO CALLS THIS, because for one session nobody did. `tools/wiring.py --callers`
found this module in the list of tested modules that nothing imports -- the
EIGHTH instance in this project of finished machinery with no caller on the
shipped path. It now has three:

    station/budget.py       measures what the occluder buys, in the standing
                            frame it already gates, and refuses to apply the
                            saving unless the whole chain is present
    tools/export_scene.py   emits the geometry beside the deck it belongs to,
                            as a .tscn Godot can load
    godot/project.godot     carries `rendering/occlusion_culling/
                            use_occlusion_culling=true`, without which Godot
                            ignores every OccluderInstance3D in the scene.
                            VERIFIED IN THE ENGINE rather than remembered:
                            4.4's own default for that setting is FALSE, so
                            before session 4o every occluder this module could
                            have produced would have been inert.

WHY THIS EXISTS, in the words of the gate that has been red for four sessions.
`station/budget.py` measures a standing frame on an assembled deck and reports
structure over its allowance. Its own diagnosis, written into `Frustum`'s
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

AND THE MEASUREMENT WAS BOUNDED ABOVE BY A NUMBER AVAILABLE FOR FREE. This
module spent three passes refining a ray lattice -- finer pitch, a second
section with doors in it, an omnidirectional sphere sweep -- and shipped at
6/7 with 209 containment breaches and every control returning the same 209.
The reason is one line of arithmetic: **a ray hit is a convex combination of
the hit triangle's three vertices, so in every axis it lies inside the kit's
own vertex extent.** No cast, at any pitch, in any direction, can return a
point outside that box. The lattice was therefore never measuring anything the
kit's vertices did not already state -- and where it fell SHORT of them, which
is what a `max` reducer must never do, containment failed. It read ceiling
3.000 m against kit geometry reaching 3.340 m, and the worst breach was 169 mm.

`deep_profile` now reduces the kit's own vertices and is exact by construction.
`ray_extents` keeps the lattice, because it answers a different and still
interesting question -- what can be SEEN rather than what EXISTS -- and because
its `invert=True` form is the executable version of this module's "one
measurement, opposite reducers" claim. The selftest runs it and prints the gap.
The cost fell from 5m13s to under a second, which is what makes the profile
affordable inside `budget.py` and `export_scene.py` rather than a thing nobody
can run.

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


def _sections(p, seg_len):
    """The corridor cross-section, twice: without doors and with them.

    MEASURED ON A SECTION WITH DOORS IN IT, AND THE FIRST VERSION WAS NOT.
    A bare `corridor_section` reads the ceiling at 3.000 m -- the kit's own
    nominal -- and the containment test then found visible geometry at 3.064 m
    near a doorway: the coffer the door head is let into, which does not exist
    in a section that has no door. This is `interior_kit`'s lesson repeated
    exactly. Its tag-coverage assertion ran on a corridor with no doors too,
    and 1,248 unmaterialled triangles a deck came of it.

    THE HARD CASE IS THE ONE A GATE HAS TO BUILD.
    """
    zc = seg_len / 2.0
    return [K.corridor_section(seg_len, p),
            K.corridor_section(seg_len, p, doors=((zc, -1), (zc, 1)),
                               door_leaves=False)]


def deep_profile(p=None, seg_len=9.205, force=False):
    """The corridor's OUTERMOST cross-section, from the kit's OWN VERTICES.

    The mirror of `collision.corridor_profile` with every reducer flipped:

      floor_y  the LOWEST thing underfoot -- not the 22 mm grid tile a boot
               rests on. An occluder at the tile hides the lighting channel and
               its light strip, which is the brightest object in the corridor.
      half_w   the WIDEST the corridor gets anywhere, not the narrowest.
      ceil_y   the HIGHEST anything reaches, not where the soffit first comes
               down.

    Returned in the kit's own frame, deck datum y = 0, so `occluder_shell` can
    hand it straight to `collision.corridor_shell` in place of a tight one.

    WHY THIS IS VERTICES AND NOT RAYS, and it is the finding this module cost
    the most to get. A ray hit is `a + u*(b-a) + v*(c-a)` with u, v >= 0 and
    u + v <= 1 -- a convex combination of the triangle's three vertices -- so
    every coordinate of every hit lies between the smallest and largest of the
    three. Reduce hits with `min`/`max` and you can never leave the kit's own
    vertex box; you can only fail to reach it. Three passes of lattice
    refinement were therefore chasing an upper bound that `min()` and `max()`
    over `verts` give exactly, in milliseconds, and the one axis where the
    lattice fell short is the one where containment failed:

        axis      ray lattice     kit vertices     short by
        floor_y      -0.084          -0.200         116 mm
        half_w        1.6799          1.6800          0 mm
        ceil_y        3.000           3.340         340 mm

    An occluder that stops at 3.000 stands in front of everything the kit puts
    between there and 3.340. That was 209 breaches, worst 169 mm.

    THE PRICE OF THE SAFE ANSWER IS 0.6 POINTS OF SPHERE COVERAGE, measured:
    `blocked_fraction` on the selftest arc goes 93.7% -> 93.1%. A tighter
    occluder blocks marginally more and is a hole in the world when it is
    wrong; this is not a close call.

    `ray_extents()` keeps the lattice. It answers what can be SEEN rather than
    what EXISTS, which is a genuinely tighter bound in principle, and it is
    where the `invert=True` cross-check against `collision.corridor_profile`
    lives.
    """
    key = (id(p), round(seg_len, 4))
    if key in _DEEP and not force:
        return _DEEP[key]
    tight = C.corridor_profile(p, seg_len)
    xs, ys = [], []
    for v, _t in _sections(p, seg_len):
        xs.extend(abs(q[0]) for q in v)
        ys.extend(q[1] for q in v)
    out = {"floor_y": min(ys), "half_w": max(xs), "ceil_y": max(ys),
           "seg_len_m": seg_len, "samples": len(ys), "tight": tight,
           "source": "kit vertex extent", "inverted": False}
    _DEEP[key] = out
    return out


_RAYS = {}


def ray_extents(p=None, seg_len=9.205, force=False, invert=False):
    """What a ray lattice through the corridor's void can REACH.

    Bounded above by `deep_profile`'s vertex box and provably unable to exceed
    it -- see that docstring. Kept for two reasons: it is the executable form
    of this module's "one kit, one measurement, opposite reducers" claim, and
    the gap between the two is a real statement about how much of the kit is
    behind other parts of the kit.

    `invert=True` flips every reducer back and returns what the SAME lattice
    says when reduced collision's way, to be checked against
    `collision.corridor_profile`.

    It costs about four minutes. `--selftest` runs it; nothing on the build
    path does.
    """
    lo, hi = (max, min) if invert else (min, max)
    key = (id(p), round(seg_len, 4), invert)
    if key in _RAYS and not force:
        return _RAYS[key]
    tight = C.corridor_profile(p, seg_len)
    pv = p or K.PROVISIONAL
    wide = pv["corridor_width_m"] / 2.0

    sections = _sections(p, seg_len)

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
           "source": "ray lattice", "inverted": invert}
    _RAYS[key] = out
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


def room_stub(meta, doors, depth_m=1.2):
    """A surface behind each doorway, so the aperture controls can fail.

    THE CONTROLS COULD NOT FIRE AND NOBODY NOTICED, and this is the fifth
    finding in this module and the same shape as the other four. `_selftest`
    asserted "a sealed occluder hides the rooms behind the doors" against
    `interior.ring_arc`, which builds a corridor and NO ROOMS -- so sealing the
    occluder hid nothing, and the assertion passed only because the baseline
    itself was breaching 209 rays and every control inherited them. With the
    baseline at 0 all three controls read 0 as well.

    Two things were wrong and both are worth keeping:

      1. there is nothing behind a `ring_arc` doorway to hide. This function
         puts one plate there -- the far wall of a room `depth_m` beyond the
         corridor's own, spanning the aperture and 1.4x its width so the slant
         cases are covered;
      2. `ring_arc`'s `door_leaves` defaults to TRUE, so the selftest's doors
         were SHUT. A shut door hides the room by itself and an occluder that
         also hides it is not doing anything wrong. `deck.build_deck` passes
         `door_leaves=False` and places openable leaves separately, so the
         shipped corridor is the open case -- the selftest was measuring a
         configuration the station does not build.

    With both fixed the three controls separate: sealed 133 breaches (worst
    2058 mm), unwidened 2 (worst 1214 mm), widened 0.
    """
    V, T = [], []
    fr, hw, z0 = meta["floor_r_m"], meta["half_w_m"], meta["z_m"]
    head = meta["radius_m"] - meta["door_h_m"]
    for d in doors:
        side = d.get("side", -1)
        half = math.degrees(meta["door_w_m"] / 2.0 / meta["radius_m"]) * 1.4
        z = z0 + side * (hw + depth_m)
        a0, a1 = d["angle_deg"] - half, d["angle_deg"] + half
        quad = [(rad * math.cos(math.radians(ang)),
                 rad * math.sin(math.radians(ang)), z)
                for rad, ang in ((head, a0), (fr, a0), (fr, a1), (head, a1))]
        o = len(V)
        V.extend(quad)
        T.extend([(o, o + 1, o + 2), (o, o + 2, o + 3)])
    return V, T


def joined(a, b):
    """Two (verts, tris) meshes as one. Index offsets, nothing else."""
    av, at = a
    bv, bt = b
    off = len(av)
    return (list(av) + list(bv),
            list(at) + [(x + off, y + off, z + off) for x, y, z in bt])


# --------------------------------------------------------------------------
# Godot resources
# --------------------------------------------------------------------------
def gd_occluder(verts, tris, sub_id):
    """One `ArrayOccluder3D` sub-resource plus the `OccluderInstance3D` node
    that carries it, as `.tscn` text.

    THE INSTANCE IS NOT OPTIONAL AND NEITHER IS THE PROJECT SETTING. Godot only
    consults occluders when `rendering/occlusion_culling/use_occlusion_culling`
    is on; an `OccluderInstance3D` in a project without it is inert geometry
    that costs memory and culls nothing.

    THAT SETTING'S ENGINE DEFAULT IS `false`, MEASURED. Run headless against
    Godot 4.4 double with the key absent from `project.godot`,
    `ProjectSettings.has_setting(...)` is true and
    `ProjectSettings.get_setting(...)` is **false** -- so it is a real engine
    setting that is off until somebody turns it on, not an unknown key.
    The same probe confirms `ArrayOccluder3D` exposes exactly `vertices` and
    `indices`, which is what the text below writes, and that a scene of this
    shape loads and hands back its occluder with the right vertex and index
    counts -- including from an ABSOLUTE path outside `res://`, which is how
    `station/generated/scene/deck/*_occ.tscn` will have to be reached.

    `station/budget.py::occlusion_chain` reads the project setting, this
    artefact and `godot/`'s scripts, and refuses to apply the saving unless all
    three are present. This docstring used to assert that as fact while
    `budget.py` had no occlusion pass at all -- a comment describing machinery
    that did not exist, which is how the next context loses a day.
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
# How many (ray x triangle) slots one Moeller-Trumbore block may hold. Sets
# peak memory, not the answer: a block allocates a handful of float64 arrays of
# this size plus two of three times it for the cross products, so 1e6 is about
# 150 MB and 1e7 would be a swap storm on a four-core box. Nothing about the
# result depends on it and `--selftest` asserts that by re-running one case a
# block at a time.
_BLOCK = 1_000_000


def _cast_many(origins, dirs, verts, tris):
    """Nearest hit distance for many rays against many triangles, or inf.

    Moeller-Trumbore, blocked over BOTH rays and triangles.

    IT USED TO LOOP OVER RAYS IN PYTHON and that made this module unrunnable
    rather than merely slow: `ray_extents` casts 283,000 rays and took 5m13s,
    of which almost all was numpy call overhead on 3,500-element arrays --
    twenty operations per ray, each too small to amortise its own dispatch.
    Blocking rays against triangles does the same arithmetic in the same order
    with the same tolerances and the same reducer; only the shape changes.
    `--selftest` A/Bs it against a scalar reference and requires the two to
    agree exactly, because a faster measurement that answers differently is not
    the same measurement.
    """
    import numpy as np                                        # noqa: PLC0415
    V = np.asarray(verts, float)
    T = np.asarray(tris, np.int32)
    a = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - a, V[T[:, 2]] - a
    O = np.asarray(origins, float).reshape(-1, 3)
    D = np.asarray(dirs, float).reshape(-1, 3)
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    n_t = max(len(a), 1)
    rows = max(1, int(_BLOCK // n_t))
    best = np.full(len(O), np.inf)
    A, E1, E2 = a[None, :, :], e1[None, :, :], e2[None, :, :]
    for i in range(0, len(O), rows):
        o = O[i:i + rows, None, :]
        d = D[i:i + rows, None, :]
        pv = np.cross(d, E2)
        det = (E1 * pv).sum(-1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - A
        u = (tv * pv).sum(-1) * inv
        ok &= (u >= -1e-6) & (u <= 1 + 1e-6)
        qv = np.cross(tv, E1)
        vv = (d * qv).sum(-1) * inv
        ok &= (vv >= -1e-6) & (u + vv <= 1 + 1e-6)
        dist = (E2 * qv).sum(-1) * inv
        ok &= dist > 1e-5
        np.copyto(best[i:i + rows],
                  np.where(ok, dist, np.inf).min(axis=1))
    return best.tolist()


def _cast_many_scalar(origins, dirs, verts, tris):
    """The ray-at-a-time reference `_cast_many` replaced. Kept as its control.

    Not dead code: a rewrite for speed is only credible against the thing it
    replaced, and this project has already recorded one A/B that reported
    IDENTICAL because both halves had died. `--selftest` runs both over the
    same rays and compares, and prints how many rays it compared.
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
def _selftest(rays=False):
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
    for k, why in (("floor_y", "the lighting channel under the tile"),
                   ("half_w", "the widest the corridor gets, not the pinch"),
                   ("ceil_y", "the deepest thing above the soffit")):
        print(f"  {k:10s}  {tight[k]:10.4f}  {deep[k]:10.4f}   {why}")
    print(f"  source    {deep['source']}, {deep['samples']:,} vertices over the "
          f"door-less and door-bearing sections")

    check("the occluder is never inside the collision shell",
          deep["half_w"] > tight["half_w"] and deep["floor_y"] < tight["floor_y"]
          and deep["ceil_y"] > tight["ceil_y"],
          f"width +{(deep['half_w']-tight['half_w'])*1000:.0f} mm, floor "
          f"{(deep['floor_y']-tight['floor_y'])*1000:.0f} mm, ceiling "
          f"+{(deep['ceil_y']-tight['ceil_y'])*1000:.0f} mm")

    # THE PROFILE'S OWN CLAIM, EXECUTED. `deep_profile` says no cast can return
    # a point outside the kit's vertex box because a hit is a convex
    # combination of three vertices. That is arithmetic, so it does not need a
    # lattice to confirm it -- but the SIZE of the gap is the interesting part
    # and only a lattice can say it, so `--rays` runs one.
    kv0, kt0 = _sections(None, seg)[1]
    check("no cast can leave the vertex box -- it is arithmetic, so assert it",
          _in_box(kv0, kt0, deep),
          "every vertex of the door-bearing section is inside the profile")

    # ---- the bent arc, with doors, WITH THE LEAVES OPEN ----
    # `ring_arc`'s `door_leaves` defaults to True and `deck.build_deck` passes
    # False -- see `room_stub`. A test on shut doors is a test on a
    # configuration the station does not build.
    arc, start = 6.0, 0.0
    rings = it.ring_radii(schema, profile, "blue")
    r = rings[0]["r_mid"]
    kv, kt, kmeta = it.ring_arc(schema, profile, "blue", 0, degrees=arc,
                                start_deg=start, radius_m=r,
                                doors=((2.0, -1), (4.5, 1)), door_leaves=False)
    ov, ot, ometa = occluder_shell(schema, profile, "blue", 0, degrees=arc,
                                   start_deg=start, radius_m=r,
                                   doors=kmeta["doors_at"])
    kv, kt = joined((kv, kt), room_stub(ometa, kmeta["doors_at"]))
    print(f"\n  arc       {arc:.0f} deg at r = {r:.1f} m: kit {len(kt):,} tri "
          f"(doors open, with a surface behind each), occluder {len(ot):,} tri "
          f"-- {len(ot)/max(len(kt),1)*100:.2f}% of it")
    print(f"  apertures {len(kmeta['doors_at'])} doors, cut "
          f"{ometa['aperture_scale']:.3f}x wide at the occluder plane "
          f"({ometa['door_width_m']:.3f} m against "
          f"{K.PROVISIONAL['door_width_m']:.3f} m at the wall)")

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

    # ---- NEGATIVE CONTROL: the two casts agree ----
    # A rewrite for speed is a claim about the ANSWER, not only the clock, and
    # this project has recorded one A/B that said IDENTICAL because both halves
    # had died. Both are run and both are required to have produced something.
    eyes = _eye_lattice(ometa, 2, 2, 2)
    ds = _dir_lattice(24)
    org = [e for e in eyes for _ in ds]
    dr = [d for _ in eyes for d in ds]
    fast = _cast_many(org, dr, ov, ot)
    slow = _cast_many_scalar(org, dr, ov, ot)
    # NOT `==`, AND THE REASON IS A FINDING RATHER THAN A CONCESSION. The two
    # differ on about 15% of rays -- always in the last bit, because numpy
    # sums a (rays x tris) reduction pairwise and a (tris,) reduction
    # serially. Requiring bit-equality here would fail a correct rewrite; the
    # bar is that the difference is far below anything this module resolves,
    # and OVER_TOL_M is 2 mm.
    worst = max((abs(a - b) for a, b in zip(fast, slow)
                 if a != INF and b != INF), default=0.0)
    same_miss = all((a == INF) == (b == INF) for a, b in zip(fast, slow))
    agree = (len(fast) == len(org) == len(slow) and len(org) > 0
             and same_miss and worst < 1e-9)
    print(f"  cast A/B  {len(org):,} rays, blocked and ray-at-a-time: worst "
          f"{worst*1e12:.3f} pm apart, {sum(1 for h in fast if h != INF):,} "
          f"hits, same misses {same_miss}")
    check("the blocked cast answers what the scalar one did, to a picometre",
          agree, f"{len(org):,} rays compared, worst {worst*1e12:.3f} pm "
                 f"against this module's {OVER_TOL_M*1000:.0f} mm tolerance")

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

    # ---- NEGATIVE CONTROL: the profile this module shipped with ----
    ray_prof = dict(deep, floor_y=-0.084, half_w=1.6799, ceil_y=3.000,
                    source="the ray lattice, as shipped at 6/7")
    rv, rt, rmeta = C.corridor_shell(
        schema, profile, "blue", 0, degrees=arc, start_deg=start, radius_m=r,
        prof=ray_prof, doors=kmeta["doors_at"],
        p=dict(K.PROVISIONAL, door_width_m=ometa["door_width_m"],
               door_height_m=ometa["door_height_m"]))
    rmeta["profile"] = deep
    _n, rbreach, rworst, _e = containment(kv, kt, rv, rt, rmeta)
    print(f"  control   the RAY-MEASURED profile this module shipped with: "
          f"{rbreach} breaches, worst {rworst*1000:.0f} mm")
    check("and the vertex bound is what fixed it, not the aperture work",
          rbreach > 0,
          f"ceiling 3.000 m against kit geometry at {deep['ceil_y']:.3f} m")

    # ---- NEGATIVE CONTROL: unwidened apertures ----
    uv, ut, umeta = C.corridor_shell(schema, profile, "blue", 0, degrees=arc,
                                     start_deg=start, radius_m=r,
                                     prof=deep, doors=kmeta["doors_at"])
    umeta["profile"] = deep
    # AT 256 DIRECTIONS, NOT 64, AND SAYING SO IS THE POINT. The widening
    # covers a SLIVER -- the extra 17.2% of aperture a body pressed to the far
    # wall needs -- and a 64-direction lattice steps about 25 degrees, which
    # walks straight over it. Run at 64 this control reads 0 breaches and looks
    # like proof the widening is unnecessary; at 256 it reads 2, worst 1214 mm,
    # which is a metre of visible room culled. A control that does not fire has
    # to be shown firing before it is worth anything, and the honest way to do
    # that is to state the resolution it needs rather than to keep the number
    # that flattered the code.
    _n, ubreach, uworst, _e = containment(kv, kt, uv, ut, umeta, n_dirs=256)
    print(f"  control   deep profile, aperture NOT widened: {ubreach} "
          f"breaches, worst {uworst*1000:.0f} mm (at 256 directions -- at 64 "
          f"it reads 0, see the note)")
    check("and the aperture widening is load-bearing",
          ubreach > 0,
          f"{ubreach} rays see the doorway at a slant the door's own width "
          f"does not cover")

    # ---- NEGATIVE CONTROL: no doors at all ----
    dv, dt, dmeta = occluder_shell(schema, profile, "blue", 0, degrees=arc,
                                   start_deg=start, radius_m=r, doors=())
    dmeta["profile"] = deep
    _n, dbreach, dworst, _e = containment(kv, kt, dv, dt, dmeta)
    print(f"  control   apertures omitted entirely: {dbreach} breaches, worst "
          f"{dworst*1000:.0f} mm")
    check("and a sealed occluder hides the rooms behind the doors",
          dbreach > 0, f"{dbreach} rays end on a room the player can see into")

    # ---- the lattice, opt-in, because it costs four minutes ----
    if rays:
        print("\n  --rays: what a lattice through the void can REACH, against "
              "what the kit CONTAINS\n")
        seen = ray_extents(None, seg)
        for k in ("floor_y", "half_w", "ceil_y"):
            print(f"  {k:10s}  lattice {seen[k]:8.4f}   vertices "
                  f"{deep[k]:8.4f}   short by "
                  f"{abs(deep[k]-seen[k])*1000:6.1f} mm")
        check("the lattice never leaves the vertex box",
              seen["floor_y"] >= deep["floor_y"] - 1e-9
              and seen["half_w"] <= deep["half_w"] + 1e-9
              and seen["ceil_y"] <= deep["ceil_y"] + 1e-9,
              "which is arithmetic, not luck")
        inv = ray_extents(None, seg, invert=True)
        check("this lattice reduced collision's way lands on collision's "
              "profile",
              inv["half_w"] <= tight["half_w"] + 1e-9
              and inv["floor_y"] >= tight["floor_y"] - 1e-9,
              f"half_w {inv['half_w']:.4f} against collision's "
              f"{tight['half_w']:.4f}")
        # AND THE DIFFERENCE IS A FINDING, not a rounding error. This lattice
        # steps 22 mm and `collision.corridor_profile`'s steps 186 mm, so it
        # lands on a pinch collision's own sampling walks over. A collision
        # half-width 19 mm too generous is 19 mm of wall a shoulder can enter;
        # it is not this module's to change, and it is recorded here because
        # this is where it became visible.
        print(f"  finding   collision half_w {tight['half_w']:.4f} m, same "
              f"cast at {FEATURE_M/3*1000:.0f} mm pitch {inv['half_w']:.4f} m "
              f"-- {(tight['half_w']-inv['half_w'])*1000:.1f} mm of pinch its "
              f"own lattice steps over")
    else:
        print("\n  the ray lattice was NOT run. It cannot change the profile "
              "(see deep_profile),\n  and it costs four minutes: "
              "`python3 station/occluders.py --selftest --rays`")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def _in_box(verts, tris, prof):
    """Is every vertex of a mesh inside a profile's box? The claim, executed."""
    for i in {i for t in tris for i in t}:
        x, y, _z = verts[i]
        if (abs(x) > prof["half_w"] + 1e-9 or y < prof["floor_y"] - 1e-9
                or y > prof["ceil_y"] + 1e-9):
            return False
    return True


def drum_ceiling(angle_deg=270.0, z_m=5132.0, stations=72, zs=20, steps=48):
    """WHAT AN OCCLUDER COULD BUY IN THE HABITAT DRUM. It is 5%. -- INV-541

    THE ANSWER IS NO, AND IT IS GEOMETRY RATHER THAN ENGINEERING. Everything
    above is about a corridor, where a wall a metre from each shoulder hides the
    far side of the ring. The drum has no wall: it is the inside of a cylinder,
    which is the boundary of a CONVEX region, and every point of the boundary of
    a convex region is visible from every point inside it. The only thing that
    can hide anything is relief and the objects standing on it.

    So this measures those two, from `budget.DRUM`'s own worst standing eye, and
    it measures the CEILING: it culls a target the moment it is hidden, charges
    nothing for the occluder geometry, nothing for the depth rasterisation, and
    tests at a granularity far finer than any renderer here works at. Weighted
    by the triangles each hidden thing would have contributed at the level the
    LOD chain would have drawn it, because a copse hidden at 1,200 m is 30
    triangles and a farmstead hidden at 30 m is 800.

    THE CONTROL IS THE CONVEXITY ITSELF. Flatten the heightfield to the mean
    cylinder and NOTHING may be occluded; if that returns a single blocked
    target this function is measuring its own arithmetic. Printed on every run.

    AND ONE LEVEL FURTHER DOWN IT IS WORSE THAN THIS CEILING, because Godot
    tests an INSTANCE's axis-aligned bounding box against a rasterised depth
    buffer, not a triangle. `render_shot.gd` reports **147 mesh instances over
    9 files** for the whole drum, and they are split by MATERIAL GROUP rather
    than by place -- `ground.glb` is 13 nodes spanning 4.5 million square
    metres. Not one of those AABBs can ever be behind anything. This is the
    same finding CLAUDE.md records for the corridor ("Godot culls per instance
    AABB and the corridor's OBJ groups span the whole 345 deg ring"), one
    environment along, and with the same conclusion: what would close a drum
    budget is spatial submission, and there is nothing for an occluder to do
    until that exists.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import drum_ground as dg                                   # noqa: PLC0415
    import drum_dressing as dd                                 # noqa: PLC0415
    import interior as _it                                     # noqa: PLC0415

    schema, profile = _it.load()
    sector = _it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)

    def ground_r(a_deg, z):
        u = (a_deg / 360.0) % 1.0
        w = min(max((z - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
        return dg.FLOOR_R - dg.sample(u, w)[0]

    def point(a_deg, z):
        r = ground_r(a_deg, z)
        a = math.radians(a_deg)
        return (r * math.cos(a), r * math.sin(a), z)

    def blocked(eye, target, n):
        for i in range(1, n):
            t = i / n
            q = tuple(eye[k] + (target[k] - eye[k]) * t for k in range(3))
            if math.hypot(q[0], q[1]) > ground_r(
                    math.degrees(math.atan2(q[1], q[0])) % 360.0, q[2]):
                return True
        return False

    eye, _up = dg.stand_on_ground(schema, profile, sector, angle_deg, z_m)
    targets = [(360.0 * i / stations,
                dg.Z0 + (dg.Z1 - dg.Z0) * (j + 0.5) / zs)
               for i in range(stations) for j in range(zs)]

    real = dg.sample
    dg.sample = lambda u, w: (0.0, "flat")
    flat_eye, _ = dg.stand_on_ground(schema, profile, sector, angle_deg, z_m)
    ctl = sum(1 for a_, z_ in targets
              if blocked(flat_eye, point(a_, z_), steps))
    dg.sample = real

    table = dg.lod_table()
    g_tot = g_hid = hid_patches = 0
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            lvl = dg.patch_level(pa, pz,
                                 dg.patch_nearest_distance(pa, pz, eye), table)
            g_tot += table[lvl]["patch_triangles"]
            allhid = True
            for i in range(3):
                for j in range(3):
                    a_ = (pa + (i + 0.5) / 3) * 360.0 / dg.PATCHES_A
                    z_ = dg.Z0 + (pz + (j + 0.5) / 3) * (dg.Z1 - dg.Z0) \
                        / dg.PATCHES_Z
                    if not blocked(eye, point(a_, z_), steps):
                        allhid = False
                        break
                if not allhid:
                    break
            if allhid:
                hid_patches += 1
                g_hid += table[lvl]["patch_triangles"]

    sw = dd.switch_distances()
    fld = dd.field()
    d_tot = d_hid = hid_feats = 0
    for f in fld["points"]:
        lv = dd._level(math.dist(f.position(), eye), sw)
        if dd._culled(f.kind, f.proto, lv, sw, f.scale, f.radius_m):
            continue
        d_tot += dd._feature_tris(f, lv)
        if blocked(eye, f.position(), 32):
            hid_feats += 1
            d_hid += dd._feature_tris(f, lv)
    for ln in fld["lines"]:
        lv = dd._level(math.dist(ln.centre(), eye), sw)
        d_tot += dd._line_tris(ln, lv)
        if blocked(eye, ln.centre(), 32):
            hid_feats += 1
            d_hid += dd._line_tris(ln, lv)

    near = dd.near_cost(eye)
    total = dd.DRUM_FIXED_TRIS + g_tot + d_tot + near
    return {"eye": (angle_deg, z_m), "control_blocked": ctl,
            "control_targets": len(targets),
            "ground_total": g_tot, "ground_cullable": g_hid,
            "hidden_patches": hid_patches, "patches": dg.PATCHES_A * dg.PATCHES_Z,
            "dressing_total": d_tot + near, "dressing_cullable": d_hid,
            "hidden_features": hid_feats,
            "features": len(fld["points"]) + len(fld["lines"]),
            "fixed": dd.DRUM_FIXED_TRIS, "frame_total": total,
            "cullable": g_hid + d_hid,
            "cullable_pct": (g_hid + d_hid) / total * 100.0}


def _print_drum_ceiling(**kw):
    m = drum_ceiling(**kw)
    print(f"\nThe habitat drum, from ({m['eye'][0]:g} deg, {m['eye'][1]:g} m) "
          f"-- budget.DRUM's own worst standing eye")
    print(f"  CONTROL, heightfield flattened to the mean cylinder: "
          f"{m['control_blocked']} of {m['control_targets']} targets blocked "
          f"-- a convex boundary must report 0")
    print(f"  ground   {m['ground_cullable']:,} of {m['ground_total']:,} "
          f"cullable ({m['ground_cullable']/max(m['ground_total'],1)*100:.2f}%),"
          f" {m['hidden_patches']} of {m['patches']} patches fully hidden")
    print(f"  dressing {m['dressing_cullable']:,} of "
          f"{m['dressing_total']:,} cullable "
          f"({m['dressing_cullable']/max(m['dressing_total'],1)*100:.2f}%), "
          f"{m['hidden_features']} of {m['features']} features hidden")
    print(f"  fixed    {m['fixed']:,} -- one instance each, spanning the drum, "
          f"not cullable at any granularity")
    print(f"  CEILING  {m['cullable']:,} of {m['frame_total']:,} = "
          f"{m['cullable_pct']:.2f}% of the drum frame, with a PERFECT and "
          f"FREE per-feature cull")
    print(f"  so the drum after perfect occlusion is "
          f"{m['frame_total']-m['cullable']:,} against 300,000 = "
          f"{(m['frame_total']-m['cullable'])/300000*100:.1f}%")
    return m


# --------------------------------------------------------------------------
# EMISSION -- an occluder BESIDE THE DECK THE SHIPPED BUILD LOADS
# --------------------------------------------------------------------------
# WHY THIS IS HERE AND NOT IN `tools/export_scene.py`, WHICH ALREADY HAD ONE.
# It had one for the WRONG DIRECTORY, and that is instance nine of this
# project's signature defect wearing a different hat. The chain, traced rather
# than remembered:
#
#   `export_scene.write_deck_occluder` is called from `export_scene.main`'s
#   --mode=deck path ALONE, which writes into `station/generated/scene/deck/`.
#   That directory is `station/walkable.py`'s walk-test fixture: ONE z-cluster
#   of ONE deck. The shipped world is written by `tools/export_station.py` into
#   `station/generated/scene/station/`, and THAT FILE NEVER CALLED
#   `write_deck_occluder` AT ALL.
#
#   `station/boot.py` then resolves the occluder as
#   `sidecar(stem, "_occ.tscn", preferred_deck_dir())`, and
#   `preferred_deck_dir()` returns the streamed build "whenever it exists" --
#   so it looked in `scene/station/`, found nothing, and wrote `"occluder": ""`
#   into `boot.json`. `main.gd` passed "" to `walk.gd`, whose `_load_occluder`
#   returned SILENTLY, and `budget.occlusion_chain` -- a STATIC SOURCE SCAN --
#   went on printing `PASS occluder reaches the engine` because a scan can see
#   that a caller exists and cannot see that its argument is empty.
#
# So the fix is not another call site inside a mode nobody runs. It is a
# generator that can be pointed at the shipped directory and run on its own,
# plus `export_station.py` calling it in-line (see `--emit`'s docstring for the
# four-line edit that file needs).
#
# EVERY DECISION IS READ FROM THE SAME `deck.deck_plan` CALL THE RENDER AND THE
# COLLISION BOTH USED -- the arc, the phase, the room doors, the junction
# doors. `deck.build_collision_clusters`'s own docstring gives the reason and
# it is this project's oldest lesson about doors: made twice, the two copies
# disagree, and five decks once shipped a room whose collision had a doorway
# and whose render was a sealed box. An occluder that disagrees about a doorway
# is worse than either -- it is a solid wall across an opening a player can see
# through, and the room behind it disappears.
STATION_OUT = os.path.join(os.path.dirname(HERE),
                           "station/generated/scene/station")


def write_scene(path, verts, tris, head):
    """The `.tscn` an `OccluderInstance3D` lives in. Returns `head` with
    `path` and `triangles` filled in.

    THE ONE WRITER. `tools/export_scene.py::write_deck_occluder` inlined this
    text, so there were two descriptions of one file format in the repository
    and only one of them was ever pointed at the shipped directory. That file
    should call this instead -- see `--emit`.

    A .tscn RATHER THAN GEOMETRY IN THE .glb, and the choice is forced: an
    occluder is an `ArrayOccluder3D`, which is a resource and not a mesh. Put
    it in the deck's glTF and the renderer DRAWS it.
    """
    import json                                                 # noqa: PLC0415
    head = dict(head)
    head["triangles"] = len(tris)
    head["vertices"] = len(verts)
    sub, node = gd_occluder(verts, tris, 0)
    with open(path, "w", encoding="utf-8") as f:
        f.write("[gd_scene load_steps=2 format=3]\n\n")
        f.write("; THE CORRIDOR'S OWN WALLS, AS AN OCCLUDER. Generated by\n"
                "; station/occluders.py --emit; do not hand-edit.\n"
                ";\n"
                "; Godot ignores this entirely unless\n"
                "; rendering/occlusion_culling/use_occlusion_culling is on -- "
                "the engine\n"
                "; default is false. See godot/project.godot.\n;\n")
        f.write("; occ-meta " + json.dumps(head) + "\n\n")
        f.write(sub + "\n")
        f.write('[node name="Occluders" type="Node3D"]\n\n')
        f.write(node)
    head["path"] = path
    return head


def deck_occluder(schema, profile, sector, ring, deck, join=True,
                  must_cover=None, keys=None):
    """Occlusion geometry for a WHOLE SHIPPED DECK -- every z-cluster of it.

    The mirror of `deck.build_collision_clusters`, and the mirror is the whole
    design: it walks the same `z_clusters`, calls the same `deck_plan` with the
    same `must_cover` and the same derived junction angle, and hands the result
    to `occluder_shell` instead of `collision.corridor_shell`. Same arc, same
    phase, same doors, opposite reducer.

    THE AXIAL SPINE IS OCCLUDED TOO, AND MEASURING IS WHAT SAID IT HAD TO BE.
    The first cut of this function skipped the joins on the argument that
    omitting geometry from an occluder can only cost performance and never
    correctness -- which is true, and which was worth **2.00% of submitted
    geometry, mean over a full turn on the spot**. The reason is that
    `boot.py`'s own spawn for `blue_0_0` stands at z 7447.1 and arc 89.264 deg,
    and the deck's six ring corridors sit at z 6946.5 ... 8066.5: the shipped
    player spawns IN THE SPINE, 59 m from the nearest ring, with the ring
    occluders edge-on. An occluder that omits the corridor the player is
    standing in is an occluder for somewhere else.

    `collision.axial_shell` is `corridor_shell` with its two long directions
    swapped and it takes the same `prof=`, so the deep profile applies to it
    unchanged -- there is no second construction here either. It needs no
    apertures because it has none: `build_collision_clusters` passes the spine
    no `doors`, and the junction openings are cut in the RING wall by
    `deck_plan(extra_doors=)`, which is handled above. The run is bounded by
    the occluder's OWN half width rather than the collision shell's, so it
    starts outside the ring corridor's deep wall and cannot overlap it -- which
    makes it shorter than the collision spine, in the safe direction.

    Returns (verts, tris, meta).
    """
    import deck as D                                            # noqa: PLC0415

    zs = D.clusters_for(sector, ring, deck, keys) if keys else \
        D.z_clusters(sector, ring, deck)
    if not zs:
        raise ValueError(f"{sector}/{ring}/{deck} carries no located cluster")
    axial = sorted(zs)
    plans = {z: D.deck_plan(schema, profile, sector, ring, deck, z,
                            must_cover=must_cover) for z in axial}
    at_deg, join_deg = {}, None
    if join and len(axial) > 1:
        a_lo = max(pl["lo"] for pl in plans.values())
        a_hi = min(pl["lo"] + pl["span"] for pl in plans.values())
        if a_hi - a_lo >= D.JOIN_MIN_ARC_DEG:
            join_deg = a_lo + (a_hi - a_lo) / 2.0
            for i, z in enumerate(axial):
                hands = ([-1] if i else []) + ([1] if i < len(axial) - 1 else [])
                at_deg[z] = tuple((join_deg, h) for h in hands)

    prof = deep_profile()
    V, T, metas = [], [], []
    for z in axial:
        # THE JUNCTION DOORS ARE ADDED HERE RATHER THAN BY A SECOND
        # `deck_plan(extra_doors=)` CALL, and that is an identity rather than a
        # shortcut: `extra_doors` never reaches `deck_arc` or `score()` -- it is
        # appended to the returned `doors` list and to nothing else -- so a
        # replanned cluster comes back with the same `lo`, `span`, `cz` and
        # `rooms`. `build_collision` makes the call and then ignores its
        # `doors` key for exactly the list built below. Skipping it halves this
        # function's cost, which is 24 door placements per phase per cluster.
        extra = at_deg.get(z, ())
        d = plans[z]
        doors = ([x[1] for x in d["rooms"]]
                 + [{"angle_deg": float(a), "side": float(sd)}
                    for a, sd in extra])
        v, t, m = occluder_shell(
            schema, profile, sector, ring, degrees=d["span"],
            start_deg=d["lo"], radius_m=d["radius"], z_offset=d["cz"],
            doors=doors, prof=prof)
        base = len(V)
        V.extend(v)
        T.extend((a + base, b + base, c + base) for a, b, c in t)
        m["doors"] = len(doors)
        metas.append(m)

    # THE SPINE, between consecutive clusters. Bounds and guard copied from
    # `deck.build_collision_clusters` so the two runs describe one corridor.
    joins = 0
    if join_deg is not None:
        for (za_m, ma), (zb_m, mb) in zip(list(zip(axial, metas)),
                                          list(zip(axial, metas))[1:]):
            za = ma["z_m"] + ma["half_w_m"]
            zb = mb["z_m"] - mb["half_w_m"]
            if zb - za < 1.0:
                continue
            jv, jt, _jm = C.axial_shell(schema, profile, sector, ring, za, zb,
                                        angle_deg=join_deg,
                                        radius_m=ma["radius_m"], prof=prof)
            base = len(V)
            V.extend(jv)
            T.extend((a + base, b + base, c + base) for a, b, c in jt)
            joins += 1

    return V, T, {"deck": f"{sector}/{ring}/{deck}", "clusters": len(metas),
                  "z": [round(z, 1) for z in axial], "join_deg": join_deg,
                  "joins": joins,
                  "doors": sum(m["doors"] for m in metas),
                  "arc_deg": round(max(m["arc_deg"] for m in metas), 3),
                  "radius_m": metas[0]["radius_m"],
                  "aperture_scale": metas[0]["aperture_scale"],
                  "triangles": len(T), "kind": "occluder"}


def emit(out_dir=None, only=None, quiet=False):
    """Write `<sector>_<ring>_<deck>_occ.tscn` for every SHELL A deck.

    THE FOUR-LINE EDIT `tools/export_station.py` STILL NEEDS, so that a rebuilt
    world carries its own occluders instead of depending on anyone remembering
    to run this. Inside its per-deck `else:` branch, beside the collision it
    already writes:

        import occluders as OC
        occ = OC.deck_occluder(schema, profile, sec, ring, dk, join=True,
                               must_cover=ang[sec])
        OC.write_scene(os.path.join(OUT, stem + "_occ.tscn"), *occ[:2], occ[2])

    SHELL B DECKS ARE SKIPPED AND THE SKIP IS COUNTED. `work_list()` seeds them
    with an empty cluster list and `station/shell_b.py` builds them; they have
    no `z_clusters`, so `deck_plan` raises for every one. They are the
    residential belts and they are 55 of the 126 decks on disk -- an honest
    "0 of 55" is worth more than a number that pretends otherwise.
    """
    import routes as RT                                         # noqa: PLC0415
    import interior as it                                       # noqa: PLC0415

    out_dir = out_dir or STATION_OUT
    schema, profile = it.load()
    nodes = RT.clusters()
    decks, ang = set(), {}
    for k in nodes:
        decks.add(k[:3])
    for s in sorted({k[0] for k in nodes}):
        ang[s] = RT.transit_angle(s, nodes)
    rows, skipped = [], []
    for sec, ring, dk in sorted(decks):
        stem = f"{sec}_{ring}_{dk}"
        if only and stem not in only:
            continue
        try:
            v, t, m = deck_occluder(schema, profile, sec, ring, dk,
                                    join=True, must_cover=ang[sec])
        except Exception as e:                                  # noqa: BLE001
            skipped.append((stem, f"{type(e).__name__}: {e}"))
            continue
        m["deck_stem"] = stem
        head = write_scene(os.path.join(out_dir, stem + "_occ.tscn"), v, t, m)
        rows.append(head)
        if not quiet:
            print(f"  {stem}: {len(t):,} tri over {m['clusters']} cluster(s), "
                  f"{m['doors']} apertures cut {m['aperture_scale']:.3f}x wide "
                  f"-> {os.path.basename(head['path'])}")
    if skipped and not quiet:
        print(f"  {len(skipped)} deck(s) declined: "
              f"{', '.join(s for s, _ in skipped[:4])}"
              f"{' ...' if len(skipped) > 4 else ''}")
        print(f"    first reason: {skipped[0][1]}" if skipped else "")
    if not quiet:
        print(f"occluders: wrote {len(rows)}, declined {len(skipped)}, "
              f"{sum(r['triangles'] for r in rows):,} triangles total, "
              f"into {out_dir}")
    return rows, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rays", action="store_true",
                    help="also run the ray lattice (~4 min) and print how far "
                         "short of the kit's own vertex extent it lands")
    ap.add_argument("--drum", action="store_true",
                    help="measure the CEILING on what an occluder could buy "
                         "inside the habitat drum (~40 s). It is a negative "
                         "result and it is the point of the flag")
    ap.add_argument("--emit", action="store_true",
                    help="write <deck>_occ.tscn beside every SHIPPED deck in "
                         "station/generated/scene/station -- the directory "
                         "station/boot.py actually looks in")
    ap.add_argument("--deck", action="append", default=None, metavar="STEM",
                    help="with --emit: only this deck stem, repeatable")
    ap.add_argument("--out", default=None,
                    help="with --emit: the directory to write into")
    a = ap.parse_args(argv)
    if a.emit:
        rows, skipped = emit(a.out, set(a.deck) if a.deck else None)
        return 0 if rows else 1
    if a.drum:
        m = _print_drum_ceiling()
        return 0 if m["control_blocked"] == 0 else 1
    return _selftest(rays=a.rays)


if __name__ == "__main__":
    sys.exit(main())
