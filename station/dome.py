#!/usr/bin/env python3
"""The INSIDE of the glazed blisters -- observation domes and rotundas.

WHY THIS MODULE EXISTS, IN ONE MEASUREMENT
------------------------------------------
Standing at an `observation_dome`'s own base-plane centre, **0 of its 192
triangles face the viewer**. `components._selftest` asserts that number now;
before this module it was nobody's job to ask. Every surface points out,
because `components.dome_mesh` builds a blister ON a hull -- its own docstring
says "the base sits inside the hull and the hole faces away from every camera",
and its base disc is "wound the other way -- it faces into the hull".

So what `deck.py --sweep` reported as *"14 module-owned places assembled as
GENERIC bays, owned by components"* was not a missing composition. Three of
those places have an authority-1 frame taken FROM INSIDE them and no interior
at all: a player who walked into Observation Dome 1 would see the background,
and the background is black.

  * `obs_dome_1`  -- **Observation Dome 1 IS Command & Control.**
    `reference/03-sector-blue/comand and contorl.webp`, authority 1, is that
    room seen from inside. `directory.py` puts `cnc` `within="obs_dome_1"`:
    the dome is the VOLUME, C&C is the room standing in it, and this module
    builds the volume and never the room.
  * `obs_dome_2`  -- the second dome. Same component, public gallery.
  * `obs_rotundas` -- `reference/05-sector-green/rotunda.webp`, authority 1,
    and 00-INDEX's richest single entry.

WHAT THE TWO FRAMES ACTUALLY SAY, MEASURED AT 4-6x WITH `tools/refzoom.py`
-------------------------------------------------------------------------
`comand and contorl.webp` (814x610), crop 0.24-0.78 x 0.05-0.60 at 4x and
0.30-0.76 x 0.08-0.34 at 6x:

  * The glazing is a **circle divided by radial spoke mullions into
    trapezoidal panes**, with a **concentric ring rib** and a **large inverted-U
    mullion springing inside the ring**, so the inner field is one unbroken
    pane. Counting panes across the visible upper arc gives **8 to 9**, which
    closes to 16-18 for a ring. `components.DOME_MULLIONS = 16` was already
    derived from exactly this count and this module does not re-derive it.
  * A **file of small circular studs follows the ring rib** -- rivet detail at
    close pitch, which is why the ring band here is a BAND and not a line.
  * The surrounding bulkhead is **flat white-grey panelling with heavy
    diagonal braces**; beyond the glass, haze and a dark gantry structure.
  * **Two courses of long horizontal cyan-white light strips** at high and mid
    level on the side walls, separated by dark panel bands. This is the room's
    ambient light and `command_control.STRIP_Y_M` already carries the heights.

`rotunda.webp` (716x968), crop 0.02-0.98 x 0.19-0.50 at 3x:

  * **Eight columns across the far arc**, evenly spaced -- a closed ring at
    that spacing implies roughly sixteen bays. The SAME number, from a second
    frame and a different sector.
  * Column order: a plain slightly tapered shaft, a group of **THREE narrow
    ring collars** at just over mid height (measured on the crop: collars at
    y 450-500 of a shaft running y 250-700, i.e. **0.54** of the way up), a
    longer plain shaft, then a short stepped capital under the entablature.
  * Above the columns a **corbel course of stepped rectangular blocks in
    layered tiers**, then a **smooth warm dome with broad radial ribs**.
  * Wall below: a **continuous band of narrow pale vertical slats at about
    waist height** running right round the room, lit so it reads as a bright
    horizontal ribbon.
  * Floor: a **radiating sunburst mosaic** -- triangular radial wedges about a
    centre and a broad concentric band of chevrons at larger radius.
  * A flight of about ten pale steps rising to a dark portal on the far side.

THE BAND PROPORTIONS ARE THE ROTUNDA FRAME'S OWN, and they are the one thing
in it that survives not knowing its scale. Measured off the same 3x crop, at
the far arc where the columns are seen face on:

    opaque wall below the sill   350 px
    window ring                  205 px      = 0.586 of the wall
    corbel course                165 px      = 0.471 of the wall

WHAT THE FRAMES CANNOT SAY, AND IT IS THE HONEST FINDING
--------------------------------------------------------
**Neither frame establishes its room's absolute size, and I tried.** The
rotunda's only in-frame scale anchors are human figures, and every one of them
is at a different depth from the wall being measured. The two dark-robed
figures at the foot of the steps read 130 px for 1.75 m, which is 74.3 px/m at
THEIR depth; the far window band is 147 px tall, which at that scale is 1.98 m
and at any plausible depth correction is more. Running the chain the other way
-- assume a 2.4 m window band, get 61 px/m, get an 8.8 m camera distance, get
a 9-10 m room; assume a 4 m band and get a 15 m room. The answer is whatever
you assumed. This is `command_control.py`'s own recorded trap ("the ordinary
trap of comparing two measurements taken at different depths") and it does not
have a solution from one frame.

So: **the frames give the ORDER and the schema gives the SIZE.** Contract 5,
via `interior.load()["components"]`, is authority 3 and says `observation_dome`
is radius 46 m by height 34 m and `observation_rotunda` radius 62 m by 40 m.
`command_control.py` already reads it that way -- "compatible with Contract 5's
92 m dome: the dome is the volume, the window is one aperture in its forward
face" -- and hard rule 4 makes it binding: inside and outside come from one
model, so the surface a player looks up at IS the surface the hull shows, built
by the same `components.dome_mesh` call with `flip=True`.

SEE INV-232 for the two extrapolations this forces and what would overturn
each: the radius clip against the register's own footprint, and the sill.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bespoke as _bsp                                          # noqa: E402
import command_control as _cc                                   # noqa: E402
import components as _comp                                      # noqa: E402
import interior_kit as _kit                                     # noqa: E402
import rooms as _rooms                                          # noqa: E402


# Which schema component each place is the inside of. The register says
# `module="components"` for nine places; six of them are exterior hardware with
# no interior at all and are listed in `bespoke.NOT_COMPOSED_COMPONENTS` with
# the reason. These three are rooms.
PLACE_COMPONENT = {
    "obs_dome_1": "observation_dome",
    "obs_dome_2": "observation_dome",
    "obs_rotundas": "observation_rotunda",
}

# ...and which ORDER each is built in. Two places share one component and are
# not one room: `directory.py` gives Dome 1 `functions=("structure",
# "viewport")` with `within="cnc"` and Dome 2 `("observation", "structure")`,
# and each of the two frames is of a different one of these orders. This is
# `bespoke.QUARTERS_CLASS`'s rule -- the CLASS comes from the place, because
# rendering one class twice is two frames of one room.
PLACE_ORDER = {
    "obs_dome_1": "command",
    "obs_dome_2": "command",
    "obs_rotundas": "rotunda",
}

# See `PROVIDES` in quarters.py and command_control.py: what a player can use,
# by the group that IS the surface. `directory.py` declares `viewport` for all
# three and `bench` for the rotundas.
PROVIDES = {
    "dome_glazing": "viewport",
    "worship_bench": "bench",
}


# --- what the schema fixes -------------------------------------------------
# Nothing here. Radius and height are read from `interior.load()` per place --
# see `geometry()` -- because a second copy of a schema number is a second
# thing to drift. `command_control.DOME_R_M`/`DOME_H_M` are that second copy
# and this module deliberately does not import them.

# --- what the frames fix ---------------------------------------------------
# Rotunda band proportions, as ratios of the opaque wall below the sill.
# Measured off rotunda.webp -- see the module docstring for the pixel figures.
ROT_WINDOW_FRAC = 205.0 / 350.0        # 0.586
ROT_CORBEL_FRAC = 165.0 / 350.0        # 0.471
# The rotunda's sill, measured. 748 px (floor) - 430 px (sill) = 318 px at the
# 74.3 px/m the figures at the foot of the steps give, and every depth
# correction available makes it LARGER, never smaller. So this is a lower
# bound stated as a value: the rotunda's window ring is a clerestory.
ROT_SILL_M = 4.30
# The slat band: 748-650 px to 748-590 px at the same scale.
ROT_SLAT_LO_M, ROT_SLAT_HI_M = 1.32, 2.13
# Three ring collars at 0.54 of the shaft, counted and measured on the 3x crop.
ROT_COLLARS = 3
ROT_COLLAR_AT = 0.54
ROT_STEPS = 10                          # "a flight of about ten pale steps"
ROT_BANNERS = 4                         # "four hanging banners"

# The command order takes its window band from the frame's own window: 5.5 m,
# `command_control.WINDOW_D_M`, which is the depth-corrected fit of the visible
# arc and the only metric dimension either frame yields. A band as tall as the
# window is wide is the same aperture wrapped round a ring.

# --- what the DOORWAY fixes, and it is the one thing neither frame can ------
# THE SILL CANNOT BE LOWER THAN THE DOOR. `bespoke.DOOR_H_M` is 2.40 m and the
# opaque podium below the sill is the only band of this room a doorway can be
# cut in without cutting the shell -- so a sill under 2.40 m would put the
# corridor's aperture halfway up a pane of glass. 0.20 m of head above the
# aperture is the same margin `doorway_wall` leaves everywhere else.
#
# This is why the command order's sill is 2.60 m and not the ~1 m the C&C frame
# shows. It is a real difference and it is stated rather than hidden: the frame
# is a 5.5 m round window in a flat bulkhead, and this is a 289 m glazed ring.
SILL_MIN_M = _bsp.DOOR_H_M + 0.20

# Shell thickness. `interior_kit.PROVISIONAL["wall_thickness_m"]` is 0.22 for
# an internal partition; a pressure shell carrying a hull blister is heavier,
# and the value that matters is only that the inner and outer surfaces are far
# enough apart to read as a solid at the reveal a player stands at. 0.45 m is
# twice the partition and is a declared extrapolation -- INV-232.
SHELL_T_M = 0.45
PODIUM_T_M = _kit.PROVISIONAL["wall_thickness_m"]

# THE GLAZING BAY PITCH, and the reason this is not simply 16. Both frames
# count sixteen bays round a ring; the frames' rings are of the order of ten
# metres across and Contract 5's are ninety-two and a hundred and twenty-four.
# Sixteen bays on Dome 1 is an 18 m pane, which is not glazing, it is a wall
# with a hole in it. So the shell is tessellated at the multiple of sixteen
# whose bay pitch lands nearest a real glazing bay, and the frames' sixteen is
# kept as the PRIMARY order: every `segs // 16`th seam carries a heavy spoke
# mullion (a column, in the rotunda) and the rest carry light bars. That is
# what a colonnade with secondary glazing between its columns is, and it
# reproduces the counted number exactly. INV-232.
BAY_PITCH_TARGET_M = 4.5

# The entry porch. A room does not open straight off a corridor, and building
# the threshold rather than assuming it is what makes `near_face_opening`
# answerable: with a porch, the only floor within its 2.0 m band is the porch's
# own, so the widest way in is the aperture and nothing else can win.
#
# WITHOUT IT THE ANSWER IS AMBIGUOUS ON A CIRCLE, and it was measured before it
# was fixed: the podium's facets fall out of `deck._mouth_clear`'s 1.2 m band
# by the fourth one either side of the entry, while the floor behind them is
# still inside `near_face_opening`'s 2.0 m band -- so a circular room offers a
# clear "opening" a dozen metres off its own axis, and `room_shell` would shift
# the whole dome sideways onto it.
PORCH_HALF_W_M = 2.00
PORCH_DEPTH_M = 2.50


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


class _M:
    """Accumulator. Same shape as `command_control._M`, deliberately.

    `bespoke._spans` accepts either a per-triangle name list or (name, lo, hi)
    spans; this emits the first, which is what every other bespoke module
    emits.
    """

    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def merge(self, verts, tris, group):
        i = len(self.v)
        self.v.extend(tuple(float(c) for c in p) for p in verts)
        self.t.extend((a + i, b + i, c + i) for a, b, c in tris)
        self.g.extend([group] * len(tris))

    def box(self, group, lo, hi):
        """A closed axis-aligned box, outward-wound, from two corners."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        v, t = [], []
        _comp._box(v, t, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        self.merge(v, t, group)

    def hexa(self, group, lo, hi):
        """A closed solid from two quads: lo[0..3] and hi[0..3], same order.

        WHAT A FACETED RING WALL IS MADE OF. A podium facet is a trapezoidal
        prism -- its inner chord is shorter than its outer one -- so it is not
        an axis-aligned box and `_box`'s corner order is the only thing that
        makes it closed and outward-wound. Adjacent facets share a corner edge,
        which is a non-manifold contact between two closed solids and NOT an
        opening: `command_control` records the same pattern and the OPEN count,
        which is the one a deck's watertightness depends on, stays at zero.
        """
        v, t = [], []
        _comp._box(v, t, list(lo) + list(hi))
        self.merge(v, t, group)

    def plate(self, group, loop, thick):
        self.merge(*_kit.plate_solid(list(loop), thick), group)

    def pad(self, group, loop, y0, y1):
        self.merge(*_kit.deck_pad(list(loop), y0, y1), group)

    def lathe(self, group, profile, segs, cx=0.0, cz=0.0, th0=0.0):
        """A closed surface of revolution. CAPPED AT BOTH ENDS, ALWAYS.

        `profile` is [(radius, y), ...] ascending in y. There is no `cap_lo` or
        `cap_hi` keyword and that is deliberate: **a lathe with both caps off
        has now shipped three separate times in this repository** --
        `dressing._cyl`, `plant_pipe`, `plant_conduit` -- each time on the
        reasoning that the end faces something nobody looks at, and each time
        it was an object a player could see straight through. A dome is a
        lathe. This one cannot be built open.

        A zero radius at either end is a point rather than a ring, so it fans
        instead of capping -- which is the same repair `dome_mesh` got at its
        pole and produces no degenerate quads.
        """
        v, t = [], []
        rows = []
        for r, y in profile:
            if abs(r) < 1e-9:
                v.append((cx, y, cz))
                rows.append((len(v) - 1, True))
                continue
            i0 = len(v)
            for k in range(segs):
                a = th0 + 2.0 * math.pi * k / segs
                v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
            rows.append((i0, False))
        for (a0, pa), (b0, pb) in zip(rows, rows[1:]):
            if pa and pb:
                continue
            for k in range(segs):
                k1 = (k + 1) % segs
                if pa:
                    t.append((a0, b0 + k, b0 + k1))
                elif pb:
                    t.append((a0 + k, b0, a0 + k1))
                else:
                    t.append((a0 + k, b0 + k, b0 + k1))
                    t.append((a0 + k, b0 + k1, a0 + k1))
        # THE CAPS. Fan from a centre vertex, not from vertex 0 of the ring --
        # a ring fan leaves the next piece nothing to weld to, which is the
        # defect `command_control._M.annulus` records for a stepped dais.
        for i, (i0, point) in ((0, rows[0]), (-1, rows[-1])):
            if point:
                continue
            y = profile[i][1]
            c = len(v)
            v.append((cx, y, cz))
            for k in range(segs):
                k1 = (k + 1) % segs
                t.append((c, i0 + k1, i0 + k) if i == 0
                         else (c, i0 + k, i0 + k1))
        self.merge(v, t, group)


# ---------------------------------------------------------------------------
# The geometry a place resolves to, and it is where the two authorities meet
# ---------------------------------------------------------------------------
def geometry(schema, profile, place):
    """(radius, height, segs, spec) for one place. All of it derived.

    THE SCHEMA SETS THE SHAPE AND THE REGISTER CLIPS THE SIZE, and both halves
    of that are needed. Hard rule 4 says the blister's profile has to be the
    schema's or the inside and the outside disagree; `directory.py`'s footprint
    is what the ring deck has actually reserved, and it is the only statement
    anywhere that two named places do not overlap.

    They agree on Dome 1 and disagree on the other two, which is the useful
    part:

        obs_dome_1    schema 2R = 92.0 m   register arc 96.0 m   -> 46.00 m
        obs_dome_2    schema 2R = 92.0 m   register arc 73.8 m   -> 36.92 m
        obs_rotundas  schema 2R = 124.0 m  register arc 59.0 m   -> 29.52 m

    On Dome 1 the two independent sources land within 4% of each other, which
    is corroboration and not a coincidence -- 26 degrees at r = 211.55 m was
    chosen to hold Contract 5's dome. On the rotundas they are 2.1x apart, and
    the register wins there for a physical reason that can be checked: the
    NEXT place along that deck, `domed_rotunda`, is 12 degrees away, which is
    59.0 m at that radius. A 124 m room would be built through it.

    Height is ALWAYS the schema's, as `height_m / radius_m` applied to whatever
    radius survives -- so a clipped blister is a smaller blister of the same
    shape and never a differently proportioned one.
    """
    cid = PLACE_COMPONENT.get(place["key"])
    if cid is None:
        raise KeyError(
            f"{place['key']}: dome.py builds only "
            f"{sorted(PLACE_COMPONENT)} -- see bespoke.NOT_COMPOSED_COMPONENTS "
            f"for why the other components places are a deliberate no")
    spec = next(c for c in schema["components"] if c["id"] == cid)
    arc_m = _rooms.room_extent_m(schema, profile, place)[0]
    rad = min(float(spec["radius_m"]), arc_m / 2.0)
    hgt = rad * float(spec["height_m"]) / float(spec["radius_m"])
    # A multiple of the counted sixteen, nearest the target bay pitch.
    n = _comp.DOME_MULLIONS
    segs = min((k * n for k in range(1, 9)),
               key=lambda s: abs(2.0 * math.pi * rad / s - BAY_PITCH_TARGET_M))
    return rad, hgt, segs, spec


def bands(place, rad, hgt):
    """(sill, head, cornice) heights for one place's order.

    The two orders differ here and nowhere else in the structure, which is the
    point: one shell, two treatments, and the treatment is what the frame of
    that place establishes.
    """
    order = PLACE_ORDER[place["key"]]
    if order == "rotunda":
        sill = max(ROT_SILL_M, SILL_MIN_M)
        head = sill + sill * ROT_WINDOW_FRAC
        corn = head + sill * ROT_CORBEL_FRAC
    else:
        sill = SILL_MIN_M
        head = sill + _cc.WINDOW_D_M
        corn = head + _cc.WINDOW_D_M * ROT_CORBEL_FRAC
    # A band stack that reached the apex would leave no dome, and on a clipped
    # blister it can: `obs_rotundas` is only 19 m tall. Hold the cornice under
    # two thirds of the rise so the cap is always the dominant surface.
    top = 0.66 * hgt
    if corn > top:
        k = (top - sill) / max(1e-6, corn - sill)
        head, corn = sill + (head - sill) * k, top
    return sill, head, corn


# ---------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------
def observation(schema, profile, place):
    """One observation dome's INTERIOR. Returns (verts, tris, groups).

    Local frame, `rooms.build`'s: +X across, +Y up, floor at y = 0, and the
    face the corridor meets at MAXIMUM z -- which is `bespoke.NEAR_END`'s
    "max_z" and is the porch's outer face.
    """
    rad, hgt, segs, _spec = geometry(schema, profile, place)
    sill, head, corn = bands(place, rad, hgt)
    order = PLACE_ORDER[place["key"]]
    m = _M()

    # The shell's inner and outer radii at the sill, which is where it springs
    # from. Everything below the sill is the podium and everything above is the
    # blister's own surface.
    phi_sill = math.asin(min(0.999, sill / hgt))
    r_out = rad * math.cos(phi_sill)
    r_in = (rad - SHELL_T_M) * math.cos(
        math.asin(min(0.999, sill / (hgt - SHELL_T_M))))

    # A FACET, NOT A VERTEX, ON THE +Z AXIS. `dome_mesh`'s frame for out =
    # (0,1,0) puts `place(0, th)` at (-R cos th, 0, R sin th), so th = pi/2 is
    # the +z direction; a phase of pi/segs moves the vertices half a bay off it
    # and leaves a flat chord there, perpendicular to z, for the doorway. segs
    # is a multiple of 16 and therefore of 4, so that chord always exists.
    th0 = math.pi / segs
    half_chord = r_in * math.sin(th0)
    entry_th = math.pi / 2.0

    _shell(m, place, rad, hgt, segs, th0, sill, head, corn, phi_sill, entry_th)
    _podium(m, place, order, r_in, r_out, segs, th0, sill, entry_th)
    _floor(m, order, r_in, segs, th0)
    _porch(m, order, r_out, segs, th0, sill)
    if order == "rotunda":
        _colonnade(m, r_in, segs, th0, sill, head, corn, entry_th)
        _sunburst(m, r_in, segs, th0)
        _steps(m, r_in, sill)
    else:
        _mullions(m, r_in, segs, th0, sill, head, corn, entry_th)
    _dome_ribs(m, rad, hgt, segs, th0, corn, order)
    _rail(m, order, r_in, segs, th0, entry_th)
    assert len(m.g) == len(m.t), "a triangle with no group name"
    assert half_chord > _bsp.DOOR_HALF_W_M + 0.30, (
        f"{place['key']}: the entry facet is {2 * half_chord:.2f} m across and "
        f"a doorway needs {2 * _bsp.DOOR_HALF_W_M:.2f} m plus jambs")
    return m.v, m.t, m.g


def _band_of(y, sill, head, corn, order):
    """Which named band a height falls in. ONE surface, four names.

    The shell is a single closed solid built by one `dome_mesh` pair, and the
    wall / glazing / cornice / cap reading is imposed on it afterwards by
    height. Doing it this way rather than as four lathes is what keeps the
    surface watertight without any welding: there are no band boundaries to
    join, only triangles that answer differently.
    """
    if y < sill - 1e-6:
        return "wall"
    if y < head - 1e-6:
        return "glazing"
    if y < corn - 1e-6:
        return "cornice"
    return "cap"


_GROUPS = {
    # command order -- Observation Dome 1 and 2. `cc_*` is not a borrowed
    # prefix: Dome 1 IS Command & Control's dome, these ARE the surfaces
    # `materials.py` measured off `comand and contorl.webp`, and using the
    # same names is what stops one frame producing two material libraries.
    "command": {"wall": "cc_panel", "glazing": "cc_glazing",
                "cornice": "cc_cornice", "cap": "cc_soffit",
                "podium": "cc_panel", "floor": "cc_floor",
                "rib": "cc_mullion", "ring": "cc_ring", "rail": "cc_rail",
                "strip": "cc_light_strip", "cove": "light_house_cove",
                "porch": "cc_bulkhead", "inlay": "cc_dais",
                "step": "cc_stair", "banner": "signage_panel"},
    # rotunda order. `worship_deck` is the material `materials.py` measured
    # from rotunda.webp itself -- "the floor's cream-and-grey radiating mosaic"
    # -- so the sunburst is laid in its own frame's own stone.
    "rotunda": {"wall": "worship_wall", "glazing": "cc_glazing",
                "cornice": "worship_wall", "cap": "worship_wall",
                "podium": "worship_wall", "floor": "worship_deck",
                "rib": "worship_rib", "ring": "worship_rib", "rail": "cc_rail",
                "strip": "light_wall_course", "cove": "light_house_cove",
                "porch": "worship_wall", "inlay": "worship_rib",
                "step": "cc_stair", "banner": "signage_panel"},
}


def _shell(m, place, rad, hgt, segs, th0, sill, head, corn, phi_sill, entry_th):
    """The blister, with THICKNESS, from the same function the hull uses.

    Two `dome_mesh` calls and an annulus rimming their base rings. The outer
    is the surface `components.domes` puts on the hull; the inner is the same
    surface at (rad - t, hgt - t) with every triangle reversed, which is the
    one a player sees. Neither carries its base disc -- the annulus is what
    closes the pair, and it is `interior_kit.plate_solid`'s shape.

    A SINGLE MEMBRANE WOULD HAVE BEEN CHEAPER AND WRONG. `bespoke`'s ledger of
    3,693 open edges across six modules is one defect in six costumes -- "a
    plate with no thickness is a plate with a boundary" -- and a dome is the
    largest plate on the station.
    """
    g = _GROUPS[PLACE_ORDER[place["key"]]]
    lat = _latitudes(phi_sill, sill, head, corn, hgt)
    v, t = [], []
    base_o = _comp.dome_mesh(v, t, 0.0, 0.0, 0.0, (0.0, 1.0, 0.0), rad, hgt,
                             segs=segs, base_disc=False, th0=th0, phis=lat)
    n_out = len(t)
    lat_i = _latitudes(math.asin(min(0.999, sill / (hgt - SHELL_T_M))),
                       sill, head, corn, hgt - SHELL_T_M)
    base_i = _comp.dome_mesh(v, t, 0.0, 0.0, 0.0, (0.0, 1.0, 0.0),
                             rad - SHELL_T_M, hgt - SHELL_T_M, segs=segs,
                             base_disc=False, th0=th0, phis=lat_i, flip=True)
    # The base annulus. Outer ring wound to face DOWN, which is what closes a
    # shell standing on a podium.
    for k in range(segs):
        k1 = (k + 1) % segs
        t.append((base_o + k, base_i + k, base_i + k1))
        t.append((base_o + k, base_i + k1, base_o + k1))

    # NAMES BY HEIGHT, AND BY AZIMUTH AT THE ENTRY. The entry bay is opaque all
    # the way up: a player who walked through the aperture and met a pane of
    # glass would be looking at the corridor through the hull.
    half_bay = math.pi / segs
    for i, tri in enumerate(t):
        p = [v[j] for j in tri]
        y = sum(q[1] for q in p) / 3.0
        band = _band_of(y, sill, head, corn, PLACE_ORDER[place["key"]])
        if band == "glazing":
            th = math.atan2(sum(q[2] for q in p) / 3.0,
                            -sum(q[0] for q in p) / 3.0)
            d = abs((th - entry_th + math.pi) % (2 * math.pi) - math.pi)
            if d < half_bay * 1.05:
                band = "wall"
        m.g.append(g[band] if i < n_out or band != "glazing" else g["glazing"])
    off = len(m.v)
    m.v.extend(tuple(float(c) for c in q) for q in v)
    m.t.extend((a + off, b + off, c + off) for a, b, c in t)


def _latitudes(phi_lo, sill, head, corn, hgt):
    """Latitudes for the shell lathe, with rows landing ON the band lines.

    `dome_mesh`'s uniform ramp puts a row NEAR a sill and never on one, so a
    band boundary would fall mid-quad and a glazing triangle would be half
    wall. Explicit latitudes are what `phis` exists for.
    """
    want = [phi_lo]
    for y in (head, corn):
        if 0.0 < y < hgt:
            want.append(math.asin(min(0.999, y / hgt)))
    # Eight rows over the cap, which is where all the curvature is.
    hi = want[-1]
    want += [hi + (math.pi / 2.0 - hi) * (k + 1) / 9.0 for k in range(8)]
    out = []
    for p in want:
        if not out or p > out[-1] + 1e-4:
            out.append(p)
    return out


def _podium(m, place, order, r_in, r_out, segs, th0, sill, entry_th):
    """The opaque band below the sill, faceted, with the doorway in it.

    ONE FACET IS THE WAY IN. `bespoke.doorway_wall` takes the caller's own box
    primitive and emits pieces AROUND the aperture -- never a solid with a hole
    punched through it, which is `quarters.unit`'s recorded rule and the
    mistake `command_control.py` shipped when it sealed its own window inside a
    wall.
    """
    g = _GROUPS[order]
    ent = _entry_facet(segs)
    for k in range(segs):
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        p = [(-r_in * math.cos(a), 0.0, r_in * math.sin(a)) for a in (a0, a1)]
        q = [(-r_out * math.cos(a), 0.0, r_out * math.sin(a)) for a in (a0, a1)]
        if k == ent:
            # The entry facet is axis-aligned by construction -- both its ends
            # are at z = r cos(pi/segs) -- so it is a box and `doorway_wall`
            # can cut it.
            x0, x1 = sorted((p[0][0], p[1][0]))
            m_z0, m_z1 = p[0][2], q[0][2]
            _bsp.doorway_wall(lambda n, lo, hi: m.box(n, lo, hi), g["podium"],
                              x0, x1, 0.0, sill, min(m_z0, m_z1),
                              max(m_z0, m_z1))
            continue
        m.hexa(g["podium"],
               [(p[0][0], 0.0, p[0][2]), (p[1][0], 0.0, p[1][2]),
                (p[1][0], sill, p[1][2]), (p[0][0], sill, p[0][2])],
               [(q[0][0], 0.0, q[0][2]), (q[1][0], 0.0, q[1][2]),
                (q[1][0], sill, q[1][2]), (q[0][0], sill, q[0][2])])
    _wall_light(m, order, r_in, segs, th0, sill, ent)


def _entry_facet(segs):
    """The facet index whose chord is perpendicular to +z. See `th0`."""
    return segs // 4 - 1


def _wall_light(m, order, r_in, segs, th0, sill, ent):
    """The lit band on the podium, and it is a different band per order.

    Command: `command_control.STRIP_Y_M` is (2.35, 3.55) measured off the C&C
    frame's two courses of horizontal cyan-white strips. A 2.60 m podium holds
    the lower one; the upper course is carried by the cornice cove instead,
    which is where a 34 m room puts its high-level wash.

    Rotunda: "a continuous band of narrow pale vertical slats at about waist
    height running right around the room, lit so it reads as a bright
    horizontal ribbon" -- 1.32 to 2.13 m, measured.
    """
    g = _GROUPS[order]
    if order == "rotunda":
        lo, hi = ROT_SLAT_LO_M, min(ROT_SLAT_HI_M, sill - 0.20)
        # SLATS, not a ribbon. The frame counts them and a flat lit strip is
        # the thing this room is least like: four narrow slats a bay, each a
        # closed plate, is what makes it read as a comb at half distance.
        per = 4
        for k in range(segs):
            if k == ent:
                continue
            for j in range(per):
                f = (j + 0.5) / per
                a = th0 + 2.0 * math.pi * (k + f) / segs
                w = 2.0 * math.pi * r_in / segs / per * 0.34
                _tangent_plate(m, g["strip"], r_in - 0.02, a, w, lo, hi)
        return
    y = min(_cc.STRIP_Y_M[0], sill - 0.30)
    for k in range(segs):
        if k == ent:
            continue
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        _chord_plate(m, g["strip"], r_in - 0.02, a0, a1, y, y + _cc.STRIP_H_M)


def _tangent_plate(m, group, r, a, half_w, y0, y1):
    """A plate tangent to the ring at angle `a`, facing inward."""
    c, s = -math.cos(a), math.sin(a)
    tx, tz = s, c                                # along the ring
    p = [(r * c + tx * half_w, y0, r * s + tz * half_w),
         (r * c - tx * half_w, y0, r * s - tz * half_w),
         (r * c - tx * half_w, y1, r * s - tz * half_w),
         (r * c + tx * half_w, y1, r * s + tz * half_w)]
    m.plate(group, p, 0.05)


def _chord_plate(m, group, r, a0, a1, y0, y1):
    """A plate on the chord from a0 to a1, facing inward (toward the axis)."""
    p0 = (-r * math.cos(a0), r * math.sin(a0))
    p1 = (-r * math.cos(a1), r * math.sin(a1))
    p = [(p1[0], y0, p1[1]), (p0[0], y0, p0[1]),
         (p0[0], y1, p0[1]), (p1[0], y1, p1[1])]
    m.plate(group, p, 0.05)


def _floor(m, order, r_in, segs, th0):
    """The deck. A polygon pad matching the podium's inner face exactly.

    Emitted as `interior_kit.deck_pad`, so it is a closed solid with a rim and
    not a fan -- `deck_pad`'s own docstring records the eight downlight pools
    that contributed 480 of a Zocalo bay's 736 open edges by being flat.
    """
    loop = [(-r_in * math.cos(th0 + 2.0 * math.pi * k / segs),
             r_in * math.sin(th0 + 2.0 * math.pi * k / segs))
            for k in range(segs)]
    m.pad(_GROUPS[order]["floor"], loop, -0.14, 0.0)


def _porch(m, order, r_out, segs, th0, sill):
    """The threshold: a short bay outside the podium, with the door in its end.

    See `PORCH_HALF_W_M` for why this is not optional on a circular plan.
    """
    g = _GROUPS[order]
    z0 = r_out * math.cos(math.pi / segs)
    z1 = z0 + PORCH_DEPTH_M
    h = max(sill, _bsp.DOOR_H_M + 0.20)
    w = PORCH_HALF_W_M
    t = PODIUM_T_M
    m.box(g["floor"], (-w - t, -0.14, z0), (w + t, 0.0, z1))
    m.box(g["porch"], (-w - t, 0.0, z0), (-w, h + t, z1))
    m.box(g["porch"], (w, 0.0, z0), (w + t, h + t, z1))
    m.box(g["porch"], (-w - t, h, z0), (w + t, h + t, z1))
    _bsp.doorway_wall(lambda n, lo, hi: m.box(n, lo, hi), g["porch"],
                      -w, w, 0.0, h, z1 - t, z1)


def _colonnade(m, r_in, segs, th0, sill, head, corn, entry_th):
    """The rotunda's window ring: sixteen columns, and glazing bars between.

    The column order is `rotunda.webp`'s, counted and measured: a plain
    slightly tapered shaft, THREE narrow ring collars at 0.54 of the shaft, a
    longer plain shaft, a short stepped capital under the entablature. Built as
    one `_M.lathe` per column so the collars are geometry rather than a texture
    -- the rubric's half distance is where a painted collar stops working.

    Above them the corbel course: "stepped rectangular blocks in layered
    tiers", two tiers a bay, the upper oversailing the lower.
    """
    g = _GROUPS["rotunda"]
    ent = _entry_facet(segs)
    primary = max(1, segs // _comp.DOME_MULLIONS)
    hcol = head - sill
    rc = 0.055 * hcol                            # shaft radius
    prof = [(0.0, sill), (rc * 1.22, sill), (rc * 1.22, sill + 0.10 * hcol),
            (rc * 1.02, sill + 0.16 * hcol)]
    y = sill + (ROT_COLLAR_AT - 0.06) * hcol
    for _ in range(ROT_COLLARS):                 # three narrow ring collars
        prof += [(rc, y), (rc * 1.30, y + 0.012 * hcol),
                 (rc * 1.30, y + 0.030 * hcol), (rc, y + 0.042 * hcol)]
        y += 0.050 * hcol
    prof += [(rc * 0.96, head - 0.16 * hcol), (rc * 1.28, head - 0.10 * hcol),
             (rc * 1.28, head - 0.05 * hcol), (rc * 1.46, head - 0.04 * hcol),
             (rc * 1.46, head), (0.0, head)]
    prof.sort(key=lambda p: p[1])
    for k in range(segs):
        a = th0 + 2.0 * math.pi * k / segs
        if k == ent or (k + 1) % segs == ent:
            continue
        if k % primary == 0:
            m.lathe(g["rib"], prof, 10,
                    cx=-(r_in - rc * 1.5) * math.cos(a),
                    cz=(r_in - rc * 1.5) * math.sin(a))
        else:
            _tangent_plate(m, g["ring"], r_in - 0.10, a, rc * 0.42, sill, head)
    # The corbel course.
    for k in range(segs):
        if k == ent:
            continue
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        for j, (inset, lo, hi) in enumerate((
                (0.30, head, head + 0.45 * (corn - head)),
                (0.75, head + 0.45 * (corn - head), corn))):
            f = 0.16 if j == 0 else 0.30
            am = (a0 + a1) / 2.0
            _chord_plate(m, g["cornice"], r_in - inset,
                         a0 + (a1 - a0) * f, a1 - (a1 - a0) * f, lo, hi)
            del am
    _banners(m, r_in, segs, th0, sill, ent)


def _banners(m, r_in, segs, th0, sill, ent):
    """Four hanging banners, evenly placed, clear of the entry bay."""
    g = _GROUPS["rotunda"]
    step = max(1, segs // ROT_BANNERS)
    for j in range(ROT_BANNERS):
        k = (ent + 2 + j * step) % segs
        if k == ent:
            continue
        a = th0 + 2.0 * math.pi * (k + 0.5) / segs
        w = 2.0 * math.pi * r_in / segs * 0.22
        _tangent_plate(m, g["banner"], r_in - 0.14, a, w,
                       0.34 * sill, 0.95 * sill)


def _sunburst(m, r_in, segs, th0):
    """The radiating floor mosaic: triangular radial wedges and a chevron band.

    "Circular mosaic with a radiating sunburst in cream and grey" (00-INDEX),
    and re-examined as "triangular radial wedges about a centre, and a broad
    concentric band of chevrons at larger radius". Laid as `deck_pad` solids a
    few millimetres proud, which is `interior_kit`'s own idiom for inlay and
    the reason a lit pool reads at grazing incidence.
    """
    g = _GROUPS["rotunda"]
    r1, r2 = 0.34 * r_in, 0.62 * r_in
    for k in range(0, segs, 2):
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        m.pad(g["inlay"],
              [(0.0, 0.0),
               (-r1 * math.cos(a0), r1 * math.sin(a0)),
               (-r1 * math.cos(a1), r1 * math.sin(a1))], 0.0, 0.014)
    for k in range(segs):
        a0 = th0 + 2.0 * math.pi * k / segs
        am = th0 + 2.0 * math.pi * (k + 0.5) / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        m.pad(g["inlay"],
              [(-r1 * math.cos(a0), r1 * math.sin(a0)),
               (-r2 * math.cos(am), r2 * math.sin(am)),
               (-r1 * math.cos(a1), r1 * math.sin(a1))], 0.0, 0.014)


def _steps(m, r_in, sill):
    """The flight of about ten pale steps to the portal on the far side.

    Opposite the entry, which is where the frame puts it relative to its own
    camera -- and which is also the only place on a ring a flight can go
    without standing in the way in.
    """
    g = _GROUPS["rotunda"]
    rise = min(0.18, (sill - 0.60) / ROT_STEPS)
    tread = 0.40
    w = min(4.2, 0.16 * r_in)
    for i in range(ROT_STEPS):
        z = -r_in + 0.30 + (ROT_STEPS - i) * tread
        m.box(g["step"], (-w, 0.0, z - tread), (w, rise * (i + 1), z))


def _mullions(m, r_in, segs, th0, sill, head, corn, entry_th):
    """The command order's window ring: radial spokes and a concentric band.

    `command_control.WINDOW_MULLIONS` is 16 and `WINDOW_RING_FRAC` is 0.62,
    both proportioned off `comand and contorl.webp` (INV-024), and both are
    imported rather than restated -- one frame, one set of numbers.

    The heavy spokes are every `segs // 16`th seam, so the counted sixteen
    survives at a bay pitch the frame could not have known about. The rest are
    the light glazing bars between them.
    """
    g = _GROUPS["command"]
    ent = _entry_facet(segs)
    primary = max(1, segs // _cc.WINDOW_MULLIONS)
    for k in range(segs):
        if k == ent or (k + 1) % segs == ent:
            continue
        a = th0 + 2.0 * math.pi * k / segs
        heavy = k % primary == 0
        _tangent_plate(m, g["rib"], r_in - _cc.WINDOW_MULLION_D_M, a,
                       _cc.WINDOW_MULLION_W_M * (3.4 if heavy else 1.0),
                       sill, head)
    yr = sill + (head - sill) * _cc.WINDOW_RING_FRAC
    for k in range(segs):
        if k == ent:
            continue
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        _chord_plate(m, g["ring"], r_in - _cc.WINDOW_MULLION_D_M, a0, a1,
                     yr - _cc.WINDOW_RING_W_M, yr + _cc.WINDOW_RING_W_M)
    # The cornice, and its cove -- the C&C frame's HIGH course of light strips,
    # which a 2.60 m podium has no room for.
    for k in range(segs):
        if k == ent:
            continue
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        _chord_plate(m, g["cornice"], r_in - 0.30, a0, a1,
                     head, head + 0.62 * (corn - head))
        _chord_plate(m, g["cove"], r_in - 0.62, a0, a1,
                     head + 0.66 * (corn - head), corn - 0.10)


def _dome_ribs(m, rad, hgt, segs, th0, corn, order):
    """The cap's ribs, from `components._dome_fittings` with `side = -1`.

    The bars a player looks up at ARE the bars the hull shows, on the other
    face of one shell. `side=-1` rides the fittings on a slightly SMALLER
    similar ellipsoid and flips `_ribbon`'s hint with it, so the thickness goes
    into the room instead of through the glass.

    The rotunda's are "broad radial ribs" and the dome's are glazing spokes, so
    they differ in weight and in nothing else.
    """
    g = _GROUPS[order]
    r_i, h_i = rad - SHELL_T_M, hgt - SHELL_T_M
    phi_lo = math.asin(min(0.999, corn / h_i))
    n = _comp.DOME_MULLIONS
    v, t = [], []
    _comp._dome_fittings(
        v, t, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), r_i, h_i, n,
        side=-1.0, th0=th0, phi_hi=phi_lo + 0.62 * (math.pi / 2.0 - phi_lo),
        rib_w=(0.030 if order == "rotunda" else 0.016) * r_i,
        rib_t=(0.022 if order == "rotunda" else 0.012) * r_i,
        collar=False)
    m.merge(v, t, g["rib"])


def _rail(m, order, r_in, segs, th0, entry_th):
    """A guardrail at the sill, on plain stanchions.

    The C&C frame's are "flat-topped bars on plain stanchions, not the
    red-orange Zocalo type", and a 92 m ring with a glazed wall wants one for
    the same reason the frame's gallery does.
    """
    g = _GROUPS[order]
    ent = _entry_facet(segs)
    h = _cc.RAIL_H_M
    r = r_in - 0.55
    for k in range(segs):
        if k == ent:
            continue
        a0 = th0 + 2.0 * math.pi * k / segs
        a1 = th0 + 2.0 * math.pi * (k + 1) / segs
        _chord_plate(m, g["rail"], r, a0, a1, h - 0.055, h + 0.010)
        m.lathe(g["rail"], [(0.0, 0.0), (0.045, 0.0), (0.045, h - 0.055),
                            (0.0, h - 0.055)], 6,
                cx=-r * math.cos(a0), cz=r * math.sin(a0))


# ---------------------------------------------------------------------------
# The gate, in the module that builds the thing, on the hard case
# ---------------------------------------------------------------------------
def _selftest():
    import interior as _it                                      # noqa: PLC0415
    import directory as _dr                                     # noqa: PLC0415
    import materials as _mat                                    # noqa: PLC0415
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = _it.load()
    places = {q["key"]: q for q in _dr.PLACES}

    # THE ONE THAT MADE THIS MODULE NECESSARY, AS AN ASSERTION AND ITS OWN
    # NEGATIVE CONTROL: the exterior blister faces nobody standing in it, and
    # the interior faces everybody.
    for key in sorted(PLACE_COMPONENT):
        q = places[key]
        v, t, g = observation(schema, profile, q)
        rad, hgt, segs, _spec = geometry(schema, profile, q)
        sill, head, corn = bands(q, rad, hgt)

        eye = (0.0, 1.70, 0.0)
        seen = 0
        for a, b, c in t:
            p0, p1, p2 = v[a], v[b], v[c]
            u = [p1[i] - p0[i] for i in range(3)]
            w = [p2[i] - p0[i] for i in range(3)]
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            mid = [(p0[i] + p1[i] + p2[i]) / 3.0 for i in range(3)]
            if sum(n[i] * (eye[i] - mid[i]) for i in range(3)) > 0.0:
                seen += 1
        check(f"{key}: a body at eye height sees the room",
              seen > 0.35 * len(t),
              f"only {seen} of {len(t)} triangles face the viewer")

        # CLOSURE, and the number is reported rather than merely asserted --
        # "a lathe with cap_lo=False, cap_hi=False is open at both ends" has
        # shipped three times here and a dome is a lathe.
        op, nm = _kit.boundary_edges(v, t)
        check(f"{key}: the shell is closed", len(op) == 0,
              f"{len(op)} open edges, {len(nm)} non-manifold")

        # THE DOORWAY IS THE PLACE A PLAYER LOOKS CLOSEST. Measured with the
        # same function `room_shell` uses, in the module's own frame.
        opn = _bsp.near_face_opening(
            [(x, y, z - max(p[2] for p in v)) for x, y, z in v], t)
        check(f"{key}: the near face has a way in", opn is not None,
              "near_face_opening found no run with floor under it")
        if opn is not None:
            check(f"{key}: the way in is on the room's own axis",
                  abs(opn[0]) < 0.20, f"centre {opn[0]:.3f} m off")
            check(f"{key}: the way in takes the corridor's leaf",
                  opn[1] >= 2.0 * _bsp.DOOR_HALF_W_M - 0.11,
                  f"{opn[1]:.2f} m wide")

        # EVERY GROUP RESOLVES. `test_materials_layer3` scans a fixed module
        # list this file is not on, and `materials._scan_generator_groups`
        # only reads eight prefixes -- so without this a new room ships
        # magenta and nothing anywhere says so.
        bad = sorted({n for n in set(g)
                      if _mat.resolve_any(n, "interior") is None})
        check(f"{key}: every group has a material", not bad, str(bad))

        # The band stack has to be a stack.
        check(f"{key}: bands ascend", 0 < sill < head < corn < hgt,
              f"sill {sill:.2f} head {head:.2f} corn {corn:.2f} hgt {hgt:.2f}")
        check(f"{key}: the sill clears the doorway", sill >= _bsp.DOOR_H_M,
              f"sill {sill:.2f} m against a {_bsp.DOOR_H_M:.2f} m aperture")
        print(f"  {key:14s} R {rad:6.2f} H {hgt:6.2f} segs {segs:3d}  "
              f"sill {sill:5.2f} head {head:5.2f} corn {corn:5.2f}  "
              f"{len(t):6,d} tris  {len(set(g)):2d} groups  "
              f"open {len(op)} non-manifold {len(nm)}  "
              f"faces viewer {seen * 100.0 // len(t):.0f}%")

    # NEGATIVE CONTROL 1 -- the defect this module exists to fix, still
    # measurable on the thing that has it. If this ever stops failing, either
    # `components.domes` grew an interior or the test stopped testing.
    spec = next(c for c in schema["components"] if c["id"] == "observation_dome")
    ev, et = _comp.domes(spec, profile)["observation_dome"]
    n = len(et) // spec["count"]
    zc = spec["z0"] + (spec["z1"] - spec["z0"]) * 0.5 / spec["rows"]
    r0 = _comp.radius_at(profile, zc)
    a = math.radians(spec.get("phase_deg", 0.0))
    centre = (math.cos(a) * r0 * 0.97, math.sin(a) * r0 * 0.97, zc)
    out_seen = 0
    for tri in et[:n]:
        p0, p1, p2 = (ev[i] for i in tri)
        u = [p1[i] - p0[i] for i in range(3)]
        w = [p2[i] - p0[i] for i in range(3)]
        nv = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
              u[0] * w[1] - u[1] * w[0])
        mid = [(p0[i] + p1[i] + p2[i]) / 3.0 for i in range(3)]
        if sum(nv[i] * (centre[i] - mid[i]) for i in range(3)) > 0.0:
            out_seen += 1
    check("CONTROL: the exterior blister still faces nobody inside it",
          out_seen == 0, f"{out_seen} of {n} -- components.domes grew a room?")
    print(f"  CONTROL exterior observation_dome: {out_seen} of {n} triangles "
          f"face a viewer at its base centre")

    # NEGATIVE CONTROL 2 -- an uncapped lathe. `_M.lathe` has no cap keyword
    # BECAUSE this defect has shipped three times; the control proves the
    # measurement that would catch a fourth is live.
    m = _M()
    m.lathe("cc_panel", [(1.0, 0.0), (1.0, 2.0)], 12)
    good = len(_kit.boundary_edges(m.v, m.t)[0])
    bare_v, bare_t = [], []
    for k in range(12):
        a0 = 2 * math.pi * k / 12
        a1 = 2 * math.pi * (k + 1) / 12
        i = len(bare_v)
        bare_v += [(math.cos(a0), 0.0, math.sin(a0)),
                   (math.cos(a1), 0.0, math.sin(a1)),
                   (math.cos(a1), 2.0, math.sin(a1)),
                   (math.cos(a0), 2.0, math.sin(a0))]
        bare_t += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
    bare = len(_kit.boundary_edges(bare_v, bare_t)[0])
    check("CONTROL: an uncapped lathe reads as open", bare == 24 and good == 0,
          f"capped {good}, uncapped {bare}")
    print(f"  CONTROL lathe closure: capped {good} open edges, the same tube "
          f"with cap_lo=False cap_hi=False {bare}")

    # NEGATIVE CONTROL 3 -- the shell must lose its closure if either
    # `dome_mesh` call drops its rim. Built deliberately wrong.
    v, t = [], []
    _comp.dome_mesh(v, t, 0, 0, 0, (0, 1, 0), 10.0, 7.0, segs=16,
                    base_disc=False)
    rimless = len(_kit.boundary_edges(v, t)[0])
    v2, t2 = [], []
    _comp.dome_mesh(v2, t2, 0, 0, 0, (0, 1, 0), 10.0, 7.0, segs=16)
    capped = len(_kit.boundary_edges(v2, t2)[0])
    check("CONTROL: a base_disc=False shell is open at its base",
          rimless == 16 and capped == 0, f"{rimless} / {capped}")
    print(f"  CONTROL dome_mesh: base_disc=False leaves {rimless} open edges, "
          f"base_disc=True leaves {capped}")

    # The registry may not claim a place the register does not have, and the
    # six components places this module refuses must refuse LOUDLY.
    check("every place named here is in the register",
          set(PLACE_COMPONENT) <= set(places),
          str(sorted(set(PLACE_COMPONENT) - set(places))))
    check("PLACE_ORDER covers PLACE_COMPONENT",
          set(PLACE_ORDER) == set(PLACE_COMPONENT))
    refused = []
    for q in _dr.PLACES:
        if q.get("module") != "components" or q["key"] in PLACE_COMPONENT:
            continue
        try:
            observation(schema, profile, q)
            refused.append((q["key"], "built something"))
        except KeyError:
            pass
        except Exception as e:                                  # noqa: BLE001
            refused.append((q["key"], f"raised {type(e).__name__}: {e}"))
    check("the six exterior components places refuse with a KeyError",
          not refused, str(refused))

    print(f"dome.py: {ok} passed, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
