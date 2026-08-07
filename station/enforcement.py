#!/usr/bin/env python3
"""WHAT HAPPENS NEXT -- a refusal is a rule only if somebody comes.

Session 4q wired `consequence.certain_check` into the game: 98 of 129 places
read your identicard on the way in, and walking into `vorlon_berth` as a citizen
puts IDENTICARD REFUSED on the HUD. The commit that landed it stated its own
limit in as many words:

    "the arrest chain behind a refusal (`consequence.arrest` -> brig -> fine ->
     release) is still Python. A refused player is TOLD they are refused and is
     not yet detained."

A refusal a player can walk away from unharmed is a SIGN, not a rule. This
module is the join, and it is the thirteenth instance of the same defect: two
finished halves -- `consequence.arrest`'s whole custody pipeline on one side,
`npc.gd`'s instanced walkers and `interact.gd`'s ledger on the other -- with
nothing between them.

WHAT IT DOES NOT DO, AND THE REASON IS HARD RULE 4. It computes nothing. Every
number below comes out of `consequence.py` or `npc/security.py` and is written
into `station/generated/scene/enforcement.json` as a RESULT, exactly the way
`boot.py::_checks` bakes `certain_check`'s result rather than its rule. The
engine holds no copy of P-05, of the offence table, of the fine ladder, or of
where the brig is. If it did, the two would drift and one of them would be
wrong on a Tuesday.

THE FOUR THINGS A PLAYER MEETS, and each is derived rather than authored:

  1. SOMEBODY COMES, AND WHEN THEY COME IS THE PLACE'S OWN ANSWER.
     `security.response_from_nearest_post` routes from every fixed post on the
     station on the graph a resident commutes on. On the boot deck that is
     **0 s at `docking_bays`** -- there is a post standing in it -- and
     **227 s at `lowg_bays`**, from `customs_north`. LAW-CRIME 2.6's headline
     is a CONTRAST rather than a number, and this is that contrast arriving as
     arithmetic.

  2. THEY HAVE NAMES AND ONE OF THEM WEARS THE ARMBAND. `security.patrol`
     returns a pair, and it deliberately does not roll the Nightwatch boolean
     twice and hope -- FACTIONS 5.3 calls one band and one bare sleeve in the
     same pair the best environmental storytelling on the station.

  3. MOST OF THE TIME NOTHING HAPPENS TO YOU, WHICH IS THE POINT.
     LAW-CRIME 2.7 rung 3 -- "Move on. No arrest, no record. The standard
     Downbelow-in-a-commercial-area outcome" -- is the commonest disposal, and
     `consequence.DETAIN_ON_FAIL` already prices it at one in five. A build
     where every refusal ends in the brig would be a worse lie than a build
     where none of them does, because it would make the brig meaningless.

  4. WHEN IT DOES, IT COSTS. `consequence.arrest` runs the whole pipeline:
     respond, escort to the brig on the routed graph, book, hold to the next
     Ombuds sitting, court, release, fine, record, rung. The fine moves in the
     ledger a drink moves through; the hold moves the station clock; the
     conviction is written into the purse and survives the process.

THE FORK IS PER EVENT AND IT IS DETERMINISTIC (INV-550). `consequence.py` has
carried `DETAIN_ON_FAIL = 0.20` since P1-G2 and used it only as a RATE, inside
`day_arrests`, where it prices a station-day. A player meets it as a single
event, so it has to resolve to a yes or a no for THIS refusal -- and it resolves
through `consequence._u`, the same hash every other per-person draw in that
module uses, keyed on (npc_id, place, day, how many times you have been stopped
here). Reload the save and the same refusal comes out the same way; walk in a
second time and it is a new draw.

WHY THE BAKE IS PER PLACE AND PER HOUR, and why that is not 24 copies of a rule.
Only ONE leg of the chain depends on the clock: the hold runs to the next 08:00
Ombuds sitting, so a 09:00 arrest is held 23 hours and a 07:00 arrest is held
one. Everything else -- response, escort, booking, court, release, the fine, the
disposal, the rung -- is hour-independent, which was measured rather than
assumed. So the table carries the hold and the total for each of the 24 hours
and the engine INDEXES it. It does not add anything up.

Run:
    python3 station/enforcement.py --report      # the table, for the boot deck
    python3 station/enforcement.py --report --all
    python3 station/enforcement.py --bake        # write the engine's sidecar
    python3 station/enforcement.py --selftest    # the arithmetic, with controls
    python3 station/enforcement.py --gate        # THE ENGINE GATE: somebody comes
    python3 station/enforcement.py --gate --legacy   # today's build: nobody does
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import consequence as cq                                          # noqa: E402
import directory as dr                                            # noqa: E402
import player as PL                                               # noqa: E402
from npc import security as sec                                   # noqa: E402

GODOT_DIR = os.path.join(ROOT, "godot")
GEN = os.path.join(ROOT, "station", "generated")
SCENE = os.path.join(GEN, "scene")
BOOT_JSON = os.path.join(SCENE, "boot.json")
LEDGER = os.path.join(GEN, "economy.json")
OUT_JSON = os.path.join(SCENE, "enforcement.json")

# ===========================================================================
# 1.  WHICH OFFENCE A REFUSAL IS -- and no new offence was invented for it
# ===========================================================================
# `OFFENCES` already carries the row, with its source sentence attached:
#
#   ("id_check_fail", 1, 2, 5, "a card that does not read. 2.7 rung 2 is the
#    commonest interaction and most of its failures end at rung 3")
#
# That IS a refusal at a reader: the card was read and it did not admit you.
# Escalation rung 2, and the table's own note says where most of them end.
REFUSAL_OFFENCE = "id_check_fail"

# And rung 3 is a row of the same table, so "nothing happens to you" is a
# disposal `consequence.arrest` can produce rather than a branch taken here.
MOVED_ON_OFFENCE = "move_on"

# HOW MANY SUCCESSIVE DETENTIONS THE TABLE CARRIES. Three, so that
# `consequence.REVOKE_ON_ORDINARY`'s "survives one and not two" is inside the
# window with the state after it -- baking one would make the ladder invisible
# and baking ten would bake a tail nobody reaches. The engine WRAPS this index
# rather than falling through to "moved on" on the fourth stop; a rule that
# switches itself off the moment somebody tests it is worse than either answer.
#
# WHAT THE LADDER ACTUALLY DOES FOR *THIS* OFFENCE IS NOTHING, and that is the
# answer rather than a gap: `Record.ordinary()` counts grade-2 convictions and
# `id_check_fail` is grade 1. A refusal at a door never costs you your standing.
# See `--selftest` check 4 and its grade-2 positive control.
CONVICTIONS_BAKED = 3

# THE OFFICER'S WALKING SPEED, and it is not a new number. `life.gd`'s Director
# walks a commuting resident at this, off `agenda`'s own gait; an officer
# crossing a room to reach you is the same body on the same deck.
WALK_SPEED_MS = 1.30


def _detain_draw(npc_id: str, place_key: str, day: int, nth: int,
                 seed: str = "b5") -> bool:
    """Does THIS refusal end in detention? INV-550.

    `consequence.DETAIN_ON_FAIL` is 0.20 and has only ever been used as a rate.
    A player meets it once, so it has to be a draw -- and it is drawn through
    `consequence._u`, which is that module's own hash, so the fork lives on the
    same seed line as every fine, every deferral and every discretionary stop.
    """
    return cq._u("detain_on_refusal", npc_id, place_key, day, nth,
                 seed) < cq.DETAIN_ON_FAIL


# ===========================================================================
# 2.  THE PLAYER, AND WHOSE RUNG THE ENGINE IS ACTUALLY HOLDING
# ===========================================================================
def player_from_ledger(path: str = None):
    """The played session's own person, rebuilt so the ENGINE agrees with it.

    THE DEFECT THIS WORKED AROUND IS FIXED. `player.from_state` now recovers a
    chosen role from the saved `role` field and raises if the rebuilt rung and
    the stored rung disagree, so it and this function agree on the shipped
    purse: both give `lurker`, rung 0. **This is kept anyway, and not because
    it is still needed** -- it is a second, independently-written derivation of
    the same person from the same file, and this module's gate compares them.
    A duplicate that CHECKS is not the same thing as a duplicate that DRIFTS.
    Retire it only together with the assertion below.

    The finding, kept because the reasoning is the valuable part. `from_state`
    regenerates the card from `(npc_id, species)` alone -- deliberately, because
    a save must not be able to describe a person the station would not produce
    -- but `player.player_from(choices)` mints a card with a CHOSEN role, and
    that choice is not in the id. So for the purse this repository ships, before
    the fix:

        stored in economy.json   role=lurker   tier=0  no_status
        player.from_state(...)   role=service  tier=4  citizen

    The engine reads the stored field and every Python caller that reloads the
    purse gets the other one. Two descriptions of one person, disagreeing about
    the exact number this whole module is a consequence of: at tier 0 the
    disposal is "already at the floor, next stop is transfer off-station"; at
    tier 4 it is "EA citizenship is not revocable". Two different games.

    So this rebuilds through `player_from` with the role the purse recorded, and
    then ASSERTS the rung it got equals the rung the engine holds. A mismatch
    raises rather than being quietly repaired, because a bake that silently
    disagreed with the HUD would be worse than no bake.
    """
    path = path or LEDGER
    with open(path) as f:
        led = json.load(f)
    purses = led.get("purses") or {}
    keys = sorted(purses)
    mine = next((k for k in keys if k.startswith("player:")), keys[0] if keys
                else None)
    if mine is None:
        raise KeyError(f"{path} holds no purse -- run the ledger first")
    st = purses[mine]
    seed = mine.split(":", 1)[1] if ":" in mine else mine
    pl = PL.player_from({"species": st.get("species", "human"),
                         "role": st.get("role", "")}, seed=seed)
    pl.restore({k: v for k, v in st.items() if k != "npc_id"})
    if int(st.get("tier", -99)) != int(pl.tier):
        raise ValueError(
            f"the purse says tier {st.get('tier')} ({st.get('tier_name')}) and "
            f"the rebuilt card says {pl.tier} ({pl.tier_name}). The engine is "
            f"holding the first and this bake would be about the second. Fix "
            f"`player.from_state` (see this function's docstring) or re-seed "
            f"the ledger; do not paper over it.")
    return pl, st


# ===========================================================================
# 3.  THE PLACES THE ENGINE CAN ACTUALLY NAME
# ===========================================================================
def boot_rooms(path: str = None) -> list:
    """The rooms the shipped build has, from the file the shipped build reads.

    THE SAME SCOPING RULE `boot.py::_collapses` USES, and for the same reason:
    an arrest in a place the player cannot walk to is a row nothing will ever
    read. `hud.gd` resolves a place from the interact sidecar's boxes, and
    `boot.json::rooms` is the list those boxes come from, so baking against it
    means the table's keys and the HUD's keys are the same keys by construction.
    """
    path = path or BOOT_JSON
    try:
        with open(path) as f:
            return [str(r) for r in (json.load(f).get("rooms") or [])]
    except Exception:                                             # noqa: BLE001
        return []


def checked_places(keys=None) -> list:
    """Of those, the ones that read a card at all -- `certain_check` decides."""
    keys = keys if keys is not None else [q["key"] for q in dr.PLACES]
    out = []
    for k in keys:
        try:
            ok, _why = cq.certain_check(k)
        except Exception:                                         # noqa: BLE001
            continue
        if ok:
            out.append(k)
    return out


# ===========================================================================
# 4.  ONE PLACE, END TO END
# ===========================================================================
def _officers(place_key: str, index: int = 0) -> list:
    p = sec.patrol(place_key, index)
    return [{"id": o["id"],
             "name": o["resident"].name,
             "card_name": o["resident"].card_name,
             "species": o["resident"].species,
             "armband": bool(o["armband"])} for o in p["officers"]]


def _custody_row(c) -> dict:
    """One rung of the ladder, and NOT one credit of anybody's money.

    THE KEY IS `fine_subject` AND THE RENAME IS THE FIX. Session 4t round 1
    baked `"fine": round(c.fine, 2)` here, and `c.fine` is
    `consequence.fine_amount(offence, npc_id, seed)` -- a draw keyed on the
    PERSON. The engine then read that scalar and debited it from whoever
    `interact.gd::_my_purse` had loaded, which is a different person the moment
    the ledger on disk is not the ledger the bake read. It measured 187.66 cr
    debited against a 206.63 cr booking record in the same run, and nothing
    asserted the two were the same number.

    The general rule this is an instance of, because the same defect was in
    `brig_cell` one key up and would have been in the next per-person draw
    somebody baked: **a draw keyed on the person may not be baked as a scalar
    in a table the engine indexes for whoever it loaded.** What is baked is the
    BAND (`offence[k].fine_lo/fine_hi`, which are policy and person-independent)
    and the draw is taken in the engine off the live `npc_id`, through the same
    blake2b `consequence._u` uses. `enforcement.gd::u()` is that hash, and
    `draw_check` below is the test vector that proves the two agree.

    The value is kept rather than deleted because `--report` prints a worked
    example for a named person and that is worth having. It is renamed so that
    an engine that still reads `fine` gets nothing and says so loudly, instead
    of quietly charging a stranger's number.
    """
    return {"disposal": c.disposal, "reason": c.reason,
            "offence": c.offence,
            "fine_subject": round(float(c.fine), 2),
            "paid": bool(c.paid),
            "outstanding": round(float(c.outstanding), 2),
            "tier_before": int(c.tier_before), "tier_after": int(c.tier_after),
            "tier_before_name": cq.tier_name(c.tier_before),
            "tier_after_name": cq.tier_name(c.tier_after),
            "revoked": bool(c.revoked),
            "deferrals": int(c.deferrals),
            "line": c.line()}


def place_row(place_key: str, pl, day: int = 1, seed: str = "b5") -> dict:
    """Everything that follows a refusal at one place, for one person.

    EVERY CALL BELOW GETS ITS OWN PLAYER. `consequence.arrest` MUTATES the
    record it is handed -- that is the point of it -- so twenty-four hourly
    calls on one player would be twenty-four convictions and the disposal of the
    24th would be baked as the disposal of the first. The hour sweep therefore
    runs on a throwaway clone and the conviction ladder runs on its own.
    """
    need, why_need = cq.required_tier(place_key)
    ok, why_check = cq.certain_check(place_key)
    r = sec.response_from_nearest_post(place_key, cq.graph())
    if r["seconds"] is None:
        raise KeyError(f"no post can reach {place_key}: that is a hole in the "
                       f"navgraph, not a fact about policing")

    def clone():
        p2 = PL.player_from({"species": pl.card.species,
                             "role": pl.card.role},
                            seed=pl.npc_id.split(":", 1)[-1])
        p2.credits = pl.credits
        return p2

    # -- the hour sweep: the ONLY leg the clock moves ------------------------
    hold_h, total_h = [], []
    legs = None
    for h in range(24):
        c = cq.arrest(clone(), place_key, REFUSAL_OFFENCE, hour=float(h),
                      day=day, seed=seed)
        hold_h.append(round(c.hold_s, 1))
        total_h.append(round(c.total_s, 1))
        if legs is None:
            legs = {"escort_s": round(c.escort_s, 1),
                    "booking_s": round(c.booking_s, 1),
                    "court_s": round(c.court_s, 1),
                    "release_s": round(c.release_s, 1)}
    # THE CLAIM THAT MAKES THE 24-ROW TABLE HONEST, asserted rather than
    # asserted-in-prose: if any leg but the hold moved with the hour, indexing
    # the hold alone would be wrong and the totals would be a fiction.
    for h in range(24):
        want = (r["seconds"] + legs["escort_s"] + legs["booking_s"]
                + hold_h[h] + legs["court_s"] + legs["release_s"])
        if abs(want - total_h[h]) > 0.2:
            raise AssertionError(
                f"{place_key} {h:02d}:00 -- the legs sum to {want:.1f} s and "
                f"the chain reports {total_h[h]:.1f}. Something other than the "
                f"hold depends on the clock, so the baked table is wrong.")

    # -- the conviction ladder: one person, stopped three times --------------
    ladder, p3 = [], clone()
    for i in range(CONVICTIONS_BAKED):
        c = cq.arrest(p3, place_key, REFUSAL_OFFENCE, hour=13.0, day=day,
                      seed=seed)
        row = _custody_row(c)
        row["convictions_after"] = len(cq.record_of(p3).convictions)
        ladder.append(row)

    # -- the same ladder from every OTHER rung -------------------------------
    # WHY IT IS BAKED AND NOT DERIVED IN THE ENGINE. `--tier=N` forces the card
    # (`main.gd::_check_gate` writes the rung onto `player.gd`, because it is the
    # identicard that changed and not the reader), and the whole interest of the
    # ladder is that the consequence of a conviction is DIFFERENT at each rung:
    # a transit visa is withdrawn on the second ordinary conviction, EA
    # citizenship cannot be withdrawn by an Ombuds at all, and the floor rung has
    # nothing left to take. A build that showed one of those for all six would be
    # a rule with the interesting half filed off.
    #
    # `_dispose` is `consequence.py`'s own disposal rule and is called here
    # rather than re-derived. The fine is per (offence, person) and does not
    # move with the rung, so it comes off the ladder above.
    by_tier = {}
    for t in cq.RUNGS:
        if t == cq.ACCREDITED:
            by_tier[str(t)] = [{"tier_before": t, "tier_after": t,
                                "tier_before_name": cq.tier_name(t),
                                "tier_after_name": cq.tier_name(t),
                                "revoked": False,
                                "disposal": "immunity -- the file dies "
                                            "(LAW-CRIME 4.3 step 4)",
                                "reason": "diplomatic immunity, LAW-CRIME 4.1",
                                "fine_subject": 0.0}
                               for _i in range(CONVICTIONS_BAKED)]
            continue
        rec, seq, t_now = cq.Record(), [], t
        for i in range(CONVICTIONS_BAKED):
            rec.convictions += (REFUSAL_OFFENCE,)
            after, revoked, why = cq._dispose(
                t_now, rec, cq.OFFENCE[REFUSAL_OFFENCE][1])
            seq.append({"tier_before": t_now, "tier_after": after,
                        "tier_before_name": cq.tier_name(t_now),
                        "tier_after_name": cq.tier_name(after),
                        "revoked": bool(revoked),
                        "disposal": ("fine paid"
                                     + (" + status revoked" if revoked else "")),
                        "reason": why,
                        "fine_subject": ladder[i]["fine_subject"]})
            t_now = after
        by_tier[str(t)] = seq

    # -- and the disposal when it is NOT a detention -------------------------
    moved = cq.arrest(clone(), place_key, MOVED_ON_OFFENCE, hour=13.0, day=day,
                      seed=seed)

    # -- THE SECOND ROW OF THE RULE: what the search finds --------------------
    # The table above is the whole engine path and it carries ONE offence, and
    # that offence is grade 1, so `--selftest` check 4's "a refusal at a door
    # never withdraws a permission, at ANY rung" was simultaneously true and the
    # reason the shipped build could not demote anybody. This is the other row:
    # a stop that SEARCHES you and finds `contraband` is grade 3, and
    # `REVOKE_ON_SERIOUS = 1` means one of them takes a conditional permission.
    # Same `_dispose`, same rungs, one grade heavier -- the positive control in
    # check 4, promoted to a thing a player can walk into.
    by_tier_c, ladder_c = {}, []
    p4 = clone()
    for _i in range(CONVICTIONS_BAKED):
        cc = cq.arrest(p4, place_key, DEMOTING_OFFENCE, hour=13.0, day=day,
                       seed=seed)
        ladder_c.append(_custody_row(cc))
    for t in cq.RUNGS:
        rec, seq, t_now = cq.Record(), [], t
        for i in range(CONVICTIONS_BAKED):
            rec.convictions += (DEMOTING_OFFENCE,)
            if t == cq.ACCREDITED:
                seq.append({"tier_before": t, "tier_after": t,
                            "tier_before_name": cq.tier_name(t),
                            "tier_after_name": cq.tier_name(t),
                            "revoked": False, "fine_subject": 0.0,
                            "disposal": "immunity -- the file dies "
                                        "(LAW-CRIME 4.3 step 4)",
                            "reason": "diplomatic immunity, LAW-CRIME 4.1"})
                continue
            after, revoked, why = cq._dispose(
                t_now, rec, cq.OFFENCE[DEMOTING_OFFENCE][1])
            seq.append({"tier_before": t_now, "tier_after": after,
                        "tier_before_name": cq.tier_name(t_now),
                        "tier_after_name": cq.tier_name(after),
                        "revoked": bool(revoked),
                        "disposal": ("fine paid"
                                     + (" + status revoked" if revoked else "")),
                        "reason": why,
                        "fine_subject": ladder_c[i]["fine_subject"]})
            t_now = after
        by_tier_c[str(t)] = seq
    legs_c = {"escort_s": round(cq._leg(cq.BRIG, place_key), 1),
              "booking_s": round(cq.BOOKING_H * 3600.0, 1),
              "court_s": round(cq._leg(cq.COURT, cq.BRIG), 1),
              "release_s": round(cq._leg(cq.BRIG, cq.COURT), 1)}

    return {
        "place": place_key,
        "name": dr.by_key(place_key).get("name", place_key),
        "need": int(need), "need_name": cq.tier_name(need),
        "why_need": why_need, "why_check": why_check, "reads_card": bool(ok),
        "respond_s": round(float(r["seconds"]), 1),
        "respond_from": r["from"],
        "respond_from_name": dr.by_key(r["from"]).get("name", r["from"]),
        "officers": _officers(place_key),
        "detain_p": cq.DETAIN_ON_FAIL,
        # The fork, drawn per event, for as many stops as the table carries.
        "detained": [bool(_detain_draw(pl.npc_id, place_key, day, i, seed))
                     for i in range(CONVICTIONS_BAKED)],
        "moved_on": {"disposal": moved.disposal, "rung": 3,
                     "offence": MOVED_ON_OFFENCE,
                     "line": "no arrest, no record (LAW-CRIME 2.7 rung 3)"},
        "detention": {"rung": 4, "offence": REFUSAL_OFFENCE,
                      "legs": legs, "hold_s_h": hold_h, "total_s_h": total_h,
                      "ladder": ladder, "ladder_by_tier": by_tier},
        # THE HOLD IS THE SAME HOLD. Only the disposal differs by offence, so
        # `hold_s_h`/`total_s_h` are NOT copied -- the engine indexes the rows
        # above and reads the ladder below. A second hold table would be a
        # second answer to "how long until the next Ombuds sitting".
        "search": {"rung": 4, "offence": DEMOTING_OFFENCE,
                   "grade": cq.OFFENCE[DEMOTING_OFFENCE][1],
                   "legs": legs_c, "ladder": ladder_c,
                   "ladder_by_tier": by_tier_c},
    }


# ===========================================================================
# 5.  THE BAKE
# ===========================================================================
def table(keys=None, day: int = 1, seed: str = "b5", ledger: str = None,
          out=None) -> dict:
    pl, st = player_from_ledger(ledger)
    keys = checked_places(keys if keys is not None else boot_rooms())
    rows = {}
    for k in keys:
        rows[k] = place_row(k, pl, day=day, seed=seed)
        if out:
            out(f"  {k}")
    return {
        "version": 1,
        "day": day, "seed": seed,
        "player": {"npc_id": pl.npc_id, "name": pl.card.card_name,
                   "species": pl.card.species, "role": pl.card.role,
                   "tier": int(pl.tier), "tier_name": pl.tier_name,
                   "credits": float(st.get("credits", pl.credits))},
        "walk_speed_ms": WALK_SPEED_MS,
        "revoke_on_ordinary": cq.REVOKE_ON_ORDINARY,
        "revoke_on_serious": cq.REVOKE_ON_SERIOUS,
        "brig": cq.BRIG, "court": cq.COURT,
        # WHERE THE BRIG IS, so the hold is a place a body can be put and not a
        # line of text. The engine gets a point and a box and no geometry rule.
        "brig_address": brig_address(),
        # THE CELL IS A DRAW ON THE PERSON, SO IT IS NOT BAKED AS A NUMBER.
        # Same defect and same fix as `_custody_row`'s fine, one key up: the
        # engine derives it from the live `npc_id` through `enforcement.gd::u`.
        # This is kept only so `--report` can print a worked example, and it is
        # NAMED for its subject so nothing can read it as "the cell".
        "brig_cell_subject": brig_cell(pl.npc_id, day, seed),
        "brig_cells": int(cq.BRIG_CELLS),
        # THE TEST VECTOR THAT MAKES THE ENGINE-SIDE HASH CHECKABLE. It is not a
        # second copy of a rule: these are four known answers from
        # `consequence._u`, so `enforcement.gd`'s blake2b can be shown to BE
        # `consequence._u` at load rather than producing a plausible wrong fine
        # nobody notices. A subtly wrong hash is the worst failure available
        # here, because every number it produces is inside the band.
        "draw_check": draw_vectors(seed),
        # What a search finds, and it is `economy.GOODS`' own contraband class.
        "restricted": list(restricted_goods()),
        # AND WHERE, IF ANYWHERE, A PLAYER COULD GET ONE. Baked because the
        # answer today is "nowhere in the shipped rooms", and an empty list
        # printed on every run is a gap somebody can close; a gap nothing
        # prints is a gap nobody knows about. See `restricted_sources`.
        "restricted_from": restricted_sources(),
        "demoting_offence": DEMOTING_OFFENCE,
        "tiers": {str(t): cq.tier_name(t) for t in (cq.DETAINED,) + cq.RUNGS},
        "offence": {k: dict(_offence_row(k)) for k in
                    (REFUSAL_OFFENCE, MOVED_ON_OFFENCE, DEMOTING_OFFENCE)},
        "places": rows,
    }


def _offence_row(k: str) -> dict:
    """One offence as the engine needs it -- grade, rung, AND THE FINE BAND.

    `fine_for` is `days * WAGE_LO .. days * WAGE_HI`, both of which are
    `economy.casual_constraint()`'s sourced wage band and neither of which
    depends on who is standing there. The band is policy and is baked; the
    point inside it is the person and is drawn in the engine.
    """
    v = cq.OFFENCE[k]
    lo, hi, days = cq.fine_for(k)
    return {"grade": v[1], "rung": v[2], "authority": v[3], "source": v[4],
            "fine_lo": round(float(lo), 2), "fine_hi": round(float(hi), 2),
            "fine_days": (None if days is None else float(days))}


def draw_vectors(seed: str = "b5") -> list:
    """Known answers from `consequence._u`, for the engine to check itself on.

    Deliberately NOT the draws the engine will make -- those depend on a person
    who does not exist at bake time. These are fixed strings whose only job is
    to fail if `enforcement.gd::u` is not blake2b-64 over `"|".join(parts)`.
    """
    vs = [("fine", DEMOTING_OFFENCE, "player:draw_check", seed),
          ("fine", REFUSAL_OFFENCE, "player:draw_check", seed),
          ("brig_cell", "player:draw_check", 3, seed),
          ("detain_on_refusal", "player:draw_check", "docking_bays", 3, 0,
           seed)]
    return [{"parts": [str(p) for p in v], "u": cq._u(*v)} for v in vs]


def restricted_sources() -> list:
    """Every counter in the shipped rooms that would sell you a restricted good.

    IT IS EMPTY TODAY AND THAT IS THE FINDING, not a bug in this function.
    `economy.json::stock` puts no `contraband`-class good behind any counter in
    `boot.json::rooms`, so the only route into the search branch is the harness
    flag `--arrest-contraband`, which is a test fixture and not a place. The
    list is baked and printed on every engine load so the gap is visible from
    inside the game rather than only from a spec ledger.

    `economy.py` is not this module's to change; `scratchpad/PATCHES-4t-g2.md`
    carries the two-line stock entry that would close it.
    """
    bad = set(restricted_goods())
    rooms = set(boot_rooms())
    out = []
    try:
        with open(LEDGER) as f:
            stock = (json.load(f).get("stock") or {})
    except Exception:                                             # noqa: BLE001
        return out
    for k in sorted(stock if isinstance(stock, dict) else ()):
        v = stock[k]
        place = k.split("/", 1)[0] if "/" in k else k
        names = (list(v) if isinstance(v, dict) else
                 [g.get("name", "") for g in v] if isinstance(v, list) else [])
        for n in sorted(names):
            if str(n) in bad:
                out.append({"where": k, "good": str(n),
                            "in_boot": bool(place in rooms)})
    return out


def emit(path: str = None, **kw) -> str:
    path = path or OUT_JSON
    d = table(**kw)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(d, f, indent=1, sort_keys=True)
    return path


# ===========================================================================
# 6.  REPORTS
# ===========================================================================
def report(all_places=False, out=print) -> dict:
    keys = None if all_places else boot_rooms()
    d = table(keys)
    p = d["player"]
    out(f"A REFUSAL, AND WHAT COMES OF IT -- for {p['name']} "
        f"({p['species']} {p['role']}), rung {p['tier']} {p['tier_name']}, "
        f"{p['credits']:.2f} cr")
    out("")
    out(f"{'place':<16}{'needs':<12}{'respond':>9}  {'from':<16}"
        f"{'who comes':<34}{'this stop':<10}")
    for k in sorted(d["places"]):
        r = d["places"][k]
        who = " + ".join(("%s%s" % (o["name"], "*" if o["armband"] else ""))
                         for o in r["officers"])
        out(f"{k:<16}{r['need_name']:<12}{r['respond_s']:>8.0f}s  "
            f"{r['respond_from']:<16}{who:<34}"
            + ("DETAINED" if r["detained"][0] else "moved on"))
    out("")
    out("  * wears the Nightwatch armband (FACTIONS 5.3)")
    out("")
    out("THE CHAIN, when it is a detention -- every leg routed:")
    out("")
    out(f"{'place':<16}{'respond':>8}{'escort':>8}{'hold@13':>9}{'court':>7}"
        f"{'total':>9}{'fine':>8}  disposal")
    for k in sorted(d["places"]):
        r = d["places"][k]
        det = r["detention"]
        c1 = det["ladder"][0]
        out(f"{k:<16}{r['respond_s']:>7.0f}s{det['legs']['escort_s'] / 60:>7.1f}m"
            f"{det['hold_s_h'][13] / 3600:>8.1f}h"
            f"{det['legs']['court_s'] / 60:>6.1f}m"
            f"{det['total_s_h'][13] / 3600:>8.1f}h{c1['fine_subject']:>8.2f}  "
            f"{c1['disposal']}")
    out("")
    out("AND WHAT IT COSTS THE THIRD TIME -- the same person, stopped again:")
    k0 = sorted(d["places"])[0]
    for i, c in enumerate(d["places"][k0]["detention"]["ladder"]):
        out(f"  stop {i + 1} at {k0}: {c['tier_before_name']} -> "
            f"{c['tier_after_name']}, {c['fine_subject']:.2f} cr, {c['reason']}")
    return d


# ===========================================================================
# 7.  THE PYTHON SELFTEST -- with controls that must fire
# ===========================================================================
_FAILED = []
# COUNTED, NOT WRITTEN DOWN. The first version of the summary line held the
# number of checks as a literal and it was already wrong by one when the
# revocation check was split in two -- a self-test that misreports its own size
# is a small instance of the thing this whole module is about.
_RAN = [0]


def check(ok, name, detail=""):
    _RAN[0] += 1
    _FAILED.append(name) if not ok else None
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f" -- {detail}" if detail
                                                    else ""))
    return ok


def control(claim, name, detail=""):
    """A control PASSES BY FAILING. `claim` is the same sentence the subject
    asserted, evaluated with one input taken away; if it is still true, the
    subject's check was not measuring that input and proves nothing."""
    if claim:
        _FAILED.append("control did not fire: " + name)
    print(f"  {'FIRED' if not claim else 'INERT'} control: {name}"
          + (f" -- {detail}" if detail else ""))
    return not claim


def selftest(out=print) -> bool:                                  # noqa: C901
    del out
    _FAILED.clear()
    _RAN[0] = 0
    print("enforcement.py -- the arithmetic behind a refusal")
    pl, st = player_from_ledger()
    check(int(pl.tier) == int(st["tier"]),
          "the rebuilt player is the rung the engine holds",
          f"{pl.tier} ({pl.tier_name}) == purse {st['tier']}")

    keys = checked_places(boot_rooms())
    check(len(keys) >= 1, "the boot deck has places that read a card",
          f"{len(keys)} of {len(boot_rooms())} rooms")

    d = table(keys)
    rows = d["places"]

    # 1. RESPONSE IS A CONTRAST, NOT A CONSTANT. If every place answered the
    #    same number the whole routed graph would be doing nothing.
    secs = sorted(r["respond_s"] for r in rows.values())
    check(secs[-1] - secs[0] > 30.0,
          "response time VARIES across the deck",
          f"{secs[0]:.0f} s at the nearest, {secs[-1]:.0f} s at the furthest")

    # 2. AND THE PLACE WITH A POST IN IT ANSWERS ZERO -- 2.6's own sentence.
    posted = [k for k, r in rows.items() if r["respond_s"] == 0.0
              and r["respond_from"] == k]
    check(bool(posted), "a place with its own post answers in zero seconds",
          ", ".join(sorted(posted)) or "none")

    # 3. THE PAIR IS SPLIT. FACTIONS 5.3.
    split = [k for k, r in rows.items()
             if len({o["armband"] for o in r["officers"]}) == 2]
    check(len(split) == len(rows), "every responding pair is one band, one bare",
          f"{len(split)} of {len(rows)}")

    # 4. A REFUSAL AT A DOOR NEVER COSTS YOU YOUR VISA, AND THAT IS THE ANSWER
    #    RATHER THAN A GAP. This check was written the other way round -- "the
    #    second conviction is where something is taken away" -- and it PASSED,
    #    because the shipped player stands on the floor rung where nothing is
    #    left to take. It could not have failed for the case it was named
    #    after. Asked at every rung it turns out to be false at all six, and the
    #    cause is one line of `consequence.py`: `Record.ordinary()` counts
    #    grade-2 convictions and `id_check_fail` is grade 1.
    #
    #    That is right. INV-347's ladder makes grade 1 one day of casual labour
    #    -- a citation -- and a station that withdrew a transit visa for two
    #    citations would have no middle to its own escalation. What DOES revoke
    #    is a grade-2 conviction, which is a different verb (carrying, theft,
    #    expired status), and the positive control below proves the machinery
    #    is live rather than absent.
    k0 = sorted(rows)[0]
    by_tier = rows[k0]["detention"]["ladder_by_tier"]
    ever = [t for t, seq in by_tier.items() if any(c["revoked"] for c in seq)]
    check(not ever,
          "a refusal at a door never withdraws a permission, at ANY rung",
          f"grade {cq.OFFENCE[REFUSAL_OFFENCE][1]} is not `ordinary` "
          f"(Record.ordinary counts grade 2); revoking rungs: {ever or 'none'}")
    # POSITIVE CONTROL, and it is the one that stops the line above being an
    # excuse: the same `_dispose`, the same rungs, one grade heavier.
    rec2, seen = cq.Record(), []
    for _i in range(cq.REVOKE_ON_ORDINARY):
        rec2.convictions += ("expired_status",)
        seen.append(cq._dispose(cq.TRANSIT, rec2, 2))
    check(seen[-1][1] and not seen[0][1],
          "and a grade-2 conviction DOES, on the second one",
          f"transit: 1st -> {seen[0][2][:34]}; 2nd -> {seen[-1][2][:44]}")

    # 5. THE FINE IS REAL MONEY AGAINST A REAL PURSE.
    fine = rows[k0]["detention"]["ladder"][0]["fine_subject"]
    lo, hi, days = cq.fine_for(REFUSAL_OFFENCE)
    check(lo <= fine <= hi, "the fine sits inside the offence's own band",
          f"{fine:.2f} cr in {lo:.2f}-{hi:.2f} ({days:g} day of wages)")
    check(fine < float(d["player"]["credits"]),
          "and the player can pay it, so 'paid' is not a fiction",
          f"{fine:.2f} of {d['player']['credits']:.2f} cr")

    # 6. THE HOLD MOVES WITH THE CLOCK AND NOTHING ELSE DOES. `place_row`
    #    asserts the sum; this asserts the SHAPE, because a table of 24
    #    identical numbers would pass the sum and mean the hour is inert.
    h = rows[k0]["detention"]["hold_s_h"]
    check(max(h) - min(h) > 3600.0, "the hold depends on the hour of arrest",
          f"{min(h) / 3600:.1f} h at {h.index(min(h)):02d}:00, "
          f"{max(h) / 3600:.1f} h at {h.index(max(h)):02d}:00")

    # 7. THE FORK IS A FORK. A draw that always says the same thing is a
    #    constant wearing a hash, so this asks the whole station.
    allk = checked_places()
    draws = [_detain_draw(pl.npc_id, k, 1, 0) for k in allk]
    got = sum(draws) / max(1, len(draws))
    check(0.5 * cq.DETAIN_ON_FAIL < got < 2.0 * cq.DETAIN_ON_FAIL,
          "one refusal in five detains, over the whole register",
          f"{sum(draws)} of {len(draws)} = {got:.3f} against "
          f"DETAIN_ON_FAIL {cq.DETAIN_ON_FAIL}")
    check(_detain_draw(pl.npc_id, allk[0], 1, 0)
          == _detain_draw(pl.npc_id, allk[0], 1, 0),
          "and it is deterministic in the event")

    # -- CONTROLS: each removes one input and the claim above must fail -------
    print("  CONTROLS -- each removes one input; the claim must stop holding")
    flat = {k: sec.response(k, cq.graph(), origin=sec.HQ) for k in rows}
    span = max(flat.values()) - min(flat.values())
    control(min(flat.values()) == 0.0,
            "route every turn-out from HQ, not from the nearest post",
            f"nearest becomes {min(flat.values()):.0f} s, span {span:.0f} s -- "
            f"2.6's 'to the Zocalo it is seconds' is gone")
    # THE FORK'S CONTROL: drop the event out of the key and it stops being a
    # draw. `_u(...)` on a constant argument list is one number, so 98 places
    # come back identical -- which is what a hash used as a decoration looks
    # like, and is exactly what check 7 would have read if the key were wrong.
    const = [cq._u("detain_on_refusal", pl.npc_id, "", 1, 0) < cq.DETAIN_ON_FAIL
             for _k in allk]
    control(len(set(const)) != 1,
            "take the place and the stop count out of the fork's key",
            f"{sum(const)} of {len(const)} detain -- one number, 98 times")

    # AND THE FINE'S CONTROL: rung 3 must not be able to take money, or the two
    # rungs are one rung and 'moved on' is a detention with better manners.
    control(cq.fine_for(MOVED_ON_OFFENCE)[2] not in (0.0, None),
            "ask rung 3's disposal for a fine",
            f"fine_for({MOVED_ON_OFFENCE}) = {cq.fine_for(MOVED_ON_OFFENCE)} "
            f"-- 0 days of wages, so nothing is taken")

    # ===================================================================
    # 8. PROGRESSION -- the second row of the offence rule, and the record
    # ===================================================================
    # CHECK 4 ABOVE IS WHY THESE EXIST. "A refusal at a door never withdraws a
    # permission, at ANY rung" is TRUE and was also the whole of what the
    # engine carried, so the shipped build could not demote anybody. These
    # check the OTHER row of the same rule, on the same machinery.
    sr = rows[k0]["search"]
    ever_c = sorted(t for t, seq in sr["ladder_by_tier"].items()
                    if any(c["revoked"] for c in seq))
    want_c = sorted(str(t) for t in cq.RUNGS
                    if cq.REVOCABLE.get(t) is not None)
    check(ever_c == want_c,
          "and a SEARCH does, at exactly the rungs that hold a permission",
          "revoking rungs %s; `REVOCABLE` says %s" % (ever_c, want_c))
    first = sr["ladder_by_tier"]["2"][0]
    check(bool(first["revoked"]) and int(first["tier_after"]) < 2,
          "one contraband docket takes a transit visa on the FIRST conviction",
          "rung 2 -> %d, %s" % (first["tier_after"], first["reason"]))

    # THE BRIG IS A PLACE. Its stand point must be inside its own box, or the
    # engine is putting a body beside the room it is meant to be in.
    ba = brig_address()
    blo, bhi = ba["box"]
    bst = ba["stand"]
    check(all(blo[i] - 0.01 <= bst[i] <= bhi[i] + 0.01 for i in range(3)),
          "the brig's stand point is inside the brig's own box",
          "(%.1f, %.1f, %.1f) in %s..%s" % (bst[0], bst[1], bst[2], blo, bhi))
    check(ba["cells"] == cq.BRIG_CELLS and ba["sector"] == "red",
          "and it is the register's brig, not a second one",
          "%s %s ring %d deck %d, %d cells"
          % (ba["place"], ba["sector"], ba["ring"], ba["deck"], ba["cells"]))

    # A CELL NUMBER MUST BE STABLE AND MUST NOT BE ONE NUMBER.
    cells = [brig_cell("player:%d" % i, 3) for i in range(64)]
    check(brig_cell(pl.npc_id, 3) == brig_cell(pl.npc_id, 3)
          and min(cells) >= 1 and max(cells) <= cq.BRIG_CELLS
          and len(set(cells)) > cq.BRIG_CELLS // 3,
          "a booking names the same cell every time, and not everyone's cell",
          "%d distinct cells over 64 bookings, range %d..%d"
          % (len(set(cells)), min(cells), max(cells)))

    # NOTHING PER-PERSON MAY BE BAKED AS A SCALAR THE ENGINE INDEXES.
    # This is the rule behind session 4t round 2's fix, asserted on the ARTEFACT
    # rather than on the intention -- a re-bake that re-introduced `fine` or
    # `brig_cell` at the top level would put a stranger's money back into the
    # shipped build, and the engine has no way to tell.
    d_now = d
    banned = [k for k in ("brig_cell",) if k in d_now]
    lad = d_now["places"][k0]["search"]["ladder"][0]
    check(not banned and "fine" not in lad and "fine_subject" in lad,
          "no per-person DRAW is baked where the engine could index it",
          "top-level %s; ladder row carries %s"
          % (banned or "clean",
             ", ".join(sorted(x for x in lad if "fine" in x))))
    orow = d_now["offence"][DEMOTING_OFFENCE]
    flo, fhi, _fd = cq.fine_for(DEMOTING_OFFENCE)
    check(abs(orow["fine_lo"] - flo) < 0.005
          and abs(orow["fine_hi"] - fhi) < 0.005 and fhi > flo,
          "what IS baked is the band, which is policy and not a person",
          "%s %.2f..%.2f cr = fine_for(%s)"
          % (DEMOTING_OFFENCE, orow["fine_lo"], orow["fine_hi"],
             DEMOTING_OFFENCE))
    # AND THE ENGINE'S OWN DRAW IS CHECKABLE. These four vectors are what
    # `enforcement.gd::_check_draw` compares its blake2b against before a credit
    # can move; here they are only asserted to be real answers from
    # `consequence._u` and not, say, zeros.
    dv = d_now["draw_check"]
    check(len(dv) >= 4
          and all(abs(v["u"] - cq._u(*v["parts"])) < 1e-15 for v in dv)
          and len({round(v["u"], 9) for v in dv}) == len(dv),
          "the engine can prove its hash IS consequence._u",
          "%d vector(s), u in %.4f..%.4f"
          % (len(dv), min(v["u"] for v in dv), max(v["u"] for v in dv)))
    # THE REACH, REPORTED RATHER THAN ASSUMED. See `restricted_sources`.
    rs = d_now["restricted_from"]
    here = [r for r in rs if r["in_boot"]]
    print("  ..   a restricted good is sold in %d place(s), %d in this build's "
          "rooms -- %s"
          % (len(rs), len(here),
             ", ".join("%s@%s" % (r["good"], r["where"]) for r in rs[:4])
             or "nowhere"))

    # THE LOOP AND THE RECORD, RUN RATHER THAN DESCRIBED.
    _q = lambda *_a, **_k: None                                  # noqa: E731
    g = progression_gate(out=_q)
    check(g["ok"],
          "the whole loop closes -- arrest, brig, fine, release, demotion, "
          "reload",
          "rung %d -> %d, reloaded %d, %.2f cr, cell %d%s"
          % (g["tier_before"], g["tier_after"], g["tier_reloaded"], g["fine"],
             g["cell"], "" if g["ok"] else "; failed: " + ", ".join(g["failed"])))

    print("  CONTROLS -- progression")
    g2 = progression_gate(no_restore=True, out=_q)
    control(g2["ok"], "reload the purse WITHOUT its record (CAST-05's premise)",
            "the rung comes back %d and not %d -- the demotion lives in the "
            "record and nowhere else" % (g2["tier_reloaded"], g2["tier_after"]))
    g3 = progression_gate(no_contraband=True, out=_q)
    control(g3["ok"], "the same stop with an EMPTY BAG",
            "rung %d -> %d: grade 1 is not `ordinary`, so being arrested is "
            "not by itself what costs you the rung"
            % (g3["tier_before"], g3["tier_after"]))

    print("enforcement selftest %s -- %d checked, %d failed"
          % ("PASS" if not _FAILED else "FAIL", _RAN[0], len(_FAILED)))
    return not _FAILED


# ===========================================================================
# 7b. PROGRESSION -- the rung you can LOSE, and the file that remembers
# ===========================================================================
# `docs/THE-GAME.md` section 5 is the whole of this section's brief, and its
# operative sentence is that there is NO DEATH AND NO GAME OVER: "Failure is
# *demotion plus a record*, and the record is what makes a second day different
# from the first." Section 7 binds that to a gate -- *"arrest -> brig -> fine ->
# release closes, and tier is one lower after"* -- and marks it RED.
#
# WHAT WAS ALREADY TRUE, MEASURED BEFORE ANYTHING WAS WRITTEN, because this
# project's own history says a session that does not measure first builds the
# half that already existed. `consequence.arrest` ALREADY closes the whole chain
# and ALREADY demotes: on a minted transit-visa player it returns
#
#   contraband at customs_north 13.00: respond 0.0 min, escort 13.7 min,
#   hold 17.8 h, court 1.2 min -> fine paid + status revoked, 206.63 cr,
#   transit -> no_status
#
# and `player.state()` carries the `record` that makes it survive a reload.
# So the missing halves were never the arithmetic. They were:
#
#   1. NOBODY EVER RAN IT ON A PLAYER WHO HAD SOMETHING TO LOSE. Section 4's
#      whole engine path is baked against `REFUSAL_OFFENCE = id_check_fail`,
#      which is GRADE 1, and `Record.ordinary()` counts grade 2 -- so the
#      shipped table's `ladder_by_tier` correctly says "revoking rungs: none"
#      at all six rungs, and `--selftest` check 4 asserts exactly that. The
#      engine could not demote anybody because the only offence it carried
#      cannot demote anybody. That is not a bug in the ladder; it is a table
#      with one row of a two-row rule.
#   2. THE BRIG WAS A DURATION AND NOT A PLACE. `enforcement.gd::_settle`'s
#      own comment: "Released into the corridor, because the brig is a real
#      place in the register and it is 6 km and four decks from this one".
#      A hold you are told about is a caption.
#   3. THERE WAS NO BOOKING RECORD. `spec_check --red` VRB-09: PLC-017 `brig`
#      declares ('cell_door','bunk','intercom') and 0 of them answer LOOK.
#
# AND THE RULE THIS SECTION REFUSES TO BREAK, because breaking it is how this
# repository got two crowds disagreeing about which way round a person is:
# **the booking record is DERIVED FROM THE PURSE, never stored beside it.**
# Every field a reader sees -- who, what, how much, which cell, what it cost
# you -- is recomputed from `record.convictions`, `record.notes`,
# `consequence.fine_amount` (deterministic in (offence, npc_id, seed)) and the
# card. Nothing is written twice, so nothing can drift, and "it survives a
# reload" is not a feature that had to be built: it is a consequence of the
# purse surviving, which `player.py` already guarantees.
#
# THE OFFENCE THAT COSTS YOU THE RUNG IS NOT A NEW OFFENCE. `contraband` is
# already row 7 of `consequence.OFFENCES` at grade 3, sourced to LAW-CRIME 6.5
# ("names Dust and concealed weapons"), and `REVOKE_ON_SERIOUS = 1` means ONE
# of them withdraws a conditional permission. That is precisely THE-GAME's
# section 4 load-bearing point -- *"Nightwatch and the Broker are both
# shortcuts, and taking either is how you lose tier 2"* -- arriving as the
# module's own arithmetic rather than as a new rule written here.
DEMOTING_OFFENCE = "contraband"


def restricted_goods() -> tuple:
    """What carrying it makes you a `contraband` docket rather than a citation.

    DERIVED FROM THE GOODS TABLE, NOT LISTED HERE. `economy.GOODS` classes four
    goods `contraband` -- Dust, identicard blanks, forged transit visas, weapons
    parts -- and `economy.py`'s own line 731 already says the offence against a
    customs-sealed one of them is `consequence.OFFENCE["contraband"]`. A list
    written in this file would be a second description of which goods are
    illegal, and the first thing that happens to a second description in this
    repository is that somebody edits the other one.
    """
    import economy as ec                                        # noqa: PLC0415
    return tuple(sorted({g.name for g in ec.GOODS
                         if getattr(g, "klass", "") == "contraband"}))


def offence_for(carrying) -> str:
    """Which offence a stop becomes, given what the player has in their bag.

    ONE FUNCTION, TWO CALLERS, AND THAT IS THE POINT. The Python gate and the
    engine must not each decide what a search finds; the engine is handed the
    ANSWER (`restricted` in the baked table) and applies this same rule to it.
    """
    bad = set(restricted_goods())
    return (DEMOTING_OFFENCE if any(str(c) in bad for c in (carrying or ()))
            else REFUSAL_OFFENCE)


# ---------------------------------------------------------------------------
#  THE BRIG, AS A PLACE AND NOT AS A DURATION
# ---------------------------------------------------------------------------
def brig_cell(npc_id: str, day: int, seed: str = "b5") -> int:
    """Which cell of `consequence.BRIG_CELLS` this booking goes into. INV-770.

    WHY IT IS DRAWN AND NOT ALLOCATED. A real custody desk assigns the next
    free cell, which needs an occupancy model of the brig across a station-day
    -- and `consequence.brig_check` already owns that question and already
    fails when the day's arrests overflow the sourced 24-40. What a PLAYER
    needs is weaker and must be stable: the same booking has to name the same
    cell every time it is read, including after a reload in a new process, or
    the record is not a record. So it is a draw through `consequence._u`, the
    hash every other per-person decision in that module goes through, keyed on
    (npc_id, day) -- the two things a booking is identified by.

    Overturned by: an occupancy model that can say which cells are free at an
    hour. Then this becomes `next_free(hour)` and the booking stores the
    result, and this function is deleted rather than kept beside it.
    """
    return 1 + int(cq._u("brig_cell", npc_id, day, seed) * cq.BRIG_CELLS)


def brig_address() -> dict:
    """Where the brig IS, in world metres, from the register and the schema.

    THE ENGINE HOLDS NO GEOMETRY RULE, same as the rest of this file. It is
    handed a point and a box; it does not know that a deck's floor is a radius,
    that `place_floor_radius` resolves a ring stack, or that a room's angular
    half-width is `deck.room_half_w_m`. `collision.stand_at`'s own formula is
    used for the point so a body put here stands where `collision.py` would
    have stood it.

    The box is the world AABB of the room's eight corners. It is deliberately
    the register's extents rather than a mesh bound: the claim the gate makes
    is "the player is at the address the register gives the brig", which is
    checkable with no deck built, and a mesh bound would make that claim
    unavailable in exactly the container where the deck is missing.
    """
    import math                                                 # noqa: PLC0415
    import interior as it                                       # noqa: PLC0415
    import deck as D                                            # noqa: PLC0415
    schema, profile = it.load()
    q = dr.by_key(cq.BRIG)
    r_m, ring_i, deck_i, meta = it.place_floor_radius(schema, profile, q)
    half_w = D.room_half_w_m(schema, profile, q)          # metres along the arc
    half_z = D.room_interior_half_m(schema, profile, q)   # metres along z
    a0 = math.radians(q["angle_deg"])
    da = half_w / max(r_m, 1e-6)
    r_in = float(meta.get("ceiling_r_m", r_m - 3.0))
    lo = [1e18, 1e18, q["z_m"] - half_z]
    hi = [-1e18, -1e18, q["z_m"] + half_z]
    for aa in (a0 - da, a0, a0 + da):
        for rr in (r_in, r_m):
            x, y = rr * math.cos(aa), rr * math.sin(aa)
            lo[0], lo[1] = min(lo[0], x), min(lo[1], y)
            hi[0], hi[1] = max(hi[0], x), max(hi[1], y)
    stand = [(r_m - 0.05) * math.cos(a0), (r_m - 0.05) * math.sin(a0),
             float(q["z_m"])]
    return {"place": cq.BRIG, "name": q["name"],
            "sector": q["sector"], "ring": int(ring_i), "deck": int(deck_i),
            "angle_deg": float(q["angle_deg"]), "z_m": float(q["z_m"]),
            "floor_r_m": float(r_m), "ceiling_r_m": r_in,
            "half_w_m": float(half_w), "half_z_m": float(half_z),
            "cells": int(cq.BRIG_CELLS),
            "stand": [round(v, 4) for v in stand],
            "box": [[round(v, 4) for v in lo], [round(v, 4) for v in hi]],
            "why": q.get("note", "")}


# ---------------------------------------------------------------------------
#  READING A CARD -- and this is the direction that did not exist
# ---------------------------------------------------------------------------
def read_card(subject, at: str = None, by=None) -> dict:
    """What somebody's identicard says TO A READER. VRB-08's second direction.

    `spec_check --red` VRB-08: *"no read-a-card-as-officer entry point in
    enforcement.py, player.py or enforcement.gd"*. The station could refuse
    the player and the player could not read anybody, including themselves,
    which made SHOW-PAPERS a one-way verb in a game whose top-of-ladder role
    (THE-GAME section 3, tier 3) is *"carry a badge and make arrests"*.

    IT COMPUTES NOTHING. The rows are `Player.identicard()`'s -- this project's
    one card renderer -- and the verdict is `consequence.admits`, the one
    reader. What this adds is the OFFICER'S half: the rung, the record, the
    outstanding money and what the offence WOULD be, which is the difference
    between looking at a card and being able to act on it.

    `by` is the reader. When it is a player it is checked for the rung
    `consequence.GATE_BY_FUNCTION` puts on `law_enforcement`, so a tier-0
    lurker holding somebody else's card gets `may_act=False` and the honest
    reason -- an officer's verb that anyone may use is not an officer's verb.
    """
    rec = cq.record_of(subject)
    tier = int(cq.tier_of(subject.card, rec))
    rows = [(str(f[0]), f[1]) for f in (subject.identicard() or ())
            if len(f) >= 2]
    out = {"name": subject.card.card_name, "npc_id": subject.npc_id,
           "species": subject.card.species, "role": subject.card.role,
           "fields": [[k, ("" if v is None else str(v))] for k, v in rows],
           "tier": tier, "tier_name": cq.tier_name(tier),
           "convictions": list(rec.convictions),
           "outstanding": round(float(rec.fines_outstanding), 2),
           "revoked_from": rec.revoked_from,
           "in_custody": bool(rec.in_custody),
           "carrying": list(getattr(subject, "carrying", ()) or ()),
           "would_be": offence_for(getattr(subject, "carrying", ()) or ())}
    if at:
        ok, why = cq.admits(at, tier)
        out["at"] = at
        out["admits"] = bool(ok)
        out["why"] = why
    need = cq.GATE_BY_FUNCTION.get("law_enforcement", cq.CITIZEN)
    if by is None:
        out["may_act"] = None
        out["may_act_why"] = "nobody is reading it"
    else:
        bt = int(cq.tier_of(by.card, cq.record_of(by)))
        out["reader"] = by.card.card_name
        out["reader_tier"] = bt
        out["may_act"] = bool(bt >= need)
        out["may_act_why"] = (
            "rung %d %s reads a card; `law_enforcement` needs %d %s"
            % (bt, cq.tier_name(bt), need, cq.tier_name(need)))
    return out


def card_lines(r: dict) -> list:
    """`read_card` as the six lines a reader actually sees."""
    out = ["IDENTICARD -- %s (%s %s)" % (r["name"], r["species"], r["role"])]
    for k, v in r["fields"]:
        out.append("  %-10s %s" % (k, v if v else "--"))
    out.append("  STANDING   rung %d %s%s"
               % (r["tier"], r["tier_name"],
                  (", %s WITHDRAWN" % r["revoked_from"].upper())
                  if r["revoked_from"] else ""))
    out.append("  RECORD     %s%s"
               % (", ".join(r["convictions"]) or "clean",
                  ("; %.2f cr outstanding" % r["outstanding"])
                  if r["outstanding"] else ""))
    if "admits" in r:
        out.append("  AT %-8s %s -- %s"
                   % (r["at"], "ADMIT" if r["admits"] else "REFUSE", r["why"]))
    return out


# ---------------------------------------------------------------------------
#  THE BOOKING RECORD -- derived from the purse, never stored beside it
# ---------------------------------------------------------------------------
_NOTE_RE = re.compile(r"^day\s+(\d+):\s*(.*)$")


def bookings(purse: dict, seed: str = "b5") -> list:
    """Every custody event on this card, RECONSTRUCTED from the purse.

    THE WHOLE ARGUMENT FOR THIS SHAPE IS ONE SENTENCE: a record that is written
    twice can disagree with itself, and this repository has paid for that four
    times. So nothing here is stored. `record.convictions` gives the offences
    in order; `record.notes` gives the day and the revocation in
    `consequence.arrest`'s own wording; `consequence.fine_amount` is
    DETERMINISTIC in (offence, npc_id, seed) and gives back the exact figure
    that was debited; `brig_cell` is deterministic in (npc_id, day); and the
    name, species and rung are the card. A booking is therefore a READING of
    the purse in the same way `tier_of` is a reading of the card -- and it
    survives a reload for the same reason, which is that it was never a second
    copy that had to be kept in step.

    THE ONE THING IT CANNOT RECOVER is the day of a conviction that left no
    note, because only a revocation writes one. Those rows report `day=None`
    rather than guessing, and `--progression-gate`'s reload check asserts on
    the rows that DO carry one, so a guess could not make it pass.
    """
    rec = (purse or {}).get("record") or {}
    convs = list(rec.get("convictions") or ())
    notes = [str(n) for n in (rec.get("notes") or ())]
    nid = str(purse.get("npc_id", ""))
    # NOTES ARE MATCHED BY OFFENCE, NOT BY INDEX, and the difference is not
    # cosmetic. `consequence.arrest` writes a note ONLY on a revocation and on
    # a transfer, so `notes[i]` is the i-th NOTE and not the i-th CONVICTION.
    # With one of each they line up, which is exactly the kind of coincidence
    # that passes a first test and is wrong on the second arrest. The note's
    # own wording ends "... on <offence_key>", so it names which one it is.
    used, by_off = set(), {}
    for j, n in enumerate(notes):
        m = _NOTE_RE.match(n)
        if not m:
            continue
        for off in set(convs):
            if m.group(2).rstrip().endswith(off) and j not in used:
                by_off.setdefault(off, []).append((int(m.group(1)), n))
                used.add(j)
                break
    taken = {}
    out = []
    for i, off in enumerate(convs):
        seq = by_off.get(off, [])
        k = taken.get(off, 0)
        day, note = (seq[k] if k < len(seq) else (None, ""))
        taken[off] = k + 1
        row = cq.OFFENCE.get(off)
        fine = (cq.fine_amount(off, nid, seed)
                if row and row[1] and row[1] < 4 else 0.0)
        cell = brig_cell(nid, day, seed) if day is not None else None
        out.append({
            "n": i + 1,
            "who": str(purse.get("name", "")),
            "npc_id": nid,
            "species": str(purse.get("species", "")),
            "offence": off,
            "grade": int(row[1]) if row else 0,
            "rung": int(row[2]) if row else 0,
            "source": str(row[4]) if row else "",
            "day": day,
            "cell": cell,
            "fine": round(float(fine), 2),
            "brig": cq.BRIG,
            "note": note,
            "revoked_from": str(rec.get("revoked_from", "")),
        })
    return out


def booking_lines(purse: dict, seed: str = "b5") -> list:
    """The booking record AS A PLAYER READS IT, standing in the cell.

    This is what PLC-017's `cell_door`, `bunk` and `intercom` have to be able
    to answer with. It names the person, the offence, the fine and the cell,
    which is the acceptance sentence for this item, and it names the standing
    that was taken, which is the acceptance sentence for the ladder.
    """
    rows = bookings(purse, seed)
    rec = (purse or {}).get("record") or {}
    if not rows:
        return ["BABYLON 5 SECURITY -- CUSTODY DESK",
                "  no booking on this card"]
    out = ["BABYLON 5 SECURITY -- CUSTODY DESK, %s" % cq.BRIG.upper(),
           "  BOOKED   %s (%s)" % (rows[-1]["who"], rows[-1]["npc_id"])]
    for r in rows:
        out.append("  %d. %s%s -- grade %d, escalation rung %d"
                   % (r["n"], r["offence"].upper().replace("_", " "),
                      ("" if r["day"] is None else ", day %d" % r["day"]),
                      r["grade"], r["rung"]))
        out.append("     CELL %s of %d   FINE %.2f cr"
                   % ("--" if r["cell"] is None else "%02d" % r["cell"],
                      cq.BRIG_CELLS, r["fine"]))
        if r["source"]:
            out.append("     %s" % r["source"][:72])
    out.append("  STANDING %s"
               % (("%s WITHDRAWN -- rung %d %s"
                   % (str(rec.get("revoked_from", "")).upper(),
                      int(purse.get("tier", -99)),
                      str(purse.get("tier_name", "?"))))
                  if rec.get("visa_revoked") else
                  "rung %d %s -- stands" % (int(purse.get("tier", -99)),
                                            str(purse.get("tier_name", "?")))))
    out.append("  PAID     %.2f cr; OUTSTANDING %.2f cr; %.1f h in custody"
               % (float(rec.get("fines_paid", 0.0)),
                  float(rec.get("fines_outstanding", 0.0)),
                  float(rec.get("custody_seconds", 0.0)) / 3600.0))
    return out


# ---------------------------------------------------------------------------
#  THE LOOP, END TO END
# ---------------------------------------------------------------------------
def _mint(species="human", role="", seed="g2c", credits=None):
    """A player with something to lose -- and NOT a new kind of person.

    `player.player_from` is the one minter and the rung is `tier_of`'s reading
    of what it produced; nothing here forces a tier. (human, "", "g2c") reads
    TRANSIT because `arrival.entry_class` puts VISAS=TRANSIT nD on a human
    visitor with no job aboard, which is FACTIONS 2.3's seven-day stay. If that
    ever stops being true this raises rather than quietly testing a rung-0
    lurker, which is the exact failure `--selftest` check 4 records.
    """
    pl = PL.player_from({"species": species, "role": role}, seed=seed)
    if credits is not None:
        pl.credits = float(credits)
    return pl


def _ledger_for(pl, day=3, seed="b5", path=None):
    """A ledger document holding this player's purse, and nothing invented."""
    import economy as ec                                        # noqa: PLC0415
    led = ec.Ledger.fresh(seed)
    led.day = day
    led.purses[pl.npc_id] = pl.state()
    if path:
        _write_ledger(led, path)
    return led


def _write_ledger(led, path: str) -> str:
    """`Ledger.save` and NOT a serialiser written here.

    A second writer would produce a document `economy.Ledger.load` might
    refuse -- it version-checks -- and the whole claim of this section is that
    the file the game reads is the file the record survives in.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return led.save(path)


def _purse_of(path: str, nid: str) -> dict:
    with open(path) as f:
        return (json.load(f).get("purses") or {}).get(nid) or {}


def arrest_to_release(pl, place_key: str, hour: float = 13.0, day: int = 3,
                      led=None, seed: str = "b5", out=None) -> dict:
    """ONE PASS: stopped, searched, taken to a cell, fined, released.

    The offence is `offence_for(pl.carrying)` -- what the search FINDS -- so
    the thing that costs you the rung is a decision you made in the world and
    not a parameter of this function. Everything after that is
    `consequence.arrest`, unchanged and uncopied.
    """
    tier_before = int(pl.tier)
    off = offence_for(getattr(pl, "carrying", ()) or ())
    cell = brig_cell(pl.npc_id, day, seed)
    c = cq.arrest(pl, place_key, off, hour=hour, day=day, led=led, seed=seed)
    tier_after = int(pl.tier)
    row = {"place": place_key, "offence": off, "cell": cell,
           "brig": cq.BRIG, "hour": hour, "day": day,
           "tier_before": tier_before, "tier_after": tier_after,
           "demoted": tier_after < tier_before,
           "revoked": bool(c.revoked), "fine": round(float(c.fine), 2),
           "paid": bool(c.paid), "outstanding": round(float(c.outstanding), 2),
           "custody_h": round(c.total_s / 3600.0, 2),
           "disposal": c.disposal, "reason": c.reason, "line": c.line()}
    if out:
        out("  %s" % c.line())
        out("  brig %s cell %02d of %d, %.1f h in custody"
            % (cq.BRIG, cell, cq.BRIG_CELLS, c.total_s / 3600.0))
    return row


# ===========================================================================
# 7c. THE PROGRESSION GATE -- and it has to be able to fail
# ===========================================================================
def progression_gate(seed: str = "b5", day: int = 3, place: str = None,
                     no_restore: bool = False, no_contraband: bool = False,
                     out=print) -> dict:
    """THE LOOP CLOSES AND THE DEMOTION PERSISTS -- in one run, with controls.

    Each control removes exactly one input and the verdict must move:

      --no-restore      reload the purse but throw the `record` away. This is
                        CAST-05's premise ("no memory of the player") applied
                        as a control: the tier comes back at 2 and the booking
                        is empty. If the subject still passed with the record
                        withheld, the subject was never reading it.
      --no-contraband   the same stop with an empty bag. The offence becomes
                        `id_check_fail` (grade 1), `Record.ordinary()` does not
                        count it, and NOTHING IS TAKEN -- which is the shape
                        control: it proves the demotion is the OFFENCE's doing
                        and not a side effect of being arrested at all.

    AND IT ASSERTS THE FILE, NOT THE PROCESS. The reload is a re-read of the
    JSON document from disk into a freshly minted player, so "it survives" is a
    claim about bytes rather than about an object that was never let go of.
    """
    import tempfile                                             # noqa: PLC0415
    fails, ran = [], [0]

    def ck(ok, name, detail=""):
        ran[0] += 1
        if not ok:
            fails.append(name)
        out("  %s %s%s" % ("ok  " if ok else "FAIL", name,
                           (" -- " + detail) if detail else ""))
        return ok

    place = place or (checked_places(boot_rooms()) or ["customs_north"])[0]
    tmp = tempfile.mkdtemp(prefix="progression-")
    path = os.path.join(tmp, "economy.json")

    out("PROGRESSION -- arrest, brig, fine, release, and the rung you lose")
    pl = _mint()
    bad = restricted_goods()
    if not no_contraband:
        pl.take(bad[0])
    ck(int(pl.tier) >= 2, "the player has something to lose",
       "%s: rung %d %s, %.2f cr, carrying %s"
       % (pl.card.card_name, pl.tier, pl.tier_name, pl.credits,
          ", ".join(pl.carrying) or "nothing"))
    tier_before = int(pl.tier)
    led = _ledger_for(pl, day=day, seed=seed, path=path)
    cr_before = float(pl.credits)

    # -- the officer reads the card, which is the verb that did not exist -----
    r = read_card(pl, at=place, by=pl)
    ck(bool(r["fields"]) and "at" in r,
       "a card can be READ, not only refused (VRB-08's second direction)",
       "%d field(s); at %s -> %s"
       % (len(r["fields"]), place, "ADMIT" if r["admits"] else "REFUSE"))

    # -- the arrest ----------------------------------------------------------
    row = arrest_to_release(pl, place, hour=13.0, day=day, led=led, seed=seed,
                            out=out)
    ck(row["offence"] == (REFUSAL_OFFENCE if no_contraband
                          else DEMOTING_OFFENCE),
       "the search decides the offence",
       "carrying %s -> %s (grade %d)"
       % (", ".join(pl.carrying) or "nothing", row["offence"],
          cq.OFFENCE[row["offence"]][1]))
    ck(row["cell"] >= 1 and row["cell"] <= cq.BRIG_CELLS,
       "the hold is a CELL in the brig, not a duration",
       "cell %02d of %d at `%s`" % (row["cell"], cq.BRIG_CELLS, cq.BRIG))
    ck(row["fine"] > 0.0 and row["paid"],
       "the fine is real money and it was paid",
       "%.2f cr of %.2f" % (row["fine"], cr_before))
    ck(abs((cr_before - float(pl.credits)) - row["fine"]) < 0.01,
       "and it left the purse", "%.2f -> %.2f cr" % (cr_before, pl.credits))
    ck(row["demoted"] if not no_contraband else not row["demoted"],
       "THE TIER AFTER IS LOWER THAN THE TIER BEFORE",
       "rung %d %s -> rung %d %s (%s)"
       % (row["tier_before"], cq.tier_name(row["tier_before"]),
          row["tier_after"], cq.tier_name(row["tier_after"]), row["reason"]))

    # -- QUIT: the document on disk ------------------------------------------
    led.purses[pl.npc_id] = pl.state()
    _write_ledger(led, path)
    on_disk = _purse_of(path, pl.npc_id)
    ck(bool(on_disk) and abs(float(on_disk.get("credits", -1))
                             - float(pl.credits)) < 0.01,
       "the purse on DISK carries the debit",
       "%.2f cr in %s" % (float(on_disk.get("credits", -1)),
                          os.path.basename(path)))

    # -- RELOAD: a new person built from the file, in this process's terms ---
    back = _mint(species=on_disk.get("species", "human"),
                 role=on_disk.get("role", ""))
    st = {k: v for k, v in on_disk.items() if k != "npc_id"}
    if no_restore:
        st.pop("record", None)
        st.pop("tier", None)
        st.pop("tier_name", None)
    back.restore(st)
    ck(int(back.tier) == row["tier_after"] and int(back.tier) < tier_before,
       "RELOADED, still demoted",
       "rung %d %s after reload (was %d %s before the arrest)"
       % (back.tier, back.tier_name, tier_before, cq.tier_name(tier_before)))

    # -- and the record is readable, naming them, the offence and the fine ---
    bk = bookings(on_disk, seed)
    lines = booking_lines(on_disk, seed)
    named = bool(bk) and bk[-1]["who"] and bk[-1]["offence"] \
        and bk[-1]["fine"] > 0.0
    ck(named, "a READABLE booking record names them, the offence and the fine",
       ("%s / %s / %.2f cr / cell %s" % (bk[-1]["who"], bk[-1]["offence"],
                                         bk[-1]["fine"], bk[-1]["cell"]))
       if bk else "no booking on the card")
    ck(bool(bk) and bk[-1]["fine"] == row["fine"],
       "and the fine it reports is the fine that was debited",
       "%.2f cr recomputed == %.2f cr taken"
       % (bk[-1]["fine"] if bk else -1.0, row["fine"]))
    for ln in lines:
        out("    | " + ln)

    # -- the SECOND DAY is different, which is the point of a record ---------
    r2 = read_card(back, at=place)
    ck(r2["convictions"] != r["convictions"],
       "the card reads differently to the next officer who stops them",
       "before %s, after %s" % (r["convictions"] or "clean", r2["convictions"]))

    ok = not fails
    out("PROGRESSION %s -- %d checked, %d failed  (tier %d -> %d, reload %d)"
        % ("PASS" if ok else "FAIL", ran[0], len(fails), tier_before,
           row["tier_after"], int(back.tier)))
    return {"ok": ok, "tier_before": tier_before,
            "tier_after": row["tier_after"], "tier_reloaded": int(back.tier),
            "fine": row["fine"], "cell": row["cell"], "ledger": path,
            "booking": lines, "failed": fails}


# ===========================================================================
# 8.  THE ENGINE GATE -- somebody comes, in the shipped scene
# ===========================================================================
# WHY IT LIVES HERE AND NOT IN `coldstart.py`. That file owns G1 and G3 to G7
# and this is its G8 in every respect but the file it is written in; the patch
# that adds it is in this session's report. What matters is the SHAPE, and the
# shape is copied from G4 deliberately: launch the scene `godot/project.godot`
# actually ships, with no `--glb=` and no fixture, drive a body across a real
# boundary, and read one verdict line. A static scan can tell you a caller
# exists; only running the thing tells you the caller runs.
GATE_TAG = "ARREST"

# Each control removes exactly ONE input and the subject's verdict must move.
# `--enforce-legacy` is the state of this repository before this session: the
# refusal is reported and nothing follows it.
GATE_CONTROLS = (
    (("--no-enforcement",), "the node is never built (the pre-4r tree)"),
    (("--enforce-legacy",), "it is built and reads no table"),
    (("--tier=5",), "the card admits -- there is no refusal to answer"),
    (("--enforce-no-detain",), "every stop takes rung 3 -- nobody is booked"),
    (("--enforce-no-officer",), "the verdict lands with nobody in the room"),
)


def godot_binary():
    """The same binary `coldstart.py` runs, found the same way.

    A SECOND SEARCH RULE IS A SECOND DESCRIPTION OF WHICH ENGINE THIS PROJECT
    SHIPS, and the copy below is the honest cost of the file boundary this
    session works under -- `coldstart.py` is not P2's file, so importing its
    `godot_binary` would have meant editing it to be importable. When G8 folds
    in (see the session's patch list) this function goes and the caller's is
    used, which is the whole reason the copy is annotated rather than quietly
    left. The one thing worse than an engine gate that cannot find a binary is
    two gates finding different ones.
    """
    import glob as _glob
    cand = ("/home/user/godot-build/godot-4.4-stable/bin/"
            "godot.linuxbsd.editor.double.x86_64")
    if os.path.exists(cand) and os.access(cand, os.X_OK):
        return cand
    for c in _glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*double*"):
        if os.access(c, os.X_OK):
            return c
    return None


def _run(extra, timeout=240, verbose=False, ledger_src=None):
    """One launch of the shipped scene, and TWO things about it are deliberate.

    A TIMEOUT IS A RESULT. `--no-enforcement` stops `interact.gd` building the
    node at all, which is the pre-4r tree exactly -- and in that tree nothing
    answers `--arrest-gate`, so `main.gd` goes on running the game for ever.
    That is not a hang to be worked around, it is the control's finding: a build
    with no responder cannot produce a verdict. The bound is stated so it reads
    as an answer rather than as a gate that gave up. The subject takes ~85 s.

    AND THE LEDGER IS A COPY, WHICH IT WAS NOT AND WHICH GAVE THIS GATE AN
    EXPIRY DATE. The fine is real money out of `station/generated/economy.json`,
    so five verification runs took the shipped purse from **420.50 to 372.40
    cr** -- correct behaviour, and a gate that spends its own subject's money
    stops passing after about thirty-eight runs, when the purse cannot cover
    9.62 cr and the fine becomes OUTSTANDING instead of PAID. `interact.gd`
    already honours `--ledger=<path>`, so each launch gets a fresh copy in a
    temp directory. The run is then repeatable AND the claim is stronger: the
    caller reads the copy back off disk and reports the delta, so the verdict
    rests on a FILE having changed rather than on the engine saying it did.
    """
    g = godot_binary()
    if g is None:
        return None, "no godot binary"
    import shutil                                                 # noqa: PLC0415
    import tempfile                                               # noqa: PLC0415
    tmp = tempfile.mkdtemp(prefix="arrest-gate-")
    led = os.path.join(tmp, "economy.json")
    shutil.copyfile(ledger_src or LEDGER, led)
    cmd = [g, "--headless", "--path", GODOT_DIR, "--", "--no-coldstart",
           "--arrest-gate", "--ledger=" + led] + list(extra)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, ("no verdict in %d s -- nothing in this build answered "
                      "--arrest-gate" % timeout)
    out = res.stdout + res.stderr + "\n" + _ledger_delta(ledger_src or LEDGER,
                                                         led)
    if verbose:
        print(out)
    m = re.search(r"^%s gate=(\S+)(.*)$" % GATE_TAG, out, re.M)
    if not m:
        return None, out
    d = {"gate": m.group(1)}
    for tok in m.group(2).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d, out


def _purse(path):
    try:
        with open(path) as f:
            p = json.load(f).get("purses", {})
    except Exception:                                             # noqa: BLE001
        return {}
    for k in sorted(p):
        if k.startswith("player:"):
            return p[k]
    return next(iter(p.values()), {})


def _ledger_delta(before: str, after: str) -> str:
    """What CHANGED ON DISK, as a line the verdict parser can read.

    THE CLAIM THE ENGINE MAKES IS NOT THE CLAIM THAT MATTERS. `ARREST fine 9.62
    cr paid` says the runtime debited a variable; this says the JSON document
    on disk carries one fewer credit, one more conviction, and a row in the
    Ombuds court's till. A consequence that does not survive the process is a
    mood, and only the file can settle that.
    """
    a, b = _purse(before), _purse(after)
    if not a or not b:
        return "ARREST ledger=UNREADABLE"
    ra = (a.get("record") or {}).get("convictions", [])
    rb = (b.get("record") or {}).get("convictions", [])
    # THE STORED `tier` FIELD USED TO BE PRINTED HERE AND IT DOES NOT MOVE.
    # `interact.gd::convict` writes the demotion into the RECORD, because
    # `player.py` deliberately keeps no stored rung -- so this line reported
    # `tier 2 -> 2.0` beside the word `ok`, which reads as a demotion that did
    # not happen. It is replaced by the thing that actually changes in the
    # document: `record.visa_revoked` and what it was taken from. The rung
    # itself is `_reload_line`'s, re-derived by `consequence.tier_of`.
    rec = b.get("record") or {}
    return ("ARREST ledger cr %.2f -> %.2f (-%.2f), convictions %d -> %d, "
            "revoked=%s from=%s (stored tier field %s -> %s, which is a "
            "report and not the rung)\n%s"
            % (float(a.get("credits", 0)), float(b.get("credits", 0)),
               float(a.get("credits", 0)) - float(b.get("credits", 0)),
               len(ra), len(rb), bool(rec.get("visa_revoked")),
               rec.get("revoked_from") or "-", a.get("tier"), b.get("tier"),
               _reload_line(a, b)))


def _reload_line(before: dict, after: dict) -> str:
    """QUIT AND RELOAD, DONE FOR REAL: the engine's file, reopened by Python.

    THE STORED `tier` FIELD IS NOT THE ANSWER AND MUST NOT BE READ AS ONE.
    `interact.gd::convict` writes the demotion where it belongs -- into the
    `record` (`visa_revoked`, `revoked_from`) -- and `player.py` DELIBERATELY
    does not store the rung as a fact: `Player.tier` is `consequence.tier_of`'s
    reading of the card plus the record, and its own comment says a stored tier
    "would be a second description of what the card already says". So the
    purse's `tier` key is a REPORT written at save time and the reload has to
    re-derive rather than trust it.

    That is what this does: it mints the player the purse names, restores the
    document the engine wrote, and asks `tier_of` again -- exactly what a second
    session's `player.from_state` does. The rung it returns is the one a player
    would come back to.
    """
    try:
        rb = after.get("record") or {}
        pl = PL.player_from({"species": after.get("species", "human"),
                             "role": after.get("role", "")},
                            seed=str(after.get("npc_id", "")).split(":")[-1])
        t0 = int(pl.tier)
        pl.restore({k: v for k, v in after.items() if k != "npc_id"})
        bk = bookings(after)
        # WHICH ROW IS QUOTED, AND WHY IT IS NOT `bk[-1]`. `bookings` recovers
        # the DAY of a conviction from the note `consequence.arrest` writes, and
        # only a revocation writes one -- so on three convictions the dated row
        # is the FIRST and `bk[-1]["cell"]` was `None`. The gate below asserts
        # on the cell, and a `None` it could not have been compared against is
        # exactly the shape of an assertion that cannot fail. The cell is the
        # same for every booking of one (person, day) by construction, so the
        # dated row is the whole answer rather than a sample of it.
        dated = next((r for r in bk if r["day"] is not None), None)
        q = dated or (bk[-1] if bk else None)
        return ("ARREST reload rung=%d(%s) from a clean card at rung %d(%s); "
                "revoked=%s from=%s; booking=%s"
                % (int(pl.tier), pl.tier_name, t0, cq.tier_name(t0),
                   bool(rb.get("visa_revoked")),
                   rb.get("revoked_from") or "-",
                   ("%d row(s) %s/%s/%.2f cr/cell %s"
                    % (len(bk), q["who"], q["offence"], q["fine"],
                       ("--" if q["cell"] is None else "%02d" % q["cell"])))
                   if q else "none"))
    except Exception as e:                                        # noqa: BLE001
        return "ARREST reload UNREADABLE -- %s" % e


# THE PROGRESSION RUN OF THE SAME GATE -- same scene, same launcher, two flags.
# `--tier=2` gives the card something to lose: the shipped purse is rung 0,
# where `REVOCABLE[NO_STATUS]` is None and there is nothing an Ombuds can take,
# so a demotion gate run against the shipped purse could only ever fail.
# `--arrest-contraband` puts an `economy.GOODS`-classed contraband good in the
# bag through `player.gd::take`, which is the call a played session makes.
PROG_FLAGS = ("--arrest-contraband",)
PROG_CONTROLS = (
    (("--enforce-no-contraband",),
     "same stop, EMPTY BAG -- grade 1, and nothing is taken"),
    (("--arrest-contraband", "--enforce-legacy"),
     "the node reads no table -- the build before session 4r"),
    (("--arrest-contraband", "--enforce-no-detain"),
     "every stop takes rung 3 -- nobody is booked, so nobody is demoted"),
)

# AND THE PURSE THE RUN OPENS, WHICH IS NOT `--tier=N`. The first version of
# this gate forced the rung with `--tier=2`, which writes the number onto
# `player.gd` and LEAVES THE FILE ALONE -- so the engine demoted a card the
# document had never issued, and the reload check correctly reported the
# document coming back at rung 0 with nothing taken from it. Forcing a field is
# not the same as issuing a card.
#
# So the progression run gets its own ledger, minted by `_mint` and written by
# `economy.Ledger.save`: a real transit visa, in the real document format, in a
# temp directory. The engine loads it the ordinary way (`--ledger=`), the whole
# chain runs against it, and the reload is then a claim about a file that
# described a rung-2 person before the arrest and a rung-0 one after.
def prog_ledger(day: int = 3, seed: str = "b5") -> tuple:
    import tempfile                                             # noqa: PLC0415
    pl = _mint()
    if int(pl.tier) < 2:
        raise AssertionError(
            "the minted card reads rung %d %s -- this gate needs somebody with "
            "something to lose, and `REVOCABLE` has nothing to take below rung "
            "1. `_mint`'s seed no longer produces a transit visa."
            % (pl.tier, pl.tier_name))
    path = os.path.join(tempfile.mkdtemp(prefix="prog-purse-"), "economy.json")
    _ledger_for(pl, day=day, seed=seed, path=path)
    return pl, path


_BOOKING_RE = re.compile(
    r"^ARREST booking -- (.+?), (\w+), cell (\d+) of (\d+), ([\d.]+) cr, ",
    re.M)
_RELOAD_BK_RE = re.compile(
    r"booking=(\d+) row\(s\) (.+?)/(\w+)/([\d.]+) cr/cell (\S+)")
_DEBIT_RE = re.compile(r"^ARREST ledger cr .*\(-([\d.]+)\)", re.M)


def _prog_money(out: str, d: dict) -> bool:
    """DOES THE MONEY BELONG TO THE PERSON THE RECORD NAMES? Four checks.

    THE DEFECT THIS EXISTS FOR, stated once so the next reader does not have to
    reconstruct it. Every per-person draw in this module goes through
    `consequence._u` keyed on `npc_id`. Session 4t round 1 baked two of them --
    the fine and the brig cell -- as SCALARS into a table the engine indexes for
    whoever `interact.gd::_my_purse` happened to load. The two are the same
    person only when the ledger on disk is the ledger the bake read, which is
    exactly the assumption a save file breaks. The gate printed both numbers,
    one line apart, and asserted neither.

    So this compares the three places the fine appears -- the debit the engine
    performed, the booking line the engine printed, and `bookings()`'s
    reconstruction from the saved record -- and the two places the cell appears.
    Any pair disagreeing is a person mismatch, and it fails.
    """
    good = True

    def ck(name, okv, detail=""):
        nonlocal good
        good = good and bool(okv)
        print("    %s %-46s %s" % ("ok  " if okv else "FAIL", name, detail))

    bks = _BOOKING_RE.findall(out)
    mr = _RELOAD_BK_RE.search(out)
    mdb = _DEBIT_RE.search(out)
    if not bks or not mr or not mdb:
        ck("the run printed a booking, a reload and a debit", False,
           "booking lines=%d reload=%s debit=%s"
           % (len(bks), bool(mr), bool(mdb)))
        return False
    who_e, off_e, cell_e, cells_e, fine_e = bks[-1]
    cell_e, cells_e, fine_e = int(cell_e), int(cells_e), float(fine_e)
    n_r, who_r, off_r, fine_r, cell_r = mr.groups()
    n_r, fine_r = int(n_r), float(fine_r)
    debited = float(mdb.group(1))
    detained = int(d.get("detained", 0) or 0)

    ck("the booking names the person the engine loaded", who_e == who_r,
       "engine `%s`, record `%s`" % (who_e, who_r))
    ck("the fine on the record is the fine that was drawn",
       abs(fine_e - fine_r) <= 0.011 and fine_e > 0.0,
       "engine %.2f cr, `bookings()` %.2f cr, offence %s/%s"
       % (fine_e, fine_r, off_e, off_r))
    ck("the credits the FILE lost are n x that fine", detained > 0
       and abs(debited - detained * fine_e) <= 0.02 * detained,
       "%d detention(s) x %.2f = %.2f against %.2f cr off the document"
       % (detained, fine_e, detained * fine_e, debited))
    ck("the cell on the record is the cell they were held in",
       cell_r != "--" and cell_r.isdigit() and int(cell_r) == cell_e
       and 1 <= cell_e <= cells_e,
       "engine cell %02d of %d, `bookings()` cell %s, %d row(s)"
       % (cell_e, cells_e, cell_r, n_r))
    return good


def _prog_gate(verbose=False) -> dict:
    """THE ACCEPTANCE, IN THE SHIPPED SCENE: arrested, held, fined, DEMOTED.

    One launch. The body walks across a real boundary at a place that reads a
    card, the bag is searched, the pair comes, the player is put in a numbered
    cell at the brig's own register address, the fine leaves the purse, the
    conviction is written, the rung goes DOWN, and the booking is printed.
    Then the LEDGER ON DISK is re-read and the demotion has to be in it, which
    is the reload half: the file is what a second session would open.
    """
    # A GATE THAT SKIPS WHEN ITS INPUT IS MISSING IS A GATE THAT PASSES WHEN
    # NOBODY BUILT ANYTHING, which is the shape of every green number in this
    # repository's history that turned out to describe nothing. `--gate`'s own
    # skip above is kept because it predates this session and something may
    # depend on it; this one fails and names the four commands.
    if not os.path.exists(OUT_JSON):
        print("  ARREST-PROG FAIL -- no %s. `station/generated/` is gitignored "
              "and a recycled container loses it. Run:\n"
              "    python3 station/enforcement.py --ensure --gate --progression"
              % os.path.relpath(OUT_JSON, ROOT))
        return {"ok": False}
    pl, src = prog_ledger()
    print("PROGRESSION IN THE ENGINE -- `godot --headless --path godot -- "
          "--no-coldstart --arrest-gate %s`" % " ".join(PROG_FLAGS))
    print("  the card this run opens: %s, rung %d %s, %.2f cr"
          % (pl.card.card_name, pl.tier, pl.tier_name, pl.credits))
    d, out = _run(PROG_FLAGS, verbose=verbose, ledger_src=src)
    if d is None:
        for line in out.splitlines()[-25:]:
            print("    | " + line)
        print("  ARREST-PROG FAIL -- the shipped scene printed no verdict")
        return {"ok": False}
    ok = d.get("gate") == "PASS"
    print("  %s %s" % (d["gate"], " ".join("%s=%s" % (k, v)
                                           for k, v in d.items()
                                           if k != "gate")))
    for line in out.splitlines():
        if line.startswith("ARREST ") and "gate=" not in line:
            print("    | " + line[7:])
        # AND THE TWO LINES THAT ARE NOT `ARREST` AND ARE THE POINT. The draw
        # check says this build's blake2b IS `consequence._u`; the restricted
        # count says whether a player could reach the search branch without the
        # harness flag. Both were printed by the engine and both were filtered
        # out of this summary, which left a reader taking the fine on trust.
        elif line.startswith("enforcement: draw check") \
                or line.startswith("enforcement: a restricted good"):
            print("    | " + line[13:])
    t0, t1 = -99, -99
    m = re.search(r"tier=(-?\d+)->(-?\d+)", out)
    if m:
        t0, t1 = int(m.group(1)), int(m.group(2))
        print("  %s TIER %d -> %d" % ("ok  " if t1 < t0 else "FAIL", t0, t1))
        ok = ok and t1 < t0
    # THE FILE, NOT THE RUNTIME -- and here it is the demotion and not only the
    # money. A rung that moved in a variable and not in the document is a rung
    # the next session does not inherit, which is the whole of THE-GAME's
    # "the record is what makes a second day different from the first".
    md = re.search(r"^ARREST ledger cr .*\(-([\d.]+)\), convictions (\d+) -> "
                   r"(\d+), revoked=(\w+) from=(\S+)", out, re.M)
    on_disk = (bool(md) and float(md.group(1)) > 0.0
               and int(md.group(3)) > int(md.group(2))
               and md.group(4) == "True")
    print("  %s the LEDGER ON DISK carries it: %s"
          % ("ok  " if on_disk else "FAIL",
             md.group(0)[7:] if md else "no ledger line"))
    ok = ok and on_disk
    # THE MONEY AND THE RECORD MUST BE ABOUT THE SAME PERSON, and until this
    # session nothing asked. The engine printed `fine 187.66 cr paid` and the
    # reconstruction printed `206.63 cr` on the next line of the same screen,
    # because the sidecar carried a fine drawn for `player:downbelow` and the
    # run loaded `player:g2c`. Three equalities close it, and each names a
    # different pair that could drift:
    #
    #   1. the engine's debit == the engine's own booking line     (runtime)
    #   2. the engine's booking == `bookings()`'s reconstruction   (the record)
    #   3. n * that fine == the credits the FILE actually lost     (the money)
    #
    # and the cell is checked the same way, because it is the same class of
    # per-person draw and was baked as a stranger's scalar beside the fine.
    ok = _prog_money(out, d) and ok
    # THE RELOAD, AND IT IS THE HALF THE ACCEPTANCE IS ACTUALLY ABOUT. The
    # engine wrote a JSON document and quit; this line is Python opening that
    # document as a second session would and asking `consequence.tier_of` for
    # the rung. It reports both the rung the reload gives AND the rung the same
    # card would read with the record thrown away -- which is `--no-restore` as
    # a number printed beside its subject rather than as a separate run.
    mr = re.search(r"^ARREST reload rung=(-?\d+)\([^)]*\) from a clean card at "
                   r"rung (-?\d+)\(", out, re.M)
    reloaded = bool(mr) and int(mr.group(1)) < int(mr.group(2))
    print("  %s RELOADED from the file the engine wrote: %s"
          % ("ok  " if reloaded else "FAIL",
             mr.group(0)[7:] if mr else "no reload line"))
    ok = ok and reloaded
    print("  PROGRESSION CONTROLS -- each removes one input; the demotion must "
          "stop happening")
    for flags, why in PROG_CONTROLS:
        cd, cout = _run(flags, verbose=verbose, ledger_src=src)
        cm = re.search(r"tier=(-?\d+)->(-?\d+)", cout)
        fell = bool(cm) and int(cm.group(2)) < int(cm.group(1)) \
            and int(cm.group(2)) >= 0
        good = not fell
        print("    %s %-46s %-52s -- %s"
              % ("ok  " if good else "FAIL", " ".join(flags), why,
                 ("tier %s -> %s" % (cm.group(1), cm.group(2))) if cm
                 else "no verdict"))
        ok = ok and good
    print("  ARREST-PROG %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok, "verdict": d, "tier_before": t0, "tier_after": t1}


def gate(verbose=False, legacy=False, progression=False) -> dict:
    if progression:
        return _prog_gate(verbose)
    if not os.path.exists(OUT_JSON):
        print("ARREST SKIP -- no %s. Run `python3 station/enforcement.py "
              "--bake`" % os.path.relpath(OUT_JSON, ROOT))
        return {"ok": True, "skipped": True}
    print("ARREST SOMEBODY COMES -- "
          "`godot --headless --path godot -- --no-coldstart --arrest-gate`")
    if legacy:
        d, out = _run(("--enforce-legacy",), verbose=verbose)
        print("  --enforce-legacy (the build before this session): %s"
              % (("no verdict -- " + out.splitlines()[-1][:80]) if d is None
                 else " ".join(f"{k}={v}" for k, v in d.items())))
        return {"ok": d is not None and d.get("gate") == "FAIL"}
    d, out = _run((), verbose=verbose)
    if d is None:
        print("  no ARREST verdict printed")
        for line in out.splitlines()[-25:]:
            print("    | " + line)
        print("  ARREST FAIL -- the shipped scene printed no verdict")
        return {"ok": False}
    ok = d.get("gate") == "PASS"
    print("  %s %s" % (d["gate"], " ".join(f"{k}={v}" for k, v in d.items()
                                           if k != "gate")))
    for line in out.splitlines():
        if line.startswith("ARREST ") and "gate=" not in line:
            print("    | " + line[7:])
    # THE FILE, NOT THE RUNTIME. `ok` already required the engine to report a
    # debit; this requires the document to carry it, and a disagreement between
    # the two is the whole reason `_ledger_delta` exists.
    m = re.search(r"^ARREST ledger cr .*\(-([\d.]+)\), convictions (\d+) -> "
                  r"(\d+)", out, re.M)
    on_disk = bool(m) and float(m.group(1)) > 0.0 \
        and int(m.group(3)) > int(m.group(2))
    print("  %s the LEDGER ON DISK carries it: %s"
          % ("ok  " if on_disk else "FAIL",
             m.group(0)[7:] if m else "no ledger line"))
    ok = ok and on_disk
    print("  ARREST CONTROLS -- each changes one input and must move the verdict")
    for flags, why in GATE_CONTROLS:
        cd, cout = _run(flags, verbose=verbose)
        good = cd is None or cd.get("gate") == "FAIL"
        said = ((cout.splitlines() or ["no verdict"])[-1][:64]
                if cd is None else
                " ".join(f"{k}={v}" for k, v in cd.items()
                         if k in ("gate", "refused", "responded", "arrived",
                                  "detained", "moved_on", "cr")))
        print("    %s %-22s %-44s -- %s"
              % ("ok  " if good else "FAIL", " ".join(flags), why, said))
        ok = ok and good
    print("  ARREST %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok, "verdict": d}


# ===========================================================================
# 8b. THE FOUR THINGS THIS GATE NEEDS ON DISK, AND HOW TO GET THEM
# ===========================================================================
# `station/generated/` is gitignored, the container recycles, and a verifier who
# is handed a gate command must be able to run it. Each step below is named with
# its OUTPUT and its cost, checked by whether the output exists rather than by
# an exit code -- `tools/bootstrap.py`'s rule, and its own first run is why:
# a step exited 0, wrote its real output, and was reported as FAILED because
# the predicate named a different file.
ENSURE = (
    # THE PREDICATE IS `boot.decks()` AND NOT A GLOB, AND THE FIRST RUN OF THIS
    # FUNCTION IS WHY. It globbed `*_col.obj`, an interrupted `arrival.py
    # --build` had written the .obj pair and not the .glb, and `--ensure`
    # reported `present  the arrival cluster` on a half-built deck -- then
    # `boot.py` failed with "no built deck", which is the same sentence a
    # missing deck gives and sent the reader to the wrong place. `boot.decks()`
    # is the consumer's OWN test (a mesh AND a collision shell), so the thing
    # that decides whether to build is the thing that decides whether it worked.
    ("the arrival cluster",
     lambda: bool(__import__("boot").decks()),
     ["python3", "station/arrival.py", "--build"], "~90 s"),
    ("the player's purse",
     lambda: os.path.exists(LEDGER),
     ["python3", "station/dockwork.py", "--loop", "--days", "14", "--role",
      "lurker", "--seed", "downbelow", "--save",
      "station/generated/economy.json"], "~9 s"),
    ("the boot manifest",
     lambda: os.path.exists(BOOT_JSON),
     ["python3", "station/boot.py"], "~28 s"),
    # AND THE SAME DEFECT ONE STEP OVER, found the same way. This predicate was
    # `os.path.exists(OUT_JSON)`, and a `--bake` run against an EMPTY boot
    # manifest writes a perfectly well-formed table with `places: {}` -- which
    # exists, so `--ensure` reported it present and the gate then failed with a
    # verdict about the arrest chain. A table with no places is not a table.
    # AND THE SAME DEFECT A THIRD TIME, which is why it is now a function. A
    # sidecar baked before session 4t round 2 has `places`, so it passed -- and
    # it has no `draw_check` and no `fine_lo`, so `enforcement.gd` refuses to
    # price anything and the gate fails talking about an unpriced fine. The
    # predicate asks what the CONSUMER needs, key by key.
    ("the consequence table",
     lambda: _table_is_current(),
     ["python3", "station/enforcement.py", "--bake"], "~63 s"),
)


def _table_is_current(path: str = None) -> bool:
    """Does the sidecar on disk carry everything `enforcement.gd` reads?

    A table with no places is not a table (see above), and a table with no
    `draw_check` is a table the engine cannot price a fine from -- it will
    refuse, loudly and correctly, and the failure will read as a defect in the
    arrest chain rather than as a stale artefact.
    """
    path = path or OUT_JSON
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception:                                             # noqa: BLE001
        return False
    if not (d.get("places") or {}):
        return False
    if not (d.get("draw_check") or []):
        return False
    if int(d.get("brig_cells", 0)) <= 0:
        return False
    off = d.get("offence") or {}
    row = off.get(DEMOTING_OFFENCE) or {}
    return float(row.get("fine_hi", 0.0)) > 0.0


def ensure(force=False, out=print) -> bool:
    ok = True
    for name, have, cmd, cost in ENSURE:
        if have() and not force:
            out("  present  %s" % name)
            continue
        out("  BUILDING %s (%s) -- %s" % (name, cost, " ".join(cmd)))
        subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if not have():
            # STOP. A later step's failure on a missing input reads as a defect
            # in the later step, which is how the half-built deck above got
            # reported as "boot: no built deck" instead of "arrival.py died".
            out("  FAILED   %s -- its output is still missing. Run it by hand "
                "and read what it says." % name)
            return False
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="every place on the station, not just the boot deck")
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--legacy", action="store_true",
                    help="with --gate: run the pre-4r build and show it FAIL")
    ap.add_argument("--progression", action="store_true",
                    help="with --gate: run the DEMOTION scenario in the "
                         "shipped scene, with its own controls")
    ap.add_argument("--progression-gate", action="store_true",
                    help="arrest -> brig -> fine -> release -> DEMOTED, and "
                         "the record survives a reload")
    ap.add_argument("--no-restore", action="store_true",
                    help="control: reload the purse without its record")
    ap.add_argument("--no-contraband", action="store_true",
                    help="control: the same stop with an empty bag")
    ap.add_argument("--card", metavar="SEED", nargs="?", const="g2c",
                    help="read a card as an officer would (VRB-08)")
    ap.add_argument("--ensure", action="store_true",
                    help="build the four artefacts this gate reads, if the "
                         "container lost them")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.ensure:
        print("enforcement --ensure -- station/generated/ is gitignored")
        if not ensure():
            return 1
    if not any((a.report, a.bake, a.selftest, a.gate, a.progression_gate,
                a.card)):
        a.report = True
    rc = 0
    if a.card:
        pl = _mint(seed=a.card)
        for ln in card_lines(read_card(pl, at="brig", by=pl)):
            print(ln)
    if a.progression_gate:
        g = progression_gate(no_restore=a.no_restore,
                             no_contraband=a.no_contraband)
        # A CONTROL PASSES BY FAILING. Run bare it must pass; run with either
        # flag it must NOT, or the flag removed an input the subject was not
        # reading and the subject's claim was about something else.
        want_pass = not (a.no_restore or a.no_contraband)
        if bool(g["ok"]) != want_pass:
            rc = 1
        if not want_pass:
            print("CONTROL %s -- with %s the loop's claim %s"
                  % ("FIRED" if not g["ok"] else "INERT",
                     "--no-restore" if a.no_restore else "--no-contraband",
                     "stops holding" if not g["ok"] else "STILL HOLDS, which "
                     "means the subject was not reading that input"))
    if a.report:
        report(all_places=a.all)
    if a.bake:
        p = emit()
        with open(p) as f:
            n = len(json.load(f)["places"])
        print("enforcement: %s -- %d place(s)" % (os.path.relpath(p, ROOT), n))
    if a.selftest and not selftest():
        rc = 1
    if a.gate and not gate(a.verbose, a.legacy, a.progression).get("ok"):
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
