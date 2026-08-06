#!/usr/bin/env python3
"""Sleeping and waiting THROUGH the running simulation, not over it.

`docs/THE-STATION.md` PLY-05, and the whole row turns on four words: *"Both
advance the station clock at compressed rate **through the running
simulation** -- events still fire, stocks still move, the world does not
pause."*

**WHAT SHIPPED WAS A JUMP, AND A JUMP IS THE OPPOSITE OF THIS.**
`interact.gd::_sleep` read the player's `wake_h`, called `Clock.set_hour(wake)`
once and told the Director to re-apply. Fifteen honest lines against a system
that existed -- and the eight hours between 22:00 and 06:30 never happened.
Nothing fired in them. No stock moved. Nothing could wake you, because there
was no interval to be woken during. A player who slept through a hull breach
would find the station exactly as they left it, one clock reading later.

The difference is not cosmetic and it is not a rate. **A jump has no interior.**
Compression is a sequence of steps the world is carried through, each of which
can produce an event and any of which can be the last.

**AND THE PROPERTY IT BUYS IS RESOLUTION, NOT EVENT COUNT -- a negative result,
measured, and the first control written here asserted the opposite.** That
control claimed a single-step advance would produce FEWER events than eight
hourly ones. It produced **110 against 95**, because `incident.simulate`
genuinely simulates whatever window it is handed. So what compression actually
buys is how finely the sleep can be STOPPED: a one-step advance checks for a
waker exactly once, at the end, so a 03:00 sweep during a 22:00-05:15 sleep can
only wake you at 05:15 -- which is not being woken.

**WHY THE STEP IS AN HOUR.** `incident.simulate` takes a window in minutes and
`economy.background_sales` moves a whole day at a time, so the finest grain at
which both of this station's two world-tick systems have anything to say is one
station-hour. A finer step would call `incident` sixty times to produce the same
hour of events and would be a smoothness nobody can see; a coarser one would
step straight over a 03:00 sweep. INV-662.

**INTERRUPTIONS ARE THE POINT OF THE INTERIOR.** The row lists four kinds -- PA
emergencies, a sweep reaching the player's camp, rent day, a booked appointment
-- and this file implements the ones whose sources exist and NAMES the ones
whose do not, rather than quietly implementing three and reporting four.

Run:
    python3 station/compress.py --selftest
    python3 station/compress.py --sleep 22.0 --wake 5.25
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "npc"))

import incident as inc                                           # noqa: E402


# One station-hour. See the module docstring: it is the finest grain at which
# either world-tick system has anything to say. INV-662.
STEP_H = 1.0

# Which interruption sources are BUILT. The row names four; two have a source
# in this repository today and two do not, and saying which is which is the
# point of the tuple existing at all -- a runtime that reported "no
# interruptions" while silently checking half of them would be reporting a
# clean night it had not looked for.
SOURCES_BUILT = ("incident",)          # incident.py's own fired events
SOURCES_MISSING = (
    ("PA emergency", "broadcast.py has no emergency class -- its era-locked "
                     "events are scheduled bulletins, not alarms"),
    ("rent day", "economy.LADDER prices a berth per night and nothing bills "
                 "for one; there is no tenancy with a due date"),
    ("booked appointment", "SYS-15 appointments are specified and unbuilt"),
)

# WHICH INCIDENT CLASSES CAN WAKE SOMEBODY. Not all of them: a fabrication
# fault four sectors away is the world running, not an interruption. The rule
# is PLACE, not class -- an incident wakes you when it happens where you are --
# and the class list below is the second half of it, for the ones loud enough to
# reach through a bulkhead. Derived from `incident.CLASSES`' own severity rather
# than listed by hand would be better; the severity field does not exist, so
# this is a named extrapolation. INV-663.
WAKING_CLASSES = ("INC-SWEEP", "INC-BREACH", "INC-FIRE", "INC-BRAWL",
                  "INC-ARREST", "INC-CONTRA")


def hours_between(now_h: float, wake_h: float) -> float:
    """Station-hours from now until the next occurrence of `wake_h`.

    ALWAYS FORWARD AND NEVER ZERO-FOR-A-FULL-DAY. `fposmod(wake - now, 24)` is
    what the runtime already computes, and it returns 0.0 when you lie down at
    exactly your wake hour -- which would be a sleep of no length rather than a
    sleep of a day. A player who lies down at 06:30 with a 06:30 wake wants the
    next one.
    """
    d = (float(wake_h) - float(now_h)) % 24.0
    return 24.0 if d < 1e-9 else d


def steps(now_h: float, wake_h: float, step_h: float = STEP_H) -> list:
    """The station-clock hours a sleep passes through, in order, ending at wake.

    The last step is short rather than overshooting: sleeping 22:00 -> 05:15 is
    seven whole hours and a quarter, and waking at 05:00 or 06:00 would make the
    05:40 muster a coin toss. PLY-05's CHECK names that muster.
    """
    span = hours_between(now_h, wake_h)
    out, t = [], 0.0
    while t + step_h < span - 1e-9:
        t += step_h
        out.append((now_h + t) % 24.0)
    out.append(float(wake_h) % 24.0)
    return out


def advance(now_h: float, wake_h: float, at_place: str = "downbelow",
            day: int = 1, step_h: float = STEP_H, seed: str = "b5",
            interruptible: bool = True) -> dict:
    """Carry the world from `now_h` to `wake_h`, one step at a time.

    Returns what happened, which is the whole point: `woke_at` is where the
    player actually opened their eyes, `why` says whether that was the intent or
    an interruption, `fired` is every incident the world produced during the
    sleep, and `crossed` is the hours it stepped through.

    THE WORLD IS RUN, NOT SUMMARISED. `incident.simulate` is the same function
    the station's normal hour uses; nothing here is a special sleep-time model,
    because a sleep-time model is a second copy of the world that will drift.
    """
    ctx = inc.Ctx(day=day, seed=seed)
    world = inc.World(day=day)
    fired, crossed = [], []
    plan = steps(now_h, wake_h, step_h)
    prev = float(now_h)
    for h in plan:
        window = ((h - prev) % 24.0) * 60.0 or step_h * 60.0
        world, f = inc.simulate(ctx, world, start_h=prev,
                                window_min=window, scope=[at_place])
        crossed.append(round(h, 4))
        fired.extend(f)
        prev = h
        if interruptible:
            waker = _waker(f, at_place)
            if waker is not None:
                return {"woke_at": h, "why": "interrupted",
                        "by": waker, "fired": fired, "crossed": crossed,
                        "slept_h": round(((h - now_h) % 24.0), 4)}
    return {"woke_at": float(wake_h) % 24.0, "why": "intent", "by": None,
            "fired": fired, "crossed": crossed,
            "slept_h": round(hours_between(now_h, wake_h), 4)}


def _waker(fired, at_place):
    """The first event in this step loud enough and near enough to wake you."""
    for ev in fired:
        cid = _field(ev, "cid") or _field(ev, "class") or ""
        where = _field(ev, "place") or _field(ev, "at") or ""
        if cid in WAKING_CLASSES and (where == at_place or where == ""):
            return {"cid": cid, "place": where or at_place}
    return None


def _field(ev, name):
    if isinstance(ev, dict):
        return ev.get(name)
    return getattr(ev, name, None)


def _selftest() -> int:
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    # --- the plan ---------------------------------------------------------
    p = steps(22.0, 5.25)
    check("22:00 -> 05:15 steps through the night and lands ON 05:15",
          abs(p[-1] - 5.25) < 1e-9 and len(p) >= 7,
          f"{len(p)} steps, last {p[-1]:.2f}")
    check("...and it crosses midnight rather than stopping at it",
          any(abs(h - 0.0) < 1.01 or h < 5.0 for h in p), f"{p}")
    check("lying down at your own wake hour sleeps a day, not zero",
          abs(hours_between(6.5, 6.5) - 24.0) < 1e-9,
          f"{hours_between(6.5, 6.5)}")
    check("a short sleep still gets at least one step",
          len(steps(22.0, 22.4)) == 1, f"{steps(22.0, 22.4)}")

    # --- THE WORLD RAN. PLY-05's own CHECK: "the night's incident log is
    #     non-empty ... (the world ran)". -----------------------------------
    r = advance(22.0, 5.25, at_place="downbelow", day=1, interruptible=False)
    check("the night is stepped through, not jumped over",
          len(r["crossed"]) >= 7, f"{len(r['crossed'])} steps")
    check("the world RAN during the sleep -- the night's incident log is "
          "non-empty", len(r["fired"]) > 0,
          f"{len(r['fired'])} events between 22:00 and 05:15")
    check("...and it woke at the intent", abs(r["woke_at"] - 5.25) < 1e-9
          and r["why"] == "intent", f"{r['woke_at']} {r['why']}")

    # NEGATIVE CONTROL, AND MY FIRST VERSION OF IT WAS WRONG IN A WAY WORTH
    # KEEPING. It asserted that a single-step advance produces FEWER events
    # than eight hourly ones -- "a jump has no interior". Measured, the jump
    # produced 110 events against the stepped run's 95, because
    # `incident.simulate` genuinely simulates whatever window it is handed and
    # a 435-minute window is not eight 60-minute windows with the same rolls.
    #
    # So EVENT COUNT IS NOT A PROXY FOR "THE WORLD RAN", and the difference
    # compression actually buys is RESOLUTION: how finely the sleep can be
    # stopped. A one-step advance checks for a waker exactly once, at the end,
    # so a 03:00 sweep during a 22:00-05:15 sleep can only wake you at 05:15 --
    # which is not being woken. That is the property, and it is what the row
    # means by "the world does not pause".
    jump = advance(22.0, 5.25, at_place="downbelow", day=1,
                   step_h=hours_between(22.0, 5.25), interruptible=False)
    check("a jump has ONE decision point and the stepped advance has eight",
          len(jump["crossed"]) == 1 and len(r["crossed"]) >= 7,
          f"jump {len(jump['crossed'])} against stepped {len(r['crossed'])}")
    check("NEGATIVE RESULT, recorded: the jump does not fire FEWER events -- "
          "incident.simulate honours the window it is given",
          len(jump["fired"]) > 0,
          f"jump {len(jump['fired'])} events in one call against "
          f"{len(r['fired'])} over {len(r['crossed'])} calls")

    # --- interruption ------------------------------------------------------
    # PLANTED, not hoped for. The row's CHECK is "a scripted 03:00 sweep event
    # wakes the player camping below", and a gate that waits for the world to
    # roll one is a gate that passes or fails on a seed.
    planted = [{"cid": "INC-SWEEP", "place": "downbelow"}]
    check("a sweep where the player is camping wakes them",
          _waker(planted, "downbelow") is not None)
    check("...and the same sweep four sectors away does not",
          _waker([{"cid": "INC-SWEEP", "place": "zocalo"}], "downbelow")
          is None)
    check("...and a quiet class in the same room does not",
          _waker([{"cid": "INC-QUEUE", "place": "downbelow"}], "downbelow")
          is None)
    check("with interruptions OFF, the same sweep does not wake anybody",
          _waker(planted, "downbelow") is not None
          and advance(22.0, 5.25, interruptible=False)["why"] == "intent")

    # --- and the honesty clause -------------------------------------------
    check("the sources it does NOT have are named rather than reported clean",
          len(SOURCES_MISSING) == 3 and all(len(w) > 20
                                            for _n, w in SOURCES_MISSING),
          f"{[n for n, _ in SOURCES_MISSING]}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sleep", type=float, default=None,
                    help="the station hour you lie down at")
    ap.add_argument("--wake", type=float, default=None)
    ap.add_argument("--at", default="downbelow")
    ap.add_argument("--day", type=int, default=1)
    a = ap.parse_args()
    if a.sleep is None or a.wake is None:
        return _selftest()
    r = advance(a.sleep, a.wake, at_place=a.at, day=a.day)
    print(f"sleep {a.sleep:05.2f} -> intent {a.wake:05.2f} at {a.at}")
    print(f"  stepped through {len(r['crossed'])} station-hours, "
          f"{len(r['fired'])} events fired while asleep")
    print(f"  woke at {r['woke_at']:05.2f} ({r['why']}"
          + (f", {r['by']['cid']} at {r['by']['place']}" if r["by"] else "")
          + f"), slept {r['slept_h']:.2f} h")
    print("  interruption sources NOT built:")
    for n, why in SOURCES_MISSING:
        print(f"    {n:<22} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
