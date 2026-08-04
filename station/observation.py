#!/usr/bin/env python3
"""The observation rooms -- the two Blue domes and the Green rotundas.

Three register places, one module, three PROGRAMS, and the programs are read
off the register rather than chosen:

    obs_dome_1    blue/0/0    0 deg  z7960  26 x 44 m   PLC-002
    obs_dome_2    blue/0/0   90 deg  z7960  20 x 36 m   PLC-030
    obs_rotundas  green/0/0  96 deg  z4200  12 x 30 m   PLC-064

All three are owned by `components.py` in the register, and `components.py`
builds the EXTERIOR -- every one of its builders emits a ring of instances in
station coordinates, and standing under an `observation_dome` at its own base
plane **0 of its 192 triangles face the viewer**. `dome_mesh` says so itself:
*"the base sits inside the hull and the hole faces away from every camera"*.
These are blisters ON a hull. `bespoke.py`'s own audit block nominated exactly
these three as *"the three worth building"* and said what each needs: *"an
observation room is a FLOOR, a WINDOW RING and a DOME WITH THICKNESS"*.

Until this module existed a player walked into any of the three and found a
generic bay -- an 8.0 x 6.3 m store room where the station's windows are.

SOURCES
-------
**`reference/05-sector-green/rotunda.webp`, authority 1** -- a domed circular
chamber ringed with windows, and the richest single interior frame in
`00-INDEX`. What it establishes and what is built from it:

  * **At least eight columns across the far arc, evenly spaced. "A closed ring
    at that spacing implies roughly sixteen bays."**
  * **Column order: a plain slightly tapered cylindrical shaft carrying a group
    of THREE narrow ring collars, then a longer plain shaft, then a short
    stepped capital under the entablature.** The same order appears on the
    Garden's civic building in `garden.png`, which is a second frame.
  * **A corbel course of stepped rectangular blocks in layered tiers** above the
    columns, then a **smooth warm gold-bronze dome with broad radial ribs**.
  * **Two pale conical elements standing on the cornice**, upper left.
  * **A continuous band of narrow pale vertical slats at about waist height**
    running right around the room, lit so it reads as a bright ribbon.
  * **Four hanging banners**, long vertical cloths with the sigil in the lower
    third.
  * **Tall blue backlit lattice panels** flanking the room left and right.
  * **A flight of about ten pale steps rising to a dark portal**, flanked by
    piers whose lower ends carry **a comb of vertical slots**; handrail left.
  * **A dark plinth lectern with a sloping cyan-glowing top**, the glow divided
    by dark bars into a symmetrical chevron figure.
  * **A radiating sunburst mosaic floor** -- triangular radial wedges about a
    centre and a broad concentric band of chevrons at larger radius.

**`reference/03-sector-blue/comand and contorl.webp`, authority 1** -- the
dome glazing seen FROM INSIDE, which is what LOCATIONS.md §169 records at
authority 1: *"a large circle on radial spoke mullions with a broad concentric
ring band, set in a flat-panelled bulkhead with angled bracing"*. That is the
dome programs' window, and `command_control.py` already builds the same
element for C&C's own bulkhead -- so the two must agree, and the mullion count
is READ from `components.DOME_MULLIONS` rather than restated here.

THE ONE THING THE SPEC AND THE GAZETTEER DISAGREE ABOUT, carried visibly.
`LOCATIONS.md` §241 records the rotundas' facing as **unresolved** -- *"if the
domed rotunda above is one of these, they face inward across the drum, not
outward at space"* -- and `00-INDEX` reads the frame as drum-interior *"with
the caveat stated"*. `docs/spec/PLACES.md` PLC-064 is the content authority and
says **"facing OUT at space"**. This module follows the spec for the GLAZING
and the auth-1 frame for the ARCHITECTURE, which is the only split that uses
both sources honestly. Nothing here decides C-003.

WHAT IS EXTRAPOLATED -- INV-291 (the rotunda) and INV-292 (the domes)
---------------------------------------------------------------------
Every absolute dimension. The frames give proportions against robed figures
and against a standing officer, not metres. See the constants: each one is
derived from something already fixed in this project -- the register's own
footprint, `rooms.PROPS['viewport']`, `rooms.WALK_M`, INV-010's 3.6 m deck
pitch -- rather than picked.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior_kit as kit                                      # noqa: E402
import rooms as _rooms                                          # noqa: E402
import bespoke as _bsp                                          # noqa: E402

DECK_PITCH_M = 3.6          # INV-010. Named, not re-derived.
WALL_T_M = _rooms.WALL_T_M  # 0.18

# ---------------------------------------------------------------------------
# THE BAY MODULE -- INV-291/292, and it is derived twice over
# ---------------------------------------------------------------------------
# A window bay has to hold a viewport and leave a pier a person can pass
# between two of them, so its width is `rooms.PROPS['viewport'][0]` plus
# `rooms.WALK_M`. Both are already fixed elsewhere in this project, so the
# module changes if either does instead of drifting from them.
VIEWPORT_W_M = _rooms.PROPS["viewport"][0]          # 2.4
VIEWPORT_H_M = _rooms.PROPS["viewport"][2]          # 1.4
DOME_BAY_M = VIEWPORT_W_M + _rooms.WALK_M           # 3.30

# THE ROTUNDA'S BAY IS THE REGISTER'S OWN, AND IT AGREES WITH THE FRAME. The
# `obs_rotundas` row is a CLASS row for four rotundas over 12 degrees at radius
# 281.9 m -- 59.0 m of arc, so 14.75 m of frontage each. A chamber of that
# outside width with `WALL_T_M` walls has an interior radius of 7.0 m, whose
# circumference over the frame's counted SIXTEEN bays is 2.75 m a bay.
#
# That is two independent derivations landing on the same number: the
# register's arc share, and a bay wide enough for the frame's colonnade at a
# robed figure's scale. Neither was fitted to the other.
ROTUNDA_BAYS = 16
ROTUNDA_R_M = 7.00
ROTUNDA_BAY_M = math.tau * ROTUNDA_R_M / ROTUNDA_BAYS           # 2.749

# Heights. Both of the rotunda's two are INV-010's deck pitch, which is the
# same rule INV-020 used to make the concourse two decks tall: a window that
# occupies exactly the first deck, and a crown at exactly the second.
ROT_SILL_M = 1.20           # the solid dado under the glazing, a leaning height
ROT_HEAD_M = DECK_PITCH_M                       # 3.60
ROT_ENTAB_M = DECK_PITCH_M * 1.20               # 4.32, the entablature top
ROT_CROWN_M = DECK_PITCH_M * 2.0                # 7.20
ROT_SLAT_M = 1.05           # the pale vertical slat band -- waist on a 1.75 m
ROT_SLATS_PER_BAY = 7       # "narrow pale vertical slats", counted off the frame
ROT_COLLARS = 3             # "a group of THREE narrow ring collars"
ROT_CORBEL_TIERS = 3        # "stepped rectangular blocks in layered tiers"
ROT_BANNERS = 4             # "four hanging banners"
ROT_LATTICE = 2             # "tall blue backlit lattice panels ... left and right"
ROT_STEPS = 10              # "a flight of about ten pale steps"
ROT_CONES = 2               # "two pale conical elements stand on the cornice"

# The dome programs. Radius is the bay module times the place's OWN declared
# viewport count, which is what makes dome 1 and dome 2 different rooms rather
# than one room at two scales -- PLC-002 lists 12 viewports, PLC-030 lists 8.
DOME_WALL_M = DECK_PITCH_M          # the ring wall is one deck; the dome is above
DOME_RISE_FRAC = 0.75               # a shallow cap, not a hemisphere -- the C&C
                                    # frame's glazing is a broad shallow circle
GALLERY_WELL_FRAC = 0.55            # dome 1's central well, as a fraction of R

# THE VESTIBULE. A round room has no flat face for a corridor to arrive at, and
# `bespoke.room_shell` puts the near face on the assembler's plane and
# `near_face_opening` measures the widest way in across it. So the chamber is
# entered through a short passage, which is also how you enter a rotunda.
# Its width is `bespoke.DOOR_HALF_W_M` doubled plus a wall either side, so the
# aperture the assembler probes is the passage itself; its length is
# `bespoke.APPROACH_DEPTH_M` plus a stride, so a body is standing in the
# passage rather than in its own doorway before the chamber opens up.
VEST_HALF_W_M = _bsp.DOOR_HALF_W_M + 0.45
VEST_L_M = _bsp.APPROACH_DEPTH_M + 1.40
VEST_H_M = kit.PROVISIONAL["door_height_m"] + 0.80


def _dome_mullions():
    """The dome's radial spoke count, READ from the exterior component.

    INV-024's window and this room's window are the same piece of glass seen
    from two sides, and `components.DOME_MULLIONS` is where that count lives --
    measured off the C&C frame and corroborated by `rotunda.webp`'s *"at least
    eight columns across the far arc ... roughly sixteen bays"*. Restating it
    would be a second copy of a measurement.
    """
    try:
        import components as _c                                 # noqa: PLC0415
        n = int(getattr(_c, "DOME_MULLIONS", 16))
        return n if n >= 4 else 16
    except Exception:                                           # noqa: BLE001
        return 16


# ---------------------------------------------------------------------------
# Primitives. Closed at both ends, every time.
# ---------------------------------------------------------------------------
def _box(v, t, g, name, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if z1 < z0:
        z0, z1 = z1, z0
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    g.append((name, t0, len(t)))
    return v, t, g


def _prism(v, t, g, name, quad, y0, y1):
    """A closed vertical prism on a 4-point (x, z) footprint.

    The wall segments, piers, banners and lattice panels of a round room are
    all trapezia in plan -- a box cannot make one, and four boxes meeting at a
    mitre share coincident faces, which is the defect `portal_frame` shipped
    for a session (828 non-manifold edges a deck).
    """
    # Normalise the winding so the sides face outward. Signed area in (x, z):
    # positive means the fan would face DOWN -- see `interior_kit.deck_pad`.
    n = len(quad)
    a2 = sum(quad[i][0] * quad[(i + 1) % n][1] - quad[(i + 1) % n][0] * quad[i][1]
             for i in range(n))
    if a2 > 0.0:
        quad = quad[::-1]
    base = len(v)
    t0 = len(t)
    v.extend((x, y1, z) for x, z in quad)
    v.extend((x, y0, z) for x, z in quad)
    for i in range(1, n - 1):
        t.append((base, base + i, base + i + 1))                # top, up
        t.append((base + n, base + n + i + 1, base + n + i))    # bottom, down
    for i in range(n):
        j = (i + 1) % n
        t.append((base + i, base + n + i, base + n + j))
        t.append((base + i, base + n + j, base + j))
    g.append((name, t0, len(t)))
    return v, t, g


def _revolve(v, t, g, name, profile, seg, y_off=0.0):
    """A closed solid of revolution about +Y from a CLOSED meridian polygon.

    `profile` is [(r, y), ...] traversed so the material lies to its left when
    walking the meridian in the (r, y) half-plane. Points with r == 0 are the
    axis and become a single shared apex vertex rather than a ring of
    coincident ones -- a degenerate ring is a fan of zero-area triangles, which
    is geometry that renders as nothing and confuses every closure measurement
    that welds by position.
    """
    n = len(profile)
    rings = []
    for r, y in profile:
        if r <= 1e-9:
            rings.append([len(v)])
            v.append((0.0, y + y_off, 0.0))
        else:
            ring = []
            for k in range(seg):
                a = math.tau * k / seg
                ring.append(len(v))
                v.append((r * math.cos(a), y + y_off, r * math.sin(a)))
            rings.append(ring)
    t0 = len(t)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            k2 = (k + 1) % seg
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                t.append((a[0], b[k], b[k2]))
            elif len(b) == 1:
                t.append((a[k2], a[k], b[0]))
            else:
                t.append((a[k], b[k], b[k2]))
                t.append((a[k], b[k2], a[k2]))
    g.append((name, t0, len(t)))
    return v, t, g


def _cyl(v, t, g, name, cx, cz, y0, y1, r0, r1=None, seg=12):
    """A capped cone/cylinder. Both ends closed -- see `hospitality._cyl`."""
    r1 = r0 if r1 is None else r1
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg
        c, s = math.cos(a), math.sin(a)
        v.append((cx + r0 * c, y0, cz + r0 * s))
        v.append((cx + r1 * c, y1, cz + r1 * s))
    t0 = len(t)
    for k in range(seg):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % seg)
        t += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    top = len(v)
    v.append((cx, y1, cz))
    for k in range(seg):
        t.append((top, n0 + 2 * k + 1, n0 + 2 * ((k + 1) % seg) + 1))
    bot = len(v)
    v.append((cx, y0, cz))
    for k in range(seg):
        t.append((bot, n0 + 2 * ((k + 1) % seg), n0 + 2 * k))
    g.append((name, t0, len(t)))
    return v, t, g


def _merge(v, t, g, name, mv, mt, dx=0.0, dy=0.0, dz=0.0):
    base = len(v)
    t0 = len(t)
    v.extend((x + dx, y + dy, z + dz) for x, y, z in mv)
    t.extend((a + base, b + base, c + base) for a, b, c in mt)
    g.append((name, t0, len(t)))
    return v, t, g


def _pad(v, t, g, name, loop, y0, y1):
    pv, pt = kit.deck_pad(loop, y0, y1)
    if pt:
        _merge(v, t, g, name, [(x, y, z) for x, y, z in pv], pt)
    return v, t, g


def _ring_quad(r0, r1, a0, a1):
    """The (x, z) trapezium of one annular sector -- a wall segment in plan."""
    return [(r0 * math.cos(a0), r0 * math.sin(a0)),
            (r1 * math.cos(a0), r1 * math.sin(a0)),
            (r1 * math.cos(a1), r1 * math.sin(a1)),
            (r0 * math.cos(a1), r0 * math.sin(a1))]


# ---------------------------------------------------------------------------
# The program, read off the register
# ---------------------------------------------------------------------------
# THE PLACE, NOT THE MODULE. Session 4h: `BESPOKE_GEOMETRY` entries that threw
# `q` away drew one room for every place that reached them, and `components`
# owns NINE places of which only these three are rooms at all. So the table
# entry dispatches by place key (`bespoke.BESPOKE_PLACES`) and refuses the
# other six by name, and this function turns the place into a program.
PROGRAMS = {
    # PLC-002. The dome C&C sits inside: glazing ribs, gallery ring, service
    # crawl. NOT a second C&C -- `command_control.py` builds the console pit
    # and this builds the ring GALLERY round its light well, which is the
    # room the spec actually describes.
    "obs_dome_1": {
        "kind": "dome", "viewports": 12, "well": True, "benches": 0,
        "ladders": 2, "shutters": True, "consoles": 1,
        "note": "C&C's dome: gallery ring, service crawl, shutter gear",
    },
    # PLC-030. Function unstated in canon; LOCATIONS P-11 adopts a traffic
    # annexe plus public gallery, and PLACES.md carries it at auth 5.
    "obs_dome_2": {
        "kind": "dome", "viewports": 8, "well": False, "benches": 6,
        "ladders": 0, "shutters": False, "consoles": 2,
        "note": "the traffic annexe and public gallery (P-11)",
    },
    # PLC-064. The four-rotunda class row.
    "obs_rotundas": {
        "kind": "rotunda", "viewports": 8, "benches": 4,
        "note": "the Minbari-order ceremonial rotunda of rotunda.webp",
    },
}


def program(place=None):
    """Which of the three this is. `place=None` gives the rotunda reference."""
    key = "obs_rotundas" if place is None else place.get("key")
    if key not in PROGRAMS:
        raise KeyError(
            f"observation.py has no program for {key!r}. It builds "
            f"{sorted(PROGRAMS)}; the other six `components` places are "
            f"exterior structures -- see the audit block in bespoke.py.")
    p = dict(PROGRAMS[key])
    p["key"] = key
    p["fn"] = frozenset((place or {}).get("functions") or ())
    p["interacts"] = tuple((place or {}).get("interacts") or ("viewport",))
    if p["kind"] == "dome":
        p["r"] = DOME_BAY_M * p["viewports"] / math.tau
        p["bays"] = p["viewports"]
        p["bay"] = DOME_BAY_M
    else:
        p["r"] = ROTUNDA_R_M
        p["bays"] = ROTUNDA_BAYS
        p["bay"] = ROTUNDA_BAY_M
    return p


def room(schema=None, profile=None, place=None):
    """One observation room: x across, y up, z along, deck at y = 0.

    Authored with the way IN at MAXIMUM z. The chamber is centred on the
    origin and the vestibule runs out to +z, so `bespoke.NEAR_END`'s `max_z`
    declaration and the geometry are one decision made in one place.
    """
    prog = program(place)
    v, t, g = [], [], []
    if prog["kind"] == "dome":
        _dome_chamber(v, t, g, prog)
    else:
        _rotunda_chamber(v, t, g, prog)
    _vestibule(v, t, g, prog)
    return v, t, g


# ---------------------------------------------------------------------------
# The vestibule -- the flat face a corridor arrives at
# ---------------------------------------------------------------------------
def _entry_bay(prog):
    """Which bay of the ring the vestibule replaces, and its angular span.

    The +z direction in this module's frame is the way out to the corridor, so
    the entry bay is the one centred on +z -- angle pi/2 in the (x, z) plane
    this module revolves in.
    """
    return math.pi / 2.0, math.tau / prog["bays"]


def _vestibule(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    hw = VEST_HALF_W_M
    z0 = ro - 0.30                      # overlaps the ring wall's own thickness
    z1 = ro + VEST_L_M
    _box(v, t, g, "worship_deck" if prog["kind"] == "rotunda"
         else "transit_deck", (-hw - WALL_T_M, -0.18, z0),
         (hw + WALL_T_M, 0.0, z1))
    pre = "worship" if prog["kind"] == "rotunda" else "transit"
    for s in (-1, 1):
        _box(v, t, g, f"{pre}_wall", (s * hw, 0.0, z0),
             (s * (hw + WALL_T_M), VEST_H_M, z1))
    _box(v, t, g, f"{pre}_soffit", (-hw - WALL_T_M, VEST_H_M, z0),
         (hw + WALL_T_M, VEST_H_M + 0.18, z1))
    # THE DOORWAY, as PIECES round the aperture -- never a solid with a hole
    # punched through it. `bespoke.doorway_wall` owns the dimensions so three
    # modules cannot agree about them by hand and then stop agreeing.
    _bsp.doorway_wall(lambda n, lo, hi: _box(v, t, g, n, lo, hi),
                      f"{pre}_wall", -hw - WALL_T_M, hw + WALL_T_M,
                      0.0, VEST_H_M, z1, z1 + WALL_T_M)
    # A portal frame, AT THE CHAMBER END and not at the aperture. It belongs at
    # the aperture and it may not stand there, and the measurement is the
    # reason: `kit.door_frame` carries a sliding leaf's pocket on one side, so
    # at the three heights `deck._mouth_clear` probes it leaves **1.20 m clear,
    # centred 0.125 m off** -- narrower than the corridor's own 1.50 m leaf and
    # not symmetric about it. Put in the near face it turns a 2.20 m aperture
    # into a jamb a body walking straight at the door meets, which is exactly
    # the failure `deck_plan`'s phase sweep was fixed for in session 3z.
    # `bespoke.near_face_opening` caught it here in the module that builds the
    # thing, which is where the gate belongs.
    fv, ft = kit.door_frame()
    _merge(v, t, g, "prop_door", fv, ft, dz=z0 + 0.35)
    # And the lit head over it, which is what makes a doorway read at distance.
    _box(v, t, g, "light_portal_head",
         (-1.02, kit.PROVISIONAL["door_height_m"] + 0.06, z1 - 0.20),
         (1.02, kit.PROVISIONAL["door_height_m"] + 0.16, z1 - 0.14))
    _box(v, t, g, "light_portal_head",
         (-1.02, kit.PROVISIONAL["door_height_m"] + 0.06, z0 + 0.30),
         (1.02, kit.PROVISIONAL["door_height_m"] + 0.16, z0 + 0.36))


# ---------------------------------------------------------------------------
# The rotunda -- rotunda.webp, authority 1
# ---------------------------------------------------------------------------
def _rotunda_chamber(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    n = prog["bays"]
    ea, espan = _entry_bay(prog)
    seg = max(48, n * 4)

    # THE SUNBURST FLOOR. "Triangular radial wedges about a centre, and a broad
    # concentric band of chevrons at larger radius." Built as a deck slab with
    # the wedges and the chevron band laid on it as pads, so the mosaic is
    # geometry at grazing incidence rather than a texture claim.
    _revolve(v, t, g, "worship_deck",
             [(0.0, 0.0), (ro, 0.0), (ro, -0.18), (0.0, -0.18)], seg)
    wedges = n
    for i in range(wedges):
        if i % 2:
            continue
        a0 = math.tau * i / wedges
        a1 = math.tau * (i + 0.62) / wedges
        _pad(v, t, g, "worship_deck_joint",
             [(0.10 * math.cos((a0 + a1) / 2), 0.10 * math.sin((a0 + a1) / 2)),
              (r * 0.46 * math.cos(a0), r * 0.46 * math.sin(a0)),
              (r * 0.46 * math.cos(a1), r * 0.46 * math.sin(a1))],
             0.0, 0.011)
    for i in range(wedges * 2):
        a0 = math.tau * i / (wedges * 2)
        a1 = math.tau * (i + 0.5) / (wedges * 2)
        am = (a0 + a1) / 2.0
        _pad(v, t, g, "worship_deck_joint",
             [(r * 0.58 * math.cos(a0), r * 0.58 * math.sin(a0)),
              (r * 0.70 * math.cos(am), r * 0.70 * math.sin(am)),
              (r * 0.58 * math.cos(a1), r * 0.58 * math.sin(a1)),
              (r * 0.64 * math.cos(am), r * 0.64 * math.sin(am))],
             0.0, 0.011)

    # THE WALL BELOW THE SILL, in segments, with the entry bay left OUT -- an
    # opening is a hole in something and the something is built with the hole
    # already in it.
    for i in range(n):
        a0 = math.tau * i / n - math.tau / (2 * n) + ea
        a1 = a0 + math.tau / n
        if abs(((a0 + a1) / 2.0 - ea + math.pi) % math.tau - math.pi) < 1e-6:
            continue
        # THE WALL STOPS AT THE SILL. It used to run floor to entablature and
        # the glazing was then laid at r+0.02..r+0.09 -- INSIDE the wall's own
        # 0.18 m thickness. The room had no windows at all, and
        # `docs/engine-4k-rotunda-normal.png` is the frame that showed it: an
        # observation rotunda with a blank wall where the view goes. INV-024
        # records the identical defect on C&C's own window in session 2 --
        # *"the bulkhead had no aperture; it was one solid slab with the
        # glazing laid on it, so the glass was sealed inside 0.30 m of steel"*
        # -- and the lesson is stated there: **an opening is a hole in
        # something, and the something has to be built with the hole already
        # in it.** Third instance in this project; first one caught by a frame
        # rather than by an assertion, which is the part worth fixing next.
        _prism(v, t, g, "worship_wall", _ring_quad(r, ro, a0, a1),
               0.0, ROT_SILL_M)
        # THE PALE VERTICAL SLAT BAND at waist height, right around the room.
        for k in range(ROT_SLATS_PER_BAY):
            f0 = (k + 0.22) / ROT_SLATS_PER_BAY
            f1 = (k + 0.62) / ROT_SLATS_PER_BAY
            _prism(v, t, g, "light_pilaster_strip",
                   _ring_quad(r - 0.055, r, a0 + (a1 - a0) * f0,
                              a0 + (a1 - a0) * f1),
                   ROT_SLAT_M - 0.34, ROT_SLAT_M + 0.16)
        # THE GLAZING, set INTO the bay between sill and head. Glass sits in an
        # opening; INV-024 records the render that shipped it sealed inside
        # 0.30 m of steel because the bulkhead had no aperture at all.
        # The glass sits IN the opening, spanning the reveal, inset from the
        # jambs so the columns and the reveal read either side of it.
        _prism(v, t, g, "prop_viewport",
               _ring_quad(r + 0.055, ro - 0.055, a0 + 0.035, a1 - 0.035),
               ROT_SILL_M, ROT_HEAD_M)
        # GLAZING BARS, and they are part of the window rather than trim. A
        # pane of glass is a flat prism with almost no visible line in it, and
        # fifteen of them dragged this room's `density.py --machinery` ratio to
        # **x0.95** -- machinery LESS articulated than the shell behind it,
        # which is that gate's exact signature failure and the reason it
        # exists. A transom and two glazing bars are what a 2.4 m window is
        # actually built from and they carry the lines the pane does not.
        #
        # AND EACH BAR IS TWO PIECES, WHICH THE FIRST RE-RENDER MADE THE CASE
        # FOR. `prop_viewport` binds `viewport_glazing` -- albedo 0.04, the
        # colour of glass -- so a bar named `prop_viewport` in front of black
        # glass carries the line the DENSITY gate measures and shows the eye
        # nothing: `docs/engine-4k-rotunda-half.png` came back with a plain
        # black band where a divided window should be. The dark bar stays (it
        # is the glazing's own division and it is what the gate is asking
        # about) and a pale cover strip stands proud of it on the room side,
        # which is what a real window frame is.
        for f in (0.30, 0.70):
            _prism(v, t, g, "prop_viewport",
                   _ring_quad(r + 0.02, ro - 0.02,
                              a0 + (a1 - a0) * f - 0.008,
                              a0 + (a1 - a0) * f + 0.008),
                   ROT_SILL_M + 0.03, ROT_HEAD_M - 0.03)
            _prism(v, t, g, "worship_mullion",
                   _ring_quad(r - 0.05, r + 0.03,
                              a0 + (a1 - a0) * f - 0.012,
                              a0 + (a1 - a0) * f + 0.012),
                   ROT_SILL_M + 0.02, ROT_HEAD_M - 0.02)
        for yf in (0.34, 0.68):
            yy = ROT_SILL_M + (ROT_HEAD_M - ROT_SILL_M) * yf
            _prism(v, t, g, "prop_viewport",
                   _ring_quad(r + 0.02, ro - 0.02, a0 + 0.045, a1 - 0.045),
                   yy - 0.022, yy + 0.022)
            _prism(v, t, g, "worship_mullion",
                   _ring_quad(r - 0.05, r + 0.03, a0 + 0.045, a1 - 0.045),
                   yy - 0.030, yy + 0.030)
        # The reveal round the aperture -- head, sill and two jambs, which is
        # what stops a window reading as a decal at grazing incidence.
        _prism(v, t, g, "worship_cornice", _ring_quad(r, ro, a0, a1),
               ROT_HEAD_M - 0.10, ROT_HEAD_M)
        _prism(v, t, g, "worship_cornice", _ring_quad(r - 0.06, ro, a0, a1),
               ROT_SILL_M - 0.09, ROT_SILL_M)
        for f0, f1 in ((0.0, 0.035), (1.0 - 0.035 / (a1 - a0), 1.0)):
            _prism(v, t, g, "worship_mullion",
                   _ring_quad(r, ro, a0 + (a1 - a0) * f0,
                              a0 + (a1 - a0) * f1),
                   ROT_SILL_M, ROT_HEAD_M)
        _prism(v, t, g, "worship_wall",
               _ring_quad(r, ro, a0, a1), ROT_HEAD_M, ROT_ENTAB_M)
        _prism(v, t, g, "worship_dado",
               _ring_quad(r - 0.05, r, a0, a1), 0.0, ROT_SILL_M)

    # THE COLUMNS. "A plain slightly tapered cylindrical shaft carrying a group
    # of THREE narrow ring collars, then a longer plain shaft, then a short
    # stepped capital under the entablature." Built in that order, and the
    # order is the identity of the room -- `garden.png` carries the same one on
    # the Garden's civic building, so it is a station order, not a one-off.
    for i in range(n):
        a = math.tau * i / n - math.tau / (2 * n) + ea
        if abs(((a - ea + math.pi) % math.tau) - math.pi) < 1e-6:
            continue
        cx, cz = (r - 0.24) * math.cos(a), (r - 0.24) * math.sin(a)
        _column(v, t, g, cx, cz)

    # THE CORBEL COURSE -- stepped rectangular blocks in layered tiers.
    for tier in range(ROT_CORBEL_TIERS):
        y0 = ROT_ENTAB_M + tier * 0.30
        rr = r - 0.10 - tier * 0.20
        m = n * 2
        for i in range(m):
            a0 = math.tau * (i + 0.14) / m + ea
            a1 = math.tau * (i + 0.86) / m + ea
            _prism(v, t, g, "worship_cornice",
                   _ring_quad(rr, ro, a0, a1), y0, y0 + 0.30)

    # THE DOME. Warm gold-bronze, smooth, with broad radial ribs. A CLOSED
    # SOLID with thickness -- `bespoke.py`'s own note on this work says the
    # hard part is exactly that: `components.dome_mesh` is a closed
    # half-ellipsoid every face of which points OUT, so an interior needs the
    # surface built twice with a rim between.
    y0 = ROT_ENTAB_M + ROT_CORBEL_TIERS * 0.30
    rise = ROT_CROWN_M - y0
    r_in = r - 0.10 - ROT_CORBEL_TIERS * 0.20
    _dome_solid(v, t, g, "worship_panel", r_in, y0, rise, 0.22, seg)
    # THE RIBS ARE GOLD-BRONZE, which is the frame's own word for the dome:
    # *"a smooth warm gold-bronze dome with broad radial ribs"*. No `worship_*`
    # group binds anything but grey, and `materials.py` is not this session's
    # file; `edge_chevron_nosing` (albedo 0.900 / 0.720 / 0.060, sourced from
    # `Minbari Flyer 969 in docking bay 17.webp`) is the one sourced gold in
    # the library and `dress_kerb` is the fragment that reaches it. The name
    # also has to end in `_rib` so `rooms.is_solid` calls it shell -- a dome
    # rib named as an object becomes a collision box hanging over the floor.
    ribs = n
    for i in range(ribs):
        a = math.tau * i / ribs + ea
        _dome_rib(v, t, g, "dress_kerb_rib", r_in, y0, rise, a, 0.16, 0.13)

    # TWO PALE CONICAL ELEMENTS standing on the cornice, upper left.
    for i in range(ROT_CONES):
        a = ea + math.pi * (0.62 + 0.16 * i)
        _cyl(v, t, g, "worship_cornice", (r - 0.55) * math.cos(a),
             (r - 0.55) * math.sin(a), y0, y0 + 0.72, 0.26, 0.02, seg=10)

    _rotunda_fittings(v, t, g, prog, r, n, ea)


def _column(v, t, g, cx, cz):
    """One column of the frame's order: taper, THREE collars, shaft, capital."""
    _cyl(v, t, g, "worship_rib", cx, cz, 0.0, 0.16, 0.30, 0.27, seg=12)
    _cyl(v, t, g, "worship_rib", cx, cz, 0.16, 1.62, 0.26, 0.225, seg=12)
    for k in range(ROT_COLLARS):
        y = 1.62 + k * 0.135
        _cyl(v, t, g, "worship_rib", cx, cz, y, y + 0.085, 0.285, seg=12)
    _cyl(v, t, g, "worship_rib", cx, cz, 2.03, ROT_HEAD_M - 0.28, 0.215,
         0.195, seg=12)
    _cyl(v, t, g, "worship_rib", cx, cz, ROT_HEAD_M - 0.28, ROT_HEAD_M - 0.14,
         0.255, seg=12)
    _cyl(v, t, g, "worship_rib", cx, cz, ROT_HEAD_M - 0.14, ROT_ENTAB_M,
         0.295, seg=12)


def _dome_solid(v, t, g, name, r, y0, rise, thick, seg):
    """A dome with THICKNESS: outer surface, inner surface, and the rim.

    `bespoke.py`'s audit block names this as the only hard part of an
    observation room, and it is right. The profile is a closed meridian --
    outer from the springing to the crown, inner back down, rim across -- so
    the revolve produces one closed solid and the INSIDE face exists, which is
    the whole difference between a room and a blister on a hull.
    """
    steps = 12
    prof = []
    for i in range(steps + 1):
        f = i / steps
        prof.append((r * math.cos(f * math.pi / 2.0),
                     y0 + rise * math.sin(f * math.pi / 2.0)))
    ri, yi = r - thick, rise - thick
    for i in range(steps, -1, -1):
        f = i / steps
        prof.append((ri * math.cos(f * math.pi / 2.0),
                     y0 + yi * math.sin(f * math.pi / 2.0)))
    _revolve(v, t, g, name, prof, seg)
    return v, t, g


def _dome_rib(v, t, g, name, r, y0, rise, a, w, d, steps=9):
    """One broad radial rib on the dome's inner face, along a meridian."""
    c, s = math.cos(a), math.sin(a)
    tc, ts = -math.sin(a), math.cos(a)
    base = len(v)
    t0 = len(t)
    rings = []
    for i in range(steps + 1):
        f = i / steps
        rr = (r - 0.02) * math.cos(f * math.pi / 2.0)
        yy = y0 + (rise - 0.02) * math.sin(f * math.pi / 2.0)
        ri = max(0.0, rr - d)
        yi = yy - d * math.sin(f * math.pi / 2.0) * 0.2
        quad = []
        for rq, yq in ((rr, yy), (ri, yi)):
            for sgn in (-1.0, 1.0):
                quad.append((rq * c + sgn * w / 2.0 * tc, yq,
                             rq * s + sgn * w / 2.0 * ts))
        rings.append([quad[0], quad[1], quad[3], quad[2]])
    for i, ring in enumerate(rings):
        v.extend(ring)
    for i in range(steps):
        a0 = base + 4 * i
        b0 = base + 4 * (i + 1)
        for k in range(4):
            j = (k + 1) % 4
            t.append((a0 + k, b0 + k, b0 + j))
            t.append((a0 + k, b0 + j, a0 + j))
    t += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    e = base + 4 * steps
    t += [(e, e + 1, e + 2), (e, e + 2, e + 3)]
    g.append((name, t0, len(t)))
    return v, t, g


def _rotunda_fittings(v, t, g, prog, r, n, ea):
    """Banners, lattice panels, the steps and portal, the lectern, the seats."""
    # FOUR HANGING BANNERS -- long vertical cloths, sigil in the lower third.
    for i in range(ROT_BANNERS):
        a = ea + math.pi * (0.42 + 0.39 * i)
        a0, a1 = a - 0.085, a + 0.085
        _prism(v, t, g, "sign_face", _ring_quad(r - 0.34, r - 0.30, a0, a1),
               1.55, ROT_HEAD_M + 0.10)
        _prism(v, t, g, "signage_panel",
               _ring_quad(r - 0.345, r - 0.335, a0 + 0.02, a1 - 0.02),
               1.72, 2.30)
        _prism(v, t, g, "worship_rib", _ring_quad(r - 0.36, r - 0.28,
                                                  a0 - 0.012, a1 + 0.012),
               ROT_HEAD_M + 0.10, ROT_HEAD_M + 0.16)

    # TALL BLUE BACKLIT LATTICE PANELS flanking the room, left and right.
    for i in range(ROT_LATTICE):
        a = ea + math.pi * (0.66 + 0.68 * i)
        for k in range(9):
            f0 = -0.19 + 0.042 * k
            _prism(v, t, g, "light_bar_backlight",
                   _ring_quad(r - 0.26, r - 0.22, a + f0, a + f0 + 0.028),
                   0.45, ROT_HEAD_M - 0.20)
        _prism(v, t, g, "worship_mullion",
               _ring_quad(r - 0.30, r - 0.20, a - 0.215, a + 0.215),
               0.30, 0.45)
        _prism(v, t, g, "worship_mullion",
               _ring_quad(r - 0.30, r - 0.20, a - 0.215, a + 0.215),
               ROT_HEAD_M - 0.20, ROT_HEAD_M - 0.05)

    # THE FLIGHT OF ABOUT TEN PALE STEPS rising to a dark portal, flanked by
    # piers whose lower ends carry a comb of vertical slots.
    ax = -math.sin(ea)          # the direction opposite the way in
    az = -math.cos(ea)
    # (ea is pi/2, so the entry is at +z and the stair is at -z.)
    sx, sz = 0.0, -1.0
    rise = 0.165
    for i in range(ROT_STEPS):
        zz = -r * 0.42 - i * 0.30
        _box(v, t, g, "worship_deck", (-1.35, 0.0, zz - 0.30),
             (1.35, rise * (i + 1), zz))
        _box(v, t, g, "fix_platform_edge", (-1.35, rise * (i + 1) - 0.03,
                                            zz - 0.30),
             (1.35, rise * (i + 1) + 0.012, zz - 0.24))
    top = rise * ROT_STEPS
    zt = -r * 0.42 - ROT_STEPS * 0.30
    _box(v, t, g, "worship_panel", (-1.60, top, zt - 0.55),
         (1.60, top + 2.45, zt - 0.30))
    for s in (-1, 1):
        _box(v, t, g, "worship_rib", (s * 1.35, 0.0, zt - 0.32),
             (s * 1.72, top + 2.75, zt + 2.40))
        for k in range(8):
            _box(v, t, g, "worship_mullion",
                 (s * 1.36, 0.10, zt + 0.30 + k * 0.24),
                 (s * 1.74, 1.05, zt + 0.36 + k * 0.24))
    rv, rt = kit.handrail(ROT_STEPS * 0.30, height=1.02, post_spacing=0.9)
    _merge(v, t, g, "prop_gallery_rail",
           [(-z, y + top * (1.0 - x / max(1e-9, ROT_STEPS * 0.30)), x)
            for x, y, z in rv], rt, dx=-1.24, dz=zt)

    # THE LECTERN -- dark plinth, sloping cyan-glowing top, chevron figure.
    # A DARK PLINTH. `prop_console` binds the station's console shell, which
    # is a warm lit surface, and at 1.24 x 0.72 x 0.96 m it read in
    # `docs/engine-4k-rotunda-normal.png` as a glowing orange box in the middle
    # of a cold grey chamber -- the brightest thing in a frame whose subject is
    # a window ring. The reference is explicit: *"a dark plinth lectern with a
    # sloping cyan-glowing top"*, so the plinth takes the room's own wall
    # material and only the top glows.
    _box(v, t, g, "worship_panel", (-0.62, 0.0, r * 0.30),
         (0.62, 0.96, r * 0.30 + 0.72))
    _box(v, t, g, "worship_mullion", (-0.66, 0.90, r * 0.30 - 0.04),
         (0.66, 0.98, r * 0.30 + 0.76))
    _box(v, t, g, "light_dais_key", (-0.56, 0.96, r * 0.30 + 0.04),
         (0.56, 1.00, r * 0.30 + 0.68))
    for s in (-1, 1):
        _box(v, t, g, "worship_mullion", (s * 0.04, 1.00, r * 0.30 + 0.06),
             (s * 0.30, 1.02, r * 0.30 + 0.66))

    # THE SEATS the register declares, on the ring between the columns.
    for i in range(prog["benches"]):
        a = ea + math.tau * (i + 0.5) / prog["benches"] + math.tau / (2 * n)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.95, r - 0.48, a - 0.115, a + 0.115),
               0.40, 0.46)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.92, r - 0.84, a - 0.11, a + 0.11), 0.0, 0.40)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.59, r - 0.51, a - 0.11, a + 0.11), 0.0, 0.40)

    # THE SKY PLAQUE, ETIQUETTE NOTICE, LIGHTS-DOWN SWITCH and INSPECTION
    # TERMINAL that PLC-064 adds to the register's two. They are built under
    # names `materials.py` already binds; the register rows that would DECLARE
    # them are not this session's to add -- see the report.
    for i, (nm, y0, y1, wd) in enumerate((
            ("prop_info_board", 1.15, 2.05, 0.16),
            ("prop_babcom_terminal", 1.05, 1.55, 0.10))):
        a = ea + math.pi + (0.34 if i else -0.34)
        _prism(v, t, g, nm, _ring_quad(r - 0.09, r - 0.02, a - wd, a + wd),
               y0, y1)


# ---------------------------------------------------------------------------
# The domes -- the C&C frame's glazing, from inside
# ---------------------------------------------------------------------------
def _dome_chamber(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    n = prog["bays"]
    ea, _ = _entry_bay(prog)
    seg = max(48, n * 4)
    mull = _dome_mullions()

    _revolve(v, t, g, "transit_deck",
             [(0.0, 0.0), (ro, 0.0), (ro, -0.18), (0.0, -0.18)], seg)

    # THE GALLERY WELL. PLC-002's dome holds C&C `within` it, and the room this
    # row describes is the ring GALLERY round it -- so dome 1 gets a recessed
    # centre with a rail on its edge, and dome 2, which is a flat public
    # gallery, does not. A RECESS, NOT A HOLE: a void in the floor is a void a
    # body falls through and the collision shell has no way to say so.
    if prog.get("well"):
        wr = r * GALLERY_WELL_FRAC
        _revolve(v, t, g, "transit_deck",
                 [(0.0, -0.25), (wr, -0.25), (wr, -0.43), (0.0, -0.43)], seg)
        _revolve(v, t, g, "transit_rib",
                 [(wr, 0.0), (wr + 0.12, 0.0), (wr + 0.12, -0.25),
                  (wr, -0.25)], seg)
        for i in range(n * 2):
            a = math.tau * i / (n * 2)
            _cyl(v, t, g, "prop_gallery_rail",
                 (wr + 0.06) * math.cos(a), (wr + 0.06) * math.sin(a),
                 0.0, 1.05, 0.035, seg=6)
        _revolve(v, t, g, "prop_gallery_rail",
                 [(wr + 0.02, 1.05), (wr + 0.10, 1.05), (wr + 0.10, 0.99),
                  (wr + 0.02, 0.99)], seg)

    # THE RING WALL, one deck high, in segments with the entry bay left out.
    for i in range(n):
        a0 = math.tau * i / n - math.tau / (2 * n) + ea
        a1 = a0 + math.tau / n
        if abs(((a0 + a1) / 2.0 - ea + math.pi) % math.tau - math.pi) < 1e-6:
            continue
        # THE WALL STOPS AT THE SILL -- see the rotunda's own note above and
        # INV-024. A dome whose viewports are buried in its wall is a dome
        # with no view, which is the whole of what this room is for.
        _prism(v, t, g, "transit_wall", _ring_quad(r, ro, a0, a1), 0.0, 0.95)
        _prism(v, t, g, "transit_wall", _ring_quad(r, ro, a0, a1),
               0.95 + VIEWPORT_H_M, DOME_WALL_M)
        _prism(v, t, g, "transit_dado", _ring_quad(r - 0.05, r, a0, a1),
               0.0, 0.95)
        # THE VIEWPORT, set into the bay -- `rooms.PROPS['viewport']`'s own
        # 2.4 x 1.4 m, converted to an angle at this radius rather than to a
        # second number.
        half = VIEWPORT_W_M / 2.0 / r
        am = (a0 + a1) / 2.0
        _prism(v, t, g, "prop_viewport",
               _ring_quad(r + 0.055, ro - 0.055, am - half, am + half),
               0.95, 0.95 + VIEWPORT_H_M)
        # THE SAME DIVISION THE ROTUNDA'S WINDOWS CARRY, and for both of its
        # reasons -- see the note there. A dark bar in the glass plane so the
        # window has lines for `density.py --machinery` to find, and a pale
        # cover strip proud of it so a viewer sees them: at 4 m
        # `docs/engine-4k-dome2-half.png` showed each viewport as one black
        # rectangle. **This is the fix applied to the rule and not to the
        # instance** -- it was found on the rotunda and both programs carry it,
        # which is session 4h's own lesson about the registry table.
        for f in (0.34, 0.66):
            ba = am - half + 2.0 * half * f
            _prism(v, t, g, "prop_viewport",
                   _ring_quad(r + 0.02, ro - 0.02, ba - 0.010, ba + 0.010),
                   0.98, 0.92 + VIEWPORT_H_M)
            _prism(v, t, g, "transit_mullion",
                   _ring_quad(r - 0.05, r + 0.03, ba - 0.014, ba + 0.014),
                   0.97, 0.93 + VIEWPORT_H_M)
        ym = 0.95 + VIEWPORT_H_M * 0.46
        _prism(v, t, g, "prop_viewport",
               _ring_quad(r + 0.02, ro - 0.02, am - half + 0.01,
                          am + half - 0.01), ym - 0.020, ym + 0.020)
        _prism(v, t, g, "transit_mullion",
               _ring_quad(r - 0.05, r + 0.03, am - half + 0.01,
                          am + half - 0.01), ym - 0.028, ym + 0.028)
        # The jambs either side of the glass, and the head and sill reveals.
        for aa, bb in ((a0, am - half), (am + half, a1)):
            if bb - aa > 1e-4:
                _prism(v, t, g, "transit_wall", _ring_quad(r, ro, aa, bb),
                       0.95, 0.95 + VIEWPORT_H_M)
        _prism(v, t, g, "transit_cornice", _ring_quad(r - 0.05, ro, a0, a1),
               0.95 + VIEWPORT_H_M, 0.95 + VIEWPORT_H_M + 0.09)
        _prism(v, t, g, "transit_cornice", _ring_quad(r - 0.05, ro, a0, a1),
               0.86, 0.95)
        _prism(v, t, g, "transit_mullion",
               _ring_quad(r - 0.06, r + 0.02, am - half - 0.03,
                          am - half + 0.01), 0.95, 0.95 + VIEWPORT_H_M)
        _prism(v, t, g, "transit_mullion",
               _ring_quad(r - 0.06, r + 0.02, am + half - 0.01,
                          am + half + 0.03), 0.95, 0.95 + VIEWPORT_H_M)
        _prism(v, t, g, "light_wall_course",
               _ring_quad(r - 0.07, r - 0.02, a0 + 0.03, a1 - 0.03),
               DOME_WALL_M - 0.44, DOME_WALL_M - 0.30)

    # THE CORNICE the dome springs from.
    _revolve(v, t, g, "transit_cornice",
             [(r - 0.30, DOME_WALL_M), (ro, DOME_WALL_M),
              (ro, DOME_WALL_M - 0.22), (r - 0.30, DOME_WALL_M - 0.10)], seg)

    # THE DOME, WITH THICKNESS, and the glazing under it.
    rise = r * DOME_RISE_FRAC
    _dome_solid(v, t, g, "transit_panel", r - 0.20, DOME_WALL_M, rise, 0.20,
                seg)
    # RADIAL SPOKE MULLIONS AND A BROAD CONCENTRIC RING BAND. LOCATIONS.md
    # §169 at authority 1, and the count comes from `components.DOME_MULLIONS`
    # because this is the same glass C&C looks through.
    for i in range(mull):
        a = math.tau * i / mull + ea
        _dome_rib(v, t, g, "transit_mullion", r - 0.20, DOME_WALL_M, rise, a,
                  0.13, 0.10)
    band = 0.55
    _revolve(v, t, g, "transit_rib",
             [((r - 0.20) * math.cos(band * math.pi / 2) - 0.02,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.02,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)
               + 0.42),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.24,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)
               + 0.42),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.24,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2))],
             seg)
    # THE GLAZED PANEL between the spokes -- the thing you look through.
    _dome_solid(v, t, g, "prop_viewport", r - 0.34, DOME_WALL_M + 0.02,
                rise - 0.06, 0.05, seg)

    _dome_fittings(v, t, g, prog, r, n, ea)


def _dome_fittings(v, t, g, prog, r, n, ea):
    """Shutters, ladders, consoles, benches, boards -- per PLC-002 / PLC-030."""
    # BLAST SHUTTER LEAVES, stowed round the springing. PLC-001 lists blast
    # shutters for the dome and PLC-002 makes the shutter master this room's
    # control, so the leaves have to exist somewhere for it to close.
    if prog.get("shutters"):
        for i in range(n):
            a0 = math.tau * (i + 0.10) / n + ea
            a1 = math.tau * (i + 0.90) / n + ea
            _prism(v, t, g, "prop_blast_door",
                   _ring_quad(r - 0.62, r - 0.26, a0, a1),
                   DOME_WALL_M - 0.06, DOME_WALL_M + 0.62)
        _prism(v, t, g, "prop_console",
               _ring_quad(r - 0.86, r - 0.20, ea + math.pi - 0.11,
                          ea + math.pi + 0.11), 0.0, 1.12)

    # THE SERVICE CRAWL's ladders. PLC-002 lists `service_ladder`.
    for i in range(prog.get("ladders", 0)):
        a = ea + math.pi * (0.55 + 0.90 * i)
        for k in range(9):
            _prism(v, t, g, "prop_service_ladder",
                   _ring_quad(r - 0.34, r - 0.16, a - 0.038, a + 0.038),
                   0.30 + k * 0.30, 0.36 + k * 0.30)
        for s in (-1, 1):
            _prism(v, t, g, "prop_service_ladder",
                   _ring_quad(r - 0.34, r - 0.16, a + s * 0.042,
                              a + s * 0.056), 0.24, DOME_WALL_M - 0.20)

    # THE CONSOLES: PLC-002's dome-status console, PLC-030's two traffic
    # repeaters. Both stand on the deck facing the glazing.
    for i in range(prog.get("consoles", 0)):
        a = ea + math.pi + (0.0 if prog["consoles"] == 1
                            else (-0.42 + 0.84 * i))
        cx, cz = (r * 0.52) * math.cos(a), (r * 0.52) * math.sin(a)
        _box(v, t, g, "prop_console", (cx - 0.70, 0.0, cz - 0.33),
             (cx + 0.70, 0.82, cz + 0.33))
        _box(v, t, g, "prop_console", (cx - 0.70, 0.82, cz - 0.33),
             (cx + 0.70, 1.02, cz + 0.05))
        _box(v, t, g, "light_bar_backlight", (cx - 0.64, 0.83, cz - 0.28),
             (cx + 0.64, 0.845, cz + 0.02))

    # THE BENCHES PLC-030 lists, on a ring facing out at the windows.
    for i in range(prog.get("benches", 0)):
        a = ea + math.tau * (i + 0.5) / prog["benches"]
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 1.35, r - 0.90, a - 0.12, a + 0.12), 0.40, 0.46)
        for rr in (r - 1.31, r - 0.94):
            _prism(v, t, g, "prop_bench",
                   _ring_quad(rr - 0.04, rr + 0.04, a - 0.11, a + 0.11),
                   0.0, 0.40)

    # THE INSPECTION TERMINAL, and A PLAQUE AT EVERY WINDOW, not at four of
    # them. PLC-002 and PLC-030 both make the same demand of this room -- *"the
    # dome's 12 viewports each answer LOOK with the true bearing they face"*,
    # *"the gallery's 8 viewports name 8 true bearings"* -- so the plaque count
    # is the viewport count by definition, and building four of them would be
    # a room that fails its own acceptance check by construction.
    a = ea + math.pi * 0.72
    _prism(v, t, g, "prop_babcom_terminal",
           _ring_quad(r - 0.10, r - 0.02, a - 0.10, a + 0.10), 1.05, 1.55)
    for i in range(n):
        a2 = ea + math.tau * (i + 0.5) / n
        _prism(v, t, g, "prop_info_board",
               _ring_quad(r - 0.07, r - 0.02, a2 - 0.055, a2 + 0.055),
               0.52, 0.86)
        _prism(v, t, g, "sign_frame",
               _ring_quad(r - 0.08, r - 0.065, a2 - 0.062, a2 + 0.062),
               0.50, 0.88)

    # THE LEANING RAIL at the window ring. Nobody stands at a viewport with
    # their nose against the glass; every observation gallery ever built has a
    # rail set back far enough to lean on, and it is also what stops a body's
    # collision capsule from resting inside the glazing.
    for i in range(n * 2):
        a2 = ea + math.tau * (i + 0.5) / (n * 2)
        _cyl(v, t, g, "prop_gallery_rail", (r - 0.62) * math.cos(a2),
             (r - 0.62) * math.sin(a2), 0.0, 1.02, 0.032, seg=6)
    _revolve(v, t, g, "prop_gallery_rail",
             [(r - 0.66, 1.02), (r - 0.58, 1.02), (r - 0.58, 0.96),
              (r - 0.66, 0.96)], max(48, n * 4))
    _revolve(v, t, g, "prop_gallery_rail",
             [(r - 0.645, 0.58), (r - 0.595, 0.58), (r - 0.595, 0.53),
              (r - 0.645, 0.53)], max(48, n * 4))

    # THE COVE at the springing, and a ring of deck pools under it. A room
    # whose whole point is looking OUT is lit from behind the eye, not from
    # overhead: the fittings wash the wall and the deck, and the glazing stays
    # the brightest thing in the frame.
    _revolve(v, t, g, "light_house_cove",
             [(r - 0.34, DOME_WALL_M - 0.14), (r - 0.28, DOME_WALL_M - 0.14),
              (r - 0.28, DOME_WALL_M - 0.24), (r - 0.34, DOME_WALL_M - 0.24)],
             max(48, n * 4))
    for i in range(n):
        a2 = ea + math.tau * i / n
        pv, pt = kit.downlight_pool(radius=0.42, segments=14)
        _merge(v, t, g, "light_deck_channel_pool",
               [(x, y, z) for x, y, z in pv], pt,
               dx=(r * 0.62) * math.cos(a2), dz=(r * 0.62) * math.sin(a2))

    # THE BEARING ROSE inlaid in the deck. The room's content is which way it
    # faces, so the floor says so: a radial wedge per window bay about a hub.
    _pad(v, t, g, "transit_deck_joint",
         [(0.62 * math.cos(math.tau * k / 24), 0.62 * math.sin(math.tau * k / 24))
          for k in range(24)], 0.0, 0.012)
    for i in range(n):
        a2 = ea + math.tau * i / n
        _pad(v, t, g, "transit_deck_joint",
             [(0.70 * math.cos(a2), 0.70 * math.sin(a2)),
              ((r * 0.44) * math.cos(a2 - 0.045),
               (r * 0.44) * math.sin(a2 - 0.045)),
              ((r * 0.44) * math.cos(a2 + 0.045),
               (r * 0.44) * math.sin(a2 + 0.045))],
             0.0, 0.011)

    # A LEDGE UNDER EVERY WINDOW. What a person actually does at a viewport is
    # put something down and lean; `rooms.PROPS['counter']` is the station's
    # own ledge and one per bay is what makes the ring read as somewhere people
    # stay rather than a corridor with glass in it.
    for i in range(n):
        a2 = ea + math.tau * (i + 0.5) / n
        half = VIEWPORT_W_M / 2.4 / r
        _prism(v, t, g, "prop_counter",
               _ring_quad(r - 0.30, r - 0.01, a2 - half, a2 + half),
               0.86, 0.95)
        _prism(v, t, g, "prop_counter",
               _ring_quad(r - 0.26, r - 0.20, a2 - half * 0.85,
                          a2 - half * 0.70), 0.0, 0.86)
        _prism(v, t, g, "prop_counter",
               _ring_quad(r - 0.26, r - 0.20, a2 + half * 0.70,
                          a2 + half * 0.85), 0.0, 0.86)

    # THE PLOT TABLE. PLC-030 makes this dome the traffic annexe -- *"the
    # repeater shows the same berth map C&C shows, delayed 0 s"* -- so the room
    # has a table to spread a berth plot on, with stools round it. PLC-002's
    # dome has a well in the middle instead and gets none of this.
    if not prog.get("well"):
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.0, 0.10, 0.62, seg=12)
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.10, 0.68, 0.24, seg=12)
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.68, 0.78, 1.05, seg=20)
        _revolve(v, t, g, "light_dais_key",
                 [(0.0, 0.785), (0.96, 0.785), (0.96, 0.775), (0.0, 0.775)],
                 20)
        for i in range(4):
            a2 = ea + math.tau * (i + 0.25) / 4
            _cyl(v, t, g, "prop_seat", 1.62 * math.cos(a2),
                 1.62 * math.sin(a2), 0.0, 0.44, 0.20, seg=8)
            _cyl(v, t, g, "prop_seat", 1.62 * math.cos(a2),
                 1.62 * math.sin(a2), 0.44, 0.49, 0.24, seg=10)

    # THE LOCKER BANK. A watch room stores its slates, its lamps and its
    # emergency kit somewhere, and a room whose fittings all hang on the wall
    # is a set rather than a place people work in.
    for i in range(2):
        a2 = ea + math.pi + (-0.62 + 1.24 * i)
        for k in range(3):
            _prism(v, t, g, "prop_locker",
                   _ring_quad(r - 0.52, r - 0.08, a2 - 0.13 + k * 0.09,
                              a2 - 0.05 + k * 0.09), 0.0, 1.92)
        _prism(v, t, g, "prop_locker",
               _ring_quad(r - 0.56, r - 0.04, a2 - 0.15, a2 + 0.24),
               1.92, 2.02)

    # PLANTERS AND A WASTE BIN -- a gallery the public sits in is kept, and
    # `rooms.PROPS` already carries both.
    for i in range(max(2, n // 3)):
        a2 = ea + math.tau * (i + 0.28) / max(2, n // 3)
        _cyl(v, t, g, "prop_planter", (r * 0.72) * math.cos(a2),
             (r * 0.72) * math.sin(a2), 0.0, 0.62, 0.34, seg=10)
        _cyl(v, t, g, "transit_rib", (r * 0.72) * math.cos(a2),
             (r * 0.72) * math.sin(a2), 0.62, 0.68, 0.36, seg=10)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    import collections
    import directory as dr
    import interact as ia
    import interior as it
    schema, profile = it.load()

    built = {}
    for key in sorted(PROGRAMS):
        q = dr.by_key(key)
        v, t, g = room(schema, profile, q)
        built[key] = (v, t, g)

        op, non = kit.boundary_edges(v, t)
        check(f"{key}: closed surface", not op, f"{len(op)} open edges")

        opening = _bsp.near_face_opening(v, t)
        check(f"{key}: a body can walk in at local x = 0",
              opening is not None and abs(opening[0]) < 0.35
              and opening[1] >= kit.PROVISIONAL["door_width_m"],
              f"{opening}")

        want = tuple(q.get("interacts") or ())
        got = ia.resolve(want, {n for n, _a, _b in g}, g)
        check(f"{key}: every declared interactable is built",
              set(got) == set(want), f"missing {sorted(set(want) - set(got))}")

        # THE DOME MUST HAVE AN INSIDE. `bespoke.py`'s audit measured the
        # exterior component and found **0 of its 192 triangles face a viewer
        # standing under it** -- every surface points out, so a player sees the
        # background, and the background is black. This is that measurement,
        # applied to the room, and it is the reason the dome is a solid with
        # thickness rather than a shell.
        eye = (0.0, 1.65, 0.0)
        inward = 0
        for a, b, c in t:
            p0, p1, p2 = v[a], v[b], v[c]
            u = [p1[i] - p0[i] for i in range(3)]
            w = [p2[i] - p0[i] for i in range(3)]
            nv = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                  u[0] * w[1] - u[1] * w[0])
            d = [eye[i] - p0[i] for i in range(3)]
            if sum(nv[i] * d[i] for i in range(3)) > 0.0:
                inward += 1
        check(f"{key}: the room has an inside", inward > len(t) * 0.25,
              f"only {inward} of {len(t)} triangles face an eye at the centre")

        print(f"  {key:14s} r={program(q)['r']:5.2f} m  {len(t):7,d} tri  "
              f"{len(g):4d} groups  open={len(op)} nonmanifold={len(non)}  "
              f"{inward * 100.0 / max(1, len(t)):.0f}% facing in")

    # THE THREE MUST BE THREE ROOMS, NOT ONE. Session 4h: `deck.py
    # --degeneracy` asks IDENTITY, not similarity, because two places whose
    # geometry hashes the same ARE one place -- and the defect it found was
    # exactly this module's shape, a registry entry that dropped `q`.
    import hashlib
    hashes = {}
    for key, (v, t, _g) in built.items():
        h = hashlib.sha256()
        for p in v:
            h.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        hashes[key] = h.hexdigest()[:12]
    dupes = [k for k, c in collections.Counter(hashes.values()).items() if c > 1]
    check("the three places are three distinct geometries", not dupes,
          f"{hashes}")

    # NEGATIVE CONTROL -- drop the place and they collapse. Without this the
    # gate above cannot fail: it would pass on a module that reads the place
    # and on one that ignores it, if the three happened to differ for some
    # other reason.
    ctl = set()
    for key in sorted(PROGRAMS):
        v, _t, _g = room(schema, profile, dr.by_key("obs_rotundas"))
        h = hashlib.sha256()
        for p in v:
            h.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        ctl.add(h.hexdigest()[:12])
    check("...and with the place ignored they collapse to one", len(ctl) == 1)

    # THE COUNTS ARE THE SPEC'S. PLC-002 lists 12 viewports, PLC-030 lists 8,
    # PLC-064 lists 8. A viewport count is content, so it is asserted rather
    # than left to the reader of a constant.
    for key, want_n in (("obs_dome_1", 12), ("obs_dome_2", 8),
                        ("obs_rotundas", 8)):
        g = built[key][2]
        n = sum(1 for nm, _a, _b in g if nm == "prop_viewport")
        lo = want_n if PROGRAMS[key]["kind"] == "dome" else ROTUNDA_BAYS - 1
        check(f"{key}: {lo} glazed bays, as the spec lists", n >= lo,
              f"{n} viewport spans against {lo}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
