"""NPC schedules, the species mix, and the statistical population layer.

A quarter of a million residents cannot all be simulated as agents, cannot all
be meshes, and cannot all be *records* either. The standard answer is simulation
LOD: full agents near the player, statistical abstraction everywhere else, with
individuals promoted and demoted as the player moves. What makes it work rather
than merely cheap is that the abstract layer has to produce the *same* aggregate
behaviour the detailed layer would -- if a district's population drops when
nobody is looking, the player will notice the moment they walk back in. That
claim is now asserted rather than asserted-in-prose: see `activity_profile()`
and the sampling-error test in `test_schedule.py`.

Schedules are driven by station time, which is not Earth time -- except that it
is. The customs board is authority 1 and says so verbatim: "TIME ON B-5 IS EARTH
MEAN TIME (EMT)" (`station/signage.py`, `BOARDS["customs_procedures"]`). The
station runs a 24-hour cycle for human convenience in a lit-from-within habitat
where neither day nor night is astronomically meaningful, so "night" is a
decision the station makes, and the species aboard do not all agree with it.

ERA DATUM
---------
**S3, pre-martial-law** -- between S3E02 *Convictions* and S3E09 *Point of No
Return*, early 2260. Set by `docs/gazetteer/FACTIONS.md` §1.3, which also shows
why `canon/00-MASTER.md`'s era-lock line cannot be satisfied as written: "all
League ambassadors resident" requires a date before S2E18 (the Markab die) and
the Nightwatch layer requires a date after S2E22. This module is written to the
datum, which is why **Markab are zero** and why the Narn population is a
refugee population rather than a trading one.

WHAT CHANGED, AND WHY IT MATTERED
---------------------------------
`STATION_MIX` was six species. INV-005 records that an EARLIER version of it
summed to 0.94 and silently dropped 120 of every 2,000 residents; the version
this session found summed to 1.00, so the leak had been fixed and the defence
against it had not been. Both halves of that defence now exist:

  1. The sum was checked by eye, and by a test with a **0.06 tolerance** --
     which is wide enough for a 0.94 mix to walk straight through the assertion
     written to catch it. `population_activity()` now *raises* on a mix that
     does not sum to 1, the tolerance is 1e-9, and the counts are integers
     summing to exactly 250,000.
  2. Apportionment was `int(total * share)`, which truncates. Flooring fourteen
     shares loses up to thirteen people per call and loses them again every
     station-hour, because the aggregate layer is recomputed from the same
     shares. Replaced with integer largest-remainder apportionment, which sums
     to `total` exactly for *every* total, not just the convenient ones.

Six species cannot read as a galactic port. The mix is now fifteen, from
FACTIONS.md §2.4, and the Vorlon is a hard-coded singleton because `int(250000 *
share)` for one person is a rounding artefact waiting to become zero or three.

Deterministic throughout: `hashlib.blake2b`, never `random`, never
`str.__hash__` (salted per process). An NPC's schedule is a function of its id,
so the same resident does the same thing at the same time in every session and
on every machine.

COST -- read `PERFORMANCE` at the foot of this file before adding anything.
"""
import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache


class Activity(Enum):
    SLEEP = "sleep"
    WORK = "work"
    EAT = "eat"
    COMMERCE = "commerce"      # Zocalo, markets, shopping
    RECREATION = "recreation"  # bars, casino, gardens
    WORSHIP = "worship"
    TRANSIT = "transit"        # in a lift or on the core shuttle
    IDLE = "idle"


def _u(seed: str, salt: str = "") -> float:
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ---------------------------------------------------------------------------
# Atmospheres
# ---------------------------------------------------------------------------
# The customs board is authority 1 and establishes the whole mechanic:
# "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5. OTHERS MAY BE
# CREATED BY PRIOR ARANGEMENT [sic]. UNCOMMON ATMOSPHERIC MAKEUPS MAY BE
# SYNTHESIZED FOR ENCOUNTER SUITS." -- station/signage.py, transcribed from
# reference/01-station-exterior/welcome to babylon 5.webp.
#
# The identicard prop numbers exactly one of the six: `DES/ATMOS: HUMAN/02`.
# NOTHING NUMBERS ANY OF THE OTHERS, so this module deliberately does not
# invent numbers for them. A species carries an atmosphere *class*; the alien
# sector's signage layer can attach numbers to classes when a source turns up,
# and until then a wrong number never gets printed on a wall.
#
# The count of distinct classes is asserted against the board's SIX in
# test_schedule.py -- a cross-module check, because a fifteen-species mix is
# exactly the kind of change that quietly needs a seventh atmosphere.
ATMOS_STANDARD = "standard_oxygen"   # numbered 02 for humans, authority 1
ATMOS_HUMID = "humid_oxygen"         # amphibian; a humidity variant, not a new gas
ATMOS_METHANE = "methane"            # Gaim; encounter suits outside their own quarter
ATMOS_UNDISCLOSED = "undisclosed"    # Vorlon; the suit is the whole point


@dataclass(frozen=True)
class SpeciesRhythm:
    """How a species divides its day.

    Hours are station-clock hours (Earth Mean Time, authority 1). Species
    differ enough that a corridor at 03:00 should not be empty -- it should be
    full of whoever is awake then, which is a specific and different crowd from
    the one at 13:00. With fifteen species that is now a real claim: Brakiri
    are night dwellers, so station-night has a *commercial* crowd rather than
    only a residual one.

    `jitter` scales individual variation. A hive-caste species does not scatter
    the way a bucket of one-off traders does, and the tail bucket has to
    scatter widest of all or it reads as a fifteenth species.
    """
    species: str
    sleep_start: float
    sleep_hours: float
    meals: tuple               # station-clock hours
    note: str
    atmos: str = ATMOS_STANDARD
    breather: str = "none"     # "none" | "mask" | "suit"
    jitter: float = 1.0        # multiplier on individual scatter
    auth: str = "5"


RHYTHMS = {
    # --- the original six, numbers UNCHANGED (INV-005) ----------------------
    # Humans set the station clock, so their rhythm is the reference against
    # which every other species reads as unusual.
    "human": SpeciesRhythm("human", 23.0, 7.5, (7.0, 12.5, 19.0),
                           "Sets the station clock. Three meals, one long sleep.",
                           auth="1 for the clock (customs board), 5 for the rhythm"),
    # Minbari famously do not sleep the whole night through -- the show
    # establishes they wake for a period in the middle. That produces a real
    # and visible effect: Minbari abroad in corridors at hours nobody else is.
    "minbari": SpeciesRhythm("minbari", 22.5, 4.0, (8.0, 18.0),
                             "Sleep is broken -- a waking period mid-rest is canon, so "
                             "Minbari are abroad at hours no one else is.",
                             auth="1 (dagger) for broken sleep"),
    # Genuinely nocturnal: retiring at 01:30 would still leave them asleep
    # through the small hours, which is not what "nocturnal" means. They go
    # down near dawn and are the crowd still in the bars at 03:00.
    "centauri": SpeciesRhythm("centauri", 4.5, 6.5, (12.0, 17.0, 23.0),
                              "Late rhythm -- retires near dawn. Heavy recreation weighting; "
                              "Centauri social life is depicted as nocturnal and "
                              "drink-centred."),
    "narn": SpeciesRhythm("narn", 21.5, 8.0, (6.0, 13.0, 19.5),
                          "Early and regimented, consistent with the Regime's depicted "
                          "military discipline."),
    "drazi": SpeciesRhythm("drazi", 0.5, 6.5, (9.0, 20.0),
                           "Two large meals rather than three."),
    # pak'ma'ra are carrion eaters, which the show treats as a source of
    # friction with other species. Feeding at hours when public spaces are
    # empty is an inference from that friction, logged as such.
    "pakmara": SpeciesRhythm("pakmara", 20.0, 9.0, (4.0, 16.0),
                             "Long sleep. Feeding placed at low-traffic hours -- INFERRED "
                             "from the depicted friction over their diet, not stated. "
                             "The only species with a segregated food economy "
                             "(FACTIONS.md 12).",
                             jitter=1.1),

    # --- the nine added with the researched mix (FACTIONS.md 2.4, 9.2) ------
    # The single most consequential addition. "Night dwellers" is authority 4
    # (fandom, League of Non-Aligned Worlds) and it is the only rhythm claim in
    # the whole file that comes from a source rather than from us. It buys the
    # station a commercial night: the Business District, the Casino and the
    # Zocalo hold a *working* Brakiri crowd at 02:00, not a residue.
    "brakiri": SpeciesRhythm("brakiri", 9.0, 7.0, (17.0, 22.5, 3.5),
                             "NIGHT DWELLERS -- authority 4, FACTIONS.md 9.2. Sleeps "
                             "through the station day and trades through its night. This "
                             "is what gives station-night a crowd of its own.",
                             auth="4 for nocturnality, 5 for the hours"),
    "vree": SpeciesRhythm("vree", 23.5, 6.0, (8.0, 19.0),
                          "Traders working human-facing market hours, so the rhythm sits "
                          "close to the station clock. No source states anything about "
                          "Vree sleep; the hours are ours.",
                          jitter=1.2),
    # Amphibian, which is why they matter to the atmosphere system rather than
    # only to the crowd: an amphibian species needs a humidity variant, and the
    # customs board says uncommon makeups are synthesized to order.
    "abbai": SpeciesRhythm("abbai", 22.0, 7.0, (7.0, 12.0, 18.5),
                           "Amphibian (authority 4) -- humid quarters in the Alien Sector "
                           "and Hydroponics work. Rest is taken in water, so the sleep "
                           "block is at a fixed place rather than merely a fixed hour.",
                           atmos=ATMOS_HUMID, breather="mask",
                           auth="4 for amphibian, 5 for the hours"),
    # Methane breathers in encounter suits. The suit is the schedule: a Gaim
    # cannot eat outside its own atmosphere, so meals bracket the working
    # period instead of interrupting it, and the Alien Sector is somewhere it
    # has to physically return to. That is the reason the Alien Sector exists
    # as a place a player can find rather than a label on a plan.
    "gaim": SpeciesRhythm("gaim", 1.0, 5.0, (6.5, 17.5),
                          "Methane breathers in encounter suits (authority 4). A Gaim "
                          "cannot eat outside its own atmosphere, so the two meals "
                          "BRACKET the shift and are taken in the Alien Sector. Hive "
                          "caste -- very little individual scatter.",
                          atmos=ATMOS_METHANE, breather="suit", jitter=0.35,
                          auth="4 for methane and suits, 5 for the hours"),
    "hyach": SpeciesRhythm("hyach", 21.0, 6.0, (6.5, 12.0, 18.0),
                           "Long-lived and formal (authority 4). Modelled as an early, "
                           "invariant rhythm with little scatter -- formality is legible "
                           "in a crowd as everyone doing the same thing at once.",
                           jitter=0.4, auth="4 for formality, 5 for the hours"),
    "llort": SpeciesRhythm("llort", 8.0, 6.0, (15.0, 1.5),
                           "Scavengers and thieves by reputation (authority 4). Sleeps "
                           "through the morning and works the margins of the market day "
                           "and the small hours -- the rhythm IS the crime layer.",
                           jitter=1.3, auth="4 for the reputation, 5 for the hours"),
    "grome": SpeciesRhythm("grome", 20.5, 8.0, (4.5, 11.5, 18.0),
                           "No character is established for the Grome anywhere. Aligned "
                           "to the agricultural shift they work -- Hydroponics runs "
                           "05:00-13:00 (FACTIONS.md 2.5), which is not an office day."),
    # The tail. FACTIONS.md 2.4: "give this bucket a rotating model set so the
    # tail never looks like the same six aliens". The schedule equivalent is a
    # very wide jitter: no two members of the bucket keep the same hours, so it
    # cannot read as a fifteenth species with a fifteenth rhythm.
    "other": SpeciesRhythm("other", 23.0, 7.0, (7.5, 13.0, 19.0),
                           "Rare League species, unidentified traders, one-off visitors. "
                           "WIDE individual scatter is the point -- the bucket must not "
                           "read as one more species.",
                           jitter=3.0),
    # Kosh. Not in STATION_MIX -- see VORLON_SINGLETON. He gets a rhythm anyway
    # because he is a person who has to be somewhere, and "almost never seen"
    # is a schedule: in seclusion twenty hours a day, abroad in the evening,
    # and the corridor clears when he moves (FACTIONS.md 12, authority 1
    # dagger). No meals: nothing has ever shown a Vorlon eat.
    "vorlon": SpeciesRhythm("vorlon", 0.0, 20.0, (),
                            "Kosh. 'Almost never seen. When he moves, the corridor clears "
                            "without being told to' -- FACTIONS.md 12. Modelled as "
                            "seclusion for twenty hours. No meals: none is ever depicted.",
                            atmos=ATMOS_UNDISCLOSED, breather="suit", jitter=0.0,
                            auth="1 (dagger) for the seclusion, 5 for the hours"),
}


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Role:
    """What an NPC does, which drives where they are during work hours."""
    key: str
    work_start: float
    work_hours: float
    workplace: str
    note: str = ""


# Workplaces that run around the clock. Members are spread across three watches
# by `shift_offset()` rather than all starting together. Every entry here is
# sourced to a sentence in FACTIONS.md rather than assumed:
#
#   patrol           "Three shifts" over 500 officers (2.2); Security Central 24 h (2.5)
#   medlab           Medlab One, 24 h (2.5)
#   cnc              "Three watches in Observation Dome 1 plus staff" (2.2)
#   traffic_control  "28 bays on three shifts" (2.2); docking bays 24 h (2.5)
#   grey_industrial  "Fabrication furnaces, power, repair ... 24 h, 3 shifts" (2.5)
#   waste_management Waste Management Control, the plant Downbelow lives beside (11.2)
#   customs_hall     "Two customs halls on three shifts is most of it" (2.2)
#   hospitality      Earhart's is busy 19:00-02:00 and the Dark Star 21:00-04:00 (2.5),
#                    so hospitality cannot be one day shift
ROTATING_WORKPLACES = frozenset({
    "patrol", "medlab", "cnc", "traffic_control", "grey_industrial",
    "waste_management", "customs_hall", "hospitality",
})

# The reference watch. A rotating role's declared `work_start` is its DAY watch,
# and the other two are +8 and +16 -- not "watch one starts at midnight", which
# is what the table used to say and is what put the night watch to bed. See
# `activity_at`. Asserted against ROLES in test_schedule.py.
REF_WORK_START = 8.0

ROLES = (
    # Deliberately NOT rotating. FACTIONS.md 2.5 gives Dock Workers' Quarters
    # two busy windows, 06:00-08:00 and 15:00-17:00, and no dead window. A
    # 06:00 start with a 9 h day puts the shift boundaries at exactly 06:00 and
    # 15:00, so the two observed surges ARE this shift's ends. Three rotating
    # dock shifts would have produced a third surge at 22:00 that the source
    # does not show. The bays are still manned 24 h -- by `traffic`.
    Role("dockworker", 6.0, 9.0, "docking_bay",
         "Day shift 06:00-15:00; reproduces the two quarters surges in 2.5"),
    Role("traffic", REF_WORK_START, 8.0, "traffic_control",
         "Three watches; keeps the 24 bays manned through the night"),
    Role("security", REF_WORK_START, 8.0, "patrol",
         "500 officers, 3 watches -- ~150 on duty across 8,047 m (2.2)"),
    Role("customs", REF_WORK_START, 8.0, "customs_hall",
         "Two halls, three shifts, ~12,600 transactions/day (2.2, 2.3)"),
    Role("merchant", 9.0, 11.0, "zocalo"),
    Role("financier", 9.0, 8.0, "business_district",
         "Rigid human office hours in a station with no day (2.5) -- and the "
         "Brakiri keep the same hours in their own frame, which puts them on "
         "the night side of the same market"),
    Role("engineer", 7.0, 9.0, "engineering"),
    Role("industrial", REF_WORK_START, 8.0, "grey_industrial",
         "Grey holds 90 of the station's 210 decks; 24 h, 3 shifts (2.5)"),
    Role("waste", REF_WORK_START, 8.0, "waste_management",
         "The plant Downbelow is built around (11.2)"),
    Role("hydroponics", 5.0, 8.0, "hydroponics",
         "Agricultural shift 05:00-13:00, not an office shift (2.5)"),
    Role("medical", REF_WORK_START, 12.0, "medlab"),
    Role("diplomat", 10.0, 7.0, "green_sector"),
    Role("command", REF_WORK_START, 8.0, "cnc",
         "Three watches in Observation Dome 1 (2.2)"),
    Role("cleric", 6.0, 8.0, "sanctuary",
         "Four Sanctuaries (authority 3) plus Brother Theo's resident order "
         "(11.3). Gives Activity.WORSHIP a destination it did not have"),
    Role("service", REF_WORK_START, 9.0, "hospitality"),
    # One person, two hours. "Almost never seen" is a schedule, and this is it.
    Role("envoy", 10.0, 2.0, "council_chamber",
         "Kosh. A two-hour public day; the rest is seclusion (FACTIONS.md 12)"),
    # Two different kinds of not-working, and they are not interchangeable.
    Role("visitor", 0.0, 0.0, "concourse",
         "~45,000 transients in port at any time, mean stay 7 days (2.3). No "
         "job aboard: they shop, eat, queue and wait for a berth"),
    Role("refugee", 0.0, 0.0, "refugee_reception",
         "13,000 Narn after the surrender (6.2). Queuing and waiting is not "
         "leisure and is not lurking"),
    Role("lurker", 0.0, 0.0, "downbelow",
         "Downbelow's unemployed -- no work hours at all"),
)

ROLES_BY_KEY = {r.key: r for r in ROLES}


# Per-species role weights, expressed as HEADCOUNTS so the table is readable and
# so it can be checked: each species' weights sum to that species' count in
# STATION_COUNTS, which makes the role table an apportionment of the mix rather
# than an unrelated set of preferences. Asserted in test_schedule.py.
#
# Three of these are transcriptions of an explicit apportionment in the source
# and are marked as such; the rest follow FACTIONS.md 9.2's "where they
# cluster" column and are ours.
ROLE_WEIGHTS = {
    # EA staffing is FACTIONS.md 2.2's apportionment of the 6,500 -- command
    # 120, security 500, medical 300, flight ops 350, engineering 1,800,
    # docking/cargo/traffic 1,200, hydroponics/water/waste 700, administration
    # and customs 900, maintenance 630. Every one of those is human here,
    # because 2.4's argument for the 62% human share is structural: EA law, EA
    # currency, EA contracts, so EA jobs. The civilian remainder (148,500) is
    # ours, anchored on 11.2's ~13,500 human lurkers and 2.3's transient block.
    "human": {"command": 120, "security": 500, "medical": 2800, "dockworker": 1150,
              "traffic": 400, "engineer": 10430, "hydroponics": 1100, "waste": 300,
              "customs": 900, "industrial": 18000, "merchant": 26000, "service": 39000,
              "financier": 9000, "cleric": 300, "diplomat": 500, "visitor": 31000,
              "lurker": 13500},
    # TRANSCRIBED from FACTIONS.md 6.2: G'Kar's household 30, resident traders
    # and shipping agents 6,000, refugees 13,000, Downbelow 2,470, transient
    # crews 1,000. The refugee block is the largest single role assignment of
    # any species aboard and it did not exist eighteen months before the datum.
    "narn": {"diplomat": 30, "merchant": 6000, "refugee": 13000, "lurker": 2470,
             "visitor": 1000},
    # TRANSCRIBED from FACTIONS.md 7.2: mission 150, merchants/shippers/
    # financiers 11,000, transients 5,000, Downbelow 1,350.
    "centauri": {"diplomat": 150, "financier": 11000, "visitor": 5000, "lurker": 1350},
    # TRANSCRIBED from FACTIONS.md 8.1: religious ~7,000, worker ~4,000,
    # warrior ~600, mission staff ~80, transient ~800, Downbelow ~20. Warrior
    # caste and mission staff are merged into `diplomat` because what they do
    # aboard is escort and legation duty at the diplomatic berths -- they are
    # emphatically not station security.
    "minbari": {"cleric": 7000, "engineer": 4000, "diplomat": 680, "visitor": 800,
                "lurker": 20},
    "drazi": {"dockworker": 4500, "industrial": 3000, "service": 1500, "merchant": 1200,
              "visitor": 1500, "lurker": 800},
    "brakiri": {"financier": 3000, "merchant": 2500, "service": 800, "visitor": 1000,
                "lurker": 200},
    "pakmara": {"waste": 2200, "dockworker": 1500, "lurker": 1400, "service": 600,
                "visitor": 550},
    "vree": {"merchant": 2000, "dockworker": 1200, "visitor": 1400, "service": 400},
    "abbai": {"hydroponics": 1400, "diplomat": 350, "service": 700, "merchant": 600,
              "visitor": 700},
    "gaim": {"industrial": 900, "dockworker": 800, "visitor": 500, "diplomat": 100,
             "merchant": 200},
    "hyach": {"financier": 700, "diplomat": 250, "merchant": 300, "visitor": 500},
    "llort": {"lurker": 500, "dockworker": 300, "merchant": 250, "visitor": 200},
    "grome": {"hydroponics": 350, "industrial": 200, "visitor": 120, "service": 80},
    "other": {"visitor": 500, "merchant": 250, "dockworker": 200, "service": 150,
              "lurker": 150},
    # One person, one job.
    "vorlon": {"envoy": 1},
}


def role_for(npc_id: str, species: str = "human") -> Role:
    """Which role this NPC holds, weighted by species.

    Was a uniform draw over nine roles for every species alike, which put as
    many Gaim in Command and Control as humans and gave 11% of the station a
    security uniform. The weights come from FACTIONS.md's apportionments, and
    the consequence is the one 2.2 asks for: security is 500 of 155,000
    humans, so a crowd almost never contains a uniform, and the two places
    that always do are chokepoints.
    """
    weights = ROLE_WEIGHTS.get(species) or ROLE_WEIGHTS["human"]
    total = sum(weights.values())
    x = _u(npc_id, "role") * total
    acc = 0.0
    for key, w in weights.items():           # insertion order, deterministic
        acc += w
        if x < acc:
            return ROLES_BY_KEY[key]
    return ROLES_BY_KEY[next(reversed(weights))]   # float slop at the top end


def role_headcount(counts=None) -> dict:
    """Station-wide heads per role, summed over the species mix.

    This is the table `ROLE_WEIGHTS` exists to produce, and it is checkable
    against FACTIONS.md's own numbers: security 500 (2.2), refugees 13,000
    (6.2), lurkers ~20,000 (2.2, 11.2), transients ~45,000 (2.2, 2.3).
    """
    counts = STATION_COUNTS if counts is None else counts
    out = {r.key: 0 for r in ROLES}
    for species in list(counts) + ["vorlon"]:
        for key, w in ROLE_WEIGHTS.get(species, {}).items():
            out[key] += w
    return out


def shift_offset(npc_id: str, role: Role) -> float:
    """Hours to shift a rotating-roster role.

    Security, medical, C&C, traffic, the furnaces, the waste plant and the two
    customs halls all run around the clock, so their members are spread across
    three watches rather than all starting together. Without this the station
    is visibly unguarded, unstaffed and unlit-by-anyone for sixteen hours a day.
    """
    if role.workplace not in ROTATING_WORKPLACES:
        return 0.0
    return 8.0 * (int(_u(npc_id, "shift") * 3) % 3)


MEAL_HALF_WINDOW_H = 0.3     # 0.6 h of meal, centred -- see the note in activity_at
TRANSIT_H = 0.5              # each way; see the note in activity_at


def wake_hour(species: str) -> float:
    """When a species' day begins: the end of its sleep block."""
    r = RHYTHMS.get(species, RHYTHMS["human"])
    return (r.sleep_start + r.sleep_hours) % 24.0


# How long before a shift starts its holder is up. DERIVED, not chosen: humans
# wake at 06:30 and the reference watch starts at 08:00, so it is 1.5 h, and
# changing either of those changes it.
PRE_SHIFT_H = REF_WORK_START - (RHYTHMS["human"].sleep_start
                                + RHYTHMS["human"].sleep_hours) % 24.0


def species_work_shift(species: str) -> float:
    """Hours to move a role's (human-frame) working day into a species' frame.

    Roles are written in human hours because the station's clock is human --
    Earth Mean Time, authority 1. A species that wakes at 16:00 does not start
    its shift at 08:00; it starts 9.5 h later. Derived from the rhythms rather
    than tabulated, so a rhythm edit cannot leave a stale offset behind.

    The consequence worth naming: a Brakiri financier works 18:30-02:30, which
    is what "night dwellers who are traders and financiers" has to mean. The
    Business District therefore has a human day shift and a Brakiri night
    shift in the same rooms, and station-night gets a WORKING crowd instead of
    a residual one.
    """
    return (wake_hour(species) - wake_hour("human")) % 24.0


def _in_window(hour: float, start: float, length: float) -> bool:
    if length <= 0.0:
        return False
    if length >= 24.0:
        return True
    a = start % 24.0
    b = (a + length) % 24.0
    return (a < b and a <= hour < b) or (a > b and (hour >= a or hour < b))


def day_offset(npc_id: str, species: str, role: Role) -> float:
    """How far this individual's whole day is displaced from their species'.

    Two contributions, and no others: how far the role's start deviates from
    the reference watch, and which of the three watches they are on. Sleep and
    meals move by exactly this, work moves by this plus `species_work_shift`.

    THIS IS THE FIX FOR THE BUG INV-005 RECORDS, AND THE PREVIOUS FIX WAS
    INCOMPLETE. Shifting sleep by the rotation alone still put the night watch
    to bed, because the rotating roles declared `work_start = 0.0`: watch one
    ran 00:00-08:00 while the human sleep block ran 23:00-06:30, so 7.5 of a
    watch's 8 hours were spent asleep. Nothing failed, because the only
    assertion was `on_duty > 0` and jitter left a handful of officers standing.
    Sleep is now anchored to the holder's own shift by construction:

        sleep ends  PRE_SHIFT_H  before work starts, always.

    The algebra is what makes it safe rather than the care taken writing it:
    `sleep_start + sleep_hours + PRE_SHIFT_H == work_start + species_shift`,
    identically, for every species and every role. The precondition is that
    `sleep_hours + work_hours + PRE_SHIFT_H <= 24`, which is asserted over
    every realisable (species, role) pair rather than assumed.
    """
    if role.work_hours <= 0:
        return 0.0      # visitors, refugees and lurkers keep the species clock
    return (role.work_start - REF_WORK_START) + shift_offset(npc_id, role)


def _jitter(npc_id: str, species: str) -> float:
    return (_u(npc_id, "jit") - 0.5) * 1.5 * RHYTHMS.get(
        species, RHYTHMS["human"]).jitter


def work_window(npc_id: str, species: str):
    """(start_hour, length_hours) of this individual's shift, or None.

    Exposed because a spawner needs to know where to put somebody, and because
    a test that has to re-derive the window from the role table will re-derive
    it slightly wrong -- the first version of the asleep-on-duty assertion
    omitted the per-individual jitter and reported thirteen false positives.
    """
    role = role_for(npc_id, species)
    if role.work_hours <= 0:
        return None
    w0 = (role.work_start + species_work_shift(species)
          + shift_offset(npc_id, role) + _jitter(npc_id, species)) % 24.0
    return w0, role.work_hours


def sleep_window(npc_id: str, species: str):
    """(start_hour, length_hours) of this individual's sleep block."""
    rhythm = RHYTHMS.get(species, RHYTHMS["human"])
    role = role_for(npc_id, species)
    s0 = (rhythm.sleep_start + _jitter(npc_id, species)
          + day_offset(npc_id, species, role)) % 24.0
    return s0, rhythm.sleep_hours


def activity_at(npc_id: str, species: str, hour: float) -> Activity:
    """What this NPC is doing at this station-clock hour.

    Resolution order matters: sleep wins over everything, then meals, then
    work, then a species-weighted leisure choice. Getting it the other way
    round produces NPCs who skip sleep to shop.
    """
    hour = hour % 24.0
    rhythm = RHYTHMS.get(species, RHYTHMS["human"])
    role = role_for(npc_id, species)

    # Individual variation so a species does not move in lockstep. Scaled per
    # species: a hive caste barely varies, the tail bucket varies wildly.
    jitter = _jitter(npc_id, species)

    off = day_offset(npc_id, species, role)
    if _in_window(hour, rhythm.sleep_start + jitter + off, rhythm.sleep_hours):
        return Activity.SLEEP

    # Meal windows are CENTRED on the meal hour. They were not: `abs((hour - m)
    # % 24.0) < 0.6` looks symmetric and is not, because a Python modulo is
    # always non-negative, so the window only ever opened *after* the meal hour
    # and never before it. Same 0.6 h of width, now half on each side.
    for m in rhythm.meals:
        d = (hour - (m + jitter * 0.4 + off)) % 24.0
        if min(d, 24.0 - d) < MEAL_HALF_WINDOW_H:
            return Activity.EAT

    if role.work_hours > 0:
        w0 = role.work_start + species_work_shift(species) \
            + shift_offset(npc_id, role) + jitter
        if _in_window(hour, w0, role.work_hours):
            return Activity.WORK
        # Commuting. `Activity.TRANSIT` existed in the enum and nothing ever
        # emitted it, so the corridors and lifts had no population of their own
        # -- everyone teleported between quarters and workplace. Half an hour
        # each way is not a guess: the drum is 2,586 m end to end and a
        # rim-to-axis lift is a two-minute ride at 0.12 g of lateral
        # acceleration (docs/AAA-STANDARD.md, interaction checklist), so a
        # cross-sector commute is tens of minutes.
        #
        # It also produces something checkable: aggregate TRANSIT should peak
        # at the hours FACTIONS.md 2.5 independently gives the Central Corridor
        # as busy -- 07:00-09:00 and 17:00-19:00. Nothing here was tuned to
        # make that happen; it falls out of the role start times.
        if _in_window(hour, w0 - TRANSIT_H, TRANSIT_H) \
                or _in_window(hour, w0 + role.work_hours, TRANSIT_H):
            return Activity.TRANSIT

    r = _u(npc_id, f"leisure-{int(hour)}")
    if species == "centauri" and r < 0.55:
        return Activity.RECREATION
    if r < 0.3:
        return Activity.COMMERCE
    if r < 0.55:
        return Activity.RECREATION
    if r < 0.62:
        return Activity.WORSHIP
    return Activity.IDLE


# ---------------------------------------------------------------------------
# The species mix -- FACTIONS.md 2.4
# ---------------------------------------------------------------------------
# Authority 5 throughout and it will never be anything else: no source states
# any species proportion for Babylon 5 (FACTIONS.md 15). What each row HAS is a
# stated reason, and the reasons are structural rather than aesthetic.
#
# COUNTS ARE THE SOURCE OF TRUTH, shares are derived. That ordering is the fix
# for INV-005: integers sum exactly, floats do not, and the previous mix summed
# to 0.94 without anything noticing.
RESIDENT_TOTAL = 250_000        # authority 1 -- S1/S2/S3 opening narration

STATION_COUNTS = {
    # Unchanged at 0.620 and defensible on structure, not headcount: the
    # station is EA sovereign territory, so every service function is
    # contracted through EA and staffed by EA citizens.
    "human": 155_000,
    # Second largest, and the fastest-growing and fastest-impoverishing
    # population aboard at the datum. Traders before S2E20, stateless after it.
    "narn": 22_500,
    # Reduced from 0.09. A contracting aristocratic power: a mission plus a
    # merchant and financier class. They are more CONSPICUOUS after the war,
    # not more numerous.
    "centauri": 17_500,
    # Reduced from 0.07. Eleven years after the war, Minbari do not settle
    # among humans in numbers.
    "minbari": 12_500,
    # Kept as the largest League species: on screen, the League species most
    # often in the background doing physical work.
    "drazi": 12_500,
    # NEW. Traders and financiers, and night dwellers -- see RHYTHMS.
    "brakiri": 7_500,
    # Halved from 0.05. 12,500 was far too many for a marginal League power.
    # Kept visible because they anchor the waste and carrion layer.
    "pakmara": 6_250,
    "vree": 5_000,      # NEW. Traders; saucer craft
    "abbai": 3_750,     # NEW. League founders and mediators; amphibian
    # NEW, and structurally important: methane breathers in encounter suits.
    # They are the visible reason the Alien Sector exists.
    "gaim": 2_500,
    "hyach": 1_750,     # NEW. Long-lived, formal
    "llort": 1_250,     # NEW. Scavengers and thieves -- the crime layer
    # The tail: rare League species, unidentified traders, one-off visitors.
    "other": 1_250,
    "grome": 750,       # NEW
}

# Kosh. A SINGLETON, and it must not be a share: 1/250,000 = 0.000004, and
# `int(2000 * 0.000004)` is 0 while `int(250000 * 0.000004)` can be 0 or 1
# depending on which way the float rounds. One person is not a proportion.
# He is therefore outside the statistical layer entirely -- authored, spawned
# by name, never sampled. Asserted in test_schedule.py, including a check that
# the artefact being avoided is real at sample scale.
VORLON_SINGLETON = 1

# Markab: ZERO. Extinct at the datum -- E4, S2E18 *Confessions and
# Lamentations*, the Drafa plague took the homeworld and the colonies
# (authority 1, dagger). Recorded here rather than omitted, because the
# difference between "we forgot the Markab" and "the Markab are dead" is the
# whole content of a sealed, powered, unlit quarter in the Alien Sector -- the
# only monument on the station to an entire species (FACTIONS.md 1.3, 13).
EXTINCT_SPECIES = {
    "markab": {
        "count": 0,
        "died": "E4 -- S2E18 'Confessions and Lamentations', the Drafa plague",
        "authority": "1 (dagger)",
        "if_datum_moves_before_S2E18": {
            "share": 0.008,
            "taken_from": ("other", "brakiri"),
            "also_needed": "a rhythm in RHYTHMS and a grammar in names.py",
        },
    },
}

# Shares, DERIVED. Nothing should ever edit this dict directly.
STATION_MIX = {sp: c / RESIDENT_TOTAL for sp, c in STATION_COUNTS.items()}

# Species in the mix that `names.py` cannot name, DECLARED rather than papered
# over. The reference set holds no personal name for any of these -- the only
# thing it holds for any of the nine new species is a partial desk name-plate
# reading "HYAC..." on a League delegate's desk
# (reference/15-races-and-makeup/Pak'ma'ra.webp at 12x), which is a SPECIES
# name and not a person's.
#
# INV-004 is the precedent and it is the right one: Vorlon is a closed list
# because a generator fitted to two data points is invention dressed as
# inference. Fitting one to ZERO data points is worse. So these species get no
# grammar until a name is attested, and a test asserts that this list and
# `names.GRAMMARS` never overlap -- which turns "we added a grammar" into a
# failing test rather than a silent duplication.
#
# `other` is not a species and can never have a grammar: it is the tail bucket.
SPECIES_WITHOUT_NAMES = ("brakiri", "vree", "abbai", "gaim", "hyach", "llort",
                         "grome", "other")

# The number of people aboard, which is not the same as the number the mix
# apportions: the mix sums to 250,000 and Kosh is additional to it.
STATION_HEADCOUNT = RESIDENT_TOTAL + VORLON_SINGLETON


def _require_unit_sum(mix: dict) -> None:
    """A mix that does not sum to 1 is a population leak, so it raises.

    INV-005: the previous mix summed to 0.94 and silently dropped 120 of every
    2,000 residents. The defence against that is not a wider tolerance, it is
    refusing to run. `math.fsum` rather than `sum` because a fourteen-term
    float sum accumulates error in the last place and this check is exact.
    """
    s = math.fsum(mix.values())
    if abs(s - 1.0) > 1e-9:
        raise ValueError(
            f"species mix sums to {s!r}, not 1.0 -- it would silently drop "
            f"{(1.0 - s) * 2000:.0f} of every 2,000 residents. This is INV-005."
        )


def apportion(total: int, mix: dict = None) -> dict:
    """Integer largest-remainder apportionment. Sums to `total` exactly.

    `int(total * share)` truncates, and flooring fourteen shares loses people:
    measured, 12 of 997, 13 of 999, 6 of 12,345, 1 of 45,001. It loses them
    again every station-hour, because the aggregate layer is recomputed from
    the same shares. Hare quota with an explicit deterministic tie-break
    instead: floor everything, then hand the remainder to the largest
    fractional parts.

    The measured losses are in the test, not only here, so a change to the mix
    that happens to make truncation exact cannot quietly retire the fix.
    """
    mix = STATION_MIX if mix is None else mix
    _require_unit_sum(mix)
    exact = {sp: mix[sp] * total for sp in mix}
    out = {sp: int(v) for sp, v in exact.items()}
    left = total - sum(out.values())
    # Tie-break is explicit and never relies on dict iteration order: largest
    # fractional part, then largest share, then species name.
    order = sorted(mix, key=lambda sp: (-(exact[sp] - int(exact[sp])), -mix[sp], sp))
    for sp in order[:left]:
        out[sp] += 1
    return out


def _agg_id(species: str, i: int) -> str:
    """The id of the i'th sampled member of a species.

    A prefix of this stream is a deterministic sample of the whole, which is
    what lets the statistical layer cost O(sample) instead of O(250,000).
    """
    return f"agg-{species}-{i}"


@dataclass(frozen=True)
class Census:
    """A deterministic sample of one species at one hour.

    Cost: `scan` calls to `activity_at`, cached. Everything statistical is
    built on this, so there is exactly one place where the population is
    counted and exactly one thing to make fast.
    """
    species: str
    hour: float
    scan: int
    _by_activity: tuple = field(repr=False, default=())
    _by_role: tuple = field(repr=False, default=())
    _by_role_work: tuple = field(repr=False, default=())

    def activity_fraction(self, a: Activity) -> float:
        return dict(self._by_activity).get(a, 0) / self.scan

    def role_fraction(self, role_key: str) -> float:
        return dict(self._by_role).get(role_key, 0) / self.scan

    def working_fraction(self, role_key: str) -> float:
        """P(at work | holds this role) -- 0.0 if the sample held none."""
        n = dict(self._by_role).get(role_key, 0)
        return (dict(self._by_role_work).get(role_key, 0) / n) if n else 0.0


CENSUS_SCAN = 2048      # see PERFORMANCE: sampling error ~1/sqrt(n) = 2.2%
AVAIL_SCAN = 512        # availability only ever appears as a RATIO, so 4.4% is fine


@lru_cache(maxsize=8192)
def census(species: str, hour: float, scan: int = CENSUS_SCAN) -> Census:
    acts, roles, work = {}, {}, {}
    for i in range(scan):
        nid = _agg_id(species, i)
        r = role_for(nid, species).key
        a = activity_at(nid, species, hour)
        acts[a] = acts.get(a, 0) + 1
        roles[r] = roles.get(r, 0) + 1
        if a is Activity.WORK:
            work[r] = work.get(r, 0) + 1
    return Census(species, hour, scan,
                  tuple(sorted(acts.items(), key=lambda kv: kv[0].value)),
                  tuple(sorted(roles.items())), tuple(sorted(work.items())))


def activity_profile(species: str, hour: float, scan: int = CENSUS_SCAN) -> dict:
    """Fraction of a species in each activity at this hour.

    THE claim the whole LOD design rests on: this must agree with counting
    every individual, or the population changes when the player looks away.
    Tested against a full enumeration in test_schedule.py rather than asserted
    in a docstring, which is where it lived before.
    """
    c = census(species, hour, scan)
    return {a: c.activity_fraction(a) for a in Activity}


def awake_fraction(species: str, hour: float, scan: int = AVAIL_SCAN) -> float:
    return 1.0 - census(species, hour, scan).activity_fraction(Activity.SLEEP)


@lru_cache(maxsize=64)
def mean_awake(species: str, scan: int = AVAIL_SCAN) -> float:
    """A species' 24-hour mean awake fraction.

    Used to normalise availability so that a species which sleeps nine hours
    is not permanently under-represented in every crowd -- only at the hours
    it is actually asleep. Numerator and denominator use the same `scan` so
    the sampling error cancels in the ratio instead of accumulating.
    """
    return sum(awake_fraction(species, float(h), scan) for h in range(24)) / 24.0


def population_activity(hour: float, species_mix: dict = None,
                        total: int = RESIDENT_TOTAL) -> dict:
    """Aggregate activity counts at a given hour. Sums to `total` exactly.

    This is the statistical layer. It has to agree with what you would get by
    simulating every individual, because the player crossing a district
    boundary must not see the population change.

    O(species x CENSUS_SCAN), not O(total): calling it for all 250,000
    residents costs the same as calling it for 2,000, which is what makes the
    full-station figure usable at runtime at all.
    """
    species_mix = STATION_MIX if species_mix is None else species_mix
    heads = apportion(total, species_mix)
    counts = {a: 0 for a in Activity}
    for species, n in heads.items():
        if n <= 0:
            continue
        prof = activity_profile(species, hour)
        # Largest remainder again, per species, so no one is lost to rounding
        # on the way out either.
        exact = {a: prof[a] * n for a in Activity}
        part = {a: int(v) for a, v in exact.items()}
        left = n - sum(part.values())
        order = sorted(Activity, key=lambda a: (-(exact[a] - int(exact[a])), a.value))
        for a in order[:left]:
            part[a] += 1
        for a in Activity:
            counts[a] += part[a]
    return counts


@lru_cache(maxsize=4096)
def role_on_duty(role_key: str, hour: float) -> int:
    """How many holders of a role are at work station-wide at this hour.

    The reason this exists: FACTIONS.md 2.2's most load-bearing invented number
    is 500 security officers, and its stated consequence is "roughly 150
    officers on duty at any moment across five pressurised sectors and 210
    decks" -- a garrison at chokepoints rather than a police presence. That
    consequence is now a measurement of the model instead of a sentence.
    """
    total = 0.0
    for species, count in STATION_COUNTS.items():
        w = ROLE_WEIGHTS.get(species, {}).get(role_key, 0)
        if not w:
            continue
        total += w * _conditional_working(species, role_key, hour)
    return int(round(total))


@lru_cache(maxsize=8192)
def _conditional_working(species: str, role_key: str, hour: float,
                         want: int = 192, max_scan: int = 250_000) -> float:
    """P(at work | species, role) by rejection sampling over the id stream.

    A flat census is too coarse here: security is 500 of 155,000 humans, so a
    2,048-id sample holds about six officers and cannot resolve a third of them
    being on watch. Conditioning on the role instead costs one `role_for` per
    scanned id -- one blake2b -- and is cached per (species, role, hour).
    """
    found = worked = 0
    for i in range(max_scan):
        nid = _agg_id(species, i)
        if role_for(nid, species).key != role_key:
            continue
        found += 1
        if activity_at(nid, species, hour) is Activity.WORK:
            worked += 1
        if found >= want:
            break
    return (worked / found) if found else 0.0


# ---------------------------------------------------------------------------
# Where the crowd is -- FACTIONS.md 2.5
# ---------------------------------------------------------------------------
# The table the spawner wants, as data rather than prose. Facility names are
# authority 3 (the `other map.png` rosettes and the Security Manual sectional
# schematic); crowd composition, hours and densities are authority 5.
#
# NO PLACE CARRIES A LEVEL NUMBER. C-003 (which longitudinal band is the drum)
# and C-004 (which ring is level 1) are OPEN and BLOCKING, so places are bound
# to a sector and a ring CLASS -- outer / middle / inner / axis -- exactly as
# FACTIONS.md 0.2 requires. A faction bound to a named facility survives both
# conflicts closing; one bound to "Brown 4" does not.

# How the non-human mass is split. The named dominants take most of it; the
# rest is spread over every other species in proportion to its station-wide
# share, so a Hyach can turn up in the Zocalo without being listed there.
DOMINANT_MASS = 0.75

# Density is in PERSONS PER 100 m^2 at the place's peak hour. Chosen as the
# unit because it is what a spawner multiplies by a floor area, and because it
# makes crowdedness and isolation the same measurement rather than two moods:
# the Dark Star at 23:00 and a Yellow Sector maintenance run at 23:00 differ by
# a factor of 600 in this one number.
DEAD_FRACTION = 0.08     # a "dead" hour still is not empty -- 05:00 Zocalo has six people
MID_FRACTION = 0.40      # neither busy nor dead
BAND_RAMP_H = 1.0        # a crowd arrives over an hour; it does not teleport


@dataclass(frozen=True)
class PlaceCrowd:
    """Who is in a place, how many, and when.

    `human_share` is FACTIONS.md 2.5's stated figure and is honoured at the
    place's BUSY hours; away from them the composition breathes, because the
    species present at 03:00 are not the species present at 13:00 and that is
    the entire reason fifteen rhythms exist.
    """
    key: str
    place: str
    sector: str                # "" where the source does not place it
    ring_class: str            # outer / middle / inner / axis / "" -- never a number
    human_share: float
    dominant: tuple            # ranked non-human species keys
    peak_per_100m2: float
    busy: tuple = ()           # ((start, end), ...) split at midnight, never wrapping
    dead: tuple = ()
    flat: bool = False         # no rhythm at all
    waves: bool = False        # driven by ship arrivals, 2.3
    sealed: bool = False       # nobody, ever
    character: str = ""
    auth: str = "3 for the facility, 5 for the crowd"


PLACES = {p.key: p for p in (
    PlaceCrowd("zocalo", "Zocalo", "red", "outer", 0.45,
               ("narn", "drazi", "centauri", "brakiri"), 20.0,
               busy=((11.0, 15.0), (18.0, 24.0)), dead=((4.0, 7.0),),
               character="The station's main social space, two storeys with an upper "
                         "gallery. Never empty, but at 05:00 it is a lit hall with six "
                         "people in it",
               auth="1 for the space (more zocalo.png), 3 for the ring, 5 for the crowd"),
    PlaceCrowd("customs_halls", "Customs halls (x2, north and south)", "blue", "outer",
               0.40, (), 25.0, busy=((0.0, 24.0),), waves=True,
               character="The most species-diverse space on the station. Queues, "
                         "encounter suits, breather-mask dispensers. Composition is the "
                         "station-wide alien mix because arrivals are 'everything, in "
                         "waves'",
               auth="1 for the boards, 3 for the halls, 5 for the crowd"),
    PlaceCrowd("central_corridor", "Central Corridor", "red", "outer", 0.55,
               ("drazi", "narn", "pakmara"), 15.0,
               busy=((7.0, 9.0), (17.0, 19.0)), dead=((2.0, 5.0),),
               character="Commuting artery. Two occupied levels in one volume",
               auth="1 for the space (central corridor.webp), 5 for the crowd"),
    PlaceCrowd("earharts", "Earhart's", "red", "outer", 0.80,
               ("centauri", "minbari"), 25.0,
               busy=((19.0, 24.0), (0.0, 2.0)), dead=((8.0, 18.0),),
               character="EarthForce bar, off-duty uniforms. Stands on the drum floor "
                         "under the far side"),
    PlaceCrowd("dark_star", "Dark Star", "red", "", 0.50,
               ("drazi", "narn", "llort"), 30.0,
               busy=((21.0, 24.0), (0.0, 4.0)), dead=((8.0, 18.0),),
               character="Rougher venue; planted entrance. The densest crowd on the "
                         "station and the one most likely to contain a Llort"),
    PlaceCrowd("casino", "Casino", "red", "inner", 0.50,
               ("centauri", "brakiri", "drazi"), 22.0,
               busy=((20.0, 24.0), (0.0, 4.0)), dead=((6.0, 11.0),),
               character="Centauri over-represented -- gambling is culturally theirs. "
                         "Brakiri because it is their working day"),
    PlaceCrowd("business_district", "Business District / Business Center", "red", "inner",
               0.65, ("brakiri", "centauri", "hyach"), 10.0,
               busy=((9.0, 17.0),), dead=((22.0, 24.0), (0.0, 6.0)),
               character="Currency exchange, banking, brokerage, guild offices. Rigid "
                         "human office hours in a station with no day -- and a Brakiri "
                         "night shift underneath it",
               auth="1 for the currency referral (customs board), 3 for the ring, 5 for "
                    "the crowd"),
    PlaceCrowd("law_courts", "Law Courts", "red", "inner", 0.75,
               ("narn", "centauri", "drazi"), 8.0,
               busy=((9.0, 16.0),), dead=((22.0, 24.0), (0.0, 6.0)),
               character="Ombuds hearings. Jurisdiction disputes are routine"),
    PlaceCrowd("security_central", "Security Central", "red", "inner", 0.95,
               (), 6.0, busy=((0.0, 24.0),),
               character="Three shifts. At the datum a visible split in one uniform: one "
                         "officer in a two-officer patrol wears the Nightwatch armband "
                         "and the other does not"),
    PlaceCrowd("docking_bays", "Docking bays 1-24 and the bay elevators", "blue", "outer",
               0.60, ("drazi", "narn", "pakmara", "vree"), 6.0,
               busy=((0.0, 24.0),), waves=True,
               character="Dockers' Guild territory. Heavy work; the Drazi share is "
                         "highest here",
               auth="3 for the bays (Security Manual), 5 for the crowd"),
    PlaceCrowd("dock_workers_quarters", "Dock Workers' Quarters", "blue", "", 0.70,
               ("drazi", "narn"), 20.0,
               busy=((6.0, 8.0), (15.0, 17.0)),
               character="Shift-change surges at both ends of the 06:00-15:00 day. "
                         "Cramped, functional"),
    PlaceCrowd("medlab_one", "Medlab One", "blue", "inner", 0.70, (), 6.0,
               busy=((0.0, 24.0),),
               character="Six atmospheres means six kinds of emergency"),
    PlaceCrowd("crew_country", "Mess Hall, Quartermaster, Post Office", "blue", "", 0.90,
               (), 12.0, busy=((7.0, 8.0), (12.0, 13.0), (18.0, 20.0)),
               dead=((0.0, 5.0),),
               character="The most human place aboard, and the far end of the gradient "
                         "the customs halls start"),
    PlaceCrowd("council_chamber", "Council Chamber and approaches", "green", "outer", 0.35,
               ("minbari", "centauri", "drazi", "brakiri", "abbai"), 15.0,
               busy=((10.0, 16.0),), dead=((22.0, 24.0), (0.0, 7.0)),
               character="Delegations, aides, guards, press. Ten League seats and a "
                         "rotation, so a delegation in the anteroom that is not sitting "
                         "today is a normal sight"),
    PlaceCrowd("ambassadorial_suites", "Ambassadorial suites", "green", "", 0.30,
               ("minbari", "centauri", "narn"), 2.0, busy=((0.0, 24.0),),
               character="Each suite is its own culture, atmosphere and gravity "
                         "preference. G'Kar's is a private residence now, not a legation"),
    PlaceCrowd("alien_sector", "Alien Sector", "green", "outer", 0.05,
               ("gaim", "abbai", "pakmara"), 4.0, busy=((0.0, 24.0),),
               character="Airlocks, breather-mask dispensers, non-standard atmospheres. "
                         "Its residents call the rest of the station the alien sector",
               auth="3 for the sector (Green rosette + Security Manual), 4 for the 14 "
                    "species and airlocks, 5 for the crowd"),
    PlaceCrowd("markab_quarter", "The sealed Markab quarter", "green", "outer", 0.0,
               (), 0.0, sealed=True,
               character="Sealed, powered, unlit, still furnished. Nobody at any hour. "
                         "The only monument on the station to an entire species, and "
                         "the reason the datum is worth its two costs",
               auth="1 (dagger) for the extinction (S2E18), 5 for the room"),
    PlaceCrowd("fresh_air_restaurant", "Fresh Air Restaurant", "green", "", 0.60,
               ("minbari", "centauri"), 18.0,
               busy=((12.0, 14.0), (19.0, 22.0)), dead=((2.0, 6.0),),
               character="Open terrace under the far side of the drum -- the ceiling is "
                         "terrain"),
    PlaceCrowd("zen_garden", "Zen Garden", "green", "", 0.50,
               ("minbari",), 2.0,
               busy=((6.0, 8.0), (21.0, 23.0)), dead=((11.0, 15.0),),
               character="Quiet. The Minbari over-representation is the point"),
    PlaceCrowd("hydroponics", "Hydroponics", "green", "", 0.85,
               ("abbai", "grome"), 3.0,
               busy=((5.0, 13.0),), dead=((22.0, 24.0), (0.0, 4.0)),
               character="Agricultural shift, not an office shift"),
    PlaceCrowd("the_garden", "The Garden (drum floor)", "drum", "outer", 0.65,
               ("minbari",), 3.0,
               busy=((9.0, 18.0),), dead=((1.0, 5.0),),
               character="A townscape, not a park -- buildings, surface transit, civic "
                         "landscaping. Sector contested by C-003",
               auth="1 for the space, 5 for the crowd; sector blocked by C-003"),
    PlaceCrowd("downbelow", "Downbelow", "brown", "outer", 0.68,
               ("narn", "drazi", "pakmara", "llort"), 8.0, flat=True,
               character="The one place with no schedule. Also the heaviest place a "
                         "person lives -- 1.117 g against the Garden's 1.000 g, next to "
                         "the waste plant, and none of that was authored",
               auth="3 for the band (Brown rosette), 4 for who lives there, 5 for the crowd"),
    PlaceCrowd("sanctuaries", "The four Sanctuaries", "", "", 0.60,
               ("minbari", "narn"), 5.0, flat=True,
               character="Counted at authority 3 on Contract 5 and never located. "
                         "Observance hours vary by faith and no source gives a rota, so "
                         "this is deliberately flat rather than invented",
               auth="3 for the count, 5 for everything else"),
    PlaceCrowd("industrial_grey", "Fabrication furnaces, power, repair", "grey", "outer",
               0.90, ("drazi", "gaim"), 2.0, busy=((0.0, 24.0),),
               character="Grey holds 90 of the station's 210 decks. Three shifts"),
    PlaceCrowd("yellow_maintenance", "Zero-G maintenance, coolant, holding tanks",
               "yellow", "", 0.95, (), 0.05, busy=((0.0, 24.0),),
               character="Almost nobody: two or three suited figures in a kilometre. "
                         "This is the isolation end of the station and the number says so"),
)}


def _band_distance(hour: float, bands: tuple) -> float:
    """Circular distance in hours from `hour` to the nearest band, 0 if inside.

    Circular, so bands written as ((21,24),(0,4)) join at midnight with no gap
    and no special case -- which is where a wrapping-range bug would live.
    """
    if not bands:
        return 24.0
    best = 24.0
    for a, b in bands:
        if a <= hour < b:
            return 0.0
        da = min(abs(hour - a) % 24.0, 24.0 - abs(hour - a) % 24.0)
        db = min(abs(hour - b) % 24.0, 24.0 - abs(hour - b) % 24.0)
        best = min(best, da, db)
    return best


# Ship arrivals, from FACTIONS.md 2.3: 24 bays + 4 low-g at 70% occupancy on a
# 9 h berth-to-berth cycle gives 2.18 arrivals/hour, 52 movements a station-day,
# ~120 souls each, ~6,300 arrivals/day across two customs halls. Arrivals are
# deliberately IRREGULAR -- evenly spaced arrivals would give the hall a steady
# trickle, and 2.3 is explicit that the design case is "a peak of 20-40/minute
# and long dead periods". The jitter is deterministic, not random.
ARRIVALS_PER_DAY = 52
SOULS_PER_ARRIVAL = 120
CUSTOMS_HALLS = 2
# 2.3 says design the hall for "a peak of 20-40/minute and long dead periods".
# Take the middle of that band and the dwell time follows rather than being
# chosen: 120 souls over two halls at 30/minute is two minutes at the counter,
# and a queue stands about three times as long as the counter takes.
PEAK_RATE_PER_MIN = 30.0
QUEUE_MULTIPLIER = 3.0
HALL_PROCESS_MIN = SOULS_PER_ARRIVAL / CUSTOMS_HALLS / PEAK_RATE_PER_MIN   # 2.0 min
HALL_DWELL_H = HALL_PROCESS_MIN * QUEUE_MULTIPLIER / 60.0                  # 0.10 h
# 52 waves x 0.10 h = 5.2 h of the 24 with a crowd in the hall, so the hall is
# empty 78% of the day and heaving for the rest. That asymmetry is the whole
# character of the room and it is why the arrival times are jittered: evenly
# spaced arrivals would give a trickle instead.


@lru_cache(maxsize=4)
def arrival_times(day: int = 0) -> tuple:
    """The 52 arrival times of a station-day, jittered deterministically."""
    step = 24.0 / ARRIVALS_PER_DAY
    out = []
    for i in range(ARRIVALS_PER_DAY):
        j = (_u(f"arrival-{day}-{i}", "t") - 0.5) * step * 1.6
        out.append((i * step + j) % 24.0)
    return tuple(sorted(out))


def wave_pulse(hour: float) -> float:
    """1.0 while a wave is being processed, 0.0 between waves."""
    hour %= 24.0
    for t in arrival_times():
        d = (hour - t) % 24.0
        if d < HALL_DWELL_H:
            return 1.0
    return 0.0


def density_at(place_key: str, hour: float) -> float:
    """Persons per 100 m^2 in a place at a station-clock hour.

    The crowdedness/isolation figure. `docs/AAA-STANDARD.md` requires this to
    be stated per space per hour and then checked against what the schedule
    model produces; stating it is this function, and checking it is
    `test_schedule.py`.
    """
    p = PLACES[place_key]
    if p.sealed:
        return 0.0
    hour %= 24.0
    if p.flat:
        return p.peak_per_100m2
    b = max(0.0, 1.0 - _band_distance(hour, p.busy) / BAND_RAMP_H)
    d = max(0.0, 1.0 - _band_distance(hour, p.dead) / BAND_RAMP_H)
    level = MID_FRACTION + (1.0 - MID_FRACTION) * b - (MID_FRACTION - DEAD_FRACTION) * d
    if p.waves:
        # A wave arrives on top of whatever the hall was already doing, and
        # between waves it falls to the dead level however busy the day is.
        level = DEAD_FRACTION + (level - DEAD_FRACTION) * wave_pulse(hour)
    return p.peak_per_100m2 * max(DEAD_FRACTION, min(1.0, level))


def crowd_at(place_key: str, hour: float) -> dict:
    """Species composition of the standing crowd. Shares, summing to 1.0.

    Three inputs, and only the first is invented per place:

      1. FACTIONS.md 2.5's stated human share and ranked dominant non-humans.
      2. The station-wide mix, for everyone not named as dominant -- so a Hyach
         can be in the Zocalo without the table having to list him.
      3. Each species' AWAKE FRACTION at this hour, normalised by its own
         24-hour mean. This is what makes station-night a different crowd
         rather than a smaller day crowd, and it is derived from the rhythms
         rather than chosen: the Brakiri night presence is a consequence of one
         authority-4 sentence, not of a magic constant.
    """
    p = PLACES[place_key]
    if p.sealed:
        return {}
    base = {"human": p.human_share}
    non_human = 1.0 - p.human_share
    named = tuple(s for s in p.dominant if s in STATION_COUNTS)
    if named:
        rank_w = [len(named) - i for i in range(len(named))]
        tot = float(sum(rank_w))
        for s, w in zip(named, rank_w):
            base[s] = non_human * DOMINANT_MASS * (w / tot)
        tail_mass = non_human * (1.0 - DOMINANT_MASS)
    else:
        tail_mass = non_human
    tail = {s: STATION_COUNTS[s] for s in STATION_COUNTS
            if s != "human" and s not in named}
    tail_total = float(sum(tail.values())) or 1.0
    for s, c in tail.items():
        base[s] = base.get(s, 0.0) + tail_mass * (c / tail_total)

    # Availability: who is actually awake to be standing here.
    w = {}
    for s, v in base.items():
        if v <= 0.0:
            continue
        m = mean_awake(s) or 1.0
        w[s] = v * (awake_fraction(s, hour) / m)
    tot = math.fsum(w.values()) or 1.0
    return {s: v / tot for s, v in sorted(w.items(), key=lambda kv: -kv[1])}


def crowd_headcount(place_key: str, hour: float, area_m2: float) -> dict:
    """Whole people, by species, for a floor area. Sums to the rounded total."""
    n = int(round(density_at(place_key, hour) * area_m2 / 100.0))
    if n <= 0:
        return {}
    mix = crowd_at(place_key, hour)
    if not mix:
        return {}
    exact = {s: mix[s] * n for s in mix}
    out = {s: int(v) for s, v in exact.items()}
    left = n - sum(out.values())
    order = sorted(mix, key=lambda s: (-(exact[s] - int(exact[s])), -mix[s], s))
    for s in order[:left]:
        out[s] += 1
    return {s: c for s, c in out.items() if c}


# ---------------------------------------------------------------------------
# PERFORMANCE -- the binding constraint, and the reason this file is shaped
# the way it is
# ---------------------------------------------------------------------------
# 250,000 residents cannot be 250,000 agents and cannot be 250,000 meshes. They
# also cannot be 250,000 *records*: at a 512-byte NPC record that is 128 MB of
# resident data for a population the player will meet 0.2% of. So identity is
# COMPUTED from (seed, id) and never stored, which is why `activity_at`,
# `role_for` and `names.name_for` are all pure functions of an id string.
#
# THREE TIERS. The numbers below are the budget this module is gated against;
# `test_schedule.py` asserts the triangle arithmetic and the agent caps, and
# `station/budget.py` owns the frame budget they come out of.
#
#   full agent      0-18 m, inside the resident streaming set (3 cells)
#                   pathfinding, animation, needs, dialogue      cap 500
#   crowd agent     the rest of the visible set, flow-field only,
#                   no individual pathing                        cap 2,000
#   statistical     everyone else -- `population_activity()` and
#                   `crowd_headcount()`. ZERO per-capita cost    250,000
#
# TRIANGLES. `station/budget.py` gives the frame 1,200,000 triangles and
# interior structure 5% of it. NPCs get 15% -- 180,000 -- because they are the
# subject of the shot in a way structure is not, and because a concourse with
# no crowd fails the brief more visibly than a concourse with a plain wall.
#
#   LOD0   0-6 m     8,000 tri   max   4  =  32,000
#   LOD1   6-18 m    2,000 tri   max  20  =  40,000
#   LOD2  18-45 m      600 tri   max  80  =  48,000
#   LOD3  45 m+        120 tri   max 400  =  48,000
#                                 total   = 168,000 of 180,000, 504 bodies
#
# The switch distances are set by SILHOUETTE, not by a taste for round numbers:
# a 1.8 m person at 45 m subtends 2.3% of a 1440p frame height, so ~33 px, at
# which a 120-triangle body plus a normal map is not distinguishable from a
# 600-triangle one. At 18 m he is ~82 px and the head silhouette starts to
# matter; at 6 m he is ~250 px and hands and face do.
#
# DRAW CALLS. One instanced batch per (species x near/far), 15 x 2 = 30, which
# fits under the exterior's 64. Costume, uniform, Nightwatch armband, skin tone
# and the tail bucket's rotating model set are PER-INSTANCE data, not extra
# batches -- an armband must never cost a draw call, because 30-40% of security
# wear one and the whole point is that they are otherwise identical.
#
# CPU. `activity_at` is ~2.9 us in Python and three blake2b hashes in principle;
# in the C# runtime it is nanoseconds. The statistical layer costs
# O(species x CENSUS_SCAN) per hour -- 15 x 2,048 = 30,720 evaluations, cached,
# recomputed once per station-hour and never per frame. That is why
# `population_activity(hour, STATION_MIX, 250_000)` costs the same as
# `population_activity(hour, STATION_MIX, 2_000)`: the sample does not grow
# with the population, only the multiplier does.
#
# MEMORY. 500 full agents x 512 B + 2,000 crowd agents x 64 B + the cached
# census (15 species x 24 h x ~26 counters) is under 0.5 MB. The population
# itself is a function, and functions are free.
def _body_frame_share():
    """`body.NPC_FRAME_SHARE`, imported at need to avoid an import cycle."""
    from npc import body as _b                                  # noqa: PLC0415
    return _b.NPC_FRAME_SHARE


NPC_BUDGET = {
    "frame_triangles": 1_200_000,
    # ONE NUMBER, and it lives in `body.NPC_FRAME_SHARE`. This was 0.15 while
    # body.py said 0.12 -- `crowd.py`'s finding (b), two budgets for one frame.
    # Imported rather than repeated so the two cannot drift again.
    "npc_frame_share": _body_frame_share(),
    "lod": (
        # (name, near_m, far_m, triangles, max_instances)
        ("lod0", 0.0, 6.0, 8_000, 4),
        ("lod1", 6.0, 18.0, 2_000, 20),
        ("lod2", 18.0, 45.0, 600, 80),
        ("lod3", 45.0, 400.0, 120, 400),
    ),
    "max_draw_calls": 32,
    "full_agents": 500,
    "crowd_agents": 2_000,
}


def npc_visible_triangles() -> int:
    return sum(t * n for _, _, _, t, n in NPC_BUDGET["lod"])


def npc_triangle_budget() -> int:
    return int(NPC_BUDGET["frame_triangles"] * NPC_BUDGET["npc_frame_share"])


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_schedule

    sys.exit(test_schedule.main())
