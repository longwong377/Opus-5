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
import bisect
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
    """The ENVELOPE radius at one z -- the outline, protrusions included.

    TWO CONVENTIONS LIVE IN THIS MODULE AND THEY DISAGREE BY UP TO 95.6 m.
    This returns the sample at or BELOW z (piecewise constant, left-continuous);
    `core_hull_radius_at` returns the NEAREST sample. At a step in the profile
    -- and the profile has steps of that size, at 4.07 m pitch over 1,978
    samples -- which side of a control point a query lands on is worth as much
    as a whole sector's taper.

    Neither convention is wrong on its own and this is NOT a licence to compare
    them pointwise: doing that made the opened core profile look as though it
    exceeded the envelope at z 7060, which is impossible (an opening is
    anti-extensive, and asserted so: 0 of 1,978 samples violate it). Any code
    that needs a hull radius over a RANGE should take the extremum over the
    profile's own samples in that range -- see `narrowest_z` -- rather than
    probing on a grid of its own.
    """
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


# Pressure hull, frames and services between the core hull surface and the
# innermost usable radius. Metric rather than fractional -- INV-013, INV-026.
#
# This replaced a `HULL_ALLOWANCE = 0.86` fraction, which was the wrong KIND of
# quantity twice over. A fraction of the radius removed 65 m of notional
# structure in Grey and 22 m in Yellow; pressure hull and frames do not scale
# with how far a sector sits from the spin axis. And it multiplied the *mean
# envelope radius over the whole sector band*, which describes no actual
# surface: Yellow's band ranges 18-440 m and Blue's 116-268 m, so their means
# are arithmetic about a shape rather than a measurement of one.
HULL_SKIN_M = 6.0

# Half-window for the morphological opening that recovers the core hull from
# the envelope. Sized to strip anything narrower than ~120 m in z, which is
# every component the exterior places and no section of hull.
CORE_HULL_WINDOW_M = 60.0

_CORE_HULL_CACHE = {}


def core_hull_profile(profile, window_m=CORE_HULL_WINDOW_M):
    """The pressure hull under the envelope, with protrusions stripped.

    `radius_profile.json` traces the station's OUTLINE, so it reports the top of
    whatever is standing proud at each z -- a cobra bay, a cargo module, a
    radiator root. Session 2b established the technique for separating the two:
    a protrusion is local in z and the hull varies slowly, so a wide running
    minimum approximates the core hull.

    A running minimum alone is wrong at a step, and measurably so. It ERODES:
    for one window either side of a real change in section it reports the
    narrower value, so Grey came out at 428.7 m -- below its own raw minimum of
    436.4 m, a radius no point in Grey actually has. The fix is a morphological
    opening, erosion followed by dilation at the same window, which removes
    features narrower than the window and restores the edges of those wider
    than it. Asserted: the opened profile never falls below the raw minimum.
    """
    key = (id(profile), window_m)
    if key in _CORE_HULL_CACHE:
        return _CORE_HULL_CACHE[key]
    rs = [q["radius_m"] for q in profile]
    zs = [q["z_m"] for q in profile]
    step = (zs[-1] - zs[0]) / max(1, len(zs) - 1)
    half = max(1, int(round(window_m / step)))

    def sweep(v, fn):
        n = len(v)
        return [fn(v[max(0, i - half):min(n, i + half + 1)]) for i in range(n)]

    out = sweep(sweep(rs, min), max)
    _CORE_HULL_CACHE[key] = out
    return out


def sector_shell_radius(schema, profile, sector, tol=0.05):
    """The radius of a sector's principal pressurised shell.

    A sector is a longitudinal band, and its hull radius is not constant across
    it -- Blue's runs 116 to 268 m. One number has to stand for the whole band
    because rings are expressed as fractions of it, so the question is which
    number, and a mean is the one answer that is guaranteed to describe no
    surface present in the sector.

    What is taken instead is the LONGEST RUN of near-constant core-hull radius
    inside the band: the sector's widest real cylinder, the piece of it that is
    actually shell rather than taper. That is a surface you could put a tape
    measure on.

    Cross-check, and it is a strong one: run against the band that contains the
    habitat cylinder this returns 314.3 m, where `habitat_hull_radius()` -- a
    completely separate derivation, a plain mean over one named schema feature
    -- gives 316.8 m before its own skin. 2.5 m apart on a 315 m radius, 0.8%,
    from two methods that share no arithmetic. The self-test asserts it.
    """
    core = core_hull_profile(profile)
    ex = schema["sectors"]["extents_m"][sector]
    idx = [i for i, q in enumerate(profile) if ex["z0"] <= q["z_m"] <= ex["z1"]]
    if not idx:
        raise ValueError(f"sector {sector!r} covers no profile samples")
    c = [core[i] for i in idx]

    best_n, best_r, i = -1, None, 0
    while i < len(c):
        j, lo, hi = i, c[i], c[i]
        while j + 1 < len(c):
            nlo, nhi = min(lo, c[j + 1]), max(hi, c[j + 1])
            if nhi - nlo > tol * nlo:
                break
            lo, hi, j = nlo, nhi, j + 1
        if j - i > best_n:
            best_n, best_r = j - i, (lo + hi) / 2.0
        i = j + 1
    return best_r


def sector_radius(schema, profile, sector):
    """Radius of the OUTERMOST DECK FLOOR in a sector -- not the hull envelope.

    The first pass used the mean envelope radius and put ring 1 at 328 m and
    **1.18 g**, which is wrong twice over: the envelope includes protrusions
    that are outside the pressure hull entirely, and canon fixes the habitat
    floor at 278.3 m *because* that is where spin gravity is exactly 1.0 g.

    The drum sector is therefore anchored to the canon figure directly, and
    every other sector sits `HULL_SKIN_M` inside its own principal shell.
    Deriving the drum the same way would let a rounding error move the one
    radius the whole rotation rate was solved from.

    Note what this function does NOT promise: that the deck at this radius is
    somewhere a person can be. Grey's is at 1.693 g. See `habitable_radius()`.
    """
    if sector == drum_sector(schema, profile):
        return schema["bio_habitat"]["interior_radius_m"]["value"]
    return sector_shell_radius(schema, profile, sector) - HULL_SKIN_M


def drum_sector(schema, profile):
    """Which longitudinal band is the habitat drum, decided by geometry.

    Which one it is *called* is C-003's open question, so this cannot be keyed
    on a name. The drum is the band whose principal shell matches the measured
    habitat pressure hull, and that answer does not move when the naming does.

    Matched against `habitat_hull_radius()` rather than against the 278.3 m
    floor, because the shell and the pressure hull are the same surface and the
    floor is 32 m inside it. Comparing a hull radius to a floor radius is a
    category error, and here it does not merely blur the answer -- it gives the
    wrong one. Against the floor the best match is **red**, at 4.3 m, with the
    drum 36 m away in second place; red's shell happens to sit 274 m out, four
    metres from where the Garden's ground is. Against the pressure hull the
    drum wins at 2.5 m with red 42.7 m behind it, a 17x margin.

    The old fraction-based version got the right answer for the wrong reason:
    it multiplied a mean envelope radius, and the drum band's mean was inflated
    by the aft hull block it happens to contain. Neither the comparison nor the
    margin was sound; the result was luck.
    """
    target = habitat_hull_radius(schema, profile) + HULL_SKIN_M
    best, best_err = None, None
    for name in schema["sectors"]["extents_m"]:
        try:
            err = abs(sector_shell_radius(schema, profile, name) - target)
        except ValueError:
            continue
        if best_err is None or err < best_err:
            best, best_err = name, err
    return best


# The heaviest deck a person may be ASSIGNED to -- quarters, a roster, a shop.
# Above this a deck is still built, still pressurised and still reachable; what
# it is not is somewhere the station bills as accommodation. INV-027.
#
# "Plant" therefore does not mean empty, and reading it that way would delete
# the most characterful population on the station. `LOCATIONS.md` puts
# Downbelow "near the outer hull, around the waste recycling system, the air
# compressors and the water reclamation facility" -- outermost rings, highest
# gravity in the sector, "corridors and chambers, not rooms" -- and fills it
# with Lurkers, people who ran out of money and cannot buy passage home.
#
# Those are the same decks. The geometry says the outer stack is too heavy to
# billet anyone on; canon says the people with no billet live in the outer
# stack among the machinery. Two independent derivations landing on one volume,
# and the second explains why the worst address on the station is the worst
# address on the station. `use == "plant"` means UNASSIGNED, not uninhabited.
HABITABLE_G_MAX = 1.25


def habitable_radius(schema, g_max=HABITABLE_G_MAX):
    """The outermost radius at which people live and work.

    Making the hull allowance metric did not fix Grey's heavy outermost deck --
    it made it worse, 1.445 g to 1.693 g, because the 0.86 fraction had been
    quietly deleting 65 m of hull that is really there. Grey sits on the aft
    hull block, the widest structure on the station at 478 m envelope radius,
    and no honest allowance moves it inboard.

    So the premise was wrong rather than the arithmetic. `STATE.md` had this
    recorded as a symptom of `HULL_ALLOWANCE`; it is not. A rigid body spinning
    at a rate fixed by the habitat floor puts 1.7 g on anything 471 m out, and
    the design response is the one any real station would make: you do not put
    quarters at the bottom of the gravity well, you put MASS there. Tankage,
    reservoirs, waste processing, reactor auxiliaries, ballast.

    Grey's outer 123 m becomes the station's basement, which is a place the
    scope asks for by name -- "the physical plant that makes 250,000 people
    possible: food, water, air, power, waste" -- and which the fraction was
    concealing behind a plausible number.
    """
    rot = schema["station"]["rotation"]
    w = rot["omega_rad_s"]["value"]
    return g_max * rot["standard_gravity_m_s2"]["value"] / (w * w)


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


def core_hull_radius_at(profile, z_m):
    """The PRESSURE hull's radius at one z, protrusions stripped.

    Distinct from `hull_radius_at` above, which returns the envelope -- the
    outline, including whatever cobra bay or radiator root is standing proud
    there. A place has to fit inside the PRESSURE hull, so this uses
    `core_hull_profile`, the same opened profile `sector_shell_radius` derives
    its one-number-per-sector from.

    THE CONSTRAINT NOTHING WAS APPLYING. `sector_shell_radius` deliberately
    collapses a sector to one radius -- its docstring says so, and says why:
    "rings are expressed as fractions of it". The same paragraph says "a sector
    is a longitudinal band, and its hull radius is not constant across it --
    Blue's runs 116 to 268 m". Both true, and the consequence was never
    checked: a place at a z where the hull is 116 m, addressed to a ring
    computed from the 268 m cylinder, is IN VACUUM.

    `tools/cutaway.py` found it by drawing the two together: 14 of 118
    locations outside the hull, `mainstage_node` by 133.5 m and `cnc` by 94.7 m.
    Every gate in this project measures a room against its own footprint, so
    nothing had ever compared an ADDRESS to the hull that must contain it.
    """
    core = core_hull_profile(profile)
    best_i, best_d = 0, float("inf")
    for i, q in enumerate(profile):
        d = abs(q["z_m"] - z_m)
        if d < best_d:
            best_i, best_d = i, d
    return core[best_i]


def rings_fitting_at(schema, profile, sector, z_m, skin_m=None):
    """`ring_radii` filtered to the rings that actually exist at this z.

    A ring whose inner radius is already outside the hull at `z_m` is not a
    ring there and is dropped; a ring the hull cuts through is returned with
    its outer radius clamped and `clamped: True`. Outermost first, exactly as
    `ring_radii` orders them, so an address naming ring 0 resolves to the
    outermost ring that is really present.
    """
    skin = HULL_SKIN_M if skin_m is None else skin_m
    lim = max(0.0, core_hull_radius_at(profile, z_m) - skin)
    out = []
    for r in _ring_radii_uncut(schema, profile, sector):
        if r["r_inner"] >= lim:
            continue
        q = dict(r)
        if q["r_outer"] > lim:
            q["r_outer"] = lim
            q["r_mid"] = (q["r_inner"] + lim) / 2.0
            q["clamped"] = True
        out.append(q)
    return out


def ring_radii(schema, profile, sector, z_m=None):
    """Ring bounds for a sector. With `z_m`, the rings that exist AT that z.

    `z_m` IS WHAT MAKES AN ADDRESS MEAN SOMETHING. Without it this returns the
    rings of the sector's widest cylinder, and a sector is not a cylinder --
    `sector_shell_radius`'s own docstring says Blue's hull runs 116 to 268 m.
    So "ring 0" meant "the outermost ring of the widest part of the sector",
    which at the fore taper is 95 m outside the ship. With `z_m` it means "the
    outermost ring present here", which is what an address on a station
    naturally means and what every reader has assumed it meant.

    See `rings_fitting_at`. 14 of the 118 located places were outside the hull
    on the first reading and none of them is now.
    """
    if z_m is not None:
        return rings_fitting_at(schema, profile, sector, z_m)
    return _ring_radii_uncut(schema, profile, sector)


def _ring_radii_uncut(schema, profile, sector):
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


RING_FRAME_PITCH_M = 56.0     # INV-073: drum ring frames
RING_FRAME_RISE_M = 1.1
RING_FRAME_W_M = 0.9
DECK_PITCH_M = 3.6        # floor-to-floor, provisional -- INV-010


def decks_in_ring(schema, profile, sector, ring_index, pitch=DECK_PITCH_M,
                  z_m=None):
    """The decks stacked inside one ring zone, outermost first.

    A ring is 38-61 m deep (see CONFLICTS.md), which is a zone, not a deck. At a
    3.6 m floor-to-floor pitch that is a dozen or more decks per ring, and it is
    the deck -- not the ring -- that a person stands on and that a level number
    indexes.

    Gravity is quoted per deck because it genuinely differs across a ring: the
    outermost and innermost decks of ring 1 differ by 18% of a g, which is more
    than enough to feel walking down a stair.
    """
    # `z_m` NARROWS THE RING TO WHAT THE HULL LEAVES THERE. Without it a deck
    # stack is built inside the sector's widest cylinder and handed to a
    # place at the taper, which is how `qtr_command`, `war_room`,
    # `admin_complex` and `cobra_bays` ended up outside the hull while
    # naming a ring that genuinely exists at their z -- the RING was there
    # and the DECK inside it was not.
    rings = ring_radii(schema, profile, sector, z_m=z_m)
    if not rings:
        return []
    ring = rings[min(ring_index, len(rings) - 1)]
    if ring["kind"] != "deck_stack":
        return []          # open air and the core carry no decks
    depth = ring["r_outer"] - ring["r_inner"]
    n = max(1, int(depth // pitch))
    r_hab = habitable_radius(schema)
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
            # Built and pressurised either way. What changes is what is IN it,
            # and therefore what it costs to dress: a plant deck is tankage and
            # machinery walked through on a catwalk, not corridor, quarters and
            # signage. Tagged here so the manifest and the budget can tell them
            # apart rather than pricing 34 decks of Grey as habitat.
            #
            # "plant" is UNASSIGNED, not uninhabited -- it is where Downbelow
            # is. The NPC layer reads this to decide who may be placed: no
            # resident is billeted here, and lurkers are placed nowhere else.
            "use": "habitat" if floor_r <= r_hab else "plant",
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


def arc_sections(schema, profile, sector, ring_index, degrees=30.0,
                 radius_m=None):
    """How a ring arc divides into kit sections: (radius, count, section length).

    Pulled out so a caller can ask WHERE THE DOORS WILL GO without building
    458,000 triangles of corridor to find out. `deck.py` has to know that before
    it builds anything, because a door that lands outside the room it serves
    must not be cut in the corridor either -- and discovering that from the
    finished mesh means throwing the mesh away.
    """
    rings = ring_radii(schema, profile, sector)
    r = rings[ring_index]["r_mid"] if radius_m is None else radius_m
    total = arc_length(r, degrees)
    n = max(1, int(round(degrees / 2.5)))
    return r, n, total / n


def place_doors(r, n, seg_len, degrees, start_deg, z_mid, doors):
    """Where each asked-for door lands: (per-section lists, placements).

    Under `ring_arc`'s remap a vertex at kit z sits at world angle
    `start + delta*i + z/r`, with delta = seg_len/r the angular width of one
    section -- so the arithmetic inverts exactly and a door's angle converts to
    a section and an offset with nothing approximated.
    """
    start_rad = math.radians(start_deg)
    delta = seg_len / r
    per_section, placed = {}, []
    for ang_deg, side in doors:
        # Wrap into the arc: an arc may start at -12 degrees and hold a door at
        # 332, which is the same place approached the other way round.
        phi = (math.radians(ang_deg) - start_rad) % (2.0 * math.pi)
        if phi > math.radians(degrees) + 1e-9:
            continue                            # not on this arc at all
        i = min(n - 1, max(0, int(phi / delta)))
        dz = (phi - delta * i) * r
        per_section.setdefault(i, []).append((dz, side))
        _ib, c = kit.wall_door_snap(seg_len, dz, None)
        placed.append({
            "angle_deg": math.degrees(start_rad + delta * i + c / r),
            "side": side,
            # WHERE THE DOOR ACTUALLY IS, which is not the wall face.
            # `corridor_section` sets its assembly back by `fd/2 - 0.06` so the
            # frame's front face stands a little proud of the wall rather than
            # half of it hanging in the corridor. Reporting the wall face
            # instead put the separately-placed moving leaves 0.16 m out of
            # their own frame -- close enough to look right in a wide shot and
            # wrong at the distance a player opens a door from.
            "z_m": z_mid + side * (
                kit.PROVISIONAL["corridor_width_m"] / 2.0
                + kit.PROVISIONAL["door_frame_depth_m"] * 0.5 - 0.06),
        })
    return per_section, placed


def ring_arc(schema, profile, sector, ring_index, degrees=30.0,
             start_deg=0.0, z_offset=None, radius_m=None, doors=(),
             door_leaves=True):
    """One arc of one ring deck: a corridor run bent around the station axis.

    The corridor kit is authored straight, along +Z. Here it is bent: each
    section is placed at its own angle about the axis and rotated to face along
    the arc. A ring corridor is not a straight corridor that happens to be
    curved -- at 278 m radius a 30 degree arc is 146 m long and closes 30
    degrees of heading, which is visible from inside and is a large part of why
    the drum reads as a drum.

    `doors` is a sequence of (angle_deg, side) -- where a room opens off this
    corridor, in the corridor's own coordinate, which is an angle. Side -1 and
    +1 are the two hands of the corridor; because the kit's +x becomes world +z
    under the remap below, **a room at lower world z is side -1**.

    UNTIL SESSION 3v THIS ARGUMENT DID NOT EXIST and `corridor_section` had
    supported doors since it was written. The corridor was a closed tube for
    every one of the sessions that built rooms to open off it -- a player could
    walk 126 m of station and could not get into any of it, and no gate could
    fail for it because every gate measured one mesh at a time.

    The returned meta carries `doors_at`: where each door ACTUALLY landed, which
    is not where it was asked for. A wall door snaps to the nearest bay centre,
    since a door straddling two bays would need its closure cut round a portal
    frame. Anything placing geometry on the far side of that door -- a
    vestibule, a room's matching aperture -- has to build against the snapped
    angle, so it is reported rather than left to be recomputed.
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

    per_section, placed = place_doors(r, n, seg_len, degrees, start_deg,
                                      z_mid, doors)

    verts, tris = [], []
    kit.reset_tags()
    for i in range(n):
        a = math.radians(start_deg + degrees * (i + 0.5) / n)
        here = per_section.get(i, ())
        # ONLY THE FIRST SECTION BRINGS ITS OWN START PORTAL. `corridor_section`
        # closes both ends of the length it is given, so a run of them repeated
        # the joint: a portal frame, its head light, two pilasters and fourteen
        # light-strip bars, built TWICE at every section boundary. Measured on a
        # 12.5 degree arc before this line existed: **1,120 exact duplicate
        # triangles and 1,760 non-manifold edges**, and 720 of the duplicates
        # are emissive -- roughly 165 coincident duplicate LIGHT SOURCES per
        # 30 degrees of corridor, on every ring deck of the station.
        #
        # `start_portal` has been a parameter of `corridor_section` since it was
        # written and no caller ever passed it. Nothing could fail for it:
        # coincident duplicate geometry is closed, correctly wound, inside its
        # own footprint and invisible to every gate this project has -- it reads
        # as a depth-sort coin toss and a doubled light, not as a hole.
        v, t = kit.corridor_section(seg_len, doors=here,
                                    door_leaves=door_leaves,
                                    start_portal=(i == 0))
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
        "z_m": z_mid,
        "doors_at": placed,
        "doors_asked": len(doors),
        # THE MATERIAL SPANS, which this function recorded and then threw away.
        # `interior_kit` tags every surface it builds -- skirting, rail band,
        # deck grid, and the three `light_*` fittings a corridor is lit BY --
        # and `ring_arc` returned none of them, so an assembler had nothing to
        # name the geometry with. `deck.py` then labelled all 458,400 triangles
        # `corridor`: materials.py's substring rules match that zero times and
        # `FIXTURE_LIGHTING` is an exact-name table, so 77% of a deck shipped
        # with the glTF fallback material and the corridor emitted NO LIGHT
        # SOURCES AT ALL while 850 fittings sat in the mesh untagged.
        "groups": kit.tagged_spans(tris),
    }


# How long a section of axial corridor is. THE SAME 9.205 m the collision shell
# and the occluder profile are both measured at, so the three agree by
# construction rather than by three people picking a similar number.
AXIAL_SECTION_M = 9.205


def axial_run(schema, profile, sector, ring_index, z0, z1, angle_deg=0.0,
              radius_m=None, doors=(), door_leaves=True):
    """A corridor along the STATION AXIS, joining two z-clusters of one deck.

    WHY THIS DID NOT EXIST UNTIL NOW, AND WHAT ITS ABSENCE MEANT. Every corridor
    in this station is a `ring_arc`: a run at CONSTANT z, bent around the axis.
    A deck's locations, though, are spread along the axis -- `blue/0/0` carries
    six z-clusters over 1,120 m, the docking bays at 7120 and the customs halls
    at 7440 -- and `deck.build_deck_clusters` says so in as many words:

        This does not join them with geometry and does not pretend to: there is
        no floor between 7120 and 7440 and inventing one would be worse than the
        gap.

    That was right when it was written, because what it declined to invent was a
    floor with nothing on either side of it. It stopped being right once both
    clusters were in one scene: the two ends now exist, the 320 m between them
    is the only thing missing, and a station whose locations cannot be walked
    between is 90 rooms rather than a place.

    IT IS THE KIT UNBENT, which is why it is thirty lines. `interior_kit`
    authors a corridor STRAIGHT along +Z and `ring_arc` bends it; here it is
    placed as authored, with its +Y (up) turned radially inward and its +X
    (across) turned tangential. Same sections, same doors, same tags, same
    lighting -- so an axial corridor cannot drift from a ring one, and neither
    can its collision shell (`collision.axial_shell`) or its occluder.

    `doors` is a sequence of (z, side) in WORLD z, matching the kit's own door
    convention rather than `ring_arc`'s angles, because along a straight run a
    door's position is a length and not an angle.
    """
    rings = ring_radii(schema, profile, sector)
    ring = rings[ring_index]
    r = ring["r_mid"] if radius_m is None else radius_m
    a0 = math.radians(angle_deg)

    lo, hi = (z0, z1) if z1 >= z0 else (z1, z0)
    length = hi - lo
    n = max(1, int(round(length / AXIAL_SECTION_M)))
    seg = length / n

    verts, tris = [], []
    kit.reset_tags()
    placed = []
    for i in range(n):
        base = lo + i * seg
        here = tuple((d[0] - base, d[1]) for d in doors
                     if base <= d[0] < base + seg)
        for dz, side in here:
            placed.append({"z_m": base + dz, "side": side})
        # SAME RULE AS `ring_arc`, and this function shipped without it this
        # very session -- an axial run is the same kit repeated along a line and
        # it doubled the same joint.
        v, t = kit.corridor_section(seg, doors=here, door_leaves=door_leaves,
                                    start_portal=(i == 0))

        def remap(x, y, z, base=base):
            rad = r - y
            a = a0 + x / r
            return (rad * math.cos(a), rad * math.sin(a), base + z)

        kit._merge(verts, tris, v, t, remap)

    return verts, tris, {
        "sector": sector,
        "ring": ring["id"],
        "ring_index": ring_index,
        "radius_m": round(r, 1),
        "gravity_g": round(gravity_at(schema, r), 3),
        "angle_deg": angle_deg,
        "z0_m": lo,
        "z1_m": hi,
        "length_m": round(length, 1),
        "sections": n,
        "section_m": round(seg, 4),
        "triangles": len(tris),
        "doors_at": placed,
        "doors_asked": len(doors),
        "groups": kit.tagged_spans(tris),
    }


# The Green rosette draws three spokes at 120 degrees. Everything radial in
# the drum keys off this: the spokes themselves, and the guideway trusses, which
# are 2.6 km long and can only be held up where they cross one.
SPOKE_COUNT = 3


# --------------------------------------------------------------------------
# The guideway structure gauge
# --------------------------------------------------------------------------
# The guideway trusses run in the spoke planes because nothing else could carry
# them: 2,586 m of truss does not span unsupported and the spokes are the only
# radial structure there is (INV-012). The consequence went unnoticed for two
# sessions -- a tram car has to CROSS a spoke, and it did, straight through
# 6.43 m of solid structure, 168 of its 3,144 vertices inside the solid.
#
# Moving the cars is not a fix. `tram.guideway_cars` advertises a `phase`
# parameter that walks the whole train along the run, so whatever static offset
# is chosen, every car reaches its own spoke eventually. The structure has to
# open.
#
# How big the opening is, is a property of the INFRASTRUCTURE, not of whichever
# vehicle happens to be running. This is a structure gauge: a volume along the
# guideway that no structure may enter. `spoke()` cuts it out; `tram.py` asserts
# the car fits inside it. Declaring it once, here, is what stops the two being
# separately guessed -- and it is the only direction the dependency can run,
# since tram.py imports interior and not the other way about.
#
# Sized off the TRUSS, not off the car. The widest thing on the guideway is the
# light run at lateral 6.7 m, nearly twice the car's half width; the depth is
# the car's 11.5 m below the chord centreline (tram.py, read off 33a/34b as
# 0.65 of the truss depth) plus a metre of slack.
GUIDEWAY_GAUGE_DEPTH_M = 12.5     # radially outward from the chord centreline; INV-050
GUIDEWAY_GAUGE_HALF_W_M = 7.4     # lateral half width; INV-050
# The soffit sits just inboard of the bottom chord's running face, so the chord
# and its light runs stand proud of it and a car meets the same surfaces inside
# the portal that it meets everywhere else on the run. Flush would be
# structurally identical and would leave two coplanar faces in one plane, which
# z-fights across the whole opening.
GUIDEWAY_SOFFIT_RELIEF_M = 0.15   # INV-050

# The portal frame. A hole is not a portal: this project has already shipped a
# door interpenetrating a portal frame, and an unframed cut is where a real
# structure tears. The frame is a ring of heavier section standing proud of both
# faces of the spoke, and it is what lines the opening the car passes through.
SPOKE_PORTAL_FRAME_M = 1.6        # section of that ring, radially and laterally; INV-050
SPOKE_PORTAL_PROUD_M = 1.2        # how far it stands proud of each spoke face; INV-050
SPOKE_PORTAL_COLLAR_M = 4.0       # header and sill depth beyond the frame; INV-050


def guideway_gauge(schema, profile, sector):
    """The volume kept clear of structure along a guideway, in spoke-local axes.

    Returned as radii and a lateral half width because that is the plane the
    problem lives in: the car's position along z is a function of phase, so
    anything true in the (lateral, radius) plane is true for every phase at once.
    """
    r_bot = sector_radius(schema, profile, sector) * TRUSS_RADIUS_FRAC
    return {
        "chord_r_m": r_bot,
        "r_inner": r_bot + TRUSS_CHORD_M / 2.0 - GUIDEWAY_SOFFIT_RELIEF_M,
        "r_outer": r_bot + GUIDEWAY_GAUGE_DEPTH_M,
        "half_width_m": GUIDEWAY_GAUGE_HALF_W_M,
    }


def spoke_portal(schema, profile, sector):
    """Where and how big the aperture through a spoke is, or None if there is
    no guideway in this sector.

    Only the drum has guideway trusses, so only the drum's spokes are pierced.
    Cutting the hole everywhere would weaken structure for a vehicle that does
    not run there.
    """
    if sector != drum_sector(schema, profile):
        return None
    g = guideway_gauge(schema, profile, sector)
    f = SPOKE_PORTAL_FRAME_M
    c = SPOKE_PORTAL_COLLAR_M
    return {
        # The opening itself is exactly the gauge. Anything more would be
        # structure thrown away; anything less would foul the vehicle.
        "r0": g["r_inner"], "r1": g["r_outer"],
        "half_w": g["half_width_m"],
        # The frame ring around it.
        "r_frame0": g["r_inner"] - f, "r_frame1": g["r_outer"] + f,
        "half_w_frame": g["half_width_m"] + f,
        # The band of the spoke that is rebuilt as a pierced section.
        "r_band0": g["r_inner"] - f - c, "r_band1": g["r_outer"] + f + c,
    }


def _ring_slab(verts, tris, at, outer, inner, z0, z1):
    """A closed rectangular ring: a slab with a rectangular hole through it in z.

    `outer` and `inner` are (r_lo, r_hi, lat_lo, lat_hi) in the spoke's own
    frame; `at(r, lat, z)` places a point in world space. The hole runs right
    through the slab along z, which is the direction a tram travels.

    The four face quads are MITRED -- outer corner to inner corner -- rather
    than butted as four strips. Butted strips put a T-junction at every corner,
    where one quad's edge is half of another's, and a T-junction is a boundary
    edge whether or not the surface looks closed. That is one of the three
    causes of the end cap's 4,064 open edges in session 2y, in miniature, and it
    is the specific way a portal cut badly opens the spoke.
    """
    ro0, ro1, lo0, lo1 = outer
    ri0, ri1, li0, li1 = inner
    o = [(ro0, lo0), (ro1, lo0), (ro1, lo1), (ro0, lo1)]
    i = [(ri0, li0), (ri1, li0), (ri1, li1), (ri0, li1)]

    def q(p0, p1, p2, p3):
        b = len(verts)
        verts.extend([p0, p1, p2, p3])
        tris.append((b, b + 1, b + 2))
        tris.append((b, b + 2, b + 3))

    for k in range(4):
        k2 = (k + 1) % 4
        # The two faces of the slab, wound away from the material.
        q(at(*o[k], z1), at(*o[k2], z1), at(*i[k2], z1), at(*i[k], z1))
        q(at(*i[k], z0), at(*i[k2], z0), at(*o[k2], z0), at(*o[k], z0))
        # Outer skin.
        q(at(*o[k], z0), at(*o[k2], z0), at(*o[k2], z1), at(*o[k], z1))
        # The lining of the opening, facing into it -- this is what a passenger
        # sees going through, and what makes the hole a tunnel rather than a
        # gap in a surface.
        q(at(*i[k], z0), at(*i[k], z1), at(*i[k2], z1), at(*i[k2], z0))


def _spoke_profile(r0, r1, bore, nseg=9):
    """(r_start, r_end, half_width) for each nominal segment of a spoke.

    Split out so the pierced band can ask what the spoke's section WOULD have
    been where it is cut. Sizing the piers against the section they replace is
    the whole structural argument, and it needs that number.
    """
    out = []
    for k in range(nseg):
        f0, f1 = k / nseg, (k + 1) / nseg
        ra, rb = r0 + (r1 - r0) * f0, r0 + (r1 - r0) * f1
        # Barrel sections separated by collar groups, with an open lattice
        # through the middle third of the run -- the core shuttle reference
        # shows the tube is not a plain extrusion.
        lattice = 0.34 < f0 < 0.66
        collar = (k % 3 == 0)
        ww = bore * (0.62 if lattice else 1.0) * (1.18 if collar else 1.0)
        out.append((ra, rb, ww))
    return out


def spoke(schema, profile, sector, from_ring, to_ring, angle_deg=0.0, z=None,
          portal=True):
    """A radial transport tube between two rings, pierced where a guideway
    crosses it.

    The rosettes draw these as spokes from the outer rings to the axis, and the
    core shuttle reference shows the tube is not a plain extrusion -- smooth
    barrel, collar groups of fine rings at segment joints, an open lattice
    section, a pale collar where it meets the drum wall.

    LOAD PATH THROUGH A PIERCED SPOKE, and why one still stands up.

    A spoke is a TENSION member. The drum spins, so everything in it is thrown
    outward and the spokes are what stop the shell leaving: load runs from the
    rim inward to the hub. The opening sits between the guideway at r 236.6 m
    and the habitat floor at r 278.3 m, which is on the loaded side -- every
    newton the shell pulls with passes through the pierced band. This is not a
    hole in a stub.

    Cutting a 14.8 m slot out of a 21.2 m wide member removes 70% of its
    section and it has to be given back. Three things do that:

      1. Two PIERS either side of the opening, sized here so their combined
         cross-section is at least what the slot removed. The spoke swells
         laterally where it is pierced -- 21.2 m wide to 35.7 m -- which is what
         a member with a hole in it actually looks like. The self-test asserts
         the net section, so widening the gauge has to buy its width from
         somewhere rather than quietly thinning the piers.
      2. A FRAME ring standing proud of both faces around the opening, taking
         the corners, which is where a plain rectangular cut concentrates
         stress and tears.
      3. A HEADER inboard of the opening and a SILL outboard of it, both full
         width. These are what make it a frame rather than two separate legs:
         they tie the piers so both extend equally under load, and they feed the
         full-width spoke into the piers over a length instead of at a corner.

    The guideway's own weight enters here too. The truss's bottom chord and its
    light runs are let INTO the header, embedded across the spoke's full 21.2 m
    thickness -- that embedment is the bearing, and it is the reason the truss
    is in the spoke plane at all. It sits inboard of the opening, so truss load
    joins the tension above the hole and is carried into the piers by the
    header rather than across the opening.

    Sizing is an invention. Nothing in the reference set shows a spoke, let
    alone a pierced one; net section preserved is a rule of thumb and not an
    analysis, and it is conservative only in the one direction a rule of thumb
    can be. A frame showing the drum's radial structure would overturn it.
    """
    rings = ring_radii(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    zc = z if z is not None else (ex["z0"] + ex["z1"]) / 2.0
    r0 = rings[to_ring]["r_mid"]
    r1 = rings[from_ring]["r_mid"]

    verts, tris, groups = [], [], []
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def at(r, lat, zz):
        return (ca * r - sa * lat, sa * r + ca * lat, zz)

    def emit(fn, group):
        before = len(tris)
        fn()
        groups.extend([group] * (len(tris) - before))

    bore = schema["interior_topology"].get("spoke_bore_m", 9.0)
    segs = _spoke_profile(r0, r1, bore)

    # The pierced band, if a guideway crosses this spoke's radial run at all.
    por = spoke_portal(schema, profile, sector) if portal else None
    if por and not (r0 < por["r_band0"] and por["r_band1"] < r1):
        por = None

    # Section rectangles in the (lateral, radius) plane: what the spoke occupies
    # ignoring z. Reported rather than re-derived by the caller, because a
    # clearance test that re-derives the shape it is testing against is testing
    # its own arithmetic. `tram.spoke_clearance` consumes this.
    rects = []

    def box(ra, rb, ww, group):
        rects.append((-ww, ww, ra, rb))
        quad = [at(ra, ww, zc - ww), at(ra, -ww, zc - ww),
                at(rb, -ww, zc - ww), at(rb, ww, zc - ww)]
        quad += [(x, y, zz + 2 * ww) for x, y, zz in quad]
        emit(lambda: _box(verts, tris, quad), group)

    for ra, rb, ww in segs:
        if por is None:
            box(ra, rb, ww, "spoke")
            continue
        # Clip the plain run against the band. A segment can contribute a piece
        # on either side of it, or nothing at all.
        for ca_, cb_ in ((ra, min(rb, por["r_band0"])),
                         (max(ra, por["r_band1"]), rb)):
            if cb_ - ca_ > 1e-6:
                box(ca_, cb_, ww, "spoke")

    if por is not None:
        # The section the slot removes, taken as the widest the spoke would have
        # been anywhere across the band -- the conservative reading when the
        # band spans a collar, which it does.
        t = max(ww for ra, rb, ww in segs
                if rb > por["r_band0"] and ra < por["r_band1"])
        f = SPOKE_PORTAL_FRAME_M
        p = SPOKE_PORTAL_PROUD_M
        aw = por["half_w"]

        # Net section: the two piers plus the two frame jambs must together be
        # at least the plain section the band replaces. Solving for the pier
        # width rather than asserting a chosen one means a wider gauge pushes
        # the spoke wider instead of silently eating into the structure.
        gross = (2 * t) * (2 * t)
        frame_area = 2 * f * 2 * (t + p)
        pier_w = max(f, (gross - frame_area) / (2 * (2 * t)))
        w = por["half_w_frame"] + pier_w

        band = (por["r_band0"], por["r_band1"], -w, w)
        fr = (por["r_frame0"], por["r_frame1"],
              -por["half_w_frame"], por["half_w_frame"])
        hole = (por["r0"], por["r1"], -aw, aw)

        emit(lambda: _ring_slab(verts, tris, at, band, fr, zc - t, zc + t),
             "spoke_portal")
        emit(lambda: _ring_slab(verts, tris, at, fr, hole,
                                zc - t - p, zc + t + p), "spoke_portal_frame")

        # Header, sill and the two piers; then the frame ring's four members.
        rects.extend([
            (-w, w, por["r_band0"], por["r_frame0"]),
            (-w, w, por["r_frame1"], por["r_band1"]),
            (-w, -por["half_w_frame"], por["r_frame0"], por["r_frame1"]),
            (por["half_w_frame"], w, por["r_frame0"], por["r_frame1"]),
            (-por["half_w_frame"], por["half_w_frame"],
             por["r_frame0"], por["r0"]),
            (-por["half_w_frame"], por["half_w_frame"],
             por["r1"], por["r_frame1"]),
            (-por["half_w_frame"], -aw, por["r0"], por["r1"]),
            (aw, por["half_w_frame"], por["r0"], por["r1"]),
        ])
        por = dict(por, half_w_outer=w, pier_w=pier_w, half_thick=t,
                   net_section_m2=2 * pier_w * 2 * t + frame_area,
                   gross_section_m2=gross)

    # Measured off the built geometry rather than predicted from the constants,
    # so a piece emitted at the wrong depth widens this instead of hiding in it.
    z_span = (min(p[2] for p in verts), max(p[2] for p in verts))

    return verts, tris, {
        "sector": sector,
        "angle_deg": angle_deg,
        "z_span": z_span,
        "from_ring": rings[from_ring]["id"],
        "to_ring": rings[to_ring]["id"],
        "length_m": round(r1 - r0, 1),
        "gravity_from_g": round(gravity_at(schema, r1), 3),
        "gravity_to_g": round(gravity_at(schema, r0), 3),
        "triangles": len(tris),
        "groups": groups,
        "section_rects": rects,
        "portal": por,
    }


def drum_spoke_rings(schema, profile, sector):
    """(from_ring, to_ring) for a sector's full radial run.

    Found by ring KIND, not by index: the drum has three rings where every other
    sector has five, so an index means a different thing in each.
    """
    rings = ring_radii(schema, profile, sector)
    return (next(i for i, r in enumerate(rings) if r["kind"] == "deck_stack"),
            next(i for i, r in enumerate(rings) if r["kind"] == "core"))


def drum_spokes(schema, profile, sector, from_ring=None, to_ring=None,
                z=None):
    """Every radial spoke in a sector, at the canon 120 degree spacing.

    Placement used to live in whichever script happened to be rendering, which
    meant the count had no single source of truth and the trusses could silently
    stop matching the structure that carries them.
    """
    # Default to the full radial run: outermost deck stack to the core. Asking
    # callers for indices meant they had to know how many rings a sector has.
    d_from, d_to = drum_spoke_rings(schema, profile, sector)
    if from_ring is None:
        from_ring = d_from
    if to_ring is None:
        to_ring = d_to

    verts, tris, groups, solids = [], [], [], []
    for i in range(SPOKE_COUNT):
        ang = 360.0 * i / SPOKE_COUNT
        v, t, m = spoke(schema, profile, sector, from_ring, to_ring, ang, z)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(m["groups"])
        solids.append({"angle_deg": ang, "section_rects": m["section_rects"],
                       "z_span": m["z_span"], "portal": m["portal"]})
    return verts, tris, {"count": SPOKE_COUNT, "triangles": len(tris),
                         "groups": groups, "solids": solids}


def _box(verts, tris, corners):
    b = len(verts)
    verts.extend(corners)
    for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        tris.append((b + a, b + d, b + c))
        tris.append((b + a, b + e, b + d))


def _signed_volume(verts, tris):
    """Volume enclosed by a closed surface. Positive means faces point outward.

    A hole in a surface is not the only way to get it wrong: a piece can be
    closed and inside out, in which case it renders as a silhouette and is
    invisible from every direction it should be seen from.
    """
    v = 0.0
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        v += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
              - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0])
              + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])) / 6.0
    return v


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

    # Bands are emitted as explicit angular SPANS, with a riser wall wherever
    # two neighbouring bands sit at different radii.
    #
    # The first version walked fixed-width segments and emitted only the top
    # surface of whichever band each segment fell in. Neighbouring bands differ
    # by up to 9.5 m of relief (settlement +7.0 against water -2.5), so that
    # left **six longitudinal slots running the full 2,586 m length of the
    # drum**, straight through the ground into the sub-floor decks. They were
    # invisible for four sessions because the gap shows the background through
    # it, and the background is black. Found by an agent rendering against
    # magenta -- which is now the reason `_selftest` checks edges rather than
    # pixels.
    spans = []
    acc = 0.0
    for frac, name, relief in LAND_USE:
        spans.append((acc, acc + frac, name, relief))
        acc += frac

    verts, tris, groups = [], [], []
    n_z = max(2, int((z1 - z0) / z_step))

    def surface(f_a, f_b, ra, name):
        n = max(1, int(round((f_b - f_a) * 360.0 / seg_deg)))
        for ia in range(n):
            a0 = 2 * math.pi * (f_a + (f_b - f_a) * ia / n)
            a1 = 2 * math.pi * (f_a + (f_b - f_a) * (ia + 1) / n)
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
                # frame.
                tris.append((b, b + 2, b + 1))
                tris.append((b, b + 3, b + 2))
                groups.extend([f"drum_{name}"] * 2)

    def riser(f, r_lo, r_hi, name, face_ccw):
        """The wall closing the step between two bands of different relief.

        A cliff is seen from the LOW side, and low here means the larger radius
        -- up is inward. So the exposed face points tangentially, toward
        whichever neighbour sits further from the axis. `face_ccw` is True when
        that neighbour is the one at increasing angle.
        """
        a = 2 * math.pi * f
        ca, sa = math.cos(a), math.sin(a)
        for iz in range(n_z):
            za = z0 + (z1 - z0) * iz / n_z
            zb = z0 + (z1 - z0) * (iz + 1) / n_z
            b = len(verts)
            verts.extend([(r_lo * ca, r_lo * sa, za), (r_hi * ca, r_hi * sa, za),
                          (r_hi * ca, r_hi * sa, zb), (r_lo * ca, r_lo * sa, zb)])
            # Ascending radius then ascending z gives -theta; flip for +theta.
            if face_ccw:
                tris.append((b, b + 2, b + 1))
                tris.append((b, b + 3, b + 2))
            else:
                tris.append((b, b + 1, b + 2))
                tris.append((b, b + 2, b + 3))
            groups.extend([f"drum_riser_{name}"] * 2)

    f_start = (start_deg / 360.0)
    f_end = f_start + arc_deg / 360.0
    prev_r = None
    cursor = f_start
    while cursor < f_end - 1e-12:
        m = cursor % 1.0
        span = next(sp for sp in spans if sp[0] <= m < sp[1])
        seg_end = min(f_end, cursor + (span[1] - m))
        ra = r0 - span[3]
        surface(cursor, seg_end, ra, span[2])
        if prev_r is not None and abs(prev_r - ra) > 1e-9:
            riser(cursor, min(prev_r, ra), max(prev_r, ra), span[2],
                  face_ccw=prev_r < ra)
        prev_r = ra
        cursor = seg_end
    # Closing the ring: the wrap-around boundary needs its riser too, and it is
    # the one a linear walk never reaches.
    if abs(arc_deg - 360.0) < 1e-9:
        first_r = r0 - spans[0][3]
        if abs(prev_r - first_r) > 1e-9:
            riser(f_start, min(prev_r, first_r), max(prev_r, first_r),
                  spans[0][2], face_ccw=prev_r < first_r)

    # CIRCUMFERENTIAL RING FRAMES -- INV-073's rule at drum scale. The shell was
    # 65.0% of its detail floor over 5.8 million m2: bands running the full
    # 2,586 m with nothing crossing them, so the only line in the largest
    # surface on the station is the six longitudinal band risers.
    #
    # A ring frame at 250 m radius lays 1,570 m of arris for thirty-two
    # triangles -- roughly 49 m of line per triangle, the best yield anywhere in
    # this project, and a 2.6 km pressure drum spinning at 1 g manifestly has
    # them. They stand PROUD OF THE INNER SURFACE, which is the direction a
    # frame goes on a pressure vessel: the hoop load is carried outside the
    # skin, and a rib standing into the habitat is a rib people would walk into.
    n_ring = max(2, int((z1 - z0) / RING_FRAME_PITCH_M))
    for jj in range(1, n_ring):
        zz = z0 + jj * (z1 - z0) / n_ring
        nseg = max(24, int(360.0 / seg_deg))
        # ONE REVOLVED TORUS PER RING, not a box per angular segment. Boxes abut
        # and share their end faces, which put 14,040 non-manifold edges into
        # the shell -- four faces meeting one edge everywhere two neighbours
        # touched. A revolved closed section has no ends to share.
        base = len(verts)
        sect = ((r0, -1), (r0, 1),
                (r0 - RING_FRAME_RISE_M, 1), (r0 - RING_FRAME_RISE_M, -1))
        for ia in range(nseg):
            aa = 2 * math.pi * ia / nseg
            for rr, zs in sect:
                verts.append((rr * math.cos(aa), rr * math.sin(aa),
                              zz + zs * RING_FRAME_W_M / 2))
        for ia in range(nseg):
            c0 = base + 4 * ia
            c1 = base + 4 * ((ia + 1) % nseg)
            for q in range(4):
                q2 = (q + 1) % 4
                tris.append((c0 + q, c1 + q, c1 + q2))
                tris.append((c0 + q, c1 + q2, c0 + q2))
            groups.extend(["drum_ring_frame"] * 8)

    # THE RING FRAMES ARE EXCLUDED, and the exemption is argued rather than
    # assumed. This test asks "would a viewer standing inside the drum see this
    # surface, or is it backface-culled". A ring frame is a closed solid that
    # intersects the shell: its base at r0 is buried in the skin, can never be
    # seen from inside, and necessarily points away from the axis. Including it
    # would make a correct mesh fail. What the test is FOR -- catching an
    # inverted ground surface, which renders black rather than erroring -- is
    # untouched, because the shell itself is still measured at 100%.
    _shell = [tr for tr, gp in zip(tris, groups) if gp != "drum_ring_frame"]
    inward = _inward_fraction(verts, _shell)
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


def boundary_edges(verts, tris, tol=4):
    """Edges used by exactly one triangle, i.e. the holes in a surface.

    A closed surface has none; an open one has them only along its intended
    borders. This is the measurement that four sessions of renders could not
    make, because a hole in geometry shows the background through it and the
    background is black.

    MOVED INTO `interior_kit` and re-exported here, so the module that builds
    the pieces can gate their closure. It was defined here and the kit could not
    import it without a cycle, which is why `interior_kit._selftest` checked
    closure by casting rays overhead -- a test that cannot see an open edge in a
    door frame, and did not, for as long as every door on the station had 176 of
    them. Returns `(open, non-manifold)`; note that it is a PAIR, and calling
    `len()` on the result is a mistake this session made and caught with a
    negative control.
    """
    return kit.boundary_edges(verts, tris, tol=tol)


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
        # "Not pointing outward" rather than "pointing inward": the band risers
        # are tangential walls whose radial component is zero, and they are
        # legitimate. A flipped ground surface still scores +1 here and still
        # fails, which is the case this measurement exists for.
        rad = math.hypot(cx, cy) or 1.0
        if (n[0] * cx + n[1] * cy) / rad <= 1e-6 * max(
                1.0, math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)):
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

    # The cap is emitted as ONE CONTINUOUS LATHE at a single fine segment count,
    # with the plating expressed as material groups and the ribs and rim lights
    # laid on top as closed boxes.
    #
    # It was not always. The first version emitted every plate as its own quad
    # at its own per-course segment count. That made the cap read correctly and
    # left it **open**: 4,064 of 7,684 edges were boundary edges, 3,744 of them
    # nowhere near the rim or the aperture, so from inside the habitat you saw
    # straight through the bulkhead in dozens of places. Three causes, all
    # invisible against a dark background, all removed by the same decision:
    #   - per-course segment counts put a T-junction at every course boundary,
    #     since a coarse course's edge vertices are not a subset of a fine one's;
    #   - the checker offset moved alternate plates 0.35 m in z with nothing
    #     bridging the step;
    #   - the axial course walls were built at a third segment count again.
    # The measured "roughly square plates" character survives, because the
    # tessellation was never what carried it -- the RIB SPACING is, and that is
    # still per-course. What the surface does underneath is now independent of
    # what is drawn on it.
    n_seg = max(_endcap_segments(us[ci], us[ci + 1], r0)
                for ci in range(len(us) - 1))

    def course_z(ci):
        return ENDCAP_STEP_M if ci % 2 == 0 else 0.0

    # Radial profile as a polyline: each course a flat annulus, each rib an
    # axial wall at the shared radius. Lathed once, so every vertex is shared
    # and the surface is watertight by construction rather than by care.
    rings = []
    for ci in range(len(us) - 1):
        rings.append((us[ci], course_z(ci), ci))
        rings.append((us[ci + 1], course_z(ci), ci))
        if ci + 1 < len(us) - 1:
            rings.append((us[ci + 1], course_z(ci + 1), ci))

    for i in range(len(rings) - 1):
        (ua, za, ca), (ub, zb, _cb) = rings[i], rings[i + 1]
        if abs(ua - ub) < 1e-12 and abs(za - zb) < 1e-12:
            continue
        wall = abs(ua - ub) < 1e-12
        for sg in range(n_seg):
            a0 = 2 * math.pi * sg / n_seg
            a1 = 2 * math.pi * (sg + 1) / n_seg
            # Checker-plating is a GROUP, not a displacement. The footage shows
            # two courses reading differently from the plain ones, which is a
            # plating pattern; expressing it as 0.35 m of relief is what tore
            # the surface, and 0.35 m on a 278 m radius was never going to read
            # as relief anyway.
            grp = ("endcap_course_wall" if wall else
                   f"endcap_plate_c{ca}" +
                   ("_checker" if (ca in ENDCAP_CHECKER and sg % 2 == 0) else ""))
            ring_quad(ua, ub, a0, a1, za, zb, grp)

    # Ribs, as closed boxes so they cannot open the surface however they are
    # spaced. Spacing stays per-course, which is what was measured.
    for ci in range(len(us) - 1):
        uo, ui = us[ci], us[ci + 1]
        n_rib = _endcap_segments(uo, ui, r0)
        z = course_z(ci)
        half = ENDCAP_RIB_W_M / 2.0 / max(uo * r0, 1.0)
        for sg in range(n_rib):
            a = 2 * math.pi * (sg + 1) / n_rib
            base = [pt(uo, a - half, z), pt(uo, a + half, z),
                    pt(ui, a + half, z), pt(ui, a - half, z)]
            _box(verts, tris,
                 base + [pt(uo, a - half, z - ENDCAP_RIB_H_M),
                         pt(uo, a + half, z - ENDCAP_RIB_H_M),
                         pt(ui, a + half, z - ENDCAP_RIB_H_M),
                         pt(ui, a - half, z - ENDCAP_RIB_H_M)])
            groups.extend(["endcap_rib"] * 12)

    # Rim lights. The one feature of the cap that was counted rather than
    # estimated, and what makes the rim read as a lit edge at 2 km. Boxes for
    # the same reason as the ribs: a flat patch laid on a surface is a free
    # edge, and free edges are what tore the first cap.
    z0c = course_z(0)
    for i in range(ENDCAP_RIM_LIGHTS):
        a0 = 2 * math.pi * (i + 0.22) / ENDCAP_RIM_LIGHTS
        a1 = 2 * math.pi * (i + 0.78) / ENDCAP_RIM_LIGHTS
        base = [pt(1.0, a0, z0c), pt(1.0, a1, z0c),
                pt(0.965, a1, z0c), pt(0.965, a0, z0c)]
        _box(verts, tris,
             base + [pt(1.0, a0, z0c - 0.6), pt(1.0, a1, z0c - 0.6),
                     pt(0.965, a1, z0c - 0.6), pt(0.965, a0, z0c - 0.6)])
        groups.extend(["endcap_rimlight"] * 12)

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

def narrowest_z(profile, z_m, z_span_m=0.0, samples=401):
    """The z over a footprint where the core hull is narrowest.

    A PLACE IS NOT A POINT ON THE AXIS. Every z-aware call in this project
    passes the place's CENTRE z, and that is enough to be wrong: the station
    tapers, footprints run to 442 m along the axis, and a room whose centre
    clears the hull comfortably can still poke out of the ship at one end.
    Measured over the register, twelve places are in exactly that state --
    `docking_bays` fits at its centre z and is 51.4 m outside the hull 70 m
    forward of it, `plant_zone` and `downbelow` by 40.9 m at the Grey/Green
    boundary.

    So the z that means something for a place is not its centre but the
    WORST z it occupies, and that is what this returns. Feed it to
    `ring_radii(z_m=)`, `decks_in_ring(z_m=)` or `ring_cells(z_m=)` and the
    result is a deck stack that fits along the whole room rather than at one
    sample of it.

    IT WALKS THE PROFILE'S OWN SAMPLES, NOT A FIXED GRID, and the first version
    did not. 401 evenly-spaced probes was chosen to match the density
    `directory.py`'s hand-audit of ten rows used -- which sounds careful and is
    the wrong shape: the radius profile is 1,978 samples at a 4.07 m pitch, so
    a fixed grid can straddle a step and miss the narrow side of it entirely.
    That is not hypothetical here. `hull_radius_at` returns the sample at or
    BELOW z and `core_hull_radius_at` returns the NEAREST sample, two
    conventions in this one module that disagree by up to **95.6 m** at a step
    in the profile -- so which side of a control point a probe lands on is
    worth as much as a whole sector's taper.

    Walking the profile's own indices, plus the two that bracket the span,
    makes the answer EXACT rather than sampled and removes the exposure. It is
    also usually cheaper: a 40 m footprint touches ~11 samples, not 401.

    `samples` is kept only so existing callers do not break; it is unused.
    """
    zs = [q["z_m"] for q in profile]
    if not z_span_m:
        # Still not a point query: bracket the sample interval containing z, so
        # a place sitting just past a control point cannot be measured against
        # the wider side of the step it is standing on.
        lo = hi = z_m
    else:
        lo, hi = z_m - z_span_m / 2.0, z_m + z_span_m / 2.0
    i0 = max(0, bisect.bisect_left(zs, lo) - 1)
    i1 = min(len(zs) - 1, bisect.bisect_right(zs, hi))
    core = core_hull_profile(profile)
    worst_i = min(range(i0, i1 + 1), key=lambda i: core[i])
    # Report a z INSIDE the footprint where one exists, so the returned value
    # can be handed to `ring_radii(z_m=)` without addressing a place to a z it
    # does not occupy.
    return min(max(zs[worst_i], lo), hi) if z_span_m else zs[worst_i]


def place_floor_radius(schema, profile, place, z_aware=False):
    """The floor radius a located place is built at, and the ring/deck it lands on.

    ONE COMPUTATION, TWO CALLERS, AND THEY USED TO BE TWO COMPUTATIONS.
    `rooms.room_extent_m` needed the floor radius to turn an angular footprint
    into metres, and `directory.gravity_of` needed it to report a gravity, and
    each wrote its own four lines: resolve the deck stacks, clamp the ring
    index, clamp the deck index, take `floor_r_m`. Identical logic, no shared
    definition, so a fix to either was a fix to one of them -- which is the
    defect this file's own history calls "a fix applied to an instance and not
    to the rule".

    `z_aware=False` reproduces what the station is built from TODAY: the
    sector's widest cylinder, regardless of where along the axis the place
    actually is. `z_aware=True` asks the same question of the hull the place
    really sits in. `hull_fit()` reports the difference and it is not small.

    Returns (floor_r_m, ring_index, deck_index, deck_dict). The indices are the
    CLAMPED ones -- what the builder used, not what the register asked for --
    so a caller can see when a place did not get the deck it named.

    THE DECK DICT IS RETURNED FOR A REASON AND IT IS NOT CONVENIENCE. The
    first version of this returned the radius alone, and `directory.gravity_of`
    then re-derived gravity from it -- which moved three places by 0.0001 g,
    because `decks_in_ring` rounds `floor_r_m` to 2 dp and computes `floor_g`
    from the UNROUNDED radius. A tiny drift, caught only because the
    refactor's A/B compared all 129 places rather than spot-checking one. The
    deck's own `floor_g` is the authority; hand it over rather than inviting
    every caller to recompute it from a rounded number.
    """
    z = None
    if z_aware:
        z = narrowest_z(profile, place["z_m"],
                        (place.get("footprint") or (0.0, 0.0))[1])
    rings = ring_radii(schema, profile, place["sector"], z_m=z)
    stacks = [i for i, r in enumerate(rings) if r["kind"] == "deck_stack"]
    if not stacks:
        return sector_radius(schema, profile, place["sector"]), None, None, None
    ri = stacks[min(place["ring"], len(stacks) - 1)]
    decks = decks_in_ring(schema, profile, place["sector"], ri, z_m=z)
    if not decks:
        return sector_radius(schema, profile, place["sector"]), ri, None, None
    di = min(place["deck"], len(decks) - 1)
    return decks[di]["floor_r_m"], ri, di, decks[di]


def hull_fit(schema, profile, verbose=True):
    """Is every located place INSIDE the pressure hull along its whole length?

    THE GATE THAT DID NOT EXIST, AND THE ONE DEFECT NO OTHER GATE HERE CAN SEE.
    Every gate in this project measures a place against a standard of its own
    kind: `density.py` scores its line density, `materials.py` its PBR
    coverage, `measure_frame.py` its exposure, `deck.py --sweep` whether a body
    can reach it. **A room that is ninety metres outside the ship passes every
    one of them**, because each is a question about the room and none is a
    question about where the room is. The interior renders never showed it
    either: you cannot see the hull from inside a room that has no window, and
    until `station/vista.py` there were no windows.

    The limit is the one `rings_fitting_at` already applies --
    `core_hull_radius_at(z) - HULL_SKIN_M` -- so this gate is not a new
    standard. It is the existing standard asked of the places that never went
    through the function that applies it.

    Three failure kinds, and they want three different fixes, so they are
    reported apart:

      `outside`   the place's floor radius is outside the hull at its own
                  CENTRE z. The address resolves against the sector's widest
                  cylinder and the place is not there. 22 of them, worst
                  `mainstage_node` at 135.9 m and `cnc` at 100.7 m.
      `taper`     the centre fits and the SPAN does not -- one end of the room
                  is outside the ship. 12 of them. See `narrowest_z`.
      `deck_gap`  the register names a deck NUMBER that the generated stack
                  does not carry as an index. `deck.deck_index()` exists to
                  rank these into indices; `rooms.room_extent_m` instead
                  clamps to the innermost deck, so the two build paths put the
                  same place on different decks.

    Returns (rows, counts). Fails loudly rather than returning a summary,
    because a summary is what let this run for twenty-odd sessions.
    """
    import directory as _dr                     # lazy: directory imports us
    rows = []
    for q in _dr.PLACES:
        if q.get("z_m") is None or q.get("sector") is None:
            continue
        span = (q.get("footprint") or (0.0, 0.0))[1]
        r_now, ri, di, _d = place_floor_radius(schema, profile, q,
                                              z_aware=False)
        z_worst = narrowest_z(profile, q["z_m"], span)
        lim_c = core_hull_radius_at(profile, q["z_m"]) - HULL_SKIN_M
        lim_w = core_hull_radius_at(profile, z_worst) - HULL_SKIN_M
        kinds = []
        if r_now > lim_c:
            kinds.append("outside")
        elif r_now > lim_w:
            kinds.append("taper")
        # A deck NUMBER the stack cannot index. Asked of the z-blind stack,
        # which is the deeper one -- the z-aware stack is shorter still.
        stack = decks_in_ring(schema, profile, q["sector"], ri) if ri is not None else []
        if stack and q["deck"] >= len(stack):
            kinds.append("deck_gap")
        r_fit, _rfi, _rdi, _rd = place_floor_radius(schema, profile, q,
                                                   z_aware=True)
        # NO DECK STACK SURVIVES AT THIS PLACE'S OWN z. Threading z through the
        # builders does NOT fix these: there is nothing at that radius to move
        # them to, so the address itself has to change. Three of them, and
        # `mainstage_node` is the clearest -- the core hull is 18.3 m where the
        # register puts it, which is narrower than a corridor.
        if _rdi is None:
            kinds.append("homeless")
        if not kinds:
            continue
        rows.append({
            "key": q["key"], "sector": q["sector"],
            "ring": q["ring"], "deck": q["deck"],
            "z_m": q["z_m"], "span_m": span, "z_worst": round(z_worst, 1),
            "built_r_m": round(r_now, 1),
            "limit_centre_m": round(lim_c, 1),
            "limit_worst_m": round(lim_w, 1),
            "out_by_m": round(r_now - min(lim_c, lim_w), 1),
            "z_aware_r_m": round(r_fit, 1),
            "decks_in_stack": len(stack),
            "kinds": kinds,
        })
    counts = {}
    for r in rows:
        for k in r["kinds"]:
            counts[k] = counts.get(k, 0) + 1
    counts["places"] = sum(1 for q in _dr.PLACES if q.get("z_m") is not None)
    counts["failing"] = len(rows)
    # THE COUNT THAT GOES IN A SENTENCE IS NOT `len(rows)`. Places can carry
    # two kinds at once -- `core_shuttle` tapers out of the hull AND names a
    # deck number the stack cannot index -- and `deck_gap` places are INSIDE
    # the hull. Reporting "49 outside the pressure hull" would have been a
    # third of it wrong, in the direction that makes the finding look bigger.
    counts["outside_hull"] = len({r["key"] for r in rows
                                  if "outside" in r["kinds"]
                                  or "taper" in r["kinds"]})
    if verbose:
        head = {
            "outside": "OUTSIDE THE HULL AT THEIR OWN CENTRE z",
            "taper": "CENTRE FITS, ONE END OF THE ROOM DOES NOT",
            "deck_gap": "DECK NUMBER THE STACK CANNOT INDEX (these are inside "
                        "the hull)",
            "homeless": "NO DECK STACK EXISTS AT THIS z AT ALL",
        }
        for kind in ("outside", "taper", "homeless", "deck_gap"):
            sel = sorted([r for r in rows if kind in r["kinds"]],
                         key=lambda r: -r["out_by_m"])
            if not sel:
                continue
            print("\n%s: %d  -- %s" % (kind.upper(), len(sel), head[kind]))
            for r in sel:
                if kind == "deck_gap":
                    print("   %-20s %-6s ring%d deck %-3s names deck %d of a "
                          "stack %d deep -- built at %7.1f m"
                          % (r["key"], r["sector"], r["ring"], r["deck"],
                             r["deck"], r["decks_in_stack"], r["built_r_m"]))
                else:
                    print("   %-20s %-6s ring%d deck%-3s built %7.1f  limit "
                          "%7.1f  out by %6.1f m   (z-aware: %7.1f)"
                          % (r["key"], r["sector"], r["ring"], r["deck"],
                             r["built_r_m"], min(r["limit_centre_m"],
                                                 r["limit_worst_m"]),
                             r["out_by_m"],
                             r["z_aware_r_m"] if "homeless" not in r["kinds"]
                             else float("nan")))
        print("\nhull fit: %d of %d located places are built OUTSIDE the "
              "pressure hull (%d at their centre, %d only at one end of their "
              "own footprint). A further %d are inside it but name a deck "
              "number their stack cannot index. %d rows in all."
              % (counts["outside_hull"], counts["places"],
                 counts.get("outside", 0), counts.get("taper", 0),
                 counts.get("deck_gap", 0), counts["failing"]))
    return rows, counts


def ring_cells(schema, profile, sector, ring_index, deck_index=0, margin=1.5,
               z_m=None):
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
    decks = decks_in_ring(schema, profile, sector, ring_index, z_m=z_m)
    if not decks:
        return None
    # CLAMPED, AND IT USED TO RAISE. `decks[deck_index]` on a stack shorter
    # than the index is an IndexError, and fifteen of the register's places
    # carry a deck NUMBER (Grey 40, 55, 80; Yellow 30) that no generated stack
    # can index -- see `deck.deck_index`, which ranks them. So this function
    # was a live crash for 15 of 129 places and nobody had found it, because
    # the two callers that DO reach those places translate or clamp first.
    # Clamping matches `rooms.room_extent_m` and `directory.gravity_of`, which
    # are the other two consumers; `hull_fit()` reports the gap rather than
    # letting the clamp hide it.
    deck = decks[min(deck_index, len(decks) - 1)]
    r = deck["floor_r_m"]
    cw = kit.PROVISIONAL["corridor_width_m"]
    want = streaming_cell_deg(r, cw, margin)
    n = max(1, int(360.0 // want))
    # Snap UP to a divisor of 36, so every cell spans a whole number of 10
    # degree regions.
    #
    # The gazetteer research (docs/gazetteer/LOCATIONS.md section 1) turned up a
    # reading in which the number in "Grey 17" is not a radial level at all but
    # one of 36 angular regions of 10 degrees each. That source is authority 4
    # and contradicts itself, so nothing here adopts it -- C-004 stays open. But
    # it costs NOTHING to keep the option, and retrofitting it after cells carry
    # authored content would be expensive.
    #
    # Snapping UP rather than down is what makes it free. Down was affordable
    # but barely: Grey ring 2 landed at 59,040 triangles against the 60,000
    # cell gate, 98% with structure alone and nothing left for props, signage or
    # NPCs. Up gives SMALLER cells, so the worst cell in the station stays where
    # it was and Grey ring 2 drops to 39,360. Every cell is still wider than its
    # own sight line, which is the property that actually matters; the margin
    # falls from 1.5 to between 1.12 and 1.68, which is slack rather than a
    # guarantee.
    # Snapping up is only safe while the smaller cell still clears its own
    # sight line, and the divisor list has a 2x gap between 18 and 36 where it
    # stops being. Grey's ring 1 found it the moment the metric hull allowance
    # widened the ring: it asks for 19 cells, 36 is the next divisor up, and
    # that halves the cell to 82.2 m against a 98.9 m sight line -- the player
    # standing at one end sees 17 m into a cell that is not resident.
    #
    # So the snap runs up only as far as the guarantee holds, then falls back
    # DOWN to the nearest divisor at or below the requested count. Down is
    # always safe for the guarantee, because it makes cells larger; it costs
    # triangles per cell rather than correctness, and the cell gate is what
    # catches that.
    divisors = (1, 2, 3, 4, 6, 9, 12, 18, 36)
    circ = 2 * math.pi * r
    sight = sight_line(r, cw)
    up = [d for d in divisors if d >= n and circ / d >= sight]
    n = min(up) if up else max([d for d in divisors if d <= n] or [1])
    cell_deg = 360.0 / n
    rr = ring_radii(schema, profile, sector, z_m=z_m)
    return {
        "sector": sector,
        "ring_index": ring_index,
        "ring": rr[min(ring_index, len(rr) - 1)]["id"] if rr else "none",
        "deck_index": min(deck_index, len(decks) - 1),
        "deck_index_asked": deck_index,
        "z_m": z_m,
        "radius_m": r,
        "gravity_g": round(gravity_at(schema, r), 4),
        "circumference_m": round(2 * math.pi * r, 1),
        "cells": n,
        "cell_deg": cell_deg,
        "cell_length_m": round(2 * math.pi * r / n, 1),
        "sight_line_m": round(sight_line(r, cw), 1),
    }


def deck_cell(schema, profile, sector, ring_index, deck_index, cell_index,
              z_offset=None, z_m=None):
    """One streaming cell: the corridor run for one deck over one arc.

    `z_m` REACHES THE GEOMETRY, which is the only reason threading it through
    `ring_cells` is worth anything: the cell's radius, cell count and arc all
    come from the plan, so a z-aware plan is a z-aware cell. Pass
    `narrowest_z(profile, centre, span)` rather than a centre -- see its
    docstring for why a place is not a point on the axis.
    """
    plan = ring_cells(schema, profile, sector, ring_index, deck_index, z_m=z_m)
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
                    # "habitat" or "plant" -- above HABITABLE_G_MAX a deck is
                    # pressurised volume the player can reach but nobody is
                    # billeted on. The engine needs it to pick a kit, and the
                    # NPC layer needs it to know where not to place residents.
                    "use": deck["use"],
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

    # --- the core hull, and the metric skin that replaced HULL_ALLOWANCE ----
    # The fraction is gone. Asserting its absence is cheap and it is exactly
    # the kind of thing a later session reintroduces because a fraction is the
    # obvious way to write "most of the radius".
    check("HULL_ALLOWANCE is gone", "HULL_ALLOWANCE" not in globals(),
          "a fraction of the radius is the wrong kind of quantity for a "
          "pressure hull -- see INV-026")

    core = core_hull_profile(profile)
    raw = [q["radius_m"] for q in profile]
    check("the opening never erodes below the raw profile",
          all(c >= r - 1e-9 or abs(c - r) < 1e-9
              for c, r in zip(core, [min(raw)] * len(raw))) and
          min(core) >= min(raw) - 1e-9,
          f"core min {min(core):.1f} vs raw min {min(raw):.1f}")
    check("the opening never rises above the raw profile",
          all(c <= r + 1e-9 for c, r in zip(core, raw)),
          "an opening is bounded above by its input")
    for sec, ex in schema["sectors"]["extents_m"].items():
        band = [(core[i], raw[i]) for i, q in enumerate(profile)
                if ex["z0"] <= q["z_m"] <= ex["z1"]]
        if not band:
            continue
        # A plain running minimum failed this in grey: it reported 428.7 m in a
        # band whose narrowest real sample is 436.4 m, because the window
        # reached past the band edge into a narrower neighbour and eroded the
        # step. The dilation half of the opening is what restores it.
        check(f"{sec}: core hull is not eroded past the band's own minimum",
              min(c for c, _ in band) >= min(r for _, r in band) - 1e-9,
              f"core {min(c for c, _ in band):.1f} < raw "
              f"{min(r for _, r in band):.1f}")

    # The cross-check that justifies the whole method: the generalised shell
    # extraction and the drum's hand-measured pressure hull are two derivations
    # that share no arithmetic, and they land 2.5 m apart on a 315 m radius.
    shell_drum = sector_shell_radius(schema, profile, drum_sector(schema, profile))
    hull_drum = habitat_hull_radius(schema, profile) + HULL_SKIN_M
    check("shell extraction agrees with the measured habitat pressure hull",
          abs(shell_drum - hull_drum) / hull_drum < 0.01,
          f"{shell_drum:.1f} m vs {hull_drum:.1f} m "
          f"({abs(shell_drum - hull_drum):.1f} m apart)")

    # Matching the drum on its pressure hull rather than on its floor is what
    # makes the identification robust. Assert the MARGIN, not just the winner:
    # a test that only checks which one won cannot tell a 39x margin from a
    # coin toss, and this decides which band the whole habitat is built in.
    errs = sorted(abs(sector_shell_radius(schema, profile, s) - hull_drum)
                  for s in schema["sectors"]["extents_m"])
    check("the drum is identified by a wide margin, not a narrow one",
          errs[1] > 10 * max(errs[0], 0.1),
          f"best {errs[0]:.1f} m, runner-up {errs[1]:.1f} m")

    for sec in schema["sectors"]["extents_m"]:
        r_out = sector_radius(schema, profile, sec)
        shell = sector_shell_radius(schema, profile, sec)
        # The outermost floor sits inside real hull, by exactly the skin. This
        # is what the fraction could not promise: 0.86 removed 65 m in grey and
        # 22 m in yellow, neither of which is a thickness of anything.
        if sec != drum_sector(schema, profile):
            # NOTE what this does and does not test. It guards the FORMULA --
            # that `sector_radius` subtracts a metric skin rather than scaling
            # by a fraction, which is the regression this change exists to
            # prevent. It cannot guard the VALUE: r_out is defined as
            # shell - HULL_SKIN_M, so the difference is that constant by
            # construction, whatever it is set to. `tools/mutation_sweep.py`
            # reported HULL_SKIN_M unguarded on exactly this point; the
            # assertions that do pin the value are below.
            check(f"{sec}: outermost floor is one metric skin inside the shell",
                  abs((shell - r_out) - HULL_SKIN_M) < 1e-6,
                  f"{shell - r_out:.2f} m")
        check(f"{sec}: outermost floor is inside the core hull",
              r_out <= shell + 1e-6, f"{r_out:.1f} m vs shell {shell:.1f} m")

    # HULL_SKIN_M is an invention (INV-013) with no source to check it against,
    # so it cannot be asserted directly -- but its CONSEQUENCES are published
    # and can be. The drum's sub-floor stack is the one place the skin decides
    # something the rest of the project quotes: STATE.md, the gazetteer's
    # Downbelow section and the streaming manifest all state nine decks between
    # the Garden floor and the pressure hull. At a 7.5 m skin that becomes
    # eight. This is what makes the constant load-bearing rather than decorative.
    #
    # Be honest about the band it pins: the stack is 38.5 - skin metres at a
    # 3.6 m pitch, so nine decks holds for any skin in (2.5, 6.1] m. It catches
    # a hull growing thick enough to eat habitable volume, which is the failure
    # that matters, and not a hull thinning from 6 m to 4 m, which is invisible
    # to every consequence the project currently derives.
    stack = decks_in_ring(schema, profile, drum_sector(schema, profile), 0)
    check("the drum's sub-floor stack is the nine decks the project quotes",
          len(stack) == 9,
          f"{len(stack)} decks in "
          f"{habitat_hull_radius(schema, profile) - r_drum:.1f} m at a "
          f"{DECK_PITCH_M} m pitch")

    # --- the habitable ceiling ---------------------------------------------
    r_hab = habitable_radius(schema)
    check("the habitable ceiling is exactly HABITABLE_G_MAX",
          abs(gravity_at(schema, r_hab) - HABITABLE_G_MAX) < 1e-9,
          f"{gravity_at(schema, r_hab):.9f} g at {r_hab:.1f} m")
    # The drum's sub-floor stack is occupied by construction -- it is the
    # service space under the Garden and the gazetteer sites people in it. If
    # the ceiling ever drops below the pressure hull's 1.117 g, the drum's own
    # basement becomes plant and that is a contradiction, not a design change.
    d_hull = habitat_hull_radius(schema, profile)
    check("the drum's whole sub-floor stack stays habitable",
          gravity_at(schema, d_hull) <= HABITABLE_G_MAX,
          f"pressure hull is {gravity_at(schema, d_hull):.3f} g against a "
          f"{HABITABLE_G_MAX} g ceiling")
    seen_plant = False
    for sec in schema["sectors"]["extents_m"]:
        for ri, ring in enumerate(ring_radii(schema, profile, sec)):
            if ring["kind"] != "deck_stack":
                continue
            for d in decks_in_ring(schema, profile, sec, ri):
                want = "habitat" if d["floor_g"] <= HABITABLE_G_MAX else "plant"
                seen_plant = seen_plant or d["use"] == "plant"
                check(f"{sec} {ring['id']} d{d['deck_index']}: use matches "
                      f"gravity", d["use"] == want,
                      f"{d['use']} at {d['floor_g']:.3f} g")
    # If nothing is plant the tag is dead weight and the ceiling is not doing
    # any work -- which would mean either the ceiling or the radii moved.
    check("the station has plant decks at all", seen_plant,
          "grey's outer 34 decks sit above 1.25 g")

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
    for cap_end in ("fore", "aft"):
        cv, ct, cm = drum_end_cap(schema, profile, "green", cap_end)
        want = -1.0 if cap_end == "fore" else 1.0
        surf = surf_ok = wall = wall_ok = 0
        solids = {}
        for i, (ia, ib, ic) in enumerate(ct):
            p0, p1, p2 = cv[ia], cv[ib], cv[ic]
            u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            w = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            n = (u[1] * w[2] - u[2] * w[1],
                 u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            nlen = math.sqrt(sum(x * x for x in n)) or 1.0
            g = cm["groups"][i]
            if g.startswith("endcap_plate"):
                surf += 1
                surf_ok += n[2] * want > 0
            elif g == "endcap_course_wall":
                wall += 1
                wall_ok += abs(n[2] / nlen) < 0.05      # axial wall, radial normal
            else:
                solids.setdefault(g, []).append([x / nlen for x in n])
        # A cap surface facing the wrong way is invisible from inside the drum,
        # which is the only place it is ever seen.
        check(f"{cap_end} cap: surface faces into the drum",
              surf and surf_ok == surf, f"{surf_ok}/{surf}")
        check(f"{cap_end} cap: course walls are axial", wall_ok == wall,
              f"{wall_ok}/{wall}")
        # Ribs and rim lights are closed boxes laid on the surface. The previous
        # version of this loop put them in an `else` branch that scored every
        # one of them as passing -- a test that could not fail, on 768 of the
        # cap's triangles. A box is distinguishable from a flat patch by having
        # faces that oppose each other, so that is what gets asserted.
        for g, ns in solids.items():
            worst = min(a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
                        for a in ns for b in ns)
            check(f"{cap_end} cap: {g} is a solid, not a flat patch",
                  worst < -0.9, f"most-opposed face pair dot = {worst:.3f}")
        check(f"{cap_end} cap: 48 rim lights as closed boxes",
              cm["rim_lights"] == 48 and
              sum(g == "endcap_rimlight" for g in cm["groups"]) == 48 * 12,
              str(sum(g == "endcap_rimlight" for g in cm["groups"])))
        check(f"{cap_end} cap: 8 concentric courses", cm["courses"] == 8,
              str(cm["courses"]))
        check(f"{cap_end} cap: aperture matches the schema core radius",
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

    # Every cell spans a whole number of 10 degree regions -- see ring_cells().
    # Cheap to keep, expensive to retrofit, and it does not commit us to the
    # reading that motivated it: C-004 is untouched either way.
    for sec in schema["sectors"]["extents_m"]:
        for i, r in enumerate(ring_radii(schema, profile, sec)):
            if r["kind"] != "deck_stack":
                continue
            pl = ring_cells(schema, profile, sec, i)
            check(f"{sec} {r['id']}: cell count divides 36",
                  36 % pl["cells"] == 0,
                  f"{pl['cells']} cells of {pl['cell_deg']:.2f} deg")
            check(f"{sec} {r['id']}: cell spans whole 10 deg regions",
                  abs(pl["cell_deg"] / 10.0 - round(pl["cell_deg"] / 10.0)) < 1e-9,
                  f"{pl['cell_deg']:.2f} deg")

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

    # --- the drum must not leak --------------------------------------------
    # Both surfaces below shipped with holes and passed every test at the time,
    # because nothing measured whether they were closed. The end cap was 4,064
    # boundary edges out of 7,684 -- gashes you could see straight through from
    # inside the habitat -- and the shell had six longitudinal slots running its
    # full 2,586 m wherever two land-use bands sat at different heights. Neither
    # showed in a render against a dark background, which is exactly why this is
    # an edge count and not a picture.
    shell_v, shell_t, shell_m = drum_interior(schema, profile, "green",
                                              arc_deg=360.0, seg_deg=4.0,
                                              z_step=200.0)
    bnd, nonman = boundary_edges(shell_v, shell_t)
    ends = {round(z, 1) for e in bnd for (_x, _y, z) in e}
    dex = schema["sectors"]["extents_m"]["green"]
    check("drum shell is closed except at its two ends",
          ends <= {round(float(dex["z0"]), 1), round(float(dex["z1"]), 1)},
          f"{len(bnd)} boundary edges at z {sorted(ends)}")
    check("drum shell has no non-manifold edges", not nonman, str(len(nonman)))
    n_steps = sum(1 for i in range(len(LAND_USE))
                  if LAND_USE[i][2] != LAND_USE[(i + 1) % len(LAND_USE)][2])
    check("every land-use step is closed by a riser",
          len({g for g in shell_m["groups"] if g.startswith("drum_riser")}) > 0
          and n_steps > 0, f"{n_steps} steps in LAND_USE")

    for cap_end in ("fore", "aft"):
        cv, ct, _cm = drum_end_cap(schema, profile, "green", cap_end)
        bnd, nonman = boundary_edges(cv, ct)
        r_out = ENDCAP_RIBS[0] * r_drum
        r_in = (schema["interior_topology"]["provisional_rings"][-1]["r_outer"]
                * r_drum)
        stray = [e for e in bnd
                 if not all(abs(math.hypot(x, y) - r_out) < 0.6
                            or abs(math.hypot(x, y) - r_in) < 0.6
                            for (x, y, _z) in e)]
        check(f"{cap_end} cap is closed except at rim and aperture",
              not stray, f"{len(stray)} stray of {len(bnd)} boundary edges")
        check(f"{cap_end} cap has no non-manifold edges", not nonman,
              str(len(nonman)))

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

    # --- the guideway portal ------------------------------------------------
    # Because the trusses are in the spoke planes, a tram car has to cross a
    # spoke, and until this session it crossed 6.43 m into solid structure.
    # The spoke is now pierced. What follows asserts the three things a render
    # cannot show about a hole in a structural member: that cutting it did not
    # open the solid, that nothing is left inside the volume it was cut for,
    # and that enough section survives to carry the load that still runs
    # through it.
    fr_i, to_i = drum_spoke_rings(schema, profile, "green")
    pv, pt, pm = spoke(schema, profile, "green", fr_i, to_i, 0.0)
    por = pm["portal"]
    check("the drum's spokes are pierced where the guideway crosses",
          por is not None)
    bnd, _nm = boundary_edges(pv, pt)
    check("cutting the portal did not open the spoke", not bnd,
          f"{len(bnd)} boundary edges")
    # Each pierced piece on its own, so a fault cannot hide inside the plain
    # run's edge count. A mitred ring is closed AND wound outward; a butted one
    # would be neither, and the butted version is the natural way to write it.
    for grp in ("spoke_portal", "spoke_portal_frame"):
        sub = [t for t, g in zip(pt, pm["groups"]) if g == grp]
        sb, sn = boundary_edges(pv, sub)
        check(f"{grp} is a closed solid",
              not sb and not sn and _signed_volume(pv, sub) > 0,
              f"{len(sb)} boundary, {len(sn)} non-manifold, "
              f"volume {_signed_volume(pv, sub):,.0f} m3")

    # Nothing may be inside the structure gauge. This is the assertion the
    # defect needed and did not have: it is about the whole volume, not about
    # one car at one phase, so no vehicle can be built to fit and later fall out
    # of fitting when something else moves.
    g = guideway_gauge(schema, profile, "green")
    fouls = [q for q in pm["section_rects"]
             if q[0] < g["half_width_m"] - 1e-9
             and -g["half_width_m"] < q[1] - 1e-9
             and q[2] < g["r_outer"] - 1e-9 and g["r_inner"] < q[3] - 1e-9]
    check("no spoke structure is inside the guideway's structure gauge",
          not fouls, f"{len(fouls)} rectangles foul the gauge")
    # And that the reported section is the section that was built. A clearance
    # test consumes these rectangles; if they described a different spoke from
    # the triangles, every test downstream would be measuring a fiction.
    a0 = math.radians(pm["angle_deg"])
    ca0, sa0 = math.cos(a0), math.sin(a0)
    astray = 0
    for x, y, _z in pv:
        rr, ll = x * ca0 + y * sa0, -x * sa0 + y * ca0
        if not any(l0 - 1e-6 <= ll <= l1 + 1e-6 and r0 - 1e-6 <= rr <= r1 + 1e-6
                   for l0, l1, r0, r1 in pm["section_rects"]):
            astray += 1
    check("the reported section covers every vertex the spoke actually has",
          astray == 0, f"{astray} of {len(pv)} vertices outside it")

    # Net section. The piers plus the frame jambs have to give back at least the
    # section the slot took out, or the spoke is a tension member with 70% of
    # itself missing at the one radius where all of the load passes.
    check("the pierced band keeps the section the slot removed",
          por["net_section_m2"] >= por["gross_section_m2"] - 1e-6,
          f"{por['net_section_m2']:.0f} m2 net against "
          f"{por['gross_section_m2']:.0f} m2 gross")
    check("the spoke widens where it is pierced",
          por["half_w_outer"] > por["half_thick"],
          f"half width {por['half_thick']:.1f} m -> "
          f"{por['half_w_outer']:.1f} m")

    # The truss is what the spoke is there to carry, so the bearing has to be
    # geometry rather than an assertion in a comment. The bottom chord is let
    # into the header: it must reach inboard past the header's inner face and
    # stand exactly the soffit relief proud of the opening, so the car meets the
    # chord's own running face inside the portal and not a step.
    r_bot = r_drum * TRUSS_RADIUS_FRAC
    check("the truss bottom chord is embedded in the portal header",
          por["r_band0"] < r_bot - TRUSS_CHORD_M / 2.0
          and por["half_w_frame"] > TRUSS_CHORD_M * 1.5,
          f"header from {por['r_band0']:.1f} m, chord inner face "
          f"{r_bot - TRUSS_CHORD_M / 2.0:.1f} m")
    check("the chord's running face stands proud of the soffit",
          abs((r_bot + TRUSS_CHORD_M / 2.0) - por["r0"]
              - GUIDEWAY_SOFFIT_RELIEF_M) < 1e-9,
          f"soffit {por['r0']:.3f} m, chord underside "
          f"{r_bot + TRUSS_CHORD_M / 2.0:.3f} m")
    # The light runs are the widest thing on the guideway, so they and not the
    # car are what sets the opening's width.
    check("the light runs pass through the opening",
          TRUSS_CHORD_M + 3.0 + TRUSS_LAMP_R_M < por["half_w"],
          f"lamp reaches {TRUSS_CHORD_M + 3.0 + TRUSS_LAMP_R_M} m against a "
          f"{por['half_w']} m opening")
    # A running gap, not a blind recess: the opening goes right through the
    # spoke's axial thickness or the car meets a wall halfway in.
    fz = [pv[i][2] for t, gg in zip(pt, pm["groups"])
          if gg == "spoke_portal_frame" for i in t]
    check("the opening runs right through the spoke in z",
          min(fz) <= pm["z_span"][0] + 1e-9
          and max(fz) >= pm["z_span"][1] - 1e-9,
          f"frame z {min(fz):.1f}-{max(fz):.1f} against spoke "
          f"{pm['z_span'][0]:.1f}-{pm['z_span'][1]:.1f}")

    # Only the drum has guideways, so only the drum's spokes are pierced.
    # Cutting the hole everywhere would weaken structure for a vehicle that does
    # not run there.
    o_from, o_to = drum_spoke_rings(schema, profile, other)
    ov, ot, om = spoke(schema, profile, other, o_from, o_to, 0.0)
    check(f"{other}: spokes carry no guideway and are not pierced",
          om["portal"] is None
          and not any(gg.startswith("spoke_portal") for gg in om["groups"]))

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
    if "--hull-fit" in sys.argv:
        _s, _p = load()
        _rows, _c = hull_fit(_s, _p)
        sys.exit(1 if _rows else 0)
    sys.exit(_selftest())
