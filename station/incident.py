#!/usr/bin/env python3
"""THE INCIDENT GENERATOR -- and the deliverable is a RATE, not an incident.

`docs/MASTER-PLAN.md` P1-G3 says it in its own parenthesis: **"(not one
incident)"**. `docs/spec/SYSTEMS.md` SYS-14 says the same thing as an
assertion -- *"classes fire from their trigger systems at their sourced rates,
weighted by district and by SYS-01's era position"*, with a floor of **">=2
meaningful incidents per station-hour inside a fixed probe volume"* and
*"'meaningful' = the incident writes >=1 world delta"*.

So the unit of work here is not an event. It is a **denominator**: how often,
out of what, in which places, and how many of them a person standing in one
spot would be near.

WHAT IT IS
----------
Thirty classes -- **exactly** `docs/spec/PLACES.md` §0.2's vocabulary and
SYS-14's mechanics table, and the gate parses BOTH FILES and asserts the
bijection both ways AND THE COUNT, rather than trusting this file's own list.
(The count used to be written `== 22` here, which made the table's size a fact
about this module rather than about the spec, so growing the table meant
editing the assertion that was guarding it. It is `len(spec_ids(...))` now.)
Each class carries:

    trigger   a rate in incidents per station-hour, computed from station
              state that already exists: `traffic.hall_rate`, `traffic.
              berths_in_use`, `security.hostility`, `security.presence_at`,
              `audio.species_mix`, `schedule.ROLE_WEIGHTS`, `arrival.checks`
              sampled through its own code path, `costume.ERA_EVENTS`.
    places    which register rows it can happen in -- DERIVED from
              `directory.PLACES`' own `functions` and `interacts`, so a class
              follows the register when a place is added or moved.
    cast      named residents from `resident.roster`, at that place, at that
              hour. Not "a thief" -- Nadia Sinclair.
    escalation SYS-14's own beats, quoted in the row.
    writes    named facts into a `World`. Custody rows, docket rows, seizure
              rows, standing changes, stock movements, work orders, card
              endorsements, camp states, casualties, ISN items.

THE LIVED-IN HALF, AND WHY IT IS NOT SIX MORE OFFENCES
-------------------------------------------------------
The first twenty-two skew hard to crime, customs and industrial fault, because
`LAW-CRIME-DOWNBELOW.md` and `TRAFFIC-AND-CUSTOMS.md` are the two gazetteer
documents with rate tables in them. The measurement said so: at 13:00 the
arrival half ran at 10.9/h and Downbelow at 7.1/h, the Zocalo's probe at
0.68/h, and **every residence row on the station at 0.0000/h** -- not "low",
exactly zero, because no class in the table could happen in a home.

The cure is not more offences. `--gate` counts the framing rather than
asserting it: **seven of the original twenty-two book somebody into the brig in
the ABSENT branch** -- what the station does when nobody is watching -- and
**none of the eight added here do.** A residential corridor furnished with six
more crimes would be a crime simulator with flats in it.

  INC-NEIGHBOUR  a dispute across a bulkhead, and THE STATION'S OWN CLOCKS
                 CAUSE IT: `schedule.RHYTHMS` says every Narn aboard is asleep
                 at 03:00 (awake 0.000) and every Centauri is awake (1.000),
                 and at 13:00 it is the Brakiri who are asleep (0.068). That
                 was already in the repository and nothing read it.
  INC-LOCKOUT    a door that will not admit its own tenant. Two causes and the
                 second is the interesting one: `consequence.py`'s rungs, so
                 the same event two decks apart is a call to maintenance or a
                 call to immigration.
  INC-ARREARS    rent arrears -- ENDOGENOUS, and `economy.py` decided that.
  INC-STILL      the camp's own kitchen, still, laundry and barber's chair.
  INC-SICK       somebody needs a clinician and there is not one.
  INC-STRAY      a child where a child should not be.
  INC-MOVEON     a busker moved off the licensed commercial floor.
  INC-STOCKOUT   a counter runs out of a line.

WHAT IS DELIBERATELY *NOT* AN INCIDENT, AND WHERE IT BELONGS
-------------------------------------------------------------
SYS-14's own CHECK is the discriminator and it is worth stating as a rule: an
incident is a thing a player can be **absent from, help with, or report**, and
that yields three different worlds. Apply it honestly and half of residential
life fails it, because **ordinary life is not an incident**:

  * eating, sleeping, coming off shift, the 19:00 crowd, thirteen journeys a
    resident a day -- `npc/life.py` and `populace.py` already carry it, and you
    cannot report somebody's dinner.
  * a species festival week, a faith rota, a wedding, a funeral and its rites,
    the Tuesday combat class, the quarterly drill, an invitation-gated
    reception -- **`docs/spec/SYSTEMS.md` SYS-15, THE CIVIC CALENDAR, and it
    has no code.** These are CALENDAR-shaped, not RATE-shaped: an observance
    that happens at a random hour is not an observance. Forcing them in here
    would have been the wrong mechanism, and the honest answer is that the
    right one does not exist yet.
  * the PA, ISN, the boards, the muster read-out -- `broadcast.py`.
  * a BIRTH, and this one is a finding rather than an omission:
    `schedule.ROLE_WEIGHTS` is a **workforce**, not a population.
    `resident._age` says minors exist in exactly three roles -- visitor,
    refugee and lurker, the ones with no work hours -- so the model has 6,253
    children and **no dependants, no schools, and nobody's parents**. A birth
    rate derived from this station's own data would be zero over 229,000 of
    its 250,001 people. That is `schedule.py`'s question to answer, not this
    file's to paper over.

THE THREE STANCES, AND THEY DIFFER IN NAMED FACTS
-------------------------------------------------
SYS-14's CHECK: *"one seeded incident replayed three ways -- player-absent /
player-helps / player-reports -- yields three world states that differ in NAMED
facts (which ledger row, whose standing, which stock line, who is in custody),
not merely in a log string"*. `three_ways()` runs it and `--gate` diffs the
three fact sets and prints the facts unique to each. **21 of 22 classes give
three distinct states and one gives two** -- INC-PSICOP, where helping and
reporting a Psi Cop's arrival are the same non-act, and that is reported here
rather than hidden.

WHAT IT FOUND ABOUT THE STATION
-------------------------------
1. **The rate floor is a PLACE fact, not a station fact.** The station runs
   ~1,300 incidents a station-day, but only **12 of the 128 probe volumes clear
   SYS-14's >=2/station-hour floor at 13:00** and the median one is at zero.
   The live ones are the arrival half (docking_bays 10.9/h, customs 7.0/h) and
   Downbelow (7.1/h); the commercial ring is quiet (the Zocalo's probe is
   0.7/h) and a residential ring has nothing to go wrong in at all. No
   class-table work changes that, so the gate asserts the floor at a NAMED
   probe and prints the whole distribution rather than picking the number that
   passes.
2. **Two classes are correctly SILENT at the datum and that is content.**
   INC-BRAWL is the Drazi factional cycle, and `docs/spec/PEOPLE.md` FAC-13
   says the spec *"carries the OFF state at datum with the switch existing"* --
   it runs at 0.000/day here and 0.268/day with the switch thrown. INC-DENOUNCE
   is era-gated on `nightwatch_visible` (2,22): 0.000/day at S2E01 against
   6.164/day at the datum. A generator whose every class fires everywhere is a
   generator with no era and no geography.
3. **FOUR classes are ENDOGENOUS -- their rate is another class's
   consequence.** INC-SWEEP fires off camp heat that INC-CONTACT and INC-PICK
   write; INC-STRIKE off the grievance board that INC-ACCIDENT and INC-ELEV
   write; INC-DEBT off the debtor pool the black market fills; INC-HOLD off
   whether an elevator is down. In a world nothing has happened in, three of
   the four are at **exactly zero**; after one station-day they are at 11.0,
   71.7 and 40.5 a day. That is what makes day 2 different from day 1 without
   anybody scripting it.
4. **The maintenance workforce BOUNDS the fault rate.** 14,430 engineers plus
   2,500 waste staff on `schedule.ROLE_WEIGHTS` can close ~8,465 corrective
   jobs a day; the 182,905 declared interactables `rooms.bays_in` tiles across
   the register break at ~501 a day, which is **5.9% of that capacity** -- so
   the thing a player can touch is a small part of what the station maintains,
   which is the right shape (INV-350).

AND FOUR THINGS IT FOUND ABOUT ITSELF, EACH BY A GATE THAT COULD FAIL
---------------------------------------------------------------------
Recorded because the mechanism is more transferable than the fix, and every
one of them was live in a version of this file that "worked".

  * **The MTBF sanity check refuted its own derivation.** `_selftest` divides
    the machine count by the fault rate and demands the answer be in
    months-to-years. First run: **0.04 days** -- a public terminal failing
    every hour. The rate was fine; the DENOMINATOR was 357 interactable TYPES
    where the tiled station has 182,905 INSTANCES. *A derivation is not checked
    until its own units are.*
  * **The step-size control found a rate, not a step.** At 4x the step the
    day's total came back **12.4% low**, and the cause was not coarseness: the
    draw was one coin flip per step, which truncates at one event, and
    INC-DEBT was running at 44/h in one room. Both were wrong -- the rate by an
    order of magnitude and the draw by construction. *A step control measures
    whether anything in the model is too fast for the clock.*
  * **A gate that reached past the code path could not see the era.** The era
    control reported INC-DENOUNCE at 6.164/day at S2E01 AND at the datum,
    because `class_rate_day` called `k.rate` directly while the era test lived
    in `_fixed_lams`. *A gate consulting a different path from the content sees
    none of the content's switches.*
  * **"M reachable" was a tautology.** It simulated the probe volume alone and
    then asserted every incident was inside the probe volume. It now simulates
    all 128 places and counts the probe out of them -- 3 of 37 in the reported
    hour. *If N is not bigger than M, M is not a measurement.*

Run: python3 station/incident.py --report      the class table and its rates
     python3 station/incident.py --day         one headless station-day
     python3 station/incident.py --three-ways  the stance diff, per class
     python3 station/incident.py --selftest    everything offline
     python3 station/incident.py --gate        THE GATE: rate, stances, controls
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_ROOT = os.path.dirname(_HERE)

import arrival as ar                                           # noqa: E402
import audio as aud                                            # noqa: E402
import consequence as cq                                       # noqa: E402
import directory as dr                                         # noqa: E402
import economy as ec                                           # noqa: E402
import interior as it                                          # noqa: E402
import player as PL                                            # noqa: E402
import populace as pop                                         # noqa: E402
import rooms as rm                                             # noqa: E402
import traffic as tr                                           # noqa: E402
from npc import costume as cos                                 # noqa: E402
from npc import friction as fr                                 # noqa: E402
from npc import resident as res                                # noqa: E402
from npc import schedule as sched                              # noqa: E402
from npc import security as sec                                # noqa: E402

SPEC_PLACES = os.path.join(_ROOT, "docs", "spec", "PLACES.md")
SPEC_SYSTEMS = os.path.join(_ROOT, "docs", "spec", "SYSTEMS.md")


# ===========================================================================
# 1.  Determinism -- one hash, and it has to be cheap
# ===========================================================================
# 128 places x 22 classes x 60 one-minute steps is 169,000 draws per
# station-hour, and a 24-hour day is four million. `hashlib` costs about 1 us a
# call, which is four seconds of nothing but hashing, so this is a splitmix64
# over interned string ids instead. It is deterministic, it is a pure function
# of its arguments, and it is ~8x cheaper than blake2b at this size.
_MASK = (1 << 64) - 1
_SIDS = {}


def _sid(s):
    v = _SIDS.get(s)
    if v is None:
        h = 0xCBF29CE484222325
        for ch in s.encode("utf-8"):
            h = ((h ^ ch) * 0x100000001B3) & _MASK
        v = _SIDS[s] = h
    return v


def _mix(x):
    x = (x + 0x9E3779B97F4A7C15) & _MASK
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _MASK
    return (x ^ (x >> 31)) & _MASK


def u(*parts):
    """A uniform in [0,1) from any tuple of strings, ints and floats."""
    h = 0x84222325CBF29CE4
    for p in parts:
        if isinstance(p, str):
            p = _sid(p)
        elif isinstance(p, float):
            p = int(p * 1e6)
        h = _mix(h ^ (p & _MASK))
    return (h >> 11) / float(1 << 53)


# ===========================================================================
# 2.  The clock, the era and the context
# ===========================================================================
STEP_MIN = 1.0            # the tick, in station-minutes. `--step` overrides.
WINDOW_MIN = 60.0         # MASTER-PLAN's own "a 60-minute headless day at x1"


class Ctx:
    """Everything a rate needs to know, and nothing about a player.

    `simulate` takes no observer on purpose -- SYS-14's player surface clause
    is *"none of them requires the player to exist"*, and a generator that can
    see the camera is a cutscene director. The player enters exactly once, in
    `three_ways`, and only to CHOOSE A STANCE toward an incident the world had
    already produced.
    """

    def __init__(self, day=0, datum=cos.ERA_DATUM, seed="b5"):
        self.day = int(day)
        self.datum = cos.era_check(tuple(datum))
        self.seed = seed
        self._rates = {}
        self._arr = None

    def arrivals(self):
        if self._arr is None:
            self._arr = tr.arrivals(self.day)
        return self._arr


def era_on(event, datum):
    return datum >= cos.ERA_EVENTS[event][0]


# ===========================================================================
# 3.  The register's own geometry -- positions, areas, and the PROBE VOLUME
# ===========================================================================
_POS = {}
_SCHEMA = [None, None]


def q_of(place_key):
    """`directory.by_key` RAISES for an unknown key, which is right for the
    register and wrong for a class that asks "is this place here?" -- five of
    the twenty-two draw their places from lists (`security.BLACK_MARKET_ROUTE`,
    `security.NO_POST`) that name rows the register has not grown yet. This is
    the only lookup in this module that is allowed to come back empty."""
    try:
        return dr.by_key(place_key)
    except KeyError:
        return None


def _schema():
    if _SCHEMA[0] is None:
        _SCHEMA[0], _SCHEMA[1] = it.load()
    return _SCHEMA[0], _SCHEMA[1]


def position_m(place_key):
    """A place's world position, in metres, from the register's own address.

    (sector, ring, deck) -> a floor radius through `interior`; angle and z are
    the register's. Double precision throughout -- the z axis runs to 8,047 m
    and hard rule 5 applies to every world-space number in this project.
    """
    if place_key in _POS:
        return _POS[place_key]
    q = q_of(place_key)
    s, p = _schema()
    rings = it.ring_radii(s, p, q["sector"])
    stacks = [i for i, r in enumerate(rings) if r["kind"] == "deck_stack"]
    if stacks:
        ri = stacks[min(int(q["ring"]), len(stacks) - 1)]
        decks = it.decks_in_ring(s, p, q["sector"], ri)
        d = decks[min(int(q["deck"]), len(decks) - 1)]
        rad = float(d["floor_r_m"])
    else:                                                    # pragma: no cover
        rad = float(rings[0].get("r_outer_m", 0.0))
    a = math.radians(float(q["angle_deg"]))
    _POS[place_key] = (rad * math.cos(a), rad * math.sin(a), float(q["z_m"]))
    return _POS[place_key]


def distance_m(a, b):
    pa, pb = position_m(a), position_m(b)
    return math.dist(pa, pb)


class Probe:
    """THE FIXED PROBE VOLUME, and 'fixed' is the whole point.

    SYS-14 is explicit and it is explicit because of a known cheat: *"within
    fixed probe volumes -- the district cell holding the player plus its
    adjacent cells, fixed at tick start (never a floating radius an
    implementation can shrink)"*. A radius chosen after the numbers are in is a
    radius chosen to make the numbers pass.

    So the volume is the register's own topology: the place the player is
    standing in, plus every place `directory.PLACES` lists as `adjacent` to it,
    resolved ONCE at construction. `span_m` then REPORTS the metric size of
    that volume rather than defining it -- it is an output, not an input, and
    it is large (400 m at the Zocalo) because `adjacent` is a topological
    relation on an 8 km station and two adjacent places can be a third of a
    ring apart.
    """

    def __init__(self, at):
        q = q_of(at)
        if q is None:
            raise KeyError(f"{at} is not a register place")
        keys = [at] + [k for k in q["adjacent"] if q_of(k) is not None]
        self.at = at
        self.places = tuple(dict.fromkeys(keys))
        self.span_m = max(
            (distance_m(a, b) for a in self.places for b in self.places),
            default=0.0)
        self.floor_m2 = sum(ec.floor_m2(k) for k in self.places)

    def __contains__(self, k):
        return k in self.places

    def describe(self):
        return (f"{self.at} + {len(self.places) - 1} adjacent "
                f"({', '.join(self.places[1:]) or 'none'}), spanning "
                f"{self.span_m:.0f} m and {self.floor_m2:,.0f} m2 of floor")


# HOW FAR A PERSON CAN SEE AN INCIDENT FROM. Not chosen: `populace` already
# measures the corridor sight line and `audio` already owns the acoustic one.
# An incident is WITNESSED if the player is inside the probe volume and within
# this of it. 60.5 m is `populace.corridor_sight_m`'s Blue-deck figure; it is
# read at call time so it cannot drift from the corridor it describes. The
# probe volume itself -- the register place plus its `adjacent` rows, resolved
# once -- is INV-365, and the reason it is topological rather than metric is
# that SYS-14 asks for a volume that CANNOT be shrunk after the numbers are
# in.
def sight_m():
    try:
        return float(pop.corridor_sight_m())
    except Exception:                                        # pragma: no cover
        return 60.5


# ===========================================================================
# 4.  THE DERIVED DENOMINATORS
# ===========================================================================
# Every number below is somebody else's, or is derived here from somebody
# else's and logged as an invention. Nothing in this section is a rate that was
# picked because it felt right.

_ONCE = {}


def _memo(key, fn):
    if key not in _ONCE:
        _ONCE[key] = fn()
    return _ONCE[key]


# --- customs: what actually happens to a card, measured through arrival.py --
# NOT a share written down here. `arrival.checks` is the ten-station gate the
# project already built; this pushes N deterministic cards through it and
# counts the outcomes, so if that code changes these rates change with it.
CARD_SAMPLES = 600


def card_outcomes():
    """(refused, referred, contraband, expired_visa, medical_flag) shares."""
    def go():
        ref = rfd = con = exp = med = 0
        for i in range(CARD_SAMPLES):
            pl = PL.random_player(f"customs-probe-{i}")
            rows = ar.checks(pl, 0, "")
            o = ar.outcome_of(rows)
            if o == PL.REFUSED:
                ref += 1
            elif o == PL.REFERRED:
                rfd += 1
            if ar.carrying_contraband(pl.card, 0, ""):
                con += 1
            _cls, expired, _why = ar.entry_class(pl.card)
            if expired:
                exp += 1
            if not pl.card.atmos_code:
                med += 1
        n = float(CARD_SAMPLES)
        return (ref / n, rfd / n, con / n, exp / n, med / n)
    return _memo("cards", go)


def hall_souls_per_hour(ctx, place_key, hour):
    """Souls crossing one customs hall in one hour, from `traffic.hall_rate`.

    `traffic.hall_rate` already divides the station's arrival curve across
    `schedule.CUSTOMS_HALLS`, so this is per hall and the two halls in the
    register are the two halls that number means.
    """
    r = tr.hall_rate(hour % 24.0, ctx.day)
    return float(r["total_per_min"]) * 60.0


# --- the crowd, and how unpoliced it is ------------------------------------
def crowd(place_key, hour):
    """People present, through `populace.occupancy` and the place's own area."""
    key = ("crowd", place_key, round(hour % 24.0, 1))
    if key in _ONCE:
        return _ONCE[key]
    q = q_of(place_key)
    n = pop.occupancy(place_key, ec.floor_m2(place_key), hour % 24.0,
                      rm.archetype(q))
    _ONCE[key] = n
    return n


def unpoliced(place_key, hour):
    """1 / (1 + officers). `security.presence_at`'s own shape, reused.

    `security.hostility` computes exactly this and multiplies it by the
    Downbelow contact rate; taking the factor out is what lets it weight the
    classes that are not Downbelow contact.
    """
    key = ("unpol", place_key, int(hour) % 24)
    if key in _ONCE:
        return _ONCE[key]
    pres = sec.presence_at(place_key, hour % 24.0)
    v = 1.0 if not pres["policed"] else 1.0 / (1.0 + pres["officers"])
    _ONCE[key] = v
    return v


def response_s(place_key, hour):
    """Seconds until a uniform is here. None if nobody is coming.

    NOT `security.response`, which routes the nav graph and costs 36 s a call --
    a gate that takes ten minutes to answer one question is a gate nobody runs.
    An officer already standing in the room responds in zero; otherwise the
    wait is half `security.beat_interval_s`, which is the mean wait for a
    Poisson-phased patrol pass and is the number that module already derives.
    """
    key = ("resp", place_key, int(hour) % 24)
    if key in _ONCE:
        return _ONCE[key]
    pres = sec.presence_at(place_key, hour % 24.0)
    if not pres["policed"]:
        v = None
    elif pres["officers"] >= 1.0:
        v = 0.0
    else:
        q = q_of(place_key)
        pairs = max(1, int(round(sec.roving_pairs(hour % 24.0))))
        v = sec.beat_interval_s(q["sector"], pairs) / 2.0
    _ONCE[key] = v
    return v


# --- the maintenance workforce, which BOUNDS the fault rate ----------------
# INV-350, AND THE FIRST DRAFT OF IT WAS REFUTED BY ITS OWN SANITY CHECK, WHICH
# IS WHY THE CHECK IS HERE.
#
# THE-STATION §2 T4 wants "a machine breaks; a maintenance job is created and
# somebody walks to it" and nothing in canon gives a failure rate. Inventing an
# MTBF alone would be a number that looks sourced and is not, so this is
# derived from BOTH ends and the two ends are made to meet.
#
#   CEILING.  A station cannot generate more corrective work than its own
#             roster closes, or the backlog grows without bound and the station
#             degrades -- which the show's station visibly does not do.
#             `schedule.ROLE_WEIGHTS` carries the roster: 14,430 engineers plus
#             2,500 waste staff.
#   FLOOR.    An MTBF of decades is a station where nothing ever breaks, and
#             T4 asks for maintenance to be a visible part of life.
#
# The first draft used the CEILING as the fault rate, and `_selftest`'s implied
# MTBF came back at **0.04 days** -- a public terminal failing every hour. The
# defect was the denominator: the register declares 357 interactable TYPES and
# `rooms.bays_in` instances them **182,905 times** across the tiled station, so
# the type count was three orders too small. The ceiling was never the incident
# rate; it is the bound the incident rate has to sit inside, and it now does,
# at 5.9% of it. Both halves are printed by `--report`.
MAINT_ROLES = ("engineer", "waste")
CORRECTIVE_SHARE = 0.25       # of a maintenance shift; the rest is planned
                              # work, watch-keeping and standby. Authority 5.
JOB_HOURS = 4.0               # one corrective job, walk included. Authority 5.
SHIFT_H = 8.0                 # schedule.py's watch length

# What a DECLARED INTERACTABLE lasts between corrective visits. One year, and
# the two constraints above bracket it: the roster's ceiling puts the shortest
# survivable MTBF at ~22 days, so a year sits 17x inside the bound, and
# anything past a decade would make T4's maintenance job a thing a player never
# sees. INV-350.
MACHINE_MTBF_DAYS = 365.0


def maint_heads():
    tot = 0
    for w in sched.ROLE_WEIGHTS.values():
        for r in MAINT_ROLES:
            tot += int(w.get(r, 0))
    return tot


def maint_capacity_per_day():
    """THE CEILING: corrective jobs the roster can close in a day.

    Every maintenance head works one `SHIFT_H` watch a day, spends
    `CORRECTIVE_SHARE` of it on corrective work, and a job takes `JOB_HOURS`.
    """
    return maint_heads() * SHIFT_H * CORRECTIVE_SHARE / JOB_HOURS


def machine_instances(place_key):
    """Declared interactables actually built in this place.

    `directory.PLACES[...]["interacts"]` is what `interact.py --audit` gates at
    357/357 -- but that is 357 TYPES over 128 places, and `rooms.tiling`
    instances each place's bay along its footprint, so the thing that can break
    is `types x bays`. `rooms.bays_in` is the register's own bay count and is
    the number `docs/spec/PLACES.md` §TILING freezes, so this follows the
    tiling milestone rather than restating it.
    """
    return _memo(("mi", place_key), lambda: _bays(place_key)
                 * len(q_of(place_key)["interacts"]))


def _bays(place_key):
    q = q_of(place_key)
    try:
        s, p = _schema()
        return int(rm.bays_in(s, p, q))
    except Exception:                                        # pragma: no cover
        return 1


def machine_instances_total():
    return _memo("mit", lambda: sum(machine_instances(p["key"])
                                    for p in dr.PLACES))


def visible_faults_per_day():
    """THE RATE: how often a thing the player can touch stops working."""
    return machine_instances_total() / MACHINE_MTBF_DAYS


def maint_load_share():
    """How much of the roster's corrective capacity the visible faults eat.

    THE SANITY CHECK, and it is the half that makes INV-350 honest. If this
    came back above 1.0 the derivation would be refuted by its own arithmetic:
    the station would be breaking faster than it can be fixed. It comes back at
    about 6%, which says the 182,905 things a player can touch are a small part
    of what 16,930 maintenance staff actually look after -- which is the right
    shape for a station with fusion reactors and a habitat drum.
    """
    return visible_faults_per_day() / maint_capacity_per_day()


def implied_mtbf_days():
    """The shortest MTBF the roster could keep up with. The bound, printed."""
    return machine_instances_total() / max(1e-9, maint_capacity_per_day())


# --- petty theft ------------------------------------------------------------
# LAW-CRIME-DOWNBELOW.md §8.2, authority 4 for the crime and authority 5 for
# the frequency, which the document says outright: "Petty theft | Constant --
# dozens/day". INV-351 reads "dozens" as three dozen and says what would
# overturn it. It is distributed by CROWD x UNPOLICED, which is the same
# document's "concentrated at customs exits, the Zocalo, and within the camps"
# expressed as a weighting rather than as a list of three places.
THEFTS_PER_DAY = 36.0


# --- Nightwatch informers ---------------------------------------------------
# PEOPLE.md FAC-04: "1,500-3,000 civilian informers -- 1-2% of 155,000 humans".
# A denunciation is a filing, and FAC-04's own ACCEPT scene puts the questioning
# at 11:00 in the Zocalo, so filings land in public commercial rooms.
INFORMERS = 2250.0            # the midpoint of FAC-04's own band
FILINGS_PER_INFORMER_YEAR = 1.0   # INV-352


# --- the two bay elevators --------------------------------------------------
# TRAFFIC-AND-CUSTOMS §4.3 D-8/T-04: two elevators for 24 bays, ~5 min full
# cycle, 24 movements/hour capacity, 62% used at peak, and the document calls
# one elevator down "the cheapest high-value event in this whole document".
ELEVATORS = 2
ELEVATOR_PEAK_USE = 0.62
ELEVATOR_MOVES_PER_H = 12.0           # T-04: ~5 min full cycle, one unit
ELEVATOR_CYCLES_PER_H = ELEVATOR_MOVES_PER_H * ELEVATOR_PEAK_USE
# INV-360. Bracketed by the document's own two words for the event: "high
# value" means it must be an EVENT rather than routine, and "the cheapest"
# means it must happen often enough to be worth building. 10,000 cycles is
# about eight weeks of service on one unit and puts an outage across the pair
# at roughly one a month.
ELEVATOR_MTBF_CYCLES = 10000.0


# ===========================================================================
# 4b.  THE DOMESTIC DENOMINATORS -- a household, a clock, a rent and a child
# ===========================================================================
# The first twenty-two classes are the arrival half and the crime half, because
# `LAW-CRIME-DOWNBELOW.md` and `TRAFFIC-AND-CUSTOMS.md` are the two gazetteer
# documents with rate tables in them. Nothing in this section is a crime. Every
# number is somebody else's, and where a constant had to be chosen it carries
# an INV id and two brackets.
#
# THE UNIT OF RESIDENTIAL LIFE IS THE HOUSEHOLD, AND THE REGISTER ALREADY
# COUNTS IT. `docs/spec/PLACES.md` §0.2's staffing rule says it outright --
# *"In residence classes every UNIT carries its door/babcom/locker/bunk set, so
# a class tag there counts once per unit (a 270-unit block holds 270 T3 babcom
# terminals)"*. So `rooms.bays_in` IS the dwelling count of a residence row,
# for the same reason it is the machine count of a plant room, and no second
# number has to be invented.

def units_in(place_key):
    """Dwelling units built in a residence row. `rooms.bays_in`, no more."""
    return _bays(place_key)


def peak_occupancy(place_key):
    """The block's own busiest hour, over its own 24. Its resident population:
    a residence is fullest when everybody who lives there is asleep in it."""
    return _memo(("peak", place_key),
                 lambda: max(crowd(place_key, float(h)) for h in range(24)))


def household_size(place_key):
    """People per unit -- AND IT IS A CROSS-CHECK, NOT AN INPUT.

    `rooms.bays_in` and `populace.occupancy` are two mechanisms that have never
    been pointed at each other: one tiles a bay along a footprint, the other
    integrates a density curve over an area. Divided, they agree on **3.07
    people per unit** across every EA-standard block aboard (qtr_personnel
    3.07, qtr_civilian 3.07, qtr_transient 3.09, alien_resident_qtr 3.14) --
    a household -- and they diverge exactly where the content says they should:
    `downbelow` 9.23 and `downbelow_arch` 14.29, which is a **3x to 4.7x
    overcrowding ratio** nothing in this project had written down. INV-380.

    A block with nobody in it returns 0.0 rather than dividing, and that is the
    sealed Markab quarter: 60 units, zero residents, and every class in this
    section is therefore silent there. `--gate` asserts it.
    """
    u = units_in(place_key)
    return peak_occupancy(place_key) / float(u) if u else 0.0


def households_home(place_key, hour):
    """Units with somebody in them right now.

    The class rates below are per HOUSEHOLD and not per head, because a dispute
    across a bulkhead, a door that will not open and a week's rent are all
    things that happen to a dwelling. `crowd / household_size` is the same
    thing as `units x (occupancy now / occupancy at peak)`, so it is zero in an
    empty block by construction rather than by a special case.
    """
    hh = household_size(place_key)
    if hh <= 0.0:
        return 0.0
    return crowd(place_key, hour) / hh


# --- THE CLOCK, WHICH IS THIS STATION'S OWN SOURCE OF DOMESTIC FRICTION -----
# `npc/schedule.py` carries fifteen species rhythms and they do not agree about
# when night is. Measured through `schedule.awake_fraction` at 03:00: **every
# Narn aboard is asleep (0.000) and every Centauri is awake (1.000)**, with
# Minbari at 0.920 and Brakiri at 0.969; at 13:00 the Brakiri are the ones
# asleep (0.068) while everybody else is up. A Brakiri who works nights lives
# on the other side of a bulkhead from a family whose day starts at seven.
#
# That is a better generator of residential friction than any crime, it is
# already in the repository, and NOTHING READ IT. This is the reading.
def clock_mismatch(place_key, hour):
    """P(two residents of this block, drawn at random, are on opposite clocks).

    `audio.species_mix` gives who lives here and `schedule.awake_fraction`
    gives who is up. The sum is over unordered pairs and doubled, so it is a
    probability over ordered draws and lands in [0,1]. Nothing here is chosen.
    """
    key = ("mism", place_key, int(hour) % 24)
    if key in _ONCE:
        return _ONCE[key]
    mix = aud.species_mix(place_key)
    sps = sorted(mix)
    aw = {s: sched.awake_fraction(s, hour % 24.0) for s in sps}
    t = 0.0
    for i, a in enumerate(sps):
        for b in sps[i + 1:]:
            t += 2.0 * mix[a] * mix[b] * abs(aw[a] - aw[b])
    _ONCE[key] = t
    return t


def mismatch_anchor():
    """The station's own mean clock mismatch over its homes and its hours.

    The DIVISOR, so `DISPUTES_PER_UNIT_YEAR` is the rate at an average block on
    an average night and the geography is the deviation from it -- the same
    shape `NC_ANCHOR_PER_H` uses, and for the same reason: an anchor plus a
    derived shape is one number to defend instead of one hundred and thirty.
    """
    def go():
        ks = home_places()
        n = len(ks) * 24
        return max(1e-9, sum(clock_mismatch(k, float(h))
                             for k in ks for h in range(24)) / max(1, n))
    return _memo("mism_anchor", go)


# --- WHO LIVES WHERE, from the roster rather than from a list here ----------
# `resident.home_for` is the station's own housing allocation and it is a pure
# function of (id, species, role). Pushed through `schedule.ROLE_WEIGHTS` it
# gives the roster's own distribution over the register's residence rows.
# Sampled rather than called once per cell because `home_for` picks a Downbelow
# address PER ID -- one synthetic id would put all 20,390 lurkers in one camp.
HOME_SAMPLE = 48


def home_roster():
    """{place: {role: heads}} -- the roster, housed. Nothing else computes it."""
    def go():
        out = {}
        for sp, w in sched.ROLE_WEIGHTS.items():
            for role, heads in w.items():
                heads = int(heads)
                if heads <= 0:
                    continue
                tally = {}
                for i in range(HOME_SAMPLE):
                    h = res.home_for(f"home-probe-{sp}-{role}-{i}", sp, role)
                    tally[h] = tally.get(h, 0) + 1
                for h, c in tally.items():
                    d = out.setdefault(h, {})
                    d[role] = d.get(role, 0.0) + heads * c / float(HOME_SAMPLE)
        return out
    return _memo("home_roster", go)


def role_share(place_key, roles):
    """What share of this block's roster holds one of these roles."""
    d = home_roster().get(place_key)
    if not d:
        return 0.0
    tot = sum(d.values())
    return (sum(d.get(r, 0.0) for r in roles) / tot) if tot else 0.0


# The three roles `schedule.ROLES` gives `work_hours = 0` -- visitor, refugee,
# lurker. They are also exactly the three `resident._age` will make a minor,
# and two of the three are `resident.NO_STATUS_ROLES`. That is not a
# coincidence: they are the people the station does not employ.
NO_WAGE_ROLES = tuple(r.key for r in sched.ROLES
                      if float(getattr(r, "work_hours", 1.0)) == 0.0)


SENIOR_ROLES = ("command", "envoy", "diplomat")


def rent_row(place_key):
    """Which `economy.LADDER` row this block's tenancy is on.

    Through `consequence.RENT_TIER`, which is already a reading of that table
    by rung -- so this is the register's roster -> the rung that roster holds ->
    the published price, and there is no second price table here.

    THE FIRST DRAFT TOOK THE BLOCK'S LOWEST RUNG AND `_selftest` REFUTED IT:
    rent came out NON-MONOTONE down the ladder, with `qtr_command` at 12.5
    cr/wk against the 30 cr LAW-CRIME §7.1 sources. A tenancy is priced by what
    the room IS, so it is the block's HIGHEST rung, and the senior roles are
    named rather than inferred because the sourced row names them: §7.1's one
    authority-1 price is *"Command / senior quarters -- 30 credits/week"* and
    the billing event behind it (S2E08) is Earth Central billing Sheridan and
    Ivanova, who are `command`. `consequence.RENT_TIER`'s top row is that row.
    """
    def go():
        d = home_roster().get(place_key) or {}
        if not d:
            return "squat"
        if any(r in d for r in SENIOR_ROLES):
            return cq.RENT_TIER[cq.ACCREDITED]
        return cq.RENT_TIER.get(max(_role_rung(r) for r in d), "squat")
    return _memo(("rent", place_key), go)


def _role_rung(role):
    """A role's rung on `consequence`'s ladder, by that module's own rules.

    Not a second visa parser -- `consequence.TIERS` states the rule for each
    rung in words and this is those words applied to a role: an envoy or a
    diplomat is ACCREDITED ('diplomatic immunity'), a lurker or a refugee is at
    or near the floor ('the reason lurkers avoid readers'), a visitor holds
    FACTIONS 2.3's seven-day transit visa, and everybody the station employs
    holds a job aboard, which is CITIZEN/RESIDENT's own criterion.
    """
    if role in ("envoy", "diplomat"):
        return cq.ACCREDITED
    if role == "lurker":
        return cq.NO_STATUS
    if role == "refugee":
        return cq.SANCTUARY
    if role == "visitor":
        return cq.TRANSIT
    return cq.CITIZEN


def rent_week_cr(place_key):
    """What a unit here costs a week, in credits, from `economy.LADDER`."""
    row = rent_row(place_key)
    lo, hi = ec.ladder(row)
    per = (lo + hi) / 2.0
    return per * 7.0 if LADDER_BY_NIGHT.get(row) else per


LADDER_BY_NIGHT = {r[0]: (r[3] == "night") for r in ec.LADDER}


def weekly_subsistence_cr():
    """Rent + food for one household-week at the cheapest tenancy aboard, and
    THE ARITHMETIC IS THE FINDING.

    Priced entirely off `economy.LADDER` and `economy.casual_constraint()`:

        room_transient, a week      6.0 cr  = 0.75 days of casual labour
        bunk_dosshouse, seven nights 7.0 cr = 0.88 days
        meal_cart x3 x7 days        31.5 cr = **3.94 days**

    **Food costs five times what the room costs.** So rent is NOT the pressure
    on a working household -- 4.7 days of casual labour a week clears both, out
    of the seven the muster offers -- and a household falls into arrears when
    its earner STOPS EARNING rather than when the rent goes up. That is why
    INC-ARREARS below is ENDOGENOUS on INC-SICK instead of carrying a rate of
    its own, and it is `economy.py`'s own numbers saying so rather than a
    design decision. The load-bearing number of the underclass is still
    LAW-CRIME §7.1's 300-800 cr passage home: 68.8 days at the same wage.
    """
    lo, hi = ec.ladder("meal_cart")
    food = (lo + hi) / 2.0 * MEALS_PER_DAY * 7.0
    return rent_week_cr("qtr_transient") + food


MEALS_PER_DAY = 3.0          # `schedule.RHYTHMS` carries three meal windows


def casual_week_cr():
    """A week's casual labour at `economy.casual_constraint()`'s own floor."""
    lo, _hi = ec.casual_constraint()
    return lo * MUSTER_DAYS_PER_WEEK


# LAW-CRIME §7.2: casual dock labour is hired at a "**06:00 and 14:00 EMT
# muster**", two a day, every day. `economy.GUILD_SHIFTS_PER_WEEK` = 5 is what
# a GUILD card buys -- five GUARANTEED shifts -- so a casual works at most the
# seven days the muster runs and is not guaranteed any of them. Seven is the
# ceiling and it is the number that makes the margin honest: if a household
# cannot clear subsistence on SEVEN days of work, the table is wrong.
MUSTER_DAYS_PER_WEEK = 7.0


# --- THE CAMP'S OWN SERVICE ECONOMY, which is not crime --------------------
# LAW-CRIME §7.2's work table, verbatim rows: "Cooking, brewing, laundry,
# barbering *for other lurkers* | **8%** | Inside the camps" -- and the
# document's own gloss on it, which is why this class exists at all: *"This is
# the one that makes it a community rather than a pit."* Plus "Begging and
# busking | 8% | The boundary between Downbelow and the commercial rings.
# **Never inside the Zocalo** -- they are moved on | Station-evening".
#
# Both shares are of "the 20,000", which `schedule.ROLE_WEIGHTS` carries as
# 20,390 lurkers. Neither is a crime in that document; both are WORK.
LURKER_SERVICE_SHARE = 0.08          # LAW-CRIME §7.2, stated
LURKER_BUSK_SHARE = 0.08             # LAW-CRIME §7.2, stated


def lurker_heads():
    return _memo("lurkers", lambda: sum(
        int(w.get("lurker", 0)) for w in sched.ROLE_WEIGHTS.values()))


# How many people one camp kitchen, still, laundry or barber's chair serves.
# INV-382, and it is bracketed by the table it comes from: at 1 the 8% share
# would mean every eighth lurker runs a business for nobody, and at 100 the
# 20,390-strong camp holds sixteen kitchens for 39,262 residents, which is a
# queue rather than a community. Twelve is a stall a household walks to.
SERVICE_PITCH_HEADS = 12.0


def service_pitches():
    """Kitchens, stills, laundries and chairs running in the camps."""
    return lurker_heads() * LURKER_SERVICE_SHARE / SERVICE_PITCH_HEADS


# How often one of them is the incident -- a batch that goes wrong, a fire
# watch, a queue, an inspection, a hand-over. INV-382. Bracketed above by the
# camps' own contact rate (`security.DOWNBELOW_CONTACT_PER_HOUR` = 1.5/h where
# nobody patrols): the camp's kitchens must not be a commoner event than being
# robbed in it, or Downbelow reads as a market. Bracketed below by the
# document's own word for the activity -- "continuous" work at 8% of the
# workforce cannot be invisible.
SERVICE_EVENT_PER_PITCH_DAY = 0.10


def busker_heads():
    return lurker_heads() * LURKER_BUSK_SHARE


# --- WHO IS ILL, and the roster that has to attend them --------------------
# THE SAME SHAPE AS INV-350, DELIBERATELY, because that derivation's own lesson
# is that a fix applied to one instance and not to the rule is a fix that will
# be needed again. INV-383. Two ends, both computed from things already here,
# and NOTHING PICKED BETWEEN THEM:
#
#   THE FLOOR.   `rooms.bays_in` x the register's own `diagnostic_bed` rows =
#                **51 beds** across medlab_one, infirmary, isolab, medlab_red,
#                medlab_green and medlab_others. A bed held for BED_DAYS at
#                ADMIT_OCCUPANCY needs 13.6 admissions a day to stay full, and
#                a station whose built beds stand empty is not modelling
#                illness at all.
#   THE CEILING. `schedule.ROLE_WEIGHTS` carries **2,800 `medical`**. At
#                CLINICAL_SHARE of a SHIFT_H watch and CONSULT_HOURS a case
#                that is 11,200 attendances a day. Above it the medlabs are a
#                queue that never clears -- the same refutation INV-350's
#                maintenance ceiling supplies for faults.
#
# The two bounds are **three orders apart** (0.0199 to 16.35 episodes per head
# per year) and canon puts nothing between them. When a quantity is bracketed
# by two DERIVED bounds and nothing sits inside, the GEOMETRIC MEAN is the only
# value equally far from being refuted by either end -- so that is what is
# used, and it is computed rather than transcribed so it moves if either bound
# does. It lands at **0.570 episodes per head per year**, which is one
# clinician contact every 21 months for a roster that is entirely working-age
# by construction (`resident.AGE_SKEW` puts the median at 34).
#
# AND THE GAP BETWEEN THE TWO BOUNDS IS ITSELF A FINDING: 2,800 medical staff
# against 51 built beds is **55 staff per bed**. The register's medlabs are a
# fraction of the medical plant a quarter of a million people need, exactly as
# its 7,637 built dwellings are a fraction of their housing. Neither is this
# module's to fix; both are reported by `--report` so the number is visible.
BED_DAYS = 3.0                       # INV-383: a bed held, admission to walk
ADMIT_OCCUPANCY = 0.80               # INV-383: a ward that is never full has
                                     # beds nobody needed
CLINICAL_SHARE = 0.25                # INV-383: of a medical watch; the rest is
                                     # ward, lab, pharmacy, isolation, research
CONSULT_HOURS = 0.5                  # INV-383: one attendance


def medical_beds():
    return _memo("beds", lambda: sum(
        _bays(p["key"]) for p in dr.PLACES
        if "diagnostic_bed" in p["interacts"]))


def medical_heads():
    return _memo("medheads", lambda: sum(
        int(w.get("medical", 0)) for w in sched.ROLE_WEIGHTS.values()))


def admissions_per_day():
    """THE FLOOR: what the built beds need to not stand empty."""
    return medical_beds() * ADMIT_OCCUPANCY / BED_DAYS


def medical_capacity_per_day():
    """THE CEILING: what the medical roster can attend."""
    return medical_heads() * SHIFT_H * CLINICAL_SHARE / CONSULT_HOURS


def presentations_per_day():
    """THE RATE: how often somebody aboard needs a clinician and is not
    already standing in a medlab. The geometric mean of the two bounds."""
    return _memo("presentations", lambda: math.sqrt(
        admissions_per_day() * medical_capacity_per_day()))


def episodes_per_head_year():
    return presentations_per_day() * 365.0 / float(sched.STATION_HEADCOUNT)


def medical_load_share():
    """The sanity check INV-350's own version made honest: the rate must sit
    INSIDE the roster's capacity. It comes back at 3.5%."""
    return presentations_per_day() / max(1e-9, medical_capacity_per_day())


# --- THE CHILDREN, and there are only three roles that can be one ----------
# `resident._age` is the only place aboard that says a child exists, and it
# says it in one line: *"Children exist on the station and do not hold roles.
# The three roles with no work hours are the only ones that can be a minor"* --
# visitor, refugee and lurker, at **8%**. So the station's child population is
# not a number anybody has to choose; it is `NO_WAGE_ROLES` x `MINOR_SHARE`
# over `schedule.ROLE_WEIGHTS`, and it comes to 6,253 of 250,001.
#
# AND IT MOVES WITH THE ERA, WHICH IS THE POINT. 13,000 of those role-heads are
# `refugee`, and `costume.ERA_EVENTS["narn_surrender"]` (2,20) is the episode
# that creates a Narn refugee population. Before it there is no such population
# aboard, so the child count is smaller and INC-STRAY's rate is lower -- a rate
# that MOVES with the era rather than a switch that flips, which is a stronger
# demonstration that the era reaches this layer than a binary gate is.
MINOR_SHARE = 0.08                   # resident._age's own literal
REFUGEE_ERA = "narn_surrender"


def child_heads(datum=None):
    datum = cos.ERA_DATUM if datum is None else datum
    roles = [r for r in NO_WAGE_ROLES
             if r != "refugee" or era_on(REFUGEE_ERA, datum)]
    return sum(int(w.get(r, 0)) for w in sched.ROLE_WEIGHTS.values()
               for r in roles) * MINOR_SHARE


# How often a child is somewhere a child should not be. INV-384. Bracketed
# above by the camps themselves: at one a week per child the 6,253 children
# aboard would generate 893 a day, more than every other class in this file
# combined, and Downbelow would be a playground. Bracketed below by
# LAW-CRIME §11.2's attested lurker children, who have no school, no roster
# entry and nobody watching them -- at one a year the station never shows one.
# Six a year is once every two months, per child, and it lands at 103/day
# across a register whose hazardous half is where it fires.
STRAYS_PER_CHILD_YEAR = 6.0


# ===========================================================================
# 5.  Where each class can happen -- derived from the register, not listed
# ===========================================================================
def _by_function(*names):
    want = set(names)
    return tuple(p["key"] for p in dr.PLACES
                 if want & set(p["functions"]))


def _by_interact(*names):
    want = set(names)
    return tuple(p["key"] for p in dr.PLACES if want & set(p["interacts"]))


def _keys(*ks):
    return tuple(k for k in ks if q_of(k) is not None)


def _memo_places(name, fn):
    return _memo(("places", name), lambda: tuple(fn()))


def customs_halls():
    return _memo_places("halls", lambda: _by_function("immigration"))


def reader_places():
    return _memo_places("readers",
                        lambda: _by_interact("identicard_reader"))


def crowd_places():
    return _memo_places("crowd", lambda: _by_function(
        "commerce", "public_social", "crowd_hub", "hospitality", "arrival",
        "retail", "recreation"))


def dock_places():
    return _memo_places("dock", lambda: _by_function(
        "cargo_handling", "ship_arrival", "ship_departure"))


def camp_places():
    return _memo_places(
        "camps", lambda: tuple(dict.fromkeys(
            [c["anchor"] for c in sec.camps()]
            + list(_keys("downbelow", "downbelow_arch", "subfloor_stack")))))


def downbelow_places():
    return _memo_places("down", lambda: tuple(dict.fromkeys(
        list(sec.NO_POST) + list(camp_places()))))


def market_places():
    return _memo_places("market", lambda: tuple(
        k for k, _why, _a in sec.BLACK_MARKET_ROUTE
        if q_of(k) is not None))


def eating_places():
    return _memo_places("eat", lambda: _by_function(
        "hospitality", "food_service", "catering"))


def machine_places():
    return _memo_places("mach", lambda: tuple(
        p["key"] for p in dr.PLACES if p["interacts"]))


def power_places():
    return _memo_places("power", lambda: _by_function(
        "power", "power_generation", "power_distribution", "reactor",
        "life_support", "atmosphere"))


def elevator_places():
    """The two bay elevators, which have their own register row.

    NOT `_by_interact("lift_call")`, which was tried and returns five places --
    the drum spokes, the radial tubes and the personnel lifts all call a lift
    and none of them is a BAY elevator. And not `dock_places()` either: the
    first draft ran the class on `docking_bays` as well and doubled the outage
    rate of a pair of machines that exist once. TRAFFIC's "2 for 24 bays" is a
    count of two, and the register carries it as one row."""
    return _memo_places("elev", lambda: _keys("bay_elevators"))


def clearance_places():
    """Where the dual-clearance chain starts: the place holding the console
    that issues a clearance. `directory.PLACES` puts `bay_control_booth` in
    exactly one row, and `docs/spec/PLACES.md`:199 says the same thing in
    words -- "INC-ACCIDENT (the dual-clearance chain lands here first)"."""
    return _memo_places("clear", lambda: _by_interact("bay_control_booth"))


def medical_places():
    return _memo_places("med", lambda: _by_function(
        "medical", "quarantine", "triage"))


# --- the domestic place sets, all three by register FUNCTION ---------------
def home_places():
    """Everywhere on the station somebody sleeps in their own space.

    `residence` and `informal_residence` -- the register's own two words for
    it, so a block added to `directory.PLACES` is a block these classes reach
    without a line being edited here. It is 13 rows today and one of them, the
    sealed Markab quarter, holds **zero** residents; every rate below therefore
    returns exactly 0.0 there, which is the cheapest negative control in this
    file because it is content rather than a stub.
    """
    return _memo_places("homes", lambda: _by_function(
        "residence", "informal_residence"))


def lockable_places():
    """Homes with a LOCK, which is not all of them.

    A LOCKOUT NEEDS A DOOR CONTROLLER AND A CAMP DOES NOT HAVE ONE. The first
    draft ran this class over every `home_places()` row and produced **35.95
    lockouts an hour in Downbelow** -- because `rooms.bays_in` gives that row
    4,256 squats and each one was being handed a card reader. The register
    already says otherwise, in its own vocabulary: `downbelow` and
    `downbelow_arch` declare a **`makeshift_door`**, and `qtr_civilian`
    declares a `door`. You cannot be locked out of a curtain.
    """
    return _memo_places("lockable", lambda: tuple(
        k for k in home_places() if "door" in q_of(k)["interacts"]))


def tenancy_places():
    """Where somebody pays rent. LAW-CRIME §7.1 prices a squat at **0** and
    says why -- *"And it is why people are there"* -- so a camp cannot fall
    into arrears and `informal_residence` is deliberately excluded."""
    return _memo_places("tenancy", lambda: _by_function("residence"))


def camp_homes():
    """The camps as DWELLINGS rather than as a crime scene. `camp_places()`
    above is `security.camps` plus the Downbelow rows and exists to be swept;
    this is the register's own `informal_residence`, and the difference is the
    whole point of INC-STILL: the same volume, read as a community."""
    return _memo_places("camp_homes",
                        lambda: _by_function("informal_residence"))


def counter_places():
    """`economy.vendors()` -- the thirteen counters that hold stock."""
    return _memo_places("counters", lambda: tuple(
        k for k in ec.vendors() if q_of(k) is not None))


def moveon_places():
    """The licensed commercial floor -- where a busker is moved OFF.

    LAW-CRIME §7.2 is precise and the precision is the content: begging and
    busking happen at *"the boundary between Downbelow and the commercial
    rings. **Never inside the Zocalo** -- they are moved on"*. So the class
    fires where the moving-on happens, which is the licensed floor, and it is
    silent in Downbelow -- where there are no officers and nobody to move
    anybody. `_r_moveon` gets that for free from `security.presence_at`
    rather than from a place list.
    """
    return _memo_places("moveon", lambda: _by_function(
        "commerce", "retail", "public_social", "crowd_hub", "hospitality",
        "food_service", "arrival", "recreation"))


# WHERE A CHILD SHOULD NOT BE, and it is a list of register FUNCTIONS rather
# than of places -- the same rule that lets `power_places` follow the register.
# Every one of these is somewhere the station itself treats as controlled: a
# pressure boundary, a power train, a moving cargo floor, a variable-gravity
# volume, a detention block, or a room whose function word is `crime`.
ADULT_FUNCTIONS = (
    "cargo_handling", "power_generation", "power_distribution", "reactor",
    "radiation_boundary", "hazardous_storage", "fuel_storage",
    "fuel_transfer", "waste_processing", "microgravity_handling",
    "variable_gravity", "atmosphere_containment", "atmosphere_feedstock",
    "coolant_loop", "coolant_transfer", "eva_egress", "detention",
    "crime", "organised_crime", "black_market", "sealed_volume",
    "ship_arrival", "ship_departure", "starfury_launch", "fabrication",
    "industry", "repair", "mortuary",
)


def stray_places():
    """AND A CAMP IS NOT ONE OF THEM, WHICH THE FIRST DRAFT GOT WRONG.

    `downbelow` declares `crime` and `black_market`, so it matched
    `ADULT_FUNCTIONS` and took **2.221 strays an hour** -- half the station's
    total -- on the strength of holding 39,262 people. But a lurker child in
    Downbelow is AT HOME. That it is a bad home is LAW-CRIME §11.2's point and
    not this class's: "somewhere a child should not be" has to mean somewhere
    that is not where they live, or the commonest place to find a stray child
    is their own bed. `informal_residence` is subtracted for that reason.
    """
    return _memo_places("stray", lambda: tuple(
        k for k in _by_function(*ADULT_FUNCTIONS)
        if "informal_residence" not in q_of(k)["functions"]))


def sick_places():
    """Everywhere a person can be, LESS the places a clinician already is.

    A presentation inside a medlab is a CONSULTATION, and a consultation is not
    an incident because there is no stance to take toward it -- you cannot help
    or report somebody's appointment. What makes this one an incident is that
    there is nobody there yet.
    """
    return _memo_places("sick", lambda: tuple(
        p["key"] for p in dr.PLACES if p["key"] not in set(medical_places())))


# ===========================================================================
# 6.  THE CLASS TABLE -- 22 rows, and the gate reads the spec to check it
# ===========================================================================
class Klass:
    __slots__ = ("cid", "title", "era", "places", "rate", "cast", "beats",
                 "resolve", "window_s", "endogenous", "_pset")

    def __init__(self, cid, title, places, rate, cast, beats, resolve,
                 era=None, window_s=60.0, endogenous=False):
        self.cid = cid
        self.title = title
        self.era = era
        self.places = places
        self.rate = rate
        self.cast = cast
        self.beats = tuple(beats)
        self.resolve = resolve
        self.window_s = float(window_s)
        self.endogenous = endogenous
        self._pset = None

    def here(self, place):
        """`place in self.places()` was 22 LINEAR SCANS OVER UP TO 125 KEYS on
        every place on every step -- 21 million tuple comparisons per
        station-hour. The place list is a pure function of the register, so it
        is resolved once into a set."""
        if self._pset is None:
            self._pset = frozenset(self.places())
        return place in self._pset


def _cast_at(place, hour, seed, n=1, species=None, role_hint=""):
    """Named residents at this place at this hour. Not 'a thief' -- a person.

    A PER-INCIDENT SEED MUST NOT REACH `resident.affiliates`, AND THE FIRST
    VERSION LET IT. `affiliates` is `lru_cache`d on (place, species, seed) and
    scans up to `POOL_BUDGET` = 4,000 candidate ids building 28 whole
    `Resident` objects to find the ones whose lives touch the place. Passing a
    fresh `f"{seed}-{day}-{step}"` in made every cast a cold 0.47 s pool build:
    profiled, ONE station-hour spent **31 of its 31.3 seconds** inside
    `resident.resident`, and the incident draw itself was free.

    So the POOL is drawn on a stable seed and cached per (place, species,
    hour), and the incident's own seed only picks WHICH member of it. The cast
    still varies per incident -- it is the same station with the same regulars,
    which is what `affiliates` is for.
    """
    mix = aud.species_mix(place)
    if species is None:
        r = u("cast-sp", place, hour, seed, role_hint)
        acc = 0.0
        species = "human"
        for sp, share in sorted(mix.items()):
            acc += share
            if r <= acc:
                species = sp
                break
    pool = _pool(place, hour, species)
    if not pool:                                             # pragma: no cover
        return [res.resident(f"{place}-{role_hint}-{i}-{seed}", species)
                for i in range(n)]
    out, used = [], set()
    for i in range(n):
        j = int(u("cast-i", place, seed, role_hint, i) * len(pool)) % len(pool)
        while j in used and len(used) < len(pool):
            j = (j + 1) % len(pool)
        used.add(j)
        out.append(pool[j])
    return out


CAST_POOL = 16                # people of one species this module ever casts


def _pool(place, hour, species):
    key = ("pool", place, int(hour) % 24, species)
    if key not in _ONCE:
        try:
            _ONCE[key] = tuple(res.roster(place, hour % 24.0, species,
                                          CAST_POOL, seed=POOL_SEED))
        except Exception:                                    # pragma: no cover
            _ONCE[key] = ()
    return _ONCE[key]


POOL_SEED = "b5"              # `resident.affiliates`' own default


def _who(person):
    return person.name or f"{person.species.upper()} {person.npc_id[-6:]}"


# --- the rate functions. one per class, each citing what it reads -----------
def _r_liner(ctx, place, hour):
    """SYS-02's liner row: 0.5/day, ~2/week, 400-800 pax through one hall."""
    if not tr.liner_today(ctx.day):
        return 0.0
    for a in ctx.arrivals():
        if a["type"] == "liner" and abs((a["hour"] % 24.0) - hour) < 0.5:
            return 1.0
    return 0.0


def _r_elev(ctx, place, hour):
    """One unit down. A LIFT FAILS ON CYCLES, NOT ON CALENDAR TIME.

    The first draft made this INC-FAULT weighted by the place's whole
    interactable population and produced **18.6 outages a day** on a pair of
    elevators. The right denominator is TRAFFIC §4.3's own: 12 movements an
    hour per unit at ~90 s each way, 62% used at peak, two units. INV-360.
    """
    return ELEVATORS * ELEVATOR_CYCLES_PER_H / ELEVATOR_MTBF_CYCLES


def _r_contra(ctx, place, hour):
    _ref, _rfd, con, _exp, _med = card_outcomes()
    return hall_souls_per_hour(ctx, place, hour) * con


def _r_refused(ctx, place, hour):
    ref, _rfd, _con, _exp, _med = card_outcomes()
    return hall_souls_per_hour(ctx, place, hour) * ref


def _r_sweep(ctx, place, hour):
    """ENDOGENOUS. LAW-CRIME §5.5: a sweep happens "occasionally, and always
    for a reason". The reason is the camp's own heat, which INC-CONTACT and
    INC-PICK write. Below the threshold the rate is zero and stays zero."""
    heat = _WORLD_HEAT.get(place, 0.0)
    if heat < SWEEP_HEAT:
        return 0.0
    return min(1.0, (heat - SWEEP_HEAT) / SWEEP_HEAT) * 0.5


def _r_brawl(ctx, place, hour):
    """PEOPLE.md FAC-13: the Drazi factional cycle is OFF at the datum and the
    switch exists. This returns zero at the datum BY DESIGN and the gate
    asserts it flips when the switch is thrown -- a class that fires anyway
    would mean the era model does not reach the incident layer."""
    if not DRAZI_CYCLE_ON:
        return 0.0
    mix = aud.species_mix(place)
    # THE SAME SHAPE AS INC-NC, ON THE SAME ANCHOR. A Drazi brawl and a
    # Narn/Centauri stand-off are the same event -- two members of factions
    # that will not yield meeting in a public room -- so this shares INC-NC's
    # scale rather than inventing a second one. The pair weight is the crowd
    # times the chance both are Drazi times the chance they are on opposite
    # sides of the split, which FACTIONS §15 leaves unstated and is therefore
    # even.
    w = crowd(place, hour) * mix.get("drazi", 0.0) ** 2 * DRAZI_SPLIT
    return NC_ANCHOR_PER_H * w / _nc_anchor_weight(hour)


# FACTIONS §15 leaves the colours and the cycle deliberately unstated, so an
# even split is the only reading that adds nothing. INV-364.
DRAZI_SPLIT = 0.5


def _r_denounce(ctx, place, hour):
    """FAC-04's box filings, era-gated on `nightwatch_visible` (2,22)."""
    filings = INFORMERS * FILINGS_PER_INFORMER_YEAR / 365.0 / 24.0
    tot = sum(crowd(k, hour) for k in crowd_places()) or 1.0
    return filings * crowd(place, hour) / tot


def _r_dust(ctx, place, hour):
    """FAC-25's supply event, priced off the theft rate in the same rooms.

    LAW-CRIME §8.2's table files petty theft as "Constant -- dozens/day" and
    Dust as "Rare, and an event when it happens", two rows apart in the same
    column, so this is the common crime in the same places at one fiftieth of
    it. INV-362.
    """
    return _r_pick(ctx, place, hour) * DUST_SHARE


DUST_SHARE = 0.02                    # INV-362


def _r_pick(ctx, place, hour):
    """Dozens/day, distributed by crowd x unpoliced. INV-351.

    TWO THINGS WERE WRONG WITH THE FIRST DRAFT AND BOTH ARE WORTH RECORDING.

    (1) THE NORMALISER MUST BE THE CLASS'S OWN PLACE SET. It distributed 36
    thefts a day over all 128 register rows and then fired only in the 21 the
    class could reach, so the station-wide total came out at **3.3/day instead
    of 36** -- an 11x loss with nothing in the log to say so. A rate normalised
    over a wider set than it fires in quietly loses most of itself.

    (2) POLICING IS NOT THE DRIVER; DENSITY IS. It weighted by
    `crowd x unpoliced`, which put 0.15% of the station's theft in the Zocalo
    because the Zocalo has 12.9 officers in it. LAW-CRIME §8.2's own sentence
    is "Everywhere; concentrated at customs exits, the **Zocalo**, and *within*
    the camps" -- and two of those three are the most heavily policed places
    aboard. A pickpocket needs a crowd and a shoulder to brush, so the weight
    is `people x people per square metre`, and whether the thief is CAUGHT is
    where the policing belongs -- which is exactly where `_res_pick` already
    puts it, through `_responded`. Weighting by it here counted it twice.
    """
    w = _theft_weight(place, hour)
    tot = _theft_weight_total(hour)
    return THEFTS_PER_DAY / 24.0 * (w / tot if tot else 0.0)


def _theft_weight(place, hour):
    n = crowd(place, hour)
    return n * n / max(1.0, ec.floor_m2(place))


def theft_places():
    """LAW-CRIME §8.2, verbatim: theft is "Everywhere; concentrated at customs
    exits, the Zocalo, and *within* the camps". Three of those are register
    functions and the fourth is the camp list `security.camps` derives."""
    return _memo_places("theft", lambda: tuple(dict.fromkeys(
        list(crowd_places()) + list(customs_halls())
        + list(downbelow_places()))))


def _theft_weight_total(hour):
    key = ("tw", int(hour) % 24)
    if key not in _ONCE:
        _ONCE[key] = sum(_theft_weight(k, hour) for k in theft_places())
    return _ONCE[key]


def _r_fraud(ctx, place, hour):
    """SYS-03/05 reader events x the expired-visa share, measured through
    `arrival.entry_class` rather than read off `resident.VISA_EXPIRED_P`, so
    the rate follows the code path a card actually takes."""
    _ref, _rfd, _con, exp, _med = card_outcomes()
    if place in customs_halls():
        return hall_souls_per_hour(ctx, place, hour) * exp
    # A reader elsewhere sees the resident traffic through its own door.
    return crowd(place, hour) * READER_TOUCHES_PER_HEAD_H * exp


READER_TOUCHES_PER_HEAD_H = 0.05     # INV-353


def _r_accident(ctx, place, hour):
    """TRAFFIC §9's chain, and it needs THREE THINGS AT ONCE.

    The S1 accident (authority 4) is: substandard microchips -> a mistaken
    clearance -> two hulls in one volume -> a dock worker killed. So the chain
    needs (a) a fault on the clearance console -- one declared machine at the
    station MTBF, (b) a second hull actually in the conflicting volume, which
    is `traffic.berths_in_use` over the schema's bay count, and (c) a gang
    standing in the gap, which is `schedule`'s 06:00-15:00 dock shift.

    That product is the FATAL case, and it lands at roughly one every 500 days,
    which is the right order for an event the show treats as memorable. The
    class fires at the recordable rate -- the same chain at lower severity --
    and `_res_accident` decides which branch. INV-361.
    """
    load = _berth_load(ctx, hour)
    on_shift = 1.0 if 6.0 <= (hour % 24.0) < 15.0 else 0.15
    fatal_per_day = load * on_shift / MACHINE_MTBF_DAYS
    return fatal_per_day * ACCIDENT_RECORDABLE_PER_FATAL / 24.0


# INV-361. A bay accident that hurts somebody is far commoner than one that
# kills them; 100:1 is the industrial ratio this uses to turn TRAFFIC §9's one
# memorable fatality into a stream of recordable incidents a player can be
# present for. Overturned by any figure for B5 dock injuries.
ACCIDENT_RECORDABLE_PER_FATAL = 100.0


def _r_brownout(ctx, place, hour):
    """A SHED IS A FAULT THAT DEFEATED THE REDUNDANCY, not a fault.

    The first draft made this INC-FAULT restricted to the eight power places
    and produced **5.7 sheds an hour** -- a district going dark every ten
    minutes on a station where SYS-07 files a brownout as "plot-grade". The
    missing term is SYS-14's own escalation column, which says "APU pickup
    (PLC-122)": every district feed has a standby behind it, so a shed needs
    the fault to land while the standby is ITSELF out for repair. That
    probability is the standby's unavailability -- `JOB_HOURS` of repair in a
    `MACHINE_MTBF_DAYS` cycle -- and it is derived from numbers already here
    rather than chosen. It comes to one district brownout every ~16 days.
    """
    share = machine_instances(place) / machine_instances_total()
    unavail = JOB_HOURS / (MACHINE_MTBF_DAYS * 24.0)
    return visible_faults_per_day() / 24.0 * share * unavail


def _r_quar(ctx, place, hour):
    _ref, _rfd, _con, _exp, med = card_outcomes()
    return hall_souls_per_hour(ctx, place, hour) * med * QUAR_SHARE


QUAR_SHARE = 0.01                    # INV-354


def _r_psicop(ctx, place, hour):
    """SYS-14: "SYS-01 era draw (every few weeks)". Three weeks is the middle
    of "a few", and the visit is a station-wide event anchored to the places a
    Psi Corps call is transacted in. INV-363."""
    return 1.0 / (PSICOP_DAYS * 24.0)


PSICOP_DAYS = 21.0                   # INV-363


def _r_nc(ctx, place, hour):
    """The 5% of FACTIONS.md §12's 95/5 rule, DERIVED from the place's own
    species mix rather than taken as a constant.

    Two people meet at a rate proportional to the crowd and to the product of
    their shares; `friction.separation_m("narn","centauri")` is 1.80 m against
    a MEASURED 1.0806 m corridor half-width, so when they do meet the pair
    cannot pass. `CONTACT_SHARE` is `security.CONTACT_SHARE` -- 5% -- so 95 of
    100 such meetings are the avoidance `encounter.py` already measures in
    metres and this class is only the other five.
    """
    w = _nc_weight(place, hour)
    if w <= 0.0:
        return 0.0
    return NC_ANCHOR_PER_H * w / _nc_anchor_weight(hour)


def _nc_weight(place, hour):
    mix = aud.species_mix(place)
    return (crowd(place, hour) * mix.get("narn", 0.0)
            * mix.get("centauri", 0.0))


def _nc_anchor_weight(hour):
    """The Zocalo at the same hour -- the place the anchor rate describes."""
    key = ("ncw", int(hour) % 24)
    if key not in _ONCE:
        _ONCE[key] = max(1e-9, _nc_weight(NC_ANCHOR_PLACE, hour))
    return _ONCE[key]


# PLACES §0.2's own figure for this class, verbatim: "the 5% of the 95/5 rule;
# 0.02/h -- rare, severe", citing friction.py:72-92. It is an ANCHOR, not a
# constant applied everywhere: the shape across the station is the geography
# (each place's own crowd x Narn share x Centauri share, through
# `audio.species_mix`) and this fixes the scale at the one place the spec's
# number describes. INV-355.
NC_ANCHOR_PER_H = 0.02
NC_ANCHOR_PLACE = "zocalo"


def _r_gqe(ctx, place, hour):
    """The G'Quan Eth collision: a Narn arrival carrying a plant that is a
    controlled substance under EA law. Narn share of the hall x the contraband
    detection rate, because it IS a contraband find -- with a liturgy."""
    _ref, _rfd, con, _exp, _med = card_outcomes()
    mix = aud.species_mix(place)
    return hall_souls_per_hour(ctx, place, hour) * mix.get("narn", 0.0) * con


def _r_strike(ctx, place, hour):
    """ENDOGENOUS, and it is the day-boundary class. FAC-06's ballot fires when
    the grievance board crosses its threshold, and the board is written by
    INC-ACCIDENT and INC-ELEV -- so a strike on day 2 is caused by an accident
    on day 1 and by nothing else."""
    if _WORLD_GRIEVANCE[0] < STRIKE_THRESHOLD:
        return 0.0
    return 0.25


def _r_fault(ctx, place, hour):
    share = machine_instances(place) / machine_instances_total()
    return visible_faults_per_day() / 24.0 * share


def _r_hold(ctx, place, hour):
    """A HOLD IS AN ARRIVING HULL THAT FINDS NO BERTH, so it is counted in
    arrivals and not in a bare multiplier.

    The first version was `max(0, load - HOLD_LOAD) * 6.0` -- and the 6.0 was
    a number nobody could defend, applied at all eight dock places, which made
    a stack form 79 times a day. `traffic.rate_per_hour` already says how many
    hulls arrive this hour and `traffic.berths_in_use` already says how full
    the map is, so the rate is the first times the chance the second leaves
    nowhere to put them -- and it happens ONCE, at the berth map, not once per
    bay.
    """
    load = _berth_load(ctx, hour)
    blocked = max(0.0, load - HOLD_LOAD) / max(1e-9, 1.0 - HOLD_LOAD)
    down = ELEVATOR_DOWN_BLOCK if _WORLD_ELEV_DOWN[0] else 0.0
    return tr.rate_per_hour(hour % 24.0) * min(1.0, blocked + down)


# With one of two elevators out, TRAFFIC §4.3's own arithmetic halves the
# port's throughput -- "24 movements/hour capacity, 62% used at peak" becomes
# 12 against a demand of 15, so every arrival queues. Half of them, since the
# demand is 62% of the pair's capacity and 100% of one unit's.
ELEVATOR_DOWN_BLOCK = 0.5


HOLD_LOAD = 0.70                     # INV-356


def _berth_load(ctx, hour):
    """`traffic.berths_in_use` over the schema's own bay count, memoised by
    the hour bucket -- it is a whole-day arrival integral and INC-HOLD is
    endogenous, so it would otherwise be rebuilt on every one-minute step."""
    key = ("berth", ctx.day, int(hour) % 24)
    if key not in _ONCE:
        b = tr.berths_in_use(hour % 24.0, ctx.day)
        _ONCE[key] = b["bay"] / max(1.0, float(tr.bay_count(_schema()[0])))
    return _ONCE[key]


def _r_contact(ctx, place, hour):
    """`security.hostility` verbatim: DOWNBELOW_CONTACT_PER_HOUR / (1+officers)
    -- 1.5/h where nobody patrols, and it already carries the 95/5 split."""
    return sec.hostility(place, hour % 24.0)["contact_per_hour"]


def _r_debt(ctx, place, hour):
    """ENDOGENOUS. FAC-25's ledger ages past terms.

    THE STEP-SIZE CONTROL FOUND THIS ONE, WHICH IS WHAT A STEP CONTROL IS FOR.
    The first draft returned `pool * 0.25` PER CAMP -- 44 calls an hour in each
    of six places -- and the 4x-step run came back **13.3% low** because a rate
    that high cannot be resolved by a one-minute Bernoulli draw at all: at
    lambda = 44/h a four-minute step is 95% certain to fire once and can never
    fire twice, so a quarter of the events simply vanished. The discrepancy was
    not a step problem; it was a rate that was wrong by an order of magnitude,
    and the step control is the only thing here that could see it.

    Fixed at both ends: the pool is the STATION's debtors, so one camp gets its
    share rather than all of it, and the fraction called on in a day is one
    week's terms rather than a quarter of the book.
    """
    pool = _WORLD_DEBTORS[0]
    if pool <= 0:
        return 0.0
    if abs((hour % 24.0) - DEBT_ROUND_H) >= 1.0:
        return 0.0
    return pool * DEBT_TERM_RATE / max(1, len(camp_places()))


DEBT_ROUND_H = 10.0                  # FAC-25: "the Collector's rounds at 10:00"
DEBT_TERM_RATE = 1.0 / 7.0           # INV-357: a week's terms


def _r_pakma(ctx, place, hour):
    """A wrong-seat diner, and every term of it is somebody else's number.

    SYS-14's trigger column is "species meal windows 04:00/16:00 + a wrong-seat
    diner", so the rate is: how many people are eating here now, times the
    share of them who are transients and would not know the convention, times
    the share of the tables that are the pak'ma'ra section. The first two come
    from `populace.occupancy` and `schedule.ROLE_WEIGHTS`; the third is
    `audio.species_mix`, sampled through the same `populace.species_for` that
    decides which body is actually placed at the table.
    """
    if not any(abs((hour % 24.0) - m) < 1.0 for m in PAKMA_MEALS):
        return 0.0
    pk = aud.species_mix(place).get("pakmara", 0.0)
    if pk <= 0.0:
        return 0.0
    return crowd(place, hour) * SEAT_TURNOVER_PER_H * transient_share() * pk


def transient_share():
    """Who aboard has not learned a local convention: `schedule.ROLE_WEIGHTS`'
    own visitor head-count over the whole roster. 44,770 of 250,001 = 17.9%."""
    def go():
        tot = vis = 0
        for w in sched.ROLE_WEIGHTS.values():
            for r, k in w.items():
                tot += int(k)
                if r == "visitor":
                    vis += int(k)
        return vis / float(max(1, tot))
    return _memo("transient", go)


SEAT_TURNOVER_PER_H = 1.0            # INV-359: a diner holds a seat an hour


PAKMA_MEALS = (4.0, 16.0)            # PLACES §0.2 / SYS-14's own hours


# ---------------------------------------------------------------------------
# THE EIGHT DOMESTIC AND COMMERCIAL RATES
# ---------------------------------------------------------------------------
# NOT ONE OF THEM IS A CRIME, and that is checked rather than claimed:
# `--gate` counts how many classes book somebody into the brig in the ABSENT
# branch -- what the station does when nobody is watching -- and the eight
# below write **zero** custody rows there against the original table's seven.
# A residential ring furnished with six more offences would be a crime
# simulator with flats in it, which is the thing this half exists not to be.

def _r_neighbour(ctx, place, hour):
    """A dispute across a bulkhead, and THE STATION'S OWN CLOCKS CAUSE IT.

    Per HOUSEHOLD, not per head -- `households_home` is `rooms.bays_in` scaled
    by how much of the block is in tonight -- times the block's own
    `clock_mismatch` against the station's mean. Everything in it belongs to
    another module: the units to `rooms.tiling`, the presence to
    `populace.occupancy`, the species to `audio.species_mix` and the sleep to
    `schedule.RHYTHMS`.

    The geography falls out and none of it was placed by hand: the mismatch
    peaks at 22:00-03:00 in every EA block (qtr_civilian 0.274 at 03:00 against
    0.066 at 19:00) because that is when the human and Narn halves are asleep
    and the Centauri and Minbari halves are not, and it peaks at **22:00 in the
    Alien Sector** (0.298), which is a corridor where four species keep four
    different nights.
    """
    hh = households_home(place, hour)
    if hh <= 0.0:
        return 0.0
    return (hh * DISPUTES_PER_UNIT_YEAR / (365.0 * 24.0)
            * clock_mismatch(place, hour) / mismatch_anchor())


# INV-381. One dispute per household every two months. Bracketed both ways and
# the brackets are this project's own numbers rather than intuition:
#   ABOVE  LAW-CRIME §8.2's commonest CRIME is petty theft at "dozens/day", and
#          INV-351 reads that as 36. At 12/unit/year the station runs 251
#          disputes a day -- seven times its whole crime rate and more than
#          every other class in this file combined -- and a residential
#          corridor becomes a soap opera.
#   BELOW  at 1/unit/year a player who lives aboard for a season never hears
#          one, and the residential rings stay at the zero this class exists
#          to fix.
# Six lands at 126/day station-wide, 3.5x the petty-theft rate, which is the
# right ORDER as well as the right sign: the commonest thing in a block of
# flats is not a crime, and it should be commoner than the commonest crime.
# Overturned by any depiction of a B5 residential complaint procedure.
DISPUTES_PER_UNIT_YEAR = 6.0


def _r_lockout(ctx, place, hour):
    """A door that will not admit its own tenant, and it has TWO CAUSES.

    (a) THE DOOR. Every unit carries a `door` in `directory.PLACES`'
        `interacts` -- `docs/spec/PLACES.md` §0.2's "every UNIT carries its
        door/babcom/locker/bunk set" -- so the mechanical term is one declared
        machine per unit at `MACHINE_MTBF_DAYS`, the same MTBF INC-FAULT uses,
        weighted by whether anybody is at it.
    (b) THE CARD. `consequence.py`'s six-rung ladder is the interesting half.
        A block housing refugees and visitors holds cards that EXPIRE --
        `arrival.entry_class`'s own expired share, measured through
        `card_outcomes()` rather than read off `resident.VISA_EXPIRED_P` -- and
        a card that no longer carries the rung the door wants is a lockout with
        no machine fault in it at all. `role_share` over `NO_WAGE_ROLES` is how
        much of the block that is, and it is 100% at qtr_transient and 0% at
        qtr_command. **The same event, two floors apart, is a call to
        maintenance or a call to immigration.**

        AND IT IS ONCE PER VISA, NOT ONCE PER TOUCH. The first draft priced
        this per door-reader touch, which said a resident's card is expired on
        1.7% of the times they come home -- several times a week, for ever. A
        card expires ONCE and is then dealt with, so the divisor is
        `resident.VISA_TRANSIT_DAYS`, FACTIONS 2.3's seven-day mean stay, which
        is the cycle a transient card actually turns over on. That drops the
        term by two orders and it is right that it does: this class is a door
        fault with a rung attached, not a card epidemic.
    """
    hh = households_home(place, hour)
    if hh <= 0.0:
        return 0.0
    door = hh / MACHINE_MTBF_DAYS / 24.0
    _ref, _rfd, _con, exp, _med = card_outcomes()
    card = (hh * role_share(place, NO_WAGE_ROLES) * exp
            / res.VISA_TRANSIT_DAYS / 24.0)
    return door + card


def _r_arrears(ctx, place, hour):
    """ENDOGENOUS, and `economy.LADDER`'s own arithmetic is what makes it so.

    THE FIRST DRAFT GAVE THIS CLASS A RATE OF ITS OWN AND THE PRICE TABLE
    REFUTED IT. Priced off `economy.ladder` and `economy.casual_constraint`,
    a week's cheapest tenancy is **0.75 days of casual labour** and a week's
    food is **3.94 days** -- so rent is a twentieth of a household's outgoings
    and a household that works at all is never in arrears. Nothing about the
    rent can produce this incident; only something that STOPS THE EARNING can.

    So the rate reads the sick pool INC-SICK writes, exactly as INC-DEBT reads
    the debtor pool and INC-SWEEP reads camp heat. A household falls behind one
    rent cycle after its earner stops, which is why the class fires at the
    week's end rather than continuously -- `RENT_DAY_H` is the hour, and the
    day is the station week's own boundary through `ctx.day`.
    """
    pool = _WORLD_SICKHOMES.get(place, 0.0)
    if pool <= 0.0:
        return 0.0
    if abs((hour % 24.0) - RENT_DAY_H) >= 1.0:
        return 0.0
    return pool * RENT_MISS_SHARE


# A household whose earner is off its feet clears subsistence on 4.7 of the
# muster's 7 days (`weekly_subsistence_cr` / `casual_constraint`'s floor), so
# it survives a short absence and not a long one. INV-381: the share of stopped
# households that actually miss the week is the share whose absence outlasts
# the margin -- 1 - 4.7/7. Bracketed by the arithmetic at both ends: at 1.0
# every illness costs a tenancy, which the margin says is false; at 0 the
# ladder's rent rows are decoration.
RENT_MISS_SHARE = 1.0 - 4.7 / 7.0
RENT_DAY_H = 9.0                     # rent is collected before the day shift


def _r_still(ctx, place, hour):
    """The camp's own kitchen, still, laundry and barber's chair.

    LAW-CRIME §7.2 gives the share -- **8%** of the lurker workforce cook,
    brew, launder and cut hair *for other lurkers* -- and gives the reason this
    is content rather than crime in the same row: *"This is the one that makes
    it a community rather than a pit."* The rate is that workforce divided into
    pitches and each pitch having something happen at it, distributed over the
    camps by their own share of the camp population, so `subfloor_stack`'s 1,930
    residents get a twentieth of what `downbelow`'s 39,262 do.
    """
    tot = _camp_heads_total(hour)
    if tot <= 0.0:
        return 0.0
    share = crowd(place, hour) / tot
    return (service_pitches() * SERVICE_EVENT_PER_PITCH_DAY / 24.0) * share


def _camp_heads_total(hour):
    key = ("camph", int(hour) % 24)
    if key not in _ONCE:
        _ONCE[key] = sum(crowd(k, hour) for k in camp_homes())
    return _ONCE[key]


def _r_sick(ctx, place, hour):
    """Somebody needs a clinician and is not standing in a medlab.

    The station-wide presentation rate, distributed by where the people
    actually are -- `populace.occupancy` summed over the register, which at
    13:00 comes to **249,801 against a roster of 250,001**, so the distribution
    is over the whole population and not over a sample of it.

    The medical places are excluded on purpose: a presentation inside a medlab
    is a consultation, and a consultation is not an incident because there is
    no stance to take toward it. What makes this one an incident is that there
    is nobody there yet -- which is also why the resolution reads
    `consequence.admits`: the same collapse in `qtr_personnel` and in
    `downbelow` is a gurney or a shrug, and the difference is the rung on the
    card.
    """
    tot = _station_crowd(hour)
    if tot <= 0.0:
        return 0.0
    return presentations_per_day() / 24.0 * crowd(place, hour) / tot


def _station_crowd(hour):
    key = ("scrowd", int(hour) % 24)
    if key not in _ONCE:
        _ONCE[key] = sum(crowd(p["key"], hour) for p in dr.PLACES)
    return _ONCE[key]


def _r_stray(ctx, place, hour):
    """A child somewhere a child should not be, AND THE ERA MOVES IT.

    `resident._age` is the only statement anywhere in this project that a child
    exists aboard, and it is one line: the three roles with no work hours --
    visitor, refugee, lurker -- are the only ones that can be a minor, at 8%.
    That is 6,253 children over `schedule.ROLE_WEIGHTS`, and 1,040 of them are
    refugee children who **do not exist before `narn_surrender` (2,20)**.

    So this rate MOVES with the era rather than switching, and that is a
    stronger demonstration that SYS-01 reaches the incident layer than a binary
    gate is: at S2E01 the class runs at 87.4/day and at the datum 103.1/day,
    a 17.9% step created by one episode, on a class nothing era-gates.

    Where it fires is `ADULT_FUNCTIONS`: a pressure boundary, a power train, a
    moving cargo floor, a detention block, a room whose function word is
    `crime`. The child comes from a household, so the weight is the place's own
    crowd share of the hazardous half -- a child is found where there are
    people to find them.
    """
    tot = _stray_weight_total(hour)
    if tot <= 0.0:
        return 0.0
    n = child_heads(ctx.datum) * STRAYS_PER_CHILD_YEAR / (365.0 * 24.0)
    return n * crowd(place, hour) / tot


def _stray_weight_total(hour):
    key = ("strayw", int(hour) % 24)
    if key not in _ONCE:
        _ONCE[key] = sum(crowd(k, hour) for k in stray_places())
    return _ONCE[key]


def _r_moveon(ctx, place, hour):
    """A busker or a beggar moved off the licensed floor.

    THE ONE CLASS HERE WHERE POLICING IS THE DRIVER, and it is the exact
    inverse of INC-PICK's recorded lesson. A theft needs a crowd and a shoulder
    to brush and happens *despite* the officers, so weighting it by policing
    counted it twice. A move-on **cannot happen without a uniform** -- it is an
    act performed by an officer -- so `security.presence_at`'s own officer
    count IS the rate, and the class is silent in Downbelow because there are
    zero officers there, which is LAW-CRIME §2.5 saying so rather than a place
    list saying so.

    The evening weighting is not a constant either: LAW-CRIME §7.2 files the
    activity as "Station-evening", and a busker works where the money is, so
    the weight is the place's own crowd against its own daily peak.
    """
    pres = sec.presence_at(place, hour % 24.0)
    if not pres["policed"] or pres["officers"] <= 0.0:
        return 0.0
    pk = peak_occupancy(place)
    if pk <= 0.0:
        return 0.0
    return (pres["officers"] * MOVEONS_PER_OFFICER_H
            * crowd(place, hour) / pk)


# INV-384. Bracketed by FACTIONS §11.4's own enforcement sentence -- *"~150
# officers on duty across 8 km. Crime is not policed, it is contained at
# chokepoints"* -- which is what a move-on IS. ABOVE: at 1.0 the Zocalo's 12.9
# officers do nothing else all watch and the 150-strong duty roster is entirely
# consumed moving people on. BELOW: at 0.05 a busker is moved on once every
# fifty working days, and LAW-CRIME §7.2's "**Never inside the Zocalo** -- they
# are moved on" would simply not be true. `--report` prints the implied
# interval per busker, which is the sanity check INV-350's `implied_mtbf_days`
# is for this derivation.
MOVEONS_PER_OFFICER_H = 0.20


def _r_stockout(ctx, place, hour):
    """A counter runs out of a line, and THERE IS NO NEW CONSTANT IN IT.

    `economy.opening_stock` stands a counter with exactly `RESTOCK_DAYS` of its
    own mean demand and no safety stock -- so a line runs out whenever the
    realised demand over a restock cycle exceeds its own mean, which is a
    Poisson tail this can evaluate. Everything is `economy.py`'s: the lines
    from `stock_list`, the demand from `line_demand`, the depth from
    `opening_stock`, the cycle from `RESTOCK_DAYS`.

    And the shape it produces is a statement about that module rather than
    about this one: because the depth SCALES with demand, a big counter is no
    likelier to run out than a small one, and the small ones are SAFER --
    N'Grath's three thin lines carry ten units against a mean of 9.5 and run
    out 36% of a cycle, the Zocalo's fourteen fat ones sit at 50%. A stockout
    is a property of how deep a counter stands, not of how much it sells.
    """
    p = _stockout_cycle(place)
    if p <= 0.0:
        return 0.0
    pk = peak_occupancy(place)
    if pk <= 0.0:
        return 0.0
    return p / (ec.RESTOCK_DAYS * 24.0) * crowd(place, hour) / pk


def _stockout_cycle(place_key):
    """Expected lines running out per restock cycle at this counter."""
    def go():
        try:
            dem = ec.line_demand(place_key)
            dep = ec.opening_stock(place_key)
        except Exception:                                    # pragma: no cover
            return 0.0
        tot = 0.0
        for g, per_day in dem.items():
            mu = per_day * ec.RESTOCK_DAYS
            d = dep.get(g, 0)
            if mu <= 0.0:
                continue
            tot += _poisson_tail(mu, d)
        return tot
    return _memo(("stockout", place_key), go)


def _poisson_tail(mu, d):
    """P(N > d) for N ~ Poisson(mu). Exact for a small depth, normal with a
    continuity correction above `POISSON_CAP` where the sum stops being cheap
    -- the Zocalo's fattest line has mu = 1,611, which is 1,611 terms."""
    if d < POISSON_CAP:
        p = math.exp(-mu)
        cum = p
        for k in range(1, int(d) + 1):
            p *= mu / k
            cum += p
        return max(0.0, 1.0 - cum)
    z = (d + 0.5 - mu) / math.sqrt(mu)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


# --- endogenous state the rate functions read ------------------------------
# Kept module-level and RESET BY `simulate` so a rate can be a function of the
# world without every rate function taking the world -- the alternative is 22
# signatures carrying a parameter 19 of them ignore.
_WORLD_HEAT = {}
_WORLD_GRIEVANCE = [0.0]
_WORLD_DEBTORS = [0]
_WORLD_ELEV_DOWN = [False]
# {place: households whose earner is off their feet}. Written by INC-SICK's
# resolution, read by INC-ARREARS' rate, and the ONLY route between them --
# so a rent notice on day 2 is caused by an illness on day 1 and by nothing
# else, which is the same shape as INC-ACCIDENT -> INC-STRIKE one floor down.
_WORLD_SICKHOMES = {}
SWEEP_HEAT = 6.0                     # INV-358
STRIKE_THRESHOLD = 3.0               # INV-358
DRAZI_CYCLE_ON = False               # PEOPLE.md FAC-13: OFF at the datum


# ===========================================================================
# 7.  THE WORLD -- named facts, because a log string is not a world state
# ===========================================================================
# SYS-14's CHECK says the three stances must "differ in NAMED facts (which
# ledger row, whose standing, which stock line, who is in custody), not merely
# in a log string". So a fact is a triple (kind, subject, detail) and the
# subject is a person, a place or a ledger row id -- never prose.
MEANINGFUL = frozenset({"custody", "docket", "seizure", "standing", "stock",
                        "work_order", "card", "casualty", "camp",
                        "grievance"})
ALL_KINDS = MEANINGFUL | frozenset({"news", "unsolved", "berth", "rumour"})


class World:
    """The mutable half of the station, and it survives a day boundary."""

    def __init__(self, day=0):
        self.day = int(day)
        self.facts = []
        self.custody = {}
        self.heat = {}
        self.grievance = 0.0
        self.debtors = 0
        self.camps = {}
        self.elev_down = False
        self.sickhomes = {}
        self.log = []

    # -- writing ------------------------------------------------------------
    def fact(self, kind, subject, detail):
        if kind not in ALL_KINDS:
            raise ValueError(f"{kind} is not a world-delta kind")
        f = (kind, str(subject), str(detail))
        self.facts.append(f)
        return f

    def named(self):
        return frozenset(self.facts)

    def deltas(self):
        return [f for f in self.facts if f[0] in MEANINGFUL]

    def fingerprint(self):
        import hashlib
        h = hashlib.blake2b(digest_size=8)
        for f in sorted(self.facts):
            h.update(("|".join(f) + "\n").encode("utf-8"))
        return h.hexdigest()

    # -- the day boundary ---------------------------------------------------
    def carry(self):
        """What survives to day N+1, and what does not.

        A custody row survives -- somebody is still in the brig. Camp heat
        DECAYS, because LAW-CRIME's own sweep rule says the camp is back in six
        hours. The grievance board survives, because FAC-06's ballot is a
        standing count. The facts list does NOT survive: it is the day's log,
        and carrying it would make the day-2 diff trivially non-empty.
        """
        w = World(day=self.day + 1)
        w.custody = dict(self.custody)
        w.heat = {k: v * HEAT_DECAY for k, v in self.heat.items()}
        w.grievance = self.grievance
        # A LEDGER THAT ONLY GROWS IS NOT A LEDGER. Every theft and every
        # Downbelow contact adds a debtor and only the Collector's round takes
        # one off, so without this the pool compounds every day and INC-DEBT
        # eventually swamps the station. Debts settle, are written off, or the
        # debtor leaves; the same decay the camps get.
        w.debtors = int(self.debtors * HEAT_DECAY)
        w.camps = dict(self.camps)
        w.elev_down = self.elev_down
        # A household whose earner is ill RECOVERS, on the same decay the camps
        # and the ledger take. Without it every illness is permanent and by day
        # 5 the whole station is in arrears -- the compounding defect `carry`
        # already fixed once for the debtor pool, applied to the rule rather
        # than to the instance.
        w.sickhomes = {k: v * HEAT_DECAY for k, v in self.sickhomes.items()
                       if v * HEAT_DECAY >= 1.0}
        for who, row in sorted(self.custody.items()):
            w.fact("custody", who, f"held from day {row['day']}: {row['charge']}")
        return w


HEAT_DECAY = 0.5                     # INV-358


# --- the resolution vocabulary. every class composes these -----------------
def _case_id(inc):
    return f"{inc.cid}-D{inc.day}-{int(inc.hour * 60):04d}-{inc.place[:6]}"


def _arrest(w, inc, person, charge, by="patrol"):
    """WHO DETECTED IT IS PART OF THE ROW, and leaving it out collapsed a
    stance. With the same docket text in both branches, `absent` was a strict
    SUBSET of `reports` on every arresting class -- three fingerprints, but the
    absent world owned no fact of its own, so "the player reported it" and "a
    patrol happened by" were the same case file. `by` is the informant field a
    real docket carries."""
    w.custody[person.npc_id] = {"name": _who(person), "charge": charge,
                                "day": inc.day, "hour": inc.hour,
                                "at": inc.place, "by": by}
    w.fact("custody", person.npc_id,
           f"{_who(person)} booked at brig, {charge}, day {inc.day} "
           f"{inc.hour:05.2f}, detained on {by}")
    w.fact("docket", _case_id(inc),
           f"{_who(person)} -- {charge} (informant: {by})")


def _seize(w, inc, item, person):
    w.fact("seizure", _case_id(inc),
           f"{item} taken from {_who(person)} at {inc.place}")


def _standing(w, whose, faction, delta):
    w.fact("standing", f"{whose}:{faction}", f"{delta:+.1f}")


def _stock(w, place, good, delta):
    w.fact("stock", f"{place}:{good}", f"{delta:+d} units")


def _order(w, inc, what):
    w.fact("work_order", _case_id(inc), f"{what} at {inc.place}")


def _casualty(w, inc, person, how):
    w.fact("casualty", person.npc_id, f"{_who(person)} -- {how}")


def _unsolved(w, inc, what):
    w.fact("unsolved", _case_id(inc), what)


def _card(w, person, endorsement):
    w.fact("card", person.npc_id, f"{_who(person)}: {endorsement}")


def _camp(w, place, state):
    w.camps[place] = state
    w.fact("camp", place, state)


def _news(w, inc, item):
    w.fact("news", f"ISN-D{inc.day}-{inc.cid}", item)


def _grievance(w, delta, why):
    w.grievance += delta
    w.fact("grievance", f"board:{why}", f"{delta:+.1f} -> {w.grievance:.1f}")


def _heat(w, place, delta):
    w.heat[place] = w.heat.get(place, 0.0) + delta


ABSENT, HELPS, REPORTS = "absent", "helps", "reports"
STANCES = (ABSENT, HELPS, REPORTS)


def _responded(inc):
    """Did a uniform get there inside the incident's own window?"""
    t = response_s(inc.place, inc.hour)
    return t is not None and t <= inc.window_s


# ===========================================================================
# 8.  The twenty-two resolutions
# ===========================================================================
# Each is (incident, world, stance) -> writes. The three branches are written
# to differ in NAMED FACTS and the gate diffs them; where two branches collapse
# the gate says so instead of the module pretending otherwise.

def _res_liner(inc, w, st):
    n = 400 + int(400 * u("pax", inc.key()))
    w.fact("berth", inc.place, f"liner alongside, {n} souls at 8.5/min")
    _heat(w, inc.place, 1.0)
    if st == ABSENT:
        _news(w, inc, f"{n} arrivals cleared through {inc.place}; queue ran "
                      f"{n / 8.5:.0f} min")
    elif st == HELPS:
        _stock(w, inc.place, "aid-ration packs", -min(40, n // 20))
        _standing(w, "player", "earthforce", +0.5)
    else:
        _order(w, inc, "second desk opened on advisory")
        _standing(w, "player", "earthforce", +0.2)


def _res_elev(inc, w, st):
    w.elev_down = True
    _order(w, inc, f"bay elevator unit {1 + int(2 * u('u', inc.key()))} down")
    _grievance(w, 0.5, "elevator")
    if st == ABSENT:
        w.fact("berth", inc.place, "throughput halved; stack forms")
    elif st == HELPS:
        w.fact("berth", inc.place, "manual cycle held; throughput 0.75")
        _standing(w, "player", "dockers_guild", +1.0)
    else:
        _order(w, inc, "maintenance escalated by report")
        _standing(w, "player", "dockers_guild", -0.5)
        _standing(w, "player", "earthforce", +0.5)


def _res_contra(inc, w, st):
    person = inc.cast[0]
    item = _contra_item(inc)
    if st == ABSENT:
        if _responded(inc):
            _seize(w, inc, item, person)
            _arrest(w, inc, person, f"possession of {item}")
        else:
            _unsolved(w, inc, f"{item} through {inc.place} unremarked")
            _stock(w, "black_market", item, +1)
    elif st == HELPS:
        _card(w, person, "CUSTOMS-II annotated: assisted declaration")
        _seize(w, inc, item, person)
        _standing(w, "player", "earthforce", -0.2)
        _standing(w, "player", "criminal", +1.0)
    else:
        _seize(w, inc, item, person)
        _arrest(w, inc, person, f"possession of {item}", by="a report")
        _standing(w, "player", "earthforce", +1.0)
        _standing(w, "player", "criminal", -1.0)


def _contra_item(inc):
    goods = [g.name for g in ec.GOODS if g.klass == "contraband"]
    if not goods:                                            # pragma: no cover
        return "concealed weapon"
    return goods[int(u("item", inc.key()) * len(goods)) % len(goods)]


def _res_refused(inc, w, st):
    person = inc.cast[0]
    _card(w, person, "ENTRY REFUSED -- held for the next outbound hull")
    if st == ABSENT:
        _camp(w, _first(camp_places()), f"+1 from {inc.place}")
        w.fact("standing", f"{person.npc_id}:home", "camp")
    elif st == HELPS:
        _stock(w, inc.place, "passage", -1)
        _standing(w, "player", "earthforce", -0.2)
        w.fact("standing", f"{person.npc_id}:home", "outbound berth bought")
    else:
        _order(w, inc, "aid desk notified; case referred to immigration")
        _standing(w, "player", "earthforce", +0.3)


def _res_sweep(inc, w, st):
    _camp(w, inc.place, "emptied ahead of the sweep; re-forms +6 h")
    w.heat[inc.place] = 0.0
    if st == ABSENT:
        w.fact("news", f"PA-D{inc.day}-sweep", f"sweep of {inc.place}: fruitless")
    elif st == HELPS:
        _standing(w, "player", "lurkers", +1.0)
        _standing(w, "player", "earthforce", -1.0)
    else:
        person = inc.cast[0]
        _arrest(w, inc, person, "obstruction during a sweep", by="a report")
        _standing(w, "player", "lurkers", -2.0)
        _standing(w, "player", "earthforce", +1.0)


def _res_brawl(inc, w, st):
    a, b = inc.cast[0], inc.cast[-1]
    if st == ABSENT:
        _casualty(w, inc, b, "contusions, treated at medlab")
        if _responded(inc):
            _arrest(w, inc, a, "affray")
        else:
            _unsolved(w, inc, f"affray at {inc.place}, nobody held")
    elif st == HELPS:
        _casualty(w, inc, b, "separated before injury")
        _standing(w, "player", "drazi", -1.0)
    else:
        _arrest(w, inc, a, "affray", by="a report")
        _arrest(w, inc, b, "affray", by="a report")
        _standing(w, "player", "earthforce", +0.5)
    _heat(w, inc.place, 2.0)


def _res_denounce(inc, w, st):
    merchant = inc.cast[0]
    informer = inc.cast[-1]
    w.fact("docket", _case_id(inc),
           f"denunciation of {_who(merchant)} filed at {inc.place}")
    if st == ABSENT:
        w.fact("standing", f"{merchant.npc_id}:trade", "shuttered next morning")
        _standing(w, informer.npc_id, "nightwatch", +1.0)
    elif st == HELPS:
        w.fact("standing", f"{merchant.npc_id}:trade", "open, lines changed")
        _standing(w, "player", "nightwatch", -2.0)
        _standing(w, "player", "merchants", +1.0)
    else:
        _standing(w, "player", "nightwatch", +2.0)
        _arrest(w, inc, merchant, "sedition (Nightwatch referral)",
                by="a report")


def _res_dust(inc, w, st):
    dealer, buyer = inc.cast[0], inc.cast[-1]
    _seize(w, inc, "Dust", dealer)
    if st == ABSENT:
        _casualty(w, inc, buyer, "Dust assault -- recovers in days")
        _news(w, inc, "Psi Corps liaison notified; a Cop follows")
    elif st == HELPS:
        _casualty(w, inc, buyer, "intercepted before the dose")
        _standing(w, "player", "criminal", -2.0)
    else:
        _arrest(w, inc, dealer, "supply of a controlled substance (Dust)",
                by="a report")
        _standing(w, "player", "psi_corps", +1.0)
        _news(w, inc, "seizure logged; Corps follow-up scheduled")


def _res_pick(inc, w, st):
    thief, victim = inc.cast[0], inc.cast[-1]
    good = _lifted(inc)
    if st == ABSENT:
        if _responded(inc):
            _arrest(w, inc, thief, f"theft of {good}")
        else:
            _unsolved(w, inc, f"{good} lifted from {_who(victim)}")
            _stock(w, "black_market", good, +1)
            w.debtors += 1
    elif st == HELPS:
        w.fact("stock", f"{victim.npc_id}:{good}", "+1 recovered")
        _standing(w, "player", "criminal", -1.0)
        _standing(w, victim.npc_id, "player", +2.0)
    else:
        if _responded(inc):
            _arrest(w, inc, thief, f"theft of {good}", by="a report")
            _standing(w, "player", "earthforce", +1.0)
        else:
            _unsolved(w, inc, f"reported: {good} from {_who(victim)}, no unit")
            _standing(w, "player", "earthforce", +0.2)
    _heat(w, inc.place, 1.0)


def _lifted(inc):
    goods = [g.name for g in ec.GOODS]
    return goods[int(u("lift", inc.key()) * len(goods)) % len(goods)]


def _res_fraud(inc, w, st):
    person = inc.cast[0]
    if st == ABSENT:
        _card(w, person, "VISAS EXPIRED -- flagged, secondary inspection")
        if _responded(inc):
            _arrest(w, inc, person, "presenting an expired identicard")
        else:
            _unsolved(w, inc, f"{_who(person)} walked from the reader")
    elif st == HELPS:
        _card(w, person, "VISAS EXPIRED -- renewal lodged")
        _standing(w, "player", "earthforce", -0.5)
        _standing(w, person.npc_id, "player", +1.0)
    else:
        _card(w, person, "VISAS EXPIRED -- refused, docketed")
        _arrest(w, inc, person, "presenting an expired identicard",
                by="a report")
        _standing(w, "player", "earthforce", +0.5)


def _res_accident(inc, w, st):
    hurt = inc.cast[0]
    fatal = u("fatal", inc.key()) < 1.0 / ACCIDENT_RECORDABLE_PER_FATAL
    _order(w, inc, "dual clearance -- substandard chip, bay isolated")
    _grievance(w, 2.0, "accident")
    if st == ABSENT:
        _casualty(w, inc, hurt, "killed in the bay; morgue drawer tagged"
                  if fatal else "crush injury; medlab bed 3")
        _news(w, inc, "dock fatality; the guild calls a meeting" if fatal
              else "bay isolated pending the board")
    elif st == HELPS:
        _casualty(w, inc, hurt, "pulled clear -- burns, medlab bed 3")
        _standing(w, "player", "dockers_guild", +2.0)
    else:
        _casualty(w, inc, hurt, "killed in the bay; morgue drawer tagged"
                  if fatal else "crush injury; medlab bed 3")
        _order(w, inc, "clearance console impounded on report")
        _standing(w, "player", "dockers_guild", -1.0)
        _standing(w, "player", "earthforce", +1.0)


def _res_brownout(inc, w, st):
    _order(w, inc, "district shed; APU pickup, relight by priority")
    if st == ABSENT:
        w.fact("news", f"PA-D{inc.day}-{inc.cid}",
               f"{inc.place} district steps down; relight in order")
    elif st == HELPS:
        _order(w, inc, "manual transfer held; medlab kept lit")
        _standing(w, "player", "earthforce", +1.0)
    else:
        _order(w, inc, "shed reported; plant watch dispatched")
        _standing(w, "player", "engineers", +0.5)


def _res_quar(inc, w, st):
    person = inc.cast[0]
    w.fact("berth", inc.place, "arrival held; isolation path opened")
    if st == ABSENT:
        _casualty(w, inc, person, "isolated at PLC-046; hall throughput cut")
    elif st == HELPS:
        _casualty(w, inc, person, "walked to isolation without a scene")
        _standing(w, "player", "medical", +1.0)
    else:
        _casualty(w, inc, person, "isolated at PLC-046; hall throughput cut")
        _order(w, inc, "medical officer summoned by report")
        _standing(w, "player", "medical", +0.5)


def _res_psicop(inc, w, st):
    w.fact("rumour", inc.place, "corridors quieten; a Psi Cop pair aboard")
    _news(w, inc, "Psi Corps business call logged")
    if st == ABSENT:
        w.fact("rumour", f"{inc.place}:crowd", "volume down; nobody looks up")
    elif st == HELPS:
        w.fact("rumour", f"{inc.place}:crowd", "volume down; nobody looks up")
        _standing(w, "player", "psi_corps", +0.5)
    else:
        w.fact("rumour", f"{inc.place}:crowd", "volume down; nobody looks up")
        _standing(w, "player", "psi_corps", +0.5)


def _res_nc(inc, w, st):
    narn, cent = inc.cast[0], inc.cast[-1]
    want = fr.separation_m("narn", "centauri")
    w.fact("rumour", _case_id(inc),
           f"{_who(narn)} and {_who(cent)} stood off at {inc.place}; "
           f"{want:.2f} m wanted in a corridor that has less")
    if st == ABSENT:
        _unsolved(w, inc, "crowds rerouted; no complaint filed")
    elif st == HELPS:
        _standing(w, "player", "narn", +1.0)
        _standing(w, "player", "centauri", -1.0)
    else:
        _arrest(w, inc, narn, "obstruction", by="a report")
        _standing(w, "player", "narn", -2.0)
        _standing(w, "player", "earthforce", +0.5)
    _heat(w, inc.place, 1.0)


def _res_gqe(inc, w, st):
    celebrant = inc.cast[0]
    _seize(w, inc, "G'Quan Eth", celebrant)
    if st == ABSENT:
        w.fact("rumour", _case_id(inc), "ceremony held without the plant")
    elif st == HELPS:
        w.fact("rumour", _case_id(inc), "plant released on the player's word")
        _standing(w, "player", "narn", +2.0)
        _standing(w, "player", "earthforce", -1.0)
    else:
        _arrest(w, inc, celebrant, "import of a controlled substance",
                by="a report")
        _standing(w, "player", "narn", -2.0)


def _res_strike(inc, w, st):
    _grievance(w, -STRIKE_THRESHOLD, "ballot carried")
    w.fact("work_order", f"guild-D{inc.day}", "blue flu: muster thins 40%")
    if st == ABSENT:
        _news(w, inc, "guild action; deliveries slip a day")
        _stock(w, "quartermaster", "aid-ration packs", -20)
    elif st == HELPS:
        _standing(w, "player", "dockers_guild", +2.0)
        w.fact("work_order", f"guild-D{inc.day}-line", "player stands the line")
    else:
        _standing(w, "player", "dockers_guild", -3.0)
        _standing(w, "player", "earthforce", +1.0)


def _res_fault(inc, w, st):
    what = _broken(inc)
    _order(w, inc, f"{what} failed -- job raised, tech assigned")
    if st == ABSENT:
        w.fact("news", f"board-D{inc.day}-{inc.cid}", f"{what} out of service")
    elif st == HELPS:
        _order(w, inc, f"{what} cleared by hand before the tech walked")
        _standing(w, "player", "engineers", +1.0)
    else:
        _order(w, inc, f"{what} reported; priority raised")
        _standing(w, "player", "engineers", +0.3)


def _broken(inc):
    q = q_of(inc.place)
    xs = q["interacts"] or ("fitting",)
    return xs[int(u("brk", inc.key()) * len(xs)) % len(xs)]


def _res_hold(inc, w, st):
    w.fact("berth", inc.place, "stack forming at the standoff ring")
    if st == ABSENT:
        w.fact("news", f"PA-D{inc.day}-hold", "port calls: arrivals delayed")
        _heat(w, inc.place, 1.0)
    elif st == HELPS:
        w.fact("berth", f"{inc.place}:manual", "one hull walked in by hand")
        _standing(w, "player", "traffic", +1.0)
    else:
        _order(w, inc, "C&C advised; berth map re-sequenced")
        _standing(w, "player", "traffic", +0.5)


def _res_contact(inc, w, st):
    lurker, mark = inc.cast[0], inc.cast[-1]
    if st == ABSENT:
        _unsolved(w, inc, f"{_who(mark)} marked out and relieved of a bag")
        w.debtors += 1
        _stock(w, "black_market", "kit bag", +1)
    elif st == HELPS:
        w.fact("stock", f"{mark.npc_id}:kit bag", "+1 kept")
        _standing(w, "player", "lurkers", -1.0)
    else:
        if _responded(inc):
            _arrest(w, inc, lurker, "robbery", by="a report")
        else:
            _unsolved(w, inc, "reported; no unit in Downbelow, by design")
        _standing(w, "player", "lurkers", -2.0)
    _heat(w, inc.place, 1.5)


def _res_debt(inc, w, st):
    debtor = inc.cast[0]
    w.debtors = max(0, w.debtors - 1)
    if st == ABSENT:
        _casualty(w, inc, debtor, "a beating; ledger rolls")
        w.fact("rumour", inc.place, "the camp does not look at the Collector")
    elif st == HELPS:
        w.fact("stock", f"{debtor.npc_id}:credits", "debt paid by the player")
        _standing(w, "player", "criminal", -1.0)
        _standing(w, debtor.npc_id, "player", +3.0)
    else:
        _arrest(w, inc, debtor, "questioned on a protection racket",
                by="a report")
        _standing(w, "player", "criminal", -3.0)
    _heat(w, inc.place, 1.0)


def _res_pakma(inc, w, st):
    diner = inc.cast[0]
    w.fact("rumour", _case_id(inc),
           f"{_who(diner)} took a pak'ma'ra table at {inc.place}; "
           f"the tables cleared")
    if st == ABSENT:
        w.fact("standing", f"{inc.place}:seating", "section left empty an hour")
    elif st == HELPS:
        w.fact("standing", f"{inc.place}:seating", "diner moved; tables refill")
        _standing(w, "player", "pakmara", +1.0)
    else:
        w.fact("standing", f"{inc.place}:seating", "staff resolved on request")
        _standing(w, "player", "hospitality", +0.5)


# ---------------------------------------------------------------------------
# THE EIGHT DOMESTIC AND COMMERCIAL RESOLUTIONS
# ---------------------------------------------------------------------------
# Every one of them writes a named fact per stance and NONE of them books
# anybody into the brig in the ABSENT branch. `--gate` counts it.

def _role_of(person):
    """This person's role, through `schedule.role_for` -- the same function
    `resident.resident` used to build them, so the resolution and the roster
    cannot disagree about what somebody does."""
    return sched.role_for(person.npc_id, person.species).key


def _home_of(person):
    """And where they live, through `resident.home_for`. Not the incident's
    place: somebody who collapses in the Zocalo goes home to a block, and
    WHICH block is what decides whether the household loses its earner."""
    return res.home_for(person.npc_id, person.species, _role_of(person))


def _person_rung(person):
    """The rung on this person's own card, by role. Not the block's."""
    return _role_rung(_role_of(person))


# CITIZEN AND ABOVE ENTER BY RIGHT; TRANSIT AND BELOW HOLD A PERMISSION. That
# line is `consequence.TIERS`' own, in its own words -- TRANSIT is *"a
# conditional permission -- so it expires, and so it can be withdrawn"* and
# SANCTUARY is *"a GRANT ... and a grant can be withdrawn"*, against CITIZEN's
# *"enters by right"*. It is the line a door, a counter and an Ombuds all draw,
# and it is where the domestic classes below bite differently on two people
# living one deck apart.
CONDITIONAL = cq.TRANSIT


def _rung_of(place_key):
    """The rung this block's tenancy is on -- `consequence`'s ladder, keyed by
    the same `rent_row` the price came from, so the money and the standing
    cannot disagree about who lives here."""
    row = rent_row(place_key)
    for t, r in sorted(cq.RENT_TIER.items(), reverse=True):
        if r == row:
            return t
    return cq.NO_STATUS                                      # pragma: no cover


def _res_neighbour(inc, w, st):
    a, b = inc.cast[0], inc.cast[-1]
    w.fact("rumour", _case_id(inc),
           f"{_who(a)} and {_who(b)} through the bulkhead at {inc.place}; "
           f"{_who(b)} keeps a {b.species} clock")
    if st == ABSENT:
        _standing(w, a.npc_id, b.npc_id, -1.0)
        _standing(w, b.npc_id, a.npc_id, -1.0)
        w.fact("standing", f"{inc.place}:corridor", "two doors that do not "
                                                   "greet each other")
    elif st == HELPS:
        _standing(w, a.npc_id, "player", +1.0)
        _standing(w, b.npc_id, "player", +1.0)
        w.fact("rumour", f"{inc.place}:corridor", "the landing goes quiet")
    else:
        w.fact("docket", _case_id(inc),
               f"noise complaint, {inc.place}, {_who(a)} v {_who(b)} -- "
               f"listed before the Ombuds")
        _standing(w, a.npc_id, "player", -2.0)
        _standing(w, b.npc_id, "player", -2.0)
    _heat(w, inc.place, 0.5)


def _res_lockout(inc, w, st):
    person = inc.cast[0]
    low = _person_rung(person) <= CONDITIONAL
    if st == ABSENT:
        if low:
            _card(w, person, "reader rejected at own door -- status queried")
            w.fact("standing", f"{person.npc_id}:home",
                   f"a night out of {inc.place}")
            _camp(w, _first(camp_homes()), f"+1 locked out of {inc.place}")
        else:
            _order(w, inc, "door controller logged fault; tenant waits")
            w.fact("standing", f"{person.npc_id}:home",
                   f"waited {int(1 + 3 * u('wait', inc.key()))} h at the door")
    elif st == HELPS:
        _card(w, person, "admitted on a neighbour's word; annotation only")
        _standing(w, person.npc_id, "player", +2.0)
    else:
        _order(w, inc, "door controller replaced on report")
        if low:
            _card(w, person, "REFERRED -- reader rejects, immigration notified")
            _standing(w, person.npc_id, "player", -2.0)
            _standing(w, "player", "earthforce", +0.5)
        else:
            _standing(w, "player", "engineers", +0.3)


def _res_arrears(inc, w, st):
    tenant = inc.cast[0]
    row = rent_row(inc.place)
    due = rent_week_cr(inc.place)
    w.sickhomes[inc.place] = max(0.0, w.sickhomes.get(inc.place, 0.0) - 1.0)
    if st == ABSENT:
        _card(w, tenant, f"TENANCY {row}: notice served, {due:.0f} cr owing")
        w.fact("stock", f"{tenant.npc_id}:credits", f"-{due:.0f} cr owing")
        _standing(w, tenant.npc_id, "housing", -1.0)
    elif st == HELPS:
        w.fact("stock", f"{tenant.npc_id}:credits",
               f"+{due:.0f} cr, arrears cleared by the player")
        _standing(w, tenant.npc_id, "player", +3.0)
        _standing(w, "player", "merchants", -0.5)
    else:
        w.fact("docket", _case_id(inc),
               f"{_who(tenant)} -- {row} arrears {due:.0f} cr, listed before "
               f"the Ombuds")
        _card(w, tenant, f"TENANCY {row}: referred, {due:.0f} cr")
        _standing(w, tenant.npc_id, "player", -3.0)


def _res_still(inc, w, st):
    keeper, customer = inc.cast[0], inc.cast[-1]
    line = _brewed(inc)
    if st == ABSENT:
        _stock(w, inc.place, line, +int(2 + 6 * u("batch", inc.key())))
        w.fact("rumour", _case_id(inc),
               f"{_who(keeper)}'s pitch at {inc.place} is open; "
               f"{_who(customer)} is in the queue")
        _camp(w, inc.place, "a kitchen, a still and a chair working")
    elif st == HELPS:
        _stock(w, inc.place, line, +int(6 + 6 * u("batch2", inc.key())))
        _standing(w, "player", "lurkers", +1.0)
        _standing(w, keeper.npc_id, "player", +2.0)
    else:
        _seize(w, inc, f"unlicensed {line}", keeper)
        _arrest(w, inc, keeper, f"unlicensed supply of {line}", by="a report")
        _camp(w, inc.place, "the pitch is gone; the queue has nowhere")
        _standing(w, "player", "lurkers", -3.0)
        _standing(w, "player", "earthforce", +0.5)
    _heat(w, inc.place, 0.5)


def _brewed(inc):
    """What the pitch makes: a `GOODS` line that a camp could actually source
    -- drum or hydroponics grown, or route-supplied. Not an invented menu."""
    goods = [g.name for g in ec.GOODS
             if g.supply in ("drum", "hydroponics", "route")]
    if not goods:                                            # pragma: no cover
        return "still spirit"
    return goods[int(u("brew", inc.key()) * len(goods)) % len(goods)]


def _res_sick(inc, w, st):
    person = inc.cast[0]
    bed, _why = cq.admits(_first(medical_places()), _person_rung(person))
    home = _home_of(person)
    if st == ABSENT:
        if bed:
            _casualty(w, inc, person,
                      f"taken from {inc.place} to a medlab bed")
        else:
            # THE RUNG IS THE WHOLE CONTENT OF THIS BRANCH. FACTIONS 6.2's
            # stateless and 3.4's card-avoiders are not admitted, which is why
            # LAW-CRIME §7.3 says the pattern is "informal patronage, not an
            # institution" and why Franklin's free clinic existed at all.
            _casualty(w, inc, person,
                      f"left at {inc.place}; the card does not admit them")
            w.sickhomes[home] = w.sickhomes.get(home, 0.0) + 1.0
            _standing(w, person.npc_id, "housing", -0.5)
    elif st == HELPS:
        _casualty(w, inc, person, "walked to triage on the player's arm")
        _standing(w, "player", "medical", +1.0)
        _standing(w, person.npc_id, "player", +2.0)
    else:
        _casualty(w, inc, person, "medical team dispatched on report")
        _order(w, inc, "triage team walked from the nearest medlab")
        _standing(w, "player", "medical", +0.5)
        if not bed:
            w.sickhomes[home] = w.sickhomes.get(home, 0.0) + 1.0


def _res_stray(inc, w, st):
    child, finder = inc.cast[0], inc.cast[-1]
    # A CHILD'S ROLE IS THEIR HOUSEHOLD'S, and there are only three it can be:
    # `resident._age` says minors exist in `NO_WAGE_ROLES` and nowhere else, so
    # the child is drawn from those three by their own headcounts rather than
    # assigned one here. That is what decides whether a card exists to read.
    role = _child_role(inc)
    home = res.home_for(child.npc_id, child.species, role)
    carded = _role_rung(role) > cq.NO_STATUS
    w.fact("rumour", _case_id(inc),
           f"a {child.species} child at {inc.place}, which is no place for one")
    if st == ABSENT:
        if u("hurt", inc.key()) < STRAY_HARM_SHARE:
            _casualty(w, inc, child, f"hurt at {inc.place}; carried out")
        else:
            _unsolved(w, inc, f"nobody claimed the child at {inc.place}")
        _standing(w, child.npc_id, "housing", -0.5)
    elif st == HELPS:
        w.fact("standing", f"{child.npc_id}:home", f"walked back to {home}")
        _standing(w, finder.npc_id, "player", +2.0)
        _standing(w, "player", "lurkers", +0.5)
    else:
        if carded:
            _card(w, child, f"MINOR: returned to {home} by security")
            _standing(w, "player", "earthforce", +0.5)
        else:
            # AND REPORTING IT IS NOT THE KIND ACT. A child with no card is
            # not taken home, they are taken into the system -- FACTIONS 3.4's
            # "the reason lurkers avoid readers", one generation down.
            _card(w, child, "NO STATUS -- minor, referred to immigration")
            _standing(w, "player", "lurkers", -2.0)
            _standing(w, "player", "earthforce", +0.5)


def _child_role(inc):
    """visitor / refugee / lurker, by their own headcounts on the roster."""
    tot = {r: sum(int(w.get(r, 0)) for w in sched.ROLE_WEIGHTS.values())
           for r in NO_WAGE_ROLES}
    n = sum(tot.values()) or 1
    r = u("childrole", inc.key()) * n
    acc = 0
    for role in NO_WAGE_ROLES:
        acc += tot[role]
        if r <= acc:
            return role
    return NO_WAGE_ROLES[-1]                                 # pragma: no cover


# INV-384: how often a child found somewhere hazardous has already been hurt.
# Bounded above by INC-ACCIDENT's own 100:1 recordable-to-fatal ratio, which
# says an industrial volume hurts people at far below the rate it holds them;
# below by zero, which would make `ADULT_FUNCTIONS` a label rather than a
# hazard. A tenth is a scrape, a burn or a fall, most of which the resolution
# treats as "carried out" rather than as a casualty ward.
STRAY_HARM_SHARE = 0.10


def _res_moveon(inc, w, st):
    busker, officer = inc.cast[0], inc.cast[-1]
    took = 1 + int(TAKINGS_CR * u("take", inc.key()))
    if st == ABSENT:
        w.fact("stock", f"{busker.npc_id}:credits",
               f"pitch ended; {took} cr short of the day")
        _standing(w, busker.npc_id, "earthforce", -1.0)
        w.fact("rumour", inc.place, "the boards get their frontage back")
    elif st == HELPS:
        w.fact("stock", f"{busker.npc_id}:credits", f"+{took} cr, given")
        _standing(w, "player", "lurkers", +1.0)
        _standing(w, busker.npc_id, "player", +2.0)
    else:
        w.fact("docket", _case_id(inc),
               f"{_who(busker)} moved on from {inc.place} on a report by "
               f"{_who(officer)}; obstruction noted, no charge")
        _standing(w, "player", "lurkers", -2.0)
        _standing(w, "player", "merchants", +1.0)


# A day's busking, and it is the LADDER's own bottom rung rather than a new
# number: LAW-CRIME §7.1 prices a Downbelow bunk at 1 cr/night and a cart meal
# at 1-2 cr, so a day that ends short of a bunk and a meal is a day that
# matters. `economy.ladder` supplies both.
TAKINGS_CR = (ec.ladder("bunk_dosshouse")[0]
              + ec.ladder("meal_cart")[1] * MEALS_PER_DAY)


def _res_stockout(inc, w, st):
    keeper, customer = inc.cast[0], inc.cast[-1]
    line = _sold_out(inc)
    _stock(w, inc.place, line, -1)
    w.fact("stock", f"{inc.place}:{line}", "line empty; board changed")
    if st == ABSENT:
        w.fact("stock", f"{inc.place}:substitute",
               "the next line up carries the trade")
        _standing(w, customer.npc_id, keeper.npc_id, -1.0)
    elif st == HELPS:
        alt = _other_counter(inc)
        _stock(w, alt, line, -2)
        _stock(w, inc.place, line, +2)
        _standing(w, keeper.npc_id, "player", +2.0)
    else:
        _order(w, inc, f"{line} re-ordered against the next consignment")
        _standing(w, "player", "merchants", +0.5)


def _sold_out(inc):
    try:
        lines = list(ec.stock_list(inc.place))
    except Exception:                                        # pragma: no cover
        lines = []
    if not lines:                                            # pragma: no cover
        return "the house line"
    return lines[int(u("line", inc.key()) * len(lines)) % len(lines)]


def _other_counter(inc):
    ks = [k for k in counter_places() if k != inc.place]
    if not ks:                                               # pragma: no cover
        return inc.place
    return ks[int(u("alt", inc.key()) * len(ks)) % len(ks)]


def _first(seq):
    return seq[0] if seq else "downbelow"


# --- the table itself -------------------------------------------------------
def _cast1(place, hour, seed, hint):
    return _cast_at(place, hour, seed, 1, role_hint=hint)


def _cast2(place, hour, seed, hint, sp_a=None, sp_b=None):
    a = _cast_at(place, hour, seed, 1, species=sp_a, role_hint=hint + "a")
    b = _cast_at(place, hour, seed + "b", 1, species=sp_b, role_hint=hint + "b")
    return [a[0], b[0]]


CLASSES = (
    Klass("INC-LINER", "liner arrival surge", customs_halls, _r_liner,
          lambda p, h, s: _cast1(p, h, s, "pax"),
          ("one hall at 8.5 souls/min for ~90 min", "queue overflow",
           "advisory PA"), _res_liner, window_s=5400.0),
    Klass("INC-ELEV", "one bay elevator down", elevator_places, _r_elev,
          lambda p, h, s: _cast1(p, h, s, "crew"),
          ("unit down", "INC-HOLD forms", "guild grievance line"),
          _res_elev, window_s=1800.0),
    Klass("INC-CONTRA", "contraband find at scan", customs_halls, _r_contra,
          lambda p, h, s: _cast1(p, h, s, "pax"),
          ("find", "seizure room PLC-003", "custody or fine"), _res_contra,
          window_s=300.0),
    Klass("INC-REFUSED", "refused entry waiting in the hall", customs_halls,
          _r_refused, lambda p, h, s: _cast1(p, h, s, "pax"),
          ("hall wait", "failed passage", "Downbelow leak"), _res_refused,
          window_s=3600.0),
    Klass("INC-SWEEP", "announced security sweep of a camp", camp_places,
          _r_sweep, lambda p, h, s: _cast1(p, h, s, "lurker"),
          ("PA-announced approach", "camp empties ahead of it", "fruitless",
           "re-forms +6 h"), _res_sweep, window_s=1800.0, endogenous=True),
    Klass("INC-BRAWL", "Drazi factional brawl", crowd_places, _r_brawl,
          lambda p, h, s: _cast2(p, h, s, "drazi", "drazi", "drazi"),
          ("shove", "melee", "RESTRAIN arrests"), _res_brawl, window_s=120.0),
    Klass("INC-DENOUNCE", "Nightwatch denunciation of a merchant",
          crowd_places, _r_denounce,
          lambda p, h, s: _cast2(p, h, s, "denounce"),
          ("box report", "19:00 muster read-out", "questioning scene",
           "shutter or changed lines"), _res_denounce,
          era="nightwatch_visible", window_s=600.0),
    Klass("INC-DUST", "Dust seizure", market_places, _r_dust,
          lambda p, h, s: _cast2(p, h, s, "dust"),
          ("deal", "seizure", "casualty to medlab", "Corps follow-up"),
          _res_dust, window_s=300.0),
    Klass("INC-PICK", "petty theft", theft_places, _r_pick,
          lambda p, h, s: _cast2(p, h, s, "pick"),
          ("lift", "detection-by-presence", "chase/arrest or clean escape"),
          _res_pick, window_s=60.0),
    Klass("INC-FRAUD", "forged/expired identicard at a reader", reader_places,
          _r_fraud, lambda p, h, s: _cast1(p, h, s, "card"),
          ("flag", "secondary inspection", "refusal/custody", "docket"),
          _res_fraud, window_s=300.0),
    Klass("INC-ACCIDENT", "dock clearance accident chain", clearance_places,
          _r_accident, lambda p, h, s: _cast1(p, h, s, "docker"),
          ("bad part", "dual clearance", "casualty", "union action"),
          _res_accident, window_s=180.0),
    Klass("INC-BROWNOUT", "power shed event", power_places, _r_brownout,
          lambda p, h, s: _cast1(p, h, s, "watch"),
          ("shed", "district lights step down", "APU pickup",
           "relight by priority"), _res_brownout, window_s=900.0),
    Klass("INC-QUAR", "medical quarantine arrival", customs_halls, _r_quar,
          lambda p, h, s: _cast1(p, h, s, "pax"),
          ("hold", "roped queue", "isolation path PLC-046", "clear/extend"),
          _res_quar, window_s=1800.0),
    Klass("INC-PSICOP", "Psi Cop visit",
          lambda: _keys("telepath_office", "zocalo"), _r_psicop,
          lambda p, h, s: _cast1(p, h, s, "psi"),
          ("arrival", "corridors quieten", "business call", "departure"),
          _res_psicop, window_s=7200.0),
    Klass("INC-NC", "Narn-Centauri contact event", crowd_places, _r_nc,
          lambda p, h, s: _cast2(p, h, s, "nc", "narn", "centauri"),
          ("stand-off", "no yield", "crowds reroute", "rare escalation"),
          _res_nc, window_s=180.0),
    Klass("INC-GQE", "G'Quan Eth seizure", customs_halls, _r_gqe,
          lambda p, h, s: _cast1(p, h, s, "narn"),
          ("seizure", "argued at the desk", "ceremony with/without the plant",
           "sometimes docket"), _res_gqe, window_s=600.0),
    Klass("INC-STRIKE", "dockers' blue flu / grievance action", dock_places,
          _r_strike, lambda p, h, s: _cast1(p, h, s, "guild"),
          ("ballot", "slowdown", "muster thins", "delivery ripple",
           "settlement"), _res_strike, window_s=28800.0, endogenous=True),
    Klass("INC-FAULT", "a machine breaks", machine_places, _r_fault,
          lambda p, h, s: _cast1(p, h, s, "tech"),
          ("fault", "order", "walk", "repair", "close"), _res_fault,
          window_s=1800.0),
    Klass("INC-HOLD", "inbound hold stack", clearance_places, _r_hold,
          lambda p, h, s: _cast1(p, h, s, "traffic"),
          ("stack forms at standoff", "PA delay calls",
           "tempers in the arrival hall"), _res_hold, window_s=3600.0,
          endogenous=True),
    Klass("INC-CONTACT", "Downbelow contact event", downbelow_places,
          _r_contact, lambda p, h, s: _cast2(p, h, s, "contact"),
          ("approach", "demand/beg/warn", "resolve comply|resist|flee"),
          _res_contact, window_s=90.0),
    Klass("INC-DEBT", "debt enforcement round", camp_places, _r_debt,
          lambda p, h, s: _cast1(p, h, s, "debtor"),
          ("visit", "pay/plead/hide", "seizure or a beating",
           "ledger closes or rolls"), _res_debt, window_s=600.0,
          endogenous=True),
    Klass("INC-PAKMA", "pak'ma'ra eating-area segregation friction",
          eating_places, _r_pakma,
          lambda p, h, s: _cast2(p, h, s, "pakma", None, "pakmara"),
          ("polite translator ask", "tables clear", "staff resolve",
           "a rumour line"), _res_pakma, window_s=600.0),

    # -- the eight that are not crimes -----------------------------------
    Klass("INC-NEIGHBOUR", "a dispute across a bulkhead", home_places,
          _r_neighbour, lambda p, h, s: _cast2(p, h, s, "neighbour"),
          ("a wall", "two clocks", "a landing that stops greeting",
           "a complaint or a quiet word"), _res_neighbour, window_s=900.0),
    Klass("INC-LOCKOUT", "a door that will not admit its own tenant",
          lockable_places, _r_lockout,
          lambda p, h, s: _cast1(p, h, s, "tenant"),
          ("the reader refuses", "the panel or the card",
           "a wait, a neighbour or immigration"), _res_lockout,
          window_s=1800.0),
    Klass("INC-ARREARS", "rent arrears, and who calls about them",
          tenancy_places, _r_arrears,
          lambda p, h, s: _cast1(p, h, s, "tenant"),
          ("the earner stopped", "a week's margin gone", "notice served",
           "cleared, carried or listed"), _res_arrears, window_s=3600.0,
          endogenous=True),
    Klass("INC-STILL", "the camp's own kitchen, still and barber's chair",
          camp_homes, _r_still, lambda p, h, s: _cast2(p, h, s, "still"),
          ("a pitch opens", "a queue", "a batch, a shave or a wash",
           "trade, help or a seizure"), _res_still, window_s=1800.0),
    Klass("INC-SICK", "somebody needs a clinician and there is not one",
          sick_places, _r_sick, lambda p, h, s: _cast1(p, h, s, "patient"),
          ("collapse", "the crowd opens", "the card is read",
           "a bed, an arm or nothing"), _res_sick, window_s=600.0),
    Klass("INC-STRAY", "a child where a child should not be", stray_places,
          _r_stray, lambda p, h, s: _cast2(p, h, s, "stray"),
          ("a child at a hazard", "nobody claims them",
           "walked home, or referred"), _res_stray, window_s=1200.0),
    Klass("INC-MOVEON", "a busker moved off the licensed floor",
          moveon_places, _r_moveon, lambda p, h, s: _cast2(p, h, s, "moveon"),
          ("a pitch on the boards", "an officer crosses",
           "moved on, paid or docketed"), _res_moveon, window_s=300.0),
    Klass("INC-STOCKOUT", "a counter runs out of a line", counter_places,
          _r_stockout, lambda p, h, s: _cast2(p, h, s, "stock"),
          ("the line empties", "the board changes",
           "a substitute, a favour or a re-order"), _res_stockout,
          window_s=1800.0),
)

BY_ID = {k.cid: k for k in CLASSES}

# The eight added in session 4o, kept as a named set because every control in
# the gate that talks about "the lived-in half" has to be able to REMOVE them
# and re-measure. A control that cannot subtract its own subject is a claim.
LIVED_IN = ("INC-NEIGHBOUR", "INC-LOCKOUT", "INC-ARREARS", "INC-STILL",
            "INC-SICK", "INC-STRAY", "INC-MOVEON", "INC-STOCKOUT")
CRIME_ORIGINAL = tuple(k.cid for k in CLASSES if k.cid not in LIVED_IN)


def books_custody(cid, stance=ABSENT, hour=13.0, seed="b5"):
    """Does this class put somebody in the brig in this stance?

    THE FRAMING CLAIM, MADE MEASURABLE. "Do not just add more crime" is an
    assertion until something counts, and the thing to count is what the
    station does when NOBODY IS WATCHING -- the absent branch. Seven of the
    original twenty-two book a custody row there; the eight above book none.
    """
    _inc, worlds, _sets, _uniq = three_ways(cid, hour=hour, seed=seed)
    return bool(worlds[stance].custody)


# ===========================================================================
# 9.  THE TICK -- a rate, drawn, in a place, at an hour
# ===========================================================================
class Incident:
    __slots__ = ("cid", "place", "day", "hour", "cast", "window_s", "seed")

    def __init__(self, cid, place, day, hour, cast, window_s, seed):
        self.cid = cid
        self.place = place
        self.day = day
        self.hour = hour
        self.cast = cast
        self.window_s = window_s
        self.seed = seed

    def key(self):
        return f"{self.cid}|{self.place}|{self.day}|{self.hour:.4f}|{self.seed}"

    def __repr__(self):                                      # pragma: no cover
        return (f"<{self.cid} {self.place} d{self.day} {self.hour:05.2f} "
                f"{', '.join(_who(c) for c in self.cast)}>")


def live_classes(ctx, place, hour):
    """Every class with a non-zero rate here, and its rate. The gate's own
    denominator: a class with rate zero is not a class that fired and failed,
    it is a class this place and this era have no business running."""
    return _fixed_lams(ctx, place, hour) + _live_lams(ctx, place, hour)


# A RATE IS CONSTANT WITHIN AN HOUR AND THE STEP LOOP MUST NOT RE-DERIVE IT.
# The first version evaluated all 22 rate functions for all 128 places on every
# one-minute step -- 4.05 MILLION rate calls for one station-day, each of them
# reaching into `populace.occupancy`, `security.presence_at` and
# `traffic.hall_rate` -- and one `--gate` run did not finish in fifteen
# minutes. Nineteen of the 22 classes read only (place, hour, day, era), all of
# which are constant inside an hour bucket, so their rates are built ONCE per
# (day, era, hour, place) and the step loop does nothing but draw.
#
# The other three are ENDOGENOUS -- they read the world the run is writing --
# so they are re-derived every step, which is 3/22 of the old cost and is the
# part that has to stay live. That split is why `Klass.endogenous` exists.
_LAM = {}


def _bucket_h(hour):
    """The hour a rate is evaluated at. Mid-bucket, and the SAME value however
    the step is chosen, so the 4x-step control measures the Bernoulli
    discretisation and not a different set of rates."""
    return float(int(hour) % 24) + 0.5


def _fixed_lams(ctx, place, hour):
    key = (ctx.day, ctx.datum, int(hour) % 24, place)
    t = _LAM.get(key)
    if t is None:
        hb = _bucket_h(hour)
        t = []
        for k in CLASSES:
            if k.endogenous:
                continue
            if k.era is not None and not era_on(k.era, ctx.datum):
                continue
            if not k.here(place):
                continue
            lam = k.rate(ctx, place, hb)
            if lam > 0.0:
                t.append((k, lam))
        t = tuple(t)
        _LAM[key] = t
    return list(t)


_ENDO = []


def _live_lams(ctx, place, hour):
    if not _ENDO:
        _ENDO.extend(k for k in CLASSES if k.endogenous)
    out = []
    for k in _ENDO:
        if not k.here(place):
            continue
        if k.era is not None and not era_on(k.era, ctx.datum):
            continue
        lam = k.rate(ctx, place, _bucket_h(hour))
        if lam > 0.0:
            out.append((k, lam))
    return out


POISSON_CAP = 32


def _poisson(mu, r):
    """How many events this step, by inverse CDF from ONE uniform.

    A COIN FLIP PER STEP TRUNCATES AT ONE EVENT AND THE STEP CONTROL SAW IT.
    The first version drew `1 - exp(-mu)` and fired at most once, which is
    exact only while `mu << 1`. INC-DEBT's Collector round and INC-HOLD's
    berth stack both run at several an hour in one place, so at a four-minute
    step `mu` reaches 0.6 and every second event was thrown away: the 4x-step
    control came back **12.4% low over a station-day**, and that was the model
    losing events rather than the step being coarse.

    This is still a PER-STEP draw -- the events land in the minute they are
    drawn in, so the step still decides when things happen -- but the count is
    unbiased at any step, which is what the control should be measuring the
    residual of rather than the bulk of.
    """
    p = math.exp(-mu)
    cum = p
    k = 0
    while r > cum and k < POISSON_CAP:
        k += 1
        p *= mu / k
        cum += p
    return k


def scope_places(scope=None):
    if scope is None:
        return tuple(p["key"] for p in dr.PLACES)
    if isinstance(scope, Probe):
        return scope.places
    return tuple(scope)


def simulate(ctx, world=None, start_h=13.0, window_min=WINDOW_MIN,
             step_min=STEP_MIN, scope=None, classes=None):
    """One window of station time over a set of places. No observer.

    THE DRAW IS PER STEP, NOT PER HOUR, and that is deliberate even though a
    per-hour Poisson count would be cheaper and exactly step-invariant. A
    generator whose answer cannot depend on the step size cannot have that
    dependence measured, and `--gate` runs the whole window again at 4x the
    step and prints how far the answer moved. An invariance you built in by
    construction is not an invariance you tested.
    """
    w = World(day=ctx.day) if world is None else world
    ks = CLASSES if classes is None else tuple(classes)
    places = scope_places(scope)
    steps = int(round(window_min / step_min))
    dt_h = step_min / 60.0

    # publish the endogenous state the rate functions read
    _WORLD_HEAT.clear()
    _WORLD_HEAT.update(w.heat)
    _WORLD_GRIEVANCE[0] = w.grievance
    _WORLD_DEBTORS[0] = w.debtors
    _WORLD_ELEV_DOWN[0] = w.elev_down
    _WORLD_SICKHOMES.clear()
    _WORLD_SICKHOMES.update(w.sickhomes)

    allow = None if classes is None else {k.cid for k in ks}
    fired = []
    for si in range(steps):
        hour = start_h + si * step_min / 60.0
        hb = int(hour) % 24
        for place in places:
            lams = _fixed_lams(ctx, place, hour)
            lams.extend(_live_lams(ctx, place, hour))
            for k, lam in lams:
                if allow is not None and k.cid not in allow:
                    continue
                r = u(k.cid, place, ctx.seed, ctx.day, si, hb)
                for c in range(_poisson(lam * dt_h, r)):
                    cast = k.cast(place, hour,
                                  f"{ctx.seed}-{ctx.day}-{si}-{c}")
                    inc = Incident(k.cid, place, ctx.day, hour, cast,
                                   k.window_s, ctx.seed)
                    k.resolve(inc, w, ABSENT)
                    fired.append(inc)
                    w.log.append(inc)
                    _WORLD_HEAT.clear()
                    _WORLD_HEAT.update(w.heat)
                    _WORLD_GRIEVANCE[0] = w.grievance
                    _WORLD_DEBTORS[0] = w.debtors
                    _WORLD_ELEV_DOWN[0] = w.elev_down
                    _WORLD_SICKHOMES.clear()
                    _WORLD_SICKHOMES.update(w.sickhomes)
    return w, fired


def expected_rate(ctx, probe, hour, only=None):
    """The probe volume's incident rate per station-hour, summed analytically.

    The measurement the gate leads with. It is the SUM OF THE CLASS RATES over
    the probe's fixed places, which is what "incidents per station-hour" means
    before any draw is made -- so it cannot be moved by a lucky seed, and the
    simulated count can be checked against it.

    `only` restricts the sum to a set of class ids, and it exists so the
    before/after in `--gate` is a SUBTRACTION OF THE SAME NUMBERS rather than a
    second derivation: the "before" figure is this same call over the original
    twenty-two, on the same code path, with the eight new rows left out of the
    sum. A before/after computed two different ways measures the two ways.
    """
    tot = 0.0
    per = {}
    for place in probe.places:
        for k, r in live_classes(ctx, place, hour):
            if only is not None and k.cid not in only:
                continue
            per[k.cid] = per.get(k.cid, 0.0) + r
            tot += r
    return tot, per


def expected_day(ctx, scope=None, endogenous=False):
    """The analytic integral of the class rates over 24 station-hours.

    ENDOGENOUS CLASSES ARE EXCLUDED BY DEFAULT AND THAT IS NOT A DODGE: their
    rate is written by the run itself -- INC-SWEEP's by camp heat, INC-STRIKE's
    by the grievance board, INC-DEBT's by the debtor pool, INC-HOLD's by
    whether an elevator is down -- so there is no static integral to compare a
    draw against. That is the whole point of them, and the gate checks them a
    different way: they must be ZERO in a fresh world and non-zero after a day.
    """
    places = scope_places(scope)
    tot = 0.0
    for h in range(24):
        for place in places:
            for k, r in _fixed_lams(ctx, place, float(h)):
                if endogenous or not k.endogenous:
                    tot += r
    return tot


def class_rate_day(ctx, cid, scope=None):
    """One class's analytic incidents-per-day over a scope.

    THE ERA GATE LIVES HERE AND THE FIRST VERSION LEFT IT OUT -- caught by this
    module's own era control, which reported INC-DENOUNCE at **6.164/day at
    S2E01 and 6.164/day at the datum** and said DOES NOT FIRE. The era test was
    in `_fixed_lams` and in `simulate`, and this function reached past both
    straight into `k.rate`, which knows nothing about the datum. A gate that
    consults a different code path from the one the content runs on is a gate
    that cannot see the content's own switches.
    """
    k = BY_ID[cid]
    if k.era is not None and not era_on(k.era, ctx.datum):
        return 0.0
    return sum(k.rate(ctx, place, float(h) + 0.5)
               for h in range(24)
               for place in scope_places(scope) if k.here(place))


def near(inc, at, radius_m=None):
    """Is this incident within sight of a player standing at `at`?"""
    radius_m = sight_m() if radius_m is None else radius_m
    return distance_m(inc.place, at) <= radius_m


# ===========================================================================
# 10.  THE THREE STANCES
# ===========================================================================
def three_ways(cid, ctx=None, place=None, hour=13.0, seed="b5"):
    """One SEEDED incident, replayed absent / helps / reports.

    The same incident object -- same class, same place, same hour, same named
    cast -- resolved into three FRESH worlds. Returns
    {stance: (world, facts)} plus the facts unique to each, which is the
    quantity SYS-14's CHECK actually asks for.
    """
    ctx = Ctx() if ctx is None else ctx
    k = BY_ID[cid]
    ps = k.places()
    if place is None:
        place = ps[0] if ps else "zocalo"
    cast = k.cast(place, hour, seed)
    inc = Incident(cid, place, ctx.day, hour, cast, k.window_s, seed)
    out = {}
    for st in STANCES:
        w = World(day=ctx.day)
        k.resolve(inc, w, st)
        out[st] = w
    sets = {st: out[st].named() for st in STANCES}
    uniq = {st: sets[st] - set().union(*(sets[o] for o in STANCES if o != st))
            for st in STANCES}
    return inc, out, sets, uniq


def stance_report(cid, out=print, **kw):
    inc, worlds, sets, uniq = three_ways(cid, **kw)
    k = BY_ID[cid]
    out(f"{cid} -- {k.title}")
    out(f"  at {inc.place} {inc.hour:05.2f}, cast "
        f"{', '.join(_who(c) for c in inc.cast)}")
    out(f"  escalation: {' -> '.join(k.beats)}")
    n_distinct = len({worlds[s].fingerprint() for s in STANCES})
    for st in STANCES:
        w = worlds[st]
        out(f"  [{st:7s}] {len(w.deltas())} delta(s), "
            f"fingerprint {w.fingerprint()}")
        for f in sorted(uniq[st]):
            out(f"      only here: {f[0]}/{f[1]} = {f[2]}")
    out(f"  DISTINCT WORLD STATES: {n_distinct} of 3")
    return n_distinct


# ===========================================================================
# 11.  A HEADLESS DAY, AND THE DAY BOUNDARY
# ===========================================================================
def headless_day(ctx, world=None, step_min=STEP_MIN, scope=None, hours=24):
    """Twenty-four station-hours over `scope`, carrying the world through."""
    w = World(day=ctx.day) if world is None else world
    fired = []
    for h in range(hours):
        w, f = simulate(ctx, w, start_h=float(h), window_min=60.0,
                        step_min=step_min, scope=scope)
        fired.extend(f)
    return w, fired


def two_days(at="customs_north", step_min=STEP_MIN, seed="b5", scope=None,
             datum=cos.ERA_DATUM):
    """Day 1 -> carry -> day 2, and day 2 again from a FRESH world.

    The persistence evidence, and it is a controlled comparison rather than an
    assertion: the SAME day-2 seed, the SAME class table, the SAME places, run
    once with day 1's consequences carried in and once without. If the two
    day-2s are identical then nothing persisted and the claim is false.
    """
    scope = scope_places(scope)
    c1 = Ctx(day=1, datum=datum, seed=seed)
    w1, f1 = headless_day(c1, step_min=step_min, scope=scope)

    c2 = Ctx(day=2, datum=datum, seed=seed)
    carried = w1.carry()
    w2, f2 = headless_day(c2, world=carried, step_min=step_min, scope=scope)

    fresh = World(day=2)
    w2f, f2f = headless_day(Ctx(day=2, datum=datum, seed=seed), world=fresh,
                            step_min=step_min, scope=scope)
    return (w1, f1), (w2, f2), (w2f, f2f)


# ===========================================================================
# 12.  Reports
# ===========================================================================
def report(out=print, at="customs_north", hour=13.0, day=0):
    ctx = Ctx(day=day)
    probe = Probe(at)
    out("THE INCIDENT GENERATOR -- 22 classes, every rate somebody else's "
        "number")
    out("")
    out(f"PROBE VOLUME (fixed at tick start): {probe.describe()}")
    tot, per = expected_rate(ctx, probe, hour)
    out(f"  rate at {hour:05.2f} on day {day}: "
        f"{tot:.3f} incidents/station-hour")
    out("")
    out(f"{'class':14s} {'rate/h here':>12s}  {'places':>6s}  what it reads")
    out("-" * 78)
    for k in CLASSES:
        ps = k.places()
        r = per.get(k.cid, 0.0)
        gated = ("" if k.era is None
                 else f" [era {cos.ERA_EVENTS[k.era][0]}]")
        endo = " [endogenous]" if k.endogenous else ""
        out(f"{k.cid:14s} {r:12.4f}  {len(ps):6d}  {k.title}{gated}{endo}")
    out("-" * 78)
    out(f"maintenance roster {maint_heads():,} heads -> "
        f"{maint_capacity_per_day():,.0f} corrective jobs/day of CAPACITY. "
        f"{machine_instances_total():,} declared interactables built "
        f"({sum(len(q['interacts']) for q in dr.PLACES)} types x "
        f"{sum(_bays(q['key']) for q in dr.PLACES):,} bays) at a "
        f"{MACHINE_MTBF_DAYS:.0f}-day MTBF = "
        f"{visible_faults_per_day():,.1f} visible faults/day, which is "
        f"{maint_load_share() * 100:.1f}% of capacity "
        f"(the bound puts the shortest survivable MTBF at "
        f"{implied_mtbf_days():.1f} days)")
    ref, rfd, con, exp, med = card_outcomes()
    out(f"customs, measured through arrival.checks over {CARD_SAMPLES} cards: "
        f"refused {ref * 100:.1f}%, referred {rfd * 100:.1f}%, "
        f"contraband {con * 100:.1f}%, expired visa {exp * 100:.1f}%, "
        f"unnumbered atmosphere {med * 100:.1f}%")
    domestic_report(out)
    return tot


def domestic_report(out=print):
    """The lived-in half's own denominators, each with its cross-check."""
    homes = home_places()
    units = sum(units_in(k) for k in homes)
    people = sum(peak_occupancy(k) for k in homes)
    out("")
    out(f"HOUSING: {len(homes)} register rows, {units:,} built dwelling units "
        f"(rooms.bays_in) holding {people:,.0f} residents at their own peak "
        f"hours -- {people / max(1, units):.2f} people a unit. The EA-standard "
        f"blocks all land at ~3.07 and the camps at "
        f"{household_size('downbelow'):.2f} (downbelow) and "
        f"{household_size('downbelow_arch'):.2f} "
        f"(downbelow_arch), which is the overcrowding ratio nothing else in "
        f"this project computes (INV-380)")
    roster = sum(sum(v.values()) for v in home_roster().values())
    out(f"  AND THE GAP IS REPORTED RATHER THAN ABSORBED: "
        f"resident.home_for over schedule.ROLE_WEIGHTS houses "
        f"{roster:,.0f} people, so the register's built housing is "
        f"{100.0 * people / max(1.0, roster):.1f}% "
        f"of the roster's. Every rate below is per HOUSEHOLD PRESENT, so a "
        f"player standing in one block sees that block rather than the "
        f"station's notional 250,000 -- INV-350's denominator lesson, the "
        f"other way round")
    for k in homes:
        d = home_roster().get(k) or {}
        top = sorted(d.items(), key=lambda x: -x[1])[:2]
        out(f"    {k:22s} {units_in(k):5d} units  rent {rent_row(k):18s} "
            f"{rent_week_cr(k):5.1f} cr/wk  no-wage share "
            f"{role_share(k, NO_WAGE_ROLES) * 100:5.1f}%  "
            + ", ".join(f"{r} {int(c):,}" for r, c in top))
    lo, _hi = ec.casual_constraint()
    out(f"  SUBSISTENCE: {weekly_subsistence_cr():.1f} cr a household-week "
        f"(cheapest tenancy + {MEALS_PER_DAY:.0f} cart meals a day) against "
        f"{casual_week_cr():.1f} cr of casual labour at "
        f"{lo:.0f} cr/day over {MUSTER_DAYS_PER_WEEK:.0f} muster days -- "
        f"a margin of {casual_week_cr() - weekly_subsistence_cr():.1f} cr, "
        f"which is why INC-ARREARS is endogenous")
    out(f"  MEDICAL: {medical_beds()} built diagnostic beds at "
        f"{ADMIT_OCCUPANCY:.0%} for {BED_DAYS:.0f} days = "
        f"{admissions_per_day():.1f} admissions/day (the FLOOR); "
        f"{medical_heads():,} medical staff can attend "
        f"{medical_capacity_per_day():,.0f}/day (the CEILING); the geometric "
        f"mean is {presentations_per_day():,.1f} presentations/day = "
        f"{episodes_per_head_year():.3f} per head per year, "
        f"{medical_load_share() * 100:.1f}% of capacity. "
        f"{medical_heads() / max(1, medical_beds()):.0f} staff per built bed "
        f"is the same shortfall the housing has")
    out(f"  THE CAMPS' OWN ECONOMY: {lurker_heads():,} lurkers, "
        f"LAW-CRIME 7.2's {LURKER_SERVICE_SHARE:.0%} cooking/brewing/laundry/"
        f"barbering = {service_pitches():,.0f} pitches at "
        f"{SERVICE_EVENT_PER_PITCH_DAY:.2f} events/day; its "
        f"{LURKER_BUSK_SHARE:.0%} begging/busking = {busker_heads():,.0f} "
        f"buskers")
    mv = sum(_r_moveon(Ctx(), k, float(h)) for k in moveon_places()
             for h in range(24))
    out(f"  MOVE-ONS: {mv:.1f}/day station-wide from "
        f"security.presence_at's own officer count -- one every "
        f"{busker_heads() / max(1e-9, mv):.1f} working days per busker, which "
        f"is the sanity check INV-350's implied_mtbf_days is for that one")
    out(f"  CHILDREN: {child_heads():,.0f} at the datum "
        f"({child_heads((2, 1)):,.0f} before narn_surrender), from "
        f"resident._age's own {MINOR_SHARE:.0%} minor rule over "
        f"{', '.join(NO_WAGE_ROLES)}")


# WHAT KIND OF PLACE THIS IS, from the register's own function words. Used
# only to REPORT where the station is alive -- "12 of 128" is a number nobody
# can act on, and "0 of 13 homes" is. Order matters: a place is labelled by the
# first row it matches, so `downbelow` reads as a camp rather than as commerce.
DISTRICTS = (
    ("home", ("residence",)),
    ("camp", ("informal_residence",)),
    ("arrival", ("immigration", "arrival", "ship_arrival", "ship_departure",
                 "cargo_handling", "ship_mooring")),
    ("commerce", ("commerce", "retail", "hospitality", "food_service",
                  "recreation", "gambling", "nightlife", "public_social",
                  "crowd_hub", "catering")),
    ("plant", ("power_generation", "power_distribution", "reactor",
               "life_support", "atmosphere", "air_handling",
               "waste_processing", "water_reclamation", "fabrication",
               "agriculture", "cooling")),
    ("medical", ("medical", "triage", "quarantine", "mortuary")),
    ("law", ("law_enforcement", "detention", "adjudication",
             "political_policing", "checkpoint")),
    ("civic", ("worship", "ceremony", "diplomacy", "council_session",
               "administration", "offices", "meeting", "observation",
               "contemplation")),
)


def district_of(place_key):
    fns = set(q_of(place_key)["functions"])
    for name, want in DISTRICTS:
        if fns & set(want):
            return name
    return "works"


def rate_map(ctx, hour=13.0, top=12, out=print):
    """Where the station is alive, and where it is not.

    IT REPORTS BY DISTRICT NOW, AND THAT IS THE POINT OF THE SESSION. The
    number this printed before -- "12 of 128 clear the floor" -- was true and
    unactionable, because it hid the SHAPE of the failure: every one of the
    twelve was the arrival half, the plant or Downbelow, and the homes and the
    commercial ring were at zero to four decimal places. `READ THE SHAPE OF A
    FAILING NUMBER BEFORE READING ITS SIZE` is this repository's own rule and
    the total could not express the shape. Per district it can.
    """
    rows = []
    for p in dr.PLACES:
        probe = Probe(p["key"])
        tot, _per = expected_rate(ctx, probe, hour)
        rows.append((tot, p["key"], probe))
    rows.sort(reverse=True)
    met = sum(1 for r in rows if r[0] >= RATE_FLOOR)
    out(f"  probe volumes at {hour:05.2f} meeting the >=2/station-hour floor: "
        f"{met} of {len(rows)}")
    for tot, key, probe in rows[:top]:
        out(f"    {key:22s} {tot:7.3f}/h   {len(probe.places)} place(s), "
            f"{probe.span_m:6.0f} m span")
    out(f"    ... {len(rows) - top} more, floor "
        f"{rows[-1][0]:.4f}/h at {rows[-1][1]}")
    by = {}
    for tot, key, _probe in rows:
        d = by.setdefault(district_of(key), [])
        d.append(tot)
    out(f"  BY DISTRICT ({'over'} the register's own function words):")
    for name, _w in DISTRICTS + (("works", ()),):
        v = by.get(name)
        if not v:
            continue
        v = sorted(v, reverse=True)
        out(f"    {name:9s} {sum(1 for x in v if x >= RATE_FLOOR):3d}/"
            f"{len(v):<3d} clear   best {v[0]:7.3f}/h   "
            f"median {v[len(v) // 2]:7.3f}/h   worst {v[-1]:7.4f}/h")
    return rows, met


def district_rate(ctx, name, hour, only=None):
    """(mean, best, cleared, n) over one district. The before/after number."""
    vals = [expected_rate(ctx, Probe(p["key"]), hour, only=only)[0]
            for p in dr.PLACES if district_of(p["key"]) == name]
    if not vals:                                             # pragma: no cover
        return 0.0, 0.0, 0, 0
    return (sum(vals) / len(vals), max(vals),
            sum(1 for v in vals if v >= RATE_FLOOR), len(vals))


RATE_FLOOR = 2.0             # SYS-14, in writing

# Below the 12.4% the Bernoulli-per-step draw scored before `_poisson` landed,
# so this gate fails if that regression comes back rather than merely being
# "under a quarter".
STEP_TOLERANCE = 0.10


# ===========================================================================
# 13.  Gate
# ===========================================================================
_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def spec_ids(path, prefix="INC-"):
    """Every INC id defined in a spec file, read from the file itself.

    The gate does NOT trust this module's own list. `docs/spec/PLACES.md` §0.2
    and `docs/spec/SYSTEMS.md` SYS-14 both enumerate the vocabulary and the
    spec says in writing that they are "the same 22 IDs, 1:1 in both
    directions"; this parses both and asserts the union three ways, so a class
    added here without a spec row -- or a spec row with no class -- fails.
    """
    import re
    ids = set()
    with open(path) as f:
        for line in f:
            m = re.match(r"^\|\s*(INC-[A-Z]+)\s*\|", line)
            if m:
                ids.add(m.group(1))
    return ids


def _verdict(fired, rate, w, probe):
    """Which content assertions a given run would fail.

    Kept separate from `gate` so the SAME list can be turned on the state of
    the project BEFORE this module -- which is a station with no incident
    layer at all, i.e. an empty class table. An assertion set that has only
    ever been pointed at the case it was written for is an assertion set
    nobody has tested.
    """
    bad = []
    cids = {i.cid for i in fired}
    if rate < RATE_FLOOR:
        bad.append(f"{RATE_FLOOR}+ incidents/station-hour in the probe volume")
    if not fired:
        bad.append("an incident happens at all, without a player")
    if len(cids) < 3:
        bad.append("at least three DIFFERENT classes fire")
    if len(w.deltas()) < 2:
        bad.append("incidents write world deltas, not log strings")
    if not w.custody:
        bad.append("somebody is in custody who was not before")
    if len({f[0] for f in w.deltas()}) < 3:
        bad.append("three different KINDS of delta are written")
    return len(bad), 6, bad


def gate(out=print, at="customs_north", hour=13.0, step_min=STEP_MIN,
         window_min=WINDOW_MIN, seed="b5"):    # noqa: C901
    del _FAILED[:]
    n = 0
    ctx = Ctx(day=1, seed=seed)
    probe = Probe(at)

    # ------------------------------------------------------------------
    # A.  THE CLASS TABLE IS THE SPEC'S, and the spec is read to prove it
    # ------------------------------------------------------------------
    ours = {k.cid for k in CLASSES}
    places_ids = spec_ids(SPEC_PLACES)
    systems_ids = spec_ids(SPEC_SYSTEMS)
    out(f"CLASSES {len(ours)}; PLACES 0.2 has {len(places_ids)}, "
        f"SYS-14 has {len(systems_ids)}")
    n += 1
    check(ours == places_ids == systems_ids,
          "the class table IS docs/spec's vocabulary, both directions, read "
          "from the two spec files rather than from this module's own list",
          f"only here {sorted(ours - places_ids)}, only in PLACES "
          f"{sorted(places_ids - ours)}, only in SYSTEMS "
          f"{sorted(systems_ids - ours)}")
    n += 1
    # NOT A LITERAL. The count used to be written `== 22` here, which meant the
    # class table's SIZE was a fact about this file rather than about the spec
    # -- so growing the table meant editing the assertion that was supposed to
    # be guarding it. It is the spec's own count, read from the spec, for the
    # same reason `len(dr.PLACES)` replaced 128 elsewhere in this project.
    check(len(ours) == len(places_ids) == len(systems_ids) > 0,
          "the class COUNT is the spec's count, read from the spec -- not a "
          "literal in this file that has to be edited to let the table grow",
          f"{len(ours)} here, {len(places_ids)} in PLACES 0.2, "
          f"{len(systems_ids)} in SYS-14")

    # ------------------------------------------------------------------
    # B.  THE RATE, IN A FIXED PROBE VOLUME
    # ------------------------------------------------------------------
    out("")
    out(f"PROBE (fixed at tick start): {probe.describe()}")
    out(f"  a player standing at {at} sees {sight_m():.1f} m "
        f"(populace.corridor_sight_m), so the probe is {probe.span_m:.0f} m "
        f"of station and the sight radius is what makes an incident WITNESSED")
    rate, per = expected_rate(ctx, probe, hour)
    live = sorted(((v, k) for k, v in per.items()), reverse=True)
    out(f"  expected {rate:.3f} incidents/station-hour at {hour:05.2f}: "
        + ", ".join(f"{c} {v:.3f}" for v, c in live[:6]))
    n += 1
    check(rate >= RATE_FLOOR,
          f"SYS-14's RATE FLOOR: >={RATE_FLOOR} meaningful incidents per "
          f"station-hour inside a FIXED probe volume -- fixed at tick start "
          f"from the register's own adjacency, never a radius chosen after "
          f"the numbers are in",
          f"{rate:.3f}/h over {len(probe.places)} places")

    # SIMULATED OVER THE WHOLE STATION, NOT OVER THE PROBE, and that is the
    # difference between an assertion and a tautology. The first version ran
    # `simulate(scope=probe)` and then checked that every incident was inside
    # the probe -- which cannot fail, because the probe was the only thing
    # simulated. MASTER-PLAN G3 asks for "N incidents, M reachable" and M is
    # only a number if N is bigger than it.
    w, fired = simulate(ctx, start_h=hour, window_min=window_min,
                        step_min=step_min, scope=None)
    out(f"  simulated {window_min:.0f} station-minutes at {step_min:.0f}-min "
        f"steps over all {len(dr.PLACES)} places: N = {len(fired)} "
        f"incident(s), {len(w.deltas())} world delta(s), "
        f"{len(w.custody)} in custody")
    n += 1
    check(len(fired) > 0,
          "AND IT ACTUALLY FIRES: the 60-minute headless window MASTER-PLAN "
          "G3 asks for logs incidents, with no player anywhere in the call",
          f"{len(fired)}")
    # A ONE-HOUR COUNT CANNOT TEST A RATE, and the first version of this gate
    # asserted that it could: at 5.6/h a Poisson draw of 2 is an ordinary hour
    # and the assertion failed on nothing. The comparison has to be over enough
    # events for the law of large numbers to bite, so it is the whole station
    # over a whole day against the analytic integral of the same rates.
    day_ctx = Ctx(day=1, seed=seed)
    wd, fd = headless_day(day_ctx, step_min=step_min)
    exp_day = expected_day(day_ctx)
    drawn_fixed = sum(1 for i in fd if not BY_ID[i.cid].endogenous)
    n += 1
    check(abs(drawn_fixed - exp_day) <= 3.0 * math.sqrt(max(1.0, exp_day)),
          "THE DRAWS AGREE WITH THE RATES. Over one station-day the count of "
          "non-endogenous incidents sits inside 3 sqrt(N) of the analytic "
          "integral of the same class rates -- so the headline is a rate and "
          "not a lucky seed",
          f"{drawn_fixed} drawn against {exp_day:.1f} expected, "
          f"3 sigma = {3.0 * math.sqrt(exp_day):.1f}")

    # -- reachable / witnessed ------------------------------------------
    r_m = sight_m()
    reach = [i for i in fired if i.place in probe]
    seen = [i for i in reach if near(i, at, r_m)]
    inside = [k for k in probe.places if distance_m(k, at) <= r_m]
    out(f"  M reachable: {len(reach)} of {len(fired)} fell inside the fixed "
        f"probe volume; {len(seen)} of those within {r_m:.1f} m of a player "
        f"standing at {at} -- the probe holds {len(inside)} of its "
        f"{len(probe.places)} places inside that radius "
        f"({', '.join(inside)}), so "
        f"{100.0 * len(seen) / max(1, len(reach)):.0f}% of what reaches the "
        f"player is witnessable on foot without moving")
    n += 1
    check(0 < len(reach) < len(fired),
          "M IS A SUBSET OF N AND BOTH ARE REAL. The station is simulated "
          "whole and the probe volume then counted out of it -- the first "
          "version simulated the probe alone and asserted every incident was "
          "inside it, which cannot fail",
          f"{len(reach)} reachable of {len(fired)} station-wide")
    n += 1
    check(len(seen) > 0,
          "...and at least one of them happens where a player standing still "
          "could see it, at populace.corridor_sight_m rather than at a radius "
          "chosen here",
          f"{len(seen)} within {r_m:.1f} m")

    # -- the station-wide picture, printed rather than asserted ---------
    out("")
    out("WHERE THE STATION IS ALIVE (every place's own probe volume):")
    rows, met = rate_map(ctx, hour, out=out)
    n += 1
    check(met >= 1,
          "at least one probe volume on the station clears the floor -- and "
          "the honest finding is that most do NOT, because a residential ring "
          "has nothing to go wrong in and no class table changes that",
          f"{met} of {len(rows)}")

    # ------------------------------------------------------------------
    # C.  MANY CLASSES, NOT ONE INCIDENT
    # ------------------------------------------------------------------
    out("")
    by = {}
    for i in fd:
        by[i.cid] = by.get(i.cid, 0) + 1
    out(f"ONE HEADLESS STATION-DAY over all {len(dr.PLACES)} places: "
        f"{len(fd)} incidents in {len(by)} classes, "
        f"{len(wd.deltas())} world deltas, {len(wd.custody)} in custody")
    for cid, c in sorted(by.items(), key=lambda x: -x[1]):
        out(f"    {cid:14s} {c:5d}")
    silent = sorted(ours - set(by))
    out("  silent classes and WHY, which is content rather than a gap:")
    for cid in silent:
        r = class_rate_day(day_ctx, cid)
        k = BY_ID[cid]
        why = ("era-gated, not yet in force" if k.era is not None
               and not era_on(k.era, day_ctx.datum)
               else "switch OFF at the datum (FAC-13)" if cid == "INC-BRAWL"
               else "endogenous: its trigger did not happen today"
               if k.endogenous
               else f"one every {1.0 / r:.1f} days, P(none today)="
                    f"{math.exp(-r):.0%}" if r > 0
               else "rate is exactly zero here")
        out(f"    {cid:14s} {r:8.4f}/day  {why}")
    loud = [c for c in silent if class_rate_day(day_ctx, c) > 3.0]
    n += 1
    check(not loud,
          "and every silent class is silent for a stated reason -- an era "
          "that has not arrived, a switch that is off, a trigger that did not "
          "happen, or a rate whose Poisson chance of a quiet day is not "
          "small. A class with an expected count above 3 that never fired "
          "would be a class that is wired up wrong",
          f"{loud} expected >3/day and drew none")
    n += 1
    check(len(by) >= 8,
          "MASTER-PLAN G3's own parenthesis -- '(not one incident)'. At least "
          "eight distinct classes fire in one station-day",
          f"{len(by)} classes: {sorted(by)}")
    n += 1
    check(len(fd) >= 24,
          "...and a day is a day's worth, not a handful",
          f"{len(fd)} in 24 station-hours")

    # ------------------------------------------------------------------
    # D.  THREE STANCES, THREE WORLD STATES, IN NAMED FACTS
    # ------------------------------------------------------------------
    out("")
    out("ABSENT / HELPS / REPORTS -- three world states per class:")
    three, two, one = [], [], []
    for k in CLASSES:
        _inc, worlds, _sets, _uniq = three_ways(k.cid, ctx=ctx, hour=hour,
                                                seed=seed)
        d = len({worlds[s].fingerprint() for s in STANCES})
        (three if d == 3 else two if d == 2 else one).append(k.cid)
    out(f"  3 distinct: {len(three)}   2 distinct: {len(two)} {two}   "
        f"1: {len(one)} {one}")
    n += 1
    check(len(three) >= 20,
          "SYS-14's CHECK: each class replayed absent/helps/reports yields "
          "three world states differing in NAMED FACTS -- not in a log string",
          f"{len(three)} of {len(CLASSES)} give three")
    n += 1
    check(not one,
          "and no class collapses all three stances into one world -- a class "
          "the player cannot change is a cutscene",
          f"{one}")

    demo = "INC-PICK"
    out("")
    stance_report(demo, out=out, ctx=ctx, hour=hour, seed=seed)
    _inc, worlds, sets, uniq = three_ways(demo, ctx=ctx, hour=hour, seed=seed)
    n += 1
    check(all(uniq[s] for s in STANCES),
          f"...and on {demo} every stance owns at least one fact the other "
          f"two do not -- which is the difference between three outcomes and "
          f"one outcome with three labels",
          {s: len(uniq[s]) for s in STANCES})

    # ------------------------------------------------------------------
    # E.  A CONSEQUENCE THAT PERSISTS TO DAY N+1
    # ------------------------------------------------------------------
    out("")
    (w1, f1), (w2, f2), (w2f, f2f) = two_days(step_min=step_min, seed=seed)
    carried = w1.carry()
    out(f"DAY 1: {len(f1)} incidents, {len(w1.custody)} in custody, "
        f"grievance board {w1.grievance:+.1f}, "
        f"camp heat on {len(w1.heat)} place(s)")
    out(f"DAY 2 with day 1 carried in: {len(f2)} incidents, "
        f"{len(w2.custody)} in custody, grievance {w2.grievance:+.1f}")
    out(f"DAY 2 from a FRESH world, same seed: {len(f2f)} incidents, "
        f"{len(w2f.custody)} in custody, grievance {w2f.grievance:+.1f}")
    still = sorted(set(carried.custody) & set(w1.custody))
    out(f"  {len(still)} person(s) arrested on day 1 are STILL IN CUSTODY at "
        f"the start of day 2 -- e.g. "
        f"{w1.custody[still[0]]['name'] if still else '(none)'}"
        + (f", {w1.custody[still[0]]['charge']}" if still else ""))
    n += 1
    check(len(still) > 0,
          "A CONSEQUENCE THAT PERSISTS TO DAY N+1: somebody booked on day 1 "
          "is in the brig on day 2, by name and by charge",
          f"{len(still)} custody rows carried")
    n += 1
    check(w2.fingerprint() != w2f.fingerprint(),
          "...and day 2 is a DIFFERENT DAY because of day 1: the same seed, "
          "the same class table and the same places, run once with day 1's "
          "consequences carried in and once without, produce different "
          "worlds. If they matched, nothing persisted",
          f"{w2.fingerprint()} against {w2f.fingerprint()}")
    d_only = w2.named() - w2f.named()
    out(f"  {len(d_only)} named fact(s) exist on day 2 ONLY because of day 1; "
        f"first: {sorted(d_only)[0] if d_only else '(none)'}")
    n += 1
    check(len(d_only) > 0,
          "and the difference is NAMED FACTS, enumerable, not a hash that "
          "differs for an unstated reason",
          f"{len(d_only)}")

    # ------------------------------------------------------------------
    # F.  THE SAME ASSERTIONS AGAINST THE STATE BEFORE THIS MODULE
    # ------------------------------------------------------------------
    out("")
    out("negative controls:")
    empty_w, empty_f = simulate(ctx, start_h=hour, window_min=window_min,
                                step_min=step_min, scope=probe, classes=())
    before = _verdict(empty_f, 0.0, empty_w, probe)
    out(f"  THE SAME ASSERTIONS AGAINST THE PRE-4o STATE (no incident layer "
        f"at all, which is what the project had): {before[0]} of {before[1]} "
        f"FAIL")
    for line in before[2]:
        out(f"    would FAIL: {line}")
    n += 1
    check(before[0] >= 5,
          "and this gate FAILS on the station as it was -- five of six "
          "content assertions cannot pass on a station with no incident "
          "generator, which is the honest before/after",
          f"{before[0]} of {before[1]}")
    n += 1
    check(not empty_f and not empty_w.deltas(),
          "THE CONTROL THAT MATTERS: empty the class table and the same "
          "station, the same seed and the same hour produce zero incidents "
          "and zero deltas",
          f"{len(empty_f)} incidents, {len(empty_w.deltas())} deltas")

    # -- the era control -------------------------------------------------
    # ON RATES, NOT ON A ONE-HOUR DRAW. INC-DENOUNCE runs at 0.26/h over the
    # whole station, so a single hour comes back 0 at BOTH eras and the control
    # reports nothing. A rate of exactly zero is a statement; a drawn zero on a
    # rare class is an hour going by.
    early = Ctx(day=1, datum=(2, 1), seed=seed)
    late = Ctx(day=1, seed=seed)
    nw_e = class_rate_day(early, "INC-DENOUNCE")
    nw_l = class_rate_day(late, "INC-DENOUNCE")
    all_e = expected_day(early)
    gated = [k.cid for k in CLASSES if k.era is not None]
    out(f"  at S2E01, before The Fall of Night: INC-DENOUNCE runs at "
        f"{nw_e:.4f}/day against {nw_l:.3f}/day at the datum, and the station "
        f"still runs {all_e:.0f} incidents/day -- the era gate "
        f"{'FIRES' if nw_e == 0 < nw_l else 'DOES NOT FIRE'}")
    n += 1
    check(nw_e == 0 < nw_l,
          "THE ERA REACHES THE INCIDENT LAYER. Before The Fall of Night "
          "(2,22) there is no armband, so no denunciation can be filed; at "
          "the datum S3E05 it can. Era-gated classes: " + str(gated),
          f"{nw_e} at S2E01 against {nw_l:.3f} at the datum")
    n += 1
    check(all_e > 0,
          "...and the station is not incident-FREE at S2E01 -- the thefts, "
          "the faults and the customs hall do not need an armband",
          f"{all_e:.0f} incidents/day at S2E01")

    # -- the Drazi switch, which is OFF at the datum ---------------------
    global DRAZI_CYCLE_ON
    off = class_rate_day(late, "INC-BRAWL")
    keep = DRAZI_CYCLE_ON
    try:
        DRAZI_CYCLE_ON = True
        _LAM.clear()
        on = class_rate_day(Ctx(day=1, seed=seed), "INC-BRAWL")
    finally:
        DRAZI_CYCLE_ON = keep
        _LAM.clear()
    out(f"  the Drazi factional cycle is OFF at the datum (PEOPLE.md FAC-13): "
        f"INC-BRAWL runs at {off:.4f}/day; with the switch thrown, "
        f"{on:.3f}/day -- the switch "
        f"{'EXISTS' if on > off == 0 else 'DOES NOT WORK'}")
    n += 1
    check(on > off == 0,
          "a class can be correctly SILENT and still be built: FAC-13 says "
          "the spec 'carries the OFF state at datum with the switch existing'",
          f"{off} off, {on:.3f} on")

    # -- the step size ---------------------------------------------------
    _wc, fc = headless_day(Ctx(day=1, seed=seed), step_min=step_min * 4.0)
    rel = abs(len(fc) - len(fd)) / max(1, len(fd))
    out(f"  at 4x the step ({step_min * 4:.0f} min), over the same "
        f"station-day: {len(fc)} incidents against {len(fd)} -- "
        f"{rel * 100:.1f}% apart")
    n += 1
    check(rel < STEP_TOLERANCE,
          "and the answer does not depend on the step size. The draw is per "
          "STEP rather than one Poisson count for the whole hour precisely so "
          "that this can be MEASURED instead of assumed -- and the tolerance "
          "is set below the 12.4% the coin-flip version scored, so a "
          "regression to it fails here",
          f"{rel * 100:.1f}% at 4x, tolerance {STEP_TOLERANCE * 100:.0f}%")

    # -- the endogenous control ------------------------------------------
    _WORLD_HEAT.clear()
    _WORLD_SICKHOMES.clear()
    _WORLD_GRIEVANCE[0] = 0.0
    _WORLD_DEBTORS[0] = 0
    _WORLD_ELEV_DOWN[0] = False
    endo_cold = {k.cid: class_rate_day(Ctx(day=1, seed=seed), k.cid)
                 for k in CLASSES if k.endogenous}
    _WORLD_HEAT.update(w1.heat)
    _WORLD_SICKHOMES.update(w1.sickhomes)
    _WORLD_GRIEVANCE[0] = w1.grievance
    _WORLD_DEBTORS[0] = w1.debtors
    _WORLD_ELEV_DOWN[0] = w1.elev_down
    endo_warm = {k.cid: class_rate_day(Ctx(day=1, seed=seed), k.cid)
                 for k in CLASSES if k.endogenous}
    woke = [c for c in endo_cold if endo_warm[c] > endo_cold[c] == 0.0]
    out(f"  {len(endo_cold)} CLASSES ARE ENDOGENOUS. In a world nothing has "
        f"happened in yet their rates are "
        f"{[f'{c} {v:.3f}' for c, v in endo_cold.items()]}"
        f"; after day 1 wrote camp heat on {len(w1.heat)} place(s), "
        f"{w1.debtors} debtor(s), a {w1.grievance:+.1f} grievance board and "
        f"{sum(w1.sickhomes.values()):.0f} household(s) with a stopped earner "
        f"in {len(w1.sickhomes)} block(s) "
        f"they are {[f'{c} {v:.3f}' for c, v in endo_warm.items()]}")
    n += 1
    check(len(woke) >= 1,
          "AND THE WORLD FEEDS THE GENERATOR: at least one class has a rate "
          "of EXACTLY ZERO in a world nothing has happened in and a non-zero "
          "rate after a day of other classes writing into it. That is the "
          "difference between a schedule of events and a simulation",
          f"{woke} woke up; heat on {len(w1.heat)} place(s), "
          f"{w1.debtors} debtors, grievance {w1.grievance:+.1f}")

    # ------------------------------------------------------------------
    # G.  THE LIVED-IN HALF -- what a player standing at home actually sees
    # ------------------------------------------------------------------
    out("")
    out("THE LIVED-IN HALF -- the same measurement with the eight new classes "
        "SUBTRACTED, which is the before, and with them, which is the after:")
    out(f"  {'district':10s} {'before mean':>11s} {'after mean':>11s} "
        f"{'before best':>11s} {'after best':>11s}  cleared")
    moved = {}
    for name in ("home", "camp", "commerce", "civic", "medical", "arrival"):
        b_m, b_b, b_c, cnt = district_rate(ctx, name, hour,
                                           only=set(CRIME_ORIGINAL))
        a_m, a_b, a_c, _ = district_rate(ctx, name, hour)
        moved[name] = (b_m, a_m, b_b, a_b, b_c, a_c, cnt)
        out(f"  {name:10s} {b_m:11.4f} {a_m:11.4f} {b_b:11.4f} {a_b:11.4f}  "
            f"{b_c} -> {a_c} of {cnt}")
    # WHICH CLASSES COULD HAPPEN IN A HOME AT ALL -- at the PLACE, not at its
    # probe, because a probe is the place plus its adjacent rows and several
    # residence rows are adjacent to something busy. This is the sharper
    # statement and it is the one that can fail: before this session exactly
    # ONE of the twenty-two could fire in a home, and it was a machine.
    def _cids(only):
        s = set()
        for p in dr.PLACES:
            if district_of(p["key"]) != "home":
                continue
            for k, r in live_classes(ctx, p["key"], hour):
                if r > 0.0 and (only is None or k.cid in only):
                    s.add(k.cid)
        return s
    was = _cids(set(CRIME_ORIGINAL))
    now = _cids(None)
    out(f"  classes that can fire in a RESIDENCE at all: before {sorted(was)}, "
        f"after {sorted(now)}")
    n += 1
    # NOT LITERALLY ONE, AND THE GATE CAUGHT THE OVERCLAIM. The first version
    # of this assertion said the before-set was exactly {INC-FAULT} and it
    # failed on INC-DUST -- which reaches `alien_sector` because
    # `security.BLACK_MARKET_ROUTE` runs through it. Both are still NON-DOMESTIC:
    # a fitting wearing out, and a smuggling route that happens to cross a
    # residential deck. The claim is about what a home could produce BECAUSE
    # SOMEBODY LIVES IN IT, and the honest form of it is a named pair.
    NON_DOMESTIC = {"INC-FAULT", "INC-DUST"}
    check(was <= NON_DOMESTIC and len(now - was) >= 4,
          "AND THE SHAPE OF THE BEFORE IS THE FINDING. Only TWO of the "
          "original twenty-two could fire in a home -- a machine breaking, "
          "and the black-market route crossing the Alien Sector -- and "
          "neither of them happens because somebody LIVES there. That is not "
          "six missing offences, it is a missing half, and the control is the "
          "subtraction: the same call, the same places, the same hour, with "
          "the eight new rows left out of the sum",
          f"before {sorted(was)}, after {sorted(now)}")
    n += 1
    check(moved["home"][1] > moved["home"][0] > 0.0,
          "...and the residential probe rate rises with them",
          f"{moved['home'][0]:.4f}/h before, {moved['home'][1]:.4f}/h after")
    # WHY THE HOMES STILL DO NOT CLEAR SYS-14's FLOOR, in arithmetic rather
    # than in apology. It is printed rather than asserted because it is a
    # finding about the FLOOR and not about the generator.
    ref = "qtr_civilian"
    ru = units_in(ref)
    rbest = max(expected_rate(ctx, Probe(ref), float(h))[0] for h in range(24))
    out(f"  AND WHY THE HOMES DO NOT CLEAR THE FLOOR, in arithmetic: "
        f"{ref} is {ru} built households, so SYS-14's >=2/station-hour is "
        f"{2 * 24 / ru:.3f} incidents per household per day -- **one thing "
        f"going wrong in every flat every {ru / 48.0:.1f} days**. This runs it "
        f"at {rbest:.3f}/h at its own busiest hour, which is one per household "
        f"per {ru / (rbest * 24.0):.0f} days. The floor is a PORT's number: "
        f"the places that clear it move 55 ships or 39,262 people a day. A "
        f"generator that made a block of flats as eventful as the customs "
        f"hall would be lying, and probe SIZE is not the excuse -- "
        f"core_shuttle and fusion_core clear it with one place")
    n += 1
    check(moved["commerce"][1] > moved["commerce"][0] > 0.0,
          "...and the commercial ring, which was NOT at zero but was quiet, "
          "moves too. It was already carrying theft and denunciation, so the "
          "test here is a strict increase rather than zero-to-something",
          f"{moved['commerce'][0]:.4f} -> {moved['commerce'][1]:.4f}/h mean")
    hrs = [(h, district_rate(ctx, "home", float(h))[1]) for h in (3, 8, 13,
                                                                 19, 22)]
    out("  a home's own clock, best residential probe by hour: "
        + ", ".join(f"{h:02d}:00 {v:.3f}/h" for h, v in hrs))
    n += 1
    check(max(v for _h, v in hrs) > 2.0 * min(v for _h, v in hrs),
          "AND A HOME HAS AN HOUR. The residential rate has to MOVE over the "
          "day or it is a constant with a place attached -- it peaks when "
          "people are in and the species clocks disagree, which is the night, "
          "not the afternoon",
          str([(h, round(v, 4)) for h, v in hrs]))

    # -- the framing, counted rather than claimed ------------------------
    old_brig = [c for c in CRIME_ORIGINAL if books_custody(c, hour=hour,
                                                           seed=seed)]
    new_brig = [c for c in LIVED_IN if books_custody(c, hour=hour, seed=seed)]
    out(f"  ORDINARY LIFE IS NOT A CRIME, counted: of the original "
        f"{len(CRIME_ORIGINAL)} classes, {len(old_brig)} book somebody into "
        f"the brig in the ABSENT branch -- what the station does when nobody "
        f"is watching -- and of the {len(LIVED_IN)} new ones, "
        f"{len(new_brig)} do. {old_brig}")
    n += 1
    check(not new_brig,
          "NOT ONE of the eight new classes puts a person in custody when the "
          "player is absent. Six more offences bolted onto a residential "
          "corridor would have made the station a crime simulator with flats "
          "in it; this is the assertion that says it did not happen, and it "
          "can fail the moment somebody adds an arrest to an absent branch",
          f"{new_brig} book custody with nobody watching")

    # -- the sealed quarter, which is a control the register supplies -----
    sealed = [p["key"] for p in dr.PLACES
              if district_of(p["key"]) in ("home", "camp")
              and peak_occupancy(p["key"]) <= 0.0]
    if sealed:
        # THE PLACE, NOT ITS PROBE, and only the domestic classes. A probe is
        # the place PLUS its adjacent rows, and `markab_quarter` is adjacent to
        # `alien_sector` -- so a probe-level assertion here would be measuring
        # the neighbours. And INC-FAULT fires in a sealed room legitimately:
        # 60 units of unpowered fittings still age.
        dom = set(LIVED_IN)
        sl = [(k, units_in(k), sum(r for kk, r in live_classes(ctx, k, hour)
                                   if kk.cid in dom)) for k in sealed]
        out("  THE SEALED QUARTER IS THE FREE CONTROL: "
            + "; ".join(f"{k} has {u} built units and {r:.4f}/h of domestic "
                        f"incident" for k, u, r in sl))
        n += 1
        check(all(r == 0.0 for _k, _u, r in sl),
              "a residence with units and NO RESIDENTS runs at exactly zero. "
              "Every domestic rate here is per HOUSEHOLD PRESENT rather than "
              "per unit built, so the sealed Markab quarter -- 60 units, a "
              "dead species, an era consequence the register already carries "
              "-- cannot generate a dispute, a lockout or a rent notice. A "
              "class that used the unit count would fire in an empty tomb",
              str(sl))

    # -- the era, on a rate that MOVES rather than a switch ---------------
    stray_e = class_rate_day(early, "INC-STRAY")
    stray_l = class_rate_day(late, "INC-STRAY")
    out(f"  and the era MOVES a rate rather than switching it: INC-STRAY runs "
        f"at {stray_e:.1f}/day at S2E01 against {stray_l:.1f}/day at the "
        f"datum ({100.0 * (stray_l / max(1e-9, stray_e) - 1.0):+.1f}%), "
        f"because {int(child_heads(late.datum) - child_heads(early.datum))} "
        f"of the station's {int(child_heads(late.datum))} children are "
        f"refugee children and there is no Narn refugee population before "
        f"narn_surrender (2,20)")
    n += 1
    check(0.0 < stray_e < stray_l,
          "THE ERA IS A WEIGHT AND NOT ONLY A SWITCH. INC-DENOUNCE proves the "
          "binary case; this proves the graded one -- a class nothing "
          "era-gates whose rate still steps when an episode lands, because "
          "the population it draws from steps. A rate that could not move "
          "would mean the era reaches the class list and not the arithmetic",
          f"{stray_e:.3f}/day at S2E01 against {stray_l:.3f}/day")

    # -- the endogenous chain the price table forced ---------------------
    _rent = rent_week_cr("qtr_transient")
    _food = weekly_subsistence_cr() - _rent
    _wage = ec.casual_constraint()[0]
    out(f"  INC-ARREARS IS ENDOGENOUS ON INC-SICK AND economy.py DECIDED "
        f"THAT: a week's cheapest tenancy is {_rent:.1f} cr = "
        f"{_rent / _wage:.2f} days of casual labour, and a week's food is "
        f"{_food:.1f} cr = {_food / _wage:.2f} days. Rent is a fifth of the "
        f"food bill, so no working household falls behind and the class can "
        f"only fire off a stopped earner")
    # AND THE RUNG LADDER MAKES THAT CHAIN NEARLY INERT, WHICH IS CONTENT.
    rented = {k: v for k, v in w1.sickhomes.items() if k in tenancy_places()}
    out(f"  ...and it is THIN BY CONSTRUCTION, which is the more interesting "
        f"half: day 1 stopped {sum(w1.sickhomes.values()):.0f} earners and "
        f"{sum(rented.values()):.0f} of them live somewhere that charges "
        f"rent. The households that lose an earner are the ones "
        f"consequence.admits turns away from a medlab -- SANCTUARY and "
        f"NO_STATUS -- and LAW-CRIME 7.1 prices their housing at 0 cr, "
        f"'and it is why people are there'. THE SAME RUNG THAT DENIES YOU A "
        f"BED MEANS YOU CANNOT BE EVICTED. "
        + str({k: round(v) for k, v in sorted(w1.sickhomes.items())}))
    n += 1
    check(sum(w1.sickhomes.values()) > 0.0
          and sum(rented.values()) < 0.5 * sum(w1.sickhomes.values()),
          "the illness -> arrears chain exists AND most of it cannot bite, "
          "because the rung that keeps you out of a medlab also keeps you out "
          "of a tenancy. If this ever inverted it would mean the rung ladder "
          "had stopped reaching the housing model",
          f"{sum(rented.values()):.0f} of {sum(w1.sickhomes.values()):.0f} "
          f"stopped earners are in rented housing")
    n += 1
    check(rent_week_cr("qtr_transient") * 4.0 < weekly_subsistence_cr()
          - rent_week_cr("qtr_transient"),
          "and that is economy.LADDER's arithmetic rather than a design "
          "decision: food costs more than four times rent at the bottom of "
          "the ladder, which is why INC-ARREARS carries no rate of its own",
          f"rent {rent_week_cr('qtr_transient'):.1f} cr against food "
          f"{weekly_subsistence_cr() - rent_week_cr('qtr_transient'):.1f} cr")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


def _selftest(out=print):                                       # noqa: C901
    """Everything answerable without simulating anything."""
    del _FAILED[:]
    n = 0
    n += 1
    check(len(CLASSES) == len(BY_ID) == len(spec_ids(SPEC_PLACES)),
          "the class table is the spec's, with no duplicate ids -- and the "
          "count comes from the spec rather than from a literal here",
          f"{len(CLASSES)} rows, {len(BY_ID)} ids, "
          f"{len(spec_ids(SPEC_PLACES))} spec rows")
    n += 1
    check(spec_ids(SPEC_PLACES) == spec_ids(SPEC_SYSTEMS) == set(BY_ID),
          "the two spec files and this table are one list",
          f"{len(spec_ids(SPEC_PLACES))}/{len(spec_ids(SPEC_SYSTEMS))}/"
          f"{len(BY_ID)}")
    n += 1
    bad = [k.cid for k in CLASSES if not k.places()]
    check(not bad, "every class has at least one register place it can happen "
                   "in, resolved through directory.PLACES", str(bad))
    n += 1
    check(all(len(k.beats) >= 3 for k in CLASSES),
          "every class carries SYS-14's own escalation beats",
          str([k.cid for k in CLASSES if len(k.beats) < 3]))
    n += 1
    p = Probe("zocalo")
    check(p.places[0] == "zocalo" and len(p.places) == 3 and p.span_m > 100.0,
          "the probe volume is the register's adjacency, fixed, and its "
          "metric span is REPORTED rather than chosen",
          f"{p.places} spanning {p.span_m:.0f} m")
    n += 1
    check(abs(distance_m("zocalo", "zocalo")) < 1e-9,
          "a place is zero metres from itself, so the geometry is a metric")
    n += 1
    share = maint_load_share()
    check(0.001 < share < 1.0 and MACHINE_MTBF_DAYS > implied_mtbf_days(),
          "INV-350's SANITY CHECK, WHICH REFUTED THE FIRST DRAFT OF IT: the "
          "visible fault load must sit INSIDE what the maintenance roster can "
          "close. Above 1.0 the station breaks faster than it is fixed; the "
          "first draft used 357 interactable TYPES as the machine count and "
          "implied a 0.04-day MTBF before rooms.bays_in gave the 182,905 "
          "INSTANCES",
          f"{share * 100:.1f}% of capacity, MTBF {MACHINE_MTBF_DAYS:.0f} d "
          f"against a {implied_mtbf_days():.1f} d bound")
    n += 1
    check(machine_instances_total() > 100 * sum(len(q["interacts"])
                                                for q in dr.PLACES),
          "...and the machine count is INSTANCES, not the register's 357 "
          "types -- rooms.bays_in tiles each place's bay along its footprint "
          "and that is what can break",
          f"{machine_instances_total():,} instances")
    n += 1
    check(fr.separation_m("narn", "centauri") > 2.0 * 1.0806 - 0.52,
          "INC-NC rests on friction.py's own arithmetic: the pair wants more "
          "room than a MEASURED ring corridor has",
          f"{fr.separation_m('narn', 'centauri'):.2f} m")
    n += 1
    check(not DRAZI_CYCLE_ON,
          "the Drazi cycle ships OFF, which is PEOPLE.md FAC-13's own state "
          "at the datum")
    n += 1
    check(all(k in ALL_KINDS for k in MEANINGFUL)
          and MEANINGFUL < ALL_KINDS,
          "'meaningful' is a strict subset of the delta kinds -- SYS-14's own "
          "definition is a ledger row, a standing change, a stock movement or "
          "a custody entry, and a news item is none of those")
    n += 1
    w = World()
    try:
        w.fact("vibes", "x", "y")
        ok = False
    except ValueError:
        ok = True
    check(ok, "a fact must be one of the declared delta kinds -- a world that "
              "accepts any string is a log")
    n += 1
    ref, rfd, con, exp, med = card_outcomes()
    check(0.0 < con < 0.1 and 0.0 < ref < 0.3,
          "the customs shares come from arrival.checks' own code path, not "
          "from a constant here",
          f"refused {ref:.3f}, contraband {con:.3f}")
    n += 1
    check(abs(con - (0.01 * (1 - 0.08) + 0.04 * 0.08)) < 0.03,
          "...and the contraband share brackets INV-250's own 1% / 4% split",
          f"{con:.4f}")

    # -- the lived-in half's own denominators, offline -------------------
    n += 1
    hh = [household_size(k) for k in tenancy_places()
          if peak_occupancy(k) > 0.0]
    check(hh and 1.5 < min(hh) and max(hh) < 7.0,
          "INV-380's CROSS-CHECK, and it is two mechanisms that had never "
          "been pointed at each other: rooms.bays_in tiles a bay along a "
          "footprint and populace.occupancy integrates a density curve over "
          "an area, and divided they agree on a HOUSEHOLD. If they did not, "
          "one of the two is wrong about what a residence row is",
          f"{min(hh):.2f}-{max(hh):.2f} people per unit over "
          f"{len(hh)} tenanted blocks")
    n += 1
    check(household_size("downbelow_arch") > 3.0 * min(hh),
          "...and the camps are OVERCROWDED by that same measurement rather "
          "than by an adjective -- downbelow_arch carries 4.7x the people per "
          "unit that an EA block does, which is content the register produced "
          "and nobody had read",
          f"{household_size('downbelow_arch'):.2f} against {min(hh):.2f}")
    n += 1
    sealed = [k for k in home_places() if peak_occupancy(k) <= 0.0]
    check(all(households_home(k, h) == 0.0
              for k in sealed for h in (3.0, 13.0, 22.0)),
          "a residence with built units and no residents is silent at every "
          "hour -- the sealed Markab quarter, which the register carries as "
          "an era consequence and which is therefore a control this file did "
          "not have to write",
          str(sealed))
    n += 1
    share = medical_load_share()
    check(0.0 < share < 1.0
          and admissions_per_day() < presentations_per_day()
          < medical_capacity_per_day(),
          "INV-383's SANITY CHECK, INV-350's shape reused rather than "
          "reinvented: the presentation rate must sit strictly between what "
          "the built beds need and what the medical roster can attend. "
          "Outside that bracket the medlabs are either empty or a queue that "
          "never clears",
          f"{admissions_per_day():.1f} < {presentations_per_day():.1f} < "
          f"{medical_capacity_per_day():,.0f}, {share * 100:.1f}% of capacity")
    n += 1
    check(rent_week_cr("qtr_command") > rent_week_cr("qtr_personnel")
          > rent_week_cr("qtr_transient") > rent_week_cr("downbelow"),
          "rent is MONOTONE down the rung ladder, and it is economy.LADDER "
          "read through consequence.RENT_TIER rather than a second price "
          "table here -- a squat is free, which is LAW-CRIME 7.1's own "
          "sentence for why people are in one",
          str([round(rent_week_cr(k), 1) for k in
               ("qtr_command", "qtr_personnel", "qtr_transient",
                "downbelow")]))
    n += 1
    check(0.0 < child_heads((2, 1)) < child_heads(cos.ERA_DATUM),
          "the child population MOVES with the era: refugee children do not "
          "exist before narn_surrender (2,20) and there are children aboard "
          "either way, so the rate that reads it steps rather than switching",
          f"{child_heads((2, 1)):.0f} at S2E01, "
          f"{child_heads(cos.ERA_DATUM):.0f} at the datum")
    n += 1
    mism = [clock_mismatch(k, 3.0) for k in home_places()]
    check(max(mism) > 0.0 and max(mism) <= 1.0
          and clock_mismatch("qtr_civilian", 3.0)
          > clock_mismatch("qtr_civilian", 19.0),
          "the species clocks disagree MORE at three in the morning than at "
          "seven in the evening, which is schedule.RHYTHMS saying so: every "
          "Narn aboard is asleep at 03:00 and every Centauri is awake",
          f"03:00 {clock_mismatch('qtr_civilian', 3.0):.4f} against 19:00 "
          f"{clock_mismatch('qtr_civilian', 19.0):.4f}")
    n += 1
    check(all(not books_custody(c) for c in LIVED_IN),
          "and NOT ONE of the eight new classes books somebody into the brig "
          "when the player is absent -- the framing claim, counted",
          str([c for c in LIVED_IN if books_custody(c)]))
    if _FAILED:
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"{n - len(_FAILED)}/{n} passed (offline)")
    return not _FAILED


def main(argv=None):                                         # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--day", action="store_true")
    ap.add_argument("--three-ways", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--at", default="customs_north")
    ap.add_argument("--hour", type=float, default=13.0)
    ap.add_argument("--step", type=float, default=STEP_MIN)
    ap.add_argument("--window", type=float, default=WINDOW_MIN)
    ap.add_argument("--seed", default="b5")
    a = ap.parse_args(argv)
    if a.report:
        report(at=a.at, hour=a.hour)
        print("")
        rate_map(Ctx(), a.hour)
        return 0
    if a.three_ways:
        tot = 0
        for k in CLASSES:
            tot += stance_report(k.cid, hour=a.hour, seed=a.seed) == 3
            print("")
        print(f"{tot} of {len(CLASSES)} classes give three distinct worlds")
        return 0
    if a.day:
        ctx = Ctx(day=1, seed=a.seed)
        w, f = headless_day(ctx, step_min=a.step)
        by = {}
        for i in f:
            by[i.cid] = by.get(i.cid, 0) + 1
        print(f"{len(f)} incidents, {len(by)} classes, {len(w.deltas())} "
              f"deltas, {len(w.custody)} in custody")
        for cid, c in sorted(by.items(), key=lambda x: -x[1]):
            print(f"  {cid:14s} {c:5d}")
        return 0
    if a.selftest:
        return 0 if _selftest() else 1
    if a.gate or not any((a.report, a.day, a.selftest, a.three_ways)):
        return 0 if gate(at=a.at, hour=a.hour, step_min=a.step,
                         window_min=a.window, seed=a.seed) else 1
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
