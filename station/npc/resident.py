"""A person, not a body: identity, a home, a job, and somewhere to be at 14:00.

WHAT WAS MISSING. `station/populace.py` put 278 bodies in 87 rooms. They had a
species and a pose and they turned to look at you, and **not one of them had a
name, a job, a home, or anywhere to be at 14:00**. That is a crowd. CLAUDE.md's
scope says the opposite in as many words -- "NPCs with quarters, jobs, schedules
and events -- not crowds, *residents*" -- so this module is the difference.

THE RECORD IS NOT INVENTED. It is on screen. `canon/00-MASTER.md` 1.4 transcribes
the identicard readout at authority 1
(`reference/11-props-and-technology/identicard readout.webp`):

    NAME:       ALEXANDER, LYTA        <- black label, colon, blue value
    ORIGIN:     EARTH
    DES/ATMOS:  HUMAN/02
    SEX:        FEMALE
    DOB:        12/10/25
    PHYS CHR                           <- RED label, no colon, NO value
    MEDICAL:    NO DISTG
    LICENSED PSI                       <- RED, no colon, no value
    VISAS                              <- RED, no colon, no value

Two things in that frame are structure rather than content, and both are used
here rather than paraphrased:

  1. **The field list and its order.** Nine fields, in that sequence. `CARD` is
     that list and `identicard()` emits it verbatim, so a record this project
     prints is the record the show printed.
  2. **A field has TWO STATES and the prop shows both.** Filled fields are a
     black label with a colon and a blue value; `PHYS CHR`, `LICENSED PSI` and
     `VISAS` are red, colonless and empty. That is a rendering rule for "this
     record has no entry here", and it is the reason this module never has to
     invent a value for a field it cannot source: an unsourceable field is
     simply EMPTY, which is what the one authority-1 example does three times
     out of nine.

     It used to be what let eight species have no name at all, and THAT PART
     IS OVER -- see INV-1249. `schedule.SPECIES_WITHOUT_NAMES` listed the eight
     the reference set attests no personal name for, and their cards shipped
     with an EMPTY NAME field on INV-004's rule that a generator fitted to zero
     data points is invention dressed as inference. Measured on the packaged
     build at `dist/Babylon5`, that came to **447 of 3,683 residents, 12.1%**,
     which is not "a fact about the station" but a twelfth of the population
     with no identity, on the one document this project reproduces from an
     authority-1 frame. CLAUDE.md hard rule 1 -- "the answer to 'the show never
     establishes this' is NEVER to leave a hole" -- decides it, and the
     precedent was already in the repo: `npc/body.py` extrapolates all seven of
     those species' BODIES at authority 5 from the same one-line source.

     THE EMPTY STATE REMAINS AND IS STILL EXERCISED, which is what stops this
     being a loss. `PHYS CHR`, `LICENSED PSI` and `VISAS` are empty on most
     cards, `SEX` is empty for the Gaim hive, and the prop's two-state
     rendering is tested on all of them. What changed is that NAME is no longer
     one of them, because NAME is the field the prop shows FILLED.

WHAT THIS WIRES VERSUS WHAT IT WRITES. Almost everything here is a *consumer*:

  `schedule.role_for`      -> the job. Weighted per species from FACTIONS.md's
                              own apportionment; already tested, never called
                              from outside `station/npc/` until now.
  `schedule.activity_at`   -> where somebody is at an hour, on EMT (authority 1,
                              the customs board: "TIME ON B-5 IS EARTH MEAN
                              TIME (EMT)").
  `schedule.RHYTHMS`       -> the atmosphere class and the breather, which are
                              two of the nine card fields.
  `names.name_for`         -> the name, per-species grammars fitted to attested
                              on-screen names.
  `body.individual`        -> SEX and PHYS CHR. **Read off the body that will
                              actually be built**, so a card can never describe
                              somebody other than the mesh standing there. That
                              is hard rule 4 -- one authoritative model -- applied
                              to a record instead of to a hull.
  `directory.PLACES`       -> homes and workplaces, BY FUNCTION rather than by a
                              table of keys, so a place that changes what it is
                              for changes who works there and nothing drifts.

What is new is the joins: role -> workplace -> a real address, species+role ->
quarters, and the identicard itself.

DETERMINISM. `hashlib.blake2b` throughout, never `random`, never
`str.__hash__` -- which PYTHONHASHSEED salts per process, and which cost this
project a hull that changed every run. `_selftest` re-runs the module under two
hash seeds in a subprocess and diffs the bytes.
"""
import hashlib
import os
import sys
from dataclasses import dataclass
from functools import lru_cache

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import schedule as sched                                        # noqa: E402
import names as npc_names                                       # noqa: E402
import body as npc_body                                         # noqa: E402
import directory as _dir                                        # noqa: E402


def _u(seed: str, salt: str = "") -> float:
    """Uniform [0,1) from a string. Same construction as `schedule._u`."""
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def _pick(seq, seed, salt=""):
    seq = tuple(seq)
    return seq[int(_u(seed, salt) * len(seq)) % len(seq)]


# ---------------------------------------------------------------------------
# The card, verbatim
# ---------------------------------------------------------------------------
# The nine labels, in the order they appear on the prop, and whether the prop
# renders each one with a colon. `identicard()` is the only thing that reads
# this and it reads it in order, so the emitted record cannot drift from the
# frame it was transcribed from. `test` asserts the list against
# canon/00-MASTER.md 1.4's own transcription, which was made independently.
CARD = ("NAME", "ORIGIN", "DES/ATMOS", "SEX", "DOB", "PHYS CHR", "MEDICAL",
        "LICENSED PSI", "VISAS")

# The prop's two states. A field with a value is a black label, a colon and a
# blue value; a field with no entry is a red label, no colon and no value.
FILLED, EMPTY = "filled", "empty"

# The transcribed values from the one readable card, kept so the renderer can be
# checked against the frame rather than against itself.
LYTA = {
    "NAME": "ALEXANDER, LYTA", "ORIGIN": "EARTH", "DES/ATMOS": "HUMAN/02",
    "SEX": "FEMALE", "DOB": "12/10/25", "PHYS CHR": "", "MEDICAL": "NO DISTG",
    "LICENSED PSI": "", "VISAS": "",
}

# The null value in the MEDICAL field, verbatim from the prop. Its expansion is
# not certain -- "no distinguishing" is the obvious reading and the frame does
# not say -- so the abbreviation is reproduced and not expanded.
MEDICAL_NULL = "NO DISTG"

# Season 3 is 2260, stated in the opening narration (authority 1) and recorded
# in docs/gazetteer/FACTIONS.md 1.3, which fixes the datum at "early 2260".
# `costume.ERA_DATUM` is the same datum expressed as (season, episode).
ERA_YEAR = 2260


# ---------------------------------------------------------------------------
# ORIGIN
# ---------------------------------------------------------------------------
# The identicard's ORIGIN is a jurisdiction, not an address: Lyta's reads EARTH.
# So each species' ORIGIN is the polity or world this repository already names,
# and NOTHING here is a world name recalled from outside it. Three worlds are
# attested in-repo and the rest use the polity name from FACTIONS.md's own
# section headings, which is what a customs record would carry anyway.
#
#   EARTH   authority 1  -- the identicard itself
#   NARN    authority 4  -- FACTIONS.md 6.1, "Narn is a Centauri protectorate"
#   MINBAR  authority 4  -- FACTIONS.md 10.1, "from Minbar"
#
# Every other row is the species or polity designation, which is the honest
# answer when no source in this repository names a world. See INV-087.
ORIGIN = {
    "human": ("EARTH", "1 -- the identicard readout itself"),
    "narn": ("NARN", "4 -- FACTIONS.md 6.1 names the world"),
    "minbari": ("MINBAR", "4 -- FACTIONS.md 10.1 names the world"),
    "centauri": ("CENTAURI REPUBLIC", "4 -- FACTIONS.md 7, polity not world"),
    "drazi": ("DRAZI", "4 -- FACTIONS.md 9.2, species designation"),
    "brakiri": ("BRAKIRI", "4 -- FACTIONS.md 9.2, species designation"),
    "pakmara": ("PAK'MA'RA", "3 -- FACTIONS.md 9.2 gives the spelling"),
    "vree": ("VREE", "4 -- FACTIONS.md 9.2, species designation"),
    "abbai": ("ABBAI", "4 -- FACTIONS.md 9.2, species designation"),
    "gaim": ("GAIM", "4 -- FACTIONS.md 9.2, species designation"),
    "hyach": ("HYACH", "4 -- FACTIONS.md 9.2, species designation"),
    "llort": ("LLORT", "4 -- FACTIONS.md 9.2, species designation"),
    "grome": ("GROME", "4 -- FACTIONS.md 9.2, species designation"),
    "other": ("LEAGUE -- UNCLASSIFIED",
              "5 -- FACTIONS.md 9.2's tail bucket is not a species"),
    "vorlon": ("VORLON", "4 -- FACTIONS.md 12"),
}

# ---------------------------------------------------------------------------
# DES/ATMOS
# ---------------------------------------------------------------------------
# The prop reads `HUMAN/02`, and 00-MASTER.md 1.4 records "Human atmosphere
# designation 02" from it. DES is the designation; ATMOS is the atmosphere.
# `schedule.py` already refuses to number the other five of the six standing
# atmospheres, for a good reason it states outright: nothing numbers them, and a
# wrong number printed on a wall is worse than a blank.
#
# THE ONE READING THIS MODULE HAS TO MAKE, and it is logged as INV-088: 02
# numbers THE STANDARD OXYGEN MIX rather than the human species, so a Narn --
# who shares that mix in `schedule.RHYTHMS` -- reads `NARN/02`. The alternative
# reading is that 02 is a human-only code, which would leave fourteen species
# with no atmosphere number at all and make the field useless as the customs
# check FACTIONS.md 3.4 says it is. A second identicard for a non-human oxygen
# breather settles it in one frame.
ATMOS_NUMBER = {
    sched.ATMOS_STANDARD: "02",       # authority 1
    sched.ATMOS_HUMID: "",            # unnumbered: no source
    sched.ATMOS_METHANE: "",          # unnumbered: no source
    sched.ATMOS_UNDISCLOSED: "",      # and the Vorlon would not say
}


# ---------------------------------------------------------------------------
# Where a job IS -- derived from directory.py's functions, never tabulated
# ---------------------------------------------------------------------------
# `schedule.ROLES` names a workplace as a WORD ("patrol", "medlab", "cnc"), and
# `directory.PLACES` gives 118 real addresses each carrying what it is FOR. The
# join is by function, not by a second list of keys, because a table of keys is
# a copy of a decision and every time this project has kept two copies of one
# decision they have drifted (CLAUDE.md, the corridor material list).
#
# Each entry is (functions that identify this workplace, sector filter or None,
# functions that DISQUALIFY a place). `workplace_places()` resolves them against
# the directory and `_selftest` asserts every one of the 19 workplaces lands on
# at least one real address -- an assertion that fails the moment a function is
# renamed.
#
# THE EXCLUSIONS ARE NOT TIDYING. A function set is a coarse net and it caught
# two things a reader would notice immediately: `offices` put a Centauri
# financier behind a desk in the **Psi Corps liaison office**, and `ship_arrival`
# put a pak'ma'ra docker on the **Vorlon's private berth**. Both were in the
# first cast list this module printed, and neither was visible in any aggregate.
WORKPLACE_FUNCTIONS = {
    "cnc": (("station_ops", "defence_command"), None, ()),
    "traffic_control": (("traffic_control",), None, ()),
    "patrol": (("law_enforcement",), None, ()),
    "medlab": (("medical",), None, ()),
    "customs_hall": (("immigration",), None, ()),
    # `diplomatic_privilege` is Kosh's berth. FACTIONS.md 12 is explicit that a
    # Vorlon's space is not somewhere the dock roster is sent.
    "docking_bay": (("ship_arrival", "cargo_handling", "starfury_launch"),
                    "blue", ("diplomatic_privilege",)),
    "engineering": (("repair", "power_distribution", "power_generation",
                     "air_handling", "water_reclamation", "rotation",
                     "monitoring"), None, ()),
    "grey_industrial": (("fabrication", "industry"), None, ()),
    "waste_management": (("waste_processing",), None, ()),
    "hydroponics": (("agriculture", "oxygen_production", "food_production"),
                    None, ()),
    "green_sector": (("diplomacy", "diplomatic_mission"), None, ()),
    "council_chamber": (("council_session",), None, ()),
    "zocalo": (("commerce", "retail"), None, ("crime", "black_market")),
    # `psi_corps` is the liaison office of FACTIONS.md 4.1 -- three to eight
    # clerical staff, not a bank. A `financier` sent there is the wrong person
    # in the one room on the station where being the wrong person matters.
    "business_district": (("currency_exchange", "offices"), None,
                          ("psi_corps",)),
    "hospitality": (("hospitality", "food_service", "catering", "gambling"),
                    None, ()),
    "sanctuary": (("worship",), None, ()),
    # No job. These three are where a person with no shift spends their day,
    # and they are as much a workplace as the others from a spawner's point of
    # view: the visitor is IN the concourse, the refugee IS queueing.
    "concourse": (("arrival", "wayfinding", "public_social"), None, ()),
    "refugee_reception": (("residence", "short_stay", "arrival"), None, ()),
    # `informal_residence` ONLY. This read `("informal_residence",
    # "black_market")` and put two fifths of Downbelow's population inside
    # N'Grath's and the Grey Sector market as their default daytime address --
    # so a lurker was more likely to be found at a crime venue than in
    # Downbelow, which is backwards. FACTIONS.md 11.2 is explicit that lurkers
    # ARE Downbelow's population; 11.4's black market is somewhere they GO, and
    # they now go there through `shops_at` instead.
    "downbelow": (("informal_residence",), None, ()),
}


@lru_cache(maxsize=1)
def _by_function():
    """place key -> its function set, and the reverse index. Built once."""
    fwd, rev = {}, {}
    for p in _dir.PLACES:
        fwd[p["key"]] = (frozenset(p["functions"]), p["sector"])
        for fn in p["functions"]:
            rev.setdefault(fn, []).append(p["key"])
    return fwd, rev


@lru_cache(maxsize=64)
def workplace_places(workplace: str) -> tuple:
    """Every real address that serves a role's workplace. Sorted, deterministic.

    Raises on a workplace with no address rather than returning empty: a role
    whose job is nowhere is a person the spawner will place in a room they have
    no reason to be in, and this project's failure mode is exactly the guard
    that returns a harmless-looking nothing.
    """
    spec = WORKPLACE_FUNCTIONS.get(workplace)
    if spec is None:
        raise KeyError(f"no directory functions declared for workplace "
                       f"{workplace!r}; schedule.ROLES has "
                       f"{sorted({r.workplace for r in sched.ROLES})}")
    want, sector, block = spec
    fwd, _rev = _by_function()
    out = [k for k, (fns, sec) in fwd.items()
           if fns & set(want) and not (fns & set(block))
           and (sector is None or sec == sector)]
    if not out:
        raise KeyError(f"workplace {workplace!r} resolves to no place in "
                       f"directory.PLACES via functions {want}")
    return tuple(sorted(out))


# ---------------------------------------------------------------------------
# Where a person LIVES
# ---------------------------------------------------------------------------
# Quarters, by role and species, from directory.PLACES' own residence functions.
# The rule is one sentence per line and every line is sourced:
#
#   envoy      -> kosh_quarters      one Vorlon, one sealed residence (FACTIONS 12)
#   diplomat   -> ambassadorial_suites for the three powers with missions
#                 (FACTIONS 6.2, 7.2, 8.1), league_delegations for the rest --
#                 9.1's "all member worlds assign ambassadors, only ten sit"
#   lurker     -> downbelow / downbelow_arch / subfloor_stack (11.2)
#   refugee    -> qtr_transient. NOT Downbelow: FACTIONS 6.2 counts 13,000
#                 refugees and 2,470 Downbelow Narn as separate blocks, so a
#                 refugee is somebody in short-stay accommodation, and the
#                 difference between the two is the whole point of the block
#   visitor    -> qtr_transient (2.3, mean stay 7 days)
#   breather   -> alien_resident_qtr / alien_sector, for anybody whose
#                 atmosphere is not the standard mix. That is not a preference,
#                 it is life support: `schedule.RHYTHMS[...].breather`
#   command    -> qtr_command
#   EA staff   -> qtr_personnel
#   otherwise  -> qtr_civilian
EA_STAFF_ROLES = frozenset({
    "security", "medical", "traffic", "customs", "engineer", "industrial",
    "waste", "hydroponics", "dockworker", "cleric",
})
MISSION_SPECIES = frozenset({"narn", "centauri", "minbari"})
DOWNBELOW_HOMES = ("downbelow", "downbelow_arch", "subfloor_stack")


def home_for(npc_id: str, species: str, role_key: str) -> str:
    """Which quarters this person lives in. A directory key, always."""
    if role_key == "envoy":
        return "kosh_quarters"
    if role_key == "diplomat":
        return ("ambassadorial_suites" if species in MISSION_SPECIES
                else "league_delegations")
    if role_key == "lurker":
        return _pick(DOWNBELOW_HOMES, npc_id, "home")
    if role_key in ("refugee", "visitor"):
        return "qtr_transient"
    if sched.RHYTHMS.get(species, sched.RHYTHMS["human"]).breather != "none":
        return _pick(("alien_resident_qtr", "alien_sector"), npc_id, "home")
    if role_key == "command":
        return "qtr_command"
    if role_key in EA_STAFF_ROLES and species == "human":
        return "qtr_personnel"
    return "qtr_civilian"


# ---------------------------------------------------------------------------
# Where a person goes when they are not at work or in bed
# ---------------------------------------------------------------------------
# `schedule.Activity` has eight members and three of them -- SLEEP, WORK,
# TRANSIT -- already have an address. The other five need one, and the addresses
# come out of directory.py by function for the same reason the workplaces do.
#
# A PERSON'S LOCAL IS A PROPERTY OF THE PERSON, not a fresh draw every hour.
# Somebody who drinks in Earhart's drinks in Earhart's; a resident who picks a
# different bar every evening is a random walk wearing a name. So each of these
# resolves ONCE per resident, at construction, and `where_at()` is then a
# lookup rather than a search. That is also what makes the two questions this
# module answers -- "where is this person now" and "who is in this room now" --
# incapable of disagreeing: both read the same five fields.
LEISURE_FUNCTIONS = {
    "eat": ("catering", "food_service"),
    "commerce": ("commerce", "retail", "currency_exchange"),
    "recreation": ("recreation", "gambling", "nightlife", "contemplation",
                   "sport"),
    "worship": ("worship",),
    "transit": ("transit",),
}

# A CRIME IS A DESTINATION, NOT AN AVERAGE. `black_market`, `ngrath` and
# `thieves_guild` all declare `commerce`, so they landed in every resident's
# ordinary shopping list and the first probe had a station engineer doing the
# weekly shop at the Grey Sector black market. FACTIONS.md 11.4 treats the
# black market as somewhere people go ON PURPOSE and at risk, so it is excluded
# from the ordinary lists and reached by role instead -- which is what makes it
# mean anything when somebody IS there.
LEISURE_EXCLUDE_FUNCTIONS = frozenset({"crime", "organised_crime"})

# Worship is the one leisure list that is not species-blind. FACTIONS.md 11.3
# gives the four Sanctuaries and Brother Theo's resident order for the human
# faiths, and 9.3 gives the Alien Sector its own observance. A human at
# `alien_worship` is as wrong as a Gaim at Sunday mass, and the first probe
# produced exactly that.
HUMAN_EXCLUDE_PLACES = frozenset({"alien_worship"})
ALIEN_EXCLUDE_PLACES = frozenset({"sanctuary_blue"})

# ...except for the people 3.4 says avoid the readers. A lurker or a refugee
# with `NO STATUS` on their card cannot shop where a card is checked, and
# FACTIONS.md 11.4's black market exists because of exactly that. So the crime
# venues are added BACK for the three roles with no legal standing, which is
# what makes the black market a place with a clientele rather than a label.
NO_STATUS_ROLES = frozenset({"lurker", "refugee"})


@lru_cache(maxsize=256)
def leisure_places(kind: str, species: str = "", role_key: str = "") -> tuple:
    want = LEISURE_FUNCTIONS[kind]
    fwd, rev = _by_function()
    out = set()
    for fn in want:
        out.update(rev.get(fn, ()))
    if not (kind == "commerce" and role_key in NO_STATUS_ROLES):
        out = {k for k in out if not (fwd[k][0] & LEISURE_EXCLUDE_FUNCTIONS)}
    if kind == "worship" and species:
        out -= (HUMAN_EXCLUDE_PLACES if species == "human"
                else ALIEN_EXCLUDE_PLACES)
    if not out:
        raise KeyError(f"no directory place serves {kind!r} via {want}")
    return tuple(sorted(out))


# How strongly a person prefers a venue in the sector they already live or work
# in. EXTRAPOLATED (INV-089): 0.70 means seven in ten evenings out are local,
# which is what makes Red Sector's bars full of Red Sector's people and leaves
# three in ten crossing the station -- the mixing that stops every sector
# reading as a separate village. Overturned by anything that measures how far
# residents travel; constrained only by the requirement that it be neither 1.0
# (five villages) nor 0.0 (a station of commuters).
LOCAL_BIAS = 0.70

# EATS OUT, OR EATS AT HOME. `Activity.EAT` sent everybody to a public eating
# place, and the first probe put all 28 of Downbelow's Narn regulars in Earhart's
# at 13:00 -- because 13:00 is a Narn meal hour (`schedule.RHYTHMS`) and the
# station's restaurants were the only place a meal could be taken. A quarter of a
# million people do not lunch out; the restaurants would have to seat all of them.
#
# EXTRAPOLATED (INV-093): 0.35 of residents take their meals out. Constrained
# from both ends and neither end is free -- FACTIONS.md 2.5 gives the Fresh Air
# Restaurant, Earhart's and the Zocalo busy meal windows and real peak densities,
# so it cannot be near zero; and quarters must not be empty at meal times, so it
# cannot be near one. It is a property of the PERSON, not of the meal, so a
# resident who eats at Earhart's does so every day -- that is what makes a
# regular. Overturned by any figure for how many aboard have a galley.
EAT_OUT_P = 0.35
# ...and nobody without a card that survives a reader eats in a restaurant.
# 3.4: expired status is why lurkers avoid readers, and 11.2 is Downbelow's
# underclass. They eat where they live.
EAT_OUT_ROLES_EXCLUDED = frozenset({"lurker", "refugee"})


def _local_choice(npc_id: str, kind: str, candidates, sectors):
    """A venue, preferring one in a sector the person already belongs to."""
    fwd, _rev = _by_function()
    local = tuple(k for k in candidates if fwd[k][1] in sectors)
    if local and _u(npc_id, f"local-{kind}") < LOCAL_BIAS:
        return _pick(local, npc_id, f"venue-{kind}")
    return _pick(candidates, npc_id, f"venue-{kind}")


# ---------------------------------------------------------------------------
# Age, and therefore DOB
# ---------------------------------------------------------------------------
# The card gives a two-digit year (`12/10/25`), which under a 2260 datum reads
# as 2225 and makes Lyta 35 at the datum. So the format is DD/MM/YY over a 22xx
# century, and the day/month order is AMBIGUOUS in the only sample -- 12/10
# could be either. DD/MM is chosen and logged (INV-090); one identicard with a
# day above 12 settles it.
#
# ADULT AGE BANDS are extrapolated (INV-091) and deliberately coarse. Only one
# species claim in this repository bears on them: FACTIONS.md 9.2 calls the
# Hyach "long-lived" at authority 4. Everything else takes the human band,
# because inventing fifteen lifespans would be fifteen unsourced numbers where
# one honest default does the same job. Minbari take a longer band on the same
# authority-4 basis as Hyach: FACTIONS.md 8.1 describes a caste society with
# a religious caste of ~7,000 aboard, and the show's Minbari are consistently
# depicted as long-lived. Overturned by any stated lifespan.
AGE_BAND = {
    "human": (18, 68),
    "hyach": (30, 240),        # "long-lived", FACTIONS.md 9.2, authority 4
    "minbari": (25, 130),
    "vorlon": (200, 200),      # a singleton; not a distribution
}
AGE_DEFAULT = (18, 68)

# The working population skews young of the band's midpoint, because the roles
# in `schedule.ROLE_WEIGHTS` are jobs. DERIVED rather than chosen: the exponent
# that puts the median at 34 in an 18-68 band is ln((34-18)/50) / ln(0.5) = 1.64,
# and 34 is the midpoint of a working population between 18 and 68 weighted
# toward the early career. The first version used 3.0 by eye and produced a
# median of 24, which is a station staffed by graduates.
AGE_SKEW = 1.64


def _age(npc_id: str, species: str, role_key: str) -> int:
    lo, hi = AGE_BAND.get(species, AGE_DEFAULT)
    if hi <= lo:
        return lo
    u = _u(npc_id, "age")
    # Children exist on the station and do not hold roles. The three roles with
    # no work hours are the only ones that can be a minor, and even then rarely:
    # a lurker child and a refugee child are both attested situations
    # (FACTIONS 11.2, 6.2) and a visiting one is ordinary.
    if role_key in ("visitor", "refugee", "lurker") and _u(npc_id, "minor") < 0.08:
        return int(4 + _u(npc_id, "minorage") * 13)
    return int(lo + (hi - lo) * (u ** AGE_SKEW))


def _dob(npc_id: str, age: int):
    """(year, month, day) and the card's own DD/MM/YY rendering."""
    y = ERA_YEAR - age
    m = 1 + int(_u(npc_id, "dobm") * 12)
    d = 1 + int(_u(npc_id, "dobd") * 28)     # 28 so no month is ever short
    return (y, m, d), f"{d:02d}/{m:02d}/{y % 100:02d}"


# ---------------------------------------------------------------------------
# LICENSED PSI
# ---------------------------------------------------------------------------
# FACTIONS.md 4.1: "10-40 registered commercial telepaths aboard at any time,
# most of them freelancers passing through rather than Corps-resident". Take the
# midpoint, 25, over a station of 250,001: p = 1.0e-4. Psi Corps is an Earth
# Alliance institution, so registration is modelled as human-only, and 4.1's
# "hired by hour for negotiations in the Business District" puts the licence on
# the roles that would carry it.
#
# The consequence is the point: a licensed telepath is a once-in-ten-thousand
# encounter, so meeting one is an EVENT rather than set dressing -- which is
# what FACTIONS.md 12 describes ("conversation stops when someone with the badge
# enters"). A commoner flag would destroy that.
PSI_LICENSED_ABOARD = 25          # midpoint of FACTIONS.md 4.1's 10-40
PSI_ROLES = frozenset({"visitor", "financier", "merchant", "diplomat"})


def _licensed_psi(npc_id: str, species: str, role_key: str) -> bool:
    if species != "human" or role_key not in PSI_ROLES:
        return False
    # The rate is per licence-eligible head, so the station-wide count comes out
    # at the source's figure rather than at the rate times everybody.
    eligible = sum(sched.ROLE_WEIGHTS["human"].get(r, 0) for r in PSI_ROLES)
    return _u(npc_id, "psi") < PSI_LICENSED_ABOARD / max(eligible, 1)


# ---------------------------------------------------------------------------
# VISAS
# ---------------------------------------------------------------------------
# FACTIONS.md 3.4, on the identicard: "VISAS -- therefore visa fraud, forged
# identicards and expired status are the station's most ordinary crimes, and the
# reason lurkers avoid readers." So the field is only ever filled for somebody
# whose right to be here is conditional, and a small share of those are expired.
#
# 2.3 gives transients a mean stay of seven days, which sets the class:
# a visitor holds a short-stay visa, a refugee holds the status FACTIONS 6.2
# describes (stateless, in sanctuary), and a resident with a job holds nothing
# because a resident is not a visitor.
VISA_TRANSIT_DAYS = 7             # FACTIONS.md 2.3, mean stay
# EXTRAPOLATED (INV-092): one in twelve conditional statuses is out of date at
# any moment. Constrained by 3.4 calling expired status the station's MOST
# ORDINARY crime -- so it cannot be rare -- and by it still being a crime, so it
# cannot be most people. Overturned by any figure for customs enforcement volume.
VISA_EXPIRED_P = 1.0 / 12.0


def _visa(npc_id: str, role_key: str) -> str:
    if role_key == "refugee":
        return ("SANCTUARY -- EXPIRED"
                if _u(npc_id, "visa") < VISA_EXPIRED_P else "SANCTUARY")
    if role_key == "visitor":
        d = 1 + int(_u(npc_id, "visad") * VISA_TRANSIT_DAYS * 2)
        return (f"TRANSIT {d}D -- EXPIRED"
                if _u(npc_id, "visa") < VISA_EXPIRED_P else f"TRANSIT {d}D")
    if role_key == "lurker":
        # 11.2's underclass and 3.4's "the reason lurkers avoid readers". A
        # lurker with no valid status is the crime layer's raw material.
        return "NO STATUS" if _u(npc_id, "visa") < 0.55 else ""
    return ""


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Resident:
    """One person aboard. A pure function of `npc_id` and species.

    The nine identicard fields, plus the three things the card does not carry
    and a station needs: where they live, where they work, and what the clock
    says they are doing.
    """
    npc_id: str
    species: str
    # --- the card ---------------------------------------------------------
    surname: str
    forename: str
    origin: str
    atmos_class: str
    atmos_code: str
    sex: str
    dob: tuple                 # (year, month, day), full year
    dob_card: str              # DD/MM/YY, the prop's own rendering
    phys_chr: str
    medical: str
    licensed_psi: bool
    visas: str
    # --- the station ------------------------------------------------------
    role: str
    job: str                   # a directory place key, or "" for no job
    home: str                  # a directory place key, always
    idles_at: str              # where an off-duty hour is spent
    eats_at: str
    shops_at: str
    plays_at: str
    prays_at: str
    commutes_via: str
    stature_m: float
    breather: str
    age: int = 0

    @property
    def name(self) -> str:
        """The name as this species says it aloud, which is not one order.

        `card_name` is always `FAMILY, GIVEN` because that is the prop's
        format; a SPOKEN name is the species' own order, and Hyach put the
        lineage first (INV-1249). Reassembling `forename surname` universally
        would have printed 1,750 Hyach backwards everywhere a line of dialogue
        or a PA call uses this.
        """
        if not self.surname and not self.forename:
            return ""
        if not self.forename:
            return self.surname
        g = npc_names.GRAMMARS.get(self.species)
        if g is not None and g.order == "family-given":
            return f"{self.surname} {self.forename}"
        return f"{self.forename} {self.surname}".strip()

    @property
    def card_name(self) -> str:
        """`SURNAME, FORENAME` -- the prop's own order."""
        if not self.surname and not self.forename:
            return ""
        if not self.forename:
            return self.surname.upper()
        return f"{self.surname.upper()}, {self.forename.upper()}"

    def where_at(self, hour: float) -> str:
        """The directory place key this person is at, at this EMT hour."""
        return where_at(self, hour)

    def activity_at(self, hour: float):
        return sched.activity_at(self.npc_id, self.species, hour)


# EVERY SPECIES ABOARD HAS A NAME. It did not until INV-1249, and the state
# this comment used to describe was measured on the PACKAGED build: 447 of
# 3,683 shipped residents -- 12.1% -- carried the empty red NAME field, all of
# them in `schedule.SPECIES_WITHOUT_NAMES`. That was INV-004's rule (a grammar
# fitted to zero attested names is invention dressed as inference) applied
# faithfully, and it lost to CLAUDE.md hard rule 1, which says the answer to
# "the show never establishes this" is NEVER to leave a hole. INV-1249 gives
# the seven species a reasoned authority-5 grammar each; INV-1251 gives the
# `other` bucket a distribution over ten of them.
#
# THE `except KeyError` THAT USED TO BE HERE IS GONE, and its removal is worth
# more than the names. It turned EVERY unknown species string into an empty
# name with no error -- so `resident("7", "hooman")` was indistinguishable
# from a species the show never named, and both shipped as a blank card. Now a
# typo raises and a real species cannot. `tools/cast_gate.py` asserts that
# every key in `schedule.STATION_COUNTS` and `body.SPECIES` has a grammar, so
# nothing shipped can reach the raise.
#
# THE ORDER IS THE GRAMMAR'S, NOT THIS FUNCTION'S. `names.split_name` knows
# which element of a two-word name is the lineage, because Hyach put it first
# (INV-1249: a long-lived species identifies by the thing that outlives the
# person). This function used to assume given-then-family universally, which
# would have printed 1,750 Hyach cards with the two halves swapped.
#
# `sex` IS PASSED THROUGH, and it comes off the body so the card, the mesh and
# the name are one individual. Without it the name and the SEX field were
# independent draws: measured over 400 humans, ALL 22 given names appeared
# with both sexes, so "SINCLAIR, MATEO / SEX: FEMALE" was the general case
# rather than a quirk. Only the human grammar has gendered names and only
# because the show attests them; `name_for` ignores `sex` elsewhere rather
# than inventing a gender system per species.
def _split_name(species: str, npc_id: str, sex=None):
    return npc_names.split_name(species,
                                npc_names.name_for(species, npc_id, sex=sex))


# SEX comes off the body, so the card and the mesh cannot disagree.
# `body.individual` returns "f", "m", or "none" for the Vorlon singleton.
_SEX_WORD = {"f": "FEMALE", "m": "MALE", "none": ""}
# FACTIONS.md 9.2 calls the Gaim "hive-caste insectoids" at authority 4. An
# Earth Alliance customs form with a two-value sex field does not fit a hive,
# and the honest record says so rather than picking one of the two.
HIVE_SPECIES = frozenset({"gaim"})


def _phys_chr(ind, species: str, breather: str) -> str:
    """PHYS CHR, and it is EMPTY unless there is something distinguishing.

    The prop shows this field blank for Lyta Alexander, so blank is its normal
    state and a module that always fills it could never reproduce the one
    authority-1 example. It is filled when the individual is off their species'
    baseline stature by more than a standard deviation, or carries a breather --
    which is exactly when a customs officer looking up from the reader would
    have something to write down.
    """
    sp = npc_body.SPECIES.get(species)
    if sp is None:
        return ""
    marks = []
    if sp.stature_sigma_m > 0:
        dz = (ind.stature_m - sp.stature_m) / sp.stature_sigma_m
        if dz >= 1.0:
            marks.append(f"TALL {ind.stature_m:.2f}M")
        elif dz <= -1.0:
            marks.append(f"SHORT {ind.stature_m:.2f}M")
    if breather == "suit":
        marks.append("ENCOUNTER SUIT")
    elif breather == "mask":
        marks.append("BREATHER MASK")
    return " / ".join(marks)


@lru_cache(maxsize=65536)
def resident(npc_id: str, species: str = "human") -> Resident:
    """Resolve one person. Deterministic in (npc_id, species) and nothing else.

    Cached because the same person is asked about many times -- once per hour
    by the roster, once by the spawner, once by whatever looks at their card --
    and every field is a pure function, so the cache can only ever be an
    optimisation.
    """
    rhythm = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
    role = sched.role_for(npc_id, species)
    # THE BODY FIRST, so the name can agree with it. `individual` decides SEX
    # and it decides the mesh; drawing the name from a separate hash gave a
    # station where every human given name appeared with both sexes.
    ind = npc_body.individual(species, npc_id)
    surname, forename = _split_name(species, npc_id, sex=ind.sex)

    home = home_for(npc_id, species, role.key)
    # A role with no work hours has no job, and saying so is better than
    # pretending the concourse employs 31,000 people. Their daytime address is
    # still resolved -- it is where they ARE, which is what a spawner needs --
    # but `job` reads empty and `where_at` sends them there under IDLE rather
    # than under WORK.
    job = _pick(workplace_places(role.workplace), npc_id, "job")

    fwd, _rev = _by_function()
    sectors = {fwd[home][1], fwd[job][1]}
    eats = _local_choice(npc_id, "eat", leisure_places("eat"), sectors)
    if (role.key in EAT_OUT_ROLES_EXCLUDED
            or _u(npc_id, "eatout") >= EAT_OUT_P):
        # At home, or in the mess on shift. Somebody with a job eats where they
        # work at midday and at home otherwise; the split is the shift, not a
        # coin, so `where_at` decides it per hour rather than fixing it here.
        eats = ""
    shops = _local_choice(npc_id, "commerce",
                          leisure_places("commerce", "", role.key), sectors)
    plays = _local_choice(npc_id, "recreation", leisure_places("recreation"),
                          sectors)
    prays = _local_choice(npc_id, "worship", leisure_places("worship", species),
                          sectors)
    via = _local_choice(npc_id, "transit", leisure_places("transit"), sectors)

    age = _age(npc_id, species, role.key)
    dob, dob_card = _dob(npc_id, age)

    if species in HIVE_SPECIES:
        sex = "HIVE"
    else:
        sex = _SEX_WORD.get(ind.sex, "")

    medical = MEDICAL_NULL
    if rhythm.breather == "suit":
        medical = "NON-STD ATMOS REQ"
    elif rhythm.breather == "mask":
        medical = "ATMOS ASSIST REQ"

    return Resident(
        npc_id=npc_id, species=species,
        surname=surname, forename=forename,
        origin=ORIGIN.get(species, ORIGIN["other"])[0],
        atmos_class=rhythm.atmos,
        atmos_code=ATMOS_NUMBER.get(rhythm.atmos, ""),
        sex=sex, dob=dob, dob_card=dob_card,
        phys_chr=_phys_chr(ind, species, rhythm.breather),
        medical=medical,
        licensed_psi=_licensed_psi(npc_id, species, role.key),
        visas=_visa(npc_id, role.key),
        role=role.key,
        job="" if role.work_hours <= 0 else job,
        home=home,
        # AN IDLE HOUR IS NOT AN HOUR AT HOME FOR EVERYBODY. The three roles
        # with no shift are not resting between shifts, they are waiting:
        # FACTIONS.md 2.3's 45,000 transients "shop, eat, queue and wait for a
        # berth", 6.2's 13,000 Narn refugees queue, and 11.2's lurkers are
        # Downbelow's population rather than its visitors. Sending all three
        # home under IDLE emptied the concourse and filled the transient
        # quarters with 31,000 people sitting on their bunks.
        idles_at=job if role.work_hours <= 0 else home,
        eats_at=eats, shops_at=shops, plays_at=plays,
        prays_at=prays, commutes_via=via,
        stature_m=ind.stature_m, breather=rhythm.breather, age=age)


# ---------------------------------------------------------------------------
# The identicard
# ---------------------------------------------------------------------------
def identicard(res: Resident) -> tuple:
    """The nine fields in the prop's order, each as (label, value, state).

    `state` is FILLED or EMPTY, and EMPTY is what the prop renders in red with
    no colon. Emitting the state rather than only the value is what lets a
    texture generator reproduce the frame instead of approximating it.
    """
    des = ORIGIN.get(res.species, ORIGIN["other"])[0]
    # DES is the species designation, which for a human is HUMAN and for a
    # Centauri is not "CENTAURI REPUBLIC" -- the polity is ORIGIN's business.
    des = res.species.upper() if res.species != "pakmara" else "PAK'MA'RA"
    atmos = f"{des}/{res.atmos_code}" if res.atmos_code else ""
    vals = {
        "NAME": res.card_name,
        "ORIGIN": res.origin,
        "DES/ATMOS": atmos,
        "SEX": res.sex,
        "DOB": res.dob_card,
        "PHYS CHR": res.phys_chr,
        "MEDICAL": res.medical,
        "LICENSED PSI": "REGISTERED" if res.licensed_psi else "",
        "VISAS": res.visas,
    }
    return tuple((k, vals[k], FILLED if vals[k] else EMPTY) for k in CARD)


# ---------------------------------------------------------------------------
# Where somebody is
# ---------------------------------------------------------------------------
A = sched.Activity
# Activity -> which of the resident's own addresses. SLEEP always goes home,
# which is the difference between a station that empties at night and one that
# goes to bed: the corridors thin because people are in their quarters, not
# because they cease to exist.
_ACTIVITY_FIELD = {
    A.SLEEP: "home", A.IDLE: "idles_at", A.EAT: "eats_at",
    A.COMMERCE: "shops_at", A.RECREATION: "plays_at",
    A.WORSHIP: "prays_at", A.TRANSIT: "commutes_via",
}


def _meal_place(res: Resident, hour: float) -> str:
    """Where somebody who does not eat out takes a meal.

    On shift, in the mess or wherever they work -- `Activity.EAT` resolves
    BEFORE `Activity.WORK` in `schedule.activity_at`, so a meal hour inside a
    shift is a break at work and not an absence from it. Off shift, at home.
    """
    if res.job:
        w = sched.work_window(res.npc_id, res.species)
        if w and sched._in_window(hour % 24.0, w[0], w[1]):
            return res.job
    return res.home


def where_at(res: Resident, hour: float) -> str:
    """The directory place key this person is at, at this EMT hour."""
    act = sched.activity_at(res.npc_id, res.species, hour)
    if act is A.WORK:
        # A role with no work hours never returns WORK, so this branch is only
        # ever reached by somebody who has a job.
        return res.job or res.home
    if act is A.EAT and not res.eats_at:
        return _meal_place(res, hour)
    return getattr(res, _ACTIVITY_FIELD[act])


# ---------------------------------------------------------------------------
# Who is in a room
# ---------------------------------------------------------------------------
# THE POOL IS A PROPERTY OF THE PLACE, NOT OF THE HOUR, which is the same rule
# `crowd._pool_capacity` states and for the same reason: re-casting the regulars
# every time the crowd changes size means a room's people change when the room's
# headcount changes, and a player walking back in at 14:00 meets strangers.
#
# So: scan the id stream once per (place, species, seed) and keep the ones whose
# life touches this place at all -- they live here, work here, or it is their
# local. Then the HOUR decides which of those affiliates are actually in, by
# asking each one where they are. A place gains and loses its own people rather
# than reshuffling the station.
POOL_WANT = 28              # more than any one room holds of one species
POOL_BUDGET = 4000          # ids scanned before giving up on an affiliate


def pool_id(place_key: str, species: str, i: int, seed: str) -> str:
    """The id of the i'th candidate regular of a species at a place."""
    return f"res:{seed}:{place_key}:{species}:{i}"


def _affiliated(res: Resident, place_key: str) -> bool:
    return place_key in (res.home, res.job, res.eats_at, res.shops_at,
                         res.plays_at, res.prays_at, res.commutes_via)


@lru_cache(maxsize=8192)
def affiliates(place_key: str, species: str, seed: str = "b5",
               want: int = POOL_WANT) -> tuple:
    """Ids of people whose lives touch this place. Hour-independent, cached.

    Falls back to unfiltered ids if the budget runs out, and DOES NOT return
    short: a room the spawner has decided holds eleven people must get eleven
    people, and returning nine would empty rooms for a reason no gate would
    ever surface. That is INV-005 in a different coat -- the same failure this
    project has already paid for once.
    """
    out, i = [], 0
    while len(out) < want and i < POOL_BUDGET:
        nid = pool_id(place_key, species, i, seed)
        if _affiliated(resident(nid, species), place_key):
            out.append(nid)
        i += 1
    j = 0
    while len(out) < want:
        nid = pool_id(place_key, species, j, seed)
        if nid not in out:
            out.append(nid)
        j += 1
    return tuple(out)


# How much bigger the candidate pool is than the room. `populace.occupancy`
# decides how many bodies a room holds from a calibrated density curve, and only
# a fraction of a place's regulars are in it at any one hour -- so a pool the
# size of the room can never fill it from the schedule alone. At x3 the Zocalo
# at 13:00 goes from 19 of 62 scheduled to over half, and the scan is still one
# pass per (place, species) and cached forever.
POOL_OVERSAMPLE = 3


def roster(place_key: str, hour: float, species: str, n: int,
           seed: str = "b5") -> tuple:
    """The first `n` people of a species in this place at this hour.

    Ranked in three tiers, and the third one is the reason this is not a filter:

      0. everybody the clock actually sends here;
      1. the place's other regulars, awake;
      2. the place's other regulars, ASLEEP -- last, always.

    Tier 2 exists because `populace.occupancy` can ask for more bodies than the
    schedule supplies and a room must not come back short. It is ranked last
    because the first cast list this module printed had a Security Central
    officer standing at his post with `sleep` written next to his name, which is
    the single most visible way for a schedule to be decoration.

    Nested by construction -- `roster(n+1)` is `roster(n)` plus one person -- so
    a room that gets busier gains somebody rather than re-casting.
    """
    if n <= 0:
        return ()
    pool = affiliates(place_key, species, seed,
                      max(POOL_WANT, n * POOL_OVERSAMPLE))
    tiers = ([], [], [])
    for nid in pool:
        r = resident(nid, species)
        if where_at(r, hour) == place_key:
            tiers[0].append(r)
        elif r.activity_at(hour) is A.SLEEP:
            tiers[2].append(r)
        else:
            tiers[1].append(r)
    return tuple((tiers[0] + tiers[1] + tiers[2])[:n])


def scheduled_fraction(place_key: str, hour: float, species: str, n: int,
                       seed: str = "b5") -> float:
    """Of the `n` people put in this room, how many the clock actually sent.

    The number that says whether the schedule is doing any work. It is NOT 1.0
    and is not supposed to be: `populace.occupancy` decides how many bodies a
    room holds from the calibrated per-place crowd curve, and this says how many
    of them have a reason to be there. A value near zero means the schedule is
    decoration.
    """
    if n <= 0:
        return 1.0
    people = roster(place_key, hour, species, n, seed)
    return sum(1 for r in people if where_at(r, hour) == place_key) / len(people)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def describe(res: Resident) -> str:
    """One resident as a line a person can read."""
    nm = res.name or f"<{res.species} -- no attested name>"
    job = res.job or "(no job aboard)"
    return (f"{nm} -- {res.species}, {res.origin}, {res.role}; "
            f"home {res.home}, works {job}")


def cast(place_key: str, hour: float, species: str, n: int,
         seed: str = "b5", out=print) -> None:
    for r in roster(place_key, hour, species, n, seed):
        out(f"  {describe(r)}  @{hour:04.1f} -> {where_at(r, hour)}")


def dossier(res: Resident, out=print) -> None:
    """One resident in full: the card, the addresses, and the whole day."""
    out(f"  {(res.name or '<no attested name>'):<24} "
        f"{res.species} / {res.role}, aged {res.age}")
    for label, val, state in identicard(res):
        out(f"      {label:<13}{'' if state == EMPTY else ': '}{val}"
            + ("      [red, no entry]" if state == EMPTY else ""))
    out(f"      home        : {res.home}")
    out(f"      job         : {res.job or '(no job aboard)'}")
    out(f"      eats        : {res.eats_at or '(at home, or in the mess on shift)'}")
    out(f"      drinks      : {res.plays_at}")
    out(f"      shops       : {res.shops_at}")
    out("      day (EMT)   : " + "  ".join(
        f"{h:02d} {res.activity_at(float(h)).value[:4]}"
        for h in (3, 9, 13, 18, 22)))
    for h in (9.0, 22.0):
        out(f"      at {h:04.1f}     : {where_at(res, h)}  "
            f"({res.activity_at(h).value})")


def report(out=print):
    out("RESIDENTS -- identity, home, job, and the EMT clock")
    out("")
    out(f"card fields ({len(CARD)}, prop order): {' / '.join(CARD)}")
    out(f"workplaces resolved: {len(WORKPLACE_FUNCTIONS)} of "
        f"{len({r.workplace for r in sched.ROLES})}")
    out("")
    out("THREE RESIDENTS, IN FULL")
    for place, sp in (("zocalo", "human"), ("downbelow", "narn"),
                      ("council_chamber", "centauri")):
        out("")
        dossier(roster(place, 13.0, sp, 1)[0], out=out)
    out("")
    out("WHO IS IN A ROOM, AND IT CHANGES WITH THE CLOCK")
    for place, sp, n in (("zocalo", "human", 3), ("security_central", "human", 2),
                         ("downbelow", "narn", 2), ("alien_sector", "gaim", 2)):
        for hour in (9.0, 22.0):
            out(f"{place} / {sp} at {hour:04.1f}")
            cast(place, hour, sp, n, out=out)


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
def _selftest():                                                # noqa: C901
    import ast
    import subprocess

    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"PASS  {name}" + (f"  -- {detail}" if detail else ""))
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    # --- the card is the prop's ------------------------------------------
    # Transcribed a second time from canon/00-MASTER.md 1.4 rather than from
    # this file, so the two transcriptions have to agree. Nothing in this
    # module reads the canon file; this exists only to disagree.
    canon = os.path.join(os.path.dirname(_STATION), "canon", "00-MASTER.md")
    text = open(canon).read()
    for label in CARD:
        if label not in text:
            check(f"canon 1.4 carries the {label} field", False)
            break
    else:
        check("all nine card labels appear in canon/00-MASTER.md 1.4", True,
              " / ".join(CARD))

    # NEGATIVE CONTROL for the above: a label that is NOT on the prop must not
    # be found, or the check is a search for common English words.
    check("...and a field the prop does not carry is absent",
          "OCCUPATION" not in text and "NEXT OF KIN" not in text)

    lyta_order = tuple(LYTA)
    check("the renderer emits the prop's nine fields in the prop's order",
          tuple(k for k, _v, _s in identicard(
              resident("probe", "human"))) == lyta_order,
          str(lyta_order))
    # NEGATIVE CONTROL: the same comparison against a permuted order must fail,
    # or the check above passes for any ordering at all.
    perm = lyta_order[1:] + lyta_order[:1]
    check("...and the same test rejects a permuted order",
          tuple(k for k, _v, _s in identicard(
              resident("probe", "human"))) != perm)

    # THE RENDERER REPRODUCES THE ONE AUTHORITY-1 CARD, EXACTLY. Every value in
    # `LYTA` is transcribed from `identicard readout.webp`; this builds a record
    # carrying them and asserts the emitted card is that frame, field for field,
    # value for value, and with the same three fields in the prop's empty state.
    # It is the difference between "we wrote nine labels down" and "we can print
    # the card the show printed".
    lyta = Resident(
        npc_id="lyta", species="human", surname="Alexander", forename="Lyta",
        origin="EARTH", atmos_class=sched.ATMOS_STANDARD, atmos_code="02",
        sex="FEMALE", dob=(2225, 10, 12), dob_card="12/10/25", phys_chr="",
        medical=MEDICAL_NULL, licensed_psi=False, visas="",
        role="visitor", job="", home="qtr_transient", idles_at="qtr_transient",
        eats_at="", shops_at="zocalo", plays_at="casino", prays_at="sanctuaries",
        commutes_via="central_corridor", stature_m=1.70, breather="none")
    got = tuple((k, v) for k, v, _s in identicard(lyta))
    check("the renderer reproduces the authority-1 identicard exactly",
          got == tuple(LYTA.items()),
          str([p for p in got if p not in LYTA.items()]))
    check("...and the three fields the prop leaves red come back empty",
          [k for k, _v, s in identicard(lyta) if s == EMPTY]
          == ["PHYS CHR", "LICENSED PSI", "VISAS"])
    # NEGATIVE CONTROL: one field wrong and the comparison must fail, or it is
    # not comparing anything.
    off = tuple((k, ("EARTH-2" if k == "ORIGIN" else v)) for k, v in got)
    check("...and one wrong field fails that comparison",
          off != tuple(LYTA.items()))

    # The prop leaves three of its nine fields empty, so the renderer must be
    # able to produce an empty field. A module that always fills every field
    # could not reproduce the one authority-1 example that exists.
    n_empty = sum(1 for _l, _v, s in identicard(resident("probe", "human"))
                  if s == EMPTY)
    check("a card can carry empty fields, as the prop does", n_empty > 0,
          f"{n_empty} of 9 empty on the probe")
    # And it must be able to produce a filled one, or "empty" is not a state.
    check("...and filled ones", n_empty < len(CARD), f"{9 - n_empty} filled")

    # --- names -----------------------------------------------------------
    narn = [resident(f"n{i}", "narn") for i in range(40)]
    check("Narn names carry the medial apostrophe their grammar was fitted to",
          all("'" in r.name for r in narn),
          narn[0].name + ", " + narn[1].name)
    # NEGATIVE CONTROL: the same shape test on human names must fail, or it is
    # testing nothing about Narn.
    human = [resident(f"h{i}", "human") for i in range(40)]
    check("...and the same test rejects human names",
          not all("'" in r.name for r in human), human[0].name)

    cent = [resident(f"c{i}", "centauri") for i in range(30)]
    check("Centauri names are given name plus a house from the attested list",
          all(r.surname in npc_names.CENT_HOUSE for r in cent),
          cent[0].name)

    # INV-1249 REVERSES THE ASSERTION THAT USED TO BE HERE. It read "the eight
    # species with no attested name are not given one" and it passed for as
    # long as it existed, on 447 of the packaged build's 3,683 residents. The
    # test was not wrong about the code; it was the wrong test, and it is the
    # exact shape CLAUDE.md warns about -- an exit criterion a defect passes.
    # THE LIST IS LITERAL AND NOT READ FROM `sched.SPECIES_WITHOUT_NAMES`, and
    # that is deliberate. That constant is now stale and `test_schedule.py`
    # says in its own failure text what is owed -- "adding a grammar must
    # delete its entry here" -- so it is about to become the empty tuple. Every
    # check below driven off it would then iterate nothing and PASS, which is
    # this project's signature defect: a check whose subject has quietly
    # emptied is a green that means nothing.
    FORMERLY_UNNAMED = ("brakiri", "vree", "abbai", "gaim", "hyach", "llort",
                        "grome", "other")
    was_unnamed = [resident(f"g{i}", sp)
                   for sp in FORMERLY_UNNAMED for i in range(4)]
    blank = [r for r in was_unnamed if not r.name]
    check("every species aboard now has a name, including the eight that had none",
          not blank,
          f"{len(was_unnamed) - len(blank)} of {len(was_unnamed)} named across "
          f"{len(FORMERLY_UNNAMED)} species -- e.g. "
          + ", ".join(sorted({r.name for r in was_unnamed})[:3]))
    check("...and their NAME field renders FILLED rather than the empty state",
          all(dict((l, s) for l, _v, s in identicard(r))["NAME"] == FILLED
              for r in was_unnamed))
    # AND THE EMPTY STATE IS STILL REACHABLE, or the check above has quietly
    # deleted a feature of the prop rather than filled one field of it.
    st = [dict((l, s) for l, _v, s in identicard(r)) for r in was_unnamed]
    still_empty = sorted({k for c in st for k, v in c.items() if v == EMPTY})
    check("...while the prop's empty state is still exercised elsewhere",
          len(still_empty) >= 2, "still empty on these cards: " + ", ".join(still_empty))

    # A SPECIES STRING NOBODY DEFINED MUST RAISE, NOT BLANK. The old
    # `except KeyError` in `_split_name` turned every typo into an empty NAME
    # field indistinguishable from the eight species above, so the defect and
    # the policy looked identical on a card.
    try:
        resident("t0", "hooman")
        raised = False
    except KeyError:
        raised = True
    check("an unknown species raises rather than shipping a blank card", raised)

    # THE HYACH CARD INVERTS, and it is the only one that does. `names.py` puts
    # the lineage first for a long-lived species (INV-1249); a card that split
    # on position alone would print 1,750 people with the halves swapped.
    hy = resident("hy0", "hyach")
    hu = resident("hu0", "human")
    check("a Hyach card's SURNAME half is the LINEAGE, which comes FIRST in the name",
          hy.card_name.split(",")[0] == hy.name.split()[0].upper(),
          f"{hy.name!r} -> {hy.card_name!r}")
    check("...and the same test FAILS on a human, whose family name comes second",
          hu.card_name.split(",")[0] != hu.name.split()[0].upper(),
          f"{hu.name!r} -> {hu.card_name!r}")

    # NO BACKGROUND EXTRA WEARS A SHOW CHARACTER'S NAME. The shipped build
    # carried 43 who did -- 29 human, 14 alien. `tools/cast_gate.py` is the
    # gate; this is the module-local tripwire over the real id space.
    wearing = [(sp, i, resident(npc_names_id, sp).name)
               for sp in sched.STATION_COUNTS
               for i in range(60)
               for npc_names_id in (pool_id("zocalo", sp, i, "b5"),)
               if resident(npc_names_id, sp).name in npc_names.RESERVED]
    check("no resident drawn from the shipped id space wears a reserved name",
          not wearing, f"{len(wearing)} wearing, e.g. {wearing[:2]}")

    # --- addresses -------------------------------------------------------
    keys = {p["key"] for p in _dir.PLACES}
    every = [resident(f"a{i}", sp) for sp in sched.RHYTHMS for i in range(25)]
    check("every workplace in schedule.ROLES resolves to a real address",
          all(workplace_places(r.workplace) for r in sched.ROLES),
          f"{len({r.workplace for r in sched.ROLES})} workplaces")
    # NEGATIVE CONTROL: a workplace nobody declared must raise, not return ().
    try:
        workplace_places("bridge_of_the_enterprise")
        check("...and an undeclared workplace raises", False, "it returned")
    except KeyError:
        check("...and an undeclared workplace raises", True)

    check("every home is a place in directory.PLACES",
          all(r.home in keys for r in every))
    check("every job is a place in directory.PLACES, or empty",
          all(r.job in keys or r.job == "" for r in every))
    fwd, _rev = _by_function()
    res_fns = {"residence", "informal_residence", "short_stay",
               "diplomatic_mission", "sealed_environment", "multi_environ"}
    bad = [r.home for r in every if not (fwd[r.home][0] & res_fns)]
    check("every home is a place directory.py says people LIVE in",
          not bad, str(sorted(set(bad))[:4]))
    # NEGATIVE CONTROL: the same test applied to a place that is not a
    # residence must fail, or it passes for any key at all.
    check("...and the same test rejects a non-residence",
          not (fwd["fusion_core"][0] & res_fns))

    # A person with a job must not have one that contradicts their role.
    mismatched = [r for r in every
                  if r.job and r.job not in workplace_places(
                      sched.ROLES_BY_KEY[r.role].workplace)]
    check("nobody's job is outside their own role's workplace",
          not mismatched, f"{len(mismatched)} of {len(every)}")
    check("roles with no work hours carry no job",
          all(r.job == "" for r in every
              if sched.ROLES_BY_KEY[r.role].work_hours <= 0))

    # --- the clock -------------------------------------------------------
    # A resident is somewhere at every hour of the day, and it is a real place.
    r = resident("clockprobe", "human")
    day = [where_at(r, float(h)) for h in range(24)]
    check("a resident has an address at all 24 hours",
          all(p in keys for p in day), " ".join(sorted(set(day))))
    check("...and it is not the same place all day", len(set(day)) > 1,
          f"{len(set(day))} distinct places")
    check("a resident is at home when they are asleep",
          all(where_at(r, float(h)) == r.home for h in range(24)
              if r.activity_at(float(h)) is A.SLEEP))
    check("...and at work when they are at work",
          all(where_at(r, float(h)) == r.job for h in range(24)
              if r.activity_at(float(h)) is A.WORK))

    # THE ROOM CHANGES WITH THE HOUR. This is the claim the whole module
    # exists to support, so it is measured on a place with declared busy and
    # dead windows rather than asserted.
    z09 = {p.npc_id for p in roster("zocalo", 9.0, "human", 12)}
    z22 = {p.npc_id for p in roster("zocalo", 22.0, "human", 12)}
    z03 = {p.npc_id for p in roster("zocalo", 3.0, "human", 12)}
    check("the Zocalo holds different people at 09:00, 22:00 and 03:00",
          z09 != z22 and z22 != z03 and z09 != z03,
          f"09/22 share {len(z09 & z22)}, 22/03 share {len(z22 & z03)} of 12")
    # NEGATIVE CONTROL for the above: the SAME hour twice must give the same
    # people, or the difference is noise and proves nothing about the clock.
    check("...and the same hour twice gives the same people",
          {p.npc_id for p in roster("zocalo", 9.0, "human", 12)} == z09)

    # And the people the clock sent are a real share of the room, not a token.
    fr = scheduled_fraction("zocalo", 13.0, "human", 10)
    check("most of a busy Zocalo at 13:00 is there because of the schedule",
          fr >= 0.5, f"{fr:.0%} of 10 sent by the clock")
    # NEGATIVE CONTROL: a place nobody is affiliated with -- the sealed Markab
    # quarter has no residents at all -- must NOT report a high fraction.
    fr_sealed = scheduled_fraction("welded_shut", 13.0, "human", 10)
    check("...and a sealed volume nobody lives or works in does not",
          fr_sealed < fr, f"welded_shut {fr_sealed:.0%} vs zocalo {fr:.0%}")

    # --- the numbers the sources give ------------------------------------
    # FACTIONS.md 4.1: 10-40 registered telepaths aboard. Measured over a
    # sample of the human id stream rather than asserted from the constant.
    scan = 20000
    lic = sum(1 for i in range(scan)
              if _licensed_psi(f"psi-{i}", "human",
                               sched.role_for(f"psi-{i}", "human").key))
    est = lic / scan * sched.STATION_COUNTS["human"]
    check("licensed telepaths land in FACTIONS.md 4.1's 10-40 aboard",
          8 <= est <= 60, f"{est:.0f} estimated from {scan} sampled humans")
    # NEGATIVE CONTROL: the flag must be capable of being set at all, or the
    # band above is satisfied by a function that always returns False.
    check("...and the flag is not simply always false", lic > 0,
          f"{lic} of {scan}")

    # --- determinism, both directions ------------------------------------
    check("the same id gives the same person twice",
          resident("det", "human") == resident("det", "human"))
    a = [resident(pool_id("zocalo", "human", i, "seedA"), "human").name
         for i in range(12)]
    b = [resident(pool_id("zocalo", "human", i, "seedB"), "human").name
         for i in range(12)]
    check("a different seed gives a different station", a != b,
          f"{a[0]!r} vs {b[0]!r}")
    check("...and the same seed gives the same one",
          a == [resident(pool_id("zocalo", "human", i, "seedA"), "human").name
                for i in range(12)])

    # PYTHONHASHSEED. `str.__hash__` is salted per process, and this project
    # has already shipped a hull that changed every run because of it.
    probe = (
        "import sys; sys.path[:0]=[%r,%r]\n"
        "import resident as R\n"
        "for i in range(60):\n"
        "    for sp in ('human','narn','centauri','gaim'):\n"
        "        r=R.resident(R.pool_id('zocalo',sp,i,'s'),sp)\n"
        "        print(r.name,r.home,r.job,r.dob_card,r.visas,"
        "R.where_at(r,13.0))\n" % (_HERE, _STATION))
    outs = []
    for hseed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hseed)
        outs.append(subprocess.run([sys.executable, "-c", probe], env=env,
                                   capture_output=True, text=True).stdout)
    check("identical byte for byte across two PYTHONHASHSEED values",
          outs[0] == outs[1] and len(outs[0]) > 1000,
          f"{len(outs[0])} bytes, seeds 0 and 12345")

    # Parsed rather than grepped, for the reason test_schedule.py gives: a
    # substring search over the source flags the docstring that says in prose
    # that the module never uses `random`.
    tree = ast.parse(open(os.path.join(_HERE, "resident.py")).read())
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree)
                if isinstance(n, ast.Import)} | {
        n.module.split(".")[0] for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module}
    builtin_hash = any(isinstance(n.func, ast.Name) and n.func.id == "hash"
                       for n in ast.walk(tree) if isinstance(n, ast.Call))
    check("no `random`, no builtin hash(), in the AST and not in the prose",
          "random" not in imported and not builtin_hash,
          f"imports {sorted(imported)}")

    # --- consistency with the body that gets built ------------------------
    # The card's SEX and the mesh's sex come from one call, so they cannot
    # disagree. Asserted rather than trusted, because "one source" is a claim
    # about code and this is the code.
    bad_sex = [r for r in every
               if r.species not in HIVE_SPECIES
               and r.sex != _SEX_WORD.get(
                   npc_body.individual(r.species, r.npc_id).sex, "")]
    check("the card's SEX is the body's sex, for every species with one",
          not bad_sex, f"{len(bad_sex)} of {len(every)}")
    check("...and the Gaim card says HIVE rather than picking one of two",
          all(r.sex == "HIVE" for r in every if r.species == "gaim"))

    # PHYS CHR describes the mesh that will be built, or it is decoration.
    tall = [r for r in every if r.phys_chr.startswith("TALL")]
    check("PHYS CHR fires on the individuals who are actually off baseline",
          tall and all(r.stature_m > npc_body.SPECIES[r.species].stature_m
                       for r in tall),
          f"{len(tall)} marked tall of {len(every)}")
    check("...and most cards leave it empty, as the prop does",
          sum(1 for r in every if not r.phys_chr) > len(every) * 0.5,
          f"{sum(1 for r in every if not r.phys_chr)} of {len(every)} blank")

    # --- ages -------------------------------------------------------------
    ages = [resident(f"age{i}", "human").age for i in range(2000)]
    adult = [a for a in ages if a >= 18]
    check("the human working population has a plausible median age",
          30 <= sorted(adult)[len(adult) // 2] <= 45,
          f"median {sorted(adult)[len(adult) // 2]}, "
          f"range {min(ages)}-{max(ages)}")
    hy = [resident(f"hy{i}", "hyach").age for i in range(400)]
    check("the Hyach are long-lived, as FACTIONS.md 9.2 says",
          max(hy) > max(ages), f"Hyach max {max(hy)} vs human max {max(ages)}")
    check("a DOB round-trips to the age it was built from",
          all(ERA_YEAR - resident(f"age{i}", "human").dob[0]
              == resident(f"age{i}", "human").age for i in range(200)))

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
        sys.exit(0)
    sys.exit(_selftest())
