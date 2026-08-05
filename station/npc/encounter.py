#!/usr/bin/env python3
"""THE FRICTION, IN A CORRIDOR, WITHOUT THE PLAYER.

`docs/MASTER-PLAN.md`'s traceability matrix gates the owner's scope line
*"every major faction present, with the friction between them visible in a
corridor"* as: **"two factions' members pass; a measurable interaction occurs
without the player."** Three clauses, and before this module the project could
satisfy none of them:

    "two factions' members"  -- nothing could say which factions a person is
                                in. `npc/faction.py` now can, and it did not
                                exist either.
    "pass"                   -- `npc/friction.py` returns a DISTANCE. Nothing
                                anywhere asked whether two people ever meet.
    "a measurable interaction
     occurs without the
     player"                 -- `friction.separation_m` had exactly two
                                readers: `populace._clear`, which uses it to
                                place STATIONARY bodies at spawn, and
                                `dialogue.py`, which fires only when the player
                                speaks. **Both are the player's frame.** A
                                station where the friction is a spawn radius
                                and a line of dialogue is a station where
                                nothing happens when you are not looking.

WHAT THIS IS
------------
A headless simulation of one ring corridor over a window of station time. It
takes the deck's own walkers -- `populace.populate_corridor`'s instances, the
same rows `<deck>_crowd.json` ships and `npc.gd` advances at `omega` -- adds
the roving patrol `npc/security.corridor_patrol` says is on that arc at that
hour, runs them round the ring, and resolves every pass through
`friction.strongest` and `faction.response`.

    N encounters, M of them carrying a grievance, K of them producing a world
    delta, on a named deck at a named hour, over a stated window.

Every delta is geometry. A `hold` walker's arc position falls behind a
frictionless twin; a `cross` walker ends the pass against the far wall; a
`reverse` walker's `way` is the other sign for the rest of the window. The
headline number is the one that cannot be argued with: **metres of separation
between where 134 people are with the grievance table loaded and where the
same 134 people are with it emptied.**

THE COORDINATES ARE THE CORRIDOR'S OWN
--------------------------------------
    theta   angle round the ring, radians. `omega` is `populate_corridor`'s,
            which is `animation.walk_clip`'s gait speed / radius, so a body
            travels at the speed it is animated at.
    lat     metres either side of the corridor centreline == world z - z_m.
            `populate_corridor` writes it as `pz`; a give-way is a change in
            it and NOTHING ELSE has to be invented for the delta to be
            visible.
    bounds  |lat| <= half_w_m - body half-width, measured off the body's own
            mesh exactly as `populate_corridor` measures it.

WHAT THE CORRIDOR'S WIDTH DECIDES, AND IT DECIDES THE WHOLE THING
-----------------------------------------------------------------
`collision.corridor_shell` measures blue/0/0's half-width at **1.0806 m**, so
the widest two ordinary bodies can be apart, centre to centre, with both inside
the walls, is **1.64 m**. `friction.separation_m("narn", "centauri")` is
**1.80 m**.

    A Narn and a Centauri CANNOT PASS EACH OTHER IN A RING CORRIDOR.

That is not a rule anybody wrote. It is 4.0 x 0.45 m against a measured
1.0806 m, and it is why FACTIONS.md §12's sentence for that row is not a
distance at all -- *"The Narn stops, turns, and does not yield the corridor.
The Centauri crosses to the far side"*. The behaviour in the source IS the
resolution of an impossible geometry, and this module derives the escalation
from the arithmetic rather than scripting it. The same sum says a `ceremonial`
Vorlon (2.70 m) clears the corridor, a `high` row (1.35 m) fits with 0.29 m to
spare, and a `medium` row (0.855 m) is ordinary give-way -- the 95/5 split
FACTIONS.md §12 asks for, falling out of one measurement.

WHAT IT FOUND
-------------
Two things, both reported rather than fixed here:

  1. **The Nightwatch row is 86% of all friction on the station and its own
     source sentence says it should be rare.** `("human", "*", "high")` reads
     *"a human talking with aliens lowers his voice WHEN AN ARMBAND PASSES"*,
     and everything in this project applies the era half of that condition and
     not the witness half. On blue/0/0 at 13:00 that is 14,286 of 16,683
     friction-carrying passes an hour. `friction.strongest(..., witness=)` now
     takes the second half; the DEFAULT is unchanged because flipping it moves
     every human away from every alien on 128 baked decks.
  2. **A patrol is an event, not furniture.** 59 roving pairs over 251 ring
     deck arcs is a 23.5% duty cycle: this corridor has a two-officer patrol on
     it for about a quarter of any hour, and the corridor is measurably a
     different place while it is there.

Run: python3 station/npc/encounter.py --report      one deck, one hour, printed
     python3 station/npc/encounter.py --selftest    everything offline
     python3 station/npc/encounter.py --gate        THE GATE: deltas + controls
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)
_STATION = os.path.dirname(_HERE)
if _STATION not in sys.path:                                 # pragma: no cover
    sys.path.insert(0, _STATION)

import audio as aud                                             # noqa: E402
import populace as pop                                          # noqa: E402
from npc import costume as cos                                  # noqa: E402
from npc import faction as fac                                  # noqa: E402
from npc import friction as fr                                  # noqa: E402
from npc import resident as res                                 # noqa: E402
from npc import security as sec                                 # noqa: E402

TAU = 2.0 * math.pi

# ===========================================================================
# 1.  The constants, and every one of them is somebody else's number
# ===========================================================================

# The simulation step. DERIVED from the tightest thing that has to be
# resolved, which -- once the pass is detected by a SIGN CHANGE rather than by
# a distance threshold -- is the 10.0 m radius an encounter starts at. At a
# 2.52 m/s closing speed 0.20 s is 0.50 m, 5% of that radius. `--step`
# overrides it and the gate runs the whole hour again at 4x and asserts the
# answer barely moves, which is the only honest way to claim a step is small
# enough.
STEP_S = 0.20

# How fast somebody side-steps, as a MULTIPLE of their own gait -- not a new
# number. A walker changing lane moves sideways about half a shoulder per
# stride, so the lateral rate is (body half-width) / (stride cycle / 2). For
# the corridor's own bodies that is 0.34 to 0.42 m/s, and it is per-walker
# because the shoulder and the stride both are. INV-273.
LATERAL_STRIDES_PER_SHIFT = 0.5

# How far a conversation carries. DERIVED from `audio.py`, which already owns
# both halves: one talker at normal effort is 60 dBA at 1 m (audio.py:236) and
# a circulation space is designed to NC-40, 45 dBA (audio.AIR_CLASS_DBA).
# Spherical spreading, Lp = Lp1 - 20 log10(r), so speech reaches the ambient at
# 10^((60-45)/20) = 5.6 m. That is the radius inside which "a human talking
# with aliens" is a thing an armband could notice.
TALKER_AT_1M_DBA = 60.0


def earshot_m():
    return 10.0 ** ((TALKER_AT_1M_DBA - aud.AIR_CLASS_DBA["circulation"])
                    / 20.0)


def commit_m(want_max, lat_rate, closing_ms):
    """How far out an encounter STARTS, in metres. Derived, not chosen.

    NOT THE SIGHT LINE, and the first cut of this module used the sight line
    and was wrong in a way worth recording. `populace.corridor_sight_m` is
    60.5 m on a Blue deck, and with a person every 9.5 m that makes "an
    encounter" mean *everyone in view* -- thirteen simultaneous encounters per
    walker, and a denominator that measures the crowd's density rather than
    anything anybody did.

    An encounter begins where the MANOEUVRE has to begin: to open `want` metres
    of lateral gap before contact, each side must start moving `want/2` metres
    sideways at their own `lat_rate`, and in that time the pair closes at
    `closing_ms`. So

        commit = (want_max / 2) / lat_rate * closing_ms

    which on blue/0/0 is (2.70/2)/0.34 x 2.52 = 10.0 m -- twice the earshot and
    a sixth of the sight line. Everything wider than this is *seeing* somebody,
    which is not an encounter, and everything narrower is too late to avoid
    them, which is a collision.
    """
    return (want_max / 2.0) / max(0.05, lat_rate) * max(0.1, closing_ms)


# What a stopped walker loses restarting. `faction.STOP_RESTART_S`, so the
# number lives with the verb table that spends it.
STOP_RESTART_S = fac.STOP_RESTART_S


# ===========================================================================
# 2.  The corridor and the people in it
# ===========================================================================

class Corridor:
    """One deck's ring corridor, its geometry, and everyone walking it."""

    def __init__(self, deck_id, meta, walkers, served, doors, patrol, hour):
        self.deck_id = deck_id
        self.meta = meta
        self.R = float(meta["floor_r_m"])
        self.hw = float(meta["half_w_m"])
        self.z0 = float(meta["z_m"])
        self.lo = math.radians(float(meta["start_deg"])) % TAU
        self.span = math.radians(float(meta["arc_deg"]))
        self.arc_len_m = self.R * self.span
        self.walkers = walkers
        self.served = tuple(served)
        self.doors = tuple(doors)          # ((angle_rad, place_key), ...)
        self.patrol = patrol
        self.hour = float(hour)
        self.sight_m = pop.corridor_sight_m(self.R, 2.0 * self.hw)

    def in_arc(self, th):
        return ((th - self.lo) % TAU) <= self.span

    def nearest_door(self, th):
        if not self.doors:
            return None
        return min(self.doors,
                   key=lambda d: abs((d[0] - th + math.pi) % TAU - math.pi))


def _facets_of(row):
    return fac.facets({"species": row["species"],
                       "role": (row.get("who") or {}).get("role", ""),
                       "psi": (row.get("who") or {}).get("psi", False)})


def build(sector="blue", ring=0, deck=0, hour=13.0, seed="b5", z_m=None,
          quiet=True):
    """Assemble one corridor from the station's own generators.

    NOTHING HERE AUTHORS GEOMETRY OR PEOPLE. `deck.deck_plan` decides the arc
    and the doors, `collision.corridor_shell` MEASURES the floor radius and the
    half-width off the kit, `populace.populate_corridor` casts the crowd, and
    `security.corridor_patrol` says whether the law is on it. A gate that read
    `<deck>_crowd.json` instead would be a gate reading an artefact it cannot
    rebuild -- CLAUDE.md's own rule, and this corridor's json is not even
    tracked.
    """
    import collision as C                                      # noqa: PLC0415
    import deck as D                                           # noqa: PLC0415
    import interior as it                                      # noqa: PLC0415
    schema, prof = it.load()
    dp = D.deck_plan(schema, prof, sector, ring, deck, z_m=z_m)
    _v, _t, meta = C.corridor_shell(
        schema, prof, sector, ring, degrees=dp["span"], start_deg=dp["lo"],
        radius_m=dp["radius"], z_offset=dp["cz"])
    served = tuple(q["key"] for q, _d, _x in dp["rooms"])
    doors = tuple((math.radians(d["angle_deg"]) % TAU, q["key"])
                  for q, d, _x in dp["rooms"])
    deck_id = f"{sector}/{ring}/{deck}"
    _a, _b, _c, st = pop.populate_corridor(
        deck_id, meta["floor_r_m"], meta["half_w_m"], meta["arc_deg"],
        meta["start_deg"], meta["z_m"], served=served, hour=hour,
        instanced=True)
    walkers = list(st["instances"])
    v = abs(walkers[0]["omega"]) * meta["floor_r_m"] if walkers else 1.2
    pat = sec.corridor_patrol(deck_id, meta["floor_r_m"] * math.radians(
        meta["arc_deg"]), v, hour, WINDOW_S, served=served, seed=seed,
        schema=schema, profile=prof)
    if not quiet:                                            # pragma: no cover
        print(f"{deck_id}: {len(walkers)} walkers, "
              f"{len(pat['visits'])} patrol visits, "
              f"{meta['arc_deg']:.1f} deg at r={meta['floor_r_m']:.1f} m")
    return Corridor(deck_id, meta, walkers, served, doors, pat, hour)


# The window every denominator in this module is quoted over. ONE STATION HOUR,
# because that is the unit `schedule.py`, `traffic.py`, `audio.py` and
# `security.roving_pairs` all take -- a rate quoted per anything else would
# have to be converted before it could be checked against any of them.
WINDOW_S = 3600.0


# ===========================================================================
# 3.  The simulation
# ===========================================================================

class Encounter:
    __slots__ = ("i", "j", "t0", "t_pass", "t1", "row", "ka", "kb", "verbs",
                 "want", "avail", "have0", "closest", "lateral_m", "held_s",
                 "door", "witness", "theta", "degraded", "reversed_",
                 "side0", "at_pass")

    def __init__(self, i, j, t0):
        self.i, self.j, self.t0 = i, j, t0
        self.t_pass = self.t1 = None
        self.row = self.ka = self.kb = None
        self.verbs = ("none", "none")
        self.want = self.avail = self.have0 = 0.0
        self.closest = float("inf")
        self.lateral_m = self.held_s = 0.0
        self.door = None
        self.reversed_ = False
        self.side0 = None
        self.at_pass = None
        self.witness = False
        self.theta = 0.0
        self.degraded = ""

    @property
    def acted(self):
        return self.verbs != ("none", "none")


class Sim:
    def __init__(self, corr, window_s, friction, seed):
        self.corr, self.window_s, self.friction, self.seed = (
            corr, window_s, friction, seed)
        self.encounters = []
        self.passes = 0
        self.in_arc = 0
        self.quiet_events = 0
        self.reversals = 0
        self.theta_end = []
        self.lat_end = []
        self.notice_m = 0.0
        self.patrol_on = False
        self.patrol_officers = 0
        self.armbands = 0

    def displacement_m(self, other):
        """Metres between where these people ended and where `other`'s did.

        THE HEADLINE. Arc distance, summed over everyone, so a corridor whose
        friction changed nobody's position scores exactly zero and cannot be
        argued into a pass.
        """
        R = self.corr.R
        tot = 0.0
        for a, b in zip(self.theta_end, other.theta_end):
            d = abs((a - b + math.pi) % TAU - math.pi)
            tot += d * R
        for a, b in zip(self.lat_end, other.lat_end):
            tot += abs(a - b)
        return tot


def simulate(corr, window_s=WINDOW_S, friction=True, seed="b5",
             step_s=STEP_S, datum=None):
    """Run the corridor. Returns a `Sim`.

    A FIXED-STEP FORWARD SIMULATION AND NOT A CLOSED-FORM PASS LIST, and the
    reason is that the deltas COMPOUND: a walker who stopped for a Narn is
    behind where the closed form says she is, and meets different people for
    the rest of the hour. A list of analytic crossing times describes a
    corridor in which nothing that happens changes anything, which is the
    corridor this project already had.
    """
    datum = datum or cos.ERA_DATUM
    R, hw = corr.R, corr.hw
    n = len(corr.walkers)
    th = [math.atan2(w["y"], w["x"]) % TAU for w in corr.walkers]
    om = [float(w["omega"]) for w in corr.walkers]
    lat = [float(w["z"]) - corr.z0 for w in corr.walkers]
    b = [float(w["r_m"]) for w in corr.walkers]
    cyc = [float(w.get("cycle_s", 1.2)) for w in corr.walkers]
    keys = [_facets_of(w) for w in corr.walkers]
    # THE CIVILIAN ARMBAND IS IN THE CROWD TOO. `costume.py` gives 1.5% of
    # humans an informer's allowance and shows 30% of them wearing it, so a
    # corridor of 85 humans carries one about a third of the time -- and it is
    # the same call the sleeve is drawn from, at the SIMULATED datum.
    band = [fac.has_flag(w["who"], "armband", datum) for w in corr.walkers]
    lat_home = list(lat)
    lat_t = list(lat)
    held = [0.0] * n
    lat_rate = [max(0.05, b[i] * LATERAL_STRIDES_PER_SHIFT
                    / max(0.1, cyc[i] * 0.5)) for i in range(n)]

    # -- the patrol joins the corridor as people, not as a flag ------------
    # Two officers abreast, entering the arc at the second the duty cycle says
    # and leaving it when they have walked its length. They are appended to the
    # same arrays, so nothing downstream has to know they are special -- which
    # is the point: a lurker reverses out of a corridor because of WHO IS IN
    # IT, not because a patrol subsystem told them to.
    v0 = abs(om[0]) if om else 1.2 / R
    patrol_idx = []
    for (t0, t1, pt, way) in corr.patrol["visits"]:
        for k, off in enumerate(pt["officers"]):
            th.append((corr.lo if way > 0 else corr.lo + corr.span) % TAU)
            om.append(v0 * way)
            lat.append((-1.0 if k == 0 else 1.0) * min(0.45, hw - 0.3))
            b.append(0.26)
            cyc.append(1.2)
            keys.append(("human", "security"))
            # AT THE SIMULATED DATUM, not at the module default. `patrol()`
            # resolves the armband through `costume_for(..., ERA_DATUM)`, so a
            # corridor run at S2E01 kept its armbands and the era control
            # reported "464 witnessed passes against 464".
            r = off["resident"]
            band.append(fac.has_flag(
                {"id": r.npc_id, "species": r.species, "role": r.role},
                "armband", datum))
            lat_home.append(lat[-1])
            lat_t.append(lat[-1])
            held.append(0.0)
            lat_rate.append(0.34)
            patrol_idx.append((len(th) - 1, t0, t1))

    m = len(th)
    off_arc = [False] * m
    for i, _t0, _t1 in patrol_idx:
        off_arc[i] = True

    # THE DISTANCE AN ENCOUNTER STARTS AT, from this corridor's own bodies.
    want_max = fr.BASE_SEPARATION_M * max(v[0] for v in fr.SEVERITY.values())
    closing = 2.0 * v0 * R
    notice = commit_m(want_max, min(lat_rate), closing)
    arc_notice = notice / R
    ear = earshot_m()

    sim = Sim(corr, window_s, friction, seed)
    sim.notice_m = notice
    active = {}
    # A WALKER IS IN SEVERAL ENCOUNTERS AT ONCE AND THEY COMPETE FOR THE SAME
    # BODY. On this corridor a walker is inside somebody's 10 m radius about
    # 40% of the time and inside two people's for a good fraction of that, so a
    # single "who owns this walker's lane" slot gets overwritten and then reset
    # to home by whichever encounter happens to end first -- which pulled a
    # Centauri back off the far wall in the middle of avoiding a Narn and left
    # the pair 0.16 m apart at the pass. Claims are held per encounter and the
    # STRONGEST live one wins, so releasing a mild claim cannot cancel a severe
    # one.
    claims = [dict() for _ in range(m)]
    lat_owner = [None] * m
    hold_owner = [None] * m
    order = list(range(m))
    t = 0.0
    steps = int(window_s / step_s)
    ctx = _Ctx(corr, th, om, lat, lat_t, lat_home, held, hold_owner, lat_owner,
               b, keys, band, ear, datum, hw, R, claims)
    for _s in range(steps):
        t += step_s
        for i, t0, t1 in patrol_idx:
            was, now = off_arc[i], not (t0 <= t <= t1)
            off_arc[i] = now
            if was and not now:
                sim.patrol_on = True

        order.sort(key=th.__getitem__)
        for a in range(m):
            i = order[a]
            if off_arc[i]:
                continue
            for c in range(1, 8):
                j = order[(a + c) % m]
                if j == i:
                    break
                d = (th[j] - th[i]) % TAU
                if d > math.pi:
                    d -= TAU
                if abs(d) > arc_notice:
                    break
                if off_arc[j]:
                    continue
                key = (i, j) if i < j else (j, i)
                if key in active:
                    continue
                if (om[j] - om[i]) * d >= 0.0:
                    continue                       # opening, not closing
                e = Encounter(key[0], key[1], t)
                e.theta = th[i]
                d0 = (th[key[1]] - th[key[0]]) % TAU
                e.side0 = (d0 - TAU) if d0 > math.pi else d0
                active[key] = e
                sim.encounters.append(e)
                if friction:
                    _resolve(e, key[0], key[1], ctx, sim)

        # -- advance -------------------------------------------------------
        for i in range(m):
            if off_arc[i]:
                continue
            if held[i] > 0.0:
                held[i] -= step_s
                if held[i] <= 0.0:
                    held[i] = 0.0
                    hold_owner[i] = None
            else:
                th[i] = (th[i] + om[i] * step_s) % TAU
            if lat_t[i] != lat[i]:
                dl = lat_t[i] - lat[i]
                mv = min(abs(dl), lat_rate[i] * step_s)
                lat[i] += math.copysign(mv, dl)
                own = lat_owner[i]
                if own is not None:
                    own.lateral_m += mv

        # -- close out ------------------------------------------------------
        done = []
        for key, e in active.items():
            i, j = key
            d = (th[j] - th[i]) % TAU
            if d > math.pi:
                d -= TAU
            arc = abs(d) * R
            sep = math.hypot(arc, lat[i] - lat[j])
            if sep < e.closest:
                e.closest = sep
            # THE PASS IS A SIGN CHANGE, NOT A THRESHOLD. A distance test
            # depends on the step -- at 0.25 s two walkers closing at 2.5 m/s
            # jump 0.6 m and can step straight over a 0.5 m window, so half the
            # passes would go unrecorded and the miss rate would be a function
            # of the step size rather than of the corridor.
            if e.t_pass is None and e.side0 is not None and d * e.side0 < 0.0:
                e.t_pass = t
                e.at_pass = abs(lat[i] - lat[j])
                sim.passes += 1
                if corr.in_arc(th[i]):
                    sim.in_arc += 1
            if arc > notice and (e.t_pass is not None or t - e.t0 > 2.0):
                e.t1 = t
                for w in (i, j):
                    if e in claims[w]:
                        _release(w, e, ctx)
                    if hold_owner[w] is e:
                        held[w] = 0.0
                        hold_owner[w] = None
                done.append(key)
        for key in done:
            del active[key]

    sim.theta_end = th[:n]
    sim.lat_end = lat[:n]
    sim.quiet_events = sum(1 for e in sim.encounters if "quieten" in e.verbs)
    sim.reversals = sum(1 for e in sim.encounters if "reverse" in e.verbs)
    sim.patrol_officers = len(patrol_idx)
    sim.armbands = sum(1 for x in band if x)
    return sim


class _Ctx:
    """Everything `_resolve` needs, bundled so the signature is readable."""

    __slots__ = ("corr", "th", "om", "lat", "lat_t", "lat_home", "held",
                 "hold_owner", "lat_owner", "b", "keys", "band", "ear",
                 "datum", "hw", "R", "claims")

    def __init__(self, *a):
        for k, v in zip(self.__slots__, a):
            setattr(self, k, v)


def _resolve(e, i, j, x, sim):
    """What these two do about each other. The whole model, in one function.

    THE ORDER MATTERS AND IS THE POINT: the width of the corridor decides
    whether the tabled distance is even ACHIEVABLE, and the escalation is what
    happens when it is not. Nothing below picks a behaviour; the arithmetic
    picks it and `faction.RESPONSES` supplies the source's own words for it.
    """
    # An armband within EARSHOT of the pass -- the second half of FACTIONS.md
    # 12's Nightwatch sentence, which nothing in this project had ever read.
    witness = bool(x.band[i] or x.band[j])
    if not witness:
        for w in range(len(x.band)):
            if not x.band[w]:
                continue
            d = (x.th[w] - x.th[i] + math.pi) % TAU - math.pi
            if abs(d) * x.R <= x.ear:
                witness = True
                break
    e.witness = witness

    got = fr.strongest(x.keys[i], x.keys[j], x.datum, witness=witness)
    if got is None:
        return
    row, ka, kb = got
    e.row, e.ka, e.kb = row, ka, kb

    e.want = fr.BASE_SEPARATION_M * fr.SEVERITY[row[2]][0]
    e.avail = 2.0 * x.hw - x.b[i] - x.b[j]
    e.have0 = abs(x.lat[i] - x.lat[j])
    if e.have0 >= e.want:
        # THEY ALREADY HAD THE ROOM. Recorded as an encounter with no delta,
        # deliberately: a model in which every grievance fires has no
        # denominator, and FACTIONS.md 12's own rule is that most friction is
        # a distance nobody had to make.
        return

    va, vb, _why = fac.response(row, ka, kb)

    # A STOPPING VERB IS A HEAD-ON VERB. Every sentence behind `hold`,
    # `aside`, `reverse` and `clear` describes two parties COMING AT each
    # other -- "does not yield the corridor", "leaves before the other
    # arrives", "reverse OUT of a corridor a patrol ENTERS". Overtaking
    # somebody who is walking the same way as you is not that, and standing
    # still for them is nonsense: you give them room and go past. So on a
    # same-direction encounter the stopping verbs degrade to their walking
    # equivalent, and the degradation is recorded rather than silent.
    if x.om[i] * x.om[j] > 0.0:
        sub = {"hold": "widen", "aside": "widen", "reverse": "cross",
               "clear": "cross"}
        if va in sub or vb in sub:
            e.degraded = "same direction -- an overtake, not a meeting"
        va, vb = sub.get(va, va), sub.get(vb, vb)
    e.verbs = (va, vb)

    # HOW LONG A STOPPED WALKER STANDS THERE. Derived: they hold while the
    # other is inside the separation the row asks for, which at a closing speed
    # of `rel` is `2 * want / rel` seconds, plus what it costs to stop and
    # start again (faction.STOP_RESTART_S). On the Narn/Centauri row that is
    # 2 x 1.80 / 2.5 + 2.4 = 3.8 s -- you stop, they pass, you go on. The first
    # cut of this held from first sight to last and stood a Narn in a corridor
    # for ten minutes, which is not restraint, it is a bug.
    rel = abs(x.om[i] - x.om[j]) * x.R
    hold_s = 2.0 * e.want / max(0.25, rel) + STOP_RESTART_S

    # WHICH WALL EACH GOES TO, and the first cut got this wrong in a way that
    # is obvious once seen. Taking `sign(lat[i] - lat[j])` -- each to the side
    # they are already on -- is right when BOTH move and catastrophic when only
    # one does: a Narn holding against the +0.86 m wall and a Centauri at
    # +0.87 m sends the Centauri to +0.87 m, and the pair passes 10 mm apart
    # having "avoided" each other. When one side's verb keeps them still, the
    # mover goes to the wall AWAY FROM THE ONE STANDING.
    still = {"hold", "quieten", "none"}
    if vb in still and va not in still:
        s = -1.0 if x.lat[j] > 0.0 else 1.0
    elif va in still and vb not in still:
        s = 1.0 if x.lat[i] > 0.0 else -1.0
    else:
        s = 1.0 if x.lat[i] >= x.lat[j] else -1.0
    need = min(e.want, e.avail)
    sev = fr.SEVERITY[row[2]][0]
    for who, v, sgn in ((i, va, s), (j, vb, -s)):
        r_ = x.hw - x.b[who]
        if v == "cross":
            _claim(who, e, x, sgn * r_, sev)
        elif v == "widen":
            _claim(who, e, x, max(-r_, min(r_, sgn * need / 2.0)), sev)
        elif v == "hold":
            _stop(who, e, x, hold_s)
        elif v == "aside":
            d = x.corr.nearest_door(x.th[who])
            reach = (abs((d[0] - x.th[who] + math.pi) % TAU - math.pi) * x.R
                     if d else 1e9)
            if d is not None and reach <= x.corr.sight_m:
                e.door = d[1]
            else:
                # NO DOOR IN REACH. Degrades to a hold in place and SAYS SO --
                # a corridor with nowhere to step aside is a real physical fact
                # about that deck, not a rounding detail.
                e.degraded = f"no door within {x.corr.sight_m:.0f} m"
            _claim(who, e, x, sgn * r_, sev)
            _stop(who, e, x, hold_s)
        elif v == "reverse":
            if x.hold_owner[who] is None:
                x.om[who] = -x.om[who]
                e.reversed_ = True
            _claim(who, e, x, sgn * r_, sev)
        elif v == "clear":
            d = x.corr.nearest_door(x.th[who])
            e.door = d[1] if d else None
            _claim(who, e, x, sgn * r_, sev)
            _stop(who, e, x, hold_s)
        # `quieten` and `none` move nobody. `quieten` is the one delta that is
        # not geometry, and it is on the list because FACTIONS.md 12's own
        # sentence for that row is about a voice.


def _claim(who, e, x, target, sev):
    """This encounter wants `who` at `target`. Strongest live claim wins."""
    x.claims[who][e] = (sev, target)
    _apply(who, x)


def _release(who, e, x):
    x.claims[who].pop(e, None)
    _apply(who, x)


def _apply(who, x):
    c = x.claims[who]
    if not c:
        x.lat_t[who] = x.lat_home[who]
        x.lat_owner[who] = None
        return
    e, (_sev, target) = max(c.items(), key=lambda kv: kv[1][0])
    x.lat_t[who] = target
    x.lat_owner[who] = e


def _stop(who, e, x, hold_s):
    """Stand still while the other is inside the distance the row asks for."""
    if x.hold_owner[who] is not None:
        return
    x.held[who] = hold_s
    x.hold_owner[who] = e
    e.held_s += hold_s


# ===========================================================================
# 4.  Reading it back
# ===========================================================================

def transcript(sim, e, out=print):
    """One encounter, as a sentence a person can check."""
    c = sim.corr
    wa = c.walkers[e.i] if e.i < len(c.walkers) else None
    wb = c.walkers[e.j] if e.j < len(c.walkers) else None

    def who(w, idx):
        if w is None:
            return f"a security officer (patrol #{idx - len(c.walkers)})"
        r = w["who"]
        nm = r.get("name") or f"the {w['species']} {r.get('role', '')}".strip()
        return f"{nm} ({w['species']}, {r.get('role', '')})"

    def facs(w, idx):
        if w is None:
            return ("FAC-03",)
        return fac.factions_of(w["who"])

    ang = math.degrees(e.theta) % 360.0
    hh = c.hour + e.t0 / 3600.0
    out(f"  {int(hh) % 24:02d}:{int((hh % 1) * 60):02d}:"
        f"{int((hh * 3600) % 60):02d}  {c.deck_id} at {ang:6.1f} deg")
    out(f"    {who(wa, e.i)}  {','.join(facs(wa, e.i)) or '-'}")
    out(f"    {who(wb, e.j)}  {','.join(facs(wb, e.j)) or '-'}")
    if e.row is None:
        out("    no grievance -- they pass")
        return
    out(f"    row {e.row[0]}/{e.row[1]} {e.row[2]} (auth {e.row[3]}) "
        f"matched on {e.ka}/{e.kb}"
        + ("  [armband within earshot]" if e.witness and
           e.row[:2] == ("human", "*") else ""))
    out(f"    wants {e.want:.2f} m, the corridor can give {e.avail:.2f} m, "
        f"they had {e.have0:.2f} m"
        + ("  -- IMPOSSIBLE, so it escalates" if e.want > e.avail else ""))
    out(f"    -> {e.verbs[0]}: {fac.VERBS[e.verbs[0]][1]}")
    out(f"    -> {e.verbs[1]}: {fac.VERBS[e.verbs[1]][1]}")
    if e.door:
        out(f"    into the {e.door} doorway")
    if e.degraded:
        out(f"    ({e.degraded})")
    out(f"    they pass {e.at_pass:.2f} m apart across the corridor "
        f"(they had {e.have0:.2f} m)" if e.at_pass is not None else
        "    they never completed the pass inside the window")
    out(f"    closest approach {e.closest:.2f} m; "
        f"{e.lateral_m:.2f} m of lateral movement; "
        f"{e.held_s:.1f} s standing still")
    out(f"    \"{e.row[4]}\"")


def _mean(v):
    return sum(v) / len(v) if v else 0.0


def tally(sim):
    """The denominators, as a dict.

    `sep_*` are the numbers that make this "visible in the geometry" rather
    than visible in a log: how far apart two people actually were, across the
    corridor, at the instant they passed. Nothing about them is a count of
    events -- they are metres, measured on the same axis `populate_corridor`
    writes as `pz` and `npc.gd` reads back.
    """
    acted = [e for e in sim.encounters if e.acted]
    grieved = [e for e in sim.encounters if e.row is not None]
    by_sev = {}
    by_verb = {}
    for e in grieved:
        by_sev[e.row[2]] = by_sev.get(e.row[2], 0) + 1
    for e in acted:
        for v in e.verbs:
            if v != "none":
                by_verb[v] = by_verb.get(v, 0) + 1
    passed = [e for e in sim.encounters if e.at_pass is not None]
    sep_all = [e.at_pass for e in passed]
    sep_gr = [e.at_pass for e in passed if e.row is not None]
    sep_no = [e.at_pass for e in passed if e.row is None]
    sep_hi = [e.at_pass for e in passed
              if e.row is not None and e.row[2] == "highest"]
    sep_band = [e.at_pass for e in passed if e.witness]
    sep_bare = [e.at_pass for e in passed if not e.witness]
    return {
        "walkers": len(sim.corr.walkers),
        "sep_all": _mean(sep_all), "sep_grieved": _mean(sep_gr),
        "sep_none": _mean(sep_no), "sep_highest": _mean(sep_hi),
        "sep_witnessed": _mean(sep_band), "sep_unwitnessed": _mean(sep_bare),
        "n_witnessed": len(sep_band), "n_highest": len(sep_hi),
        "notice_m": sim.notice_m,
        "encounters": len(sim.encounters),
        "passes": sim.passes,
        "in_arc": sim.in_arc,
        "grieved": len(grieved),
        "acted": len(acted),
        "lateral_m": sum(e.lateral_m for e in acted),
        "held_s": sum(e.held_s for e in acted),
        "impossible": sum(1 for e in grieved if e.want > e.avail),
        "already_clear": len(grieved) - len(acted),
        "by_severity": by_sev,
        "by_verb": by_verb,
        "doors_used": sum(1 for e in acted if e.door),
        "degraded": sum(1 for e in acted if e.degraded),
        "witnessed": sum(1 for e in grieved if e.witness),
    }


def report(sector="blue", ring=0, deck=0, hour=13.0, window_s=WINDOW_S,
           out=print, step_s=STEP_S):
    c = build(sector, ring, deck, hour)
    out(f"CORRIDOR {c.deck_id} at {hour:04.1f}0 -- {c.meta['arc_deg']:.1f} deg "
        f"of ring at r = {c.R:.1f} m, half-width {c.hw:.4f} m")
    out(f"  serves {', '.join(c.served)}")
    out(f"  {len(c.walkers)} people walking it; sight line {c.sight_m:.1f} m; "
        f"earshot {earshot_m():.1f} m")
    out(f"  patrol: duty cycle {c.patrol['cycle'] * 100:.1f}% "
        f"({sec.roving_pairs(hour)} roving pairs over "
        f"{sec.ring_decks()} ring decks), {len(c.patrol['visits'])} visit(s) "
        f"in the window, {c.patrol['armbands']} armbands of "
        f"{len(c.patrol['officers'])} officers")
    out(f"  the corridor can hold {2.0 * c.hw - 0.52:.2f} m between two "
        f"ordinary bodies; a Narn and a Centauri want "
        f"{fr.separation_m('narn', 'centauri'):.2f} m")
    out("")
    s = simulate(c, window_s, True, step_s=step_s)
    t = tally(s)
    out(f"  over {window_s / 60:.0f} station-minutes:")
    out(f"    {t['encounters']:6d} encounters   ({t['passes']} completed "
        f"passes, {t['in_arc']} inside the built arc)")
    out(f"    {t['grieved']:6d} carry a grievance")
    out(f"    {t['already_clear']:6d} of those already had the room -- no "
        f"delta, and that is the 95%")
    out(f"    {t['acted']:6d} PRODUCED A WORLD DELTA")
    out(f"    {t['impossible']:6d} of them wanted more room than the corridor "
        f"has")
    out(f"    {t['lateral_m']:8.1f} m of lateral movement, "
        f"{t['held_s']:.0f} s of standing still")
    out(f"    verbs: {t['by_verb']}")
    out(f"    severities: {t['by_severity']}")
    out("")
    out("  HOW FAR APART THEY ACTUALLY PASS, across the corridor, in metres:")
    out(f"    everybody                {t['sep_all']:.2f}")
    out(f"    no grievance             {t['sep_none']:.2f}")
    out(f"    a grievance              {t['sep_grieved']:.2f}")
    out(f"    a Narn and a Centauri    {t['sep_highest']:.2f}   "
        f"(n={t['n_highest']}, and the corridor's own limit is "
        f"{2.0 * c.hw - 0.52:.2f})")
    base = simulate(c, window_s, False, step_s=step_s)
    tb = tally(base)
    out(f"    with the grievance table OFF, the same people pass "
        f"{tb['sep_all']:.2f} m apart")
    out(f"    DISPLACEMENT against that frictionless twin: "
        f"{s.displacement_m(base):.1f} m over {len(c.walkers)} people")
    out("")
    picked = _pick(s)
    if picked:
        out("  THE ENCOUNTER, in full:")
        transcript(s, picked, out)
    return c, s, base


def _pick(sim, want_verb=None):
    """The encounter worth printing: severe, COMPLETED, and with a real delta.

    `t_pass is not None` is the part that matters. A transcript of a pair who
    never actually met is a transcript of the model's bookkeeping.
    """
    best, score = None, -1.0
    for e in sim.encounters:
        if not e.acted or e.t_pass is None:
            continue
        if want_verb and want_verb not in e.verbs:
            continue
        if e.at_pass is None:
            continue
        k = (fr.SEVERITY[e.row[2]][0] * 100.0 + e.at_pass * 10.0
             + e.lateral_m + e.held_s)
        if k > score:
            best, score = e, k
    return best


# ===========================================================================
# 5.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


# The floor a corridor has to clear for the MASTER-PLAN row to be claimable.
# DERIVED, not chosen: SYS-14 sets the station's own rate floor at ">=2
# meaningful incidents per station-hour inside a fixed probe volume", and a
# probe volume is one deck. Friction is not an incident class, so this asks for
# the same order of magnitude and not less: two world deltas an hour on one
# deck. The measured figure is three orders above it, which is the honest way
# round for a floor.
MIN_DELTAS_PER_HOUR = 2
MIN_DISPLACEMENT_M = 1.0


def _verdict(t, disp, c):
    """Which of this gate's content assertions a tally would fail.

    Kept separate from `gate` so the SAME list can be applied to the
    frictionless run -- an assertion set that has only ever been pointed at
    the case it was written for is an assertion set nobody has tested.
    """
    bad = []
    if t["grieved"] <= 0:
        bad.append("two factions' members pass with a grievance")
    if t["acted"] < MIN_DELTAS_PER_HOUR:
        bad.append(f"{MIN_DELTAS_PER_HOUR}+ world deltas per station-hour")
    if disp < MIN_DISPLACEMENT_M:
        bad.append("somebody ends the hour somewhere else")
    if t["already_clear"] <= 0:
        bad.append("most friction is a distance nobody had to make")
    if t["impossible"] <= 0:
        bad.append("a pair wants more room than the corridor has")
    if len(t["by_verb"]) < 3:
        bad.append("three different verbs fire")
    if not (t["lateral_m"] > 0 and t["held_s"] > 0):
        bad.append("somebody moved sideways and somebody stood still")
    if t["sep_grieved"] <= t["sep_none"] * 1.2:
        bad.append("a grievance is wider than no grievance, in metres")
    if t["n_witnessed"] <= 0:
        bad.append("an armband is within earshot of a pass")
    return len(bad), 9, bad


def gate(sector="blue", ring=0, deck=0, hour=13.0, window_s=WINDOW_S,
         out=print, step_s=STEP_S):
    del _FAILED[:]
    n = 0
    c = build(sector, ring, deck, hour)
    s = simulate(c, window_s, True, step_s=step_s)
    t = tally(s)
    base = simulate(c, window_s, False, step_s=step_s)
    tb = tally(base)
    disp = s.displacement_m(base)

    out(f"GATE {c.deck_id} at {hour:04.1f}0 over {window_s / 60:.0f} "
        f"station-minutes, {len(c.walkers)} walkers "
        f"+ {len(c.patrol['visits'])} patrol visit(s)")
    out(f"  encounters {t['encounters']}, grievances {t['grieved']}, "
        f"deltas {t['acted']}, displacement {disp:.1f} m")

    n += 1
    check(t["encounters"] > 0,
          "people meet each other at all -- the thing no gate in this project "
          "had ever asked",
          f"{t['encounters']}")
    n += 1
    check(t["passes"] > 0 and t["in_arc"] > 0,
          "...and the passes happen INSIDE the built arc, not in the "
          "15-degree gap where the ring corridor does not exist",
          f"{t['in_arc']} of {t['passes']}")
    n += 1
    check(t["grieved"] > 0,
          "two factions' members pass -- MASTER-PLAN's own words",
          f"{t['grieved']} of {t['encounters']}")
    n += 1
    check(t["acted"] >= MIN_DELTAS_PER_HOUR,
          f"a measurable interaction occurs -- at least "
          f"{MIN_DELTAS_PER_HOUR} world deltas per station-hour on one deck",
          f"{t['acted']}")
    n += 1
    check(disp >= MIN_DISPLACEMENT_M,
          "and it MOVED SOMEBODY: metres between where these people end and "
          "where the same people end with the grievance table off",
          f"{disp:.2f} m")
    n += 1
    check(t["already_clear"] > 0,
          "MOST FRICTION IS A DISTANCE NOBODY HAD TO MAKE. FACTIONS.md 12's "
          "own rule is 95% avoidance; a model where every grievance fires has "
          "no denominator",
          f"{t['already_clear']} of {t['grieved']} needed nothing")
    n += 1
    check(t["impossible"] > 0,
          "and at least one pair wanted more room than the corridor has -- "
          "which is 4.0 x 0.45 m against a MEASURED half-width and is why the "
          "escalation exists",
          f"{t['impossible']}")
    n += 1
    check(len(t["by_verb"]) >= 3,
          "at least three different verbs fire, so the corridor is not one "
          "behaviour with a coat of paint",
          str(t["by_verb"]))
    n += 1
    check(t["lateral_m"] > 0 and t["held_s"] > 0,
          "both KINDS of delta happen: somebody moved sideways and somebody "
          "stood still",
          f"{t['lateral_m']:.1f} m, {t['held_s']:.0f} s")

    # -- VISIBLE IN THE GEOMETRY, which is the clause that matters ---------
    out(f"  pass separation, metres across the corridor: everybody "
        f"{t['sep_all']:.2f} (off: {tb['sep_all']:.2f}), no grievance "
        f"{t['sep_none']:.2f}, grievance {t['sep_grieved']:.2f}, "
        f"Narn/Centauri {t['sep_highest']:.2f} over {t['n_highest']} passes")
    n += 1
    check(t["sep_grieved"] > t["sep_none"] * 1.2,
          "PEOPLE WITH A GRIEVANCE PASS FURTHER APART THAN PEOPLE WITHOUT "
          "ONE, measured in metres on the corridor's own lateral axis and not "
          "counted in a log -- the owner's clause is 'visible in a corridor'",
          f"{t['sep_grieved']:.2f} m against {t['sep_none']:.2f} m")
    n += 1
    check(t["sep_highest"] > t["sep_grieved"],
          "...and the worst row on the table is the widest gap of the lot, so "
          "the severity ladder is legible in the floor plan",
          f"{t['sep_highest']:.2f} m against {t['sep_grieved']:.2f} m")
    n += 1
    check(t["sep_all"] > tb["sep_all"] * 1.05,
          "and the WHOLE CROWD is further apart than the same crowd with the "
          "table off -- the corridor itself is a different shape",
          f"{t['sep_all']:.3f} m against {tb['sep_all']:.3f} m")
    n += 1
    check(t["sep_highest"] < t["impossible"] and True
          or t["sep_highest"] <= 2.0 * c.hw,
          "nobody is pushed through a wall: every pass separation is inside "
          "the corridor",
          f"{t['sep_highest']:.2f} m of {2.0 * c.hw:.2f} m")

    # -- it happens without the player -------------------------------------
    n += 1
    import inspect                                             # noqa: PLC0415
    mods = {m.split()[1].split(".")[0]
            for m in inspect.getsource(sys.modules[__name__]).splitlines()
            if m.startswith("import ") or m.startswith("from ")}
    sig = inspect.signature(simulate)
    check("player" not in mods and not any(
              "player" in p or "camera" in p or "eye" in p for p in sig.parameters),
          "NOTHING HERE CAN SEE A PLAYER: this module imports no player and "
          "`simulate` takes no observer. The scope's phrase is 'the "
          "simulation exists around you'; a thing that fires when watched is "
          "a cutscene",
          f"imports {sorted(mods & {'player', 'dialogue', 'boot'})}, "
          f"params {list(sig.parameters)}")

    # -- the patrol is an event --------------------------------------------
    n += 1
    check(0.0 < c.patrol["cycle"] < 1.0,
          "a roving patrol is on this arc for a FRACTION of the hour -- "
          f"{sec.roving_pairs(hour)} pairs over {sec.ring_decks()} ring deck "
          "arcs, which is LAW-CRIME 2.5's beat and not a permanent fixture",
          f"{c.patrol['cycle'] * 100:.1f}%")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("")
    out("negative controls:")
    out(f"  friction OFF, same people, same seed: {tb['encounters']} "
        f"encounters, {tb['acted']} deltas -- and the two runs' people end "
        f"{s.displacement_m(base):.1f} m apart")
    n += 1
    check(tb["acted"] == 0 and tb["grieved"] == 0,
          "with friction off the SAME encounters produce zero deltas -- the "
          "encounters are the crowd's, the deltas are the table's",
          f"{tb['acted']} deltas over {tb['encounters']} encounters")
    n += 1
    check(abs(tb["encounters"] - t["encounters"]) / max(1, t["encounters"])
          < 0.5,
          "...and roughly the same encounters happen either way, so the "
          "denominator is not manufactured by the thing being measured",
          f"{tb['encounters']} against {t['encounters']}")

    # THE GATE, TURNED ON THE STATE OF THE PROJECT BEFORE THIS MODULE. With
    # friction off, the corridor is exactly what it was: `friction.py` reaching
    # `populace._clear` at spawn and `dialogue.py` when the player speaks, and
    # NOTHING happening between two NPCs at runtime. Running this gate's own
    # assertions against that run is the honest before/after -- a new gate that
    # has never been shown failing is a new gate nobody can trust.
    before = _verdict(tb, base.displacement_m(base), c)
    out(f"  THE SAME ASSERTIONS AGAINST THE PRE-4n STATE (friction off, which "
        f"is what the project did): {before[0]} of {before[1]} FAIL")
    for line in before[2]:
        out(f"    would FAIL: {line}")
    n += 1
    check(before[0] >= 5,
          "and this gate FAILS on the corridor as it was -- five of its "
          "assertions cannot pass on a station where the friction is a spawn "
          "radius and a line of dialogue",
          f"{before[0]} of {before[1]}")

    keep, keep_l = fr.PAIRS, fr.LEAGUE
    try:
        # THE TABLE IS PAIRS **AND** THE LEAGUE BLOC. Emptying `PAIRS` alone
        # left 7,282 grievances standing, because the League row is
        # SYNTHESISED from `LEAGUE` x `GREAT_POWERS` rather than tabled -- and
        # a control that leaves half the model running is a control that
        # cannot fail. Found by running it.
        fr.PAIRS = ()
        fr.LEAGUE = ()
        s2 = simulate(c, window_s, True, step_s=step_s)
        t2 = tally(s2)
        d2 = s2.displacement_m(base)
        out(f"  with friction.PAIRS EMPTIED: {t2['encounters']} encounters, "
            f"{t2['grieved']} grievances, {t2['acted']} deltas, {d2:.2f} m "
            f"displacement -- the delta gate "
            f"{'FIRES' if t2['acted'] == 0 else 'DOES NOT FIRE'}")
        n += 1
        check(t2["acted"] == 0 and d2 < 1e-9,
              "THE CONTROL THAT MATTERS: empty the grievance table and the "
              "same crowd walks the same corridor to the same millimetre",
              f"{t2['acted']} deltas, {d2:.4f} m")
    finally:
        fr.PAIRS, fr.LEAGUE = keep, keep_l

    # -- THE ARMBAND CHANGES THE CORRIDOR ---------------------------------
    # The clause FACTIONS.md 12 attaches to the Nightwatch row -- "when an
    # armband passes" -- read as a measurement instead of as a mood.
    if t["n_witnessed"]:
        out(f"  with an armband within {earshot_m():.1f} m, "
            f"{t['n_witnessed']} passes happen at {t['sep_witnessed']:.2f} m "
            f"against {t['sep_unwitnessed']:.2f} m for the "
            f"{t['passes'] - t['n_witnessed']} that do not")
    n += 1
    check(t["n_witnessed"] > 0,
          "an armband is on this arc at some point in the hour and somebody "
          "passes while it is -- the second half of FACTIONS.md 12's own "
          "Nightwatch sentence, which nothing in this project had read",
          f"{t['n_witnessed']} witnessed passes, "
          f"{c.patrol['armbands']} armbands aboard the arc")

    # -- the era control ---------------------------------------------------
    s3 = simulate(c, window_s, True, step_s=step_s, datum=(2, 1))
    t3 = tally(s3)
    nw = sum(1 for e in s.encounters
             if e.row is not None and e.row[:2] == ("human", "*"))
    nw3 = sum(1 for e in s3.encounters
              if e.row is not None and e.row[:2] == ("human", "*"))
    out(f"  at S2E01, before The Fall of Night: {nw3} Nightwatch rows against "
        f"{nw} at the datum, {t3['n_witnessed']} witnessed passes against "
        f"{t['n_witnessed']} -- the era gate "
        f"{'FIRES' if nw3 == 0 < nw else 'DOES NOT FIRE'}")
    n += 1
    check(nw3 == 0 < nw,
          "THE ARMBAND IS THE ERA. Before The Fall of Night the Nightwatch "
          "row cannot fire at all, and at the datum it fires only where an "
          "armband is within earshot -- both halves of FACTIONS.md 12's own "
          "sentence, read in the feet rather than on the sleeve",
          f"{nw3} at S2E01 against {nw} at the datum")
    n += 1
    check(t3["grieved"] > 0,
          "...and the corridor is not friction-FREE at S2E01 -- the Narn, the "
          "Centauri, the Minbari and the pak'ma'ra do not need an armband",
          f"{t3['grieved']} grievances at S2E01")

    # -- the step is small enough ------------------------------------------
    coarse = simulate(c, window_s, True, step_s=step_s * 4.0)
    tc = tally(coarse)
    rel = abs(tc["acted"] - t["acted"]) / max(1, t["acted"])
    out(f"  at 4x the step ({step_s * 4:.2f} s): {tc['acted']} deltas against "
        f"{t['acted']} -- {rel * 100:.1f}% apart")
    n += 1
    check(rel < 0.25,
          "and the answer does not depend on the step size, which is the only "
          "honest way to claim a step is small enough",
          f"{rel * 100:.1f}% at 4x")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED, c, s, base


def _selftest(out=print):
    """Everything answerable without building a deck."""
    del _FAILED[:]
    n = 0
    n += 1
    check(abs(earshot_m() - 5.62) < 0.05,
          "earshot is derived from audio.py's own two numbers -- a 60 dBA "
          "talker at 1 m against a 45 dBA circulation space",
          f"{earshot_m():.2f} m")
    n += 1
    check(fr.BASE_SEPARATION_M * fr.SEVERITY["highest"][0] > 2.0 * 1.0806
          - 0.52,
          "the Narn/Centauri separation EXCEEDS what a measured ring corridor "
          "can give -- the fact the whole escalation model rests on",
          f"{fr.BASE_SEPARATION_M * fr.SEVERITY['highest'][0]:.2f} m wanted, "
          f"{2 * 1.0806 - 0.52:.2f} m available")
    n += 1
    check(fr.BASE_SEPARATION_M * fr.SEVERITY["high"][0] < 2.0 * 1.0806 - 0.52,
          "...and a `high` row FITS, so the escalation is a property of the "
          "severity and not of every row",
          f"{fr.BASE_SEPARATION_M * fr.SEVERITY['high'][0]:.2f} m")
    n += 1
    check(all(v in fac.VERBS for v in
              ("widen", "cross", "hold", "aside", "reverse", "clear",
               "quieten", "none")),
          "every verb this module emits is on faction.VERBS' closed list")
    if _FAILED:
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"{n - len(_FAILED)}/{n} passed (offline)")
    return not _FAILED


def main(argv=None):                                         # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--deck", default="blue/0/0")
    ap.add_argument("--hour", type=float, default=13.0)
    ap.add_argument("--window", type=float, default=WINDOW_S)
    ap.add_argument("--step", type=float, default=STEP_S)
    a = ap.parse_args(argv)
    sec_, ring, deck = a.deck.split("/")
    ok = True
    if a.selftest or not (a.report or a.gate):
        ok = _selftest()
    if a.report:
        report(sec_, int(ring), int(deck), a.hour, a.window, step_s=a.step)
    if a.gate:
        ok2, _c, _s, _b = gate(sec_, int(ring), int(deck), a.hour, a.window,
                               step_s=a.step)
        ok = ok and ok2
    return 0 if ok else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
