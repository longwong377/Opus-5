"""Who avoids whom, and how far apart they stand.

CLAUDE.md's scope: *"every major faction present, with the friction between them
visible in a corridor."* `docs/gazetteer/FACTIONS.md` §12 is fourteen sourced
rows answering exactly that -- *"what happens when two of them pass each
other"*, each with a severity and a described behaviour -- and nothing read it.

THE RULE THE WHOLE MODULE IS BUILT ON, and it is §12's own closing line:

    "Friction should be expressed 95% AS AVOIDANCE AND 5% AS CONTACT. A station
     where hostile species brawl on sight is a cheaper and less believable place
     than one where two crowds move through the same concourse and never once
     intersect. BUILD THE AVOIDANCE FIRST; the fights are set dressing on top
     of it."

So this module produces **distance**, not violence. `separation_m(a, b)` is the
whole deliverable: how much room two species leave each other, as a number a
crowd placer can use. `station/populace.py`'s `_clear()` kept every body 0.45 m
from every other body regardless of who they were -- one radius for a Narn and a
Centauri and for two humans queuing at the same stall -- so the friction was
invisible by construction. It is now a function of the pair.

WHAT IS SOURCED AND WHAT IS DESIGN
----------------------------------
§12 is explicit about the split and this module keeps it: *"Authority for the
FACT of the antagonism is given; the BEHAVIOURS are authority 5 and are the
design."* So every row below carries the authority of the antagonism, and the
metres are mine (INV-245).

THE ONE PAIR THAT IS ALREADY BUILT, and it is worth naming because it shows the
shape: **security against security.** §12 lists it at High -- *"one officer in a
two-officer patrol wears the armband and the other does not. They do not talk
much"* -- and `npc/security.py`'s `patrol()` already guarantees exactly that
split, from `costume.py`'s own armband roll. That row needs no distance; the
friction is on the sleeve.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_STATION = os.path.dirname(_HERE)
if _STATION not in sys.path:                                 # pragma: no cover
    sys.path.insert(0, _STATION)

from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(_STATION), "docs", "gazetteer",
                         "FACTIONS.md")

# ===========================================================================
# 1.  The ladder
# ===========================================================================

# §12's severities, in its own order, mapped to the two numbers a crowd needs:
# how much room the pair leaves each other, and how often the 5% fires.
#
# THE BASE SEPARATION IS THE CROWD'S OWN, NOT A NEW NUMBER. `populace._clear`
# keeps bodies 0.45 m apart -- a shoulder plus clearance -- and every distance
# here is a MULTIPLE of it, so a change to personal space moves the whole
# ladder and the ratios survive. That is hard rule 4 applied to a distance.
BASE_SEPARATION_M = 0.45

# (multiple of base, contact events per hour of exposure). The contact rates
# are the 5% of §12's rule, scaled by severity; `highest` is deliberately the
# RAREST rather than the commonest, because §12 says so in as many words about
# the Narn and the Centauri: "violence is rare and enormous when it happens --
# the surrender terms (500 executions for one Centauri death) are why restraint
# is the ambient state".
SEVERITY = {
    "highest":     (4.0, 0.02),
    "high":        (3.0, 0.08),
    "medium-high": (2.4, 0.05),
    "medium":      (1.9, 0.04),
    "low":         (1.3, 0.01),
    "ceremonial":  (6.0, 0.00),
    "episodic":    (2.2, 0.00),
    "latent":      (1.0, 0.00),
}

# §12, row for row. `a` and `b` are species keys from `schedule.ROLE_WEIGHTS`
# or role keys from `schedule.ROLES` -- the two vocabularies this project
# already has -- so a pair can be about what someone IS or what they DO.
#
# (a, b, severity, authority for the antagonism, what a player sees)
PAIRS = (
    ("narn", "centauri", "highest", "1 (S2E20)",
     "The Narn stops, turns, and does not yield the corridor. The Centauri "
     "crosses to the far side. Neither speaks. Groups reroute around each "
     "other entirely"),
    ("human", "*", "high", "4 + 1 (S2E22)",
     "Under Nightwatch: a human talking with aliens lowers his voice when an "
     "armband passes"),
    ("security", "security", "high", "2 (the still) + 1",
     "One officer in a two-officer patrol wears the armband and the other "
     "does not. They do not talk much -- ALREADY BUILT, see npc/security.py"),
    ("telepath", "*", "high", "1",
     "Conversation stops when someone with the Psi badge enters. Nobody sits "
     "at the adjacent table"),
    ("minbari", "human", "medium-high", "1",
     "Cold formality on the Minbari side; older humans stare. The "
     "Earth-Minbari War is eleven years back and everyone remembers it"),
    ("minbari", "minbari", "medium", "4",
     "Two Minbari castes that do not mix, sharing a Sanctuary schedule by "
     "rota"),
    ("pakmara", "*", "medium", "1",
     "Their eating areas are their own and other species do not sit there. "
     "Tables clear around them -- the only species with a segregated food "
     "economy"),
    ("drazi", "drazi", "episodic", "1 (S2E03)",
     "A factional split, one colour against another, on a multi-year cycle. "
     "A builder may switch it on or off for the datum"),
    ("lurker", "merchant", "medium", "4",
     "Moved on from the Zocalo. Conspicuous by clothing before anything "
     "else. Avoid identicard readers"),
    ("narn", "command", "medium", "1",
     "Earth signed a non-aggression pact with the Centauri; the Narn regard "
     "EA neutrality as complicity. Cold, not hostile"),
    ("vorlon", "*", "ceremonial", "1",
     "Kosh is almost never seen. When he moves, the corridor clears without "
     "being told to"),
    ("dockworker", "command", "latent", "1 (S1E12)",
     "Grievance boards, notices, the memory of the strike. An event rather "
     "than ambient"),
)

# The League of Non-Aligned Worlds -- §12's "League vs the great powers" row at
# Low, constant: "League delegations caucus together in the Council anteroom,
# and are visibly not being consulted." A list rather than a pair, because the
# friction is between a BLOC and three named powers.
LEAGUE = ("abbai", "brakiri", "drazi", "gaim", "grome", "hyach", "llort",
          "pakmara", "vree")
GREAT_POWERS = ("human", "minbari", "narn", "centauri", "vorlon")

# The Nightwatch row is conditional on the era, exactly as the armband is.
# FACTIONS.md 5.1: "Any armband before The Fall of Night is an error."
NIGHTWATCH_EVENT = "nightwatch_visible"


def _era_on(event: str, datum=None) -> bool:
    from npc import costume as _cos                             # noqa: PLC0415
    return _cos.era_active(event, datum or _cos.ERA_DATUM)


# ===========================================================================
# 2.  The query
# ===========================================================================

def _match(pa, pb, a, b) -> bool:
    """Does the unordered pair (a, b) match the table row (pa, pb)?

    `*` is "anyone else", and it must NOT match the same key on both sides --
    `("pakmara", "*")` is pak'ma'ra against everyone, not pak'ma'ra against
    pak'ma'ra, who share their own eating area perfectly happily.
    """
    for x, y in ((a, b), (b, a)):
        if pa == x and (pb == y or (pb == "*" and y != x)):
            return True
    return False


def pair(a: str, b: str, datum=None):
    """The strongest friction row between `a` and `b`, or None.

    Strongest rather than first, so adding a mild row later cannot mask a
    severe one by being earlier in the table.
    """
    best = None
    for pa, pb, sev, auth, why in PAIRS:
        if not _match(pa, pb, a, b):
            continue
        if pa == "human" and pb == "*" and not _era_on(NIGHTWATCH_EVENT,
                                                       datum):
            continue                      # no armband, no chill
        if best is None or SEVERITY[sev][0] > SEVERITY[best[2]][0]:
            best = (pa, pb, sev, auth, why)
    if best is None and _league_split(a, b):
        return (a, b, "low", "1",
                "League delegations caucus together and are visibly not "
                "being consulted")
    return best


def _league_split(a: str, b: str) -> bool:
    return ((a in LEAGUE and b in GREAT_POWERS)
            or (b in LEAGUE and a in GREAT_POWERS))


def separation_m(a: str, b: str, datum=None) -> float:
    """How much room these two leave each other, in metres.

    THE DELIVERABLE. `populace._clear` used one radius for everybody, so two
    crowds could stand shoulder to shoulder in the same concourse and the
    friction §12 calls the most important thing in the brief was invisible by
    construction. A Narn and a Centauri now keep 1.80 m; two humans keep 0.45.
    """
    p = pair(a, b, datum)
    if p is None:
        return BASE_SEPARATION_M
    return BASE_SEPARATION_M * SEVERITY[p[2]][0]


def contact_per_hour(a: str, b: str, datum=None) -> float:
    """The 5%. Events an hour of sustained exposure, per §12's severities."""
    p = pair(a, b, datum)
    return 0.0 if p is None else SEVERITY[p[2]][1]


def avoids(a: str, b: str, datum=None) -> bool:
    """Is there anything between these two at all?"""
    return pair(a, b, datum) is not None


def will_share_table(a: str, b: str, datum=None) -> bool:
    """Will these two sit at the same table?

    §12 gives three rows that are specifically about SEATING rather than
    passing -- the pak'ma'ra's segregated food economy, the empty chair beside
    a telepath, and the Narn who "will not enter a Centauri-run venue and is
    not served if he does". Anything at `medium` or worse is a no.
    """
    p = pair(a, b, datum)
    if p is None:
        return True
    return SEVERITY[p[2]][0] < SEVERITY["medium"][0]


def report(out=print):
    from npc import costume as _cos                             # noqa: PLC0415
    out(f"FRICTION at datum {_cos.ERA_DATUM} -- FACTIONS.md 12, "
        f"{len(PAIRS)} rows plus the League bloc")
    seen = []
    for a in sorted(sched.ROLE_WEIGHTS):
        for b in sorted(sched.ROLE_WEIGHTS):
            if a >= b:
                continue
            p = pair(a, b)
            if p is None:
                continue
            seen.append((separation_m(a, b), a, b, p))
    seen.sort(reverse=True)
    out(f"  {len(seen)} species pairs of "
        f"{len(sched.ROLE_WEIGHTS) * (len(sched.ROLE_WEIGHTS) - 1) // 2} "
        f"carry friction")
    for m, a, b, p in seen[:10]:
        out(f"  {a:9s} / {b:9s} {m:4.2f} m  {p[2]:12s} auth {p[3]:14s} "
            f"{p[4][:42]}")
    out("")
    out("  the same pair, two datums -- the Nightwatch row is era-locked")
    for dm, label in (((2, 1), "S2E01"), ((3, 5), "S3E05")):
        out(f"    {label}: human/narn {separation_m('human', 'narn', dm):.2f} m")
    out("")
    out("  seating: " + ", ".join(
        f"{a}/{b} {'shares' if will_share_table(a, b) else 'does NOT share'}"
        for a, b in (("human", "human"), ("pakmara", "human"),
                     ("narn", "centauri"), ("abbai", "brakiri"))))


# ===========================================================================
# 3.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _selftest(out=print):                                       # noqa: C901
    global PAIRS
    del _FAILED[:]
    n = 0

    n += 1
    check(all(sev in SEVERITY for _a, _b, sev, _u, _w in PAIRS),
          "every row's severity is on the ladder")
    n += 1
    check(all(len(w) > 20 for _a, _b, _s, _u, w in PAIRS),
          "every row says what a player SEES -- the behaviour is the content")
    n += 1
    check(all(_au for _a, _b, _s, _au, _w in PAIRS),
          "every row cites the authority for the antagonism, which is the "
          "half of FACTIONS.md 12 that is sourced")

    # -- the ladder is a ladder ------------------------------------------
    n += 1
    check(SEVERITY["highest"][0] > SEVERITY["high"][0]
          > SEVERITY["medium-high"][0] > SEVERITY["medium"][0]
          > SEVERITY["low"][0],
          "the separations are monotonic in severity")
    n += 1
    check(SEVERITY["highest"][1] < SEVERITY["high"][1],
          "and the CONTACT rate is not -- the Narn/Centauri row is the most "
          "severe and the RAREST, because 'violence is rare and enormous when "
          "it happens ... restraint is the ambient state'",
          f"{SEVERITY['highest'][1]} against {SEVERITY['high'][1]}")
    n += 1
    check(SEVERITY["ceremonial"][1] == 0.0,
          "a Vorlon does not get into fights")

    # -- the numbers a crowd uses ----------------------------------------
    n += 1
    check(separation_m("human", "human") == BASE_SEPARATION_M,
          "two humans keep ordinary personal space",
          f"{separation_m('human', 'human')}")
    n += 1
    nc = separation_m("narn", "centauri")
    check(nc >= 4.0 * BASE_SEPARATION_M,
          "a Narn and a Centauri keep four times it -- the highest row",
          f"{nc:.2f} m")
    n += 1
    check(separation_m("narn", "centauri")
          == separation_m("centauri", "narn"),
          "friction is symmetric")
    n += 1
    check(separation_m("pakmara", "pakmara") == BASE_SEPARATION_M,
          "pak'ma'ra sit with each other perfectly happily -- `*` must not "
          "match the same key on both sides",
          f"{separation_m('pakmara', 'pakmara')}")
    n += 1
    check(separation_m("pakmara", "human") > BASE_SEPARATION_M,
          "and everyone else leaves them room")
    n += 1
    check(separation_m("vorlon", "human") > separation_m("narn", "centauri"),
          "the corridor clears for a Vorlon further than it parts for the "
          "Narn and the Centauri -- ceremonial, not hostile",
          f"{separation_m('vorlon', 'human'):.2f} against {nc:.2f}")

    # -- the era lock ----------------------------------------------------
    n += 1
    early = separation_m("human", "narn", (2, 1))
    late = separation_m("human", "narn", (3, 5))
    check(late > early,
          "the Nightwatch chill is era-locked, exactly as the armband is -- "
          "FACTIONS.md 5.1: 'any armband before The Fall of Night is an error'",
          f"S2E01 {early:.2f} m, S3E05 {late:.2f} m")

    # -- the League ------------------------------------------------------
    n += 1
    check(avoids("abbai", "human") and not avoids("abbai", "brakiri"),
          "the League caucuses together and is not consulted by the great "
          "powers -- a bloc, not a pair")
    n += 1
    check(separation_m("abbai", "human") < separation_m("narn", "centauri"),
          "and it is the mildest row on the table, constant rather than sharp")

    # -- seating ---------------------------------------------------------
    n += 1
    check(will_share_table("human", "human")
          and not will_share_table("pakmara", "human")
          and not will_share_table("narn", "centauri"),
          "the three seating rows behave: nobody sits with the pak'ma'ra, "
          "nobody sits with both a Narn and a Centauri")
    n += 1
    # NOT against a human, and the reason is a real finding rather than a
    # weaker test: at the datum the Nightwatch row makes EVERY human/alien
    # pair `high`, so it swallows the League row whenever one side is human.
    # That is correct -- §12's Nightwatch row is "a human talking with aliens
    # lowers his voice", which does not care which alien -- and it means the
    # League's own friction is only observable between an alien bloc and a
    # non-human great power.
    check(will_share_table("abbai", "minbari"),
          "a League delegate and a Minbari will share a table -- low, "
          "constant friction is not a wall",
          f"{separation_m('abbai', 'minbari'):.2f} m")
    n += 1
    check(not will_share_table("abbai", "human"),
          "...but not with a human at the datum, because the Nightwatch row "
          "outranks the League one and applies to every alien",
          f"{separation_m('abbai', 'human'):.2f} m")
    n += 1
    check(will_share_table("abbai", "human", (2, 1)),
          "and BEFORE The Fall of Night they do share it -- which is the "
          "control that proves the row above is the Nightwatch row and not "
          "something else",
          f"{separation_m('abbai', 'human', (2, 1)):.2f} m")

    # -- coverage --------------------------------------------------------
    n += 1
    keys = sorted(sched.ROLE_WEIGHTS)
    pairs_with = sum(1 for i, a in enumerate(keys) for b in keys[i + 1:]
                     if avoids(a, b))
    total = len(keys) * (len(keys) - 1) // 2
    check(0.1 < pairs_with / total < 0.9,
          "friction covers a real fraction of the species pairs and not all "
          "of them -- a station where everyone avoids everyone is as flat as "
          "one where nobody does",
          f"{pairs_with} of {total}")

    n += 1
    txt = open(GAZETTEER).read() if os.path.exists(GAZETTEER) else ""
    check("95% as avoidance and 5% as" in txt
          and "contact" in txt,
          "the rule this module is built on is still in FACTIONS.md")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")
    keep = PAIRS
    try:
        PAIRS = tuple(p for p in PAIRS
                      if not (p[0] == "narn" and p[1] == "centauri"))
        nc2 = separation_m("narn", "centauri")
        ctl = nc2 < 4.0 * BASE_SEPARATION_M
        out(f"  drop the Narn/Centauri row -> {nc2:.2f} m (was {nc:.2f}) -- "
            f"separation gate {'FIRES' if ctl else 'DOES NOT FIRE'}")
        n += 1
        check(ctl, "the separation gate fires when a row is removed")
    finally:
        PAIRS = keep

    flat = all(SEVERITY[s][0] == SEVERITY["low"][0] for s in SEVERITY)
    out(f"  the ladder is {'FLAT -- every severity the same' if flat else 'graded: '}"
        + ("" if flat else ", ".join(
            f"{k} x{v[0]:.1f}" for k, v in sorted(
                SEVERITY.items(), key=lambda kv: -kv[1][0]))))
    out(f"  era control: human/narn {separation_m('human', 'narn', (2, 1)):.2f} m "
        f"at S2E01 against {separation_m('human', 'narn', (3, 5)):.2f} m at "
        f"the datum -- the Nightwatch row is off before The Fall of Night")

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
    if a.selftest or not a.report:
        ok = _selftest()
        if a.report:
            print()
            report()
        raise SystemExit(0 if ok else 1)
    report()
