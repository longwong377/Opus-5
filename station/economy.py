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
    # PLY-03's TOP RUNG, and it was missing from a ladder the row calls
    # "climbable": THE-STATION.md:172 gives the player's own ladder as
    # "transient 4-8 cr/wk -> civilian 10-15 -> hotel/business class, filed at
    # PLC-032", and the first two were rows here while the third was not, so
    # the thing the row says you climb TO had no price. INV-720.
    #
    # DERIVED IN ONE STEP FROM EACH OF THE TWO ROWS THAT BRACKET IT, rather
    # than picked:
    #   floor  = `quarters_command`, the ONE sourced price in this table. A
    #            commercial let cannot sensibly undercut what the station
    #            values its own senior tenancy at, and 30 is the only figure
    #            here with authority 1 behind it.
    #   spread = the civilian row's own, 15/10 = x1.5, applied to that floor.
    #            The published table gives exactly one width for a residential
    #            rung and re-using it is one decision instead of two.
    # -> 30-45 cr/week, which is 3-5.6 days of the `labour_casual` band, so it
    # is a SINK for a lurker and ordinary for a trader -- which is what "one of
    # SYS-04's three late-game sinks" has to mean arithmetically.
    # OVERTURNED BY: any stated hotel or business-let rate; PLACES.md:1957's
    # four Red hotels acquiring a tariff.
    ("room_hotel",         30.0,  45.0, "week",  5,
     "Hotel / business class -- PLY-03's top rung, filed at PLC-032"),
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

    # =======================================================================
    # THE 4t WIDENING -- 34 lines to the GDS-01 floor of 60. INV-721.
    # =======================================================================
    # WHY IT IS HERE AND NOT SPREAD ACROSS THE BLOCKS ABOVE: those blocks are
    # the seed set PLACES §0.3 names, in the order that annex names it, and
    # `gds.py`'s seed matcher reads them. Interleaving twenty-eight new lines
    # through them would make the seed sentence's residue impossible to read.
    #
    # AND WHY WIDENING WAS NEEDED AT ALL, which is not the floor. The floor is
    # a number; the reason is the SELL verb below. A vocabulary of 34 lines,
    # 27 of which only a licensed counter carries, gives a player nothing to
    # dispose of -- so `sell()` would have been a function with no content the
    # way `stream.gd` was a mover with nobody to move. Every block below is
    # something somebody in this station would put on a counter and somebody
    # else would carry away.

    # -- (a) HOUSEHOLD GOODS -- PLY-03's vendor, and the sink it names -------
    # THE-STATION.md:172: "A **household-goods vendor** exists (a named keeper
    # among PLC-052's shops)" and "the top tier plus furnishing it is one of
    # SYS-04's three late-game sinks". A sink needs things to buy.
    #
    # THE BAND IS ONE STEP OFF A PUBLISHED ROW: a durable furnishing costs
    # about a week of the rent of the unit it furnishes, so `household` IS the
    # `quarters_personnel` row, 10-15 cr. Eight items is then 80-120 cr against
    # an 8-15 cr/day casual wage -- eight days' work to furnish a room, which
    # is a sink a player feels and a lurker cannot reach. INV-721.
    #
    # SUPPLY: Grey's fabrication decks already have `industrial polymer stock`
    # above as their declared feedstock, so a moulded durable is made ABOARD
    # (`station`); the two that are not moulded are shipped.
    Good("bunk mattress", "b5 fabrication", "station", "household", "bulk",
         _SHOP, "PLC-052's household keeper; moulded from polymer stock"),
    Good("storage locker", "b5 fabrication", "station", "household",
         "containerised", _SHOP, "Where a placed prop goes -- VRB-03"),
    Good("shelf unit", "b5 fabrication", "station", "household",
         "containerised", _SHOP,
         "PLY-03's CHECK names the unit's SHELF by name"),
    Good("folding chair", "b5 fabrication", "station", "household",
         "containerised", _SHOP),
    Good("lamp panel", "earth alliance", "import", "household",
         "containerised", _SHOP, "A quarters light that is not the ceiling"),
    Good("water jug", "human", "import", "household", "containerised", _SHOP,
         "The standpipe economy needs something to carry it in"),
    Good("cook ring", "earth alliance", "import", "household", "hazmat",
         _SHOP, "An induction ring: mains current in a residence, so hazmat"),
    Good("privacy curtain", "human", "import", "household", "containerised",
         _SHOP, "Downbelow's own architecture, sold legitimately in Red"),

    # -- (b) WHAT A LURKER SELLS -- the fence's supply side ------------------
    # LAW-CRIME 6.2 puts 22% of the underclass on salvage and this file already
    # prices the `salvage` class at "under the casual day rate: salvage pays
    # worse than labour, which is why 22% do it and it is still the bottom".
    # `salvage lots` was ONE line standing for all of it. These are the four
    # things the same person actually carries up out of the unfinished decks,
    # and they are what makes `sell()` a verb rather than a function.
    Good("stripped cable", "b5 unfinished decks", "station", "salvage",
         "bulk", _SHOP + _ROUTE, "A day of stripping cable, LAW-CRIME 6.2"),
    Good("scrap plating", "b5 unfinished decks", "station", "salvage", "bulk",
         _SHOP + _ROUTE),
    Good("used breather filters", "b5 unfinished decks", "station", "salvage",
         "containerised", _ROUTE,
         "Re-packed and re-sold: the alien sector's grey trade"),
    Good("recovered data crystals", "b5 unfinished decks", "station",
         "salvage", "containerised", _ROUTE,
         "What is ON them is why the fence and not the shop"),

    # -- (c) THE ROUTE, WIDENED -- SYS-06's five stations carry more than three
    # LAW-CRIME:858-879's route is a supply chain and a chain that moves three
    # lines is a prop. Each of these displaces a named licensed line above, so
    # `SUPPLY_MULT["route"]`'s undercut has something to undercut.
    Good("untaxed jala", "centauri", "route", "drink", "bonded", _ROUTE,
         "Displaces `jala`, off the manifest"),
    Good("unlicensed breathers", "route", "route", "medical", "bonded",
         _ROUTE, "Displaces `breather cartridges`; nobody certifies these"),
    Good("black-market spoo", "narn", "route", "staple", "perishable", _ROUTE,
         "Displaces `spoo`. A perishable on the route is a short window"),
    Good("stolen tool sets", "route", "route", "hardware", "containerised",
         _ROUTE, "8.2's petty theft, arriving at the other end"),
    Good("forged transit visas", "route", "route", "contraband", "bonded",
         _ROUTE, "The other half of `identicard blanks` -- FAC-25's trade"),
    Good("weapons parts", "route", "route", "contraband", "bonded", _ROUTE,
         "8.2 smuggling_military: 'Rare, enormous.' Off the fine ladder"),

    # -- (d) WHAT THE SHOW PUT ON A COUNTER, and what 250,000 people need ----
    # Era-locked S2-3 and each one traceable to something already in this
    # repository rather than to a memory: the species mix `schedule` carries,
    # the fixtures `rooms.FIXTURES` names, the classes `traffic` lands.
    Good("Centauri hair oils", "centauri", "import", "household",
         "containerised", _SHOP,
         "9% of the station is Centauri and the Republic's grooming is a plot "
         "point in its own right"),
    Good("Minbari tea", "minbari", "import", "drink", "containerised",
         _BAR + _SHOP),
    Good("Narn ration bricks", "narn", "import", "ration", "containerised",
         _SHOP, "What the Regime issues its own nationals in transit"),
    Good("Drazi fermented cakes", "drazi", "import", "meal", "perishable",
         _BAR),
    Good("pak'ma'ra carrion stock", "pak'ma'ra", "import", "staple",
         "perishable", _SHOP,
         "INC-PAKMA's 04:00 meal has to come from somewhere"),
    Good("Vree memory cores", "vree", "import", "precision", "containerised",
         _SHOP, "The other half of `Vree instrument optics`"),
    Good("Abbai water reclaim units", "abbai", "import", "household",
         "containerised", _SHOP, "A water species sells water hardware"),
    Good("Llort scrap consignments", "llort", "import", "salvage", "bulk",
         _SHOP + _ROUTE,
         "PEOPLE.md CAST-41: 'Llort suppliers overnight' at the fence"),
    Good("EarthForce ration issue", "earth alliance", "import", "ration",
         "containerised", _SHOP, "Free at a mess, priced at a stall"),
    Good("hydroponic seed stock", "b5 hydroponics", "hydroponics", "staple",
         "perishable", _SHOP, "PLC-026's racks come from somewhere"),
    Good("drum dairy", "b5 drum", "drum", "staple", "perishable",
         _SHOP + _BAR, "The Grome's herds -- FAC-21's grading dispute"),
    Good("drum fibre", "b5 drum", "drum", "hardware", "bulk", _SHOP,
         "What `privacy curtain` and a station's cordage are woven from"),
    Good("pitch-fee scrip", "b5 station", "station", "licence",
         "containerised", _SHOP,
         "PEOPLE.md's 4 cr/wk Zocalo pitch fee, as the chit a stallholder "
         "buys at PLC-032 and shows to a patrol. GDS-01's own seed set names "
         "it and no row carried it"),
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
    # -- the two classes the 4t widening needed, one step each. INV-721 -----
    #   household   a durable furnishing costs about a week of the rent of the
    #               unit it furnishes, so the band IS `quarters_personnel`.
    #               Eight of them furnish a room for 80-120 cr, which against
    #               the 8-15 cr/day casual band is the eight days of work
    #               PLY-03 needs its "late-game sink" to be.
    #   licence     NOT derived at all: PEOPLE.md:758 states the Zocalo pitch
    #               fee as 4 cr/wk against TRAFFIC:630-643, so the band is that
    #               figure, both ends, and it is the second SOURCED price in
    #               this file after `quarters_command`.
    "household":  _band(*ladder("quarters_personnel")),
    "licence":    _band(4.0, 4.0),
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

    A SERVICE COMES THROUGH HERE TOO, and it is one line rather than a second
    function because every consumer in the project -- `interact.counter_offer`,
    `background_sales`, `buy`, `lines_at`, `godot/scripts/interact.gd`'s baked
    `cr` field -- asks this one question. A second price function would be a
    second answer to it, which is hard rule 4 at the scale of an arithmetic.
    """
    if good_name in SERVICE_BY_NAME:
        return service_price(good_name, place_key)
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
    # AND EVERY SERVICE IS ITS LADDER ROW TO THE MILLICREDIT. There is no band
    # to be inside here -- the price IS the published floor -- so this checks
    # identity rather than membership, which is the strongest form the claim
    # has and the one that fails if anybody re-introduces a draw.
    for s in SERVICES:
        want = round(ladder(s.ladder or "squat")[0], 2)
        for k in tuple(p["key"] for p in dr.PLACES
                       if s.function in p["functions"]):
            got = price(s.name, k)
            if abs(got - want) > 1e-9:
                bad.append((s.name, k, got,
                            f"is not the {s.ladder or 'squat'} row's "
                            f"{want:.2f}"))
    return bad


# ===========================================================================
# 4a.  THE BID -- what a counter PAYS, which is the other half of a price
# ===========================================================================
# VRB-05 IS "BUY/SELL" AND HALF OF IT WAS NEVER BUILT. `spec_check.py --red`
# said so in the row's own words -- *"the buy side is consequence.purchase; the
# sell side is not implemented -- no sell/fence entry point exists"* -- and a
# verb the spec enumerates with no entry point is the shape of defect this
# project has produced nine times, arriving from the other direction: not
# machinery with no caller, but a caller (the spec) with no machinery.
#
# NOT ONE NEW NUMBER IS INTRODUCED HERE, and that is deliberate. Both factors
# below are ratios this file already derived for other purposes, re-read:
#
#   BUY_BACK = 0.5.  `CLASS_BAND` derives the `staple` band as HALF the `meal`
#       band on a stated argument -- *"a cart selling a 1-2 cr plate cannot
#       have paid more than about half of that for its ingredients or there is
#       no cart"*. That sentence IS a buy-back rate: it says what a counter
#       pays for a unit of what it sells. A counter taking a line back over
#       its own counter pays what it pays a supplier, because it is buying the
#       same thing. Using the number twice for one decision is the point;
#       inventing a second margin would be two answers to one question.
#
#   FENCE_TAKE = SUPPLY_MULT["route"] = 0.75.  A fence does not keep what it
#       buys, it moves it on the route -- and the route already sells at 0.75
#       of the licensed line it displaces (LAW-CRIME:858-879, SYS-06). So the
#       fence's own shelf is worth 0.75 of a licit shelf and its bid is 0.75
#       of a licit bid. The fence pays 37.5% of a shopfront's price against a
#       shopfront's 50%.
#
# AND THAT SPREAD IS THE WHOLE MECHANIC. The fence pays WORSE and is the only
# buyer for what a licensed reader will not touch, which is exactly what
# FACTIONS 11.4 says the black market is for. A player with a clean card and a
# clean crate goes to a shop; everybody else goes to Solly Vane. INV-722.
BUY_BACK = 0.5
FENCE_TAKE = SUPPLY_MULT["route"]                                # 0.75

# THE NAMED FENCE. PEOPLE.md's CAST row 41, quoted: `41 | Solly Vane | hum M 44
# | the fence, black_market stall | subfloor_stack | buys 14:00-02:00; Llort
# suppliers overnight`. The hours are his, not ours.
#
# AND THE REGISTER DISAGREES WITH THAT ROW, which is reported rather than
# papered over: `directory.by_key("subfloor_stack")["functions"]` is
# ("services", "informal_residence", "storage") -- no `black_market`, so the
# place CAST-41 files him at is not a counter and `sell()` will refuse there in
# so many words. `fence_places()` returns the places that actually trade, and
# `fence_register_gap()` is the finding, printed by `--trade`. Closing it is a
# one-tuple edit in `directory.py`, which this module does not own.
FENCE_NAME = "Solly Vane"
FENCE_FILED_AT = "subfloor_stack"                    # PEOPLE.md CAST row 41
FENCE_HOURS = (14.0, 2.0)                            # buys 14:00-02:00

# The named household keeper PLY-03 asks for: *"A household-goods vendor
# exists (a named keeper among PLC-052's shops)"*. PLC-052 is `shops_kiosks`,
# whose register functions are ("commerce", "retail") -- so the keeper's stall
# is derived from the register exactly the way `Good.sold_by` is, and the name
# is the only authored thing about it. `npc/names.py`'s human grammar is what
# an in-world nameplate would draw from; this is one draw from it, fixed so a
# save can refer to it. INV-723.
HOUSEHOLD_GOODS_FUNCTION = "retail"
HOUSEHOLD_KEEPER = ("Ada Roskoe", "shops_kiosks")


def household_goods():
    """PLY-03's furnishing catalogue: every `household` line, ordered."""
    return tuple(g.name for g in GOODS if g.klass == "household")


def household_vendor():
    """(keeper, place, what they sell). The named keeper among PLC-052's."""
    name, key = HOUSEHOLD_KEEPER
    return name, key, tuple(n for n in goods_list(key)
                            if GOODS_BY_NAME[n].klass == "household")


def fence_places():
    """Every counter with no reader on it -- where a fence can actually trade.

    Derived from `consequence.UNCHECKED_FUNCTIONS` via the register, never
    listed. Imported lazily: `consequence` imports THIS module at its top, so a
    module-level import here would be a cycle that takes both files down.
    """
    import consequence as _cq                                # noqa: PLC0415
    return tuple(p["key"] for p in dr.PLACES
                 if set(p["functions"]) & _cq.UNCHECKED_FUNCTIONS
                 and set(p["functions"]) & SELLING_FUNCTIONS)


def fence_register_gap():
    """(ok, note) -- does the register agree with PEOPLE.md's CAST row 41."""
    fns = tuple(dr.by_key(FENCE_FILED_AT)["functions"])
    ok = FENCE_FILED_AT in fence_places()
    return ok, (f"CAST-41 files {FENCE_NAME} at `{FENCE_FILED_AT}` and the "
                f"register gives it {fns} -- no unchecked SELLING function, so "
                f"it is not a counter. Trading fences: "
                f"{', '.join(fence_places())}")


def unchecked(place_key):
    """Is this counter one the reader does not cover -- i.e. a fence."""
    import consequence as _cq                                # noqa: PLC0415
    return bool(set(dr.by_key(place_key)["functions"])
                & _cq.UNCHECKED_FUNCTIONS)


def bid(good_name, place_key, seed="b5"):
    """What this counter PAYS for one unit, in credits. The mirror of `price`.

    Deterministic in exactly the same (good, place, seed) as `price`, because
    it IS `price` times a constant -- which is what makes the spread a fact a
    player can learn rather than a draw they cannot.
    """
    p = round(price(good_name, place_key, seed) * BUY_BACK
              * (FENCE_TAKE if unchecked(place_key) else 1.0), 2)
    # A counter that pays a whole credit for a 0.66 cr drink is a money pump,
    # and rounding to 2 dp can reach zero from below. Millicredits exist
    # (LAW-CRIME:730) and a zero bid is a real answer for a `free` line.
    return max(0.0, p)


def spread(good_name, place_key, seed="b5"):
    """(bid, price, price - bid). What the counter makes on a round trip."""
    a, b = bid(good_name, place_key, seed), price(good_name, place_key, seed)
    return a, b, round(b - a, 2)


def buys_list(place_key, seed="b5"):
    """What this counter will take OFF you. Derived, never listed.

    THE TWO RULES ARE THE WHOLE CONTENT OF THE VERB and both come from rules
    already in this project:

      a licensed counter buys back ONLY ITS OWN LINES -- a chandlery has no
        use for a plate of flarn and no shelf to put it on -- and never a
        `bonded` or `route` line, because the identicard IS the credit card
        (INV-342) so a payout is a named transaction and a named transaction
        against a customs-sealed good is `consequence.OFFENCE["contraband"]`.

      a FENCE buys anything, because there is no reader on the counter
        (FACTIONS 11.4) and it does not keep what it buys.
    """
    if unchecked(place_key):
        return tuple(g.name for g in GOODS)
    return tuple(n for n in goods_list(place_key, seed)
                 if GOODS_BY_NAME[n].cargo != "bonded"
                 and GOODS_BY_NAME[n].supply != "route")


# ===========================================================================
# 4b.  SERVICES -- what a station takes money for that is not a unit of stock
# ===========================================================================
# WHAT THIS EXISTS TO END, MEASURED. Before session 4r the whole economy was a
# SHOP: `GOODS` is 33 lines of spoo and bearings and every one of them is a
# thing you carry away. So `vendors()` was 13 places, `interact.counter_offer`
# said `sells: False` everywhere else, and the shipped boot deck -- `blue_0_0`,
# where a player actually spawns -- carried **one** `serve` interactable
# (`docking_bays__prop_bay_control_booth`) which sold **nothing**. Counting the
# whole register: 28 places declare a prop whose verb is `serve` and **9** of
# them could take a credit. In the build a player launches, the number was ZERO.
#
# And the ladder this file is built on has always known better. Four of its
# eight rows are not goods at all:
#
#     quarters_command  30 cr/week    -- THE one sourced price in the project
#     room_transient    4-8 cr/week
#     bunk_dosshouse    1 cr/night    -- "the floor of the market"
#     passage_home      300-800 cr    -- "the load-bearing number of the
#                                        underclass"
#
# A player could see every one of those prices in `--report` and pay none of
# them. `dockwork.py`'s fourteen-day loop walks a Downbelow lurker from 267 to
# 420.50 credits and 420.50 is ABOVE the 300 cr passage floor -- so the arc
# this repository already ships had no ending, because nothing sold the ticket.
#
# THE THREE RULES, and they are the goods rules applied to a second noun:
#
# 1. **A service's price is a LADDER ROW, verbatim where one exists.**  INV-560 No supply
#    multiplier and no venue multiplier: those two exist because a good has to
#    cross hyperspace and pay rent on a shopfront before it reaches a counter,
#    and a berth on a ship does neither -- the ladder's 300-800 already IS the
#    fare. The one service with no row of its own (`a stake at the table`)
#    takes another row with ONE stated step, and it says which.
# 2. **A service is stocked and replenished by exactly the goods rule** --
#    demand x RESTOCK_DAYS at open, one day's demand back each day -- and the
#    only difference is what the delivery IS. A crate comes off a ship;
#    a bunk-night comes back because tomorrow is another night. `deliver()`
#    does both, and says so.
# 3. **The daily demand is a REAL physical count wherever one exists.** INV-561 Passage
#    home is free berths on the hulls that actually leave that day, off
#    `traffic.MANIFEST`, which is the same rule `consignments()` uses for
#    crates -- "a delivery is a real container off a real ship". Where no
#    physical count exists it is the counter's own covers, and the counter is
#    ONE counter (`COUNTER_M2`), because "a counter is not a district" is a
#    lesson this file has already paid for once.
@dataclass(frozen=True)
class Service:
    """One thing a station sells that you cannot put in a crate.

    `function` is a REGISTER function, never a place key -- the same rule
    `Good.sold_by` follows, so the list of places that sell passage is derived
    from `directory.py` and would follow the register if it changed.
    """
    name: str
    function: str           # the register function that puts it at a place
    ladder: str             # the LADDER row its price IS, "" if derived
    limiter: str            # "berths" | "covers"
    unit: str
    note: str = ""


SERVICES = (
    Service("passage home", "ship_departure", "passage_home", "berths", "each",
            "LAW-CRIME 7.1's own row. The only place on the station a hull "
            "leaves from, so the only place a berth can be bought"),
    Service("a bunk for the night", "informal_residence", "bunk_dosshouse",
            "covers", "night",
            "The floor of the market, at the three places that declare "
            "somewhere people sleep without a tenancy"),
    Service("a hot meal", "catering", "", "covers", "each",
            "An EarthForce crew mess ISSUES: 0.00 cr. The `squat` row exists "
            "in the ladder for exactly this reason -- free is a price, not a "
            "missing entry"),
    Service("a stake at the table", "gambling", "meal_cart", "covers", "each",
            "One stated step: the minimum stake is the smallest discretionary "
            "sum the ladder carries, because a table whose minimum excludes "
            "the dockers and lurkers `populace` puts in that room is a table "
            "with nobody at it"),
)
SERVICE_BY_NAME = {s.name: s for s in SERVICES}
SERVICE_FUNCTIONS = frozenset(s.function for s in SERVICES)

# THREE SERVICES THAT ARE NOT HERE, AND THE REASON IS THE SAME ONE EACH TIME:
# there is no derivable daily count, so a number would be an invention with
# nothing constraining it -- which is the "looks sourced and is not" that hard
# rule 1 forbids, rather than the declared extrapolation it permits.
#
#   a week's tenancy (`residence`, 10 places).  The PRICE is free -- `_RENT`
#       below already reads the ladder through the sector, so a week in Green
#       is the sourced 30 cr and a week in Grey is 1. What is missing is
#       VACANCIES: this repository has a measured occupancy for a quarters
#       block (`populace.occupancy(k, area, 3.0, "residence")` -- 951 people
#       asleep in `qtr_civilian`) and no DESIGN capacity anywhere, so
#       "how many are free this week" has no answer that is not made up.
#       OVERTURNED BY: any per-block unit count, which closes it in one line.
#   a fare (`transit`, 13 places).  Nothing establishes that station transit
#       is charged for, and a fare invented here would put a paywall between a
#       player and the rest of the station -- a design cost bought with an
#       unsourced number.
#   an exchange commission (`currency_exchange`, business_center).  The board
#       (authority 1, `signage.BOARDS`) establishes that exchange HAPPENS and
#       states no rate; a commission with no transaction size is a percentage
#       of nothing. `business_center` already trades goods, so it is not a
#       dead counter meanwhile.

# THE PASSENGER CLASSES. A hull that carries souls can carry one more; a
# freighter cannot, and `CREW_STAYS_ABOARD` never lands anybody at all.
# Derived from `traffic.MANIFEST`'s own soul bands rather than listed: a class
# whose band tops out at nobody is not a passenger class.
#
# LAZY BECAUSE `FREIGHT_CLASSES` IS DEFINED IN SECTION 7, below this one. That
# is not tidiness: a module-level read of a name that is bound later raises at
# IMPORT, which would take every consumer of this file down with it.
_PAX = None


def pax_classes():
    """(classes that can sell a berth, {class: its capacity band top})."""
    global _PAX
    if _PAX is None:
        cls = tuple(r[0] for r in tf.MANIFEST
                    if r[0] not in tf.CREW_STAYS_ABOARD
                    and r[0] not in FREIGHT_CLASSES and r[4] > 0)
        _PAX = (cls, {r[0]: float(r[4]) for r in tf.MANIFEST})
    return _PAX


def outbound_berths(day=0):
    """(free berths, hulls, seats) leaving during station day `day`. INV-561

    A HULL LEAVES WHEN ITS STAY IS UP, which the manifest already says: an
    arrival carries `hour` and `stay_h`, so its departure is arithmetic and
    not a second table. Its SEATS are its class's own capacity band top
    (`traffic.MANIFEST` column 5) and its outbound LOAD is what it brought --
    TRAFFIC-AND-CUSTOMS 5.3's steady state, where the transient population is
    resupplied entirely by arrivals, so over a day out equals in.
    A hull that came in full leaves full, and on a day when they all did the
    shelf is honestly empty.
    """
    classes, cap_of = pax_classes()
    free = 0
    hulls = 0
    seats = 0
    for d in (day - 1, day):
        if d < 0:
            continue
        for a in tf.arrivals(d):
            if a["type"] not in classes:
                continue
            if d + int((a["hour"] + a["stay_h"]) // 24.0) != day:
                continue
            cap = int(cap_of.get(a["type"], a["souls"]))
            hulls += 1
            seats += cap
            free += max(0, cap - int(a["souls"]))
    return free, hulls, seats


def services_at(place_key):
    """The services this place's own register functions put on its counter."""
    fns = set(dr.by_key(place_key)["functions"])
    return tuple(s.name for s in SERVICES if s.function in fns)


def service_price(name, place_key):
    """What one of these costs here: THE FLOOR OF ITS LADDER BAND, exactly. INV-560

    NO JITTER, AND THE FIRST VERSION OF THIS FUNCTION HAD ONE -- it drew inside
    the band the way `price()` does for goods and quoted **618.69 cr** for
    passage home. That number is wrong for a reason worth keeping, because it
    is this repository's oldest failure wearing a new hat: **the project had
    already decided this price and I was about to decide it a second time.**
    `player.py` line 194 carries `PASSAGE_HOME_CR = 300.0` with the note
    *"a berth on an outbound transport (band floor)"* and SPEC-CHANGE #1,
    owner-approved -- and `CREDIT_SKEW` is SOLVED against it so that exactly 1%
    of arrivals land under the line, which is the mechanism that produces
    Downbelow. A desk quoting 618.69 would have refused a player whom
    `Player.can_afford_passage()` had just told they could afford to leave.
    `_selftest` asserts the two are equal, so they cannot drift apart again.

    So the rule, and it holds for every row: **a ladder band is the spread of a
    market and a counter quotes one price, which is the cheapest thing the
    counter has.** A berth in economy, a bunk on the floor, the minimum stake.
    The top of the band is a cabin, a room and a high table -- none of which
    this counter is offering. The upshot is that every service price in the
    project is a published number rather than a number near one.

    A ROW OF ITS OWN IS NOT REQUIRED, only a stated one. `a hot meal` takes
    `squat`'s 0.0 -- the row the ladder carries so that free is a price and not
    a missing entry -- because an EarthForce crew mess issues.
    """
    s = SERVICE_BY_NAME[name]
    return round(ladder(s.ladder or "squat")[0], 2)


def service_demand(place_key, day=0):
    """{service: units a day} at this place. The physical count where one is.

    A COUNTER IS NOT A DISTRICT, and this function is where that lesson is
    applied a second time. `retail_m2` learned it for goods -- Downbelow's
    654,370 m2 footprint gave it 235,572 transactions a day -- and a bunk desk
    has the identical shape: `daily_covers("downbelow_arch")` is 4,714, which
    is a district's worth of beds behind one desk (INV-562). So a service is
    sold across
    exactly one counter, and one counter is `COUNTER_M2` -- `bar_unnamed`'s own
    225 m2 register footprint, the figure `MAX_RETAIL_M2` is already solved
    from. No new constant, and the numbers come out at 84-166 a day.
    """
    out = {}
    for n in services_at(place_key):
        s = SERVICE_BY_NAME[n]
        if s.limiter == "berths":
            out[n] = float(outbound_berths(day)[0])
        else:
            out[n] = counter_covers(place_key)
    return out


def counter_covers(place_key):
    """Transactions a day across ONE counter at this place."""
    a = min(floor_m2(place_key), COUNTER_M2)
    arch = _arch(place_key)
    rate = SERVE_PER_HEAD if arch == "hospitality" else SHOP_SERVE_PER_HEAD
    return sum(pop.occupancy(place_key, a, float(h) + 0.5, arch)
               for h in range(24)) * rate


# ===========================================================================
# 5.  WHO SELLS WHAT -- derived from the register, never listed
# ===========================================================================
# TWO SETS AND A UNION, AND THE SPLIT IS LOAD-BEARING. `GOODS_FUNCTIONS` is
# what it has always been: the functions that put LINES OF STOCK on a counter,
# and `vendors()` reads it, so every goods number in this file, in
# `incident.py` and in `consequence.counters_for` is bit-for-bit what it was.
# `SELLING_FUNCTIONS` is now the union, and it is the union because
# `consequence.sells_to` asks it exactly one question -- *is this place a
# counter at all* (INV-564) -- and a booking desk that takes 300 credits for a berth is a
# counter by any reading of that word.
GOODS_FUNCTIONS = frozenset({"commerce", "retail", "hospitality",
                             "food_service", "black_market"})
SELLING_FUNCTIONS = GOODS_FUNCTIONS | SERVICE_FUNCTIONS


def vendors():
    """Every place in the register that sells GOODS. Ordered, deterministic."""
    return tuple(p["key"] for p in dr.PLACES
                 if set(p["functions"]) & GOODS_FUNCTIONS)


def counters():
    """Every place money can change hands at -- goods, services or both."""
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


def goods_list(place_key, seed="b5"):
    """The GOODS lines this counter carries. Deterministic, derived, ordered."""
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
    if p["functions"][0] not in GOODS_FUNCTIONS:
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


def stock_list(place_key, seed="b5"):
    """Everything on this counter: goods first, then services.

    THE ONE FUNCTION THE ENGINE REACHES. `interact.counter_offer` builds the
    `serve` payload from this and `interact.container_holds` builds the `store`
    payload from it, and both are baked into the deck sidecar
    `godot/scripts/interact.gd` reads -- so a name that is not in this tuple is
    a thing no player can ever be sold. Adding services HERE rather than in a
    second accessor is what makes them reach the game without one line of
    GDScript changing: the bridge is one-way and this is the near end of it.

    Goods first and services last, deliberately: `interact.gd::_verb_serve`
    walks the list from `it.used` and takes the first line with stock, so a
    stall that sells both offers what it has on the shelf before it offers a
    berth on somebody else's ship.
    """
    return tuple(goods_list(place_key, seed)) + tuple(services_at(place_key))


def lines_at(place_key, seed="b5"):
    """What a menu board or a price board at this place SAYS. One row a line.

    THIS FUNCTION HAD A CALLER AND NO BODY. `interact.read_text` has read
    `economy.lines_at(place_key)` since session 4p -- guarded by
    `hasattr(economy, "lines_at")`, which is False, so the `menu_display` /
    `price_board` branch has been returning "" for every board on the station
    since it was written. **A `hasattr` guard around a function that does not
    exist is an assertion that cannot fail**, and it is this repository's own
    signature defect (machinery with no caller) with the ends swapped: a caller
    with no callee, degrading silently to the empty string. Found by reading
    the branch rather than by any gate.

    WHAT IT MAY AND MAY NOT CARRY, and that is the one-way bridge deciding it.
    `interact.sidecar()` BAKES this string at export time and `LIVE_READ` names
    `menu_display` and `price_board` as tokens a runtime ought to refresh --
    and nothing refreshes any of them. So a board may carry only what is
    DETERMINISTIC in (place, seed): the lines and their prices, both of which
    `price()` and `service_price()` reproduce identically in any process. It
    must NOT carry how many are left, because that is the ledger's, it moves
    every time anybody buys, and a baked count would be a board that lies with
    a number on it. The stock is live at the counter (`interact.gd` reads
    `_led.stock`); the board is the price list.
    """
    out = []
    for g in stock_list(place_key, seed):
        out.append("%-28s %8.2f cr" % (g, price(g, place_key, seed)))
    return tuple(out)


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
    """Units a day of each GOODS line this counter carries."""
    lines = goods_list(place_key, seed)
    if not lines:
        return {}
    per = daily_covers(place_key) / len(lines)
    return {g: per for g in lines}


def demand_of(place_key, seed="b5", day=0):
    """Units a day of EVERY line, goods and services, at this counter.

    The two halves are computed separately and merged rather than divided out
    of one total, and that is what keeps the goods economy bit-identical: a
    place that gained a service (`downbelow` gained a bunk) still spreads its
    own `daily_covers` across its own GOODS lines and nothing else, so every
    number in `--report`, in `incident.py` and in the fourteen-day drift check
    is exactly what it was before services existed.
    """
    out = dict(line_demand(place_key, seed))
    out.update(service_demand(place_key, day))
    return out


def opening_stock(place_key, seed="b5", day=0):
    """Units per line a counter stands with at the start of the ledger.

    A SERVICE STANDS THE SAME DEPTH A GOOD DOES -- `RESTOCK_DAYS` of its own
    demand -- because the alternative is a special case, and a special case is
    where a second rule hides. What differs is only where the top-up comes
    from, and `deliver()` is where that is said.
    """
    return {g: max(1, int(round(v * RESTOCK_DAYS)))
            for g, v in demand_of(place_key, seed, day).items()}


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
# BUMPED FROM 1 BY THE 4t WORK, and `load()` refuses the old number rather than
# defaulting around it -- a ledger written before `placements` existed has no
# key for it, and silently reading `{}` would be a save that lost a shelf
# without saying so.
LEDGER_VERSION = 2

# THE SYS-13 DELTA CLASS, NAMED ONCE. It is the JSON key, the constant a
# GDScript reader would look for, and the string PLY-03 spells out. One
# spelling, so a grep for it finds the store and not a comment about it.
PLAYER_PLACEMENTS = "player_placements"


@dataclass
class Ledger:
    day: int = 0
    stock: dict = field(default_factory=dict)     # place -> good -> units
    till: dict = field(default_factory=dict)      # place -> credits taken
    purses: dict = field(default_factory=dict)    # npc_id -> Player.state()
    wages: dict = field(default_factory=dict)     # npc_id -> credits paid
    sales: list = field(default_factory=list)     # every transaction, in order
    delivered: dict = field(default_factory=dict)  # day -> crates landed
    # SYS-13's `player_placements` SAVE-DELTA CLASS. PLY-03 names it by that
    # exact string -- *"Placed props persist -- TAKE/PLACE anywhere in the
    # player's unit survives save/reload as a SYS-13 delta class
    # (player_placements)"* -- and it existed nowhere in station/, godot/ or
    # tools/.
    #
    # IT BELONGS TO THE LEDGER AND NOT TO THE PURSE, and that is a decision
    # rather than convenience. `player.Player.state()` is a PERSON: where they
    # are, what they carry, what they are owed. A crate standing on a shelf in
    # a room is the WORLD's, and it stays on that shelf when the person who put
    # it there is on the other side of the station -- which is precisely the
    # distinction `hud.gd` had to be taught in 4q ("the ledger also holds every
    # counter's stock and till, and those belong to the world rather than to
    # the person standing in it"). This file already survives a process and is
    # already the engine's one writable world-state artefact, so a placement
    # put here needs no second save path.
    #
    # NOTE FOR WHOEVER OWNS `player.py`: `spec_harness/vrb.py`'s VRB-03 asks
    # `player.state()` for a placement key and will keep saying RED while the
    # store is here. That is not a defect in either half -- it is one open
    # question about which of the two owns a shelf -- and it is written down
    # rather than settled by whichever module the harness happened to look in.
    placements: dict = field(default_factory=dict)  # place -> [placement]
    seed: str = "b5"

    # -- construction -------------------------------------------------------
    @classmethod
    def fresh(cls, seed="b5"):
        """Opening balances: every counter stood up from its own derivation.

        `counters()` rather than `vendors()` since 4r -- a booking desk that
        holds no crate still holds berths, and a counter with no row in
        `led.stock` is a counter `godot/scripts/interact.gd::_verb_serve`
        refuses with "the shelf is empty", which is the wrong sentence for a
        desk that has forty seats going out at 14:20.
        """
        led = cls(seed=seed)
        for v in counters():
            s = opening_stock(v, seed, 0)
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
                       "delivered": self.delivered,
                       PLAYER_PLACEMENTS: self.placements}, f, indent=1,
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
                   delivered=d.get("delivered", {}),
                   placements=d.get(PLAYER_PLACEMENTS, {}),
                   seed=d.get("seed", "b5"))

    # -- queries ------------------------------------------------------------
    def units(self, place_key, good):
        return int(self.stock.get(place_key, {}).get(good, 0))

    def total_units(self):
        return sum(sum(v.values()) for v in self.stock.values())

    def total_till(self):
        return sum(self.till.values())

    # -- SYS-13 `player_placements` -----------------------------------------
    def place(self, who, place_key, good, spot="shelf"):
        """PUT an object down somewhere and have it still be there. VRB-03.

        Takes it OUT OF THE BAG, because a thing cannot be both carried and
        standing on a shelf -- the half of TAKE/PLACE that made the verb a
        pair. Returns the placement record.
        """
        if not who.has(good):
            raise Refused(f"{who.name} is not carrying {good}")
        who.drop(good)
        rec = {"good": good, "at": place_key, "spot": spot,
               "who": who.npc_id, "day": self.day}
        self.placements.setdefault(place_key, []).append(rec)
        self.purses[who.npc_id] = who.state()
        return rec

    def lift(self, who, place_key, good):
        """The inverse. Back in the bag, off the shelf, or `Refused`."""
        rows = self.placements.get(place_key, [])
        for i, r in enumerate(rows):
            if r["good"] == good:
                if who.full():
                    raise Refused(f"{who.name}'s bag is full")
                rows.pop(i)
                who.take(good)
                self.purses[who.npc_id] = who.state()
                return r
        raise Refused(f"no {good} placed at {place_key}")

    def placed_at(self, place_key):
        return tuple(r["good"] for r in self.placements.get(place_key, ()))

    def total_placed(self):
        return sum(len(v) for v in self.placements.values())


# ---------------------------------------------------------------------------
# The transaction
# ---------------------------------------------------------------------------
class Refused(Exception):
    """A sale that did not happen, with the reason a counter would give."""


def buy(led, buyer, place_key, good, n=1, bag=False):
    """BUY/SELL (VRB-05). Credits move one way, stock the other, till up.

    `bag` CLOSES A DIVERGENCE THIS FILE ALREADY REPORTED RATHER THAN HID.
    `godot/scripts/interact.gd::_verb_serve` moves FIVE things -- it calls
    `_player.take(good)` -- and this moved four, so the engine could refuse a
    sale Python allowed. It defaults False so every existing caller
    (`dockwork.py`'s fourteen-day loop, `background_sales`, `--selftest`) is
    bit-for-bit what it was; `--trade` passes True, because a thing you are
    going to SELL has to have been in your hands first.

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
    if bag:
        buyer.take(good)
        led.purses[buyer.npc_id] = buyer.state()
    return unit, total


# How deep a counter will stand on one line before it stops taking more.
# NOT A NEW NUMBER: `opening_stock` already derives what a counter stands with
# from its own covers over `RESTOCK_DAYS`, and a counter already holding that
# has its next delivery contracted -- it has nowhere to put another and no
# reason to want one. So the cap IS the opening depth.
def shelf_cap(place_key, good, seed="b5"):
    """Units of one line a counter will hold. 0 if it does not deal in it."""
    return int(opening_stock(place_key, seed, 0).get(good, 0))


def sell(led, seller, place_key, good, n=1):
    """SELL (VRB-05), and it is `buy` run backwards through the same four rows.

    buy   purse DOWN   shelf DOWN   till UP     one row, cr > 0
    sell  purse UP     shelf UP     till DOWN   one row, cr < 0

    THE SIGN IS THE DIRECTION and it is load-bearing rather than cosmetic:
    `till[place]` is cumulative takings, so after any mix of buys and sells it
    must still equal the sum of the `cr` of that place's own rows. `--trade`
    asserts exactly that, and it is the invariant that would catch a sell
    that moved money without writing it down.

    THE SELLER MUST BE CARRYING IT. `player.Player.carrying` is a set of
    NAMES -- `take()` refuses a duplicate -- so one bag slot is one line and
    `n` is how many units of that line leave it. The slot clears on the sale.

    Raises `Refused` with the sentence a keeper would give.
    """
    if place_key not in led.stock:
        raise Refused(f"{place_key} is not a counter")
    if n < 1:
        raise Refused("nothing to sell")
    if not seller.has(good):
        raise Refused(f"{seller.name} is not carrying {good}")
    if good not in buys_list(place_key, led.seed):
        g = GOODS_BY_NAME.get(good)
        if g is not None and (g.cargo == "bonded" or g.supply == "route"):
            raise Refused(
                f"{place_key} will not take {good} over a counter with a "
                f"reader on it -- that is a `contraband` docket, not a sale")
        raise Refused(f"{place_key} does not deal in {good}")
    if not unchecked(place_key):
        cap = shelf_cap(place_key, good, led.seed)
        if led.units(place_key, good) + n > cap:
            raise Refused(
                f"{place_key} stands {cap} {good} deep and has "
                f"{led.units(place_key, good)} -- no room on the shelf")
    unit = bid(good, place_key, led.seed)
    total = round(unit * n, 2)
    seller.drop(good)
    seller.credits = round(seller.credits + total, 3)
    led.stock[place_key][good] = led.units(place_key, good) + n
    led.till[place_key] = round(led.till.get(place_key, 0.0) - total, 2)
    led.purses[seller.npc_id] = seller.state()
    led.sales.append({"day": led.day, "at": place_key, "good": good,
                      "n": -n, "cr": -total, "who": seller.npc_id})
    return unit, total


# PLY-06's ENTIRE PAY EFFECT. The spec says the bonus is "stated in credits on
# the stub", so it is a separate line in the sales log rather than a silently
# larger wage -- a player who cannot see the bonus cannot notice forfeiting it,
# and a forfeited bonus nobody notices is a rule that is not in the game.
#
# 4% is chosen HERE rather than in `condition.py`, because the size of a bonus
# is an economic fact and belongs beside the wage table. It is small on purpose:
# PLY-06 is ruled LIGHT, and a rested shift that paid 25% more would make sleep
# a resource to optimise, which is the thing the row's effect list forbids.
# INV-661.
RESTED_BONUS = 0.04


def pay(led, worker, credits, why="", rested=False):
    """Wages. The other direction, and the only one that creates credits.

    `rested` is `condition.Condition.effects()["pay_bonus"]`. It adds a SECOND,
    NAMED line to the stub rather than inflating the first, so the bonus and its
    absence are both visible.
    """
    credits = round(float(credits), 2)
    if rested and credits > 0.0:
        bonus = round(credits * RESTED_BONUS, 2)
        if bonus > 0.0:
            worker.credits = int(round(worker.credits + bonus))
            led.wages[worker.npc_id] = round(
                led.wages.get(worker.npc_id, 0.0) + bonus, 2)
            led.purses[worker.npc_id] = worker.state()
            led.sales.append({"day": led.day, "at": why,
                              "good": "(rested bonus)", "n": 1,
                              "cr": -bonus, "who": worker.npc_id})
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
        keys = sorted(lines)
        if not keys:
            continue
        # PER LINE, NOT COVERS/LINES, and the change is a no-op on every place
        # that existed before services did: `line_demand` IS `daily_covers`
        # over the goods lines, so a goods-only counter draws exactly the
        # number it drew before. What it fixes is a MIXED counter -- adding a
        # bunk to Downbelow would otherwise have divided its black-market
        # covers by one more line and quietly changed the goods economy.
        want_of = demand_of(v, led.seed, day)
        for g in keys:
            want = int(want_of.get(g, 0.0) * (0.6 + 0.8 * _u("bg", v, g, day)))
            take = min(want, lines[g])
            if take > 0:
                lines[g] -= take
                led.till[v] = round(led.till.get(v, 0.0)
                                    + take * price(g, v, led.seed), 2)
                moved += take
    # THE OTHER DIRECTION, ON THE SAME TICK. Called from here rather than left
    # for a caller to remember, because "a caller has to remember" is how this
    # project produced nine pieces of machinery nobody ran. `moved` still
    # counts units SOLD BY counters, so every existing assertion against this
    # return value means what it did.
    background_fencing(led, day)
    return moved


# How much of a fence's daily turnover walks in off the deck instead of coming
# off a hull. NOT A NEW NUMBER: `BLACK_MARKET_SHARE = 0.05` above is already
# the share of the station's trade the route carries, and this is that same
# fraction read the other way -- five percent of a fence's stock is what
# somebody sold it. LAW-CRIME 6.2 puts 22% of the underclass on salvage and
# gives them nowhere to take it; this is where they take it.
FENCE_INTAKE_SHARE = BLACK_MARKET_SHARE


def background_fencing(led, day=None):
    """What the fences BUY on a day nobody plays. The route's supply side.

    THIS IS THE CALLER `sell()` NEEDED AND IT IS ON THE SHIPPED PATH. This
    project has shipped finished machinery with no caller nine times, and the
    ninth got past the static scan built to catch the eighth. So the sell side
    is not left for a GDScript verb to discover: every tick of the world that
    produces `station/generated/economy.json` -- the file
    `godot/scripts/interact.gd` loads -- runs through here, and the rows it
    appends are `cr < 0` rows a reader can see.

    The sellers are deterministic in (day, place, line): the same lurkers bring
    the same cable to the same stall in any process, which is what lets
    `--trade` assert it twice and get the same answer.
    """
    day = led.day if day is None else day
    import player as _pl                                     # noqa: PLC0415
    n = 0
    for v in fence_places():
        if v not in led.stock:
            continue
        for g in sorted(led.stock[v]):
            good = GOODS_BY_NAME.get(g)
            if good is None or good.klass not in ("salvage", "contraband"):
                continue                 # what a lurker actually carries up
            want = int(demand_of(v, led.seed, day).get(g, 0.0)
                       * FENCE_INTAKE_SHARE
                       * (0.5 + _u("fenceint", v, g, day)))
            if want < 1:
                continue
            s = _pl.random_player(f"fence/{day}/{v}/{g}")
            s.move_to(v)
            s.credits = 0
            if not s.take(g):
                continue
            try:
                sell(led, s, v, g, want)
            except Refused:
                continue                 # a full shelf is a real answer
            n += want
    return n


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
    landed += _renew_services(led, day)
    led.delivered[str(day)] = led.delivered.get(str(day), 0) + landed
    return landed


def _renew_services(led, day):
    """A SERVICE'S DELIVERY IS THE DAY ITSELF. INV-563

    A crate arrives on a hull and `consignments` says which; a bunk-night comes
    back because tomorrow is another night, and a berth comes back because
    tomorrow is another ship -- so this is where the two nouns differ and it is
    the ONLY place they do. Everything else about a service (its depth, its
    demand, its price, its refusals) is the goods rule unchanged.

    Topped up by one day's demand and capped at `RESTOCK_DAYS` of it, exactly
    as the goods half is sized, so the shelf neither starves nor runs away and
    the fourteen-day drift check does not have to be widened to admit it.

    IT RUNS ON EVERY `deliver()`, INCLUDING `deliver(only=...)`, AND THE FIRST
    VERSION DID NOT -- which is a mistake worth keeping written down because
    the reasoning sounded right and the measurement killed it. `only=` exists
    so `dockwork.py` can prove the crates the player's own gang worked are the
    crates that arrived, and skipping the renewal there looked like the same
    honesty. But `only=` restricts which CONSIGNMENTS land, and a service is
    not a consignment: no gang has ever moved a berth. The effect of the skip
    was that `dockwork.py --loop` -- the ONE loop in this project that runs
    fourteen consecutive days -- drained every service shelf to nothing and
    never refilled it, so the transcript's closing scene read
    *"300.00 cr, **0 free today**"* on a day the manifest sailed 22 hulls.
    A rule that is right about goods is not automatically right about the
    other noun.
    """
    added = 0
    for v in led.stock:
        want = service_demand(v, day)
        if not want:
            continue
        shelf = led.stock[v]
        for g, per_day in want.items():
            if g not in shelf:
                continue
            cap = max(1, int(round(per_day * RESTOCK_DAYS)))
            new = min(cap, int(shelf[g]) + int(round(per_day)))
            added += max(0, new - int(shelf[g]))
            shelf[g] = new
    return added


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

    # -- 4b. THE SERVICES -- what a station sells that is not a crate ---------
    # These are the four claims that make a service a real price rather than a
    # second vocabulary, and each has a control that fires.
    check("every service price IS its ladder row, to the millicredit -- there "
          "is no band to be inside, because a counter quotes one price",
          not [b for b in price_check() if b[0] in SERVICE_BY_NAME],
          "; ".join(str(b) for b in price_check()
                    if b[0] in SERVICE_BY_NAME)[:160]
          or ", ".join(f"{s.name} = {s.ladder or 'squat'} "
                       f"{ladder(s.ladder or 'squat')[0]:.2f}"
                       for s in SERVICES))
    # THE ONE THAT STOPS THIS FILE DECIDING A PRICE TWICE. `player.py` solved
    # `CREDIT_SKEW` against 300 cr so that 1% of arrivals land under it; a desk
    # quoting anything else would refuse a player `can_afford_passage()` had
    # just cleared. The first draft of `service_price` quoted 618.69.
    check("the fare at the desk is the number `player.PASSAGE_HOME_CR` was "
          "solved against, so `can_afford_passage()` is a true statement "
          "about a real counter",
          abs(price("passage home", "docking_bays") - pl.PASSAGE_HOME_CR) < 1e-9,
          f"{price('passage home', 'docking_bays'):.2f} cr at the desk "
          f"against player.py's {pl.PASSAGE_HOME_CR:.2f}")
    # NEGATIVE CONTROL: a drawn fare. This is what the first version did, and
    # it must break the equality above -- otherwise the assertion is vacuous.
    drawn = round(PASSAGE_LO + (PASSAGE_HI - PASSAGE_LO)
                  * _u("service", "passage home", "docking_bays"), 2)
    check("...and a fare DRAWN inside the same band breaks it, which is why "
          "the draw was taken out",
          abs(drawn - pl.PASSAGE_HOME_CR) > 1.0,
          f"the draw gives {drawn:.2f} cr, {drawn - pl.PASSAGE_HOME_CR:+.2f} "
          f"off the solved line")
    free0, hulls0, seats0 = outbound_berths(0)
    free1, _h1, _s1 = outbound_berths(1)
    check("a berth is a real seat on a real hull that really leaves that day "
          "-- the crate rule, applied to people",
          free0 > 0 and hulls0 > 0 and free0 < seats0,
          f"day 0: {hulls0} passenger hulls depart with {seats0} seats, "
          f"{free0} of them free ({seats0 - free0} already carrying the souls "
          f"they brought)")
    check("...and two days do not sail the same ships",
          free0 != free1, f"day 0 {free0} free berths, day 1 {free1}")
    # A COUNTER IS NOT A DISTRICT, asked a second time. `daily_covers` over
    # `downbelow_arch`'s whole footprint gives 4,714 bunks a night behind one
    # desk; across ONE counter it is 106.
    wide = daily_covers("downbelow_arch")
    one = counter_covers("downbelow_arch")
    check("a service is sold across ONE counter, not across the place's whole "
          "footprint -- the lesson `retail_m2` already paid for",
          one < wide / 10.0,
          f"downbelow_arch: {wide:.0f} covers/day over its footprint, "
          f"{one:.0f} over one {COUNTER_M2:.0f} m2 counter")
    # THE ARC THIS PROJECT ALREADY SHIPS, AND IT NOW HAS AN ENDING.
    check("the fourteen-day dock loop earns a lurker past the fare, so the "
          "one transaction the underclass exists around can be completed",
          420.50 >= price("passage home", "docking_bays"),
          f"dockwork's lurker reaches 420.50 cr against a "
          f"{price('passage home', 'docking_bays'):.2f} cr berth")
    # AND THE SHELF CAN BE EMPTY, which is what makes the counter a counter.
    lp = Ledger.fresh()
    berths = lp.units("docking_bays", "passage home")
    rich = pl.random_player("passage")
    rich.credits = 5000
    rich.move_to("docking_bays")
    u_p, t_p = buy(lp, rich, "docking_bays", "passage home", 1)
    check("a player buys a berth at the departure bay: purse down, shelf down, "
          "till up, one row in the ledger",
          rich.credits == 5000 - t_p
          and lp.units("docking_bays", "passage home") == berths - 1
          and lp.till["docking_bays"] == round(t_p, 2)
          and lp.sales[-1]["good"] == "passage home",
          f"{t_p:.2f} cr, {berths} -> "
          f"{lp.units('docking_bays', 'passage home')} berths, till "
          f"{lp.till['docking_bays']:.2f}")
    # A DIVERGENCE THIS GATE REPORTS RATHER THAN HIDES, and it is between the
    # two languages. `godot/scripts/interact.gd::_verb_serve` moves FIVE
    # things -- it calls `_player.take(good)` and refuses with "nothing to
    # carry it in" when the bag is full -- and `buy()` below moves four. So the
    # engine can refuse a sale Python allows. It is not repaired here because
    # the repair is a design decision with a cost either way: put every
    # purchase in the bag and `dockwork.py`'s fourteen-day loop fills its eight
    # slots on day six and starves; leave it out and `interact.verify_buy` --
    # which compares till, stock, purse and sales and NOT `carrying` -- cannot
    # see the difference. What is needed is a consumable flag on `Good`, and
    # `station/till.py --divergence` measures the gap meanwhile.
    check("the engine's transaction and this one move the same money, and the "
          "BAG is the one thing they do not agree about -- reported, not hidden",
          "passage home" not in rich.carrying,
          f"python leaves the bag at {len(rich.carrying)} items; the engine "
          f"would have made it {len(rich.carrying) + 1} of "
          f"{pl.CARRY_CAPACITY}")
    lp.stock["docking_bays"]["passage home"] = 0
    try:
        buy(lp, rich, "docking_bays", "passage home", 1)
        sold_out = False
    except Refused as e:
        sold_out = "out of" in str(e)
    check("...and a day whose hulls all sailed full refuses, in the words a "
          "clerk would use", sold_out)

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


# ===========================================================================
# 9.  --trade -- THE VRB-05 ACCEPTANCE RUN, BOTH DIRECTIONS, ONE PROCESS
# ===========================================================================
def trade_gate(out=print, break_margin=False):
    """A player BUYS and SELLS in one run, and every number is shown moving.

    THE ROW'S OWN WORDS ARE THE BAR: VRB-05's CHECK is *"credits and stock move
    BOTH ways"* at a named place with a named counter. So this prints the four
    ledger rows on each side of each transaction, at named places, and asserts
    the invariants a sale in two directions has to satisfy but a sale in one
    direction cannot even express.

    `break_margin=True` is the NEGATIVE CONTROL and it is the whole reason this
    function takes an argument: it sets the buy-back rate above 1.0, which is a
    counter paying more than it charges, and the money-pump assertion must go
    red. A gate nobody has watched fail is a gate nobody has tested.
    """
    import consequence as CQ                                  # noqa: PLC0415
    import player as pl                                       # noqa: PLC0415
    global BUY_BACK
    n = [0]
    failed = []

    def check(name, ok, note=""):
        n[0] += 1
        if not ok:
            failed.append(name)
        out(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if note:
            out(f"         {note}")

    saved = BUY_BACK
    if break_margin:
        BUY_BACK = 1.2
        out("!! NEGATIVE CONTROL: BUY_BACK forced to 1.2 -- a counter paying "
            "more than it charges")
    try:
        out("")
        out("THE COUNTER, AND WHO IS BEHIND IT")
        keeper, shop, cat = household_vendor()
        out(f"  PLC-052 `{shop}` -- {keeper}, household goods: "
            f"{', '.join(cat) or '(none on her list today)'}")
        gap_ok, gap_note = fence_register_gap()
        out(f"  the fence: {FENCE_NAME}, CAST-41, buys "
            f"{FENCE_HOURS[0]:04.1f}-{FENCE_HOURS[1]:04.1f}")
        out(f"  {'ok' if gap_ok else 'REGISTER GAP'}: {gap_note}")
        check("PLY-03's household-goods vendor has something to sell",
              bool(cat), f"{len(household_goods())} `household` lines in "
                         f"GOODS, {len(cat)} of them on her stall")

        led = Ledger.fresh()
        p = pl.random_player("vrb05/trade")
        p.credits = 400
        p.move_to(shop)
        t = CQ.tier_of(p.card, getattr(p, "record", None))
        good = cat[0] if cat else goods_list(shop)[0]
        out("")
        out(f"THE PLAYER: {p.name} ({p.npc_id}), rung {t} "
            f"{CQ.tier_name(t)}, {p.credits:.2f} cr")

        # -- BUY ------------------------------------------------------------
        b = (p.credits, led.units(shop, good), led.till.get(shop, 0.0),
             len(led.sales))
        unit_b, tot_b = CQ.purchase(led, p, shop, good, 1, bag=True)
        a = (p.credits, led.units(shop, good), led.till.get(shop, 0.0),
             len(led.sales))
        out("")
        out(f"BUY  1 x {good} at `{shop}` for {tot_b:.2f} cr")
        out(f"  purse {b[0]:8.2f} -> {a[0]:8.2f}   shelf {b[1]:5d} -> "
            f"{a[1]:5d}   till {b[2]:8.2f} -> {a[2]:8.2f}   rows "
            f"{b[3]} -> {a[3]}")
        check("BUY: purse DOWN, shelf DOWN, till UP, one row",
              a[0] < b[0] and a[1] == b[1] - 1 and a[2] > b[2]
              and a[3] == b[3] + 1)
        check("...and it is in the player's hands, which is what makes a sale "
              "possible at all", p.has(good),
              f"carrying {', '.join(p.carrying)}")

        # -- SELL -------------------------------------------------------------
        b2 = (p.credits, led.units(shop, good), led.till.get(shop, 0.0),
              len(led.sales))
        unit_s, tot_s = CQ.fence(led, p, shop, good, 1)
        a2 = (p.credits, led.units(shop, good), led.till.get(shop, 0.0),
              len(led.sales))
        out("")
        out(f"SELL 1 x {good} back to {keeper} for {tot_s:.2f} cr")
        out(f"  purse {b2[0]:8.2f} -> {a2[0]:8.2f}   shelf {b2[1]:5d} -> "
            f"{a2[1]:5d}   till {b2[2]:8.2f} -> {a2[2]:8.2f}   rows "
            f"{b2[3]} -> {a2[3]}")
        check("SELL: purse UP, shelf UP, till DOWN, one row",
              a2[0] > b2[0] and a2[1] == b2[1] + 1 and a2[2] < b2[2]
              and a2[3] == b2[3] + 1)
        check("...and it is out of the player's hands", not p.has(good),
              f"carrying {', '.join(p.carrying)}")
        check("the two directions are SYMMETRIC -- the same line, the same "
              "counter, the same shelf, opposite signs",
              a2[1] == b[1] and led.sales[-2]["n"] == 1
              and led.sales[-1]["n"] == -1,
              f"shelf back to {a2[1]}; rows n=+1 cr={led.sales[-2]['cr']:.2f} "
              f"then n=-1 cr={led.sales[-1]['cr']:.2f}")

        # -- THE INVARIANTS ONLY A TWO-WAY MARKET CAN BREAK -------------------
        out("")
        out("INVARIANTS")
        rows = [r for r in led.sales if r["at"] == shop]
        s = round(sum(r["cr"] for r in rows), 2)
        check("the till equals the sum of its own rows, signs and all",
              abs(s - led.till[shop]) < 0.011,
              f"sum(cr) {s:.2f} against till {led.till[shop]:.2f} over "
              f"{len(rows)} row(s)")
        check("a round trip LOSES money -- buy then sell is never free",
              tot_s < tot_b,
              f"paid {tot_b:.2f}, got back {tot_s:.2f}, "
              f"spread {tot_b - tot_s:.2f} cr "
              f"({100.0 * (1 - tot_s / tot_b):.1f}%)")
        pump = []
        for k in counters():
            for g in buys_list(k):
                if g in SERVICE_BY_NAME:
                    continue
                if bid(g, k) >= price(g, k) and price(g, k) > 0:
                    pump.append((k, g, bid(g, k), price(g, k)))
        check("NO COUNTER ANYWHERE PAYS MORE THAN IT CHARGES -- the money "
              "pump a player finds in ten minutes",
              not pump,
              f"{len(pump)} pair(s) over {len(counters())} counters"
              + (f"; e.g. {pump[0]}" if pump else ""))

        # -- THE FENCE, AND WHY IT EXISTS -------------------------------------
        out("")
        out("THE FENCE")
        p.credits = 400
        p.take("Dust")
        try:
            CQ.fence(led, p, shop, "Dust", 1)
            licit, why_l = True, ""
        except Refused as ex:
            licit, why_l = False, str(ex)
        check("a licensed counter will NOT take a customs-sealed line",
              not licit, why_l)
        check("...and names the docket it would be instead",
              CQ.would_book(shop, "Dust") == "contraband",
              f"consequence.would_book -> {CQ.would_book(shop, 'Dust')!r}, "
              f"fine band {CQ.fine_for('contraband')}")
        # THE STALL, not merely a room with no reader in it. `fence_places()`
        # is every unchecked counter and includes the casino and Happy Daze,
        # which are `black_market_fringe`; CAST-41 puts Solly Vane behind a
        # `black_market` stall, so the trade goes to a place that declares that
        # function outright and falls back to the fringe only if none does.
        _f = [k for k in fence_places() if k in led.stock
              and "Dust" in buys_list(k)]
        fkey = ([k for k in _f if "black_market" in dr.by_key(k)["functions"]]
                or _f)[0]
        p.move_to(fkey)
        b3 = (p.credits, led.units(fkey, "Dust"), led.till.get(fkey, 0.0))
        unit_f, tot_f = CQ.fence(led, p, fkey, "Dust", 1)
        a3 = (p.credits, led.units(fkey, "Dust"), led.till.get(fkey, 0.0))
        out(f"  SELL 1 x Dust to {FENCE_NAME}'s trade at `{fkey}` for "
            f"{tot_f:.2f} cr")
        out(f"  purse {b3[0]:8.2f} -> {a3[0]:8.2f}   shelf {b3[1]:5d} -> "
            f"{a3[1]:5d}   till {b3[2]:8.2f} -> {a3[2]:8.2f}")
        check("the fence takes what the shop refused", a3[0] > b3[0]
              and a3[1] == b3[1] + 1 and a3[2] < b3[2])
        check("...and pays WORSE for it -- FENCE_TAKE is the route's own "
              "undercut, read backwards",
              abs(bid("salvage lots", fkey)
                  - price("salvage lots", fkey) * BUY_BACK * FENCE_TAKE) < 0.02,
              f"BUY_BACK {BUY_BACK} x FENCE_TAKE {FENCE_TAKE} = "
              f"{BUY_BACK * FENCE_TAKE:.3f} of shelf, against "
              f"{BUY_BACK:.3f} at a shopfront")

        # -- THE REFUSALS -----------------------------------------------------
        out("")
        out("REFUSALS -- a till that cannot say no is not a till")
        def _carrying(seed_, place, line, n_=1):
            q = pl.random_player(seed_)
            q.credits = 50
            q.move_to(place)
            q.take(line)
            return lambda: sell(led, q, place, line, n_)

        for label, fn, want in (
            ("not carrying it",
             lambda: sell(led, p, shop, good, 1), "not carrying"),
            ("carrying it, at a counter that does not deal in it",
             _carrying("r2", "bar_unnamed", "bearing sets"),
             "does not deal in"),
            ("a shelf already at its standing depth",
             _carrying("r3", shop, good, 999), "no room on the shelf"),
        ):
            try:
                fn()
                got = "(allowed)"
            except Refused as ex:
                got = str(ex)
            check(f"refused: {label}", want in got, got)
        ok_l, why_c = CQ.buys_from(shop, CQ.DETAINED)
        ok_f, why_f = CQ.buys_from(fkey, CQ.DETAINED)
        check("a card in custody is refused by BOTH a shop and a fence",
              not ok_l and not ok_f, f"{shop}: {why_c} / {fkey}: {why_f}")
        ok_n, why_n = CQ.buys_from(shop, CQ.NO_STATUS)
        ok_nf, why_nf = CQ.buys_from(fkey, CQ.NO_STATUS)
        check("a card that will not read is refused by the SHOP and taken by "
              "the FENCE -- which is the whole reason FACTIONS 11.4's market "
              "exists", not ok_n and ok_nf,
              f"{shop}: {why_n} / {fkey}: {why_nf}")

        # -- PERSISTENCE, AND A SECOND PROCESS --------------------------------
        out("")
        out("PERSISTENCE -- the artefact the engine reads")
        import subprocess                                     # noqa: PLC0415
        import tempfile                                       # noqa: PLC0415
        p.take("storage locker")
        rec = led.place(p, "qtr_civilian", "storage locker", "shelf")
        tmp = os.path.join(tempfile.mkdtemp(), "economy.json")
        led.save(tmp)
        code = (f"import sys; sys.path.insert(0, {HERE!r}); import economy as e;"
                f"L = e.Ledger.load({tmp!r});"
                f"neg = [r for r in L.sales if r['cr'] < 0];"
                f"print(len(neg), round(neg[-1]['cr'], 2), neg[-1]['at'],"
                f" L.placed_at('qtr_civilian'), L.total_placed())")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True)
        out(f"  child process said: {r.stdout.strip()!r}")
        mine = [x for x in led.sales if x["cr"] < 0]
        check("a SECOND PROCESS reads the sell rows back off the file",
              r.returncode == 0
              and r.stdout.strip().startswith("%d " % len(mine)),
              f"{len(led.sales)} rows written, {len(mine)} of them SELLS; "
              f"child rc={r.returncode} {r.stderr.strip()[:100]}")
        check(f"...and SYS-13's `{PLAYER_PLACEMENTS}` survives it too",
              "storage locker" in r.stdout,
              f"placed {rec['good']} on the {rec['spot']} at {rec['at']}; "
              f"the JSON key is {PLAYER_PLACEMENTS!r}")
        fresh = Ledger.fresh()
        check("...and a ledger that was never written carries neither",
              not [x for x in fresh.sales if x["cr"] < 0]
              and fresh.total_placed() == 0,
              f"{len(fresh.sales)} rows, {fresh.total_placed()} placements")

        # -- THE WORLD SELLS TOO, ON THE TICK THAT WRITES THE SHIPPED FILE ----
        out("")
        out("THE CALLER ON THE SHIPPED PATH")
        w = Ledger.fresh()
        before = len([x for x in w.sales if x["cr"] < 0])
        background_sales(w, 0)
        wrows = [x for x in w.sales if x["cr"] < 0]
        check("`background_sales` -- the tick every writer of "
              "station/generated/economy.json goes through -- moves goods INTO "
              "fences, so sell() has a caller that is not a selftest",
              before == 0 and len(wrows) > 0,
              f"{len(wrows)} sell row(s) on day 0, e.g. "
              f"{wrows[0]['n']} x {wrows[0]['good']} at {wrows[0]['at']} for "
              f"{-wrows[0]['cr']:.2f} cr" if wrows else "none")
        w2 = Ledger.fresh()
        background_sales(w2, 0)
        check("...and it is DETERMINISTIC -- two ledgers, same day, same rows",
              [x for x in w2.sales if x["cr"] < 0] == wrows,
              f"{len(wrows)} rows compared field for field")
    finally:
        BUY_BACK = saved

    out("")
    out(f"{n[0] - len(failed)}/{n[0]} passed"
        + (f"  FAILED: {'; '.join(failed)}" if failed else ""))
    return not failed


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--trade", action="store_true",
                    help="VRB-05: a player buys and sells in one run")
    ap.add_argument("--break-margin", action="store_true",
                    help="the --trade negative control: pay more than you "
                         "charge and watch the money-pump assertion fail")
    ap.add_argument("--day", type=int, default=None)
    a = ap.parse_args()
    if a.trade or a.break_margin:
        # RUN IT OUT OF THE *IMPORTED* COPY, NOT OUT OF `__main__`, and this
        # is not tidiness -- it is a live defect this gate hit on its first
        # run. `python3 station/economy.py` makes this file `__main__`, and
        # `consequence.py` does `import economy as EC`, which loads the file a
        # SECOND time under the name `economy`. The two copies then have
        # different `Refused` classes (so `except Refused` does not catch what
        # `consequence` raises) and different `BUY_BACK` globals (so
        # `--break-margin` would mutate a constant nothing reads). Dispatching
        # into the imported module makes one copy authoritative.
        sys.path.insert(0, HERE)
        import economy as _EC                                # noqa: PLC0415
        raise SystemExit(0 if _EC.trade_gate(
            break_margin=a.break_margin) else 1)
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
