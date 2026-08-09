#!/usr/bin/env python3
"""CAN A PLAYER SPEND A CREDIT? -- asked of the whole station, and of the
build a player actually launches.

WHAT THIS EXISTS TO END, AND IT IS A NUMBER RATHER THAN A FEELING.
`docs/MASTER-PLAN.md` A4b-3 reads *"the economy is read-only in the game ...
the bar, the market, the kiosks and the black market all exist as geometry and
not one of them will take your money"*, and after session 4q's transaction work
its row still reads **HALF** -- *"the bar's till debits and the purse survives
the process; most counters are still read-only"*. Nobody had counted "most".

Counted, at the start of session 4r:

    STATION  28 places declare a prop whose verb is `serve`
              9 of them could take a credit
    SHIPPED  the boot deck `blue_0_0` carries 16 interactables, ONE with a
             `serve` verb -- `docking_bays__prop_bay_control_booth` -- and it
             sold NOTHING.  **In the build a player launches, the number of
             counters that would take money was ZERO.**

So the honest reading of A4b-3 was not "most counters are read-only". It was
*"there is no counter in the game"*: the nine that worked were all on decks the
shipped scene does not boot into.

WHY A NEW GATE AND NOT A BIGGER OLD ONE. The 4d ruling forbids growing coverage
gates, and this is not one: it asks a question no gate here asks, and it asks it
about a *chain* rather than a part. Every existing gate scores one link --
`economy.py` scores prices and stock, `consequence.py` scores the card ladder,
`interact.py --audit` scores whether a declared prop resolves to a mesh,
`interact.py --coverage` scores whether a verb has a payload. **All four are
green on a station where nobody can buy anything**, because a chain is exactly
what a part-wise gate cannot see. This one walks the whole chain, per place:

    register functions -> consequence.sells_to(place, rung)
                       -> economy.stock_list(place)   (the lines)
                       -> economy.price(line, place)  (the money)
                       -> interact.counter_offer()    (what the sidecar BAKES)
                       -> a `serve`-verb prop declared at that place
                       -> a row for it in the SHIPPED sidecar
                       -> stock on the shelf in the ledger
                       -> economy.buy moves four numbers

and reports the place where it breaks, which is the only output that tells
anybody what to build next.

AND IT RUNS THE ENGINE HALF, because a Python chain that ends at "the sidecar
would bake this" is Python talking to itself. `--engine` launches the SHIPPED
streamed scene, walks a body through a pressure door to the counter, presses E,
and reads `station/generated/economy.json` back off disk -- then replays the
same purchase through `consequence.purchase` with `interact.verify_buy`, which
fails on a one-millicredit disagreement between the two languages.

Run: python3 station/till.py --gate        # the chain, whole station + controls
     python3 station/till.py --engine      # the shipped scene, a body, a press
     python3 station/till.py --report
     python3 station/till.py --divergence  # where the two languages disagree
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import consequence as CQ                                        # noqa: E402
import directory as dr                                          # noqa: E402
import economy as EC                                            # noqa: E402
import interact as IX                                           # noqa: E402
import player as PL                                             # noqa: E402

GEN = os.path.join(HERE, "generated")
SCENE = os.path.join(GEN, "scene")
BOOT = os.path.join(SCENE, "boot.json")
LEDGER = os.path.join(GEN, "economy.json")

# The rung a plain aboard-and-legal player holds. `consequence.CITIZEN`, read
# rather than written -- the ladder is INV-342's and a literal here would be a
# second copy of a rung number that has moved once already.
CITIZEN = CQ.CITIZEN


# ===========================================================================
# 1.  THE CHAIN, PER PLACE
# ===========================================================================
def serve_props():
    """{place -> (tokens,)} for every `serve`-verb interactable declared.

    From the register through `interact.verb_of`, so this is the same
    classification `interact.sidecar` gives the engine and not a second one.
    """
    out = {}
    for p in dr.PLACES:
        for t in (p.get("interacts") or ()):
            try:
                if IX.verb_of(t) == "serve":
                    out.setdefault(p["key"], []).append(t)
            except KeyError:
                continue
    return {k: tuple(v) for k, v in out.items()}


def chain(place_key, rung=CITIZEN, seed="b5"):
    """(spendable, where it breaks, detail) for one place.

    The links are checked in the order a player meets them, and the FIRST
    failure is the answer -- a place with no counter and no stock has one
    problem, not two, and reporting both is how a list of jobs gets double
    counted.
    """
    props = serve_props().get(place_key, ())
    if not props:
        return False, "no prop", ("nothing in this place carries a `serve` "
                                  "verb, so there is no counter to stand at")
    ok, why = CQ.sells_to(place_key, rung)
    if not ok:
        return False, "no counter", why
    lines = EC.stock_list(place_key, seed)
    if not lines:
        return False, "no lines", ("the register's functions put nothing on "
                                   "this counter")
    offer = IX.counter_offer(place_key, seed)
    if not offer.get("sells"):
        return False, "empty offer", offer.get("why", "counter_offer bakes "
                                                     "nothing for this place")
    cheap = min(offer["goods"], key=lambda g: g["cr"])
    return True, "", (f"{props[0]} sells {len(offer['goods'])} line(s), "
                      f"cheapest {cheap['good']} at {cheap['cr']:.2f} cr")


def station_ledger(rung=CITIZEN, seed="b5"):
    """Every place with a `serve` prop, and whether a credit moves there."""
    rows = []
    for k in sorted(serve_props()):
        ok, where, detail = chain(k, rung, seed)
        rows.append({"place": k, "ok": ok, "break": where, "detail": detail})
    return rows


# ===========================================================================
# 2.  THE SHIPPED BUILD -- the only build a player launches
# ===========================================================================
def boot_deck():
    """(deck name, sidecar rows, why) for the scene `godot --headless` boots.

    READ THROUGH `boot.json`'s OWN KEY rather than off a guessed path. Session
    4n lost time to `ls station/generated/starfury/` returning "no such file"
    for data that exists at `station/generated/scene/starfury/`, and the rule
    that came out of it is that a scan follows the read, never a guess.
    """
    if not os.path.exists(BOOT):
        return "", None, ("no station/generated/scene/boot.json -- run "
                          "`python3 station/boot.py --bake`")
    with open(BOOT, encoding="utf-8") as f:
        doc = json.load(f)
    ip = doc.get("interact", "")
    if not ip or not os.path.exists(ip):
        return doc.get("deck", ""), None, (
            "boot.json names no interact sidecar that exists (%r)" % ip)
    with open(ip, encoding="utf-8") as f:
        rows = json.load(f)
    return doc.get("deck", ""), rows, ""


def shipped_counters(rows, rung=CITIZEN, seed="b5"):
    """(rows with a serve verb, how many of them would take a credit).

    ASKED OF THE SIDECAR THE ENGINE READS, not of the register. That is the
    whole point of this function: `interact.gd::_verb_serve` returns "" the
    moment `it.counter` is empty, so a row baked before `verb_payload` existed
    is a counter that cannot sell however good the register looks.
    """
    serve = [r for r in rows if r.get("verb") == "serve"]
    live = []
    for r in serve:
        ctr = r.get("counter")
        baked = bool(ctr and ctr.get("sells"))
        ok, _w, _d = chain(r.get("place", ""), rung, seed)
        live.append({"group": r.get("group", ""), "place": r.get("place", ""),
                     "baked": baked, "would": ok})
    return serve, live


# ===========================================================================
# 3.  THE GATE
# ===========================================================================
def gate(out=print, seed="b5"):                                  # noqa: C901
    """The whole-station chain, the shipped deck, and four controls."""
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

    rows = station_ledger(CITIZEN, seed)
    good = [r for r in rows if r["ok"]]
    out(f"THE CHAIN -- {len(good)} of {len(rows)} places with a `serve` prop "
        f"will take a credit from a {CQ.tier_name(CITIZEN)}")
    by_break = {}
    for r in rows:
        if not r["ok"]:
            by_break.setdefault(r["break"], []).append(r["place"])
    for w in sorted(by_break):
        out(f"    {len(by_break[w]):>2d} break at `{w}`: "
            f"{', '.join(by_break[w][:6])}"
            + (" ..." if len(by_break[w]) > 6 else ""))
    out("")

    # -- 1. THE SHIPPED BUILD ------------------------------------------------
    deck, srows, why = boot_deck()
    if srows is None:
        out(f"SKIP  the shipped deck cannot be read -- {why}")
        out("      (a missing input is not a failure: rebuild and re-run)")
    else:
        serve, live = shipped_counters(srows, CITIZEN, seed)
        would = sum(1 for x in live if x["would"])
        baked = sum(1 for x in live if x["baked"])
        out(f"THE SHIPPED DECK `{deck}` -- {len(srows)} interactables, "
            f"{len(serve)} with a `serve` verb")
        for x in live:
            out(f"    {x['group']:<44s} would_sell={x['would']} "
                f"baked_in_sidecar={x['baked']}")
        check("the deck a player actually boots into has at least one counter "
              "that will take money -- the number this session found at ZERO",
              would >= 1,
              f"{would} of {len(serve)} serve props on {deck} can take a "
              f"credit")
        # AND THE SECOND HALF, WHICH IS A DIFFERENT FAILURE: the register can
        # be right and the BAKED artefact stale. `interact.gd` reads the file,
        # not the register.
        check("...and the sidecar on disk carries the counter, so the engine "
              "can see it without a rebuild",
              baked >= 1,
              f"{baked} of {len(serve)} rows carry a `counter` payload"
              + ("" if baked else " -- the committed sidecar predates "
                                 "`interact.verb_payload`; re-bake with "
                                 "`python3 station/boot.py --bake`"))

    # -- 2. THE LEDGER CAN ACTUALLY BE MOVED ---------------------------------
    led = EC.Ledger.fresh(seed)
    who = None
    for r in rows:
        if r["ok"] and led.stock.get(r["place"]):
            who = r["place"]
            break
    check("a counter exists whose shelf the ledger stands up", who is not None,
          f"{who}" if who else "no place with a chain AND stock")
    if who:
        line = EC.stock_list(who, seed)[0]
        p = PL.random_player("till")
        p.credits = 5000
        p.move_to(who)
        b_units = led.units(who, line)
        b_till = led.till.get(who, 0.0)
        unit, total = CQ.purchase(led, p, who, line, 1)
        check("...and a purchase through the card reader moves four numbers "
              "and no fifth",
              p.credits == 5000 - total
              and led.units(who, line) == b_units - 1
              and abs(led.till[who] - (b_till + total)) < 1e-6
              and led.sales[-1]["at"] == who,
              f"{who}: {line} at {unit:.2f} cr, purse 5000 -> {p.credits}, "
              f"shelf {b_units} -> {led.units(who, line)}, till "
              f"{b_till:.2f} -> {led.till[who]:.2f}")

    # -- 2b. MONEY IS NOT THE ONLY THING IN THE WAY -------------------------
    # THE FINDING THIS GATE FOUND, and it was not what it went looking for.
    # `dockwork.py` walks a Downbelow lurker from 267 to 420.50 credits over
    # fourteen days and the fare is 300, so the arc reads as closed -- and it
    # is not, because `consequence.sells_to` puts every licit counter behind
    # `COUNTER_MIN`: *"the reader will not take that card -- the identicard IS
    # the credit card (6.4)"*. Anna Allan stands at the departure desk holding
    # a hundred and twenty credits more than the ticket costs and is refused
    # for her standing. That is canon-consistent and it is a DIFFERENT story
    # from the one LAW-CRIME 7.1 tells (*"did not have the money to afford a
    # ticket back home"*), so it is asserted here rather than left to be
    # rediscovered: whichever way P2 settles it, this check moves.
    lurk = PL.player_from({"role": "lurker"}, seed="downbelow")
    lurk.credits = 420.50
    fare = EC.price("passage home", "docking_bays")
    sells_lurk, why_lurk = CQ.sells_to("docking_bays", lurk.tier)
    # AND THE MECHANISM IS NOT THE ONE I EXPECTED, WHICH IS WHY THE REASON IS
    # PRINTED RATHER THAN ASSUMED: the refusal comes back
    # *"cannot get in: needs transit (sector blue)"* -- `consequence.admits`,
    # not the card reader. A no_status person cannot reach the departure bay at
    # all, which is a stronger and more canon-shaped answer than being turned
    # away at the window, and I would have written the wrong sentence if the
    # check had asserted the reason instead of showing it.
    check("the fourteen-day lurker earns PAST the fare and is refused at the "
          "desk anyway, on STANDING and not on money -- stated, because it is "
          "a different story from the one canon tells",
          lurk.credits > fare and not sells_lurk,
          f"{lurk.credits:.2f} cr against a {fare:.2f} cr berth, rung "
          f"{CQ.tier_name(lurk.tier)}: {why_lurk}")
    rich2 = PL.random_player("citizen_fare")
    check("...and the SAME desk serves a rung the reader will take, so the "
          "refusal is the card and not the counter",
          CQ.sells_to("docking_bays", rich2.tier)[0]
          or CQ.sells_to("docking_bays", CITIZEN)[0],
          f"{CQ.tier_name(CITIZEN)}: {CQ.sells_to('docking_bays', CITIZEN)[1]}")

    # -- 3. THE SERVICES REACH THE ENGINE'S OWN DATA STRUCTURE ---------------
    # Not "economy has services" -- that is `economy.py`'s own gate. This asks
    # whether they cross the one-way bridge: `counter_offer` is the exact dict
    # `interact.sidecar` bakes and `interact.gd` reads.
    svc_places = [k for k in sorted(serve_props())
                  if EC.services_at(k)]
    crossed = [k for k in svc_places
               if any(g["good"] in EC.SERVICE_BY_NAME
                      for g in IX.counter_offer(k, seed)["goods"])]
    check("a service crosses into the baked counter payload, which is the "
          "only thing `interact.gd` can read",
          len(crossed) >= 1,
          f"{len(crossed)} of {len(svc_places)} service places bake one: "
          f"{crossed}")

    # -- 4. THE CONTROLS -- each withholds ONE input and must move the number -
    out("")
    out("CONTROLS -- each removes one input and must change the verdict")

    def count_ok(rung=CITIZEN):
        IX._OFFER_CACHE.clear()
        return sum(1 for r in station_ledger(rung, seed) if r["ok"])

    base = len(good)

    # (a) WITHHOLD THE SERVICES. This is the state this session started in and
    # it is run in the same process, so it is an A/B and not a memory.
    keep = EC.SERVICES
    EC.SERVICES = ()
    EC.SERVICE_BY_NAME = {}
    EC.SERVICE_FUNCTIONS = frozenset()
    EC.SELLING_FUNCTIONS = EC.GOODS_FUNCTIONS
    no_svc = count_ok()
    no_svc_ship = 0
    if srows is not None:
        _s, lv = shipped_counters(srows, CITIZEN, seed)
        no_svc_ship = sum(1 for x in lv if x["would"])
    EC.SERVICES = keep
    EC.SERVICE_BY_NAME = {s.name: s for s in keep}
    EC.SERVICE_FUNCTIONS = frozenset(s.function for s in keep)
    EC.SELLING_FUNCTIONS = EC.GOODS_FUNCTIONS | EC.SERVICE_FUNCTIONS
    IX._OFFER_CACHE.clear()
    check("  --no-services reproduces the state this session started in: the "
          "station loses counters and the SHIPPED DECK loses all of them",
          no_svc < base and no_svc_ship == 0,
          f"station {base} -> {no_svc} counters, shipped deck "
          f"{would if srows is not None else '?'} -> {no_svc_ship}")

    # (b) WITHHOLD THE CARD. A no-status rung is refused at every licit
    # counter (INV-342) and served at the unchecked ones.
    no_card = count_ok(CQ.NO_STATUS)
    check("  --no-card (a NO_STATUS rung) is refused at the licit counters "
          "and served only where FACTIONS 11.4 says there is no reader",
          0 < no_card < base,
          f"{no_card} of {base} counters serve "
          f"{CQ.tier_name(CQ.NO_STATUS)}")

    # (c) WITHHOLD THE MONEY.
    broke = PL.random_player("broke")
    broke.credits = 0
    broke.move_to(who or "bar_unnamed")
    led2 = EC.Ledger.fresh(seed)
    tgt = who or "bar_unnamed"
    ln2 = EC.stock_list(tgt, seed)[0]
    u0 = led2.units(tgt, ln2)
    t0 = led2.till.get(tgt, 0.0)
    try:
        CQ.purchase(led2, broke, tgt, ln2, 1)
        refused = False
    except EC.Refused:
        refused = True
    check("  --broke: an empty purse is refused AND moves no stock and no till",
          refused and led2.units(tgt, ln2) == u0
          and led2.till.get(tgt, 0.0) == t0,
          f"{tgt}/{ln2}: shelf {u0}, till {t0:.2f}, unchanged")

    # (d) WITHHOLD THE STOCK.
    led3 = EC.Ledger.fresh(seed)
    for g in list(led3.stock.get(tgt, {})):
        led3.stock[tgt][g] = 0
    rich = PL.random_player("rich")
    rich.credits = 5000
    rich.move_to(tgt)
    try:
        CQ.purchase(led3, rich, tgt, ln2, 1)
        empty_refused = False
    except EC.Refused:
        empty_refused = True
    check("  --empty: a counter with nothing on the shelf refuses a rich "
          "buyer, so the shelf is what is being read and not the price list",
          empty_refused and rich.credits == 5000)

    out("")
    out(f"{n - len(failed)}/{n} passed")
    return not failed


# ===========================================================================
# 4.  WHERE THE TWO LANGUAGES DISAGREE
# ===========================================================================
def divergence(out=print, seed="b5"):
    """What `economy.buy` moves against what `interact.gd::_verb_serve` moves.

    THE BRIDGE IS ONE-WAY AND THIS IS THE COST OF IT. There is no call from
    GDScript into `consequence.purchase`, so the engine performs the ARITHMETIC
    itself against a price and a ladder verdict Python baked -- one decision,
    two evaluations, which is the shape this repository has been burned by
    three times. `interact.verify_buy` gates four of the five things that move.
    This function names the fifth, because a gate that compares four fields
    cannot fail for the one it does not read.
    """
    rowsA = ("the purse", "debited by the price", "debited by the price", True)
    rowsB = ("the shelf", "down one", "down one", True)
    rowsC = ("the till", "up by the price", "up by the price", True)
    rowsD = ("the sales log", "one row appended", "one row appended", True)
    rowsE = ("the BAG", "untouched",
             "`_player.take(good)`, and REFUSED when full", False)
    out("WHAT MOVES, IN EACH LANGUAGE")
    out(f"  {'':<14s} {'economy.buy (python)':<34s} "
        f"{'interact.gd::_verb_serve':<44s} agree")
    for name, py, gd, ok in (rowsA, rowsB, rowsC, rowsD, rowsE):
        out(f"  {name:<14s} {py:<34s} {gd:<44s} {'yes' if ok else 'NO'}")
    out("")
    out("  `interact.verify_buy` compares till, stock, purse and sales -- the "
        "four that agree.")
    out(f"  The bag holds {PL.CARRY_CAPACITY} things, so the engine refuses "
        f"the {PL.CARRY_CAPACITY + 1}th purchase of a session and python does "
        f"not.")
    out("  THE FIX IS A DESIGN DECISION, NOT A LINE: putting every purchase "
        "in the bag")
    out(f"  fills `dockwork.py`'s fourteen-day drink loop on day "
        f"{PL.CARRY_CAPACITY - 2} and starves it. What is")
    out("  wanted is a consumable flag on `economy.Good` -- a measure of "
        "brivari is drunk,")
    out("  a berth is a ticket you keep -- and that is a vocabulary change, "
        "so it is stated")
    out("  here rather than guessed at.")


# ===========================================================================
# 5.  THE ENGINE HALF -- the shipped scene, a body, a keypress
# ===========================================================================
def godot_binary():
    """The double-precision Godot this project builds against, or None.

    BORROWED, NOT REWRITTEN. `coldstart.godot_binary()` already knows where the
    build is (`/home/user/godot-build/*/bin/godot.linuxbsd.*double*`, which is
    NOT on `PATH` -- the first draft of this function looked on `PATH`, found
    nothing and printed SKIP, which is a gate silently declining to run). One
    definition, one place to fix it.
    """
    try:
        import coldstart as CS                                # noqa: PLC0415
        p = CS.godot_binary()
        if p:
            return p
    except Exception:                                         # noqa: BLE001
        pass
    return shutil.which("godot")


def rebake_sidecar(rows, dest, hour=13.0, day=0):
    """Re-derive the sidecar for a deck from the group names it already names.

    WHY THIS IS NOT A BUILD. `interact.sidecar()` takes GROUP NAMES and nothing
    else -- no geometry, no engine -- so the payloads can be re-derived from
    the names in a committed sidecar in about a second, without rebuilding a
    single triangle. That matters twice over: the committed
    `blue_0_0_interact.json` predates `interact.verb_payload` and carries no
    `counter` at all, and rewriting the shared artefact in place while other
    agents are running is exactly the artefact collision CLAUDE.md records from
    session 3w. So this writes a COPY and `--interact=` points the engine at it.

    The centres and half-extents are copied through from the committed rows,
    because those are the only fields that DO come off geometry.
    """
    names = [r["group"] for r in rows if r.get("group")]
    fresh = IX.sidecar(names, hour=hour, day=day)
    geo = {r["group"]: r for r in rows}
    for r in fresh:
        src = geo.get(r["group"], {})
        for k in ("centre", "half", "tris", "yaw"):
            if k in src:
                r[k] = src[k]
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(fresh, f, indent=1)
    return fresh


def _ledger_snapshot(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _seed_ledger(path, place_key, lurker=False, seed="b5"):
    """A ledger the engine can be pointed at, with one purse in it.

    THE SUBJECT AND THE CONTROL ARE THE SAME LEDGER WITH ONE FIELD CHANGED --
    who is holding the card. `lurker=True` reproduces the shipped
    `player:downbelow` purse (no_status, 420.50 cr from fourteen days on the
    dock); `lurker=False` is a player the register's own machinery produced who
    holds a rung a licit counter will read. Everything else -- stock, tills,
    prices, the day -- is identical, so the difference between the two runs is
    the card and nothing else.

    The world's OWN half is `Ledger.fresh()` rather than a copy of the shared
    file, because that file was written before `SERVICES` existed and carries no
    `docking_bays` row at all: a gate reading a committed artefact must be able
    to rebuild it.
    """
    led = EC.Ledger.fresh(seed)
    live = _ledger_snapshot(LEDGER) or {}
    led.day = int(live.get("day", 0))
    led.wages = dict(live.get("wages", {}))
    if lurker:
        st = None
        for k, v in sorted((live.get("purses") or {}).items()):
            if k.startswith("player:"):
                st = dict(v)
                break
        if st is None:
            p = PL.player_from({"role": "lurker"}, seed="downbelow",
                               at=place_key)
            st = p.state()
        st["at"] = place_key
        led.purses[st["npc_id"]] = st
    else:
        p = PL.random_player("till_citizen", at=place_key)
        p.status = PL.ADMITTED
        # ENOUGH TO BUY THE DEAREST THING ON THE COUNTER AND NOTHING SPARE
        # BEYOND IT: a purse that could buy everything twice would not tell a
        # refusal from a sale.
        dearest = max((EC.price(g, place_key, seed)
                       for g in EC.stock_list(place_key, seed)), default=1.0)
        p.credits = int(round(dearest + 1.0))
        led.purses[p.npc_id] = p.state()
    led.save(path)
    return path


def engine_gate(verbose=False, timeout=1500, keep=None,          # noqa: C901
                lurker=False, from_head=False):
    """Drive the SHIPPED streamed scene at a counter and read the ledger back.

    THE DRIVER ALREADY EXISTS AND IS NOT MINE. `walk.gd --visit
    --use-group=<group>` walks a body along the ring to the cell's pressure
    door, lines up on the aperture, walks through it to a named interactable
    and PRESSES it -- then walks away until the cell is freed, comes back and
    does it again. `station/walkable.py` uses it for the streaming gate. So
    this function adds no engine code at all: it points that driver at the
    counter, and reads `station/generated/economy.json` before and after.

    A PRESS IS NOT A SALE and the gate says which it got. `walk.gd` reports
    `v1_presses`; the ledger reports whether money moved. Those are different
    claims and conflating them is how a keypress that does nothing passes for
    a shop.
    """
    godot = godot_binary()
    if godot is None:
        print("TILL SKIP -- no Godot binary on PATH")
        return True
    deck, rows, why = boot_deck()
    if rows is None:
        print(f"TILL SKIP -- {why}")
        return True
    # ABSOLUTE, ALWAYS. `godot --path godot` runs with the project directory as
    # its cwd, so a relative `--interact=scratchpad/...` resolved to nothing and
    # the run died on *"is not a JSON array"* -- a path error wearing the
    # costume of a data error.
    work = os.path.abspath(keep or tempfile.mkdtemp(prefix="till-"))
    os.makedirs(work, exist_ok=True)
    side = os.path.join(work, "interact.json")
    fresh = rebake_sidecar(rows, side)
    counters = [r for r in fresh
                if r.get("verb") == "serve"
                and (r.get("counter") or {}).get("sells")]
    if not counters:
        print(f"TILL FAIL -- the shipped deck {deck} bakes no counter that "
              f"sells; there is nothing on it to buy from")
        return False
    tgt = counters[0]
    goods = tgt["counter"]["goods"]
    cheap = min(goods, key=lambda g: g["cr"])
    print(f"TILL THE SHIPPED SCENE TAKES MONEY -- deck {deck}, "
          f"{tgt['group']}")
    print(f"     sells {len(goods)} line(s), cheapest {cheap['good']} at "
          f"{cheap['cr']:.2f} cr")

    # A LEDGER OF ITS OWN, AND TWO REASONS FOR IT.
    #
    # (1) THE SHARED ONE IS NOT MINE TO STOMP. `station/generated/economy.json`
    # is the container's live world state, `coldstart.purse_ledger` reads it as
    # G4's third input, and CLAUDE.md's own session-3w lesson is that two
    # agents with disjoint SOURCE files are not disjoint in their ARTEFACTS.
    # `interact.gd::ledger_path()` honours `--ledger=`, so the run gets a copy.
    #
    # (2) THE SHIPPED PURSE CANNOT BUY A BERTH, AND THAT IS A FINDING RATHER
    # THAN A NUISANCE. The ledger in this container was seeded by
    # `dockwork.py --loop --role lurker`, so the player is `player:downbelow`,
    # **no_status**, holding **420.50 cr** -- past the 300 cr fare and refused
    # anyway, because `consequence.sells_to` puts every licit counter behind
    # `COUNTER_MIN` (*"the reader will not take that card -- the identicard IS
    # the credit card (6.4)"*). Money is not the only thing standing between
    # the underclass and the door. The gate needs a purse that CAN buy, so it
    # rebuilds one from `player.py` at the rung the register expects, and
    # `--lurker` runs the same scene with the shipped purse to show the refusal.
    before = os.path.join(work, "economy.before.json")
    _seed_ledger(before, tgt["place"], lurker=lurker)
    b = _ledger_snapshot(before)
    who = next((k for k in sorted(b.get("purses", {}))
                if k.startswith("player:")), None)
    if who is None:
        print("TILL SKIP -- the ledger holds no `player:` purse")
        return True
    b_cr = float(b["purses"][who].get("credits", 0.0))
    b_till = float(b.get("till", {}).get(tgt["place"], 0.0))
    b_units = int(b.get("stock", {}).get(tgt["place"], {})
                  .get(cheap["good"], 0))
    b_sales = len(b.get("sales", []))
    live_led = os.path.join(work, "economy.json")
    shutil.copy(before, live_led)
    print(f"     before: purse {who} ({b['purses'][who].get('tier_name')}) "
          f"{b_cr:.2f} cr, till {b_till:.2f}, shelf {b_units} x "
          f"{cheap['good']}, {b_sales} sales")

    ok = _drive(godot, deck, side, tgt["group"], work, verbose, timeout,
                live_led, from_head)
    a = _ledger_snapshot(live_led)
    a_cr = float(a["purses"][who].get("credits", 0.0))
    a_till = float(a.get("till", {}).get(tgt["place"], 0.0))
    a_units = int(a.get("stock", {}).get(tgt["place"], {})
                  .get(cheap["good"], 0))
    a_sales = len(a.get("sales", []))
    print(f"     after : purse {a_cr:.2f} cr, till {a_till:.2f}, "
          f"shelf {a_units}, {a_sales} sales")

    moved = (a_sales > b_sales and a_cr < b_cr and a_till > b_till
             and a_units < b_units)
    print(f"     TILL money=%s (purse %+0.2f, till %+0.2f, shelf %+d, "
          f"sales %+d)" % ("MOVED" if moved else "DID NOT MOVE",
                           a_cr - b_cr, a_till - b_till,
                           a_units - b_units, a_sales - b_sales))
    if moved:
        after = os.path.join(work, "economy.after.json")
        shutil.copy(live_led, after)
        good_replay, note = IX.verify_buy(before, after, who, tgt["place"],
                                          cheap["good"], 1)
        print(f"     CROSS-LANGUAGE {'agree' if good_replay else 'DISAGREE'} "
              f"-- {note}")
        ok = ok and good_replay
    if lurker:
        # THE CONTROL INVERTS THE VERDICT. A no_status card must be refused at
        # a licit counter, so `money=DID NOT MOVE` is the PASS here.
        print(f"TILL gate={'PASS' if (ok and not moved) else 'FAIL'} "
              f"(--lurker: a refusal is the expected result)")
        return bool(ok and not moved)
    print(f"TILL gate={'PASS' if (ok and moved) else 'FAIL'}")
    return bool(ok and moved)


def project_dir(work, from_head=False):
    """Which `godot/` the run uses, and why it is sometimes not this one.

    CLAUDE.md's session-4e lesson, met head-on: *"before believing a render
    taken while an agent is running, check whether it imports anything that
    agent owns."* The first engine run of this gate died at the cell holding
    the counter with

        SCRIPT ERROR: Parse Error: Closing ")" doesn't match the opening "["
        ERROR: Failed to load script "res://scripts/enforcement.gd"

    -- an **untracked** file another agent had written 90 seconds earlier.
    Nothing was wrong with the build; the run was taken against a file
    mid-edit. `--from-head` exports `godot/` at HEAD into the working directory
    and runs that, which is the cheap form of the `git worktree` fix: no engine
    input of mine is in `godot/` at all, because the sidecar, the cells and the
    ledger are all passed as absolute paths.
    """
    if not from_head:
        return os.path.join(ROOT, "godot")
    dest = os.path.join(work, "head")
    if not os.path.exists(os.path.join(dest, "godot", "project.godot")):
        os.makedirs(dest, exist_ok=True)
        tar = subprocess.Popen(["git", "archive", "HEAD", "godot"],
                               cwd=ROOT, stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", dest], stdin=tar.stdout, check=True)
        tar.wait()
    return os.path.join(dest, "godot")


def _drive(godot, deck, side, group, work, verbose, timeout, ledger,
           from_head=False):
    """One `--visit` run of the shipped streamed build at one interactable."""
    d = os.path.join(SCENE, "deck")
    cells = os.path.join(d, f"cells_{deck}", f"{deck}_cells.json")
    cmd = [godot, "--headless", "--path", project_dir(work, from_head),
           "res://scenes/walk.tscn", "--", f"--cells={cells}",
           "--stream-test", "--visit", "--gravity-mode=drum", "--settle=120",
           f"--interact={side}", f"--use-group={group}",
           f"--ledger={ledger}"]
    print("     $ " + " ".join(cmd[-7:]))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"     the run timed out after {timeout} s")
        return False
    out = r.stdout + r.stderr
    with open(os.path.join(work, "engine.log"), "w") as f:
        f.write(out)
    if verbose:
        print(out)
    for line in out.splitlines():
        if line.startswith("USE ") or line.startswith("STREAMTEST ") \
                or "bought" in line or "REFUSED" in line \
                or line.startswith("interact: purse"):
            print("     | " + line[:200])
    return "USE " in out


# ===========================================================================
# 6.  Reporting
# ===========================================================================
def report(out=print, seed="b5"):
    rows = station_ledger(CITIZEN, seed)
    out("WHERE A CREDIT CHANGES HANDS -- every place with a `serve` prop")
    out("")
    for r in rows:
        mark = "  " if r["ok"] else "XX"
        out(f" {mark} {r['place']:<22s} {r['detail'][:88]}")
    good = sum(1 for r in rows if r["ok"])
    out("")
    out(f"  {good} of {len(rows)} take money from a "
        f"{CQ.tier_name(CITIZEN)}")
    out("")
    out("SERVICES -- what a station sells that is not a crate")
    for s in EC.SERVICES:
        places = [p["key"] for p in dr.PLACES if s.function in p["functions"]]
        out(f"  {s.name:<24s} {EC.service_price(s.name, places[0]):>7.2f} cr "
            f"/{s.unit:<6s} <- LADDER `{s.ladder or 'squat'}` "
            f"@ {len(places)} place(s) declaring `{s.function}`")
        out(f"      {s.note}")
    free, hulls, seats = EC.outbound_berths(0)
    out("")
    out(f"  passage home is limited by real hulls: day 0 sails {hulls} "
        f"passenger ships with {seats} seats, {free} free")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--engine", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--divergence", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--keep", default=None,
                    help="working directory for the engine run's artefacts")
    ap.add_argument("--from-head", action="store_true",
                    help="run the engine against `git archive HEAD godot`, so a\n                         file another agent is mid-write on cannot poison it")
    ap.add_argument("--lurker", action="store_true",
                    help="engine control: run the same scene with the shipped "
                         "no_status purse, which must be REFUSED")
    a = ap.parse_args(argv)
    if a.report:
        report()
        return 0
    if a.divergence:
        divergence()
        return 0
    if a.engine:
        return 0 if engine_gate(a.verbose, keep=a.keep,
                                lurker=a.lurker,
                                from_head=a.from_head) else 1
    good = gate()
    return 0 if good else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
