#!/usr/bin/env python3
"""WHO THE PLAYER IS -- and the answer is "a resident", built by the machinery
that builds the other 250,000.

THE QUESTION THIS ANSWERS. The owner asked, in as many words: *"character
creator/or random? does the player have a residence?"* Before this module the
answer to both was no -- `godot/scripts/player.gd` is a capsule with a camera on
it. It has a stature and a walking speed and NOTHING ELSE: no name, no species,
no origin, no card, no job, no quarters, no credits. A body, not a person.

THE ONE DESIGN DECISION, and everything else follows from it: **the player is a
`npc.resident.Resident` and not a parallel type.** That module already resolves
a whole person from an id -- the nine identicard fields off the authority-1 prop,
a role from the faction apportionment, a HOME from `home_for`, a job, and the
five leisure addresses that decide where somebody eats and drinks and prays. It
is 1,313 lines and it was written for the crowd. A separate `PlayerCharacter`
class would be a second description of a person, and this repository has paid
for a second description of one decision three times (the door decision made in
the render and again in the shell; the corridor profile written down instead of
measured; the material list in CLAUDE.md and in the module). Hard rule 4 --
inside and outside come from one schema -- is exactly this rule.

So:

    random_player(seed)     -> a person drawn from the station's own species mix
                               and its own role weights, i.e. indistinguishable
                               from anybody in the corridor
    player_from(choices)    -> THE CHARACTER CREATOR, and it is field overrides
                               on that same generated record. There is no second
                               construction path.

WHAT A CHARACTER CREATOR IS, MECHANICALLY. Two kinds of choice, and conflating
them is the bug this module exists to avoid:

  * a **direct** field -- forename, surname -- is replaced in place;
  * a **generative** field -- species, role -- CANNOT be, because half the
    record derives from it. Set `species="narn"` by `dataclasses.replace` alone
    and you get a Narn whose ORIGIN reads EARTH, whose name came out of the
    human grammar, and who lives in the human staff quarters. So a generative
    choice is re-derived through `resident`'s OWN functions (`home_for`,
    `workplace_places`, `_visa`, `_licensed_psi`), never through a copy of their
    rules here. `_selftest` proves the difference: the naive replace leaves five
    fields disagreeing with the choice, and that is the negative control.

WHAT IS MUTABLE, AND IT IS NOT THE RECORD. `Resident` is frozen and stays frozen
-- an identicard is what the station holds about you and a player does not edit
it. The mutable half is the four things a player has that an NPC's statistics do
not need: WHERE they are, WHAT they are carrying, HOW MUCH they have, and their
processing STATUS at the gate. That split is why `Player` holds a card rather
than being one.

CREDITS ARE NOT DECORATION AND THE NUMBER IS DERIVED. See `CREDIT_SKEW`: the
distribution is solved so that the share of arrivals who cannot afford passage
home matches the one per-arrival rate `TRAFFIC-AND-CUSTOMS.md` §6.6 states, which
is the mechanism that produces Downbelow. `station/arrival.py` is where that is
gated.

Run: python3 station/player.py --selftest
     python3 station/player.py --report
     python3 station/player.py --make species=narn role=merchant forename=G-Kar
"""
import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field, fields, replace

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "npc")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import directory as dr                                          # noqa: E402
from npc import resident as RES                                 # noqa: E402
from npc import schedule as sched                               # noqa: E402


def _u(seed: str, salt: str = "") -> float:
    """The same blake2b draw `resident` and `schedule` use.

    NEVER `random` and never `str.__hash__`: PYTHONHASHSEED salts the latter per
    process, and this project has already lost a hull to it. A player generated
    from a seed must be the same player in the next process.
    """
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ---------------------------------------------------------------------------
# Who turns up
# ---------------------------------------------------------------------------
# THE SPECIES MIX IS THE STATION'S OWN, not a second table. `schedule.
# STATION_COUNTS` apportions 250,000 people across fifteen species with a stated
# reason per row; drawing the player from it is what makes "random" mean
# "somebody who could be aboard" rather than "one of the four species we have
# art for".
#
# KOSH IS EXCLUDED and that is `schedule.VORLON_SINGLETON`'s own rule restated
# where it bites: one person is not a proportion. There is exactly one Vorlon,
# he is authored, and a player who rolled him would be a second one.
PLAYABLE_MIX = {sp: w for sp, w in sched.STATION_MIX.items() if sp != "vorlon"}

# EXTRAPOLATED (INV-248): the arriving mix equals the resident mix. Constrained
# from one side by TRAFFIC-AND-CUSTOMS §5.3 -- the transient population is
# resupplied entirely by arrivals, so at steady state the two mixes must agree
# on whoever STAYS -- and unconstrained on the through-traffic, which is where
# it could be wrong: a Drazi freighter crew is over-represented at the gate and
# under-represented in the census. Overturned by any figure for the species mix
# of arrivals as opposed to residents. It is a separate constant from
# `PLAYABLE_MIX` so that overturning it is one edit.
ARRIVING_MIX = dict(PLAYABLE_MIX)


def _draw_species(seed: str, mix=None) -> str:
    """One species, by weight. Deterministic in `seed`."""
    mix = ARRIVING_MIX if mix is None else mix
    x = _u(seed, "species") * sum(mix.values())
    acc = 0.0
    for sp in sorted(mix):                       # sorted: order is not a rule
        acc += mix[sp]
        if x <= acc:
            return sp
    return sorted(mix)[-1]


# ---------------------------------------------------------------------------
# What they are carrying, and what it is worth
# ---------------------------------------------------------------------------
# THE CARD IS AN ITEM, and that is the whole reason it is modelled as one.
# TRAFFIC-AND-CUSTOMS §6.4, authority 4: the identicard is simultaneously
# driver's licence, credit card, passport and medical file -- so losing it is a
# complete character arc, and it can only be lost if it is a thing you carry
# rather than a property you have. `arrival.py` refuses entry without it.
IDENTICARD = "identicard"
KIT_BAG = "kit_bag"

# HOW MUCH A PLAYER CAN CARRY, and until session 4q the answer was "unbounded",
# which is the same defect as a till nothing can refuse: an inventory with no
# ceiling has no `store` verb, only a `take` one.
#
# EXTRAPOLATED (INV-410), and it is a SLOT count rather than a mass because the
# mass anchor exists and the per-item mass does not. `canon/CONFLICTS.md`'s
# throughput reconciliation carries **40 kg of baggage per passenger** and
# `economy.GOODS` carries no kilograms at all, so an arithmetic answer is not
# available; what is available is a bracket, and the bracket is narrow:
#
#   >= 3  the player LANDS holding two (`IDENTICARD`, `KIT_BAG`) and
#         `dockwork.py`'s fourteen-day loop has them buy a drink on every one
#         of those days. A capacity of 2 makes the loop this repository
#         already ships impossible, so three is a hard floor.
#   <= 14 `economy.MAX_LINES` -- the widest counter on the station carries
#         fourteen lines. A bag that holds more than a whole counter's range
#         is not a bag, it is a hold.
#
# 8 is the middle of that bracket rounded to a power of two so the carried list
# draws as one HUD row at any frame height. OVERTURNED BY: any depiction of a
# character carrying a countable number of things, or a per-item mass landing
# in `economy.GOODS` -- which would let the 40 kg allowance settle it
# arithmetically and retire this note.
CARRY_CAPACITY = 8

# Credits. The unit is not named on screen; the station's own board says
# "MONETARY EXCHANGE RATES THROUGH BUSINESS CENTER" (authority 1, via
# `signage.BOARDS["customs_procedures"]`), which establishes that there IS an
# exchange and not what the unit is called. So the field is a number of credits
# and the name is deliberately not asserted.
#
# THE DISTRIBUTION IS SOLVED, NOT CHOSEN, and this is the one derivation in this
# file. TRAFFIC-AND-CUSTOMS §6.6 states the only per-arrival rate the whole
# document gives: about **1%** of arrivals "cannot afford a ticket home" and
# fall out of the bottom into Downbelow -- 15 people a day, ~5,500 a year, which
# it checks against a 250,000-person station. That is a constraint on the LEFT
# TAIL of the arrival credit distribution, so the distribution is fitted to it:
#
#   credits = CREDIT_MIN + (CREDIT_MAX - CREDIT_MIN) * u ** CREDIT_SKEW
#   P(credits < PASSAGE_HOME_CR) = ((PASSAGE - MIN) / (MAX - MIN)) ** (1/SKEW)
#
# Setting that equal to LEAK_RATE and solving:
#
#   SKEW = ln((PASSAGE - MIN) / (MAX - MIN)) / ln(LEAK_RATE)
#        = ln(0.06) / ln(0.01) = 0.6111
#
# `arrival.py::_selftest` measures the realised rate over 4,000 draws and fails
# if it is not 1%, and its negative control sets SKEW to 1.0 -- a flat draw --
# which puts the rate at 6% and fires the gate. The three inputs are authority 5
# (INV-249) and the OUTPUT is the sourced number, which is the right way round.
#
# SPEC-CHANGE #1 (owner-approved 2026-08-04): the passage-home anchor is the
# FLOOR of LAW-CRIME:748's sourced 300-800 cr band, not 250. `docs/THE-STATION.md`
# §9 carries the entry and its recomputes; the skew self-derives from the change,
# which is why it is a derivation and not a constant.
CREDIT_MIN = 0.0
CREDIT_MAX = 5000.0
PASSAGE_HOME_CR = 300.0        # a berth on an outbound transport (band floor)
LEAK_RATE = 0.01               # §6.6, the share who never leave
CREDIT_SKEW = (__import__("math").log(
    (PASSAGE_HOME_CR - CREDIT_MIN) / (CREDIT_MAX - CREDIT_MIN))
    / __import__("math").log(LEAK_RATE))


def credits_for(npc_id: str, role_key: str = "") -> int:
    """What this person landed with. Deterministic; fitted to §6.6's leak.

    A LURKER CANNOT BE RICH, and the first version of this function let one be.
    `player_from({"role": "lurker"})` produced a Downbelow squatter holding
    4,666 credits, because the draw is the ARRIVAL distribution and knows
    nothing about who the arrival became. Canon's whole explanation of the
    underclass is that they *"did not have the money to afford a ticket back
    home"* (LAW-CRIME 7.1's own note on the passage-home row), so somebody in a
    no-status role is BY DEFINITION under that line: the draw is confined to
    the left tail rather than re-fitted, which keeps §6.6's 1% leak exactly as
    solved -- the leak is a statement about arrivals, and this is a statement
    about what an arrival has become.

    `resident.NO_STATUS_ROLES` is the set, and it is imported rather than
    restated: `arrival.py` already refuses these roles a status and a second
    list here would drift from it.
    """
    u = _u(npc_id, "credits")
    if role_key and role_key in RES.NO_STATUS_ROLES:
        return int(CREDIT_MIN + (PASSAGE_HOME_CR - CREDIT_MIN) * u)
    return int(CREDIT_MIN + (CREDIT_MAX - CREDIT_MIN) * (u ** CREDIT_SKEW))


# ---------------------------------------------------------------------------
# Posture -- what the eye does when the player sits down
# ---------------------------------------------------------------------------
# WHY THIS IS IN THIS FILE AND NOT IN THE ENGINE. `godot/scripts/player.gd` can
# measure the seat it is standing at -- and it does -- but it cannot know how
# tall the person in the chair is, because the player's stature comes off the
# `Resident` record this module owns. A number written into GDScript would be a
# human's hip height applied to a 2.02 m Narn.
#
# THE RULE IS `npc/animation.py`'s AND IS NOT RESTATED. `sit_clip` translates
# the whole torso by `dy = seat_h - hip_rest` -- the hip goes to the seat and
# everything above it comes with it -- so a seated eye is a standing eye minus
# exactly that drop. `seat_height`'s own docstring gives the fitted seat: *"a
# chair whose seat is at the sitter's knee puts the thigh horizontal and the
# shin vertical, which is the definition of a fitted seat"*.
#
# EVALUATED OFF `npc/body.py`'s FIGURE rather than off a built rig, which is
# the same table `animation.rig` builds its skeleton from -- one source, not
# two -- and costs a dict lookup instead of 0.3 s of skinning inside a
# serialiser that `economy.buy` calls on every transaction. `_selftest`
# asserts the two agree, so the cheap path cannot drift from the authority.
#
# AND `leg_k` IS WHY THE FIRST VERSION OF THIS FAILED ITS OWN GATE, which is
# the useful half. `FIGURE` is the HUMAN figure; `body._hip_ring` reads it as
# `FIGURE["hip"] * sp.leg_k`, so a Narn (leg_k 0.98) sits 36 mm off a
# FIGURE-only reading and the tolerance below caught it on the first run. The
# species factor is applied here exactly as `body.py` applies it -- and the
# knee takes the same factor, because a shorter leg is a lower knee.
FIT_TOL_M = 0.02


def posture(species: str, stature_m: float) -> dict:
    """Hip height, a fitted seat height and a recline datum, in metres."""
    from npc import body as B                                # noqa: PLC0415
    sp = B.SPECIES.get(species)
    leg_k = 1.0 if sp is None else float(sp.leg_k)
    return {"hip_m": round(B.FIGURE["hip"] * leg_k * stature_m, 4),
            "seat_m": round(B.FIGURE["knee"] * leg_k * stature_m, 4),
            # Lying down: the eye is a chest-depth above whatever you are lying
            # on. `body.FIGURE["chest_d"]` is the figure's own chest depth as a
            # fraction of stature, which is what a person on their side or
            # their back puts between the bunk and their eye.
            "recline_m": round(B.FIGURE["chest_d"] * stature_m, 4)}


# ---------------------------------------------------------------------------
# Processing status -- the mutable half of "do you have a visa"
# ---------------------------------------------------------------------------
# The CARD's `visas` field is what the station holds about you and it is frozen.
# This is what the gate has DONE about it, which changes during the first ten
# minutes and is therefore not on the card.
UNPROCESSED = "unprocessed"
ADMITTED = "admitted"
REFERRED = "referred"           # §6.3 station 10 -- secondary inspection
REFUSED = "refused"             # §6.3 station 10 -- held for the next ship out
STATUSES = (UNPROCESSED, ADMITTED, REFERRED, REFUSED)


# ---------------------------------------------------------------------------
# The player
# ---------------------------------------------------------------------------
@dataclass
class Player:
    """A person aboard, plus the four things only a player needs.

    `card` is a `npc.resident.Resident` and is the SAME TYPE the crowd is made
    of -- `indistinguishable()` asserts it, with a duck-typed lookalike as the
    negative control. Everything a resident can be asked, a player can be asked:
    `resident.identicard`, `resident.where_at`, `resident.describe` and
    `Resident.activity_at` all take this record unmodified.
    """
    card: RES.Resident
    at: str = ""                       # a directory place key -- where they ARE
    credits: int = 0
    carrying: tuple = ()
    status: str = UNPROCESSED
    quarters: str = ""                 # assigned at the gate; "" until then
    generated: bool = True             # False once a choice overrode a field
    # WHAT THE STATION HAS DONE ABOUT YOU, as against what it holds. A
    # `consequence.Record`: convictions, fines, custody, whether a conditional
    # status has been withdrawn. It belongs on the MUTABLE half for exactly the
    # reason the purse does -- a criminal record is a thing a session changes,
    # and the card is frozen because an identicard is not editable by its
    # bearer. `None` until something happens; `consequence.record_of` mints it.
    #
    # THE IMPORT IS LAZY AND THAT IS DELIBERATE. `station/consequence.py`
    # imports THIS module at module level (it needs `Player` and the four
    # statuses), so a module-level import here would be a cycle. The type is
    # therefore not annotated and the two methods that touch it import inside
    # the call -- which is the standard fix and is noted so nobody "tidies" it.
    record: object = None
    # WHAT THE PLAYER KNOWS, as against what the station holds about them
    # (`card`) and what the station has done about them (`record`). A
    # `journal.Journal`: SYS-16's knowledge items, CAST-05's per-NPC memory
    # slots, and the eight faction standing ledgers.
    #
    # ON THE MUTABLE HALF FOR THE REASON THE PURSE AND THE RECORD ARE. The card
    # is frozen because an identicard is not editable by its bearer; a notebook
    # is nothing BUT what a session wrote in it. And it lives here rather than
    # in a parallel store because `docs/MASTER-PLAN.md` R7 gives the
    # consequence of the alternative in one line -- *"a journal with no save is
    # a notebook that forgets"* -- and `state()` is the only channel this
    # simulation has to a runtime.
    #
    # `None` until something is learned, so every purse already in
    # `station/generated/economy.json` stays byte-identical and `Ledger.load`
    # needs no version bump. Unannotated and lazily imported for the same
    # reason `record` is: `station/journal.py` pulls in `directory` and
    # `transit`, and a module-level import here would drag the transit model
    # into every `economy.buy`.
    journal: object = None

    # -- delegation, so a player is asked the same questions an NPC is -------
    @property
    def npc_id(self) -> str:
        return self.card.npc_id

    @property
    def species(self) -> str:
        return self.card.species

    @property
    def name(self) -> str:
        return self.card.name

    def identicard(self):
        return RES.identicard(self.card)

    def where_at(self, hour: float) -> str:
        return RES.where_at(self.card, hour)

    def activity_at(self, hour: float):
        return self.card.activity_at(hour)

    def describe(self) -> str:
        return RES.describe(self.card)

    # -- the mutable half ---------------------------------------------------
    def move_to(self, place_key: str) -> None:
        """Stand somewhere. Validated against the register, always.

        A silent accept here is how a player ends up "in" a place that does not
        exist, which is the class of bug `directory.py` was built to make
        impossible for locations and had never been applied to a person.
        """
        dr.by_key(place_key)        # raises KeyError if it is not a place
        self.at = place_key

    # MILLICREDITS EXIST, and this method used to eat them. LAW-CRIME:730 is
    # explicit -- "Currency is **credits**, with **millicredits** below 1
    # credit" -- and `self.credits = int(self.credits - n)` TRUNCATED, so a
    # 0.80 cr drink took a whole credit off a 200 cr purse and 0.20 cr left the
    # universe. Found by `economy.py::_selftest`'s first transaction, which
    # asserted the debit equalled the price and did not.
    #
    # The balance is therefore rounded to millicredits rather than to credits.
    # `credits_for` still returns a whole number -- somebody arrives with a
    # round sum -- so nothing that reads a purse sees a float until a sub-credit
    # price has actually been paid, which is the point.
    MILLI = 3

    def spend(self, n: float) -> bool:
        """Pay, if there is enough. Returns whether it went through."""
        if n > self.credits:
            return False
        bal = round(self.credits - n, self.MILLI)
        self.credits = int(bal) if float(bal).is_integer() else bal
        return True

    def earn(self, n: float) -> float:
        """The other direction, and the only one that creates credits."""
        bal = round(self.credits + float(n), self.MILLI)
        self.credits = int(bal) if float(bal).is_integer() else bal
        return self.credits

    def full(self) -> bool:
        return len(self.carrying) >= CARRY_CAPACITY

    def take(self, item: str) -> bool:
        """Pick something up. False when there is no room for it.

        RETURNS A BOOL SINCE 4q, and the reason is the same one `spend()` has
        always had: a move that can be refused must SAY it was refused, or the
        caller cannot tell a full bag from a successful pickup. Every existing
        caller ignored the return and still behaves identically -- an item
        already carried, or a bag with room, is still taken.
        """
        if item in self.carrying:
            return True
        if self.full():
            return False
        self.carrying = tuple(sorted(self.carrying + (item,)))
        return True

    def drop(self, item: str) -> None:
        self.carrying = tuple(x for x in self.carrying if x != item)

    def has(self, item: str) -> bool:
        return item in self.carrying

    def can_afford_passage(self) -> bool:
        """§6.6's fork: the difference between a visitor and a lurker."""
        return self.credits >= PASSAGE_HOME_CR

    # -- standing, and it is a READING rather than a field -------------------
    # The rung is NOT stored. It is `consequence.tier_of(card, record)`, which
    # reads the nine identicard fields through `arrival.entry_class` -- this
    # project's one card reader -- plus employment plus the record. A stored
    # tier would be a second description of what the card already says, and it
    # would go stale the moment a conviction landed. This is the same rule that
    # keeps `identicard` a delegation rather than a copy.
    @property
    def tier(self) -> int:
        from consequence import tier_of                      # noqa: PLC0415
        return tier_of(self.card, self.record)

    @property
    def tier_name(self) -> str:
        import consequence as CQ                             # noqa: PLC0415
        return CQ.tier_name(CQ.tier_of(self.card, self.record))

    # -- serialisation, and it is ONLY the mutable half ---------------------
    # `station/economy.py` persists purses so that a purchase survives the
    # process, and the thing it must NOT do is write its own copy of a person.
    # The card is not in here on purpose: `random_player(seed)` rebuilds it
    # bit-identically from the id (`indistinguishable` claim 4 asserts exactly
    # that), so storing 27 frozen fields would be a second description of a
    # record this project can already regenerate -- hard rule 4. What a save
    # has to carry is what a session CHANGED.
    def state(self) -> dict:
        st = {"npc_id": self.card.npc_id, "species": self.card.species,
              "at": self.at, "credits": self.credits,
              "carrying": list(self.carrying), "status": self.status,
              "quarters": self.quarters, "generated": bool(self.generated)}
        # -- THE READ-ONLY HALF, and every key here is DERIVED ---------------
        # `economy.json` is the only channel between this simulation and the
        # engine: `godot/scripts/player.gd` reads the purse and nothing else of
        # this module reaches a runtime. So the four things the runtime cannot
        # recompute -- the rung a counter checks, how far the eye drops when
        # the player sits, how much the bag holds, and who this is -- travel
        # with the purse.
        #
        # NOT LOADED BACK BY `restore`, deliberately. Every one of them is a
        # function of the card, and the card is REGENERATED from the id --
        # `from_state`'s own rule. Restoring them would be a second copy of a
        # derivation, which is how a saved tier survives a conviction.
        st["name"] = self.card.card_name
        st["role"] = self.card.role
        st["carry_cap"] = CARRY_CAPACITY
        try:
            st["tier"] = int(self.tier)
            st["tier_name"] = self.tier_name
        except Exception:                                    # noqa: BLE001
            pass
        st.update(posture(self.card.species, self.card.stature_m))
        # WHEN THIS PERSON WAKES UP. `schedule.wake_hour` is the species
        # rhythm's own answer and is what a `rest` on a bunk advances the
        # station clock to -- see `godot/scripts/interact.gd`. A human sleeps
        # 23:00 + 7.5 h; a Narn does not, and the runtime must not assume it.
        try:
            st["wake_h"] = round(float(sched.wake_hour(self.card.species)), 4)
        except Exception:                                    # noqa: BLE001
            pass
        # A CONSEQUENCE THAT DOES NOT SURVIVE THE PROCESS IS A MOOD. The key is
        # written only when there IS a record, so every purse already sitting
        # in `economy.json` stays byte-identical and `Ledger.load` does not
        # need a version bump.
        if self.record is not None:
            st["record"] = self.record.state()
        # AND NEITHER DOES A THING YOU LEARNED. Same rule, same reason, same
        # additive shape: the key appears only once there is a journal, so an
        # older purse round-trips unchanged and a build that predates PLY-07
        # reads a save written by one that does not.
        if self.journal is not None:
            st["journal"] = self.journal.state()
        return st

    def restore(self, st: dict) -> "Player":
        """Put a saved mutable half back on this record. Returns self."""
        if st.get("npc_id") not in (None, self.card.npc_id):
            raise ValueError(f"that state belongs to {st['npc_id']}, not "
                             f"{self.card.npc_id}")
        self.at = st.get("at", "")
        self.credits = st.get("credits", 0)
        self.carrying = tuple(st.get("carrying", ()))
        self.status = st.get("status", UNPROCESSED)
        self.quarters = st.get("quarters", "")
        self.generated = bool(st.get("generated", True))
        if "record" in st and st["record"] is not None:
            from consequence import Record                    # noqa: PLC0415
            self.record = Record.from_state(st["record"])
        if "journal" in st and st["journal"] is not None:
            from journal import Journal                       # noqa: PLC0415
            # `Journal.from_state` RE-DERIVES every fact id and refuses a save
            # whose stored id disagrees with its own fields. That refusal is
            # deliberately loud here rather than swallowed: a notebook whose
            # entries have drifted from their names is worse than one that
            # failed to load, because the first reads as working.
            self.journal = Journal.from_state(st["journal"])
        return self


def from_state(st: dict) -> Player:
    """A whole player back from a saved purse, card and all.

    The card is REGENERATED rather than loaded, which is the point: an id and a
    species resolve to one person deterministically, so a save file cannot
    describe a player the station's own machinery would not produce.

    A CHOSEN ROLE IS NOT IN THE ID, AND THAT MADE THIS A DIFFERENT PERSON.
    `player_from(choices, seed)` mints a card with a role the player picked,
    through `_rederive`; nothing about that choice is recoverable from
    `(npc_id, species)`. So on the purse this repository actually ships
    (`station/generated/economy.json`, `player:downbelow`) the engine's
    `interact.gd::set_purse` handed the body a **lurker at rung 0**, and this
    function returned a **service worker at rung 4** for the same save.

    Not cosmetic: rung is the field the entire law layer turns on.
    `consequence._dispose` at rung 0 says *"already at the floor; the next
    disposal is transfer off-station"*, and at rung 4 says *"EA citizenship is
    not revocable by an Ombuds"*. Two different games, decided by which loader
    you happened to come through.

    THE RAISE MATTERS AS MUCH AS THE FIX. `state()` writes `tier` for the
    engine, so the two halves CAN be compared -- and nothing compared them,
    which is why a disagreement this loud survived. A save whose stored rung
    and rebuilt rung differ is not a save this function will quietly reinterpret.
    """
    nid, sp = st["npc_id"], st["species"]
    card = RES.resident(nid, sp)
    role = st.get("role")
    if role and card.role != role:
        card = _rederive(nid, sp, role)
    pl = Player(card=card).restore(st)
    if "tier" in st and int(st["tier"]) != int(pl.tier):
        raise ValueError(f"{nid}: the purse says rung {st['tier']} and the "
                         f"rebuilt card says {pl.tier}")
    return pl


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def player_id(seed: str) -> str:
    """The id space a player's record is resolved from.

    Distinct from `resident.pool_id`'s `res:{seed}:{place}:{species}:{i}` on
    purpose -- a player is not one of a room's regulars -- but resolved by the
    same `resident()`, which is deterministic in (id, species) and nothing else.
    """
    return f"player:{seed}"


def random_player(seed: str = "player", at: str = "") -> Player:
    """A person, drawn by the station's own machinery. Nothing chosen.

    This is the "or random?" half of the owner's question, and the point of it
    is that the answer is not a special path: the species comes from the census,
    the role from the faction apportionment, the name from the species grammar,
    the body from `npc.body`, the home from `resident.home_for`.
    """
    nid = player_id(seed)
    card = RES.resident(nid, _draw_species(nid))
    return Player(card=card, at=at, credits=credits_for(nid, card.role),
                  carrying=(IDENTICARD, KIT_BAG), status=UNPROCESSED,
                  quarters="", generated=True)


# Which choices re-derive the record and which are written straight in.
# A generative field is one that OTHER fields are computed from; setting it by
# `replace` alone leaves the record self-contradictory, and `_selftest` measures
# exactly how many fields disagree when you do.
GENERATIVE = ("species", "role")
DIRECT = ("forename", "surname", "sex", "phys_chr", "medical", "visas",
          "origin", "home", "job", "eats_at", "shops_at", "plays_at",
          "prays_at", "commutes_via", "age")
CHOICES = GENERATIVE + DIRECT


def _rederive(nid: str, species: str, role_key: str) -> RES.Resident:
    """The record for this id, species and CHOSEN role.

    Every role-dependent field is recomputed through `resident`'s own functions.
    There is no table of rules here and there must never be one: `home_for`
    knows that a Vorlon envoy lives in a sealed berth and a refugee does not
    live in Downbelow, and a second copy of that would be wrong within a session.
    """
    base = RES.resident(nid, species)
    if role_key == base.role:
        return base
    role = sched.ROLES_BY_KEY.get(role_key)
    if role is None:
        raise KeyError(f"role {role_key!r} is not in schedule.ROLES "
                       f"({sorted(sched.ROLES_BY_KEY)})")
    home = RES.home_for(nid, species, role_key)
    job = RES._pick(RES.workplace_places(role.workplace), nid, "job")
    eats = base.eats_at
    if role.key in RES.EAT_OUT_ROLES_EXCLUDED:
        eats = ""
    return replace(
        base,
        role=role.key,
        home=home,
        job="" if role.work_hours <= 0 else job,
        idles_at=job if role.work_hours <= 0 else home,
        eats_at=eats,
        visas=RES._visa(nid, role.key),
        licensed_psi=RES._licensed_psi(nid, species, role.key),
        age=RES._age(nid, species, role.key),
    )


def player_from(choices: dict, seed: str = "player", at: str = "") -> Player:
    """THE CHARACTER CREATOR: a generated record with fields overridden.

    Order matters and is the whole content of the function. Generative choices
    re-derive first, direct choices are written on top, and the DOB is re-cut
    whenever the age changes -- because the card prints DD/MM/YY and a record
    whose age and DOB disagree is a forgery a customs officer would catch.
    """
    bad = [k for k in choices if k not in CHOICES]
    if bad:
        raise KeyError(f"not a choosable field: {bad}. "
                       f"choosable: {list(CHOICES)}")
    nid = player_id(seed)
    species = choices.get("species") or _draw_species(nid)
    if species not in sched.RHYTHMS:
        raise KeyError(f"species {species!r} has no rhythm in schedule.RHYTHMS "
                       f"({sorted(sched.RHYTHMS)})")
    role_key = choices.get("role") or RES.sched.role_for(nid, species).key
    card = _rederive(nid, species, role_key)
    direct = {k: v for k, v in choices.items() if k in DIRECT}
    if direct:
        card = replace(card, **direct)
    if "age" in direct:
        dob, dob_card = RES._dob(nid, int(direct["age"]))
        card = replace(card, dob=dob, dob_card=dob_card)
    return Player(card=card, at=at, credits=credits_for(nid, card.role),
                  carrying=(IDENTICARD, KIT_BAG), status=UNPROCESSED,
                  quarters="", generated=not choices)


# ---------------------------------------------------------------------------
# THE ASSERTION THIS MODULE EXISTS TO MAKE
# ---------------------------------------------------------------------------
_RESIDENT_FIELDS = tuple(f.name for f in fields(RES.Resident))


def indistinguishable(p: Player):
    """Is the player's record the same THING an NPC's is? (ok, detail).

    Four claims, weakest to strongest, and they are separate because they fail
    separately:

      1. it is a `Resident` BY TYPE, not by shape -- a namedtuple with the same
         field names must not pass, which is the negative control;
      2. it carries every one of the record's fields with a value the station
         needs -- a home that is a real place, a species with a rhythm;
      3. every consumer written for an NPC accepts it unmodified;
      4. for an ungenerated (i.e. unchosen) player, the record is BIT-IDENTICAL
         to what `resident()` returns for that id -- the player is not merely
         like an NPC, they ARE the NPC that id resolves to.
    """
    c = p.card
    if type(c) is not RES.Resident:
        return False, f"the card is a {type(c).__name__}, not a Resident"
    missing = [f for f in _RESIDENT_FIELDS if not hasattr(c, f)]
    if missing:
        return False, f"the record is missing {missing}"
    # `directory.by_key` RAISES for an unknown key rather than returning None,
    # which is the right shape for the register and the wrong shape for a
    # predicate -- so it is caught here rather than pre-checked, and the empty
    # string is included in what it rejects.
    try:
        home = dr.by_key(c.home)
    except KeyError:
        return False, f"home {c.home!r} is not a place in the register"
    # `informal_residence` COUNTS, and finding out that it had to is the useful
    # half of this check. The first version asked for `residence` and failed on
    # 19 of 200 random players -- every one of them a lurker, because
    # `downbelow`, `downbelow_arch` and `subfloor_stack` declare
    # `informal_residence` and NOT `residence`. That is not a register defect,
    # it is the register being precise: Downbelow is squatted, not housed, and
    # FACTIONS.md 11.2's underclass is exactly the population whose address is
    # not a tenancy. A player can be one of them, so the predicate has to admit
    # them -- while still rejecting a home that is a workshop or a bar.
    HOMELY = ("residence", "informal_residence")
    if not set(home["functions"]) & set(HOMELY):
        return False, (f"home {c.home!r} is {home['functions']}, none of "
                       f"which is somewhere anybody lives")
    if c.species not in sched.RHYTHMS:
        return False, f"species {c.species!r} has no rhythm"
    try:
        RES.identicard(c)
        RES.where_at(c, 13.0)
        RES.describe(c)
        c.activity_at(13.0)
    except Exception as e:                                  # pragma: no cover
        return False, f"a consumer written for an NPC rejected it: {e!r}"
    if p.generated and RES.resident(c.npc_id, c.species) != c:
        return False, ("an unchosen player's record is not what resident() "
                       "returns for that id")
    return True, (f"{c.species}/{c.role}, home {c.home}, "
                  f"card {len(RES.identicard(c))} fields")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def dossier(p: Player, out=print) -> None:
    RES.dossier(p.card, out=out)
    out(f"      credits     : {p.credits} "
        f"({'can' if p.can_afford_passage() else 'CANNOT'} afford the "
        f"{PASSAGE_HOME_CR:.0f} cr passage home)")
    out(f"      carrying    : {', '.join(p.carrying) or '(nothing)'}")
    out(f"      status      : {p.status}"
        + (f", quarters {p.quarters}" if p.quarters else ""))


def report(out=print):
    out("THE PLAYER -- a resident, built by the machinery that builds the rest")
    out("")
    out(f"species mix: {len(PLAYABLE_MIX)} playable of "
        f"{len(sched.STATION_MIX)} in the census (Kosh is a singleton, "
        f"not a share)")
    out(f"credits: {CREDIT_MIN:.0f}-{CREDIT_MAX:.0f}, skew {CREDIT_SKEW:.4f} "
        f"SOLVED so {LEAK_RATE:.0%} land under the {PASSAGE_HOME_CR:.0f} cr "
        f"passage home -- TRAFFIC-AND-CUSTOMS 6.6")
    out("")
    out("FIVE RANDOM PLAYERS -- nothing chosen")
    for s in ("a", "b", "c", "d", "e"):
        p = random_player(s)
        ok, why = indistinguishable(p)
        out(f"  seed {s}: {p.describe()}  [{p.credits} cr]"
            + ("" if ok else f"   NOT A RESIDENT: {why}"))
    out("")
    out("ONE IN FULL")
    dossier(random_player("a"))
    out("")
    out("THE CHARACTER CREATOR IS FIELD OVERRIDES ON THAT SAME RECORD")
    for ch in ({"species": "narn"},
               {"species": "narn", "role": "diplomat"},
               {"species": "centauri", "role": "financier",
                "forename": "Anton"},
               {"species": "human", "role": "lurker"}):
        p = player_from(ch)
        out(f"  {str(ch):<58} -> {p.describe()}")


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
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

    # -- 1. the player IS a resident ---------------------------------------
    p = random_player("a")
    ok, why = indistinguishable(p)
    check("a random player is indistinguishable from an NPC", ok, why)

    # NEGATIVE CONTROL, and it is the one that matters: a duck-typed lookalike
    # carrying every field name must FAIL, or `indistinguishable` is testing
    # shape rather than type and the claim is empty.
    import collections
    Fake = collections.namedtuple("Fake", _RESIDENT_FIELDS)
    fake = Fake(**{f: getattr(p.card, f) for f in _RESIDENT_FIELDS})
    ok2, why2 = indistinguishable(Player(card=fake))
    check("...and a namedtuple with all 27 field names does NOT pass",
          not ok2, why2)

    # NEGATIVE CONTROL 2: a real Resident with its home blanked must fail, or
    # the check only ever looked at the type.
    homeless = replace(p.card, home="")
    ok3, why3 = indistinguishable(Player(card=homeless))
    check("...and a Resident with no home does NOT pass", not ok3, why3)

    # -- 2. every random player, not just the lucky one --------------------
    bad = []
    for i in range(200):
        q = random_player(f"s{i}")
        o, w = indistinguishable(q)
        if not o:
            bad.append((i, w))
    check("200 random players are all residents with somewhere to live",
          not bad, f"{len(bad)} bad" + (f": {bad[:3]}" if bad else ""))

    # -- 3. determinism -----------------------------------------------------
    check("a seed gives the same person twice",
          random_player("k").card == random_player("k").card)
    check("...and two seeds give different people",
          random_player("k").card != random_player("k2").card)

    # -- 4. the mix is the station's ---------------------------------------
    seen = {}
    for i in range(4000):
        seen[_draw_species(f"n{i}")] = seen.get(_draw_species(f"n{i}"), 0) + 1
    check("the draw reaches every species in the census except the Vorlon",
          set(seen) == set(PLAYABLE_MIX),
          f"{len(seen)} of {len(PLAYABLE_MIX)}; missing "
          f"{sorted(set(PLAYABLE_MIX) - set(seen))}")
    check("...and never draws Kosh, who is a person and not a proportion",
          "vorlon" not in seen)
    h = seen.get("human", 0) / 4000.0
    want = PLAYABLE_MIX["human"] / sum(PLAYABLE_MIX.values())
    check("the human share of 4,000 draws matches the census share",
          abs(h - want) < 0.03, f"{h:.3f} against {want:.3f}")

    # -- 5. THE CHARACTER CREATOR ------------------------------------------
    chosen = player_from({"species": "narn"})
    check("a chosen species gives a Narn", chosen.card.species == "narn")
    check("...whose ORIGIN is NARN, not EARTH",
          chosen.card.origin == "NARN", chosen.card.origin)
    # NEGATIVE CONTROL: the naive `replace(species=...)` a creator would write
    # first. Count the fields that end up disagreeing with the choice -- if the
    # number is zero, re-derivation buys nothing and this module is overbuilt.
    naive = replace(random_player("player").card, species="narn")
    disagree = [f for f in ("origin", "surname", "forename", "home", "job",
                            "atmos_class", "medical", "phys_chr", "age",
                            "dob_card", "visas", "role", "stature_m")
                if getattr(naive, f) != getattr(chosen.card, f)]
    check("...and a naive replace() would have left the record contradicting "
          "itself, which is why generative choices re-derive",
          len(disagree) >= 3, f"{len(disagree)} fields differ: {disagree}")

    # A chosen ROLE has to move the home, or `home_for` is not being consulted.
    dip = player_from({"species": "narn", "role": "diplomat"})
    check("a chosen role of diplomat re-derives the home through home_for",
          dip.card.home == "ambassadorial_suites", dip.card.home)
    lur = player_from({"species": "human", "role": "lurker"})
    check("...and a lurker's home is one of Downbelow's three",
          lur.card.home in RES.DOWNBELOW_HOMES, lur.card.home)
    check("...and a lurker has no job aboard", lur.card.job == "",
          repr(lur.card.job))
    # NEGATIVE CONTROL for the role path: a role nobody declares must raise
    # rather than silently produce a person with no workplace.
    try:
        player_from({"role": "starship_captain"})
        raised = False
    except KeyError:
        raised = True
    check("...and an undeclared role raises instead of building a nobody",
          raised)

    # A direct field is written through untouched.
    nm = player_from({"species": "centauri", "forename": "Anton"})
    check("a direct field override lands verbatim on the card",
          nm.card.forename == "Anton" and nm.card.card_name.startswith("A")
          is False or nm.card.forename == "Anton",
          nm.card.card_name)
    try:
        player_from({"eye_colour": "blue"})
        raised2 = False
    except KeyError:
        raised2 = True
    check("...and a field the record does not have raises", raised2)

    # An overridden AGE re-cuts the DOB, or the card prints two ages.
    aged = player_from({"species": "human", "age": 51})
    check("an overridden age re-cuts the DOB the card prints",
          aged.card.dob[0] == RES.ERA_YEAR - 51,
          f"age {aged.card.age}, DOB {aged.card.dob_card} "
          f"(year {aged.card.dob[0]})")

    # -- 6. credits, and the derivation --------------------------------------
    poor = sum(1 for i in range(4000)
               if credits_for(f"c{i}") < PASSAGE_HOME_CR) / 4000.0
    check("the credit distribution reproduces 6.6's 1% who cannot afford "
          "passage home -- the number the skew was SOLVED for",
          abs(poor - LEAK_RATE) < 0.005,
          f"{poor:.4f} against {LEAK_RATE:.4f}, skew {CREDIT_SKEW:.4f}")
    # NEGATIVE CONTROL: a flat draw. The share must move off 1% and fire it.
    flat = sum(1 for i in range(4000)
               if CREDIT_MIN + (CREDIT_MAX - CREDIT_MIN)
               * _u(f"c{i}", "credits") < PASSAGE_HOME_CR) / 4000.0
    check("...and a FLAT credit draw misses it, so the skew is doing the work",
          abs(flat - LEAK_RATE) > 0.02,
          f"flat gives {flat:.4f}, {flat / LEAK_RATE:.1f}x the target")

    # A LURKER CANNOT AFFORD TO LEAVE -- which is the entire canon explanation
    # of the underclass, and was false in this module until 4n.
    lurkers = [player_from({"species": "human", "role": "lurker"}, seed=f"L{i}")
               for i in range(40)]
    check("no lurker can afford the passage home -- the one fact the whole "
          "underclass rests on",
          all(not q.can_afford_passage() for q in lurkers),
          f"richest of 40 has {max(q.credits for q in lurkers)} cr against "
          f"the {PASSAGE_HOME_CR:.0f} cr fare")
    # NEGATIVE CONTROL: the role-blind draw, which is what this used to do.
    blind = [credits_for(player_id(f"L{i}")) for i in range(40)]
    check("...and the role-BLIND draw does not, which is why the draw reads "
          "the role", any(c >= PASSAGE_HOME_CR for c in blind),
          f"{sum(1 for c in blind if c >= PASSAGE_HOME_CR)}/40 of them could, "
          f"richest {max(blind)} cr")

    # -- 7. the mutable half -------------------------------------------------
    q = random_player("m")
    q.move_to("customs_north")
    check("a player stands in a register place", q.at == "customs_north")
    try:
        q.move_to("the_bridge_of_the_enterprise")
        raised3 = False
    except KeyError:
        raised3 = True
    check("...and cannot stand somewhere that does not exist", raised3)
    q.credits = 100
    check("spending more than you have fails and takes nothing",
          q.spend(200) is False and q.credits == 100)
    check("...and spending what you have goes through",
          q.spend(60) is True and q.credits == 40)
    q.drop(IDENTICARD)
    check("the identicard is an ITEM and can be lost", not q.has(IDENTICARD))
    check("...and the card RECORD survives it, because the station holds it",
          q.card.card_name == random_player("m").card.card_name)

    # -- 7b. THE BAG HAS A BOTTOM -------------------------------------------
    # An inventory with no ceiling has no `store` verb, only a `take` one.
    bag = random_player("bag")
    bag.carrying = ()
    took = [bag.take(f"thing_{i}") for i in range(CARRY_CAPACITY + 3)]
    check(f"the bag holds {CARRY_CAPACITY} things and refuses the "
          f"{CARRY_CAPACITY + 1}th",
          sum(took) == CARRY_CAPACITY and len(bag.carrying) == CARRY_CAPACITY
          and took[CARRY_CAPACITY] is False,
          f"{sum(took)} taken of {len(took)} offered, carrying "
          f"{len(bag.carrying)}")
    check("...and a full bag takes one more once something leaves it",
          (bag.drop("thing_0") or True) and bag.take("thing_99") is True
          and len(bag.carrying) == CARRY_CAPACITY,
          f"carrying {len(bag.carrying)}")
    check("...and re-taking what you already carry is not a refusal",
          bag.take(sorted(bag.carrying)[0]) is True)
    check("the ceiling sits inside the bracket its derivation states -- at "
          "least the two an arrival lands with plus one, at most the widest "
          "counter's line count",
          3 <= CARRY_CAPACITY <= 14,
          f"{CARRY_CAPACITY} in [3, economy.MAX_LINES=14]")

    # -- 7c. POSTURE, and it is `npc/animation.py`'s rule ---------------------
    # THE CHEAP PATH IS GATED AGAINST THE AUTHORITY. `posture` reads
    # `body.FIGURE` because `state()` is called on every transaction and a rig
    # build is 0.3 s; this is the assertion that stops that shortcut becoming a
    # second description of where a knee is.
    from npc import animation as AN                            # noqa: PLC0415
    worst = ("", 0.0)
    for sp in ("human", "narn", "centauri", "minbari"):
        rg = AN.rig(sp, AN.NOMINAL, 0)
        got = posture(sp, rg.skel.stature_m)
        d = abs(got["seat_m"] - AN.seat_height(sp))
        dh = abs(got["hip_m"] - (rg.skel.head("hip_r")[1] - rg.skel.ground_y))
        if max(d, dh) > worst[1]:
            worst = (sp, max(d, dh))
    check("the cheap posture agrees with animation.seat_height and the rig's "
          "own hip, so the shortcut cannot drift from the skeleton",
          worst[1] <= FIT_TOL_M,
          f"worst is {worst[0]} at {worst[1] * 1000:.1f} mm against a "
          f"{FIT_TOL_M * 1000:.0f} mm tolerance")
    # NEGATIVE CONTROL: the drop has to be a real distance, or "sitting" is a
    # camera that does not move.
    hp = random_player("a")
    po = posture(hp.card.species, hp.card.stature_m)
    drop = po["hip_m"] - po["seat_m"]
    check("...and sitting drops the eye by a distance a player would see",
          0.25 <= drop <= 0.75,
          f"{hp.card.species} at {hp.card.stature_m:.2f} m drops "
          f"{drop:.3f} m from hip {po['hip_m']:.3f} to seat {po['seat_m']:.3f}")

    # -- 7d. THE PURSE CARRIES WHAT THE ENGINE CANNOT RECOMPUTE --------------
    # `godot/scripts/player.gd` reads `economy.json` and nothing else of this
    # module reaches a runtime, so a key missing here is a mechanic missing in
    # the game -- which is exactly the shape of the ten built-but-unreachable
    # defects this project has produced.
    st = random_player("w").state()
    want = ("tier", "tier_name", "hip_m", "seat_m", "recline_m", "carry_cap",
            "wake_h", "name")
    gone = [k for k in want if k not in st]
    check("the purse carries the rung, the posture, the bag size and the "
          "wake hour -- the four things the engine cannot derive",
          not gone, f"missing {gone}" if gone else f"{len(st)} keys")
    back = from_state(st)
    check("...and none of them is RESTORED, because every one is a function "
          "of a card `from_state` regenerates",
          back.tier == st["tier"] and back.card.card_name == st["name"],
          f"tier {back.tier} == {st['tier']}, name {back.card.card_name!r}")

    # -- 8. the record is frozen ---------------------------------------------
    try:
        object.__setattr__  # noqa: B018
        p.card.origin = "MARS"
        froze = False
    except Exception:
        froze = True
    check("the identicard record is FROZEN -- a player does not edit what the "
          "station holds about them", froze)

    # -- 9. what the player KNOWS travels with the purse ---------------------
    # PLY-07 through the one channel this simulation has to a runtime. The
    # claim is not "a journal exists": it is that a fact learned on this
    # record comes back on a record rebuilt from the saved state, because
    # `docs/MASTER-PLAN.md` R7's whole argument for putting the journal in P2
    # is that *"a journal with no save is a notebook that forgets"*.
    import journal as JN                                          # noqa: PLC0415
    q = random_player("journal-carrier")
    q.journal = JN.Journal()
    jfid = JN.mint_name_given(
        q.journal, {"group": "g", "who": {"id": "res:met",
                                          "name": "Delgado, Ruth"}},
        "customs_north", 0, 5.67)
    q.journal.move_standing("ea_lawful", +12.0, "you reported the fence")
    jst = json.loads(json.dumps(q.state()))
    r = from_state(jst)
    check("a fact learned survives the purse round trip, with its source event",
          r.journal is not None and r.journal.has(jfid)
          and "gave you their name" in r.journal.get(jfid).source,
          r.journal.get(jfid).line()[:100] if r.journal else "no journal")
    check("...and so do CAST-05's name-given flag and the standing ledger",
          r.journal.name_given("res:met")
          and r.journal.standing["ea_lawful"] == 12.0,
          "name_given=%s ea_lawful=%s" % (r.journal.name_given("res:met"),
                                          r.journal.standing["ea_lawful"]))
    # NEGATIVE CONTROL: a player who learned nothing must come back with NO
    # journal rather than an empty one, or the key would be written into every
    # purse in `economy.json` and the round trip above would pass on a record
    # that never learned anything.
    blank = from_state(json.loads(json.dumps(random_player("blank").state())))
    check("...and a player who learned nothing carries no journal key at all",
          blank.journal is None and "journal" not in random_player("b").state(),
          "journal=%r" % blank.journal)

    out("")
    out(f"{n - len(failed)}/{n} passed")
    return not failed


if __name__ == "__main__":                                   # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--make", nargs="*", metavar="field=value",
                    help="build one player from choices and print the dossier")
    ap.add_argument("--seed", default="player")
    a = ap.parse_args()
    if a.make is not None:
        ch = dict(x.split("=", 1) for x in a.make)
        if "age" in ch:
            ch["age"] = int(ch["age"])
        pl = player_from(ch, seed=a.seed)
        okk, whyy = indistinguishable(pl)
        dossier(pl)
        print(f"\n  indistinguishable from an NPC: "
              f"{'yes' if okk else 'NO'} -- {whyy}")
        raise SystemExit(0)
    if a.report and not a.selftest:
        report()
        raise SystemExit(0)
    good = _selftest()
    if a.report:
        print()
        report()
    raise SystemExit(0 if good else 1)
