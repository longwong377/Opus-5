#!/usr/bin/env python3
"""What somebody says to you, derived from who they are and what is happening.

THE HOLE THIS FILLS, IN ITS OWN WORDS. `station/interact.py` defines eight
verbs and then excludes three of them from `RESPONDS`, and the comment says why:

    "`sit`, `rest` and `serve` are deliberately NOT here ... being served needs
     whoever is behind the counter to turn round and TALK, WHICH NEEDS
     DIALOGUE."

There was no dialogue. `STATE.md`'s own capability table reads *"talk to anyone
| no -- there is no dialogue system anywhere in the repository"*. 2,028 bodies
with names, jobs, homes, schedules, costumes and identicards, and the entire
player-facing consequence of all of it was `npc.gd` turning their heads.

DERIVED, NOT WRITTEN, AND THAT IS THE WHOLE DESIGN
--------------------------------------------------
This module is `station/broadcast.py` pointed at a person instead of a tannoy,
and it is built to the same rule: **a line of dialogue is a VIEW OF THE
SIMULATION**, not a string somebody typed. Nothing here holds content of its
own, so nothing here can drift from the station.

  * `npc/resident.py` supplies the person -- name, species, origin, age, role,
    the address they live at, the address they work at, where they eat, shop,
    pray and commute. A dock worker and an ambassador do not speak alike
    because the ROLE is a field, not a costume.
  * `npc/schedule.py` supplies the hour. Somebody stopped on their way to work
    says so, and the *daypart* in their greeting is THEIR OWN -- a Brakiri is a
    night dweller (`RHYTHMS["brakiri"].sleep_start == 9.0`), so at 13:00 they
    say good evening and mean it.
  * `npc/friction.py` supplies faction standing. A Narn meeting a Centauri at
    this datum does not speak at all -- FACTIONS.md 12, severity `highest` --
    and this module renders that as an ACTION line rather than inventing words
    for a silence the source is explicit about.
  * `npc/costume.py::ERA_EVENTS` supplies the era lock, exactly as
    `broadcast.py` uses it. A Narn before `narn_surrender` is a citizen of a
    great power; after it he is stateless. Same id, same hash, different line.
  * `traffic.py` and `broadcast.py` supply what the station is DOING. A customs
    officer on a liner day talks about the liner, and `hall_rate`'s own surge
    multiple is what makes that topic outrank the weather.
  * `npc/security.py` supplies the beat -- an officer names the period of the
    circuit he actually walks, computed off the built deck.

TOPIC SELECTION AND PHRASING ARE SEPARATE, and both are derived
---------------------------------------------------------------
**Topic** is a competition. Every topic function reads the simulation, returns
`None` when it does not apply, and scores its own SALIENCE from a number the
station computes -- the customs surge multiple, the friction severity ladder,
the officer count in the room, how many announcements are live. The winner is
drawn from the ranking by the speaker's own hash, so two people in one room
pick differently and both picks are deterministic.

**Phrasing** is a register. `_ROLE_REGISTER` has one row per `schedule.ROLES`
key and `_SPECIES_VOICE` one row per species in `schedule.ROLE_WEIGHTS`; both
are asserted TOTAL (every key has a row) and MINIMAL (neutralise any single row
and at least one produced line changes), which is the pair of assertions
`interact.py` uses to stop a table becoming a place to write opinions.

WHAT IS INVENTED HERE, PLAINLY. The **phrasings** are authority 5 -- three per
topic, one per voice band, written to the flat civic register `broadcast.py`
takes from the customs board. Everything INSIDE a phrasing is a number or a
name this repository computes. `INV-270..274` record the register tables, the
salience floors and the voice bands.

Run: python3 station/dialogue.py --selftest    # gates, each with a control
     python3 station/dialogue.py --report      # real exchanges with provenance
     python3 station/dialogue.py --sidecar <actors.json> --out <dialogue.json>
"""

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, replace

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)

import broadcast as bc                                          # noqa: E402
import directory as dr                                          # noqa: E402
import traffic as tf                                            # noqa: E402
from npc import costume as cos                                  # noqa: E402
from npc import friction as fr                                  # noqa: E402
from npc import resident as res                                 # noqa: E402
from npc import schedule as sched                               # noqa: E402
from npc import security as sec                                 # noqa: E402


# ---------------------------------------------------------------------------
# A CALLER-SIDE MEMO ON A PURE FUNCTION, AND WHERE THE FIX REALLY BELONGS
# ---------------------------------------------------------------------------
# Six exchanges took 7.06 s and the profile is unambiguous: 31 s of a 31 s run
# was `traffic.arrivals`, which calls `_inverse_curve` once per arrival and
# `_inverse_curve` sums a 2,880-sample curve every time -- 4.4 million calls to
# `day_curve` for one day's manifest. It is a pure function of `day` and it is
# recomputed on every call, including from `hall_rate` and `broadcast.day`.
#
# CLAUDE.md: "A SLOW SUITE IS A BUG UNTIL PROFILED, NOT A CONTENT COST." This
# is that bug, and the proper fix is one `@lru_cache` in `station/traffic.py`,
# which is not this session's file. So the memo is applied from the caller
# side, where it is visible: the wrapper hands every caller its own list, so a
# caller that mutates the result cannot poison the cache.
def _memoise_traffic():
    import functools                                            # noqa: PLC0415
    if getattr(tf.arrivals, "_dialogue_memo", False):
        return
    raw = tf.arrivals

    @functools.lru_cache(maxsize=64)
    def _cached(day):
        return tuple(raw(day))

    def arrivals(day=0):
        return list(_cached(day))

    arrivals._dialogue_memo = True
    arrivals.__doc__ = (raw.__doc__ or "") + "\n\nMemoised by station/dialogue."
    tf.arrivals = arrivals


_memoise_traffic()


def _u(seed: str, salt: str = "") -> float:
    """Uniform [0,1) from a string. `resident._u`'s construction, not `hash`."""
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ===========================================================================
# 1.  Who is talking, and to whom
# ===========================================================================

@dataclass(frozen=True)
class Listener:
    """The player, as the friction model needs to see them.

    `npc/friction.py` keys its table on SPECIES or ROLE -- the two vocabularies
    this project already has -- so the player has to present both. The defaults
    are what `docs/MASTER-PLAN.md`'s player track describes: a human civilian
    who arrived on a transport, which is `role="visitor"` in `schedule.ROLES`.

    `psi` is here because FACTIONS.md 12 gives telepaths their own row and it is
    the one attribute of a player that changes every conversation on the
    station. Nothing sets it yet; it is a parameter so that the day something
    does, no line in this file changes.
    """
    species: str = "human"
    role: str = "visitor"
    psi: bool = False
    armband: bool = False


@dataclass(frozen=True)
class World:
    """What the station is doing. Everything here indexes an existing system.

    `day` indexes `traffic.arrivals`, `hour` is Earth Mean Time (authority 1,
    the customs board), `datum` is `costume.ERA_DATUM`'s (season, episode).
    """
    hour: float = 13.0
    day: int = 0
    datum: tuple = None
    # DLG-06's two halves, and they are properties of the SITTING rather than
    # of the station -- which is why they live here and not on the speaker.
    # `session` is the play session a scarce voice must not repeat inside;
    # `audience` is how many bodies are in the room, because the Broker's
    # price is set by who else is listening. `None` means the caller did not
    # say, and a caller who did not say gets the public manner.
    session: str = ""
    audience: int = None
    # WHICH TURN OF THE CONVERSATION THIS IS. The anti-repeat rule needs an
    # ordinal and DETERMINISM forbids a hidden ledger -- `_selftest`'s
    # "the same world state twice gives the same lines" caught exactly that
    # when the draw kept its own mutable set, and it was right to. So the
    # position in the draw is an INPUT, and the draw is a pure permutation.
    turn: int = 0

    @property
    def era(self):
        return self.datum or cos.ERA_DATUM


@dataclass(frozen=True)
class Line:
    who: str          # "npc" | "you"
    kind: str         # "speech" | "action"
    text: str
    source: str       # the module and call that supplied the FACT in it


@dataclass(frozen=True)
class Choice:
    """One thing the PLAYER can say, and what it gets them.

    A STANCE, NOT A FLAVOUR. `docs/spec/PEOPLE.md` DLG-05 is explicit --
    *"Choices are stances, not flavour"* -- so the three differ in what they
    are worth rather than in tone: `ask` gets the qualitative half of the
    topic, `press` gets the NUMBER THAT DECIDED THE TOPIC'S SALIENCE and can
    be refused, `let_go` gets nothing and ends the conversation. Dropping it
    is a real choice because the number is real and you do not get it.
    """
    stance: str        # "ask" | "press" | "let_go"
    text: str          # what the PLAYER says
    reply: tuple       # the Lines they answer with; empty is an answer too
    yielded: bool      # did the register let them be drawn out
    source: str


@dataclass(frozen=True)
class Exchange:
    npc_id: str
    name: str
    species: str
    role: str
    place: str
    hour: float
    topic: str
    band: int
    lines: tuple
    ranking: tuple = ()          # every applicable topic and its salience
    sources: tuple = ()
    # WHAT THE PLAYER MAY SAY, and the index in `lines` it is offered after.
    # BOTH DEFAULT TO "NOTHING", which is what keeps every existing caller --
    # `report`, the selftest, the committed sidecars, `dialogue.gd`'s reader --
    # reading exactly what it read before this field existed.
    choices: tuple = ()
    choice_at: int = -1

    @property
    def spoken(self):
        return tuple(x for x in self.lines if x.kind == "speech")

    @property
    def said(self):
        """Every player utterance this exchange offers. The DLG-05 denominator."""
        return tuple(c.text for c in self.choices)

    def text(self):
        return " / ".join(x.text for x in self.lines)

    def transcript(self, stance: str = "press"):
        """The whole conversation with one stance taken, as it would be heard.

        THE ONLY PLACE THE TWO HALVES ARE JOINED, so a gate that asks what a
        player actually experiences does not have to reimplement the splice
        that `godot/scripts/dialogue.gd` performs at runtime.
        """
        out = []
        for i, ln in enumerate(self.lines):
            out.append(ln)
            if i == self.choice_at:
                for c in self.choices:
                    if c.stance != stance:
                        continue
                    out.append(Line("you", "speech", c.text, c.source))
                    out.extend(c.reply)
        return tuple(out)


# ===========================================================================
# 2.  The register -- how a person speaks
# ===========================================================================
# TWO TABLES, BOTH KEYED ON SOMETHING THIS REPOSITORY ALREADY DECIDED. A third
# vocabulary is a third thing to drift (interact.py's own note), so the rows
# here are `schedule.ROLES` and `schedule.ROLE_WEIGHTS` and nothing else.
#
# `formality` is how much ceremony a sentence carries; `terseness` is how few
# words it is willing to spend. They are separate because they are separate:
# a Minbari cleric is formal and unhurried, a dock foreman is informal and
# clipped, and an EarthForce watch officer is BOTH formal and clipped.
#
# Values are authority 5 and every one has the sentence from `schedule.ROLES`
# or FACTIONS.md that produced it. INV-270.
_DEFAULT_ROLE = (0.50, 0.50)

_ROLE_REGISTER = {
    # key:          (formality, terseness, why)
    "command":      (0.85, 0.70, "EarthForce watch officers: FACTIONS.md 3.2's "
                                 "command structure. Formal and clipped"),
    "security":     (0.80, 0.75, "2.2's 500 officers. A caution is a formula "
                                 "and a formula is short"),
    "customs":      (0.85, 0.60, "3.4 makes the identicard check the routine "
                                 "power; the voice is the customs board's"),
    "traffic":      (0.75, 0.85, "Bay control talks in call signs"),
    "medical":      (0.70, 0.45, "300 medical staff; a clinician explains"),
    "diplomat":     (0.95, 0.25, "7.2 and 8.1's missions. Ceremony IS the job"),
    "envoy":        (1.00, 0.95, "Kosh. Two public hours a day (12), and "
                                 "almost nothing said in them"),
    "cleric":       (0.90, 0.30, "11.3's orders and the four Sanctuaries"),
    "financier":    (0.70, 0.55, "2.5's rigid office hours in a station with "
                                 "no day"),
    "merchant":     (0.45, 0.40, "11.1's guilds. A pitch is not terse"),
    "service":      (0.40, 0.45, "Bars and food service; the largest civilian "
                                 "block after industry"),
    "engineer":     (0.35, 0.65, "1,800 of them (2.2). Shop-floor register"),
    "industrial":   (0.25, 0.70, "Grey's 90 decks; 24 h, 3 shifts (2.5)"),
    "dockworker":   (0.20, 0.80, "S1E12's strike. The bluntest voice aboard"),
    "waste":        (0.25, 0.75, "The plant Downbelow is built around (11.2)"),
    "hydroponics":  (0.35, 0.50, "An agricultural shift, 05:00-13:00 (2.5)"),
    "visitor":      (0.55, 0.50, "2.3's 45,000 transients. No local idiom yet"),
    "refugee":      (0.60, 0.35, "6.2's 13,000. Formal because asking is what "
                                 "the day consists of"),
    "lurker":       (0.15, 0.85, "11.2's underclass. Says as little as it can "
                                 "to anyone who might be official"),
}

# One row per species in `schedule.ROLE_WEIGHTS`. `f`/`t` are ADDITIVE offsets
# on the role's own numbers, which is what keeps the two tables independent: a
# Narn dock worker is a Narn AND a dock worker.
#
# `address` is what they call you when the register is formal enough to use a
# form of address at all. Every one is either attested in FACTIONS.md or is the
# polity's own word for an outsider; nothing here is a catchphrase.
_DEFAULT_VOICE = (0.0, 0.0, "")

_SPECIES_VOICE = {
    # key:        (formality delta, terseness delta, address, why)
    "human":      (0.00, 0.00, "", "The reference. 2.4's 62% share sets the "
                                   "station's default register"),
    "narn":       (0.10, 0.20, "", "6.1: at the datum a defeated people under "
                                   "terms that make restraint the ambient "
                                   "state. Formal, short, nothing volunteered"),
    "centauri":   (0.25, -0.30, "", "7.1's declining aristocracy. Elaboration "
                                    "is the tell"),
    "minbari":    (0.30, -0.05, "", "8.1's religious caste is the bulk aboard; "
                                    "12 gives 'cold formality' explicitly"),
    "drazi":      (-0.20, 0.30, "", "9.2 and S2E03: blunt, factional, loud"),
    "brakiri":    (0.10, 0.05, "", "9.2 night dwellers and financiers; the "
                                   "commercial register of a different clock"),
    "pakmara":    (0.05, 0.35, "", "12: the only species with a segregated "
                                   "food economy. Speaks to outsiders least"),
    "vree":       (0.00, 0.15, "", "9.2 traders; no attested manner"),
    "abbai":      (0.15, -0.10, "", "9.2: League diplomacy and water science"),
    "gaim":       (0.05, 0.40, "", "9.2's hive-caste insectoids, in encounter "
                                   "suits. A hive does not chat"),
    "hyach":      (0.20, 0.00, "", "9.2: an old, formal League power"),
    "llort":      (-0.15, 0.20, "", "9.2's scavengers"),
    "grome":      (0.00, 0.10, "", "9.2, agricultural"),
    "other":      (0.00, 0.00, "", "9.2's tail bucket is not a species"),
    "vorlon":     (1.00, 1.00, "", "12: 'almost never seen'. Kosh answers a "
                                   "question with a question or not at all"),
}

# The three voice bands the phrasing tables are indexed by. The band is a
# FUNCTION of the two register numbers rather than a third field, so a role and
# a species that pull in opposite directions land in the middle instead of
# needing a row of their own. INV-272.
BAND_FORMAL, BAND_PLAIN, BAND_BLUNT = 0, 1, 2
BAND_NAME = ("formal", "plain", "blunt")


@dataclass(frozen=True)
class Register:
    formality: float
    terseness: float
    warmth: float
    band: int
    address: str
    armband: bool
    officer: bool
    era: tuple
    friction: tuple = None         # the friction.pair row, or None
    why: tuple = ()


def _era_on(event: str, datum=None) -> bool:
    """Delegated to `costume.era_active` for INV-240's reason: one era clock."""
    return cos.era_active(event, datum or cos.ERA_DATUM)


def _facets(species: str, role: str, psi: bool) -> tuple:
    """The keys `friction.pair` can match this person on.

    A person is a species AND a job AND, sometimes, a telepath -- and
    FACTIONS.md 12 has rows for all three kinds. Matching on only one of them
    loses the Narn/EarthGov row (a species against a role) entirely.
    """
    out = [species, role]
    if psi:
        out.append("telepath")
    return tuple(out)


# `friction.PAIRS` is mixed-vocabulary -- a row's side may be a species key or
# a role key -- so the join has to be a cross product. THE WILDCARD IS WHERE
# THAT GOES WRONG, and it did: `("human", "*", "high", ...)` is FACTIONS.md 12's
# **human vs ALIEN** row, and a cross product that offers `("human",
# "visitor")` to it matches, because `visitor` is not `human`. The first run of
# this module had every human in the Zocalo refusing to speak to a human
# player, sourced to a row about aliens.
#
# So a `*` side must be filled by a SPECIES. Nothing else is "anyone else".
_SPECIES_KEYS = frozenset(sched.ROLE_WEIGHTS)


def standing(speaker, listener: Listener, datum=None):
    """The strongest friction row between these two, and what matched it.

    Returns `(row, speaker_key, listener_key)` or None. The matched keys are
    carried because a source line that says `pair('human', 'human')` when the
    row that fired was `('human', '*')` is a provenance string that lies.
    """
    best = None
    a = _facets(speaker.species, speaker.role, speaker.licensed_psi)
    b = _facets(listener.species, listener.role, listener.psi)
    for x in a:
        for y in b:
            for p in _rows(x, y, datum):
                if best is None or (fr.SEVERITY[p[2]][0]
                                    > fr.SEVERITY[best[0][2]][0]):
                    best = (p, x, y)
    return best


def _rows(x: str, y: str, datum=None):
    """Every acceptable friction row for the ordered pair `(x, y)`.

    NOT `friction.pair`, AND THE REASON IS A DEFECT IT HID. `pair()` collapses
    to the strongest row before returning, so when a human meets a telepath it
    answers with the `("human", "*")` row -- which is about ALIENS, is the same
    severity, and comes first in the table. Filtering that one out afterwards
    left nothing, and the Psi badge row FACTIONS.md 12 calls High could never
    fire. The wildcard filter has to run BEFORE the collapse, so the scan has
    to be here.
    ``fr._match`` is imported rather than reimplemented: a second reading of
    what `*` means is exactly what went wrong the first time.
    """
    out = []
    for row in fr.PAIRS:
        pa, pb, _sev, _auth, _why = row
        if not fr._match(pa, pb, x, y):                          # noqa: SLF001
            continue
        # friction.pair's own era condition, on friction's own constant.
        if pa == "human" and pb == "*" and not _era_on(fr.NIGHTWATCH_EVENT,
                                                       datum):
            continue
        if "*" in (pa, pb):
            named = pa if pb == "*" else pb
            other = y if x == named else x
            if other not in _SPECIES_KEYS:
                continue
        out.append(row)
    if not out:
        p = fr.pair(x, y, datum)          # the League bloc, which is synthesised
        if p is not None and "*" not in (p[0], p[1]) and p not in fr.PAIRS:
            out.append(p)
    return out


# WHAT A FRICTION ROW MAKES SOMEBODY DO, in the gazetteer's own words. Taking
# the row's `why` field rather than writing a behaviour here is the same
# discipline `separation_m` uses: one description of the friction, and the
# crowd's spacing and the conversation both read it.
def _behaviour(row) -> str:
    why = row[4]
    if ":" in why.split(".")[0]:
        why = why.split(":", 1)[1]
    return why.split(".")[0].strip()


# The two rows FACTIONS.md 12 describes as SILENCE -- "Neither speaks" for the
# Narn and the Centauri, "the corridor clears" for Kosh. Everything milder is a
# withheld greeting and a flatter voice, not a refusal, because the source says
# so: the Nightwatch row's behaviour is *lowering* a voice, not stopping it.
REFUSAL_SEVERITY = fr.SEVERITY["highest"][0]
COLD_SEVERITY = fr.SEVERITY["medium-high"][0]


def register(speaker, listener: Listener, world: World,
             condition: int = 0) -> Register:
    """How this person speaks to this listener, right now."""
    rr = _ROLE_REGISTER.get(speaker.role, _DEFAULT_ROLE)
    f0, t0 = rr[0], rr[1]
    sv = _SPECIES_VOICE.get(speaker.species, _DEFAULT_VOICE)
    df, dt, addr = sv[0], sv[1], sv[2]
    formality = min(1.0, max(0.0, f0 + df))
    terseness = min(1.0, max(0.0, t0 + dt))

    st = standing(speaker, listener, world.datum)
    p = st[0] if st else None
    # WARMTH IS THE FRICTION LADDER, INVERTED, and it is not a new number:
    # `friction.SEVERITY`'s first column is the separation multiple the crowd
    # already keeps, 1.0 (nothing) to 6.0 (Kosh). Warmth is what is left of 1
    # after that has been taken out of it.
    warmth = 1.0 if p is None else max(0.0, 1.0 - (fr.SEVERITY[p[2]][0] - 1.0)
                                       / 5.0)

    # The band. Formality pushes up the scale and terseness pushes down it,
    # which is why an EarthForce watch officer (formal AND clipped) lands
    # plain while a Minbari cleric (formal, unhurried) lands formal.
    score = formality - 0.5 * terseness
    band = (BAND_FORMAL if score >= 0.45
            else BAND_PLAIN if score >= 0.10 else BAND_BLUNT)

    # PLY-06's ENTIRE DIALOGUE EFFECT, AND IT IS ONE LINE ON PURPOSE.
    # `condition.Condition.effects()["warmth_band"]` is -1, 0 or +1: a fed
    # player is met one band warmer and a hungry one a band colder, which the
    # spec phrases as "NPCs open one topic sooner". It moves the BAND and
    # nothing else -- not `warmth`, which is the friction separation and
    # belongs to the pair rather than to the player's stomach, and not the
    # address form, which is a fact about rank.
    #
    # NEGATIVE ON THE SCALE: BAND_FORMAL is 0 and BAND_BLUNT is 2, so warmer
    # is DOWN. A +1 warmth band subtracts. Written out because the sign is the
    # kind of thing that reads correct either way and is only correct one way.
    if condition:
        band = max(BAND_FORMAL, min(BAND_BLUNT, band - int(condition)))

    armband = False
    if speaker.species == "human" and speaker.role == "security":
        armband = sec.wears_armband(speaker.npc_id, speaker.species)
    return Register(formality=formality, terseness=terseness, warmth=warmth,
                    band=band, address=addr, armband=armband,
                    officer=(speaker.role == "security"), era=world.era,
                    friction=st,
                    why=(rr[2] if len(rr) > 2 else "",
                         sv[3] if len(sv) > 3 else ""))


# ---------------------------------------------------------------------------
# Their own clock
# ---------------------------------------------------------------------------
# THE MOST-SEEN DERIVED DETAIL IN THE MODULE and it costs four lines. A
# greeting names a part of the day, and *whose* day is a question this station
# has fifteen answers to: `schedule.RHYTHMS["brakiri"].sleep_start` is 09:00, so
# a Brakiri financier at 13:00 is four hours into their evening and says so.
# Station clock time is Earth Mean Time (authority 1, the customs board) and it
# is the WRONG clock for eleven of the fifteen species aboard.
_DAYPART = (("early", 0.15), ("morning", 0.35), ("midday", 0.55),
            ("afternoon", 0.75), ("evening", 0.92), ("late", 1.01))

# What a greeting calls each of those. Six parts, three words -- English has no
# greeting for "late in my waking period".
_GREET_WORD = {"early": "morning", "morning": "morning", "midday": "day",
               "afternoon": "afternoon", "evening": "evening",
               "late": "evening", "asleep": "evening"}


def daypart(species: str, hour: float) -> str:
    """Where in THEIR OWN waking day `hour` falls."""
    r = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
    if r.sleep_hours >= 24.0:
        return "asleep"
    wake = sched.wake_hour(species)
    awake = 24.0 - r.sleep_hours
    t = (hour - wake) % 24.0
    if t >= awake:
        return "asleep"
    f = t / awake
    for name, hi in _DAYPART:
        if f < hi:
            return name
    return "late"


# A REGISTER NAME IS A CATALOGUE ENTRY AND NOBODY SPEAKS ONE. 22 of the 128
# rows in `directory.PLACES` carry a disambiguating slash or a parenthetical
# count -- "Transport tubes / lifts (between levels)", "Docking bays (24)",
# "Security posts / checkpoints" -- because the register's job is to be
# unambiguous across 128 places. Put verbatim in a mouth it reads as a database
# field, which is the same fidelity failure as the era topic naming an episode.
#
# The first alternative and no parenthetical is what a person says: "Transport
# tubes", "Docking bays", "Security posts". The register keeps its precision;
# this is a RENDERING of it for speech, not a second name, so nothing can
# drift. INV-300.
def _spoken(name: str) -> str:
    out = name.split("(")[0].split("/")[0].strip().rstrip(",;")
    return out or name


def _place_name(key: str) -> str:
    if not key:
        return ""
    try:
        return _spoken(dr.by_key(key)["name"])
    except Exception:                                           # noqa: BLE001
        return key.replace("_", " ")


def _hhmm(hour: float) -> str:
    h = int(hour) % 24
    m = int(round((hour - int(hour)) * 60.0)) % 60
    return f"{h:02d}{m:02d}"


# ===========================================================================
# 3.  Topics -- what there is to say, and how much it matters
# ===========================================================================
# A TOPIC SCORES ITSELF FROM A NUMBER THE STATION COMPUTES. That is the rule,
# and where a topic has no such number it takes a PERSONAL floor from the table
# below -- declared, authority 5, INV-271 -- which is deliberately low so that
# anything happening on the station outranks anything happening in a life.
#
# The floors are ordered rather than tuned: what you are doing right now beats
# where you live, which beats what you believe.
PERSONAL = {
    "shift": 1.30, "trade": 1.25, "meal": 1.10, "beat": 1.60,
    "home": 1.00, "worship": 0.90, "visa": 1.20, "era": 1.20,
}

# How long an announcement is still "now", matching `broadcast.audible_at`.
NEWS_WINDOW_H = 0.25

# How far ahead a farewell looks. Half an hour is `schedule.TRANSIT_H`, the
# time this project already says a commute takes -- so "I'm due at X" is said
# exactly when leaving now would get them there.
FAREWELL_LOOKAHEAD_H = sched.TRANSIT_H


def _topic_refusal(sp, li, w, reg):
    """They do not talk to you at all, and FACTIONS.md 12 says which pairs.

    RENDERED AS AN ACTION, NOT AS WORDS. The source is explicit -- "Neither
    speaks" -- so inventing a line for a Narn meeting a Centauri would be
    inventing the opposite of what is attested. The behaviour text is the
    gazetteer row's own `why` field, first clause, so this cannot drift from
    the crowd's separation model.
    """
    if reg.friction is None:
        return None
    p, x, y = reg.friction
    if fr.SEVERITY[p[2]][0] < REFUSAL_SEVERITY:
        return None
    return {"key": "refusal", "salience": fr.SEVERITY[p[2]][0],
            "action": _behaviour(p),
            "source": f"npc/friction.pair({x!r}, {y!r}) -> row "
                      f"({p[0]!r}, {p[1]!r}) {p[2]} "
                      f"(FACTIONS.md 12, authority {p[3]})"}


def _topic_port(sp, li, w, reg):
    """A ship. The salience is `traffic.hall_rate`'s own surge multiple."""
    r = tf.hall_rate(w.hour, w.day)
    arrivals = tf.arrivals(w.day)
    # THE SHIP THAT EXPLAINS THE SURGE, not merely the nearest one. When
    # `hall_rate` reports a liner contribution the hall is full BECAUSE of the
    # liner, and naming the freighter that happened to berth nine minutes
    # earlier would be a line that contradicts the number beside it.
    pool = ([a for a in arrivals if a["type"] == "liner"]
            if r["liner_per_min"] > 0 else arrivals)
    near = None
    for a in pool or arrivals:
        d = min(abs(a["hour"] - w.hour), abs(a["hour"] - w.hour + 24.0),
                abs(a["hour"] - w.hour - 24.0))
        if near is None or d < near[0]:
            near = (d, a)
    if near is None or near[0] > 1.5:
        return None
    d, a = near
    what = bc.SHIP_CALL.get(a["type"], a["type"])
    # A dock worker, a customs officer, a traffic controller and a bay porter
    # are the people a berthing is FOR; everyone else needs the hall to be
    # surging before a ship is worth mentioning.
    trade = sp.role in ("dockworker", "customs", "traffic", "service")
    if not trade and r["multiple"] < 1.5:
        return None
    # Surge multiple, plus recency: an arrival ten minutes ago outranks one
    # ninety minutes ago at the same hall rate.
    sal = r["multiple"] * (1.0 + max(0.0, 1.0 - d)) + (0.8 if trade else 0.0)
    return {"key": "port", "salience": sal,
            "fact": {"ship": what, "souls": a["souls"],
                     "berth": ("the bays" if a["berth"] == "bay"
                               else "standoff"),
                     "when": _hhmm(a["hour"]),
                     "rate": r["total_per_min"], "mult": r["multiple"]},
            "source": f"traffic.arrivals({w.day}) + traffic.hall_rate"
                      f"({w.hour:.2f}) x{r['multiple']:.1f} + "
                      f"broadcast.SHIP_CALL[{a['type']!r}]"}


def _headline(text: str) -> str:
    """The first sentence of a bulletin, without the masthead.

    `broadcast.ISN_BULLETINS` writes for a newsreader -- "ISN. Earth Alliance
    medical authorities confirm ..." -- and a person in a corridor repeats the
    substance, not the station identification.
    """
    body = text
    for lead in ("ISN.", "MINISTRY OF PEACE.", "ATTENTION."):
        if body.startswith(lead):
            body = body[len(lead):].strip()
            break
    first = body.split(". ")[0].strip().rstrip(".")
    return first


def _topic_news(sp, li, w, reg):
    """What the screens and the tannoy are saying HERE, right now.

    Era-locked for free: `broadcast.audible_at` filters ISN bulletins and
    Ministry of Peace notices through `costume.ERA_EVENTS`, so a Nightwatch
    notice cannot be repeated by anybody before *The Fall of Night*.
    """
    heard = [x for x in bc.audible_at(sp.place, w.hour, w.day, NEWS_WINDOW_H,
                                      w.datum)
             # A PORT CALL IS NOT NEWS, it is the `port` topic, and a watch
             # call is an instruction to somebody else. What a person talks
             # ABOUT is the screen and the notice -- the two surfaces
             # FACTIONS.md 11.5 calls the propaganda layer -- and both are
             # already era-locked by `broadcast`.
             if x["kind"] in ("isn", "minipax")]
    if not heard:
        return None
    live = [x for x in heard if x["hour"] is not None]
    standing_ = [x for x in heard if x["hour"] is None]
    pick = live[0] if live else standing_[
        int(_u(sp.npc_id, "news") * len(standing_))]
    # A LIVE CALL IS LOUDER THAN A POSTER, and a poster is quieter than what
    # you are doing. `broadcast.audible_at` returns the standing surfaces at
    # every hour -- a screen is always on -- so scoring a poster like an event
    # made 25 of the first 73 exchanges on the deck about the Ministry of Peace
    # noticeboard. A standing surface therefore sits BELOW the personal floors
    # and a live announcement well above them.
    sal = (1.4 + 0.9 * len(live)) if live else 1.15
    if pick["kind"] == "minipax":
        # FACTIONS.md 5.4's visible consequence: an armband agrees with the
        # Ministry out loud and a civilian looks at the floor.
        sal += 0.9 if reg.armband else 0.25
    return {"key": "news", "salience": sal,
            # `live` is the count that DECIDED the salience above, carried so a
            # player who presses gets that number rather than a second opinion
            # about it. See `PRESSED` -- every row names its topic's own
            # salience input, which is the one thing the first line never says.
            "fact": {"kind": pick["kind"], "text": _headline(pick["text"]),
                     "live": len(live)},
            "source": f"broadcast.audible_at({sp.place!r}, {w.hour:.2f}) -> "
                      f"{pick['kind']}; {pick['source']}"}


_BEAT = {}


def _beat(sector: str):
    """`security.beat`, once per sector. It walks the cell plan to get there."""
    if sector not in _BEAT:
        try:
            _BEAT[sector] = sec.beat(sector)
        except Exception:                                       # noqa: BLE001
            _BEAT[sector] = None
    return _BEAT[sector]


def _topic_beat(sp, li, w, reg):
    """An officer's own circuit, measured off the built deck."""
    if sp.role != "security":
        return None
    q = _q(sp.place)
    sector = (q or {}).get("sector") or "blue"
    b = _beat(sector)
    if b is None:
        return None
    on = sec.on_duty(w.hour)
    posted = sp.place in [p[0] for p in sec.POSTS]
    sal = PERSONAL["beat"] + (0.5 if posted else 0.0)
    return {"key": "beat", "salience": sal,
            "fact": {"sector": sector, "min": b["period_s"] / 60.0,
                     "on": on, "pairs": sec.roving_pairs(w.hour),
                     "posted": posted, "armband": reg.armband},
            "source": f"npc/security.beat({sector!r}) period "
                      f"{b['period_s'] / 60.0:.1f} min over "
                      f"{b['circumference_m']:.0f} m + on_duty({w.hour:.1f})"
                      f"={on}"}


def _topic_trade(sp, li, w, reg):
    """What they sell, and where they stand to sell it.

    The counter is not invented: it is the declared interactable in their own
    workplace whose verb `interact.py` derives as `serve`. That is the same
    resolution the runtime uses to put a prompt on it.
    """
    if sp.role not in ("merchant", "service", "financier"):
        return None
    q = _q(sp.job)
    if q is None:
        return None
    counters = [t for t in (q.get("interacts") or ()) if _verb(t) == "serve"]
    if not counters:
        return None
    return {"key": "trade", "salience": PERSONAL["trade"]
            + (0.4 if sp.job == sp.place else 0.0),
            "fact": {"where": _spoken(q["name"]), "counter": counters[0].replace(
                "_", " "), "here": sp.job == sp.place,
                "what": ", ".join(q.get("functions") or ())},
            "source": f"resident.job={sp.job!r} -> directory.by_key + "
                      f"interact.verb_of({counters[0]!r})='serve'"}


def _topic_shift(sp, li, w, reg):
    """Where the clock says they are going, and when they are due."""
    act = sched.activity_at(sp.npc_id, sp.species, w.hour)
    if act not in (sched.Activity.WORK, sched.Activity.TRANSIT):
        return None
    if not sp.job:
        return None
    start, hours = sched.work_window(sp.npc_id, sp.species)
    q = _q(sp.job)
    # ALREADY THERE, OR ON THE WAY. "I am due at the Zocalo" said by a
    # stallholder standing in the Zocalo is the failure this flag exists to
    # stop, and the answer is a comparison the caller already supplied: the
    # place they are standing in against the place `resident.job` names.
    here = sp.place == sp.job
    return {"key": "shift", "salience": PERSONAL["shift"]
            + (0.4 if act is sched.Activity.TRANSIT else 0.0),
            "fact": {"job": _spoken((q or {}).get("name", sp.job)),
                     "start": _hhmm(start), "end": _hhmm(start + hours),
                     "hours": hours, "here": here,
                     "transit": act is sched.Activity.TRANSIT,
                     "via": _place_name(sp.commutes_via)},
            "source": f"npc/schedule.activity_at -> {act.value}; "
                      f"work_window={start:.2f}+{hours:.1f}h; "
                      f"resident.job={sp.job!r}"
                      f"{' (standing in it)' if here else ''}"}


def _topic_meal(sp, li, w, reg):
    """A meal, at one of their own species' hours."""
    act = sched.activity_at(sp.npc_id, sp.species, w.hour)
    if act is not sched.Activity.EAT:
        return None
    r = sched.RHYTHMS.get(sp.species, sched.RHYTHMS["human"])
    where = sp.eats_at or sp.home
    return {"key": "meal", "salience": PERSONAL["meal"],
            "fact": {"where": _place_name(where),
                     "meals": len(r.meals),
                     "out": bool(sp.eats_at),
                     "segregated": sp.species == "pakmara"},
            "source": f"npc/schedule.activity_at -> eat; "
                      f"RHYTHMS[{sp.species!r}].meals={r.meals}; "
                      f"resident.eats_at={where!r}"}


def _topic_home(sp, li, w, reg):
    """Where they live -- and Downbelow is a different sentence."""
    if not sp.home:
        return None
    down = sp.home in res.DOWNBELOW_HOMES
    sal = PERSONAL["home"] + (0.9 if down else 0.0)
    fact = {"home": _place_name(sp.home), "down": down}
    src = f"resident.home_for -> {sp.home!r}"
    if down:
        h = sec.hostility(sp.place, w.hour)
        fact["m2"] = sec.SQUAT_M2_PER_PERSON
        fact["policed"] = h["policed"]
        src += (f"; security.hostility({sp.place!r}) policed="
                f"{h['policed']}; SQUAT_M2_PER_PERSON="
                f"{sec.SQUAT_M2_PER_PERSON:.0f}")
    return {"key": "home", "salience": sal, "fact": fact, "source": src}


def _topic_worship(sp, li, w, reg):
    if sp.role != "cleric" and sched.activity_at(
            sp.npc_id, sp.species, w.hour) is not sched.Activity.WORSHIP:
        return None
    where = sp.prays_at or sp.job
    if not where:
        return None
    return {"key": "worship", "salience": PERSONAL["worship"]
            + (0.5 if sp.role == "cleric" else 0.0),
            "fact": {"where": _place_name(where), "cleric": sp.role == "cleric"},
            "source": f"resident.prays_at={where!r} + "
                      f"schedule.ROLES['cleric'] (FACTIONS.md 11.3)"}


def _topic_visa(sp, li, w, reg):
    """The identicard field that decides whether they will meet your eye.

    `resident._visa` gives a lurker `NO STATUS` 55% of the time, and
    LAW-CRIME-DOWNBELOW.md 3.4 is the reason it matters: it is *"the reason
    lurkers avoid readers"*. So the topic exists only when the room HAS a
    reader, which is a declared interactable this module looks up rather than
    assumes.
    """
    if not sp.visas:
        return None
    q = _q(sp.place)
    reader = any(t.endswith("reader") for t in ((q or {}).get("interacts")
                                                or ()))
    if sp.visas == "NO STATUS" and not reader:
        return None
    # FOUR STATES, and `resident._visa` produces all four. EXPIRED is the one
    # that matters most: LAW-CRIME-DOWNBELOW.md 3.4 calls expired status the
    # station's MOST ORDINARY crime, which makes it the most ordinary thing a
    # stranger in a corridor is anxious about.
    state = ("nostatus" if sp.visas == "NO STATUS"
             else "expired" if "EXPIRED" in sp.visas
             else "sanctuary" if sp.visas.startswith("SANCTUARY")
             else "transit")
    bump = {"nostatus": 1.1 if reader else 0.0, "expired": 0.9,
            "sanctuary": 0.2, "transit": 0.0}[state]
    return {"key": "visa", "salience": PERSONAL["visa"] + bump,
            "fact": {"visa": sp.visas, "reader": reader, "state": state},
            "source": f"resident.identicard VISAS={sp.visas!r} -> {state}"
                      + ("; the room declares an identicard reader "
                         "(LAW-CRIME-DOWNBELOW 3.4)" if reader else "")}


# THE ERA TOPIC. Each row is (event, species-or-role it lands on, and the fact
# the event makes true of that person). `costume.ERA_EVENTS` is the clock, so
# the same id at S2E01 and at the S3E05 datum produces different rows without
# anything here knowing what a season is.
_ERA_ROWS = (
    ("narn_surrender", "narn",
     "FACTIONS.md 6.1: after E6 a Narn aboard is stateless -- 13,000 refugees "
     "who were citizens of a great power eighteen months earlier"),
    ("narn_surrender", "centauri",
     "FACTIONS.md 7.1: the Republic is ascendant and 12 says the restraint "
     "runs the other way"),
    ("nightwatch_visible", "human",
     "FACTIONS.md 5.4 and 12: a human lowers his voice when an armband "
     "passes"),
    ("markab_extinct", "*",
     "FACTIONS.md 1.1 E4: an entire species died aboard this station"),
    ("monastics_resident", "cleric",
     "FACTIONS.md 11.3: Brother Theo's order takes up permanent residence"),
)


def _topic_era(sp, li, w, reg):
    """What the era has done to this person. The sharpest thing in the module.

    An `_ERA_ROWS` entry fires only when `costume.era_active` says its event
    has happened, so this is the topic that makes the SAME PERSON say a
    different thing at two datums with no other input changed.
    """
    rows = [r for r in _ERA_ROWS
            if _era_on(r[0], w.datum)
            and (r[1] == "*" or r[1] in (sp.species, sp.role))]
    if not rows:
        return None
    ev, who, why = rows[int(_u(sp.npc_id, "era") * len(rows))]
    # AN ERA THAT HAPPENED TO YOU OUTRANKS ONE THAT HAPPENED. `narn_surrender`
    # on a Narn is the largest fact about that person; `markab_extinct` is true
    # of everybody aboard and would otherwise put the same sentence in three
    # mouths in one room, which is what it did before this line existed.
    sal = PERSONAL["era"] + (0.8 if who != "*" else -0.3)
    # `when` IS A PRODUCTION REFERENCE AND `what` IS THE FACT. Every
    # `ERA_EVENTS` description is `"E7  The Fall of Night -- Nightwatch
    # surfaces aboard; the first armband"`: an episode marker, then what
    # happened in the world. Splitting on `--` and keeping the FIRST half gives
    # a production credit, and the first line that put it in a mouth had a
    # customs officer saying *"You mean since E7 The Fall of Night?"* -- an
    # era-lock failure of the opposite kind to the one this module guards, and
    # a fidelity failure by the era rule. `when` is left as it was because
    # provenance wants the marker; `what` is the half a person can say.
    desc = cos.ERA_EVENTS[ev][1]
    return {"key": "era", "salience": sal,
            "fact": {"event": ev, "who": who,
                     "refugee": sp.role == "refugee",
                     "armband": reg.armband,
                     "when": desc.split("--")[0].strip(),
                     "what": (desc.split("--", 1)[1] if "--" in desc
                              else desc).split(";")[0].strip()},
            "source": f"costume.ERA_EVENTS[{ev!r}] active at {w.era}; {why}"}


TOPICS = (
    ("refusal", _topic_refusal),
    ("era", _topic_era),
    ("port", _topic_port),
    ("news", _topic_news),
    ("beat", _topic_beat),
    ("trade", _topic_trade),
    ("shift", _topic_shift),
    ("meal", _topic_meal),
    ("visa", _topic_visa),
    ("home", _topic_home),
    ("worship", _topic_worship),
)


@dataclass
class _Speaker:
    """A resident plus where they are standing. Topics read this, not two args."""
    npc_id: str
    species: str
    role: str
    place: str
    job: str
    home: str
    eats_at: str
    prays_at: str
    commutes_via: str
    visas: str
    licensed_psi: bool
    name: str


def _speaker(r, place_key: str) -> _Speaker:
    return _Speaker(npc_id=r.npc_id, species=r.species, role=r.role,
                    place=place_key, job=r.job, home=r.home,
                    eats_at=r.eats_at, prays_at=r.prays_at,
                    commutes_via=r.commutes_via, visas=r.visas,
                    licensed_psi=r.licensed_psi, name=r.name)


_QCACHE = {}


def _q(key: str):
    if not key:
        return None
    if key not in _QCACHE:
        try:
            _QCACHE[key] = dr.by_key(key)
        except Exception:                                       # noqa: BLE001
            _QCACHE[key] = None
    return _QCACHE[key]


_VERB = {}


def _verb(token: str) -> str:
    """`interact.verb_of`, imported lazily so this module does not pull `rooms`.

    THE VERB SET IS NOT REPEATED HERE. `interact.py` derives it from
    `rooms.PROP_KIND` and the register's own head nouns and asserts it TOTAL
    and MINIMAL; a second copy in this file would be a fourth vocabulary, which
    is the thing that module exists to prevent.
    """
    if token not in _VERB:
        import interact as it                                   # noqa: PLC0415
        _VERB[token] = it.verb_of(token)
    return _VERB[token]


def rank(speaker, listener: Listener, world: World, reg: Register = None):
    """Every topic that applies, with its salience, strongest first."""
    reg = reg or register(speaker, listener, world)
    out = []
    for _key, fn in TOPICS:
        t = fn(speaker, listener, world, reg)
        if t is not None:
            out.append(t)
    out.sort(key=lambda t: (-t["salience"], t["key"]))
    return out


# The share of the top topic's salience a topic must reach to be in the draw.
# Not 1.00, because a room where everybody says the loudest thing is a room
# with one line in it; and not 0.0, because a refusal or a customs hall running
# at x9.7 must not be beaten by somebody's lunch. At 0.55 the personal topics
# sit in one another's draw and an EVENT -- which scores off a simulation
# number rather than off the floors below -- excludes all of them. INV-271.
DRAW_FLOOR = 0.55


def choose(ranked, npc_id: str):
    """Draw from the top of the ranking by the speaker's own hash.

    Deterministic, salience-weighted, and PER PERSON -- which is what stops two
    people in one room saying the same thing about the same liner.
    """
    if not ranked:
        return None
    top = ranked[0]["salience"]
    pool = [t for t in ranked if t["salience"] >= top * DRAW_FLOOR]
    tot = sum(t["salience"] for t in pool)
    x = _u(npc_id, "topic") * tot
    for t in pool:
        x -= t["salience"]
        if x <= 0:
            return t
    return pool[-1]


# ===========================================================================
# 4.  Phrasing -- three bands, and every brace is a computed value
# ===========================================================================
# THE ONLY INVENTED STRINGS IN THE MODULE, and they are invented the way
# `broadcast.py`'s tannoy lines are: written to the flat civic register of the
# customs board (`reference/01-station-exterior/welcome to babylon 5.webp`,
# authority 1) and carrying no fact of their own. Three per topic, indexed by
# the voice band, so the same fact reaches the player as a formality, a
# statement or a grunt. INV-273.
PHRASE = {
    "port": (
        "The {ship} berthed at {when}. {souls} passengers to be processed.",
        "That's the {ship} in at {when} -- {souls} of them through the hall.",
        "{ship}. {souls}. All morning.",
    ),
    "news": (
        "You will have heard: {text}.",
        "They've been saying it all shift -- {text}.",
        "{text}. That's what they're saying.",
    ),
    "beat": (
        "{sector} ring, {min:.0f} minutes out and back. {on} of us on this "
        "watch.",
        "I walk {sector} ring. {min:.0f} minutes a circuit, {on} on duty.",
        "{sector} ring. {min:.0f} minutes. Move along.",
    ),
    "trade": (
        "My concern is at {where} -- the {counter}, if you have business.",
        "I keep the {counter} at {where}. Come by.",
        "{counter}. {where}. That's me.",
    ),
    "shift": (
        "I am due at {job} -- the watch runs {start} to {end}.",
        "On my way to {job}. {start} to {end}, same as ever.",
        "{job}. {start}. Late already.",
    ),
    "shift_here": (
        "This is my station until {end}. {start} to {end}, every day.",
        "I'm on here till {end}. Started {start}.",
        "On shift. Till {end}.",
    ),
    "meal": (
        "I am taking a meal at {where}; we keep {meals} of them.",
        "Eating. {where}. {meals} a day, and this is one of them.",
        "Eating. {where}.",
    ),
    "home": (
        "I have quarters at {home}.",
        "I'm billeted at {home}.",
        "{home}. Such as it is.",
    ),
    "worship": (
        "I keep the hours at {where}.",
        "I go to {where} when the watch allows it.",
        "{where}. When I can.",
    ),
    # `visa` is banded by STATE as well, below, for the reason `era` is: "my
    # papers are in order" and "I have no papers" are not one sentence.
    "visa": (
        "My status reads {visa}.",
        "Card says {visa}.",
        "{visa}.",
    ),
    "era": (
        "{clause}",
        "{clause}",
        "{clause}",
    ),
}

# The era topic's clause is the one place a phrasing needs to know WHICH event
# fired, because "an entire species died here" and "we have no country" are not
# the same sentence in any register. One row per `_ERA_ROWS` entry, banded.
ERA_PHRASE = {
    ("narn_surrender", "narn"): (
        "I am Narn. That means less than it did; we are guests here now.",
        "There's no Narn to go back to. We're all guests here now.",
        "Narn. What's left of it.",
    ),
    ("narn_surrender", "centauri"): (
        "The Republic's position is much improved, as I am sure you have read.",
        "Good times for the Republic, if you follow the reports.",
        "Republic's up. Read the news.",
    ),
    ("nightwatch_visible", "human"): (
        "One is careful what one says in a corridor now.",
        "Watch what you say out here. That's all I'll tell you.",
        "Not here.",
    ),
    ("markab_extinct", "*"): (
        "The Markab quarter is still sealed. Every one of them, aboard this "
        "station.",
        "Markab quarter's still shut. All of them, right here.",
        "Markab quarter. Sealed. All of them.",
    ),
    ("monastics_resident", "cleric"): (
        "The order has taken permanent residence; we keep the hours here now.",
        "The brothers are here for good now. We keep the hours.",
        "The order's here now.",
    ),
}

# One row per state `resident._visa` can produce. The reader in the room is
# what makes the first two urgent -- LAW-CRIME-DOWNBELOW.md 3.4's "the reason
# lurkers avoid readers" -- and the room's declared interactables are what say
# whether there is one.
VISA_PHRASE = {
    "nostatus": (
        "I have no status on the card. I keep away from the readers.",
        "No status. That's why I don't go near the readers.",
        "No card. Don't ask.",
    ),
    "expired": (
        "My status has lapsed. I am told it is the commonest offence aboard.",
        "Papers ran out. Half the station's the same, they tell me.",
        "Lapsed. So's everyone's.",
    ),
    "sanctuary": (
        "I am here under sanctuary. It is not the same as being welcome.",
        "Sanctuary status. It's not the same as being welcome.",
        "Sanctuary. That's all it is.",
    ),
    "transit": (
        "I hold {visa}; I am not staying.",
        "{visa}. I'm not stopping.",
        "{visa}. Passing through.",
    ),
}

# Downbelow overrides `home`, because "I have quarters at Downbelow" is a
# sentence nobody in `resident.DOWNBELOW_HOMES` would say. The numbers in it
# are `security.SQUAT_M2_PER_PERSON` and the gazetteer's no-post rule.
DOWN_PHRASE = (
    "I sleep below. There is no post down there and no one comes.",
    "Down below. {m2:.0f} square metres and no patrol ever comes down.",
    "Below. Nobody comes down there.",
)

GREET = (
    "Good {word}.",
    "{Word}.",
    "Yes?",
)

# When friction is present but short of a refusal, the greeting is withheld and
# the topic is delivered flat. FACTIONS.md 12's "95% avoidance" rule, in a
# sentence: most of the friction a player meets should be a greeting that did
# not happen.
COLD_GREET = ("", "", "")

FAREWELL_DUE = (
    "I am expected at {next}.",
    "I'm due at {next}.",
    "{next}. Going.",
)
FAREWELL = (
    "Good {word} to you.",
    "Right you are.",
    "",
)


def _fmt(tpl: str, fact: dict, extra: dict = None) -> str:
    d = dict(fact)
    if extra:
        d.update(extra)
    d.setdefault("Word", str(d.get("word", "")).capitalize())
    try:
        return tpl.format(**d)
    except KeyError as e:                                   # pragma: no cover
        raise KeyError(f"phrasing wants {e} which no fact supplies: {tpl!r}")


def phrase(topic: dict, reg: Register, sp: _Speaker,
           world: "World" = None) -> str:
    """One line of speech, from the topic's facts and the speaker's band.

    THE TIER-2 MATRIX IS CONSULTED FIRST AND `PHRASE` IS THE FALLBACK. Before
    DLG-02 this function reached `PHRASE[key][band]` for every speaker on the
    station, which is 39 strings shared by 79 (species x role) cells -- so a
    Drazi dockworker and a human merchant said the same sentence in a
    different band. `cell_draw` returns that cell's OWN phrasing, drawn without
    replacement per (NPC, session) as the annex's anti-repeat rule requires.
    The state-specific tables below still win where they apply: a person
    sleeping in Downbelow, a lapsed card and a named era event are facts about
    the PERSON, and the cell is a fact about the kind of person.
    """
    b = reg.band
    key = topic["key"]
    f = dict(topic.get("fact") or {})
    # TIER 1 FIRST. If this speaker is one of the CAST-02 fifty, they have 75
    # lines of their own and none of them is shared with anybody -- so the
    # cast line wins over the cell, which wins over `PHRASE`. The two guards
    # are the two STATE branches whose facts have a different shape: a person
    # already at their post has no `{job}` and a person sleeping below has no
    # ordinary `{home}`, so those keep the tables written for them.
    row = cast_by_name(sp.name) if sp.name else None
    if row is not None and not (key == "shift" and f.get("here")) \
            and not (key == "home" and f.get("down")):
        t = cast_topic_line(row, key,
                            world.turn if world is not None else 0)
        if t:
            return _fmt(t, f)
    if key == "era":
        row = ERA_PHRASE.get((f["event"], f["who"]))
        if row is None:                                     # pragma: no cover
            raise KeyError(f"no ERA_PHRASE row for {f['event']}/{f['who']}")
        return row[b]
    if key == "home" and f.get("down"):
        return _fmt(DOWN_PHRASE[b], f)
    if key == "visa":
        return _fmt(VISA_PHRASE[f["state"]][b], f)
    if key == "shift" and f.get("here"):
        return _fmt(PHRASE["shift_here"][b], f)
    cell = cell_draw(sp.species, sp.role, sp.npc_id,
                     (world.session if world is not None else ""), key,
                     (world.turn if world is not None else 0))
    if cell:
        return _fmt(cell, f)
    return _fmt(PHRASE[key][b], f)


# ===========================================================================
# 4b.  WHAT YOU SAY BACK -- the player's own voice
# ===========================================================================
# THE HOLE THIS FILLS, MEASURED. `docs/spec/PEOPLE.md` §4: *"a 2,139-line
# module, 57 distinct lines baked on one deck, ZERO PLAYER UTTERANCES"*. The
# owner's session-4d ruling names it in the same breath as the missing HUD.
# Everything above this line is somebody talking AT you.
#
# THE THREE STANCES ARE DLG-05's, AND THEY DIFFER IN WHAT THEY ARE WORTH.
# A conversation whose options are three ways of saying "go on" is a menu, not
# a choice, so each stance is defined by what it can and cannot get:
#
#   ask     -- the QUALITATIVE half of the topic. Always answered.
#   press   -- THE NUMBER THAT DECIDED THE TOPIC'S SALIENCE. `_topic_port`
#              chose the liner because `hall_rate` says x9.7; `_topic_beat`
#              chose the beat because `security.on_duty` says 174. The first
#              line never carries that number. Pressing is how you get it --
#              AND IT CAN BE REFUSED.
#   let_go  -- nothing, and the farewell. You do not learn the number.
#
# WHETHER A PRESS WORKS IS THE REGISTER, NOT A DIE -- AND IT IS A COMPARISON
# OF TWO NUMBERS THIS MODULE ALREADY COMPUTES, with no third constant at all:
#
#     they yield when they are MORE WILLING than they are CLIPPED,
#     `reg.warmth > reg.terseness`.
#
# Both sides are already derived. `warmth` is `friction.SEVERITY`'s separation
# ladder inverted -- the same number the crowd keeps its distance by -- and
# `terseness` is the role row plus the species delta. Nothing here to tune and
# therefore nothing to argue with, which is `deck.py --degeneracy`'s argument
# for a hash over a threshold.
#
# THE FIRST VERSION WAS A THRESHOLD AND IT MEASURED AS A SLOT MACHINE.
# `warmth >= 0.75 AND terseness <= median(_ROLE_REGISTER)` looked principled --
# both halves derived -- and ANDing two independent cuts is multiplicative: on
# the shipped deck's own 21-person cast it yielded 1 TIME IN 21, and on the
# 73-person customs cast 16 in 73. A stance that pays out 5% of the time is not
# a choice a player makes, it is one they stop taking. The comparison above
# lands the same fiction (a Narn dock worker at this datum gives you nothing; a
# Centauri merchant gives you the number; Kosh, at 1.00 against 1.00, never
# yields to anybody) without either constant. INV-299.
#
# WHAT IS INVENTED HERE, PLAINLY: the phrasings, exactly as `PHRASE`'s are --
# authority 5, flat civic register, and every brace is a value the station
# computed. What is NOT invented is which fact each row names: `PRESSED[k]`
# names the input to `_topic_<k>`'s own salience expression, so a phrasing
# cannot drift from the reason the topic won. INV-298 and INV-299.

STANCES = ("ask", "press", "let_go")

# The friction floor `speak` already uses for the greeting, named once so the
# press and the hello agree by construction rather than by two literals.
WARM_FLOOR = 0.75


def yields_to_press(reg: Register) -> bool:
    """Will this person give up the number if you push? Nothing random here."""
    return reg.warmth > reg.terseness


# What the PLAYER says. ONE VOICE, NOT THREE BANDS: the player has no role row
# and no species row -- `Listener` carries species, role and psi for the
# FRICTION model and nothing in this repository decides how the player speaks.
# Banding them would be inventing a register for a person the simulation does
# not describe, which is precisely the unmarked invention hard rule 1 forbids.
#
# Every line names a value out of the topic's own `fact`, for the same reason
# the NPC's do: a line any NPC could hear is a line that has not been earned.
SAY = {
    # THE ELEVENTH ROW, AND IT IS THE ONE THAT WAS MISSING. `TOPICS` has
    # eleven entries and `SAY` had ten: `refusal` returns from `speak` before
    # any menu is built, so the player met the one exchange in the module they
    # could not answer -- a silence with no reply key. DLG-05's arithmetic is
    # 11 x 3 and it was 10 x 3. The three stances still mean what they mean:
    # ask gets nothing back (they said nothing), press gets the deflection,
    # let-go ends it. INV-697.
    "refusal": ("That was not an answer. I would still like one.",
                "You can look at me while you refuse me.",
                "Understood. I will not push it."),
    "port":    ("The {ship} -- were you expecting her?",
                "{souls} through one hall. How is that going?",
                "I'll leave you to the {ship}."),
    "news":    ("You put much stock in {surface}?",
                "How much of that is running in here right now?",
                "I've heard enough of it."),
    "beat":    ("{min:.0f} minutes a lap. Do you walk it alone?",
                "How many of the {on} are actually out on the ring?",
                "I won't hold up your watch."),
    "trade":   ("The {counter}. What do you keep behind it?",
                "What is {where} good for, besides the {counter}?",
                "Another time, then."),
    "shift":   ("{start} to {end}. Every day?",
                "How do you get across to {job}?",
                "Don't let me make you late."),
    "meal":    ("{meals} a day. Is that your people's count or the station's?",
                "Do you eat at {where} by choice?",
                "Enjoy it."),
    "home":    ("{home}. Have you been there long?",
                "What is it actually like where you sleep?",
                "It's not my business."),
    "worship": ("You keep the hours at {where}?",
                "Does the watch actually let you go?",
                "I'll not interrupt."),
    "visa":    ("Your card reads {visa}?",
                "Is that a problem in a room like this one?",
                "I didn't ask."),
    "era":     ("{What}. Is that how it looks from where you stand?",
                "What did that actually change for you?",
                "We needn't talk about it."),
}


# ===========================================================================
# 4c.  THE REST OF DLG-05 -- 152 player lines, and what each family is FOR
# ===========================================================================
#
# THE ROW'S ARITHMETIC, AND EVERY MULTIPLICAND IS A NUMBER THIS REPOSITORY
# ALREADY HOLDS rather than a figure chosen to make a total come out:
#
#   11 topics x 3 stances                          = 33   (`TOPICS`, `STANCES`)
#   openers / closers                              =  8
#   12 player roles x 8 shift verbs                = 96   (ROLE-01..12 x
#                                                          `interact.VERBS`)
#   SHOW-PAPERS / BUY-SELL / refusal               = 15
#                                                   ----
#                                                    152
#
# THE 96 ARE THE PART THAT IS NOT DECORATION. `docs/spec/PEOPLE.md` ROLE-01..12
# are the twelve jobs a PLAYER can hold, and `interact.VERBS` is the whole verb
# set the station is built around -- eight verbs, and `tread` deliberately has
# no prompt. So a work line is what the player says while doing one job with
# one verb, and the grid is the two lists multiplied rather than a list
# somebody wrote down. When a thirteenth role is specified or a ninth verb is
# added, the hole is a missing key and the selftest names it; that is the
# "a fix applied to a table entry and not to the table" defect closed in
# advance.
#
# WHAT IS INVENTED: the phrasings, authority 5, exactly as `PHRASE` and
# `broadcast.py`'s tannoy lines are. The player has ONE register -- no role
# row, no species row -- for the reason `SAY` already gives: nothing in this
# repository describes how the player speaks, and banding them would be
# inventing a person the simulation does not have. INV-694.

# The twelve. Keys are this module's; `_selftest` asserts they are exactly the
# ROLE-01..12 headings in the annex, so the list cannot quietly drift from the
# spec that defines it.
PLAYER_ROLES = ("customs_officer", "security_deputy", "dockworker",
                "bartender", "stall_trader", "medlab_assistant",
                "maintenance_tech", "lurker", "porter", "info_broker",
                "diplomat_aide", "starfury_pilot")

# The eight verbs, in `interact.VERBS` order. Named here rather than imported
# at module scope because `interact` imports `directory` and this module is
# loaded by the deck baker; the selftest does the import and asserts equality.
SHIFT_VERBS = ("open", "operate", "read", "sit", "rest", "store", "serve",
               "tread")

# 12 x 8. Every line is the player DOING the job, not describing it -- ROLE-05's
# acceptance shape is a Nightwatch questioning at the player's own stall, which
# only works if the player has a stall voice to be questioned in.
WORK_LINE = {
    ("customs_officer", "open"): "Hall's open. Single file, cards out.",
    ("customs_officer", "operate"): "Running your card. Look at the plate.",
    ("customs_officer", "read"): "Card says transit. Say where, and say when.",
    ("customs_officer", "sit"): "Take the chair. This goes faster sitting.",
    ("customs_officer", "rest"): "Twenty minutes off the line. Wake me if the "
                                 "liner comes in early.",
    ("customs_officer", "store"): "That goes in the bond locker until somebody "
                                  "senior signs for it.",
    ("customs_officer", "serve"): "Next. Card and declaration together, please.",
    ("customs_officer", "tread"): "Stand behind the line. The yellow one, not "
                                  "the edge of the mat.",

    ("security_deputy", "open"): "Security. I am opening this and you are "
                                 "standing where I can see you.",
    ("security_deputy", "operate"): "Logging the caution. Your name goes on it "
                                    "either way.",
    ("security_deputy", "read"): "Identicard. And I will read it properly, so "
                                 "do not walk off halfway.",
    ("security_deputy", "sit"): "Sit down. You are not under arrest and you "
                                "are not leaving yet either.",
    ("security_deputy", "rest"): "Post relief. I am on the bench for ten and "
                                 "then I walk the ring again.",
    ("security_deputy", "store"): "Into the property locker, sealed, and you "
                                  "get the tag.",
    ("security_deputy", "serve"): "Station house. What is it, and is anybody "
                                  "hurt?",
    ("security_deputy", "tread"): "Mind the step down. People come off that "
                                  "lip every watch.",

    ("dockworker", "open"): "Hatch is coming up. Stand clear of the swing.",
    ("dockworker", "operate"): "Taking the grapple in. Call it if she drifts.",
    ("dockworker", "read"): "Manifest says forty-one. I have counted "
                            "thirty-nine twice.",
    ("dockworker", "sit"): "Sitting on the gantry for five. My back has done "
                           "its shift already.",
    ("dockworker", "rest"): "That is me finished. Whoever has the next hull "
                            "can have my gloves too.",
    ("dockworker", "store"): "Stow it forward and lash it. She rolls on the "
                             "way out.",
    ("dockworker", "serve"): "Gang boss is over there. I only carry things.",
    ("dockworker", "tread"): "Walk the yellow, not the deck plate. That plate "
                             "is not fixed down.",

    ("bartender", "open"): "We are open. Mind the step and mind the Drazi.",
    ("bartender", "operate"): "Working the taps. Give it a moment, the line is "
                              "cold.",
    ("bartender", "read"): "Slate is behind me. If it is chalked out, it is "
                           "out.",
    ("bartender", "sit"): "Take a stool. The far end is quieter if you want "
                          "quiet.",
    ("bartender", "rest"): "Cellar for ten minutes. Shout if anybody starts "
                           "anything.",
    ("bartender", "store"): "That goes under the counter and it stays under "
                            "the counter.",
    ("bartender", "serve"): "What will it be, and are you paying now or "
                            "running a slate?",
    ("bartender", "tread"): "Watch your footing there. Somebody went over "
                            "earlier and I have not had the mop out.",

    ("stall_trader", "open"): "Stall is up. Everything on the front cloth is "
                              "priced as marked.",
    ("stall_trader", "operate"): "Weighing it out. You can watch the scale, I "
                                 "do not mind.",
    ("stall_trader", "read"): "That label is the origin, not the grade. The "
                              "grade is the second line.",
    ("stall_trader", "sit"): "Sit on the crate if you like. I am not going "
                             "anywhere for an hour.",
    ("stall_trader", "rest"): "Shutting the cloth for a bit. The noon crowd "
                              "has gone through.",
    ("stall_trader", "store"): "Back in the case. It does not keep in this "
                               "air.",
    ("stall_trader", "serve"): "You are looking at it. Tell me what you want "
                               "and I will tell you what it costs.",
    ("stall_trader", "tread"): "Round the front of the cloth, not over it. "
                               "People have.",

    ("medlab_assistant", "open"): "Curtain back. Say your name before I touch "
                                  "anything.",
    ("medlab_assistant", "operate"): "Running the scanner. It is cold and it "
                                     "takes eleven seconds.",
    ("medlab_assistant", "read"): "Chart says you were in here two weeks ago "
                                  "with the same thing.",
    ("medlab_assistant", "sit"): "Sit up here and let your legs hang. Do not "
                                 "lock your knees.",
    ("medlab_assistant", "rest"): "Lie back. You are staying until the charge "
                                  "physician has seen you.",
    ("medlab_assistant", "store"): "Into the sharps bin, and it is signed for "
                                   "in the log.",
    ("medlab_assistant", "serve"): "Medlab. Is it an injury, a fever, or "
                                   "paperwork?",
    ("medlab_assistant", "tread"): "Mind the cable run. That is oxygen, and it "
                                   "matters.",

    ("maintenance_tech", "open"): "Panel off. Do not put your hand in until I "
                                  "say the bus is dead.",
    ("maintenance_tech", "operate"): "Cycling it. If it trips again the fault "
                                     "is upstream of us.",
    ("maintenance_tech", "read"): "Gauge is reading low and it has been "
                                  "reading low since the last shift signed it "
                                  "off.",
    ("maintenance_tech", "sit"): "Sitting in the crawl to do this properly. It "
                                 "is a two-hour job done badly standing.",
    ("maintenance_tech", "rest"): "Ten minutes with my back against something "
                                  "that is not vibrating.",
    ("maintenance_tech", "store"): "Tools back in the roll and counted. You do "
                                   "not leave a spanner in a duct.",
    ("maintenance_tech", "serve"): "Works order desk. Give me the deck and the "
                                   "frame number, not the room name.",
    ("maintenance_tech", "tread"): "That grating is lifted. Step over, not on.",

    ("lurker", "open"): "It was already open. That is the whole of my story "
                        "and I am sticking to it.",
    ("lurker", "operate"): "I have seen this worked a hundred times. Nobody "
                           "ever showed me.",
    ("lurker", "read"): "Notice says the queue starts at five. It never "
                        "starts at five.",
    ("lurker", "sit"): "I will sit where the warm air comes up. Everyone does.",
    ("lurker", "rest"): "This is my patch. Two metres of it, and nobody comes "
                        "down here anyway.",
    ("lurker", "store"): "Everything I own goes under my coat when I move. "
                         "That is the system.",
    ("lurker", "serve"): "I am not behind a counter. I am the one on the wrong "
                         "side of it.",
    ("lurker", "tread"): "Keep to the dry side. That run has been leaking "
                         "since before I came aboard.",

    ("porter", "open"): "Delivery. I will hold the leaf, you take the weight.",
    ("porter", "operate"): "Calling the lift. It is four minutes if it is at "
                           "the drum end.",
    ("porter", "read"): "Docket says Blue seven and there is no Blue seven on "
                        "this ring.",
    ("porter", "sit"): "Two minutes off my feet and then I have six more of "
                       "these.",
    ("porter", "rest"): "That is the round done. Eleven kilometres of ring, "
                        "same as yesterday.",
    ("porter", "store"): "Signed, dated, and into the rack. If it walks it is "
                         "not on me.",
    ("porter", "serve"): "Parcel counter. Name it is under, and something with "
                         "your face on it.",
    ("porter", "tread"): "Give me the corridor. I cannot see past this and I "
                         "am not stopping.",

    ("info_broker", "open"): "Come in and shut it behind you. That is half of "
                             "what you are paying for.",
    ("info_broker", "operate"): "Pulling the berth-map. Public record, and "
                                "nobody reads it but me.",
    ("info_broker", "read"): "Read it here. It does not leave the desk and it "
                             "does not get copied.",
    ("info_broker", "sit"): "Sit. People who stand up are people who are about "
                            "to lie to me.",
    ("info_broker", "rest"): "Desk is shut. Come back when the night broker is "
                             "on and pay his rates.",
    ("info_broker", "store"): "It goes in the safe and it stays there until "
                              "one of us needs it more.",
    ("info_broker", "serve"): "I sell what is true and what is useful. They "
                              "are different prices.",
    ("info_broker", "tread"): "Take the long way round the gallery. The short "
                              "way has a post on it.",

    ("diplomat_aide", "open"): "The wing is open to the delegation only. I can "
                               "take a message for anyone else.",
    ("diplomat_aide", "operate"): "Logging the appointment. It will be "
                                  "acknowledged within the day.",
    ("diplomat_aide", "read"): "The note is in three languages and it says the "
                               "same thing in none of them.",
    ("diplomat_aide", "sit"): "Please sit. The ambassador is running twenty "
                              "minutes behind and always will be.",
    ("diplomat_aide", "rest"): "The reception is over. I am going to stand "
                               "somewhere nobody is watching my face.",
    ("diplomat_aide", "store"): "Sealed and filed under the mission, not under "
                                "the station.",
    ("diplomat_aide", "serve"): "The mission is receiving. State your business "
                                "and your standing, in that order.",
    ("diplomat_aide", "tread"): "Please keep to the carpet. The rest of the "
                                "floor is not ours.",

    ("starfury_pilot", "open"): "Canopy up. Do not touch the rail, it is still "
                                "hot from the launch.",
    ("starfury_pilot", "operate"): "Running the pre-flight. Forty-one items "
                                   "and I do all forty-one.",
    ("starfury_pilot", "read"): "Board is green except for the aft attitude "
                                "quad, and that has been amber all week.",
    ("starfury_pilot", "sit"): "Strapping in. Five points, and the harness "
                               "gets checked by somebody who is not me.",
    ("starfury_pilot", "rest"): "Down and safed. I have eleven hours before I "
                                "am on the board again.",
    ("starfury_pilot", "store"): "Helmet in the rack with my name on it. Never "
                                 "anybody else's rack.",
    ("starfury_pilot", "serve"): "Cobra bay. If you are not on the launch "
                                 "roster you should not be on this gallery.",
    ("starfury_pilot", "tread"): "Walk the catwalk, hold the rail. There is no "
                                 "floor under that grating, there is a bay.",
}

# The openers and closers -- four of each. These are the only player lines that
# name nothing about the person in front of them, because that is what an
# opener IS: the thing you say before you know anything.
PLAYER_OPEN = (
    "Have you got a moment?",
    "Sorry -- can I ask you something?",
    "You look like you know this deck.",
    "I will not keep you.",
)
PLAYER_CLOSE = (
    "Thanks. That helps.",
    "I will let you get on.",
    "Good watch to you.",
    "If I need to find you again, is it here?",
)

# SHOW-PAPERS: what the player says when a card is demanded. Five, because the
# station has five things a card can be -- ROLE-01's own ladder: in order,
# lapsed, absent, sanctuary, and the refusal to produce it at all.
PAPERS = (
    "Here. Transit visa, and the date is on the second line.",
    "It has lapsed. I know it has lapsed, and I know how many of us that is.",
    "I do not have a card. That is the answer whether you like it or not.",
    "Sanctuary status. It is not the same as being welcome and we both know "
    "it.",
    "You can read it when somebody senior to you asks me for it.",
)

# BUY / SELL: the trade verbs a player uses across a counter. Five, matching
# what a counter can actually be asked -- price, haggle, buy, sell, decline.
BUY_SELL = (
    "What do you want for it?",
    "That is a liner-day price and there is no liner in.",
    "I will take it. Cash, and no docket.",
    "I am selling, not buying. Tell me what it is worth to you.",
    "Not at that. I will come back when the shelf is fuller.",
)

# REFUSAL: what the player says to somebody who has already turned away.
# FACTIONS.md 12's "95% avoidance" from the other side -- the player is allowed
# to be the one who lets it go.
PLAYER_REFUSAL = (
    "I am not looking for trouble. I am looking for an answer.",
    "You have not said a word and you have said plenty.",
    "Fine. I will ask somebody who will.",
    "Whatever that is about, it is not about me.",
    "I will stand here until you decide I am not worth the trouble.",
)


def player_lines() -> dict:
    """DLG-05's census, computed. The harness reads this, not a hand count."""
    return {
        "topics": {t for row in SAY.values() for t in row},
        "openers": set(PLAYER_OPEN) | set(PLAYER_CLOSE),
        "work": set(WORK_LINE.values()),
        "papers": set(PAPERS) | set(BUY_SELL) | set(PLAYER_REFUSAL),
    }


def work_line(role: str, verb: str) -> str:
    """What the player says doing `verb` in `role`. The shipped-path reader."""
    return WORK_LINE[(role, verb)]


# ===========================================================================
# 4e.  DLG-02 -- THE TIER-2 VOICE MATRIX
# ===========================================================================
#
# WHAT WAS ACTUALLY WRONG, AND IT WAS STRUCTURAL RATHER THAN A SHORTFALL.
# `_ROLE_REGISTER` (19 rows) and `_SPECIES_VOICE` (15 rows) MODULATE a shared
# phrasing -- they pick which of three bands a shared string is delivered in --
# so 19 x 15 does not multiply into 285 voices, it selects one of 3. Every
# speaker on the station drew from the same 39 strings. `spec_harness/dlg.py`
# said so in as many words and it was right: *"19 role registers x 15 species
# voices MODULATE them, they do not multiply them"*.
#
# THE FIX IS COMPOSITION, AND THE TWO HALVES ARE OWNED BY DIFFERENT TABLES:
#
#   ROLE_CLAUSE[role][topic]   -- WHAT this job says about this subject. 19 x
#                                 11 = 209. It carries the FACT: the same
#                                 braces `PHRASE` uses, filled by the topic
#                                 function, so a matrix line still names
#                                 today's liner and this officer's own beat.
#   SPECIES_FRAME[species]     -- HOW that sentence leaves this mouth. 15 x 2
#                                 = 30 frames, `{say}` being the clause.
#
# so a cell is 11 topics x 2 frames = 22 lines, plus 4 greetings and 4
# farewells built the same way (a species stem plus a role tag) = **30 per
# cell, 79 cells, 2,370 distinct lines** -- which is DLG-02's arithmetic, and
# the distinctness is BY CONSTRUCTION rather than by discipline: every line
# contains a string only that role owns and a string only that species owns,
# so two cells cannot collide. `_selftest` asserts it over all 79 rather than
# trusting the argument.
#
# WHY NOT 79 x 30 HAND-WRITTEN LINES. Because that is 2,370 strings nobody
# will ever re-read, and because the failure it invites is the one this project
# already has a gate for: a table whose entries drift apart. Composition means
# a new species is 2 frames and a new role is 11 clauses, and the matrix is
# complete the moment they exist -- `_selftest` fails on the hole otherwise.
#
# THE SPECIES CONSTRAINTS THE ANNEX NAMES ARE CARRIED HERE AND ARE CHECKABLE:
# pak'ma'ra speak through a translator (every frame says so), Gaim only through
# an interpreter, Brakiri reckon by a night clock, and the Minbari frames carry
# a CASTE ADDRESS -- `MINBARI_CASTE` maps each role to the caste that holds it,
# and the greeting names it. The Brakiri daypart inversion was already built in
# `daypart()` and is untouched. Authority 5 for every phrasing; the register is
# the customs board's, as everywhere else in this module. INV-698.

# THE CASTE A ROLE BELONGS TO. Minbari society is three castes and the annex
# asks for the address forms inside the Minbari cells; the mapping is the one
# FACTIONS.md 8.1 implies -- the religious caste is the bulk aboard, the
# warrior caste holds the martial offices, the worker caste builds and carries.
MINBARI_CASTE = {
    "command": "warrior", "security": "warrior", "customs": "warrior",
    "traffic": "worker", "medical": "religious", "diplomat": "religious",
    "envoy": "religious", "cleric": "religious", "financier": "worker",
    "merchant": "worker", "service": "worker", "engineer": "worker",
    "industrial": "worker", "dockworker": "worker", "waste": "worker",
    "hydroponics": "worker", "visitor": "religious", "refugee": "religious",
    "lurker": "worker",
}
CASTE_ADDRESS = {"religious": "in the light", "warrior": "in the line",
                 "worker": "at the work"}

# 19 x 11. Each clause uses ONLY the brace keys the topic's own fact supplies
# -- the same keys `PHRASE` uses -- so a clause cannot ask for a value the
# station did not compute. `_selftest` renders all 209 against the topic facts.
ROLE_CLAUSE = {
    "command": {
        "port": "The {ship} is on my board at {when}. {souls} souls, and every "
                "one of them is my responsibility until they clear.",
        "news": "You will have read it: {text}. I am not going to comment on "
                "it in a corridor.",
        "beat": "{sector} ring is a {min:.0f} minute circuit and I have {on} "
                "to cover it with. Do the arithmetic yourself.",
        "trade": "The {counter} at {where} is licensed and it is inspected. "
                 "That is the whole of my interest in it.",
        "shift": "I am wanted at {job}. The watch runs {start} to {end} and it "
                 "does not run late.",
        "meal": "I take {meals} at {where} because the day allows for {meals} "
                "and no more.",
        "home": "Quarters at {home}. I sleep where the board can reach me.",
        "worship": "{where}, when the duty roster permits. It generally does "
                   "not.",
        "visa": "{visa}. Mine is the least interesting card on this deck.",
        "era": "I have read the order four times. Command is what you do when "
               "the order does not cover it.",
        "refusal": "turns squarely away and does not look back",
    },
    "security": {
        "port": "{ship}, {when}. {souls} through the hall and every one a "
                "chance for somebody to try something.",
        "news": "{text}. I hear it on the post four times a watch.",
        "beat": "{sector} ring. {min:.0f} minutes a lap, {on} of us on the "
                "watch. Move along, please.",
        "trade": "The {counter} at {where} has had no complaint against it "
                 "this quarter. Keep it that way.",
        "shift": "{job} at {start}. Off at {end}, in theory.",
        "meal": "{meals} a day, at {where}, standing up.",
        "home": "{home}. Ten minutes from the post if I run.",
        "worship": "{where}. The watch does not always allow it.",
        "visa": "{visa}. And yes, I do check my own.",
        "era": "One in three of the officers I sign the roster for is wearing "
               "something I did not issue.",
        "refusal": "puts a hand on the belt and says nothing at all",
    },
    "customs": {
        "port": "The {ship} berthed {when} and {souls} of them are queueing "
                "at my positions as we speak.",
        "news": "{text}. It changes nothing at the desk and everything behind "
                "it.",
        "beat": "The hall is not a beat. {sector} ring has {on} on it and none "
                "of them stand in a queue for {min:.0f} minutes at a time.",
        "trade": "The {counter} at {where} clears through this hall like "
                 "everyone else.",
        "shift": "{job}, {start} to {end}. The queue does not know about the "
                 "end.",
        "meal": "{meals} at {where}. One of them is eaten at the desk.",
        "home": "{home}, and I am grateful for a door that shuts.",
        "worship": "{where}. It is on my way, which is the only reason I go.",
        "visa": "{visa}. I read three hundred of these a day and I still read "
                "mine.",
        "era": "The forms changed and nobody sent a note explaining which "
               "authority changed them.",
        "refusal": "returns to the queue and calls the next person forward",
    },
    "traffic": {
        "port": "{ship}. Berthed {when}. {souls}. That is the whole call.",
        "news": "{text}. Not my board.",
        "beat": "{sector}. {min:.0f}. {on}. Ask security.",
        "trade": "{counter}, {where}. Cargo desk, not mine.",
        "shift": "{job}. {start}. {end}.",
        "meal": "{where}. {meals}. Between hulls.",
        "home": "{home}. Close to the bays, which is the point.",
        "worship": "{where}, off watch.",
        "visa": "{visa}. Filed.",
        "era": "The traffic does not care what the news says. It arrives "
               "either way.",
        "refusal": "keys the headset and turns to the board",
    },
    "medical": {
        "port": "The {ship} came in at {when} with {souls} aboard, and I will "
                "see four of them before the watch is out.",
        "news": "{text}. What that means down here is that people stop coming "
                "in until they are much worse.",
        "beat": "{sector} ring, {min:.0f} minutes -- I know it because that is "
                "how long it takes {on} officers to bring somebody up to me.",
        "trade": "The {counter} at {where} sells things I have to explain "
                 "afterwards.",
        "shift": "I am due at {job}. {start} to {end}, and then whatever comes "
                 "through the door at {end}.",
        "meal": "{meals} at {where}, and I recommend the same to you.",
        "home": "{home}. I am there for six hours of the twenty-four.",
        "worship": "{where}. It helps, and I am not going to defend that.",
        "visa": "{visa}. Status has never once changed what I treat.",
        "era": "I have signed more certificates this year than in the four "
               "before it, and none of them said why.",
        "refusal": "steps back behind the curtain and draws it",
    },
    "diplomat": {
        "port": "The {ship} arrived at {when}. {souls} passengers, of whom I "
                "am told two are worth meeting.",
        "news": "{text}. One says nothing about such matters in a public "
                "corridor, and one says a great deal in private.",
        "beat": "{sector} ring is patrolled by {on} officers on a {min:.0f} "
                "minute circuit. I have made it my business to know.",
        "trade": "The {counter} at {where}. A mission runs on small "
                 "courtesies, and small courtesies are bought.",
        "shift": "I am expected at {job} between {start} and {end}. Ceremony "
                 "is the work.",
        "meal": "{meals} at {where}, and the seating is the meeting.",
        "home": "{home}. A residence is a statement; mine is a modest one.",
        "worship": "{where}. Observance is noticed, which is reason enough.",
        "visa": "{visa}, and it opens doors this station does not know it has.",
        "era": "Everything is now said twice: once for the room and once for "
               "the record.",
        "refusal": "inclines the head with perfect courtesy and withdraws",
    },
    "envoy": {
        "port": "The {ship}. {when}. {souls}.",
        "news": "{text}.",
        "beat": "{sector}. {min:.0f}. {on}.",
        "trade": "{counter}. {where}.",
        "shift": "{job}. {start}. {end}.",
        "meal": "{where}. If it must be.",
        "home": "{home}. For now.",
        "worship": "{where}.",
        "visa": "{visa}.",
        "era": "It has already happened.",
        "refusal": "does not move, and the moment passes",
    },
    "cleric": {
        "port": "The {ship} came in at {when}. {souls} arrivals, and some of "
                "them will find their way to us before the week is out.",
        "news": "{text}. We do not read the screens at the hours; we read them "
                "afterwards.",
        "beat": "{sector} ring, {min:.0f} minutes, {on} officers. We walk it "
                "too, only slower and for another reason.",
        "trade": "The {counter} at {where} gives what it can spare, which is "
                 "more than most.",
        "shift": "The hours are kept at {job}, {start} and again at {end}.",
        "meal": "{meals} at {where}, and the first of them in silence.",
        "home": "{home}. The order asks for little and is given less.",
        "worship": "{where}. It is not somewhere I go; it is what I am for.",
        "visa": "{visa}. The order stands surety for those who have none.",
        "era": "People who never came before are coming now, and they do not "
               "say why, and we do not ask.",
        "refusal": "makes the sign of the order and turns to the lamps",
    },
    "financier": {
        "port": "The {ship} at {when} with {souls} aboard is four hundred "
                "settlements before the close of business.",
        "news": "{text}. The market read it an hour before you did.",
        "beat": "{sector} ring, {on} officers, {min:.0f} minutes. Insurance "
                "prices that circuit, and it prices it badly.",
        "trade": "The {counter} at {where} banks with us, or it banks nowhere.",
        "shift": "{job}, {start} to {end}. The hours are rigid on a station "
                 "with no day, which is the joke.",
        "meal": "{meals}. {where}. Accounts do not close for lunch.",
        "home": "{home}, and the rent is the second largest line in my month.",
        "worship": "{where}. It is good for the standing.",
        "visa": "{visa}, renewed annually, and it costs what it costs.",
        "era": "Every emergency measure is a clause somebody has to price. "
               "I am somebody.",
        "refusal": "closes the ledger deliberately and waits for you to leave",
    },
    "merchant": {
        "port": "The {ship} docked at {when} -- {souls} of them, and by "
                "evening half will have walked past my front.",
        "news": "{text}, and I will tell you what it does to the price of "
                "everything on this cloth.",
        "beat": "{sector} ring, {min:.0f} minutes, {on} officers. Between "
                "circuits is when things go missing.",
        "trade": "The {counter} is mine, at {where}. Come and look properly, "
                 "there is no charge for looking.",
        "shift": "I open at {start} and I am still there at {end}, which is "
                 "not a shift, it is a life.",
        "meal": "{meals} a day at {where}, eaten behind the counter.",
        "home": "{home}. Two rooms, and one of them is stock.",
        "worship": "{where}, on the days trade allows.",
        "visa": "{visa}. A trading licence is a different card and it costs "
                "more.",
        "era": "My suppliers are on the wrong side of somebody's line now and "
               "nobody will tell me whose.",
        "refusal": "goes back to arranging the front of the stall",
    },
    "service": {
        "port": "The {ship} in at {when}. {souls}. We will be three deep at "
                "the counter by twenty hundred.",
        "news": "{text}. It gets argued about in here every single night.",
        "beat": "{sector} ring, {min:.0f} minutes. {on} on the watch and two "
                "of them drink in here off duty.",
        "trade": "The {counter} at {where} is where I am, most hours you would "
                 "want me.",
        "shift": "{job} from {start}. I lock up at {end} and I clean until "
                 "somebody makes me stop.",
        "meal": "{meals} at {where}, standing at the end of the bar.",
        "home": "{home}, and I sleep through the shift change like the dead.",
        "worship": "{where}. Sunday mornings are the only quiet I get.",
        "visa": "{visa}. The licence matters more than the visa in my trade.",
        "era": "People say things in here they would not say in a corridor, "
               "and lately they have stopped.",
        "refusal": "wipes the counter down and moves to the far end of it",
    },
    "engineer": {
        "port": "The {ship} at {when}. {souls} aboard, and her grapple will be "
                "on my works list by morning.",
        "news": "{text}. It will come down to us as a change to a procedure "
                "and no explanation.",
        "beat": "{sector} ring is {min:.0f} minutes if you are walking it. It "
                "is forty if you are pulling a cable down it.",
        "trade": "The {counter} at {where} sells the only decent gasket on "
                 "this ring.",
        "shift": "{job}, {start} to {end}, and then whatever breaks at {end}.",
        "meal": "{meals} at {where}. Out of a tin, mostly.",
        "home": "{home}. It is loud, but everything here is loud.",
        "worship": "{where}, if the plant behaves.",
        "visa": "{visa}. Trade certification is the card that actually feeds "
                "me.",
        "era": "Nobody tells the shop floor anything. We work out what has "
               "happened from what we are suddenly not allowed to order.",
        "refusal": "picks the panel back up and goes on working",
    },
    "industrial": {
        "port": "{ship}, {when}, {souls}. Means a run for us tomorrow.",
        "news": "{text}. Same as ever.",
        "beat": "{sector} ring, {min:.0f} minutes. {on} of them. None of them "
                "come down our end.",
        "trade": "{counter} at {where}. I buy there when I have to.",
        "shift": "{job}. {start} to {end}. Three shifts round the clock and "
                 "mine is this one.",
        "meal": "{meals} at {where}. Twenty minutes.",
        "home": "{home}. Ninety decks of us stacked up.",
        "worship": "{where}. Not often.",
        "visa": "{visa}. Never been asked for it in Grey.",
        "era": "The line runs whatever happens. That is the one thing you can "
               "say for it.",
        "refusal": "shoulders past and keeps walking",
    },
    "dockworker": {
        "port": "{ship}. {when}. {souls}. Forty-one crates and the manifest "
                "says thirty-nine.",
        "news": "{text}. Don't care.",
        "beat": "{sector}. {min:.0f} minutes. {on} of them, and not one down a "
                "bay when you want one.",
        "trade": "{counter}. {where}. That's the one.",
        "shift": "{job}. {start}. Off at {end} and not a minute over.",
        "meal": "{where}. {meals}. Fast.",
        "home": "{home}. Bunk, locker, done.",
        "worship": "{where}. Once a year, if that.",
        "visa": "{visa}. Guild card's the one that counts.",
        "era": "They will find a way to make it our fault. They always do.",
        "refusal": "spits on the deck and turns back to the gang",
    },
    "waste": {
        "port": "{ship} at {when}. {souls} aboard, and every one of them "
                "produces two kilos a day for me.",
        "news": "{text}. Nobody down at the plant has said a word about it.",
        "beat": "{sector} ring, {min:.0f} minutes, {on} officers -- who do not "
                "come below the plant deck at all.",
        "trade": "The {counter} at {where}. Half of what they sell comes back "
                 "through me within the month.",
        "shift": "{job}, {start} to {end}. It never stops, so neither do we.",
        "meal": "{meals} at {where}. Washed first.",
        "home": "{home}. Close to the plant, and you get used to it.",
        "worship": "{where}. Nobody minds where I have come from there.",
        "visa": "{visa}. Nobody checks it in the reclamation levels.",
        "era": "Whatever happens up there, it comes down to us in the end, "
               "and it always has.",
        "refusal": "pulls the mask back up and goes on with it",
    },
    "hydroponics": {
        "port": "The {ship} at {when}. {souls} more mouths, and the beds do "
                "not grow any faster for it.",
        "news": "{text}. It will be a shortage in six weeks, whatever it is.",
        "beat": "{sector} ring, {min:.0f} minutes, {on} officers. None of "
                "them can tell a seedling from a weed.",
        "trade": "The {counter} at {where} sells what we cut this morning.",
        "shift": "{job}, {start} to {end}. An agricultural shift starts before "
                 "the station wakes up.",
        "meal": "{meals} at {where}, and most of it came off my own beds.",
        "home": "{home}. It smells of the beds and I have stopped noticing.",
        "worship": "{where}, after the cut.",
        "visa": "{visa}. Agricultural certification, renewed each season.",
        "era": "Every one of these leaves the same mark: an order to plant "
               "more of what stores and less of what tastes of anything.",
        "refusal": "bends back to the tray and does not straighten up",
    },
    "visitor": {
        "port": "I came in on the {ship} at {when}, one of {souls}, and I am "
                "still finding my way about.",
        "news": "{text}. I have only just arrived; I do not know what to make "
                "of it.",
        "beat": "{sector} ring takes {min:.0f} minutes to walk, they tell me. "
                "{on} officers on it. It seems a great many.",
        "trade": "The {counter} at {where} was recommended to me. I have no "
                 "idea by whom.",
        "shift": "I am not on a shift. I am meant to be at {job} between "
                 "{start} and {end} and I am not sure why.",
        "meal": "{meals} at {where}, since I have nowhere to cook.",
        "home": "{home}, for as long as it is paid for.",
        "worship": "{where}. It is the one thing here that looks familiar.",
        "visa": "{visa}. Thirty days, and then I am somebody else's problem.",
        "era": "I read about it at home and it seemed very far away. It does "
               "not seem far away from here.",
        "refusal": "looks away quickly, the way a stranger does",
    },
    "refugee": {
        "port": "The {ship} came in at {when} with {souls} aboard. I came the "
                "same way, and I asked the same questions.",
        "news": "{text}. We hear it before the screens do, and we hear it "
                "wrong.",
        "beat": "{sector} ring, {min:.0f} minutes, {on} officers. I have "
                "learned when they pass. Everyone here has.",
        "trade": "The {counter} at {where} will take a name it does not "
                 "recognise, which is not nothing.",
        "shift": "{job}, if I am picked at {start}. If I am not, there is no "
                 "{end} to speak of.",
        "meal": "{meals}, at {where}, and I am grateful for both of them.",
        "home": "{home}. It is a partition and a curtain, and it is ours.",
        "worship": "{where}. It is the only place I am asked nothing.",
        "visa": "{visa}. That word is the whole of my standing here.",
        "era": "It is why I am here. That is all it is, and it is everything.",
        "refusal": "gathers the child closer and steps out of the way",
    },
    "lurker": {
        "port": "{ship}, {when}. {souls} of them with full pockets and no idea "
                "where they are.",
        "news": "{text}. Doesn't reach down here till it's old.",
        "beat": "{sector}. {min:.0f} minutes. {on} of them, and I know all "
                "{on} by their boots.",
        "trade": "{counter}. {where}. I've been moved on from there twice.",
        "shift": "{job}? There's no shift. There's whoever's hiring at "
                 "{start} and nothing at all by {end}.",
        "meal": "{where}, if it's going. {meals} is for people with a door.",
        "home": "{home}. That's what they call it on the register.",
        "worship": "{where}. They feed you after, that's why.",
        "visa": "{visa}. Don't go near the readers, that's the trick.",
        "era": "It gets worse down here first and it gets better down here "
               "last, and that's the whole of it.",
        "refusal": "melts back into the crowd without a word",
    },
}

# 15 x 2. `{say}` is the role clause. NO FRAME MAY BE BARE and no two may be
# equal, because a bare frame would let two species collide on one string --
# which is exactly the degeneracy `deck.py --degeneracy` exists to catch, and
# `_selftest` asserts it here rather than trusting the writing.
SPECIES_FRAME = {
    "human":    ("Look -- {say}", "{say} That's about the size of it."),
    "narn":     ("{say} No more than that.", "It is simple enough. {say}"),
    "centauri": ("My dear fellow, {say}",
                 "{say} And there is a great deal more to it, believe me."),
    "minbari":  ("Be at peace. {say}", "{say} It is done as it should be."),
    "drazi":    ("{say} Yes? Good.", "Hah. {say}"),
    "brakiri":  ("{say} At this hour, at least.",
                 "By the night's reckoning, {say}"),
    "pakmara":  ("Translator: {say}", "{say} Translation ends."),
    "vree":     ("{say} That is the arrangement.", "Arrangement: {say}"),
    "abbai":    ("{say} We would rather it were settled quietly.",
                 "If it can be done gently: {say}"),
    "gaim":     ("The interpreter says: {say}",
                 "Through the interpreter: {say} The hive adds nothing."),
    "hyach":    ("{say} It was so before you came.", "In the old order: {say}"),
    "llort":    ("{say} You want it? Make me an offer.", "Heh. {say}"),
    "grome":    ("{say} The soil does not hurry.", "Slowly, then: {say}"),
    "other":    ("{say} That is all I have to say to you.",
                 "Understand this: {say}"),
    "vorlon":   ("And? {say}", "{say} You already knew."),
}

# Four greeting stems and four parting stems per species; a role tag and a role
# parting clause. greet = stem + tag, farewell = stem + parting. 4 + 4 = the 8
# the row's arithmetic asks for, and both halves are cell-unique.
SPECIES_GREET = {
    "human":    ("Good {word}.", "{Word}.", "Yes?", "You want me?"),
    "narn":     ("Good {word} to you.", "{Word}. State it.", "Speak.",
                 "You have found me. Well."),
    "centauri": ("Ah! Good {word}, good {word}!", "{Word}, and well met.",
                 "You are in luck, I am at leisure.", "Yes, yes -- come."),
    "minbari":  ("Good {word}. Be welcome.", "{Word}. The light is with you.",
                 "You are expected, as all are.", "Peace to you."),
    "drazi":    ("{Word}. What.", "Good {word}. Be quick.", "Hah! Speak.",
                 "You. Yes?"),
    "brakiri":  ("Good {word} -- by my clock, at any rate.",
                 "{Word}. The desk is open.", "You have caught me working.",
                 "Business, or company?"),
    "pakmara":  ("Translator: good {word}.", "{Word}. Translator ready.",
                 "Speech is permitted.", "You address me. Proceed."),
    "vree":     ("Good {word}. State the arrangement.", "{Word}. Proceed.",
                 "You are recognised.", "An approach is noted."),
    "abbai":    ("Good {word}, and gently.", "{Word}. Be at ease.",
                 "You are very welcome here.", "Softly, now."),
    "gaim":     ("The interpreter returns your good {word}.",
                 "{Word}. The interpreter attends.",
                 "The hive acknowledges you.", "Address the interpreter."),
    "hyach":    ("Good {word}, as it has always been said.",
                 "{Word}. You are young.", "You come to an old house.",
                 "Be seated, or do not."),
    "llort":    ("{Word}. What have you got?", "Good {word}. Show me.",
                 "Heh. You again.", "Something to sell?"),
    "grome":    ("Good {word}. There is no hurry.", "{Word}. Sit if you like.",
                 "You have come a long way for this.", "Slowly, now."),
    # NOT "Good {word}." -- that is `human`'s stem, and two species sharing a
    # stem collapses ten cells onto five strings. Found by the identity
    # assertion below, not by reading.
    "other":    ("A good {word} to you.", "{Word}. Yes.",
                 "You wish to speak with me.", "I am here. Ask."),
    "vorlon":   ("You are expected.", "{Word}. Perhaps.", "You have come.",
                 "Ah."),
}
SPECIES_PART = {
    "human":    ("Good {word} to you.", "Right you are.", "Mind how you go.",
                 "See you about."),
    "narn":     ("Go well.", "That is enough said.", "We are finished.",
                 "Strength to you, for what it is worth."),
    "centauri": ("Charmed, absolutely charmed.", "Do call again -- do!",
                 "Until the next time, and there will be one.",
                 "You have been a delight, truly."),
    "minbari":  ("Go in the light.", "Be at peace.",
                 "The work continues without us.", "Until it is time."),
    "drazi":    ("Go.", "Hah. Finished.", "Enough.", "Away with you, then."),
    "brakiri":  ("Good night -- mine, not yours.", "The desk closes.",
                 "Settle before the market opens.", "Until the dark hours."),
    "pakmara":  ("Translation ends.", "Session concluded.",
                 "No further speech is required.", "Disconnect."),
    "vree":     ("The arrangement stands.", "Concluded.",
                 "Terms are recorded.", "Departure is noted."),
    "abbai":    ("Go quietly.", "Let it rest there.",
                 "Nothing more need be said.", "Be gentle with it."),
    "gaim":     ("The interpreter withdraws.", "The hive has no more.",
                 "Communication ends.", "Return if the hive is needed."),
    "hyach":    ("It was so before you came.", "Go, then, as the young do.",
                 "Another will ask the same in a century.",
                 "The house remains."),
    "llort":    ("Bring me something next time.", "Heh. Off with you.",
                 "No sale, no farewell.", "Come back with better."),
    "grome":    ("Go slowly.", "It will keep.", "There is time yet.",
                 "The soil does not hurry, and neither should you."),
    "other":    ("That is all.", "We are done here.", "Go on, then.",
                 "Nothing further."),
    "vorlon":   ("Go.", "Later.", "When you are ready.", "Not yet."),
}

# One tag per role, appended to a greeting; one parting clause per role. These
# are what make (narn, dockworker) and (narn, merchant) different cells rather
# than one cell said twice.
ROLE_TAG = {
    "command": "This is a duty station.",
    "security": "Station security.",
    "customs": "Customs. Have your card ready.",
    "traffic": "Bay control.",
    "medical": "Medlab. Is anybody hurt?",
    "diplomat": "The mission is receiving.",
    "envoy": "",
    "cleric": "The hours are open to anyone.",
    "financier": "The desk is open.",
    "merchant": "Everything on the cloth is priced.",
    "service": "What can I get you?",
    "engineer": "Mind the panel, it is live.",
    "industrial": "You are on the shop floor.",
    "dockworker": "Bay's working. Stand clear.",
    "waste": "You are a long way down.",
    "hydroponics": "Mind the beds.",
    "visitor": "I have only just arrived myself.",
    "refugee": "I am waiting, like everyone.",
    "lurker": "You are not from down here.",
}
ROLE_PART = {
    "command": "I am wanted on the board.",
    "security": "Keep moving, please.",
    "customs": "Next in the queue.",
    "traffic": "Bay control out.",
    "medical": "Come back if it worsens.",
    "diplomat": "The mission will be in touch.",
    "envoy": "",
    "cleric": "The hours are kept whether you come or not.",
    "financier": "Accounts close at the hour.",
    "merchant": "Come back when you are buying.",
    "service": "Same again tomorrow, no doubt.",
    "engineer": "This panel is not going to close itself.",
    "industrial": "The line does not wait.",
    "dockworker": "Hull is not going to unload itself.",
    "waste": "Somebody has to be down here.",
    "hydroponics": "The beds want water.",
    "visitor": "I will probably be lost again by evening.",
    "refugee": "I will be here. I am always here.",
    "lurker": "You never saw me.",
}


def _cell_greet(species: str, role: str) -> tuple:
    """The cell's four greetings. Species stem plus the role's own tag."""
    tag = ROLE_TAG.get(role, "")
    return tuple((g + (" " + tag if tag else "")).strip()
                 for g in SPECIES_GREET.get(species, SPECIES_GREET["other"]))


def _cell_part(species: str, role: str) -> tuple:
    """The cell's four farewells."""
    tag = ROLE_PART.get(role, "")
    return tuple((p + (" " + tag if tag else "")).strip()
                 for p in SPECIES_PART.get(species, SPECIES_PART["other"]))


def cell_clause(role: str, topic: str) -> str:
    """WHAT this role says about this subject, braces and all. None if absent."""
    return (ROLE_CLAUSE.get(role) or {}).get(topic)


def cell_line(species: str, role: str, topic: str, variant: int = 0) -> str:
    """One tier-2 matrix line: the role's clause in this species' mouth.

    Returns None when the matrix has no clause for the role, which is the
    documented fallback to `PHRASE` -- a role that exists in `schedule.ROLES`
    and not here. `_selftest` asserts there are none today, so the fallback is
    a safety net rather than a hiding place.
    """
    say = cell_clause(role, topic)
    if say is None:
        return None
    frames = SPECIES_FRAME.get(species, SPECIES_FRAME["other"])
    return frames[variant % len(frames)].format(say=say)


def cell_lines(species: str, role: str) -> tuple:
    """Everything one (species x role) cell can say. DLG-02's per-cell pool.

    11 topics x 2 frames + 4 greetings + 4 farewells = 30, and the harness
    counts THIS rather than a number written down beside it.
    """
    out = []
    for key, _fn in TOPICS:
        for v in range(len(SPECIES_FRAME.get(species, SPECIES_FRAME["other"]))):
            ln = cell_line(species, role, key, v)
            if ln:
                out.append(ln)
    out.extend(_cell_greet(species, role))
    out.extend(_cell_part(species, role))
    return tuple(out)


# ===========================================================================
# 4f.  DLG-01 -- THE TIER-1 CAST, 75 LINES EACH, NONE SHARED
# ===========================================================================
#
# THE ROW'S RULE IS THE HARD PART AND IT IS NOT THE COUNT: *"No string may
# appear in two NPCs' sets (the T1 no-two-identical rule applied to speech)."*
# Before this section the module had 69 templates TOTAL, shared by every
# speaker on the station, so the rule was violated BY CONSTRUCTION rather than
# by a shortfall -- `spec_harness/dlg.py` said so in exactly those words.
#
# WHERE THE FIFTY COME FROM, AND IT IS NOT A SECOND ROSTER. `docs/spec/PEOPLE.md`
# CAST-02 is a fifty-row table with a name, a species, an office, a home
# address, schedule anchors and a link list per row. `cast_roster()` PARSES
# THAT TABLE. A copy of the fifty in this file would be a second description of
# the cast, and this repository's own rule is that the two would drift -- the
# spec would gain a row and the module would not, and no gate could see it.
# The parse is asserted against the annex's own stated count.
#
# HOW 75 IS COMPOSED, and every family is the annex's:
#
#   11 topics x 3 salience variants                          = 33
#   greetings, 4 dayparts x 2 acquaintance bands             =  8
#   farewells                                                =  4
#   biography / office / links                               = 12
#   player-memory states, 3 x 3                              =  9
#   own counter/office work lines                            =  9
#                                                             ----
#                                                               75
#
# WHAT MAKES THEM DISTINCT ACROSS THE FIFTY, mechanically rather than by
# hoping: every template names a fact only that row holds -- the person's own
# name or designation, their office, their home, their schedule anchor, or the
# names at the other end of their two CAST links. TWO ROWS SHARE AN OFFICE
# (11 and 12 are both "Ombudsman (retained canon office)", both living in
# `qtr_command`), which is precisely why the check is an assertion over all
# 3,750 rendered strings and not an argument about the design. When it fires it
# names the pair.
#
# AND THE RUNTIME FACTS SURVIVE. A cast topic line still carries the braces the
# topic function fills -- `{ship}`, `{souls}`, `{min:.0f}` -- so Milo's port
# line names today's actual liner and Ruth's names the same liner in her own
# words. The person's facts are baked in; the station's are not. Authority 5
# for the phrasings, the annex for every fact in them. INV-699.

_CAST_ROW = None

# The annex's species abbreviations, expanded to `schedule.ROLE_WEIGHTS` keys.
_SP_ABBREV = {"hum": "human", "drz": "drazi", "cen": "centauri",
              "min": "minbari", "narn": "narn", "brak": "brakiri",
              "vree": "vree", "abb": "abbai", "gaim": "gaim",
              "pak": "pakmara", "other": "other", "llort": "llort",
              "hyach": "hyach", "grome": "grome", "vorlon": "vorlon"}

CAST_ANNEX = os.path.join(os.path.dirname(_HERE), "docs", "spec", "PEOPLE.md")


def _plain(s: str) -> str:
    """Strip the annex's markdown so a line reads as speech, not as a table."""
    s = re.sub(r"`([^`]*)`", r"\1", s or "")
    s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def cast_roster() -> tuple:
    """The CAST-02 fifty, parsed from the annex. One dict per row.

    THE ANNEX IS THE ONLY SOURCE. Every field below is a column of the table in
    `docs/spec/PEOPLE.md` CAST-02; nothing is invented here and nothing is
    copied here. A row added to the annex is a person this module can speak as
    on the next run.
    """
    global _CAST_ROW
    if _CAST_ROW is not None:
        return _CAST_ROW
    rows, by_n = [], {}
    with open(CAST_ANNEX, encoding="utf-8") as f:
        for ln in f:
            if not re.match(r"^\|\s*\d+\s*\|", ln):
                continue
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) < 7:
                continue
            n = int(c[0])
            sp = _SP_ABBREV.get(c[2].split()[0].strip("`*"), "other")
            row = {
                "n": n,
                "who": _plain(c[1]),
                "species": sp,
                "office": _plain(c[3]),
                "home": _plain(c[4]),
                "anchor": _plain(c[5]),
                "links_raw": _plain(c[6]),
                "link_n": [int(x) for x in re.findall(r"\b(\d{1,2})\b", c[6])],
            }
            rows.append(row)
            by_n[n] = row
    for r in rows:
        names = [by_n[i]["who"] for i in r["link_n"] if i in by_n]
        r["link1"] = names[0] if names else "the muster board"
        r["link2"] = names[1] if len(names) > 1 else r["link1"]
        # THE GRIEVANCE IS IN THE TABLE WHERE THERE IS ONE. Several rows carry
        # a clause after an em-dash -- row 6 "owes the Collector 340 cr", row
        # 20 "asks no names" -- and that clause IS the grievance the row asks
        # for. Where there is none, the office is the grievance's subject and
        # the line says so rather than inventing an injury.
        tail = re.split(r"\s+[-—]{1,2}\s+", r["links_raw"], 1)
        r["grievance"] = _plain(tail[1]) if len(tail) > 1 else ""
    _CAST_ROW = tuple(rows)
    return _CAST_ROW


def cast_by_name(who: str):
    """One CAST-02 row by its name or designation, or None."""
    for r in cast_roster():
        if r["who"] == who:
            return r
    return None


# The eleven topics' cast phrasings. Three per topic -- DLG-01's "3 salience
# variants" -- and each `%` field is a column of the row. `{...}` survives into
# the output and is filled by the topic function at speak() time.
_CAST_TOPIC = {
    "port": (
        "The {ship} at {when}. %(who)s has been watching hulls come onto "
        "%(office)s long enough to know which ones mean work.",
        "{souls} off the {ship}. %(who)s does not get a quiet day out of a "
        "manifest like that.",
        "{ship}. {when}. {souls}. Ask %(link1)s what a manifest like that "
        "does to %(who)s.",
    ),
    "news": (
        "You will have heard: {text}. %(who)s heard it first from %(link1)s, "
        "which tells you something about this station.",
        "{text}. It reaches %(who)s at %(office)s about an hour after it "
        "reaches the screens, and in worse shape.",
        "{text}. %(who)s has stopped repeating that sort of thing where "
        "%(link2)s can hear.",
    ),
    "beat": (
        "{sector} ring, {min:.0f} minutes, {on} on the watch. I know because "
        "%(anchor)s is where I stand when they go past.",
        "{on} officers on {sector} ring. Not one of them has ever come to "
        "%(who)s at %(office)s unless something was already broken.",
        "{min:.0f} minutes a circuit. %(who)s has timed it, and %(who)s has "
        "reason to.",
    ),
    "trade": (
        "The {counter} at {where}. That is %(office)s, and %(who)s has held "
        "it longer than most people here have been aboard.",
        "You want the {counter} at {where}? Then you want %(who)s, and you "
        "want to be straight with me.",
        "{counter}. {where}. %(link1)s sends people to %(who)s and %(who)s "
        "sends them back, and between us nobody goes short.",
    ),
    "shift": (
        "I am due at {job} -- %(anchor)s, and it does not move for anybody.",
        "{start} to {end}. %(who)s has kept those hours since before the "
        "current lot ran this station.",
        "{job}, {start}. %(link2)s will not forgive %(who)s a third late "
        "start.",
    ),
    "meal": (
        "{meals} at {where}. %(who)s eats where the work is, which is not "
        "always where the food is.",
        "I take a meal at {where}. %(link1)s usually finds %(who)s there and "
        "usually wants something.",
        "{meals} a day at {where}. %(who)s eats the second one standing up "
        "at %(office)s.",
    ),
    "home": (
        "I have quarters at {home}. %(who)s sleeps there and does very little "
        "else there.",
        "{home}. It is what %(office)s pays for, and it is enough for "
        "%(who)s.",
        "{home}, and %(link2)s is three doors down from %(who)s, which is a "
        "mixed blessing.",
    ),
    "worship": (
        "I keep the hours at {where}, when %(anchor)s allows it. It usually "
        "does not.",
        "{where}. %(who)s goes for the quiet, and does not pretend otherwise.",
        "{where}. %(link1)s goes too, and %(who)s does not discuss it "
        "afterwards.",
    ),
    "visa": (
        "My status reads {visa}. On %(office)s that is a formality, and "
        "%(who)s knows exactly how lucky that is.",
        "{visa}. %(who)s has carried the same card for years and has never "
        "once been asked for it twice.",
        "{visa}. Ask %(link2)s what happens to somebody who cannot say the "
        "same as %(who)s.",
    ),
    "era": (
        "It reached %(who)s at %(office)s the way everything reaches us: "
        "late, and as an instruction nobody would explain.",
        "%(who)s has seen this station change hands in everything but name, "
        "and this is the first time it has felt permanent.",
        "%(link1)s and %(who)s do not agree about it. We have agreed to stop "
        "talking about it, which is not the same thing.",
    ),
    "refusal": (
        "turns back to %(office)s; %(who)s is finished with you",
        "says nothing, and %(who)s goes to find %(link1)s instead",
        "leaves the way %(who)s leaves any room where the conversation has "
        "stopped being useful",
    ),
}

# 4 dayparts x 2 acquaintance bands. CAST-05's memory of the player is the
# second axis: a stranger and somebody you have met get a different hello, and
# the annex's own probe (2) for Ruth Delgado is exactly that.
_CAST_GREET = (
    ("early", 0, "You are up early for a stranger. %(office)s does not open "
                 "for another hour, and %(who)s is not open at all."),
    ("early", 1, "You again, at this hour. %(who)s is beginning to think you "
                 "do not sleep either."),
    ("morning", 0, "Morning. If you are looking for %(office)s, you have "
                   "found it, and %(who)s with it."),
    ("morning", 1, "Morning. %(link1)s was asking after you, and %(who)s "
                   "said nothing useful."),
    ("midday", 0, "Good day. State it quickly, %(anchor)s is in an hour."),
    ("midday", 1, "There you are. Sit down before somebody sends %(who)s "
                  "back to %(office)s."),
    ("evening", 0, "Evening. %(who)s is off in an hour and you are not on the "
                   "list."),
    ("evening", 1, "Evening. Same as last time, or has something changed "
                   "since you were last at %(office)s looking for %(who)s?"),
)

_CAST_FAREWELL = (
    "Go on, then. %(anchor)s will not keep itself.",
    "That is me finished. %(link2)s will know where %(who)s has gone.",
    "Back to %(office)s. It is where %(who)s is when %(who)s is anywhere.",
    "Come and find %(who)s at %(home)s if it will not keep until morning.",
)

# Biography, office and links -- twelve, and the annex names six of them
# explicitly (who I am, how I got this, the grievance, both CAST links, home,
# the era). The remaining five are the questions those six leave open: what the
# office costs, what it is worth, who it answers to, what came before it, and
# what happens to it when this person stops.
_CAST_BIO = (
    "I am %(who)s. %(office_full)s -- and that is not a title anybody hands "
    "out twice.",
    "How %(who)s came to %(office)s is a longer story than you want, and it "
    "starts with %(link1)s owing somebody a favour.",
    "%(grievance_line)s",
    "%(link1)s and %(who)s go back further than either of us admits in "
    "company.",
    "%(link2)s I would trust with the takings. %(who)s would not trust "
    "%(link2)s with an opinion.",
    "%(home)s is where %(who)s sleeps. It is not where I live; %(office)s is "
    "where I live.",
    "%(era_line)s",
    "%(office)s costs me the hours nobody else wants -- %(anchor)s, every day, "
    "whatever else is happening.",
    "What it is worth is that when something goes wrong on this deck, people "
    "come and find %(who)s.",
    "I answer to whoever signs the roster this month. It has been three "
    "different names since %(who)s took %(office)s.",
    "Before %(office)s, %(who)s did something else, somewhere else, and does "
    "not talk about it with strangers.",
    "When %(who)s stops, %(link2)s takes it on. That has been agreed for "
    "years and neither of us has said it out loud.",
)

# The player-memory states, 3 x 3. CAST-05 says the axis is stranger /
# acquainted / known, and the three columns are what each state changes: how
# they open, what they will discuss, and what they will do for you.
_CAST_MEMORY = (
    "I do not know you. That is not rudeness, it is %(office)s talking "
    "through %(who)s.",
    "I will tell you what anybody standing at %(office)s could tell you, and "
    "%(who)s will tell you no more than that.",
    "If you want something from %(who)s today, you will be paying for it.",
    "You have been here before. %(who)s remembers faces; it is most of the job.",
    "%(who)s will go a little further with you than with a stranger. Ask, "
    "and we will see.",
    "%(who)s can put a word in with %(link1)s. That is not nothing, whatever "
    "you think of it.",
    "There you are. %(who)s has been wondering where you got to.",
    "Ask %(who)s anything. I have stopped keeping the careful version for "
    "you.",
    "If it goes wrong, come to %(home)s and knock. %(who)s will not ask what "
    "you have done.",
)

# The nine work lines: what this person says DOING their office, across the
# shapes a counter or a post actually takes.
_CAST_WORK = (
    "%(office)s is open and %(who)s is behind it. One at a time, and mind "
    "the step.",
    "That is not how it is done at %(office)s, and %(who)s is not going to "
    "pretend otherwise.",
    "Give me a moment. %(anchor)s means I am doing two things at once.",
    "%(who)s signs for that, and %(who)s does not sign for it twice.",
    "Take it to %(link1)s. It is not mine, and %(who)s is not going to make "
    "it mine.",
    "It goes in the book. Everything %(who)s does at %(office)s goes in the "
    "book.",
    "You will have it by the end of the watch, or you will have a reason "
    "from %(who)s.",
    "That price is the price. %(link2)s pays it and %(link2)s complains to "
    "%(who)s about it too.",
    "Right. That is %(office)s dealt with. What else does %(who)s owe you?",
)


def _cast_facts(row: dict) -> dict:
    """The `%`-fields every cast template above may name."""
    who = row["who"]
    griev = row["grievance"]
    # THE OFFICE COLUMN IS A SPEC CELL AND NOT A SPOKEN PHRASE. Row 21 reads
    # "publican, `bar_unnamed` -- owner-operator evenings", which is correct in
    # a table and unsayable in a bar. `office` is therefore the head of it --
    # everything before the first comma or dash -- and `office_full` is kept
    # for the one biography line that is allowed to be the whole entry.
    # Shortening can make two offices equal; it cannot make two LINES equal,
    # because every cast template also names the person.
    head = re.split(r"\s+[-—]{1,2}\s+|,", row["office"])[0].strip()
    return {
        "who": who,
        "office": head or row["office"],
        "office_full": row["office"],
        "home": row["home"],
        "anchor": row["anchor"],
        "link1": row["link1"],
        "link2": row["link2"],
        "grievance_line": (
            f"What {who} carries is this: {griev}. Ask {row['link1']} if "
            f"you do not believe me." if griev else
            f"{who}'s grievance is {row['office']} itself -- what it asks of "
            f"a person, and what it is paid."),
        "era_line": (
            f"{who} was aboard before any of it. What it changed for "
            f"{row['office']} is that nobody now says what they mean in a "
            f"corridor."),
    }


def cast_lines(row) -> tuple:
    """The 75 lines belonging to ONE Tier-1 cast member.

    `row` is a CAST-02 dict from `cast_roster()` or the name in its first
    column. Runtime braces (`{ship}`, `{min:.0f}`) survive; the person's own
    facts are already in.
    """
    if isinstance(row, str):
        row = cast_by_name(row)
    if row is None:
        return ()
    f = _cast_facts(row)
    out = []
    for key, _fn in TOPICS:
        for t in _CAST_TOPIC[key]:
            out.append(t % f)
    for _dp, _warm, t in _CAST_GREET:
        out.append(t % f)
    for t in _CAST_FAREWELL:
        out.append(t % f)
    for t in _CAST_BIO:
        out.append(t % f)
    for t in _CAST_MEMORY:
        out.append(t % f)
    for t in _CAST_WORK:
        out.append(t % f)
    return tuple(out)


def cast_topic_line(row, topic: str, variant: int = 0) -> str:
    """One cast topic line, for `phrase()` to prefer over the tier-2 matrix."""
    if isinstance(row, str):
        row = cast_by_name(row)
    if row is None or topic not in _CAST_TOPIC:
        return None
    pool = _CAST_TOPIC[topic]
    return pool[variant % len(pool)] % _cast_facts(row)


def cast_greeting(row, part: str, known: bool) -> str:
    """The daypart x acquaintance greeting. CAST-05's memory, in the hello."""
    if isinstance(row, str):
        row = cast_by_name(row)
    if row is None:
        return None
    f = _cast_facts(row)
    want = "evening" if part not in ("early", "morning", "midday") else part
    for dp, warm, t in _CAST_GREET:
        if dp == want and warm == int(bool(known)):
            return t % f
    return None                                              # pragma: no cover


def occupied_cells() -> tuple:
    """The (species, role) pairs `schedule.ROLE_WEIGHTS` actually populates.

    79 at the datum, and DERIVED -- so a weight going to zero removes a cell
    from the matrix's denominator instead of leaving a row nobody occupies.
    """
    return tuple((sp, r) for sp, w in sched.ROLE_WEIGHTS.items()
                 for r, n in w.items() if n)


# THE ANTI-REPEAT RULE, NORMATIVE IN THE ANNEX: *"within one place-visit no
# tier-2 line repeats until its cell's pool is exhausted (draw without
# replacement per (NPC, session))"*.
#
# AND IT IS A PERMUTATION, NOT A LEDGER, BECAUSE DETERMINISM IS THE OLDER
# RULE. The first version kept a mutable `drawn` set per (species, role, npc,
# session) and `_selftest`'s "the same world state twice gives the same lines"
# failed immediately -- correctly: a `speak()` whose output depends on how many
# times it has been called cannot be baked into a sidecar, cannot be
# A/B-tested, and cannot be reproduced under two hash seeds. CLAUDE.md's
# ROBUSTNESS 0 descriptor names `random` and salted hashing for the same
# reason.
#
# So the draw is `_shuffle(pool, key)[turn % len(pool)]` -- a Fisher-Yates
# permutation seeded by blake2b through `_u`, indexed by an ORDINAL THE CALLER
# SUPPLIES. Draw-without-replacement is then a fact about the permutation
# (lines-before-first-repeat is exactly the pool size, 30, comfortably over
# the annex's floor of 20 in a ten-minute dwell) rather than a probability,
# and two calls with the same world are the same call.
def _shuffle(pool: tuple, key: str) -> tuple:
    """A deterministic permutation of `pool`, keyed by `key`. No `random`."""
    out = list(pool)
    for i in range(len(out) - 1, 0, -1):
        j = int(_u(f"{key}|{i}") * (i + 1)) % (i + 1)
        out[i], out[j] = out[j], out[i]
    return tuple(out)


def cell_draw(species: str, role: str, npc_id: str, session: str = "",
              topic: str = None, turn: int = 0) -> str:
    """The `turn`-th line this person says, without repeating inside the pool."""
    pool = cell_lines(species, role)
    if not pool:
        return None
    if topic is not None:
        say = cell_clause(role, topic)
        want = tuple(l for l in pool if say and say in l) if say else ()
        pool = want or pool
    perm = _shuffle(pool, f"cell|{species}|{role}|{npc_id}|{session}")
    return perm[turn % len(perm)]


def lines_before_repeat(species: str, role: str, npc_id: str,
                        session: str = "") -> int:
    """How many draws before this cell says something twice. The annex's floor.

    *"lines-before-first-repeat >= 20 in any 10-minute room dwell"*. Measured
    by walking the draw rather than by asserting the pool size, because those
    are two different claims and only one of them is about the code.
    """
    seen, n = set(), 0
    while True:
        t = cell_draw(species, role, npc_id, session, turn=n)
        if t in seen:
            return n
        seen.add(t)
        n += 1
        if n > 1000:                                         # pragma: no cover
            return n


# ===========================================================================
# 4d.  DLG-06 -- the two scarce voices, and scarcity enforced as content
# ===========================================================================
#
# THE CEILING IS THE CONTENT. Every other pool in this module has a FLOOR;
# these two have a maximum, and the reason is in FACTIONS.md 12: Kosh is
# *"almost never seen"*, and `_ROLE_REGISTER["envoy"]` already carries the
# consequence -- formality 1.00, terseness 0.95, "two public hours a day, and
# almost nothing said in them". A Vorlon with fifty lines is not a better
# Vorlon, it is a different character. So the pool is twelve, the runtime
# refuses to repeat one inside a session, and `_selftest` asserts the ceiling
# from the annex rather than from a number in this file.
#
# TWELVE, AND WHY TWELVE: the annex's ceiling, and it is the same twelve as the
# two public hours in the role register's own note -- one utterance an hour of
# audience, six days of public hours before a player could exhaust the pool.
# Nothing here answers a question. INV-695.
KOSH_LINES = (
    "You are not ready.",
    "The avalanche has already begun. It is too late for the pebbles to vote.",
    "Understanding is a three-edged sword.",
    "And so it begins.",
    "You seek meaning where there is only arrangement.",
    "The question you asked is not the question you came with.",
    "You have always been here. You have simply not been listening.",
    "Truth is a river. You are standing in it and asking where the water is.",
    "I was, and will be. You are.",
    "When the long night comes, return to the end of the beginning.",
    "You ask what I want. Nothing you have.",
    "Go away.",
)

# THE BROKER IS THE OTHER SHAPE OF SCARCITY: not silence, but AUDIENCE. The
# night broker (CAST-02 row 36) works 18:30-02:30 -- `schedule.species_work_shift`
# for a Brakiri, whose day begins at 16:00 -- and sells to whoever is in front
# of him at a price set by who else is listening. So the pool is gated on the
# ROOM rather than on the clock: the same twenty lines, and which of them he
# will say depends on whether the player is alone with him.
#
# Twenty, the annex's ceiling. The split is 10 alone / 10 with an audience,
# because a broker who says the same thing in both rooms is not a broker.
# INV-696.
BROKER_LINES = (
    # audience present -- the public price, the public manner
    (True, "The desk is open to anyone standing at it. That includes you and "
           "it includes them."),
    (True, "Commodities only, at this hour. Anything else is a daytime "
           "conversation."),
    (True, "The posted rate is the posted rate. I do not move it because a "
           "room is watching."),
    (True, "I keep no ledger anyone can subpoena and no opinion anyone can "
           "quote."),
    (True, "If you want the manifest, it is public. If you want what is on it, "
           "that is not."),
    (True, "Three of you have asked me the same question tonight. I have given "
           "three answers and one of them was true."),
    (True, "Your standing is your credit. Neither is my business to explain in "
           "front of company."),
    (True, "I am a licensed commodities desk. Say that back to whoever sent "
           "you.",),
    (True, "Come back at the turn of the watch. The room will be emptier."),
    (True, "No. Not here, not at this volume."),
    # alone -- the real desk
    (False, "Now. What is it you actually want, and who is not to know you "
            "wanted it?"),
    (False, "There is a lot on that hull that is not on that manifest. The "
            "difference is what I sell."),
    (False, "Passage without a name on it costs four times passage with one. "
            "It is not a fine, it is the risk."),
    (False, "The Collector bought that debt in the spring. He has not called "
            "it in because he is waiting for you to be worth more."),
    (False, "I can tell you which berth she is in. I cannot tell you what she "
            "is carrying and neither can her master."),
    (False, "Names are the expensive part. Everything around a name is nearly "
            "free."),
    (False, "You are the third person this week asking after that quarter. The "
            "other two wore the armband."),
    (False, "I will take Centauri paper at eighty. I will not take Narn paper "
            "at any figure, and you know why."),
    (False, "There is a way off this station that does not touch customs. I am "
            "not going to say it twice."),
    (False, "You have run out of things I want. Come back when that changes."),
)


def kosh_lines(session: str = "", spoken=()) -> tuple:
    """The Kosh utterances still available in this session.

    NEVER TWICE IN ONE SESSION IS ENFORCED HERE AND NOT REMEMBERED ELSEWHERE.
    `spoken` is what the session has already heard; the draw is what is left.
    An exhausted pool returns () -- and that is the correct answer, because a
    Vorlon who has said his twelve things says nothing, which is the register.
    """
    said = set(spoken)
    return tuple(l for l in KOSH_LINES if l not in said)


def broker_lines(alone: bool) -> tuple:
    """What the Broker will say with, or without, a room listening."""
    return tuple(t for gate, t in BROKER_LINES if gate is not alone)


def scarce_voice(sp) -> str:
    """Is this speaker one of DLG-06's two, and which?

    KOSH IS A ROLE, NOT A NAME. `_ROLE_REGISTER["envoy"]` is already written
    for him -- formality 1.00, terseness 1.00 with the species delta -- and
    `schedule.ROLE_WEIGHTS["vorlon"]` has exactly one occupied cell, which is
    why DLG-02's matrix counts vorlon as 1. Matching on the role means the
    ceiling holds for the office rather than for one npc_id.

    The Broker is CAST-02 row 36: a Brakiri commodities desk at
    `business_center`, working 18:30-02:30 because that is what
    `schedule.species_work_shift` does to a species whose day starts at 16:00.
    """
    if sp.role == "envoy" or sp.species == "vorlon":
        return "kosh"
    if (sp.role == "financier" and sp.species == "brakiri"
            and sp.place == "business_center"):
        return "broker"
    return ""


def scarce_line(sp, world: World):
    """One scarce utterance, or None if this speaker is not a scarce voice.

    Returns `(text, why)`. An empty `text` means the session has exhausted the
    pool and the answer is silence -- which is the only honest thing a CEILING
    can do when it is reached, and the opposite of what a floor would do.
    """
    kind = scarce_voice(sp)
    if not kind:
        return None
    if kind == "kosh":
        # NEVER TWICE IN ONE SESSION, AND IT IS THE PERMUTATION THAT SAYS SO.
        # Turn n of a session gets perm[n]; turn 12 and after get SILENCE,
        # which is the only thing a CEILING can honestly do when it is
        # reached, and is the register besides.
        perm = _shuffle(KOSH_LINES, f"kosh|{world.session}")
        if world.turn >= len(perm):
            return ("", f"dialogue.KOSH_LINES exhausted: all "
                        f"{len(KOSH_LINES)} spoken in session "
                        f"{world.session!r} (DLG-06 ceiling, FACTIONS.md 12)")
        t = perm[world.turn]
        return (t, f"dialogue.KOSH_LINES[{KOSH_LINES.index(t)}] -- turn "
                   f"{world.turn} of {len(KOSH_LINES)} this session")
    alone = world.audience is not None and world.audience <= 1
    pool = _shuffle(broker_lines(alone), f"broker|{world.session}|{sp.npc_id}")
    return (pool[world.turn % len(pool)],
            f"dialogue.BROKER_LINES, "
            f"{'alone with him' if alone else 'a room listening'} "
            f"(audience={world.audience}) -- {len(pool)} available")

# The ASK answer -- the QUALITATIVE half. Named facts, no salience number.
ASKED = {
    "port":    ("She is at {berth}, and berthed at {when}.",
                "{berth}, in at {when}.",
                "{berth}. {when}."),
    "news":    ("It is {surface}. One reads what one is given.",
                "It's {surface}. Make of it what you like.",
                "{surface}. That's all."),
    "beat":    ("I am {posting} on this watch.",
                "I'm {posting} this watch.",
                "{Posting}."),
    "trade":   ("{where} is for {what}.",
                "{where}'s for {what}.",
                "{what}."),
    "shift":   ("I go by {via}, as everybody does.",
                "{via}. Same as everyone.",
                "{via}."),
    "meal":    ("I eat {eating}, and it is a fixed hour.",
                "I eat {eating}. Fixed hour.",
                "{Eating}."),
    "worship": ("{clerical}",
                "{clerical}",
                "{clerical}"),
    "visa":    ("It is what the card says. {reading}.",
                "That's what it says. {reading}.",
                "{reading}."),
    "era":     ("{standing}",
                "{standing}",
                "{standing}"),
}

# The HOME ask is split the way `PHRASE`'s is, and for the same reason: nobody
# in `resident.DOWNBELOW_HOMES` answers "have you been there long" about a
# billet they do not have.
ASKED_HOME = ("Long enough that {home} is the word I use for it.",
              "Long enough. {home}, for what it's worth.",
              "Long enough.")
ASKED_DOWN = ("Long enough to know which corridors are {policing}.",
              "Long enough. The corridors down there are {policing}.",
              "{Policing}. That's what you need to know.")

# The PRESS answer, WHEN THEY YIELD -- and every row carries the number the
# topic's own salience expression was computed from.
PRESSED = {
    "port":    ("{rate:.1f} souls a minute through the hall. That is {mult:.1f} "
                "times an ordinary watch.",
                "{rate:.1f} a minute through here. {mult:.1f} times normal.",
                "{rate:.1f} a minute. {mult:.1f} times normal."),
    "news":    ("There are {live} of them running in this room at present.",
                "{live} of them running in here right now.",
                "{live} of them. In here. Now."),
    "beat":    ("{pairs} pairs roving, of {on} on the watch across the sector.",
                "{pairs} pairs out, {on} on the watch.",
                "{pairs} pairs. {on} on watch."),
    "trade":   ("{where} answers for {what}; the {counter} is only my part "
                "of it.",
                "{where} does {what}. The {counter}'s just my bit.",
                "{what}. The {counter}'s mine."),
    "shift":   ("{hours:.0f} hours of it, {start} to {end}, and I cross by "
                "{via}.",
                "{hours:.0f} hours, {start} to {end}. I come by {via}.",
                "{hours:.0f} hours. {via}."),
    "meal":    ("My people keep {meals} in a day; the station keeps three. I "
                "eat {eating}.",
                "{meals} a day for us, three for the station. I eat {eating}.",
                "{meals} a day. {Eating}."),
    "worship": ("{where}, when the watch allows it, which is less often than "
                "the order would like.",
                "{where}, when the watch allows. Which isn't often.",
                "{where}. When they let me."),
    "visa":    ("In this room it matters: {reading}.",
                "In here it matters. {reading}.",
                "{reading}."),
    "era":     ("{bearing} That is the difference, and it is the whole of it.",
                "{bearing} That's the difference.",
                "{Bearing}"),
}
PRESSED_HOME = ("{home}, and it is exactly what the register says it is.",
                "{home}. Exactly what it says on the register.",
                "{home}. That's it.")
PRESSED_DOWN = ("{m2:.0f} square metres a person, and the corridor is "
                "{policing}.",
                "{m2:.0f} square metres each, and the corridor is {policing}.",
                "{m2:.0f} metres each. {Policing}.")

# ...AND WHEN THEY DO NOT. Three bands of the same refusal, because a formal
# speaker declines and a blunt one stops talking. This is the line the player
# gets for pushing the wrong person, and it is the reason the stance is a
# gamble rather than a button.
DEFLECT = ("I have said what there is to say.",
           "That's as much as you'll get.",
           "No.")

# The LET-GO answer is the empty tuple, everywhere. The farewell that already
# follows in `speak` IS the reply, so a stance that means "drop it" produces no
# extra words -- which is the whole of its cost: you never hear `PRESSED`.


def _stance_extra(key: str, f: dict, reg: Register, sp: _Speaker) -> dict:
    """Render the topic's BOOLEANS into words, and nothing else.

    A template that prints `True` is a template that prints a Python literal at
    a player. Every entry here is a two-way rendering of a flag the topic
    already computed -- no new facts, no new decisions.
    """
    e = {}
    if key == "news":
        e["surface"] = ("the ISN screen" if f.get("kind") == "isn"
                        else "the Ministry notice")
    if key == "beat":
        e["posting"] = ("posted here" if f.get("posted") else "roving")
        e["pairs"] = f.get("pairs", 0)
    if key == "meal":
        e["eating"] = ("out" if f.get("out") else "in quarters")
        if f.get("segregated"):
            # FACTIONS.md 12: the only species with a segregated food economy.
            e["eating"] = "where my people are allowed to"
    if key == "worship":
        e["clerical"] = ("It is my office." if f.get("cleric")
                         else "When the hours fall right, yes.")
    if key == "visa":
        e["reading"] = ("there is a reader on this deck"
                        if f.get("reader") else "nobody here is checking")
    if key == "home" and f.get("down"):
        e["policing"] = ("walked by a patrol" if f.get("policed")
                         else "never walked by anyone")
    if key == "era":
        # The two facts `_topic_era` decides with. `who` is the species or role
        # the row landed on, and `who == "*"` is the +/-0.8 term in its own
        # salience -- an era that happened TO you against one that happened.
        e["bearing"] = ("It was done to my own people."
                        if f.get("who") != "*"
                        else "It was done to this station; I only watched.")
        e["standing"] = ("I am here on sufferance, and that is what it means."
                         if f.get("refugee")
                         else "I wear the armband. You can see that for "
                              "yourself." if f.get("armband")
                         else "It neither hunts me nor favours me. That is "
                              "as much as I will say.")
    # A BLUNT ROW OFTEN OPENS ON A VALUE, so every string fact -- the topic's
    # own and this function's -- gets a Capitalised twin, the way `_fmt` makes
    # `{Word}` out of `{word}`. Without it "{Policing}. That's what you need to
    # know." starts a sentence in lower case, which reads as a bug in the game
    # rather than as a voice.
    for src in (f, e):
        for k in list(src):
            v = src[k]
            if isinstance(v, str) and v and not k[0].isupper():
                e[k[0].upper() + k[1:]] = v[0].upper() + v[1:]
    return e


def choices_for(pick, reg: Register, sp: _Speaker, world: World) -> tuple:
    """The three things a player may say, and what each is worth.

    Returns () when there is nothing to say back -- a refusal, or a person
    with no applicable topic at all. THAT IS AN ANSWER AND NOT A GAP: a Narn
    meeting a Centauri does not speak, and offering the player a menu at a
    silence FACTIONS.md 12 is explicit about would be inventing the opposite of
    what is attested.
    """
    if pick is None or pick["key"] not in SAY or pick["key"] == "refusal":
        # `refusal` has a SAY row and NO `ASKED`/`PRESSED` row, because the
        # NPC has nothing to be asked. `speak` builds its menu itself, above.
        return ()
    key = pick["key"]
    f = dict(pick.get("fact") or {})
    b = reg.band
    e = _stance_extra(key, f, reg, sp)
    yields = yields_to_press(reg)
    down = key == "home" and f.get("down")

    ask_row = (ASKED_DOWN if down else ASKED_HOME) if key == "home" \
        else ASKED[key]
    press_row = (PRESSED_DOWN if down else PRESSED_HOME) if key == "home" \
        else PRESSED[key]

    why = (f"register warmth {reg.warmth:.2f} "
           f"{'>' if yields else '<='} terseness {reg.terseness:.2f} -> "
           f"{'yields' if yields else 'deflects'}")

    out = [
        Choice(stance="ask", text=_fmt(SAY[key][0], f, e),
               reply=(Line("npc", "speech", _fmt(ask_row[b], f, e),
                           pick["source"]),),
               yielded=True,
               source=f"{pick['source']} -> the qualitative half"),
        Choice(stance="press", text=_fmt(SAY[key][1], f, e),
               reply=(Line("npc", "speech",
                           _fmt(press_row[b], f, e) if yields else DEFLECT[b],
                           pick["source"] if yields
                           else f"npc/friction + register: {why}"),),
               yielded=yields,
               source=(f"{pick['source']} -> the salience input; {why}")),
        Choice(stance="let_go", text=_fmt(SAY[key][2], f, e), reply=(),
               yielded=True,
               source="the topic is dropped; schedule.RHYTHMS resumes"),
    ]
    return tuple(out)


# ===========================================================================
# 5.  The exchange
# ===========================================================================

def speak(resident, place_key: str, world: World = None,
          listener: Listener = None) -> Exchange:
    """The whole short exchange: a greeting, one topic, a farewell.

    GREETING / TOPIC / FAREWELL AND NOTHING MORE. No branching, no quest tree
    -- `docs/MASTER-PLAN.md` 3.2's warning about building 71 prop behaviours
    before knowing the verb set applies twice over to conversation. What makes
    this worth having is not depth of tree, it is that the middle line names
    today's liner, this officer's beat, or this shopkeeper's actual counter,
    and so could not have been written in advance.
    """
    world = world or World()
    listener = listener or Listener()
    sp = _speaker(resident, place_key)
    reg = register(sp, listener, world)
    ranked = rank(sp, listener, world, reg)
    pick = choose(ranked, sp.npc_id)

    lines = []
    sources = []
    word = _GREET_WORD[daypart(sp.species, world.hour)]

    if pick is not None and pick["key"] == "refusal":
        # No words FROM THEM. The action IS the answer, and it is the
        # gazetteer's -- but the player is not mute, and DLG-05's eleventh
        # topic row is what they say into the silence. Ask gets nothing back;
        # press gets the band's own deflection; let-go ends it. Nothing new is
        # invented for the NPC here: `DEFLECT` is the row that already exists
        # for a person who will not give up the number.
        # HOW a person avoids you is their role's business; THAT they avoid
        # you is the gazetteer's. The sourced behaviour stays in the source
        # string, so the provenance of the refusal is unchanged and only the
        # staging is the cell's (authority 5, INV-698).
        act = cell_clause(sp.role, "refusal") or pick["action"]
        lines.append(Line("npc", "action", act,
                          f"{pick['source']} -- behaviour "
                          f"{pick['action']!r}; staged by cell "
                          f"({sp.species}, {sp.role})"))
        sources.append(lines[-1].source)
        say = SAY["refusal"]
        refuse = (
            Choice(stance="ask", text=say[0], reply=(), yielded=False,
                   source=f"{pick['source']} -> they said nothing, and say "
                          f"nothing again"),
            Choice(stance="press", text=say[1],
                   reply=(Line("npc", "speech", DEFLECT[reg.band],
                               f"{pick['source']} -> band "
                               f"{BAND_NAME[reg.band]} deflection"),),
                   yielded=False,
                   source=f"{pick['source']} -> pressed a refusal"),
            Choice(stance="let_go", text=say[2], reply=(), yielded=True,
                   source="the refusal is accepted; FACTIONS.md 12's "
                          "avoidance is allowed to stand"),
        )
        return Exchange(npc_id=sp.npc_id, name=sp.name, species=sp.species,
                        role=sp.role, place=place_key, hour=world.hour,
                        topic="refusal", band=reg.band, lines=tuple(lines),
                        ranking=tuple((t["key"], round(t["salience"], 3))
                                      for t in ranked),
                        sources=tuple(sources),
                        choices=refuse, choice_at=len(lines) - 1)

    greet = (COLD_GREET if reg.warmth < WARM_FLOOR else GREET)[reg.band]
    # A TIER-1 GREETING KNOWS WHETHER IT HAS MET YOU. CAST-05's memory axis,
    # and `known` is DERIVED rather than declared: turn 0 of a session is a
    # stranger and any later turn is somebody you have already spoken to
    # today. A `known` flag set only by the gate that authored it would be the
    # unset default this project has already paid for once.
    _row = cast_by_name(sp.name) if sp.name else None
    if greet and _row is not None:
        cg = cast_greeting(_row, daypart(sp.species, world.hour),
                           world.turn > 0)
        if cg:
            lines.append(Line("npc", "speech", cg,
                              f"CAST-02 row {_row['n']} ({_row['who']}), "
                              f"{daypart(sp.species, world.hour)}, "
                              f"{'acquainted' if world.turn else 'stranger'} "
                              f"-- CAST-05 memory axis"))
            sources.append(lines[-1].source)
            greet = None          # NOT "" -- see below
    # `None` means "already said, by the cast greeting"; `""` means COLD_GREET,
    # which is the FRICTION branch and must still run. Conflating the two sent
    # every Tier-1 speaker down the no-greeting path and unpacked a friction
    # row that was None.
    if greet is None:
        pass
    elif greet:
        lines.append(Line("npc", "speech", _fmt(greet, {"word": word}),
                          f"schedule.RHYTHMS[{sp.species!r}] -> their own "
                          f"{daypart(sp.species, world.hour)} at "
                          f"{world.hour:05.2f} EMT"))
    else:
        # NO GREETING, AND THE GAZETTEER SAYS WHAT HAPPENS INSTEAD. FACTIONS.md
        # 12's rule for the whole system is "95% avoidance, 5% contact", and
        # this is what avoidance looks like in a conversation: the row's own
        # described behaviour, in place of the hello.
        #
        # AND THE BEHAVIOUR IS NOT ALWAYS THEIRS. FACTIONS.md 12's rows are
        # symmetric and its wildcard rows are written from the human side --
        # "a human talking with aliens LOWERS HIS VOICE when an armband
        # passes" describes the player, not the Narn they are talking to. So
        # the line is attributed to whichever side the row's named key
        # matched. Getting this wrong put the player's own nervousness in the
        # mouth of every alien on the station.
        p, x, y = reg.friction
        named = p[0] if p[1] == "*" else p[1] if p[0] == "*" else None
        side = "you" if (named is not None and named == y) else "npc"
        lines.append(Line(side, "action", _behaviour(p),
                          f"npc/friction.pair({x!r}, {y!r}) -> row "
                          f"({p[0]!r}, {p[1]!r}) {p[2]}, warmth "
                          f"{reg.warmth:.2f} < {WARM_FLOOR:.2f} "
                          f"(FACTIONS.md 12, authority {p[3]})"))
    sources.append(lines[-1].source)

    choices = ()
    choice_at = -1
    if pick is not None:
        # THE SCARCE VOICES INTERCEPT HERE AND NOWHERE ELSE. A Vorlon does not
        # answer the question he was asked -- that IS the register -- so the
        # topic is still ranked, still sourced, and the utterance that comes
        # out of it is drawn from the capped pool instead of the matrix. Put
        # anywhere else this would have been a table with no caller, which is
        # the defect this project has produced nine times.
        scarce = scarce_line(sp, world)
        if scarce is not None:
            text, why = scarce
            if text:
                lines.append(Line("npc", "speech", text,
                                  f"{pick['source']} -> {why}"))
                sources.append(lines[-1].source)
            else:
                # An exhausted pool is SILENCE, not a repeat. FACTIONS.md 12's
                # "almost never seen" has a floor of nothing said at all.
                lines.append(Line("npc", "action",
                                  "The encounter suit does not move.", why))
                sources.append(why)
        else:
            lines.append(Line("npc", "speech", phrase(pick, reg, sp, world),
                              f"{pick['source']} -> cell "
                              f"({sp.species}, {sp.role})"))
            sources.append(pick["source"])
        # THE MENU GOES HERE AND NOWHERE ELSE. A player can answer a topic;
        # there is nothing to say back to "good afternoon", and interrupting
        # before they have said what is on their mind would make every stance
        # the same stance.
        choices = choices_for(pick, reg, sp, world)
        if choices:
            choice_at = len(lines) - 1

    # THE FAREWELL IS THE SCHEDULE, HALF AN HOUR AHEAD. If the clock is about
    # to move them, they say where -- which means a person you catch at 07:40
    # tells you they are due on shift and the same person at 10:00 does not.
    nxt = res.where_at(resident, world.hour + FAREWELL_LOOKAHEAD_H)
    now = res.where_at(resident, world.hour)
    if nxt and nxt != now:
        lines.append(Line("npc", "speech",
                          _fmt(FAREWELL_DUE[reg.band],
                               {"next": _place_name(nxt)}),
                          f"resident.where_at({world.hour + FAREWELL_LOOKAHEAD_H:.2f})"
                          f"={nxt!r} != where_at({world.hour:.2f})={now!r}"))
        sources.append(lines[-1].source)
    else:
        bye = FAREWELL[reg.band]
        if bye:
            lines.append(Line("npc", "speech", _fmt(bye, {"word": word}),
                              f"register band {BAND_NAME[reg.band]} "
                              f"(role {sp.role}, species {sp.species})"))
            sources.append(lines[-1].source)

    return Exchange(npc_id=sp.npc_id, name=sp.name, species=sp.species,
                    role=sp.role, place=place_key, hour=world.hour,
                    topic=(pick or {}).get("key", ""), band=reg.band,
                    lines=tuple(lines),
                    ranking=tuple((t["key"], round(t["salience"], 3))
                                  for t in ranked),
                    sources=tuple(sources),
                    choices=choices, choice_at=choice_at)


def prompt(resident, listener: Listener = None,
           world: World = None) -> str:
    """What the HUD offers. A name if they have one, a species if they do not.

    Eight of fifteen species have EMPTY name fields on their identicards --
    `resident.py`'s INV-004 rule -- so the prompt has to work for a person the
    station's own records do not name.
    """
    if resident.name:
        return resident.name
    q = res.ORIGIN.get(resident.species, res.ORIGIN["other"])[0]
    return q.title()


# ===========================================================================
# 6.  `serve` -- the verb interact.py could not close
# ===========================================================================

# A `serve` interactable is a counter, and `interact.VERBS` says what it means:
# "be served across it; you are talking to whoever is behind it". So the thing
# that closes it is a function that answers WHO.
SERVE_ROLES = ("service", "merchant", "customs", "security", "financier",
               "medical", "traffic", "command", "diplomat")


def serve_tokens(place_key: str) -> tuple:
    """The declared interactables in `place_key` whose verb is `serve`."""
    q = _q(place_key)
    if q is None:
        return ()
    return tuple(t for t in (q.get("interacts") or ()) if _verb(t) == "serve")


def serve_places() -> tuple:
    """Every register place with a counter somebody must stand behind."""
    return tuple(p["key"] for p in dr.PLACES if serve_tokens(p["key"]))


def behind_counter(place_key: str, world: World = None, species: str = "human",
                   n: int = 8):
    """Who is behind the counter here, as a resident.

    `resident.roster` casts a PLACE's regulars from each resident's own `job`,
    so this is not a new population -- it is the same people the room is
    already built with, filtered to the roles that serve. Returns None when
    nobody does, which is a real answer: `black_market`'s stall is not manned
    by anyone with a job in the register.
    """
    world = world or World()
    people = res.roster(place_key, world.hour, species, n)
    for r in people:
        if r.role in SERVE_ROLES and r.job == place_key:
            return r
    for r in people:
        if r.role in SERVE_ROLES:
            return r
    return None


# ===========================================================================
# 4g.  DLG-03 -- WHAT IS ACTUALLY BEHIND EACH COUNTER
# ===========================================================================
#
# THE ROW'S TEST IS SPECIFICITY, NOT VOLUME: *"Trade lines name their wares
# from the GDS-01 goods vocabulary -- a counter that trades in 'goods' fails
# the T1 specificity rule"*, and *"the Quartermaster does not sell spices"*.
# Before this table `serve_response()` returned `speak()`, whose trade line
# came from `PHRASE["trade"]`'s pool of THREE, shared by every counter on the
# station -- so the fence, the quartermaster and the spice pitch made the same
# sentence with a different place name in it.
#
# EACH ROW IS A COUNTER AND NAMES REAL WARES. `sells` are GDS-01 names
# (`docs/spec/PLACES.md` 0.3 -- spoo, brivari, flarn, G'Quan Eth, Jovian
# Sunspot, treel, jala, bagna cauda, salvage lots, breather cartridges,
# identicard blanks, Dust, aid-ration packs, water containers, pitch-fee
# scrip, Nightwatch pamphlets, drum staples, Vree optics, Drazi hardware
# grades, dock-grade tools); `short` is what this counter cannot get at the
# datum and `never` is what it will not stock at any price. Those last two are
# what make a counter a PLACE rather than an inventory: a person who tells you
# what they have not got has told you where you are.
#
# SIX LINES PER COUNTER, from six shapes over the row's own wares -- the pitch,
# the price, the provenance, the shortage, the refusal, and the haggle. 30
# counters x 6 = 180 distinct lines, and `_selftest` asserts the distinctness
# rather than assuming the wares differ.
#
# THE SPEC SAYS 29 COUNTERS ACROSS 27 PLACES AND THE REGISTER NOW HAS 30
# ACROSS 28. That is DRIFT and it is left standing: `docs/spec/PEOPLE.md`
# DLG-03 cites `interact.py:120-126` for its figures and a place has been
# added to the register since. Neither side may be edited to make the other
# pass (MASTER-PLAN R1), so this table covers what the register ACTUALLY has
# and the harness reports the two numbers side by side. INV-700.
_W = lambda sells, short, never, source: dict(                   # noqa: E731
    sells=sells, short=short, never=never, source=source)

COUNTER_WARES = {
    ("customs_north", "customs_desk"): _W(
        ("transit visas", "bonded-cargo seals", "declaration forms"),
        "same-day clearances, since the liner surge",
        "anything at all -- this is a desk, not a stall",
        "GDS-01 controlled classes + TRAFFIC-AND-CUSTOMS 5.2"),
    ("customs_south", "customs_desk"): _W(
        ("transit visas", "quarantine certificates", "bond releases"),
        "quarantine clearances for anything Markab-flagged",
        "the G'Quan Eth waiver -- that is a north-hall signature",
        "GDS-01 controlled classes + the Markab seal"),
    ("docking_bays", "bay_control_booth"): _W(
        ("berth allocations", "grapple time", "dock-grade tools on loan"),
        "a bay under tier three before the afternoon",
        "cargo -- take a manifest to the cargo desk",
        "SYS-02 berth map"),
    ("mess_hall", "serving_counter"): _W(
        ("drum staples", "orchard fruit off the 05:00 transfer", "flarn"),
        "treel, until the tanks come back up",
        "brivari, or anything else you could get drunk on",
        "GDS-01 drum staples + hydroponics"),
    ("zocalo", "market_stall"): _W(
        ("spoo", "jala", "Abbai wet-farm greens"),
        "spoo, and it will be short until the Narn routes reopen",
        "identicard blanks -- take that below and do not come back",
        "GDS-01 attested names; G'Dral's row, CAST-02 32"),
    ("zocalo", "shopfront"): _W(
        ("Vree instrument-grade optics", "Drazi duct-sealant",
         "breather cartridges"),
        "optics above grade four; the Vree hulls are standing off",
        "food of any kind -- that is the cloth two rows down",
        "GDS-01 hardware grades; CAST-02 34, 35"),
    ("bar_unnamed", "bar_counter"): _W(
        ("Jovian Sunspot", "brivari", "bagna cauda for anyone who asks twice"),
        "brivari, since the Centauri put a levy on it",
        "Dust. Not here, not ever, and you can ask outside",
        "GDS-01 bar_unnamed board; CAST-02 21"),
    ("dark_star", "bar_counter"): _W(
        ("brivari", "Jovian Sunspot", "jala for the Centauri tables"),
        "anything Narn, and the tables notice",
        "credit -- this house takes cash and takes it first",
        "GDS-01 Centauri drink; CAST-02 24, 25"),
    ("casino", "bar_counter"): _W(
        ("brivari", "house tokens", "Jovian Sunspot at the tables"),
        "nothing. The house is never short of anything you can drink",
        "a tab. The floor boss decides who runs one and she has decided",
        "GDS-01 + CAST-02 30"),
    ("security_central", "duty_desk"): _W(
        ("cautions", "property receipts", "identicard readings"),
        "cell space, on any night after a liner",
        "an opinion about the Ministry, at this desk or any other",
        "LAW-CRIME-DOWNBELOW 2.2"),
    ("ambassadorial_suites", "reception"): _W(
        ("appointments", "credentials", "the mission's own courtesies"),
        "an hour of the ambassador's day inside the month",
        "gifts. They are logged, and then they are declined",
        "FACTIONS.md 7.2, 8.1"),
    ("admin_complex", "desk"): _W(
        ("residency filings", "pitch-fee scrip", "docket numbers"),
        "a docket date inside three weeks",
        "an exception. This desk has never once made one",
        "FACTIONS.md 2.5"),
    ("quartermaster", "issue_counter"): _W(
        ("dock-grade tools", "breather cartridges", "issue kit against signature"),
        "cartridges above the reserve, until the next EarthForce transport",
        "spices, delicacies or drink -- this is an issue counter and it "
        "issues what the establishment says it issues",
        "GDS-01 dock-grade tools; CAST-02 14"),
    ("post_office", "counter"): _W(
        ("parcels off the liner", "bonded packets", "rack storage by the day"),
        "rack space, for the two days after every liner",
        "anything unlabelled. If it has no name on it, it does not come in",
        "CAST-02 15"),
    ("eclipse_cafe", "bar_counter"): _W(
        ("orchard fruit", "drum staples", "the A-watch handover breakfast"),
        "eggs, whenever the drum's birds are off",
        "alcohol before the evening. Ask next door",
        "GDS-01 drum staples; CAST-02 26"),
    ("shops_kiosks", "market_stall"): _W(
        ("breather cartridges", "Drazi hardware grades", "water containers"),
        "containers, since the standpipe queues doubled",
        "food. There is a whole concourse of it below",
        "GDS-01 hardware + standpipe economy"),
    ("shops_kiosks", "shopfront"): _W(
        ("Vree instrument-grade optics", "identicard wallets",
         "hydroponic specialty racks by order"),
        "the specialty racks, until PLC-026 logs the next cut",
        "anything I would have to explain to a customs officer",
        "GDS-01 hydroponics racks"),
    ("earthforce_office", "desk"): _W(
        ("service records", "pension filings", "transport berths"),
        "berths on anything outbound before the month's end",
        "civilian business. The concourse desk is two decks up",
        "FACTIONS.md 3.2"),
    ("league_delegations", "reception"): _W(
        ("anteroom appointments", "translated filings", "League standing lists"),
        "an anteroom slot, and the queue is by standing not by date",
        "a private word. Everything here is heard by everyone here",
        "FACTIONS.md 9.2; CAST-02 46"),
    ("drum_office", "desk"): _W(
        ("drum staples by consignment", "crop-board allocations",
         "orchard fruit lots"),
        "grain, until the next cut clears the boards",
        "retail. This office sells by the consignment or not at all",
        "PLC-110's 12 crop boards"),
    ("telepath_office", "desk"): _W(
        ("commercial scan bookings", "Corps filings", "sealed depositions"),
        "a resident telepath, since the posting closed",
        "an unlogged scan. There is no such thing and there never was",
        "FACTIONS.md 4; CAST-02 49"),
    ("maintenance", "workbench"): _W(
        ("Drazi duct-sealant", "dock-grade tools", "gasket stock by grade"),
        "sealant, because Grey took the last drum of it",
        "anything for a private job. Bring a works order",
        "GDS-01 hardware grades"),
    ("research_labs", "lab_bench"): _W(
        ("Vree instrument-grade optics", "sample cases",
         "Abbai wet-farm cultures"),
        "optics, and the whole programme is waiting on them",
        "specimens out of the building. Not signed, not carried",
        "GDS-01 Vree optics"),
    ("black_market", "stall"): _W(
        ("salvage lots", "identicard blanks", "Dust, if you already knew to ask"),
        "clean salvage. Everything on this cloth has a history",
        "aid-ration packs. I do not take food out of a queue",
        "GDS-01 contraband; CAST-02 41, 38"),
    ("core_shuttle", "counter"): _W(
        ("transit tokens", "drum-side consignment space",
         "pitch-fee scrip for the drum markets"),
        "space on the 05:00 transfer, every single morning",
        "livestock. It has been tried",
        "GDS-01 pitch-fee scrip"),
    ("earharts", "bar_counter"): _W(
        ("bagna cauda", "Jovian Sunspot", "EarthForce pension-day measures"),
        "bagna cauda, when the Earth consignment misses a liner",
        "anybody without a membership. The steward is sorry and he is not",
        "GDS-01 human/Italian; CAST-02 27"),
    ("happy_daze", "bar_counter"): _W(
        ("Jovian Sunspot", "Llort overnight stock", "brivari of a sort"),
        "anything you would put a name to after midnight",
        "questions. You drink here, you do not ask here",
        "GDS-01 + CAST-02 29"),
    ("security_posts", "duty_desk"): _W(
        ("cautions", "lost property", "Downbelow boundary passes"),
        "officers, on the C watch and every watch",
        "a favour. Not at a post, not with the log running",
        "LAW-CRIME-DOWNBELOW 2.2"),
    ("nightwatch", "duty_desk"): _W(
        ("Nightwatch pamphlets", "enrolment forms",
         "the supplementary allowance, paid weekly"),
        "nothing. The Ministry is never short",
        "an explanation. You are told, or you are not told",
        "FACTIONS.md 5"),
    ("minipax", "desk"): _W(
        ("Nightwatch pamphlets", "reporting terminals", "civic notices"),
        "patience, with people who file the same report twice",
        "a copy of what you filed. It is filed; that is the whole of it",
        "FACTIONS.md 5 and 13"),
}

# The six shapes. Each names a ware; none of them can say "goods".
_TRADE_SHAPE = (
    "The %(a)s is what people come to this counter for, and I have %(b)s and "
    "%(c)s besides.",
    "%(b)s is priced where it is because of what it costs me to have it here "
    "at all, with %(short)s the way it is. I am not moving on it.",
    "The %(c)s comes in the way everything comes in here -- %(source)s -- and "
    "when that stops, so do I.",
    "What I have not got is %(short)s. Ask me again next week and I will "
    "probably say the same.",
    "I do not sell %(never)s.",
    "You can have the %(a)s at the marked figure, or the %(c)s, and neither "
    "of them moves for anybody. Your choice.",
)


def counter_wares(place_key: str, token: str) -> dict:
    """What is actually behind this counter, or None if it is not a counter."""
    return COUNTER_WARES.get((place_key, token))


def counter_trade(place_key: str, token: str) -> tuple:
    """The six place-specific trade lines for one counter. DLG-03's floor."""
    w = counter_wares(place_key, token)
    if w is None:
        return ()
    a, b, c = (list(w["sells"]) + ["", "", ""])[:3]
    f = {"a": a, "b": b, "c": c, "short": w["short"], "never": w["never"],
         "source": w["source"]}
    return tuple(t % f for t in _TRADE_SHAPE)


def counter_line(place_key: str, token: str, turn: int = 0) -> str:
    """One trade line, without repeating inside the counter's six."""
    pool = counter_trade(place_key, token)
    if not pool:
        return None
    return _shuffle(pool, f"trade|{place_key}|{token}")[turn % len(pool)]


def trade_lines() -> dict:
    """DLG-03's census: every counter's six, keyed by counter. Computed."""
    return {(p, t): counter_trade(p, t)
            for p in serve_places() for t in serve_tokens(p)}


def serve_response(place_key: str, world: World = None,
                   listener: Listener = None, species: str = "human"):
    """The exchange `interact.py` says `serve` needs and could not have.

    This is the function that would let `serve` join `interact.RESPONDS`. That
    tuple lives in a file this session does not own, so the wiring is one word
    in `station/interact.py` and the check that it is earned is here.
    """
    world = world or World()
    who = behind_counter(place_key, world, species)
    if who is None:
        return None
    ex = speak(who, place_key, world, listener)
    # AND THE COUNTER SAYS WHAT IS ON IT. DLG-03: six place-specific trade
    # lines BEYOND the matrix cell, naming GDS-01 wares. Appended rather than
    # substituted, because the exchange above is the PERSON and this is the
    # COUNTER -- the same Narn merchant behind the spice pitch and behind the
    # fence gets his own voice from the cell or his cast row, and different
    # wares from here.
    tok = (serve_tokens(place_key) or ("",))[0]
    line = counter_line(place_key, tok, world.turn)
    if line:
        src = (f"dialogue.COUNTER_WARES[({place_key!r}, {tok!r})] -- "
               f"{counter_wares(place_key, tok)['source']}")
        ex = replace(ex, lines=ex.lines + (Line("npc", "speech", line, src),),
                     sources=ex.sources + (src,))
    return ex


# ===========================================================================
# 7.  The runtime sidecar
# ===========================================================================

def sidecar(actors, world: World = None, listener: Listener = None) -> list:
    """One row per baked actor, for `godot/scripts/dialogue.gd` to read.

    THE ACTOR LIST IS THE INPUT AND NOT A SECOND POPULATION. `populace._who`
    already writes every person's id, species and role into
    `<deck>_actors.json`, and `deck.py` copies it verbatim -- so the runtime's
    cast and this module's cast are the same people by construction. Building a
    roster here instead would have been a second description of who is aboard.
    """
    world = world or World()
    listener = listener or Listener()
    # THE AUDIENCE IS THE BAKED CROWD, COUNTED, NOT A PARAMETER SOMEBODY SETS.
    # DLG-06's Broker is audience-gated, and the only honest source for "who
    # else is in this room" is the actor list this function is already reading
    # -- the same bodies `populace` placed and `walk.gd` loads. Deriving it
    # from anything else would be a second description of the crowd.
    crowd = {}
    for a in actors:
        k = a.get("place") or (a.get("who") or {}).get("at_post") or ""
        crowd[k] = crowd.get(k, 0) + 1
    out = []
    for a in actors:
        who = a.get("who") or {}
        npc_id = who.get("id")
        if not npc_id:
            continue
        r = res.resident(npc_id, who.get("species", "human"))
        place = a.get("place") or who.get("at_post") or ""
        ex = speak(r, place,
                   replace(world, audience=crowd.get(place, 1)), listener)
        out.append({
            "group": a.get("group", ""),
            "id": npc_id,
            "name": prompt(r),
            "species": r.species,
            "role": r.role,
            "place": place,
            "hour": world.hour,
            # WHAT THEY GO BACK TO WHEN YOU STOP TALKING, at THIS take's hour.
            # `<deck>_actors.json` carries a `who.doing` too and it is the one
            # `populace` baked -- one hour, frozen, so a conversation held at
            # 03:00 ended with a dock worker going "back to work". This is the
            # same call `populace` makes, asked at the hour being baked.
            "doing": sched.activity_at(npc_id, r.species, world.hour).value,
            "topic": ex.topic,
            "band": BAND_NAME[ex.band],
            "lines": [{"who": ln.who, "kind": ln.kind, "text": ln.text}
                      for ln in ex.lines],
            # WHAT THE PLAYER MAY SAY. A row without it is an old sidecar and
            # `dialogue.gd` reads it exactly as it always did -- the key is
            # additive, like `cells=` in the COLDSTART verdict.
            "choice_at": ex.choice_at,
            "choices": [{"stance": c.stance, "text": c.text,
                         "yielded": c.yielded,
                         "reply": [{"who": ln.who, "kind": ln.kind,
                                    "text": ln.text} for ln in c.reply]}
                        for c in ex.choices],
            "sources": list(ex.sources),
        })
    return out


# WHICH HOURS GET BAKED, and why it is four rather than one.
#
# THE SIDECAR USED TO BE A PHOTOGRAPH. `speak` is a function of `world.hour`
# and `boot.py` baked it once at 13:00, so every derivation in this module --
# the species daypart, `schedule.activity_at`, `traffic.hall_rate`, the
# farewell's half-hour lookahead -- was frozen at one instant and the station's
# clock ran on underneath it. A resident said "I am due at the Zocalo" at
# 03:00 because he had been due there at 13:00 when the deck was built.
#
# Four is the schedule's own structure and not a round number: `npc/schedule`
# gives a human RHYTHM sleep/work/eat/leisure, and 03:00, 09:00, 13:00 and
# 19:00 are one sample inside each of the four. `dialogue.gd` takes the nearest
# on the ring, so a clock at 05:00 gets the 03:00 row rather than an average of
# two -- an averaged person is a person nobody is.
SIDECAR_HOURS = (3.0, 9.0, 13.0, 19.0)


def coverage(actors_path: str, sidecar_path: str):
    """How many of the deck's cast can actually speak. (spoke, cast, silent).

    THE GATE THAT DID NOT EXIST, AND THE FIRST THING IT FOUND WAS A STALE FILE
    RATHER THAN A CONTENT GAP -- which is why it reports the two apart.
    The shipped build printed `dialogue: 21 people can speak, of 84 in the
    cast`, and the obvious reading is that the cast grew and the writing did
    not. It is wrong. `sidecar()` emits a row for EVERY actor carrying a
    `who.id`, and all 84 carry one; the baked file was written on 2026-08-04
    against an actors file dated 2026-08-05. Re-baked, it is 336 rows and
    **84 of 84**. Nobody was mute; the artefact was old.

    That makes this the third artefact-staleness defect in the same family --
    `bootstrap._boot_has` (a boot.json missing the keys the gates read),
    `bootstrap._sidecars_carry` (interact sidecars predating four verb fields),
    and now this. A coverage ratio that nothing gates is a ratio that falls in
    the direction nobody re-checks.

    100% IS THE BAR AND IT IS REACHABLE, which is what makes it a fair one: it
    is not an aspiration, it is the state of every deck on disk right now.
    A resident the player can walk up to and who has nothing to say is a
    resident the scope document ("NPCs with names, species, roles and
    schedules -- not crowds, *residents*") says should not exist.
    """
    with open(actors_path) as f:
        cast = {a.get("group", "") for a in json.load(f) if a.get("who")}
    with open(sidecar_path) as f:
        spoke = {r.get("group", "") for r in json.load(f)}
    return len(cast & spoke), len(cast), sorted(cast - spoke)


def coverage_gate(out=print) -> bool:
    """Every baked deck's cast can speak, and the sidecar is not older than it.

    TWO CHECKS, BECAUSE ONE OF THEM CANNOT SEE THE OTHER'S FAILURE. Coverage
    alone passes on a stale pair that happen to agree; freshness alone passes
    on a current file that covers half the deck. The defect this was written
    for needed both to be visible at once.
    """
    import glob                                                   # noqa: PLC0415
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "generated", "scene", "deck")
    pairs = [(a, a.replace("_actors.json", "_dialogue.json"))
             for a in sorted(glob.glob(os.path.join(root, "*_actors.json")))]
    if not pairs:
        out("dialogue coverage: no baked deck on disk -- nothing to check. "
            "Run `python3 station/walkable.py --deck blue/0/0` first.")
        return True
    ok = True
    for a, d in pairs:
        name = os.path.basename(d)
        if not os.path.exists(d):
            out("  FAIL %-34s no sidecar beside its actors file" % name)
            ok = False
            continue
        spoke, cast, silent = coverage(a, d)
        stale = os.path.getmtime(d) < os.path.getmtime(a)
        note = ""
        if stale:
            note = ("  STALE: baked before its own actors file, so this number "
                    "describes an older cast")
            ok = False
        if spoke < cast:
            note += ("  %d silent, first: %s"
                     % (len(silent), ", ".join(silent[:3])))
            ok = False
        out("  %-4s %-34s %3d of %3d can speak%s"
            % ("ok" if spoke == cast and not stale else "FAIL", name,
               spoke, cast, note))
    out("dialogue coverage: %s -- the bar is 100%%, and it is reachable rather "
        "than aspirational: every deck on disk meets it today. A resident you "
        "can walk up to with nothing to say is one the scope forbids."
        % ("PASS" if ok else "FAIL"))
    return ok


def write_sidecar(actors_path: str, out_path: str, world: World = None,
                  hours=SIDECAR_HOURS) -> int:
    """Bake the exchanges beside the deck. Returns the row count.

    `hours=None` writes the single-hour form this function had before, which
    is what `--hour` on the command line asks for.
    """
    with open(actors_path) as f:
        actors = json.load(f)
    world = world or World()
    rows = []
    for h in (hours or (world.hour,)):
        rows += sidecar(actors, World(hour=h, day=world.day,
                                      datum=world.datum))
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=1)
    return len(rows)


# ===========================================================================
# 8.  Report
# ===========================================================================

# ===========================================================================
# 7b.  THE CONVERSATION GATE -- can a player talk back, and to how many?
# ===========================================================================
# WHY THIS GATE AND NOT ANOTHER COVERAGE COUNT. CLAUDE.md's session-4d ruling
# is that this project optimises what can be counted and a game cannot be
# expressed as a count, and the honest reading of that is NOT "stop counting".
# It is that the count must be of the thing a player does. `--selftest` above
# asks whether the derivation is sound -- 37 checks, every one of them about a
# table or a topic. NONE of them could fail for *"there is no way to answer"*,
# and for 2,139 lines there was none.
#
# So this asks four questions with DENOMINATORS, over the cast a player
# actually meets rather than a synthetic roster:
#
#   1. how many of the deck's people can be spoken to at all
#   2. how many DISTINCT things they open with     -- variety, not existence
#   3. how many offer the player a line back, and how many distinct player
#      lines exist                                 -- DLG-05, from zero
#   4. does the same person say the same thing at 03:00 and at 13:00
#
# AND THREE CONTROLS, because a gate that only runs the working configuration
# cannot tell a working thing from a lucky one. Every one of them removes a
# single mechanism and must break exactly the number that names it.
#
# WHAT IT LOOKED LIKE BEFORE THIS SESSION, run against the same casts:
# `utterances 0/94`, `distinct player lines 0`, `press yields 0 deflects 0`.
# The gate FAILS on that, which is the only reason to believe it.

# `docs/spec/PEOPLE.md` DLG-05's own arithmetic: 11 topics x 3 stances = 33,
# plus openers/closers, role work-lines and the papers/trade sets = 152. The
# floor is quoted rather than met, because quoting a floor you have not reached
# is honest and moving the floor to where you are is not.
DLG05_FLOOR = 152


def _cast_files():
    """Every baked cast on disk, newest deck first. The population, not a roster.

    A gate that built its own roster would be measuring `resident.roster` and
    calling it dialogue. These are the JSON files `populace.py` wrote and
    `godot/scripts/walk.gd` loads, so the people counted here are the people
    standing in the build.
    """
    import glob                                                  # noqa: PLC0415
    d = os.path.join(_HERE, "generated", "scene", "deck")
    return sorted(glob.glob(os.path.join(d, "*_actors.json")))


# WHERE THE CAST COMES FROM WHEN THERE IS NO DECK ON DISK.
#
# `station/generated/scene/` IS GITIGNORED, and this gate would otherwise be
# the fourth in this repository to depend on an artefact its own CI cannot
# rebuild -- the defect `--gate-frames` had with stale PNGs and `budget.py` had
# with a cached collision total. Building a deck takes twenty minutes and CI
# does not do it, so a gate that needs one is a gate that reports
# "NO BAKED CAST" on every push and is read as noise inside a month.
#
# So the fallback is a ROSTER over real register places -- the same
# `resident.roster` the deck baker itself casts rooms from, so it is the same
# people, just not yet placed against a mesh. It is WEAKER and the gate says
# which one it used on every run: the deck form additionally proves the join to
# `<deck>_actors.json` and the shipped manifest, and the roster form cannot.
#
# The places are the four the selftest already samples plus the two that carry
# the roles those four do not (an officer's beat, a cleric's hours), so every
# `PHRASE` row that a stance table has a row for can appear.
ROSTER_PLACES = (("zocalo", 10.0), ("customs_north", 9.0),
                 ("docking_bays", 14.0), ("downbelow", 2.0),
                 ("bar_unnamed", 20.0), ("security_posts", 6.0))
ROSTER_SPECIES = ("human", "narn", "centauri", "minbari", "drazi")


def _roster_cast(per=4):
    """A stand-in cast shaped exactly like `_cast`'s rows, from the register."""
    out = []
    for place, h in ROSTER_PLACES:
        for sp in ROSTER_SPECIES:
            for r in res.roster(place, h, sp, per):
                out.append(("(roster)", {
                    "group": f"{place}__{r.npc_id}",
                    "place": place,
                    "who": {"id": r.npc_id, "species": r.species},
                }))
    return out


def _cast(paths=None, cap=None):
    out = []
    for p in (paths if paths is not None else _cast_files()):
        try:
            with open(p) as f:
                rows = json.load(f)
        except Exception:                                        # noqa: BLE001
            continue
        for a in rows:
            who = a.get("who") or {}
            if who.get("id"):
                out.append((os.path.basename(p), a))
    # Deduplicate on (person, place): the same resident is baked into more than
    # one deck of one z-cluster, and counting them twice would inflate every
    # denominator below by a factor nobody could see.
    seen, uniq = set(), []
    for stem, a in out:
        k = (a["who"]["id"], a.get("place", ""))
        if k in seen:
            continue
        seen.add(k)
        uniq.append((stem, a))
    return uniq[:cap] if cap else uniq


def _exchange_for(a, hour, day=0, listener=None):
    who = a["who"]
    r = res.resident(who["id"], who.get("species", "human"))
    place = a.get("place") or who.get("at_post") or ""
    return speak(r, place, World(hour=hour, day=day), listener)


def converse(out=print, hours=(3.0, 13.0), cap=None):            # noqa: C901
    """The gate. Returns True if a player can hold a conversation on this deck."""
    cast = _cast(cap=cap)
    fails = []
    baked = bool(cast)
    if not baked:
        cast = _roster_cast()
        if cap:
            cast = cast[:cap]
    if not cast:
        out("converse: no cast could be assembled, baked or rostered")
        return False

    h_a, h_b = hours[0], hours[-1]
    ex_a = [_exchange_for(a, h_a) for _stem, a in cast]
    ex_b = [_exchange_for(a, h_b) for _stem, a in cast]
    n = len(cast)
    decks = sorted({s for s, _ in cast})

    # -- 1. who is here ---------------------------------------------------
    people = len({a["who"]["id"] for _s, a in cast})
    out("the cast: %s, %d distinct residents"
        % ((f"{n} placed bodies over {len(decks)} baked deck(s)" if baked
            else f"{n} rostered from {len(ROSTER_PLACES)} register places "
                 f"-- NO BAKED DECK in this checkout, so the join to "
                 f"<deck>_actors.json is NOT exercised"), people))

    # -- 2. what they open with -------------------------------------------
    def opener(ex):
        for ln in ex.lines:
            return ln.text
        return ""
    openers = {opener(e) for e in ex_b} - {""}
    # AND WHAT THEY ACTUALLY TELL YOU, which is the number that matters.
    # A greeting is drawn from three banded forms plus the withheld one, so its
    # ceiling is 4 BY CONSTRUCTION and reporting it alone would make a station
    # of 136 people look like it had four things to say. The topic line is the
    # one that names today's liner, this officer's beat or this stallholder's
    # counter, and it is the one a repeat would be felt in.
    tells = {e.lines[e.choice_at].text for e in ex_b if e.choice_at >= 0}
    out(f"openers: {len(openers)} distinct greetings (a banded table of "
        f"{len(GREET)} plus the withheld one -- 4 is its ceiling) over {n} "
        f"people, who then tell you {len(tells)} distinct things")
    if len(openers) < 2:
        fails.append(f"the whole cast opens {len(openers)} way(s)")
    if len(tells) < 8:
        fails.append(f"{n} people between them say {len(tells)} distinct "
                     f"things")

    # -- 3. CAN THE PLAYER SAY ANYTHING ------------------------------------
    with_choice = [e for e in ex_b if e.choices]
    said = {t for e in ex_b for t in e.said}
    out(f"player utterances: {len(with_choice)}/{n} exchanges offer one, "
        f"{len(said)} distinct player lines "
        f"(DLG-05 floor {DLG05_FLOOR}; this is not that yet)")
    if not with_choice:
        fails.append("NOT ONE exchange offers the player a line -- this is the "
                     "state the owner's session-4d ruling named")
    # A person who does not speak to you at all is the one legitimate zero, and
    # it is `friction`'s decision rather than a gap. Everybody else must be
    # answerable.
    silent = [e for e in ex_b if not e.choices]
    unexplained = [e for e in silent if e.topic not in ("refusal", "")]
    if unexplained:
        fails.append(f"{len(unexplained)} exchange(s) have a topic and no way "
                     f"to answer it: {sorted({e.topic for e in unexplained})}")
    if silent:
        out(f"  the {len(silent)} with nothing to answer are "
            f"{sorted({e.topic or '(no topic)' for e in silent})} -- "
            f"friction.PAIRS' refusals, which FACTIONS.md 12 calls a silence")
    else:
        out("  nobody on this cast is unanswerable; no refusal fires against "
            "a human listener here, which is the friction model's answer and "
            "not a gap")
    if len(said) < len(STANCES):
        fails.append(f"{len(said)} distinct player lines is below one full "
                     f"set of {len(STANCES)} stances")

    # -- 4. IS A STANCE WORTH ANYTHING -------------------------------------
    press = [c for e in ex_b for c in e.choices if c.stance == "press"]
    yes = [c for c in press if c.yielded]
    out(f"the press: {len(yes)}/{len(press)} yield the number that decided "
        f"their topic, {len(press) - len(yes)} deflect")
    if not yes or len(yes) == len(press):
        fails.append("the press has ONE outcome on this whole cast -- a stance "
                     "with one outcome is not a stance")
    # ...and what it is worth is a fact the first line did not carry.
    earned = 0
    for e in ex_b:
        first = " ".join(ln.text for ln in e.lines)
        for c in e.choices:
            if c.stance != "press" or not c.yielded:
                continue
            new = {w.strip(".,;:-") for r in c.reply
                   for w in r.text.split()} - {w.strip(".,;:-")
                                               for w in first.split()}
            if new:
                earned += 1
    out(f"  {earned}/{len(yes)} of those replies carry a word the exchange had "
        f"not already said")
    if earned < len(yes):
        fails.append(f"{len(yes) - earned} press(es) yield nothing new -- the "
                     f"stance is a rephrase")
    lets = [c for e in ex_b for c in e.choices if c.stance == "let_go"]
    if any(c.reply for c in lets):
        fails.append("let_go produced words -- dropping it must cost the "
                     "player the answer, or it is not a third option")

    # -- 5. THE HOUR --------------------------------------------------------
    moved = sum(1 for a, b in zip(ex_a, ex_b) if a.text() != b.text())
    said_a = {t for e in ex_a for t in e.said}
    out(f"the hour: {moved}/{n} say something different at "
        f"{h_a:05.2f} and {h_b:05.2f}; the player's own options move too "
        f"({len(said_a)} -> {len(said)} distinct)")
    if moved == 0:
        fails.append("nobody on the deck says anything different at 03:00 and "
                     "13:00 -- the exchange is not a function of the clock")

    # -- 6. AND IT REACHES THE BUILD ---------------------------------------
    # A DERIVATION THE RUNTIME CANNOT READ IS NOT IN THE GAME. `boot.py`'s
    # manifest names a `_dialogue.json` beside the deck it boots, and
    # `walk.gd::_wire_dialogue` returns without building the node when that
    # string is empty -- which is exactly what the shipped manifest held when
    # this gate was written, so every line above was true and NOBODY SPOKE.
    boot_p = os.path.join(_HERE, "generated", "scene", "boot.json")
    if not os.path.exists(boot_p):
        # SAID OUT LOUD, because a green run that silently skipped this clause
        # would read as "the shipped build speaks" and it would not have been
        # asked. `station/generated/scene/` is gitignored.
        out("the shipped build: NOT CHECKED -- no boot manifest in this "
            "checkout, so whether a player can reach any of the above is "
            "unanswered here. `python3 station/boot.py` writes it.")
    else:
        with open(boot_p) as f:
            man = json.load(f)
        side = man.get("dialogue", "")
        ok_side = bool(side) and os.path.exists(side)
        out(f"the shipped build: boot.json deck={man.get('deck', '?')!r} "
            f"dialogue={'-> ' + os.path.basename(side) if side else 'EMPTY'}"
            f"{'' if ok_side else '  <-- nobody speaks in the shipped build'}")
        if not ok_side:
            fails.append("the shipped boot manifest names no dialogue sidecar, "
                         "so walk.gd builds no Dialogue node and the whole "
                         "system is unreachable from the game")
        else:
            with open(side) as f:
                rows = json.load(f)
            hs = sorted({r.get("hour") for r in rows})
            with_c = sum(1 for r in rows if r.get("choices"))
            out(f"  {len(rows)} baked rows over hours {hs}, {with_c} carrying "
                f"player utterances")
            if with_c == 0:
                fails.append("the shipped sidecar carries no player utterances "
                             "-- rebuild it with `--sidecar`")

    # ------------------------------------------------------------------
    # CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")
    global SAY
    keep = dict(SAY)
    try:
        SAY = {}
        muted = [_exchange_for(a, h_b) for _s, a in cast[:40]]
        got = sum(len(e.choices) for e in muted)
        out(f"  with SAY emptied, the same 40 people offer {got} player "
            f"line(s) -- utterance gate {'FIRES' if got == 0 else 'DOES NOT '}"
            f"{'' if got == 0 else 'FIRE'}")
        if got != 0:
            fails.append("CONTROL: the player lines survive SAY being emptied")
    finally:
        SAY = keep

    global yields_to_press
    keepy = yields_to_press
    try:
        yields_to_press = lambda _reg: True                      # noqa: E731
        allyes = [c for _s, a in cast[:60]
                  for c in _exchange_for(a, h_b).choices
                  if c.stance == "press"]
        d_now = sum(1 for c in allyes if not c.yielded)
        out(f"  with every register forced to yield, {d_now} of "
            f"{len(allyes)} press(es) deflect -- register gate "
            f"{'FIRES' if d_now == 0 else 'DOES NOT FIRE'}")
        if d_now != 0:
            fails.append("CONTROL: deflection does not come from the register")
    finally:
        yields_to_press = keepy

    ex_same = [_exchange_for(a, h_b) for _s, a in cast]
    still = sum(1 for a, b in zip(ex_same, ex_b) if a.text() != b.text())
    out(f"  the same cast read twice at {h_b:05.2f} differs on {still} of {n} "
        f"-- clock gate {'FIRES' if still == 0 else 'DOES NOT FIRE'}")
    if still:
        fails.append("CONTROL: two reads of one hour disagree, so the hour "
                     "difference above is noise")

    for f in fails:
        out(f"  FAIL {f}")
    out(f"\nconverse: {'PASS' if not fails else 'FAIL'}")
    return not fails


def _show(ex: Exchange, out=print, prov=True):
    who = ex.name or f"[unnamed {ex.species}]"
    out(f"  {who} -- {ex.species}/{ex.role} at {ex.place} "
        f"{ex.hour:05.2f} EMT  [{ex.topic}, {BAND_NAME[ex.band]}]")
    for ln in ex.lines:
        mark = '"' if ln.kind == "speech" else "*"
        body = ln.text if ln.kind == "speech" else ln.text
        out(f"      {mark}{body}{mark if ln.kind == 'speech' else '*'}")
        if prov:
            out(f"           <- {ln.source}")


def report(out=print):                                          # noqa: C901
    w = World(hour=10.0, day=0)
    out(f"DIALOGUE at datum {cos.ERA_DATUM}, {len(TOPICS)} topics, "
        f"{len(_ROLE_REGISTER)} role registers x {len(_SPECIES_VOICE)} "
        f"species voices")
    out("")
    out("A CORRIDOR AT THE ZOCALO, 10:00 EMT")
    for r in res.roster("zocalo", w.hour, "human", 3):
        _show(speak(r, "zocalo", w), out)
        out("")

    out("THE COMPETITION -- every topic that applied, and what scored it")
    one = res.roster("customs_north", 10.0, "human", 1)
    if one:
        ld0 = next((n for n in range(8) if tf.liner_today(n)), 0)
        la0 = next((a for a in tf.arrivals(ld0) if a["type"] == "liner"), None)
        ww0 = World(hour=(la0["hour"] + 0.2) if la0 else 10.0, day=ld0)
        s0 = _speaker(one[0], "customs_north")
        for t in rank(s0, Listener(), ww0):
            out(f"  {t['salience']:6.2f}  {t['key']:8s} {t['source'][:88]}")
        out(f"  -> drew [{speak(one[0], 'customs_north', ww0).topic}]")
    out("")

    out("THE SAME PERSON, TWO ERAS -- nothing else changed")
    # A Narn at the refugee reception, because 6.2's 13,000 are the population
    # the surrender created and the era row lands on them hardest.
    narn = (res.roster("refugee_reception", w.hour, "narn", 1)
            or res.roster("zocalo", w.hour, "narn", 1))
    if narn:
        for dm, label in (((2, 1), "S2E01"), ((3, 5), "S3E05, the datum")):
            ex = speak(narn[0], "refugee_reception",
                       World(hour=w.hour, datum=dm))
            out(f"  {label}: {ex.text()}")
    out("")

    out("THE SAME PERSON, TWO LISTENERS -- friction is the whole difference")
    if narn:
        for li, label in ((Listener(), "a human visitor"),
                          (Listener(species="centauri", role="financier"),
                           "a Centauri")):
            ex = speak(narn[0], "zocalo", w, li)
            out(f"  to {label}: [{ex.topic}] {ex.text()}")
    out("")

    out("A LINER DAY AT THE NORTH CUSTOMS HALL -- the port sets the topic")
    ld = next((n for n in range(8) if tf.liner_today(n)), 0)
    la = next((a for a in tf.arrivals(ld) if a["type"] == "liner"), None)
    off = res.roster("customs_north", 10.0, "human", 4)
    if la and off:
        for d, lbl in ((ld, "liner day"),
                       (next((n for n in range(8) if not tf.liner_today(n)), 1),
                        "no liner")):
            ww = World(hour=la["hour"] + 0.2, day=d)
            ex = speak(off[0], "customs_north", ww)
            r = tf.hall_rate(ww.hour, d)
            out(f"  {lbl:10s} hall x{r['multiple']:.1f}  [{ex.topic}] "
                f"{ex.text()}")
    out("")

    out("DOWNBELOW, 02:00")
    for r in res.roster("downbelow", 2.0, "human", 2):
        _show(speak(r, "downbelow", World(hour=2.0)), out, prov=False)
    out("")

    out(f"THE `serve` VERB: {len(serve_places())} register places declare a "
        f"counter and had nobody behind it")
    for k in ("zocalo", "earharts", "customs_north", "post_office"):
        ex = serve_response(k, World(hour=13.0))
        if ex is None:
            out(f"  {k:16s} NOBODY")
        else:
            said = [ln.text for ln in ex.spoken] or [ex.lines[0].text]
            out(f"  {k:16s} {ex.name or ex.species} ({ex.role}, "
                f"{serve_tokens(k)[0]}): {said[-2] if len(said) > 2 else said[0]}")


# ===========================================================================
# 9.  Gates
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _probe(role: str, species: str = "human", psi: bool = False) -> _Speaker:
    """A synthetic speaker with exactly one role and one species.

    THE SAMPLE CANNOT COVER THE TABLES AND A GATE THAT USES ONE IS LYING ABOUT
    ITS COVERAGE. Security is 500 people in 155,000 (0.32%) and the Vorlon is
    one; sixteen residents drawn from two rooms contained four roles, so the
    first version of the minimality test reported 18 of 19 role rows inert when
    what it had actually measured was that 15 of them never appeared. A probe
    puts one speaker in every cell of both tables.
    """
    return _Speaker(npc_id=f"probe/{species}/{role}", species=species,
                    role=role, place="zocalo", job="zocalo",
                    home="qtr_civilian", eats_at="", prays_at="",
                    commutes_via="", visas="", licensed_psi=psi, name="Probe")


@__import__("functools").lru_cache(maxsize=64)
def _sample(place="zocalo", hour=10.0, species="human", n=6):
    """A place's regulars. Cached: `resident.roster` scans an id pool to find
    them and the gates below ask for the same four rooms many times over."""
    return tuple(res.roster(place, hour, species, n))


def _reg_tuple(r: Register) -> tuple:
    """A register as a comparable value -- what a table row can change."""
    return (round(r.formality, 6), round(r.terseness, 6), r.band)


def _texts(people, place, world, listener=None):
    return [speak(r, place, world, listener).text() for r in people]


def _selftest(out=print):                                       # noqa: C901
    global _SPECIES_VOICE, _ROLE_REGISTER, PERSONAL
    del _FAILED[:]
    n = 0
    w = World(hour=10.0, day=0)

    # -- the tables are TOTAL --------------------------------------------
    n += 1
    missing = [r.key for r in sched.ROLES if r.key not in _ROLE_REGISTER]
    check(not missing, "every schedule.ROLES key has a register row",
          f"{missing}")
    n += 1
    extra = [k for k in _ROLE_REGISTER if k not in sched.ROLES_BY_KEY]
    check(not extra, "and no register row names a role that does not exist",
          f"{extra}")
    n += 1
    miss_sp = [s for s in sched.ROLE_WEIGHTS if s not in _SPECIES_VOICE]
    check(not miss_sp, "every species in ROLE_WEIGHTS has a voice row",
          f"{miss_sp}")
    n += 1
    check(all(k in ERA_PHRASE for k in
              {(e, who) for e, who, _ in _ERA_ROWS}),
          "every era row has a phrasing in all three bands")
    n += 1
    check(all(len(v) == 3 for v in list(PHRASE.values())
              + list(ERA_PHRASE.values())),
          "every phrasing has exactly one form per voice band")
    n += 1
    keys = {k for k, _ in TOPICS} - {"refusal"}
    check(keys <= set(PHRASE), "every topic that speaks has a phrasing",
          f"{keys - set(PHRASE)}")

    # -- it varies by SPECIES, and here is the control --------------------
    ids = [r.npc_id for r in _sample(n=4)]
    n += 1
    by_species = {}
    for spk in ("human", "narn", "minbari", "drazi", "centauri"):
        r = res.resident(ids[0], spk)
        by_species[spk] = speak(r, "zocalo", w).text()
    check(len(set(by_species.values())) >= 4,
          "the SAME id speaks differently as five different species",
          f"{len(set(by_species.values()))} distinct of 5")
    n += 1
    # ... and it varies by ROLE, holding species and id fixed.
    by_role = {}
    for r in _sample(n=14):
        by_role.setdefault(r.role, set()).add(speak(r, "zocalo", w).text())
    check(len(by_role) >= 3 and len({t for v in by_role.values() for t in v})
          >= len(by_role),
          "and different roles in one room produce different lines",
          f"{sorted(by_role)}")

    # -- it varies by FACTION STANDING -----------------------------------
    n += 1
    nrn = res.resident(ids[0], "narn")
    to_human = speak(nrn, "zocalo", w, Listener())
    to_cent = speak(nrn, "zocalo", w,
                    Listener(species="centauri", role="financier"))
    check(to_cent.topic == "refusal" and to_human.topic != "refusal",
          "a Narn speaks to a human and REFUSES a Centauri -- FACTIONS.md 12, "
          "severity highest", f"{to_human.topic} vs {to_cent.topic}")
    n += 1
    check(all(ln.kind == "action" for ln in to_cent.lines),
          "and the refusal is an ACTION, not invented words for a silence the "
          "source calls 'neither speaks'")
    n += 1
    psi_to = speak(res.resident(ids[0], "human"), "zocalo", w,
                   Listener(psi=True))
    plain_to = speak(res.resident(ids[0], "human"), "zocalo", w, Listener())
    check(psi_to.text() != plain_to.text(),
          "and a telepath in the room changes what a human says to you -- "
          "FACTIONS.md 12's Psi badge row")

    # -- it varies by ERA -------------------------------------------------
    n += 1
    early = speak(nrn, "zocalo", World(hour=10.0, datum=(2, 1)))
    late = speak(nrn, "zocalo", World(hour=10.0, datum=(3, 5)))
    check(early.text() != late.text(),
          "the same Narn says different things before and after the surrender",
          f"{early.topic} vs {late.topic}")
    n += 1
    # WHICH era row he draws is his own hash's business; that there IS one at
    # the datum and NONE before it is the era lock, and that is what is
    # asserted. Naming the row would be a gate that passes or fails on an id.
    nsp = _speaker(nrn, "zocalo")
    r_late = {t["key"] for t in rank(nsp, Listener(),
                                     World(hour=10.0, datum=(3, 5)))}
    r_early = {t["key"] for t in rank(nsp, Listener(),
                                      World(hour=10.0, datum=(2, 1)))}
    check("era" in r_late and "era" not in r_early,
          "and the difference is an era topic that exists at the datum and "
          "does not exist at S2E01 -- costume.ERA_EVENTS, not a hash",
          f"{sorted(r_late)} vs {sorted(r_early)}")
    n += 1
    _w35 = World(hour=10.0, datum=(3, 5))
    evt = _topic_era(nsp, Listener(), _w35,
                     register(nsp, Listener(), _w35))
    check(evt is not None and "costume.ERA_EVENTS" in evt["source"],
          "and it cites the event by name in its provenance",
          f"{(evt or {}).get('source')}")
    n += 1
    same = speak(nrn, "zocalo", World(hour=10.0, datum=(3, 5)))
    check(same.text() == late.text(),
          "CONTROL: two identical datums produce identical text, so the "
          "difference above is the era and not noise")

    # -- it varies by WHAT THE STATION IS DOING ---------------------------
    n += 1
    ld = next((d for d in range(8) if tf.liner_today(d)), None)
    nold = next((d for d in range(8) if not tf.liner_today(d)), None)
    check(ld is not None and nold is not None,
          "a liner day and a linerless day both occur within a week")
    if ld is not None and nold is not None:
        la = next(a for a in tf.arrivals(ld) if a["type"] == "liner")
        cust = _sample("customs_north", 10.0, "human", 6)
        hh = la["hour"] + 0.2
        n += 1
        a_txt = _texts(cust, "customs_north", World(hour=hh, day=ld))
        b_txt = _texts(cust, "customs_north", World(hour=hh, day=nold))
        check(a_txt != b_txt,
              "the same officers at the same hour say different things on a "
              "liner day", f"{a_txt[0][:50]!r}")
        n += 1
        r_on = tf.hall_rate(hh, ld)["multiple"]
        r_off = tf.hall_rate(hh, nold)["multiple"]
        check(r_on > r_off,
              "and the reason is traffic.hall_rate's own surge multiple",
              f"x{r_on:.1f} vs x{r_off:.1f}")
        n += 1
        c_txt = _texts(cust, "customs_north", World(hour=hh, day=ld))
        check(a_txt == c_txt,
              "CONTROL: the same world state twice gives the same lines")

    # -- and by the HOUR --------------------------------------------------
    n += 1
    day_txt = _texts(_sample(n=5), "zocalo", World(hour=10.0))
    night_txt = _texts(_sample(n=5), "zocalo", World(hour=2.0))
    check(day_txt != night_txt,
          "the same people say different things at 02:00 and 10:00")
    n += 1
    # THE SPECIES CLOCK. A Brakiri sleeps from 09:00 (RHYTHMS, authority 4), so
    # at 13:00 they are late in their own day and a human is at midday.
    check(daypart("brakiri", 13.0) != daypart("human", 13.0),
          "a Brakiri and a human are at different points of THEIR OWN day at "
          "the same station hour",
          f"{daypart('brakiri', 13.0)} vs {daypart('human', 13.0)}")
    n += 1
    check(_GREET_WORD[daypart("brakiri", 13.0)]
          != _GREET_WORD[daypart("human", 13.0)],
          "and they greet you with different words because of it",
          f"{_GREET_WORD[daypart('brakiri', 13.0)]} vs "
          f"{_GREET_WORD[daypart('human', 13.0)]}")

    # -- every line is traceable ------------------------------------------
    n += 1
    ex = speak(_sample(n=1)[0], "zocalo", w)
    check(all(ln.source for ln in ex.lines),
          "every line carries the call that supplied its facts")
    n += 1
    mods = {"traffic", "broadcast", "schedule", "resident", "friction",
            "security", "costume", "directory", "interact", "register"}
    bad = [ln.source for ln in ex.lines
           if not any(m in ln.source for m in mods)]
    check(not bad, "and each source names a module in this repository",
          f"{bad}")

    # -- the station does not say one thing -------------------------------
    n += 1
    many = []
    for place, hour in (("zocalo", 10.0), ("customs_north", 9.0),
                        ("docking_bays", 14.0), ("downbelow", 2.0)):
        many += _texts(_sample(place, hour, "human", 6), place,
                       World(hour=hour))
    uniq = len(set(many)) / max(1, len(many))
    check(uniq >= 0.60,
          "across four places, most people say something different",
          f"{len(set(many))}/{len(many)} distinct = {uniq:.2f}")

    # -- serve: the verb interact.py could not close ----------------------
    n += 1
    sp_places = serve_places()
    check(len(sp_places) >= 20,
          "the register declares counters in many places",
          f"{len(sp_places)}")
    n += 1
    manned = [k for k in sp_places[:14]
              if serve_response(k, World(hour=13.0)) is not None]
    check(len(manned) >= 10,
          "and somebody is behind most of them, by name",
          f"{len(manned)}/14")
    n += 1
    # THIS ASSERTION WAS WRITTEN INVERTED, ON PURPOSE, AND HAS NOW FLIPPED.
    # `interact.RESPONDS` excluded `serve` because "being served needs whoever
    # is behind the counter to turn round and talk, which needs dialogue", and
    # this module could not edit that file. So it asserted the EXCLUSION -- a
    # change detector, so the day somebody wired it up the gate would say so
    # rather than the two files drifting apart in silence.
    #
    # It said so. Session 4e added `serve` at integration and this fired on the
    # next run. It now asserts the other direction: `serve` responds, and what
    # responds to it is THIS module.
    import interact as _it
    check("serve" in _it.RESPONDS,
          "interact.RESPONDS lists `serve` -- and `serve_response()` is what "
          "answers it")
    n += 1
    check(_it.verb_of("bar_counter") == "serve"
          and "serve" in _it.PRESSABLE,
          "...and a counter still resolves to it, pressably",
          f"{_it.verb_of('bar_counter')}")

    # -- the Vorlon -------------------------------------------------------
    n += 1
    kosh = res.resident("res:b5:vorlon:0", "vorlon")
    kex = speak(kosh, "council_chamber", w)
    check(kex.band == BAND_FORMAL or all(len(ln.text) < 90 for ln in kex.lines),
          "the Vorlon does not make a speech", f"{kex.text()!r}")

    # ==================================================================
    # THE DLG FLOORS AND CEILINGS -- and every one is IDENTITY, not a
    # threshold. `deck.py --degeneracy`'s argument transferred to text: two
    # speakers whose line sets hash the same ARE one speaker, and no
    # tolerance has to be chosen or defended.
    # ==================================================================
    cells = occupied_cells()
    n += 1
    check(len(cells) == 79, "the tier-2 matrix has 79 occupied cells "
                            "(schedule.ROLE_WEIGHTS)", f"{len(cells)}")
    n += 1
    sizes = {len(cell_lines(sp, r)) for sp, r in cells}
    check(sizes == {30}, "every cell can say 30 things "
                         "(11 topics x 2 frames + 4 greet + 4 part)",
          f"{sorted(sizes)}")
    n += 1
    flat = [l for sp, r in cells for l in cell_lines(sp, r)]
    dupe = {l for l in flat if flat.count(l) > 1} if len(set(flat)) != len(flat) \
        else set()
    check(len(set(flat)) == len(flat) == 2370,
          f"{len(flat)} tier-2 lines, all distinct across the 79 cells",
          f"{len(flat) - len(set(flat))} shared, e.g. {sorted(dupe)[:2]}")
    n += 1
    holes = [(sp, r) for sp, r in cells
             if r not in ROLE_CLAUSE or sp not in SPECIES_FRAME]
    check(not holes, "no occupied cell is missing its clause or its frame",
          f"{holes[:4]}")
    n += 1
    worst = min(lines_before_repeat(sp, r, "probe") for sp, r in cells)
    check(worst >= 20, f"lines before a cell repeats itself is {worst}, "
                       f"over the annex's floor of 20", f"{worst}")

    # -- DLG-01: the fifty, 75 each, and no string in two sets -----------
    roster = cast_roster()
    n += 1
    check(len(roster) == 50, "CAST-02 parses to 50 rows from the annex",
          f"{len(roster)}")
    n += 1
    per = {len(cast_lines(r)) for r in roster}
    check(per == {75}, "every Tier-1 cast member has 75 lines", f"{sorted(per)}")
    n += 1
    cflat = [l for r in roster for l in cast_lines(r)]
    check(len(set(cflat)) == len(cflat) == 3750,
          f"{len(cflat)} Tier-1 lines and no string appears in two NPCs' sets",
          f"{len(cflat) - len(set(cflat))} shared")
    n += 1
    # AND THEY ARE NOT THE TIER-2 LINES EITHER. A cast member who fell back to
    # the matrix would pass the count above and be nobody in particular.
    check(not (set(cflat) & set(flat)),
          "no Tier-1 line is also a tier-2 matrix line",
          f"{len(set(cflat) & set(flat))} shared")

    # -- DLG-05: 152, and the 96 are two lists multiplied ----------------
    n += 1
    pl = player_lines()
    tot = sum(len(v) for v in pl.values())
    check(tot == 152 and len({x for v in pl.values() for x in v}) == 152,
          f"{tot} distinct player lines "
          f"({', '.join(f'{k} {len(v)}' for k, v in pl.items())})", f"{tot}")
    n += 1
    import interact as _iv                                       # noqa: PLC0415
    check(tuple(_iv.VERBS) == SHIFT_VERBS,
          "the shift verbs ARE interact.VERBS, in order",
          f"{tuple(_iv.VERBS)}")
    n += 1
    grid = [(r, v) for r in PLAYER_ROLES for v in SHIFT_VERBS
            if (r, v) not in WORK_LINE]
    check(not grid, f"the work grid is {len(PLAYER_ROLES)} roles x "
                    f"{len(SHIFT_VERBS)} verbs with no hole", f"{grid[:4]}")
    n += 1
    # The twelve roles are the annex's ROLE-01..12, counted from the annex.
    _rh = len(re.findall(r"^### ROLE-\d+", open(CAST_ANNEX, encoding="utf-8")
                         .read(), re.M))
    check(_rh == len(PLAYER_ROLES),
          f"PLAYER_ROLES matches the annex's {_rh} ROLE- headings",
          f"{len(PLAYER_ROLES)}")

    # -- DLG-03: the counters, and what is actually on them --------------
    n += 1
    tl = trade_lines()
    tflat = [x for v in tl.values() for x in v]
    check(len(set(tflat)) == len(tflat) and all(len(v) == 6 for v in tl.values()),
          f"{len(tl)} counters x 6 = {len(tflat)} place-specific trade lines, "
          f"all distinct", f"{len(tflat) - len(set(tflat))} shared")
    n += 1
    bare = [k for k, v in tl.items() if not v]
    check(not bare, "every counter in the register has named wares", f"{bare}")
    n += 1
    # THE ROW'S OWN EXAMPLE, ASSERTED: "the Quartermaster does not sell spices".
    qm = " ".join(counter_trade("quartermaster", "issue_counter"))
    zc = " ".join(counter_trade("zocalo", "market_stall"))
    check("I do not sell spices" in qm and "spoo" in zc,
          "the Quartermaster refuses spices and the Zocalo pitch names spoo",
          f"{qm[:60]!r}")
    n += 1
    # AND NO COUNTER TRADES IN "goods" -- the row's T1 specificity rule.
    vague = [k for k, v in tl.items()
             if any(re.search(r"\bgoods\b|\bitems\b|\bwares\b", x)
                    for x in v)]
    check(not vague, "no counter anywhere trades in unnamed 'goods'",
          f"{vague[:3]}")
    n += 1
    # AND IT REACHES THE PLAYER. `serve_response` is the shipped caller.
    _sr = serve_response("quartermaster", World(hour=10.0))
    check(_sr is not None
          and any(l.text in counter_trade("quartermaster", "issue_counter")
                  for l in _sr.lines),
          "serve_response() puts the counter's own wares in the exchange",
          f"{_sr and [l.text[:40] for l in _sr.lines]}")

    # -- DLG-06: the two ceilings ---------------------------------------
    n += 1
    check(len(set(KOSH_LINES)) == len(KOSH_LINES) <= 12,
          f"the Kosh pool is {len(KOSH_LINES)}, at or under the ceiling of 12",
          f"{len(KOSH_LINES)}")
    n += 1
    _k = _Speaker("kosh", "vorlon", "envoy", "council_chamber", "", "", "", "",
                  "", "", False, "")
    said = [scarce_line(_k, World(session="probe", turn=t))[0]
            for t in range(len(KOSH_LINES) + 3)]
    spoke = [x for x in said if x]
    check(len(set(spoke)) == len(spoke) == len(KOSH_LINES)
          and not any(said[len(KOSH_LINES):]),
          f"a session hears {len(spoke)} distinct Kosh lines and then silence",
          f"{len(spoke)} spoken, {len(set(spoke))} distinct")
    n += 1
    check(len({t for _g, t in BROKER_LINES}) == len(BROKER_LINES) <= 20,
          f"the Broker pool is {len(BROKER_LINES)}, at or under 20",
          f"{len(BROKER_LINES)}")
    n += 1
    check(not (set(broker_lines(True)) & set(broker_lines(False)))
          and broker_lines(True) and broker_lines(False),
          "the Broker says different things alone and in front of a room",
          f"{len(broker_lines(True))} / {len(broker_lines(False))}")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")

    # -- THE DLG POOLS, BROKEN ON PURPOSE -------------------------------
    # Each of the three counts above is shown failing, because a count that
    # has never been seen to fail is a count nobody has tested.
    global SPECIES_FRAME, _CAST_TOPIC
    _keepf = dict(SPECIES_FRAME)
    SPECIES_FRAME = {k: SPECIES_FRAME["human"] for k in SPECIES_FRAME}
    _f2 = [l for sp, r in cells for l in cell_lines(sp, r)]
    out(f"  with every species frame collapsed onto human's, the 79 cells "
        f"fall from {len(set(flat))} distinct lines to {len(set(_f2))} -- "
        f"tier-2 identity gate FIRES")
    SPECIES_FRAME = _keepf
    _keept = dict(_CAST_TOPIC)
    _CAST_TOPIC = dict(_CAST_TOPIC,
                       trade=("It is a counter. Things are sold at it.",) * 3)
    _c2 = [l for r in roster for l in cast_lines(r)]
    out(f"  with one cast topic written generically, the fifty fall from "
        f"{len(set(cflat))} distinct lines to {len(set(_c2))} -- the "
        f"no-two-identical rule FIRES on {len(_c2) - len(set(_c2))} strings")
    _CAST_TOPIC = _keept
    global COUNTER_WARES
    _keepw = dict(COUNTER_WARES)
    COUNTER_WARES = {k: dict(v, sells=("goods", "goods", "goods"))
                     for k, v in COUNTER_WARES.items()}
    _t2 = [x for v in trade_lines().values() for x in v]
    out(f"  with every counter selling \"goods\", the 30 counters fall from "
        f"{len(set(tflat))} distinct trade lines to {len(set(_t2))} and the "
        f"specificity rule FIRES on the word itself")
    COUNTER_WARES = _keepw
    _kl = KOSH_LINES
    out(f"  a Kosh pool of {len(_kl)} would break the <=12 ceiling at "
        f"{len(_kl) + 1}: the check is `<= 12` and reads len(KOSH_LINES), so "
        f"a thirteenth line fails it without any tolerance to argue about")

    # -- THE VOICE TABLE'S OWN CONTRIBUTION, isolated --------------------
    # Flattening `_SPECIES_VOICE` does NOT make five species say the same
    # thing, and that is correct rather than a failure: species also reaches
    # the line through `RHYTHMS` (their own daypart) and through `_ERA_ROWS`.
    # So the control is on the thing this table alone decides -- the band.
    keep = dict(_SPECIES_VOICE)
    bands_live = {k: register(_probe("merchant", k), Listener(), w).band
                  for k in keep}
    try:
        _SPECIES_VOICE = {k: _DEFAULT_VOICE + ("flat",) for k in keep}
        bands_flat = {k: register(_probe("merchant", k), Listener(), w).band
                      for k in keep}
    finally:
        _SPECIES_VOICE = keep
    out(f"  with every species voice flattened, 15 species in one role fall "
        f"from {len(set(bands_live.values()))} distinct band(s) to "
        f"{len(set(bands_flat.values()))} -- voice-table gate "
        f"{'FIRES' if len(set(bands_flat.values())) == 1 else 'DOES NOT FIRE'}")
    n += 1
    check(len(set(bands_live.values())) >= 2
          and len(set(bands_flat.values())) == 1,
          "the voice band varies by species and stops varying when the table "
          "is flattened",
          f"{sorted(set(bands_live.values()))} -> "
          f"{sorted(set(bands_flat.values()))}")

    # -- MINIMALITY, EXHAUSTIVELY, ONE ROW AT A TIME ---------------------
    # `_probe` puts a speaker in every cell of both tables, which a roster
    # cannot: the first version of this measured a sixteen-person sample from
    # two rooms, found four roles in it, and reported the other fifteen rows
    # "inert" when what it had measured was that they never appeared.
    dead_role = []
    keep_r = dict(_ROLE_REGISTER)
    base_r = {k: _reg_tuple(register(_probe(k), Listener(), w))
              for k in keep_r}
    try:
        for k in keep_r:
            _ROLE_REGISTER = dict(keep_r)
            _ROLE_REGISTER[k] = _DEFAULT_ROLE + ("neutralised",)
            if _reg_tuple(register(_probe(k), Listener(), w)) == base_r[k]:
                dead_role.append(k)
    finally:
        _ROLE_REGISTER = keep_r
    out(f"  neutralising each of the {len(keep_r)} role rows in turn: "
        f"{len(keep_r) - len(dead_role)} change that role's register, "
        f"{len(dead_role)} do not ({', '.join(dead_role) or '-'})")
    n += 1
    check(not dead_role,
          "every role row earns its place -- neutralise it and a speaker in "
          "that role speaks differently", f"{dead_role}")

    dead_sp = []
    keep_s = dict(_SPECIES_VOICE)
    base_s = {k: _reg_tuple(register(_probe("merchant", k), Listener(), w))
              for k in keep_s}
    try:
        for k in keep_s:
            _SPECIES_VOICE = dict(keep_s)
            _SPECIES_VOICE[k] = _DEFAULT_VOICE + ("neutralised",)
            if (_reg_tuple(register(_probe("merchant", k), Listener(), w))
                    == base_s[k]):
                dead_sp.append(k)
    finally:
        _SPECIES_VOICE = keep_s
    out(f"  neutralising each of the {len(keep_s)} species rows in turn: "
        f"{len(keep_s) - len(dead_sp)} change that species' register, "
        f"{len(dead_sp)} do not ({', '.join(dead_sp) or '-'})")
    n += 1
    # `human` and `other` carry (0, 0) BY DESIGN and say so on the row: the
    # human register is the reference the other fourteen are offsets from, and
    # FACTIONS.md 9.2's tail bucket is not a species. Any THIRD inert row is a
    # row with no consequence, and this is what would catch it.
    check(set(dead_sp) <= {"human", "other"},
          "the only inert species rows are the two documented as the "
          "reference and the tail bucket", f"{sorted(dead_sp)}")

    keepf = fr.PAIRS
    try:
        fr.PAIRS = ()
        cold = speak(nrn, "zocalo", w,
                     Listener(species="centauri", role="financier"))
        out(f"  with friction.PAIRS emptied, a Narn meeting a Centauri says "
            f"[{cold.topic}] -- refusal gate "
            f"{'FIRES' if cold.topic != 'refusal' else 'DOES NOT FIRE'}")
        n += 1
        check(cold.topic != "refusal",
              "the refusal gate depends on friction.PAIRS")
    finally:
        fr.PAIRS = keepf

    keepp = dict(PERSONAL)
    try:
        # Drive every personal floor above any event's salience: the topics
        # must stop tracking the port, which is what proves the port topic was
        # winning on the SIMULATION's number and not on a coin.
        PERSONAL = {k: 99.0 for k in keepp}
        if ld is not None:
            cust = _sample("customs_north", 10.0, "human", 6)
            hh = next(a for a in tf.arrivals(ld) if a["type"] == "liner")
            hh = hh["hour"] + 0.2
            forced = _texts(cust, "customs_north", World(hour=hh, day=ld))
            same_now = (forced == _texts(cust, "customs_north",
                                         World(hour=hh, day=nold)))
            out(f"  with the personal floors raised above every event, the "
                f"liner day and the quiet day read "
                f"{'THE SAME' if same_now else 'differently'} -- liner gate "
                f"{'FIRES' if same_now else 'DOES NOT FIRE'}")
            n += 1
            check(same_now,
                  "the liner gate depends on the port topic outranking a life")
    finally:
        PERSONAL = keepp

    # DETERMINISM, the way resident.py proves it: two hash seeds, one diff.
    n += 1
    import subprocess
    prog = ("import sys; sys.path.insert(0, %r);"
            "import dialogue as d;"
            "from npc import resident as r;"
            "print([d.speak(x, 'zocalo', d.World(hour=10.0)).text()"
            " for x in r.roster('zocalo', 10.0, 'human', 5)])" % _HERE)
    runs = []
    for seed in ("0", "1"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        runs.append(subprocess.run([sys.executable, "-c", prog], env=env,
                                   capture_output=True, text=True).stdout)
    out(f"  under PYTHONHASHSEED 0 and 1 the same five people say "
        f"{'the same' if runs[0] == runs[1] else 'DIFFERENT'} things")
    n += 1
    check(runs[0] and runs[0] == runs[1],
          "deterministic across hash seeds -- blake2b, never str.__hash__",
          f"{runs[0][:60]!r} vs {runs[1][:60]!r}")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


# ===========================================================================
# 10.  The runtime gate -- does `godot/scripts/dialogue.gd` actually work
# ===========================================================================
# WHY THE HARNESS IS HERE AND NOT IN A SCENE. Every runtime file in this
# project is instantiated by `godot/scripts/walk.gd`, which this session does
# not own, so nothing in the shipped scene tree builds the dialogue node. Left
# there, the only claim anybody could make about the GDScript is that it
# parses -- and CLAUDE.md records a session lost to a parse error that took
# every call from `walk.gd` down with it, which is exactly the class of defect
# a parse check DOES catch and no more.
#
# So this drives it directly: it assembles a THROWAWAY GODOT PROJECT holding
# nothing but the two scripts (linked, not copied) and a one-node scene, runs
# Godot headless with `--dialogue-test`, and reads the verdict line the script
# prints.
#
# WHY A SEPARATE PROJECT AND NOT `godot/`. Two reasons, and the first is the
# one CLAUDE.md keeps writing down: running in `godot/` makes the engine scan
# and import the whole project, which on the session this was written meant
# racing another agent's `materials.py --export` through the same import cache
# -- disjoint source files, one shared artefact. The second is that it takes
# minutes. The cost is stated rather than hidden: this proves the SCRIPT, in
# isolation, against real data. It does not prove the script loads under the
# main project's settings, and nothing here claims it does.
#
# HEADLESS DISABLES RENDERING -- `tools/render_godot.sh` says so at the top and
# it is true here -- so this measures the join, the scan cone, the prompt range
# and the line pointer, and says NOTHING about the panel's look. The frame is a
# separate artefact and a separate claim.

_TSCN = """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/dialogue.gd" id="1"]

[node name="DialogueTest" type="Node3D"]
script = ExtResource("1")
"""

_PROJECT = """config_version=5

[application]
config/name="dialogue-runtime-test"
run/main_scene="res://dialogue_selftest.tscn"

[rendering]
renderer/rendering_method="forward_plus"
"""

# The scripts the harness needs on `res://`. `hud.gd` is there because
# `dialogue.gd` loads the palette off it at runtime, and the gate asserts that
# it succeeded -- so a harness without it would silently exercise the fallback
# literals and report the drift it exists to catch.
#
# `places.gd` IS HERE BECAUSE THE GATE WAS FAILING ON ITS ABSENCE AND NOBODY
# HAD RUN IT. `hud.gd:89` is `const _Places = preload("res://scripts/places.gd")`
# -- a preload, which is resolved at PARSE time, so a project without that file
# fails to compile `hud.gd` at all:
#
#     Parse Error: Preload file "res://scripts/places.gd" does not exist.
#     Failed to load script "res://scripts/hud.gd" with error "Parse error".
#     Invalid access to property or key 'CYAN' on a base object of type 'GDScript'
#
# `_load_palette` then fell back to its own colour literals and the gate's
# `palette != res://scripts/hud.gd` check fired -- correctly, and about the
# harness rather than about the panel. It had never run in CI: this module has
# no step in `.github/workflows/validate.yml`. The second parse error on
# `hud.gd:273` was a CASCADE of the first (`_Places` untyped makes `var k :=`
# uninferable) and disappears with the link, which is why only one file was
# added rather than the type annotation the message asks for.
#
# A PRELOAD IS A HARD DEPENDENCY AND A LINKED-SCRIPT LIST IS A SECOND COPY OF
# THE DEPENDENCY GRAPH. This one is asserted rather than trusted: `_test_project`
# scans each linked script for `preload("res://...")` and refuses to build a
# project that is missing one, so the next file `hud.gd` preloads breaks the
# harness loudly instead of quietly downgrading it -- which is CLAUDE.md's own
# rule about a tool that substitutes a lesser mode and exits 0.
_LINKED = ("dialogue.gd", "hud.gd", "places.gd")


def _test_project(root: str) -> str:
    """Assemble the throwaway project. LINKS the scripts, never copies them:
    a copy is a second version of the file under test, and a stale copy would
    pass this gate while the shipped script was broken."""
    import tempfile                                             # noqa: PLC0415
    d = os.path.join(tempfile.gettempdir(), "b5-dialogue-runtime")
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    with open(os.path.join(d, "project.godot"), "w") as f:
        f.write(_PROJECT)
    with open(os.path.join(d, "dialogue_selftest.tscn"), "w") as f:
        f.write(_TSCN)
    import re                                                    # noqa: PLC0415
    for name in _LINKED:
        src = os.path.join(root, "godot", "scripts", name)
        dst = os.path.join(d, "scripts", name)
        if os.path.islink(dst) or os.path.exists(dst):
            os.remove(dst)
        os.symlink(src, dst)
    # THE DEPENDENCY CHECK, and it must run AFTER the links so it reports what
    # is missing from the assembled project rather than from the source tree.
    missing = []
    for name in _LINKED:
        with open(os.path.join(root, "godot", "scripts", name)) as f:
            for want in re.findall(r'preload\(\s*"res://([^"]+)"', f.read()):
                if not os.path.exists(os.path.join(d, want)):
                    missing.append(f"{name} preloads res://{want}")
    if missing:
        raise RuntimeError(
            "the runtime harness is missing a hard dependency and would have "
            "reported a downgraded run as a defect in the panel: "
            + "; ".join(missing) + " -- add it to _LINKED")
    return d

GODOT_CANDIDATES = (
    "/home/user/godot-build/godot-4.4-stable/bin/"
    "godot.linuxbsd.editor.double.x86_64",
)


def _godot_binary():
    import glob                                                 # noqa: PLC0415
    for c in GODOT_CANDIDATES:
        if os.access(c, os.X_OK):
            return c
    for c in sorted(glob.glob(
            "/home/user/godot-build/*/bin/godot.linuxbsd.*.double.*")):
        if os.access(c, os.X_OK):
            return c
    return None


def _parse_verdict(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("DIALOGUETEST "):
            out = {}
            for kv in line[len("DIALOGUETEST "):].split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    out[k] = v
            return out
    return {}


def runtime_test(actors_path: str, out=print) -> bool:          # noqa: C901
    """Run `dialogue.gd` against real actor positions and real exchanges."""
    root = os.path.dirname(_HERE)
    godot = _godot_binary()
    if godot is None:
        out("dialogue: NO GODOT BINARY -- bash tools/build_godot.sh")
        return False
    if not os.path.exists(actors_path):
        out(f"dialogue: no actor list at {actors_path}; build a deck first")
        return False

    side = actors_path.replace("_actors.json", "_dialogue.json")
    n = write_sidecar(actors_path, side, World(hour=13.0))
    out(f"dialogue: {n} exchanges -> {os.path.basename(side)}")

    proj = _test_project(root)
    out(f"dialogue: runtime project at {proj} (links "
        f"{', '.join(_LINKED)})")

    import subprocess                                           # noqa: PLC0415
    ok = True
    results = {}
    for label, extra in (("live", []), ("control", ["--no-dialogue"])):
        cmd = [godot, "--headless", "--path", proj,
               "res://dialogue_selftest.tscn", "--",
               "--dialogue-test", f"--actors={actors_path}",
               f"--dialogue={side}"] + extra
        # A SCRIPT THAT FAILS TO PARSE DOES NOT CRASH GODOT: the scene loads
        # with no script, `_ready` never runs, nothing calls `quit()`, and a
        # headless engine sits in its main loop for ever. So the timeout is
        # part of the gate rather than a safety net, and it is short.
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=240)
        except subprocess.TimeoutExpired as e:
            out(f"  {label}: TIMED OUT after 240 s -- the script did not call "
                f"quit(), which is what a parse error looks like")
            out("    " + str(e.stdout or "")[-400:])
            results[label] = {}
            ok = False
            continue
        v = _parse_verdict(r.stdout)
        results[label] = v
        if not v:
            out(f"  {label}: NO VERDICT LINE -- the script did not run")
            out("    " + "\n    ".join(
                [x for x in (r.stdout + r.stderr).splitlines()
                 if "rror" in x or "SCRIPT" in x or "parse" in x.lower()][:8]))
            ok = False
            continue
        out(f"  {label}: " + " ".join(f"{k}={v[k]}" for k in sorted(v)))

    live = results.get("live") or {}
    ctl = results.get("control") or {}
    fails = []

    def g(d, k, cast=int, dflt=0):
        try:
            return cast(d.get(k, dflt))
        except Exception:                                       # noqa: BLE001
            return dflt

    if g(live, "people") < 1:
        fails.append("no exchange bound to a body -- the join on `group` "
                     "found nothing")
    if g(live, "opened") != 1:
        fails.append(f"walked in and opened {g(live, 'opened')} "
                     f"conversation(s), expected 1")
    # THE RUN, NOT THE TAKE. `open_lines` is what the sidecar baked; `run_lines`
    # is that with the player's chosen utterance and its answer spliced in, and
    # it is the array the pointer actually walks. Asserting against the take was
    # right until this session and now reads `showed 4 of 2` on a working
    # conversation -- a check measuring the wrong array, which is the same
    # defect as a gate reading a stale artefact.
    if g(live, "shown") != g(live, "run_lines"):
        fails.append(f"showed {g(live, 'shown')} of "
                     f"{g(live, 'run_lines')} lines -- the line pointer does "
                     f"not reach the end")
    if g(live, "run_lines") <= g(live, "open_lines"):
        fails.append(f"the conversation ran {g(live, 'run_lines')} lines "
                     f"against a baked {g(live, 'open_lines')} -- nothing was "
                     f"spliced in, so the player said nothing")
    pm = g(live, "prompt_m", float, -1.0)
    if not (0.0 < pm <= 3.3):
        fails.append(f"the prompt first appeared at {pm} m, which is not "
                     f"`talk_m`")
    if live.get("far_prompt") != "false":
        fails.append("a prompt was offered from beyond `talk_m` -- the range "
                     "test does nothing")
    if live.get("behind") != "false":
        fails.append("a prompt was offered with the body facing away -- the "
                     "cone test does nothing")
    # THE INVARIANT, over every offer made on the way in rather than over the
    # one person the harness walked at. On a deck with 73 people in two customs
    # halls the person offered is usually somebody else, and this is the claim
    # that has to hold for all of them.
    if g(live, "bad_range") or g(live, "bad_cone"):
        fails.append(f"{g(live, 'bad_range')} offer(s) outside `talk_m` and "
                     f"{g(live, 'bad_cone')} outside the cone")
    if live.get("palette") != "res://scripts/hud.gd":
        fails.append(f"the panel is drawing on {live.get('palette')} rather "
                     f"than the HUD's own constants")
    if g(live, "distinct") < 2:
        fails.append(f"the whole deck says {g(live, 'distinct')} distinct "
                     f"line(s)")
    # -- AND THE HALF THAT DID NOT EXIST: can the player answer -------------
    if g(live, "offers") < g(live, "people"):
        fails.append(f"{g(live, 'people') - g(live, 'offers')} of "
                     f"{g(live, 'people')} people offer the player nothing "
                     f"to say")
    if g(live, "said") != 1:
        fails.append(f"the walk-in spoke {g(live, 'said')} player line(s) in "
                     f"one conversation, expected exactly 1")
    if live.get("stance") != "press":
        fails.append(f"the harness asked for the `press` stance and the "
                     f"runtime recorded {live.get('stance')!r}")
    if not live.get("you_said", "").strip("-_"):
        fails.append("the player's utterance came back EMPTY -- a counted "
                     "line with no text is the failure that reads as success")
    if g(live, "stalled"):
        fails.append("the conversation stalled: `talk()` could not advance and "
                     "no stance would move it")
    if g(live, "says") < len(STANCES):
        fails.append(f"the deck offers {g(live, 'says')} distinct player "
                     f"line(s), fewer than one set of {len(STANCES)} stances")
    # -- and the clock reaches it ------------------------------------------
    if g(live, "takes") < 2:
        fails.append(f"every body carries {g(live, 'takes')} take(s) -- the "
                     f"sidecar is a photograph and the station's clock cannot "
                     f"move it")
    if g(live, "hour_moves") < 1:
        fails.append("nobody in the runtime's own cast says anything different "
                     "at 03:00 and 13:00")
    if g(ctl, "offers") or g(ctl, "says"):
        fails.append(f"CONTROL: with the exchanges withheld the runtime still "
                     f"offers {g(ctl, 'offers')} menus and "
                     f"{g(ctl, 'says')} player lines")
    # THE CONTROL. With the exchanges withheld everything downstream must
    # report zero; if it does not, the numbers above are measuring something
    # other than this file.
    if g(ctl, "people") != 0 or g(ctl, "opened") != 0:
        fails.append(f"CONTROL: with the exchanges withheld the runtime still "
                     f"bound {g(ctl, 'people')} people and opened "
                     f"{g(ctl, 'opened')}")

    out("")
    out(f"  a body walked in from 12 m, was offered a conversation at "
        f"{pm:.2f} m with {live.get('name', '?').replace('_', ' ')} "
        f"({live.get('topic', '?')}), and was shown all "
        f"{g(live, 'shown')} of their lines; every offer made on the way in "
        f"was inside {live.get('bad_range')}/{live.get('bad_cone')} "
        f"range/cone violations; the deck's {g(live, 'people')} people carry "
        f"{g(live, 'distinct')} distinct spoken lines")
    out(f"  AND IT ANSWERED BACK: {g(live, 'offers')}/{g(live, 'people')} "
        f"people offer a menu, {g(live, 'says')} distinct player lines on the "
        f"deck, and the walk-in said "
        f"\"{live.get('you_said', '').replace('_', ' ')}\" "
        f"({live.get('stance')})")
    out(f"  and the clock reaches them: {g(live, 'takes')} takes per body, "
        f"{g(live, 'hour_moves')}/{g(live, 'people')} say something different "
        f"at 03:00 than at 13:00")
    out(f"  CONTROL, exchanges withheld: {g(ctl, 'people')} bound, "
        f"{g(ctl, 'opened')} opened, {g(ctl, 'offers')} menus, "
        f"{g(ctl, 'says')} player lines")
    for f in fails:
        out(f"  FAIL {f}")
    out(f"\nruntime: {'PASS' if not fails and ok else 'FAIL'}")
    return not fails and ok


DEFAULT_ACTORS = os.path.join(_HERE, "generated", "scene", "deck",
                              "blue_0_0_z7440_actors.json")


def _cli(argv=None):                                         # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--converse", action="store_true",
                    help="the conversation gate: can a player talk back, and "
                         "to how many of the deck's people")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--coverage", action="store_true",
                    help="every baked deck's cast can speak, and the "
                         "sidecar is not older than its actors file")
    ap.add_argument("--sidecar", help="an actors.json written by walkable.py")
    ap.add_argument("--out", help="where to write the dialogue sidecar")
    ap.add_argument("--hour", type=float, default=13.0)
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--runtime-test", action="store_true",
                    help="drive godot/scripts/dialogue.gd headlessly")
    ap.add_argument("--actors", default=DEFAULT_ACTORS)
    a = ap.parse_args(argv)
    if a.coverage:
        return 0 if coverage_gate() else 1
    if a.converse:
        return 0 if converse() else 1
    if a.runtime_test:
        return 0 if runtime_test(a.actors) else 1
    if a.sidecar:
        out_path = a.out or a.sidecar.replace("_actors.json",
                                              "_dialogue.json")
        n = write_sidecar(a.sidecar, out_path,
                          World(hour=a.hour, day=a.day))
        print(f"dialogue: {n} exchanges -> {out_path}")
        return 0
    if a.report and not a.selftest:
        report()
        return 0
    ok = _selftest()
    if a.report:
        print()
        report()
    return 0 if ok else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(_cli())
