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

THEY ARE PEOPLE NOW, AND THAT IS THE DIFFERENCE BETWEEN A CROWD AND RESIDENTS.
Everything above was true and produced 278 bodies of which **not one had a name,
a job, a home, or anywhere to be at 14:00** -- which is a crowd, and CLAUDE.md's
scope asks for the opposite in as many words. `station/npc/resident.py` supplies
the person: the nine-field identicard record from the authority-1 prop, a home
and a job resolved out of `directory.PLACES` by function, and a destination for
every hour on Earth Mean Time.

Three consequences here, and each one was a defect before it was a feature:

  * **The body is built from the RESIDENT'S id, not from a slot number.** It was
    `f"{seed}-{i}"`, cached once per species, so every human in a room was the
    same mesh and the record said FEMALE while the mesh was whatever the slot
    hashed to. `resident()` reads `body.individual()` for SEX and PHYS CHR, so
    the two now come from one call and a card cannot describe somebody else.
  * **`who` in the actor record is the PERSON**, not the species string it was.
    `deck.py` copies that field verbatim into `<deck>_actors.json`, so identity
    reaches the engine with no change to any file this module does not own.
  * **A room with no `PlaceCrowd` entry is no longer all human.** 101 of the 118
    directory places have no entry of their own and every one of them was
    populated with 100% humans -- on a station whose own species mix is 62%.
    `SECTOR_MIX` derives the fallback from the `PlaceCrowd` entries that DO
    exist in the same sector, so the Alien Sector's neighbours inherit the Alien
    Sector's composition rather than Earth's.
"""
import hashlib
import math
import os
import sys
from functools import lru_cache as _lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "npc"))

import body as _body                                            # noqa: E402
import dressing as _dress                                       # noqa: E402
import resident as _res                                         # noqa: E402
import schedule as _sched                                       # noqa: E402

# THE STATION'S SEED. Every id this module hands to `resident` carries it, so
# one number changes who lives aboard -- different names, roles, homes, ages and
# cards -- while leaving the calibrated species mix and the crowd curve alone,
# because those are canon rather than a random draw. `_selftest` gates both
# directions: the same seed twice gives the same station, a different seed does
# not.
STATION_SEED = "b5"

# Seat and desk heights, in metres. A face inside SEAT_BAND is something you sit
# on; one inside DESK_BAND is something you stand at and work on. Taken from
# `rooms.PROPS`' own dimensions -- seat 0.45, bench 0.45, stool 0.62, table 0.74
# -- so the bands describe the furniture this station actually builds.
SEAT_BAND = (0.38, 0.66)
DESK_BAND = (0.68, 1.15)
# A body needs this much clear floor in front of a desk to stand at it.
STAND_OFF_M = 0.55
# Half the shoulder width of a standing body, from npc/body.py's own build.
BODY_R_M = 0.32
# Grid pitch for enumerating where a body can stand. Under the shoulder width,
# so a gap a person fits through is never missed between two samples.
SPOT_CELL_M = 0.30
# The group `dressing._chair` gives a seat pan. Seating is a kind of object,
# not a height band.
SEAT_GROUP = "dress_soft"
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
        return max(STAFFED_MINIMUM.get(arch, MIN_PRESENT),
                   int(round(peak * f)))
    rate = FALLBACK_PER_100M2.get(arch, 4.0)
    day = 0.25 + 0.75 * max(0.0, math.sin(math.pi * (hour - 6.0) / 14.0))
    floor = STAFFED_MINIMUM.get(arch, MIN_PRESENT)
    return max(floor, int(round(rate * area_m2 / 100.0 * day)))


# Peak occupancy per 100 m2 for places with no `PlaceCrowd` entry of their own.
# ANCHORED TO THE ONE MEASURED VALUE THIS PROJECT HAS: `schedule.PLACES` puts
# the Zocalo at 20.0 per 100 m2 at peak, which is the busiest public space on
# the station. Everything here is a fraction of that and says which:
#   a working office at 8.0 is 40% of a market -- a desk each and room to pass
#   a bar at 14.0 is 70%, which is what a full room feels like
#   a plant space at 3.0 is a shift of two or three in a big hall
# The first version of this table was a quarter of these values and produced 60
# people across 68 rooms with 25 of them EMPTY. A station of 250,000 with empty
# rooms at one in the afternoon is not quiet, it is abandoned, and that reads as
# a bug rather than as a mood.
FALLBACK_PER_100M2 = {
    "commerce": 15.0, "hospitality": 14.0, "transit": 12.0, "office": 8.0,
    "medical": 6.0, "research": 5.0, "industrial": 3.0, "store": 2.0,
    "detention": 3.0, "worship": 4.0, "generic": 4.0,
}

# Archetypes that are never unattended, and the minimum on duty. A medical bay,
# a cell block, a transit hub and a plant space all have somebody in them at
# 0400 -- that is what a staffed facility means -- while a store room and a
# chapel legitimately empty out. Without this the night station reads as
# evacuated instead of asleep.
STAFFED_MINIMUM = {
    "medical": 1, "detention": 1, "transit": 1, "industrial": 1, "office": 1,
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


# A SECTOR'S COMPOSITION, DERIVED FROM THE PLACES IN IT THAT ARE MEASURED.
# `schedule.PLACES` gives a human share and a ranked non-human list for 25
# places. `directory.PLACES` has 118, so **101 of them had no entry and were
# populated entirely with humans** -- Blue Sector's cargo bays, Green Sector's
# conference rooms, the Alien Sector's own corridors. On a station the same
# module says is 62% human with a fifteen-species mix, an all-human room is a
# bug that renders as a design decision.
#
# The fix reads the sector rather than inventing one: a place with no entry of
# its own takes the mean human share of the entries that ARE in its sector,
# weighted by their peak density so a 25-per-100m2 customs hall counts for more
# than a 2-per-100m2 suite, and the union of their dominant species ranked by
# how many of those places name each one. So Green Sector's unmeasured rooms
# inherit Green Sector's aliens and Blue Sector's inherit Blue Sector's crew,
# and nothing is typed in.
def _sector_mix():
    acc = {}
    for pc in _CROWD.values():
        if pc.sealed:
            continue
        w = max(pc.peak_per_100m2, 0.05)
        row = acc.setdefault(pc.sector, [0.0, 0.0, {}])
        dom = row[2]
        row[0] += pc.human_share * w
        row[1] += w
        for rank, sp in enumerate(pc.dominant):
            dom[sp] = dom.get(sp, 0.0) + w / (rank + 1.0)
    out = {}
    for sector, (hw, w, dom) in acc.items():
        if not sector or w <= 0:
            continue
        out[sector] = (hw / w,
                       tuple(k for k, _v in sorted(dom.items(),
                                                   key=lambda kv: (-kv[1], kv[0]))))
    return out


SECTOR_MIX = _sector_mix()
# The whole-station fallback, for a sector no measured place sits in. Derived
# from `schedule.STATION_COUNTS` rather than chosen, so it cannot drift from the
# mix the rest of the project apportions 250,000 people over.
_NONHUMAN = tuple(sp for sp, _c in sorted(_sched.STATION_COUNTS.items(),
                                          key=lambda kv: -kv[1])
                  if sp != "human")
STATION_FALLBACK = (_sched.STATION_MIX["human"], _NONHUMAN)


# `schedule.PLACES` and `directory.PLACES` were authored independently and eight
# of the 25 crowd entries name a place the directory holds under another key. So
# eight measured compositions -- including the customs halls, "the most
# species-diverse space on the station" -- were being thrown away and replaced
# by a sector average. Each row says which directory entry it is and why.
#
# THE MIX ONLY, DELIBERATELY. `occupancy()` still reads `_CROWD` directly and
# still falls back per archetype, because these entries carry peak densities and
# busy windows that would move headcounts in eight places at once -- the customs
# halls go from 4.0 to 25.0 per 100 m2 -- and this increment is about WHO is in a
# room, not how many. The measured numbers are in the session notes; applying
# them is the next increment and needs its own render.
CROWD_ALIAS = {
    # 00-MASTER.md 1.4: the customs board says exchange is "through Business
    # Center", and records that it "matches 'Business District' in the Red
    # Sector cross-section". The two names are the same place, at authority 1.
    "business_center": "business_district",
    # schedule's own place string is "Mess Hall, Quartermaster, Post Office".
    "mess_hall": "crew_country",
    "quartermaster": "crew_country",
    "post_office": "crew_country",
    # "Customs halls (x2, north and south)" is the directory's two halls.
    "customs_north": "customs_halls",
    "customs_south": "customs_halls",
    # "Fresh Air Restaurant" under a shorter key.
    "fresh_air": "fresh_air_restaurant",
    # "Fabrication furnaces, power, repair" -- schedule names the function,
    # the directory names the rooms.
    "fabrication": "industrial_grey",
    "maintenance": "industrial_grey",
    # FACTIONS.md 2.5's Dock Workers' Quarters is Blue Sector personnel
    # accommodation, which the directory holds as qtr_personnel.
    "qtr_personnel": "dock_workers_quarters",
}


def _mix_for(place_key):
    """(human share, ranked non-human species) for a place. Never all-human."""
    pc = _CROWD.get(place_key) or _CROWD.get(CROWD_ALIAS.get(place_key, ""))
    if pc is not None and (pc.dominant or not pc.sealed):
        return pc.human_share, (pc.dominant or _NONHUMAN)
    sector = _SECTOR_OF.get(place_key, "")
    share, dom = SECTOR_MIX.get(sector, STATION_FALLBACK)
    return share, (dom or _NONHUMAN)


def _sector_index():
    try:
        import directory as _D                                  # noqa: PLC0415
    except Exception:                                           # noqa: BLE001
        return {}
    return {p["key"]: p["sector"] for p in _D.PLACES}


_SECTOR_OF = _sector_index()


def species_for(place_key, i, seed):
    """Which species this person is, from the place's own mix."""
    human_share, dom = _mix_for(place_key)
    if _u(seed, "sp", i) < human_share:
        return "human"
    dom = dom or ("human",)
    return dom[int(_u(seed, "dom", i) * len(dom)) % len(dom)]


def _faces_in_band(v, t, g, lo_h, hi_h, min_area=0.12, only=None):
    """Upward faces whose height is in a band -- seats, or desks.

    Read off the geometry rather than tracked beside it, for the reason
    `dressing._surfaces_of` is: a kit that grows a new bench gets people sitting
    on it with nothing to keep in step.
    """
    out = []
    for _name, lo, hi in g:
        if only is not None and not _name.startswith(only):
            continue
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


def _place_body(v, t, g, mesh, x, y, z, yaw, group, actors=None, who=None):
    """One body, baked into the room's mesh at a position and a yaw.

    `actors` RECORDS WHAT WAS BAKED. A person is geometry in a merged mesh, so
    nothing downstream can tell which way they are facing by looking at them --
    and an inhabitant who is going to turn and look at the player has to be
    turned FROM somewhere. The generator knows the yaw it used; asking the
    geometry to give it back later is guessing at what was already known, which
    is how the door leaves ended up 0.16 m out of their own frame.
    """
    bv, bt, bg = mesh
    n0 = len(v)
    ca, sa = math.cos(yaw), math.sin(yaw)
    for (px, py, pz) in bv:
        v.append((x + px * ca - pz * sa, y + py, z + px * sa + pz * ca))
    t0 = len(t)
    t.extend((a + n0, b + n0, c + n0) for a, b, c in bt)
    # THE BODY'S OWN PART NAMES, CARRIED THROUGH. `npc/body.py` tags what it
    # builds -- `npc_skin_head`, `npc_skin_torso`, `npc_hair`, eight names on a
    # human -- and wrapping the lot in one group threw all of them away. That is
    # the same mistake `deck.py` made with the corridor, where one flat name
    # replaced fourteen real ones and cost 77% of a deck its materials: a body
    # with one group can only ever be ONE surface, so 278 people took whatever
    # single material matched and rendered as silhouettes.
    #
    # The person's own group is emitted too, as a PREFIX of the parts, because
    # `npc.gd` addresses a person and `rooms.is_solid` keys off `npc_`.
    g.append((group, t0, len(t)))
    for nm, lo, hi in bg:
        g.append((f"{group}_{nm}", t0 + lo, t0 + hi))
    if actors is not None:
        actors.append({"group": group, "who": who, "x": x, "y": y, "z": z,
                       "yaw": yaw, "pose": "seated" if "seated" in group
                       else "standing"})


@_lru_cache(maxsize=4096)
def _mesh_for(species, npc_id, lod):
    """This individual's body. Cached, because a room asks for it once.

    Per-INDIVIDUAL rather than per-species: `body.individual` varies stature,
    build, shoulder, head and sex per id, and caching one mesh per species threw
    all of that away -- 278 people were five meshes repeated. The cache key is
    the id, so the variation survives and a repeat still costs nothing.

    Falls back to a human body for a species `body.py` cannot build, rather than
    dropping the person: a missing inhabitant is invisible to every gate here
    and a wrong-species one is not.
    """
    try:
        return _body.build(species, npc_id, lod=lod)[:3]
    except Exception:                                           # noqa: BLE001
        return _body.build("human", npc_id, lod=lod)[:3]


def _who(res, hour, place_key):
    """The person, as the actor record carries them out to the engine.

    `who` USED TO BE THE SPECIES STRING, and `deck.py` copies this field
    verbatim into `<deck>_actors.json` -- so making it the person is how a name
    and a job reach the runtime without touching a file this module does not
    own. The fields are the identicard's, plus the two things the card cannot
    know: where they live and why they are standing here.
    """
    return {
        "id": res.npc_id,
        "name": res.name,
        "card_name": res.card_name,
        "species": res.species,
        "origin": res.origin,
        "atmos": f"{res.atmos_class}/{res.atmos_code}".rstrip("/"),
        "sex": res.sex,
        "dob": res.dob_card,
        "age": res.age,
        "psi": res.licensed_psi,
        "visa": res.visas,
        "role": res.role,
        "home": res.home,
        "job": res.job,
        # WHY THEY ARE HERE, which is the field that makes the rest mean
        # anything: "work" and "recreation" are different people standing in
        # the same room, and an NPC that can be asked will need to answer it.
        "doing": res.activity_at(hour).value,
        "at_post": _res.where_at(res, hour),
        # AND WHETHER THE CLOCK SENT THEM, said out loud. `occupancy` can ask
        # for more bodies than the schedule supplies -- a medlab wants 18 and
        # its roster has three medics on this watch -- so the rest are the
        # place's own regulars filling out the room. Recording which is which
        # is the difference between a compromise and a lie, and it is the field
        # a later increment will use to shrink the gap.
        "here_by": ("schedule" if _res.where_at(res, hour) == place_key
                    else "fill"),
    }


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
    # ONE GROUP PER PERSON. They all shared `npc_standing`, so the exporter
    # merged every inhabitant of a room into a single mesh and nothing could
    # address one of them -- the same reason the door leaves had to come out of
    # the corridor. A resident who reacts has to be a thing, not a region of a
    # thing.
    actors = []
    area = max(w_m * l_m, 1e-6)
    n = occupancy(place_key, area, hour, arch)
    if max_people is not None:
        n = min(n, max_people)
    hw, hl = w_m / 2.0, l_m / 2.0

    # SEATS ARE SEATING, not any face at seat height. A shelf tier sits at
    # 0.5 m and a crate lid at 0.6, and neither is something you sit on -- the
    # first version put a body on a crate lid and its own "no NPC inside a
    # solid fitting" check caught the pelvis inside the crate. `dress_soft` is
    # what `dressing._chair` emits for a seat pan and a back, so it is the
    # geometry's own word for "you can sit here".
    seats = _faces_in_band(room_v, room_t, room_g, *SEAT_BAND,
                           only=SEAT_GROUP)
    desks = _faces_in_band(room_v, room_t, room_g, *DESK_BAND)
    seats.sort(key=lambda s: (-s[3], s[0], s[2]))
    desks.sort(key=lambda s: (-s[3], s[0], s[2]))

    stats = {"seated": 0, "standing": 0, "walking": 0, "wanted": n}
    used = []

    # WHO IS IN THIS ROOM. The species mix is unchanged -- it is calibrated per
    # place and per sector and is canon, not a draw -- but each slot in it is
    # now filled by a PERSON: `resident.roster` hands back the place's own
    # regulars, ranked so that everybody the clock actually sends here comes
    # first. It is asked for the whole room in one call per species rather than
    # once per body, because the pool is a property of the place and re-casting
    # it per occupant is exactly the defect `crowd._pool_capacity` documents.
    slots = [species_for(place_key, i, seed) for i in range(n)]
    # `pool_id` already carries the place, so folding the default seed -- which
    # IS the place key -- back in gave ids reading `res:b5:docking_bays:
    # docking_bays:vree:60`. Only a caller-supplied seed adds anything.
    pool_seed = (STATION_SEED if seed == place_key
                 else f"{STATION_SEED}:{seed}")
    want = {}
    for sp in slots:
        want[sp] = want.get(sp, 0) + 1
    queue = {sp: list(_res.roster(place_key, hour, sp, k, pool_seed))
             for sp, k in want.items()}
    people = []
    for sp in slots:
        q = queue.get(sp)
        # A roster can only ever come back short if `resident.affiliates`
        # returned short, which it is written never to do; the guard is here
        # because a missing person would silently become a missing BODY and
        # this project has paid for a room that emptied without a gate noticing.
        people.append(q.pop(0) if q else _res.resident(
            _res.pool_id(place_key, sp, len(people), pool_seed), sp))
    stats["scheduled"] = sum(1 for r in people
                             if _res.where_at(r, hour) == place_key)
    stats["named"] = sum(1 for r in people if r.name)

    def _clear(x, z, r=0.45):
        return all((x - ux) ** 2 + (z - uz) ** 2 > r * r for ux, uz in used)

    # WHAT IS ALREADY STANDING THERE. `_clear` only ever checked against other
    # PEOPLE, so a body could be dropped inside a shelf run. Three things about
    # this list are deliberate and each was got wrong once:
    #
    #  * it is read from `room_*`, WHICH IS THE ROOM. `v, t, g` are the bodies
    #    being built and are empty here, so reading them gave an obstacle list
    #    that could never reject anything -- a guard that looked exactly like a
    #    working guard and was a no-op;
    #  * it is EXACTLY THE SET `rooms.py` ASSERTS ON, fittings and furniture but
    #    not the clutter standing on top of them. A mug on a desk is at chest
    #    height and is not something a person can be inside; counting it emptied
    #    a staffed medlab, because every clear spot in a working room is beside
    #    something with objects on it;
    #  * the invariant enforced here is the one checked over there, measured on
    #    the same boxes, because a guard computed against a different world than
    #    the one that ships is not a guard.
    import rooms as _R                                          # noqa: PLC0415
    _solid = [b for _n, b in _R._boxes(
        room_v, room_t, room_g,
        lambda n: n.startswith(("fix_", "dress_"))
        and not n.startswith("dress_clutter"))]

    def _free(x, z):
        """Is this point clear of the room's furniture, for a body's width?

        Ignores anything below the ankle or above the head, exactly as
        `rooms.walkable` does: a deck joint is stepped over and a soffit tee is
        walked under, and a person standing on one or beneath the other is fine.
        """
        for x0, y0, z0, x1, y1, z1 in _solid:
            if y1 <= 0.05 or y0 > 1.9:
                continue
            if (x0 - BODY_R_M < x < x1 + BODY_R_M
                    and z0 - BODY_R_M < z < z1 + BODY_R_M):
                return False
        return True

    def _free_spots():
        """Every place in this room a body can actually stand, off the floor.

        SAMPLE-AND-REJECT CANNOT FIND A SMALL TARGET. The wander placement drew
        random points and tested them, which works in an empty room and stops
        working the moment the room is full: once bays were sized to hold their
        furniture, **32 of 87 rooms came out with nobody in them** while
        `occupancy` said every one of them should have somebody at 1300. Adding
        tries did not help and neither did biasing the draw, because the problem
        is not where the darts land -- it is that a room with machinery down its
        spine has its clear floor in two narrow strips and a dart is a poor way
        to find a strip.

        So the free floor is ENUMERATED, the same way `rooms.walkable` finds a
        path: grid the room, keep the cells a body's width clear of everything
        solid, and pick from those. A room with one clear square metre gets its
        one occupant; a room with none gets nobody and means it.

        Ordered by hash so the choice is deterministic and scattered rather than
        sorted into a corner, and the reserved circulation lane comes first --
        that band is where a person standing in a room actually is.
        """
        nx = max(1, int(2 * hw / SPOT_CELL_M))
        nz = max(1, int(2 * hl / SPOT_CELL_M))
        lane = min(_dress.LANE_M / 2.0, max(0.35, hw - 0.9))
        out = []
        for i in range(nx):
            x = -hw + (i + 0.5) * (2 * hw / nx)
            if abs(x) + BODY_R_M > hw:
                continue
            for j in range(nz):
                z = -hl + (j + 0.5) * (2 * hl / nz)
                if abs(z) + BODY_R_M > hl:
                    continue
                if _free(x, z):
                    out.append((0 if abs(x) <= lane else 1,
                                _u(seed, "spot", i, j), x, z))
        out.sort()
        return [(x, z) for _lane, _h, x, z in out]

    spots = _free_spots()

    def _embedded(mark_v, mark_t):
        """Did the body just placed end up inside a fitting?

        CHECKED ON THE MESH THAT WAS EMITTED, not on the point it was asked for.
        Guarding the placement point was not enough: a standing figure's
        bounding box is not centred on its origin -- an arm reaches, a stance is
        offset -- so a body cleared at (x, z) can come to rest with its centre
        0.2 m away and inside a table. `rooms.py`'s assertion measures the
        body's box, so this measures the body's box; anything else is answering
        a different question from the one being asked.
        """
        pts = v[mark_v:]
        if not pts:
            return False
        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0
        cz = (min(p[2] for p in pts) + max(p[2] for p in pts)) / 2.0
        for x0, y0, z0, x1, y1, z1 in _solid:
            if y1 <= 0.8:
                continue
            if x0 + 0.10 < cx < x1 - 0.10 and z0 + 0.10 < cz < z1 - 0.10:
                del v[mark_v:]
                del t[mark_t:]
                while g and g[-1][1] >= mark_t:
                    g.pop()
                # And the record of them. A body rolled out of the geometry but
                # left in the actor list is an inhabitant the runtime would look
                # for and never find -- a ghost, which is worse than a missing
                # person because it looks like a loading bug.
                while actors and actors[-1]["group"] not in {
                        n for n, _l, _h in g}:
                    actors.pop()
                return True
        return False

    def _inside(x, z):
        """A whole body fits within the room, not just its centre point.

        The seat and desk placements skipped this and put a shoulder through
        the end wall of three cargo rooms -- a bench hard against the wall is a
        perfectly good bench, and the person sitting on it still has a body.
        rooms.py's footprint assertion caught it; the wander placement already
        allowed for width and these two did not.
        """
        return (abs(x) + BODY_R_M <= hw + 1e-9
                and abs(z) + BODY_R_M <= hl + 1e-9)

    for i in range(n):
        who = people[i]
        sp = who.species
        # THE BODY IS THIS PERSON'S BODY. It was `_body.build(sp, f"{seed}-{i}")`
        # cached once per (species, lod), so every human in a room was one mesh
        # repeated -- and worse, `resident` reads `body.individual(species,
        # npc_id)` for SEX and PHYS CHR, so the card described a body nobody was
        # standing in. Same id on both sides, and `resident._selftest` asserts
        # the two agree.
        mesh = _mesh_for(sp, who.npc_id, lod)
        who_rec = _who(who, hour, place_key)

        # A SEAT THAT DOES NOT WORK OUT MEANS THE PERSON STANDS, not that the
        # person ceases to exist. Every failure below used to be a bare
        # `continue`, which dropped that occupant entirely -- and once the rooms
        # were furnished properly there were seats everywhere, so most people
        # were ASSIGNED a seat, and any that did not take left a hole in the
        # population. 320 people were wanted across the station and 96 arrived,
        # with 32 rooms empty; the wander placement underneath was never even
        # reached. Assignment is a preference, not a filter.
        seated = False
        if i < len(seats):
            sx, sy, sz, _a = seats[i]
            if _clear(sx, sz) and _inside(sx, sz):
                # The body's origin drops to the seat pan, and it faces the
                # room rather than the wall it is against.
                _place_body(v, t, g, mesh, sx, sy - 0.42, sz,
                            math.atan2(-sx, -sz), f"npc_seated_{i}",
                            actors, who_rec)
                used.append((sx, sz))
                stats["seated"] += 1
                seated = True

        j = i - len(seats)
        if not seated and 0 <= j < len(desks):
            dx, dy, dz, _a = desks[j]
            # Stand OFF the desk, on the side facing the room centre.
            ux = dx - STAND_OFF_M * (1.0 if dx > 0 else -1.0)
            uz = dz
            if _clear(ux, uz) and _inside(ux, uz) and _free(ux, uz):
                _mv, _mt = len(v), len(t)
                _place_body(v, t, g, mesh, ux, 0.0, uz,
                            math.atan2(dx - ux, dz - uz), f"npc_standing_{i}",
                            actors, who_rec)
                if not _embedded(_mv, _mt):
                    used.append((ux, uz))
                    stats["standing"] += 1
                    seated = True

        if seated:
            continue

        # Everyone else stands somewhere the room actually has room for them.
        # BODY_R_M off every wall -- the first version inset by 0.6 m from a
        # half-span it had been handed as the OUTER extent, so a shoulder poked
        # through the wall and rooms.py's footprint assertion caught it on three
        # locations. A person has width; a placement point is not a person.
        for px, pz in spots:
            if not _clear(px, pz, 0.7):
                continue
            _mv, _mt = len(v), len(t)
            _place_body(v, t, g, mesh, px, 0.0, pz,
                        _u(seed, "yaw", i) * math.tau, f"npc_standing_{i}",
                        actors, who_rec)
            if _embedded(_mv, _mt):
                continue
            used.append((px, pz))
            stats["walking"] += 1
            break
    stats["placed"] = stats["seated"] + stats["standing"] + stats["walking"]
    stats["triangles"] = len(t)
    stats["actors"] = actors
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
    # COVERAGE, NOT A SUM -- a person's own group contains their body parts,
    # so the spans nest and legitimately sum to more than the mesh.
    _cov = set()
    for _n, _lo, _hi in g:
        _cov.update(range(_lo, _hi))
    check("every triangle is grouped",
          len(_cov) == len(t) and all(0 <= lo <= hi <= len(t)
                                      for _n, lo, hi in g),
          f"{len(_cov)} of {len(t)} covered")

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

    # ------------------------------------------------------------------
    # RESIDENTS, not a crowd
    # ------------------------------------------------------------------
    zv, zt, zg, zs = populate("zocalo", dv, dt, dg, 14.0, 22.0, hour=13.0,
                              arch="commerce")
    acts = zs["actors"]
    check("the Zocalo at 1300 is populated", len(acts) > 3, f"{len(acts)}")

    # EVERY BODY IS A PERSON. `who` was the species string; if it is still a
    # string then nothing downstream can ask an inhabitant anything.
    all_dicts = bool(acts) and all(isinstance(a["who"], dict) for a in acts)
    check("every actor carries a person record, not a species string",
          all_dicts)
    if not all_dicts:
        # Everything below reads the record, so it would raise rather than
        # report -- and a crashed suite hides whatever else regressed. Bail out
        # loudly instead.
        print(f"{ok}/{ok + fail} passed (aborted: `who` is not a record)")
        return 1
    need = {"id", "name", "species", "origin", "role", "home", "job", "doing"}
    check("...and the record carries an identity, a home and a job",
          all(need <= set(a["who"]) for a in acts),
          str(sorted(need & set(acts[0]["who"]))))
    # NEGATIVE CONTROL: the same test on the field set MINUS one must fail, or
    # it passes for any dict at all.
    check("...and the same test rejects a record missing a field",
          not all(need <= (set(a["who"]) - {"home"}) for a in acts))

    check("every inhabitant lives somewhere real",
          all(a["who"]["home"] for a in acts))
    named = [a for a in acts if a["who"]["name"]]
    check("most inhabitants have a name", len(named) > len(acts) * 0.5,
          f"{len(named)} of {len(acts)}")
    # NEGATIVE CONTROL for the naming rule: the eight species with no attested
    # personal name must NOT have been given one. If this ever passes trivially
    # -- because no such species turned up -- the detail says so.
    unnamed_sp = {a["who"]["species"] for a in acts if not a["who"]["name"]}
    check("...and nobody from a species with no attested name has one",
          unnamed_sp <= set(_sched.SPECIES_WITHOUT_NAMES),
          f"unnamed species present: {sorted(unnamed_sp) or 'none in this room'}")

    # THE CARD DESCRIBES THE BODY THAT WAS BUILT, and this is measured on the
    # MESH rather than on the record. The first version of this check compared
    # `who["sex"]` against `body.individual(species, who["id"]).sex` -- which
    # is the record against itself, and it went on passing with the body
    # deliberately rebuilt from the slot number instead of the person. A gate
    # that cannot fail on the defect it names is worse than none.
    #
    # `_place_body` translates by (x, y, z) and rotates about Y, so for a
    # STANDING body (y = 0) the world y of every vertex IS the body's own local
    # y. The multiset of those is a fingerprint of the individual: stature,
    # build, head size and sex all move it. Comparing it to a fresh build from
    # the person's id is exact and cannot be satisfied by a different person.
    spans = {nm: (lo, hi) for nm, lo, hi in zg}
    mism = []
    for a in acts:
        if a["pose"] != "standing" or a["group"] not in spans:
            continue
        lo, hi = spans[a["group"]]
        idx = {i for tri in zt[lo:hi] for i in tri}
        got = sorted(round(zv[i][1], 6) for i in idx)
        bv, _bt, _bg = _mesh_for(a["who"]["species"], a["who"]["id"], ROOM_LOD)
        want = sorted(round(q[1], 6) for q in bv)
        if got != want:
            mism.append(a["who"]["id"])
    check("a person's card and a person's MESH are the same individual",
          not mism, f"{len(mism)} of {len(acts)} bodies belong to somebody else")
    # NEGATIVE CONTROL: the same comparison against a DIFFERENT person's body
    # must fail, or the fingerprint is not a fingerprint.
    a0 = next(a for a in acts if a["pose"] == "standing")
    lo, hi = spans[a0["group"]]
    idx = {i for tri in zt[lo:hi] for i in tri}
    got = sorted(round(zv[i][1], 6) for i in idx)
    other = _mesh_for(a0["who"]["species"], a0["who"]["id"] + "-not-me",
                      ROOM_LOD)[0]
    check("...and the same comparison rejects somebody else's body",
          got != sorted(round(q[1], 6) for q in other))

    # The record's own SEX still has to agree with the individual, which is a
    # different claim from the one above and is the one the card renders.
    bad = [a for a in acts
           if a["who"]["species"] not in _res.HIVE_SPECIES
           and a["who"]["sex"] != {"f": "FEMALE", "m": "MALE", "none": ""}[
               _body.individual(a["who"]["species"], a["who"]["id"]).sex]]
    check("a person's card says the sex their body was built with",
          not bad, f"{len(bad)} of {len(acts)} disagree")

    # THE CLOCK MOVES PEOPLE, and it must move WHO and not only HOW MANY.
    def _ids(hour, seed=None):
        _v, _t, _g, st = populate("zocalo", dv, dt, dg, 14.0, 22.0, hour=hour,
                                  arch="commerce", seed=seed)
        return [a["who"]["id"] for a in st["actors"]], st

    at09, s09 = _ids(9.0)
    at22, s22 = _ids(22.0)
    check("the Zocalo holds different people at 09:00 and 22:00",
          set(at09) != set(at22),
          f"{len(set(at09) & set(at22))} of {len(at09)}/{len(at22)} in common")
    # NEGATIVE CONTROL: the same hour twice must give the same people, or the
    # difference above is noise and says nothing about the clock.
    check("...and the same hour twice gives the same people",
          _ids(9.0)[0] == at09)

    # And people are here because the schedule sent them, not only because a
    # density curve asked for bodies.
    check("a real share of the room is there because of the schedule",
          s09["scheduled"] >= 1 and s22["scheduled"] >= 1,
          f"09:00 {s09['scheduled']}/{s09['placed']}, "
          f"22:00 {s22['scheduled']}/{s22['placed']}")
    # NEGATIVE CONTROL: a place nobody lives or works in must score lower.
    _v, _t, _g, sw = populate("welded_shut", dv, dt, dg, 14.0, 22.0, hour=9.0,
                              arch="store")
    check("...and a sealed volume nobody is affiliated with does not",
          sw["scheduled"] == 0, f"welded_shut {sw['scheduled']}/{sw['placed']}")

    # DETERMINISM, BOTH DIRECTIONS. Same seed, same station; different seed,
    # different people -- and the same species mix either way, because the mix
    # is canon and not a draw.
    global STATION_SEED
    keep = STATION_SEED
    try:
        base_ids, base_st = _ids(13.0)
        base_sp = [a["who"]["species"] for a in base_st["actors"]]
        STATION_SEED = "b5"
        check("the same seed gives the same station", _ids(13.0)[0] == base_ids)
        STATION_SEED = "other-seed"
        alt_ids, alt_st = _ids(13.0)
        check("a different seed gives a different station",
              alt_ids != base_ids, f"{alt_ids[:1]} vs {base_ids[:1]}")
        check("...and does NOT move the calibrated species mix",
              [a["who"]["species"] for a in alt_st["actors"]] == base_sp)
    finally:
        STATION_SEED = keep

    # A ROOM WITH NO CROWD ENTRY IS NOT ALL HUMAN. 101 of the 118 places have
    # no entry of their own and every one of them used to be.
    cargo = {species_for("cargo_bays", i, "s") for i in range(60)}
    check("a Blue Sector cargo bay is not all human", len(cargo) > 1,
          str(sorted(cargo)))
    # NEGATIVE CONTROL: Yellow Sector maintenance is 95% human by measurement,
    # so it must come back nearly all human -- or the check above is just
    # "everything is mixed" and means nothing.
    yellow = [species_for("spinal_cargo", i, "s") for i in range(60)]
    check("...and Yellow Sector, measured at 0.95 human, still is",
          yellow.count("human") >= 50,
          f"{yellow.count('human')}/60 human")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _cast(hour=13.0, places=("zocalo", "security_central", "downbelow",
                             "medlab_one", "alien_sector")):
    """Print who is actually in a few rooms. The readable form of the gates."""
    import dressing as D                                        # noqa: PLC0415
    import rooms as R                                           # noqa: PLC0415
    for key in places:
        try:
            place = R._dir.by_key(key) if hasattr(R, "_dir") else None
        except Exception:                                       # noqa: BLE001
            place = None
        arch = "generic"
        if place is not None:
            arch = R.archetype(place)
        w, l = 14.0, 22.0
        dv, dt, dg, _c = D.dress(key, w, l, 3.2, arch)
        _v, _t, _g, st = populate(key, dv, dt, dg, w, l, hour=hour, arch=arch)
        print(f"\n{key} at {hour:04.1f} EMT -- {st['placed']} present, "
              f"{st['scheduled']} of them sent here by the clock")
        for a in st["actors"][:6]:
            w_ = a["who"]
            nm = w_["name"] or f"<{w_['species']}, no attested name>"
            print(f"  {nm:<26} {w_['species']:<9} {w_['origin']:<18} "
                  f"{w_['role']:<10} home {w_['home']:<20} "
                  f"job {w_['job'] or '-':<18} {w_['doing']}")


if __name__ == "__main__":
    if "--cast" in sys.argv:
        h = 13.0
        if "--hour" in sys.argv:
            h = float(sys.argv[sys.argv.index("--hour") + 1])
        _cast(hour=h)
        sys.exit(0)
    sys.exit(_selftest())
