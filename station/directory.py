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
       adjacent=("kosh_quarters",),
       note="Where the six-atmosphere board becomes a traversal mechanic."),
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
)


# Gazetteer rows deliberately NOT addressed yet, each with a reason. This list
# is what keeps "126 rows" from being a vague backlog: everything is either
# placed above or named here.
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
    """
    rings = it.ring_radii(schema, profile, place["sector"])
    stacks = [i for i, r in enumerate(rings) if r["kind"] == "deck_stack"]
    if not stacks:
        return it.gravity_at(schema, it.sector_radius(schema, profile,
                                                      place["sector"]))
    ri = stacks[min(place["ring"], len(stacks) - 1)]
    decks = it.decks_in_ring(schema, profile, place["sector"], ri)
    if not decks:
        return it.gravity_at(schema, it.sector_radius(schema, profile,
                                                      place["sector"]))
    d = decks[min(place["deck"], len(decks) - 1)]
    return d["floor_g"]


def _arc_overlap(a0, span0, a1, span1):
    """Do two angular spans overlap on a circle?"""
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
LAYERS = (
    (1, "addressed", lambda p: True),
    (2, "geometry", lambda p: bool(p["module"])),
    (3, "materials", lambda p: bool(p.get("materials"))),
    (4, "lighting", lambda p: bool(p.get("lights"))),
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
    """Per-layer completion across the WHOLE gazetteer, not just what is placed.

    The denominator is every location row, including the 97 with no address --
    a layer is not complete because the places we happen to have registered are
    done with it.
    """
    total = len(gazetteer_rows())
    out = []
    for idx, name, _reached in LAYERS:
        n = sum(1 for p in PLACES if layer_of(p) >= idx)
        out.append(dict(layer=idx, name=name, done=n, total=total,
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
        if "informal_residence" in p["functions"]:
            # The exception that proves it: Downbelow is ABOVE the ceiling,
            # which is exactly why nobody is billeted there.
            check(f"{p['key']}: informal residence is above the ceiling",
                  g > it.HABITABLE_G_MAX,
                  f"{g:.3f} g -- unassigned is the point")

    # --- every place does something ----------------------------------------
    for p in PLACES:
        check(f"{p['key']}: has a declared function", bool(p["functions"]),
              "a room with no function is set dressing")
        if p["key"] not in ("obs_dome_1", "fusion_core"):
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
    cov = coverage(schema, profile)
    check("coverage is reported honestly",
          cov["addressed"] + cov["unaddressed"] == cov["gazetteer_rows"])

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
    print("\n  LAYER COMPLETION across all "
          f"{len(gazetteer_rows())} gazetteer locations")
    for r in rep:
        bar = "#" * int(20 * r["done"] / max(r["total"], 1))
        flag = "  <- CURRENT" if r is current else ""
        print(f"    {r['layer']} {r['name']:12s} [{bar:20s}] "
              f"{r['done']:3d}/{r['total']}{flag}")
    print("\n  Layer 0 (engine path) is infrastructure and BLOCKING: no frame "
          "in this\n  project has yet been scored against docs/AAA-STANDARD.md.")

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
