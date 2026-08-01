#!/usr/bin/env python3
"""THE FIRST TEN MINUTES: a ship, a bay, a queue, a card in a reader, and a room
with your name on it.

WHAT THE OWNER ASKED. *"any of the intro scene where you arrive on a transport
and are processed been made yet? character creator/or random? does the player
have a residence?"* The answer to all three was no, and the striking part is
that almost none of the material was missing -- only the joins were:

  `traffic.arrivals`      55 ships a day, each with a type, an hour, a berth
                          tier, a passenger count and a stay. Written in session
                          4b. NOTHING had ever read it.
  `customs.py`            the hall, from the authority-1 frame -- the boards, the
                          screens, the bollards, the desks. Built. Nobody in it.
  `npc/resident.py`       the nine-field identicard off the prop, a role, a job,
                          and a HOME. Built for the crowd.
  `directory.PLACES`      `customs_north` declares `identicard_reader`,
                          `customs_desk`, `baggage_scanner`, `info_board`.
  `interact.py`           the verb set, and `identicard_reader -> operate`.
  TRAFFIC-AND-CUSTOMS 6.3 the ten-station process a visitor goes through,
                          sourced check by check.

So this module invents almost nothing. It is a JOIN, and its self-test is mostly
a set of assertions that the join is real: that the ship is one of `traffic`'s
own, that every step stands in a register place, that every object a step names
is declared in that place's own `interacts`, and that every verb is
`interact.verb_of`'s and not a second opinion.

WHY IT IS DATA AND NOT A SCRIPT. `godot/scripts/arrival.gd` steps through what
`--emit` writes. A hard-coded sequence in GDScript would be the fourth
description of the station's own facts in a project that has paid three times
for the third. It also means the sequence can be gated in Python, where there is
no engine, no GPU and no window -- which is the only place anything gets checked
here.

IT VARIES, AND THE VARIATION IS SOURCED. A Narn on a sanctuary visa is not
processed like an Earth citizen, and the difference is not a table of species
manners: it is `ORIGIN` (authority 1, the prop), `VISAS` (authority 1, the prop,
and FACTIONS.md 3.4 on why it is the station's most ordinary crime),
`DES/ATMOS` (authority 1, and the customs board's six standing atmospheres), and
`LICENSED PSI` (authority 1). Four fields that already existed, read as a customs
officer would read them. `--matrix` prints the outcome for every species and
role and shows they are not all the same.

WHAT IT ADDS, DECLARED. Three things, and each is logged:
  INV-248  the arriving species mix equals the resident mix (`player.py`)
  INV-249  the arrival credit distribution, SOLVED against 6.6's 1% leak
  INV-250  ship names, bay assignment and the customs-area numbering

Run: python3 station/arrival.py --selftest
     python3 station/arrival.py --report
     python3 station/arrival.py --matrix
     python3 station/arrival.py --emit station/generated/arrival.json
"""
import argparse
import json
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import customs as CU                                            # noqa: E402
import deck as DK                                               # noqa: E402
import directory as dr                                          # noqa: E402
import interact as IX                                           # noqa: E402
import player as PL                                             # noqa: E402
import signage as SG                                            # noqa: E402
import traffic as TR                                            # noqa: E402
from npc import resident as RES                                 # noqa: E402
from npc import schedule as sched                               # noqa: E402

GAZETTEER = TR.GAZETTEER


def _u(*parts) -> float:
    """`traffic`'s own draw, so an arrival day is reproducible across runs."""
    return sched._u("arrival", "/".join(str(p) for p in parts))


# A DAY IS ASKED FOR A HUNDRED TIMES AND COSTS 0.4 s TO BUILD. `traffic.arrivals`
# rebuilds the manifest and inverts the day curve on every call and is not
# cached; this module resolves a day per sequence and the self-test resolves 190
# sequences, which is 230 s of recomputing the same 56 ships. Cached HERE rather
# than in `traffic.py`, which is another agent's file this session, and it is
# strictly an optimisation: `arrivals(day)` is deterministic in `day` alone, so
# the cached list is the same list. It also makes the identity `pick_transport`
# returns stable across calls, which `sequence` relies on for `.index()`.
@lru_cache(maxsize=64)
def day_arrivals(day: int = 0) -> tuple:
    return tuple(TR.arrivals(day))


# ===========================================================================
# 1.  The ship -- from traffic.py, never invented
# ===========================================================================

# Which manifest rows land a passenger who then walks through a customs hall.
# DERIVED from `traffic.MANIFEST` rather than listed: a row qualifies if it
# berths in a bay (so its people walk off rather than being lightered), carries
# souls, and is not a hull whose crew stays aboard. Listing them would be a
# second copy of the manifest, and the manifest is the thing that changes.
@lru_cache(maxsize=1)
def passenger_types():
    return tuple(row[0] for row in TR.MANIFEST
                 if row[2] == "bay" and row[4] > 0
                 and row[0] not in TR.CREW_STAYS_ABOARD)


def pick_transport(day: int = 0, seed: str = "player") -> dict:
    """Which of the day's arrivals the player is aboard.

    WEIGHTED BY PASSENGER COUNT, and that is a derivation rather than a taste:
    picking uniformly among ships would put the player on a two-seat shuttle as
    often as on a liner, and a randomly chosen arriving PERSON is on a given
    ship with probability proportional to how many people it landed. It is also
    what makes `traffic`'s liner the event it is documented to be -- on a liner
    day, most arriving people are on the liner.

    Returns the arrival dict from `traffic.arrivals(day)` BY IDENTITY, so
    `_selftest` can assert the player's ship is one of the port's own.
    """
    day_list = arrivals_with_passengers(day)
    if not day_list:                                        # pragma: no cover
        raise RuntimeError(f"day {day} landed nobody -- traffic.arrivals is "
                           f"{len(day_arrivals(day))} ships")
    tot = float(sum(a["souls"] for a in day_list))
    x = _u("ship", day, seed) * tot
    acc = 0.0
    for a in day_list:
        acc += a["souls"]
        if x <= acc:
            return a
    return day_list[-1]


def arrivals_with_passengers(day: int = 0) -> list:
    want = set(passenger_types())
    return [a for a in day_arrivals(day)
            if a["type"] in want and a["souls"] > 0]


# ---------------------------------------------------------------------------
# The ship's NAME -- INV-250, and the only thing here the port did not already
# have. `traffic` gives a type, an hour, a berth tier, souls and a stay; the
# comms discipline of TRAFFIC-AND-CUSTOMS 4.4 is that a ship is addressed **by
# name and type** ("Transport Von Braun", "Narn cargo ship Tal'Quith"), never by
# registry alone, so a nameless ship cannot be announced and D-11's announcement
# is the player's first line of dialogue.
#
# The grammars are not new vocabularies. Human hulls take the attested pattern --
# Von Braun is a twentieth-century rocket engineer, so EA civil hulls are named
# for explorers and scientists, which is also how Earth has named ships for four
# hundred years. Alien hulls go through `npc/names.py`'s OWN species grammars,
# which are fitted to attested names and which produced Tal'Quith-shaped strings
# before this module existed. Overturned by any list of B5-era civilian hull
# names; constrained by the two attested examples, which both fit.
EA_HULL_NAMES = (
    # Explorers, navigators and scientists. Von Braun (attested, authority 4)
    # sets the class; these are the same class and nothing more.
    "Von Braun", "Magellan", "Shackleton", "Amundsen", "Cousteau", "Curie",
    "Hawking", "Bering", "Drake", "Cabot", "Tereshkova", "Gagarin",
    "Armstrong", "Hillary", "Da Gama", "Cook", "Nansen", "Scott",
    "Copernicus", "Kepler", "Halley", "Herschel", "Hubble", "Sagan",
)
# Which species' grammar names a hull of each manifest type. `ef_transport` is
# EarthForce and therefore always EA; everything else is drawn from the traffic
# the station actually gets, weighted by the arriving mix.
HULL_SPECIES_FIXED = {"ef_transport": "human", "liner": "human"}
HULL_GRAMMAR_SPECIES = ("human", "narn", "centauri", "minbari", "drazi")


def ship_species(a: dict, day: int, i: int) -> str:
    sp = HULL_SPECIES_FIXED.get(a["type"])
    if sp:
        return sp
    x = _u("hullsp", day, i, a["type"])
    return HULL_GRAMMAR_SPECIES[int(x * len(HULL_GRAMMAR_SPECIES))
                                % len(HULL_GRAMMAR_SPECIES)]


def ship_name(a: dict, day: int, i: int) -> str:
    """A hull name of the right nationality. See INV-250."""
    sp = ship_species(a, day, i)
    if sp == "human":
        x = _u("hull", day, i)
        return EA_HULL_NAMES[int(x * len(EA_HULL_NAMES)) % len(EA_HULL_NAMES)]
    # `names.name_for` raises for the eight species with no attested name; the
    # five in HULL_GRAMMAR_SPECIES all have grammars, and this is deliberate --
    # a hull named out of a grammar fitted to zero examples would be INV-004's
    # exact failure.
    from npc import names as npc_names                      # noqa: PLC0415
    return npc_names.name_for(sp, f"hull:{day}:{i}")


# How a hull is spoken about. TRAFFIC-AND-CUSTOMS 4.4: by name AND type.
SHIP_TYPE_WORD = {
    "transport": "Transport", "shuttle": "Shuttle", "liner": "Liner",
    "freighter_bay": "Freighter", "freighter_standoff": "Freighter",
    "ef_transport": "EarthForce transport", "diplomatic": "Diplomatic courier",
    "ef_warship": "EarthForce cruiser", "alien_warship": "Warship",
}


def ship_title(a: dict, day: int, i: int) -> str:
    word = SHIP_TYPE_WORD.get(a["type"], a["type"].replace("_", " ").title())
    sp = ship_species(a, day, i)
    if sp != "human" and a["type"] in ("transport", "freighter_bay",
                                       "freighter_standoff", "shuttle"):
        # "Narn cargo ship Tal'Quith" -- the attested alien form carries the
        # nationality as well as the type.
        word = f"{sp.title()} {word.lower()}"
    return f"{word} {ship_name(a, day, i)}"


# ===========================================================================
# 2.  The bay, the hall and the customs area
# ===========================================================================

# BAYS ARE ASSIGNED, NOT DRAWN. D-2 is explicit that a ship is cleared for a
# NUMBERED bay, and a port that hands two hulls the same berth is a port with no
# traffic control -- which is the one thing C&C is unambiguously for
# (TRAFFIC-AND-CUSTOMS 4.4). So the day's bay-tier arrivals are walked in time
# order and each takes the lowest-numbered berth that is free at its hour, using
# `traffic`'s own `stay_h`. `_selftest` asserts no overlap, with an
# all-to-bay-1 control that fires.
#
# The count comes from the schema, via `traffic.bay_count` -- the Security
# Manual's DOCKING BAYS (24) at authority 3, in one place.
#
# THE LETTER SUFFIX IS REAL AND ITS MEANING IS NOT. *The Gathering* has "Final
# approach to Docking Bay 12B" while "Grail" has plain "Bay 7", so bays
# sometimes carry a letter and the show never says what it distinguishes. D-9
# gives a bay a LANDING PAD and a PARKING LEVEL BELOW IT, i.e. two places a hull
# can be, so the letter is modelled as the berth within the bay: A on the pad,
# B on the parking level. INV-250. Overturned by any line that uses a letter
# beyond B, or that uses one for something else.
BAY_BERTHS = ("A", "B")


@lru_cache(maxsize=64)
def bay_assignment(day: int = 0, bays: int = None) -> dict:
    """`id(arrival) -> (bay number, berth letter)` for one station day."""
    if bays is None:
        bays = TR.bay_count()
    # (bay, berth) -> hour it comes free
    free = {}
    out = {}
    for i, a in enumerate(day_arrivals(day)):
        if a["berth"] != "bay":
            continue
        for n in range(1, bays + 1):
            for b in BAY_BERTHS:
                if free.get((n, b), -1e9) <= a["hour"]:
                    free[(n, b)] = a["hour"] + a["stay_h"]
                    out[i] = (n, b)
                    break
            if i in out:
                break
        if i not in out:                                    # pragma: no cover
            # Every berth full. `traffic._selftest` asserts this cannot happen
            # at the shipped manifest; if it ever does, the port is over
            # capacity and saying so is better than silently double-booking.
            raise RuntimeError(f"day {day} hour {a['hour']:.1f}: all "
                               f"{bays * len(BAY_BERTHS)} berths occupied")
    return out


def bay_label(n: int, berth: str) -> str:
    """"7" or "12B". A pad-A berth is spoken as a bare number -- "Bay 7"."""
    return f"{n}" if berth == "A" else f"{n}{berth}"


@lru_cache(maxsize=512)
def bay_angle_deg(n: int, bays: int = None) -> float:
    """Where bay `n` is on the ring, in the register's own angle convention.

    The 24 bays tile the circle -- `directory.PLACES['docking_bays']` has a
    360-degree footprint and the gazetteer's note says "24 bays tiling the
    circle" -- so bay 1 sits at 0 degrees and they step round from there. This
    is the whole basis of the hall assignment below, and it is geometry rather
    than a table.
    """
    if bays is None:
        bays = TR.bay_count()
    return (360.0 / bays) * (n - 1)


HALLS = ("customs_north", "customs_south")


def _arc(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


@lru_cache(maxsize=512)
def hall_for_bay(n: int, bays: int = None) -> str:
    """Which customs hall a bay's passengers are routed to.

    DERIVED FROM THE REGISTER'S OWN ANGLES, not from a north/south table:
    `customs_north` is at 40 degrees and `customs_south` at 220, so a bay goes
    to whichever hall is the shorter walk round the ring. Move either hall in
    `directory.PLACES` and this follows it. That is the same rule
    `resident.workplace_places` uses for jobs -- join by what a thing IS, never
    by a second list of keys.
    """
    ang = bay_angle_deg(n, bays)
    return min(HALLS, key=lambda k: _arc(ang, dr.by_key(k)["angle_deg"]))


# THE NUMBERED CUSTOMS AREAS. "TKO" gives "...disembark through customs area 7"
# (authority 4), and TRAFFIC-AND-CUSTOMS 6.1/T-X1 reasons that the pair of halls
# carries seven between them. Our BUILT hall has `customs.DESKS` processing
# positions, and the two disagree -- see `area_cross_check()`, which prints the
# gap rather than smoothing it. The numbering runs north first, so area 7 falls
# in the south hall either way, which is the only thing the source constrains.
@lru_cache(maxsize=1)
def areas_per_hall() -> int:
    return int(CU.DESKS)


def area_for(n: int, bays: int = None, seed: str = "") -> int:
    """The numbered customs area a bay's passengers are sent through."""
    hall = hall_for_bay(n, bays)
    per = areas_per_hall()
    base = 0 if hall == HALLS[0] else per
    return base + 1 + int(_u("area", n, seed) * per) % per


def area_cross_check() -> dict:
    """What the built hall gives against what the gazetteer reasoned. A GAP.

    Kept as a printed comparison rather than an assertion because neither
    number is canon: "area 7" is authority 4 and constrains only that a
    seventh area exists somewhere in the pair, which both readings satisfy.
    """
    per = areas_per_hall()
    return {"built_per_hall": per, "built_across_pair": per * len(HALLS),
            "gazetteer_across_pair": 7, "attested_area": 7,
            "attested_reachable": per * len(HALLS) >= 7}


# ===========================================================================
# 3.  The announcement -- D-11, authority 4, in the show's own shape
# ===========================================================================
# The attested line is "Liner White Star arriving from Earth is now docking in
# bay 5. Passengers will disembark through customs area 7." Four slots: hull,
# origin, bay, area. Everything in them comes from `traffic`, `directory` and
# the identicard's ORIGIN field.
ANNOUNCE = ("{ship} arriving from {origin} is now docking in bay {bay}. "
            "Passengers will disembark through customs area {area}.")


def announcement(seq: dict) -> str:
    return ANNOUNCE.format(ship=seq["ship"], origin=seq["from"],
                           bay=seq["bay_label"], area=seq["area"])


# ===========================================================================
# 4.  Entry class -- WHY a Narn is not processed like an Earth citizen
# ===========================================================================
# Every branch below reads a field that already exists on the identicard and
# nothing else. There is no species manners table and there must not be one.
#
#   EA_CITIZEN         ORIGIN reads EARTH. The station is Earth Alliance
#                      sovereign territory (LOCATIONS/FACTIONS), so an EA
#                      citizen enters by right and the VISAS field is properly
#                      empty. This is why Lyta Alexander's card has three red
#                      rows: she needs no visa.
#   RESIDENT           a non-EA national with a job and quarters aboard. Their
#                      standing IS the record; VISAS is empty for the same
#                      reason and it means something different.
#   TRANSIT            "TRANSIT nD" -- FACTIONS.md 2.3's seven-day mean stay,
#                      written on the card by `resident._visa`.
#   SANCTUARY          "SANCTUARY" -- FACTIONS.md 6.2's 13,000 stateless Narn.
#                      Referred to immigration rather than waved through: that
#                      referral IS the queue the show puts in the background.
#   NO_STATUS          "NO STATUS" -- FACTIONS.md 3.4's "the reason lurkers
#                      avoid readers", and 11.2's underclass.
#   EXPIRED            any of the above with " -- EXPIRED" on it. 3.4 calls
#                      expired status the station's MOST ORDINARY crime.
EA_CITIZEN, RESIDENT, TRANSIT, SANCTUARY, NO_STATUS = (
    "ea_citizen", "resident", "transit", "sanctuary", "no_status")
EXPIRED_SUFFIX = " -- EXPIRED"


def entry_class(card) -> tuple:
    """(class, expired, the field it was read off). Pure card reading."""
    v = card.visas or ""
    expired = v.endswith(EXPIRED_SUFFIX)
    base = v[:-len(EXPIRED_SUFFIX)] if expired else v
    if base.startswith("TRANSIT"):
        return TRANSIT, expired, f"VISAS={v}"
    if base.startswith("SANCTUARY"):
        return SANCTUARY, expired, f"VISAS={v}"
    if base.startswith("NO STATUS"):
        return NO_STATUS, expired, f"VISAS={v}"
    if card.origin == "EARTH":
        return EA_CITIZEN, False, "ORIGIN=EARTH"
    if card.job:
        return RESIDENT, False, f"ORIGIN={card.origin}, job {card.job}"
    return NO_STATUS, False, f"ORIGIN={card.origin}, VISAS empty, no job"


# ===========================================================================
# 5.  The ten stations of 6.3, applied to one card
# ===========================================================================
PASS, FLAG, REFER, REFUSE = "pass", "flag", "refer", "refuse"
_SEVERITY = {PASS: 0, FLAG: 1, REFER: 2, REFUSE: 3}

# CONTRABAND. TRAFFIC-AND-CUSTOMS 6.5 names Dust and concealed weapons
# explicitly (authority 4) and proposes a schedule at authority 5, and it says
# outright that each item "wants a detection probability" and that nothing in
# the document supplies one. INV-250: 1 in 100 arrivals is carrying something
# the scan finds. Constrained from below by 6.5 calling the discretionary search
# "the power that makes customs a CHARACTER" -- a rate near zero makes station 9
# set dressing -- and from above by it being a crime rather than the norm.
# Overturned by any figure for customs seizure volume. Deliberately the same
# order as 6.6's leak, because both are "one arrival in a hundred goes wrong",
# and they are separate constants so that overturning one does not move the
# other.
CONTRABAND_P = 0.01
# ...except for the people with no legal standing, for whom the black market IS
# the economy (FACTIONS.md 11.4, and `resident.NO_STATUS_ROLES`). Four times the
# base rate, which is a guess about magnitude and stated as one.
CONTRABAND_P_NO_STATUS = 0.04


def carrying_contraband(card, day: int = 0, seed: str = "") -> bool:
    p = (CONTRABAND_P_NO_STATUS if card.role in RES.NO_STATUS_ROLES
         else CONTRABAND_P)
    return _u("contraband", card.npc_id, day, seed) < p


def checks(pl, day: int = 0, seed: str = "") -> tuple:
    """TRAFFIC-AND-CUSTOMS 6.3's ten stations, resolved against one card.

    Every row carries the authority the gazetteer gives that station, so a
    reader can see which parts of the player's first ten minutes are on screen
    in the show and which are this project's reasoning. Five of the ten are
    authority 1 -- they are fields on the prop.
    """
    card = pl.card
    cls, expired, why = entry_class(card)
    rows = []

    def row(n, station, auth, result, detail):
        rows.append({"n": n, "station": station, "auth": auth,
                     "result": result, "detail": detail})

    row(1, "Disembark", 4, PASS,
        "ramp from the parking level to the bay concourse; the announcement "
        "has already named the hall and the area (D-11)")
    row(2, "Queue", 5, PASS, "routed by ship, not by species")

    # 3. THE CARD ITSELF. It is an item (`player.IDENTICARD`), so it can be
    # absent, and 6.4 makes losing it a whole arc. No card, no entry.
    if pl.has(PL.IDENTICARD):
        row(3, "Identicard presented", 1, PASS, "inserted into the reader")
    else:
        row(3, "Identicard presented", 1, REFUSE,
            "NO IDENTICARD. 6.4: the card is passport, licence, credit and "
            "medical file at once -- without it there is no record to pull")
        row(10, "Admit / refer / refuse", 5, REFUSE,
            "held pending identity; 6.3 station 10")
        return tuple(rows)

    # 4. Genetic match -- authority 4, and it is what makes the card
    # forgery-proof. A person presenting their OWN card always matches; the
    # interesting case is a forged one, which this project does not model as a
    # separate item yet and says so rather than pretending to roll for it.
    row(4, "Genetic match", 4, PASS,
        "card matched to the bearer's genetic code (6.4); a forged card is "
        "not modelled as a separate item yet")
    row(5, "Record pulled", 1, PASS,
        " / ".join(f"{k}={v}" for k, v, s in RES.identicard(card)
                   if s == RES.FILLED))

    # 6. VISAS -- the field that makes a Narn refugee a different ten minutes
    # from an Earth citizen.
    if expired:
        row(6, "Visa checked", 1, REFUSE,
            f"{why} -- FACTIONS.md 3.4 calls expired status the station's most "
            f"ordinary crime")
    elif cls == EA_CITIZEN:
        row(6, "Visa checked", 1, PASS,
            f"{why}: Earth Alliance sovereign territory, entry by right, "
            f"VISAS properly empty")
    elif cls == RESIDENT:
        row(6, "Visa checked", 1, PASS,
            f"{why}: standing is the residency record, not a visa")
    elif cls == TRANSIT:
        row(6, "Visa checked", 1, PASS, f"{why} (FACTIONS.md 2.3)")
    elif cls == SANCTUARY:
        row(6, "Visa checked", 1, REFER,
            f"{why}: stateless -- referred to immigration (FACTIONS.md 6.2's "
            f"13,000)")
    else:
        row(6, "Visa checked", 1, REFUSE,
            f"{why} -- FACTIONS.md 3.4, and the reason lurkers avoid readers")

    # 7. DES/ATMOS -- the customs board's own subject. Authority 1 both for the
    # field and for the board that explains it.
    if card.atmos_code:
        row(7, "Atmosphere declared", 1, PASS,
            f"{card.species.upper()}/{card.atmos_code} -- the standard mix")
    else:
        row(7, "Atmosphere declared", 1, FLAG,
            f"{card.atmos_class}, unnumbered: the board says others "
            f"\"MAY BE CREATED BY PRIOR ARANGEMENT\" (sic, authority 1) and "
            f"the record reads {card.medical!r}")

    # 8. LICENSED PSI. One in ten thousand (FACTIONS.md 4.1's 10-40 aboard), so
    # this line firing at all is an event.
    if card.licensed_psi:
        row(8, "Telepath status", 1, FLAG,
            "LICENSED PSI: REGISTERED -- Psi Corps liaison notified "
            "(FACTIONS.md 4.1)")
    else:
        row(8, "Telepath status", 1, PASS,
            "no registration on the record; an UNregistered telepath is not a "
            "field the prop carries and is not modelled")

    # 9. The scan.
    if carrying_contraband(card, day, seed):
        row(9, "Scan", 4, REFER,
            "the scan finds something: 6.5 names Dust and concealed weapons "
            "and gives no detection rate, so this one is ours -- INV-250")
    else:
        row(9, "Scan", 4, PASS, "person and baggage clear")

    worst = max(rows, key=lambda r: _SEVERITY[r["result"]])
    row(10, "Admit / refer / refuse", 5, worst["result"],
        {PASS: "through to the arrival concourse",
         FLAG: "through to the arrival concourse, with a note on the record",
         REFER: f"secondary inspection -- station {worst['n']}, "
                f"{worst['station']}",
         REFUSE: f"refused and held for the next ship out -- station "
                 f"{worst['n']}, {worst['station']}"}[worst["result"]])
    return tuple(rows)


def outcome_of(rows) -> str:
    """PASS/FLAG both admit; REFER and REFUSE do not. §6.3's three outcomes."""
    worst = max(_SEVERITY[r["result"]] for r in rows)
    if worst <= _SEVERITY[FLAG]:
        return PL.ADMITTED
    return PL.REFERRED if worst == _SEVERITY[REFER] else PL.REFUSED


# ===========================================================================
# 6.  Where they end up
# ===========================================================================
# THE QUARTERS ARE NOT ASSIGNED HERE. `resident.home_for` already gave this
# person a home, by role and species, from the register's own residence
# functions -- a diplomat to the ambassadorial suites, a breather to the alien
# sector, a visitor to transient habitation, a lurker to one of Downbelow's
# three. The gate does not decide where you live; it decides whether you get to
# go there. That is why the answer to "does the player have a residence" is yes
# and always was: the function that gives 250,000 people theirs gives the player
# one too, and nothing had ever asked it.
#
# The UNIT within the block is new (INV-250) and is a label, not geometry: the
# register addresses `qtr_transient` as one place with an 26x80 m footprint and
# `quarters.py` builds units inside it. Overturned by any on-screen quarters
# numbering; constrained only by the LEVEL plaque convention already in
# `directory.PLACES['lifts']`, which is authority-1 signage of the same kind.
UNITS_PER_BLOCK = 60


def unit_label(card) -> str:
    n = 1 + int(_u("unit", card.npc_id) * UNITS_PER_BLOCK) % UNITS_PER_BLOCK
    letter = "ABCD"[int(_u("unitl", card.npc_id) * 4) % 4]
    return f"{n:02d}-{letter}"


# Where a refusal and a referral GO. Both are proposed rooms that the register
# does not yet address, and saying so is the point: 6.3 proposes a secondary
# inspection room off the hall and a holding area behind it, and LOCATIONS.md
# has neither. They are emitted with `built=False` so the runtime reports an
# unbuilt destination instead of walking the player into a wall.
UNBUILT = {
    "secondary_inspection": "TRAFFIC-AND-CUSTOMS 6.3 proposes a secondary "
                            "inspection room off each hall; LOCATIONS.md does "
                            "not address one",
    "customs_holding": "6.3 proposes a holding area in the hall -- \"a "
                       "refusal is not an arrest, it is a wait for the next "
                       "ship out\"; LOCATIONS.md does not address one",
}


def destination(pl, status: str) -> dict:
    """Where the first ten minutes end, and whether that place is built."""
    if status == PL.ADMITTED:
        return {"place": pl.card.home, "unit": unit_label(pl.card),
                "built": True, "why": "resident.home_for, by role and species"}
    if status == PL.REFERRED:
        return {"place": "secondary_inspection", "unit": "", "built": False,
                "why": UNBUILT["secondary_inspection"]}
    # REFUSED, and 6.6's fork: a refusal you cannot afford to comply with is
    # how Downbelow's population is made. "Downbelow is not where poor people
    # live; it is where the port's failures accumulate."
    if not pl.can_afford_passage():
        return {"place": "downbelow", "unit": "", "built": True,
                "why": f"6.6's leak: {pl.credits} cr against a "
                       f"{PL.PASSAGE_HOME_CR:.0f} cr passage home"}
    return {"place": "customs_holding", "unit": "", "built": False,
            "why": UNBUILT["customs_holding"]}


# ===========================================================================
# 7.  The walk -- steps a runtime can drive
# ===========================================================================
# Each step names a PLACE from the register and an OBJECT that place declares in
# its own `interacts`, and the verb is `interact.verb_of`'s. `_selftest` asserts
# all three, so a step cannot ask a player to use something that is not there.
#
# `cluster` is the z-cluster `deck.z_clusters` puts the place in, and it is
# emitted because of a finding this module made and could not fix: the docking
# bays sit at z=7120 and the customs halls at z=7440 on the SAME deck, which are
# two different walkable clusters. `deck.build_deck` assembles one cluster at a
# time, so the very first leg of the player's first ten minutes -- ramp to
# queue -- is not walkable in the current build. The runtime says so rather than
# pretending; see `godot/scripts/arrival.gd`.
STEP_SPEC = (
    ("berth", "docking_bays", "docking_clamp",
     "The clamps let go. You are on the parking level of bay {bay}."),
    ("disembark", "docking_bays", "bay_door",
     "Down the ramp into the bay concourse."),
    ("queue", "{hall}", "info_board",
     "Customs area {area}. The board tells you which line is yours."),
    ("present", "{hall}", "identicard_reader",
     "Present your identicard."),
    ("scan", "{hall}", "baggage_scanner",
     "Person and baggage, for weapons and Dust."),
    ("desk", "{hall}", "customs_desk",
     "{verdict}"),
    ("welcome", "arrival_concourse", "welcome_board",
     "WELCOME TO BABYLON 5. Smoking permitted in designated areas only."),
    ("orient", "arrival_concourse", "station_schematic_screen",
     "The station shows you a map of itself."),
    ("transit", "lifts", "lift_call",
     "A transport tube to {dest_sector} sector."),
    # THE LAST TWO STEPS NAME A VERB, NOT AN OBJECT, and that is not a
    # flourish -- it is the only form that works. The first version wrote
    # `door` and `bunk`, which are exactly what `qtr_transient` declares and
    # exactly what four of the eleven possible homes do NOT: `downbelow` has a
    # `makeshift_door` and a `brazier` and no bed at all, `alien_sector` has an
    # `airlock_door` because it holds a different atmosphere, `kosh_quarters`
    # has neither, and `league_delegations` has a `reception` instead of a
    # bunk. Resolving through `interact.verb_of` asks the destination what IT
    # has that you can open and what you can rest on, so a Narn who ends up in
    # Downbelow pushes aside a makeshift door and sits at a brazier, which is
    # the correct sentence and nobody had to write it.
    ("door", "{dest}", "@open", "{dest_name}{unit_suffix}."),
    ("bunk", "{dest}", "@rest", "Yours until the visa runs out."),
)


def token_with_verb(place_key: str, verb: str):
    """The first thing this place declares that you can do `verb` to.

    Ordered by the register's own `interacts` order, which is how the rooms are
    described rather than an alphabet, so the first `open` in a quarters is the
    door and not a locker.
    """
    for tok in dr.by_key(place_key)["interacts"]:
        if IX.verb_of(tok) == verb:
            return tok
    return None


@lru_cache(maxsize=256)
def cluster_of(place_key: str):
    """The z-cluster a place's deck assembles it into, or None.

    Read from `deck.z_clusters`/`deck.places_on` -- the same functions the
    walkable build uses -- so this cannot disagree with what gets assembled.
    """
    p = dr.by_key(place_key)
    try:
        zs = DK.z_clusters(p["sector"], p["ring"], p["deck"])
    except Exception:                                       # pragma: no cover
        return None
    for z in zs:
        if any(q["key"] == place_key
               for q in DK.places_on(p["sector"], p["ring"], p["deck"],
                                     z_m=z)):
            return {"sector": p["sector"], "ring": p["ring"],
                    "deck": p["deck"], "z_m": z}
    return None


def steps(seq: dict, pl) -> tuple:
    """The walk, as rows the engine steps through.

    A step is DROPPED rather than emitted broken when the place it needs does
    not exist or does not have the kind of object it wants. That is the same
    rule `resident.workplace_places` follows in the opposite direction: a
    guard that returns a harmless-looking nothing is this project's own
    documented failure mode, so the drop is recorded on the sequence as
    `steps_dropped` and printed, never swallowed.
    """
    dest_key = seq["destination"]["place"]
    dest_built = seq["destination"]["built"]
    dest_p = dr.by_key(dest_key) if dest_built else None
    subs = {
        "bay": seq["bay_label"], "area": seq["area"], "hall": seq["hall"],
        "dest": dest_key,
        "unit": seq["destination"]["unit"] or "",
        "unit_suffix": (f", unit {seq['destination']['unit']}"
                        if seq["destination"]["unit"] else ""),
        "verdict": seq["verdict"],
        "dest_name": dest_p["name"] if dest_p else dest_key,
        "dest_sector": dest_p["sector"].title() if dest_p else "-",
    }
    out, dropped = [], []
    for sid, place_t, token, text_t in STEP_SPEC:
        place = place_t.format(**subs)
        if place == dest_key and not dest_built:
            dropped.append((sid, f"{place} is proposed, not built"))
            continue
        if token.startswith("@"):
            tok = token_with_verb(place, token[1:])
            if tok is None:
                dropped.append((sid, f"{place} declares nothing you can "
                                     f"{token[1:]}"))
                continue
            token = tok
        p = dr.by_key(place)
        group = f"{place}{IX.PLACE_SEP}prop_{token}"
        verb = IX.verb_of(token)
        out.append({
            "id": sid, "place": place, "place_name": p["name"],
            "token": token, "group": group, "verb": verb,
            "pressable": verb in IX.PRESSABLE,
            "responds": verb in IX.RESPONDS,
            "text": text_t.format(**subs),
            "cluster": cluster_of(place),
        })
    return tuple(out), tuple(dropped)


# ===========================================================================
# 8.  The sequence
# ===========================================================================
def sequence(day: int = 0, seed: str = "player", pl=None,
             choices: dict = None) -> dict:
    """One player's arrival, end to end, as data.

    Deterministic in (day, seed, choices). Everything factual in it comes from
    another module and the provenance is carried in `sources` so a reader can
    check rather than trust.
    """
    if pl is None:
        pl = (PL.player_from(choices, seed=seed) if choices
              else PL.random_player(seed))
    a = pick_transport(day, seed)
    i = day_arrivals(day).index(a)
    assign = bay_assignment(day)
    n, berth = assign[i]
    hall = hall_for_bay(n)
    area = area_for(n, seed=seed)
    rows = checks(pl, day, seed)
    status = outcome_of(rows)
    pl.status = status
    dest = destination(pl, status)
    if status == PL.ADMITTED:
        pl.quarters = dest["place"]
    pl.at = "docking_bays"

    verdict = {
        PL.ADMITTED: "Cleared. Welcome to Babylon 5.",
        PL.REFERRED: "Step aside, please. Secondary inspection.",
        PL.REFUSED: "You are not going anywhere. Hold him.",
    }[status]

    seq = {
        "day": day, "seed": seed,
        # -- the ship, from traffic.py --------------------------------------
        "ship": ship_title(a, day, i),
        "ship_type": a["type"], "ship_index": i,
        "hour": a["hour"], "souls": a["souls"], "stay_h": a["stay_h"],
        "from": pl.card.origin,
        # -- the port -------------------------------------------------------
        "bay": n, "berth": berth, "bay_label": bay_label(n, berth),
        "bay_angle_deg": bay_angle_deg(n),
        "hall": hall, "hall_name": dr.by_key(hall)["name"], "area": area,
        # -- the person -----------------------------------------------------
        "npc_id": pl.card.npc_id, "species": pl.card.species,
        "name": pl.card.name, "card_name": pl.card.card_name,
        "role": pl.card.role, "age": pl.card.age,
        "credits": pl.credits,
        "identicard": [{"label": k, "value": v, "state": s}
                       for k, v, s in RES.identicard(pl.card)],
        "entry_class": entry_class(pl.card)[0],
        # -- the processing -------------------------------------------------
        "checks": [dict(r) for r in rows],
        "status": status, "verdict": verdict,
        "destination": dest,
        "home": pl.card.home, "home_name": dr.by_key(pl.card.home)["name"],
        "unit": dest["unit"],
        # -- provenance ------------------------------------------------------
        "sources": {
            "ship": "station/traffic.py :: arrivals() -- the day's manifest",
            "bay": "station/traffic.py :: bay_count() from the schema; "
                   "assignment by occupancy, D-2",
            "hall": "station/directory.py angles for customs_north/south",
            "area": "station/customs.py :: DESKS; \"customs area 7\", TKO",
            "card": "station/npc/resident.py :: identicard(), off the "
                    "authority-1 prop",
            "checks": "docs/gazetteer/TRAFFIC-AND-CUSTOMS.md 6.3",
            "home": "station/npc/resident.py :: home_for()",
            "verbs": "station/interact.py :: verb_of()",
        },
    }
    seq["announcement"] = announcement(seq)
    _steps, _dropped = steps(seq, pl)
    seq["steps"] = [dict(s) for s in _steps]
    seq["steps_dropped"] = [{"id": a, "why": b}
                            for a, b in _dropped]
    seq["boards"] = {
        "welcome": list(CU.WELCOME_BOARD["lines"]),
        "atmosphere": list(SG.BOARDS["customs_atmosphere"]["lines"]),
        "procedures": list(SG.BOARDS["customs_procedures"]["lines"]),
    }
    return seq


DEFAULT_EMIT = os.path.join(ROOT, "station", "generated", "arrival.json")

# ---------------------------------------------------------------------------
# The build the playable scene stands in
# ---------------------------------------------------------------------------
# WHICH CLUSTER, AND WHY IT IS THE CUSTOMS ONE. `cluster_of` reports that the
# docking bays and the customs halls are on the same deck at different z, so
# `deck.build_deck` -- which assembles ONE cluster -- cannot hold both. The
# playable arrival therefore runs on the cluster that carries the processing:
# `customs_north`, `arrival_concourse`, `customs_south`. The two steps before it
# are narrated by D-11's announcement, which is what the show does with them
# anyway, and the steps after it are on three further clusters and are reported
# by `arrival.gd` as off-build rather than silently dropped.
PLAY_CLUSTER = ("blue", 0, 0, 7440.0)


def build_playable(cluster=PLAY_CLUSTER, out_dir=None, emit_json=True):
    """Assemble the cluster the playable arrival runs on. Returns the paths.

    This calls the SAME `deck.build_deck` / `deck.build_collision` the walk gate
    calls and the same `walkable.interact_rows` that writes its sidecar -- so
    the scene a player stands in is the scene `walkable.py --deck` measures, and
    there is one description of how a deck becomes a build. Nothing here is a
    second exporter.
    """
    import interior as it                                    # noqa: PLC0415
    import collision as C                                    # noqa: PLC0415
    import walkable as WK                                    # noqa: PLC0415

    sector, ring, dk, z = cluster
    out_dir = out_dir or os.path.join(ROOT, "station/generated/scene/deck")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{sector}_{ring}_{dk}_z{int(z)}"
    schema, profile = it.load()
    v, t, g, s = DK.build_deck(schema, profile, sector, ring, dk, z_m=z)
    cv, ct, cm = DK.build_collision(schema, profile, sector, ring, dk,
                                    z_m=z, props=True)
    C.write_obj(os.path.join(out_dir, f"{stem}_col.obj"), cv, ct,
                cm.get("groups"))
    DK.write_obj(os.path.join(out_dir, f"{stem}.obj"), v, t, g)
    with open(os.path.join(out_dir, f"{stem}_interact.json"), "w") as f:
        json.dump(WK.interact_rows(v, t, g), f)
    with open(os.path.join(out_dir, f"{stem}_actors.json"), "w") as f:
        json.dump(s.get("actors", []), f)
    WK._glb(os.path.join(out_dir, f"{stem}.obj"),
            os.path.join(out_dir, f"{stem}.glb"))
    WK._glb(os.path.join(out_dir, f"{stem}_col.obj"),
            os.path.join(out_dir, f"{stem}_col.glb"))
    paths = {
        "stem": stem, "dir": out_dir,
        "glb": os.path.join(out_dir, f"{stem}.glb"),
        "collision": os.path.join(out_dir, f"{stem}_col.glb"),
        "interact": os.path.join(out_dir, f"{stem}_interact.json"),
        "actors": os.path.join(out_dir, f"{stem}_actors.json"),
        "spawn": list(s["spawn"]), "spawn_at": s["spawn_at"],
        # `build_deck`'s `stats["rooms"]` is a COUNT, not a list. The room keys
        # come from the same `places_on` the plan was built from.
        "room_count": s.get("rooms", 0),
        "rooms": [q["key"] for q in DK.places_on(sector, ring, dk, z_m=z)],
        "tris": len(t), "collision_tris": len(ct),
    }
    if emit_json:
        paths["arrival"] = write_arrival_sidecar(out_dir, stem, paths)
    return paths


def spawn_for(cluster=PLAY_CLUSTER):
    """Where the body starts, WITHOUT rebuilding the render mesh.

    `build_deck` computes this as `collision.stand_at(cmeta, here[0].angle)` and
    takes ten minutes to get there; the collision shell alone takes twenty-seven
    seconds and carries the same `cmeta`. Same two functions, same answer, one
    fortieth of the cost -- which is what makes re-running the playable scene
    cheap enough to iterate on.
    """
    import interior as it                                    # noqa: PLC0415
    import collision as C                                    # noqa: PLC0415
    sector, ring, dk, z = cluster
    schema, profile = it.load()
    _cv, _ct, cm = DK.build_collision(schema, profile, sector, ring, dk,
                                      z_m=z, props=True)
    dp = DK.deck_plan(schema, profile, sector, ring, dk, z)
    here = dp["here"][0]
    return list(C.stand_at(cm, here["angle_deg"])), here["key"]


def write_arrival_sidecar(out_dir, stem, paths=None, day: int = 0,
                          seed: str = "player", choices: dict = None) -> str:
    """The sequence, beside the mesh, WITH the build it is to be played on.

    THE SCENE IS SELF-DESCRIBING ON PURPOSE. The first run of `arrival.tscn`
    was given `--spawn=0,0,0`, which on a ring deck at radius 210 m is the spin
    axis: the body fell for two minutes and the run was killed by a timeout
    that looked exactly like a slow load. A sidecar that names the mesh it
    belongs to and the point a body can stand on cannot be launched against the
    wrong world.
    """
    seq = sequence(day=day, seed=seed, choices=choices)
    if paths:
        seq["build"] = {k: paths.get(k) for k in
                        ("glb", "collision", "interact", "actors",
                         "spawn", "spawn_at", "rooms")}
    path = os.path.join(out_dir, f"{stem}_arrival.json")
    with open(path, "w") as f:
        json.dump(seq, f, indent=1)
    return path


def emit(path: str = DEFAULT_EMIT, day: int = 0, seed: str = "player",
         choices: dict = None) -> str:
    seq = sequence(day=day, seed=seed, choices=choices)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(seq, f, indent=1)
    return path


# ===========================================================================
# 9.  Reporting
# ===========================================================================
def narrate(seq: dict, out=print) -> None:
    out(f"  {seq['announcement']}")
    out("")
    out(f"  YOU ARE  {seq['name'] or '<no attested name>'} -- "
        f"{seq['species']}, {seq['from']}, {seq['role']}, aged {seq['age']}, "
        f"{seq['credits']} cr")
    out(f"  ABOARD   {seq['ship']} ({seq['ship_type']}, {seq['souls']} souls) "
        f"at {seq['hour']:04.1f} EMT, berthed bay {seq['bay_label']}")
    out(f"  ROUTED   {seq['hall_name']}, area {seq['area']}")
    out("")
    out("  THE READER (TRAFFIC-AND-CUSTOMS 6.3)")
    for c in seq["checks"]:
        mark = {"pass": "  ", "flag": " !", "refer": " >", "refuse": " X"}
        out(f"   {mark[c['result']]} {c['n']:2d} {c['station']:<24} "
            f"auth {c['auth']}  {c['detail'][:96]}")
    out("")
    out(f"  {seq['verdict'].upper()}  -> {seq['destination']['place']}"
        + (f" unit {seq['destination']['unit']}"
           if seq['destination']['unit'] else "")
        + ("" if seq["destination"]["built"] else "   [NOT BUILT]"))
    out(f"     {seq['destination']['why']}")
    out("")
    out("  THE WALK")
    for s in seq["steps"]:
        cl = s["cluster"]
        where = ("-" if cl is None
                 else f"{cl['sector']}/{cl['ring']}/{cl['deck']}"
                      f" z{cl['z_m']:.0f}")
        out(f"     {s['id']:<9} {s['place']:<20} {s['verb']:<8} "
            f"{where:<20} {s['text'][:52]}")


def report(out=print):
    out("THE FIRST TEN MINUTES -- arrive, be processed, be given a room")
    out("")
    ac = area_cross_check()
    out(f"the port: {TR.bay_count()} bays x {len(BAY_BERTHS)} berths, "
        f"{len(arrivals_with_passengers(0))} passenger arrivals on day 0, "
        f"{len(HALLS)} halls x {ac['built_per_hall']} areas = "
        f"{ac['built_across_pair']} against the gazetteer's "
        f"{ac['gazetteer_across_pair']}")
    out("")
    for day, seed in ((0, "player"), (0, "b"), (3, "c")):
        out(f"--- day {day}, seed {seed!r} "
            + "-" * 40)
        narrate(sequence(day=day, seed=seed), out=out)
        out("")
    out("--- a chosen character: a Narn refugee "
        + "-" * 24)
    narrate(sequence(day=1, seed="narn1",
                     choices={"species": "narn", "role": "refugee"}), out=out)


def matrix(out=print, day: int = 0):
    """The outcome for every species and role. IT IS NOT ALL THE SAME.

    This is the evidence for the claim in the docstring -- that processing
    varies with who you are -- and it is a table rather than a sentence so it
    can be read for the cases that look wrong.
    """
    out("OUTCOME BY SPECIES AND ROLE -- the four card fields doing the work")
    out(f"{'species':<10} {'role':<12} {'origin':<20} {'VISAS':<22} "
        f"{'class':<10} outcome")
    seen = {}
    for sp in sorted(PL.PLAYABLE_MIX):
        for role in ("visitor", "refugee", "lurker", "merchant", "diplomat",
                     "engineer"):
            try:
                pl = PL.player_from({"species": sp, "role": role},
                                    seed=f"{sp}-{role}")
            except KeyError:                                # pragma: no cover
                continue
            rows = checks(pl, day, f"{sp}-{role}")
            st = outcome_of(rows)
            seen[st] = seen.get(st, 0) + 1
            cls, exp, _why = entry_class(pl.card)
            out(f"{sp:<10} {role:<12} {pl.card.origin:<20} "
                f"{(pl.card.visas or '-'):<22} "
                f"{cls + ('/exp' if exp else ''):<10} {st}")
    out("")
    out("  " + ", ".join(f"{k}: {v}" for k, v in sorted(seen.items())))
    return seen


# ===========================================================================
# 10.  Gates
# ===========================================================================
def _selftest(out=print):                                        # noqa: C901
    global CONTRABAND_P, CONTRABAND_P_NO_STATUS
    failed = []
    n = 0

    def check(name, cond, detail=""):
        nonlocal n
        n += 1
        if cond:
            out(f"PASS  {name}" + (f"  -- {detail}" if detail else ""))
        else:
            failed.append(name)
            out(f"FAIL  {name}  -- {detail}")

    seq = sequence(0, "player")

    # -- 1. THE SHIP IS THE PORT'S, not this module's ----------------------
    day0 = day_arrivals(0)
    ship = day0[seq["ship_index"]]
    check("the player's transport is one of traffic.arrivals()' own ships",
          ship["type"] == seq["ship_type"] and ship["hour"] == seq["hour"]
          and ship["souls"] == seq["souls"],
          f"index {seq['ship_index']} of {len(day0)}: {seq['ship_type']} at "
          f"{seq['hour']:.2f} h with {seq['souls']} aboard")
    # NEGATIVE CONTROL: a ship this module made up must NOT be findable in the
    # port's day, or the check above passes for anything.
    fake = {"day": 0, "hour": 9.0, "type": "transport", "berth": "bay",
            "souls": 77, "stay_h": 8.0}
    check("...and a ship this module invented is NOT in that day",
          fake not in day0)
    check("the player is only ever on a ship that lands passengers in a bay",
          seq["ship_type"] in passenger_types(),
          f"{seq['ship_type']} of {passenger_types()}")

    # -- 2. bays --------------------------------------------------------------
    bays = TR.bay_count()
    assign = bay_assignment(0)
    clash = []
    arr = day_arrivals(0)
    for i, (bn, bb) in assign.items():
        for j, (cn, cb) in assign.items():
            if j <= i or (bn, bb) != (cn, cb):
                continue
            a, b = arr[i], arr[j]
            if (a["hour"] < b["hour"] + b["stay_h"]
                    and b["hour"] < a["hour"] + a["stay_h"]):
                clash.append((i, j, bn, bb))
    check("no two hulls hold the same berth at the same time",
          not clash, f"{len(assign)} bay-tier arrivals over {bays} bays x "
                     f"{len(BAY_BERTHS)} berths, {len(clash)} clashes")
    # NEGATIVE CONTROL: put every hull in berth 1A and the same test must fire.
    ctl = {i: (1, "A") for i in assign}
    ctl_clash = 0
    for i in ctl:
        for j in ctl:
            if j <= i:
                continue
            a, b = arr[i], arr[j]
            if (a["hour"] < b["hour"] + b["stay_h"]
                    and b["hour"] < a["hour"] + a["stay_h"]):
                ctl_clash += 1
    check("...and the same test fires when every hull is put in berth 1A",
          ctl_clash > 0, f"{ctl_clash} clashes in the control")
    check("every assigned bay is a real bay",
          all(1 <= v[0] <= bays and v[1] in BAY_BERTHS
              for v in assign.values()))

    # -- 3. the hall is derived from the register's angles ------------------
    check("bay 1 (0 deg) is routed to the hall at 40 deg, not the one at 220",
          hall_for_bay(1) == "customs_north",
          f"{hall_for_bay(1)}; north is at "
          f"{dr.by_key('customs_north')['angle_deg']:.0f} deg, south at "
          f"{dr.by_key('customs_south')['angle_deg']:.0f}")
    mid = max(1, int(round(bays / 2)))
    check("...and a bay on the far side goes to the far hall",
          hall_for_bay(mid + 1) == "customs_south",
          f"bay {mid + 1} at {bay_angle_deg(mid + 1):.0f} deg -> "
          f"{hall_for_bay(mid + 1)}")
    both = {hall_for_bay(k) for k in range(1, bays + 1)}
    check("both halls are used", both == set(HALLS), str(sorted(both)))
    # NEGATIVE CONTROL: routing by angle has to beat routing by parity, or the
    # geometry is doing nothing. Count how many bays the two rules disagree on.
    par = sum(1 for k in range(1, bays + 1)
              if hall_for_bay(k) != HALLS[k % 2])
    check("...and the angle rule is not just alternating bays",
          par > bays // 4, f"{par} of {bays} bays differ from parity routing")

    # -- 4. EVERY STEP IS A REAL PLACE AND A DECLARED OBJECT ----------------
    # The strongest join in the module: a step cannot ask a player to use
    # something the register does not say is in that room.
    bad = []
    for s in seq["steps"]:
        p = dr.by_key(s["place"])
        if s["token"] not in p["interacts"]:
            bad.append(f"{s['id']}: {s['place']} does not declare "
                       f"{s['token']} (it has {p['interacts']})")
    check("every step's object is declared in that place's own `interacts`",
          not bad, f"{len(seq['steps'])} steps" + ("; " + "; ".join(bad[:3])
                                                   if bad else ""))
    # NEGATIVE CONTROL: a step naming a plausible object the room does not
    # declare must be caught.
    p = dr.by_key("arrival_concourse")
    check("...and the same test rejects an object that room does not have",
          "identicard_reader" not in p["interacts"],
          f"arrival_concourse declares {p['interacts']}")

    # AND ACROSS EVERY DESTINATION, not just the transient quarters. This is
    # the gate that caught the whole `@open`/`@rest` design: written as literal
    # `door` and `bunk` tokens it failed on Downbelow (a makeshift door and a
    # brazier), the Alien Sector (an airlock, a different atmosphere) and the
    # League delegations (a reception and no bed).
    bad3, homes = [], set()
    for sp in sorted(PL.PLAYABLE_MIX):
        for role in sorted(sched.ROLES_BY_KEY):
            pl2 = PL.player_from({"species": sp, "role": role},
                                 seed=f"{sp}-{role}")
            for st in (PL.ADMITTED, PL.REFERRED, PL.REFUSED):
                pl2.status = st
                d2 = destination(pl2, st)
                homes.add(d2["place"])
                s2 = dict(seq, destination=d2, verdict="x")
                for stp in steps(s2, pl2)[0]:
                    if stp["token"] not in dr.by_key(stp["place"])["interacts"]:
                        bad3.append(f"{d2['place']}/{stp['id']}: "
                                    f"{stp['token']}")
    check("every step of every species x role x outcome names an object its "
          "own room declares -- 15 species, 19 roles, 3 outcomes",
          not bad3, f"{len(homes)} distinct destinations "
                    f"{sorted(homes)[:6]}...; {len(bad3)} bad"
                    + (f": {bad3[:3]}" if bad3 else ""))
    # NEGATIVE CONTROL for the verb resolution: Downbelow genuinely has no bed,
    # so a literal `bunk` step there would be unresolvable. `token_with_verb`
    # must return something DIFFERENT from the quarters' answer, or it is not
    # reading the room.
    check("...because the last two steps resolve by VERB: a bed in quarters, "
          "a brazier in Downbelow, an airlock in the Alien Sector",
          (token_with_verb("qtr_transient", "rest"),
           token_with_verb("downbelow", "rest"),
           token_with_verb("downbelow", "open"),
           token_with_verb("alien_sector", "open"))
          == ("bunk", "brazier", "makeshift_door", "airlock_door"),
          str((token_with_verb("qtr_transient", "rest"),
               token_with_verb("downbelow", "rest"),
               token_with_verb("downbelow", "open"),
               token_with_verb("alien_sector", "open"))))
    check("...and a room with nothing to rest on drops the step instead of "
          "emitting one that can never resolve",
          token_with_verb("league_delegations", "rest") is None,
          str(dr.by_key("league_delegations")["interacts"]))

    # -- 5. ONE SOURCE FOR THE VERB ------------------------------------------
    wrong = [s for s in seq["steps"] if s["verb"] != IX.verb_of(s["token"])]
    check("every step's verb is interact.verb_of's, not a second opinion",
          not wrong, str([(s["token"], s["verb"]) for s in wrong[:3]]))
    check("the identicard reader is OPERATE and it responds",
          IX.verb_of("identicard_reader") == "operate"
          and "operate" in IX.RESPONDS,
          "so a keypress has somewhere to go")
    presses = [s for s in seq["steps"] if s["pressable"]]
    check("the sequence contains at least one thing a player PRESSES",
          len(presses) >= 3, f"{len(presses)} of {len(seq['steps'])}: "
                             f"{[s['id'] for s in presses]}")

    # -- 6. IT VARIES WITH WHO YOU ARE ---------------------------------------
    outs = matrix(out=lambda *_a, **_k: None)
    check("processing is NOT the same for everybody -- the four card fields "
          "produce more than one outcome across species and role",
          len(outs) >= 2, str(outs))
    ea = PL.player_from({"species": "human", "role": "engineer"}, seed="ea")
    nr = PL.player_from({"species": "narn", "role": "refugee"}, seed="nr")
    ea_rows, nr_rows = checks(ea, 0, "ea"), checks(nr, 0, "nr")
    ea_visa = next(r for r in ea_rows if r["n"] == 6)
    nr_visa = next(r for r in nr_rows if r["n"] == 6)
    check("an Earth citizen clears station 6 and a stateless Narn does not",
          ea_visa["result"] == PASS and nr_visa["result"] == REFER,
          f"human/engineer {ea_visa['result']} ({ea.card.origin}, "
          f"{ea.card.visas or 'no visa'}) vs narn/refugee "
          f"{nr_visa['result']} ({nr.card.origin}, {nr.card.visas})")
    check("...and they end up in different rooms",
          destination(ea, outcome_of(ea_rows))["place"]
          != destination(nr, outcome_of(nr_rows))["place"],
          f"{destination(ea, outcome_of(ea_rows))['place']} vs "
          f"{destination(nr, outcome_of(nr_rows))['place']}")
    # NEGATIVE CONTROL: read the SAME card with the origin/visa branch removed
    # -- everybody becomes an EA citizen and the two agree. If they still
    # differed, something other than the card would be deciding.
    both_ea = (entry_class(nr.card)[0] != EA_CITIZEN
               and entry_class(RES.replace_origin(nr.card)
                               if hasattr(RES, "replace_origin")
                               else nr.card)[0] is not None)
    import dataclasses
    flat = entry_class(dataclasses.replace(nr.card, origin="EARTH",
                                           visas=""))[0]
    check("...and blanking ORIGIN and VISAS collapses the difference, so it "
          "is those two fields doing the work",
          flat == EA_CITIZEN and both_ea,
          f"a Narn refugee with ORIGIN=EARTH and no visa reads {flat!r}")

    # -- 7. no card, no entry -------------------------------------------------
    lost = PL.random_player("lost")
    lost.drop(PL.IDENTICARD)
    lrows = checks(lost, 0, "lost")
    check("without the identicard the record cannot be pulled and entry is "
          "refused -- 6.4, the card IS the passport",
          outcome_of(lrows) == PL.REFUSED and len(lrows) == 4,
          f"{len(lrows)} stations reached, {outcome_of(lrows)}")
    lost.take(PL.IDENTICARD)
    check("...and giving it back restores a full ten-station pass",
          len(checks(lost, 0, "lost")) == 10)

    # -- 8. determinism -------------------------------------------------------
    check("a (day, seed) gives the same arrival twice",
          sequence(2, "z") == sequence(2, "z"))
    check("...and two days differ", sequence(2, "z") != sequence(3, "z"))
    check("...and two seeds differ", sequence(2, "z") != sequence(2, "y"))

    # -- 9. the destination is a real room, or declared unbuilt --------------
    bad2 = []
    for i in range(120):
        s = sequence(i % 7, f"p{i}")
        d = s["destination"]
        if d["built"]:
            try:
                dr.by_key(d["place"])
            except KeyError:
                bad2.append(d["place"])
        elif d["place"] not in UNBUILT:
            bad2.append(d["place"])
    check("120 arrivals all end in a register place or a DECLARED unbuilt one",
          not bad2, f"{sorted(set(bad2))[:4]}")
    admitted = [sequence(i % 7, f"p{i}") for i in range(60)]
    got_home = [s for s in admitted if s["status"] == PL.ADMITTED]
    check("every admitted arrival is given quarters by resident.home_for",
          all(s["destination"]["place"] == s["home"] for s in got_home)
          and got_home, f"{len(got_home)} of 60 admitted")
    check("...and the unit label is a label, not a place",
          all(s["unit"] and "-" in s["unit"] for s in got_home))

    # -- 10. the CONTRABAND rate is the declared one, and it can fire --------
    hits = sum(1 for i in range(3000)
               if carrying_contraband(PL.random_player(f"k{i}").card, 0, ""))
    check("the scan finds something at about the declared 1 in 100",
          0.004 <= hits / 3000.0 <= 0.03,
          f"{hits}/3000 = {hits / 3000.0:.4f} against {CONTRABAND_P}")
    keep = (CONTRABAND_P, CONTRABAND_P_NO_STATUS)
    try:
        CONTRABAND_P = CONTRABAND_P_NO_STATUS = 1.0
        allhit = sum(1 for i in range(200)
                     if carrying_contraband(PL.random_player(f"k{i}").card,
                                            0, ""))
        srow = next(r for r in checks(PL.random_player("k0"), 0, "")
                    if r["n"] == 9)
        check("...and with the rate at 1.0 EVERY arrival is stopped at station "
              "9, so the scan is a live branch and not a decoration",
              allhit == 200 and srow["result"] == REFER,
              f"{allhit}/200 flagged, station 9 = {srow['result']}")
    finally:
        CONTRABAND_P, CONTRABAND_P_NO_STATUS = keep

    # -- 11. THE FINDING: the first leg crosses a cluster boundary -----------
    cl = {s["id"]: s["cluster"] for s in seq["steps"]}
    bay_c, hall_c = cl.get("disembark"), cl.get("queue")
    check("the bay and the customs hall are on the same DECK",
          bay_c and hall_c and (bay_c["sector"], bay_c["ring"], bay_c["deck"])
          == (hall_c["sector"], hall_c["ring"], hall_c["deck"]),
          f"{bay_c} / {hall_c}")
    check("...and they are in DIFFERENT z-clusters, which is why the ramp-to-"
          "queue leg is not walkable in one assembled build -- reported, not "
          "hidden",
          bay_c and hall_c and bay_c["z_m"] != hall_c["z_m"],
          f"bays z={bay_c['z_m']:.0f}, halls z={hall_c['z_m']:.0f}, "
          f"{abs(bay_c['z_m'] - hall_c['z_m']):.0f} m apart")
    onhall = [s["id"] for s in seq["steps"]
              if s["cluster"] and hall_c
              and s["cluster"]["z_m"] == hall_c["z_m"]]
    check("the customs cluster carries the processing half of the sequence",
          len(onhall) >= 5, f"{len(onhall)} steps: {onhall}")

    # -- 12. the announcement is the show's shape ---------------------------
    ann = seq["announcement"]
    check("the announcement is D-11's four-slot line",
          ann.startswith(seq["ship"]) and f"bay {seq['bay_label']}" in ann
          and f"customs area {seq['area']}" in ann, ann)

    # -- 13. the sources still say what is quoted ---------------------------
    check("the gazetteer is where traffic.py says it is",
          os.path.exists(GAZETTEER))
    if os.path.exists(GAZETTEER):
        txt = open(GAZETTEER).read()
        for phrase in ("The process a visitor goes through",
                       "customs area 7",
                       "could not afford a ticket home",
                       "Passengers will disembark through customs area 7"):
            check(f"the gazetteer still says {phrase!r}",
                  phrase.lower() in txt.lower())
    check("the welcome board this module prints is customs.py's transcription",
          any("BABYLON 5" == ln for ln, _c in CU.WELCOME_BOARD["lines"]))
    check("...and the atmosphere board is signage.py's, sic and all",
          any("ARANGEMENT" in ln
              for ln in SG.BOARDS["customs_atmosphere"]["lines"]))

    # -- 14. the emitted JSON round-trips ------------------------------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        pth = emit(os.path.join(td, "a.json"), 0, "player")
        nbytes = os.path.getsize(pth)
        back = json.load(open(pth))
    check("the sidecar the engine reads round-trips through JSON",
          back["steps"] == seq["steps"] and back["checks"] == seq["checks"],
          f"{len(back['steps'])} steps, {len(back['checks'])} checks, "
          f"{nbytes} bytes")

    # -- 15. the cross-check that is a GAP, printed ---------------------------
    ac = area_cross_check()
    out("")
    out(f"cross-check: the built hall has {ac['built_per_hall']} processing "
        f"areas, so {ac['built_across_pair']} across the pair, against "
        f"TRAFFIC-AND-CUSTOMS T-X1's {ac['gazetteer_across_pair']}. "
        f"\"customs area 7\" is reachable either way: "
        f"{ac['attested_reachable']}")

    out("")
    out(f"{n - len(failed)}/{n} passed")
    return not failed


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--emit", nargs="?", const=DEFAULT_EMIT, default=None)
    ap.add_argument("--build", action="store_true",
                    help="assemble the cluster the playable arrival runs on")
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--seed", default="player")
    ap.add_argument("--choose", nargs="*", metavar="field=value", default=None)
    a = ap.parse_args()
    ch = dict(x.split("=", 1) for x in (a.choose or [])) or None
    if a.build:
        info = build_playable()
        for k in ("stem", "glb", "collision", "interact", "arrival",
                  "spawn_at", "spawn", "rooms", "tris", "collision_tris"):
            print(f"  {k:<15} {info.get(k)}")
        raise SystemExit(0)
    if a.emit:
        print(emit(a.emit, a.day, a.seed, ch))
        narrate(sequence(a.day, a.seed, choices=ch))
        raise SystemExit(0)
    if a.matrix:
        matrix()
        raise SystemExit(0)
    if a.report and not a.selftest:
        report()
        raise SystemExit(0)
    ok = _selftest()
    if a.report:
        print()
        report()
    raise SystemExit(0 if ok else 1)
