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


BUILDERS = {
    "planar_blades": planar_blades,
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
