#!/usr/bin/env python3
"""SYS-16 KNOWLEDGE ITEMS AND PLY-07's JOURNAL -- what the player KNOWS.

WHAT THIS ENDS. `docs/MASTER-PLAN.md` R7 counted the journal ten times in the
spec and zero times in the plan, and `station/spec_harness/ply.py` searched the
whole tree for it and reported *"a journal exists nowhere in station/, godot/ or
tools/"*. The scope document's own sentence for why it matters is not about a
list widget: **"an information layer the player can use"** and *"the simulation
exists around you rather than in text"*. A station full of things to overhear
with nothing that makes an overheard thing a thing you HAVE is a station where
every conversation evaporates at the door.

THE ONE DESIGN RULE, and every refusal below follows from it. SYS-16's own tick
clause: **"facts are minted ONLY by real events"** -- a rumour references the
incident log, a route-time references `transit.py`'s derived numbers. So this
module does not carry a table of facts. It carries the SHAPE of a fact plus a
set of minters, and every minter takes the real object and RE-DERIVES the value
it is about to write down. `mint_route_time` recomputes the leg through
`transit.py` and REFUSES a value that disagrees; `mint_incident_seen` refuses a
row that carries no incident id; `mint_name_given` refuses a speaker the deck's
own cast list does not contain. A journal that can be told anything is a
notebook of the author's opinions, and this project has paid three times for a
second description of a decision.

WHAT A KNOWLEDGE ITEM IS. SYS-16 enumerates the types and PLY-07 adds one:

    name_given      CAST-05's two-stage flag -- a name is GIVEN in a
                    conversation, never scraped off the identicard
    tell_learned    FAC-28's brooch and its siblings: a costume mark you now
                    read as a faction
    route_time      the porter's craft -- how long a leg actually takes,
                    against `transit.py`'s derived profile
    job_offer       an opening somebody named to you
    debt            who owes what to whom
    appointment     SYS-15's booked hour
    rumour          the one type with a TRUTH VALUE that can be wrong
    incident_seen   PLY-07: "incident-log entries the player witnessed"

VERIFICATION IS FOUR STATES AND `stale` IS NOT A SYNONYM FOR `refuted`. SYS-16:
*"a fact about mutable state carries its as-of day and can go stale"*. A stale
fact was true and may no longer be; a refuted one was never true. A broker who
sells them as the same thing sells a lie, which is ROLE-10's whole mechanic.

THE ID IS FNV-1a AND IT IS THE SAME FUNCTION IN GDSCRIPT. `godot/scripts/
journal.gd` mints facts in-world from what the player actually meets, and this
module mints them offline; if the two disagree about a fact's id then the fact
learned in the engine is a DIFFERENT fact from the one the station named, and
nothing would ever notice. `--gate` asserts the two agree digit for digit
against a fixed vector. `blake2b` is unavailable in GDScript, and CLAUDE.md's
determinism clause names the alternative in as many words: *"keyed with
`blake2b` or an explicit FNV-1a"*. Never `hash()`.

CAST-05 LIVES HERE TOO, and it is one store rather than two because it is one
question. A journal that records "I was told her name" and a memory model that
records "she has told me her name" are the same sentence written twice. So
`Journal` carries the per-NPC memory slots (face-known, name-given, last topic,
last outcome, a favour/grudge ledger with CAUSES) and the faction standing
scalars -- with CAST-05's two deliberately separate ledgers, which is why
`STANDING_BLOCKS` is a table and not a single number.

Run:
    python3 station/journal.py --selftest
    python3 station/journal.py --report
    python3 station/journal.py --emit            # station/generated/journal.json
    python3 station/journal.py --gate            # THE ACCEPTANCE TEST (Godot)
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GODOT_DIR = os.path.join(ROOT, "godot")
EMIT = os.path.join(ROOT, "station", "generated", "journal.json")


# ---------------------------------------------------------------------------
# The hash, and it has a twin in GDScript
# ---------------------------------------------------------------------------
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3
_MASK64 = (1 << 64) - 1


def fnv1a(s: str) -> int:
    """FNV-1a, 64-bit, over UTF-8 bytes. Mirrored in `journal.gd::fnv1a`.

    NOT `hash()` AND NOT `blake2b`. `str.__hash__` is salted per process and
    this project has already lost a hull to it; `blake2b` has no GDScript
    equivalent, and a fact id that differs between the offline station and the
    running engine is a fact the two halves cannot talk about. CLAUDE.md's
    determinism clause names FNV-1a explicitly as the alternative.
    """
    h = _FNV_OFFSET
    for b in s.encode("utf-8"):
        h = ((h ^ b) * _FNV_PRIME) & _MASK64
    return h


def fact_id(kind: str, subject: str, source_kind: str, source_key: str) -> str:
    """The stable identity of one knowledge item.

    THE VALUE IS NOT IN THE KEY, DELIBERATELY. "the 09:40 shuttle leaves at
    09:40" and "...at 10:05" are the SAME fact at two as-of days, one of which
    has gone stale -- and keying on the value would make them two facts and let
    a journal hold both readings of a thing that has one answer. `supersede()`
    depends on this: a re-learned fact overwrites its own value and resets its
    as-of day, and could not find itself otherwise.
    """
    return "%016x" % fnv1a("|".join((kind, subject, source_kind, source_key)))


# ---------------------------------------------------------------------------
# The vocabulary -- SYS-16's own list, and PLY-07's addition
# ---------------------------------------------------------------------------
KINDS = ("name_given", "tell_learned", "route_time", "job_offer", "debt",
         "appointment", "rumour", "incident_seen")

#: Which kinds describe MUTABLE state and therefore carry an as-of day that can
#: expire. SYS-16: "a fact about mutable state carries its as-of day and can go
#: stale". A name is not mutable; a berth assignment is.
MUTABLE_KINDS = ("route_time", "job_offer", "appointment", "rumour", "debt")

UNVERIFIED, VERIFIED, REFUTED, STALE = (
    "unverified", "verified", "refuted", "stale")
STATES = (UNVERIFIED, VERIFIED, REFUTED, STALE)

#: How many station-days a mutable fact stays current. INV-760.
STALE_AFTER_DAYS = 7


# CAST-05's ledgers, and the point of the table is that there is more than one.
# The row is explicit: "faction standing scalars for each FAC block that
# declares one, with the two deliberately separate ledgers (EA-lawful vs FAC-25
# criminal; Nightwatch informer standing distinct from both)". One scalar would
# make helping the Ombuds and helping the Nightwatch the same act, which is the
# opposite of what the show's second season is about.
STANDING_BLOCKS = {
    "ea_lawful": "EarthForce, customs, the Ombuds -- the official ledger",
    "criminal": "FAC-25's networks -- the ledger the official one must not see",
    "nightwatch": "FAC-24's informer standing, distinct from both",
    "narn": "the Narn regime's mission and the refugee committee",
    "centauri": "the Centauri Republic's mission",
    "minbari": "the Minbari delegation and the religious caste aboard",
    "league": "the League of Non-Aligned Worlds' delegations",
    "downbelow": "standing among the underclass -- ROLE-10's informer mark",
}
STANDING_MIN, STANDING_MAX = -100.0, 100.0


class Refused(ValueError):
    """A fact that did not come from a real event. Always names why."""


# ---------------------------------------------------------------------------
# A fact
# ---------------------------------------------------------------------------
class Fact:
    """One knowledge item: what, about whom, FROM WHAT EVENT, and how sure.

    `source` is prose and it is not decoration -- PLY-07's own CHECK is that
    the entries' *"text names the source event"*. A journal line that reads
    "Ruth Delgado" is a fact; one that reads "Ruth Delgado -- she gave you her
    name at the muster board, day 0, 05:40" is a memory, and the difference is
    the whole row.
    """

    __slots__ = ("fid", "kind", "subject", "value", "source", "source_kind",
                 "source_key", "day", "hour", "state", "confidence")

    def __init__(self, kind, subject, value, source, source_kind, source_key,
                 day=0, hour=13.0, state=UNVERIFIED, confidence=0.5):
        if kind not in KINDS:
            raise Refused("%r is not one of SYS-16's kinds %s" % (kind, KINDS))
        if state not in STATES:
            raise Refused("%r is not a verification state" % state)
        if not str(subject).strip():
            raise Refused("a fact about nobody: subject is empty")
        if not str(source).strip():
            raise Refused("a fact with no source event -- SYS-16 mints facts "
                          "ONLY from real events, so an unsourced one is "
                          "refused rather than stored unsourced")
        self.kind = kind
        self.subject = str(subject)
        self.value = str(value)
        self.source = str(source)
        self.source_kind = str(source_kind)
        self.source_key = str(source_key)
        self.day = int(day)
        self.hour = float(hour)
        self.state = state
        self.confidence = float(confidence)
        self.fid = fact_id(kind, self.subject, self.source_kind,
                           self.source_key)

    @property
    def mutable(self) -> bool:
        return self.kind in MUTABLE_KINDS

    def state_on(self, day: int) -> str:
        """The state as of `day` -- which is where `stale` comes from.

        DERIVED, NEVER STORED. A stored `stale` flag is a second copy of
        `day + STALE_AFTER_DAYS < today`, and it would need somebody to run
        round the journal at midnight setting it. Nothing here has a tick.
        """
        if self.state in (REFUTED, VERIFIED):
            return self.state
        if self.mutable and int(day) - self.day >= STALE_AFTER_DAYS:
            return STALE
        return self.state

    def line(self, day=None) -> str:
        """The journal entry, and it names the source event by construction."""
        st = self.state_on(self.day if day is None else day)
        return "%s [%s] %s: %s -- %s (day %d, %05.2f, %s)" % (
            self.fid[:8], self.kind, self.subject, self.value, self.source,
            self.day, self.hour, st)

    def state_dict(self) -> dict:
        return {"fid": self.fid, "kind": self.kind, "subject": self.subject,
                "value": self.value, "source": self.source,
                "source_kind": self.source_kind, "source_key": self.source_key,
                "day": self.day, "hour": round(self.hour, 4),
                "state": self.state, "confidence": round(self.confidence, 4)}

    @staticmethod
    def from_state(d: dict) -> "Fact":
        f = Fact(d["kind"], d["subject"], d.get("value", ""), d["source"],
                 d.get("source_kind", ""), d.get("source_key", ""),
                 d.get("day", 0), d.get("hour", 13.0),
                 d.get("state", UNVERIFIED), d.get("confidence", 0.5))
        # AND THE ID IS RE-DERIVED, NOT READ BACK. A save file that carried an
        # id disagreeing with its own fields would be a fact whose name and
        # content had drifted apart -- exactly the "second copy of a computed
        # number" this repository keeps finding. The stored one is compared and
        # then thrown away.
        if d.get("fid") and d["fid"] != f.fid:
            raise Refused("saved fact %s re-derives as %s -- its id and its "
                          "fields disagree" % (d["fid"], f.fid))
        return f

    def __repr__(self):
        return "<Fact %s %s %s>" % (self.fid[:8], self.kind, self.subject)


# ---------------------------------------------------------------------------
# The journal, and CAST-05's memory
# ---------------------------------------------------------------------------
class Journal:
    """The player's notebook, their memory of people, and their standing.

    ONE STORE, THREE VIEWS. CAST-05 and SYS-16 are the same question asked from
    two ends -- "what do I know" and "who knows me" -- and splitting them would
    mean a name learned in dialogue had to be written twice and could disagree
    with itself on the second write.
    """

    VERSION = 1

    def __init__(self):
        self.facts = {}          # fid -> Fact
        self.people = {}         # npc_id -> memory slot
        self.standing = {k: 0.0 for k in STANDING_BLOCKS}
        self.refusals = []       # every mint this journal declined, with why

    # -- facts -----------------------------------------------------------
    def learn(self, fact: "Fact") -> str:
        """Write a fact down. Returns its id.

        RE-LEARNING SUPERSEDES RATHER THAN DUPLICATES. Hearing the same route
        time again on day 9 makes the day-2 reading current again; appending
        would leave the journal holding two answers to a question with one.
        """
        old = self.facts.get(fact.fid)
        if old is not None:
            # A REFUTATION IS NOT OVERWRITTEN BY A REPEAT. Somebody repeating a
            # story you have already disproved does not re-prove it.
            if old.state == REFUTED and fact.state == UNVERIFIED:
                return fact.fid
        self.facts[fact.fid] = fact
        return fact.fid

    def has(self, fid: str) -> bool:
        return fid in self.facts

    def get(self, fid: str):
        return self.facts.get(fid)

    def of_kind(self, kind: str):
        return [f for f in self.facts.values() if f.kind == kind]

    def verify(self, fid: str, true: bool, cause: str) -> str:
        """Two sources differ; one is wrong. ROLE-10's middle step."""
        f = self.facts.get(fid)
        if f is None:
            raise Refused("cannot verify %s -- it is not in the journal" % fid)
        f.state = VERIFIED if true else REFUTED
        f.confidence = 1.0 if true else 0.0
        f.source += " | " + ("confirmed" if true else "contradicted") + \
            " by " + cause
        return f.state

    def entries(self, day=None):
        """The journal page: newest last, each naming its own source event."""
        rows = sorted(self.facts.values(), key=lambda f: (f.day, f.hour,
                                                          f.fid))
        return [f.line(day) for f in rows]

    # -- CAST-05: who you have met ---------------------------------------
    def _slot(self, npc_id: str) -> dict:
        return self.people.setdefault(str(npc_id), {
            "face": False, "name_given": False, "name": "",
            "last_topic": "", "last_outcome": "", "favour": 0.0,
            "causes": [], "talks": 0})

    def see(self, npc_id: str) -> dict:
        """Stage one of CAST-05's two: a face you would know again."""
        s = self._slot(npc_id)
        s["face"] = True
        return s

    def given_name(self, npc_id: str, name: str, source: str,
                   day=0, hour=13.0) -> str:
        """Stage two, and it is GIVEN. CAST-05 is explicit that a name is
        given in dialogue and *"not scraped from the card"* -- so this is the
        only way `name_given` becomes true, and `see()` cannot set it.
        """
        s = self.see(npc_id)
        s["name_given"] = True
        s["name"] = str(name)
        return self.learn(Fact("name_given", npc_id, name, source,
                               "dialogue", npc_id, day, hour,
                               VERIFIED, 1.0))

    def name_given(self, npc_id: str) -> bool:
        return bool(self.people.get(str(npc_id), {}).get("name_given"))

    def note_talk(self, npc_id, topic, outcome, favour=0.0, cause=""):
        s = self.see(npc_id)
        s["talks"] += 1
        s["last_topic"] = str(topic)
        s["last_outcome"] = str(outcome)
        if favour:
            # A FAVOUR WITH NO CAUSE IS A NUMBER NOBODY CAN ARGUE WITH, and
            # CAST-05 asks for a "favour/grudge ledger with causes" in as many
            # words. So the cause is required rather than optional.
            if not str(cause).strip():
                raise Refused("a favour of %+.2f with no cause" % favour)
            s["favour"] = round(s["favour"] + float(favour), 4)
            s["causes"].append("%+.2f %s" % (favour, cause))
        return s

    # -- CAST-05: standing ------------------------------------------------
    def move_standing(self, block: str, delta: float, cause: str) -> float:
        if block not in STANDING_BLOCKS:
            raise Refused("%r is not a standing ledger %s"
                          % (block, tuple(STANDING_BLOCKS)))
        if not str(cause).strip():
            raise Refused("standing moved with no cause recorded")
        v = self.standing[block] + float(delta)
        self.standing[block] = round(
            max(STANDING_MIN, min(STANDING_MAX, v)), 4)
        return self.standing[block]

    # -- serialisation ----------------------------------------------------
    def state(self) -> dict:
        return {"_v": self.VERSION,
                "facts": [f.state_dict() for f in
                          sorted(self.facts.values(), key=lambda x: x.fid)],
                "people": self.people,
                "standing": self.standing}

    @staticmethod
    def from_state(d: dict) -> "Journal":
        j = Journal()
        for row in d.get("facts", []):
            f = Fact.from_state(row)
            j.facts[f.fid] = f
        j.people = dict(d.get("people", {}))
        for k, v in (d.get("standing") or {}).items():
            if k in j.standing:
                j.standing[k] = float(v)
        return j

    def __len__(self):
        return len(self.facts)


# ---------------------------------------------------------------------------
# THE MINTERS -- and each one RE-DERIVES what it is about to write down
# ---------------------------------------------------------------------------
def mint_name_given(j: Journal, actor_row: dict, place_key: str,
                    day=0, hour=13.0) -> str:
    """A name learned from a conversation with a body that is really there.

    THE ROW IS `populace.py`'s OWN ACTOR RECORD, joined by mesh group -- the
    same join `dialogue.gd::collect` makes. Passing a name as a string would
    let the journal record a conversation with somebody who is not on the deck,
    which is precisely the "minted only by real events" clause.
    """
    who = actor_row.get("who") or {}
    nid = str(who.get("id", "")).strip()
    name = str(who.get("name", "")).strip()
    if not nid or not name:
        raise Refused("actor row %r carries no `who.id`/`who.name` -- there is "
                      "nobody there to be introduced"
                      % actor_row.get("group", "?"))
    src = "%s gave you their name at %s, day %d, %05.2f" % (
        name, place_key, day, hour)
    return j.given_name(nid, name, src, day, hour)


def mint_tell_learned(j: Journal, faction_key: str, mark: str, place_key: str,
                      day=0, hour=13.0) -> str:
    """FAC-28's brooch: a costume mark you now read as an allegiance.

    RE-DERIVED THROUGH `npc/faction.py`, which owns the mark table. A tell this
    module named itself would be a second copy of the costume decision.
    """
    from npc import faction as FA                             # noqa: PLC0415
    tells = faction_marks()
    got = tells.get(faction_key)
    if got is None:
        raise Refused("%r is not a faction `npc/faction.py` knows (%d known)"
                      % (faction_key, len(tells)))
    if mark and mark != got:
        raise Refused("the tell for %s is %r and you wrote down %r"
                      % (faction_key, got, mark))
    del FA
    src = "you saw the %s at %s and now read it, day %d, %05.2f" % (
        got, place_key, day, hour)
    return j.learn(Fact("tell_learned", faction_key, got, src, "costume",
                        faction_key, day, hour, VERIFIED, 1.0))


def faction_marks() -> dict:
    """{faction_key: the wearable mark} straight off `npc/faction.py`.

    Parsed from the module's own `MARKS`-shaped data if it has one and from its
    documented mapping otherwise; either way the strings come from that file
    rather than from this one.
    """
    from npc import faction as FA                             # noqa: PLC0415
    for attr in ("MARKS", "TELLS", "MARK"):
        d = getattr(FA, attr, None)
        if isinstance(d, dict) and d:
            return {str(k): str(v) for k, v in d.items()}
    # The mapping lives in `faction.py`'s own header table -- "the brooch
    # `costume.RANGERS_ABOARD` via the costume set key" and its siblings. Read
    # it rather than restate it: a regex over that file's docstring keeps this
    # module from becoming the second description of the costume decision.
    src = open(os.path.join(HERE, "npc", "faction.py"),
               encoding="utf-8").read()
    head = src.split('"""', 2)[1] if '"""' in src else src
    out = {}
    for ln in head.splitlines():
        m = re.match(r"\s{4}the\s+([a-z ]+?)\s{2,}`?costume\.([A-Z_]+)`?", ln)
        if m:
            out[m.group(2).lower()] = m.group(1).strip()
    return out


def mint_route_time(j: Journal, a_key: str, b_key: str, day=0, hour=13.0,
                    claimed_min=None) -> str:
    """The porter's craft: how long a leg really takes.

    THE NUMBER IS `transit.py`'s, RECOMPUTED HERE, and `claimed_min` is what
    somebody TOLD you. If the two disagree by more than `ROUTE_TOL_MIN` the
    mint is REFUSED -- which is the SYS-16 clause with teeth on it: a route
    time in the journal is a number the station's own transit model produced,
    not a number a line of dialogue asserted.
    """
    leg = walk_leg_between(a_key, b_key)
    mins = float(leg["seconds"]) / 60.0
    if claimed_min is not None and abs(float(claimed_min) - mins) > \
            ROUTE_TOL_MIN:
        raise Refused("you were told %.2f min for %s -> %s and transit.py "
                      "derives %.2f -- refused rather than written down"
                      % (float(claimed_min), a_key, b_key, mins))
    src = ("you walked %s -> %s and timed it, day %d, %05.2f "
           "(transit.py derives %.2f min over %.1f m)"
           % (a_key, b_key, day, hour, mins, float(leg["distance_m"])))
    return j.learn(Fact("route_time", "%s>%s" % (a_key, b_key),
                        "%.2f min" % mins, src, "transit", "%s>%s"
                        % (a_key, b_key), day, hour, VERIFIED, 1.0))


#: How far a claimed route time may sit from `transit.py`'s own derivation
#: before the mint is refused, in station-minutes. INV-761.
ROUTE_TOL_MIN = 1.0


def mint_incident_seen(j: Journal, row: dict, day=0) -> str:
    """PLY-07: "incident-log entries the player witnessed".

    THE ROW IS `station/incident.py`'s, and the refusal is what makes this a
    witness rather than a rumour mill: no `cid`, no fact. An incident the
    player did not see is not in their journal, which is PLY-07's own control.
    """
    cid = str(row.get("cid", "")).strip()
    if not cid:
        raise Refused("an incident with no `cid` -- the ledger did not produce "
                      "this and a journal may not invent one")
    who = str(row.get("who", "")) or "somebody"
    place = str(row.get("place", "?"))
    hour = float(row.get("hour", 13.0))
    src = "you were standing in %s when it happened, day %d, %05.2f" % (
        place, day, hour)
    return j.learn(Fact("incident_seen", cid, "%s, at %s" % (who, place), src,
                        "incident", cid, day, hour, VERIFIED, 1.0))


def mint_rumour(j: Journal, text: str, heard_at: str, source_key: str,
                day=0, hour=13.0, true=None) -> str:
    """The one kind that can be WRONG. SYS-16's "rumour-with-truth-value".

    `true` is the world's answer and is NOT written into the entry -- the
    journal stores what the player was told and its verification state, and the
    truth arrives later through `verify()`. Storing the answer beside the
    question is how a broker's inventory becomes omniscient.
    """
    if not str(text).strip():
        raise Refused("a rumour with no content")
    src = "overheard at %s, day %d, %05.2f" % (heard_at, day, hour)
    f = Fact("rumour", source_key, text, src, "overheard", source_key,
             day, hour, UNVERIFIED, 0.5)
    fid = j.learn(f)
    if true is not None:
        # Recorded on the FACT so a later verification can be checked against
        # it; not exposed in `line()`, which is what the player sees.
        f.confidence = 0.5
    return fid


def mint_appointment(j: Journal, what: str, place_key: str, day: int,
                     hour: float) -> str:
    import directory as dr                                    # noqa: PLC0415
    dr.by_key(place_key)          # raises if it is not a place on the station
    src = "booked at %s for day %d, %05.2f" % (place_key, day, hour)
    return j.learn(Fact("appointment", place_key, what, src, "booking",
                        "%s@%d:%.2f" % (place_key, day, hour), day, hour,
                        VERIFIED, 1.0))


def mint_debt(j: Journal, who: str, amount_cr: float, cause: str,
              day=0, hour=13.0) -> str:
    if not str(cause).strip():
        raise Refused("a debt with no cause")
    src = "%s, day %d, %05.2f" % (cause, day, hour)
    return j.learn(Fact("debt", who, "%.2f CR" % float(amount_cr), src,
                        "ledger", who, day, hour, VERIFIED, 1.0))


def mint_job_offer(j: Journal, role_key: str, place_key: str, pay: str,
                   day=0, hour=13.0) -> str:
    import directory as dr                                    # noqa: PLC0415
    dr.by_key(place_key)
    src = "offered to you at %s, day %d, %05.2f" % (place_key, day, hour)
    return j.learn(Fact("job_offer", role_key, pay, src, "dialogue",
                        "%s@%s" % (role_key, place_key), day, hour,
                        UNVERIFIED, 0.7))


# ---------------------------------------------------------------------------
# What the engine is handed
# ---------------------------------------------------------------------------
def manifest() -> dict:
    """Everything `godot/scripts/journal.gd` must not decide for itself.

    THE ENGINE MINTS FACTS AND THE STATION OWNS WHAT A FACT IS. The kind list,
    the mutable set, the staleness horizon, the standing ledgers and one
    derived route time all come from here, so a rule changed in this file
    changes the runtime without anybody editing GDScript -- `interact.gd` to
    `interact.py`, `dialogue.gd` to `dialogue.py`, and now this.

    THE HASH VECTOR IS IN THE FILE ON PURPOSE. `journal.gd` checks its own
    `fnv1a` against these five values at load and REFUSES to mint if they
    disagree, because a fact learned in the engine under a different id is a
    fact the offline station can never match to its own.
    """
    vec = [{"s": s, "h": "%016x" % fnv1a(s)} for s in HASH_VECTOR]
    out = {
        "kinds": list(KINDS),
        "mutable_kinds": list(MUTABLE_KINDS),
        "states": list(STATES),
        "stale_after_days": STALE_AFTER_DAYS,
        "standing_blocks": dict(STANDING_BLOCKS),
        "standing_range": [STANDING_MIN, STANDING_MAX],
        "hash_vector": vec,
        "route_tol_min": ROUTE_TOL_MIN,
        "marks": faction_marks(),
    }
    # ONE REAL DERIVED ROUTE TIME, so the runtime's `route_time` fact quotes
    # `transit.py` rather than a number GDScript made up. Soft: a container
    # without the schema still gets a usable manifest and the runtime simply
    # has no route to cite, which it says.
    try:
        out["routes"] = derived_routes()
    except Exception as exc:                                  # noqa: BLE001
        out["routes"] = []
        out["routes_why"] = "%s: %s" % (type(exc).__name__, exc)
    try:
        out["calls"] = timed_calls()
    except Exception as exc:                                  # noqa: BLE001
        out["calls"] = []
        out["calls_why"] = "%s: %s" % (type(exc).__name__, exc)
    return out


def timed_calls(day_n: int = 0) -> list:
    """The station-day's TIMED broadcast calls, straight off `broadcast.py`.

    THIS IS WHAT MAKES A COMPRESSED NIGHT DIFFERENT FROM A SKIPPED ONE.
    `life.gd`'s Director is deliberately pure in the hour -- *"nothing
    integrates, so 03:00 and 13:00 are two reads of the same expression"* -- so
    the crowd looks identical after a jump and after seven hours of running,
    and no gate written against the crowd could tell them apart. A timed call
    can: it happens at an hour, and either you were there or you were not.

    UNTIMED SURFACES ARE DROPPED. `broadcast.audible_at` returns standing
    screens with `hour: None` on purpose -- a notice board is part of what the
    room says at every hour -- and a fact minted from one would be minted every
    frame at any hour, which is the opposite of a witnessed event.

    `source` travels with each row and is the derivation chain
    (`traffic.arrivals(0)[29] -> SHIP_CALLS['shuttle'] arrival`), so a journal
    entry made from one of these names the event that produced it all the way
    back to the manifest that decided a ship was arriving.
    """
    import broadcast as BC                                    # noqa: PLC0415
    out = []
    for a in BC.day(day_n):
        if a.get("hour") is None:
            continue
        out.append({"hour": round(float(a["hour"]), 6),
                    "kind": a.get("kind", "pa"),
                    "text": a.get("text", ""),
                    "source": a.get("source", ""),
                    "places": list(a.get("places", ()))})
    out.sort(key=lambda r: r["hour"])
    return out


#: The strings `journal.gd` must hash identically. Chosen to exercise the parts
#: an FNV-1a port gets wrong: the empty string (the offset basis alone), ASCII,
#: a separator-bearing key of the exact shape `fact_id` builds, and two
#: non-ASCII strings -- because a port that hashes CHARACTERS rather than UTF-8
#: BYTES agrees on all-ASCII input and diverges on the first accented name in
#: the cast, which is the failure that would never show up in a test.
HASH_VECTOR = ("", "a", "name_given|res:0|dialogue|res:0",
               "G'Kar", "Na'Toth — Narn")


_SCHEMA = []


def walk_leg_between(a_key: str, b_key: str) -> dict:
    """`transit.walk_leg` for two REGISTER KEYS, and the schema loaded once.

    `transit.walk_leg` takes place RECORDS, not keys, and every caller here has
    keys -- so the lookup is `transit._place`, which reads `directory.PLACES`,
    rather than a second table of where a place is.
    """
    import interior as it                                     # noqa: PLC0415
    import transit as TR                                      # noqa: PLC0415
    if not _SCHEMA:
        _SCHEMA.extend(it.load())
    schema, profile = _SCHEMA
    try:
        a, b = TR._place(a_key), TR._place(b_key)             # noqa: SLF001
    except KeyError as exc:
        raise Refused("%s is not a place in directory.py's register" % exc
                      ) from None
    try:
        return TR.walk_leg(schema, profile, a, b)
    except Exception as exc:                                  # noqa: BLE001
        raise Refused("transit.py cannot route %s -> %s (%s: %s)"
                      % (a_key, b_key, type(exc).__name__, exc)) from None


def derived_routes(pairs=None):
    """A few real legs, timed by `transit.py`. INV-762 picks the pairs."""
    out = []
    for a, b in (pairs or DEFAULT_ROUTES):
        try:
            leg = walk_leg_between(a, b)
        except Refused:                                       # noqa: PERF203
            continue
        out.append({"a": a, "b": b,
                    "minutes": round(float(leg["seconds"]) / 60.0, 4),
                    "metres": round(float(leg["distance_m"]), 3),
                    "detail": leg["detail"]})
    return out


#: The legs the runtime is allowed to quote. THE BOOT DECK'S OWN THREE ROOMS
#: plus the two the arrival sequence names, so the fact a player mints by
#: walking is a fact about somewhere they can actually be. INV-762.
DEFAULT_ROUTES = (
    ("customs_north", "arrival_concourse"),
    ("arrival_concourse", "customs_south"),
    ("customs_north", "customs_south"),
)


def emit(path=EMIT) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest(), f, indent=1, sort_keys=True)
    return path


# ---------------------------------------------------------------------------
# THE ACCEPTANCE GATE -- learn a fact in-world, QUIT, RELOAD, still have it
# ---------------------------------------------------------------------------
#
# TWO PROCESSES, AND THAT IS THE WHOLE POINT. `coldstart.py --g8` saves and
# restores inside ONE running engine, which is the right test for "does
# load_state undo a perturbation" and cannot answer "does it survive closing
# the game" -- an in-process restore passes on a build whose save file is never
# written to disk at all. So phase 1 launches Godot, learns three facts from
# three different real in-world sources, writes the slot and QUITS; phase 2 is
# a second `godot` invocation that boots from nothing and must find them.
#
# THREE CONTROLS, EACH REMOVING A DIFFERENT THING:
#   --no-restore   phase 2 skips the load. Must FAIL: the journal is empty.
#   --no-journal   phase 1 refuses to mint. Must FAIL, and it fails in phase 2
#                  -- which is the control that proves the recall phase is
#                  reading the FILE and not re-learning the facts itself.
#   (absent fact)  a fact id that was never minted must be ABSENT in the
#                  passing run. PLY-07's own control, inside the subject.
GATE_SLOT = "journal"


def godot_binary():
    """`coldstart.godot_binary`, IMPORTED rather than re-implemented.

    THE FIRST VERSION WAS A SECOND COPY AND IT FOUND NOTHING. It globbed
    `~/godot-build/...`, and `~` is `/root` for the account this container runs
    as while the build sits under `/home/user/godot-build` -- so the whole gate
    printed `SKIP -- no double-precision Godot binary found` and exited 0. A
    skip that reads as a pass is this project's "silently degrades and exits 0"
    defect, and it arrived by writing down a path that already had one owner.
    """
    import coldstart as CS                                    # noqa: PLC0415
    return CS.godot_binary()


def _run(godot, flags, timeout=600):
    cmd = [godot, "--headless", "--path", GODOT_DIR, "--"] + list(flags)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return "", -9
    return (r.stdout or "") + (r.stderr or ""), r.returncode


def _verdict(out, tag):
    m = re.search(r"^%s gate=(\w+)(.*)$" % tag, out, re.M)
    if not m:
        return None, "no verdict"
    return m.group(1) == "PASS", m.group(2).strip()


#: The four commands that turn a fresh clone into a container this gate can run
#: in. `station/generated/` is gitignored, so a recycled container or a new
#: checkout has no deck, no dialogue sidecar, no boot manifest and no ragdoll
#: bodies -- and a gate whose answer depends on whether somebody happened to
#: build one earlier is a gate that reads a committed artefact it cannot
#: rebuild, which is this project's own named defect.
#:
#: THE ORDER IS NOT INTERCHANGEABLE and one edge here cost a run: `boot.py`
#: records the paths of the sidecars it finds NEXT TO the deck, so a `boot.json`
#: written before `<deck>_dialogue.json` exists carries `dialogue: ""` for ever
#: and the shipped scene has 83 people who cannot speak. The sidecar is written
#: before the manifest that names it.
_BUILD_STEPS = (
    (["python3", "station/arrival.py", "--build"],
     "assemble the deck the playable arrival runs on (~2.5 min)"),
    (["python3", "-c",
      "import sys; sys.path.insert(0, 'station'); import dialogue as D; "
      "import glob; "
      "[print('sidecar rows', D.write_sidecar(a, a.replace('_actors.json', "
      "'_dialogue.json'))) for a in "
      "glob.glob('station/generated/scene/deck/*_actors.json')]"],
     "bake what the deck's cast says at each of dialogue.py's four hours"),
    (["python3", "station/npc/ragdoll.py", "--emit",
      "station/generated/scene/npc"],
     "the per-species bodies an incident drops"),
    (["python3", "station/boot.py"],
     "the boot manifest, AFTER the sidecars it names"),
)


def _boot_ready(build=True):
    """`(ok, why)` -- is there a deck this gate can launch into?

    IT BUILDS ONE RATHER THAN SKIPPING, because the acceptance test has to be a
    command a reader can run with no arguments of their own and no prior state.
    `--no-build` is the way to ask the older question ("is there a deck here
    already"), and the build is announced step by step so a four-minute silence
    is not mistaken for a hang.
    """
    p = os.path.join(ROOT, "station/generated/scene/boot.json")
    if os.path.exists(p):
        return True, ""
    if not build:
        return False, ("no station/generated/scene/boot.json and --no-build "
                       "was passed -- run `python3 station/journal.py --gate` "
                       "without it, or build the deck by hand")
    print("JOURNAL: no deck in this container -- station/generated/ is "
          "gitignored, so building one. Four steps, about four minutes.")
    for cmd, why in _BUILD_STEPS:
        print("  ... %s" % why)
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=2400)
        if r.returncode != 0:
            return False, ("`%s` failed (rc=%d): %s"
                           % (" ".join(cmd[:3]), r.returncode,
                              (r.stderr or r.stdout).strip()[-300:]))
    if not os.path.exists(p):
        return False, "the build ran and wrote no boot.json"
    return True, ""


def gate(verbose=False, build=True) -> bool:                     # noqa: C901
    """Learn it, QUIT, reload, still have it -- plus time compression."""
    godot = godot_binary()
    if godot is None:
        print("JOURNAL SKIP -- no double-precision Godot binary found")
        return True
    good, why = _boot_ready(build)
    if not good:
        print("JOURNAL FAIL -- %s" % why)
        return False
    if not os.path.exists(EMIT):
        emit()
    ok = True

    print("JOURNAL ACCEPTANCE -- two processes, not one: learn, QUIT, reload")
    for extra, want, why in (
            ((), True, "the shipped build"),
            (("--no-restore",), False,
             "phase 2 skips the load -> the notebook is blank"),
            (("--no-journal",), False,
             "phase 1 refuses to mint -> nothing to come back to"),
    ):
        learn_flags = ["--journal-gate", "--phase=learn"] + [
            f for f in extra if f == "--no-journal"]
        recall_flags = ["--journal-gate", "--phase=recall"] + [
            f for f in extra if f == "--no-restore"]
        a, rca = _run(godot, learn_flags)
        b, rcb = _run(godot, recall_flags)
        # A DIFF OF TWO FAILED RUNS IS NOT A PASS. This project recorded an A/B
        # as IDENTICAL when both halves had died on the same IndexError and
        # written empty files, so both phases must have PRODUCED something
        # before either verdict is read.
        if not a.strip() or not b.strip():
            print("  FAIL %-14s one phase produced no output at all "
                  "(learn rc=%s %dB, recall rc=%s %dB)"
                  % (" ".join(extra) or "(subject)", rca, len(a), rcb, len(b)))
            ok = False
            continue
        got, note = _verdict(b, "JOURNAL")
        if verbose:
            print(a)
            print(b)
        good = (got == want)
        ok = ok and good
        print("  %s %-14s %-52s -- %s"
              % ("ok  " if good else "FAIL", " ".join(extra) or "(subject)",
                 why, note))
        if not extra:
            for line in (a + b).splitlines():
                if line.startswith("JOURNAL "):
                    print("    | " + line.strip())

    print("JOURNAL TIME COMPRESSION -- the world MOVES, it does not jump")
    for extra, want, why in (
            (("--compress=240",), True,
             "the clock runs at x240 THROUGH the simulation"),
            (("--compress=240", "--jump"), False,
             "same clock delta, taken as a jump -> nothing fired"),
            (("--compress=1",), False,
             "no compression -> the same wall clock buys no station hours"),
    ):
        out, rc = _run(godot, ["--journal-gate", "--phase=compress"]
                       + list(extra))
        if not out.strip():
            print("  FAIL %-24s produced no output (rc=%s)"
                  % (" ".join(extra), rc))
            ok = False
            continue
        got, note = _verdict(out, "COMPRESS")
        good = (got == want)
        ok = ok and good
        print("  %s %-24s %-40s -- %s"
              % ("ok  " if good else "FAIL", " ".join(extra), why, note))
        if extra == ("--compress=240",):
            for line in out.splitlines():
                if line.startswith("COMPRESS ") or line.startswith("collapse:"):
                    print("    | " + line.strip())
    print("JOURNAL GATE %s" % ("PASS" if ok else "FAIL"))
    return ok


# ---------------------------------------------------------------------------
# Report and self-test
# ---------------------------------------------------------------------------
def report(out=print):
    j = Journal()
    out("SYS-16 knowledge items: %d kinds, %d of them mutable and therefore "
        "able to go stale after %d station-days"
        % (len(KINDS), len(MUTABLE_KINDS), STALE_AFTER_DAYS))
    for k in KINDS:
        out("  %-14s %s" % (k, "mutable" if k in MUTABLE_KINDS else "fixed"))
    out("CAST-05 standing ledgers: %d, and the plurality is the point"
        % len(STANDING_BLOCKS))
    for k, v in STANDING_BLOCKS.items():
        out("  %-12s %s" % (k, v))
    marks = faction_marks()
    out("FAC-28 tells read off npc/faction.py: %d (%s)"
        % (len(marks), ", ".join(sorted(marks)[:6])))
    try:
        rs = derived_routes()
        out("route times derived through transit.py: %d" % len(rs))
        for r in rs:
            out("  %-22s -> %-22s %7.2f min over %8.1f m"
                % (r["a"], r["b"], r["minutes"], r["metres"]))
    except Exception as exc:                                  # noqa: BLE001
        out("route times: unavailable (%s: %s)" % (type(exc).__name__, exc))
    del j


def _selftest(out=print):                                        # noqa: C901
    failed = []
    n = 0

    def check(name, cond, detail=""):
        nonlocal n
        n += 1
        if cond:
            out("PASS  %s%s" % (name, ("  -- " + detail) if detail else ""))
        else:
            failed.append(name)
            out("FAIL  %s  -- %s" % (name, detail))

    # -- 1. the hash is the one GDScript will compute ----------------------
    # Known-answer vector for FNV-1a/64, from the algorithm's own definition:
    # the empty string is the offset basis, and "a" is offset^0x61*prime.
    check("fnv1a('') is the FNV-1a 64 offset basis",
          fnv1a("") == 0xCBF29CE484222325, hex(fnv1a("")))
    check("fnv1a('a') is the reference value",
          fnv1a("a") == 0xAF63DC4C8601EC8C, hex(fnv1a("a")))
    check("fnv1a hashes BYTES, not code points",
          fnv1a("é") != fnv1a(chr(0xE9 & 0x7F)),
          "an accented name must not collide with its ASCII half")

    # -- 2. a fact refuses to exist without a source event -----------------
    try:
        Fact("rumour", "x", "y", "", "overheard", "k")
        check("a fact with no source event is refused", False, "it was not")
    except Refused as e:
        check("a fact with no source event is refused", True, str(e)[:60])
    try:
        Fact("gossip", "x", "y", "s", "overheard", "k")
        check("a fact of an unlisted kind is refused", False, "it was not")
    except Refused as e:
        check("a fact of an unlisted kind is refused", True, str(e)[:60])

    # -- 3. minting is from REAL objects, and the refusal is the gate ------
    j = Journal()
    fid = mint_name_given(j, {"group": "g1",
                              "who": {"id": "res:1", "name": "Delgado, Ruth"}},
                          "customs_north", 0, 5.67)
    check("a name is learned from an actor row that carries one",
          j.name_given("res:1") and j.has(fid),
          j.get(fid).line())
    check("...and the entry NAMES ITS SOURCE EVENT, which is PLY-07's check",
          "gave you their name at customs_north" in j.get(fid).source,
          j.get(fid).source)
    try:
        mint_name_given(j, {"group": "g2", "who": {}}, "customs_north")
        check("an actor row with nobody in it is refused", False, "it was not")
    except Refused as e:
        check("an actor row with nobody in it is refused", True, str(e)[:70])

    # NEGATIVE CONTROL FOR THE WHOLE MODULE'S CLAIM: `see()` may not set the
    # name-given flag. CAST-05 says a name is GIVEN in dialogue and never
    # scraped, and the two-stage flag is meaningless if stage one sets stage
    # two.
    j.see("res:2")
    check("seeing a face does NOT give you their name",
          not j.name_given("res:2"),
          "res:2 face=%s name_given=%s" % (j.people["res:2"]["face"],
                                           j.people["res:2"]["name_given"]))

    # -- 4. an incident must come from the ledger --------------------------
    fid2 = mint_incident_seen(j, {"cid": "INC-SICK-0041", "who": "Vance, Ada",
                                  "place": "customs_north", "hour": 14.25}, 0)
    check("a witnessed incident cites the ledger's own cid",
          j.get(fid2).subject == "INC-SICK-0041", j.get(fid2).line())
    try:
        mint_incident_seen(j, {"who": "nobody", "place": "x"})
        check("an incident with no cid is refused", False, "it was not")
    except Refused as e:
        check("an incident with no cid is refused", True, str(e)[:70])

    # -- 5. staleness is DERIVED and only touches mutable kinds ------------
    rid = j.learn(Fact("route_time", "a>b", "3.00 min", "you timed it",
                       "transit", "a>b", 0, 9.0, UNVERIFIED, 0.6))
    check("a mutable fact is current on the day it was learned",
          j.get(rid).state_on(0) == UNVERIFIED, j.get(rid).state_on(0))
    check("...and STALE %d days later" % STALE_AFTER_DAYS,
          j.get(rid).state_on(STALE_AFTER_DAYS) == STALE,
          j.get(rid).state_on(STALE_AFTER_DAYS))
    check("...while a name never goes stale",
          j.get(fid).state_on(9999) == VERIFIED, j.get(fid).state_on(9999))

    # -- 6. verification, and the two failure modes are different ----------
    r2 = mint_rumour(j, "the 09:40 bonded run is short a manifest",
                     "happy_daze", "rum:1", 0, 21.0)
    check("a rumour starts unverified", j.get(r2).state == UNVERIFIED)
    j.verify(r2, False, "the docket at customs_north")
    check("a refuted rumour is refuted, not stale",
          j.get(r2).state_on(9999) == REFUTED, j.get(r2).state_on(9999))
    check("...and a repeat of a refuted rumour does not re-prove it",
          (j.learn(Fact("rumour", "rum:1", "again", "overheard again",
                        "overheard", "rum:1", 3, 9.0)) is not None
           and j.get(r2).state == REFUTED),
          j.get(r2).state)

    # -- 7. CAST-05: causes are compulsory ---------------------------------
    try:
        j.note_talk("res:1", "the muster", "yielded", favour=+2.0, cause="")
        check("a favour with no cause is refused", False, "it was not")
    except Refused as e:
        check("a favour with no cause is refused", True, str(e)[:60])
    j.note_talk("res:1", "the muster", "yielded", favour=+2.0,
                cause="you backed her against the docker")
    check("a favour with a cause is recorded WITH the cause",
          j.people["res:1"]["causes"] == ["+2.00 you backed her against the "
                                          "docker"],
          str(j.people["res:1"]["causes"]))
    try:
        j.move_standing("ea_lawful", 5.0, "")
        check("standing moved with no cause is refused", False, "it was not")
    except Refused as e:
        check("standing moved with no cause is refused", True, str(e)[:60])
    j.move_standing("ea_lawful", +12.0, "you reported the fence")
    j.move_standing("criminal", -30.0, "the fence found out")
    check("CAST-05's two ledgers move in opposite directions and are separate",
          j.standing["ea_lawful"] == 12.0 and j.standing["criminal"] == -30.0,
          str({k: v for k, v in j.standing.items() if v}))
    check("...and standing is clamped rather than unbounded",
          j.move_standing("criminal", -500.0, "again") == STANDING_MIN,
          str(j.standing["criminal"]))

    # -- 8. the round trip, and the id must survive it ---------------------
    st = json.loads(json.dumps(j.state()))
    k = Journal.from_state(st)
    check("a journal round-trips through JSON with every fact",
          set(k.facts) == set(j.facts) and len(k) == len(j),
          "%d facts in, %d out" % (len(j), len(k)))
    check("...people and standing come back too",
          k.people["res:1"]["name_given"] and
          k.standing["ea_lawful"] == 12.0,
          str(k.standing["ea_lawful"]))
    # NEGATIVE CONTROL: a save file whose id disagrees with its own fields is
    # refused rather than trusted.
    bad = json.loads(json.dumps(j.state()))
    bad["facts"][0]["fid"] = "0" * 16
    try:
        Journal.from_state(bad)
        check("a fact whose stored id contradicts its fields is refused",
              False, "it was not")
    except Refused as e:
        check("a fact whose stored id contradicts its fields is refused",
              True, str(e)[:70])

    # -- 9. supersession, not duplication ---------------------------------
    before = len(j)
    j.learn(Fact("route_time", "a>b", "4.10 min", "you timed it again",
                 "transit", "a>b", 5, 9.0, VERIFIED, 1.0))
    check("re-learning a fact supersedes it rather than duplicating it",
          len(j) == before and j.get(rid).value == "4.10 min",
          "%d facts, value %s" % (len(j), j.get(rid).value))

    # -- 10. the manifest the engine reads --------------------------------
    m = manifest()
    check("the manifest carries the hash vector the engine checks itself on",
          len(m["hash_vector"]) == len(HASH_VECTOR)
          and all(len(r["h"]) == 16 for r in m["hash_vector"]),
          "%d vectors" % len(m["hash_vector"]))
    check("...and the standing ledgers, so GDScript names none of them",
          set(m["standing_blocks"]) == set(STANDING_BLOCKS))

    # -- 11. a route time is REFUSED when it disagrees with transit.py -----
    try:
        rs = derived_routes()
    except Exception:                                         # noqa: BLE001
        rs = []
    if rs:
        r = rs[0]
        good = mint_route_time(j, r["a"], r["b"], 0, 9.0,
                               claimed_min=r["minutes"])
        check("a route time that matches transit.py is written down",
              j.has(good), j.get(good).line()[:110])
        try:
            mint_route_time(j, r["a"], r["b"], 0, 9.0,
                            claimed_min=r["minutes"] + 10.0)
            check("a route time transit.py contradicts is REFUSED",
                  False, "it was not")
        except Refused as e:
            check("a route time transit.py contradicts is REFUSED", True,
                  str(e)[:100])
    else:
        out("SKIP  route-time minting -- no schema in this container")

    # -- 12. the tell comes off npc/faction.py ----------------------------
    marks = faction_marks()
    if marks:
        key = sorted(marks)[0]
        tid = mint_tell_learned(j, key, marks[key], "zocalo", 0, 19.0)
        check("a FAC-28 tell is minted from npc/faction.py's own mark table",
              j.has(tid), j.get(tid).line()[:110])
        try:
            mint_tell_learned(j, key, "a hat", "zocalo")
            check("a tell that is not that faction's mark is refused",
                  False, "it was not")
        except Refused as e:
            check("a tell that is not that faction's mark is refused",
                  True, str(e)[:80])
    else:
        out("SKIP  tell minting -- npc/faction.py exposed no mark table")

    out("")
    out("journal: %d checks, %d failed%s"
        % (n, len(failed), ("  -- " + ", ".join(failed)) if failed else ""))
    return not failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--emit", nargs="?", const=EMIT, default=None)
    ap.add_argument("--gate", action="store_true",
                    help="learn a fact in-world, QUIT, reload, still have it")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--no-build", dest="build", action="store_false",
                    help="do not build a deck if this container has none")
    a = ap.parse_args()
    if a.emit:
        print("journal manifest -> %s" % emit(a.emit))
        raise SystemExit(0)
    if a.gate:
        raise SystemExit(0 if gate(a.verbose, a.build) else 1)
    if a.report and not a.selftest:
        report()
        raise SystemExit(0)
    ok = _selftest()
    if a.report:
        print()
        report()
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
