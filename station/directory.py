"""The station directory: where every location actually IS, relative to every other.

WHY THIS EXISTS
---------------
Fifteen modules build geometry. **Three of them knew where they were.** The
Zocalo, the Council Chamber, C&C, the bar, quarters, the Alien Sector and the
plant zone were all authored in their own local frames -- rooms floating in
nowhere. There was no collision check, no adjacency, and no way to say whether
you could walk from one to another, because nothing had a station address.

That is the difference between a prop warehouse and a station, and this module
is the fix. Every location gets a real address:

    (sector, ring_index, deck_index, angle_deg, z_m)

and the addresses are checked **against each other** -- footprints must not
overlap, adjacencies the sources require must hold, and a room's gravity must
suit what happens in it.

IT IS DRIVEN FROM THE GAZETTEER, NOT FROM MEMORY
------------------------------------------------
`docs/gazetteer/LOCATIONS.md` holds **126 location rows**. This module parses
that file at test time and asserts that **every row is either addressed here or
explicitly deferred with a reason**. There is no third state. That is what makes
the remaining work countable instead of a feeling, and it is what stops the
build order looking arbitrary: what is left is a list, not a mood.

FUNCTION AND INTERACTION ARE PART OF THE ADDRESS
-------------------------------------------------
The brief asks for locations that *do* something. A room with no function is
set dressing, so every entry carries:

  * `functions`  -- what the place is FOR, in the simulation's terms
  * `interacts`  -- the props and fittings a player can actually use there

These are declarations, not implementations -- the interaction layer does not
exist yet -- but declaring them here means the layer has a specification to be
built against rather than being invented per room later, and it means a room
that cannot be used is visible as an empty `interacts` tuple rather than as a
silence.

COORDINATES
-----------
`angle_deg` is measured about the station's spin axis, `z_m` along it from the
aft terminus, both matching `interior.py`. `footprint` is (angular extent in
degrees, longitudinal extent in metres) -- the two axes a ring deck actually
has. Radial extent is the deck, which the address already names.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "docs", "gazetteer", "LOCATIONS.md")


def _P(key, name, sector, ring, deck, angle, z, foot, module=None,
       functions=(), interacts=(), adjacent=(), within=None, auth=4, note=""):
    # A bare string here is the classic missing-comma bug: `("x")` is "x", not
    # ("x",), and `tuple("x")` then yields ('x',) for one-character names --
    # ("ambassadorial_suites") produced twenty single-letter adjacencies and
    # twelve failing assertions. Reject strings outright rather than coercing
    # them, so the error surfaces where it is written.
    for field, val in (("functions", functions), ("interacts", interacts),
                       ("adjacent", adjacent)):
        if isinstance(val, str):
            raise TypeError(
                f"{key}: {field} is a string {val!r} -- a missing trailing "
                f"comma. Write ({val!r},)")
    return dict(key=key, name=name, sector=sector, ring=ring, deck=deck,
                angle_deg=angle, z_m=z, footprint=foot, module=module,
                functions=tuple(functions), interacts=tuple(interacts),
                adjacent=tuple(adjacent), within=within, auth=auth, note=note)


# ---------------------------------------------------------------------------
# The addressed places
# ---------------------------------------------------------------------------
# Sector z-extents, for reference while reading the table:
#   yellow    0-3397   grey 3397-3839   green 3839-6425
#   red    6425-6794   blue 6794-8047
#
# Everything with geometry today is here, plus the major named locations whose
# sector the gazetteer states. Angles are spread deliberately: two things on the
# same deck at the same angle is the collision the assertions exist to catch.
PLACES = (
    # --- Blue: the arrival half -------------------------------------------
    _P("cnc", "Command & Control", "blue", 0, 0, 0.0, 7960.0, (24.0, 40.0),
       module="command_control", auth=3,
       functions=("station_ops", "traffic_control", "defence_command"),
       interacts=("console", "comms_channel", "tactical_display", "blast_door"),
       adjacent=("obs_dome_1",), within="obs_dome_1",
       note="Observation Dome 1. The most-seen room on the show."),
    _P("obs_dome_1", "Observation Dome 1", "blue", 0, 0, 0.0, 7960.0,
       (26.0, 44.0), module="components", auth=3,
       functions=("structure", "viewport"), interacts=("viewport",),
       note="The dome C&C sits inside; exterior geometry is still a box."),
    _P("customs_north", "Customs hall, north", "blue", 0, 0, 40.0, 7460.0,
       (10.0, 34.0), module="customs", auth=1,
       functions=("immigration", "identicard_check", "contraband_search",
                  "atmosphere_assignment"),
       interacts=("identicard_reader", "customs_desk", "info_board",
                  "babcom_terminal", "baggage_scanner"),
       adjacent=("arrival_concourse", "docking_bays"),
       note="Two halls, north and south -- Security Manual, authority 3."),
    _P("customs_south", "Customs hall, south", "blue", 0, 0, 220.0, 7460.0,
       (10.0, 34.0), module="customs", auth=3,
       functions=("immigration", "identicard_check"),
       interacts=("identicard_reader", "customs_desk", "info_board"),
       adjacent=("docking_bays",)),
    _P("arrival_concourse", "Arrival concourse", "blue", 0, 0, 52.0, 7460.0,
       (12.0, 34.0), module="customs", auth=1,
       functions=("arrival", "wayfinding", "public_information"),
       interacts=("babcom_terminal", "station_schematic_screen",
                  "welcome_board", "bollard"),
       adjacent=("customs_north",)),
    _P("docking_bays", "Docking bays (24)", "blue", 0, 0, 0.0, 7115.0,
       (360.0, 140.0), module="docking_bay", auth=3,
       functions=("ship_arrival", "ship_departure", "cargo_handling",
                  "starfury_launch"),
       interacts=("bay_door", "docking_clamp", "deck_marking", "cargo_crane",
                  "bay_control_booth"),
       adjacent=("customs_north", "customs_south"),
       note="24 bays tiling the circle; the launch-and-dock hinge."),
    _P("qtr_command", "Command staff quarters", "blue", 0, 2, 150.0, 7600.0,
       (30.0, 60.0), module="quarters", auth=4,
       functions=("residence",),
       interacts=("door", "babcom_terminal", "locker", "shower", "bunk"),
       note="0.760 g. Showers here and the suites only -- water is rationed."),
    _P("qtr_personnel", "Station personnel quarters", "blue", 0, 4, 190.0,
       7600.0, (44.0, 90.0), module="quarters", auth=3,
       functions=("residence",),
       interacts=("door", "babcom_terminal", "locker", "bunk"),
       note="Includes the Blue rosette's Dock Workers' Quarters."),
    _P("medlab_one", "Medlab One", "blue", 0, 1, 100.0, 7300.0, (14.0, 30.0),
       auth=3, functions=("medical", "triage", "surgery", "quarantine"),
       interacts=("diagnostic_bed", "medcabinet", "isolation_door",
                  "babcom_terminal"),
       note="The primary Medlab. Blue rosette; X-6 is a rare auth-3/4 hold."),
    _P("mess_hall", "Mess hall", "blue", 0, 3, 260.0, 7700.0, (16.0, 34.0),
       auth=3, functions=("catering", "crew_social"),
       interacts=("serving_counter", "table", "tray_dispenser"),
       note="Named in the Blue rosette."),

    # --- Red: the commercial half ------------------------------------------
    _P("zocalo", "The Zocalo", "red", 0, 0, 0.0, 6600.0, (70.0, 120.0),
       module="zocalo", auth=3,
       functions=("commerce", "public_social", "crowd_hub"),
       interacts=("market_stall", "shopfront", "cafe_table", "planter",
                  "neon_sign", "babcom_terminal", "gallery_rail"),
       adjacent=("business_center", "bar_unnamed"),
       note="Outermost ring of Red. The station's main social space."),
    _P("business_center", "Business District / Business Center", "red", 1, 0,
       80.0, 6600.0, (24.0, 60.0), auth=3,
       functions=("currency_exchange", "commerce", "offices"),
       interacts=("exchange_terminal", "office_door", "babcom_terminal"),
       adjacent=("zocalo",),
       note="The customs board directs arrivals here for exchange rates -- "
            "an authority-1 sign pointing at an authority-3 rosette label."),
    _P("bar_unnamed", "An unnamed bar / diner", "red", 0, 0, 96.0, 6620.0,
       (4.0, 12.0), module="hospitality", auth=1,
       functions=("hospitality", "food_service", "recreation", "rumour"),
       interacts=("bar_counter", "table", "stool", "dartboard",
                  "pendant_lamp", "menu_display"),
       adjacent=("zocalo",),
       note="Do NOT use the uploader's caption as a name -- §218."),
    _P("dark_star", "Dark Star", "red", 1, 2, 140.0, 6600.0, (5.0, 14.0),
       auth=3, functions=("hospitality", "recreation", "nightlife"),
       interacts=("bar_counter", "table", "neon_sign", "door"),
       note="Named in an inner ring of the Red rosette; planted entrance."),
    _P("casino", "The Casino", "red", 1, 1, 160.0, 6600.0, (8.0, 22.0),
       auth=4, functions=("gambling", "recreation", "black_market_fringe"),
       interacts=("gaming_table", "credit_terminal", "bar_counter", "door")),
    _P("security_central", "Security Central", "red", 2, 0, 200.0, 6600.0,
       (10.0, 26.0), auth=3,
       functions=("law_enforcement", "dispatch", "surveillance", "detention"),
       interacts=("duty_desk", "monitor_wall", "weapons_locker",
                  "cell_door", "babcom_terminal"),
       adjacent=("brig", "law_courts"),
       note="Red inner ring. Runs 24 h across three watches."),
    _P("brig", "The brig / holding cells", "red", 2, 1, 206.0, 6600.0,
       (6.0, 18.0), auth=5,
       functions=("detention",), interacts=("cell_door", "bunk", "intercom"),
       adjacent=("security_central", "law_courts"),
       note="PROPOSED, P-04. No source places it; it must be walkable from "
            "Security Central and from the courtroom, and it is where a "
            "customs refusal ends."),
    _P("law_courts", "Law Courts / the Judiciary", "red", 2, 0, 216.0, 6600.0,
       (8.0, 22.0), auth=3,
       functions=("adjudication", "ombudsman_hearings"),
       interacts=("bench", "public_gallery", "door"),
       adjacent=("security_central", "brig")),
    _P("qtr_civilian", "Civilian residential", "red", 1, 6, 280.0, 6650.0,
       (50.0, 120.0), module="quarters", auth=4,
       functions=("residence",),
       interacts=("door", "babcom_terminal", "locker", "bunk")),
    _P("qtr_transient", "Transient habitation", "red", 1, 9, 330.0, 6650.0,
       (26.0, 80.0), module="quarters", auth=4,
       functions=("residence", "short_stay"),
       interacts=("door", "locker", "bunk")),

    # --- Green: the diplomatic half and the drum --------------------------
    _P("council_chamber", "Babylon 5 Advisory Council chamber", "green", 0, 0,
       0.0, 4100.0, (12.0, 30.0), module="council_chamber", auth=3,
       functions=("diplomacy", "council_session", "ceremony"),
       interacts=("delegate_bench", "speaking_position", "gallery_door"),
       adjacent=("ambassadorial_suites",)),
    _P("ambassadorial_suites", "Ambassadorial suites", "green", 0, 1, 24.0,
       4100.0, (40.0, 90.0), module="quarters", auth=3,
       functions=("residence", "diplomatic_mission"),
       interacts=("door", "babcom_terminal", "shower", "bunk", "reception"),
       adjacent=("council_chamber",),
       note="Wrapped around the Garden per authority 4."),
    _P("alien_sector", "The Alien Sector", "green", 0, 3, 300.0, 4400.0,
       (36.0, 120.0), module="alien_sector", auth=3,
       functions=("residence", "multi_environ", "atmosphere_containment"),
       interacts=("airlock_door", "breather_dispenser", "barred_screen",
                  "atmosphere_status_lamp"),
       adjacent=("kosh_quarters", "markab_quarter"),
       note="Where the six-atmosphere board becomes a traversal mechanic."),
    # THE ONLY MONUMENT ON THE STATION TO AN ENTIRE SPECIES, and until now it
    # was a room the simulation modelled and a player could not walk to.
    # `npc/schedule.py` has carried it as a `PlaceCrowd` since it was written
    # -- sealed, density 0.0, the ONE place `npc/crowd.py` asserts is empty at
    # every hour of the day -- `npc/crowd.py::EXTENTS` gives it a real floor,
    # and `npc/navigation.py::EXPECTED_ISLANDS` names it as a deliberate island
    # in the walk graph. Three modules knew about it and the register did not,
    # so there was nothing to stand in front of.
    #
    # THE FOOTPRINT IS NOT MINE: `crowd.EXTENTS` gives 12.0 x 58.32 m
    # (699.84 m2), so the register and the crowd model agree by construction
    # rather than by discipline -- hard rule 4 applied to a fourth pair of
    # descriptions.
    #
    # BUT `footprint[0]` IS DEGREES OF ARC, NOT METRES, and writing 12.0 here
    # would have been a unit error that no assertion in this file could catch:
    # `rooms.py` reads it as `arc = 2*pi*r * (footprint[0]/360)`, so a 12.0
    # would have built a 61 m frontage at this deck's 292.700 m radius -- five
    # times the room the crowd model prices, and still "agreeing" on paper.
    # 12.0 m of arc at r=292.700 is 2.3490 deg, and that is what is written.
    #
    # THE ANGLE MOVED FOR THE SAME REASON. 284.0 deg was the first choice and it
    # sits INSIDE `alien_sector`, which spans 36 deg about 300.0, i.e. 282..318
    # -- `overlaps()` would have caught it, but only after a 15-minute gate.
    # 279.0 clears 282.0 with the room's own 2.349 deg to spare, and it is
    # still the next door along.
    #
    # `sealed_volume` is the existing function for exactly this and is borrowed
    # from `welded_shut` in Grey; `welded_door` is an existing BUILT prop
    # (rooms.py: 1.90 x 0.22 x 2.35 m, wall-mounted), so declaring it does not
    # ask `interact.py --audit` for something nobody made.
    _P("markab_quarter", "The sealed Markab quarter", "green", 0, 3, 279.0,
       4400.0, (2.349, 58.32), auth=5,
       functions=("residence", "sealed_volume"),
       interacts=("welded_door", "atmosphere_status_lamp", "level_plaque"),
       adjacent=("alien_sector",),
       note="Sealed, powered, unlit, still furnished. Nobody at any hour. "
            "AUTHORITY SPLITS: the extinction is authority 1 (S2E18, "
            "Confessions and Lamentations); the room's PLACEMENT is 5 -- no "
            "source places it, and it sits beside the Alien Sector because "
            "that is where a non-human community's quarter is. Its emptiness "
            "is a measured zero over a real floor rather than a missing "
            "entry, which is the whole point of building it."),
    _P("kosh_quarters", "Kosh's quarters", "green", 0, 3, 316.0, 4400.0,
       (4.0, 12.0), module="alien_sector", auth=1,
       functions=("residence", "sealed_environment"),
       interacts=("airlock_door", "atmosphere_status_lamp"),
       adjacent=("alien_sector",), within="alien_sector",
       note="A player cannot enter without a suit -- a hard interaction rule "
            "falling out of the atmosphere system, not out of scripting."),
    _P("garden_town", "The Garden's townscape", "green", 1, 0, 112.0, 4900.0,
       (50.0, 300.0), module="garden", auth=1,
       functions=("agriculture", "recreation", "civic", "atmosphere_plant"),
       interacts=("building_door", "bench", "pool_edge", "path"),
       within="the_garden",
       note="Settlement band. The drum's open volume, not a deck."),
    _P("hydroponics", "Hydroponics", "green", 0, 5, 200.0, 4600.0,
       (30.0, 120.0), auth=3,
       functions=("agriculture", "oxygen_production", "food_production"),
       interacts=("grow_rack", "irrigation_control", "door"),
       note="P-07: racked and enclosed, in the sub-floor stack -- the drum "
            "floor is open fields."),

    # --- Grey: the plant, and the people with no billet --------------------
    _P("plant_zone", "The plant zone", "grey", 0, 0, 0.0, 3618.0,
       (360.0, 442.0), module="plant", auth=5,
       functions=("water_storage", "waste_processing", "air_handling",
                  "power_distribution", "fabrication"),
       interacts=("catwalk", "valve", "tank_gauge", "service_ladder"),
       adjacent=("downbelow",),
       note="34 decks at 1.26-1.69 g. INV-027/INV-028."),
    _P("downbelow", "Downbelow", "grey", 0, 0, 180.0, 3618.0, (180.0, 442.0),
       module="plant", auth=3,
       functions=("informal_residence", "black_market", "crime"),
       interacts=("catwalk", "standpipe", "makeshift_door", "brazier"),
       adjacent=("plant_zone",), within="plant_zone",
       note="Not rooms. The people with no billet live in the stack nobody "
            "can be billeted on."),

    # --- Yellow: engineering ------------------------------------------------
    _P("fusion_core", "Primary fusion core", "yellow", 0, 0, 0.0, 400.0,
       (360.0, 800.0), auth=3,
       functions=("power_generation",),
       interacts=("reactor_console", "blast_door"),
       note="Non-rotating aft assembly; everything aft of z=2680 jettisons."),

    # ======================================================================
    # M1 BATCH — the remaining gazetteer rows, session 3k
    # ----------------------------------------------------------------------
    # Angles are allocated per (sector, ring, deck) so nothing collides; the
    # assertions check that rather than trusting this comment. Where the
    # gazetteer says "unplaced", the entry is a PROPOSED placement at auth 5
    # with its constraint in the note -- CLAUDE.md rule 1: extrapolate and mark
    # it, never leave a hole.
    # ======================================================================

    # --- Blue: command, docking, medical, admin ---------------------------
    _P("obs_dome_2", "Observation Dome 2", "blue", 0, 0, 90.0, 7960.0,
       (20.0, 36.0), module="components", auth=3,
       functions=("observation", "structure"), interacts=("viewport",)),
    _P("war_room", "The War Room", "blue", 1, 0, 300.0, 7900.0, (10.0, 24.0),
       auth=5, functions=("defence_command", "briefing"),
       interacts=("tactical_display", "console", "blast_door"),
       adjacent=("cnc",),
       note="PROPOSED. No source assigns it; constraint is that it must be "
            "secure and reachable from C&C without crossing public space."),
    _P("admin_complex", "Station commander's administration complex", "blue",
       1, 1, 314.0, 7900.0, (12.0, 28.0), auth=5,
       functions=("administration", "command"),
       interacts=("desk", "babcom_terminal", "door"),
       adjacent=("cnc",),
       note="PROPOSED. Contested between Blue on screen and Green in print."),
    _P("bay_elevators", "Bay elevators (2)", "blue", 0, 0, 300.0, 7115.0,
       (8.0, 24.0), auth=3, functions=("transit", "cargo_handling"),
       interacts=("lift_call", "lift_door"), adjacent=("docking_bays",),
       within="docking_bays"),
    _P("lowg_bays", "Low-g / zero-g docking bays", "blue", 0, 0, 130.0, 7115.0,
       (16.0, 60.0), auth=3, functions=("ship_arrival", "microgravity_handling"),
       interacts=("bay_door", "docking_clamp", "handhold"),
       within="docking_bays"),
    _P("cobra_bays", "Cobra bays (28)", "blue", 0, 0, 0.0, 6900.0,
       (360.0, 120.0), module="components", auth=3,
       functions=("starfury_launch", "fighter_maintenance"),
       interacts=("launch_tube", "clamp"),
       note="Exterior launch tubes; C-002 on 24 vs 28."),
    _P("cargo_bays", "Cargo bays (42)", "blue", 1, 3, 60.0, 7000.0,
       (60.0, 200.0), auth=3, functions=("cargo_handling", "storage"),
       interacts=("cargo_crane", "container", "manifest_terminal")),
    _P("quartermaster", "Quartermaster's Office", "blue", 1, 2, 20.0, 7250.0,
       (6.0, 16.0), auth=3, functions=("logistics", "issue_stores"),
       interacts=("issue_counter", "manifest_terminal", "locker")),
    _P("post_office", "Post Office", "blue", 1, 2, 34.0, 7250.0, (6.0, 16.0),
       auth=3, functions=("mail", "commerce"),
       interacts=("counter", "parcel_locker", "babcom_terminal")),
    _P("fuel_stores", "Fuel stores", "blue", 0, 8, 240.0, 7000.0,
       (30.0, 90.0), auth=3, functions=("fuel_storage", "hazardous_storage"),
       interacts=("valve", "tank_gauge", "blast_door")),
    _P("mooring_clamps", "Hard docking mooring clamps", "blue", 0, 0, 180.0,
       7115.0, (14.0, 50.0), module="components", auth=3,
       functions=("ship_mooring",), interacts=("docking_clamp",),
       within="docking_bays"),
    _P("plantroom_bay", "A docking bay dressed as a plant room", "blue", 0, 0,
       260.0, 7115.0, (10.0, 40.0), auth=1,
       functions=("plant", "cargo_handling"),
       interacts=("valve", "catwalk", "bay_door"),
       within="docking_bays"),
    _P("proximity_arrays", "Space traffic proximity arrays (4)", "blue", 0, 0,
       200.0, 7900.0, (30.0, 60.0), module="components", auth=3,
       functions=("traffic_control", "sensors"), interacts=()),
    _P("nav_beacon", "Primary navigation beacon", "blue", 0, 0, 340.0, 8000.0,
       (10.0, 24.0), module="components", auth=3,
       functions=("navigation",), interacts=()),
    _P("vorlon_berth", "The Vorlon transport berth", "blue", 0, 0, 320.0,
       7115.0, (10.0, 40.0), auth=4,
       functions=("ship_arrival", "diplomatic_privilege"),
       interacts=("bay_door", "docking_clamp"), within="docking_bays",
       note="Kept clear for the Vorlon transport; a privilege made physical."),
    _P("infirmary", "The infirmary", "blue", 0, 1, 116.0, 7300.0, (8.0, 20.0),
       auth=4, functions=("medical", "triage"),
       interacts=("diagnostic_bed", "medcabinet"), adjacent=("medlab_one",)),
    _P("isolab", "Isolab", "blue", 0, 1, 128.0, 7300.0, (6.0, 16.0), auth=4,
       functions=("medical", "quarantine", "research"),
       interacts=("isolation_door", "diagnostic_bed", "medcabinet"),
       adjacent=("medlab_one",)),
    _P("morgue", "Morgue / mortuary", "blue", 0, 6, 140.0, 7300.0,
       (8.0, 20.0), auth=5, functions=("medical", "mortuary"),
       interacts=("cold_drawer", "door"),
       note="PROPOSED. Unplaced by every source; sited with medical and at "
            "low traffic."),
    _P("cryo_storage", "Cryo storage", "blue", 0, 7, 152.0, 7300.0,
       (8.0, 20.0), auth=5, functions=("medical", "storage"),
       interacts=("cryo_pod", "console"),
       note="PROPOSED. Unplaced; sited with the morgue."),
    _P("sanctuary_blue", "The Sanctuary", "blue", 1, 5, 76.0, 7500.0,
       (10.0, 24.0), auth=3, functions=("worship", "quiet"),
       interacts=("pew", "door")),
    _P("comms_grid", "Deep space communications grids (2)", "blue", 0, 0,
       160.0, 7900.0, (40.0, 120.0), module="components", auth=3,
       functions=("communications",), interacts=()),

    # --- Red: commerce, law, media ----------------------------------------
    _P("eclipse_cafe", "Eclipse Cafe", "red", 0, 0, 110.0, 6620.0,
       (4.0, 12.0), module="hospitality", auth=4,
       functions=("hospitality", "food_service"),
       interacts=("bar_counter", "table", "stool"), adjacent=("zocalo",)),
    _P("shops_kiosks", "Shops, kiosks and cart vendors", "red", 0, 0, 24.0,
       6600.0, (40.0, 100.0), module="zocalo", auth=4,
       functions=("commerce", "retail"),
       interacts=("market_stall", "shopfront", "credit_terminal"),
       adjacent=("zocalo",), within="zocalo"),
    _P("ceremonial_rooms", "Rooms for ceremonial and festive hire", "red",
       1, 3, 100.0, 6600.0, (10.0, 26.0), auth=4,
       functions=("ceremony", "hire"), interacts=("door", "table")),
    _P("water_storage", "Water storage", "red", 3, 0, 20.0, 6600.0,
       (40.0, 120.0), auth=3, functions=("water_storage",),
       interacts=("tank_gauge", "valve", "catwalk"),
       note="Named in an INNER ring of the Red rosette."),
    _P("waste_red", "Waste management systems, Red", "red", 3, 4, 90.0, 6600.0,
       (30.0, 100.0), auth=3, functions=("waste_processing",),
       interacts=("valve", "catwalk", "tank_gauge")),
    _P("central_corridor", "The Central Corridor", "red", 0, 0, 300.0, 6600.0,
       (40.0, 120.0), module="interior_kit", auth=3,
       functions=("transit", "public_social"),
       interacts=("babcom_terminal", "gallery_rail", "door"),
       note="Two-level public concourse; exposed hull ribs. Outermost ring."),
    _P("medlab_red", "Medlab, Red", "red", 1, 4, 240.0, 6600.0, (10.0, 24.0),
       auth=4, functions=("medical", "triage"),
       interacts=("diagnostic_bed", "medcabinet")),
    _P("outdoor_rec", "Outdoor recreation -- lake pool, ball diamond", "red",
       1, 5, 60.0, 6650.0, (30.0, 90.0), auth=3,
       functions=("recreation", "sport"),
       interacts=("pool_edge", "bench", "path")),

    # --- Green: diplomacy, the drum, worship -------------------------------
    _P("conference_5", "Conference / lounge with the \"5\" floor roundel",
       "green", 0, 0, 40.0, 4100.0, (8.0, 20.0), auth=4,
       functions=("diplomacy", "meeting"),
       interacts=("table", "seat", "door")),
    _P("conference_rooms", "Conference rooms (general)", "green", 0, 0, 56.0,
       4100.0, (12.0, 28.0), auth=3, functions=("meeting",),
       interacts=("table", "seat", "babcom_terminal", "door")),
    _P("earthforce_office", "Earthforce Office", "green", 0, 2, 70.0, 4100.0,
       (8.0, 20.0), auth=3, functions=("administration", "military_liaison"),
       interacts=("desk", "babcom_terminal", "door")),
    _P("league_delegations", "League of Non-Aligned Worlds delegations",
       "green", 0, 1, 200.0, 4100.0, (16.0, 40.0), module="quarters", auth=3,
       functions=("diplomatic_mission", "residence"),
       interacts=("door", "babcom_terminal", "reception"),
       adjacent=("council_chamber",)),
    _P("domed_rotunda", "The domed rotunda", "green", 0, 0, 84.0, 4200.0,
       (10.0, 26.0), auth=4, functions=("observation", "public_social"),
       interacts=("viewport", "bench")),
    _P("obs_rotundas", "Observation rotundas (4)", "green", 0, 0, 96.0, 4200.0,
       (12.0, 30.0), module="components", auth=3,
       functions=("observation",), interacts=("viewport", "bench")),
    _P("drum_office", "A drum-facing office with a multi-pane window", "green",
       0, 2, 128.0, 4900.0, (6.0, 16.0), auth=1,
       functions=("offices",), interacts=("desk", "viewport", "babcom_terminal"),
       note="Talia Winters' office; the clearest view of the drum interior."),
    _P("telepath_office", "The resident commercial telepath's office", "green",
       0, 2, 140.0, 4900.0, (6.0, 16.0), auth=5,
       functions=("offices", "psi_corps"),
       interacts=("desk", "babcom_terminal"),
       note="PROPOSED. Unplaced; sited with the drum-facing offices."),
    _P("zen_garden", "The Zen Garden", "green", 1, 0, 150.0, 5000.0,
       (20.0, 80.0), module="garden", auth=3,
       functions=("recreation", "contemplation"),
       interacts=("path", "bench")),
    _P("garden_terrace", "A landscaped garden terrace", "green", 1, 0, 130.0,
       4900.0, (14.0, 60.0), module="garden", auth=1,
       functions=("recreation",), interacts=("path", "bench", "pool_edge"),
       within="garden_town"),
    _P("water_rec", "Water recreation facilities", "green", 1, 0, 175.0,
       5100.0, (16.0, 70.0), module="garden", auth=3,
       functions=("recreation", "sport"), interacts=("pool_edge", "bench")),
    _P("drum_endcaps", "The drum end caps", "green", 1, 0, 340.0, 4000.0,
       (18.0, 100.0), module="interior", auth=1,
       functions=("structure", "transit"), interacts=("service_ladder",)),
    _P("drum_spokes", "The three radial spokes", "green", 1, 0, 0.0, 5200.0,
       (12.0, 60.0), module="interior", auth=1,
       functions=("transit", "structure"),
       interacts=("lift_call", "lift_door")),
    _P("subfloor_stack", "The sub-floor deck stack under the Garden", "green",
       0, 7, 250.0, 5000.0, (60.0, 300.0), module="interior", auth=3,
       functions=("services", "informal_residence", "storage"),
       interacts=("catwalk", "door", "valve")),
    _P("ground_tram", "Ground-level tram", "green", 1, 0, 210.0, 5000.0,
       (20.0, 200.0), auth=5,
       functions=("transit",), interacts=("tram_door", "seat"),
       note="PROPOSED. A second transit system at ground level; the guideway "
            "tram flies overhead and cannot serve the fields."),
    _P("drum_tram", "The drum guideway tram", "green", 1, 0, 240.0, 5000.0,
       (24.0, 240.0), module="tram", auth=1,
       functions=("transit",), interacts=("tram_door", "seat", "handhold")),
    _P("alien_worship", "Alien worship spaces", "green", 0, 4, 330.0, 4400.0,
       (12.0, 30.0), auth=4, functions=("worship",),
       interacts=("door", "shrine"), adjacent=("alien_sector",)),
    _P("waste_green", "Waste management systems, Green", "green", 0, 8, 190.0,
       4600.0, (30.0, 120.0), auth=3, functions=("waste_processing",),
       interacts=("valve", "catwalk")),
    _P("medlab_green", "Medlab, Green", "green", 0, 2, 158.0, 4300.0,
       (8.0, 22.0), auth=4, functions=("medical", "triage"),
       interacts=("diagnostic_bed", "medcabinet")),
    _P("ngrath", "N'Grath's premises", "green", 0, 6, 344.0, 4400.0,
       (5.0, 14.0), auth=4, functions=("black_market", "crime"),
       interacts=("door", "credit_terminal"),
       note="Quarters in Green, operations in Brown."),

    # --- Grey: industry, research, power -----------------------------------
    _P("alpha_substation", "Alpha power substation", "grey", 0, 40, 20.0,
       3618.0, (20.0, 100.0), auth=3, functions=("power_distribution",),
       interacts=("reactor_console", "blast_door")),
    _P("primary_breaker", "Primary breaker", "grey", 0, 42, 40.0, 3618.0,
       (12.0, 60.0), auth=3, functions=("power_distribution",),
       interacts=("breaker_lever", "console")),
    _P("fabrication", "Fabrication furnaces", "grey", 0, 50, 70.0, 3618.0,
       (30.0, 200.0), auth=4, functions=("fabrication", "industry"),
       interacts=("furnace_control", "crane", "catwalk")),
    _P("maintenance", "Maintenance and repair facilities", "grey", 0, 55,
       110.0, 3618.0, (30.0, 200.0), auth=4,
       functions=("repair", "fabrication"),
       interacts=("workbench", "tool_rack", "crane")),
    _P("research_labs", "Commercial research laboratories", "grey", 0, 60,
       150.0, 3618.0, (24.0, 140.0), auth=4, functions=("research",),
       interacts=("lab_bench", "console", "door")),
    _P("gravity_torus", "Variable gravity research torus", "grey", 0, 65,
       220.0, 3618.0, (30.0, 160.0), auth=4,
       functions=("research", "variable_gravity"),
       interacts=("console", "door")),
    _P("zerog_maint", "Zero-G maintenance facility", "grey", 0, 70, 260.0,
       3618.0, (24.0, 140.0), auth=4, functions=("repair", "microgravity_handling"),
       interacts=("handhold", "tool_rack")),
    _P("atmos_monitor", "Atmosphere monitoring station", "grey", 0, 30, 300.0,
       3618.0, (12.0, 60.0), auth=3, functions=("air_handling", "monitoring"),
       interacts=("console", "tank_gauge")),
    _P("raw_material", "Raw material storage bays (5)", "grey", 0, 75, 330.0,
       3618.0, (24.0, 160.0), auth=3, functions=("storage",),
       interacts=("container", "crane")),
    _P("micro_g_bays", "Micro-gravity maintenance bays (2)", "grey", 0, 80,
       350.0, 3618.0, (10.0, 60.0), auth=3,
       functions=("repair", "microgravity_handling"), interacts=("handhold",)),
    _P("downbelow_arch", "Downbelow's architecture", "grey", 0, 20, 200.0,
       3618.0, (60.0, 300.0), module="plant", auth=1,
       functions=("informal_residence", "transit"),
       interacts=("catwalk", "makeshift_door", "brazier"),
       within="plant_zone",
       note="ERA CAVEAT: the only frame is S5 with the station derelict. The "
            "set architecture is in era; the debris and dead panels are not."),
    _P("black_market", "The Downbelow black market", "grey", 0, 22, 230.0,
       3618.0, (30.0, 150.0), auth=4,
       functions=("black_market", "commerce", "crime"),
       interacts=("stall", "credit_terminal"), within="plant_zone"),
    _P("thieves_guild", "Thieves Guild presence", "grey", 0, 24, 250.0, 3618.0,
       (20.0, 100.0), auth=4, functions=("crime", "organised_crime"),
       interacts=("makeshift_door",), within="plant_zone"),
    _P("welded_shut", "Sections welded shut", "grey", 0, 26, 270.0, 3618.0,
       (24.0, 120.0), auth=4, functions=("sealed_volume",),
       interacts=("welded_door",),
       note="Unfinished or abandoned volume. Sealed doors with a reason."),
    _P("water_reclamation", "Water reclamation", "grey", 0, 5, 150.0, 3618.0,
       (40.0, 200.0), module="plant", auth=3,
       functions=("water_reclamation",),
       interacts=("valve", "tank_gauge", "catwalk"), within="plant_zone"),
    _P("waste_control", "Waste Management Control", "grey", 0, 8, 190.0,
       3618.0, (14.0, 70.0), auth=3, functions=("waste_processing", "control"),
       interacts=("console", "valve"), within="plant_zone"),
    _P("air_compressors", "Air compressors", "grey", 0, 10, 215.0, 3618.0,
       (24.0, 120.0), module="plant", auth=4, functions=("air_handling",),
       interacts=("valve", "tank_gauge"), within="plant_zone"),

    # --- Yellow: engineering ----------------------------------------------
    _P("disconnect_point", "Explosive disconnect point", "yellow", 0, 0, 40.0,
       2680.0, (30.0, 60.0), auth=3, functions=("structure", "emergency"),
       interacts=("blast_door",)),
    # z 925 +/- 125, i.e. 800-1050, NOT 900 +/- 150 = 750-1050. The reactor
    # (`fusion_core`) runs 0-800 and this ran 750-1050, so the two
    # interpenetrated by 50 m -- and `collisions()` could not see it, because
    # a 360-degree footprint collapsed to a point in `_arc_overlap`. Both were
    # invisible together for as long as both existed.
    #
    # The fore end is unchanged; only the aft end moves, to where the reactor
    # actually ends. `canon/00-MASTER.md` Sec.2 orders these aft to fore --
    # reactor housing, then purge vents, fuel delivery, cooling fins -- so the
    # transfer core beginning where the reactor stops is the arrangement the
    # source describes. Nothing in the register or the reference fixes either
    # boundary to the metre, so this is the smaller of the two possible edits
    # and it is declared rather than silent.
    _P("power_transfer", "Power transfer core + 12 cooling fins", "yellow", 0,
       0, 90.0, 925.0, (60.0, 250.0), module="components", auth=3,
       functions=("power_distribution", "cooling"), interacts=("console",)),
    # MOVED z 3000 -> 3250 IN 4r. It was the only place on the station with no
    # home at its own z, and `interior.hull_fit()`'s `homeless` category exists
    # because of it: at z 3000 Yellow waists to a core hull of 18.3 m -- 12.3 m
    # inside the skin, narrower than a corridor -- and carries ZERO deck stacks.
    # The old row named ring 0 deck 2, which at Yellow's widest cylinder is a
    # 148.2 m floor, so the node was assembled 135.9 m outside the ship: the
    # largest single miss in the register. Threading z through the builders
    # cannot fix it, because there is nothing at that z to move it to.
    #
    # z 3250 is chosen and not guessed. The gazetteer's own constraint is the
    # loose one -- "Yellow/Grey ... on the schematic between the reactor and
    # the carousel" (LOCATIONS.md:302, Security Manual callout, authority 3) --
    # and it gives a band, not a number. Inside that band z 3200-3300 is the
    # only stretch that satisfies all four: forward of the explosive
    # disconnect at z 2,680 so it is not on the jettisoned assembly; inside
    # Yellow (0-3397) and near the Grey boundary, which matches "Yellow/Grey"
    # better than z 3000 did; a full 7-deck stack present across the WHOLE
    # 100 m footprint rather than at its centre only; and a deck-2 floor that
    # is a constant 148.2 m over the entire span.
    #
    # That last number is why this move is nearly free: 148.2 m is EXACTLY the
    # radius the node is built at today. The room does not change shape, gain
    # or lose a metre of arc, or change gravity. Only where along the axis it
    # sits changes -- and the z-aware answer now equals the z-blind one, so the
    # pending builder flip costs this place nothing.
    #
    # Nearest neighbour is `rotation_drivers` at angle 320 deg, z 3240-3360;
    # this sits at 140 deg, 180 deg away. No arc overlap.
    _P("mainstage_node", "Mainstage power distribution node", "yellow", 0, 2,
       140.0, 3250.0, (20.0, 100.0), auth=3, functions=("power_distribution",),
       interacts=("console", "breaker_lever")),
    _P("spinal_cargo", "Spinal cargo facility", "yellow", 0, 4, 200.0, 2200.0,
       (40.0, 400.0), auth=3, functions=("cargo_handling", "storage"),
       interacts=("cargo_crane", "container")),
    _P("hazard_tanks", "Hazardous liquid and inert gas holding tanks",
       "yellow", 0, 6, 260.0, 1400.0, (40.0, 300.0), auth=3,
       functions=("hazardous_storage", "atmosphere_feedstock"),
       interacts=("valve", "tank_gauge", "blast_door")),
    _P("rotation_drivers", "Rotation drivers and mag-lev bearing points",
       "yellow", 0, 8, 320.0, 3300.0, (40.0, 120.0), auth=3,
       functions=("rotation", "structure"), interacts=("console",)),
    # SPEC-CHANGE #2 (owner-approved 2026-08-04): z and footprint corrected to
    # the line `transit.core_shuttle_line` actually derives -- z 3,397..8,047,
    # so the midpoint is 5,722 and the length 4,650 m, not 1,700/3,000. The old
    # row put the shuttle in Yellow's aft third, which is exactly the 42% of the
    # station the shuttle DOES NOT serve (transit.py's own finding), so a
    # register row and a timetable disagreed about where a vehicle was.
    # SPEC-CHANGE (proposed 2026-08-04, needs an adoption stamp): the five
    # interactables `docs/spec/PLACES.md` PLC-102 lists under "added" are
    # DECLARED here, so they are checkable by `interact.py --audit` rather than
    # only visible in a render. Every token is already in `rooms.PROPS` and
    # already tiered by PLACES.md 0.1, so nothing here is a new vocabulary:
    #   info_board                 = the stop board (T1 live)
    #   station_schematic_screen   = the line map (T1)
    #   breaker_lever              = the emergency stop (T3)
    #   intercom                   = the help point (T3)
    #   counter                    = the line control desk at stop 1 (T3 serve)
    # `station/shuttle.py` builds all five; before this row they existed in the
    # geometry and no gate could ask for them. THE ADOPTION DIGEST IN
    # `docs/THE-STATION.md` PINS THIS FILE, so this needs a SPEC-CHANGE stamp.
    _P("core_shuttle", "The core shuttle", "yellow", 0, 30, 0.0, 5722.0,
       (20.0, 4650.0), module="core_tube", auth=1,
       functions=("transit",),
       interacts=("shuttle_door", "seat", "handhold", "info_board",
                  "station_schematic_screen", "breaker_lever", "intercom",
                  "counter"),
       note="Runs the axis z 3,397-8,047; does not serve Yellow's aft 3,397 m."),

    # --- M1 completion: the last real places ------------------------------
    _P("alien_resident_qtr", "Alien residential quarters", "green", 0, 4,
       260.0, 4500.0, (30.0, 90.0), module="quarters", auth=4,
       functions=("residence",),
       interacts=("door", "babcom_terminal", "locker", "bunk"),
       note="The non-human population who are NOT ambassadors -- the majority "
            "of the station's aliens. Distinct from both the ambassadorial "
            "suites and the sealed Alien Sector."),
    _P("earharts", "Earhart's", "green", 1, 0, 120.0, 4800.0, (5.0, 16.0),
       module="hospitality", auth=3,
       functions=("hospitality", "food_service", "recreation"),
       interacts=("bar_counter", "table", "stool", "menu_display"),
       within="garden_town",
       note="A named bar on the drum floor -- agricultural fields behind it."),
    _P("fresh_air", "The Fresh Air Restaurant", "green", 1, 0, 128.0, 4800.0,
       (5.0, 16.0), module="hospitality", auth=3,
       functions=("hospitality", "food_service"),
       interacts=("table", "seat", "menu_display"), within="garden_town",
       note="The name is the joke: real air, on the drum floor."),
    _P("happy_daze", "Happy Daze Bar", "grey", 0, 18, 240.0, 3618.0,
       (5.0, 14.0), module="hospitality", auth=4,
       functions=("hospitality", "recreation", "black_market_fringe"),
       interacts=("bar_counter", "table", "stool"), within="plant_zone",
       note="Downbelow's bar. The bottom of the hospitality ladder."),
    _P("security_posts", "Security posts / checkpoints", "red", 2, 2, 230.0,
       6600.0, (30.0, 120.0), auth=4,
       functions=("law_enforcement", "checkpoint"),
       interacts=("duty_desk", "identicard_reader", "barrier"),
       adjacent=("security_central",),
       note="Distributed across all sectors; registered here at its Red hub."),
    _P("nightwatch", "Nightwatch", "red", 2, 3, 244.0, 6600.0, (10.0, 30.0),
       auth=1, functions=("surveillance", "political_policing"),
       interacts=("duty_desk", "babcom_terminal"),
       adjacent=("security_central",),
       note="ERA-CRITICAL: exists only after S2E22. costume.py gates the "
            "armband on the same datum."),
    _P("minipax", "The Ministry of Peace office", "red", 2, 4, 258.0, 6600.0,
       (8.0, 20.0), auth=5, functions=("political_policing", "administration"),
       interacts=("desk", "babcom_terminal"),
       adjacent=("nightwatch",),
       note="PROPOSED. Unplaced by every source; sited with Nightwatch, which "
            "it runs."),
    _P("the_garden", "The Garden (the drum interior)", "green", 1, 0, 60.0,
       5100.0, (60.0, 600.0), module="interior", auth=1,
       functions=("agriculture", "recreation", "atmosphere_plant",
                  "public_social"),
       interacts=("path", "bench"),
       note="The open volume itself -- 2.6 km long, 556 m of air overhead."),
    _P("sanctuaries", "Sanctuaries (4)", "green", 0, 5, 20.0, 4300.0,
       (16.0, 50.0), auth=3, functions=("worship",),
       interacts=("pew", "door", "shrine"),
       note="A counted exterior system whose function Contract 5 never "
            "states; X-7. Four of them."),
    _P("interfaith_chapel", "The interfaith chapel", "green", 0, 5, 40.0,
       4300.0, (8.0, 22.0), auth=5, functions=("worship", "ceremony"),
       interacts=("pew", "door"), adjacent=("sanctuaries",),
       note="PROPOSED. Unplaced; sited with the Sanctuaries."),
    # SPEC-CHANGE (proposed 2026-08-04, needs an adoption stamp): PLC-113's
    # five "added" interactables declared, same rule as `core_shuttle` above --
    #   breaker_lever  = emergency stop (T3) · intercom = help point (T3)
    #   parcel_locker  = lost-property tag point (T3)
    #   level_plaque   = the car plaque (T1 -- 6 cars, 6 numbers)
    #   info_board     = the advert/notice panel (T1, ISN + MiniPax rotation)
    _P("shuttle_car", "Core shuttle car interior", "yellow", 0, 30, 40.0,
       5722.0, (8.0, 40.0), module="core_tube", auth=3,   # SPEC-CHANGE #2
       functions=("transit",),
       interacts=("seat", "handhold", "shuttle_door", "breaker_lever",
                  "intercom", "parcel_locker", "level_plaque", "info_board"),
       within="core_shuttle"),
    _P("radial_tubes", "Radial transport tubes (the spokes)", "green", 1, 0,
       20.0, 5200.0, (10.0, 50.0), module="interior", auth=3,
       functions=("transit",), interacts=("lift_call", "lift_door",
                                          "handhold"),
       note="The 2-minute rim-to-axis ride; 2.00 g of Coriolis if rushed."),
    _P("transfer_systems", "Concentric personnel transfer systems", "green",
       0, 6, 100.0, 4700.0, (20.0, 90.0), auth=3,
       functions=("transit",), interacts=("lift_call", "lift_door"),
       note="The schematic's own callout, at the rotating interface."),
    _P("lifts", "Transport tubes / lifts (between levels)", "blue", 0, 5,
       80.0, 7500.0, (40.0, 200.0), auth=3, functions=("transit",),
       interacts=("lift_call", "lift_door", "level_plaque"),
       note="Distributed; registered at its Blue hub. The LEVEL plaque is "
            "authority-1 signage whose number is a parameter -- C-004."),
    _P("standard_corridor", "Standard corridor", "blue", 0, 9, 300.0, 7500.0,
       (60.0, 400.0), module="interior_kit", auth=1,
       functions=("transit",),
       interacts=("door", "babcom_terminal", "level_plaque"),
       note="The kit. 3,414 streaming cells of it across 251 decks."),
    _P("medlab_others", "The other Medlabs", "red", 1, 7, 320.0, 6600.0,
       (12.0, 30.0), auth=4, functions=("medical", "triage"),
       interacts=("diagnostic_bed", "medcabinet"),
       note="X-6: medical distributed across Red, Green and Blue."),

    # ======================================================================
    # THE VOLUME AUDIT'S MISSING INTERIORS -- session 3z
    # ----------------------------------------------------------------------
    # `docs/volume-audit.md` matched all 28 `exterior_systems` against the
    # interior each implies and found **7 matched, 21 not**: eleven with no
    # interior at all, five addressed hundreds or thousands of metres from the
    # geometry the same schema builds, five with a function somewhere in the
    # register and nothing placed against the system. A reactor on the hull
    # with no reactor hall behind it is the facade the owner's session-3y
    # question was about -- "everything on the outside has a function on the
    # inside ... it can't be a facade".
    #
    # These ten are the audit's Sec.4 rows, RE-VERIFIED rather than copied,
    # and four of them moved as a result. What the re-check found:
    #
    #  * `coolant_gallery` was proposed at yellow ring 3, z 450-950, and
    #    **ring 3 does not exist anywhere in that band.** The hull waists to a
    #    48.9 m core radius at z 435 and carries ONE deck stack from 435 to
    #    475; four stacks -- the condition for a ring index of 3 to mean the
    #    28.0-59.1 m shell -- exist only at z 35-305, 1265-2755 and 3120-3397.
    #    Moved to z 170, which is where the manifolds wrap the reactor anyway.
    #  * `generator_hall`, `comms_operations` and `gunnery_control` each
    #    STRADDLED a boundary where the hull closes a ring. `ring_radii(z_m=)`
    #    drops a ring the hull has closed, so "ring 1" was the 93.3-127.5 m
    #    shell at one end of the room and the 59.1-93.3 m shell at the other.
    #    Shrunk or shifted so each sits in one ring set.
    #  * `heat_exchanger_hall` was proposed on yellow ring 0 **deck 3**, a deck
    #    number that ring does not currently carry. `deck.deck_index` ranks the
    #    distinct deck numbers on a ring when they exceed the stack depth, so a
    #    NEW number re-ranks every existing place on that ring -- it would have
    #    moved `spinal_cargo`, `hazard_tanks`, `rotation_drivers`,
    #    `core_shuttle` and `shuttle_car` one deck each. Deck 4 is an existing
    #    label at 141.1 m and 0.507 g and disturbs nothing.
    #
    # Every row below was checked at 401 samples across its own footprint span
    # for: the ring set constant across the span, the ring and deck indices
    # unclamped, the UNCUT floor radius -- the one `rooms.room_extent_m` and
    # `interior.ring_cells` actually build at, because neither takes z_m --
    # inside `core_hull_profile(z) - HULL_SKIN_M`, and no collision under
    # `collisions()`'s own arc/z test. Margins are quoted per row.
    #
    # auth=5 throughout: these are extrapolations under hard rule 1, logged as
    # INV-104. No source gives a room dimension for a reactor hall.

    # --- Yellow: the power train the hull has and the register did not -----
    _P("reactor_hall", "Primary reactor hall and control room", "yellow", 0, 0,
       20.0, 240.0, (60.0, 120.0), auth=5,
       functions=("power_generation", "reactor_control", "radiation_boundary"),
       interacts=("reactor_console", "blast_door", "breaker_lever", "catwalk"),
       adjacent=("fuel_bunkerage", "coolant_gallery"), within="fusion_core",
       note="`primary_fusion_reactor` is z 39-331 of hull and held ZERO "
            "addressed places -- `fusion_core` covers the z and declares only "
            "`power_generation`. 155.4 m floor, 0.559 g, 18.8 m clear of the "
            "pressure hull across z 180-300. INV-104."),
    _P("fuel_bunkerage", "Core fuel housing and transfer gallery", "yellow", 0,
       2, 200.0, 150.0, (60.0, 220.0), auth=5,
       functions=("fuel_storage", "hazardous_storage", "fuel_transfer"),
       interacts=("valve", "tank_gauge", "blast_door", "cargo_crane"),
       adjacent=("reactor_hall",), within="fusion_core",
       note="00-MASTER.md Sec.2 item 1, the aft terminus. `fuel_stores` is "
            "SHIP fuel at the docks 7 km fore. 148.2 m, 0.533 g, 30.8 m "
            "clear. INV-104."),
    _P("coolant_gallery", "Coolant manifold gallery", "yellow", 3, 3, 120.0,
       170.0, (90.0, 240.0), auth=5,
       functions=("cooling", "coolant_transfer", "maintenance_access"),
       interacts=("valve", "tank_gauge", "catwalk", "handhold"),
       adjacent=("reactor_hall",),
       note="The 8 coolant manifolds of 00-MASTER.md Sec.2 item 2, wrapping "
            "the reactor at 48.3 m and 0.173 g -- a crawlway, not a corridor. "
            "MOVED from the audit's z 700: yellow carries one deck stack from "
            "z 435 to 475 and ring 3 does not exist there. 130 m clear. "
            "INV-104."),
    _P("generator_hall", "Generator torus hall", "yellow", 1, 4, 250.0, 1185.0,
       (60.0, 150.0), auth=5,
       functions=("power_generation", "power_distribution"),
       interacts=("console", "breaker_lever", "catwalk", "blast_door"),
       note="`generator_torus_housing` is z 1095-1295, 0.0176 km^3 of hull, "
            "zero addressed places. 113.1 m, 0.406 g, 1.0 m clear -- the "
            "tightest row here, and the outermost deck the hull leaves at that "
            "z. Span shrunk to 1110-1260 so the ring set does not change "
            "under it. INV-104."),
    _P("heat_exchanger_hall", "Heat exchanger hall", "yellow", 0, 4, 60.0,
       2300.0, (60.0, 400.0), auth=5,
       functions=("heat_rejection", "cooling", "coolant_loop",
                  "emergency_power"),
       interacts=("valve", "tank_gauge", "catwalk", "console"),
       note="Behind the 12 heat exchange / emergency solar arrays, z "
            "2020-2537. ~1.9 GW of rejected heat (LIFE-SUPPORT-AND-INDUSTRY.md "
            "L-01) and NO place on the station carried a thermal function. "
            "141.1 m, 0.507 g, 6.4 m clear. INV-104."),
    _P("comms_operations", "Deep space comms operations", "yellow", 1, 5,
       300.0, 2600.0, (24.0, 100.0), auth=5,
       functions=("communications", "signal_ops"),
       interacts=("console", "monitor_wall", "babcom_terminal"),
       note="At the root of `comms_grid_pylon` AS BUILT (z 2515-2988). The "
            "register's `comms_grid` is at z 7900 -- 5,148 m from the pylons "
            "that carry it -- with an empty interacts tuple. Position "
            "contested: volume-audit.md Sec.6 has three sources giving three "
            "answers. 109.5 m, 0.393 g, 49.3 m clear. INV-104."),

    # --- Green: behind 1,140 m of magnetic cargo rail ----------------------
    _P("cargo_transfer_deck", "Cargo transfer deck", "green", 0, 5, 90.0,
       5400.0, (30.0, 900.0), auth=5,
       functions=("cargo_handling", "storage", "manifest"),
       interacts=("cargo_crane", "container", "manifest_terminal", "bay_door",
                  "docking_clamp"),
       adjacent=("subfloor_stack",),
       note="Under the six dorsal cargo modules (schema components."
            "cargo_module, z 4870-6010, 0.3601 km^3) -- 1,140 m of magnetic "
            "rail outside with no hold, no handling deck and no manifest "
            "office behind it. On the drum's sub-floor stack at 299.9 m and "
            "1.078 g; 1.4 m clear of the hull, the thinnest margin of the "
            "ten. INV-104."),

    # --- Blue: the pressure boundary, and the defence grid -----------------
    _P("mooring_gallery", "Mooring clamp gallery", "blue", 0, 2, 180.0, 7250.0,
       (20.0, 60.0), auth=5,
       functions=("ship_mooring", "umbilical_service"),
       interacts=("docking_clamp", "console", "blast_door", "handhold"),
       adjacent=("docking_bays", "mooring_clamps"),
       note="Behind 00-MASTER.md Sec.2 item 23. `mooring_clamps` is a label "
            "with one interact and no geometry. 204.3 m, 0.734 g, 5.3 m "
            "clear. INV-104."),
    _P("eva_lock_blue", "EVA airlock and suit room, Blue", "blue", 0, 1, 100.0,
       7230.0, (10.0, 30.0), auth=5,
       functions=("eva_egress", "suit_service"),
       interacts=("blast_door", "tool_rack", "handhold", "console",
                  "intercom"),
       adjacent=("docking_bays",),
       note="FACTIONS.md rosters 630 EarthForce crew in 'maintenance, repair, "
            "EVA' and the station has no airlock, inside or out -- "
            "`airlock_door` appears in exactly two places' interacts, both of "
            "them Alien Sector atmosphere locks. 207.9 m, 0.747 g, 15.4 m "
            "clear. INV-104.\n"
            "THE INTERACTS ARE CONSTRAINED BY MATERIAL COVERAGE, and it is "
            "worth saying so rather than leaving it to look like a choice. "
            "The lock's outer door is `blast_door` and not `airlock_door`, and "
            "the suit stowage is `tool_rack` and not `locker`, because 33 of "
            "the 99 entries in `rooms.PROPS` -- including `airlock_door`, "
            "`locker`, `service_ladder`, `comms_channel` and "
            "`atmosphere_status_lamp` -- have NO bind in materials.py, which "
            "is not this session's file. Emitting one would ship "
            "unmaterialled geometry and worsen "
            "station/test_materials_layer3.py. The suit RACK is present as a "
            "fixture (`fix_suit_plant_frame`); what is missing is the thing a "
            "player opens. The binds needed are reported with the session."),
    _P("gunnery_control", "Defence grid fire control", "blue", 1, 4, 340.0,
       7100.0, (14.0, 40.0), auth=5,
       functions=("defence_command", "fire_control"),
       interacts=("console", "tactical_display", "blast_door"),
       adjacent=("cnc", "war_room"),
       note="00-MASTER.md Sec.1 lists anti-fighter pulse cannons at AUTHORITY "
            "1 and four documents state the era lock as 'defence grid "
            "installed'; `pulse cannon` and `defence grid` appear in no .py, "
            "no .yaml and no exterior_systems entry. At the cobra bays' own z "
            "(7026-7204). 159.1 m, 0.572 g, 59.4 m clear. INV-104."),
)


# Gazetteer rows deliberately NOT addressed yet, each with a reason. This list
# is what keeps "126 rows" from being a vague backlog: everything is either
# placed above or named here.
# Gazetteer rows that are deliberately NOT addressed as places, each with the
# reason. Layer 1 is complete when every row is either in PLACES or here.
NOT_A_PLACE = {
    "\"Customs Sector\"": "an area LABEL used alongside the six colour sectors, "
                         "not a room. Wayfinding must carry both naming "
                         "systems; that is a signage requirement.",
    "The jump gate": "off-station. Its own subsystem, not a location on the "
                     "8,047 m hull.",
    "The Zocalo neon wordmark": "a prop within the Zocalo, not a separate "
                                "place. Six Latin glyphs, ZoCaLo.",
    "The \"5\" roundel as furniture branding": "a motif applied across many "
                                             "places, not a place.",
    "Babcom terminals": "a prop type, already declared in 20 places' "
                        "`interacts`. Registering it as a location would "
                        "double-count it.",
    "Public information monitors": "a prop type, as above.",
    "Alien signage systems": "a signage/typography system spanning every "
                             "place, not a place.",
    "ISN -- Interstellar Network News": "a broadcast, not a room. It is world "
                                        "system W8 (information).",
}

# Gazetteer rows whose wording differs enough from the place name that fuzzy
# matching cannot resolve them. Mapped by hand rather than by loosening the
# threshold, which would start matching unrelated rows to each other.
ALIASES = {
    "Customs (×2, north and south)": "customs_north",
    "An unnamed bar / diner": "bar_unnamed",
    "Alien sector corridor": "alien_sector",
    "Kosh's quarters (Vorlon ambassador)": "kosh_quarters",
    "A second, ground-level transit system": "ground_tram",
    "Ambassadorial / diplomatic quarters": "ambassadorial_suites",
    "Alien residential quarters": "alien_resident_qtr",
}

DEFERRED = {
    "unplaced": "no source places it; needs a P-number proposal first",
    "off_station": "not on the station -- the jump gate, arriving ships",
    "exterior": "hull components, tracked by components.py rather than here",
    "duplicate": "a detail of a location already addressed",
    "not_a_place": "a signage, typography or naming row rather than a room",
    "backlog": "a real room, sourced, simply not reached yet",
}


def by_key(key):
    for p in PLACES:
        if p["key"] == key:
            return p
    raise KeyError(f"no place {key!r}")


def gravity_of(schema, profile, place):
    """The gravity a person feels standing in this place.

    Read live from `interior.py` per deck, never restated -- the same
    discipline `quarters.py` uses, and for the same reason: INV-026 moved
    every sector radius and any copied figure went stale that day.

    THE RESOLUTION ITSELF IS NOW READ LIVE TOO. This used to be four lines --
    find the deck stacks, clamp the ring, clamp the deck, take the radius --
    and `rooms.room_extent_m` had the same four for the same reason. Two
    copies, no shared definition, so `interior.place_floor_radius` now owns it
    and both call it. Same values; the point is that the next fix lands once.
    """
    r, _ri, _di, deck = it.place_floor_radius(schema, profile, place)
    return deck["floor_g"] if deck else it.gravity_at(schema, r)


def _arc_overlap(a0, span0, a1, span1):
    """Do two angular spans overlap on a circle?

    A FULL CIRCLE OVERLAPS EVERYTHING, and this said it overlapped almost
    nothing. `norm(a - 180)` and `norm(a + 180)` are the SAME NUMBER, so a
    360-degree footprint collapsed to a single point and
    `_arc_overlap(0, 360, 90, 10)` returned False. Four places carry a
    full-circle footprint -- `docking_bays`, `plant_zone`, `fusion_core`,
    `cobra_bays` -- so every collision involving one of them was invisible.
    `collisions()` returned an empty list, which reads as "no location on this
    station overlaps another" and really meant "the check cannot see the four
    largest footprints on the station".

    Found by the volume audit, which asked what the exterior implies the
    interior must contain and noticed the register was claiming no overlaps at
    all.
    """
    if span0 >= 360.0 or span1 >= 360.0:
        return True

    def norm(x):
        return x % 360.0
    s0, e0 = norm(a0 - span0 / 2), norm(a0 + span0 / 2)
    s1, e1 = norm(a1 - span1 / 2), norm(a1 + span1 / 2)

    def covers(s, e, x):
        return (s <= x <= e) if s <= e else (x >= s or x <= e)
    return (covers(s0, e0, s1) or covers(s0, e0, e1)
            or covers(s1, e1, s0) or covers(s1, e1, e0))


def contains(outer, inner):
    """Is `inner` declared to sit inside `outer`, transitively?"""
    seen = set()
    cur = inner
    while cur and cur.get("within") and cur["within"] not in seen:
        seen.add(cur["within"])
        if cur["within"] == outer["key"]:
            return True
        try:
            cur = by_key(cur["within"])
        except KeyError:
            return False
    return False


def collisions():
    """Pairs of places that occupy the same deck AND overlap in both axes.

    Two rooms on the same deck at the same angle and the same z are the same
    room, and nothing else in the project could have noticed: each module
    builds in its own frame and never sees another.

    CONTAINMENT IS NOT COLLISION, and the first run of this check proved the
    model needed to say so. It flagged three pairs -- C&C inside Observation
    Dome 1, Kosh's quarters inside the Alien Sector, Downbelow inside the plant
    zone -- and all three are correct nesting. A place declares `within` and is
    then expected to overlap its container; anything else overlapping is a real
    defect. Exempting them by name would have been a fudge; modelling
    containment is the fact.
    """
    out = []
    for i, a in enumerate(PLACES):
        for b in PLACES[i + 1:]:
            if (a["sector"], a["ring"], a["deck"]) != (b["sector"], b["ring"],
                                                       b["deck"]):
                continue
            if contains(a, b) or contains(b, a):
                continue
            if not _arc_overlap(a["angle_deg"], a["footprint"][0],
                                b["angle_deg"], b["footprint"][0]):
                continue
            za0, za1 = a["z_m"] - a["footprint"][1] / 2, a["z_m"] + a["footprint"][1] / 2
            zb0, zb1 = b["z_m"] - b["footprint"][1] / 2, b["z_m"] + b["footprint"][1] / 2
            if za1 <= zb0 or zb1 <= za0:
                continue
            out.append((a["key"], b["key"]))
    return out


def gazetteer_rows():
    """Every location row in LOCATIONS.md, parsed rather than remembered."""
    rows = []
    with open(GAZETTEER, encoding="utf-8") as f:
        for line in f:
            if line.startswith("| **") and line.count("|") > 6:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                name = re.sub(r"\*+", "", cells[0]).strip()
                rows.append(name)
    return rows


# The layers, from CLAUDE.md's plan. A location's layer is the HIGHEST one it
# has reached; layers are cumulative and ordered, so a room with geometry but no
# materials is at layer 2 and saying it is finished is false.
#
# `reached` is a predicate over a place. Layers 3+ have no evidence to read yet
# -- there are no materials, no lights, no props -- and they deliberately return
# False rather than being omitted, so the register reports zero instead of
# reporting nothing.
GENERATOR = "rooms"


def _generated_keys():
    """Keys `rooms.py` actually emits geometry for.

    Imported lazily: `rooms` imports this module at load time, and asking for
    it at import would be circular. Cached because `layer_report` asks 118
    times.

    This is a MEMBERSHIP TEST rather than `module is None`, and the difference
    is the whole point. Treating "no bespoke module" as "the generator covers
    it" would make the layer-2 predicate return True for every row in the
    table -- a counter that cannot go down, which is the same class of defect
    as an assertion that cannot fail. Asking the generator what it built means
    the count drops the moment it stops building something.
    """
    if _generated_keys.cache is None:
        import rooms                                          # noqa: PLC0415
        s, p = it.load()
        _generated_keys.cache = frozenset(
            q["key"] for q in rooms.unbuilt(s, p))
    return _generated_keys.cache


_generated_keys.cache = None


def _materialled_keys():
    """Places whose every emitted group resolves to a material.

    Computed, not flagged. The alternative was a `materials=True` field on each
    entry, which is a claim somebody types; this asks the material library
    whether it actually covers the geometry, so the number falls the moment a
    room grows a surface nobody has painted.

    Only the generated places can be answered today: `rooms.py` will tell you
    exactly which groups a place emits, and the fifteen bespoke modules will
    not without being run. Those are reported as NOT at layer 3 rather than
    assumed to be at it -- CLAUDE.md rule 4, nothing is done at a layer it has
    not reached, and an unknown is not a pass.
    """
    if _materialled_keys.cache is None:
        import rooms                                           # noqa: PLC0415
        import materials as mat                                # noqa: PLC0415
        import test_materials_layer3 as gate                   # noqa: PLC0415
        s, p = it.load()
        done = set()
        # The 68 procedural places, each measured on its own geometry.
        for q in rooms.unbuilt(s, p):
            _v, _t, g = rooms.build(s, p, q)
            if all(mat.resolve_any(n, "interior") for n, _lo, _hi in g):
                done.add(q["key"])
        # The bespoke places, measured on their MODULE's geometry. A module is
        # one generator emitting one set of surfaces, so a place it owns is
        # materialled exactly when that set resolves -- there is no per-place
        # geometry to measure separately, and pretending otherwise would mean
        # inventing a subdivision the generator does not have.
        #
        # Only modules `test_materials_layer3` knows how to BUILD are counted.
        # The rest are reported as not-at-layer-3 rather than assumed to be,
        # which is why this number is lower than "everything resolves" would
        # suggest and is the honest one.
        for name, build in gate.BESPOKE_BUILDERS.items():
            try:
                groups = build(s, p)
            except Exception:                                  # noqa: BLE001
                continue
            if not groups:
                continue
            scene = gate.BESPOKE_SCENE.get(name, "interior")
            # A scene with a declared fallback covers what no rule matches --
            # `hull_exterior` is deliberately unbound because most of an 8 km
            # hull is hull. Four exterior components land there by design, and
            # counting them as unmaterialled would hold this number below 118
            # for ever over surfaces that render correctly.
            ok = scene in gate.SCENE_FALLBACK or all(
                mat.resolve_any(g, scene) for g in groups)
            if ok:
                done |= {q["key"] for q in PLACES if q["module"] == name}
        _materialled_keys.cache = frozenset(done)
    return _materialled_keys.cache


_materialled_keys.cache = None


def materials_of(place):
    """Does every surface this place emits carry a material?"""
    return place["key"] in _materialled_keys()


# Which `drum_parts` part each place-bearing drum module supplies. Needed
# because DRUM_CALIBRATION is keyed by PART and PLACES by MODULE, and the two
# vocabularies are not the same: `interior` alone supplies four parts.
_MODULE_PARTS = {
    "interior": ("endcap_fore", "endcap_aft", "guideways", "spokes"),
    "core_tube": ("core",),
    "tram": ("trams",),
    "garden": ("townscape",),
}


def _lit_keys():
    """Places whose geometry emits at least one tagged light fitting.

    Computed for the same reason layer 3 is, and against the same failure. The
    predicate this replaces was `bool(place.get("lights"))` -- a field nobody
    sets, so the counter read 0 whatever the geometry did, and would have read
    118 the moment somebody typed the field in.

    WHY A TAGGED FITTING AND NOT "ANYTHING THAT GLOWS". Seventeen of the 68
    generated rooms emit a console or a screen, and `device_screen_glass` has
    an emission. Counting those would have reported the station lit while
    every one of those rooms rendered black, which is precisely what it did
    for a session: `export_scene.fixture_lights` makes a real light source per
    `light_*` group and nothing else in an interior casts anything, so a
    location without one is dark no matter how many of its props glow.

    The sixteen bespoke modules are reported as NOT at layer 4 rather than
    assumed to be. Several of them do build lamps -- the Zocalo's rib lamps,
    the docking bay's floods -- but they have not been through a layer-4 pass,
    which is a calibrated exposure and a frame measured against its reference
    (tools/measure_frame.py), not just a lamp in the geometry. CLAUDE.md rule
    4: nothing is done at a layer it has not reached, and an unknown is not a
    pass.
    """
    if _lit_keys.cache is None:
        import rooms                                            # noqa: PLC0415
        import test_materials_layer3 as gate                    # noqa: PLC0415
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "tools"))
        import export_scene as X                                # noqa: PLC0415
        s, p = it.load()
        done = set()
        for q in rooms.unbuilt(s, p):
            _v, _t, g = rooms.build(s, p, q)
            if any(n.startswith("light_") for n, _lo, _hi in g):
                done.add(q["key"])
        # A BESPOKE MODULE COUNTS ON TWO CONDITIONS, not one. It must emit a
        # group the light rig will actually turn into a source -- membership of
        # FIXTURE_LIGHTING, which is what `fixture_lights` tests -- AND it must
        # have a calibrated exposure. Fittings without an exposure is a lit
        # room at an unmeasured brightness, and layer 4 is "lit to its
        # reference's mood", not "lit".
        for name, build in gate.BESPOKE_BUILDERS.items():
            # THE ANCHOR COUNTS, and it was the one module this test excluded.
            # `interior_kit` builds the corridor and the junction -- the two
            # places every exposure in the project is calibrated against, whose
            # fittings were the first ever measured and whose frame is what
            # 1.40 means. It has no BESPOKE_EXPOSURE entry because it IS the
            # 1.0 the others are measured in, handled by name in
            # `export_scene.room_exposure`, so a membership test on that dict
            # reported the best-calibrated room on the station as unlit.
            if name != "interior_kit" and name not in X.BESPOKE_EXPOSURE:
                continue
            try:
                groups = build(s, p)
            except Exception:                                  # noqa: BLE001
                continue
            if any(g in X.FIXTURE_LIGHTING for g in groups):
                done |= {q["key"] for q in PLACES if q["module"] == name}
        # THE DRUM IS ONE LIT VOLUME WITH ONE RIG, and its rig is not
        # FIXTURE_LIGHTING. `export_scene.light_runs` derives sixty sources
        # from the guideway trusses' own placement arithmetic -- authority 1,
        # `Babylon_5_2-22_34b.jpg` shows the tubes alongside the truss -- so
        # the modules inside the drum are lit by the drum, exactly as the
        # corridor kit's two places are lit by the corridor's fittings.
        #
        # The condition is the same two-part one the interior modules face: a
        # real rig, and a measured exposure. `DRUM_EXPOSURE` is that exposure
        # and it was the last lit volume in the project to get one -- the shot
        # read x1.03 of its reference against the x1.40 target until session
        # 3q measured it. Without the exposure this branch does not fire.
        if X.DRUM_EXPOSURE and X.RUN_ENERGY > 0:
            # ONLY THE MODULES THE DRUM SHOT ACTUALLY CONTAINS, and the first
            # version of this did not check. It counted every drum-scene module
            # because the DRUM had an exposure, which took `garden` -- four
            # locations -- on the strength of a frame its geometry is not in.
            # `drum_parts` is the one list of what the shot holds: ground, two
            # end caps, guideways, spokes, core and trams. `garden.townscape()`
            # is not among them, so the four garden places have never appeared
            # in a rendered frame and are not at layer 4.
            #
            # Computed by intersecting each module's own group names with the
            # shot's, rather than by listing the modules here: a list would be
            # a second copy of `drum_parts`, and this project's recurring
            # failure is two copies of a mapping with one of them updated.
            # ...AND ONLY THE PARTS IT DEMONSTRABLY SHOWS. Membership of
            # `drum_parts` is what the shot BUILDS; `drum_visible_parts` is
            # what it SHOWS, measured by omitting one part at a time and
            # counting pixels that move. Three of the eight contribute
            # essentially nothing -- `endcap_aft` is behind the camera,
            # `townscape` is 92 degrees around the barrel, and `trams` is
            # thirteen pixels at the far end of a 2.6 km drum.
            eye = (0.0, it.sector_radius(s, p, it.drum_sector(s, p)) * 0.5,
                   0.0)
            visible = X.drum_visible_parts()
            shot_groups = set()
            for _n, _v, _t, g_ in X.drum_parts(s, p, it.drum_sector(s, p),
                                               eye):
                if _n not in visible:
                    continue
                shot_groups |= ({x[0] for x in g_}
                                if g_ and isinstance(g_[0], (list, tuple))
                                else set(g_))
            for name, sc in gate.BESPOKE_SCENE.items():
                if sc != "drum" or name not in gate.BESPOKE_BUILDERS:
                    continue
                try:
                    groups = gate.BESPOKE_BUILDERS[name](s, p)
                except Exception:                              # noqa: BLE001
                    continue
                if groups & shot_groups:
                    done |= {q["key"] for q in PLACES if q["module"] == name}
        # THE EXTERIOR IS A LIT VOLUME TOO, and the nine `components` places --
        # cobra bays, the observation domes and rotundas, mooring clamps,
        # proximity arrays, nav beacon, comms grids, power transfer core -- are
        # fittings on its hull. They fell through both branches above: they are
        # not in BESPOKE_EXPOSURE, which holds ROOM exposures, and they are not
        # in the drum.
        #
        # The condition is the same two-part one, read the same way. A real rig:
        # the exterior's is the Sun, and unlike an interior it needs no
        # FIXTURE_LIGHTING membership, because a hull fitting in sunlight is lit
        # by the sun whether or not it carries a lamp of its own. And a measured
        # exposure: `EXTERIOR_CALIBRATION["day"]` was derived against
        # `exterior more.jpg`'s habitat drum by `tools/measure_frame.py`, the
        # same code every room exposure uses, and verified at x1.403.
        #
        # WHAT MAKES THIS FALSIFIABLE rather than a second way of saying the
        # exterior exists: the .tscn is read back, and the recorded verification
        # only counts if the scene is still at the exposure it was verified at.
        # Set `Env`'s tonemap_exposure back to the 1.00 it sat at for four
        # sessions -- two and a third stops hot, the setting that made
        # `engine-approach-far.png` a white shape -- and these nine places stop
        # counting, which is correct, because nobody would have measured the
        # frame they are in.
        try:
            cal = X.EXTERIOR_CALIBRATION["day"]
            tscn = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "godot/scenes/exterior.tscn")
            calibrated = abs(X.scene_env_exposure(tscn, "Env")
                             - cal["exposure"]) < 1e-6
        except Exception:                                      # noqa: BLE001
            calibrated = False
        if calibrated:
            hull = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "station/generated/hull.obj")
            ext_groups = set()
            if os.path.exists(hull):
                with open(hull, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("g "):
                            ext_groups.add(line[2:].strip())
            for name, sc in gate.BESPOKE_SCENE.items():
                if sc != "exterior" or name not in gate.BESPOKE_BUILDERS:
                    continue
                try:
                    groups = gate.BESPOKE_BUILDERS[name](s, p)
                except Exception:                              # noqa: BLE001
                    continue
                if groups & ext_groups:
                    done |= {q["key"] for q in PLACES if q["module"] == name}
        _lit_keys.cache = frozenset(done)
    return _lit_keys.cache


_lit_keys.cache = None


def lighting_of(place):
    """Does this place emit a light fitting the renderer will turn into a lamp?"""
    return place["key"] in _lit_keys()


def geometry_of(place):
    """Which module builds this place, or None if nothing does."""
    if place["module"]:
        return place["module"]
    return GENERATOR if place["key"] in _generated_keys() else None


def _articulated_keys():
    """Layer 2b: places that clear their DERIVED detail floor.

    THE OLD PREDICATE WAS `bool(geometry_of(place))` -- does a mesh exist -- and
    that is why 118 locations of blockout passed layer 2 while the owner, looking
    at a render, called the buildings "shitty little cubes" and every gate in the
    repository was green. A cube has a mesh. It is closed, correctly wound and
    inside its footprint, so it satisfied every word of the criterion, and layers
    3 and 4 then put materials and lighting on blockout.

    `station/density.py` supplies the missing half: visible line density against
    a floor derived three ways -- the triangle budget, a Nyquist limit at the
    distance the place is actually composed from, and edge density measured off
    scale-anchored B5 frames -- smallest bound wins. A subdivided box cannot
    defeat it: split a box 8x8 per face and it has 64x the triangles and an
    IDENTICAL lambda to six decimal places, because a coplanar split draws no
    line.

    ERRORS ARE NOT CAUGHT HERE, and that is deliberate. The first version of
    this wrapped `density.score` in a bare `except` returning False, called it
    with the wrong signature, and reported a confident **0/118** -- a number that
    looked entirely plausible and was fabricated by the exception handler. A
    silent except that invents a count is the same defect as an assertion that
    cannot fail. If the metric breaks, this must break loudly.
    """
    if _articulated_keys.cache is None:
        import density                                          # noqa: PLC0415
        s, p = it.load()
        out = set()
        for q in PLACES:
            if not geometry_of(q):
                continue
            if density.score(s, p, q)["passes"]:
                out.add(q["key"])
        _articulated_keys.cache = frozenset(out)
    return _articulated_keys.cache


_articulated_keys.cache = None


LAYERS = (
    (1, "addressed", lambda p: True),
    (2, "geometry", lambda p: p["key"] in _articulated_keys()),
    (3, "materials", materials_of),
    (4, "lighting", lighting_of),
    (5, "props", lambda p: bool(p.get("props_built"))),
    (6, "inhabitants", lambda p: bool(p.get("npcs_placed"))),
    (7, "audio", lambda p: bool(p.get("audio"))),
    (8, "judged", lambda p: bool(p.get("rubric_score"))),
)


def layer_of(place):
    """The highest CONTIGUOUS layer this place has reached.

    Contiguous matters: a place that somehow had audio but no materials is not
    at layer 7, it is at layer 2 with a stray attribute. Reporting the highest
    reached rather than the highest contiguous is how a project convinces
    itself it is further along than it is.
    """
    n = 0
    for idx, _name, reached in LAYERS:
        if not reached(place):
            break
        n = idx
    return n


def layer_report(schema, profile):
    """Per-layer completion, counted against every gazetteer row that is a PLACE.

    THE DENOMINATOR IS THE DELICATE PART. It was every gazetteer row, which was
    right while rows were unaddressed: a layer is not complete because the
    places we happen to have registered are done with it. But 8 of the 126 rows
    are not locations -- a prop type declared in 20 rooms' `interacts`, a
    broadcast, an area label, the off-station jump gate -- and they can never
    reach any layer. Left in the denominator they would hold every layer at
    118/126 forever, and CLAUDE.md rule 3 says a layer is complete when this
    file says so. A rule that can never fire is not a rule.

    So the denominator is rows-minus-deferrals, and BOTH numbers are reported
    and printed. Moving a row into `NOT_A_PLACE` to make a number go green is
    the failure this guards against, and it is guarded by the assertion that
    every row is either addressed or deferred WITH A REASON -- so the deferral
    list cannot grow silently, and the report shows its size next to the count.
    """
    rows = len(gazetteer_rows())
    total = rows - len(NOT_A_PLACE)
    out = []
    for idx, name, _reached in LAYERS:
        n = sum(1 for p in PLACES if layer_of(p) >= idx)
        out.append(dict(layer=idx, name=name, done=n, total=total,
                        gazetteer_rows=rows, deferred=len(NOT_A_PLACE),
                        complete=(n == total)))
    return out


def coverage(schema, profile):
    """What fraction of the gazetteer has an address, and what has geometry."""
    rows = gazetteer_rows()
    addressed = len(PLACES)
    built = len({p["module"] for p in PLACES if p["module"]})
    with_geom = sum(1 for p in PLACES if p["module"])
    return dict(gazetteer_rows=len(rows), addressed=addressed,
                addressed_with_geometry=with_geom, modules=built,
                unaddressed=len(rows) - addressed)


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

    # --- addresses are real ------------------------------------------------
    sectors = set(schema["sectors"]["extents_m"])
    for p in PLACES:
        check(f"{p['key']}: sector exists", p["sector"] in sectors,
              p["sector"])
        ex = schema["sectors"]["extents_m"][p["sector"]]
        z0 = p["z_m"] - p["footprint"][1] / 2
        z1 = p["z_m"] + p["footprint"][1] / 2
        check(f"{p['key']}: fits inside its sector longitudinally",
              ex["z0"] - 1e-6 <= z0 and z1 <= ex["z1"] + 1e-6,
              f"z {z0:.0f}-{z1:.0f} in {ex['z0']}-{ex['z1']}")
        check(f"{p['key']}: angular footprint is sane",
              0 < p["footprint"][0] <= 360.0, str(p["footprint"]))

    # --- THE POINT: they do not collide with each other --------------------
    col = collisions()
    check("no two places occupy the same volume", not col, str(col))

    # Containment must be REAL, not merely declared: a place inside another
    # must actually fit inside it, or `within` becomes a way to silence the
    # collision check.
    for p in PLACES:
        if not p.get("within"):
            continue
        o = by_key(p["within"])
        check(f"{p['key']}: its container is in the same sector",
              p["sector"] == o["sector"], f"{p['sector']} vs {o['sector']}")
        check(f"{p['key']}: fits inside {o['key']} angularly",
              p["footprint"][0] <= o["footprint"][0] + 1e-9,
              f"{p['footprint'][0]} vs {o['footprint'][0]} deg")
        check(f"{p['key']}: fits inside {o['key']} longitudinally",
              p["footprint"][1] <= o["footprint"][1] + 1e-9,
              f"{p['footprint'][1]} vs {o['footprint'][1]} m")

    # --- adjacency is symmetric and real -----------------------------------
    keys = {p["key"] for p in PLACES}
    for p in PLACES:
        for a in p["adjacent"]:
            check(f"{p['key']}: adjacent {a!r} exists", a in keys, a)
            if a in keys:
                other = by_key(a)
                # Adjacent means reachable, so at minimum the same sector.
                check(f"{p['key']}~{a}: adjacency is within one sector",
                      p["sector"] == other["sector"],
                      f"{p['sector']} vs {other['sector']}")

    # The two adjacencies the sources actually require.
    check("customs adjoins the docking bays, as the gazetteer states",
          "docking_bays" in by_key("customs_north")["adjacent"])
    check("the brig is reachable from Security Central and the courts",
          set(by_key("brig")["adjacent"]) >= {"security_central",
                                              "law_courts"},
          "P-04's whole constraint")

    # --- gravity suits the function ----------------------------------------
    # A room's gravity is not a detail: surgery at 1.7 g is a different
    # operation. This is the first check in the project that ties FUNCTION to
    # PLACEMENT, and it is what stops a location being dropped somewhere
    # merely because the deck was free.
    for p in PLACES:
        g = gravity_of(schema, profile, p)
        if "surgery" in p["functions"] or "medical" in p["functions"]:
            check(f"{p['key']}: medical is not sited in punishing gravity",
                  g <= 1.10, f"{g:.3f} g")
        if "residence" in p["functions"]:
            check(f"{p['key']}: residence is within the habitable ceiling",
                  g <= it.HABITABLE_G_MAX, f"{g:.3f} g")
    # Informal residence, stated honestly. The first version asserted EVERY
    # informal-residence place sits above the habitable ceiling, and
    # subfloor_stack failed it at 1.103 g -- correctly, because LOCATIONS.md
    # puts Downbelow in "Grey OR the drum sub-floor" and the sub-floor is below
    # the ceiling. The per-place claim was false. What the sources DO say is
    # that the worst of it is the heaviest inhabited place on the station.
    informal = [q for q in PLACES if "informal_residence" in q["functions"]]
    check("informal residence exists at all", bool(informal))
    if informal:
        gs = [gravity_of(schema, profile, q) for q in informal]
        formal = [gravity_of(schema, profile, q) for q in PLACES
                  if "residence" in q["functions"]]
        check("the worst informal residence is above the habitable ceiling",
              max(gs) > it.HABITABLE_G_MAX,
              f"heaviest {max(gs):.3f} g vs a {it.HABITABLE_G_MAX} g ceiling")
        check("and it is heavier than any formal residence",
              not formal or max(gs) > max(formal),
              "the people with the least power live where they weigh the most")

    # --- every place does something ----------------------------------------
    for p in PLACES:
        check(f"{p['key']}: has a declared function", bool(p["functions"]),
              "a room with no function is set dressing")
        # A place with no interactions must be one a player cannot enter --
        # hull-mounted systems and sealed structure. Anything else with an
        # empty tuple is a room that cannot be used, which is what this check
        # exists to surface.
        unenterable = {"structure", "sensors", "navigation", "communications",
                       "power_generation", "cooling", "rotation",
                       "sealed_volume"}
        if not (set(p["functions"]) & unenterable):
            check(f"{p['key']}: has something to interact with",
                  bool(p["interacts"]),
                  "the brief asks for locations that can be used")

    # --- every module with geometry is placed ------------------------------
    placed_modules = {p["module"] for p in PLACES if p["module"]}
    for m in ("zocalo", "docking_bay", "command_control", "council_chamber",
              "plant", "customs", "garden", "alien_sector", "quarters",
              "hospitality"):
        check(f"the {m} module has a station address",
              m in placed_modules,
              "it was built in a local frame and placed nowhere")

    # --- the gazetteer is the source, and coverage is countable ------------
    rows = gazetteer_rows()
    check("the gazetteer parses", len(rows) > 100, f"{len(rows)} rows")

    # LAYER 1's EXIT CRITERION: every gazetteer row is addressed or explicitly
    # deferred. No third state. This is what makes 126 a denominator rather
    # than a backlog.
    import difflib
    low = [q["name"].lower() for q in PLACES]
    unresolved = []
    for r in rows:
        if difflib.get_close_matches(r.lower(), low, n=1, cutoff=0.70):
            continue
        if any(difflib.SequenceMatcher(None, r.lower(), k.lower()).ratio() > 0.7
               for k in NOT_A_PLACE):
            continue
        # Aliases match by PREFIX, not by ratio. The gazetteer's row for the
        # unnamed bar carries an 60-character parenthetical, which drags any
        # similarity ratio to 0.64; lowering the threshold to catch it would
        # start matching unrelated rows to each other. A prefix is exact.
        if any(r.lower().startswith(k.lower().rstrip(")( ")) for k in ALIASES):
            continue
        unresolved.append(r)
    check("every gazetteer row is addressed or explicitly deferred",
          not unresolved,
          f"{len(unresolved)} unresolved: {[u[:34] for u in unresolved[:6]]}")
    cov = coverage(schema, profile)
    check("coverage is reported honestly",
          cov["addressed"] + cov["unaddressed"] == cov["gazetteer_rows"])

    # --- layer 4 counts what has been SEEN, not what shares a rig ----------
    # The drum branch of `_lit_keys` counted every drum-scene module because
    # the DRUM had a measured exposure, and that took `garden` -- four
    # locations -- on the strength of a frame its geometry is not in. The drum
    # shot holds ground, two end caps, guideways, spokes, core and trams;
    # `garden.townscape()` is not among them.
    #
    # This pins the distinction rather than the number. It fails if the
    # predicate is re-broadened, and it ALSO fails once garden really does
    # enter a rendered frame -- which is the right time to be made to look at
    # this again, because the fix then is to update the assertion, not the
    # predicate.
    _lit = _lit_keys()
    # THESE TWO CHECKS USED TO NAME THE GARDEN AND THE TRAM and assert they
    # were NOT counted, because at the time each was being credited off a frame
    # it did not appear in -- the garden 0.00% of the wide drum shot, the tram
    # 0.01%. Both were written to fail in two directions: if the predicate were
    # re-broadened, AND once the geometry really did enter a measured frame,
    # "which is the right time to be made to look at this again, because the
    # fix then is to update the assertion, not the predicate."
    #
    # That second direction fired. `DRUM_CALIBRATION` now carries a garden
    # framing measured against `garden.png` -- the frame garden.townscape() was
    # actually built from, which is NOT the 29a I had assumed -- where the
    # townscape is 30.78% of the picture, and a tram framing where the cars are
    # 5.47%. So the specific claims are retired and replaced by the INVARIANT
    # they were two instances of, which is stronger than either: no place is
    # credited at layer 4 off a frame its own geometry is not in.
    import test_materials_layer3 as _gate                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import export_scene as _X                                # noqa: PLC0415
    import test_materials_layer3 as _gate                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import export_scene as _X                                # noqa: PLC0415
    # MY FIRST REPLACEMENT FOR THESE WAS VACUOUS AND THE PROBE CAUGHT IT.
    # It asserted "no module counted as lit has a contribution below the
    # threshold" -- but `_lit_keys` credits a module BY that same threshold on
    # that same table, so the two can never disagree. Zeroing the townscape
    # dropped the count 118 -> 114 and the check never fired, because the
    # module simply stopped being counted. One source of truth cannot
    # cross-check itself, and dressing that up as an assertion is the exact
    # defect this file exists to catch.
    #
    # What IS falsifiable is the MECHANISM: these four places are credited only
    # because `drum_visible_parts` takes the UNION over framings. The wide shot
    # -- the only drum framing that existed this morning -- shows 0.00% of the
    # townscape and 0.01% of the trams, and crediting them off it was the bug.
    # So: assert the wide framing alone would still credit neither. That fails
    # if someone puts a fictitious number in wide's table, and it fails if the
    # union is ever collapsed back to one framing.
    _wide = _X.DRUM_CALIBRATION["wide"]["contribution"]
    _wide_only = {k for k, v in _wide.items()
                  if v >= _X.DRUM_FRAME_MIN_PERCENT}
    check("the wide drum shot alone still credits neither the garden nor the "
          "tram -- crediting them off it was the defect",
          "townscape" not in _wide_only and "trams" not in _wide_only,
          f"wide credits {sorted(_wide_only & {'townscape', 'trams'})}")
    check("...and they ARE credited, by framings that do show them",
          {q["key"] for q in PLACES if q["module"] in ("garden", "tram")}
          <= _lit,
          f"{sorted({q['key'] for q in PLACES if q['module'] in ('garden', 'tram')} - _lit)}")
    _core = {q["key"] for q in PLACES if q["module"] == "core_tube"}
    check("the core tube IS counted -- the drum shot contains it",
          _core and _core <= _lit, f"{sorted(_core - _lit)}")

    # --- the layer model ---------------------------------------------------
    rep = layer_report(schema, profile)
    check("no layer claims more than the gazetteer holds",
          all(r["done"] <= r["total"] for r in rep))
    # Layers are cumulative: each must be <= the one above it. A break here
    # means layer_of() is reporting a non-contiguous layer as reached.
    check("layer completion is monotonically non-increasing",
          all(rep[i]["done"] >= rep[i + 1]["done"]
              for i in range(len(rep) - 1)),
          str([(r["name"], r["done"]) for r in rep]))
    # CLAUDE.md's rule 1: do not start a layer before the one above it is
    # complete. This does not fail the build -- work in progress is normal --
    # but it names which layer is the current one, so a session cannot drift
    # into a later layer without the register saying so.
    current = next((r for r in rep if not r["complete"]), None)
    check("there is a current layer, and it is the earliest incomplete one",
          current is not None and current["layer"] == min(
              r["layer"] for r in rep if not r["complete"]),
          str(current))

    # --- THE LAYER-2 PREDICATE MUST BE ABLE TO SAY "NO" --------------------
    # `module=None` used to mean "unbuilt" and now means "the generator builds
    # it". The lazy way to express that is `module or GENERATOR`, which is True
    # for every row in the table -- a completion counter that cannot go down.
    # This asserts the predicate is a real membership test by handing it a
    # place the generator does not build.
    ghost = _P("__not_a_real_place__", "ghost", "blue", 0, 0, 0.0, 7000.0,
               (1.0, 1.0))
    check("layer 2 says no to a place nothing builds",
          geometry_of(ghost) is None and layer_of(ghost) == 1)
    check("layer 2 says yes to a generated place",
          geometry_of(by_key("fabrication")) == GENERATOR)
    check("layer 2 still credits bespoke modules",
          geometry_of(by_key("cnc")) == "command_control")
    # And the generator's coverage plus the bespoke modules must be the whole
    # table -- if a row falls between them it is at layer 1 and must be seen.
    ungeom = [p["key"] for p in PLACES if not geometry_of(p)]
    check("every addressed place has geometry from somewhere",
          not ungeom, f"{len(ungeom)}: {ungeom[:6]}")

    print(f"\nSTATION DIRECTORY")
    print(f"  gazetteer rows       {cov['gazetteer_rows']:4d}")
    print(f"  addressed here       {cov['addressed']:4d}"
          f"  ({cov['addressed'] / cov['gazetteer_rows']:.0%})")
    print(f"  of those, with mesh  {cov['addressed_with_geometry']:4d}")
    print(f"  still unaddressed    {cov['unaddressed']:4d}")
    print()
    for p in sorted(PLACES, key=lambda p: (p["sector"], p["angle_deg"])):
        g = gravity_of(schema, profile, p)
        mark = "mesh" if p["module"] else "    "
        print(f"  {mark} {p['sector']:6s} r{p['ring']}d{p['deck']:<3d} "
              f"{p['angle_deg']:5.0f}deg z{p['z_m']:6.0f} {g:5.3f}g  "
              f"{p['name'][:38]:38s} {len(p['interacts'])} interactions")
    print(f"\n  LAYER COMPLETION across {rep[0]['total']} places "
          f"({rep[0]['gazetteer_rows']} gazetteer rows less "
          f"{rep[0]['deferred']} that are not locations)")
    for r in rep:
        bar = "#" * int(20 * r["done"] / max(r["total"], 1))
        flag = ("  <- CURRENT" if r is current
                else "  COMPLETE" if r["complete"] else "")
        print(f"    {r['layer']} {r['name']:12s} [{bar:20s}] "
              f"{r['done']:3d}/{r['total']}{flag}")
    print("\n  Layer 0 (engine path) is infrastructure and is DONE: Godot 4.4 "
          "double +\n  lavapipe renders exterior and interior offscreen, and "
          "four frames are scored\n  in docs/aaa-scorecard.json. The craft "
          "layers can now be checked as well as built.")

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
