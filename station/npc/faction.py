#!/usr/bin/env python3
"""THE 28 FACTIONS, AS A THING CODE CAN ASK ABOUT.

WHAT WAS MISSING, MEASURED RATHER THAN SUMMARISED. CLAUDE.md's scope names
*"every major faction present, with the friction between them visible in a
corridor"*, and `docs/spec/PEOPLE.md` §1 enumerates 28 of them (FAC-01..FAC-28)
with numbers, territory, hours, two frictions apiece and an acceptance check.

**`station/npc/faction.py` did not exist.** `grep -rn "faction" station/*.py
station/npc/*.py` returned prose in six docstrings and one image in
`reference/`. What the code actually had was `npc/friction.py`'s twelve PAIRS,
keyed on **species** and **role** -- and a faction is neither:

    Nightwatch (FAC-04)  is an ARMBAND over a security uniform and an allowance
                         in a civilian pocket. Not a species, not a role.
    Psi Corps  (FAC-05)  is a BADGE. `resident.licensed_psi`.
    the Rangers(FAC-28)  is a BROOCH. `costume.costume_for(...).set_key`.
    org. crime (FAC-25)  is a PLACE and a ledger. Nobody's role says it.
    the Guild  (FAC-06)  is a CARD -- 1,500 of the 9,650 dockworker heads.
    the Markab (FAC-22)  is a species with **zero** members, and that is the
                         content.

So `MASTER-PLAN.md`'s gate for the row -- *"two factions' members pass"* --
could not even be **stated**, because nothing could answer "which factions is
this person in". That is what this module is: the membership question, the
head-count question, the territory question, and **what two members of two
factions DO when they pass each other in a corridor**.

WHAT IS DERIVED AND WHAT IS DECLARED
------------------------------------
Nothing here restates a number that exists elsewhere. Every head-count is a
call:

    role heads          `schedule.role_headcount()`      (ROLE_WEIGHTS x counts)
    species heads       `schedule.STATION_COUNTS`
    the armband         `costume.costume_for(...).nightwatch`, which already
                        carries the security rate AND the civilian informer
                        rate, both era-gated on `nightwatch_visible`
    the badge           `resident.Resident.licensed_psi` / PSI_LICENSED_ABOARD
    the brooch          `costume.RANGERS_ABOARD` via the costume set key
    the guild card      `security`-style: a declared share of the role, INV-271
    territory           asserted against `directory.py`'s register, so a
                        faction cannot own a place that does not exist

Declared here and nowhere else (authority 5, INV-270..INV-273): the corridor
VERB each side of a friction takes, the guild-carded share, and the tiebreak
when the sources do not say who yields. Every one is argued at its table.

THE VERBS, AND WHY THEY ARE A CLOSED LIST
-----------------------------------------
`friction.py` produces a **distance**: how much room two people leave each
other. That is the right primitive and it is not a behaviour. A corridor is
2.16 m wide and a Narn and a Centauri want 1.80 m of it, which the corridor
cannot give once two bodies are in it -- so *something else has to happen*, and
FACTIONS.md §12 says exactly what:

    "The Narn stops, turns, and does not yield the corridor. The Centauri
     crosses to the far side. Neither speaks. Groups reroute around each other
     entirely."

Two different verbs for the two sides of one row. `RESPONSES` below is that,
for every row, in the source's own words where the source has words. The list
is closed at eight because a ninth would be invention with no sentence behind
it.

Run: python3 station/npc/faction.py --report
     python3 station/npc/faction.py --selftest
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_STATION = os.path.dirname(_HERE)
if _STATION not in sys.path:                                 # pragma: no cover
    sys.path.insert(0, _STATION)

from npc import costume as cos                                 # noqa: E402
from npc import friction as fr                                 # noqa: E402
from npc import resident as res                                # noqa: E402
from npc import schedule as sched                              # noqa: E402

SPEC = os.path.join(os.path.dirname(_STATION), "docs", "spec", "PEOPLE.md")


# ===========================================================================
# 1.  THE VERBS -- what a body does in a corridor
# ===========================================================================
#
# key -> (does the walker keep walking, what a player sees, where it comes
#         from). A verb that does not change the geometry is not on this list;
#         `quieten` is the one exception and it is on it because FACTIONS.md
#         §12's Nightwatch row is a SPEECH behaviour and pretending otherwise
#         would be inventing a movement the source does not describe.
VERBS = {
    "widen":  (True,  "shifts across the corridor to leave the required room",
               "FACTIONS.md 12's own closing rule -- '95% as avoidance'"),
    "cross":  (True,  "crosses to the far side of the corridor and stays there",
               "FACTIONS.md 12, Narn/Centauri: 'The Centauri crosses to the "
               "far side'"),
    "hold":   (False, "stops, turns, and holds the middle of the corridor",
               "FACTIONS.md 12, Narn/Centauri: 'The Narn stops, turns, and "
               "does not yield the corridor'"),
    "aside":  (False, "steps into the nearest doorway and waits for them to "
               "pass",
               "PEOPLE.md FAC-11: 'one caste leaves before the other arrives'; "
               "the doorway is `deck_plan`'s own door list"),
    "reverse": (False, "turns round and leaves the way they came",
                "PEOPLE.md FAC-03 friction 2: 'lurkers reverse out of a "
                "corridor a patrol enters, and the patrol does not follow'"),
    "clear":  (False, "leaves the corridor entirely",
               "FACTIONS.md 12, Vorlon: 'When he moves, the corridor clears "
               "without being told to'"),
    "quieten": (True, "keeps walking and stops talking",
                "FACTIONS.md 12 / PEOPLE.md FAC-04: 'a human talking with "
                "aliens lowers his voice when an armband passes'"),
    "none":   (True,  "nothing -- they pass",
               "the null case, so 'no friction' is a value and not a gap"),
}

# A verb that stops the walker costs them time. The number is DERIVED, not
# chosen: it is how long the other party takes to clear the encounter, which
# `encounter.py` computes from the two closing speeds and the sight line. What
# is declared here is only the FLOOR -- a body that stops and starts again does
# not do it instantly. From `navigation.walk_speed`'s own gait: a walker at
# 1.2 m/s stopping and restarting at a comfortable 1.0 m/s^2 loses 2 x 1.2 s.
# INV-272.
STOP_RESTART_S = 2.4


# ===========================================================================
# 2.  MEMBERSHIP -- how you tell, from a person, which factions they are in
# ===========================================================================
#
# A clause is (kind, value). A person is in a faction if they match ANY of its
# clauses. Kinds, and the ONE resolver each of them has:
#
#   species   `who["species"]`                      -- schedule.STATION_COUNTS
#   role      `who["role"]`                         -- schedule.ROLE_WEIGHTS
#   flag      a named boolean, resolved by `_FLAGS` -- every one of them is
#             already computed by a shipped module; none is invented here
#   place     `who["home"]` or `who["job"]` or where they are standing
#
# `place` is the kind that makes FAC-25 expressible at all: organised crime has
# no role and no species, it has three rooms and a route.

def _flag_armband(who, datum):
    """Is this person wearing a Nightwatch armband RIGHT NOW at `datum`?

    `costume.costume_for` owns it -- security at NIGHTWATCH_SECURITY_RATE and
    human civilians at the informer rate x the visible fraction, both gated on
    `era_active('nightwatch_visible')`. Asking costume rather than rolling a
    second die is what keeps the sleeve in the render and the behaviour in the
    corridor talking about the same person.
    """
    sp = who.get("species", "human")
    if sp not in cos.body.SPECIES:
        return False
    try:
        return bool(cos.costume_for(sp, who["id"], datum,
                                    role_key=who.get("role")).nightwatch)
    except (KeyError, ValueError):                           # pragma: no cover
        return False


def _flag_psi(who, datum):
    """LICENSED PSI on the card. `resident.PSI_LICENSED_ABOARD` = 25."""
    return bool(who.get("psi"))


def _flag_ranger(who, datum):
    """The brooch. `costume.RANGERS_ABOARD` = 40 in 250,000, era-gated."""
    sp = who.get("species", "human")
    if sp not in ("human", "minbari"):
        return False
    try:
        return cos.costume_for(sp, who["id"], datum,
                               role_key=who.get("role")).set_key == "ranger"
    except (KeyError, ValueError):                           # pragma: no cover
        return False


def _flag_sanctuary(who, datum):
    """A stateless Narn. `resident._visa` writes SANCTUARY post-(2,20)."""
    return str(who.get("visa", "")).startswith("SANCTUARY")


def _flag_guild(who, datum):
    """A carded docker: 1,500 of the 9,650 dockworker heads (TRAFFIC:596-667).

    A SHARE OF THE ROLE, drawn deterministically off the id, exactly the way
    `security.wears_armband` draws the armband -- because the source gives a
    population and not a rule, and a share is the only honest reading of a
    population. INV-271.
    """
    if who.get("role") != "dockworker":
        return False
    return res._u(who["id"], "guild") < GUILD_CARDED / max(
        1.0, sched.role_headcount().get("dockworker", 1))


# A flag whose population lives INSIDE a role: the guild card is drawn on
# dockworkers, the armband on security. Consulted by `head_count` so a subset
# is never added to its own superset.
_FLAG_SUBSET_OF = {"guild": "dockworker", "sanctuary": None,
                   "armband": None, "psi": None, "ranger": None}

_FLAGS = {
    "armband": _flag_armband,
    "psi": _flag_psi,
    "ranger": _flag_ranger,
    "sanctuary": _flag_sanctuary,
    "guild": _flag_guild,
}

# PEOPLE.md FAC-06: "1,500 guild-carded core (TRAFFIC:596-667)".
GUILD_CARDED = 1500


# ===========================================================================
# 3.  THE REGISTER -- PEOPLE.md 1, row for row
# ===========================================================================
#
# (fid, name, clauses, territory, hours, era_event or None, note)
#
# `territory` is register keys from `directory.py` and is ASSERTED against it,
# so a faction cannot hold a room the station does not have. Keys PEOPLE.md
# names as "placed -- SHB-xx" but which the register does not yet carry are
# listed in `PENDING` instead of being quietly dropped: a faction whose ground
# is unbuilt is a state of the build, not a rounding detail.

FACTIONS = (
    ("FAC-01", "EarthGov civil administration",
     (("role", "customs"),),
     ("law_courts", "customs_north", "customs_south", "quartermaster",
      "post_office", "business_center", "admin_complex"),
     "office 09:00-17:00; customs on all three watches", None,
     "900 admin+customs heads inside the 6,500 EarthForce/staff"),

    ("FAC-02", "EarthForce command",
     (("role", "command"),),
     ("cnc", "war_room", "qtr_command", "earharts"),
     "continuous 3-watch rotation, 00/08/16", None,
     "120 command heads, 3 watches in Obs Dome 1"),

    ("FAC-03", "Security",
     (("role", "security"),),
     ("security_central", "security_posts", "brig", "customs_north",
      "customs_south", "zocalo", "council_chamber", "bay_elevators",
      "docking_bays"),
     "watches A/B/C at 00/08/16; zero posts in Downbelow by rule", None,
     "500 officers, ~150 on duty per watch, patrol unit = 2 always"),

    ("FAC-04", "Nightwatch",
     (("flag", "armband"),),
     ("nightwatch",),
     "wherever its wearers' shifts are", "nightwatch_visible",
     "an overlay, not a force: 175 of 500 officers plus 1-2% of 155,000 "
     "humans as informers"),

    ("FAC-05", "Psi Corps",
     (("flag", "psi"),),
     ("telepath_office",),
     "office 09:00-17:00", None,
     "25 licensed aboard: a 1-in-10,000 encounter by design"),

    ("FAC-06", "The Dockers' Guild",
     (("role", "dockworker"), ("role", "traffic"), ("flag", "guild")),
     ("docking_bays", "cargo_bays", "bay_elevators"),
     "fixed day shift 06:00-15:00; muster crowds 06:00 and 14:00", None,
     "9,650 dockworker heads, 1,500 guild-carded core"),

    ("FAC-07", "Medical service",
     (("role", "medical"),),
     ("medlab_one", "infirmary", "isolab", "morgue", "cryo_storage",
      "medlab_red", "medlab_green", "medlab_others"),
     "08:00/20:00 12-hour turnover; the free clinic evenings", None,
     "2,800 medical heads"),

    ("FAC-08", "The Zocalo merchants",
     (("role", "merchant"),),
     ("zocalo", "shops_kiosks", "eclipse_cafe", "cargo_bays"),
     "merchant shift 09:00 for 11 h", None,
     "39,300 merchant heads; the Traders' Association is the named subset"),

    ("FAC-09", "The Narn",
     (("species", "narn"),),
     ("ambassadorial_suites", "refugee_reception"),
     "sleep 21:30-05:30; aid queue from 06:00; traders 09:00-20:00",
     None,
     "22,500: 30 mission, 6,000 traders, 13,000 refugees, 2,470 Downbelow, "
     "1,000 transient -- stateless post-(2,20)"),

    ("FAC-10", "The Centauri",
     (("species", "centauri"),),
     ("ambassadorial_suites", "casino", "business_center", "fresh_air"),
     "late; the casino is culturally theirs", None,
     "17,500, of whom 1,350 Downbelow"),

    ("FAC-11", "The Minbari",
     (("species", "minbari"),),
     ("zen_garden", "sanctuaries", "council_chamber"),
     "the Sanctuary rota; caste turnover at 18:00", None,
     "12,500 -- 'a warrior-caste Minbari in a corridor is an event'"),

    ("FAC-12", "The League of Non-Aligned Worlds",
     tuple(("species", s) for s in fr.LEAGUE),
     ("league_delegations", "alien_sector", "council_chamber"),
     "council hours; the anteroom is staffed 09:00-17:00", None,
     "the council organ: a bloc of nine, and a rotating tenth seat"),

    ("FAC-13", "The Drazi", (("species", "drazi"),),
     ("dark_star",), "dock gang hours", None,
     "12,500; the colour split is OFF at datum and the switch exists"),

    ("FAC-14", "The Brakiri", (("species", "brakiri"),),
     ("business_center", "casino", "dark_star"),
     "night desks 18:30-02:30", None,
     "7,500 -- 'the Brakiri keep the Zocalo from silence overnight'"),

    ("FAC-15", "The pak'ma'ra", (("species", "pakmara"),),
     ("waste_control",), "meal windows 04:00 and 16:00", None,
     "6,250 -- the only species with a segregated food economy"),

    ("FAC-16", "The Vree", (("species", "vree"),),
     ("docking_bays", "cargo_bays", "zocalo"),
     "08:00-19:00 at the manifest desk", None,
     "5,000; their saucers stand off and never berth"),

    ("FAC-17", "The Abbai", (("species", "abbai"),),
     ("hydroponics", "alien_sector"), "09:00-17:00", None,
     "3,750; breather-dependent, the humid zone is theirs"),

    ("FAC-18", "The Gaim", (("species", "gaim"),),
     ("alien_sector",), "in-zone meals bracket the shift", None,
     "2,500 behind a methane lock; every arrival is a secondary referral"),

    ("FAC-19", "The Hyach", (("species", "hyach"),),
     ("business_center", "council_chamber"),
     "arrive at the stated minute, leave at the stated minute", None,
     "1,750"),

    ("FAC-20", "The Llort", (("species", "llort"),),
     ("downbelow", "dark_star", "black_market"), "overnight", None,
     "1,250; the fence's overnight suppliers"),

    ("FAC-21", "The Grome", (("species", "grome"),),
     ("hydroponics",), "field hours", None, "750"),

    ("FAC-22", "The Markab (the absence)", (("species", "markab"),),
     ("markab_quarter",), "none -- the quarter is sealed at every hour",
     "!markab_extinct",
     "0 aboard. The only faction whose head-count must be zero, and the "
     "sealed quarter is 'the only monument to an extinct species'"),

    ("FAC-23", "The Vorlon (Kosh)",
     (("species", "vorlon"), ("role", "envoy")),
     ("kosh_quarters", "council_chamber"), "almost never", None,
     "1"),

    ("FAC-24", "Downbelow / the lurkers",
     (("role", "lurker"),),
     ("downbelow", "downbelow_arch", "subfloor_stack"),
     "salvage by day, fence by night", None,
     "20,390 lurker heads; 4 camps pinned to the sector waste plants"),

    ("FAC-25", "Organised crime",
     (("place", "ngrath"), ("place", "thieves_guild"),
      ("place", "black_market")),
     ("ngrath", "thieves_guild", "black_market"),
     "audiences 20:00-02:00 by token", None,
     "no role and no species -- three rooms and a route. 'Lurkers are its "
     "victims, not its authors'"),

    ("FAC-26", "Religious orders", (("role", "cleric"),),
     ("sanctuary_blue", "sanctuaries", "interfaith_chapel", "alien_worship"),
     "cleric shift 06:00; the Minbari rota", "monastics_resident",
     "7,300 cleric heads"),

    ("FAC-27", "ISN", (("place", "business_center"),),
     ("arrival_concourse", "business_center"),
     "files 10:00; liner-day concourse", None,
     "presence without premises -- a stringer and the screens"),

    ("FAC-28", "The Rangers", (("flag", "ranger"),),
     ("bar_unnamed",), "the brooch worn open, 19:00-22:00",
     "rangers_visible",
     "40 aboard in 250,000; 'the tell is the brooch'"),
)

BY_ID = {f[0]: f for f in FACTIONS}

# PEOPLE.md gives these as faction territory, `station/npc/` treats them as
# real, and `directory.PLACES` -- the 128-place GEOMETRY register -- does not
# carry either. Named rather than dropped, because a faction whose ground is
# unbuilt is a fact about the build and not a rounding detail:
#
#   markab_quarter      is a `schedule.PlaceCrowd` (crowd.py:554,
#                       schedule.py:1041) and `navigation.EXPECTED_ISLANDS`'
#                       only island. Every hour of every day it holds zero
#                       people, which is FAC-22's whole content -- and there is
#                       nowhere to stand and look at it.
#   refugee_reception   is `schedule.ROLES`' workplace for the refugee role
#                       (schedule.py:321) -- 13,000 people whose day IS the
#                       queue (resident.py:760-767) -- with no address.
#
# `_selftest` asserts this list only ever SHRINKS by something being built,
# never grows to make an assertion pass: the count is capped at what it is now.
PENDING = ("markab_quarter", "refugee_reception")
PENDING_CAP = 2


def faction(fid):
    return BY_ID[fid]


def era_ok(era, datum):
    """Is a faction's era gate satisfied at `datum`?

    TWO POLARITIES, AND THE SECOND ONE IS THE MARKAB. `"nightwatch_visible"`
    means the faction STARTS at that event; `"!markab_extinct"` means it ENDS
    at one. Written as one function because the first cut had only the first
    polarity, and a species that had been dead for eleven episodes came back
    the moment the datum passed its own extinction.
    """
    if not era:
        return True
    if era.startswith("!"):
        return not cos.era_active(era[1:], datum)
    return cos.era_active(era, datum)


def head_count(fid, datum=None):
    """How many people this faction has aboard. DERIVED every time.

    Species clauses go to `schedule.STATION_COUNTS`, role clauses to
    `schedule.role_headcount`, flags to the module that owns the flag. Nothing
    below is a number typed into this file.
    """
    datum = datum or cos.ERA_DATUM
    _fid, _nm, clauses, _t, _h, era, _note = BY_ID[fid]
    if not era_ok(era, datum):
        return 0
    roles = sched.role_headcount()
    counted_roles = {v for k, v in clauses if k == "role"}
    n, censused = 0, False
    for kind, val in clauses:
        if kind == "species":
            n += int(sched.STATION_COUNTS.get(val, 0))
            censused = True
        elif kind == "role":
            n += int(roles.get(val, 0))
            censused = True
        elif kind == "flag":
            # A CARD IS A SUBSET OF A JOB, NOT AN ADDITION TO IT. The Guild's
            # 1,500 carded core are 1,500 OF the 9,650 dockworker heads, so a
            # register that adds them reports 11,550 dockers on a station that
            # has 9,650. Every flag names the role it subsets, or none.
            if _FLAG_SUBSET_OF.get(val) in counted_roles:
                continue
            n += _flag_population(val, datum)
            censused = True
    return n if censused else None


def _flag_population(flag, datum):
    """The aboard-count for a flag, from the module that owns the flag."""
    if flag == "armband":
        # security officers + visible civilian informers, both from costume's
        # own rates, both era-gated there.
        officers = sched.role_headcount().get("security", 0)
        humans = sched.STATION_COUNTS.get("human", 0)
        return int(round(officers * cos.NIGHTWATCH_SECURITY_RATE
                         + humans * cos.NIGHTWATCH_CIVILIAN_INFORMER_RATE
                         * cos.NIGHTWATCH_CIVILIAN_VISIBLE_FRACTION))
    if flag == "psi":
        return res.PSI_LICENSED_ABOARD
    if flag == "ranger":
        return cos.RANGERS_ABOARD
    if flag == "guild":
        return GUILD_CARDED
    if flag == "sanctuary":                                  # pragma: no cover
        return int(sched.STATION_COUNTS.get("narn", 0))
    raise KeyError(flag)                                     # pragma: no cover


def _person(who):
    """Accept either a crowd row's `who` dict or a `resident.Resident`."""
    if isinstance(who, dict):
        return who
    return {"id": who.npc_id, "species": who.species, "role": who.role,
            "psi": who.licensed_psi, "visa": who.visas,
            "home": who.home, "job": who.job}


def factions_of(who, at=None, datum=None):
    """Every faction this person belongs to, as a sorted tuple of FAC ids.

    THE FUNCTION THE MASTER-PLAN GATE NEEDS. *"Two factions' members pass"* is
    not a checkable sentence until something can answer this, and before this
    module nothing could.

    `at` is the place key they are standing in, for the `place` clauses -- an
    ISN stringer and a fixer are defined by where they are, not by what their
    card says.
    """
    p = _person(who)
    datum = datum or cos.ERA_DATUM
    out = []
    for fid, _nm, clauses, _t, _h, era, _note in FACTIONS:
        if not era_ok(era, datum):
            continue
        for kind, val in clauses:
            if kind == "species" and p.get("species") == val:
                out.append(fid)
                break
            if kind == "role" and p.get("role") == val:
                out.append(fid)
                break
            if kind == "flag" and _FLAGS[val](p, datum):
                out.append(fid)
                break
            if kind == "place" and val in (at, p.get("home"), p.get("job")):
                out.append(fid)
                break
    return tuple(out)


def has_flag(who, flag, datum=None):
    """One named boolean about a person, at a datum. `_FLAGS`' resolver.

    Public because `npc/encounter.py` needs the armband AT THE SIMULATED
    DATUM rather than at the module default -- a corridor run at S2E01 whose
    officers still carry the armband `costume_for(..., ERA_DATUM)` gave them is
    a corridor that cannot show the era lock, and the first run of that gate
    reported "464 witnessed passes against 464".
    """
    return bool(_FLAGS[flag](_person(who), datum or cos.ERA_DATUM))


def facets(who, datum=None):
    """The keys `friction.PAIRS` can match this person on.

    Species AND role AND, sometimes, `telepath` -- FACTIONS.md 12 has rows for
    all three vocabularies and matching on one loses the others. Lifted here
    from `dialogue._facets` so the CORRIDOR and the CONVERSATION ask the same
    question; `_selftest` asserts the two agree.
    """
    p = _person(who)
    out = [p.get("species", ""), p.get("role", "")]
    if p.get("psi"):
        out.append("telepath")
    return tuple(x for x in out if x)


# ===========================================================================
# 4.  WHAT HAPPENS WHEN THEY PASS
# ===========================================================================
#
# PEOPLE.md gives every FAC block two frictions and, for most of them, the
# observable corridor behaviour in a sentence. `RESPONSES` is that sentence
# turned into two verbs -- one per side -- keyed on the `friction.PAIRS` row
# it comes from.
#
# ROW KEY -> (verb for side a, verb for side b, whose words these are)
#
# Where the source names the behaviour the verbs are quoted from it. Where it
# does not, the tiebreak is ONE rule, applied everywhere, and it is INV-270:
#
#     THE PARTY ON ITS OWN FACTION'S TERRITORY DOES NOT YIELD.
#
# Which is not a preference: PEOPLE.md gives every faction a `Territory` line
# of register keys, so "whose corridor is this" is already a fact the register
# can answer, and a corridor serving `docking_bays` is the Guild's ground in a
# way it is not the Psi Corps'. What would overturn it: a frame showing a
# docker giving way to a passenger on a dock deck.
RESPONSES = {
    ("narn", "centauri"): ("hold", "cross",
                           "FACTIONS.md 12 verbatim -- 'The Narn stops, turns, "
                           "and does not yield the corridor. The Centauri "
                           "crosses to the far side'"),
    ("human", "*"): ("quieten", "none",
                     "FACTIONS.md 12 -- 'a human talking with aliens lowers "
                     "his voice when an armband passes'. The alien does "
                     "nothing; the chill is on the human side"),
    ("security", "security"): ("none", "none",
                               "already built -- the friction is on the "
                               "sleeve, not in the feet (npc/security.patrol)"),
    ("telepath", "*"): ("none", "aside",
                        "FACTIONS.md 12 -- 'nobody sits at the adjacent "
                        "table'. The telepath walks; the room moves"),
    ("minbari", "human"): ("cross", "none",
                           "PEOPLE.md FAC-11 -- 'cold formality on the "
                           "Minbari side; older humans stare'. The formality "
                           "is a distance the Minbari keeps; the staring is "
                           "not a movement"),
    ("minbari", "minbari"): ("aside", "none",
                             "PEOPLE.md FAC-11 -- 'one caste leaves before "
                             "the other arrives'"),
    ("pakmara", "*"): ("none", "widen",
                       "FACTIONS.md 12 -- 'tables clear AROUND them'. They do "
                       "not move; everyone else does"),
    ("drazi", "drazi"): ("widen", "widen",
                         "episodic and OFF at datum -- both sides carry the "
                         "mild verb so the switch has somewhere to go"),
    # NOT `reverse`, AND THE DISTINCTION IS THE MODEL'S SHARPEST EDGE.
    # PEOPLE.md FAC-08's scene -- "a lurker lifted off a bench by two words
    # from a stallholder" -- happens at a STALL, and §12's own words for the
    # corridor are "conspicuous by clothing before anything else. AVOID
    # identicard readers". Avoidance, not retreat. A first cut had this at
    # `reverse` and 14 lurkers turned round 210 times an hour on one deck,
    # which is not a station, it is a farce. `reverse` belongs to the row that
    # literally says the word, which is security/lurker below.
    ("lurker", "merchant"): ("cross", "none",
                             "FACTIONS.md 12 -- 'moved on from the Zocalo. "
                             "Conspicuous by clothing before anything else. "
                             "Avoid identicard readers'"),
    ("narn", "command"): ("none", "widen",
                          "PEOPLE.md FAC-02 -- 'salutes that stop when a "
                          "SANCTUARY-visa Narn passes the party'. Cold, not "
                          "hostile: the officer gives the room"),
    ("vorlon", "*"): ("none", "clear",
                      "FACTIONS.md 12 -- 'when he moves, the corridor clears "
                      "without being told to'"),
    ("dockworker", "command"): ("none", "none",
                                "latent -- 'an event rather than ambient'. "
                                "The notice layer, not the feet"),
    ("security", "lurker"): ("none", "reverse",
                             "PEOPLE.md FAC-03 friction 2 -- 'lurkers reverse "
                             "out of a corridor a patrol enters, and the "
                             "patrol does not follow'"),
    # the League bloc, which `friction.pair` synthesises rather than tabling
    ("league", "*"): ("widen", "widen",
                      "PEOPLE.md FAC-12 -- 'the caucus visibly not being "
                      "consulted'. Low and constant: room, not a wall"),
}


def response(row, a_key, b_key):
    """`(verb_for_a, verb_for_b, source)` for a matched `friction` row.

    `row` is what `friction.pair`/`friction.strongest` returned and
    `(a_key, b_key)` are the keys that matched it, IN THE CALLER'S ORDER --
    because the Narn/Centauri row is asymmetric and answering it the wrong way
    round has the Centauri planted in the middle of the corridor.
    """
    pa, pb = row[0], row[1]
    key = (pa, pb)
    if key not in RESPONSES:
        # the synthesised League row: `friction.pair` returns (a, b, "low", ..)
        if row[2] == "low" and (pa in fr.LEAGUE or pb in fr.LEAGUE):
            key = ("league", "*")
        else:                                                # pragma: no cover
            return ("widen", "widen", "no tabled behaviour -- the default is "
                    "FACTIONS.md 12's own 95% avoidance")
    va, vb, why = RESPONSES[key]
    # The row's own sides decide which verb belongs to which caller. `pb == "*"`
    # means "b is anyone else", so the named side takes `va`.
    if key == ("league", "*"):
        a_named = a_key in fr.LEAGUE
    elif pb == "*":
        a_named = (a_key == pa)
    else:
        a_named = (a_key == pa)
    return (va, vb, why) if a_named else (vb, va, why)


def stops(verb):
    """Does this verb take the walker off their line? `VERBS`' own column."""
    return not VERBS[verb][0]


# ===========================================================================
# 5.  Report
# ===========================================================================

def report(out=print, datum=None):
    datum = datum or cos.ERA_DATUM
    out(f"THE 28 FACTIONS at datum {datum} -- docs/spec/PEOPLE.md 1")
    uncensused = []
    for fid, name, clauses, terr, _h, era, note in FACTIONS:
        n = head_count(fid, datum)
        kinds = ",".join(sorted({k for k, _v in clauses}))
        gate = f" [{era}]" if era else ""
        # NOT ZERO. A faction defined by a PLACE has no census -- FAC-25's own
        # PEOPLE.md line is "no role and no species: three rooms and a route",
        # and FAC-27's is "presence without premises". Printing 0 for those
        # would say the station has no organised crime, which is a different
        # claim from the one the spec makes and a much less true one.
        shown = f"{n:>7,}" if n is not None else "     --"
        out(f"  {fid} {name:38s} {shown}  by {kinds:14s} "
            f"{len(terr)} places{gate}")
        if n is None:
            uncensused.append(fid)
            out(f"         ^ no census: {note.split('.')[0]}")
        elif n == 0:
            out(f"         ^ {note.split('.')[0]}")
    out(f"  -- {len(FACTIONS)} factions; the membership clauses are "
        f"{sum(len(f[2]) for f in FACTIONS)} over four kinds; "
        f"{len(uncensused)} have no head-count by design "
        f"({', '.join(uncensused)})")
    out("")
    out("  THE CORRIDOR VERBS -- what a body actually does")
    for k, (walks, seen, src) in VERBS.items():
        out(f"    {k:8s} {'walks on' if walks else 'STOPS   '}  {seen}")
        out(f"             {src}")


# ===========================================================================
# 6.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _selftest(out=print):                                       # noqa: C901
    del _FAILED[:]
    n = 0
    datum = cos.ERA_DATUM

    # -- the register itself ------------------------------------------------
    n += 1
    check(len(FACTIONS) == 28,
          "PEOPLE.md 1 enumerates 28 factions and this register carries 28",
          f"{len(FACTIONS)}")
    n += 1
    ids = [f[0] for f in FACTIONS]
    check(ids == [f"FAC-{i:02d}" for i in range(1, 29)],
          "and they are FAC-01..FAC-28 with no gap and no repeat",
          str([i for i in ids if ids.count(i) > 1])[:60])
    n += 1
    txt = open(SPEC, encoding="utf-8").read() if os.path.exists(SPEC) else ""
    missing = [i for i in ids if f"### {i} " not in txt]
    check(not missing,
          "every id in this file has a block in docs/spec/PEOPLE.md -- the "
          "register cannot invent a faction the spec does not enumerate",
          str(missing))

    # -- territory is real --------------------------------------------------
    n += 1
    import directory as dr                                     # noqa: PLC0415
    keys = {q["key"] for q in dr.PLACES}
    bad = sorted({t for f in FACTIONS for t in f[3]} - keys - set(PENDING))
    check(not bad,
          "every faction's territory is a place the register actually holds -- "
          "a faction cannot own a room the station does not have",
          str(bad))
    n += 1
    still = sorted(set(PENDING) - keys)
    check(len(still) <= PENDING_CAP,
          "and the pending list only ever SHRINKS -- a territory that cannot "
          "be found may not be added to it to make the assertion above pass",
          f"{len(still)} of a cap of {PENDING_CAP}: {still}")
    n += 1
    check(all(k in sched.PLACES or k in
              {r.workplace for r in sched.ROLES} for k in PENDING),
          "...and every pending key is a place the PEOPLE layer already "
          "treats as real, so the gap is between the people register and the "
          "GEOMETRY register rather than a typo here",
          str([k for k in PENDING if k not in sched.PLACES]))

    # -- head-counts are derived, and one of them must be ZERO --------------
    n += 1
    check(head_count("FAC-22") == 0,
          "the Markab are EXTINCT and their head-count is zero -- the one "
          "faction whose correct answer is nobody, and the check that this "
          "register reports what the station is rather than what a faction "
          "list would like",
          f"{head_count('FAC-22')}")
    n += 1
    check(head_count("FAC-23") == 1,
          "and the Vorlon is one", f"{head_count('FAC-23')}")
    n += 1
    check(head_count("FAC-03") == 500 and head_count("FAC-02") == 120,
          "security is 500 and command is 120, from schedule.role_headcount "
          "and not from a number typed here",
          f"{head_count('FAC-03')}, {head_count('FAC-02')}")
    n += 1
    nw = head_count("FAC-04")
    check(150 <= nw <= 3200,
          "the Nightwatch is 175 armbanded officers plus the visible share of "
          "1-2% civilian informers -- FACTIONS.md 5.4's own band",
          f"{nw}")

    # -- the era gates ------------------------------------------------------
    n += 1
    check(head_count("FAC-04", (2, 1)) == 0 and head_count("FAC-04") > 0,
          "BEFORE The Fall of Night the Nightwatch has NO members -- the same "
          "era lock the armband itself carries",
          f"S2E01 {head_count('FAC-04', (2, 1))}, datum {nw}")
    n += 1
    check(head_count("FAC-28", (2, 1)) == 0 and head_count("FAC-28") == 40,
          "and the Rangers appear at Matters of Honor, not before",
          f"S2E01 {head_count('FAC-28', (2, 1))}, datum {head_count('FAC-28')}")

    # -- membership ---------------------------------------------------------
    n += 1
    narn = {"id": "b5/t/1", "species": "narn", "role": "merchant",
            "psi": False, "visa": "SANCTUARY", "home": "downbelow", "job": ""}
    check("FAC-09" in factions_of(narn),
          "a Narn is in FAC-09")
    n += 1
    check("FAC-08" in factions_of(narn),
          "...and a Narn MERCHANT is also in FAC-08, because a person is in "
          "more than one faction and that is the whole reason the corridor is "
          "interesting",
          str(factions_of(narn)))
    n += 1
    fixer = {"id": "b5/t/2", "species": "other", "role": "visitor",
             "psi": False, "visa": "", "home": "ngrath", "job": ""}
    check("FAC-25" in factions_of(fixer),
          "organised crime has no role and no species -- it is three rooms, "
          "and a person who lives in one is in it",
          str(factions_of(fixer)))
    n += 1
    # a real crowd row, so the shape the corridor actually hands us works
    r = res.resident("b5/corridor/blue/0/0/0", "human")
    check(isinstance(factions_of(r), tuple),
          "a `resident.Resident` resolves as well as a crowd row's dict")

    # -- the flags are somebody else's numbers ------------------------------
    n += 1
    band = sum(1 for i in range(2000)
               if _FLAGS["armband"]({"id": f"b5/nw/{i}", "species": "human",
                                     "role": "security"}, datum))
    check(0.25 < band / 2000 < 0.45,
          "the armband rate off 2,000 officers lands on costume.py's "
          "NIGHTWATCH_SECURITY_RATE, because this module ASKS costume rather "
          "than rolling a second die",
          f"{band}/2000 = {band / 2000:.3f} against "
          f"{cos.NIGHTWATCH_SECURITY_RATE}")
    n += 1
    band2 = sum(1 for i in range(2000)
                if _FLAGS["armband"]({"id": f"b5/nw/{i}", "species": "human",
                                      "role": "security"}, (2, 1)))
    check(band2 == 0,
          "...and it is zero before The Fall of Night, from the SAME call",
          f"{band2}")

    # -- the verbs ----------------------------------------------------------
    n += 1
    check(all(v in VERBS for va, vb, _s in RESPONSES.values() for v in (va, vb)),
          "every response uses a verb on the closed list")
    n += 1
    check(all(len(s) > 30 for _a, _b, s in RESPONSES.values()),
          "every response says whose words it is -- the half of PEOPLE.md's "
          "friction rows that is sourced")
    n += 1
    rows = {(p[0], p[1]) for p in fr.PAIRS}
    uncovered = sorted(rows - set(RESPONSES))
    check(not uncovered,
          "every friction.PAIRS row has a corridor behaviour -- a row with a "
          "separation and no verb is a distance nobody can see",
          str(uncovered))

    # -- the asymmetry, which is the whole point ---------------------------
    n += 1
    row = fr.pair("narn", "centauri")
    va, vb, _s = response(row, "narn", "centauri")
    vb2, va2, _s2 = response(row, "centauri", "narn")
    check((va, vb) == ("hold", "cross") and (vb2, va2) == ("cross", "hold"),
          "the Narn holds and the Centauri crosses, whichever order they are "
          "asked in -- an asymmetric row answered symmetrically puts the "
          "Centauri in the middle of the corridor",
          f"{va}/{vb} and {vb2}/{va2}")
    n += 1
    check(stops("hold") and not stops("cross"),
          "and they are different KINDS of delta: one stops, one does not")

    # -- facets agree with the module that already had them -----------------
    n += 1
    import dialogue as dlg                                     # noqa: PLC0415
    who = {"id": "b5/x", "species": "human", "role": "security", "psi": True}
    check(set(facets(who)) == set(dlg._facets("human", "security", True)),
          "this module's facet keys agree with `dialogue._facets`, which is "
          "the second copy of the same rule -- a change detector, so the "
          "corridor and the conversation cannot start disagreeing about what "
          "a person IS",
          f"{facets(who)} against {dlg._facets('human', 'security', True)}")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")
    ghost = {"id": "b5/t/9", "species": "markab", "role": "visitor",
             "psi": False, "visa": "", "home": "", "job": ""}
    got = factions_of(ghost)
    out(f"  a Markab resolves to {got or '()'} -- the era gate holds even "
        f"when a person of that species is constructed by hand")
    n += 1
    check("FAC-22" not in got,
          "an era-gated faction cannot be joined by constructing a member")

    keep = dict(RESPONSES)
    try:
        RESPONSES.clear()
        v = response(fr.pair("narn", "centauri"), "narn", "centauri")
        out(f"  with RESPONSES emptied, the Narn/Centauri row falls back to "
            f"{v[0]}/{v[1]} -- the asymmetry gate "
            f"{'FIRES' if v[:2] == ('widen', 'widen') else 'DOES NOT FIRE'}")
        n += 1
        check(v[:2] == ("widen", "widen"),
              "the asymmetry gate fires when the response table is emptied")
    finally:
        RESPONSES.update(keep)

    z = head_count("FAC-28", (2, 1))
    out(f"  the Rangers at S2E01: {z} against {head_count('FAC-28')} at the "
        f"datum -- the start-at gate "
        f"{'FIRES' if z == 0 else 'DOES NOT FIRE'}")
    mk = head_count("FAC-22", (2, 1))
    out(f"  the Markab at S2E01 (before Confessions and Lamentations): "
        f"{mk:,} against {head_count('FAC-22')} at the datum -- the "
        f"ends-at gate {'FIRES' if mk > 0 else 'DOES NOT FIRE'}")
    n += 1
    check(mk == 0,
          "and the Markab are zero at BOTH datums, because STATION_COUNTS "
          "carries the extinction as a count of nought rather than as a flag "
          "-- the era gate on FAC-22 is belt and braces over a species the "
          "census has already emptied",
          f"S2E01 {mk}")

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
    if a.report:
        report()
        print()
    raise SystemExit(0 if _selftest() else 1)
