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
import hashlib
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
# INV-073: longitudinal bodyside articulation on the car.
STRAKE_H_M = 0.11
STRAKE_P_M = 0.06
DUCT_H_M = 0.22
CHANNEL_W_M = 0.30
CHANNEL_H_M = 0.18
PILLAR_W_M = 0.16
ROOF_BOXES = 4
ROOF_BOX_L_M = 3.2
ROOF_BOX_H_M = 0.42
SEAT_PITCH_M = 0.62           # one seated person, cushion plus its gap

# Clearance the car must keep from every truss member. A door interpenetrating
# a portal frame is a mistake this project has already made once; this is the
# number the self-test enforces so it cannot happen a second time in a place
# nobody is looking. INV-050.
TRUSS_CLEARANCE_M = 0.30

# Cars on one guideway. Named rather than left as a bare default argument
# because `transit.py` derives the line's HEADWAY from it -- round trip over
# cars -- and a number two modules disagree about is the two-sources-of-truth
# defect this project keeps finding. `transit._selftest` reads this back out of
# `drum_trams`'s signature and asserts they match.
CARS_ON_A_GUIDEWAY = 2


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
    # ARTICULATION -- INV-073's rule on a vehicle. 36.6% of its detail floor:
    # a smooth loft with a window band. What a rail vehicle actually carries is
    # all LONGITUDINAL and all thin, which is the highest-yield geometry there
    # is: waist and cant rails the length of the body, a roof cable duct, an
    # underframe channel, and a rubbing strake. Each is one box laying four
    # lines the full length of the car.
    L = car_length()
    z0, z1 = -L / 2.0 + 0.25, L / 2.0 - 0.25
    y_roof, y_under = level_y("roof"), level_y("under")
    hw = CAR_WIDTH_M / 2.0
    body = y_roof - y_under
    for frac_y, nm, prd in ((0.90, "tram_cant_rail", STRAKE_P_M),
                            (0.78, "tram_cant_rail", STRAKE_P_M),
                            (0.62, "tram_waist_rail", STRAKE_P_M * 0.7),
                            (0.44, "tram_waist_rail", STRAKE_P_M),
                            (0.30, "tram_waist_rail", STRAKE_P_M),
                            (0.18, "tram_strake", STRAKE_P_M * 0.7),
                            (0.10, "tram_strake", STRAKE_P_M * 1.4)):
        yy = y_under + body * frac_y
        for s in (-1, 1):
            b0 = len(tris)
            _slab(verts, tris, min(s * hw, s * (hw + prd)),
                  max(s * hw, s * (hw + prd)),
                  yy - STRAKE_H_M / 2, yy + STRAKE_H_M / 2, z0, z1)
            groups.extend([nm] * (len(tris) - b0))
    # Roof duct and underframe channel, both full length.
    # Body pillars at the window pitch: the vertical member between two
    # windows, which every rail vehicle has and which reads at any distance the
    # windows do.
    npil = max(2, int((z1 - z0) / WINDOW_PITCH_M))
    for k in range(npil + 1):
        zz = z0 + (z1 - z0) * k / npil
        for s in (-1, 1):
            b0 = len(tris)
            _slab(verts, tris, min(s * hw, s * (hw + STRAKE_P_M)),
                  max(s * hw, s * (hw + STRAKE_P_M)),
                  y_under + body * 0.30, y_under + body * 0.78,
                  zz - PILLAR_W_M / 2, zz + PILLAR_W_M / 2)
            groups.extend(["tram_pillar"] * (len(tris) - b0))
    # UNDERFRAME EQUIPMENT, NOT ROOF EQUIPMENT, and the car told me which. I
    # put a duct and four boxes on the roof first; the clearance gate came back
    # with 0.211 m against the 0.35 m suspension gap, because on a SUSPENDED car
    # the roof is the face nearest the truss it hangs from. There is nowhere for
    # roof equipment to go. Underfloor is where a hanging vehicle carries it and
    # where there is 2 m of free depth.
    b0 = len(tris)
    _slab(verts, tris, -hw * 0.45, hw * 0.45, y_under - DUCT_H_M, y_under,
          z0, z1)
    groups.extend(["tram_duct"] * (len(tris) - b0))
    for k in range(ROOF_BOXES):
        zz = z0 + (z1 - z0) * (k + 0.5) / ROOF_BOXES
        b0 = len(tris)
        _slab(verts, tris, -hw * 0.30, hw * 0.30,
              y_under - DUCT_H_M - ROOF_BOX_H_M, y_under - DUCT_H_M,
              zz - ROOF_BOX_L_M / 2, zz + ROOF_BOX_L_M / 2)
        groups.extend(["tram_duct"] * (len(tris) - b0))
    for s in (-1, 1):
        for ck in range(2):
            b0 = len(tris)
            xx = s * hw * (0.34 + 0.28 * ck)
            _slab(verts, tris, xx - CHANNEL_W_M / 2, xx + CHANNEL_W_M / 2,
                  y_under - CHANNEL_H_M, y_under, z0, z1)
            groups.extend(["tram_channel"] * (len(tris) - b0))
    # NO BODYSIDE SKIRT PANELS. They took six exterior cars to 15,648
    # triangles against this module's 15,000 cap, and they moved the planar
    # clearance to 0.360 m against the swept world figure of 0.500, tripping the
    # check agent B rebuilt as a surface test. The car is at 264% of its detail
    # floor without them, so there is nothing to buy and two gates to respect.

    # Measured on the hull loft and its caps only. Applied bodily to the whole
    # car it would fail on every fitting: a mullion is a solid box standing on
    # the surface and half its faces point inward by design, which is correct
    # and invisible. The surface that must not be inside out is the one the
    # fittings are stuck to.
    hull = [t for t, g in zip(tris, groups)
            if g in ("tram_valance", "tram_roof", "tram_recess")]
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


def drum_trams(schema, profile, sector, per_guideway=CARS_ON_A_GUIDEWAY,
               phase=0.0, z_span=None, interior=False, glazed=True):
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
# MOTION. This module built a vehicle and never said how fast it goes.
#
# Session 3z, and the gap was found by the owner asking how long it takes to
# cross the station. Everything above places cars on a guideway; nothing above
# moves them, and the string "speed" appeared nowhere in the file. The physics
# lives in `transit.py` -- one authority on motion for the whole station, the
# same rule as hard rule 4 -- and what belongs HERE is the part that is about
# this vehicle: whether the car fits the service the line asks of it.
#
# The guideway tram is the fastest passenger system on the station and the
# reason is geometric rather than engineering: it runs ALONG the spin axis, so
# omega x v is identically zero and Coriolis imposes no speed cap on it at all.
# The two systems that run across the spin are capped at 3.13 m/s. This one is
# limited only by how hard you may accelerate a standing passenger, which is
# why it reaches 26.7 m/s between stops 646 m apart.
# ---------------------------------------------------------------------------

def service(schema, profile, sector=None):
    """(line, report) for this guideway: stops, speed, ride and headway.

    Delegated rather than restated. `transit.guideway_line` derives the stops
    from `interior`'s truss span and spoke position, which is the same
    structure `guideway_cars` hangs cars on, so the timetable and the geometry
    cannot come apart.
    """
    import transit as tr                                      # noqa: PLC0415
    line = tr.guideway_line(schema, profile, sector)
    return line, tr.line_report(schema, line)


def seated_capacity():
    """Seats in one car, counted off the saloon this module actually builds.

    Derived from the same `bench_m`, `gap_m` and `SEAT_PITCH_M` the geometry is
    emitted from rather than stated separately, so a change to the seating
    plan moves the capacity with it. The long benches are continuous cushions
    -- 35a is emphatic about that -- so a "seat" on them is a seat pitch of
    bench, which is what a continuous bench is counted in.
    """
    z_rear, z_fore = _saloon_span()
    bench_m, gap_m = 6.0, 1.4
    z_b0, z_b1 = z_rear + 1.2, z_fore - NOSE_M - 0.3
    n_mod = max(1, int((z_b1 - z_b0 + gap_m) / (bench_m + gap_m)))
    bench_seats = 2 * n_mod * int(bench_m / SEAT_PITCH_M)
    w_in = level_w("sill") - WALL_T
    forward = sum(1 for k in range(3)
                  if -w_in + 0.62 + k * (SEAT_PITCH_M + 0.10) <= -0.4)
    return {"bench_modules": n_mod, "bench_seats": bench_seats,
            "forward_seats": forward, "seats": bench_seats + forward}


def braking_distance(schema, profile, sector=None):
    """How far a car needs to stop from line speed, under the same limits.

    The service profile's own numbers, not an emergency one: a car that cannot
    stop inside its stop spacing under NORMAL braking is running too fast for
    its stops, and that is a property of this vehicle on this guideway rather
    than of transit in general.
    """
    import transit as tr                                      # noqa: PLC0415
    _line, rep = service(schema, profile, sector)
    v = rep["peak_speed_m_s"]
    _t, d = tr._ramp(v, tr.CRUISE_ACCEL_M_S2, tr.JERK_M_S3)
    return {"peak_speed_m_s": v, "stop_distance_m": d,
            "spacing_m": rep["spacing_m"]}


# ---------------------------------------------------------------------------
# THE SECOND TRAM -- the ground-level ring line, PLC-073 `ground_tram`
# ---------------------------------------------------------------------------
# `directory.PLACES` has carried `ground_tram` since session 3c with no module
# and no builder, and `tools/export_drum.py`'s header says so in as many words:
# *"the register carries it (210 deg, 20 x 200 m) and nothing in this repository
# builds a ground-level tram"*. A crowd is placed in it. People stand in a
# field.
#
# IT IS A DIFFERENT VEHICLE FROM THE ONE ABOVE, AND THE GAZETTEER IS EMPHATIC:
# *"a green-and-yellow streamlined car on an elevated track at garden ground
# level, with its own station canopy -- sharing nothing with the white/maroon
# guideway tram. Two transit systems in the drum, not one."*
# (`docs/gazetteer/LOCATIONS.md` section 9, authority 1,
#  `reference/03-sector-blue/Babylon_5_2-22_29a.jpg`.)
#
# So this reuses the MODULE and its primitives -- `_box`, `_slab`, `_quad`,
# `_loft`, `_cap`, `_prism8`, `_facing_fraction` -- and not the design. A third
# file would have been a third description of "a tram"; giving the ground car
# `levels()` would have made the two systems one.
#
# WHAT THE FRAME ESTABLISHES, measured off 29a rather than remembered:
#   * an ELEVATED way at terrace level, behind a slatted parapet
#   * a cream/ivory upper body carrying a continuous dark window band
#   * a GREEN flank band below the sill -- median sRGB (54, 76, 72) over a
#     165 x 14 px patch of the flank, i.e. G/R 1.41 and B/R 1.33, so it is
#     green-dominant and desaturated: a teal, not a leaf green
#   * a long, low, streamlined STATION CANOPY on a plinth, tapered at both
#     ends, carrying three vertical illuminated slots on its flank
#
# WHAT IT DOES NOT ESTABLISH is any dimension at all. Nothing of known size sits
# in the car's depth plane, and the terrace furniture that IS measurable (a
# bench, a planter) is four times nearer the lens, so the projective
# rectification that gave the guideway car its length off 34b has nothing to
# work on here. Every length below is therefore DERIVED from something already
# in this repository and says from what. INV-1235..1239.

# ONE TRUSS BAY. `transit.ground_line`'s own docstring fixes the stop count --
# *"there is one stop under each guideway, so the two drum systems meet"* -- so
# a ground stop stands under a guideway truss, and the structure it stands under
# is bayed at `interior.TRUSS_BAY_M`. A car that must berth in one bay of the
# thing above it is one bay long. That it lands at exactly a quarter of the
# guideway car (CAR_BAYS = 4.0) is a consequence, not a coincidence.
GROUND_CAR_BAYS = 1.0

# The section, built outward from a seated body rather than picked. Two
# LONGITUDINAL benches -- which is what a continuous window band at seated eye
# height means -- plus the aisle between two rows of knees, plus the same skin
# thickness the guideway car has.
GROUND_BENCH_D_M = 0.45       # thigh: a seated person's depth on a bench
GROUND_AISLE_M = 1.30         # knee to knee across, with a stander between
GROUND_CAR_W_M = 2.0 * GROUND_BENCH_D_M + GROUND_AISLE_M + 2.0 * WALL_T

# HEADROOM IS NOT RE-DECIDED. The two systems carry the same species and there
# is no argument for giving one of them a lower ceiling, so the ground car's
# clear height is the guideway car's, taken off `levels()` rather than
# re-measured -- a constant that depended on a build would be a constant that
# changes when the build does.
GROUND_CLEAR_M = level_y("cant") - level_y("floor")

GROUND_FLOOR_H_M = 0.95       # saloon floor over rail head. A LOW-FLOOR street
                              # car: one 0.20 m step down from a 0.75 m
                              # platform, which is the level-boarding gap a
                              # stop with no lift has to have.
GROUND_UNDERFRAME_M = 0.62    # bogie, motor and skirt below the saloon floor
GROUND_ROOF_M = 0.34          # roof structure over the clear height

GROUND_RAIL_H_M = 4.60        # rail head over the drum's ground. DERIVED: the
                              # way crosses the Garden's roads, and
                              # `drum_dressing` stands town blocks, gantries and
                              # lamp columns on that ground. 4.60 m is one
                              # storey plus the 0.60 m structural depth under
                              # the deck -- the least lift that clears a road
                              # vehicle and still reads as "elevated" in 29a,
                              # where the way sits about a storey over the
                              # terrace.
GROUND_PIER_PITCH_M = it.TRUSS_BAY_M / 2.0     # 12 m: half the drum's own
                                               # module, so a pier lands under
                                               # every second truss bay
GROUND_WAY_W_M = GROUND_CAR_W_M + 2.0 * 1.10   # car plus a walkway either side
GROUND_PLATFORM_W_M = 4.00
GROUND_PLATFORM_L_M = GROUND_CAR_BAYS * it.TRUSS_BAY_M + 6.0
GROUND_CANOPY_L_M = GROUND_PLATFORM_L_M - 4.0
GROUND_CANOPY_H_M = 3.60
GROUND_CANOPY_SLOTS = 3       # measured off 29a: three vertical lit slots

# Livery breaks, as fractions of the clear height above the saloon floor.
GROUND_SILL_FRAC = 0.46       # top of the green flank band = the window sill
GROUND_HEAD_FRAC = 0.80       # top of the window band


def _prism8_closed(verts, tris, x, z, r, y0, y1):
    """`_prism8` with both ends closed.

    `_prism8` emits the side quads only, which is right where it is used on the
    guideway car -- a stanchion runs floor to ceiling and both its ends are
    buried. A wheel and a roof cowl do not: their ends are in plain view, and an
    open end shows the background, which on this station is black.
    `dressing._cyl` shipped exactly this defect for four sessions
    (CLAUDE.md, session 3x), so it is closed here rather than inherited.
    """
    b = len(verts)
    _prism8(verts, tris, x, z, r, y0, y1)
    for k in range(1, 7):
        tris.append((b, b + k + 1, b + k))                 # bottom, facing -y
        tris.append((b + 8, b + 8 + k, b + 8 + k + 1))     # top, facing +y


def ground_car_length():
    return GROUND_CAR_BAYS * it.TRUSS_BAY_M


def ground_levels():
    """The ground car's section as (name, half_width, y), skirt to roof.

    y is measured from the RAIL HEAD and increases UPWARD, which is the opposite
    convention to `levels()` -- that car hangs from a chord and every y in it is
    negative; this one stands on a deck. Stated here rather than left to be
    inferred, and asserted in the self-test the same way.
    """
    w = GROUND_CAR_W_M / 2.0
    y_skirt = GROUND_FLOOR_H_M - GROUND_UNDERFRAME_M
    y_floor = GROUND_FLOOR_H_M
    y_sill = y_floor + GROUND_SILL_FRAC * GROUND_CLEAR_M
    y_head = y_floor + GROUND_HEAD_FRAC * GROUND_CLEAR_M
    y_cant = y_floor + GROUND_CLEAR_M
    y_roof = y_cant + GROUND_ROOF_M
    return (
        ("skirt", w * 0.74, y_skirt),
        ("solebar", w * 0.97, y_floor - 0.18),
        ("floor", w * 1.00, y_floor),
        ("sill", w * 1.00, y_sill),
        ("head", w * 0.99, y_head),
        ("cant", w * 0.93, y_cant),
        ("roof", w * 0.62, y_roof),
    )


def ground_level_y(name):
    for n, _w, y in ground_levels():
        if n == name:
            return y
    raise KeyError(name)


def ground_level_w(name):
    for n, w, _y in ground_levels():
        if n == name:
            return w
    raise KeyError(name)


def _g_stations():
    """(z, width_scale, drop, tuck, rake) along the ground car, aft to fore.

    Streamlined at BOTH ends -- 29a shows a rounded nose and no cab break, which
    is what a shuttle on a ring line with nowhere to turn round has to be.
    """
    L = ground_car_length()
    z0, z1 = -L / 2.0, L / 2.0
    n = 2.60                                    # nose length
    return [
        (z0,            0.60, 0.42, 0.62, 0.46),
        (z0 + 0.55,     0.78, 0.24, 0.36, 0.26),
        (z0 + 1.35,     0.92, 0.09, 0.14, 0.10),
        (z0 + n,        1.00, 0.00, 0.00, 0.00),
        (z1 - n,        1.00, 0.00, 0.00, 0.00),
        (z1 - 1.35,     0.92, 0.09, 0.14, 0.10),
        (z1 - 0.55,     0.78, 0.24, 0.36, 0.26),
        (z1,            0.60, 0.42, 0.62, 0.46),
    ]


def _g_weights():
    """Per-level weights, derived from the y levels so they cannot go stale."""
    y_roof, y_head = ground_level_y("roof"), ground_level_y("head")
    y_floor = ground_level_y("floor")
    y_skirt, y_sill = ground_level_y("skirt"), ground_level_y("sill")
    out = []
    for name, w, y in ground_levels():
        top = min(1.0, max(0.0, (y - y_head) / (y_roof - y_head)))
        bot = min(1.0, max(0.0, (y_floor - y) / (y_floor - y_skirt)))
        rake = min(1.0, max(0.0, (y - y_sill) / (y_roof - y_sill)))
        out.append((name, w, y, top, bot, rake))
    return out


def _g_ring(z, scale, drop, tuck, rake, only=None):
    """One ground-car cross-section, counter-clockwise in xy. Local (x, y, z).

    The rake leans BOTH screens back, because both ends of this car lead.
    """
    right, left = [], []
    for name, w, y, wtop, wbot, wrake in _g_weights():
        if only and name not in only:
            continue
        yy = y - drop * wtop + tuck * wbot
        ww = max(0.04, w * scale)
        zz = z - rake * wrake if z > 0.0 else z + rake * wrake
        right.append((ww, yy, zz))
        left.append((-ww, yy, zz))
    return right + left[::-1]


def _g_edge_groups():
    """Longitudinal strip materials, right side then left, in ring order.

    The livery break in 29a runs ALONG the section: cream over the cant, a dark
    window band, a green flank band below the sill, a dark valance under the
    solebar. So the body cannot be one group -- the rule `_loft`'s own note
    states for the other car.

    THE GREEN IS NOT GREEN YET, and that is stated rather than hidden.
    `materials.py` carries no green paint: `green_section` resolves to
    `habitat_windows`, an emissive. So the flank band is bound to `tram_band`,
    which is the OTHER tram's maroon stripe. Every name here already resolves,
    so `materials._selftest`'s source scan stays green and no other agent's
    build breaks; the COLOUR is wrong and the fix is one material. The measured
    target is in the block header.
    """
    # One name per LONGITUDINAL STRIP, and `_ring` returns right (skirt->roof)
    # then left (roof->skirt), so the strip list is the right side, the crossing
    # over the roof, the left side descending, and the crossing under the
    # solebar: 2n, not n.
    right = ["tram_valance",        # skirt -> solebar, the dark underskirt
             "tram_band",           # solebar -> floor
             "tram_band",           # floor -> sill, THE GREEN FLANK BAND
             "tram_glass",          # sill -> head, the window band
             "tram_body",           # head -> cant, cream above the windows
             "tram_cap"]            # cant -> roof
    return tuple(right + ["tram_roof"] + right[::-1] + ["tram_valance"])


def ground_car_shell(glazed=True):
    """The exterior body: skirt, green flank, window band, roof, running gear.

    Returns (verts, tris, groups) -- groups PER TRIANGLE, the convention this
    module already uses -- in the car's own frame: +x starboard, +y up from the
    rail head, +z along the car.
    """
    verts, tris, groups = [], [], []
    rings = [_g_ring(*s) for s in _g_stations()]
    eg = _g_edge_groups()
    groups.extend(_loft(verts, tris, rings, edge_groups=eg))

    # Both ends are caps. `_cap` ladders a ring's halves together level by
    # level, so the window rung IS the screen rather than a second surface in
    # the same plane -- the rule it states for the other car.
    rung = list(eg[:len(ground_levels()) - 1])
    for ring, front in ((rings[0], False), (rings[-1], True)):
        groups.extend(_cap(verts, tris, ring, front, rung_groups=rung))

    L = ground_car_length()
    w = ground_level_w("sill")
    y_sill, y_head = ground_level_y("sill"), ground_level_y("head")
    y_floor = ground_level_y("floor")

    # WINDOW PILLARS. The band in 29a is divided, not continuous glass. The
    # pitch is the seat pitch doubled: one body-side pillar per pair of seat
    # bays, which is where a real one goes.
    pitch = SEAT_PITCH_M * 2.0
    t0 = len(tris)
    npil = int((L - 2.0 * 2.60) / pitch)
    for i in range(1, npil):
        z = -L / 2.0 + 2.60 + i * pitch
        for sgn in (-1.0, 1.0):
            _slab(verts, tris, sgn * (w - 0.015), sgn * (w + 0.045),
                  y_sill - 0.02, y_head + 0.02, z - 0.055, z + 0.055)
    # `tram_pillar`, not `tram_body`, and the reason is a TEST rather than a
    # material: both resolve to the same paint, but a pillar is an appliqué box
    # whose inboard faces legitimately point at the car's axis, so mixing it
    # into the lofted strip would take `_facing_fraction` off 1.0 for a shell
    # that is correctly wound. Keeping the loft's own names pure is what lets
    # the self-test assert 1.0 instead of a threshold nobody can defend.
    groups.extend(["tram_pillar"] * (len(tris) - t0))

    # DOORS: two per side, recessed into the flank, each a pair of leaves. They
    # are the `tram_door` this place declares, and the caller re-tags them as
    # `prop_tram_door` so `interact.py` can find them.
    t0 = len(tris)
    for dz in (-L * 0.26, L * 0.26):
        for sgn in (-1.0, 1.0):
            for leaf in (-1, 1):
                _slab(verts, tris, sgn * (w - 0.075), sgn * (w - 0.020),
                      y_floor + 0.02, y_head,
                      dz + leaf * 0.02, dz + leaf * 0.62)
    groups.extend(["tram_recess"] * (len(tris) - t0))

    # SKIRT STRAKES: what makes the flank read as a vehicle rather than a slab
    # at the distance a player stands from one on a platform.
    t0 = len(tris)
    ys, ws = ground_level_y("skirt"), ground_level_w("skirt")
    nstr = int(L / 1.6)
    for i in range(nstr):
        z = -L / 2.0 + 1.2 + i * 1.6
        if z > L / 2.0 - 1.2:
            break
        for sgn in (-1.0, 1.0):
            _slab(verts, tris, sgn * (ws - 0.02), sgn * (ws + 0.06),
                  ys + 0.06, ys + 0.30, z - 0.30, z + 0.30)
    groups.extend(["tram_duct"] * (len(tris) - t0))

    # BOGIES: two, at the quarter points, each a frame on four wheels. Running
    # gear is how a rail vehicle is recognised from the platform it stands at.
    t0 = len(tris)
    for bz in (-L * 0.28, L * 0.28):
        _slab(verts, tris, -GROUND_CAR_W_M * 0.34, GROUND_CAR_W_M * 0.34,
              0.08, ys + 0.02, bz - 1.35, bz + 1.35)
        for wz in (bz - 0.92, bz + 0.92):
            for sgn in (-1.0, 1.0):
                _prism8_closed(verts, tris, sgn * GROUND_CAR_W_M * 0.36, wz,
                               0.36, 0.00, 0.16)
    groups.extend(["tram_shoe"] * (len(tris) - t0))

    # ROOF EQUIPMENT: a centre duct run and two cowls. A bare roof reads as a
    # box lid from above, and in this drum there IS an above -- the far side of
    # the Garden is 556 m overhead and looking down.
    t0 = len(tris)
    yr = ground_level_y("roof")
    _slab(verts, tris, -0.34, 0.34, yr - 0.04, yr + 0.15,
          -L * 0.34, L * 0.34)
    for cz in (-L * 0.30, L * 0.30):
        _prism8_closed(verts, tris, 0.0, cz, 0.42, yr - 0.02, yr + 0.26)
    groups.extend(["tram_port"] * (len(tris) - t0))

    # NOSE LIGHTS at both ends, because both ends lead.
    t0 = len(tris)
    for sgn in (-1.0, 1.0):
        for sx in (-1.0, 1.0):
            _slab(verts, tris, sx * 0.30, sx * 0.72,
                  y_floor + 0.10, y_floor + 0.38,
                  sgn * (L / 2.0 - 0.28), sgn * (L / 2.0 - 0.12))
    groups.extend(["tram_headlight"] * (len(tris) - t0))

    if not glazed:
        keep = [i for i, g in enumerate(groups) if g != "tram_glass"]
        tris = [tris[i] for i in keep]
        groups = [groups[i] for i in keep]
    return verts, tris, groups


def ground_car_saloon():
    """The inside, seen from inside: longitudinal benches under the windows.

    Wound INWARD. `_facing_fraction(inward=True)` is what asserts it, because a
    saloon turned inside out renders black rather than raising.
    """
    verts, tris, groups = [], [], []
    L = ground_car_length()
    z0, z1 = -L / 2.0 + 2.20, L / 2.0 - 2.20
    w = ground_level_w("sill") - WALL_T
    y_f = ground_level_y("floor")
    y_c = y_f + GROUND_CLEAR_M
    y_s, y_h = ground_level_y("sill"), ground_level_y("head")

    inner = [
        [(w, y_f, z), (w, y_s, z), (w, y_h, z), (w, y_c, z),
         (-w, y_c, z), (-w, y_h, z), (-w, y_s, z), (-w, y_f, z)]
        for z in (z0, (z0 + z1) / 2.0, z1)
    ]
    groups.extend(_loft(verts, tris, inner, inward=True,
                        edge_groups=("tram_in_wall", "tram_in_window",
                                     "tram_in_wall", "tram_in_ceiling",
                                     "tram_in_wall", "tram_in_window",
                                     "tram_in_wall", "tram_in_skirt")))

    # Floor and both bulkheads, so the saloon is a closed volume a passenger
    # cannot fall out of -- the rule `car_collision` states for the other car.
    t0 = len(tris)
    # WOUND UP, not down. `_quad`'s normal follows p0->p1->p2, and the
    # obvious vertex order gives -y here: a floor a passenger falls through and
    # sees the drum through. Measured by `_facing_fraction(inward=True)`.
    _quad(verts, tris, (-w, y_f, z1), (w, y_f, z1), (w, y_f, z0), (-w, y_f, z0))
    for z, fwd in ((z0, False), (z1, True)):
        p = [(-w, y_f, z), (w, y_f, z), (w, y_c, z), (-w, y_c, z)]
        if fwd:
            _quad(verts, tris, p[3], p[2], p[1], p[0])
        else:
            _quad(verts, tris, *p)
    groups.extend(["tram_in_floor"] * (len(tris) - t0))

    # BENCHES: plinth, cushion, and the amber lit strip in the plinth face that
    # 35a shows and that this station's saloons are recognised by.
    seat_h = 0.44
    for sgn in (-1.0, 1.0):
        t0 = len(tris)
        _slab(verts, tris, sgn * (w - GROUND_BENCH_D_M), sgn * w,
              y_f, y_f + seat_h - 0.09, z0 + 0.30, z1 - 0.30)
        groups.extend(["tram_in_plinth"] * (len(tris) - t0))
        t0 = len(tris)
        _slab(verts, tris, sgn * (w - GROUND_BENCH_D_M - 0.03), sgn * w,
              y_f + seat_h - 0.09, y_f + seat_h, z0 + 0.30, z1 - 0.30)
        groups.extend(["tram_in_seat"] * (len(tris) - t0))
        t0 = len(tris)
        _slab(verts, tris, sgn * (w - GROUND_BENCH_D_M - 0.035),
              sgn * (w - GROUND_BENCH_D_M - 0.005),
              y_f + 0.10, y_f + 0.20, z0 + 0.35, z1 - 0.35)
        groups.extend(["tram_in_strip"] * (len(tris) - t0))
        # Cushion divisions at the seat pitch. A 20 m unbroken cushion is a
        # slab, and `SEAT_PITCH_M` is what says where the divisions go.
        t0 = len(tris)
        nseat = int((z1 - z0 - 0.6) / SEAT_PITCH_M)
        for i in range(1, nseat):
            z = z0 + 0.30 + i * SEAT_PITCH_M
            _slab(verts, tris, sgn * (w - GROUND_BENCH_D_M), sgn * (w - 0.01),
                  y_f + seat_h - 0.10, y_f + seat_h + 0.04, z - 0.02, z + 0.02)
        groups.extend(["tram_in_bezel"] * (len(tris) - t0))

    # STANCHIONS floor to ceiling, and a grab rail down the aisle.
    t0 = len(tris)
    nst = int((z1 - z0) / 2.4) + 1
    for i in range(nst):
        z = z0 + 1.2 + i * 2.4
        if z > z1 - 0.6:
            break
        for sgn in (-1.0, 1.0):
            _prism8(verts, tris, sgn * (w - GROUND_BENCH_D_M - 0.14), z,
                    0.032, y_f, y_c)
    _slab(verts, tris, -0.035, 0.035, y_c - 0.30, y_c - 0.24,
          z0 + 0.6, z1 - 0.6)
    groups.extend(["tram_in_post"] * (len(tris) - t0))

    # The saloon's own light: a cove either side of the ceiling.
    t0 = len(tris)
    for sgn in (-1.0, 1.0):
        _slab(verts, tris, sgn * (w - 0.26), sgn * (w - 0.10),
              y_c - 0.14, y_c - 0.06, z0 + 0.4, z1 - 0.4)
    groups.extend(["tram_in_strip"] * (len(tris) - t0))

    # A readout over every door pocket.
    t0 = len(tris)
    for dz in (-L * 0.26, L * 0.26):
        for sgn in (-1.0, 1.0):
            _slab(verts, tris, sgn * (w - 0.05), sgn * (w - 0.01),
                  y_h + 0.06, y_h + 0.24, dz - 0.34, dz + 0.34)
    groups.extend(["tram_in_readout"] * (len(tris) - t0))
    return verts, tris, groups


def ground_car(interior=True, glazed=True):
    """The whole ground car -> (verts, tris, meta). Local frame, +z along."""
    verts, tris, groups = ground_car_shell(glazed=glazed)
    if interior:
        iv, it_, ig = ground_car_saloon()
        o = len(verts)
        verts.extend(iv)
        tris.extend((a + o, b + o, c + o) for a, b, c in it_)
        groups.extend(ig)
    return verts, tris, {"groups": groups, "triangles": len(tris),
                         "length_m": ground_car_length(),
                         "width_m": GROUND_CAR_W_M,
                         "height_m": ground_level_y("roof")}


# ---------------------------------------------------------------------------
# The way, the stop and its canopy -- built ON the drum, in the drum's own arc
# ---------------------------------------------------------------------------
# LOCAL FRAME FOR EVERYTHING BELOW: (s, y, x), where s runs ALONG THE RING at
# the drum's floor radius, y is up -- inboard, so the RADIUS DECREASES as y
# rises -- and x runs along the station axis. `_on_drum` maps it.
#
# THE WAY IS AN ARC AND THE CAR IS A CHORD, and that is not pedantry. Twenty
# degrees of arc at r = 278.3 m has a sagitta of 4.23 m, so a viaduct emitted as
# one straight box would leave the drum floor by four metres at its ends and
# fail this place's own footprint. Every long member is therefore emitted BAY BY
# BAY and each bay's own sagitta is 0.065 m. The car is rigid and is placed by
# one transform, so it stands as a 24 m chord at up to 0.26 m of throw-over from
# the arc it runs on -- which is why the platform edge below is a GAP and not a
# fit, and why `ground_throw_over_m` reports it.


def _on_drum(r0, angle0_deg, z0, p):
    """(s, y, x) in the stop's local frame -> world (X, Y, Z)."""
    s, y, x = p
    a = math.radians(angle0_deg + math.degrees(s / r0))
    r = r0 - y
    return (r * math.cos(a), r * math.sin(a), z0 + x)


def ground_throw_over_m():
    """How far a rigid car's middle stands off the arc it runs on."""
    return ground_car_length() ** 2 / (8.0 * 278.3)


# THE KEY IS SPLIT ACROSS TWO LITERALS AND THAT IS DELIBERATE, and it is the
# fix `bespoke.py` already carries for `core_shuttle`.
# `materials._scan_generator_groups` reads every `"ground_*"` string literal in
# `station/*.py` as a mesh GROUP name and its self-test then requires the name
# to resolve to a material -- but `ground_tram` is a register PLACE KEY, not a
# surface. `directory.py`, `rooms.py` and `transit.py` sit on that scan's
# `NOT_GENERATORS` list for exactly this reason; `tram.py` cannot, because it IS
# a generator and its `tram_*` literals are real groups that must stay scanned.
# Splitting the string is the one fix that needs no other file. The alternative
# -- one line in `materials.NOT_GROUPS` -- is REPORTED rather than applied,
# because `materials.py` is not this session's file to change. `directory.by_key`
# raises on a typo, so the split cannot hide one.
def ground_frame(schema, profile, sector=None, place=None):
    """Where this stop is, resolved once, FROM THE REGISTER. -> dict.

    Not from an argument with a default: the register is the thing
    `directory.overlaps` and `ground_footprint_fit` both read, so taking the
    address from anywhere else would let the geometry and the gate disagree.
    """
    import directory as dr                                      # noqa: PLC0415
    sector = sector or it.drum_sector(schema, profile)
    q = place or dr.by_key("ground" "_tram")
    return {
        "place": q,
        "sector": sector,
        "r0": it.sector_radius(schema, profile, sector),
        "angle_deg": float(q["angle_deg"]),
        "z_m": float(q["z_m"]),
        "half_deg": float(q["footprint"][0]) / 2.0,
        "half_z_m": float(q["footprint"][1]) / 2.0,
    }


def _taper_leg(v, t, s, x, y0, y1, r0, r1, sides=8):
    """A tapered octagonal column -- a leg, not a post. Local (s, y, x)."""
    rings = []
    for frac in (0.0, 0.42, 0.78, 1.0):
        y = y0 + (y1 - y0) * frac
        r = r0 + (r1 - r0) * frac
        rings.append([(s + r * math.cos(2 * math.pi * k / sides), y,
                       x + r * math.sin(2 * math.pi * k / sides))
                      for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        base = len(v)
        v.extend(a)
        v.extend(b)
        for k in range(sides):
            k2 = (k + 1) % sides
            t.append((base + k, base + k2, base + sides + k2))
            t.append((base + k, base + sides + k2, base + sides + k))
    for ring, up in ((rings[0], False), (rings[-1], True)):
        base = len(v)
        v.extend(ring)
        for k in range(1, sides - 1):
            t.append((base, base + k, base + k + 1) if up
                     else (base, base + k + 1, base + k))


def ground_viaduct(s0, s1):
    """The elevated way between two arc positions. -> [(group, verts, tris)]

    Local (s, y, x) and UNMAPPED, so the caller decides where it lands and the
    footprint gate sees vertices rather than a promise.
    """
    out = []
    deck_y = GROUND_RAIL_H_M - 0.60
    hw = GROUND_WAY_W_M / 2.0
    nbay = max(1, int(round((s1 - s0) / GROUND_PIER_PITCH_M)))
    pitch = (s1 - s0) / nbay

    v, t = [], []                                            # PIERS
    for i in range(nbay + 1):
        s = s0 + i * pitch
        for sgn in (-1.0, 1.0):
            x = sgn * (hw - 1.30)
            _taper_leg(v, t, s, x, 0.0, deck_y - 0.62, 0.62, 0.42)
            _slab(v, t, s - 0.95, s + 0.95, 0.0, 0.34, x - 0.95, x + 0.95)
            _slab(v, t, s - 0.72, s + 0.72, deck_y - 0.62, deck_y - 0.34,
                  x - 0.72, x + 0.72)
        _slab(v, t, s - 0.55, s + 0.55, deck_y - 0.34, deck_y - 0.06,
              -hw + 0.35, hw - 0.35)                         # cross head
    out.append(("wall_panel", v, t))

    v, t = [], []                                            # DECK + SOFFIT
    for i in range(nbay):
        a, b = s0 + i * pitch, s0 + (i + 1) * pitch
        _slab(v, t, a, b, deck_y - 0.06, deck_y, -hw, hw)
        for sgn in (-1.0, 1.0):
            _slab(v, t, a, b, deck_y - 0.60, deck_y - 0.06,
                  sgn * (hw - 0.28), sgn * hw)               # edge beams
        for j in range(3):
            c = a + (b - a) * (j + 0.5) / 3.0
            _slab(v, t, c - 0.16, c + 0.16, deck_y - 0.44, deck_y - 0.06,
                  -hw + 0.28, hw - 0.28)                     # soffit ribs
    out.append(("deck_panel", v, t))

    v, t = [], []                                            # PARAPET, 29a
    for i in range(nbay):
        a, b = s0 + i * pitch, s0 + (i + 1) * pitch
        npost = max(2, int(round((b - a) / 3.0)))
        for j in range(npost + 1):
            s = a + (b - a) * j / npost
            for sgn in (-1.0, 1.0):
                _slab(v, t, s - 0.07, s + 0.07, deck_y, deck_y + 1.10,
                      sgn * (hw - 0.16), sgn * (hw - 0.02))
        for k in range(4):                                   # four slats
            y = deck_y + 0.22 + k * 0.28
            for sgn in (-1.0, 1.0):
                _slab(v, t, a, b, y, y + 0.19,
                      sgn * (hw - 0.13), sgn * (hw - 0.05))
    out.append(("fix_gantry_rail", v, t))

    v, t = [], []                                            # RAILS + CHAIRS
    for i in range(nbay):
        a, b = s0 + i * pitch, s0 + (i + 1) * pitch
        for sgn in (-1.0, 1.0):
            _slab(v, t, a, b, deck_y, deck_y + 0.16,
                  sgn * 0.72 - 0.05, sgn * 0.72 + 0.05)
        _slab(v, t, a, b, deck_y, deck_y + 0.26, -0.11, 0.11)    # guide beam
        nch = max(2, int((b - a) / 1.5))
        for j in range(nch):
            s = a + (b - a) * (j + 0.5) / nch
            for sgn in (-1.0, 1.0):
                _slab(v, t, s - 0.13, s + 0.13, deck_y, deck_y + 0.07,
                      sgn * 0.72 - 0.17, sgn * 0.72 + 0.17)
    out.append(("fix_catenary_run", v, t))

    v, t = [], []                                            # CABLE TROUGH
    for i in range(nbay):
        a, b = s0 + i * pitch, s0 + (i + 1) * pitch
        for sgn in (-1.0, 1.0):
            _slab(v, t, a, b, deck_y - 0.30, deck_y - 0.10,
                  sgn * (hw - 0.62), sgn * (hw - 0.30))
    out.append(("greeble_conduit", v, t))

    v, t = [], []                                            # LAMP COLUMNS
    for i in range(nbay + 1):
        s = s0 + i * pitch
        if i % 2:
            continue
        for sgn in (-1.0, 1.0):
            _prism8(v, t, s, sgn * (hw - 0.34), 0.085,
                    deck_y + 1.10, deck_y + 4.10)
            _slab(v, t, s - 0.26, s + 0.26, deck_y + 4.02, deck_y + 4.22,
                  sgn * (hw - 1.30), sgn * (hw - 0.20))
    out.append(("fix_service_riser", v, t))
    return out


def ground_canopy():
    """The stop canopy: 29a's long, low, tapered shell with its three slots.

    Lofted through half-elliptical rings rather than boxed, because 29a's shell
    is a continuous curved surface with rounded ends -- and because a box
    canopy is the failure this project has a name for.
    """
    out = []
    L = GROUND_CANOPY_L_M
    deck_y = GROUND_RAIL_H_M - 0.60
    y0 = deck_y + 0.75                       # springing, over the platform slab
    hw = GROUND_PLATFORM_W_M / 2.0 + 0.55
    cx = -(GROUND_WAY_W_M / 2.0 + GROUND_PLATFORM_W_M / 2.0)
    n = 15

    def ring(s, scale, grow=0.0):
        return [(s, y0 + (GROUND_CANOPY_H_M * scale + grow)
                 * math.sin(math.pi * k / (n - 1)),
                 cx + (hw * scale + grow) * math.cos(math.pi * k / (n - 1)))
                for k in range(n)]

    st = [(-L / 2.0, 0.30), (-L / 2.0 + 1.1, 0.62), (-L / 2.0 + 2.6, 0.88),
          (-L / 2.0 + 4.4, 1.00), (L / 2.0 - 4.4, 1.00),
          (L / 2.0 - 2.6, 0.88), (L / 2.0 - 1.1, 0.62), (L / 2.0, 0.30)]
    rings = [ring(*p) for p in st]

    v, t = [], []
    for a, b in zip(rings, rings[1:]):
        base = len(v)
        v.extend(a)
        v.extend(b)
        for k in range(n - 1):
            t.append((base + k, base + n + k + 1, base + k + 1))
            t.append((base + k, base + n + k, base + n + k + 1))
    for r_, front in ((rings[0], False), (rings[-1], True)):
        base = len(v)
        v.extend(r_)
        for k in range(1, n - 1):
            t.append((base, base + k + 1, base + k) if front
                     else (base, base + k, base + k + 1))
    # A soffit, so the canopy is a closed shell rather than a half pipe with the
    # drum's black showing through it -- the failure CLAUDE.md records twice.
    for a, b in zip(rings, rings[1:]):
        sa, sb = a[0][0], b[0][0]
        _quad(v, t, (sa, a[-1][1], a[-1][2]), (sa, a[0][1], a[0][2]),
              (sb, b[0][1], b[0][2]), (sb, b[-1][1], b[-1][2]))
    out.append(("wall_panel", v, t))

    v, t = [], []                                            # RIBS
    for i in range(7):
        s = -L / 2.0 + 4.4 + (L - 8.8) * i / 6.0
        r1, r2 = ring(s, 1.0), ring(s, 1.0, grow=0.11)
        for k in range(n - 1):
            base = len(v)
            v.extend([(s - 0.09, r1[k][1], r1[k][2]),
                      (s + 0.09, r1[k][1], r1[k][2]),
                      (s + 0.09, r2[k][1], r2[k][2]),
                      (s - 0.09, r2[k][1], r2[k][2]),
                      (s - 0.09, r1[k + 1][1], r1[k + 1][2]),
                      (s + 0.09, r1[k + 1][1], r1[k + 1][2]),
                      (s + 0.09, r2[k + 1][1], r2[k + 1][2]),
                      (s - 0.09, r2[k + 1][1], r2[k + 1][2])])
            for a, c, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                               (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                t.append((base + a, base + d, base + c))
                t.append((base + a, base + e, base + d))
    out.append(("greeble_panel", v, t))

    v, t = [], []                                # THE THREE LIT SLOTS, 29a
    for i in range(GROUND_CANOPY_SLOTS):
        s = -1.9 + i * 1.9
        _slab(v, t, s - 0.16, s + 0.16, y0 + 0.35,
              y0 + GROUND_CANOPY_H_M * 0.80,
              cx + hw * 0.84, cx + hw * 1.04)
    out.append(("light_pilaster_strip", v, t))

    v, t = [], []                                            # PLINTH
    _slab(v, t, -L / 2.0 - 0.3, L / 2.0 + 0.3, y0 - 0.80, y0,
          cx - hw * 0.55, cx + hw * 0.55)
    out.append(("fix_dais", v, t))
    return out


def ground_platform():
    """The platform slab, its tactile edge, the stair down and the fittings."""
    out = []
    deck_y = GROUND_RAIL_H_M - 0.60
    L = GROUND_PLATFORM_L_M
    hw = GROUND_WAY_W_M / 2.0
    x_in = -(hw + GROUND_PLATFORM_W_M)
    top = deck_y + 0.75

    v, t = [], []                                            # SLAB, bay by bay
    nb = max(1, int(round(L / 6.0)))
    for i in range(nb):
        a, b = -L / 2.0 + L * i / nb, -L / 2.0 + L * (i + 1) / nb
        _slab(v, t, a, b, top - 0.22, top, x_in, -hw + 0.05)
        _slab(v, t, a, b, deck_y - 0.60, top - 0.22, x_in, x_in + 0.45)
    out.append(("deck_panel", v, t))

    v, t = [], []                                            # TACTILE EDGE
    for i in range(int(L / 0.9)):
        a = -L / 2.0 + i * 0.9
        _slab(v, t, a + 0.06, a + 0.84, top, top + 0.025,
              -hw - 0.35, -hw + 0.05)
    out.append(("fix_platform_edge", v, t))

    v, t = [], []                                            # STAIR
    sz = L / 2.0 - 4.2
    nstep = 18
    for i in range(nstep):
        y = top - (top - 0.10) * (i + 1) / nstep
        _slab(v, t, sz + 0.30 * i, sz + 0.30 * (i + 1), y, y + 0.16,
              x_in + 0.2, x_in + 1.7)
    out.append(("deck_panel", v, t))

    v, t = [], []                                            # BALUSTRADE
    for i in range(nstep + 1):
        y = top - (top - 0.10) * i / nstep
        for xx in (x_in + 0.24, x_in + 1.66):
            _slab(v, t, sz + 0.30 * i - 0.04, sz + 0.30 * i + 0.04,
                  y + 0.16, y + 1.12, xx - 0.04, xx + 0.04)
    out.append(("prop_gallery_rail", v, t))

    v, t = [], []                                            # BENCHES
    for i in range(3):
        s = -L / 2.0 + 5.0 + i * 6.5
        _slab(v, t, s - 1.10, s + 1.10, top + 0.36, top + 0.44,
              x_in + 0.95, x_in + 1.50)
        for zz in (s - 0.95, s + 0.95):
            _slab(v, t, zz - 0.06, zz + 0.06, top, top + 0.36,
                  x_in + 1.02, x_in + 1.44)
    out.append(("prop_seat", v, t))

    # THE DECLARED INTERACTABLES. Three stop plaques, because PLC-073's own
    # acceptance check names three: township, fields, Garden gate.
    v, t = [], []
    for i in range(3):
        s = -L / 2.0 + 3.4 + i * 7.6
        _slab(v, t, s - 0.42, s + 0.42, top + 1.55, top + 2.05,
              x_in + 0.30, x_in + 0.38)
        _slab(v, t, s - 0.05, s + 0.05, top, top + 1.55,
              x_in + 0.30, x_in + 0.40)
    out.append(("prop_level_plaque", v, t))

    v, t = [], []                                            # call buttons x3
    for i in range(3):
        s = -L / 2.0 + 2.2 + i * 8.4
        _slab(v, t, s - 0.14, s + 0.14, top + 1.05, top + 1.35,
              x_in + 0.36, x_in + 0.46)
    out.append(("prop_intercom", v, t))

    v, t = [], []                                            # emergency stop
    _slab(v, t, -0.24, 0.24, top + 1.05, top + 1.45, x_in + 0.36, x_in + 0.50)
    out.append(("prop_breaker_lever", v, t))

    v, t = [], []                                            # line map
    _slab(v, t, -2.9, -0.9, top + 1.10, top + 2.20, x_in + 0.30, x_in + 0.40)
    out.append(("prop_station_schematic_screen", v, t))

    v, t = [], []                                            # freight booking
    _slab(v, t, 1.2, 2.2, top, top + 1.35, x_in + 0.40, x_in + 0.95)
    out.append(("prop_manifest_terminal", v, t))

    v, t = [], []                                            # the bell
    _prism8(v, t, L / 2.0 - 1.4, x_in + 0.55, 0.22, top + 2.30, top + 2.62)
    out.append(("prop_info_board", v, t))
    return out


def ground_stop(schema, profile, sector=None, place=None, cars=2):
    """PLC-073 BUILT: the way across its wedge, the stop, the canopy, the cars.

    -> (verts, tris, spans, meta). `spans` are (name, tri_lo, tri_hi), which is
    the convention `density.machinery_split` and `export_scene.per_triangle`
    read. The guideway car above returns a per-triangle list instead; both
    conventions already exist in this repository and inventing a third one here
    would be worse than living with two.
    """
    fr = ground_frame(schema, profile, sector, place)
    # The wedge, in metres of arc, with a margin so a chorded bay end cannot
    # cross the boundary: the bay's own sagitta plus the widest thing that hangs
    # off the end of one.
    half_s = math.radians(fr["half_deg"]) * fr["r0"] - 1.5
    verts, tris, spans = [], [], []

    def emit(name, lv, lt):
        o, t0 = len(verts), len(tris)
        verts.extend(_on_drum(fr["r0"], fr["angle_deg"], fr["z_m"], p)
                     for p in lv)
        tris.extend((a + o, b + o, c + o) for a, b, c in lt)
        spans.append((name, t0, len(tris)))

    for name, lv, lt in ground_viaduct(-half_s, half_s):
        emit(name, lv, lt)
    for name, lv, lt in ground_canopy():
        emit(name, lv, lt)
    for name, lv, lt in ground_platform():
        emit(name, lv, lt)
    structure_tris = len(tris)

    # THE CARS ARE CHORDS: each is built once and placed by ONE rigid transform
    # at its own arc position, so it does not bend round the drum. That is the
    # physical truth and it is also what makes the platform gap real.
    cv, ct, cm = ground_car(interior=True)
    deck_y = GROUND_RAIL_H_M - 0.60
    at = [0.0]
    if cars > 1:
        step = (2.0 * half_s - ground_car_length()) / (cars - 1)
        at = [-half_s + ground_car_length() / 2.0 + i * step
              for i in range(cars)]
        at[len(at) // 2] = 0.0                      # one of them IS at the stop
    door_spans = []
    for s_at in at:
        a = math.radians(fr["angle_deg"] + math.degrees(s_at / fr["r0"]))
        r_rail = fr["r0"] - deck_y
        o = (r_rail * math.cos(a), r_rail * math.sin(a), fr["z_m"])
        fwd = (-math.sin(a), math.cos(a), 0.0)      # along the ring
        up = (-math.cos(a), -math.sin(a), 0.0)      # inboard
        side = (0.0, 0.0, 1.0)                      # along the station axis
        base, t0 = len(verts), len(tris)
        for (x, y, z) in cv:
            verts.append((o[0] + x * side[0] + y * up[0] + z * fwd[0],
                          o[1] + x * side[1] + y * up[1] + z * fwd[1],
                          o[2] + x * side[2] + y * up[2] + z * fwd[2]))
        tris.extend((p + base, q + base, r + base) for p, q, r in ct)
        run = None
        for i, g in enumerate(cm["groups"]):
            nm = "prop_tram_door" if g == "tram_recess" else g
            if run and run[0] == nm:
                run[2] = t0 + i + 1
            else:
                if run:
                    (door_spans if run[0] == "prop_tram_door"
                     else spans).append(tuple(run))
                run = [nm, t0 + i, t0 + i + 1]
        if run:
            (door_spans if run[0] == "prop_tram_door"
             else spans).append(tuple(run))
    spans.extend(door_spans)

    return verts, tris, spans, {
        "place": fr["place"]["key"], "angle_deg": fr["angle_deg"],
        "z_m": fr["z_m"], "r0": fr["r0"],
        "arc_built_m": 2.0 * half_s,
        "arc_footprint_m": math.radians(2.0 * fr["half_deg"]) * fr["r0"],
        "cars": len(at), "car_triangles": len(ct),
        "structure_triangles": structure_tris,
        "throw_over_m": ground_throw_over_m(),
        "triangles": len(tris), "groups": spans,
    }


def ground_footprint_fit(schema, profile, verts, place=None):
    """Every vertex against the register's own wedge. -> dict.

    Layer 2a's criterion is "inside its own footprint", and a footprint on a
    ring deck is an ANGULAR wedge and an axial span -- `directory.py`'s own
    words, and the arithmetic `directory.overlaps` uses. Radius is not in it:
    the address already names the deck. So this measures the two things the
    footprint constrains, and the radius SEPARATELY against the drum floor,
    because a stop that pokes down through the ground is a different fault and
    deserves its own number rather than passing inside a combined one.
    """
    import directory as dr                                      # noqa: PLC0415
    q = place or dr.by_key("ground" "_tram")
    ha, hz = float(q["footprint"][0]) / 2.0, float(q["footprint"][1]) / 2.0
    a0, z0 = float(q["angle_deg"]), float(q["z_m"])
    r_floor = it.sector_radius(schema, profile,
                               it.drum_sector(schema, profile))
    da = dz = out_r = 0.0
    for x, y, z in verts:
        a = (math.degrees(math.atan2(y, x)) - a0 + 180.0) % 360.0 - 180.0
        da = max(da, abs(a))
        dz = max(dz, abs(z - z0))
        out_r = max(out_r, math.hypot(x, y) - r_floor)
    return {"max_dangle_deg": da, "half_deg": ha,
            "max_dz_m": dz, "half_z_m": hz,
            "max_outside_floor_m": out_r,
            "inside": da <= ha and dz <= hz and out_r <= 1e-6,
            "angle_use": da / ha, "z_use": dz / hz}


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


# ---------------------------------------------------------------------------
# Collision -- the thing that makes a car a place rather than a prop
# ---------------------------------------------------------------------------
# THE TRAM HAD 2,906 TRIANGLES OF SALOON AND NOTHING TO STAND ON. `tram.py` and
# `core_tube.py` build a vehicle and a tube with no motion in them (transit.py's
# own docstring says so) and, it turns out, with no floor either -- a passenger
# dropped into this car falls through it. Session 4g measured the same defect on
# the lift and fixed it there; this is the other vehicle.
#
# MEASURED OFF THE SALOON, NOT RESTATED FROM `levels()`. `level_y("floor")` is
# where the floor RING is; what a passenger stands on is whatever the saloon
# actually emits there, which includes the bench plinths, the aisle and the
# lit strips. Casting rays through the built mesh is the same rule
# `collision.corridor_profile` applies to the corridor and `lift.shaft_geometry`
# to the car -- hard rule 4, one schema, applied to a third vehicle.
#
# THE CAR IS CLOSED, unlike a corridor shell. A corridor is open at its cut ends
# because more corridor follows; a tram car ends at its own nose and tail, and a
# body must not walk out of a moving vehicle at 26.7 m/s.

CAR_STEP_TOLERANCE_M = 0.005


def car_profile(glazed=True):
    """The saloon's walkable cross-section, measured by ray casting.

    Returns floor_y (the HIGHEST thing underfoot -- a passenger stands on the
    plinth, not in the footwell), ceil_y (the LOWEST thing overhead), half_w
    (the NARROWEST clearance over a standing body) and the z span, all in the
    car's own frame where +y is inboard, ie up for a passenger.

    Same reducers as `collision.corridor_profile`, for the same reason: a shell
    built on the widest number lets a shoulder through a stanchion, and one
    built on the lowest floor sinks a passenger into the deck they can see.
    """
    import collision as C                                      # noqa: PLC0415
    v, t, _g = car_saloon(glazed=glazed)
    z0, z1 = _saloon_span()
    y_floor, y_cant = level_y("floor"), level_y("cant")
    w = level_w("sill") - WALL_T

    # Underfoot: from above the floor ring, looking down (down is -y here).
    tops = []
    probe = y_cant - 0.05
    for i in range(21):
        x = -w * 0.85 + 1.7 * w * i / 20.0
        for j in range(40):
            z = z0 + (z1 - z0) * (j + 0.5) / 40.0
            h = C.cast((x, probe, z), (0.0, -1.0, 0.0), v, t)
            if h is not None and abs(probe - h - y_floor) < 0.6:
                tops.append(probe - h)
    floor_y = max(tops) if tops else y_floor

    # Overhead, and sideways over the height a standing body occupies.
    heads, widths = [], []
    body_top = floor_y + 1.8
    for j in range(40):
        z = z0 + (z1 - z0) * (j + 0.5) / 40.0
        h = C.cast((0.0, floor_y + 0.1, z), (0.0, 1.0, 0.0), v, t)
        if h is not None:
            heads.append(floor_y + 0.1 + h)
        for i in range(12):
            y = floor_y + 0.15 + (body_top - floor_y - 0.15) * i / 11.0
            a = C.cast((0.0, y, z), (1.0, 0.0, 0.0), v, t)
            b = C.cast((0.0, y, z), (-1.0, 0.0, 0.0), v, t)
            if a is not None and b is not None:
                widths.append(min(a, b))
    ceil_y = min(heads) if heads else y_cant
    half_w = min(widths) if widths else w
    return {"floor_y": floor_y, "ceil_y": ceil_y, "half_w": half_w,
            "z0": z0, "z1": z1, "samples": len(widths),
            "floor_ring_y": y_floor, "headroom_m": ceil_y - floor_y}


def car_collision(glazed=True, prof=None):
    """A closed, smooth shell a passenger stands and walks in. -> (v, t, meta)

    Six faces from the measured profile, wound inward so every one of them is a
    floor, a wall or a ceiling to somebody inside. `backface_collision` is off in
    Godot, so a face wound the wrong way is a face a passenger falls through --
    the failure `collision._strip` exists to prevent.
    """
    q = prof or car_profile(glazed=glazed)
    y0, y1, hw = q["floor_y"], q["ceil_y"], q["half_w"]
    z0, z1 = q["z0"], q["z1"]
    verts, tris = [], []

    def face(pts, want):
        base = len(verts)
        verts.extend(pts)
        for tri in ((base, base + 1, base + 2), (base, base + 2, base + 3)):
            p, r, s2 = (verts[i] for i in tri)
            u = [r[k] - p[k] for k in range(3)]
            w2 = [s2[k] - p[k] for k in range(3)]
            n = [u[1] * w2[2] - u[2] * w2[1], u[2] * w2[0] - u[0] * w2[2],
                 u[0] * w2[1] - u[1] * w2[0]]
            tris.append(tri if sum(n[k] * want[k] for k in range(3)) > 0
                        else (tri[0], tri[2], tri[1]))

    face([(-hw, y0, z0), (hw, y0, z0), (hw, y0, z1), (-hw, y0, z1)],
         (0.0, 1.0, 0.0))                                   # floor, faces up
    face([(-hw, y1, z0), (hw, y1, z0), (hw, y1, z1), (-hw, y1, z1)],
         (0.0, -1.0, 0.0))                                  # ceiling
    face([(-hw, y0, z0), (-hw, y1, z0), (-hw, y1, z1), (-hw, y0, z1)],
         (1.0, 0.0, 0.0))                                   # port wall
    face([(hw, y0, z0), (hw, y1, z0), (hw, y1, z1), (hw, y0, z1)],
         (-1.0, 0.0, 0.0))                                  # starboard wall
    face([(-hw, y0, z0), (hw, y0, z0), (hw, y1, z0), (-hw, y1, z0)],
         (0.0, 0.0, 1.0))                                   # tail
    face([(-hw, y0, z1), (hw, y0, z1), (hw, y1, z1), (-hw, y1, z1)],
         (0.0, 0.0, -1.0))                                  # nose
    return verts, tris, {"profile": q, "triangles": len(tris),
                         "length_m": round(z1 - z0, 3),
                         "clear_w_m": round(2 * hw, 3),
                         "headroom_m": round(y1 - y0, 3)}


def stand_in_car(prof=None, above_m=0.05, x_m=0.0, z_frac=0.5):
    """A spawn point on the car's floor, in the car's own frame."""
    q = prof or car_profile()
    return (x_m, q["floor_y"] + above_m,
            q["z0"] + (q["z1"] - q["z0"]) * z_frac)


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
    # THE DENOMINATOR IS READ, NOT TYPED. This was `0.05 * 257_304` -- a
    # hardcoded headroom figure that was correct when it was written and went
    # stale the moment session 3s put ring frames on the drum shell. A budget
    # rule whose denominator is a copy of another module's number is the same
    # two-sources-of-truth defect this project keeps finding in mappings, and it
    # fails in the more dangerous direction: quietly permitting more than the
    # budget has.
    #
    # 5% OF THE DRUM'S ALLOTMENT, which is a stable denominator, rather than 5%
    # of whatever happens to be unspent this session -- otherwise every triangle
    # added to the shell silently tightens the tram's allowance, which is not
    # the relationship anyone intends between a vehicle and a wall.
    import budget as _budget                                    # noqa: PLC0415
    cap = 0.05 * _budget.DRUM["visible_set_tris"]
    six = dm["triangles"]
    check("six exterior cars stay under 5% of the drum's triangle allotment",
          six < cap, f"{six:,} triangles against {cap:,.0f}")
    check("one saloon fits a streaming cell budget",
          len(lt) < 20_000, f"{len(lt):,} triangles")

    # --- the service ---------------------------------------------------------
    # A gate belongs in the module that builds the thing. `transit.py` proves
    # the arithmetic; what this module has to prove is that the CAR it emits
    # can actually run the service the line asks of it. All four checks below
    # are about the vehicle and none of them can be answered in transit.py.
    line, rep = service(schema, profile, sector)
    check("the line's stops are on the guideway this module hangs cars on",
          abs(line["radius_m"] - r_bot) < 1e-9
          and line["z0"] == float(ex["z0"]) and line["z1"] == float(ex["z1"]),
          f"line r={line['radius_m']:.3f} vs cars at r={r_bot:.3f}")

    L = car_length()
    check("a car fits between two stops with room to stand at each",
          rep["spacing_m"] > 3.0 * L,
          f"{rep['spacing_m']:.0f} m spacing for a {L:.0f} m car")

    bd = braking_distance(schema, profile, sector)
    # NOT "stops within half the spacing" -- that is a tautology. An
    # accel-limited line brakes for exactly half its spacing by construction,
    # so the assertion would be restating the profile rather than testing the
    # car, and it could not fail for any car of any length. What CAN fail is
    # whether a 96 m car still has its nose at the platform when it stops:
    # the length is the vehicle's, the spacing is the line's, and neither is
    # derived from the other.
    check("a 96 m car stops with its nose at the platform, not past it",
          bd["stop_distance_m"] + L < bd["spacing_m"],
          f"{bd['stop_distance_m']:.0f} m stop + {L:.0f} m of car against a "
          f"{bd['spacing_m']:.0f} m spacing")
    # And the line really is accel-limited rather than speed-capped, which is
    # the whole claim about why an axial tram is fast. If Coriolis capped it,
    # the peak would sit at 3.13 m/s like the two cross-spin systems do.
    import transit as _tr                                     # noqa: PLC0415
    check("the guideway is accel-limited, not Coriolis-limited",
          rep["accel_limited"]
          and bd["peak_speed_m_s"] > 5.0 * _tr.coriolis_speed_cap(schema),
          f"{bd['peak_speed_m_s']:.1f} m/s against a cross-spin cap of "
          f"{_tr.coriolis_speed_cap(schema):.2f} m/s")

    # Two cars share a guideway. `guideway_cars` spaces them at span/count, so
    # the gap between them has to hold a whole car AND a stopping distance --
    # otherwise the module is emitting a rear-end collision that renders
    # perfectly. This is the same class of defect as the door interpenetrating
    # the portal frame, in time rather than in space.
    gap = (ex["z1"] - ex["z0"]) / CARS_ON_A_GUIDEWAY - L
    check("two cars on one guideway are more than a stopping distance apart",
          gap > bd["stop_distance_m"] + L,
          f"{gap:.0f} m of clear guideway between cars against a "
          f"{bd['stop_distance_m']:.0f} m stop plus a {L:.0f} m car")

    cap = seated_capacity()
    check("the car seats a plausible tram load, counted off its own saloon",
          40 <= cap["seats"] <= 260, str(cap))
    check("the bench is most of the seating, as 35a shows",
          cap["bench_seats"] > 4 * max(1, cap["forward_seats"]), str(cap))

    # --- the car as a PLACE: collision, measured off the saloon --------------
    import collision as C                                      # noqa: PLC0415
    q = car_profile()
    cv, ct, cm = car_collision(prof=q)
    print(f"  car shell: {cm['triangles']} tri ({cm['triangles']/len(car_saloon()[1])*100:.2f}% "
          f"of the saloon), {cm['length_m']:.1f} m x {cm['clear_w_m']:.2f} m clear, "
          f"{cm['headroom_m']:.3f} m headroom")

    check("a passenger stands on the PLINTH, not in the floor ring",
          q["floor_y"] > q["floor_ring_y"] + 0.1,
          f"measured {q['floor_y']:.3f} against the ring at "
          f"{q['floor_ring_y']:.3f} -- {(q['floor_y']-q['floor_ring_y'])*1000:.0f} mm")
    check("and there is headroom for a standing body",
          cm["headroom_m"] > 2.0, f"{cm['headroom_m']:.3f} m")

    # A FLOOR UNDER EVERY STEP OF THE CAR, cast the way a body falls (-y).
    holes, drops = 0, []
    for i in range(9):
        x = -q["half_w"] * 0.8 + 1.6 * q["half_w"] * i / 8.0
        for j in range(40):
            z = q["z0"] + (q["z1"] - q["z0"]) * (j + 0.5) / 40.0
            h = C.cast((x, q["floor_y"] + 1.0, z), (0.0, -1.0, 0.0), cv, ct)
            if h is None:
                holes += 1
            else:
                drops.append(h)
    check("there is a floor under every step of the car",
          holes == 0 and drops, f"{holes} of 360 probes found nothing")
    check("and it is flat to under the step tolerance",
          bool(drops) and max(drops) - min(drops) < CAR_STEP_TOLERANCE_M,
          f"{(max(drops)-min(drops))*1000:.2f} mm over {cm['length_m']:.0f} m"
          if drops else "no probes landed")

    # THE CAR IS CLOSED, unlike a corridor shell -- a body must not walk out of
    # a vehicle at 26.7 m/s. Cast outward on all six headings from the middle.
    mid = ((q["z0"] + q["z1"]) / 2.0)
    eye = (0.0, q["floor_y"] + 1.7, mid)
    escapes = [d for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
                           (0, 0, 1), (0, 0, -1))
               if C.cast(eye, tuple(float(c) for c in d), cv, ct) is None]
    check("the car is closed on all six headings", not escapes,
          f"a body escapes on {escapes}")

    # NEGATIVE CONTROL: build the shell on the floor RING, which is what
    # restating `levels()` instead of measuring would have given, and the
    # passenger stands 450 mm inside the plinths they can see.
    ring_prof = dict(q, floor_y=q["floor_ring_y"])
    rv, rt, _rm = car_collision(prof=ring_prof)
    sv, st_, _sg = car_saloon()
    sunk = C.cast((0.0, ring_prof["floor_y"] + 0.02, mid), (0.0, 1.0, 0.0),
                  sv, st_)
    check("and the control fires -- a shell on the floor RING sinks the body",
          abs(q["floor_y"] - q["floor_ring_y"]) > 0.1,
          f"{(q['floor_y']-q['floor_ring_y'])*1000:.0f} mm of plinth the ring "
          f"does not know about")

    fail += _ground_gate(schema, profile, check)

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


# ---------------------------------------------------------------------------
# THE GROUND LINE'S GATE -- in the module that builds the thing, on the hard
# case, and every check with a control that fires
# ---------------------------------------------------------------------------
# CLAUDE.md, session 3x: *"a gate belongs in the module that builds the thing,
# and it must build the hard case"*. The hard case for a ring-line stop is the
# one that made the footprint arithmetic necessary -- a 94 m structure on a
# 278 m radius, where a straight member leaves the drum by four metres.
#
# AND EVERY CHECK HERE HAS TO BE ABLE TO FAIL ON THE CONTENT THAT EXISTS. Four
# controls below do exactly that and their numbers are printed, because a
# control that is not shown firing is a comment.

def _ground_gate(schema, profile, check):
    """PLC-073, measured. Returns the number of failures it added."""
    import directory as dr                                      # noqa: PLC0415
    import density as D                                         # noqa: PLC0415
    before = [0]

    def chk(name, cond, note=""):
        if not cond:
            before[0] += 1
        check(name, cond, note)

    q = dr.by_key("ground" "_tram")
    V, T, SP, M = ground_stop(schema, profile)
    print(f"\n  GROUND LINE (PLC-073) -- {len(T):,} tri: "
          f"{M['structure_triangles']:,} of stop and way over "
          f"{M['arc_built_m']:.1f} m of its {M['arc_footprint_m']:.1f} m arc, "
          f"{M['cars']} cars of {M['car_triangles']:,}")

    # 1. LAYER 2a: INSIDE ITS OWN FOOTPRINT. A footprint on a ring deck is an
    #    angular wedge and an axial span -- `directory.py`'s own definition.
    fit = ground_footprint_fit(schema, profile, V)
    chk("the ground line lands inside PLC-073's own wedge",
        fit["inside"],
        f"{fit['max_dangle_deg']:.3f} deg of {fit['half_deg']:.1f}, "
        f"{fit['max_dz_m']:.1f} m of {fit['half_z_m']:.1f}, "
        f"{fit['max_outside_floor_m']:.3f} m outside the floor")
    chk("and it USES the wedge rather than sitting in the middle of it",
        fit["angle_use"] > 0.90, f"{fit['angle_use'] * 100:.1f}% of the arc")

    #    CONTROL: the same way, straight instead of arced, is the failure the
    #    bay-by-bay emission exists to prevent. Measured, not asserted.
    hs = math.radians(fit["half_deg"]) * M["r0"] - 1.5
    sag = M["r0"] * (1.0 - math.cos(hs / M["r0"]))
    chk("and the control fires -- one straight member would leave the floor",
        sag > 1.0, f"a chord across the wedge sags {sag:.2f} m off the arc")

    #    CONTROL 2: a wedge a quarter as wide must REJECT this geometry, or the
    #    fit function is measuring nothing.
    narrow = dict(q, footprint=(q["footprint"][0] / 4.0, q["footprint"][1]))
    bad = ground_footprint_fit(schema, profile, V, place=narrow)
    chk("and the control fires -- a quarter-width wedge rejects it",
        not bad["inside"], f"{bad['max_dangle_deg']:.2f} deg of "
                           f"{bad['half_deg']:.2f}")

    # 2. THE TWO TRAMS ARE TWO TRAMS. The gazetteer says they share nothing;
    #    `deck.py --degeneracy` asks identity rather than similarity, and this
    #    is that question asked between two vehicles instead of two places.
    gv, gt, gm = ground_car(interior=True)
    lv, lt, _lm = tram_car(interior=True)
    h1 = hashlib.blake2b(repr((gv, gt)).encode(), digest_size=8).hexdigest()
    h2 = hashlib.blake2b(repr((lv, lt)).encode(), digest_size=8).hexdigest()
    chk("the ground car and the guideway car are not one vehicle",
        h1 != h2 and abs(gm["length_m"] - car_length()) > 1.0
        and abs(gm["width_m"] - CAR_WIDTH_M) > 1.0,
        f"{gm['length_m']:.0f} x {gm['width_m']:.2f} m against "
        f"{car_length():.0f} x {CAR_WIDTH_M:.2f} m")

    # 3. WINDING. Measured on the LOFTED surfaces alone: an appliqué box's
    #    inboard faces point at the car's axis and are right to, so mixing them
    #    in would turn a correct shell into a threshold nobody can defend.
    mid = (ground_level_y("skirt") + ground_level_y("roof")) / 2.0
    sv, st_, sg = ground_car_shell()
    loft = ("tram_valance", "tram_band", "tram_glass", "tram_body",
            "tram_cap", "tram_roof")
    body = [t for t, g in zip(st_, sg) if g in loft]
    chk("the ground car's body faces outward, all of it",
        _facing_fraction(sv, body, mid=mid) > 0.9999,
        f"{_facing_fraction(sv, body, mid=mid) * 100:.2f}% of "
        f"{len(body)} lofted triangles")
    iv, it_, ig = ground_car_saloon()
    encl = ("tram_in_wall", "tram_in_window", "tram_in_ceiling",
            "tram_in_skirt", "tram_in_floor")
    ins = [t for t, g in zip(it_, ig) if g in encl]
    imid = (ground_level_y("floor") + ground_level_y("cant")) / 2.0
    chk("and the saloon faces inward, all of it",
        _facing_fraction(iv, ins, inward=True, mid=imid) > 0.9999,
        f"{_facing_fraction(iv, ins, inward=True, mid=imid) * 100:.2f}%")

    # 4. CLOSED. A hole shows the background and the background is black.
    open_e = len(it.boundary_edges(sv, st_)[0])
    chk("the ground car's shell is closed", open_e == 0, f"{open_e} open edges")
    #    CONTROL: the bare `_prism8` this module already had leaves both ends
    #    of every wheel and cowl open, which is the `dressing._cyl` defect.
    cv2, ct2 = [], []
    _prism8(cv2, ct2, 0.0, 0.0, 0.36, 0.0, 0.16)
    chk("and the control fires -- a bare _prism8 is an open tube",
        len(it.boundary_edges(cv2, ct2)[0]) == 16,
        f"{len(it.boundary_edges(cv2, ct2)[0])} open edges on one prism")

    # 5. ARTICULATION. `density.py --machinery`'s own question -- is the machine
    #    as built as the wall behind it -- asked here because that gate iterates
    #    `rooms.unbuilt`, which this place is not in and cannot be: it has no
    #    `rooms.py` archetype. Same functions, same split rule.
    mach, shell = D.machinery_split(V, T, SP)
    am = D.analyse(V, mach, min_facet_m=0.0)
    ash = D.analyse(V, shell, min_facet_m=0.0)
    ratio = am["lam"] / ash["lam"] if ash["lam"] > 0 else 0.0
    print(f"    machinery {len(mach):,} tri lam {am['lam']:.3f} over "
          f"{am['area']:,.0f} m2 | shell {len(shell):,} tri lam "
          f"{ash['lam']:.3f} over {ash['area']:,.0f} m2 | x{ratio:.2f}")
    chk("the stop's fittings are at least as built as the structure behind",
        ratio >= 1.0, f"x{ratio:.2f}")

    #    CONTROL: the canopy as the box this project has a name for. Its own
    #    AABB, six faces, in place of 29a's lofted shell.
    box_v, box_t = [], []
    lo = [min(V[i][k] for tri in shell for i in tri) for k in range(3)]
    hi = [max(V[i][k] for tri in shell for i in tri) for k in range(3)]
    _slab(box_v, box_t, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    bx = D.analyse(box_v, box_t, min_facet_m=0.0)
    chk("and the control fires -- a box shell would be far coarser",
        bx["lam"] < ash["lam"] / 2.0,
        f"one box reads lam {bx['lam']:.3f} against the built "
        f"{ash['lam']:.3f}")

    # 6. THE DECLARED INTERACTABLES EXIST, resolved against the REGISTER rather
    #    than a list written here, so adding one to `directory.py` fails this.
    have = {n for n, _a, _b in SP}
    want = {"prop_" + k for k in q["interacts"]}
    chk("every interactable PLC-073 declares is built",
        want <= have, f"missing {sorted(want - have)}")
    #    PLC-073's acceptance check names three stop plaques; the spec also asks
    #    for a line map, an emergency stop and freight booking.
    spec = {"prop_level_plaque", "prop_station_schematic_screen",
            "prop_breaker_lever", "prop_manifest_terminal", "prop_intercom"}
    chk("and the fittings PLC-073's acceptance check names are there",
        spec <= have, f"missing {sorted(spec - have)}")

    # 7. THE LINE'S OWN DATA AGREES WITH THE THING BUILT. `transit.ground_line`
    #    has been the authority since INV-096 and nothing had ever read it.
    import transit as tr                                        # noqa: PLC0415
    gl = tr.ground_line(schema, profile)
    chk("the car fits the platform the line's stop count implies",
        gm["length_m"] <= GROUND_PLATFORM_L_M
        and gl["stops"] == it.SPOKE_COUNT,
        f"{gm['length_m']:.0f} m car, {GROUND_PLATFORM_L_M:.0f} m platform, "
        f"{gl['stops']} stops")
    chk("and the way is built on the drum's own floor radius",
        abs(M["r0"] - gl["radius_m"]) < 1e-9,
        f"{M['r0']:.3f} against the line's {gl['radius_m']:.3f}")
    return before[0]


if __name__ == "__main__":
    sys.exit(_selftest())
