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


def _selftest_winding():
    v, t = [], []
    _box(v, t, [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)])
    vol = signed_volume(v, t)
    if abs(vol - 1.0) > 1e-9:
        raise AssertionError(
            f"_box winding is inside-out: unit cube signed volume {vol:+.3f}, expected +1.000")


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


def radial_band(spec, profile):
    """N shallow blocks around the circumference, hugging the hull.

    Used for the cobra bays and the cargo modules, which read as surface
    articulation rather than as protruding structures.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    prot, w = spec["protrusion_m"], spec["width_m"]
    # Distribute around the circumference and along z together, so a large
    # count wraps into several rings rather than crowding one.
    per_ring = min(n, 14)
    rings = max(1, math.ceil(n / per_ring))
    placed = 0
    for ring in range(rings):
        zc = z0 + (z1 - z0) * (ring + 0.5) / rings
        r0 = radius_at(profile, zc)
        k = min(per_ring, n - placed)
        for i in range(k):
            a = 2.0 * math.pi * i / k + ring * math.pi / max(1, per_ring)
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa, ca
            hw = w / 2.0
            c = []
            for rr in (r0 - 6, r0 + prot):
                for zz in (zc - hw, zc + hw):
                    c.append((ca * rr - tx * hw * 0.5, sa * rr - ty * hw * 0.5, zz))
            c = [c[0], c[1], c[3], c[2]]
            c += [(x + tx * hw, y + ty * hw, z) for x, y, z in c]
            _box(verts, tris, c)
            placed += 1
    return verts, tris


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


def dome_mesh(verts, tris, cx, cy, cz, out, radius, height, rings=6, segs=14):
    """Half-ellipsoid bulging along an arbitrary outward direction."""
    ox, oy, oz = out
    # Build an orthonormal frame with `out` as the pole.
    if abs(oz) < 0.9:
        ux, uy, uz = 0.0, 0.0, 1.0
    else:
        ux, uy, uz = 1.0, 0.0, 0.0
    ax = uy * oz - uz * oy
    ay = uz * ox - ux * oz
    az = ux * oy - uy * ox
    al = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
    ax, ay, az = ax / al, ay / al, az / al
    bx = oy * az - oz * ay
    by = oz * ax - ox * az
    bz = ox * ay - oy * ax

    base = len(verts)
    for r in range(rings + 1):
        phi = (math.pi / 2) * r / rings
        rr, hh = radius * math.cos(phi), height * math.sin(phi)
        for sgm in range(segs):
            th = 2 * math.pi * sgm / segs
            c, sn = math.cos(th) * rr, math.sin(th) * rr
            verts.append((cx + ax * c + bx * sn + ox * hh,
                          cy + ay * c + by * sn + oy * hh,
                          cz + az * c + bz * sn + oz * hh))
    for r in range(rings):
        for sgm in range(segs):
            a = base + r * segs + sgm
            b = base + r * segs + (sgm + 1) % segs
            c = base + (r + 1) * segs + (sgm + 1) % segs
            d = base + (r + 1) * segs + sgm
            tris.append((a, b, c))
            tris.append((a, c, d))


def domes(spec, profile):
    """Hemispherical blisters on the hull -- observation domes and rotundas.

    Observation Dome 1 is Command & Control, so these are not decoration: they
    are the places the player stands and looks out of, and their positions have
    to survive into the interior layout.
    """
    verts, tris = [], []
    z0, z1 = spec["z0"], spec["z1"]
    n = spec["count"]
    rad, hgt = spec["radius_m"], spec["height_m"]
    rows = spec.get("rows", 1)
    per_row = max(1, n // rows)
    for row in range(rows):
        zc = z0 + (z1 - z0) * (row + 0.5) / rows if rows > 1 else (z0 + z1) / 2.0
        r0 = radius_at(profile, zc)
        for i in range(per_row):
            a = 2 * math.pi * i / per_row + math.radians(spec.get("phase_deg", 0.0))
            ca, sa = math.cos(a), math.sin(a)
            dome_mesh(verts, tris, ca * r0 * 0.97, sa * r0 * 0.97, zc,
                      (ca, sa, 0.0), rad, hgt)
    return verts, tris


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
    return verts, tris


BUILDERS = {
    "plate_array": plate_array,
    "planar_blades": planar_blades,
    "domes": domes,
    "swept_fins": swept_fins,
    "dorsal_line": dorsal_line,
    "radial_array": radial_array,
    "pylon_pair": pylon_pair,
    "radial_band": radial_band,
}


def build_all(specs, profile):
    """Return {component_id: (verts, tris)} for every component in the schema."""
    out = {}
    for spec in specs:
        builder = BUILDERS.get(spec["kind"])
        if builder is None:
            raise ValueError(f"unknown component kind: {spec['kind']}")
        out[spec["id"]] = builder(spec, profile)
    return out
