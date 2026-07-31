#!/usr/bin/env python3
"""Collision geometry, which is NOT render geometry -- and this project learned
why the hard way.

WHAT THIS FIXES. Session 3u assembled a deck, put a body on it, and the body
stood there: `on_floor=true`, `drop=1.07`, and `moved_1s=0.001` in all four
headings. The level looked right, the controller was right, gravity was right,
and the body could not take a step. The cause was found by casting rays into the
corridor's own cross-section and reading the numbers off:

  the deck carries a lighting channel 0.18 m wide and 66 mm deep down its exact
  centreline, flanked by grid tiles standing 22 mm proud with 38 mm seams
  between them, and every kit section repeats its neighbour's portal frame

so a 0.35 m capsule dropped on the centreline lands straddling a 66 mm slot,
Godot's concave shape hands back an internal-edge normal tilted 18 degrees
across the corridor, and `move_and_slide` spends all six of its iterations
sliding against a wall it cannot climb. Moving the spawn off the channel did not
help: 0.62 m further on there is a 22 mm step at every tile seam.

THE PROOF, because a diagnosis without one is a guess. A smooth shell at the
same radius, the same 7 km from the origin, over the same 344 degrees, walked at
**4.200 m/s** -- full speed, clean floor normal, no axial term. Same everything
else. It is the millimetres.

THE RULE THAT FOLLOWS, and it is general: **a player walks on a surface built
for walking on, not on the surface built for looking at.** Every shipping game
does this and this project needed it for two independent reasons -- the physical
one above, and that trimesh collision over 458,160 corridor triangles is not
something a runtime can afford. The shell is 83x smaller.

HOW IT CANNOT DRIFT. The profile is not written down here. It is MEASURED off
`interior_kit.corridor_section` by casting rays through its cross-section, so if
the kit's floor or walls move the shell moves with them -- hard rule 4, inside
and outside from one schema, applied to the third thing that has to agree.

Run: python3 station/collision.py --selftest
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import interior as it                                           # noqa: E402
import interior_kit as K                                        # noqa: E402

# How much a facet of the swept shell may sag inside the true cylinder. At the
# ring radius this sets the step count; 1 mm is far below anything a character
# controller reacts to and still costs only a few thousand triangles.
MAX_SAG_M = 0.001

# The tallest lip a walking body should ever meet on a floor it is meant to
# cross. Godot's own step handling is generous, but the failure this module
# exists for happened at 22 mm, so the tolerance that certifies a floor smooth
# has to be tighter than that.
STEP_TOLERANCE_M = 0.005


def _ray_tri(o, d, a, b, c):
    """Moeller-Trumbore. Returns distance along `d`, or None."""
    e1 = [b[i] - a[i] for i in range(3)]
    e2 = [c[i] - a[i] for i in range(3)]
    p = [d[1] * e2[2] - d[2] * e2[1],
         d[2] * e2[0] - d[0] * e2[2],
         d[0] * e2[1] - d[1] * e2[0]]
    det = sum(e1[i] * p[i] for i in range(3))
    if abs(det) < 1e-12:
        return None
    inv = 1.0 / det
    t = [o[i] - a[i] for i in range(3)]
    u = sum(t[i] * p[i] for i in range(3)) * inv
    if u < -1e-6 or u > 1 + 1e-6:
        return None
    q = [t[1] * e1[2] - t[2] * e1[1],
         t[2] * e1[0] - t[0] * e1[2],
         t[0] * e1[1] - t[1] * e1[0]]
    v = sum(d[i] * q[i] for i in range(3)) * inv
    if v < -1e-6 or u + v > 1 + 1e-6:
        return None
    dist = sum(e2[i] * q[i] for i in range(3)) * inv
    return dist if dist > 1e-5 else None


def cast(o, d, verts, tris):
    """Nearest hit along a ray, or None. Brute force, and fast enough: the
    things measured here are one kit section, not a station."""
    best = None
    for tri in tris:
        h = _ray_tri(o, d, verts[tri[0]], verts[tri[1]], verts[tri[2]])
        if h is not None and (best is None or h < best):
            best = h
    return best


_PROFILE = {}


def corridor_profile(p=None, seg_len=9.205, force=False):
    """The corridor's walkable cross-section, MEASURED off the kit.

    Returns floor_y (the surface a boot rests on), half_w (how far from the
    centreline a body may get) and ceil_y, all in the kit's own frame where the
    deck datum is y = 0.

    `floor_y` is the HIGHEST thing underfoot, not the lowest. The deck is three
    surfaces -- a lighting channel at -0.066, its panel at 0.000, and grid tiles
    at +0.022 -- and a body walks on the tiles. Taking the mean or the minimum
    would sink the player into the floor they can see.

    `half_w` is the NARROWEST clearance over the body's height, not the widest
    or the typical. Portal frames pinch the corridor to 1.080 m every 3.6 m
    while the run between them is 1.255 m; a shell built on the wider number
    lets a player walk their shoulder through a jamb. 175 mm of unreachable
    corridor is the price and it is invisible in first person, because the
    capsule's own radius is twice that.
    """
    key = (id(p), round(seg_len, 4))
    if key in _PROFILE and not force:
        return _PROFILE[key]
    v, t = K.corridor_section(seg_len, p)

    # Underfoot: sample across the width and along the run, and keep the top.
    tops = []
    for i in range(24):
        x = -1.2 + 2.4 * i / 23.0
        for j in range(10):
            z = seg_len * (j + 0.5) / 10.0
            h = cast((x, 2.0, z), (0.0, -1.0, 0.0), v, t)
            if h is not None and 2.0 - h < 0.5:
                tops.append(2.0 - h)
    floor_y = max(tops) if tops else 0.0

    # Sideways: the narrowest the corridor gets anywhere a body occupies.
    body_top = floor_y + 1.8
    widths = []
    for i in range(14):
        y = floor_y + 0.05 + (body_top - floor_y - 0.05) * i / 13.0
        for j in range(45):
            z = 0.2 + (seg_len - 0.4) * j / 44.0
            a = cast((0.0, y, z), (1.0, 0.0, 0.0), v, t)
            b = cast((0.0, y, z), (-1.0, 0.0, 0.0), v, t)
            if a is not None and b is not None:
                widths.append(min(a, b))
    half_w = min(widths) if widths else K.PROVISIONAL["corridor_width_m"] / 2.0

    # Overhead: where the soffit first comes down. Closes the shell; a walking
    # body never touches it.
    heads = []
    for j in range(20):
        z = seg_len * (j + 0.5) / 20.0
        h = cast((0.0, floor_y + 0.1, z), (0.0, 1.0, 0.0), v, t)
        if h is not None:
            heads.append(floor_y + 0.1 + h)
    ceil_y = min(heads) if heads else K.PROVISIONAL["ceiling_height_m"]

    out = {"floor_y": floor_y, "half_w": half_w, "ceil_y": ceil_y,
           "seg_len_m": seg_len, "samples": len(widths)}
    _PROFILE[key] = out
    return out


def _strip(verts, tris, pts_a, pts_b, want):
    """A quad strip between two matched polylines, wound so its faces point the
    way `want(i)` says they should.

    WINDING IS NOT COSMETIC HERE. Godot's ConcavePolygonShape3D has
    `backface_collision` off by default, so a floor wound the wrong way is a
    floor a body falls straight through -- the exact failure this project spent
    four sessions on with open surfaces, arriving by a different road.
    """
    base = len(verts)
    verts.extend(pts_a)
    verts.extend(pts_b)
    n = len(pts_a)
    for i in range(n - 1):
        a0, a1 = base + i, base + i + 1
        b0, b1 = base + n + i, base + n + i + 1
        for tri in ((a0, a1, b1), (a0, b1, b0)):
            p, q, r = (verts[j] for j in tri)
            u = [q[k] - p[k] for k in range(3)]
            w = [r[k] - p[k] for k in range(3)]
            nrm = [u[1] * w[2] - u[2] * w[1],
                   u[2] * w[0] - u[0] * w[2],
                   u[0] * w[1] - u[1] * w[0]]
            d = want(i)
            tris.append(tri if sum(nrm[k] * d[k] for k in range(3)) > 0
                        else (tri[0], tri[2], tri[1]))


def corridor_shell(schema, profile, sector, ring_index, degrees=30.0,
                   start_deg=0.0, radius_m=None, z_offset=None, p=None,
                   prof=None, doors=()):
    """A closed, smooth collision shell for one arc of ring corridor.

    Same arguments and same frame as `interior.ring_arc`, deliberately: the two
    are the render and the collide of one corridor and any divergence between
    their signatures is a divergence waiting to happen.

    `doors` is `ring_arc`'s own `meta["doors_at"]` -- the SNAPPED positions, not
    the requested ones -- so the hole a player walks through is the hole they can
    see. Passing the asked-for angles instead would put the two up to 1.5 m
    apart, which is a door you can see and cannot enter, or worse a wall you can
    walk through.

    THE COLLISION APERTURE HAS NO SILL. The visible door has a 100 mm one, and a
    100 mm vertical face is a wall to a capsule, not a step -- the player would
    stop dead in the doorway. Feet passing 100 mm through a sill is invisible in
    first person and is exactly the class of thing this module exists to smooth.
    """
    rings = it.ring_radii(schema, profile, sector)
    ring = rings[ring_index]
    ex = schema["sectors"]["extents_m"][sector]
    z_mid = z_offset if z_offset is not None else (ex["z0"] + ex["z1"]) / 2.0
    r = ring["r_mid"] if radius_m is None else radius_m
    q = prof or corridor_profile(p)

    floor_r = r - q["floor_y"]
    ceil_r = r - q["ceil_y"]
    hw = q["half_w"]

    # Steps sized so a facet's sag stays under MAX_SAG_M: sag = r(1-cos(dt/2)).
    dt = 2.0 * math.acos(max(-1.0, 1.0 - MAX_SAG_M / max(r, 1e-9)))
    steps = max(4, int(math.ceil(math.radians(degrees) / dt)))

    def arc_angles(a0_deg, a1_deg):
        """Angles across a sub-range at the shell's own resolution."""
        n = max(1, int(math.ceil(abs(a1_deg - a0_deg) / (degrees / steps))))
        return [math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
                for i in range(n + 1)]

    angs = arc_angles(start_deg, start_deg + degrees)

    def band(rad, x, aa=None):
        return [(rad * math.cos(a), rad * math.sin(a), z_mid + x)
                for a in (angs if aa is None else aa)]

    verts, tris = [], []
    inward = [(-math.cos(a), -math.sin(a), 0.0) for a in angs]
    outward = [(math.cos(a), math.sin(a), 0.0) for a in angs]

    # Floor: faces inward, which is UP for anyone standing on a spun ring. It
    # runs THROUGH the doorways uninterrupted -- a player steps from corridor to
    # vestibule without the floor ever handing over.
    _strip(verts, tris, band(floor_r, -hw), band(floor_r, hw),
           lambda i: inward[i])
    # Ceiling: faces outward, back down at the floor.
    _strip(verts, tris, band(ceil_r, -hw), band(ceil_r, hw),
           lambda i: outward[i])

    # Walls: face into the corridor, which is +Z for the -x side and vice versa.
    # Each is broken by the doors on its own hand: full height between them, and
    # only a header above them, so the aperture is genuinely open.
    door_w = (p or K.PROVISIONAL)["door_width_m"]
    door_h = (p or K.PROVISIONAL)["door_height_m"]
    head_r = r - door_h
    for side, face in ((-1.0, (0.0, 0.0, 1.0)), (1.0, (0.0, 0.0, -1.0))):
        cuts = sorted((d["angle_deg"] - math.degrees(door_w / 2.0 / r),
                       d["angle_deg"] + math.degrees(door_w / 2.0 / r))
                      for d in doors if d.get("side", -1) == side)
        at = start_deg
        for c0, c1 in cuts:
            c0 = max(c0, start_deg)
            c1 = min(c1, start_deg + degrees)
            if c1 <= at:
                continue
            if c0 > at:
                aa = arc_angles(at, c0)
                _strip(verts, tris, band(floor_r, side * hw, aa),
                       band(ceil_r, side * hw, aa), lambda i, f=face: f)
            # Over the opening, wall only from the door head upward.
            aa = arc_angles(c0, c1)
            _strip(verts, tris, band(head_r, side * hw, aa),
                   band(ceil_r, side * hw, aa), lambda i, f=face: f)
            at = c1
        if at < start_deg + degrees:
            aa = arc_angles(at, start_deg + degrees)
            _strip(verts, tris, band(floor_r, side * hw, aa),
                   band(ceil_r, side * hw, aa), lambda i, f=face: f)

    return verts, tris, {
        "doors": list(doors),
        "door_w_m": door_w,
        "door_h_m": door_h,
        "sector": sector,
        "ring_index": ring_index,
        "radius_m": round(r, 3),
        "floor_r_m": round(floor_r, 4),
        "ceil_r_m": round(ceil_r, 4),
        "half_w_m": round(hw, 4),
        "z_m": z_mid,
        "arc_deg": degrees,
        "start_deg": start_deg,
        "steps": steps,
        "triangles": len(tris),
        "profile": q,
    }


def _quad(verts, tris, pts, want):
    """One quad, wound so its faces point the way `want` says.

    Winding decides whether a surface is a floor or a hole: Godot's
    ConcavePolygonShape3D has `backface_collision` off, so a face wound away
    from the player is a face the player falls through.
    """
    base = len(verts)
    verts.extend(pts)
    for tri in ((base, base + 1, base + 2), (base, base + 2, base + 3)):
        p, q, s = (verts[j] for j in tri)
        u = [q[k] - p[k] for k in range(3)]
        w = [s[k] - p[k] for k in range(3)]
        nrm = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
               u[0] * w[1] - u[1] * w[0]]
        tris.append(tri if sum(nrm[k] * want[k] for k in range(3)) > 0
                    else (tri[0], tri[2], tri[1]))


def room_shell(meta, angle_deg, hw_m, hl_m, ceil_m, z_m, door_angle_deg=None,
               steps=None):
    """A room's collision: floor, ceiling, four walls, and a hole to get in by.

    ROOMS GET A SHELL FOR THE SAME REASON THE CORRIDOR DOES. `articulate` runs
    the same skirting, dado, rail and deck-joint vocabulary round every room on
    the station, so a room's render mesh has the millimetre relief that stopped
    the body in the corridor -- and its walls carry bands that cross a doorway.

    WHAT THIS COSTS, and it is worth saying plainly rather than discovering
    later: **the props in the room are not solid.** `dressing.py` puts 82,362
    triangles of furniture on this station and none of it is in this shell, so a
    player walks through tables. Prop collision is a real piece of work -- convex
    decomposition per prop type, not trimesh per instance -- and it is its own
    task, not a line in this one.

    The room's frame is the ring's: it spans `angle_deg +/- hw/r`, world z from
    `z_m -/+ hl`, and radius from the deck floor inward by `ceil_m`.
    """
    r = meta["floor_r_m"]
    ceil_r = r - ceil_m
    da = hw_m / r
    a0, a1 = math.radians(angle_deg) - da, math.radians(angle_deg) + da
    z0, z1 = z_m - hl_m, z_m + hl_m
    n = steps or max(2, int(math.ceil(2 * da / max(
        2.0 * math.acos(max(-1.0, 1.0 - MAX_SAG_M / max(r, 1e-9))), 1e-9))))
    verts, tris = [], []

    def arc(rad, z, i0, i1):
        return [(rad * math.cos(a0 + (a1 - a0) * k / n),
                 rad * math.sin(a0 + (a1 - a0) * k / n), z)
                for k in (i0, i1)]

    # Floor and ceiling, tessellated round the arc so they do not sag.
    for k in range(n):
        m = (a0 + (a1 - a0) * (k + 0.5) / n)
        up = (-math.cos(m), -math.sin(m), 0.0)
        down = (math.cos(m), math.sin(m), 0.0)
        for rad, want in ((r, up), (ceil_r, down)):
            p0, p1 = arc(rad, z0, k, k + 1)
            q0, q1 = arc(rad, z1, k, k + 1)
            _quad(verts, tris, [p0, p1, q1, q0], want)

    # The two long walls, at the room's angular edges, facing in.
    for a, s in ((a0, 1.0), (a1, -1.0)):
        inward = (-math.sin(a) * s, math.cos(a) * s, 0.0)
        _quad(verts, tris,
              [(r * math.cos(a), r * math.sin(a), z0),
               (r * math.cos(a), r * math.sin(a), z1),
               (ceil_r * math.cos(a), ceil_r * math.sin(a), z1),
               (ceil_r * math.cos(a), ceil_r * math.sin(a), z0)], inward)

    # The two end walls. The far one -- toward the corridor, at higher z -- is
    # broken by the doorway; the near one is solid.
    door_h = meta["door_h_m"]
    door_da = meta["door_w_m"] / 2.0 / r
    for z, want in ((z0, (0.0, 0.0, 1.0)), (z1, (0.0, 0.0, -1.0))):
        cuts = []
        if door_angle_deg is not None and z == z1:
            d = math.radians(door_angle_deg)
            cuts = [(max(a0, d - door_da), min(a1, d + door_da))]
        at = a0
        spans = []
        for c0, c1 in cuts:
            if c0 > at:
                spans.append((at, c0, r))
            spans.append((c0, c1, r - door_h))     # header only over the door
            at = c1
        if at < a1:
            spans.append((at, a1, r))
        for b0, b1, rad_lo in spans:
            if b1 - b0 < 1e-9:
                continue
            _quad(verts, tris,
                  [(rad_lo * math.cos(b0), rad_lo * math.sin(b0), z),
                   (rad_lo * math.cos(b1), rad_lo * math.sin(b1), z),
                   (ceil_r * math.cos(b1), ceil_r * math.sin(b1), z),
                   (ceil_r * math.cos(b0), ceil_r * math.sin(b0), z)], want)
    return verts, tris


def vestibule_shell(meta, angle_deg, z_from, z_to, width_m=None, height_m=None):
    """A walkable stub joining a corridor door to a room that does not reach it.

    WHY THESE EXIST. The rooms on a deck are sized by what they hold, so their
    outer walls do not land on one line: on Blue ring 0 deck 0 the corridor sits
    flush against `plantroom_bay` and **1.98 m** clear of `bay_elevators`. A door
    onto a 2 m gap is a door onto vacuum. A short entry passage is also simply
    what a station has, so this is architecture rather than a patch.

    Built in the shell's frame: floor at the corridor's own floor radius so a
    player crosses the threshold without a step, walls at the door's width, and
    a ceiling at the door head. Open at both ends -- it is a hole between two
    places, and capping it would be the wall it exists to remove.
    """
    r = meta["floor_r_m"]
    hw = (width_m or meta["door_w_m"]) / 2.0
    ceil_r = r - (height_m or meta["door_h_m"])
    da = hw / r
    a0, a1 = math.radians(angle_deg) - da, math.radians(angle_deg) + da
    lo, hi = min(z_from, z_to), max(z_from, z_to)
    if hi - lo < 1e-6:
        return [], []                      # flush already: the door IS the join

    verts, tris = [], []

    def quad(pts, want):
        _quad(verts, tris, pts, want)

    mid = (a0 + a1) / 2.0
    up = (-math.cos(mid), -math.sin(mid), 0.0)
    down = (math.cos(mid), math.sin(mid), 0.0)
    for rad, want in ((r, up), (ceil_r, down)):
        quad([(rad * math.cos(a0), rad * math.sin(a0), lo),
              (rad * math.cos(a1), rad * math.sin(a1), lo),
              (rad * math.cos(a1), rad * math.sin(a1), hi),
              (rad * math.cos(a0), rad * math.sin(a0), hi)], want)
    for a, s in ((a0, 1.0), (a1, -1.0)):
        inward = (-math.sin(a) * s, math.cos(a) * s, 0.0)
        quad([(r * math.cos(a), r * math.sin(a), lo),
              (r * math.cos(a), r * math.sin(a), hi),
              (ceil_r * math.cos(a), ceil_r * math.sin(a), hi),
              (ceil_r * math.cos(a), ceil_r * math.sin(a), lo)], inward)
    return verts, tris


def stand_at(meta, angle_deg, x_m=0.0, above_m=0.05):
    """Where to put a body so it starts on this shell's floor.

    `above_m` is small ON PURPOSE. `deck.spawn_m` dropped bodies from a metre up
    and called the resulting 1.07 m fall a settle; a spawn is a claim that a
    person can stand at a place, and a claim that needs a metre of falling to
    resolve is not being checked, it is being hoped for.
    """
    a = math.radians(angle_deg)
    rad = meta["floor_r_m"] - above_m
    return (rad * math.cos(a), rad * math.sin(a), meta["z_m"] + x_m)


def _down_index(verts, tris):
    """Bin triangles by angle so a radial cast need not test all of them.

    INDEXED, because a gate too slow to run is a gate that does not run. Brute
    force is 9 lanes x 240 casts x 26,000 triangles and takes minutes; binning
    by angle and rejecting on the lane's own z first takes seconds and answers
    the identical question.
    """
    bins, nbin = {}, 720
    for tri in tris:
        ps = [verts[j] for j in tri]
        zs = [p[2] for p in ps]
        angs = [math.atan2(p[1], p[0]) for p in ps]
        if max(angs) - min(angs) > math.pi:      # straddles the +/-pi seam
            b0, b1 = 0, nbin - 1
        else:
            b0 = int((min(angs) + math.pi) / (2 * math.pi) * nbin)
            b1 = int((max(angs) + math.pi) / (2 * math.pi) * nbin)
        for b in range(max(0, b0 - 1), min(nbin, b1 + 2)):
            bins.setdefault(b, []).append((min(zs), max(zs), tri))
    return bins, nbin


def surface_radii(verts, tris, meta, samples=240, lanes=9, from_m=1.9):
    """Radii of the first surface under a body, sampled over the walkable width.

    Yields (lane_index, sample_index, radius). Everything that asks "where is
    the floor" goes through this, so the several questions cannot end up
    answered by several slightly different casts.
    """
    bins, nbin = _down_index(verts, tris)
    lo, hi = meta["start_deg"], meta["start_deg"] + meta["arc_deg"]
    top = meta["floor_r_m"] - from_m
    hw = meta["half_w_m"]
    for k in range(lanes):
        x = -hw + 2.0 * hw * k / (lanes - 1) if lanes > 1 else 0.0
        z = meta["z_m"] + x
        for i in range(samples):
            a = math.radians(lo + (hi - lo) * i / (samples - 1))
            aa = math.atan2(math.sin(a), math.cos(a))
            b = int((aa + math.pi) / (2 * math.pi) * nbin) % nbin
            o = (top * math.cos(a), top * math.sin(a), z)
            d = (math.cos(a), math.sin(a), 0.0)
            best = None
            for z0, z1, tri in bins.get(b, ()):
                if z < z0 - 1e-6 or z > z1 + 1e-6:
                    continue
                h = _ray_tri(o, d, verts[tri[0]], verts[tri[1]], verts[tri[2]])
                if h is not None and (best is None or h < best):
                    best = h
            yield k, i, (None if best is None else top + best)


def underfoot_radius(verts, tris, meta, **kw):
    """The radius of the surface MOST of this floor presents, in metres.

    The check that the collision shell has not drifted off the geometry it
    stands in for. `corridor_profile` finds the floor by taking the HIGHEST
    thing underfoot anywhere in the kit's cross-section; this takes the MEDIAN
    over the width and length a body can occupy. Agreement means the surface a
    body rests on is the surface most of the deck actually presents -- a high
    pimple over 2% of the deck would pass the first test and fail this one, and
    a player standing on a pimple hovers.

    Not a statistic over triangle radii: a corridor deck stacks three surfaces
    within 88 mm and every wall and portal has its base on the middle one, so
    counting triangles elects the wrong plane. Cast, as a foot does.
    """
    rs = sorted(r for _k, _i, r in surface_radii(verts, tris, meta, **kw)
                if r is not None)
    if not rs:
        return None
    return rs[len(rs) // 2]


def floor_steps(verts, tris, meta, samples=240, lanes=9):
    """The biggest lip a body meets walking this floor, in metres.

    THIS IS THE GATE THE PROJECT DID NOT HAVE. Walk the floor casting down, and
    report the largest jump between neighbouring samples. A smooth shell reads
    under a millimetre; the render corridor reads its tile height, which is what
    stopped the body. It measures a surface rather than trusting whatever made
    it, so it works on either.

    IT SWEEPS LANES, and the first version did not -- it walked the centreline
    alone and reported the render corridor smooth to 0.6 mm, because the
    centreline is the inside of the lighting channel and the channel bottom is
    the one continuous lane on the whole deck. The 22 mm tile seams start at
    x = 0.09 m. A gate that samples the single place the defect is absent is the
    same mistake as the render-at-one-distance that cost this project three
    layers, so this one covers the width a body can actually occupy.
    """
    worst, prev, lane = 0.0, None, -1
    for k, _i, rad in surface_radii(verts, tris, meta, samples, lanes):
        if k != lane:
            lane, prev = k, None
        if rad is None:
            prev = None
            continue
        if prev is not None:
            worst = max(worst, abs(rad - prev))
        prev = rad
    return worst


def prop_boxes(verts, tris, groups, solid=None, min_m=0.18, gap=0.04):
    """Collision boxes for a room's furniture, DERIVED from its own geometry.

    `dressing.py` puts 82,362 triangles of furniture on this station and none of
    it was solid, so a player walked through tables. That is the thing a person
    notices first once the doors work, and it is not a detail: a room you can
    walk through the middle of is a backdrop, not a place.

    NOT A SECOND LIST. The obvious approach is to have every prop builder record
    the box it just placed, and this project has now been bitten twice by two
    descriptions of one thing drifting apart -- the door decision made in the
    render and again in the shell, the corridor profile written down instead of
    measured. So this reads the emitted mesh: connected components of shared
    vertices are the individual boxes `_box`/`_cyl` wrote, and boxes that touch
    are one object. A chair's seat, back and legs merge into a chair.

    `min_m` drops anything smaller than a fist in every dimension -- a stapler
    on a desk is not something a body walks into, and 9 items per square metre
    of tabletop is a lot of collision to carry for nothing.

    `solid` decides what counts as an object, and it defaults to `rooms.is_solid`
    ON PURPOSE: that is the same predicate `rooms.build`'s density trial uses to
    ask whether a body can still cross the room. The first version took only the
    `dress_` furniture, so a player walked straight through every FIXTURE -- a
    bar's till, a medlab's scanner -- while the walkability guarantee had been
    computed as though they were solid. A guarantee computed against a different
    world than the one that ships is not a guarantee.
    """
    if solid is None:
        import rooms as _R                                       # noqa: PLC0415
        solid = _R.is_solid
    per = [None] * len(tris)
    for name, lo, hi in groups:
        for i in range(lo, min(hi, len(tris))):
            per[i] = name
    keep = [tri for i, tri in enumerate(tris)
            if per[i] and solid(per[i])]
    if not keep:
        return []

    # Connected components over shared vertices: one per emitted primitive.
    parent = {}

    def find(a):
        while parent.get(a, a) != a:
            parent[a] = parent.get(parent[a], parent[a])
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for tri in keep:
        for j in tri:
            parent.setdefault(j, j)
        union(tri[0], tri[1])
        union(tri[1], tri[2])

    comp = {}
    for tri in keep:
        r = find(tri[0])
        b = comp.get(r)
        for j in tri:
            p = verts[j]
            if b is None:
                b = [p[0], p[1], p[2], p[0], p[1], p[2]]
            else:
                for k in range(3):
                    b[k] = min(b[k], p[k])
                    b[k + 3] = max(b[k + 3], p[k])
        comp[r] = b
    boxes = list(comp.values())

    # Merge whatever touches. Repeated until nothing changes, because a chair is
    # a chain -- legs touch the seat, the seat touches the back.
    changed = True
    while changed:
        changed = False
        out = []
        for b in boxes:
            for o in out:
                if all(b[k] - gap <= o[k + 3] and o[k] - gap <= b[k + 3]
                       for k in range(3)):
                    for k in range(3):
                        o[k] = min(o[k], b[k])
                        o[k + 3] = max(o[k + 3], b[k + 3])
                    changed = True
                    break
            else:
                out.append(list(b))
        boxes = out
    return [b for b in boxes
            if max(b[k + 3] - b[k] for k in range(3)) >= min_m]


def boxes_mesh(boxes, place_fn):
    """Boxes -> a closed collision mesh, each face turned to face outward.

    `place_fn` maps a room-local point into world space, so the same boxes work
    on a ring deck, on the drum, or anywhere else a room gets put.
    """
    verts, tris = [], []
    for x0, y0, z0, x1, y1, z1 in boxes:
        c = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
        wc = place_fn([c])[0]
        for face in (
            [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
            [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
            [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        ):
            pts = place_fn(face)
            mid = [sum(p[k] for p in pts) / 4.0 for k in range(3)]
            want = [mid[k] - wc[k] for k in range(3)]
            _quad(verts, tris, pts, want)
    return verts, tris


def floor_holes(verts, tris, meta, along_m=0.35, samples=90):
    """Places on a route from the corridor into each room where there is no
    floor. Returns a list of (room_key, z, angle_deg).

    THE GATE THAT WOULD HAVE SAVED A DEBUG CYCLE. The corridor shell, the
    vestibules and the room shells are three separately-generated meshes that
    have to hand a walking body over to one another, and the first assembly left
    a **0.219 m gap at every doorway**: the vestibule ran to the kit's nominal
    half width while the corridor's floor stops at its MEASURED clear half
    width. A body that walked into one fell through and accelerated outward
    under spin gravity for 30 km.

    The walk test did catch it -- `offfloor=2363/3000` -- but only after a
    Godot launch, and only for the one route it happened to take. This walks
    every doorway in Python, in a second, and says WHICH one and WHERE.

    `along_m` is the sampling pitch, a capsule diameter: a hole a body cannot
    fall through is not a hole.
    """
    bins, nbin = _down_index(verts, tris)
    top = meta["floor_r_m"] - 1.9
    out = []
    for room in meta.get("rooms", ()):
        a = math.radians(room["door_deg"])
        z1 = meta["z_m"] - meta["half_w_m"] + 0.2      # inside the corridor
        z0 = z1 - room["vestibule_m"] - 2.0            # into the room
        n = max(samples, int((z1 - z0) / along_m))
        b = int((math.atan2(math.sin(a), math.cos(a)) + math.pi)
                / (2 * math.pi) * nbin) % nbin
        o_dir = (math.cos(a), math.sin(a), 0.0)
        for i in range(n + 1):
            z = z0 + (z1 - z0) * i / n
            o = (top * math.cos(a), top * math.sin(a), z)
            hit = None
            for tz0, tz1, tri in bins.get(b, ()):
                if z < tz0 - 1e-6 or z > tz1 + 1e-6:
                    continue
                h = _ray_tri(o, o_dir, verts[tri[0]], verts[tri[1]],
                             verts[tri[2]])
                if h is not None and (hit is None or h < hit):
                    hit = h
            # A HOLE IS NOTHING UNDERFOOT, OR SOMETHING BELOW THE FLOOR -- not
            # something ABOVE it. The first version demanded the first surface
            # be the floor itself, which was fine until the furniture became
            # solid: a ray cast down through a table hits the table, and the
            # gate called five tabletops in `mooring_clamps` a hole in the deck.
            # Standing on a table is not falling through the deck. Up is inward
            # on a spun ring, so "above the floor" is a SMALLER radius.
            if hit is None or top + hit > meta["floor_r_m"] + 0.05:
                out.append((room["key"], round(z, 3),
                            round(room["door_deg"], 2)))
    return out


def write_obj(path, verts, tris, name="collision"):
    with open(path, "w") as f:
        f.write(f"g {name}\n")
        for x, y, z in verts:
            f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        for a, b, c in tris:
            f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = it.load()
    q = corridor_profile()
    print(f"measured profile: floor_y={q['floor_y']:+.4f}  "
          f"half_w={q['half_w']:.4f}  ceil_y={q['ceil_y']:.3f}  "
          f"({q['samples']} width samples)")

    # The profile must come off the kit, so it must agree with the kit's own
    # numbers where the kit states them.
    check("the floor is the top surface, not the channel or the panel",
          abs(q["floor_y"] - 0.022) < 1e-6,
          f"floor_y={q['floor_y']} -- deck_grid stands its tiles 22 mm proud")
    check("the clear width is the pinch, not the average",
          q["half_w"] < K.PROVISIONAL["corridor_width_m"] / 2.0,
          f"half_w={q['half_w']} vs kit half {K.PROVISIONAL['corridor_width_m'] / 2}")
    check("a person fits standing up",
          q["ceil_y"] - q["floor_y"] > 1.9,
          f"headroom {q['ceil_y'] - q['floor_y']:.2f} m")

    plan = it.ring_cells(schema, profile, "blue", 0, 0)
    v, t, m = corridor_shell(schema, profile, "blue", 0, degrees=20.0,
                             start_deg=150.0, radius_m=plan["radius_m"],
                             z_offset=7120.0)
    check("a shell is emitted", len(t) > 0, str(m)[:100])

    # It has to be MUCH cheaper than the render mesh, because the other half of
    # why this module exists is that 458k triangles of trimesh collision per
    # deck is not affordable at runtime.
    rv, rt, _rm = it.ring_arc(schema, profile, "blue", 0, degrees=20.0,
                              start_deg=150.0, radius_m=plan["radius_m"],
                              z_offset=7120.0)
    check("the shell is far cheaper than the render mesh",
          len(t) * 8 < len(rt),
          f"{len(t):,} shell vs {len(rt):,} render")

    # THE ONE THAT MATTERS, and it is stated as a comparison rather than an
    # absolute so it cannot pass by being vague: the shell's floor is smooth and
    # THE RENDER MESH'S FLOOR IS NOT. If the second half ever stops failing, the
    # render corridor has lost the detail that makes it worth looking at and
    # this module has stopped being necessary.
    smooth = floor_steps(v, t, m)
    rough = floor_steps(rv, rt, m)
    check("the collision floor is smooth enough to walk",
          smooth <= STEP_TOLERANCE_M, f"largest lip {smooth * 1000:.1f} mm")
    check("and the render floor is NOT -- the reason this module exists",
          rough > STEP_TOLERANCE_M,
          f"render floor lip {rough * 1000:.1f} mm, under tolerance: the "
          f"corridor has lost its deck articulation")
    print(f"  floor lip: shell {smooth * 1000:.2f} mm, "
          f"render {rough * 1000:.2f} mm")

    # Winding, which decides whether the floor is a floor or a hole.
    n_up = 0
    for tri in t:
        a, b, c = (v[j] for j in tri)
        if not (abs(math.hypot(*a[:2]) - m["floor_r_m"]) < 1e-6
                and abs(math.hypot(*b[:2]) - m["floor_r_m"]) < 1e-6):
            continue
        u = [b[k] - a[k] for k in range(3)]
        w = [c[k] - a[k] for k in range(3)]
        nrm = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
               u[0] * w[1] - u[1] * w[0])
        mid = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
        rr = math.hypot(*mid) or 1.0
        if nrm[0] * -mid[0] / rr + nrm[1] * -mid[1] / rr > 0:
            n_up += 1
    floor_tris = sum(
        1 for tri in t
        if all(abs(math.hypot(v[j][0], v[j][1]) - m["floor_r_m"]) < 1e-6
               for j in tri))
    check("every floor triangle faces the player, not the void",
          floor_tris > 0 and n_up == floor_tris,
          f"{n_up}/{floor_tris} wound inward -- the rest are holes")

    # The sag bound is what sets the step count, so it has to hold.
    sag = m["radius_m"] * (1.0 - math.cos(
        math.radians(m["arc_deg"]) / m["steps"] / 2.0))
    check("facet sag is inside the bound", sag <= MAX_SAG_M * 1.001,
          f"{sag * 1000:.3f} mm against {MAX_SAG_M * 1000:.1f} mm")

    sp = stand_at(m, 158.0)
    check("a stand point is on the floor, just above it",
          abs(math.hypot(sp[0], sp[1]) - m["floor_r_m"] + 0.05) < 1e-6,
          f"r={math.hypot(sp[0], sp[1]):.4f} floor={m['floor_r_m']}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", default="blue")
    ap.add_argument("--ring", type=int, default=0)
    ap.add_argument("--deck", type=int, default=0)
    ap.add_argument("--degrees", type=float, default=30.0)
    ap.add_argument("--start-deg", type=float, default=0.0)
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--obj", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    schema, profile = it.load()
    plan = it.ring_cells(schema, profile, a.sector, a.ring, a.deck)
    v, t, m = corridor_shell(schema, profile, a.sector, a.ring,
                             degrees=a.degrees, start_deg=a.start_deg,
                             radius_m=plan["radius_m"], z_offset=a.z)
    print(f"{a.sector} ring {a.ring} deck {a.deck}: {len(t):,} collision "
          f"triangles over {a.degrees} deg, floor r={m['floor_r_m']} m, "
          f"clear width {m['half_w_m'] * 2:.3f} m")
    if a.obj:
        write_obj(a.obj, v, t)
        print(f"  wrote {a.obj}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
