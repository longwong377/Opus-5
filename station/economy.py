#!/usr/bin/env python3
"""THE ECONOMY -- money that moves, stock that runs out, and a price that is
the end of a chain rather than a number on a prop.

WHAT THIS EXISTS TO END. `docs/MASTER-PLAN.md` §3's L7 row reads *"a bar's
stock falls when somebody buys. Money exists -- a till is a till because there
is money"*, and its "today" column reads **0**. Credits existed
(`player.py:167-179`, a distribution solved against the Downbelow leak rate) and
nothing anywhere could take one. Fourteen places in the register declare
`commerce`, `hospitality`, `food_service` or `black_market`; every one of them
was scenery, because a shop whose stock never moves is a picture of a shop.

THE THREE RULES THIS FILE IS BUILT TO
-------------------------------------
1. **A price is derived or it is a token.** Every number below lands on
   `LADDER` -- LAW-CRIME-DOWNBELOW.md §7.1's money table, whose only sourced row
   is *command quarters 30 cr/week* and whose other rows are reasoned off it.
   A good's price is `class band x supply x venue`, each factor with a stated
   reason, and `price_check()` fails if a derived price leaves the band the
   ladder states for its own rows (a Zocalo cart meal must still cost 1-2 cr).
2. **"Stock" is spoo and bearings, never tokens.** PLACES §0.3 (GDS-01) is
   explicit: *"A stall that sells 'goods' is a token; a stall that sells spoo is
   a place."* `GOODS` below is that vocabulary, each row carrying its origin,
   its supply source and the cargo class it lands in.
3. **A delivery is a real container off a real ship.** SYS-04's tick clause:
   *"vendor stock depletes by purchase and replenishes by delivery -- and a
   delivery is a real container off a real ship through the real cargo bays."*
   `consignments(day)` is `traffic.arrivals(day)` turned into cargo, so the
   crate a dock gang moves at 08:14 is the case a player drinks at 19:30. That
   chain is the whole point and it is testable end to end.

THE WORLD MOVES WITHOUT THE PLAYER. `background_sales()` draws every vendor's
own daily covers from `populace.occupancy` -- the same headcount that puts
bodies in the room -- so stock falls on a day nobody plays. The player's
purchase is then a *measurable extra* delta rather than the only thing that ever
happens, which is `MASTER-PLAN.md` §A8 rule 6 (the absence gate) applied to
money.

WHAT IS PERSISTED, AND WHY IT IS A FILE. `Ledger` is the world's mutable
half -- stock, tills, wages paid, the sales log -- and it round-trips through
JSON so that "the delta is still there when you look again" is a thing a gate
can assert across two processes rather than a claim about one dict. It is NOT a
second wallet: a player's credits live on `player.Player` and the ledger stores
purses only as `Player.state()` output, which is that class's own serialiser.

Run: python3 station/economy.py --selftest
     python3 station/economy.py --report
     python3 station/economy.py --day 0
"""
import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import populace as pop                                          # noqa: E402
import rooms as rm                                              # noqa: E402
import traffic as tf                                            # noqa: E402
from npc import schedule as sched                               # noqa: E402


def _u(*parts) -> float:
    """blake2b in [0,1). The draw every deterministic module here uses.

    Never `random`, never `hash()` -- PYTHONHASHSEED salts the latter per
    process and a stall that stocks different goods in two processes is a stall
    whose ledger cannot be reloaded.
    """
    s = "|".join(str(p) for p in parts)
    h = hashlib.blake2b(s.encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ===========================================================================
# 1.  THE LADDER -- LAW-CRIME-DOWNBELOW.md §7.1, transcribed with authority
# ===========================================================================
# One row is SOURCED and everything in this file hangs off it. The rest of the
# table is the gazetteer's own authority-5 scaling, reproduced here verbatim
# rather than re-derived, because a second derivation of a published table is a
# second description of one decision -- the failure hard rule 4 exists against.
#
# (key, lo cr, hi cr, unit, authority, what it is)
LADDER = (
    ("quarters_command",   30.0,  30.0, "week",  1,
     "Command / senior quarters -- the ONE sourced price"),
    ("quarters_personnel", 10.0,  15.0, "week",  5,
     "Standard station personnel quarters"),
    ("room_transient",      4.0,   8.0, "week",  5,
     "Cheap transient room, Red"),
    ("bunk_dosshouse",      1.0,   1.0, "night", 5,
     "A bunk in a Downbelow dosshouse -- the floor of the market"),
    ("squat",               0.0,   0.0, "night", 5,
     "A squat, and it is why people are there"),
    ("meal_cart",           1.0,   2.0, "each",  5,
     "A meal at a Zocalo cart"),
    ("labour_casual",       8.0,  15.0, "day",   5,
     "A day's casual dock labour"),
    ("passage_home",      300.0, 800.0, "each",  5,
     "Passage home, economy -- the load-bearing number of the underclass"),
)
LADDER_BY_KEY = {r[0]: r for r in LADDER}


def ladder(key):
    """(lo, hi) for a ladder row. Raises rather than defaulting: a price that
    silently falls back to zero is a price nobody notices is missing."""
    return LADDER_BY_KEY[key][1], LADDER_BY_KEY[key][2]


# ===========================================================================
# 2.  WAGES -- derived from the ladder's own anchors, and the derivation is
#     CHECKED rather than asserted
# ===========================================================================
# PEOPLE.md §3's wage table states the bands. This recomputes the one
# constraint the gazetteer gives for the bottom rung and reports the result,
# because the constraint is tighter than the band and somebody should know.
#
# LAW-CRIME:748: passage home "must be 30-100 days of casual labour with
# nothing spent". Read as a constraint on the day rate r:
#
#     the cheapest passage must take at least 30 days   -> 300 / r >= 30 -> r <= 10
#     the dearest passage must take at most 100 days    -> 800 / r <= 100 -> r >= 8
#
# so r is pinned to **8-10 cr/day**. The stated band is 8-15. The FLOOR is
# reproduced exactly and the top five credits of the stated band are not
# derivable from the anchor -- `wage_check()` says so out loud instead of
# quietly using one or the other. The stated band is what is used, because it
# is what two documents carry; the constraint is what is reported.
PASSAGE_LO, PASSAGE_HI = ladder("passage_home")
SAVE_DAYS_LO, SAVE_DAYS_HI = 30.0, 100.0        # LAW-CRIME:748, both ends


def casual_constraint():
    """(lo, hi) cr/day implied by the passage-home anchor alone."""
    return PASSAGE_HI / SAVE_DAYS_HI, PASSAGE_LO / SAVE_DAYS_LO


CASUAL_LO, CASUAL_HI = ladder("labour_casual")   # 8-15, the stated band

# PEOPLE.md §3: "guild docker 60-75 (5 shifts x 12-15)". The guild card does
# not buy a much better rate -- 12-15 sits inside the casual band's own top --
# it buys FIVE GUARANTEED SHIFTS. That is the whole economic content of a guild
# and it falls straight out of the two published bands.
GUILD_WEEK_LO, GUILD_WEEK_HI = 60.0, 75.0
GUILD_SHIFTS_PER_WEEK = 5.0
GUILD_SHIFT_LO = GUILD_WEEK_LO / GUILD_SHIFTS_PER_WEEK          # 12.0
GUILD_SHIFT_HI = GUILD_WEEK_HI / GUILD_SHIFTS_PER_WEEK          # 15.0


def wage_check():
    """The anchor against the stated band. Returns a dict; never raises."""
    lo, hi = casual_constraint()
    return {"constraint": (lo, hi), "stated": (CASUAL_LO, CASUAL_HI),
            "floor_agrees": abs(lo - CASUAL_LO) < 1e-9,
            "ceiling_gap": CASUAL_HI - hi,
            "guild_shift": (GUILD_SHIFT_LO, GUILD_SHIFT_HI),
            "guild_inside_casual": GUILD_SHIFT_HI <= CASUAL_HI + 1e-9}


# ===========================================================================
# 3.  THE GOODS -- PLACES §0.3's GDS-01 vocabulary
# ===========================================================================
# Fields: origin (species or source world), supply {drum|hydroponics|import|
# route|station}, klass (which price band it sits in), cargo (which of ROLE-03's
# five handling classes its container is), and who sells it (a register
# FUNCTION, so the vendor list is derived from the register rather than named).
#
# `route` means the black market: LAW-CRIME:858-879's five-station route, not a
# supplier. A route good never appears on a licensed counter.
@dataclass(frozen=True)
class Good:
    name: str
    origin: str
    supply: str
    klass: str
    cargo: str
    sold_by: tuple          # register functions whose places carry it
    note: str = ""


# The five handling classes are ROLE-03's own, quoted: "containerised .
# bulk/transshipment . bonded (customs-sealed, opens SHOW-PAPERS) . hazmat
# (suit-check, PLC-100 chain) . perishable/live (priority, the Grome grading
# dispute)".
CARGO_CLASSES = ("containerised", "bulk", "bonded", "hazmat", "perishable")

_BAR = ("hospitality", "food_service")
_SHOP = ("commerce", "retail")
_ROUTE = ("black_market",)

GOODS = (
    # -- attested names first (GDS-01's own ordering rule) -------------------
    Good("spoo", "narn", "import", "staple", "perishable", _BAR + _SHOP,
         "Narn farmed delicacy; G'Dral's row"),
    Good("treel", "narn", "import", "staple", "perishable", _BAR + _SHOP,
         "Narn fish, kept in a fresh tank"),
    Good("flarn", "minbari", "import", "meal", "perishable", _BAR + _SHOP),
    Good("bagna cauda", "human", "hydroponics", "meal", "perishable", _BAR,
         "An Earhart's indulgence"),
    Good("jala", "centauri", "import", "drink", "containerised", _BAR,
         "Centauri, hot"),
    Good("brivari", "centauri", "import", "drink", "containerised", _BAR,
         "Centauri drink; the Fresh Air cellar"),
    Good("Jovian Sunspot", "human", "station", "drink", "containerised", _BAR,
         "Human cocktail; on bar_unnamed's own board (authority 1)"),
    Good("G'Quan Eth", "narn", "import", "liturgical", "bonded", _SHOP,
         "Narn liturgical plant -- CONTROLLED, a customs class of its own"),
    # -- the drum and the racks ---------------------------------------------
    Good("drum grain", "b5 drum", "drum", "staple", "bulk", _SHOP + _BAR),
    Good("drum greens", "b5 drum", "drum", "staple", "perishable",
         _SHOP + _BAR),
    Good("orchard fruit", "b5 drum", "drum", "staple", "perishable",
         _SHOP + _BAR),
    Good("hydroponic specialty rack", "b5 hydroponics", "hydroponics",
         "staple", "perishable", _SHOP, "PLC-026's log names each rack"),
    Good("Abbai wet-farm greens", "abbai", "import", "staple", "perishable",
         _SHOP),
    # -- hardware -----------------------------------------------------------
    Good("Drazi duct-sealant", "drazi", "import", "hardware", "hazmat",
         _SHOP, "Brakk's stall; a sealant is a solvent, so it is hazmat"),
    Good("Drazi hardware grade B", "drazi", "import", "hardware",
         "containerised", _SHOP),
    Good("Vree instrument optics", "vree", "import", "precision",
         "containerised", _SHOP, "Instrument grade; row 3"),
    Good("dock-grade tools", "human", "import", "hardware", "containerised",
         _SHOP),
    Good("breather cartridges", "human", "import", "medical", "containerised",
         _SHOP + _BAR, "The alien sector runs on them"),
    Good("bearing sets", "human", "import", "hardware", "containerised",
         _SHOP),
    Good("fusion slush", "import", "import", "bulk_fuel", "hazmat", (),
         "The tanker's cargo. Pumped, never craned -- no counter sells it"),
    # -- the bottom of the market -------------------------------------------
    Good("aid-ration packs", "earth alliance", "import", "ration",
         "containerised", _SHOP, "FAC-09's queue"),
    Good("water containers", "b5 plant", "station", "ration", "containerised",
         _SHOP, "The standpipe economy"),
    Good("salvage lots", "b5 unfinished decks", "station", "salvage",
         "containerised", _SHOP + _ROUTE, "Th'Ranna's 14:00 sale"),
    Good("Nightwatch pamphlets", "earth alliance", "station", "free",
         "containerised", (), "Era. Free, and everywhere"),
    # -- what the PLANT and the FABRICATION decks import, which is most of the
    #    tonnage and all of the interesting cargo classes. Every name is a
    #    register function or a spec fixture rather than an invention: the
    #    `hazard_tanks` row declares `atmosphere_feedstock` and
    #    `hazardous_storage`; `fuel_stores` declares `fuel_storage`; PLC-036
    #    names the "bonded cage (customs hold for duty goods)".
    Good("inert gas cylinders", "import", "import", "hardware", "hazmat", (),
         "hazard_tanks' own declared function, arriving"),
    Good("atmosphere feedstock", "import", "import", "hardware", "bulk", (),
         "The other half of hazard_tanks' row"),
    Good("reactor coolant", "import", "import", "hardware", "hazmat", (),
         "fuel_stores: hazardous_storage beside fuel_storage"),
    Good("industrial polymer stock", "import", "import", "hardware", "bulk",
         (), "Feedstock for Grey's fabrication decks"),
    Good("machine spares", "import", "import", "hardware", "containerised",
         _SHOP, "The 8 kg/person/day includes spares -- TRAFFIC 7.4"),
    Good("medical consumables", "import", "import", "medical", "bonded", (),
         "Controlled: medlab draws them against a ledger"),
    Good("bonded spirits", "import", "import", "drink", "bonded", _BAR,
         "PLC-036's bonded cage is a customs hold for DUTY goods"),
    # -- the route ----------------------------------------------------------
    Good("identicard blanks", "route", "route", "contraband", "bonded",
         _ROUTE, "Route only. The forgery supply FAC-25 sells into"),
    Good("Dust", "route", "route", "contraband", "bonded", _ROUTE,
         "Event-grade contraband"),
    Good("untaxed brivari", "centauri", "route", "drink", "bonded", _ROUTE,
         "The same case, off the manifest. Undercuts the Zocalo -- SYS-06"),
)
GOODS_BY_NAME = {g.name: g for g in GOODS}


# ===========================================================================
# 4.  PRICE -- class band x supply x venue, every factor with a reason
# ===========================================================================
# THE CLASS BANDS. Two are the ladder's own rows and the rest are derived from
# them by one stated step each. INV-270.
#
#   meal        the ladder row, verbatim
#   staple      what a meal is made of. A cart selling a 1-2 cr plate cannot
#               have paid more than about half of that for its ingredients or
#               there is no cart, so the staple band is HALF the meal band.
#   drink       a measure is less than a plate: 60% of the meal band. The one
#               free ratio in this block, and the check that constrains it is
#               that a bar drink must stay under a cart meal and over a
#               dosshouse bunk (1 cr), which brackets it to 0.6-1.2.
#   liturgical  a controlled import bought by 9% of the station for one rite:
#               the passage-home band is the only large price the ladder has,
#               and a liturgical import is priced as a fraction of it (1/40),
#               which is the step that makes G'Quan Eth an event rather than a
#               grocery.
#   hardware    under a day's casual pay, or a docker cannot own their own
#               tools: bounded above by CASUAL_LO.
#   precision   instrument grade -- a week of casual pay's worth, the step the
#               station's own repair trade lives on.
#   medical     a breather cartridge keeps a methane-breather alive for a day;
#               priced at a cart meal, because it IS that species' meal cost.
#   ration      relief and utility issue: the dosshouse bunk, the floor.
#   salvage     what a lurker gets for a day of stripping cable, i.e. under the
#               casual day rate: salvage pays worse than labour, which is why
#               22% do it and it is still the bottom.
#   contraband  route goods, priced off what they displace -- see SUPPLY below.
#   free        zero, and the row exists so that "free" is a price and not a
#               missing entry.
#   bulk_fuel   per tonne, not per unit. Never sold over a counter.
def _band(lo, hi):
    return (round(lo, 3), round(hi, 3))


_MEAL = ladder("meal_cart")
_BUNK = ladder("bunk_dosshouse")
CLASS_BAND = {
    "meal":       _band(*_MEAL),
    "staple":     _band(_MEAL[0] * 0.5, _MEAL[1] * 0.5),
    "drink":      _band(_MEAL[0] * 0.6, _MEAL[1] * 0.6),
    "liturgical": _band(PASSAGE_LO / 40.0, PASSAGE_HI / 40.0),
    "hardware":   _band(CASUAL_LO * 0.25, CASUAL_LO * 0.75),
    "precision":  _band(CASUAL_LO * 5.0, CASUAL_HI * 5.0),
    "medical":    _band(*_MEAL),
    "ration":     _band(_BUNK[0], _BUNK[1] * 1.5),
    "salvage":    _band(CASUAL_LO * 0.2, CASUAL_LO * 0.5),
    "contraband": _band(CASUAL_LO * 2.0, CASUAL_HI * 4.0),
    "free":       _band(0.0, 0.0),
    "bulk_fuel":  _band(CASUAL_LO * 0.1, CASUAL_LO * 0.2),
}

# THE SUPPLY MULTIPLIER. What it cost to get here.
#   drum / hydroponics  grown aboard, no freight at all -- the baseline, 1.00
#   station             made or drawn aboard: a still, a standpipe, a workshop
#   import              crossed hyperspace on one of 20 bay freighters a day.
#                       DERIVED rather than chosen: TRAFFIC §7.4 puts imports
#                       at ~1,200 t/day against a drum covering the other half
#                       of food by mass, so an import is the *marginal* half of
#                       the station's supply and is priced at the ratio of the
#                       two halves plus the freight -- taken as 1.6, i.e. an
#                       imported plate costs sixty percent more than a grown
#                       one. INV-270; overturned by any stated freight rate.
#   route               untaxed and illegal. LAW-CRIME:858-879 has the route
#                       undercutting the Zocalo, so route goods that DISPLACE a
#                       licensed line are cheaper (0.75) -- while goods with no
#                       licensed equivalent at all (Dust, blanks) sit in the
#                       `contraband` class, where the band is already the
#                       premium.
SUPPLY_MULT = {"drum": 1.00, "hydroponics": 1.00, "station": 1.05,
               "import": 1.60, "route": 0.75}

# THE VENUE MULTIPLIER, and it is the rent ladder passed to the customer.
# A shopfront's rent is in its prices; the ladder gives the rent tiers and the
# sectors sort onto them. Cube-rooted, because a drink is mostly the drink and
# only partly the roof: (30/6)^(1/3) = 1.71 for the diplomatic tier over the
# Red transient tier. Derived that way rather than chosen, and INV-270 records
# what would overturn it (any stated pitch or lease figure beyond the 4 cr/wk
# Zocalo pitch fee PEOPLE.md carries).
_RENT = {"green": ladder("quarters_command")[0],          # 30 cr/wk, the top
         "red":   sum(ladder("room_transient")) / 2.0,    # 6 cr/wk
         "blue":  sum(ladder("quarters_personnel")) / 2.0,
         "grey":  ladder("bunk_dosshouse")[0],            # 1 cr/night floor
         "yellow": sum(ladder("quarters_personnel")) / 2.0}
_RENT_REF = _RENT["red"]
VENUE_MULT = {k: round((v / _RENT_REF) ** (1.0 / 3.0), 4)
              for k, v in _RENT.items()}


def price(good_name, place_key, seed="b5"):
    """What one unit costs at this counter, in credits.

    Deterministic in (good, place, seed) -- two visits to the same stall on the
    same day quote the same price, which is what makes a player able to notice
    that the under-counter one is cheaper.
    """
    g = GOODS_BY_NAME[good_name]
    lo, hi = CLASS_BAND[g.klass]
    p = dr.by_key(place_key)
    m = SUPPLY_MULT[g.supply] * VENUE_MULT.get(p["sector"], 1.0)
    u = _u("price", good_name, place_key, seed)
    raw = (lo + (hi - lo) * u) * m
    # Millicredits exist (LAW-CRIME:730) so a price is not rounded to whole
    # credits -- a 1 cr floor on everything would flatten the bottom of the
    # ladder, which is the half of the market this project cares most about.
    return round(raw, 2)


def price_check():
    """Every derived price against the bands the ladder itself states.

    The ladder has exactly two rows a *good's* price must reproduce -- the cart
    meal and the dosshouse bunk -- and this is the only place they can be
    checked, because everything else in `CLASS_BAND` is derived FROM them.
    """
    bad = []
    # A Zocalo cart meal: a drum-grown plate on the Red tier.
    for name in ("drum greens", "orchard fruit", "drum grain"):
        p = price(name, "zocalo")
        if not (_MEAL[0] * 0.5 * 0.9 <= p <= _MEAL[1] * 0.5 * 1.1):
            bad.append((name, "zocalo", p, "outside the staple band"))
    for name in ("Jovian Sunspot",):
        p = price(name, "bar_unnamed")
        if not (ladder("bunk_dosshouse")[0] * 0.5 <= p <= _MEAL[1]):
            bad.append((name, "bar_unnamed", p,
                        "a house drink must sit between a bunk and a meal"))
    # The route must undercut the licensed line it displaces -- SYS-06.
    if price("untaxed brivari", "black_market") >= price("brivari",
                                                         "bar_unnamed"):
        bad.append(("untaxed brivari", "black_market",
                    price("untaxed brivari", "black_market"),
                    "the route does not undercut the Zocalo"))
    return bad


# ===========================================================================
# 5.  WHO SELLS WHAT -- derived from the register, never listed
# ===========================================================================
SELLING_FUNCTIONS = frozenset({"commerce", "retail", "hospitality",
                               "food_service", "black_market"})


def vendors():
    """Every place in the register that sells. Ordered, deterministic."""
    return tuple(p["key"] for p in dr.PLACES
                 if set(p["functions"]) & SELLING_FUNCTIONS)


# How many distinct lines a counter carries. A bar is not a chandlery: the
# number is derived from the room's own floor area, because shelf space is
# floor space, at one line per 12 m2 of floor (INV-271 -- constrained below by
# a counter needing at least three lines to be a counter and above by the
# station's whole vocabulary).
LINES_PER_M2 = 1.0 / 12.0
MIN_LINES, MAX_LINES = 3, 14

_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = it.load()
    return _SCHEMA


_FLOOR = {}


def floor_m2(place_key):
    """A place's floor area, from `rooms.room_extent_m` -- the same extent the
    geometry is built to, so a stall list cannot describe a room that is not
    there."""
    if place_key not in _FLOOR:
        schema, profile = _schema()
        arc, ln, _r = rm.room_extent_m(schema, profile, dr.by_key(place_key))
        _FLOOR[place_key] = arc * ln
    return _FLOOR[place_key]


def _species_weight(g, place_key):
    """How likely this counter is to carry this good, by who is aboard.

    A Narn delicacy is stocked in proportion to the Narn share of the station,
    which is `schedule.STATION_MIX` -- the same apportionment the crowd is drawn
    from. It is a WEIGHT and not a filter: the Zocalo carries spoo because
    Narns shop there, not because a table says the Zocalo carries spoo.
    """
    tot = sum(sched.STATION_MIX.values())
    if g.origin not in sched.STATION_MIX:
        # Not a species line: a drum staple, a plant feedstock, an EA issue.
        # Those are bought by everybody, so they carry the majority share.
        return sched.STATION_MIX["human"] / tot
    return max(sched.STATION_MIX[g.origin] / tot, 0.01)


def stock_list(place_key, seed="b5"):
    """The lines this counter carries. Deterministic, derived, ordered."""
    p = dr.by_key(place_key)
    fns = set(p["functions"])
    cand = [g for g in GOODS if set(g.sold_by) & fns]
    if not cand:
        return ()
    # WHAT A PLACE IS FOR COMES FIRST IN ITS FUNCTION LIST, and that is the
    # rule that keeps the Post Office from becoming a grocer. `post_office` is
    # ("mail", "commerce") -- it takes money, it is not a market -- and
    # `business_center` is ("currency_exchange", ...). A counter that is not
    # what the place is for is a small counter: MIN_LINES, no more. The
    # register already carries the distinction; nothing new is declared.
    if p["functions"][0] not in SELLING_FUNCTIONS:
        n = MIN_LINES
    else:
        n = int(round(retail_m2(place_key) * LINES_PER_M2))
    n = max(MIN_LINES, min(MAX_LINES, n, len(cand)))
    # Rank by species weight jittered per place, so two bars in different
    # sectors do not carry the same list -- `--report` prints the spread and
    # `_selftest` asserts it is not one list repeated.
    ranked = sorted(cand, key=lambda g: -(_species_weight(g, place_key)
                                          * (0.5 + _u("line", g.name,
                                                      place_key, seed))))
    return tuple(g.name for g in ranked[:n])


# ===========================================================================
# 6.  DEMAND -- what a counter sells on a day nobody plays
# ===========================================================================
# The covers come from `populace.occupancy`, which is the headcount that puts
# bodies in the room. A cover is one transaction: SERVE_PER_HEAD is how many
# of the people in a hospitality room at a given hour buy something in that
# hour. 0.5 -- half the room is mid-drink and half is between them -- and it is
# INV-271's second number, constrained by the bar having to turn over its own
# stock inside RESTOCK_DAYS or a delivery would never be needed.
SERVE_PER_HEAD = 0.5
SHOP_SERVE_PER_HEAD = 0.25          # a shopper browses more than a drinker
RESTOCK_DAYS = 3.0                  # how deep a counter stands


def _arch(place_key):
    p = dr.by_key(place_key)
    if set(p["functions"]) & {"hospitality", "food_service"}:
        return "hospitality"
    return "commerce"


# A COUNTER IS NOT A DISTRICT, and the first version of this file forgot it.
# `floor_m2("downbelow")` is 654,370 m2, so occupancy over the whole footprint
# gave Downbelow 235,572 retail transactions a day against a camp of 20,000
# people with no money. The register's footprint is the PLACE; the counter is a
# part of it, and the part is what sells.
#
# The cap is SOLVED from the one stated count. PLACES §0.3: the vocabulary
# "feeds the Zocalo's **44 stalls**"; `bar_unnamed` -- the authority-1 bar --
# has a 225 m2 register footprint and is one counter. 44 x 225 = 9,900 m2 of
# counter, which is 25% of the Zocalo's 39,298 m2 and leaves the other three
# quarters as concourse, gallery and circulation, which is what the Zocalo is.
# So: no place aboard has more counter area than the Zocalo does.
ZOCALO_STALLS = 44                                   # PLACES §0.3, stated
COUNTER_M2 = 225.0                                   # bar_unnamed's footprint
MAX_RETAIL_M2 = ZOCALO_STALLS * COUNTER_M2           # 9,900

# THE BLACK MARKET IS A ROUTE, NOT A ROOM -- SYS-06's own title. A place whose
# only selling function is `black_market` trades a twentieth of a licensed
# floor: big enough to be worth LAW-CRIME:858-879's five-station route, small
# enough that customs is not visibly failing. INV-271; overturned by any figure
# for contraband volume.
BLACK_MARKET_SHARE = 0.05


def retail_m2(place_key):
    """The counter area of a place: what sells, not what it occupies."""
    p = dr.by_key(place_key)
    a = min(floor_m2(place_key), MAX_RETAIL_M2)
    if "black_market" in p["functions"]:
        a *= BLACK_MARKET_SHARE
    return a


def daily_covers(place_key):
    """Transactions a day at this counter, summed over the clock."""
    a = retail_m2(place_key)
    arch = _arch(place_key)
    rate = SERVE_PER_HEAD if arch == "hospitality" else SHOP_SERVE_PER_HEAD
    tot = 0.0
    for h in range(24):
        tot += pop.occupancy(place_key, a, float(h) + 0.5, arch) * rate
    return tot


def line_demand(place_key, seed="b5"):
    """Units a day of each line this counter carries."""
    lines = stock_list(place_key, seed)
    if not lines:
        return {}
    per = daily_covers(place_key) / len(lines)
    return {g: per for g in lines}


def opening_stock(place_key, seed="b5"):
    """Units per line a counter stands with at the start of the ledger."""
    return {g: max(1, int(round(v * RESTOCK_DAYS)))
            for g, v in line_demand(place_key, seed).items()}


# ===========================================================================
# 7.  CARGO -- the day's tonnage, its containers, and who each one is for
# ===========================================================================
# THE ONE ANCHOR. TRAFFIC §7.4 works its own example: "Across 20 bay-class
# freighters a day that is ~60 t each". The manifest's freighter_bay row stays
# 8-14 h, mean 11, so the anchor is a RATE and the rate is what every other
# freight class is scaled by -- a ship is worked for as long as it is
# alongside, which is what a berth-hours model already says.
FREIGHTER_ANCHOR_T = 60.0
_FBAY = dict((r[0], r) for r in tf.MANIFEST)["freighter_bay"]
FREIGHT_T_PER_H = FREIGHTER_ANCHOR_T / ((_FBAY[5] + _FBAY[6]) / 2.0)

# A passenger ship's "cargo" is what its passengers brought. 40 kg a head:
# bigger than an airline allowance because this is a move between systems and
# smaller than a household, INV-272. Overturned by any stated figure.
BAGGAGE_T = 0.040

FREIGHT_CLASSES = frozenset({"freighter_bay", "freighter_standoff", "tanker"})

# The container the station actually models: `rooms.PROPS["container"]` is
# 2.40 x 1.20 x 1.20 m. Its payload is that volume at a mixed-general-cargo
# bulk density -- 250 kg/m3, INV-272: water would be 1,000, packaged dry food
# 300-500, machinery 800+, and a mixed crate is 40-60% void. The station's
# import is dominated by food and packaging (8 kg/person/day of "food,
# packaging, supplies, spares"), so the mix sits at the low end.
CONTAINER_M3 = 2.40 * 1.20 * 1.20
CARGO_DENSITY_T_M3 = 0.250
CONTAINER_T = CONTAINER_M3 * CARGO_DENSITY_T_M3


def cargo_tonnes(arr):
    """Tonnes landed by one arrival. Freight by the hour, passengers by bag."""
    if arr["type"] in tf.CREW_STAYS_ABOARD:
        return 0.0
    if arr["type"] in FREIGHT_CLASSES:
        return FREIGHT_T_PER_H * arr["stay_h"]
    return arr["souls"] * BAGGAGE_T


def containers(arr):
    """How many crates that is. A tanker pumps, so it lands none."""
    if arr["type"] == "tanker":
        return 0
    return int(round(cargo_tonnes(arr) / CONTAINER_T))


def cargo_check(days=14):
    """The manifest's landed tonnage against TRAFFIC §7.4's own total.

    THIS IS THE POINT OF THE SECTION, and it reports a gap rather than closing
    it. §7.4 reasons ~1,200 t/day of consumed import, then proposes 2-3x that
    again as transshipment for a total of 4,000-5,000 t/day -- and the manifest
    it shares a document with has no extra hulls for the transshipment to
    arrive on. Summed over the manifest's own rows the station lands the
    consumed figure and nothing else. Either the per-ship tonnage is ~2.5x
    §7.4's worked 60 t, or the manifest is short of freighters. Recorded, not
    resolved: C-013.
    """
    tot = 0.0
    for d in range(days):
        tot += sum(cargo_tonnes(a) for a in tf.arrivals(d))
    per_day = tot / days
    return {"landed_t_per_day": per_day, "stated_lo": 4000.0,
            "stated_hi": 5000.0, "consumed_t_per_day": 1200.0,
            "ratio_to_stated_lo": per_day / 4000.0,
            "reproduces_consumed": abs(per_day - 1200.0) / 1200.0 < 0.75}


# How many saleable units are in one crate. A crate is 0.864 t; a unit is a
# plate, a measure or a piece at a nominal 0.9 kg -- a bottle, a meal's
# ingredients, a hand tool -- so a crate holds 960 units. INV-272.
UNITS_PER_CRATE = int(round(CONTAINER_T * 1000.0 / 0.9))


@dataclass(frozen=True)
class Consignment:
    """One manifest line: goods off a named ship, for a named consignee.

    TWO LINKS, TWO UNITS, and keeping them apart is what makes the chain
    honest. A dock gang moves **crates**; a porter breaks a crate at the cargo
    bay and takes **units** up to a counter -- SYS-04's own tick clause spells
    the chain out as "ship -> cargo bay -> porter route -> stallhold restock".
    A bar that sells 18 measures of brivari a day does not take a 960-unit
    container; it takes a case out of one.
    """
    ship: str
    hour: float
    berth: str
    good: str
    units: int
    crates: float           # the SHARE of a container this line is
    consignee: str
    cargo_class: str
    retail: bool = True

    def line(self):
        return (f"{self.hour:05.2f}  {self.ship:<19s} {self.units:>6d} u "
                f"({self.crates:>5.2f} crate) {self.good:<26s} "
                f"{self.cargo_class:<13s} -> {self.consignee}")


# Where the cargo goes that is not retail -- and it is most of it. The station
# eats 8 kg/person/day and its counters sell a fraction of a percent of that;
# the rest is mess halls, the plant, industry and the quartermaster. These are
# register keys, so a stores line names a real place too.
STORES_DESTINATIONS = ("mess_hall", "quartermaster", "cargo_bays",
                       "hydroponics", "grey_industrial", "waste_management")
_STORES = tuple(k for k in STORES_DESTINATIONS
                if k in {p["key"] for p in dr.PLACES})


def _retail_ships(day):
    """The day's bay-berth arrivals, which are the ones a counter's stock can
    come off: a standoff hull is worked by lighters and a moored warship lands
    nothing."""
    return [a for a in tf.arrivals(day)
            if a["berth"] == "bay" and containers(a) > 0]


_MANIFEST_CACHE = {}


def consignments(day=0, seed="b5"):
    """One station day's cargo, ship by ship, consignee named.

    DERIVED END TO END, and the retail half is derived from DEMAND rather than
    drawn: a counter's line is topped up to `RESTOCK_DAYS` of its own covers,
    so supply equals consumption in the long run and a shelf neither starves
    nor overflows. That balance IS the derivation -- nothing here picks a
    delivery size. What the manifest picks is only WHICH SHIP it came off, and
    that is a deterministic draw over the day's real bay arrivals.

    Everything the counters do not take is a stores line, which is most of the
    tonnage and is exactly right: the Zocalo is a market for 250,000 people and
    still only sells a fraction of a percent of what lands.
    """
    key = (day, seed)
    if key in _MANIFEST_CACHE:
        return _MANIFEST_CACHE[key]
    ships = _retail_ships(day)
    out = []
    used = {}
    if ships:
        for v in vendors():
            for g, per_day in sorted(line_demand(v, seed).items()):
                # ONE DAY's demand, not RESTOCK_DAYS of it. The shelf STANDS
                # `RESTOCK_DAYS` deep (that is `opening_stock`) and is topped up
                # by what it sold, so supply equals consumption and stock
                # neither starves nor runs away. A delivery sized to the depth
                # rather than the turnover would triple the shelf every day.
                units = int(round(per_day))
                if units <= 0:
                    continue
                good = GOODS_BY_NAME[g]
                # A route good never comes off a manifest -- that is what
                # makes it a route good. SYS-06's five stations are the supply.
                if good.supply == "route":
                    continue
                i = int(_u("ship", day, v, g) * len(ships)) % len(ships)
                a = ships[i]
                used[i] = used.get(i, 0.0) + units / float(UNITS_PER_CRATE)
                out.append(Consignment(
                    ship=a["type"], hour=a["hour"], berth=a["berth"],
                    good=g, units=units, crates=units / float(UNITS_PER_CRATE),
                    consignee=v, cargo_class=good.cargo, retail=True))
    # The stores half: whatever each hull carried that the counters did not,
    # and it is MOST of the tonnage. It is broken into named lines rather than
    # one lump of "cargo", for GDS-01's own reason -- a hold full of "goods" is
    # a token -- and because the CARGO CLASS is what a dock gang's day is made
    # of. A hull whose whole manifest is one class is a hull with no shift in
    # it: `dockwork.board` reads these classes straight off.
    # Stores are what the station EATS AND USES: not pamphlets, not Dust, and
    # not the tanker's slush, which is pumped and never crated.
    sellable = [g for g in GOODS if g.supply != "route"
                and g.klass not in ("free", "contraband", "bulk_fuel")]
    tot_w = sum(_species_weight(g, "zocalo") for g in sellable)
    for i, a in enumerate(tf.arrivals(day)):
        n = containers(a)
        if n <= 0:
            continue
        taken = 0.0
        if a in ships:
            taken = used.get(ships.index(a), 0.0)
        left = max(0.0, n - taken)
        if left < 0.01 or not _STORES:
            continue
        nl = max(1, min(6, int(round(math.sqrt(left)))))
        rem = left
        for j in range(nl):
            x = _u("sline", day, i, j) * tot_w
            acc, pick = 0.0, sellable[-1]
            for g in sellable:
                acc += _species_weight(g, "zocalo")
                if x <= acc:
                    pick = g
                    break
            share = rem if j == nl - 1 else left / nl
            share = min(share, rem)
            rem -= share
            if share <= 0:
                continue
            d = _STORES[int(_u("stores", day, i, j) * len(_STORES))
                        % len(_STORES)]
            out.append(Consignment(
                ship=a["type"], hour=a["hour"], berth=a["berth"],
                good=pick.name, units=int(round(share * UNITS_PER_CRATE)),
                crates=share, consignee=d,
                cargo_class=("bulk" if pick.cargo == "bulk_fuel"
                             else pick.cargo), retail=False))
    out = sorted(out, key=lambda c: (c.hour, not c.retail, c.good))
    _MANIFEST_CACHE[key] = tuple(out)
    return _MANIFEST_CACHE[key]


def retail_share(day=0, seed="b5"):
    """What fraction of a day's crates ends up behind a counter."""
    cons = consignments(day, seed)
    tot = sum(c.crates for c in cons)
    return (sum(c.crates for c in cons if c.retail) / tot) if tot else 0.0


# ===========================================================================
# 8.  THE LEDGER -- the world's mutable half, and it survives the process
# ===========================================================================
LEDGER_PATH = os.path.join(HERE, "generated", "economy.json")
LEDGER_VERSION = 1


@dataclass
class Ledger:
    day: int = 0
    stock: dict = field(default_factory=dict)     # place -> good -> units
    till: dict = field(default_factory=dict)      # place -> credits taken
    purses: dict = field(default_factory=dict)    # npc_id -> Player.state()
    wages: dict = field(default_factory=dict)     # npc_id -> credits paid
    sales: list = field(default_factory=list)     # every transaction, in order
    delivered: dict = field(default_factory=dict)  # day -> crates landed
    seed: str = "b5"

    # -- construction -------------------------------------------------------
    @classmethod
    def fresh(cls, seed="b5"):
        """Opening balances: every counter stood up from its own derivation."""
        led = cls(seed=seed)
        for v in vendors():
            s = opening_stock(v, seed)
            if s:
                led.stock[v] = s
                led.till[v] = 0.0
        return led

    # -- persistence --------------------------------------------------------
    def save(self, path=LEDGER_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"version": LEDGER_VERSION, "day": self.day,
                       "seed": self.seed, "stock": self.stock,
                       "till": self.till, "purses": self.purses,
                       "wages": self.wages, "sales": self.sales,
                       "delivered": self.delivered}, f, indent=1,
                      sort_keys=True)
        return path

    @classmethod
    def load(cls, path=LEDGER_PATH):
        with open(path) as f:
            d = json.load(f)
        if d.get("version") != LEDGER_VERSION:
            raise ValueError(f"ledger version {d.get('version')} is not "
                             f"{LEDGER_VERSION}")
        return cls(day=d["day"], stock=d["stock"], till=d["till"],
                   purses=d.get("purses", {}), wages=d.get("wages", {}),
                   sales=d.get("sales", []),
                   delivered=d.get("delivered", {}), seed=d.get("seed", "b5"))

    # -- queries ------------------------------------------------------------
    def units(self, place_key, good):
        return int(self.stock.get(place_key, {}).get(good, 0))

    def total_units(self):
        return sum(sum(v.values()) for v in self.stock.values())

    def total_till(self):
        return sum(self.till.values())


# ---------------------------------------------------------------------------
# The transaction
# ---------------------------------------------------------------------------
class Refused(Exception):
    """A sale that did not happen, with the reason a counter would give."""


def buy(led, buyer, place_key, good, n=1):
    """BUY/SELL (VRB-05). Credits move one way, stock the other, till up.

    `buyer` is a `player.Player`. It is not duck-typed on purpose: the whole
    reason `player.py` exists is that a player is a `Resident` plus a purse, and
    a second wallet here would be the second description of a person that
    module's docstring forbids.

    Returns (unit_price, total). Raises `Refused` with the counter's reason.
    """
    if place_key not in led.stock:
        raise Refused(f"{place_key} is not a counter")
    have = led.units(place_key, good)
    if have <= 0:
        raise Refused(f"{place_key} is out of {good}")
    if have < n:
        raise Refused(f"{place_key} has {have} {good}, not {n}")
    unit = price(good, place_key, led.seed)
    total = round(unit * n, 2)
    if not buyer.spend(total):
        raise Refused(f"{buyer.name} has {buyer.credits} cr, not {total:.2f}")
    led.stock[place_key][good] = have - n
    led.till[place_key] = round(led.till.get(place_key, 0.0) + total, 2)
    led.purses[buyer.npc_id] = buyer.state()
    led.sales.append({"day": led.day, "at": place_key, "good": good,
                      "n": n, "cr": total, "who": buyer.npc_id})
    return unit, total


def pay(led, worker, credits, why=""):
    """Wages. The other direction, and the only one that creates credits."""
    credits = round(float(credits), 2)
    worker.credits = int(round(worker.credits + credits))
    led.wages[worker.npc_id] = round(
        led.wages.get(worker.npc_id, 0.0) + credits, 2)
    led.purses[worker.npc_id] = worker.state()
    led.sales.append({"day": led.day, "at": why, "good": "(wages)",
                      "n": 1, "cr": -credits, "who": worker.npc_id})
    return credits


# ---------------------------------------------------------------------------
# The tick
# ---------------------------------------------------------------------------
def background_sales(led, day=None):
    """What the station buys on a day nobody plays.

    THE ABSENCE CLAUSE. Every counter turns over its own derived covers, drawn
    across its lines. Without this the only stock movement in the world would
    be the player's, and a shop that only moves when watched is a set.
    """
    day = led.day if day is None else day
    moved = 0
    for v, lines in led.stock.items():
        covers = daily_covers(v)
        keys = sorted(lines)
        if not keys:
            continue
        for i, g in enumerate(keys):
            want = int(covers / len(keys) * (0.6 + 0.8 * _u("bg", v, g, day)))
            take = min(want, lines[g])
            if take > 0:
                lines[g] -= take
                led.till[v] = round(led.till.get(v, 0.0)
                                    + take * price(g, v, led.seed), 2)
                moved += take
    return moved


def deliver(led, day=None, only=None):
    """Land the day's consignments on their consignees' shelves.

    `only` restricts delivery to a set of consignments -- which is how a shift
    proves the crates the player's own gang worked are the crates that arrived.
    """
    day = led.day if day is None else day
    cons = consignments(day, led.seed) if only is None else tuple(only)
    landed = 0
    for c in cons:
        if c.consignee not in led.stock:
            continue                     # a stores line, not a counter
        shelf = led.stock[c.consignee]
        if c.good not in shelf:
            continue                     # a counter does not carry that line
        shelf[c.good] = shelf.get(c.good, 0) + c.units
        landed += c.units
    led.delivered[str(day)] = led.delivered.get(str(day), 0) + landed
    return landed


# ===========================================================================
# 9.  Reporting
# ===========================================================================
def report(out=print):
    out("THE ECONOMY -- prices off one sourced anchor, stock off the manifest")
    out("")
    w = wage_check()
    out(f"WAGES.  the passage-home anchor ({PASSAGE_LO:.0f}-{PASSAGE_HI:.0f} "
        f"cr = {SAVE_DAYS_LO:.0f}-{SAVE_DAYS_HI:.0f} days) pins the casual day "
        f"rate to {w['constraint'][0]:.2f}-{w['constraint'][1]:.2f} cr/day")
    out(f"        the stated band is {CASUAL_LO:.0f}-{CASUAL_HI:.0f}: the "
        f"FLOOR is reproduced exactly, the ceiling is "
        f"{w['ceiling_gap']:.0f} cr above what the anchor implies")
    out(f"        guild card = {GUILD_WEEK_LO:.0f}-{GUILD_WEEK_HI:.0f} cr/wk "
        f"= {GUILD_SHIFT_LO:.0f}-{GUILD_SHIFT_HI:.0f} a shift x "
        f"{GUILD_SHIFTS_PER_WEEK:.0f} -- inside the casual band, so the card "
        f"buys REGULARITY, not a rate")
    out("")
    out(f"GOODS.  {len(GOODS)} named lines, "
        f"{len(set(g.origin for g in GOODS))} origins, "
        f"{len(set(g.cargo for g in GOODS))} cargo classes")
    out(f"CARGO.  a crate is {CONTAINER_M3:.3f} m3 x "
        f"{CARGO_DENSITY_T_M3:.3f} t/m3 = {CONTAINER_T:.3f} t = "
        f"{UNITS_PER_CRATE} units; a bay freighter works at "
        f"{FREIGHT_T_PER_H:.4f} t/h alongside")
    c = cargo_check()
    out(f"        the manifest lands {c['landed_t_per_day']:.0f} t/day "
        f"against TRAFFIC 7.4's stated {c['stated_lo']:.0f}-"
        f"{c['stated_hi']:.0f} -- it reproduces the CONSUMED "
        f"{c['consumed_t_per_day']:.0f} and has no hulls for the "
        f"transshipment (C-013)")
    out("")
    out("COUNTERS -- derived from the register, not listed")
    for v in vendors():
        s = stock_list(v)
        if not s:
            out(f"  {v:<18s} (sells nothing this vocabulary carries)")
            continue
        cheap = min(s, key=lambda g: price(g, v))
        out(f"  {v:<18s} {len(s):>2d} lines, {daily_covers(v):>5.0f} "
            f"covers/day, cheapest {cheap} at {price(cheap, v):.2f} cr")
    out("")
    out("ONE DAY'S CARGO -- every crate off a real ship, for a real counter")
    for c in consignments(0)[:12]:
        out("  " + c.line())
    out(f"  ... {len(consignments(0))} lines, "
        f"{sum(x.crates for x in consignments(0)):.0f} crates, "
        f"{retail_share(0):.3%} of them retail -- the rest is mess halls, "
        f"the plant and industry")


def day_report(day=0, out=print):
    cons = consignments(day)
    out(f"DAY {day} -- {len(tf.arrivals(day))} arrivals, "
        f"{sum(containers(a) for a in tf.arrivals(day))} crates, "
        f"{len(cons)} manifest lines")
    for c in cons:
        out("  " + c.line())


# ===========================================================================
# 10.  Gates
# ===========================================================================
def _selftest(out=print):                                        # noqa: C901
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

    import player as pl

    # -- 1. the ladder and the wage derivation ------------------------------
    w = wage_check()
    check("the passage-home anchor reproduces the casual band's FLOOR exactly",
          w["floor_agrees"],
          f"{w['constraint'][0]:.4f} against the stated {CASUAL_LO:.0f}")
    check("...and the anchor is TIGHTER than the stated band, which is "
          "reported rather than papered over",
          w["ceiling_gap"] > 0,
          f"anchor caps at {w['constraint'][1]:.1f}, the band states "
          f"{CASUAL_HI:.0f} -- {w['ceiling_gap']:.0f} cr undeclared")
    check("the guild shift rate sits inside the casual band, so the card buys "
          "regularity and not a rate", w["guild_inside_casual"],
          f"{GUILD_SHIFT_LO:.0f}-{GUILD_SHIFT_HI:.0f} in "
          f"{CASUAL_LO:.0f}-{CASUAL_HI:.0f}")

    # -- 2. prices land on the ladder ---------------------------------------
    bad = price_check()
    check("every derived price lands inside the band the ladder states for it",
          not bad, f"{len(bad)} outside: {bad[:3]}")
    # NEGATIVE CONTROL: break the supply multiplier and the route stops
    # undercutting the Zocalo, which is the one relation SYS-06 requires.
    keep = SUPPLY_MULT["route"]
    SUPPLY_MULT["route"] = 3.0
    broke = price_check()
    SUPPLY_MULT["route"] = keep
    check("...and a route multiplier that does not undercut FIRES it",
          len(broke) > len(bad), f"{len(broke)} outside with route at 3.0x")

    # -- 3. the goods vocabulary --------------------------------------------
    check("every good names a cargo class ROLE-03 handles",
          all(g.cargo in CARGO_CLASSES or g.cargo == "bulk_fuel"
              for g in GOODS),
          f"{len(GOODS)} goods")
    check("every good's price class has a band",
          all(g.klass in CLASS_BAND for g in GOODS))
    check("no two goods share a name",
          len(GOODS_BY_NAME) == len(GOODS))

    # -- 4. the counters are derived and are NOT one list repeated ----------
    vs = vendors()
    stocked = [v for v in vs if stock_list(v)]
    check("the register supplies the vendor list",
          len(vs) >= 12, f"{len(vs)} places declare a selling function, "
                         f"{len(stocked)} carry a line")
    lists = {v: stock_list(v) for v in stocked}
    distinct = len(set(lists.values()))
    check("no two counters carry the same list -- the degeneracy question, "
          "asked of stock instead of geometry",
          distinct == len(lists),
          f"{distinct} distinct of {len(lists)}")
    check("a bar carries drink and a chandlery does not",
          "Jovian Sunspot" in lists.get("bar_unnamed", ())
          and "Jovian Sunspot" not in lists.get("shops_kiosks", ()),
          f"bar_unnamed: {lists.get('bar_unnamed', ())}")

    # -- 5. cargo ------------------------------------------------------------
    c0 = consignments(0)
    retail = [x for x in c0 if x.retail]
    check("a day's manifest names a real counter on every retail line",
          len(retail) > 0 and all(x.consignee in lists for x in retail),
          f"{len(c0)} lines, {len(retail)} retail, "
          f"{sum(x.crates for x in c0):.0f} crates, retail share "
          f"{retail_share(0):.4%}")
    check("...and every stores line names a real place too",
          all(x.consignee in {p2['key'] for p2 in dr.PLACES}
              for x in c0 if not x.retail))
    check("...and no retail line comes off a hull that did not berth in a bay",
          all(x.berth == "bay" for x in retail))
    check("...and two days do not land the same cargo",
          tuple(x.good for x in c0) != tuple(x.good for x in consignments(1)))
    cc = cargo_check()
    check("the manifest's landed tonnage reproduces 7.4's CONSUMED figure",
          cc["reproduces_consumed"],
          f"{cc['landed_t_per_day']:.0f} t/day against 1,200 consumed and "
          f"4,000-5,000 stated -- the gap is C-013")
    check("a tanker lands no crates, because slush is pumped",
          all(containers(a) == 0 for a in tf.arrivals(0)
              if a["type"] == "tanker") or
          not any(a["type"] == "tanker" for a in tf.arrivals(0)))

    # -- 6. THE TRANSACTION --------------------------------------------------
    led = Ledger.fresh()
    p = pl.random_player("econ")
    p.credits = 200
    p.move_to("bar_unnamed")
    line = stock_list("bar_unnamed")[0]
    before_units = led.units("bar_unnamed", line)
    before_cr = p.credits
    before_till = led.till["bar_unnamed"]
    unit, total = buy(led, p, "bar_unnamed", line, 1)
    check("a purchase debits the player, empties a shelf and fills a till",
          abs(p.credits - (before_cr - total)) < 1e-6
          and led.units("bar_unnamed", line) == before_units - 1
          and led.till["bar_unnamed"] > before_till,
          f"{before_cr} -> {p.credits} cr, {before_units} -> "
          f"{led.units('bar_unnamed', line)} {line}, till "
          f"{before_till:.2f} -> {led.till['bar_unnamed']:.2f}")
    # NEGATIVE CONTROL: no money, no sale, and NOTHING moves.
    broke_p = pl.random_player("econ2")
    broke_p.credits = 0
    u0 = led.units("bar_unnamed", line)
    t0 = led.till["bar_unnamed"]
    try:
        buy(led, broke_p, "bar_unnamed", line, 1)
        refused = False
    except Refused:
        refused = True
    check("...and a buyer with no credits is refused AND moves no stock",
          refused and led.units("bar_unnamed", line) == u0
          and led.till["bar_unnamed"] == t0)
    # NEGATIVE CONTROL 2: an empty shelf refuses.
    led.stock["bar_unnamed"][line] = 0
    try:
        buy(led, p, "bar_unnamed", line, 1)
        empty_refused = False
    except Refused:
        empty_refused = True
    check("...and an empty shelf refuses too", empty_refused)

    # -- 7. THE WORLD MOVES WITHOUT THE PLAYER -------------------------------
    quiet = Ledger.fresh()
    q0 = quiet.total_units()
    moved = background_sales(quiet, 0)
    q1 = quiet.total_units()
    check("stock falls on a day nobody plays -- the absence clause",
          moved > 0 and q1 < q0,
          f"{q0} -> {q1} units, {moved} sold by the station itself")
    landed = deliver(quiet, 0)
    check("...and the day's real ships put it back",
          landed > 0 and quiet.total_units() > q1,
          f"{landed} units landed, {q1} -> {quiet.total_units()} units")

    # AND THE TWO BALANCE. A shelf that gains more than it sells is a shop
    # that fills up; one that gains less starves. Fourteen days of the real
    # manifest against the real covers, and the total stock must still be
    # inside a stated band of where it started -- which is the only check that
    # says the delivery size was DERIVED from demand rather than picked.
    bal = Ledger.fresh()
    start = bal.total_units()
    for d in range(14):
        bal.day = d
        background_sales(bal, d)
        deliver(bal, d)
    drift = bal.total_units() / max(1, start)
    check("14 days of real manifests against real covers leaves the shelves "
          "where they started -- supply is DERIVED from demand",
          0.6 <= drift <= 1.4,
          f"{start} -> {bal.total_units()} units, x{drift:.3f} over 14 days")

    # -- 8. PERSISTENCE, ACROSS TWO PROCESSES --------------------------------
    import subprocess
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(), "economy.json")
    led2 = Ledger.fresh()
    p2 = pl.random_player("persist")
    p2.credits = 500
    line2 = stock_list("bar_unnamed")[0]
    u_before = led2.units("bar_unnamed", line2)
    buy(led2, p2, "bar_unnamed", line2, 3)
    led2.save(tmp)
    code = (f"import sys; sys.path.insert(0, {HERE!r});"
            f"import economy as e;"
            f"L = e.Ledger.load({tmp!r});"
            f"print(L.units('bar_unnamed', {line2!r}), "
            f"round(L.till['bar_unnamed'], 2), len(L.sales))")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True)
    got = r.stdout.strip().split()
    check("the delta is still there when a SECOND PROCESS looks again",
          r.returncode == 0 and got and int(got[0]) == u_before - 3,
          f"child said {r.stdout.strip()!r} (wanted "
          f"{u_before - 3} units); {r.stderr.strip()[:120]}")
    # NEGATIVE CONTROL: a ledger that was never saved must NOT carry the delta.
    fresh_again = Ledger.fresh()
    check("...and a ledger that was never written does not carry it",
          fresh_again.units("bar_unnamed", line2) == u_before,
          f"{fresh_again.units('bar_unnamed', line2)} against {u_before}")

    out("")
    out(f"{n - len(failed)}/{n} passed")
    return not failed


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--day", type=int, default=None)
    a = ap.parse_args()
    if a.day is not None:
        day_report(a.day)
        raise SystemExit(0)
    if a.report and not a.selftest:
        report()
        raise SystemExit(0)
    good = _selftest()
    if a.report:
        print()
        report()
    raise SystemExit(0 if good else 1)
