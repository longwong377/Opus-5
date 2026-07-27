"""Generate a sector's interior: concentric ring decks, spokes, core tube.

This is the thing C-003 and C-004 were assumed to block, and they do not.
They block knowing **which name** attaches to a volume -- which longitudinal
band is the habitat drum, and whether "Red 3" counts outward-in or inward-out.
Neither of those changes **what shape the volume is**. The topology is settled:
sectors are longitudinal bands, decks are concentric radial rings joined by
radial transport tubes, with the core shuttle on the axis.

So names are LATE BINDING. Everything here is generated against
(sector_index, ring_index) and the human-facing label is attached afterwards by
`bind_labels()`. When the two conflicts close, the mapping changes and the
geometry does not.

The buildable unit is a RING ARC, not a whole ring. Ring 1 of the habitat drum
is 2*pi*278 = 1,749 m of circumference; generating all of it for every ring of
every sector would be millions of triangles that are never simultaneously in
frame. An arc is what a streaming cell will be, so it is what the generator
emits.
"""
import json
import math
import os

import yaml

import interior_kit as kit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "station/schema/station.yaml")
PROFILE = os.path.join(ROOT, "station/schema/radius_profile.json")


def load():
    with open(SCHEMA) as f:
        schema = yaml.safe_load(f)
    with open(PROFILE) as f:
        profile = json.load(f)["profile"]
    return schema, profile


def hull_radius_at(profile, z):
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


# Structure between the outer hull surface and the outermost deck floor:
# pressure hull, frames, services, and the thickness of the deck itself.
HULL_ALLOWANCE = 0.86


def sector_radius(schema, profile, sector):
    """Radius of the OUTERMOST DECK FLOOR in a sector -- not the hull envelope.

    The first pass used the mean hull radius and put ring 1 at 328 m and
    **1.18 g**, which is wrong twice over: the envelope includes protrusions
    that are outside the pressure hull entirely, and canon fixes the habitat
    floor at 278.3 m *because* that is where spin gravity is exactly 1.0 g.

    The drum sector is therefore anchored to the canon figure directly, and
    every other sector derives from its own hull radius less an allowance for
    pressure hull, frames, services and deck thickness. Deriving the drum the
    same way would let a rounding error move the one radius the whole rotation
    rate was solved from.
    """
    drum_r = schema["bio_habitat"]["interior_radius_m"]["value"]
    ex = schema["sectors"]["extents_m"][sector]
    zs = [p for p in profile if ex["z0"] <= p["z_m"] <= ex["z1"]]
    hull = sum(p["radius_m"] for p in zs) / max(1, len(zs))

    # Which band is the drum is C-003's open question, so this cannot be keyed
    # on a sector NAME. Key it on geometry instead: the sector whose hull radius
    # is closest to the canon drum radius, over the allowance, is the drum. That
    # answer does not move when the naming does.
    best, best_err = None, None
    for name in schema["sectors"]["extents_m"]:
        e = schema["sectors"]["extents_m"][name]
        band = [p["radius_m"] for p in profile if e["z0"] <= p["z_m"] <= e["z1"]]
        if not band:
            continue
        err = abs(sum(band) / len(band) * HULL_ALLOWANCE - drum_r)
        if best_err is None or err < best_err:
            best, best_err = name, err
    if sector == best:
        return drum_r
    return hull * HULL_ALLOWANCE


def ring_radii(schema, profile, sector):
    """Absolute radius bounds for each ring in a sector, outermost first."""
    r_out = sector_radius(schema, profile, sector)
    return [
        {
            "id": r["id"],
            "r_inner": r["r_inner"] * r_out,
            "r_outer": r["r_outer"] * r_out,
            "r_mid": (r["r_inner"] + r["r_outer"]) / 2.0 * r_out,
        }
        for r in schema["interior_topology"]["provisional_rings"]
    ]


def gravity_at(schema, r):
    """Spin gravity in g at radius r. Ring 1 is a full g; the core is zero.

    Worth generating alongside the geometry rather than looking up later: it is
    what makes a ring a different *place* rather than a different *radius*, and
    it decides what can plausibly be put there.
    """
    rot = schema["station"]["rotation"]
    w = rot["omega_rad_s"]["value"]
    return (w * w * r) / rot["standard_gravity_m_s2"]["value"]


def arc_length(r, degrees):
    return 2.0 * math.pi * r * (degrees / 360.0)


def ring_arc(schema, profile, sector, ring_index, degrees=30.0,
             start_deg=0.0, z_offset=None):
    """One arc of one ring deck: a corridor run bent around the station axis.

    The corridor kit is authored straight, along +Z. Here it is bent: each
    section is placed at its own angle about the axis and rotated to face along
    the arc. A ring corridor is not a straight corridor that happens to be
    curved -- at 278 m radius a 30 degree arc is 146 m long and closes 30
    degrees of heading, which is visible from inside and is a large part of why
    the drum reads as a drum.
    """
    rings = ring_radii(schema, profile, sector)
    ring = rings[ring_index]
    ex = schema["sectors"]["extents_m"][sector]
    z_mid = z_offset if z_offset is not None else (ex["z0"] + ex["z1"]) / 2.0

    r = ring["r_mid"]
    total = arc_length(r, degrees)
    # One kit section per few degrees. Too coarse and the corridor is a polygon;
    # too fine and the section count explodes for no visible gain.
    step_deg = 2.5
    n = max(1, int(round(degrees / step_deg)))
    seg_len = total / n

    verts, tris = [], []
    kit.reset_tags()
    for i in range(n):
        a = math.radians(start_deg + degrees * (i + 0.5) / n)
        v, t = kit.corridor_section(seg_len)
        ca, sa = math.cos(a), math.sin(a)

        # The kit's +Z becomes the tangential direction; its +Y (up) becomes
        # radially INWARD, because in a spun habitat "up" is toward the axis.
        def remap(x, y, z, ca=ca, sa=sa):
            rad = r - y
            ang = z / r
            aa = a + ang - (seg_len / 2.0) / r
            return (rad * math.cos(aa), rad * math.sin(aa), x)

        kit._merge(verts, tris, v, t, remap, (0.0, 0.0, z_mid))

    return verts, tris, {
        "sector": sector,
        "ring": ring["id"],
        "ring_index": ring_index,
        "radius_m": round(r, 1),
        "gravity_g": round(gravity_at(schema, r), 3),
        "arc_deg": degrees,
        "arc_length_m": round(total, 1),
        "sections": n,
        "triangles": len(tris),
    }


def spoke(schema, profile, sector, from_ring, to_ring, angle_deg=0.0, z=None):
    """A radial transport tube between two rings.

    The rosettes draw these as spokes from the outer rings to the axis, and the
    core shuttle reference shows the tube is not a plain extrusion -- smooth
    barrel, collar groups of fine rings at segment joints, an open lattice
    section, a pale collar where it meets the drum wall.
    """
    rings = ring_radii(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    zc = z if z is not None else (ex["z0"] + ex["z1"]) / 2.0
    r0 = rings[to_ring]["r_mid"]
    r1 = rings[from_ring]["r_mid"]

    verts, tris = [], []
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    bore = schema["interior_topology"].get("spoke_bore_m", 9.0)

    nseg = 9
    for k in range(nseg):
        f0, f1 = k / nseg, (k + 1) / nseg
        ra, rb = r0 + (r1 - r0) * f0, r0 + (r1 - r0) * f1
        # Collars at segment joints, lattice in the middle third.
        lattice = 0.34 < f0 < 0.66
        w = bore * (0.62 if lattice else 1.0)
        collar = (k % 3 == 0)
        ww = w * (1.18 if collar else 1.0)
        for sgn in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            pass
        quad = [(ca * ra - sa * ww, sa * ra + ca * ww, zc - ww),
                (ca * ra + sa * ww, sa * ra - ca * ww, zc - ww),
                (ca * rb + sa * ww, sa * rb - ca * ww, zc - ww),
                (ca * rb - sa * ww, sa * rb + ca * ww, zc - ww)]
        quad += [(x, y, z + 2 * ww) for x, y, z in quad]
        kit._slab_free(verts, tris, quad) if hasattr(kit, "_slab_free") else _box(verts, tris, quad)

    return verts, tris, {
        "sector": sector,
        "from_ring": rings[from_ring]["id"],
        "to_ring": rings[to_ring]["id"],
        "length_m": round(r1 - r0, 1),
        "gravity_from_g": round(gravity_at(schema, r1), 3),
        "gravity_to_g": round(gravity_at(schema, r0), 3),
        "triangles": len(tris),
    }


def _box(verts, tris, corners):
    b = len(verts)
    verts.extend(corners)
    for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        tris.append((b + a, b + d, b + c))
        tris.append((b + a, b + e, b + d))


# --- late binding ----------------------------------------------------------
# Geometry is generated against (sector, ring_index). These maps attach the
# human-facing names, and are the ONLY thing that changes when C-003's
# assignment and C-004's numbering close. Nothing above depends on them.

LEVEL_NUMBERING = "outermost_is_1"   # C-004: UNCONFIRMED, see CONFLICTS.md


def bind_labels(schema, sector, ring_index):
    """Human address for a ring, e.g. "Red 1". Late-bound on purpose."""
    rings = schema["interior_topology"]["provisional_rings"]
    if LEVEL_NUMBERING == "outermost_is_1":
        level = ring_index + 1
    else:
        level = len(rings) - ring_index
    return f"{sector.capitalize()} {level}"


def sector_report(schema, profile, sector):
    """Ring radii, gravity and circumference for a sector. The table that makes
    a ring a place rather than a number."""
    out = []
    for i, r in enumerate(ring_radii(schema, profile, sector)):
        # Gravity is quoted at the FLOOR, which is the ring's OUTER radius: in a
        # spun habitat you stand on the outside of the volume looking inward.
        # Quoting the mid-radius understated ring 1 by 9% and would have made
        # the one radius the rotation rate was solved from look wrong.
        out.append({
            "label": bind_labels(schema, sector, i),
            "ring": r["id"],
            "floor_r_m": round(r["r_outer"], 1),
            "headroom_m": round(r["r_outer"] - r["r_inner"], 1),
            "floor_g": round(gravity_at(schema, r["r_outer"]), 3),
            "ceiling_g": round(gravity_at(schema, r["r_inner"]), 3),
            "circumference_m": round(2 * math.pi * r["r_outer"], 1),
        })
    return out
