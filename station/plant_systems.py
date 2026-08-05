#!/usr/bin/env python3
"""THE PHYSICAL PLANT AS A SYSTEM WITH A LOAD -- capacity, margin, and a way
to lose them.

`docs/MASTER-PLAN.md` P4a item A4a-3 states the gap this closes, and it states
it as an absence rather than a bug: *"power, air, water, waste and rotation
exist as geometry plus a staffing roster. There is no state in which power
drops and lights go out. C&C has a watch roster and controls nothing that can
break. INC-BROWNOUT is an event with a rate, not a system with a load."*

THE FORK, AND IT IS SETTLED HERE
--------------------------------
A4a-3 offers two: a **resource simulation** (each system carries capacity, load
and a degradation curve, feeding the incident generator) or a **scripted-failure
layer**. This module is the first, and the reason is one sentence from the plan
that is checkable rather than stylistic: **no rate in `incident.py` is
authored.** A plant that broke on a script would be the only system aboard whose
behaviour did not derive from station state, and the seam between them would be
a lie -- `incident._r_brownout` would be reading a number nobody could trace.

The scripted layer was not rejected as inferior in every respect. It is cheaper,
it is easier to author for drama, and a resource sim can produce a station that
never visibly breaks. That last risk is real and is answered by measurement
rather than by assertion: `--report` prints how often each system sheds in a
station-year, and `--controls` shows the failure happening.

WHAT A SYSTEM IS HERE
---------------------
Six: power, air, water, food, waste, rotation. Each carries

    demand(hour)    what the station asks of it now, in the system's own unit,
                    derived from `npc/schedule.py`'s activity census, `traffic`,
                    `interior.LAND_USE` and the per-capita figures in
                    `docs/gazetteer/LIFE-SUPPORT-AND-INDUSTRY.md` (L-01..L-06).
                    Nothing here is a rate somebody liked the look of.
    units()         its plant, READ OFF `directory.PLACES`' own function tags --
                    so a place added to the register joins the plant without
                    this file being edited, exactly as `incident.py`'s place
                    sets follow the register.
    capacity()      N+1 against its own design peak (INV-420).
    store           what stands behind it when the plant stops, in hours.
    wear / shed     the degradation curve, and it is a LADDER rather than a
                    slope -- see below.

THE DEGRADATION CURVE IS A REDUNDANCY LADDER, AND IT COST NO NEW CONSTANT
-------------------------------------------------------------------------
The first draft of this module had a power-law wear curve, `(load/knee)**k`,
with `k` fitted so the worst survivable load saturated the maintenance roster.
It was thrown away, and the reason is worth keeping: **a fitted exponent is an
authored rate wearing a derivation's clothes.** Two numbers had to be chosen
(the knee and the exponent) and neither could be refuted by anything in the
repository.

What replaced it was already in `incident.py`, in `_r_brownout`'s own docstring:
*"a shed needs the fault to land while the standby is ITSELF out for repair.
That probability is the standby's unavailability -- `JOB_HOURS` of repair in a
`MACHINE_MTBF_DAYS` cycle."* Generalise that one line and the whole curve falls
out with no free parameter at all:

    a shed needs the running unit to fail AND every remaining spare to be
    unavailable, so  P(shed | fault) = UNAVAIL ** spares.

`spares` is `units_up - ceil(demand / nameplate)` -- an integer that changes as
load rises. So the curve is a **staircase**, each step worth a factor of
1/UNAVAIL = 2,190x, and the step position is set by demand and the step height
by numbers `incident.py` already owns. Redundancy is not a safety factor the
plant has; it is a thing the load spends.

The continuous half is the same idea one level up. `incident.CORRECTIVE_SHARE`
says a maintenance shift is 25% corrective and 75% planned; a unit with no spare
behind it **cannot be taken out of service for planned work**, so the planned
share is deferred and eventually arrives as corrective. That gives the wear
multiplier as `1 / CORRECTIVE_SHARE` = 4.0 with no new number, and the ceiling
as `1 / incident.maint_load_share()` -- the point at which the station breaks
exactly as fast as its roster can fix it, which INV-350 says must not be
crossed. Three states, three derived values, nothing tuned.

WHAT THE REGISTER TURNED OUT TO SAY, AND IT IS THE FINDING
-----------------------------------------------------------
The plant is not uniformly redundant, and nobody designed that -- it is what
`directory.PLACES`' function tags contain when you count them:

    power        3 generating rows + the APU row      N=4
    air          5 producing rows (two of them the drum) N=5
    waste        3 processing rows                    N=3
    food         3 growing rows                       N=3
    water        ONE reclamation row                  N=1
    rotation     ONE driver row                       N=1

**Water reclamation and rotation have no redundant twin anywhere on the
station**, and the sources agree with the register rather than contradicting it:
LIFE-SUPPORT §5.1 says waste is named in three rosettes and is therefore
*distributed*, while §3.1 names water reclamation once. So the two systems the
station cannot do without are the two it cannot fail over -- and what stands
behind water instead is L-04's sourced **30-day reserve**. The station trades
redundancy against storage, and it trades them in opposite directions on its two
most critical loops.

The mirror image is air: five units, and a buffer measured in **hours**, because
the binding constraint is not oxygen. 250 t/day of CO2 into 3.4 M m3 of air
reaches the 1% occupational limit in **5.77 h**, against **26.29 h** for oxygen
to fall to 16%. **Air is the fastest system on the station by two orders of
magnitude, and CO2 is what makes it fast.**

AND THE SECOND HALF OF THAT SENTENCE IS WEAKER THAN THE FIRST, WHICH THIS
MODULE'S OWN SENSITIVITY BOX FOUND AFTER THE SENTENCE WAS WRITTEN. The gate
first asserted "CO2 binds at every corner of INV-423's declared bounds" and
**the box refuted it**: at the one corner where the CO2 limit is taken at its
most permissive (3%) *and* the O2 limit at its most conservative (19.5%)
simultaneously, O2 binds first at 7.89 h. CO2 binds at the other three corners
and at the declared values, by 4.6x. So the claim that survives is not *which
gas* binds -- it is that **the air buffer is 3-18 hours at every corner of the
box**, against water's 720. The docstring was corrected and the check was kept;
the reverse would have been the easy move and the wrong one.

A NEGATIVE RESULT, RECORDED BECAUSE IT LOOKED RIGHT
----------------------------------------------------
Unit capacities were first weighted by each place's built size -- `rooms.bays_in`
x its declared interactables, the same measure `incident.machine_instances` uses.
It is refuted by its own output: `fusion_core` is 10,413 bays and would be
**91% of the station's generation**, `plant_zone` 6,880 bays and **98% of its
waste plant**, so N+1-on-the-largest-unit gave margins of 1,054% and 4,897%.
A size proxy measures FLOOR AREA, and the plant zone is 34 decks of "structure,
tankage and void" by LIFE-SUPPORT §0's own ruling -- not a bigger pump. Units
are equal here, and the reason is printed by `--report` rather than assumed.

WHAT A PLAYER SEES, AND WHERE
------------------------------
A deficit is shed by priority, and the priority is the register's own function
vocabulary sorted by what a station protects: life safety, then habitation, then
work, then leisure (INV-424). A shed place loses a share of its fixtures, and
both of the things that follow are computed with the modules that already own
the question rather than asserted here:

    LIGHT   irradiance falls with the fixture share, so the place goes down
            log2(1/(1-f)) stops -- a number `export_scene.ROOM_EXPOSURE` speaks
            the same units as.
    SOUND   `audio.machinery_lw` gives the room's own fixture sound power, so a
            shed of f drops it by 10 log10(1-f) dBA.

`--report` names the places, the stops, the dBA and the heads standing in them.

THE SEAM TO `incident.py`, AND IT IS INERT UNTIL SOMETHING BREAKS
------------------------------------------------------------------
Three functions exist for `incident.py` to call, and every one of them returns
**exactly today's value at the nominal plant state**:

    wear_at(place, hour)      1.0   -> INC-FAULT unchanged
    shed_factor("power", h)   UNAVAIL -> INC-BROWNOUT unchanged (power holds
                                         exactly one spare at every hour)
    scarcity("food", hour)    1.0   -> INC-STOCKOUT unchanged

That is deliberate and it is gated: `--gate` computes the patched and unpatched
rate functions side by side and asserts they agree to 1e-12 at the datum, so the
patch cannot move `incident.py --gate` off 33/33. The rates only move when a
unit goes offline -- which is the whole point, and `--controls` shows it.

AND THE GATE APPLIES THE PATCH IN MEMORY AND RUNS IT, WHICH FOUND TWO DEFECTS A
DIFF CANNOT SHOW. Both produced the *same* symptom -- a degraded station-hour
returning byte-identical results to a nominal one, 64 incidents and 94 world
deltas either way -- so neither was distinguishable from "the plant model never
reached the simulation", and neither was distinguishable from the other until
each was ruled out separately.

  1. **`incident._fixed_lams` memoises on a key the plant state is not in.**
     `simulate` does not call the rate functions per step; it calls
     `_fixed_lams`, which caches the whole (class, lambda) list per
     `(day, datum, hour, place)` and never recomputes it. With the patch applied
     and nothing else done, a unit going down changes nothing for the rest of
     the process. This is the session-4c `id(schema)` defect in another module:
     a cache key that omits an input. `set_offline` clears the cache, and the
     patch also widens the key, because a cache that is only correct because
     something else remembers to clear it is not correct.
  2. **Run as a script this module is `__main__`, so the patched file's
     `import plant_systems` built a SECOND COPY** with its own `OFFLINE` set,
     permanently nominal. The guard is three lines below the imports. It is the
     same defect as (1) one level up -- two copies of a state that has to be one
     -- and it is why the fix for (1) appeared not to work.

With both closed, the degraded hour is **168 incidents, 198 world deltas,
INC-BROWNOUT 6** against the nominal hour's 64 / 94 / 0. That is the plant
reaching the existing simulation, measured by running it.

**THIS MODULE HAS NO IMPORTER UNTIL THE PATCH IS APPLIED**, and
`tools/wiring.py --selftest` says so by name. Unapplied, it is instance ten of
the defect CLAUDE.md lists nine of: finished, tested machinery with no caller on
the shipped path. The patch is the caller.

Run: python3 station/plant_systems.py --report     the six systems and their day
     python3 station/plant_systems.py --controls   the four controls, firing
     python3 station/plant_systems.py --patch      the incident.py diff, printed
     python3 station/plant_systems.py --gate       THE GATE
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_ROOT = os.path.dirname(_HERE)

import audio as aud                                            # noqa: E402
import directory as dr                                         # noqa: E402
import economy as ec                                           # noqa: E402
import interior as it                                          # noqa: E402
import populace as pop                                         # noqa: E402
import rooms as rm                                             # noqa: E402
import traffic as tr                                           # noqa: E402
from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(_ROOT, "docs", "gazetteer",
                         "LIFE-SUPPORT-AND-INDUSTRY.md")
SPEC_SYSTEMS = os.path.join(_ROOT, "docs", "spec", "SYSTEMS.md")


# `incident.py` is imported LAZILY and only from inside functions, and that is
# load-bearing rather than tidy. The patch this module ships makes `incident`
# import `plant_systems` at module level; a module-level import back the other
# way would be a cycle. Deferring it means whichever is imported first finishes
# its module body before the other is touched.
# RUN AS A SCRIPT, THIS MODULE IS `__main__` -- AND ANYTHING THAT IMPORTS
# `plant_systems` WHILE IT RUNS GETS A SECOND COPY WITH ITS OWN `OFFLINE` SET.
# That is not hypothetical: `--gate` execs the PATCHED `incident.py`, which
# does `import plant_systems as plant`, and without this line the patched file
# binds to a fresh copy whose plant is forever nominal. The symptom was a degraded
# hour returning byte-identical results to a nominal one -- which is exactly
# the symptom of the cache defect above, from a completely different cause, so
# the two were indistinguishable until each was ruled out separately.
# Aliasing self into `sys.modules` under the canonical name makes the import
# find THIS object. It is the same defect as the stale cache key one level up:
# two copies of a state that has to be one.
if __name__ == "__main__" and "plant_systems" not in sys.modules:
    sys.modules["plant_systems"] = sys.modules[__name__]

_INC = [None]


def _inc():
    if _INC[0] is None:
        import incident                                       # noqa: E402
        _INC[0] = incident
    return _INC[0]


_ONCE = {}


def _memo(key, fn):
    if key not in _ONCE:
        _ONCE[key] = fn()
    return _ONCE[key]


def _schema():
    return _memo("schema", it.load)


def q_of(place_key):
    return _memo("qidx", lambda: {p["key"]: p for p in dr.PLACES}).get(place_key)


# ===========================================================================
# 1.  THE SOURCED AND DERIVED DEMANDS
# ===========================================================================
# Every figure in this section is `docs/gazetteer/LIFE-SUPPORT-AND-INDUSTRY.md`,
# cited by its own L-number, and `docs/spec/SYSTEMS.md` SYS-07 restates the
# headline four. Nothing here is new. Where a per-capita rate exists it is used
# rather than the station total, so the totals MOVE when the population does --
# which is what makes the population control able to fire at all.
HEADCOUNT = int(sched.STATION_HEADCOUNT)          # 250,001, schedule.py

# --- L-02, atmosphere -------------------------------------------------------
O2_KG_PER_HEAD_DAY = 0.84            # L-02
CO2_KG_PER_HEAD_DAY = 1.0            # L-02
HABITABLE_M3 = 3.4e6                 # L-02, "~3.4 M m3"

# --- L-04, water ------------------------------------------------------------
WATER_DRINK_L_HEAD_DAY = 3.0         # L-04
WATER_HYGIENE_L_HEAD_DAY = 50.0      # L-04, "rationed"
WATER_RESERVE_DAYS = 30.0            # L-04, "30-day strategic reserve"

# --- L-05, food -------------------------------------------------------------
FOOD_KG_PER_HEAD_DAY = 1.8           # L-05, wet mass

# --- L-06, waste ------------------------------------------------------------
WASTE_SOLID_KG_HEAD_DAY = 0.15       # L-06, dry organic
WASTE_OTHER_T_DAY = 40.0             # L-06, packaging/industrial; a station
                                     # total, not per capita, so it does NOT
                                     # scale with the population control -- and
                                     # the control prints that it did not.

# --- L-01, power ------------------------------------------------------------
# THE LADDER IS THE SHAPE AND THE TOTAL IS THE FACT. L-01's own closing
# paragraph says the radiator cross-check "is worth more than the table above
# it", and `docs/spec/SYSTEMS.md` SYS-07 freezes the total: "power (~1.9 GW
# demand ladder)". The rows below are that table, used for WHICH LOAD RESPONDS
# TO WHAT rather than as seven independent facts.
#
# AND ONE OF THE ROWS DOES NOT COMPUTE FROM ITS OWN STATED BASIS, which is
# recorded here rather than quietly corrected. Habitat lighting is tabled at
# 600 MW on a basis of "4.5 M m2 ... at 15 W/m2 ... only the ~40% under arable
# bands": 4.5e6 x 15 = 67.5 MW, and 40% of that is 27 MW. The number is
# reachable at ~333 W/m2 over the 1.8 M m2 of arable -- which is the right
# order for horticultural lighting -- so the ROW is defensible and its BASIS is
# mis-stated by a factor of ~9-22. Correcting the row downward would put the
# total at ~1.35 GW, still inside the decade the radiators bound, so no
# conclusion here depends on it. Flagged for the gazetteer, not patched here:
# this module does not own that file.
POWER_LADDER = (
    ("habitat_lighting", 600.0, "drum"),
    ("interior_services", 250.0, "interior"),
    ("atmosphere", 180.0, "air"),
    ("water_reclamation", 90.0, "water"),
    ("rotation", 5.0, "flat"),
    ("industry", 400.0, "industry"),
    ("docking_traffic_defence", 350.0, "berth"),
)
POWER_TOTAL_MW = sum(r[1] for r in POWER_LADDER)      # 1,875 MW ~ L-01's 1.9 GW

# INV-421. The one split in the power shape that is not read off another
# module: how much of L-01's "interior lighting and services" row follows the
# people and how much is corridor lighting that never turns off. 0.5.
# BOUNDED ABOVE by 1.0 -- every watt following occupancy would mean the
# corridors go dark at 03:00, which `export_scene`'s corridor rig refutes,
# since the anchor frame that defines this project's exposure is lit at a fixed
# level. BOUNDED BELOW by 0.0 -- no watt following occupancy would mean 251
# decks of displays, doors and comms draw the same at 03:00 as at 13:00, which
# `schedule`'s own census refutes (160,342 of 250,001 are asleep at 03:00).
# The gate prints the margin at both bounds; the conclusion does not turn on it.
INTERIOR_SERVICES_FOLLOWING_PEOPLE = 0.5

# INV-422. The physiology behind the diurnal air and water curves. A sleeping
# body still breathes, so O2 draw does not follow the awake fraction; it
# follows a metabolic rate that is LOWER asleep. This is the sleeping rate as a
# fraction of the 24-hour mean.
# BOUNDED ABOVE by 1.0 (no diurnal variation at all -- refuted by L-04's own
# separation of 3 L/day of drinking from 50 L/day of hygiene, since hygiene
# does not happen while asleep, so the station's metabolic day is demonstrably
# not flat). BOUNDED BELOW by ~0.6 (a 40% metabolic drop in sleep is far outside
# anything a mammal does; basal rate during sleep is a few per cent under
# resting). Overturned by any figure for the station's own O2 draw curve.
METABOLIC_SLEEP_RATIO = 0.85

# INV-423. The CO2 and O2 limits the air buffer is measured against. 1% CO2 by
# volume is the standard prolonged-exposure limit; 16% O2 is where unimpaired
# function ends. BOUNDED: CO2 0.5% (a conservative habitat set point) to 3%
# (frank impairment); O2 19.5% (the usual "oxygen deficient" trigger) to 16%.
# `--report` prints the buffer at both ends of both bounds, and the ORDERING --
# CO2 binds before O2 -- holds across the whole box, which is the finding.
CO2_LIMIT_FRACTION = 0.01
CO2_AMBIENT_FRACTION = 0.0004
O2_LIMIT_FRACTION = 0.16
O2_AMBIENT_FRACTION = 0.21
AIR_DENSITY_KG_M3 = 1.225            # sea-level standard; the station holds
                                     # "six atmospheres" (L-02 §2.1, auth 1)
                                     # and numbers none of them, so the
                                     # standard one is used and declared.
CO2_DENSITY_KG_M3 = 1.842            # CO2 at 20 C, 101 kPa
O2_MASS_FRACTION = 0.232             # O2 share of air by mass at 21% by volume
AIR_CP_J_KG_K = 1005.0               # specific heat of air at constant pressure
METABOLIC_W_PER_HEAD = 100.0         # INV-423: sensible heat per person.
                                     # BOUNDED 80 W (sleeping) to 120 W (light
                                     # activity). Only used for the thermal
                                     # clock, which is reported as a LOWER
                                     # BOUND on time because it counts the air's
                                     # heat capacity and not the structure's.


# ===========================================================================
# 2.  THE DIURNAL SHAPES -- every one read off a module that already has it
# ===========================================================================
HOURS = tuple(float(h) for h in range(24))


def _activity_day():
    """`schedule.population_activity` for all 24 hours. One call per hour."""
    return _memo("act", lambda: tuple(sched.population_activity(h)
                                      for h in HOURS))


def awake_heads(hour):
    """Station-wide heads not asleep, from `schedule`'s own activity census."""
    c = _activity_day()[int(hour) % 24]
    tot = sum(c.values())
    return tot - c[sched.Activity.SLEEP]


def eating_heads(hour):
    """Heads in `Activity.EAT`. THE FOOD CURVE IS THIS AND NOTHING ELSE."""
    return _activity_day()[int(hour) % 24][sched.Activity.EAT]


def industrial_on_duty(hour):
    return sched.role_on_duty("industrial", float(int(hour) % 24))


def berth_load(hour):
    """Bays occupied over the schema's own bay count -- `traffic`'s answer."""
    def go():
        s, _p = _schema()
        n = float(tr.bay_count(s))
        return tuple(tr.berths_in_use(h, 1)["bay"] / n for h in HOURS)
    return _memo("berth", go)[int(hour) % 24]


def drum_lit(hour):
    """Is the drum's non-arable ground lit now?

    NOT A CHOSEN DAY LENGTH. L-05's yield argument requires the arable bands to
    be under "permanent artificial light with no seasons", so `interior.LAND_USE`'s
    arable share never goes dark. The rest of the floor is where people live,
    and the station clock is the human one (`schedule.RHYTHMS["human"]`, auth 1
    for the clock) -- so the drum's night IS the human sleep window, 23:00 to
    06:30. That makes the drum's day a fact about the roster rather than a
    lighting decision, and it moves if the rhythm table moves.
    """
    r = sched.RHYTHMS["human"]
    h = float(hour) % 24.0
    start = r.sleep_start % 24.0
    end = (r.sleep_start + r.sleep_hours) % 24.0
    dark = (start <= h or h < end) if start > end else (start <= h < end)
    return 0.0 if dark else 1.0


def arable_share():
    """`interior.LAND_USE`'s arable fraction of the drum floor. L-05 uses 48%."""
    return _memo("arable", lambda: sum(f for f, kind, _h in it.LAND_USE
                                       if kind == "arable"))


def metabolic_heads(hour):
    """Heads weighted by metabolic rate: asleep at INV-422's ratio, awake at
    whatever makes the day integrate to the population.

    So the CURVE is `schedule`'s census and the LEVEL is L-02's 0.84 kg/head/day
    -- neither is invented here, and the only free parameter is the ratio, which
    is bounded and whose sensitivity the gate prints.
    """
    def solve():
        # awake_rate chosen so sum over the day of (asleep*ratio + awake*rate)
        # equals sum over the day of total heads.
        tot = sum(sum(_activity_day()[h].values()) for h in range(24))
        asleep = sum(_activity_day()[h][sched.Activity.SLEEP] for h in range(24))
        awake = tot - asleep
        return (tot - asleep * METABOLIC_SLEEP_RATIO) / max(1.0, awake)
    rate = _memo("metrate", solve)
    c = _activity_day()[int(hour) % 24]
    tot = sum(c.values())
    sl = c[sched.Activity.SLEEP]
    return sl * METABOLIC_SLEEP_RATIO + (tot - sl) * rate


def _normalise(fn):
    """A 24-hour shape with mean 1.0. Every ladder row uses one of these, so a
    row's tabled value is its DAILY MEAN and the peak is derived rather than
    tabled."""
    vals = [fn(h) for h in HOURS]
    m = sum(vals) / 24.0
    if m <= 0.0:                                             # pragma: no cover
        return tuple(1.0 for _ in vals)
    return tuple(v / m for v in vals)


def shape(name):
    """The named diurnal shapes, each mean-normalised, each from a module."""
    def go():
        if name == "flat":
            return tuple(1.0 for _ in HOURS)
        if name == "air":
            return _normalise(metabolic_heads)
        if name == "water":
            return _normalise(_water_shape_raw)
        if name == "food":
            return _normalise(eating_heads)
        if name == "industry":
            return _normalise(industrial_on_duty)
        if name == "berth":
            return _normalise(berth_load)
        if name == "drum":
            a = arable_share()
            return _normalise(lambda h: a + (1.0 - a) * drum_lit(h))
        if name == "interior":
            k = INTERIOR_SERVICES_FOLLOWING_PEOPLE
            aw = _normalise(awake_heads)
            return tuple((1.0 - k) + k * v for v in aw)
        raise KeyError(name)                                 # pragma: no cover
    return _memo(("shape", name), go)


def _water_shape_raw(hour):
    """Drinking is flat over the day; hygiene happens while awake. L-04's own
    3 L / 50 L split does all the work -- there is no third number."""
    aw = awake_heads(hour)
    tot = sum(_activity_day()[int(hour) % 24].values())
    drink = WATER_DRINK_L_HEAD_DAY * tot / 24.0
    hyg = WATER_HYGIENE_L_HEAD_DAY * aw
    return drink + hyg


# ===========================================================================
# 3.  THE PLANT, READ OFF THE REGISTER
# ===========================================================================
# A system's units are `directory.PLACES` rows carrying its PRODUCTION
# functions. Two rules separate the plant from the things beside it, and both
# are the register's own vocabulary rather than a place list:
#
#   CONTROL  a row whose functions include `monitoring` or `control` is that
#            system's control room and produces nothing. Over the 129 rows that
#            is exactly `atmos_monitor` and `waste_control`, and it correctly
#            does NOT catch `reactor_hall`, whose tag is `reactor_control`.
#   STORE    a row carrying a storage function holds the system's buffer and
#            does not make capacity.
CONTROL_FUNCTIONS = frozenset({"monitoring", "control"})
STORE_FUNCTIONS = frozenset({"water_storage", "fuel_storage",
                             "hazardous_storage"})

PRODUCTION = {
    "power": ("power_generation", "emergency_power"),
    "air": ("air_handling", "atmosphere_plant", "oxygen_production"),
    "water": ("water_reclamation",),
    "food": ("food_production", "agriculture"),
    "waste": ("waste_processing",),
    "rotation": ("rotation",),
}
STORAGE = {
    "power": (),
    "air": ("atmosphere_feedstock",),
    "water": ("water_storage",),
    "food": (),
    "waste": (),
    "rotation": (),
}
# Where a shed is DELIVERED. Generation makes the watts; a district feed is
# what drops out. `INC-BROWNOUT`'s escalation column says "district lights step
# down", and these are the rows that do it.
DISTRIBUTION = {"power": ("power_distribution",)}


def _rows_with(*functions):
    want = set(functions)
    return tuple(p["key"] for p in dr.PLACES if want & set(p["functions"]))


def is_control_room(place_key):
    q = q_of(place_key)
    return bool(q and CONTROL_FUNCTIONS & set(q["functions"]))


def units(system):
    """The producing units of a system, in register order."""
    return _memo(("units", system), lambda: tuple(
        k for k in _rows_with(*PRODUCTION[system]) if not is_control_room(k)))


def control_rooms(system):
    return _memo(("ctrl", system), lambda: tuple(
        k for k in _rows_with(*PRODUCTION[system]) if is_control_room(k)))


def stores(system):
    return _memo(("stores", system), lambda: _rows_with(*STORAGE[system])
                 if STORAGE[system] else ())


def feeds(system):
    return _memo(("feeds", system),
                 lambda: _rows_with(*DISTRIBUTION[system])
                 if system in DISTRIBUTION else ())


def system_places(system):
    """Every register row this system owns -- plant, store, control, feed."""
    return _memo(("sysp", system), lambda: tuple(dict.fromkeys(
        units(system) + stores(system) + control_rooms(system)
        + feeds(system))))


def plant_places():
    """Every row owned by any system. `wear_at` is 1.0 everywhere else."""
    return _memo("plantp", lambda: tuple(dict.fromkeys(
        k for s in SYSTEM_KEYS for k in system_places(s))))


def systems_at(place_key):
    def go():
        idx = {}
        for s in SYSTEM_KEYS:
            for k in system_places(s):
                idx.setdefault(k, []).append(s)
        return {k: tuple(v) for k, v in idx.items()}
    return _memo("sysat", go).get(place_key, ())


# ===========================================================================
# 4.  DEMAND, CAPACITY, MARGIN
# ===========================================================================
class Sys:
    """A system is a set of LOAD ROWS, each with its own daily mean and its own
    diurnal shape, plus a store and a plant.

    Rows rather than one curve because L-01's power ladder genuinely is seven
    loads on seven drivers, and because waste is a per-capita organic stream
    plus a flat station stream -- and collapsing either into a single shape
    would lose exactly the distinction the population control tests.
    """

    __slots__ = ("key", "title", "unit", "rows", "store_fn", "store_why",
                 "why")

    def __init__(self, key, title, unit, rows, store_fn, store_why, why):
        self.key = key
        self.title = title
        self.unit = unit
        self.rows = tuple(rows)
        self.store_fn = store_fn
        self.store_why = store_why
        self.why = why

    def daily_mean(self, heads=None):
        h = HEADCOUNT if heads is None else heads
        return sum(fn(h) for _name, fn, _shp in self.rows)

    def raw_demand(self, hour, heads=None):
        """What the CONSUMER asks for right now. Taps running, mouths eating."""
        h = HEADCOUNT if heads is None else heads
        i = int(hour) % 24
        return sum(fn(h) * shape(shp)[i] for _name, fn, shp in self.rows)

    def raw_day(self, heads=None):
        return tuple(self.raw_demand(h, heads) for h in HOURS)

    # ---- THE PLANT SEES A DIFFERENT CURVE FROM THE TAP, AND THE STORE IS THE
    # ---- DIFFERENCE. This is the correction that a first draft of this module
    # ---- got wrong, and the wrong version is worth recording because it looked
    # ---- fine: food demand was driven by `schedule.Activity.EAT` directly, so
    # ---- the FARM was asked for 936 t/day at 13:00 against a 450 t/day mean --
    # ---- 4.7x -- and the N+1 rule then sized the hydroponics racks and the
    # ---- drum's fields to lunchtime. A field does not grow faster at lunchtime.
    # ---- A store is a LOW-PASS FILTER on the plant's load, which is literally
    # ---- what a buffer tank is for, so the plant's curve is the consumer's
    # ---- curve smoothed over the store's own length. One rule, no cases:
    # ----   store 0 h  -> no smoothing at all -> the plant sees the peak
    # ----                 (power: there is no way to store a gigawatt)
    # ----   store 6 h  -> a six-hour moving average (air: the room air itself)
    # ----   store >=24 -> flat -> the plant sees the daily MEAN
    # ----                 (water, food, waste: tanks and larders)
    # ---- and the diurnal curve still does work in the stored systems, because
    # ---- `store_turnover` measures how much of the reserve the ordinary day
    # ---- already spends.
    def plant_day(self, heads=None):
        raw = self.raw_day(heads)
        w = store_hours(self.key, heads)
        return _smooth_circular(raw, w)

    def demand(self, hour, heads=None):
        return self.plant_day(heads)[int(hour) % 24]

    def peak(self, heads=None):
        return max(self.plant_day(heads))


def _smooth_circular(vals, width_h):
    """A circular moving average of a 24-hour curve over `width_h` hours.

    width <= 1 returns the curve unchanged; width >= 24 returns the flat mean.
    Fractional widths are handled by weighting the partial end bucket, so the
    filter is continuous in the store size rather than stepping at integers.
    """
    n = len(vals)
    if width_h is None or width_h <= 1.0:
        return tuple(vals)
    if width_h >= float(n):
        m = sum(vals) / float(n)
        return tuple(m for _ in vals)
    out = []
    full = int(math.floor(width_h))
    frac = width_h - full
    for i in range(n):
        acc = 0.0
        for j in range(full):
            acc += vals[(i - j) % n]
        acc += frac * vals[(i - full) % n]
        out.append(acc / width_h)
    return tuple(out)


def store_turnover(system, heads=None):
    """Share of the store the ORDINARY DAY spends, with nothing wrong at all.

    The area between the tap curve and the plant curve, over the store. A
    reserve that turns over 3% of itself a day is a reserve; one that turns
    over 60% is a day tank being called a reserve, and the number says which.
    """
    s = BY_KEY[system]
    raw = s.raw_day(heads)
    smooth = s.plant_day(heads)
    # UNITS MATTER HERE AND THE FIRST VERSION GOT THEM WRONG BY 24x, printing
    # a waste tank turning over 422% of itself a day. `raw` and `smooth` are
    # rates in unit/DAY sampled hourly, so an hour's excess is (raw-smooth)/24
    # of a unit, and the store holds store_h * mean / 24 units.
    excess = sum(max(0.0, a - b) for a, b in zip(raw, smooth)) / 24.0
    st = store_hours(system, heads)
    if st in (0.0, float("inf")):
        return 0.0
    cap = st * s.daily_mean(heads) / 24.0
    return excess / max(1e-9, cap)


# --- the load rows ----------------------------------------------------------
def _row(mw, scales_with_people):
    """A power ladder row as a mean function of the population.

    The rows whose basis in L-01 is a per-capita or per-occupant quantity scale
    with the population; the rows whose basis is the STATION -- drum area, deck
    count, berth count, furnace count -- do not, and the population control
    prints which did which.
    """
    if scales_with_people:
        return lambda heads: mw * heads / float(HEADCOUNT)
    return lambda _heads: mw


POWER_ROWS = tuple(
    (name, _row(mw, shp in ("air", "water", "interior")), shp)
    for name, mw, shp in POWER_LADDER)


def _power_demand_mw(hour, heads=None):
    scale = (HEADCOUNT if heads is None else heads) / float(HEADCOUNT)
    tot = 0.0
    for name, mw, shp in POWER_LADDER:
        s = scale if shp in ("air", "water", "interior") else 1.0
        tot += mw * s * shape(shp)[int(hour) % 24]
    return tot


def _air_mean(heads):
    return O2_KG_PER_HEAD_DAY * heads / 1000.0            # t/day of O2


def _water_mean(heads):
    return (WATER_DRINK_L_HEAD_DAY + WATER_HYGIENE_L_HEAD_DAY) * heads / 1000.0


def _food_mean(heads):
    return FOOD_KG_PER_HEAD_DAY * heads / 1000.0


def _waste_organic_mean(heads):
    return WASTE_SOLID_KG_HEAD_DAY * heads / 1000.0


def _waste_other_mean(_heads):
    return WASTE_OTHER_T_DAY


def _rotation_mean(_heads):
    return dict((n, mw) for n, mw, _s in POWER_LADDER)["rotation"]


# --- the stores, each with its own derivation and its own authority ---------
def _store_power(_sys, heads=None):
    """ZERO, and it is architectural rather than an omission. Electricity is
    not stored at gigawatt scale; L-01's four auxiliary power units are
    CAPACITY behind the primary, not a reservoir in front of it, and they are
    already counted as a unit. So power is the only system aboard whose deficit
    is felt in the same second it appears -- which is exactly why canon files a
    brownout as plot-grade and why `INC-BROWNOUT`'s beats begin with "district
    lights step down" and not with a warning."""
    return 0.0


def _store_air(_sys, heads=None):
    """Hours. The SMALLER OF THE TWO COMPOSITION CLOCKS -- and deliberately not
    the smallest of the three.

    `air_clocks` also returns a sensible-heat clock, and at 0.23 h it is the
    smallest number in this module. It is NOT the buffer, because it counts the
    heat capacity of the air and nothing else: the structure a habitat is built
    from outweighs its air by orders of magnitude and is the thermal mass that
    actually absorbs 25 MW of metabolic heat. This project holds no mass for
    that structure, so the honest form of the thermal clock is a LOWER BOUND
    that is known to be far too short, and using it as the store would let an
    unbounded quantity set a bound. It is reported beside the other two with
    that caveat and does no work.
    """
    c = air_clocks(heads)
    return min(c["co2_h"], c["o2_h"])


def _store_water(sys, heads=None):
    return WATER_RESERVE_DAYS * 24.0


def _store_food(sys, heads=None):
    """INV-425. 30 days, and the derivation is that it is the SAME STANDARD as
    the water reserve rather than a second guess: L-04 sizes a strategic
    reserve at 30 days against resupply failure, and food is the other stream
    that arrives by ship (L-05's "three-sourced" diet, one source of which is
    imports). BOUNDED BELOW by the resupply interval -- `traffic` lands 55
    hulls a day, so a few days would be survivable and a reserve shorter than
    that would be no reserve. BOUNDED ABOVE by the drum's own crop cycle: a
    reserve longer than the time to grow a replacement crop is dead mass
    nobody would carry. Overturned by any statement of the station's larder."""
    return 30.0 * 24.0


def _store_waste(sys, heads=None):
    """INV-426. ONE DAY, and it is a different KIND of store from food's --
    which is the point. A strategic reserve protects against resupply failing;
    a balance tank protects against the plant stopping, and it is sized to one
    cycle of the stream it balances. The stream's cycle here is the station-day
    (`schedule`'s meal windows are diurnal and L-06's organic stream is what
    L-05's food becomes). BOUNDED BELOW by `incident.JOB_HOURS` = 4 h -- a
    plant that cannot be taken down for one corrective job is a plant that
    cannot be maintained. BOUNDED ABOVE by the 30-day strategic standard, which
    would be absurd for a stream nobody wants to hold. Overturned by any
    figure for the station's waste tankage."""
    return 24.0


def _store_rotation(sys, heads=None):
    """NOT DERIVABLE, and this module says so rather than inventing it.

    L-01 files rotation as "effectively zero in steady state -- a flywheel in
    vacuum", so the store is the drum's angular momentum and the clock is
    I x omega / torque. `canon/00-MASTER.md` gives the period (33.4716 s) and
    the geometry gives the radius, but NOTHING anywhere in this project gives
    the drum's MASS, and a moment of inertia invented to fill that hole would
    be a number that looks sourced and is not -- hard rule 1, exactly.

    So this returns infinity and `--report` prints WHY. What is derivable, and
    is reported instead, is that the consequence of a rotation outage is not
    gravity: it is the loss of docking torque correction, which is `traffic`'s
    problem and lands in INC-HOLD. Overturned by any figure for the drum's
    mass, or any on-screen statement of spin-down time."""
    return float("inf")


SYSTEMS = (
    Sys("power", "electrical power", "MW", POWER_ROWS, _store_power,
        "no store: electricity is not tanked",
        "L-01's ~1.9 GW ladder, seven rows, each on its own driver"),
    Sys("air", "atmosphere", "t/day O2",
        (("metabolic", _air_mean, "air"),), _store_air,
        "the habitable volume itself, and CO2 binds before O2",
        "L-02: 0.84 kg O2 and 1.0 kg CO2 per head per day"),
    Sys("water", "water", "m3/day",
        (("tap", _water_mean, "water"),), _store_water,
        "L-04's sourced 30-day strategic reserve, 397,500 m3",
        "L-04: 3 L drinking + 50 L rationed hygiene per head per day"),
    Sys("food", "food", "t/day",
        (("eaten", _food_mean, "food"),), _store_food,
        "INV-425: 30 days, the same strategic standard as water",
        "L-05: 1.8 kg wet per head per day, eaten in schedule.Activity.EAT"),
    Sys("waste", "waste", "t/day",
        (("organic", _waste_organic_mean, "food"),
         ("packaging_industrial", _waste_other_mean, "industry")),
        _store_waste,
        "INV-426: one day, a balance tank rather than a reserve",
        "L-06: 0.15 kg dry organic per head per day + 40 t/day other"),
    Sys("rotation", "rotation maintenance", "MW",
        (("torque_correction", _rotation_mean, "berth"),), _store_rotation,
        "not derivable: no drum mass exists anywhere in this project",
        "L-01: ~5 MW, docking torque correction and mass redistribution"),
)
BY_KEY = {s.key: s for s in SYSTEMS}
SYSTEM_KEYS = tuple(s.key for s in SYSTEMS)


# --- capacity: N+1 against the system's own design peak ---------------------
# INV-420. The station has no stated plant capacity anywhere, and one had to be
# derived rather than left out, because "capacity" is the whole difference
# between a system and a roster. The rule is the standard for life-critical
# infrastructure and it is also what canon's own equipment list describes:
# L-01 §1.1 names a *primary* fusion core, *auxiliary* fusion cores and *four*
# auxiliary power units -- an explicitly redundant architecture, authority 3.
#
#   THE PLANT MEETS ITS OWN DESIGN PEAK WITH ONE UNIT OUT.
#
# So per-unit nameplate is peak/(N-1), and total capacity is peak*N/(N-1). The
# margin at design peak is therefore 1/(N-1) and is a FACT ABOUT THE REGISTER
# rather than a number chosen here: a system with more units carries less
# reserve, because redundancy is cheaper when the units are smaller.
#
# N=1 has no N+1 available at all. Those systems are sized to their own peak
# exactly, carry zero margin at peak, and the module reports that as a finding
# rather than smoothing it: water reclamation and rotation are the two, and
# they are the two the station cannot do without.
#
# BOUNDED ABOVE by N+2 (capacity peak*N/(N-2)), which would put a third of the
# station's plant permanently idle -- and the drum, whose growing area is
# sized by L-05's yield argument to *just* feed the station, refutes that
# directly: nothing about this station is built with a third of it spare.
# BOUNDED BELOW by N+0 (capacity = peak), which would mean a single outage is
# always a deficit, and `INC-BROWNOUT`'s "APU pickup" beat refutes that: the
# station is written as having a standby that picks up.
# Overturned by any figure for any unit's output.
def nameplate(system, heads=None):
    n = len(units(system))
    pk = BY_KEY[system].peak(heads)
    if n <= 1:
        return pk
    return pk / float(n - 1)


def capacity(system, offline=(), heads=None):
    up = [u for u in units(system) if u not in set(offline)]
    return nameplate(system, heads) * len(up)


def demand(system, hour, heads=None):
    return BY_KEY[system].demand(hour, heads)


def margin(system, hour, offline=(), heads=None):
    d = demand(system, hour, heads)
    if d <= 0.0:                                             # pragma: no cover
        return float("inf")
    return capacity(system, offline, heads) / d - 1.0


def deficit(system, hour, offline=(), heads=None):
    """The share of demand the plant cannot meet, in [0,1]."""
    d = demand(system, hour, heads)
    if d <= 0.0:                                             # pragma: no cover
        return 0.0
    return max(0.0, 1.0 - capacity(system, offline, heads) / d)


def spares(system, hour, offline=(), heads=None):
    """Units up beyond the number the current load needs running.

    THE DEGRADATION CURVE IS THIS INTEGER. Every step down is worth a factor of
    1/UNAVAIL in the shed rate, and load is what spends it.
    """
    up = len([u for u in units(system) if u not in set(offline)])
    np_ = nameplate(system, heads)
    if np_ <= 0.0:                                           # pragma: no cover
        return 0
    need = int(math.ceil(demand(system, hour, heads) / np_ - 1e-12))
    # NEGATIVE IS MEANINGFUL AND THE FIRST VERSION CLAMPED IT AWAY. -1 means
    # the system is one unit SHORT of what the load needs running, and clamping
    # to zero made "the only water plant is offline" indistinguishable from
    # "the only water plant is running", so `shed_factor` could not see the
    # difference and reported x1.
    return up - max(1, need)


def design_spares(system, heads=None):
    """The spares the system has when NOTHING is wrong -- its worst nominal
    hour, with every unit up.

    DEGRADATION IS LOSS OF MARGIN AGAINST THE DESIGN STATE, NOT ABSENCE OF
    MARGIN, and getting that distinction wrong is what an earlier draft did:
    `wear_at` fired on `spares == 0`, which is permanently true for the two N=1
    systems, so `water_reclamation` and `rotation_drivers` reported a 4x fault
    multiplier on a station where nothing had happened. A single-unit system
    having no standby is a DESIGN FACT the station has always lived with -- it
    schedules that plant's maintenance around an outage, which is exactly why
    L-04 gives it a thirty-day reserve. What degrades a station is losing a
    spare it was built with.
    """
    return _memo(("dspares", system, heads),
                 lambda: min(spares(system, h, (), heads) for h in HOURS))


# ===========================================================================
# 5.  THE BUFFERS -- how long each system survives with its plant stopped
# ===========================================================================
def air_clocks(heads=None):
    """The three clocks on the air system, in hours. CO2, O2 and heat.

    All three are the habitable volume against a per-head production rate, and
    the only reason they differ is which limit binds first. The FINDING is the
    ordering rather than the values: CO2 binds, at about a quarter of the O2
    clock, so the air plant is a SCRUBBER whose failure is felt in hours and
    not an oxygen supply whose failure is felt in a day.
    """
    h = HEADCOUNT if heads is None else heads
    air_kg = HABITABLE_M3 * AIR_DENSITY_KG_M3
    # CO2: headroom between ambient and the limit, in kg, over production.
    co2_head_m3 = HABITABLE_M3 * (CO2_LIMIT_FRACTION - CO2_AMBIENT_FRACTION)
    co2_head_kg = co2_head_m3 * CO2_DENSITY_KG_M3
    co2_kg_h = CO2_KG_PER_HEAD_DAY * h / 24.0
    # O2: the mass between 21% and 16%, over consumption.
    o2_kg = air_kg * O2_MASS_FRACTION
    o2_head_kg = o2_kg * (1.0 - O2_LIMIT_FRACTION / O2_AMBIENT_FRACTION)
    o2_kg_h = O2_KG_PER_HEAD_DAY * h / 24.0
    # Heat: metabolic power into the air's own heat capacity. A LOWER BOUND on
    # time, because the structure's thermal mass is not counted -- it is not
    # known, and counting it would need a mass this project does not have.
    cap_j_k = air_kg * AIR_CP_J_KG_K
    k_per_h = METABOLIC_W_PER_HEAD * h / cap_j_k * 3600.0
    return {"co2_h": co2_head_kg / max(1e-9, co2_kg_h),
            "o2_h": o2_head_kg / max(1e-9, o2_kg_h),
            "heat_h": 5.0 / max(1e-9, k_per_h)}   # 5 K is a room going warm


def store_hours(system, heads=None):
    return BY_KEY[system].store_fn(BY_KEY[system], heads)


def survives_h(system, hour=13.0, offline=None, heads=None):
    """Hours before the store empties, with the named units offline.

    `offline=None` means ALL of them -- "how long does it survive with its
    plant offline", which is denominator #5 in the brief this was built to.
    """
    if offline is None:
        offline = units(system)
    d = deficit(system, hour, offline, heads)
    if d <= 0.0:
        return float("inf")
    st = store_hours(system, heads)
    if st == float("inf"):
        return float("inf")
    return st / d


# ===========================================================================
# 6.  DEGRADATION -- the seam to `incident.py`, and it is 1.0 at nominal
# ===========================================================================
# The module-level offline set mirrors `incident.py`'s `_WORLD_*` pattern
# deliberately: the rate functions this feeds take (place, hour) and adding a
# world parameter would mean changing signatures 27 of the 30 classes ignore.
OFFLINE = set()


def state_key():
    """A cheap, stable token for the current plant state.

    Exists to be put in a cache key. `incident._fixed_lams` memoises a place's
    class rates on `(day, datum, hour, place)` -- and the plant state is now an
    input to two of those rates, so without this the cache is a copy of a
    computed number that can go stale silently. Which is the session-4c defect
    (`id(schema)` as a memo key) in a different module.
    """
    return ",".join(sorted(OFFLINE)) or "-"


def set_offline(*keys):
    """Put named plant units out of service. THIS IS THE ONLY WRITER.

    AND IT MUST INVALIDATE `incident._LAM`, WHICH IS THE ONE THING A STATIC
    READING OF THE PATCH DOES NOT SHOW. `simulate` does not call the rate
    functions per step: it calls `_fixed_lams`, which memoises the whole
    (class, lambda) list for a (day, datum, hour, place) and NEVER RECOMPUTES
    it. So with the patch applied and nothing else done, a one-hour simulation
    run before a unit goes down and one run after return byte-identical results
    -- 64 incidents, 18 INC-FAULT, 94 world deltas, both times -- and it looks
    exactly like a plant model that does not reach the simulation.

    It was found by running the patched file in memory rather than by reading
    the diff, which is CLAUDE.md's own rule twice over: "a static scan can tell
    you a caller exists; only running the thing tells you the caller runs", and
    "an A/B of two runs in one process is not an A/B".

    Invalidating here is the version that needs no second edit to `incident.py`
    and works with or without the patch. The DURABLE fix is to widen the cache
    key, and `--patch` prints that line too -- a cache whose key omits one of
    its inputs is wrong even when something else happens to clear it.
    """
    OFFLINE.clear()
    OFFLINE.update(k for k in keys if k)
    inc = sys.modules.get("incident")
    if inc is not None and hasattr(inc, "_LAM"):
        inc._LAM.clear()
    return tuple(sorted(OFFLINE))


def unavail():
    """A unit's chance of being unavailable when wanted: one corrective job in
    one MTBF cycle. `incident.py`'s own number, not a second copy of it."""
    i = _inc()
    return i.JOB_HOURS / (i.MACHINE_MTBF_DAYS * 24.0)


def wear_ceiling():
    """The multiplier at which the station breaks exactly as fast as its roster
    fixes it. INV-350's own sanity check, inverted."""
    return 1.0 / max(1e-12, _inc().maint_load_share())


def shed_factor(system, hour, offline=None, heads=None):
    """P(a fault here sheds load) -- `_r_brownout`'s missing term, generalised.

    THE EXPONENT IS SPARES *LOST*, NOT SPARES HELD, and the first draft had it
    the other way. `UNAVAIL ** spares` looks like the cleaner statement and it
    is wrong twice over: it makes a single-unit system (water reclamation,
    rotation) shed on EVERY fault at its own design state -- 80 sheds a day on
    a station where nothing has happened -- and it makes a system with two
    spares 2,190x SAFER than `incident.py` currently models, which would move
    `_r_brownout` off a rate that is already calibrated.

    What `UNAVAIL` actually measures at the design state is: given a fault at
    one of this system's places, the chance it becomes a shed. For a redundant
    system that is the standby being out for repair; for a single-unit system
    it is the plant's own internal redundancy -- a hall tiled to 460 bays holds
    460 valves and one valve is not the plant. Both readings give the same
    number, so the design state is `UNAVAIL` for every system alike and the
    exponent counts DEPARTURE from it.

    AND IT SATURATES AT 1.0, which is a statement rather than a clamp: once the
    redundancy is gone every fault is already a shed, and losing further units
    cannot make sheds likelier. It makes the DEFICIT worse instead, and the
    deficit is a different consequence with a different consumer -- `wear_at`
    and `shed_plan`.
    """
    off = OFFLINE if offline is None else offline
    lost = max(0, design_spares(system, heads)
               - spares(system, hour, off, heads))
    return unavail() ** max(0, 1 - lost)


def wear_at(place_key, hour, heads=None):
    """The fault-rate multiplier at a place. 1.0 everywhere the plant is well.

    Three states and no fitted parameter:
      spares >= 1     1.0                     planned maintenance proceeds
      spares == 0     1 / CORRECTIVE_SHARE    a unit that cannot be taken out
                                              of service defers its planned
                                              work, and the whole maintenance
                                              effort becomes corrective
      deficit  > 0    1 / maint_load_share    the roster ceiling: the station
                                              is breaking as fast as it is
                                              being fixed, which INV-350 says
                                              is the bound, not a rate
    """
    syss = systems_at(place_key)
    if not syss:
        return 1.0
    w = 1.0
    for s in syss:
        if deficit(s, hour, OFFLINE, heads) > 0.0:
            w = max(w, wear_ceiling())
        elif spares(s, hour, OFFLINE, heads) < design_spares(s, heads):
            w = max(w, 1.0 / _inc().CORRECTIVE_SHARE)
    return w


def scarcity(system, hour, heads=None):
    """1 + the unmet share. 1.0 at nominal; INC-STOCKOUT's optional seam."""
    return 1.0 + deficit(system, hour, OFFLINE, heads)


# ===========================================================================
# 7.  WHAT A PLAYER SEES -- the shed ladder, in stops and dBA and heads
# ===========================================================================
# INV-424. The order in which load is shed. There is no source for it, and one
# was needed because "the lights go out" has to say WHOSE. The ladder is the
# register's own function vocabulary sorted by what any station protects:
# life safety, then habitation, then work, then leisure. First match wins, and
# a function not named here sits at rank 2 with the working places.
# BOUNDED: no ordering can put medical below leisure and remain a station;
# no ordering can shed nothing, or a deficit has no consequence. What would
# overturn it is any on-screen brownout showing which lights went first --
# S1's "Survivors" and S2's power-loss scenes are the frames to check.
SHED_LADDER = (
    (0, ("medical", "surgery", "triage", "quarantine", "mortuary",
         "air_handling", "atmosphere_plant", "oxygen_production",
         "water_reclamation", "waste_processing", "power_generation",
         "power_distribution", "emergency_power", "reactor_control",
         "command", "defence_command", "fire_control", "traffic_control",
         "sealed_environment", "atmosphere_containment", "rotation")),
    (1, ("residence", "informal_residence", "short_stay", "transit",
         "immigration", "identicard_check", "law_enforcement", "detention",
         "food_production", "agriculture", "food_service", "catering")),
    (3, ("recreation", "gambling", "nightlife", "sport", "observation",
         "viewport", "public_social", "ceremony", "crew_social")),
)
DEFAULT_RANK = 2


def shed_rank(place_key):
    q = q_of(place_key)
    if not q:                                                # pragma: no cover
        return DEFAULT_RANK
    fns = set(q["functions"])
    for rank, names in SHED_LADDER:
        if fns & set(names):
            return rank
    return DEFAULT_RANK


def _place_load_weight(place_key):
    """How much of the station's electrical load a place carries.

    `incident.machine_instances` -- bays x declared interactables -- is the
    register's own measure of how much machinery is in a room, and it is the
    same measure `audio.machinery_lw` counts fixtures with. Reusing it means
    there is no second table of per-room load to drift from the first.
    """
    return _memo(("plw", place_key), lambda: _inc().machine_instances(place_key))


def _total_load_weight():
    return _memo("plwtot", lambda: sum(_place_load_weight(p["key"])
                                       for p in dr.PLACES))


def shed_plan(hour, offline=None, heads=None, limit=8):
    """Which places lose what, in priority order, for the current POWER deficit.

    POWER ONLY, and the first version's mistake is worth recording because it
    passed its own assertion: `shed_plan` took a system argument and happily
    shed *electrical* load across 126 places to answer a WATER deficit,
    reporting that a broken reclamation plant turns the Zocalo's lights off.
    A deficit is only shed as darkness in the one system whose product is
    delivered as electricity and cannot be stored. Every other system's
    consequence is a different physical thing in a different place, and
    `consequence()` derives those separately.

    Returns rows of (place, shed_fraction, stops_of_light, dBA_change, heads).
    """
    off = OFFLINE if offline is None else offline
    d = deficit("power", hour, off, heads)
    if d <= 0.0:
        return []
    need = d * demand("power", hour, heads)
    per_mw = demand("power", hour, heads) / max(1.0, float(_total_load_weight()))
    order = sorted((p["key"] for p in dr.PLACES),
                   key=lambda k: (-shed_rank(k), -_place_load_weight(k), k))
    rows = []
    got = 0.0
    for k in order:
        if got >= need - 1e-9:
            break
        avail = _place_load_weight(k) * per_mw
        if avail <= 0.0:
            continue
        take = min(avail, need - got)
        f = min(1.0, take / avail)
        got += take
        rows.append((k, f, _stops(f), _dba(f), _heads_at(k, hour)))
    return rows[:limit] if limit else rows


def consequence(system, hour, offline=None, heads=None):
    """What a player SEES when this system is short, and where. Derived rows.

    Every line below is computed from the deficit and from a fact this project
    already holds -- L-03's water ration, L-06's Downbelow texture, SYS-14's
    own escalation columns -- rather than being a sentence about mood.
    """
    off = OFFLINE if offline is None else offline
    d = deficit(system, hour, off, heads)
    if d <= 0.0:
        return []
    rows = []
    if system == "power":
        plan = shed_plan(hour, off, heads, limit=0)
        heads_n = sum(r[4] for r in plan)
        rows.append(("<the shed ladder>",
                     f"{len(plan)} places dark or dimmed, {heads_n:,} people "
                     f"standing in them; INV-424 order, leisure first"))
        for k, f, st, db, hd in plan[:4]:
            lw, after = machinery_dba_after(k, f)
            rows.append((k, f"{_stopfmt(st)}, machinery "
                            f"{_dbfmt(lw)} -> {_dbfmt(after)} dBA, "
                            f"{hd:,} present"))
    elif system == "water":
        # L-03, ADOPTED AS A MECHANIC RATHER THAN A NOTE. "Showers are for
        # executive suites and command quarters only" makes hygiene the
        # rationable 50 L of the 53, so a water deficit is not a dry station:
        # it is hygiene cut first, and the reserve stretches by the ratio.
        drink = WATER_DRINK_L_HEAD_DAY / (WATER_DRINK_L_HEAD_DAY
                                          + WATER_HYGIENE_L_HEAD_DAY)
        st = store_hours(system, heads)
        rows.append(("<the ration>",
                     f"hygiene is {1 - drink:.1%} of the draw, so cutting it "
                     f"stretches the {st / 24:.0f}-day reserve to "
                     f"{st / 24 / drink:,.0f} days of drinking water"))
        for k in _rows_with("water_storage") + _rows_with("water_reclamation"):
            rows.append((k, "tank gauges falling; the standpipe queue is the "
                            "visible fact, and L-03 says who still has a tap"))
        for k in _keys_of("downbelow", "downbelow_arch"):
            rows.append((k, "queues at the standpipe -- proximity to the loop "
                            "is the only way to get water without status "
                            "(L-03)"))
    elif system == "air":
        ac = air_clocks(heads)
        rows.append(("<the whole pressurised volume>",
                     f"CO2 rises to the 1% limit in {ac['co2_h'] / max(1e-9, d):.1f} h "
                     f"at this deficit; the air-handling layer of every "
                     f"ambience runs harder before anything says so"))
        for k in units("air"):
            rows.append((k, "compressors at full duty -- LIFE-SUPPORT 2.3's "
                            "'audible from Downbelow' beat, louder"))
    elif system == "food":
        rows.append(("<every counter>",
                     f"INC-STOCKOUT's rate is multiplied by "
                     f"{scarcity(system, hour, heads):.3f}; the boards change "
                     f"and the substitutions start"))
        for k in _by_interact_local("counter", "stall_frame"):
            rows.append((k, "thinner lines, and L-05's three-sourced diet "
                            "shows: the imported class goes first"))
    elif system == "waste":
        st = store_hours(system, heads)
        rows.append(("<the balance tanks>",
                     f"{st / max(1e-9, d):.1f} h of holding at this deficit, "
                     f"then it backs up where the plant is"))
        for k in units(system) + _keys_of("downbelow", "downbelow_arch"):
            rows.append((k, "L-06 5.3's texture, turned up: haze in the light "
                            "shafts, dripping, stained decking, a wet "
                            "mechanical rhythm in the ambience"))
    elif system == "rotation":
        rows.append(("<the berth map>",
                     "not gravity -- the drum is a flywheel in vacuum. What is "
                     "lost is docking torque correction, so clearances slow "
                     "and the stack forms: INC-HOLD, not a spin-down"))
    return rows


def _keys_of(*ks):
    return tuple(k for k in ks if q_of(k) is not None)


def _by_interact_local(*names):
    want = set(names)
    return tuple(p["key"] for p in dr.PLACES if want & set(p["interacts"]))


def _dbfmt(v):
    if v is None or v == float("-inf"):
        return "  --"
    return f"{v:.1f}"


def _stops(f):
    """Stops of light lost when a fraction f of a room's fittings drop out.
    Irradiance is linear in fixture count, and a stop is a doubling."""
    if f >= 1.0:
        return float("inf")
    return -math.log(1.0 - f, 2.0)


def _stopfmt(st):
    """A room that sheds everything is DARK, not "-inf stops". A stop is a
    ratio and a ratio to zero has no logarithm; printing one is how a formatter
    tells you the model reached a boundary case it has a word for."""
    return "DARK" if st == float("inf") else f"-{st:.2f} stops of light"


def _dba(f):
    """dBA the room's machinery layer loses. `audio.py`'s own arithmetic:
    sound power is linear in source count and a decade is 10 dB."""
    if f >= 1.0:
        return float("-inf")
    return 10.0 * math.log10(1.0 - f)


def _heads_at(place_key, hour):
    q = q_of(place_key)
    if not q:                                                # pragma: no cover
        return 0
    return _memo(("heads", place_key, int(hour) % 24),
                 lambda: pop.occupancy(place_key, ec.floor_m2(place_key),
                                       float(int(hour) % 24), rm.archetype(q)))


def machinery_dba_after(place_key, f):
    """The room's actual machinery level after a shed, through `audio.py`.

    Computed rather than asserted: `audio.machinery_lw` owns the question of
    how loud a room's fixtures are, so the shed is applied to ITS number.
    It returns None for a room `rooms.FIXTURES` puts no machinery in -- a
    chapel, a viewing gallery -- and None is the right answer there rather than
    a defect: those rooms have no machinery layer to lose.
    """
    q = q_of(place_key)
    lw, _parts = aud.machinery_lw(q, rm.archetype(q))
    if lw is None:
        return None, None
    return lw, lw + _dba(f)


def affected_heads(hour, offline=None, heads=None):
    """How many people are standing in a place a POWER deficit sheds."""
    rows = shed_plan(hour, offline, heads, limit=0)
    return sum(r[4] for r in rows), len(rows)


# ===========================================================================
# 8.  THE REPAIR LOOP -- 14,430 engineers, and their day is not flat
# ===========================================================================
# INC-FAULT already models the corrective visit; what did not exist was the
# QUEUE. A failure somebody fixes is a system; a failure nobody fixes is a
# countdown, and the difference is whether the arrival rate stays under the
# roster's throughput. Both halves come from `incident.py` and `schedule.py`:
# nothing new is invented here at all.
def corrective_capacity_per_hour(hour):
    """Jobs the maintenance roster can close in this hour.

    `incident.maint_capacity_per_day` divides the roster's whole headcount by a
    day; this asks `schedule.role_on_duty` who is ACTUALLY AT WORK now, so the
    station's ability to repair itself is diurnal -- which it is: 10,430
    engineers are on shift at 13:00 and 2,042 at 03:00.
    """
    i = _inc()
    heads = sum(sched.role_on_duty(r, float(int(hour) % 24))
                for r in i.MAINT_ROLES)
    return heads * i.CORRECTIVE_SHARE / i.JOB_HOURS


def fault_arrivals_per_hour(hour, heads=None, wear_scale=1.0):
    """Faults arriving this hour across the whole register, with wear applied.

    The baseline is `incident.visible_faults_per_day` exactly; the only new
    term is `wear_at`, which is 1.0 everywhere unless the plant is in trouble.
    `wear_scale` exists for the control below and is 1.0 on every real path.
    """
    i = _inc()
    base = i.visible_faults_per_day() / 24.0
    tot = float(_total_load_weight())
    extra = 0.0
    for k in plant_places():
        w = 1.0 + (wear_at(k, hour, heads) - 1.0) * wear_scale
        if w != 1.0:
            extra += base * (_place_load_weight(k) / tot) * (w - 1.0)
    return base + extra


def repair_day(offline=None, heads=None, hours=24, start_backlog=0.0,
               wear_scale=1.0):
    """Run the queue for a day. Returns (peak_backlog, end_backlog, series).

    THE PROPERTY THAT MATTERS IS BOUNDEDNESS, not the value: INV-350's own
    sanity check says the station must not break faster than it can be fixed,
    so a backlog that ends the day where it started is the loop closing and one
    that grows is the loop open.

    AND THE FIRST ATTEMPT AT THE CONTROL COULD NOT OPEN IT, WHICH IS A RESULT
    AND NOT A BUG. Taking the whole plant offline puts the wear multiplier at
    its ceiling everywhere the plant is, and the day's arrivals still clear --
    because INV-350's own headline says the visible faults are 5.92% of the
    roster's corrective capacity, so a 16.89x multiplier is by construction
    exactly the point where the two meet. The station cannot be broken by wear
    alone; the roster is too big. `wear_scale` is therefore the control's
    knob: at 1.0 the loop closes at the ceiling, above 1.0 it opens, and the
    boundary between them IS the ceiling, which is what INV-350 asserts.
    """
    if offline is not None:
        saved = set(OFFLINE)
        set_offline(*offline)
    try:
        b = float(start_backlog)
        peak = b
        series = []
        for h in range(hours):
            b += fault_arrivals_per_hour(h, heads, wear_scale)
            b = max(0.0, b - corrective_capacity_per_hour(h))
            peak = max(peak, b)
            series.append(b)
        return peak, b, tuple(series)
    finally:
        if offline is not None:
            OFFLINE.clear()
            OFFLINE.update(saved)


# ===========================================================================
# 9.  THE PATCH `incident.py` NEEDS -- printed, not applied
# ===========================================================================
PATCH = '''\
--- station/incident.py
+++ station/incident.py
@@ imports @@
 import player as PL
+import plant_systems as plant
 import populace as pop

@@ def _r_brownout(ctx, place, hour): @@
     share = machine_instances(place) / machine_instances_total()
-    unavail = JOB_HOURS / (MACHINE_MTBF_DAYS * 24.0)
+    # A SHED NEEDS EVERY REMAINING STANDBY TO BE OUT, NOT JUST ONE. The
+    # literal below was this expression with the exponent 1 written into it,
+    # which is right only while the power plant holds exactly one spare -- and
+    # it holds exactly one spare only while nothing is offline.
+    # `plant_systems.shed_factor` is UNAVAIL ** max(0, 1 - spares_LOST), so it
+    # returns this same value at the nominal state and saturates at 1.0 once
+    # the redundancy is gone. This line does not move any rate until a
+    # generating unit goes down.
+    unavail = plant.shed_factor("power", hour)
     return visible_faults_per_day() / 24.0 * share * unavail

@@ def _r_fault(ctx, place, hour): @@
     share = machine_instances(place) / machine_instances_total()
-    return visible_faults_per_day() / 24.0 * share
+    # A UNIT WITH NO SPARE BEHIND IT CANNOT BE TAKEN OUT OF SERVICE, so its
+    # planned maintenance is deferred and arrives later as corrective work.
+    # `wear_at` is 1.0 at every place on the station at the nominal state.
+    return (visible_faults_per_day() / 24.0 * share
+            * plant.wear_at(place, hour))

@@ def _fixed_lams(ctx, place, hour): @@
-    key = (ctx.day, ctx.datum, int(hour) % 24, place)
+    # THE PLANT STATE IS AN INPUT TO TWO OF THE RATES BELOW, so it belongs in
+    # this key. Without it a unit going offline mid-process leaves every
+    # already-computed lambda frozen, and a one-hour simulation before and
+    # after the failure returns byte-identical results -- which reads exactly
+    # like a plant model that never reached the simulation. `state_key()` is a
+    # short constant string at the nominal state, so this changes no cache
+    # behaviour until something is actually out of service.
+    key = (ctx.day, ctx.datum, int(hour) % 24, place, plant.state_key())
     t = _LAM.get(key)

@@ OPTIONAL, and only if the food seam is wanted @@
@@ def _r_stockout(ctx, place, hour): @@
-    return p / (ec.RESTOCK_DAYS * 24.0) * crowd(place, hour) / pk
+    # `plant.scarcity("food", hour)` is 1.0 at the nominal state and
+    # 1 + the unmet share when the growing plant is short, so a counter runs
+    # out oftener when the station is short of food and identically otherwise.
+    return (p / (ec.RESTOCK_DAYS * 24.0) * crowd(place, hour) / pk
+            * plant.scarcity("food", hour))
'''

SPEC_ROWS = '''\
docs/spec/SYSTEMS.md -- SYS-07 gains a State line and a harness line:

  **State:** ... plus **live plant state**: six systems (power, air, water,
  food, waste, rotation), each carrying demand derived from the roster and the
  activity census, capacity N+1 against its own design peak over the register's
  own producing rows (INV-420), a store in hours, and a redundancy ladder --
  `spares = units_up - ceil(demand/nameplate)` -- whose every step is worth
  1/UNAVAIL in the shed rate. `station/plant_systems.py`.
  **Check:** with every unit up, `INC-BROWNOUT` and `INC-FAULT` fire at exactly
  the rates they fire at today (asserted to 1e-12); with `water_reclamation`
  offline the water margin is negative within the hour and the 30-day reserve
  is the only thing between the station and a dry tap; with the power plant
  short one unit the shed rate rises by 1/UNAVAIL = 2,190x and named places
  lose named stops of light.
  harness: station/plant_systems.py --gate (exists) + incident.py --gate 33/33.
'''

YAML_ROWS = '''\
# docs/spec/completion.yaml -- regenerate with tools/spec_registry.py after
# the SYS-07 edit above. The rows the registry should emit:
- id: SYS-07
  title: THE PHYSICAL PLANT, LIVE
  state: live
  harness: station/plant_systems.py --gate
  status: GREEN-when-patched
  notes: >-
    six systems with capacity, load, store and a redundancy ladder; the seam to
    SYS-14 is three functions that are identities at the nominal plant state
'''

INVENTIONS = '''\
INV-420  PLANT CAPACITY IS N+1 AGAINST THE SYSTEM'S OWN DESIGN PEAK
  WHAT.  Every system's plant is sized so that it meets its own design peak
         demand with one producing unit out of service. Per-unit nameplate is
         peak/(N-1) where N is the count of `directory.PLACES` rows carrying
         that system's production functions; total capacity is peak*N/(N-1);
         the margin at design peak is therefore 1/(N-1) and is a fact about
         the register rather than a number chosen here.
  WHY.   Nothing in canon or the gazetteer states any plant capacity, and a
         system without one is a roster, not a system. L-01 1.1's equipment
         list is itself an explicitly redundant architecture at authority 3 --
         a *primary* fusion core, *auxiliary* fusion cores, and *four*
         auxiliary power units -- so redundancy is sourced even though its
         size is not.
  BOUNDED ABOVE by N+2 (peak*N/(N-2)): a third of the station's plant
         permanently idle, refuted by L-05's yield argument, which sizes the
         drum's growing area to *just* feed the station -- nothing here is
         built with a third of it spare.
  BOUNDED BELOW by N+0 (capacity = peak): every single outage becomes a
         deficit, refuted by SYS-14's own INC-BROWNOUT escalation column,
         which contains the beat "APU pickup (PLC-122)" -- the station is
         written as having a standby that picks up.
  OVERTURNED BY any figure for any plant unit's output, or any on-screen
         statement of how many reactors the station runs.
  N=1 SYSTEMS have no N+1 available: `water_reclamation` and `rotation_drivers`
         are single register rows, are sized to their own peak exactly, and
         carry zero margin at peak. That is reported as a finding, not smoothed.

INV-421  THE SHARE OF INTERIOR SERVICES THAT FOLLOWS OCCUPANCY -- 0.5
  WHAT.  Half of L-01's "interior lighting and services" row (250 MW) varies
         with the awake population; half is corridor lighting that never
         turns off.
  WHY.   The row's own basis is "251 decks, corridor and room lighting,
         displays, doors, comms", which is two kinds of load in one line.
  BOUNDED ABOVE by 1.0: every watt following occupancy means the corridors go
         dark at 03:00, refuted by the corridor rig that defines this
         project's exposure anchor, which is lit at a fixed level.
  BOUNDED BELOW by 0.0: no watt following occupancy means 251 decks of
         displays and doors draw the same at 03:00 as at 13:00, refuted by
         `schedule.population_activity` -- 160,342 of 250,001 are asleep.
  OVERTURNED BY any statement of the station's lighting control regime.
  SENSITIVITY: `--gate` prints the power margin at both bounds. It moves the
         13:00 margin by under two points and changes no conclusion.

INV-422  THE SLEEPING METABOLIC RATIO -- 0.85 of the 24-hour mean
  WHAT.  A sleeping resident's O2 draw as a fraction of the station's mean
         per-head draw. The awake rate is then solved so that the day
         integrates to L-02's sourced 0.84 kg/head/day.
  WHY.   Air demand cannot follow the awake fraction -- a sleeping body still
         breathes -- but it is not flat either.
  BOUNDED ABOVE by 1.0 (no diurnal variation), refuted by L-04's own split of
         3 L/day of drinking from 50 L/day of hygiene: hygiene does not happen
         while asleep, so the station's metabolic day is demonstrably not flat.
  BOUNDED BELOW by 0.6: a 40% metabolic drop in sleep is far outside anything
         a mammal does.
  OVERTURNED BY any figure for the station's own O2 draw curve.

INV-423  THE AIR BUFFER'S LIMITS -- CO2 1% by volume, O2 16%, 100 W per head
  WHAT.  The thresholds the air system's survival clocks are measured against.
  WHY.   "How long does the station survive with its air plant off" has no
         answer without a limit, and the answer is the most useful number in
         this module: under six hours.
  BOUNDED. CO2 0.5% (a conservative habitat set point) to 3% (frank
         impairment); O2 19.5% (the usual oxygen-deficient trigger) to 16%;
         metabolic heat 80 W (sleeping) to 120 W (light activity).
  THE BOX REFUTED THE FIRST CLAIM MADE FROM IT, and the corrected one is
         narrower. "CO2 binds before O2 at every corner" is FALSE: at CO2 3%
         with O2 19.5% -- the most permissive CO2 limit against the most
         conservative O2 limit, taken together -- O2 binds at 7.89 h against
         CO2's 17.80 h. CO2 binds at the other three corners and at the
         declared values, by 4.6x. WHAT IS ROBUST is that the air buffer is
         3-18 hours over the whole box, two orders under water's 720, so "air
         is the fastest system on the station" does not depend on the numbers
         chosen and "it is a scrubber rather than an oxygen supply" does,
         mildly. Both are printed by `--gate` section G, corner by corner.
  THE THERMAL CLOCK IS DECLARED AND THEN NOT USED, deliberately. At 0.23 h it
         is the smallest number in the module and it counts the heat capacity
         of the air alone; the structure of a habitat outweighs its air by
         orders of magnitude and is what actually absorbs 25 MW. No mass for
         that structure exists in this project, so the clock is a lower bound
         known to be far too short, and letting an unbounded quantity set a
         bound would be worse than reporting it beside the others with the
         caveat attached.
  OVERTURNED BY any statement of the station's atmospheric set points -- the
         customs board's "SIX DIFFERENT ATMOSPHERES" (authority 1) numbers
         none of them, which is why these are declared rather than sourced.

INV-424  THE SHED LADDER -- life safety, habitation, work, leisure
  WHAT.  The order in which electrical load is shed, expressed over
         `directory.PLACES`' own function vocabulary rather than as a place
         list, so a new place joins the ladder by its function.
  WHY.   "The lights go out" has to say whose.
  BOUNDED. No ordering can put medical below leisure and remain a station; no
         ordering can shed nothing, or a deficit has no consequence.
  OVERTURNED BY any on-screen brownout showing which lights went first.

INV-425  THE FOOD RESERVE -- 30 days
  WHAT.  The station's larder, as hours of store behind the food system.
  WHY.   It is the SAME STANDARD as the water reserve rather than a second
         guess: L-04 sizes a strategic reserve at 30 days against resupply
         failure, and L-05's diet is three-sourced with imports as one source.
  BOUNDED BELOW by the resupply interval -- `traffic` lands 55 hulls a day, so
         a reserve shorter than a few days would be no reserve at all.
  BOUNDED ABOVE by the drum's own crop cycle: a reserve longer than the time
         to grow a replacement is dead mass nobody would carry.
  OVERTURNED BY any statement of the station's larder or rationing.

INV-426  THE WASTE BALANCE TANK -- one day
  WHAT.  How long the waste stream can be held with the plant stopped.
  WHY.   It is a different KIND of store from food's, and that is the point: a
         strategic reserve protects against resupply failing, a balance tank
         protects against the plant stopping, and a balance tank is sized to
         one cycle of the stream it balances. The cycle here is the station-day
         -- L-06's organic stream is what L-05's food becomes, and food is
         eaten in `schedule`'s three diurnal meal windows.
  BOUNDED BELOW by `incident.JOB_HOURS` = 4 h: a plant that cannot be taken
         down for one corrective job cannot be maintained.
  BOUNDED ABOVE by the 30-day strategic standard, which would be absurd for a
         stream nobody wants to hold.
  OVERTURNED BY any figure for the station's waste tankage.

INV-427  ROTATION'S STORE IS NOT DERIVABLE, AND THAT IS RECORDED AS A HOLE
  WHAT.  The rotation system reports an infinite store and a stated reason.
  WHY.   L-01 files rotation as "effectively zero in steady state -- a flywheel
         in vacuum", so the store is the drum's angular momentum and the clock
         is I*omega/torque. The period (33.4716 s) and the radius are both
         held; the drum's MASS is not held anywhere in this project, and an
         inertia invented to fill that hole would be exactly the "number that
         looks sourced and is not" hard rule 1 forbids.
  WHAT IS DERIVABLE INSTEAD, and is reported: the consequence of a rotation
         outage is not gravity but the loss of docking torque correction,
         which is `traffic`'s problem and lands in INC-HOLD.
  OVERTURNED BY any figure for the drum's mass, or any on-screen statement of
         spin-down time.
'''


# ===========================================================================
# 10.  REPORT
# ===========================================================================
def _fmt_h(h):
    if h == float("inf"):
        return "     inf"
    if h >= 48.0:
        return f"{h / 24.0:6.1f} d"
    return f"{h:6.1f} h"


def report(out=print, hours=(3.0, 13.0)):
    out("THE PHYSICAL PLANT, LIVE -- six systems with a load")
    out(f"  population {HEADCOUNT:,} (schedule.STATION_HEADCOUNT); "
        f"register {len(dr.PLACES)} places; "
        f"UNAVAIL {unavail():.6e}; wear ceiling x{wear_ceiling():.2f}")
    out("")
    out("  THE TAP AND THE PLANT ARE DIFFERENT CURVES, and the store is the "
        "difference.")
    out("  A system with a tank sees its own daily MEAN; one without sees the "
        "instant.")
    out("")
    out("  system    unit        N   tap@03     tap@13    plant@03   plant@13"
        "   margin@03  margin@13")
    for s in SYSTEMS:
        n = len(units(s.key))
        out(f"  {s.key:9s} {s.unit:11s} {n:2d} {s.raw_demand(3.0):9.1f} "
            f"{s.raw_demand(13.0):10.1f} {demand(s.key, 3.0):11.1f} "
            f"{demand(s.key, 13.0):10.1f} "
            f"{margin(s.key, 3.0) * 100.0:9.1f}% "
            f"{margin(s.key, 13.0) * 100.0:9.1f}%")
    out("")
    out("  system    store   nameplate     capacity   peak/mean(tap)   "
        "store turned over per ordinary day")
    for s in SYSTEMS:
        raw = s.raw_day()
        pm = max(raw) / (sum(raw) / 24.0)
        out(f"  {s.key:9s} {_fmt_h(store_hours(s.key))} {nameplate(s.key):11.1f} "
            f"{capacity(s.key):12.1f} {pm:16.3f}   "
            f"{store_turnover(s.key) * 100:6.2f}%")
    out("")
    out("  WHERE EACH NUMBER COMES FROM")
    for s in SYSTEMS:
        out(f"    {s.key:9s} demand: {s.why}")
        out(f"    {'':9s} plant : {', '.join(units(s.key))}")
        if stores(s.key):
            out(f"    {'':9s} store : {', '.join(stores(s.key))}")
        if control_rooms(s.key):
            out(f"    {'':9s} watch : {', '.join(control_rooms(s.key))}"
                f"  (control room -- makes no capacity)")
    out("")
    out("  THE REDUNDANCY LADDER -- spares, and the shed factor they buy")
    out("    system      spares@03  spares@13   shed factor@13   "
        "one shed every")
    for s in SYSTEMS:
        sf = shed_factor(s.key, 13.0)
        _fpd, every = shed_every(s.key, 13.0)
        out(f"    {s.key:11s} {spares(s.key, 3.0):9d} {spares(s.key, 13.0):10d}"
            f"   {sf:14.6e}   {every}")
    _f, xcheck = shed_every("power", 13.0, scope="all")
    out(f"    CROSS-CHECK: over incident.power_places()' own rows the power "
        f"shed rate is one every {xcheck},")
    out(f"    against the '~16 days' _r_brownout's docstring records. The "
        f"arithmetic here reproduces theirs.")
    out("")
    out("  THE BUFFERS -- with the whole plant stopped, at 13:00")
    for s in SYSTEMS:
        out(f"    {s.key:11s} {_fmt_h(survives_h(s.key, 13.0))}   "
            f"{s.store_why}")
    ac = air_clocks()
    out(f"    air's three clocks: CO2 {ac['co2_h']:.2f} h, "
        f"O2 {ac['o2_h']:.2f} h, sensible heat (+5 K) {ac['heat_h']:.2f} h "
        f"-- CO2 BINDS")
    out("")
    out("  THE REPAIR LOOP -- and the roster's day is not flat")
    out(f"    corrective capacity 03:00 {corrective_capacity_per_hour(3):8.1f} "
        f"jobs/h    13:00 {corrective_capacity_per_hour(13):8.1f} jobs/h")
    out(f"    fault arrivals      03:00 {fault_arrivals_per_hour(3):8.1f} "
        f"faults/h  13:00 {fault_arrivals_per_hour(13):8.1f} faults/h")
    peak, end, _ser = repair_day()
    out(f"    one nominal day: peak backlog {peak:.1f} jobs, "
        f"end-of-day backlog {end:.1f} -- the loop closes")
    out("")


def _plant_faults_per_day(system, scope="units"):
    """Faults a day arriving at this system's plant, at `incident.py`'s own
    base rate.

    `scope="units"` counts only the producing units, which is where a shed can
    originate. `scope="all"` counts every row the system owns -- stores,
    control rooms and district feeds included -- and exists for exactly one
    reason: over the power system it is the same place set
    `incident.power_places()` uses, so it is the CROSS-CHECK that this module's
    arithmetic reproduces `_r_brownout`'s recorded "one district brownout every
    ~16 days" rather than a number of its own.
    """
    i = _inc()
    tot = float(_total_load_weight())
    keys = units(system) if scope == "units" else system_places(system)
    share = sum(_place_load_weight(k) for k in keys) / tot
    return i.visible_faults_per_day() * share


def shed_every(system, hour=13.0, scope="units"):
    """(sheds per day, a human string). The denominator behind the ladder."""
    fpd = _plant_faults_per_day(system, scope) * shed_factor(system, hour)
    if fpd <= 0.0:                                           # pragma: no cover
        return 0.0, "never"
    d = 1.0 / fpd
    return fpd, (f"{d / 365.0:,.1f} station-years" if d >= 365.0
                 else f"{d:,.1f} station-days" if d >= 1.0
                 else f"{fpd:,.1f} a day")


# ===========================================================================
# 11.  THE CONTROLS -- and every one of them has to FIRE
# ===========================================================================
def controls(out=print):                                        # noqa: C901
    fired = []
    out("CONTROL 1 -- TAKE A UNIT OFFLINE. The margin goes negative, the "
        "spares go to zero,")
    out("            the shed factor jumps, and named places lose named stops "
        "of light.")
    for sysname, off in (("power", ("fusion_core", "reactor_hall")),
                         ("water", ("water_reclamation",)),
                         ("air", ("plant_zone", "the_garden"))):
        before_m = margin(sysname, 13.0)
        before_s = spares(sysname, 13.0)
        before_f = shed_factor(sysname, 13.0)
        set_offline(*off)
        after_m = margin(sysname, 13.0, OFFLINE)
        after_s = spares(sysname, 13.0, OFFLINE)
        after_f = shed_factor(sysname, 13.0)
        after_w = max(wear_at(k, 13.0) for k in system_places(sysname))
        surv = survives_h(sysname, 13.0, OFFLINE)
        out(f"  {sysname:8s} offline {', '.join(off)}")
        out(f"           margin {before_m * 100:+8.1f}% -> "
            f"{after_m * 100:+8.1f}%   spares {before_s} -> {after_s}"
            f"   shed factor {before_f:.3e} -> {after_f:.3e} "
            f"(x{after_f / before_f:,.0f})   wear x{after_w:.2f}")
        out(f"           survives {_fmt_h(surv)} on its store")
        for k, what in consequence(sysname, 13.0)[:5]:
            out(f"           {k:24s} {what}")
        fired.append(after_m < before_m and after_f >= before_f
                     and after_w > 1.0)
        set_offline()
    out("")

    out("CONTROL 2 -- EMPTY THE TABLE. With no systems the station has no "
        "plant state at all,")
    out("            which is the pre-4p condition, and every seam function "
        "returns its identity.")
    saved = tuple(SYSTEMS)
    try:
        _blank_systems()
        w = wear_at("reactor_hall", 13.0)
        sf = _unpatched_unavail()
        out(f"  systems {len(SYSTEMS)}; plant places {len(plant_places())}; "
            f"wear_at(reactor_hall) = {w:.6f}; "
            f"no margin is defined for any system")
        out(f"  and the seam is exactly the unpatched literal: "
            f"UNAVAIL = {sf:.6e}")
        fired.append(len(plant_places()) == 0 and w == 1.0)
    finally:
        _restore_systems(saved)
    out(f"  restored: {len(SYSTEMS)} systems, {len(plant_places())} plant "
        f"places")
    out("")

    out("CONTROL 3 -- DOUBLE THE POPULATION. Demand moves; capacity does not; "
        "margins fall.")
    out("            The rows whose basis is the STATION and not the PEOPLE "
        "must NOT move, and")
    out("            they are the control inside the control.")
    dbl = HEADCOUNT * 2
    ok = True
    for s in SYSTEMS:
        t1, t2 = s.raw_demand(13.0), s.raw_demand(13.0, dbl)
        d1 = demand(s.key, 13.0)
        d2 = demand(s.key, 13.0, dbl)
        m1 = margin(s.key, 13.0)
        m2 = capacity(s.key, (), None) / d2 - 1.0
        out(f"  {s.key:9s} tap {t1:10.1f} -> {t2:10.1f} (x{t2 / max(1e-9, t1):.3f})"
            f"   plant {d1:9.1f} -> {d2:9.1f}   margin {m1 * 100:+7.1f}% -> "
            f"{m2 * 100:+7.1f}%")
        # THE TAP IS THE EXACT TEST AND THE PLANT IS THE DIRECTIONAL ONE. Air's
        # plant demand does NOT double exactly (x2.006), and that is the model
        # being right rather than sloppy: doubling the population halves the
        # CO2 clock, which halves the store, which narrows the smoothing window
        # the plant sees. A population change moves an air buffer. Asserting
        # x2.000 on the plant curve would have been asserting that it does not.
        if s.key in ("air", "water", "food"):
            ok = ok and abs(t2 / t1 - 2.0) < 1e-9 and m2 < m1
        if s.key == "rotation":
            ok = ok and abs(t2 / t1 - 1.0) < 1e-9
    out(f"  waste is the interesting row: it is 0.15 kg/head/day of organic "
        f"PLUS a flat 40 t/day of")
    out(f"  packaging and industrial (L-06), so doubling the population "
        f"multiplies it by "
        f"{demand('waste', 13.0, dbl) / demand('waste', 13.0):.3f} and not by "
        f"2 -- which is the")
    out(f"  per-capita/station split being real rather than decorative.")
    fired.append(ok)
    out("")

    out("CONTROL 4 -- THE BEFORE-STATE. The same content assertions run "
        "against the UNPATCHED")
    out("            rate functions, and they fail -- which is the evidence "
        "the patch is needed.")
    ub = _unpatched_brownout_rate("reactor_hall", 13.0)
    pb_ok = _patched_brownout_rate("reactor_hall", 13.0)
    set_offline("fusion_core", "reactor_hall")
    ub2 = _unpatched_brownout_rate("reactor_hall", 13.0)
    pb2 = _patched_brownout_rate("reactor_hall", 13.0)
    set_offline()
    out(f"  INC-BROWNOUT at reactor_hall, 13:00")
    out(f"    plant nominal          unpatched {ub:.6e}   patched {pb_ok:.6e}"
        f"   {'IDENTICAL' if abs(ub - pb_ok) < 1e-18 else 'DIFFER'}")
    out(f"    two generators offline  unpatched {ub2:.6e}   patched "
        f"{pb2:.6e}   x{pb2 / max(1e-30, ub2):,.0f}")
    out(f"  So today's INC-BROWNOUT cannot tell the difference between a "
        f"healthy plant and a")
    out(f"  crippled one: its rate is IDENTICAL in both columns "
        f"({ub:.6e} = {ub2:.6e}). That is")
    out(f"  the assertion failing against the before-state.")
    fired.append(abs(ub - ub2) < 1e-30 and pb2 > pb_ok * 100.0)
    out("")
    out(f"{sum(1 for f in fired if f)} of {len(fired)} controls FIRED")
    return all(fired)


_SAVED_SYSTEMS = []


def _blank_systems():
    global SYSTEMS, SYSTEM_KEYS, BY_KEY
    SYSTEMS = ()
    SYSTEM_KEYS = ()
    BY_KEY = {}
    for k in [k for k in _ONCE if isinstance(k, tuple)
              and k and k[0] in ("units", "stores", "ctrl", "feeds", "sysp")]:
        del _ONCE[k]
    for k in [k for k in _ONCE if isinstance(k, tuple) and k
              and k[0] == "dspares"]:
        del _ONCE[k]
    _ONCE.pop("plantp", None)
    _ONCE.pop("sysat", None)


def _restore_systems(saved):
    global SYSTEMS, SYSTEM_KEYS, BY_KEY
    SYSTEMS = tuple(saved)
    SYSTEM_KEYS = tuple(s.key for s in SYSTEMS)
    BY_KEY = {s.key: s for s in SYSTEMS}
    _ONCE.pop("plantp", None)
    _ONCE.pop("sysat", None)


# --- the two rate functions, both forms, so the gate can diff them ----------
def _unpatched_unavail():
    i = _inc()
    return i.JOB_HOURS / (i.MACHINE_MTBF_DAYS * 24.0)


def _unpatched_brownout_rate(place, hour):
    """`incident._r_brownout` exactly as it stands today, recomputed here so
    the gate can diff the two forms without importing a patched file."""
    i = _inc()
    share = i.machine_instances(place) / i.machine_instances_total()
    return i.visible_faults_per_day() / 24.0 * share * _unpatched_unavail()


def _patched_brownout_rate(place, hour):
    i = _inc()
    share = i.machine_instances(place) / i.machine_instances_total()
    return (i.visible_faults_per_day() / 24.0 * share
            * shed_factor("power", hour))


def _unpatched_fault_rate(place, hour):
    i = _inc()
    share = i.machine_instances(place) / i.machine_instances_total()
    return i.visible_faults_per_day() / 24.0 * share


def _patched_fault_rate(place, hour):
    return _unpatched_fault_rate(place, hour) * wear_at(place, hour)


# ===========================================================================
# 12.  THE GATE
# ===========================================================================
_FAILED = []


def check(cond, what, detail="", out=print):
    ok = bool(cond)
    out(f"  [{'PASS' if ok else 'FAIL'}] {what}")
    if detail:
        out(f"         {detail}")
    if not ok:
        _FAILED.append(what)
    return ok


def gate(out=print):                                            # noqa: C901
    del _FAILED[:]
    n = 0
    out("PLANT SYSTEMS -- THE GATE")
    out("")

    # A. the plant follows the register
    out("A. THE PLANT IS THE REGISTER'S, and the register is read to prove it")
    tot_units = sum(len(units(s)) for s in SYSTEM_KEYS)
    out(f"   {len(SYSTEMS)} systems, {tot_units} producing units, "
        f"{len(plant_places())} register rows owned, of {len(dr.PLACES)}")
    n += 1
    check(all(q_of(k) is not None for s in SYSTEM_KEYS for k in units(s)),
          "every unit is a row in directory.PLACES -- no place key is written "
          "in this file that the register does not carry",
          f"{tot_units} units across {len(SYSTEMS)} systems", out)
    n += 1
    check(set(control_rooms("air")) == {"atmos_monitor"}
          and set(control_rooms("waste")) == {"waste_control"}
          and "reactor_hall" in units("power"),
          "the CONTROL rule separates a watch room from a plant using the "
          "register's own vocabulary, and it does NOT catch reactor_hall "
          "(whose tag is reactor_control, not control)",
          f"air watch {control_rooms('air')}, waste watch "
          f"{control_rooms('waste')}, power units {units('power')}", out)
    n += 1
    check(len(units("water")) == 1 and len(units("rotation")) == 1
          and len(units("air")) > 1,
          "THE FINDING: the two systems the station cannot do without are the "
          "two with no redundant twin, and the register says so rather than "
          "this file",
          f"water N={len(units('water'))} {units('water')}, rotation "
          f"N={len(units('rotation'))}, air N={len(units('air'))}", out)

    # B. demand derives, and moves
    out("")
    out("B. DEMAND IS DERIVED, AND IT MOVES BECAUSE THE STATION DOES")
    for s in SYSTEMS:
        d3, d13 = demand(s.key, 3.0), demand(s.key, 13.0)
        out(f"   {s.key:9s} {d3:11.1f} -> {d13:11.1f} {s.unit:10s} "
            f"(x{d13 / max(1e-9, d3):.3f})   peak {s.peak():11.1f}")
    n += 1
    # THIS CHECK FAILED WHEN IT WAS FIRST WRITTEN AND IT WAS RIGHT TO. It
    # compared `demand()`, which is the PLANT curve, and reported food flat --
    # because food has a thirty-day larder and a farm does not grow faster at
    # lunchtime. The swing is a property of the TAP, and the flatness is a
    # property of the STORE, so the honest assertion is both at once.
    tap = {s.key: s.raw_demand(13.0) / max(1e-9, s.raw_demand(3.0))
           for s in SYSTEMS}
    plant = {s.key: demand(s.key, 13.0) / max(1e-9, demand(s.key, 3.0))
             for s in SYSTEMS}
    out("   tap swing 03->13: "
        + ", ".join(f"{k} x{v:.3f}" for k, v in tap.items()))
    out("   plant swing     : "
        + ", ".join(f"{k} x{v:.3f}" for k, v in plant.items()))
    check(tap["food"] > 1.5 and tap["water"] > 1.5
          and abs(tap["power"] - plant["power"]) < 1e-9
          and abs(plant["food"] - 1.0) < 1e-9
          and abs(plant["water"] - 1.0) < 1e-9,
          "the TAP swings where the consumer does (food is "
          "schedule.Activity.EAT, water is L-04's hygiene split) and the "
          "PLANT is flat wherever a store stands between them -- power, which "
          "has no store, is the one system where the two curves are the same",
          f"tap food x{tap['food']:.3f} water x{tap['water']:.3f}; plant food "
          f"x{plant['food']:.3f} water x{plant['water']:.3f}; power tap and "
          f"plant agree to {abs(tap['power'] - plant['power']):.1e}", out)
    n += 1
    check(abs(_power_demand_mw(13.0) / POWER_TOTAL_MW - 1.0) < 0.35,
          "power stays inside a third of L-01's ~1.9 GW ladder total at every "
          "hour -- the shapes redistribute the day, they do not invent load",
          f"{min(_power_demand_mw(h) for h in HOURS):.0f}-"
          f"{max(_power_demand_mw(h) for h in HOURS):.0f} MW against a tabled "
          f"{POWER_TOTAL_MW:.0f} MW", out)

    # C. capacity, margin, the ladder
    out("")
    out("C. CAPACITY IS N+1 OVER THE REGISTER'S OWN UNIT COUNT (INV-420)")
    for s in SYSTEMS:
        out(f"   {s.key:9s} N={len(units(s.key)):d} nameplate "
            f"{nameplate(s.key):10.1f} capacity {capacity(s.key):11.1f} "
            f"margin@peak {(capacity(s.key) / max(1e-9, s.peak()) - 1) * 100:+7.1f}%"
            f"  margin@13 {margin(s.key, 13.0) * 100:+7.1f}%")
    n += 1
    check(all(abs(capacity(s.key) / max(1e-9, s.peak()) - 1.0
                  - (1.0 / (len(units(s.key)) - 1) if len(units(s.key)) > 1
                     else 0.0)) < 1e-9 for s in SYSTEMS),
          "the margin at design peak IS 1/(N-1) for every system -- so the "
          "reserve is the register's unit count and not a number typed here",
          ", ".join(f"{s.key} 1/{len(units(s.key)) - 1 or 'inf'}"
                    for s in SYSTEMS), out)
    n += 1
    check(all(margin(s.key, 13.0) > -1e-9 for s in SYSTEMS),
          "with every unit up the whole plant is in surplus at 13:00 -- a "
          "model whose nominal state was already broken would be a model of "
          "nothing",
          ", ".join(f"{s.key} {margin(s.key, 13.0) * 100:+.1f}%"
                    for s in SYSTEMS), out)

    # D. the seam is an identity at nominal
    out("")
    out("D. THE SEAM TO incident.py IS AN IDENTITY AT THE NOMINAL STATE")
    set_offline()
    worst_b = worst_f = 0.0
    for k in ("reactor_hall", "plant_zone", "water_reclamation", "zocalo",
              "docking_bays", "hydroponics", "the_garden", "rotation_drivers"):
        if q_of(k) is None:                                  # pragma: no cover
            continue
        ub, pb = (_unpatched_brownout_rate(k, 13.0),
                  _patched_brownout_rate(k, 13.0))
        uf, pf = _unpatched_fault_rate(k, 13.0), _patched_fault_rate(k, 13.0)
        worst_b = max(worst_b, abs(ub - pb) / max(1e-30, ub))
        worst_f = max(worst_f, abs(uf - pf) / max(1e-30, uf))
    hourly = max(abs(shed_factor("power", h) - _unpatched_unavail())
                 for h in HOURS)
    out(f"   worst relative difference over 8 named places: "
        f"INC-BROWNOUT {worst_b:.3e}, INC-FAULT {worst_f:.3e}")
    out(f"   power holds {spares('power', 0.0)}-{spares('power', 13.0)} "
        f"spare(s) at every hour of the day, so shed_factor == UNAVAIL "
        f"everywhere (max deviation {hourly:.3e})")
    n += 1
    check(worst_b < 1e-12 and worst_f < 1e-12 and hourly < 1e-18,
          "the patched rate functions return EXACTLY today's values with the "
          "plant nominal, so applying the patch cannot move incident.py --gate "
          "off 33/33",
          f"brownout {worst_b:.3e}, fault {worst_f:.3e}, shed factor "
          f"{hourly:.3e}", out)
    n += 1
    check(all(wear_at(p["key"], 13.0) == 1.0 for p in dr.PLACES),
          "wear_at is 1.0 at every one of the register's places at the "
          "nominal state -- the multiplier cannot silently be somewhere other "
          "than one",
          f"{len(dr.PLACES)} places", out)

    # E. it can break, and breaking reaches the world
    out("")
    out("E. IT CAN BREAK, AND BREAKING REACHES THE EXISTING SIMULATION")
    set_offline("fusion_core", "reactor_hall")
    m = margin("power", 13.0, OFFLINE)
    sf = shed_factor("power", 13.0)
    wf = wear_at("reactor_hall", 13.0)
    pb = _patched_brownout_rate("reactor_hall", 13.0)
    ub = _unpatched_brownout_rate("reactor_hall", 13.0)
    rows = shed_plan(13.0)
    heads, nplaces = affected_heads(13.0)
    out(f"   two of four generating units offline: margin "
        f"{m * 100:+.1f}%, spares {spares('power', 13.0, OFFLINE)}, "
        f"shed factor {sf:.3e}, wear x{wf:.2f}")
    out(f"   INC-BROWNOUT at reactor_hall {ub:.3e} -> {pb:.3e} "
        f"per hour (x{pb / max(1e-30, ub):,.0f})")
    out(f"   {nplaces} places shed, {heads:,} people standing in them; "
        f"the first five:")
    for k, f, st, db, hd in rows[:5]:
        lw, after = machinery_dba_after(k, f)
        out(f"     {k:22s} {_stopfmt(st):20s} machinery {_dbfmt(lw)} -> "
            f"{_dbfmt(after)} dBA, {hd:,} present")
    n += 1
    check(m < 0.0 and pb > ub * 100.0 and wf > 1.0 and nplaces > 0,
          "a plant in deficit raises the rate of classes that ALREADY EXIST, "
          "sheds named places, and is visible in stops of light and dBA of "
          "ambience -- not in a parallel event stream",
          f"margin {m * 100:+.1f}%, brownout x{pb / max(1e-30, ub):,.0f}, "
          f"wear x{wf:.2f}, {nplaces} places, {heads:,} people", out)
    set_offline()

    # F. the repair loop
    out("")
    out("F. THE REPAIR LOOP -- THE NIGHT OPENS THE QUEUE AND THE MORNING SHIFT CLOSES IT")
    off3 = tuple(units("power")[:3])
    peak0, end0, _ = repair_day()
    peak1, end1, ser1 = repair_day(offline=off3)
    _p3, end3, _s3 = repair_day(offline=off3, hours=72)
    out(f"   nominal day        peak backlog {peak0:9.1f}  end {end0:9.1f}")
    out(f"   three units down   peak backlog {peak1:9.1f}  end {end1:9.1f}  "
        f"trough {min(ser1):9.1f}   after 3 days {end3:9.1f}")
    out(f"   corrective capacity 03:00 {corrective_capacity_per_hour(3):.1f} "
        f"jobs/h vs 13:00 {corrective_capacity_per_hour(13):.1f} jobs/h "
        f"-- the roster's day is not flat")
    set_offline(*off3)
    deg_arr = fault_arrivals_per_hour(13)
    set_offline()
    nom_arr = fault_arrivals_per_hour(13)
    out(f"   arrivals {nom_arr:.1f}/h nominal -> {deg_arr:.1f}/h with three "
        f"units down (wear at its ceiling on the power places), against a "
        f"capacity that runs")
    out(f"   {min(corrective_capacity_per_hour(h) for h in range(24)):.0f}-"
        f"{max(corrective_capacity_per_hour(h) for h in range(24)):.0f} "
        f"jobs/h -- so the queue BUILDS THROUGH THE STATION NIGHT and clears "
        f"on the morning shift:")
    out(f"   a plant failure at 20:00 waits for 08:00, and the backlog is "
        f"periodic rather than divergent (trough {min(ser1):.1f} at "
        f"h={ser1.index(min(ser1))}, 3-day end {end3:.1f} against 1-day "
        f"{end1:.1f})")
    n += 1
    check(end0 <= 1e-6 and peak1 > 100.0 and min(ser1) <= 1e-6
          and abs(end3 - end1) < 1e-6,
          "at the nominal state the day's faults are closed by the day's "
          "roster (INV-350's own bound holding); taking units down opens a "
          "queue hundreds deep that the morning shift still clears, so the "
          "loop is PERIODIC and not divergent -- a loop that could not open "
          "is not a loop, and one that could not close is not a station",
          f"nominal end {end0:.1f}; degraded peak {peak1:.1f}, trough "
          f"{min(ser1):.1f}, 1-day end {end1:.1f}, 3-day end {end3:.1f}", out)
    n += 1
    check(corrective_capacity_per_hour(13) > corrective_capacity_per_hour(3)
          * 2.0,
          "repair capacity is DIURNAL because schedule.role_on_duty is -- the "
          "station is materially worse at fixing itself at 03:00",
          f"{corrective_capacity_per_hour(3):.1f} vs "
          f"{corrective_capacity_per_hour(13):.1f} jobs/h", out)

    # G. the buffers, and the sensitivity of the ones that are invented
    out("")
    out("G. THE BUFFERS, AND THE INVENTED ONES PRINT THEIR OWN SENSITIVITY")
    for s in SYSTEMS:
        out(f"   {s.key:9s} {_fmt_h(survives_h(s.key, 13.0))}  {s.store_why}")
    ac = air_clocks()
    out(f"   air clocks: CO2 {ac['co2_h']:.2f} h | O2 {ac['o2_h']:.2f} h | "
        f"heat(+5 K) {ac['heat_h']:.2f} h")
    box = _air_sensitivity()
    out(f"   INV-423 sensitivity box, all four corners:")
    for c, o, ch, oh, who in box["corners"]:
        out(f"     CO2 limit {c * 100:4.1f}%  O2 limit {o * 100:4.1f}%  ->  "
            f"CO2 {ch:6.2f} h, O2 {oh:6.2f} h  ->  {who} binds "
            f"({min(ch, oh):.2f} h)")
    lo, hi = _interior_sensitivity()
    out(f"   INV-421 sensitivity: power margin@13 is {lo * 100:+.1f}% at "
        f"k=0.0 and {hi * 100:+.1f}% at k=1.0 "
        f"(shipped k={INTERIOR_SERVICES_FOLLOWING_PEOPLE} gives "
        f"{margin('power', 13.0) * 100:+.1f}%)")
    n += 1
    # THE FIRST VERSION OF THIS CHECK ASSERTED "CO2 BINDS AT EVERY CORNER" AND
    # THE BOX REFUTED IT, which is the whole reason for printing a box. At the
    # one corner where the CO2 limit is taken at its MOST PERMISSIVE (3%) and
    # the O2 limit at its MOST CONSERVATIVE (19.5%) simultaneously, O2 binds at
    # 7.89 h. CO2 binds at the other three and at the declared values, by 4.6x.
    # So the docstring's claim was corrected rather than the check: what is
    # robust is not WHICH GAS binds, it is that the air buffer is 3-18 hours at
    # every corner of the box -- two orders under water's month, and the
    # smallest buffer on the station whichever limit you take.
    worst = max(min(c[2], c[3]) for c in box["corners"])
    best = min(min(c[2], c[3]) for c in box["corners"])
    co2_binds = sum(1 for c in box["corners"] if c[4] == "CO2")
    check(worst < 24.0 and best > 1.0 and co2_binds >= 3,
          "the air finding survives its own invention in the form that "
          "matters: the buffer is under a day at EVERY corner of INV-423's "
          "box, and CO2 binds at 3 of the 4 -- 'the air plant is a scrubber' "
          "is a strong claim rather than a certain one, and the box says so",
          f"buffer {best:.2f}-{worst:.2f} h over the box; CO2 binds at "
          f"{co2_binds} of 4 corners; the flip is at CO2 3.0% with O2 19.5%",
          out)
    n += 1
    check(survives_h("water", 13.0) > 100.0 * survives_h("air", 13.0),
          "the station's two extremes are two orders apart and for opposite "
          "reasons -- water has no redundancy and a month of reserve, air has "
          "five units and hours of buffer",
          f"water {_fmt_h(survives_h('water', 13.0))} against air "
          f"{_fmt_h(survives_h('air', 13.0))}", out)

    # H. the four controls
    out("")
    out("H. THE CONTROLS")
    ok = controls(out=lambda *a: None)
    n += 1
    check(ok, "all four controls fire (run --controls to see them)",
          "unit offline / empty table / double population / the before-state",
          out)

    # ------------------------------------------------------------------
    # I.  THE PATCH IS APPLIED IN MEMORY AND RUN, because a diff is not a
    #     demonstration
    # ------------------------------------------------------------------
    out("")
    out("I. THE PATCH, APPLIED IN MEMORY AND RUN THROUGH incident.simulate")
    res = apply_patch_in_memory()
    n += 1
    check(res["anchors_ok"],
          "every line the patch replaces still appears in incident.py EXACTLY "
          "ONCE -- so this gate fails the day that file is edited out from "
          "under the patch, instead of the patch silently rotting",
          f"three anchors, counts {res['anchor_counts']}", out)
    if res["anchors_ok"]:
        out(f"   nominal   {res['nominal'][0]:4d} incidents, "
            f"INC-BROWNOUT {res['nominal'][1]}, INC-FAULT {res['nominal'][2]}, "
            f"{res['nominal'][3]} world deltas")
        out(f"   degraded  {res['degraded'][0]:4d} incidents, "
            f"INC-BROWNOUT {res['degraded'][1]}, "
            f"INC-FAULT {res['degraded'][2]}, "
            f"{res['degraded'][3]} world deltas   "
            f"(fusion_core + reactor_hall offline)")
        out(f"   worst nominal rate difference against the literals the file "
            f"carries today: {res['worst']:.3e}")
        n += 1
        check(res["worst"] < 1e-12,
              "the PATCHED file's own rate functions return exactly today's "
              "values with the plant nominal, over 14 places x 6 hours -- "
              "measured by running it, not by reading it",
              f"{res['worst']:.3e}", out)
        n += 1
        check(res["degraded"][0] > res["nominal"][0]
              and res["degraded"][3] > res["nominal"][3]
              and res["degraded"][1] > 0,
              "and a degraded plant WRITES MORE WORLD FACTS through the "
              "existing simulation -- INC-BROWNOUT actually fires, which it "
              "never does in a nominal hour",
              f"{res['nominal'][0]} -> {res['degraded'][0]} incidents, "
              f"{res['nominal'][3]} -> {res['degraded'][3]} deltas, "
              f"INC-BROWNOUT {res['nominal'][1]} -> {res['degraded'][1]}",
              out)
        n += 1
        check(res["cache_defect_reproduced"],
              "AND THE CACHE DEFECT IS REPRODUCED ON PURPOSE: with "
              "incident._LAM left alone, the degraded hour returns the "
              "IDENTICAL result to the nominal one, because _fixed_lams "
              "memoises on a key the plant state is not in. That is what the "
              "patch's second hunk is for, and this is the control for it",
              f"stale-cache degraded run {res['stale']} against nominal "
              f"{res['nominal']}", out)

    out("")
    out(f"{n - len(_FAILED)} of {n} checks passed")
    for f in _FAILED:
        out(f"  FAILED: {f}")
    return not _FAILED


PATCH_ANCHORS = (
    ("import player as PL                                            "
     "# noqa: E402",
     "import player as PL                                            "
     "# noqa: E402\nimport plant_systems as plant                    "
     "               # noqa: E402"),
    ("    share = machine_instances(place) / machine_instances_total()\n"
     "    unavail = JOB_HOURS / (MACHINE_MTBF_DAYS * 24.0)\n"
     "    return visible_faults_per_day() / 24.0 * share * unavail",
     "    share = machine_instances(place) / machine_instances_total()\n"
     "    unavail = plant.shed_factor(\"power\", hour)\n"
     "    return visible_faults_per_day() / 24.0 * share * unavail"),
    ("def _r_fault(ctx, place, hour):\n"
     "    share = machine_instances(place) / machine_instances_total()\n"
     "    return visible_faults_per_day() / 24.0 * share",
     "def _r_fault(ctx, place, hour):\n"
     "    share = machine_instances(place) / machine_instances_total()\n"
     "    return (visible_faults_per_day() / 24.0 * share\n"
     "            * plant.wear_at(place, hour))"),
)

PATCH_PROBES = ("reactor_hall", "plant_zone", "water_reclamation", "zocalo",
                "docking_bays", "hydroponics", "generator_hall", "fusion_core",
                "mainstage_node", "alpha_substation", "primary_breaker",
                "customs_north", "medlab_one", "downbelow")


def apply_patch_in_memory(offline=("fusion_core", "reactor_hall")):
    """Build the PATCHED `incident.py` in memory, run it, and report.

    A DIFF IS NOT A DEMONSTRATION. This module ships a patch to a file it is
    forbidden to edit, and the only honest evidence that the patch is safe is
    to apply it and run the thing. Nothing is written to disk: the source is
    read, the three replacements are applied to the text, and the result is
    exec'd as a module of its own -- registered under a name that is NOT
    "incident", so the real one this module already imported is untouched.

    The consequence of that isolation is worth stating: `set_offline` clears
    `sys.modules["incident"]._LAM`, and the patched copy is not that module, so
    its cache has to be cleared here by hand. Which is convenient, because
    NOT clearing it is exactly the stale-cache control -- `stale` below is the
    degraded run with the cache left alone, and it comes back identical to the
    nominal one.
    """
    src = open(os.path.join(_HERE, "incident.py")).read()
    counts = tuple(src.count(a) for a, _b in PATCH_ANCHORS)
    if any(c != 1 for c in counts):
        return {"anchors_ok": False, "anchor_counts": counts}
    for a, b in PATCH_ANCHORS:
        src = src.replace(a, b)

    import types
    mod = types.ModuleType("_incident_patched")
    mod.__file__ = os.path.join(_HERE, "incident.py")
    sys.modules["_incident_patched"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)

    ref = _inc()
    worst = 0.0
    ctx = mod.Ctx(day=1)
    probes = [k for k in PATCH_PROBES if q_of(k) is not None]
    power = set(mod.power_places())
    for k in probes:
        for h in (0.0, 3.0, 8.0, 13.0, 19.0, 23.0):
            got = mod._r_fault(ctx, k, h)
            want = _unpatched_fault_rate(k, h)
            worst = max(worst, abs(got - want) / max(1e-30, want))
            if k in power:
                got = mod._r_brownout(ctx, k, h)
                want = _unpatched_brownout_rate(k, h)
                worst = max(worst, abs(got - want) / max(1e-30, want))
    del ref

    def _hour():
        w, fired = mod.simulate(mod.Ctx(day=1, seed="b5"), start_h=13.0,
                                window_min=60.0, step_min=1.0, scope=None)
        by = {}
        for i in fired:
            by[i.cid] = by.get(i.cid, 0) + 1
        return (len(fired), by.get("INC-BROWNOUT", 0), by.get("INC-FAULT", 0),
                len(w.deltas()))

    set_offline()
    mod._LAM.clear()
    nominal = _hour()
    # THE STALE-CACHE CONTROL: change the plant and DO NOT clear the memo.
    set_offline(*offline)
    stale = _hour()
    # And now the same state with the memo cleared, which is what the patch's
    # cache-key hunk buys.
    mod._LAM.clear()
    degraded = _hour()
    set_offline()
    mod._LAM.clear()
    sys.modules.pop("_incident_patched", None)
    return {"anchors_ok": True, "anchor_counts": counts, "worst": worst,
            "nominal": nominal, "stale": stale, "degraded": degraded,
            "cache_defect_reproduced": stale == nominal and degraded != nominal}


def _air_sensitivity():
    """INV-423's declared box, evaluated at all four corners.

    Returns every corner rather than a min/max pair, because the interesting
    thing about this box turned out to be WHERE the ordering flips and not how
    wide it is.
    """
    global CO2_LIMIT_FRACTION, O2_LIMIT_FRACTION
    c0, o0 = CO2_LIMIT_FRACTION, O2_LIMIT_FRACTION
    corners = []
    try:
        for c in (0.005, 0.03):
            for o in (0.16, 0.195):
                CO2_LIMIT_FRACTION, O2_LIMIT_FRACTION = c, o
                a = air_clocks()
                corners.append((c, o, a["co2_h"], a["o2_h"],
                                "CO2" if a["co2_h"] < a["o2_h"] else "O2"))
    finally:
        CO2_LIMIT_FRACTION, O2_LIMIT_FRACTION = c0, o0
    return {"corners": tuple(corners)}


def _interior_sensitivity():
    """INV-421's bounds, as the power margin they produce."""
    global INTERIOR_SERVICES_FOLLOWING_PEOPLE
    k0 = INTERIOR_SERVICES_FOLLOWING_PEOPLE
    out = []
    try:
        for k in (0.0, 1.0):
            INTERIOR_SERVICES_FOLLOWING_PEOPLE = k
            _ONCE.pop(("shape", "interior"), None)
            out.append(margin("power", 13.0))
    finally:
        INTERIOR_SERVICES_FOLLOWING_PEOPLE = k0
        _ONCE.pop(("shape", "interior"), None)
    return out[0], out[1]


def main(argv=None):                                         # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--patch", action="store_true")
    ap.add_argument("--inventions", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args(argv)
    if a.patch:
        print(PATCH)
        print(SPEC_ROWS)
        print(YAML_ROWS)
        return 0
    if a.inventions:
        print(INVENTIONS)
        return 0
    if a.report:
        report()
        return 0
    if a.controls:
        return 0 if controls() else 1
    return 0 if gate() else 1


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
