"""The law-and-order layer: where the force is, when, and how long it takes.

`docs/gazetteer/LAW-CRIME-DOWNBELOW.md` is 1,181 lines of sourced material --
the force's size and shape, what an officer wears and carries, where the posts
are, patrol patterns, response times, the escalation ladder, the brig, law, the
black market, Downbelow -- and **until this module existed nothing in the
project read it**. `grep -rl LAW-CRIME-DOWNBELOW station/ tools/` returned
nothing while the other three gazetteer files had 23 readers between them. The
owner's scope brief names "customs and immigration, law enforcement, crime, the
black market, Downbelow's underclass" in the same breath as the NPCs; two of
those five were written down and wired to nothing.

WHAT THIS MODULE IS FOR, AND WHAT IT IS NOT
-------------------------------------------
It is the answer to "is there a uniform in this corridor right now, and if I
scream, how long until one arrives". It is deliberately NOT a second copy of
the gazetteer: every number the gazetteer asserts about geometry or timing is
**recomputed here from the built station** and the difference is reported. That
is the whole reason it is worth writing rather than reading.

Three of those recomputations came out different, and they are the interesting
part of this file:

  1. THE GAZETTEER'S RING RADIUS IS STALE. Section 2.5 quotes "Grey ring 1's
     circumference is 2,527 m" and section 2.6 "Grey ring 1 (r = 402.2 m)".
     The built station's outermost Grey deck is at **r 471.2 m, circumference
     2,961 m** -- 17% larger. The gazetteer's figure was taken from
     `interior.sector_report` before the addresses became hull-correct
     (`interior.rings_fitting_at`, session 3z). Nothing was wrong when it was
     written; the station moved underneath it. `beat_report()` prints both.

  2. THE GAZETTEER'S WALK SPEED IS FLAT AND THIS PROJECT'S IS NOT. Section 2.5
     computes a beat at "1.3 m/s". `navigation.walk_speed(g)` is a Froude-
     number gait model -- v scales as sqrt(g*L) -- so the same officer walks
     **1.94 m/s** in Grey's 1.69 g and 1.12 m/s in Yellow's 0.56 g. The heavy
     outer ring is walked FASTER, not slower, and the penalty the gazetteer
     correctly identifies is in the officer's WEIGHT (127 kgf for a 75 kg
     officer at 1.69 g, against the 108 kgf the gazetteer quotes), not in the
     time. Both effects are real and they point opposite ways.

  3. THE GAZETTEER CONTRADICTS ITSELF ON PATROL COUNT, by one line. Section 2.5
     says "Roving patrols ~35 pairs ... The remaining 90". Ninety officers is
     forty-five pairs. `roving_pairs()` derives the count instead of choosing
     between them and `report()` prints the discrepancy rather than quietly
     picking one. Logged as C-011.

WHAT IS DERIVED AND WHAT IS DECLARED
------------------------------------
Derived, from modules that already existed:

  * how many officers are on duty at an hour  -- `schedule.role_on_duty`,
    which already spread 500 security over three shifts and which INV-005
    warns must not be re-litigated (resolving sleep before work once put the
    entire night watch to bed and showed zero security at 02:00)
  * every beat length, gravity and walk speed -- `navigation.cell_plan`,
    `navigation.walk_speed`, `interior.gravity_at`
  * every response time                       -- `navigation.build_graph` and
    `NavGraph.path`, i.e. the SAME routed graph a resident commutes on, with
    lifts modelled as vehicles rather than staircases
  * who an officer is                         -- `resident.resident`, so a
    patrolman has a name, a species, quarters, an age and an identicard

Declared (authority 5, INV-240): how the ~60 officers on fixed posts are split
between the posts. Everything about that split is constrained rather than free
-- see `POSTS`.
"""

import functools
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_STATION = os.path.dirname(_HERE)
if _STATION not in sys.path:                                 # pragma: no cover
    sys.path.insert(0, _STATION)

import interior as it                                          # noqa: E402
import directory as dr                                         # noqa: E402
from npc import navigation as nav                              # noqa: E402
from npc import resident as res                                # noqa: E402
from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(_STATION), "docs", "gazetteer",
                         "LAW-CRIME-DOWNBELOW.md")

# ===========================================================================
# 1.  The force
# ===========================================================================

# NOT RESTATED HERE. `schedule.ROLE_WEIGHTS` carries the 500 that FACTIONS.md
# section 2.2 apportions, and CLAUDE.md's first hard rule is that a canon or
# declared number lives in exactly one place. This module asks `schedule` and
# checks the answer against the gazetteer rather than carrying a copy that can
# drift.
ROLE_KEY = "security"

# FACTIONS.md section 5.2: 150-200 of the 500 wear the Nightwatch armband at
# the S3E01-E08 datum, "one in three ... the other two do not, it is the same
# uniform". The midpoint of the stated band, as a fraction. Used ONLY to decide
# a per-officer boolean -- FACTIONS.md is explicit that the armband is a flag
# on the security uniform and not a separate NPC type.
NIGHTWATCH_SHARE = 175.0 / 500.0

# LAW-CRIME-DOWNBELOW.md section 2.5, and it is the rule that shapes every
# other number in this file: "Patrol unit: 2 officers, always -- FACTIONS.md
# section 12 makes the two-officer pair carry the Nightwatch split, one armband
# and one bare sleeve. A lone officer destroys that."
PATROL_UNIT = 2

# The gazetteer's own figures, kept so this module can CHECK them rather than
# repeat them. Nothing here is used to compute anything.
GAZETTEER_CLAIMS = {
    "on_duty": 150,                # section 2.2
    "fixed_post_officers": 60,     # section 2.5
    "roving_pairs": 35,            # section 2.5 -- see C-011
    "roving_officers": 90,         # section 2.5 -- and 90/2 is 45, not 35
    "grey_ring1_circumference_m": 2527.0,   # section 2.5
    "grey_ring1_radius_m": 402.2,           # section 2.6
    "grey_ring1_weight_kgf_at_75kg": 108.0,  # section 2.5
    "beat_walk_speed_m_s": 1.3,             # section 2.5
    "vehicle_transit_s": 300.0,             # section 2.6, door to door
    "far_sector_response_min": (12.0, 20.0),  # section 2.6, the headline
}


def force_total() -> int:
    """The whole force, from `schedule`'s own apportionment."""
    return int(sched.ROLE_WEIGHTS["human"][ROLE_KEY])


def on_duty(hour: float) -> int:
    """Officers on duty at station hour `hour`.

    Delegates to `schedule.role_on_duty`, which already rotates security over
    three shifts. INV-005 records that this was once broken in the worst
    possible way -- resolving sleep before work put the entire night watch to
    bed and reported ZERO security on duty at 02:00 -- so this function exists
    to have exactly one caller-visible answer and no second implementation.
    """
    return int(sched.role_on_duty(ROLE_KEY, hour))


# ===========================================================================
# 2.  The fixed posts
# ===========================================================================

# WHERE THE FORCE PHYSICALLY IS. Every row's `key` is a `directory.PLACES` key,
# so a post is a place on the station rather than a name in a document, and a
# post that loses its register row fails `_selftest` instead of silently
# vanishing. Ordered exactly as LAW-CRIME-DOWNBELOW.md section 2.4 orders them:
# by how certain the placement is.
#
# `pairs` IS THE DECLARED PART AND IT IS CONSTRAINED THREE WAYS, which is what
# stops it being ten free numbers:
#
#   1. A post is manned by PATROL_UNIT officers or a multiple of it. Section
#      2.5's "2 officers, always" is not a patrol rule, it is a force rule --
#      it exists so the Nightwatch split is visible in any glance, and a post
#      of one destroys that exactly as a lone patrol does.
#   2. A post is manned CONTINUOUSLY, so its cost is per shift and it is
#      charged against the on-duty figure, not against the 500.
#   3. The total is checked against section 2.5's "~60 of the 150 on duty".
#      It comes to 56, which is the sum of the reasons below rather than a
#      number tuned to hit 60 -- `post_report()` prints both.
#
# INV-240 records the split and what would overturn it.
POSTS = (
    # key, pairs, confidence, authority, why this many
    ("security_central", 4, "STATED", 3,
     "Force HQ and the one post the sources call 24 h. Two pairs on the "
     "watch floor, one on the duty desk, one turning out"),
    ("security_posts", 6, "STATED/PROPOSED", 4,
     "The station houses. Authority 4 names them plural and distributed, "
     "'one per pressurised sector' -- five sectors, one pair each -- plus "
     "one pair on the Grey boundary, whose access restriction is stated at "
     "authority 4 and which has no register row of its own"),
    ("customs_north", 3, "STATED", 1,
     "Permanent and doubled. Contraband, identicards, visas -- section 2.7 "
     "makes the identicard check the routine power and the customs hall the "
     "place it is routinely used"),
    ("customs_south", 3, "STATED", 1, "The southern half of the same pair"),
    ("zocalo", 4, "PROPOSED (D-03)", 5,
     "'The most-policed civilian space on the station.' This post is what "
     "produces the effect section 2.5 asks for: four officers in one glance"),
    ("council_chamber", 2, "PROPOSED (D-03)", 5,
     "Access control to the ambassadorial zone. Diplomatic immunity makes "
     "this a checkpoint rather than a patrol"),
    ("bay_elevators", 2, "PROPOSED (D-03)", 5,
     "Where craft, crew and cargo enter the pressurised volume"),
    ("docking_bays", 2, "PROPOSED (D-03)", 5,
     "The other half of the same boundary, at the bay face"),
    ("brig", 2, "DERIVED", 5,
     "A detention facility holding prisoners has a watch on it. Section 3 "
     "sources almost nothing about the brig except that it holds people"),
)

# LAW-CRIME-DOWNBELOW.md section 2.4, last row, and it is a positive design
# decision rather than an omission: "Downbelow -- NO PERMANENT POST." Named
# here so that a future session adding posts by intuition has to delete a line
# with a reason on it rather than merely fail to think of one.
NO_POST = ("downbelow", "downbelow_arch", "black_market", "thieves_guild",
           "happy_daze", "welded_shut")


def posted_officers() -> int:
    """Officers standing on fixed posts, at any moment."""
    return sum(p[1] for p in POSTS) * PATROL_UNIT


def roving_pairs(hour: float) -> int:
    """Two-officer patrols free to move, at station hour `hour`.

    DERIVED, not chosen, and the derivation is why: the gazetteer says both
    "~35 pairs" and "the remaining 90" one row apart, and ninety officers is
    forty-five pairs. Picking either would be picking the convenient reading
    of a conflict, which CLAUDE.md's third hard rule forbids. This computes it
    and `report()` prints the gap. See C-011.
    """
    return max(0, (on_duty(hour) - posted_officers()) // PATROL_UNIT)


# ===========================================================================
# 3.  The beat -- recomputed against the built station
# ===========================================================================

# MEMOISED, AND THE COST OF NOT DOING IT WAS MEASURED. `navigation.cell_plan`
# walks every sector, ring and deck to build 2,330 cells, and `presence_at` is
# called once per room by `populace.populate` -- so a whole-station sweep was
# rebuilding the entire cell plan 128 times to learn which deck is outermost.
# Keyed on the schema's identity because `interior.load()` returns a singleton
# and a dict is not hashable.
_OUTERMOST = {}


def outermost_decks(schema=None, profile=None) -> dict:
    """The outermost pressurised deck of each sector, as `cell_plan` built it.

    THE OUTERMOST RING IS WHERE THE BEAT IS, because it is where the people
    are: LAW-CRIME-DOWNBELOW.md section 2.2 counts 753 of the station's 2,330
    streaming cells in it. It is also the heaviest place on the station, which
    is the whole of why foot patrol there is a real cost.
    """
    if schema is None:
        schema, profile = it.load()
    key = (id(schema), id(profile))
    hit = _OUTERMOST.get(key)
    if hit is not None:
        return hit
    decks, _cells = nav.cell_plan(schema, profile)
    out = {}
    for d in decks:
        s = d["sector"]
        if s not in out or d["floor_r_m"] > out[s]["floor_r_m"]:
            out[s] = d
    _OUTERMOST[key] = out
    return out


def beat(sector: str, schema=None, profile=None) -> dict:
    """One sector's out-and-back beat on its outermost ring.

    Section 2.5 defines the beat as "one outermost-ring deck arc, out and
    back", so the period is a whole circumference at the local walk speed --
    a half-circuit each way. Everything here is measured off the built deck
    and the project's own gait model; nothing is quoted.
    """
    d = outermost_decks(schema, profile)[sector]
    circ = 2.0 * math.pi * d["floor_r_m"]
    v = nav.walk_speed(d["floor_g"])
    return {
        "sector": sector,
        "ring_index": d["ring_index"],
        "floor_r_m": d["floor_r_m"],
        "g": d["floor_g"],
        "circumference_m": circ,
        "walk_speed_m_s": v,
        "half_circuit_s": circ / 2.0 / v,
        # Out and back: a pair passes any given point twice per circuit, so
        # the interval between passes at a fixed point is HALF the period.
        "period_s": circ / v,
        "cells": d["cells"],
        # A 75 kg officer, in kgf. Section 2.5 calls foot patrol in the heavy
        # outer rings "genuinely punishing" and this is the number behind it.
        "officer_weight_kgf": 75.0 * d["floor_g"],
    }


def beat_interval_s(sector: str, pairs: int, schema=None, profile=None):
    """How long between one pair passing a fixed point, with `pairs` on beat.

    The number section 2.5 tabulates as "beat frequency, by place" and does
    not derive. With `pairs` patrols evenly spread over one out-and-back
    circuit, a fixed point sees one every `period / (2 * pairs)` seconds --
    the 2 because the beat is out AND back.
    """
    if pairs <= 0:
        return float("inf")
    return beat(sector, schema, profile)["period_s"] / (2.0 * pairs)


# ===========================================================================
# 4.  Response -- on the graph a resident actually walks
# ===========================================================================

HQ = "security_central"


def response(place_key: str, G=None, schema=None, profile=None,
             origin: str = HQ):
    """Time for the nearest turn-out to reach `place_key`, in seconds.

    THE GAZETTEER COMPUTED THIS BY HAND AND THIS RECOMPUTES IT. Section 2.6
    assembled 300 s door to door out of `physics/core_shuttle.py` legs -- 43 s
    radial, 100 s axial, 158 s radial -- and then added "call-out, waiting for
    a car, and the walk at the far end" in prose to reach 12-20 minutes. That
    was the best available at the time; there was no routed graph. There is
    now, and it prices the walk at both ends, the lift waits, the dwell and
    the transfers, in one number, on the same graph a resident commutes on.

    Returns None when the place has no node, which is a defect in
    `register_nodes` rather than a fact about policing, so callers should not
    silently treat it as "far".
    """
    if G is None:
        G = nav.build_graph(schema, profile)
    a, b = f"place:{origin}", f"place:{place_key}"
    if a not in G.nodes or b not in G.nodes:
        return None
    if a == b:
        return 0.0
    r = G.path(a, b)
    return None if r is None else r["time_s"]


def response_from_nearest_post(place_key: str, G=None, schema=None,
                               profile=None):
    """Time from whichever fixed post is closest -- which is the real answer.

    Section 2.6's headline is a CONTRAST, not a number: "response to the outer
    ring of a distant sector is 12-20 minutes. To the Zocalo, from the
    standing post already there, it is seconds." Routing everything from HQ
    gets the first half right and the second half badly wrong, because the
    Zocalo has four pairs standing in it. This takes the minimum over the
    posts, so a post's own place answers 0.
    """
    if G is None:
        G = nav.build_graph(schema, profile)
    best, who = None, None
    for key, _pairs, _c, _a, _why in POSTS:
        t = response(place_key, G, origin=key)
        if t is not None and (best is None or t < best):
            best, who = t, key
    return {"seconds": best, "from": who}


# ===========================================================================
# 5.  Who is standing there
# ===========================================================================

def wears_armband(npc_id: str, species: str = "human") -> bool:
    """The per-NPC boolean FACTIONS.md section 5.3 asks for.

    DELEGATED, NOT DECIDED HERE, and that is hard rule 4 applied to a boolean.
    The first version of this function rolled its own
    `_u("security/nightwatch", id) < NIGHTWATCH_SHARE` and passed every test
    in this file -- while `costume.py` was independently rolling
    `_u(seed, "nw") < NIGHTWATCH_SECURITY_RATE` to decide whether to hang the
    armband decal on the sleeve. Two descriptions of one fact, agreeing only
    by luck, and the RENDER is driven by the other one. A player would have
    seen the band on a different officer from the one this module called
    banded.

    `costume.costume_for` is the authority because it is what reaches a frame.
    It also gets the era right for free -- `era_active("nightwatch_visible")`
    means no armband exists before *The Fall of Night*, which a bare hash
    could not know.
    """
    from npc import costume as _cos                             # noqa: PLC0415
    return bool(_cos.costume_for(species, npc_id).nightwatch)


def is_officer(r) -> bool:
    """Is this resident one of the 500?"""
    return getattr(r, "role", None) == ROLE_KEY


# ONE OFFICER IN 270 IDS, and that ratio is the whole reason this is a search
# rather than a roster. `schedule.role_for` draws a role from the id by hash
# against FACTIONS.md's apportionment, and security is 500 of the 155,000
# humans -- 0.32%. `resident.roster` cannot supply them either: it casts a
# PLACE's regulars and a place has a capacity, so `roster(security_central,
# ..., 300)` returns four officers however many are asked for.
#
# `role_for` is the cheap half of `resident()` and filtering on it first is
# what makes this affordable: 120 officers out of 32,406 candidate ids in
# 0.06 s, against building 32,406 residents. Measured, not assumed.
OFFICER_SEARCH_CAP = 200_000


@functools.lru_cache(maxsize=64)
def _officer_pool_cached(hour_bucket: int, n: int, seed: str) -> tuple:
    out, i = [], 0
    while len(out) < n and i < OFFICER_SEARCH_CAP:
        npc_id = res.pool_id(HQ, "human", i, f"{seed}:force")
        i += 1
        if sched.role_for(npc_id, "human").key != ROLE_KEY:
            continue
        out.append(res.resident(npc_id, "human"))
    return tuple(out)


def officer_pool(hour: float, n: int, seed: str = "b5") -> list:
    """`n` real officers, as residents, drawn from the force's own places.

    WHY THIS EXISTS, AND WHY A POST IS NOT AN AFFILIATION. `resident.roster`
    casts a place's REGULARS, resolved from each resident's `job`, and it does
    that job well: ask it for twelve people at `security_central` and seven
    come back with `role == "security"`; at `customs_north`, six come back
    customs officers. **Ask it at the Zocalo and none do** -- merchants,
    financiers, visitors and service staff -- because an officer standing a
    post in the Zocalo has `job == "patrol"`, not `job == "zocalo"`, and no
    amount of rostering will put them there.

    That is the whole gap this module closes. The gazetteer calls the Zocalo
    "the most-policed civilian space on the station" and the crowd system
    could not put a single officer in it.
    """
    # Cached, and NOT on the hour: the force is a cast, not a clock. Who is
    # ON DUTY at an hour is `on_duty()`; who the five hundred ARE does not
    # change between 02:00 and 18:00. The hour is taken so callers can pass it
    # without thinking and is deliberately not part of the key.
    del hour
    return list(_officer_pool_cached(0, int(n), seed))


def patrol(place_key: str, index: int = 0, seed: str = "b5") -> dict:
    """One two-officer patrol, as people rather than as a count.

    THE PAIR IS THE UNIT AND THE SPLIT IS THE POINT. FACTIONS.md section 5.3
    calls one band and one bare sleeve in the same pair "the single best piece
    of environmental storytelling on the station", so this does not roll the
    boolean twice and hope: it rolls each officer's own flag, and if they came
    out the same it swaps the SECOND officer for the next id that differs.
    That is a declared bias in a 1-in-3 process -- INV-240 records it -- and it
    is taken deliberately, because a pair that reads as uniform teaches the
    player the opposite of what is true.
    """
    pool = officer_pool(18.0, (index + 1) * PATROL_UNIT + 24, seed)
    if len(pool) < PATROL_UNIT:
        raise RuntimeError("the force has fewer than two officers in it")
    band = [r for r in pool if wears_armband(r.npc_id)]
    bare = [r for r in pool if not wears_armband(r.npc_id)]
    if not band or not bare:
        # Cannot make the split. The pair comes back uniform and the caller's
        # gate sees it, rather than being quietly repaired into a lie.
        picked = (pool[index * PATROL_UNIT:(index + 1) * PATROL_UNIT]
                  or pool[:PATROL_UNIT])
    else:
        picked = [band[index % len(band)], bare[index % len(bare)]]
    officers = [{"id": r.npc_id, "resident": r,
                 "armband": wears_armband(r.npc_id)} for r in picked]
    return {"place": place_key, "index": index, "officers": tuple(officers),
            "armbands": sum(1 for o in officers if o["armband"])}


def presence_at(place_key: str, hour: float, schema=None, profile=None,
                G=None) -> dict:
    """Officers a player can see in one place at one hour.

    This is the function the corridor populace would consume, and its whole
    job is to produce the effect section 2.5 names as the thing the player
    must feel: "twenty minutes of walking in the outer ring with no uniform in
    sight, then four officers in one glance in the Zocalo."

    A place gets its fixed post, plus its share of the sector's roving pairs
    weighted by how much of the sector's outermost ring it occupies. Downbelow
    gets zero and says so.
    """
    q = dr.by_key(place_key)
    fixed = 0
    for key, pairs, _c, _a, _why in POSTS:
        if key == place_key:
            fixed = pairs * PATROL_UNIT
    if place_key in NO_POST:
        return {"place": place_key, "hour": hour, "fixed": 0, "roving": 0.0,
                "officers": 0.0, "policed": False,
                "why": "LAW-CRIME-DOWNBELOW.md 2.4: no permanent post, by "
                       "design"}
    sector = q.get("sector")
    b = beat(sector, schema, profile) if sector in outermost_decks(
        schema, profile) else None
    roving = 0.0
    if b is not None:
        # The sector's share of the station's roving pairs, by cell count,
        # then this place's share of the sector's ring by its own footprint.
        alld = outermost_decks(schema, profile)
        tot_cells = sum(d["cells"] for d in alld.values())
        pairs_here = roving_pairs(hour) * (b["cells"] / max(1, tot_cells))
        arc_share = float(q["footprint"][0]) / 360.0
        roving = pairs_here * arc_share * PATROL_UNIT
    return {"place": place_key, "hour": hour, "fixed": fixed,
            "roving": roving, "officers": fixed + roving, "policed": True,
            "why": ""}


# ===========================================================================
# 6.  Reports
# ===========================================================================

def post_report(out=print):
    """The fixed posts, and the check against the gazetteer's ~60."""
    out("FIXED POSTS -- LAW-CRIME-DOWNBELOW.md 2.4, at register addresses")
    total = 0
    for key, pairs, conf, auth, why in POSTS:
        q = dr.by_key(key)
        total += pairs * PATROL_UNIT
        out(f"  {key:18s} {pairs} pair(s) = {pairs * PATROL_UNIT:2d}  "
            f"{q['sector']:6s} ring {q.get('ring')}  {conf:16s} auth {auth}")
    g = GAZETTEER_CLAIMS["fixed_post_officers"]
    out(f"  {'':18s} {total} officers on post, against the gazetteer's ~{g} "
        f"({total / g:.2f}x) -- the sum of the reasons above, not a fit")
    out(f"  {len(NO_POST)} places have NO post by design: "
        f"{', '.join(NO_POST)}")
    return total


def beat_report(schema=None, profile=None, out=print):
    """Every sector's beat, and the three places the gazetteer went stale."""
    if schema is None:
        schema, profile = it.load()
    out("BEATS -- recomputed off the built decks, not quoted")
    out(f"  {'sector':8s} {'r_m':>7s} {'g':>5s} {'circ_m':>8s} "
        f"{'v_m_s':>6s} {'half_min':>9s} {'kgf@75kg':>9s}")
    rows = {}
    for sector, b in sorted(beat_all(schema, profile).items()):
        rows[sector] = b
        out(f"  {sector:8s} {b['floor_r_m']:7.1f} {b['g']:5.2f} "
            f"{b['circumference_m']:8.1f} {b['walk_speed_m_s']:6.2f} "
            f"{b['half_circuit_s'] / 60.0:9.1f} "
            f"{b['officer_weight_kgf']:9.1f}")
    g = rows.get("grey")
    if g:
        c = GAZETTEER_CLAIMS
        out(f"  grey against the gazetteer: circumference "
            f"{g['circumference_m']:.0f} m vs {c['grey_ring1_circumference_m']:.0f} m "
            f"({g['circumference_m'] / c['grey_ring1_circumference_m']:.2f}x), "
            f"radius {g['floor_r_m']:.1f} vs {c['grey_ring1_radius_m']:.1f}")
        out(f"  grey walk speed {g['walk_speed_m_s']:.2f} m/s vs the "
            f"gazetteer's flat {c['beat_walk_speed_m_s']:.2f} -- a Froude gait "
            f"model, so the HEAVY ring is walked FASTER")
        out(f"  grey officer weight {g['officer_weight_kgf']:.0f} kgf vs "
            f"{c['grey_ring1_weight_kgf_at_75kg']:.0f} kgf -- the penalty is "
            f"real and it is in the weight, not the clock")
    return rows


def beat_all(schema=None, profile=None) -> dict:
    """Every sector's beat, keyed by sector."""
    if schema is None:
        schema, profile = it.load()
    return {s: beat(s, schema, profile)
            for s in outermost_decks(schema, profile)}


def response_report(G=None, schema=None, profile=None, out=print):
    """Response times on the routed graph, against section 2.6's headline."""
    if G is None:
        if schema is None:
            schema, profile = it.load()
        G = nav.build_graph(schema, profile)
    out("RESPONSE -- on the same routed graph a resident commutes on")
    rows = []
    for q in dr.PLACES:
        k = q["key"]
        r = response_from_nearest_post(k, G)
        if r["seconds"] is None:
            continue
        rows.append((r["seconds"], k, r["from"], q.get("sector")))
    rows.sort()
    for t, k, who, sec in rows[:3]:
        out(f"  nearest  {k:20s} {t / 60.0:6.1f} min from {who} ({sec})")
    for t, k, who, sec in rows[-3:]:
        out(f"  farthest {k:20s} {t / 60.0:6.1f} min from {who} ({sec})")
    lo, hi = GAZETTEER_CLAIMS["far_sector_response_min"]
    worst = rows[-1][0] / 60.0 if rows else 0.0
    out(f"  {len(rows)} of {len(dr.PLACES)} register places reachable from a "
        f"post; worst {worst:.1f} min against the gazetteer's stated "
        f"{lo:.0f}-{hi:.0f} min for a distant outer ring")
    return rows


def report(out=print):
    """Everything, in the order a builder needs it."""
    schema, profile = it.load()
    out(f"THE FORCE: {force_total()} officers "
        f"(schedule.ROLE_WEIGHTS, FACTIONS.md 2.2)")
    duty = [(h, on_duty(h)) for h in (2, 10, 18, 23)]
    out("  on duty by hour: " + ", ".join(f"{h:02d}h {n}" for h, n in duty)
        + f"  -- the gazetteer says ~{GAZETTEER_CLAIMS['on_duty']}")
    out("")
    posted = post_report(out)
    out("")
    for h in (2, 10, 18):
        rp = roving_pairs(h)
        out(f"  {h:02d}h: {on_duty(h)} on duty - {posted} on post = "
            f"{on_duty(h) - posted} roving = {rp} pairs")
    out(f"  the gazetteer says ~{GAZETTEER_CLAIMS['roving_pairs']} pairs AND "
        f"'the remaining {GAZETTEER_CLAIMS['roving_officers']}', which is "
        f"{GAZETTEER_CLAIMS['roving_officers'] // 2} pairs. See C-011")
    out("")
    beat_report(schema, profile, out)
    out("")
    G = nav.build_graph(schema, profile)
    response_report(G, schema, profile, out)
    out("")
    out("PRESENCE at 18h -- what a player sees")
    for k in ("zocalo", "customs_north", "council_chamber", "downbelow",
              "black_market", "fabrication", "qtr_command"):
        p = presence_at(k, 18.0, schema, profile, G)
        note = p["why"] or ""
        out(f"  {k:18s} {p['officers']:5.1f} officers "
            f"(fixed {p['fixed']}, roving {p['roving']:.1f}) {note}")
    out("")
    pt = patrol("zocalo", 0)
    names = " and ".join(
        f"{o['resident'].name}{' [armband]' if o['armband'] else ''}"
        for o in pt["officers"])
    out(f"A PATROL: {names}")


# ===========================================================================
# 7.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _selftest(out=print):                                       # noqa: C901
    global POSTS, NIGHTWATCH_SHARE
    del _FAILED[:]
    n = 0
    schema, profile = it.load()

    # -- the force -------------------------------------------------------
    n += 1
    check(force_total() == 500,
          "the force is 500", f"{force_total()}")
    n += 1
    duties = [on_duty(h) for h in range(24)]
    check(all(d > 0 for d in duties),
          "somebody is on duty at every hour -- INV-005's night watch",
          f"min {min(duties)} at {duties.index(min(duties))}h")
    n += 1
    check(min(duties) >= 100 and max(duties) <= 260,
          "on duty brackets the gazetteer's ~150",
          f"{min(duties)}..{max(duties)}")

    # -- posts -----------------------------------------------------------
    n += 1
    missing = [k for k, *_ in POSTS if not _has_place(k)]
    check(not missing, "every post is a register place", f"{missing}")
    n += 1
    check(all(p >= 1 for _k, p, *_ in POSTS),
          "every post is manned in whole pairs -- section 2.5's force rule")
    n += 1
    g = GAZETTEER_CLAIMS["fixed_post_officers"]
    check(0.75 * g <= posted_officers() <= 1.25 * g,
          "posted officers agree with the gazetteer's ~60",
          f"{posted_officers()}")
    n += 1
    check(all(_has_place(k) for k in NO_POST),
          "the unpoliced places are real places too")
    n += 1
    check(not set(k for k, *_ in POSTS) & set(NO_POST),
          "no place is both posted and declared unpoliced")

    # -- roving ----------------------------------------------------------
    n += 1
    check(all(roving_pairs(h) > 0 for h in range(24)),
          "there is always at least one roving patrol",
          f"{[roving_pairs(h) for h in range(24)]}")
    n += 1
    check(roving_pairs(10) > roving_pairs(2),
          "the day watch is bigger than the night watch",
          f"10h {roving_pairs(10)} vs 02h {roving_pairs(2)}")

    # -- beats, recomputed -----------------------------------------------
    beats = beat_all(schema, profile)
    n += 1
    check(len(beats) >= 4, "every pressurised sector has a beat",
          f"{sorted(beats)}")
    n += 1
    grey = beats.get("grey")
    check(grey is not None and grey["circumference_m"] > 2000.0,
          "Grey's outermost ring is kilometres round",
          f"{grey['circumference_m']:.0f} m" if grey else "no grey")
    n += 1
    # THE ASSERTION THAT MATTERS: the gazetteer's number is STALE and this is
    # what says so. It is written as a bound rather than an equality because
    # the point is that they DISAGREE, and a future re-address that closed the
    # gap should make this fail and be looked at.
    ratio = grey["circumference_m"] / GAZETTEER_CLAIMS[
        "grey_ring1_circumference_m"]
    check(ratio > 1.10,
          "the gazetteer's Grey circumference is stale by >10% and this "
          "module reports it rather than repeating it", f"x{ratio:.3f}")
    n += 1
    check(grey["walk_speed_m_s"] > GAZETTEER_CLAIMS["beat_walk_speed_m_s"],
          "a Froude gait walks the heavy ring FASTER than the flat 1.3 m/s",
          f"{grey['walk_speed_m_s']:.2f}")
    n += 1
    check(grey["officer_weight_kgf"] >
          GAZETTEER_CLAIMS["grey_ring1_weight_kgf_at_75kg"],
          "and the officer is heavier there than the gazetteer says",
          f"{grey['officer_weight_kgf']:.0f} kgf")
    n += 1
    # A beat is out AND back, so a fixed point is passed twice a circuit.
    b = beats["red"]
    one = beat_interval_s("red", 1, schema, profile)
    two = beat_interval_s("red", 2, schema, profile)
    check(abs(one - b["period_s"] / 2.0) < 1e-6 and abs(two - one / 2.0) < 1e-6,
          "twice the patrols is half the interval, and one patrol is half a "
          "period because the beat is out and back",
          f"{one:.1f} s, {two:.1f} s, period {b['period_s']:.1f} s")
    n += 1
    check(beat_interval_s("red", 0) == float("inf"),
          "no patrols is never, not zero")

    # -- response, on the real graph -------------------------------------
    G = nav.build_graph(schema, profile)
    n += 1
    check(response("brig", G) is not None and response("brig", G) < 120.0,
          "the brig is next door to Security Central",
          f"{response('brig', G)}")
    n += 1
    zoc = response_from_nearest_post("zocalo", G)
    check(zoc["seconds"] == 0.0 and zoc["from"] == "zocalo",
          "the Zocalo answers itself -- section 2.6's 'it is seconds'",
          f"{zoc}")
    n += 1
    far = response_from_nearest_post("fabrication", G)
    lo, hi = GAZETTEER_CLAIMS["far_sector_response_min"]
    check(far["seconds"] is not None and far["seconds"] / 60.0 >= lo,
          "a distant outer-ring place is at least the gazetteer's 12 min "
          "away, computed rather than asserted",
          f"{far['seconds'] / 60.0:.1f} min from {far['from']}"
          if far["seconds"] else "unreachable")
    n += 1
    reach = [k for k in (q["key"] for q in dr.PLACES)
             if response_from_nearest_post(k, G)["seconds"] is not None]
    check(len(reach) >= 100,
          "most of the register is reachable from a post",
          f"{len(reach)} of {len(dr.PLACES)}")
    n += 1
    # THE CONTRAST IS THE POINT, and this is the assertion that carries it.
    check(far["seconds"] > 60.0 * 10.0 and zoc["seconds"] < 60.0,
          "the dramatic geometry holds: seconds in the Zocalo, a quarter of "
          "an hour in Grey",
          f"{zoc['seconds']:.0f} s vs {far['seconds'] / 60.0:.1f} min")

    # -- people ----------------------------------------------------------
    n += 1
    force = officer_pool(18.0, 300)
    check(len(force) >= 100 and all(is_officer(r) for r in force),
          "the officer pool is officers", f"{len(force)}")
    n += 1
    share = (sum(1 for r in force if wears_armband(r.npc_id)) / len(force)
             if force else 0.0)
    check(0.25 <= share <= 0.45,
          "30-40% of the FORCE wear the armband -- FACTIONS.md 5.2's "
          "150-200 of 500. Measured over officers, because a civilian's "
          "band is the informer rate and mixing them reads 1%",
          f"{share * 100:.1f}% over {len(force)}")
    n += 1
    civ = [res.pool_id("zocalo", "human", i, "b5") for i in range(300)]
    civ_share = sum(1 for i in civ if wears_armband(i)) / len(civ)
    check(civ_share < share / 3.0,
          "and a civilian is an order of magnitude less likely to wear one",
          f"civilian {civ_share * 100:.1f}% vs force {share * 100:.1f}%")
    n += 1
    pt = patrol("zocalo", 0)
    check(len(pt["officers"]) == PATROL_UNIT,
          "a patrol is two officers")
    n += 1
    check(pt["armbands"] == 1,
          "one band and one bare sleeve in the same pair -- FACTIONS.md 5.3",
          f"{pt['armbands']}")
    n += 1
    check(all(patrol("zocalo", i)["armbands"] == 1 for i in range(40)),
          "and that holds for every patrol, not the first one")
    n += 1
    a = patrol("customs_north", 3)
    b2 = patrol("customs_north", 3)
    check([o["id"] for o in a["officers"]] == [o["id"] for o in b2["officers"]],
          "a patrol is deterministic in its seed")
    n += 1
    check(a["officers"][0]["resident"].name
          != a["officers"][1]["resident"].name,
          "the two officers are different people",
          f"{a['officers'][0]['resident'].name}")

    # -- presence --------------------------------------------------------
    n += 1
    z = presence_at("zocalo", 18.0, schema, profile, G)
    check(z["officers"] >= 8.0,
          "the Zocalo shows four officers in a glance",
          f"{z['officers']:.1f}")
    n += 1
    d = presence_at("downbelow", 18.0, schema, profile, G)
    check(d["officers"] == 0.0 and not d["policed"],
          "Downbelow has nobody, by design and with the reason attached",
          f"{d}")
    n += 1
    q = presence_at("qtr_command", 18.0, schema, profile, G)
    check(0.0 < q["officers"] < z["officers"],
          "an ordinary residential place is policed, thinly",
          f"{q['officers']:.2f} against the Zocalo's {z['officers']:.1f}")

    # -- THE MEMO, ASSERTED BY CALL COUNT AND NOT BY A STOPWATCH ---------
    # `populace.populate` calls `presence_at` once per room, so a whole-station
    # sweep calls it 128 times. Without the memo each call rebuilt the entire
    # 2,330-cell plan. A timing assertion would be flaky under load; counting
    # the calls is exact.
    n += 1
    real_plan = nav.cell_plan
    calls = []

    def _counting(sch, prof):
        calls.append(1)
        return real_plan(sch, prof)
    try:
        nav.cell_plan = _counting
        _OUTERMOST.clear()
        for _ in range(50):
            presence_at("zocalo", 18.0, schema, profile, G)
        memo_calls = len(calls)
        del calls[:]
        for _ in range(50):
            _OUTERMOST.clear()
            presence_at("zocalo", 18.0, schema, profile, G)
        naive_calls = len(calls)
    finally:
        nav.cell_plan = real_plan
        _OUTERMOST.clear()
    check(memo_calls == 1,
          "50 presence_at calls build the cell plan ONCE",
          f"{memo_calls}")
    n += 1
    check(naive_calls >= 50,
          "and the control -- clearing the memo each time -- builds it every "
          "call, which is what the sweep was doing", f"{naive_calls}")
    out(f"  memo: 50 calls -> {memo_calls} cell_plan build(s); "
        f"control (memo cleared each call) -> {naive_calls}")

    # -- the gazetteer is actually read ----------------------------------
    n += 1
    check(os.path.exists(GAZETTEER),
          "the file this module exists to read is where it says it is")
    n += 1
    txt = open(GAZETTEER).read()
    for phrase in ("2 officers", "No permanent post", "Security Central"):
        check(phrase.lower() in txt.lower(),
              f"the gazetteer still says {phrase!r}")
        n += 1

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS -- every one of these is run, and each restores what
    # it broke. CLAUDE.md: a gate that cannot fail is not a gate.
    # ------------------------------------------------------------------
    out("negative controls:")

    keep = POSTS
    try:
        POSTS = tuple(p for p in POSTS if p[0] != "zocalo")
        z2 = presence_at("zocalo", 18.0, schema, profile, G)
        ctl_a = z2["officers"] < 8.0
        out(f"  drop the Zocalo post -> {z2['officers']:.1f} officers "
            f"(was {z['officers']:.1f}) -- presence gate "
            f"{'FIRES' if ctl_a else 'DOES NOT FIRE'}")
        n += 1
        check(ctl_a, "the presence gate fires when a post is removed")
        posted2 = posted_officers()
        lo = 0.75 * GAZETTEER_CLAIMS["fixed_post_officers"]
        hi = 1.25 * GAZETTEER_CLAIMS["fixed_post_officers"]
        # AND THE ~60 GATE DOES NOT SEE IT, which is stated rather than fixed
        # by tightening a band to make a control look good. A +/-25% window on
        # 60 is 45..75, and one 8-officer post out of 56 lands at 48, inside.
        # That is the honest sensitivity of a tolerance this wide: it catches
        # the table going empty or doubling, not one row going missing. The
        # per-place `presence_at` gate above is what catches one row, and it
        # DOES fire. Both controls are run so the division of labour between
        # them is visible.
        out(f"  and posted officers -> {posted2} -- the ~60 gate does NOT "
            f"fire ({lo:.0f}..{hi:.0f} admits it), and that is its stated "
            f"sensitivity, not a pass")
        n += 1
        check(lo <= posted2 <= hi,
              "one missing post is inside the ~60 band -- the limit is "
              "reported, not hidden", f"{posted2}")
        POSTS = tuple(p for p in POSTS
                      if p[0] not in ("customs_north", "customs_south"))
        posted3 = posted_officers()
        ctl_b = not (lo <= posted3 <= hi)
        out(f"  drop the two customs halls as well -> {posted3} -- the ~60 "
            f"gate {'FIRES' if ctl_b else 'DOES NOT FIRE'}")
        n += 1
        check(ctl_b, "three missing posts DO break the ~60 band",
              f"{posted3}")
    finally:
        POSTS = keep

    # THE CONTROL PATCHES `costume`, NOT THIS MODULE, and that is the point of
    # it: `wears_armband` delegates, so moving costume.py's rate MUST move
    # every number here. If it does not, the delegation has silently been
    # replaced by a second roll -- which is the exact defect this function was
    # rewritten to remove.
    from npc import costume as _cos                              # noqa: PLC0415
    keepn = _cos.NIGHTWATCH_SECURITY_RATE
    try:
        _cos.NIGHTWATCH_SECURITY_RATE = 1.0
        _cos.costume_for.cache_clear() if hasattr(
            _cos.costume_for, "cache_clear") else None
        share2 = (sum(1 for r in force if wears_armband(r.npc_id))
                  / len(force))
        pt2 = patrol("zocalo", 0)
        ctl_c = share2 > 0.45
        # With every officer banded there is no bare sleeve to pair with, so
        # the pair comes back 2/2 -- the split gate's failure, and it must be
        # VISIBLE rather than silently repaired.
        ctl_d = pt2["armbands"] != 1
        out(f"  costume.NIGHTWATCH_SECURITY_RATE -> 1.0 gives "
            f"{share2 * 100:.0f}% of the force banded (was "
            f"{share * 100:.0f}%) -- share gate "
            f"{'FIRES' if ctl_c else 'DOES NOT FIRE'}; the pair reads "
            f"{pt2['armbands']}/2 -- split gate "
            f"{'FIRES' if ctl_d else 'DOES NOT FIRE'}. Both moved from a "
            f"file this module does not own, which is what proves the "
            f"delegation is live")
        n += 2
        check(ctl_c, "the armband-share gate fires when COSTUME moves")
        check(ctl_d, "the one-band-one-sleeve gate fires")
    finally:
        _cos.NIGHTWATCH_SECURITY_RATE = keepn
        _cos.costume_for.cache_clear() if hasattr(
            _cos.costume_for, "cache_clear") else None

    out(f"  the gazetteer's own Grey circumference would pass a x1.10 "
        f"staleness bound at "
        f"{GAZETTEER_CLAIMS['grey_ring1_circumference_m']:.0f} m; the built "
        f"one is {beats['grey']['circumference_m']:.0f} m")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


def _has_place(key: str) -> bool:
    try:
        dr.by_key(key)
        return True
    except Exception:
        return False


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
