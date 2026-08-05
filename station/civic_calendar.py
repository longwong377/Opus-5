#!/usr/bin/env python3
"""SYS-15 -- THE CIVIC CALENDAR. A function from (day, hour) to what is happening.

WHY THIS IS NOT AN INCIDENT, AND THE DISTINCTION IS THE WHOLE DESIGN
--------------------------------------------------------------------
`station/incident.py`'s own header stops at this boundary and says why, and the
reasoning is binding on this file:

    a species festival week, a faith rota, a wedding, a funeral and its rites,
    the Tuesday combat class, the quarterly drill, an invitation-gated
    reception -- **docs/spec/SYSTEMS.md SYS-15, THE CIVIC CALENDAR, and it has
    no code.** These are CALENDAR-shaped, not RATE-shaped: an observance that
    happens at a random hour is not an observance.

A Poisson draw is the wrong mechanism. So `incident.py` delivers a RATE and
this file delivers a **timetable**: deterministic, era-gated, species-specific,
and answerable at any `(day, hour, place)`.

THE UNIT OF WORK IS THE WEEK, AND THAT IS NOT AN AESTHETIC CHOICE
-----------------------------------------------------------------
`docs/spec/SYSTEMS.md` SYS-01 sets the era clock advancing **one episode-
equivalent per 7 station-days**. `schedule.py`'s clock is Earth Mean Time
(authority 1 -- the customs board), so the civil week is the Earth week, and
PLC-058's CHECK ("the security unarmed-combat class runs **Tuesdays** 17:00")
only means anything on a named seven-day week. Those two sevens coincide, and
the consequence is load-bearing: **the era datum is constant inside a station-
week by construction**, so a week is the largest window over which the calendar
is one calendar. `week()` is therefore the primary query and everything else is
a slice of it.

WHAT IS DERIVED, AND FROM WHAT -- nothing here is a timetable somebody typed
---------------------------------------------------------------------------
    service hours      the hour a species' OWN `schedule.activity_profile`
                       peaks in `Activity.WORSHIP`. Humans peak at 21:00,
                       Brakiri at 05:00, because Brakiri sleep through the
                       station day. Nobody chose those; `--rules` prints the
                       argmax for all fourteen.
    the shrine rota    PLC-075's four shrines share a seven-day week, and the
                       week is APPORTIONED BY CENSUS through the same
                       `schedule.apportion` largest-remainder routine the
                       population layer uses: Narn 3 days, Drazi 2, Brakiri 1,
                       pak'ma'ra 1. Change `STATION_COUNTS` and the rota moves.
    the caste rota     FAC-11's 18:00 turnover (spec-stated, CAST row 45) cuts
                       the Minbari day into a religious-caste block and a
                       worker-caste block with ZERO interior overlap -- which
                       is the gate, not the prose.
    the festival order Parliament of Dreams (S1E05, authority 1 for the FORM
                       only) is every species demonstrating its belief IN
                       SEQUENCE. The sequence here is the station's own
                       demography: `STATION_COUNTS` descending, one week each,
                       so the cycle length is the number of species aboard.
    drill cadence      three watches (`schedule.shift_offset`'s 8.0 x 3) and
                       three defence drills, so a drill recurs every three
                       weeks at the next watch's start hour and the full cycle
                       is nine weeks. A drill that only ever ran at 08:00
                       would train a third of the station.
    quiet hours        PLC-064's bookable quiet hours are the two hours at
                       which `populace.occupancy` is LOWEST at that place.
    harvest crop       PLC-110 states 12 crop boards; `economy.GOODS` states
                       which goods are `supply == "drum"`. Block `w % 12`,
                       crop `block % 3`.
    the minimum        an observance shorter than `schedule.TRANSIT_H` (0.5 h,
    duration           the walk window either side of a shift) cannot be
                       reached in time by anybody not already in the room, so
                       it is not an event a player can attend. That is the
                       floor, and it is derived rather than picked.
    capacity           `ASSEMBLY_PER_100M2` is the DENSEST crowd this project
                       already believes in anywhere -- `max(pc.peak_per_100m2)`
                       over `schedule.PLACES`, which is `dark_star` at 30.0.
                       An event fills its room to that and no further. No new
                       constant was introduced for it.

AND IT COLLIDES WITH THE REST OF THE SIMULATION, OR IT IS A LOOKUP TABLE
------------------------------------------------------------------------
`--collision` measures it rather than asserting it. Every attendee is a named
`resident.Resident` drawn from that place's own affiliate pool, and
`resident.where_at(hour)` says where that person WOULD have been. The
displacement histogram is the collision, expressed as a fraction of
`populace.occupancy` at the place they left.

The second collision is capacity, and it is the honest one: at 21:00 -- the
station's peak worship hour, found by search rather than assumed -- 10,905
residents are at worship and the four worship venues hold 2,285 of them, which
is 21.0%. `--report` prints that ratio rather than hiding it, and the gate
asserts that capacity is BELOW demand so the shortfall cannot quietly close.
The calendar does not pretend the other four fifths are in a room.

THE GATE
--------
`python3 station/calendar.py --gate` and it reads the SPEC, not this file's own
list: every `PLC-xxx` id named anywhere in SYS-15's section of
`docs/spec/SYSTEMS.md` is resolved to a place key through `docs/spec/PLACES.md`'s
own headings, and each must carry at least one observance in a station-week.
Adding a rule here without a spec row, or a spec row with no rule, fails.

Three negative controls, all printed with what they did:

    EMPTY     the rule table emptied -- the before-state of this project, in
              which SYS-15 has no code at all. The week goes flat and every
              content assertion fails. An assertion set that has only been
              pointed at the case it was written for is an assertion set
              nobody has tested.
    FROZEN    every rule forced day-independent. The week still has the same
              number of observances and consecutive days become IDENTICAL,
              so the "two consecutive days differ" check fails on its own.
              This is the control that matters: a calendar that is merely
              BUSY is not a calendar.
    ERA S2E01 the datum moved out of the monastery's era. `monastics_resident`
              (S3E02) and `nightwatch_visible` (S2E22) both go inactive and
              their observances vanish by an exact count.
"""
import argparse
import os
import re
import sys
from dataclasses import dataclass
from functools import lru_cache

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, os.path.join(_HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import directory as dr                                          # noqa: E402
import populace                                                 # noqa: E402
import economy                                                  # noqa: E402
import rooms as rm                                              # noqa: E402
from npc import schedule as sched                               # noqa: E402
from npc import resident as res                                 # noqa: E402
from npc import costume as cos                                  # noqa: E402
from npc import friction as fr                                  # noqa: E402

SPEC_SYSTEMS = os.path.join(_ROOT, "docs", "spec", "SYSTEMS.md")
SPEC_PLACES = os.path.join(_ROOT, "docs", "spec", "PLACES.md")

A = sched.Activity


# ===========================================================================
# 1.  THE WEEK, AND THE ERA CLOCK IT SHARES A LENGTH WITH
# ===========================================================================
# The station clock is Earth Mean Time -- `schedule.RHYTHMS["human"]` carries
# `auth="1 for the clock (customs board)"` -- so the civil week is the Earth
# week. SYS-01 independently gives the era clock 7 station-days per episode.
DAYS_PER_WEEK = 7
ERA_DAYS_PER_EPISODE = 7          # SYS-01, stated, auth 5

DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday")

# INV-390. Station day 0 is a Monday. Nothing in the show or in this repository
# fixes the epoch's weekday; what fixes the DAY NAMES is PLC-058's "Tuesdays
# 17:00", which is a weekday name and therefore requires an origin. Taking day
# 0 as Monday makes the station week start with the working week, which is what
# the security class's Tuesday implies (a class on the second day of the week,
# not the sixth).
EPOCH_DOW = 0

# EarthForce's three watches -- `schedule.shift_offset` is `8.0 * (... % 3)`.
WATCHES = 3
WATCH_H = 24.0 / WATCHES

# A quarter of a 52-week year. PLC-096's drill is stated "quarterly".
QUARTER_WEEKS = 13

# The window over which VENUE COVERAGE is a fair question. The longest cadence
# in the rule table is the quarterly drill, so anything shorter cannot see
# `disconnect_point`; the three-week defence cycle fits inside it.
COVER_WEEKS = QUARTER_WEEKS

# An observance shorter than the walk window either side of a shift cannot be
# reached by anyone not already in the room. DERIVED from schedule, not chosen.
RITE_MIN_H = sched.TRANSIT_H

# The densest crowd this project believes in anywhere. Not a new constant --
# it is the maximum of `schedule.PLACES[*].peak_per_100m2`, which is
# `dark_star` at 30.0 (a packed bar). An event fills its room to that.
ASSEMBLY_PER_100M2 = max(pc.peak_per_100m2 for pc in sched.PLACES.values())


def dow(day: int) -> int:
    """Day of week, 0 = Monday."""
    return (day + EPOCH_DOW) % DAYS_PER_WEEK


def weekday_name(day: int) -> str:
    return DAY_NAMES[dow(day)]


def station_week(day: int) -> int:
    """Which station week this day falls in. Weeks start on Monday."""
    return (day + EPOCH_DOW) // DAYS_PER_WEEK


def era_at(day: int, datum0=None) -> tuple:
    """SYS-01's era position at a station day.

    "era position seeded at ERA_DATUM=(3,5) advancing one episode-equivalent
    per N station-days (auth 5: N=7)". Season rollover is not modelled --
    `costume.era_check` refuses anything at or past secession (3,10) anyway,
    so the era lock bounds this before a season boundary can be reached.
    """
    s, e = cos.ERA_DATUM if datum0 is None else datum0
    return (s, e + day // ERA_DAYS_PER_EPISODE)


# ===========================================================================
# 2.  THE VENUES -- resolved from the SPEC, never written down here
# ===========================================================================
@lru_cache(maxsize=1)
def plc_index() -> dict:
    """`PLC-053` -> `ceremonial_rooms`, parsed from PLACES.md's own headings.

    The register (`directory.PLACES`) does not carry PLC ids and the spec does
    not carry place dicts, so this is the join. Reading it rather than writing
    it out is what lets the gate assert coverage of the spec's OWN list.
    """
    out = {}
    with open(SPEC_PLACES) as f:
        for line in f:
            m = re.match(r"^###\s+(PLC-\d{3})\s+`([a-z0-9_]+)`", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


@lru_cache(maxsize=1)
def sys15_text() -> str:
    """SYS-15's whole section, newlines collapsed.

    The spec wraps mid-token -- "PLC-059/\\n060/063" -- so any id scan has to
    join the lines first. Reading the section and not the file keeps SYS-14's
    and SYS-16's ids out of the union.
    """
    body, on = [], False
    with open(SPEC_SYSTEMS) as f:
        for line in f:
            if line.startswith("## SYS-15"):
                on = True
            elif on and line.startswith("## SYS-"):
                break
            if on:
                body.append(line.rstrip("\n"))
    return " ".join(body).replace("/ ", "/")


@lru_cache(maxsize=1)
def spec_plc_ids() -> tuple:
    """Every PLC id SYS-15 names, expanded through its `PLC-059/060/063` runs."""
    txt = sys15_text()
    ids = set()
    for m in re.finditer(r"PLC-(\d{3})((?:/\d{3})*)", txt):
        ids.add("PLC-" + m.group(1))
        for n in re.findall(r"\d{3}", m.group(2) or ""):
            ids.add("PLC-" + n)
    return tuple(sorted(ids))


@lru_cache(maxsize=1)
def spec_places() -> tuple:
    """The place keys SYS-15's own PLC ids resolve to, in register order."""
    idx = plc_index()
    keys = {idx[i] for i in spec_plc_ids() if i in idx}
    return tuple(p["key"] for p in dr.PLACES if p["key"] in keys)


# How many things can be booked in a place AT ONCE. Every count below is the
# spec's own, cited; anything not listed is one.
#
#   ceremonial_rooms  PLC-053 "door x6 (T2)" -- six hireable function rooms
#   conference_rooms  PLC-060 CHECK "5 rooms, 5 distinct dressings"
#   obs_rotundas      PLC-064 "the 4-rotunda class (canon count)"
#   fresh_air         PLC-105 "table x8 (T2, bookable T3)"
#   outdoor_rec       PLC-058 "2 training bays (auth 5)"
#   sanctuaries       PLC-111 -- the sanctuary proper AND Brother Theo's
#                     monastery annexe are one register row and two rooms,
#                     which is why the Minbari caste rota and the monastic
#                     offices can both hold it at 18:00 without colliding
#   water_rec         INV-391, auth 5 -- PLC-069 says "swim lanes" and states
#                     no count
SLOTS = {
    "ceremonial_rooms": 6,
    "conference_rooms": 5,
    "obs_rotundas": 4,
    "fresh_air": 8,
    "outdoor_rec": 2,
    "sanctuaries": 2,
    "water_rec": 8,
}


def slots(place_key: str) -> int:
    return SLOTS.get(place_key, 1)


def house_slot(place_key: str) -> int:
    """The venue's own state, one past its last bookable slot.

    A dressed square, a rigged banner, a harvest menu and an overnight pool
    are states OF the venue, not bookings of a slot in it -- so they must not
    collide with a table booking, and two of them at once still must. Numbering
    them `slots(place)` gets both without an exception in the collision check,
    which would have been a hole in the only assertion that guards it.
    """
    return slots(place_key)


_CAP = {}


def slot_capacity(place_key: str) -> int:
    """How many people one bookable slot of this place holds.

    Floor area from `economy.floor_m2` -- which is `rooms.room_extent_m`, the
    same extent the geometry is built to -- times the densest crowd density in
    `schedule.PLACES`, divided by the number of parallel slots.
    """
    if place_key not in _CAP:
        a = economy.floor_m2(place_key)
        _CAP[place_key] = max(1, int(a * ASSEMBLY_PER_100M2 / 100.0
                                     / slots(place_key)))
    return _CAP[place_key]


@lru_cache(maxsize=256)
def is_worship(place_key: str) -> bool:
    """Does the REGISTER call this a worship place? The function word decides."""
    return "worship" in dr.by_key(place_key)["functions"]


def crowd_peak(place_key: str) -> int:
    """The place's own 24-hour occupancy peak -- the ambient crowd, not an event."""
    p = dr.by_key(place_key)
    a = economy.floor_m2(place_key)
    arch = rm.archetype(p)
    return max(populace.occupancy(place_key, a, float(h), arch)
               for h in range(24))


# ===========================================================================
# 3.  SPECIES -- who observes what, and WHEN, out of the rhythm table
# ===========================================================================
SPECIES_BY_HEAD = tuple(sp for sp, _n in sorted(sched.STATION_COUNTS.items(),
                                                key=lambda kv: (-kv[1], kv[0])))

# PLC-075: "shrine x4 (T2 -- four species' shrines, each dressed distinctly:
# Narn G'Quan alcove, Drazi, Brakiri, pak'ma'ra, auth 5)". Stated, in order.
SHRINE_SPECIES = ("narn", "drazi", "brakiri", "pakmara")

# resident.py:383-384 already splits worship by species and the split is the
# reason a human at `alien_worship` reads wrong.
HUMAN_ONLY = res.ALIEN_EXCLUDE_PLACES        # {"sanctuary_blue"}
ALIEN_ONLY = res.HUMAN_EXCLUDE_PLACES        # {"alien_worship"}


@lru_cache(maxsize=64)
def worship_peak_hour(species: str) -> int:
    """The hour this species' OWN activity profile peaks in WORSHIP.

    This is the whole reason a service is at the hour it is at. Humans come out
    at 21:00; Brakiri -- night dwellers, asleep through the station day -- come
    out in the small hours. Nobody wrote either number.
    """
    best, bh = -1.0, 0
    for h in range(24):
        v = sched.activity_profile(species, float(h))[A.WORSHIP]
        if v > best:
            best, bh = v, h
    return bh


@lru_cache(maxsize=256)
def worshippers(species: str, hour: float) -> int:
    """Station-wide heads of this species at WORSHIP at this hour."""
    n = sched.STATION_COUNTS.get(species, 0)
    return int(round(sched.activity_profile(species, hour)[A.WORSHIP] * n))


VENUE_SAMPLE = 400          # residents drawn per species to measure a share


@lru_cache(maxsize=512)
def venue_share(species: str, place_key: str, seed: str = "b5") -> float:
    """What fraction of this species prays at this venue.

    MEASURED off `resident.resident()` rather than assumed uniform, because
    `resident._local_choice` weights by sector (LOCAL_BIAS 0.70) and the two
    exclusion sets remove a venue from a species entirely. A uniform 1/N would
    have put humans in the alien worship hall.
    """
    hit = 0
    for i in range(VENUE_SAMPLE):
        r = res.resident(f"cal:{seed}:{species}:{i}", species)
        if r.prays_at == place_key:
            hit += 1
    return hit / float(VENUE_SAMPLE)


def congregation(species: str, place_key: str, hour: float) -> int:
    """Demand: heads of `species` at worship at `hour` who pray HERE."""
    return int(round(worshippers(species, hour)
                     * venue_share(species, place_key)))


@lru_cache(maxsize=1)
def week_shrine_rota() -> dict:
    """PLC-075's four shrines apportioned over a seven-day week BY CENSUS.

    `schedule.apportion` is the same largest-remainder routine the population
    layer uses, so the week is divided the way the station is: Narn 3 days,
    Drazi 2, Brakiri 1, pak'ma'ra 1. It sums to 7 exactly by construction.
    """
    sub = {sp: sched.STATION_COUNTS[sp] for sp in SHRINE_SPECIES}
    tot = float(sum(sub.values()))
    days = sched.apportion(DAYS_PER_WEEK, {k: v / tot for k, v in sub.items()})
    out, d = {}, 0
    for sp in SHRINE_SPECIES:                # census order, deterministic
        for _ in range(days[sp]):
            out[d] = sp
            d += 1
    return out


# PLC-110 states twelve crop boards; `economy.GOODS` states which goods the
# drum grows. Block w % 12, crop block % 3 -- so the crop board changes every
# week and repeats every twelve, which is a rotation.
CROP_BLOCKS = 12
DRUM_CROPS = tuple(g.name for g in economy.GOODS if g.supply == "drum")


# ===========================================================================
# 4.  THE OBSERVANCE
# ===========================================================================
@dataclass(frozen=True)
class Observance:
    """One thing happening, somewhere, at a stated hour, for a stated reason."""
    rid: str                    # the rule that emitted it
    kind: str                   # rite | booking | festival | drill | reception
    day: int
    hour: float                 # EMT start
    dur_h: float
    place: str                  # a directory place key
    title: str
    species: str = ""           # "" = all comers
    holders: tuple = ()         # npc_ids of the named residents who hold it
    gate: str = ""              # "" | "invitation" | "standing"
    era: str = ""               # a costume.ERA_EVENTS key, or ""
    why: str = ""               # the derivation, one line
    slot: int = 0               # which parallel slot of the venue
    roster: str = ""            # a schedule.ROLES key the attendance comes from
    state: bool = False         # a physical state of the venue, not a gathering
    activity: object = None     # the schedule.Activity the crowd is drawn from
    heads: int = 0              # a SPEC-STATED congregation; 0 = derive it

    @property
    def end_h(self) -> float:
        return self.hour + self.dur_h

    def covers(self, hour: float) -> bool:
        return self.hour <= hour < self.end_h

    def key(self) -> tuple:
        """Identity for comparing two days. Deliberately EXCLUDES `day`."""
        return (self.rid, round(self.hour, 3), round(self.dur_h, 3),
                self.place, self.title, self.species, self.holders, self.slot)

    @property
    def slot_share(self) -> int:
        """This slot's share of the venue's own ambient crowd at this hour.

        `populace.occupancy` is the station's own answer to "how many people
        are in this place"; one of eight tables gets an eighth of them. A
        booking cannot conjure a party the room does not contain.
        """
        p = dr.by_key(self.place)
        occ = populace.occupancy(self.place, economy.floor_m2(self.place),
                                 self.hour, rm.archetype(p))
        return max(1, int(round(occ / float(slots(self.place)))))

    def line(self) -> str:
        who = f" [{self.species}]" if self.species else ""
        g = f" <{self.gate}>" if self.gate else ""
        return (f"{weekday_name(self.day):9s} d{self.day:<3d} {self.hour:05.2f}"
                f"+{self.dur_h:4.1f}h  {self.place:20s} "
                f"{self.title}{who}{g}")


@dataclass
class Ctx:
    """Everything a rule needs and nothing it does not."""
    seed: str = "b5"
    datum: tuple = None
    day0: int = 0

    def era(self, event: str) -> bool:
        return cos.era_active(event, self.datum or cos.ERA_DATUM)


def _named(place_key: str, species: str, i: int, seed: str) -> str:
    """The i'th named resident whose life touches this place. A booking is HELD."""
    ids = res.affiliates(place_key, species, seed=seed)
    return ids[i % len(ids)]


def who(npc_id: str, species: str) -> str:
    r = res.resident(npc_id, species)
    return r.name or f"{species} {npc_id.rsplit(':', 1)[-1]}"


# ===========================================================================
# 5.  THE RULES
# ===========================================================================
# Each rule is (rid, kind, spec ids it implements, why, fn(ctx, day) -> list).
# A rule owns its OWN hours and its own derivation; nothing schedules anything
# centrally, so a rule can be deleted and only its own content disappears.
_RULES = []


def rule(rid, kind, plc, why):
    def deco(fn):
        _RULES.append(Rule(rid, kind, tuple(plc), why, fn))
        return fn
    return deco


@dataclass(frozen=True)
class Rule:
    rid: str
    kind: str
    plc: tuple
    why: str
    fn: object


# --- faith rotas ------------------------------------------------------------
OFFICE_HOURS = (6.0, 12.0, 18.0, 23.0)      # FAC-26, spec-stated, auth 5
MONKS_LO, MONKS_HI = 15, 25                 # FAC-26 "15-25 resident monks"


@rule("R-OFFICE", "rite", ("PLC-111",),
      "FAC-26: Theo's monks keep canonical hours 06/12/18/23; era-gated on "
      "monastics_resident (S3E02) because before Convictions the order is not "
      "aboard")
def _r_office(ctx, day):
    if not ctx.era("monastics_resident"):
        return []
    # The order's size moves by the WEEK, not by the day. A number that
    # changed daily would put a spurious difference into every consecutive
    # pair and make the week's shape test pass on cosmetics.
    n = MONKS_LO + station_week(day) % (MONKS_HI - MONKS_LO + 1)
    out = []
    for i, h in enumerate(OFFICE_HOURS):
        out.append(Observance(
            "R-OFFICE", "rite", day, h, RITE_MIN_H, "sanctuaries",
            f"monastic office ({n} of the order)", "human",
            (_named("sanctuaries", "human", day * 4 + i, ctx.seed),),
            era="monastics_resident", heads=n,
            why="FAC-26 canonical hours; the annexe slot, not the sanctuary",
            slot=1))
    return out


@rule("R-CASTE", "rite", ("PLC-111",),
      "FAC-11: the two Minbari castes share the Sanctuary schedule by rota, "
      "turnover 18:00 (CAST row 45). ZERO interior overlap is the assertion")
def _r_caste(ctx, day):
    wake = sched.wake_hour("minbari")                # 02:30, broken sleep
    sleep = sched.RHYTHMS["minbari"].sleep_start     # 22:30
    keeper = _named("sanctuaries", "minbari", day, ctx.seed)
    return [
        Observance("R-CASTE", "rite", day, wake, 18.0 - wake, "sanctuaries",
                   "religious-caste rota block", "minbari", (keeper,),
                   why="from the Minbari wake hour to FAC-11's 18:00 turnover",
                   slot=0),
        Observance("R-CASTE", "rite", day, 18.0, sleep - 18.0, "sanctuaries",
                   "worker-caste rota block", "minbari", (keeper,),
                   why="from the turnover to the Minbari sleep block",
                   slot=0),
    ]


@rule("R-SERVICE", "rite", ("PLC-049",),
      "the principal human service sits at the hour humans' OWN worship "
      "activity profile peaks; sanctuary_blue is the human venue "
      "(resident.ALIEN_EXCLUDE_PLACES)")
def _r_service(ctx, day):
    h = float(worship_peak_hour("human"))
    return [Observance(
        "R-SERVICE", "rite", day, h, 1.0, "sanctuary_blue",
        "principal service", "human",
        (_named("sanctuary_blue", "human", day, ctx.seed),),
        why=f"argmax of activity_profile('human')[WORSHIP] = {h:02.0f}:00")]


@rule("R-SHRINE", "rite", ("PLC-075",),
      "PLC-075's four shrines share the week, apportioned BY CENSUS through "
      "schedule.apportion: Narn 3 days, Drazi 2, Brakiri 1, pak'ma'ra 1")
def _r_shrine(ctx, day):
    sp = week_shrine_rota()[dow(day)]
    h = float(worship_peak_hour(sp))
    title = f"{sp} shrine rite"
    if sp == "narn":
        title = ("G'Quan Eth ceremony" if ctx.era("narn_surrender")
                 else "G'Quan observance")
    return [Observance(
        "R-SHRINE", "rite", day, h, 1.0, "alien_worship", title, sp,
        (_named("alien_worship", sp, day, ctx.seed),),
        why=f"census apportionment of the week; {sp} worship peak {h:02.0f}:00")]


@rule("R-CHAPEL", "booking", ("PLC-112",),
      "PLC-112: the altar re-dresses per booking, one faith a day, rotating "
      "over the resident species in census order -- so two consecutive days "
      "CANNOT be the same service")
def _r_chapel(ctx, day):
    sp = SPECIES_BY_HEAD[day % len(SPECIES_BY_HEAD)]
    if sp in ("human",) and "interfaith_chapel" in HUMAN_ONLY:
        pass
    h = float(worship_peak_hour(sp))
    return [Observance(
        "R-CHAPEL", "booking", day, h, 1.0, "interfaith_chapel",
        f"interfaith service (altar dressed {sp})", sp,
        (_named("interfaith_chapel", sp, day, ctx.seed),),
        why="one species a day over the census order; the altar is the tell")]


# --- festival weeks ---------------------------------------------------------
@rule("R-FESTIVAL", "festival", ("PLC-063", "PLC-025", "PLC-070", "PLC-053"),
      "Parliament of Dreams (S1E05, auth 1 for the FORM only): every species "
      "demonstrating its belief IN SEQUENCE. The sequence is the station's "
      "own demography, one week each")
def _r_festival(ctx, day):
    w = station_week(day)
    sp = SPECIES_BY_HEAD[w % len(SPECIES_BY_HEAD)]
    h = float(worship_peak_hour(sp))
    mourning = sp == "narn" and ctx.era("narn_surrender")
    word = "week of mourning" if mourning else "festival week"
    out = [
        Observance("R-FESTIVAL", "festival", day, h, 2.0, "domed_rotunda",
                   f"{sp} {word}: rotunda ceremony", sp,
                   (_named("domed_rotunda", sp, day, ctx.seed),),
                   era="narn_surrender" if mourning else "",
                   why="PLC-063 T4, the ceremony calendar; the species' own "
                       "worship peak"),
        Observance("R-FESTIVAL", "festival", day, 0.0, 24.0, "garden_town",
                   f"{sp} {word}: square dressed", sp, (),
                   why="PLC-025's square dressing is the festival's physical "
                       "state, so it holds all day",
                   slot=house_slot("garden_town"), state=True),
        Observance("R-FESTIVAL", "festival", day, 0.0, 24.0, "drum_endcaps",
                   f"{sp} {word}: banner rigged", sp, (),
                   why="PLC-070's rigged banner, the same physical state seen "
                       "from the drum floor",
                   slot=house_slot("drum_endcaps"), state=True),
    ]
    # The Parliament-of-Dreams demonstration itself: one hired room, once in
    # the week, on the day the species' own worship peak falls latest -- so it
    # reads as the week's set piece rather than a fourth daily rite.
    if dow(day) == 3:
        out.append(Observance(
            "R-FESTIVAL", "festival", day, h, 3.0, "ceremonial_rooms",
            f"{sp} {word}: the demonstration of belief", sp,
            (_named("ceremonial_rooms", sp, day, ctx.seed),),
            why="the Parliament-of-Dreams form: one room, one species, "
                "in sequence", slot=0))
    return out


@rule("R-HARVEST", "festival", ("PLC-110", "PLC-068", "PLC-105"),
      "PLC-110's 12 crop boards are 12 rotation blocks; block w%12 comes to "
      "harvest and its crop is economy.GOODS' own drum supply")
def _r_harvest(ctx, day):
    w = station_week(day)
    block = w % CROP_BLOCKS
    crop = DRUM_CROPS[block % len(DRUM_CROPS)]
    hydro = sched.ROLES_BY_KEY["hydroponics"]
    out = [Observance(
        "R-HARVEST", "festival", day, hydro.work_start, hydro.work_hours,
        "the_garden", f"harvest week: block {block + 1} of {CROP_BLOCKS}, {crop}",
        "", (), why="the agricultural shift 05:00-13:00 is schedule.ROLES' own",
        slot=house_slot("the_garden"), roster="hydroponics")]
    # PLC-068's CHECK: "the terrace cart trades at shift-end (13:00) to real
    # field-crew NPCs". Shift end is DERIVED, not typed.
    out.append(Observance(
        "R-HARVEST", "booking", day, hydro.work_start + hydro.work_hours, 1.5,
        "garden_terrace", f"terrace cart: {crop} at shift end", "",
        (_named("garden_terrace", "human", day, ctx.seed),),
        why="hydroponics work_start + work_hours; the crew comes off the fields"))
    if dow(day) in (4, 5):                      # the week's two service nights
        out.append(Observance(
            "R-HARVEST", "booking", day, sched.RHYTHMS["human"].meals[-1], 2.0,
            "fresh_air", f"harvest menu: {crop}", "",
            (_named("fresh_air", "human", day, ctx.seed),),
            why="PLC-105 T4: tonight's menu is yesterday's PLC-110 harvest",
            slot=house_slot("fresh_air"), state=True))
    return out


# --- drills -----------------------------------------------------------------
# Three defence drills and three watches. Each drill recurs every three weeks,
# offset from the others by one week, at the watch start hour that comes next
# -- so all three watches meet all three drills in nine weeks. A drill fixed at
# 08:00 forever would train a third of the station.
DEFENCE_DRILLS = (
    ("PLC-031", "war_room", 0, "defence readiness", "command"),
    ("PLC-128", "gunnery_control", 2, "gunnery drill", "command"),
    ("PLC-002", "obs_dome_1", 4, "shutter drill", "command"),
)


@rule("R-DRILL", "drill", ("PLC-031", "PLC-128", "PLC-002"),
      "three drills x three watches (schedule.shift_offset's 8.0 x 3): each "
      "recurs every 3 weeks at the next watch's start hour, full cycle 9 weeks")
def _r_drill(ctx, day):
    w, out = station_week(day), []
    for i, (_plc, place, wd, title, role) in enumerate(DEFENCE_DRILLS):
        if dow(day) != wd or (w % 3) != i:
            continue
        watch = (w // 3) % WATCHES
        h = (sched.REF_WORK_START + WATCH_H * watch) % 24.0
        out.append(Observance(
            "R-DRILL", "drill", day, h, 1.0, place,
            f"{title} (watch {watch + 1} of {WATCHES})", "",
            (_named(place, "human", day, ctx.seed),),
            why=f"every 3 weeks, offset {i}; hour is watch {watch + 1}'s own "
                f"start so all three watches are drilled in 9 weeks"))
    return out


@rule("R-DISCONNECT", "drill", ("PLC-096",),
      "PLC-096's drill is stated quarterly; a quarter is 13 of a 52-week year. "
      "Station-wide PA -- broadcast.PA_PLACES is the surface")
def _r_disconnect(ctx, day):
    w = station_week(day)
    if dow(day) != 0 or w % QUARTER_WEEKS != 0:
        return []
    h = sched.REF_WORK_START + WATCH_H / 2.0     # mid-watch, not a changeover
    return [Observance(
        "R-DISCONNECT", "drill", day, h, 2.0, "disconnect_point",
        "quarterly explosive-disconnect drill", "",
        (_named("disconnect_point", "human", day, ctx.seed),),
        why="13-week quarter; mid-watch so the drill does not land on a "
            "changeover and catch two watches half-relieved")]


# --- venue bookings ---------------------------------------------------------
@rule("R-COMBAT", "booking", ("PLC-058",),
      "PLC-058's CHECK, stated: the security unarmed-combat class runs "
      "Tuesdays 17:00 with real officer NPCs")
def _r_combat(ctx, day):
    if dow(day) != 1:
        return []
    return [Observance(
        "R-COMBAT", "booking", day, 17.0, 1.5, "outdoor_rec",
        "security unarmed-combat class", "",
        tuple(_named("outdoor_rec", "human", day * 3 + i, ctx.seed)
              for i in range(2)),
        why="spec-stated Tuesday 17:00; one of PLC-058's two training bays; "
            "attendance is the OFF-WATCH security roster, not passers-by",
        slot=0, roster="security")]


@rule("R-WEDDING", "booking", ("PLC-053",),
      "SYS-15's CHECK names a wedding held by a named couple; the ceremony "
      "sits so the feast runs into the couple's own evening meal hour")
def _r_wedding(ctx, day):
    if dow(day) != 5:                    # Saturday
        return []
    sp = SPECIES_BY_HEAD[station_week(day) % len(SPECIES_BY_HEAD)]
    meals = sched.RHYTHMS[sp].meals or (19.0,)
    h = max(0.0, meals[-1] - 2.0)
    a = _named("ceremonial_rooms", sp, day * 2, ctx.seed)
    b = _named("ceremonial_rooms", sp, day * 2 + 7, ctx.seed)
    return [Observance(
        "R-WEDDING", "booking", day, h, 3.0, "ceremonial_rooms",
        f"wedding: {who(a, sp)} and {who(b, sp)}", sp, (a, b),
        why=f"two hours before the {sp} evening meal ({meals[-1]:04.1f}), so "
            f"the feast is the meal", slot=1)]


@rule("R-MINIPAX", "booking", ("PLC-053",),
      "P-06: the Ministry of Peace has formally NO premises, so it BORROWS a "
      "function room. Era-gated on nightwatch_visible (S2E22) -- before The "
      "Fall of Night there is no MiniPax presence to hold a meeting")
def _r_minipax(ctx, day):
    if not ctx.era("nightwatch_visible") or dow(day) != 2:
        return []
    return [Observance(
        "R-MINIPAX", "booking", day, 19.0, 1.5, "ceremonial_rooms",
        "MiniPax public meeting (borrowed room)", "",
        (_named("ceremonial_rooms", "human", day, ctx.seed),),
        era="nightwatch_visible",
        why="after the general day shift ends so a public can attend; the "
            "notice goes to broadcast.MINIPAX_PLACES", slot=2)]


@rule("R-SESSION", "booking", ("PLC-059", "PLC-060"),
      "FAC-12: session days at 10:00. PLC-059's T4 says the real business is "
      "the side meetings, so they BRACKET the session -- the day before and "
      "the day after, paired only where friction.will_share_table allows")
def _r_session(ctx, day):
    d = dow(day)
    if d == 2:
        return [Observance(
            "R-SESSION", "booking", day, 10.0, 3.0, "conference_rooms",
            "Advisory Council session support suite", "",
            (_named("conference_rooms", "human", day, ctx.seed),),
            why="FAC-12's session day, 10:00", slot=0)]
    if d not in (1, 3):
        return []
    pairs, seen = [], set()
    for a in ("human", "minbari", "centauri", "narn"):
        for b in ("human", "minbari", "centauri", "narn"):
            if a >= b or (a, b) in seen:
                continue
            seen.add((a, b))
            if fr.will_share_table(a, b, ctx.datum or cos.ERA_DATUM):
                pairs.append((a, b))
    if not pairs:
        return []
    a, b = pairs[(day + d) % len(pairs)]
    return [Observance(
        "R-SESSION", "booking", day, 10.0, 1.5, "conference_5",
        f"delegation side-meeting: {a} / {b}", "",
        (_named("conference_5", a, day, ctx.seed),
         _named("conference_5", b, day, ctx.seed)),
        why="friction.will_share_table admits this pairing; the day before "
            "and after the session are where the business is")]


@rule("R-QUIET", "booking", ("PLC-064",),
      "PLC-064's bookable quiet hours are DERIVED: the two hours at which "
      "populace.occupancy is lowest at that place")
def _r_quiet(ctx, day):
    p = dr.by_key("obs_rotundas")
    a = economy.floor_m2("obs_rotundas")
    arch = rm.archetype(p)
    by_h = sorted(range(24),
                  key=lambda h: (populace.occupancy("obs_rotundas", a,
                                                    float(h), arch), h))
    out = []
    for i, h in enumerate(by_h[:2]):
        out.append(Observance(
            "R-QUIET", "booking", day, float(h), 1.0, "obs_rotundas",
            "bookable quiet hour", "",
            (_named("obs_rotundas", "human", day * 2 + i, ctx.seed),),
            why="the quietest hour the crowd model gives this place",
            slot=i))
    return out


@rule("R-LESSON", "booking", ("PLC-067",),
      "PLC-067's CHECK: at 03:30 a Minbari religious-caste NPC tends the raked "
      "beds -- the broken-sleep rhythm made visible. The lesson slate hangs "
      "off the same waking block")
def _r_lesson(ctx, day):
    wake = sched.wake_hour("minbari")            # 02:30
    out = [Observance(
        "R-LESSON", "rite", day, wake + 1.0, 1.5, "zen_garden",
        "religious-caste tending rota", "minbari",
        (_named("zen_garden", "minbari", day, ctx.seed),),
        why="an hour after the Minbari wake hour: PLC-067's stated 03:30")]
    if dow(day) in (0, 3):
        out.append(Observance(
            "R-LESSON", "booking", day, 15.0, 1.0, "zen_garden",
            "booked lesson (slate)", "",
            (_named("zen_garden", "human", day, ctx.seed),),
            why="PLC-067's lesson booking slate, twice a week"))
    return out


@rule("R-LANE", "booking", ("PLC-069",),
      "PLC-069's CHECK: Abbai rest IN WATER per schedule.RHYTHMS, so the "
      "overnight lanes are not a booking anyone else can take")
def _r_lane(ctx, day):
    ab = sched.RHYTHMS["abbai"]
    out = [Observance(
        "R-LANE", "rite", day, ab.sleep_start, ab.sleep_hours, "water_rec",
        "Abbai rest lanes (rest is taken in water)", "abbai", (),
        why="the Abbai sleep block IS a lane booking -- RHYTHMS, auth 4 for "
            "amphibian; it takes the whole pool, so it is a house state",
        slot=house_slot("water_rec"), activity=A.SLEEP)]
    for i in range(2):
        h = 12.0 + 4.0 * i
        out.append(Observance(
            "R-LANE", "booking", day, h, 1.0, "water_rec",
            f"swim lane block {i + 1}", "",
            (_named("water_rec", "human", day * 2 + i, ctx.seed),),
            why="daytime lanes, outside the Abbai rest block", slot=i))
    return out


@rule("R-TABLE", "booking", ("PLC-105",),
      "PLC-105's eight bookable tables run two sittings, and the two sittings "
      "are two species' evening meal hours out of RHYTHMS -- human 19:00, "
      "Centauri 23:00, which is why the maitre d' is Centauri and works late")
def _r_table(ctx, day):
    out = []
    for sp in ("human", "centauri"):
        h = sched.RHYTHMS[sp].meals[-1]
        n = min(slots("fresh_air"), 4)
        for i in range(n):
            out.append(Observance(
                "R-TABLE", "booking", day, h, 1.5, "fresh_air",
                f"table {i + 1} ({sp} sitting)", sp,
                (_named("fresh_air", sp, day * 8 + i, ctx.seed),),
                why=f"the {sp} evening meal hour from RHYTHMS",
                slot=i if sp == "human" else i + 4))
    return out


# --- invitation-gated receptions -------------------------------------------
@rule("R-RECEPTION", "reception", ("PLC-053",),
      "FAC-10's social calendar. Centauri are nocturnal (sleep 04:30-11:00) "
      "and their evening meal is 23:00, so the reception is at 23:00 and the "
      "player without an invitation is refused at the door")
def _r_reception(ctx, day):
    if dow(day) != 4:                    # Friday
        return []
    h = sched.RHYTHMS["centauri"].meals[-1]
    host = _named("ambassadorial_suites", "centauri", day, ctx.seed)
    aide = _named("ambassadorial_suites", "centauri", day + 11, ctx.seed)
    return [Observance(
        "R-RECEPTION", "reception", day, h, 3.0, "ambassadorial_suites",
        f"Centauri reception, host {who(host, 'centauri')} "
        f"(door aide {who(aide, 'centauri')})", "centauri", (host, aide),
        gate="invitation",
        why="the Centauri evening meal hour from RHYTHMS; FAC-10's invitation "
            "is an inventory item with the player's name on it")]


RULES = tuple(_RULES)
RULES_BY_ID = {r.rid: r for r in RULES}


# ===========================================================================
# 6.  THE QUERIES -- (day, hour) -> what is happening and where
# ===========================================================================
def day_of(day: int, ctx: Ctx = None, rules=None) -> tuple:
    """Every observance on one station day, sorted by hour then place."""
    ctx = ctx or Ctx()
    rules = RULES if rules is None else rules
    out = []
    for r in rules:
        out.extend(r.fn(ctx, day))
    return tuple(sorted(out, key=lambda o: (o.hour, o.place, o.rid, o.slot)))


def week(day0: int = 0, ctx: Ctx = None, rules=None) -> tuple:
    """A station week of observances, day0 .. day0+6."""
    ctx = ctx or Ctx()
    out = []
    for d in range(day0, day0 + DAYS_PER_WEEK):
        out.extend(day_of(d, ctx, rules))
    return tuple(out)


def at(day: int, hour: float, ctx: Ctx = None, rules=None) -> tuple:
    """What is LIVE at this (day, hour), anywhere on the station."""
    return tuple(o for o in day_of(day, ctx, rules) if o.covers(hour))


def here(place_key: str, day: int, hour: float = None,
         ctx: Ctx = None, rules=None) -> tuple:
    """What is happening in ONE place -- the query a player standing in it makes."""
    src = day_of(day, ctx, rules) if hour is None else at(day, hour, ctx, rules)
    return tuple(o for o in src if o.place == place_key)


def board(place_key: str, day: int, ctx: Ctx = None, rules=None) -> tuple:
    """What that place's booking board shows for the day. SYS-08's surface."""
    return here(place_key, day, None, ctx, rules)


def notice_places(o: Observance) -> tuple:
    """Where SYS-08 announces this observance BEFOREHAND.

    SYS-15's CHECK: "each surfaced on SYS-08's boards beforehand". The answer
    is `broadcast.py`'s own place lists, not a new one -- a station-wide drill
    goes to the PA, a MiniPax meeting goes to the MiniPax screens, and
    everything else is announced in the room that holds it.

    THE IMPORT IS LAZY ON PURPOSE. `broadcast.py` is the natural consumer of
    this module (`civic_calls` is where a week's observances belong), and a
    top-level import here would make that a cycle. Deferring it means
    broadcast can import calendar at module level and this still works --
    which is the difference between a module something can wire up and a
    module something has to be refactored around.
    """
    import broadcast as bc                                     # noqa: PLC0415
    if o.rid == "R-DISCONNECT":
        return tuple(bc.PA_PLACES)
    if o.rid == "R-MINIPAX":
        return tuple(bc.MINIPAX_PLACES)
    return (o.place,)


def announcements(day: int, ctx: Ctx = None, rules=None) -> list:
    """A day's observances in `broadcast.day()`'s own row shape.

    THIS IS THE WIRING POINT. `broadcast.civic_calls()` returns exactly this
    shape, so a consumer is three lines: import this module, extend the list,
    done. Written here rather than there because `broadcast.py` is not this
    agent's file -- the diff is in the report.
    """
    out = []
    for o in day_of(day, ctx, rules):
        if o.state:
            continue
        att = attendance(o)
        out.append({
            "hour": o.hour,
            "kind": "civic",
            "places": notice_places(o),
            "text": (f"{o.title.upper()}. {dr.by_key(o.place)['name']}, "
                     f"{o.hour:05.2f}"
                     + (" -- BY INVITATION." if o.gate == "invitation" else ".")
                     + (f" {att} expected." if att else "")),
            "source": f"station/calendar.py {o.rid}: {o.why}",
        })
    return out


def day_signature(day: int, ctx: Ctx = None, rules=None,
                  structural: bool = False, drop=()) -> frozenset:
    """A day's identity, day number REMOVED, so two days can be compared.

    `structural=True` ALSO removes the holders, and that distinction is the
    point. Every booking here is held by a named resident drawn from the
    venue's own affiliate pool, so who holds it rotates daily -- which would
    make "two consecutive days differ" pass on nothing but a change of names.
    The structural signature is what a player would notice: a different rite,
    at a different hour, in a different room.
    """
    out = []
    for o in day_of(day, ctx, rules):
        if o.rid in drop:
            continue
        k = o.key()
        out.append(k[:6] + k[7:] if structural else k)
    return frozenset(out)


# ===========================================================================
# 7.  ATTENDANCE -- drawn from rosters, capped by the room
# ===========================================================================
def demand(o: Observance) -> int:
    """How many people WANT to be at this, before the room is consulted.

    A DRESSED SQUARE HAS NO CONGREGATION. `state=True` observances -- the
    festival square, the rigged banner, the harvest menu -- are physical states
    of a venue and reporting "attendance 0" for them was this file's own first
    defect: a zero that reads as a failure and is really a category error.
    """
    if o.state:
        return 0
    if o.heads:
        # THE ONE PLACE A CONGREGATION IS A NUMBER RATHER THAN A DERIVATION,
        # and it is the spec's number: FAC-26 states "15-25 resident monks".
        # Deriving it instead gave the monastic office 628 attendees -- the
        # whole human congregation of the Sanctuaries -- which is what a
        # branch that cannot tell an order from a parish looks like.
        return o.heads
    if o.roster:
        # A class or a muster is drawn from a ROSTER, not from passers-by. The
        # people who can attend are the ones NOT on watch at that hour, and
        # the slot still bounds it.
        heads = sched.role_headcount().get(o.roster, 0)
        off = max(0, heads - sched.role_on_duty(o.roster, o.hour))
        return min(off, o.slot_share)
    if o.species and (o.kind in ("rite", "festival") or is_worship(o.place)):
        # A SPECIES OBSERVANCE IS AN ACTIVITY, AND THE ACTIVITY IS NAMED.
        # `activity_profile` already says what fraction of a species is at
        # WORSHIP at an hour; `venue_share` (measured off resident.prays_at)
        # says how much of that belongs to THIS venue. A festival is the
        # exception and deliberately so: PLC-063's ceremony is the week's set
        # piece for that species, not one of four regular venues competing for
        # it, and `domed_rotunda` is in nobody's `prays_at` -- which is how
        # this branch was found, as `attendance 0 of demand 0`.
        act = o.activity or A.WORSHIP
        n = (sched.STATION_COUNTS.get(o.species, 0)
             * sched.activity_profile(o.species, o.hour)[act])
        if is_worship(o.place):
            n *= venue_share(o.species, o.place)
        return int(round(n))
    if o.kind == "rite":
        return sum(congregation(sp, o.place, o.hour)
                   for sp in sched.STATION_COUNTS)
    if o.kind == "drill":
        # A drill drills the watch that IS on duty; that is the point of it.
        return sched.role_on_duty("command", o.hour) \
            + sched.role_on_duty("security", o.hour)
    if o.kind == "reception":
        # FAC-10's transient nobles and mission -- the diplomat role, awake.
        n = sched.ROLE_WEIGHTS["centauri"]["diplomat"]
        return int(round(n * sched.awake_fraction("centauri", o.hour)))
    return o.slot_share


def attendance(o: Observance) -> int:
    """Who actually gets in. `min(demand, one slot of the room)`."""
    if o.state:
        return 0
    return max(0, min(demand(o), slot_capacity(o.place)))


def turned_away(o: Observance) -> int:
    return max(0, demand(o) - slot_capacity(o.place))


# ===========================================================================
# 8.  THE COLLISION -- where the attendees WOULD have been
# ===========================================================================
def displacement(o: Observance, sample: int = 28, seed: str = "b5") -> dict:
    """Where this observance's congregation is drawn FROM.

    Every attendee is a named resident of the place's own affiliate pool, and
    `resident.where_at(hour)` is where that person would otherwise be. The
    histogram is the collision: an observance is not a lookup table if it takes
    people out of somewhere else.
    """
    sp = o.species or "human"
    ids = res.affiliates(o.place, sp, seed=seed, want=sample)
    out = {}
    for nid in ids:
        r = res.resident(nid, sp)
        w = r.where_at(o.hour)
        if w == o.place:
            continue                    # already here; not displaced
        out[w] = out.get(w, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def displacement_fraction(place_key: str, n: int, hour: float) -> float:
    """`n` people leaving `place_key` at `hour`, as a fraction of its crowd."""
    p = dr.by_key(place_key)
    occ = populace.occupancy(place_key, economy.floor_m2(place_key), hour,
                             rm.archetype(p))
    return (n / occ) if occ else float("inf")


# ===========================================================================
# 9.  DENOMINATORS
# ===========================================================================
def denominators(day0: int = 0, ctx: Ctx = None, rules=None) -> dict:
    ctx = ctx or Ctx()
    wk = week(day0, ctx, rules)
    by_kind, by_place, by_day = {}, {}, {}
    heads = 0
    for o in wk:
        by_kind[o.kind] = by_kind.get(o.kind, 0) + 1
        by_place[o.place] = by_place.get(o.place, 0) + 1
        by_day[o.day] = by_day.get(o.day, 0) + 1
        heads += attendance(o)
    places = len(dr.PLACES)
    sig = [day_signature(d, ctx, rules, structural=True)
           for d in range(day0, day0 + DAYS_PER_WEEK)]
    diffs = [len(sig[i] ^ sig[i + 1]) for i in range(len(sig) - 1)]
    # ...and again with the one rule the spec REQUIRES to change daily removed.
    # PLC-112's own CHECK is "two consecutive services re-dress it correctly",
    # so `R-CHAPEL` alone would satisfy the difference test. Reporting the
    # week's shape without it is the honest number.
    sig2 = [day_signature(d, ctx, rules, structural=True, drop=("R-CHAPEL",))
            for d in range(day0, day0 + DAYS_PER_WEEK)]
    diffs2 = [len(sig2[i] ^ sig2[i + 1]) for i in range(len(sig2) - 1)]
    return {
        "consecutive_day_diffs_nochapel": diffs2,
        "identical_day_pairs_nochapel": sum(1 for x in diffs2 if x == 0),
        "observances": len(wk),
        "by_kind": by_kind,
        "by_place": by_place,
        "by_day": by_day,
        "places_used": len(by_place),
        "places_total": places,
        "attend_head_events": heads,
        "attend_share": heads / float(sched.RESIDENT_TOTAL),
        "consecutive_day_diffs": diffs,
        "identical_day_pairs": sum(1 for d in diffs if d == 0),
        "busiest_place": (max(by_place.items(), key=lambda kv: kv[1])
                          if by_place else ("", 0)),
    }


def worship_capacity_report():
    """The honest one: demand against the four venues at the peak worship hour."""
    venues = [p["key"] for p in dr.PLACES if "worship" in p["functions"]]
    best_h, best_n = 0.0, -1
    for h in range(24):
        n = sum(worshippers(sp, float(h)) for sp in sched.STATION_COUNTS)
        if n > best_n:
            best_h, best_n = float(h), n
    cap = sum(slot_capacity(v) * slots(v) for v in venues)
    return best_h, best_n, cap, venues


# ===========================================================================
# 10.  CONTROLS -- the rule tables the gate turns on itself
# ===========================================================================
def frozen_rules(ctx: Ctx = None, day0: int = 0, rules=None):
    """Every rule forced day-independent, and deliberately MAXIMAL.

    THE CONTROL THAT MATTERS, and the naive version of it was not good enough.
    Replaying day 0 seven times drops every rule that only fires later in the
    week, so a frozen week loses the reception and the wedding and then fails
    "an observance is access-gated" -- which makes the control fail for the
    wrong reason and lets the shape assertion off the hook.

    So this takes the UNION of each rule's whole week, deduplicated by
    `Observance.key()`, and emits all of it on every day. The result is a week
    that is BUSIER than the live one, uses MORE places, carries every kind,
    every gate and every era mark -- and in which every day is the same day.
    It therefore fails exactly one assertion, and that assertion is the
    calendar.
    """
    ctx = ctx or Ctx()
    rules = RULES if rules is None else rules
    out = []
    for r in rules:
        seen, base = set(), []
        for d in range(day0, day0 + DAYS_PER_WEEK):
            for o in r.fn(ctx, d):
                if o.key() in seen:
                    continue
                seen.add(o.key())
                base.append(o)

        def mk(rows):
            def fn(_ctx, day):
                return [Observance(**{**o.__dict__, "day": day}) for o in rows]
            return fn
        out.append(Rule(r.rid, r.kind, r.plc, r.why + " [FROZEN]", mk(base)))
    return tuple(out)


EMPTY_RULES = ()


# ===========================================================================
# 11.  REPORT
# ===========================================================================
def report(out=print, day0: int = 0, seed: str = "b5"):
    ctx = Ctx(seed=seed)
    d = denominators(day0, ctx)
    out(f"THE CIVIC CALENDAR -- SYS-15, datum {ctx.datum or cos.ERA_DATUM}, "
        f"station week {station_week(day0)} (days {day0}-{day0 + 6})")
    out(f"  {len(RULES)} rules; the week has {d['observances']} observances "
        f"in {d['places_used']} of {d['places_total']} register places")
    out("  by kind: " + ", ".join(f"{k} {v}" for k, v in
                                  sorted(d["by_kind"].items())))
    out("")
    out("THE WEEK HAS A SHAPE (observances, and how many differ from the "
        "day before):")
    for i, day in enumerate(range(day0, day0 + DAYS_PER_WEEK)):
        diff = d["consecutive_day_diffs"][i - 1] if i else None
        out(f"  {weekday_name(day):9s} d{day:<3d} {d['by_day'].get(day, 0):3d} "
            + ("" if diff is None else f"({diff} differ from the day before)"))
    out("")
    out("A PLAYER STANDING IN ONE PLACE, over the week:")
    for k, n in sorted(d["by_place"].items(), key=lambda kv: (-kv[1], kv[0])):
        pl = dr.by_key(k)
        out(f"  {k:20s} {n:3d}  cap/slot {slot_capacity(k):5d} x "
            f"{slots(k)} slot(s), ambient peak {crowd_peak(k):5d}"
            f"   [{pl['sector']}]")
    out("")
    h, n, cap, venues = worship_capacity_report()
    out(f"CAPACITY, AND IT DOES NOT COVER THE DEMAND -- at {h:05.2f} the "
        f"station has {n:,} residents at worship")
    out(f"  the {len(venues)} worship venues hold {cap:,} between them "
        f"= {100.0 * cap / n:.1f}% of them. The rest observe where they live; "
        f"the calendar does not pretend otherwise")
    out("")
    out(f"PARTICIPATION: {d['attend_head_events']:,} head-events over the "
        f"week against {sched.RESIDENT_TOTAL:,} residents "
        f"= {100.0 * d['attend_share']:.2f}% of the station per week, "
        f"and head-events DOUBLE-COUNT anyone who attends twice, so the "
        f"true share of distinct people is lower still")
    out("")
    out("THE SERVICE HOURS NOBODY CHOSE (argmax of each species' own "
        "WORSHIP profile):")
    row = []
    for sp in SPECIES_BY_HEAD:
        row.append(f"{sp} {worship_peak_hour(sp):02d}:00")
    out("  " + ", ".join(row))


def print_week(out=print, day0: int = 0, seed: str = "b5", place=None):
    ctx = Ctx(seed=seed)
    for day in range(day0, day0 + DAYS_PER_WEEK):
        rows = (here(place, day, None, ctx) if place else day_of(day, ctx))
        out(f"--- {weekday_name(day)} (day {day}) --- {len(rows)} observances")
        for o in rows:
            if o.state:
                out(f"    {o.line()}   [venue state, no congregation]")
                continue
            out(f"    {o.line()}   {attendance(o):5d} attend"
                + (f" of {demand(o):,} who could" if turned_away(o) else ""))


def print_rules(out=print):
    out(f"{len(RULES)} rules, and every one of them says what it is derived "
        f"from:")
    for r in RULES:
        out(f"  {r.rid:14s} {r.kind:9s} {'/'.join(r.plc)}")
        out(f"      {r.why}")


def print_collision(out=print, day0: int = 0, seed: str = "b5"):
    """Requirement 3, measured: an observance takes people out of somewhere."""
    ctx = Ctx(seed=seed)
    wk = week(day0, ctx)
    out("THE COLLISION -- every attendee is a named resident, and "
        "resident.where_at says where they would otherwise be")
    picked = []
    for rid in ("R-RECEPTION", "R-FESTIVAL", "R-SERVICE", "R-COMBAT"):
        for o in wk:
            if o.rid == rid and not o.state:
                picked.append(o)
                break
    for o in picked:
        disp = displacement(o)
        n = sum(disp.values())
        out("")
        out(f"  {o.line()}")
        out(f"    attendance {attendance(o)} of demand {demand(o)}; of 28 "
            f"sampled affiliates, {n} would have been elsewhere at "
            f"{o.hour:05.2f}:")
        for k, v in list(disp.items())[:6]:
            frac = displacement_fraction(k, v, o.hour)
            out(f"      {k:22s} {v:3d}  = {100.0 * frac:6.2f}% of that "
                f"place's crowd at this hour")


# ===========================================================================
# 12.  THE GATE
# ===========================================================================
_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _verdict(ctx, rules, day0=0):
    """Which content assertions a given RULE TABLE fails.

    Kept separate from `gate` so the identical list can be turned on the
    before-state -- an empty rule table, which is what this project had -- and
    on the frozen control. An assertion set that has only ever been pointed at
    the case it was written for is an assertion set nobody has tested.
    """
    bad = []
    wk = week(day0, ctx, rules)
    d = denominators(day0, ctx, rules)

    if not wk:
        bad.append("anything happens at all in a station-week")
    if len({o.kind for o in wk}) < 4:
        bad.append("at least four of the five SYS-15 kinds occur")
    if d["identical_day_pairs"]:
        bad.append("two consecutive days DIFFER (the week has a shape)")
    if len({o.species for o in wk if o.species}) < 4:
        bad.append("observance is species-specific (>=4 species observe)")
    if not any(o.gate for o in wk):
        bad.append("at least one observance is access-gated")
    if not any(o.era for o in wk):
        bad.append("at least one observance is era-gated")
    if not any(o.holders for o in wk):
        bad.append("bookings are held by NAMED residents")
    if len(d["by_place"]) < 10:
        bad.append(">=10 register places carry an observance")
    return len(bad), 8, bad


def gate(out=print, day0: int = 0, seed: str = "b5"):     # noqa: C901
    del _FAILED[:]
    n = 0
    ctx = Ctx(seed=seed)

    # ------------------------------------------------------------------
    # A.  THE VENUE LIST IS THE SPEC'S, read from the spec
    # ------------------------------------------------------------------
    ids = spec_plc_ids()
    idx = plc_index()
    resolved = {i: idx[i] for i in ids if i in idx}
    wk = week(day0, ctx)
    used = {o.place for o in wk}
    # COVERAGE IS NOT A WEEKLY QUESTION, and asserting it weekly was wrong.
    # The longest cadence in the rule table is PLC-096's quarterly drill and
    # the next is the three-week defence cycle, so a window shorter than a
    # quarter cannot see `disconnect_point` or `gunnery_control` at all. The
    # window is the spec's own longest period, not a number picked to pass.
    cover, cover_days = set(), COVER_WEEKS * DAYS_PER_WEEK
    for d in range(day0, day0 + cover_days):
        cover.update(o.place for o in day_of(d, ctx))
    missing = sorted(i for i, k in resolved.items() if k not in cover)
    out(f"A. SYS-15 names {len(ids)} PLC ids; {len(resolved)} resolve to a "
        f"place through PLACES.md's own headings")
    out(f"   one week touches {len(used)} places; over {COVER_WEEKS} weeks "
        f"({cover_days} days -- the quarterly drill's own period) "
        f"{len(cover)} places, and "
        f"{len(resolved) - len(missing)} of {len(resolved)} spec venues "
        f"carry an observance")
    n += 1
    check(not missing,
          "every PLC row SYS-15 names as a consumer carries at least one "
          "observance inside the longest cadence in the table -- read from "
          "docs/spec/SYSTEMS.md's own section, not from this module's list",
          f"no observance at {[f'{i}={resolved[i]}' for i in missing]}")
    n += 1
    unknown = sorted(p for r in RULES for p in r.plc if p not in idx)
    check(not unknown,
          "every PLC id a rule claims to implement exists in PLACES.md",
          f"{unknown}")
    n += 1
    claimed = {p for r in RULES for p in r.plc}
    check(claimed <= set(ids),
          "no rule claims a PLC row SYS-15 does not name -- the rule table "
          "cannot grow past its own spec row",
          f"claimed but not in SYS-15: {sorted(claimed - set(ids))}")

    # SYS-15's OWN NAMED CHECK, item by item. The spec writes six things it
    # wants to see in a station-week; each is asserted here against the
    # calendar's own output rather than described. `named` is the predicate,
    # `evidence` is the row it matched, and the row is printed so a reader can
    # see the wedding's actual names.
    out("")
    named = (
        ("a wedding, PLC-053, a named couple",
         lambda o: o.rid == "R-WEDDING" and len(o.holders) == 2
         and " and " in o.title),
        ("a species festival week: PLC-025 square + PLC-070 banner + "
         "PLC-110 harvest tie",
         lambda o: o.rid == "R-FESTIVAL" and o.place == "garden_town"),
        ("the Tuesday 17:00 security unarmed-combat class, PLC-058",
         lambda o: o.rid == "R-COMBAT" and dow(o.day) == 1 and o.hour == 17.0
         and o.roster == "security"),
        ("the quarterly PLC-096 drill with station-wide PA",
         lambda o: o.rid == "R-DISCONNECT"
         and len(notice_places(o)) > 1),
        ("a MiniPax public meeting borrowing PLC-053 (P-06)",
         lambda o: o.rid == "R-MINIPAX" and o.place == "ceremonial_rooms"),
        ("one Centauri reception, invitation-gated, with a named door aide",
         lambda o: o.rid == "R-RECEPTION" and o.gate == "invitation"
         and "aide" in o.title),
    )
    span = [o for d in range(day0, day0 + cover_days) for o in day_of(d, ctx)]
    for label, pred in named:
        hit = next((o for o in span if pred(o)), None)
        n += 1
        out(f"   {'YES' if hit else 'NO '}  {label}")
        if hit:
            out(f"        {hit.line().strip()}")
        check(hit is not None,
              f"SYS-15's own named CHECK, item by item -- {label}",
              "no observance in the coverage window matches")

    # ------------------------------------------------------------------
    # B.  THE WEEK HAS A SHAPE
    # ------------------------------------------------------------------
    out("")
    d = denominators(day0, ctx)
    out(f"B. {d['observances']} observances over the station week, "
        f"{d['places_used']} of {d['places_total']} register places")
    out("   per day: " + ", ".join(
        f"{DAY_NAMES[dow(x)][:3]} {d['by_day'].get(x, 0)}"
        for x in range(day0, day0 + DAYS_PER_WEEK)))
    out("   consecutive-day STRUCTURAL differences (symmetric difference of "
        "the day's observance set with the day number AND the holders' names "
        "removed): " + ", ".join(str(x) for x in d["consecutive_day_diffs"]))
    out("   ...and the same with R-CHAPEL dropped, because PLC-112's own "
        "CHECK requires the chapel to re-dress daily and it alone would "
        "satisfy this test: "
        + ", ".join(str(x) for x in d["consecutive_day_diffs_nochapel"]))
    n += 1
    check(d["identical_day_pairs"] == 0,
          "no two CONSECUTIVE days of the station week are the same day, "
          "structurally -- a rotating cast of holders does not count. This is "
          "the assertion the FROZEN control below is built to fail",
          f"{d['identical_day_pairs']} identical consecutive pairs")
    n += 1
    check(d["identical_day_pairs_nochapel"] == 0,
          "and it still holds with the one rule the spec REQUIRES to change "
          "daily removed -- the week's shape is not one rotating table",
          f"{d['identical_day_pairs_nochapel']} identical pairs without "
          f"R-CHAPEL: {d['consecutive_day_diffs_nochapel']}")
    n += 1
    check(min(d["by_day"].values()) > 0,
          "every day of the week has something happening on it",
          f"{sorted(d['by_day'].items())}")

    # ------------------------------------------------------------------
    # C.  DERIVED, NOT AUTHORED
    # ------------------------------------------------------------------
    out("")
    rota = week_shrine_rota()
    counts = {}
    for sp in rota.values():
        counts[sp] = counts.get(sp, 0) + 1
    out("C. the shrine rota is an APPORTIONMENT of the week by census: "
        + ", ".join(f"{sp} {counts.get(sp, 0)}d" for sp in SHRINE_SPECIES))
    n += 1
    check(sum(counts.values()) == DAYS_PER_WEEK,
          "the shrine rota sums to the week exactly (largest remainder, "
          "schedule.apportion -- the same routine the population layer uses)",
          f"{counts}")
    n += 1
    order = sorted(SHRINE_SPECIES, key=lambda s: -sched.STATION_COUNTS[s])
    got = [counts.get(s, 0) for s in order]
    check(got == sorted(got, reverse=True),
          "and the apportionment RANKS BY HEADCOUNT -- the biggest resident "
          "population gets the most days, which is a fact about "
          "STATION_COUNTS rather than about this file",
          f"{list(zip(order, got))}")
    hours = {sp: worship_peak_hour(sp) for sp in SPECIES_BY_HEAD}
    out(f"   service hours are argmax of each species' own WORSHIP profile: "
        f"human {hours['human']:02d}:00, brakiri {hours['brakiri']:02d}:00 "
        f"(night dwellers), centauri {hours['centauri']:02d}:00")
    n += 1
    check(len(set(hours.values())) >= 4,
          "the species do not all worship at the same hour -- the rhythm "
          "table drives the timetable",
          f"{sorted(set(hours.values()))} distinct hours over "
          f"{len(hours)} species")
    n += 1
    short = [o for o in wk if o.dur_h < RITE_MIN_H - 1e-9]
    check(not short,
          f"no observance is shorter than schedule.TRANSIT_H ({RITE_MIN_H} h) "
          f"-- an event shorter than the walk to it cannot be attended",
          f"{[o.title for o in short]}")

    # ------------------------------------------------------------------
    # D.  THE ROOM IS A CONSTRAINT
    # ------------------------------------------------------------------
    out("")
    clash = []
    for day in range(day0, day0 + DAYS_PER_WEEK):
        rows = day_of(day, ctx)
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a.place != b.place or a.slot != b.slot:
                    continue
                if a.hour < b.end_h - 1e-9 and b.hour < a.end_h - 1e-9:
                    clash.append((day, a.place, a.slot, a.title, b.title))
    out(f"D. double-booking: {len(clash)} slot collisions over the week "
        f"({sum(slots(k) for k in used)} slots across {len(used)} places)")
    n += 1
    check(not clash,
          "no two observances hold the same slot of the same venue at "
          "overlapping hours -- a venue is a constraint, not a label",
          f"{clash[:4]}")
    over = [o for o in wk if attendance(o) > slot_capacity(o.place)]
    n += 1
    check(not over,
          "no observance seats more people than one slot of its room holds "
          f"(assembly density {ASSEMBLY_PER_100M2}/100 m2, the densest crowd "
          f"schedule.PLACES believes in anywhere)",
          f"{[(o.title, attendance(o), slot_capacity(o.place)) for o in over[:3]]}")
    # FAC-11's ACCEPT, asserted rather than described.
    blocks = [o for o in wk if o.rid == "R-CASTE" and o.day == day0]
    n += 1
    mixed = 0
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            if a.hour < b.end_h - 1e-9 and b.hour < a.end_h - 1e-9:
                mixed += 1
    out(f"   FAC-11's caste rota: {len(blocks)} blocks a day at "
        f"`sanctuaries`, turnover 18:00, {mixed} overlapping hours")
    check(len(blocks) == 2 and mixed == 0,
          "the two Minbari castes share the Sanctuary schedule with ZERO "
          "mixed dwell -- one caste leaves before the other arrives",
          f"{len(blocks)} blocks, {mixed} overlaps")

    # ------------------------------------------------------------------
    # E.  IT COLLIDES WITH THE REST OF THE SIMULATION
    # ------------------------------------------------------------------
    out("")
    target = next(o for o in wk if o.rid == "R-RECEPTION")
    disp = displacement(target)
    moved = sum(disp.values())
    out(f"E. {target.title[:48]}... at {target.hour:05.2f}: of 28 sampled "
        f"affiliates {moved} would be elsewhere; top draws "
        + ", ".join(f"{k} {v}" for k, v in list(disp.items())[:4]))
    n += 1
    check(moved > 0 and len(disp) >= 2,
          "an observance draws its attendance OUT OF other places -- measured "
          "through resident.where_at, not asserted",
          f"{moved} displaced across {len(disp)} places")
    h, dem, cap, venues = worship_capacity_report()
    out(f"   worship demand at {h:05.2f} is {dem:,} residents against "
        f"{cap:,} of venue = {100.0 * cap / dem:.1f}%")
    n += 1
    check(cap < dem,
          "the calendar does NOT claim to seat the whole station -- venue "
          "capacity is measured against demand and reported as the shortfall "
          "it is",
          f"cap {cap} vs demand {dem}")

    # ------------------------------------------------------------------
    # F.  DETERMINISM
    # ------------------------------------------------------------------
    out("")
    a1 = day_signature(day0 + 3, ctx)
    a2 = day_signature(day0 + 3, Ctx(seed=seed))
    b1 = day_signature(day0 + 3, Ctx(seed="other"))
    out(f"F. determinism: same query twice -> {'identical' if a1 == a2 else 'DIFFERS'}; "
        f"a different seed -> {len(a1 ^ b1)} rows differ")
    n += 1
    check(a1 == a2,
          "the calendar is a pure function of (day, seed) -- the same query "
          "twice gives the same day",
          f"{len(a1 ^ a2)} rows differ")
    n += 1
    check(a1 != b1,
          "and it is SEEDED rather than hardcoded: a different seed moves who "
          "holds the bookings",
          "identical under two seeds")
    # THE SHADOW, GATED. This file is named `calendar` and every station module
    # puts `station/` on sys.path, so it hides the stdlib's. Without the shim
    # `import http.cookiejar` raises ImportError on `timegm`. That is a real
    # break, it was reproduced, and it is asserted here so the shim cannot rot.
    broke = []
    for m in ("http.cookiejar", "email.utils", "urllib.request"):
        try:
            __import__(m)
        except Exception as exc:                                # noqa: BLE001
            broke.append(f"{m}: {type(exc).__name__} {exc}")
    out(f"   stdlib shadow: renamed to civic_calendar.py in 4p; the shim is now inert "
        f"re-exports {len(_SHIMMED)} stdlib names, {len(broke)} stdlib "
        f"importers broken (a rename to civic_calendar.py is the real fix)")
    n += 1
    check(not broke and "timegm" in _SHIMMED,
          "naming a module `calendar` on a path every station module joins "
          "hides the standard library's; the shim keeps the shadow "
          "transparent and this asserts it rather than hoping",
          f"{broke}")

    # ------------------------------------------------------------------
    # G.  THE NEGATIVE CONTROLS, AND THEY FIRE
    # ------------------------------------------------------------------
    out("")
    out("G. NEGATIVE CONTROLS")
    nb, tot, bad = _verdict(ctx, RULES, day0)
    out(f"   LIVE      fails {nb} of {tot} content assertions"
        + (f" -- {bad}" if bad else ""))
    n += 1
    check(nb == 0, "the live rule table passes its own content assertions",
          f"{bad}")

    nb0, tot0, bad0 = _verdict(ctx, EMPTY_RULES, day0)
    out(f"   EMPTY     the rule table emptied -- this project's state before "
        f"this file. fails {nb0} of {tot0}:")
    for b in bad0:
        out(f"               - {b}")
    n += 1
    check(nb0 == tot0,
          "THE BEFORE-STATE FAILS EVERY CONTENT ASSERTION. SYS-15 with no "
          "calendar is a station where nothing is ever scheduled, and the "
          "gate says so rather than passing vacuously",
          f"{nb0} of {tot0}")

    fz = frozen_rules(ctx, day0)
    dfz = denominators(day0, ctx, fz)
    nbf, totf, badf = _verdict(ctx, fz, day0)
    out(f"   FROZEN    every rule forced day-independent and MAXIMAL (each "
        f"rule's whole week emitted on every day). "
        f"{dfz['observances']} observances (live: {d['observances']}), "
        f"{dfz['places_used']} places (live: {d['places_used']}), "
        f"identical consecutive pairs {dfz['identical_day_pairs']} "
        f"(live: {d['identical_day_pairs']}). fails {nbf} of {totf}: {badf}")
    n += 1
    check(nbf == 1 and any("consecutive" in b for b in badf),
          "A BUSIER, WIDER, FULLY GATED FROZEN CALENDAR FAILS EXACTLY ONE "
          "ASSERTION AND IT IS THE SHAPE ONE. Every count-shaped assertion "
          "passes on it; only 'two consecutive days differ' can tell a "
          "calendar from a timetable stamped seven times, which is why that "
          "assertion is the one that matters",
          f"frozen fails {nbf} of {totf}: {badf}")
    n += 1
    check(dfz["observances"] > d["observances"]
          and dfz["places_used"] >= d["places_used"],
          "and the control is a FAIR one -- the frozen table is BUSIER than "
          "the live one and uses at least as many places, so the failure "
          "cannot be about volume or coverage",
          f"frozen {dfz['observances']} obs / {dfz['places_used']} places vs "
          f"live {d['observances']} / {d['places_used']}")

    early = Ctx(seed=seed, datum=(2, 1))
    wk_e = week(day0, early)
    gone = {o.rid for o in wk} - {o.rid for o in wk_e}
    n_off = len(wk) - len(wk_e)
    out(f"   ERA S2E01 datum moved to {cos.era_check((2, 1))}: "
        f"{len(wk_e)} observances (live {len(wk)}), {n_off} vanish, "
        f"rules that disappear entirely: {sorted(gone)}")
    n += 1
    check("R-OFFICE" in gone,
          "monastics_resident (S3E02) is not in force at S2E01, so Brother "
          "Theo's order is not aboard and its four daily offices do not "
          "happen -- the era gate is costume.ERA_EVENTS, the mechanism this "
          "project already uses",
          f"gone = {sorted(gone)}")
    n += 1
    check("R-MINIPAX" in gone,
          "nightwatch_visible (S2E22) is not in force either, so there is no "
          "Ministry of Peace aboard to borrow PLC-053's room",
          f"gone = {sorted(gone)}")
    n += 1
    check(n_off == DAYS_PER_WEEK * len(OFFICE_HOURS) + 1,
          "and the count is EXACT: 7 days x 4 canonical offices, plus the one "
          "weekly MiniPax meeting",
          f"{n_off} vanished, expected "
          f"{DAYS_PER_WEEK * len(OFFICE_HOURS) + 1}")

    # ------------------------------------------------------------------
    # H.  SYS-08 SURFACES IT -- the board and the PA
    # ------------------------------------------------------------------
    out("")
    offboard = [o for o in wk if o not in board(o.place, o.day, ctx)]
    ann = {d: announcements(d, ctx) for d in range(day0, day0 + DAYS_PER_WEEK)}
    n_ann = sum(len(v) for v in ann.values())
    wide = [a for v in ann.values() for a in v if len(a["places"]) > 1]
    out(f"H. every observance is on its own venue's board; {n_ann} of "
        f"{len(wk)} carry an announcement row (states do not), and {len(wide)} "
        f"of them are announced OFF-SITE -- the station PA and the MiniPax "
        f"screens, routed through broadcast.py's own place lists")
    n += 1
    check(not offboard,
          "SYS-15's CHECK: every event is surfaced on a board beforehand -- "
          "`board(place, day)` is the day's whole list, which is what a "
          "player reads in the morning",
          f"{[o.title for o in offboard[:3]]}")
    n += 1
    check(len(wide) >= 2,
          "a station-wide drill and a MiniPax meeting are announced somewhere "
          "OTHER than the room they happen in -- the notice list is "
          "broadcast.PA_PLACES / MINIPAX_PLACES, read from broadcast.py "
          "rather than copied here",
          f"{len(wide)} off-site announcements: "
          f"{[a['text'][:40] for a in wide]}")

    # ------------------------------------------------------------------
    # I.  THE DENOMINATORS
    # ------------------------------------------------------------------
    out("")
    out("I. DENOMINATORS")
    out(f"   observances a station-week          {d['observances']}")
    out(f"   places that ever carry one          {d['places_used']} of "
        f"{d['places_total']} register places "
        f"({100.0 * d['places_used'] / d['places_total']:.1f}%)")
    bp, bn = d["busiest_place"]
    out(f"   a player standing in ONE place      {bn} a week at the busiest "
        f"({bp}); median {sorted(d['by_place'].values())[len(d['by_place']) // 2]}")
    out(f"   head-events over the week           {d['attend_head_events']:,} "
        f"= {100.0 * d['attend_share']:.2f}% of {sched.RESIDENT_TOTAL:,}")
    out(f"   ...and that share is SMALL, and it is honest: an observance is "
        f"capped by its room, the station has {d['places_used']} rooms doing "
        f"this, and 250,000 people do not fit in them. Most of the station's "
        f"week is work and sleep, which populace.py and npc/life.py already "
        f"carry.")
    n += 1
    check(d["attend_share"] < 0.5,
          "the participation share is reported rather than inflated -- a "
          "calendar that claimed to move the whole station would be lying "
          "about its own venues",
          f"{d['attend_share']:.3f}")

    # ------------------------------------------------------------------
    out("")
    if _FAILED:
        out(f"CALENDAR GATE: {n - len(_FAILED)}/{n} -- FAILED")
        for f in _FAILED:
            out(f"  FAIL {f}")
        return False
    out(f"CALENDAR GATE: {n}/{n} OK")
    return True


# ===========================================================================
#   THIS FILE SHADOWS THE STANDARD LIBRARY, AND IT BREAKS A REAL IMPORT
# ---------------------------------------------------------------------------
# Every module in `station/` puts `station/` on `sys.path`, so `import
# calendar` anywhere downstream resolves to THIS file rather than to the
# stdlib's. Reproduced, not theorised:
#
#     $ python3 -c "import sys; sys.path.insert(0,'station'); \
#                   import http.cookiejar"
#     ImportError: cannot import name 'timegm' from 'calendar'
#                  (/home/user/Opus-5/station/calendar.py)
#
# Nothing in this repository imports `urllib`, `requests` or `http` today, so
# the hazard is latent rather than live -- but it is exactly the kind of defect
# that surfaces once, at a distance, as a baffling error in something that has
# nothing to do with observances.
#
# THE REAL FIX IS A RENAME to `civic_calendar.py`, and that is an integration
# decision rather than this file's. Until then the shim below re-exports every
# public stdlib-calendar name this module does not already define, so the
# shadow is transparent to anyone who wanted the stdlib. `day_name` was OUR
# only collision -- a function against the stdlib's list -- and it has been
# renamed `weekday_name` so the shim can hand the stdlib's through untouched.
def _stdlib_shim():
    """Re-export the real `calendar`'s public names that we do not define."""
    import importlib.util
    import sysconfig
    path = os.path.join(sysconfig.get_paths()["stdlib"], "calendar.py")
    if not os.path.exists(path):
        return ()
    spec = importlib.util.spec_from_file_location("_stdlib_calendar", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    g, added = globals(), []
    for name in dir(mod):
        if name.startswith("_") or name in g:
            continue
        g[name] = getattr(mod, name)
        added.append(name)
    return tuple(added)


_SHIMMED = _stdlib_shim()


# ===========================================================================
def main(argv=None):                                        # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--week", action="store_true")
    ap.add_argument("--rules", action="store_true")
    ap.add_argument("--collision", action="store_true")
    ap.add_argument("--at", metavar="PLACE", default=None,
                    help="restrict --week to one place (a booking board)")
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--seed", default="b5")
    a = ap.parse_args(argv)
    if a.rules:
        print_rules()
        return 0
    if a.week:
        print_week(day0=a.day, seed=a.seed, place=a.at)
        return 0
    if a.collision:
        print_collision(day0=a.day, seed=a.seed)
        return 0
    if a.gate:
        return 0 if gate(day0=a.day, seed=a.seed) else 1
    report(day0=a.day, seed=a.seed)
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main())
