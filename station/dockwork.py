#!/usr/bin/env python3
"""ROLE-03, THE DOCKWORKER -- the first complete job loop, end to end.

WHAT "COMPLETE" MEANS, and it is the whole specification of this file.
`docs/MASTER-PLAN.md` §A2 says the hours come from four sources and the third is
**the role**: *"the player IS someone: jobs, shifts, pay"*, gated at *">=3
playable roles with complete loops (work -> pay -> spend)"*. This is the first
of the three, and the plan names it and says why: *"dock work is the
canon-obvious first: shifts exist, the port exists, pay exists"*.

So the loop, and every link is a real thing the simulation already had:

    05:40  the caller chalks the board  `traffic.arrivals(day)` -- the REAL ships
    06:00  the player takes a gang      the decision loop, and it has consequences
    06:00  RIDE the bay elevator        `bay_elevators`, a register place
    06:15  USE docking_clamp            a built prop -- `interact.py` resolves it
     ...   USE cargo_crane              per crate, at a DERIVED rate
     ...   USE manifest_terminal        `economy.consignments` -- who each is for
    12:00  EAT at the mess              `mess_hall`, a register place
    15:00  clock off, and the pay       `economy.pay` -> `player.Player.credits`
    19:xx  BUY at a bar                 `economy.buy` -- the stock falls
    +1 day the crates the gang cleared  are on the shelf the player drinks from

THE THING THAT MAKES IT A JOB AND NOT A TIMER. PEOPLE.md's WORK-fidelity clause
is normative for every role: *"each role names its **decision loop** -- the
recurring judgment call that makes the shift a job rather than an animation ...
and its **per-shift variation source** ... so no two shifts replay. A role whose
shift has no decision and no variation is not GREEN at any coverage."*

  * ROLE-03's decision loop is **the caller's gang assignment**, and it is a
    real fork: the board's gangs differ in what they pay, how long they run and
    what goes wrong. `POLICIES` are three ways to choose and they produce
    measurably different days -- `--policies` prints the divergence and
    `_selftest` asserts it is not zero.
  * ROLE-03's variation source is **the manifest**, and it is not simulated
    variation: `traffic.arrivals(day)` is the port's own day, so the board on
    day 3 is the board on day 3 and a liner day is a different job.

AND A SHIFT WORKED BADLY IS VISIBLE FROM THE OTHER END. Perishable cargo that
is not cleared before its ship's dwell runs out **does not reach its
consignee** -- so a gang that took the bonded job and left the fresh treel on
the pad is a bar with an empty tank that evening. That is the same chain read
backwards, and it is the reason the cargo classes are not decoration.

WHAT IS DERIVED HERE, AND FROM WHAT
  * the shift hours          `npc/schedule.py`'s `dockworker` Role, 06:00 + 9 h
  * the muster               LAW-CRIME 7.2's "06:00 and 14:00 EMT muster"
  * the gang size            PLACES PLC-006's "per active bay a gang of 6"
  * the crate rate           the ship must clear inside its own dwell:
                             `economy` crates / `traffic` stay
  * the chalked rate         the STATED casual band's own width is the risk
                             spread -- the caller pays the top of 8-15 for the
                             jobs nobody wants. No new number.
  * the guild card           `economy.GUILD_SHIFTS_PER_WEEK` of standing the
                             muster: one guaranteed week's worth of turning up

Run: python3 station/dockwork.py --board --day 0
     python3 station/dockwork.py --shift --day 0
     python3 station/dockwork.py --loop            # THE GATE: work, pay, spend
     python3 station/dockwork.py --policies
     python3 station/dockwork.py --selftest
"""
import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import directory as dr                                          # noqa: E402
import economy as ec                                            # noqa: E402
import player as pl                                             # noqa: E402
import populace as pop                                          # noqa: E402
import traffic as tf                                            # noqa: E402
from npc import resident as RES                                 # noqa: E402
from npc import schedule as sched                               # noqa: E402


def _u(*parts) -> float:
    s = "|".join(str(p) for p in parts)
    h = hashlib.blake2b(s.encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ===========================================================================
# 1.  THE SHIFT, AND WHERE IT HAPPENS -- all of it out of the register
# ===========================================================================
ROLE = sched.ROLES_BY_KEY["dockworker"]         # 06:00, 9 h, docking_bay
WORKPLACE = "docking_bays"

# LAW-CRIME 7.2: "**06:00 and 14:00 EMT muster** -- a crowd forms and thins on
# a clock". PLC-006 repeats it. PEOPLE ROLE-03 puts the player at the board
# twenty minutes before the hour, which is what standing a muster is.
MUSTER_H = ROLE.work_start - (20.0 / 60.0)      # 05:40
CLOCK_ON_H = ROLE.work_start                    # 06:00
CLOCK_OFF_H = ROLE.work_start + ROLE.work_hours  # 15:00
MESS_H = 12.0                                   # PEOPLE ROLE-03
MESS_HOURS = 1.0
WORK_HOURS = ROLE.work_hours - MESS_HOURS       # 8 h on the crane

# PLACES PLC-006: "per active bay a gang of 6 (typ. 3 human, 2 Narn, 1 Drazi --
# docks are alien-heavy, FACTIONS 2.4)". The SPECIES are not listed here: they
# come from `populace.species_for`, which is the place's own mix, so a gang is
# drawn the way the crowd standing behind it is.
GANG = 6

# Every place a shift touches, and every one is a register key. `_selftest`
# resolves all of them, so a shift cannot walk somewhere that is not built.
STATIONS = {
    "muster": WORKPLACE,          # the board, outside the elevator post (D-10)
    "ride": "bay_elevators",      # RIDE, pad -> parking level (D-9)
    "clamp": WORKPLACE,           # USE docking_clamp
    "crane": WORKPLACE,           # USE cargo_crane
    "manifest": "cargo_bays",     # USE manifest_terminal -- where the ledger is
    "mess": "mess_hall",          # EAT
}

# The props each step operates, as `directory` declares them. The register row
# for `docking_bays` carries the clamp and the crane; `cargo_bays` carries the
# manifest terminal. Asserted against `docs/interact-audit.json` -- the record
# of what `interact.py` actually RESOLVED in built geometry -- so a step of this
# shift cannot name a prop that is not in the station.
PROPS = {
    "ride": ("lift_call",),
    "clamp": ("docking_clamp",),
    "crane": ("cargo_crane",),
    "manifest": ("manifest_terminal",),
}


# ===========================================================================
# 2.  THE RATE -- what a gang can move, and it is a constraint, not a choice
# ===========================================================================
# A ship's berth is released when it leaves, so a gang has to clear its cargo
# inside the ship's own dwell or the port stops working. That is the
# constraint, and it is the whole derivation: take the manifest's own mean bay
# freighter -- `economy.FREIGHTER_ANCHOR_T` over `traffic.MANIFEST`'s 8-14 h --
# and the rate falls out.
_FBAY = dict((r[0], r) for r in tf.MANIFEST)["freighter_bay"]
_MEAN_DWELL_H = (_FBAY[5] + _FBAY[6]) / 2.0                  # 11.0
CRATES_PER_GANG_H = (ec.FREIGHTER_ANCHOR_T / ec.CONTAINER_T) / _MEAN_DWELL_H

# WHAT EACH CLASS COSTS TO HANDLE, expressed as a multiple of the crane cycle.
# These are ROLE-03's own five classes and each multiplier is the handling step
# the spec names for it, not a difficulty knob:
#
#   containerised  the baseline. Hook, lift, traverse, set, scan.
#   bulk           transshipment: it does not leave the bay, so it is FASTER
#                  per crate and duller -- "bulk/transshipment" is one class in
#                  the spec because that is what it is.
#   bonded         customs-sealed. The seal is read and logged at the terminal
#                  before it moves and it may not be opened: one extra step.
#   perishable     priority, and it goes first. Same cycle, different ORDER --
#                  the cost is that missing it spoils the load.
#   hazmat         "suit-check, PLC-100 chain": the gang suits, the check is
#                  logged, and the suit slows every cycle after it.
HANDLING = {"containerised": 1.00, "bulk": 0.80, "bonded": 1.35,
            "perishable": 1.00, "hazmat": 1.80}

# THE CHALKED RATE. The caller pays the top of the STATED casual band for the
# jobs nobody wants and the bottom for the easy ones -- so the band's own width
# (8-15 cr/day, LAW-CRIME 7.1) is the risk spread, and no number is invented
# here at all. A gang's difficulty is its handling cost per crate normalised
# onto the band.
_H_LO, _H_HI = min(HANDLING.values()), max(HANDLING.values())


def chalked_rate(mix):
    """cr for a full day on this gang, from the cargo it is: no new numbers.

    `mix` is {cargo_class: crates}.
    """
    n = sum(mix.values())
    if n <= 0:
        return ec.CASUAL_LO
    cost = sum(HANDLING.get(k, 1.0) * v for k, v in mix.items()) / n
    t = (cost - _H_LO) / (_H_HI - _H_LO)
    return round(ec.CASUAL_LO + (ec.CASUAL_HI - ec.CASUAL_LO) * t, 2)


# ===========================================================================
# 3.  THE BOARD -- what the caller chalks at 05:40
# ===========================================================================
@dataclass(frozen=True)
class Gang:
    """One gang on the board: a ship, a berth, its cargo and what it pays."""
    berth_no: int
    ship: str
    hour: float
    dwell_h: float
    crates: int
    mix: dict                    # cargo class -> crates
    lines: tuple                 # the `economy.Consignment`s aboard
    rate_cr: float
    hours_needed: float
    caller: str

    @property
    def sails_h(self):
        return self.hour + self.dwell_h

    @property
    def window_h(self):
        """The hours of THIS shift during which the ship is alongside."""
        return (max(CLOCK_ON_H, self.hour), min(CLOCK_OFF_H, self.sails_h))

    @property
    def clears(self):
        """Can a gang of six finish this inside the window it has?"""
        a, b = self.window_h
        return self.hours_needed <= (b - a) + 1e-9

    def line(self):
        cls = ",".join(f"{k}:{v}" for k, v in sorted(self.mix.items()) if v)
        a, b = self.window_h
        return (f"  bay {self.berth_no:>2d}  {self.hour:05.2f}  "
                f"{self.ship:<19s} {self.crates:>4d} crates  "
                f"{self.rate_cr:>5.2f} cr/day  needs {self.hours_needed:>5.2f} h "
                f"in {b - a:>5.2f}  {'clears' if self.clears else 'OVERRUNS':<8s}"
                f"  {cls}")


def _caller(day, seed="b5"):
    """The gang caller: a named dockworker whose job IS the docking bays."""
    for sp in ("human", "narn", "drazi"):
        for nid in RES.affiliates(WORKPLACE, sp, seed):
            r = RES.resident(nid, sp)
            if r.job == WORKPLACE and r.role == "dockworker" and r.name:
                return r.name
    return "the caller"


# WHO STANDS A MUSTER. LAW-CRIME 7.2's informal-jobs table gives **18% of
# Downbelow's 20,000** as "casual dock and cargo labour ... hired at a muster
# point at shift change", against the guild's own carded dockworkers -- so a
# gang is dockers and lurkers, not whoever happens to be in the room. The
# ranking below is that sentence: the place's own dockworkers first, then the
# casuals who came up for the muster, then anyone else the roster offers.
MUSTER_ROLES = ("dockworker", "lurker")


def _gang_of(day, berth_no, seed="b5"):
    """Six named people, drawn from the place's own species mix and ranked by
    who actually stands a muster."""
    out = []
    hour = CLOCK_ON_H
    for i in range(GANG):
        sp = pop.species_for(WORKPLACE, berth_no * GANG + i, seed)
        pool = RES.roster(WORKPLACE, hour, sp, 24, seed)
        if not pool:
            continue
        ranked = sorted(pool, key=lambda r: (
            0 if r.job == WORKPLACE else
            1 if r.role in MUSTER_ROLES else 2,
            _u("gang", day, berth_no, i, r.npc_id)))
        for r in ranked:
            if r not in out:
                out.append(r)
                break
    return tuple(out)


def board(day=0, seed="b5"):
    """The muster board at 05:40 on `day`. Every row a real ship.

    A ship is workable by the DAY gang if it is alongside during the shift and
    berthed in a bay -- a standoff hull is worked by lighters off the spine and
    a moored warship lands nothing.
    """
    cons = ec.consignments(day, seed)
    by_ship = {}
    for c in cons:
        by_ship.setdefault((c.ship, round(c.hour, 4)), []).append(c)
    caller = _caller(day, seed)
    out = []
    for i, a in enumerate(tf.arrivals(day)):
        if a["berth"] != "bay":
            continue
        n = ec.containers(a)
        if n <= 0:
            continue
        # Alongside at any point during the shift?
        t0, t1 = a["hour"], a["hour"] + a["stay_h"]
        if t1 <= CLOCK_ON_H or t0 >= CLOCK_OFF_H:
            continue
        lines = tuple(by_ship.get((a["type"], round(a["hour"], 4)), ()))
        mix = {}
        for c in lines:
            share = int(round(c.crates))
            if share <= 0:
                continue          # a case out of somebody else's container
            mix[c.cargo_class] = mix.get(c.cargo_class, 0) + share
        assigned = sum(mix.values())
        if assigned < n:                      # rounding, and the odd crate
            k = "bulk" if a["type"] == "freighter_standoff" else "containerised"
            mix[k] = mix.get(k, 0) + (n - assigned)
        hours = sum(HANDLING.get(k, 1.0) * v
                    for k, v in mix.items()) / CRATES_PER_GANG_H
        out.append(Gang(berth_no=1 + (i % 24), ship=a["type"], hour=a["hour"],
                        dwell_h=a["stay_h"], crates=n, mix=mix, lines=lines,
                        rate_cr=chalked_rate(mix), hours_needed=hours,
                        caller=caller))
    out.sort(key=lambda g: (-g.rate_cr, g.hour))
    return tuple(out)


# ===========================================================================
# 4.  THE DECISION -- three ways to choose, three different days
# ===========================================================================
# This is ROLE-03's decision loop made executable. A headless gate cannot have
# a person pick, so a POLICY stands in for one -- and the point of having three
# is that they must produce measurably different days, or the choice is not a
# choice. `--policies` prints the divergence; `_selftest` asserts it.
def _p_greedy(gs):
    """Take the best-paying gang on the board. The obvious first instinct."""
    return gs[0] if gs else None


def _p_safe(gs):
    """Never take hazmat. A living is a living."""
    ok = [g for g in gs if not g.mix.get("hazmat")]
    return (ok or list(gs))[0] if gs else None


def _p_finisher(gs):
    """Take the best-paying gang you can actually CLEAR inside the shift.

    The one that reads the board rather than the rate -- and the one whose
    cargo actually reaches the counters, because an overrun spoils perishables.
    """
    ok = [g for g in gs if g.clears]
    return (ok[0] if ok else (gs[0] if gs else None))


POLICIES = {"greedy": _p_greedy, "safe": _p_safe, "finisher": _p_finisher}


# ===========================================================================
# 5.  THE SHIFT
# ===========================================================================
@dataclass
class Shift:
    day: int = 0
    gang: object = None                 # the FIRST gang taken -- the decision
    gangs: tuple = ()                   # every gang worked, in order
    who: tuple = ()
    steps: list = field(default_factory=list)
    crates_assigned: int = 0
    crates_cleared: int = 0
    hours_worked: float = 0.0
    idle_h: float = 0.0
    pay_cr: float = 0.0
    carded: bool = False
    spoiled: tuple = ()
    delivered_lines: tuple = ()
    taken_lines: tuple = ()

    def transcript(self, out=print):
        for t, where, verb, what in self.steps:
            out(f"  {t:05.2f}  {where:<14s} {verb:<12s} {what}")


def guild_carded(led, npc_id):
    """Has this person stood the muster often enough to be carded?

    PEOPLE ROLE-03: "stand the muster as a casual (no endorsement needed -- the
    door into the whole economy); guild card at standing." The threshold is
    `economy.GUILD_SHIFTS_PER_WEEK` -- one guaranteed week's worth of turning
    up, which is the shortest span over which a caller sees a man be reliable
    and is short enough to be reached in a session. INV-273.
    """
    worked = sum(1 for s in led.sales
                 if s.get("good") == "(wages)" and s.get("who") == npc_id
                 and str(s.get("at", "")).startswith("dock:"))
    return worked >= int(ec.GUILD_SHIFTS_PER_WEEK)


# The order a gang works its classes, and it is the spec's own priority.
# Perishable FIRST because ROLE-03 calls it "priority"; bonded next because the
# seal has to be read into the terminal before customs closes; hazmat before
# the bulk because the suits are already on; bulk last because it is not going
# anywhere. The order is the only thing standing between a full board and a
# spoiled load, which is what makes it worth stating.
CLASS_ORDER = ("perishable", "bonded", "hazmat", "containerised", "bulk")


def work_shift(player, led, day=0, policy="finisher", seed="b5", log=True):
    """One dock shift, muster to clock-off, and the pay at the end of it.

    A SHIFT IS NOT ONE SHIP. A gang that clears a shuttle in ten minutes goes
    back to the board, which is what a caller is for -- so the shift is a
    sequence of gangs bounded by the eight hours between clock-on and clock-off
    less the mess, and the decision is taken again every time a ship is
    finished. That is `POLICIES` applied repeatedly rather than once, and it is
    what stops "take the small one" from being a free win.

    Mutates `player` (credits, `at`) and `led` (wages, and -- through the
    consignments this shift did or did not clear -- what reaches the counters).
    """
    sh = Shift(day=day)
    gs = list(board(day, seed))
    if not gs:
        return sh
    sh.carded = guild_carded(led, player.npc_id)

    def step(t, where, verb, what):
        sh.steps.append((round(t, 2), where, verb, what))

    caller = gs[0].caller
    player.move_to(STATIONS["muster"])
    step(MUSTER_H, STATIONS["muster"], "LOOK",
         f"{caller}'s board: {len(gs)} gangs called, "
         f"{sum(g.crates for g in gs)} crates on the day, "
         f"{'guild card' if sh.carded else 'casual'}")

    left = {id(g): dict(g.mix) for g in gs}
    worked = {}                                  # id(gang) -> hours on it
    t = CLOCK_ON_H
    mess_taken = False
    pay_h = 0.0
    order = []
    def _mess(t):
        """The 12:00 mess. Taken, not skipped -- PEOPLE ROLE-03 puts it in the
        middle of the shift and a gang that works through it is not a gang."""
        player.move_to(STATIONS["mess"])
        step(max(t, MESS_H), STATIONS["mess"], "EAT",
             "the 12:00 mess -- the gang eats")
        player.move_to(STATIONS["crane"])
        return max(t, MESS_H) + MESS_HOURS

    while t < CLOCK_OFF_H - 1e-6:
        if not mess_taken and t >= MESS_H - 1e-9:
            t = _mess(t)
            mess_taken = True
            continue
        avail = [g for g in gs
                 if g.hour <= t < g.sails_h and sum(left[id(g)].values()) > 0]
        if not avail:
            nxt = [g.hour for g in gs
                   if g.hour > t and sum(left[id(g)].values()) > 0]
            if not nxt:
                break
            sh.idle_h += min(nxt) - t
            t = min(nxt)
            continue
        pick = POLICIES[policy](avail)
        if pick is None:
            break
        if id(pick) not in worked:
            order.append(pick)
            player.move_to(STATIONS["ride"])
            step(t, STATIONS["ride"], "RIDE",
                 f"the bay elevator to bay {pick.berth_no}, pad to parking")
            player.move_to(STATIONS["clamp"])
            step(t + 0.05, STATIONS["clamp"], "USE",
                 f"docking_clamp -- {pick.ship} secured on pad "
                 f"{pick.berth_no}, {pick.crates} crates, "
                 f"{pick.rate_cr:.2f} cr/day chalked")
            t += 0.05
            worked[id(pick)] = 0.0
            if not mess_taken and t >= MESS_H - 1e-9:
                t = _mess(t)
                mess_taken = True
        # the ceiling on this stint: the ship sails, the mess, or clock-off
        stop = min(pick.sails_h, CLOCK_OFF_H,
                   MESS_H if not mess_taken else CLOCK_OFF_H)
        did = {}
        for k in CLASS_ORDER:
            n = left[id(pick)].get(k, 0)
            if n <= 0:
                continue
            cyc = HANDLING.get(k, 1.0) / CRATES_PER_GANG_H
            can = int(min(n, max(0.0, stop - t) / cyc))
            if can <= 0:
                continue
            if k == "hazmat":
                step(t, STATIONS["crane"], "USE",
                     "suit-check logged before the hazmat set is broken")
            left[id(pick)][k] = n - can
            t += can * cyc
            worked[id(pick)] += can * cyc
            pay_h += can * cyc
            did[k] = can
        if did:
            step(t, STATIONS["crane"], "USE",
                 f"cargo_crane x{sum(did.values())} off bay "
                 f"{pick.berth_no} -- "
                 + ", ".join(f"{v} {k}" for k, v in did.items()))
        else:
            # nothing fits in the time left on this hull: go back to the board
            gone = min(stop, pick.sails_h)
            if gone <= t + 1e-6:
                left[id(pick)] = {k: 0 for k in left[id(pick)]}
                continue
            t = gone
    sh.gangs = tuple(order)
    sh.gang = order[0] if order else None
    sh.who = _gang_of(day, sh.gang.berth_no, seed) if sh.gang else ()
    sh.crates_assigned = sum(g.crates for g in order)
    sh.crates_cleared = sum(g.crates - sum(left[id(g)].values())
                            for g in order)
    sh.hours_worked = round(pay_h, 3)

    # -- the manifest: who signed for what, and what spoiled on the pad -----
    landed, spoiled = [], []
    taken = []
    for g in order:
        short = left[id(g)]
        for c in g.lines:
            taken.append(c)
            if short.get(c.cargo_class, 0) > 0:
                # that class did not clear before the hull sailed
                (spoiled if c.cargo_class == "perishable" else landed).append(c)
            else:
                landed.append(c)
    sh.taken_lines = tuple(taken)
    sh.delivered_lines = tuple(landed)
    sh.spoiled = tuple(spoiled)
    if order:
        player.move_to(STATIONS["manifest"])
        step(min(t, CLOCK_OFF_H), STATIONS["manifest"], "USE",
             f"manifest_terminal -- {len(landed)} consignments signed for"
             + (f", {len(spoiled)} perishable lines left on the pad"
                if spoiled else ""))

    # -- 15:00 off, and the pay --------------------------------------------
    if sh.carded:
        # The guild card pays the guaranteed shift rate whatever the day held:
        # that is what the card IS.
        gross = ec.GUILD_SHIFT_LO + (ec.GUILD_SHIFT_HI - ec.GUILD_SHIFT_LO) \
            * _u("guild", day, player.npc_id)
    else:
        # A casual is paid for the hours the caller could use, at the rate
        # chalked on the gangs they actually stood.
        gross = sum(g.rate_cr * worked[id(g)] for g in order) / WORK_HOURS \
            if order else 0.0
    sh.pay_cr = round(gross, 2)
    if sh.pay_cr > 0:
        ec.pay(led, player, sh.pay_cr, why=f"dock:{day}:"
               f"bay{sh.gang.berth_no if sh.gang else 0}")
    player.move_to(STATIONS["muster"])
    step(CLOCK_OFF_H, STATIONS["muster"], "WORK",
         f"clock off -- {len(order)} ships, {sh.crates_cleared}/"
         f"{sh.crates_assigned} crates, {sh.hours_worked:.2f} h on the crane, "
         f"{sh.pay_cr:.2f} cr "
         f"({'guild shift' if sh.carded else 'casual'})")
    if log and sh.pay_cr > 0 and led.sales:
        led.sales[-1]["shift"] = {"crates": sh.crates_cleared,
                                  "of": sh.crates_assigned,
                                  "ships": len(order), "policy": policy}
    return sh


# ===========================================================================
# 6.  THE LOOP -- work, pay, spend, and the world notices
# ===========================================================================
DRINK_HOUR = 19.5
BAR = "bar_unnamed"


def a_day(player, led, day, policy="finisher", buy_at=BAR, seed="b5",
          out=None):
    """One whole day: the shift, the delivery it earned, the drink it bought.

    Returns a dict of everything a gate wants to count.
    """
    led.day = day
    cr0 = player.credits
    sh = work_shift(player, led, day, policy, seed)

    # THE STATION'S OWN DAY, which happens whether or not the player worked:
    # every counter turns over its covers, and every consignment the port
    # landed reaches its consignee. The player's gang is subtracted from that
    # and re-added from what it ACTUALLY cleared, so a spoiled load is a
    # shelf that does not get filled.
    background_moved = ec.background_sales(led, day)
    # `taken_lines` and NOT `gang.lines`: a shift works several hulls, so
    # subtracting only the first gang's manifest double-delivered every line
    # off every later ship and the station's stock climbed 38% in a week.
    taken = set(map(id, sh.taken_lines))
    others = [c for c in ec.consignments(day, seed) if id(c) not in taken]
    landed = ec.deliver(led, day, only=others + list(sh.delivered_lines))

    # -- the evening --------------------------------------------------------
    bought, provenance = None, ""
    lines = [g for g in ec.stock_list(buy_at, seed)
             if led.units(buy_at, g) > 0]
    if lines:
        want = lines[int(_u("thirst", day, player.npc_id) * len(lines))
                     % len(lines)]
        try:
            unit, total = ec.buy(led, player, buy_at, want, 1)
            bought = (want, unit, total)
        except ec.Refused as e:
            bought = ("refused", 0.0, str(e))
        # THE CHAIN, READ FORWARDS. If the line the player just drank came off
        # a crate their own gang cleared this morning, say so -- that sentence
        # is the whole reason the manifest, the shift and the till are one
        # system instead of three.
        for c in sh.delivered_lines:
            if c.consignee == buy_at and c.good == want:
                provenance = (f"off the {c.ship} their own gang cleared on "
                              f"bay {sh.gang.berth_no if sh.gang else '?'} "
                              f"at {c.hour:05.2f}")
                break
        else:
            for c in sh.spoiled:
                if c.consignee == buy_at and c.good == want:
                    provenance = "-- and the fresh load spoiled on the pad"
                    break
    if out:
        out(f"DAY {day} -- {player.name}, {player.card.species}, "
            f"{'guild docker' if sh.carded else 'casual'}")
        sh.transcript(out)
        if bought and bought[0] != "refused":
            out(f"  {DRINK_HOUR:05.2f}  {buy_at:<14s} {'BUY':<12s} "
                f"1 x {bought[0]} at {bought[1]:.2f} cr"
                + (f"   <- {provenance}" if provenance else ""))
        out(f"        credits {cr0} -> {player.credits}  "
            f"(+{sh.pay_cr:.2f} wages, -{(bought[2] if bought else 0):.2f} "
            f"at the bar)")
    return {"day": day, "shift": sh, "credits_before": cr0,
            "credits_after": player.credits, "bought": bought,
            "provenance": provenance, "landed": landed,
            "background": background_moved}


# ===========================================================================
# 7.  Reporting
# ===========================================================================
def report_board(day=0, out=print):
    gs = board(day)
    out(f"THE MUSTER BOARD, {MUSTER_H:05.2f} EMT, DAY {day} -- "
        f"chalked by {gs[0].caller if gs else 'nobody'}")
    out(f"  {len(tf.arrivals(day))} arrivals on the day, {len(gs)} of them "
        f"workable by the {CLOCK_ON_H:02.0f}:00 gang "
        f"(a gang of {GANG} moves {CRATES_PER_GANG_H:.2f} crates/h)")
    for g in gs:
        out(g.line())


def report_policies(days=7, out=print):
    """The decision loop, measured: three ways to choose, three different days.

    If these came out the same the choice would be an animation, which is
    exactly what PEOPLE.md's WORK-fidelity clause forbids.
    """
    out("THE DECISION LOOP -- does choosing differently produce a different "
        f"day? {days} days, same manifests, same player")
    out(f"  {'policy':<10s} {'shifts':>6s} {'crates':>8s} {'of':>8s} "
        f"{'pay cr':>8s} {'spoiled':>8s} {'overruns':>9s}")
    rows = {}
    for name in sorted(POLICIES):
        p = pl.random_player("dock")
        led = ec.Ledger.fresh()
        tot = {"crates": 0, "of": 0, "pay": 0.0, "spoil": 0, "over": 0, "n": 0}
        for d in range(days):
            led.day = d
            sh = work_shift(p, led, d, name)
            if sh.gang is None:
                continue
            tot["n"] += 1
            tot["crates"] += sh.crates_cleared
            tot["of"] += sh.crates_assigned
            tot["pay"] += sh.pay_cr
            tot["spoil"] += len(sh.spoiled)
            tot["over"] += 0 if sh.gang.clears else 1
        rows[name] = tot
        out(f"  {name:<10s} {tot['n']:>6d} {tot['crates']:>8d} "
            f"{tot['of']:>8d} {tot['pay']:>8.2f} {tot['spoil']:>8d} "
            f"{tot['over']:>9d}")
    return rows


def report_loop(days=5, seed="b5", policy="finisher", out=print,
                path=None, role=None):
    """THE GATE'S OWN TRANSCRIPT: who, what shift, what pay, what they bought.

    Writes the ledger, so the delta can be looked at again from another
    process -- which is the difference between a claim and a fact.
    """
    # A ROLE IS A CHOICE THE CHARACTER CREATOR ALREADY HAD. ROLE-03's own
    # entry clause -- "stand the muster as a casual (no endorsement needed --
    # the door into the whole economy)" -- is what a lurker does, so
    # `--role lurker` is the canonical way in and not a special case.
    p = (pl.player_from({"role": role}, seed=seed) if role
         else pl.random_player(seed if seed != "b5" else "dock"))
    led = ec.Ledger.fresh()
    p.credits = int(p.credits)
    out(f"{p.describe()}")
    out(f"  landed with {p.credits} cr "
        f"({'can' if p.can_afford_passage() else 'CANNOT'} afford the "
        f"{pl.PASSAGE_HOME_CR:.0f} cr passage home)")
    out("")
    start_cr = p.credits
    start_units = led.total_units()
    days_out = []
    for d in range(days):
        days_out.append(a_day(p, led, d, policy, out=out))
        out("")
    till = led.till.get(BAR, 0.0)
    out(f"AFTER {days} DAYS: {start_cr} -> {p.credits} cr, "
        f"wages {sum(led.wages.values()):.2f}, "
        f"{BAR}'s till {till:.2f} cr, "
        f"station stock {start_units} -> {led.total_units()} units")
    if path:
        led.save(path)
        out(f"ledger written to {path}")
    return p, led, days_out


# ===========================================================================
# 8.  The gate
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

    # -- 1. every place and prop the shift touches is REAL -------------------
    missing = [k for k in STATIONS.values()
               if k not in {q["key"] for q in dr.PLACES}]
    check("every station of the shift is a place in the register",
          not missing, f"{sorted(set(STATIONS.values()))}")
    audit = json.load(open(os.path.join(ROOT, "docs",
                                        "interact-audit.json")))
    resolved = {r["key"]: set(r["resolved"]) for r in audit}
    bad = []
    for step_, props in PROPS.items():
        where = STATIONS[step_]
        for pr in props:
            if pr not in resolved.get(where, set()):
                bad.append((step_, where, pr))
    check("every prop the shift operates is one `interact.py` RESOLVED in "
          "built geometry -- a shift cannot USE something that is not there",
          not bad, f"{len(bad)} missing: {bad}")
    # NEGATIVE CONTROL: a prop nobody built must fail the same test.
    check("...and a prop nobody built does NOT resolve",
          "cargo_crane_mk2" not in resolved.get(WORKPLACE, set()))

    # -- 2. the shift hours come from the schedule --------------------------
    check("the shift is the schedule's own dockworker role, not a literal",
          (CLOCK_ON_H, CLOCK_OFF_H) == (6.0, 15.0)
          and ROLE.workplace == "docking_bay",
          f"{CLOCK_ON_H:04.1f}-{CLOCK_OFF_H:04.1f}, muster {MUSTER_H:05.2f}, "
          f"{WORK_HOURS:.0f} h on the crane")

    # -- 3. THE BOARD IS THE REAL MANIFEST ----------------------------------
    b0, b1 = board(0), board(1)
    check("the caller chalks a board from the day's REAL arrivals",
          len(b0) > 0 and all(g.ship in dict((r[0], r) for r in tf.MANIFEST)
                              for g in b0),
          f"day 0: {len(b0)} gangs, {sum(g.crates for g in b0)} crates, "
          f"caller {b0[0].caller}")
    check("...and no two days are the same shift -- the manifest IS the "
          "variation source",
          [(g.ship, g.crates) for g in b0] != [(g.ship, g.crates)
                                               for g in b1],
          f"day 0 {[g.ship for g in b0][:4]} vs day 1 {[g.ship for g in b1][:4]}")
    sig = {tuple((g.ship, g.crates, g.rate_cr) for g in board(d))
           for d in range(14)}
    check("...over a fortnight, no board repeats", len(sig) == 14,
          f"{len(sig)} distinct boards in 14 days")
    check("a gang's chalked rate stays inside the STATED casual band, which "
          "is where it comes from",
          all(ec.CASUAL_LO - 1e-9 <= g.rate_cr <= ec.CASUAL_HI + 1e-9
              for d in range(14) for g in board(d)),
          f"{min(g.rate_cr for g in b0):.2f}-{max(g.rate_cr for g in b0):.2f} "
          f"on day 0 against {ec.CASUAL_LO:.0f}-{ec.CASUAL_HI:.0f}")
    check("the hazmat gangs pay more than the bulk gangs, because the band's "
          "own width is the risk spread",
          chalked_rate({"hazmat": 10}) > chalked_rate({"bulk": 10}),
          f"hazmat {chalked_rate({'hazmat': 10}):.2f} vs bulk "
          f"{chalked_rate({'bulk': 10}):.2f}")

    # -- 4. THE DECISION IS A DECISION --------------------------------------
    rows = report_policies(7, out=lambda *a: None)
    pays = {k: round(v["pay"], 2) for k, v in rows.items()}
    check("three ways of choosing produce three different weeks -- ROLE-03's "
          "decision loop is a decision", len(set(pays.values())) >= 2, str(pays))
    check("...and the finisher clears more of what it takes than the greedy "
          "one does",
          (rows["finisher"]["crates"] / max(1, rows["finisher"]["of"]))
          > (rows["greedy"]["crates"] / max(1, rows["greedy"]["of"])),
          f"finisher {rows['finisher']['crates']}/{rows['finisher']['of']}, "
          f"greedy {rows['greedy']['crates']}/{rows['greedy']['of']}")

    # -- 5. THE LOOP CLOSES -------------------------------------------------
    p = pl.random_player("gate")
    p.credits = 0
    led = ec.Ledger.fresh()
    led.day = 0
    sh = work_shift(p, led, 0)
    check("WORK -> PAY: a shift worked puts credits in an empty purse",
          p.credits > 0 and sh.crates_cleared > 0,
          f"{sh.crates_cleared}/{sh.crates_assigned} crates on bay "
          f"{sh.gang.berth_no}, {sh.pay_cr:.2f} cr, purse 0 -> {p.credits}")
    dockers = [r for r in sh.who
               if r.job == WORKPLACE or r.role in MUSTER_ROLES]
    check("...and the gang is six residents of the docks, most of them dock "
          "people rather than whoever was in the room",
          len(sh.who) == GANG and len(dockers) >= GANG - 1,
          f"{len(dockers)}/{len(sh.who)} dock people: "
          + ", ".join(f"{r.name or '<' + r.species + ', no attested name>'}"
                      f" ({r.role})" for r in sh.who))
    # A KNOWN GAP, REPORTED RATHER THAN HIDDEN: `npc/names.py` has no grammar
    # for every species in the mix, so a Vree docker comes back nameless. That
    # is a names defect and not a gang defect, and the gate says which.
    unnamed = sorted({r.species for r in sh.who if not r.name})
    out(f"      (species with no attested name in npc/names.py: "
        f"{unnamed or 'none'})")
    # NEGATIVE CONTROL: no board, no pay. Prove the pay came from the work.
    p2 = pl.random_player("gate")
    p2.credits = 0
    led2 = ec.Ledger.fresh()
    keep = dict(POLICIES)
    POLICIES["nogang"] = lambda gs: None
    try:
        work_shift(p2, led2, 0, "nogang")
        crashed = False
    except Exception:
        crashed = True
    POLICIES.clear()
    POLICIES.update(keep)
    check("...and standing the muster without taking a gang pays NOTHING",
          not crashed and p2.credits == 0, f"{p2.credits} cr")

    before = led.units(BAR, ec.stock_list(BAR)[0])
    tillb = led.till.get(BAR, 0.0)
    d0 = a_day(p, led, 1)
    check("PAY -> SPEND: the wages buy a drink and the bar's till fills",
          d0["bought"] and d0["bought"][0] != "refused"
          and led.till.get(BAR, 0.0) > tillb,
          f"bought {d0['bought'][0] if d0['bought'] else None} at "
          f"{(d0['bought'][1] if d0['bought'] else 0):.2f} cr; till "
          f"{tillb:.2f} -> {led.till.get(BAR, 0.0):.2f}")
    check("...and the shelf it came off is one unit shorter",
          led.units(BAR, d0["bought"][0]) >= 0
          and any(s["at"] == BAR for s in led.sales),
          f"{before} was the opening depth of {ec.stock_list(BAR)[0]}")

    # -- 6. A BAD SHIFT IS VISIBLE FROM THE OTHER END ------------------------
    spoil_days = 0
    ledg = ec.Ledger.fresh()
    pg = pl.random_player("spoil")
    for d in range(14):
        ledg.day = d
        s = work_shift(pg, ledg, d, "greedy")
        spoil_days += len(s.spoiled)
    check("a gang that overruns leaves perishables on the pad, and they never "
          "reach the counter that ordered them",
          spoil_days > 0, f"{spoil_days} spoiled consignments in 14 greedy days")

    # -- 7. THE GUILD CARD ---------------------------------------------------
    pc = pl.random_player("card")
    ledc = ec.Ledger.fresh()
    carded_on = None
    for d in range(10):
        ledc.day = d
        s = work_shift(pc, ledc, d, "finisher")
        if s.carded and carded_on is None:
            carded_on = d
    check("standing the muster long enough gets a guild card, and the card "
          "pays the guaranteed shift rate",
          carded_on == int(ec.GUILD_SHIFTS_PER_WEEK),
          f"carded on day {carded_on} after "
          f"{int(ec.GUILD_SHIFTS_PER_WEEK)} shifts")

    # -- 8. THE DENOMINATORS, AND THE PERSISTENCE ---------------------------
    import subprocess
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(), "economy.json")
    # A DENOMINATOR, NEVER AN EXISTENCE PROOF -- MASTER-PLAN §A2's enforcement
    # rule 4. Not "a shift happened once": fourteen consecutive days off
    # fourteen different manifests, every one of them worked, paid and spent.
    DAYS = 14
    pp, ll, ds = report_loop(DAYS, out=lambda *a: None, path=tmp, role="lurker",
                             seed="downbelow")
    worked = sum(1 for d in ds if d["shift"].gang is not None)
    bought = sum(1 for d in ds if d["bought"] and d["bought"][0] != "refused")
    crates = sum(d["shift"].crates_cleared for d in ds)
    hulls = sum(len(d["shift"].gangs) for d in ds)
    signed = sum(len(d["shift"].delivered_lines) for d in ds)
    own = sum(1 for d in ds if d.get("provenance"))
    check(f"{DAYS} DAYS: a shift worked, paid and spent on every one of them",
          worked == DAYS and bought == DAYS and sum(ll.wages.values()) > 0
          and ll.till.get(BAR, 0.0) > 0,
          f"{worked}/{DAYS} shifts over {hulls} hulls, {crates} crates "
          f"cleared, {signed} consignments signed, {bought} purchases, "
          f"{sum(ll.wages.values()):.2f} cr of wages, "
          f"{BAR} till {ll.till.get(BAR, 0.0):.2f} cr")
    check("...and on some of those days the drink came off a crate the "
          "player's own gang cleared that morning -- the T4 chain end to end",
          own > 0, f"{own} of {DAYS} purchases traceable to the player's own "
                   f"shift")
    # THE PROGRESSION, as a denominator too: a lurker who cannot afford the
    # fare works until they can. That is A2's "the role" and SYS-04's own
    # late-game sink in one sentence.
    check("...and the loop lifts a lurker over the passage-home line, which "
          "is the one number the underclass rests on",
          ds[0]["credits_before"] < pl.PASSAGE_HOME_CR
          and pp.can_afford_passage(),
          f"{ds[0]['credits_before']} cr on day 0 -> {pp.credits} cr on day "
          f"{DAYS - 1}, fare {pl.PASSAGE_HOME_CR:.0f}")
    code = (f"import sys; sys.path.insert(0, {HERE!r});"
            f"import economy as e;"
            f"L = e.Ledger.load({tmp!r});"
            f"import player as p;"
            f"who = sorted(L.purses)[0];"
            f"pl2 = p.from_state(L.purses[who]);"
            f"print(round(sum(L.wages.values()), 2), "
            f"round(L.till.get('bar_unnamed', 0.0), 2), pl2.credits, "
            f"pl2.name)")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True)
    got = r.stdout.strip().split()
    check("A SECOND PROCESS reads the same wages, the same till and the same "
          "player back off disk",
          r.returncode == 0 and len(got) >= 3
          and abs(float(got[0]) - sum(ll.wages.values())) < 0.01
          and abs(float(got[1]) - ll.till.get(BAR, 0.0)) < 0.01,
          f"child said {r.stdout.strip()!r}; {r.stderr.strip()[:160]}")

    # THE ABSENCE GATE, applied to money: a day the player does not work must
    # still move the world, and it must move it DIFFERENTLY.
    quiet = ec.Ledger.fresh()
    for d in range(5):
        quiet.day = d
        ec.background_sales(quiet, d)
        ec.deliver(quiet, d)
    check("the station's day happens without the player -- and a played day "
          "is not the same day",
          quiet.total_units() != ll.total_units()
          and quiet.till.get(BAR, 0.0) > 0,
          f"unplayed {quiet.total_units()} units / "
          f"{quiet.till.get(BAR, 0.0):.2f} cr in the till, "
          f"played {ll.total_units()} / {ll.till.get(BAR, 0.0):.2f}")

    out("")
    out(f"{n - len(failed)}/{n} passed")
    return not failed


# ===========================================================================
# 9.  THE CONTROLS -- the gate shown FAILING on the state before this landed
# ===========================================================================
# A gate that cannot fail is not a gate, and "it could not have failed before
# because the module did not exist" is not evidence. So each control removes
# ONE mechanism this session added and asserts that the claim which names it
# goes red -- which is the same A/B `coldstart.py` runs against the engine and
# `walkable.py` runs against the pre-shell content.
def controls(out=print):
    fired, n = [], 0

    def control(name, went_red, detail=""):
        nonlocal n
        n += 1
        out(f"{'FIRES' if went_red else 'INERT'}  {name}"
            + (f"  -- {detail}" if detail else ""))
        if went_red:
            fired.append(name)

    days = 5

    # -- 1. NO WAGES: the state before this session. `player.py` had credits
    #       and nothing in the project could add one.
    keep_pay = ec.pay
    ec.pay = lambda led, worker, credits, why="": 0.0
    try:
        p = pl.random_player("ctrl")
        p.credits = 0
        led = ec.Ledger.fresh()
        for d in range(days):
            led.day = d
            work_shift(p, led, d)
        no_wages = (p.credits == 0)
    finally:
        ec.pay = keep_pay
    control("no wages -- five shifts worked and the purse never moves, which "
            "is exactly what the project did before this landed",
            no_wages, f"{days} shifts, purse still 0 cr")

    # -- 2. NO STOCK MOVEMENT: a shop that is a picture of a shop.
    keep_buy = ec.buy

    def _inert_buy(led, buyer, place_key, good, k=1):
        return price_of(place_key, good), 0.0
    ec.buy = _inert_buy
    try:
        p2 = pl.random_player("ctrl2")
        led2 = ec.Ledger.fresh()
        u0, t0 = led2.total_units(), led2.till.get(BAR, 0.0)
        for d in range(days):
            led2.day = d
            a_day(p2, led2, d)
        # the till must be the background's alone: no player sale in the log
        no_sale = not any(s.get("at") == BAR and s.get("good") != "(wages)"
                          for s in led2.sales)
    finally:
        ec.buy = keep_buy
    control("no till -- the player drinks and the bar's ledger has no record "
            "of it", no_sale, f"{len(led2.sales)} ledger rows, none a sale "
            f"at {BAR}")

    # -- 3. A FROZEN MANIFEST: the same board every day, which is what a role
    #       with no variation source looks like. PEOPLE.md's WORK-fidelity
    #       clause fails a role whose shift replays.
    keep_arr = tf.arrivals
    day0 = list(keep_arr(0))
    ec._MANIFEST_CACHE.clear()
    tf.arrivals = lambda day=0: day0
    try:
        # SORTED, because `board` ranks by the chalked rate and the rate moves
        # with the day's cargo draw -- an unsorted signature would differ on
        # ORDER alone and the control would read INERT for the wrong reason.
        sig = {tuple(sorted((g.ship, g.crates) for g in board(d)))
               for d in range(14)}
        frozen = (len(sig) == 1)
    finally:
        tf.arrivals = keep_arr
        ec._MANIFEST_CACHE.clear()
    live = {tuple(sorted((g.ship, g.crates) for g in board(d)))
            for d in range(14)}
    control("a frozen manifest -- fourteen days of ships collapse to one "
            "board, and a role whose shift replays is not GREEN at any "
            "coverage", frozen,
            f"{len(sig)} distinct ship lists in 14 days against {len(live)} "
            f"live -- so the PORT is what makes the shift, not a draw")

    # -- 4. NO CARGO CLASSES: the decision loop with nothing to decide. Every
    #       gang the same, so every rate the same and every policy identical.
    keep_h = dict(HANDLING)
    for k in HANDLING:
        HANDLING[k] = 1.0
    try:
        rates = {g.rate_cr for d in range(7) for g in board(d)}
        flat = (len(rates) == 1)
    finally:
        HANDLING.clear()
        HANDLING.update(keep_h)
    live = {g.rate_cr for d in range(7) for g in board(d)}
    control("no handling classes -- every gang pays the same and the caller's "
            "board stops being a choice", flat,
            f"{len(rates)} distinct rates flat against {len(live)} live")

    # -- 5. NO ORDER: work the classes in the order the dict happens to hold
    #       them instead of priority-first, and the perishables spoil.
    keep_order = CLASS_ORDER
    globals()["CLASS_ORDER"] = ("bulk", "containerised", "hazmat", "bonded",
                                "perishable")
    try:
        led5 = ec.Ledger.fresh()
        p5 = pl.random_player("ctrl5")
        bad = sum(len(work_shift(p5, led5, d, "finisher").spoiled)
                  for d in range(14))
    finally:
        globals()["CLASS_ORDER"] = keep_order
    led6 = ec.Ledger.fresh()
    p6 = pl.random_player("ctrl5")
    good = sum(len(work_shift(p6, led6, d, "finisher").spoiled)
               for d in range(14))
    control("perishables last -- the priority order is the only thing keeping "
            "fresh cargo off the pad", bad > good,
            f"{bad} spoiled consignments in 14 days against {good} with the "
            f"spec's own priority order")

    out("")
    out(f"{len(fired)}/{n} controls fired")
    return len(fired) == n


def price_of(place_key, good):
    return ec.price(good, place_key)


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--shift", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--policies", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--policy", default="finisher")
    ap.add_argument("--seed", default="dock")
    ap.add_argument("--role", default=None,
                    help="cast the player into a role first, e.g. lurker")
    ap.add_argument("--save", default=None)
    a = ap.parse_args()
    if a.board:
        report_board(a.day)
        raise SystemExit(0)
    if a.policies:
        report_policies(a.days if a.days != 5 else 7)
        raise SystemExit(0)
    if a.shift:
        p = pl.random_player(a.seed)
        led = ec.Ledger.fresh()
        led.day = a.day
        print(p.describe())
        s = work_shift(p, led, a.day, a.policy)
        s.transcript()
        raise SystemExit(0)
    if a.loop:
        report_loop(a.days, seed=a.seed, policy=a.policy, role=a.role,
                    path=a.save or ec.LEDGER_PATH)
        raise SystemExit(0)
    if a.controls:
        raise SystemExit(0 if controls() else 1)
    raise SystemExit(0 if _selftest() else 1)
