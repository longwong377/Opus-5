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
    """Append an axis-agnostic box given 8 corners in the standard order."""
    b = len(verts)
    verts.extend(corners)
    for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        tris.append((b + a, b + c, b + d))
        tris.append((b + a, b + d, b + e))


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
    root_frac = spec.get("root_taper", 0.55)

    for side in (1, -1):
        a = plane if side > 0 else plane + math.pi
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        for i in range(per_side):
            zc = z0 + (z1 - z0) * (i + 0.5) / per_side
            r0 = radius_at(profile, zc)
            # Blades taper: wide at the root, narrower at the tip.
            for seg, (f0, f1) in enumerate(((0.0, 0.5), (0.5, 1.0))):
                ri = r0 * 0.9 + span * f0
                ro = r0 * 0.9 + span * f1
                c0 = chord * (1.0 - (1.0 - root_frac) * f0)
                c1 = chord * (1.0 - (1.0 - root_frac) * f1)
                quad = [
                    (ca * ri - tx * th, sa * ri - ty * th, zc - c0 / 2),
                    (ca * ri - tx * th, sa * ri - ty * th, zc + c0 / 2),
                    (ca * ro - tx * th, sa * ro - ty * th, zc + c1 / 2),
                    (ca * ro - tx * th, sa * ro - ty * th, zc - c1 / 2),
                ]
                quad += [(x + 2 * tx * th, y + 2 * ty * th, z) for x, y, z in quad]
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


def _dome_mesh(verts, tris, cx, cy, cz, out, radius, height, rings=6, segs=14):
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
            _dome_mesh(verts, tris, ca * r0 * 0.97, sa * r0 * 0.97, zc,
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
        # Root at z0, tip swept aft-to-fore by `sweep` and narrowing.
        quad = [
            (ca * r0 * 0.95 - tx * th, sa * r0 * 0.95 - ty * th, z0),
            (ca * r0 * 0.95 - tx * th, sa * r0 * 0.95 - ty * th, z1),
            (ca * (r0 + span) - tx * th, sa * (r0 + span) - ty * th, z1 + sweep),
            (ca * (r0 + span) - tx * th, sa * (r0 + span) - ty * th, z1 + sweep * 0.62),
        ]
        quad += [(x + 2 * tx * th, y + 2 * ty * th, z) for x, y, z in quad]
        _box(verts, tris, quad)
    return verts, tris


BUILDERS = {
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
