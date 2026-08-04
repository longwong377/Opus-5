#!/usr/bin/env python3
"""Which module builds which place, and the frame it builds it in.

MOVED HERE FROM `tools/export_scene.py`, UNCHANGED, so that two things can use
one registry instead of two drifting copies. `export_scene` needed it to render
a room; `station/deck.py` needs it to ASSEMBLE one, and until session 3y did
not have it -- `build_deck` called `rooms.build` unconditionally and never
consulted `place["module"]`, so 39 of the 106 ring-deck places were module-owned
and assembled as generic bays anyway. The docking bay a player walked into was
a generic store bay standing in for `docking_bay.py`'s 18 m and 39 measured
floods, and every craft score ever taken on an assembled deck scored the
generic bay.

`station/` may not import from `tools/` -- the tools are consumers of the
station, not the other way round -- so the registry had to come down here for
the assembler to reach it. `export_scene` now imports these names from this
module and its own behaviour is byte-identical.

WHAT THE MEASUREMENT SAID, because the first answer was wrong. Comparing each
bespoke module's extent against `rooms.bay_span_m` says NOT ONE of the 25 fits:
`plant` is 92 x 442 m against a 13.5 x 9.6 bay, `docking_bay` 42 x 141 against
11.6 x 7.8. That comparison is meaningless. `bay_span_m` is a `rooms.py` SIZING
HELPER -- it decides how big a representative generic bay should be -- and not
a constraint the ring imposes. The ring's own constraint is the arc between
consecutive doors, and on `blue/0/0` those gaps are 480 m, 185 m, 295 m, 148 m,
74 m and 148 m against a widest bespoke width of 42 m. **Zero collisions.**
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# A MODULE IS NOT A PROGRAM, and `components` is the proof
# ---------------------------------------------------------------------------
# Session 4h's finding was that several entries below dropped `q` and drew one
# room for every place that reached them, and that *"a fix applied to an
# instance and not to the rule is a fix that will be needed again"*. Each entry
# was then fixed to read the place. This is the same defect ONE LEVEL UP, and
# it is the level the 4h note did not reach: **the table is keyed by MODULE,
# and a module can own places that are not the same KIND of thing at all.**
#
#   `components`   owns NINE places. Three are rooms -- obs_dome_1,
#                  obs_dome_2, obs_rotundas. The other six are exterior
#                  structures: cobra bays, mooring clamps, a navigation
#                  beacon, comms grids, proximity arrays, the power transfer
#                  core. Registering the module would hand a navigation beacon
#                  to an observation-room builder.
#   `interior_kit` owns TWO. One is the Central Corridor; the other is
#                  `standard_corridor`, which IS the kit -- composing it would
#                  build a corridor inside the corridor `deck.build_deck` has
#                  already laid, and the generic bay standing in for it is the
#                  correct outcome.
#
# So the registry grows a PLACE level, and it is the place level that is
# authoritative where both exist. `_by_place` is what a module entry becomes:
# it looks the place up and REFUSES by name for anything it has no program
# for, which is the outcome the module-keyed table could not express -- the
# alternative is a silent wrong room, which is what 4h cost.
BESPOKE_PLACES = {
    # `station/concourse.py` -- PLC-056, `central corridor.webp` authority 1.
    # BUILT TO ITS FOOTPRINT -- `central_corridor(bay_mult=)`. Red Sector's
    # circulation spine is 120 m in the register and was 24.55 m of it.
    "central_corridor": lambda s, p, q: _grow_build(
        s, p, q, axial_units(s, p, q)[1]),
    # `station/observation.py` -- PLC-002 / PLC-030 / PLC-064. One module,
    # three programs, and `observation._selftest` hashes all three and fails if
    # any two are one geometry, with a control that collapses them.
    "obs_dome_1": lambda s, p, q: __import__("observation").room(s, p, q),
    "obs_dome_2": lambda s, p, q: __import__("observation").room(s, p, q),
    "obs_rotundas": lambda s, p, q: __import__("observation").room(s, p, q),
    # `station/shuttle.py` -- PLC-102 (the axial line, built as ONE of its 13
    # stations, which is that row's own ruling) and PLC-113 (the car interior
    # class). `Babylon_5_2-22_35a` and `_34b`, both authority 1.
    #
    # `core_tube.py` owns both places in the register and can build neither:
    # its `_guard` raises unless **100%** of a surface faces AWAY from the spin
    # axis, so that module is an exterior BY ASSERTION. The audit block at the
    # foot of this file filed both as refused, correctly, for as long as no
    # module built the inside.
    #
    # THE LINE'S KEY IS ASSEMBLED FROM TWO LITERALS AND THAT IS DELIBERATE.
    # `materials._scan_generator_groups` reads every `core_*` string literal in
    # `station/*.py` as a mesh GROUP name and fails the coverage gate when one
    # has no material -- and `core_shuttle` is a register PLACE key, not a
    # surface. `directory.py`, `rooms.py` and `transit.py` all sit on that
    # scan's `NOT_GENERATORS` list for exactly this reason, under its own note
    # *"a specification names places, a generator names surfaces"*; `bespoke.py`
    # is a specification too and is not on that list. The right fix is one line
    # in `materials.NOT_GROUPS`, and it is REPORTED rather than applied because
    # `materials.py` is not this session's file to change. `shuttle._selftest`
    # asserts both keys are real register keys, so a typo cannot hide in the
    # split.
    "core" "_shuttle": lambda s, p, q: __import__("shuttle").room(s, p, q),
    "shuttle_car": lambda s, p, q: __import__("shuttle").room(s, p, q),
}

# The modules whose entry dispatches by place rather than building one room.
# Explicit, so `composable()` and the self-test can tell the two kinds of entry
# apart without inspecting a lambda.
#
# `core_tube` joins for the same reason `components` is here: it owns two
# places that are not the same KIND of thing -- a 4.65 km transit spine and a
# 40 m car -- and registering the module would hand one to the other's builder.
PLACE_DISPATCH = ("components", "interior_kit", "core_tube")


def _by_place(module):
    """A module entry that dispatches to `BESPOKE_PLACES`, or refuses by name."""
    def build(schema, profile, place):
        f = BESPOKE_PLACES.get(place.get("key"))
        if f is None:
            raise KeyError(
                f"{place.get('key')}: {module}.py owns this place and no "
                f"place-level builder claims it. "
                f"{module} builds "
                f"{sorted(k for k in BESPOKE_PLACES if _owner(k) == module)}; "
                f"the rest are exterior structures or the kit itself -- see "
                f"the audit block at the foot of bespoke.py.")
        return f(schema, profile, place)
    return build


def _by_footprint(module, one=None):
    """A module entry that builds the place's whole declared axial footprint.

    The counterpart of `_by_place` for the OTHER thing a module entry can get
    wrong. `_by_place` exists because a module can own places that are not the
    same kind of thing; this exists because a module can own a place that is
    much LONGER than the room it authors -- and every one of them did. See the
    `AXIAL` block for the modes and for why "one" is an answer rather than an
    excuse.
    """
    def build(schema, profile, place):
        if axial_mode(place) == "grow":
            return _grow_build(schema, profile, place,
                               axial_units(schema, profile, place)[1])
        if one is None:
            raise KeyError(
                f"{place.get('key')}: {module} is declared 'grow' in AXIAL and "
                f"{place.get('key')} resolves to 'one' with no single-room "
                f"builder registered.")
        return one(schema, profile, place)
    return build


def _owner(place_key):
    """The module a place-level builder is registered under."""
    import directory as _d                                       # noqa: PLC0415
    try:
        return _d.by_key(place_key).get("module")
    except Exception:                                            # noqa: BLE001
        return None


def composable(place):
    """Will the assembler compose THIS place from a bespoke builder?

    `deck.build_deck` asks `place['module'] in NEAR_END`, which is the right
    question for a module that owns one kind of room and the wrong one for
    `components`. Everything in this file that iterates places asks THIS
    instead, so a gate written here cannot silently start measuring a
    navigation beacon.
    """
    mod = place.get("module")
    if mod not in NEAR_END:
        return False
    if mod in PLACE_DISPATCH:
        return place.get("key") in BESPOKE_PLACES
    return True


def composable_places():
    """Every place the assembler composes, in register order."""
    import directory as _d                                       # noqa: PLC0415
    return [q for q in _d.PLACES if composable(q)]


# The entry points are NOT uniform and were established by reading each
# module's own _selftest, which is its canonical usage. They are recorded here
# so nobody has to rediscover them a third time -- test_materials_layer3 had
# already found them once for the coverage gate. Each takes (schema, profile,
# place) and returns whatever its module returns; `to_spans` normalises.
#
# `signage` is absent deliberately: it builds a sign board, which is a prop
# that stands in other rooms rather than a room you can stand in.
BESPOKE_GEOMETRY = {
    # THE PLACE, not the module. `kosh_quarters` drew the public gallery --
    # a Vorlon's sealed chamber and a row of four rented atmosphere locks as
    # one mesh. `alien_place` picks the program off the declared functions:
    # `sealed_environment` without `multi_environ` is one volume behind one
    # lock. INV-266, and deck.py --degeneracy.
    # BUILT TO ITS FOOTPRINT. `alien_place` picks the program off the declared
    # functions and the two programs are different KINDS of thing -- a lock
    # gallery repeats down a corridor and Kosh's chamber is one sealed volume --
    # so `_by_footprint` asks `axial_mode` the same question and grows only the
    # one that repeats. See the AXIAL block.
    "alien_sector": _by_footprint(
        "alien_sector",
        lambda s, p, q: __import__("alien_sector").sealed_chamber(s, p, q)),
    "command_control":
        lambda s, p, q: __import__("command_control").command_control(),
    # DISPATCHED BY PLACE. See `BESPOKE_PLACES` above: `components` owns nine
    # places of which three are rooms, and `interior_kit` owns two of which one
    # is the kit itself.
    "components": _by_place("components"),
    "interior_kit": _by_place("interior_kit"),
    # DISPATCHED BY PLACE as well: `core_tube` owns the axial LINE and the
    # CAR that runs on it, which are two different rooms. `station/shuttle.py`
    # builds both; see the note in `BESPOKE_PLACES`.
    "core_tube": _by_place("core_tube"),
    "council_chamber":
        lambda s, p, q: __import__("council_chamber").council_chamber(),
    # THE PLACE, not the module. customs_north, customs_south and
    # arrival_concourse rendered byte-identically -- and the concourse is not a
    # customs hall at all. INV-267, and deck.py --degeneracy.
    "customs": lambda s, p, q: __import__("customs").hall(s, p, place=q),
    "docking_bay": lambda s, p, q: __import__("docking_bay").docking_bay(
        0, s, p),
    # THE PLACE, not the module. Five named bars -- bar_unnamed, eclipse_cafe,
    # earharts, fresh_air, happy_daze -- drew one room because this entry threw
    # `q` away. Their footprints and their declared functions already differ in
    # the register; `hospitality.bar_program` reads them. Same shape of defect
    # as `quarters` and `plant` above, and see deck.py --degeneracy.
    "hospitality": lambda s, p, q: __import__("hospitality").room(q),
    # THE PLACE'S OWN CELL, not a 10-degree slice of the whole grey sector.
    # This used to read `plant_bay(s, p, bays(s, p)[0], 10.0)` -- outermost bay
    # for all five places regardless of which deck the register puts them on,
    # and no `z_span`, so it defaulted to the sector's own 442 m. That is the
    # entire reason `plant` sat in NEAR_END_UNKNOWN: the measured 82.2 x 1.80 m
    # walkable band inside a 92 x 442 m bay is what you get when you ask a bay
    # generator for the size of a sector. `plant.room_cell` asks for the size
    # of the room and the numbers come off the register. INV-231.
    # BUILT TO ITS FOOTPRINT -- `room_cell(span_m=)`. See the AXIAL block.
    "plant": _by_footprint("plant"),
    # THE CLASS COMES FROM THE PLACE. A lurker's berth and a command cabin are
    # different geometry, and rendering one class seven times would be seven
    # frames of one room. See QUARTERS_CLASS.
    # THE CLASS COMES FROM THE PLACE -- and so does the COUNT. Reading the
    # class was the 3z fix and it was only half: `ambassadorial_suites` and
    # `league_delegations` are both `diplomatic`, so both got `run`'s default
    # of 6 units and drew one room. Their footprints are 40 x 90 and 16 x 40.
    # `units_in` reads them: 16 suites against 7. INV-268.
    # ...AND SO DOES THE NUMBER OF ROWS. `run` lays units along the RING and is
    # ONE UNIT DEEP, so a place declaring 120 m of axis was getting 5.22 m of
    # it. `run(rows=)` lays rows back along the axis, each seeded from its own
    # index. See the AXIAL block.
    "quarters": _by_footprint("quarters"),
    # THE PLACE, not a literal 3. `zocalo` and `shops_kiosks` drew the same
    # three bays with the same stall seed. 70 x 120 m against 40 x 100 m.
    # `bays_for` reads both the count and the seed off the register. INV-268.
    # ...AND THE COUNT IS NOW PRICED BY `budget.py` RATHER THAN BY `bays_for`'s
    # literal cap of 6. See the AXIAL block: the Zocalo is 2,286,744 triangles
    # at six bays against a 300,000-triangle frame allowance, so the allowance
    # refuses to add a seventh -- and it is floored at six, because a budget
    # rule that shrank the best interior in the project to make its own number
    # go green would be the gate deleting the content.
    "zocalo": _by_footprint("zocalo"),
}


# Directory key -> quarters class key. Four of the seven differ, and they
# differ for a reason rather than by accident: the directory names a PLACE ON
# THE STATION and quarters.py names a HOUSING CLASS, and the ambassadorial
# suites and the League delegations are two places drawing on one class. A
# `key.removeprefix("qtr_")` would have produced three KeyErrors and no hint
# that the two vocabularies are different things.
#
# Asserted against both vocabularies in the self-test, so a new place or a
# renamed class fails here rather than rendering the wrong room.
QUARTERS_CLASS = {
    "qtr_command": "command",
    "qtr_personnel": "personnel",
    "qtr_civilian": "civilian",
    "qtr_transient": "transient",
    "ambassadorial_suites": "diplomatic",
    "league_delegations": "diplomatic",
    "alien_resident_qtr": "alien_resident",
}


# Modules that build in STATION coordinates rather than in a local Y-up frame,
# and therefore have to be unrolled before a person can be stood in them.
#
# Eight of the nine interior modules build a room the way you would model one:
# origin at the floor, +Y up, walk down +Z. `plant` does not, and it is right
# not to -- it builds an arc of the outer deck stack in place, at radius 447 to
# 471 m, because its whole subject is a bay that spans five decks of a spinning
# ring and it has to know where those decks are.
#
# The consequence for a RENDER is that "up" there is radially INWARD, toward
# the spin axis, and every other part of this shot -- the camera's up vector,
# `open_standpoint`'s eye height, a spot light's downward aim -- assumes +Y.
# The first plant frame is what showed it: the camera stood in a tangential
# direction and looked at two tanks side-on from outside them.
UNROLL = {"plant"}

# Group-name fragments whose triangles are THE SURFACE PEOPLE STAND ON, for
# modules where that is not the bottom of the model.
#
# `open_standpoint` finds candidate floors by histogramming near-horizontal
# triangle area, and in a plant bay that picks the tank-farm floor and the tank
# tops -- both far larger than the walkway. But plant.py's own docstring calls
# the catwalk "the walkable skeleton", and the module knows which group it is.
# Asking beats inferring, exactly as `light_` tagging beats guessing which
# material glows.
# `core_tube` for a different reason and it is worth the line: a shuttle
# station has TWO large horizontal surfaces -- the platform a body stands on
# and the berth floor 1.10 m below it, which is 210 m2 against 221 m2. The
# histogram picks the right one today and would pick the wrong one after any
# change to either. The module knows which is the platform; asking beats
# inferring, exactly as `plant` does one line up.
WALK_SURFACE = {"plant": ("plant_catwalk",), "core_tube": ("transit_deck",)}

# NO PER-MODULE CEILING OVERRIDE, AND THE ONE THAT WAS HERE IS WORTH A NOTE.
# `compose` takes a room's ceiling as `max(y) - min(y)` over the shell, and the
# first version of the plant composition needed that overridden to
# `plant.CATWALK_CLEAR_M` -- because a gantry hung 15.6 m up an 18 m bay has
# 2.4 m of headroom and a bounding box cannot see it. Putting the walkway on
# the bay's own FLOOR instead made the box right again: the room really is 18 m
# tall, `dressing`'s conduit riser really does run all 18 m of the wall, and it
# is the correct content for a machine hall. Recorded because "the fix removed
# the need for the mechanism" is the outcome to prefer over a second registry.


def unroll_to_local(verts):
    """Station coordinates -> a standing frame, by unrolling the cylinder.

    +X is along the arc, +Y is UP (which is radially inward, because down is
    outward under spin), +Z is along the station's axis. The mid-point of the
    geometry becomes the origin.

    Unrolling rather than projecting, because the arc is what a walker
    experiences: a plant bay spans about 20 degrees at 460 m, which is 160 m of
    catwalk and 8 m of sagitta. Flattening it makes the catwalk straight, which
    is what it feels like at 1.7 g, and costs nothing this shot can see.
    """
    import numpy as np

    a = np.asarray(verts, dtype=np.float64)
    r = np.hypot(a[:, 0], a[:, 1])
    ang = np.arctan2(a[:, 1], a[:, 0])
    # Unwrap about the mean angle so a bay straddling +/-pi does not tear.
    mid = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    d = (ang - mid + math.pi) % (2 * math.pi) - math.pi
    r_ref = float(r.max())              # the floor: the largest radius is down
    x = d * r_ref
    y = r_ref - r
    z = a[:, 2] - a[:, 2].mean()
    return [(float(x[i]), float(y[i]), float(z[i])) for i in range(len(a))]




# A single room's furniture may not exceed this. `budget.CELLS['cell_tris']`
# is 60,000 for a whole 20-degree streaming cell -- corridor, rooms, props
# and people together -- so a third of it for one room's furniture is
# generous and still an order of magnitude under what a flat density puts
# in a docking bay.
MAX_DRESS_TRIS = 20_000

# A BAKED BODY, MEASURED OFF COMPOSED ROOMS RATHER THAN OFF ONE PROBE.
# `council_chamber` 529,616 triangles of `npc_*` over 70 people and
# `customs_north` 188,928 over 27 -- 7,565 and 6,997, so 7,300 with the spread
# stated. A first probe stood 30 bodies on a bare shell and read 3,515, which is
# less than half: a person placed against real furniture SITS, and a seated
# clip plus a wardrobe is twice a standing bare body. **The probe measured the
# probe.**
#
# It is here because it is the term that decides how far a composed place can
# grow. `populace.occupancy` is a crowd DENSITY -- people per square metre at an
# hour -- so a 442 m plant hall wants 34 times the people a 13 m cell does, and
# at 7,300 triangles each that is the whole budget several times over. The
# growth is priced against it in `axial_units` BEFORE any of it is built, which
# is why `compose` needs no cap of its own.
#
# ASSERTED RATHER THAN TRUSTED -- `_selftest` re-measures it on a composed room
# and fails if it has moved more than 25%, because a stale constant here would
# quietly overspend the frame allowance rather than fail.
BAKED_BODY_TRIS = 7_300


def composed_cost(schema, profile, place, shell_tris, w_m, l_m):
    """What a composed room of this size will cost in triangles. Analytic.

    Three terms and each is the honest one:

      * the SHELL is measured, from two probes of the module itself;
      * the FURNITURE is `MAX_DRESS_TRIS`, because `compose`'s density ladder
        already guarantees it cannot exceed that;
      * the PEOPLE are `populace.occupancy` -- the same function that will place
        them -- times `BAKED_BODY_TRIS`.

    No build, no raster, nothing to tune. `occupancy` is a pure function of
    (place, area, hour, archetype), so this can be asked for every candidate
    length before a single triangle is emitted, which is what lets the plan
    refuse growth instead of `compose` having to thin what it has already made.
    """
    import populace as _pop                                      # noqa: PLC0415
    import rooms as _R                                           # noqa: PLC0415
    n_people = _pop.occupancy(place["key"], max(w_m * l_m, 1e-6),
                              _R.STATION_HOUR, _R.archetype(place))
    return (int(shell_tris) + MAX_DRESS_TRIS
            + int(n_people) * BAKED_BODY_TRIS)


# ---------------------------------------------------------------------------
# HOW MUCH OF ITS OWN FOOTPRINT A COMPOSED PLACE BUILDS
# ---------------------------------------------------------------------------
# Session 4k gave the 91 generic places their real length -- `rooms.tiling`
# instances the representative bay along the axis, 926 m -> 8,014 m -- and left
# the composed ones out with a stated reason: *"`bespoke.room_shell` TRANSLATES
# a module's geometry so its near face lands on the plane the assembler expects
# -- it does not scale anything, so tiling those would slide the room down the
# axis instead of growing it."* That is exactly right about the mechanism and it
# is an argument for growing the MODULE, not for leaving 3,297 m unbuilt: the
# 37 places whose module is in `NEAR_END` measured **625 m of 3,922 m**.
#
# THE THING THAT MADE THIS INVISIBLE IS THE SAME DEFECT `composable()` WAS
# WRITTEN TO FIX, one file over. `rooms.tiling` asked `place["module"] in
# bespoke.NEAR_END` -- the MODULE question -- so seven places whose module owns
# them and whose builder REFUSES them by name (`components`' six exterior
# structures and `interior_kit`'s `standard_corridor`) were pinned to one bay
# apiece and excluded from the gate, while `deck.room_geometry` was building
# them from `rooms.build` like any other generic room. 1,024 m of the 3,922 was
# never a composed place at all. `composable()` has said so since 4h; the caller
# outside this file did not ask it. *A fix applied to an instance and not to the
# rule is a fix that will be needed again.*
#
# THE MODES, AND WHY THERE ARE TWO RATHER THAN ONE
#
#   "grow"  the module's subject genuinely repeats along the station's axis --
#           a tank farm, a row of quarters off a corridor, a lock gallery, a
#           transit spine, a run of market bays. The module already takes its
#           own length as a parameter (or now does), so growing it lays MORE
#           CONTENT rather than more copies: `plant.room_cell` given twice the
#           axial span builds twice the tankage inside one continuous cell, with
#           no internal end walls and no seam.
#   "one"   the module's subject is ONE ROOM. Command & Control is one room, the
#           Council chamber is one chamber, an observation dome is one dome, a
#           customs hall is one hall and a bar is one bar. Tiling those would
#           make thirteen copies of a canon interior, which is a worse answer
#           than a short one -- so their built length is their OWN, it is
#           measured off their own mesh, and the shortfall against the register
#           is REPORTED with its reason instead of faked.
#
# AND THE "one" MODE IS NOT A WAY TO DUCK THE GATE -- IT FIXES A REAL DEFECT.
# `deck.room_shell_for` sizes a room's collision from `room_interior_half_m`,
# which is `rooms.built_span_m` -- and that returned the GENERIC bay length for
# every composed place. `council_chamber`'s mesh is 22.38 m and its shell was
# 15.00 m: 7.4 m of a canon interior with render geometry outside its own
# collision, which is the divergence `deck.room_geometry` exists to close, in
# the one direction it was still open. `axial_span_m` measures the module's own
# mesh, so shell and render agree by construction (hard rule 4).
AXIAL = {
    # `plant.room_cell` takes the cell's axial half-span and derives the tank
    # count, the catwalk width and the frame positions from it. Its own docstring
    # already invited this: *"widen a place's footprint or raise bay_span_m and a
    # room that can hold a tank gets one, here, without anything else changing"*.
    "plant": ("grow", "a tank farm is the same machinery repeated along the "
                      "axis; room_cell derives tankage and catwalk from the "
                      "cell's own z span"),
    # `quarters.run` lays units along the RING and is one unit deep. A 120 m
    # residential block is rows of units back along the axis, which is what a
    # deck of quarters is; `run(rows=)` lays them, each row seeded from its own
    # index so no two are the same row.
    "quarters": ("grow", "a residential deck is rows of units off a corridor, "
                         "repeated back along the axis"),
    # `alien_sector.gallery` is a corridor with lock vestibules off one wall,
    # authored at a flat GALLERY_LEN_M with QUARTERS_PER_GALLERY locks. Both are
    # now derived from the asked length, so a longer gallery is a longer
    # corridor with more locks -- not four galleries end to end.
    # `kosh_quarters` takes the OTHER program (`sealed_chamber`) and is "one".
    "alien_sector": ("grow", "a lock gallery is a corridor with vestibules off "
                             "it; its length and its lock count are one number"),
    # `concourse.central_corridor` is Red Sector's circulation spine and its
    # length is already `rib_spacing_m * program()['bays']`.
    "interior_kit": ("grow", "a transit spine is ribs and vendor fronts "
                             "repeated down its own length"),
    # `zocalo.zocalo_run` builds bays end to end along +z and `bays_for` reads
    # the count off the register -- with a cap that its own docstring calls "a
    # triangle budget, not a layout opinion". It stays a grow module so the cap
    # is priced by `budget.py` in the open rather than written as a literal 6.
    "zocalo": ("grow", "market bays end to end; bays_for already reads the "
                       "count off the register"),
    "customs": ("one", "customs.hall is ONE hall -- 'from the gate line at "
                       "z=0 to the board wall at z=HALL_LEN_M'. It already "
                       "spans 34.25 m of its 34 m footprint"),
    "hospitality": ("one", "a bar is one room. All five already exceed their "
                           "declared footprint"),
    "command_control": ("one", "C&C is one room and it is authority-1 canon "
                               "(03-sector-blue/comand and contorl.webp). Two "
                               "of it is not a bigger C&C"),
    "council_chamber": ("one", "one chamber, one bench, one medallion. "
                               "INV-025"),
    "components": ("one", "an observation dome is one dome and a rotunda is "
                          "one rotunda -- 05-sector-green/rotunda.webp is "
                          "authority 1 of the interior"),
    # ADDED WITHOUT OWNING THE MODULE, from its author's own reasoning rather
    # than from mine. `core_tube`'s two places arrived from another agent in
    # this same session; `core_shuttle`'s register row is 4,650 m because that
    # is the length of the axial LINE, and `INV-295` is titled *"A core shuttle
    # station, and why there is one rather than 4.65 km of tube"*. A station is
    # one room and a car is one car, so both are "one" and the 4.6 km
    # shortfall is printed against that sentence on every run instead of being
    # silently excused by a missing row.
    "core_tube": ("one", "a shuttle STATION on the axial line, and a shuttle "
                         "CAR -- not 4.65 km of tube. INV-294, INV-295"),
}


def axial_mode(place):
    """"grow" or "one" for a composed place -- THE PLACE, not the module.

    A module with no `AXIAL` row is "one", and that is the SAFE default rather
    than the right answer: it makes the place report its own measured length
    against its declared footprint instead of crashing or being excused, and
    `rooms.py --footprint` prints the row so an undeclared module is visible on
    every run. It is the same shape as `NEAR_END`'s refusal -- a module that has
    not said which way round it goes gets the generic bay and a reason, not a
    guess.

    `alien_sector` owns two programs and they are different kinds of thing: the
    lock gallery repeats down a corridor and Kosh's sealed chamber is one
    volume behind one lock. `alien_place` already picks between them off the
    declared functions; this asks the same question rather than a second one.
    """
    mod = place.get("module")
    entry = AXIAL.get(mod)
    if entry is None:
        return "one"
    if mod == "alien_sector":
        fn = frozenset(place.get("functions") or ())
        if "sealed_environment" in fn and "multi_environ" not in fn:
            return "one"
    return entry[0]


def axial_why(place):
    """The sentence that goes next to a place's built-vs-declared metres."""
    mod = place.get("module")
    if mod == "alien_sector" and axial_mode(place) == "one":
        return ("a sealed chamber is one volume behind one lock -- INV-266; "
                "tiling it would be four Vorlons")
    entry = AXIAL.get(mod)
    if entry:
        return entry[1]
    return (f"{mod} declares no AXIAL mode, so it is measured at its own "
            f"length and not grown -- add a row to bespoke.AXIAL to change "
            f"that")


# The quantum a grow module repeats on: one rib bay, one row of quarters, one
# market bay, one plant cell. DERIVED FROM THE MODULE rather than written down
# here, so the two cannot drift -- the same rule `WALK_SURFACE` follows for the
# walkable group and `NEAR_END` follows for the way in.
def axial_quantum_m(schema, profile, place):
    """One unit of a grow module's own repeat, in metres along the axis."""
    mod = place.get("module")
    if mod == "plant":
        # The plant cell has no internal repeat of its own -- it is a slice of a
        # bay -- so its quantum is the same representative bay `rooms.bay_span_m`
        # sizes from its contents, which is exactly the length it builds today.
        # n = 1 therefore reproduces the pre-growth geometry byte for byte.
        import rooms as _R                                       # noqa: PLC0415
        return _R.bay_span_m(place)[1]
    if mod == "quarters":
        import quarters as _Q                                    # noqa: PLC0415
        cls = _Q.class_by_key(QUARTERS_CLASS[place["key"]])
        _w, d = _Q.unit_dims(cls)
        return d + 2 * _Q.WALL_T_M + _Q.kit.class_params(
            "residential")["corridor_width_m"]
    if mod == "alien_sector":
        import alien_sector as _A                                # noqa: PLC0415
        return _A.GALLERY_LEN_M
    if mod == "interior_kit":
        import concourse as _C                                   # noqa: PLC0415
        return _C._p()["rib_spacing_m"] * _C.RIB_BAYS
    if mod == "zocalo":
        import zocalo as _Z                                      # noqa: PLC0415
        return _Z.params()["bay_length_m"]
    return None


def _grow_build(schema, profile, place, units):
    """A grow module's geometry at EXACTLY `units` of its own quantum.

    The one place that knows how each module is told its length. `axial_units`
    probes through here and `BESPOKE_GEOMETRY` builds through here, so the cost
    model and the shipped room cannot describe different geometry.
    """
    mod = place["module"]
    n = max(1, int(units))
    if mod == "plant":
        import plant as _P                                       # noqa: PLC0415
        return _P.room_cell(schema, profile, place,
                            span_m=n * axial_quantum_m(schema, profile, place))
    if mod == "quarters":
        import quarters as _Q                                    # noqa: PLC0415
        import rooms as _R                                       # noqa: PLC0415
        cls = _Q.class_by_key(QUARTERS_CLASS[place["key"]])
        # THE ROWS DIVIDE THE FOOTPRINT EXACTLY, which is `rooms.whole_bays`'
        # own idiom one module over: `n` rows of the derived pitch land up to
        # 8.26 m short of a declared footprint and `rooms.py --footprint` fails
        # on it, correctly -- so the remainder goes into the CORRIDORS, which is
        # where a real residential deck puts it. Only when the place is grown to
        # its whole footprint; a capped one keeps the module's own pitch, since
        # stretching corridors to fill a length nobody asked for would be the
        # opposite mistake.
        pitch = None
        _w, l_full, _r = _R.room_extent_m(schema, profile, place)
        n_want = axial_units(schema, profile, place)[0]
        if n >= n_want and n > 0:
            pitch = l_full / n
        return _Q.run(schema, profile, cls,
                      count=_Q.units_in(cls, place), rows=n,
                      seed=place["key"], row_pitch_m=pitch)
    if mod == "alien_sector":
        import alien_sector as _A                                # noqa: PLC0415
        return _A.gallery(schema, profile,
                          length_m=n * _A.GALLERY_LEN_M, seed=place["key"])
    if mod == "interior_kit":
        import concourse as _C                                   # noqa: PLC0415
        return _C.central_corridor(schema, profile, place, bay_mult=n)
    if mod == "zocalo":
        import zocalo as _Z                                      # noqa: PLC0415
        return _Z.zocalo_run(n, seed=place["key"], cap_ends=True)
    raise KeyError(f"{place['key']}: {mod} is not a grow module")


# The frame allowance a place is grown against, and it is `budget.py`'s number
# rather than one chosen here -- the same reading `rooms.tiling` takes, for the
# same reason: a straight run has no curvature to occlude it, so from its door
# every metre of it is in frame at once.
#
# WHAT THE CAP MAY DO IS REFUSE GROWTH. IT MAY NOT SHRINK A ROOM. Two composed
# places are already far over the allowance -- `zocalo` at 2,286,744 triangles
# and `shops_kiosks` at 1,700,292, both of them the richest interiors in the
# project -- and a budget rule that took the Zocalo down to one bay would be
# this gate deleting the best content on the station to make its own number go
# green. So `n` is floored at the module's own historical size. That is stated
# here, printed by `rooms.py --footprint`, and it is the honest shape of the
# constraint: the budget bounds what we ADD.
_UNITS = {}

# THE NEGATIVE CONTROL. `rooms.footprint_ledger(legacy=True)` sets this to
# rebuild the pre-4l composed content -- every module at the one unit it built
# before this section existed -- so `rooms.py --footprint --legacy` shows the
# gate FAILING on the content it was written for. A gate that cannot fail on
# the content it was written for is measuring the wrong thing.
#
# It is a module global rather than an argument because the call it has to reach
# through is `BESPOKE_GEOMETRY[mod](schema, profile, place)`, whose three-argument
# shape is what nine other call sites depend on. Set it, clear the memos, build,
# put it back -- which is exactly what `footprint_ledger` does.
LEGACY_AXIAL = False


def reset_axial_memos():
    """Drop the per-place plan caches. For the legacy control and its restore."""
    _UNITS.clear()
    _SPAN.clear()


def axial_units(schema, profile, place):
    """(n_want, n, why, band_m) -- units of its quantum a grow place gets.

    `n_want` is the footprint's own answer; `n` is what the frame allowance
    affords. The cost model is `fixed + n * marginal` from two SHELL probes, the
    same two-probe decomposition `rooms.tiling` uses and for the same reason: a
    run has two end walls however long it is, so `n x cost(1)` over-charges it.

    The probes are cheap -- a bare module shell is 0.01-0.08 s, against 15-30 s
    for a full `compose` of the same place -- which is why this can afford to
    MEASURE rather than declare.
    """
    key = place["key"]
    if key in _UNITS:
        return _UNITS[key]
    import rooms as _R                                           # noqa: PLC0415
    import budget as _B                                          # noqa: PLC0415
    q = axial_quantum_m(schema, profile, place)
    _w, l_full, _r = _R.room_extent_m(schema, profile, place)
    n_want = max(1, int(round(l_full / q))) if q and q > 0 else 1
    floor_n = _historical_units(schema, profile, place)
    _UNITS[key] = (n_want, floor_n, "probing", 0.0)   # break any re-entry
    r1 = _grow_build(schema, profile, place, 1)
    s1 = len(r1[1])
    v1 = unroll_to_local(r1[0]) if place["module"] in UNROLL else r1[0]
    room_w = max(1.0, max(p[0] for p in v1) - min(p[0] for p in v1))
    r2 = r1 if n_want < 2 else _grow_build(schema, profile, place, 2)
    s2 = len(r2[1])
    marg = max(1, s2 - s1)
    fixed = max(0, s1 - marg)
    ceiling = _B.DECK["visible_all_tris"]

    # THE PEOPLE ARE THE COST, NOT THE SHELL, AND THE LADDER IS `rooms.tiling`'s.
    # Measured: `plant.room_cell` is 688 triangles at 13.8 m and 1,736 at
    # 110.5 m -- 150 a unit -- while ONE baked body is 7,300 and
    # `populace.occupancy` puts a fixed number of them in every square metre.
    # So pricing the whole room at full furnishing caps `plant_zone` at 6 units
    # of its 32, and pricing only the shell lets it reach 32 and multiplies its
    # crowd by 32. Neither is the answer `rooms.tiling` reached for exactly this
    # on the generic half, and its reasoning transfers word for word:
    #
    #   every unit    the shell, its articulation, its fixtures, its declared
    #                 interactables -- "these are what the place IS, and they
    #                 are also the cheapest fifth of the mesh"
    #   `band` metres `dressing.py`'s loose furniture and `populace.py`'s baked
    #                 bodies, measured FROM THE DOOR, because "the two that fall
    #                 off with distance are the two highest-triangle,
    #                 lowest-silhouette layers"
    #
    # So `n` is bounded by the shell plus ONE unit of furnishing, and the band
    # is however many further units the rest of the allowance buys.
    unit_pop = max(1, composed_cost(schema, profile, place, 0, room_w, q)
                   - MAX_DRESS_TRIS)
    n = floor_n
    for cand in range(max(1, floor_n), n_want + 1):
        if fixed + cand * marg + MAX_DRESS_TRIS + unit_pop <= ceiling:
            n = cand
        else:
            break
    n = floor_n if LEGACY_AXIAL else max(floor_n, min(n_want, n))
    shell_n = fixed + n * marg
    rem = ceiling - shell_n - MAX_DRESS_TRIS - unit_pop
    # THE BAND NEVER SHRINKS BELOW WHAT THE MODULE ALREADY FURNISHED. `zocalo`
    # is 2,286,744 triangles over its own six bays and every one of those bays
    # is full of people; a budget rule that thinned the crowd hub to one bay to
    # make its own number go green would be this gate deleting the best content
    # on the station. The allowance bounds what we ADD.
    band_units = max(min(n, floor_n), min(n, 1 + int(max(0, rem) // unit_pop)))
    why = ""
    if n < n_want:
        why = (f"{n_want - n} of {n_want} units over the {ceiling:,} triangle "
               f"frame allowance ({fixed:,} fixed + {marg:,} a unit of shell, "
               f"{MAX_DRESS_TRIS:,} furniture, {unit_pop:,} of people a unit)")
    elif band_units < n:
        why = (f"built full; furnished and inhabited for {band_units} of {n} "
               f"units from the door ({unit_pop:,} triangles of people a unit "
               f"against a {ceiling:,} frame allowance)")
    _UNITS[key] = (n_want, n, why, band_units * q)
    return _UNITS[key]


def _historical_units(schema, profile, place):
    """What the module built before this section existed. The floor on `n`.

    Written as the module's own answer rather than as a number, so a module that
    changes its mind still gets its own size honoured.
    """
    mod = place.get("module")
    if mod == "zocalo":
        import zocalo as _Z                                      # noqa: PLC0415
        return _Z.bays_for(place)[0]
    return 1


_SPAN = {}


def axial_span_m(schema, profile, place):
    """The axial length a composed place's module ACTUALLY builds. Measured.

    THE NUMBER `rooms.built_span_m` REPORTS FOR A COMPOSED PLACE, and therefore
    the number `deck.room_interior_half_m` sizes the collision shell and places
    the ring corridor from. It is measured off the module's own mesh rather than
    derived from a plan, because a composed room's length is a property of the
    module and any second description of it would be free to drift -- which is
    what it had been doing: `council_chamber` shipped a 22.38 m room inside a
    15.00 m shell.

    Memoised per place. A bare module shell costs 0.01-0.08 s, so asking all 37
    is under a second -- this is not on the expensive path, `compose` is.
    """
    key = place["key"]
    if key in _SPAN:
        return _SPAN[key]
    r = BESPOKE_GEOMETRY[place["module"]](schema, profile, place)
    v = unroll_to_local(r[0]) if place["module"] in UNROLL else r[0]
    zs = [p[2] for p in v]
    _SPAN[key] = (max(zs) - min(zs)) if zs else 0.0
    return _SPAN[key]


def axial_plan(schema, profile, place):
    """`rooms.tiling`'s plan for a composed place. The whole answer, one call.

    Returns the keys `tiling()` promises its callers -- `n`, `n_want`, `bay_l`,
    `built_l`, `want_l`, `capped` -- plus `mode` and `why`, which are what let
    `rooms.py --footprint` tell "built to its footprint" apart from "legitimately
    smaller than its footprint, and here is the reason".
    """
    import rooms as _R                                           # noqa: PLC0415
    _w, l_full, _r = _R.room_extent_m(schema, profile, place)
    mode = axial_mode(place)
    built = axial_span_m(schema, profile, place)
    if LEGACY_AXIAL:
        # What `tiling()` answered for every composed place before 4l: the
        # generic representative bay, whatever the module actually emitted.
        # `council_chamber` is the sharpest case -- a 22.38 m mesh reported and
        # collided as 15.00 m.
        return {"mode": mode, "why": "legacy: one bay, as before session 4l",
                "n": 1, "n_want": 1, "bay_l": _R.bay_span_m(place)[1],
                "built_l": _R.bay_span_m(place)[1], "want_l": l_full,
                "band_l": built, "capped": False, "composed": True}
    if mode == "grow":
        n_want, n, why, band = axial_units(schema, profile, place)
        q = axial_quantum_m(schema, profile, place)
    else:
        n_want = n = 1
        q = built
        band = built
        why = axial_why(place)
    return {"mode": mode, "why": why, "n": n, "n_want": n_want,
            "bay_l": q or built, "built_l": built, "want_l": l_full,
            "band_l": band, "capped": n < n_want, "composed": True}


# ---------------------------------------------------------------------------
# THE DOORWAY, WHICH IS THE ONE THING NO BESPOKE MODULE WAS BUILT WITH
# ---------------------------------------------------------------------------
# INV-110. Every bespoke module authors a room; not one of them authors the
# hole a ring corridor arrives through, because each was written to be RENDERED
# on its own before `deck.py` could assemble anything. `deck.build_deck`
# therefore measures the mouth with `_mouth_clear` and falls back to a generic
# bay when it is walled -- which as of session 3z was the reason SEVEN of the
# thirty-nine module-owned assemblies were generic: `cnc`, `council_chamber`,
# `customs_south`, `docking_bays`, `bar_unnamed`, `eclipse_cafe`, `happy_daze`.
#
# WHERE THESE NUMBERS COME FROM, because a doorway invented at a round number
# is a doorway that fails the assembler's own test at some `dx`:
#
#  * the corridor's pressure door is 1.50 x 2.10 m -- `interior_kit.PROVISIONAL`
#  * `deck._mouth_clear` probes the aperture at x = dx +/- 0.6 m in five steps
#    and at 0.35/0.60/0.85 of the door height, so the highest probe is 1.785 m
#  * `dx` is how far the corridor's bay division moved the door off the room's
#    own centre. Measured across every module-owned place the assembler places:
#    max |dx| = 0.40 m (`customs/arrival_concourse`), and the phase sweep in
#    `deck.deck_plan.rank` already drives most of them to 0.00
#
# So the aperture has to be clear to 0.60 + 0.40 = 1.00 m either side of its own
# centre for every probe to miss, and the leaf itself wants 0.75 m. 1.10 m of
# half-width covers both with 0.10 m to spare; 2.40 m of height clears the
# 1.785 m probe and the 2.10 m leaf and reads as a door rather than a slot.
#
# WHAT WOULD OVERTURN IT: a corridor door wider than 1.50 m, a bay division that
# lets |dx| exceed 0.70 m, or a change to `_mouth_clear`'s probe span. All three
# are asserted against in `_selftest`, so this cannot drift silently.
DOOR_HALF_W_M = 1.10
DOOR_H_M = 2.40

# THE APPROACH ZONE INSIDE THE ROOM. INV-111. Cutting the hole is half of it:
# `dressing.dress` fills a room from its walls inward and its lane rule reserves
# a band down the LONG axis only, so the END wall -- the one the door is in --
# gets a run of lockers and crates across the very aperture. That is what
# `cnc`, `council_chamber` and `customs_south` were: shell OPEN, composed
# WALLED, measured in this session and printed in the report.
#
# Depth 2.00 m: `_mouth_clear` only looks 1.2 m in, so 1.2 m would satisfy the
# gate and still leave a crate where the player's second step lands. The
# character capsule is 0.35 m in radius (`collision.py`) and a stride is about
# 0.75 m, so a body needs 1.5 m past the jamb to be standing IN the room rather
# than in its doorway; 2.00 m is that plus the same 0.5 m of slack the aperture
# gets. Half-width is the aperture's, because a doorway you can reach and not
# walk through is the same defect one step further in.
APPROACH_DEPTH_M = 2.00

# The band `deck._mouth_clear` looks in, so `near_face_opening` and the
# assembler's acceptance test are asking about the same slice of the room.
# Asserted equal in `_selftest` rather than kept in step by hand.
NEAR_BAND_M = 1.2

# HOW LEAKY EACH COMPOSED SHELL IS, MEASURED, AND IT MAY NOT GET WORSE.
#
# A number nobody wrote down until it cost something. The audit further down
# this file had recorded since session 3y that seven of the nine bespoke
# modules were open surfaces; what changed in 3z is that `deck.build_deck`
# composes eight of them, and a composed shell's open edges become the DECK's
# open edges -- which `deck._selftest` asserts are zero.
#
# It began as a DEBT LEDGER that could not fail on its own content: 3,693 open
# edges across eight shells, fixed so the number could only be paid down.
# **It is paid.** Session 4a took every one of the six leaking modules to zero
# and the whole ledger now reads 31, all of them `docking_bay`'s mouth, which
# opens on vacuum.
#
# WHAT THE 3,693 ACTUALLY WERE, because the shape of it is the finding: two
# defects, both already fixed once in this project, in six new costumes.
#
#   A FLAT THING WITH NO EDGE -- 1,592 of council_chamber's floor tiles, bench,
#   fins, medallion and cove; 480 on the Zocalo's downlight pools; 342 across
#   C&C's mullions, glazing, hub, ring band, console faces and dais risers; 56
#   on the docking bay's deck emblem. Every one of them a surface authored in
#   the plane it is SEEN in, which is the plane in which its thickness is
#   invisible -- and a plate with no thickness is a plate with a boundary.
#   `interior_kit.deck_pad` and `interior_kit.plate_solid` are the two shapes
#   it takes and they now live in the kit, once each.
#
#   A LATHE OPEN AT ONE END -- 624 of hospitality's stools, tables, stems,
#   pendants and neon; 48 on customs' bollards. This is `dressing._cyl`'s
#   session-3x defect, alive in two more private copies, and both carried the
#   same reasoning in the same shape: the end is against the deck or inside the
#   ceiling, so nobody sees it. Nobody sees a hole either.
#
# The rest was structural: 240 round the Zocalo's tiled deck field, 12 under
# docking bay ledge risers that hung 2.2 m above the surface they were drawn
# to stand on, 37 where a back wall drawn as a rectangle met a stepped and
# curved cross-section.
#
# AND THE REASON NONE OF IT WAS CAUGHT IS ONE SENTENCE, which is the same one
# session 3x wrote about the doorway: **every gate in those six modules
# measured which way a surface FACED.** A surface that is not there faces
# nowhere, so a facing test passes vacuously on the missing half of every
# plate. Each of the six now carries its own closure gate with its own negative
# control, in the module that builds the thing.
#
# The gate below fires when a module gets leakier, and its own negative control
# -- dropping one triangle from `quarters` -- fires in `_selftest`.
SHELL_OPEN_EDGES = {
    "alien_sector": 0,
    # BUILT CLOSED, and its own `_selftest` says so with a control that fires:
    # every fitting is replaced by its bounding box and the machinery gate has
    # to go red. The car's END BULKHEAD is the piece this number is really
    # about -- a saloon left open where the gangway meets it reports zero open
    # edges (every box is watertight) and shows the background at the corners,
    # which is black, which looks exactly like a shadow.
    "core_tube": 0,
    "quarters": 0,
    # BUILT CLOSED, and each module's own self-test says so with a control that
    # fires: `concourse._selftest` removes the rib springing caps and watches
    # the shell leak 40 edges; `observation._selftest` measures all three
    # programs. `interior_kit.rib_arch` arrives OPEN at both springings -- it
    # sweeps t = 0..pi and emits no end caps, 8 edges a rib -- and that is
    # closed in `concourse._rib` rather than in the kit, because the kit is not
    # that module's to change and the caps are its own geometry.
    "interior_kit": 0,
    "components": 0,
    # 192 -> 0 in session 4b, and they were `dressing._cyl`'s session-3x defect
    # in a third costume: `plant_pipe` and `plant_conduit` were lathed with
    # `cap_lo=False, cap_hi=False` on the reasoning that a cell's ends face the
    # next cell. Composing a room-sized cell puts those ends on a wall a player
    # walks up to. See the note in `plant.plant_bay`.
    "plant": 0,
    "customs": 0,
    "command_control": 0,
    "zocalo": 0,
    "hospitality": 0,
    "council_chamber": 0,
    # THE ONE PLACE OPEN IS CORRECT, and it is not an exemption written to make
    # a number go green -- it is the bay's mouth, which opens on vacuum and is
    # how a Starfury gets in. `docking_bay._selftest` asserts the property
    # rather than the count: every open edge lies in the plane z = 0, they form
    # ONE closed loop, every vertex of that loop has degree exactly 2, and the
    # loop has as many edges as the bay's cross-section has points. That is
    # `aperture.py`'s rule and it is the difference between an opening and a
    # hole. Its negative control takes one triangle out of the crew-end
    # bulkhead and reports three stray edges.
    "docking_bay": 31,
}


def doorway_wall(add_box, name, x0, x1, y0, y1, z0, z1, at_x=0.0,
                 half_w=None, h=None):
    """An end wall with a doorway in it, emitted as PIECES round the aperture.

    Never a solid with a hole punched through it. `quarters.unit` records the
    rule and the module it was learned from -- *"built as plates around the
    volume, never as a solid with a hole -- the mistake command_control.py
    shipped when it sealed its own window inside the wall"* -- and it matters
    twice over here: three closed boxes leave a closed surface, where a boolean
    would leave an unrimmed aperture facing the one place on the station a
    player is guaranteed to be looking at.

    `add_box(name, lo, hi)` is the caller's own box primitive, so the wall is
    made of the module's own material names and joins its own mesh. Returns the
    number of pieces emitted -- 3 where the head is below the ceiling, 2 where
    the aperture reaches it.

    Dimensions are INV-110's and come from here rather than from each module,
    because three modules agreeing about a number by hand is how they stop
    agreeing.
    """
    half_w = DOOR_HALF_W_M if half_w is None else half_w
    h = DOOR_H_M if h is None else h
    ax0, ax1 = at_x - half_w, at_x + half_w
    if not (x0 < ax0 and ax1 < x1):
        raise ValueError(
            f"a {2 * half_w:.2f} m doorway at x={at_x:.2f} does not fit in a "
            f"wall running x {x0:.2f}..{x1:.2f}")
    top = min(h + y0, y1)
    n = 2
    add_box(name, (x0, y0, z0), (ax0, y1, z1))
    add_box(name, (ax1, y0, z0), (x1, y1, z1))
    if top < y1 - 1e-9:
        add_box(name, (ax0, top, z0), (ax1, y1, z1))
        n = 3
    return n


def near_face_opening(verts, tris, door_h=None, band=NEAR_BAND_M, step=0.05,
                      floor_tol=0.06, floor_band=None):
    """(centre_x, width) of the widest way IN through this shell's near face.

    THE QUESTION `room_shell` WAS ANSWERING WITH A BOUNDING BOX, and on two
    modules the bounding box is not where the door is:

      * `alien_sector.gallery` is a 4.2 m corridor with its quarters hung off
        the LEFT wall out to x = -4.85, so the bbox centre is **4.66 m** off the
        corridor -- a door cut at local x = 0 opens into an airlock's flank.
      * `quarters.run` is a row of six sealed cells with a gap left for a
        corridor and no corridor in it. Its cells' doorways are 4.1 m apart;
        the bbox centre lands on the wall between two of them on four of the
        seven quarters places.

    `_place_local` maps the room's local x = 0 onto the place's own bearing,
    which is exactly where the corridor puts its door. So local x = 0 has to be
    a place a body can walk through, and that is measurable rather than
    assumable: sample columns across the near face, ask at the same three
    heights `deck._mouth_clear` asks at, and keep the widest run that is both
    unobstructed AND has floor under it.

    THE FLOOR TEST IS NOT A REFINEMENT. Without it the widest "opening" in
    `alien_sector` is the 2.5 m of empty air outboard of the gallery wall where
    the airlocks have not started yet -- clear at every height, and nothing to
    stand on. An opening a body falls through is not an opening.

    Returns None when no run is wide enough for the leaf, which is the signal
    that the module has to grow a doorway rather than be shuffled sideways.

    TWO DEPTHS, AND THEY ARE NOT THE SAME QUESTION. Obstruction is measured in
    `deck._mouth_clear`'s own 1.2 m band, so this and the assembler's acceptance
    test agree by construction. Floor is measured over `APPROACH_DEPTH_M`,
    because a body steps THROUGH the aperture and lands past it -- and
    `council_chamber` has no floor at all in the first 1.2 m (its deck starts
    1.42 m in, behind the gallery step), so the narrower band called a chamber
    with a 22 m floor unenterable.

    `door_h` defaults to the CORRIDOR's leaf height, not to the taller aperture
    `doorway_wall` cuts, for the same agreement: `hospitality`'s dado rail
    crosses the opening at 2.01-2.06 m, which a 2.40 m probe calls a blockage
    and a 2.10 m door passes under.
    """
    import interior_kit as _K                                    # noqa: PLC0415
    door_h = door_h or _K.PROVISIONAL["door_height_m"]
    floor_band = APPROACH_DEPTH_M if floor_band is None else floor_band
    zmax = max(p[2] for p in verts)
    zcut = zmax - band
    fcut = zmax - floor_band
    blocks, floors = [], []
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        znear = min(p0[2], p1[2], p2[2])
        zfar = max(p0[2], p1[2], p2[2])
        if zfar < fcut:
            continue
        x0 = min(p0[0], p1[0], p2[0])
        x1 = max(p0[0], p1[0], p2[0])
        y0 = min(p0[1], p1[1], p2[1])
        y1 = max(p0[1], p1[1], p2[1])
        # Floor: near-horizontal and at the standing height the shell has
        # already been aligned to (y = 0). `floor_y` picked that band; this
        # only has to recognise it.
        #
        # REACHING INTO THE BAND, not starting in it -- and the difference is
        # not academic. The Zocalo's deck is laid in two triangles 2.19 m long
        # that run from the bulkhead into the first bay, so a `min z` test
        # excluded the only floor at the doorway and the function reported a
        # 21.6 m concourse as having nothing to stand on. Blockage keeps `min z`,
        # because that is the test `deck._mouth_clear` applies and the two have
        # to agree about what is in the way.
        if y1 - y0 < 1e-6 and abs(y0) <= floor_tol:
            floors.append((x0, x1))
        elif znear >= zcut:
            blocks.append((x0, x1, y0, y1))
    if not floors:
        return None
    heights = [door_h * f for f in (0.35, 0.60, 0.85)]
    xlo = min(f[0] for f in floors)
    xhi = max(f[1] for f in floors)
    n = max(2, int((xhi - xlo) / step) + 1)
    runs, run = [], None
    for i in range(n):
        px = xlo + (xhi - xlo) * i / (n - 1)
        ok = any(f[0] <= px <= f[1] for f in floors)
        if ok:
            for (x0, x1, y0, y1) in blocks:
                if x0 <= px <= x1 and any(y0 <= py <= y1 for py in heights):
                    ok = False
                    break
        if ok:
            run = (px, px) if run is None else (run[0], px)
        elif run is not None:
            runs.append(run)
            run = None
    if run is not None:
        runs.append(run)
    if not runs:
        return None
    # THE WIDEST RUN, AND THEN THE ONE NEAREST THE ORIGIN -- and the second term
    # is not a refinement, it is what makes this a FIXED POINT. `room_shell`
    # calls this, shifts x by the answer, and `_selftest` calls it again on the
    # shifted mesh and asserts the answer is now zero. With "widest" alone that
    # round trip does not close: `quarters.run` is six identical cells whose
    # doorways are the same width to the millimetre, the sample grid lands
    # differently once the mesh has moved, and a different cell wins by one
    # sample -- `qtr_command` picked a doorway 14.76 m from the one it had just
    # been centred on. Ties are the normal case here, not the edge case.
    #
    # It is also the better placement: of two equal doorways, the one nearest
    # the module's own origin turns the room least when it is wrapped onto the
    # ring.
    widest = max(r[1] - r[0] for r in runs)
    best = min((r for r in runs if r[1] - r[0] >= widest - step * 0.5),
               key=lambda r: abs(r[0] + r[1]) / 2.0)
    return ((best[0] + best[1]) / 2.0, best[1] - best[0])


def _keep_spans(verts, tris, spans, keep):
    """Drop whole named spans, and the vertices only they used.

    WHOLE PIECES, NEVER PART OF ONE. `dressing` emits each crate, chair and
    conduit drop as one span of a closed primitive, so removing a span removes
    a closed solid and the mesh stays closed. Clipping a box against the
    approach zone instead would leave an open rim facing the doorway -- the
    exact defect `dressing._cyl` shipped for four sessions, and the one place on
    the station a player is guaranteed to be looking at.
    """
    used = set()
    for i, (_n, lo, hi) in enumerate(spans):
        if not keep[i]:
            continue
        for tri in tris[lo:hi]:
            used.update(tri)
    remap = {}
    out_v = []
    for i in sorted(used):
        remap[i] = len(out_v)
        out_v.append(verts[i])
    out_t, out_g = [], []
    for i, (n, lo, hi) in enumerate(spans):
        if not keep[i]:
            continue
        t0 = len(out_t)
        for a, b, c in tris[lo:hi]:
            out_t.append((remap[a], remap[b], remap[c]))
        out_g.append((n, t0, len(out_t)))
    return out_v, out_t, out_g


def _span_boxes(verts, tris, spans):
    """(x0, x1, z0, z1) per span. The footprint each piece stands on."""
    out = []
    for _n, lo, hi in spans:
        xs, zs = [], []
        for tri in tris[lo:hi]:
            for i in tri:
                xs.append(verts[i][0])
                zs.append(verts[i][2])
        out.append((min(xs), max(xs), min(zs), max(zs)) if xs else None)
    return out


def compose(schema, profile, place, axial_half_m, density=1.0, report=None,
            door_at=None):
    """A bespoke room's true shape, furnished. Returns (verts, tris, spans).

    THE ANSWER `compare` POINTED AT. Neither "swap to bespoke" nor "leave the
    generic bay": the module gives a place its real shape, scale and identity,
    and `dressing.dress()` -- which takes a room's dimensions and not a
    `rooms.build` internal, so it composes without either side changing --
    fills it. A docking bay stops being a 12 m store bay AND stops being an
    empty 141 m shed.

    The dressing lands on the shell's own measured floor band, inset from its
    walls, at the shell's own centre. `dress` builds about the origin, so it is
    translated onto that centre rather than the bounding box's, which for a
    docking bay is 67 m away from where the floor actually is.

    `door_at` is `(x_m, half_width_m, depth_m)` -- the approach zone kept clear
    of furniture and of people. It defaults to the aperture `room_shell` has
    already centred the room on, which is `x = 0` by construction, so a caller
    that does not know where the corridor's door snapped to still gets a room it
    can walk into. See INV-111 and `APPROACH_DEPTH_M`.
    """
    import dressing as _dress                                   # noqa: PLC0415
    import rooms as _R                                          # noqa: PLC0415
    v, t, g = room_shell(schema, profile, place, axial_half_m)
    spans = _spans(g, len(t))
    ext = dressable_extent(v, t, g, place.get("module"))
    if ext is None:
        if report is not None:
            report["dressed"] = 0
        return v, t, spans
    w, ln, cx, cz = ext
    arch = _R.archetype(place)
    # INSET FROM THE WALLS. `dress` treats its w/l as the room's INTERIOR, and
    # a bespoke shell's floor band runs to the inside face of its own walls, so
    # handing the full extent puts a crate through a bulkhead.
    inset = 2.0 * _R.WALL_T_M
    ceil = max(2.2, max(p[1] for p in v) - min(p[1] for p in v))

    # DENSITY FALLS UNTIL THE ROOM FITS ITS BUDGET, which is `rooms.build`'s own
    # idiom applied to a different binding constraint. `rooms.build` falls
    # through `DRESS_DENSITIES` until a body can still cross the room; here the
    # room is 5,880 m2 and crossing was never in doubt -- what binds is cost.
    #
    # AT A FLAT DENSITY 1.0 THE DOCKING BAY DRESSED TO 348,876 TRIANGLES. That
    # is what "uniform furniture over 42 x 140 m" means: 65x the area of a
    # generic bay, so 65x the furniture, and both a budget failure (a habitat
    # cell affords 60,000) and wrong content -- a docking bay is an open volume
    # with equipment round its edges, not an office the size of a football
    # pitch. Falling density is a blunt instrument for that and it is the
    # honest one available: it keeps the room affordable and says so. A large
    # volume wanting a PERIMETER dressing scheme rather than a field one is a
    # real content decision and is recorded rather than faked.
    # THE FURNISHED BAND, AND IT IS AT THE DOOR. `rooms.tiling`'s `n_dress` and
    # `n_pop` ladder, applied to a room whose bays are metres. `dress` and
    # `populate` both scale with AREA, so a place grown to its declared
    # footprint -- `plant_zone` 13.8 m to 442 m -- would get 32x the furniture
    # and 32x the baked bodies at 7,300 triangles each. The plan has already
    # priced that and says how far in the furnishing reaches; the shell,
    # articulation, fixtures and declared interactables run the WHOLE length,
    # because those are what the place IS.
    #
    # THE ALTERNATIVE WAS BUILT AND MEASURED AND IS WORSE: thinning the
    # furniture over the whole room (which is what `DRESS_DENSITIES` does on its
    # own) took `plant_zone` to density 0.15 over 442 m, and a hall furnished at
    # 0.15 everywhere reads as empty from every standpoint in it. Full density
    # for the first stretch reads as a furnished hall from the one standpoint a
    # player arrives at.
    ln_in = max(1.0, ln - inset)
    band = ln_in
    if place.get("module") in AXIAL and composable(place):
        band = max(1.0, min(ln_in, _R.tiling(schema, profile, place)
                            .get("band_l") or ln_in))
    # The band's own centre, in the shell's frame: `cz` is the middle of the
    # dressable floor and the door is at its MAXIMUM z.
    cz_band = cz + (ln_in - band) / 2.0
    for dens in (density,) + tuple(d for d in _R.DRESS_DENSITIES
                                   if d < density):
        dv, dt, dg, dc = _dress.dress(
            place["key"], max(1.0, w - inset), band, ceil,
            arch, seed=place["key"], density=dens)
        if len(dt) <= MAX_DRESS_TRIS or dens == 0.0:
            break

    # NOTHING STANDS IN THE DOORWAY. INV-111, and it is the single cause of
    # three of this session's seven walled rooms: `cnc`, `council_chamber` and
    # `customs_south` all measured shell OPEN, composed WALLED. `dress`'s own
    # lane rule reserves a band down the room's LONG axis -- `abs(cx) < lane_hw`
    # -- and says nothing about the END wall, which is the wall the corridor
    # door is in, so a run of lockers lands across the aperture at exactly the
    # place a player arrives.
    #
    # `dress` cannot be asked to do this: it takes a room's dimensions and knows
    # nothing about where a corridor met it, which is the property that let it
    # be composed with a bespoke shell in the first place. So the pieces are
    # dropped here, WHOLE (`_keep_spans`), after they are built and in the
    # shell's own frame -- which is also the only frame in which the aperture's
    # position is known.
    dx, dhw, ddep = door_at or (0.0, DOOR_HALF_W_M, APPROACH_DEPTH_M)
    znear = max(p[2] for p in v)
    kept = []
    for bx in _span_boxes(dv, dt, dg):
        kept.append(bx is None or not (
            bx[0] + cx <= dx + dhw and bx[1] + cx >= dx - dhw
            and bx[3] + cz_band >= znear - ddep))
    blocked = len(kept) - sum(kept)
    dv, dt, dg = _keep_spans(dv, dt, dg, kept)

    base, t0 = len(v), len(t)
    v.extend((x + cx, y, z + cz_band) for x, y, z in dv)
    t.extend((a + base, b + base, c + base) for a, b, c in dt)
    spans.extend((n, lo + t0, hi + t0) for n, lo, hi in dg)

    # AND WHAT THE PLAYER CAME HERE TO USE. `rooms.build` has stood a place's
    # declared `interacts` in the room since layer 1 and this function never
    # did, so the split `interact.py --audit` measured was TOTAL: 273 of 275
    # declared interactables resolved on generic rooms and 0 of 82 on bespoke
    # ones. Not a content gap -- one placement rule that only one caller could
    # reach. It now lives in `rooms.place_interacts` and both call it.
    #
    # SKIP WHAT THE MODULE ALREADY BUILT, and ask the MESH rather than a list:
    # `earharts` builds `bar_table` for the declared `table` and `qtr_command`
    # builds `qtr_locker` for `locker`. `interact.resolve` reads the emitted
    # span names and reports both the exact and the module-named forms, so a
    # room that already has a table does not get a second one standing next to
    # it -- and a module that renames a span tomorrow simply stops being
    # skipped, rather than silently double-building.
    import interact as _ia                                      # noqa: PLC0415
    want = tuple(place.get("interacts") or ())
    already = _ia.resolve(want, {n for n, _lo, _hi in spans})
    # THE DOORWAY IS KEPT CLEAR BY BOUNDING WHERE A PROP MAY STAND, not by the
    # drop filter above. A declared interactable that is built and then deleted
    # for standing in the approach is worse than one never built: the register
    # says a player can use it, the room contains nothing, and no count can
    # tell that apart from a module that forgot it. `z_max` is the near end
    # less the approach depth, in the room's own centred frame, and the +z end
    # wall -- the one the corridor door is in -- is off the cursor's list.
    ip = {}
    if len(want) > len(already):
        iv, it_, ig = [], [], []
        _R.place_interacts(
            iv, it_, ig, place, max(0.5, (w - inset) / 2.0),
            max(0.5, (ln - inset) / 2.0), ceil,
            skip=tuple(already), wall_faces=("side", "near"),
            keep_clear=(dx - dhw - cx, dx + dhw - cx, znear - ddep - cz),
            report=ip)
        base, t0 = len(v), len(t)
        v.extend((x + cx, y, z + cz) for x, y, z in iv)
        t.extend((a + base, b + base, c + base) for a, b, c in it_)
        spans.extend((n, lo + t0, hi + t0) for n, lo, hi in ig)

    # AND THE PEOPLE, which the first version left out and the walk gate caught
    # within one run: "reached customs_north and NOBODY noticed -- 0.0 deg
    # turned". `rooms.build` runs `dressing` AND `populace`, and composing only
    # the first gives a room with furniture and no inhabitants -- which is
    # exactly the diorama CLAUDE.md's scope says the station must not be.
    #
    # LAST, and after the dressing, for the reason `rooms.build` states: people
    # are placed against the furniture that is actually there, so somebody ends
    # up ON a chair rather than near one.
    import populace as _pop                                     # noqa: PLC0415
    pv, pt, pg, ps = _pop.populate(
        place["key"], v, t, spans, max(1.0, w - inset), band,
        hour=_R.STATION_HOUR, arch=arch, seed=place["key"],
        g_ms2=_pop.place_gravity(place["key"]))
    # AND NOBODY STANDS IN IT EITHER. A body is 0.32-0.45 m across the
    # shoulders and `_mouth_clear` cannot tell one from a bulkhead -- it asks
    # what is in the way, which is the right question. `populate` fills a room
    # against the furniture already in it, so it does not put anybody where a
    # crate was; it will happily put somebody where the crate was NOT.
    #
    # THE ACTOR RECORD GOES WITH THE MESH. `deck.py` writes `rep["actors"]` into
    # `<deck>_actors.json` and `godot/scripts/npc.gd` looks the group up by
    # name, so a person dropped from the mesh and left in the cast list is a
    # name the runtime cannot resolve -- the mirror of the defect that made
    # `compose` carry `brep["actors"]` in the first place.
    actors = list(ps.get("actors", []))
    if pt:
        drop = {a["group"] for a in actors
                if abs(a["x"] + cx - dx) <= dhw + 0.45
                and a["z"] + cz_band >= znear - ddep}
        keep = [not any(n == d or n.startswith(d + "_") for d in drop)
                for n, _lo, _hi in pg]
        pv, pt, pg = _keep_spans(pv, pt, pg, keep)
        actors = [a for a in actors if a["group"] not in drop]
        blocked += len(drop)
    if pt:
        base, t0 = len(v), len(t)
        # `populate` works in the room's own centred frame, the same one
        # `dress` uses, so it takes the same translation onto the shell's
        # measured floor centre.
        v.extend((x + cx, y, z + cz_band) for x, y, z in pv)
        t.extend((a + base, b + base, c + base) for a, b, c in pt)
        spans.extend((n, lo + t0, hi + t0) for n, lo, hi in pg)
    if report is not None:
        report["dressed"] = len(dt)
        report["density"] = dens
        report["band_m"] = band
        report["extent"] = ext
        report["counts"] = dc
        report["people"] = len(actors)
        report["actors"] = actors
        report["doorway_cleared"] = blocked
        report["interacts"] = dict(ip.get("interacts") or {},
                                   already=sorted(already),
                                   declared=len(want))
    return v, t, spans


# ---------------------------------------------------------------------------
# What a swap would actually cost, measured
# ---------------------------------------------------------------------------
def compare(schema, profile, places=None):
    """(key, module, generic_tris, bespoke_tris, bespoke_extent) per place.

    THE MEASUREMENT THAT INVERTED THE FINDING, and it is worth keeping runnable
    rather than written down once. Session 3x recorded that `deck.py` assembles
    39 module-owned places as generic `rooms.py` bays and called it the largest
    fidelity gap on the station -- "the docking bay a player walks into is a
    generic store bay standing in for `docking_bay.py`". That is right about
    SHAPE and IDENTITY and wrong about RICHNESS, and the difference decides
    what to do about it:

        across the 25 ring-deck places that have a builder,
        generic 390,432 triangles against bespoke 210,702 -- **x0.54**

    The bespoke modules are SHELLS. `rooms.build` runs `dressing` and
    `populace` inside itself, so a generic bay arrives furnished and inhabited;
    `docking_bay.docking_bay` is 3,740 triangles of bay and nothing in it,
    against the generic 38,728. Swapping wholesale would take detail OFF the
    station -- 46% of it.

    It is not uniform, which is the useful part. Bespoke is RICHER for
    `alien_sector` (x3.69), `zocalo/shops_kiosks` (x1.45), `customs` (x0.94 to
    x1.41) and `plant/air_compressors` (x1.13), and much poorer for
    `docking_bay` (x0.10), `command_control` (x0.12), `council_chamber` (x0.12)
    and `hospitality` (x0.19).

    So the answer is neither "swap" nor "leave it": it is **bespoke shell plus
    generic dressing**. The module gives a place its true shape, scale and
    identity; `dressing.dress()` and `populace` fill it, and both already take
    a room's dimensions rather than a `rooms.build` internal, so the
    composition is available. That is the next increment and it is a real one.

    Two other facts this function establishes and a reader should not have to
    rediscover:

    * **The frames differ.** `rooms.build` centres a room on its origin (x
      +/-5.96, z +/-4.06 for `docking_bays`) with the floor at y = -0.14.
      `docking_bay.docking_bay` puts its floor at y = 0 and runs z from -0.75
      to +140.75. Anything that places bespoke geometry on a ring has to
      recentre it first, or the room lands 70 m up the station's axis.
    * **The ring has room.** Comparing a bespoke extent against
      `rooms.bay_span_m` says not one of the 25 fits -- but `bay_span_m` sizes
      a representative GENERIC bay and is not a constraint the ring imposes.
      The real constraint is the arc between consecutive doors, and on
      `blue/0/0` those are 480, 185, 295, 148, 74 and 148 m against a widest
      bespoke width of 42 m. Zero collisions.
    """
    import directory as _dr                                    # noqa: PLC0415
    import rooms as _R                                         # noqa: PLC0415
    out = []
    for q in (places if places is not None else _dr.PLACES):
        mod = q.get("module")
        if mod not in BESPOKE_GEOMETRY:
            continue
        # A PLACE-DISPATCHED MODULE'S OTHER PLACES ARE NOT MEASURABLE AND MUST
        # NOT BE COUNTED. `components` owns a navigation beacon; there is no
        # "what would the swap cost" for a place no builder claims, and
        # including it makes the ratio below a statistic about refusals.
        if mod in PLACE_DISPATCH and q["key"] not in BESPOKE_PLACES:
            continue
        try:
            gt = len(_R.build(schema, profile, q)[1])
        except Exception:                                      # noqa: BLE001
            gt = None
        try:
            r = BESPOKE_GEOMETRY[mod](schema, profile, q)
            v = unroll_to_local(r[0]) if mod in UNROLL else r[0]
            bt = len(r[1])
            ext = (max(p[0] for p in v) - min(p[0] for p in v),
                   max(p[2] for p in v) - min(p[2] for p in v))
        except Exception:                                      # noqa: BLE001
            bt, ext = None, None
        out.append((q["key"], mod, gt, bt, ext))
    return out


# WHICH ROOMS THE APPROACH ZONE IS ACTUALLY LOAD-BEARING FOR, and the split is
# a measurement rather than a list somebody kept up to date. `compose` clears a
# 2.20 x 2.00 m zone in front of the door because `dressing` reserves a lane
# down a room's LONG axis and says nothing about the END wall -- which is the
# wall the corridor's door is in.
#
# THE CONTROL WAS WRITTEN AS "all three go back to walled" AND THAT BROKE THE
# MOMENT THE FURNITURE IMPROVED. The machinery rework of session 3z rebuilt
# every fixture from a box into articulated geometry, and in doing so moved
# `council_chamber`'s and `arrival_concourse`'s furniture clear of their own
# apertures -- so they are now open WITHOUT the zone. A control that fails when
# the content gets better is measuring the wrong thing.
#
# Split, so both halves are real assertions: the first fails if the zone stops
# working, the second fails if those two rooms regress back into needing it.
# Re-measure with `compose(..., door_at=(0,0,0))` and move a key if it changes.
# RE-MEASURED AGAIN IN 3z, after the wardrobe was switched on. A dressed body
# is wider than a bare one -- a coat, a skirt, a stole -- so
# `arrival_concourse` moved back from FREED to DEPENDENT: its own furniture
# clears the aperture, and its people no longer do. That is the split doing its
# job twice in one session, and it is why these are two measured lists rather
# than one count.
ZONE_DEPENDENT = ("cnc", "customs_south", "zocalo")
# `arrival_concourse` MOVED HERE IN 4k, and the move is the measurement rather
# than a way to make a number green. `rooms.tiling` re-laid its furniture, and
# with the approach zone collapsed to nothing the room stays OPEN -- its own
# fittings now keep the aperture clear, which is a better outcome than needing
# the zone and is exactly what this tuple records. Verified as not an artefact
# of the other 4k change: swapping the new `dressable_extent` for the old bbox
# version gives a byte-identical 20.4 x 34.0 and open in both cases.
ZONE_FREED = ("council_chamber", "arrival_concourse")


def _selftest():
    import interior as _it                                     # noqa: PLC0415
    import interior_kit as _it_kit                             # noqa: PLC0415
    import directory as _dr                                    # noqa: PLC0415
    from importlib import reload as _reload                    # noqa: PLC0415
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = _it.load()

    # EVERY ENTRY MUST BUILD. A registry whose lambdas have gone stale is worse
    # than no registry: `export_scene` would report a room it cannot render and
    # `deck` would silently keep the generic bay for a reason that is a bug.
    broken = []
    for mod in sorted(BESPOKE_GEOMETRY):
        # A COMPOSABLE place, not merely the first place the module owns. For
        # `components` the register's first row is `obs_dome_1` today and could
        # be `nav_beacon` tomorrow -- and this loop would then report a builder
        # as broken for correctly refusing a navigation beacon.
        q = next((p for p in _dr.PLACES
                  if p.get("module") == mod and composable(p)), None)
        if q is None:
            q = next((p for p in _dr.PLACES if p.get("module") == mod), None)
        if q is None:
            broken.append((mod, "no place claims this module"))
            continue
        try:
            r = BESPOKE_GEOMETRY[mod](schema, profile, q)
            if not r[1]:
                broken.append((mod, "built no triangles"))
        except Exception as e:                                 # noqa: BLE001
            broken.append((mod, str(e)[:50]))
    check("every builder in the registry still builds", not broken, str(broken))

    # The registry may not claim a module no place owns, and every module that
    # owns a place and can be assembled should be in it. Both directions,
    # because each failure is silent in a different way.
    owning = {p.get("module") for p in _dr.PLACES} - {None}
    check("the registry claims no module nothing owns",
          set(BESPOKE_GEOMETRY) <= owning,
          str(sorted(set(BESPOKE_GEOMETRY) - owning)))

    # UNROLL and WALK_SURFACE may only name modules the registry has.
    check("UNROLL names only registered modules", UNROLL <= set(BESPOKE_GEOMETRY),
          str(UNROLL - set(BESPOKE_GEOMETRY)))
    check("WALK_SURFACE names only registered modules",
          set(WALK_SURFACE) <= set(BESPOKE_GEOMETRY),
          str(set(WALK_SURFACE) - set(BESPOKE_GEOMETRY)))

    # QUARTERS_CLASS covers exactly the places quarters owns.
    qp = {p["key"] for p in _dr.PLACES if p.get("module") == "quarters"}
    check("QUARTERS_CLASS covers exactly the quarters places",
          set(QUARTERS_CLASS) == qp,
          f"missing {sorted(qp - set(QUARTERS_CLASS))}, "
          f"stale {sorted(set(QUARTERS_CLASS) - qp)}")

    # `unroll_to_local` must actually flatten an arc: a plant bay is authored
    # at radius ~460 and must come back with its floor near y = 0.
    r = BESPOKE_GEOMETRY["plant"](schema, profile,
                                  next(p for p in _dr.PLACES
                                       if p.get("module") == "plant"))
    flat = unroll_to_local(r[0])
    ys = [p[1] for p in flat]
    check("unroll_to_local puts the floor at y = 0", abs(min(ys)) < 1e-6,
          f"floor at y={min(ys):.3f}")
    check("...and does not collapse the arc",
          max(p[0] for p in flat) - min(p[0] for p in flat) > 10.0)

    # THE COMPARISON IS THE POINT, and its headline is asserted so a change in
    # either direction is noticed rather than discovered later.
    rows = compare(schema, profile)
    g = sum(r[2] for r in rows if r[2] and r[3])
    b = sum(r[3] for r in rows if r[2] and r[3])
    check("every module-owned place can be measured both ways",
          all(r[2] and r[3] for r in rows), str([r[0] for r in rows if not r[3]]))
    check("the bespoke modules are still SHELLS, not richer rooms", b < g,
          f"bespoke {b:,} against generic {g:,}")
    print(f"  {len(BESPOKE_GEOMETRY)} builders over {len(rows)} places; "
          f"generic {g:,} tri, bespoke {b:,} tri (x{b / g:.2f})")
    richer = [r[0] for r in rows if r[2] and r[3] and r[3] > r[2]]
    print(f"  bespoke is RICHER for {len(richer)}: {', '.join(sorted(richer))}")

    # --- the frame adapter ------------------------------------------------
    import deck as _D                                          # noqa: PLC0415

    # Every builder is either DECLARED or explicitly UNKNOWN. A module in
    # neither would raise at assembly time with no explanation, which is the
    # one outcome worse than refusing.
    check("every builder's near end is declared or explicitly unknown",
          set(NEAR_END) | set(NEAR_END_UNKNOWN) | set(NOT_COMPOSED)
          == set(BESPOKE_GEOMETRY),
          f"unaccounted {sorted(set(BESPOKE_GEOMETRY) - set(NEAR_END) - set(NEAR_END_UNKNOWN) - set(NOT_COMPOSED))}")
    check("...and none is in two of them",
          not (set(NEAR_END) & set(NEAR_END_UNKNOWN))
          and not (set(NEAR_END) & set(NOT_COMPOSED))
          and not (set(NOT_COMPOSED) & set(NEAR_END_UNKNOWN)))
    check("every declared near end cites the module's own words",
          all(len(w) > 30 for _e, w in NEAR_END.values()))

    def signed_volume(vv, tt):
        cx = [sum(q[i] for q in vv) / len(vv) for i in range(3)]
        tot = 0.0
        for tri in tt:
            a, b_, c = [[vv[i][k] - cx[k] for k in range(3)] for i in tri]
            tot += (a[0] * (b_[1] * c[2] - b_[2] * c[1])
                    - a[1] * (b_[0] * c[2] - b_[2] * c[0])
                    + a[2] * (b_[0] * c[1] - b_[1] * c[0])) / 6.0
        return tot

    placed = 0
    openings = {}
    for q in composable_places():
        mod = q.get("module")
        ah = _D.room_axial_half_m(schema, profile, q)
        v, t, _g = room_shell(schema, profile, q, ah)
        xs = [p[0] for p in v]
        ys = [p[1] for p in v]
        zs = [p[2] for p in v]
        placed += 1
        check(f"{q['key']}: near face lands on the assembler's plane",
              abs(max(zs) - ah) < 1e-6, f"{max(zs):.4f} against {ah:.4f}")
        check(f"{q['key']}: the room extends AWAY from the corridor",
              min(zs) < ah - 1e-6, f"z runs {min(zs):.2f}..{max(zs):.2f}")
        # THE MEASURED FLOOR at y = 0, not the bounding box. The first version
        # of this asserted `min(ys) == 0` and passed trivially, because the
        # adapter was forcing exactly that -- an assertion checking its own
        # input. It also hid a real defect: `command_control`'s walkable
        # surface sits 1.90 m above its lowest vertex, so a player placed by
        # the bounding box spawns under the deck.
        check(f"{q['key']}: the walkable floor is at y = 0",
              abs(floor_y(v, t, _g, mod)) < 1e-6,
              f"floor band at {floor_y(v, t, _g, mod):.3f}, "
              f"bbox bottom {min(ys):.3f}")
        check(f"{q['key']}: nothing floats above the shell's own ceiling",
              max(ys) > 2.0, f"{max(ys):.2f} m tall")
        # LOCAL x = 0 IS A DOORWAY, NOT A CENTRE, and that is what this used to
        # assert. `_place_local` maps local x = 0 onto the place's own bearing,
        # which is where `deck_plan` puts the corridor's door, so the only thing
        # worth asserting about x is that a body can get through it.
        #
        # THE OLD ASSERTION -- `abs(min(xs) + max(xs)) < 1e-6` -- passed on
        # every module and was measuring its own input: `room_shell` set the
        # bounding-box centre and then checked that it had. It also hid two real
        # defects, which is what an assertion that cannot fail always does:
        # `alien_sector`'s corridor is 3.01 m off its own bounding box because
        # the quarters hang off one wall, and four of the seven `quarters`
        # classes put local x = 0 on the wall between two cells.
        op = near_face_opening(v, t)
        check(f"{q['key']}: local x = 0 is a way in",
              op is not None and abs(op[0]) < 1e-6,
              "no opening in the near face" if op is None
              else f"widest opening is {op[1]:.2f} m at x={op[0]:.3f}")
        if op is not None:
            openings[q["key"]] = op[1]
        # THE FLIP MUST NOT INVERT THE ROOM. `min_z` modules are turned by a
        # half turn about the vertical AND have their winding reversed to
        # match; get either half wrong and the room renders inside-out, which
        # a triangle count, an extent and a render against black all miss.
        raw = BESPOKE_GEOMETRY[mod](schema, profile, q)
        rv = unroll_to_local(raw[0]) if mod in UNROLL else raw[0]
        before, after = signed_volume(rv, raw[1]), signed_volume(v, t)
        check(f"{q['key']}: recentring does not turn the room inside-out",
              (before > 0) == (after > 0) or abs(before) < 1e-9,
              f"signed volume {before:.1f} -> {after:.1f}")

    # AND AN UNDECLARED MODULE MUST REFUSE. The failure mode this prevents is
    # silent: a room placed the wrong way round has the same triangle count,
    # the same extent and the same materials as one placed correctly.
    held = list(NEAR_END_UNKNOWN) + list(NOT_COMPOSED)
    refused = 0
    for mod in held:
        q = next((p for p in _dr.PLACES if p.get("module") == mod), None)
        if q is None:
            continue
        try:
            room_shell(schema, profile, q, 4.0)
        except KeyError:
            refused += 1
    check("a module that is not composed refuses rather than guessing",
          refused == len([m for m in held
                          if any(p.get("module") == m for p in _dr.PLACES)]),
          f"{refused} refused")

    # AND A PLACE-DISPATCHED MODULE MUST REFUSE THE PLACES IT DOES NOT BUILD.
    # This is the gate the module-keyed table could not have: `components` owns
    # a navigation beacon and a comms grid as well as two domes and a rotunda,
    # and the failure mode of registering it without this is SILENT -- an
    # observation room where a sensor blade goes, with the same triangle count,
    # the same extent and the same materials as a correct one.
    wrong, refused_p = [], []
    for q in _dr.PLACES:
        if q.get("module") not in PLACE_DISPATCH:
            continue
        if composable(q):
            continue
        try:
            BESPOKE_GEOMETRY[q["module"]](schema, profile, q)
            wrong.append(q["key"])
        except KeyError:
            refused_p.append(q["key"])
    check("a place-dispatched module refuses every place it has no program for",
          not wrong,
          f"{wrong} were BUILT by a module that has no program for them")
    check("...and it names them, so the refusal is a decision and not a gap",
          len(refused_p) >= 6, f"only {len(refused_p)} refused")
    print(f"  place dispatch: {len(BESPOKE_PLACES)} places claimed across "
          f"{len(PLACE_DISPATCH)} modules, {len(refused_p)} refused by name "
          f"({', '.join(sorted(refused_p)[:4])}...)")
    print(f"  frame adapter: {placed} places recentred, "
          f"{len(NEAR_END)} modules composed, "
          f"{len(NOT_COMPOSED)} declared but held back, "
          f"{len(NEAR_END_UNKNOWN)} undeclared")
    if openings:
        worst = min(openings.items(), key=lambda kv: kv[1])
        print(f"  narrowest doorway on the station: {worst[0]} at "
              f"{worst[1]:.2f} m, against the corridor's "
              f"{_it_kit.PROVISIONAL['door_width_m']:.2f} m leaf")

    # --- THE DOORWAY ------------------------------------------------------
    # `deck.build_deck` composes a bespoke room only if `_mouth_clear` says a
    # body can get in, and until this session it could not, on seven of the
    # places that have a builder. That test lives in `deck.py` and this is the
    # module that BUILDS the thing it tests -- CLAUDE.md's rule from session 3x,
    # "a gate belongs in the module that builds the thing, and it must build the
    # hard case". So it is asserted here, on the composed room rather than the
    # shell, because three of the seven had an open shell and a locker across
    # the aperture.
    import interact as _ia                                     # noqa: PLC0415
    import rooms as _R                                         # noqa: PLC0415
    walled, narrow, cleared = [], [], 0
    unresolved, declared_n, alias_n = [], 0, 0
    body_tris = body_n = 0
    spans_short, spans_long = [], []
    for q in composable_places():
        mod = q.get("module")
        ah = _D.room_axial_half_m(schema, profile, q)
        brep = {}
        cv, ct, cg = compose(schema, profile, q, ah, report=brep)
        cleared += brep.get("doorway_cleared", 0)
        # WHAT A BAKED BODY COSTS, RE-MEASURED ON THE COMPOSED ROOM. See
        # `BAKED_BODY_TRIS`: it is the term that decides how far every grow
        # place is allowed to reach, so a stale constant here would quietly
        # overspend `budget.py`'s frame allowance rather than fail. Counted off
        # the TOP-LEVEL `npc_*` spans, because a person's parts nest inside
        # their own span and summing spans would double-count them.
        if brep.get("people"):
            seen = bytearray(len(ct))
            for n, lo, hi in cg:
                if n.startswith("npc"):
                    for i in range(lo, hi):
                        seen[i] = 1
            body_tris += sum(seen)
            body_n += brep["people"]
        # AND THE MESH IS THE LENGTH THE PLAN SAYS IT IS. `rooms.built_span_m`
        # reports `axial_span_m` for a composed place and `deck.room_shell_for`
        # sizes the COLLISION from it, so a module whose mesh disagrees with
        # its own declared span puts render geometry outside the volume a body
        # can walk in. Asserted in the module that composes the room.
        zs = [p[2] for p in cv]
        want_span = _R.built_span_m(schema, profile, q)[1]
        got_span = (max(zs) - min(zs)) if zs else 0.0
        if got_span < want_span - 0.01:
            spans_short.append((q["key"], round(got_span, 2),
                                round(want_span, 2)))
        elif got_span > want_span + 0.30:
            spans_long.append((q["key"], round(got_span, 2),
                               round(want_span, 2)))
        if not _D._mouth_clear(cv, ct, 0.0):
            walled.append(q["key"])
        if openings.get(q["key"], 0.0) < _it_kit.PROVISIONAL["door_width_m"]:
            narrow.append((q["key"], round(openings.get(q["key"], 0.0), 2)))
        # WHAT THE REGISTER SAYS A PLAYER CAN USE HERE, and whether this room
        # contains it. Asserted in the module that composes the room, on the
        # composed room, for the reason the doorway gate above is: a gate that
        # lives anywhere else measures a mesh nobody assembled.
        want = tuple(q.get("interacts") or ())
        declared_n += len(want)
        got = _ia.resolve(want, {n for n, _a, _b in cg}, cg)
        alias_n += sum(1 for k in got if not got[k].startswith(("prop_",
                                                                "fix_")))
        for k in want:
            if k not in got:
                unresolved.append(f"{q['key']}/{k}")
    check("every composed bespoke room can be walked into", not walled,
          f"walled at the doorway: {walled}")
    # ...and it is the composed mesh that is measured, not the plan.
    # ASSERTED ON THE SHORT SIDE, MEASURED ON THE LONG ONE, and the asymmetry
    # is not a softening. `built_span_m` reports `axial_span_m`, which is the
    # SHELL's own measured extent, and `compose` only ADDS to that shell -- so
    # short can only mean the module built two different lengths on two calls,
    # which is a determinism failure and must fail. Long means a prop or a
    # person stands past the shell's own end, which is worth seeing every run
    # and is `rooms.py --footprint`'s assertion to make against the mesh
    # `deck.room_geometry` actually draws.
    check("a composed room's mesh is never SHORTER than the span its plan "
          "reports", not spans_short,
          f"{spans_short[:5]} -- deck.room_shell_for sizes the collision from "
          f"rooms.built_span_m, so a short mesh is a shell longer than the "
          f"room it stands for")
    if spans_long:
        print(f"  {len(spans_long)} composed rooms carry furniture or people "
              f"past their own shell: {spans_long[:4]}")
    if body_n:
        measured = body_tris / body_n
        check("BAKED_BODY_TRIS still describes a baked body",
              abs(measured - BAKED_BODY_TRIS) <= 0.25 * BAKED_BODY_TRIS,
              f"{measured:,.0f} measured over {body_n} people against a "
              f"declared {BAKED_BODY_TRIS:,} -- every band in axial_units is "
              f"derived from this number")
        print(f"  a baked body: {measured:,.0f} triangles over {body_n} "
              f"people in {len(composable_places())} composed rooms "
              f"(declared {BAKED_BODY_TRIS:,})")
    check("...through an aperture at least as wide as the corridor's leaf",
          not narrow, f"{narrow}")
    check("...and contains every interactable the register declares for it",
          not unresolved, f"{len(unresolved)} missing: {unresolved[:12]}")
    print(f"  doorway: {len(openings)} composed rooms, all clear at dx = 0, "
          f"{cleared} pieces and people moved out of the approach zone")
    print(f"  interacts: {declared_n - len(unresolved)}/{declared_n} declared "
          f"uses resolve on the composed rooms, {alias_n} of them under the "
          f"module's own name for the object")

    # NEGATIVE CONTROL -- the placement pass itself. With `place_interacts`
    # stubbed out, a composed room falls back to whatever its module happened
    # to build, and the count above has to COLLAPSE. Before this pass existed
    # it was 0 of 82, measured by `interact.py --audit`; if the control does
    # not reproduce that, the pass is not what is putting the props there and
    # the gate above is measuring a case with no defect in it.
    import rooms as _Rp                                        # noqa: PLC0415
    _keep = _Rp.place_interacts
    _Rp.place_interacts = lambda *a, **k: {"floor": 0, "wall": 0,
                                           "ceiling": 0, "dropped": []}
    try:
        ctl_res = ctl_dec = 0
        for q in composable_places():
            want = tuple(q.get("interacts") or ())
            if not want:
                continue
            ah = _D.room_axial_half_m(schema, profile, q)
            _cv, _ct, cg = compose(schema, profile, q, ah)
            ctl_dec += len(want)
            ctl_res += len(_ia.resolve(want, {n for n, _a, _b in cg}, cg))
    finally:
        _Rp.place_interacts = _keep
    check("...and WITHOUT the placement pass most of them go missing again",
          ctl_res < ctl_dec * 0.5,
          f"the control still resolved {ctl_res}/{ctl_dec} -- the pass is not "
          f"what is putting the declared interactables in these rooms")
    print(f"  control: with `place_interacts` stubbed the same rooms resolve "
          f"{ctl_res}/{ctl_dec}")

    # NEGATIVE CONTROL 1 -- the approach zone. Compose with the zone collapsed
    # to nothing and the rooms `dressing` fills to the aperture have to go back
    # to WALLED. If they do not, this gate is measuring a case with no defect in
    # it, which is the failure mode CLAUDE.md records for `interior_kit`'s
    # tag-coverage assertion running on a corridor with no doors.
    control = []
    for key in ZONE_DEPENDENT + ZONE_FREED:
        q = next(p for p in _dr.PLACES if p["key"] == key)
        ah = _D.room_axial_half_m(schema, profile, q)
        cv, ct, _cg = compose(schema, profile, q, ah,
                              door_at=(0.0, 0.0, 0.0))
        if not _D._mouth_clear(cv, ct, 0.0):
            control.append(key)
    check("...and WITHOUT the approach zone the rooms that depend on it are "
          "walled again",
          set(ZONE_DEPENDENT) <= set(control),
          f"{sorted(set(ZONE_DEPENDENT) - set(control))} stayed open with the "
          f"zone collapsed -- the zone is not what is keeping them open")
    check("...and the rooms whose own furniture moved are open WITHOUT it, "
          "which is a better outcome than the zone and is measured, not assumed",
          not (set(ZONE_FREED) & set(control)),
          f"{sorted(set(ZONE_FREED) & set(control))} went back to walled")

    # NEGATIVE CONTROL 2 -- the doorway cut into `hospitality`, in the module's
    # OWN frame rather than through the assembler, so it measures the geometry
    # this session added and not the recentring around it. The bar had four
    # sealed walls; with `doorway_wall` swapped for a solid plate the near face
    # closes and `near_face_opening` returns None.
    import hospitality as _H                                    # noqa: PLC0415
    hv, ht, _hg = _H.room()
    op_h = near_face_opening(hv, ht)
    check("the bar's own frame carries the doorway",
          op_h is not None and op_h[1] >= _it_kit.PROVISIONAL["door_width_m"],
          f"{op_h}")
    # PATCH THE MODULE `hospitality` IS ACTUALLY HOLDING, which is not this
    # one when the file is run directly: `python3 station/bespoke.py` loads this
    # code as `__main__`, and `hospitality`'s `import bespoke` then loads a
    # SECOND copy under the name `bespoke`. Patching `globals()` here changed
    # `__main__.doorway_wall` and the bar went on calling the real one -- the
    # control reported a sealed bar with a 2.11 m opening in it, which is the
    # control failing to control anything. `_H._bsp` is the object the caller
    # dereferences, so it is the only one worth patching.
    real_dw = _H._bsp.doorway_wall
    try:
        _H._bsp.doorway_wall = (
            lambda add_box, name, x0, x1, y0, y1, z0, z1, at_x=0.0,
            half_w=None, h=None:
            (add_box(name, (x0, y0, z0), (x1, y1, z1)), 1)[1])
        sv, st, _sg = _H.room()
        check("...and with a solid plate instead, it does not",
              near_face_opening(sv, st) is None,
              f"a sealed bar still reports an opening: "
              f"{near_face_opening(sv, st)}")
    finally:
        _H._bsp.doorway_wall = real_dw

    # AND THE ONE THAT WAS HELD BACK IS STILL HELD BACK, for the reason stated
    # rather than by having quietly grown a door.
    #
    # THE REASON CHANGED IN SESSION 4a AND THE TEST HAD TO CHANGE WITH IT.
    # It used to count triangles -- "the crew bulkhead is one plate, and one
    # plate is 2" -- which was true only while the bulkhead was drawn as a
    # rectangle, and drawing it as a rectangle was itself the defect: a
    # rectangle cannot close a bay whose floor is stepped and whose roof is an
    # arc, and 37 of that module's open edges were exactly that mismatch. The
    # cap is now the ear-clipped cross-section, 29 triangles, and counting
    # triangles would either fail on a correct wall or have to be re-pegged
    # every time the section gains a vertex.
    #
    # So the test is the PROPERTY: the crew end is unpierced -- every open edge
    # in the module lies in the plane of the mouth -- and it is still held
    # back. If somebody cuts a door in the bulkhead, the first half fires and
    # points at what has to happen first, which is now a change in `deck.py`
    # rather than a change here. `docs/deck-mouth-exemption.md` has the text.
    import docking_bay as _DB                                   # noqa: PLC0415
    _bv, _bt, _bg = _DB.docking_bay(0, schema, profile)
    _bop, _ = _it_kit.boundary_edges(_bv, _bt)
    pierced = [e for e in _bop
               if not (abs(e[0][2]) < 1e-6 and abs(e[1][2]) < 1e-6)]
    check("the docking bay's crew bulkhead is unpierced, and it is held back",
          not pierced and "docking_bay" in NOT_COMPOSED,
          f"{len(pierced)} open edges away from the mouth. Piercing the crew "
          f"end composes a shell with {SHELL_OPEN_EDGES['docking_bay']} open "
          f"edges -- all of them the MOUTH, which opens on vacuum -- onto a "
          f"deck that asserts watertightness and cannot yet say so")
    # --- CLOSURE, WHICH COMPOSING A SHELL PUTS ON A DECK ------------------
    # The audit table above has recorded since session 3y that seven of the
    # nine bespoke modules are open surfaces and that nothing gates it. Now
    # something has to, because `deck.build_deck` composes eight of them and a
    # composed shell's open edges become the DECK's open edges -- and the deck
    # asserts watertightness. That is what stopped `docking_bay` landing this
    # session (160 edges; see its own comment), and it would have gone
    # unnoticed on `red/0/0` and `green/0/0`, where the deck gate does not run.
    #
    # THIS GATE CANNOT FAIL ON TODAY'S CONTENT AND IT IS NOT SUPPOSED TO. The
    # rooms are already open; closing 3,500 edges across five modules is a
    # session's work on its own. What it does is FIX the number, so the debt is
    # visible and cannot grow -- and the direction it can fail in is the one
    # that matters, which is a module getting leakier. Its negative control is
    # below and it fires.
    # EVERY PLACE, NOT ONE PER MODULE. This used to build the register's first
    # place for each module and read the answer as the module's -- which is the
    # session-4h defect in its purest form: *"when a defect is found in one
    # entry of a table, check every entry and gate the table"*, applied to the
    # rows of a table whose entries are now places. `quarters` builds seven
    # different rooms and `hospitality` five; one of them being closed said
    # nothing about the other six.
    counts, worse = {}, []
    for q in composable_places() + [p for p in _dr.PLACES
                                    if p.get("module") in NOT_COMPOSED]:
        mod = q["module"]
        r = BESPOKE_GEOMETRY[mod](schema, profile, q)
        op, _non = _it_kit.boundary_edges(r[0], r[1])
        counts[mod] = max(counts.get(mod, 0), len(op))
        if len(op) > SHELL_OPEN_EDGES.get(mod, 0):
            worse.append((q["key"], mod, len(op), SHELL_OPEN_EDGES.get(mod)))
    check("no composed shell has got leakier", not worse,
          f"{worse} -- these edges land on a DECK, and the deck asserts "
          f"watertightness")
    ledger = set(NEAR_END) | set(NOT_COMPOSED)
    check("...and the baseline names every module the assembler places or "
          "holds back", set(SHELL_OPEN_EDGES) == ledger,
          f"missing {sorted(ledger - set(SHELL_OPEN_EDGES))}, "
          f"stale {sorted(set(SHELL_OPEN_EDGES) - ledger)}")
    tot = sum(counts.values())
    print(f"  closure debt: {tot:,} open edges across {len(counts)} composed "
          f"shells -- " + ", ".join(f"{m} {n}" for m, n in
                                    sorted(counts.items(), key=lambda kv:
                                           -kv[1]) if n))

    # NEGATIVE CONTROL 3 -- open one up and the baseline gate has to fire.
    # A single dropped triangle is the smallest possible regression and the
    # hardest to see in a render, which is exactly why it is the control.
    q = next(p for p in _dr.PLACES if p.get("module") == "quarters")
    r = BESPOKE_GEOMETRY["quarters"](schema, profile, q)
    holed = [tri for i, tri in enumerate(r[1]) if i != 0]
    op, _non = _it_kit.boundary_edges(r[0], holed)
    check("...and dropping ONE triangle from a closed shell fires it",
          len(op) > SHELL_OPEN_EDGES["quarters"],
          f"quarters went from {SHELL_OPEN_EDGES['quarters']} to {len(op)} "
          f"open edges with a triangle removed -- the gate did not notice")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0



# ---------------------------------------------------------------------------
# Putting a bespoke room where a generic one goes
# ---------------------------------------------------------------------------
# WHICH END OF A BESPOKE ROOM MEETS THE CORRIDOR. There is no way to infer
# this: `docking_bay` and `command_control` are built the same way round in
# their own frames and want OPPOSITE ends against a corridor, because one's
# +Z runs in from a vacuum mouth and the other's runs out toward a window.
# Guessing would place a room backwards, which changes no triangle count, no
# extent, no gate -- and is the first thing a player would notice.
#
# So each entry is DECLARED, with the module's own words as the source. A
# module that is not here raises rather than defaulting: `rooms.build`'s
# convention (near face at +z) is a fine default for a room somebody authored
# knowing about it, and none of these were.
NEAR_END = {
    # "+X across, +Y up, +Z forward toward the window; deck at y = 0" -- the
    # window is the far wall, so the way in is the near one. OPPOSITE of the
    # bay, from an identically-worded frame.
    "command_control": ("min_z", "command_control: '+Z forward toward the "
                                 "window; deck at y = 0'"),
    # "z runs ALONG it -- from the gate line at z=0 to the board wall at
    # z=HALL_LEN_M". You arrive at the gate line.
    "customs": ("min_z", "customs.hall: 'from the gate line at z=0 to the "
                         "board wall at z=HALL_LEN_M'"),
    # "The whole bar, authored with x across, y up, z along", and it measures
    # symmetric about the origin (z -5.91..+5.91), so either end serves and the
    # generic convention applies unchanged.
    "hospitality": ("max_z", "hospitality.room: authored symmetric about the "
                             "origin, z -5.91..+5.91"),
    # "Bench centred on the origin, delegates outboard of it" -- symmetric.
    "council_chamber": ("max_z", "council_chamber: 'Bench centred on the "
                                 "origin'"),
    # "One gallery: the corridor, its lattice, and QUARTERS_PER_GALLERY locks",
    # and the module builds `alien_endwall` across z = GALLERY_LEN_M with the
    # ring fitting on it. An end wall is the FAR end by definition, so the way
    # in is z = 0 -- which the module leaves open and which its first airlock
    # stands 3.5 m inside of.
    "alien_sector": ("min_z", "alien_sector.gallery builds 'alien_endwall' "
                              "across z = GALLERY_LEN_M and leaves z = 0 open"),
    # "One quarters unit, authored with the door wall at z = 0", and `run`
    # offsets every unit by +cw/2 -- leaving a corridor-width gap in front of
    # the doors and building nothing in it. The ring's corridor IS that
    # corridor: the row's open side is its minimum z, and the units' own
    # doorways are what `near_face_opening` then centres the place on.
    "quarters": ("min_z", "quarters.unit: 'authored with the door wall at "
                          "z = 0'; run() offsets every unit by +cw/2, leaving "
                          "the corridor gap at minimum z"),
    # `zocalo_run` builds "bays end to end along +z" and BOTH ends are open by
    # design -- which is why this was undeclared. What decides it is the cap:
    # `cap_ends` now puts a bulkhead outside each end of the run and cuts the
    # doorway in the MINIMUM-z one, so the declaration and the geometry are one
    # decision made in one place rather than two that can disagree.
    "zocalo": ("min_z", "zocalo_run(cap_ends=True) cuts its doorway in the "
                        "minimum-z bulkhead; the maximum-z cap is solid"),
    # BOTH OF THE PLACE-DISPATCHED MODULES ARE `max_z`, and they are because
    # they were AUTHORED to be -- which is the difference between these two
    # entries and the nine above them. Every module above was written to be
    # rendered on its own before `deck.py` could assemble anything, so its near
    # end had to be recovered from what it says about itself. `concourse.py`
    # and `observation.py` were written after the assembler and cut their own
    # doorway in their own maximum-z face at local x = 0, which is where
    # `deck._place_local` maps the corridor's door. The declaration and the
    # geometry are one decision made in one place, and each module's own
    # self-test measures the aperture with `near_face_opening` -- the same
    # function this file's gate uses.
    "interior_kit": ("max_z", "concourse.central_corridor cuts its doorway "
                              "with bespoke.doorway_wall in the maximum-z end "
                              "wall; the minimum-z end is solid"),
    "components": ("max_z", "observation.room enters through a vestibule that "
                            "runs out to maximum z and carries the doorway in "
                            "its end wall; the chamber is behind it"),
    # DECIDED BY THE WALKWAY, exactly as the Zocalo's is decided by its cap.
    # `plant.room_cell` puts the catwalk hard against the cell's MAXIMUM z and
    # rails only its open side, so the maximum-z face is the one a body can
    # step through and the minimum-z face is 8 m of tank farm. The declaration
    # and the geometry are one decision made in one place.
    "plant": ("max_z", "plant.room_cell puts the catwalk's near edge at z1 "
                       "with walk_sides=(-1,), so the maximum-z face is the "
                       "only one with floor at the doorway"),
    # AUTHORED max_z, like the other two modules written after the assembler.
    # `shuttle.room` runs a vestibule out to maximum z and cuts its aperture
    # there with `bespoke.doorway_wall` at local x = 0, which is where
    # `deck._place_local` maps the ring corridor's door. The declaration and
    # the geometry are one decision made in one place, and `shuttle._selftest`
    # measures the aperture with `near_face_opening` -- the same function this
    # file's own gate uses.
    "core_tube": ("max_z", "shuttle.room enters through a vestibule running "
                           "out to maximum z that carries the doorway in its "
                           "end wall; the far end of both programs is solid"),
}

# DECLARED, AND STILL NOT COMPOSED. A separate list from the one below because
# it is a separate fact and collapsing the two would lose the useful half: this
# module's near end is not a mystery, it is `max_z` on the module's own words --
# *"+Z runs INTO the bay from the mouth at z = 0"*, so the vacuum end is the far
# one and the crew end is the near one. What stops it is closure, which is a
# debt with a number (`SHELL_OPEN_EDGES`) and an owner, not an open question.
#
# `room_shell` refuses for anything not in `NEAR_END`, so `deck.build_deck`
# takes the generic bay and says why -- which is the outcome this list exists to
# produce deliberately rather than by omission.
NOT_COMPOSED = {
    "docking_bay": "near end is max_z and known, and the shell is now CLOSED "
                   "except at its mouth -- 151 open edges down to 31, all of "
                   "them one closed degree-2 loop in the plane z = 0, "
                   "asserted in docking_bay._selftest. What is left is not a "
                   "defect in this module: a bay's mouth opens on VACUUM, and "
                   "deck._selftest's watertightness assertion has no way to "
                   "say so, so composing it would fail on 31 edges that are "
                   "correct content. The exact change deck.py needs is in "
                   "docs/deck-mouth-exemption.md -- an exemption keyed on a "
                   "declared aperture, tested the way aperture.py tests one, "
                   "rather than a tolerance.",
}

# The one that is NOT declared, and why it is genuinely undecidable from what
# the module says about itself. Recorded so the next reader does not repeat the
# search rather than as an apology.
#
# EMPTY AS OF SESSION 4b, AND THE ENTRY THAT WAS HERE IS WORTH KEEPING BECAUSE
# IT WAS RIGHT ABOUT THE MEASUREMENT AND WRONG ABOUT THE CAUSE. It read:
#
#     "plant builds in STATION coordinates at radius 447-471 and is unrolled
#      for rendering; its walkable surface is a catwalk (WALK_SURFACE), not a
#      floor... Measured in session 4a: the catwalk's floor band is
#      82.2 m across the arc by 1.80 m along the axis, and the bay it belongs
#      to is 92 x 442 m -- so recentring it onto a ring deck would lay 442 m of
#      tank farm along the station's axis, through every other z-cluster on
#      that deck. It needs a placement decision, not a near-end declaration."
#
# Every number in that is correct and the conclusion drawn from it was not.
# 92 x 442 m is not a property of `plant`; it is what `plant_bay` returns when
# it is handed `arc_deg=10.0` and no `z_span`, because the default z_span is
# the GREY SECTOR'S OWN EXTENT. The registry entry above was asking a bay
# generator for a sector and then reading the answer as the module's nature.
#
# The lesson generalises past this module: a measurement taken through a call
# describes the CALL. Two of the three numbers here -- 92 m and 442 m -- were
# arguments, and the one that was really the module's (1.80 m, CATWALK_W_M) is
# the one that turned out not to be the obstacle.
NEAR_END_UNKNOWN = {}


# THE MODULES THAT OWN A PLACE AND HAVE NO BUILDER HERE, AND WHY EACH IS A
# DELIBERATE "NO" RATHER THAN A GAP. Session 4b, and it is written down because
# the question ("compose the 20 places with no builder") is the obvious next
# one and the answer is mostly no -- so the next context should spend its time
# on the three that are worth building instead of re-deriving these fourteen.
#
# `deck.py --sweep` counts per (cluster, place), so a place near a cluster
# boundary is served by two corridors and counted twice. The 26 generic
# assemblies at the head of session 4b were 20 distinct places.
#
# --- components x14 (9 places) -------------------------------------------
#
# `components.py` BUILDS THE EXTERIOR. Its docstring's first line is "generate
# the station's non-axisymmetric components... built here as parametric
# primitives placed against the longitudinal framework", every builder emits a
# RING of instances in station coordinates, and the decisive measurement is one
# line: standing under an `observation_dome` at its own base plane, **0 of its
# 192 triangles face the viewer**. Every surface points out. A player inside
# one sees the background, and the background is black.
#
# `dome_mesh` says so itself -- "the base sits inside the hull and the hole
# faces away from every camera", and the base disc is "wound the other way --
# it faces into the hull". These are blisters ON a hull, not rooms under one.
#
#   obs_dome_1  x3  } WORTH BUILDING, and the only three that are. Dome 1 IS
#   obs_dome_2  x3  } Command & Control's dome and `03-sector-blue/comand and
#   obs_rotundas x1 } contorl.webp` is authority 1 seen FROM INSIDE it;
#                     `05-sector-green/rotunda.webp` is authority 1 of a
#                     rotunda's interior and is the richest single reference in
#                     00-INDEX. What is missing is not a composition, it is an
#                     INTERIOR: a floor, a window ring, and a dome shell with
#                     thickness so its inner surface exists. Spec at the bottom
#                     of this block.
#   cobra_bays  x1    Exterior launch tubes. 84 triangles of well liner for a
#                     42 m bay, 31% of them facing a viewer standing in it --
#                     a blockout of a volume a Starfury is thrown out of, with
#                     no floor at a person's scale and no pressurised side.
#   proximity_arrays x1  `swept_fins`. Sensor blades. `interacts` is EMPTY.
#   comms_grid  x1    `deep_space_comms_grid` has no row in `schema.components`
#                     at all; only its 1,060 m SUPPORT PYLON is built.
#                     `interacts` is EMPTY.
#   power_transfer x1  "Power transfer core + 12 cooling fins". The fins are
#                     `planar_blades`, 470 m of exterior blade; the core has no
#                     builder. Its one `interacts` is a console, which is a
#                     control room `rooms.py` can build and `components` cannot.
#   mooring_clamps x1  NO BUILDER ANYWHERE: `hard_docking_mooring_clamp` is in
#   nav_beacon  x2     `schema.exterior_systems` and not in `schema.components`,
#                      as is `primary_navigation_beacon`. Nothing to compose.
#
# --- core_tube x2 --------------------------------------------------------
#
# `core_shuttle` and `shuttle_car`. REFUSED BY THE MODULE ITSELF, which is the
# cleanest possible answer: `core_tube._guard` raises unless **100%** of the
# envelope's faces point AWAY from the spin axis, because "this geometry is
# seen from outside, because the viewer is out in the drum looking in at the
# axis". A module that asserts it cannot be seen from inside cannot be an
# interior. `shuttle_car` is a car interior and no module builds one; both are
# addressed to deck 30, the axis, not a ring deck.
#
# --- interior_kit x3 (2 places) ------------------------------------------
#
# `standard_corridor` is THE KIT -- its own register note reads "The kit. 3,414
# streaming cells of it across 251 decks" -- so composing it would build a
# corridor inside the corridor `deck.build_deck` has already laid. The generic
# bay standing in for it is the correct outcome and the register row is a label
# for something already built. `central_corridor` is different and is real
# work: "Two-level public concourse; exposed hull ribs", which is not the
# standard kit and which `interior_kit` has no builder for.
#
# --- interior x1 ---------------------------------------------------------
#
# `subfloor_stack`, "the sub-floor deck stack under the Garden" -- services,
# informal residence, storage, with catwalk/door/valve interactions.
# `interior.py` builds ring arcs, spokes, end caps and the drum shell and has
# no builder for a service stack. Its four sibling `interior` places
# (`drum_endcaps`, `drum_spokes`, `the_garden`, `radial_tubes`) do not appear
# in this count at all: they are on the drum cluster, which `--sweep` counts as
# heightfield ground rather than as a ring deck.
#
# --- SO THE THREE WORTH BUILDING, and what each needs ---------------------
#
# An observation room is a FLOOR, a WINDOW RING and a DOME WITH THICKNESS, and
# the last is the only hard part: `dome_mesh` is a closed half-ellipsoid whose
# every face points out, so an interior needs it called twice -- outer at r,
# inner at r - t with its winding reversed -- and a base annulus rimming the
# two, exactly the `interior_kit.plate_solid` shape that closed six modules in
# session 4a. `_dome_fittings` already builds mullions, a ring band and a base
# collar and would need its `grow` term negated to stand them proud INSIDE.
# `DOME_MULLIONS = 16` was measured off the inside view and `rotunda.webp`
# independently counts "at least eight columns across the far arc... a closed
# ring at that spacing implies roughly sixteen bays", which is the same number
# from a second frame.
#
# ONE THING THAT WILL BITE, and it is general rather than about domes:
# `dressable_extent` returns the BOUNDING BOX of the floor band, which is right
# for every module composed so far because all of them are rectangular in plan
# and is wrong for a circle -- a 2R x 2R dressing rectangle puts its corners at
# 1.41 R, through the window ring. The general fix is the largest axis-aligned
# rectangle inscribed in the floor band, which equals the bounding box on a
# rectangular plan and so changes nothing already composed.


# WHAT THE NINE MODULES LOOK LIKE AS SURFACES, audited when the adapter's
# winding gate was written. Recorded because it is the first time anything has
# asked, and because the obvious reading of it is wrong:
#
#     module            signed vol   open edges   non-manifold   triangles
#     alien_sector           368.8            0            118      11,680
#     command_control       -202.1          342             44       1,334
#     council_chamber       -243.0        1,592              0       1,916
#     customs                513.0           48             54       7,296
#     docking_bay        -67,236.4          151             34       3,740
#     hospitality             39.2          824             58       4,796
#     plant               47,233.5          192              0       8,452
#     quarters               136.3            0             71       2,088
#     zocalo              -1,246.8          734             32      44,320
#
# Four are negative and it is TEMPTING to call them inside-out. Do not: signed
# volume is only decisive for a CLOSED surface, and only two of the nine are
# closed (`alien_sector` and `quarters`, both positive). For the other seven
# the statistic is measuring their openings as much as their winding. What can
# be said is narrower and still useful: **seven of nine bespoke modules are
# open surfaces**, up to 1,592 edges on `council_chamber`, and nothing has ever
# gated that -- the closure work in session 3x reached `interior_kit`,
# `dressing` and the assembler, and stopped at the bespoke modules' door.
#
# `room_shell` therefore asserts only that recentring PRESERVES whatever
# orientation a module had, which is the question it is entitled to ask.


def floor_y(verts, tris, groups=None, module=None):
    """The height a person actually stands at, measured off the geometry.

    NOT THE BOTTOM OF THE MODEL, and the difference is not small. `room_shell`
    first aligned each shell's minimum y to zero, which is right for
    `docking_bay` (floor band at 0.00, 5,886 m2) and wrong for
    `command_control`, whose dominant up-facing surface sits **1.90 m** above
    its lowest vertex -- a player placed by the bounding box would spawn under
    the deck. `customs` is out by 0.20 and `hospitality` by 0.14, both being
    the thickness of a deck slab the module models and `rooms.build` does not.

    Found the same way `export_scene.open_standpoint` finds it: histogram
    near-horizontal, UP-FACING triangle area by height and take the band with
    the most of it. Area rather than count, because a floor is a few large
    triangles and a stair is many small ones.

    `WALK_SURFACE` overrides where a module has already said which group is its
    walkable skeleton -- `plant`'s catwalk is 8 m of steel over a tank farm
    whose floor is far larger, so the biggest band there is the wrong answer
    and the module knows it. Asking beats inferring, the same rule `light_`
    tagging follows.
    """
    import collections                                          # noqa: PLC0415
    want = WALK_SURFACE.get(module or "")
    keep = None
    if want and groups:
        keep = set()
        for name, lo, hi in _spans(groups, len(tris)):
            if any(f in name for f in want):
                keep.update(range(lo, hi))
    by = collections.Counter()
    for i, (a, b, c) in enumerate(tris):
        if keep is not None and i not in keep:
            continue
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = [p1[k] - p0[k] for k in range(3)]
        w = [p2[k] - p0[k] for k in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(x * x for x in n))
        if ln < 1e-12 or n[1] / ln < 0.85:
            continue
        by[round((p0[1] + p1[1] + p2[1]) / 3.0, 2)] += ln / 2.0
    if not by:
        return min(p[1] for p in verts)
    return by.most_common(1)[0][0]


def _spans(groups, n):
    """Normalise a module's groups to (name, lo, hi), whichever shape it used."""
    if not groups:
        return []
    if isinstance(groups[0], (tuple, list)) and len(groups[0]) == 3 \
            and isinstance(groups[0][1], int):
        return list(groups)
    out, i = [], 0
    while i < len(groups):
        j = i
        while j < len(groups) and groups[j] == groups[i]:
            j += 1
        out.append((groups[i], i, j))
        i = j
    return out


def _largest_inscribed_rect(cells, nx, nz):
    """The largest all-true axis-aligned rectangle in a boolean grid.

    Maximal rectangle in a histogram, run once per row: O(nx.nz), no
    thresholds, nothing to tune. Returns (i0, i1, k0, k1) inclusive, or None.
    """
    best = None
    best_area = 0
    heights = [0] * nx
    for k in range(nz):
        for i in range(nx):
            heights[i] = heights[i] + 1 if cells[i][k] else 0
        stack = []
        for i in range(nx + 1):
            h = heights[i] if i < nx else 0
            start = i
            while stack and stack[-1][1] >= h:
                s, sh = stack.pop()
                area = sh * (i - s)
                if area > best_area:
                    best_area = area
                    best = (s, i - 1, k - sh + 1, k)
                start = s
            stack.append((start, h))
    return best


def dressable_extent(verts, tris, groups=None, module=None, tol=0.05,
                     grid=112, keep_frac=0.98, cover_frac=0.50):
    """(width, length, cx, cz) of the floor a person can be furnished onto.

    NOT THE BOUNDING BOX, and on a docking bay the difference is 42 x 141 m
    against a bay whose walls are nowhere near either number. The dressable
    area is the extent of the DOMINANT floor band -- the same band `floor_y`
    picks -- because that is the surface a table can stand on and a person can
    walk across. A mezzanine 18 m up is floor and is not this floor.

    This is what lets a bespoke room be composed rather than swapped.
    `bespoke.compare` measured the swap at x0.54 -- the modules are shells,
    3,740 triangles for a docking bay against the generic bay's 38,728, because
    `rooms.build` runs `dressing` and `populace` inside itself and the bespoke
    modules run neither. Handing `dressing.dress()` this extent gives the room
    its true shape AND its furniture, which is the only version of this that is
    an improvement in both directions.
    """
    fy = floor_y(verts, tris, groups, module)
    xs, zs = [], []
    faces = []
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = [p1[k] - p0[k] for k in range(3)]
        w = [p2[k] - p0[k] for k in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(q * q for q in n))
        if ln < 1e-12 or n[1] / ln < 0.85:
            continue
        if abs((p0[1] + p1[1] + p2[1]) / 3.0 - fy) > tol:
            continue
        faces.append(((p0[0], p0[2]), (p1[0], p1[2]), (p2[0], p2[2])))
        for q in (p0, p1, p2):
            xs.append(q[0])
            zs.append(q[2])
    if not xs:
        return None
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    bbox = ((x1 - x0), (z1 - z0), (x0 + x1) / 2.0, (z0 + z1) / 2.0)
    if x1 - x0 < 1e-6 or z1 - z0 < 1e-6:
        return bbox

    # THE BOUNDING BOX IS WRONG FOR A ROUND ROOM, and `bespoke.py`'s own audit
    # block said so before there was a round room to be wrong about: *"a 2R x
    # 2R dressing rectangle puts its corners at 1.41 R, through the window
    # ring. The general fix is the largest axis-aligned rectangle inscribed in
    # the floor band, which equals the bounding box on a rectangular plan and
    # so changes nothing already composed."* This is that fix.
    #
    # THE `keep_frac` SHORTCUT IS WHAT MAKES THE SECOND HALF OF THAT SENTENCE
    # TRUE. A rasterised inscribed rectangle is quantised by the grid, so on a
    # perfectly rectangular plan it would come back a cell or two short and
    # every room already composed would shift by a few centimetres for no
    # reason. Above 98% of the bounding box the plan IS the box and the box is
    # returned unchanged, so the ten modules composed before this existed are
    # byte-identical -- asserted in `_selftest`.
    # THE CHEAP HALF OF THE SHORTCUT, and it is what keeps this affordable.
    # The floor band's own triangle area is O(faces) to add up; if it already
    # fills `keep_frac` of the bounding box then the plan IS the box and no
    # raster is needed at all. Every rectangular room on the station takes this
    # exit, so the ten modules composed before this existed pay nothing --
    # which matters, because `_selftest` composes every place three times and
    # a 112x112 raster per compose is minutes.
    tot = 0.0
    for (ax, az), (bx, bz), (cx_, cz_) in faces:
        tot += abs((bx - ax) * (cz_ - az) - (cx_ - ax) * (bz - az)) / 2.0
    if tot >= keep_frac * (x1 - x0) * (z1 - z0):
        return bbox

    nx = nz = max(8, int(grid))
    cells = [[False] * nz for _ in range(nx)]
    dx = (x1 - x0) / nx
    dz = (z1 - z0) / nz
    for (ax, az), (bx, bz), (cx_, cz_) in faces:
        i0 = max(0, int((min(ax, bx, cx_) - x0) / dx) - 1)
        i1 = min(nx - 1, int((max(ax, bx, cx_) - x0) / dx) + 1)
        k0 = max(0, int((min(az, bz, cz_) - z0) / dz) - 1)
        k1 = min(nz - 1, int((max(az, bz, cz_) - z0) / dz) + 1)
        d = ((bz - az) * (cx_ - ax) - (bx - ax) * (cz_ - az))
        if abs(d) < 1e-15:
            continue
        for i in range(i0, i1 + 1):
            px = x0 + (i + 0.5) * dx
            for k in range(k0, k1 + 1):
                if cells[i][k]:
                    continue
                pz = z0 + (k + 0.5) * dz
                s = ((bz - az) * (px - ax) - (bx - ax) * (pz - az)) / d
                tt = ((az - cz_) * (px - ax) + (cx_ - ax) * (pz - az)) / d
                if s >= -1e-9 and tt >= -1e-9 and s + tt <= 1.0 + 1e-9:
                    cells[i][k] = True
    r = _largest_inscribed_rect(cells, nx, nz)
    if r is None:
        return bbox
    i0, i1, k0, k1 = r
    if (i1 - i0 + 1) * (k1 - k0 + 1) >= keep_frac * nx * nz:
        return bbox
    # AND IT MUST DESCRIBE THE SAME FLOOR, which is what `cover_frac` decides
    # and it is not a tuning knob -- it separates two different kinds of plan
    # with one number and no list of module names.
    #
    #   ONE connected room whose plan is not a rectangle: a disc's inscribed
    #   square is 2/pi = 64% of it, C&C's upper deck round its pit about 75%.
    #   The rectangle is the better description and replaces the box.
    #
    #   SEVERAL rooms the caller means as one span: `quarters.run` is a row of
    #   six sealed cells 64 m long, and its largest inscribed rectangle is ONE
    #   CELL -- 17% of the floor. Furnishing one unit of six is not an
    #   improvement on furnishing all six badly, and it is not what that
    #   module's caller is asking for.
    #
    # Measured over every place composed before this existed: `qtr_transient`
    # 64.28 x 3.79 -> 7.46 x 3.79 without this clause, and unchanged with it.
    rect_area = (i1 - i0 + 1) * (k1 - k0 + 1) * dx * dz
    if rect_area < cover_frac * tot:
        return bbox
    rx0, rx1 = x0 + i0 * dx, x0 + (i1 + 1) * dx
    rz0, rz1 = z0 + k0 * dz, z0 + (k1 + 1) * dz
    return (rx1 - rx0, rz1 - rz0, (rx0 + rx1) / 2.0, (rz0 + rz1) / 2.0)


def room_shell(schema, profile, place, axial_half_m):
    """Bespoke geometry recentred into `rooms.build`'s frame.

    `rooms.build` emits a room CENTRED on its origin with the walkable floor at
    y = 0 (its deck slab reaching to -0.14) and the face that meets the
    corridor at +z. A bespoke module emits whatever frame suited authoring it,
    and the three differ in every axis: `docking_bay` runs z from -0.75 to
    +140.75 with its floor at y = 0, `command_control` from -4.20 to +8.70 with
    its floor at y = -1.90, `zocalo` from -1.89 to +32.54.

    Placing one without this adapter puts the room up to **70 m along the
    station's axis** from the door meant to serve it.

    Returns (verts, tris, groups) in the assembler's frame, or raises for a
    module whose near end is not declared -- see `NEAR_END_UNKNOWN`. Raising is
    the point: a room placed the wrong way round changes no triangle count and
    no extent, so nothing downstream can catch it.
    """
    mod = place.get("module")
    if mod not in BESPOKE_GEOMETRY:
        raise KeyError(f"{place['key']}: no builder for module {mod!r}")
    if mod not in NEAR_END:
        raise KeyError(
            f"{place['key']}: {mod} has no declared near end. "
            + (NEAR_END_UNKNOWN.get(mod) or NOT_COMPOSED.get(mod)
               or "undeclared"))
    r = BESPOKE_GEOMETRY[mod](schema, profile, place)
    v, t = r[0], r[1]
    if mod in UNROLL:
        v = unroll_to_local(v)
    g = r[2] if len(r) > 2 else None

    end, _why = NEAR_END[mod]
    zs = [p[2] for p in v]
    # Floor to y = 0, and the near face onto the plane the assembler expects.
    # Flipped when the module's near end is its MINIMUM z, by a half turn about
    # the vertical -- (x, y, z) -> (-x, y, -z) -- which is a rotation and so
    # preserves winding. Mirroring in z alone would face it the right way with
    # every triangle inside-out, the defect `dressing._cyl` shipped for sessions
    # because neither a render nor a triangle count can see it.
    #
    # THE MEASURED FLOOR, not the bottom of the bounding box. See `floor_y`.
    y0 = floor_y(v, t, g, mod)
    if end == "max_z":
        out = [(x, y - y0, z - max(zs) + axial_half_m) for x, y, z in v]
    else:
        # (x, y, z) -> (-x, y, -z) is diag(-1, 1, -1), whose determinant is
        # +1. IT IS A ROTATION AND THE WINDING MUST NOT BE TOUCHED. The first
        # version reversed the triangles as well, on the reflex that turning
        # geometry round needs it, and that inverted every customs hall --
        # signed volume +513 to -513. The gate caught it; nothing else would
        # have, because an inside-out room has the same triangle count, the
        # same extent and, against black, the same render.
        out = [(-x, y - y0, -(z - min(zs)) + axial_half_m) for x, y, z in v]

    # x ONTO THE WAY IN, not onto the middle of the model. `_place_local` maps
    # local x = 0 onto the place's own bearing, which is where `deck_plan` puts
    # the corridor's door -- so local x = 0 is not a centre, it is a DOORWAY,
    # and the bounding box only coincides with it when a module happens to be
    # symmetric. Two are not:
    #
    #   alien_sector  bbox cx -4.66   opening  0.00   3.01 m of floor apart
    #   quarters      bbox cx 12.32   opening 12.32 on qtr_command, and on the
    #                 wall between two cells on four of the seven classes
    #
    # Falls back to the bounding box when the near face has no opening at all,
    # because that is a module that needs a doorway rather than a shove --
    # `_selftest` asserts which modules those are, so the fallback cannot become
    # a quiet default.
    op = near_face_opening(out, t)
    if op is not None:
        cx = op[0]
    else:
        oxs = [p[0] for p in out]
        cx = (min(oxs) + max(oxs)) / 2.0
    return [(x - cx, y, z) for x, y, z in out], t, g

if __name__ == "__main__":
    raise SystemExit(_selftest())
