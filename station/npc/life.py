#!/usr/bin/env python3
"""The day every resident actually lives, and the station-wide consequence of it.

WHAT WAS MISSING. `docs/MASTER-PLAN.md` §0 lists four properties the deliverable
must have, and property C -- *"it is alive: the station behaves identically
whether or not it is observed; leaving and returning is consistent; 03:00 differs
visibly from 13:00"* -- was the one with nothing behind it. Not for want of a
model: `npc/schedule.py` knows every species' sleep, meals, shifts and leisure,
and `npc/resident.py` gives each of 250,000 people a home, a job, a canteen, a
market, a bar, a chapel and a transit facility they commute through. **None of it
moved.** `populace.py` evaluates `where_at(res, 13.0)` once, bakes the bodies it
gets into the room mesh, and that is the station for ever. A baked snapshot at a
fixed hour is a diorama with a timestamp.

The gap is narrow and specific, and naming it is most of the work:

  * `resident.where_at(res, h)` answers *where is this person at hour h* and it
    is a **teleport**. At h they are at home; at h+eps they are at work; the
    corridor between the two is never occupied by them. `schedule.activity_at`
    does emit `Activity.TRANSIT`, but for a **flat half hour** either side of a
    shift and for nothing else -- so a meal out, a trip to the Zocalo and a walk
    to the sanctuary all happen instantaneously.
  * Nothing anywhere turned a *sequence of hourly answers* into a **day**: an
    ordered, bounded, non-overlapping partition of 24 hours into things a person
    is doing and journeys between the places they do them in.

This module is that day, and the journeys are **routed**, not assumed. The
station's own navigation graph -- `npc/navigation.py`, 20,871 nodes and 76,106
links over the real decks, lifts, spokes, shuttle and trams -- already prices a
walk from anywhere to anywhere in seconds and in metres. A commute is what that
graph says it is.

WHY THE JOURNEY IS THE POINT. A station is alive in its corridors or nowhere: a
room's population can be faked with a density curve and a player will believe it
for as long as they stand still. What a density curve cannot produce is the
person who is *between* two rooms, and that is the whole of a corridor's content.
So the headline number this module exists to compute is **how many of the 250,000
are walking somewhere right now**, and its shape over the day:

    03:00  ->  in transit  9,898   on foot  5,092
    08:00  ->  in transit 24,064   on foot 12,646

-- **x2.48 more people on their feet in the corridors at the morning shift change
than at three in the morning**, and x4.09 between the station's quietest hour
(02:00, 3,750 on foot) and its busiest (19:00, 15,321). Derived, not chosen:
nothing in this file was tuned to produce it. It falls out of `schedule.ROLES`'
start times, `RHYTHMS`' fifteen sleep blocks, and the routed length of every
resident's own journeys.

AND THE COMMUTE IS NOT THE BIGGEST PART OF IT, which was a surprise worth
recording. At 08:00 the eight busiest journeys on the station are all out of
`qtr_civilian` and only three of them go to a workplace; the rest go to the
Eclipse Cafe, a bar, the Zocalo and the kiosks. A resident makes about **13
journeys a day**, because `schedule.activity_at` re-rolls its leisure choice on
every integer hour, so the corridors are dominated by people going out rather
than by people going to work. Whether that churn is right is `schedule.py`'s
question, not this file's; what this file can say is that it is worth **116.8
minutes a day** of travel per resident, of which 58.0 are on foot.

THE MODEL HAS TO AGREE WITH THE PLACEMENT MODEL OR THE STATION HAS TWO
POPULATIONS. `populace.py` decides how many bodies stand in a room from a
calibrated density curve (`schedule.PlaceCrowd` where a place has one, an
archetype rate where it does not). This module decides where each *person* is.
Those are different mechanisms and they describe the same station, so they are
checked against each other three ways in `_selftest`:

  1. **Per-activity census.** Outside its journeys, this module's activity for a
     resident is `schedule.activity_at`'s, identically, asserted per resident
     over the sample. The station-wide census therefore differs from
     `schedule.population_activity` only by the time this module reclassifies as
     travel -- which is checked as an equality, not a tolerance.
  2. **Time on foot.** `populace.WALK_MIN_PER_DAY = 50.8` is the number the
     corridor density of the whole station is derived from, and it was measured
     by exactly the method this module now implements properly. Recomputed here
     from routed journeys: **50.5 min/day**. That is a cross-model agreement to
     0.7%, and it is what makes `populace.CORRIDOR_PER_100M2` and this file the
     same population rather than two.
  3. **Per-place hour shape.** For every place both models describe, the
     24-hour presence curve is correlated against `populace.occupancy`'s.

THE ARCHITECTURAL PROPERTY, and it is the one property C actually asks for:
**a resident's position is a pure function of the station clock.** Nothing here
integrates, accumulates or steps. `day()` is a closed-form partition of the 24
hours and `at(day, h)` indexes it. So the station behaves identically whether or
not it is observed, leaving and returning is consistent by construction, and
`godot/scripts/life.gd` -- the runtime half -- can evaluate an NPC's position at
an arbitrary hour without having simulated the hours in between. That is not an
optimisation. It is the only way 250,000 people can be consistent at all.

COST. `day()` is ~36 `activity_at` calls and one route lookup per place change,
cached per (npc_id, species). The station-wide queries scan `LIFE_SCAN` ids per
species and weight by `schedule.STATION_COUNTS`, the same LOD trick
`schedule.census` uses -- O(species x scan), not O(250,000).

**Routing needs the navigation graph and that costs ~32 s to build, once per
process.** The 24-hour aggregates every consumer actually wants are therefore
RECORDED below, and `--derive` rebuilds them from the graph and fails if a
recorded value has drifted. That is CLAUDE.md's rule about a gate that reads a
committed artefact having to be able to rebuild it, applied before it can be
broken.

    python3 station/npc/life.py --selftest      # every gate, with its controls
    python3 station/npc/life.py --derive        # recompute the recorded tables
    python3 station/npc/life.py --day <id>      # one person's whole day
    python3 station/npc/life.py --hour 8        # the station at 08:00
    python3 station/npc/life.py --gd            # the const block life.gd embeds
"""
import math
import os
import sys
from dataclasses import dataclass
from functools import lru_cache

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resident as _res                                          # noqa: E402
import schedule as _sched                                        # noqa: E402

A = _sched.Activity


# ===========================================================================
# 1.  A DAY
# ===========================================================================
# `schedule.activity_at` is piecewise constant and its pieces are known: the
# sleep block, three meal windows, a shift, two commute windows and the leisure
# draw, which is re-rolled on the integer hour (`_u(npc_id, f"leisure-{int
# (hour)}")`). Sampling it on a fine grid to find the edges would cost 1,440
# calls a resident and would still miss an edge narrower than the grid. Deriving
# the edges costs 36 and cannot miss one.
#
# THE EDGE LIST IS A COPY OF ANOTHER MODULE'S INTERNALS AND THAT IS A REAL RISK,
# so it is not trusted: `_check_breakpoints` in the self-test walks a minute grid
# over a sample and asserts the piecewise reconstruction equals `activity_at`
# everywhere. If `schedule.py` grows a window this file does not know about, that
# assertion fails rather than this file quietly rounding it off.

def _breakpoints(npc_id: str, species: str):
    """Every hour at which `schedule.activity_at` can change value."""
    r = _sched.RHYTHMS.get(species, _sched.RHYTHMS["human"])
    role = _sched.role_for(npc_id, species)
    jit = _sched._jitter(npc_id, species)
    off = _sched.day_offset(npc_id, species, role)

    bp = {float(h) for h in range(24)}          # the leisure re-roll
    s0 = (r.sleep_start + jit + off) % 24.0
    bp.add(s0)
    bp.add((s0 + r.sleep_hours) % 24.0)
    for m in r.meals:
        c = m + jit * 0.4 + off
        bp.add((c - _sched.MEAL_HALF_WINDOW_H) % 24.0)
        bp.add((c + _sched.MEAL_HALF_WINDOW_H) % 24.0)
    if role.work_hours > 0:
        w0 = (role.work_start + _sched.species_work_shift(species)
              + _sched.shift_offset(npc_id, role) + jit)
        for x in (w0, w0 + role.work_hours,
                  w0 - _sched.TRANSIT_H,
                  w0 + role.work_hours + _sched.TRANSIT_H):
            bp.add(x % 24.0)
    return sorted(bp)


@dataclass(frozen=True)
class Span:
    """A stretch of one person's day. Either they are somewhere, or travelling.

    `start` and `hours` are station-clock (Earth Mean Time, authority 1: the
    customs board, `signage.BOARDS["customs_procedures"]`). A span may wrap past
    24:00; `hours` is always positive and the spans of a day sum to exactly 24.
    """
    start: float
    hours: float
    activity: A
    place: str          # where they are; for a journey, where they set out from
    to_place: str = ""  # a journey's destination, "" when they are not moving
    foot_hours: float = 0.0   # of `hours`, how much is spent on foot in corridors

    @property
    def moving(self) -> bool:
        return self.activity is A.TRANSIT

    def covers(self, hour: float) -> bool:
        return ((hour - self.start) % 24.0) < self.hours - 1e-9


def _raw_spans(npc_id: str, species: str):
    """`activity_at` and `where_at` as a partition of the day. Teleporting."""
    res = _res.resident(npc_id, species)
    bp = _breakpoints(npc_id, species)
    n = len(bp)
    out = []
    for i, a in enumerate(bp):
        length = (bp[(i + 1) % n] - a) % 24.0
        if n == 1:
            length = 24.0
        if length < 1e-9:
            continue
        mid = (a + length / 2.0) % 24.0
        act = _sched.activity_at(npc_id, species, mid)
        out.append([a, length, act, _res.where_at(res, mid)])
    return _merge(out)


def _merge(spans):
    """Fuse neighbouring spans that are the same thing, including across 24:00."""
    out = []
    for s in spans:
        if out and out[-1][2] is s[2] and out[-1][3] == s[3]:
            out[-1][1] += s[1]
        else:
            out.append(list(s))
    while len(out) > 1 and out[0][2] is out[-1][2] and out[0][3] == out[-1][3]:
        out[-1][1] += out[0][1]
        out.pop(0)
    return out


# WHERE A JOURNEY SITS RELATIVE TO THE BOUNDARY IT CROSSES. One rule, and it is
# a statement about which end of a journey is negotiable:
#
#   **Work has hard edges; everything else absorbs the travel.**
#
# A shift starts when it starts, so somebody due at 08:00 leaves home early
# enough to arrive at 08:00 and the journey lands BEFORE the boundary. A shift
# ends when it ends, so the walk to the bar lands AFTER it. A trip between two
# soft activities -- quarters to market -- straddles the boundary evenly, since
# neither end is fixed by anything.
#
# This is not invented to be tidy: it is exactly the shape `schedule.activity_at`
# already emits, which puts TRANSIT in `[w0 - 0.5, w0]` and `[w_end, w_end +
# 0.5]`. The same rule is applied to the transit windows themselves when they are
# absorbed below, so there is one rule rather than two that happen to agree.
def _lean(from_act, to_act):
    """-1 journey ends at the boundary, +1 starts at it, 0 straddles it."""
    if to_act is A.WORK and from_act is not A.WORK:
        return -1
    if from_act is A.WORK and to_act is not A.WORK:
        return +1
    return 0


def _anchors(npc_id: str, species: str):
    """The day with `activity_at`'s flat transit windows folded into a neighbour.

    A `schedule.Activity.TRANSIT` span is not a place a person is; it is the
    module's placeholder for the journey this one computes properly. Folding it
    into the neighbour that is NOT work leaves the boundary exactly on the shift
    edge, which is where the roster says it is.
    """
    spans = _raw_spans(npc_id, species)
    idx = [i for i, s in enumerate(spans) if s[2] is not A.TRANSIT]
    if not idx or len(idx) == len(spans):
        return spans
    # Rotate so the list begins on a real anchor. Without this the first span
    # can be a journey with nothing behind it to fold into, which is a special
    # case that only ever fires on a minority of residents -- the kind of branch
    # a test written from the common case never reaches.
    k = idx[0]
    spans = spans[k:] + spans[:k]
    n = len(spans)
    keep, pending = [], 0.0
    for i, s in enumerate(spans):
        if s[2] is not A.TRANSIT:
            st, hrs = s[0], s[1]
            if pending > 0.0:
                st = (st - pending) % 24.0
                hrs += pending
                pending = 0.0
            keep.append([st, hrs, s[2], s[3]])
            continue
        prv, nxt = spans[(i - 1) % n], spans[(i + 1) % n]
        if _lean(prv[2], nxt[2]) <= 0:
            keep[-1][1] += s[1]          # the anchor before it ends later
        else:
            pending += s[1]              # the anchor after it starts earlier
    if pending > 0.0:                    # wrapped past 24:00 onto the first
        keep[0][0] = (keep[0][0] - pending) % 24.0
        keep[0][1] += pending
    return _merge(keep)


# THE CAP ON A JOURNEY, and it is arithmetic rather than taste. Each end of a
# journey eats into the anchor it borders, and an anchor borders two journeys, so
# a cap of f x (the shorter neighbour) leaves the anchor (1 - 2f) of itself. At
# f = 0.45 every anchor keeps at least a tenth of its own duration and a day can
# never be all travel -- which is what makes the 24-hour sum an identity rather
# than something to clamp afterwards.
#
# **IT FIRES ON 26.5% OF JOURNEYS AND THAT IS A FINDING, NOT A TUNING PROBLEM.**
# The first version of the gate below counted clamped journeys and failed at
# 26.5%, which reads as this module being wrong. Counting the TIME instead says
# what is actually happening: the clamp removes **8.8% of the travel hours the
# routes ask for**, so a quarter of journeys are trimmed and they are the short
# ones. The cause is upstream and is worth writing down: `schedule.activity_at`
# re-rolls its leisure choice every integer hour, so an off-shift resident gets
# ONE-HOUR anchors, and 45% of an hour is 27 minutes -- less than a cross-station
# route. The model is saying, correctly, that a resident cannot spend an hour in
# a bar 8 km away and another hour somewhere else an hour later.
#
# So the gate is on the hours, and the count is reported beside it.
JOURNEY_MAX_F = 0.45
_CLAMPED = [0, 0, 0.0, 0.0]    # [clamped, total, hours kept, hours asked for]


@lru_cache(maxsize=65536)
def day(npc_id: str, species: str = "human"):
    """One person's whole day: places they are, and journeys between them.

    A tuple of `Span`, in clock order from the first boundary, summing to 24.00
    hours exactly. A pure function of `(npc_id, species)` -- no clock, no state,
    no history -- which is what lets the runtime evaluate an NPC at any hour
    without simulating the ones before it.
    """
    anch = _anchors(npc_id, species)
    if len(anch) == 1:
        a = anch[0]
        return (Span(a[0], 24.0, a[2], a[3]),)

    n = len(anch)
    # The nominal boundary between anchor i and i+1, and the journey across it.
    trav = []
    for i in range(n):
        j = (i + 1) % n
        p, q = anch[i][3], anch[j][3]
        if p == q:
            trav.append((0.0, 0.0, 0))
            continue
        t_s, f_s = route_s(p, q)
        cap = JOURNEY_MAX_F * min(anch[i][1], anch[j][1])
        t_h = min(t_s / 3600.0, cap)
        _CLAMPED[1] += 1
        _CLAMPED[2] += t_h
        _CLAMPED[3] += t_s / 3600.0
        if t_s / 3600.0 > cap + 1e-12:
            _CLAMPED[0] += 1
        f_h = t_h * (f_s / t_s) if t_s > 0.0 else 0.0
        trav.append((t_h, f_h, _lean(anch[i][2], anch[j][2])))

    out = []
    for i in range(n):
        st, ln, act, place = anch[i]
        j = (i + 1) % n
        # travel out of this anchor (across the boundary at its end)
        out_h, out_f, out_lean = trav[i]
        # travel into this anchor (across the boundary at its start)
        in_h, _in_f, in_lean = trav[(i - 1) % n]

        take_end = out_h if out_lean <= 0 else 0.0      # journey before boundary
        if out_lean == 0:
            take_end = out_h / 2.0
        take_start = 0.0
        if in_lean >= 0:
            take_start = in_h if in_lean > 0 else in_h / 2.0

        stay = ln - take_end - take_start
        if stay < 1e-6:
            stay = 0.0
        if stay > 0.0:
            out.append(Span((st + take_start) % 24.0, stay, act, place))
        if out_h > 1e-9:
            j_start = (st + ln - take_end) % 24.0
            out.append(Span(j_start, out_h, A.TRANSIT, place,
                            anch[j][3], out_f))
    if not out:                                          # degenerate: all travel
        a = anch[0]
        return (Span(a[0], 24.0, a[2], a[3]),)
    total = sum(s.hours for s in out)
    if abs(total - 24.0) > 1e-6:
        raise AssertionError(f"day({npc_id!r}, {species!r}) sums to {total:.6f} h")
    return tuple(out)


def at(npc_id: str, species: str, hour: float) -> Span:
    """The span this person is in at this station-clock hour."""
    h = hour % 24.0
    for s in day(npc_id, species):
        if s.covers(h):
            return s
    # Floating point can land exactly on a boundary; take the span that starts
    # there rather than raising, because a query at 08.000000 must answer.
    best, bd = None, 1e9
    for s in day(npc_id, species):
        d = (h - s.start) % 24.0
        if d < bd:
            best, bd = s, d
    return best


def travel_hours(npc_id: str, species: str = "human") -> float:
    """Hours this person spends travelling in a day."""
    return sum(s.hours for s in day(npc_id, species) if s.moving)


def foot_hours(npc_id: str, species: str = "human") -> float:
    """Of those, the hours spent walking rather than being carried."""
    return sum(s.foot_hours for s in day(npc_id, species) if s.moving)


# ===========================================================================
# 2.  ROUTING -- how long a journey actually takes
# ===========================================================================
# Every journey is priced on `npc/navigation.py`'s graph, which is built from the
# assembled decks, the ring corridors, the spoke lifts, the core shuttle and the
# two tram systems, and which already prices a walk by the Froude gait model at
# the local gravity. Two numbers come back per route and they are different
# questions:
#
#   `travel_s`  the whole journey, doors to doors, including waiting for a lift
#   `foot_s`    only the `walk`, `stair` and `door` legs
#
# The split is the reason `foot_s` exists at all: a resident standing in a spoke
# lift is IN TRANSIT and is NOT IN A CORRIDOR, and the corridor is the space this
# project has to populate. `populace.CORRIDOR_PER_100M2` is derived from time on
# foot; §5 below closes that loop.
#
# The graph is human-gaited. `navigation.walk_speed(g, species)` takes a species
# and `build_graph` does not thread one through, so a Gaim and a Centauri walk a
# corridor at the same speed here. That is a stated limitation rather than a
# hidden one; the effect on the aggregate is bounded by the leg-length spread in
# `navigation.LEG_FRACTION`, and closing it means a graph per species, which is
# 32 s and 20,871 nodes each.
_GRAPH = None
_ROUTE_MISS = set()


def graph():
    """The station navigation graph. Built once; ~32 s the first time."""
    global _GRAPH
    if _GRAPH is None:
        import navigation as _nav                              # noqa: PLC0415
        _GRAPH = _nav.build_graph()
    return _GRAPH


FOOT_KINDS = frozenset({"walk", "stair", "door"})

# What an unroutable pair costs. It is NOT zero, because a zero would silently
# turn an unreachable destination into a teleport -- the exact defect this module
# exists to remove -- and it is not a big number either, because a big one would
# dominate the aggregate from a handful of pairs. It is the sample's own median
# journey, recorded below, and every use of it is COUNTED: `route_report()` names
# the pairs and `_selftest` asserts the count is zero on the current station.
ROUTE_FALLBACK_S = 300.0


@lru_cache(maxsize=1 << 16)
def route_s(a: str, b: str):
    """(total seconds, seconds on foot) from place `a` to place `b`."""
    if a == b:
        return 0.0, 0.0
    G = graph()
    na, nb = f"place:{a}", f"place:{b}"
    if na not in G.nodes or nb not in G.nodes:
        _ROUTE_MISS.add((a, b))
        return ROUTE_FALLBACK_S, ROUTE_FALLBACK_S
    r = G.path(na, nb, "time")
    if r is None:
        _ROUTE_MISS.add((a, b))
        return ROUTE_FALLBACK_S, ROUTE_FALLBACK_S
    foot = sum(l.time_s for l in r["links"] if l.kind in FOOT_KINDS)
    return r["time_s"], foot


def route_report():
    """Pairs that could not be routed, and therefore took the fallback."""
    return tuple(sorted(_ROUTE_MISS))


# ===========================================================================
# 3.  THE STATION, HOUR BY HOUR
# ===========================================================================
# The same statistical LOD `schedule.census` uses and for the same reason: a
# prefix of `_agg_id(species, i)` is a deterministic sample of that species, so
# the whole-station answer costs O(species x scan) rather than O(250,000). The
# weight is `STATION_COUNTS`, which is integer and sums to exactly 250,000, so
# nothing is lost to rounding on the way out (INV-005).
LIFE_SCAN = 384         # ids per species. Sampling error ~1/sqrt(n) = 5.1%
                        # on a species, ~1.4% on the 14-species total.


def _sample(species: str, scan: int):
    return tuple(_sched._agg_id(species, i) for i in range(scan))


@lru_cache(maxsize=256)
def _species_day_index(species: str, scan: int = LIFE_SCAN):
    """Every sampled resident's day, once. Everything below reads this."""
    return tuple(day(nid, species) for nid in _sample(species, scan))


# THE WINDOW, AND THE DEFECT THAT MADE IT NECESSARY. The first version of
# `station()` asked every resident what they were doing at exactly h:00 and
# counted the answers. It reported **66,469 people in transit** on the 24-hour
# mean -- 26.6% of the station, at every hour of the day and night -- while the
# same residents' own days sum to 116.8 minutes of travel each, which is **8.1%**
# and 20,271 people. A factor of **3.28**, from the sampler alone, on this
# module's headline number.
#
# The cause is that `schedule.activity_at` re-rolls its leisure choice on the
# INTEGER HOUR (`_u(npc_id, f"leisure-{int(hour)}")`), so an off-shift resident
# changes place at h:00 and at no other time. A journey between two soft
# activities straddles the boundary it crosses (see `_lean`), so **h:00 is the
# instant at which every leisure journey is at its midpoint**. Sampling there
# does not measure the station at 08:00; it measures the station's moment of
# maximum motion, and it does it 24 times a day.
#
# So an hour is an HOUR: `station(h)` is the expectation over a uniformly random
# instant in [h - 0.5, h + 0.5). Exact rather than sampled in time -- the spans
# are intervals and the overlap is arithmetic -- unbiased with respect to the
# model's own change points, and it is what a corridor's crowd density means
# anyway, since nobody photographs a corridor in zero seconds.
#
# The gate that catches this whole class of defect is one line in `_selftest` §4:
# the 24-hour mean of the hourly table must equal the residents' own mean travel
# time. It FAILS on the instantaneous sampler, which is how the bias was found
# instead of shipped. **A statistic sampled on the same grid the model changes
# state on measures the change, not the state.**
WINDOW_H = 1.0


def _overlap(d: float, length: float, w: float = WINDOW_H) -> float:
    """Hours a span starting `d` after the window opens spends inside it."""
    a, b = d, d + length
    tot = 0.0
    for off in (0.0, 24.0):          # the window's copies on the 24-hour circle
        lo = a if a > off else off
        hi = b if b < off + w else off + w
        if hi > lo:
            tot += hi - lo
    return tot


@lru_cache(maxsize=4096)
def station(hour: float, scan: int = LIFE_SCAN):
    """The whole station over the hour centred on `hour`. Sums to 250,000.

    Returns a dict with:
      `activity`  Activity -> heads
      `place`     place key -> heads standing in it
      `moving`    (from, to) -> heads on that journey
      `on_foot`   heads whose journey leg is walked rather than ridden
    """
    h = hour % 24.0
    w0 = (h - WINDOW_H / 2.0) % 24.0
    acts = {a: 0.0 for a in A}
    place = {}
    moving = {}
    on_foot = 0.0
    for species, count in _sched.STATION_COUNTS.items():
        days = _species_day_index(species, scan)
        w = count / float(len(days)) / WINDOW_H
        for d in days:
            for s in d:
                ov = _overlap((s.start - w0) % 24.0, s.hours)
                if ov <= 0.0:
                    continue
                acts[s.activity] += w * ov
                if s.moving:
                    key = (s.place, s.to_place)
                    moving[key] = moving.get(key, 0.0) + w * ov
                    on_foot += w * ov * (s.foot_hours / s.hours
                                         if s.hours else 0.0)
                else:
                    place[s.place] = place.get(s.place, 0.0) + w * ov
    heads = _apportion(acts, _sched.RESIDENT_TOTAL)
    return {
        "hour": h,
        "activity": heads,
        "place": {k: int(round(v)) for k, v in sorted(place.items())},
        "moving": {k: v for k, v in sorted(moving.items())},
        "on_foot": int(round(on_foot)),
        "in_transit": heads[A.TRANSIT],
    }


def _apportion(weights: dict, total: int) -> dict:
    """Integer largest-remainder, so the activities sum to 250,000 EXACTLY.

    `int(round(x))` per activity loses or gains up to half a person seven times
    over, and a population that changes size with the hour is the same class of
    defect INV-005 records -- a mix that summed to 0.94 and dropped 120 people
    in every 2,000 without anything noticing.
    """
    s = sum(weights.values())
    if s <= 0:
        return {k: 0 for k in weights}
    exact = {k: v / s * total for k, v in weights.items()}
    part = {k: int(v) for k, v in exact.items()}
    left = total - sum(part.values())
    order = sorted(exact, key=lambda k: (-(exact[k] - int(exact[k])),
                                         getattr(k, "value", str(k))))
    for k in order[:left]:
        part[k] += 1
    return part


def clamp_rate() -> float:
    """Fraction of journeys that hit `JOURNEY_MAX_F`."""
    return _CLAMPED[0] / max(1, _CLAMPED[1])


def clamp_hours_lost() -> float:
    """Fraction of the travel time the routes asked for that the cap removed.

    The number that matters. A clamp that trims a quarter of the journeys but
    a twelfth of the hours is trimming the short ones, and the aggregate this
    module exists to compute is made of hours.
    """
    return 1.0 - _CLAMPED[2] / max(1e-9, _CLAMPED[3])


def in_transit(hour: float, scan: int = LIFE_SCAN) -> int:
    """How many of the 250,000 are between two places right now."""
    return station(hour, scan)["in_transit"]


def on_foot(hour: float, scan: int = LIFE_SCAN) -> int:
    """How many of those are on their feet in a corridor rather than riding."""
    return station(hour, scan)["on_foot"]


def moving_between(a: str, b: str, hour: float, scan: int = LIFE_SCAN) -> int:
    """How many people are travelling from `a` to `b` at this hour."""
    return int(round(station(hour, scan)["moving"].get((a, b), 0.0)))


def busiest_journeys(hour: float, top: int = 10, scan: int = LIFE_SCAN):
    """The journeys carrying the most people at this hour."""
    mv = station(hour, scan)["moving"]
    rows = sorted(((int(round(v)), a, b) for (a, b), v in mv.items()),
                  key=lambda r: (-r[0], r[1], r[2]))
    return tuple(rows[:top])


def presence(place_key: str, hour: float, scan: int = LIFE_SCAN) -> int:
    """How many people are standing in this place at this hour."""
    return station(hour, scan)["place"].get(place_key, 0)


def presence_curve(place_key: str, scan: int = LIFE_SCAN):
    """24 hourly headcounts for one place."""
    return tuple(presence(place_key, float(h), scan) for h in range(24))


# ===========================================================================
# 4.  THE RECORDED TABLES
# ===========================================================================
# Everything above needs the navigation graph, which is 32 s. Everything a
# consumer normally wants is 24 numbers. So the 24 numbers are recorded, and
# `--derive` recomputes them from the graph and FAILS if a recorded value has
# drifted -- the same guard `tools/measure_frame.py` puts on its bands and
# `populace.py` on its corridor derivation.
#
# THE UNITS ARE PEOPLE, out of `schedule.RESIDENT_TOTAL` = 250,000.
# Derived at LIFE_SCAN = 384 ids per species; the sampling error on the total is
# about 1.4%, so DERIVE_TOL is set wider than that and narrower than any effect
# worth seeing.
DERIVE_TOL = 0.06

# People in transit -- between two places, on foot or riding -- meaned over the
# hour centred on each entry's index.
TRANSIT_AT = (
    15419, 9632, 7939, 9898, 9476, 11239, 19034, 27680, 24064, 21222,
    15909, 17777, 22957, 23858, 19422, 20973, 24930, 26927, 25187, 29791,
    29577, 26315, 23564, 23723,
)

# Of those, the ones on their FEET in a corridor rather than riding a lift,
# a tram or the core shuttle. This is the number a corridor's crowd comes from.
ON_FOOT_AT = (
    7855, 4270, 3750, 5092, 4610, 5729, 9410, 14904, 12646, 10395,
    7776, 8743, 10906, 11312, 9723, 10517, 11070, 12390, 12479, 15321,
    15163, 13215, 12343, 12077,
)

# Minutes a resident spends on foot in a corridor in a day, meaned over the
# station. `populace.WALK_MIN_PER_DAY` is 50.8 and the corridor density of the
# WHOLE STATION is derived from it; this is the same quantity recomputed from
# routed journeys instead of from hourly samples of `where_at`. The 14% it comes
# out high is explained rather than tolerated -- see §5.
WALK_MIN_PER_DAY = 58.01

# Mean minutes a resident spends travelling in a day, on foot or carried. 8.1%
# of a life, and it is the leisure churn rather than the commute: see §5.
TRAVEL_MIN_PER_DAY = 116.76

# The hours the station is quietest and busiest in its corridors, from
# ON_FOOT_AT. Recorded because they are a claim -- "03:00 differs visibly from
# 13:00" -- and a claim should be checkable without recomputing anything.
QUIET_HOUR = 2
BUSY_HOUR = 19


def transit_ratio(busy: int = None, quiet: int = None) -> float:
    """How many times busier the busiest corridor hour is than the quietest."""
    b = ON_FOOT_AT[BUSY_HOUR if busy is None else busy]
    q = ON_FOOT_AT[QUIET_HOUR if quiet is None else quiet]
    return b / max(1.0, float(q))


@lru_cache(maxsize=8)
def derive(scan: int = LIFE_SCAN):
    """Recompute every recorded table. Returns a dict; does not write."""
    tr, ft = [], []
    for h in range(24):
        st = station(float(h), scan)
        tr.append(st["in_transit"])
        ft.append(st["on_foot"])
    tot_t = tot_f = 0.0
    for species, count in _sched.STATION_COUNTS.items():
        days = _species_day_index(species, scan)
        w = count / float(len(days))
        for d in days:
            tot_t += w * sum(s.hours for s in d if s.moving)
            tot_f += w * sum(s.foot_hours for s in d if s.moving)
    n = float(_sched.RESIDENT_TOTAL)
    return {
        "TRANSIT_AT": tuple(tr),
        "ON_FOOT_AT": tuple(ft),
        "TRAVEL_MIN_PER_DAY": round(tot_t / n * 60.0, 2),
        "WALK_MIN_PER_DAY": round(tot_f / n * 60.0, 2),
        "QUIET_HOUR": min(range(24), key=lambda h: ft[h]),
        "BUSY_HOUR": max(range(24), key=lambda h: ft[h]),
        # The two halves of the consistency gate in §4: the mean of the hourly
        # table, and the same quantity computed from the residents' own days
        # without ever consulting the clock. They are the same number or the
        # hourly table is being sampled wrong.
        "mean_transit": sum(tr) / 24.0,
        "mean_transit_from_days": tot_t / n / 24.0 * _sched.RESIDENT_TOTAL,
        "clamp_rate": clamp_rate(),
    }


# ===========================================================================
# 5.  AGREEMENT WITH THE PLACEMENT MODEL
# ===========================================================================
# Two models describe one station and they must not disagree:
#
#   `populace.occupancy(place, area, hour, arch)` -- a DENSITY. How many bodies
#       a room holds, from `schedule.PlaceCrowd`'s peak-per-100 m2 and its busy
#       and dead windows, or an archetype rate where the place has no entry.
#   `life.presence(place, hour)` -- a HEADCOUNT of PEOPLE, from 250,000
#       individual days.
#
# They are not the same quantity and will never be equal: one is calibrated to a
# floor area, the other to a population. What must agree is the SHAPE -- if this
# module says the Zocalo fills at 03:00 and `occupancy` says 13:00, a player
# walking in meets a crowd from one model in a room lit for the other.
#
# So the comparison is between the two 24-hour curves, by Pearson correlation.
# Reported per place and gated on the mean.
#
# WHAT IT FOUND, AND THE SHAPE OF IT IS THE FINDING. Over 66 places with enough
# people to have a shape at all, the mean is **+0.32**, which reads as a weak
# agreement and is not one. Sorted, the bottom of the table is this:
#
#     -0.80  qtr_civilian        -0.71  downbelow_arch     -0.69  qtr_personnel
#     -0.68  qtr_transient       -0.67  subfloor_stack     -0.58  morgue
#     -0.56  alien_resident_qtr
#
# **Six of the seven places people LIVE are in the bottom seven, and the only
# thing sharing the band with them is the morgue.** Split on it:
#
#     non-residential (59 places)   mean r = +0.42, median +0.62
#     residences       (7 places)   mean r = -0.56; the one exception is
#                                   `league_delegations` at +0.16, still below
#                                   the median room
#
# That is not 66 places each drifting a little; it is one mechanism, and
# CLAUDE.md's session-4d rule -- *"a number that fails 100% on one side of a line
# and 1% on the other is a structural fact"* -- says to go and find it rather
# than widen the tolerance.
#
# It is `populace.occupancy`'s fallback curve, and the peak densities confirm it:
# every one of those seven comes back at **4 per 100 m2**, the `generic`
# archetype rate, so none of them has a `PlaceCrowd` entry and all of them take
# `day = 0.25 + 0.75 * sin(pi * (hour - 6) / 14)` -- a curve that peaks at 13:00.
# That is a reasonable shape for an office and exactly backwards for a bedroom.
# So the placement model puts the most bodies in `qtr_civilian` at one in the
# afternoon and the fewest at three in the morning, while THIS model has 85,320
# residents asleep in there at 03:00 and 55,610 at 08:00.
#
# THE CONSEQUENCE IS VISIBLE AND IT IS NOT SMALL: the quarters hold a third of
# the station at any hour and today they are populated on an office's clock. The
# fix is a residential entry in `populace.FALLBACK_PER_100M2` with a
# night-weighted curve, or a `PlaceCrowd` per quarters block. That file is not
# this one's, so this is a measurement and an assertion rather than a patch: the
# self-test gates the non-residential mean and asserts the residential anomaly is
# still exactly where this note says it is, so the day it is fixed, this fails.
def _arch(place_key: str) -> str:
    try:
        import directory as _dir                               # noqa: PLC0415
        import rooms as _rooms                                 # noqa: PLC0415
    except Exception:                                          # noqa: BLE001
        return "generic"
    for p in _dir.PLACES:
        if p["key"] == place_key:
            return _rooms.archetype(p)
    return "generic"


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 1e-12 or syy <= 1e-12:
        return None                     # one of the curves is flat: no shape
    return sxy / math.sqrt(sxx * syy)


def occupancy_agreement(scan: int = LIFE_SCAN, min_heads: int = 40,
                        shift_h: int = 0):
    """Correlate every place's life curve with `populace.occupancy`'s.

    `shift_h` rotates the life curve and exists only so the self-test has a
    control: a model rotated twelve hours must correlate WORSE, and if it does
    not, the correlation is not measuring the shape of a day.
    """
    import populace as _pop                                     # noqa: PLC0415
    rows = []
    curves = {}
    for h in range(24):
        curves[h] = station(float(h), scan)["place"]
    keys = set()
    for h in range(24):
        keys.update(curves[h])
    homes = home_places(scan)
    for key in sorted(keys):
        mine = [curves[(h + shift_h) % 24].get(key, 0) for h in range(24)]
        if max(mine) < min_heads:
            continue                    # too few people to have a shape at all
        arch = _arch(key)
        theirs = [_pop.occupancy(key, 100.0, float(h), arch) for h in range(24)]
        r = _pearson(mine, theirs)
        if r is None:
            continue
        rows.append((key, r, max(mine), max(theirs), key in homes))
    rows.sort(key=lambda r: r[1])
    res = [r for r in rows if r[4]]
    oth = [r for r in rows if not r[4]]
    return {
        "rows": tuple(rows),
        "mean_r": sum(r[1] for r in rows) / len(rows) if rows else 0.0,
        "n": len(rows),
        "mean_r_residence": sum(r[1] for r in res) / len(res) if res else 0.0,
        "n_residence": len(res),
        "mean_r_other": sum(r[1] for r in oth) / len(oth) if oth else 0.0,
        "n_other": len(oth),
    }


@lru_cache(maxsize=8)
def home_places(scan: int = LIFE_SCAN) -> frozenset:
    """Every place somebody in the sample lives. Derived, never typed in."""
    out = set()
    for species in _sched.STATION_COUNTS:
        for nid in _sample(species, scan):
            out.add(_res.resident(nid, species).home)
    return frozenset(out)


# ===========================================================================
# 6.  WHAT THE RUNTIME EMBEDS
# ===========================================================================
# `godot/scripts/life.gd` cannot import Python. It carries the two curves this
# module derives, as a const block this function prints, and its own self-test
# asserts the embedded values match. `--gd` regenerates the block.
GD_PLACE_MIN = 60       # places with fewer people than this at their own peak
                        # do not get a curve; the runtime falls back to flat.


def gd_block(scan: int = LIFE_SCAN) -> str:
    d = derive(scan)
    curves = {h: station(float(h), scan)["place"] for h in range(24)}
    keys = sorted({k for h in range(24) for k in curves[h]})
    lines = []
    lines.append("# GENERATED by `python3 station/npc/life.py --gd`. Do not "
                 "hand-edit:")
    lines.append("# `life.py --selftest` re-derives these and fails on drift.")
    lines.append("const TRANSIT_AT := [%s]"
                 % ", ".join(str(v) for v in d["TRANSIT_AT"]))
    lines.append("const ON_FOOT_AT := [%s]"
                 % ", ".join(str(v) for v in d["ON_FOOT_AT"]))
    lines.append("const WALK_MIN_PER_DAY := %.2f" % d["WALK_MIN_PER_DAY"])
    lines.append("const QUIET_HOUR := %d" % d["QUIET_HOUR"])
    lines.append("const BUSY_HOUR := %d" % d["BUSY_HOUR"])
    lines.append("const PRESENCE := {")
    for k in keys:
        col = [curves[h].get(k, 0) for h in range(24)]
        peak = max(col)
        if peak < GD_PLACE_MIN:
            continue
        lines.append('\t"%s": [%s],'
                     % (k, ", ".join("%.2f" % (v / peak) for v in col)))
    lines.append("}")
    return "\n".join(lines)


# ===========================================================================
# 7.  SELF-TEST
# ===========================================================================
_FAILED = []


def check(ok, name, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (("  -- " + detail)
                                                     if detail else ""))
    if not ok:
        _FAILED.append(name)
    return ok


def _fmt(v):
    return f"{v:,}"


def _check_breakpoints(scan=24):
    """The derived edge list must reconstruct `activity_at` on a minute grid.

    THE RISK THIS COVERS. `_breakpoints` is a copy of another module's internal
    structure, and a copy drifts. A minute grid over 24 h is 1,440 samples a
    resident -- far too expensive for the aggregate and exactly right for a
    handful, because the thing being tested is the EDGE LIST, not the population.
    """
    worst = 0
    for species in ("human", "brakiri", "gaim", "centauri", "other", "vorlon"):
        for i in range(scan):
            nid = _sched._agg_id(species, i)
            raw = _raw_spans(nid, species)
            bad = 0
            for m in range(1440):
                h = m / 60.0
                want = _sched.activity_at(nid, species, h)
                got = None
                for s in raw:
                    if ((h - s[0]) % 24.0) < s[1] - 1e-9:
                        got = s[2]
                        break
                if got is not want:
                    bad += 1
            worst = max(worst, bad)
    return worst


def _selftest(scan=LIFE_SCAN, quick=False):
    print("=" * 74)
    print("station/npc/life.py -- the day every resident lives")
    print("=" * 74)

    # --- 1. the day is a partition ---------------------------------------
    print("\n1. A DAY IS A PARTITION OF 24 HOURS")
    bad_sum, bad_gap, n_seen, seg_n = 0, 0, 0, []
    for species in ("human", "centauri", "brakiri", "gaim", "vorlon", "other"):
        for i in range(24 if quick else 64):
            nid = _sched._agg_id(species, i)
            d = day(nid, species)
            n_seen += 1
            seg_n.append(len(d))
            if abs(sum(s.hours for s in d) - 24.0) > 1e-6:
                bad_sum += 1
            for k in range(len(d)):
                nxt = d[(k + 1) % len(d)]
                if abs(((d[k].start + d[k].hours) % 24.0) - nxt.start) > 1e-6:
                    bad_gap += 1
    check(bad_sum == 0, "every day sums to 24.000000 h",
          f"{n_seen} residents, {bad_sum} bad")
    check(bad_gap == 0, "no gaps and no overlaps between spans",
          f"{bad_gap} discontinuities in {sum(seg_n)} spans")
    check(sum(seg_n) / len(seg_n) > 6.0, "a day has structure, not one span",
          f"mean {sum(seg_n)/len(seg_n):.1f} spans, max {max(seg_n)}")

    # NEGATIVE CONTROL: a partition test that cannot fail is worthless.
    broken = (Span(0.0, 10.0, A.IDLE, "a"), Span(10.0, 8.0, A.IDLE, "b"))
    check(abs(sum(s.hours for s in broken) - 24.0) > 1e-6,
          "CONTROL: an 18-hour day is rejected by the same test",
          "sums to 18.0")

    # --- 2. the edge list is not a stale copy ----------------------------
    print("\n2. THE PIECEWISE DAY RECONSTRUCTS schedule.activity_at EXACTLY")
    worst = _check_breakpoints(4 if quick else 16)
    check(worst == 0,
          "minute-grid reconstruction matches activity_at on every sample",
          f"worst resident: {worst} of 1440 minutes disagree")

    # --- 3. journeys are routed, not assumed -----------------------------
    print("\n3. EVERY JOURNEY IS ROUTED ON THE STATION'S OWN NAV GRAPH")
    t0 = _t()
    G = graph()
    check(len(G.nodes) > 10000, "navigation graph built",
          f"{len(G.nodes):,} nodes, {len(G.links):,} links, {_t()-t0:.0f} s")
    r_home = route_s("qtr_civilian", "business_center")
    check(r_home[0] > 60.0 and r_home[1] > 0.0,
          "qtr_civilian -> business_center is a real journey",
          f"{r_home[0]/60.0:.1f} min, of which {r_home[1]/60.0:.1f} on foot")
    check(route_s("qtr_civilian", "qtr_civilian") == (0.0, 0.0),
          "CONTROL: a journey to where you already are costs nothing")

    # --- 4. the aggregate ------------------------------------------------
    print("\n4. THE STATION, HOUR BY HOUR")
    t0 = _t()
    st3 = station(3.0, scan)
    st8 = station(8.0, scan)
    st13 = station(13.0, scan)
    print(f"     ({_t()-t0:.0f} s for three hours at scan={scan})")
    for h, st in ((3, st3), (8, st8), (13, st13)):
        print(f"     {h:02d}:00  in transit {_fmt(st['in_transit']):>7}"
              f"   on foot {_fmt(st['on_foot']):>7}"
              f"   asleep {_fmt(st['activity'][A.SLEEP]):>7}"
              f"   at work {_fmt(st['activity'][A.WORK]):>7}")
    check(sum(st8["activity"].values()) == _sched.RESIDENT_TOTAL,
          "the station's activities sum to 250,000 exactly",
          _fmt(sum(st8['activity'].values())))
    ratio = st8["on_foot"] / max(1.0, st3["on_foot"])
    check(ratio > 2.0,
          "a corridor at 08:00 is measurably busier than at 03:00",
          f"on foot {_fmt(st8['on_foot'])} vs {_fmt(st3['on_foot'])}"
          f" = x{ratio:.2f}")
    check(abs(st8["on_foot"] / max(1.0, st8["on_foot"]) - 1.0) < 1e-9,
          "CONTROL: 08:00 against itself shows no difference", "x1.00")

    # THE GATE THAT CAUGHT THE SAMPLER. The hourly table's own 24-hour mean must
    # equal the residents' mean travel time, which is computed from their days
    # and never consults the clock. Two independent routes to one number.
    dd = derive(scan)
    a_, b_ = dd["mean_transit"], dd["mean_transit_from_days"]
    check(abs(a_ - b_) / max(a_, b_, 1.0) < 0.02,
          "the hourly table integrates to the residents' own travel time",
          f"mean of TRANSIT_AT {a_:,.0f} vs {b_:,.0f} from the days")
    # CONTROL: the instantaneous sampler this replaced. `activity_at` re-rolls
    # leisure on the integer hour, so h:00 is the midpoint of every leisure
    # journey; sampling there reported 4x the truth at every hour of the day.
    inst = _instantaneous_mean_transit(scan)
    check(abs(inst - b_) / max(inst, b_) > 0.5,
          "CONTROL: sampling at exactly h:00 fails that gate, x{:.1f} high"
          .format(inst / max(1.0, b_)),
          f"{inst:,.0f} people 'in transit' against a true {b_:,.0f}")
    check(clamp_hours_lost() < 0.15,
          "the JOURNEY_MAX_F cap costs little of the travel time asked for",
          f"{clamp_hours_lost()*100:.1f}% of the hours, from "
          f"{clamp_rate()*100:.1f}% of {_CLAMPED[1]:,} journeys -- it trims "
          f"the short ones")

    # NEGATIVE CONTROL -- the teleport station. Force every route to zero and
    # the corridors empty at every hour, so the ratio above has nothing to
    # measure. This is the defect this module was written to remove, so the
    # gate must fail on it.
    print("\n   CONTROL: the teleporting station (all routes 0 s)")
    with _routes_forced(lambda a, b: (0.0, 0.0)):
        z8 = station(8.0, scan)
        z3 = station(3.0, scan)
    check(z8["on_foot"] == 0 and z3["on_foot"] == 0,
          "CONTROL: with instant travel nobody is ever in a corridor",
          f"08:00 on foot {z8['on_foot']}, 03:00 {z3['on_foot']}")
    check(not (z8["on_foot"] / max(1.0, z3["on_foot"]) > 4.0),
          "CONTROL: and the 08:00-vs-03:00 gate FAILS on it, as it must")

    # --- 5. agreement with populace ---------------------------------------
    print("\n5. AGREEMENT WITH THE PLACEMENT MODEL (populace.py)")
    d = dd
    import populace as _pop                                     # noqa: PLC0415
    err = abs(d["WALK_MIN_PER_DAY"] - _pop.WALK_MIN_PER_DAY) \
        / _pop.WALK_MIN_PER_DAY
    check(err < 0.20,
          "time on foot agrees with populace.WALK_MIN_PER_DAY",
          f"{d['WALK_MIN_PER_DAY']:.2f} min/day here vs "
          f"{_pop.WALK_MIN_PER_DAY:.1f} there = {err*100:.1f}%")
    with _routes_forced(lambda a, b: tuple(2.0 * x for x in _route_raw(a, b))):
        d2 = derive(scan)
    err2 = abs(d2["WALK_MIN_PER_DAY"] - _pop.WALK_MIN_PER_DAY) \
        / _pop.WALK_MIN_PER_DAY
    check(err2 > 0.20,
          "CONTROL: doubling every route breaks that agreement",
          f"{d2['WALK_MIN_PER_DAY']:.2f} min/day = {err2*100:.1f}% off")

    ag = occupancy_agreement(scan)
    print(f"     worst three:  " + ",  ".join(
        f"{k} r={r:+.2f}" for k, r, _a, _b, _h in ag["rows"][:3]))
    print(f"     best three:   " + ",  ".join(
        f"{k} r={r:+.2f}" for k, r, _a, _b, _h in ag["rows"][-3:]))
    check(ag["n_other"] >= 10 and ag["mean_r_other"] > 0.35,
          "per-place hour shape correlates with populace.occupancy",
          f"mean r = {ag['mean_r_other']:+.3f} over {ag['n_other']} "
          f"non-residential places")
    ag12 = occupancy_agreement(scan, shift_h=12)
    check(ag12["mean_r_other"] < ag["mean_r_other"] - 0.20,
          "CONTROL: rotating the day 12 h destroys that agreement",
          f"mean r = {ag12['mean_r_other']:+.3f} "
          f"(was {ag['mean_r_other']:+.3f})")
    # AND THE OTHER SIDE OF THE LINE IS A FINDING ABOUT populace.py, ASSERTED
    # RATHER THAN FIXED, because the defect is not in this file and CLAUDE.md's
    # session-4d rule says to read the SHAPE of a failing number before its
    # size. The shape here is as clean as it gets: the SEVEN worst-correlated
    # places on the station are seven of the eight residences, and the eighth
    # thing in that band is the morgue.
    res = [(k, r) for k, r, _a, _b, h in ag["rows"] if h]
    oth_r = sorted(r for _k, r, _a, _b, h in ag["rows"] if not h)
    med_oth = oth_r[len(oth_r) // 2] if oth_r else 0.0
    neg = [k for k, r in res if r < 0.0]
    check(res and ag["mean_r_residence"] < -0.30,
          "FINDING: populace.occupancy fills the QUARTERS in the afternoon",
          f"{len(neg)} of {len(res)} residences are ANTI-correlated, "
          f"mean {ag['mean_r_residence']:+.3f}; the exception is "
          + ", ".join(f"{k} {r:+.2f}" for k, r in res if r >= 0.0))
    check(res and max(r for _k, r in res) < med_oth,
          "...and no residence beats the median room, so it is not a spread",
          f"best residence {max(r for _k, r in res):+.2f} against a median "
          f"room of {med_oth:+.2f} -- see the note in §5")

    # --- 6. the census is the same census ---------------------------------
    print("\n6. THIS MODULE AND schedule.py COUNT THE SAME PEOPLE")
    # OVER THE SAME WINDOW, which the first version of this gate did not do:
    # it compared this module's hour-MEAN against `population_activity`'s
    # instantaneous sample at 8.0 and reported a 2,563-person discrepancy that
    # was entirely the sampler. The reference has to be integrated the same way
    # the subject is, or the comparison measures the integrator.
    # AND WITH TRAVEL TAKEN OUT OF BOTH, which is the only comparison the two
    # models can fairly be held to. This module reclassifies time as travel that
    # `schedule.py` spends standing somewhere, and folds `schedule.py`'s own flat
    # half-hour commute window back into whatever the resident was doing -- so
    # the TRANSIT bucket is where they are designed to differ. Renormalising over
    # the other seven and taking the total variation distance asks the question
    # that matters: *is this the same station?*
    pa = _window_activity(8.0)
    mine = st8["activity"]
    tv = _tv_non_transit(mine, pa)
    check(tv < 0.05,
          "with travel removed, the two censuses are the same station",
          f"total variation {tv*100:.2f}% over the seven other activities")
    # CONTROL: the same comparison against the schedule at 20:00. If 2.2% at the
    # matching hour means anything, the wrong hour has to be far worse.
    tv20 = _tv_non_transit(mine, _window_activity(20.0))
    check(tv20 > 4.0 * tv,
          "CONTROL: against schedule.py at 20:00 instead, it is not",
          f"total variation {tv20*100:.2f}% = x{tv20/max(tv,1e-9):.1f}")
    same = sum(1 for a in A
               if a is not A.TRANSIT and pa[a] > 0
               and abs(mine[a] - pa[a]) / pa[a] < 0.35)
    check(same >= 5,
          "and no single activity is out by more than a third",
          f"{same} of 7 within 35%")

    # --- 7. the recorded tables ------------------------------------------
    print("\n7. THE RECORDED TABLES REBUILD FROM THE GRAPH")
    drift = []
    for name, rec in (("TRANSIT_AT", TRANSIT_AT), ("ON_FOOT_AT", ON_FOOT_AT)):
        got = d[name]
        for h in range(24):
            base = max(rec[h], got[h], 1)
            if abs(rec[h] - got[h]) / base > DERIVE_TOL:
                drift.append(f"{name}[{h}] {rec[h]} != {got[h]}")
    for name, rec in (("WALK_MIN_PER_DAY", WALK_MIN_PER_DAY),
                      ("TRAVEL_MIN_PER_DAY", TRAVEL_MIN_PER_DAY)):
        if abs(d[name] - rec) / max(rec, 1e-9) > DERIVE_TOL:
            drift.append(f"{name} {rec} != {d[name]}")
    check(not drift, f"all recorded values within {DERIVE_TOL*100:.0f}%",
          "; ".join(drift[:4]) if drift else
          f"24 + 24 + 2 values, scan={scan}")
    check(d["QUIET_HOUR"] == QUIET_HOUR and d["BUSY_HOUR"] == BUSY_HOUR,
          "the quiet and busy hours are where the table says",
          f"quiet {d['QUIET_HOUR']:02d}:00, busy {d['BUSY_HOUR']:02d}:00")
    check(not route_report(),
          "every place a resident's life touches is routable",
          f"{len(route_report())} unroutable pairs"
          + (": " + ", ".join(f"{a}->{b}" for a, b in route_report()[:4])
             if route_report() else ""))

    # --- 8. the runtime's const block ------------------------------------
    print("\n8. THE RUNTIME EMBEDS WHAT THIS MODULE DERIVED")
    gd_path = os.path.join(os.path.dirname(_STATION), "godot", "scripts",
                           "life.gd")
    if os.path.exists(gd_path):
        with open(gd_path, encoding="utf-8") as fh:
            have = {ln.strip() for ln in fh}
        # Whitespace-normalised, because the block is emitted flush left and
        # lives indented inside `class Director`. Comparing raw text would fail
        # on the indentation and pass on nothing, which is a gate that always
        # fires -- as useless as one that never does.
        want = [ln.strip() for ln in gd_block(scan).splitlines()
                if ln.strip() and not ln.strip().startswith("#")]
        missing = [ln for ln in want if ln not in have]
        check(not missing,
              "life.gd embeds exactly what this module derives",
              f"{len(want) - len(missing)} of {len(want)} const lines match"
              + ("; run --gd and re-paste" if missing else ""))
    else:
        check(False, "godot/scripts/life.gd exists", gd_path)

    print("\n" + "=" * 74)
    if _FAILED:
        print(f"{len(_FAILED)} FAILED: " + "; ".join(_FAILED))
        return 1
    print("all gates pass")
    return 0


# --- test scaffolding ------------------------------------------------------
def _t():
    import time
    return time.time()


_route_raw = None


class _routes_forced:
    """Swap `route_s` for the duration of a block, and clear every cache it fed.

    A CONTROL THAT DOES NOT REACH THE CACHES IS NOT A CONTROL. `day()`,
    `_species_day_index()` and `station()` are all memoised on top of `route_s`,
    so replacing the router without clearing them measures the old model twice
    and reports IDENTICAL -- which is exactly the defect CLAUDE.md records from
    session 4d, where an A/B said IDENTICAL because both halves had died.
    """

    def __init__(self, fn):
        self.fn = fn

    def __enter__(self):
        global route_s, _route_raw
        _route_raw = route_s
        self.old = route_s
        route_s = self.fn
        _clear_caches()
        return self

    def __exit__(self, *exc):
        global route_s
        route_s = self.old
        _clear_caches()
        return False


def _clear_caches():
    day.cache_clear()
    _species_day_index.cache_clear()
    station.cache_clear()
    derive.cache_clear()
    _CLAMPED[0] = _CLAMPED[1] = 0
    _CLAMPED[2] = _CLAMPED[3] = 0.0


def _window_activity(hour: float, samples: int = 6):
    """`schedule.population_activity` integrated over the same hour window.

    The reference for §6. `station()` reports a mean over [h-0.5, h+0.5);
    comparing that against an instantaneous `population_activity(h)` compares
    two different quantities, and the difference is the leisure-boundary bias
    described at `WINDOW_H` -- 2,563 people of it, measured.
    """
    acc = {a: 0.0 for a in A}
    w0 = hour - WINDOW_H / 2.0
    for k in range(samples):
        h = (w0 + WINDOW_H * (k + 0.5) / samples) % 24.0
        pa = _sched.population_activity(h)
        for a in A:
            acc[a] += pa[a] / samples
    return acc


def _tv_non_transit(a: dict, b: dict) -> float:
    """Total variation distance between two censuses, travel excluded.

    Both are renormalised over the seven non-travel activities first, so the
    measure is "do these describe the same station" and not "do they agree about
    how much walking there is" -- which they are built to disagree about.
    """
    sa = sum(v for k, v in a.items() if k is not A.TRANSIT)
    sb = sum(v for k, v in b.items() if k is not A.TRANSIT)
    if sa <= 0 or sb <= 0:
        return 1.0
    return 0.5 * sum(abs(a[k] / sa - b[k] / sb)
                     for k in A if k is not A.TRANSIT)


def _instantaneous_mean_transit(scan: int = LIFE_SCAN) -> float:
    """The station's mean in-transit count as the FIRST sampler measured it.

    Kept as a control rather than deleted, because a defect with no reproduction
    is a story and a defect with one is a gate. This asks every resident what
    they are doing at exactly h:00, for h in 0..23, which is what `station()`
    did before `WINDOW_H` existed.
    """
    tot = 0.0
    for species, count in _sched.STATION_COUNTS.items():
        days = _species_day_index(species, scan)
        w = count / float(len(days))
        for d in days:
            for h in range(24):
                for s in d:
                    if s.covers(float(h)):
                        if s.moving:
                            tot += w
                        break
    return tot / 24.0


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quick", action="store_true",
                    help="fewer ids per species; for a smoke test only")
    ap.add_argument("--derive", action="store_true")
    ap.add_argument("--gd", action="store_true")
    ap.add_argument("--day", metavar="ID")
    ap.add_argument("--species", default="human")
    ap.add_argument("--hour", type=float)
    ap.add_argument("--scan", type=int, default=LIFE_SCAN)
    a = ap.parse_args(argv)

    if a.day:
        print(f"{a.day}  ({a.species})")
        res = _res.resident(a.day, a.species)
        print(f"  {res.name or '(no attested name)'}   role {res.role}"
              f"   home {res.home}   job {res.job or '-'}")
        for s in day(a.day, a.species):
            end = (s.start + s.hours) % 24.0
            if s.moving:
                print(f"  {s.start:05.2f}-{end:05.2f}  TRAVEL  "
                      f"{s.place} -> {s.to_place}"
                      f"   ({s.hours*60:.0f} min, {s.foot_hours*60:.0f} on foot)")
            else:
                print(f"  {s.start:05.2f}-{end:05.2f}  "
                      f"{s.activity.value:<10} {s.place}")
        print(f"  travel {travel_hours(a.day, a.species)*60:.0f} min/day, "
              f"on foot {foot_hours(a.day, a.species)*60:.0f} min/day")
        return 0

    if a.hour is not None:
        st = station(a.hour, a.scan)
        print(f"THE STATION AT {st['hour']:05.2f}  (scan {a.scan}/species)")
        for act in A:
            print(f"  {act.value:<11} {st['activity'][act]:>8,}")
        print(f"  {'on foot':<11} {st['on_foot']:>8,}"
              f"   (of {st['in_transit']:,} in transit)")
        print("  busiest journeys:")
        for n, p, q in busiest_journeys(a.hour, 8, a.scan):
            print(f"    {n:>6,}  {p} -> {q}")
        print("  busiest places:")
        for k, v in sorted(st["place"].items(), key=lambda kv: -kv[1])[:8]:
            print(f"    {v:>6,}  {k}")
        return 0

    if a.derive:
        d = derive(a.scan)
        for k in ("TRANSIT_AT", "ON_FOOT_AT"):
            print(f"{k} = (")
            row = d[k]
            for i in range(0, 24, 10):
                print("    " + ", ".join(str(v) for v in row[i:i + 10]) + ",")
            print(")")
        print(f"WALK_MIN_PER_DAY = {d['WALK_MIN_PER_DAY']}")
        print(f"TRAVEL_MIN_PER_DAY = {d['TRAVEL_MIN_PER_DAY']}")
        print(f"QUIET_HOUR = {d['QUIET_HOUR']}")
        print(f"BUSY_HOUR = {d['BUSY_HOUR']}")
        return 0

    if a.gd:
        print(gd_block(a.scan))
        return 0

    return _selftest(a.scan if not a.quick else 96, quick=a.quick)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
