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

# An archetype's height is right for the kind of room and wrong for a few
# named ones, and the coolant gallery is the case that forced this. It is
# `industrial` because its shell, materials and fittings are a plant room's --
# and `industrial` is 7.5 m, which is a foundry. `docs/volume-audit.md` §4
# describes it as *"0.173 g on the spine -- a crawlway, not a corridor"*, and a
# crawlway wrapping a reactor at 48.3 m radius is not seven and a half metres
# tall. 3.20 m is a service gallery: standing height plus the pipe run over it.
#
# THE MEASURED CONSEQUENCE, stated because it also moves a gate. `_selftest`
# holds multi-deck rooms under 40% of the generator's remit -- "a small, named
# minority rather than the generator quietly inflating everything" -- and with
# the gallery at 7.5 m that count is 32 of 78, which FAILS. It is 31 of 78 with
# the gallery at its right height. The threshold was NOT touched: 39.7% against
# a 40% bar is one room of margin, and the next tall room added here will fail
# it. That is the gate working, and the fix then is a look at the ceilings, not
# at the number.
PLACE_CEILING = {"coolant_gallery": 3.20}

# ---------------------------------------------------------------------------
# V1 -- CLEAR HEIGHT, KEYED ON FUNCTION.  INV-141
# ---------------------------------------------------------------------------
# `docs/variety-V0.md` section 5: the SECTION channel is the worst number in
# the whole measurement -- **47.6% of all 8,128 pairs are above the ceiling
# there**, median 0.699 against 0.269 for plan -- and section 7 says why in one
# line: **48 of 128 places share a 2.90 m ceiling** and eleven distinct heights
# exist on the entire station, one per archetype.
#
# A cross-section IoU between two box rooms is exactly `min(h1,h2)/max(h1,h2)`,
# which is worth stating because it bounds what this table can do: two rooms
# are told apart on section alone only if one is 1.37x the height of the other.
# So this does NOT break clusters on its own and is not meant to -- it moves the
# distribution, and it moves `rib_pitch_m` and `light_pitch_m` with it, which
# are plan.
#
# THE LADDER, and every value on it is a clearance argument rather than a taste:
#
#   2.40  a berth.  1.70 m standing plus hair, and a bunk you sit up in.
#         Nothing passes overhead because there is nothing to pass.
#   2.60  a cell.  One person, a fixed light, a door that opens inward.
#   2.90  THE STATION'S FITTED STANDARD, and the anchor the rest is read
#         against.  It is what `CEIL_BY_ARCHETYPE` already called an office.
#   3.10  people stand round a table in it, so the space over the table has to
#         read as room rather than as lid.
#   3.20  a ducted service zone runs over it -- 0.30 m of duct on 0.15 m of
#         hanger, clear of a 2.35 m door head.
#   3.40  a public room: a queue, a counter, signage over the counter.
#   3.60  a gantry track or a lifting point over a working surface.  One deck
#         pitch, which is the most a room can be without spanning two.
#   4.20+ a volume where height IS the content -- worship, and the plant.
#
# NOTHING BELOW 3.60 IS RAISED ABOVE IT and that is a hard constraint rather
# than a style: `_selftest` holds rooms taller than `interior.DECK_PITCH_M` to
# under 40% of the generator's remit and the count stands at 31 of 78, which is
# 39.7% -- ONE ROOM of margin.  The industrial and store functions below are
# already over that line and are varied within it; every other function here is
# clamped under 3.60 so this table cannot move the count at all.  Asserted.
FUNCTION_HEIGHT = {
    # --- you sleep in it ---------------------------------------------------
    "residence": 2.60, "informal_residence": 2.40, "short_stay": 2.45,
    "detention": 2.55, "crime": 2.40, "organised_crime": 2.65,
    # --- you work in it, one or two of you ---------------------------------
    "offices": 2.75, "administration": 2.90, "psi_corps": 3.00,
    "political_policing": 2.85, "law_enforcement": 2.95, "surveillance": 2.70,
    "military_liaison": 3.05, "hire": 2.90, "mortuary": 2.80,
    # --- you meet in it: the table needs air over it ------------------------
    "meeting": 3.10, "diplomacy": 3.45, "diplomatic_mission": 3.40,
    "briefing": 3.25, "adjudication": 3.50, "ombudsman_hearings": 3.35,
    "council_session": 3.60, "ceremony": 3.55, "civic": 3.50,
    # --- medical: the gantry over the bed decides it ------------------------
    "medical": 3.05, "triage": 3.00, "surgery": 3.60, "quarantine": 3.10,
    "research": 3.30, "monitoring": 3.15, "variable_gravity": 3.55,
    # --- a watch floor: screens above eye level, cable tray above those -----
    "station_ops": 3.45, "traffic_control": 3.40, "control": 3.20,
    "command": 3.50, "defence_command": 3.35, "fire_control": 3.30,
    "signal_ops": 3.25, "communications": 3.30, "sensors": 3.15,
    "navigation": 3.35,
    # --- you queue in it ----------------------------------------------------
    "commerce": 3.40, "retail": 3.20, "mail": 3.00, "issue_stores": 3.30,
    "currency_exchange": 3.10, "immigration": 3.50, "identicard_check": 3.20,
    "checkpoint": 3.00, "contraband_search": 3.25, "manifest": 3.05,
    "dispatch": 3.15, "public_information": 3.30, "logistics": 3.45,
    "arrival": 3.60, "wayfinding": 3.30, "ship_arrival": 3.55,
    "ship_departure": 3.55,
    # --- you drink in it: low is the point, it is why a bar feels like one --
    "hospitality": 2.90, "food_service": 3.10, "catering": 3.20,
    "gambling": 3.35, "crew_social": 2.85, "rumour": 2.80, "nightlife": 3.45,
    "black_market": 2.70, "black_market_fringe": 2.75, "public_social": 3.55,
    "crowd_hub": 3.60,
    # --- you pass through it ------------------------------------------------
    "transit": 3.40, "eva_egress": 3.30, "suit_service": 3.45,
    "umbilical_service": 3.50, "starfury_launch": 3.60, "ship_mooring": 3.55,
    # --- height IS the content ----------------------------------------------
    "worship": 4.20, "contemplation": 3.60, "quiet": 3.00,
    "observation": 3.60, "viewport": 3.50, "recreation": 3.40, "sport": 3.60,
    # --- and the ones already over a deck pitch, varied within it -----------
    # Every value here is what has to fit UNDER the roof: a vessel and the
    # crane that lifts its head off, a stacked container and the reach of the
    # gantry over it, a heat exchanger and its pull space.
    "power_generation": 8.40, "power_distribution": 7.50,
    "emergency_power": 6.20, "reactor_control": 6.80, "rotation": 8.10,
    "coolant_loop": 5.40, "coolant_transfer": 5.20, "cooling": 5.80,
    "heat_rejection": 7.20, "air_handling": 6.40, "atmosphere_plant": 6.00,
    "oxygen_production": 6.60, "water_reclamation": 6.20, "water_storage": 8.20,
    "waste_processing": 6.80, "fabrication": 7.50, "industry": 7.20,
    "repair": 6.00, "fighter_maintenance": 7.20, "plant": 7.40,
    "storage": 6.50, "hazardous_storage": 5.60, "fuel_storage": 7.80,
    "cargo_handling": 8.60, "atmosphere_feedstock": 6.90,
    "microgravity_handling": 7.40, "fuel_transfer": 6.30,
}
# What a function may not do to a room that is under a deck pitch today.
FUNCTION_HEIGHT_CAP_M = 3.60


def function_ceiling_m(place):
    """The clear height this place's own functions ask for, or None.

    The MAX over its functions, because a room has to hold the tallest thing it
    is for: `waste_control` is (waste_processing, control) and is a 6.80 m plant
    hall with a control desk in it, not a 3.20 m control room with a digester.
    """
    hs = [FUNCTION_HEIGHT[f] for f in place["functions"] if f in FUNCTION_HEIGHT]
    return max(hs) if hs else None


def ceiling_m(place):
    """Room height: the archetype's nominal, raised to hold its own props.

    Deliberately allowed to exceed DECK_PITCH_M. A docking bay is 18 m tall in
    `docking_bay.py` and spans many decks; pretending every volume fits in one
    3.6 m pitch is what produced a 5 m door in a 2.9 m room.
    """
    arch_base = CEIL_BY_ARCHETYPE.get(archetype(place), 2.9)
    base = PLACE_CEILING.get(place["key"])
    if base is None:
        base = function_ceiling_m(place)
        # THE CAP, AND IT IS LOAD-BEARING.  A function may vary a room's height
        # freely inside the band its archetype already occupies, and may NOT
        # push a room that fits in one deck pitch into two.  Measured without
        # it: `hydroponics` (agriculture, oxygen_production, food_production),
        # `fusion_core` (power_generation) and `cryo_storage` (medical,
        # storage) all went from under 3.60 m to 6.5-8.4 m, taking the
        # multi-deck count from 31 of 78 to 34 and failing the 40% gate by one
        # room.  Each of those three IS arguably a tall volume -- and this
        # session was asked to make rooms various, not to re-proportion three
        # named places as a side effect.  `ARCHETYPES` records the identical
        # decision about `power_generation` for the identical reason.
        if base is not None and arch_base <= it.DECK_PITCH_M:
            base = min(base, FUNCTION_HEIGHT_CAP_M)
    if base is None:
        base = arch_base
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
    # --- session 3u: the 33 declared interactables that had no definition ----
    # `directory.py` has carried these in `interacts` since layer 1 -- they are
    # what a player can USE -- and `PROPS` never gained an entry for any of
    # them, so `lateral_stack` raised KeyError on the location. It went unnoticed
    # because every gate that touches a room either samples a subset or catches
    # broadly; `station/deck.py` found it by trying to assemble five of them
    # into one deck and getting one.
    #
    # Dimensions are (width, depth, height, mount) like the rest, chosen at the
    # scale the object has to be to work: a customs desk you queue at, a service
    # ladder a person climbs, a market stall you walk past. All extrapolation
    # and all replaceable -- what matters is that the location BUILDS.
    "menu_display": (0.6, 0.06, 0.8, "wall"),
    "customs_desk": (2.2, 0.9, 1.05, "floor"),
    "info_board": (1.2, 0.08, 0.9, "wall"),
    "shower": (0.9, 0.9, 2.1, "floor"),
    "market_stall": (2.4, 1.6, 2.2, "floor"),
    "shopfront": (3.0, 0.4, 2.4, "wall"),
    "gallery_rail": (2.0, 0.08, 1.05, "floor"),
    "reception": (2.6, 0.8, 1.1, "floor"),
    "airlock_door": (1.6, 0.25, 2.1, "wall"),
    "atmosphere_status_lamp": (0.22, 0.12, 0.22, "wall"),
    "service_ladder": (0.5, 0.18, 2.4, "wall"),
    "brazier": (0.7, 0.7, 0.9, "floor"),
    "shuttle_door": (1.8, 0.25, 2.1, "wall"),
    "comms_channel": (0.4, 0.1, 0.5, "wall"),
    "baggage_scanner": (1.4, 2.2, 1.6, "floor"),
    "station_schematic_screen": (1.8, 0.1, 1.2, "wall"),
    "welcome_board": (2.0, 0.1, 1.0, "wall"),
    "bollard": (0.25, 0.25, 0.9, "floor"),
    "deck_marking": (1.2, 1.2, 0.01, "floor"),
    "bay_control_booth": (2.4, 2.0, 2.4, "floor"),
    "cafe_table": (0.8, 0.8, 0.74, "floor"),
    "planter": (1.2, 0.6, 0.7, "floor"),
    "dartboard": (0.45, 0.06, 0.45, "wall"),
    "pendant_lamp": (0.3, 0.3, 0.4, "ceiling"),
    "delegate_bench": (2.4, 0.6, 0.9, "floor"),
    "speaking_position": (1.0, 0.6, 1.15, "floor"),
    "gallery_door": (1.2, 0.2, 2.1, "wall"),
    "breather_dispenser": (0.5, 0.3, 1.3, "wall"),
    "barred_screen": (1.6, 0.1, 2.2, "wall"),
    "building_door": (1.4, 0.2, 2.2, "wall"),
    "standpipe": (0.3, 0.3, 1.1, "floor"),
    "launch_tube": (3.0, 3.0, 3.0, "floor"),
    "clamp": (1.2, 1.2, 0.8, "floor"),
}

# Which archetype a location uses, chosen by its primary function. Order
# matters: the first match wins, so the most specific functions come first.
ARCHETYPES = (
    ("medical", ("medical", "triage", "surgery", "mortuary")),
    ("detention", ("detention", "checkpoint")),
    ("worship", ("worship", "contemplation")),
    ("industrial", ("fabrication", "industry", "repair", "power_distribution",
                    "waste_processing", "water_reclamation", "air_handling",
                    "water_storage", "cooling", "rotation",
                    # The volume audit's plant rooms (session 3z). A reactor
                    # hall, a generator hall, a heat-exchanger hall and a
                    # coolant gallery are all the same KIND of volume -- tall,
                    # oxide-ribbed, high-bay lit, plate floor -- and differ in
                    # the machinery standing in them, which is PLACE_FIXTURES'
                    # job rather than the archetype's.
                    #
                    # `power_generation` is deliberately NOT here. It would
                    # take `fusion_core` from `generic` to `industrial` -- an
                    # improvement, but a silent change to a place this session
                    # was not asked to move, and its 360 deg x 800 m footprint
                    # is not a room this generator should be re-proportioning
                    # as a side effect. Recorded rather than done.
                    "reactor_control", "heat_rejection", "coolant_loop")),
    ("research", ("research", "monitoring", "variable_gravity")),
    ("store", ("storage", "hazardous_storage", "fuel_storage",
               "cargo_handling", "atmosphere_feedstock",
               "microgravity_handling", "fuel_transfer", "manifest")),
    # AN AIRLOCK IS A PLACE YOU PASS THROUGH, and that is why the two
    # pressure-boundary rooms are transit and not store. The shell is what the
    # archetype decides -- 3.4 m clear, nosed deck edges, pooled deck lighting,
    # painted rather than plate wall -- and every one of those is right for a
    # lock chamber and wrong for a 6.5 m cargo hall. `ship_mooring` is NOT
    # here: `mooring_clamps` declares it and is a hull component, not a room.
    ("transit", ("transit", "eva_egress", "suit_service",
                 "umbilical_service")),
    ("hospitality", ("hospitality", "food_service", "catering", "gambling")),
    ("commerce", ("commerce", "retail", "currency_exchange", "black_market",
                  "mail", "issue_stores", "logistics")),
    ("office", ("offices", "administration", "command", "diplomacy",
                "meeting", "briefing", "adjudication", "law_enforcement",
                "surveillance", "political_policing", "station_ops",
                "traffic_control", "control", "psi_corps",
                "military_liaison", "ceremony", "hire",
                # A watch floor is an office with racks in it. `communications`
                # and `defence_command` are deliberately absent: `comms_grid`
                # declares the first and is a hull pylon, and `cnc`/`war_room`
                # already resolve here on their own functions, so adding either
                # would move a place without changing an outcome.
                "fire_control", "signal_ops")),
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


# ===========================================================================
# V1 -- THE PLAN GRAMMAR.  WHAT SHAPE A ROOM'S FLOOR IS, FROM WHAT IT IS FOR
# ===========================================================================
# `station/variety.py` measured the station and found 27 clusters of mutually
# indistinguishable places covering 82 of 128, and `--drivers` measured the
# CAUSE rather than guessing it:
#
#     both built generic   +0.195 on form      <-- ten times the next driver
#     same archetype       +0.021
#     shared function      +0.162  -- and the sign is BACKWARDS
#     sector / auth / ring / species mix   inert, +/-0.01
#
# Read the shape of that before its size, which is this repository's own rule.
# The places are not alike because they are similar KINDS of place; they are
# alike because they come out of the SAME FUNCTION.  Eleven archetypes decided
# the whole of form for 128 places, `functions` was read exactly once in the
# entire generator (by `archetype()`), and the register declares **122 distinct
# functions**, of which the archetypes claim 66.
#
# So form is keyed here on the FUNCTION rather than on the eleven-way
# archetype, and it is keyed by COMPOSITION rather than by a winner-takes-all
# lookup.  That second half is the whole design and it is forced by the data:
# the eight-place office cluster holds eight DISTINCT function tuples --
# (administration, command), (ceremony, hire), (diplomacy, meeting),
# (meeting,), (offices,), (administration, military_liaison),
# (political_policing, administration), (offices, psi_corps) -- so any rule
# that picks one function and throws the rest away collapses four of those onto
# one plan again.  An element per function keeps all eight apart.
#
# WHAT AN ELEMENT IS.  Not a prop.  V0's own last section says what not to do
# -- *"content is already the least bad channel ... they are the same because
# they are the same box, and a box with more things in it is still that box"*
# -- so every element here is a piece of PLAN: something standing in the middle
# of the floor, or dividing it, or ranked across it.  A player reads the
# arrangement of a room from the door and reads its props by walking up to one.
#
# (name, span_along_z, extent_across_x, height, kind), the same 5-tuple shape
# `FIXTURES` uses, so `_fixture` builds these through exactly the same
# articulated machines -- there is no second geometry path to drift.  What the
# two middle numbers mean depends on the kind, and that is stated per kind in
# `place_elements`:
#
#   island  ONE block on the centreline, walked around.  A conference table, a
#           bar counter, a reactor drum.
#   rank    rows across the room at a pitch, with a centre aisle.  Pews, desk
#           ranks, racking, market stalls.  The strongest plan signature there
#           is, because it fills the middle of the floor in stripes.
#   cross   ONE run across the room a third of the way in, with a gap at one
#           end.  The counter that divides a public side from a staff side.
#   cell    fins off ONE long wall at a pitch, making units off an aisle.  This
#           is the one V0 names outright: *"a residence is CELLULAR -- that is a
#           topology change, not a furniture change"*.
#   end     ONE block against the far end wall, spanning most of the width with
#           a way past it.  A dais, a shielded booth, an airlock lobby.
#
# THE NAMES READ BACKWARDS AND THAT IS THE HOUSE RULE, not an oversight -- see
# `PLACE_FIXTURES` below.  `materials.resolve` matches a group name against bind
# FRAGMENTS as substrings, `station/materials.py` is not editable from this
# session, and a fixture whose name resolved to nothing would ship rooms of
# unmaterialled surface and take `test_materials_layer3.py` down with it.  So
# the bound fragment names the MATERIAL and the qualifier names the OBJECT:
# `fume_column_table` is a conference table in `furn_casework`, the painted
# steel desk and counter body, and `dais_pew_row` is seating in
# `furn_worship_stone`.  `_selftest` asserts every name here resolves.
#
# INV-140.  Everything in this table is extrapolation.  What constrains it: an
# element must leave the room crossable by a 0.9 m walker (asserted), must not
# occupy the same cubic metre as anything else (asserted, and by construction
# -- see `place_elements`), must fit under the room's own ceiling (asserted),
# and must be the arrangement the named activity actually has -- a counter you
# queue at, rows you sit in, cells you sleep in.
PLAN_ELEMENTS = {
    # --- you sit round it -------------------------------------------------
    # A meeting is a table with people on both sides of it, and the room is the
    # walkround.  3.2 m seats eight; 1.30 m across is two 0.65 m reaches.
    "meeting":            (("fume_column_table", 3.20, 1.30, 0.74, "island"),),
    "diplomacy":          (("dais_delegate_bench", 0.60, 1.40, 0.90, "rank"),),
    "adjudication":       (("dais_platform", 1.40, 0.00, 0.35, "end"),),
    "council_session":    (("dais_delegate_bench", 0.60, 1.40, 0.90, "rank"),),
    "ombudsman_hearings": (("dais_platform", 1.20, 0.00, 0.35, "end"),),
    "briefing":           (("dais_pew_row", 0.50, 1.40, 0.90, "rank"),),
    # --- you queue at it --------------------------------------------------
    # A counter across the room is what makes a public side and a staff side,
    # and it is the plan every transactional space on the station has.  The gap
    # is a walker plus a trolley.
    "commerce":           (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "retail":             (("stall_frame_row", 1.30, 1.80, 2.20, "rank"),),
    "mail":               (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "issue_stores":       (("racking_run_rank", 1.00, 1.60, 2.40, "rank"),),
    "currency_exchange":  (("fume_column_counter", 0.60, 1.60, 1.15, "cross"),),
    "immigration":        (("fume_column_counter", 0.80, 1.60, 1.05, "cross"),),
    "identicard_check":   (("partition_screen_booth", 1.60, 0.00, 2.20, "end"),),
    "checkpoint":         (("partition_screen_booth", 1.40, 0.00, 2.20, "end"),),
    "contraband_search":  (("fume_column_counter", 0.90, 1.60, 0.95, "cross"),),
    "manifest":           (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "hire":               (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "dispatch":           (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "public_information": (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "logistics":          (("racking_run_rank", 1.10, 1.60, 2.60, "rank"),),
    # --- you work at it, in rows ------------------------------------------
    # A clerked office is desks in ranks, not furniture round the walls -- and
    # the ranks are what a player sees from the door.
    "offices":            (("fume_column_desk_rank", 0.80, 1.40, 0.74, "rank"),),
    "administration":     (("fume_column_desk_rank", 0.80, 1.40, 0.74, "rank"),),
    "station_ops":        (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "traffic_control":    (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "control":            (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "command":            (("dais_platform", 1.60, 0.00, 0.35, "end"),),
    "defence_command":    (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "fire_control":       (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "signal_ops":         (("racking_run_rank", 0.70, 1.60, 2.20, "rank"),),
    "communications":     (("racking_run_rank", 0.70, 1.60, 2.20, "rank"),),
    "sensors":            (("racking_run_rank", 0.70, 1.60, 2.20, "rank"),),
    "navigation":         (("fume_column_console_rank", 0.90, 1.60, 1.05, "rank"),),
    "monitoring":         (("fume_column_console_rank", 0.85, 1.60, 1.05, "rank"),),
    "surveillance":       (("partition_screen_booth", 1.60, 0.00, 2.20, "end"),),
    # A telepath's office and the Ministry of Peace are both an office with a
    # room inside it, and they are DIFFERENT rooms inside it: a Psi Corps
    # consulting suite is a shielded box you are taken into, and a political
    # police office is a barrier you are stopped at.
    "psi_corps":          (("partition_screen_booth", 2.00, 0.00, 2.35, "end"),),
    "political_policing": (("fume_column_counter", 0.90, 1.60, 1.15, "cross"),),
    "law_enforcement":    (("fume_column_counter", 0.80, 1.60, 1.15, "cross"),),
    "military_liaison":   (("fume_column_table", 2.40, 1.10, 0.74, "island"),),
    "diplomatic_mission": (("dais_delegate_bench", 0.60, 1.40, 0.90, "rank"),),
    "ceremony":           (("dais_platform", 1.80, 0.00, 0.35, "end"),),
    "civic":              (("dais_pew_row", 0.50, 1.40, 0.90, "rank"),),
    # --- you sit in rows facing one end ------------------------------------
    "worship":            (("dais_pew_row", 0.50, 1.40, 0.90, "rank"),),
    "contemplation":      (("dais_platform", 1.40, 0.00, 0.35, "end"),),
    "quiet":              (("dais_pew_row", 0.45, 1.40, 0.90, "rank"),),
    # --- you sleep in it, and it is CELLULAR -------------------------------
    # V0's own example.  A residence is not a differently furnished hall: it is
    # a run of units off an aisle, and the fins are the units.
    "residence":          (("partition_screen_cell", 0.16, 2.00, 2.20, "cell"),),
    "informal_residence": (("partition_screen_cell", 0.12, 1.60, 2.00, "cell"),),
    "short_stay":         (("partition_screen_cell", 0.16, 1.80, 2.20, "cell"),),
    "detention":          (("cell_divider_bay", 0.30, 2.20, 2.30, "cell"),),
    "quarantine":         (("partition_screen_cell", 0.20, 2.20, 2.35, "cell"),),
    "sealed_environment": (("partition_screen_booth", 1.60, 0.00, 2.35, "end"),),
    "multi_environ":      (("partition_screen_cell", 0.20, 2.40, 2.35, "cell"),),
    # --- a bed with servicing round it -------------------------------------
    # A medlab is BAYS, and a bay is defined by what stands between two beds.
    "medical":            (("equipment_gantry_bay", 0.55, 1.60, 2.30, "cell"),),
    "triage":             (("cell_divider_bay", 0.25, 1.40, 1.90, "cell"),),
    "surgery":            (("equipment_gantry_bay", 0.70, 2.00, 2.30, "cell"),),
    "mortuary":           (("cell_divider_bay", 0.30, 2.10, 2.00, "cell"),),
    "repair":             (("cell_divider_bay", 0.30, 2.20, 2.00, "cell"),),
    "fighter_maintenance": (("cell_divider_bay", 0.35, 2.40, 2.20, "cell"),),
    "suit_service":       (("racking_run_rank", 0.60, 1.60, 2.10, "rank"),),
    "research":           (("fume_column_bench_rank", 0.75, 1.60, 0.90, "rank"),),
    "variable_gravity":   (("racking_run_rank", 0.80, 1.60, 2.40, "rank"),),
    # --- you drink at it ----------------------------------------------------
    # A bar IS its counter, and the counter is an island you are served at from
    # one side -- which is why a bar reads differently from a mess hall even
    # when both are 8 x 8 m with tables in them.
    "hospitality":        (("back_shelving_bar", 4.00, 0.72, 1.08, "island"),),
    "food_service":       (("fume_column_counter", 0.70, 1.60, 1.05, "cross"),),
    "catering":           (("racking_run_rank", 0.60, 1.60, 2.20, "rank"),),
    "gambling":           (("back_shelving_bar", 2.20, 1.10, 0.78, "island"),),
    "crew_social":        (("back_shelving_bar", 3.20, 0.72, 1.08, "island"),),
    "rumour":             (("partition_screen_booth", 1.20, 0.00, 2.00, "end"),),
    "nightlife":          (("stall_frame_row", 1.10, 1.80, 2.20, "rank"),),
    # --- the black economy, which is stalls and screens ---------------------
    "black_market":       (("stall_frame_row", 1.40, 1.80, 2.20, "rank"),),
    "black_market_fringe": (("stall_frame_row", 1.00, 1.80, 2.00, "rank"),),
    "organised_crime":    (("partition_screen_booth", 1.80, 0.00, 2.20, "end"),),
    "crime":              (("partition_screen_cell", 0.12, 1.40, 2.00, "cell"),),
    "public_social":      (("dais_platform", 1.20, 0.00, 0.35, "end"),),
    "crowd_hub":          (("fume_column_counter", 0.60, 1.60, 1.05, "cross"),),
    # --- the plant, which is one big machine you walk round -----------------
    "power_generation":   (("plant_column_core", 2.40, 2.40, 3.20, "island"),),
    "power_distribution": (("plant_column_core", 2.00, 1.80, 3.00, "island"),),
    "emergency_power":    (("plant_column_core", 1.80, 1.60, 2.60, "island"),),
    "reactor_control":    (("fume_column_console_rank", 0.90, 1.60, 1.15, "rank"),),
    "rotation":           (("plant_column_core", 2.60, 2.20, 3.40, "island"),),
    "coolant_loop":       (("plant_column_core", 1.60, 1.60, 3.00, "island"),),
    "coolant_transfer":   (("racking_run_rank", 0.90, 1.60, 2.60, "rank"),),
    "cooling":            (("racking_run_rank", 1.00, 1.60, 2.80, "rank"),),
    "heat_rejection":     (("plant_column_core", 2.20, 2.00, 3.20, "island"),),
    "air_handling":       (("plant_column_core", 2.00, 2.00, 3.40, "island"),),
    "atmosphere_plant":   (("plant_column_core", 2.40, 2.20, 3.60, "island"),),
    "oxygen_production":  (("racking_run_rank", 1.20, 1.60, 2.60, "rank"),),
    "water_reclamation":  (("plant_column_core", 2.20, 2.20, 3.00, "island"),),
    "water_storage":      (("plant_column_core", 2.60, 2.40, 3.60, "island"),),
    "waste_processing":   (("racking_run_rank", 1.10, 1.60, 2.80, "rank"),),
    "fabrication":        (("cell_divider_bay", 0.30, 2.40, 2.20, "cell"),),
    "industry":           (("racking_run_rank", 1.10, 1.60, 2.80, "rank"),),
    "plant":              (("plant_column_core", 2.00, 2.00, 3.00, "island"),),
    "maintenance_access": (("racking_run_rank", 0.70, 1.40, 2.20, "rank"),),
    "services":           (("racking_run_rank", 0.70, 1.40, 2.20, "rank"),),
    # --- you put things down in it ------------------------------------------
    "storage":            (("racking_run_rank", 1.10, 1.60, 2.60, "rank"),),
    "hazardous_storage":  (("racking_run_rank", 1.20, 1.80, 2.40, "rank"),),
    "fuel_storage":       (("plant_column_core", 2.40, 2.40, 3.40, "island"),),
    "cargo_handling":     (("racking_run_rank", 1.30, 1.80, 3.00, "rank"),),
    "atmosphere_feedstock": (("plant_column_core", 2.20, 2.20, 3.20, "island"),),
    "microgravity_handling": (("racking_run_rank", 0.90, 1.60, 2.80, "rank"),),
    "fuel_transfer":      (("plant_column_core", 1.80, 1.80, 2.80, "island"),),
    # --- you pass through it -------------------------------------------------
    # A concourse is not furnished: it is a floor with a line across it and
    # everything else pushed to the walls.
    "arrival":            (("fume_column_counter", 0.60, 1.80, 1.05, "cross"),),
    "ship_arrival":       (("partition_screen_booth", 1.20, 0.00, 2.10, "end"),),
    "ship_departure":     (("fume_column_counter", 0.60, 1.80, 1.05, "cross"),),
    "wayfinding":         (("partition_screen_booth", 1.00, 0.00, 2.20, "end"),),
    "eva_egress":         (("racking_run_rank", 0.60, 1.60, 2.10, "rank"),),
    "umbilical_service":  (("racking_run_rank", 0.80, 1.60, 2.40, "rank"),),
    "starfury_launch":    (("plant_column_core", 2.20, 2.20, 3.20, "island"),),
    "ship_mooring":       (("plant_column_core", 2.00, 2.00, 2.80, "island"),),
    # --- and the ones that are a floor rather than a fit-out ------------------
    "agriculture":        (("racking_run_rank", 1.20, 1.60, 1.20, "rank"),),
    "food_production":    (("racking_run_rank", 1.10, 1.60, 2.20, "rank"),),
    "recreation":         (("dais_platform", 1.20, 0.00, 0.35, "end"),),
    "sport":              (("dais_platform", 1.60, 0.00, 0.35, "end"),),
    "observation":        (("dais_platform", 1.00, 0.00, 0.35, "end"),),
    "viewport":           (("dais_platform", 0.90, 0.00, 0.35, "end"),),
}

# HOW MANY OF THEM, and the cap is a triangle budget rather than a taste:
# `station/budget.py` gates deck primitives at 401 of 600 and every element
# instance is a group.  Two also keeps the composition legible -- a room is a
# thing and a modifier -- and it is enough for combinatorial separation: the
# eight-place office cluster resolves to eight distinct ordered pairs.
MAX_ELEMENTS = 2
ROW_GAP_M = 0.90           # between two ranked rows: a person, edge on
CELL_PITCH_M = 2.40        # a unit's width between two fins
ELEMENT_CLEAR_M = 0.10     # element to the band the walls' own furniture takes


def elements_for(place):
    """The plan elements this place composes, in the order it declares them.

    THE ORDER IS THE REGISTER'S, not this table's, and that is deliberate: the
    directory lists a place's functions with the primary one first, so the
    element that shapes the middle of the floor is the one the place is chiefly
    for.  `minipax` is (political_policing, administration) and gets the
    barrier counter first; `earthforce_office` is (administration,
    military_liaison) and gets the desk ranks first.  Two rooms that share a
    function but declare it at a different rank get different plans, which is
    correct -- they are different rooms.

    Deduplicated BY NAME, so a place declaring two functions that want the same
    element gets one of it rather than two in the same cubic metre.
    """
    out, seen = [], set()
    for fn in place["functions"]:
        for el in PLAN_ELEMENTS.get(fn, ()):
            if el[0] in seen:
                continue
            seen.add(el[0])
            out.append(el)
            if len(out) >= MAX_ELEMENTS:
                return tuple(out)
    return tuple(out)


# WHICH WALLS CARRY FURNITURE, and it is the cheapest half of the plan channel.
# `dressing.dress` put furniture against ALL FOUR walls of every room on the
# station, so every room wore the same ring -- and that ring is roughly 6 m2 of
# an 11 m2 plan, over half of everything the plan channel can see.  Which walls
# a room uses is a fact about what it is for: you do not stand shelving across
# an observation deck's window wall, and a room whose middle is full of ranked
# rows keeps its long walls clear because that is how you reach the rows.
#
# Keyed on the FIRST element's kind, because that is what the room is chiefly
# for.  `dressing.dress`'s own wall names.
DRESS_WALLS = {
    "island": ("z-", "z+"),        # walked round: the long walls ARE the walkround
    "rank":   ("z-", "z+"),        # reached from the ends, down the aisle
    "cross":  ("x-", "x+"),        # the counter divides; the sides are fitted out
    "cell":   ("x-", "z-"),        # the units take +x; the opposite wall is fitted
    "end":    ("x-", "x+", "z-"),  # everything but the wall the block stands on
}


def dress_walls(place):
    """Which of the four walls this room's furniture stands against."""
    els = elements_for(place)
    if not els:
        return ("x-", "x+", "z-", "z+")
    use = list(DRESS_WALLS[els[0][4]])
    # AND THE SECOND ELEMENT HAS A CLAIM TOO.  Measured, not reasoned:
    # `telepath_office` is (offices, psi_corps) -- a desk rank, whose kind
    # dresses both end walls, and then a shielded booth against the far one,
    # which reported `want 1, got 0` because the furniture was already there.
    # A room where the second element silently does not exist is a room that
    # came back generic, so the wall it stands on is taken off the list.
    if any(k == "end" for *_r, k in els) and "z+" in use:
        use.remove("z+")
    if any(k == "cell" for *_r, k in els) and "x+" in use:
        use.remove("x+")
    return tuple(use)


def element_keep_m(place):
    """The band each of the four walls keeps for its own furniture, in metres.

    ONE STATEMENT, READ BY THREE CALLERS -- the width sizing, the length sizing
    and the placement -- because the last time this project kept two copies of
    one cross-section they disagreed by 0.26 m and a flood fill found it
    (`lateral_stack`'s docstring).  Returns (x-, x+, z-, z+).

    A wall that carries no furniture keeps almost nothing, which is most of why
    keying the dressing on the plan pays for itself twice: a cellular room
    dresses two walls, so its run of cells has the other two ends of the room
    to run into.
    """
    import dressing as _dress                                   # noqa: PLC0415
    band = _dress.wall_band_m(archetype(place))
    deep = max((PROPS[k][1] for k in place["interacts"]
                if PROPS.get(k, (0, 0, 0, "floor"))[3] == "floor"), default=0.0)
    dw = dress_walls(place)
    # The two long walls carry the DECLARED floor props whether they are dressed
    # or not -- `place_interacts` ranks them down both -- so their band is the
    # deeper of the two claims.  The end walls carry only wall-mounted props,
    # which are 0.45 m at the deepest.
    return (max(band if "x-" in dw else 0.0, deep) + ELEMENT_CLEAR_M,
            max(band if "x+" in dw else 0.0, deep) + ELEMENT_CLEAR_M,
            (band if "z-" in dw else 0.45) + ELEMENT_CLEAR_M,
            (band if "z+" in dw else 0.45) + ELEMENT_CLEAR_M)


def element_cross_m(place):
    """How much of the room's WIDTH the plan elements need, insets included.

    `bay_span_m` adds this so the bay is sized for the arrangement, rather than
    the arrangement being squeezed into a bay sized for something else -- which
    is the defect `lateral_stack` was extracted to close, one level up.
    """
    els = elements_for(place)
    if not els:
        return 0.0
    kx0, kx1, _z0, _z1 = element_keep_m(place)
    need = 0.0
    for _n, _span_z, ext_x, _h, kind in els:
        if kind == "island":
            need = max(need, ext_x + 2 * AISLE_M)
        elif kind in ("rank", "cross"):
            need = max(need, ext_x + 2 * 1.20)   # the aisle plus two half rows
        elif kind == "cell":
            need = max(need, ext_x * (2 if sum(
                1 for e in els if e[4] == "cell") > 1 else 1) + AISLE_M + 1.20)
        elif kind == "end":
            need = max(need, AISLE_M + 1.20)
    return need + kx0 + kx1


def element_along_m(place):
    """How much of the room's LENGTH the plan elements need, insets included.

    Three rows is a rank and one row is a table; two cells is a cellular run and
    one cell is a cupboard.  A bay shorter than this gets the degenerate case,
    which is variety measured and not built -- so the sizing asks for the real
    thing and `place_elements`' report says whether it got it.
    """
    els = elements_for(place)
    if not els:
        return 0.0
    _x0, _x1, kz0, kz1 = element_keep_m(place)
    # THE CLAIMS ADD AND THE FILLS DO NOT, because that is the order they are
    # built in (`place_elements`): an `end` block and a `cross` counter each
    # take a band out of the length and hand the rest on, while a `rank` or a
    # `cell` run takes what is left.  Summing them was the third thing building
    # this found -- `earharts` is (hospitality, food_service, recreation), so a
    # counter across the room AND a bar island behind it, and with the two
    # taking the max the bar reported `want 1, got 0`.
    claim, fill = 0.0, 0.0
    for _n, span_z, _x, _h, kind in els:
        if kind == "island":
            claim += span_z + 2 * AISLE_M
        elif kind == "cross":
            claim += 3 * span_z + 3.20
        elif kind == "end":
            claim += span_z + AISLE_M + 1.60
        elif kind == "rank":
            fill = max(fill, 3 * (span_z + ROW_GAP_M) - ROW_GAP_M + 1.20)
        elif kind == "cell":
            fill = max(fill, 2 * (span_z + CELL_PITCH_M) - CELL_PITCH_M + 1.20)
    return claim + fill + kz0 + kz1


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

# ---------------------------------------------------------------------------
# WHAT SHAPE EACH FIXTURE ACTUALLY IS -- INV-130
# ---------------------------------------------------------------------------
# Every one of the 45 fixture names above used to be emitted as a single call
# to `_box`, so a "fusion containment vessel" was a rectangular pier and a
# "fabrication furnace" was a slab. `docs/AAA-STANDARD.md` defines CRAFT 1 as
# *"a box primitive standing in for a named object"*; `docs/aaa-scorecard.json`
# scores `generated_rooms` at exactly that, over 58% of the station.
#
# `dressing.MACHINES` supplies fifteen parametric machines. This table says
# which one each fixture is, and it is the whole of the mapping -- there is no
# per-room special case, because the same table has to move all 78 rooms at
# once or it is the wrong architecture (`dressing.py` docstring, session 3u).
#
# THE KIND IS CHOSEN FROM WHAT THE OBJECT IS, NOT FROM ITS NAME. A "coolant
# manifold" and a "charging manifold" are both banks of pipe on brackets; a
# "switchgear cubicle", a "signal rack", a "patch panel" and a "suit locker
# bank" are all cabinet line-ups with doors; a bund kerb and a dais are both
# low platforms and get the cheapest machine in the kit, because no
# articulation finer than the step itself would read on a 0.45 m object.
#
# `_selftest` asserts this table covers every name in FIXTURES and
# PLACE_FIXTURES in both directions, so a fixture added without a shape is a
# build failure rather than a box that quietly comes back.
MACHINE_KIND = {
    # --- archetype scenery ---------------------------------------------
    "furnace_stack": "furnace",       # body, charge door, lifting gear, flue
    "plant_column": "vessel",
    "service_duct": "duct",
    "service_riser": "vessel",
    "racking_run": "rack",
    "gantry_rail": "duct",
    "equipment_gantry": "gantry",
    "fume_column": "cabinet",
    "cell_divider": "screen",
    "platform_edge": "kerb",
    "catenary_run": "duct",
    "back_shelving": "rack",
    "dais": "kerb",
    "screen_panel": "screen",
    "stall_frame": "screen",
    "awning_rail": "duct",
    "partition_screen": "screen",
    # --- V1 plan elements (PLAN_ELEMENTS) -------------------------------
    # Same rule as everything above: the kind is chosen from WHAT THE OBJECT
    # IS.  A conference table, a service counter, a desk rank and a bar back
    # are all casework bodies with a top, so all four are `counter`; a dais and
    # a planting bed are low platforms, which is `kerb`; a cell fin, a stall
    # frame and a shielded booth are all panelled screens.
    "fume_column_table": "counter",
    "fume_column_counter": "counter",
    "fume_column_desk_rank": "counter",
    "fume_column_console_rank": "console",
    "fume_column_bench_rank": "counter",
    "dais_delegate_bench": "seat",
    "dais_platform": "kerb",
    "dais_pew_row": "seat",
    "partition_screen_booth": "screen",
    "partition_screen_cell": "screen",
    "cell_divider_bay": "screen",
    "equipment_gantry_bay": "gantry",
    "stall_frame_row": "screen",
    "racking_run_rank": "rack",
    "plant_column_core": "vessel",
    "back_shelving_bar": "counter",
    # --- the named machines --------------------------------------------
    "reactor_plant_tank": "vessel",
    "shield_plant_frame": "block",     # a biological shield is a mass, not a machine
    "refuel_crane": "crane",
    "generator_plant_tank": "drum",    # "the generator torus IN SECTION" -- on its side
    "switchgear_plant_frame": "cabinet",
    "busbar_plant_conduit": "duct",
    "exchanger_plant_tank": "vessel",
    "header_plant_pipe": "pipe_bank",
    "condensate_plant_pipe": "duct",
    "manifold_plant_pipe": "pipe_bank",
    "pump_plant_frame": "skid",
    "return_plant_pipe": "duct",
    "bunker_plant_tank": "vessel",
    "bund_plant_frame": "kerb",
    "transfer_crane": "crane",
    "transfer_plant_frame": "rack",
    "hoist_crane": "crane",
    "suit_plant_frame": "cabinet",
    "charging_plant_pipe": "pipe_bank",
    "lock_plant_conduit": "duct",
    "umbilical_plant_pipe": "reel",
    "clamp_plant_frame": "skid",
    "gallery_plant_conduit": "duct",
    "plot_plant_frame": "console",
    "rack_plant_frame": "cabinet",
    "tray_plant_conduit": "duct",
    "patch_plant_conduit": "cabinet",
    "waveguide_plant_pipe": "duct",
}

# ---------------------------------------------------------------------------
# AND THE DECLARED PROPS ARE BOXES TOO -- INV-131
# ---------------------------------------------------------------------------
# `PROPS` above states it outright: *"(width, depth, height, mount)"* -- a prop
# IS a box, and `dressing.py`'s own docstring says the same thing about the old
# furniture. The machinery gate found it: with every FIXTURE articulated, the
# medlab still measured its machinery at 0.51x its own shell, because a medlab
# is a gantry (built) plus a diagnostic bed, a medcabinet, an isolation door
# and a monitor wall (four slabs). `interacts` is what a player can USE, so
# these are the objects a player is standing closest to when they use them.
#
# Same fifteen builders, same nine part names, prefix inherited so
# `budget.klass_of` still counts them as props rather than as fixtures.
PROP_KIND = {
    # seating and surfaces
    "table": "counter", "seat": "seat", "bench": "seat", "pew": "seat",
    "stool": "seat", "desk": "counter", "workbench": "counter",
    "lab_bench": "counter", "counter": "counter", "issue_counter": "counter",
    "serving_counter": "counter", "bar_counter": "counter",
    "duty_desk": "counter", "stall": "screen", "gaming_table": "counter",
    "cafe_table": "counter", "customs_desk": "counter",
    "reception": "counter", "delegate_bench": "seat",
    "speaking_position": "console", "market_stall": "screen",
    "public_gallery": "counter", "tray_dispenser": "cabinet",
    # sleeping and storage
    "bunk": "bed", "locker": "cabinet", "weapons_locker": "cabinet",
    "medcabinet": "cabinet", "parcel_locker": "cabinet",
    "tool_rack": "rack", "container": "crate", "cold_drawer": "bed",
    "cryo_pod": "bed", "grow_rack": "rack", "shower": "cabinet",
    "breather_dispenser": "cabinet", "planter": "crate",
    # terminals and controls -- a wall terminal is a bezel and a screen
    "babcom_terminal": "wallpanel", "console": "console",
    "reactor_console": "console", "furnace_control": "console",
    "irrigation_control": "wallpanel", "monitor_wall": "wallpanel",
    "tactical_display": "wallpanel", "credit_terminal": "console",
    "exchange_terminal": "console", "manifest_terminal": "console",
    "identicard_reader": "wallpanel", "intercom": "wallpanel",
    "breaker_lever": "wallpanel", "tank_gauge": "wallpanel",
    "valve": "wallpanel", "lift_call": "wallpanel",
    "level_plaque": "wallpanel", "neon_sign": "wallpanel",
    "menu_display": "wallpanel", "info_board": "wallpanel",
    "comms_channel": "wallpanel", "station_schematic_screen": "wallpanel",
    "welcome_board": "wallpanel", "dartboard": "wallpanel",
    "atmosphere_status_lamp": "wallpanel", "shrine": "cabinet",
    "shopfront": "screen", "barred_screen": "screen",
    "gallery_rail": "screen",
    # medical
    "diagnostic_bed": "bed",
    # doors and apertures -- fifteen slabs, and a door is what you stand at
    "door": "leaf", "office_door": "leaf", "cell_door": "leaf",
    "isolation_door": "leaf", "blast_door": "leaf", "welded_door": "leaf",
    "makeshift_door": "leaf", "lift_door": "leaf", "tram_door": "leaf",
    "bay_door": "leaf", "airlock_door": "leaf", "shuttle_door": "leaf",
    "gallery_door": "leaf", "building_door": "leaf", "viewport": "wallpanel",
    "barrier": "screen",
    # heavy plant and handling
    "cargo_crane": "crane", "crane": "crane", "catwalk": "kerb",
    "docking_clamp": "skid", "clamp": "skid", "handhold": "post",
    "path": "kerb", "pool_edge": "kerb", "deck_marking": "kerb",
    "bollard": "post", "standpipe": "post", "service_ladder": "screen",
    "brazier": "post", "launch_tube": "vessel", "pendant_lamp": "post",
    "bay_control_booth": "cabinet", "baggage_scanner": "gantry",
}

# Below this, a machine has no room to be one. `platform_edge` is declared with
# ZERO depth across x, which `_box` renders as twelve degenerate triangles and
# which no builder can articulate; anything that thin falls back to the box it
# already was rather than emitting slivers. Stated rather than silently
# handled, and counted by `_selftest`.
MACHINE_MIN_M = 0.05
# The infix that marks a nested machine part. Imported from the module that
# creates it rather than spelled twice -- two copies of one decision is the
# defect this repository keeps rediscovering.
_MACH = "_mp_"


def _fixture(v, t, g, name, lo, hi, seed, prefix="fix_", report=None):
    """Emit one fixture or prop instance as an articulated machine.

    Falls back to `_box` only for a declared dimension too small to hold one --
    `platform_edge` is 0.00 m across x and `deck_marking` is 0.01 m tall, and
    a builder given a zero extent emits slivers rather than detail.

    `report["machines"]` records (group, tri_lo, tri_hi, declared_lo,
    declared_hi) for every instance, because the containment invariant needs
    the box that was ASKED FOR and only this function knows it. Deriving it
    again in the self-test would be a second copy of the placement arithmetic,
    which is the failure mode this repository keeps rediscovering.
    """
    import dressing as _dress                                   # noqa: PLC0415
    table = PROP_KIND if prefix == "prop_" else MACHINE_KIND
    kind = table.get(name)
    t0 = len(t)
    if kind is None or min(hi[i] - lo[i] for i in range(3)) < MACHINE_MIN_M:
        _box(v, t, g, f"{prefix}{name}", lo, hi)
        built = False
    else:
        _dress.machine(v, t, g, kind, f"{prefix}{name}", lo, hi,
                       f"{seed}-{name}")
        built = True
    if report is not None:
        report.setdefault("machines", []).append(
            (f"{prefix}{name}", kind if built else None, t0, len(t),
             tuple(lo), tuple(hi)))
    return built

# ---------------------------------------------------------------------------
# PLACE_FIXTURES -- machinery for the rooms that are one of a kind
# ---------------------------------------------------------------------------
# An ARCHETYPE describes a kind of room and there are eleven of them for 128
# places, which is the right ratio for a medlab or a store and the wrong one
# for the only fusion reactor on the station. `FIXTURES` above says what an
# industrial room contains *in general* -- a furnace stack, a plant column, a
# service duct -- and a reactor hall furnished from it is CLAUDE.md's
# "Fabrication furnaces" defect one level up: a plant room standing in for a
# named machine.
#
# So a place may override its archetype's scenery entirely. The archetype still
# decides the SHELL -- height, density, wall and deck material, light fittings
# -- because that is genuinely shared; only the machinery is per place.
#
# WHY THE NAMES ARE COMPOUND, and it is a real constraint rather than a style.
# `materials.resolve` matches a group name against bind FRAGMENTS, longest
# match wins, and `station/test_materials_layer3.py` asserts that every group
# this generator emits resolves. `station/materials.py` is not this session's
# file, so a fixture called `fix_containment_vessel` would ship 10 rooms of
# unmaterialled surface and take that gate down with it -- verified: all eight
# natural names resolve to None today.
#
# The rule adopted instead: **the bound fragment names the MATERIAL and the
# qualifier names the OBJECT.** `fix_reactor_plant_tank` is a clad pressure
# vessel (`clad_services`, the plant tankage material), `fix_shield_plant_frame`
# is oxide steel structure (`steel_gantry_oxide`), `fix_busbar_plant_conduit`
# is the conduit metal. Those are the surfaces these objects genuinely have,
# and the vocabulary is `station/plant.py`'s own, so the names are honest even
# though they read backwards. The materials.py delta that would let them be
# renamed is reported to whoever owns that file.
#
# Dimensions are (name, width_along_z, depth_across_x, height, kind). Height
# 0.00 means full height, exactly as in FIXTURES. Everything here is
# extrapolation -- INV-104 -- constrained by three things the self-test
# measures rather than asserts in prose: the piece must fit under its room's
# ceiling, the room must still be crossable by a 0.9 m walker, and no two
# solids may occupy the same cubic metre.
#
# AND ONE ARITHMETIC CONSTRAINT WORTH STATING, because it is not obvious and it
# fires as an interpenetration failure a long way from its cause. `build`
# repeats a fixture `nz = int(room_len / FIXTURE_PITCH_M)` times in slots of
# `room_len / nz`, and `bay_span_m` grows the room to hold the widest of them.
# A piece wider than about 4.2 m along z therefore ends up in a slot narrower
# than itself and overlaps its own next instance. Nothing here exceeds 4.0 m
# along z for that reason; depth across x is unconstrained and is where these
# machines get their bulk.
PLACE_FIXTURES = {
    # --- Yellow: the power train ------------------------------------------
    # A fusion containment drum, the biological shield either side of it, and
    # the refuelling crane that has to reach the head of the vessel. 4 m across
    # is the smallest drum that reads as a reactor at a 7.5 m ceiling; it runs
    # full height because a containment vessel penetrates the deck above.
    # 6.20 m, NOT full height, and the self-test is why: an `over` run is
    # centred on the free channel and a `spine` sits on the centreline, so a
    # full-height vessel and the crane that serves it are the same cubic metre.
    # Which is also true of the real object -- a crane has to reach OVER the
    # head of the vessel it refuels -- so the arithmetic and the machine agree.
    "reactor_hall": (
        ("reactor_plant_tank",     4.00, 4.00, 6.20, "spine"),
        ("shield_plant_frame",     3.20, 1.60, 0.00, "flank"),
        ("refuel_crane",           1.10, 1.10, 0.90, "over"),
    ),
    # The generator torus in section, its switchgear cubicles against one
    # flank, and the bus duct that carries the output away overhead. Height
    # 3.40 rather than full: a machine you look down on across a hall reads as
    # a machine; one that touches the ceiling reads as a wall.
    "generator_hall": (
        ("generator_plant_tank",   3.60, 3.20, 3.40, "spine"),
        ("switchgear_plant_frame", 2.40, 1.10, 2.30, "flank"),
        ("busbar_plant_conduit",   0.60, 0.60, 0.55, "over"),
    ),
    # Exchanger drums on the centreline, the coolant headers that feed them
    # standing full height against a flank, and the condensate main overhead.
    "heat_exchanger_hall": (
        ("exchanger_plant_tank",   3.00, 2.60, 6.40, "spine"),
        ("header_plant_pipe",      2.40, 0.90, 0.00, "flank"),
        ("condensate_plant_pipe",  0.80, 0.80, 0.70, "over"),
    ),
    # NO SPINE, and that is the room. A gallery at 0.173 g is a crawlway you
    # move along beside the pipework, not a hall you cross: both flanks carry
    # machinery and the centre is the only floor there is.
    "coolant_gallery": (
        ("manifold_plant_pipe",    2.60, 0.85, 0.00, "flank"),
        ("pump_plant_frame",       2.00, 1.10, 1.40, "flank"),
        ("return_plant_pipe",      0.70, 0.70, 0.60, "over"),
    ),
    # Slush tanks against both flanks with a bund kerb round their feet, and a
    # transfer crane over the aisle. `00-MASTER.md` Sec.2 item 1.
    "fuel_bunkerage": (
        ("bunker_plant_tank",      3.20, 2.20, 0.00, "flank"),
        ("bund_plant_frame",       3.20, 0.60, 0.45, "flank"),
        ("transfer_crane",         0.90, 0.90, 0.70, "over"),
    ),

    # --- Green: under the dorsal cargo rail --------------------------------
    # Racking down one flank, the rail's transfer carriage frame down the
    # other, and the hoist that moves a container between them.
    "cargo_transfer_deck": (
        ("racking_run",            1.10, 2.60, 4.20, "flank"),
        ("transfer_plant_frame",   3.00, 1.20, 2.40, "flank"),
        ("hoist_crane",            0.70, 0.70, 0.60, "over"),
    ),

    # --- Blue: the pressure boundary ---------------------------------------
    # A suit rack bank and the charging manifold that services it, either side
    # of the lane a suited person walks down to the lock.
    "eva_lock_blue": (
        ("suit_plant_frame",       2.20, 0.85, 2.30, "flank"),
        ("charging_plant_pipe",    2.20, 0.45, 1.90, "flank"),
        ("lock_plant_conduit",     0.45, 0.45, 0.35, "over"),
    ),
    # Umbilical reels on one flank, the clamp actuator housings on the other.
    "mooring_gallery": (
        ("umbilical_plant_pipe",   1.60, 1.10, 1.80, "flank"),
        ("clamp_plant_frame",      2.20, 0.90, 1.60, "flank"),
        ("gallery_plant_conduit",  0.50, 0.50, 0.40, "over"),
    ),
    # A plot table on the centreline with the fire-control racks behind it.
    "gunnery_control": (
        ("plot_plant_frame",       2.40, 1.40, 1.05, "spine"),
        ("rack_plant_frame",       2.00, 0.80, 2.10, "flank"),
        ("tray_plant_conduit",     0.40, 0.40, 0.30, "over"),
    ),
    # Signal racks and patch panels on both flanks, and the waveguide run that
    # leaves the room for the pylon overhead.
    "comms_operations": (
        ("rack_plant_frame",       2.00, 0.80, 2.10, "flank"),
        ("patch_plant_conduit",    2.00, 0.35, 1.90, "flank"),
        ("waveguide_plant_pipe",   0.55, 0.55, 0.45, "over"),
    ),
}

# ---------------------------------------------------------------------------
# Light fittings: the reason a room is not black
# ---------------------------------------------------------------------------
# LAYER 4. Until this table existed, sixty-eight of the station's 118 locations
# rendered BLACK -- `export_scene.fixture_lights` makes one source per tagged
# `light_*` group and this generator tagged none, so the only things that
# glowed in a rooms.py room were seventeen terminal screens. That is not a
# tuning problem; it is a missing object, the same class of defect FIXTURES was
# added for.
#
# NOTHING HERE IS INVENTED FROM SCRATCH. Three agents measured every light
# source visible in the reference frames in session 3n and the results are
# committed in docs/layer4-lighting/*.json -- colour, colour temperature,
# relative energy, range, spacing, shadow, and the frame each came from. What
# this table does is decide WHICH MEASURED FITTING EACH ARCHETYPE USES, and
# that mapping is the extrapolation (INV-036). The alternative -- authoring
# eleven new lamp colours by eye -- is exactly the unmarked invention the
# project's first hard rule forbids.
#
# The mapping, and why:
#
#   industrial  <- bay_flood + service_wall_tube. A 7.5 m plant hall is lit
#                  the way a docking bay is: a few cool high-bay floods and
#                  cold blue tube trim on the walls.
#   store       <- bay_flood + the concourse deck channel. Same high bay; the
#                  deck run is what gives a cargo hall its length.
#   transit     <- concourse_deck_spot + deck channel. The measured concourse.
#   hospitality <- bar_pendant_lamp + casino_bar_backlight. Doug's Dugout and
#                  the Casino are the two measured hospitality interiors and
#                  they agree: warm pendants over the tables, a cyan strip
#                  behind the bar, and darkness in between.
#   worship     <- cc_dais_key + cc_wall_course. A key on the dais and cold
#                  courses on the walls -- the chapel's dais is the only thing
#                  in the room that should be lit.
#   medical     <- fa_batten + service_wall_tube. The only measured NEUTRAL
#                  white source in the whole set (S 0.010, clipping in all
#                  three channels) belongs over a medlab bed.
#   research    <- fa_batten + cc_wall_course.
#   detention   <- fa_batten's register behind a guard + cc_pit_indicator.
#                  The brig is the one archetype with NO measured frame; see
#                  `light_cage_lamp` in materials.py for what is declared.
#   commerce    <- zoc_downlight_overhead + zoc_stall_light. The Zocalo.
#   office      <- wr_soffit_blade + wr_wall_strip_bank. The War Room is the
#                  measured working office and its light is warm, wall-mounted
#                  and low -- not a ceiling grid.
#   generic     <- light_downlight + deck channel: the corridor kit's own
#                  fittings, so an unclassified room reads as station fabric.
#
# (name, w_along_z, d_along_x, h, kind, mount_y_m). Kinds:
#   "ceiling" -- two rows either side of the free overhead channel
#   "key"     -- ONE fitting on the centreline, over whatever the spine holds
#   "course"  -- a horizontal band on both long walls at mount_y_m
#   "festoon" -- small bulbs strung along the channel edges at mount_y_m
#   "deck"    -- discrete lit panels inlaid down the channel at deck level
LIGHTS = {
    "industrial":  (("light_highbay", 0.80, 0.80, 0.34, "ceiling", 0.0),
                    ("light_service_tube", 0.11, 0.13, 1.43, "course", 0.95)),
    "store":       (("light_highbay", 0.80, 0.80, 0.34, "ceiling", 0.0),
                    ("light_deck_channel", 1.20, 0.90, 0.02, "deck", 0.0)),
    "transit":     (("light_platform_pool", 0.62, 0.62, 0.22, "ceiling", 0.0),
                    ("light_deck_channel", 1.20, 0.90, 0.02, "deck", 0.0)),
    "hospitality": (("light_pendant", 0.46, 0.46, 0.30, "ceiling", 0.0),
                    ("light_bar_backlight", 1.60, 0.06, 0.16, "course", 1.25)),
    "worship":     (("light_dais_key", 0.55, 0.55, 0.28, "key", 0.0),
                    ("light_wall_course", 2.40, 0.08, 0.22, "course", 1.15)),
    "medical":     (("light_ceiling_batten", 1.80, 0.34, 0.12, "ceiling", 0.0),
                    ("light_service_tube", 0.11, 0.13, 1.43, "course", 0.95)),
    "research":    (("light_ceiling_batten", 1.80, 0.34, 0.12, "ceiling", 0.0),
                    ("light_wall_course", 2.40, 0.08, 0.22, "course", 1.15)),
    "detention":   (("light_cage_lamp", 0.40, 0.40, 0.18, "ceiling", 0.0),
                    ("light_indicator_red", 0.10, 0.05, 0.10, "course", 2.10)),
    "commerce":    (("light_market_pool", 0.55, 0.55, 0.24, "ceiling", 0.0),
                    ("light_stall_festoon", 0.06, 0.06, 0.06, "festoon", 2.29)),
    "office":      (("light_soffit_blade", 1.20, 0.28, 0.14, "ceiling", 0.0),
                    ("light_wall_strip_bank", 0.09, 0.06, 0.34, "course", 1.20)),
    "generic":     (("light_downlight", 0.26, 0.10, 0.22, "course", 0.88),
                    ("light_deck_channel", 1.20, 0.90, 0.02, "deck", 0.0)),
}

# How many times a course repeats UP the wall, and at what vertical pitch.
# Three of the four measured wall fittings are ganged in more than one course
# and saying so is most of what makes a wall read as lit rather than as having
# a strip on it. All three numbers are measured:
#   cc_wall_course        "Four horizontal courses per side wall ... vertical
#                          pitch 1.2 m measured", from y ~1.15
#   wr_wall_strip_bank    "two heights ... vertical pitch ~1.4 m", the lower at
#                          seated shoulder height ~1.2 m
#   service_wall_tube     "two courses -- an upper run hung off the overhead
#                          truss and a lower run at head height". Only the
#                          LOWER is placed: the upper hangs from a truss this
#                          generator does not build, and inventing the truss to
#                          hang it from would be a layer-2 change made inside
#                          layer 4.
LIGHT_COURSES = {"light_wall_course": (4, 1.20),
                 "light_wall_strip_bank": (2, 1.40),
                 "light_service_tube": (1, 0.0)}

# Spacing along the room, in metres, as MEASURED. Where a frame gives a
# spacing this is that number; where it does not, the derivation is stated.
LIGHT_PITCH_M = {
    # measured directly
    "light_downlight": 3.6,          # corridor_kit.json, spacing_m 3.6
    "light_wall_strip_bank": 1.4,    # command_working.json: banks of 4-8 bars
                                     # at ~1.4 m. The BAR is 0.09 wide, so this
                                     # is the bank pitch and the bars inside a
                                     # bank are not modelled individually.
    "light_pendant": 2.2,            # public_social.json, one per table
    "light_wall_course": 2.60,       # the 1.2 m in command_working.json is the
                                     # VERTICAL pitch of four courses, not an
                                     # along-wall spacing -- the placement says
                                     # each course runs continuously from
                                     # z -3.6 to +5.04 m. So the along-wall
                                     # figure is a construction joint: 2.40 m
                                     # sections with a 0.20 m gap.
    # derived, and the derivation is the argument
    "light_service_tube": 2.4,       # "they flank the corridor in pairs"; no
                                     # pitch measured. Set to two thirds of the
                                     # 3.6 m deck frame so a pair lands between
                                     # every rib rather than on one.
    "light_stall_festoon": 0.156,    # MEASURED AS A RATIO, not a length:
                                     # zocalo.webp blob analysis gives a median
                                     # nearest-neighbour spacing of 2.6 bulb
                                     # diameters. The bulb here is 0.06 m, so
                                     # the pitch is 0.06 x 2.6. Taking the
                                     # JSON's 0.08 m literally would assume
                                     # their bulb size rather than this one's.
    "light_platform_pool": 3.6,      # no spacing measured; the pool is 1.57 m
                                     # across and the deck frame is 3.6, so one
                                     # pool a bay with dark deck between them --
                                     # which is what the frame shows.
    "light_ceiling_batten": 3.6,     # one batten a deck frame
    "light_cage_lamp": 3.0,
    "light_soffit_blade": 3.0,
    "light_indicator_red": 1.6,
    "light_deck_channel": 1.6,       # "discrete lit deck panels", 1.20 long
    "light_bar_backlight": 1.8,      # "continuous horizontal strip ... ~10 m
                                     # run": one 1.60 m section every 1.80 m
                                     # reads continuous and leaves the joint.
}
# Two fittings' spacing scales with MOUNTING HEIGHT rather than being fixed,
# because both were measured in volumes far taller than the room they are being
# put in and a fixed spacing would carry the wrong floor coverage across.
#   bay_flood:               11.0 m spacing at a 18.0 m mount = 0.611
#   zoc_downlight_overhead:   2.7 m spacing at a  7.2 m mount = 0.375
LIGHT_PITCH_RATIO = {"light_highbay": 0.611, "light_market_pool": 0.375}

# Wall ribs. Every B5 interior in the reference is heavily articulated: a flat
# wall run from floor to a 7.5 m soffit is the single strongest tell that a
# volume is a placeholder box. Ribs are structural, cheap, and true of the
# sets. Pitch is derived from the deck frame in `interior.py` rather than
# picked, so a schema change moves them.
RIB_D_M = 0.16
RIB_W_M = 0.45
# Articulation bands and grids -- INV-073. Domestic/industrial fit-out
# proportions; nothing in canon fixes them, and a room without them reads as a
# box, which is what the owner saw.
SKIRT_H_M = 0.14
SKIRT_D_M = 0.035
DADO_H_M = 0.95
BAND_H_M = 0.09
BAND_D_M = 0.030
CORNICE_H_M = 0.16
CORNICE_D_M = 0.055
CORNICE_DROP_M = 0.75
DECK_BAY_M = 0.40
JOINT_W_M = 0.05
SOFFIT_BAY_M = 0.40
TEE_W_M = 0.07
TEE_D_M = 0.04
CONDUITS = 4
CONDUIT_R_M = 0.055
PANEL_D_M = 0.045

# ---------------------------------------------------------------------------
# THE PLATE MODULE -- imported from the corridor kit, never restated. INV-210.
# ---------------------------------------------------------------------------
# `articulate()`'s own docstring already argues that "there is no reason a bar,
# a quarters unit or a customs hall should be articulated differently -- they
# are the same station, built by the same people". The same argument applies
# one level up: there is no reason a room's wall should be built to a different
# module than the corridor wall outside its door, and until now it was.
#
# WHAT WAS WRONG, measured rather than asserted. `station/density.py --shell`
# scores each shell surface against the corridor kit's own:
#
#     surface        room lam      kit lam    room facet p50   kit facet p50
#     war_room wall     5.48         3.62         4.33 m          0.99 m
#     cargo    wall     3.48         3.62         6.43 m          0.99 m
#     fabric.  wall     2.98         3.62         9.51 m          0.99 m
#     war_room deck     6.70         4.12         7.25 m          0.57 m
#
# The rooms were AT OR ABOVE the corridor on line density and four to ten times
# coarser on facet size, and that pair is the whole finding: `articulate` ran a
# skirt, a dado, a rail, a cornice, six mullions a bay and four conduits round
# every wall -- continuous elements, enormous line, negligible area -- and left
# the field between them a single box. `docs/shell/before-office-half.png` is
# what that is: 2 x 1.5 m pale rectangles joined by hairline scribes, nothing
# inside any of them. `docs/aaa-scorecard.json` had written the words for two
# sessions -- *"one unbroken pale panel across 4 m with a scribed line and no
# joint"* -- and no gate could produce them as a number.
#
# The corridor kit was already right. `interior_kit.wall_assembly` has plated
# both its fields since it was written: "Every course is plated with recessed
# seams -- the exterior hull's plating language seen from the other side, which
# it has to be, being the same plate." The room generator simply never picked
# the vocabulary up.
#
# So the module comes from `interior_kit.PROVISIONAL`, whose wall build-up is
# read off `grey level 1.webp` -- the authority-1 frame that defines 1.00 for
# this project, and the one `docs/reference-values.md` §1 measures rung by rung.
# Nothing here is a new number: `wall_plate_l_m`, `wall_seam_m`,
# `wall_plate_proud_m`, `wall_plate_courses` and `deck_panel_l_m` are the kit's,
# and the COURSE HEIGHT is solved from them rather than picked -- see below.
SHADOW_GAP_M = 0.06        # the skirt's dark line: bare substrate under an
                           # overhanging field. `docs/reference-values.md` §1
                           # measures the reference's dark horizontals at 5%
                           # of the key the wall beside them gets and concludes
                           # they are "a deep, narrow reveal with an occluding
                           # lip, not a 20 mm groove". The lip is the field's
                           # own PANEL_D_M standing 10 mm proud of the skirt.
DECK_TILE_M = 0.62         # interior_kit.deck_grid's own tile, and the same
                           # relationship: proud tiles, recessed joints.
# The lip at the bottom of each plate course. Proportioned off the kit's own
# rail band rather than picked: `wall_rail_proud_m` is 0.10 and
# `wall_plate_proud_m` is 0.045, so the corridor's one nosing stands 55 mm
# proud of the plates it interrupts, and the height is `wall_rail_frac` of the
# corridor's wall (0.075 x 2.5 m = 0.19 m) halved, because this repeats every
# course where the corridor's happens once.
NOSING_PROUD_M = (ik.PROVISIONAL["wall_rail_proud_m"]
                  - ik.PROVISIONAL["wall_plate_proud_m"])
NOSING_H_M = 0.5 * ik.PROVISIONAL["wall_rail_frac"] * (
    ik.PROVISIONAL["ceiling_height_m"] - ik.PROVISIONAL["wall_chamfer_m"])


def kit_plate_module(scale=1.0):
    """(plate length, course height, seam, proud) for a room wall.

    THE COURSE HEIGHT IS SOLVED, NOT COPIED, and that is what makes this work
    on a 7.5 m foundry wall as well as on a 2.9 m office one. `PROVISIONAL`
    states `wall_plate_courses = 3`, but 3 is a count over the corridor's own
    upper field, not a property of a plate. Reproducing the corridor's build-up
    arithmetic gives the field height that count divides, and the quotient is
    the size of one plate -- 0.446 m -- which is then laid as many times as the
    room is tall. A fixed count would stretch a plate to 2 m in a foundry,
    which is the mistake this whole module exists to stop making.

    `scale` is `articulate`'s existing coarsener and multiplies both pitches,
    so a 3 m quarters unit is not given a 12 m ward's plate count.
    """
    p = ik.PROVISIONAL
    wall_h = p["ceiling_height_m"] - p["wall_chamfer_m"]
    sk = wall_h * p["wall_skirt_frac"]
    dado_top = sk + wall_h * p["wall_dado_frac"]
    rail_top = dado_top + wall_h * p["wall_rail_frac"]
    course = (wall_h - rail_top) / p["wall_plate_courses"]
    return (p["wall_plate_l_m"] * scale, course * scale,
            p["wall_seam_m"], p["wall_plate_proud_m"])


def _plate_field(v, t, g, name, axis, face, sign, a0, a1, y0, y1,
                 plate_l, course_h, seam, proud, skip=None, nosing=None):
    """A field of proud plates with recessed seams between them.

    `interior_kit.wall_assembly.plated()`, generalised to either wall axis and
    to a field of any height. `axis` is "x" for a side wall (`face` is the x of
    its inner surface and the field runs along z between `a0` and `a1`) or "z"
    for an end wall. `sign` is which way the plate stands proud of `face`.

    WHY A PLATE AND NOT A SCRIBED LINE. A line drawn on a wall does not divide
    the wall: the surface behind it is still one plane, so `density.analyse`
    unions it back into one facet and, more to the point, so does the eye at
    half distance. A plate is a separate piece of surface with a real crease
    round it. That is why this is 12 triangles a plate and not a texture.

    `skip(lo, hi)` -- the door. A plate that would cross an aperture is not
    emitted, for the same reason `articulate`'s bands split round one: a hole
    in a wall is a hole in everything that wall carries.

    `nosing` -- (group name, proud, height). A COURSE NEEDS A LIP OR ITS JOINT
    IS A HAIRLINE, and the first after-frame said so: with every plate at the
    same 45 mm and a 38 mm seam, the horizontal joints rendered as scribed
    lines rather than as the deep dark bands the reference carries.
    `docs/reference-values.md` §1 measures both halves of what is missing --
    rung 14, *"rail nosing, proud lit edge"* at x1.309 of the wall, and rung 5,
    *"rail band, dark reveal"* at x0.298 -- and its §1 fit says plainly that no
    albedo reproduces the second, because the ratio varies with the light. The
    nosing is the occluder that makes it vary: one strip per course, running
    the field's length, standing proud of the plates so the joint under it is
    shielded. Twelve triangles a course, against twelve a plate.
    """
    span, hgt = a1 - a0, y1 - y0
    if span <= 2.2 * seam or hgt <= 2.2 * seam:
        return
    n_a = max(1, int(round(span / plate_l)))
    n_c = max(1, int(round(hgt / course_h)))

    def emit(p0, p1, cy0, cy1, depth, nm):
        lo = (face - sign * depth, cy0, p0)
        hi = (face, cy1, p1)
        if axis == "z":
            lo = (p0, cy0, face - sign * depth)
            hi = (p1, cy1, face)
        lo, hi = (tuple(min(a, b) for a, b in zip(lo, hi)),
                  tuple(max(a, b) for a, b in zip(lo, hi)))
        if skip is not None and skip(lo, hi):
            return
        _box(v, t, g, nm, lo, hi)

    for c in range(n_c):
        cy0 = y0 + hgt * c / n_c
        cy1 = y0 + hgt * (c + 1) / n_c
        for i in range(n_a):
            p0 = a0 + span * i / n_a
            p1 = a0 + span * (i + 1) / n_a
            emit(p0 + seam, p1 - seam, cy0 + seam, cy1 - seam, proud, name)
        if nosing is not None and cy1 - cy0 > 4.0 * nosing[2]:
            nm, nproud, nh = nosing
            emit(a0, a1, cy0 + seam, cy0 + seam + nh, nproud, nm)


def _plate_deck(v, t, g, name, y_face, sign, x0, x1, z0, z1, tile, seam,
                proud):
    """The same construction laid flat: proud tiles, recessed joints.

    THE ROOM DECK HAD IT INVERTED, and that is why it measured as one 7 m
    facet while looking tiled. `articulate` laid *proud ribs on a continuous
    plane*, so the plane was the surface and the ribs were applied to it;
    `interior_kit.deck_grid` lays *proud tiles over a substrate*, so the tiles
    are the surface and the substrate shows only in the joints. The second is
    what both corridor references show, and it is also the kinder of the two to
    a character capsule -- `station/collision.py` exists because 22 mm proud
    ribs wedged one.

    The walking surface does not move: the tile tops sit exactly on `y_face`
    (y = 0 for a deck, y = ceil for a soffit) and the substrate is set back
    behind them, so every height in the room is what it was.

    `ceil`, NOT `round`, and it is worth one line of why. A tile module is a
    CEILING on coarseness -- it is the size the gate measures against -- so
    rounding the count DOWN makes the tile bigger than the module it came from.
    `density.py --shell` caught exactly that on four decks: `lake_pool` at
    0.85 m against a 0.62 m tile, and three more at 0.59-0.60 m missing their
    floor by 2%. Rounding up can only make a tile smaller than the reference,
    which is a direction the floor does not care about.
    """
    nx = max(1, int(math.ceil((x1 - x0) / tile - 1e-9)))
    nz = max(1, int(math.ceil((z1 - z0) / tile - 1e-9)))
    for i in range(nx):
        px0 = x0 + (x1 - x0) * i / nx
        px1 = x0 + (x1 - x0) * (i + 1) / nx
        for j in range(nz):
            pz0 = z0 + (z1 - z0) * j / nz
            pz1 = z0 + (z1 - z0) * (j + 1) / nz
            _box(v, t, g, name,
                 (px0 + seam, min(y_face, y_face - sign * proud), pz0 + seam),
                 (px1 - seam, max(y_face, y_face - sign * proud), pz1 - seam))


# The hour the whole station is generated at. 1300 is a working day, which is
# what the reference frames show. `populace` reads each place's own busy and
# dead windows off `npc/schedule.py`, so this one number moves all 118.
STATION_HOUR = 13.0
DRESS_DENSITIES = (1.0, 0.75, 0.5, 0.3, 0.15, 0.0)
_TRIM_SUFFIXES = ("_skirt", "_dado", "_rail", "_cornice", "_deck_joint",
                  "_soffit_tee", "_conduit", "_panel", "_mullion")
# The shell of a room, as opposed to the things standing in it. Anything not
# ending in one of these is an OBJECT: a workbench, a till, a shelf run, a chair.
_SHELL_SUFFIXES = ("_deck", "_soffit", "_wall", "_rib") + _TRIM_SUFFIXES


def is_solid(name):
    """Is this group something a body walks into, rather than the room itself?

    ONE DEFINITION, USED TWICE, and that is the whole point of its existing.
    `build`'s density trial asks "can a body still cross this room" of one set of
    groups, and `collision.prop_boxes` builds what the body actually collides
    with. Those were different sets for exactly as long as it took to notice:
    collision took only the `dress_` furniture, so a player walked through every
    fixture -- a bar's till, a medlab's scanner -- while the walkability
    guarantee had been computed as though they were solid. A guarantee computed
    against a different world than the one that ships is not a guarantee.

    PEOPLE ARE NOT FURNITURE. `npc_` groups are excluded, and the first version
    of this did not exclude them -- which baked all 134 inhabitants into the
    station's static collision as immovable obstacles. A person you bump into
    and who never moves is worse than one you walk through: it is a statue where
    a resident should be, and it is permanent, because static collision is
    generated once. NPCs get their own capsules when they get their own
    movement. Measured with them solid, `mess_hall` and `happy_daze` read
    unwalkable; they are not, and the rooms were never the problem.
    """
    return not name.endswith(_SHELL_SUFFIXES) and not name.startswith("npc_")
TRIM_MAX_PROUD_M = 0.10          # a step you do not trip on
TRIM_HEAD_M = 2.0
MULLIONS_PER_BAY = 6
MULLION_W_M = 0.06
MULLION_D_M = 0.035                # above this it is out of the walking envelope


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
    # AND THE PLAN ELEMENTS, for the same reason the dressing had to be added
    # to `bay_span_m`: a bay sized for its props and then given a rank of desks
    # down the middle is a bay whose desks do not fit, and this generator's
    # answer to that is to drop them -- which is variety measured and not
    # built.  `element_cross_m` is asked here so there is ONE statement of the
    # cross-section and both the sizing and the placing read it.
    el = element_cross_m(place)
    if el:
        need = max(need, inset[0] + inset[1] + el)
    return need, start[0], start[1]


def rib_pitch_m(place):
    """Structural rib spacing -- one per frame bay, floor to soffit."""
    return max(2.4, min(4.2, ceiling_m(place) * 0.62))


def fixtures_for(place):
    """Scenery for one room: its own set if it has one, else its archetype's.

    Height 0.00 means full height, resolved against this room's ceiling rather
    than the archetype's nominal, so a full-height piece in a 3.4 m lock is
    3.4 m and the same declaration in a 7.5 m reactor hall is 7.5 m.
    """
    fx = PLACE_FIXTURES.get(place["key"]) or FIXTURES.get(archetype(place), ())
    # AN ARCHETYPE'S SPINE AND A PLAN ELEMENT WANT THE SAME CUBIC METRE, and
    # the archetype loses, because the element is what this PLACE is for and
    # the spine is what its KIND of place is for.  Measured: with both in,
    # `alpha_substation`'s power core reported `want 1, got 0` -- silently not
    # built, because `industrial` puts a furnace stack down the centreline of
    # every room in the sector and a substation does not have a furnace in it.
    # A place with its OWN fixtures (`PLACE_FIXTURES`) keeps them: those are
    # hand-authored for one named room and are not a kind's default.
    if (place["key"] not in PLACE_FIXTURES
            and any(k in ("island", "rank", "cross")
                    for *_r, k in elements_for(place))):
        fx = tuple(f for f in fx if f[4] != "spine")
    out = []
    for name, w, d, h, kind in fx:
        out.append((name, w, d, ceiling_m(place) if h == 0.0 else h, kind))
    return tuple(out)


# A ROOM'S OWN FITTINGS, for the same reason it may have its own scenery.
# Measured, not guessed: the first render of `coolant_gallery` (industrial, and
# so lit by `light_highbay`) came back with the entire ceiling clipped white.
# `light_highbay` is `bay_flood`, measured at an **18 m mount** in a docking
# bay, and `LIGHT_PITCH_RATIO` scales its SPACING with ceiling height but
# nothing scales its ENERGY -- so in a 3.20 m gallery it lands floods 1.95 m
# apart, two metres over a person's head, and the room is a lightbox.
#
# The replacement is not new: `light_ceiling_batten` is the fitting `medical`
# and `research` already use at a 3.6 m pitch, which is what a 3.2 m service
# gallery has. It keeps the industrial `light_service_tube` course, so the room
# still reads as plant rather than as a ward.
#
# ONLY EXISTING FITTING NAMES ARE ALLOWED HERE, and that is a hard constraint
# rather than a preference: `tools/export_scene.py` asserts that every `light_`
# group rooms.py emits is either a measured source in FIXTURE_LIGHTING or one
# of four measured emissive-only fittings, and that file is not editable from
# this session. A new lamp name would take that gate down. Asserted below.
PLACE_LIGHTS = {
    "coolant_gallery": (
        ("light_ceiling_batten", 1.80, 0.34, 0.12, "ceiling", 0.0),
        ("light_service_tube", 0.11, 0.13, 1.43, "course", 0.95)),
}


def lights_for(place):
    """Light fittings for one room: its own set if it has one, else its
    archetype's, verbatim from LIGHTS."""
    return (PLACE_LIGHTS.get(place["key"])
            or LIGHTS.get(archetype(place), LIGHTS["generic"]))


def light_pitch_m(name, place):
    """Spacing between repeats of one fitting, in metres.

    Height-scaled where the fitting was measured in a volume much taller than
    the room it is being placed in -- see LIGHT_PITCH_RATIO. Floored at 1.2 m
    so a low ceiling cannot pack floods shoulder to shoulder.
    """
    ratio = LIGHT_PITCH_RATIO.get(name)
    if ratio is not None:
        return max(1.2, ratio * ceiling_m(place))
    return LIGHT_PITCH_M[name]


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


def _fit_bay(place, w_min, l_min):
    """The contents-derived minimum, grown to a whole fraction of the location.

    NEVER LARGER THAN THE LOCATION, which is what makes this safe for
    `station/deck.py`: that module sizes every room slot as
    `min(room_extent_m, bay_span_m)` and `rooms.build` uses the same two lines,
    so the assembler and the geometry agree by construction (hard rule 4). A bay
    that came back bigger than its own footprint would break that agreement in
    the one direction it cannot survive.
    """
    w_full, l_full, _r = _place_extent(place)
    return whole_bays(w_full, w_min), whole_bays(l_full, l_min)


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

    # AND THE FURNITURE THAT IS GOING TO BE PUT IN IT. `dressing.py` dresses
    # every wall of every room, and this derivation never allowed for it: the
    # bay was sized for its declared props and its fixtures, dressing added a
    # second layer on top, and `build`'s walkability trial then threw that layer
    # away again to keep the room crossable -- 44 of 87 rooms below full density
    # and three of them empty. A fixture and a shelf stand on the same floor, so
    # their needs ADD; taking the larger of the two is what made the room too
    # small for both. `wall_band_m` is asked of the module that does the
    # placing, so the two cannot drift.
    import dressing as _dress                                   # noqa: PLC0415
    band = _dress.wall_band_m(archetype(place))
    dressed = fx_width + 2.0 * band + max(WALK_M, 1.2)
    # The plan elements' own length: three rows of a rank, two cells of a
    # cellular run, an island plus its walkround.
    el_len = element_along_m(place)

    if not floor:
        # A room with nothing standing on its floor is small by nature -- a
        # micro-g bay you float through, a sealed section, a checkpoint. A
        # 6 x 8 m minimum made those read as empty halls, which is the same
        # picked-not-derived mistake one size down. Size to the wall props.
        wide = max((PROPS[k][0] for k in wall), default=1.6)
        return _fit_bay(place, max(wide + 1.2, fx_width, dressed, 3.0),
                        max(wide + 1.6, fx_len, el_len, 4.0))
    # Ranked alternately down two walls, so each wall takes half of them.
    per_side = [PROPS[k] for k in floor] * 2
    run = sum(pw + 0.45 for pw, _pd, _ph, _m in per_side) / 2.0 + 1.2
    deep = max(pd for _pw, pd, _ph, _m in per_side)
    width = 2 * deep + max(WALK_M, 1.6) + 0.5
    # Wall props run along z, so the bay must be long enough to hang the
    # widest of them -- a 6 m bay door needs 6 m of wall.
    widest_wall = max((PROPS[k][0] for k in wall), default=0.0)
    return _fit_bay(place, max(width, fx_width, dressed, 4.0),
                    max(run, widest_wall + 1.2, fx_len, el_len, 6.0))


_EXTENT_MEMO = {}
_SCHEMA_MEMO = []


def _place_extent(place):
    """`room_extent_m` for a place, memoised, without the caller holding a schema.

    `room_extent_m` needs the deck radius and therefore the schema, which is why
    the bay sizing has never been able to look at the location it is a bay OF.
    Loading it costs 49 ms and computing an extent 10 ms, and `bay_span_m` is
    called from six modules and thousands of times, so both are cached -- the
    same defect `interior.load()`'s missing memo caused in session 4c, where an
    `id(schema)`-keyed cache missed every call and one gate went from 2 minutes
    to 24. Keyed on the place KEY, so `variety.clone_place` (which changes only
    the key) recomputes rather than inheriting, and gets the same answer.
    """
    k = place["key"]
    if k not in _EXTENT_MEMO:
        if not _SCHEMA_MEMO:
            _SCHEMA_MEMO.append(it.load())
        _EXTENT_MEMO[k] = room_extent_m(_SCHEMA_MEMO[0][0], _SCHEMA_MEMO[0][1],
                                        place)
    return _EXTENT_MEMO[k]


def whole_bays(full_m, min_m):
    """Divide a real footprint into a whole number of bays, none below `min_m`.

    THE BAY IS A FRACTION OF ITS OWN LOCATION, and until V1 it was a constant
    derived from the contents alone -- so all six medlabs on the station built
    the identical 7.9 x 6.0 m room, and `variety.py` scored them 0.93 to 0.96 on
    plan because they ARE the identical room. Four of the six declare the same
    two functions and the same two interactables; the register's only remaining
    statement that they are different places is how big they are: 8 x 20, 8 x 22,
    12 x 30 and 10 x 24 degrees by metres.

    That number reached the geometry through `bays_in()`, whose two callers both
    put it in a report dict (STATE.md section 13), and nowhere else. Here it
    decides the PROPORTION of the bay that is built: a 40.8 m wide medlab is
    five 8.16 m bays and a 35.8 m one is four 8.95 m bays. Under `variety.py`'s
    `fit` mapping the absolute size is normalised away -- correctly, a player
    cannot tell 6 x 8 from 6 x 10 -- but the RATIO of the furniture band to the
    open floor is not, and neither is how many rows of anything fit.

    Never larger than about 1.5x the minimum, because `round` is what picks the
    count: a bay twice the size its contents need is an empty hall again.
    """
    if full_m <= min_m:
        return min_m
    n = max(1, int(round(full_m / min_m)))
    while n > 1 and full_m / n < min_m:
        n -= 1
    return full_m / n


def bays_in(schema, profile, place):
    """How many representative bays tile this location's real footprint."""
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    return max(1, int(w_full / bw)) * max(1, int(l_full / bl))


# ---------------------------------------------------------------------------
# TILING -- A LOCATION IS ITS FOOTPRINT, NOT ONE BAY OF IT
# ---------------------------------------------------------------------------
# `bay_span_m`'s docstring has always ended "the full location is then that bay
# instanced along its footprint", and until this section NOTHING INSTANCED IT.
# `bays_in` had two callers and both put the number in a report dict. Measured
# in 4e and restated in CLAUDE.md's W-track: 128 places, one bay apiece, against
# the 49,265 the footprints ask for -- `docking_bays` is 140 m in the gazetteer
# and a player walked 10.8 m of it before meeting a wall that was drawn as well
# as felt, so nothing looked broken and the room was one thirteenth of itself.
#
# WHAT IS TILED IS THE AXIS AND NOT THE RING, and that is STATE.md section 13's
# ruling rather than a convenience: "the ACROSS count is the ring direction and
# is largely handled -- a player walks along the ring corridor and meets the
# next location, so a 219-bay-wide plant is the sector, not a room. The DEEP
# count is the real gap." The deep axis is the one a player walks INTO a room
# along, and it is where the wall is.
#
# NOTHING HERE EMITS A SECOND COPY OF ANY GEOMETRY RULE. `build` already sizes
# every one of its loops off `ln` -- the rib count, the fixture pitch, the light
# courses, the plate fields, the dressing's area. The only thing standing
# between one bay and the whole footprint was the clamp `ln = min(l_full, bl)`.
# What this section decides is HOW FAR that clamp opens, WHAT DETAIL each bay
# gets, and the per-bay seed that stops the repeat reading as a tile pattern.


def bays_along(schema, profile, place):
    """Bays the footprint wants along the STATION AXIS.

    `round`, not `int`, and the difference is a whole bay of every location on
    the station. `whole_bays` divides the footprint into a WHOLE number of bays,
    so `l_full / bl` is an integer in exact arithmetic and 12.999999999999998 in
    floating point -- which `bays_in`'s `int()` truncates to 12, losing 10.77 m
    of `docking_bays`' 140.

    `bays_in` IS DELIBERATELY NOT CHANGED. Its 49,265 total is frozen normative
    in `docs/spec/PLACES.md` §TILING ("ANY recompute divergence, in either
    direction, fails the gate until a SPEC-CHANGE entry shows the
    re-derivation"), and quietly correcting an off-by-one underneath a frozen
    number is exactly the move that annex exists to prevent. The discrepancy is
    recorded here so it can be reconciled deliberately.
    """
    _w, l_full, _r = room_extent_m(schema, profile, place)
    _bw, bl = bay_span_m(place)
    if bl >= l_full:
        return 1
    return max(1, int(round(l_full / bl)))


_TILING = {}


def tiling(schema, profile, place):
    """How many bays of this location get built, and at what detail.

    Returns the plan every caller must read rather than re-derive:
    `n_want` / `n` / `n_dress` / `n_pop` / `bay_w` / `bay_l` / `built_l` /
    `want_l` / `tris` / `cap` / `capped`.

    THE CAP IS `budget.py`, AND IT IS STATED RATHER THAN SILENT. A tiled
    location is a straight run with no curvature to occlude it, so from its door
    every bay of it is in frame at once -- the same visibility case `budget.py`
    prices the habitat drum on ("every triangle in the volume is in the frustum
    at once"). The number that file already commits to for *everything* in a
    standing frame, not structure alone, is `DECK["visible_all_tris"]` = 300,000,
    and a place gets the whole of it because at the distance where it fills the
    frame it IS the frame -- the same reading `density.scene_budget` takes, in
    its own words, for the same reason. Nothing new is chosen here.

    THE LADDER IS DISTANCE FROM THE DOOR. The door is cut in the +z wall
    (`_end_wall_with_door`), so bay `n-1` is the one a player walks into and bay
    0 is the far end. Three tiers, and which layer sits in which is a measured
    argument, not a preference -- on `docking_bays` one bay is 96,628 triangles
    and splits 51% baked bodies, 26% dressing, 19% shell and articulation, 5%
    fixtures and declared props:

      every bay      shell, articulation, ribs, the fixtures the room is named
                     for, its plan elements, its declared interactables and its
                     light fittings. These are what the place IS. A 140 m
                     docking bay with machinery in the first 11 m is the defect
                     this section exists to remove, and they are also the
                     cheapest fifth of the mesh.
      `n_dress` bays `dressing.py`'s loose furniture and clutter.
      `n_pop` bays   `populace.py`'s baked bodies.

    The two that fall off with distance are the two highest-triangle,
    lowest-silhouette layers, and they are exactly what a streaming system
    instantiates instead of baking -- `deck.CORRIDOR_INSTANCED` already makes
    that trade for the corridor crowd, at 88% fewer triangles. `--footprint`
    prints `n`, `n_dress` and `n_pop` per place so the cap reads as a cap.

    THE PROBE IS THREE BUILDS AND IT IS WHY THIS IS DERIVED RATHER THAN TUNED.
    The per-bay cost of a room is a property of that room -- 25,740 triangles a
    bay in `docking_bays` against 4,928 in `core_shuttle` -- so a single global
    bay count would be a picked number, which is the defect `bay_span_m`'s own
    docstring was written to record ("A SIZE WAS PICKED INSTEAD OF DERIVED").

    THE COST OF A ROOM IS NOT ITS BAY COUNT TIMES THE COST OF ONE BAY, and the
    first version of this assumed it was. A run has TWO end walls however long it
    is, and their plating is a fifth of a one-bay build -- so `n x shell(1)`
    over-charged `docking_bays` by 30% and cost it four bays, 43 m of room, to an
    arithmetic error. Two shell probes at one and two bays give the marginal cost
    and the fixed cost separately, which is the model that is actually true:
    `f + n*m`. The third probe turns the two falling-off layers on and prices
    them. All three go through `build` itself, so there is no second description
    of what a bay contains.
    """
    key = place["key"]
    if key in _TILING:
        return _TILING[key]
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    bay_w, bay_l = min(w_full, bw), min(l_full, bl)
    n_want = bays_along(schema, profile, place)
    plan = {"key": key, "n_want": n_want, "bay_w": bay_w, "bay_l": bay_l,
            "want_l": n_want * bay_l, "cap": 0, "capped": False,
            "shell_tris": 0, "fixed_tris": 0, "dress_tris": 0, "pop_tris": 0}

    # A COMPOSED PLACE IS ITS MODULE'S OWN SIZE, AND THE MODULE IS ASKED WHAT
    # THAT IS. This branch used to answer `n=1, built_l=bay_l` for every place
    # whose module is in `bespoke.NEAR_END`, on the true observation that
    # `room_shell` TRANSLATES rather than scales -- so tiling one here would
    # slide the room down the axis instead of growing it. That is an argument
    # for growing the MODULE, which `bespoke.AXIAL` now does, and this branch
    # asks `bespoke.axial_plan` for the answer instead of assuming one. The
    # module's own mesh is measured, so `built_span_m` -- and therefore
    # `deck.room_interior_half_m`, the collision shell and the ring corridor's
    # position -- describes the room that is actually drawn.
    #
    # AND IT ASKS `composable()`, NOT `module in NEAR_END`. That is the question
    # `bespoke.composable` exists to replace and its docstring says so: a module
    # can own places it has no program for. Seven places -- `components`' six
    # exterior structures and `interior_kit`'s `standard_corridor` -- are built
    # by `rooms.build` like any other generic room and were being pinned to one
    # bay by this test, 1,024 m of them, invisible to the gate below because it
    # excused every row it thought was composed.
    #
    # NOT WRAPPED IN A `try`, deliberately. Swallowing an import error here
    # would answer "no module composes this place" for all 128 and silently
    # tile the 30 that a module builds -- sliding each of them down the axis
    # instead of growing it, with nothing in any output to say so. A tool that
    # degrades quietly is worse than one that fails.
    import bespoke as _BSP                                      # noqa: PLC0415
    composed = _BSP.composable(place)

    if composed:
        plan.update(_BSP.axial_plan(schema, profile, place))
        plan.update(n_dress=1, n_pop=1, tris=0)
        _TILING[key] = plan
        return plan

    if n_want <= 1:
        # A place whose footprint is one bay of its own contents. Five of those
        # were already at full footprint before this section existed and
        # `docs/spec/PLACES.md` names them.
        plan.update(n=1, n_dress=1, n_pop=1, built_l=bay_l, tris=0,
                    composed=False)
        _TILING[key] = plan
        return plan

    import budget as _B                                         # noqa: PLC0415
    ceiling = _B.DECK["visible_all_tris"]
    plan["cap"] = ceiling
    # Seed the memo before probing so the probes' own `build` calls cannot
    # recurse into here. They pass `_tiles` explicitly and therefore do not,
    # but a plan that depends on a build that depends on the plan is worth
    # closing by construction rather than by reading the call graph.
    _TILING[key] = dict(plan, n=1, n_dress=1, n_pop=1, built_l=bay_l, tris=0)

    s1 = len(build(schema, profile, place, _tiles=(1, 0, 0))[1])
    s2 = (s1 if n_want < 2
          else len(build(schema, profile, place, _tiles=(2, 0, 0))[1]))
    marg = max(1, s2 - s1)                  # one more bay of shell
    fixed = max(0, s1 - marg)               # the two end walls, once
    rep = {}
    full = len(build(schema, profile, place, report=rep, _tiles=(1, 1, 1))[1])
    dress = max(0, rep.get("dress_tris", 0))
    pop = max(0, full - s1 - dress)

    def _cost(n_, nd_, np_):
        return fixed + n_ * marg + nd_ * dress + np_ * pop

    n = max(1, min(n_want, int((ceiling - fixed - dress - pop) // marg)))
    rem = ceiling - _cost(n, 1, 1)
    n_dress = n if dress <= 0 else 1 + int(max(0, rem) // dress)
    n_dress = max(1, min(n, n_dress))
    rem -= (n_dress - 1) * dress
    n_pop = n_dress if pop <= 0 else 1 + int(max(0, rem) // pop)
    n_pop = max(1, min(n_dress, n_pop))

    plan.update(n=n, n_dress=n_dress, n_pop=n_pop, built_l=n * bay_l,
                capped=n < n_want, shell_tris=marg, fixed_tris=fixed,
                dress_tris=dress, pop_tris=pop, composed=False,
                tris=_cost(n, n_dress, n_pop))
    _TILING[key] = plan
    return plan


def built_span_m(schema, profile, place):
    """The size of what `build` ACTUALLY emits: (across the ring, along the axis).

    THE ONE FUNCTION EVERYTHING THAT PLACES A ROOM MUST ASK, and it exists
    because three places in `deck.py` each carried their own copy of the old
    answer -- `min(room_extent_m, bay_span_m)`, written out twice per site. With
    the bay tiled that expression is no longer how big the room is, and a
    collision shell sized on it would put an invisible wall 11 m into a 140 m
    room a player can see all the way down. `build`'s own note on `door_at` says
    what that is worth: "Physics and pixels disagreeing about whether there is a
    wall there is worse than either being wrong on its own."
    """
    plan = tiling(schema, profile, place)
    return plan["bay_w"], plan["built_l"]


def articulate(v, t, g, prefix, hw, hl, ceil, nrib=None, ln=None,
               ow=None, ol=None, z_off=0.0, x_off=0.0, scale=1.0,
               soffit=True, conduit=True, bands=True,
               mullions=True, deck=True, door_at=None, plates=True,
               owns_box=False):
    """Bands, grids, mullions, panels and conduit for a box-shaped interior.

    Extracted from `build()` so the BESPOKE modules can carry the same
    vocabulary. It was written once for the 68 procedural rooms and there is no
    reason a bar, a quarters unit or a customs hall should be articulated
    differently -- they are the same station, built by the same people, and the
    alternative is nine copies of this drifting apart.

    `prefix` is the group-name stem the calling module already uses, so the
    material bindings stay that module's own. Everything else is the room's own
    box. See INV-073 for the proportions and for why LENGTH, not triangle
    count, is what earns line density.

    `plates=False` REBUILDS THE PRE-INV-210 SHELL -- one panel box a rib bay,
    proud deck ribs on a flat plane, a bare soffit, mullions on their own
    lattice. It exists so `density.py --shell`'s negative control can be run on
    the geometry the gate was written against instead of on a description of
    it, which is the same reason `generate_hull` keeps `--no-apertures`. It is
    not a mode anything ships; `_selftest` asserts the gate fails on it.

    `owns_box` IS NOT A STYLE FLAG -- IT IS WHO OWNS THE VOLUME, and everything
    INV-210 added is behind it. It defaults OFF, so `articulate()` on its own
    emits exactly the geometry it emitted before INV-210; only a caller that
    says it owns the box gets the plated shell. `rooms.build` is that caller
    and is currently the only one.

    Two measured reasons, both of them findings rather than caution:

    1. **THE DOORWAY.** The MAXIMUM-z face is the near face:
       `bespoke.near_face_opening` measures the widest way in across `zmax`,
       and `deck._place_local` maps a room's local x = 0 onto the bearing the
       corridor's door is at (INV-112). `rooms.build` cuts its own aperture in
       that wall and passes it here as `door_at`, so it can be plated round.
       A BESPOKE MODULE CUTS ITS DOORWAY IN ITS OWN GEOMETRY, LATER AND
       ELSEWHERE, and hands this function nothing to skip -- so a continuous
       field across `+hl` walls the room up. `bespoke.py` went 149/149 to
       142/149 with *"walled at the doorway"* on eleven rooms and *"narrowest
       doorway on the station: bar_unnamed at 0.00 m"*.
    2. **THE DECK AND THE SOFFIT DO NOT TOUCH A DOORWAY, AND STILL BELONG
       BEHIND IT.** Plating those alone on the bespoke callers took the
       whole-station gate from 122/128 to 120/128 -- `bar_unnamed` and
       `eclipse_cafe` to 95.7% of their floor, `council_chamber` to 93.7%.
       `density.report` filters a line out when either facet meeting at it is
       finer than one screen pixel AT THAT LOCATION'S COMPOSING DISTANCE, and
       a 38 mm seam in a room composed from across a concourse is under it: the
       area counts and the line does not, so lambda falls. Those modules are
       not this one's to change, they have their own composing distances, and
       each can opt in with one keyword when somebody measures it there.
    """
    # `scale` coarsens every pitch. A 3 m quarters unit given the same 0.40 m
    # deck bay as a 12 m ward comes out at 334% of its floor and 44,640
    # triangles for a bedroom -- detail is not free, and a floor is a floor and
    # not a target. `soffit` and `conduit` are off where a module's own lights
    # live in that band; quarters puts a portal head light exactly there.
    deck_bay = DECK_BAY_M * scale
    soffit_bay = SOFFIT_BAY_M * scale
    n_mull = max(1, int(round(MULLIONS_PER_BAY / scale)))
    ln = ln if ln is not None else 2 * hl
    nrib = nrib if nrib is not None else max(1, int(ln / 4.0))
    ow = ow if ow is not None else hw + WALL_T_M
    ol = ol if ol is not None else hl + WALL_T_M
    arch = prefix
    # `z_off`/`x_off` let a module whose shell is not centred on the origin --
    # the quarters unit runs z 0..d, the customs hall z 0..HALL_LEN_M -- use
    # this without rewriting its own geometry. NOT named `zc`: the mullion loop
    # below already binds `zc`, and the first version of this shadowed the
    # parameter, so every band shifted by the last mullion's z and 68 rooms
    # left their own footprint. The footprint assertion caught it.
    mark = len(v)
    # ARTICULATION. Ribs alone leave a flat field of wall between them, and
    # `station/density.py` scores the whole module at 18% of its floor. What
    # follows is archetype-agnostic on purpose: it is the vocabulary any built
    # interior has, so one pass moves all 68 procedural rooms.
    #
    # THE ARITHMETIC THAT CHOSE IT, measured on station/garden.py in this same
    # session (INV-072): line density is metres of visible line per m2, so
    # LENGTH earns it, not triangle count. A continuous band round a room's
    # perimeter is twelve triangles laying four lines the length of that
    # perimeter -- about 13 m of line per triangle in a room this size. A panel
    # relief grid, which is the construction the budget bound is derived from,
    # yields 0.17. Bands first, then grids, then panels.
    per = 2 * (2 * ow + 2 * ol)                      # noqa: F841  (documented)
    #
    # THE SKIRT'S SHADOW GAP, and it is a construction rather than a paint.
    # `docs/reference-values.md` §1 fits the reference's dark horizontals seven
    # x-bins at a time and finds the affine fit beats the multiplicative one by
    # 3x on both the reveal and the dado -- "no albedo produces a ratio that
    # varies with the light" -- so the band has to be geometrically shielded.
    # The old build-up ran two proud skirt bands with no gap between them and
    # got a scribe. What replaces it is a plinth to SKIRT_H_M, then bare
    # substrate for SHADOW_GAP_M, then the plate field standing PANEL_D_M
    # proud, which overhangs that gap by 10 mm and shields it. The lip is the
    # field's own bottom course; nothing extra is emitted for it.
    for y, h_, d_, nm in (() if not bands else
                          (((0.0, SKIRT_H_M, SKIRT_D_M, "skirt"),) if plates
                           else ((0.0, SKIRT_H_M, SKIRT_D_M, "skirt"),
                                 (SKIRT_H_M + 0.02, 0.05, SKIRT_D_M * 0.6,
                                  "skirt"))) +
                          ((DADO_H_M, BAND_H_M, BAND_D_M, "dado"),
                          (DADO_H_M + BAND_H_M + 0.06, 0.05, BAND_D_M * 0.7,
                           "dado"),
                          (ceil - CORNICE_DROP_M, BAND_H_M, BAND_D_M, "rail"),
                          (ceil - CORNICE_DROP_M - 0.14, 0.05, BAND_D_M * 0.7,
                           "rail"),
                           (ceil - CORNICE_H_M, CORNICE_H_M, CORNICE_D_M,
                            "cornice"))):
        if y + h_ > ceil:
            continue
        for s in (-1, 1):
            _box(v, t, g, f"{arch}_{nm}",
                 (s * (hw - d_), y, -hl), (s * hw, y + h_, hl))
            # THE BANDS HAVE TO KNOW ABOUT THE DOOR TOO. Cutting the wall BOX
            # round an aperture and then running a skirt, a dado and a rail
            # straight across it leaves the opening barred at shin, hip and
            # shoulder -- visible in the first frame taken through one. A hole
            # in a wall is a hole in everything that wall carries.
            if s > 0 and door_at is not None and y < door_at[2]:
                dx0 = door_at[0] - door_at[1] / 2.0
                dx1 = door_at[0] + door_at[1] / 2.0
                for a, b in ((-hw, dx0), (dx1, hw)):
                    if b - a > 1e-6:
                        _box(v, t, g, f"{arch}_{nm}",
                             (a, y, s * (hl - d_)), (b, y + h_, s * hl))
            else:
                _box(v, t, g, f"{arch}_{nm}",
                     (-hw, y, s * (hl - d_)), (hw, y + h_, s * hl))
    # THE DECK: PROUD TILES, RECESSED JOINTS -- the way round the kit builds it
    # and the reverse of what this generator used to do. See `_plate_deck`. The
    # old construction laid proud ribs across a continuous plane every 0.40 m;
    # it read as a tiled floor and MEASURED as one 7 m facet, because the plane
    # was still the surface. `density.py --shell` puts the room deck at 7.25 to
    # 12.80 m against the corridor's 0.57.
    #
    # Tile at `interior_kit.deck_grid`'s own 0.62 m, and the bay joint every
    # `deck_panel_l_m` on top of it: the kit has both scales and so does every
    # corridor frame -- a fine tile field crossed by the structural panel
    # division. `deck_bay` is retained as the coarse pitch it always was.
    _pl, _course, _seam, _proud = kit_plate_module(scale)
    if deck and plates and owns_box:
        _plate_deck(v, t, g, f"{arch}_deck_joint", 0.0, 1, -hw, hw, -hl, hl,
                    DECK_TILE_M * scale, _seam * 0.5, 0.022)
        for i in range(1, max(2, int(2 * hw / deck_bay))):
            x = -hw + (2 * hw) * i / max(2, int(2 * hw / deck_bay))
            _box(v, t, g, f"{arch}_deck_joint",
                 (x - JOINT_W_M / 2, -0.03, -hl), (x + JOINT_W_M / 2, 0.0, hl))
        for i in range(1, max(2, int(2 * hl / deck_bay))):
            z = -hl + (2 * hl) * i / max(2, int(2 * hl / deck_bay))
            _box(v, t, g, f"{arch}_deck_joint",
                 (-hw, -0.03, z - JOINT_W_M / 2), (hw, 0.0, z + JOINT_W_M / 2))
    elif deck:                                   # the pre-INV-210 deck
        for i in range(1, max(2, int(2 * hw / deck_bay))):
            x = -hw + (2 * hw) * i / max(2, int(2 * hw / deck_bay))
            _box(v, t, g, f"{arch}_deck_joint",
                 (x - JOINT_W_M / 2, -0.01, -hl), (x + JOINT_W_M / 2, 0.012, hl))
        for i in range(1, max(2, int(2 * hl / deck_bay))):
            z = -hl + (2 * hl) * i / max(2, int(2 * hl / deck_bay))
            _box(v, t, g, f"{arch}_deck_joint",
                 (-hw, -0.01, z - JOINT_W_M / 2), (hw, 0.012, z + JOINT_W_M / 2))
    # THE SOFFIT IS A DECK SEEN FROM BELOW, and it is plated to the same module
    # for the same reason hard rule 4 exists: two descriptions of one plate
    # drift. Pans at `deck_panel_l_m`, hung 30 mm below the slab, so the
    # ceiling plane a player sees is broken into panels instead of being one
    # 12 m sheet with a tee grid drawn on it. The ceiling height does not move:
    # the pan faces sit exactly on `ceil`, and the slab is set back behind them.
    if soffit and plates and owns_box:
        _plate_deck(v, t, g, f"{arch}_soffit", ceil, -1, -hw, hw, -hl, hl,
                    ik.PROVISIONAL["deck_panel_l_m"] * scale, _seam, 0.03)
    # Soffit service grid: the T-bar every serviced ceiling has, and the run it
    # conceals. Both are continuous, which is why they are affordable.
    for i in range(1, max(2, int(2 * hl / soffit_bay)) if soffit else 1):
        z = -hl + (2 * hl) * i / max(2, int(2 * hl / soffit_bay))
        _box(v, t, g, f"{arch}_soffit_tee",
             (-hw, ceil - TEE_D_M, z - TEE_W_M / 2),
             (hw, ceil, z + TEE_W_M / 2))
    if soffit:
        _box(v, t, g, f"{arch}_soffit_tee",
             (-TEE_W_M / 2, ceil - TEE_D_M, -hl), (TEE_W_M / 2, ceil, hl))
    # High-level conduit along both long walls: a six-sided prism is 2 m of
    # line per triangle and every serviced deck on this station has one.
    for s in (-1, 1) if conduit else ():
        for k in range(CONDUITS):
            yy = ceil - CORNICE_H_M - 0.22 - k * 0.20
            # ABOVE HEAD HEIGHT OR NOT AT ALL. A 110 mm conduit at chest height
            # in a 2.4 m detention cell is something you walk into, and the trim
            # check above caught exactly that on `brig` and `security_central`.
            # A low room gets fewer conduits, not lower ones.
            if yy - CONDUIT_R_M < TRIM_HEAD_M:
                break
            _box(v, t, g, f"{arch}_conduit",
                 (s * (hw - CONDUIT_R_M * 2), yy - CONDUIT_R_M, -hl),
                 (s * hw, yy + CONDUIT_R_M, hl))
    # Deck joints on the SOFFIT too, and a second grid direction: a serviced
    # ceiling is a tile field, and the tile edges are continuous line for
    # twelve triangles a run.
    for i in range(1, max(2, int(2 * hw / soffit_bay)) if soffit else 1):
        x = -hw + (2 * hw) * i / max(2, int(2 * hw / soffit_bay))
        _box(v, t, g, f"{arch}_soffit_tee",
             (x - TEE_W_M / 2, ceil - TEE_D_M, -hl),
             (x + TEE_W_M / 2, ceil, hl))
    # THE WALL FIELD. Two plated fields -- dado and upper -- on all four walls,
    # at the corridor's own plate module. This replaces one box per rib bay,
    # which is the defect `docs/shell/before-office-half.png` shows and
    # `density.py --shell` measures. See `_plate_field` and INV-210.
    #
    # ALL FOUR WALLS, where the old panel ran on two. A room is entered through
    # an end wall and the first thing a player sees is the wall opposite; the
    # 2 x 1.5 m rectangles in the office frame are an END wall, which carried
    # bands and nothing else.
    ptop = min(ceil - CORNICE_H_M - 0.30, ceil - 0.5)
    gap_top = SKIRT_H_M + SHADOW_GAP_M
    field_bot = DADO_H_M + BAND_H_M + 0.16
    dx0 = dx1 = dh = 0.0
    if door_at is not None:
        dx0, dx1 = door_at[0] - door_at[1] / 2.0, door_at[0] + door_at[1] / 2.0
        dh = door_at[2]

    def _door_skip(lo, hi):
        """Does this plate cross the aperture in the +z wall, or its jamb?

        0.08 m of margin either side, so a plate edge does not land on the
        reveal a player walks through. `_end_wall_with_door` cuts the hole at
        exactly dx0..dx1 and the frame stands in front of it.
        """
        return (door_at is not None and hi[2] > hl - 1e-6
                and hi[0] > dx0 - 0.08 and lo[0] < dx1 + 0.08
                and lo[1] < dh + 0.08)

    # THE PLATE FIELD IS FOR A CALLER THAT OWNS ITS OWN APERTURES, and the
    # reason is measured rather than cautious. `articulate` is shared with nine
    # bespoke modules that cut their doorway in their own geometry, later and
    # elsewhere; a continuous field 45 mm proud runs straight up to a jamb this
    # function cannot see. `bespoke.py` fell 149/149 -> 142/149 with
    # *"walled at the doorway"* on eleven rooms, and the last 0.09 m of it was
    # exactly two plate faces: `alien_sector` and `kosh_quarters` measured a
    # 1.41 m aperture against the corridor's 1.50 m leaf. So a caller that has
    # not declared its aperture gets the wall it had before -- one panel a rib
    # bay, with the rib gaps the old construction left, which is where those
    # doorways were passing.
    if bands and plates and owns_box:
        # THE DADO FIELD IS ONE COURSE and the upper field is as many as it
        # takes. That is the kit's own division, not a saving:
        # `wall_assembly` calls `plated(0.0, sk_h, dado_top - reveal)` with
        # the default `courses=1` for the field below the rail and
        # `courses=wall_plate_courses` for the field above it. The reference
        # shows the same -- one tall dado panel, a stack of plate courses over.
        for s in (-1, 1):
            for a, b, nc in ((gap_top, DADO_H_M - 0.02, 1),
                             (field_bot, ptop, 0)):
                if b - a < 0.18:
                    continue
                ch = (b - a) if nc == 1 else _course
                nose = (f"{arch}_rail", PANEL_D_M + NOSING_PROUD_M,
                        NOSING_H_M)
                _plate_field(v, t, g, f"{arch}_panel", "x", s * hw, s,
                             -hl, hl, a, b, _pl, ch, _seam, PANEL_D_M,
                             nosing=nose)
                _plate_field(v, t, g, f"{arch}_panel", "z", s * hl, s,
                             -hw, hw, a, b, _pl, ch, _seam, PANEL_D_M,
                             skip=_door_skip if s > 0 else None,
                             nosing=nose)
    elif bands and ptop > DADO_H_M + 0.4:    # the pre-INV-210 wall field
        for i in range(nrib):
            z0 = -hl + i * (ln / nrib) + RIB_W_M
            z1 = -hl + (i + 1) * (ln / nrib) - RIB_W_M
            if z1 - z0 < 0.5:
                continue
            for s in (-1, 1):
                _box(v, t, g, f"{arch}_panel",
                     (s * (hw - PANEL_D_M), DADO_H_M + 0.25, z0),
                     (s * hw, ptop, z1))
    # Vertical members dividing the plate field, and they now land ON A PLATE
    # SEAM rather than on a lattice of their own. Six mullions a rib bay and a
    # 1.15 m plate module are two unrelated grids, and two unrelated grids on
    # one wall read as neither -- which is the moire in the "before" frame.
    #
    # AND THEY STAND PROUD OF THE PLATES. `MULLION_D_M` is 0.035 and
    # `PANEL_D_M` is 0.045, so every mullion above the old panel's bottom edge
    # was BURIED INSIDE IT: 288 triangles a room of geometry nobody could see,
    # and the reason the upper wall in the frame has no vertical division at
    # all while the lower wall does.
    #
    # ONE EVERY `portal_spacing_m`, NOT ONE EVERY PLATE, and this is the first
    # after-frame's own finding. `docs/shell/after-office-half.png` at the
    # first attempt put a 0.06 x 0.08 m member on every 1.15 m seam, which is a
    # ROD at that proportion and read as pipework strapped to the wall rather
    # than as the wall's own structure. `grey level 1.webp`'s right wall
    # settles both questions: the field between two pilasters carries only the
    # plate seams, and the strong verticals are the portal columns at
    # `portal_spacing_m` -- 3.6 m, the kit's own number. Widened to a flat
    # strap over the seam it stands on, because 60 mm proud of 60 mm wide is a
    # bar and 60 mm proud of 190 mm wide is a member.
    mtop = min(ceil - CORNICE_H_M - 0.05, ceil - 0.3)
    m_pitch = ik.PROVISIONAL["portal_spacing_m"] * scale
    m_w = MULLION_W_M * 3.2                       # 0.19 m: a strap, not a rod
    m_d = PANEL_D_M + MULLION_D_M * 0.5           # 20 mm proud of the plates
    if mullions and not (plates and owns_box):   # the pre-INV-210 lattice
        for i in range(nrib):
            z0 = -hl + i * (ln / nrib) + RIB_W_M
            z1 = -hl + (i + 1) * (ln / nrib) - RIB_W_M
            if z1 - z0 < 0.6:
                continue
            for k in range(1, n_mull + 1):
                zc = z0 + (z1 - z0) * k / (n_mull + 1)
                for s in (-1, 1):
                    _box(v, t, g, f"{arch}_mullion",
                         (s * (hw - MULLION_D_M), SKIRT_H_M,
                          zc - MULLION_W_M / 2),
                         (s * hw, mtop, zc + MULLION_W_M / 2))
    elif mullions and mtop > gap_top + 0.3:
        # SNAPPED TO A PLATE SEAM. A member standing mid-plate is a strap over
        # nothing; on the seam it is the cover strip that joint would need.
        n_m = max(1, int(round(2 * hl / m_pitch)))
        n_p = max(1, int(round(2 * hl / _pl)))
        for k in range(1, n_m):
            zc = -hl + (2 * hl) * round(n_p * k / n_m) / n_p
            for s in (-1, 1):
                _box(v, t, g, f"{arch}_mullion",
                     (s * (hw - m_d), SKIRT_H_M, zc - m_w / 2),
                     (s * hw, mtop, zc + m_w / 2))
        n_m = max(1, int(round(2 * hw / m_pitch)))
        n_p = max(1, int(round(2 * hw / _pl)))
        for k in range(1, n_m):
            xc = -hw + (2 * hw) * round(n_p * k / n_m) / n_p
            for s in (-1, 1):
                if (door_at is not None and s > 0
                        and dx0 - 0.08 - m_w / 2 < xc < dx1 + 0.08 + m_w / 2):
                    continue
                _box(v, t, g, f"{arch}_mullion",
                     (xc - m_w / 2, SKIRT_H_M, s * (hl - m_d)),
                     (xc + m_w / 2, mtop, s * hl))
    # SERVICE RISERS. The four high-level conduit runs above have to get down
    # to the deck somewhere, and until now they ran round the room and vanished
    # into the corner. A riser beside each rib is the fitting that has to be
    # there -- `docs/AAA-STANDARD.md`'s craft 4 is "a fitting is where a fitting
    # would be needed" -- and it is the only full-height vertical element on
    # the wall, which is what a field of horizontal courses needs against it.
    # `owns_box` guards it for the same reason the dado field is guarded: a
    # riser runs deck to cornice, so it is an obstruction at every height a
    # doorway probe looks at.
    if conduit and plates and owns_box and ceil > TRIM_HEAD_M + 0.4:
        for i in range(nrib):
            zc = -hl + (i + 0.5) * (ln / nrib)
            for s in (-1, 1):
                _box(v, t, g, f"{arch}_conduit",
                     (s * (hw - RIB_D_M - CONDUIT_R_M * 1.6), 0.0,
                      zc + RIB_W_M * 0.5 + 0.05),
                     (s * (hw - RIB_D_M), ceil - CORNICE_H_M - 0.22,
                      zc + RIB_W_M * 0.5 + 0.05 + CONDUIT_R_M * 1.6))
    if z_off or x_off:
        for i in range(mark, len(v)):
            x, y, z = v[i]
            v[i] = (x + x_off, y, z + z_off)
    return v, t, g


def spawn_m(schema, profile, place):
    """A point in this room where a person can actually stand, in room-local m.

    THE WALKABLE BUILD NEEDS THIS AND GUESSING DOES NOT WORK. The first walk
    test spawned a body at the room's origin, which in a room with a `spine`
    fixture is INSIDE the machinery: the body walked 0.63 m and stopped against
    a workbench. The room already knows where its free channel is -- that is
    what `lateral_stack` computes so that scenery and props do not occupy the
    same cubic metre -- so the answer is read from the room rather than assumed
    about it.

    Returned in the same local frame `build()` emits: x across, y up from the
    deck, z along. y is a small clearance above the deck so the body settles
    onto the floor rather than starting embedded in it.
    """
    w, ln = built_span_m(schema, profile, place)
    _bw, bay_l = bay_span_m(place)
    bay_l = min(ln, bay_l)
    hw, hl = w / 2.0, ln / 2.0
    _need, i0, i1 = lateral_stack(place)
    fx = fixtures_for(place)
    # A spine fixture sits ON the centreline, so the free lane is beside it.
    spine_d = max([f[2] for f in fx if f[4] == "spine"], default=0.0)
    lo, hi = -hw + i0, hw - i1
    if spine_d > 0.0:
        # Take the wider of the two lanes either side of the spine.
        left = (lo, -spine_d / 2.0)
        right = (spine_d / 2.0, hi)
        lo, hi = left if (left[1] - left[0]) > (right[1] - right[0]) else right
    x = (lo + hi) / 2.0
    # Keep clear of the end walls, and of the first fixture bay along z.
    #
    # IN THE BAY THE DOOR IS IN, and that is the tiling's doing. This read
    # `-hl + FIXTURE_PITCH_M * 0.5` -- just inside the FAR wall -- which was the
    # same thing as "just inside the room" only while the room was one bay. On a
    # tiled `docking_bays` it would put a body 140 m from the way in and 129 m
    # from the nearest furniture, and every room-reach measurement taken from it
    # would be measuring the walk back. The expression is unchanged; it is
    # applied to the NEAR bay's own frame, so a one-bay room gets exactly the
    # point it got before.
    z = max(-hl + 1.2, min(hl - 1.2,
                           hl - bay_l + max(1.2, FIXTURE_PITCH_M * 0.5)))
    return (x, 0.35, z)


def _end_wall_with_door(v, t, g, arch, ow, ceil, hl, ol, door_at):
    """The +z end wall as three pieces round an opening, instead of one box.

    No sill piece: the aperture runs to the deck. The visible corridor door has
    a 100 mm sill and this end does not, because a 100 mm vertical face is a
    wall to a character capsule rather than a step -- see `collision.py`. Two
    thresholds a metre apart, one you step over and one you do not, is worse
    than neither having one.
    """
    x, w, h = door_at
    x0, x1 = x - w / 2.0, x + w / 2.0
    if not (-ow < x0 and x1 < ow):
        raise ValueError(
            f"a {w:.2f} m door at x={x:.2f} does not fit in a {2 * ow:.2f} m "
            f"wall -- the corridor door snapped further than this room is wide")
    h = min(h, ceil)
    _box(v, t, g, f"{arch}_wall", (-ow, 0.0, hl), (x0, ceil, ol))
    _box(v, t, g, f"{arch}_wall", (x1, 0.0, hl), (ow, ceil, ol))
    if h < ceil:
        _box(v, t, g, f"{arch}_wall", (x0, h, hl), (x1, ceil, ol))


def place_interacts(v, t, g, place, hw, hl, ceil, inset=(0.0, 0.0),
                    spine_d=0.0, chan_c=0.0, chan_lo=None, chan_hi=None,
                    over_h=0.0, budget=None, skip=(), wall_faces=None,
                    keep_clear=None, report=None, z_off=0.0, seed=0):
    """Stand this place's DECLARED interactables in a room. One rule, two shells.

    THE SPLIT THIS FUNCTION EXISTS TO CLOSE. `directory.PLACES["interacts"]` is
    the register's list of what a player can use, and until this was extracted
    it was read by exactly one piece of code -- the body of `build` -- so a
    place composed by a bespoke module got its true shape and NONE of its
    declared uses. `interact.py --audit` measured the split and it was total:

        built generic  273 / 275        built bespoke  0 / 82

    Every generic room resolved essentially all of its declared interactables
    and every bespoke room resolved none of them, which is not a coincidence
    and is not a content gap -- it is one function that only one caller could
    reach. So the placement moved out here and `bespoke.compose` calls it too.

    THE GEOMETRY IS THE CALLER'S, THE RULE IS NOT. A generic bay knows its
    insets, its spine and its overhead channel; a bespoke shell measures its
    own floor band and passes that instead. Both get the same three passes:

      floor   rows against the two long walls, alternating sides, the centre
              left clear for walking
      wall    a CURSOR along the -x side wall and then the end walls -- never a
              fixed lattice, which used to wrap and put two props in the same
              0.85 m of wall
      ceiling hung under the overhead run, on the free channel

    `skip` is the tokens the caller has already built under another name --
    `earharts` builds `bar_table` for the declared `table` -- and passing them
    is what stops a room getting two tables. `interact.resolve` computes that
    set from the emitted mesh rather than from a written list.

    `keep_clear` is `(x_lo, x_hi, z_lo)` -- the doorway's approach rectangle in
    this frame -- and it is how a bespoke caller keeps the way in free WITHOUT
    the drop filter that would otherwise delete a declared interactable and
    leave it unresolvable. A prop that is never built is worse than one that is
    moved: the register says a player can use it, the room contains nothing,
    and no count can tell that apart from a module that forgot it.

    IT IS A RECTANGLE AND NOT A DEPTH, and the difference is a whole room.
    Bounding z alone reserves the entire near band, which in `qtr_transient` --
    15.83 m wide and 3.79 m deep, with a 2 m approach -- is over half the
    cabin, and the bunk it dropped was going to stand 6 m to one side of the
    door. What a body walking in actually needs is the LANE, so only a prop
    whose x range overlaps the lane is bound by z at all.

    `wall_faces` restricts which walls the cursor may use, for the same reason:
    the +z end wall is the one the corridor door is in.

    THE FIRST PASS IGNORES THE AREA BUDGET, and that is deliberate. The budget
    exists to stop a room filling with repeats -- the loop runs the prop list
    three times over -- but a DECLARED interactable that is never placed is a
    thing the register says a player can use and the room does not contain.
    One of each is the floor; repeats are what the budget governs.

    `z_off` IS WHAT MAKES THIS WORK IN A TILED LOCATION, and without it the
    tiling would have been furniture in the first bay and 129 m of nothing. Both
    passes are CURSORS from `-hl`, and the floor pass runs `floor_props * 3` --
    a hard cap of three copies of each declared prop no matter how long the
    room is. Handed a 140 m room they place a handful of props against one end
    and stop. So `build` calls this once per bay with `hl` the BAY's half-length
    and `z_off` the bay's centre, which is exactly what `bay_span_m`'s docstring
    always meant by "that bay instanced along its footprint".

    `seed` IS PER BAY AND IT IS WHY THE REPEAT IS NOT A TILE PATTERN. It picks
    which side wall the floor cursor starts on and phases the cursor within its
    own clearance, so bay 7's declared props are not bay 6's translated by
    `bay_l`. `deck.py --degeneracy` asks identity of two PLACES; the same
    question asked of two bays of one place is what this answers, and
    `--footprint` asserts it.
    """
    want = [p for p in place["interacts"] if p not in skip]
    floor_props = [p for p in want
                   if PROPS.get(p, (0, 0, 0, "floor"))[3] == "floor"]
    wall_props = [p for p in want
                  if PROPS.get(p, (0, 0, 0, "floor"))[3] == "wall"]
    ceil_props = [p for p in want
                  if PROPS.get(p, (0, 0, 0, "floor"))[3] == "ceiling"]
    if chan_lo is None:
        chan_lo = -hw + inset[0]
    if chan_hi is None:
        chan_hi = hw - inset[1]
    if budget is None:
        budget = DENSITY.get(archetype(place), 0.22) * (2 * hw) * (2 * hl)
    placed = {"floor": 0, "wall": 0, "ceiling": 0, "dropped": [],
              "turned": 0}

    z_lo, z_top = z_off - hl, z_off + hl

    def z_limit(xa, xb):
        """How far up the room a prop spanning x in [xa, xb] may reach."""
        if keep_clear is None:
            return z_top
        cx0, cx1, cz0 = keep_clear
        return min(z_top, cz0) if (xb > cx0 and xa < cx1) else z_top

    z_hi = z_limit(-hw, hw)             # the tightest bound, for the reports

    used = 0.0
    # THE BAY'S OWN PHASE. `_u` is the module's seeded hash, so this is
    # reproducible from (place, bay) and there is no `random` anywhere in the
    # build. The start side alternates and the cursor is offset by up to one
    # prop gap, which is enough that two bays never rank the same props against
    # the same wall at the same z.
    #
    # SEED 0 IS EXACTLY THE PRE-TILING BEHAVIOUR -- side `-1`, cursor at
    # `-hl + 0.6`, instance seeds without the bay in them. A one-bay room, every
    # `bespoke.compose` caller and the two probes in `_selftest` therefore emit
    # the geometry they emitted before, byte for byte, and the variation is
    # purely additive. A change that moved every prop on the station a
    # centimetre would be a content churn nothing asked for, and it would land
    # in `variety.py` and `--degeneracy` as noise on top of the real signal.
    side = -1 if (seed % 2 == 0) else 1
    z0_start = z_lo + 0.6 + (0.40 * _u(place["key"], "interacts", seed)
                             if seed else 0.0)
    cursor = [z0_start, z0_start]

    def _sd(*parts):
        """An instance seed that carries the bay only when there is one."""
        return (place["key"],) + ((seed,) if seed else ()) + parts
    ndist = len(floor_props)
    free_x = 2 * hw - inset[0] - inset[1] - 0.1
    for i, key in enumerate(floor_props * 3):
        pw, pd, ph, _m = PROPS.get(key, (0.8, 0.6, 0.8, "floor"))
        if i >= ndist and used + pw * pd > budget:
            break                        # repeats are what the budget governs
        # A PROP TURNS RATHER THAN NOT EXISTING. The default is long-side to
        # the wall, running along z; where the room is too shallow for that it
        # turns through 90 degrees and runs along x instead. Measured cause:
        # three of the four quarters are 2.6 to 4.1 times wider than they are
        # deep -- `qtr_transient` is 15.83 x 3.79 m -- so a 2.05 m bunk cannot
        # run along the shallow axis, and it was silently dropped. A bunk
        # standing head-to-wall across a wide, shallow cabin is also what the
        # room actually looks like, so this is the right shape and not only the
        # one that fits.
        #
        # THE SEARCH IS WIDER FOR THE FIRST OF EACH THAN FOR A REPEAT, and the
        # asymmetry is the whole point. A declared interactable that is not in
        # the room is a hole in what the register promises, so the first one
        # tries both walls and both orientations; a second copy of a table is
        # furniture, so it keeps the original rule and stops when the wall it
        # is on runs out. Letting repeats retry too changed the furniture in
        # four of fifteen generic rooms -- one wall's worth of props became
        # two -- which is a content change this was not for.
        first = i < ndist
        pick = None
        for s in ((side, -side) if first else (side,)):
            z0 = cursor[0 if s < 0 else 1]
            for j, (ax, az) in enumerate(((pd, pw), (pw, pd))
                                         if first else ((pd, pw),)):
                if ax > free_x:
                    continue
                x0 = ((-hw + inset[0] + 0.05) if s < 0
                      else (hw - inset[1] - 0.05 - ax))
                if abs(x0) < spine_d / 2.0 + 0.1:    # would sit in the spine
                    pick = "spine"
                    break
                if z0 + az <= z_limit(x0, x0 + ax) - 0.6:
                    pick = (s, ax, az, x0, z0, j)
                    break
            if pick:
                break
        if pick == "spine":
            break
        if pick is None:
            if not first:
                break
            placed["dropped"].append(key)
            continue
        s, ax, az, x0, z0, turned = pick
        _fixture(v, t, g, key, (x0, 0.0, z0), (x0 + ax, ph, z0 + az),
                 _sd(i), "prop_", report)
        cursor[0 if s < 0 else 1] = z0 + az + 0.45
        used += pw * pd
        side = -s
        placed["floor"] += 1
        placed["turned"] += turned

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
    # The side wall's own bound, from its own x band -- a terminal hung at
    # x = -hw is only in the doorway's way if the doorway reaches that wall.
    walls = [("side", z_lo, z_limit(-hw, -hw + 0.6)),
             ("near", -hw + inset[0], hw - inset[1]),
             ("far", -hw + inset[0], hw - inset[1])]
    if wall_faces is not None:
        walls = [w for w in walls if w[0] in wall_faces]
    wi, cur = 0, (walls[0][1] if walls else 0.0)
    for key in wall_props:
        pw, pd, ph, _m = PROPS.get(key, (0.6, 0.1, 0.6, "wall"))
        while wi < len(walls) and cur + pw > walls[wi][2]:
            wi += 1
            if wi < len(walls):
                cur = walls[wi][1]
        if wi >= len(walls):
            placed["dropped"].append(key)
            break                      # room is out of wall; sized by bay_span
        # A WALL PROP THAT WILL NOT FIT ABOVE THE SILL STANDS ON THE FLOOR.
        # `ph > 2.0` misses a 2.00 m door by a hair, so `prop_makeshift_door`
        # was hung with its head at 3.05 m -- which passed for as long as every
        # generic room was 2.90 m and the containment tolerance was 0.15, and
        # failed the moment `thieves_guild` became the 2.65 m room its own
        # functions ask for. A latent defect that a variety pass merely
        # uncovered; the sill is now derived from the room it is in.
        sill = 0.0 if ph > 2.0 else min(1.05, max(0.0, ceil - ph - 0.10))
        sd = _sd(walls[wi][0], round(cur, 2))
        if walls[wi][0] == "side":
            _fixture(v, t, g, key, (-hw, sill, cur),
                     (-hw + pd, sill + ph, cur + pw), sd, "prop_", report)
        elif walls[wi][0] == "near":
            _fixture(v, t, g, key, (cur, sill, z_lo),
                     (cur + pw, sill + ph, z_lo + pd), sd, "prop_", report)
        else:
            _fixture(v, t, g, key, (cur, sill, z_hi - pd),
                     (cur + pw, sill + ph, z_hi), sd, "prop_", report)
        cur += pw + 0.35
        placed["wall"] += 1
    for i, key in enumerate(ceil_props):
        pw, pd, ph, _m = PROPS.get(key, (1.0, 1.0, 0.5, "ceiling"))
        # A crane RIDES the gantry rail, so it hangs BELOW the overhead run
        # rather than beside it. Placing it beside was the first attempt and it
        # put a 3 m crane through a 0.35 m rail -- which is also what a real
        # gantry crane does not do.
        top = ceil - over_h
        xc = min(max(chan_c, chan_lo + pd / 2), chan_hi - pd / 2)
        z0 = min(max(z_lo + 2.0 + i * 3.0, z_lo), z_hi - pw)
        _fixture(v, t, g, key, (xc - pd / 2, top - ph, z0),
                 (xc + pd / 2, top, z0 + pw), _sd(i), "prop_",
                 report)
        placed["ceiling"] += 1
    if report is not None:
        report["interacts"] = placed
    return placed


def place_elements(v, t, g, place, hw, hl, ceil, chan_lo, chan_hi,
                   report=None, w=None, ln=None, z_off=0.0, seed=0):
    """Build this place's PLAN ELEMENTS -- the middle of its floor.  INV-140.

    Runs AFTER the declared props and BEFORE the dressing, and that order is
    the whole safety argument.  Every instance is tested against the solids
    already standing in the room and simply is not built where it would clash,
    so `_selftest`'s interpenetration assertion cannot be made to fire by a
    table that is 20 mm too wide: the geometry is correct BY CONSTRUCTION
    rather than by my arithmetic being right in 78 rooms at once.

    What the arithmetic still has to get right is the SIZE OF THE BAY, and that
    is exactly what `element_cross_m` / `element_along_m` are for -- so this
    reports, per element, how many instances it WANTED and how many it got.  A
    room too small for its own plan is then a number rather than a room that
    quietly came back generic.  `--elements` prints it for all 78.

    The free floor is the fixtures' channel less the band each wall keeps for
    its own furniture (`element_keep_m`), which is why nothing here needs to
    know anything about the props or the dressing.

    `z_off` AND `seed` ARE THE TILING'S, and this function needed them for a
    sharper reason than `place_interacts` did. A `rank` is capped at `min(5, ...)`
    rows and a `cell` at `min(6, ...)`, and both CENTRE what they build in the
    window they are given -- so over a 140 m run the plan would be five rows of
    desks in the middle and 120 m of bare deck either side, which reads worse
    than the one bay it replaced. `build` calls this per bay against the bay's
    own window; `w`/`ln` stay the WHOLE run, because the walkability trial in
    `put` must ask whether the run is still crossable end to end and not whether
    one bay of it is.
    """
    els = elements_for(place)
    if not els:
        return
    kx0, kx1, kz0, kz1 = element_keep_m(place)
    # A FIN THINNER THAN THIS HAS NO ROOM TO BE A MACHINE. `dressing.machine`
    # insets its builders by 12% of the box so that flanges, bands and nosings
    # have somewhere to be proud into, and on a 0.12 m screen that is 14 mm --
    # which `machine_escapes` measured leaving the box by exactly 0.0144 m in
    # `ngrath` and `thieves_guild`. Stated as a floor rather than fixed in the
    # table, because it is a property of the BUILDER and would come back the
    # next time somebody writes a thin element.
    els = tuple((n, max(sz, 0.16) if k == "cell" else sz, ex, h, k)
                for n, sz, ex, h, k in els)
    lo, hi = chan_lo + kx0, chan_hi - kx1
    zlo, zhi = z_off - hl + kz0, z_off + hl - kz1
    solids = [b for _n, b in _boxes(v, t, g, is_solid)]

    def put(name, kind, x0, x1, y1, z0, z1, i):
        """Build one instance -- unless it would clash, or seal the room.

        THE WALKABILITY IS TESTED ON BOXES BEFORE ANY GEOMETRY IS EMITTED, and
        that is why it can be a guarantee rather than a hope. `gunnery_control`
        is (defence_command, fire_control) in a 9.7 x 7.5 m bay already holding
        a plot frame and a signal rack on both flanks, and the fifth console row
        closed the last 0.9 m path across it -- `walkable` said so, on a room
        the interpenetration check was perfectly happy with. A room a player
        cannot cross is worse than a room with one row fewer in it, so the row
        is not built and the shortfall is in the report.
        """
        box = (x0, 0.0, z0, x1, min(y1, ceil - 0.10), z1)
        if x1 - x0 < 0.20 or z1 - z0 < 0.10:
            return 0
        if any(_overlaps(box, s) for s in solids):
            return 0
        if w is not None and not walkable(
                [(name, b) for b in solids + [box]], w, ln):
            return 0
        _fixture(v, t, g, name, (box[0], box[1], box[2]),
                 (box[3], box[4], box[5]),
                 (place["key"],) + ((seed,) if seed else ()) + (kind, i),
                 report=report)
        solids.append(box)
        return 1

    # ORDER OF PLACEMENT IS NOT THE ORDER OF DECLARATION, and it is the second
    # thing building this found.  `telepath_office` is (offices, psi_corps) --
    # ranks of desks and a shielded booth against the far wall -- and declared
    # in that order the ranks fill the room to both ends and the booth reports
    # `want 1, got 0`.  A `rank` and a `cell` FILL whatever is left; an `end`,
    # a `cross` and an `island` CLAIM one piece of the room.  So the claims go
    # in first and take their band out of the free rectangle, and what fills is
    # then honest about how much room it had.  The declared order still decides
    # WHICH elements a place gets -- see `elements_for` -- only not the order
    # they are built in.
    _CLAIM = {"end": 0, "cross": 1, "island": 2, "cell": 3, "rank": 4}
    for name, span_z, ext_x, h, kind in sorted(els, key=lambda e: _CLAIM[e[4]]):
        want = got = 0
        cx = (lo + hi) / 2.0
        if kind == "island":
            dx = min(ext_x, (hi - lo) - 2 * AISLE_M)
            dz = min(span_z, (zhi - zlo) - 2 * AISLE_M)
            want = 1
            zc = (zlo + zhi) / 2.0
            if dx > 0.0 and dz > 0.0:
                got = put(name, kind, cx - dx / 2, cx + dx / 2, h,
                          zc - dz / 2, zc + dz / 2, 0)
            if got:
                zhi = zc - dz / 2 - AISLE_M
        elif kind == "rank":
            aisle = max(AISLE_M, ext_x)
            half = ((hi - lo) - aisle) / 2.0
            pitch = span_z + ROW_GAP_M
            n = max(0, min(5, int((zhi - zlo + ROW_GAP_M) / pitch)))
            want = 2 * n
            z = zlo + ((zhi - zlo) - (n * pitch - ROW_GAP_M)) / 2.0
            for i in range(n if half > 0.25 else 0):
                got += put(name, kind, lo, lo + half, h, z, z + span_z, 2 * i)
                got += put(name, kind, hi - half, hi, h, z, z + span_z,
                           2 * i + 1)
                z += pitch
        elif kind == "cross":
            gap = max(AISLE_M, ext_x)
            want = 1
            zc = zlo + (zhi - zlo) / 3.0
            got = put(name, kind, lo, hi - gap, h, zc, zc + span_z, 0)
            if got:
                zlo = zc + span_z + AISLE_M
        elif kind == "cell":
            # A SECOND CELLULAR RUN GOES DOWN THE OTHER WALL.  `medlab_red` is
            # (medical, triage) -- servicing bays and then triage bays -- and
            # with both on +x the second reported `want 2, got 0`: two runs of
            # fins at two pitches down one wall are the same cubic metre.  Two
            # facing runs off an aisle is also what a ward actually is.
            # `+ seed` is the tiling's, and it is the one variation in this
            # function that changes the PLAN rather than the machine: a ward's
            # bays face off an aisle either way round, so alternating which wall
            # they hang on down the run is both varied and correct.
            side = (sum(1 for e in els[:els.index(
                (name, span_z, ext_x, h, kind))] if e[4] == "cell")
                + seed) % 2
            pitch = span_z + CELL_PITCH_M
            n = max(0, min(6, int((zhi - zlo + CELL_PITCH_M) / pitch)))
            want = n
            z = zlo + ((zhi - zlo) - (n * pitch - CELL_PITCH_M)) / 2.0
            x0, x1 = ((hi - ext_x, hi) if side == 0 else (lo, lo + ext_x))
            for i in range(n if hi - ext_x > lo + AISLE_M else 0):
                got += put(name, kind, x0, x1, h, z, z + span_z, i)
                z += pitch
            if got and side == 0:
                hi -= ext_x
            elif got:
                lo += ext_x
        elif kind == "end":
            gap = max(AISLE_M, ext_x)
            want = 1
            got = put(name, kind, lo, hi - gap, h, zhi - span_z, zhi, 0)
            if got:
                zhi -= span_z + AISLE_M
        else:
            raise ValueError(f"{place['key']}: unknown plan kind {kind!r}")
        if report is not None:
            report.setdefault("elements", []).append((name, kind, want, got))


def build(schema, profile, place, max_span_m=None, door_at=None,
          report=None, plates=True, _tiles=None):
    """Geometry for a location: its bay, instanced along its own footprint.

    IT USED TO BE ONE BAY AND THAT IS THE DEFECT THIS ANSWERS. The docstring
    here read "Geometry for one representative bay of a location... `bays_in()`
    says how many the streaming system instances", and nothing instanced them --
    so `docking_bays` is 140 m in the gazetteer and a player walked 10.77 m of
    it. `tiling()` decides how many bays are built and at what detail; the loops
    below already scale with `ln` and always did, which is why this is a change
    of one clamp plus the four content passes that had to become per-bay.

    `_tiles` is `(n, n_dress, n_pop)` and exists for ONE caller: `tiling()`'s own
    probe, which needs the cost of a single bay with and without the two layers
    that fall off with distance. Everything else asks for the plan. It is private
    because a caller that picks its own tile count is a second description of how
    big a room is, and hard rule 4 is that there is only ever one.

    `door_at` is `(x_m, width_m, height_m)` -- an opening in the wall at +z,
    which is the end a ring corridor arrives at. Without it a room is a sealed
    box, which is what all 118 of them were until session 3v: the collision
    shell let a player walk into the room and the render mesh still showed them
    a solid wall to walk through. Physics and pixels disagreeing about whether
    there is a wall there is worse than either being wrong on its own.

    The x is NOT the room's centre. A corridor door snaps to the nearest bay
    centre of its kit section, by up to 1.5 m of arc, so the opening has to be
    cut where the door actually landed -- `interior.ring_arc` reports that in
    `meta["doors_at"]` and the caller converts it to this frame.
    """
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    w = min(w_full, bw)
    bay_l = min(l_full, bl)
    if _tiles is None:
        _plan = tiling(schema, profile, place)
        n_bay, n_dress, n_pop = (_plan["n"], _plan["n_dress"], _plan["n_pop"])
        # A COMPOSED PLACE'S `n` COUNTS THE MODULE'S OWN UNITS, NOT THESE BAYS.
        # `bespoke.axial_quantum_m` is a row of quarters or a rib bay or a
        # market bay, and only for `plant` does it coincide with `bay_span_m`.
        # This is the FALLBACK path -- what `deck.room_geometry` draws when a
        # composed room raises or comes back walled -- and a fallback that is a
        # different size from the thing it stands in for is precisely the
        # divergence `deck.room_geometry` exists to close. So it is re-divided
        # to land on the composed room's own length exactly.
        if _plan.get("composed") and _plan.get("built_l"):
            n_bay = max(1, int(round(_plan["built_l"] / max(bay_l, 1e-9))))
            bay_l = _plan["built_l"] / n_bay
            n_dress = max(1, min(n_bay, n_dress))
            n_pop = max(1, min(n_dress, n_pop))
    else:
        n_bay, n_dress, n_pop = _tiles
    # THE ONE CLAMP THAT KEPT 128 LOCATIONS AT A BAY APIECE. Everything below
    # is written against `ln` and scales with it; this line is what used to make
    # `ln` one bay.
    ln = n_bay * bay_l
    arch = archetype(place)
    ceil = ceiling_m(place)
    v, t, g = [], [], []
    hw, hl = w / 2.0, ln / 2.0
    ow, ol = hw + WALL_T_M, hl + WALL_T_M
    # Bay k's centre in the run's own frame. The door is in the +z wall, so the
    # LAST bay is the one a player walks into and detail falls off backwards
    # from it -- `_near` is that ordering, and it is what makes `n_dress` and
    # `n_pop` mean "within this far of the way in" rather than "somewhere".
    def _bay_z(k):
        return -hl + (k + 0.5) * bay_l

    def _near(k):
        return n_bay - 1 - k                 # 0 at the door, n-1 at the far end

    # Shell: deck and soffit run to the OUTER wall extent, or every wall/soffit
    # junction is an open corner. hospitality.py shipped that defect and it
    # took a magenta-pixel count to find.
    _box(v, t, g, f"{arch}_deck", (-ow, -0.14, -ol), (ow, 0.0, ol))
    _box(v, t, g, f"{arch}_soffit", (-ow, ceil, -ol), (ow, ceil + 0.14, ol))
    for s in (-1, 1):
        _box(v, t, g, f"{arch}_wall", (s * hw, 0.0, -ol), (s * ow, ceil, ol))
        if s > 0 and door_at is not None:
            _end_wall_with_door(v, t, g, arch, ow, ceil, hl, ol, door_at)
        else:
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

    # ARTICULATION -- see `articulate()` and INV-073. One vocabulary for every
    # box-shaped interior on the station, procedural and bespoke alike.
    # `owns_box=True` because THIS function owns the whole volume: it emitted
    # the deck, the soffit and all four walls above, and cut the aperture in
    # the +z one through `_end_wall_with_door`, so `articulate` can plate them
    # and knows where the hole is. A bespoke module cannot say either of those
    # things and does not. See the `owns_box` paragraph in `articulate`'s
    # docstring for the two measurements that put everything behind it.
    articulate(v, t, g, arch, hw, hl, ceil, nrib=nrib, ln=ln, ow=ow, ol=ol,
               door_at=door_at, plates=plates, owns_box=True)

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
            for i, zc in enumerate(_zs(fw)):
                _fixture(v, t, g, name, (-fd / 2, 0.0, zc),
                         (fd / 2, min(fh, ceil - 0.1), zc + fw),
                         (place["key"], i), report=report)
        elif kind == "flank":
            s = flank_side
            x0 = (-hw + inset[s]) if s == 0 else (hw - inset[s] - fd)
            for i, zc in enumerate(_zs(fw)):
                _fixture(v, t, g, name, (x0, 0.0, zc),
                         (x0 + fd, min(fh, ceil), zc + fw),
                         (place["key"], i), report=report)
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
        for i, zc in enumerate(_zs(fw)):
            _fixture(v, t, g, name, (chan_c - fd / 2, ceil - fh, zc),
                     (chan_c + fd / 2, ceil, zc + fw), (place["key"], i),
                     report=report)

    # DRESSING -- station/dressing.py. The generator that fills every room, as
    # against the 311 hand-declared prop instances that covered the whole
    # station at 4.5 per room. One 6x9 m office comes out of it with 367
    # objects. It runs AFTER the fixtures so it can read the free channel they
    # leave, and before the declared props so a declared prop always wins its
    # spot -- `interacts` is what a player can USE and must not be buried.
    # PER BAY, and that is the whole of what "instanced along its footprint"
    # means for the things a player uses. Both passes are cursors from the near
    # end of the window they are given, and both cap how many copies they will
    # make -- `floor_props * 3` here, `min(5, ...)` rows and `min(6, ...)` cells
    # in the plan elements. Called once over a 140 m run they put a handful of
    # props against one end and centre five rows of desks in the middle; called
    # once per bay they furnish all of it. The seed is the bay index, so bay 7
    # is not bay 6 translated by `bay_l`.
    for k in range(n_bay):
        # ONLY THE END BAYS HAVE END WALLS. `place_interacts` hangs wall props
        # on the -x side wall first and spills onto the two end walls when it
        # runs out; in a tiled run those planes are interior to the room for
        # every bay but the two on the ends, so a spilled monitor wall would
        # hang in mid-air 60 m down an open hall. `wall_faces` already existed
        # for exactly this question and a one-bay room gets all three, which is
        # what it got before.
        faces = ("side",) + (("near",) if k == 0 else ()) \
            + (("far",) if k == n_bay - 1 else ())
        place_interacts(v, t, g, place, hw, bay_l / 2.0, ceil,
                        inset=inset, spine_d=spine_d, chan_c=chan_c,
                        chan_lo=chan_lo, chan_hi=chan_hi, over_h=over_h,
                        budget=DENSITY.get(arch, 0.22) * w * bay_l,
                        report=report, z_off=_bay_z(k), seed=k,
                        wall_faces=faces)

        # THE PLAN ELEMENTS -- INV-140, and this is the line that makes a
        # medlab's floor a different shape from an office's rather than a
        # differently furnished one.  See `place_elements` and `PLAN_ELEMENTS`.
        # `w`/`ln` stay the WHOLE run: `put`'s walkability trial has to ask
        # whether a body can still cross the location end to end, and a bay that
        # is crossable inside a run that is not is the failure the tiling would
        # otherwise introduce.
        place_elements(v, t, g, place, hw, bay_l / 2.0, ceil, chan_lo, chan_hi,
                       report=report, w=w, ln=ln, z_off=_bay_z(k), seed=k)

    # ------------------------------------------------------------------
    # Light fittings. See LIGHTS. Emitted LAST and tested against what is
    # already standing, because a lamp is the one thing in the room whose
    # position is negotiable: a furnace has to be where the furnace is, and a
    # fitting that would be inside it simply is not fitted there. The
    # alternative -- reserving a lighting zone up front the way
    # `lateral_stack` reserves the wall band -- would push the props around to
    # suit the lamps, which is backwards.
    #
    # RIBS COUNT AS OBSTACLES HERE and do not for props. A prop standing in
    # front of a rib is a chair against an articulated wall; a light course
    # running THROUGH one is a strip of light passing through structure, and
    # the wall course is the fitting most likely to do it.
    obstacles = _boxes(v, t, g, lambda n: n.startswith(("prop_", "fix_"))
                       or n.endswith("_rib"))

    def _lay(name, x0, x1, y0, y1, lw, pitch):
        """Repeat one fitting down the z axis, THROUGH the gaps.

        The first version placed fittings at nominal centres and dropped any
        that collided, and it produced ZERO wall courses in every room in the
        station. The reason is worth keeping: `rib_pitch_m` and the fitting
        pitch are both derived from the room, so the nominal positions of the
        two lattices coincide and every single course landed on a rib.

        So the free intervals are measured first and the fitting is laid into
        them at its own measured pitch, centred in each run. A light course in
        the recessed bay BETWEEN two ribs is also what the reference frames
        show; the collide-and-drop version could not have got there.
        """
        blocks = sorted((s[2], s[5]) for _n, s in obstacles
                        if s[0] < x1 - 1e-6 and x0 < s[3] - 1e-6
                        and s[1] < y1 - 1e-6 and y0 < s[4] - 1e-6)
        runs, cur, longest = [], -hl + 0.05, (0.0, 0.0, 0.0)
        for b0, b1 in blocks + [(hl - 0.05, hl)]:
            if b0 - cur >= lw:
                runs.append((cur, b0))
            if b0 - cur > longest[0]:
                longest = (b0 - cur, cur, b0)
            cur = max(cur, b1)
        # A FITTING LONGER THAN EVERY BAY IS CUT TO THE BAY, and until V1 it
        # simply was not fitted. `light_wall_course` is 2.40 m and `rib_pitch_m`
        # is 2.60 m at a 4.2 m ceiling, so the clear run between two ribs is
        # 2.15 m -- the course NEVER fits, and the only reason `interfaith_chapel`
        # had one was that its bay was short enough to carry two ribs instead of
        # four. Growing the bay for its pews turned that luck off and the room
        # lost its wall lighting entirely, which is how this was found. A strip
        # cut to the recess it sits in is also what the reference frames show.
        if not runs and longest[0] >= 0.60:
            lw = longest[0] - 0.02
            runs = [(longest[1], longest[2])]
        n = 0
        for lo, hi in runs:
            k = max(1, int((hi - lo - lw) / pitch) + 1)
            span = lw + (k - 1) * pitch
            z = lo + (hi - lo - span) / 2.0
            for _ in range(k):
                _box(v, t, g, name, (x0, y0, z), (x1, y1, z + lw))
                z += pitch
                n += 1
        return n

    for name, lw, ld, lh, kind, my in lights_for(place):
        # A key fitting is a single object over the spine, so it has no pitch
        # and asking for one would need an entry in LIGHT_PITCH_M that means
        # nothing.
        pitch = ln if kind == "key" else light_pitch_m(name, place)
        if kind in ("ceiling", "key"):
            top = ceil - 0.02
            if kind == "key":
                # One fitting, on the centreline, over whatever the spine
                # holds. In a chapel that is the dais, and the dais is the
                # only thing in the room that should be lit.
                xs = [chan_c]
            else:
                # Two rows a quarter of the free channel either side of its
                # centre. The centreline already carries the `over` fixtures
                # and anything riding them, so a row down the middle would be
                # squeezed out of every industrial and store bay in the
                # station.
                q = (chan_hi - chan_lo) / 4.0
                xs = ([chan_c] if chan_hi - chan_lo < ld + 0.4
                      else [chan_c - q, chan_c + q])
                xs = [min(max(x, chan_lo + ld / 2), chan_hi - ld / 2)
                      for x in xs]
            for x in xs:
                _lay(name, x - ld / 2, x + ld / 2, top - lh, top, lw, pitch)
        elif kind == "course":
            # Courses repeat UP the wall as well as along it: the war room's
            # strip banks are at two heights and command and control's wall
            # courses at four. Each is clamped under the soffit rather than
            # dropped, and duplicates that clamp onto the same height collapse
            # -- so a 2.9 m office gets its upper course just under the
            # ceiling instead of losing it.
            ncourse, vpitch = LIGHT_COURSES.get(name, (1, 0.0))
            ys, top_y = [], ceil - lh - 0.15
            for k in range(ncourse):
                y = round(min(my + k * vpitch, top_y), 3)
                if y > 0.0 and y not in ys:
                    ys.append(y)
            for s in (-1, 1):
                x = s * hw
                for y0 in ys:
                    _lay(name, min(x, x - s * ld), max(x, x - s * ld),
                         y0, y0 + lh, lw, pitch)
        elif kind == "festoon":
            # Strung along the inboard edge of whatever flanks the room -- in
            # a market that is the stall awning, whose eave the frame puts at
            # 2.29 m. Dense: the measurement's whole point is that a stall
            # carries 60-100 bulbs and not the six a generator would place.
            y0 = min(my, ceil - lh - 0.10)
            for x in (chan_lo + ld / 2, chan_hi - ld / 2):
                _lay(name, x - ld / 2, x + ld / 2, y0, y0 + lh, lw, pitch)
        elif kind == "deck":
            _lay(name, chan_c - ld / 2, chan_c + ld / 2, 0.0, lh, lw, pitch)
        else:
            raise ValueError(f"{place['key']}: unknown light kind {kind!r}")

    # THE DRESSING RUNS LAST, AND BACKS OFF UNTIL THE ROOM IS WALKABLE. A single global
    # density left 21 to 37 rooms impassable at every value tried, because what
    # blocks a room is its own proportions and the fixtures already in it, not
    # a constant. So it is offered the room at falling densities and the first
    # one a 0.9 m body can still cross end to end is the one that ships. A
    # generator that guarantees its own invariant beats a number I tuned.
    #
    # LAST, not mid-build: the first version ran before the props and the
    # light fittings, so its walkability trial judged a room that was not
    # finished yet. It accepted full density, the props went in on top, and
    # 21 rooms came out impassable -- including the brig, which is walkable
    # with no dressing at all. A trial has to run on what actually ships.
    # PER BAY, WITH THE BAY'S OWN SEED, AND ONLY AS FAR BACK AS `n_dress`.
    # Two reasons, and the second is the one that matters.
    #
    # 1. COST. Dressing is 26% of a `docking_bays` bay -- 25,500 triangles --
    #    and it is the layer a streaming system instantiates rather than bakes.
    #    `tiling()` decides how deep it reaches from the budget, not from a
    #    number chosen here.
    # 2. VARIETY. One `dress()` call over a 140 m room is one seed, and the
    #    generator would lay the same furniture against the same wall at the
    #    same pitch for the whole run -- a visible tile pattern, which is the
    #    failure `deck.py --degeneracy` exists to catch one level up. A seed per
    #    bay is what makes the repeat a place instead of a texture.
    #
    # The trial is per bay for a third reason that is not cost: it now runs
    # against the run's OWN solids clipped to the bay's window, computed once
    # instead of re-derived from the whole merged mesh at every density -- the
    # old form was O(bays x densities x run triangles) and would have made a
    # 140 m room quadratic in its own length.
    import dressing as _dress                                   # noqa: PLC0415
    run_boxes = _boxes(v, t, g, is_solid)
    dress_tris, dens_used = 0, None
    _walls = dress_walls(place)

    def _bay_walls(k):
        """The walls THIS bay actually has, which at a join is not four.

        THE GATE FOUND THIS AND IT IS THE FAILURE THE TILING EXISTS TO AVOID.
        `dressing.dress` ranks furniture against the walls it is given, and
        `"z-"`/`"z+"` are walls only for the two bays on the ends of the run.
        Given all four, every bay put a rank of furniture across the room at
        each of its own z faces -- so at a join two ranks stood back to back and
        SEALED the run. `casino` and `admin_complex` came back crossable bay by
        bay and not end to end, which `_selftest`'s "the lit room is still
        walkable" said in one line. A 22 m room a body is stopped halfway down
        is worse than the 11 m room it replaced.

        Same rule as `wall_faces` above, for the same reason, and a one-bay room
        gets exactly what it got before.
        """
        if n_bay <= 1:
            return _walls
        keep = {"x-", "x+"}
        if k == 0:
            keep.add("z-")
        if k == n_bay - 1:
            keep.add("z+")
        return tuple(x for x in _walls if x in keep)

    for k in range(n_bay - 1, -1, -1):          # from the door backwards
        if _near(k) >= n_dress:
            continue
        zc = _bay_z(k)
        window = [(n_, (b[0], b[1], b[2] - zc, b[3], b[4], b[5] - zc))
                  for n_, b in run_boxes
                  if b[5] > zc - bay_l / 2.0 - 1e-6
                  and b[2] < zc + bay_l / 2.0 + 1e-6]
        for _dens in DRESS_DENSITIES:
            dv, dt, dg, _dc = _dress.dress(
                place["key"], w - 2 * WALL_T_M, bay_l - 2 * WALL_T_M, ceil,
                arch, inset=(inset[0], inset[1]),
                seed=f"{place['key']}#{k}", density=_dens,
                walls=_bay_walls(k))
            _trial_boxes = window + _boxes(dv, dt, dg, is_solid)
            _ok = walkable(_trial_boxes, w, bay_l)
            if report is not None:
                report.setdefault("trials", []).append(
                    (_dens, _ok, len(_trial_boxes)))
            if _dens == 0.0 or _ok:
                # WHICH DENSITY IT SETTLED ON. Without this the only way to know
                # how much furniture a room actually got is to re-run the trial
                # from outside, which is a second copy of the rule that decides
                # it -- and every time this project has kept two copies of one
                # decision they have drifted. `report` is how a caller asks the
                # thing that decided. Across a tiled run it is the WORST bay's,
                # because that is the one a claim about the room has to survive.
                off, t0 = len(v), len(t)
                v.extend((x, y, z + zc) for x, y, z in dv)
                t.extend((a + off, b + off, c + off) for a, b, c in dt)
                g.extend((n_, lo + t0, hi + t0) for n_, lo, hi in dg)
                dress_tris += len(dt)
                dens_used = (_dens if dens_used is None
                             else min(dens_used, _dens))
                break
    if report is not None:
        report["density"] = dens_used
        report["dress_tris"] = dress_tris

    # POPULATION -- station/populace.py, and it runs LAST for the same reason
    # the dressing does: people are placed against the furniture that is
    # actually there, so somebody ends up ON a chair rather than near one. The
    # hour comes from STATION_HOUR so the whole station can be moved to 0300
    # with one number.
    #
    # `max_people` IS THE TILING'S CAP AND IT IS THE BIGGEST ONE. A baked body
    # is ~3,760 triangles and 51% of a `docking_bays` bay; at the room's own
    # derived density a 140 m bay ring holds 114 of them, which is 429,000
    # triangles of people in one room and more than the whole frame allowance.
    # `deck.CORRIDOR_INSTANCED` already made exactly this trade for the corridor
    # crowd -- 88% fewer triangles and the only form that can move -- and rooms
    # bake theirs because nothing has instanced them yet. So the DENSITY is the
    # room's own over its full length and the COUNT is capped at what `n_pop`
    # bays' worth is; `occupancy` is asked rather than assumed, so the cap is
    # stated in the same units the uncapped number is.
    import populace as _pop                                     # noqa: PLC0415
    _bay_people = _pop.occupancy(place["key"],
                                 (w - 2 * WALL_T_M) * (bay_l - 2 * WALL_T_M),
                                 STATION_HOUR, arch)
    _cap = max(1, int(round(_bay_people * n_pop)))
    pv, pt, pg, _ps = _pop.populate(
        place["key"], v, t, g, w - 2 * WALL_T_M, ln - 2 * WALL_T_M,
        hour=STATION_HOUR, arch=arch, seed=place["key"],
        max_people=_cap, g_ms2=_pop.place_gravity(place["key"]))
    if report is not None:
        report["people_cap"] = _cap
    if report is not None:
        # WHO IS IN THIS ROOM AND WHICH WAY THEY ARE FACING. A body is baked
        # into the merged mesh, so nothing downstream can recover its yaw by
        # looking at it -- and an inhabitant who turns to face the player has to
        # be turned FROM somewhere.
        report["actors"] = _ps.get("actors", [])
    if pt:
        off, t0 = len(v), len(t)
        v.extend(pv)
        t.extend((a + off, b + off, c + off) for a, b, c in pt)
        g.extend((n, lo + t0, hi + t0) for n, lo, hi in pg)

    return v, t, g


def machine_escapes(v, t, report, tol=0.0):
    """Every machine part that left the box its fixture declared.

    Returns [(group, kind, metres outside)] and is empty when the invariant
    holds. `report` is what `build(..., report=...)` filled in; the boxes come
    from `_fixture`, which is the only place that knows what was asked for.

    WHY THIS IS THE GATE THE CHANGE NEEDS. Since INV-130 `_solid_boxes` skips
    the nested part spans, so the interpenetration check cannot see inside a
    machine -- correctly, because a flange inside its own vessel is one solid.
    That leaves exactly one thing between an articulated fixture and a room it
    silently makes impassable: parts staying where the box was. Everything
    downstream -- `walkable`, `standpoint`, `collision.prop_boxes`, the
    interpenetration check -- reads that box and nothing else.
    """
    import dressing as _dress                                   # noqa: PLC0415
    out = []
    for nm, kind, t0, t1, lo, hi in report.get("machines", ()):
        if kind is None:
            continue
        d = _dress.machine_bounds_ok(v, t[t0:t1], 0, lo, hi, tol)
        if d > 1e-9:
            out.append((nm, kind, round(d, 4)))
    return out


def _boxes(v, t, g, pred):
    """AABBs of the groups whose name satisfies `pred`."""
    out = []
    for name, lo, hi in g:
        if not pred(name):
            continue
        idx = {i for tri in t[lo:hi] for i in tri}
        pts = [v[i] for i in idx]
        out.append((name, (min(q[0] for q in pts), min(q[1] for q in pts),
                           min(q[2] for q in pts), max(q[0] for q in pts),
                           max(q[1] for q in pts), max(q[2] for q in pts))))
    return out


def _solid_boxes(v, t, g):
    """AABBs of the room's solid objects -- props and fixtures, not shell.

    Ribs are excluded: they are wall articulation flush against a wall, and a
    prop legitimately stands in front of one. Light fittings are excluded for
    the same reason and one more: a deck channel is 20 mm proud and a wall
    course is 130 mm proud, neither of which a walker collides with.

    AND MACHINE PARTS ARE EXCLUDED, because they are not separate objects.
    Since INV-130 a fixture emits an OUTER span covering the whole machine and
    then part spans NESTED inside it -- a vessel's flanges, legs, stubs and
    ladder. Counting a part as a solid in its own right would report a flange
    interpenetrating the vessel it is a flange of, which is not two solids in
    one place; it is one solid. The outer span still owns the AABB, so every
    rule that reads this function -- the interpenetration gate, the walkability
    trial, `standpoint`, `collision.prop_boxes` -- sees exactly the box the
    fixture occupied before.

    The invariant that makes that safe is `dressing.machine_bounds_ok`: no part
    may leave its parent's box. `_selftest` measures it on every location, and
    the negative control -- a machine deliberately built oversize -- is there
    too, because a containment rule nobody has watched fail is a rule nobody
    has tested.
    """
    return _boxes(v, t, g, lambda n: n.startswith(("prop_", "fix_"))
                  and _MACH not in n)


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


# ---------------------------------------------------------------------------
# THE GATE: DOES THE GEOMETRY SPAN THE FOOTPRINT
# ---------------------------------------------------------------------------


def bay_signatures(v, t, plan):
    """One hash per bay, of that bay's own geometry IN ITS OWN FRAME.

    IDENTITY, NOT SIMILARITY, and it is `deck.py --degeneracy`'s question asked
    one level down. That gate hashes a PLACE and says two places whose geometry
    hashes the same are one place; the same argument applies exactly to two bays
    of one place, and it is the failure mode tiling introduces -- a 140 m room
    built as thirteen copies of one 10.77 m room is a texture, not a location.
    There is no raster, no threshold and nothing to tune, so there is nothing to
    argue with.

    Order-independent by construction: each triangle is hashed in its bay's
    local frame and the hashes are XORed, so two bays match only if they hold
    the same set of triangles in the same places. Sorting eight hundred thousand
    triangles to get the same answer would cost thirty times as much.
    """
    n, bl = plan["n"], plan["bay_l"]
    hl = n * bl / 2.0
    acc = [0] * n
    for a, b, c in t:
        pa, pb, pc = v[a], v[b], v[c]
        k = int(((pa[2] + pb[2] + pc[2]) / 3.0 + hl) / bl)
        k = min(n - 1, max(0, k))
        zc = -hl + (k + 0.5) * bl
        # Rotate to a fixed starting vertex so winding order alone cannot make
        # two identical triangles hash differently.
        tri = [(round(p[0], 4), round(p[1], 4), round(p[2] - zc, 4))
               for p in (pa, pb, pc)]
        i0 = tri.index(min(tri))
        key = repr(tri[i0:] + tri[:i0]).encode()
        acc[k] ^= int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(),
                                 "big")
    return [f"{a:016x}" for a in acc]


def footprint_ledger(schema, profile, places=None, legacy=False):
    """Metres of each location that are actually BUILT, measured off the mesh.

    THE NUMBER THIS PROJECT DID NOT HAVE. `deck.py --sweep` answers "how much of
    the station can I walk in" per LOCATION and reports 128 of 128; it is a count
    of locations REACHED, not of location BUILT, and the difference was 0.17% of
    the declared footprint. This measures the built extent off the emitted mesh
    -- not off the plan, not off `bays_in`, off the geometry -- so it can catch a
    plan that says 140 m and a builder that emits 11.

    `legacy=True` REBUILDS THE PRE-TILING CONTENT -- one bay per location, which
    is what `build` emitted for every session up to this one -- and is the
    negative control. This gate must fail on it, and it does: the station comes
    back at 1,280 m of the 18,790 m its own register declares, with the mesh
    short of the plan in 115 of 128 places. A gate that cannot fail on the
    content it was written for is measuring the wrong thing, which is the defect
    that cost this repository three layers of work.
    """
    import bespoke as _BSP                                      # noqa: PLC0415
    import deck as _D                                           # noqa: PLC0415
    if places is None:
        places = [p for p in dr.PLACES]
    rows = []
    was, _BSP.LEGACY_AXIAL = _BSP.LEGACY_AXIAL, bool(legacy)
    if was != _BSP.LEGACY_AXIAL:
        _BSP.reset_axial_memos()
        _TILING.clear()
    try:
        rows = _ledger_rows(schema, profile, places, legacy, _BSP, _D)
    finally:
        if was != _BSP.LEGACY_AXIAL:
            _BSP.LEGACY_AXIAL = was
            _BSP.reset_axial_memos()
            _TILING.clear()
    return rows


def _ledger_rows(schema, profile, places, legacy, _BSP, _D):
    """`footprint_ledger`'s loop, with the legacy switch already set."""
    rows = []
    for p in places:
        plan = tiling(schema, profile, p)
        composed = bool(plan.get("composed"))
        # A COMPOSED PLACE IS MEASURED ON THE MESH THAT IS ACTUALLY DRAWN.
        # `deck.room_geometry` is the function that decides which of the two
        # builds a place gets, so asking it is the only way to get a number
        # about the shipped room -- and building the generic fallback as well
        # would be two full builds of every composed place for a number nothing
        # reads. That was costing this 23-minute gate a third of its time.
        if composed:
            v, t, g, used = _D.room_geometry(schema, profile, p)
            zs = [q[2] for q in v]
            built_m = max(zs) - min(zs)
        else:
            v, t, g = build(schema, profile, p,
                            _tiles=(1, 1, 1) if legacy else None)
            used = "generic"
            zs = [q[2] for q in v]
            # The shell's deck, soffit and side walls run to the OUTER extent,
            # so the mesh is the interior length plus a wall at each end.
            built_m = (max(zs) - min(zs)) - 2 * WALL_T_M
        sigs = bay_signatures(v, t, plan) if plan["n"] > 1 and not legacy else []
        row = {
            "key": p["key"], "want_m": plan["want_l"],
            "plan_m": plan["built_l"], "built_m": built_m,
            "n_want": plan["n_want"], "n": plan["n"],
            "n_dress": plan["n_dress"], "n_pop": plan["n_pop"],
            "capped": plan["capped"], "tris": len(t),
            "est": plan["tris"], "cap": plan["cap"],
            # EMPTY SLICES ARE NOT TWINS. A generic tiled place instances a
            # whole bay, so every bay holds triangles and every signature is
            # meaningful. A composed GROW place is not instanced -- `plant` is
            # one continuous cell 442 m long, and a single 442 m box
            # contributes twelve triangles whose centroids land in two of the
            # thirty-two slices. Thirty empty slices hashing to zero is not
            # thirty copies of one room, it is a long object, and counting it
            # as wallpaper would be the gate failing on the shape of its own
            # arithmetic -- the same class of mistake as `roomnav.Grid.snap`'s
            # "every failure at exactly z_half - 0.1", which was an identity of
            # the gate rather than a fact about the station.
            "twins": (len([x for x in sigs if x != f"{0:016x}"])
                      - len({x for x in sigs if x != f"{0:016x}"})),
            "composed": composed,
            "module_m": built_m if composed else None,
            "used": used,
            # WHY A COMPOSED PLACE IS SHORTER THAN ITS FOOTPRINT, IN ITS OWN
            # WORDS. This is what lets the gate below tell "built to its
            # footprint" apart from "legitimately smaller than its footprint,
            # and here is the reason" -- the distinction that stops a "one"
            # mode being a way to duck the assertion.
            "mode": plan.get("mode"), "why": plan.get("why") or "",
            "band_m": plan.get("band_l"),
        }
        rows.append(row)
    return rows


def spans_footprint(schema, profile, legacy=False, verbose=False):
    """Assert that a location's geometry spans the footprint it declares.

    Three properties, and each of them can fail on its own:

    1. THE MESH FOLLOWS THE PLAN. What `tiling()` says is built and what `build`
       emits must agree to a centimetre. This is the one that fails on the
       pre-tiling content, by an order of magnitude, in 115 of 128 places.
    2. THE PLAN IS THE FOOTPRINT UNLESS THE BUDGET SAYS OTHERWISE. A place is
       built to its full declared length; a place that is not must be one whose
       own measured per-bay cost puts the full length over `budget.py`'s frame
       allowance, and the shortfall is printed in metres. There is no list of
       exemptions to grow -- the only thing that can shorten a room is its own
       triangle cost, and that is a number, not a decision.
    3. NO TWO BAYS OF ONE PLACE ARE THE SAME BAY. `bay_signatures`, above.

    ASSERTED OVER ALL 128 NOW, AND IT USED TO BE ASSERTED OVER 91. The composed
    places were measured and printed and not asserted, on the reasoning that
    *"this file cannot make `zocalo` reach 120 m and asserting that it does
    would be a gate demanding a fix it does not own"*. That was true while
    `bespoke` had no answer to the question; `bespoke.AXIAL` is that answer, so
    the exemption goes and all three properties above apply to a composed row:

      1. its mesh is what `bespoke.axial_span_m` says it is, to a centimetre --
         and that number is now what `deck.room_interior_half_m` sizes the
         collision shell from, so property 1 on a composed row is the assertion
         that a player cannot see geometry outside the room they can walk in;
      2. it is built to its footprint UNLESS it is one of two stated things --
         over the frame allowance (`capped`, with the triangle arithmetic), or a
         place whose true form is ONE ROOM (`mode == "one"`, with the sentence
         from `bespoke.AXIAL` saying which room and why). Anything else fails.
         **The "one" mode cannot be used to duck this**: a module declared
         `grow` that comes back short with no cap fails exactly as a generic
         place does;
      3. no two units of a grown place are the same unit.

    Prints the station's built length against its declared length, because that
    is the figure the owner's complaint is actually about and no other gate in
    this repository computes it.
    """
    rows = footprint_ledger(schema, profile, legacy=legacy)
    mine = [r for r in rows if not r["composed"]]
    theirs = [r for r in rows if r["composed"]]
    bad_plan = [r for r in rows if abs(r["built_m"] - r["plan_m"]) > 0.01]
    # THE THREE REASONS A ROW MAY BE SHORT, AND THERE IS NO FOURTH. Over the
    # budget, or a place whose true form is one room and says so; everything
    # else is a failure. `one_room` is counted and printed rather than filtered
    # out, so it can never become an exemption list nobody reads.
    one_room = [r for r in theirs if r["mode"] == "one"
                and r["plan_m"] < r["want_m"] - 0.01]
    excused = {id(r) for r in one_room}
    short = [r for r in rows if r["plan_m"] < r["want_m"] - 0.01
             and not r["capped"] and id(r) not in excused]
    twins = [r for r in rows if r["twins"]]
    want = sum(r["want_m"] for r in mine)
    built = sum(r["built_m"] for r in mine)
    capped = [r for r in mine if r["capped"]]

    tris = sum(r["tris"] for r in rows)
    print(f"  {len(mine)} places built here   {built:,.0f} m of {want:,.0f} m "
          f"declared ({100.0 * built / want:.1f}%)   "
          f"{len(mine) - len(capped)} at full footprint, "
          f"{len(capped)} capped by budget.py")
    if theirs:
        tw = sum(r["want_m"] for r in theirs)
        tb = sum((r["module_m"] or r["built_m"]) for r in theirs)
        tcap = [r for r in theirs if r["capped"]]
        print(f"  {len(theirs)} places built by a bespoke module   "
              f"{tb:,.0f} m of {tw:,.0f} m declared "
              f"({100.0 * tb / max(tw, 1e-9):.1f}%)   "
              f"{len(theirs) - len(tcap) - len(one_room)} at full footprint, "
              f"{len(tcap)} capped by budget.py, "
              f"{len(one_room)} whose true form is ONE ROOM")
        for r in sorted(one_room, key=lambda r: r["want_m"] - r["plan_m"],
                        reverse=True):
            print(f"     one room {r['key']:<21} {r['built_m']:>7.1f} m of "
                  f"{r['want_m']:>7.1f} m  -- {r['why'][:96]}")
        for r in sorted(tcap, key=lambda r: r["want_m"] - r["plan_m"],
                        reverse=True):
            print(f"     capped   {r['key']:<21} {r['built_m']:>7.1f} m of "
                  f"{r['want_m']:>7.1f} m  -- {r['why'][:96]}")
    # PER BUILT METRE OVER EVERY METRE THAT IS BUILT. This used to divide the
    # whole station's triangles by only the metres `rooms.py` builds, which was
    # right while the composed places were unasserted and is not now that they
    # are: 2,833 m of built room was in the numerator and not in the
    # denominator, which reads as a third worse than the truth.
    built_all = built + sum((r["module_m"] or r["built_m"]) for r in theirs)
    print(f"  {tris:,d} triangles over the {len(rows)}, "
          f"{tris / max(built_all, 1e-9):,.0f} per built metre "
          f"over {built_all:,.0f} m; "
          f"worst place {max(r['tris'] for r in rows):,d} against a "
          f"{max(r['cap'] for r in rows):,d} frame allowance")
    # AND WHERE THE ESTIMATE WAS WRONG, PRINTED RATHER THAN LEFT TO BE NOTICED.
    # `tiling()` picks the bay count from three probe builds and a linear model,
    # `fixed + n*marginal`, so the count is chosen against an ESTIMATE and the
    # built room is the truth. Six places land over their own ceiling by up to a
    # third. That is a real overrun and it is stated here because a cap nobody
    # reports is the "silent cap reads as coverage" failure STATE.md section 13
    # names -- one level in, applied to the cap's own arithmetic.
    over = sorted((r for r in mine if r["cap"] and r["tris"] > r["cap"]),
                  key=lambda r: -r["tris"])
    if over:
        print(f"  {len(over)} of {len(mine)} land OVER the allowance the plan "
              f"was chosen against (estimate low): "
              + ", ".join(f"{r['key']} {r['tris']:,}/{r['est']:,} est"
                          for r in over[:5]))
    if verbose or capped:
        for r in sorted(capped, key=lambda r: r["want_m"] - r["built_m"],
                        reverse=True)[:12]:
            print(f"     capped {r['key']:<22} {r['built_m']:>7.1f} m of "
                  f"{r['want_m']:>7.1f} m  ({r['n']}/{r['n_want']} bays, "
                  f"dressed {r['n_dress']}, peopled {r['n_pop']}, "
                  f"{r['est']:,} tri est vs {r['cap']:,})")
    if verbose:
        for r in sorted(mine, key=lambda r: -r["built_m"])[:20]:
            print(f"     {r['key']:<22} {r['built_m']:>7.1f} m  "
                  f"{r['n']:>3d} bays  {r['tris']:>9,d} tri")
        for r in sorted(theirs, key=lambda r: (r["module_m"] or 0)
                        - r["want_m"])[:12]:
            print(f"     bespoke {r['key']:<20} "
                  f"{(r['module_m'] or 0):>7.1f} m of {r['want_m']:>7.1f} m "
                  f"({r.get('used')})")

    ok = True
    if bad_plan:
        ok = False
        print(f"FAIL  the mesh does not span what the plan says it does "
              f"({len(bad_plan)} of {len(rows)})")
        for r in bad_plan[:8]:
            print(f"        {r['key']:<22} built {r['built_m']:.2f} m, "
                  f"plan {r['plan_m']:.2f} m, declared {r['want_m']:.2f} m")
    if short:
        ok = False
        print(f"FAIL  {len(short)} places are short of their footprint with no "
              f"budget cap and no one-room declaration to account for it: "
              f"{[r['key'] for r in short][:8]}")
        for r in short[:6]:
            print(f"        {r['key']:<22} built {r['plan_m']:.2f} m of "
                  f"{r['want_m']:.2f} m  mode={r['mode']}  {r['why'][:60]}")
    if twins:
        ok = False
        print(f"FAIL  {len(twins)} places contain two byte-identical bays: "
              f"{[(r['key'], r['twins']) for r in twins][:8]}")
    if ok:
        print("PASS  every location's geometry spans its own footprint, or is "
              "capped by a stated triangle budget, or is one room and says so; "
              "and no bay is a copy")
    return ok


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
    w, ln = built_span_m(schema, profile, place)
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
    # ONE BUILD PER PLACE, ANSWERING EVERY PER-PLACE QUESTION. This loop, the
    # furnished-density loop, the "every room has scenery" comprehension and the
    # light-fitting loop each used to rebuild all 128 places -- four full builds
    # apiece, which was affordable at one bay each and is not now that a place
    # is its whole footprint. The checks are unchanged and still fire where they
    # did; only the mesh they read is built once.
    total = 0
    dark, pierced, outside, unwalkable = [], [], [], []
    lamp_total = 0
    furnished, has_fix = {}, {}
    for p in places:
        rep = {}
        v, t, g = build(schema, profile, p, report=rep)
        total += len(t)
        check(f"{p['key']}: builds", len(t) > 40, f"{len(t)} tri")
        # COVERAGE, NOT A SUM. Groups NEST: a person's `npc_standing_3`
        # span contains their eight `..._npc_skin_*` parts, exactly as the
        # corridor kit's `wall_assembly` contains its skirt and rail band. The
        # sum was a proxy that held only while nothing nested, and it fired on
        # correct data the moment bodies carried their own part names through.
        covered = set()
        for _n, lo, hi in g:
            covered.update(range(lo, hi))
        check(f"{p['key']}: every triangle grouped",
              len(covered) == len(t) and all(0 <= lo <= hi <= len(t)
                                             for _n, lo, hi in g),
              f"{len(covered)} of {len(t)} covered")
        w, ln = built_span_m(schema, profile, p)
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

        # --- EVERY MACHINE PART STAYS IN THE BOX ITS FIXTURE DECLARED -----
        # INV-130's load-bearing invariant. `_solid_boxes` skips the nested
        # part spans, so the interpenetration check above no longer sees a
        # flange inside its own vessel -- correct, and it means the ONLY thing
        # standing between an articulated machine and a room it quietly makes
        # impassable is this. Measured against the box `_fixture` asked for,
        # which is why `report["machines"]` exists.
        #
        # It has fired twice on real content and neither case was visible in
        # the probe boxes the builders were developed against: a 0.70 m `over`
        # crane whose hoist block hung 56 mm below its own rail, and a
        # patch-panel cabinet that ran its cable way 0.29 m sideways out of a
        # 0.35 m deep footprint and through the console in front of it.
        esc = machine_escapes(v, t, rep)
        check(f"{p['key']}: no machine part leaves the box it replaced",
              not esc, f"{len(esc)}: {esc[:3]}")

        # Walkability, measured rather than assumed. The old form subtracted a
        # hardcoded 0.9 m of prop depth per side; once fixtures started eating
        # the walls that number was fiction, and a room could pass this while
        # having no floor left to stand on.
        check(f"{p['key']}: the room is still walkable",
              walkable(boxes, w, ln),
              f"no {WALK_M:.1f} m path across a {w:.1f}x{ln:.1f} m bay")

        # --- what the later checks need, taken off this one build ----------
        furnished[p["key"]] = (
            sum(1 for n_, _lo, _hi in g
                if n_.startswith("prop_") or n_.startswith("fix_")), w * ln)
        has_fix[p["key"]] = any(n_.startswith("fix_") for n_, _l, _h in g)

        # LIGHT FITTINGS. Placed, not inside anything solid, inside the room,
        # and not closing it. The containment bound is the BUILT run and not
        # `bay_span_m`: a tiled room's light courses repeat the whole length of
        # it, so measured against one bay every fitting past the first would
        # read as outside the room it lights.
        want_l = {n_ for n_, *_ in lights_for(p)}
        got_l = {n_ for n_, _l, _h in g if n_.startswith("light_")}
        lamps = _boxes(v, t, g, lambda n_: n_.startswith("light_"))
        lamp_total += len(lamps)
        if want_l - got_l:
            dark.append((p["key"], sorted(want_l - got_l)))
        # A fitting inside a furnace stack lights the inside of the furnace.
        # Ribs count here and do not for props: a chair in front of an
        # articulated wall is a chair; a light course through one is a strip
        # of light passing through structure.
        solid = _boxes(v, t, g, lambda n_: n_.startswith(("prop_", "fix_"))
                       or n_.endswith("_rib"))
        for ln_, lb in lamps:
            if any(_overlaps(lb, sb) for _sn, sb in solid):
                pierced.append((p["key"], ln_))
                break
        ceil_p = ceiling_m(p)
        for ln_, lb in lamps:
            if (lb[0] < -w / 2 - WALL_T_M - 1e-6
                    or lb[3] > w / 2 + WALL_T_M + 1e-6
                    or lb[2] < -ln / 2 - WALL_T_M - 1e-6
                    or lb[5] > ln / 2 + WALL_T_M + 1e-6
                    or lb[1] < -1e-6 or lb[4] > ceil_p + 1e-6):
                outside.append((p["key"], ln_))
                break
        # The deck channel is 20 mm proud and the warm practical is 100 mm
        # proud at hip height. Neither should close a room, and the flood fill
        # is the only thing that can say so.
        # PEOPLE ARE NOT WALLS. An NPC is an agent: a player walks around one
        # and one steps aside, so a crowded bar is walkable and a bar with a
        # locker across the door is not. Counting bodies as permanent obstacles
        # made 11 rooms fail the moment the population generator was wired in,
        # which is the wrong answer to a right-looking question.
        #
        # THE EXEMPTION IS EARNED BELOW, not assumed: a separate check asserts
        # no body is spawned INSIDE solid furniture, which is a real defect and
        # the one this exclusion could otherwise hide.
        if not walkable(_boxes(v, t, g, lambda n_: not (
                n_.endswith(("_deck", "_soffit", "_wall", "_rib")
                             + _TRIM_SUFFIXES)
                or n_.startswith("npc_"))), w, ln):
            unwalkable.append(p["key"])

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
    # AREA OVER THE WHOLE BUILT RUN, not over one bay of it. Left as
    # `bay_span_m` this metric goes vacuous the moment tiling lands: the prop
    # count would be the run's and the area one bay's, so a 13-bay room would
    # score thirteen times better for building nothing new. A metric whose
    # numerator and denominator describe different rooms is not a metric.
    worst = None
    for p in places:
        n, area = furnished[p["key"]]
        per = area / max(n, 1)
        if worst is None or per > worst[1]:
            worst = (p["key"], per, n)
        check(f"{p['key']}: the bay is furnished, not an empty hall",
              per < 30.0, f"{per:.0f} m2 per prop ({n} props in "
                          f"{area:.0f} m2)")
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
    # AND THE FUNCTION TABLE MAY NOT MOVE THAT COUNT.  The gate above has one
    # room of margin, so the constraint is stated where it can fire rather than
    # only in FUNCTION_HEIGHT's comment.  Negative control: remove the
    # `FUNCTION_HEIGHT_CAP_M` clamp in `ceiling_m` and this names hydroponics,
    # fusion_core and cryo_storage.
    _was_tall = [p["key"] for p in places
                 if max(PLACE_CEILING.get(p["key"],
                                          CEIL_BY_ARCHETYPE.get(archetype(p),
                                                                2.9)),
                        max((PROPS[k][2] for k in p["interacts"]
                             if k in PROPS), default=0.0) + CEIL_HEADROOM_M)
                 > it.DECK_PITCH_M]
    check("keying height on function did not make any room multi-deck",
          not (set(tall) - set(_was_tall)),
          f"newly tall: {sorted(set(tall) - set(_was_tall))}")
    check("...and it did give the station more than eleven ceiling heights",
          len({round(ceiling_m(p), 2) for p in places}) >= 25,
          f"{len({round(ceiling_m(p), 2) for p in places})} distinct heights")

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

    # --- AND NO FIXTURE IS ONE -- INV-130 ---------------------------------
    # `MACHINE_KIND` must cover every declared fixture in both directions, so
    # a fixture added without a shape is a build failure rather than a box that
    # quietly comes back. The negative control is one line: delete an entry and
    # this fires naming it.
    import dressing as _dress                                   # noqa: PLC0415
    fx_names = set()
    for _fx in (list(FIXTURES.values()) + list(PLACE_FIXTURES.values())
                + list(PLAN_ELEMENTS.values())):
        fx_names.update(n for n, *_r in _fx)
    check("every fixture has a machine shape",
          not (fx_names - set(MACHINE_KIND)),
          f"box-only: {sorted(fx_names - set(MACHINE_KIND))}")
    check("no machine shape is declared for a fixture that does not exist",
          not (set(MACHINE_KIND) - fx_names),
          f"orphans: {sorted(set(MACHINE_KIND) - fx_names)}")
    check("every machine kind named here is one `dressing.py` can build",
          not (set(MACHINE_KIND.values()) | set(PROP_KIND.values()))
          - set(_dress.MACHINES),
          f"unknown: {sorted((set(MACHINE_KIND.values()) | set(PROP_KIND.values())) - set(_dress.MACHINES))}")
    # PROPS are allowed to be unmapped only where a machine cannot be built --
    # `platform_edge` is 0.00 m across and `deck_marking` is 10 mm tall. The
    # list is PRINTED rather than silently tolerated, so it cannot grow.
    prop_box_only = sorted(k for k in PROPS if k not in PROP_KIND)
    check("every declared prop has a machine shape or a stated reason",
          not prop_box_only, f"box-only: {prop_box_only}")
    tiny = sorted(k for k, s in PROPS.items()
                  if min(s[0], s[1], s[2]) < MACHINE_MIN_M)
    print(f"  props still emitted as a plain box because a declared dimension "
          f"is under {MACHINE_MIN_M} m: {tiny}")
    unscened = [p["key"] for p in places if not has_fix[p["key"]]]
    check("every room contains scenery it does not declare",
          not unscened, f"{len(unscened)}: {unscened[:6]}")
    # A fixture's whole point is being present WITHOUT being interactable. If
    # one ever gets a PROPS entry the two systems have merged and the honesty
    # check above ("no prop geometry nothing declares") stops meaning anything.
    _allfix = ({n for a in FIXTURES for n, *_ in FIXTURES[a]}
               | {n for k in PLACE_FIXTURES for n, *_ in PLACE_FIXTURES[k]})
    dual = sorted(_allfix & set(PROPS))
    check("no fixture is also a prop", not dual, f"{dual}")

    # --- PLACE_FIXTURES: the per-place machinery --------------------------
    # Four properties, and every one of them is a way this table can be wrong
    # while every other gate stays green.
    #
    # 1. A key that names no place is scenery nothing will ever build -- the
    #    same class as a light fitting nobody emits. It reads as covered and
    #    is not.
    _keys = {q["key"] for q in dr.PLACES}
    ghost_fx = sorted(set(PLACE_FIXTURES) - _keys)
    check("every PLACE_FIXTURES key is a real place",
          not ghost_fx, f"{ghost_fx}")
    ghost_ce = sorted(set(PLACE_CEILING) - _keys)
    check("every PLACE_CEILING key is a real place", not ghost_ce,
          f"{ghost_ce}")
    # 2. AND THE OVERRIDE MUST ACTUALLY OVERRIDE. `fixtures_for` could fall
    #    back to the archetype through a typo in the lookup and every room
    #    would still build, furnished, walkable and lit -- with a furnace in
    #    the reactor hall. This asserts the swap happened.
    _sub = [k for k in PLACE_FIXTURES
            if {n for n, *_ in fixtures_for(dr.by_key(k))}
            != {n for n, *_ in PLACE_FIXTURES[k]}]
    check("a place with its own fixtures gets them, not its archetype's",
          not _sub, f"{_sub}")
    # AND THE PLAN ELEMENTS TAKE THE CENTRELINE OFF IT, which is a real change
    # to this rule and is stated here rather than left for the diff to imply:
    # a place whose own function puts something down the middle of the floor
    # does not also get its archetype's spine, because they are the same cubic
    # metre and the element is what THIS place is for. `fabrication` gets a
    # `cell` element, which is not a centreline, so it still gets all three
    # industrial fixtures verbatim.
    _spine = {n for n, *_r, k in FIXTURES["industrial"] if k == "spine"}
    check("...and a place without them still gets its archetype's, less any "
          "centreline its own plan takes",
          {n for n, *_ in fixtures_for(dr.by_key("fabrication"))}
          == {n for n, *_ in FIXTURES["industrial"]} - _spine
          and bool(_spine))
    check("...and a place whose own plan takes the centreline loses the "
          "archetype's spine",
          {n for n, *_ in fixtures_for(dr.by_key("alpha_substation"))}
          == {n for n, *_, k in FIXTURES["industrial"] if k != "spine"}
          and any(k == "spine" for *_r, k in FIXTURES["industrial"]))
    # NEGATIVE CONTROL, run rather than described: hand the resolver a place
    # whose key is in neither table and confirm it falls back, and hand it one
    # that is in both and confirm it does not.
    _probe = dict(dr.by_key("reactor_hall"))
    _probe["key"] = "__not_in_place_fixtures__"
    _probe["functions"] = ("storage",)   # a rank, so the spine rule does not fire
    check("the override test can fail",
          {n for n, *_ in fixtures_for(_probe)}
          == {n for n, *_ in FIXTURES[archetype(_probe)]}
          and ceiling_m(_probe) == CEIL_BY_ARCHETYPE[archetype(_probe)],
          "a place NOT in the tables still took an override")
    # --- `place_interacts`, on rooms built to make it fail -----------------
    # THE STATION DOES NOT REACH THESE PATHS TODAY and that is exactly why
    # they are tested here rather than left to the audit. Measured over all
    # fourteen bespoke-composed places, `turned` is 0: once the doorway became
    # a RECTANGLE rather than a depth, every declared prop fitted the way
    # round it was declared. The turn and the drop are robustness for content
    # that does not exist yet -- the observation domes are next and are round
    # -- and an untested branch is where the transposed `pw`/`pd` in the first
    # version of this hid.
    def _plc(w_m, l_m, tok="bunk", **kw):
        pr = dict(dr.by_key("qtr_civilian"))
        pr["key"] = "__interact_probe__"
        pr["interacts"] = [tok]
        pv, pt, pg = [], [], []
        got = place_interacts(pv, pt, pg, pr, w_m / 2.0, l_m / 2.0, 2.6, **kw)
        return got, [n for n, _a, _b in pg if n == "prop_" + tok]

    # A 2.05 x 0.95 m bunk in a room 16 m wide and 3.8 m deep -- the shape
    # `qtr_transient` actually is -- cannot run along the shallow axis and has
    # to turn. The room is deliberately shallower than the 0.6 m end margins
    # plus the bunk's length allow.
    _turn, _tg = _plc(16.0, 3.0)
    check("a prop too long for a shallow room TURNS rather than vanishing",
          _turn["turned"] == 1 and not _turn["dropped"] and _tg,
          f"{_turn} {_tg}")
    # ... and the control: shrink the OTHER axis too and there is nowhere to
    # put it, so it is reported dropped rather than silently absent.
    _drop, _dg = _plc(1.6, 2.0)
    check("...and is REPORTED dropped when neither way round fits",
          _drop["dropped"] == ["bunk"] and not _dg, f"{_drop} {_dg}")
    # The doorway rectangle bounds only what is IN the lane. Same room, same
    # bunk, with a lane down the middle: the bunk stands beside it.
    _lane, _lg = _plc(16.0, 8.0, keep_clear=(-1.3, 1.3, -2.0))
    check("the doorway lane does not reserve the whole near band",
          not _lane["dropped"] and _lg, f"{_lane} {_lg}")
    # ... and the control ON that: a lane as wide as the room DOES bound it,
    # or the rectangle is not being applied at all.
    _wide, _wg = _plc(16.0, 8.0, keep_clear=(-99.0, 99.0, -3.4))
    check("...and a lane spanning the room bounds every prop in it",
          _wide["dropped"] == ["bunk"] and not _wg, f"{_wide} {_wg}")
    # `skip` is what stops a room getting two of the same object.
    _skip, _sg = _plc(16.0, 8.0, skip=("bunk",))
    check("a skipped token is not built a second time",
          not _sg and _skip["floor"] == 0, f"{_skip} {_sg}")

    # 3. EVERY GROUP THIS TABLE EMITS MUST CARRY A MATERIAL. `materials.py` is
    #    not editable from here, `resolve` matches by longest bind FRAGMENT,
    #    and the natural names for these objects (`fix_containment_vessel`,
    #    `fix_suit_locker_bank`) resolve to None -- which would ship ten rooms
    #    of unmaterialled machinery and take station/test_materials_layer3.py
    #    down with them. So the naming rule is asserted where it is used.
    import materials as _mat                                    # noqa: PLC0415
    unpainted = sorted(f"fix_{n}" for k in PLACE_FIXTURES
                       for n, *_ in PLACE_FIXTURES[k]
                       if _mat.resolve_any(f"fix_{n}", "interior") is None)
    check("every per-place fixture resolves to a material",
          not unpainted, f"{len(unpainted)}: {unpainted[:6]}")
    check("the material check can fail -- the natural names do NOT resolve",
          _mat.resolve_any("fix_containment_vessel", "interior") is None
          and _mat.resolve_any("fix_suit_locker_bank", "interior") is None,
          "materials.py has grown these binds -- rename the fixtures and "
          "delete this control")
    # 4. A PIECE WIDER THAN ITS OWN SLOT OVERLAPS ITS NEXT INSTANCE, and that
    #    surfaces as an interpenetration failure a long way from its cause.
    #    `build` repeats a fixture `int(ln / FIXTURE_PITCH_M)` times in slots
    #    of `ln / nz`, so the widest safe piece is FIXTURE_PITCH_M less a
    #    working gap. Asserted on the declaration rather than waiting for the
    #    clash, because the clash names two fixtures and not the rule.
    wide = sorted((k, n, w) for k in PLACE_FIXTURES
                  for n, w, _d, _h, _kd in PLACE_FIXTURES[k]
                  if w > FIXTURE_PITCH_M - 0.3)
    check("no per-place fixture is wider along z than its own repeat slot",
          not wide, f"{wide[:4]}")

    # --- PLACE_LIGHTS: a room may relamp, but only from the measured set ---
    ghost_li = sorted(set(PLACE_LIGHTS) - _keys)
    check("every PLACE_LIGHTS key is a real place", not ghost_li,
          f"{ghost_li}")
    _known = {n for a in LIGHTS for n, *_ in LIGHTS[a]}
    _new = sorted({n for k in PLACE_LIGHTS for n, *_ in PLACE_LIGHTS[k]}
                  - _known)
    check("a per-place light set uses only fittings LIGHTS already declares",
          not _new,
          f"{_new} -- export_scene.py asserts every fitting is a measured "
          f"source or a measured emissive, and it is not editable from here")
    _sub = [k for k in PLACE_LIGHTS
            if {n for n, *_ in lights_for(dr.by_key(k))}
            != {n for n, *_ in PLACE_LIGHTS[k]}]
    check("a place with its own light set gets it, not its archetype's",
          not _sub, f"{_sub}")
    # The defect this exists for, asserted as a RELATION rather than a name:
    # the fitting it replaced is the one whose spacing scales with mount height
    # and whose energy does not, so in a low room it packs floods overhead.
    check("the relamped gallery is off the height-scaled flood",
          all(n not in LIGHT_PITCH_RATIO
              for n, *_ in lights_for(dr.by_key("coolant_gallery")))
          and any(n in LIGHT_PITCH_RATIO
                  for n, *_ in LIGHTS[archetype(dr.by_key("coolant_gallery"))]),
          "coolant_gallery is 3.20 m and its archetype lamps a 7.5 m hall")

    # --- lights: the room is not black ------------------------------------
    # LAYER 4's floor. `export_scene.fixture_lights` makes one source per
    # tagged `light_*` group and nothing else in an interior emits, so a room
    # with no fitting renders BLACK -- which is what all 68 of these did until
    # this table existed. The gate is therefore not "are there lights" but
    # "does every room get every fitting its archetype declares", because the
    # placement routine is allowed to skip a fitting it cannot fit and a room
    # that quietly lost its wall course would look merely dim.
    unlit = [a for a, _ in ARCHETYPES if not LIGHTS.get(a)]
    check("every archetype has light fittings",
          not unlit and bool(LIGHTS.get("generic")), f"no lights for {unlit}")
    nopitch = sorted({n for a in LIGHTS for n, _w, _d, _h, k, _y in LIGHTS[a]
                      if k != "key" and n not in LIGHT_PITCH_M
                      and n not in LIGHT_PITCH_RATIO})
    check("every repeated fitting has a measured or derived pitch",
          not nopitch, f"{nopitch}")
    kinds = {k for a in LIGHTS for _n, _w, _d, _h, k, _y in LIGHTS[a]}
    check("no light declares a kind the builder cannot place",
          kinds <= {"ceiling", "key", "course", "festoon", "deck"}, f"{kinds}")
    # A fitting is neither a prop nor a fixture, for the same reason a fixture
    # is not a prop: the moment one name appears in two tables the honesty
    # checks above stop partitioning anything.
    lit_names = {n for a in LIGHTS for n, *_ in LIGHTS[a]}
    check("no light fitting is also a prop or a fixture",
          not (lit_names & set(PROPS))
          and not (lit_names & {n for a in FIXTURES for n, *_ in FIXTURES[a]}),
          f"{sorted(lit_names & set(PROPS))}")
    check("every fitting name is tagged so the exporter can find it",
          all(n.startswith("light_") for n in lit_names),
          f"{sorted(n for n in lit_names if not n.startswith('light_'))}")

    # `dark`, `pierced`, `outside`, `unwalkable` and `lamp_total` are filled in
    # the single geometry pass above -- this loop used to be the fourth full
    # rebuild of all 128 places.
    check("no room renders black -- every fitting its archetype declares is "
          "placed", not dark, f"{len(dark)}: {dark[:4]}")
    check("no light fitting is inside something solid",
          not pierced, f"{len(pierced)}: {pierced[:4]}")
    check("every light fitting is inside the room it lights",
          not outside, f"{len(outside)}: {outside[:4]}")
    # THE EXEMPTION ABOVE IS EARNED HERE, not assumed. Adding the articulation
    # trim to the flood fill's ignore list would otherwise be exactly the move
    # this project keeps catching itself at: a gate found something, and the
    # gate was changed. Trim is genuinely not an obstacle -- a 22 mm deck joint
    # and a 35 mm skirting are things you walk over and past -- but that is a
    # claim about DIMENSIONS, so it is measured. Make a "skirting" half a metre
    # deep and this fails, and the walkability exemption stops applying to it.
    fat = []
    for p in places[:12]:
        v, t, g = build(schema, profile, p)
        ceil_ = ceiling_m(p)
        for nm, lo, hi in g:
            # A MACHINE PART IS NOT ROOM TRIM, and the two collide by name:
            # `dressing`'s vessel builder emits a `plant_conduit` part, and
            # `_conduit` is in `_TRIM_SUFFIXES`, so `fusion_core`'s reactor drum
            # was being measured against the rule for skirtings. Its containment
            # is `machine_escapes`' job and is gated there; this check is about
            # the bands `articulate` puts on the SHELL.
            if not nm.endswith(_TRIM_SUFFIXES) or _MACH in nm:
                continue
            pts = [v[i] for tri in t[lo:hi] for i in tri]
            if not pts:
                continue
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            zs = [q[2] for q in pts]
            thin = min(max(xs) - min(xs), max(ys) - min(ys),
                       max(zs) - min(zs))
            # Either it is thinner than a step, or it is above head height.
            if thin > TRIM_MAX_PROUD_M and min(ys) < TRIM_HEAD_M:
                fat.append((p["key"], nm, round(thin, 3)))
    check("every articulation band is trim, not an obstacle -- thinner than a "
          "step or above head height", not fat, f"{len(fat)}: {fat[:3]}")
    # NOBODY IS INSIDE THE FURNITURE. This is what buys the exemption above.
    # A body merged into a locker is invisible to a walkability test that
    # ignores bodies, and it is exactly the defect that exclusion could hide.
    embedded = []
    for p in places[:14]:
        v, t, g = build(schema, profile, p)
        solids = _boxes(v, t, g, lambda n: n.startswith(("fix_", "dress_"))
                        and not n.startswith("dress_clutter"))
        for nm, nb in _boxes(v, t, g, lambda n: n.startswith("npc_")):
            cx = (nb[0] + nb[3]) / 2.0
            cz = (nb[2] + nb[5]) / 2.0
            for _sn, sb in solids:
                if (sb[0] + 0.12 < cx < sb[3] - 0.12
                        and sb[2] + 0.12 < cz < sb[5] - 0.12
                        and sb[4] > 0.8):
                    embedded.append((p["key"], nm))
                    break
    check("no NPC is standing inside a solid fitting",
          not embedded, f"{len(embedded)}: {embedded[:3]}")

    check("the lit room is still walkable",
          not unwalkable, f"{len(unwalkable)}: {unwalkable[:6]}")
    print(f"  lights: {lamp_total} fittings over {len(places)} rooms "
          f"({lamp_total / len(places):.1f} each), "
          f"{len(lit_names)} distinct types")

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

    # The light gates are only worth their runtime if they can fire. The
    # interpenetration one in particular went green on its first run and that
    # is exactly when a gate deserves least trust -- four of this project's
    # material rules were wrong about the corpus rather than the corpus being
    # clean. So: take a real room, put a lamp inside its own furnace, and
    # confirm the check that just passed 68 rooms says so.
    fv, ft, fg = build(schema, profile, dr.by_key("fabrication"))
    fx = _boxes(fv, ft, fg, lambda n: n.startswith("fix_"))
    check("there is a fixture to hide a lamp inside", bool(fx))
    x0, y0, z0, x1, y1, z1 = fx[0][1]
    _box(fv, ft, fg, "light_probe",
         ((x0 + x1) / 2 - 0.1, (y0 + y1) / 2 - 0.1, (z0 + z1) / 2 - 0.1),
         ((x0 + x1) / 2 + 0.1, (y0 + y1) / 2 + 0.1, (z0 + z1) / 2 + 0.1))
    probe = _boxes(fv, ft, fg, lambda n: n == "light_probe")
    check("the lamp-inside-a-solid gate fires",
          any(_overlaps(probe[0][1], sb) for _n, sb in fx))
    # And that a room MISSING a fitting is detected -- the failure mode that
    # would otherwise show up as a room that is merely dim.
    check("the missing-fitting gate fires",
          bool({n for n, *_ in LIGHTS["worship"]}
               - {n for n, _l, _h in build(
                   schema, profile, dr.by_key("fabrication"))[2]}))

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
    ap.add_argument("--footprint", action="store_true",
                    help="does every location's geometry span its footprint")
    ap.add_argument("--legacy", action="store_true",
                    help="--footprint's negative control: build one bay per "
                         "location, the way every session before 4k did")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.footprint:
        schema, profile = it.load()
        return 0 if spans_footprint(schema, profile, legacy=a.legacy,
                                    verbose=a.verbose) else 1
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
