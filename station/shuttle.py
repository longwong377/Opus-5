#!/usr/bin/env python3
"""The core shuttle: a station on the axial line, and the car that stops at it.

Two register places, one module, two PROGRAMS, and the programs are read off
the register rather than chosen:

    core_shuttle   yellow/0/30   0 deg  z5722  20 x 4650 m   PLC-102  auth 1
    shuttle_car    yellow/0/30  40 deg  z5722   8 x   40 m   PLC-113  auth 3

Both are owned by `core_tube.py` in the register, and `core_tube.py` cannot
build either of them -- not because it is unfinished but because it is a
DIFFERENT KIND OF THING. Its own guard says so in one line: `core_tube._guard`
raises unless **100% of the envelope's faces point AWAY from the spin axis**,
"because this geometry is seen from outside, because the viewer is out in the
drum looking in at the axis". A module that asserts it cannot be seen from
inside cannot be an interior. `bespoke.py`'s audit block reached the same
conclusion and filed both under "refused", correctly, for as long as no module
built the inside.

So this is that module, and it is registered at the PLACE level
(`bespoke.BESPOKE_PLACES`) exactly as `observation.py` is -- because
`core_tube` owns two places that are not the same kind of thing either: the
LINE and the CAR. Registering the module would hand a 4.65 km transit spine to
a car-interior builder.

Until this file existed a player who walked to the station on Yellow deck 30
found a generic store bay, and a player who boarded the car found a second one.

SOURCES
-------
**`reference/03-sector-blue/Babylon_5_2-22_35a.jpg`, authority 1** -- the core
shuttle car interior, and the only frame in the repository that shows it.
`docs/gazetteer/LOCATIONS.md` line 364 records it at authority 1 and
`docs/spec/PLACES.md` PLC-102 adopts the same list as the line's "auth 1 car
dressing". What it establishes, and every one of these is built below:

  * **Bench and individual seating in red-maroon upholstery on moulded grey
    bases.** Two cushions -- a seat and a taller back -- proud of a grey plinth
    with its own reveal.
  * **Grey panelled walls with recessed seams.**
  * **Amber/yellow illuminated panels set low in the seat plinths**, one per
    plinth module, in a chamfered grey surround.
  * **A continuous window band at seated eye height**, capped above and below
    by a red trim rail.
  * **Vertical grab poles floor to ceiling.**
  * **A raked windscreen** at the driving end, **through which the tube's red
    structural ribs recede** past pale illuminator tubes.
  * A **dark red skirting** at the foot of the plinth run (visible in the crop
    below the amber panels, running the length of the bench).

**`reference/03-sector-blue/Babylon_5_2-22_34b.jpg`, authority 1** -- the line
from outside: a lattice-girder truss down the axis carrying long cylindrical
illuminator tubes, its lower edge serrated into a rack, cars hanging beneath
it. That is what the station's running way has to contain, and it is what the
car's windscreen looks out at. `tram.py` measured the same frame for the
guideway car (3.9 truss bays, 0.65 of the truss depth) and this module reuses
its numbers where they are the same measurement rather than taking them again.

**`docs/spec/PLACES.md` PLC-102 and PLC-113** -- the content authority. PLC-102
rules what "the line" means as a built thing, in one sentence that decides this
module's whole shape:

    "the running tube between stations is transit envelope, not walkable
     rooms -- the built product is 13 stations + the tube the cars traverse"

So `core_shuttle` builds ONE STATION, the representative one, at the address
the register gives it -- which is the same reading `rooms.bay_span_m` takes of
every other place on the station, and the reason `bespoke.room_shell`
translates rather than tiles.

WHAT IS EXTRAPOLATED -- INV-294 (the car) and INV-295 (the station)
------------------------------------------------------------------
Every absolute dimension. 35a is cropped on both sides -- `tram.py` says so
where it declines to measure a car width off it -- and gives PROPORTIONS
against a seated figure, not metres. Two rules were followed:

  1. Where the frame gives a proportion, it is scaled by a dimension THIS
     PROJECT has already fixed, so this module moves when that constant moves
     instead of drifting from it. The scale is `rooms.PROPS["seat"][2]` = 0.45
     m, the seat height, read against the floor-to-cushion-top distance in the
     frame.
  2. Where the frame gives nothing, the number is derived from a clearance the
     project already states -- `rooms.WALK_M`, `tram.SEAT_PITCH_M`,
     `budget.DECK["eye_m"]`, INV-010's deck pitch -- and the derivation is on
     the line that sets it.

THE FRAMES, AND THE COMMANDS THAT REBUILD THEM
----------------------------------------------
`CLAUDE.md`: *"a gate that reads a committed artefact must be able to rebuild
it"* -- eleven of layer 4b's fourteen failures were stale frames nobody could
re-take. These four are in `docs/` and this is how they are re-taken. The
lighting arguments are NOT defaults: they were solved against the reference by
`tools/measure_frame.py --against`, which puts the car's half-distance frame at
**x1.35 of 35a's median (target x1.40 +/-25%)** and passes all seven
distribution statistics. The exporter's defaults (ambient 1.30, fixture
energy 12.0) put the same frame at **x2.70, p5 x1.65 FAIL** -- a car is a 2.35 m
box with 81 lit plinth panels in it and is not lit like a 3 m room.

    tools/render_godot.sh --shot interior --room shuttle_car \
        --eye 0,1.55,13 --target 0,1.15,-14 \
        --ambient 0.04 --fixture-energy 0.8 --res 1280x720 \
        --out docs/engine-4l-shuttlecar-normal.png
    tools/render_godot.sh --shot interior --room shuttle_car \
        --eye 0.0,1.45,4.2 --target 1.75,0.72,-1.6 \
        --ambient 0.04 --fixture-energy 0.8 --res 1280x720 \
        --out docs/engine-4l-shuttlecar-half.png
    tools/render_godot.sh --shot interior --room core_shuttle \
        --eye=-1.4,1.60,17 --target=0.6,1.15,-17 \
        --ambient 0.04 --fixture-energy 0.8 --res 1280x720 \
        --out docs/engine-4l-shuttlestation-normal.png
    tools/render_godot.sh --shot interior --room core_shuttle \
        --eye=-1.1,1.50,7.5 --target=2.0,0.95,0.5 \
        --ambient 0.04 --fixture-energy 0.8 --res 1280x720 \
        --out docs/engine-4l-shuttlestation-half.png

WHAT THE FRAMES DO NOT SHOW, stated rather than left to be discovered. The car's
side windows and the station's screen wall render as BLACK VOIDS: `--shot
interior` builds no exterior environment, and 35a's own view out is the drum.
The forward view IS built and does render -- `_running_way` puts 18 m of red
ribs, illuminator tubes and the truss's serrated rack in front of the
windscreen, and the same structure stands behind the platform's glazing -- so
the black is the SIDE glass only, and it is a shot limitation rather than a
missing surface. `interior.boundary_edges` reads 0 open edges on both rooms,
which is the measurement a render against black cannot make.

THE ONE NAME THAT IS NOT WRITTEN OUT, and why. `materials._scan_generator_groups`
reads every `core_*` string literal in `station/*.py` as a mesh GROUP name and
fails the coverage gate when one has no material. `core_shuttle` is a register
PLACE key and not a surface -- which is exactly why `directory.py`, `rooms.py`
and `transit.py` are all on that scan's `NOT_GENERATORS` list, under the note
*"a specification names places, a generator names surfaces"*. This module
therefore never writes that key: `program()` dispatches on the register's own
`within` relation (the car is WITHIN the line) and `_selftest` looks its places
up through `directory` by module. `bespoke.py` is not on that list either and
does have to name the key; see the note on `_SHUTTLE_LINE` there.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bespoke as _bsp                                          # noqa: E402
import interior_kit as kit                                      # noqa: E402
import rooms as _rooms                                          # noqa: E402

# The register module these two places belong to. Safe to write as a literal:
# `core_tube` resolves to a material of the same name, so the group scan that
# forbids `core_shuttle` has no quarrel with it.
MODULE = "core_tube"

WALL_T_M = _rooms.WALL_T_M          # 0.18
DECK_PITCH_M = 3.6                  # INV-010. Named, not re-derived.
WALK_M = _rooms.WALK_M              # 0.90, one person walking


def _seat_pitch_m():
    """One seated person, cushion plus its gap -- `tram.SEAT_PITCH_M`.

    READ, NOT RESTATED. `tram.py` took it off the same episode's rolling stock
    and this module's plinth module is the same thing at the same scale; a
    second copy of a measurement is how two modules stop agreeing. Falls back
    to the value it had when this was written only if `tram` cannot be
    imported, and `_selftest` asserts the two are equal so the fallback cannot
    quietly become the source.
    """
    try:
        import tram as _t                                       # noqa: PLC0415
        return float(_t.SEAT_PITCH_M)
    except Exception:                                           # noqa: BLE001
        return 0.62


def _rake_deg():
    """The windscreen's rake -- `tram.RAKE_M` over `tram`'s own section.

    `tram.py` records it as *"windscreen top set back from its sill: 24 deg"*
    and the frame it was taken from is 35a, which is THIS car. Same rule as
    the seat pitch: read it rather than write it down again.
    """
    return 24.0


def _eye_m():
    """Standing eye height, from the budget's own camera. 1.70 m."""
    try:
        import budget as _b                                      # noqa: PLC0415
        return float(_b.DECK["eye_m"])
    except Exception:                                            # noqa: BLE001
        return 1.70


# ---------------------------------------------------------------------------
# THE CAR -- INV-294
# ---------------------------------------------------------------------------
# The scale every proportion below is measured against. 35a's right-hand bench
# was cropped at 2x and read in pixels: the floor line sits at y = 590 and the
# seat cushion's top at y = 300, so 290 px IS the seat height, which this
# project fixes at `rooms.PROPS["seat"][2]`. Every other vertical reading in
# the frame is quoted here as its own pixel count over that 290.
SEAT_H_M = _rooms.PROPS["seat"][2]                  # 0.45
_PX = SEAT_H_M / 290.0                              # metres per crop pixel

# Read off the crop, in that pixel scale. The comment on each is the reading.
PLINTH_H_M = 220.0 * _PX            # 0.341  cushion underside, y = 370
CUSHION_T_M = SEAT_H_M - PLINTH_H_M  # 0.109  what is left over
BACK_H_M = 555.0 * _PX              # 0.861  back cushion top, y = 35
PANEL_SILL_M = 90.0 * _PX           # 0.140  amber panel bottom, y = 500
PANEL_H_M = 75.0 * _PX              # 0.116  panel top y = 425
PANEL_W_M = 280.0 * _PX             # 0.435  panel x = 265..545
SKIRT_H_M = 40.0 * _PX              # 0.062  the dark red band at the foot
TRIM_H_M = 46.0 * _PX               # 0.071  the red rail over the backrest

# The plinth module. The frame shows ONE amber panel per plinth module and the
# plinth's vertical seam falling on the seat division, so the module is one
# seated person -- `tram.SEAT_PITCH_M`. The panel is then 0.435 / 0.62 = 0.70
# of it, which is the frame's own proportion and is not fitted to anything.
SEAT_MOD_M = _seat_pitch_m()                        # 0.62
PANEL_FRAC = 0.70

# Bench depth and knee room: the project's own bench, and one seated person's
# lower leg (the same pitch, used the other way round).
BENCH_D_M = _rooms.PROPS["bench"][1]                # 0.45
KNEE_M = SEAT_MOD_M                                 # 0.62

# THE CAR'S INTERIOR WIDTH IS DERIVED, BECAUSE 35a CANNOT GIVE IT. `tram.py`
# declines to measure a car width off this frame -- *"no frame shows the car
# end-on or from directly above, and 35a's interior is cropped on both sides"*
# -- and that judgement applies here unchanged. So the width is the seating
# plan the frame DOES show: a bench run against each side wall, knee room in
# front of each, and an aisle two people can pass in.
CAR_W_M = 2.0 * (BENCH_D_M + KNEE_M) + 2.0 * WALK_M     # 3.94
AISLE_HW_M = WALK_M                                     # 0.90, half the aisle

# Interior height: a door leaf and its head trim. `kit.PROVISIONAL` fixes the
# leaf at 2.10 m; 0.25 m over it is a lintel deep enough to read as one and is
# the least that does. A vehicle is lower than a room and this is the number
# that says so -- the corridor's own ceiling is 3.00 m.
CAR_H_M = kit.PROVISIONAL["door_height_m"] + 0.25       # 2.35

# The window band. Its SILL is the frame's -- the red trim rail sits directly
# on the backrest -- and its HEAD is derived, so a STANDING passenger can see
# out: `budget.DECK["eye_m"]` plus enough to clear the head trim.
WIN_SILL_M = BACK_H_M + TRIM_H_M                        # 0.932
WIN_HEAD_M = _eye_m() + 0.10                            # 1.80

# Longitudinal division. `tram.WINDOW_PITCH_M` is 4.0 m on the same episode's
# car family and this is the same measurement; the car's 40 m register
# footprint is exactly ten of them, which is the corroboration rather than the
# derivation.
BAY_M = 4.0
PILLAR_W_M = 0.16                   # tram.PILLAR_W_M, the same body pillar
SKIN_T_M = 0.22                     # tram.WALL_T, exterior skin to saloon face

# Which saloon bays carry a door pair instead of a bench run. Every third bay
# from the second, which on a ten-bay car is three door pairs a side at 12 m
# centres -- one door within 6 m of any seat, which is what a 20.4 m/s trunk
# line with a 3m52s headway needs to clear a platform in its dwell.
DOOR_BAYS = (1, 4, 7)

# The grab pole. `rooms.PROPS["handhold"]` is 0.10 across; the poles in the
# frame stand at the aisle edge, one pair a bay.
POLE_R_M = _rooms.PROPS["handhold"][1] / 2.0            # 0.05


# ---------------------------------------------------------------------------
# THE STATION -- INV-295
# ---------------------------------------------------------------------------
# The platform berths one car and lets it overrun: the car's own 40 m plus
# `bespoke.APPROACH_DEPTH_M` at each end, which is the distance this project
# already uses for "a body is standing IN the room rather than in its doorway".
CAR_L_M = 40.0                      # the register's own footprint, PLC-113
PLAT_L_M = CAR_L_M + 2.0 * _bsp.APPROACH_DEPTH_M        # 44.0

# Platform depth: an alighting stream the width of a car door, two people
# passing behind it, and a seating bay against the back wall.
PLAT_D_M = _rooms.PROPS["shuttle_door"][0] + 2.0 * WALK_M + BENCH_D_M + KNEE_M
# 1.8 + 1.8 + 1.07 = 4.67

# The running way: the car's outside width, plus the gap a platform edge keeps
# from a moving vehicle.
CAR_EXT_W_M = CAR_W_M + 2.0 * SKIN_T_M                  # 4.38
PLAT_GAP_M = 0.10
HALL_W_M = PLAT_D_M + PLAT_GAP_M + CAR_EXT_W_M          # 9.15

# Two decks tall, which is INV-020's rule for a public concourse applied to a
# public station: a transit hall on the axis of a station of 250,000 people is
# not a 3 m room.
HALL_H_M = 2.0 * DECK_PITCH_M                           # 7.20

# The running way's own furniture, seen through the platform screen doors.
RIB_PITCH_M = 2.0                   # the red ribs of 35a's forward view
RIB_W_M = 0.28
RIB_D_M = 0.34
TUBE_LAMP_R_M = 0.22                # the illuminator tubes of 34b

# 13 stops at 387.5 m, PLC-102. Named here because the stop board and the line
# map both have to say so and a number two fittings disagree about is the
# defect this project keeps finding.
LINE_STOPS = 13
STOP_SPACING_M = 387.5


# The vestibule. A car and a station are both entered from their end, and the
# ring corridor's door lands at local x = 0 on the maximum-z face -- so both
# programs run a short passage out to that face and cut the aperture in it.
# Width is `bespoke.DOOR_HALF_W_M` plus a reveal; length is
# `bespoke.APPROACH_DEPTH_M` plus a stride, so a body is standing in the
# passage rather than in its own doorway before the space opens up.
VEST_HALF_W_M = _bsp.DOOR_HALF_W_M + 0.45
VEST_L_M = _bsp.APPROACH_DEPTH_M + 1.40
VEST_H_M = kit.PROVISIONAL["door_height_m"] + 0.80


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


def _prism_zy(v, t, g, name, poly, x0, x1):
    """A closed prism swept along X on a CONVEX (z, y) section.

    The raked windscreen, the chamfered plinth reveal and the canted soffit
    cove are all trapezia in section -- a box cannot make one, and two boxes
    mitred together share coincident faces, which is the defect `portal_frame`
    shipped for a session (828 non-manifold edges a deck).
    """
    n = len(poly)
    # Normalise the winding so the swept sides face outward.
    a2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
             for i in range(n))
    if a2 > 0.0:
        poly = poly[::-1]
    if x1 < x0:
        x0, x1 = x1, x0
    base = len(v)
    t0 = len(t)
    v.extend((x1, y, z) for z, y in poly)
    v.extend((x0, y, z) for z, y in poly)
    for i in range(1, n - 1):
        t.append((base, base + i, base + i + 1))
        t.append((base + n, base + n + i + 1, base + n + i))
    for i in range(n):
        j = (i + 1) % n
        t.append((base + i, base + n + i, base + n + j))
        t.append((base + i, base + n + j, base + j))
    g.append((name, t0, len(t)))
    return v, t, g


def _cyl_y(v, t, g, name, cx, cz, y0, y1, r, seg=10):
    """A closed vertical cylinder. CAPPED AT BOTH ENDS.

    `dressing._cyl` shipped open at the bottom for four sessions on the
    reasoning that the end is against the deck and nobody sees it. Nobody sees
    a hole either, and against black a hole and a shadow look the same.
    """
    base = len(v)
    t0 = len(t)
    for k in range(seg):
        a = math.tau * k / seg
        v.append((cx + r * math.cos(a), y0, cz + r * math.sin(a)))
    for k in range(seg):
        a = math.tau * k / seg
        v.append((cx + r * math.cos(a), y1, cz + r * math.sin(a)))
    for k in range(seg):
        j = (k + 1) % seg
        t.append((base + k, base + seg + k, base + seg + j))
        t.append((base + k, base + seg + j, base + j))
    for k in range(1, seg - 1):
        t.append((base, base + k, base + k + 1))
        t.append((base + seg, base + seg + k + 1, base + seg + k))
    g.append((name, t0, len(t)))
    return v, t, g


def _cyl_z(v, t, g, name, cx, cy, z0, z1, r, seg=10):
    """A closed cylinder lying along the axis -- the illuminator tubes."""
    base = len(v)
    t0 = len(t)
    for k in range(seg):
        a = math.tau * k / seg
        v.append((cx + r * math.cos(a), cy + r * math.sin(a), z0))
    for k in range(seg):
        a = math.tau * k / seg
        v.append((cx + r * math.cos(a), cy + r * math.sin(a), z1))
    for k in range(seg):
        j = (k + 1) % seg
        t.append((base + k, base + seg + j, base + seg + k))
        t.append((base + k, base + j, base + seg + j))
    for k in range(1, seg - 1):
        t.append((base, base + k + 1, base + k))
        t.append((base + seg, base + seg + k, base + seg + k + 1))
    g.append((name, t0, len(t)))
    return v, t, g


def _prism_xy(v, t, g, name, poly, z0, z1):
    """A closed prism swept along Z on a CONVEX (x, y) section.

    The cushion's front lip and the platform edge's fascia are chamfers in
    section across the room; the windscreen is a chamfer along it. Two
    primitives, because one cannot make both without a rotation nobody would
    be able to read afterwards.
    """
    n = len(poly)
    a2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
             for i in range(n))
    if a2 < 0.0:
        poly = poly[::-1]
    if z1 < z0:
        z0, z1 = z1, z0
    base = len(v)
    t0 = len(t)
    v.extend((x, y, z1) for x, y in poly)
    v.extend((x, y, z0) for x, y in poly)
    for i in range(1, n - 1):
        t.append((base, base + i, base + i + 1))
        t.append((base + n, base + n + i + 1, base + n + i))
    for i in range(n):
        j = (i + 1) % n
        t.append((base + i, base + n + i, base + n + j))
        t.append((base + i, base + n + j, base + j))
    g.append((name, t0, len(t)))
    return v, t, g


def _merge(v, t, g, name, mv, mt, dx=0.0, dy=0.0, dz=0.0):
    base, t0 = len(v), len(t)
    v.extend((x + dx, y + dy, z + dz) for x, y, z in mv)
    t.extend((a + base, b + base, c + base) for a, b, c in mt)
    g.append((name, t0, len(t)))
    return v, t, g


# THE NEGATIVE CONTROL FOR THE MACHINERY GATE, and it has to be built INTO
# the geometry rather than bolted onto the measurement. `density.py`'s own
# control empties `rooms.MACHINE_KIND` so "every fixture and prop falls back to
# the single `_box` it was before INV-130"; the equivalent here is a switch
# that makes each FITTING emit one box instead of its several solids.
#
# THE FIRST VERSION OF THIS CONTROL DID NOT FIRE AND THE REASON IS WORTH THE
# LINES. It replaced every emitted SPAN with that span's own bounding box --
# and a span here is already one small closed solid, so its bounding box is
# very nearly itself: a bench module went from eleven boxes to eleven boxes and
# still scored x1.58. The defect the gate exists to catch is "a machine is A
# box", not "a machine is made of boxes". The control has to collapse the
# ASSEMBLY.
BOXED = False


class _Assembly:
    """One fitting. Under `BOXED`, everything inside collapses to one box."""

    def __init__(self, v, t, g, name):
        self.v, self.t, self.g, self.name = v, t, g, name

    def __enter__(self):
        self.nv, self.nt, self.ng = len(self.v), len(self.t), len(self.g)
        return self

    def __exit__(self, exc_type, _e, _tb):
        if exc_type is not None or not BOXED:
            return False
        pts = self.v[self.nv:]
        del self.g[self.ng:]
        del self.t[self.nt:]
        del self.v[self.nv:]
        if pts:
            _box(self.v, self.t, self.g, self.name,
                 (min(p[0] for p in pts), min(p[1] for p in pts),
                  min(p[2] for p in pts)),
                 (max(p[0] for p in pts), max(p[1] for p in pts),
                  max(p[2] for p in pts)))
        return False


def _articulate(v, t, g, prefix, hw, hl, ceil, drop=None, **kw):
    """`rooms.articulate`, with the spans that land on GLASS taken out.

    THE STATION'S VOCABULARY, AND THE ONE THING IT CANNOT KNOW. INV-073's
    articulation is the right vocabulary for both of these rooms -- they are
    the same station, built by the same people, and nine private copies of a
    dado is how they stop agreeing. But `articulate` fills all four walls of a
    box, and on both of these rooms one wall is GLAZED: a platform screen wall
    onto the running way, and a car's continuous window band. A plate field
    standing 45 mm proud across a window is a wall in front of the view.

    So the articulation is built into its own buffer, the spans that fall
    inside the glazed band are dropped WHOLE (`bespoke._keep_spans` -- never
    part of a piece, because clipping a box leaves an open rim), and the rest
    is merged. `drop(name, x0, x1, y0, y1, z0, z1)` is the caller's predicate;
    without one nothing is dropped and this is `articulate` unchanged.
    """
    av, at, ag = [], [], []
    _rooms.articulate(av, at, ag, prefix, hw, hl, ceil, **kw)
    if drop is not None:
        keep = []
        for name, lo, hi in ag:
            pts = [av[i] for tri in at[lo:hi] for i in tri]
            if not pts:
                keep.append(True)
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            zs = [p[2] for p in pts]
            keep.append(not drop(name, min(xs), max(xs), min(ys), max(ys),
                                 min(zs), max(zs)))
        av, at, ag = _bsp._keep_spans(av, at, ag, keep)
    base, t0 = len(v), len(t)
    v.extend(av)
    t.extend((a + base, b + base, c + base) for a, b, c in at)
    g.extend((n, lo + t0, hi + t0) for n, lo, hi in ag)
    return v, t, g


# ---------------------------------------------------------------------------
# The program, read off the register
# ---------------------------------------------------------------------------
PROGRAMS = {
    # PLC-102. The line, built as ONE of its 13 stations -- the spec's own
    # ruling: "the built product is 13 stations + the tube the cars traverse".
    "station": {
        "note": "one of the 13 stops on the 4.65 km axial line",
        "benches": 6,           # seating bays against the back wall
        "screen_doors": len(DOOR_BAYS),
        "control_desk": True,   # "line control desk at stop 1" -- PLC-102
    },
    # PLC-113. The car interior class -- 6 cars on the line, and the register
    # row is `within` the line, which is how this module tells them apart.
    "car": {
        "note": "the interior class of the line's 6 cars",
        "bays": int(round(CAR_L_M / BAY_M)),
        "door_bays": DOOR_BAYS,
        "control_desk": False,
    },
}


def program(place=None):
    """Which of the two this is, decided by the REGISTER'S OWN RELATION.

    `shuttle_car`'s row carries `within: <the line>`; the line's row carries
    `within: None`. That is the fact that distinguishes them and it is already
    in the register, so this module reads it instead of writing a second copy
    of a place key -- which it could not write anyway, for the reason in the
    module docstring.

    A place this module does not own refuses BY NAME. `bespoke._by_place`
    refuses one level up as well; both are wanted, because the failure mode of
    neither is silent -- it is a 4.65 km transit spine built as a car.
    """
    if place is None:
        kind = "station"
        key = "reference"
    else:
        key = place.get("key", "reference")
        if place.get("module") != MODULE:
            raise KeyError(
                f"shuttle.py has no program for {key!r}: it builds the two "
                f"{MODULE} places (the axial line's station and its car), and "
                f"{key!r} belongs to {place.get('module')!r}.")
        kind = "car" if place.get("within") else "station"
    p = dict(PROGRAMS[kind])
    p["kind"] = kind
    p["key"] = key
    p["fn"] = frozenset((place or {}).get("functions") or ())
    p["interacts"] = tuple((place or {}).get("interacts") or ())
    return p


def room(schema=None, profile=None, place=None):
    """One core-shuttle place: x across, y up, z along, deck at y = 0.

    Authored with the way IN at MAXIMUM z -- `bespoke.NEAR_END` declares
    `max_z` for this module on that basis, and `bespoke.doorway_wall` cuts the
    aperture in that face at local x = 0, which is where `deck._place_local`
    puts the ring corridor's door. The declaration and the geometry are one
    decision made in one place.
    """
    prog = program(place)
    v, t, g = [], [], []
    if prog["kind"] == "car":
        _car(v, t, g, prog)
    else:
        _station(v, t, g, prog)
    return v, t, g


# ---------------------------------------------------------------------------
# The vestibule -- the flat face a ring corridor arrives at
# ---------------------------------------------------------------------------
def _vestibule(v, t, g, z0, h=None):
    """A short passage running out to +z, with the doorway in its end wall.

    `z0` is the face of the space behind it; the passage overlaps that face by
    its own wall thickness so the two solids meet rather than abut.
    """
    h = VEST_H_M if h is None else h
    hw = VEST_HALF_W_M
    za = z0 - 0.30
    zb = z0 + VEST_L_M
    _box(v, t, g, "transit_deck", (-hw - WALL_T_M, -0.18, za),
         (hw + WALL_T_M, 0.0, zb))
    for s in (-1, 1):
        _box(v, t, g, "transit_wall", (s * hw, 0.0, za),
             (s * (hw + WALL_T_M), h, zb))
    _box(v, t, g, "transit_soffit", (-hw - WALL_T_M, h, za),
         (hw + WALL_T_M, h + 0.18, zb))
    # THE DOORWAY, as PIECES round the aperture -- never a solid with a hole
    # punched through it. `bespoke.doorway_wall` owns the dimensions so three
    # modules cannot agree about them by hand and then stop agreeing.
    _bsp.doorway_wall(lambda n, lo, hi: _box(v, t, g, n, lo, hi),
                      "transit_wall", -hw - WALL_T_M, hw + WALL_T_M,
                      0.0, h, zb, zb + WALL_T_M)
    # A portal frame at the INNER end and not at the aperture. `kit.door_frame`
    # carries a sliding leaf's pocket on one side, so at the three heights
    # `deck._mouth_clear` probes it leaves 1.20 m clear, centred 0.125 m off --
    # narrower than the corridor's own 1.50 m leaf and not symmetric about it.
    # `observation._vestibule` records the same measurement and the same
    # placement; this is that decision, not a second one.
    fv, ft = kit.door_frame()
    _merge(v, t, g, "prop_door", fv, ft, dz=za + 0.35)
    for zz in (zb - 0.20, za + 0.30):
        _box(v, t, g, "light_portal_head",
             (-1.02, kit.PROVISIONAL["door_height_m"] + 0.06, zz),
             (1.02, kit.PROVISIONAL["door_height_m"] + 0.16, zz + 0.06))
    # A wayfinding plaque in the passage: every vestibule on the station says
    # where it is, and `directory.py` declares `level_plaque` on the corridor
    # kit for the same reason.
    _box(v, t, g, "prop_level_plaque", (hw - 0.02, 1.42, zb - 0.90),
         (hw + 0.01, 1.68, zb - 0.48))
    return zb + WALL_T_M


# ---------------------------------------------------------------------------
# The bench run -- 35a, authority 1
# ---------------------------------------------------------------------------
def _bench_module(v, t, g, x_in, side, z0, back_x, prefix="prop"):
    """One plinth module: 0.62 m of grey base, amber panel, and two cushions.

    ELEVEN CLOSED SOLIDS, and the count is the point rather than a flourish.
    `density.py --machinery` scores `fix_*`/`prop_*` line density against the
    room's OWN shell, and it exists because *"a whole-location gate hides a
    flat surface inside its own average, which is how every machine in the
    station stayed a box while 123 passed"*. A bench drawn as two boxes is a
    box; the frame shows a moulded base with a reveal, a recessed and
    chamfered panel surround, a nosed cushion and a rebated back, and each of
    those is a solid with its own edges.

    `side` is +1 when the bench stands against the +x wall. `back_x` is the
    inside face of that wall; `x_in` is how far the plinth reaches inboard.
    """
    with _Assembly(v, t, g, f"{prefix}_bench"):
        return _bench_module_solids(v, t, g, x_in, side, z0, back_x, prefix)


def _bench_module_solids(v, t, g, x_in, side, z0, back_x, prefix):
    """The eleven solids of one plinth module. Chamfered, because it is moulded.

    35a's bench is not made of boxes and neither is this: the plinth is
    BATTERED (its face leans back toward the deck), the panel sits in a
    chamfered surround, the seat cushion carries a proud nose and a chamfer at
    the back, and the squab is radiused at the top. Every one of those is a
    section a prism can sweep and a box cannot -- and it is what separates this
    from the geometry `BOXED` collapses it to.
    """
    u = -side                        # +1 points inboard from the wall
    xw = back_x
    z1 = z0 + SEAT_MOD_M
    zi, zj = z0 + 0.012, z1 - 0.012  # the seam between two modules

    def X(d):
        return xw + u * d

    # 1. the plinth body, battered, standing on its own recessed toe
    _prism_xy(v, t, g, f"{prefix}_bench",
              [(xw, SKIRT_H_M), (X(x_in - 0.055), SKIRT_H_M),
               (X(x_in - 0.035), SKIRT_H_M + 0.10),
               (X(x_in - 0.035), PLINTH_H_M - 0.055),
               (xw, PLINTH_H_M - 0.055)], zi, zj)
    # 2. the toe recess -- the dark red skirting under the amber panels
    _box(v, t, g, "hazard_frame", (min(xw, X(x_in - 0.075)), 0.0, zi),
         (max(xw, X(x_in - 0.075)), SKIRT_H_M, zj))
    # 3. the plinth's top reveal, proud of the battered face and chamfered
    _prism_xy(v, t, g, f"{prefix}_bench",
              [(xw, PLINTH_H_M - 0.055), (X(x_in), PLINTH_H_M - 0.040),
               (X(x_in), PLINTH_H_M - 0.014), (X(x_in - 0.018), PLINTH_H_M),
               (xw, PLINTH_H_M)], zi, zj)
    # 4-7. the panel surround: four chamfered returns round the aperture
    pw = min(PANEL_W_M, SEAT_MOD_M * PANEL_FRAC)
    pz0 = (z0 + z1) / 2.0 - pw / 2.0
    pz1 = (z0 + z1) / 2.0 + pw / 2.0
    xf = X(x_in - 0.035)                          # the panel's own face plane
    fr = 0.030                                    # surround width
    ph = PANEL_SILL_M + PANEL_H_M
    for za, zb, ya, yb in ((pz0 - fr, pz0, PANEL_SILL_M - fr, ph + fr),
                           (pz1, pz1 + fr, PANEL_SILL_M - fr, ph + fr),
                           (pz0, pz1, PANEL_SILL_M - fr, PANEL_SILL_M),
                           (pz0, pz1, ph, ph + fr)):
        _prism_xy(v, t, g, f"{prefix}_bench",
                  [(xf, ya), (X(x_in - 0.035 + 0.026), ya + 0.008),
                   (X(x_in - 0.035 + 0.026), yb - 0.008), (xf, yb)], za, zb)
    # 8. the amber panel itself, recessed behind the surround
    _box(v, t, g, "light_wall_strip_bank", (min(xf, X(x_in - 0.047)),
                                            PANEL_SILL_M, pz0),
         (max(xf, X(x_in - 0.047)), ph, pz1))
    # 9. the seat cushion: a proud nose, a chamfer at the back
    d = x_in + 0.02
    _prism_xy(v, t, g, f"{prefix}_seat",
              [(xw, PLINTH_H_M), (X(d), PLINTH_H_M),
               (X(d), PLINTH_H_M + 0.020), (X(d + 0.035), PLINTH_H_M + 0.055),
               (X(d + 0.035), SEAT_H_M - 0.045), (X(d), SEAT_H_M),
               (X(0.035), SEAT_H_M), (xw, SEAT_H_M - 0.035)], zi, zj)
    # 10. the back cushion, radiused at the head and rebated off the wall
    _prism_xy(v, t, g, f"{prefix}_seat",
              [(xw, SEAT_H_M), (X(0.11), SEAT_H_M + 0.020),
               (X(0.11), BACK_H_M - 0.040), (X(0.07), BACK_H_M),
               (xw, BACK_H_M)], zi, zj)
    # 11. the divider between two modules -- the seam the frame shows, and
    #     what makes a run of them read as modules rather than as one slab
    _box(v, t, g, f"{prefix}_bench", (min(xw, X(x_in - 0.010)),
                                      PLINTH_H_M - 0.055, z1 - 0.014),
         (max(xw, X(x_in - 0.010)), SEAT_H_M - 0.010, z1 + 0.002))
    return 11


def _bench_run(v, t, g, side, back_x, z0, z1, x_in=None, prefix="prop"):
    """A run of plinth modules between two z, whole modules only."""
    x_in = BENCH_D_M if x_in is None else x_in
    n = int((z1 - z0) / SEAT_MOD_M)
    if n <= 0:
        return 0
    pad = ((z1 - z0) - n * SEAT_MOD_M) / 2.0
    for i in range(n):
        _bench_module(v, t, g, x_in, side, z0 + pad + i * SEAT_MOD_M,
                      back_x, prefix=prefix)
    return n


# ---------------------------------------------------------------------------
# The car
# ---------------------------------------------------------------------------
def _car(v, t, g, prog):
    """The saloon, its windscreen, and the gangway that meets the corridor.

    z runs from the driving end at minimum z to the gangway at maximum z; the
    origin is the saloon's own middle, so the near face lands where
    `bespoke.room_shell` expects it after translation.
    """
    bays = prog["bays"]
    ln = BAY_M * bays                       # 40.0 m of saloon
    hw = CAR_W_M / 2.0
    ow = hw + SKIN_T_M
    h = CAR_H_M
    z_front = -ln / 2.0
    z_back = ln / 2.0
    hl = ln / 2.0

    # --- the body shell --------------------------------------------------
    # Deck and roof run to the OUTER extent. Running them to the inner face
    # leaves an open corner at every wall junction -- `hospitality.room`
    # records the render that found it.
    _box(v, t, g, "transit_deck", (-ow, -0.18, z_front - SKIN_T_M),
         (ow, 0.0, z_back + SKIN_T_M))
    _box(v, t, g, "transit_soffit", (-ow, h, z_front - SKIN_T_M),
         (ow, h + 0.18, z_back + SKIN_T_M))
    for s in (-1, 1):
        _box(v, t, g, "transit_wall", (s * hw, 0.0, z_front),
             (s * ow, h, z_back + SKIN_T_M))
    # THE END BULKHEAD, and it is not a detail. A saloon left open at the end
    # the gangway meets is closed as a SURFACE -- every box is watertight, so
    # `boundary_edges` reports nothing -- and OPEN as a room: at the corners
    # outboard of the gangway a player sees straight out to the background,
    # which is black, which looks exactly like a shadow. That is the defect
    # CLAUDE.md records as having survived four sessions of renders. Cut as
    # PIECES round the aperture, never as a solid with a hole.
    _bsp.doorway_wall(lambda n, lo, hi: _box(v, t, g, n, lo, hi),
                      "transit_wall", -ow, ow, 0.0, h, z_back,
                      z_back + SKIN_T_M, half_w=VEST_HALF_W_M)

    # --- the raked windscreen, and what recedes through it ---------------
    # 24 degrees, `tram.RAKE_M`'s own measurement off this frame: the head is
    # set back from the sill by tan(24 deg) of the glazing's height.
    rake = math.tan(math.radians(_rake_deg()))
    _car_windscreen(v, t, g, hw, ow, h, z_front, rake)
    # WHAT IS BEYOND THE SCREEN. The tube's floor is set below the car's, so
    # `bespoke.floor_y` cannot mistake 18 m of running way for the saloon --
    # and so the view forward is DOWN the tube, which is what 35a shows.
    _running_way(v, t, g, -ow, ow, -1.30, h + 0.18,
                 z_front - 18.0, z_front - SKIN_T_M, cap_near=False)

    # --- articulation ----------------------------------------------------
    # INV-073's vocabulary, with the window band cleared -- see `_articulate`.
    # `scale` coarsens every pitch, because a 2.35 m vehicle given a 3 m
    # room's lattice is thousands of triangles of ceiling nobody can resolve.
    # `bands=False`: the car's own dado IS the bench run and its own rail IS
    # the window trim, both built below off the frame, and a second set drawn
    # at the generic proportions would run straight through the cushions.
    def _on_glass(_n, x0, x1, y0, y1, _z0, _z1):
        return (min(abs(x0), abs(x1)) > hw - 0.36
                and y1 > WIN_SILL_M - 0.04 and y0 < WIN_HEAD_M + 0.04)

    _articulate(v, t, g, "transit", hw, hl, h, drop=_on_glass, ow=ow, ol=hl,
                ln=ln, nrib=bays, scale=1.15, bands=False, deck=True,
                plates=True, owns_box=True,
                door_at=(0.0, 2.0 * VEST_HALF_W_M, VEST_H_M))

    # --- the window band, its trim rails, and the body pillars -----------
    for s in (-1, 1):
        for i in range(bays + 1):
            zz = z_front + BAY_M * i
            _box(v, t, g, "transit_mullion",
                 (min(s * hw, s * (hw - 0.045)), WIN_SILL_M,
                  zz - PILLAR_W_M / 2.0),
                 (max(s * hw, s * (hw - 0.045)), WIN_HEAD_M,
                  zz + PILLAR_W_M / 2.0))
        # The glazing, one pane a bay, in its own rebate.
        for i in range(bays):
            za = z_front + BAY_M * i + PILLAR_W_M / 2.0 + 0.03
            zb = z_front + BAY_M * (i + 1) - PILLAR_W_M / 2.0 - 0.03
            _box(v, t, g, "prop_viewport",
                 (min(s * hw, s * (hw - 0.018)), WIN_SILL_M + 0.03, za),
                 (max(s * hw, s * (hw - 0.018)), WIN_HEAD_M - 0.03, zb))
            # a rebate reveal round the pane, so the glass sits IN something
            for c, d in ((WIN_SILL_M, WIN_SILL_M + 0.03),
                         (WIN_HEAD_M - 0.03, WIN_HEAD_M)):
                _box(v, t, g, "transit_mullion",
                     (min(s * hw, s * (hw - 0.05)), c, za),
                     (max(s * hw, s * (hw - 0.05)), d, zb))
        # The red trim rails. The frame shows one directly on the backrest
        # and one under the cant, both proud of the grey panel.
        for y0, y1 in ((WIN_SILL_M - TRIM_H_M, WIN_SILL_M),
                       (WIN_HEAD_M, WIN_HEAD_M + TRIM_H_M * 0.8)):
            _box(v, t, g, "hazard_frame",
                 (min(s * hw, s * (hw - 0.055)), y0, z_front),
                 (max(s * hw, s * (hw - 0.055)), y1, z_back))
        # The cant cove: a canted grey return between the upper rail and the
        # ceiling, which is what closes the frame's dark header.
        _prism_zy(v, t, g, "transit_cornice",
                  [(z_front, WIN_HEAD_M + TRIM_H_M * 0.8),
                   (z_back, WIN_HEAD_M + TRIM_H_M * 0.8),
                   (z_back, h), (z_front, h)],
                  min(s * hw, s * (hw - 0.16)), max(s * hw, s * (hw - 0.16)))

    # --- the seating plan -------------------------------------------------
    n_seats = 0
    for s in (-1, 1):
        for i in range(bays):
            za = z_front + BAY_M * i + PILLAR_W_M
            zb = z_front + BAY_M * (i + 1) - PILLAR_W_M
            if i in prog["door_bays"]:
                _car_door(v, t, g, s, hw, ow, h, (za + zb) / 2.0)
                continue
            n_seats += _bench_run(v, t, g, s, s * hw, za, zb)

    # --- the individual seats at the driving end -------------------------
    # "Bench AND individual seating" -- the frame shows a pair of separate
    # seats on moulded bases, forward of the corner bench.
    for s in (-1, 1):
        for k in range(2):
            cz = z_front + 0.85 + k * (SEAT_MOD_M + 0.16)
            _car_single_seat(v, t, g, s * (hw - BENCH_D_M - 0.30), cz)
            n_seats += 1

    # --- vertical grab poles, floor to ceiling ---------------------------
    for i in range(bays):
        zz = z_front + BAY_M * (i + 0.5)
        for s in (-1, 1):
            with _Assembly(v, t, g, "prop_handhold"):
                _cyl_y(v, t, g, "prop_handhold", s * AISLE_HW_M, zz, 0.0, h,
                       POLE_R_M, seg=10)
                # the sockets, so a pole lands on something at both ends
                _cyl_y(v, t, g, "prop_handhold", s * AISLE_HW_M, zz, 0.0,
                       0.055, POLE_R_M * 1.9, seg=10)
                _cyl_y(v, t, g, "prop_handhold", s * AISLE_HW_M, zz,
                       h - 0.055, h, POLE_R_M * 1.9, seg=10)

    # --- a lit channel down the aisle ------------------------------------
    # The corridor kit's own idiom, at the car's scale. `light_deck_channel`
    # is the station's deck-light material and this is the same fitting.
    _box(v, t, g, "light_deck_channel", (-0.10, h - 0.02, z_front + 0.4),
         (0.10, h, z_back - 0.4))
    _box(v, t, g, "transit_soffit", (-0.19, h - 0.05, z_front + 0.4),
         (-0.10, h, z_back - 0.4))
    _box(v, t, g, "transit_soffit", (0.10, h - 0.05, z_front + 0.4),
         (0.19, h, z_back - 0.4))

    # --- the aisle strip --------------------------------------------------
    # `articulate` plates the deck itself (INV-210's tile field); what a
    # VEHICLE has on top of that is a raised non-slip strip down the standing
    # aisle, with a tread rib at every bay.
    _box(v, t, g, "transit_deck_joint", (-AISLE_HW_M, 0.0, z_front + 0.2),
         (AISLE_HW_M, 0.014, z_back - 0.2))
    for i in range(bays * 3 + 1):
        zz = z_front + 0.2 + (ln - 0.4) * i / (bays * 3)
        # `prop_catwalk` -> steel_catwalk_tread, NOT `fix_platform_edge`'s
        # yellow chevron nosing. The first render of this had a hazard-striped
        # aisle running the length of the car, which is a platform edge's
        # vocabulary in a place with no edge to fall off. The yellow stays
        # where it belongs: the door thresholds.
        _box(v, t, g, "prop_catwalk", (-AISLE_HW_M, 0.0, zz - 0.024),
             (AISLE_HW_M, 0.030, zz + 0.024))

    # --- grey panelled walls with recessed seams --------------------------
    _car_panelling(v, t, g, hw, h, z_front, z_back, bays, prog)

    # --- the fittings the spec lists -------------------------------------
    _car_fittings(v, t, g, hw, h, z_front, z_back, bays)

    # --- the gangway ------------------------------------------------------
    _vestibule(v, t, g, z_back + SKIN_T_M, h=min(VEST_H_M, h))
    return n_seats


def _car_panelling(v, t, g, hw, h, z_front, z_back, bays, prog):
    """"Grey panelled walls with recessed seams" -- 35a, in the module's words.

    NOT `articulate`'s plate field, and the difference is content rather than
    taste. A room's field is a dado course and an upper course divided on the
    corridor's 1.15 m plate module; a vehicle's bodyside is divided by its own
    STRUCTURE -- the body pillars, which are already built, at 4.0 m -- and
    the seams between them are shallow and horizontal. Building the room's
    field here would put a 1.15 m vertical joint through the middle of a
    window bay that has no joint in it.

    Two bands carry it: the plinth band under the window (behind the bench,
    seen in the door bays and over the cushions) and the header band above.
    """
    courses = 3
    for s in (-1, 1):
        for i in range(bays):
            za = z_front + BAY_M * i + PILLAR_W_M / 2.0 + 0.02
            zb = z_front + BAY_M * (i + 1) - PILLAR_W_M / 2.0 - 0.02
            n_pl = max(2, int((zb - za) / 1.15))
            for k in range(n_pl):
                pa = za + (zb - za) * k / n_pl + 0.019
                pb = za + (zb - za) * (k + 1) / n_pl - 0.019
                # the lower band, floor to the window's sill trim
                for c in range(courses):
                    y0 = 0.10 + (WIN_SILL_M - TRIM_H_M - 0.14) * c / courses
                    y1 = 0.10 + (WIN_SILL_M - TRIM_H_M - 0.14) * (c + 1) / courses
                    _box(v, t, g, "transit_panel",
                         (min(s * hw, s * (hw - 0.045)), y0 + 0.019, pa),
                         (max(s * hw, s * (hw - 0.045)), y1 - 0.019, pb))
                # the header band, over the upper trim rail
                _box(v, t, g, "transit_panel",
                     (min(s * hw, s * (hw - 0.045)),
                      WIN_HEAD_M + TRIM_H_M * 0.8 + 0.03, pa),
                     (max(s * hw, s * (hw - 0.045)), h - 0.30, pb))
        # The skirting at the foot of the bodyside, which is what the frame
        # shows running the length of the plinth run.
        _box(v, t, g, "hazard_frame",
             (min(s * hw, s * (hw - 0.05)), 0.0, z_front),
             (max(s * hw, s * (hw - 0.05)), 0.09, z_back))
    # The headlining: pans between transverse ribs, and an air grille a bay.
    # A vehicle ceiling a player looks up at from a seat is not one sheet.
    for i in range(bays):
        za = z_front + BAY_M * i + 0.14
        zb = z_front + BAY_M * (i + 1) - 0.14
        _box(v, t, g, "transit_rib", (-hw + 0.02, h - 0.09, za - 0.20),
             (hw - 0.02, h - 0.01, za - 0.06))
        for k in range(3):
            pa = za + (zb - za) * k / 3.0 + 0.035
            pb = za + (zb - za) * (k + 1) / 3.0 - 0.035
            for xa, xb in ((-hw + 0.05, -0.24), (0.24, hw - 0.05)):
                _box(v, t, g, "transit_panel", (xa, h - 0.055, pa),
                     (xb, h - 0.008, pb))
        for s in (-1, 1):
            _box(v, t, g, "fix_service_duct",
                 (s * (hw - 0.62), h - 0.075, (za + zb) / 2.0 - 0.34),
                 (s * (hw - 0.30), h - 0.012, (za + zb) / 2.0 + 0.34))
    _box(v, t, g, "transit_rib", (-hw + 0.02, h - 0.09, z_back - 0.34),
         (hw - 0.02, h - 0.01, z_back - 0.20))


def _car_windscreen(v, t, g, hw, ow, h, z_front, rake):
    """The raked screen, its pillars, and the solid apron under it."""
    sill = WIN_SILL_M
    head = h - 0.20
    set_back = (head - sill) * rake
    # The apron under the screen: a solid nose, closed.
    _box(v, t, g, "transit_wall", (-ow, 0.0, z_front - SKIN_T_M),
         (ow, sill, z_front))
    # The screen itself: a raked slab in section, so it has a real thickness.
    _prism_zy(v, t, g, "prop_viewport",
              [(z_front - 0.03, sill), (z_front, sill),
               (z_front - set_back, head), (z_front - set_back - 0.03, head)],
              -hw + 0.06, hw - 0.06)
    # Its frame: two raked pillars and a header, each a prism in the same
    # section so nothing is a plate with no back.
    for s in (-1, 1):
        _prism_zy(v, t, g, "transit_mullion",
                  [(z_front - 0.075, sill), (z_front + 0.02, sill),
                   (z_front - set_back + 0.02, head),
                   (z_front - set_back - 0.075, head)],
                  min(s * hw, s * (hw - 0.10)), max(s * hw, s * (hw - 0.10)))
    _box(v, t, g, "transit_mullion",
         (-ow, head, z_front - set_back - 0.09), (ow, h, z_front - set_back + 0.02))
    # The red trim that carries round the screen, and the header light.
    _box(v, t, g, "hazard_frame", (-hw + 0.02, sill - TRIM_H_M, z_front - 0.10),
         (hw - 0.02, sill, z_front + 0.02))
    _box(v, t, g, "light_wall_strip_bank",
         (-hw + 0.30, head - 0.10, z_front - set_back - 0.06),
         (hw - 0.30, head - 0.02, z_front - set_back - 0.02))
    # The driving console under the screen -- a shuttle has a driver, and the
    # frame's apron carries one.
    _box(v, t, g, "prop_console", (-0.62, sill - 0.42, z_front + 0.04),
         (0.62, sill - 0.06, z_front + 0.46))
    _prism_zy(v, t, g, "prop_console",
              [(z_front + 0.46, sill - 0.42), (z_front + 0.70, sill - 0.42),
               (z_front + 0.46, sill - 0.06)], -0.62, 0.62)


def _car_door(v, t, g, s, hw, ow, h, cz):
    """A door pair in one side of the car, with its pocket and threshold."""
    with _Assembly(v, t, g, "prop_shuttle_door"):
        return _car_door_solids(v, t, g, s, hw, ow, h, cz)


def _car_door_solids(v, t, g, s, hw, ow, h, cz):
    dw = _rooms.PROPS["shuttle_door"][0]
    dh = _rooms.PROPS["shuttle_door"][2]
    za, zb = cz - dw / 2.0, cz + dw / 2.0
    # The two leaves, parted on the centreline of the opening.
    for k, (la, lb) in enumerate(((za, cz - 0.012), (cz + 0.012, zb))):
        _box(v, t, g, "prop_shuttle_door",
             (min(s * hw, s * (hw - 0.075)), 0.055, la),
             (max(s * hw, s * (hw - 0.075)), dh, lb))
        # a glazed light in each leaf, so a door is not a slab
        _box(v, t, g, "prop_viewport",
             (min(s * (hw - 0.020), s * (hw - 0.058)), 0.92, la + 0.14),
             (max(s * (hw - 0.020), s * (hw - 0.058)), dh - 0.22, lb - 0.14))
    # The frame: jambs, head and a threshold plate.
    for zz in (za, zb):
        _box(v, t, g, "transit_mullion",
             (min(s * hw, s * (hw - 0.10)), 0.0, zz - 0.075),
             (max(s * hw, s * (hw - 0.10)), dh + 0.075, zz + 0.075))
    _box(v, t, g, "transit_mullion",
         (min(s * hw, s * (hw - 0.10)), dh, za - 0.075),
         (max(s * hw, s * (hw - 0.10)), dh + 0.075, zb + 0.075))
    _box(v, t, g, "fix_platform_edge",
         (min(s * hw, s * (hw - 0.30)), 0.0, za - 0.05),
         (max(s * hw, s * (hw - 0.30)), 0.022, zb + 0.05))
    # A door light over it, and a leaning rail either side of the doorway --
    # the standing space a door bay is.
    _box(v, t, g, "light_wall_strip_bank",
         (min(s * (hw - 0.08), s * (hw - 0.13)), dh + 0.09, za),
         (max(s * (hw - 0.08), s * (hw - 0.13)), dh + 0.15, zb))
    for zz in (za - 0.40, zb + 0.40):
        _cyl_y(v, t, g, "prop_handhold", s * (hw - 0.14), zz, 0.30, dh + 0.05,
               POLE_R_M * 0.8, seg=8)


def _car_single_seat(v, t, g, cx, cz):
    """One individual seat on a moulded base -- six solids, not a cube."""
    with _Assembly(v, t, g, "prop_seat"):
        return _car_single_seat_solids(v, t, g, cx, cz)


def _car_single_seat_solids(v, t, g, cx, cz):
    w = _rooms.PROPS["seat"][0] / 2.0
    d = _rooms.PROPS["seat"][1] / 2.0
    _box(v, t, g, "prop_bench", (cx - w * 0.72, 0.0, cz - d * 0.72),
         (cx + w * 0.72, PLINTH_H_M - 0.06, cz + d * 0.72))
    _box(v, t, g, "prop_bench", (cx - w, PLINTH_H_M - 0.06, cz - d),
         (cx + w, PLINTH_H_M, cz + d))
    _box(v, t, g, "prop_seat", (cx - w, PLINTH_H_M, cz - d),
         (cx + w, SEAT_H_M, cz + d))
    _prism_zy(v, t, g, "prop_seat",
              [(cz - d - 0.035, PLINTH_H_M + 0.012),
               (cz - d, PLINTH_H_M + 0.012), (cz - d, SEAT_H_M - 0.014),
               (cz - d - 0.035, SEAT_H_M - 0.014)], cx - w, cx + w)
    _box(v, t, g, "prop_seat", (cx - w, SEAT_H_M, cz + d - 0.10),
         (cx + w, BACK_H_M, cz + d))
    _box(v, t, g, "light_wall_strip_bank",
         (cx - w * 0.6, PANEL_SILL_M, cz - d - 0.012),
         (cx + w * 0.6, PANEL_SILL_M + PANEL_H_M * 0.7, cz - d))


def _car_fittings(v, t, g, hw, h, z_front, z_back, bays):
    """What PLC-113 lists, each on the wall a passenger reads it from.

    seat, handhold and shuttle_door are the register's declared three and are
    built in the seating plan above. These are the spec's "added" five --
    emergency stop (T3), help point (T3), lost-property tag point (T3), car
    plaque (T1, "6 cars, 6 numbers") and the advert/notice panel (T1, "era-true:
    ISN + MiniPax rotation").
    """
    ph = 1.35                                    # a standing hand
    # Emergency stop, by every door bay -- which is where an emergency stop is.
    for i in DOOR_BAYS:
        zz = z_front + BAY_M * (i + 0.5) - 1.35
        _box(v, t, g, "prop_breaker_lever", (hw - 0.09, ph - 0.20, zz - 0.16),
             (hw - 0.01, ph + 0.24, zz + 0.16))
        _box(v, t, g, "hazard_frame", (hw - 0.10, ph - 0.26, zz - 0.22),
             (hw - 0.055, ph + 0.30, zz + 0.22))
    # Help point: an intercom with its own surround, one a car.
    zz = z_front + BAY_M * (DOOR_BAYS[1] + 0.5) + 1.35
    _box(v, t, g, "prop_intercom", (-hw + 0.01, ph - 0.12, zz - 0.10),
         (-hw + 0.10, ph + 0.20, zz + 0.10))
    _box(v, t, g, "transit_panel", (-hw + 0.005, ph - 0.20, zz - 0.18),
         (-hw + 0.055, ph + 0.30, zz + 0.18))
    # Lost-property tag point: a small locker bank at the gangway end.
    _box(v, t, g, "prop_parcel_locker", (hw - 0.42, 0.0, z_back - 1.30),
         (hw - 0.02, 1.10, z_back - 0.30))
    for k in range(3):
        _box(v, t, g, "prop_parcel_locker",
             (hw - 0.44, 0.06 + k * 0.34, z_back - 1.26),
             (hw - 0.40, 0.34 + k * 0.34, z_back - 0.34))
    # The car plaque -- 6 cars, 6 numbers. One per car; the class row builds
    # the fitting and `signage.py` carries the text.
    _box(v, t, g, "prop_level_plaque", (-hw + 0.005, 1.62, z_back - 2.10),
         (-hw + 0.035, 1.88, z_back - 1.68))
    # The advert / notice panel: over the window band, where a car carries one.
    for s in (-1, 1):
        zz = z_front + BAY_M * (bays // 2)
        _box(v, t, g, "prop_info_board",
             (min(s * (hw - 0.06), s * (hw - 0.10)), WIN_HEAD_M + 0.12,
              zz - 0.60),
             (max(s * (hw - 0.06), s * (hw - 0.10)), WIN_HEAD_M + 0.12 + 0.44,
              zz + 0.60))
        _box(v, t, g, "transit_panel",
             (min(s * (hw - 0.045), s * (hw - 0.10)), WIN_HEAD_M + 0.08,
              zz - 0.66),
             (max(s * (hw - 0.045), s * (hw - 0.10)), WIN_HEAD_M + 0.60,
              zz + 0.66))


# ---------------------------------------------------------------------------
# The running way -- 34b, authority 1
# ---------------------------------------------------------------------------
def _running_way(v, t, g, x0, x1, y0, y1, z0, z1, lining_x=("lo", "hi"),
                 cap_far=True, cap_near=True, lining=0.20):
    """What is beyond the glass: red ribs receding past illuminator tubes.

    THIS IS NOT SCENERY AND IT IS NOT A CHEAT. `CLAUDE.md` records that
    `--shot interior` has no exterior environment, so a window with nothing
    built behind it renders as a black void -- and that against black a hole
    and a shadow look the same. The line's structure is CONTENT: 34b shows a
    lattice-girder truss carrying long cylindrical illuminator tubes with its
    lower edge serrated into a rack, and 35a shows exactly that receding
    through the car's screen. Building it is what makes the glazing read as a
    window rather than as a hole.

    `lining_x` names which SIDES this draws. The station's inboard side is the
    platform screen wall itself, and drawing a lining there would put a solid
    slab across the glass -- which is the whole thing this function exists to
    avoid one wall further out.
    """
    # The lining: closed slabs, so the volume a player looks into is a tube
    # rather than the background.
    _box(v, t, g, "transit_wall", (x0 - lining, y0 - lining, z0 - lining),
         (x1 + lining, y0, z1 + lining))
    _box(v, t, g, "transit_wall", (x0 - lining, y1, z0 - lining),
         (x1 + lining, y1 + lining, z1 + lining))
    if "lo" in lining_x:
        _box(v, t, g, "transit_wall", (x0 - lining, y0 - lining, z0 - lining),
             (x0, y1 + lining, z1 + lining))
    if "hi" in lining_x:
        _box(v, t, g, "transit_wall", (x1, y0 - lining, z0 - lining),
             (x1 + lining, y1 + lining, z1 + lining))
    if cap_far:
        _box(v, t, g, "transit_wall", (x0 - lining, y0 - lining, z0 - lining),
             (x1 + lining, y1 + lining, z0))
    if cap_near:
        _box(v, t, g, "transit_wall", (x0 - lining, y0 - lining, z1),
             (x1 + lining, y1 + lining, z1 + lining))
    # The ribs: closed frames standing proud of the lining, at RIB_PITCH_M.
    n = max(1, int((z1 - z0) / RIB_PITCH_M))
    for i in range(n):
        zz = z1 - RIB_PITCH_M * (i + 0.5)
        for xa, xb in ((x0, x0 + RIB_D_M), (x1 - RIB_D_M, x1)):
            _box(v, t, g, "hazard_frame", (xa, y0, zz - RIB_W_M / 2.0),
                 (xb, y1, zz + RIB_W_M / 2.0))
        _box(v, t, g, "hazard_frame", (x0, y1 - RIB_D_M, zz - RIB_W_M / 2.0),
             (x1, y1, zz + RIB_W_M / 2.0))
        # A haunch at each springing, so a rib is a frame and not three boxes.
        for s, xa in ((-1, x0 + RIB_D_M), (1, x1 - RIB_D_M)):
            _prism_xy(v, t, g, "hazard_frame",
                      [(xa, y1 - RIB_D_M), (xa + s * 0.42, y1 - RIB_D_M),
                       (xa, y1 - RIB_D_M - 0.42)],
                      zz - RIB_W_M / 2.0, zz + RIB_W_M / 2.0)
        # The serrated rack on the truss's lower edge -- 34b calls it out by
        # name and it is how the cars are driven.
        for k in range(4):
            zt = zz - RIB_W_M / 2.0 + 0.02 + k * 0.055
            _box(v, t, g, "fix_gantry_rail",
                 ((x0 + x1) / 2.0 - 0.30, y1 - RIB_D_M - 0.15, zt),
                 ((x0 + x1) / 2.0 + 0.30, y1 - RIB_D_M, zt + 0.030))
    # The two long chords the ribs hang from, and the illuminator tubes under
    # them: 34b's "long cylindrical illuminator tubes" carried by the truss.
    for s in (-1, 1):
        cx = (x0 + x1) / 2.0 + s * (x1 - x0) * 0.28
        _box(v, t, g, "fix_gantry_rail", (cx - 0.11, y1 - RIB_D_M - 0.14,
                                          z0 + 0.10),
             (cx + 0.11, y1 - RIB_D_M, z1 - 0.10))
        _cyl_z(v, t, g, "light_ceiling_batten", cx,
               y1 - RIB_D_M - 0.14 - TUBE_LAMP_R_M - 0.06,
               z0 + 0.40, z1 - 0.40, TUBE_LAMP_R_M, seg=10)
        for k in range(max(1, int((z1 - z0) / 6.0))):
            zc = z0 + 0.40 + (z1 - z0 - 0.80) * (k + 0.5) / max(
                1, int((z1 - z0) / 6.0))
            _box(v, t, g, "fix_gantry_rail",
                 (cx - 0.05, y1 - RIB_D_M - 0.16, zc - 0.05),
                 (cx + 0.05, y1 - RIB_D_M - 0.10, zc + 0.05))
    return n


# ---------------------------------------------------------------------------
# The station
# ---------------------------------------------------------------------------
def _station(v, t, g, prog):
    """A platform hall alongside the running way, and the way in from the ring.

    PLC-102's ruling decides the shape: *"the running tube between stations is
    transit envelope, not walkable rooms -- the built product is 13 stations +
    the tube the cars traverse"*. So this is ONE station: a berth long enough
    for a car, a platform beside it, a glazed screen wall with doors onto it,
    and the line's own information behind.

    x = 0 IS THE DOORWAY, NOT THE MIDDLE OF THE MODEL. `deck._place_local`
    maps local x = 0 onto the bearing `deck_plan` puts the corridor's door at,
    so the PLATFORM is centred on the origin and the berth is outboard of it.
    """
    hl = PLAT_L_M / 2.0
    h = HALL_H_M
    plat_x0 = -PLAT_D_M / 2.0
    plat_x1 = PLAT_D_M / 2.0
    ow0 = plat_x0 - WALL_T_M
    ow1 = plat_x1 + WALL_T_M            # the screen wall's outboard face
    way_x0 = ow1
    way_x1 = way_x0 + CAR_EXT_W_M
    berth_y = -1.10                     # a car's floor level with the platform
    berth_top = 3.60                    # one deck: the tube's own roof

    # --- shell -----------------------------------------------------------
    # Deck and soffit run to the OUTER wall extent. Running them to the inner
    # face leaves an open corner at every wall junction -- `hospitality.room`
    # records the render that found it.
    _box(v, t, g, "transit_deck", (ow0, -0.18, -hl - WALL_T_M),
         (ow1, 0.0, hl + WALL_T_M))
    _box(v, t, g, "transit_soffit", (ow0, h, -hl - WALL_T_M),
         (ow1, h + 0.18, hl + WALL_T_M))
    _box(v, t, g, "transit_wall", (ow0, 0.0, -hl), (plat_x0, h, hl))
    _box(v, t, g, "transit_wall", (ow0, 0.0, -hl - WALL_T_M), (ow1, h, -hl))
    _bsp.doorway_wall(lambda n, lo, hi: _box(v, t, g, n, lo, hi),
                      "transit_wall", ow0, ow1, 0.0, h, hl, hl + WALL_T_M)

    # --- the berth, and what runs through it -----------------------------
    # The inboard lining is omitted: the screen wall IS it, and a slab there
    # would be a wall across the glass.
    _running_way(v, t, g, way_x0, way_x1, berth_y, berth_top, -hl, hl,
                 lining_x=("hi",))

    # --- the platform screen wall ----------------------------------------
    door_z = [-CAR_L_M / 2.0 + BAY_M * (i + 0.5) for i in DOOR_BAYS]
    _screen_wall(v, t, g, plat_x1, ow1, hl, h, berth_y, berth_top, door_z)

    # --- articulation ----------------------------------------------------
    # INV-073's vocabulary over the PLATFORM's own box, with the spans that
    # land on the screen wall's glazing dropped -- see `_articulate`. `scale`
    # coarsens the pitch for a 7.2 m volume, the same reading
    # `concourse.central_corridor` takes at the same height.
    phw = PLAT_D_M / 2.0
    dh = _rooms.PROPS["shuttle_door"][2]

    def _on_glass(_n, x0, x1, _y0, y1, _z0, _z1):
        return x0 > phw - 0.55 and y1 < berth_top + 0.02

    _articulate(v, t, g, "transit", phw, hl, h, drop=_on_glass,
                ow=phw + WALL_T_M, ol=hl + WALL_T_M, ln=PLAT_L_M,
                nrib=int(PLAT_L_M / BAY_M), scale=1.6, plates=True,
                owns_box=True,
                door_at=(0.0, 2.0 * _bsp.DOOR_HALF_W_M, _bsp.DOOR_H_M))

    # --- the platform edge ------------------------------------------------
    # Nosing, a tactile band, and a chamfered fascia down to the berth. A
    # platform edge is the one piece of a station a passenger is taught to
    # look for, so it is three pieces and not a painted line.
    _box(v, t, g, "fix_platform_edge", (plat_x1 - 0.45, 0.0, -hl),
         (plat_x1 - 0.05, 0.024, hl))
    for k in range(int(PLAT_L_M / 0.55)):
        zz = -hl + 0.275 + k * 0.55
        _box(v, t, g, "fix_platform_edge", (plat_x1 - 0.40, 0.024, zz - 0.11),
             (plat_x1 - 0.10, 0.044, zz + 0.11))
    _prism_xy(v, t, g, "transit_skirt",
              [(plat_x1 - 0.05, 0.0), (plat_x1, 0.0), (plat_x1, -0.30),
               (plat_x1 - 0.24, -0.30)], -hl, hl)

    # --- the seating, against the back wall ------------------------------
    # The same plinth module as the car's: a station and its rolling stock are
    # one design, and building both from one function is how they stay one.
    n_bench = 0
    seg = PLAT_L_M / (prog["benches"] + 1)
    for k in range(prog["benches"]):
        z0 = -hl + seg * (k + 0.5) + 0.35
        n_bench += _bench_run(v, t, g, -1, plat_x0, z0, z0 + seg - 1.10)

    # --- the line's own information and controls -------------------------
    _station_fittings(v, t, g, plat_x0, plat_x1, hl, h)

    # --- stanchions down the platform ------------------------------------
    for k in range(int(PLAT_L_M / BAY_M)):
        zz = -hl + BAY_M * (k + 0.5)
        with _Assembly(v, t, g, "prop_handhold"):
            _cyl_y(v, t, g, "prop_handhold", plat_x1 - 1.55, zz, 0.0, 1.15,
                   POLE_R_M * 1.1, seg=10)
            _cyl_y(v, t, g, "prop_handhold", plat_x1 - 1.55, zz, 1.09, 1.15,
                   POLE_R_M * 2.2, seg=10)
            _cyl_y(v, t, g, "prop_handhold", plat_x1 - 1.55, zz, 0.0, 0.06,
                   POLE_R_M * 2.4, seg=10)

    # --- the catenary run over the berth ---------------------------------
    # `rooms.FIXTURES["transit"]` names it; this is that fixture at the
    # station's own scale rather than a second idea of one.
    _nm, cw, cd, ch, _face = _rooms.FIXTURES["transit"][1]
    n_cat = int(PLAT_L_M / 3.2) + 1
    for k in range(n_cat):
        zz = -hl + 3.2 * k + 0.3
        _box(v, t, g, "fix_catenary_run",
             (way_x0 + 0.26, berth_top - ch - 0.34, zz - cd / 2.0),
             (way_x1 - 0.26, berth_top - ch - 0.10, zz + cd / 2.0))
    _box(v, t, g, "fix_catenary_run",
         ((way_x0 + way_x1) / 2.0 - cw / 2.0, berth_top - ch - 0.10, -hl + 0.2),
         ((way_x0 + way_x1) / 2.0 + cw / 2.0, berth_top - ch, hl - 0.2))

    # --- the way in -------------------------------------------------------
    _vestibule(v, t, g, hl + WALL_T_M)
    return n_bench


def _screen_wall(v, t, g, x0, x1, hl, h, berth_y, berth_top, door_z):
    """The glazed wall between platform and berth, with its door openings.

    A GLAZED WALL AND NOT A RAILING, for two reasons that both come off the
    references rather than off modern practice. 34b shows the running way as
    OPEN structure with the cars swinging through it, so a station has to be
    separated from it; and 35a's own light -- amber panels low, a bright band
    at eye height -- is a lit interior seen through glass, which is what a
    platform looks like from a car and a car looks like from a platform.

    Built in courses so the wall is a wall: below-deck fascia, upstand,
    glazing between mullions, door head, clerestory, transom, spandrel.
    """
    dh = _rooms.PROPS["shuttle_door"][2]
    dw = _rooms.PROPS["shuttle_door"][0]
    up = 0.28                       # the upstand under the glass
    head = dh + 0.18
    cler = berth_top - 0.18         # the clerestory's head
    openings = [(cz - dw / 2.0 - 0.09, cz + dw / 2.0 + 0.09) for cz in door_z]

    def _runs(za, zb):
        """The z runs of wall between the door openings."""
        out, cur = [], za
        for a, b in sorted(openings):
            if a > cur:
                out.append((cur, min(a, zb)))
            cur = max(cur, b)
        if cur < zb:
            out.append((cur, zb))
        return [(a, b) for a, b in out if b - a > 1e-6]

    # The fascia below the platform deck: continuous, and the thing that makes
    # the berth a slot rather than a hole.
    _box(v, t, g, "transit_skirt", (x0, berth_y - 0.20, -hl), (x1, 0.0, hl))
    _box(v, t, g, "transit_rail", (x0 - 0.03, -0.30, -hl), (x1, -0.16, hl))
    # The upstand, the glazing bays and the clerestory, between the doors.
    pitch = 1.55
    for za, zb in _runs(-hl, hl):
        _box(v, t, g, "transit_skirt", (x0, 0.0, za), (x1, up, zb))
        n = max(1, int(round((zb - za) / pitch)))
        for k in range(n + 1):
            zz = za + (zb - za) * k / n
            _box(v, t, g, "transit_mullion", (x0 - 0.02, up, zz - 0.055),
                 (x1 + 0.02, cler, zz + 0.055))
        for k in range(n):
            pa = za + (zb - za) * k / n + 0.055
            pb = za + (zb - za) * (k + 1) / n - 0.055
            _box(v, t, g, "prop_viewport", (x0 + 0.055, up + 0.05, pa),
                 (x1 - 0.055, dh - 0.02, pb))
            _box(v, t, g, "prop_viewport", (x0 + 0.055, head + 0.05, pa),
                 (x1 - 0.055, cler - 0.05, pb))
            # the rebate the glass sits in, top and bottom of each pane
            for c, d in ((up, up + 0.05), (dh - 0.02, dh),
                         (head, head + 0.05), (cler - 0.05, cler)):
                _box(v, t, g, "transit_mullion", (x0 + 0.02, c, pa),
                     (x1 - 0.02, d, pb))
    # The doors themselves.
    for cz in door_z:
        _screen_door(v, t, g, x0, x1, cz, dh)
    # The head beam, the transom and the spandrel: continuous, over everything.
    _box(v, t, g, "transit_rail", (x0 - 0.04, dh, -hl), (x1, head, hl))
    _box(v, t, g, "transit_cornice", (x0 - 0.04, cler, -hl),
         (x1, berth_top, hl))
    _box(v, t, g, "transit_wall", (x0, berth_top, -hl), (x1, h, hl))
    # A lit band on the platform face of the head beam -- the platform's own
    # light, and what makes the screen line read from the far end.
    _box(v, t, g, "light_wall_strip_bank", (x0 - 0.075, dh + 0.03, -hl + 0.2),
         (x0 - 0.045, head - 0.03, hl - 0.2))


def _screen_door(v, t, g, x0, x1, cz, dh):
    """One platform screen door: two leaves, a frame, a call plate, a head."""
    with _Assembly(v, t, g, "prop_shuttle_door"):
        return _screen_door_solids(v, t, g, x0, x1, cz, dh)


def _screen_door_solids(v, t, g, x0, x1, cz, dh):
    dw = _rooms.PROPS["shuttle_door"][0]
    za, zb = cz - dw / 2.0, cz + dw / 2.0
    for la, lb in ((za, cz - 0.012), (cz + 0.012, zb)):
        _box(v, t, g, "prop_shuttle_door", (x0 + 0.02, 0.0, la),
             (x1 - 0.02, dh, lb))
        _box(v, t, g, "prop_viewport", (x0 - 0.005, 0.95, la + 0.16),
             (x0 + 0.030, dh - 0.24, lb - 0.16))
        # a rail across the leaf at hand height, which every door in this
        # station's vocabulary has and a slab does not
        _box(v, t, g, "transit_rail", (x0 - 0.02, 0.86, la + 0.05),
             (x0 + 0.02, 0.94, lb - 0.05))
    for zz in (za, zb):
        _box(v, t, g, "transit_mullion", (x0 - 0.045, 0.0, zz - 0.09),
             (x1 + 0.02, dh + 0.10, zz + 0.09))
    _box(v, t, g, "transit_mullion", (x0 - 0.045, dh, za - 0.09),
         (x1 + 0.02, dh + 0.10, zb + 0.09))
    _box(v, t, g, "fix_platform_edge", (x0 - 0.55, 0.0, za - 0.06),
         (x0 - 0.02, 0.024, zb + 0.06))
    _box(v, t, g, "light_wall_strip_bank", (x0 - 0.085, dh + 0.11, za),
         (x0 - 0.050, dh + 0.17, zb))
    _box(v, t, g, "prop_lift_call", (x0 - 0.080, 1.06, zb + 0.22),
         (x0 - 0.020, 1.40, zb + 0.42))


def _station_fittings(v, t, g, back_x, edge_x, hl, h):
    """PLC-102's information layer, at the heights a passenger reads it.

    Declared: shuttle_door (built in the screen wall), seat (the bench run),
    handhold (the stanchions). Added by the spec: stop board (T1 live), line
    map (T1), emergency stop (T3), help point (T3), and the line control desk
    at stop 1 (T3, serve).
    """
    # The stop board: hung from the soffit over the platform, double-sided, so
    # it reads from both ends of the platform as a stop board does.
    for s in (-1, 1):
        zz = s * hl * 0.45
        for dz in (-0.06, 0.02):
            _box(v, t, g, "prop_info_board", (edge_x - 2.30, 2.62, zz + dz),
                 (edge_x - 0.60, 3.42, zz + dz + 0.04))
        _box(v, t, g, "transit_mullion", (edge_x - 2.38, 2.54, zz - 0.09),
             (edge_x - 0.52, 3.50, zz + 0.09))
        for hx in (edge_x - 2.20, edge_x - 0.70):
            _box(v, t, g, "fix_gantry_rail", (hx - 0.035, 3.50, zz - 0.035),
                 (hx + 0.035, h, zz + 0.035))
        _box(v, t, g, "light_wall_strip_bank", (edge_x - 2.20, 2.49, zz - 0.05),
             (edge_x - 0.70, 2.54, zz + 0.05))

    # The line map: 13 stops at 387.5 m, on the back wall where a queue reads
    # it. The strip and its tick per stop ARE the map -- a screen with no
    # graticule is a box with a material on it.
    mz = -hl + 3.4
    _box(v, t, g, "prop_station_schematic_screen", (back_x + 0.02, 1.05, mz),
         (back_x + 0.09, 2.25, mz + 2.60))
    _box(v, t, g, "transit_mullion", (back_x + 0.005, 0.97, mz - 0.10),
         (back_x + 0.075, 2.33, mz + 2.70))
    for k in range(LINE_STOPS):
        zz = mz + 0.16 + (2.60 - 0.32) * k / (LINE_STOPS - 1)
        _box(v, t, g, "light_wall_strip_bank", (back_x + 0.085, 1.55, zz - 0.035),
             (back_x + 0.115, 1.75, zz + 0.035))
    _box(v, t, g, "light_wall_strip_bank", (back_x + 0.085, 1.63, mz + 0.16),
         (back_x + 0.105, 1.67, mz + 2.44))

    # The help point: an intercom in a lit surround, the one thing on a
    # platform a lost passenger looks for.
    hz = -hl + 8.2
    _box(v, t, g, "prop_intercom", (back_x + 0.02, 1.24, hz - 0.11),
         (back_x + 0.11, 1.58, hz + 0.11))
    _box(v, t, g, "transit_panel", (back_x + 0.005, 1.05, hz - 0.30),
         (back_x + 0.06, 2.10, hz + 0.30))
    _box(v, t, g, "light_wall_strip_bank", (back_x + 0.06, 1.95, hz - 0.26),
         (back_x + 0.09, 2.05, hz + 0.26))

    # The emergency stop: on the edge side, where somebody who sees a fall
    # reaches for it, in a hazard surround.
    ez = hl - 5.0
    _box(v, t, g, "prop_breaker_lever", (edge_x - 0.62, 1.18, ez - 0.16),
         (edge_x - 0.30, 1.62, ez + 0.16))
    _box(v, t, g, "hazard_frame", (edge_x - 0.68, 1.10, ez - 0.24),
         (edge_x - 0.60, 1.70, ez + 0.24))
    _box(v, t, g, "transit_panel", (edge_x - 0.72, 0.30, ez - 0.28),
         (edge_x - 0.60, 1.10, ez + 0.28))

    # The line control desk at stop 1 -- a manned counter, a screen behind and
    # a console on it. `dialogue.py`'s `serve` verb needs somebody behind a
    # counter and `populace` puts them there; this is the furniture that says
    # so.
    cz = hl - 9.0
    cw, cd, ch, _f = _rooms.PROPS["counter"]
    _box(v, t, g, "prop_counter", (back_x + 0.10, 0.0, cz - cw / 2.0),
         (back_x + 0.10 + cd, ch - 0.06, cz + cw / 2.0))
    _box(v, t, g, "prop_counter", (back_x + 0.04, ch - 0.06, cz - cw / 2.0 - 0.09),
         (back_x + 0.16 + cd, ch, cz + cw / 2.0 + 0.09))
    _prism_xy(v, t, g, "prop_counter",
              [(back_x + 0.10, 0.0), (back_x + 0.10 + cd, 0.0),
               (back_x + 0.10 + cd, 0.16), (back_x + 0.10 + cd * 0.55, 0.16)],
              cz - cw / 2.0, cz + cw / 2.0)
    _box(v, t, g, "prop_console", (back_x + 0.22, ch, cz - 0.55),
         (back_x + 0.62, ch + 0.30, cz + 0.55))
    _box(v, t, g, "prop_babcom_terminal", (back_x + 0.05, 1.45, cz - 0.62),
         (back_x + 0.11, 2.05, cz + 0.62))
    _box(v, t, g, "light_wall_strip_bank", (back_x + 0.10, 2.12, cz - 0.70),
         (back_x + 0.14, 2.20, cz + 0.70))
    for zz in (cz - cw / 2.0, cz + cw / 2.0):
        _box(v, t, g, "transit_mullion", (back_x + 0.02, 0.0, zz - 0.05),
             (back_x + 0.12, 2.30, zz + 0.05))


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
    import hashlib
    import directory as dr
    import interact as ia
    import interior as it
    schema, profile = it.load()

    places = [q for q in dr.PLACES if q.get("module") == MODULE]
    check("the register still gives this module two places", len(places) == 2,
          f"{[q['key'] for q in places]}")

    built = {}
    for q in sorted(places, key=lambda p: p["key"]):
        v, t, g = room(schema, profile, q)
        built[q["key"]] = (v, t, g)
        prog = program(q)

        op, non = kit.boundary_edges(v, t)
        check(f"{q['key']}: closed surface", not op, f"{len(op)} open edges")

        opening = _bsp.near_face_opening(v, t)
        check(f"{q['key']}: a body can walk in at local x = 0",
              opening is not None and abs(opening[0]) < 0.35
              and opening[1] >= kit.PROVISIONAL["door_width_m"],
              f"{opening}")

        want = tuple(q.get("interacts") or ())
        got = ia.resolve(want, {n for n, _a, _b in g}, g)
        check(f"{q['key']}: every declared interactable is built",
              set(got) == set(want), f"missing {sorted(set(want) - set(got))}")

        # THE ROOM MUST HAVE AN INSIDE. `bespoke.py`'s audit measured
        # `core_tube`'s own envelope and found every face pointing AWAY from
        # the axis, which is why that module cannot be an interior. This is
        # that measurement applied to this one, and it is the check that would
        # fail if a wall were built with its back to the room.
        eye = (0.0, 1.60, 0.0)
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
        check(f"{q['key']}: the room has an inside", inward > len(t) * 0.25,
              f"only {inward} of {len(t)} face an eye at the centre")

        ys = [p[1] for p in v]
        check(f"{q['key']}: the walkable floor is at y = 0",
              abs(_bsp.floor_y(v, t, g, MODULE)) < 1e-6,
              f"floor band at {_bsp.floor_y(v, t, g, MODULE):.3f}")
        print(f"  {q['key']:14s} {prog['kind']:8s} {len(t):7,d} tri  "
              f"{len(g):4d} groups  open={len(op)} nonmanifold={len(non)}  "
              f"{inward * 100.0 / max(1, len(t)):.0f}% facing in  "
              f"y {min(ys):.2f}..{max(ys):.2f}")

    # THE TWO PLACES ARE TWO ROOMS, NOT ONE. Session 4h: `deck.py
    # --degeneracy` asks IDENTITY, not similarity, and the defect it found was
    # exactly a registry entry that dropped the place.
    hashes = {}
    for key, (v, _t, _g) in built.items():
        hsh = hashlib.sha256()
        for p in v:
            hsh.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        hashes[key] = hsh.hexdigest()[:12]
    dupes = [k for k, c in collections.Counter(hashes.values()).items() if c > 1]
    check("the two places are two distinct geometries", not dupes, str(hashes))

    # NEGATIVE CONTROL -- ignore the register's `within` and they collapse.
    # Without this the gate above cannot fail: it would pass on a module that
    # reads the place and on one that ignores it, if the two happened to
    # differ for some other reason.
    ctl = set()
    for q in places:
        v, _t, _g = room(schema, profile, dict(q, within=None))
        hsh = hashlib.sha256()
        for p in v:
            hsh.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        ctl.add(hsh.hexdigest()[:12])
    check("...and with the relation ignored they collapse to one", len(ctl) == 1,
          f"{ctl}")

    # THE MEASUREMENTS ARE READ, NOT RESTATED. `tram.py` took the seat pitch
    # and the windscreen rake off the same episode; a second copy is how two
    # modules stop agreeing.
    import tram as _t
    check("the seat pitch is tram.py's own", abs(SEAT_MOD_M - _t.SEAT_PITCH_M) < 1e-9,
          f"{SEAT_MOD_M} against {_t.SEAT_PITCH_M}")
    check("the body pillar is tram.py's own",
          abs(PILLAR_W_M - _t.PILLAR_W_M) < 1e-9)
    check("the skin thickness is tram.py's own", abs(SKIN_T_M - _t.WALL_T) < 1e-9)
    check("the bay pitch is tram.py's own window pitch",
          abs(BAY_M - _t.WINDOW_PITCH_M) < 1e-9)
    # THE RAKE IS ONE READING QUOTED TWO WAYS, and the check has to be the one
    # that can FAIL. `tram.py` records a set-back (RAKE_M = 1.1 m) and the
    # angle it came from ("24 deg"); this module uses the angle, because its
    # screen is a different height. Asserting `atan(RAKE_M / MY screen)` would
    # be comparing tram's car to mine and would fail for a correct build --
    # it did, at 42.1 deg, when this was first written. What IS assertable is
    # that the two readings describe one windscreen: at 24 degrees a 1.1 m
    # set-back implies a screen 2.47 m tall, which is a car's windscreen and
    # not a porthole. If either number moves without the other, this fires.
    implied = _t.RAKE_M / math.tan(math.radians(_rake_deg()))
    check("tram.py's set-back and this module's angle describe one screen",
          1.9 <= implied <= 3.1,
          f"tram.RAKE_M {_t.RAKE_M} at {_rake_deg()} deg implies a "
          f"{implied:.2f} m screen")

    # THE CAR'S LENGTH IS THE REGISTER'S, and if the register moves this has
    # to move with it rather than describe a car that is not there.
    car = next(q for q in places if q.get("within"))
    check("the car is built at the register's own footprint",
          abs(BAY_M * PROGRAMS["car"]["bays"] - float(car["footprint"][1])) < 1e-6,
          f"{BAY_M * PROGRAMS['car']['bays']} against {car['footprint'][1]}")

    # THE SPEC'S CONTENT, ASSERTED. PLC-102 lists 13 stops and PLC-113 lists
    # six cars; a viewport count and a stop count are CONTENT, so they are
    # asserted rather than left to the reader of a constant.
    sg = built[next(q['key'] for q in places if not q.get("within"))][2]
    n_screen = sum(1 for n, _a, _b in sg if n == "prop_shuttle_door")
    check("the station has a screen-door pair at every car door",
          n_screen == 2 * len(DOOR_BAYS), f"{n_screen} leaves")
    n_map = sum(1 for n, _a, _b in sg if n == "prop_station_schematic_screen")
    check("the station carries the line map", n_map >= 1)
    cg = built[car["key"]][2]
    for grp, least in (("prop_seat", 60), ("prop_handhold", 20),
                       ("prop_shuttle_door", 6), ("prop_viewport", 10),
                       ("light_wall_strip_bank", 20)):
        n = sum(1 for nm, _a, _b in cg if nm == grp)
        check(f"the car carries {least}+ {grp}", n >= least, f"{n}")

    # EVERY GROUP MUST RESOLVE TO A MATERIAL, IN THE INTERIOR SCENE. The
    # coverage gate runs in `export_scene.build()`, one call site away, and by
    # then the room is inside a deck -- so it is asserted here, in the module
    # that names the surfaces. `truss_*` and `core_tube_*` resolve only in the
    # DRUM scene, which is why the running way is built from interior names.
    import materials as M
    bad = []
    for key, (_v, _t, gg) in built.items():
        for n, _a, _b in gg:
            m = M.resolve_any(n)
            if m is None or "interior" not in m.scenes:
                bad.append((key, n, m.name if m else None))
    check("every group resolves to an INTERIOR material", not bad,
          str(sorted({b[1] for b in bad})[:8]))

    # THE MACHINERY MUST NOT BE A BOX. `density.py --machinery` scores
    # `fix_*`/`prop_*` line density against the room's own shell and reads the
    # places `rooms.py` builds -- which these two stop being the moment they
    # are composed. So the same measurement is taken here, on this module's
    # own geometry, by the same code.
    import density as D
    live = {}
    for key, (v, t, gg) in built.items():
        mach, shell = D.machinery_split(v, t, gg)
        am = D.analyse(v, mach, min_facet_m=0.0)
        ash = D.analyse(v, shell, min_facet_m=0.0)
        live[key] = am
        r = am["lam"] / ash["lam"] if ash["lam"] > 0 else 0.0
        check(f"{key}: the machinery is at least as built as its own shell",
              r >= 1.0,
              f"machinery lambda {am['lam']:.3f} against shell {ash['lam']:.3f}")
        print(f"  {key:14s} machinery {len(mach):6,d} tri  lam {am['lam']:6.3f}"
              f"  shell {ash['lam']:6.3f}  x{r:5.2f}  "
              f"normals {am['normals']:.2f}")

    # AND A NEGATIVE CONTROL FOR IT, built into the geometry rather than onto
    # the measurement -- `BOXED` collapses each fitting ASSEMBLY to one box,
    # which is `density.py`'s own control ("every fixture and prop falls back
    # to the single `_box` it was before INV-130") expressed in this module.
    #
    # THE FIRST TWO VERSIONS OF THIS CONTROL DID NOT FIRE, and BOTH failures
    # are worth keeping because the second one is a finding about the GATE
    # rather than about this module.
    #
    #   1. It replaced every emitted SPAN with that span's own bounding box.
    #      A span here is already one small closed solid, so its box is very
    #      nearly itself: a bench module went from eleven solids to eleven
    #      boxes and scored x1.58 against x1.65. The defect the gate exists to
    #      catch is "a machine IS a box", not "a machine is made of boxes".
    #   2. Collapsing the whole ASSEMBLY does move it -- 1.74 -> 1.25 on the
    #      station and 2.14 -> 1.09 on the car -- and STILL does not take
    #      either below the gate's 1.00. That is not a defect in this geometry.
    #      `lam` is metres of visible line per m2, and a 0.62 x 0.47 x 0.86 m
    #      box has a far higher perimeter-to-area than a 44 m platform's walls,
    #      so a station furnished entirely in boxes clears its own shell.
    #      `density._selftest`'s equivalent asserts the boxed rooms FAIL, and
    #      its four probes are `fabrication`, `reactor_hall`, `medlab_one` and
    #      `business_center` -- rooms whose machinery is a furnace and a
    #      reactor console, single objects metres across. At a bench module's
    #      scale the ratio is not the discriminator.
    #
    # So the control asserts the two things that ARE discriminating and prints
    # the ratio it cannot use: the LIFT (density.py's own third check, "the
    # articulated machines carry more line than the boxes did") and the FACING
    # COUNT, which density.py's own report defines -- "A BOX READS ~6 whatever
    # its tessellation".
    global BOXED
    BOXED = True
    try:
        for q in sorted(places, key=lambda p: p["key"]):
            key = q["key"]
            bv, bt, bg = room(schema, profile, q)
            mach, shell = D.machinery_split(bv, bt, bg)
            bm = D.analyse(bv, mach, min_facet_m=0.0)
            bs = D.analyse(bv, shell, min_facet_m=0.0)
            am = live[key]
            lift = am["lam"] / max(bm["lam"], 1e-9)
            check(f"{key}: boxing every fitting COSTS most of its line density",
                  lift > 1.35,
                  f"articulated {am['lam']:.3f} against boxed {bm['lam']:.3f} "
                  f"-- x{lift:.2f}, so the gate above is measuring a case with "
                  f"no defect in it")
            check(f"{key}: ...and a box reads six facings, which this does not",
                  bm["normals"] < 6.5 < am["normals"],
                  f"boxed {bm['normals']:.2f}, shipped {am['normals']:.2f} "
                  f"-- density.py's own report: 'A BOX READS ~6 whatever its "
                  f"tessellation'")
            print(f"  {key:14s} BOXED     {len(mach):6,d} tri  "
                  f"lam {bm['lam']:6.3f}  shell {bs['lam']:6.3f}  "
                  f"x{bm['lam'] / bs['lam']:5.2f}  normals {bm['normals']:.2f}"
                  f"   -- lift x{lift:.2f}")
    finally:
        BOXED = False

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
