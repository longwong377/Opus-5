"""NPC schedules and simulation LOD.

A quarter of a million residents cannot all be simulated as agents. The
standard answer is simulation LOD: full agents near the player, statistical
abstraction everywhere else, with individuals promoted and demoted as the
player moves. What makes it work rather than merely cheap is that the abstract
layer has to produce the *same* aggregate behaviour the detailed layer would --
if a district's population drops when nobody is looking, the player will notice
the moment they walk back in.

Schedules are driven by station time, which is not Earth time. The station runs
on a 24-hour cycle for human convenience (the show references shifts and
"night" in a lit-from-within habitat where neither is astronomically
meaningful), but its species keep different hours, and the drum's rotation
gives no day at all -- lighting is entirely artificial, so "night" is a
decision the station makes.

Deterministic throughout: an NPC's schedule is a function of its id, so the
same resident does the same thing at the same time in every session.
"""
import hashlib
from dataclasses import dataclass
from enum import Enum


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


@dataclass(frozen=True)
class SpeciesRhythm:
    """How a species divides its day.

    Hours are station-clock hours. Species differ enough that a corridor at
    03:00 should not be empty -- it should be full of whoever is awake then,
    which is a specific and different crowd from the one at 13:00.
    """
    species: str
    sleep_start: float
    sleep_hours: float
    meals: tuple               # station-clock hours
    note: str


RHYTHMS = {
    # Humans set the station clock, so their rhythm is the reference against
    # which every other species reads as unusual.
    "human": SpeciesRhythm("human", 23.0, 7.5, (7.0, 12.5, 19.0),
                           "Sets the station clock. Three meals, one long sleep."),
    # Minbari famously do not sleep the whole night through -- the show
    # establishes they wake for a period in the middle. That produces a real
    # and visible effect: Minbari abroad in corridors at hours nobody else is.
    "minbari": SpeciesRhythm("minbari", 22.5, 4.0, (8.0, 18.0),
                             "Sleep is broken -- a waking period mid-rest is canon, so "
                             "Minbari are abroad at hours no one else is."),
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
                             "from the depicted friction over their diet, not stated."),
}


@dataclass(frozen=True)
class Role:
    """What an NPC does, which drives where they are during work hours."""
    key: str
    work_start: float
    work_hours: float
    workplace: str


ROLES = (
    Role("dockworker", 6.0, 9.0, "docking_bay"),
    Role("security", 0.0, 8.0, "patrol"),          # rotating shifts, see shift_offset
    Role("merchant", 9.0, 11.0, "zocalo"),
    Role("engineer", 7.0, 9.0, "engineering"),
    Role("medical", 0.0, 12.0, "medlab"),          # rotating
    Role("diplomat", 10.0, 7.0, "green_sector"),
    Role("command", 8.0, 10.0, "cnc"),
    Role("service", 5.0, 10.0, "hospitality"),
    Role("lurker", 0.0, 0.0, "downbelow"),         # no work -- Downbelow's unemployed
)


def role_for(npc_id: str) -> Role:
    return ROLES[int(_u(npc_id, "role") * len(ROLES)) % len(ROLES)]


def shift_offset(npc_id: str, role: Role) -> float:
    """Hours to shift a rotating-roster role.

    Security and medical run around the clock, so their members are spread
    across three shifts rather than all starting together. Without this the
    station would be visibly unguarded for sixteen hours a day.
    """
    if role.workplace not in ("patrol", "medlab"):
        return 0.0
    return 8.0 * (int(_u(npc_id, "shift") * 3) % 3)


def activity_at(npc_id: str, species: str, hour: float) -> Activity:
    """What this NPC is doing at this station-clock hour.

    Resolution order matters: sleep wins over everything, then meals, then
    work, then a species-weighted leisure choice. Getting it the other way
    round produces NPCs who skip sleep to shop.
    """
    hour = hour % 24.0
    rhythm = RHYTHMS.get(species, RHYTHMS["human"])
    role = role_for(npc_id)

    # Individual variation so a species does not move in lockstep.
    jitter = (_u(npc_id, "jit") - 0.5) * 1.5

    # Sleep has to follow the shift, not the clock. Resolving sleep before work
    # against an unshifted rhythm put the entire night watch to bed and left
    # the station unguarded from midnight to morning -- security showed zero on
    # duty at 02:00. A night-shift worker sleeps during the day.
    off = shift_offset(npc_id, role)
    s0 = (rhythm.sleep_start + jitter + off) % 24.0
    s1 = (s0 + rhythm.sleep_hours) % 24.0
    in_sleep = (s0 < s1 and s0 <= hour < s1) or (s0 > s1 and (hour >= s0 or hour < s1))
    if in_sleep:
        return Activity.SLEEP

    for m in rhythm.meals:
        if abs((hour - (m + jitter * 0.4)) % 24.0) < 0.6:
            return Activity.EAT

    if role.work_hours > 0:
        w0 = (role.work_start + shift_offset(npc_id, role) + jitter) % 24.0
        w1 = (w0 + role.work_hours) % 24.0
        at_work = (w0 < w1 and w0 <= hour < w1) or (w0 > w1 and (hour >= w0 or hour < w1))
        if at_work:
            return Activity.WORK

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


def population_activity(hour: float, species_mix: dict, total: int) -> dict:
    """Aggregate activity counts at a given hour.

    This is the statistical layer. It has to agree with what you would get by
    simulating every individual, because the player crossing a district
    boundary must not see the population change.
    """
    counts = {a: 0 for a in Activity}
    idx = 0
    for species, share in species_mix.items():
        n = int(total * share)
        for i in range(n):
            counts[activity_at(f"agg-{species}-{i}", species, hour)] += 1
            idx += 1
    return counts


# Canon population is 250,000 (S1 opening narration). The mix below is an
# INFERENCE from on-screen crowd composition, not a stated figure -- humans
# dominate, Narn and Centauri are the most visible non-humans, and the League
# species fill the remainder. Logged as part of INV-005.
# Shares must sum to 1.0 or the aggregate layer silently loses people -- at
# 0.94 it was dropping 120 of every 2,000 residents, which is exactly the kind
# of quiet population leak the statistical layer exists to avoid.
STATION_MIX = {
    "human": 0.62,
    "narn": 0.10,
    "centauri": 0.09,
    "minbari": 0.07,
    "drazi": 0.07,
    "pakmara": 0.05,
}
