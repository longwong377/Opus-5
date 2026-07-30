#!/usr/bin/env python3
"""The drum tram -- the car that runs slung beneath the guideway truss.

The guideway has existed since session 2u (`interior.guideway_truss`): three
Warren trusses at r = 236.6 m, bay 24 m, depth 16 m. Nothing ran on them. This
builds the vehicle.

The reference is unusually good for a vehicle in this project, and unusually
good in the one place vehicles are normally worst -- the inside:

  03-sector-blue/Babylon_5_2-22_34b.jpg  cars slung under the bottom chord,
      seen from above and behind, with a long run of truss bays in the same
      frame. This is the only frame that gives the car a SIZE.
  03-sector-blue/Babylon_5_2-22_33a.jpg  one car from below and ahead: white
      body, maroon window-band framing, dark underside with round ports, two
      white lights low on the nose.
  03-sector-blue/Babylon_5_2-22_35a.jpg  the car interior, shot forward past a
      seated passenger: raked multi-pane windscreen with red reveals, brick-red
      upholstered benches on light grey plinths, grey wall panels, vertical
      stanchions, yellow lit strips low in the plinth face, a small magenta-lit
      wall device, and the guideway truss receding outside.

HOW THE LENGTH WAS MEASURED, since guessing it was the whole risk. 34b looks
nearly along the drum axis, so the truss is foreshortened about 6:1 and a bay
near the camera covers three times the pixels of a bay half a kilometre away.
Measuring the car against "a bay" in raw pixels is therefore meaningless. The
frame was instead rectified projectively: the two chord lines were fitted
(y = 0.142x + 113 and y = 0.024x + 230), intersected to give the vanishing
point of the drum axis at (991.5, 253.8) px, and the image resampled in
w = 1/(x_vanish - x), which is affine in real distance along the truss. In that
frame the Warren zigzag is uniform across a 4:1 range of depth -- which is the
test that the rectification is right -- with a period of 78 +/- 3 px, i.e. two
bays. The near car measures 151 px between nose and tail: **3.9 +/- 0.25 bays**.
Its depth below the chord measures 0.65 of the truss depth, read as a fraction
of the local chord separation so it needs no scale at all.

Everything dimensional here is therefore expressed as a multiple of
`interior.TRUSS_BAY_M` or `interior.TRUSS_DEPTH_M`. Those are INV-012, an
invention, and if the truss is ever rescaled the tram rescales with it instead
of silently ceasing to fit. See INVENTIONS for what that measurement does and
does not establish.

WINDING. Two shells with opposite conventions in one file. The body is seen
from outside and its faces point away from the car's axis; the saloon is seen
from inside and its faces point at it. Both are measured, not asserted in a
comment -- `_facing_fraction` refuses geometry that would render black.

CLEARANCE. The car crosses a radial spoke every time round, because the
guideways are in the spoke planes and nothing else could hold a 2.6 km truss up.
The spoke is cut open for it; the gauge, the portal and the clearances they buy
are INV-050, and `truss_clearance`/`spoke_clearance` are what keep the cut open.
Both are SURFACE tests, and the header above them says why a vertex loop is not.
The windscreen members' standoff is INV-051.

No pseudo-randomness anywhere, so regeneration is byte-identical by
construction rather than by seeding discipline.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it


# ---------------------------------------------------------------------------
# Dimensions. Measured ones carry the frame they came from; the rest are
# extrapolation and say so.
# ---------------------------------------------------------------------------

# Measured off 34b by projective rectification: 3.9 +/- 0.25 bays. Built at 4.
CAR_BAYS = 4.0
# Measured off 34b as a fraction of the local chord separation: 0.65 of the
# truss depth from the underside of the bottom chord to the car's underside.
CAR_DEPTH_FRAC = 0.65

# Not measurable. No frame shows the car end-on or from directly above, and
# 35a's interior is cropped on both sides. Set so no part of the car ever
# passes under a light run -- the lamps sit at lateral +/-5.2 m with a 1.5 m
# radius, so anything inside +/-3.7 m never shadows the habitat's lighting.
CAR_WIDTH_M = 7.2

# The suspension is non-contact. Nothing mechanical is visible in 33a or 34b
# between the chord and the car, and mechanical running gear has nowhere to go:
# the truss's centre gap is crossed by a transverse tie every second bay and
# its outboard flanks are occupied by the light runs. A magnetic gap under the
# two bottom chords is the only reading that does not require inventing a hole
# in the truss. See INVENTIONS.
SUSPENSION_GAP_M = 0.35
SHOE_DEPTH_M = 0.50           # the dorsal plate that rides under each chord
SHOE_WIDTH_M = 2.0            # narrower than the chord it runs under

NOSE_M = 6.0                  # length over which the section tapers forward
TAIL_M = 5.0
RAKE_M = 1.1                  # windscreen top set back from its sill: 24 deg

WALL_T = 0.22                 # exterior skin to saloon face
WINDOW_PITCH_M = 4.0
SEAT_PITCH_M = 0.62           # one seated person, cushion plus its gap

# Clearance the car must keep from every truss member. A door interpenetrating
# a portal frame is a mistake this project has already made once; this is the
# number the self-test enforces so it cannot happen a second time in a place
# nobody is looking. INV-050.
TRUSS_CLEARANCE_M = 0.30


def car_length():
    return CAR_BAYS * it.TRUSS_BAY_M


def levels():
    """The car's cross-section as (name, half_width, y) from underside to roof.

    y is measured from the bottom chord's CENTRELINE and increases inboard --
    that is, toward the spin axis -- so every part of the car has y < 0. The
    self-test asserts that, because a car built with the sign wrong hangs above
    the guideway instead of below it and still renders perfectly.
    """
    d = it.TRUSS_DEPTH_M
    chord_half = it.TRUSS_CHORD_M / 2.0
    y_roof = -(chord_half + SUSPENSION_GAP_M + SHOE_DEPTH_M)
    y_under = -(chord_half + CAR_DEPTH_FRAC * d)
    body = y_roof - y_under

    w = CAR_WIDTH_M / 2.0
    # Proportions within the body height are read off 33a: a maroon roof cap,
    # then the window band, then a tall white lower body, then the dark valance
    # which is visibly narrower than the body above it.
    return (
        ("under", w * 0.53, y_under),
        ("waist", w * 0.92, y_under + 0.29 * body),
        ("floor", w * 0.99, y_under + 0.58 * body),
        ("sill",  w * 1.00, y_under + 0.69 * body),
        ("head",  w * 1.00, y_under + 0.81 * body),
        ("cant",  w * 0.96, y_under + 0.88 * body),
        ("roof",  w * 0.83, y_roof),
    )


def level_y(name):
    for n, _w, y in levels():
        if n == name:
            return y
    raise KeyError(name)


def level_w(name):
    for n, w, _y in levels():
        if n == name:
            return w
    raise KeyError(name)


# ---------------------------------------------------------------------------
# Primitives. Local frame: +x starboard, +y inboard (toward the spin axis, so
# "up" for a passenger), +z forward along the guideway.
# ---------------------------------------------------------------------------

def _box(verts, tris, corners):
    """Axis-order box from eight corners, every face wound outward."""
    b = len(verts)
    verts.extend(corners)
    for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        tris.append((b + a, b + d, b + c))
        tris.append((b + a, b + e, b + d))


def _slab(verts, tris, x0, x1, y0, y1, z0, z1):
    _box(verts, tris, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])


def _quad(verts, tris, p0, p1, p2, p3):
    """One planar quad, normal by the right-hand rule on p0->p1->p2."""
    b = len(verts)
    verts.extend([p0, p1, p2, p3])
    tris.append((b, b + 1, b + 2))
    tris.append((b, b + 2, b + 3))


def _loft(verts, tris, rings, inward=False, edge_groups=None, skip=()):
    """Tube through a list of equal-length rings ordered by increasing z.

    Rings are listed counter-clockwise in the xy-plane, which makes the side
    faces point away from the axis. `inward` reverses that for the saloon,
    which is the one surface here seen from its concave side.

    `edge_groups` names the material of each longitudinal strip. The livery
    break in 33a runs along the section, not along the car, so the body cannot
    be one group: white above the waist, near-black below it, maroon over the
    cant. Returned per triangle so the caller does not have to recount.
    """
    n = len(rings[0])
    out = [] if edge_groups else None
    for a, b in zip(rings, rings[1:]):
        ba, bb = len(verts), len(verts) + n
        verts.extend(a)
        verts.extend(b)
        for k in range(n):
            if k in skip:
                continue
            k2 = (k + 1) % n
            t1 = (ba + k, ba + k2, bb + k2)
            t2 = (ba + k, bb + k2, bb + k)
            if inward:
                t1, t2 = t1[::-1], t2[::-1]
            tris.append(t1)
            tris.append(t2)
            if out is not None:
                out.extend([edge_groups[k]] * 2)
    return out


def _facing_fraction(verts, tris, axis_x=0.0, inward=False, mid=None):
    """Fraction of faces pointing away from (or toward) the car's long axis.

    The exterior and the saloon are the same shape with opposite conventions,
    and getting either backwards renders black rather than erroring -- exactly
    the failure `interior._inward_fraction` exists to catch on the drum shell.
    Measured against the axis line x = axis_x, y = `mid`, so it is meaningful
    for a long tube rather than for a sphere. `mid` has to be the axis of the
    surface being measured, not of the car: the saloon's axis sits well above
    the body's, and using the body's marked the cabin floor as inside out
    because its normal points up and away from a datum below it.
    """
    if mid is None:
        ys = [y for _n, _w, y in levels()]
        mid = (min(ys) + max(ys)) / 2.0
    good = oriented = 0
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = tuple(p1[i] - p0[i] for i in range(3))
        v = tuple(p2[i] - p0[i] for i in range(3))
        n = (u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0])
        cx = (p0[0] + p1[0] + p2[0]) / 3.0 - axis_x
        cy = (p0[1] + p1[1] + p2[1]) / 3.0 - mid
        d = n[0] * cx + n[1] * cy
        nl = math.sqrt(sum(k * k for k in n)) * math.hypot(cx, cy)
        # An end cap's normal is along the car, so it says nothing about which
        # way the tube is turned inside out. Counting those as passes let a
        # fully reversed shell still score 7%, which is not a test.
        if nl < 1e-12 or abs(d) / nl < 0.05:
            continue
        oriented += 1
        if (d < 0) == inward:
            good += 1
    return good / max(1, oriented)


# ---------------------------------------------------------------------------
# The body shell
# ---------------------------------------------------------------------------

def _stations():
    """(z, width_scale, drop, tuck, rake) along the car, aft to fore.

    `drop` lowers the roof, `tuck` lifts the valance, `rake` sets the top of
    the section back from its sill. All three are zero over the straight body
    and only the nose gets rake, which is what makes the windscreen lean.
    """
    L = car_length()
    z0, z1 = -L / 2.0, L / 2.0
    s = [
        (z0,                0.78, 0.55, 2.0, 0.0),
        (z0 + 1.2,          0.89, 0.28, 1.1, 0.0),
        (z0 + 3.0,          0.97, 0.08, 0.35, 0.0),
        (z0 + TAIL_M,       1.00, 0.00, 0.00, 0.0),
        (z1 - NOSE_M,       1.00, 0.00, 0.00, 0.0),
        (z1 - 4.0,          0.98, 0.08, 0.50, 0.08),
        (z1 - 2.4,          0.94, 0.24, 1.30, 0.30),
        (z1 - 1.1,          0.89, 0.42, 2.20, 0.65),
        (z1,                0.85, 0.60, 3.00, RAKE_M),
    ]
    return s


def _weights():
    """Per-level weights for drop, tuck and rake. Derived from the y levels so
    a change to the section proportions cannot leave them stale."""
    y_roof, y_head = level_y("roof"), level_y("head")
    y_floor, y_under, y_sill = level_y("floor"), level_y("under"), level_y("sill")
    out = []
    for name, w, y in levels():
        top = min(1.0, max(0.0, (y - y_head) / (y_roof - y_head)))
        bot = min(1.0, max(0.0, (y_floor - y) / (y_floor - y_under)))
        rake = min(1.0, max(0.0, (y - y_sill) / (y_roof - y_sill)))
        out.append((name, w, y, top, bot, rake))
    return out


def _ring(z, scale, drop, tuck, rake, inset=0.0, only=None):
    """One cross-section ring, counter-clockwise in xy."""
    right, left = [], []
    for name, w, y, wtop, wbot, wrake in _weights():
        if only and name not in only:
            continue
        yy = y - drop * wtop + tuck * wbot
        if inset:
            yy += inset * (wtop - wbot)
        ww = max(0.05, w * scale - inset)
        zz = z - rake * wrake
        right.append((ww, yy, zz))
        left.append((-ww, yy, zz))
    return right + left[::-1]


def _cap(verts, tris, ring, front, aperture=(), rung_groups=None):
    """Cap a ring by laddering its right and left halves together.

    Emitted level by level rather than as a fan so a window aperture can be a
    missing rung. The front cap IS the windscreen: putting a separate screen
    inside it would mean two surfaces claiming the same plane, and the interior
    camera would see the wrong one.
    """
    n = len(ring) // 2
    right = ring[:n]
    left = ring[n:][::-1]
    out = [] if rung_groups else None
    for j in range(n - 1):
        if j in aperture:
            continue
        p = (right[j], right[j + 1], left[j + 1], left[j])
        if front:
            _quad(verts, tris, *p)
        else:
            _quad(verts, tris, p[3], p[2], p[1], p[0])
        if out is not None:
            out.extend([rung_groups[j]] * 2)
    return out


def car_shell(glazed=True):
    """The exterior body: hull, window band, livery break, nose, running gear.

    Returns (verts, tris, groups) in the car's local frame.
    """
    verts, tris, groups = [], [], []

    def emit(fn, group):
        before = len(tris)
        fn()
        groups.extend([group] * (len(tris) - before))

    st = _stations()
    rings = [_ring(*s) for s in st]

    names = [n for n, _w, _y in levels()]
    sill_i = names.index("sill")
    nl = len(names)
    # Livery, read straight off 33a: dark valance below the waist, white body,
    # maroon behind the window band, maroon cap above the cant.
    rung = []
    for j in range(nl - 1):
        lo = names[j]
        if lo in ("under",):
            rung.append("tram_valance")
        elif lo == "sill":
            rung.append("tram_recess")
        elif lo == "cant":
            rung.append("tram_roof")
        else:
            rung.append("tram_body")
    # A ring runs up the starboard side, across the roof, down the port side
    # and back across the underside, so the edge list is the rung list, the
    # roof, the rung list reversed, and the underside.
    edge = rung + ["tram_roof"] + rung[::-1] + ["tram_valance"]

    # Unglazed the window band is an actual slot, so a passenger sees the drum
    # through it -- 35a shows the fields through the side glass, and a render
    # that puts a wall there is testing a different vehicle. The preview
    # rasteriser has no transparency, so "glass" and "hole" have to be two
    # builds rather than one material.
    # A ring is the levels up the starboard side then the same levels back
    # down the port side, so the port counterpart of edge k is 2*nl - 2 - k.
    win_edges = (sill_i, 2 * nl - 2 - sill_i)
    groups.extend(_loft(verts, tris, rings, edge_groups=edge,
                        skip=() if glazed else win_edges))
    # The windscreen is TALLER than the side band: it runs from the sill right
    # up to the cant rail. 35a's panes are portrait trapezoids reaching the
    # ceiling, and an aperture only as tall as a side window is a letterbox
    # that reads nothing like the frame.
    screen = (sill_i, sill_i + 1)      # sill -> head -> cant
    groups.extend(_cap(verts, tris, rings[-1], True, aperture=screen,
                       rung_groups=rung))
    groups.extend(_cap(verts, tris, rings[0], False, rung_groups=rung))

    if glazed:
        emit(lambda: _cap(verts, tris, rings[-1], True,
                          aperture=tuple(i for i in range(len(names) - 1)
                                         if i not in screen)), "tram_glass")

    y_sill, y_head = level_y("sill"), level_y("head")
    w_sill = level_w("sill")
    L = car_length()
    z_win0 = -L / 2.0 + TAIL_M + 1.0
    z_win1 = L / 2.0 - NOSE_M - 0.5
    nbay = max(1, int((z_win1 - z_win0) / WINDOW_PITCH_M))
    pitch = (z_win1 - z_win0) / nbay

    for sgn in (1.0, -1.0):
        # Head and sill rails run the whole band as single members. Framing
        # each pane individually quadrupled the count for joints that are
        # inside the solid anyway.
        for y in (y_head, y_sill):
            emit(lambda y=y: _slab(
                verts, tris, sgn * (w_sill - 0.02), sgn * (w_sill + 0.06),
                y - 0.16, y + 0.16, z_win0 - 0.35, z_win1 + 0.35),
                "tram_band")
        xg = sgn * (w_sill - 0.09)
        for i in range(nbay):
            za = z_win0 + pitch * i
            zb = za + pitch
            if glazed:
                corners = [(xg, y_sill + 0.16, za + 0.16),
                           (xg, y_sill + 0.16, zb - 0.16),
                           (xg, y_head - 0.16, zb - 0.16),
                           (xg, y_head - 0.16, za + 0.16)]
                if sgn < 0:
                    corners.reverse()
                emit(lambda c=corners: _quad(verts, tris, *c), "tram_glass")
            emit(lambda zb=zb: _slab(
                verts, tris, sgn * (w_sill - 0.02), sgn * (w_sill + 0.06),
                y_sill + 0.10, y_head - 0.10, zb - 0.18, zb + 0.18),
                "tram_band")

    # Roof cap. In 33a the strip above the window band reads distinctly darker
    # than the body, and it is what separates the car from the truss shadow.
    y_cant, y_roof = level_y("cant"), level_y("roof")
    w_cant = level_w("cant")
    emit(lambda: _slab(verts, tris, -w_cant * 0.99, w_cant * 0.99,
                       y_cant, y_roof + 0.02,
                       -L / 2.0 + TAIL_M * 0.5, L / 2.0 - NOSE_M * 0.5),
         "tram_cap")

    # The two dorsal shoe plates. These ride under the bottom chords at the
    # suspension gap and are the only part of the car that comes near the
    # truss; the clearance test is aimed squarely at them.
    lat = it.TRUSS_CHORD_M
    y_shoe_top = -(it.TRUSS_CHORD_M / 2.0 + SUSPENSION_GAP_M)
    for sgn in (1.0, -1.0):
        emit(lambda sgn=sgn: _slab(
            verts, tris, sgn * (lat - SHOE_WIDTH_M / 2.0),
            sgn * (lat + SHOE_WIDTH_M / 2.0),
            y_shoe_top - SHOE_DEPTH_M, y_shoe_top,
            -L / 2.0 + TAIL_M, L / 2.0 - NOSE_M), "tram_shoe")

    # Two white lights low on the nose -- 33a, the brightest thing on the car.
    y_lamp = level_y("floor") - 0.25
    for sgn in (1.0, -1.0):
        emit(lambda sgn=sgn: _slab(
            verts, tris, sgn * 0.55, sgn * 1.55, y_lamp - 0.30, y_lamp + 0.30,
            L / 2.0 - 0.55, L / 2.0 - 0.20), "tram_headlight")

    # Round ports along the dark valance, again 33a. Cheap, and they are what
    # stops the underside reading as a painted shadow at distance.
    y_v = (level_y("waist") + level_y("under")) / 2.0
    w_v = (level_w("waist") + level_w("under")) / 2.0
    nport = int((L - TAIL_M - NOSE_M) / 6.0)
    for i in range(nport):
        z = -L / 2.0 + TAIL_M + 3.0 + i * 6.0
        for sgn in (1.0, -1.0):
            emit(lambda sgn=sgn, z=z: _slab(
                verts, tris, sgn * (w_v - 0.04), sgn * (w_v + 0.10),
                y_v - 0.45, y_v + 0.45, z - 0.45, z + 0.45), "tram_port")

    # Measured on the hull loft and its caps only. Applied bodily to the whole
    # car it would fail on every fitting: a mullion is a solid box standing on
    # the surface and half its faces point inward by design, which is correct
    # and invisible. The surface that must not be inside out is the one the
    # fittings are stuck to.
    hull = [t for t, g in zip(tris, groups)
            if g in ("tram_body", "tram_valance", "tram_roof",
                     "tram_recess")]
    frac = _facing_fraction(verts, hull)
    if frac < 0.99:
        raise AssertionError(
            f"car_shell: {(1 - frac) * 100:.1f}% of hull faces point at the "
            "car's own axis; they will be backface-culled from outside")

    return verts, tris, groups


# ---------------------------------------------------------------------------
# The saloon
# ---------------------------------------------------------------------------

def _saloon_span():
    L = car_length()
    return (-L / 2.0 + TAIL_M + 0.4, L / 2.0)


def car_saloon(glazed=True):
    """The interior of 35a: floor, benches, stanchions, panels, lit strips.

    Built from the same station list as the shell, inset by the wall thickness,
    so the saloon narrows into the nose exactly as the body does and the
    windscreen sits in the body's own front plane rather than in a second one
    invented for it.
    """
    verts, tris, groups = [], [], []

    def emit(fn, group):
        before = len(tris)
        fn()
        groups.extend([group] * (len(tris) - before))

    y_floor, y_cant = level_y("floor"), level_y("cant")
    y_sill, y_head = level_y("sill"), level_y("head")
    z_rear, z_fore = _saloon_span()

    st = [s for s in _stations() if z_rear <= s[0] <= z_fore]
    if st[0][0] > z_rear + 1e-6:
        st.insert(0, (z_rear, 1.0, 0.0, 0.0, 0.0))
    rings = [_ring(*s, inset=WALL_T, only=("floor", "sill", "head", "cant"))
             for s in st]
    names = ("floor", "sill", "head", "cant")
    sill_i = names.index("sill")
    n_in = len(names)
    edge_in = (["tram_in_wall", "tram_in_window", "tram_in_wall"]
               + ["tram_in_ceiling"]
               + ["tram_in_wall", "tram_in_window", "tram_in_wall"]
               + ["tram_in_floor"])
    win_in = (sill_i, 2 * n_in - 1 - 1 - sill_i)
    groups.extend(_loft(verts, tris, rings, inward=True, edge_groups=edge_in,
                        skip=() if glazed else win_in))
    screen_in = (sill_i, sill_i + 1)
    emit(lambda: _cap(verts, tris, rings[-1], False, aperture=screen_in),
         "tram_in_wall")
    emit(lambda: _cap(verts, tris, rings[0], True), "tram_in_wall")
    if glazed:
        emit(lambda: _cap(verts, tris, rings[-1], False,
                          aperture=(0,)), "tram_glass")

    shell_only = _facing_fraction(verts, tris, inward=True,
                                  mid=(y_floor + y_cant) / 2.0)
    if shell_only < 0.99:
        raise AssertionError(
            f"car_saloon: {(1 - shell_only) * 100:.1f}% of shell faces point "
            "away from the cabin; a passenger sees straight through them")

    w_in = level_w("sill") - WALL_T

    # --- the side benches, which are the wall 35a is looking at --------------
    # The long bench's cushions are CONTINUOUS -- one back pad and one seat pad
    # per module, with no divisions. That is what the frame shows, and it is
    # worth being literal about because the first pass built one cushion per
    # seated person and spent 6,400 triangles, two thirds of the whole car, on
    # divisions that are not there. The individual square cushions in 35a are
    # the forward group, below, not the bench.
    seat_h = 0.45
    back_h = 1.02
    depth = 0.64
    bench_m = 6.0                  # module, broken by a door bay between each
    gap_m = 1.4
    z_b0, z_b1 = z_rear + 1.2, z_fore - NOSE_M - 0.3
    n_mod = max(1, int((z_b1 - z_b0 + gap_m) / (bench_m + gap_m)))
    for sgn in (1.0, -1.0):
        x_wall = sgn * w_in
        x_front = sgn * (w_in - depth)
        lo, hi = min(x_wall, x_front), max(x_wall, x_front)
        xb0 = min(x_wall, x_wall - sgn * 0.16)
        xb1 = max(x_wall, x_wall - sgn * 0.16)
        for i in range(n_mod):
            zb = z_b1 - i * (bench_m + gap_m)
            za = zb - bench_m
            emit(lambda za=za, zb=zb: _slab(
                verts, tris, lo, hi, y_floor, y_floor + seat_h - 0.10,
                za, zb), "tram_in_plinth")
            emit(lambda za=za, zb=zb: _slab(
                verts, tris, lo, hi,
                y_floor + seat_h - 0.10, y_floor + seat_h,
                za + 0.04, zb - 0.04), "tram_in_seat")
            emit(lambda za=za, zb=zb: _slab(
                verts, tris, xb0, xb1,
                y_floor + seat_h + 0.02, y_floor + back_h,
                za + 0.04, zb - 0.04), "tram_in_seat")

        # Yellow lit strips in a grey bezel, low in the plinth face. In 35a
        # they are the only light source below waist height and they are what
        # makes the interior read as a vehicle rather than as a room. Three to
        # a bench module, so none of them floats in a door bay.
        x_face = x_front
        xf0 = min(x_face, x_face - sgn * 0.06)
        xf1 = max(x_face, x_face - sgn * 0.06)
        lits = [z_b1 - i * (bench_m + gap_m) - 5.0 + k * 2.0
                for i in range(n_mod) for k in range(3)]
        for zc in lits:
            xb0, xb1 = xf0, xf1
            emit(lambda xb0=xb0, xb1=xb1, zc=zc: _slab(
                verts, tris, xb0, xb1, y_floor + 0.10, y_floor + 0.30,
                zc - 0.62, zc + 0.62), "tram_in_bezel")
            # The lit face has to look at the AISLE, not at the wall behind
            # the bench. Both were pointing outward on the first build, so a
            # backface-culled renderer showed no lit strips at all in a car
            # whose most distinctive interior feature is lit strips.
            xs = x_face - sgn * 0.07
            corners = [(xs, y_floor + 0.13, zc - 0.55),
                       (xs, y_floor + 0.27, zc - 0.55),
                       (xs, y_floor + 0.27, zc + 0.55),
                       (xs, y_floor + 0.13, zc + 0.55)]
            if sgn > 0:
                corners.reverse()
            emit(lambda c=corners: _quad(verts, tris, *c), "tram_in_strip")

        # Dark red skirt at floor level, under the plinth -- 35a again.
        emit(lambda lo=lo, hi=hi: _slab(
            verts, tris, lo, hi, y_floor + 0.005, y_floor + 0.11,
            z_b0 - 0.1, z_b1 + 0.1), "tram_in_skirt")

    # --- side window reveals ------------------------------------------------
    # 35a frames every pane in maroon and it is the most recognisable thing in
    # the interior after the seats. Two continuous members per side rather than
    # a frame per pane, for the same reason the exterior rails are continuous.
    for sgn in (1.0, -1.0):
        xr0 = min(sgn * w_in, sgn * (w_in - 0.10))
        xr1 = max(sgn * w_in, sgn * (w_in - 0.10))
        for y in (y_sill, y_head):
            emit(lambda xr0=xr0, xr1=xr1, y=y: _slab(
                verts, tris, xr0, xr1, y - 0.09, y + 0.09,
                z_rear + 0.6, z_fore - NOSE_M - 0.2), "tram_in_reveal")

    # --- forward seat group -------------------------------------------------
    # 35a shows individual forward-facing seats round the front corner, not the
    # longitudinal bench, and they are on the far side of the aisle from the
    # camera's own seat. Square cushions with a visible gap, unlike the bench.
    z_fs = z_fore - NOSE_M + 1.0
    half = SEAT_PITCH_M / 2.0 - 0.03
    for k in range(3):
        x = -w_in + 0.62 + k * (SEAT_PITCH_M + 0.10)
        if x > -0.4:
            break
        emit(lambda x=x: _slab(verts, tris, x - half - 0.01, x + half + 0.01,
                               y_floor, y_floor + seat_h - 0.10,
                               z_fs - 0.62, z_fs), "tram_in_plinth")
        emit(lambda x=x: _slab(verts, tris, x - half, x + half,
                               y_floor + seat_h - 0.10, y_floor + seat_h,
                               z_fs - 0.60, z_fs - 0.02), "tram_in_seat")
        emit(lambda x=x: _slab(verts, tris, x - half, x + half,
                               y_floor + seat_h, y_floor + back_h,
                               z_fs - 0.74, z_fs - 0.60), "tram_in_seat")

    # --- stanchions ---------------------------------------------------------
    # Floor to ceiling, on the aisle edge of each bench. In 35a two of them
    # cross the frame and they are most of what places the camera inside a
    # vehicle rather than looking at a set.
    post_r = 0.055
    z_p0 = z_rear + 1.6
    n_post = int((z_b1 - z_p0) / 3.2) + 1
    for sgn in (1.0, -1.0):
        xp = sgn * (w_in - depth - 0.22)
        for i in range(n_post):
            zp = z_p0 + i * 3.2
            emit(lambda xp=xp, zp=zp: _prism8(
                verts, tris, xp, zp, post_r, y_floor, y_cant), "tram_in_post")

    # --- the magenta-lit wall device ---------------------------------------
    # Small, and included because it is the one piece of equipment 35a shows:
    # a dark unit on the wall above the bench back with a magenta readout and a
    # blank screen beneath it.
    zd = z_b0 + 6.0
    if zd < z_b1:
        emit(lambda: _slab(verts, tris, w_in - 0.30, w_in - 0.14,
                           y_floor + back_h + 0.08, y_floor + back_h + 0.62,
                           zd - 0.22, zd + 0.22), "tram_in_device")
        emit(lambda: _quad(
            verts, tris,
            (w_in - 0.31, y_floor + back_h + 0.40, zd - 0.16),
            (w_in - 0.31, y_floor + back_h + 0.56, zd - 0.16),
            (w_in - 0.31, y_floor + back_h + 0.56, zd + 0.16),
            (w_in - 0.31, y_floor + back_h + 0.40, zd + 0.16)),
            "tram_in_readout")

    # --- windscreen mullions ------------------------------------------------
    # The screen is the body's front cap. Its divisions are separate members
    # standing proud on the inside, which is how they read in 35a: grey posts
    # with a red reveal either side of each pane.
    #
    # STANDING PROUD ON THE INSIDE, and it did not. `_strut` centres its section
    # on the line through its two endpoints, and those endpoints lie IN the
    # screen, so half of every mullion and reveal was in front of it -- 74 mm of
    # mullion and 100 mm of reveal poking out through the nose of the car, at
    # the one place a car is seen close up from outside (33a). Found by
    # replacing a vacuous triangle-count check with a containment one. Each
    # member is now slid back until it is wholly behind the screen plane.
    fr = rings[-1]
    n = len(fr) // 2
    right, left = fr[:n], fr[n:][::-1]
    a_lo_r, a_hi_r = right[sill_i], right[sill_i + 2]
    a_lo_l, a_hi_l = left[sill_i], left[sill_i + 2]
    # The screen's outward normal, taken from the aperture's own two rails so a
    # change to RAKE_M carries the members with it. The screen leans back at the
    # top, so outward is forward and inboard.
    dy, dz = a_hi_r[1] - a_lo_r[1], a_hi_r[2] - a_lo_r[2]
    ln = math.hypot(dy, dz) or 1.0
    nrm = (0.0, -dz / ln, dy / ln)
    if nrm[2] < 0.0:
        nrm = (0.0, -nrm[1], -nrm[2])

    z_nose = car_length() / 2.0

    def behind(fn, group, relief=0.01):
        """Emit a member, then slide it back until it clears the screen.

        Measured on the member's own vertices rather than predicted from its
        section: `_strut` orients its depth axis from the endpoints, so how much
        of it lands in front of the screen depends on which way the member runs,
        and a mullion and a sill rail do not get the same answer.

        Two constraints, because the screen is not the whole nose. The raked
        plane only exists between the sill and the cant; below the sill the cap
        is flat at z_nose, and the sill reveal is offset 0.11 m below the sill,
        which is exactly where the extrapolated plane runs forward of the car.
        """
        b = len(verts)
        emit(fn, group)
        over = max(sum((verts[i][k] - a_lo_r[k]) * nrm[k] for k in range(3))
                   for i in range(b, len(verts)))
        d = over + relief
        if d > 0.0:
            for i in range(b, len(verts)):
                verts[i] = tuple(verts[i][k] - d * nrm[k] for k in range(3))
        dz_ = max(verts[i][2] for i in range(b, len(verts))) - z_nose + relief
        if dz_ > 0.0:
            for i in range(b, len(verts)):
                verts[i] = (verts[i][0], verts[i][1], verts[i][2] - dz_)

    for i in range(1, 5):
        t = i / 5.0
        p_lo = tuple(a_lo_l[j] + (a_lo_r[j] - a_lo_l[j]) * t for j in range(3))
        p_hi = tuple(a_hi_l[j] + (a_hi_r[j] - a_hi_l[j]) * t for j in range(3))
        behind(lambda p_lo=p_lo, p_hi=p_hi: _strut(
            verts, tris, p_lo, p_hi, 0.10, 0.16), "tram_in_mullion")
    # Sill and head reveals, in the maroon the reference is emphatic about.
    # Offset clear of the aperture rather than centred on its edge: centred,
    # they ate 0.10 m of the opening at the sill, which is more than a seated
    # passenger's eye clears it by, and the view forward closed up.
    for (lo, hi), dy in (((a_lo_l, a_lo_r), -0.11), ((a_hi_l, a_hi_r), 0.11)):
        lo = (lo[0], lo[1] + dy, lo[2])
        hi = (hi[0], hi[1] + dy, hi[2])
        behind(lambda lo=lo, hi=hi: _strut(verts, tris, lo, hi, 0.13, 0.20),
               "tram_in_reveal")

    return verts, tris, groups


def _prism8(verts, tris, x, z, r, y0, y1):
    """Vertical octagonal post. Cheaper than a cylinder and, at 55 mm radius,
    indistinguishable at any distance a passenger sees one from."""
    ring0, ring1 = [], []
    for k in range(8):
        th = 2 * math.pi * k / 8 + math.pi / 8
        ring0.append((x + r * math.cos(th), y0, z + r * math.sin(th)))
        ring1.append((x + r * math.cos(th), y1, z + r * math.sin(th)))
    b = len(verts)
    verts.extend(ring0)
    verts.extend(ring1)
    for k in range(8):
        k2 = (k + 1) % 8
        tris.append((b + k, b + 8 + k2, b + k2))
        tris.append((b + k, b + 8 + k, b + 8 + k2))


def _strut(verts, tris, p0, p1, w, h):
    """Box section between two points, section w across by h deep."""
    ax = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = [c / ln for c in ax]
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


def tram_car(interior=True, glazed=True):
    """One complete car in its local frame.

    `interior=False` is the streaming form: three guideways of cars are always
    in frame in the drum and only the one you are riding needs a saloon.
    """
    verts, tris, groups = car_shell(glazed=glazed)
    if interior:
        v, t, g = car_saloon(glazed=glazed)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(g)
    return verts, tris, {
        "length_m": round(car_length(), 2),
        "width_m": round(CAR_WIDTH_M, 2),
        "depth_m": round(level_y("roof") - level_y("under"), 2),
        "bays": CAR_BAYS,
        "interior": interior,
        "triangles": len(tris),
        "groups": groups,
    }


# ---------------------------------------------------------------------------
# Clearance against the truss
# ---------------------------------------------------------------------------

def truss_envelope():
    """Axis-aligned boxes in (x, y) that every truss member lives inside.

    Derived from `interior`'s own constants rather than copied, so a change to
    the truss cannot leave the clearance test measuring against a truss that no
    longer exists. Boxes are infinite in z: the diagonals sweep the full depth
    somewhere in every bay, so treating them as z-independent is the
    conservative reading and the only one a static test can make.
    """
    c = it.TRUSS_CHORD_M / 2.0
    lat = it.TRUSS_CHORD_M
    d = it.TRUSS_DEPTH_M
    # A diagonal is a square section on an arbitrary axis, so its projected
    # half-width is up to w/sqrt(2) rather than w/2.
    wdiag = it.TRUSS_WEB_M / math.sqrt(2.0)
    lamp_lat = it.TRUSS_CHORD_M + 3.0
    r = it.TRUSS_LAMP_R_M
    boxes = []
    for s in (1.0, -1.0):
        boxes.append((min(s * (lat - c), s * (lat + c)),
                      max(s * (lat - c), s * (lat + c)), -c, c))
        boxes.append((min(s * (lat - c), s * (lat + c)),
                      max(s * (lat - c), s * (lat + c)), d - c, d + c))
        boxes.append((min(s * (lat - wdiag), s * (lat + wdiag)),
                      max(s * (lat - wdiag), s * (lat + wdiag)),
                      -wdiag, d + wdiag))
        boxes.append((min(s * (lamp_lat - r), s * (lamp_lat + r)),
                      max(s * (lamp_lat - r), s * (lamp_lat + r)), -r, r))
    boxes.append((-(lat + wdiag), lat + wdiag, -wdiag, wdiag))   # transverse ties
    return boxes


# ---------------------------------------------------------------------------
# SURFACE separation, and why a vertex loop is not it.
#
# Both clearance tests below used to walk the car's VERTICES and measure each
# one against the obstacle rectangles. That is the trap this repository keeps
# falling into -- three other functions here already carry a comment about it --
# and it is worth writing down exactly why, because the arithmetic looks right:
#
#   * a rectangle that lies WHOLLY INSIDE the car contains no car vertex, so a
#     vertex loop reports the distance to the nearest vertex, which is a
#     comfortable positive number, while a beam runs the length of the saloon;
#   * two rectangles can cross like a plus sign with no corner of either inside
#     the other, so vertex-in-box misses that too.
#
# Neither is hypothetical. `interior.spoke()`'s own docstring says the truss's
# bottom chord and light runs are "let INTO the header"; the day somebody adds a
# tie across the portal to carry them it lands inside the car's footprint, and
# the vertex loop then reports 0.500 m -- the SAME number it reports with no tie
# there at all, because the tie touches no vertex. Measured, not supposed:
# `_selftest` builds that case and runs both metrics on it.
#
# What replaces it: the car is projected TRIANGLE by triangle into the plane the
# sweep lives in, and each projected triangle is measured against each obstacle
# rectangle exactly -- separating-axis for overlap, edge-pair distance for the
# gap. The projection of a closed solid is the union of the projections of its
# boundary triangles, so this is the real surface, not a point cloud sampled
# from it.
# ---------------------------------------------------------------------------

def _tri_rect_gap(tri, rect):
    """Exact signed separation between a 2-D triangle and an axis-aligned box.

    Positive is a gap; negative is the penetration depth, i.e. the shortest
    translation that would separate them. Both shapes are convex, so the
    separating-axis theorem over the five candidate axes -- the rectangle's two
    and the triangle's three -- is complete: no separating axis means they
    really do overlap.
    """
    l0, l1, r0, r1 = rect
    quad = ((l0, r0), (l1, r0), (l1, r1), (l0, r1))

    # Overlap test and, if they overlap, the minimum translation distance.
    depth = float("inf")
    for poly in (tri, quad):
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            ax, ay = y0 - y1, x1 - x0
            ln = math.hypot(ax, ay)
            if ln < 1e-12:
                continue
            ax, ay = ax / ln, ay / ln
            ta = [ax * p[0] + ay * p[1] for p in tri]
            qa = [ax * p[0] + ay * p[1] for p in quad]
            # Separated on this axis when one interval starts past the other's
            # end; otherwise they overlap by however much they share.
            sep = max(min(ta) - max(qa), min(qa) - max(ta))
            if sep > 0.0:
                depth = 0.0             # separated on this axis -> disjoint
                break
            depth = min(depth, -sep)
        if depth == 0.0:
            break
    if depth > 0.0:
        return -depth

    # Disjoint and convex, so the closest pair of points lies on the boundaries
    # and it is enough to walk the 3 x 4 edge pairs.
    best = float("inf")
    for i in range(3):
        p, q = tri[i], tri[(i + 1) % 3]
        for j in range(4):
            best = min(best, _seg_seg_gap(p, q, quad[j], quad[(j + 1) % 4]))
    return best


def _seg_seg_gap(p, q, r, s):
    """Distance between two 2-D segments."""
    def pt_seg(a, b, c):
        bx, by = c[0] - b[0], c[1] - b[1]
        ln = bx * bx + by * by
        if ln < 1e-18:
            return math.hypot(a[0] - b[0], a[1] - b[1])
        t = ((a[0] - b[0]) * bx + (a[1] - b[1]) * by) / ln
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return math.hypot(a[0] - b[0] - t * bx, a[1] - b[1] - t * by)
    return min(pt_seg(p, r, s), pt_seg(q, r, s), pt_seg(r, p, q), pt_seg(s, p, q))


def _surface_gap(tris2d, rects):
    """Smallest signed separation between a projected surface and some boxes.

    Branch and bound on the bounding boxes: a disjoint pair of AABBs is a lower
    bound on the true distance, so once a close pair has been found the rest of
    the mesh is rejected with two comparisons apiece. Exact, and fast enough
    that the 24-phase world sweep still runs in under a second.
    """
    worst = float("inf")
    for tri in tris2d:
        (ax, ay), (bx, by), (cx, cy) = tri
        tl0 = ax if ax < bx else bx
        tl0 = tl0 if tl0 < cx else cx
        tl1 = ax if ax > bx else bx
        tl1 = tl1 if tl1 > cx else cx
        tr0 = ay if ay < by else by
        tr0 = tr0 if tr0 < cy else cy
        tr1 = ay if ay > by else by
        tr1 = tr1 if tr1 > cy else cy
        for rc in rects:
            dl = rc[0] - tl1 if rc[0] > tl1 else (tl0 - rc[1] if tl0 > rc[1]
                                                  else 0.0)
            dr = rc[2] - tr1 if rc[2] > tr1 else (tr0 - rc[3] if tr0 > rc[3]
                                                  else 0.0)
            if dl or dr:
                lo = math.hypot(dl, dr)
                if lo >= worst:
                    continue
            d = _tri_rect_gap(tri, rc)
            if d < worst:
                worst = d
    return worst


def car_section(verts, tris, r_bot=None):
    """The car's footprint in the sweep plane, one 2-D triangle per face.

    With `r_bot` the plane is the spoke's (lateral, radius); without it, the
    car's own (x, y). z is dropped either way, and dropping it is the point --
    a car's z is a function of the guideway phase, so a shape measured in this
    plane answers for every phase at once.
    """
    if r_bot is None:
        return [tuple((verts[i][0], verts[i][1]) for i in t) for t in tris]
    return [tuple((verts[i][0], r_bot - verts[i][1]) for i in t) for t in tris]


def truss_clearance(verts, tris):
    """Smallest SURFACE separation between the car and the truss envelope.

    Negative means interpenetration. A door interpenetrating a portal frame is
    a mistake this project has already made, and the reason it survived is that
    a solid inside another solid renders as a perfectly convincing solid.
    """
    return _surface_gap(car_section(verts, tris), truss_envelope())


# ---------------------------------------------------------------------------
# Clearance against the radial spokes
# ---------------------------------------------------------------------------

# The bar for the spoke is the bar for the truss. Anything tighter than the
# suspension gap would mean the fixed structure, not the running gear, is what
# decides how close the car can be built -- and the spoke is the one piece of
# structure a car cannot steer around. INV-050.
SPOKE_CLEARANCE_M = TRUSS_CLEARANCE_M


def spoke_section(schema, profile, sector):
    """The spoke's footprint in the plane the car sweeps, taken FROM the spoke.

    `truss_envelope` above rebuilds the truss from interior's constants, which
    is defensible for four beams laid on a grid. A spoke with a portal cut
    through it is seventeen rectangles, and re-deriving those here would
    guarantee that one day the test and the geometry describe different spokes.
    `interior.spoke()` reports its own section instead.
    """
    fr, to = it.drum_spoke_rings(schema, profile, sector)
    return it.spoke(schema, profile, sector, fr, to, 0.0)[2]["section_rects"]


def spoke_clearance(schema, profile, sector, verts, tris):
    """Smallest SURFACE separation between the car and spoke structure, over the
    whole run rather than at one point on it. Negative means interpenetration.

    z is dropped, and dropping it is the point. A spoke sits at one fixed z; a
    car's z is a function of the guideway phase, which `guideway_cars` takes as
    an argument and sweeps. Measuring in the (lateral, radius) plane therefore
    answers the question for EVERY phase at once -- it is a swept-volume test,
    not a sample of one. A test that fixed z would have to be believed for all
    the other z it did not look at, and the defect this replaces was a car
    sitting exactly in a spoke plane at the module's own default phase.

    The car's local frame maps straight onto the spoke's: x is the same lateral
    axis, and y is measured inboard from the bottom chord's centreline, so
    radius is the chord radius minus y.
    """
    r_bot = it.sector_radius(schema, profile, sector) * it.TRUSS_RADIUS_FRAC
    return _surface_gap(car_section(verts, tris, r_bot),
                        spoke_section(schema, profile, sector))


def spoke_sweep_report(schema, profile, sector, phases=24, per_guideway=2):
    """Place real cars at `phases` positions on every guideway and measure them
    against the real spokes, in world coordinates.

    The planar measurement above is exact and already covers every phase. This
    is the cross-check that the two subsystems agree about WHERE they are: a car
    whose guideway angle did not match its spoke's angle, or whose radius came
    off a different chord, would clear the section rectangles perfectly in the
    car's own frame and still hit the structure in the drum.

    Triangles, not vertices, and the z filter is on the triangle's own z RANGE:
    a face can straddle the spoke's 23.6 m band with both its ends outside it,
    and a vertex filter drops exactly the face that is inside the structure.

    `faces_in_spoke_z` is reported so the caller can assert the sweep actually
    drove cars through the spokes. A sweep that never reaches one passes for the
    wrong reason.
    """
    sm = it.drum_spokes(schema, profile, sector)[2]
    worst = float("inf")
    overlapping = crossings = 0
    for i in range(phases):
        wv, wt, _wm = drum_trams(schema, profile, sector,
                                 per_guideway=per_guideway,
                                 phase=i / float(phases), interior=False)
        for s in sm["solids"]:
            a = math.radians(s["angle_deg"])
            ca, sa = math.cos(a), math.sin(a)
            z0, z1 = s["z_span"]
            band = []
            for t in wt:
                p = (wv[t[0]], wv[t[1]], wv[t[2]])
                if max(q[2] for q in p) < z0 or min(q[2] for q in p) > z1:
                    continue
                crossings += 1
                band.append(tuple((-q[0] * sa + q[1] * ca,
                                   q[0] * ca + q[1] * sa) for q in p))
            if not band:
                continue
            g = _surface_gap(band, s["section_rects"])
            if g < 0.0:
                overlapping += 1
            worst = min(worst, g)
    return {"phases": phases, "faces_in_spoke_z": crossings,
            "overlapping": overlapping, "min_clearance_m": worst}


# ---------------------------------------------------------------------------
# Placement on a guideway
# ---------------------------------------------------------------------------

def car_frame(schema, profile, sector, angle_deg, z):
    """(origin, lateral, up, forward) for a car on the guideway at `angle_deg`.

    The origin is on the bottom chord's centreline, which is what the local
    frame measures y from, so the car's own geometry decides how far below the
    chord it hangs and no caller can get that wrong.
    """
    r0 = it.sector_radius(schema, profile, sector)
    r_bot = r0 * it.TRUSS_RADIUS_FRAC
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    origin = (r_bot * ca, r_bot * sa, z)
    lateral = (-sa, ca, 0.0)
    up = (-ca, -sa, 0.0)          # inboard: "up" is toward the spin axis
    forward = (0.0, 0.0, 1.0)
    return origin, lateral, up, forward


def to_world(schema, profile, sector, angle_deg, z, verts):
    o, lat, up, fwd = car_frame(schema, profile, sector, angle_deg, z)
    out = []
    for x, y, zz in verts:
        out.append((o[0] + x * lat[0] + y * up[0] + zz * fwd[0],
                    o[1] + x * lat[1] + y * up[1] + zz * fwd[1],
                    o[2] + x * lat[2] + y * up[2] + zz * fwd[2]))
    return out


def guideway_cars(schema, profile, sector, angle_deg, count=3, phase=0.0,
                  z_span=None, interior=False, glazed=True):
    """`count` cars evenly spaced along one guideway.

    Spacing is the sector length over the count, so cars are a headway apart
    rather than clustered, and the whole train set moves by changing `phase`
    alone -- which is what an animated guideway needs.
    """
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = z_span if z_span else (ex["z0"], ex["z1"])
    L = car_length()
    span = z1 - z0
    spacing = span / count
    if spacing < L * 1.5:
        raise ValueError(f"{count} cars of {L:.0f} m do not fit in {span:.0f} m "
                         "of guideway with a headway between them")

    verts, tris, groups, places = [], [], [], []
    lv, lt, lm = tram_car(interior=interior, glazed=glazed)
    for i in range(count):
        z = z0 + spacing * ((i + 0.5 + phase) % count)
        z = min(max(z, z0 + L / 2.0), z1 - L / 2.0)
        o = len(verts)
        verts.extend(to_world(schema, profile, sector, angle_deg, z, lv))
        tris.extend((a + o, b + o, c + o) for a, b, c in lt)
        groups.extend(lm["groups"])
        places.append({"angle_deg": angle_deg, "z_m": round(z, 2)})
    return verts, tris, {"cars": count, "angle_deg": angle_deg,
                         "placements": places, "car_triangles": len(lt),
                         "triangles": len(tris), "groups": groups}


def drum_trams(schema, profile, sector, per_guideway=2, phase=0.0,
               z_span=None, interior=False, glazed=True):
    """Cars on every guideway. One truss per spoke, so one line per spoke."""
    verts, tris, groups, places = [], [], [], []
    for i in range(it.TRUSS_COUNT):
        ang = 360.0 * i / it.TRUSS_COUNT
        v, t, m = guideway_cars(schema, profile, sector, ang,
                                count=per_guideway,
                                phase=phase + i / float(it.TRUSS_COUNT),
                                z_span=z_span, interior=interior,
                                glazed=glazed)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(m["groups"])
        places.extend(m["placements"])
    return verts, tris, {"guideways": it.TRUSS_COUNT,
                         "cars": len(places), "placements": places,
                         "triangles": len(tris), "groups": groups}


def seat_local(eye_h=1.22):
    """Eye and aim point of the 35a passenger, in the car's own frame.

    Split out from `passenger_seat` so the self-test can cast the camera's real
    ray through the windscreen. A test that casts a hand-written direction is
    testing a different camera from the one that renders.
    """
    y_floor = level_y("floor")
    _z_rear, z_fore = _saloon_span()
    # Just aft of the forward seat group, on the port side of the aisle, at a
    # seated eye height. Aimed forward and across so the windscreen, the near
    # seat backs and a run of side bench are all in one frame, which is what
    # 35a holds. Note the handedness: because "up" in the drum points at the
    # spin axis, the car's PORT side comes out on the right of the image, so
    # this viewpoint reproduces 35a mirrored rather than matched.
    z_eye = z_fore - NOSE_M - 4.4
    return ((-1.50, y_floor + eye_h, z_eye),
            (0.95, y_floor + eye_h - 0.55, z_eye + 8.4))


def passenger_seat(schema, profile, sector, angle_deg, z, eye_h=1.22):
    """Eye and look direction for the passenger position of 35a, in world space.

    Reproducing 35a by hand at the render call site would bury the numbers in a
    shell script; keeping the viewpoint next to the geometry that defines it
    means a change to the seat pitch or the saloon length moves the camera with
    it instead of silently pointing it at a wall.
    """
    eye_l, tgt_l = seat_local(eye_h)
    eye, tgt = to_world(schema, profile, sector, angle_deg, z, [eye_l, tgt_l])
    _o, _lat, up, _f = car_frame(schema, profile, sector, angle_deg, z)
    return eye, tgt, up


# ---------------------------------------------------------------------------
# Self-test. The properties a render cannot be trusted to show.
# ---------------------------------------------------------------------------

def _ray_hits(origin, direction, verts, tris):
    """Moller-Trumbore, any hit in front of the origin."""
    ox, oy, oz = origin
    dx, dy, dz = direction
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        h = (dy * e2[2] - dz * e2[1], dz * e2[0] - dx * e2[2],
             dx * e2[1] - dy * e2[0])
        det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
        if -1e-9 < det < 1e-9:
            continue
        inv = 1.0 / det
        s = (ox - p0[0], oy - p0[1], oz - p0[2])
        u = inv * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
        if u < 0.0 or u > 1.0:
            continue
        q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
             s[0] * e1[1] - s[1] * e1[0])
        v = inv * (dx * q[0] + dy * q[1] + dz * q[2])
        if v < 0.0 or u + v > 1.0:
            continue
        if inv * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) > 1e-6:
            return True
    return False


def screen_centre():
    """Centre of the windscreen aperture in the car's frame.

    The self-test aims at this rather than at the camera's own aim point,
    because the camera looks diagonally across the saloon and a ray on that
    heading leaves through the side band. Two different questions need two
    different rays.
    """
    L = car_length()
    return (0.0, (level_y("sill") + level_y("cant")) / 2.0, L / 2.0 - 0.6)


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)

    lv, lt, lm = tram_car(interior=True)
    ev, et, em = tram_car(interior=False)
    sv, st_, sg = car_shell()
    iv, it_, ig = car_saloon()
    hull_t = [t for t, g in zip(st_, sg) if g == "tram_body"]
    wall_t = [t for t, g in zip(it_, ig)
              if g in ("tram_in_wall", "tram_in_window", "tram_in_ceiling",
                       "tram_in_floor")]

    check("the car builds", len(lt) > 500, f"{len(lt)} triangles")

    # --- what was measured, and that the MESH still measures it -------------
    # These three replace assertions that could not fail. They compared
    # `L / TRUSS_BAY_M` against `CAR_BAYS` where L was defined as
    # `CAR_BAYS * TRUSS_BAY_M`, and `(total - c/2) / d` against CAR_DEPTH_FRAC
    # where total was defined as `c/2 + CAR_DEPTH_FRAC * d`. Both are algebraic
    # identities: they hold for CAR_BAYS = -3.0 and CAR_DEPTH_FRAC = 99.0, and
    # they never touched a triangle. What has to be true is that the BUILT hull
    # measures what was read off the reference, so that is what is measured --
    # off the loft's own vertices, against the numbers from 34b rather than
    # against the constants those numbers were written into.
    L = car_length()
    hull_g = ("tram_body", "tram_valance", "tram_roof", "tram_recess")
    hull_v = sorted({i for t, g in zip(st_, sg) if g in hull_g for i in t})
    hz = [sv[i][2] for i in hull_v]
    hy = [sv[i][1] for i in hull_v]
    bays_built = (max(hz) - min(hz)) / it.TRUSS_BAY_M
    check("the built hull is the 3.9 bays rectified off 34b",
          abs(bays_built - 3.9) <= 0.25,
          f"{max(hz) - min(hz):.1f} m = {bays_built:.2f} bays")
    # 34b measures the car's depth below the chord as a fraction of the local
    # chord separation, so that is the form the mesh is checked in.
    frac_built = (-min(hy) - it.TRUSS_CHORD_M / 2.0) / it.TRUSS_DEPTH_M
    check("the built hull hangs the measured 0.65 of the truss depth",
          abs(frac_built - 0.65) <= 0.05,
          f"{-min(hy) - it.TRUSS_CHORD_M / 2.0:.2f} m below the chord "
          f"underside = {frac_built:.3f} of {it.TRUSS_DEPTH_M} m")
    # The module docstring claims the car is expressed in truss units, so that
    # rescaling the truss rescales the car rather than breaking it. That is a
    # property of the code, and the only honest way to test it is to move the
    # truss and rebuild.
    bay0, dep0 = it.TRUSS_BAY_M, it.TRUSS_DEPTH_M
    try:
        it.TRUSS_BAY_M, it.TRUSS_DEPTH_M = bay0 * 1.5, dep0 * 1.5
        rv, rt_, rg = car_shell()
        rvi = sorted({i for t, g in zip(rt_, rg) if g in hull_g for i in t})
        rz = max(rv[i][2] for i in rvi) - min(rv[i][2] for i in rvi)
        ry = -min(rv[i][1] for i in rvi) - it.TRUSS_CHORD_M / 2.0
    finally:
        it.TRUSS_BAY_M, it.TRUSS_DEPTH_M = bay0, dep0
    # Depth is measured below the chord UNDERSIDE, so only that part scales --
    # the chord's own half section is a separate constant and does not.
    hang = -min(hy) - it.TRUSS_CHORD_M / 2.0
    check("rescaling the truss rescales the car with it",
          abs(rz - 1.5 * (max(hz) - min(hz))) < 1e-6
          and abs(ry - 1.5 * hang) < 1e-6,
          f"{rz:.1f} m long and {ry:.2f} m below the chord on a truss 1.5x "
          "bigger")
    # `len(et) == len(st_)` used to be half of this check and could not fail:
    # `tram_car(interior=False)` returns `car_shell()` unmodified, so the two
    # are the same list. What "a strict addition" has to mean geometrically is
    # that the saloon adds detail INSIDE the shell and nothing outside it -- a
    # saloon built at the wrong scale or hung off the wrong datum would still
    # satisfy a triangle count.
    box_s = [(min(p[i] for p in ev), max(p[i] for p in ev)) for i in range(3)]
    outside = sum(1 for p in iv
                  if any(p[i] < box_s[i][0] - 1e-9 or p[i] > box_s[i][1] + 1e-9
                         for i in range(3)))
    check("interior LOD is a strict addition to the exterior",
          len(et) < len(lt) and outside == 0,
          f"{len(et)} exterior vs {len(lt)} with saloon; {outside} saloon "
          "vertices outside the shell's own extent")

    # --- it hangs BELOW the chord, and does not touch it ---------------------
    # Getting the sign wrong builds a car riding on top of the guideway, which
    # renders perfectly and is nonsense.
    y_max = max(y for _x, y, _z in lv)
    chord_bottom = -it.TRUSS_CHORD_M / 2.0
    check("every part of the car hangs below the bottom chord",
          y_max < chord_bottom,
          f"highest point y={y_max:.2f} m, chord underside {chord_bottom:.2f} m")
    check("the car is entirely outboard of the truss depth",
          y_max < it.TRUSS_DEPTH_M / 2.0, f"y_max {y_max:.2f}")

    clear = truss_clearance(lv, lt)
    check("the car clears every truss member",
          clear >= TRUSS_CLEARANCE_M - 1e-9,
          f"min clearance {clear:.3f} m, need {TRUSS_CLEARANCE_M} m")
    check("the clearance is the suspension gap and nothing tighter",
          abs(clear - SUSPENSION_GAP_M) < 0.02,
          f"{clear:.3f} m vs gap {SUSPENSION_GAP_M} m")

    # A clearance test that cannot fail is worthless. Prove it fires.
    lifted = [(x, y + 1.0, z) for x, y, z in lv]
    check("the clearance test detects interpenetration",
          truss_clearance(lifted, lt) < 0, f"{truss_clearance(lifted, lt):.3f} m")

    # --- and against the radial spokes --------------------------------------
    # The guideways are in the spoke planes because nothing else could carry a
    # 2,586 m truss (INV-012), so a car HAS to cross a spoke. It used to cross
    # it the way a bullet crosses a wall: 168 of 3,144 vertices inside solid
    # structure, 6.43 m deep, at this module's own default phase, with no test
    # of any kind looking. `interior.spoke()` now cuts a framed portal for the
    # guideway's structure gauge. These keep it cut.
    g = it.guideway_gauge(schema, profile, sector)
    rr_l = [g["chord_r_m"] - y for _x, y, _z in lv]
    check("the car fits inside the guideway's structure gauge",
          min(rr_l) >= g["r_inner"] + SPOKE_CLEARANCE_M
          and max(rr_l) <= g["r_outer"] - SPOKE_CLEARANCE_M
          and max(abs(x) for x, _y, _z in lv)
          <= g["half_width_m"] - SPOKE_CLEARANCE_M,
          f"car r {min(rr_l):.2f}-{max(rr_l):.2f} m, half width "
          f"{max(abs(x) for x, _y, _z in lv):.2f} m against a gauge of "
          f"{g['r_inner']:.2f}-{g['r_outer']:.2f} m by {g['half_width_m']} m")

    sc = spoke_clearance(schema, profile, sector, lv, lt)
    check("the car clears the spoke at every phase, not just the default",
          sc >= SPOKE_CLEARANCE_M,
          f"{sc:.3f} m, need {SPOKE_CLEARANCE_M} m")
    # The spoke must never be what limits the car. If it becomes tighter than
    # the truss, the portal has stopped being sized off the gauge and started
    # being sized off whatever fitted.
    check("the spoke is never tighter than the guideway itself",
          sc >= clear - 1e-9, f"spoke {sc:.3f} m vs truss {clear:.3f} m")

    # Both directions of failure, because the portal is bounded in both and a
    # test that only catches one is half a test.
    wide = [(x * 3.0, y, z) for x, y, z in lv]
    deep = [(x, y - 3.0, z) for x, y, z in lv]
    check("the spoke clearance test detects a car too wide for the portal",
          spoke_clearance(schema, profile, sector, wide, lt) < 0,
          f"{spoke_clearance(schema, profile, sector, wide, lt):.3f} m")
    check("the spoke clearance test detects a car hanging below the portal",
          spoke_clearance(schema, profile, sector, deep, lt) < 0,
          f"{spoke_clearance(schema, profile, sector, deep, lt):.3f} m")

    # And the failure a VERTEX loop cannot see, which is the reason these two
    # metrics were rewritten as surface tests.
    #
    # Put a 1.4 m square member down the middle of the portal, two metres below
    # the saloon floor. That is not a contrived place: it is the car's
    # underfloor void, it is where running gear or a bearing beam would go, and
    # `interior.spoke()`'s docstring already talks about letting the truss's
    # bottom chord and light runs INTO the header. It lands wholly inside the
    # car's footprint and contains not one car vertex, so the vertex loop
    # returns the same 0.500 m it returns with no member there at all, while
    # 1.4 m of structure runs the length of the car.
    r_bot_l = it.sector_radius(schema, profile, sector) * it.TRUSS_RADIUS_FRAC
    sec2d = car_section(lv, lt, r_bot_l)
    h = 0.7
    r_void = r_bot_l - (level_y("floor") - 2.0)
    member = (-h, h, r_void - h, r_void + h)
    rects = list(spoke_section(schema, profile, sector))

    def vertex_loop(rs):
        """What the metric this replaced would have said. The two are compared
        by running both, not by remembering a number."""
        worst = float("inf")
        for x, y, _z in lv:
            lat, r = x, r_bot_l - y
            for l0, l1, r0, r1 in rs:
                dl = max(l0 - lat, 0.0, lat - l1)
                dr = max(r0 - r, 0.0, r - r1)
                if dl == 0.0 and dr == 0.0:
                    worst = min(worst, -min(min(lat - l0, l1 - lat),
                                            min(r - r0, r1 - r)))
                else:
                    worst = min(worst, math.hypot(dl, dr))
        return worst

    surf = _surface_gap(sec2d, rects + [member])
    vtx, vtx0 = vertex_loop(rects + [member]), vertex_loop(rects)
    check("a member wholly inside the car is inside the car",
          surf < 0.0, f"surface separation {surf:.3f} m")
    # The demonstration has to keep demonstrating. If the saloon ever grows a
    # fitting into that void the comparison stops being about the metric, so
    # say so here rather than letting the pair quietly become a tautology.
    check("...and the vertex loop it replaced is blind to it",
          abs(vtx - vtx0) < 1e-9 and vtx > 0.0,
          f"vertex loop {vtx:.3f} m with the member against {vtx0:.3f} m "
          "without it")

    # World-space cross-check: real cars at 24 phases on all three guideways,
    # measured against the real spokes. The planar test above already covers
    # every phase; this one covers the possibility that the car and the spoke
    # disagree about where they are.
    swp = spoke_sweep_report(schema, profile, sector, phases=24)
    check("the sweep actually drives cars through the spokes",
          swp["faces_in_spoke_z"] > 0,
          f"{swp['faces_in_spoke_z']} car faces inside a spoke's z span")
    check("no car surface overlaps a spoke at any sampled phase",
          swp["overlapping"] == 0, f"{swp['overlapping']} overlapping")
    check("the swept world clearance agrees with the planar one",
          abs(swp["min_clearance_m"] - sc) < 0.05,
          f"world {swp['min_clearance_m']:.3f} m vs planar {sc:.3f} m")

    # The car must never reach under a light run, or it shadows the habitat.
    lamp_in = it.TRUSS_CHORD_M + 3.0 - it.TRUSS_LAMP_R_M
    check("the car stays inboard of the light runs",
          max(abs(x) for x, _y, _z in lv) < lamp_in,
          f"half width {max(abs(x) for x, _y, _z in lv):.2f} m "
          f"vs lamp at {lamp_in:.2f} m")

    # --- winding, both conventions, both measured ---------------------------
    out = _facing_fraction(sv, hull_t)
    check("the body faces outward", out >= 0.99, f"{out * 100:.1f}%")
    cab_mid = (level_y("floor") + level_y("cant")) / 2.0
    inw = _facing_fraction(iv, wall_t, inward=True, mid=cab_mid)
    check("the saloon shell faces the cabin", inw >= 0.99, f"{inw * 100:.1f}%")
    # And that the measurement can fail, so it is a test rather than a comment.
    flipped = [t[::-1] for t in hull_t]
    check("the facing measurement detects a reversed shell",
          _facing_fraction(sv, flipped) < 0.05,
          f"{_facing_fraction(sv, flipped) * 100:.1f}%")

    # Every lit strip must face the aisle. An emissive wound at the wall is
    # invisible and silently so: it costs triangles, passes every other test,
    # and removes the interior's most distinctive feature from the render.
    facing_wall = 0
    for (a, b, c), g in zip(lt, lm["groups"]):
        if g != "tram_in_strip":
            continue
        p0, p1, p2 = lv[a], lv[b], lv[c]
        u = [p1[i] - p0[i] for i in range(3)]
        v = [p2[i] - p0[i] for i in range(3)]
        nx = u[1] * v[2] - u[2] * v[1]
        # In the car frame, x runs from the axis outward to each wall, so a
        # face whose normal shares the sign of its own x points at the wall.
        if nx * p0[0] > 0:
            facing_wall += 1
    check("every lit strip faces the aisle", facing_wall == 0,
          f"{facing_wall} strip faces pointing at the wall")

    # --- the saloon is enclosed ---------------------------------------------
    # Cast a deterministic sphere of rays from the seated eye. Every one must
    # hit something. A corridor open to space down both sides survived seven
    # render passes in session 2p because a hole and a shadow are the same
    # pixels; this is the numeric version of that lesson.
    eye, _aim = seat_local()
    n_ray = 240
    misses = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n_ray):
        w = 1.0 - 2.0 * (i + 0.5) / n_ray
        rad = math.sqrt(max(0.0, 1.0 - w * w))
        th = ga * i
        d = (rad * math.cos(th), w, rad * math.sin(th))
        if not _ray_hits(eye, d, lv, lt):
            misses.append(d)
    check("the saloon is closed in every direction", not misses,
          f"{len(misses)}/{n_ray} rays escaped")

    # Unglazed, the windscreen must actually be a hole -- otherwise the render
    # that is supposed to reproduce 35a looks at a wall.
    ov, ot, _om = tram_car(interior=True, glazed=False)
    sc = screen_centre()
    fwd = tuple(sc[i] - eye[i] for i in range(3))
    check("unglazed, the windscreen is an aperture the camera sees through",
          not _ray_hits(eye, fwd, ov, ot))
    check("glazed, the same direction is closed",
          _ray_hits(eye, fwd, lv, lt))
    # 35a shows the drum's fields through the SIDE glass as well, so the side
    # band has to be a real slot too, not just the screen.
    y_win = (level_y("sill") + level_y("head")) / 2.0
    # A fan rather than one ray: the mullions are opaque and a single ray that
    # happens to line up with one proves nothing about the band.
    sides = [(1.0, (y_win - eye[1]) / 3.4, dz)
             for dz in (-1.2, -0.6, 0.0, 0.6, 1.2)]
    escaped = sum(1 for d in sides if not _ray_hits(eye, d, ov, ot))
    check("unglazed, the side window band is open too", escaped >= 3,
          f"{escaped}/5 rays out")
    check("glazed, the side window band is closed",
          all(_ray_hits(eye, d, lv, lt) for d in sides))

    # --- placement ----------------------------------------------------------
    ex = schema["sectors"]["extents_m"][sector]
    v, t, m = guideway_cars(schema, profile, sector, 0.0, count=3)
    # This was `m["cars"] == 3`, and `guideway_cars` returns `{"cars": count}` --
    # the argument, handed straight back. It could not fail. It passed for
    # count = 0 and for a build that emitted no geometry at all. What has to be
    # true is that three separate car BODIES came out, so count them off the
    # mesh: split the emitted vertices at every z gap wider than a car and see
    # how many runs there are. That also catches the one way this function can
    # legitimately lose a car -- the clamp on the line after the spacing, which
    # will happily stack two cars at the same end of the run.
    zs_all = sorted(p[2] for p in v)
    runs, start = [], zs_all[0]
    for a, b in zip(zs_all, zs_all[1:]):
        # Split on a gap wider than half a car: the body has its own z gaps --
        # window bays, the ports along the valance -- and the widest of those is
        # 4.1 m, while the headway between cars is 862 m.
        if b - a > L / 2.0:
            runs.append((start, a))
            start = b
    runs.append((start, zs_all[-1]))
    check("three separate car bodies come out of one guideway",
          len(runs) == 3 and all(abs((hi - lo) - L) < 0.05 for lo, hi in runs),
          f"{len(runs)} runs of "
          f"{[round(hi - lo, 1) for lo, hi in runs]} m against a {L:.0f} m car")
    check("and every one of them is real geometry",
          len(t) == 3 * m["car_triangles"] and len(v) == 3 * len(ev),
          f"{len(t)} triangles, {len(v)} vertices for three "
          f"{m['car_triangles']}-triangle cars")
    for p in m["placements"]:
        check(f"car at z={p['z_m']} is inside the sector",
              ex["z0"] + L / 2 - 1e-6 <= p["z_m"] <= ex["z1"] - L / 2 + 1e-6)
    zs = sorted(p["z_m"] for p in m["placements"])
    check("placed cars do not overlap",
          all(zs[i + 1] - zs[i] > L for i in range(len(zs) - 1)),
          str([round(zs[i + 1] - zs[i], 1) for i in range(len(zs) - 1)]))

    # Every placed vertex must sit at a radius between the chord and the drum
    # floor: a car that pokes through the ground, or up past the truss, is the
    # failure the local frame exists to prevent.
    r0 = it.sector_radius(schema, profile, sector)
    r_bot = r0 * it.TRUSS_RADIUS_FRAC
    rr = [math.hypot(x, y) for x, y, _z in v]
    check("placed cars hang between the chord and the ground",
          r_bot < min(rr) and max(rr) < r0 - 2.0,
          f"radii {min(rr):.1f}-{max(rr):.1f} m, chord {r_bot:.1f}, "
          f"floor {r0:.1f}")
    # And clear of the tallest thing on the ground under them.
    tallest = max(rel for _f, _n, rel in it.LAND_USE)
    check("cars clear the tallest land-use relief",
          r0 - tallest - max(rr) > 5.0,
          f"{r0 - tallest - max(rr):.1f} m over a {tallest} m terrace")

    dv, dt, dm = drum_trams(schema, profile, sector, per_guideway=2)
    # These three were:
    #     dm["guideways"] == it.TRUSS_COUNT == it.SPOKE_COUNT
    #     dm["cars"] == 2 * it.TRUSS_COUNT
    #     sorted({p["angle_deg"] ...}) == [0.0, 120.0, 240.0]
    # and the first two could not fail. `drum_trams` returns
    # `{"guideways": it.TRUSS_COUNT}` -- the constant, handed back -- and
    # `interior.py` defines `TRUSS_COUNT = SPOKE_COUNT`, so all three names in
    # that chain are one object. `dm["cars"]` is `len(places)`, appended once
    # per iteration of `range(count)` over `range(TRUSS_COUNT)`, so it is
    # `count * TRUSS_COUNT` by construction. The third compared derived angles
    # against a literal, which says the constant is 3 and nothing about the
    # station.
    #
    # What actually matters is the invariant the spoke defect turned on: a
    # guideway that is not in a spoke plane is a truss nothing holds up, and a
    # car on it crosses the spoke where there is no portal. So take the spokes'
    # angles from the BUILT spokes and require the lines to match them.
    spoke_angs = sorted(s["angle_deg"]
                        for s in it.drum_spokes(schema, profile,
                                                sector)[2]["solids"])
    angs = sorted({p["angle_deg"] for p in dm["placements"]})
    check("there is one tram line per BUILT spoke, in its plane",
          len(angs) == len(spoke_angs)
          and all(abs(a - b) < 1e-9 for a, b in zip(angs, spoke_angs)),
          f"lines at {angs} against spokes at {spoke_angs}")
    # And the cars are geometry, not entries in a list. Two per line, each a
    # whole car, measured off the emitted mesh.
    check("every line carries its cars as real geometry",
          len(dm["placements"]) == 2 * len(spoke_angs)
          and len(dt) == 2 * len(spoke_angs) * len(et),
          f"{len(dm['placements'])} placements and {len(dt)} triangles for "
          f"{len(spoke_angs)} lines of two {len(et)}-triangle cars")

    # --- determinism --------------------------------------------------------
    a1 = tram_car(interior=True)[0]
    a2 = tram_car(interior=True)[0]
    check("regeneration is identical", a1 == a2)

    # --- the passenger viewpoint --------------------------------------------
    eye_w, tgt_w, up_w = passenger_seat(schema, profile, sector, 0.0, 5000.0)
    r_eye = math.hypot(eye_w[0], eye_w[1])
    check("the passenger eye is inside the car",
          r_bot < r_eye < r0 - 5.0, f"r={r_eye:.1f} m")
    check("the passenger's up points at the spin axis",
          up_w[0] * eye_w[0] + up_w[1] * eye_w[1] < 0)
    d = tuple(tgt_w[i] - eye_w[i] for i in range(3))
    check("the passenger looks forward along the guideway",
          d[2] > 0 and abs(d[2]) > max(abs(d[0]), abs(d[1])),
          f"look {tuple(round(c, 2) for c in d)}")

    # --- cost ---------------------------------------------------------------
    # The drum's whole headroom is 257,304 triangles. Six cars must not be a
    # meaningful fraction of it or the ground has nothing left.
    six = dm["triangles"]
    check("six exterior cars stay under 5% of the drum's headroom",
          six < 0.05 * 257_304, f"{six:,} triangles")
    check("one saloon fits a streaming cell budget",
          len(lt) < 20_000, f"{len(lt):,} triangles")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
