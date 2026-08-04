"""The port: what arrives, when, where it berths, and how many people it lands.

CLAUDE.md's scope names *"transports and visitors arriving and departing
continuously; the jump gate working"* and *"customs and immigration"* in the
same sentence as the NPCs. `docs/gazetteer/TRAFFIC-AND-CUSTOMS.md` is 910 lines
answering exactly that -- the jump gate, the ship classes, docking end to end,
arrival rates, the daily manifest, customs, cargo, and a section titled *"THE
PORT AS A LIVING SYSTEM -- what to actually simulate"* -- and until this module
existed **one file read it**, `station/aperture.py`, for a hull cut.

WHY IT IS WORTH A MODULE AND NOT A TABLE
----------------------------------------
Because the crowd system already has an arrival model, and **the two disagree by
a factor of four**. `npc/schedule.py` carries `ARRIVALS_PER_DAY = 52` and
`SOULS_PER_ARRIVAL = 120`, i.e. **6,240 people a day inbound**. §5.3 of the
gazetteer reasons its own manifest to **~1,500**:

    14 transports x ~50 pax = 700 | 12 shuttles x ~10 = 120
    0.5 liners x ~600 = 300      | freighter and warship crew ashore ~300
    diplomatic and EarthForce ~100                        total ~1,500

Neither number is canon. What matters is that they are **two descriptions of one
quantity**, and until now nothing could see them at once. `cross_check()` puts
them side by side and `report()` prints the gap. See C-012.

THREE THINGS THE ARRIVAL STREAM DOES NOT CURRENTLY HAVE
-------------------------------------------------------
Measured against `schedule.arrival_times`, which is what the crowd actually uses:

  1. **It is flat.** 52 arrivals land essentially uniformly over the day.
     §5.4 gives peak-to-trough **3:1** -- one movement every 25 minutes at
     04:00 and one every 8 minutes at 10:00.
  2. **It has one peak and the day has two.** `schedule.wave_pulse` reads 1.0 at
     10:00 and 0.0 at 18:00. §5.4's second peak is 17:00-21:00 and it is the
     interesting one: *"departures; the Zocalo is busiest at station-evening and
     the port empties into it."*
  3. **There is no liner.** §5.2 is explicit -- *"the liner is the event ...
     build the day around it"* -- because 600 passengers through one hall in 90
     minutes is **13x the per-hall background** of half a person a minute. That
     contrast is the same crowdedness-and-isolation axis the owner named, and a
     uniform stream cannot produce it.

`day_curve`, `arrivals` and `hall_rate` here supply all three. Nothing in this
module changes `schedule.py`; it is a second, sourced description that can be
compared with the first, and the comparison is the deliverable.
"""

import math
import os
import sys
from functools import lru_cache

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)

import interior as it                                          # noqa: E402
from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(_HERE), "docs", "gazetteer",
                         "TRAFFIC-AND-CUSTOMS.md")

# ===========================================================================
# 1.  The tempo of the port
# ===========================================================================

# THE ONE SOURCED FIGURE. Authority 4, the Babylon 5 wiki: "On a daily basis,
# over 50 to 60 ships used it as a waypoint, nearly 95% of this traffic was
# purely civilian". Kept as a BAND because that is how it is stated.
SOURCED_MOVEMENTS_PER_DAY = (50.0, 60.0)
CIVILIAN_SHARE = 0.95

# Mean hours a berth is occupied per visit. This is the free parameter of the
# cross-check below and §5.1 sweeps it: 6 h gives 96 movements a day, 8 h gives
# 72, 10 h gives 57.6, 12 h gives 48, 24 h gives 24. Ten is taken because it is
# the value that lands inside the sourced band -- and the agreement is the
# evidence, not the choice.
MEAN_BERTH_HOURS = 10.0

# WHAT ONE HALL PROCESSES, from `npc/schedule.py` rather than restated -- the
# customs model already exists and this module must not become a second copy
# of it.
HALLS = int(sched.CUSTOMS_HALLS)


def bay_count(schema=None) -> int:
    """The docking bays, from the schema rather than the number 24.

    `station/docking_bay.py` reads the same field. The Security Manual's
    sectional schematic gives DOCKING BAYS (24) at authority 3, and it lives in
    `schema["docking"]["docking_bay"]["count"]` -- one place, as CLAUDE.md's
    first hard rule requires.
    """
    if schema is None:
        schema, _profile = it.load()
    return int(schema["docking"]["docking_bay"]["count"])


def movements_per_day(schema=None, berth_h: float = None) -> float:
    """Ship movements a day, derived from berths and turnaround.

    THE CROSS-CHECK THAT MAKES THE SOURCED FIGURE CREDIBLE, and it is §5.1's
    and worth restating because it is a good one: 24 berths x 24 hours over a
    10-hour mean occupancy is 57.6 movements a day, and an unrelated source says
    50-60. Two numbers from sources that know nothing about each other, agreeing
    to within a couple of percent, on a quantity neither was computed to match.
    """
    # RESOLVED AT CALL TIME, NOT BOUND AT DEF TIME. `berth_h=MEAN_BERTH_HOURS`
    # in the signature captures the module-level value when the `def` runs, so
    # the negative control below could set MEAN_BERTH_HOURS = 24.0 and this
    # function went on returning 57.6. The control printed DOES NOT FIRE and
    # was right to.
    if berth_h is None:
        berth_h = MEAN_BERTH_HOURS
    return bay_count(schema) * 24.0 / berth_h


# ===========================================================================
# 2.  The daily manifest -- section 5.2, PROPOSED (T-05), authority 5
# ===========================================================================

# Reasoned in the gazetteer to hit 55 arrivals a day, the 95/5 civilian split
# and section 3.3's three size tiers. Percentages there are of arrivals.
#
# `berth` is one of section 3.3's tiers and it is not decoration: a bay-class
# hull goes through the axial mouth and a bay elevator, a standoff-class hull is
# too long for the elevator and makes hull contact at a port, and a moored-class
# hull above ~400 m cannot contact an 8,047 m station without becoming a
# structural load case. Three tiers, three kinds of berth, one reason.
#
# (name, arrivals/day, berth tier, souls lo, souls hi, stay lo h, stay hi h)
MANIFEST = (
    ("freighter_bay", 20.0, "bay", 6, 15, 8.0, 14.0),
    ("transport", 14.0, "bay", 26, 86, 6.0, 12.0),
    ("shuttle", 12.0, "bay", 2, 20, 1.0, 4.0),
    # SPEC-CHANGE #3 (owner-approved 2026-08-04): the tanker split out of the
    # standoff freighters, 4.0 -> 3.7 + 0.3, so the daily total is UNCHANGED at
    # 55.0. The station imports ~2,000 t/day of consumables and burns fusion
    # slush it cannot make (LIFE-SUPPORT §1), so a fuel carrier had to be a
    # class rather than an unnamed freighter -- PLC-039 and PLC-120's checks
    # already name its arrival stepping up the slush wall, and a check naming a
    # ship class the manifest does not carry is a check that cannot pass.
    ("freighter_standoff", 3.7, "standoff", 10, 30, 12.0, 36.0),
    ("tanker", 0.3, "standoff", 3, 8, 12.0, 24.0),
    ("diplomatic", 2.0, "standoff", 1, 12, 48.0, 96.0),
    ("liner", 0.5, "bay", 400, 800, 4.0, 8.0),
    ("ef_transport", 2.0, "bay", 20, 200, 6.0, 24.0),
    ("ef_warship", 0.3, "moored", 0, 0, 24.0, 72.0),
    ("alien_warship", 0.2, "moored", 0, 0, 24.0, 48.0),
)

# Section 3.3. The ~100 m bay limit is PROPOSED (T-03) and derived in §10; the
# other two bounds follow from it and from the moored-class argument.
BERTH_TIERS = {
    "bay": (0.0, 100.0, "one of the rotating docking bays, via the axial "
                        "mouth and a bay elevator"),
    "standoff": (100.0, 400.0, "the low-g bays on the non-rotating spine, or "
                               "the primary and service docking ports"),
    "moored": (400.0, float("inf"), "hard docking mooring clamps, or free "
                                    "station-keeping with lighters"),
}

# Ships whose crew stay aboard. §5.2: a warship's "crew stays aboard; liberty
# parties by shuttle", so it lands nobody through customs directly -- its people
# arrive as extra shuttle movements, which the manifest already counts.
CREW_STAYS_ABOARD = ("ef_warship", "alien_warship")


def manifest_arrivals_per_day() -> float:
    return sum(row[1] for row in MANIFEST)


def manifest_souls_per_day() -> float:
    """Inbound people a day, from the manifest's own midpoints."""
    return sum(n * (lo + hi) / 2.0
               for name, n, _b, lo, hi, _s0, _s1 in MANIFEST
               if name not in CREW_STAYS_ABOARD)


def mean_stay_h() -> float:
    """Arrival-weighted mean berth occupancy, from the manifest.

    This is the number `MEAN_BERTH_HOURS` claims to be, computed from the rows
    instead of asserted -- so the manifest and the tempo cannot drift apart
    without `_selftest` noticing.
    """
    n = manifest_arrivals_per_day()
    return sum(a * (s0 + s1) / 2.0
               for _nm, a, _b, _l, _h, s0, s1 in MANIFEST) / n


# ===========================================================================
# 3.  The shape of the day -- section 5.4
# ===========================================================================

# THE STATION RUNS ON EARTH MEAN TIME. Authority 1, off the customs board in
# `reference/11-props-and-technology/`. So the peaks are EMT peaks and they are
# what make the port feel alive rather than uniform.
#
# (start EMT, end EMT, relative rate). The rates are the reciprocal of §5.4's
# stated intervals where it gives one -- "~1 movement/25 min" at night against
# "~1 per 8 min" at the morning peak is 3.1:1, and the file states the ratio as
# "about 3:1" -- so this table is the section's own numbers, not a curve fitted
# to them.
DAY_BANDS = (
    (0.0, 5.0, 0.32, "freight window -- cargo turns round while the "
                     "concourse sleeps"),
    (5.0, 8.0, 0.70, "dock crews change; the first shift"),
    (8.0, 12.0, 1.00, "peak. Scheduled passenger arrivals; the liner berths "
                      "here if it berths at all"),
    (12.0, 17.0, 0.72, "steady, mixed"),
    (17.0, 21.0, 0.95, "second peak, outbound. The Zocalo is busiest at "
                       "station-evening and the port empties into it"),
    (21.0, 24.0, 0.50, "falling"),
)
# §5.4 states it: "Peak-to-trough is about 3:1. Deliberately not more: the gate
# runs continuously and freight has no reason to prefer daylight, which is
# itself a nice alien-ness -- a port that never closes, laid over a human
# working day."
PEAK_TO_TROUGH = 3.0
# How far either side of a band edge the rate ramps, so the day is a curve
# rather than six steps. Authority 5, and small on purpose: the bands are the
# measurement and this only removes the discontinuity between them.
BAND_RAMP_H = 0.75


def _band_rate(hour: float) -> float:
    h = hour % 24.0
    for h0, h1, r, _why in DAY_BANDS:
        if h0 <= h < h1:
            return r
    return DAY_BANDS[-1][2]


def day_curve(hour: float) -> float:
    """Relative arrival rate at station hour `hour`. 1.0 at the morning peak.

    Ramped across band edges, so a ship does not appear at 07:59 at the night
    rate and at 08:01 at three times it. The ramp is cosmetic; the bands are
    the measurement.
    """
    h = hour % 24.0
    a = _band_rate(h)
    for h0, _h1, _r, _why in DAY_BANDS:
        d = min(abs(h - h0), abs(h - h0 + 24.0), abs(h - h0 - 24.0))
        if d < BAND_RAMP_H:
            b = _band_rate(h0 - 1e-6)
            c = _band_rate(h0)
            # smoothstep from b to c centred on the edge
            u = 0.5 + 0.5 * (h - h0) / BAND_RAMP_H
            u = max(0.0, min(1.0, u))
            u = u * u * (3.0 - 2.0 * u)
            return b + (c - b) * u
    return a


def _mean_curve(samples: int = 1440) -> float:
    return sum(day_curve(i * 24.0 / samples)
               for i in range(samples)) / samples


def rate_per_hour(hour: float) -> float:
    """Arrivals an hour at station hour `hour`, normalised to the manifest.

    The curve is RELATIVE and the manifest is ABSOLUTE, so the normalisation is
    over the whole day rather than by scaling the peak -- otherwise the day's
    total silently becomes whatever the curve's mean happens to be.
    """
    return (manifest_arrivals_per_day() / 24.0) * (day_curve(hour)
                                                   / _mean_curve())


# ===========================================================================
# 4.  A day's arrivals
# ===========================================================================

def _u(*parts) -> float:
    """`schedule`'s own blake2b draw. Never `random` -- a port that reshuffles
    itself between two runs cannot be regression-tested."""
    return sched._u("traffic", "/".join(str(p) for p in parts))


def _pick_type(x: float):
    """Manifest row for a uniform draw, by arrival share."""
    tot = manifest_arrivals_per_day()
    acc = 0.0
    for row in MANIFEST:
        acc += row[1] / tot
        if x <= acc:
            return row
    return MANIFEST[-1]


def _inverse_curve(u: float, samples: int = 2880) -> float:
    """The hour at cumulative fraction `u` of the day's arrivals.

    Inverse-transform sampling on `day_curve`, which is what puts the arrivals
    where the bands say they are instead of spreading them evenly. This is the
    single thing `schedule.arrival_times` does not do.
    """
    step = 24.0 / samples
    tot = sum(day_curve(i * step) for i in range(samples))
    acc = 0.0
    for i in range(samples):
        acc += day_curve(i * step)
        if acc / tot >= u:
            return i * step
    return 24.0 - step


def liner_today(day: int = 0) -> bool:
    """Is there a liner today? 0.5 a day, so about every other one.

    THE LINER IS THE EVENT. §5.2 says so in as many words -- "every other row is
    a trickle; a liner is 400-800 people through one customs hall in a couple of
    hours. Build the day around it."
    """
    rate = dict((r[0], r[1]) for r in MANIFEST)["liner"]
    return _u("liner", day) < rate


# One day's manifest is ~52 rows of pure arithmetic over `day`, and it is
# recomputed by every caller that wants to know what is in port. Measured by the
# dialogue agent: **1.7 s a call, and 31 s of a 31 s run** -- because an
# exchange asks the port what berthed, and there are a lot of exchanges.
#
# It is a PURE FUNCTION OF `day`, so the memo is sound rather than a risk:
# `_u(...)` is a blake2b of its arguments and nothing here reads the clock or a
# mutable global. 32 days is a month of station time and about 50 kB.
#
# The alternative the agent shipped -- a caller-side memo in `dialogue.py` --
# works and is in the wrong place: every other caller goes on paying. Six
# exchanges went 7.06 s -> 0.75 s cold and 0.01 s warm on the caller-side memo
# alone; this puts that in front of `traffic.py`'s other readers too.
@lru_cache(maxsize=32)
def arrivals(day: int = 0) -> list:
    """One station day's arrivals: when, what, where it berths, how many aboard.

    Deterministic in `day`. Returns dicts sorted by hour.

    MEMOISED -- see above. The returned list is SHARED between callers, so a
    caller that mutates it corrupts every later call. Nothing does today and
    the self-test asserts the identity so that a caller which starts to would
    be found by a test rather than by a wrong manifest three modules away.
    """
    n = int(round(manifest_arrivals_per_day()))
    out = []
    for i in range(n):
        row = _pick_type(_u("type", day, i))
        name, _rate, berth, lo, hi, s0, s1 = row
        if name == "liner" and not liner_today(day):
            # The half-a-day rate is realised as a day-level event, so a day
            # without one must not still land one from the per-arrival draw.
            row = _pick_type(_u("retype", day, i))
            name, _rate, berth, lo, hi, s0, s1 = row
        hour = _inverse_curve((i + 0.5) / n)
        souls = lo + (hi - lo) * _u("souls", day, i)
        stay = s0 + (s1 - s0) * _u("stay", day, i)
        out.append({"day": day, "hour": hour, "type": name, "berth": berth,
                    "souls": 0 if name in CREW_STAYS_ABOARD else int(souls),
                    "stay_h": stay})
    if liner_today(day) and not any(a["type"] == "liner" for a in out):
        # §5.4: "the liner berths here if it berths at all" -- the morning peak.
        out.append({"day": day, "hour": 9.5 + 2.0 * _u("linerhour", day),
                    "type": "liner", "berth": "bay",
                    "souls": int(400 + 400 * _u("linersouls", day)),
                    "stay_h": 4.0 + 4.0 * _u("linerstay", day)})
    out.sort(key=lambda a: a["hour"])
    return out


def berths_in_use(hour: float, day: int = 0) -> dict:
    """How many berths of each tier are occupied at `hour`.

    A ship arriving at `hour - stay` is still there. Wraps the previous day, so
    a freighter that berthed at 22:00 for fourteen hours is still alongside at
    06:00 -- which is most of what the night shift is looking at.
    """
    use = {k: 0 for k in BERTH_TIERS}
    for d in (day - 1, day):
        for a in arrivals(d):
            t0 = a["hour"] + (0.0 if d == day else -24.0)
            if t0 <= hour < t0 + a["stay_h"]:
                use[a["berth"]] += 1
    return use


# ===========================================================================
# 5.  Customs load
# ===========================================================================

def hall_rate(hour: float, day: int = 0) -> dict:
    """People a minute through ONE customs hall at `hour`.

    §5.4 gives the background as "~1 person a minute across both halls ...
    about 0.5 a minute per hall", and a liner as "600 passengers through one
    hall in 90 minutes -- 6.7 a minute, which is 13x the per-hall background."
    Both come out of this rather than being quoted: `background` is the day's
    souls spread on the same curve the ships are, and `liner` is whatever is
    actually alongside.
    """
    day_souls = manifest_souls_per_day()
    per_min = day_souls / (24.0 * 60.0) * (day_curve(hour) / _mean_curve())
    base = per_min / HALLS
    surge = 0.0
    for a in arrivals(day):
        if a["type"] != "liner":
            continue
        # A liner clears its passengers over 90 minutes from berthing.
        if a["hour"] <= hour < a["hour"] + 1.5:
            surge += a["souls"] / 90.0
    return {"background_per_min": base, "liner_per_min": surge,
            "total_per_min": base + surge,
            "multiple": (base + surge) / base if base else 0.0}


def cross_check(schema=None) -> dict:
    """Every number here against every number elsewhere that describes it.

    THIS IS THE POINT OF THE MODULE. Four independent comparisons, three of
    which nothing in the project could make before it existed.
    """
    m = movements_per_day(schema)
    lo, hi = SOURCED_MOVEMENTS_PER_DAY
    sched_souls = float(sched.ARRIVALS_PER_DAY) * float(sched.SOULS_PER_ARRIVAL)
    ours = manifest_souls_per_day()
    stay_days = 9.0                        # §5.3's stated mean stay
    transient = ours * stay_days
    return {
        # 1. berths x turnaround against the sourced band
        "derived_movements": m,
        "sourced_band": (lo, hi),
        "movements_in_band": lo <= m <= hi,
        # 2. the manifest's own arrival total against the same band
        "manifest_arrivals": manifest_arrivals_per_day(),
        # 3. the manifest's mean stay against the tempo's assumed berth hours
        "manifest_mean_stay_h": mean_stay_h(),
        "assumed_berth_h": MEAN_BERTH_HOURS,
        # 4. souls a day, two ways -- SEE C-012
        "manifest_souls_per_day": ours,
        "schedule_souls_per_day": sched_souls,
        "souls_ratio": sched_souls / ours if ours else 0.0,
        # 5. transient population against FACTIONS.md's 45,000
        "transient_population": transient,
        "factions_transient": 45_000.0,
    }


# ===========================================================================
# 6.  Report
# ===========================================================================

def report(out=print):
    schema, _profile = it.load()
    c = cross_check(schema)
    out(f"THE PORT: {bay_count(schema)} docking bays, {MEAN_BERTH_HOURS:.0f} h "
        f"mean occupancy")
    out(f"  derived {c['derived_movements']:.1f} movements/day against the "
        f"sourced {c['sourced_band'][0]:.0f}-{c['sourced_band'][1]:.0f} "
        f"-- {'INSIDE' if c['movements_in_band'] else 'OUTSIDE'} the band")
    out(f"  the manifest totals {c['manifest_arrivals']:.1f} arrivals/day at a "
        f"{c['manifest_mean_stay_h']:.1f} h mean stay against the "
        f"{c['assumed_berth_h']:.0f} h the tempo assumes")
    out("")
    out("SOULS A DAY, TWO WAYS -- and they disagree by a factor of "
        f"{c['souls_ratio']:.1f}. See C-012")
    out(f"  this manifest (TRAFFIC-AND-CUSTOMS 5.3): "
        f"{c['manifest_souls_per_day']:,.0f}")
    out(f"  npc/schedule.py ({sched.ARRIVALS_PER_DAY} arrivals x "
        f"{sched.SOULS_PER_ARRIVAL} souls): {c['schedule_souls_per_day']:,.0f}")
    out(f"  transient population at a 9-day stay: "
        f"{c['transient_population']:,.0f} against FACTIONS.md's "
        f"{c['factions_transient']:,.0f}")
    out("")
    out("THE SHAPE OF THE DAY -- EMT, authority 1 for the clock")
    for h0, h1, r, why in DAY_BANDS:
        out(f"  {h0:05.2f}-{h1:05.2f}  x{r:.2f}  "
            f"{rate_per_hour((h0 + h1) / 2.0):4.1f}/h  {why[:52]}")
    pk = max(day_curve(i / 60.0) for i in range(24 * 60))
    tr = min(day_curve(i / 60.0) for i in range(24 * 60))
    out(f"  peak-to-trough {pk / tr:.2f}:1 against the stated "
        f"{PEAK_TO_TROUGH:.0f}:1")
    out("")
    for d in (0, 1):
        a = arrivals(d)
        liner = [x for x in a if x["type"] == "liner"]
        out(f"DAY {d}: {len(a)} arrivals, {sum(x['souls'] for x in a):,} souls, "
            f"{'a LINER at %.1f h with %d aboard' % (liner[0]['hour'], liner[0]['souls']) if liner else 'no liner'}")
        for h in (4, 10, 18, 22):
            b = berths_in_use(float(h), d)
            hr = hall_rate(float(h), d)
            out(f"   {h:02d}h  berths bay {b['bay']:2d}/{bay_count(schema)} "
                f"standoff {b['standoff']} moored {b['moored']}  "
                f"customs {hr['total_per_min']:5.2f}/min a hall "
                f"(x{hr['multiple']:.1f})")
    if liner_today(0):
        peak = max((hall_rate(h / 4.0, 0)["total_per_min"]
                    for h in range(96)))
        out(f"  the liner peak is {peak:.1f} people a minute through one hall")


# ===========================================================================
# 7.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _selftest(out=print):                                       # noqa: C901
    global DAY_BANDS, MEAN_BERTH_HOURS
    del _FAILED[:]
    n = 0
    schema, _profile = it.load()
    c = cross_check(schema)

    n += 1
    check(bay_count(schema) == 24,
          "the bay count comes from the schema and is the Security Manual's 24",
          f"{bay_count(schema)}")
    n += 1
    check(c["movements_in_band"],
          "berths x turnaround lands inside the sourced 50-60 -- two unrelated "
          "sources agreeing on a quantity neither was computed to match",
          f"{c['derived_movements']:.1f}")
    n += 1
    check(abs(manifest_arrivals_per_day() - 55.0) < 1.0,
          "the manifest totals the 55 it was reasoned to",
          f"{manifest_arrivals_per_day()}")
    n += 1
    check(abs(mean_stay_h() - MEAN_BERTH_HOURS) < 4.0,
          "the manifest's own mean stay agrees with the berth occupancy the "
          "tempo assumes, so the two halves cannot drift apart",
          f"{mean_stay_h():.1f} h against {MEAN_BERTH_HOURS:.0f}")
    n += 1
    check(all(t in BERTH_TIERS for _n, _a, t, *_r in MANIFEST),
          "every manifest row berths in a declared tier")
    n += 1
    check(all(BERTH_TIERS[t][0] < BERTH_TIERS[t][1] for t in BERTH_TIERS),
          "the tiers are ordered bands, not overlapping labels")

    # -- the shape of the day -------------------------------------------
    n += 1
    pk = max(day_curve(i / 60.0) for i in range(24 * 60))
    tr = min(day_curve(i / 60.0) for i in range(24 * 60))
    check(2.0 <= pk / tr <= 4.0,
          "peak-to-trough is the stated ~3:1", f"{pk / tr:.2f}")
    n += 1
    check(day_curve(10.0) > day_curve(4.0)
          and day_curve(19.0) > day_curve(14.0),
          "THE DAY HAS TWO PEAKS. schedule.wave_pulse reads 1.0 at 10h and "
          "0.0 at 18h, so the evening one -- the outbound one, which is what "
          "fills the Zocalo -- was not modelled anywhere",
          f"04h {day_curve(4.0):.2f}, 10h {day_curve(10.0):.2f}, "
          f"14h {day_curve(14.0):.2f}, 19h {day_curve(19.0):.2f}")
    n += 1
    check(abs(sum(rate_per_hour(h + 0.5) for h in range(24))
              - manifest_arrivals_per_day()) < 1.0,
          "the curve integrates to the manifest's day, so shaping the day "
          "does not silently change how many ships come",
          f"{sum(rate_per_hour(h + 0.5) for h in range(24)):.2f}")

    # -- a day's arrivals ------------------------------------------------
    a0 = arrivals(0)
    n += 1
    check(len(a0) >= 55, "a day lands its manifest", f"{len(a0)}")
    n += 1
    check([x["hour"] for x in a0] == sorted(x["hour"] for x in a0),
          "arrivals come back in time order")
    n += 1
    check([x["type"] for x in arrivals(3)] == [x["type"] for x in arrivals(3)],
          "a day is deterministic in its number")
    n += 1
    check(arrivals(0) != arrivals(1), "and two days differ")
    n += 1
    morning = sum(1 for x in a0 if 8.0 <= x["hour"] < 12.0)
    night = sum(1 for x in a0 if 0.0 <= x["hour"] < 4.0)
    check(morning > night,
          "more ships arrive in the morning peak than in the freight window "
          "-- which is the whole reason the curve exists",
          f"{morning} against {night}")
    n += 1
    check(all(x["souls"] == 0 for x in a0
              if x["type"] in CREW_STAYS_ABOARD),
          "a warship lands nobody through customs -- its crew stays aboard "
          "and liberty parties arrive as shuttle movements")

    # -- berths -----------------------------------------------------------
    n += 1
    worst = max(berths_in_use(h / 4.0, 0)["bay"] for h in range(96))
    check(worst <= bay_count(schema),
          "the port never berths more bay-class hulls than it has bays",
          f"{worst} of {bay_count(schema)}")
    n += 1
    check(worst >= 4,
          "and it is not empty either", f"{worst}")

    # -- customs ----------------------------------------------------------
    n += 1
    base = hall_rate(3.0, 0)["background_per_min"]
    check(0.05 <= base <= 2.0,
          "the night background is a trickle through one hall, order half a "
          "person a minute", f"{base:.3f}/min")
    n += 1
    lday = next((d for d in range(8) if liner_today(d)), None)
    check(lday is not None, "a liner turns up within a week")
    if lday is not None:
        n += 1
        la = next(x for x in arrivals(lday) if x["type"] == "liner")
        peak = max(hall_rate(la["hour"] + i / 60.0, lday)["multiple"]
                   for i in range(0, 80, 5))
        check(peak >= 5.0,
              "A LINER IS THE EVENT: it puts several times the background "
              "through one hall, which is the crowdedness-and-isolation axis "
              "the owner named and a uniform stream cannot produce",
              f"x{peak:.1f} at {la['hour']:.1f} h with {la['souls']} aboard")

    # -- the file is actually read ---------------------------------------
    n += 1
    check(os.path.exists(GAZETTEER), "the gazetteer is where it says it is")
    if os.path.exists(GAZETTEER):
        txt = open(GAZETTEER).read()
        for phrase in ("50 to 60 ships", "Peak-to-trough",
                       "The liner is the event"):
            n += 1
            check(phrase.lower() in txt.lower(),
                  f"the gazetteer still says {phrase!r}")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")

    keep = DAY_BANDS
    try:
        DAY_BANDS = tuple((h0, h1, 1.0, w) for h0, h1, _r, w in DAY_BANDS)
        flat_pk = max(day_curve(i / 60.0) for i in range(24 * 60))
        flat_tr = min(day_curve(i / 60.0) for i in range(24 * 60))
        # A MEMO DEFEATS EVERY CONTROL THAT PATCHES A GLOBAL THE MEMOISED
        # FUNCTION READS, and this one caught it on the first run: with
        # `arrivals` newly `@lru_cache`d, flattening `DAY_BANDS` and asking
        # again returned the SHAPED day out of the cache and the gate reported
        # "3.50 against 3.50 -- DOES NOT FIRE". The control was right and the
        # cache made it blind.
        #
        # This is the same defect class CLAUDE.md already records for
        # `movements_per_day(berth_h=MEAN_BERTH_HOURS)`, whose default bound at
        # def time so the control could set the module global and change
        # nothing. A cache is that, generalised: any negative control that
        # patches state a cached function reads MUST clear the cache, and any
        # cache added to this module must be cleared here.
        arrivals.cache_clear()
        flat = arrivals(0)
        f_morning = sum(1 for x in flat if 8.0 <= x["hour"] < 12.0)
        f_night = sum(1 for x in flat if 0.0 <= x["hour"] < 4.0)
        ctl_a = not (2.0 <= flat_pk / flat_tr <= 4.0)
        # THE RATIO, NOT THE COUNTS. Fifty-five discrete arrivals over two
        # four-hour windows is a small sample and a flat day still comes back
        # 11 against 9 -- so a "morning <= night" control fails for a reason
        # that has nothing to do with the curve. What must collapse is the
        # RATIO, and it does: 3.50 shaped against 1.22 flat.
        shaped_ratio = morning / max(1, night)
        flat_ratio = f_morning / max(1, f_night)
        ctl_b = flat_ratio < shaped_ratio / 2.0
        out(f"  flatten the day -> peak-to-trough {flat_pk / flat_tr:.2f}:1 "
            f"(was {pk / tr:.2f}) -- shape gate "
            f"{'FIRES' if ctl_a else 'DOES NOT FIRE'}; morning/night "
            f"{flat_ratio:.2f} (was {shaped_ratio:.2f}) -- peak gate "
            f"{'FIRES' if ctl_b else 'DOES NOT FIRE'}")
        n += 2
        check(ctl_a, "the peak-to-trough gate fires on a flat day")
        check(ctl_b, "and the morning/night ratio collapses with it",
              f"{flat_ratio:.2f} against {shaped_ratio:.2f}")
    finally:
        DAY_BANDS = keep
        arrivals.cache_clear()          # and restore the real day for later gates

    keeph = MEAN_BERTH_HOURS
    try:
        MEAN_BERTH_HOURS = 24.0
        m2 = movements_per_day(schema)
        lo, hi = SOURCED_MOVEMENTS_PER_DAY
        ctl_c = not (lo <= m2 <= hi)
        out(f"  a 24 h turnaround -> {m2:.1f} movements/day -- the sourced "
            f"band gate {'FIRES' if ctl_c else 'DOES NOT FIRE'} "
            f"(the agreement at 10 h is evidence, not an identity)")
        n += 1
        check(ctl_c, "the sourced-band gate fires at the wrong turnaround")
    finally:
        MEAN_BERTH_HOURS = keeph

    # -- THE MEMO IS SOUND, AND THE SHARING IS THE RISK ---------------------
    # `arrivals` is `@lru_cache`d because it cost 1.7 s a call and 31 s of a
    # 31 s dialogue run. That is only safe while it stays a pure function of
    # `day` AND no caller mutates what it hands back -- the list is SHARED.
    _a0, _a1 = arrivals(0), arrivals(0)
    check("arrivals is memoised -- the same day returns the SAME list",
          _a0 is _a1)
    check("...and two different days do not", arrivals(0) is not arrivals(1))
    check("...and the memo did not change the manifest",
          [r["hour"] for r in arrivals(3)]
          == sorted(r["hour"] for r in arrivals(3)))
    # The control on the sharing hazard, run rather than described: mutate the
    # returned list and the next call sees it. That is the cost of the memo and
    # it is stated here so a caller who starts mutating is caught by this
    # rather than by a wrong manifest three modules away.
    _n0 = len(arrivals(7))
    arrivals(7).append({"__probe__": True})
    _shared = len(arrivals(7)) != _n0
    arrivals(7).pop()
    check("...and a caller that MUTATES the list corrupts every later call, "
          "which is why nothing may", _shared,
          "the list is copied per call -- then the memo is not what this "
          "assertion describes")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


if __name__ == "__main__":                                   # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.report:
        ok = _selftest()
        if a.report:
            print()
            report()
        raise SystemExit(0 if ok else 1)
    report()
