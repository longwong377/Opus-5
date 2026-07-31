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


def pylon_pair(spec, profile):
    """Two opposed pylons carrying the deep-space communications grid.

    The grid is the widest structure on the station -- 2,120 m tip to tip,
    against a hull that is under 1 km at its broadest -- so it dominates the
    silhouette from any angle and is worth placing precisely.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    zc = (z0 + z1) / 2.0
    r0 = radius_at(profile, zc)
    span, gw, th = spec["span_m"], spec["grid_width_m"], spec["thickness_m"] / 2.0

    for i in range(spec["count"]):
        # On +/-X, not +/-Y: the grid must not be edge-on to the North/South
        # docking axis, which is where traffic approaches from.
        a = 2.0 * math.pi * i / spec["count"]
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        # Pylon: a tapering strut from the hull out to the grid panel.
        c = []
        for rr in (r0 * 0.9, r0 + span):
            for zz in (zc - 40, zc + 40):
                c.append((ca * rr - tx * th, sa * rr - ty * th, zz))
        c = [c[0], c[1], c[3], c[2]]
        c += [(x + 2 * tx * th, y + 2 * ty * th, z) for x, y, z in c]
        _box(verts, tris, c)

        # Grid panel at the tip, broad face normal to the station axis.
        rt = r0 + span
        pw = gw / 2.0
        c = []
        for rr in (rt - spec.get("panel_depth_m", 90), rt):
            for zz in (zc - pw, zc + pw):
                c.append((ca * rr - tx * 9, sa * rr - ty * 9, zz))
        c = [c[0], c[1], c[3], c[2]]
        c += [(x + tx * 18, y + ty * 18, z) for x, y, z in c]
        _box(verts, tris, c)
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


def dorsal_line(spec, profile):
    """Modules in a row along one line of longitude, riding the hull surface.

    The orthographic sheet shows the cargo modules as a single dorsal row on the
    mid-section, clearly visible in both top and side views -- which only happens
    for a row lying along one meridian. They were previously wrapped around the
    circumference, which read as surface noise rather than as a cargo train.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    rows = spec.get("rows", 1)
    per_row = max(1, n // rows)
    prot, w = spec["protrusion_m"], spec["width_m"]
    length = (z1 - z0) / per_row * spec.get("fill", 0.72)

    for row in range(rows):
        a = math.radians(spec.get("plane_deg", 0.0)) + row * 2.0 * math.pi / rows
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        for i in range(per_row):
            zc = z0 + (z1 - z0) * (i + 0.5) / per_row
            r0 = radius_at(profile, zc)
            hw = w / 2.0
            quad = []
            for rr in (r0 - 8, r0 + prot):
                for zz in (zc - length / 2, zc + length / 2):
                    quad.append((ca * rr - tx * hw, sa * rr - ty * hw, zz))
            quad = [quad[0], quad[1], quad[3], quad[2]]
            quad += [(x + 2 * tx * hw, y + 2 * ty * hw, z) for x, y, z in quad]
            _box(verts, tris, quad)
    return verts, tris


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

    tris = sum(len(t) for _v, t in parts.values())
    print(f"\n  {tris:,} component triangles across {len(parts)} groups")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
