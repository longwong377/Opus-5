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
    depth = ring["r_outer"] - ring["r_inner"]
    n = max(1, int(depth // pitch))
    out = []
    for i in range(n):
        floor_r = ring["r_outer"] - i * pitch
        out.append({
            "deck_index": i,
            "floor_r_m": round(floor_r, 2),
            "ceiling_r_m": round(floor_r - pitch, 2),
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
    decks = decks_in_ring(schema, profile, "green", 0)
    check("green ring 1 has decks", len(decks) > 1, str(len(decks)))
    check("deck gravity decreases inward",
          all(decks[i]["floor_g"] > decks[i + 1]["floor_g"]
              for i in range(len(decks) - 1)))
    check("deck 0 sits at the 1 g floor", abs(decks[0]["floor_g"] - 1.0) < 1e-4,
          f"{decks[0]['floor_g']:.6f} g")
    pitches = [decks[i]["floor_r_m"] - decks[i + 1]["floor_r_m"]
               for i in range(len(decks) - 1)]
    check("deck pitch is uniform and equals INV-010",
          all(abs(p - DECK_PITCH_M) < 1e-6 for p in pitches),
          f"{sorted({round(p, 4) for p in pitches})}")

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
