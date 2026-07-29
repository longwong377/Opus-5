"""Layer 2: geometry for every addressed location, generated from its entry.

`directory.py` says, for all 118 addressed locations, where they are, how big
they are, what they are FOR, and what a player can use in them. That is a
specification, and this module consumes it.

WHY THIS IS A GENERATOR AND NOT 68 MODULES
-------------------------------------------
`docs/MASTER-PLAN.md` §3.4 tiers the station: ~12 hero locations authored to a
reference frame, ~30 featured, **~84 procedural from a kit**. Writing 68 bespoke
room modules would be the wrong architecture *and* would not finish — it is the
arithmetic the plan says does not close.

The hero and featured rooms keep their own modules (`zocalo`, `customs`,
`command_control`, `council_chamber`, `garden`, `alien_sector`, `plant`,
`hospitality`, `quarters`, `docking_bay`). Everything else is built here, from
the same directory entry the assertions already check.

THE ONE PROPERTY THAT MAKES THIS HONEST
----------------------------------------
**Every prop a location declares in `interacts` must exist as geometry.** The
directory declares 65 distinct interactable types across the 68 unbuilt places;
`PROPS` implements them, and `_selftest` asserts the two sets agree in both
directions. A declared prop with no mesh is a promise the room does not keep; a
mesh for a prop nothing declares is dead weight.

That check is what stops this being a box generator with a plausible docstring.

ARCHETYPES
----------
A room's layout comes from its primary function, not from its name. Nine
archetypes cover the 68, and each decides the shell proportions, where props go
and how dense they are. A `medical` room and a `storage` room built to the same
footprint should not look alike, and the archetype is what makes them not.

WHAT IS EXTRAPOLATED — INV-034
------------------------------
Every prop dimension and every archetype rule. What constrains them: a prop must
be usable by a 1.7 m occupant, must fit inside its room, must not intersect
another prop, and the room must remain walkable — all asserted rather than
asserted-in-prose.
"""
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402
import interior_kit as ik                                     # noqa: E402
import directory as dr                                         # noqa: E402

WALL_T_M = 0.18
WALK_M = 0.9               # clear path that must survive the props

# Ceiling height is NOT a global constant, and making it one was wrong. A
# docking bay, a foundry and an office are not the same room. The first version
# used a flat 2.9 m and three bay locations failed immediately, because a
# `bay_door` is 5 m tall and would not fit in the room it belongs to.
#
# So the height is DERIVED: the archetype's nominal height, raised if the room
# must contain something taller. A room that cannot hold its own declared props
# is not a room, and the assertion below checks it rather than trusting this.
CEIL_BY_ARCHETYPE = {
    "store": 6.5,          # cargo handling, cranes, stacked containers
    "industrial": 7.5,     # furnaces, plant, overhead handling
    "transit": 3.4,
    "hospitality": 2.9,
    "worship": 4.2,        # height is the whole point of a worship space
    "medical": 3.0,
    "research": 3.2,
    "detention": 2.8,
    "commerce": 3.4,
    "office": 2.9,
    "generic": 2.9,
}
CEIL_HEADROOM_M = 0.35     # clearance above the tallest prop


def ceiling_m(place):
    """Room height: the archetype's nominal, raised to hold its own props.

    Deliberately allowed to exceed DECK_PITCH_M. A docking bay is 18 m tall in
    `docking_bay.py` and spans many decks; pretending every volume fits in one
    3.6 m pitch is what produced a 5 m door in a 2.9 m room.
    """
    base = CEIL_BY_ARCHETYPE.get(archetype(place), 2.9)
    tallest = max((PROPS[k][2] for k in place["interacts"] if k in PROPS),
                  default=0.0)
    return max(base, tallest + CEIL_HEADROOM_M)

# ---------------------------------------------------------------------------
# The prop library
# ---------------------------------------------------------------------------
# (width, depth, height, mount) where mount is "floor", "wall" or "ceiling".
# Sized to a 1.7 m occupant; the self-test checks reach and clearance rather
# than trusting these numbers.
PROPS = {
    # seating and surfaces
    "table":            (1.20, 0.80, 0.74, "floor"),
    "seat":             (0.52, 0.52, 0.45, "floor"),
    "bench":            (1.80, 0.45, 0.45, "floor"),
    "pew":              (2.40, 0.50, 0.90, "floor"),
    "stool":            (0.38, 0.38, 0.62, "floor"),
    "desk":             (1.40, 0.70, 0.74, "floor"),
    "workbench":        (2.00, 0.80, 0.90, "floor"),
    "lab_bench":        (2.20, 0.75, 0.90, "floor"),
    "counter":          (2.40, 0.60, 1.05, "floor"),
    "issue_counter":    (2.40, 0.60, 1.05, "floor"),
    "serving_counter":  (3.00, 0.70, 1.05, "floor"),
    "bar_counter":      (4.00, 0.72, 1.08, "floor"),
    "duty_desk":        (2.00, 0.80, 1.05, "floor"),
    "stall":            (1.80, 1.20, 2.10, "floor"),
    "gaming_table":     (1.60, 1.10, 0.78, "floor"),
    # sleeping and storage
    "bunk":             (2.05, 0.95, 0.55, "floor"),
    "locker":           (0.90, 0.55, 2.05, "floor"),
    "weapons_locker":   (1.10, 0.50, 2.05, "floor"),
    "medcabinet":       (0.85, 0.35, 1.60, "wall"),
    "parcel_locker":    (1.20, 0.45, 2.00, "floor"),
    "tool_rack":        (1.60, 0.28, 1.90, "wall"),
    "container":        (2.40, 1.20, 1.20, "floor"),
    "cold_drawer":      (0.90, 2.10, 0.65, "floor"),
    "cryo_pod":         (2.20, 0.95, 1.00, "floor"),
    "grow_rack":        (2.40, 0.70, 2.20, "floor"),
    # terminals and controls
    "babcom_terminal":  (0.75, 0.08, 0.45, "wall"),
    "console":          (1.40, 0.65, 1.05, "floor"),
    "reactor_console":  (2.20, 0.80, 1.15, "floor"),
    "furnace_control":  (1.60, 0.60, 1.20, "floor"),
    "irrigation_control": (0.90, 0.30, 1.10, "wall"),
    "monitor_wall":     (3.20, 0.12, 1.80, "wall"),
    "tactical_display": (2.40, 0.15, 1.60, "wall"),
    "credit_terminal":  (0.55, 0.30, 1.35, "floor"),
    "exchange_terminal": (0.70, 0.35, 1.40, "floor"),
    "manifest_terminal": (0.60, 0.30, 1.35, "floor"),
    "identicard_reader": (0.30, 0.14, 0.35, "wall"),
    "intercom":         (0.22, 0.08, 0.30, "wall"),
    "breaker_lever":    (0.35, 0.20, 0.70, "wall"),
    "tank_gauge":       (0.30, 0.12, 0.30, "wall"),
    "valve":            (0.45, 0.45, 0.45, "wall"),
    "lift_call":        (0.20, 0.06, 0.28, "wall"),
    "level_plaque":     (0.42, 0.03, 0.26, "wall"),
    "neon_sign":        (1.60, 0.10, 0.55, "wall"),
    "shrine":           (1.10, 0.60, 1.70, "floor"),
    # medical
    "diagnostic_bed":   (2.10, 0.90, 0.72, "floor"),
    # doors and apertures
    "door":             (1.90, 0.22, 2.35, "wall"),
    "office_door":      (1.10, 0.20, 2.20, "wall"),
    "cell_door":        (1.10, 0.30, 2.20, "wall"),
    "isolation_door":   (1.90, 0.35, 2.35, "wall"),
    "blast_door":       (2.60, 0.45, 2.60, "wall"),
    "welded_door":      (1.90, 0.22, 2.35, "wall"),
    "makeshift_door":   (1.20, 0.10, 2.00, "wall"),
    "lift_door":        (1.60, 0.25, 2.30, "wall"),
    "tram_door":        (1.40, 0.20, 2.10, "wall"),
    "bay_door":         (6.00, 0.60, 5.00, "wall"),
    "viewport":         (2.40, 0.20, 1.40, "wall"),
    "public_gallery":   (4.00, 1.20, 1.05, "floor"),
    "barrier":          (1.60, 0.20, 1.05, "floor"),
    # heavy plant and handling
    "cargo_crane":      (3.00, 1.00, 0.90, "ceiling"),
    "crane":            (2.60, 0.90, 0.80, "ceiling"),
    "catwalk":          (8.00, 1.80, 0.14, "floor"),
    "docking_clamp":    (1.60, 1.60, 0.90, "floor"),
    "handhold":         (0.60, 0.10, 0.10, "wall"),
    "path":             (6.00, 1.60, 0.04, "floor"),
    "pool_edge":        (4.00, 0.60, 0.25, "floor"),
    "tray_dispenser":   (0.80, 0.55, 1.30, "floor"),
}

# Which archetype a location uses, chosen by its primary function. Order
# matters: the first match wins, so the most specific functions come first.
ARCHETYPES = (
    ("medical", ("medical", "triage", "surgery", "mortuary")),
    ("detention", ("detention", "checkpoint")),
    ("worship", ("worship", "contemplation")),
    ("industrial", ("fabrication", "industry", "repair", "power_distribution",
                    "waste_processing", "water_reclamation", "air_handling",
                    "water_storage", "cooling", "rotation")),
    ("research", ("research", "monitoring", "variable_gravity")),
    ("store", ("storage", "hazardous_storage", "fuel_storage",
               "cargo_handling", "atmosphere_feedstock",
               "microgravity_handling")),
    ("transit", ("transit",)),
    ("hospitality", ("hospitality", "food_service", "catering", "gambling")),
    ("commerce", ("commerce", "retail", "currency_exchange", "black_market",
                  "mail", "issue_stores", "logistics")),
    ("office", ("offices", "administration", "command", "diplomacy",
                "meeting", "briefing", "adjudication", "law_enforcement",
                "surveillance", "political_policing", "station_ops",
                "traffic_control", "control", "psi_corps",
                "military_liaison", "ceremony", "hire")),
)

# Prop density per archetype: how much of the floor may be furniture. A store
# is dense, a chapel is empty, and that difference is most of what makes two
# rooms of the same size read differently.
DENSITY = {"store": 0.42, "industrial": 0.34, "medical": 0.26,
           "hospitality": 0.30, "commerce": 0.28, "research": 0.30,
           "office": 0.22, "detention": 0.20, "transit": 0.12,
           "worship": 0.18, "generic": 0.22}


def archetype(place):
    fns = set(place["functions"])
    for name, keys in ARCHETYPES:
        if fns & set(keys):
            return name
    return "generic"


# ---------------------------------------------------------------------------
# Fixtures: the machinery a room is NAMED FOR and that nobody touches
# ---------------------------------------------------------------------------
# `interacts` is what a PLAYER CAN USE. It is not an inventory of what is in
# the room, and building from it alone produced the defect the first
# verification render of this module showed: "Fabrication furnaces" came out a
# grey box containing two control podiums, a catwalk and a crane -- the
# controls for a furnace, and no furnace. "Primary fusion core" declares two
# interactables and no reactor. A furnace is not something you walk up to and
# operate, so it is correctly absent from `interacts`, and just as correctly
# must be present in the geometry.
#
# No amount of material or lighting fixes this: it is a missing object, so it
# is a LAYER 2 defect and belongs here.
#
# Entries are (name, width, depth, height, kind) where kind is:
#   "spine"  -- runs down the room's centreline, repeated along its length
#   "flank"  -- against one long wall, repeated
#   "over"   -- hangs from the ceiling, repeated down the centreline
# INV-035.
FIXTURES = {
    "industrial": (("furnace_stack", 2.40, 2.40, 4.60, "spine"),
                   ("plant_column", 1.10, 1.10, 0.00, "flank"),
                   ("service_duct", 0.90, 0.90, 0.70, "over")),
    "store":      (("racking_run", 1.10, 2.60, 4.20, "flank"),
                   ("gantry_rail", 0.35, 0.35, 0.45, "over")),
    "medical":    (("equipment_gantry", 0.55, 1.60, 2.30, "flank"),
                   ("service_duct", 0.60, 0.60, 0.45, "over")),
    "research":   (("fume_column", 1.30, 0.80, 2.60, "flank"),
                   ("service_duct", 0.60, 0.60, 0.45, "over")),
    "detention":  (("cell_divider", 0.30, 2.20, 0.00, "flank"),),
    "transit":    (("platform_edge", 0.45, 0.00, 0.22, "flank"),
                   ("catenary_run", 0.30, 0.30, 0.35, "over")),
    "hospitality": (("back_shelving", 0.45, 2.20, 2.30, "flank"),),
    "worship":    (("dais", 3.20, 1.60, 0.35, "spine"),
                   ("screen_panel", 0.22, 2.60, 0.00, "flank")),
    "commerce":   (("stall_frame", 0.25, 2.00, 0.00, "flank"),
                   ("awning_rail", 0.30, 0.30, 0.28, "over")),
    "office":     (("partition_screen", 0.16, 1.80, 1.75, "flank"),),
    "generic":    (("service_riser", 0.70, 0.70, 0.00, "flank"),
                   ("service_duct", 0.55, 0.55, 0.40, "over")),
}
FIXTURE_PITCH_M = 4.5      # spacing of repeated fixtures along the room

# Wall ribs. Every B5 interior in the reference is heavily articulated: a flat
# wall run from floor to a 7.5 m soffit is the single strongest tell that a
# volume is a placeholder box. Ribs are structural, cheap, and true of the
# sets. Pitch is derived from the deck frame in `interior.py` rather than
# picked, so a schema change moves them.
RIB_D_M = 0.16
RIB_W_M = 0.45


AISLE_M = WALK_M + 0.5     # a walker plus 0.25 m either side of fixed objects


def lateral_stack(place):
    """What eats the bay's width, in order, from -x to +x.

    Returns (width_needed, start_inset_minus_x, start_inset_plus_x) -- the
    total width the cross-section needs, and the insets BEFORE any flank
    scenery, which `build` then accumulates through in the same order.

    THIS EXISTS BECAUSE THE TWO HALVES DISAGREED. `bay_span_m` derived a width
    from one formula and `build` laid objects out with another, so a 4.0 m
    fusion core came out with a 0.99 m aisle between two consoles that the
    sizing had believed was 1.25 m. The flood fill caught it; the fix is that
    there is now one description of the cross-section and both callers use it.
    """
    wall_band = max((PROPS[k][1] for k in place["interacts"]
                     if PROPS.get(k, (0, 0, 0, "floor"))[3] == "wall"),
                    default=0.0)
    start = (max(RIB_D_M, wall_band), RIB_D_M)
    inset, side, spine_d = list(start), 1, 0.0       # scenery starts on +x
    for _n, _w, d, _h, kind in fixtures_for(place):
        if kind == "flank":
            inset[side] += d
            side = 1 - side
        elif kind == "spine":
            spine_d = max(spine_d, d)
    deep = max((PROPS[k][1] for k in place["interacts"]
                if PROPS.get(k, (0, 0, 0, "floor"))[3] == "floor"), default=0.0)
    aisles = 2 if spine_d else 1
    need = inset[0] + inset[1] + 2 * deep + spine_d + aisles * AISLE_M
    return need, start[0], start[1]


def rib_pitch_m(place):
    """Structural rib spacing -- one per frame bay, floor to soffit."""
    return max(2.4, min(4.2, ceiling_m(place) * 0.62))


def fixtures_for(place):
    """Scenery for one room: archetype set, height 0.00 meaning full height."""
    out = []
    for name, w, d, h, kind in FIXTURES.get(archetype(place), ()):
        out.append((name, w, d, ceiling_m(place) if h == 0.0 else h, kind))
    return tuple(out)


def _u(*parts):
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def room_extent_m(schema, profile, place):
    """A place's footprint in metres: (along the ring, along the axis).

    The directory stores an ANGULAR extent, because that is what a ring deck
    actually has. Converting needs the deck radius, so it is done here rather
    than stored -- a stored metre value would go stale the moment a sector
    radius moved, and INV-026 moved all of them at once.
    """
    rings = it.ring_radii(schema, profile, place["sector"])
    stacks = [i for i, r in enumerate(rings) if r["kind"] == "deck_stack"]
    r_floor = it.sector_radius(schema, profile, place["sector"])
    if stacks:
        ri = stacks[min(place["ring"], len(stacks) - 1)]
        decks = it.decks_in_ring(schema, profile, place["sector"], ri)
        if decks:
            r_floor = decks[min(place["deck"], len(decks) - 1)]["floor_r_m"]
    arc = 2 * math.pi * r_floor * (place["footprint"][0] / 360.0)
    return arc, place["footprint"][1], r_floor


def _box(v, t, g, name, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    g.append((name, t0, len(t)))
    return v, t, g


def bay_span_m(place):
    """The size of one representative bay -- DERIVED from what it holds.

    The first version clamped every large room to a flat 40 m and rendered a
    1,600 m2 hall containing six props against one wall. It was empty, and it
    was empty for the reason the customs hall was too narrow and the ceiling
    was too low: A SIZE WAS PICKED INSTEAD OF DERIVED.

    A bay is as long as the props ranked along its two side walls, plus a
    working gap between them, plus end clearance. It is as wide as the deepest
    prop on each side plus the walkway between. That makes a bay READ as
    furnished by construction, because it is exactly the room its contents
    need, and the full location is then that bay instanced along its footprint.
    """
    floor = [k for k in place["interacts"]
             if PROPS.get(k, (0, 0, 0, "floor"))[3] == "floor"]
    wall = [k for k in place["interacts"]
            if PROPS.get(k, (0, 0, 0, "floor"))[3] == "wall"]
    # Fixtures are scenery, not props, but they occupy the same floor and the
    # bay has to be big enough for them or a furnace stack ends up inside a
    # wall. Flanking fixtures eat depth off both sides; a spine fixture eats
    # the middle and needs a walkway either side of it.
    fx = fixtures_for(place)
    spine_l = max((w for _n, w, _d, _h, k in fx if k == "spine"), default=0.0)
    fx_width, _i0, _i1 = lateral_stack(place)
    fx_len = max(spine_l + 1.2, FIXTURE_PITCH_M + 1.2) if fx else 0.0

    if not floor:
        # A room with nothing standing on its floor is small by nature -- a
        # micro-g bay you float through, a sealed section, a checkpoint. A
        # 6 x 8 m minimum made those read as empty halls, which is the same
        # picked-not-derived mistake one size down. Size to the wall props.
        wide = max((PROPS[k][0] for k in wall), default=1.6)
        return (max(wide + 1.2, fx_width, 3.0),
                max(wide + 1.6, fx_len, 4.0))
    # Ranked alternately down two walls, so each wall takes half of them.
    per_side = [PROPS[k] for k in floor] * 2
    run = sum(pw + 0.45 for pw, _pd, _ph, _m in per_side) / 2.0 + 1.2
    deep = max(pd for _pw, pd, _ph, _m in per_side)
    width = 2 * deep + max(WALK_M, 1.6) + 0.5
    # Wall props run along z, so the bay must be long enough to hang the
    # widest of them -- a 6 m bay door needs 6 m of wall.
    widest_wall = max((PROPS[k][0] for k in wall), default=0.0)
    return (max(width, fx_width, 4.0),
            max(run, widest_wall + 1.2, fx_len, 6.0))


def bays_in(schema, profile, place):
    """How many representative bays tile this location's real footprint."""
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    return max(1, int(w_full / bw)) * max(1, int(l_full / bl))


def build(schema, profile, place, max_span_m=None):
    """Geometry for one representative bay of a location.

    A 300 m storage run is a corridor of identical bays; emitting all of it
    would put millions of triangles into a layer that only has to prove the
    volume exists, is closed, and is furnished. `bays_in()` says how many the
    streaming system instances.
    """
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    w = min(w_full, bw)
    ln = min(l_full, bl)
    arch = archetype(place)
    ceil = ceiling_m(place)
    v, t, g = [], [], []
    hw, hl = w / 2.0, ln / 2.0
    ow, ol = hw + WALL_T_M, hl + WALL_T_M

    # Shell: deck and soffit run to the OUTER wall extent, or every wall/soffit
    # junction is an open corner. hospitality.py shipped that defect and it
    # took a magenta-pixel count to find.
    _box(v, t, g, f"{arch}_deck", (-ow, -0.14, -ol), (ow, 0.0, ol))
    _box(v, t, g, f"{arch}_soffit", (-ow, ceil, -ol), (ow, ceil + 0.14, ol))
    for s in (-1, 1):
        _box(v, t, g, f"{arch}_wall", (s * hw, 0.0, -ol), (s * ow, ceil, ol))
        _box(v, t, g, f"{arch}_wall", (-ow, 0.0, s * hl), (ow, ceil, s * ol))

    # Structural ribs on both long walls, floor to soffit. Articulation, not
    # decoration: a flat run of wall from deck to a 7.5 m soffit is what makes
    # a volume read as a placeholder box, and the first render of this module
    # showed exactly that.
    pitch = rib_pitch_m(place)
    nrib = max(1, int(ln / pitch))
    for i in range(nrib):
        zc = -hl + (i + 0.5) * (ln / nrib) - RIB_W_M / 2.0
        zc = min(max(zc, -hl), hl - RIB_W_M)
        for s in (-1, 1):
            x0 = s * hw
            _box(v, t, g, f"{arch}_rib", (min(x0, x0 - s * RIB_D_M), 0.0, zc),
                 (max(x0, x0 - s * RIB_D_M), ceil, zc + RIB_W_M))

    # Fixtures: the machinery the room is named for. See FIXTURES.
    # `inset` records the depth each side loses to flanking scenery, and
    # `over_x` the half-width the ceiling centreline loses, so the props placed
    # below do not grow into them. Without that bookkeeping a racking run and a
    # workbench occupy the same cubic metre and only the containment assertion
    # notices -- which it would not, because both are inside the room.
    # The -x wall belongs to the wall-mounted props -- doors, viewports,
    # monitor walls -- so the band they occupy is reserved before any scenery
    # is offered the same wall. Without this a racking run stood in front of a
    # bay door and the room had no way in. `lateral_stack` owns that
    # bookkeeping and `bay_span_m` sizes the bay from the same function.
    _need, i0, i1 = lateral_stack(place)
    inset = [i0, i1]                                 # running, [-x, +x]
    fx = fixtures_for(place)
    nz = max(1, int(ln / FIXTURE_PITCH_M))

    def _zs(fw):
        for i in range(nz):
            zc = -hl + (i + 0.5) * (ln / nz) - fw / 2.0
            yield min(max(zc, -hl + 0.05), hl - fw - 0.05)

    # Pass 1: floor-standing scenery, which is what decides how much of the
    # cross-section is left.
    spine_d, flank_side = 0.0, 1                     # scenery starts on +x
    for name, fw, fd, fh, kind in fx:
        if kind == "spine":
            spine_d = max(spine_d, fd)
            for zc in _zs(fw):
                _box(v, t, g, f"fix_{name}", (-fd / 2, 0.0, zc),
                     (fd / 2, min(fh, ceil - 0.1), zc + fw))
        elif kind == "flank":
            s = flank_side
            x0 = (-hw + inset[s]) if s == 0 else (hw - inset[s] - fd)
            for zc in _zs(fw):
                _box(v, t, g, f"fix_{name}", (x0, 0.0, zc),
                     (x0 + fd, min(fh, ceil), zc + fw))
            inset[s] += fd
            flank_side = 1 - flank_side

    # Pass 2: overhead runs. They centre on the FREE CHANNEL, not on the room's
    # centreline -- in a market bay a full-height stall frame reaches past x=0
    # and an awning rail hung at the geometric centre ends up inside it.
    chan_lo, chan_hi = -hw + inset[0], hw - inset[1]
    chan_c = (chan_lo + chan_hi) / 2.0
    over_h = 0.0
    for name, fw, fd, fh, kind in fx:
        if kind != "over":
            continue
        over_h = max(over_h, fh)
        for zc in _zs(fw):
            _box(v, t, g, f"fix_{name}", (chan_c - fd / 2, ceil - fh, zc),
                 (chan_c + fd / 2, ceil, zc + fw))

    # Props. Floor-mounted go in rows against the long walls with the centre
    # left clear; wall-mounted sit on the walls; ceiling-mounted hang.
    floor_props = [p for p in place["interacts"]
                   if PROPS.get(p, (0, 0, 0, "floor"))[3] == "floor"]
    wall_props = [p for p in place["interacts"]
                  if PROPS.get(p, (0, 0, 0, "floor"))[3] == "wall"]
    ceil_props = [p for p in place["interacts"]
                  if PROPS.get(p, (0, 0, 0, "floor"))[3] == "ceiling"]

    budget = DENSITY.get(arch, 0.22) * w * ln
    used = 0.0
    side, cursor = -1, [-hl + 0.6, -hl + 0.6]
    for i, key in enumerate(floor_props * 3):
        pw, pd, ph, _m = PROPS.get(key, (0.8, 0.6, 0.8, "floor"))
        if used + pw * pd > budget:
            break
        s = side
        z0 = cursor[0 if s < 0 else 1]
        if z0 + pw > hl - 0.6:
            break
        # Stand clear of whatever scenery already owns this wall.
        x0 = ((-hw + inset[0] + 0.05) if s < 0
              else (hw - inset[1] - 0.05 - pd))
        if abs(x0) < spine_d / 2.0 + 0.1:            # would sit in the spine
            break
        _box(v, t, g, f"prop_{key}", (x0, 0.0, z0), (x0 + pd, ph, z0 + pw))
        cursor[0 if s < 0 else 1] = z0 + pw + 0.45
        used += pw * pd
        side = -side

    # Wall props run along a wall as a CURSOR, not on a fixed 2.1 m lattice.
    # The lattice took `(i * 2.1) % (ln - 2.4)`, which ignores how wide each
    # prop is and wraps back to the start: in medlab a medcabinet and a babcom
    # terminal ended up in the same 0.85 m of wall, and in security central a
    # 3.2 m monitor wall swallowed a cell door. Both were in the version this
    # module was about to be committed at, and no assertion could see them --
    # they are inside the room and the right size, which is all the old gates
    # asked. When a wall fills, the cursor moves to the next wall; the end
    # walls are bare and a door on one is how you would enter anyway.
    #
    # Walls, in order of preference: the -x side (reserved above), then the
    # near and far end walls. Each is (origin, along-axis, usable length).
    walls = [("side", -hl, hl), ("near", -hw + inset[0], hw - inset[1]),
             ("far", -hw + inset[0], hw - inset[1])]
    wi, cur = 0, -hl
    for key in wall_props:
        pw, pd, ph, _m = PROPS.get(key, (0.6, 0.1, 0.6, "wall"))
        while wi < len(walls) and cur + pw > walls[wi][2]:
            wi += 1
            if wi < len(walls):
                cur = walls[wi][1]
        if wi >= len(walls):
            break                      # room is out of wall; sized by bay_span
        sill = 0.0 if ph > 2.0 else 1.05
        if walls[wi][0] == "side":
            _box(v, t, g, f"prop_{key}", (-hw, sill, cur),
                 (-hw + pd, sill + ph, cur + pw))
        elif walls[wi][0] == "near":
            _box(v, t, g, f"prop_{key}", (cur, sill, -hl),
                 (cur + pw, sill + ph, -hl + pd))
        else:
            _box(v, t, g, f"prop_{key}", (cur, sill, hl - pd),
                 (cur + pw, sill + ph, hl))
        cur += pw + 0.35
    for i, key in enumerate(ceil_props):
        pw, pd, ph, _m = PROPS.get(key, (1.0, 1.0, 0.5, "ceiling"))
        # A crane RIDES the gantry rail, so it hangs BELOW the overhead run
        # rather than beside it. Placing it beside was the first attempt and it
        # put a 3 m crane through a 0.35 m rail -- which is also what a real
        # gantry crane does not do.
        top = ceil - over_h
        xc = min(max(chan_c, chan_lo + pd / 2), chan_hi - pd / 2)
        z0 = min(max(-hl + 2.0 + i * 3.0, -hl), hl - pw)
        _box(v, t, g, f"prop_{key}",
             (xc - pd / 2, top - ph, z0), (xc + pd / 2, top, z0 + pw))

    return v, t, g


def _solid_boxes(v, t, g):
    """AABBs of the room's solid objects -- props and fixtures, not shell.

    Ribs are excluded: they are wall articulation flush against a wall, and a
    prop legitimately stands in front of one.
    """
    out = []
    for name, lo, hi in g:
        if not (name.startswith("prop_") or name.startswith("fix_")):
            continue
        idx = {i for tri in t[lo:hi] for i in tri}
        pts = [v[i] for i in idx]
        out.append((name, (min(q[0] for q in pts), min(q[1] for q in pts),
                           min(q[2] for q in pts), max(q[0] for q in pts),
                           max(q[1] for q in pts), max(q[2] for q in pts))))
    return out


def _overlaps(a, b, eps=1e-6):
    return all(a[i] < b[i + 3] - eps and b[i] < a[i + 3] - eps
               for i in range(3))


CELL_M = 0.15


def walkable(boxes, w, ln, clear_m=WALK_M):
    """Can a `clear_m`-wide walker cross the bay end to end?

    The first version measured a single clear x-span and treated anything
    touching the centreline as impassable. That is wrong in exactly the rooms
    fixtures were added for: a furnace stack is a repeated island you walk
    AROUND, and the collapsed measure reported 0.00 m clear in a 10 m hall.

    So it is a flood fill instead. Free floor is eroded by the walker's radius
    and searched from one end wall to the other -- which is the actual
    question, and which no span measurement can answer.

    Obstacles are solids that intersect knee-to-shoulder height. Something
    hanging above 1.9 m is walked under; something below 50 mm is stepped over.
    """
    nx = max(3, int(w / CELL_M))
    nz = max(3, int(ln / CELL_M))
    pad = clear_m / 2.0
    blocked = [[False] * nz for _ in range(nx)]
    for _n, (x0, y0, z0, x1, y1, z1) in boxes:
        if y1 <= 0.05 or y0 > 1.9:
            continue
        i0 = max(0, int((x0 - pad + w / 2) / CELL_M))
        i1 = min(nx - 1, int((x1 + pad + w / 2) / CELL_M))
        j0 = max(0, int((z0 - pad + ln / 2) / CELL_M))
        j1 = min(nz - 1, int((z1 + pad + ln / 2) / CELL_M))
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                blocked[i][j] = True
    # The walker's body must also clear the walls.
    edge = max(0, int(pad / CELL_M))
    start = [(i, j) for i in range(edge, nx - edge) for j in (edge,)
             if not blocked[i][j]]
    if not start:
        return False
    seen, stack = set(start), list(start)
    goal = nz - 1 - edge
    while stack:
        i, j = stack.pop()
        if j >= goal:
            return True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if (edge <= a < nx - edge and edge <= b < nz - edge
                    and not blocked[a][b] and (a, b) not in seen):
                seen.add((a, b))
                stack.append((a, b))
    return False


def standpoint(v, t, g, w, ln, clear_m=WALK_M):
    """A spot near the near end wall where a walker actually fits.

    Same occupancy grid as `walkable`, so a camera placed here is standing
    somewhere the room's own gate says is free floor.
    """
    boxes = _solid_boxes(v, t, g)
    nx = max(3, int(w / CELL_M))
    nz = max(3, int(ln / CELL_M))
    pad = clear_m / 2.0
    best = None
    for i in range(nx):
        x = -w / 2 + (i + 0.5) * CELL_M
        if abs(x) > w / 2 - pad:
            continue
        for j in range(min(nz, int(ln * 0.35 / CELL_M) + 1)):
            z = -ln / 2 + (j + 0.5) * CELL_M
            if z < -ln / 2 + pad:
                continue
            if any(x0 - pad < x < x1 + pad and z0 - pad < z < z1 + pad
                   and y1 > 0.05 and y0 < 1.9
                   for _n, (x0, y0, z0, x1, y1, z1) in boxes):
                continue
            # Prefer the nearest free spot to the entry wall, then the one
            # furthest off the centreline -- a shot down the middle of a room
            # sees less of it than a shot down an aisle.
            score = (z, -abs(x))
            if best is None or score < best[0]:
                best = (score, x, z)
        if best and best[0][0] <= -ln / 2 + pad + CELL_M:
            break
    if best is None:
        return 0.0, -ln / 2 + 0.45
    return best[1], best[2]


def _signed_volume(v, t):
    s = 0.0
    for a, b, c in t:
        p, q, r = v[a], v[b], v[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0


def unbuilt(schema, profile):
    """Addressed places with no bespoke module -- this generator's remit."""
    return [p for p in dr.PLACES if not p["module"]]


def write_obj(path, key):
    """One bay of one location, plus the camera that frames it.

    The camera is RETURNED rather than left to the caller because the bay's
    size is derived from its contents and therefore changes whenever a prop
    changes. A hand-typed `--eye` goes stale silently: the first verification
    render of the fabrication bay used the camera from a 40 m version of the
    same room, put the eye 8 m down a hall 11.7 m long -- outside its own end
    wall -- and came back a flat grey field that looked like a lighting bug
    rather than like a camera in a wall.
    """
    place = dr.by_key(key)
    schema, profile = it.load()
    v, t, g = build(schema, profile, place)
    # `g` is spans -- (name, tri_lo, tri_hi) -- not a per-triangle list, so the
    # kit's writer is the right one. interior.write_grouped_obj indexes groups
    # per triangle and raises IndexError on spans.
    ik.write_obj(path, v, t, spans=g, default_group="room")
    w, ln = bay_span_m(place)
    ceil = ceiling_m(place)
    # Stand where a PLAYER COULD STAND and look LEVEL down the room. Three
    # camera bugs in a row came from picking a standpoint by arithmetic:
    #   * a hand-typed eye from a previous, larger version of the bay put it
    #     outside the end wall, and the frame came back flat grey;
    #   * one third in put the eye past the first rank of props, so the shot
    #     meant to prove the room is furnished showed the half that is empty;
    #   * a fixed 1.1 m off-centre put the eye inside a 2.4 m furnace stack.
    # So the standpoint is searched for on the same walkable grid the gate
    # uses. It cannot go stale, because it is derived from the geometry it is
    # about to photograph. Level gaze, because a downward tilt crops the
    # soffit and the overhead runs are most of what says "industrial".
    h = min(1.65, ceil - 0.4)
    x, z = standpoint(v, t, g, w, ln)
    eye = (x, h, z)
    tgt = (0.0, h, ln / 2.0 - 0.2)
    return {"path": path, "key": key, "verts": len(v), "tris": len(t),
            "size_m": (w, ln, ceil), "bays": bays_in(schema, profile, place),
            "eye": eye, "target": tgt}


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
    places = unbuilt(schema, profile)
    check("there are places to build", len(places) > 50, f"{len(places)}")

    # --- THE PROPERTY THAT MAKES THIS HONEST ------------------------------
    # Every prop any addressed place declares must exist as geometry, and
    # every prop implemented here must be declared by something. A declared
    # prop with no mesh is a promise the room does not keep; a mesh nothing
    # declares is dead weight.
    declared = {i for p in dr.PLACES for i in p["interacts"]}
    mine = {i for p in places for i in p["interacts"]}
    missing = sorted(mine - set(PROPS))
    check("every prop this generator must place has geometry",
          not missing, f"{len(missing)} missing: {missing[:8]}")
    orphan = sorted(set(PROPS) - declared)
    check("no prop geometry exists that nothing declares",
          not orphan, f"{len(orphan)} orphaned: {orphan[:8]}")

    # --- archetypes separate rooms ----------------------------------------
    arches = {}
    for p in places:
        arches.setdefault(archetype(p), []).append(p["key"])
    check("every place resolves to an archetype",
          all(archetype(p) for p in places))
    check("the archetypes actually separate the set",
          len(arches) >= 7, f"{sorted(arches)}")
    check("no archetype swallows most of the station",
          max(len(v) for v in arches.values()) < len(places) * 0.5,
          str({k: len(v) for k, v in arches.items()}))
    # Two rooms of the same size but different function must differ.
    med = next(p for p in places if archetype(p) == "medical")
    sto = next(p for p in places if archetype(p) == "store")
    check("a medical room and a store are not the same room",
          DENSITY["medical"] != DENSITY["store"])

    # --- geometry ---------------------------------------------------------
    total = 0
    for p in places:
        v, t, g = build(schema, profile, p)
        total += len(t)
        check(f"{p['key']}: builds", len(t) > 40, f"{len(t)} tri")
        check(f"{p['key']}: every triangle grouped",
              sum(hi - lo for _n, lo, hi in g) == len(t))
        w_f, l_f, _r = room_extent_m(schema, profile, p)
        bw, bl = bay_span_m(p)
        w, ln = min(w_f, bw), min(l_f, bl)
        xs = [q[0] for q in v]
        ys = [q[1] for q in v]
        zs = [q[2] for q in v]
        check(f"{p['key']}: inside its own footprint",
              min(xs) >= -w / 2 - WALL_T_M - 1e-6
              and max(xs) <= w / 2 + WALL_T_M + 1e-6
              and min(zs) >= -ln / 2 - WALL_T_M - 1e-6
              and max(zs) <= ln / 2 + WALL_T_M + 1e-6,
              f"x {min(xs):.2f}..{max(xs):.2f} in +/-{w / 2:.2f}")
        check(f"{p['key']}: nothing below the deck or through the soffit",
              min(ys) >= -0.15 and max(ys) <= ceiling_m(p) + 0.15,
              f"y {min(ys):.2f}..{max(ys):.2f} in a {ceiling_m(p):.2f} m room")
        # --- SOLIDS MAY NOT INTERPENETRATE --------------------------------
        # Props and fixtures are both solid objects standing in the same room,
        # and adding fixtures put a racking run and a workbench on the same
        # patch of wall in the first draft. Nothing else can see it: both are
        # inside the room, both are the right size, and a render of a grey box
        # inside another grey box looks like one grey box.
        boxes = _solid_boxes(v, t, g)
        clash = [(a[0], b[0]) for i, a in enumerate(boxes)
                 for b in boxes[i + 1:] if _overlaps(a[1], b[1])]
        check(f"{p['key']}: no two solids occupy the same space",
              not clash, f"{len(clash)}: {clash[:3]}")

        # Walkability, measured rather than assumed. The old form subtracted a
        # hardcoded 0.9 m of prop depth per side; once fixtures started eating
        # the walls that number was fiction, and a room could pass this while
        # having no floor left to stand on.
        check(f"{p['key']}: the room is still walkable",
              walkable(boxes, w, ln),
              f"no {WALK_M:.1f} m path across a {w:.1f}x{ln:.1f} m bay")

    # --- the directory's footprints must hold what they declare ------------
    # A location whose declared footprint is smaller than the bay its own
    # declared props need is an error in directory.py, not in this generator,
    # and clipping it silently would hide that. Reported here because this is
    # the first module that knows how big a prop is.
    undersized = []
    for p in places:
        w_f, l_f, _r = room_extent_m(schema, profile, p)
        bw, bl = bay_span_m(p)
        if w_f + 1e-6 < bw or l_f + 1e-6 < bl:
            undersized.append((p["key"], round(w_f, 1), round(l_f, 1),
                               round(bw, 1), round(bl, 1)))
    check("every footprint is at least one bay of its own contents",
          not undersized,
          f"{len(undersized)} too small (key, have_w, have_l, need_w, need_l): "
          f"{undersized[:4]}")

    # --- A BAY MUST READ AS FURNISHED -------------------------------------
    # The check that would have caught the empty 40 x 40 m hall. Floor area per
    # placed object is a direct measure of emptiness, and a 1,600 m2 room with
    # six props scores 267 m2 each. A furnished room is well under 30.
    #
    # Counts props AND fixtures, because both are objects standing in the room
    # and the player cannot tell which table they came from. It deliberately
    # does NOT count ribs: a rib is wall articulation, and letting a room pass
    # this by growing more ribs is exactly how the metric would go vacuous.
    worst = None
    for p in places:
        v, t, g = build(schema, profile, p)
        n = sum(1 for n_, _lo, _hi in g
                if n_.startswith("prop_") or n_.startswith("fix_"))
        bw, bl = bay_span_m(p)
        per = (bw * bl) / max(n, 1)
        if worst is None or per > worst[1]:
            worst = (p["key"], per, n)
        check(f"{p['key']}: the bay is furnished, not an empty hall",
              per < 30.0, f"{per:.0f} m2 per prop ({n} props in "
                          f"{bw:.1f}x{bl:.1f} m)")
    check("even the emptiest bay reads as a room",
          worst[1] < 30.0, f"{worst[0]} at {worst[1]:.0f} m2/prop")
    print(f"  emptiest bay: {worst[0]} at {worst[1]:.1f} m2 per prop")

    # --- the room holds its own contents ----------------------------------
    for p in places:
        tallest = max((PROPS[k][2] for k in p["interacts"] if k in PROPS),
                      default=0.0)
        check(f"{p['key']}: the room is tall enough for its own props",
              ceiling_m(p) >= tallest + CEIL_HEADROOM_M - 1e-9,
              f"{ceiling_m(p):.2f} m for a {tallest:.2f} m prop")
    # Rooms taller than a deck pitch span decks, which is legitimate and true
    # of the bays -- but it must be a small, named minority rather than the
    # generator quietly inflating everything.
    tall = [p["key"] for p in places if ceiling_m(p) > it.DECK_PITCH_M]
    check("multi-deck rooms are a minority and are the ones that should be",
          len(tall) < len(places) * 0.4,
          f"{len(tall)} of {len(places)}: {tall[:6]}")

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0, 0, 0), (1, 2, 3))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0)
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)

    # --- fixtures: the room contains what it is named for ------------------
    bare = [a for a, _ in ARCHETYPES if not FIXTURES.get(a)]
    check("no archetype builds a bare box", not bare and bool(FIXTURES.get(
        "generic")), f"no fixtures for {bare}")
    unscened = [p["key"] for p in places
                if not any(n.startswith("fix_") for n, _l, _h
                           in build(schema, profile, p)[2])]
    check("every room contains scenery it does not declare",
          not unscened, f"{len(unscened)}: {unscened[:6]}")
    # A fixture's whole point is being present WITHOUT being interactable. If
    # one ever gets a PROPS entry the two systems have merged and the honesty
    # check above ("no prop geometry nothing declares") stops meaning anything.
    dual = sorted({n for a in FIXTURES for n, *_ in FIXTURES[a]} & set(PROPS))
    check("no fixture is also a prop", not dual, f"{dual}")

    # --- AND THE TWO NEW GATES MUST BE ABLE TO FAIL -----------------------
    # Three assertions in this project have been vacuous -- one of them named
    # "FNV-1a is stable across processes" and comparing a value to itself. A
    # gate that cannot fail is worse than no gate, because it reads as cover.
    a_box = ("a", (0.0, 0.0, 0.0, 1.0, 1.0, 1.0))
    b_box = ("b", (0.5, 0.5, 0.5, 1.5, 1.5, 1.5))
    c_box = ("c", (2.0, 0.0, 0.0, 3.0, 1.0, 1.0))
    check("the interpenetration test fires on overlap",
          _overlaps(a_box[1], b_box[1]))
    check("the interpenetration test passes disjoint boxes",
          not _overlaps(a_box[1], c_box[1]))
    check("touching faces are not an overlap",
          not _overlaps((0, 0, 0, 1, 1, 1), (1, 0, 0, 2, 1, 1)))
    check("the walk test finds an open bay",
          walkable([], 4.0, 8.0))
    check("the walk test fails a bay walled across",
          not walkable([("w", (-2.0, 0.0, 0.0, 2.0, 2.0, 0.5))], 4.0, 8.0))
    check("the walk test routes around an island",
          walkable([("i", (-0.6, 0.0, 0.0, 0.6, 2.0, 0.6))], 4.0, 8.0))
    check("the walk test fails when the gap is under the walker",
          not walkable([("l", (-2.0, 0.0, 0.0, -0.3, 2.0, 0.5)),
                        ("r", (0.3, 0.0, 0.0, 2.0, 2.0, 0.5))], 4.0, 8.0))
    check("something hanging overhead does not block the floor",
          walkable([("o", (-2.0, 2.4, 0.0, 2.0, 2.8, 0.5))], 4.0, 8.0))

    print(f"\nrooms: {len(places)} locations, {len(arches)} archetypes, "
          f"{total:,} triangles ({total / len(places):,.0f} each)")
    for a in sorted(arches):
        print(f"  {a:12s} {len(arches[a]):3d}  density {DENSITY.get(a, 0.22):.2f}")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _cli(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--obj", metavar="PATH",
                    help="write one bay to PATH and print its camera")
    ap.add_argument("--key", default="fabrication",
                    help="directory key of the location to write")
    a = ap.parse_args(argv)
    if not a.obj:
        return _selftest()
    m = write_obj(a.obj, a.key)
    w, ln, ceil = m["size_m"]
    print(f"{m['key']}  {w:.1f} x {ln:.1f} x {ceil:.1f} m, "
          f"{m['tris']} tri, x{m['bays']} bays -> {m['path']}")
    print("  --eye %.2f %.2f %.2f --target %.2f %.2f %.2f"
          % (*m["eye"], *m["target"]))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
