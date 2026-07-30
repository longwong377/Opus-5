#!/usr/bin/env python3
"""Put people in every room on the station, from the schedule that already exists.

WHAT THIS WIRES UP. Seven modules under `station/npc/` -- 226 callables and some
three thousand passing assertions -- had **zero importers outside their own
directory** when this was written. `npc/body.build('human', id)` returns a
4,560-triangle body 1.72 m tall and nothing had ever called it.
`npc/schedule.py` carries 25 `PlaceCrowd` entries with peak occupancy per 100 m2,
species mix, and busy and dead hours; a 250,000 resident total; and an
`NPC_BUDGET` with a four-level LOD chain. None of it reached a frame. This module
is the consumer.

THE PLACEMENT IDEA, and it is the whole difference between a room with people in
it and people using a room. `station/dressing.py` finds surfaces by READING THEM
BACK off the geometry it just emitted -- that is how clutter lands on tabletops
with no second list to keep in step. The same read finds SEATS: a horizontal face
at 0.40-0.55 m is a chair, one at 0.70-0.80 m is a desk you stand at. So people
are placed AT things. A chair with nobody on it and a person standing in the
middle of the floor are both wrong in the same way, and both were what a naive
scatter would give.

THE HOUR IS A PARAMETER, so the same generator gives a different station at 0300
than at 1300 for nothing. `PlaceCrowd.busy` and `.dead` are already written per
place. A shift change is `hour=`.

Poses, not animation, for now: a standing figure and a seated figure read as a
populated station in a frame and cost nothing at runtime. `npc/animation.py` has
`Rig`, `Skeleton` and `apply_pose` for when they need to walk.
"""
import hashlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "npc"))

import body as _body                                            # noqa: E402
import schedule as _sched                                       # noqa: E402

# Seat and desk heights, in metres. A face inside SEAT_BAND is something you sit
# on; one inside DESK_BAND is something you stand at and work on. Taken from
# `rooms.PROPS`' own dimensions -- seat 0.45, bench 0.45, stool 0.62, table 0.74
# -- so the bands describe the furniture this station actually builds.
SEAT_BAND = (0.38, 0.66)
DESK_BAND = (0.68, 1.15)
# A body needs this much clear floor in front of a desk to stand at it.
STAND_OFF_M = 0.55
# LOD1 from `schedule.NPC_BUDGET`: 2,000 triangles, good from 6 to 18 m, which
# is the range a room is seen at. LOD0 is 8,000 and is for a face in dialogue.
ROOM_LOD = 1
# Nobody is in a sealed plant room at 0300, and a bar at 1300 is not full.
# Without a floor every quiet room reads as abandoned rather than quiet.
MIN_PRESENT = 0


def _u(*parts):
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# `schedule.PLACES` is a dict keyed by place, not a list -- checked rather
# than assumed, because the first version iterated it and got its keys.
_CROWD = dict(_sched.PLACES)


def occupancy(place_key, area_m2, hour, arch="generic"):
    """How many people are in this place at this hour.

    Reads `schedule.PlaceCrowd` where the gazetteer key has one -- 25 places do
    -- and falls back to a per-archetype rate for the rest. The fallback is
    deliberately LOW: a store room with four people in it is wrong in a way a
    viewer notices, and this project's failure mode has been claiming things it
    has not measured.
    """
    pc = _CROWD.get(place_key)
    if pc is not None:
        peak = pc.peak_per_100m2 * area_m2 / 100.0
        f = _hour_factor(pc, hour)
        return max(MIN_PRESENT, int(round(peak * f)))
    rate = FALLBACK_PER_100M2.get(arch, 0.6)
    day = 0.25 + 0.75 * max(0.0, math.sin(math.pi * (hour - 6.0) / 14.0))
    return max(MIN_PRESENT, int(round(rate * area_m2 / 100.0 * day)))


FALLBACK_PER_100M2 = {
    "commerce": 6.0, "hospitality": 8.0, "transit": 5.0, "office": 2.5,
    "medical": 2.0, "research": 1.5, "industrial": 1.0, "store": 0.5,
    "detention": 0.8, "worship": 1.5, "generic": 1.2,
}


def _hour_factor(pc, hour):
    """Fraction of peak at this hour, from the place's own busy/dead windows."""
    h = hour % 24.0

    def _in(windows):
        for a, b in windows:
            if a <= b:
                if a <= h < b:
                    return True
            elif h >= a or h < b:
                return True
        return False

    if getattr(pc, "flat", False):
        return 0.75
    if _in(getattr(pc, "dead", ()) or ()):
        return 0.08
    if _in(getattr(pc, "busy", ()) or ()):
        return 1.0
    return 0.45


def species_for(place_key, i, seed):
    """Which species this person is, from the place's own mix."""
    pc = _CROWD.get(place_key)
    if pc is None:
        return "human"
    if _u(seed, "sp", i) < pc.human_share:
        return "human"
    dom = pc.dominant or ("human",)
    return dom[int(_u(seed, "dom", i) * len(dom)) % len(dom)]


def _faces_in_band(v, t, g, lo_h, hi_h, min_area=0.12):
    """Upward faces whose height is in a band -- seats, or desks.

    Read off the geometry rather than tracked beside it, for the reason
    `dressing._surfaces_of` is: a kit that grows a new bench gets people sitting
    on it with nothing to keep in step.
    """
    out = []
    for _name, lo, hi in g:
        for tri in t[lo:hi]:
            p = [v[i] for i in tri]
            y = p[0][1]
            if not (lo_h <= y <= hi_h):
                continue
            if max(abs(y - p[1][1]), abs(y - p[2][1])) > 1e-6:
                continue
            xs = [q[0] for q in p]
            zs = [q[2] for q in p]
            a = abs((xs[1] - xs[0]) * (zs[2] - zs[0])
                    - (xs[2] - xs[0]) * (zs[1] - zs[0]))
            if a < min_area:
                continue
            out.append((sum(xs) / 3.0, y, sum(zs) / 3.0, a))
    return out


def _place_body(v, t, g, mesh, x, y, z, yaw, group):
    bv, bt, _bg = mesh
    n0 = len(v)
    ca, sa = math.cos(yaw), math.sin(yaw)
    for (px, py, pz) in bv:
        v.append((x + px * ca - pz * sa, y + py, z + px * sa + pz * ca))
    t0 = len(t)
    t.extend((a + n0, b + n0, c + n0) for a, b, c in bt)
    g.append((group, t0, len(t)))


def populate(place_key, room_v, room_t, room_g, w_m, l_m, hour=13.0,
             arch="generic", seed=None, lod=ROOM_LOD, max_people=None):
    """Put the hour's population into one room. Returns (v, t, g, stats).

    `room_*` is the finished room, and it is an INPUT rather than something this
    module rebuilds: people are placed against the furniture that is actually
    there, which is the only way a person ends up on a chair rather than near
    one.
    """
    seed = seed or place_key
    v, t, g = [], [], []
    area = max(w_m * l_m, 1e-6)
    n = occupancy(place_key, area, hour, arch)
    if max_people is not None:
        n = min(n, max_people)
    hw, hl = w_m / 2.0, l_m / 2.0

    seats = _faces_in_band(room_v, room_t, room_g, *SEAT_BAND)
    desks = _faces_in_band(room_v, room_t, room_g, *DESK_BAND)
    seats.sort(key=lambda s: (-s[3], s[0], s[2]))
    desks.sort(key=lambda s: (-s[3], s[0], s[2]))

    stats = {"seated": 0, "standing": 0, "walking": 0, "wanted": n}
    cache = {}
    used = []

    def _clear(x, z, r=0.45):
        return all((x - ux) ** 2 + (z - uz) ** 2 > r * r for ux, uz in used)

    for i in range(n):
        sp = species_for(place_key, i, seed)
        key = (sp, lod)
        if key not in cache:
            try:
                cache[key] = _body.build(sp, f"{seed}-{i}", lod=lod)[:3]
            except Exception:                                   # noqa: BLE001
                cache[key] = _body.build("human", f"{seed}-{i}", lod=lod)[:3]
        mesh = cache[key]

        if i < len(seats):
            sx, sy, sz, _a = seats[i]
            if not _clear(sx, sz):
                continue
            # Seated: the body's origin drops to the seat pan, and it faces the
            # room rather than the wall it is against.
            _place_body(v, t, g, mesh, sx, sy - 0.42, sz,
                        math.atan2(-sx, -sz), "npc_seated")
            used.append((sx, sz))
            stats["seated"] += 1
            continue

        j = i - len(seats)
        if j < len(desks):
            dx, dy, dz, _a = desks[j]
            # Stand OFF the desk, on the side facing the room centre.
            ux = dx - STAND_OFF_M * (1.0 if dx > 0 else -1.0)
            uz = dz
            if not _clear(ux, uz):
                continue
            _place_body(v, t, g, mesh, ux, 0.0, uz,
                        math.atan2(dx - ux, dz - uz), "npc_standing")
            used.append((ux, uz))
            stats["standing"] += 1
            continue

        # Everyone else is in the room, in the circulation lane, spaced out.
        for _try in range(8):
            px = (_u(seed, "px", i, _try) - 0.5) * (2 * hw - 1.2)
            pz = (_u(seed, "pz", i, _try) - 0.5) * (2 * hl - 1.2)
            if _clear(px, pz, 0.7):
                _place_body(v, t, g, mesh, px, 0.0, pz,
                            _u(seed, "yaw", i) * math.tau, "npc_standing")
                used.append((px, pz))
                stats["walking"] += 1
                break
    stats["placed"] = stats["seated"] + stats["standing"] + stats["walking"]
    stats["triangles"] = len(t)
    return v, t, g, stats


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    import dressing as D
    dv, dt, dg, _dc = D.dress("t", 6.0, 9.0, 2.9, "office")

    v, t, g, s = populate("t", dv, dt, dg, 6.0, 9.0, hour=13.0, arch="office")
    check("an office at 1300 has people in it", s["placed"] > 0, str(s))
    check("...and some of them are sitting on the furniture",
          s["seated"] > 0, str(s))
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in g) == len(t))

    # THE HOUR IS REAL. A place with dead hours must empty out, or the schedule
    # this reads is decoration.
    z_day = occupancy("zocalo", 6444.0, 13.0)
    z_night = occupancy("zocalo", 6444.0, 5.0)
    check("the Zocalo is busy at 1300 and dead at 0500",
          z_day > z_night * 5, f"{z_day} vs {z_night}")

    # Determinism, same as every other generator here.
    v2, _t2, _g2, _s2 = populate("t", dv, dt, dg, 6.0, 9.0, hour=13.0,
                                 arch="office")
    check("the same room populates identically twice", v == v2)

    # Bodies must stand ON the deck, not in it or above it.
    ys = [q[1] for q in v]
    check("nobody is below the deck", min(ys) > -0.5, f"{min(ys):.2f}")
    check("nobody is floating at head height", min(ys) < 0.5, f"{min(ys):.2f}")

    # Species mix comes from the place, not from a default.
    sp = {species_for("zocalo", i, "s") for i in range(40)}
    check("the Zocalo is not all human", len(sp) > 1, str(sp))

    # A seat band that matched nothing would silently give a room of standers.
    seats = _faces_in_band(dv, dt, dg, *SEAT_BAND)
    check("the seat band finds seats in a dressed room", len(seats) > 0,
          f"{len(seats)} seat faces")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
