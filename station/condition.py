#!/usr/bin/env python3
"""Hunger and fatigue, as a rhythm rather than a resource bar.

`docs/THE-STATION.md` PLY-06, ruled **LIGHT** by the owner in §9 ("I also like
the hunger/fatigue stuff too"), and the spec does something unusual with it: it
enumerates the COMPLETE effect set and says nothing outside it may be added
without a SPEC-CHANGE. That is the whole design, and it is a design about what
this must never become:

    | state   | reached by                        | effect -- and this is ALL of it |
    | fed     | a meal in the species-normal window | dialogue warmth band +1       |
    | rested  | a sleep of species-normal length    | pay-stub bonus on next shift  |
    | hungry  | no meal for ~1.5 normal intervals   | dialogue warmth band -1       |
    | tired   | no sleep for ~1.5 normal intervals  | pay-stub bonus forfeited      |
    | worse   | anything worse                      | NOTHING. No damage, no death  |
    |         |                                     | spiral, no HUD nag, no screen |
    |         |                                     | effect.                       |

**THE GATE IS A WHOLE-STATE DIFF, NOT A CHECKLIST**, and that is the spec's own
choice of harness: *"two station-days with no food and no sleep produce EXACTLY
the two declared penalties and nothing else -- asserted as a whole-state diff
against a fed-and-rested control run, so an undeclared effect fails."* A
checklist can only fail for a MISSING effect. A diff fails for an EXTRA one,
which is the failure mode a mild system actually has: it grows.

**EVERY WINDOW COMES FROM `npc/schedule.py`.** The spec says so in as many
words -- *"the species windows come from `npc/schedule.py`, not from a constant
in the condition model"* -- and the reason is the one this project keeps
relearning: a constant here is a second copy of a computed number, and the
species rhythms move. A Vorlon has NO meals in `RHYTHMS` and a pak'ma'ra has
two; a table in this file would have three for everyone.

Run:
    python3 station/condition.py --selftest
    python3 station/condition.py --diff        # the two-day starved/fed diff
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "npc"))

import schedule as sched                                         # noqa: E402


# HOW LATE IS LATE. The spec says "~1.5 species-normal intervals" for both, and
# the tilde is the spec's, so this is the one number this file chooses and it is
# chosen at the value the sentence names. It is a MULTIPLIER on an interval the
# schedule derives, never an hour count -- 1.5 human meal intervals is 7.5 h and
# 1.5 pak'ma'ra intervals is 18 h, and a single "12 hours" would be wrong for
# both. INV-660.
LATE_FACTOR = 1.5

# The four states, worst last so a max() is meaningful and a UI can order them.
FED, RESTED, HUNGRY, TIRED = "fed", "rested", "hungry", "tired"


def meal_interval_h(species: str) -> float:
    """Hours between this species' meals, from its own rhythm.

    DERIVED FROM THE MEAL LIST, not tabulated. A species with three meals at
    07:00, 12:30 and 19:00 has a mean interval of 8 h once the wrap round
    midnight is counted, which is what "species-normal interval" means -- and a
    species with ONE meal has a 24 h interval by the same arithmetic rather
    than by a special case.

    A species with NO meals returns 0.0, which `state_at` reads as "this
    species does not eat" rather than as "starving". Vorlons are the case:
    `RHYTHMS` records `meals: ()` with the note "nothing has ever shown a
    Vorlon eat", and a hunger model that made Kosh hungry would be inventing
    a fact the reference set deliberately does not carry.
    """
    r = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
    meals = sorted(float(m) % 24.0 for m in r.meals)
    if not meals:
        return 0.0
    if len(meals) == 1:
        return 24.0
    gaps = [meals[i + 1] - meals[i] for i in range(len(meals) - 1)]
    gaps.append(24.0 - meals[-1] + meals[0])
    return sum(gaps) / len(gaps)


def sleep_length_h(species: str) -> float:
    """How long this species sleeps, from its own rhythm."""
    r = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
    return float(r.sleep_hours)


def sleep_interval_h(species: str) -> float:
    """How often. A day, for everything that sleeps at all."""
    return 24.0 if sleep_length_h(species) > 0.0 else 0.0


def next_meal_hour(species: str, after_h: float) -> float:
    """The next hour this species would normally eat, at or after `after_h`."""
    r = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
    meals = sorted(float(m) % 24.0 for m in r.meals)
    if not meals:
        return -1.0
    base = after_h % 24.0
    for m in meals:
        if m >= base - 1e-9:
            return after_h + (m - base)
    return after_h + (24.0 - base + meals[0])


class Condition:
    """One person's hunger and fatigue, in absolute station hours.

    ABSOLUTE HOURS, NOT WRAPPED. `life.gd::Clock.hours_abs()` is the reading
    that does not wrap at midnight, and it is the only correct one here: a meal
    at 23:00 and a check at 01:00 is two hours, not twenty-two. The wrapped
    `hour()` is right for "how full is the Zocalo" and wrong for every duration,
    which is a distinction `Clock` already documents and this file inherits.

    `last_meal_h` and `last_sleep_h` of `None` mean "never recorded" -- a new
    character who has not eaten in this simulation is not two days hungry. They
    are seeded from the arrival, and until then the person is simply unrated.
    """

    __slots__ = ("species", "last_meal_h", "last_sleep_h", "last_sleep_len_h")

    def __init__(self, species="human", last_meal_h=None, last_sleep_h=None,
                 last_sleep_len_h=0.0):
        self.species = species
        self.last_meal_h = last_meal_h
        self.last_sleep_h = last_sleep_h
        self.last_sleep_len_h = float(last_sleep_len_h)

    # -- the two things a player does ------------------------------------
    def ate(self, hours_abs: float) -> None:
        self.last_meal_h = float(hours_abs)

    def slept(self, hours_abs: float, length_h: float) -> None:
        self.last_sleep_h = float(hours_abs)
        self.last_sleep_len_h = float(length_h)

    # -- and the two things the world reads -------------------------------
    def states(self, hours_abs: float) -> tuple:
        """Every state that applies now, sorted. Never more than two.

        A PERSON IS AT MOST ONE OF fed/hungry AND AT MOST ONE OF rested/tired,
        which is asserted rather than assumed -- the four are two independent
        axes and a state set holding both `fed` and `hungry` would be a bug in
        the windows, not a person in an interesting mood.
        """
        out = []
        mi = meal_interval_h(self.species)
        if mi > 0.0 and self.last_meal_h is not None:
            since = hours_abs - self.last_meal_h
            if since <= mi:
                out.append(FED)
            elif since > mi * LATE_FACTOR:
                out.append(HUNGRY)
        si = sleep_interval_h(self.species)
        want = sleep_length_h(self.species)
        if si > 0.0 and self.last_sleep_h is not None:
            since = hours_abs - self.last_sleep_h
            slept_enough = self.last_sleep_len_h >= want * 0.9
            if since <= si and slept_enough:
                out.append(RESTED)
            elif since > si * LATE_FACTOR or not slept_enough:
                out.append(TIRED)
        return tuple(sorted(out))

    # -- THE COMPLETE EFFECT SET. Nothing else may be added here ----------
    def effects(self, hours_abs: float) -> dict:
        """The whole of PLY-06's consequence, as data.

        TWO KEYS. NOT THREE. A new key here is a SPEC-CHANGE, and
        `_selftest`'s whole-state diff exists to make adding one fail rather
        than pass quietly -- which is the failure mode the spec's own harness
        choice is aimed at. The keys are:

          `warmth_band`  -1, 0 or +1, added to a conversation's warmth band.
                         NPCs open one topic sooner when you have eaten.
          `pay_bonus`    True or False. The shift bonus, stated in credits on
                         the stub, is forfeited when tired.
        """
        st = self.states(hours_abs)
        return {
            "warmth_band": (1 if FED in st else -1 if HUNGRY in st else 0),
            "pay_bonus": RESTED in st,
        }

    # -- persistence -------------------------------------------------------
    def save_state(self) -> dict:
        return {"species": self.species, "last_meal_h": self.last_meal_h,
                "last_sleep_h": self.last_sleep_h,
                "last_sleep_len_h": self.last_sleep_len_h}

    def load_state(self, d: dict) -> None:
        self.species = str(d.get("species", self.species))
        self.last_meal_h = d.get("last_meal_h", self.last_meal_h)
        self.last_sleep_h = d.get("last_sleep_h", self.last_sleep_h)
        self.last_sleep_len_h = float(
            d.get("last_sleep_len_h", self.last_sleep_len_h))


def run(species: str, start_h: float, days: float, feed: bool, rest: bool,
        step_h: float = 0.25) -> dict:
    """Two station-days of a life, sampled. The gate's subject and control.

    `feed`/`rest` say whether this person keeps the rhythm. Everything else --
    when a meal is due, how long a sleep is -- comes off `npc/schedule.py`.
    Returns the WHOLE observable state over the run, so the diff can be taken
    over all of it rather than over the two fields somebody remembered to check.
    """
    c = Condition(species)
    # SEEDED FED AND RESTED AT t0 IN BOTH ARMS. The starved arm has to START
    # from the same place as the control or the diff is measuring the seed.
    c.ate(start_h)
    c.slept(start_h - sleep_length_h(species), sleep_length_h(species))
    samples = []
    t = start_h
    end = start_h + days * 24.0
    while t <= end + 1e-9:
        if feed:
            nm = next_meal_hour(species, t % 24.0)
            if nm >= 0.0:
                due = t + ((nm - (t % 24.0)) % 24.0)
                if abs(due - t) < step_h / 2.0:
                    c.ate(t)
        if rest and sleep_interval_h(species) > 0.0:
            if t - (c.last_sleep_h or -1e9) >= 24.0:
                c.slept(t, sleep_length_h(species))
        samples.append({
            "t": round(t - start_h, 4),
            "states": c.states(t),
            "effects": c.effects(t),
        })
        t += step_h
    return {"species": species, "samples": samples}


def whole_state_diff(a: dict, b: dict) -> list:
    """Every way two runs differ, by sample. The gate reads this, not a count.

    IT COMPARES EFFECT KEYS TOO, not just their values. An `effects()` that
    grew a third key would produce identical values on every key the test knew
    about and a diff on the key set -- which is exactly the undeclared-effect
    case PLY-06's harness is written to catch.
    """
    out = []
    if a["species"] != b["species"]:
        out.append(("species", a["species"], b["species"]))
    n = min(len(a["samples"]), len(b["samples"]))
    if len(a["samples"]) != len(b["samples"]):
        out.append(("sample_count", len(a["samples"]), len(b["samples"])))
    for i in range(n):
        sa, sb = a["samples"][i], b["samples"][i]
        if sa["states"] != sb["states"]:
            out.append((f"t={sa['t']} states", sa["states"], sb["states"]))
        ka, kb = sorted(sa["effects"]), sorted(sb["effects"])
        if ka != kb:
            out.append((f"t={sa['t']} EFFECT KEYS", ka, kb))
            continue
        for k in ka:
            if sa["effects"][k] != sb["effects"][k]:
                out.append((f"t={sa['t']} {k}",
                            sa["effects"][k], sb["effects"][k]))
    return out


DECLARED_EFFECT_KEYS = ("pay_bonus", "warmth_band")


def _selftest() -> int:
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    # --- the windows are the schedule's, not ours -----------------------
    hm = meal_interval_h("human")
    check("a human meal interval comes off RHYTHMS", 5.0 < hm < 11.0,
          f"{hm:.2f} h from {sched.RHYTHMS['human'].meals}")
    pk = meal_interval_h("pak'ma'ra") if "pak'ma'ra" in sched.RHYTHMS else None
    two_meal = [s for s, r in sched.RHYTHMS.items() if len(r.meals) == 2]
    check("a two-meal species has a longer interval than a three-meal one",
          not two_meal or meal_interval_h(two_meal[0]) > hm,
          f"{two_meal[:1]} {meal_interval_h(two_meal[0]) if two_meal else 0:.2f} h"
          f" against human {hm:.2f} h")
    no_meal = [s for s, r in sched.RHYTHMS.items() if not r.meals]
    check("a species the show never depicts eating is not made hungry",
          bool(no_meal) and all(
              Condition(s).states(500.0) == () or
              HUNGRY not in Condition(s, last_meal_h=0.0).states(500.0)
              for s in no_meal),
          f"no-meal species: {no_meal}")

    # --- the four states are two independent axes -----------------------
    c = Condition("human", last_meal_h=0.0, last_sleep_h=0.0,
                  last_sleep_len_h=sleep_length_h("human"))
    for t in [x * 0.25 for x in range(0, 400)]:
        st = c.states(t)
        if FED in st and HUNGRY in st:
            check("fed and hungry are never both true", False, f"at t={t}")
            break
        if RESTED in st and TIRED in st:
            check("rested and tired are never both true", False, f"at t={t}")
            break
    else:
        ok += 1

    # --- THE SPEC'S OWN HARNESS: the two-day whole-state diff ------------
    # "two station-days with no food and no sleep produce EXACTLY the two
    #  declared penalties and nothing else."
    kept = run("human", 8.0, 2.0, feed=True, rest=True)
    starved = run("human", 8.0, 2.0, feed=False, rest=False)
    diff = whole_state_diff(kept, starved)
    fields = sorted({d[0].split(" ", 1)[1] for d in diff if " " in d[0]})
    check("two starved days differ from the control ONLY on the declared "
          "effects and the states behind them",
          fields and set(fields) <= {"states", "warmth_band", "pay_bonus"},
          f"differing fields: {fields}")
    check("the starved run actually reaches both penalties",
          any(d[0].endswith("warmth_band") and d[2] == -1 for d in diff)
          and any(d[0].endswith("pay_bonus") and d[2] is False for d in diff),
          f"{len(diff)} differences")
    check("the kept rhythm actually earns both bonuses",
          any(s["effects"]["warmth_band"] == 1 for s in kept["samples"])
          and any(s["effects"]["pay_bonus"] for s in kept["samples"]))

    # NEGATIVE CONTROL ON THE DIFF ITSELF. A diff that cannot see an extra
    # effect key is the whole failure this harness was chosen to prevent, so
    # the harness is made to fail before it is believed.
    grown = {"species": "human",
             "samples": [dict(s, effects=dict(s["effects"], screen_blur=0.4))
                         for s in kept["samples"]]}
    check("an UNDECLARED effect key fails the diff",
          any("EFFECT KEYS" in d[0] for d in whole_state_diff(kept, grown)),
          "the diff cannot see a new key -- it is not a whole-state diff")
    check("the diff of a run against itself is empty",
          whole_state_diff(kept, kept) == [])

    # --- and nothing worse than the four ---------------------------------
    worst = Condition("human", last_meal_h=0.0, last_sleep_h=0.0,
                      last_sleep_len_h=0.0)
    e = worst.effects(1000.0)          # 41 days with no food and no sleep
    check("41 days of nothing produces the SAME two effects and no others",
          sorted(e) == list(DECLARED_EFFECT_KEYS), f"{sorted(e)}")
    check("...and the worst values are the declared ones, not worse",
          e["warmth_band"] == -1 and e["pay_bonus"] is False, f"{e}")

    # --- AND THE TWO EFFECTS REACH THE TWO CONSUMERS ---------------------
    # THE PART THAT STOPS THIS BEING INSTANCE TWELVE. `tools/wiring.py` would
    # report `condition.py` as imported and be satisfied; this project's
    # signature defect is finished machinery whose caller does not run. So both
    # effects are pushed through the real function that consumes them, with the
    # opposite value as the control.
    import dialogue as dlg                                       # noqa: PLC0415
    import economy as eco                                        # noqa: PLC0415
    import types                                                 # noqa: PLC0415
    w = dlg.World(hour=13.0)
    lis = dlg.Listener()
    # A speaker is duck-typed here on purpose: `register` reads four attributes
    # and building a real resident would drag `populace` into a model that has
    # no business knowing about it.
    spk = types.SimpleNamespace(npc_id="r-000001", species="human",
                                role="dockworker", licensed_psi=False)
    base = dlg.register(spk, lis, w).band
    warm = dlg.register(spk, lis, w, condition=+1).band
    cold = dlg.register(spk, lis, w, condition=-1).band
    check("a fed player is met at a warmer band, a hungry one colder",
          warm <= base <= cold and (warm < base or cold > base),
          f"warm {warm} base {base} cold {cold} "
          f"(0 formal, 2 blunt -- warmer is DOWN)")
    check("the condition cannot push the band off the scale",
          dlg.register(spk, lis, w, condition=+9).band >= dlg.BAND_FORMAL
          and dlg.register(spk, lis, w, condition=-9).band <= dlg.BAND_BLUNT)

    led = eco.Ledger() if hasattr(eco, "Ledger") else None
    if led is not None and hasattr(eco, "pay"):
        class _W:
            npc_id = "player:gate"
            credits = 100

            def state(self):
                return {"npc_id": self.npc_id, "credits": self.credits}
        w1, w2 = _W(), _W()
        w2.npc_id = "player:gate2"
        eco.pay(led, w1, 50.0, why="shift", rested=False)
        eco.pay(led, w2, 50.0, why="shift", rested=True)
        got = w2.credits - w1.credits
        want = round(50.0 * eco.RESTED_BONUS)
        check("a rested shift pays the declared bonus and a tired one does not",
              got == want and got > 0, f"{got} credits against {want}")
        stub = [r for r in led.sales if r["good"] == "(rested bonus)"]
        check("...and the bonus is a NAMED line on the stub, not a bigger wage",
              len(stub) == 1 and stub[0]["who"] == "player:gate2",
              f"{len(stub)} bonus lines")

    # --- it persists ------------------------------------------------------
    src = Condition("narn", last_meal_h=12.5, last_sleep_h=3.0,
                    last_sleep_len_h=7.5)
    dst = Condition()
    dst.load_state(src.save_state())
    check("a condition round-trips through save_state/load_state",
          dst.save_state() == src.save_state(), f"{dst.save_state()}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diff", action="store_true",
                    help="the two-day starved/fed whole-state diff, printed")
    ap.add_argument("--species", default="human")
    a = ap.parse_args()
    if a.diff:
        kept = run(a.species, 8.0, 2.0, feed=True, rest=True)
        starved = run(a.species, 8.0, 2.0, feed=False, rest=False)
        d = whole_state_diff(kept, starved)
        print(f"{a.species}: meal interval {meal_interval_h(a.species):.2f} h, "
              f"sleep {sleep_length_h(a.species):.2f} h, late at x{LATE_FACTOR}")
        print(f"  {len(d)} differences over two station-days")
        seen = set()
        for what, kept_v, starved_v in d:
            key = what.split(" ", 1)[1] if " " in what else what
            if key in seen:
                continue
            seen.add(key)
            print(f"  first {key:<12} at {what.split()[0]}: "
                  f"kept {kept_v!r} -> starved {starved_v!r}")
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
