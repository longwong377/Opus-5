"""A Babylon 5 docking bay interior.

The hinge of the seamless launch-and-dock requirement from the opening brief.
The flight model (`physics/starfury.py`, 18 tests) and the docking solver
(`physics/docking.py`, 15 tests) have existed since session 2g; what has never
existed is the room they arrive in.

WHAT THE REFERENCE ESTABLISHES (authority 1 unless noted)

`reference/03-sector-blue/dock.webp` -- the defining frame:

  - It is a **long low slot, not a hangar box**. The mouth is a wide flat-topped
    opening with the far side of the station visible beyond it, and the bay runs
    away from it rather than opening upward.
  - **Red-orange painted structural steel overhead**: deep box girders spanning
    the width, carrying a lattice gantry, with **pendant floodlights** hanging at
    regular spacing. This is the bay's whole lighting scheme and it is the first
    thing that reads.
  - A file of **eleven dock workers** crossing the deck. They are the scale
    anchor -- see MEASURED below -- and the gazetteer is explicit that the deck
    markings must be sized against THEM and not against the Starfuries, whose
    own size is derived rather than sourced.
  - A **large red disc carrying a white oval emblem** painted on the deck.
  - **Yellow-and-black hazard chevrons** on ramp and step edges.
  - Craft parked in a row along one side, tail fins up, one carrying **29**.
  - The ceiling is the **ribbed inner wall of the rotating drum**, curving.

`reference/03-sector-blue/Minbari Flyer 969 in docking bay 17.webp`:

  - **Stepped side ledges**, with chevron nosings on *every* step, not just the
    outermost. Service gantries and handling equipment stand on them.
  - Confirms bays are numbered and that bay 17 exists, which is the on-screen
    cross-check for the Security Manual's "DOCKING BAYS (24)".

WHAT IS NOT SOURCED is the bay's absolute size. No frame contains anything of
known size except the dock workers, and they are on the deck rather than against
a wall. Every dimension below is therefore either measured off them, derived
from canon, or logged in INVENTIONS.md as INV-022.

THE ROTATION PROBLEM, which is why this is not a hangar

The bays are in the **rotating** section. A ship entering one has to match the
station's spin first -- `physics/docking.py` models exactly this, and the result
that an *axial* port has no tangential velocity to match is why the low-g bays
exist for craft too large to spin up. The consequence for geometry is that the
bay's ceiling is a section of the drum wall and curves, and that "up" in the bay
is radially inward. Both are built.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import directory as _directory                                  # noqa: E402
import interior as it                                        # noqa: E402
import rooms as _rooms                                          # noqa: E402

# ---------------------------------------------------------------------------
# Measured
# ---------------------------------------------------------------------------
# `dock.webp` is 1000x750. The file of dock workers spans x = 310..620 px and an
# individual stands about 28 px tall. At a 1.75 m adult that is 16.0 px/m at
# their depth, so the file is 310/16.0 = 19.4 m long for eleven people --
# 1.94 m apart, which is a walking file rather than a parade and is the
# consistency check that the reading is sane.
#
# The red deck disc spans x = 420..590 px at the same depth: 170/16.0 = 10.6 m.
# That is "many times a person tall" as the gazetteer describes it, and it is
# the ONLY painted marking whose size is measured rather than chosen.
DOCK_WORKER_H_M = 1.75
REF_PX_PER_M = 16.0
DECK_DISC_D_M = 10.6

# ---------------------------------------------------------------------------
# Canon
# ---------------------------------------------------------------------------
# Blue Section is 520.4 m in diameter (00-MASTER.md 1.1, authority 3 rescaled),
# and the Security Manual sectional schematic gives DOCKING BAYS (24). Bay 17
# appears on screen, which cross-checks the count from the other direction.
#
# Read from the schema for the same reason as BAY_W_M below: a canon count that
# lives as a literal in one module is a fact this project cannot regenerate
# from its own source of truth.
BAY_COUNT = int(it.load()[0]["docking"]["docking_bay"]["count"])

# 42 m is the schema's own `cobra_bay` width, authority 3 off Contract 5. Using
# it here is not a guess dressed as a citation: it is the width the same
# document gives the same station for the same class of structure -- a bay cut
# into a rotating hull to take a craft -- and adopting it keeps one number
# instead of inventing a second. See INV-022.
#
# READ FROM THE SCHEMA, not retyped from it. It was a bare `42.0` with the
# sentence above sitting over it, which is a duplicated literal wearing a
# citation -- exactly what hard rule 4 exists to stop ("consistency is by
# construction, not by discipline"). `tools/mutation_sweep.py` found it: with
# the value perturbed to 52.5 m the module still passed 18/18, because the only
# assertion touching it asks whether a bay FITS its 66.5 m of arc, and 52.5
# also fits. The prose was the only thing holding the two numbers together.
def _schema_bay_width_m():
    for c in it.load()[0]["components"]:
        if c["id"] == "cobra_bay":
            return float(c["width_m"])
    raise KeyError("cobra_bay is not in the schema's components")


BAY_W_M = _schema_bay_width_m()
BAY_H_M = 18.0          # INV-022: a LOW slot, which is what the frame shows
BAY_LEN_M = 140.0       # INV-022

# Stepped side ledges. Three courses, from the Minbari Flyer frame.
LEDGE_COURSES = 3
LEDGE_RISE_M = 2.2
LEDGE_RUN_M = 3.4
CHEVRON_W_M = 0.9       # the nosing band on every step

# The overhead steel. Deep box girders across the bay, a lattice between them,
# and floodlights pendant from the lattice.
GIRDER_PITCH_M = 11.0
GIRDER_D_M = 2.4        # depth of the box section
GIRDER_W_M = 1.1
LAMP_DROP_M = 2.6
LAMP_R_M = 0.75
LAMPS_PER_BAY_GIRDER = 3


def bay_radius(schema, profile):
    """Radius of the docking bay deck.

    The bays are cut into Blue Section, whose diameter canon fixes at 520.4 m.
    The DECK is inboard of the hull by the same pressure-hull skin every other
    interior uses, so this is derived from canon and INV-013 rather than chosen.
    """
    d = schema["station"]["sections"]["blue"]["diameter_m"]["value"] \
        if "sections" in schema["station"] else 520.4
    return d / 2.0 - it.HULL_SKIN_M


def bay_pitch_deg():
    """Angular spacing of the 24 bays around the docking sphere."""
    return 360.0 / BAY_COUNT


class _M:
    """Vertices, triangles and a per-triangle group."""

    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def quad(self, a, b, c, d, group):
        i = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        self.g.extend([group, group])

    def box(self, x0, x1, y0, y1, z0, z1, group):
        """An axis-aligned solid, wound outward."""
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)

    def as_tuple(self):
        return self.v, self.t, self.g


def _disc(m, cx, cz, r, y, group, seg=28):
    """A flat painted marking on the deck, wound to face UP.

    Ascending angle in the XZ plane with +Y up gives a DOWNWARD normal, so the
    fan is reversed. That mistake has now been made three times in this project
    and each time the geometry was simply invisible, so it is asserted rather
    than remembered.
    """
    i = len(m.v)
    m.v.append((cx, y, cz))
    for k in range(seg):
        a = 2.0 * math.pi * k / seg
        m.v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
    for k in range(seg):
        m.t.append((i, i + 1 + (k + 1) % seg, i + 1 + k))
    m.g.extend([group] * seg)


def docking_bay(index=0, schema=None, profile=None):
    """One bay, authored in its own frame.

    Frame: +Z runs INTO the bay from the mouth at z = 0, +X across, +Y up, and
    the deck is y = 0. Up is radially inward once placed, but authoring in a
    local frame is what lets a height be written down as a height -- the same
    correction the corridor kit needed in session 2p.
    """
    m = _M()
    hw, H, L = BAY_W_M / 2.0, BAY_H_M, BAY_LEN_M

    # --- deck ---------------------------------------------------------------
    m.quad((-hw, 0.0, 0.0), (-hw, 0.0, L), (hw, 0.0, L), (hw, 0.0, 0.0),
           "bay_deck")

    # The red disc with its white emblem, at the measured 10.6 m, set where the
    # frame puts it: off the bay's centreline, on the walking side.
    _disc(m, -hw * 0.30, L * 0.42, DECK_DISC_D_M / 2.0, 0.02, "bay_disc")
    _disc(m, -hw * 0.30, L * 0.42, DECK_DISC_D_M * 0.22, 0.03, "bay_emblem")

    # --- stepped side ledges, chevron on every nosing ------------------------
    for side in (-1, 1):
        x = side * hw
        for c in range(LEDGE_COURSES):
            y0, y1 = c * LEDGE_RISE_M, (c + 1) * LEDGE_RISE_M
            inner = abs(x) - (c + 1) * LEDGE_RUN_M
            outer = abs(x) - c * LEDGE_RUN_M
            xi, xo = side * inner, side * outer
            # tread
            a, b = min(xi, xo), max(xi, xo)
            m.quad((a, y1, 0.0), (a, y1, L), (b, y1, L), (b, y1, 0.0),
                   "bay_ledge")
            # riser
            m.quad((xi, y0, 0.0), (xi, y1, 0.0), (xi, y1, L), (xi, y0, L),
                   "bay_ledge") if side > 0 else m.quad(
                (xi, y0, L), (xi, y1, L), (xi, y1, 0.0), (xi, y0, 0.0),
                "bay_ledge")
            # chevron nosing band on the tread edge
            cx0 = xi - side * CHEVRON_W_M
            m.quad((min(xi, cx0), y1 + 0.01, 0.0), (min(xi, cx0), y1 + 0.01, L),
                   (max(xi, cx0), y1 + 0.01, L), (max(xi, cx0), y1 + 0.01, 0.0),
                   "bay_chevron")

    # --- the curving ribbed ceiling: the drum's inner wall -------------------
    # A shallow arc rather than a flat soffit. The bay is cut into a rotating
    # hull, so its roof is a section of that hull and curves across the width.
    seg = 16
    sag = BAY_W_M * 0.10
    def ceil_y(t):
        return H + sag * (1.0 - (2.0 * t - 1.0) ** 2)
    for k in range(seg):
        t0, t1 = k / seg, (k + 1) / seg
        x0, x1 = -hw + BAY_W_M * t0, -hw + BAY_W_M * t1
        m.quad((x0, ceil_y(t0), 0.0), (x1, ceil_y(t1), 0.0),
               (x1, ceil_y(t1), L), (x0, ceil_y(t0), L), "bay_ceiling")

    # --- overhead steel: box girders, lattice, pendant floodlights -----------
    n_g = max(1, int(L / GIRDER_PITCH_M))
    for i in range(n_g + 1):
        z = L * i / n_g
        m.box(-hw, hw, H - GIRDER_D_M, H, z - GIRDER_W_M / 2.0,
              z + GIRDER_W_M / 2.0, "bay_girder")
        for j in range(LAMPS_PER_BAY_GIRDER):
            lx = -hw + BAY_W_M * (j + 0.5) / LAMPS_PER_BAY_GIRDER
            m.box(lx - LAMP_R_M, lx + LAMP_R_M,
                  H - GIRDER_D_M - LAMP_DROP_M, H - GIRDER_D_M,
                  z - LAMP_R_M, z + LAMP_R_M, "bay_lamp")

    # --- back wall, and the mouth left open ---------------------------------
    m.quad((-hw, 0.0, L), (-hw, ceil_y(0.5), L), (hw, ceil_y(0.5), L),
           (hw, 0.0, L), "bay_backwall")

    # ARTICULATION -- rooms.articulate(), INV-073. 38.2% of its detail floor:
    # a 140 m hangar whose walls were flat plate. Conduit off -- a bay this tall
    # puts the band above the useful envelope -- and the grids coarse, because
    # 23,000 m2 at a corridor's pitch is not detail, it is a triangle bill.
    #
    # `_M` keeps ONE GROUP PER TRIANGLE and `articulate` emits (name, lo, hi)
    # SPANS, so this adapts rather than reaching into either. Two group
    # conventions in one module is how a mesh silently loses its material
    # bindings.
    av, at, aspans = [], [], []
    _rooms.articulate(av, at, aspans, "bay", hw, L / 2.0, H,
                      z_off=L / 2.0, conduit=False, deck=False,
                      scale=5.5)
    # DECK JOINTS OFF, and this one is a placement fact rather than a
    # taste call: a joint is emitted 10 mm BELOW the deck plane, which
    # is correct in a room whose deck is a 140 mm slab and wrong here,
    # because once placed the bay's deck IS the outermost surface --
    # up is radially inward. Ten millimetres put the bay outside
    # Blue's hull. Both of this module's own assertions caught it.
    off = len(m.v)
    per = [None] * len(at)
    for nm, lo, hi in aspans:
        for i in range(lo, hi):
            per[i] = nm
    m.v.extend(av)
    m.t.extend((a + off, b + off, c + off) for a, b, c in at)
    m.g.extend(per)

    return m.as_tuple()


def bay_angle_deg(index):
    return (index % BAY_COUNT) * bay_pitch_deg()


def mouth_z_m():
    """Where the bay's mouth is in STATION coordinates, and which way it faces.

    `docking_bay()` authors the bay in its own frame with the mouth at local
    z = 0 and +Z running into it. That says where the mouth is relative to the
    back wall and nothing about where it is on the station, and until session
    3z nothing said the second thing at all -- which is how the bays came to
    have no exterior (`docs/volume-audit.md` §5.1).

    The register puts the bays at z = 7115 with a 140 m footprint, so the bay
    occupies z 7045-7185. The mouth is at the FORE end, 7185, and that is a
    finding rather than a choice -- see INV-100. Fore, the docking sphere's
    taper falls through the mouth's radial band and the prism swept out of the
    mouth leaves the hull through it. Aft, the hull at z 7045 is already
    166.2 m, well inside the 232-254 m the mouth spans, so a mouth facing that
    way opens onto nothing: there is no hull left to make a hole in.

    So placing a bay in station coordinates is z_station = mouth_z_m() - z_local.
    """
    place = _directory.by_key("docking_bays")
    return place["z_m"] + place["footprint"][1] / 2.0


def place_bay(index, schema=None, profile=None, station_z=False):
    """One bay placed in station coordinates, at its own angle.

    `station_z` maps the bay's local z onto the station's, mouth fore -- see
    `mouth_z_m`. It defaults off because `bespoke.py` and `density.py` both
    consume this module's LOCAL frame and both have assertions about which way
    round it is.

    Up in the bay becomes radially INWARD, and +Z stays axial. The bay deck sits
    at `bay_radius()`, so a person standing in a bay is standing on the inside
    of the rotating hull looking toward the axis -- the same convention as every
    other interior in the project.
    """
    if schema is None:
        schema, profile = it.load()
    v, t, g = docking_bay(index, schema, profile)
    r0 = bay_radius(schema, profile)
    a = math.radians(bay_angle_deg(index))
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y, z in v:
        # local +Y (up) -> radially inward; local +X -> an ARC at constant
        # radius, not a tangent.
        #
        # A tangent was the first version and it pushed the bay's edges OUTSIDE
        # the hull: a point 21 m along a tangent from radius 254.2 is at
        # sqrt(254.2^2 + 21^2) = 255.1, so both bay walls stood 0.9 m proud of
        # the pressure hull they are cut into. The floor of a bay in a rotating
        # hull follows that hull, and over a 42 m width at this radius it
        # genuinely cambers by 0.87 m -- enough that a craft parked across the
        # bay sits nose-down relative to one parked along it.
        r = r0 - y
        aa = a + x / r0
        zz = (mouth_z_m() - z) if station_z else z
        out.append((r * math.cos(aa), r * math.sin(aa), zz))
    return out, t, g


def budget_report(out=print):
    v, t, g = docking_bay()
    per = {}
    for name in g:
        per[name] = per.get(name, 0) + 1
    out(f"one bay: {len(v):,} verts, {len(t):,} tris")
    for k in sorted(per, key=lambda k: -per[k]):
        out(f"  {k:<16} {per[k]:6,}")
    out(f"all {BAY_COUNT} bays: {len(t) * BAY_COUNT:,} tris "
        f"(instanced: {len(t):,} unique)")
    return len(t)


def write_obj(path, index=0):
    v, t, g = docking_bay(index)
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


# ---------------------------------------------------------------------------
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
    v, t, g = docking_bay()

    check("bay is a long low slot, not a hangar box",
          BAY_LEN_M > BAY_W_M > BAY_H_M,
          f"L {BAY_LEN_M} > W {BAY_W_M} > H {BAY_H_M}")

    # The deck marking is the one painted feature with a measured size. If the
    # px/m reading changes, this must move with it rather than staying put.
    check("the deck disc matches its measured diameter",
          abs(DECK_DISC_D_M - 170.0 / REF_PX_PER_M) < 0.05,
          f"{DECK_DISC_D_M} m against 170 px / {REF_PX_PER_M} px/m")
    check("the scale anchor is the dock workers, not the craft",
          abs(REF_PX_PER_M - 28.0 / DOCK_WORKER_H_M) < 0.05,
          f"{REF_PX_PER_M} px/m from a {DOCK_WORKER_H_M} m figure at 28 px")

    # Flat painted markings and treads must face UP. Three separate subsystems
    # in this project have shipped flat geometry facing down, and it is
    # invisible every time.
    for grp in ("bay_deck", "bay_disc", "bay_emblem", "bay_chevron"):
        bad = 0
        for i, tri in enumerate(t):
            if g[i] != grp:
                continue
            p0, p1, p2 = (v[k] for k in tri)
            u = tuple(p1[k] - p0[k] for k in range(3))
            w = tuple(p2[k] - p0[k] for k in range(3))
            ny = u[2] * w[0] - u[0] * w[2]
            if ny <= 0:
                bad += 1
        check(f"{grp} faces up", bad == 0, f"{bad} downward triangles")

    # The ceiling curves, because it is a section of a rotating hull.
    ceil = [v[i][1] for tri in
            [t[k] for k in range(len(t)) if g[k] == "bay_ceiling"] for i in tri]
    check("the ceiling is an arc, not a flat soffit",
          max(ceil) - min(ceil) > 1.0,
          f"{max(ceil) - min(ceil):.2f} m of camber")
    check("the ceiling clears the girders",
          min(ceil) >= BAY_H_M - 1e-9, f"{min(ceil):.2f} vs {BAY_H_M}")

    # Lamps hang BELOW the girders they hang from, and above head height.
    lamp_y = [v[i][1] for tri in
              [t[k] for k in range(len(t)) if g[k] == "bay_lamp"] for i in tri]
    check("floodlights hang below the girders",
          max(lamp_y) <= BAY_H_M - GIRDER_D_M + 1e-9,
          f"top of lamp {max(lamp_y):.2f}")
    check("floodlights clear a standing person",
          min(lamp_y) > DOCK_WORKER_H_M * 2, f"{min(lamp_y):.2f} m")

    # Every ledge course must be reachable from the one below it: a 2.2 m rise
    # with a 3.4 m run is a stair, a 2.2 m rise with no run is a wall.
    check("ledge courses are climbable, not a cliff",
          LEDGE_RUN_M > LEDGE_RISE_M, f"rise {LEDGE_RISE_M} run {LEDGE_RUN_M}")
    check("the ledges do not meet in the middle",
          LEDGE_COURSES * LEDGE_RUN_M * 2 < BAY_W_M,
          f"{LEDGE_COURSES * LEDGE_RUN_M * 2:.1f} m of ledge in a "
          f"{BAY_W_M} m bay")

    # Placement: 24 bays must tile the circle without overlapping.
    #
    # This was `abs(BAY_COUNT * bay_pitch_deg() - 360) < 1e-9`, and
    # `bay_pitch_deg()` returns `360.0 / BAY_COUNT`. That is x * (360/x) == 360,
    # which is true for every value of x including the wrong ones -- an
    # algebraic identity restating its own input, the third of this family in
    # the project. It is replaced by a test on the PLACED GEOMETRY: build every
    # bay, take the angle each one actually landed at, and check the gaps
    # between consecutive bays are equal and close the circle. That can fail.
    angles = sorted(bay_angle_deg(i) % 360.0 for i in range(BAY_COUNT))
    gaps = [(angles[(i + 1) % BAY_COUNT] - angles[i]) % 360.0
            for i in range(BAY_COUNT)]
    check(f"{BAY_COUNT} placed bays tile the circle evenly",
          len(set(round(g, 9) for g in gaps)) == 1
          and abs(sum(gaps) - 360.0) < 1e-9,
          f"gaps {sorted(set(round(g, 3) for g in gaps))}")
    check("no two bays are placed at the same angle",
          len(set(round(a, 9) for a in angles)) == BAY_COUNT)

    r0 = bay_radius(schema, profile)
    arc = 2.0 * math.pi * r0 / BAY_COUNT
    check("a bay fits the arc it is allotted", arc > BAY_W_M,
          f"{arc:.1f} m of arc for a {BAY_W_M} m bay at r={r0:.1f}")
    # And that the bays do not merely fit their slices but leave hull between
    # them. Two bays sharing a wall is not 24 bays, it is one annulus, and the
    # "fits" test above passes right up to the moment they touch.
    check("there is hull structure between neighbouring bays",
          arc - BAY_W_M >= BAY_W_M * 0.25,
          f"{arc - BAY_W_M:.1f} m of hull between {BAY_W_M} m bays")

    # Placed geometry must sit inside the hull and face the axis.
    pv, pt, _pg = place_bay(0, schema, profile)
    radii = [math.hypot(q[0], q[1]) for q in pv]
    check("the placed bay sits inside Blue's hull",
          max(radii) <= r0 + 1e-6, f"max radius {max(radii):.1f} vs {r0:.1f}")
    check("the bay deck is the outermost surface in the bay",
          abs(max(radii) - r0) < 1e-6)

    check("bays are numbered and 17 exists", BAY_COUNT >= 17)

    # Both canon numbers are read from the schema rather than retyped, so these
    # cannot drift silently -- but a later edit could reintroduce a literal, and
    # then the module would look sourced and not be. Asserting the tie is what
    # makes the derivation load-bearing rather than merely tidy.
    check("the bay count is the schema's, not a literal",
          BAY_COUNT == int(schema["docking"]["docking_bay"]["count"]),
          f"{BAY_COUNT} vs schema "
          f"{schema['docking']['docking_bay']['count']}")
    check("the bay width is the schema's cobra_bay width",
          abs(BAY_W_M - _schema_bay_width_m()) < 1e-9,
          f"{BAY_W_M} vs schema {_schema_bay_width_m()}")
    # 24 docking bays and 28 cobra bays are DIFFERENT SYSTEMS, both listed on
    # the same sheet. If a future edit ever collapses them into one number this
    # is what says so.
    check("docking bays are not the cobra bays",
          BAY_COUNT != sum(c["count"] for c in schema["components"]
                           if c["id"] == "cobra_bay"),
          "24 bays and 28 launch tubes -- see C-002")

    # --- THE BAY HAS AN OUTSIDE ------------------------------------------
    # `docs/volume-audit.md` §5.1: "the 24 docking bays get nothing ... an
    # interior with no exterior". This module could build a perfect bay behind
    # a hull with no hole in it, and every assertion above would still pass --
    # which is exactly what happened for four sessions. These three are the
    # ones that could not.
    import aperture as _ap                                    # noqa: PLC0415
    aps = _ap.docking_bay_apertures(schema, profile)
    check("every bay has an aperture in the hull", len(aps) == BAY_COUNT,
          f"{len(aps)} mouths for {BAY_COUNT} bays")
    a0 = aps[0]
    check("the aperture is the bay's own mouth, not a hole near it",
          abs((a0.a1 - a0.a0) * a0.r_out - BAY_W_M) < 1e-9
          and abs(a0.r_out - r0) < 1e-9
          and abs((a0.r_out - a0.r_in) - (BAY_H_M + BAY_W_M * 0.10)) < 1e-9,
          f"{(a0.a1 - a0.a0) * a0.r_out:.2f} x "
          f"{a0.r_out - a0.r_in:.2f} m at r={a0.r_out:.1f}")
    check("the mouth is at the fore end, where the hull can be cut",
          abs(a0.z_mouth - mouth_z_m()) < 1e-9
          and a0.z_mouth < a0.z_out < a0.z_in,
          f"mouth {a0.z_mouth:.0f}, hull crossed at {a0.z_out:.1f} "
          f"and {a0.z_in:.1f}")

    # --- AND MOST OF IT IS STILL OUTSIDE THAT HULL -----------------------
    # A ratchet, not a pass. The register addresses a 140 m bay at z 7115 and
    # the docking sphere is only wide enough to contain a 254.2 m deck over
    # 58 m of that. This is `tools/cutaway.py`'s "14 of 118 locations are
    # addressed OUTSIDE THE HULL" on this location, measured. The fix belongs
    # to whoever owns directory.py -- shorten the footprint or move z -- and
    # until then this asserts the number does not get WORSE, and prints it so
    # it cannot be forgotten.
    prof = profile["profile"] if isinstance(profile, dict) else profile
    place = _directory.by_key("docking_bays")
    z_lo = place["z_m"] - place["footprint"][1] / 2.0
    inside = [s for s in prof
              if z_lo <= s["z_m"] <= mouth_z_m()
              and s["radius_m"] >= r0 + it.HULL_SKIN_M]
    total = [s for s in prof if z_lo <= s["z_m"] <= mouth_z_m()]
    frac = len(inside) / len(total)
    check("the addressed bay is no further outside the hull than it was",
          frac >= 0.40,
          f"{frac * 100:.1f}% of the bay's {place['footprint'][1]:.0f} m is "
          f"inside a hull wide enough for a {r0:.1f} m deck "
          f"({len(inside)} of {len(total)} profile samples) -- KNOWN DEFECT, "
          f"see the directory.py note in station/aperture.py")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
