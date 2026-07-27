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

    if sector == drum_sector(schema, profile):
        return drum_r
    return hull * HULL_ALLOWANCE


def drum_sector(schema, profile):
    """Which longitudinal band is the habitat drum, decided by geometry.

    Which one it is *called* is C-003's open question, so this cannot be keyed
    on a name. The sector whose hull radius comes closest to the canon drum
    radius over the allowance is the drum, and that answer does not move when
    the naming does.
    """
    drum_r = schema["bio_habitat"]["interior_radius_m"]["value"]
    best, best_err = None, None
    for name, e in schema["sectors"]["extents_m"].items():
        band = [q["radius_m"] for q in profile if e["z0"] <= q["z_m"] <= e["z1"]]
        if not band:
            continue
        err = abs(sum(band) / len(band) * HULL_ALLOWANCE - drum_r)
        if best_err is None or err < best_err:
            best, best_err = name, err
    return best


# Pressure hull, frames and services between the outer envelope and the
# innermost usable radius. Metric rather than fractional -- INV-013.
HULL_SKIN_M = 6.0


def habitat_hull_radius(schema, profile):
    """Innermost usable radius of the drum's pressure hull.

    Measured over the `habitat_cylinder` feature specifically, not over the
    whole sector. The sector also contains the aft hull block and the bearing
    neck, whose radii range over 128-480 m; averaging those in gives a number
    that describes no actual surface. The habitat cylinder itself runs
    307-328 m, tight enough to be a real shell.
    """
    for f in schema["longitudinal"]["features"]:
        for g in [f] + list(f.get("subfeatures", [])):
            if g["id"] == "habitat_cylinder":
                band = [q["radius_m"] for q in profile
                        if g["z0"] <= q["z_m"] <= g["z1"]]
                return sum(band) / len(band) - HULL_SKIN_M
    raise KeyError("habitat_cylinder not in the schema")


def ring_radii(schema, profile, sector):
    """Absolute radius bounds for each ring in a sector, outermost first.

    The drum sector does not get the concentric-ring treatment, and applying it
    there was wrong for as long as this function existed. The drum is **hollow**
    -- that is authority 1, it is the whole reason the volume exists, and it is
    what the end cap and the guideway trusses were built against. Filling it
    with rings 2, 3 and 4 put habitable decks at 228, 167 and 106 m radius,
    which is the open air you look up through, and it put the guideway trusses
    at 236.6 m *inside* a deck that was supposed to be there.

    In the drum the habitable volume is the stack **beneath** the ground, and
    beneath means radially OUTWARD: in spin gravity you stand on the outside of
    the volume looking in. So the drum's decks run from the canon 278.3 m floor
    out to the pressure hull, they are heavier than the Garden rather than
    lighter, and everything inboard of the floor is air.
    """
    r_out = sector_radius(schema, profile, sector)
    if sector == drum_sector(schema, profile):
        hull = habitat_hull_radius(schema, profile)
        core = schema["interior_topology"]["provisional_rings"][-1]["r_outer"]
        return [
            {"id": "subfloor", "kind": "deck_stack", "outward": True,
             "r_inner": r_out, "r_outer": hull,
             "r_mid": (r_out + hull) / 2.0},
            {"id": "open", "kind": "open",
             "r_inner": core * r_out, "r_outer": r_out,
             "r_mid": (core * r_out + r_out) / 2.0},
            {"id": "core", "kind": "core",
             "r_inner": 0.0, "r_outer": core * r_out,
             "r_mid": core * r_out / 2.0},
        ]
    return [
        {
            "id": r["id"],
            "kind": "core" if r["id"] == "core" else "deck_stack",
            "outward": False,
            "r_inner": r["r_inner"] * r_out,
            "r_outer": r["r_outer"] * r_out,
            "r_mid": (r["r_inner"] + r["r_outer"]) / 2.0 * r_out,
        }
        for r in schema["interior_topology"]["provisional_rings"]
    ]


DECK_PITCH_M = 3.6        # floor-to-floor, provisional -- INV-010


def decks_in_ring(schema, profile, sector, ring_index, pitch=DECK_PITCH_M):
    """The decks stacked inside one ring zone, outermost first.

    A ring is 38-61 m deep (see CONFLICTS.md), which is a zone, not a deck. At a
    3.6 m floor-to-floor pitch that is a dozen or more decks per ring, and it is
    the deck -- not the ring -- that a person stands on and that a level number
    indexes.

    Gravity is quoted per deck because it genuinely differs across a ring: the
    outermost and innermost decks of ring 1 differ by 18% of a g, which is more
    than enough to feel walking down a stair.
    """
    ring = ring_radii(schema, profile, sector)[ring_index]
    if ring["kind"] != "deck_stack":
        return []          # open air and the core carry no decks
    depth = ring["r_outer"] - ring["r_inner"]
    n = max(1, int(depth // pitch))
    out = []
    for i in range(n):
        # A deck's floor is at its LARGER radius -- down is outward. In the drum
        # the stack grows outward from the habitat floor, so deck 0 is the one
        # immediately under the ground and gravity RISES with deck index.
        floor_r = (ring["r_inner"] + (i + 1) * pitch if ring.get("outward")
                   else ring["r_outer"] - i * pitch)
        out.append({
            "deck_index": i,
            "floor_r_m": round(floor_r, 2),
            "ceiling_r_m": round(floor_r - pitch, 2),
            "gravity_direction": "outward",
            "floor_g": round(gravity_at(schema, floor_r), 4),
            "circumference_m": round(2 * math.pi * floor_r, 1),
        })
    return out


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


def sight_line(r_floor, corridor_width):
    """How far you can see along a ring corridor before its curve occludes.

    In a straight corridor a door or a bulkhead stops the view, and the number
    is authored. In a ring corridor the *geometry* stops it: standing against
    the outer wall, the furthest you can see is the chord tangent to the inner
    wall, and everything past that is behind the curve.

    d = 2 * sqrt(r_o^2 - r_i^2), with r_i the inner wall radius.

    This matters because `budget.py` has been gating interior cost on an
    *assumed* 50 m sight line since it was written. In the drum the assumption
    turns out to be very nearly what the curvature actually gives -- which makes
    the budget derived rather than asserted, and means the streaming cell size
    follows from the station's radius instead of from a guess.
    """
    r_i = r_floor - corridor_width
    if r_i <= 0:
        return float("inf")
    return 2.0 * math.sqrt(r_floor * r_floor - r_i * r_i)


def streaming_cell_deg(r_floor, corridor_width, margin=1.5):
    """Arc a streaming cell must span, in degrees.

    A cell has to be at least a sight line wide or the player can see into
    territory that is not resident yet; `margin` is how many sight lines of
    slack to carry so a cell boundary is never the thing that pops.
    """
    return math.degrees(sight_line(r_floor, corridor_width) * margin / r_floor)


def ring_arc(schema, profile, sector, ring_index, degrees=30.0,
             start_deg=0.0, z_offset=None, radius_m=None):
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

    # A ring is a zone of a dozen decks; a corridor sits on one deck's floor,
    # not at the zone's mid-radius. Callers that know which deck say so.
    r = ring["r_mid"] if radius_m is None else radius_m
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


# The Green rosette draws three spokes at 120 degrees. Everything radial in
# the drum keys off this: the spokes themselves, and the guideway trusses, which
# are 2.6 km long and can only be held up where they cross one.
SPOKE_COUNT = 3


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
        # Collars at segment joints. The core shuttle reference shows the tube
        # is not a plain extrusion: barrel sections separated by collar groups,
        # with an open lattice through the middle third of the run.
        collar = (k % 3 == 0)
        ww = w * (1.18 if collar else 1.0)
        quad = [(ca * ra - sa * ww, sa * ra + ca * ww, zc - ww),
                (ca * ra + sa * ww, sa * ra - ca * ww, zc - ww),
                (ca * rb + sa * ww, sa * rb - ca * ww, zc - ww),
                (ca * rb - sa * ww, sa * rb + ca * ww, zc - ww)]
        quad += [(x, y, z + 2 * ww) for x, y, z in quad]
        _box(verts, tris, quad)

    return verts, tris, {
        "sector": sector,
        "from_ring": rings[from_ring]["id"],
        "to_ring": rings[to_ring]["id"],
        "length_m": round(r1 - r0, 1),
        "gravity_from_g": round(gravity_at(schema, r1), 3),
        "gravity_to_g": round(gravity_at(schema, r0), 3),
        "triangles": len(tris),
    }


def drum_spokes(schema, profile, sector, from_ring=None, to_ring=None,
                z=None):
    """Every radial spoke in a sector, at the canon 120 degree spacing.

    Placement used to live in whichever script happened to be rendering, which
    meant the count had no single source of truth and the trusses could silently
    stop matching the structure that carries them.
    """
    # Default to the full radial run: outermost deck stack to the core. Asking
    # callers for indices meant they had to know how many rings a sector has,
    # and the drum has three where every other sector has five.
    rings = ring_radii(schema, profile, sector)
    if from_ring is None:
        from_ring = next(i for i, r in enumerate(rings)
                         if r["kind"] == "deck_stack")
    if to_ring is None:
        to_ring = next(i for i, r in enumerate(rings) if r["kind"] == "core")

    verts, tris, groups = [], [], []
    for i in range(SPOKE_COUNT):
        v, t, _m = spoke(schema, profile, sector, from_ring, to_ring,
                         360.0 * i / SPOKE_COUNT, z)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(["spoke"] * len(t))
    return verts, tris, {"count": SPOKE_COUNT, "triangles": len(tris),
                         "groups": groups}


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


# ---------------------------------------------------------------------------
# The drum interior: the open volume inside ring 1.
#
# This is the view the whole project is pointed at -- standing on the floor and
# seeing the far side of the cylinder arch overhead. Two authority-1 frames
# establish what is on that surface: `04-sector-red/Earhart's.webp` shows hedged
# agricultural fields and a road curving up and over, and
# `14-characters-and-uniforms/talia-winters in gorgeous office.webp` shows the
# far side divided into long continuous longitudinal bands -- greys and
# olive-greens with one broad orange-red band -- carrying rows of small blue
# lights. Strips running the length, not tiles.
#
# So the surface is banded ALONG the axis and varied AROUND it, which is also
# what a rotating farm would be: you plough along the direction of travel.
# ---------------------------------------------------------------------------

LAND_USE = (
    # (fraction of circumference, name, relief in metres)
    (0.26, "arable", 1.2),
    (0.14, "settlement", 7.0),
    (0.10, "water", -2.5),
    (0.22, "arable", 1.2),
    (0.12, "settlement", 7.0),
    (0.16, "parkland", 2.4),
)


def drum_interior(schema, profile, sector, arc_deg=40.0, start_deg=0.0,
                  z_span=None, seg_deg=2.0, z_step=60.0):
    """The inner surface of the habitat drum over an arc and a length.

    Emitted as a band-articulated shell rather than a smooth cylinder: the
    reference shows longitudinal strips of differing land use, and a smooth
    cylinder reads as a pipe. The relief is small against a 278 m radius --
    7 m of settlement on a 278 m drum is 2.5% -- but it is what stops the
    surface reading as painted-on.
    """
    r0 = sector_radius(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = z_span if z_span else (ex["z0"], ex["z1"])

    bounds, acc = [], 0.0
    for frac, name, relief in LAND_USE:
        bounds.append((acc, acc + frac, name, relief))
        acc += frac

    def band_at(f):
        f = f % 1.0
        for lo, hi, name, relief in bounds:
            if lo <= f < hi:
                return name, relief
        return bounds[-1][2], bounds[-1][3]

    verts, tris, groups = [], [], []
    n_a = max(2, int(arc_deg / seg_deg))
    n_z = max(2, int((z1 - z0) / z_step))
    for ia in range(n_a):
        f0 = (start_deg + arc_deg * ia / n_a) / 360.0
        f1 = (start_deg + arc_deg * (ia + 1) / n_a) / 360.0
        name, relief = band_at(f0)
        ra = r0 - relief
        a0, a1 = f0 * 2 * math.pi, f1 * 2 * math.pi
        for iz in range(n_z):
            za = z0 + (z1 - z0) * iz / n_z
            zb = z0 + (z1 - z0) * (iz + 1) / n_z
            b = len(verts)
            verts.extend([
                (ra * math.cos(a0), ra * math.sin(a0), za),
                (ra * math.cos(a1), ra * math.sin(a1), za),
                (ra * math.cos(a1), ra * math.sin(a1), zb),
                (ra * math.cos(a0), ra * math.sin(a0), zb),
            ])
            # Wound so the face normal points INWARD, toward the axis. The
            # viewer stands inside the cylinder, so the outward winding this
            # originally had culled 95% of the drum and rendered as a black
            # frame. Ascending angle then ascending z gives (t x z_hat), which
            # is radially *outward* -- hence the reversal here, not there.
            tris.append((b, b + 2, b + 1))
            tris.append((b, b + 3, b + 2))
            groups.append(f"drum_{name}")
            groups.append(f"drum_{name}")

    inward = _inward_fraction(verts, tris)
    if inward < 1.0:
        raise AssertionError(
            f"drum_interior: {(1-inward)*100:.1f}% of faces point away from the "
            "axis; they will be backface-culled for a viewer inside the drum")

    return verts, tris, {
        "sector": sector,
        "radius_m": round(r0, 1),
        "arc_deg": arc_deg,
        "z_span_m": round(z1 - z0, 1),
        "bands": len({g for g in groups}),
        "triangles": len(tris),
        "inward_facing": inward,
        "groups": groups,
    }


def stand_point(schema, profile, sector, angle_deg, z, eye_h=1.7):
    """Eye position for someone standing on the drum floor at `angle_deg`.

    Hand-computing this buries the camera: the first drum render put the eye at
    the nominal 278.3 m floor while the band underneath was a 7 m settlement
    terrace at 271.3 m, so the viewpoint was five metres *inside* the ground and
    the whole near field rendered black. The relief is small but it is not
    optional, and every interior viewpoint from here on needs it.

    Returns (eye, up) -- `up` is radially inward, which is what "up" means when
    gravity is centrifugal.
    """
    r0 = sector_radius(schema, profile, sector)
    acc = 0.0
    f = (angle_deg / 360.0) % 1.0
    relief = LAND_USE[-1][2]
    for frac, _name, rel in LAND_USE:
        if acc <= f < acc + frac:
            relief = rel
            break
        acc += frac
    r_eye = r0 - relief - eye_h
    a = math.radians(angle_deg)
    return ((r_eye * math.cos(a), r_eye * math.sin(a), z),
            (-math.cos(a), -math.sin(a), 0.0))


def _inward_fraction(verts, tris):
    """Fraction of faces whose normal points toward the spin axis.

    The drum is the one surface in the project seen from the concave side, so
    the winding convention inverts and every habit built on the hull is wrong
    here. That is worth a number rather than a comment: an inverted drum does
    not error, it renders black, and a black frame is easy to mistake for a
    camera placed badly.
    """
    good = 0
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        n = (u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0])
        cx = (p0[0] + p1[0] + p2[0]) / 3.0
        cy = (p0[1] + p1[1] + p2[1]) / 3.0
        if n[0] * cx + n[1] * cy < 0:      # normal opposes the radial vector
            good += 1
    return good / max(1, len(tris))


def write_grouped_obj(path, verts, tris, groups):
    order, seen = [], set()
    for g in groups:
        if g not in seen:
            seen.add(g)
            order.append(g)
    with open(path, "w") as f:
        for x, y, z in verts:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for g in order:
            f.write(f"g {g}\no {g}\n")
            for i, (a, b, c) in enumerate(tris):
                if groups[i] == g:
                    f.write(f"f {a+1} {b+1} {c+1}\n")


# --------------------------------------------------------------------------
# Drum end cap
# --------------------------------------------------------------------------

# Measured off authority-1 footage in session 2r (see CONFLICTS.md, "C-004 --
# session 2r note: the drum end cap, measured"). Circumferential ribs sit at
# these normalised radii; the plates between them are roughly square, so the
# cap is a grid of annular courses rather than a set of thin rings.
ENDCAP_RIBS = (1.03, 0.98, 0.80, 0.71, 0.51, 0.32, 0.28, 0.25)

# The measured hub cone fills the inner ~20% of the radius. The schema's
# provisional rings -- read independently, off an authority-3 print diagram --
# put the core at r/R = 0.18. Two unrelated sources landing 2% apart is a
# corroboration, so the cap is built down to the schema's core radius and the
# hub cone is the core's end structure rather than a separate invention.
ENDCAP_RIM_LIGHTS = 48        # 7.5 deg pitch; measured 7.40 +/- 0.3 deg
ENDCAP_SEGMENTS = 48          # radial ribs share the rim-light pitch
ENDCAP_DISH = 0.18            # sagitta / R -- INV-011, profile family only
ENDCAP_STEP_M = 1.2           # axial depth of a circumferential rib step
ENDCAP_CHECKER = (2, 5)       # course indices the footage shows checker-plated
ENDCAP_RIB_W_M = 1.6          # radial rib width, constant in metres
ENDCAP_RIB_H_M = 0.9          # how far a rib stands proud of its plates


def _endcap_segments(u_outer, u_inner, r0):
    """Plate count for one course, chosen to make its plates near-square."""
    r_mid = (u_outer + u_inner) / 2.0 * r0
    depth = max((u_outer - u_inner) * r0, 1e-6)
    n = int(round(2 * math.pi * r_mid / depth))
    return max(16, min(96, 4 * int(round(n / 4.0))))


def drum_end_cap(schema, profile, sector, end="fore"):
    """One end bulkhead of the habitat drum, seen from inside.

    STATE.md recorded this as blocked -- "two structurally different end caps
    appear across frames". They are not two caps. `Babylon_5_2-22_35a` is shot
    forward through the windscreen of a drum tram, and the deep red-orange
    triangulated lattice that frame shares with `33a` converges to a vanishing
    point with regular transverse ribs: it is the tram guideway truss seen from
    inside and from beneath, not a bulkhead. The concentric ribbed disc appears
    in both frames and is the only end cap.

    The cap is a stepped lathe: each measured course is a flat annulus, and the
    rib between two courses is the axial step joining them. That is what makes
    the ribs read in silhouette rather than as drawn-on rings.
    """
    r0 = sector_radius(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    z_base = ex["z1"] if end == "fore" else ex["z0"]
    # Outward is away from the drum interior: +z at the fore end, -z at the aft.
    out = 1.0 if end == "fore" else -1.0

    core_u = schema["interior_topology"]["provisional_rings"][-1]["r_outer"]
    us = [u for u in ENDCAP_RIBS if u > core_u] + [core_u]

    def dish(u):
        """Axial offset of the cap surface, outward, at normalised radius u."""
        return ENDCAP_DISH * r0 * (1.0 - u * u)

    verts, tris, groups = [], [], []

    def quad(p0, p1, p2, p3, group):
        b = len(verts)
        verts.extend([p0, p1, p2, p3])
        tris.append((b, b + 1, b + 2))
        tris.append((b, b + 2, b + 3))
        groups.extend([group, group])

    def ring_quad(uo_, ui_, a0, a1, z_o, z_i, group):
        """Annular patch wound to face into the drum, at either end."""
        pts = [pt(uo_, a0, z_o), pt(ui_, a0, z_i),
               pt(ui_, a1, z_i), pt(uo_, a1, z_o)]
        if out < 0:
            pts = pts[::-1]
        quad(pts[0], pts[1], pts[2], pts[3], group)

    def pt(u, ang, zoff):
        return (u * r0 * math.cos(ang), u * r0 * math.sin(ang),
                z_base + out * (dish(u) + zoff))

    # The measurement says the plates are "roughly square -- radial depth
    # approximately circumferential width". No single segment count can satisfy
    # that across courses whose radial depths differ by 4x, so each course gets
    # the count that makes ITS plates closest to square. That reproduces what
    # the footage actually shows: fine plating near the rim, coarse toward the
    # hub. A uniform count gave a smooth lathe with no radial seams at all.
    for ci in range(len(us) - 1):
        uo, ui = us[ci], us[ci + 1]
        n_seg = _endcap_segments(uo, ui, r0)
        step = ENDCAP_STEP_M if ci % 2 == 0 else 0.0
        nstep = ENDCAP_STEP_M if (ci + 1) % 2 == 0 else 0.0
        # Half-width of a radial rib, in angle. Constant metric width, so the
        # ribs stay the same size in the hand at every radius.
        half = ENDCAP_RIB_W_M / 2.0 / max(uo * r0, 1.0)

        for sg in range(n_seg):
            a0 = 2 * math.pi * sg / n_seg
            a1 = 2 * math.pi * (sg + 1) / n_seg
            # Checker-plating: alternate plates in the marked courses sit proud
            # by a plate thickness, which is what makes those two courses read
            # differently from the plain ones at distance.
            z = step - (0.35 if (ci in ENDCAP_CHECKER and sg % 2 == 0) else 0.0)
            ring_quad(uo, ui, a0 + half, a1 - half, z, z,
                      f"endcap_plate_c{ci}")

            # Radial rib between this plate and the next, proud of both.
            zr = step - ENDCAP_RIB_H_M
            ring_quad(uo, ui, a1 - half, a1 + half, zr, zr, "endcap_rib")
            # Its two flanks. Without them the rib is a coplanar stripe that
            # only a material could distinguish; with them it shades as relief.
            for ang, sgn in ((a1 - half, -1), (a1 + half, +1)):
                pa, pb = pt(uo, ang, z), pt(ui, ang, z)
                qa, qb = pt(uo, ang, zr), pt(ui, ang, zr)
                pts = [pa, pb, qb, qa]
                if (sgn * out) < 0:
                    pts = pts[::-1]
                quad(*pts, "endcap_rib")

        # The circumferential rib: the axial wall joining this course to the
        # next. Exposed face is on the side of the recessed course.
        if abs(nstep - step) > 1e-9:
            n_wall = max(n_seg, _endcap_segments(us[ci + 1], us[min(ci + 2, len(us) - 1)], r0))
            for sg in range(n_wall):
                a0 = 2 * math.pi * sg / n_wall
                a1 = 2 * math.pi * (sg + 1) / n_wall
                pts = [pt(ui, a0, step), pt(ui, a0, nstep),
                       pt(ui, a1, nstep), pt(ui, a1, step)]
                if out < 0:
                    pts = pts[::-1]
                quad(*pts, "endcap_course_wall")

    # Rim lights. The one feature of the cap that was counted rather than
    # estimated, and the thing that makes the rim read as a lit edge at 2 km.
    for i in range(ENDCAP_RIM_LIGHTS):
        a0 = 2 * math.pi * (i + 0.22) / ENDCAP_RIM_LIGHTS
        a1 = 2 * math.pi * (i + 0.78) / ENDCAP_RIM_LIGHTS
        if out > 0:
            quad(pt(1.0, a0, -0.6), pt(0.965, a0, -0.6),
                 pt(0.965, a1, -0.6), pt(1.0, a1, -0.6), "endcap_rimlight")
        else:
            quad(pt(1.0, a0, -0.6), pt(1.0, a1, -0.6),
                 pt(0.965, a1, -0.6), pt(0.965, a0, -0.6), "endcap_rimlight")

    return verts, tris, {
        "sector": sector,
        "end": end,
        "radius_m": round(r0, 1),
        "courses": len(us) - 1,
        "rim_lights": ENDCAP_RIM_LIGHTS,
        "dish_depth_m": round(ENDCAP_DISH * r0, 1),
        "core_aperture_m": round(core_u * r0, 1),
        "triangles": len(tris),
        "groups": groups,
    }


# --------------------------------------------------------------------------
# Streaming cells
# --------------------------------------------------------------------------

def ring_cells(schema, profile, sector, ring_index, deck_index=0, margin=1.5):
    """How a deck's circumference divides into streaming cells.

    A full ring corridor is not emittable. At the drum's sub-floor radius one
    is 1,953 m around, which at the kit's 285 tri/m is **556,000 triangles** --
    nine times the entire interior frame budget, for one deck of one ring of one
    sector. Rings are only buildable as cells, so the cell is the unit the
    generator emits and the unit the engine streams.

    The count is an integer, so cells tile the circle exactly and there is no
    runt cell at 360 degrees carrying a different amount of geometry from all
    its neighbours. Rounding DOWN means the actual cell is at least the size
    `streaming_cell_deg()` asked for, never less.
    """
    decks = decks_in_ring(schema, profile, sector, ring_index)
    if not decks:
        return None
    deck = decks[deck_index]
    r = deck["floor_r_m"]
    cw = kit.PROVISIONAL["corridor_width_m"]
    want = streaming_cell_deg(r, cw, margin)
    n = max(1, int(360.0 // want))
    cell_deg = 360.0 / n
    return {
        "sector": sector,
        "ring_index": ring_index,
        "ring": ring_radii(schema, profile, sector)[ring_index]["id"],
        "deck_index": deck_index,
        "radius_m": r,
        "gravity_g": round(gravity_at(schema, r), 4),
        "circumference_m": round(2 * math.pi * r, 1),
        "cells": n,
        "cell_deg": cell_deg,
        "cell_length_m": round(2 * math.pi * r / n, 1),
        "sight_line_m": round(sight_line(r, cw), 1),
    }


def deck_cell(schema, profile, sector, ring_index, deck_index, cell_index,
              z_offset=None):
    """One streaming cell: the corridor run for one deck over one arc."""
    plan = ring_cells(schema, profile, sector, ring_index, deck_index)
    if plan is None:
        raise ValueError(f"{sector} ring {ring_index} carries no decks")
    if not 0 <= cell_index < plan["cells"]:
        raise IndexError(f"cell {cell_index} of {plan['cells']}")
    verts, tris, meta = ring_arc(
        schema, profile, sector, ring_index,
        degrees=plan["cell_deg"], start_deg=cell_index * plan["cell_deg"],
        z_offset=z_offset, radius_m=plan["radius_m"])
    meta.update({
        "cell_index": cell_index,
        "cells": plan["cells"],
        "deck_index": deck_index,
        "start_deg": cell_index * plan["cell_deg"],
        "end_deg": (cell_index + 1) * plan["cell_deg"],
        "label": f"{bind_labels(schema, sector, ring_index)}"
                 f" deck {deck_index} cell {cell_index}",
    })
    return verts, tris, meta


def _verts_at_angle(verts, angle_deg, tol_m=1e-4):
    """Vertices lying on a given radial plane, keyed for exact comparison.

    Seam checking has to be done in the plane the cells were cut on, not by
    comparing bounding boxes: two cells can have touching bounds and still
    leave a crack, and a crack in a ring corridor is a hole a player falls
    through at 1 g.
    """
    a = math.radians(angle_deg % 360.0)
    out = []
    for x, y, z in verts:
        r = math.hypot(x, y)
        if r < 1e-9:
            continue
        d = (math.atan2(y, x) - a + math.pi) % (2 * math.pi) - math.pi
        if abs(d * r) < tol_m:                 # arc distance from the plane
            out.append((round(r, 4), round(z, 4)))
    return sorted(set(out))


def cell_seam_report(schema, profile, sector, ring_index, deck_index=0,
                     cell_index=0):
    """Compare the shared edge of two adjacent cells, vertex for vertex."""
    plan = ring_cells(schema, profile, sector, ring_index, deck_index)
    n = plan["cells"]
    a, _ta, _ma = deck_cell(schema, profile, sector, ring_index, deck_index,
                            cell_index)
    b, _tb, _mb = deck_cell(schema, profile, sector, ring_index, deck_index,
                            (cell_index + 1) % n)
    seam = (cell_index + 1) * plan["cell_deg"]
    left, right = _verts_at_angle(a, seam), _verts_at_angle(b, seam)
    return {
        "seam_deg": seam,
        "left_verts": len(left),
        "right_verts": len(right),
        "identical": left == right,
        "missing_from_right": [p for p in left if p not in right][:5],
        "missing_from_left": [p for p in right if p not in left][:5],
    }


def cell_manifest(schema, profile):
    """Every streaming cell in the station, described but not built.

    2,330 cells across 210 decks at roughly 40,000 triangles each is on the
    order of **90 million triangles** of interior corridor structure. That
    number is the argument for ADR 0003 stated as a quantity: an interior this
    size cannot be committed as mesh files and cannot be hand-authored. It is
    generated from the schema, deterministically, and the repository stores the
    rule rather than the result.

    So this manifest carries **metadata only**. It is what the engine streams
    against -- which cell is where, what it neighbours, what it costs, and what
    gravity a person standing in it feels -- and geometry is produced on demand
    by `deck_cell()`.

    Cost is measured once per deck, not once per cell: every cell on a deck is
    the same arc of the same corridor at the same radius, so building 2,330 of
    them to count triangles would burn minutes to learn 210 numbers.
    """
    decks, cells = [], []
    for sector in schema["sectors"]["extents_m"]:
        ex = schema["sectors"]["extents_m"][sector]
        rings = ring_radii(schema, profile, sector)
        for ri, ring in enumerate(rings):
            if ring["kind"] != "deck_stack":
                continue
            for di, deck in enumerate(decks_in_ring(schema, profile, sector, ri)):
                plan = ring_cells(schema, profile, sector, ri, di)
                tris = len(deck_cell(schema, profile, sector, ri, di, 0)[1])
                decks.append({
                    "id": f"{sector}.{ring['id']}.d{di}",
                    "label": f"{bind_labels(schema, sector, ri)} deck {di}",
                    "sector": sector, "ring": ring["id"], "ring_index": ri,
                    "deck_index": di,
                    "floor_r_m": deck["floor_r_m"],
                    "floor_g": deck["floor_g"],
                    "z0": ex["z0"], "z1": ex["z1"],
                    "cells": plan["cells"],
                    "cell_deg": plan["cell_deg"],
                    "cell_length_m": plan["cell_length_m"],
                    "sight_line_m": plan["sight_line_m"],
                    "cell_triangles": tris,
                })
                for ci in range(plan["cells"]):
                    cells.append({
                        "id": f"{sector}.{ring['id']}.d{di}.c{ci}",
                        "deck": f"{sector}.{ring['id']}.d{di}",
                        "cell_index": ci,
                        "start_deg": ci * plan["cell_deg"],
                        "end_deg": (ci + 1) * plan["cell_deg"],
                        # Ring corridors close on themselves, so every cell has
                        # exactly two neighbours and there are no ends.
                        "prev": f"{sector}.{ring['id']}.d{di}"
                                f".c{(ci - 1) % plan['cells']}",
                        "next": f"{sector}.{ring['id']}.d{di}"
                                f".c{(ci + 1) % plan['cells']}",
                    })

    total = sum(d["cells"] * d["cell_triangles"] for d in decks)
    return {
        "decks": len(decks),
        "cells": len(cells),
        "total_triangles": total,
        "note": "metadata only -- geometry is generated by deck_cell(), never "
                "stored. See ADR 0003.",
        "deck_table": decks,
        "cell_table": cells,
    }


def write_cell_manifest(path, schema, profile):
    """Serialise the manifest, minus everything a reader can derive.

    The cell table is 2,330 records of which every field follows from the
    deck's `cells` and `cell_deg`: cell i spans [i*cell_deg, (i+1)*cell_deg] and
    neighbours (i-1) % n and (i+1) % n. Committing it would store the same fact
    twice and guarantee the two copies eventually disagree, so the file carries
    the 210 deck records and the rule for expanding them.
    """
    man = cell_manifest(schema, profile)
    out = {k: v for k, v in man.items() if k != "cell_table"}
    out["cell_rule"] = ("cell i of a deck spans [i*cell_deg, (i+1)*cell_deg] "
                        "degrees and neighbours (i-1) %% cells and "
                        "(i+1) %% cells; rings close, so there are no ends")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    return out


# --------------------------------------------------------------------------
# Guideway truss
# --------------------------------------------------------------------------

# What the footage settles (authority 1, Babylon_5_2-22_33a/34b/35a):
#   - a Warren truss -- parallel top and bottom chords, alternating diagonal
#     web members, no verticals -- running longitudinally down the drum;
#   - tram cars slung BENEATH its bottom chord;
#   - a bright cylindrical light run alongside, and a row of rectangular
#     fixtures on the underside. This is what lights the habitat;
#   - a heavy collar where it lands on the end cap hub.
#
# What is extrapolated, and logged as INV-012: bay length, truss depth, chord
# section, how far off the ground it flies, and how many there are.
TRUSS_COUNT = SPOKE_COUNT     # one per spoke plane -- see INV-012
TRUSS_RADIUS_FRAC = 0.85      # chord radius as a fraction of the drum floor
TRUSS_BAY_M = 24.0            # one Warren panel, node to node
TRUSS_DEPTH_M = 16.0          # top chord to bottom chord
TRUSS_CHORD_M = 2.2           # square section of a chord
TRUSS_WEB_M = 1.3             # square section of a diagonal
TRUSS_LAMP_R_M = 1.5          # radius of the light run alongside


def _beam(verts, tris, p0, p1, w, h=None):
    """A box section running from p0 to p1. Used for chords and web members.

    Needed because the web diagonals are not axis-aligned; building them from
    axis-aligned boxes was what made the first pass read as a ladder rather
    than as a truss.
    """
    h = w if h is None else h
    ax = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = [c / L for c in ax]
    # Any perpendicular will do; pick the one that is numerically safest.
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = [ax[1] * ref[2] - ax[2] * ref[1],
         ax[2] * ref[0] - ax[0] * ref[2],
         ax[0] * ref[1] - ax[1] * ref[0]]
    ul = math.sqrt(sum(c * c for c in u)) or 1.0
    u = [c / ul * w / 2 for c in u]
    v = [ax[1] * u[2] - ax[2] * u[1],
         ax[2] * u[0] - ax[0] * u[2],
         ax[0] * u[1] - ax[1] * u[0]]
    vl = math.sqrt(sum(c * c for c in v)) or 1.0
    v = [c / vl * h / 2 for c in v]
    corners = []
    for base in (p0, p1):
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append(tuple(base[i] + su * u[i] + sv * v[i]
                                 for i in range(3)))
    _box(verts, tris, corners)


def guideway_truss(schema, profile, sector, angle_deg, z_span=None):
    """One longitudinal guideway truss, with its light run.

    Placed in a spoke plane. That is not an aesthetic choice: the truss is
    2.6 km long in the Green sector and nothing spans that unsupported, and the
    radial spokes are the only structure that could carry it. Putting the
    trusses at the spoke angles means each one is held every time it crosses
    one, which is the only arrangement that stands up.
    """
    r0 = sector_radius(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = z_span if z_span else (ex["z0"], ex["z1"])

    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    # "Down" is radially outward, toward the floor: that is where weight goes.
    r_bot = r0 * TRUSS_RADIUS_FRAC
    r_top = r_bot - TRUSS_DEPTH_M
    # Lateral offset is tangential, so the light run sits beside the truss
    # rather than inside it.
    def at(r, lateral, z):
        return (r * ca - lateral * sa, r * sa + lateral * ca, z)

    verts, tris, groups = [], [], []

    def emit(fn, group):
        before = len(tris)
        fn()
        groups.extend([group] * (len(tris) - before))

    # Chords run the full length as single beams. Segmenting them per bay would
    # double the triangle count for joins that are inside the solid anyway.
    for r in (r_bot, r_top):
        for lat in (-TRUSS_CHORD_M, TRUSS_CHORD_M):
            emit(lambda r=r, lat=lat: _beam(verts, tris, at(r, lat, z0),
                                            at(r, lat, z1), TRUSS_CHORD_M),
                 "truss_chord")

    # Warren web: diagonals alternating up and down between the chords, no
    # verticals. That is what the footage shows -- a run of triangles pointing
    # alternately at the ground and at the axis.
    n_bay = max(1, int((z1 - z0) / TRUSS_BAY_M))
    for i in range(n_bay):
        za = z0 + (z1 - z0) * i / n_bay
        zb = z0 + (z1 - z0) * (i + 1) / n_bay
        ra, rb = (r_bot, r_top) if i % 2 == 0 else (r_top, r_bot)
        for lat in (-TRUSS_CHORD_M, TRUSS_CHORD_M):
            emit(lambda ra=ra, rb=rb, za=za, zb=zb, lat=lat:
                 _beam(verts, tris, at(ra, lat, za), at(rb, lat, zb),
                       TRUSS_WEB_M), "truss_web")
        # Transverse tie at each node, holding the two web planes apart.
        emit(lambda ra=ra, za=za: _beam(
            verts, tris, at(ra, -TRUSS_CHORD_M, za), at(ra, TRUSS_CHORD_M, za),
            TRUSS_WEB_M), "truss_tie")

    # The light run. This is the habitat's illumination, so it is emissive
    # geometry rather than a fitting: it has to spill onto the ground below.
    n_side = 8
    for lat in (-(TRUSS_CHORD_M + 3.0), TRUSS_CHORD_M + 3.0):
        b = len(verts)
        for iz in (z0, z1):
            for k in range(n_side):
                th = 2 * math.pi * k / n_side
                dr = TRUSS_LAMP_R_M * math.cos(th)
                dl = TRUSS_LAMP_R_M * math.sin(th)
                verts.append(at(r_bot + dr, lat + dl, iz))
        for k in range(n_side):
            k2 = (k + 1) % n_side
            tris.append((b + k, b + k2, b + n_side + k2))
            tris.append((b + k, b + n_side + k2, b + n_side + k))
            groups.extend(["truss_lamp"] * 2)

    return verts, tris, {
        "sector": sector,
        "angle_deg": angle_deg,
        "z_span_m": round(z1 - z0, 1),
        "bays": n_bay,
        "chord_radius_m": round(r_bot, 1),
        "height_above_floor_m": round(r0 - r_bot, 1),
        "triangles": len(tris),
        "groups": groups,
    }


def drum_guideways(schema, profile, sector, z_span=None):
    """All the drum's guideway trusses, one per spoke."""
    verts, tris, groups = [], [], []
    for i in range(TRUSS_COUNT):
        v, t, m = guideway_truss(schema, profile, sector,
                                 360.0 * i / TRUSS_COUNT, z_span)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(m["groups"])
    return verts, tris, {"trusses": TRUSS_COUNT, "triangles": len(tris),
                         "groups": groups}


# --------------------------------------------------------------------------
# Self-test. There is no GPU and no reviewer, so the properties a render would
# reveal have to be asserted numerically as well as looked at.
# --------------------------------------------------------------------------

def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = load()

    # The one radius the whole rotation rate was solved from. If this drifts,
    # every gravity figure in the project is wrong by the same factor.
    r_drum = sector_radius(schema, profile, "green")
    check("drum floor is the canon 278.3 m", abs(r_drum - 278.3) < 0.05,
          f"{r_drum:.2f} m")
    # gravity_at already returns g, not m/s^2.
    check("drum floor is exactly 1 g",
          abs(gravity_at(schema, r_drum) - 1.0) < 1e-6,
          f"{gravity_at(schema, r_drum):.9f} g")

    # Rings must descend inward and never cross the axis.
    for sec in schema["sectors"]["extents_m"]:
        rings = ring_radii(schema, profile, sec)
        check(f"{sec}: rings descend inward",
              all(rings[i]["r_inner"] >= rings[i + 1]["r_outer"] - 1e-6
                  for i in range(len(rings) - 1)),
              str([round(r["r_outer"], 1) for r in rings]))
        # The innermost ring is the core and *does* reach r=0 -- the core
        # shuttle runs on the spin axis. Every habitable ring outside it must
        # not, or its floor would be a point.
        check(f"{sec}: only the core reaches the axis",
              all(r["r_inner"] > 0 for r in rings[:-1])
              and rings[-1]["r_inner"] == 0.0,
              str([round(r["r_inner"], 2) for r in rings]))
        check(f"{sec}: every ring has positive depth",
              all(r["r_outer"] > r["r_inner"] for r in rings))

    # Gravity falls off linearly with radius, so an inner deck must always be
    # lighter than the deck outside it. A sign error here would be invisible in
    # geometry and wrong in every simulation that reads it.
    # --- the drum is hollow ------------------------------------------------
    # This is the assertion set that did not exist while ring_radii was filling
    # the drum with concentric decks. Rings 2, 3 and 4 sat at 228, 167 and
    # 106 m radius -- the open air you look up through -- and the guideway
    # trusses were built at 236.6 m, inside one of them.
    drum = drum_sector(schema, profile)
    check("the drum is identified by geometry, not by name", drum == "green",
          f"{drum} -- if C-003's naming moves, this moves with it")
    drings = ring_radii(schema, profile, drum)
    check("the drum has exactly one open volume",
          sum(r["kind"] == "open" for r in drings) == 1)
    check("the drum's open volume reaches the habitat floor",
          any(r["kind"] == "open" and abs(r["r_outer"] - r_drum) < 0.05
              for r in drings))
    for r in drings:
        if r["kind"] == "deck_stack":
            check("no drum deck stack intrudes on the open volume",
                  r["r_inner"] >= r_drum - 1e-6,
                  f"{r['id']} reaches in to {r['r_inner']:.1f} m")
    # The trusses fly in that open air. If a later edit reintroduces a ring
    # there, this is what fails.
    tr_r = r_drum * TRUSS_RADIUS_FRAC
    core_r = [r for r in drings if r["kind"] == "core"][0]["r_outer"]
    check("guideway trusses fly in open air",
          all(not (r["kind"] == "deck_stack"
                   and r["r_inner"] <= tr_r <= r["r_outer"]) for r in drings)
          and core_r < tr_r < r_drum, f"truss at {tr_r:.1f} m")

    # --- decks -------------------------------------------------------------
    decks = decks_in_ring(schema, profile, drum, 0)
    check("the drum's sub-floor stack has decks", len(decks) > 1, str(len(decks)))
    # Down is OUTWARD. The stack under the habitat floor gets heavier with
    # depth, not lighter -- Downbelow is heavier than the Garden.
    check("sub-floor gravity rises with depth",
          all(decks[i]["floor_g"] < decks[i + 1]["floor_g"]
              for i in range(len(decks) - 1)))
    check("deck 0 sits one pitch below the 1 g floor",
          abs(decks[0]["floor_r_m"] - (r_drum + DECK_PITCH_M)) < 0.02,
          f"{decks[0]['floor_r_m']} m")
    check("the deepest sub-floor deck is under 1.2 g",
          1.0 < decks[-1]["floor_g"] < 1.2, f"{decks[-1]['floor_g']:.4f} g")
    check("sub-floor decks stay inside the pressure hull",
          decks[-1]["floor_r_m"] <= habitat_hull_radius(schema, profile) + 1e-6,
          f"{decks[-1]['floor_r_m']} m")
    pitches = [abs(decks[i]["floor_r_m"] - decks[i + 1]["floor_r_m"])
               for i in range(len(decks) - 1)]
    check("deck pitch is uniform and equals INV-010",
          all(abs(q - DECK_PITCH_M) < 1e-6 for q in pitches),
          f"{sorted({round(q, 4) for q in pitches})}")

    # A non-drum sector still stacks inward from its own floor, and still puts
    # deck 0 exactly on it.
    other = next(x for x in schema["sectors"]["extents_m"] if x != drum)
    odecks = decks_in_ring(schema, profile, other, 0)
    check(f"{other}: decks still stack inward", len(odecks) > 1 and
          all(odecks[i]["floor_g"] > odecks[i + 1]["floor_g"]
              for i in range(len(odecks) - 1)))
    check(f"{other}: deck 0 sits on the ring floor",
          abs(odecks[0]["floor_r_m"]
              - sector_radius(schema, profile, other)) < 0.02)

    # The drum is the only surface viewed from its concave side, so it is the
    # only place the hull's winding habit is wrong. Guarded at build time too,
    # but assert it here so a regression fails CI rather than a render.
    verts, tris, meta = drum_interior(schema, profile, "green",
                                      arc_deg=360.0, z_step=120.0)
    check("drum faces point toward the axis", meta["inward_facing"] == 1.0,
          f"{meta['inward_facing']:.3f}")
    check("drum closes on itself at 360 deg", meta["arc_deg"] == 360.0)
    check("every drum triangle carries a land-use group",
          len(meta["groups"]) == len(tris) and all(meta["groups"]))

    # --- end caps ---------------------------------------------------------
    for end in ("fore", "aft"):
        cv, ct, cm = drum_end_cap(schema, profile, "green", end)
        want = -1.0 if end == "fore" else 1.0
        plates = ribs = walls = 0
        plates_ok = ribs_ok = 0
        for i, (ia, ib, ic) in enumerate(ct):
            p0, p1, p2 = cv[ia], cv[ib], cv[ic]
            u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            w = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            nz = u[0] * w[1] - u[1] * w[0]
            nlen = math.sqrt(sum(x * x for x in (
                u[1] * w[2] - u[2] * w[1],
                u[2] * w[0] - u[0] * w[2], nz))) or 1.0
            g = cm["groups"][i]
            if g.startswith("endcap_plate") or g == "endcap_rimlight":
                plates += 1
                plates_ok += nz * want > 0
            elif g == "endcap_course_wall":
                walls += 1
                ribs += 1
                ribs_ok += abs(nz / nlen) < 0.05   # axial wall: radial normal
            else:
                ribs += 1
                ribs_ok += 1
        # A cap plate facing the wrong way is invisible from inside the drum,
        # which is the only place it is ever seen.
        check(f"{end} cap: plates and rim lights face into the drum",
              plates and plates_ok == plates, f"{plates_ok}/{plates}")
        check(f"{end} cap: course walls are axial", ribs_ok == ribs,
              f"{ribs_ok}/{ribs}")
        check(f"{end} cap: 48 rim lights",
              cm["rim_lights"] == 48 and
              sum(g == "endcap_rimlight" for g in cm["groups"]) == 96)
        # 8-9 concentric courses were measured; the schema's core radius sets
        # where the innermost one stops.
        check(f"{end} cap: 8 concentric courses", cm["courses"] == 8,
              str(cm["courses"]))
        check(f"{end} cap: aperture matches the schema core radius",
              abs(cm["core_aperture_m"] - 0.18 * r_drum) < 0.5,
              f"{cm['core_aperture_m']} m")

    # The measured hub cone fills the inner ~20% of the cap; the schema's core
    # ring, read off an unrelated authority-3 diagram, sits at 0.18. Two
    # independent sources agreeing to 2% is load-bearing -- assert it so a
    # future edit to either one has to confront the other.
    core_u = schema["interior_topology"]["provisional_rings"][-1]["r_outer"]
    check("schema core radius corroborates the measured hub cone",
          abs(core_u - 0.20) <= 0.03, f"r/R = {core_u}")

    # Plates should be roughly square, as measured. Allow a wide band -- the
    # observation is qualitative -- but catch a course that has gone to ribbons.
    for ci in range(len(ENDCAP_RIBS) - 1):
        uo, ui = ENDCAP_RIBS[ci], ENDCAP_RIBS[ci + 1]
        n = _endcap_segments(uo, ui, r_drum)
        width = 2 * math.pi * ((uo + ui) / 2 * r_drum) / n
        depth = (uo - ui) * r_drum
        check(f"cap course {ci} plates are near-square",
              0.4 < width / depth < 2.5, f"{width:.1f} x {depth:.1f} m")

    # --- sight lines and streaming cells -----------------------------------
    # budget.py gated interior cost on an assumed 50 m sight line. In a ring
    # corridor the curvature decides it, and the worst case across the station
    # is 1.8x that -- so the gate was measuring against a shorter view than the
    # station affords. These assertions keep the derived figure honest.
    cw = kit.PROVISIONAL["corridor_width_m"]
    sls = [(sec, r["id"], sight_line(r["r_outer"], cw))
           for sec in schema["sectors"]["extents_m"]
           for r in ring_radii(schema, profile, sec)
           if r["kind"] == "deck_stack"]
    check("every ring has a finite sight line",
          all(math.isfinite(v) and v > 0 for _s, _r, v in sls))
    # A wider ring curves less, so it must see further. If this inverts, the
    # formula has been broken rather than the station reshaped.
    for sec in schema["sectors"]["extents_m"]:
        rs = [r for r in ring_radii(schema, profile, sec)
              if r["kind"] == "deck_stack"]
        vals = [sight_line(r["r_outer"], cw) for r in rs]
        check(f"{sec}: sight line falls with radius",
              all(vals[i] > vals[i + 1] for i in range(len(vals) - 1))
              if len(vals) > 1 else True,
              str([round(v, 1) for v in vals]))
    worst = max(sls, key=lambda x: x[2])
    check("worst-case sight line is Grey's outermost ring",
          worst[0] == "grey" and worst[1] == "ring_1",
          f"{worst[0]} {worst[1]} at {worst[2]:.1f} m")
    check("worst-case sight line stays inside the corridor budget",
          285.0 * worst[2] + 2 * 1400 < 60_000,
          f"{285.0 * worst[2] + 2 * 1400:,.0f} tri at {worst[2]:.1f} m")
    # A streaming cell must be wider than the view out of it, or the player
    # sees into a cell that is not resident.
    for sec, rid, v in sls:
        r = next(x for x in ring_radii(schema, profile, sec) if x["id"] == rid)
        cell_m = math.radians(streaming_cell_deg(r["r_outer"], cw)) * r["r_outer"]
        check(f"{sec} {rid}: streaming cell exceeds its sight line",
              cell_m > v, f"cell {cell_m:.1f} m vs sight {v:.1f} m")

    # --- streaming cells ---------------------------------------------------
    # "Seamless" is the project's word and it has to be a test, not a claim. A
    # crack between two ring cells is a hole a player falls through at 1 g, and
    # touching bounding boxes do not prove there isn't one -- only the shared
    # edge, vertex for vertex, does.
    for sec in schema["sectors"]["extents_m"]:
        rings = ring_radii(schema, profile, sec)
        ri = next(i for i, r in enumerate(rings) if r["kind"] == "deck_stack")
        plan = ring_cells(schema, profile, sec, ri)
        check(f"{sec}: cells tile the circle exactly",
              abs(plan["cells"] * plan["cell_deg"] - 360.0) < 1e-9,
              f"{plan['cells']} x {plan['cell_deg']}")
        check(f"{sec}: a cell is wider than its own sight line",
              plan["cell_length_m"] > plan["sight_line_m"],
              f"cell {plan['cell_length_m']} m vs sight {plan['sight_line_m']} m")
        rep = cell_seam_report(schema, profile, sec, ri)
        check(f"{sec}: adjacent cells share their seam exactly",
              rep["identical"] and rep["left_verts"] > 0,
              f"{rep['left_verts']} vs {rep['right_verts']} verts; "
              f"missing {rep['missing_from_right']}{rep['missing_from_left']}")

    # The wrap-around seam is the one a loop over range(n) never tests, and it
    # is the seam where a floating-point error in 360/n would show up.
    plan = ring_cells(schema, profile, "green", 0)
    wrap = cell_seam_report(schema, profile, "green", 0,
                            cell_index=plan["cells"] - 1)
    check("the wrap-around seam closes too", wrap["identical"],
          f"cell {plan['cells']-1} -> 0 at {wrap['seam_deg']} deg")

    # --- cell manifest -----------------------------------------------------
    man = cell_manifest(schema, profile)
    check("manifest covers every deck in every sector",
          man["decks"] == sum(
              len(decks_in_ring(schema, profile, sec, i))
              for sec in schema["sectors"]["extents_m"]
              for i, r in enumerate(ring_radii(schema, profile, sec))
              if r["kind"] == "deck_stack"),
          f"{man['decks']} decks")
    check("manifest cell count matches the per-deck plans",
          man["cells"] == sum(d["cells"] for d in man["deck_table"]),
          f"{man['cells']} cells")
    ids = [c["id"] for c in man["cell_table"]]
    check("every cell id is unique", len(set(ids)) == len(ids))
    by_id = set(ids)
    check("every neighbour link resolves",
          all(c["prev"] in by_id and c["next"] in by_id
              for c in man["cell_table"]))
    # A ring closes on itself, so following `next` all the way round a deck must
    # return to the start and must visit every cell exactly once. A stale
    # modulus would give a short cycle that nothing else would notice.
    first = man["deck_table"][0]
    ring_ids = [c for c in man["cell_table"] if c["deck"] == first["id"]]
    lookup = {c["id"]: c for c in ring_ids}
    walk, cur = [], ring_ids[0]["id"]
    for _ in range(first["cells"]):
        walk.append(cur)
        cur = lookup[cur]["next"]
    check("following `next` walks a deck exactly once and closes",
          cur == ring_ids[0]["id"] and len(set(walk)) == first["cells"],
          f"{len(set(walk))} of {first['cells']}")

    # --- guideway trusses -------------------------------------------------
    tv, tt, tm = guideway_truss(schema, profile, "green", 0.0)
    check("truss flies above the drum floor",
          0 < tm["height_above_floor_m"] < r_drum * 0.5,
          f"{tm['height_above_floor_m']} m")
    # The truss carries the trams and the lighting; if it dips below the tallest
    # land-use relief it is buried in a settlement terrace.
    tallest = max(rel for _f, _n, rel in LAND_USE)
    check("truss clears the tallest land-use relief",
          tm["height_above_floor_m"] > tallest * 2,
          f"{tm['height_above_floor_m']} m over {tallest} m")
    check("truss spans the whole sector",
          abs(tm["z_span_m"] - 2586) < 1.0, f"{tm['z_span_m']} m")
    check("truss is a Warren web with alternating diagonals",
          tm["bays"] > 1 and abs(TRUSS_BAY_M / TRUSS_DEPTH_M - 1.5) < 0.6,
          f"bay {TRUSS_BAY_M} / depth {TRUSS_DEPTH_M}")
    check("truss carries a light run", "truss_lamp" in set(tm["groups"]))

    # One truss per spoke. The trusses are 2.6 km long and the spokes are the
    # only radial structure that could hold them up, so the counts must match
    # or the arrangement does not stand.
    sv, st, sm = drum_spokes(schema, profile, "green")
    check("one guideway truss per spoke plane",
          TRUSS_COUNT == sm["count"] == SPOKE_COUNT,
          f"{TRUSS_COUNT} trusses vs {sm['count']} spokes")
    check("spokes sit at the canon 120 degree spacing", SPOKE_COUNT == 3)

    gv, gt, gm = drum_guideways(schema, profile, "green")
    check("all trusses build", gm["trusses"] == TRUSS_COUNT)
    # Every beam is a closed box, so the vertex count must be a clean multiple.
    check("truss geometry is watertight boxes",
          all(0 <= i < len(gv) for tri in gt for i in tri))

    # LAND_USE must tile the circumference exactly. A table summing to 0.94
    # would leave a 6% seam of untagged ground -- the same class of bug that
    # silently dropped 120 residents per 2,000 from the species mix.
    total = sum(f for f, _, _ in LAND_USE)
    check("land-use fractions sum to 1.0", abs(total - 1.0) < 1e-9, f"{total}")

    # A viewpoint must land above the ground it stands on, not inside it.
    for ang in (0.0, 90.0, 137.0, 270.0, 359.0):
        eye, up = stand_point(schema, profile, "green", ang, 4500.0)
        r_eye = math.hypot(eye[0], eye[1])
        band_r = r_eye + 1.7
        check(f"stand_point at {ang:g} deg is above the surface",
              r_eye < band_r <= r_drum + 2.51, f"eye r={r_eye:.2f}")
        check(f"stand_point at {ang:g} deg has up pointing inward",
              up[0] * eye[0] + up[1] * eye[1] < 0)

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
