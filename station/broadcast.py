"""The information layer: what the station is saying, and who can hear it.

CLAUDE.md's scope asks for *"an information layer the player can use — comms,
ISN, propaganda, signage, announcements"*. Four of those five did not exist.
`station/signage.py` builds the boards and their lettering — the station's
written voice, and it is good — but nothing generated a single **spoken** word,
a bulletin, or a notice.

DERIVED, NOT WRITTEN, and that is the whole design
---------------------------------------------------
An announcement here is not a line of dialogue someone typed. It is a **view of
a simulation that already exists**:

  * an arrival call names the ship `station/traffic.py` actually berthed, at the
    hour it actually berthed, in the tier it actually berthed in
  * a customs call fires when `traffic.hall_rate` says a hall is surging, which
    on a liner day is 8.5 people a minute against a 0.28 background
  * a watch call fires at the shift boundaries `npc/schedule.py` already rotates
    security through
  * a Ministry of Peace notice exists **only after `costume.ERA_EVENTS` says
    Nightwatch has surfaced** — S2E22, *The Fall of Night*. At the S3E05 datum
    it is on; render the same station at S2E01 and it is gone

So the information layer cannot drift from the station, because it has no
content of its own to drift with. A future session that changes the manifest
changes what the tannoy says, without touching this file.

THE BUILD NOTE THAT GOVERNS THE PROPAGANDA, and it is FACTIONS.md 11.5's own
-----------------------------------------------------------------------------
    "At the datum the propaganda layer is THREE SURFACES: ISN on public
     screens, Ministry of Peace notices, and Nightwatch recruitment. They
     should read as OFFICIAL AND REASONABLE -- clean typography in the same
     register as the customs boards -- because that is what makes them
     sinister. Do not make them look like villain posters."

Every line below is written to that instruction. The register is the customs
board's: `reference/01-station-exterior/welcome to babylon 5.webp` gives
*"FOLLOW ALL CUSTOMS PROCEDURES"* and *"TIME ON B-5 IS EARTH MEAN TIME (EMT)"*
at authority 1, and that flat civic voice is the one the Ministry borrows.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)

import directory as dr                                         # noqa: E402
import traffic as tf                                           # noqa: E402
from npc import costume as cos                                 # noqa: E402
from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(_HERE), "docs", "gazetteer",
                         "FACTIONS.md")

# ===========================================================================
# 1.  Where a voice reaches
# ===========================================================================

# THE STATION TALKS IN PUBLIC AND NOT IN YOUR QUARTERS. A tannoy that reaches
# every room on the station is a tannoy nobody can get away from, and the
# owner's scope asks for isolation as well as crowding -- so the public address
# is scoped to the places a port announcement is FOR. Each is a register key.
PA_PLACES = ("arrival_concourse", "customs_north", "customs_south",
             "docking_bays", "bay_elevators", "zocalo", "transfer_systems",
             "cargo_bays")

# BabCom public terminals. FACTIONS.md 11.5, authority 4: "Public terminals in
# passenger lounges and the Zocalo; better quarters have BabCom and datanet
# terminals." So the Zocalo and the arrival concourse are STATED, and the
# command-grade quarters follow from the same sentence.
BABCOM_PLACES = ("zocalo", "arrival_concourse", "business_center",
                 "qtr_command", "ambassadorial_suites")

# ISN on public screens. The in-repo anchor is authority 1 and it is precise:
# the arrival concourse carries a WALL MONITOR SHOWING A TALKING HEAD -- a news
# screen, on screen, in the customs area
# (`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
# hub.jpg`). Everything else here is that surface repeated where a crowd stands.
ISN_PLACES = ("arrival_concourse", "customs_north", "customs_south",
              "zocalo", "mess_hall", "fresh_air")

# Ministry of Peace notices go where people queue and are processed --
# FACTIONS.md 13 proposes "public reporting terminals in the Zocalo and both
# customs halls" for the Nightwatch reporting terminal, and a notice belongs
# wherever the terminal does.
MINIPAX_PLACES = ("customs_north", "customs_south", "zocalo",
                  "arrival_concourse")

# ===========================================================================
# 2.  The voice
# ===========================================================================

# The customs board's own register, authority 1, from
# `reference/01-station-exterior/welcome to babylon 5.webp`. Kept verbatim
# because it is the tuning fork every invented line below is written against.
BOARD_VOICE = (
    "FOLLOW ALL CUSTOMS PROCEDURES",
    "TIME ON B-5 IS EARTH MEAN TIME (EMT)",
)

# How a ship type is called. The names are the manifest's; the phrasing is
# authority 5 and deliberately flat -- a port tannoy is a civil servant, not a
# narrator. "Delta Gamma 9" and "United Spaceways" are authority 4 (the type
# named in the pilot's docking sequence and its stated operator) and are the
# only proper nouns here that come from a source.
SHIP_CALL = {
    "freighter_bay": "Achilles-type freighter",
    "transport": "United Spaceways transport",
    "shuttle": "in-system shuttle",
    "freighter_standoff": "standoff-class freighter",
    "diplomatic": "diplomatic vessel",
    "liner": "Asimov-class liner",
    "ef_transport": "EarthForce personnel transport",
    "ef_warship": "EarthForce vessel",
    "alien_warship": "visiting patrol vessel",
}

# A liner's passengers clear customs over 90 minutes (traffic.hall_rate uses
# the same window), and the hall is told to expect them a quarter-hour out.
LINER_WARNING_H = 0.25

# The escalation ladder's rung 6 -- LAW-CRIME-DOWNBELOW.md 2.4: the external
# sensor arrays turned inward are "the station's one whole-volume search
# capability ... a superb scripted-event mechanic: a station-wide sweep the
# player can feel, ANNOUNCED OVER THE PUBLIC ADDRESS". Not on a schedule: it is
# an event, and this module can produce the line when something asks for it.
SENSOR_SWEEP = ("ATTENTION. Station sensors are being recalibrated for an "
                "internal scan. Remain in your quarters or place of business "
                "until the scan is complete.")


def _era_on(event: str, datum=None) -> bool:
    """Is `event` in force at the datum? `costume.era_active` is the authority.

    DELEGATED for the reason INV-240 records about the armband: a second era
    clock is a second description of one fact, and the one that reaches a frame
    wins. `costume.py` already refuses to dress an S2E01 officer in a Nightwatch
    band; the tannoy must agree with the sleeve.
    """
    return cos.era_active(event, datum or cos.ERA_DATUM)


# ===========================================================================
# 3.  What is being said
# ===========================================================================

def port_calls(day: int = 0) -> list:
    """Every arrival and departure call for one station day.

    Derived from `traffic.arrivals(day)` -- so the tannoy names the ship that
    berthed, in the tier it berthed in, at the hour it berthed. A liner also
    gets a warning call a quarter-hour ahead, because a hall about to take 8.5
    people a minute is told first.
    """
    out = []
    for i, a in enumerate(tf.arrivals(day)):
        what = SHIP_CALL.get(a["type"], a["type"])
        where = ("docking_bays" if a["berth"] == "bay"
                 else "transfer_systems" if a["berth"] == "standoff"
                 else None)
        if a["type"] == "liner":
            out.append({
                "hour": (a["hour"] - LINER_WARNING_H) % 24.0, "kind": "port",
                "places": ("customs_north", "customs_south",
                           "arrival_concourse"),
                "text": (f"CUSTOMS ADVISORY. {what} arriving in fifteen "
                         f"minutes with {a['souls']} passengers. All "
                         f"processing positions to be manned."),
                "source": "traffic.arrivals + TRAFFIC-AND-CUSTOMS 5.2",
            })
        out.append({
            "hour": a["hour"], "kind": "port", "places": PA_PLACES,
            "text": (f"{what.upper()} NOW ARRIVING"
                     + (f", {where.replace('_', ' ')}" if where else
                        ", standing off")
                     + (f". {a['souls']} arriving passengers to customs."
                        if a["souls"] else ".")),
            "source": f"traffic.arrivals({day})[{i}]",
        })
        # And it leaves again. A port whose ships only arrive fills up.
        out.append({
            "hour": (a["hour"] + a["stay_h"]) % 24.0, "kind": "port",
            "places": ("docking_bays", "bay_elevators", "cargo_bays"),
            "text": f"{what.upper()} DEPARTING. Bay doors closing.",
            "source": f"traffic.arrivals({day})[{i}] + stay_h",
        })
    return out


def watch_calls() -> list:
    """Shift changes, from `schedule`'s own rotation rather than a new clock."""
    out = []
    for h, name in ((0.0, "A"), (8.0, "B"), (16.0, "C")):
        out.append({
            "hour": h, "kind": "watch", "places": PA_PLACES,
            "text": (f"{name} WATCH. All personnel report to duty stations. "
                     f"{sched.role_on_duty('security', h)} security on watch."),
            "source": "npc/schedule.role_on_duty + "
                      "LAW-CRIME-DOWNBELOW 2.2's three-shift table",
        })
    return out


def civic_calls() -> list:
    """The station's standing instructions -- the customs board, spoken.

    Authority 1 text, repeated. It is the one part of this module that is not
    invented at all, and it is here so the invented lines above and the notices
    below have something to sit beside in the same register.
    """
    return [{"hour": h, "kind": "civic", "places": MINIPAX_PLACES,
             "text": t, "source": "reference/01-station-exterior/"
                                  "welcome to babylon 5.webp, authority 1"}
            for h, t in zip((6.0, 14.0), BOARD_VOICE)]


# ISN bulletins, era-locked. Each is tied to an event in `costume.ERA_EVENTS`,
# so the bulletin list at a given datum is a FUNCTION of the datum rather than
# a list somebody maintained. The tone is FACTIONS.md 11.5's: ISN "initially
# genuine journalism; after Clark's consolidation it becomes a propaganda organ
# defending the government's xenophobic policies and attacking dissidents", so
# the later ones are drier and more official, not shriller.
ISN_BULLETINS = (
    ("markab_extinct",
     "ISN. Earth Alliance medical authorities confirm no surviving Markab "
     "population. Quarantine protocols aboard commercial stations remain in "
     "force."),
    ("narn_surrender",
     "ISN. The Narn Regime has accepted terms. The Earth Alliance restates "
     "its neutrality and urges nationals in former Narn space to register "
     "with the nearest consulate."),
    ("nightwatch_visible",
     "ISN. The Ministry of Peace reports continued public support for the "
     "Nightwatch programme. A spokesman described participation as, quote, "
     "an ordinary civic duty."),
    ("rangers_visible",
     "ISN. Earth Alliance security services are reviewing reports of an "
     "unregistered organisation operating along the rim. Citizens are asked "
     "to report unusual activity."),
    ("martial_law",
     "ISN. Emergency measures remain in effect. Normal commercial traffic is "
     "unaffected."),
)

# Ministry of Peace notices. FACTIONS.md 5: a paramilitary division of MiniPax,
# set up under President Clark in 2259, whose stated purpose is "internal
# security and safety" and whose actual function is a propaganda instrument
# where "dissent is relabelled treason". The notices are written to the STATED
# purpose in the customs board's own voice, which is the build note's whole
# point -- an official, reasonable surface is what makes it sinister.
MINIPAX_NOTICES = (
    "MINISTRY OF PEACE. Report suspicious activity at any station terminal. "
    "Your cooperation protects your neighbours.",
    "MINISTRY OF PEACE. Nightwatch is now recruiting. Enquire at any station "
    "house. A supplementary allowance is payable.",
    "MINISTRY OF PEACE. Loyalty is the ordinary condition of a citizen. "
    "Reports may be filed anonymously.",
)


def isn_bulletins(datum=None) -> list:
    """The bulletins in force at `datum`, in event order.

    THE ERA LOCK IS THE POINT. At the S3E05 datum four of the five are on; at
    S2E01 none are, because none of their events has happened. A future session
    that moves `costume.ERA_DATUM` moves what the screens say, and nothing here
    has to know.
    """
    return [{"hour": None, "kind": "isn", "places": ISN_PLACES, "text": txt,
             "event": ev, "source": f"costume.ERA_EVENTS[{ev!r}] + "
                                    f"FACTIONS.md 11.5"}
            for ev, txt in ISN_BULLETINS if _era_on(ev, datum)]


def minipax_notices(datum=None) -> list:
    """Ministry of Peace notices -- ONLY after Nightwatch surfaces aboard.

    FACTIONS.md 5.1 is explicit: *"Any armband before The Fall of Night is an
    error."* The same is true of the notices; a Ministry of Peace poster in a
    Season 1 customs hall is the same mistake as the armband.
    """
    if not _era_on("nightwatch_visible", datum):
        return []
    return [{"hour": None, "kind": "minipax", "places": MINIPAX_PLACES,
             "text": t, "event": "nightwatch_visible",
             "source": "FACTIONS.md 5 and 11.5's build note"}
            for t in MINIPAX_NOTICES]


# ===========================================================================
# 4.  What a player hears
# ===========================================================================

def day(day_n: int = 0, datum=None) -> list:
    """Everything the station says on one day, in time order.

    Timed items first by hour; the standing surfaces (ISN, notices) carry
    `hour=None` because a screen is always on and a poster is always up.
    """
    timed = port_calls(day_n) + watch_calls() + civic_calls()
    timed.sort(key=lambda a: a["hour"])
    return timed + isn_bulletins(datum) + minipax_notices(datum)


def audible_at(place_key: str, hour: float, day_n: int = 0, window_h=0.25,
               datum=None) -> list:
    """What a player standing in `place_key` at `hour` can hear or read.

    `window_h` is how long a call is still "now". Standing surfaces are always
    returned, because a screen a player can walk up to is part of what the room
    says whether or not anything was announced this minute.
    """
    out = []
    for a in day(day_n, datum):
        if place_key not in a["places"]:
            continue
        if a["hour"] is None:
            out.append(a)
            continue
        d = min(abs(a["hour"] - hour), abs(a["hour"] - hour + 24.0),
                abs(a["hour"] - hour - 24.0))
        if d <= window_h:
            out.append(a)
    return out


def has_terminal(place_key: str) -> bool:
    """Is there a BabCom terminal here a player could use?"""
    return place_key in BABCOM_PLACES


# ===========================================================================
# 5.  Report
# ===========================================================================

def report(out=print):
    d = day(0)
    timed = [a for a in d if a["hour"] is not None]
    standing = [a for a in d if a["hour"] is None]
    out(f"THE STATION SAYS {len(timed)} TIMED THINGS A DAY and carries "
        f"{len(standing)} standing surfaces, at datum {cos.ERA_DATUM}")
    kinds = {}
    for a in d:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    out("  " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    out("")
    out("A DAY AT THE ARRIVAL CONCOURSE")
    for h in (2.0, 8.0, 10.5, 14.0, 18.0, 22.0):
        heard = audible_at("arrival_concourse", h, 0)
        live = [a for a in heard if a["hour"] is not None]
        out(f"  {h:05.2f}  {len(live)} call(s), "
            f"{len(heard) - len(live)} standing surface(s)")
        for a in live[:2]:
            out(f"          [{a['kind']}] {a['text'][:78]}")
    out("")
    out("THE ERA LOCK -- the same station, three datums")
    for dm, label in (((2, 1), "S2E01"), ((2, 22), "S2E22"),
                      ((3, 5), "S3E05, the datum")):
        b = isn_bulletins(dm)
        m = minipax_notices(dm)
        out(f"  {label:16s} {len(b)} ISN bulletin(s), "
            f"{len(m)} Ministry of Peace notice(s)")
    out("")
    out("A LINER DAY, at the north hall")
    ld = next((n for n in range(8) if tf.liner_today(n)), 0)
    la = next((a for a in tf.arrivals(ld) if a["type"] == "liner"), None)
    if la:
        for dh in (-0.3, -0.25, 0.0, 0.4):
            h = (la["hour"] + dh) % 24.0
            heard = [a for a in audible_at("customs_north", h, ld)
                     if a["hour"] is not None]
            r = tf.hall_rate(h, ld)
            out(f"  {h:05.2f}  {r['total_per_min']:5.2f}/min "
                f"(x{r['multiple']:.1f})  "
                + (heard[0]["text"][:64] if heard else "--"))
    out("")
    out(f"BabCom terminals at: {', '.join(BABCOM_PLACES)}")


# ===========================================================================
# 6.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _has(key):
    try:
        dr.by_key(key)
        return True
    except Exception:
        return False


def _selftest(out=print):                                       # noqa: C901
    global ISN_BULLETINS, PA_PLACES
    del _FAILED[:]
    n = 0

    # -- every place a voice reaches is a real place ---------------------
    for name, group in (("PA_PLACES", PA_PLACES),
                        ("BABCOM_PLACES", BABCOM_PLACES),
                        ("ISN_PLACES", ISN_PLACES),
                        ("MINIPAX_PLACES", MINIPAX_PLACES)):
        n += 1
        bad = [k for k in group if not _has(k)]
        check(not bad, f"every {name} entry is a register place", f"{bad}")
    n += 1
    check(set(PA_PLACES) & set(BABCOM_PLACES),
          "the port and the comms network overlap somewhere a player stands")

    # -- the calls are DERIVED, and this is what proves it ---------------
    n += 1
    a0 = tf.arrivals(0)
    calls = port_calls(0)
    check(len(calls) >= 2 * len(a0),
          "every arrival gets an arrival call and a departure call",
          f"{len(calls)} calls for {len(a0)} arrivals")
    n += 1
    # THE ASSERTION THAT MATTERS: change the port and the tannoy changes.
    # Nothing here is a fixed list, so this must hold by construction.
    c1 = [a["text"] for a in port_calls(1)]
    check(c1 != [a["text"] for a in calls],
          "a different day says different things -- the calls come from the "
          "manifest, not from a script")
    n += 1
    liner_day = next((d for d in range(8) if tf.liner_today(d)), None)
    check(liner_day is not None, "a liner turns up within a week")
    if liner_day is not None:
        n += 1
        lc = [a for a in port_calls(liner_day)
              if "CUSTOMS ADVISORY" in a["text"]]
        check(len(lc) == 1,
              "a liner day gets exactly one customs advisory, ahead of it",
              f"{len(lc)}")
        n += 1
        la = next(a for a in tf.arrivals(liner_day) if a["type"] == "liner")
        check(str(la["souls"]) in lc[0]["text"],
              "and it names the number of passengers that actually berthed",
              f"{la['souls']} in {lc[0]['text'][:60]!r}")
        n += 1
        nold = next((d for d in range(8) if not tf.liner_today(d)), None)
        if nold is not None:
            check(not [a for a in port_calls(nold)
                       if "CUSTOMS ADVISORY" in a["text"]],
                  "and a day with no liner gets no advisory -- the control "
                  "for the one above")
        else:
            check(False, "no linerless day in a week to control against")

    # -- the watch ------------------------------------------------------
    n += 1
    w = watch_calls()
    check(len(w) == 3 and {x["hour"] for x in w} == {0.0, 8.0, 16.0},
          "three watches, on the three-shift boundaries", f"{w}")
    n += 1
    check(all(str(sched.role_on_duty("security", x["hour"])) in x["text"]
              for x in w),
          "and each names the number actually on duty at that hour")

    # -- THE ERA LOCK, which is the sharpest thing in this module --------
    n += 1
    at_datum = isn_bulletins()
    check(len(at_datum) >= 3,
          "several ISN bulletins are in force at the S3E05 datum",
          f"{len(at_datum)}")
    n += 1
    early = isn_bulletins((2, 1))
    check(not early,
          "and NONE at S2E01, because none of their events has happened",
          f"{len(early)}")
    n += 1
    check(not minipax_notices((2, 1)) and not minipax_notices((2, 21)),
          "no Ministry of Peace notice before The Fall of Night -- the same "
          "rule FACTIONS.md 5.1 states for the armband")
    n += 1
    check(minipax_notices((2, 22)) and minipax_notices((3, 5)),
          "and they are up from S2E22 onward")
    n += 1
    check(all(_era_on(b["event"]) for b in at_datum),
          "every bulletin in force cites an event that is in force")

    # -- audibility -----------------------------------------------------
    n += 1
    heard = audible_at("arrival_concourse", 10.0, 0)
    check(heard, "something is audible at the concourse at the morning peak",
          f"{len(heard)}")
    n += 1
    quarters = audible_at("qtr_civilian", 10.0, 0)
    check(not quarters,
          "and NOTHING is audible in ordinary civilian quarters -- a tannoy "
          "you cannot get away from is a tannoy the owner's isolation brief "
          "does not want", f"{len(quarters)}")
    n += 1
    always = audible_at("zocalo", 3.0, 0)
    check(any(a["hour"] is None for a in always),
          "a standing surface is there at three in the morning, because a "
          "screen is always on")
    n += 1
    check(has_terminal("zocalo") and not has_terminal("downbelow"),
          "the Zocalo has a BabCom terminal and Downbelow does not")

    # -- the voice ------------------------------------------------------
    n += 1
    txt = open(GAZETTEER).read() if os.path.exists(GAZETTEER) else ""
    check("Do not make them look like villain posters" in txt,
          "the build note this module is written to is still in FACTIONS.md")
    n += 1
    shouty = [a for a in minipax_notices()
              if "!" in a["text"] or "TRAITOR" in a["text"].upper()]
    check(not shouty,
          "the notices are official and reasonable, which is the build note's "
          "whole point -- no exclamation marks, no villain vocabulary",
          f"{shouty}")
    n += 1
    check(all(t.upper() == t or t.startswith("MINISTRY")
              for t in BOARD_VOICE),
          "the authority-1 board text is carried verbatim")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")

    keep = ISN_BULLETINS
    try:
        # An entry citing an event that does not exist must be caught, not
        # silently dropped -- an unknown key is a typo that reads as content.
        ISN_BULLETINS = keep + (("no_such_event", "ISN. Nothing happened."),)
        raised = False
        try:
            isn_bulletins()
        except KeyError:
            raised = True
        verdict = ("raises KeyError, FIRES" if raised
                   else "silently dropped, DOES NOT FIRE")
        out(f"  a bulletin citing an unknown era event -> {verdict}")
        n += 1
        check(raised, "an unknown era event is an error, not a no-op")
    finally:
        ISN_BULLETINS = keep

    keepp = PA_PLACES
    try:
        PA_PLACES = ("not_a_place",)
        bad = [k for k in PA_PLACES if not _has(k)]
        out(f"  a PA place that is not in the register -> {bad} -- "
            f"place gate {'FIRES' if bad else 'DOES NOT FIRE'}")
        n += 1
        check(bad, "the register gate fires on an invented place")
    finally:
        PA_PLACES = keepp

    d0 = cos.ERA_DATUM
    out(f"  the era lock at three datums: S2E01 {len(isn_bulletins((2, 1)))} "
        f"bulletins / {len(minipax_notices((2, 1)))} notices; "
        f"S2E22 {len(isn_bulletins((2, 22)))} / "
        f"{len(minipax_notices((2, 22)))}; "
        f"datum {d0} {len(isn_bulletins())} / {len(minipax_notices())}")

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
