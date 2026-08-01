"""Layer 7: what the station SOUNDS like, derived rather than composed.

CLAUDE.md's layer table has read `7  Audio  Ambience and event audio per
location  0` since it was written, and session 4d's ruling put it on the list
by name: *"no audio at all"*, against an owner standard that names *"the
sound"* in the same breath as the textures and the physics.

AN AMBIENCE IS A VIEW OF THE SIMULATION, NOT A LIBRARY OF LOOPS
---------------------------------------------------------------
This is `station/broadcast.py`'s move, applied to sound, and for the same
reason: content with a life of its own drifts from the station, and content
that is a *function* of the station cannot.

  * the crowd layer is `populace.occupancy` -- the same headcount that puts
    bodies in the room -- put through the diffuse-field equation. Three
    hundred people in the Zocalo are three hundred voices, and when a future
    session moves the density the murmur moves with it
  * how many of those are AWAKE comes from `npc/schedule.awake_fraction`
    weighted by the place's OWN species mix, so 03:00 in a Brakiri quarter is
    not 03:00 in a human one. `RHYTHMS["brakiri"]` says NIGHT DWELLERS at
    authority 4, and that fact reaches the ear without this file knowing it
  * the docking bay is loud when a liner is in, because `traffic.berths_in_use`
    says a liner is in
  * the customs hall's traffic layer is `traffic.hall_rate`, which on a liner
    day is 8.5 people a minute against a 0.28 background
  * the PA layer carries the lines `broadcast.audible_at` is already writing,
    so the tannoy is era-correct because `costume.ERA_EVENTS` says it is
  * the machinery layer is `rooms.FIXTURES[archetype]` -- the furnace stacks
    and plant columns a room is NAMED for -- radiating into the room's own
    measured surface area

Nothing below is a level someone liked the sound of. Every number in a bed
carries a `why` string naming what produced it, and `--report` prints them.

THE ACOUSTICS ARE THE SAME EQUATION TWICE, and that is deliberate
------------------------------------------------------------------
Crowd and machinery are both incoherent sources in a room, so both go through
the classical diffuse-field result

    Lp = Lw + 10 log10(4 / R),     R = S a_bar / (1 - a_bar)

with S taken from `density.budget_area`'s own surface formula so the room's
acoustics and the room's triangle budget describe the SAME box. A large,
absorbent, sparsely-populated hall comes out quiet for both layers without
either being told to, and a hard-surfaced corridor comes out live.

And the crowd absorbs itself: `a_bar` rises with occupancy at 0.4 sabins a
standing body, so a packed room does not go on getting louder at 10 log10(N)
for ever. That is why the Zocalo's 463 people at 13:00 are not 14 dB above its
185 at 03:00 -- see `--report`.

WHAT IS INVENTED, AND IT IS THE LEVELS
---------------------------------------
No frame of the show measures a sound pressure level, so every absolute number
here is authority 5 and logged: INV-260 (the level ladder), INV-261 (the
spoke-pass modulation), INV-262 (the compressor beat), INV-263 (the surface
absorption and the acoustic horizon), INV-264 (bulkhead transmission loss).
What is NOT invented is the shape: which place is louder than which, and at
what hour, falls out of modules that already existed.

THE WAVEFORMS ARE LOOP-EXACT BY CONSTRUCTION, NOT BY EDITING
-------------------------------------------------------------
Every stream is synthesised in a length-N circular buffer and every filter is
a multiply in the frequency domain, which is a CIRCULAR convolution. A signal
built that way is exactly periodic with period N, so the loop seam is not a
place two ends were faded together -- it is an ordinary sample boundary. The
gate measures that rather than trusting it: `seam_ratio` is the step across the
seam over the 99.9th percentile of the steps inside the loop, and it must be
<= 1. The negative control rebuilds one stream with a time-domain IIR instead
of the circular filter and the gate fires at ~40x.
"""

import json
import math
import os
import struct
import sys
import zlib

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)

import broadcast as bc                                          # noqa: E402
import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import populace as pop                                          # noqa: E402
import rooms as rm                                              # noqa: E402
import traffic as tf                                            # noqa: E402
from npc import schedule as sched                               # noqa: E402

OUT_DIR = os.path.join(_HERE, "generated", "audio")
DOCS = os.path.join(os.path.dirname(_HERE), "docs")
GAZETTEER = os.path.join(os.path.dirname(_HERE), "docs", "gazetteer",
                         "LIFE-SUPPORT-AND-INDUSTRY.md")


# ===========================================================================
# 1.  The level ladder -- INV-260
# ===========================================================================
# There is no sound reference for Babylon 5 anywhere in `reference/`, so the
# absolute levels are extrapolated and the derivation is the whole of their
# defence:
#
#   * NASA-STD-3001 caps CONTINUOUS noise in a crew habitable volume at 60 dBA
#     over 24 h. The ISS US Lab measures 60-65 dBA, which is a TOLERATED result
#     on a six-person research outpost, not a designed one.
#   * B5 is a civil station where a quarter of a million people LIVE. Its
#     design target is therefore terrestrial habitability, and the terrestrial
#     criterion for a dwelling is NC-30, about 35 dBA.
#   * A concourse is not a bedroom. NC-40, about 45 dBA, is the ordinary design
#     level for a public circulation space with a crowd in it.
#   * A plant deck is a WORKING space and is allowed the full 60 dBA the
#     standard permits -- which is the same class distinction
#     LIFE-SUPPORT-AND-INDUSTRY.md 3.1 already draws about water, arriving in a
#     second medium. Downbelow lives next to the compressors precisely because
#     nobody with a choice would.
#
# Overturned by: any dialogue or production note establishing a level, or a
# scene where a named space is audibly outside its class.
AIR_CLASS_DBA = {
    "living": 35.0,        # NC-30, a dwelling
    "quiet": 30.0,         # a sanctuary or a contemplation space, one class down
    "circulation": 45.0,   # NC-40, an occupied public space
    "working": 60.0,       # the NASA-STD-3001 continuous ceiling
}

# Which class a place is in, read off `directory.PLACES`' own function
# vocabulary rather than from a second list of place keys. First match wins.
AIR_CLASS_BY_FUNCTION = (
    ("quiet", ("quiet", "contemplation", "worship", "mortuary")),
    ("living", ("residence", "informal_residence", "short_stay")),
    ("working", ("power_generation", "power_distribution", "fabrication",
                 "air_handling", "waste_processing", "water_reclamation",
                 "coolant_loop", "coolant_transfer", "cooling",
                 "heat_rejection", "industry", "repair", "maintenance_access",
                 "rotation", "fuel_transfer", "microgravity_handling",
                 "cargo_handling", "atmosphere_plant")),
)

# A room ventilated for a dense crowd runs its ducts harder than one ventilated
# for two people. LIFE-SUPPORT-AND-INDUSTRY.md 2.2 derives ~7 M m3/h through
# ~3.4 M m3, i.e. about 2 volumes an hour in OCCUPIED space -- so the design
# air rate follows the design occupancy, and duct noise follows the rate. The
# reference density is the one the ladder's 45 dBA was set for: a circulation
# space at its own peak.
AIR_REF_PEAK_PER_M2 = 0.10       # 10 people per 100 m2, the circulation datum
AIR_RATE_EXPONENT = 10.0         # dB per decade of design air rate; a duct is
                                 # a broadband source and doubling flow is
                                 # about +3 dB, which is 10 dB a decade

# ---------------------------------------------------------------------------
# INV-261 -- the structure layer, and why the rotation cannot be HEARD
# ---------------------------------------------------------------------------
# canon/00-MASTER.md: "period 33.4716 s, 1.7926 rpm". That is 0.0299 Hz --
# twelve octaves below the bottom of hearing. The station's rotation is
# therefore INAUDIBLE and no ambience should contain it as a tone.
#
# What a body can perceive is the modulation. `interior.SPOKE_COUNT` is 3 (the
# Green rosette's three spokes at 120 degrees), so a fixed point on the ring
# sees a spoke pass three times a revolution: 0.0896 Hz, an 11.16 s cycle. The
# structure-borne rumble breathes at that rate, and that slow swell is the only
# thing in the mix that says you are standing on something that is turning.
ROTATION_PERIOD_S = 33.4716                       # canon/00-MASTER.md
SPOKE_COUNT = int(it.SPOKE_COUNT)                 # interior.py, not retyped
SPOKE_PASS_HZ = SPOKE_COUNT / ROTATION_PERIOD_S   # 0.08963 Hz
SPOKE_PASS_S = 1.0 / SPOKE_PASS_HZ                # 11.157 s

# The hull is one continuous body, so the rumble is THE SAME EVERYWHERE. That
# is the point of the layer and the self-test asserts it: it is what tells a
# player they are aboard a ship rather than in a building, and a rumble that
# changed room to room would say the opposite. Set below the 35 dBA living
# floor so it is a presence and not a noise.
STRUCTURE_DBA = 28.0
STRUCTURE_MOD_DEPTH = 0.35
# The one exception, and it is a bearing: a place whose declared function is
# `rotation` is standing ON the drive. Not a special case for a named room --
# any place that acquires the function acquires the noise.
STRUCTURE_BEARING_FN = "rotation"
STRUCTURE_BEARING_DB = 8.0

# ---------------------------------------------------------------------------
# INV-262 -- the compressor beat
# ---------------------------------------------------------------------------
# LIFE-SUPPORT-AND-INDUSTRY.md 2.3, verbatim: "the compressors are audible from
# Downbelow -- a low beat that is the reason nobody chooses to sleep there."
# The gazetteer says BEAT, which constrains the rate from both ends:
#   * it must be countable rather than pitched, so below ~20 Hz, and below the
#     ~4 Hz flutter rate above which a listener stops counting and starts
#     hearing roughness
#   * it must be relentless enough to keep somebody awake, which rules out
#     anything slower than about one every two seconds
# 0.75 Hz -- 45 strokes a minute -- sits in the middle of that 0.5-4 Hz window.
# Overturned by any depiction of the compressor deck with audio.
COMPRESSOR_BEAT_HZ = 0.75

# ---------------------------------------------------------------------------
# INV-263 -- surface absorption and the acoustic horizon
# ---------------------------------------------------------------------------
# The station's interior kit is metal panel, composite and glass: `materials.py`
# carries no soft surface in the corridor set at all. A hard-surfaced interior
# sits at a mean absorption coefficient around 0.15, and that is deliberately
# LIVE -- a station that sounded like a carpeted office would be the wrong
# station.
SURFACE_ALPHA = 0.15
# A standing person is about 0.4 m2 of absorption. This is what stops the crowd
# layer running away: a room fills up, its own absorption rises, and the
# reverberant level saturates. Standard occupancy figure.
PERSON_SABINS = 0.4
# A diffuse field only exists inside a coupled volume. `plant_zone` is 360 deg
# by 442 m and `downbelow` is 101,950 m2; treating either as ONE room gives a
# reverberant field over a volume no sound crosses. Each acoustic dimension is
# therefore clamped, exactly as `density.budget_area` clamps the visual extent
# to `sight_line_m` and for the same reason -- beyond it, the place is a series
# of coupled volumes rather than a room.
ACOUSTIC_EXTENT_M = 60.0

# ---------------------------------------------------------------------------
# INV-264 -- what gets through a bulkhead
# ---------------------------------------------------------------------------
# A pressure-rated station bulkhead is a heavy, sealed, double-skinned
# partition; terrestrial equivalents (a 200 mm concrete wall, a sealed steel
# pressure door) sit at Rw 50-55 dB. But a station is coupled STRUCTURALLY as
# well as through the air, and low-frequency plant noise travels in the frame,
# where the airborne rating does not apply. The effective figure for the low
# beat is therefore much worse than the airborne one, and 25 dB is what makes
# the gazetteer's own sentence true: the compressors ARE audible from Downbelow.
# Overturned by: a scene establishing that plant rooms are inaudible next door.
BULKHEAD_TL_DB = 25.0

# ---------------------------------------------------------------------------
# The crowd
# ---------------------------------------------------------------------------
# One talker at normal effort is 60 dBA at 1 m. In a free field
# Lp = Lw - 10 log10(4 pi r^2), so Lw = 60 + 11 = 71 dB. Standard figure.
TALKER_LW_DB = 71.0
# Not everyone in a room is speaking at any instant. The figure used in speech
# privacy work for a conversing group is about one third, and it is the right
# one here because `occupancy` counts BODIES, not conversations.
TALKING_SHARE = 1.0 / 3.0
# Below this many audible voices the murmur stops being a murmur and becomes
# individual people, which is a different stream and a different mood -- the
# owner's brief asks for isolation as well as crowding.
BABBLE_THRESHOLD = 12.0

# ---------------------------------------------------------------------------
# The machinery, by fixture
# ---------------------------------------------------------------------------
# `rooms.FIXTURES` is the machinery a room is NAMED for, and it is already
# per-archetype, so the machinery layer needs no place list of its own: the
# room that has furnace stacks in the geometry has furnace stacks in the sound.
# Sound powers are authority 5, ranked by what the object is: a furnace and a
# fume column move air, a partition and a cell divider do not move at all.
#
# `service_duct` AND `service_riser` ARE DELIBERATELY ABSENT, and the first
# version of this table had them at 74 and 70 dB Lw. That put **62 dBA of duct
# noise in the command staff's bedrooms** -- above the working-space ceiling,
# in a space INV-260 puts at 35 dBA. The bug is not the number, it is that the
# duct IS the air handling: the air layer already models the whole ventilation
# system by design class, so a duct counted here as well is the same physical
# plant counted twice, and the second count answers to nothing. They stay in
# `EMITTERS` below, where they belong -- the room's ventilation is the air
# layer, and standing under the duct is the duct.
FIXTURE_LW_DB = {
    "furnace_stack": 92.0,      # a combustion-scale plant item
    "plant_column": 86.0,       # a vertical process vessel with a pump on it
    "fume_column": 80.0,        # extract, so it is moving air by definition
    # -- THE LIGHT END WAS 12-14 dB TOO HOT AND THE MORGUE CAUGHT IT. At
    # `equipment_gantry` = 66 dB Lw, ten gantries put 58 dBA into a 530 m2
    # mortuary -- a space INV-260 classes `quiet` at 30 dBA, running at the
    # working-deck ceiling. 66 dB Lw is a fan-coil unit; a medical monitoring
    # gantry is small-appliance class, 50-55. The rest of the light end was
    # scaled to the same reference: 40 dB Lw is a thing that is technically
    # not silent, 55 is a thing with a fan in it, 85+ is plant.
    "equipment_gantry": 52.0,   # monitoring: a small fan and a beep
    "racking_run": 44.0,        # a rack is silent; this is its handling gear
    "gantry_rail": 54.0,
    "platform_edge": 50.0,      # a platform hums because a tram is coming
    "catenary_run": 58.0,       # this one really does hum
    "back_shelving": 40.0,
    "stall_frame": 40.0,
    "awning_rail": 40.0,
    "partition_screen": 36.0,
    "cell_divider": 36.0,
    "dais": 34.0,
    "screen_panel": 34.0,
}
FIXTURE_DEFAULT_LW_DB = 50.0
# Fixtures that are part of the ventilation system and are therefore ALREADY
# in the air layer. Listed rather than merely omitted so that a future session
# adding a duct-like fixture to `rooms.FIXTURES` has somewhere to put it, and
# so the self-test can assert none of them leaked back in.
AIR_SYSTEM_FIXTURES = ("service_duct", "service_riser")

# ---------------------------------------------------------------------------
# Water -- LIFE-SUPPORT-AND-INDUSTRY.md 3.3
# ---------------------------------------------------------------------------
# "A tap is a status symbol. The Zocalo sells water. Downbelow queues at a
# standpipe. The reflecting pool and the waterfall in the Garden's townscape
# ... conspicuous consumption in an environment where hygiene is rationed."
# So water is present exactly where a water PROP is declared, and it is louder
# where it is being shown off than where it is being queued for.
WATER_PROPS = {
    "pool_edge":           ("water_pool", 62.0),   # civic display: a waterfall
    "planter":             ("water_pool", 46.0),   # irrigation, intermittent
    "irrigation_control":  ("water_run", 54.0),
    "grow_rack":           ("water_run", 52.0),
    "standpipe":           ("water_run", 58.0),    # a queue and a running tap
    "shower":              ("water_run", 60.0),
}

# ---------------------------------------------------------------------------
# The port
# ---------------------------------------------------------------------------
# A docking bay is loud when a ship is in it, and `traffic.berths_in_use` says
# which. Empty, a bay is its own air handling and nothing else.
BAY_MACHINERY_LW_DB = 96.0       # clamps, cranes, an umbilical under load
BAY_FUNCTIONS = ("ship_arrival", "ship_departure", "ship_mooring",
                 "starfury_launch", "umbilical_service")
# A customs hall's noise is its queue, and the queue is `traffic.hall_rate`.
# One person a minute through a hall is a room with a desk in it; 8.5 a minute
# is a hall under load, which is where the shouting starts.
HALL_FUNCTIONS = ("immigration", "identicard_check", "contraband_search")
HALL_REF_PER_MIN = 0.5           # TRAFFIC-AND-CUSTOMS 5.4's per-hall background
HALL_SURGE_DB = 10.0             # dB per decade of rate over the background

# ---------------------------------------------------------------------------
# The tannoy
# ---------------------------------------------------------------------------
# `broadcast.PA_PLACES` decides where a voice reaches, so this file does not.
PA_IDLE_DBA = 26.0               # the horn's own hiss, under everything
PA_CALL_DBA = 68.0               # a port announcement over a crowd

LAYERS = ("air", "structure", "machinery", "crowd", "water", "traffic", "pa")


# ===========================================================================
# 2.  Room acoustics
# ===========================================================================

_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = it.load()
    return _SCHEMA


_GEOM_CACHE = {}


def room_geometry(place):
    """(surface m2, floor m2, height m) for a place, clamped to the horizon.

    The surface formula is `density.budget_area`'s, so the box the acoustics
    describe and the box the triangle budget describes are the same box. It is
    not imported from `density` because that module clamps to the VISUAL sight
    line; the acoustic horizon is a different number for a different reason and
    both are declared above.
    """
    key = place["key"]
    if key in _GEOM_CACHE:
        return _GEOM_CACHE[key]
    schema, profile = _schema()
    arc, ln, _r = rm.room_extent_m(schema, profile, place)
    h = rm.ceiling_m(place)
    arc = min(arc, ACOUSTIC_EXTENT_M)
    ln = min(ln, ACOUSTIC_EXTENT_M)
    surface = 2.0 * arc * ln + 2.0 * (arc + ln) * h
    _GEOM_CACHE[key] = (surface, arc * ln, h)
    return _GEOM_CACHE[key]


def room_constant(surface_m2, occupants=0.0):
    """R = S a / (1 - a), with the occupants' own absorption folded in.

    THE OCCUPANTS ARE WHY THE CROWD LAYER SATURATES. Bodies absorb: at 0.4
    sabins each, five hundred people in the Zocalo add 200 m2 of absorption to
    a room whose hard surfaces give about 1,600, so the reverberant field they
    generate is damped by the fact of their being there. Without this term a
    crowd goes on getting 3 dB louder every time it doubles for ever, which is
    both wrong and, in a mix, exhausting.
    """
    a_total = surface_m2 * SURFACE_ALPHA + occupants * PERSON_SABINS
    a_bar = min(0.95, a_total / max(surface_m2, 1.0))
    return max(1.0, surface_m2 * a_bar / (1.0 - a_bar))


def diffuse_lp(lw_db, surface_m2, occupants=0.0):
    """Reverberant sound pressure level from a sound power level in a room."""
    r = room_constant(surface_m2, occupants)
    return lw_db + 10.0 * math.log10(4.0 / r)


def db_sum(levels):
    """Add decibels the only way incoherent sources add."""
    lv = [x for x in levels if x is not None and x > -200.0]
    if not lv:
        return None
    return 10.0 * math.log10(sum(10.0 ** (x / 10.0) for x in lv))


# ===========================================================================
# 3.  Who is here, and are they awake
# ===========================================================================

_MIX_CACHE = {}
_AWAKE_CACHE = {}
_PEAK_CACHE = {}
_DAY_CACHE = {}
MIX_SAMPLES = 128


def _station_says(day, datum):
    """`broadcast.day` memoised.

    It rebuilds the whole manifest on every call -- 0.75 s -- and a bed asks
    what is audible here and now. 128 places x 24 hours is 2,300 rebuilds of
    one identical list. The memo is keyed on exactly the arguments that change
    it, so it cannot go stale the way a written-down copy would.
    """
    key = (day, datum)
    if key not in _DAY_CACHE:
        _DAY_CACHE[key] = bc.day(day, datum)
    return _DAY_CACHE[key]


def audible_here(place_key, hour, day, datum, window_h=0.25):
    """`broadcast.audible_at`, off the memoised manifest. Same rule, no rebuild.

    The window and the wrap-around distance are copied from `broadcast` rather
    than reimplemented differently -- and the self-test asserts this function
    agrees with `broadcast.audible_at` on a sample, so the copy cannot drift.
    """
    out = []
    for a in _station_says(day, datum):
        if place_key not in a["places"]:
            continue
        if a["hour"] is None:
            out.append(a)
            continue
        d = min(abs(a["hour"] - hour), abs(a["hour"] - hour + 24.0),
                abs(a["hour"] - hour - 24.0))
        if d <= window_h:
            out.append(a)
    return out


def species_mix(place_key):
    """The place's own species mix, sampled through `populace.species_for`.

    Sampled rather than read from a table because `species_for` is the function
    that decides which body actually gets placed in the room. A second copy of
    that rule would be a second thing to drift; hard rule 4.
    """
    if place_key in _MIX_CACHE:
        return _MIX_CACHE[place_key]
    counts = {}
    for i in range(MIX_SAMPLES):
        sp = pop.species_for(place_key, i, "audio")
        counts[sp] = counts.get(sp, 0) + 1
    mix = {k: v / float(MIX_SAMPLES) for k, v in counts.items()}
    _MIX_CACHE[place_key] = mix
    return mix


def awake_share(place_key, hour):
    """Fraction of the people here who are awake, weighted by the local mix.

    THIS IS WHERE 03:00 STOPS BEING A NUMBER AND BECOMES A PLACE. A human room
    at 03:00 is 26% awake; `schedule.RHYTHMS["brakiri"]` is flagged NIGHT
    DWELLERS at authority 4 and comes out 97%. So a Brakiri-heavy space keeps
    its crowd through the station night and a human one does not, and neither
    fact is written down here -- it arrives from the rhythm table.
    """
    hb = round(hour % 24.0, 3)
    key = (place_key, hb)
    if key in _AWAKE_CACHE:
        return _AWAKE_CACHE[key]
    tot = 0.0
    for sp, share in species_mix(place_key).items():
        ck = (sp, hb)
        if ck not in _AWAKE_CACHE:
            _AWAKE_CACHE[ck] = sched.awake_fraction(sp, hb)
        tot += share * _AWAKE_CACHE[ck]
    _AWAKE_CACHE[key] = tot
    return tot


# ===========================================================================
# 4.  The bed
# ===========================================================================

def _air_class(place):
    fns = set(place["functions"])
    for cls, keys in AIR_CLASS_BY_FUNCTION:
        if fns & set(keys):
            return cls
    return "circulation"


def _peak_occupancy(place, floor_m2, arch):
    """The design occupancy the ventilation was sized for: the day's maximum."""
    key = (place["key"], round(floor_m2, 3), arch)
    if key not in _PEAK_CACHE:
        _PEAK_CACHE[key] = max(pop.occupancy(place["key"], floor_m2, h, arch)
                               for h in range(24))
    return _PEAK_CACHE[key]


_MACHINERY_CACHE = {}


def machinery_lw(place, arch):
    """Total sound power of the fixtures `rooms.FIXTURES` puts in this room.

    Counts are derived the way `rooms` lays them out -- spine and over items
    repeat down the length at `FIXTURE_PITCH_M`, flank items repeat along both
    walls -- so a long hall full of furnaces is louder than a short one, and
    nothing has to say how many furnaces there are.
    """
    key = (place["key"], arch)
    if key in _MACHINERY_CACHE:
        return _MACHINERY_CACHE[key]
    _surface, _floor, _h = room_geometry(place)
    schema, profile = _schema()
    arc, ln, _r = rm.room_extent_m(schema, profile, place)
    arc, ln = min(arc, ACOUSTIC_EXTENT_M), min(ln, ACOUSTIC_EXTENT_M)
    parts = []
    for name, _w, _d, _ht, kind in rm.FIXTURES.get(arch, ()):
        if name in AIR_SYSTEM_FIXTURES:
            continue                    # already counted, as the air layer
        run = ln if kind in ("spine", "over") else arc
        n = max(1, int(run / rm.FIXTURE_PITCH_M))
        if kind == "flank":
            n *= 2
        lw = FIXTURE_LW_DB.get(name, FIXTURE_DEFAULT_LW_DB)
        parts.append((name, n, lw + 10.0 * math.log10(n)))
    total = db_sum([p[2] for p in parts])
    _MACHINERY_CACHE[key] = (total, parts)
    return _MACHINERY_CACHE[key]


_ADJ_INDEX = None


def _plant_neighbours(place):
    """Adjacent places whose machinery leaks in through the bulkhead.

    LIFE-SUPPORT-AND-INDUSTRY.md 2.3 says the compressors are audible from
    Downbelow. `directory` already records `downbelow.adjacent = ('plant_zone',)`
    and `plant_zone` is an `industrial` archetype, so the gazetteer's sentence
    comes out of the register instead of being asserted here.
    """
    global _ADJ_INDEX
    if _ADJ_INDEX is None:
        _ADJ_INDEX = {p["key"]: p for p in dr.PLACES}
    out = []
    for k in place["adjacent"]:
        nb = _ADJ_INDEX.get(k)
        if nb is None:
            continue
        if rm.archetype(nb) == "industrial":
            out.append(nb)
    return out


_BERTH_AREA = None


def _berth_floor_total():
    """Every square metre of the station that a ship can be berthed against."""
    global _BERTH_AREA
    if _BERTH_AREA is None:
        schema, profile = _schema()
        tot = 0.0
        for p in dr.PLACES:
            if set(p["functions"]) & set(BAY_FUNCTIONS):
                arc, ln, _r = rm.room_extent_m(schema, profile, p)
                tot += arc * ln
        _BERTH_AREA = max(tot, 1.0)
    return _BERTH_AREA


def berths_audible(place, hour, day):
    """Expected number of berthed ships inside the acoustic horizon with you.

    `traffic.berths_in_use` is a STATION-WIDE count and the first version of
    this layer handed all of it to every berth. `vorlon_berth` -- one ship, in
    a 1,477 m2 room -- came out the loudest place on the station at **88.8
    dBA**, because a single berth was hearing all 32 ships alongside. It was
    the loudest bed in the manifest, which is how it was found: the master trim
    is derived from that maximum, so one wrong bed set the gain for the whole
    station.

    The right quantity is one line of geometry: the station's berthed ships,
    spread over the station's berthing floor, times the patch of that floor
    inside your horizon. `room_geometry` has already clamped the patch to
    ACOUSTIC_EXTENT_M on both axes, so a 1,395 m bay row contributes its 60 m
    of itself and a single berth contributes all of its small self.
    """
    _s, floor, _h = room_geometry(place)
    n_all = sum(tf.berths_in_use(hour, day).values())
    return n_all * floor / _berth_floor_total(), n_all


def _traffic_layer(place, hour, day):
    """The port, when the port is doing something."""
    fns = set(place["functions"])
    surface, _floor, _h = room_geometry(place)
    if fns & set(BAY_FUNCTIONS):
        use = tf.berths_in_use(hour, day)
        n, n_all = berths_audible(place, hour, day)
        if n_all <= 0 or n < 1e-3:
            return None, "no berth occupied within the acoustic horizon", {}
        lw = BAY_MACHINERY_LW_DB + 10.0 * math.log10(n)
        return (diffuse_lp(lw, surface),
                f"{n_all} berth(s) alongside station-wide "
                f"(traffic.berths_in_use); {n:.2f} expected inside this "
                f"place's {ACOUSTIC_EXTENT_M:.0f} m horizon, at "
                f"{BAY_MACHINERY_LW_DB:.0f} dB Lw each",
                dict(use, audible=round(n, 3)))
    if fns & set(HALL_FUNCTIONS):
        r = tf.hall_rate(hour, day)
        rate = max(r["total_per_min"], 1e-4)
        over = HALL_SURGE_DB * math.log10(rate / HALL_REF_PER_MIN)
        return (45.0 + over,
                f"traffic.hall_rate {rate:.2f}/min, x{r['multiple']:.1f} the "
                f"background", {"per_min": rate, "multiple": r["multiple"]})
    return None, "", {}


def bed(place_key, hour, day=0, datum=None):
    """The complete ambience bed for one place at one hour of one day.

    Returns every layer with its level in dBA and the reason it is that level.
    Nothing is cached across hours: the whole point is that the same room at
    two hours is two beds.
    """
    place = dr.by_key(place_key)
    arch = rm.archetype(place)
    surface, floor, height = room_geometry(place)
    layers = []

    def add(name, stream, db, why, **extra):
        if db is None:
            return
        layers.append(dict(layer=name, stream=stream, db=round(db, 2),
                           why=why, **extra))

    # -- air handling ----------------------------------------------------
    cls = _air_class(place)
    base = AIR_CLASS_DBA[cls]
    peak = _peak_occupancy(place, floor, arch)
    dens = peak / max(floor, 1.0)
    rate_db = AIR_RATE_EXPONENT * math.log10(
        max(dens, 1e-4) / AIR_REF_PEAK_PER_M2)
    rate_db = max(-8.0, min(8.0, rate_db))
    air_db = base + rate_db
    add("air", AIR_STREAM_BY_CLASS[cls], air_db,
        f"INV-260 {cls} class {base:.0f} dBA, {rate_db:+.1f} dB for a design "
        f"occupancy of {peak} in {floor:.0f} m2 "
        f"({dens:.3f}/m2 vs {AIR_REF_PEAK_PER_M2:.2f} datum)",
        air_class=cls)

    # -- structure -------------------------------------------------------
    st = STRUCTURE_DBA
    why = (f"INV-261: the hull is one body, so this is the same everywhere. "
           f"Breathes at the {SPOKE_COUNT}-per-rev spoke pass, "
           f"{SPOKE_PASS_HZ:.4f} Hz / {SPOKE_PASS_S:.2f} s")
    if STRUCTURE_BEARING_FN in place["functions"]:
        st += STRUCTURE_BEARING_DB
        why += f"; +{STRUCTURE_BEARING_DB:.0f} dB -- this place IS the bearing"
    add("structure", "structure_hull", st, why)

    # -- machinery -------------------------------------------------------
    own_lw, parts = machinery_lw(place, arch)
    own = diffuse_lp(own_lw, surface) if own_lw is not None else None
    mwhy = (f"rooms.FIXTURES[{arch!r}] = "
            + ", ".join(f"{n}x{c}" for n, c, _ in parts)
            + f" -> {own_lw:.1f} dB Lw into R={room_constant(surface):.0f} m2"
            if parts else "no fixtures declared for this archetype")
    leaked = []
    for nb in _plant_neighbours(place):
        nlw, _p = machinery_lw(nb, rm.archetype(nb))
        if nlw is None:
            continue
        nsurf, _f, _h = room_geometry(nb)
        leaked.append((nb["key"], diffuse_lp(nlw, nsurf) - BULKHEAD_TL_DB))
    if leaked:
        best = max(leaked, key=lambda x: x[1])
        if own is None or best[1] > own:
            mwhy = (f"{best[0]} next door at {best[1] + BULKHEAD_TL_DB:.1f} "
                    f"dBA, less INV-264's {BULKHEAD_TL_DB:.0f} dB bulkhead -- "
                    f"LIFE-SUPPORT-AND-INDUSTRY.md 2.3's own sentence")
        own = db_sum([own, best[1]])
    add("machinery", MACHINE_STREAM_BY_ARCH.get(arch, "machine_hum"), own,
        mwhy, fixtures=[(n, c) for n, c, _ in parts])

    # -- crowd -----------------------------------------------------------
    heads = pop.occupancy(place_key, floor, hour, arch)
    awake = awake_share(place_key, hour)
    voices = heads * awake * TALKING_SHARE
    if voices > 0.05:
        lw = TALKER_LW_DB + 10.0 * math.log10(voices)
        crowd_db = diffuse_lp(lw, surface, occupants=heads * awake)
        stream = ("crowd_babble" if voices >= BABBLE_THRESHOLD
                  else "crowd_sparse")
        mix = species_mix(place_key)
        top = sorted(mix.items(), key=lambda kv: -kv[1])[:3]
        add("crowd", stream, crowd_db,
            f"populace.occupancy {heads} bodies x {awake:.2f} awake x "
            f"{TALKING_SHARE:.2f} talking = {voices:.1f} voices at "
            f"{TALKER_LW_DB:.0f} dB Lw; mix "
            + ", ".join(f"{s} {f:.0%}" for s, f in top),
            heads=heads, awake=round(awake, 3), voices=round(voices, 2))

    # -- water -----------------------------------------------------------
    wat = [(WATER_PROPS[k][0], WATER_PROPS[k][1], k)
           for k in place["interacts"] if k in WATER_PROPS]
    if wat:
        stream = max(wat, key=lambda w: w[1])[0]
        lw = db_sum([w[1] for w in wat])
        add("water", stream, diffuse_lp(lw, surface),
            "declared water props "
            + ", ".join(w[2] for w in wat)
            + f" -> {lw:.1f} dB Lw; LIFE-SUPPORT-AND-INDUSTRY.md 3.3")

    # -- traffic ---------------------------------------------------------
    tdb, twhy, tex = _traffic_layer(place, hour, day)
    add("traffic", TRAFFIC_STREAM_BY_FN(place), tdb, twhy, detail=tex)

    # -- public address --------------------------------------------------
    calls = audible_here(place_key, hour, day, datum)
    live = [c for c in calls if c["hour"] is not None]
    if place_key in bc.PA_PLACES:
        add("pa", "pa_horn", PA_IDLE_DBA,
            "broadcast.PA_PLACES -- the horn is live even when silent")
    if live:
        layers.append(dict(
            layer="pa", stream="pa_chime", db=round(PA_CALL_DBA, 2),
            why=f"broadcast.audible_at: {len(live)} call(s) in window",
            event=True, calls=[c["text"] for c in live]))

    # STEADY AND EVENT ARE SEPARATED, and the first version did not separate
    # them. A port announcement at 68 dBA is 6 dB over the Zocalo's busiest
    # crowd, so with the chime folded into one total the room's day-night
    # difference read +1.82 dB when the CROWD LAYER ITSELF was moving +6.3 --
    # the gate was measuring whether the tannoy happened to fire in that
    # quarter-hour. An ambience is the steady bed; a call is an event on top.
    event = [x for x in layers if x.get("event")]
    steady = [x for x in layers if not x.get("event")]
    total = db_sum([x["db"] for x in layers])
    return dict(place=place_key, name=place["name"], hour=round(hour % 24, 3),
                day=day, archetype=arch, air_class=cls,
                floor_m2=round(floor, 1), surface_m2=round(surface, 1),
                height_m=round(height, 2),
                room_constant_m2=round(room_constant(surface, heads * awake), 1),
                layers=layers,
                total_dba=round(total, 2) if total else None,
                steady_dba=round(db_sum([x["db"] for x in steady]), 2),
                event_dba=(round(db_sum([x["db"] for x in event]), 2)
                           if event else None))


def total_dba(place_key, hour, day=0):
    """The STEADY bed. `bed()['total_dba']` includes any live announcement."""
    return bed(place_key, hour, day)["steady_dba"]


# ===========================================================================
# 5.  The stream bank
# ===========================================================================
# One shared bank of loop-exact streams; the bed sets their levels. 128 places
# x 24 hours of pre-mixed audio would be gigabytes and would also be a SECOND
# description of the levels, which is the drift this project keeps paying for.

RATE = 32000                    # Nyquist 16 kHz; there is nothing above it in
                                # a duct, a crowd or a plant deck
BITS = 16

AIR_STREAM_BY_CLASS = {"living": "air_plenum", "quiet": "air_plenum",
                       "circulation": "air_duct", "working": "air_duct"}
MACHINE_STREAM_BY_ARCH = {
    "industrial": "plant_beat", "store": "machine_hum",
    "transit": "dock_machinery", "medical": "machine_hum",
    "research": "machine_hum", "office": "machine_hum",
    "commerce": "machine_hum", "hospitality": "machine_hum",
    "detention": "machine_hum", "worship": "machine_hum",
    "generic": "machine_hum",
}


def TRAFFIC_STREAM_BY_FN(place):
    fns = set(place["functions"])
    return "dock_machinery" if fns & set(BAY_FUNCTIONS) else "crowd_babble"


# (name, seconds, band-limits for the spectral gate in Hz, builder)
# The band is what the stream CLAIMS to be, and the gate measures its actual
# spectral centroid against it. Swapping two rows makes the gate fire; that is
# the negative control.
#
# THREE OF THESE FAILED ON THE FIRST RUN AND THE BUILDS WERE CHANGED, NOT THE
# BANDS. `crowd_babble` came out at 1,683 Hz against a speech long-term average
# spectrum that sits near 700; `water_run` at 7,134 Hz, which is a hiss and not
# a tap; `air_alien` at 3,455, brighter than a shower. Widening a band to admit
# the stream you happened to build is the "grow the gate" move this repository
# has a rule against, so the tilts were corrected instead.
STREAM_BANDS = {
    "air_duct":       (700.0, 2400.0),
    "air_plenum":     (90.0, 700.0),
    "air_alien":      (1500.0, 4000.0),
    "structure_hull": (18.0, 120.0),
    "plant_beat":     (35.0, 260.0),
    "machine_hum":    (90.0, 900.0),
    "dock_machinery": (60.0, 600.0),
    "crowd_babble":   (450.0, 1200.0),   # speech LTAS, not white noise
    "crowd_sparse":   (450.0, 1900.0),
    "water_run":      (2200.0, 5500.0),
    "water_pool":     (700.0, 5000.0),
    "pa_horn":        (400.0, 4000.0),
    "pa_chime":       (500.0, 1800.0),
}


def _cycles(freq_hz, n):
    """Nearest whole number of cycles of `freq_hz` in an n-sample buffer.

    EVERY periodic component goes through this. A modulator at a frequency that
    does not divide the buffer is the single easiest way to make a loop click,
    and rounding here is what makes the seam gate pass by construction rather
    than by luck.
    """
    return max(1, int(round(freq_hz * n / float(RATE))))


def _phase(n, cycles, rng):
    return 2.0 * np.pi * (cycles * np.arange(n) / float(n)
                          + rng.uniform(0.0, 1.0))


def _spectral_noise(n, rng, tilt_db_oct=-3.0, lo=20.0, hi=16000.0, order=4):
    """Band-limited noise built in the frequency domain -- loop-exact.

    Random phase on every bin of a length-N spectrum, inverse transformed. The
    result is EXACTLY periodic with period N because that is what a DFT of
    length N means. There is no crossfade and no editing anywhere in this file.
    """
    k = np.fft.rfftfreq(n, 1.0 / RATE)
    kk = np.maximum(k, 1e-9)
    mag = 10.0 ** (tilt_db_oct * np.log2(kk / 1000.0) / 20.0)
    mag /= np.sqrt(1.0 + (lo / kk) ** order)
    mag /= np.sqrt(1.0 + (kk / hi) ** order)
    ph = rng.uniform(0.0, 2.0 * np.pi, k.shape)
    spec = mag * np.exp(1j * ph)
    spec[0] = 0.0
    if n % 2 == 0:
        spec[-1] = np.abs(spec[-1])
    return np.fft.irfft(spec, n)


def _circular_filter(x, lo=None, hi=None, order=4):
    """Filter by multiplying the spectrum -- a CIRCULAR convolution.

    This is the whole loop-exactness argument in one function. A time-domain
    IIR has state that does not wrap, so its output is not periodic and its
    seam clicks; a spectral multiply wraps by definition. `_selftest` runs the
    IIR version as its negative control and the seam gate fires at ~40x.
    """
    n = len(x)
    k = np.fft.rfftfreq(n, 1.0 / RATE)
    kk = np.maximum(k, 1e-9)
    h = np.ones_like(kk)
    if lo:
        h /= np.sqrt(1.0 + (lo / kk) ** order)
    if hi:
        h /= np.sqrt(1.0 + (kk / hi) ** order)
    return np.fft.irfft(np.fft.rfft(x) * h, n)


def _impulse_train(n, rng, count, decay_s, lo, hi):
    """Random transients, filtered circularly so a wrapped one is still exact.

    A drip near the end of the buffer wraps into the beginning, which for a
    LOOP is not an artefact -- it is the correct behaviour, and it is only
    correct because the filtering is circular.
    """
    x = np.zeros(n)
    idx = rng.integers(0, n, size=count)
    amp = rng.uniform(0.3, 1.0, size=count)
    for i, a in zip(idx, amp):
        x[i] += a
    env = np.exp(-np.arange(n) / (decay_s * RATE))
    y = np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(env), n)
    return _circular_filter(y, lo=lo, hi=hi)


def _am(n, rng, freq_hz, depth, shape=1.0):
    c = _cycles(freq_hz, n)
    s = 0.5 + 0.5 * np.sin(_phase(n, c, rng))
    return 1.0 - depth + depth * (s ** shape)


def _build_streams():
    """Every stream, with the reason it sounds like that in its own entry."""
    out = {}

    def secs(s):
        return int(round(s * RATE))

    r = np.random.default_rng

    # -- air: a duct is broadband hiss, a plenum is what is left of it after
    #    a long run of lined trunk. Both are pink-ish; the plenum is rolled off
    #    because distance and duct lining eat the top two octaves.
    n = secs(6.0)
    out["air_duct"] = dict(
        x=_spectral_noise(n, r(101), -3.5, lo=120.0, hi=6000.0)
        * _am(n, r(102), 0.19, 0.10),
        why="pink noise, 120 Hz-6 kHz, breathing at 0.19 Hz -- a supply duct "
            "close to its diffuser")
    out["air_plenum"] = dict(
        x=_spectral_noise(n, r(103), -6.0, lo=45.0, hi=900.0)
        * _am(n, r(104), 0.11, 0.08),
        why="brown noise rolled off at 900 Hz -- the same air two rooms away, "
            "which is what a dwelling gets (INV-260's living class)")
    out["air_alien"] = dict(
        x=_spectral_noise(n, r(105), -3.0, lo=350.0, hi=4200.0)
        * _am(n, r(106), 0.31, 0.22),
        why="LIFE-SUPPORT-AND-INDUSTRY.md 2.3: 'crossing into the Alien Sector "
            "should change the ambience track ... before any sign says so'. "
            "Brighter, faster, and a different gas")

    # -- structure: the rotation is 0.0299 Hz and cannot be heard. What can be
    #    heard is very low broadband breathing at the 3-per-rev spoke pass, and
    #    the loop is exactly one spoke-pass period long so the swell is whole.
    n = secs(SPOKE_PASS_S)
    rr = r(107)
    base = _spectral_noise(n, rr, -9.0, lo=14.0, hi=180.0)
    for f, a in ((23.0, 0.5), (31.0, 0.3), (47.0, 0.18)):
        base += a * 0.25 * np.sin(_phase(n, _cycles(f, n), rr))
    out["structure_hull"] = dict(
        x=base * _am(n, r(108), SPOKE_PASS_HZ, STRUCTURE_MOD_DEPTH),
        why=f"INV-261. Loop length is one spoke-pass period exactly "
            f"({SPOKE_PASS_S:.3f} s = {n} samples), so the swell is whole and "
            f"the rotation is present as MODULATION, never as a tone")

    # -- machinery
    n = secs(8.0)                       # exactly six compressor strokes
    rr = r(109)
    beat = _spectral_noise(n, rr, -5.0, lo=30.0, hi=700.0)
    beat *= _am(n, rr, COMPRESSOR_BEAT_HZ, 0.62, shape=2.5)
    for f, a in ((58.0, 0.45), (116.0, 0.22), (174.0, 0.10)):
        beat += a * 0.2 * np.sin(_phase(n, _cycles(f, n), rr))
    out["plant_beat"] = dict(
        x=beat,
        why=f"INV-262's {COMPRESSOR_BEAT_HZ} Hz beat over a 58 Hz shaft line "
            f"and its harmonics. 8.000 s is exactly "
            f"{COMPRESSOR_BEAT_HZ * 8:.0f} strokes")
    n = secs(6.0)
    rr = r(110)
    hum = _spectral_noise(n, rr, -6.0, lo=60.0, hi=1200.0) * 0.55
    for f, a in ((100.0, 1.0), (200.0, 0.35), (300.0, 0.12)):
        hum += a * 0.16 * np.sin(_phase(n, _cycles(f, n), rr))
    out["machine_hum"] = dict(
        x=hum * _am(n, r(111), 0.5, 0.06),
        why="100 Hz and harmonics -- fittings, fans and cabinets. The sound of "
            "a room with equipment in it and no plant")
    n = secs(8.0)
    rr = r(112)
    dock = _spectral_noise(n, rr, -7.0, lo=35.0, hi=900.0)
    dock *= _am(n, rr, 0.13, 0.45, shape=1.6)
    dock += 0.35 * _impulse_train(n, r(113), 9, 0.55, 60.0, 1400.0)
    out["dock_machinery"] = dict(
        x=dock,
        why="low broadband under clamp and crane transients. The bay is not "
            "steady: things land in it")

    # -- crowd
    n = secs(8.0)
    rr = r(114)
    # -7 dB/oct is the long-term average spectrum of speech, which is what a
    # room full of talking actually measures. Flat noise reads as air, not
    # people, and the centroid gate says so.
    band = _spectral_noise(n, rr, -7.0, lo=220.0, hi=3200.0)
    env = np.zeros(n)
    for f in (2.9, 4.3, 5.7, 7.1, 9.3):
        env += _am(n, rr, f, 1.0, shape=1.4)
    env = 0.35 + 0.65 * (env / env.max())
    out["crowd_babble"] = dict(
        x=_circular_filter(band * env, lo=250.0, hi=4000.0),
        why="speech-band noise under five incommensurate syllable rates -- a "
            "murmur, which is what more than "
            f"{BABBLE_THRESHOLD:.0f} voices in a room actually is")
    rr = r(115)
    band = _spectral_noise(n, rr, -5.0, lo=220.0, hi=4000.0)
    sparse = band * (0.06 + 0.94 * (_am(n, rr, 0.37, 1.0, shape=6.0)))
    sparse += 0.12 * _impulse_train(n, r(116), 5, 0.18, 400.0, 5000.0)
    out["crowd_sparse"] = dict(
        x=sparse,
        why="the same band, gated hard. Below the babble threshold you hear "
            "PEOPLE rather than a crowd, and the gaps are the isolation the "
            "owner's brief asks for")

    # -- water
    n = secs(6.0)
    rr = r(117)
    run = _spectral_noise(n, rr, -2.5, lo=900.0, hi=6500.0)
    run *= _am(n, rr, 1.17, 0.18)
    out["water_run"] = dict(
        x=run,
        why="high band-limited noise, gently modulated -- a standpipe, and "
            "LIFE-SUPPORT-AND-INDUSTRY.md 3.3's queue for it")
    rr = r(118)
    pool = _spectral_noise(n, rr, -0.5, lo=600.0, hi=8000.0) * 0.7
    pool *= _am(n, rr, 0.41, 0.25)
    pool += 0.45 * _impulse_train(n, r(119), 40, 0.09, 900.0, 9000.0)
    out["water_pool"] = dict(
        x=pool,
        why="broader noise plus forty drips -- the Garden's reflecting pool "
            "and waterfall, authority 1 (garden.png), which 3.3 calls "
            "conspicuous consumption")

    # -- public address
    n = secs(4.0)
    rr = r(120)
    out["pa_horn"] = dict(
        x=_spectral_noise(n, rr, -1.0, lo=350.0, hi=5000.0)
        * _am(n, rr, 1.0, 0.05),
        why="the horn's own hiss. A live tannoy is never silent, and a player "
            "who notices it has noticed the station is talking to them")
    n = secs(2.0)
    rr = r(121)
    t = np.arange(n) / float(RATE)
    chime = np.zeros(n)
    # THE ENVELOPES MUST BE WHOLLY INSIDE THE BUFFER and the first version's
    # were not: the leading tone was centred at 0.25 s with a 0.32 s half-width
    # and so was already at 0.055 amplitude AT SAMPLE ZERO. The pump gate read
    # +33.3 dB. On a one-shot that is not a loop artefact, it is a click every
    # time the tannoy fires -- which is the single most-triggered sound in the
    # station. Centres 0.45 and 0.95 s, half-width 0.35, both clear of 0 and 2.
    for i, f in enumerate((880.0, 1174.0)):
        c = _cycles(f, n)
        seg = np.sin(2.0 * np.pi * c * np.arange(n) / float(n))
        g = np.clip(1.0 - np.abs(t - (0.45 + 0.50 * i)) / 0.35, 0.0, 1.0) ** 2
        chime += seg * g
    out["pa_chime"] = dict(
        x=_circular_filter(chime, lo=400.0, hi=6000.0),
        why="two tones, A5 and D6, envelopes wholly inside the buffer so the "
            "one-shot starts and ends at silence")

    return out


# ===========================================================================
# 6.  Measurement -- the gates measure the file, not the intention
# ===========================================================================

SEAM_ENV_MS = 20.0
SEAM_ENV_DB = 3.0        # a level step this size at a loop join is audible as
                         # a pump once a pass; 3 dB is the classic JND


def seam(x):
    """How big the loop join is, measured two ways, because ONE IS NOT ENOUGH.

    1. `ratio` -- the sample step across the join over the 99.9th percentile
       of the steps inside the loop. This is the CLICK test, and it is the
       right one for a smooth signal.

    2. `env_db` -- the short-term level of the first 20 ms against the last
       20 ms. This is the PUMP test, and it exists because the first version of
       this gate had only the click test and a deliberately broken control
       walked straight through it.

       The control was a stream whose amplitude envelope jumps from 0.5 to 1.0
       across the join -- 6 dB, plainly wrong -- and `ratio` read **0.097, a
       comfortable pass**. It is not a fault in the control: for broadband
       noise adjacent samples are already nearly uncorrelated, so a step across
       the join is statistically indistinguishable from any other step, and no
       sample-level statistic can see an envelope discontinuity in noise.
       What a listener hears there is not a click, it is a surge once a loop.

    Two artefacts, two mechanisms, two measurements. Neither subsumes the other
    and the negative controls fire on one each.
    """
    d = np.abs(np.diff(x))
    p999 = float(np.percentile(d, 99.9))
    step = float(abs(x[0] - x[-1]))
    d2 = np.abs(np.diff(x, 2))
    p999_2 = float(np.percentile(d2, 99.9))
    step2 = float(abs((x[0] - x[-1]) - (x[-1] - x[-2])))
    # THE ENVELOPE WINDOW HAS TO BE DERIVED FROM THE SIGNAL, and a fixed 20 ms
    # was wrong on two shipped streams. `structure_hull` runs down to 14 Hz and
    # `air_plenum` to 45; a 20 ms window is a quarter of a cycle at 14 Hz, so
    # "the RMS of the first 20 ms" is really "where in the bass cycle the
    # buffer happens to start", and both read a pump of 5-11 dB while being
    # perfectly continuous. The window is therefore at least four periods of
    # the stream's own 5th-percentile frequency -- measured off the spectrum,
    # never written down, which is hard rule 4 applied to a gate.
    p = np.abs(np.fft.rfft(x)) ** 2
    k = np.fft.rfftfreq(len(x), 1.0 / RATE)
    cum = np.cumsum(p) / max(p.sum(), 1e-30)
    f5 = float(k[int(np.searchsorted(cum, 0.05))]) if p.sum() > 0 else 1000.0
    w = int(max(SEAM_ENV_MS * RATE / 1000.0, 4.0 * RATE / max(f5, 1.0)))
    w = max(8, min(w, len(x) // 8))
    head = float(np.sqrt(np.mean(x[:w] ** 2)))
    tail = float(np.sqrt(np.mean(x[-w:] ** 2)))
    env_db = 20.0 * math.log10(max(head, 1e-12) / max(tail, 1e-12))
    return dict(step=step, p999=p999, ratio=step / max(p999, 1e-12),
                step2=step2, p999_2=p999_2,
                ratio2=step2 / max(p999_2, 1e-12),
                env_db=env_db, head_rms=head, tail_rms=tail,
                env_window_ms=1000.0 * w / RATE, f5_hz=f5)


def centroid_hz(x):
    """Spectral centroid -- what band the stream actually occupies."""
    k = np.fft.rfftfreq(len(x), 1.0 / RATE)
    p = np.abs(np.fft.rfft(x)) ** 2
    return float((k * p).sum() / max(p.sum(), 1e-30))


def third_octave(x, lo=25.0, hi=12500.0):
    """(centre frequencies, dB) in third-octave bands -- what a plot shows."""
    k = np.fft.rfftfreq(len(x), 1.0 / RATE)
    p = np.abs(np.fft.rfft(x)) ** 2
    fc, lv = [], []
    f = lo
    while f <= hi:
        a, b = f / 2.0 ** (1.0 / 6.0), f * 2.0 ** (1.0 / 6.0)
        m = (k >= a) & (k < b)
        e = float(p[m].sum())
        fc.append(f)
        lv.append(10.0 * math.log10(e + 1e-30))
        f *= 2.0 ** (1.0 / 3.0)
    return np.array(fc), np.array(lv)


def rms_dbfs(x):
    return 20.0 * math.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-12))


# ===========================================================================
# 7.  Writing it out
# ===========================================================================

# Streams are normalised to a common RMS so the bed's dB values are the ONLY
# thing that sets loudness, and peak-limited if that would clip. The high-crest
# streams -- the ones with transients in them, the dock and the pool -- fall
# back to the peak rule and their actual RMS is recorded, so the runtime can
# still level-match them. Peak normalising everything wasted 17 dB of the word
# on `crowd_sparse`; RMS normalising everything would clip the dock.
TARGET_RMS_DBFS = -20.0
PEAK_DBFS = -1.0
REF_DBA_AT_0DBFS = 94.0          # the acoustic calibration standard: 0 dBFS is
                                 # 1 Pa is 94 dB SPL. Not a taste decision.
RUNTIME_HEADROOM_DBFS = -6.0     # where the loudest bed on the station lands


def _wav_bytes(x):
    """16-bit mono PCM. Written by hand so the file is exactly what it says."""
    rms = max(float(np.sqrt(np.mean(x ** 2))), 1e-12)
    g = 10.0 ** (TARGET_RMS_DBFS / 20.0) / rms
    peak = float(np.max(np.abs(x))) * g
    limit = 10.0 ** (PEAK_DBFS / 20.0)
    if peak > limit:
        g *= limit / peak
    y = x * g
    pcm = np.clip(np.round(y * 32767.0), -32768, 32767).astype("<i2").tobytes()
    hdr = (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
           + struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE * 2, 2, BITS)
           + b"data" + struct.pack("<I", len(pcm)))
    return hdr + pcm, y


def write_bank(outdir=OUT_DIR):
    """Synthesise every stream, write the WAVs, and return the bank manifest."""
    os.makedirs(outdir, exist_ok=True)
    streams = _build_streams()
    bank = {"rate": RATE, "bits": BITS, "peak_dbfs": PEAK_DBFS,
            "ref_dba_at_0dbfs": REF_DBA_AT_0DBFS, "streams": {}}
    total = 0
    for name in sorted(streams):
        x = streams[name]["x"]
        raw, y = _wav_bytes(x)
        path = os.path.join(outdir, name + ".wav")
        with open(path, "wb") as f:
            f.write(raw)
        total += len(raw)
        s = seam(y)
        bank["streams"][name] = dict(
            file=name + ".wav", samples=int(len(y)),
            seconds=round(len(y) / float(RATE), 6),
            rms_dbfs=round(rms_dbfs(y), 2),
            peak_dbfs=round(20.0 * math.log10(
                max(float(np.max(np.abs(y))), 1e-12)), 2),
            # what the runtime adds so every stream plays at the level the bed
            # asks for, whatever normalisation rule it actually landed on
            level_trim_db=round(TARGET_RMS_DBFS - rms_dbfs(y), 2),
            centroid_hz=round(centroid_hz(y), 1),
            band=list(STREAM_BANDS[name]),
            seam_ratio=round(s["ratio"], 4),
            seam_ratio_d2=round(s["ratio2"], 4),
            bytes=len(raw), why=streams[name]["why"])
    bank["total_bytes"] = total
    return bank, streams


# The point emitters. A bed is the REVERBERANT field of a room; an emitter is
# the DIRECT field of one object, so the two do not double-count -- walk up to
# a duct and the duct gets louder while the room does not.
#
# Matched against mesh names, which already carry `fix_*` and `prop_*` from
# `rooms._fixture` and the place key as a `<place>__<group>` prefix. There is
# no second list of where the fans are: if the room has a duct in the geometry,
# the runtime finds it.
EMITTERS = (
    ("fix_service_duct",  "air_duct",       -3.0,  7.0, "air"),
    ("fix_service_riser", "air_duct",       -6.0,  6.0, "air"),
    ("fix_fume_column",   "air_duct",        0.0,  9.0, "air"),
    ("fix_plant_column",  "plant_beat",     -1.0, 14.0, "machinery"),
    ("fix_furnace_stack", "plant_beat",     +3.0, 20.0, "machinery"),
    ("fix_equipment_gantry", "machine_hum", -8.0,  5.0, "machinery"),
    ("fix_catenary_run",  "dock_machinery", -6.0, 10.0, "machinery"),
    ("fix_platform_edge", "dock_machinery", -9.0,  8.0, "machinery"),
    ("prop_standpipe",    "water_run",      -2.0,  6.0, "water"),
    ("prop_shower",       "water_run",      -4.0,  4.0, "water"),
    ("prop_pool_edge",    "water_pool",     +1.0, 16.0, "water"),
    ("prop_planter",      "water_pool",    -12.0,  3.5, "water"),
    ("prop_intercom",     "pa_horn",       -10.0,  6.0, "pa"),
    ("prop_info_board",   "pa_horn",       -14.0,  5.0, "pa"),
    ("prop_reactor_console", "machine_hum", -6.0,  4.0, "machinery"),
    ("prop_tank_gauge",   "machine_hum",   -14.0,  3.0, "machinery"),
    ("prop_lift_door",    "dock_machinery", -8.0,  6.0, "machinery"),
    ("prop_bay_door",     "dock_machinery", -2.0, 18.0, "traffic"),
)
EMITTER_CAP = 24                 # nearest N kept live; stated, not implicit
# An emitter's `db` above is an offset from this: the DIRECT-field level one
# metre from the object, in dBA. 60 dBA at 1 m is the same conversational
# reference `TALKER_LW_DB` is derived from, so a duct at -3 is a thing you can
# talk over and a furnace stack at +3 is a thing you cannot.
EMITTER_REF_DBA = 60.0


def beds_manifest(day=0, datum=None, hours=range(24)):
    """Every place, every hour, as layer levels the runtime can read.

    Deliberately levels-and-reasons rather than audio: a pre-mixed bed per
    place per hour would be a second description of the same numbers, and this
    project's whole recorded history is second descriptions drifting.
    """
    # STEADY LAYERS ONLY. The runtime test caught the reason: an announcement
    # occupies about 30 minutes of `broadcast`'s quarter-hour window, and an
    # HOURLY manifest cannot say that -- so a chime that fires once landed in
    # the bed at 03:00 and 13:00 alike and read as a tannoy that never stops.
    # Events are a separate list with their real times, in `announcements()`.
    out = {}
    for p in dr.PLACES:
        rows = {}
        for h in hours:
            b = bed(p["key"], float(h), day, datum)
            rows[str(h)] = {x["layer"] + ":" + x["stream"]: x["db"]
                            for x in b["layers"] if not x.get("event")}
        b0 = bed(p["key"], 13.0, day, datum)
        out[p["key"]] = dict(name=p["name"], archetype=b0["archetype"],
                             air_class=b0["air_class"],
                             floor_m2=b0["floor_m2"],
                             surface_m2=b0["surface_m2"], hours=rows)
    return out


def announcements(day=0, datum=None):
    """Every spoken call of the day, with its real time and its real text.

    Straight off `broadcast.day` -- so the runtime fires the chime at the
    minute the ship berths, and the line it carries is the era-correct one
    `costume.ERA_EVENTS` allows at the datum. A standing surface (a screen, a
    poster) has no hour and is not an announcement.
    """
    return [dict(hour=round(a["hour"], 4), db=PA_CALL_DBA, stream="pa_chime",
                 kind=a["kind"], places=list(a["places"]), text=a["text"])
            for a in _station_says(day, datum) if a["hour"] is not None]


def write_all(outdir=OUT_DIR, day=0, datum=None):
    bank, streams = write_bank(outdir)
    beds = beds_manifest(day, datum)
    peak = max([v for pl in beds.values() for hr in pl["hours"].values()
                for v in [db_sum(list(hr.values()))] if v] + [PA_CALL_DBA])
    # DERIVED, not chosen: the trim is whatever puts the loudest bed on the
    # station at the stated headroom.
    bank["master_trim_db"] = round(RUNTIME_HEADROOM_DBFS
                                   - (peak - REF_DBA_AT_0DBFS), 2)
    bank["loudest_bed_dba"] = round(peak, 2)
    bank["emitters"] = [dict(match=m, stream=s, db=d, range_m=r, layer=ly)
                        for m, s, d, r, ly in EMITTERS]
    bank["emitter_cap"] = EMITTER_CAP
    bank["emitter_ref_dba"] = EMITTER_REF_DBA
    bank["target_rms_dbfs"] = TARGET_RMS_DBFS
    bank["layers"] = list(LAYERS)
    bank["fallback_place"] = "central_corridor"   # what a corridor sounds like
    bank["announcements"] = announcements(day, datum)
    bank["announcement_window_h"] = 0.25          # broadcast.audible_at's own
    bank["loudest"] = max(
        ((db_sum(list(hr.values())), k, h)
         for k, pl in beds.items() for h, hr in pl["hours"].items()),
        key=lambda t: t[0])[1:]
    with open(os.path.join(outdir, "bank.json"), "w") as f:
        json.dump(bank, f, indent=1, sort_keys=True)
    with open(os.path.join(outdir, "beds.json"), "w") as f:
        json.dump(beds, f, separators=(",", ":"), sort_keys=True)
    sizes = {n: os.path.getsize(os.path.join(outdir, n))
             for n in sorted(os.listdir(outdir))}
    return bank, beds, sizes


# ===========================================================================
# 8.  Plots -- you cannot listen to it, so look at it
# ===========================================================================
# A tiny PNG writer and a tiny plotter, because there is no matplotlib in this
# container. Both are here rather than in `tools/` so the module that makes the
# claim also makes the evidence -- CLAUDE.md's "a gate belongs in the module
# that builds the thing".

_FONT = {
    " ": "0000000000", "0": "3E5149453E", "1": "00427F4000", "2": "4261514946",
    "3": "2141454B31", "4": "18141211 7F".replace(" ", ""), "5": "2745454539",
    "6": "3C4A494930", "7": "0171090503", "8": "3649494936", "9": "0649494A3C",
    ".": "0060600000", ":": "0036360000", "-": "0808080808", "/": "2010080402",
    "%": "2213086432", "(": "001C224100", ")": "0041221C00", "+": "081C1C0808",
    ",": "00A0600000", "A": "7E1111117E", "B": "7F49494936", "C": "3E41414122",
    "D": "7F4141221C", "E": "7F49494941", "F": "7F09090901", "G": "3E41494978",
    "H": "7F0808087F", "I": "00417F4100", "J": "3040413F01", "K": "7F08142241",
    "L": "7F40404040", "M": "7F0204027F", "N": "7F0408107F", "O": "3E4141413E",
    "P": "7F09090906", "Q": "3E4151215E", "R": "7F09192946", "S": "2645494932",
    "T": "01017F0101", "U": "3F4040403F", "V": "1F2040201F", "W": "3F4038403F",
    "X": "63140814 63".replace(" ", ""), "Y": "0704780407", "Z": "6151494543",
}


# Five columns of seven rows, two hex digits a column. Checked at import
# because the failure mode is a ValueError thrown 200 s into a plot run, after
# everything expensive has already been computed -- which is exactly what
# happened: the space glyph was five characters instead of ten and took the
# whole `--write --plots` run down with it at the last step.
_BAD_GLYPHS = [k for k, v in _FONT.items() if len(v) != 10]
assert not _BAD_GLYPHS, f"malformed font glyphs: {_BAD_GLYPHS}"


def _png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


class Canvas:
    def __init__(self, w, h, bg=(16, 18, 22)):
        self.w, self.h = w, h
        self.im = np.zeros((h, w, 3), dtype=np.uint8)
        self.im[:, :] = bg

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im[int(y), int(x)] = c

    def rect(self, x0, y0, x1, y1, c):
        x0, x1 = sorted((max(0, int(x0)), min(self.w, int(x1))))
        y0, y1 = sorted((max(0, int(y0)), min(self.h, int(y1))))
        self.im[y0:y1, x0:x1] = c

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / float(n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dy in range(thick):
                for dx in range(thick):
                    self.px(x + dx, y + dy, c)

    def poly(self, xs, ys, c, thick=1):
        for i in range(len(xs) - 1):
            self.line(xs[i], ys[i], xs[i + 1], ys[i + 1], c, thick)

    def text(self, x, y, s, c=(190, 200, 210), scale=1):
        cx = x
        for ch in str(s).upper():
            g = _FONT.get(ch)
            if g is None:
                cx += 6 * scale
                continue
            for col in range(5):
                bits = int(g[col * 2:col * 2 + 2], 16)
                for row in range(7):
                    if bits & (1 << row):
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, c)
            cx += 6 * scale
        return cx

    def save(self, path):
        _png(path, self.im)


# Fourteen, because the bank has thirteen streams and an eight-colour palette
# gave `air_plenum` and `structure_hull` the same green on the spectrum plot --
# two lines a reader is meant to tell apart, in one colour.
PALETTE = ((120, 200, 255), (255, 170, 90), (140, 235, 150), (255, 130, 150),
           (200, 160, 255), (245, 225, 120), (150, 220, 220), (240, 150, 220),
           (110, 150, 240), (255, 120, 70), (80, 190, 110), (215, 90, 110),
           (170, 120, 220), (190, 190, 190))


def plot_spectra(streams, path):
    """Third-octave spectrum of every stream, on one log-frequency axis."""
    c = Canvas(1180, 700)
    x0, y0, x1, y1 = 80, 40, 1000, 610
    c.rect(x0, y0, x1, y1, (24, 27, 33))
    lo, hi = 25.0, 12500.0
    dbmin, dbmax = -80.0, 10.0

    def fx(f):
        return x0 + (x1 - x0) * math.log10(f / lo) / math.log10(hi / lo)

    def fy(d):
        return y1 - (y1 - y0) * (d - dbmin) / (dbmax - dbmin)
    for f in (31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000):
        c.line(fx(f), y0, fx(f), y1, (44, 48, 56))
        lab = f"{f / 1000:g}K" if f >= 1000 else f"{f:g}"
        c.text(fx(f) - 8, y1 + 6, lab, (150, 160, 175))
    for d in range(-80, 11, 10):
        c.line(x0, fy(d), x1, fy(d), (40, 44, 52))
        c.text(x0 - 32, fy(d) - 3, f"{d}", (150, 160, 175))
    for i, name in enumerate(sorted(streams)):
        col = PALETTE[i % len(PALETTE)]
        x = streams[name]["x"]
        x = x / max(float(np.max(np.abs(x))), 1e-12)
        fc, lv = third_octave(x, lo, hi)
        lv = lv - lv.max()
        c.poly([fx(f) for f in fc], [fy(max(dbmin, v)) for v in lv], col, 2)
        yy = y0 + 6 + i * 14
        c.rect(x1 + 16, yy + 1, x1 + 30, yy + 6, col)
        c.text(x1 + 36, yy, name.replace("_", "-"), col)
    c.text(x0, 14, "LAYER 7 STREAM BANK - THIRD-OCTAVE SPECTRA, "
                   "NORMALISED TO PEAK BAND", (225, 232, 240))
    c.text(x0, y1 + 26, "FREQUENCY HZ", (150, 160, 175))
    c.text(8, y0, "DB", (150, 160, 175))
    c.save(path)


def plot_day(path, keys, day=0):
    """Total dBA against hour for a handful of places -- the day/night claim."""
    c = Canvas(1180, 640)
    x0, y0, x1, y1 = 80, 46, 940, 540
    c.rect(x0, y0, x1, y1, (24, 27, 33))
    hours = [h * 0.5 for h in range(49)]
    series = {}
    for k in keys:
        series[k] = [total_dba(k, h, day) or 0.0 for h in hours]
    lo = math.floor(min(min(v) for v in series.values()) / 5.0) * 5 - 2
    hi = math.ceil(max(max(v) for v in series.values()) / 5.0) * 5 + 2

    def fx(h):
        return x0 + (x1 - x0) * h / 24.0

    def fy(d):
        return y1 - (y1 - y0) * (d - lo) / (hi - lo)
    for h in range(0, 25, 3):
        c.line(fx(h), y0, fx(h), y1, (44, 48, 56))
        c.text(fx(h) - 8, y1 + 6, f"{h:02d}", (150, 160, 175))
    for d in range(int(lo), int(hi) + 1, 5):
        c.line(x0, fy(d), x1, fy(d), (40, 44, 52))
        c.text(x0 - 32, fy(d) - 3, f"{d}", (150, 160, 175))
    # the station night, from the human sleep block the clock is set by
    r = sched.RHYTHMS["human"]
    c.rect(fx(r.sleep_start), y0, x1, y1, (30, 32, 44))
    c.rect(x0, y0, fx((r.sleep_start + r.sleep_hours) % 24.0), y1, (30, 32, 44))
    for i, k in enumerate(keys):
        col = PALETTE[i % len(PALETTE)]
        c.poly([fx(h) for h in hours], [fy(v) for v in series[k]], col, 2)
        yy = y0 + 8 + i * 15
        c.rect(x1 + 16, yy + 1, x1 + 30, yy + 6, col)
        d3, d13 = total_dba(k, 3.0, day), total_dba(k, 13.0, day)
        c.text(x1 + 36, yy, f"{k[:16]} {d13 - d3:+.1f}", col)
    c.text(x0, 14, "TOTAL AMBIENCE DBA AGAINST STATION HOUR - "
                   "SHADED IS THE HUMAN SLEEP BLOCK", (225, 232, 240))
    c.text(x0, 28, "LEGEND SHOWS 13:00 MINUS 03:00 IN DB", (150, 160, 175))
    c.text(x0, y1 + 26, "STATION HOUR EMT", (150, 160, 175))
    c.text(8, y0, "DBA", (150, 160, 175))
    c.save(path)


def plot_seam(streams, path, name="crowd_babble"):
    """The loop join, and the control that does not survive it."""
    c = Canvas(1180, 520)
    x = streams[name]["x"]
    x = x / max(float(np.max(np.abs(x))), 1e-12)
    rr = np.random.default_rng(931)
    bad = _bad_loop(len(x), rr)
    bad = bad / max(float(np.max(np.abs(bad))), 1e-12)
    w = 160
    for row, (sig, label) in enumerate(
            ((x, f"{name} - CIRCULAR, SHIPPED"),
             (bad, "CONTROL - TIME-DOMAIN IIR, NOT LOOP-EXACT"))):
        y0 = 60 + row * 230
        y1 = y0 + 180
        c.rect(90, y0, 1090, y1, (24, 27, 33))
        c.line(590, y0, 590, y1, (110, 90, 90), 1)
        seg = np.concatenate([sig[-w:], sig[:w]])
        mx = max(float(np.max(np.abs(seg))), 1e-9)
        xs = [90 + 1000.0 * i / (len(seg) - 1) for i in range(len(seg))]
        ys = [(y0 + y1) / 2 - (v / mx) * (y1 - y0) * 0.45 for v in seg]
        c.poly(xs, ys, PALETTE[row], 2)
        s = seam(sig)
        c.text(90, y0 - 16, f"{label}   SEAM RATIO {s['ratio']:.2f}",
               (225, 232, 240) if row == 0 else (255, 150, 150))
        c.text(500, y1 + 6, "LOOP JOIN", (200, 140, 140))
    c.text(90, 16, "THE LOOP SEAM - LAST 160 SAMPLES AND FIRST 160, "
                   "SHIPPED ABOVE AND CONTROL BELOW", (225, 232, 240))
    c.text(90, 30, "GATE IS STEP ACROSS THE JOIN OVER THE 99.9 PERCENTILE "
                   "STEP INSIDE THE LOOP - PASS IS AT OR UNDER 1.0",
           (150, 160, 175))
    c.save(path)


def _bad_loop_iir(n, rng, a=5e-4):
    """Control 1: the same noise through a TIME-DOMAIN one-pole filter.

    A recursive filter carries state that never wraps, so its output is not
    periodic and the two ends of the buffer are unrelated. This is what would
    happen if the streams were made with an ordinary audio filter instead of a
    spectral multiply.

    THE FIRST VERSION OF THIS CONTROL DID NOT FIRE, and the reason is worth
    keeping: at a = 0.02 the pole is fast enough that the settled value at the
    end is the same size as an ordinary sample step, so the ratio came out 0.87
    -- a PASS, on a signal that is definitely not loop-exact. A control that
    fails to fire is the defect this repository has caught twice at plan scale.
    The pole is now slow (a = 5e-4), where the settled value is forty times a
    per-sample step, which is the regime a real ambience filter runs in.
    """
    x = rng.standard_normal(n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def _bad_loop_am(n, rng):
    """Control 2: a shipped-style stream with a NON-INTEGER-CYCLE modulator.

    This is the mistake `_cycles` exists to prevent, and it is the one anybody
    writing an ambience makes first: pick a modulation rate in Hz, multiply,
    ship it. 0.5 cycles left over at the buffer end means the envelope arrives
    at the seam at the opposite phase from where it started, and the loop
    thumps once a pass.
    """
    x = _spectral_noise(n, rng, -3.0, lo=200.0, hi=4000.0)
    # k + 1/4 cycles: the envelope starts at its mid-point and ends at its
    # maximum, so the seam carries the full modulation depth as one step.
    cycles = math.floor(0.19 * n / RATE) + 0.25
    env = 0.5 + 0.5 * np.sin(2.0 * np.pi * cycles * np.arange(n) / float(n))
    return x * env


def _bad_loop(n, rng):
    return _bad_loop_iir(n, rng)


# ===========================================================================
# 9.  Report
# ===========================================================================

REPORT_PLACES = ("zocalo", "qtr_civilian", "docking_bays", "customs_north",
                 "downbelow", "the_garden", "alien_sector", "reactor_hall",
                 "central_corridor", "sanctuaries")


def report(out=print, day=0):
    out(f"THE STATION HAS {len(LAYERS)} AMBIENCE LAYERS AND "
        f"{len(STREAM_BANDS)} STREAMS, over {len(dr.PLACES)} places")
    out("")
    out("ONE ROOM, TWO HOURS -- the whole claim, itemised")
    for k in ("zocalo",):
        for h in (3.0, 13.0):
            b = bed(k, h, day)
            out(f"  {b['name']} at {h:05.2f}  STEADY "
                f"{b['steady_dba']:.1f} dBA"
                + (f", {b['total_dba']:.1f} with the announcement"
                   if b["event_dba"] else "")
                + f"  ({b['floor_m2']:.0f} m2 floor, "
                f"{b['surface_m2']:.0f} m2 surface, "
                f"R={b['room_constant_m2']:.0f})")
            for L in b["layers"]:
                out(f"      {L['layer']:<10s} {L['db']:6.1f} dBA  "
                    f"[{L['stream']}]")
                out(f"                 {L['why']}")
        d = total_dba(k, 13.0, day) - total_dba(k, 3.0, day)
        out(f"    13:00 minus 03:00 = {d:+.2f} dB")
    out("")
    out("A DAY, EVERYWHERE THAT MATTERS")
    out(f"  {'place':<20s} {'03:00':>7s} {'08:00':>7s} {'13:00':>7s} "
        f"{'19:00':>7s} {'23:00':>7s}  {'day-night':>9s}")
    for k in REPORT_PLACES:
        v = [total_dba(k, h, day) for h in (3, 8, 13, 19, 23)]
        out(f"  {k:<20s} " + " ".join(f"{x:7.1f}" for x in v)
            + f"  {v[2] - v[0]:+9.2f}")
    out("")
    out("THE PORT -- a docking bay is loud when a liner is in")
    ld = next((n for n in range(8) if tf.liner_today(n)), 0)
    la = next((a for a in tf.arrivals(ld) if a["type"] == "liner"), None)
    if la:
        for label, h, d in (("quiet hour", (la["hour"] - 6) % 24, ld),
                            ("liner alongside", la["hour"] + 0.2, ld)):
            b = bed("docking_bays", h, d)
            t = next((x for x in b["layers"] if x["layer"] == "traffic"), None)
            out(f"  {label:<18s} {h:05.2f}  total {b['total_dba']:6.1f} dBA  "
                f"traffic {(t['db'] if t else float('nan')):6.1f}  "
                f"{t['why'] if t else '--'}")
        for label, h in (("background", (la["hour"] - 4) % 24),
                         ("liner clearing", la["hour"] + 0.5)):
            b = bed("customs_north", h, ld)
            t = next((x for x in b["layers"] if x["layer"] == "traffic"), None)
            out(f"  {label:<18s} {h:05.2f}  total {b['total_dba']:6.1f} dBA  "
                f"traffic {(t['db'] if t else float('nan')):6.1f}  "
                f"{t['why'] if t else '--'}")
    out("")
    out("SPECIES -- 03:00 is a different hour depending on who lives there")
    for k in REPORT_PLACES:
        mix = species_mix(k)
        top = sorted(mix.items(), key=lambda kv: -kv[1])[:2]
        out(f"  {k:<20s} awake 03:00 {awake_share(k, 3.0):.2f}  "
            f"13:00 {awake_share(k, 13.0):.2f}   "
            + ", ".join(f"{s} {f:.0%}" for s, f in top))
    out("")
    out("THE GAZETTEER'S OWN SENTENCE -- the compressors from Downbelow")
    b = bed("downbelow", 3.0, day)
    m = next((x for x in b["layers"] if x["layer"] == "machinery"), None)
    if m:
        out(f"  machinery in downbelow at 03:00: {m['db']:.1f} dBA")
        out(f"    {m['why']}")
        air = next(x for x in b["layers"] if x["layer"] == "air")
        out(f"  against its own air handling at {air['db']:.1f} dBA -- "
            f"{m['db'] - air['db']:+.1f} dB, so it is the loudest thing there")


# ===========================================================================
# 10.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _selftest(out=print):                                       # noqa: C901
    global SURFACE_ALPHA, STREAM_BANDS
    del _FAILED[:]
    n = 0
    streams = _build_streams()

    # -- the streams ------------------------------------------------------
    out("STREAMS -- measured, not described")
    out(f"  {'stream':<16s} {'sec':>7s} {'rms':>7s} {'centroid':>9s} "
        f"{'band':>14s} {'click':>6s} {'d2':>6s} {'pump dB':>8s} {'win ms':>7s}")
    worst = 0.0
    for name in sorted(streams):
        _raw, x = _wav_bytes(streams[name]["x"])   # measure what is WRITTEN
        s = seam(x)
        cen = centroid_hz(x)
        lo, hi = STREAM_BANDS[name]
        worst = max(worst, s["ratio"])
        out(f"  {name:<16s} {len(x) / RATE:7.3f} {rms_dbfs(x):7.1f} "
            f"{cen:9.1f} {f'{lo:.0f}-{hi:.0f}':>14s} {s['ratio']:6.2f} "
            f"{s['ratio2']:6.2f} {s['env_db']:+8.2f} "
            f"{s['env_window_ms']:7.1f}")
        n += 1
        check(s["ratio"] <= 1.0,
              f"{name}: no click -- the loop seam is no bigger than an "
              f"ordinary step", f"ratio {s['ratio']:.3f}")
        n += 1
        check(abs(s["env_db"]) <= SEAM_ENV_DB,
              f"{name}: no pump -- the level either side of the join agrees",
              f"{s['env_db']:+.2f} dB over {SEAM_ENV_MS:.0f} ms")
        n += 1
        check(lo <= cen <= hi,
              f"{name}: spectral centroid is in the band it claims",
              f"{cen:.0f} Hz outside {lo:.0f}-{hi:.0f}")
        n += 1
        check(float(np.max(np.abs(x))) < 1.0, f"{name}: does not clip",
              f"peak {float(np.max(np.abs(x))):.4f}")
        n += 1
        check(abs(float(np.mean(x))) < 1e-3, f"{name}: no DC offset",
              f"{float(np.mean(x)):.5f}")
    out(f"  worst seam ratio across the bank: {worst:.3f}")

    # -- the structure loop is one spoke pass -----------------------------
    n += 1
    want = SPOKE_PASS_S * RATE
    got = len(streams["structure_hull"]["x"])
    check(abs(got - want) <= 1.0,
          "the structure loop is exactly one spoke-pass period",
          f"{got} samples vs {want:.1f}")
    out(f"  structure loop {got} samples = {got / RATE:.6f} s against the "
        f"spoke pass's {SPOKE_PASS_S:.6f} s -- quantisation error "
        f"{abs(got / RATE - SPOKE_PASS_S) * 1e6:.1f} us a cycle")

    # -- beds are real places ---------------------------------------------
    out("")
    n += 1
    bad = []
    for p in dr.PLACES:
        try:
            b = bed(p["key"], 13.0)
        except Exception as e:                                  # noqa: BLE001
            bad.append((p["key"], repr(e)))
            continue
        if not b["layers"] or b["total_dba"] is None:
            bad.append((p["key"], "empty bed"))
    check(not bad, "every place in the register gets a bed", f"{bad[:4]}")
    n += 1
    beds13 = {p["key"]: bed(p["key"], 13.0) for p in dr.PLACES}
    silent = [k for k, b in beds13.items() if b["total_dba"] < 20.0]
    check(not silent,
          "nowhere on the station is silent -- a sealed volume still has air "
          "handling and a hull", f"{silent[:5]}")
    n += 1
    # NOTHING ON THE STATION IS ABOVE A HEARING-PROTECTION LEVEL, and this is
    # the gate that caught the berth bug. `vorlon_berth` -- one ship, in a
    # 1,477 m2 room -- was reading 88.8 dBA because `traffic.berths_in_use` is
    # a STATION-WIDE count and every berth was being handed all 32 of them. It
    # was the loudest bed in the manifest, and the master trim is derived from
    # the loudest bed, so one wrong room was setting the gain for everywhere.
    loudest = max(((b["steady_dba"], k) for k, b in beds13.items()))
    out(f"  loudest steady bed on the station: {loudest[1]} at "
        f"{loudest[0]:.1f} dBA")
    check(loudest[0] < 85.0,
          "no steady bed on the station is above a hearing-protection level",
          f"{loudest[1]} at {loudest[0]:.1f} dBA")
    n += 1
    # ...and its control: hand every berth the whole station's ships again.
    keep_area = _BERTH_AREA
    try:
        globals()["_BERTH_AREA"] = None
        _bad = []
        for p in dr.PLACES:
            if not (set(p["functions"]) & set(BAY_FUNCTIONS)):
                continue
            _s, _f, _hh = room_geometry(p)
            n_all = sum(tf.berths_in_use(13.0, 0).values())
            _bad.append((diffuse_lp(BAY_MACHINERY_LW_DB
                                    + 10.0 * math.log10(max(n_all, 1)), _s),
                         p["key"]))
        worst_bad = max(_bad) if _bad else (0.0, "-")
    finally:
        globals()["_BERTH_AREA"] = keep_area
    out(f"  control: with the station's berths NOT shared out by floor area, "
        f"{worst_bad[1]} reads {worst_bad[0]:.1f} dBA -- "
        f"{'FIRES' if worst_bad[0] >= 85.0 else 'DOES NOT FIRE'}")
    check(worst_bad[0] >= 85.0,
          "and the gate fires on the bug it was written for")
    n += 1
    lay = {L["layer"] for b in beds13.values() for L in b["layers"]}
    check(lay == set(LAYERS),
          "every declared layer occurs somewhere on the station",
          f"missing {set(LAYERS) - lay}")

    # -- THE CLAIM: the same room at two hours is two beds -----------------
    out("A DAY IS NOT A NIGHT")
    diurnal = []
    for k in REPORT_PLACES:
        d = total_dba(k, 13.0) - total_dba(k, 3.0)
        diurnal.append((k, d))
        out(f"  {k:<20s} 13:00 - 03:00 = {d:+6.2f} dB")
    n += 1
    check(any(abs(d) >= 3.0 for _k, d in diurnal),
          "at least one place changes audibly between night and day",
          f"{diurnal}")
    n += 1
    z = total_dba("zocalo", 13.0) - total_dba("zocalo", 3.0)
    check(z >= 2.0,
          "the Zocalo is louder at one in the afternoon than at three in the "
          "morning", f"{z:+.2f} dB")
    n += 1
    # ...AND THE CONTROL, which had to be replaced. The first one was
    # `downbelow`, on the grounds that `schedule.PLACES` marks it flat -- and
    # it swung +3.57 dB, MORE than the Zocalo. That is not a bug: its headcount
    # is flat and its RESIDENTS' sleep is not, so the swing is the species
    # clock doing exactly what it should. It is simply not a control for
    # anything. A room whose sound is machinery rather than people is.
    flat = total_dba("reactor_hall", 13.0) - total_dba("reactor_hall", 3.0)
    check(abs(flat) < 1.0,
          "and the reactor hall, whose ambience is plant rather than people, "
          "has no day and no night -- the control for the line above",
          f"reactor_hall {flat:+.2f} vs zocalo {z:+.2f}")
    out(f"  control: reactor_hall (machinery, not people) {flat:+.2f} dB")
    dbl = total_dba("downbelow", 13.0) - total_dba("downbelow", 3.0)
    out(f"  and downbelow, whose HEADCOUNT is flat, still swings "
        f"{dbl:+.2f} dB -- because its residents sleep on their own clocks")

    # -- THE SPECIES CLOCK, which is the sharpest thing here ---------------
    out("")
    out("SPECIES -- awake share at 03:00, from schedule.RHYTHMS")
    hum = sched.awake_fraction("human", 3.0)
    bra = sched.awake_fraction("brakiri", 3.0)
    out(f"  human {hum:.2f}   brakiri {bra:.2f}  "
        f"(RHYTHMS['brakiri'] is flagged NIGHT DWELLERS, authority 4)")
    n += 1
    check(bra > hum + 0.5,
          "the rhythm table makes Brakiri a night crowd and humans not")
    n += 1
    # And it reaches a bed: a place with aliens in the mix keeps more of its
    # crowd at 03:00 than one that is nearly all human.
    ratios = {}
    for k in ("qtr_civilian", "alien_sector", "zocalo", "crew_country"):
        try:
            ratios[k] = awake_share(k, 3.0) / max(awake_share(k, 13.0), 1e-6)
        except Exception:                                       # noqa: BLE001
            pass
    out("  awake(03:00)/awake(13:00) by place: "
        + ", ".join(f"{k} {v:.2f}" for k, v in sorted(ratios.items())))
    n += 1
    check(len(set(round(v, 3) for v in ratios.values())) > 1,
          "and different places keep different fractions of their crowd "
          "overnight, because they hold different species", f"{ratios}")

    # -- THE PORT ---------------------------------------------------------
    out("")
    ld = next((d for d in range(8) if tf.liner_today(d)), 0)
    la = next((a for a in tf.arrivals(ld) if a["type"] == "liner"), None)
    n += 1
    check(la is not None, "a liner turns up within a week to test against")
    if la:
        hot = bed("customs_north", la["hour"] + 0.5, ld)
        cold = bed("customs_north", (la["hour"] - 4) % 24, ld)
        th = next(x["db"] for x in hot["layers"] if x["layer"] == "traffic")
        tc = next(x["db"] for x in cold["layers"] if x["layer"] == "traffic")
        out(f"  customs_north traffic layer: {tc:.1f} dBA background -> "
            f"{th:.1f} dBA with a liner clearing ({th - tc:+.1f} dB)")
        n += 1
        check(th - tc >= 5.0,
              "the customs hall is measurably louder while a liner clears",
              f"{th - tc:+.2f} dB")
        n += 1
        # THE CONTROL: a day with no liner has no surge at the same hour.
        nold = next((d for d in range(8) if not tf.liner_today(d)), None)
        if nold is not None:
            q = bed("customs_north", la["hour"] + 0.5, nold)
            tq = next(x["db"] for x in q["layers"] if x["layer"] == "traffic")
            out(f"  control: the same hour on a linerless day {tq:.1f} dBA "
                f"({tq - th:+.1f} dB)")
            check(th - tq >= 5.0,
                  "and the same hour on a day with no liner is not loud -- "
                  "the surge is the SHIP, not the hour", f"{th - tq:+.2f}")
        else:
            check(False, "no linerless day in a week to control against")
        n += 1
        use_hot = tf.berths_in_use(la["hour"] + 0.2, ld)
        b_hot = bed("docking_bays", la["hour"] + 0.2, ld)
        empt = [h for h in range(24)
                if sum(tf.berths_in_use(float(h), ld).values()) == 0]
        out(f"  docking_bays: {sum(use_hot.values())} berths alongside -> "
            f"{b_hot['total_dba']:.1f} dBA; "
            + (f"{len(empt)} empty hour(s) in the day" if empt
               else "the port is never empty in this manifest"))
        check(any(x["layer"] == "traffic" for x in b_hot["layers"]),
              "a bay with ships in it has a traffic layer")

    # -- THE GAZETTEER'S SENTENCE -----------------------------------------
    out("")
    n += 1
    txt = " ".join(open(GAZETTEER).read().split()) if os.path.exists(
        GAZETTEER) else ""
    check("the compressors are audible from Downbelow" in txt,
          "the gazetteer sentence the machinery leak is built to is still "
          "in LIFE-SUPPORT-AND-INDUSTRY.md",
          "not found (the file is hard-wrapped, so whitespace is collapsed "
          "before matching)")
    db = bed("downbelow", 3.0)
    mach = next((x for x in db["layers"] if x["layer"] == "machinery"), None)
    air = next(x for x in db["layers"] if x["layer"] == "air")
    n += 1
    check(mach is not None and mach["db"] > air["db"],
          "the compressors ARE audible from Downbelow, and are the loudest "
          "thing in it", f"machinery {mach and mach['db']} vs air {air['db']}")
    out(f"  downbelow 03:00: machinery {mach['db']:.1f} dBA over air "
        f"{air['db']:.1f} dBA")
    n += 1
    qtr = bed("qtr_command", 3.0)
    qm = next((x for x in qtr["layers"] if x["layer"] == "machinery"), None)
    qa = next(x for x in qtr["layers"] if x["layer"] == "air")
    check(qm is None or qm["db"] < qa["db"],
          "and command quarters, which are NOT next to the plant, are not -- "
          "the control", f"machinery {qm and qm['db']} vs air {qa['db']}")
    out(f"  control qtr_command 03:00: machinery "
        f"{(qm['db'] if qm else float('-inf')):.1f} under air {qa['db']:.1f}")
    n += 1
    # And the reason that control now passes: the ducts left the machinery
    # layer. If one is ever put back the bedrooms go to 62 dBA again.
    leaked = [f for f in AIR_SYSTEM_FIXTURES if f in FIXTURE_LW_DB]
    check(not leaked,
          "no ventilation fixture is counted in the machinery layer as well "
          "as the air layer", f"{leaked}")
    n += 1
    # EVERY LOUD DWELLING MUST BE EXPLAINED BY THE PLANT, and this is the gate
    # that found the morgue. Four dwellings came out over 45 dBA of machinery:
    # `downbelow`, `subfloor_stack` and `downbelow_arch` are all inside or next
    # to `plant_zone` and are loud for the reason the gazetteer gives. The
    # fourth was the mortuary, which is nowhere near the plant and was loud
    # because `equipment_gantry` was mis-rated by 14 dB.
    loud, unexplained = [], []
    for k, b in beds13.items():
        if b["air_class"] not in ("living", "quiet"):
            continue
        m = next((x for x in b["layers"] if x["layer"] == "machinery"), None)
        if m is None or m["db"] <= 45.0:
            continue
        p = dr.by_key(k)
        near = ([n_["key"] for n_ in _plant_neighbours(p)]
                + ([p["within"]] if p["within"] and
                   rm.archetype(dr.by_key(p["within"])) == "industrial"
                   else []))
        loud.append((k, m["db"], near))
        if not near:
            unexplained.append((k, round(m["db"], 1)))
    out("  dwellings over 45 dBA of machinery: "
        + (", ".join(f"{k} {d:.1f} ({'/'.join(nr)})" for k, d, nr in loud)
           or "none"))
    check(not unexplained,
          "every dwelling loud enough to keep you awake is inside or beside "
          "the plant -- nowhere else on the station is", f"{unexplained}")

    # -- the ladder -------------------------------------------------------
    n += 1
    living = [b for b in beds13.values() if b["air_class"] == "living"]
    working = [b for b in beds13.values() if b["air_class"] == "working"]
    la_ = [x["db"] for b in living for x in b["layers"] if x["layer"] == "air"]
    wa_ = [x["db"] for b in working for x in b["layers"] if x["layer"] == "air"]
    check(la_ and wa_ and max(la_) < min(wa_),
          "INV-260's ladder holds: every living space's air handling is "
          "quieter than every working space's",
          f"living max {max(la_ or [0]):.1f}, working min {min(wa_ or [0]):.1f}")
    out(f"  air ladder: {len(living)} living {min(la_):.1f}-{max(la_):.1f} "
        f"dBA, {len(working)} working {min(wa_):.1f}-{max(wa_):.1f} dBA")
    n += 1
    st = {tuple(x["db"] for x in b["layers"] if x["layer"] == "structure")
          for k, b in beds13.items()
          if STRUCTURE_BEARING_FN not in dr.by_key(k)["functions"]}
    check(len(st) == 1,
          "the hull rumble is identical in every place that is not the "
          "bearing -- one body, one rumble", f"{sorted(st)[:4]}")

    # -- the crowd equation ----------------------------------------------
    n += 1
    surf = 2000.0
    mono = [diffuse_lp(TALKER_LW_DB + 10 * math.log10(v), surf, v * 3)
            for v in (1, 3, 10, 30, 100, 300)]
    check(all(b > a for a, b in zip(mono, mono[1:])),
          "crowd level rises monotonically with voices", f"{mono}")
    sat = (mono[-1] - mono[-2]) < (mono[1] - mono[0])
    n += 1
    check(sat,
          "and SATURATES, because the crowd's own absorption grows with it -- "
          "1->3 gains more than 100->300",
          f"{mono[1] - mono[0]:.2f} vs {mono[-1] - mono[-2]:.2f}")
    out(f"  crowd curve at 2,000 m2: "
        + ", ".join(f"{v}v {L:.1f}" for v, L in
                    zip((1, 3, 10, 30, 100, 300), mono)))

    # -- the tannoy -------------------------------------------------------
    n += 1
    with_call = None
    for h in [x / 4.0 for x in range(96)]:
        b = bed("arrival_concourse", h, 0)
        if any(x["stream"] == "pa_chime" for x in b["layers"]):
            with_call = (h, b)
            break
    check(with_call is not None,
          "the concourse hears an announcement at some point in the day")
    n += 1
    q = bed("qtr_civilian", 10.0, 0)
    check(not any(x["layer"] == "pa" for x in q["layers"]),
          "and ordinary civilian quarters have no tannoy at all -- "
          "broadcast.py's isolation rule, inherited rather than restated")
    if with_call:
        out(f"  arrival_concourse hears a call at {with_call[0]:05.2f}: "
            + next(x["calls"][0][:58] for x in with_call[1]["layers"]
                   if x["stream"] == "pa_chime"))
    n += 1
    # The memo above is a SECOND COPY of broadcast's audibility rule, which is
    # exactly the thing this project keeps being bitten by. So it is checked
    # against the original everywhere it is used, rather than trusted.
    dis = [(k, h) for k in ("arrival_concourse", "zocalo", "docking_bays",
                            "customs_north", "qtr_civilian")
           for h in (0.0, 3.5, 8.0, 10.0, 14.0, 16.0, 19.5, 23.0)
           if ([a["text"] for a in audible_here(k, h, 0, None)]
               != [a["text"] for a in bc.audible_at(k, h, 0)])]
    check(not dis,
          "the memoised audibility agrees with broadcast.audible_at "
          "everywhere it is asked -- 40 samples", f"{dis[:4]}")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("")
    out("negative controls:")

    # 1. two ways of building a stream that is NOT loop-exact
    _r, good = _wav_bytes(streams["crowd_babble"]["x"])
    sg = seam(good)
    out(f"  shipped crowd_babble for reference: click {sg['ratio']:.2f}, "
        f"pump {sg['env_db']:+.2f} dB")
    for label, sig, which in (
            ("a time-domain one-pole IIR instead of a spectral multiply",
             _bad_loop_iir(RATE * 4, np.random.default_rng(931)), "click"),
            ("a modulator at a non-integer number of cycles (what _cycles "
             "exists to prevent)",
             _bad_loop_am(RATE * 4, np.random.default_rng(932)), "pump")):
        _r2, y = _wav_bytes(sig)
        sb = seam(y)
        fired = (sb["ratio"] > 1.0 if which == "click"
                 else abs(sb["env_db"]) > SEAM_ENV_DB)
        out(f"  {label} -> click {sb['ratio']:.2f}, pump {sb['env_db']:+.2f} "
            f"dB -- the {which} gate "
            f"{'FIRES' if fired else 'DOES NOT FIRE'}")
        n += 1
        check(fired,
              f"the {which} gate fires on a stream that is not loop-exact",
              f"{label}: click {sb['ratio']:.3f} pump {sb['env_db']:+.2f}")
    n += 1
    # AND THE CROSS-CHECK THAT MADE THE SECOND GATE NECESSARY: the click gate
    # alone passes the envelope-broken stream. Recorded as an assertion so
    # nobody deletes the pump gate as redundant.
    _r3, yam = _wav_bytes(_bad_loop_am(RATE * 4, np.random.default_rng(932)))
    check(seam(yam)["ratio"] <= 1.0,
          "the CLICK gate alone cannot see an envelope break in noise -- this "
          "is why there are two", f"{seam(yam)['ratio']:.3f}")
    out(f"  (and the click gate alone reads {seam(yam)['ratio']:.2f} on that "
        f"same stream -- a pass. Neither gate subsumes the other.)")

    # 2. swap two streams' declared bands and the spectral gate must fire
    keep = dict(STREAM_BANDS)
    try:
        STREAM_BANDS = dict(keep)
        STREAM_BANDS["structure_hull"], STREAM_BANDS["water_run"] = (
            keep["water_run"], keep["structure_hull"])
        fired = []
        for nm in ("structure_hull", "water_run"):
            c = centroid_hz(streams[nm]["x"])
            lo, hi = STREAM_BANDS[nm]
            if not (lo <= c <= hi):
                fired.append(nm)
        out(f"  the rumble's and the tap's bands swapped -> {len(fired)}/2 "
            f"fail the centroid gate -- "
            f"{'FIRES' if len(fired) == 2 else 'DOES NOT FIRE'}")
        n += 1
        check(len(fired) == 2,
              "the spectral gate fires when a stream is mislabelled")
    finally:
        STREAM_BANDS = keep

    # 3. remove the crowd's own absorption and the level runs away
    keep_a = SURFACE_ALPHA
    try:
        base = [diffuse_lp(TALKER_LW_DB + 10 * math.log10(v), 2000.0, v * 3)
                for v in (10, 300)]
        no_abs = [TALKER_LW_DB + 10 * math.log10(v)
                  + 10 * math.log10(4.0 / (2000.0 * SURFACE_ALPHA
                                           / (1 - SURFACE_ALPHA)))
                  for v in (10, 300)]
        out(f"  with the crowd's own absorption switched off, 10->300 voices "
            f"gains {no_abs[1] - no_abs[0]:.1f} dB instead of "
            f"{base[1] - base[0]:.1f} dB")
        n += 1
        check(no_abs[1] - no_abs[0] > base[1] - base[0] + 1.0,
              "the saturation term is doing real work")
    finally:
        SURFACE_ALPHA = keep_a

    # 4. freeze the occupancy and the day/night claim must collapse
    keep_occ = pop.occupancy
    try:
        pop.occupancy = lambda *a, **k: 100
        _AWAKE_CACHE.clear()
        _PEAK_CACHE.clear()
        frozen = total_dba("zocalo", 13.0) - total_dba("zocalo", 3.0)
    finally:
        pop.occupancy = keep_occ
        _AWAKE_CACHE.clear()
        _PEAK_CACHE.clear()
    out(f"  with populace.occupancy frozen at 100, the Zocalo's day-night "
        f"swing falls from {z:+.2f} dB to {frozen:+.2f} dB -- the crowd layer "
        f"IS the occupancy")
    n += 1
    check(abs(frozen) < abs(z),
          "freezing the occupancy flattens the day", f"{frozen:+.2f}")

    # 5. a bed for a place that does not exist must raise
    raised = False
    try:
        bed("not_a_place", 12.0)
    except Exception:                                           # noqa: BLE001
        raised = True
    out(f"  a bed for an invented place -> "
        f"{'raises, FIRES' if raised else 'returns something, DOES NOT FIRE'}")
    n += 1
    check(raised, "an unknown place is an error, not an empty bed")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


# ===========================================================================
# 11.  CLI
# ===========================================================================

if __name__ == "__main__":                                   # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="synthesise the bank and write the bed manifest")
    ap.add_argument("--plots", action="store_true",
                    help="write the evidence PNGs into docs/")
    ap.add_argument("--bed", metavar="PLACE")
    ap.add_argument("--hour", type=float, default=13.0)
    ap.add_argument("--day", type=int, default=0)
    a = ap.parse_args()

    if a.bed:
        b = bed(a.bed, a.hour, a.day)
        print(json.dumps(b, indent=2))
        raise SystemExit(0)

    ok = True
    if a.write:
        bank, beds, sizes = write_all()
        tot = sum(sizes.values())
        print(f"wrote {len(sizes)} files, {tot / 1e6:.2f} MB, into {OUT_DIR}")
        for k, v in sizes.items():
            print(f"  {k:<24s} {v / 1024:9.1f} KiB")
        print(f"loudest bed on the station {bank['loudest_bed_dba']:.1f} dBA "
              f"-> master trim {bank['master_trim_db']:+.2f} dB for "
              f"{RUNTIME_HEADROOM_DBFS:.0f} dBFS headroom")
    if a.plots:
        os.makedirs(DOCS, exist_ok=True)
        st = _build_streams()
        plot_spectra(st, os.path.join(DOCS, "audio-spectra.png"))
        plot_day(os.path.join(DOCS, "audio-day.png"),
                 ("zocalo", "qtr_civilian", "docking_bays", "customs_north",
                  "downbelow", "reactor_hall", "central_corridor"))
        plot_seam(st, os.path.join(DOCS, "audio-seam.png"))
        print(f"wrote docs/audio-spectra.png, audio-day.png, audio-seam.png")
    if a.selftest or not (a.write or a.plots or a.report):
        ok = _selftest()
    if a.report:
        print()
        report()
    raise SystemExit(0 if ok else 1)
