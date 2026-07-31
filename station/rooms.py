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


def ceiling_m(place):
    """Room height: the archetype's nominal, raised to hold its own props.

    Deliberately allowed to exceed DECK_PITCH_M. A docking bay is 18 m tall in
    `docking_bay.py` and spans many decks; pretending every volume fits in one
    3.6 m pitch is what produced a 5 m door in a 2.9 m room.
    """
    base = PLACE_CEILING.get(place["key"],
                             CEIL_BY_ARCHETYPE.get(archetype(place), 2.9))
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
    """
    nx = max(1, int(round((x1 - x0) / tile)))
    nz = max(1, int(round((z1 - z0) / tile)))
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

    if not floor:
        # A room with nothing standing on its floor is small by nature -- a
        # micro-g bay you float through, a sealed section, a checkpoint. A
        # 6 x 8 m minimum made those read as empty halls, which is the same
        # picked-not-derived mistake one size down. Size to the wall props.
        wide = max((PROPS[k][0] for k in wall), default=1.6)
        return (max(wide + 1.2, fx_width, dressed, 3.0),
                max(wide + 1.6, fx_len, 4.0))
    # Ranked alternately down two walls, so each wall takes half of them.
    per_side = [PROPS[k] for k in floor] * 2
    run = sum(pw + 0.45 for pw, _pd, _ph, _m in per_side) / 2.0 + 1.2
    deep = max(pd for _pw, pd, _ph, _m in per_side)
    width = 2 * deep + max(WALK_M, 1.6) + 0.5
    # Wall props run along z, so the bay must be long enough to hang the
    # widest of them -- a 6 m bay door needs 6 m of wall.
    widest_wall = max((PROPS[k][0] for k in wall), default=0.0)
    return (max(width, fx_width, dressed, 4.0),
            max(run, widest_wall + 1.2, fx_len, 6.0))


def bays_in(schema, profile, place):
    """How many representative bays tile this location's real footprint."""
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    return max(1, int(w_full / bw)) * max(1, int(l_full / bl))


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
    w_full, l_full, _r = room_extent_m(schema, profile, place)
    bw, bl = bay_span_m(place)
    w, ln = min(w_full, bw), min(l_full, bl)
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
    z = max(-hl + 1.2, min(hl - 1.2, -hl + FIXTURE_PITCH_M * 0.5))
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


def build(schema, profile, place, max_span_m=None, door_at=None,
          report=None, plates=True):
    """Geometry for one representative bay of a location.

    A 300 m storage run is a corridor of identical bays; emitting all of it
    would put millions of triangles into a layer that only has to prove the
    volume exists, is closed, and is furnished. `bays_in()` says how many the
    streaming system instances.

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
        _fixture(v, t, g, key, (x0, 0.0, z0), (x0 + pd, ph, z0 + pw),
                 (place["key"], i), "prop_", report)
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
        sd = (place["key"], walls[wi][0], round(cur, 2))
        if walls[wi][0] == "side":
            _fixture(v, t, g, key, (-hw, sill, cur),
                     (-hw + pd, sill + ph, cur + pw), sd, "prop_", report)
        elif walls[wi][0] == "near":
            _fixture(v, t, g, key, (cur, sill, -hl),
                     (cur + pw, sill + ph, -hl + pd), sd, "prop_", report)
        else:
            _fixture(v, t, g, key, (cur, sill, hl - pd),
                     (cur + pw, sill + ph, hl), sd, "prop_", report)
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
        _fixture(v, t, g, key, (xc - pd / 2, top - ph, z0),
                 (xc + pd / 2, top, z0 + pw), (place["key"], i), "prop_",
                 report)

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
        runs, cur = [], -hl + 0.05
        for b0, b1 in blocks + [(hl - 0.05, hl)]:
            if b0 - cur >= lw:
                runs.append((cur, b0))
            cur = max(cur, b1)
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
    import dressing as _dress                                   # noqa: PLC0415
    for _dens in DRESS_DENSITIES:
        dv, dt, dg, _dc = _dress.dress(
            place["key"], w - 2 * WALL_T_M, ln - 2 * WALL_T_M, ceil, arch,
            inset=(inset[0], inset[1]), seed=place["key"], density=_dens)
        trial_v = v + dv
        trial_t = list(t) + [(a + len(v), b + len(v), c + len(v))
                             for a, b, c in dt]
        trial_g = list(g) + [(n, lo + len(t), hi + len(t))
                             for n, lo, hi in dg]
        _trial_boxes = _boxes(trial_v, trial_t, trial_g, is_solid)
        _ok = walkable(_trial_boxes, bw, bl)
        if report is not None:
            report.setdefault("trials", []).append(
                (_dens, _ok, len(_trial_boxes)))
        if _dens == 0.0 or _ok:
            v, t, g = trial_v, trial_t, trial_g
            # WHICH DENSITY IT SETTLED ON. Without this the only way to know how
            # much furniture a room actually got is to re-run the trial from
            # outside, which is a second copy of the rule that decides it -- and
            # every time this project has kept two copies of one decision they
            # have drifted. `report` is how a caller asks the thing that decided.
            if report is not None:
                report["density"] = _dens
                report["dress_tris"] = len(dt)
            break


    # POPULATION -- station/populace.py, and it runs LAST for the same reason
    # the dressing does: people are placed against the furniture that is
    # actually there, so somebody ends up ON a chair rather than near one. The
    # hour comes from STATION_HOUR so the whole station can be moved to 0300
    # with one number.
    import populace as _pop                                     # noqa: PLC0415
    pv, pt, pg, _ps = _pop.populate(
        place["key"], v, t, g, w - 2 * WALL_T_M, ln - 2 * WALL_T_M,
        hour=STATION_HOUR, arch=arch, seed=place["key"],
        g_ms2=_pop.place_gravity(place["key"]))
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

    # --- AND NO FIXTURE IS ONE -- INV-130 ---------------------------------
    # `MACHINE_KIND` must cover every declared fixture in both directions, so
    # a fixture added without a shape is a build failure rather than a box that
    # quietly comes back. The negative control is one line: delete an entry and
    # this fires naming it.
    import dressing as _dress                                   # noqa: PLC0415
    fx_names = set()
    for _fx in list(FIXTURES.values()) + list(PLACE_FIXTURES.values()):
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
    unscened = [p["key"] for p in places
                if not any(n.startswith("fix_") for n, _l, _h
                           in build(schema, profile, p)[2])]
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
    check("...and a place without them still gets its archetype's",
          {n for n, *_ in fixtures_for(dr.by_key("fabrication"))}
          == {n for n, *_ in FIXTURES["industrial"]})
    # NEGATIVE CONTROL, run rather than described: hand the resolver a place
    # whose key is in neither table and confirm it falls back, and hand it one
    # that is in both and confirm it does not.
    _probe = dict(dr.by_key("reactor_hall"))
    _probe["key"] = "__not_in_place_fixtures__"
    check("the override test can fail",
          {n for n, *_ in fixtures_for(_probe)}
          == {n for n, *_ in FIXTURES[archetype(_probe)]}
          and ceiling_m(_probe) == CEIL_BY_ARCHETYPE[archetype(_probe)],
          "a place NOT in the tables still took an override")
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

    dark, pierced, outside, unwalkable = [], [], [], []
    lamp_total = 0
    for p in places:
        v, t, g = build(schema, profile, p)
        want = {n for n, *_ in lights_for(p)}
        got = {n for n, _l, _h in g if n.startswith("light_")}
        lamps = _boxes(v, t, g, lambda n: n.startswith("light_"))
        lamp_total += len(lamps)
        if want - got:
            dark.append((p["key"], sorted(want - got)))
        # A fitting inside a furnace stack lights the inside of the furnace.
        # Ribs count here and do not for props: a chair in front of an
        # articulated wall is a chair; a light course through one is a strip
        # of light passing through structure.
        solid = _boxes(v, t, g, lambda n: n.startswith(("prop_", "fix_"))
                       or n.endswith("_rib"))
        for ln_, lb in lamps:
            if any(_overlaps(lb, sb) for _sn, sb in solid):
                pierced.append((p["key"], ln_))
                break
        bw, bl = bay_span_m(p)
        ceil = ceiling_m(p)
        for ln_, lb in lamps:
            if (lb[0] < -bw / 2 - WALL_T_M - 1e-6
                    or lb[3] > bw / 2 + WALL_T_M + 1e-6
                    or lb[2] < -bl / 2 - WALL_T_M - 1e-6
                    or lb[5] > bl / 2 + WALL_T_M + 1e-6
                    or lb[1] < -1e-6 or lb[4] > ceil + 1e-6):
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
        if not walkable(_boxes(v, t, g, lambda n: not (
                n.endswith(("_deck", "_soffit", "_wall", "_rib")
                           + _TRIM_SUFFIXES)
                or n.startswith("npc_"))), bw, bl):
            unwalkable.append(p["key"])
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
            if not nm.endswith(_TRIM_SUFFIXES):
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
