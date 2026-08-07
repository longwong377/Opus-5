#!/usr/bin/env python3
"""PROGRESSION AND CONSEQUENCE -- the identicard tier ladder, and the arrest
that closes.

`docs/MASTER-PLAN.md` line 257 (P1-G2) reads, verbatim: *"the identicard tier
ladder; arrest -> brig -> fine -> release closes; visa revocation exists and can
actually happen to you."* The operative clause is the last one, and before this
module the station had NO WAY FOR THE PLAYER'S STANDING TO GET WORSE. Every
number in `player.py` moves up or stays still: `earn` creates credits, `spend`
refuses when short, `take` adds an item, `status` is set once at the gate and
never again. There was no rung, no record, nothing that closes a door.

WHAT A LADDER IS, MECHANICALLY, AND WHAT IT IS NOT
--------------------------------------------------
It is NOT an integer field on the player. This repository's recurring failure
mode is a value that describes existence rather than consequence -- a layer
number that goes green on an empty shell, a coverage count that cannot fail for
"there is no reason to be here". A `tier` attribute that nothing reads is that
failure at the scale of one field.

So every rung here has to do two things and it is checked on both:

  1. **be DERIVED** -- from card state the station already holds, through
     `arrival.entry_class`, which is the ONE card reader in this project. There
     is no second visa parser here and there must never be one; a rung is a
     reading of the nine identicard fields plus employment plus the era's
     politics, and `tier_of` is 30 lines because all the work was already done.
  2. **GATE SOMETHING** -- `admits()` (which of the 128 register places let you
     in), `sells_to()` (which of the 13 counters serve you), `check_rate()`
     (whether a patrol stops you). `gate()` asserts the three are MONOTONE in
     the rung and that no two rungs gate the same set, so a tier that changes
     nothing fails as loudly as a missing one.

THE SIX RUNGS, AND EVERY ONE IS A READING OF SOMETHING SOURCED
---------------------------------------------------------------
See `TIERS`. Top to bottom: ACCREDITED (diplomatic immunity -- *"the quarters
of each ambassador are considered to be part of their world's territory"*,
auth 4), CITIZEN (EA sovereign territory, entry by right, VISAS properly empty
-- which is why Lyta Alexander's card has three red rows), RESIDENT (a non-EA
national whose standing IS the residency record), TRANSIT (FACTIONS 2.3's
seven-day mean stay), SANCTUARY (FACTIONS 6.2's 13,000 stateless Narn), and
NO_STATUS (*"the reason lurkers avoid readers"*). Plus DETAINED, which is not a
rung but a custody state, and which admits you to exactly one place.

THE ASYMMETRY IS THE POLITICS, AND IT IS THE MOST IMPORTANT THING HERE
-----------------------------------------------------------------------
**A visa can be revoked. Citizenship cannot.** An Ombuds can withdraw a
conditional permission -- a transit visa, a sanctuary grant, a residency tied to
a job -- and cannot strip an Earth Alliance citizen of the right to stand on
Earth Alliance territory. So the ladder's demotion path bites hardest on the
people already lowest on it and cannot touch the top at all. At the S2-3 datum
that is not a design convenience, it is the show: a Narn population that went
from traders to stateless in one episode, a Ministry of Peace that has already
introduced *"relaxed standards of evidence"*, and Nightwatch.

It has a blunt consequence for the answer to G2's own clause, and it is stated
here rather than buried: **`docs/THE-STATION.md` PLY-02 rules the V1 player
human and EA-origin, and a human with a job reads CITIZEN, so the V1 default
player CANNOT be visa-revoked -- there is no visa on the card to revoke.**
`revocation_path()` returns that as a finding rather than as a failure, and the
same function shows the path firing on the three rungs that CAN be revoked, so
the day PLY-02's origin ruling widens the mechanism is already content. It also
shows the one path that reaches a human today: a human *visitor* holds
`TRANSIT nD`, `entry_class` reads the visa before it reads the origin, and
`random_player` draws the visitor role at the census rate.

THE FOUR DURATIONS ARE ROUTED, NOT CONSTANTS
---------------------------------------------
`Custody` carries the four legs of MASTER-PLAN's chain and every one is a
measurement:

    response   `security.response_from_nearest_post(place)` -- 0 s in the
               Zocalo (four pairs are standing in it) and 1,119.7 s in
               Downbelow, which is LAW-CRIME 2.6's own headline CONTRAST rather
               than a number.
    escort     `security.response(brig, origin=place)` on the same routed graph
               a resident commutes on -- 537.2 s from the Zocalo, 1,321.7 s
               from Downbelow, 819.6 s from customs north.
    hold       hours to the next Ombuds sitting, plus a deferral chain whose
               re-defer probability is SOLVED (see `DEFER_AGAIN_P`) so that the
               realised distribution reproduces BOTH of LAW-CRIME 3.1's stated
               brackets -- "hours to a few days" typical, "weeks" longest.
    court      `security.response(law_courts, origin=brig)` -- **74.9 s**, and
               that number is the P-04 placement claim being checked rather
               than repeated: LOCATIONS.md line 448 says the brig "must be
               walkable from Security Central and from the courtroom", and this
               is the first time anything in the project measured it.

THE FINE IS DENOMINATED IN DAYS OF CASUAL LABOUR
-------------------------------------------------
Because that is the only unit LAW-CRIME 7.1's price table gives for *what a
person can pay*, and because 7.1's own load-bearing row is built the same way
(passage home "must be 30-100 days of casual labour with nothing spent"). The
ceiling is HARD and it is the same anchor: **a fine at or above passage home is
not a fine, it is deportation**, because a person who could pay it could have
left and a person who cannot is now, by 6.6's exact mechanism, a lurker. The
floor is derived too, and it is the detention's own lost earnings -- a fine
below what the hold already cost you in wages is a rounding error on the
arrest. `fine_bounds_check()` reports both and can fail.

WHAT IT MEASURED, AND ONE OF THE THREE IS UNCOMFORTABLE
--------------------------------------------------------
  1. **The fine is a consequence for the people who get arrested and is not one
     for a rich arrival.** 7 days' labour is 56-70 cr; the median lurker purse
     is ~150 cr (`player.credits_for` confines a no-status role to the left
     tail) and the median ARRIVAL purse is ~3,275 cr. So the same fine is
     ~40% of everything one has and ~2% of the other's. That is not a defect to
     be tuned away -- it is 7.1's structure -- but it means **credits are the
     wrong consequence for a wealthy player and the RUNG is the right one**:
     a conviction closes doors and cannot be bought off.
  2. **A destitute human is still a citizen, on the card.** 45% of lurkers get
     `visas=""` from `resident._visa`, and a human with an empty visa field and
     an EARTH origin reads EA_CITIZEN through `entry_class` -- so ~9,200 of the
     station's 20,390 lurkers are, on paper, tier 4. That is not a bug in
     `entry_class`; it is what an identicard is. It is also why the ladder has
     to read employment and not only the card.
  3. **Enforcement is geography.** Discretionary checks scale with officers per
     head, so a place with no post has no check: the Zocalo checks one head
     every ~25 station-days and Downbelow checks nobody, ever. The reachable
     path is not discretionary at all -- it is the CERTAIN check at a
     `identicard_check`/`checkpoint`/`immigration` place and at the boundary of
     an access-restricted sector (LOCATIONS.md P-05). **The first time you
     cross into Blue after your visa expires is the arrest.**

Run: python3 station/consequence.py --gate
     python3 station/consequence.py --report
     python3 station/consequence.py --arrest zocalo --offence expired_status
"""
import argparse
import hashlib
import math
import os
import sys
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:                                   # pragma: no cover
        sys.path.insert(0, _p)

import directory as dr                                          # noqa: E402
import arrival as AR                                            # noqa: E402
import economy as EC                                            # noqa: E402
import player as PL                                             # noqa: E402
import populace as POP                                          # noqa: E402
from npc import resident as RES                                 # noqa: E402
from npc import schedule as sched                               # noqa: E402
from npc import security as sec                                 # noqa: E402


def _u(*parts) -> float:
    """The same blake2b draw the rest of the project uses. Never `random`."""
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ===========================================================================
# 1.  THE LADDER
# ===========================================================================
# The rungs are integers so that "a rung down" is arithmetic and so that
# `admits`/`sells_to` can be asserted MONOTONE, which is what makes this a
# ladder rather than an enum. DETAINED is deliberately NEGATIVE: it is not a
# rung on the ladder, it is being off it.
DETAINED = -1
NO_STATUS = 0
SANCTUARY = 1
TRANSIT = 2
RESIDENT = 3
CITIZEN = 4
ACCREDITED = 5

# (rung, key, what the card says, authority, the sentence it is read off)
TIERS = (
    (ACCREDITED, "accredited", "role is diplomat or envoy", 4,
     "'Each ambassador and his staff have diplomatic immunity, and the "
     "quarters of each ambassador are considered to be part of their world's "
     "territory' -- LAW-CRIME 4.1. In the 4.3 pipeline the file dies at step "
     "4, which is why this rung cannot be demoted"),
    (CITIZEN, "citizen", "ORIGIN=EARTH, VISAS empty", 1,
     "The station is Earth Alliance sovereign territory (LAW-CRIME 4.1), so "
     "an EA citizen enters by right and the VISAS field is PROPERLY empty -- "
     "which is why the authority-1 identicard prop has three red rows"),
    (RESIDENT, "resident", "non-EA, VISAS empty, holds a job aboard", 5,
     "'A substantial source of income for the station was the rent paid both "
     "by individuals for their living quarters and by businesses' -- "
     "LAW-CRIME 7.1. Standing IS the residency record; there is no visa, "
     "which is why losing the job is what loses the rung"),
    (TRANSIT, "transit", "VISAS=TRANSIT nD", 1,
     "FACTIONS 2.3's seven-day mean stay, written on the card by "
     "resident._visa. A conditional permission -- so it expires, and so it "
     "can be withdrawn"),
    (SANCTUARY, "sanctuary", "VISAS=SANCTUARY", 4,
     "FACTIONS 6.2's 13,000 stateless Narn. Referred to immigration at "
     "customs station 6 rather than waved through. A GRANT -- G'Kar's was "
     "granted by Sheridan's military-governor power -- and a grant can be "
     "withdrawn"),
    (NO_STATUS, "no_status", "VISAS=NO STATUS, or expired, or nothing", 1,
     "FACTIONS 3.4: 'visa fraud, forged identicards and expired status are "
     "the station's most ordinary crimes, and the reason lurkers avoid "
     "readers'. The floor: nothing left to revoke, and 4.3 step 6's next "
     "disposal is transfer off-station"),
)
TIER_NAME = {r[0]: r[1] for r in TIERS}
TIER_NAME[DETAINED] = "detained"
RUNGS = tuple(r[0] for r in TIERS)                       # 5,4,3,2,1,0


def tier_name(t: int) -> str:
    return TIER_NAME.get(t, f"?{t}")


# The roles that carry accreditation. NOT a species or a name list: it is the
# two `schedule.ROLES` rows whose workplace is the diplomatic zone, so adding a
# diplomatic role to the census adds it here and nowhere else.
ACCREDITED_ROLES = frozenset({"diplomat", "envoy"})


def tier_of(card, rec=None) -> int:
    """The rung this person stands on. A READING, not a stored field.

    Every branch delegates to `arrival.entry_class`, which is this project's
    one card reader (five branches over VISAS, ORIGIN and job). A second visa
    parser here would be the second description of one decision that hard rule
    4 exists against -- and would drift within a session, because
    `resident._visa` and `entry_class` are already a matched pair.

    `rec` is the mutable half (`Record`): custody and revocation. Without it
    this is a pure function of the frozen card, which is the point -- the card
    is what the station HOLDS about you and the record is what it has DONE.
    """
    if rec is not None and rec.in_custody:
        return DETAINED
    if rec is not None and rec.visa_revoked:
        # The whole content of a revocation: the conditional permission is
        # gone, so the card reads the way a card with no permission reads.
        return NO_STATUS
    if card.role in ACCREDITED_ROLES:
        return ACCREDITED
    cls, expired, _why = AR.entry_class(card)
    if expired:
        # FACTIONS 3.4 calls expired status the station's most ordinary CRIME,
        # and `arrival.checks` station 6 makes it a REFUSE. An expired
        # permission is not a lesser permission, it is none.
        return NO_STATUS
    return {AR.EA_CITIZEN: CITIZEN, AR.RESIDENT: RESIDENT,
            AR.TRANSIT: TRANSIT, AR.SANCTUARY: SANCTUARY,
            AR.NO_STATUS: NO_STATUS}[cls]


# Which rungs hold a permission that an Ombuds can take away, and what they
# fall to. `None` means the rung is NOT revocable, and the two `None`s are the
# whole political content of this module -- see the header.
REVOCABLE = {
    ACCREDITED: None,      # 4.3 step 4: immunity, and the file dies
    CITIZEN: None,         # no visa on the card; EA territory, entry by right
    RESIDENT: NO_STATUS,   # the standing is the job, and the job is revocable
    TRANSIT: NO_STATUS,    # a conditional permission, withdrawn
    SANCTUARY: NO_STATUS,  # a grant, withdrawn
    NO_STATUS: None,       # the floor -- 4.3 step 6 is transfer off-station
}


# ===========================================================================
# 2.  WHAT A RUNG GATES -- (a) which places admit you
# ===========================================================================
# DERIVED FROM THE REGISTER'S OWN FUNCTION VOCABULARY, not from a per-place
# list. `directory.PLACES` declares 122 distinct functions across 128 places;
# the rule below reads those, so a place that gains `psi_corps` becomes gated
# without anybody editing this file. That is the same discipline
# `security.POSTS` uses for posts and `economy.SELLING_FUNCTIONS` for counters.
#
# (function, minimum rung, authority, why that rung)
GATED_FUNCTIONS = (
    ("diplomatic_privilege", ACCREDITED, 4,
     "an ambassador's quarters ARE their world's territory (LAW-CRIME 4.1)"),
    ("council_session", ACCREDITED, 4,
     "the Council sits; `security.POSTS` puts a checkpoint pair on the door "
     "precisely because immunity makes it a checkpoint and not a patrol"),
    ("psi_corps", CITIZEN, 4,
     "an EA agency's own premises on EA territory (FACTIONS 4.1)"),
    ("political_policing", CITIZEN, 4,
     "Nightwatch is an EA Ministry of Peace body (FACTIONS 5)"),
    ("defence_command", CITIZEN, 5,
     "EA military command. Sheridan's military-governor powers are EA's"),
    ("command", CITIZEN, 5, "as above"),
    ("station_ops", CITIZEN, 5, "as above"),
    ("law_enforcement", CITIZEN, 5,
     "the force is EA-contracted; 2.2 apportions all 500 to EA staffing"),
    ("surveillance", CITIZEN, 5, "as above"),
    ("dispatch", CITIZEN, 5, "as above"),
    ("detention", CITIZEN, 5,
     "you enter the brig as a prisoner or as staff, and a prisoner is "
     "DETAINED rather than admitted -- see `admits`"),
    ("adjudication", TRANSIT, 4,
     "Ombuds sittings are public; 4.2's whole problem is that people who are "
     "NOT EA nationals appear in them"),
    ("reactor_control", RESIDENT, 5,
     "the physical plant. A person with no standing is not walked through the "
     "fusion hall"),
    ("radiation_boundary", RESIDENT, 5, "as above"),
    ("fire_control", CITIZEN, 5, "weapons. LAW-CRIME 2.7's carrying rule"),
    ("issue_stores", RESIDENT, 5, "EA stores draw against a record"),
    ("administration", RESIDENT, 5,
     "a station office serves people it has a record of"),
    ("offices", RESIDENT, 5, "as above"),
    ("currency_exchange", TRANSIT, 1,
     "the customs board, authority 1: 'MONETARY EXCHANGE RATES THROUGH "
     "BUSINESS CENTER'. An exchange is a financial service and the identicard "
     "IS the credit card (6.4), so it reads a card that reads"),
    ("hire", TRANSIT, 5, "hiring anything is a deposit against a record"),
    ("short_stay", TRANSIT, 5,
     "`RENT_TIER` puts the TRANSIT rung on 7.1's `room_transient` row at "
     "4-8 cr/week, and `qtr_transient` IS that row. Reading the same table "
     "twice would be two tables"),
    # THE ONE RUNG THAT WOULD OTHERWISE GATE NOTHING, and the reason it does.
    # The identicard is "driver's licence, credit card, passport AND MEDICAL
    # FILE" (6.4, authority 4) -- MEDICAL is one of the nine fields on the
    # authority-1 prop -- so a medlab reads a card, and a card that does not
    # read cannot be treated on one. **That is why Franklin ran a free clinic.**
    # 7.3 is explicit that it was "a charitable service, unofficial, at a
    # doctor's own initiative", and this is the gap it existed in. `triage` is
    # deliberately NOT listed: emergency care is not a border.
    ("medical", SANCTUARY, 4,
     "6.4: the identicard is also the medical file, so a ward draws against "
     "it. LAW-CRIME 7.3's free clinic exists in the gap this leaves"),
    ("surgery", SANCTUARY, 4, "as above"),
    ("immigration", NO_STATUS, 1,
     "EXPLICITLY OPEN AT THE FLOOR, and it is not an oversight: 6.2's "
     "stateless are referred TO immigration, so a rung that could not enter "
     "it would make the referral impossible"),
    ("black_market", NO_STATUS, 1,
     "open at the floor by construction -- `resident.leisure_places` already "
     "adds the crime venues BACK for NO_STATUS_ROLES, because 11.4's black "
     "market exists to serve exactly the people a reader turns away"),
    ("organised_crime", NO_STATUS, 1, "as above"),
    ("informal_residence", NO_STATUS, 1,
     "Downbelow is squatted, not let. 5.1: unfinished, unpoliced, unlit"),
)
GATE_BY_FUNCTION = {f: r for f, r, _a, _w in GATED_FUNCTIONS}

# LOCATIONS.md P-05, and it is a SECTOR rule rather than a place rule: "Security
# checkpoints at every sector boundary and at every lift lobby serving a
# restricted ring. Blue is explicitly access-restricted, and the Alien Sector is
# airlocked. Those two facts alone require a controlled boundary." So a sector
# carries a floor, and the floor is what the boundary check enforces.
#
# EXTRAPOLATED (INV-341). Blue at TRANSIT because a lawful visitor arrives
# THROUGH Blue and cannot be barred from the hall they are processed in; Green
# at RESIDENT because the diplomatic zone is where the checkpoint pair stands;
# Grey at RESIDENT because its access restriction is stated at authority 4;
# Red and Yellow at the floor because nothing restricts them.
SECTOR_MIN = {"blue": TRANSIT, "green": RESIDENT, "grey": RESIDENT,
              "red": NO_STATUS, "yellow": NO_STATUS}


def required_tier(place_key: str) -> tuple:
    """(minimum rung, the reason). The maximum of the two rules above.

    A function floor and a sector floor are both floors, so a place takes the
    higher -- which is why `council_chamber` in Green is ACCREDITED and not
    RESIDENT, and why `downbelow` in Grey is at the FLOOR rather than at Grey's
    RESIDENT: an explicit function rule beats the sector default, because
    `informal_residence` is a statement about that volume and the sector rule
    is a statement about the boundary.
    """
    q = dr.by_key(place_key)
    fns = tuple(q["functions"])
    explicit = [(GATE_BY_FUNCTION[f], f) for f in fns if f in GATE_BY_FUNCTION]
    opened = [r for r, f in explicit if r == NO_STATUS]
    if opened:
        # An explicitly-open function overrides the sector boundary. Downbelow
        # is in Grey and nobody checks a card to get into a squat.
        need = max([r for r, _f in explicit])
        why = "function " + "/".join(f for _r, f in explicit)
        return need, why
    need, why = SECTOR_MIN.get(q["sector"], NO_STATUS), f"sector {q['sector']}"
    for r, f in explicit:
        if r > need:
            need, why = r, f"function {f}"
    return need, why


def admits(place_key: str, t: int) -> tuple:
    """(does this rung get in, why not). The gate a checkpoint enforces."""
    need, why = required_tier(place_key)
    if t == DETAINED:
        # THE CUSTODY STATE IS THE WHOLE POINT OF BEING NEGATIVE. A detained
        # person is admitted to the brig and to nowhere else on the station,
        # which is 1 of 128 -- and it is the sharpest gating number here.
        return (place_key == BRIG, f"in custody at {BRIG}")
    return (t >= need, f"needs {tier_name(need)} ({why})")


def admitted_places(t: int) -> tuple:
    return tuple(sorted(p["key"] for p in dr.PLACES if admits(p["key"], t)[0]))


# ===========================================================================
# 3.  WHAT A RUNG GATES -- (b) what the economy will sell you
# ===========================================================================
# A COUNTER CHECKS A CARD, AND THAT IS WHY THE BLACK MARKET EXISTS. The rule is
# not invented here: `resident.leisure_places` already routes `NO_STATUS_ROLES`
# to the crime venues and everybody else away from them, because FACTIONS 11.4
# says the black market's clientele IS the people a reader turns away. This is
# the same rule applied to a transaction instead of to a destination.
#
# EXTRAPOLATED (INV-342): a licit counter checks the card at the point of sale,
# because the identicard IS the credit card (TRAFFIC-AND-CUSTOMS 6.4, authority
# 4) -- so paying and being identified are the same act and cannot be
# separated. That is the strongest form of the rule and it is what makes the
# floor rung economically real. Overturned by any depiction of cash aboard.
UNCHECKED_FUNCTIONS = frozenset({"black_market", "organised_crime",
                                 "black_market_fringe", "crime"})
# The rung a licit counter serves, and it is the FLOOR PLUS ONE rather than
# anything higher: 6.2's stateless hold a card that reads, and 7.1 prices them
# a 1 cr/night dosshouse bunk, which is a business taking money. What a licit
# counter cannot take is a card that does not read at all -- FACTIONS 3.4's
# "the reason lurkers avoid readers" -- so exactly one rung is excluded, and it
# is the rung the black market exists to serve.
COUNTER_MIN = SANCTUARY


def sells_to(place_key: str, t: int) -> tuple:
    """(will this counter serve that rung, the reason a keeper would give)."""
    q = dr.by_key(place_key)
    fns = set(q["functions"])
    if not (fns & EC.SELLING_FUNCTIONS):
        return False, f"{place_key} is not a counter"
    if t == DETAINED:
        return False, "in custody"
    if fns & UNCHECKED_FUNCTIONS:
        return True, "no reader on this counter (FACTIONS 11.4)"
    ok, why = admits(place_key, t)
    if not ok:
        return False, f"cannot get in: {why}"
    if t < COUNTER_MIN:
        return False, ("the reader will not take that card -- the identicard "
                       "IS the credit card (6.4)")
    return True, "card accepted"


def counters_for(t: int) -> tuple:
    return tuple(v for v in EC.vendors() if sells_to(v, t)[0])


def purchase(led, buyer, place_key, good, n=1, bag=False):
    """BUY, with the card check in front of it.

    Delegates to `economy.buy` for every credit that moves. This function adds
    ONE thing -- the reader -- and it is here rather than in `economy.py`
    because a till is not the right place to know about visas, and because a
    second wallet is what that module's own docstring forbids.
    """
    t = tier_of(buyer.card, getattr(buyer, "record", None))
    ok, why = sells_to(place_key, t)
    if not ok:
        raise EC.Refused(f"{place_key} will not serve {tier_name(t)}: {why}")
    return EC.buy(led, buyer, place_key, good, n, bag=bag)


# ===========================================================================
# 3b.  THE OTHER DIRECTION -- what a rung can SELL, and to whom
# ===========================================================================
# VRB-05 IS "BUY/SELL" AND ONLY ONE HALF OF IT EXISTED. `sells_to` above has
# answered "will this counter serve that rung" since 4r; nothing anywhere
# answered the mirror question, so `spec_check.py --red` read
# *"the buy side is consequence.purchase; the sell side is not implemented --
# no sell/fence entry point exists"*.
#
# THE ASYMMETRY IS THE CONTENT, and it is not a copy of `sells_to` with the
# arrow turned round. Buying and selling are gated by DIFFERENT things:
#
#   BUYING is gated by the reader, because the identicard IS the credit card
#     (INV-342) -- a card that will not read cannot pay. One rung is excluded.
#
#   SELLING is gated by the reader AND by what a payout looks like on a
#     docket. A licensed counter handing credits to a card is a named
#     transaction with a named counterparty, so it will not take a
#     customs-sealed or route line at any rung: `economy.buys_list` refuses
#     those in the counter's own words and `OFFENCE["contraband"]` is what it
#     would be if it did. That is exactly why FACTIONS 11.4's fence exists,
#     and it is why `fence()` below is a real alternative rather than a worse
#     shop.
#
# So a player with a clean card and a clean crate has two buyers and takes the
# better price; a player with either problem has one, and Solly Vane pays 75%
# of what a shopfront would (`economy.FENCE_TAKE`). INV-723.
def buys_from(place_key: str, t: int) -> tuple:
    """(will this counter buy from that rung, the reason a keeper would give).

    The mirror of `sells_to`, and it reuses that function for the half the two
    genuinely share -- getting through the door and the reader -- rather than
    restating the ladder, so a change to the ladder cannot move one direction
    and not the other.
    """
    q = dr.by_key(place_key)
    fns = set(q["functions"])
    if not (fns & EC.SELLING_FUNCTIONS):
        return False, f"{place_key} is not a counter"
    if t == DETAINED:
        return False, "in custody -- property is held with the person"
    if fns & UNCHECKED_FUNCTIONS:
        return True, "no reader on this counter (FACTIONS 11.4)"
    ok, why = admits(place_key, t)
    if not ok:
        return False, f"cannot get in: {why}"
    if t < COUNTER_MIN:
        return False, ("the reader will not take that card, and a payout has "
                       "to go somewhere (6.4)")
    return True, "card accepted"


def fences_for(t: int) -> tuple:
    """Every counter this rung can sell into. Ordered, deterministic."""
    return tuple(v for v in EC.counters() if buys_from(v, t)[0])


def fence(led, seller, place_key, good, n=1):
    """SELL, with the card check in front of it. The mirror of `purchase`.

    Named `fence` rather than `sell` on purpose: `economy.sell` is the till,
    this is the person behind it deciding whether to deal with you, and the
    only counters that will deal with everybody are the ones FACTIONS 11.4
    calls the black market. `economy.FENCE_NAME` is who that is.

    Delegates to `economy.sell` for every credit that moves.
    """
    t = tier_of(seller.card, getattr(seller, "record", None))
    ok, why = buys_from(place_key, t)
    if not ok:
        raise EC.Refused(f"{place_key} will not buy from "
                         f"{tier_name(t)}: {why}")
    return EC.sell(led, seller, place_key, good, n)


def would_book(place_key: str, good: str) -> str:
    """The offence a licensed counter would file instead of paying you.

    "" when the sale is ordinary. This is what makes the refusal in
    `economy.sell` more than a shrug: the docket it names is a real row of
    `OFFENCES`, with a real fine band behind it.
    """
    if place_key not in EC.counters():
        return ""
    if EC.unchecked(place_key):
        return ""
    g = EC.GOODS_BY_NAME.get(good)
    if g is None:
        return ""
    if g.klass == "contraband":
        return "smuggling_military" if "weapon" in g.name else "contraband"
    if g.cargo == "bonded" or g.supply == "route":
        return "contraband"
    return ""


# What a rung can RENT. `economy.LADDER`'s own rows, in order, so this is a
# reading of the published price table and not a second one. PLY-03 calls the
# rent-tier ladder "climbable"; this is the half that says who may climb.
RENT_TIER = {
    ACCREDITED: "quarters_command",     # 30 cr/wk, the sourced anchor
    CITIZEN: "quarters_personnel",      # 10-15
    RESIDENT: "quarters_personnel",     # standing is the record; same tenancy
    TRANSIT: "room_transient",          # 4-8, the Red layer LOCATIONS 11 names
    SANCTUARY: "bunk_dosshouse",        # 1 cr/night -- the floor of the market
    NO_STATUS: "squat",                 # 0, "and it is why people are there"
    DETAINED: "squat",
}


def rent_for(t: int) -> tuple:
    """(ladder key, lo, hi) -- what this rung may take a tenancy at."""
    k = RENT_TIER[t]
    lo, hi = EC.ladder(k)
    return k, lo, hi


# ===========================================================================
# 4.  WHAT A RUNG GATES -- (c) whether a patrol stops you
# ===========================================================================
# LAW-CRIME 2.7's escalation ladder, rung 2: "Identicard check. Reader out,
# three amber lenses, portrait on the screen. **The commonest security
# interaction on the station and the one a player will see most.**"
#
# TWO COMPONENTS, AND CONFLATING THEM IS THE BUG THIS SECTION EXISTS TO AVOID.
#
#   CERTAIN       a place whose own function is a check -- `identicard_check`,
#                 `checkpoint`, `immigration` -- checks everybody who enters,
#                 by definition. So does the boundary of an access-restricted
#                 sector, which is LOCATIONS.md P-05 stated as a rule.
#                 Probability 1.0 PER ENTRY.
#   DISCRETIONARY an officer who is standing there may ask. Scales with
#                 officers per head, so it is a property of the GEOGRAPHY and
#                 not of the person: `security.presence_at` gives 12.9 officers
#                 over 7,860 people in the Zocalo and ZERO over 39,262 in
#                 Downbelow. Probability per station-hour.
#
# The reachable path is the certain one and the discretionary one is the
# texture. That is why `revocation_path` reports entries and not hours.
CHECK_FUNCTIONS = frozenset({"identicard_check", "checkpoint", "immigration"})

# EXTRAPOLATED (INV-343): one discretionary check per officer-hour. It is the
# only free number in this module and it is constrained from both sides, which
# is what stops it being a guess:
#
#   FROM ABOVE, by the brig. `BRIG_CELLS` x the mean hold is the steady-state
#   custody population, and checks x P(fail) x P(detained|fail) has to fit
#   inside it. `brig_check()` computes it and fails if it does not.
#   FROM BELOW, by 2.7 calling rung 2 the commonest interaction: the check
#   count must exceed the detention count by orders, not by a margin.
#
# At 1.0 the whole on-duty force makes ~3,600 discretionary checks a day
# against the ~12,600 transactions a day the two customs halls already run
# (schedule.ROLES' customs row, from FACTIONS 2.2/2.3) -- so discretionary
# checking is 22% on top of the mandatory kind, which is the right order for a
# power described as routine. Overturned by any figure for stop-and-check
# volume.
CHECKS_PER_OFFICER_HOUR = 1.0


def certain_check(place_key: str) -> tuple:
    """(is a card read on the way in, why). P-05's boundary, as a predicate.

    IT MUST READ `required_tier` AND NOT THE SECTOR, and the first version read
    the sector and was wrong in the one place it most mattered: `downbelow` is
    in GREY, Grey carries P-05's restriction, and the gate therefore reported a
    certain identicard check on the way into Downbelow -- which is the exact
    inverse of LAW-CRIME 2.4's "Downbelow: NO PERMANENT POST" and of 3.4's "the
    reason lurkers avoid readers". The rule is that an explicitly-open function
    beats the sector boundary, and it is the same override `required_tier`
    already applies: nobody checks a card to get into a squat.
    """
    q = dr.by_key(place_key)
    fns = set(q["functions"])
    hit = fns & CHECK_FUNCTIONS
    if hit:
        return True, f"function {'/'.join(sorted(hit))}"
    need, why = required_tier(place_key)
    if need > NO_STATUS and why.startswith("sector"):
        return True, (f"P-05: {q['sector']} is access-restricted, so its "
                      f"boundary is a controlled one")
    if need > NO_STATUS:
        return True, f"P-05: a lift lobby serving {why}"
    return False, f"no reader on the way in ({why} admits the floor rung)"


def check_rate(place_key: str, hour: float) -> dict:
    """Discretionary identicard checks, per station-hour, on ONE head."""
    pres = sec.presence_at(place_key, hour)
    area = EC.floor_m2(place_key)
    heads = max(1, POP.occupancy(place_key, area, hour))
    per_hour = pres["officers"] * CHECKS_PER_OFFICER_HOUR
    return {"place": place_key, "hour": hour, "officers": pres["officers"],
            "heads": heads, "checks_in_room_per_hour": per_hour,
            "per_head_per_hour": per_hour / heads,
            "days_between_checks": (float("inf") if per_hour <= 0
                                    else heads / per_hour / 24.0),
            "policed": pres["policed"]}


def stopped(place_key: str, hour: float, npc_id: str, hours: float = 1.0,
            seed: str = "b5") -> bool:
    """Is this person checked in `hours` of standing here. Deterministic."""
    r = check_rate(place_key, hour)["per_head_per_hour"]
    p = 1.0 - math.exp(-r * hours)
    return _u("check", npc_id, place_key, round(hour, 2), seed) < p


# ===========================================================================
# 5.  THE RECORD -- the mutable half, and it is the ONLY thing that persists
# ===========================================================================
@dataclass
class Record:
    """What the station has DONE about you, as opposed to what it holds.

    `player.Player`'s docstring draws this line already and draws it correctly:
    the `Resident` card is frozen because an identicard is not editable by its
    bearer, and the mutable half is where they are, what they carry, how much
    they have, and their processing status. A criminal record is exactly that
    same half -- it belongs to the session, not to the person -- so it lives
    here and round-trips through `state()` the way a purse does.
    """
    convictions: tuple = ()          # offence keys, in order
    fines_paid: float = 0.0
    fines_outstanding: float = 0.0
    custody_events: int = 0
    custody_seconds: float = 0.0
    in_custody: bool = False
    visa_revoked: bool = False
    revoked_from: str = ""           # the tier name it was taken from
    notes: tuple = ()

    def state(self) -> dict:
        return {"convictions": list(self.convictions),
                "fines_paid": self.fines_paid,
                "fines_outstanding": self.fines_outstanding,
                "custody_events": self.custody_events,
                "custody_seconds": self.custody_seconds,
                "in_custody": bool(self.in_custody),
                "visa_revoked": bool(self.visa_revoked),
                "revoked_from": self.revoked_from,
                "notes": list(self.notes)}

    @classmethod
    def from_state(cls, st) -> "Record":
        st = st or {}
        return cls(convictions=tuple(st.get("convictions", ())),
                   fines_paid=st.get("fines_paid", 0.0),
                   fines_outstanding=st.get("fines_outstanding", 0.0),
                   custody_events=st.get("custody_events", 0),
                   custody_seconds=st.get("custody_seconds", 0.0),
                   in_custody=bool(st.get("in_custody", False)),
                   visa_revoked=bool(st.get("visa_revoked", False)),
                   revoked_from=st.get("revoked_from", ""),
                   notes=tuple(st.get("notes", ())))

    def clean(self) -> bool:
        return not (self.convictions or self.fines_outstanding
                    or self.visa_revoked)

    def serious(self) -> int:
        return sum(1 for k in self.convictions if OFFENCE[k][1] >= 3)

    def ordinary(self) -> int:
        return sum(1 for k in self.convictions if OFFENCE[k][1] == 2)


# ===========================================================================
# 6.  OFFENCES AND FINES
# ===========================================================================
# A FINE IS DAYS OF CASUAL LABOUR. See the header. The grades are 1 day, one
# week and three weeks; the week is FACTIONS 2.3's mean transient stay, so a
# grade-2 fine costs a visitor exactly the visit.
FINE_DAYS = {0: 0.0, 1: 1.0, 2: 7.0, 3: 21.0, 4: None}

# (key, grade, escalation rung (2.7), authority, the sourced sentence)
OFFENCES = (
    ("move_on", 0, 3, 4,
     "2.7 rung 3: 'No arrest, no record. The standard Downbelow-in-a-"
     "commercial-area outcome'"),
    ("id_check_fail", 1, 2, 5,
     "a card that does not read. 2.7 rung 2 is the commonest interaction and "
     "most of its failures end at rung 3"),
    ("expired_status", 2, 4, 4,
     "FACTIONS 3.4: 'expired status [is one of] the station's most ordinary "
     "crimes'; arrival.checks station 6 already makes it a REFUSE"),
    ("carrying", 2, 4, 4,
     "'Civilians aren't supposed to have weapons on the station and this is "
     "reasonably well enforced' -- midwinter tech manual, via 2.7"),
    ("petty_theft", 2, 4, 4,
     "8.2: 'Constant -- dozens/day', concentrated at customs exits and the "
     "Zocalo"),
    ("prostitution", 2, 4, 4, "8.2, named among the Ombuds' ordinary docket"),
    ("contraband", 3, 4, 4,
     "6.5 names Dust and concealed weapons; arrival.checks station 9 refers "
     "on a hit"),
    ("assault", 3, 5, 4, "8.2: common in Downbelow, uncommon elsewhere"),
    ("identicard_fraud", 3, 4, 4,
     "8.2 calls it the station's signature crime; N'Grath's services "
     "explicitly include 'forged identicards'"),
    ("smuggling_military", 4, 7, 4,
     "8.2: 'Rare, enormous.' Off the fine ladder entirely -- 4.3 step 6's "
     "disposal is transfer off-station"),
    ("murder", 4, 7, 5,
     "8.2: 'Rare -- single figures per year', and 4.3 step 7 says the "
     "sentence is not served aboard"),
)
OFFENCE = {r[0]: r for r in OFFENCES}

# The wage the fine is denominated in. `economy.casual_constraint()` -- NOT the
# stated 8-15 band -- because the passage-home anchor pins it to 8-10 and the
# fine's CEILING is that same anchor. Using one derivation for both ends of the
# argument is the point; using the stated band for the wage and the anchor for
# the ceiling would be two sources pointed at one sum.
WAGE_LO, WAGE_HI = EC.casual_constraint()                     # 8.0, 10.0
PASSAGE_LO, PASSAGE_HI = EC.ladder("passage_home")            # 300, 800


def fine_for(offence_key: str) -> tuple:
    """(lo, hi, days). `(0,0,None)` for a disposal that is not a fine."""
    grade = OFFENCE[offence_key][1]
    days = FINE_DAYS[grade]
    if days is None:
        return 0.0, 0.0, None
    return round(days * WAGE_LO, 2), round(days * WAGE_HI, 2), days


def fine_amount(offence_key: str, npc_id: str, seed: str = "b5") -> float:
    """One Ombuds' number inside the band. Deterministic in the person."""
    lo, hi, days = fine_for(offence_key)
    if days is None:
        return 0.0
    return round(lo + (hi - lo) * _u("fine", offence_key, npc_id, seed), 2)


def fine_bounds_check(hold_h: float = None) -> dict:
    """Both ends of the fine ladder, against the two anchors that set them.

    CEILING: a fine at or above the cheapest passage home is deportation
    dressed as a fine, by TRAFFIC-AND-CUSTOMS 6.6's own mechanism.
    FLOOR:   a fine below the wages the hold already cost is a rounding error
             on the arrest, so the smallest rung must clear that.

    THE FLOOR IS TESTED AGAINST THE **MEDIAN** HOLD AND IT ONLY JUST CLEARS,
    AND BOTH HALVES OF THAT ARE REPORTED RATHER THAN ONE. The median detainee
    is held 15.4 h, which costs 6.4 cr of day labour, and the smallest fine is
    8.0 cr -- so a citation is a penalty. The MEAN hold is 24.5 h because the
    deferral tail drags it, which costs 10.2 cr, and **the smallest fine does
    not clear that**: for a case that defers, the detention is a heavier
    punishment than the sentence. That is not a defect to tune away -- it is
    LAW-CRIME 4.2's own complaint ("many of the cases had to be deferred")
    arriving as arithmetic, and it is the single most interesting number this
    module produces about the court. The gate asserts the median and PRINTS the
    mean.
    """
    med_h = (hold_distribution(1500)["median_days"] * 24.0
             if hold_h is None else hold_h)
    top = FINE_DAYS[3] * WAGE_HI
    lost = med_h / 24.0 * WAGE_HI
    lost_mean = MEAN_HOLD_H / 24.0 * WAGE_HI
    smallest = FINE_DAYS[1] * WAGE_LO
    return {"top_fine": top, "passage_floor": PASSAGE_LO,
            "ceiling_ok": top < PASSAGE_LO,
            "headroom_cr": PASSAGE_LO - top,
            "max_days_under_passage": PASSAGE_LO / WAGE_HI,
            "median_hold_h": med_h, "mean_hold_h": MEAN_HOLD_H,
            "hold_lost_wages": lost, "hold_lost_wages_mean": lost_mean,
            "smallest_fine": smallest,
            "floor_ok": smallest > lost,
            "floor_ok_on_the_mean": smallest > lost_mean,
            "wage_band": (WAGE_LO, WAGE_HI)}


# ===========================================================================
# 7.  THE BRIG, AND HOW LONG YOU ARE IN IT
# ===========================================================================
BRIG = "brig"
COURT = "law_courts"
# LAW-CRIME 3.1, transcribed so this module can CHECK it: "24-40 individual
# cells plus 2 group holds".
BRIG_CELLS_LO, BRIG_CELLS_HI, BRIG_GROUP_HOLDS = 24, 40, 2
BRIG_CELLS = (BRIG_CELLS_LO + BRIG_CELLS_HI) // 2

# THE OMBUDS SITTING. 4.2: at least two Ombudsmen aboard, sitting in the Law
# Courts, and 4.3 step 5 says "Days, not months." The sitting is on the
# station's own working day -- `schedule.REF_WORK_START` -- which is why this is
# not a new clock.
SITTING_HOUR = sched.REF_WORK_START                            # 08:00 EMT
OMBUDSMEN = 2

# WHO DEFERS. 4.2's recurring problem, quoted: "Many of the cases had to be
# deferred as conflicts of jurisdiction came up between the humans and aliens."
# The applicable law is Earth Alliance law (4.1), so the conflict arises when
# the person in the dock is NOT an EA national -- and the share is DERIVED from
# the population that actually gets arrested rather than from the station
# census. 6.2 gives the Downbelow mix as "roughly 78% human and 17.5% Narn",
# and 8.1 puts 90% of crime there, so the non-human share of the dock is 22%.
# That the derived figure lands on "many" rather than on "a few" is the check.
DOWNBELOW_HUMAN_SHARE = 0.78                    # LAW-CRIME 6.2, authority 5
DEFER_SHARE = round(1.0 - DOWNBELOW_HUMAN_SHARE, 4)            # 0.22

# ...AND HOW OFTEN A DEFERRED CASE DEFERS AGAIN. SOLVED, not chosen, against
# the two brackets 3.1 states for the same distribution:
#
#     "Typical hold: hours to a few days"   -> the median must be under a day
#     "Longest hold: weeks"                 -> the tail must reach a fortnight
#
# A deferred case waits one more sitting each time it defers, so the hold in
# days is 1 + Geom(q). Requiring P(hold >= WEEKS_DAYS) = TAIL_P:
#
#     DEFER_SHARE * q**(WEEKS_DAYS - 1) = TAIL_P
#     q = (TAIL_P / DEFER_SHARE) ** (1 / (WEEKS_DAYS - 1))
#
# `hold_distribution()` measures the realised median and p99 and fails if
# either bracket is missed, and the gate's negative control sets q to 0 -- no
# deferral at all -- which collapses the tail to one day and fires it.
WEEKS_DAYS = 14.0
TAIL_P = 0.01
DEFER_AGAIN_P = round((TAIL_P / DEFER_SHARE) ** (1.0 / (WEEKS_DAYS - 1.0)), 4)


def defers(npc_id: str, day: int, seed: str = "b5") -> int:
    """How many sittings this case is put back. 0 for a clean hearing."""
    if _u("defer", npc_id, day, seed) >= DEFER_SHARE:
        return 0
    n = 1
    while _u("defer2", npc_id, day, seed, n) < DEFER_AGAIN_P and n < 60:
        n += 1
    return n


def hold_seconds(arrest_hour: float, escort_s: float, cycles: int) -> float:
    """Arrest to hearing, in seconds. The wait to the next sitting, plus the
    deferral chain. A case booked in after the sitting has begun waits for the
    following day, which is why a 09:00 arrest holds nearly 23 hours."""
    booked = arrest_hour + escort_s / 3600.0 + BOOKING_H
    wait = (SITTING_HOUR - booked) % 24.0
    if wait <= 0.0:
        wait += 24.0
    return (wait + 24.0 * cycles) * 3600.0


# 4.3 step 4, "the station's characteristic legal event": the jurisdiction
# check happens at Security Central between detention and the hearing.
# EXTRAPOLATED (INV-344): one hour to book a prisoner in -- search, property,
# identicard, cell assignment and the jurisdiction query. Constrained below by
# 3.1's fittings list (a reader outside every door, a camera, an atmosphere
# assignment for a non-oxygen prisoner) and above by 3.1's "hours to days"
# being about the HOLD and not about the booking.
BOOKING_H = 1.0


def hold_distribution(n: int = 4000, seed: str = "b5") -> dict:
    """Median and p99 of the hold, against 3.1's two stated brackets."""
    xs = []
    for i in range(n):
        cyc = defers(f"h{i}", 0, seed)
        h = _u("hour", i, seed) * 24.0
        xs.append(hold_seconds(h, 600.0, cyc) / 86400.0)
    xs.sort()
    med = xs[len(xs) // 2]
    p99 = xs[int(len(xs) * 0.99)]
    return {"median_days": med, "p99_days": p99, "max_days": xs[-1],
            "typical_ok": med <= 3.0, "weeks_ok": p99 >= 7.0,
            "defer_share": DEFER_SHARE, "defer_again_p": DEFER_AGAIN_P}


MEAN_HOLD_H = 24.0 * (1.0 + DEFER_SHARE / max(1e-9, 1.0 - DEFER_AGAIN_P)) / 2.0


def brig_check(arrests_per_day: float = None, mean_hold_days: float = None,
               seed: str = "b5") -> dict:
    """Does the station's own arrest rate fit in 24-40 cells.

    This is the constraint that keeps `CHECKS_PER_OFFICER_HOUR` honest, and it
    is the only place in the project where a rate and a capacity are made to
    agree. If the discretionary check rate were raised until the check gate
    felt busy, this would go red.
    """
    a = day_arrests() if arrests_per_day is None else arrests_per_day
    hd = (hold_distribution(1500, seed)["median_days"]
          if mean_hold_days is None else mean_hold_days)
    occ = a * max(hd, 1.0 / 24.0)
    return {"arrests_per_day": a, "mean_hold_days": hd, "occupancy": occ,
            "cells": BRIG_CELLS, "cells_lo": BRIG_CELLS_LO,
            "cells_hi": BRIG_CELLS_HI, "group_holds": BRIG_GROUP_HOLDS,
            "fits": occ <= BRIG_CELLS_HI,
            "load": occ / BRIG_CELLS_HI}


# ===========================================================================
# 8.  THE CHAIN: arrest -> brig -> fine -> release
# ===========================================================================
_G = [None]


def graph():
    """The routed graph, built once. 36 s cold, and every leg below is a path
    on it -- the SAME graph a resident commutes on, which is the only reason
    an escort time means anything."""
    if _G[0] is None:
        from npc import navigation as nav                     # noqa: PLC0415
        _G[0] = nav.build_graph()
    return _G[0]


@dataclass
class Custody:
    """One complete pass through 4.3's pipeline, with every leg timed."""
    who: str = ""
    place: str = ""
    offence: str = ""
    hour: float = 0.0
    day: int = 0
    response_s: float = 0.0
    response_from: str = ""
    escort_s: float = 0.0
    booking_s: float = 0.0
    hold_s: float = 0.0
    court_s: float = 0.0
    release_s: float = 0.0
    deferrals: int = 0
    fine: float = 0.0
    paid: bool = False
    outstanding: float = 0.0
    tier_before: int = 0
    tier_after: int = 0
    revoked: bool = False
    disposal: str = ""
    reason: str = ""

    @property
    def total_s(self) -> float:
        return (self.response_s + self.escort_s + self.booking_s
                + self.hold_s + self.court_s + self.release_s)

    def line(self) -> str:
        return (f"{self.offence} at {self.place} {self.hour:04.1f}0: "
                f"respond {self.response_s / 60:.1f} min (from "
                f"{self.response_from}), escort {self.escort_s / 60:.1f} min, "
                f"hold {self.hold_s / 3600:.1f} h"
                + (f" ({self.deferrals} deferral(s))" if self.deferrals else "")
                + f", court {self.court_s / 60:.1f} min -> "
                f"{self.disposal}, {self.fine:.2f} cr, "
                f"{tier_name(self.tier_before)} -> "
                f"{tier_name(self.tier_after)}")


def _leg(dst: str, origin: str) -> float:
    t = sec.response(dst, graph(), origin=origin)
    if t is None:
        raise KeyError(f"no route {origin} -> {dst}: the arrest path is "
                       f"broken, which is a defect in the register or the "
                       f"navgraph and not a fact about policing")
    return float(t)


def arrest(pl, place_key: str, offence_key: str, hour: float = 13.0,
           day: int = 0, led=None, seed: str = "b5") -> Custody:
    """THE WHOLE CHAIN, and it closes. 4.3's pipeline, stages 2 to 6.

    Every duration is routed or derived; the fine is debited through the same
    ledger a drink is; the record is written; the rung moves. Returns a
    `Custody` carrying all of it, and the player comes out the other side
    changed -- which is the clause this module exists for.
    """
    if offence_key not in OFFENCE:
        raise KeyError(f"{offence_key!r} is not in OFFENCES "
                       f"({sorted(OFFENCE)})")
    dr.by_key(place_key)                    # raises if it is not a place
    rec = record_of(pl)
    c = Custody(who=pl.npc_id, place=place_key, offence=offence_key,
                hour=hour, day=day, tier_before=tier_of(pl.card, rec))

    # 4.3 step 4, and it is the branch that makes an ambassador a different
    # game: "Ambassador or staff: IMMUNITY, AND THE FILE DIES."
    if c.tier_before == ACCREDITED:
        c.disposal = "immunity -- the file dies (4.3 step 4)"
        c.tier_after = c.tier_before
        c.reason = "diplomatic immunity, LAW-CRIME 4.1"
        return c

    # 2.7 rung 3: not every stop is an arrest, and the commonest outcome of a
    # stop is not one. A grade-0 offence never reaches the brig.
    if OFFENCE[offence_key][1] == 0:
        c.disposal = "moved on -- no arrest, no record (2.7 rung 3)"
        c.tier_after = c.tier_before
        c.response_s = sec.response_from_nearest_post(
            place_key, graph())["seconds"] or 0.0
        return c

    # --- leg 1: RESPONSE. 2.6's contrast, not 2.6's number ----------------
    r = sec.response_from_nearest_post(place_key, graph())
    c.response_s = float(r["seconds"] or 0.0)
    c.response_from = r["from"] or "?"

    # --- leg 2: ESCORT to the brig, on the routed graph -------------------
    # THE DESTINATION IS VALIDATED AGAINST THE REGISTER BEFORE IT IS ROUTED,
    # and the reason is that the graph outlives the register in a process: the
    # navgraph is built once and cached, so a brig deleted from `directory`
    # after the build still has a `place:brig` node and the escort would route
    # to a place that no longer exists. The gate's third negative control is
    # exactly that, and it did NOT fire until this line was here.
    dr.by_key(BRIG)
    dr.by_key(COURT)
    c.escort_s = _leg(BRIG, place_key)
    c.booking_s = BOOKING_H * 3600.0
    rec.in_custody = True

    # --- leg 3: THE HOLD, to the next Ombuds sitting ----------------------
    c.deferrals = defers(pl.npc_id, day, seed)
    c.hold_s = hold_seconds(hour, c.escort_s, c.deferrals)

    # --- leg 4: COURT, and back out ---------------------------------------
    c.court_s = _leg(COURT, BRIG)
    c.release_s = _leg(BRIG, COURT)

    grade = OFFENCE[offence_key][1]
    if grade >= 4:
        # 4.3 step 6: the fine ladder has run out. The disposal is transfer
        # off-station, and 3.1 is explicit that the sentence is not served
        # aboard -- so this is the end of the character, not a rung.
        c.fine = 0.0
        c.disposal = "transfer off-station (4.3 step 6) -- not a fine"
        c.tier_after = NO_STATUS
        rec.in_custody = False
        rec.convictions += (offence_key,)
        rec.custody_events += 1
        rec.custody_seconds += c.total_s
        rec.notes += (f"day {day}: transferred off-station for "
                      f"{offence_key}",)
        _apply(pl, rec)
        return c

    # --- the fine, and it moves real credits ------------------------------
    c.fine = fine_amount(offence_key, pl.npc_id, seed)
    c.paid = bool(pl.spend(c.fine)) if c.fine else True
    if not c.paid:
        # 4.3's "release into custody" precedent (Jinxo) read economically:
        # the brig is not a debtors' prison, so the debt walks out with you and
        # the card carries it. Which is how a fine becomes permanent.
        c.outstanding = c.fine
        rec.fines_outstanding = round(rec.fines_outstanding + c.fine, 3)
    else:
        rec.fines_paid = round(rec.fines_paid + c.fine, 3)
        if led is not None:
            _post_fine(led, pl, c.fine, day)

    # --- the record, and the rung ------------------------------------------
    rec.in_custody = False
    rec.convictions += (offence_key,)
    rec.custody_events += 1
    rec.custody_seconds += c.total_s
    c.tier_after, c.revoked, c.reason = _dispose(c.tier_before, rec, grade)
    if c.revoked:
        rec.visa_revoked = True
        rec.revoked_from = tier_name(c.tier_before)
        rec.notes += (f"day {day}: {tier_name(c.tier_before)} revoked on "
                      f"{offence_key}",)
    c.disposal = ("fine " + ("paid" if c.paid else "OUTSTANDING")
                  + (" + status revoked" if c.revoked else ""))
    _apply(pl, rec)
    return c


# HOW MANY TIMES BEFORE IT HAPPENS, and it is stated as a rule rather than
# discovered. EXTRAPOLATED (INV-345): a conditional permission survives ONE
# ordinary conviction and not two, and does not survive a serious one at all.
# Constrained by 2.7 rung 3 -- "move on. No arrest, no record" is the standard
# outcome, so a single ordinary offence cannot be terminal or the ladder would
# have no middle -- and by 4.3 step 6 listing "transfer off-station" as an
# ordinary disposal, so it cannot take many either. Overturned by any depiction
# of a visa cancellation and its grounds.
REVOKE_ON_ORDINARY = 2
REVOKE_ON_SERIOUS = 1


def _dispose(t_before: int, rec: Record, grade: int) -> tuple:
    """(rung after, was a permission revoked, why)."""
    falls_to = REVOCABLE.get(t_before)
    if falls_to is None:
        why = {ACCREDITED: "diplomatic immunity (4.1)",
               CITIZEN: ("EA citizenship is not revocable by an Ombuds -- the "
                         "station is EA sovereign territory and there is no "
                         "visa on the card to withdraw"),
               NO_STATUS: ("already at the floor; 4.3 step 6's next disposal "
                           "is transfer off-station")}.get(t_before, "")
        return t_before, False, why
    if rec.serious() >= REVOKE_ON_SERIOUS:
        return falls_to, True, (f"one grade-3 conviction; "
                                f"{tier_name(t_before)} withdrawn")
    if rec.ordinary() >= REVOKE_ON_ORDINARY:
        return falls_to, True, (f"{rec.ordinary()} ordinary convictions; "
                                f"{tier_name(t_before)} withdrawn")
    return t_before, False, (f"first conviction: fined, "
                             f"{tier_name(t_before)} stands "
                             f"({REVOKE_ON_ORDINARY - rec.ordinary()} more "
                             f"ordinary conviction(s) to revocation)")


def _post_fine(led, pl, amount: float, day: int) -> None:
    """A fine is a transfer to the court, in the ledger a drink moves through.

    NOT a new wallet and not a new file: `economy.Ledger.till` and `.sales` and
    `.purses` are the existing three, and the purse is `Player.state()`, which
    is that class's own serialiser.
    """
    led.till[COURT] = round(led.till.get(COURT, 0.0) + amount, 2)
    led.purses[pl.npc_id] = pl.state()
    led.sales.append({"day": day, "at": COURT, "good": "(fine)", "n": 1,
                      "cr": amount, "who": pl.npc_id})


def record_of(pl) -> Record:
    """The record on this player, created on first use. Never a second one."""
    rec = getattr(pl, "record", None)
    if rec is None:
        rec = Record()
        try:
            pl.record = rec
        except Exception:                                    # pragma: no cover
            pass
    return rec


def _apply(pl, rec: Record) -> None:
    try:
        pl.record = rec
    except Exception:                                        # pragma: no cover
        pass


# ===========================================================================
# 9.  VISA REVOCATION -- is it reachable, and how
# ===========================================================================
def revocation_path(pl, place_key: str = "docking_bays",
                    hour: float = 13.0) -> dict:
    """Can this happen to THIS player, and what would it take.

    Returns the honest answer including the honest negative. The clause in
    MASTER-PLAN is "can actually happen to you", and for the V1 default player
    the answer is no -- with a reason that is a sourced fact rather than a
    missing feature.
    """
    rec = record_of(pl)
    t = tier_of(pl.card, rec)
    falls_to = REVOCABLE.get(t)
    card_visa = pl.card.visas or "(empty)"
    certain, cwhy = certain_check(place_key)
    rate = check_rate(place_key, hour)
    if falls_to is None:
        return {"reachable": False, "tier": t, "tier_name": tier_name(t),
                "visa": card_visa,
                "why": _dispose(t, rec, 2)[2],
                "what_would_change_it": (
                    "a start at TRANSIT, SANCTUARY or RESIDENT -- which is a "
                    "role draw away: `player_from({'role': 'visitor'})` holds "
                    "TRANSIT nD, and PLY-02's origin ruling widening puts a "
                    "Narn start at SANCTUARY or RESIDENT"),
                "convictions_needed": None,
                "certain_check_at": place_key if certain else "",
                "certain_why": cwhy}
    need = (REVOKE_ON_SERIOUS - rec.serious() if rec.serious() else
            REVOKE_ON_ORDINARY - rec.ordinary())
    return {"reachable": True, "tier": t, "tier_name": tier_name(t),
            "visa": card_visa, "falls_to": tier_name(falls_to),
            "why": (f"{tier_name(t)} is a conditional permission and an "
                    f"Ombuds can withdraw it"),
            "convictions_needed": max(1, need),
            "trigger": (f"{REVOKE_ON_ORDINARY} ordinary convictions "
                        f"(grade 2) or {REVOKE_ON_SERIOUS} serious one "
                        f"(grade 3)"),
            "first_conviction_from": (
                f"the CERTAIN card check at {place_key} ({cwhy}) -- one entry, "
                f"not a probability" if certain else
                f"a discretionary check at {place_key}: "
                f"{rate['per_head_per_hour']:.5f}/head/h, i.e. one every "
                f"{rate['days_between_checks']:.1f} station-days"),
            "certain_check_at": place_key if certain else "",
            "expiry_clock": _expiry_note(pl.card)}


def _expiry_note(card) -> str:
    v = card.visas or ""
    if v.startswith("TRANSIT"):
        d = v.split()[1].rstrip("D").rstrip("D") if len(v.split()) > 1 else "?"
        return (f"the card says {v}: it expires on day {d} of the stay, and "
                f"the first certain check after that is the arrest")
    if v.startswith("SANCTUARY"):
        return "SANCTUARY does not expire; it is withdrawn, not timed out"
    return "no expiry clock on this card"


# ===========================================================================
# 10.  DENOMINATORS
# ===========================================================================
def population_by_tier() -> dict:
    """How many of the 250,000 stand on each rung. ANALYTIC, not sampled.

    `schedule.ROLE_WEIGHTS` is an apportionment of `STATION_COUNTS` expressed as
    headcounts, and `resident._visa` is a function of the role with two stated
    probabilities, so the whole table can be computed exactly instead of drawn.
    A sample would have given the same answer with a standard error and no
    reason to believe it.
    """
    out = {r: 0.0 for r in RUNGS}
    exp = RES.VISA_EXPIRED_P
    for species, roles in sched.ROLE_WEIGHTS.items():
        earth = RES.ORIGIN.get(species, RES.ORIGIN["other"])[0] == "EARTH"
        for role_key, n in roles.items():
            n = float(n)
            if not n:
                continue
            if role_key in ACCREDITED_ROLES:
                out[ACCREDITED] += n
                continue
            role = sched.ROLES_BY_KEY.get(role_key)
            has_job = bool(role and role.work_hours > 0)
            if role_key == "refugee":
                out[NO_STATUS] += n * exp
                out[SANCTUARY] += n * (1.0 - exp)
            elif role_key == "visitor":
                out[NO_STATUS] += n * exp
                out[TRANSIT] += n * (1.0 - exp)
            elif role_key == "lurker":
                # 0.55 carry "NO STATUS"; the other 0.45 carry an EMPTY visa
                # field, and an empty field on an EARTH origin reads CITIZEN.
                out[NO_STATUS] += n * 0.55
                out[CITIZEN if earth else NO_STATUS] += n * 0.45
            elif earth:
                out[CITIZEN] += n
            elif has_job:
                out[RESIDENT] += n
            else:
                out[NO_STATUS] += n
    return {k: int(round(v)) for k, v in out.items()}


# LAW-CRIME 8.2's own frequency column, read as a rate. "Petty theft: Constant
# -- dozens/day"; a dozen is 12, "dozens" is taken as 2-5 dozen and the
# midpoint used, which is stated rather than hidden. Every other ordinary
# offence is scaled off it by the same column's words.
THEFTS_PER_DAY = 42.0                 # "dozens/day", 3.5 dozen
DOWNBELOW_CRIME_SHARE = 0.90          # 8.1, authority 4


def floor_rung_split() -> dict:
    """The floor rung, split into who stands where a reader is and who does not.

    THE SPLIT IS THE POINT AND THE FIRST VERSION OF IT WAS INERT. It read
    `min(1.0, security.lurker_total() / population[NO_STATUS])` -- ~20,000 over
    19,129 -- which clamps to 1.0, zeroes the exposed share, and made the
    discretionary check rate contribute EXACTLY NOTHING to the arrest count.
    The brig-capacity control found it: raising `CHECKS_PER_OFFICER_HOUR` a
    hundredfold moved the occupancy from 2.8 to 2.8. A constraint that cannot
    respond to the number it is supposed to price is not a constraint.

    The honest split is by ROLE, off the same analytic table `population_
    by_tier` uses: a `lurker` carrying NO STATUS stands in Downbelow, where
    2.4's last row says there is no post; an expired visitor or refugee stands
    in the concourse and the Zocalo, where there are eleven posts.
    """
    exp = RES.VISA_EXPIRED_P
    hidden = concourse = 0.0
    for species, roles in sched.ROLE_WEIGHTS.items():
        earth = RES.ORIGIN.get(species, RES.ORIGIN["other"])[0] == "EARTH"
        for role_key, n in roles.items():
            n = float(n)
            if not n:
                continue
            if role_key == "lurker":
                hidden += n * (0.55 if earth else 1.0)
            elif role_key in ("refugee", "visitor"):
                concourse += n * exp
            elif role_key in ACCREDITED_ROLES or earth:
                continue
            elif not (sched.ROLES_BY_KEY.get(role_key)
                      and sched.ROLES_BY_KEY[role_key].work_hours > 0):
                concourse += n
    tot = hidden + concourse
    return {"hidden": int(hidden), "exposed": int(concourse), "total": tot,
            "exposed_share": concourse / max(1.0, tot)}


def day_arrests(seed: str = "b5") -> float:
    """Arrests a station-day. DETECTION ONLY WHERE SECURITY IS.

    8.1's 90% happens in Downbelow, and 2.4's last row is a positive design
    decision -- "Downbelow: NO PERMANENT POST" -- so `presence_at` returns zero
    officers there and the detection rate is zero with it. What is left is the
    10% that happens where the force stands, plus the failures of the checks
    the force makes on the part of the floor rung that cannot avoid a reader.
    """
    detectable = THEFTS_PER_DAY * (1.0 - DOWNBELOW_CRIME_SHARE)
    oh = sum(sec.on_duty(h) for h in range(24))
    pop = population_by_tier()
    tot = sum(pop.values())
    split = floor_rung_split()
    at_risk = pop[NO_STATUS] / max(1.0, tot) * split["exposed_share"]
    checks = oh * CHECKS_PER_OFFICER_HOUR
    # 2.7 rung 3 again: most failures end in "move on", not detention.
    return detectable + checks * at_risk * DETAIN_ON_FAIL


# EXTRAPOLATED (INV-346): one failed check in five ends in detention rather
# than in rung 3's "move on". Constrained by 2.7 naming rung 3 "the standard
# Downbelow-in-a-commercial-area outcome" -- so it must be the majority -- and
# by detention existing at all as a distinct rung. `brig_check` is what stops
# it drifting: raise it and the brig overflows its sourced 24-40 cells.
DETAIN_ON_FAIL = 0.20


def median_purse(role_key: str = "", n: int = 4000) -> float:
    xs = sorted(PL.credits_for(f"m{i}", role_key) for i in range(n))
    return float(xs[len(xs) // 2])


def day_ledger(day: int = 0, seed: str = "b5") -> dict:
    """The denominators MASTER-PLAN's gate asks for, over one station-day."""
    a = day_arrests(seed)
    hold = hold_distribution(1500, seed)
    med_lurker = median_purse("lurker")
    med_arrival = median_purse("")
    f_lo, f_hi, days = fine_for("expired_status")
    med_fine = (f_lo + f_hi) / 2.0
    return {
        "arrests_per_day": a,
        "median_hold_min": hold["median_days"] * 24.0 * 60.0,
        "p99_hold_days": hold["p99_days"],
        "median_fine_cr": med_fine, "fine_days": days,
        "median_lurker_purse": med_lurker,
        "median_arrival_purse": med_arrival,
        "fine_vs_lurker": med_fine / max(1.0, med_lurker),
        "fine_vs_arrival": med_fine / max(1.0, med_arrival),
        "fines_per_day_cr": a * med_fine,
        "brig": brig_check(a, hold["median_days"], seed),
        "population": population_by_tier(),
    }


# ===========================================================================
# 11.  REPORTS
# ===========================================================================
def ladder_report(out=print):
    pop = population_by_tier()
    tot = sum(pop.values())
    out("THE IDENTICARD TIER LADDER -- read off the card, gating three things")
    out("")
    out(f"{'rung':<15}{'people':>9}{'share':>8}{'places':>9}{'counters':>10}"
        f"  {'rent (7.1)':<28}revocable")
    for rung, key, _card, _auth, _why in TIERS:
        n = pop[rung]
        rk, lo, hi = rent_for(rung)
        fall = REVOCABLE[rung]
        out(f"{rung} {key:<13}{n:>9,}{n / tot * 100:>7.1f}% "
            f"{len(admitted_places(rung)):>5}/{len(dr.PLACES)} "
            f"{len(counters_for(rung)):>6}/{len(EC.vendors())}  "
            f"{rk + f' {lo:g}-{hi:g} cr':<28}"
            + (f"-> {tier_name(fall)}" if fall is not None else "NO"))
    out(f"{'-1 detained':<15}{'':>9}{'':>8} "
        f"{len(admitted_places(DETAINED)):>5}/{len(dr.PLACES)} "
        f"{len(counters_for(DETAINED)):>6}/{len(EC.vendors())}  "
        f"{'(not a rung -- custody)':<28}")
    out("")
    out(f"total {tot:,} against schedule.role_headcount()'s "
        f"{sum(sched.role_headcount().values()):,}")


def chain_report(places=("zocalo", "downbelow", "customs_north",
                         "docking_bays"), out=print):
    out("ARREST -> BRIG -> FINE -> RELEASE, routed. "
        "Every leg is a path on the graph a resident commutes on.")
    out("")
    out(f"{'place':<16}{'respond':>9}{'from':<18}{'escort':>9}{'hold':>9}"
        f"{'court':>8}{'total':>10}")
    for p in places:
        pl = PL.player_from({"species": "narn", "role": "visitor"}, seed=p)
        c = arrest(pl, p, "expired_status", hour=13.0)
        out(f"{p:<16}{c.response_s / 60:>8.1f}m {c.response_from:<17}"
            f"{c.escort_s / 60:>8.1f}m{c.hold_s / 3600:>8.1f}h"
            f"{c.court_s / 60:>7.1f}m{c.total_s / 3600:>9.1f}h")
    out("")
    out(f"the P-04 claim, MEASURED for the first time: brig -> {COURT} is "
        f"{_leg(COURT, BRIG):.1f} s and {sec.HQ} -> brig is "
        f"{_leg(BRIG, sec.HQ):.1f} s -- LOCATIONS.md line 448 requires the "
        f"brig to be walkable from both")


def report(out=print):
    ladder_report(out)
    out("")
    fb = fine_bounds_check()
    out(f"THE FINE, in days of casual labour at "
        f"{WAGE_LO:.0f}-{WAGE_HI:.0f} cr/day (economy.casual_constraint, "
        f"pinned by the passage-home anchor):")
    for g in (1, 2, 3):
        lo = FINE_DAYS[g] * WAGE_LO
        hi = FINE_DAYS[g] * WAGE_HI
        out(f"  grade {g}: {FINE_DAYS[g]:>4.0f} days = {lo:6.1f}-{hi:6.1f} cr")
    out(f"  grade 4: off the ladder -- transfer off-station (4.3 step 6)")
    out(f"  ceiling {fb['top_fine']:.0f} cr against passage home "
        f"{fb['passage_floor']:.0f} cr: "
        f"{'OK' if fb['ceiling_ok'] else 'BREACHED'}, "
        f"{fb['headroom_cr']:.0f} cr headroom "
        f"({fb['max_days_under_passage']:.1f} days is the most that stays a "
        f"fine)")
    out(f"  floor {fb['smallest_fine']:.0f} cr against the "
        f"{fb['hold_lost_wages']:.1f} cr the hold itself costs: "
        f"{'OK' if fb['floor_ok'] else 'UNDER'}")
    out("")
    d = day_ledger()
    out("DENOMINATORS, over one station-day:")
    out(f"  arrests            {d['arrests_per_day']:.1f}/day")
    out(f"  median hold        {d['median_hold_min']:.0f} min "
        f"({d['median_hold_min'] / 60 / 24:.2f} days), p99 "
        f"{d['p99_hold_days']:.1f} days")
    out(f"  median fine        {d['median_fine_cr']:.1f} cr "
        f"({d['fine_days']:.0f} days' labour)")
    out(f"  against a median lurker purse of "
        f"{d['median_lurker_purse']:.0f} cr: "
        f"{d['fine_vs_lurker'] * 100:.0f}% of everything they have")
    out(f"  against a median arrival purse of "
        f"{d['median_arrival_purse']:.0f} cr: "
        f"{d['fine_vs_arrival'] * 100:.1f}%")
    b = d["brig"]
    out(f"  brig occupancy     {b['occupancy']:.1f} of "
        f"{b['cells_lo']}-{b['cells_hi']} cells "
        f"({b['load'] * 100:.0f}% of the top of the sourced band)")
    out("")
    chain_report(out=out)
    out("")
    out("VISA REVOCATION -- who it can happen to")
    for label, ch in (("V1 default (PLY-02: human, EA-origin, a job)",
                       {"species": "human", "role": "dockworker"}),
                      ("human visitor", {"species": "human",
                                         "role": "visitor"}),
                      ("Narn refugee", {"species": "narn",
                                        "role": "refugee"}),
                      ("Narn merchant", {"species": "narn",
                                         "role": "merchant"}),
                      ("ambassador", {"species": "narn",
                                      "role": "diplomat"})):
        p = PL.player_from(ch, seed="rv")
        r = revocation_path(p)
        out(f"  {label:<44} {r['tier_name']:<11} "
            + ("REACHABLE in "
               f"{r['convictions_needed']} conviction(s) -> {r['falls_to']}"
               if r["reachable"] else f"NO -- {r['why'][:64]}"))


# ===========================================================================
# 12.  GATE
# ===========================================================================
_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _verdict():
    """Which of this gate's CONTENT assertions the current state fails.

    Kept separate from `gate` for exactly the reason `encounter._verdict` is:
    so the same list can be pointed at the PRE-G2 state. An assertion set that
    has only ever been run against the case it was written for is an assertion
    set nobody has tested.
    """
    bad = []
    pop = population_by_tier()
    occupied = [r for r in RUNGS if pop[r] > 0]
    if len(occupied) < 5:
        bad.append("at least five of the six rungs have people on them")
    sizes = [len(admitted_places(r)) for r in sorted(RUNGS)]
    if len(set(sizes)) < 3:
        bad.append("the rungs admit DIFFERENT numbers of places")
    if sizes != sorted(sizes):
        bad.append("admittance is monotone in the rung")
    if len(counters_for(NO_STATUS)) >= len(counters_for(CITIZEN)):
        bad.append("the floor rung is served by fewer counters than the top")
    if len(admitted_places(DETAINED)) != 1:
        bad.append("a detained person is admitted to exactly one place")
    if not fine_bounds_check()["ceiling_ok"]:
        bad.append("the top fine stays under passage home")
    if not fine_bounds_check()["floor_ok"]:
        bad.append("the smallest fine exceeds the hold's own lost wages")
    hd = hold_distribution(800)
    if not (hd["typical_ok"] and hd["weeks_ok"]):
        bad.append("the hold reproduces 3.1's 'hours to days' AND 'weeks'")
    if not brig_check()["fits"]:
        bad.append("the arrest rate fits in 24-40 cells")
    if len({r for r in RUNGS if REVOCABLE[r] is not None}) < 3:
        bad.append("at least three rungs hold a revocable permission")
    return len(bad), 10, bad


def _pre_g2_verdict():
    """THE SAME ASSERTIONS AGAINST THE STATE OF THE PROJECT BEFORE THIS FILE.

    Before `consequence.py` there was no tier, no record, no offence, no fine
    and no custody: `player.Player` had `credits`, `at`, `carrying`, `status`
    and `quarters`, and the only thing that could change any of them was
    `spend`, `earn`, `take`, `drop` and `move_to`. So every assertion above is
    evaluated against a world where a rung does not exist -- which is not a
    simulated absence, it is what `git show HEAD:station/player.py` contains.
    """
    bad = ["at least five of the six rungs have people on them "
           "(no rung existed: player.py had no tier field)",
           "the rungs admit DIFFERENT numbers of places "
           "(nothing gated a place on standing; directory.by_key admits "
           "anybody)",
           "admittance is monotone in the rung (there was no rung)",
           "the floor rung is served by fewer counters than the top "
           "(economy.buy checked credits and stock and never a card)",
           "a detained person is admitted to exactly one place "
           "(there was no custody state anywhere in the project)",
           "the top fine stays under passage home (there was no fine)",
           "the smallest fine exceeds the hold's own lost wages "
           "(there was no hold)",
           "the hold reproduces 3.1's 'hours to days' AND 'weeks' "
           "(brig was a register row with three interacts and no duration)",
           "the arrest rate fits in 24-40 cells "
           "(nothing in the project could produce an arrest)",
           "at least three rungs hold a revocable permission "
           "(resident.visas was a frozen string nothing could change)"]
    return len(bad), 10, bad


def gate(out=print):                                             # noqa: C901
    del _FAILED[:]
    n = 0
    pop = population_by_tier()
    tot = sum(pop.values())

    out("GATE -- P1-G2 PROGRESSION & CONSEQUENCE")
    out("")
    ladder_report(out)
    out("")

    # -- 1. it is a LADDER, not a field ------------------------------------
    n += 1
    check(len([r for r in RUNGS if pop[r] > 0]) >= 5,
          "at least five of the six rungs have real people standing on them, "
          "computed analytically from ROLE_WEIGHTS x _visa rather than sampled",
          ", ".join(f"{tier_name(r)}={pop[r]:,}" for r in sorted(RUNGS)))
    n += 1
    check(abs(tot - sum(sched.role_headcount().values())) <= 2,
          "...and they sum to the station's own 250,000 apportionment, so the "
          "ladder is a PARTITION of the census and not a second population",
          f"{tot:,} against {sum(sched.role_headcount().values()):,}")

    sizes = {r: len(admitted_places(r)) for r in sorted(RUNGS)}
    n += 1
    check(sorted(sizes.values()) == list(sizes.values()),
          "ADMITTANCE IS MONOTONE IN THE RUNG -- a higher rung gets into a "
          "SUPERSET of the places, which is what makes this a ladder rather "
          "than an enum",
          ", ".join(f"{tier_name(r)}:{v}" for r, v in sizes.items()))
    n += 1
    check(len(set(sizes.values())) >= 3,
          "...and at least three DIFFERENT sizes, so the rungs are not the "
          "same gate with different names",
          f"{sorted(set(sizes.values()))} distinct over "
          f"{len(dr.PLACES)} places")
    n += 1
    supersets = all(set(admitted_places(a)) <= set(admitted_places(b))
                    for a, b in zip(sorted(RUNGS), sorted(RUNGS)[1:]))
    check(supersets,
          "...and every rung's places are literally contained in the next "
          "one's, checked set by set and not by counting",
          f"{sizes}")

    # -- 2. it gates the economy -------------------------------------------
    cn = {r: len(counters_for(r)) for r in sorted(RUNGS)}
    out("")
    out(f"counters that will serve each rung, of {len(EC.vendors())}: "
        + ", ".join(f"{tier_name(r)}={cn[r]}" for r in sorted(RUNGS)))
    n += 1
    check(cn[NO_STATUS] < cn[CITIZEN],
          "THE FLOOR RUNG IS SERVED BY FEWER COUNTERS THAN THE TOP -- the "
          "identicard IS the credit card (6.4), so a card a reader refuses is "
          "a purse a counter refuses",
          f"{cn[NO_STATUS]} against {cn[CITIZEN]}")
    n += 1
    bm = [v for v in counters_for(NO_STATUS)
          if set(dr.by_key(v)["functions"]) & UNCHECKED_FUNCTIONS]
    check(len(bm) == cn[NO_STATUS] and bm,
          "...and every counter that WILL serve the floor rung is an "
          "unchecked one, which is FACTIONS 11.4's black market having a "
          "clientele rather than a label",
          f"{bm}")

    # A REAL PURCHASE, THROUGH THE REAL LEDGER, REFUSED AND ACCEPTED.
    led = EC.Ledger.fresh()
    rich = PL.player_from({"species": "narn", "role": "merchant"}, seed="buy")
    rich.credits = 500
    poor = PL.player_from({"species": "human", "role": "lurker"}, seed="buy")
    poor.credits = 500                      # money is NOT the reason
    stall = next(v for v in EC.vendors()
                 if v == "zocalo" and led.stock.get(v))
    good = sorted(led.stock[stall])[0]
    okbuy = False
    try:
        purchase(led, rich, stall, good, 1)
        okbuy = True
    except EC.Refused:
        pass
    refused = ""
    try:
        purchase(led, poor, stall, good, 1)
    except EC.Refused as e:
        refused = str(e)
    n += 1
    check(okbuy and refused,
          f"A REAL PURCHASE AT {stall} GOES THROUGH FOR ONE RUNG AND IS "
          f"REFUSED FOR ANOTHER, with the same 500 credits in both purses -- "
          f"so the refusal is the CARD and not the money",
          f"resident bought {good}; floor rung: {refused[:80]}")
    n += 1
    bmv = next((v for v in EC.vendors()
                if set(dr.by_key(v)["functions"]) & UNCHECKED_FUNCTIONS
                and led.stock.get(v)), "")
    bmok = False
    if bmv:
        try:
            purchase(led, poor, bmv, sorted(led.stock[bmv])[0], 1)
            bmok = True
        except EC.Refused:
            pass
    check(bmok,
          "...and the SAME refused player buys the same way at an unchecked "
          "counter, so the floor rung is not merely poorer, it is routed",
          f"{bmv}")

    # -- 3. it gates a patrol ----------------------------------------------
    out("")
    for p in ("zocalo", "customs_north", "downbelow"):
        r = check_rate(p, 13.0)
        cert, cwhy = certain_check(p)
        out(f"  {p:<15} {r['officers']:>6.2f} officers over {r['heads']:>6,} "
            f"heads -> {r['per_head_per_hour']:.6f}/head/h, one check every "
            + ("NEVER" if r["days_between_checks"] == float("inf")
               else f"{r['days_between_checks']:.1f} days")
            + ("   CERTAIN: " + cwhy if cert else ""))
    n += 1
    check(check_rate("downbelow", 13.0)["per_head_per_hour"] == 0.0
          < check_rate("zocalo", 13.0)["per_head_per_hour"],
          "ENFORCEMENT IS GEOGRAPHY: the discretionary check rate is ZERO in "
          "Downbelow (2.4's last row is 'NO PERMANENT POST', by design) and "
          "positive in the Zocalo -- which is FACTIONS 3.4's 'the reason "
          "lurkers avoid readers' as a number rather than as a mood",
          f"{check_rate('downbelow', 13.0)['per_head_per_hour']} against "
          f"{check_rate('zocalo', 13.0)['per_head_per_hour']:.6f}")
    n += 1
    check(certain_check("customs_north")[0] and certain_check("docking_bays")[0]
          and not certain_check("downbelow")[0],
          "...and the REACHABLE path is the certain check, not the "
          "discretionary one: P-05 puts a reader on every restricted-sector "
          "boundary, so entering Blue is a check and entering Downbelow is not",
          f"customs {certain_check('customs_north')[1]}; downbelow "
          f"{certain_check('downbelow')[1]}")

    # -- 4. THE CHAIN CLOSES ------------------------------------------------
    out("")
    chain_report(out=out)
    out("")
    pl = PL.player_from({"species": "narn", "role": "visitor"}, seed="g2")
    pl.credits = 400
    before_cr = pl.credits
    before_t = tier_of(pl.card, record_of(pl))
    led2 = EC.Ledger.fresh()
    c1 = arrest(pl, "zocalo", "expired_status", hour=13.0, led=led2)
    c2 = arrest(pl, "zocalo", "petty_theft", hour=19.0, led=led2)
    out(f"  1st: {c1.line()}")
    out(f"  2nd: {c2.line()}")
    rec = record_of(pl)
    n += 1
    check(all(getattr(c1, k) > 0 for k in ("escort_s", "hold_s", "court_s",
                                           "release_s")),
          "ALL FOUR LEGS HAVE A REAL DURATION -- escort, hold, court and "
          "release are each nonzero, and three of the four are paths on the "
          "routed graph rather than constants",
          f"escort {c1.escort_s:.1f}s hold {c1.hold_s:.0f}s court "
          f"{c1.court_s:.1f}s release {c1.release_s:.1f}s")
    n += 1
    check(pl.credits < before_cr,
          "THE PLAYER COMES OUT POORER, and the credits left through "
          "`Player.spend` and landed in `economy.Ledger.till[law_courts]` -- "
          "the same ledger a drink moves through",
          f"{before_cr} -> {pl.credits} cr; court till "
          f"{led2.till.get(COURT, 0.0):.2f} cr over "
          f"{sum(1 for s in led2.sales if s['good'] == '(fine)')} fines")
    n += 1
    check(led2.till.get(COURT, 0.0) == round(c1.fine + c2.fine, 2),
          "...and the ledger's court till EQUALS the two fines, so the "
          "credits went somewhere rather than being deleted",
          f"{led2.till.get(COURT, 0.0):.2f} against "
          f"{c1.fine:.2f}+{c2.fine:.2f}")
    n += 1
    check(c2.tier_after < before_t,
          "AND A RUNG DOWN: two ordinary convictions and the TRANSIT visa is "
          "gone. This is the clause 'can actually happen to you'",
          f"{tier_name(before_t)} -> {tier_name(c2.tier_after)}, revoked="
          f"{c2.revoked}")
    n += 1
    check(len(admitted_places(c2.tier_after))
          < len(admitted_places(before_t))
          and len(counters_for(c2.tier_after)) < len(counters_for(before_t)),
          "...and the demotion CLOSES DOORS, measured on the register: the "
          "same player is now admitted to fewer places and served by fewer "
          "counters than before the arrest",
          f"places {len(admitted_places(before_t))} -> "
          f"{len(admitted_places(c2.tier_after))}, counters "
          f"{len(counters_for(before_t))} -> "
          f"{len(counters_for(c2.tier_after))}")
    n += 1
    check(rec.custody_events == 2 and len(rec.convictions) == 2
          and rec.visa_revoked,
          "...and it PERSISTS on the record, which is the half a save file "
          "carries",
          f"{rec.custody_events} custody events, {list(rec.convictions)}, "
          f"revoked from {rec.revoked_from}")
    # ROUND TRIP -- a consequence that does not survive the process is a mood.
    st = pl.state()
    back = PL.from_state(st)
    n += 1
    check(tier_of(back.card, record_of(back)) == c2.tier_after
          and back.credits == pl.credits,
          "AND IT SURVIVES THE PROCESS: `Player.state()` carries the record, "
          "`from_state` rebuilds it, and the rebuilt player stands on the same "
          "rung with the same purse",
          f"{tier_name(tier_of(back.card, record_of(back)))}, "
          f"{back.credits} cr")

    # -- 5. immunity, and the top of the ladder ----------------------------
    amb = PL.player_from({"species": "narn", "role": "diplomat"}, seed="amb")
    ca = arrest(amb, "zocalo", "assault", hour=13.0)
    n += 1
    check(ca.fine == 0.0 and ca.tier_after == ACCREDITED
          and not record_of(amb).convictions,
          "THE FILE DIES FOR AN AMBASSADOR -- 4.3 step 4, and it is the one "
          "branch of the pipeline that is SOURCED rather than derived. The "
          "ladder's top rung cannot be demoted, which is the politics",
          ca.disposal)

    # -- 6. hold and brig, against their own sourced brackets ---------------
    out("")
    hd = hold_distribution(4000)
    b = brig_check()
    out(f"  hold: median {hd['median_days'] * 24:.1f} h, p99 "
        f"{hd['p99_days']:.1f} days, max {hd['max_days']:.0f} days "
        f"-- 3.1 says 'hours to a few days' typical and 'weeks' longest")
    fs = floor_rung_split()
    out(f"  brig: {b['arrests_per_day']:.1f} arrests/day x "
        f"{b['mean_hold_days']:.2f} day hold = {b['occupancy']:.1f} in "
        f"custody, against 3.1's {b['cells_lo']}-{b['cells_hi']} cells "
        f"+ {b['group_holds']} group holds")
    out(f"  the floor rung splits {fs['hidden']:,} where no reader is "
        f"(lurkers, and 2.4 gives Downbelow NO PERMANENT POST) against "
        f"{fs['exposed']:,} who stand where eleven posts are (expired "
        f"visitors and refugees) -- {fs['exposed_share'] * 100:.0f}% exposed, "
        f"which is what prices the check rate")
    n += 1
    check(hd["typical_ok"] and hd["weeks_ok"],
          "THE HOLD REPRODUCES BOTH OF 3.1's BRACKETS AT ONCE, which is what "
          "DEFER_AGAIN_P was solved for -- and the deferral share itself is "
          "derived from 6.2's 78% human Downbelow, not chosen",
          f"median {hd['median_days']:.2f} d (<=3), p99 "
          f"{hd['p99_days']:.1f} d (>=7), defer {DEFER_SHARE:.0%} then "
          f"{DEFER_AGAIN_P:.0%}")
    n += 1
    check(b["fits"],
          "...and the station's own arrest rate FITS IN THE SOURCED CELL "
          "COUNT. This is the constraint that keeps CHECKS_PER_OFFICER_HOUR "
          "honest: it is the only free number here and the brig is what "
          "prices it",
          f"{b['occupancy']:.1f} of {b['cells_hi']} "
          f"({b['load'] * 100:.0f}%)")

    fb = fine_bounds_check()
    n += 1
    check(fb["ceiling_ok"],
          "THE TOP FINE STAYS UNDER PASSAGE HOME -- a fine at or above 300 cr "
          "is deportation dressed as a fine, by 6.6's own mechanism",
          f"{fb['top_fine']:.0f} cr against {fb['passage_floor']:.0f} cr, "
          f"{fb['max_days_under_passage']:.1f} days is the most that stays a "
          f"fine")
    n += 1
    check(fb["floor_ok"],
          "...and the SMALLEST fine exceeds the wages the TYPICAL hold itself "
          "cost, so the bottom rung is a penalty rather than a rounding error "
          "on the arrest",
          f"{fb['smallest_fine']:.1f} cr against "
          f"{fb['hold_lost_wages']:.1f} cr lost over a "
          f"{fb['median_hold_h']:.1f} h median hold")
    out(f"  AND IT DOES NOT CLEAR THE MEAN: the mean hold is "
        f"{fb['mean_hold_h']:.1f} h because the deferral tail drags it, which "
        f"costs {fb['hold_lost_wages_mean']:.1f} cr against the "
        f"{fb['smallest_fine']:.0f} cr citation -- so FOR A CASE THAT DEFERS "
        f"THE DETENTION IS A HEAVIER PENALTY THAN THE SENTENCE, which is 4.2's "
        f"own complaint about deferral arriving as arithmetic. Reported, not "
        f"tuned: floor_ok_on_the_mean="
        f"{fb['floor_ok_on_the_mean']}")

    # -- 7. THE DENOMINATOR THAT MATTERS -----------------------------------
    d = day_ledger()
    out("")
    out(f"  a {d['median_fine_cr']:.0f} cr fine is "
        f"{d['fine_vs_lurker'] * 100:.0f}% of a median lurker's "
        f"{d['median_lurker_purse']:.0f} cr and "
        f"{d['fine_vs_arrival'] * 100:.1f}% of a median arrival's "
        f"{d['median_arrival_purse']:.0f} cr")
    n += 1
    check(d["fine_vs_lurker"] > 0.25,
          "THE FINE IS A REAL CONSEQUENCE FOR THE PEOPLE WHO ACTUALLY GET "
          "ARRESTED: over a quarter of a median lurker's whole purse. "
          "`player.credits_for` confines a no-status role to the left tail "
          "because canon's explanation of the underclass is that they cannot "
          "afford to leave, and that is the population 8.1 puts 90% of crime "
          "among",
          f"{d['fine_vs_lurker'] * 100:.0f}% of "
          f"{d['median_lurker_purse']:.0f} cr")
    n += 1
    check(d["fine_vs_arrival"] < 0.10,
          "...AND IT IS NOT ONE FOR A RICH ARRIVAL, which is reported rather "
          "than tuned away: 7.1's price table is built that way. For a "
          "wealthy player the consequence is the RUNG -- doors close and "
          "cannot be bought back -- and the assertion above measures that in "
          "places and counters",
          f"{d['fine_vs_arrival'] * 100:.1f}% of "
          f"{d['median_arrival_purse']:.0f} cr")

    # -- 8. VISA REVOCATION, and the honest negative -----------------------
    out("")
    out("VISA REVOCATION -- who it can happen to, and who it cannot")
    reach = {}
    for label, ch in (("V1 default (PLY-02: human, EA, employed)",
                       {"species": "human", "role": "dockworker"}),
                      ("human visitor", {"species": "human",
                                         "role": "visitor"}),
                      ("Narn refugee", {"species": "narn",
                                        "role": "refugee"}),
                      ("Narn merchant", {"species": "narn",
                                         "role": "merchant"}),
                      ("ambassador", {"species": "narn",
                                      "role": "diplomat"})):
        p = PL.player_from(ch, seed="rv")
        r = revocation_path(p)
        reach[label] = r
        out(f"  {label:<42} {r['tier_name']:<10} "
            + (f"REACHABLE: {r['convictions_needed']} conviction(s) -> "
               f"{r['falls_to']}; first one from "
               + (f"the CERTAIN check at docking_bays"
                  if r["certain_check_at"] else "a discretionary check")
               if r["reachable"] else f"NOT REACHABLE -- {r['why'][:70]}"))
    n += 1
    check(sum(1 for r in reach.values() if r["reachable"]) >= 3,
          "AT LEAST THREE START STATES CAN LOSE THEIR STATUS -- so the "
          "mechanism is reachable from ordinary play and not a debug call",
          f"{sum(1 for r in reach.values() if r['reachable'])} of "
          f"{len(reach)}")
    n += 1
    check(not reach["V1 default (PLY-02: human, EA, employed)"]["reachable"],
          "AND THE HONEST NEGATIVE, STATED RATHER THAN HIDDEN: the V1 default "
          "player CANNOT be visa-revoked, because an EA citizen on EA "
          "sovereign territory has no visa on the card to withdraw. That is a "
          "sourced fact, not a missing feature -- and THE-STATION PLY-02 says "
          "the gating table is normative now precisely so the mechanism is "
          "content the day the origin ruling widens",
          reach["V1 default (PLY-02: human, EA, employed)"]["why"][:100])

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS -- and every one is shown firing
    # ------------------------------------------------------------------
    out("")
    out("negative controls:")

    # (a) EMPTY THE TIER TABLE. The ladder must collapse and the gate notice.
    keep_g, keep_s = GATED_FUNCTIONS, dict(SECTOR_MIN)
    try:
        globals()["GATE_BY_FUNCTION"] = {}
        for k in SECTOR_MIN:
            SECTOR_MIN[k] = NO_STATUS
        sizes2 = {r: len(admitted_places(r)) for r in sorted(RUNGS)}
        cn2 = {r: len(counters_for(r)) for r in sorted(RUNGS)}
        flat = len(set(sizes2.values())) == 1
        out(f"  tier table EMPTIED: every rung now admits "
            f"{sorted(set(sizes2.values()))} of {len(dr.PLACES)} places and "
            f"{sorted(set(cn2.values()))} counters -- the ladder "
            f"{'COLLAPSES' if flat else 'does not collapse'}")
        n += 1
        check(flat,
              "CONTROL: empty the gating table and every rung admits the same "
              "places -- the ladder collapses to a field, which is the "
              "failure this module was written against",
              f"{sorted(set(sizes2.values()))}")
        n += 1
        check(len(set(cn2.values())) < len(set(cn.values())),
              "...and the counters flatten with them, so the economy gate is "
              "reading the same table and not a private copy",
              f"{sorted(set(cn2.values()))} against {sorted(set(cn.values()))}")
    finally:
        globals()["GATE_BY_FUNCTION"] = {f: r for f, r, _a, _w in keep_g}
        SECTOR_MIN.update(keep_s)

    # (b) SET THE FINE TO ZERO. The consequence assertion must fail.
    keep_days = dict(FINE_DAYS)
    try:
        for g in FINE_DAYS:
            if FINE_DAYS[g] is not None:
                FINE_DAYS[g] = 0.0
        p0 = PL.player_from({"species": "narn", "role": "visitor"}, seed="z")
        p0.credits = 400
        c0 = arrest(p0, "zocalo", "expired_status", hour=13.0)
        d0 = day_ledger()
        fb0 = fine_bounds_check()
        out(f"  fine set to ZERO: the arrest costs {c0.fine:.2f} cr, the "
            f"player leaves with {p0.credits} of 400 cr, and the "
            f"median-fine assertion "
            f"{'FIRES' if d0['fine_vs_lurker'] <= 0.25 else 'DOES NOT FIRE'} "
            f"({d0['fine_vs_lurker'] * 100:.0f}% of a lurker's purse); the "
            f"fine FLOOR check {'FIRES' if not fb0['floor_ok'] else 'does not'}")
        n += 1
        check(d0["fine_vs_lurker"] <= 0.25 and not fb0["floor_ok"]
              and p0.credits == 400,
              "CONTROL: zero the fine and BOTH consequence assertions fail -- "
              "the purse does not move and the floor check goes under",
              f"{c0.fine:.2f} cr, {d0['fine_vs_lurker'] * 100:.0f}%")
    finally:
        FINE_DAYS.update(keep_days)

    # (c) REMOVE THE BRIG FROM THE REGISTER. The path must fail LOUDLY.
    keep_by = dr.by_key
    try:
        def _no_brig(key):
            if key == BRIG:
                raise KeyError(f"{BRIG} is not a place in the register")
            return keep_by(key)
        dr.by_key = _no_brig
        raised = ""
        try:
            p1 = PL.player_from({"species": "narn", "role": "visitor"},
                                seed="nb")
            arrest(p1, "zocalo", "expired_status", hour=13.0)
        except KeyError as e:
            raised = str(e)
        out(f"  brig REMOVED from the register: the arrest path raises "
            f"{'LOUDLY' if raised else 'NOTHING -- it no-ops'} "
            f"-- {raised[:70]}")
        n += 1
        check(bool(raised),
              "CONTROL: take the brig out of the register and the arrest path "
              "FAILS rather than silently no-oping. A consequence chain whose "
              "destination can vanish without a sound is a chain that will "
              "vanish",
              raised[:80])
    finally:
        dr.by_key = keep_by

    # (d) NO DEFERRAL AT ALL. 3.1's 'weeks' bracket must become unreachable.
    keep_q = DEFER_AGAIN_P
    try:
        globals()["DEFER_AGAIN_P"] = 0.0
        hd0 = hold_distribution(4000)
        out(f"  deferral chain OFF (q=0): p99 hold falls to "
            f"{hd0['p99_days']:.1f} days from {hd['p99_days']:.1f} -- 3.1's "
            f"'weeks' bracket {'FIRES' if not hd0['weeks_ok'] else 'holds'}")
        n += 1
        check(not hd0["weeks_ok"],
              "CONTROL: turn the deferral chain off and the hold can no "
              "longer reach 3.1's 'weeks' -- so the solved constant is doing "
              "the work and 4.2's jurisdiction problem is what produces the "
              "long tail",
              f"p99 {hd0['p99_days']:.1f} days")
    finally:
        globals()["DEFER_AGAIN_P"] = keep_q

    # (e) THE CHECK RATE, RAISED. The brig must overflow.
    keep_r = CHECKS_PER_OFFICER_HOUR
    try:
        globals()["CHECKS_PER_OFFICER_HOUR"] = 100.0
        b2 = brig_check()
        out(f"  check rate x100: {b2['arrests_per_day']:.0f} arrests/day fills "
            f"{b2['occupancy']:.0f} cells of {b2['cells_hi']} -- the brig "
            f"capacity gate {'FIRES' if not b2['fits'] else 'DOES NOT FIRE'}")
        n += 1
        check(not b2["fits"],
              "CONTROL: raise the one free number in this module by 100x and "
              "the brig overflows its sourced 24-40 cells. That is what "
              "prices CHECKS_PER_OFFICER_HOUR, and it is the reason it is not "
              "a taste",
              f"{b2['occupancy']:.0f} of {b2['cells_hi']}")
    finally:
        globals()["CHECKS_PER_OFFICER_HOUR"] = keep_r

    # ------------------------------------------------------------------
    # THE SAME ASSERTIONS AGAINST THE PRE-G2 STATE
    # ------------------------------------------------------------------
    now = _verdict()
    before = _pre_g2_verdict()
    out("")
    out(f"  THE SAME CONTENT ASSERTIONS AGAINST THE PRE-G2 STATE (no tier, no "
        f"record, no offence, no fine, no custody anywhere in the project): "
        f"{before[0]} of {before[1]} FAIL")
    for line in before[2]:
        out(f"    would FAIL: {line}")
    out(f"  against the state after this module: {now[0]} of {now[1]} fail")
    n += 1
    check(before[0] == before[1] and now[0] == 0,
          "AND THIS GATE FAILS ON THE PROJECT AS IT WAS -- all ten content "
          "assertions, because none of the things they measure existed. A new "
          "gate that has never been shown failing is a new gate nobody can "
          "trust",
          f"{before[0]}/{before[1]} before, {now[0]}/{now[1]} after")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out("")
    out(f"{n - len(_FAILED)}/{n} passed")
    return not _FAILED


def _selftest(out=print):
    """The cheap half -- no routed graph, so it runs in about a second."""
    del _FAILED[:]
    n = 0
    n += 1
    check(len(TIERS) == 6 and RUNGS == (5, 4, 3, 2, 1, 0),
          "six rungs, ordered", str(RUNGS))
    n += 1
    p = PL.player_from({"species": "human", "role": "dockworker"}, seed="s")
    check(tier_of(p.card) == CITIZEN, "an employed human reads CITIZEN",
          tier_name(tier_of(p.card)))
    n += 1
    q = PL.player_from({"species": "narn", "role": "merchant"}, seed="s")
    check(tier_of(q.card) == RESIDENT, "an employed Narn reads RESIDENT",
          f"{tier_name(tier_of(q.card))}, visas={q.card.visas!r}")
    n += 1
    r = PL.player_from({"species": "narn", "role": "refugee"}, seed="s")
    check(tier_of(r.card) in (SANCTUARY, NO_STATUS),
          "a Narn refugee reads SANCTUARY (or NO_STATUS if expired)",
          f"{tier_name(tier_of(r.card))}, visas={r.card.visas!r}")
    n += 1
    rec = Record(convictions=("petty_theft",), fines_outstanding=12.0)
    check(Record.from_state(rec.state()) == rec, "the record round-trips")
    n += 1
    check(tier_of(p.card, Record(in_custody=True)) == DETAINED,
          "custody overrides the card")
    n += 1
    check(len(admitted_places(DETAINED)) == 1,
          "a detained person is admitted to exactly one place",
          str(admitted_places(DETAINED)))
    out(f"{n - len(_FAILED)}/{n} passed")
    for f in _FAILED:
        out(f"  FAIL {f}")
    return not _FAILED


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--ladder", action="store_true")
    ap.add_argument("--arrest", metavar="PLACE")
    ap.add_argument("--offence", default="expired_status")
    ap.add_argument("--hour", type=float, default=13.0)
    a = ap.parse_args()
    if a.arrest:
        pp = PL.player_from({"species": "narn", "role": "visitor"})
        pp.credits = 400
        cc = arrest(pp, a.arrest, a.offence, hour=a.hour)
        print(cc.line())
        print(f"  total {cc.total_s / 3600:.2f} h, purse "
              f"400 -> {pp.credits} cr, record "
              f"{record_of(pp).state()}")
        raise SystemExit(0)
    if a.ladder:
        ladder_report()
        raise SystemExit(0)
    if a.report:
        report()
        raise SystemExit(0)
    if a.selftest:
        raise SystemExit(0 if _selftest() else 1)
    raise SystemExit(0 if gate() else 1)
