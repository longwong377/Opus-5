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
import sys
from dataclasses import dataclass, field

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


def phrase(topic: dict, reg: Register, sp: _Speaker) -> str:
    """One line of speech, from the topic's facts and the speaker's band."""
    b = reg.band
    key = topic["key"]
    f = dict(topic.get("fact") or {})
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
    if pick is None or pick["key"] not in SAY:
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
        # No words at all. The action IS the answer, and it is the gazetteer's.
        lines.append(Line("npc", "action", pick["action"], pick["source"]))
        sources.append(pick["source"])
        return Exchange(npc_id=sp.npc_id, name=sp.name, species=sp.species,
                        role=sp.role, place=place_key, hour=world.hour,
                        topic="refusal", band=reg.band, lines=tuple(lines),
                        ranking=tuple((t["key"], round(t["salience"], 3))
                                      for t in ranked),
                        sources=tuple(sources))

    greet = (COLD_GREET if reg.warmth < WARM_FLOOR else GREET)[reg.band]
    if greet:
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
        lines.append(Line("npc", "speech", phrase(pick, reg, sp),
                          pick["source"]))
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
    return speak(who, place_key, world, listener)


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
    out = []
    for a in actors:
        who = a.get("who") or {}
        npc_id = who.get("id")
        if not npc_id:
            continue
        r = res.resident(npc_id, who.get("species", "human"))
        place = a.get("place") or who.get("at_post") or ""
        ex = speak(r, place, world, listener)
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

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")

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
