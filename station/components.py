"""Generate the station's non-axisymmetric components.

The hull lathe cannot produce anything that is not a surface of revolution, so
the fins, solar arrays, communications grid, cobra bays and cargo modules are
built here as parametric primitives placed against the longitudinal framework.

Every component attaches to the hull at the radius the profile reports for its
z, so components stay welded to the hull automatically when the profile changes.
That is the same by-construction consistency that keeps interior and exterior
in agreement -- there is no second source of truth to drift.
"""
import math


def _box(verts, tris, corners):
    """Append an axis-agnostic box given 8 corners in the standard order.

    Winding is outward. It was inward for the first several sessions of
    exterior work and nothing caught it, because a closed solid has the same
    silhouette either way -- the renderer simply culled the near faces instead
    of the far ones and shaded the inside of the far wall. Proportions judged
    from those renders were still right; the lighting was not.

    A unit cube through this function must have signed volume +1, which
    _selftest_winding() asserts.
    """
    b = len(verts)
    verts.extend(corners)
    for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        tris.append((b + a, b + d, b + c))
        tris.append((b + a, b + e, b + d))


def signed_volume(verts, tris):
    """Six-times signed volume of a closed mesh. Positive means outward winding.

    The cheapest possible check that a solid is not inside-out, and the one
    that would have caught _box four sessions earlier.
    """
    v6 = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        v6 += (p[0] * (q[1] * r[2] - q[2] * r[1])
               - p[1] * (q[0] * r[2] - q[2] * r[0])
               + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return v6 / 6.0


def _slab(verts, tris, origin, eu, ev, ew):
    """A box from one corner and three edge vectors, outward-wound.

    `_box`'s eight-corner convention is correct and unreadable: every caller
    above builds a quad, reorders it into 0,1,3,2, then offsets it, and the
    two components whose winding was inside-out for four sessions both got it
    wrong at exactly that step. This takes a corner and three edges instead,
    which is the form the cobra bays are actually described in -- so much
    across the hull, so much along the axis, so much radially out.

    Winding is outward iff (eu, ev, ew) is RIGHT-HANDED, i.e. eu x ev . ew > 0.
    That is not a convention to remember, it is a determinant, and
    `_selftest_winding` feeds it a left-handed triple to prove the sign
    actually follows it rather than being positive for every input.
    """
    ox, oy, oz = origin

    def p(a, b, c):
        return (ox + a * eu[0] + b * ev[0] + c * ew[0],
                oy + a * eu[1] + b * ev[1] + c * ew[1],
                oz + a * eu[2] + b * ev[2] + c * ew[2])

    _box(verts, tris, [p(0, 0, 0), p(1, 0, 0), p(1, 1, 0), p(0, 1, 0),
                       p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1)])


def _selftest_winding():
    v, t = [], []
    _box(v, t, [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)])
    vol = signed_volume(v, t)
    if abs(vol - 1.0) > 1e-9:
        raise AssertionError(
            f"_box winding is inside-out: unit cube signed volume {vol:+.3f}, expected +1.000")

    # _slab must agree with _box on the same cube, and must REVERSE when the
    # frame does. Without the second half this assertion cannot fail for a
    # winding reason -- it would pass just as happily if _slab ignored its
    # edge vectors and emitted a fixed cube.
    v, t = [], []
    _slab(v, t, (0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 5))
    right = signed_volume(v, t)
    v, t = [], []
    _slab(v, t, (0, 0, 0), (0, 3, 0), (2, 0, 0), (0, 0, 5))     # left-handed
    left = signed_volume(v, t)
    if abs(right - 30.0) > 1e-9 or abs(left + 30.0) > 1e-9:
        raise AssertionError(
            f"_slab winding does not follow its frame: right-handed {right:+.3f} "
            f"(expected +30.000), left-handed {left:+.3f} (expected -30.000)")


_selftest_winding()


def radius_at(profile, z):
    """Hull radius at a given z, by nearest sample."""
    lo, hi = 0, len(profile) - 1
    if z <= profile[0]["z_m"]:
        return profile[0]["radius_m"]
    if z >= profile[hi]["z_m"]:
        return profile[hi]["radius_m"]
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if profile[mid]["z_m"] < z:
            lo = mid
        else:
            hi = mid
    return profile[lo]["radius_m"]


def radial_array(spec, profile):
    """N flat plates arrayed around the axis, extending radially outward.

    Used for the reactor cooling fins and the heat-exchange / solar arrays.
    Radiators must face empty space rather than each other, so the plates lie
    in planes containing the axis -- the configuration that actually radiates.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    span, chord, th = spec["span_m"], spec["chord_m"], spec["thickness_m"] / 2.0
    # The Contract 5 profile shows the radiators as a small number of discrete
    # assemblies along the spine, not one crowded ring. With a total count of 12
    # that reconciles to 3 assemblies of 4 -- which is also why 12 appears in the
    # Exterior map as a single figure covering the whole system.
    n_rings = spec.get("rings", 1)
    per_ring = max(1, spec["count"] // n_rings)

    for idx in range(spec["count"]):
        ring = idx // per_ring
        i = idx % per_ring
        zc = (z0 + (z1 - z0) * (ring + 0.5) / n_rings) if n_rings > 1 else (z0 + z1) / 2.0
        r0 = radius_at(profile, zc)
        za, zb = zc - chord / 2.0, zc + chord / 2.0
        # Clock successive assemblies so they do not line up down the spine.
        a = 2.0 * math.pi * i / per_ring + ring * math.pi / per_ring
        ca, sa = math.cos(a), math.sin(a)
        # Radial direction (outward) and tangential direction (plate thickness).
        rx, ry = ca, sa
        tx, ty = -sa, ca
        inner, outer = r0 * 0.92, r0 + span
        corners = []
        for rr in (inner, outer):
            for zz in (za, zb):
                corners.append((rx * rr - tx * th, ry * rr - ty * th, zz))
        # Reorder into the box corner convention: bottom quad then top quad.
        c = [corners[0], corners[1], corners[3], corners[2]]
        c += [(x + 2 * tx * th, y + 2 * ty * th, z) for x, y, z in c]
        _box(verts, tris, c)
        # RADIAL STIFFENERS. The last flat-plate builder without them: these
        # are the reactor cooling fins and the heat-exchange arrays, and a
        # radiator plate spanning `span` metres with two outline edges is the
        # same defect `swept_fins` and `planar_blades` had.
        for rk in range(1, _ribs(ARRAY_RIBS) + 1):
            zz = za + (zb - za) * rk / (ARRAY_RIBS + 1)
            for face in (-1, 1):
                off = th + ARRAY_RIB_P_M / 2.0
                rq = []
                for rr in (inner, outer):
                    rq.append((rx * rr + tx * face * off,
                               ry * rr + ty * face * off,
                               zz - ARRAY_RIB_W_M / 2))
                    rq.append((rx * rr + tx * face * off,
                               ry * rr + ty * face * off,
                               zz + ARRAY_RIB_W_M / 2))
                rq = [rq[0], rq[1], rq[3], rq[2]]
                rq += [(x + tx * face * ARRAY_RIB_P_M,
                        y + ty * face * ARRAY_RIB_P_M, z) for x, y, z in rq]
                _box(verts, tris, rq)
    return verts, tris


# --- the deep space communications grid -------------------------------------
#
# WHAT WAS WRONG. Each pylon was TWO BOXES -- 24 triangles, 12 facets, a 517.6
# m unbroken face, visible line density 0.0120 m^-1, the lowest number anywhere
# in this file. Its own docstring said the grid "is the widest structure on the
# station ... so it dominates the silhouette from any angle and is worth
# placing precisely"; it was placed precisely and never built. At the rubric's
# half distance (docs/craft-4r-ext-pylon-before-half.png) it is a featureless
# plank on a featureless stick.
#
# WHAT THE REFERENCE SHOWS, and it decides the SHAPE rather than the size.
# `01-station-exterior/exterior more.jpg` is authority 2 and carries BOTH end
# views. In each of them the grid reads as a **short dark stub arm at the
# equator carrying a very long, very hairline-thin mast** running perpendicular
# to it -- 2 to 3 px of width against a hull some 370 px across at that
# magnification -- and there is **no broad panel anywhere on it**. 00-INDEX
# records the same reading twice, independently: "two very long thin masts run
# vertically far beyond the hull silhouette in *both* end views, and two
# shorter stub arms project laterally at the equator", and for the Miller
# sheet, "long thin masts extend beyond the hull at spine level toward the
# fore end".
#
# WHAT IS NOT CHANGED, AND WHY. `span_m` 1,060.25 and `grid_width_m` 893.2 are
# schema numbers off `canon/00-MASTER.md`'s rescaled specification table and
# they stay exactly as they are: the span is corroborated (2,120.5 m tip to tip
# against masts that visibly overrun the hull in both end views), and the width
# is AMBIGUOUS in a way that is not mine to resolve -- see INV-584. So the
# extent of this component is untouched and only its CONSTRUCTION changes.
#
# A GRID IS A LATTICE. That is what the word means, it is what the end views
# are consistent with -- an open framework of thin members reads as thin masts
# at 100 km and a solid 893 x 300 m plate does not -- and it is what turns 24
# triangles into a structure with three tiers. Primary: two booms at the inner
# and outer radius plus two end posts, 26 m. Secondary: the radial ribs that
# divide it into bays, 14 m. Tertiary: one diagonal brace per bay, 9 m. The
# aperture between them is open, which is the point: a communications grid that
# is solid is a billboard. INV-583.
GRID_RIBS = 9                  # radial ribs dividing the grid into bays
GRID_BOOM_FRAC = 0.055         # boom section / panel depth
GRID_RIB_FRAC = 0.030          # rib section / panel depth
GRID_BRACE_FRAC = 0.019        # diagonal brace section / panel depth
GRID_BAY_BIAS = 1.45           # >1 bunches the bays where the mast meets the
                               # grid, which is where the shear is
MAST_SEGMENTS = 6              # tapering lengths between collars
MAST_TIP_FRAC = 0.42           # tip section as a fraction of the root's


def pylon_pair(spec, profile):
    """Two opposed masts carrying the deep-space communications grid.

    The grid is the widest structure on the station -- 2,120 m tip to tip,
    against a hull that is under 1 km at its broadest -- so it dominates the
    silhouette from any angle and is worth building as well as placing.

    Built in the mast's own (tangential, axial, radial) frame, which is
    RIGHT-HANDED -- u_t x u_z = u_r -- so every member takes positive extents
    and comes out wound outward.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    zc = (z0 + z1) / 2.0
    r0 = radius_at(profile, zc)
    span, gw = spec["span_m"], spec["grid_width_m"]
    th = spec["thickness_m"] / 2.0
    depth = spec.get("panel_depth_m", 90)

    for i in range(spec["count"]):
        # On +/-X, not +/-Y: the grid must not be edge-on to the North/South
        # docking axis, which is where traffic approaches from.
        a = 2.0 * math.pi * i / spec["count"]
        ca, sa = math.cos(a), math.sin(a)

        def put(t0, dt, dz0, dz, r_at, dr, _ca=ca, _sa=sa):
            _cargo_put((verts, tris), _ca, _sa, 0.0, zc, t0, dt, dz0, dz,
                       r_at, dr)

        root_r, tip_r = r0 * 0.9, r0 + span
        # --- the stub arm: the heavy root bracket the end views show ---------
        # A mast 1,060 m long does not bolt straight to plate. The bracket is
        # three stepping blocks, widest at the hull, and it is the only part of
        # this component that is thicker than the mast.
        brk = tip_r - root_r
        for k, (f0, f1, wide) in enumerate((
                (0.00, 0.045, 3.4), (0.045, 0.085, 2.3), (0.085, 0.125, 1.5))):
            put(-th * wide, 2.0 * th * wide, -40.0 * wide, 80.0 * wide,
                root_r + brk * f0, brk * (f1 - f0))

        # --- the mast: tapering segments with a collar at every joint --------
        m0, m1 = root_r + brk * 0.125, tip_r - depth
        for k in range(MAST_SEGMENTS):
            f0, f1 = k / MAST_SEGMENTS, (k + 1) / MAST_SEGMENTS
            s0 = 1.0 - (1.0 - MAST_TIP_FRAC) * f0
            ra, rb = m0 + (m1 - m0) * f0, m0 + (m1 - m0) * f1
            put(-th * s0, 2.0 * th * s0, -40.0 * s0, 80.0 * s0, ra, rb - ra)
            # The collar. It is what makes a long thin member read as built
            # rather than extruded, and it is where the taper steps.
            if k < MAST_SEGMENTS - 1:
                s1 = 1.0 - (1.0 - MAST_TIP_FRAC) * f1
                put(-th * s1 * 1.55, 2.0 * th * s1 * 1.55,
                    -40.0 * s1 * 1.25, 80.0 * s1 * 1.25,
                    rb - (m1 - m0) * 0.012, (m1 - m0) * 0.024)

        # --- the grid: an open lattice, not a plate --------------------------
        boom = GRID_BOOM_FRAC * depth
        rib = GRID_RIB_FRAC * depth
        brace = GRID_BRACE_FRAC * depth
        gt = th * 0.9                 # the lattice is thinner than the mast
        pw = gw / 2.0
        r_in, r_out = tip_r - depth, tip_r
        # two booms along the axis, at the inner and outer radius
        for r_at in (r_in, r_out - boom):
            put(-gt, 2.0 * gt, -pw, gw, r_at, boom)
        # two end posts, radial, closing the frame
        for sz in (-1.0, +1.0):
            put(-gt, 2.0 * gt, sz * pw if sz > 0 else -pw, boom,
                r_in + boom, depth - 2.0 * boom)
        # ribs dividing it into bays, and one diagonal brace per bay
        # BAYS ARE NOT EVENLY SPACED, and that is structural rather than
        # decorative. The mast meets the grid at its MID-SPAN, so that is where
        # the shear is highest and where a real truss puts its bays closest
        # together. Spacing them by |2f-1|^GRID_BAY_BIAS does exactly that, and
        # it costs one line. It also removes the only thing about this
        # component the eye could index -- ten identical bays is a ladder, and
        # AAA-STANDARD's C4 asks that a specialist find the repeat and nobody
        # else. `_bay_f` is used for the ribs and the braces alike so the two
        # cannot disagree about where a bay boundary is.
        nrib = _ribs(GRID_RIBS)
        bays = nrib + 1

        def _bay_f(k, n=bays):
            f = k / n
            s = -1.0 if f < 0.5 else 1.0
            return 0.5 + s * 0.5 * abs(2.0 * f - 1.0) ** GRID_BAY_BIAS

        for k in range(nrib):
            zz = -pw + gw * _bay_f(k + 1) - rib / 2.0
            put(-gt, 2.0 * gt, zz, rib, r_in + boom, depth - 2.0 * boom)
        inner_d = depth - 2.0 * boom
        for k in range(bays):
            za = -pw + gw * _bay_f(k)
            zb = -pw + gw * _bay_f(k + 1)
            # Alternating diagonal: a Warren brace, which is what carries shear
            # in a boom this slender and what stops the bays reading as a
            # ladder. Built through `_ribbon` because it is the one member here
            # that is not axis-aligned.
            p0 = (ca * (r_in + boom) - sa * 0.0, sa * (r_in + boom) + ca * 0.0,
                  zc + (za if k % 2 == 0 else zb))
            p1 = (ca * (r_in + boom + inner_d) - sa * 0.0,
                  sa * (r_in + boom + inner_d) + ca * 0.0,
                  zc + (zb if k % 2 == 0 else za))
            _ribbon(verts, tris, p0, p1, (0.0, 0.0, 1.0), brace, 2.0 * gt,
                    (ca, sa, 0.0))
    return verts, tris


# --- cobra bays -------------------------------------------------------------
#
# WHAT WAS WRONG. Each of the 28 bays was ONE BOX standing 26 m proud of the
# hull -- a smooth blister. `01-station-exterior/Cobra Bays with
# starfurries.webp` is authority 1 and shows the opposite: a deep structural
# WELL that you look into, framed by heavy chamfered box columns with red
# beacons at their heads and files of marker lights down their inner faces,
# with chevron-nosed deck ledges inside and a launch arm lying in it. A
# blister and a well have the same silhouette from 9 km and nothing in common
# from 400 m, which is where the arrival shot ends up.
#
# THE ONE MEASUREMENT. That frame has no scale anchor -- no figure, no
# caption, and INV-008 already records that `01-station-exterior/` holds no
# authority-1 exterior at all. What it does carry is a RATIO, and a ratio
# survives having no scale. Measured at native 843x474: the two framing
# columns read 57 px wide with 136 px of clear opening between them, so a
# column is 57/250 = 0.228 of the bay unit and the clear mouth is 0.544 of it.
# Rounded to 0.23, with the clear falling out as 1 - 2x0.23 = 0.54, which is
# the measured 0.544 to within the width of one pixel at that magnification.
#
# Everything else is proportion, and INV-040 says which numbers those are and
# which one is weak. The weak one is the bay's AXIAL length: no source gives
# it, and 42 m is inherited from the box this replaces, where it was an
# artefact of `2 * (width/2)` rather than a measurement of anything.
FIN_RIBS = 14                  # INV-073: chordwise stiffeners on a radiator blade
FIN_RIB_W_M = 1.4
FIN_RIB_P_M = 0.55
PLATE_RIBS = 11
PLATE_RIB_W_M = 1.6
PLATE_RIB_P_M = 0.7
BLADE_RIBS = 11
BLADE_RIB_W_M = 1.8
BLADE_RIB_P_M = 0.6
ARRAY_RIBS = 6
ARRAY_RIB_W_M = 1.5
ARRAY_RIB_P_M = 0.6
COBRA_COLUMN_FRAC = 0.23      # column width / bay unit width, measured, see above
COBRA_BEAM_FRAC = 0.50        # head and sill beam depth, as a fraction of a column
COBRA_CAPITAL_FRAC = 1.14     # capital oversails its column by 7% each side
COBRA_PLINTH_FRAC = 1.14      # and the plinth by the same
COBRA_SHAFT_FRAC = 0.82       # the column steps in above the sill
COBRA_SHAFT_RISE = 0.55       # where it steps, as a fraction of the protrusion
COBRA_BEAM_RISE = 0.58        # sill and lintel are LOW ties, not walls
COBRA_FLOOR_CLEAR_M = 1.6     # well floor above the hull: clears +/-1.3 m of plate jitter


def cobra_bay_ring(spec, profile):
    """The cobra bays: a ring of framed structural wells, not a ring of boxes.

    Returns FIVE groups, because a bay is not one surface. The frame, the well
    liner, the hazard lip and the two light families are five materials, and
    emitting them as one group is what left `cobra_bay` on the exterior
    fallback for eleven sessions with nowhere for `marker_light_red` -- a
    material measured off THIS frame's column beacons -- to land.

    Placement is unchanged from the box it replaces: `count` bays in
    `ceil(count / per_ring)` rings, successive rings clocked half a pitch so
    they do not line up down the spine. Placement is layer-1 work and was
    signed off; this is layer-2 work on the same footprint.

    The bay is built on a flat chord rather than curved to the hull. At the
    aft ring's 167 m radius a 42 m chord has a sagitta of 1.3 m, against a
    frame whose root reaches at least 6 m below the hull -- `root_drop` below
    -- so the chord never lifts off it.
    """
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    prot, w = spec["protrusion_m"], spec["width_m"]
    length = spec.get("length_m", w)
    sink = spec.get("sink_m", 6.0)

    col_w = COBRA_COLUMN_FRAC * w
    clear_u = w - 2.0 * col_w
    beam_d = COBRA_BEAM_FRAC * col_w
    clear_z = length - 2.0 * beam_d

    frame = ([], [])
    well = ([], [])
    lip = ([], [])
    beacon = ([], [])
    marker = ([], [])

    # Distribute around the circumference and along z together, so a large
    # count wraps into several rings rather than crowding one.
    per_ring = min(n, spec.get("per_ring", 14))
    rings = max(1, math.ceil(n / per_ring))
    placed = 0
    for ring in range(rings):
        zc = z0 + (z1 - z0) * (ring + 0.5) / rings
        za, zb = zc - length / 2.0, zc + length / 2.0
        # The hull flares hard through this band -- 167 m at z 7050 and 269 m
        # at z 7180 -- so a bay sized off the radius at its CENTRE hangs in
        # space at one end and buries itself at the other. Take the extremes
        # over the bay's own z span: the frame roots below the lowest hull
        # under it and the well floor sits above the highest.
        span = [radius_at(profile, za + (zb - za) * f / 8.0) for f in range(9)]
        r_lo, r_hi = min(span), max(span)
        # The bay FOLLOWS the hull instead of sitting on one radius. Sizing it
        # off the radius at its centre buried the fore end; sizing it off the
        # maximum stood the aft end 51 m proud of a hull the schema says the
        # bay clears by 26. Both are wrong for the same reason: this band
        # flares 25 m inside a single bay's length, and a flat-bottomed box on
        # a flare has to be wrong at one end. The datum is therefore the line
        # between the hull radii at the bay's own two ends, and `protrusion_m`
        # is measured from it -- so the mouth tilts with the hull and stays
        # exactly 26 m clear of it all the way along.
        r_a, r_b = radius_at(profile, za), radius_at(profile, zb)
        # The datum runs above the hull wherever the hull dips below the line
        # between its ends, by at most the flare across the span. Sinking the
        # frame's root by that much plus the nominal 6 m guarantees it reaches
        # the hull everywhere rather than only at its ends.
        root_drop = sink + (r_hi - r_lo)

        k = min(per_ring, n - placed)
        # The widest thing in a bay is not `width_m`: the plinths oversail
        # their columns, so the envelope is width + (plinth - 1) x column. Two
        # bays whose envelopes overlap interpenetrate, and interpenetration at
        # this scale is a 4 m seam of coplanar faces that z-fights in every
        # frame. A box primitive could not collide with its neighbour because
        # it was half the width it should have been; this one can.
        pitch = 2.0 * math.pi * r_lo / k
        envelope = w + (COBRA_PLINTH_FRAC - 1.0) * col_w
        if envelope >= pitch:
            raise ValueError(
                f"cobra bay envelope {envelope:.1f} m does not fit the "
                f"{pitch:.1f} m arc pitch of {k} bays at r={r_lo:.0f} m")
        for i in range(k):
            a = 2.0 * math.pi * i / k + ring * math.pi / max(1, per_ring)
            _cobra_bay(frame, well, lip, beacon, marker, a, zc,
                       length, w, col_w, clear_u, beam_d, clear_z,
                       (za, r_a, zb, r_b), root_drop, prot)
            placed += 1

    return {
        spec["id"]: frame,
        spec["id"] + "_well": well,
        # `hazard_stripe` is materials.py's fragment for the yellow-and-black
        # diagonal, and its note has said "no geometry carries this group yet"
        # since session 2m. It does now.
        "hazard_stripe_cobra": lip,
        "cobra_beacon_red": beacon,
        "cobra_marker_white": marker,
    }


def _cobra_bay(frame, well, lip, beacon, marker, a, zc,
               length, w, col_w, clear_u, beam_d, clear_z,
               datum, root_drop, prot):
    """One bay, in the local frame (u across the hull, z along it, r outward).

    (u, z, r) is right-handed -- u x z = r for u = (-sin a, cos a, 0) -- so
    every box below takes positive extents and comes out wound outward. That
    is why the whole bay is written in this order and not another.

    `datum` is (za, r_a, zb, r_b): the hull line the bay is built on, so every
    radius here is an OFFSET FROM THE HULL rather than an absolute radius, and
    the bay tilts with the hull instead of cutting into it.
    """
    ca, sa = math.cos(a), math.sin(a)
    za, r_a, zb, r_b = datum
    slope = (r_b - r_a) / (zb - za)

    def put(part, u0, du, z_off, dz, r_off, dr):
        """Place a box. `u0` is the offset from the bay's centre line and
        `r_off` the offset from the hull datum at that box's own z."""
        if du <= 0 or dz <= 0 or dr <= 0:
            raise ValueError(f"cobra bay box has a non-positive extent: "
                             f"du={du} dz={dz} dr={dr}")
        z_lo, z_hi = zc + z_off, zc + z_off + dz
        r_lo = r_a + slope * (z_lo - za) + r_off
        r_hi = r_a + slope * (z_hi - za) + r_off

        def P(u, zz, rr):
            return (ca * rr - sa * u, sa * rr + ca * u, zz)

        quad = [P(u0, z_lo, r_lo), P(u0 + du, z_lo, r_lo),
                P(u0 + du, z_hi, r_hi), P(u0, z_hi, r_hi)]
        quad += [P(u0, z_lo, r_lo + dr), P(u0 + du, z_lo, r_lo + dr),
                 P(u0 + du, z_hi, r_hi + dr), P(u0, z_hi, r_hi + dr)]
        _box(part[0], part[1], quad)

    # Offsets from the hull datum, not radii.
    r_root = -root_drop
    r_floor = COBRA_FLOOR_CLEAR_M
    r_mouth = prot
    depth = r_mouth - r_root
    # --- the frame: two columns, two beams, capitals and plinths -----------
    # THE COLUMNS ARE THE TALL THING. The first build ran the columns and the
    # beams to the same radius, and face-on that is one flat 42 x 42 m plate
    # with a hole in it -- no relief anywhere, which is exactly what a box
    # primitive looks like and exactly what this rebuild is for. In the
    # reference the column heads are the highest thing in frame, the beacons
    # sit on them, and the sill and lintel are low ties between them. So the
    # beams stop at COBRA_BEAM_RISE of the protrusion and the columns go all
    # the way, stepping in to a narrower shaft on the way.
    #
    # Fittings are proportioned against the VISIBLE height, `prot`, not
    # against `depth`. Depth now carries `root_drop`, which is however far the
    # frame has to reach to find the hull under a bay -- 31 m at the aft ring
    # -- and scaling a capital off that put 34.5 m of column above a hull the
    # schema says the bay clears by 26. `_selftest` measures it.
    cap_rise = 0.13 * prot
    r_step = COBRA_SHAFT_RISE * prot
    for side in (-1.0, +1.0):
        u_in = side * clear_u / 2.0                       # inner face
        u0 = min(u_in, u_in + side * col_w)               # low-u corner
        put(frame, u0, col_w, -length / 2.0, length, r_root, depth - prot + r_step)
        shaft = COBRA_SHAFT_FRAC * col_w
        put(frame, u0 + (col_w - shaft) / 2.0, shaft,
            -length / 2.0, length, r_step, prot - r_step)
        # Plinth and capital, both centred on the column. The plinth stands on
        # the HULL, not on the column's root: the root is `sink` metres inside
        # the hull, so a plinth measured from there is buried in it and the
        # first version of this built eight metres of invisible geometry.
        for frac, r_at, rise in ((COBRA_PLINTH_FRAC, r_floor, 0.22 * prot),
                                 (COBRA_CAPITAL_FRAC, r_mouth, cap_rise)):
            wide = frac * col_w
            put(frame, u0 - (wide - col_w) / 2.0, wide,
                -length / 2.0, length, r_at, rise)
    for z_side in (-1.0, +1.0):
        z_in = z_side * clear_z / 2.0
        z_off = min(z_in, z_in + z_side * beam_d)
        put(frame, -w / 2.0, w, z_off, beam_d,
            r_root, depth - prot + COBRA_BEAM_RISE * prot)

    # --- the well: a liner inset from the frame, its floor, its ledges -----
    # The liner is a separate skin 0.4 m inside the frame rather than the
    # frame's own inner faces. It buys two things for 48 triangles: a reveal
    # shadow line round the mouth, and a surface the well can be darker on
    # without darkening the columns that catch the key light.
    inset = 0.40
    liner_t = 0.9
    r_liner = r_floor
    liner_h = r_mouth - r_floor
    for side in (-1.0, +1.0):
        u_face = side * (clear_u / 2.0 - inset)
        u0 = min(u_face, u_face - side * liner_t)
        put(well, u0, liner_t, -clear_z / 2.0, clear_z, r_liner, liner_h)
    for z_side in (-1.0, +1.0):
        # Flush with the beam, not inset from it. The beams stop well below the
        # mouth, so above them these panels ARE the end of the well; a 0.4 m
        # inset there is a 0.4 m slot to space rather than a shadow line. The
        # reveal that makes the mouth read stays on the u sides, where the
        # columns run full height behind it.
        z_face = z_side * clear_z / 2.0
        z_off = min(z_face, z_face - z_side * (liner_t + inset))
        put(well, -clear_u / 2.0, clear_u, z_off, liner_t, r_liner, liner_h)
    put(well, -clear_u / 2.0, clear_u, -clear_z / 2.0, clear_z, r_floor, 2.4)

    # Stepped deck ledges. "At least three stepped deck levels within the bay
    # volume" -- 00-INDEX on this frame. Two are built and the well floor is
    # the third, because a ledge that reaches the mouth would hide the floor
    # and the depth is the whole point of the rebuild.
    ledge_reach = 0.22 * clear_u
    for step, frac in enumerate((0.30, 0.58)):
        r_at = r_floor + frac * liner_h
        side = -1.0 if step == 0 else +1.0
        u_face = side * (clear_u / 2.0 - inset - liner_t)
        u0 = min(u_face, u_face - side * ledge_reach)
        put(well, u0, ledge_reach, -clear_z / 2.0 + inset, clear_z - 2 * inset,
            r_at, 2.0)
        # Chevron nosing on the ledge's leading edge -- every deck edge in the
        # frame carries one.
        nose = min(1.6, ledge_reach * 0.25)
        u_nose = u0 if side > 0 else u0 + ledge_reach - nose
        put(lip, u_nose, nose, -clear_z / 2.0 + inset, clear_z - 2 * inset,
            r_at + 2.0, 0.7)

    # The sill lip: the chevron band on the threshold you cross going in.
    put(lip, -w / 2.0, w, -clear_z / 2.0 - beam_d, beam_d * 0.8,
        r_mouth, 1.1)

    # --- the launch arm, stowed --------------------------------------------
    # A triangulated lattice truss with a pentagonal cradle ring, hinged at a
    # heavy root block, is what the frame shows. It is modelled as three boxes:
    # at the range this is seen from, a truss and a solid boom differ by a few
    # pixels of transparency and by 300 triangles a bay. The arm swings, so
    # STOWED is the state the hull mesh can honestly carry -- an extended arm
    # is a runtime pose, not geometry.
    arm_w = 0.20 * clear_u
    root_l = 0.18 * clear_z
    put(frame, -arm_w / 2.0, arm_w, -clear_z / 2.0 + inset, root_l,
        r_floor + 2.4, 0.16 * liner_h)
    boom_l = 0.55 * clear_z
    put(frame, -arm_w * 0.28, arm_w * 0.56,
        -clear_z / 2.0 + inset + root_l, boom_l,
        r_floor + 2.4 + 0.05 * liner_h, 0.06 * liner_h)
    put(frame, -arm_w * 0.62, arm_w * 1.24,
        -clear_z / 2.0 + inset + root_l + boom_l, 0.9 * arm_w,
        r_floor + 2.4 + 0.02 * liner_h, 0.13 * liner_h)

    # --- lights -------------------------------------------------------------
    # Both fittings already have measured materials taken FROM THIS FRAME and
    # neither had any geometry: marker_light_red cites "red and white marker
    # lights on the columns" and marker_light_white the same sentence.
    lamp = max(1.4, 0.06 * col_w)
    for side in (-1.0, +1.0):
        u_in = side * clear_u / 2.0
        # Beacon on the capital, facing out along the axis of the column.
        put(beacon, u_in + (side * col_w / 2.0) - lamp, 2.0 * lamp,
            -lamp, 2.0 * lamp, r_mouth + cap_rise, lamp)
        # A file of three markers down the well's inner face, in the top half
        # where a pilot lining up would see them. On the LINER's face rather
        # than the column's: the column face is 0.4 m outboard of it and a
        # lamp mounted there sinks two thirds of its body into the liner.
        face = side * (clear_u / 2.0 - inset - liner_t)
        u0 = face if side < 0 else face - lamp * 0.7
        for j in range(3):
            r_at = r_floor + liner_h * (0.46 + 0.20 * j)
            put(marker, u0, lamp * 0.7, -lamp, 2.0 * lamp, r_at, lamp * 0.5)


def planar_blades(spec, profile):
    """Tall blades lying in a single plane containing the axis.

    The radiators are NOT arrayed around the axis. The orthographic reference
    sheet (reference/01-station-exterior/exterior more.jpg) shows them edge-on
    in the top view and full-face in the side view -- three blades above the
    spine and three below, all coplanar. A radial array was wrong; see
    canon/CONFLICTS.md C-007.

    Coplanar is also the physically sensible arrangement for radiators on a
    spine this thin: blades in one plane never radiate into each other.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    per_side = spec["count"] // 2
    span, chord, th = spec["span_m"], spec["chord_m"], spec["thickness_m"] / 2.0
    plane = math.radians(spec.get("plane_deg", 0.0))

    # Planform read off the production sheet, as fractions of (span, chord).
    # The blades are LOZENGES, not tapered plates: narrow where they bolt to
    # the spine, widest about a quarter of the way out, then a long slow taper
    # to a capped tip. A simple root-to-tip taper -- which is what was here --
    # gives a wedge and loses the whole silhouette.
    PLANFORM = (
        (0.00, 0.42),   # root, narrow: this is a bolted joint, not the wide part
        (0.09, 0.78),
        (0.27, 1.00),   # widest
        (0.55, 0.86),
        (0.82, 0.58),
        (0.95, 0.34),
        (1.00, 0.22),   # capped tip, still square rather than pointed
    )
    # A separate frame runs round the panel. On the sheet it reads as a pale
    # structural border against the dark radiating face, and it is most of what
    # makes a blade look fabricated rather than cut from card.
    frame_t = th * 1.9
    frame_inset = spec.get("frame_inset", 0.86)

    for side in (1, -1):
        a = plane if side > 0 else plane + math.pi
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        for i in range(per_side):
            zc = z0 + (z1 - z0) * (i + 0.5) / per_side
            r0 = radius_at(profile, zc)
            root_r = r0 * 0.9

            def shell(half_scale, thick):
                for (f0, w0), (f1, w1) in zip(PLANFORM, PLANFORM[1:]):
                    ri, ro = root_r + span * f0, root_r + span * f1
                    c0 = chord * w0 * half_scale / 2.0
                    c1 = chord * w1 * half_scale / 2.0
                    quad = [
                        (ca * ri - tx * thick, sa * ri - ty * thick, zc - c0),
                        (ca * ri - tx * thick, sa * ri - ty * thick, zc + c0),
                        (ca * ro - tx * thick, sa * ro - ty * thick, zc + c1),
                        (ca * ro - tx * thick, sa * ro - ty * thick, zc - c1),
                    ]
                    quad += [(x + 2 * tx * thick, y + 2 * ty * thick, z)
                             for x, y, z in quad]
                    _box(verts, tris, quad)
                    # CHORDWISE RIBS, as on `swept_fins`. These blades are the
                    # largest single surfaces on the exterior and carried only
                    # their own planform outline -- two lines for a 500 m
                    # radiator. A stiffened panel is what one actually is.
                    for rk in range(1, _ribs(BLADE_RIBS) + 1):
                        fr = rk / (_ribs(BLADE_RIBS) + 1)
                        za = zc - c0 + 2 * c0 * fr
                        zb = zc - c1 + 2 * c1 * fr
                        for face in (-1, 1):
                            off = thick + BLADE_RIB_P_M / 2.0
                            rq = [
                                (ca * ri + tx * face * off,
                                 sa * ri + ty * face * off, za
                                 - BLADE_RIB_W_M / 2),
                                (ca * ri + tx * face * off,
                                 sa * ri + ty * face * off, za
                                 + BLADE_RIB_W_M / 2),
                                (ca * ro + tx * face * off,
                                 sa * ro + ty * face * off, zb
                                 + BLADE_RIB_W_M / 2),
                                (ca * ro + tx * face * off,
                                 sa * ro + ty * face * off, zb
                                 - BLADE_RIB_W_M / 2),
                            ]
                            rq += [(x + tx * face * BLADE_RIB_P_M,
                                    y + ty * face * BLADE_RIB_P_M, z)
                                   for x, y, z in rq]
                            _box(verts, tris, rq)

            shell(1.0, frame_t)              # structural frame
            shell(frame_inset, th * 2.4)     # radiating panel, proud of the frame

            # Root mount block and tip cap. Both are visible fittings on the
            # sheet and both stop the blade reading as a floating plate.
            for r_at, w_at, depth in ((root_r - span * 0.02, 0.46, th * 3.2),
                                      (root_r + span * 1.0, 0.26, th * 2.8)):
                c = chord * w_at / 2.0
                ln = span * 0.035
                quad = [
                    (ca * r_at - tx * depth, sa * r_at - ty * depth, zc - c),
                    (ca * r_at - tx * depth, sa * r_at - ty * depth, zc + c),
                    (ca * (r_at + ln) - tx * depth, sa * (r_at + ln) - ty * depth, zc + c),
                    (ca * (r_at + ln) - tx * depth, sa * (r_at + ln) - ty * depth, zc - c),
                ]
                quad += [(x + 2 * tx * depth, y + 2 * ty * depth, z) for x, y, z in quad]
                _box(verts, tris, quad)

    # Spine rail the blades rise from. On the sheet the blades do not touch the
    # hull directly -- they stand on a beam running along it, which is what
    # gives the assembly its horizontal base line.
    rail_r = radius_at(profile, (z0 + z1) / 2.0) * 0.9
    for side in (1, -1):
        a = plane if side > 0 else plane + math.pi
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        d, h = th * 2.6, span * 0.045
        quad = [
            (ca * rail_r - tx * d, sa * rail_r - ty * d, z0),
            (ca * rail_r - tx * d, sa * rail_r - ty * d, z1),
            (ca * (rail_r + h) - tx * d, sa * (rail_r + h) - ty * d, z1),
            (ca * (rail_r + h) - tx * d, sa * (rail_r + h) - ty * d, z0),
        ]
        quad += [(x + 2 * tx * d, y + 2 * ty * d, z) for x, y, z in quad]
        _box(verts, tris, quad)

    return verts, tris


# --- the cargo train --------------------------------------------------------
#
# WHAT WAS WRONG. Each of the six cargo modules was ONE BOX -- 12 triangles, 6
# facets, a 110.7 m unbroken face -- and the row had nothing else in it at all.
# At the rubric's half distance (docs/craft-4r-ext-cargo-before-half.png) that
# is a dark red slab filling 720 of 720 rows with no hatch, no rib, no door and
# no seam, sitting on a hull that carries plating, window rows and greebles.
# AAA-STANDARD's C1 verbatim: "a box primitive standing in for a named object".
#
# AND THE SCHEMA ALREADY SAID WHAT WAS MISSING. `station.yaml` gives
# cargo_module `rail: True` and its `src` reads "six dark-red modules countable
# on a continuous raised dorsal rail with grey plinths between them" -- and the
# key `rail` appeared nowhere in this file. A sourced fact, declared in the
# schema, that no builder read. `_selftest`'s spec-key check now fires on that
# class of defect rather than on this instance of it.
#
# TWO AUTHORITY-2 SOURCES THAT COULD NOT HAVE COPIED EACH OTHER agree on the
# rail, which is what FIDELITY 4 asks for:
#   * `01-station-exterior/exterior more.jpg`, production orthographic renders:
#     "six dark-red rectangular modules ... sitting on a continuous raised
#     dorsal rail with small grey plinths between them. Six, not 5-6."
#   * `other map 4.jpg`, the Miller print sheet: "A dorsal row of ~6 small
#     square modules on a rail runs aft-of-centre along the spine, with six
#     blue leader arrows taking them to six callout boxes under the heading
#     AUTO LOADERS SEQUENCE."
# The second also says what they ARE -- auto-loader positions -- which is why
# the row ends in a machinery block rather than in nothing.
#
# THE MEASUREMENT, AND IT IS STORED AS RATIOS. `exterior more.jpg` carries no
# scale bar, so INV-018's rule applies: store the figure as a ratio and the
# unknown scale cancels. Measured on the native 1280x960 sheet by thresholding
# the modules' red against a neutral hull (45 < r < 200, r-g > 18, r-b > 18),
# over the top view's rows 176..192 and the side view's rows 400..450:
#
#   six runs at x 639-657, 673-691, 707-724, 742-759, 776-793, 810-827
#   module length along z   18.33 px   (1.000, the datum)
#   gap between modules     15.80 px   (0.862)
#   module width across     17.0  px   (0.927)
#   module height, side vw  16.0  px   (0.873)
#
# Grey pixels fill 14 of 15 and 14 of 16 columns in two of the five gaps and
# some of every other one -- the plinths, measured rather than taken on trust.
# See INV-580.
CARGO_GAP_FRAC = 0.862         # gap / module length along z, measured
CARGO_WIDE_FRAC = 0.927        # module width across / module length, measured
CARGO_TALL_FRAC = 0.873        # module height / module length, measured. NOT
                               # BUILT -- see the note in _selftest and the
                               # patch proposal; `protrusion_m` is schema.
CARGO_POST_FRAC = 0.055        # corner post width / module length
CARGO_PROUD_FRAC = 0.020       # frame relief, as a fraction of module length
CARGO_CASTING_FRAC = 1.45      # a corner casting oversails its post
CARGO_CORRUGATIONS = 9         # ribs per wall panel between the corner posts
CARGO_RIB_PROUD_FRAC = 0.009   # rib relief -- HALF the frame's, deliberately
CARGO_RAIL_TOP_FRAC = 0.14     # rail height / protrusion
CARGO_FOOT_TOP_FRAC = 0.20     # module underside / protrusion
CARGO_SLEEPERS = 4             # rail cross-ties per module pitch

# DOES THE RAIL GET ITS OWN GROUP, AND THEREFORE ITS OWN MATERIAL.
#
# It should. The sheet shows the modules dark red and the rail, plinths and
# gantry GREY, measured on the native image as a same-frame ratio against two
# independent hull patches: the rail band reads 0.788/0.778/0.910 of the hull
# plate beside it, which on `materials.hull_exterior`'s 0.600/0.582/0.564 is an
# albedo of 0.473/0.453/0.513 -- the same plated grey, darker and slightly
# cooler. INV-585, and the frames are
# docs/craft-4r-ext-cargo-after-railmat.png (bound) against
# docs/craft-4r-ext-cargo-after.png (unbound).
#
# It is OFF because binding it needs a `Material` in `station/materials.py`,
# which another agent owns and is editing this session. `export_scene`'s
# exterior coverage check is STRICT -- an emitted group matching no rule in
# `exterior.tscn` RAISES rather than warns -- so shipping the split group
# without its material would not render a grey rail, it would stop the exterior
# exporting at all. The whole diff, with the measurement behind it, is in
# `scratchpad/PATCHES-4r-exterior.md`; flipping this to True is the other half
# of that patch and `_selftest` builds BOTH branches so neither can rot.
#
# What is lost meanwhile is a hue, not a shape: the rail, plinths, feet and
# gantry are all built either way and read as structure either way. They just
# read as red structure.
SPLIT_RAIL_GROUP = False


def dorsal_line(spec, profile):
    """The cargo train: six auto-loader modules on a continuous dorsal rail.

    Returns TWO groups, because the sheet shows two materials and a group is
    the finest thing the engine binds a material to: the modules are dark red
    (`materials.cargo_module`, albedo 0.340/0.222/0.205, measured off this same
    sheet) and the rail, plinths, feet and terminal block are GREY. Emitting
    them as one group would paint a grey rail red, which is the defect
    `cobra_bay_ring` was split five ways to avoid.

    AND THE SECOND GROUP IS `cargo_rail`, NOT `cargo_module_rail`, WHICH IS NOT
    A STYLE CHOICE. `render_shot.gd::_material_for` binds by LONGEST SUBSTRING
    -- `mesh_name.contains(frag)` -- so any group name CONTAINING
    `cargo_module` inherits the red container skin. The first build of this was
    named `cargo_module_rail` and the frame came back with a red rail and red
    plinths against a sheet that says grey. Nothing failed and no gate fired;
    the only tell was the picture. Until `materials.py` binds it -- the patch
    is written out in `scratchpad/PATCHES-4r-exterior.md` -- this group matches
    no rule and lands on `exterior.tscn`'s `fallback_material = m_hull`, the
    pale structural grey. That is the right family BY ACCIDENT rather than by
    decision, and this sentence exists so the next reader knows which.

    Placement is unchanged. The row lies along one meridian because the
    orthographic sheet shows it in BOTH the top and side views, which only
    happens for a row on one line of longitude; it was once wrapped around the
    circumference and read as surface noise. `z0`, `z1`, `count`, `rows`,
    `fill`, `width_m`, `protrusion_m` and `plane_deg` all mean exactly what
    they meant before and the outer envelope is unmoved -- the module top is
    still exactly `r0 + protrusion_m`, so `validate.py`'s radius envelope and
    `lod.max_radius` cannot see this change.

    THREE TIERS, which is what AAA-STANDARD C3 asks for and what a box cannot
    have. Primary: the container, 118 m. Secondary: its structural frame --
    four corner posts, top and bottom rails, eight corner castings -- at 6.5 m,
    standing 2.4 m proud. Tertiary: the corrugation between the posts at 1.1 m
    proud, half the frame's relief so the frame still reads as the higher tier
    rather than as more of the same. A container IS a welded frame with
    corrugated panels between; this is not decoration applied to a box, it is
    the object's own construction. INV-582.
    """
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    rows = spec.get("rows", 1)
    per_row = max(1, n // rows)
    prot, w = spec["protrusion_m"], spec["width_m"]
    pitch = (z1 - z0) / per_row
    length = pitch * spec.get("fill", 0.72)

    mod = ([], [])
    rail = ([], [])
    # `rail` is a schema key and it is READ here, which is the whole point of
    # _selftest's spec-key check. A row with the rail switched off is the
    # pre-4r silhouette and the gate's negative control uses it.
    want_rail = bool(spec.get("rail", False))

    for row in range(rows):
        a = math.radians(spec.get("plane_deg", 0.0)) + row * 2.0 * math.pi / rows
        ca, sa = math.cos(a), math.sin(a)
        r_mid = radius_at(profile, (z0 + z1) / 2.0)
        if want_rail:
            _cargo_rail(rail, ca, sa, profile, z0, z1, w, prot, pitch, per_row)
        for i in range(per_row):
            zc = z0 + (z1 - z0) * (i + 0.5) / per_row
            r0 = radius_at(profile, zc)
            _cargo_module(mod, rail, ca, sa, r0, zc, length, w, prot,
                          want_rail)
            if want_rail and i < per_row - 1:
                # A plinth in each gap. Its own z span is the gap the sheet
                # measures, not a guess: the modules are `length` long on a
                # `pitch`, so the gap is whatever the schema's `fill` leaves.
                zg = zc + pitch / 2.0
                _cargo_plinth(rail, ca, sa, radius_at(profile, zg), zg,
                              pitch - length, w, prot)
        if want_rail:
            # THE TERMINAL MUST NOT SIT ON A MODULE. The first build of it took
            # `pitch * 0.26` of length off `z1` and landed 21 m inside the last
            # container -- two solids sharing a volume, which is R5's standing
            # counter-example (the tram 6.43 m inside a spoke) reproduced in
            # miniature, and which no render at this scale would have shown
            # because the block is grey against a red module in shadow. The
            # space actually available is whatever `fill` leaves past the last
            # module, so that is what it is given, and the guard raises rather
            # than silently clamping.
            last_end = z0 + (z1 - z0) * (per_row - 0.5) / per_row + length / 2.0
            avail = z1 - last_end
            # A tenth of the module pitch is the smallest the gantry can be and
            # still read as machinery rather than as a chip off the last
            # container -- one rail cross-tie's spacing, `CARGO_SLEEPERS` per
            # pitch being four. Below that the honest answer is that the run
            # does not fit, not a thinner block.
            if avail < pitch / CARGO_SLEEPERS / 2.5:
                raise ValueError(
                    f"cargo train has no room for its terminal block: the last "
                    f"module ends at z={last_end:.1f}, the run ends at "
                    f"z={z1:.1f}, so {avail:.1f} m is left against a minimum of "
                    f"{pitch / CARGO_SLEEPERS / 2.5:.1f} m. Lower `fill` "
                    f"({spec.get('fill', 0.72)}) or extend z1.")
            _cargo_terminal(rail, ca, sa, r_mid, last_end, avail, w, prot)

    if not SPLIT_RAIL_GROUP:
        base = len(mod[0])
        mod[0].extend(rail[0])
        mod[1].extend((a + base, b + base, c + base) for a, b, c in rail[1])
        return {spec["id"]: mod}
    return {spec["id"]: mod, "cargo_rail": rail}


def _cargo_put(part, ca, sa, r0, zc, t0, dt, dz0, dz, r_off, dr):
    """Place a box in the module's own (across, along, radial) frame.

    (u_t, u_z, u_r) is RIGHT-HANDED -- u_t x u_z = (-sa, ca, 0) x (0, 0, 1) =
    (ca, sa, 0) = u_r -- so every call takes positive extents and comes out
    wound outward, and `_selftest`'s signed-volume check on the group is what
    holds me to it. Same discipline as `_cobra_bay.put`, and for the same
    reason: the two components whose winding was inside-out for four sessions
    both got it wrong reordering corners by hand.
    """
    if dt <= 0 or dz <= 0 or dr <= 0:
        raise ValueError(f"cargo box has a non-positive extent: "
                         f"dt={dt} dz={dz} dr={dr}")
    ut = (-sa, ca, 0.0)
    uz = (0.0, 0.0, 1.0)
    ur = (ca, sa, 0.0)
    origin = (ur[0] * (r0 + r_off) + ut[0] * t0,
              ur[1] * (r0 + r_off) + ut[1] * t0,
              zc + dz0)
    _slab(part[0], part[1], origin,
          tuple(c * dt for c in ut), tuple(c * dz for c in uz),
          tuple(c * dr for c in ur))


def _cargo_module(mod, rail, ca, sa, r0, zc, length, w, prot, want_rail):
    """One container: body, frame, castings, corrugation, hatch and feet."""
    post = CARGO_POST_FRAC * length
    proud = CARGO_PROUD_FRAC * length
    rib_proud = CARGO_RIB_PROUD_FRAC * length
    base = CARGO_FOOT_TOP_FRAC * prot if want_rail else 0.0
    # The top is exactly `prot`, unchanged from the box this replaces, so the
    # silhouette's outer extent does not move. What changes is everything
    # between the top and the hull.
    hgt = prot - base
    if hgt <= 0:
        raise ValueError(f"cargo module has no height: prot={prot} base={base}")
    hw, hl = w / 2.0, length / 2.0

    # --- primary: the container body ---------------------------------------
    _cargo_put(mod, ca, sa, r0, zc, -hw, w, -hl, length, base, hgt)

    # --- secondary: the welded frame ---------------------------------------
    # Four corner posts, running the full height and standing proud on BOTH
    # faces they meet at, which is what a corner post does and what makes the
    # corner read as a corner rather than as an arris.
    for st in (-1.0, +1.0):
        for sz in (-1.0, +1.0):
            t_out = st * (hw + proud)
            z_out = sz * (hl + proud)
            _cargo_put(mod, ca, sa, r0, zc,
                       min(t_out, t_out - st * (post + proud)), post + proud,
                       min(z_out, z_out - sz * (post + proud)), post + proud,
                       base, hgt)
    # Top and bottom rails round the whole perimeter. `rail_d` is the post
    # width, so the frame is one member size throughout -- a frame built of
    # three different sections reads as three unrelated things.
    for r_at in (base, base + hgt - post):
        for st in (-1.0, +1.0):
            _cargo_put(mod, ca, sa, r0, zc, st * hw if st > 0 else -hw - proud,
                       proud, -hl, length, r_at, post)
        for sz in (-1.0, +1.0):
            _cargo_put(mod, ca, sa, r0, zc, -hw, w,
                       sz * hl if sz > 0 else -hl - proud, proud, r_at, post)
    # Eight corner castings -- the lift points an auto-loader grabs. They are
    # the reason the frame has corners at all, and they are the smallest thing
    # in the secondary tier, so they set its lower bound.
    cast = CARGO_CASTING_FRAC * post
    for st in (-1.0, +1.0):
        for sz in (-1.0, +1.0):
            for r_at in (base, base + hgt - cast):
                t_out = st * (hw + proud + rib_proud)
                z_out = sz * (hl + proud + rib_proud)
                _cargo_put(mod, ca, sa, r0, zc,
                           min(t_out, t_out - st * cast), cast,
                           min(z_out, z_out - sz * cast), cast,
                           r_at, cast)

    # --- tertiary: corrugation between the posts ---------------------------
    nrib = _ribs(CARGO_CORRUGATIONS)
    inner_t, inner_z = w - 2.0 * post, length - 2.0 * post
    rib_w = max(0.6, inner_z / (2.0 * nrib + 1.0)) if nrib else 0.0
    for k in range(nrib):
        f = (k + 0.5) / nrib
        # long faces: ribs run radially, spaced along z
        zz = -inner_z / 2.0 + inner_z * f - rib_w / 2.0
        for st in (-1.0, +1.0):
            _cargo_put(mod, ca, sa, r0, zc,
                       st * hw if st > 0 else -hw - rib_proud, rib_proud,
                       zz, rib_w, base + post, hgt - 2.0 * post)
        # end faces: ribs run radially, spaced across
        tt = -inner_t / 2.0 + inner_t * f - rib_w / 2.0
        for sz in (-1.0, +1.0):
            _cargo_put(mod, ca, sa, r0, zc, tt, rib_w,
                       sz * hl if sz > 0 else -hl - rib_proud, rib_proud,
                       base + post, hgt - 2.0 * post)

    # --- the loading hatch, on the face the loader reaches --------------------
    # `other map 4.jpg` calls these AUTO LOADER positions, so the top face is
    # the working face and it gets the aperture the name implies: a recessed
    # lid inside a raised rim. Without it the top is the one face with nothing
    # on it, and the top is what a camera above the dorsal line looks straight
    # down at -- which is the framing docs/craft-4r-ext-cargo-before-half.png
    # is taken from.
    ht, hz = inner_t * 0.62, inner_z * 0.62
    rim = post * 0.85
    for st in (-1.0, +1.0):
        _cargo_put(mod, ca, sa, r0, zc, st * ht / 2.0 if st > 0
                   else -ht / 2.0 - rim, rim, -hz / 2.0, hz,
                   base + hgt, rim * 1.2)
    for sz in (-1.0, +1.0):
        _cargo_put(mod, ca, sa, r0, zc, -ht / 2.0 - rim, ht + 2.0 * rim,
                   sz * hz / 2.0 if sz > 0 else -hz / 2.0 - rim, rim,
                   base + hgt, rim * 1.2)
    _cargo_put(mod, ca, sa, r0, zc, -ht / 2.0, ht, -hz / 2.0, hz,
               base + hgt, rim * 0.55)

    # --- the feet, and they belong to the RAIL's material --------------------
    # The side view shows a shadow gap under every module with two dark blocks
    # in it. That gap is why the modules read as cargo standing ON something
    # rather than as blisters grown out of the hull.
    if want_rail:
        foot_t, foot_z = w * 0.26, length * 0.16
        for sz in (-1.0, +1.0):
            _cargo_put(rail, ca, sa, r0, zc, -foot_t / 2.0, foot_t,
                       sz * length * 0.30 - foot_z / 2.0, foot_z,
                       CARGO_RAIL_TOP_FRAC * prot,
                       base - CARGO_RAIL_TOP_FRAC * prot)


def _cargo_rail(rail, ca, sa, profile, z0, z1, w, prot, pitch, per_row):
    """The continuous raised dorsal rail, stepped, with cross-ties.

    Two authority-2 sources call it continuous, so it is built as one run from
    z0 to z1 rather than as a plinth under each module. It follows the hull the
    way `_cobra_bay` does -- sampled per tie -- because this band is 1,140 m
    long and a rail on one radius would bury itself at one end.
    """
    ties = max(1, int(round(CARGO_SLEEPERS * per_row)))
    seg = (z1 - z0) / ties
    top = CARGO_RAIL_TOP_FRAC * prot
    for k in range(ties):
        za = z0 + seg * k
        r0 = radius_at(profile, za + seg / 2.0)
        # lower deck, wider; upper rail, narrower. The step is what gives the
        # run its own base line in the side view.
        _cargo_put(rail, ca, sa, r0, za, -w * 0.56, w * 1.12, 0.0, seg,
                   -10.0, 10.0 + top * 0.5)
        _cargo_put(rail, ca, sa, r0, za, -w * 0.36, w * 0.72, 0.0, seg,
                   top * 0.5, top * 0.5)
        # A cross-tie standing proud at the head of each segment -- the row of
        # small dark ticks running the length of the band under the modules in
        # the top view, which is the only tertiary detail the rail has in the
        # sheet.
        _cargo_put(rail, ca, sa, r0, za, -w * 0.60, w * 1.20,
                   seg * 0.06, seg * 0.16, -2.0, top * 0.62)


def _cargo_plinth(rail, ca, sa, r0, zc, gap, w, prot):
    """A grey plinth in the gap between two modules. Measured: grey fills 14 of
    15 and 14 of 16 columns in two of the five gaps on the sheet."""
    top = CARGO_RAIL_TOP_FRAC * prot
    gl = gap * 0.52
    _cargo_put(rail, ca, sa, r0, zc, -w * 0.24, w * 0.48, -gl / 2.0, gl,
               top, prot * 0.20)
    _cargo_put(rail, ca, sa, r0, zc, -w * 0.30, w * 0.60,
               -gl * 0.34, gl * 0.68, top + prot * 0.20, prot * 0.06)


def _cargo_terminal(rail, ca, sa, r0, zc, avail, w, prot):
    """The machinery block that closes the run, inside `avail` metres of z.

    Both sheets show the row ending in a taller grey structure rather than in
    nothing, and `other map 4.jpg` says what it is for: the modules are AUTO
    LOADER positions, so the run terminates at the loader itself. It is TALL
    rather than long because `fill` leaves it 36 m and it is 104 m wide -- a
    gantry over the end of a train is the shape that fits and the shape the
    sheet shows.
    """
    top = CARGO_RAIL_TOP_FRAC * prot
    dz = avail * 0.86
    z0_ = avail * 0.07
    _cargo_put(rail, ca, sa, r0, zc, -w * 0.44, w * 0.88, z0_, dz,
               top, prot * 0.52)
    _cargo_put(rail, ca, sa, r0, zc, -w * 0.30, w * 0.60, z0_ + dz * 0.12,
               dz * 0.76, top + prot * 0.52, prot * 0.34)
    _cargo_put(rail, ca, sa, r0, zc, -w * 0.11, w * 0.22, z0_ + dz * 0.26,
               dz * 0.48, top + prot * 0.86, prot * 0.30)
    # Two legs straddling the rail, so the loader stands over the train rather
    # than beside it.
    for st in (-1.0, +1.0):
        _cargo_put(rail, ca, sa, r0, zc, st * w * 0.44 if st > 0
                   else -w * 0.44 - w * 0.09, w * 0.09, z0_ + dz * 0.30,
                   dz * 0.40, -6.0, top + 6.0)


def dome_frame(out):
    """An orthonormal (a, b) pair spanning the plane normal to `out`."""
    ox, oy, oz = out
    if abs(oz) < 0.9:
        ux, uy, uz = 0.0, 0.0, 1.0
    else:
        ux, uy, uz = 1.0, 0.0, 0.0
    ax = uy * oz - uz * oy
    ay = uz * ox - ux * oz
    az = ux * oy - uy * ox
    al = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
    ax, ay, az = ax / al, ay / al, az / al
    return (ax, ay, az), (oy * az - oz * ay,
                          oz * ax - ox * az,
                          ox * ay - oy * ax)


def dome_mesh(verts, tris, cx, cy, cz, out, radius, height, rings=6, segs=14):
    """Half-ellipsoid bulging along an arbitrary outward direction. CLOSED.

    It was not closed, and no render could have said so: the base sits inside
    the hull and the hole faces away from every camera. `_selftest` measures
    it instead, and found 56 boundary edges on `observation_dome`, 56 on
    `docking_port` and 112 on `observation_rotunda` -- the open base ring, and
    a top ring of `segs` coincident vertices that made `segs` degenerate
    quads at the pole.

    Both are fixed here and the triangle count is unchanged: the pole becomes
    one vertex with a fan under it (2*segs triangles become segs), and the
    base gets a disc fan (segs triangles). greeble.py's blisters call this too
    and get the same repair for the same count.
    """
    (ax, ay, az), (bx, by, bz) = dome_frame(out)
    ox, oy, oz = out

    def place(phi, th):
        rr, hh = radius * math.cos(phi), height * math.sin(phi)
        c, sn = math.cos(th) * rr, math.sin(th) * rr
        return (cx + ax * c + bx * sn + ox * hh,
                cy + ay * c + by * sn + oy * hh,
                cz + az * c + bz * sn + oz * hh)

    base = len(verts)
    for r in range(rings):                       # latitude bands, base upward
        phi = (math.pi / 2) * r / rings
        for sgm in range(segs):
            verts.append(place(phi, 2 * math.pi * sgm / segs))
    pole = len(verts)
    verts.append((cx + ox * height, cy + oy * height, cz + oz * height))
    centre = len(verts)
    verts.append((cx, cy, cz))

    for r in range(rings - 1):
        for sgm in range(segs):
            a = base + r * segs + sgm
            b = base + r * segs + (sgm + 1) % segs
            c = base + (r + 1) * segs + (sgm + 1) % segs
            d = base + (r + 1) * segs + sgm
            tris.append((a, b, c))
            tris.append((a, c, d))
    top = base + (rings - 1) * segs
    for sgm in range(segs):
        tris.append((top + sgm, top + (sgm + 1) % segs, pole))
        # Base disc, wound the other way -- it faces into the hull.
        tris.append((centre, base + (sgm + 1) % segs, base + sgm))


def _ribbon(verts, tris, p0, p1, across, width, thick, out_hint):
    """A straight box from p0 to p1, `width` across and `thick` proud.

    The one shape a dome's fittings are all made of: a mullion is a ribbon up
    a meridian, a collar is a ring of ribbons round the base, a ring band is a
    ring of ribbons round a latitude. `out_hint` orients the thickness away
    from the shell -- flipping `across` rather than the normal, because
    negating the normal alone would invert the winding and `_slab` would emit
    an inside-out box that still looked right in a render.
    """
    m = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    ac = math.sqrt(sum(c * c for c in across)) or 1.0
    across = tuple(c / ac for c in across)
    n = (across[1] * m[2] - across[2] * m[1],
         across[2] * m[0] - across[0] * m[2],
         across[0] * m[1] - across[1] * m[0])
    if sum(a * b for a, b in zip(n, out_hint)) < 0.0:
        across = tuple(-c for c in across)
        n = tuple(-c for c in n)
    nl = math.sqrt(sum(c * c for c in n)) or 1.0
    n = tuple(c / nl for c in n)
    origin = tuple(p0[i] - across[i] * width / 2.0 for i in range(3))
    _slab(verts, tris, origin,
          tuple(across[i] * width for i in range(3)), m,
          tuple(n[i] * thick for i in range(3)))


# The glazing pattern, and it is SOURCED. `03-sector-blue/comand and
# contorl.webp` is authority 1 and is Observation Dome 1 -- Command and
# Control -- seen from inside: "a large circle carried on radial spoke
# mullions with a broad concentric ring band" (00-INDEX). Counting panes
# across the visible upper arc of that frame at 5x gives 8 to 9, which closes
# to 16-18 for a full ring. 16 is taken because it is in the counted range
# AND divides the shell's segment count, so every mullion lands on a shell
# seam instead of crossing one; a rib that crosses a seam has to be pushed
# further out to stay proud, and the further out it goes the more it reads as
# a cage over the dome rather than as its glazing bars.
DOME_MULLIONS = 16
DOME_BAND_PHI = 0.42          # latitude of the concentric ring band, 0 = base
DOME_RIB_SEGMENTS = 2
# THE MULLIONS STOP AT THE BAND. They ran all the way to the pole in the first
# build and the render said no: sixteen 4.8 m bars converging on a point is 77 m
# of structure crowding into nothing, and it read as a starburst. The reference
# does not do that either -- 00-INDEX's phrasing is "a LARGE CIRCLE carried on
# radial spoke mullions with a broad concentric ring band", and in the frame the
# area inside the band is one unbroken pane. Fixing the accuracy fixed the
# artefact, which is the usual direction.


def domes(spec, profile):
    """Glazed blisters on the hull -- observation domes, rotundas, docking ports.

    Observation Dome 1 is Command & Control, so these are not decoration: they
    are the places the player stands and looks out of, and their positions have
    to survive into the interior layout.

    Two groups. The shell is glazing and the mullions, ring band and base
    collar are structure, and those are different materials -- a smooth
    half-ellipsoid with one material on it was the whole reason these read as
    grey eggs. Everything the frame adds is proportion except the mullion
    count, which is measured; see DOME_MULLIONS and INV-041.
    """
    verts, tris = [], []
    fv, ft = [], []
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    rad, hgt = spec["radius_m"], spec["height_m"]
    segs = spec.get("segments", DOME_MULLIONS)
    rings = spec.get("rings_lat", 6)
    rows = spec.get("rows", 1)
    per_row = max(1, n // rows)
    for row in range(rows):
        zc = z0 + (z1 - z0) * (row + 0.5) / rows if rows > 1 else (z0 + z1) / 2.0
        r0 = radius_at(profile, zc)
        for i in range(per_row):
            a = 2 * math.pi * i / per_row + math.radians(spec.get("phase_deg", 0.0))
            ca, sa = math.cos(a), math.sin(a)
            centre = (ca * r0 * 0.97, sa * r0 * 0.97, zc)
            dome_mesh(verts, tris, centre[0], centre[1], centre[2],
                      (ca, sa, 0.0), rad, hgt, rings=rings, segs=segs)
            _dome_fittings(fv, ft, centre, (ca, sa, 0.0), rad, hgt, segs)
    return {spec["id"]: (verts, tris), spec["id"] + "_frame": (fv, ft)}


def _dome_fittings(verts, tris, centre, out, rad, hgt, segs):
    """Mullions, the concentric ring band and the base collar for one dome."""
    (ax, ay, az), (bx, by, bz) = dome_frame(out)
    cx, cy, cz = centre

    # Fittings sit on a slightly larger similar ellipsoid so that a straight
    # chord between two of their nodes still clears the curved shell between
    # them. Sagitta over a 30 deg chord is 0.034 r; 0.05 covers it with room.
    d = 0.05 * max(rad, hgt)

    def surf(phi, th, grow=0.0):
        rr = (rad + grow) * math.cos(phi)
        hh = (hgt + grow) * math.sin(phi)
        c, sn = math.cos(th) * rr, math.sin(th) * rr
        return (cx + ax * c + bx * sn + out[0] * hh,
                cy + ay * c + by * sn + out[1] * hh,
                cz + az * c + bz * sn + out[2] * hh)

    def radial(th):
        """Outward in the dome's BASE plane."""
        return (ax * math.cos(th) + bx * math.sin(th),
                ay * math.cos(th) + by * math.sin(th),
                az * math.cos(th) + bz * math.sin(th))

    def azimuth(th):
        """Round the dome at constant latitude."""
        return (-ax * math.sin(th) + bx * math.cos(th),
                -ay * math.sin(th) + by * math.cos(th),
                -az * math.sin(th) + bz * math.cos(th))

    def meridian(phi, th):
        """Up the dome at constant longitude. d(surf)/d(phi)."""
        s, c = -rad * math.sin(phi), hgt * math.cos(phi)
        return (ax * s * math.cos(th) + bx * s * math.sin(th) + out[0] * c,
                ay * s * math.cos(th) + by * s * math.sin(th) + out[1] * c,
                az * s * math.cos(th) + bz * s * math.sin(th) + out[2] * c)

    half = math.pi / 2.0
    rib_w, rib_t = 0.055 * rad, 0.045 * rad
    for sgm in range(segs):
        th = 2 * math.pi * sgm / segs
        # Mullion: up the meridian in DOME_RIB_SEGMENTS straight lengths.
        # `across` is the AZIMUTH, not the base-plane radial. The first version
        # passed the radial, which near the base is all but parallel to the
        # meridian the rib runs along -- their cross product collapses, and
        # sixteen 4.8 m structural bars rendered as sixteen hairlines. It is
        # the failure mode `_ribbon` is degenerate under and the only cue was
        # the picture.
        top = half * DOME_BAND_PHI
        for k in range(DOME_RIB_SEGMENTS):
            p0 = surf(top * k / DOME_RIB_SEGMENTS, th, d)
            p1 = surf(top * (k + 1) / DOME_RIB_SEGMENTS, th, d)
            _ribbon(verts, tris, p0, p1, azimuth(th), rib_w, rib_t,
                    tuple(p0[j] - centre[j] for j in range(3)))
        # Concentric ring band, and the base collar the dome stands on. Both
        # run round the dome, so their width is across the run: up the meridian
        # for the band, along the dome's axis for the collar, which is what the
        # base of a blister on a hull actually is.
        th1 = 2 * math.pi * (sgm + 1) / segs
        mid = (th + th1) / 2.0
        band_phi = half * DOME_BAND_PHI
        for phi, across, wide, thick, grow in (
                (band_phi, meridian(band_phi, mid), 0.16 * hgt, 0.05 * rad, d),
                (0.0, out, 0.16 * hgt, 0.10 * rad, 0.0)):
            q0, q1 = surf(phi, th, grow), surf(phi, th1, grow)
            qm = surf(phi, mid, grow)
            hint = (tuple(qm[j] - centre[j] for j in range(3))
                    if phi > 0.0 else radial(mid))
            _ribbon(verts, tris, q0, q1, across, wide, thick, hint)


def swept_fins(spec, profile):
    """Long swept-back blades, as the top view shows on the forward section."""
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    span, th = spec["span_m"], spec["thickness_m"] / 2.0
    sweep = spec.get("sweep_m", 400.0)
    for i in range(spec["count"]):
        a = 2 * math.pi * i / spec["count"] + math.radians(spec.get("phase_deg", 0.0))
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        r0 = radius_at(profile, z0)
        root = z1 - z0
        # Built as several spanwise segments so the planform tapers and the
        # trailing edge sweeps, instead of reading as one flat plank.
        nseg = spec.get("segments", 4)
        for k in range(nseg):
            f0, f1 = k / nseg, (k + 1) / nseg
            ri = r0 * 0.95 + span * f0
            ro = r0 * 0.95 + span * f1
            # Chord narrows toward the tip; both edges sweep forward.
            c0, c1 = root * (1.0 - 0.72 * f0), root * (1.0 - 0.72 * f1)
            s0, s1 = sweep * f0, sweep * f1
            t0 = th * (1.0 - 0.55 * f0)
            t1 = th * (1.0 - 0.55 * f1)
            quad = [
                (ca * ri - tx * t0, sa * ri - ty * t0, z0 + s0),
                (ca * ri - tx * t0, sa * ri - ty * t0, z0 + s0 + c0),
                (ca * ro - tx * t1, sa * ro - ty * t1, z0 + s1 + c1),
                (ca * ro - tx * t1, sa * ro - ty * t1, z0 + s1),
            ]
            quad += [(quad[j][0] + 2 * tx * (t0 if j < 2 else t1),
                      quad[j][1] + 2 * ty * (t0 if j < 2 else t1),
                      quad[j][2]) for j in range(4)]
            _box(verts, tris, quad)
            # CHORDWISE STIFFENER RIBS -- INV-073's rule on a radiator blade.
            # A fin is the largest flat area on the exterior and carried two
            # lines, its leading and trailing edge. A radiator this size has
            # flow channels and the ribs between them; each one runs the full
            # span of its segment, which is the cheapest line there is.
            for rk in range(1, _ribs(FIN_RIBS) + 1):
                fr = rk / (_ribs(FIN_RIBS) + 1)
                za = z0 + s0 + c0 * fr
                zb = z0 + s1 + c1 * fr
                for face in (-1, 1):
                    ta = t0 + face * 0.0
                    rq = [
                        (ca * ri + tx * face * (ta + FIN_RIB_P_M)
                         - tx * FIN_RIB_W_M / 2,
                         sa * ri + ty * face * (ta + FIN_RIB_P_M)
                         - ty * FIN_RIB_W_M / 2, za),
                        (ca * ri + tx * face * (ta + FIN_RIB_P_M)
                         + tx * FIN_RIB_W_M / 2,
                         sa * ri + ty * face * (ta + FIN_RIB_P_M)
                         + ty * FIN_RIB_W_M / 2, za),
                        (ca * ro + tx * face * (t1 + FIN_RIB_P_M)
                         + tx * FIN_RIB_W_M / 2,
                         sa * ro + ty * face * (t1 + FIN_RIB_P_M)
                         + ty * FIN_RIB_W_M / 2, zb),
                        (ca * ro + tx * face * (t1 + FIN_RIB_P_M)
                         - tx * FIN_RIB_W_M / 2,
                         sa * ro + ty * face * (t1 + FIN_RIB_P_M)
                         - ty * FIN_RIB_W_M / 2, zb),
                    ]
                    rq += [(rq[j][0] - tx * face * FIN_RIB_P_M,
                            rq[j][1] - ty * face * FIN_RIB_P_M,
                            rq[j][2]) for j in range(4)]
                    _box(verts, tris, rq)
    return verts, tris


def plate_array(spec, profile):
    """A flat plate carried above the hull on a short pylon, blading forward.

    The forward structure was built as four swept wings from a top-view read of
    "long swept structures". The orthographic sheet shows it is a single flat
    plate-like communications array on a short pylon, extending forward as a
    thin blade -- a plane, not a wing pair. Four wings and one plate look
    similar in plan and nothing like each other in silhouette.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    r0 = radius_at(profile, z0)
    a = math.radians(spec.get("plane_deg", 90.0))
    ca, sa = math.cos(a), math.sin(a)
    tx, ty = -sa, ca
    stand = spec.get("standoff_m", 70.0)
    half = spec["width_m"] / 2.0
    th = spec["thickness_m"] / 2.0
    reach = spec.get("reach_m", 520.0)

    # Pylon: short, and squarer than the plate it carries.
    pr0, pr1 = r0 * 0.94, r0 + stand
    pw = half * 0.20
    quad = [(ca * pr0 - tx * pw, sa * pr0 - ty * pw, z0),
            (ca * pr0 - tx * pw, sa * pr0 - ty * pw, z1),
            (ca * pr1 - tx * pw, sa * pr1 - ty * pw, z1),
            (ca * pr1 - tx * pw, sa * pr1 - ty * pw, z0)]
    quad += [(x + 2 * tx * pw, y + 2 * ty * pw, z) for x, y, z in quad]
    _box(verts, tris, quad)

    # Plate: thin in the radial direction, wide across, reaching forward and
    # tapering as it goes. Built in spanwise strips so the taper is a shape
    # rather than a single wedge.
    rp = r0 + stand
    nseg = spec.get("segments", 5)
    for k in range(nseg):
        f0, f1 = k / nseg, (k + 1) / nseg
        za, zb = z1 + reach * f0, z1 + reach * f1
        w0 = half * (1.0 - 0.62 * f0)
        w1 = half * (1.0 - 0.62 * f1)
        quad = [(ca * rp - tx * w0, sa * rp - ty * w0, za),
                (ca * rp + tx * w0, sa * rp + ty * w0, za),
                (ca * rp + tx * w1, sa * rp + ty * w1, zb),
                (ca * rp - tx * w1, sa * rp - ty * w1, zb)]
        quad += [(x + ca * th * 2, y + sa * th * 2, z) for x, y, z in quad]
        _box(verts, tris, quad)
        # SPANWISE RIBS AND A FRAME EDGE. A communications plate this size is
        # a stiffened panel, not a sheet: the ribs are what stop it flexing and
        # they are the only thing giving 500 m of flat plate any line at all.
        for rk in range(1, _ribs(PLATE_RIBS) + 1):
            fr = rk / (_ribs(PLATE_RIBS) + 1)
            wr0 = w0 + (w1 - w0) * 0.0
            xa = -wr0 + 2 * wr0 * fr
            wr1 = w1
            xb = -wr1 + 2 * wr1 * fr
            for face in (0, 1):
                rr = rp + (th * 2 if face else 0.0)
                pr = PLATE_RIB_P_M * (1 if face else -1)
                rq = [(ca * rr + tx * (xa - PLATE_RIB_W_M / 2),
                       sa * rr + ty * (xa - PLATE_RIB_W_M / 2), za),
                      (ca * rr + tx * (xa + PLATE_RIB_W_M / 2),
                       sa * rr + ty * (xa + PLATE_RIB_W_M / 2), za),
                      (ca * rr + tx * (xb + PLATE_RIB_W_M / 2),
                       sa * rr + ty * (xb + PLATE_RIB_W_M / 2), zb),
                      (ca * rr + tx * (xb - PLATE_RIB_W_M / 2),
                       sa * rr + ty * (xb - PLATE_RIB_W_M / 2), zb)]
                rq += [(x + ca * pr, y + sa * pr, z) for x, y, z in rq]
                _box(verts, tris, rq)
    return verts, tris


BUILDERS = {
    "plate_array": plate_array,
    "planar_blades": planar_blades,
    "domes": domes,
    "swept_fins": swept_fins,
    "dorsal_line": dorsal_line,
    "radial_array": radial_array,
    "pylon_pair": pylon_pair,
    # `radial_band` was the generic "shallow blocks around the circumference"
    # kind and it had exactly one user left -- the cobra bays -- once the cargo
    # modules moved to `dorsal_line`. What replaced it is bay-specific and says
    # so in its name. Both keys are registered so that renaming the kind in
    # station/schema/station.yaml, which is the honest thing to call it, needs
    # no matching edit here and cannot land half-done.
    "radial_band": cobra_bay_ring,
    "cobra_bay_ring": cobra_bay_ring,
}


# HOW MUCH RIB DETAIL THIS BUILD EMITS, 0..1. Session 3s put chordwise
# stiffeners on the radiator blades, the comms plate and the cooling fins, which
# took components from 19,800 to 53,568 triangles. Components are welded
# primitives that no lathe schedule decimates, so at the coarsest LOD they went
# from 46% of the mesh to 93% and `station/lod.py`'s "coarsest under a tenth of
# finest" assertion refused the chain -- correctly. A stiffener 1.5 m wide is
# invisible at the distance lod7 is drawn from, and geometry you cannot see is
# the definition of what a LOD drops.
DETAIL = 1.0


# --- the ionization vanes: MEASURED, NOT BUILT ------------------------------
#
# `docs/volume-audit.md` §5.1 lists "Ionization vane support rings (3) and
# fusion reactor ionization vanes (6)" as canon with no builder:
# `00-MASTER.md` §1.3 counts both at authority 4, and
# `schema.longitudinal.features[main_truss_spine].contains` names both, and
# grep for `ionization`/`vane` in `station/` returns only Starfury geometry.
#
# THE RINGS ARE ON THE DRAWING AND THEY HAVE BEEN MEASURED. `other map 4.jpg`
# at the profile extractor's own calibration (TAIL_PX 71, 4.0703 m/px, from
# `station/extract_radius_profile.py`) shows three heavy transverse ribs
# crossing the truss spine, read as ink density in the upper rail band
# (rows AXIS_PY-40 .. AXIS_PY-8):
#
#     rib   peak px    z (m)     spacing
#     1     465-474    1,604-1,640, centre ~1,620
#     2     537-542    1,897-1,917, centre ~1,907      287 m
#     3     610-612    2,194-2,202, centre ~2,198      291 m
#
# Three ribs, evenly spaced to within 1.4%, inside `main_truss_spine`
# (z 1295-2680) whose `contains` names exactly three support rings. Their
# radial extent reaches the spine's own lathed radius (164.8 m) and no further,
# so they are flush bands rather than protruding fins. Nothing in the frame
# resolves the six VANES; two per ring is the reading "support ring" implies
# and it is a reading, not a measurement.
#
# WHY THERE IS NO BUILDER HERE. A component needs a spec in
# `station.yaml::components`, which is the only machine-readable home for one,
# and the counts 3 and 6 live only in `canon/00-MASTER.md` §1.3 as a table.
# Writing them as literals in this file would put a canon count in a second
# place -- the exact defect `docking_bay._schema_bay_width_m` was rewritten to
# remove, and `tools/mutation_sweep.py` found that one by perturbing a literal
# nothing was tied to. The spec belongs in the schema. Proposed text is in the
# session report; whoever owns `station.yaml` adds it and `radial_band` or a
# `bands` builder consumes it, with the z values above rather than a formula.
def _ribs(n):
    """Rib count at the current detail level. Zero is a valid answer."""
    return max(0, int(round(n * DETAIL)))


def build_all(specs, profile, detail=1.0):
    """Return {group_name: (verts, tris)} for every component in the schema.

    Most builders return one (verts, tris) and take the component's id as their
    group name. A builder may instead return a dict of several groups, because
    a component whose parts are different MATERIALS cannot be one group: the
    engine binds materials by group name and nothing finer. It must still emit
    a group named for the component, since station/validate.py asserts every
    schema component appears in the hull manifest by id -- and that assertion
    is the only thing standing between a renamed group and a component that
    silently stops being built.
    """
    global DETAIL
    prev, DETAIL = DETAIL, detail
    try:
        return _build_all(specs, profile)
    finally:
        DETAIL = prev


def _build_all(specs, profile):
    out = {}
    for spec in specs:
        builder = BUILDERS.get(spec["kind"])
        if builder is None:
            raise ValueError(f"unknown component kind: {spec['kind']}")
        built = builder(spec, profile)
        if isinstance(built, dict):
            if spec["id"] not in built:
                raise ValueError(
                    f"{spec['kind']} emitted {sorted(built)} for component "
                    f"'{spec['id']}' and none of them is named for it")
            for gid, part in built.items():
                if gid in out:
                    raise ValueError(f"two components claim the group '{gid}'")
                out[gid] = part
        else:
            out[spec["id"]] = built
    return out


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def boundary_edges(tris):
    """Directed edges used an odd number of times -- i.e. the mesh's holes.

    The same measure `interior.boundary_edges()` uses, and for the same
    reason: a hole in a solid shows the background through it and the
    background is black, so no render can see one. A union of closed boxes
    has none even where the boxes interpenetrate, because interpenetration
    does not open a surface.
    """
    seen = {}
    for a, b, c in tris:
        for e in ((a, b), (b, c), (c, a)):
            key = (min(e), max(e))
            seen[key] = seen.get(key, 0) + 1
    return sorted(k for k, v in seen.items() if v != 2)


# --- THE GATE THIS FILE DID NOT HAVE -----------------------------------------
#
# Every assertion above this line is TOPOLOGICAL -- closed, outward-wound,
# inside its envelope, not floating, not interpenetrating -- and CLAUDE.md's
# most expensive lesson is that **a cube passes every word of a topological
# test**. It cost three layers of work on the interior; out here it cost eleven
# sessions of `cargo_module` being six boxes and `comms_grid_pylon` being four,
# with 44/44 green the whole time.
#
# So this one measures FORM. `density.analyse` gives visible line density in
# metres of line per square metre; `density.lam_of_plain_box` gives the same
# number for a plain box of the same surface area -- the null hypothesis, which
# is 1.0 by construction. The ratio is "how many times more line-work than a
# cuboid", and a component that is a cuboid scores 1.
#
# TWO NORMALISATIONS MATTER AND GETTING EITHER WRONG MAKES THE NUMBER LIE.
#
#  1. PER INSTANCE, not per group. `lam_of_plain_box` builds its null from the
#     TOTAL area it is handed, so N separate instances of one shape score
#     sqrt(N) times higher than one of them -- the 28 cobra bays read 20.31x
#     over the group and 3.84x per bay. Written the first way a component could
#     pass by being numerous. So the null is a box of ONE INSTANCE's area.
#
#  2. PER SCHEMA COMPONENT, not per emitted group. A cobra bay IS its frame,
#     its well liner, its hazard lip and its two light families; a dome IS its
#     glazing and its mullions. Scoring the glazing alone asks a pane of glass
#     to carry line-work, which is C1's "detail that reads as noise rather than
#     machinery". The rubric judges the object, so the gate concatenates every
#     group a component emits and scores that.
#
# THE FLOOR IS DERIVED FROM THE CONTROL, which is what makes it defensible.
# `boxed_control` rebuilds every component as its own bounding boxes -- which is
# exactly what `dorsal_line` and `pylon_pair` WERE -- and that population tops
# out at **2.02x** (the self-test prints it on every run, so this number cannot
# go stale silently). The least articulated real component is `cobra_bay` at
# **5.43x**. The log-space midpoint is sqrt(2.02 x 5.43) = 3.31, taken as 3.0 --
# rounded DOWN rather than up, so that where the derivation is soft the gate
# errs toward accepting a real component rather than toward rejecting one.
#
# AND IT IS SHOWN FAILING ON THE PRE-4r CONTENT, which is the only evidence
# that matters. Run against `git show 1982be0:station/components.py`, the same
# ten components score:
#
#     reactor_cooling_fin     34.20x       observation_dome           8.39x
#     forward_comms_plate     18.46x       observation_rotunda        8.34x
#     space_traffic_prox      16.65x       docking_port               8.31x
#     heat_exchange_array     14.36x       cobra_bay                  5.43x
#     comms_grid_pylon         2.19x  FAIL
#     cargo_module             1.02x  FAIL
#
# and `cargo_module`'s own boxed control is **1.02x** -- the identical number,
# because it WAS its bounding boxes. Eight components pass unchanged, the two
# the frames showed to be boxes fail, and nothing else does. After this
# session's rework they read 8.61x and 10.56x.
#
# WHAT WOULD BREAK IF IT IS WRONG: too high and a legitimately smooth surface is
# forced to carry decoration it should not have. Too low and it stops
# separating a box from a built thing, which is the only job it has.
ARTICULATION_FLOOR = 3.0


def component_groups(specs, profile):
    """{component id: the group names its builder emits}."""
    out = {}
    for spec in specs:
        built = BUILDERS[spec["kind"]](spec, profile)
        out[spec["id"]] = (sorted(built) if isinstance(built, dict)
                           else [spec["id"]])
    return out


def _concat(gids, parts):
    verts, tris = [], []
    for gid in gids:
        base = len(verts)
        verts.extend(parts[gid][0])
        tris.extend((a + base, b + base, c + base) for a, b, c in parts[gid][1])
    return verts, tris


def articulation(specs, parts, groups, min_facet_m=0.0):
    """{component id: its line density / that of a box of ONE instance's area}.

    `density` is imported here rather than at module scope because `density`
    imports THIS module (lazily, inside `_m_components`) and a top-level pair
    would be a cycle. The measurement is not restated here, for the same reason
    a second copy of any computed number is forbidden: there is one definition
    of "visible line density" in this repository and it is `density.analyse`.
    """
    import density                                           # noqa: PLC0415
    out = {}
    for spec in specs:
        verts, tris = _concat(groups[spec["id"]], parts)
        a = density.analyse(verts, tris, min_facet_m=min_facet_m)
        n = max(1, spec["count"])
        inst_area = a["area"] / n
        if inst_area <= 0.0:
            out[spec["id"]] = 0.0
            continue
        # `lam_of_plain_box` on ONE instance's area, written out rather than
        # called because that helper takes a whole analysis row and the whole
        # row is the group.
        box = (12.0 * math.sqrt(inst_area / 6.0)) / inst_area
        out[spec["id"]] = a["lam"] / box
    return out


def boxed_control(parts, specs, groups):
    """Every instance of every group replaced by its own bounding box.

    The negative control for `articulation`, and it is not a stand-in for
    something else: this IS what `dorsal_line` and `pylon_pair` were before
    session 4r -- one box per cargo module, two per pylon -- reconstructed from
    the real geometry rather than kept alive as dead code that no shipped path
    calls. `tools/wiring.py`'s whole subject is machinery with no caller, and a
    legacy builder retained only so a test can call it is exactly that.

    Instances are taken as `count` equal runs of the vertex list, which is how
    every builder here emits them. Where a group merges parts of more than one
    instance -- `cargo_module` does, when SPLIT_RAIL_GROUP is off -- the runs
    are not the true instances and the control is then simply "this group as a
    handful of boxes", which is still the null hypothesis it exists to be.
    """
    out = {}
    by_spec = {spec["id"]: spec for spec in specs}
    owner = {gid: by_spec[cid] for cid, gids in groups.items() for gid in gids}
    for gid, (verts, tris) in parts.items():
        spec = owner.get(gid)
        n = max(1, spec["count"] if spec else 1)
        per = max(1, len(verts) // n)
        v, t = [], []
        for i in range(n):
            chunk = verts[i * per:(i + 1) * per] or verts
            lo = [min(p[k] for p in chunk) for k in range(3)]
            hi = [max(p[k] for p in chunk) for k in range(3)]
            for k in range(3):
                if hi[k] - lo[k] < 1e-6:
                    hi[k] = lo[k] + 1e-3
            _box(v, t, [(lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]),
                        (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
                        (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]),
                        (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])])
        out[gid] = (v, t)
    return out


# A schema key that no builder reads is a sourced fact that silently does
# nothing, and this file had two. `cargo_module` carried `rail: True` with the
# `src` "six dark-red modules countable on a continuous raised dorsal rail with
# grey plinths between them", and `rail` appeared nowhere in this module for
# eleven sessions -- the rail and the plinths were sourced, declared, and
# unbuilt. The check below is on the CLASS, not on that instance: CLAUDE.md's
# rule is that a fix applied to one entry of a table and not to the table will
# be needed again.
#
# An exemption must say why and must name what would end it. Metadata keys are
# not builder input and are exempt by kind rather than by name.
SPEC_META_KEYS = ("id", "kind", "auth", "src")
SUPERSEDED_SPEC_KEYS = {
    ("reactor_cooling_fin", "root_taper"):
        "Superseded, and by something better sourced. `planar_blades` replaced "
        "the root-to-tip taper this key sets with PLANFORM, a seven-point "
        "lozenge read off reference/01-station-exterior/exterior more.jpg -- "
        "00-INDEX: 'tapered lozenges, wide at mid-height and narrowing at both "
        "root and tip'. A single taper factor cannot express that shape. The "
        "key survives only because station/schema/station.yaml is not this "
        "module's file to edit; the one-line deletion is proposed in "
        "scratchpad/PATCHES-4r-exterior.md.",
}


def unread_spec_keys(specs, source=None):
    """Schema keys a component declares that no builder in this file reads."""
    if source is None:
        import os                                            # noqa: PLC0415
        with open(os.path.abspath(__file__)) as f:
            source = f.read()
    bad = []
    for spec in specs:
        for key in spec:
            if key in SPEC_META_KEYS:
                continue
            if (spec["id"], key) in SUPERSEDED_SPEC_KEYS:
                continue
            if f'"{key}"' not in source and f"'{key}'" not in source:
                bad.append((spec["id"], key))
    return sorted(bad)


def _selftest():
    import json                                              # noqa: PLC0415
    import os                                                # noqa: PLC0415

    import yaml                                              # noqa: PLC0415

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "station/schema/station.yaml")) as f:
        schema = yaml.safe_load(f)
    with open(os.path.join(root, "station/schema/radius_profile.json")) as f:
        profile = json.load(f)["profile"]
    specs = schema.get("components", [])
    parts = build_all(specs, profile)

    ok = fail = 0

    def check(what, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ok   {what}")
        else:
            fail += 1
            print(f"  FAIL {what} -- {detail}")

    # -- every component is a closed, outward-wound solid -------------------
    for gid, (verts, tris) in sorted(parts.items()):
        holes = boundary_edges(tris)
        check(f"{gid} is closed", not holes,
              f"{len(holes)} boundary edges, first {holes[:3]}")
        vol = signed_volume(verts, tris)
        check(f"{gid} is wound outward", vol > 0.0, f"signed volume {vol:+,.0f}")

    # -- the cobra bays -----------------------------------------------------
    cobra = next(c for c in specs if c["id"] == "cobra_bay")
    groups = cobra_bay_ring(cobra, profile)
    check("a cobra bay emits the five groups its five materials need",
          set(groups) == {"cobra_bay", "cobra_bay_well", "hazard_stripe_cobra",
                          "cobra_beacon_red", "cobra_marker_white"},
          str(sorted(groups)))

    # Nothing floats. The hull flares 100 m through this band, so the test
    # that matters is per bay against the hull under THAT bay, not against a
    # single radius for the ring. Every vertex of the frame must have some
    # part of itself at or below the local hull, which for a bay reduces to:
    # the lowest frame vertex is below the lowest hull sample it spans.
    # Nothing floats, AT EITHER END. Checking the bay's lowest vertex against
    # the hull's lowest sample under it is the weak version of this test and it
    # passed on the build that stood 51 m proud at one end, because the other
    # end was buried and one buried end satisfies a global minimum. The two
    # ends are tested separately for exactly that reason.
    fv = groups["cobra_bay"][0]
    per_bay = len(fv) // cobra["count"]
    floating = []
    for b in range(cobra["count"]):
        chunk = fv[b * per_bay:(b + 1) * per_bay]
        z_lo = min(v[2] for v in chunk)
        z_hi = max(v[2] for v in chunk)
        mid = (z_lo + z_hi) / 2.0
        for label, sel in (("aft", lambda v, m=mid: v[2] <= m),
                           ("fore", lambda v, m=mid: v[2] >= m)):
            end = [v for v in chunk if sel(v)]
            r_min = min(math.hypot(v[0], v[1]) for v in end)
            hull = min(radius_at(profile, v[2]) for v in end)
            if r_min > hull:
                floating.append((b, label, round(r_min, 1), round(hull, 1)))
    check("neither end of any cobra bay floats off the hull", not floating,
          str(floating[:4]))

    # And the other half of the same defect: a bay must not stand further proud
    # of its own hull datum than `protrusion_m` says it does. 26 m is authority
    # 3 off Contract 5, and a fitting scaled off the wrong quantity turns it
    # into 34.5 m without anything saying so -- which is what the first build
    # of the capitals did, scaling them off `depth` (protrusion PLUS however
    # far the frame reaches down to find the hull) instead of off `prot`.
    #
    # Measured against the datum rather than the raw hull, and the datum is
    # recomputed here from the profile rather than taken from the builder: the
    # hull dips up to 13.5 m below the line between a bay's two ends, and a
    # rigid bay bridging a dish is necessarily proud of it at the middle. That
    # is the hull's shape, not the bay's height. 1.25 covers the capital and
    # its beacon (measured 1.18) and rejects the `depth` bug (1.34).
    prot = cobra["protrusion_m"]
    over = []
    for b in range(cobra["count"]):
        chunk = fv[b * per_bay:(b + 1) * per_bay]
        z_lo, z_hi = min(v[2] for v in chunk), max(v[2] for v in chunk)
        r_a, r_b = radius_at(profile, z_lo), radius_at(profile, z_hi)
        worst = max(math.hypot(v[0], v[1])
                    - (r_a + (r_b - r_a) * (v[2] - z_lo) / (z_hi - z_lo))
                    for v in chunk)
        if worst > prot * 1.25:
            over.append((b, round(worst / prot, 2)))
    check("no cobra bay stands more than 1.25x its schema protrusion proud",
          not over, f"protrusion {prot} m, worst multiples {over[:4]}")

    # The envelope guard has to be able to fail. Double the bay's width and it
    # must: 86.7 m of envelope will not fit the aft ring's 74.6 m arc pitch.
    try:
        cobra_bay_ring(dict(cobra, width_m=cobra["width_m"] * 2.0), profile)
        check("the arc-pitch guard rejects bays that would interpenetrate",
              False, "a double-width bay was accepted")
    except ValueError as exc:
        check("the arc-pitch guard rejects bays that would interpenetrate",
              "does not fit" in str(exc), str(exc))

    # And it must ACCEPT the schema's own layout, or it is a guard that only
    # ever says no.
    check("the arc-pitch guard accepts the schema's own layout",
          cobra_bay_ring(cobra, profile) is not None)

    # -- THE COBRA BAYS DO NOT NEED AN APERTURE, and here is the measurement --
    #
    # Session 3z cut 24 mouths in the hull for the docking bays, because
    # `docs/volume-audit.md` §5.1 found a bay you can stand in behind a hull
    # with no hole in it. The obvious next question is whether the 28 cobra
    # bays have the same defect. They have the OPPOSITE one, and the two
    # measurements below are what say so rather than an argument:
    #
    #   1. The well is a CLOSED RECESS whose floor stands COBRA_FLOOR_CLEAR_M
    #      above the hull datum -- a modelled pocket, not a hole. The docking
    #      bays had no recess at all.
    #   2. `cobra_bays` declares `module="components"`, so THIS FILE is its
    #      whole implementation. There is no interior volume behind it to vent
    #      to space, and cutting its floor would open onto unmodelled hull --
    #      a black hole in every frame, which is worse than what is there.
    #
    # Assertion 2 is the live one: the day somebody builds a cobra bay
    # interior and points the register at it, this fires and says the floor
    # now needs cutting. Authority-1 `01-station-exterior/Cobra Bays with
    # starfurries.webp` shows a well with a stowed launch arm lying in it and
    # no opening in its floor, so until then the closed floor is the sourced
    # reading and the hole would be the invention.
    import directory as _dir                                  # noqa: PLC0415
    well_v, well_t = groups["cobra_bay_well"]
    check("the cobra bay well is a closed recess, not a hole in the hull",
          not boundary_edges(well_t) and signed_volume(well_v, well_t) > 0.0,
          f"{len(boundary_edges(well_t))} boundary edges")
    check("the well floor stands above the hull it sits on",
          COBRA_FLOOR_CLEAR_M > 0.0, f"{COBRA_FLOOR_CLEAR_M} m")
    check("cobra_bays is exterior-only, so there is nothing behind it to open",
          _dir.by_key("cobra_bays")["module"] == "components",
          f"module is now {_dir.by_key('cobra_bays')['module']!r} -- an "
          f"interior exists, so the well floor needs an aperture the way "
          f"station/aperture.py gives the docking bays one")

    # -- build_all's contract ------------------------------------------------
    check("build_all still keys single-group builders by component id",
          all(c["id"] in parts for c in specs),
          str([c["id"] for c in specs if c["id"] not in parts]))
    # A multi-group builder that forgets to emit a group named for its
    # component silently deletes that component from validate.py's manifest
    # check. Renaming the SPEC cannot demonstrate the guard -- cobra_bay_ring
    # derives its group names from spec["id"], so it renames along with it.
    # Only a builder that misnames its groups can, so the test registers one.
    BUILDERS["__misnaming_builder"] = lambda _s, _p: {"something_else": ([], [])}
    try:
        build_all([dict(cobra, kind="__misnaming_builder")], profile)
        check("build_all rejects a multi-group builder that drops its id",
              False, "accepted a dict with no group named for the component")
    except ValueError as exc:
        check("build_all rejects a multi-group builder that drops its id",
              "none of them is named for it" in str(exc), str(exc))
    finally:
        del BUILDERS["__misnaming_builder"]

    # -- the cargo train ----------------------------------------------------
    cargo = next(c for c in specs if c["id"] == "cargo_module")
    prev, globals()["SPLIT_RAIL_GROUP"] = SPLIT_RAIL_GROUP, True
    try:
        split = dorsal_line(cargo, profile)
    finally:
        globals()["SPLIT_RAIL_GROUP"] = prev
    merged = dorsal_line(cargo, profile)
    # BOTH BRANCHES ARE BUILT, so the one that is off cannot rot. That is the
    # defect this project has produced nine times -- finished machinery with no
    # caller on the shipped path -- and a flag defaulting to False is the
    # easiest possible way to produce a tenth.
    check("the rail group is named so it cannot inherit the container skin",
          set(split) == {"cargo_module", "cargo_rail"}
          and "cargo_module" not in "cargo_rail",
          f"{sorted(split)}; render_shot.gd binds by longest substring, so a "
          f"group containing 'cargo_module' would render red")
    check("both rail-group branches build closed, outward-wound solids",
          all(not boundary_edges(t) and signed_volume(v, t) > 0.0
              for v, t in list(split.values()) + list(merged.values())))
    check("merging the rail into the module group loses no geometry",
          sum(len(t) for _v, t in merged.values())
          == sum(len(t) for _v, t in split.values()),
          f"{sum(len(t) for _v, t in merged.values()):,} merged against "
          f"{sum(len(t) for _v, t in split.values()):,} split")
    # And the terminal block must not stand on the last module. It did, by 21 m,
    # on the first build of it -- two solids sharing a volume, which is R5's
    # standing counter-example in miniature and which no frame showed.
    rail_v = split["cargo_rail"][0]
    per_row = max(1, cargo["count"] // cargo.get("rows", 1))
    pitch = (cargo["z1"] - cargo["z0"]) / per_row
    last_end = (cargo["z0"] + (cargo["z1"] - cargo["z0"])
                * (per_row - 0.5) / per_row + pitch * cargo.get("fill", 0.72) / 2.0)
    mod_v = split["cargo_module"][0]
    mod_max = max(v[2] for v in mod_v)
    term = [v for v in rail_v if v[2] > last_end]
    check("the cargo terminal block clears the last module",
          term and min(v[2] for v in term) >= last_end - 1e-6,
          f"terminal starts at {min((v[2] for v in term), default=0):.1f}, "
          f"last module ends at {last_end:.1f}")
    check("no cargo geometry leaves the run's own z envelope",
          mod_max <= cargo["z1"] + 1e-6
          and max(v[2] for v in rail_v) <= cargo["z1"] + 1e-6,
          f"module max z {mod_max:.1f}, rail max z "
          f"{max(v[2] for v in rail_v):.1f}, z1 {cargo['z1']}")
    # The guard has to be able to fail: a `fill` that leaves the terminal no
    # room must be refused rather than silently overlapped.
    try:
        dorsal_line(dict(cargo, fill=0.95), profile)
        check("the terminal guard rejects a run with no room for it",
              False, "a fill of 0.95 was accepted")
    except ValueError as exc:
        check("the terminal guard rejects a run with no room for it",
              "no room for its terminal" in str(exc), str(exc))

    # -- ARTICULATION: the gate a cube cannot pass --------------------------
    cgroups = component_groups(specs, profile)
    ratios = articulation(specs, parts, cgroups)
    low = sorted((r, g) for g, r in ratios.items() if r < ARTICULATION_FLOOR)
    check(f"every component carries more than {ARTICULATION_FLOOR}x a plain "
          f"box's line density",
          not low,
          "; ".join(f"{g} {r:.2f}x" for r, g in low[:4]))
    # AND THE CONTROL, which is the whole reason the number above means
    # anything. Re-boxed, EVERY group must fail it -- if a boxed component can
    # still pass, the gate is measuring something other than what it says.
    boxed = articulation(specs, boxed_control(parts, specs, cgroups), cgroups)
    passing = sorted(g for g, r in boxed.items() if r >= ARTICULATION_FLOOR)
    check("and a boxed rebuild of every component fails that gate",
          not passing,
          f"{len(passing)} of {len(boxed)} still passed as bare boxes: "
          f"{passing[:4]}")
    print(f"       worst three: "
          + ", ".join(f"{g} {r:.2f}x"
                      for r, g in sorted((r, g) for g, r in ratios.items())[:3])
          + f"   (boxed control tops out at {max(boxed.values()):.2f}x, "
          f"floor {ARTICULATION_FLOOR})")

    # -- every schema key a component declares is READ ----------------------
    unread = unread_spec_keys(specs)
    check("every schema key a component declares is read by its builder",
          not unread,
          f"{unread} -- a key in station.yaml that no builder reads is a "
          f"sourced fact that silently does nothing. Either consume it or add "
          f"it to SUPERSEDED_SPEC_KEYS with a reason.")
    # The control, and its own name has to be BUILT rather than written out:
    # this check scans THIS FILE for the key as a literal, so a probe spelled
    # out here would find itself and the control would pass vacuously. It did,
    # on the first run -- the check returned [] because the test was reading its
    # own source. Same shape as `drum_ground`'s periodicity assertion comparing
    # a value against itself.
    probe = "__" + "unread" + "_probe_key"
    check("and the spec-key check catches a key nothing reads",
          unread_spec_keys([dict(cargo, **{probe: 1})])
          == [("cargo_module", probe)],
          str(unread_spec_keys([dict(cargo, **{probe: 1})])))

    tris = sum(len(t) for _v, t in parts.values())
    print(f"\n  {tris:,} component triangles across {len(parts)} groups")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
