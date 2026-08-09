#!/usr/bin/env python3
"""Aurora-class Starfury airframe, built in the flight model's own body frame.

`station/physics/starfury.py` already fixes where this craft's thrusters are.
Geometry and physics describing the same machine differently is the exact
failure this project exists to avoid, so the mesh is anchored to those mount
points rather than eyeballed alongside them, and
`station/test_starfury_geometry.py` asserts the two still agree.

Body frame, matching the flight model: **+z forward, +y up, +x starboard.**

Convention: a thruster's mount point is the centre of its **nozzle exit plane**.
That is where the flight model applies the force, so it is the one point on a
nozzle with physical meaning; using the throat or the housing centroid instead
would put the mesh a nozzle-length away from where the craft is actually pushed.

## What the references establish

`reference/12-starfury/` holds four files: two scans of Steve Burg's 1993
concept sheet (`Starfury more.jpg`, `earth alliance fighter.jpeg`, authority 2),
one on-screen frame (`Starfury.jpg`, authority 1), one community 3D model
(`starfury even more detailed.jpeg`, authority 4). They agree on the
arrangement, which is what gets modelled here:

  * A compact angular fuselage under a flat arrowhead deck, with a long faceted
    canopy raking forward **and downward** out from under that deck, pilot
    visible inside, caged by heavy structural struts.
  * Four booms in an X, joined to the fuselage by broad flat root fairings.
  * A main engine bell at the aft end of each boom, and nozzles facing forward
    at the nose -- Burg draws open bell mouths at both ends, which is what "no
    preferred direction of travel" looks like as hardware.
  * Vaned plate structures outboard of each nacelle, and small nozzles on short
    stalks around the central hub between the boom roots.

**Nothing here is an aerofoil.** The root fairings and tip vanes are flat plates
lying in the plane spanned by their own boom axis and the craft's roll axis, so
from dead ahead they are edge-on and the craft reads as four thin arms. That is
the Starfury's design premise and the reason its silhouette is not an
aeroplane's.

Dimensions are extrapolation, not canon -- canon fixes the station's length, not
the fighter's. See canon/INVENTIONS.md INV-009 for what constrains them.
"""
import argparse
import json
import math
import os

# --- anchors shared with the flight model -----------------------------------
# Deliberately *duplicated* from station/physics/starfury.py rather than
# imported. Importing would make the agreement test vacuous; the point is to
# fail loudly when one side's layout is edited and the other is not.
BOOM_HALF_SPAN_M = 3.4     # main engine offset on both x and y
ENGINE_STATION_M = -2.1    # main engine exit plane, aft of the centre of mass
RCS_RING_RADIUS_M = 3.4    # lateral and vertical RCS exit planes
RETRO_STATION_M = 2.4      # forward-firing retro exit plane

X = (1.0, 0.0, 0.0)
Y = (0.0, 1.0, 0.0)
Z = (0.0, 0.0, 1.0)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (0.0, 0.0, 0.0) if n == 0 else _mul(a, 1.0 / n)


def _frame(axis, hint):
    """Orthonormal (right, up) with cross(right, up) == axis.

    Constructed rather than assumed, so a loft advancing along an arbitrary
    direction still winds outward. Get this backwards on one boom and it renders
    as a hole rather than as an error, which is why every section's winding is
    checked numerically by signed volume in the test.
    """
    axis = _unit(axis)
    up = _unit(_sub(hint, _mul(axis, _dot(hint, axis))))
    return _cross(up, axis), up


def _ring(centre, right, up, half_r, half_u, chamfer=0.32):
    """One section, wound CCW seen from +axis.

    A chamfered rectangle rather than a circle: Earth Alliance hardware reads as
    folded plate with cut corners, and one chamfer parameter spans plate-flat
    (0) to nearly round (0.6) without needing a second primitive.
    """
    if chamfer <= 0.0:
        local = ((half_r, half_u), (-half_r, half_u),
                 (-half_r, -half_u), (half_r, -half_u))
    else:
        cr, cu = chamfer * half_r, chamfer * half_u
        local = ((half_r, half_u - cu), (half_r - cr, half_u),
                 (-half_r + cr, half_u), (-half_r, half_u - cu),
                 (-half_r, -half_u + cu), (-half_r + cr, -half_u),
                 (half_r - cr, -half_u), (half_r, -half_u + cu))
    return [_add(centre, _add(_mul(right, u), _mul(up, v))) for u, v in local]


def _loft(verts, tris, rings, cap_start=False, cap_end=False):
    """Skin a sequence of equal-length rings advancing along their axis."""
    base = len(verts)
    n = len(rings[0])
    for r in rings:
        verts.extend(r)
    for k in range(len(rings) - 1):
        a0, a1 = base + k * n, base + (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            tris.append((a0 + i, a0 + j, a1 + j))
            tris.append((a0 + i, a1 + j, a1 + i))
    for want, idx, flip in ((cap_start, 0, True), (cap_end, len(rings) - 1, False)):
        if not want:
            continue
        ring = rings[idx]
        centre = len(verts)
        verts.append(tuple(sum(p[k] for p in ring) / n for k in range(3)))
        off = base + idx * n
        for i in range(n):
            j = (i + 1) % n
            tris.append((centre, off + j, off + i) if flip
                        else (centre, off + i, off + j))


def _revolve(verts, tris, centre, axis, profile, chamfer=0.62, hint=None):
    """Lathe a (distance-along-axis, radius) profile about `axis`.

    A radius of zero at either end of the profile becomes an apex point, so a
    cup -- outer wall, lip, then back down the inside -- comes out as one closed
    surface with correct normals on both faces. That matters for every nozzle on
    the craft: an engine bell modelled as an open tube has no inside, and an
    engine bell capped flat has no mouth.
    """
    axis = _unit(axis)
    right, up = _frame(axis, hint or (Z if abs(_dot(axis, Z)) < 0.9 else Y))
    rings, apex_start, apex_end = [], None, None
    for i, (t, r) in enumerate(profile):
        p = _add(centre, _mul(axis, t))
        if r <= 0.0:
            if i == 0:
                apex_start = p
            elif i == len(profile) - 1:
                apex_end = p
            else:
                raise ValueError("zero radius is only meaningful at a profile end")
            continue
        rings.append(_ring(p, right, up, r, r, chamfer))

    base = len(verts)
    n = len(rings[0])
    _loft(verts, tris, rings, cap_start=apex_start is None, cap_end=apex_end is None)
    for apex, idx, flip in ((apex_start, 0, True), (apex_end, len(rings) - 1, False)):
        if apex is None:
            continue
        a = len(verts)
        verts.append(apex)
        off = base + idx * n
        for i in range(n):
            j = (i + 1) % n
            tris.append((a, off + j, off + i) if flip else (a, off + i, off + j))


def _sweep(verts, tris, path, half, hint=Z, chamfer=0.4):
    """Sweep a small section along a polyline -- struts, barrels, cable runs."""
    rings = []
    for i, p in enumerate(path):
        d = _sub(path[min(i + 1, len(path) - 1)], path[max(i - 1, 0)])
        right, up = _frame(d, hint)
        rings.append(_ring(p, right, up, half, half, chamfer))
    _loft(verts, tris, rings, cap_start=True, cap_end=True)


def _slab(verts, tris, a, b, normal, half_wide, half_thick):
    """Flat plate running a -> b, lying in the plane `normal` is normal to.

    `half_wide` is measured across the plate inside that plane; `half_thick` is
    measured along `normal`. Naming them the other way round is how a structural
    fin becomes a wing without anything failing.
    """
    axis = _sub(b, a)
    inplane, thickwise = _frame(axis, normal)
    _loft(verts, tris,
          [_ring(a, inplane, thickwise, half_wide, half_thick, 0.0),
           _ring(b, inplane, thickwise, half_wide, half_thick, 0.0)],
          cap_start=True, cap_end=True)


def signed_volume(verts, tris):
    """Six times the enclosed volume. Positive iff the surface winds outward.

    The one property that catches a flipped loft without a renderer: an
    inside-out section is invisible rather than wrong-looking, so it survives
    visual inspection and fails here instead.
    """
    total = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        total += _dot(p, _cross(q, r))
    return total


# --- the airframe -----------------------------------------------------------
#
# Stations are (z, half-width, half-height, ...) in metres, body frame. Sizes
# come from two things and nothing else: the thruster anchors above, and the
# requirement that a reclined pilot fits inside the canopy.

FUSELAGE = (
    # z,   half_w, half_h, chamfer
    (-2.45, 0.50, 0.42, 0.42),
    (-1.75, 0.84, 0.63, 0.38),
    (-0.70, 1.00, 0.77, 0.34),
    (0.45, 0.96, 0.79, 0.32),
    (1.35, 0.74, 0.66, 0.32),
    (1.95, 0.50, 0.48, 0.36),
)

# The flat arrowhead deck the booms grow out of. It is what makes the craft read
# as one body with four arms rather than as four engines sharing a pod.
DORSAL_DECK = (
    # z,   half_w, half_thk, y
    (-2.00, 0.40, 0.07, 0.55),
    (-1.10, 0.70, 0.09, 0.68),
    (0.10, 0.78, 0.10, 0.75),
    (1.10, 0.60, 0.09, 0.73),
    (1.80, 0.38, 0.08, 0.64),
    (2.20, 0.17, 0.06, 0.54),
)

# Canopy stations. It rakes forward and down out from under the deck, which is
# the most recognisable thing about the craft from any front angle.
CANOPY = (
    # z,  half_w, half_h,   y
    (0.15, 0.66, 0.78, 0.00),
    (1.00, 0.72, 0.80, -0.14),
    (1.80, 0.66, 0.70, -0.36),
    (2.35, 0.46, 0.46, -0.70),
    (2.78, 0.19, 0.22, -0.94),
)

# Longitudinal span of the pressurised cockpit, inboard of the solid tip and of
# the bulkhead where the canopy meets the fuselage.
COCKPIT_SPAN_M = (0.20, 2.05)

# Which facets of the canopy section carry glazing, in _ring() index order: the
# upper ones and both flanks, so the pilot looks up, forward and out rather than
# through the floor. The set has to be closed under the port/starboard mirror
# (facet i reflects to facet 2 - i mod 8) or the craft comes out lopsided, which
# a test catches and no render would.
GLAZING_FACETS = (7, 0, 1, 2, 3)

BOOM_ROOT_RADIUS_M = 0.85      # diagonal radius where a boom leaves the hull
BOOM_ROOT_STATION_M = 2.15     # and how far forward that is
BOOM_BOW_M = 0.20              # forward bow at mid-span, zero at both ends

# Where a boom meets its nacelle. The nacelle is an axial cylinder carried on
# the boom's outboard end rather than a bulge in the boom itself, and the boom
# arrives on its inboard flank.
NACELLE_JOIN_RADIUS_M = 4.30
NACELLE_JOIN_STATION_M = -0.60

# Root fairing planform, as (diagonal radius, leading edge z, trailing edge z,
# half thickness). The trailing edge runs much further aft than the leading edge
# runs forward, so the fillet sweeps.
FAIRING = (
    (0.85, 2.30, -1.85, 0.16),
    (1.80, 1.85, -1.30, 0.12),
    (2.80, 1.15, -0.65, 0.09),
    (3.60, 0.55, -0.60, 0.07),
    (4.15, 0.05, -0.85, 0.06),
)

# Nacelle body profile as (z, radius), lathed about each engine's own position.
# The booms sit on the 45 deg diagonals, so that position is 4.81 m from the
# roll axis -- sqrt(2) times the 3.4 m x and y offset the flight model gives.
# The nacelle runs *along the roll axis*, which is what leaves room for the bell
# to project aft where it can be seen and where its plume is unobstructed.
# An earlier version ran the nacelle along the boom instead; from dead astern
# the craft then had no visible engines at all, which for a Starfury is the one
# view that has to be unmistakable. The forward end closes as a cup -- Burg
# draws open nozzle mouths at the outboard tips as well as at the tails.
NACELLE = (
    (-1.15, 0.40), (-0.85, 0.50), (-0.20, 0.54), (0.80, 0.53),
    (1.80, 0.50), (2.70, 0.45), (3.25, 0.38), (3.55, 0.30),
    (3.55, 0.25), (3.38, 0.16), (3.22, 0.0),
)

# The vaned tip assembly leaves the nacelle outboard and sweeps *forward*, given
# as (diagonal radius, z) endpoints. Forward rather than aft so that nothing
# crosses the engine plume or hides a bell from behind.
TIP_ROOT = (5.00, 1.75)
TIP_END = (6.40, 2.85)


def boom_axis(k):
    """Unit vector along boom k, plus its (thin, wide) plate frame and diagonal.

    The wide direction lies in the plane containing the boom axis and the roll
    axis, so fairings and vanes are edge-on from dead ahead. A plate in any
    other plane would be a wing, and the Aurora has none.
    """
    a = math.pi / 4 + k * math.pi / 2
    radial = (math.cos(a), math.sin(a), 0.0)
    root = _add(_mul(radial, BOOM_ROOT_RADIUS_M), (0.0, 0.0, BOOM_ROOT_STATION_M))
    tip = _add(_mul(radial, NACELLE_JOIN_RADIUS_M),
               (0.0, 0.0, NACELLE_JOIN_STATION_M))
    d = _unit(_sub(tip, root))
    thin, wide = _frame(d, Z)
    return d, thin, wide, radial


def boom_point(k, radius):
    """Point on boom k's axis at a given diagonal radius from the roll axis.

    Bowed forward at mid-span rather than dead straight. The on-screen frame
    shows the boom leaving the fuselage, sweeping out and then flattening toward
    the nacelle -- a dogleg, not a spoke -- and a straight spoke is the single
    thing that makes a four-armed craft read as a toy. The bow is zero at both
    ends by construction, so the root stays on the hull and the engine stays
    exactly on its mount point.
    """
    _d, _t, wide, radial = boom_axis(k)
    f = ((radius - BOOM_ROOT_RADIUS_M)
         / (NACELLE_JOIN_RADIUS_M - BOOM_ROOT_RADIUS_M))
    z = BOOM_ROOT_STATION_M + f * (NACELLE_JOIN_STATION_M - BOOM_ROOT_STATION_M)
    bow = BOOM_BOW_M * math.sin(math.pi * min(max(f, 0.0), 1.0))
    return _add(_add(_mul(radial, radius), (0.0, 0.0, z)), _mul(wide, bow))


def thruster_mounts():
    """Nozzle exit-plane centres, keyed by the flight model's thruster names.

    station/test_starfury_geometry.py asserts this equals the layout in
    station/physics/starfury.py `aurora_thrusters()`. Move a nacelle without
    moving its thruster and the test says so.
    """
    b, r = BOOM_HALF_SPAN_M, RCS_RING_RADIUS_M
    mounts = {}
    for sx in (1, -1):
        for sy in (1, -1):
            mounts[f"main_{'u' if sy > 0 else 'l'}{'r' if sx > 0 else 'l'}"] = (
                sx * b, sy * b, ENGINE_STATION_M)
    for sx in (1, -1):
        mounts[f"rcs_lat_{'r' if sx > 0 else 'l'}"] = (sx * r, 0.0, 0.0)
    for sy in (1, -1):
        mounts[f"rcs_vert_{'u' if sy > 0 else 'd'}"] = (0.0, sy * r, 0.0)
    mounts["rcs_retro"] = (0.0, 0.0, RETRO_STATION_M)
    return mounts


def canopy_section(z):
    """Interpolated (half_width, half_height, y_centre) of the canopy at z."""
    if z <= CANOPY[0][0]:
        return CANOPY[0][1:]
    for a, b in zip(CANOPY, CANOPY[1:]):
        if z <= b[0]:
            f = (z - a[0]) / (b[0] - a[0])
            return tuple(a[i] + f * (b[i] - a[i]) for i in (1, 2, 3))
    return CANOPY[-1][1:]


def cockpit_volume():
    """Clear volume inside the canopy, measured along the canopy's own rake.

    Derived from the canopy loft rather than written down, so changing a station
    moves it. It exists so the cockpit interior can later be built against a
    volume known to be inside the shell instead of against a remembered number.

    The pilot is **reclined, head forward** -- Burg draws the seat that way, and
    it is the posture that makes sense for a craft whose mains pull 1.87 g along
    its own long axis (station/physics/starfury.py): acceleration then goes
    through the seat back rather than head to foot. So the volume is reported
    along the canopy centreline, not as an axis-aligned box. An axis-aligned
    box would understate it by roughly a third and would be measuring a posture
    the craft does not use.
    """
    wall = 0.08                          # canopy skin and frame allowance
    z0, z1 = COCKPIT_SPAN_M
    hw = hh = 9.9
    for i in range(41):
        half_w, half_h, _y = canopy_section(z0 + (z1 - z0) * i / 40.0)
        hw, hh = min(hw, half_w - wall), min(hh, half_h - wall)
    y0, y1 = canopy_section(z0)[2], canopy_section(z1)[2]
    dz, dy = z1 - z0, y1 - y0
    return {
        "aft": (0.0, y0, z0),
        "forward": (0.0, y1, z1),
        "length_m": math.hypot(dz, dy),
        "width_m": 2.0 * hw,
        "height_m": 2.0 * hh,
        "rake_deg": math.degrees(math.atan2(-dy, dz)),
    }


def _fuselage():
    verts, tris = [], []
    _loft(verts, tris,
          [_ring((0.0, 0.0, z), X, Y, hw, hh, ch) for z, hw, hh, ch in FUSELAGE],
          cap_start=True, cap_end=True)
    return verts, tris


def _dorsal_deck():
    verts, tris = [], []
    _loft(verts, tris,
          [_ring((0.0, y, z), X, Y, hw, ht, 0.55) for z, hw, ht, y in DORSAL_DECK],
          cap_start=True, cap_end=True)
    return verts, tris


def _canopy_rings():
    return [_ring((0.0, y, z), X, Y, hw, hh, 0.36) for z, hw, hh, y in CANOPY]


def _canopy():
    verts, tris = [], []
    _loft(verts, tris, _canopy_rings(), cap_start=True, cap_end=True)
    return verts, tris


def _canopy_glazing():
    """Individual panes inset into the canopy facets.

    Separate section so the engine can give it a transparent material, and inset
    per pane so the frame between panes is real geometry rather than a texture
    seam -- the reference canopy is mostly frame.
    """
    verts, tris = [], []
    rings = _canopy_rings()
    axis_pts = [(0.0, y, z) for z, _hw, _hh, y in CANOPY]
    inset, proud, thick = 0.10, 0.015, 0.05
    for (a, b), (ca, cb) in zip(zip(rings, rings[1:]), zip(axis_pts, axis_pts[1:])):
        # Outward is taken from the canopy centreline rather than from the
        # facet's own corners. A quad spanning two loft stations is not planar,
        # so a corner-derived normal depends on which corner you start at -- and
        # a facet and its port/starboard mirror start at different corners,
        # which left the two sides of the canopy fractionally different.
        centre = _mul(_add(ca, cb), 0.5)
        for i in GLAZING_FACETS:
            j = (i + 1) % len(a)
            quad = (a[i], a[j], b[j], b[i])
            mid = tuple(sum(q[k] for q in quad) / 4.0 for k in range(3))
            n = _unit(_sub(mid, centre))
            shrunk = [_add(_mul(_sub(q, mid), 1.0 - inset), mid) for q in quad]
            base = len(verts)
            verts.extend(_add(q, _mul(n, proud)) for q in shrunk)
            verts.extend(_add(q, _mul(n, proud - thick)) for q in shrunk)
            for f in ((0, 1, 2), (0, 2, 3), (4, 7, 6), (4, 6, 5),
                      (4, 5, 1), (4, 1, 0), (5, 6, 2), (5, 2, 1),
                      (6, 7, 3), (6, 3, 2), (7, 4, 0), (7, 0, 3)):
                tris.append(tuple(base + q for q in f))
    return verts, tris


def _canopy_frame():
    """The strut cage: heavy chines down the canopy edges plus a transverse arch."""
    verts, tris = [], []
    rings = _canopy_rings()
    for i in (0, 1, 2, 3, 4, 7):
        _sweep(verts, tris, [r[i] for r in rings], 0.058)
    arch = rings[1]
    _sweep(verts, tris, [arch[k] for k in (7, 0, 1, 2, 3, 4)], 0.05)
    return verts, tris


def _nose():
    """Blunt forebody above the canopy, ending where the retro nozzle begins."""
    verts, tris = [], []
    _loft(verts, tris,
          [_ring((0.0, 0.0, z), X, Y, hw, hh, 0.4) for z, hw, hh in
           ((1.88, 0.46, 0.44), (2.14, 0.36, 0.34), (2.32, 0.25, 0.24))],
          cap_start=True, cap_end=True)
    return verts, tris


def _retro():
    """Forward-firing nozzle, exit plane exactly on the retro mount point.

    Burg's sheet draws open bell mouths facing forward as well as aft. That is
    what a craft with no preferred direction of travel needs, and it is the same
    nozzle the flight model calls rcs_retro.
    """
    verts, tris = [], []
    _revolve(verts, tris, (0.0, 0.0, 0.0), Z,
             ((2.02, 0.0), (2.08, 0.15), (2.24, 0.23), (RETRO_STATION_M, 0.29),
              (RETRO_STATION_M, 0.26), (2.26, 0.18), (2.14, 0.0)))
    return verts, tris


def _root_fairings():
    """Flat delta plates blending each boom into the fuselage.

    Structural fillets, not wings. Each lies in the plane spanned by its boom's
    radial direction and the roll axis -- the same plane the boom itself lies in
    -- so from dead ahead the whole assembly projects to a line. The leading
    edge rakes back and the trailing edge sweeps far aft, which is what gives
    the craft a body instead of four struts meeting at a point.
    """
    verts, tris = [], []
    for k in range(4):
        _d, _thin, _wide, radial = boom_axis(k)
        right, up = _frame(radial, Z)
        rings = []
        for span, z_le, z_te, thick in FAIRING:
            centre = _add(_mul(radial, span), (0.0, 0.0, (z_le + z_te) / 2.0))
            rings.append(_ring(centre, right, up, thick, (z_le - z_te) / 2.0, 0.45))
        _loft(verts, tris, rings, cap_start=True, cap_end=True)
    return verts, tris


def _booms():
    verts, tris = [], []
    for k in range(4):
        _d, thin, wide, _radial = boom_axis(k)
        _loft(verts, tris,
              [_ring(boom_point(k, radius), thin, wide, ht, hw, 0.4)
               for radius, ht, hw in ((1.10, 0.26, 0.46), (2.10, 0.22, 0.36),
                                      (3.20, 0.19, 0.28), (4.15, 0.18, 0.24))],
              cap_start=True, cap_end=True)
    return verts, tris


def _engine_pods():
    """Axial nacelle at each boom tip, ending forward in a retro nozzle cup."""
    verts, tris = [], []
    for sx in (1, -1):
        for sy in (1, -1):
            _revolve(verts, tris,
                     (sx * BOOM_HALF_SPAN_M, sy * BOOM_HALF_SPAN_M, 0.0), Z,
                     NACELLE)
    return verts, tris


def _engine_bells():
    """Main engine bells: axis along -z, exit plane on the mount point.

    Aligned with the roll axis rather than with their boom, because the flight
    model applies main thrust along +z. A bell pointing anywhere else would be a
    mesh that disagrees with the craft's own acceleration.
    """
    verts, tris = [], []
    for sx in (1, -1):
        for sy in (1, -1):
            centre = (sx * BOOM_HALF_SPAN_M, sy * BOOM_HALF_SPAN_M, 0.0)
            _revolve(verts, tris, centre, (0.0, 0.0, -1.0),
                     ((0.95, 0.0), (1.05, 0.31), (1.45, 0.44), (1.80, 0.58),
                      (-ENGINE_STATION_M, 0.70), (-ENGINE_STATION_M, 0.66),
                      (1.88, 0.50), (1.66, 0.32), (1.46, 0.0)))
    return verts, tris


def _tip_point(k, f):
    """Point along the outboard tip assembly of boom k, f in [0, 1]."""
    a = math.pi / 4 + k * math.pi / 2
    radial = (math.cos(a), math.sin(a), 0.0)
    r = TIP_ROOT[0] + f * (TIP_END[0] - TIP_ROOT[0])
    z = TIP_ROOT[1] + f * (TIP_END[1] - TIP_ROOT[1])
    return _add(_mul(radial, r), (0.0, 0.0, z)), radial


def _boom_tips():
    """Stub pylon carrying the vane comb outboard of each nacelle."""
    verts, tris = [], []
    for k in range(4):
        rings = []
        for f, r in ((0.0, 0.36), (0.30, 0.28), (0.48, 0.20)):
            p, radial = _tip_point(k, f)
            right, up = _frame(_unit(_sub(_tip_point(k, 1.0)[0],
                                          _tip_point(k, 0.0)[0])), radial)
            rings.append(_ring(p, right, up, r, r, 0.6))
        _loft(verts, tris, rings, cap_start=True, cap_end=True)
    return verts, tris


def _tip_vanes():
    """The comb of flat fingers outboard of each nacelle.

    Radiator and sensor vanes, lying in the plane spanned by their boom's radial
    direction and the roll axis -- edge-on from dead ahead, like everything else
    out there. Three fingers with narrow gaps rather than one plate, because a
    solid plate this size would read as a wing and this craft has none.
    """
    verts, tris = [], []
    for k in range(4):
        a0, radial = _tip_point(k, 0.30)
        a1, _ = _tip_point(k, 1.0)
        axis = _unit(_sub(a1, a0))
        tangential = _unit(_cross(radial, Z))       # normal to the meridional plane
        inplane = _unit(_cross(tangential, axis))   # in-plane, across the run
        for offset, shorten in ((-0.32, 0.22), (0.0, 0.0), (0.32, 0.22)):
            a = _add(a0, _mul(inplane, offset))
            b = _add(_add(a1, _mul(inplane, offset)), _mul(axis, -shorten))
            _slab(verts, tris, a, b, tangential, 0.145, 0.035)
    return verts, tris


def _rcs_sponsons():
    """Slender outriggers carrying the lateral and vertical RCS quads.

    The flight model puts those four thrusters 3.4 m off the axis on the
    *cardinal* meridians -- between the booms, not on them -- so a nozzle out
    there needs something to be bolted to. Burg draws stalked nozzle cylinders
    radiating from the hub between the boom roots, which is the same idea at a
    smaller scale.

    They are deliberately thin rods with a faired root rather than plates.
    A first pass built them as tapering fins and the craft read from dead ahead
    as an eight-armed asterisk instead of an X, which is the one silhouette a
    Starfury must never have. Reach is fixed by the flight model; visual mass is
    not, so visual mass is what got cut.

    Worth recording: these four mount points contribute **zero torque** in the
    flight model -- their thrust vectors are parallel to their own position
    vectors, so the cross product vanishes. Their radius is therefore inert
    physically and matters only here, which is why it can be honoured exactly
    without arguing about it.
    """
    verts, tris = [], []
    for radial in (X, (-1.0, 0.0, 0.0), Y, (0.0, -1.0, 0.0)):
        right, up = _frame(radial, Z)
        _loft(verts, tris,
              [_ring(_mul(radial, r), right, up, s, s * a, 0.62)
               for r, s, a in ((0.70, 0.26, 1.45), (1.15, 0.16, 1.30),
                               (2.20, 0.105, 1.15), (3.02, 0.085, 1.0))],
              cap_start=True, cap_end=True)
    return verts, tris


def _rcs_nozzles():
    """RCS bells, exit plane on the mount point, opening outward.

    Outward because the flight model's lateral and vertical thrusters push
    *inward* -- rcs_lat_r sits at +x and applies force along -x -- so the plume
    has to leave the craft rather than enter it.
    """
    verts, tris = [], []
    r = RCS_RING_RADIUS_M
    for radial in (X, (-1.0, 0.0, 0.0), Y, (0.0, -1.0, 0.0)):
        _revolve(verts, tris, (0.0, 0.0, 0.0), radial,
                 ((2.94, 0.0), (3.00, 0.10), (3.22, 0.15), (r, 0.18),
                  (r, 0.155), (3.26, 0.10), (3.14, 0.0)))
    return verts, tris


def _gun_pod():
    """Ventral weapon package under the forebody, with two forward barrels."""
    verts, tris = [], []
    _loft(verts, tris,
          [_ring((0.0, y, z), X, Y, hw, hh, 0.38) for z, hw, hh, y in
           ((-0.65, 0.32, 0.19, -1.08), (0.10, 0.46, 0.25, -1.20),
            (0.90, 0.42, 0.23, -1.24), (1.45, 0.28, 0.16, -1.20))],
          cap_start=True, cap_end=True)
    for sx in (1, -1):
        _sweep(verts, tris,
               [(sx * 0.29, -1.21, 1.35), (sx * 0.29, -1.18, 2.10)],
               0.075, hint=Y, chamfer=0.6)
    return verts, tris


SECTIONS = (
    ("fuselage", _fuselage),
    ("dorsal_deck", _dorsal_deck),
    ("nose", _nose),
    ("retro_nozzle", _retro),
    ("cockpit_canopy", _canopy),
    ("cockpit_glazing", _canopy_glazing),
    ("canopy_frame", _canopy_frame),
    ("root_fairing", _root_fairings),
    ("boom", _booms),
    ("engine_pod", _engine_pods),
    ("engine_bell", _engine_bells),
    ("boom_tip", _boom_tips),
    ("tip_vane", _tip_vanes),
    ("rcs_sponson", _rcs_sponsons),
    ("rcs_nozzle", _rcs_nozzles),
    ("gun_pod", _gun_pod),
)


def build():
    """Return {section_name: (verts, tris)}.

    Named sections rather than one welded blob, so the cockpit can be entered
    later: the canopy, its glazing and its frame are addressable on their own,
    which is what a switch to an interior view needs.
    """
    return {name: fn() for name, fn in SECTIONS}


def write_obj(path, sections):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Aurora-class Starfury -- generated by station/starfury_geometry.py\n")
        f.write("# Do not edit by hand. Thruster mounts are shared with "
                "station/physics/starfury.py\n")
        offset, blocks = 0, []
        for name, (verts, tris) in sections.items():
            for x, y, z in verts:
                f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            blocks.append((name, tris, offset))
            offset += len(verts)
        for name, tris, base in blocks:
            f.write(f"g {name}\no {name}\n")
            for a, b, c in tris:
                f.write(f"f {a+base+1} {b+base+1} {c+base+1}\n")


def manifest(sections):
    verts = [v for s in sections.values() for v in s[0]]
    xs, ys, zs = ([v[i] for v in verts] for i in range(3))
    cockpit = cockpit_volume()
    return {
        "source": "station/starfury_geometry.py",
        "frame": "+z forward, +y up, +x starboard (matches station/physics/starfury.py)",
        "sections": {k: len(v[1]) for k, v in sections.items()},
        "vertices": len(verts),
        "triangles": sum(len(v[1]) for v in sections.values()),
        "bounds": {
            "length_m": round(max(zs) - min(zs), 3),
            "span_x_m": round(max(xs) - min(xs), 3),
            "span_y_m": round(max(ys) - min(ys), 3),
            "z": [round(min(zs), 3), round(max(zs), 3)],
        },
        "thruster_mounts": {k: [round(c, 4) for c in v]
                            for k, v in thruster_mounts().items()},
        "cockpit_clear_volume_m": {
            "length": round(cockpit["length_m"], 3),
            "width": round(cockpit["width_m"], 3),
            "height": round(cockpit["height_m"], 3),
            "rake_deg": round(cockpit["rake_deg"], 1),
        },
    }


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--out",
                    default=os.path.join(root, "station/generated/starfury.obj"))
    a = ap.parse_args()

    sections = build()
    write_obj(a.out, sections)
    man = manifest(sections)
    with open(os.path.join(os.path.dirname(a.out), "starfury_manifest.json"), "w") as f:
        json.dump(man, f, indent=1)
    print(json.dumps(man, indent=1))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
