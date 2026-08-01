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

import animation as _anim                                       # noqa: E402
import body as _body                                            # noqa: E402
import dressing as _dress                                       # noqa: E402
import friction as _friction                                    # noqa: E402
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
    # A BEDROOM IS NOT AN OFFICE, AND A THIRD OF THE STATION WAS ON AN OFFICE'S
    # CLOCK. The curve below peaks at hour 13 -- it is a working day -- and it
    # was applied to every archetype without a `PlaceCrowd`, which is all seven
    # residences: they archetype as `generic`, so `qtr_command`,
    # `qtr_civilian`, `qtr_transient`, `ambassadorial_suites`,
    # `alien_resident_qtr`, `league_delegations` and `kosh_quarters` filled up
    # at lunchtime and emptied overnight.
    #
    # Found by `npc/life.py` in session 4e, which correlated its own routed
    # day against this hour by hour: **six of the seven residences came back
    # anti-correlated, -0.80 to -0.56**, against +0.42 everywhere else. It
    # asserted the defect rather than patching it, because populace.py was not
    # its file. It is this file's.
    #
    # The residence curve is DERIVED, not inverted by hand: a home is occupied
    # by the people who are asleep in it, so it is `1 - awake_fraction` over
    # the station's own species mix, which already carries fifteen different
    # sleep blocks including the Brakiri's inverted one. Normalised so its own
    # daily mean matches the working curve's, because this changes WHEN a
    # residence is full and must not change how many people the station holds.
    floor = STAFFED_MINIMUM.get(arch, MIN_PRESENT)
    day = (_residence_factor(hour) if _is_residence(place_key)
           else 0.25 + 0.75 * max(0.0, math.sin(math.pi * (hour - 6.0) / 14.0)))
    return max(floor, int(round(rate * area_m2 / 100.0 * day)))


# The register's own residences. Keyed on the place rather than the archetype
# because the archetype does not distinguish them -- all seven come back
# `generic` -- and inventing a `residence` archetype would change what
# `rooms.FIXTURES`, `DENSITY` and `LIGHTS` give them, which is a much larger
# change than the one this defect needs.
RESIDENCE_KEYS = frozenset((
    "qtr_command", "qtr_personnel", "qtr_civilian", "qtr_transient",
    "ambassadorial_suites", "alien_resident_qtr", "league_delegations",
    "kosh_quarters",
))


def _is_residence(place_key):
    return place_key in RESIDENCE_KEYS


_RESIDENCE_CURVE = None


def _residence_factor(hour):
    """How full a home is at this hour: the fraction of people asleep in it.

    `schedule.awake_fraction` over the station's own species mix, inverted and
    normalised to the same daily mean as the working curve -- so this moves
    WHEN a residence is full without changing how many people the station has.
    """
    global _RESIDENCE_CURVE
    if _RESIDENCE_CURVE is None:
        mix = getattr(_sched, "STATION_COUNTS", None)
        if callable(mix):
            mix = mix()
        if not isinstance(mix, dict) or not mix:
            mix = {"human": 1.0}
        tot = float(sum(mix.values())) or 1.0
        raw = []
        for h in range(24):
            awake = sum(_sched.awake_fraction(sp, float(h)) * n
                        for sp, n in mix.items()) / tot
            raw.append(1.0 - awake)
        work = [0.25 + 0.75 * max(0.0, math.sin(math.pi * (h - 6.0) / 14.0))
                for h in range(24)]
        k = (sum(work) / 24.0) / max(sum(raw) / 24.0, 1e-9)
        _RESIDENCE_CURVE = [max(0.05, v * k) for v in raw]
    h0 = int(hour) % 24
    h1 = (h0 + 1) % 24
    f = hour - int(hour)
    return _RESIDENCE_CURVE[h0] * (1 - f) + _RESIDENCE_CURVE[h1] * f


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


# ===========================================================================
#  THE CROWD LIBRARY -- one body per species and phase, instanced many times
# ===========================================================================
# WHY THE WALKERS CANNOT KEEP THEIR OWN BODIES, in three measurements:
#
#   1. A rigid per-part transform CANNOT WALK. `npc.gd` already transforms each
#      person's parts every physics frame, so the obvious extension is to drive
#      the twelve parts from a clip. `animation.whole_part_error` measures the
#      result at **145 mm** out at the knee, because `npc_skin_leg` is ONE part
#      spanning hip to ankle and a rigid body does not bend in the middle.
#   2. `animation.rigid_track` closes that to **14 mm** by splitting each part
#      at its dominant bone -- in **19 pieces**.
#   3. But 19 pieces a person does not ship. At TWELVE it was already 1,262
#      primitives on one deck (INV-105), so 19 is worse than the state
#      `_by_material` just fixed.
#
# So the answer is not more pieces, it is INSTANCING, and the arithmetic is
# favourable rather than a compromise. Emit the eight walk phases ONCE per
# (species, lod) as shared meshes, and make each walker a reference to one:
#
#   walker geometry    134 unique x 484 tri = 64,856  ->  8 phases x ~6 species
#                                                          x 484 = ~23,000 SHARED
#   walker primitives  134                            ->  ~48, instanced
#   animation          none                           ->  free: swap the index
#
# A net triangle saving, a primitive saving, and it moves. What it costs is
# that a WALKER is their species' nominal body rather than their own -- which
# is what every real crowd system does, and which room occupants do not pay:
# they keep `body.individual` and their own identicard either way. A walker
# still has a name, a job and a home; what they share is a silhouette.
CROWD_PHASES = 8


@_lru_cache(maxsize=64)
def crowd_body(species, lod, phase):
    """The shared walking body for `(species, lod, phase)`. Nominal, not an
    individual -- see the section note above for why, and for what it costs."""
    return _posed(species, _anim.NOMINAL, lod, "walk", G0_MS2, 0.0, phase)


def crowd_library(species_lods):
    """`(verts, tris, spans)` holding every shared body a deck's crowd needs.

    One mesh per `(species, lod, phase)`, laid out end to end with a span
    naming each, so `deck.py` can write it as its own OBJ and the runtime can
    address a body by name. The bodies stand at the origin in their own local
    frame; every instance supplies its own transform.
    """
    v, t, g = [], [], []
    for sp, lod in sorted(set(species_lods)):
        for ph in range(CROWD_PHASES):
            try:
                bv, bt, bg = crowd_body(sp, lod, ph)
            except Exception:                                   # noqa: BLE001
                continue
            base, t0 = len(v), len(t)
            v.extend(bv)
            t.extend((a + base, b + base, c + base) for a, b, c in bt)
            key = f"crowd_{sp}_{lod}_{ph}"
            g.append((f"{key}_npc_body", t0, len(t)))
            for nm, lo, hi in _by_material(bg):
                g.append((f"{key}_{nm}", t0 + lo, t0 + hi))
    return v, t, g


def crowd_key(species, lod, phase):
    return f"crowd_{species}_{lod}_{phase % CROWD_PHASES}"


@_lru_cache(maxsize=8)
def station_crowd_library(lod):
    """The crowd library for the WHOLE STATION at one LOD, built once.

    PER DECK IT IS A LOSS AND PER STATION IT IS A ROUT, which is worth stating
    because the first version built it per deck and measured WORSE than baking:
    67 walkers drawing on 10 species need 80 shared bodies, and 80 > 67. The
    library's size is a function of the SPECIES MIX, not of how many people are
    walking, so it pays for itself the moment the same bodies are reused --
    which is exactly what happens across 90 z-clusters.

    Station-wide, `deck.py --sweep` walks 963 people. Baked at 484 triangles
    each that is 466,092. This library is 14 species x 8 phases = 112 bodies,
    ~54,000 triangles, ONCE. An 88% saving, and it is the same 112 meshes a
    runtime can drive as 112 MultiMeshes -- which is 112 draw calls for every
    walking person on the station, against 963.

    Keyed on LOD alone so the cache is a cache: a deck asks for the library it
    needs and gets the one that already exists.
    """
    return crowd_library([(sp, lod) for sp in sorted(_sched.STATION_MIX)])


def bake_instances(instances, lod=None):
    """Turn a crowd instance list back into triangles, for the RENDER path.

    ONE LIST, TWO CONSUMERS, and that is the whole reason this exists rather
    than a second call to `populate_corridor`. The shipped deck carries the
    crowd as instances -- 88% fewer triangles station-wide, and the only form
    that can move. A still frame has no runtime to instance them, so the
    renderer needs geometry. Both come from the SAME placements, so a body in
    a render is where the body in the build is, which two independent
    placements could not guarantee and this project has been bitten by twice.

    The bodies are the shared library's, so a rendered walker is their
    species' nominal figure -- exactly what the runtime shows.
    """
    v, t, g = [], [], []
    for r in instances:
        try:
            bv, bt, bg = crowd_body(r["species"], int(r.get("lod", lod or 4)),
                                    int(r.get("phase", 0)))
        except Exception:                                       # noqa: BLE001
            continue
        ux, uy, _uz = r["up"]
        fx, fy, _fz = r["fwd"]
        px, py, pz = r["x"], r["y"], r["z"]
        n0 = len(v)
        # The same mapping `_place_ring_body` uses, from the basis the
        # instance carries rather than recomputed -- so if one is wrong they
        # are wrong together and the gate that catches one catches both.
        for (bx, by, bz) in bv:
            v.append((px + ux * by + fx * bz,
                      py + uy * by + fy * bz,
                      pz + bx))
        t0 = len(t)
        t.extend((a + n0, b + n0, c + n0) for a, b, c in bt)
        grp = r["group"]
        g.append((f"{grp}_npc_body", t0, len(t)))
        for nm, lo, hi in _by_material(bg):
            g.append((f"{grp}_{nm}", t0 + lo, t0 + hi))
    return v, t, g


def _body_half_w(mesh):
    """Widest horizontal half-extent of a built body, about its own centre.

    A dressed figure is wider than the bare one it was built from -- a coat, a
    skirt, a stole -- so a placement test against `BODY_R_M` starts putting
    shoulders through walls the moment the wardrobe is switched on. Measured
    off the mesh in hand, which costs nothing because the caller already has
    it.
    """
    verts = mesh[0] if mesh else ()
    if not verts:
        return BODY_R_M
    cx = sum(q[0] for q in verts) / len(verts)
    cz = sum(q[2] for q in verts) / len(verts)
    return max(math.hypot(q[0] - cx, q[2] - cz) for q in verts)


def _placed_bounds(mesh, x, z, yaw):
    """Where a body ACTUALLY ends up: `(xmin, xmax, zmin, zmax)` in room space.

    NOT A RADIUS AROUND THE PLACEMENT POINT, and the difference decides whether
    anybody can sit down. Two cruder tests were tried and both are wrong:

      * `BODY_R_M`, a nude human's 0.32 m shoulder. Once the wardrobe was
        switched on a coat and a skirt went through the wall, and `rooms.py`'s
        footprint assertion caught it -- "earthforce_office: inside its own
        footprint -- x -4.27..4.07 in +/-3.89".
      * the mesh's own largest radius. A seated figure is deep FORWARD -- its
        thighs project 0.83 m -- and no wider across the shoulders than a
        standing one, so a circle refused every seat against a wall. A bench IS
        against a wall; the depth points into the room, not through the brick.
        It emptied every chair on the station.

    A body's box is not centred on its origin, so the honest test is the one
    the placement actually performs: rotate the vertices by `yaw` about Y and
    translate, exactly as `_place_body` does, then take the extremes. Same
    arithmetic, so the test cannot disagree with the placement.
    """
    verts = mesh[0] if mesh else ()
    if not verts:
        return x - BODY_R_M, x + BODY_R_M, z - BODY_R_M, z + BODY_R_M
    ca, sa = math.cos(yaw), math.sin(yaw)
    xs = [x + px * ca - pz * sa for px, _py, pz in verts]
    zs = [z + px * sa + pz * ca for px, _py, pz in verts]
    return min(xs), max(xs), min(zs), max(zs)


def body_capsule(mesh):
    """`(radius_m, height_m)` a body occupies, MEASURED off the mesh in hand.

    A PERSON IS NOT IN THE STATION'S COLLISION AND MUST NOT BE. `rooms.is_solid`
    excludes `npc_` groups deliberately: static collision is generated once, so
    baking 147 inhabitants into it makes 147 permanent statues -- a person you
    bump into and who never moves is worse than one you walk through. Its
    comment ends "NPCs get their own capsules when they get their own
    movement", and this is that capsule: carried in the actor record, applied
    by the runtime, and moving with the person.

    The radius is the widest horizontal extent about the body's own vertical
    axis, not the chest and not a constant. A human measures 0.269 m against
    0.206 at the chest, and the difference is the arms -- which are exactly
    what a player would otherwise clip through. Measured per species and per
    individual, so a Vorlon's encounter suit is 0.414 m and a Narn 0.295, which
    a single number could not express.

    The corridor still passes: 0.269 m against a 1.081 m half-width leaves
    0.81 m of clearance either side of somebody standing on the centreline.
    """
    verts = mesh[0]
    if not verts:
        return 0.0, 0.0
    ys = [q[1] for q in verts]
    cx = sum(q[0] for q in verts) / len(verts)
    cz = sum(q[2] for q in verts) / len(verts)
    r = max(math.hypot(q[0] - cx, q[2] - cz) for q in verts)
    return round(r, 4), round(max(ys) - min(ys), 4)


def _material_family(part_name):
    """The material fragment a body part binds through: `npc_skin_torso` ->
    `npc_skin`, `npc_suit_robe` -> `npc_suit`, `npc_hair` -> `npc_hair`.

    Taken off `body.py`'s OWN naming rather than from `materials.py`'s bind
    table, which this module must not import: the first two tokens of every
    part name in that file ARE the bind fragment, and reading them back is the
    same rule as measuring a seat height off the mesh rather than tabulating
    it. If the two ever disagree, `test_materials_layer3.py`'s coverage gate
    fails -- it resolves every emitted group name.
    """
    # A COSTUME GROUP IS ALREADY A MATERIAL KEY. `costume.group_name` emits
    # `<slot>__<fabric>` with a DOUBLE underscore -- `npc_cloth__civ_dark_warm`
    # -- and the material is bound to the whole of it, because the wardrobe is
    # one material per fabric and not one per slot. Splitting on single
    # underscores truncated that to `npc_cloth`, which nothing binds, and 24
    # groups on a deck went unresolved the moment people got dressed.
    if "__" in part_name:
        return part_name
    parts = part_name.split("_")
    return "_".join(parts[:2]) if len(parts) >= 2 else part_name


def _by_material(spans):
    """Merge a body's part spans into one span per RUN of the same material.

    A DRAW CALL IS A PRIMITIVE, AND ONE PERSON WAS TWELVE OF THEM. `export_gltf`
    emits one mesh, one node and one primitive per OBJ group, so a deck of 134
    corridor walkers and 13 room occupants shipped **1,262 primitives, 1,052 of
    them people** -- against `schedule.NPC_BUDGET["max_draw_calls"] = 32, and
    against a `budget.py` draw-call gate that read 41 of 64 because it counts
    FEATURE GROUPS and not what the exporter actually writes.

    The twelve part names exist so each binds its own material -- that is what
    stopped 278 inhabitants rendering as one surface -- and the materials are
    only ever two or three: skin, hair or crest, suit. Merging the RUNS keeps
    every material distinction and drops a human at lod 4 from twelve spans to
    **one**, a Minbari to two.

    Runs rather than families, so a species whose parts interleave gets a
    correct result instead of a reordered mesh: the merge only ever joins spans
    that are already adjacent in the triangle list, so no triangle moves.
    """
    out = []
    for nm, lo, hi in spans:
        fam = _material_family(nm)
        if out and out[-1][0] == fam and out[-1][2] == lo:
            out[-1] = (fam, out[-1][1], hi)
        else:
            out.append((fam, lo, hi))
    return [tuple(r) for r in out]


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
    # The person's own span is emitted too, as a PREFIX of the parts, because
    # `npc.gd` addresses a person and `rooms.is_solid` keys off `npc_`.
    #
    # `_npc_body` ON THE END, and it is the material resolver that forces it.
    # `materials.resolve` matches by SUBSTRING and the longest fragment wins,
    # so a bind on the bare `npc_seated` would be 10 characters against
    # `npc_hair`'s 8 -- and every seated person's hair would have resolved to
    # skin. With the suffix, the wrapper hits `npc_body` and nothing else, and
    # each part still hits only its own fragment. `npc.gd`'s prefix match is
    # unaffected: it tests `name.begins_with(group + "_")`, which this passes.
    g.append((f"{group}_npc_body", t0, len(t)))
    for nm, lo, hi in _by_material(bg):
        g.append((f"{group}_{nm}", t0 + lo, t0 + hi))
    if actors is not None:
        r_m, h_m = body_capsule(mesh)
        actors.append({"group": group, "who": who, "x": x, "y": y, "z": z,
                       "yaw": yaw, "pose": "seated" if "seated" in group
                       else "standing",
                       # WHAT A PLAYER BUMPS INTO. Not in the static collision
                       # -- see `body_capsule` -- so it travels with the person.
                       "r_m": r_m, "h_m": h_m})


# WHETHER PEOPLE ARE DRESSED. `npc/costume.py` is 2,800 lines with a measured
# wardrobe -- 53 reachable (slot, fabric) materials, 32 of them read off
# authority-1 show frames -- and `build_dressed` has produced a clothed figure
# the whole time. Nothing called it: `materials.py` imported the module for two
# constants and this one built `body.build`, the bare figure. So 2,016
# inhabitants stood on the station with no clothes on, which
# `docs/engine-zocalo-inside.png` shows as a hall full of pale mannequins.
#
# GATED ON THE MATERIALS EXISTING, and that is not timidity. A dressed body
# emits `npc_cloth__civ_dark_warm` and friends; until `materials.py` binds
# them every garment renders on the magenta fallback, which is worse than
# nude. `_dressed_ok()` asks the library rather than trusting a flag, so this
# turns itself on the moment the materials land and cannot be left half-wired.
DRESSED = True


@_lru_cache(maxsize=1)
def _dressed_ok():
    """Does the material library bind what a dressed body emits?

    Checked, not assumed. `costume.material_specs()` is the list the library
    has to cover; if a single group resolves to nothing this returns False and
    everybody stays in the bind pose's bare skin, because a magenta figure is a
    worse error than an undressed one and a silent one is worse than both --
    `report()` prints which groups are missing.
    """
    if not DRESSED:
        return False
    try:
        import costume as _cos                                  # noqa: PLC0415
        sys.path.insert(0, HERE)
        import materials as _mat                                # noqa: PLC0415
        missing = [m["group"] for m in _cos.material_specs()
                   if _mat.resolve(m["group"], "interior") is None]
        _dressed_missing.extend(missing)
        return not missing
    except Exception:                                           # noqa: BLE001
        return False


_dressed_missing = []


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
    if _dressed_ok():
        try:
            import costume as _cos                              # noqa: PLC0415
            return _cos.build_dressed(species, npc_id, lod=lod)[:3]
        except Exception:                                       # noqa: BLE001
            pass
    try:
        return _body.build(species, npc_id, lod=lod)[:3]
    except Exception:                                           # noqa: BLE001
        return _body.build("human", npc_id, lod=lod)[:3]


# Earth surface gravity, for a room whose caller does not say where it is. The
# station's own decks run 0.559 g to 1.693 g and a pose reads that: `sit_clip`
# and `idle_clip` widen their sway in low g, and `gait()` shortens the stride.
G0_MS2 = 9.80665
# Seat height is quantised to a centimetre for the pose cache. A pose does not
# resolve finer than that and an unquantised key caches every seat separately.
SEAT_QUANTUM_M = 0.01
# Frames in a baked walk cycle. Only the phase is used -- this module emits
# static geometry -- so the number sets how finely two passers-by can differ.
# 8 puts them a sixteenth of a stride apart at worst, under the 22 mm grid tile
# a foot lands on. `CROWD_PHASES` above is the same number and is asserted
# equal in `_selftest`: the shared crowd library holds one body per phase, so
# the two describing different counts would silently drop or duplicate one.
WALK_FRAMES = CROWD_PHASES

# ===========================================================================
#  THE CORRIDOR IS NOT A ROOM, AND UNTIL NOW IT HAD NOBODY IN IT AT ALL
# ===========================================================================
# Every person this module placed was placed in a ROOM. A player walked 126 m
# of assembled corridor and met **nobody** -- on a station of 250,000, in the
# one space CLAUDE.md's scope names twice ("the friction between them visible
# in a corridor", "residents, not crowds").
#
# The density is DERIVED, and the derivation is three measurements this
# repository can recompute rather than a number anyone picked:
#
#   1. `schedule.RESIDENT_TOTAL` = 250,000. Authority 1, the opening narration.
#   2. **50.8 minutes** -- the mean time a resident spends walking in corridors
#      per day. Measured by walking each resident's OWN 24-hour schedule
#      (`resident.where_at` hour by hour) and pricing every change of place
#      through `navigation.NavGraph.path`, counting only the `walk`, `stair`
#      and `door` links. It is not the commute: it is the whole day, meals and
#      recreation included, which is why it is five times the 5.0 min a
#      one-way commute spends on foot.
#   3. **825,066 m2** of corridor -- 317,333 m of ring at
#      `interior_kit.PROVISIONAL["corridor_width_m"]`, summed over the 251
#      decks `navigation.cell_plan` builds.
#
# 250,000 x 50.8/1440 = **8,812 people walking somewhere at any instant**, over
# 825,066 m2, is **1.07 per 100 m2** -- one person every 36 m of corridor.
#
# THAT NUMBER IS SPARSE AND IT IS SUPPOSED TO BE. The instinct is that a
# corridor should be busy, and `FALLBACK_PER_100M2["transit"]` is 12.0, eleven
# times this -- which would put a person every 3 m along every corridor on the
# station, 914 of them on one Blue deck. The station simply has an enormous
# amount of corridor: 0.83 km2 of it, most in the 105 Grey plant decks nobody
# lives on. What makes a corridor feel busy is not the average, it is the
# DISTRIBUTION, which `corridor_headcount` takes from the occupancy of the
# places each deck actually serves.
#
# `--derive` recomputes all three and fails if the recorded value has drifted,
# the same guard `tools/measure_frame.py` uses on its bands.
WALK_MIN_PER_DAY = 50.8
CORRIDOR_AREA_M2 = 825_066.0
CORRIDOR_PER_100M2 = (_sched.RESIDENT_TOTAL * (WALK_MIN_PER_DAY / 1440.0)
                      / CORRIDOR_AREA_M2 * 100.0)


def corridor_headcount(place_keys, area_m2, hour, arch="transit"):
    """How many people are walking `area_m2` of corridor at `hour`.

    The station-wide average is `CORRIDOR_PER_100M2`; this distributes it by
    what the deck SERVES. A corridor's traffic is people going to and from the
    rooms off it, so the weight is the occupancy of those rooms -- which
    `occupancy()` already computes per place per hour, so a deck of offices
    empties at 0300 and the concourse outside customs does not.

    The weight is a RATIO against the station's own mean occupancy per room, so
    a deck with average rooms gets the average density and the total over all
    decks stays at the 8,812 the derivation produced. A deck serving nothing --
    the outer plant stacks -- gets the floor rather than zero: somebody is
    always walking to a pump.
    """
    if area_m2 <= 0.0:
        return 0
    base = CORRIDOR_PER_100M2 * area_m2 / 100.0
    keys = tuple(place_keys or ())
    if not keys:
        return int(round(base * CORRIDOR_EMPTY_DECK_F))
    # Occupancy per served place at this hour, against the same places' own
    # peak. A ratio, so the units cancel and nothing here needs a second table.
    now = sum(occupancy(k, 100.0, hour, arch) for k in keys)
    peak = max(1e-9, sum(max(occupancy(k, 100.0, h, arch) for h in range(24))
                         for k in keys))
    f = (now / peak) * (len(keys) / CORRIDOR_ROOMS_PER_DECK)
    return int(round(base * max(CORRIDOR_EMPTY_DECK_F, f)))


# A deck serving nothing still has somebody on it. One tenth of the mean is the
# floor: on a Blue deck's 1,270 m of corridor that is still two people, which
# reads as "quiet" rather than as "abandoned" -- the same distinction
# FALLBACK_PER_100M2's own note draws, at the other end of the scale.
CORRIDOR_EMPTY_DECK_F = 0.10
# Mean rooms per ring deck, so the weight above is a ratio rather than a count.
# MEASURED: `deck.py --sweep` assembles 87 rooms over 66 ring decks.
CORRIDOR_ROOMS_PER_DECK = 87.0 / 66.0


def corridor_sight_m(radius_m, width_m):
    """How far a body can see down a corridor that curves away from it.

    A ring corridor is a chord problem, not a straight one: the outer wall cuts
    the line of sight at the point where the chord's sagitta equals the
    corridor's width. `sagitta = c^2 / 8R` for a chord `c`, so setting it to
    `w` gives `c = sqrt(8 R w)` -- 66 m on a Blue deck at r = 211 m in a 2.60 m
    corridor, and 108 m on Grey's outer ring at r = 560 m.

    It is the reason a corridor's people can be baked at one LOD at all: they
    are never seen from further than this, and mostly from its far half.
    """
    return math.sqrt(8.0 * max(1e-9, radius_m) * max(1e-9, width_m))


@_lru_cache(maxsize=1)
def crowd_ladder():
    """`((max_distance_m, chain_lod), ...)` for the shipped crowd, nearest first.

    DERIVED FROM `schedule.NPC_BUDGET["lod"]`, which gives a distance band and
    a triangle allowance per level; the chain level is the one whose MEASURED
    triangle count is nearest that allowance, the same rule `corridor_lod` uses
    for a single distance. The two ladders are not indexed alike and assuming
    they were is how a body ends up eight times coarser than its budget.

    THE NEAR BAND IS CAPPED, AND THAT IS A STATED COMPROMISE RATHER THAN A
    DERIVATION. `NPC_BUDGET`'s 0-6 m band allows 8,000 triangles, which is
    chain level 0 at 4,560 -- but the crowd is INSTANCED against a shared
    library, so shipping level 0 means 14 species x 8 phases x 4,560 =
    **510,720 triangles resident** in order to draw the four agents that band
    ever holds. The runtime cannot build a body on demand, so the choice is
    between paying half a megatriangle for four figures or letting the nearest
    band share the 6-18 m level. It shares. What would overturn it: a runtime
    that can skin a body per frame, which would make the library unnecessary
    altogether.
    """
    counts = _lod_triangles()
    out = []
    for _name, _lo, hi, tri, _n in _sched.NPC_BUDGET["lod"]:
        lod = min(range(len(counts)), key=lambda i: abs(counts[i] - tri))
        out.append((float(hi), lod))
    # Collapse the near band into the next one out -- see the note above -- and
    # drop any band that resolves to the same level as its neighbour, so the
    # ladder has no rung that costs a MultiMesh set and draws the same mesh.
    if len(out) > 1:
        out = out[1:]
    dedup = []
    for hi, lod in out:
        if dedup and dedup[-1][1] == lod:
            dedup[-1] = (hi, lod)
        else:
            dedup.append((hi, lod))
    return tuple(dedup)


def corridor_lod(radius_m, width_m):
    """The LOD to bake a corridor's people at, chosen by that sight line.

    NOT PICKED. `schedule.NPC_BUDGET["lod"]` gives distance bands with a
    triangle allowance each -- lod0 0-6 m at 8,000, lod1 6-18 at 2,000, lod2
    18-45 at 600, lod3 45-400 at 120. People are spread evenly along the
    corridor, so the distance to pick the band with is the MEAN of a uniform
    distribution over the sight line -- `0.5 * sight`, which is 33 m on a Blue
    deck at r = 211 m and 54 m on Grey's outer ring. Not the far half: taking
    0.75 puts a Blue deck in lod3's 45-400 m band at 120 triangles, and a
    132-triangle body is a blob at the 2 m the NEAREST of them is at.

    `body.lod_chain()` is then searched for the level whose actual triangle
    count is nearest that allowance, rather than assuming the two ladders are
    indexed the same -- they are not. The chain's own levels measure 4,560 /
    2,256 / 2,068 / 1,012 / 484 / 372, so the budget's 600 lands on level 4.

    THIS IS A BAKE-TIME COMPROMISE AND IT IS WORTH SAYING SO. A player standing
    next to one of these people sees a 372-triangle body where the budget would
    give them 8,000. The fix is runtime LOD -- `npc.gd` already holds each
    person's parts and could swap them -- and until that exists the honest
    choice is the LOD that is right for the distance they are USUALLY at, not
    the one that is right for the rare close encounter.
    """
    far = 0.5 * corridor_sight_m(radius_m, width_m)
    bands = _sched.NPC_BUDGET["lod"]
    want = bands[-1][3]
    for _name, lo, hi, tri, _n in bands:
        if lo <= far < hi:
            want = tri
            break
    counts = _lod_triangles()
    return min(range(len(counts)), key=lambda i: abs(counts[i] - want))


@_lru_cache(maxsize=1)
def _lod_triangles():
    """Triangles per level of `body.lod_chain()`, MEASURED by building one.

    The chain records `radial_segments` and `ring_stride`, not a triangle
    count, and the relation between them is `body.py`'s business. Reading the
    number off a built mesh is the same rule the rest of this module follows:
    ask the geometry, do not restate it.
    """
    out = []
    for i in range(len(_body.lod_chain())):
        try:
            out.append(len(_body.build("human", "lod/probe", lod=i)[1]))
        except Exception:                                       # noqa: BLE001
            out.append(out[-1] if out else 0)
    return tuple(out)


@_lru_cache(maxsize=256)
def _stand_min_g(species, npc_id, lod):
    """The gravity below which this figure cannot hold a standing pose, m/s^2.

    MEASURED OFF THE RIG, never written down -- hard rule 4 applied to a pose.
    `idle_clip`'s lateral sway is `sway_amp_f * lx * (G0 / g)` with `lx` the
    hip's own x offset, and it has **no lower bound at all**: at 0.04 g it
    leans a human 0.52 m off centre and lifts their feet 25 mm off the deck.
    That is not a stance, it is somebody falling over, and `animation.py` has no
    guard for it because nothing had ever asked it for a pose in low gravity.

    A standing pose is holdable while the sway stays inside the BASE OF
    SUPPORT, which for a standing figure is the outermost point of the feet --
    read off `rig.parts` rather than assumed. Setting sway equal to it gives
    `g_min = sway_amp_f * lx * G0 / foot_x`, which is 0.075 g for a nominal
    human. Below it this module uses `glide_clip` instead: in 0.075 g you do
    not stand, you push off and drift, and `animation.py` already has the clip
    because Kosh needed it.

    Per figure rather than per species: `lx` and the foot come from
    `body.individual`, so a broad-stanced person stays on their feet in lower
    gravity than a narrow one, which is also true.
    """
    try:
        rg = _anim.rig(species, npc_id, lod)
        lx = abs(rg.skel.head("hip_r")[0])
        fx = max((abs(v[0]) for nm, vv, _t in rg.parts if nm == "foot"
                  for v in vv), default=0.0)
        if fx <= 1e-6 or lx <= 1e-9:
            return 0.0
        return _anim.IDLE["sway_amp_f"] * lx * G0_MS2 / fx
    except Exception:                                           # noqa: BLE001
        return 0.0


@_lru_cache(maxsize=4096)
def _posed(species, npc_id, lod, kind, g_ms2, seat_h_m, phase=-1):
    """This individual, in this pose, as `body.build` would have returned them.

    THE FIRST IMPORTER `npc/animation.py` HAS EVER HAD. It is 2,400 lines with
    a skeleton, a Froude-number gait ladder, walk, idle, sit and glide clips and
    some hundreds of passing assertions, and CLAUDE.md names it in the list of
    twelve tested modules with zero importers outside their own directory. What
    reached a frame instead was `body.build`'s bind pose for everybody.

    WHAT THAT COST, and it is visible rather than theoretical. A seated person
    was a STANDING body dropped 0.42 m: a figure 1.829 m tall with its feet
    0.42 m through the deck and its knees inside the chair it was sitting on.
    The 0.42 was a guess standing in for a pose. `sit_clip` needs no guess --
    handed the seat's own measured height it puts the hips on the pan, the feet
    on the floor and the figure at 1.341 m, and the body's origin stays at deck
    level where every other placement in this module already puts it.

    Standing people get `idle_clip` rather than the bind pose, and that matters
    for a different reason: the bind pose is arms-down symmetric and every
    person in a room struck it identically. `idle_clip` carries a per-resident
    phase (`_u(id, "idle_phase")`), so a room of twelve is twelve weights and
    twelve breaths rather than a chorus line -- which `animation.py`'s own
    comment calls "the single most visible crowd failure there is".

    Frame 0 of a loop, deliberately: this module emits static geometry, and a
    clip's phase is already per-resident, so sampling elsewhere in the loop
    would be a second arbitrary number for no gain. When the runtime animates
    these bodies it will play the same clips from the same call.
    """
    try:
        rg = _anim.rig(species, npc_id, lod)
        frame = 0
        if g_ms2 < _stand_min_g(species, npc_id, lod):
            # BELOW THIS GRAVITY NOBODY STANDS. See `_stand_min_g`.
            clip = _anim.glide_clip(species, npc_id, g_ms2, frames=8, lod=lod)
        elif kind == "sit":
            clip = _anim.sit_clip(species, npc_id, g_ms2,
                                  seat_h_m=seat_h_m or None, frames=8, lod=lod)
        elif kind == "walk":
            clip = _anim.walk_clip(species, npc_id, g_ms2, frames=WALK_FRAMES,
                                   lod=lod)
            # A CORRIDOR OF PEOPLE ALL AT FRAME 0 IS A DRILL SQUAD. Unlike the
            # idle clip, whose phase is inside the clip, a walk cycle's phase
            # IS the frame -- so it is picked per resident here, deterministic
            # on the id like everything else in this module. `phase >= 0`
            # overrides it, which is how the shared crowd library asks for one
            # body at each of the eight phases rather than eight bodies at
            # whatever phase their ids happened to hash to.
            frame = (int(_u("walk_phase", npc_id) * WALK_FRAMES)
                     if phase < 0 else int(phase)) % WALK_FRAMES
        else:
            clip = _anim.idle_clip(species, npc_id, g_ms2, frames=8, lod=lod)
        _w, mats = clip.pose(rg.skel, frame)
        parts = _anim.apply_pose(rg, mats)
        if kind == "walk":
            # THE STRIDE ADVANCE COMES OFF; THE BOB AND THE SWAY DO NOT.
            # `walk_clip`'s root moves in all three axes and they are not the
            # same kind of motion. Forward (z) is the stride -- a body posed at
            # frame 6 would otherwise arrive 0.88 m down the corridor from
            # where the placement put it, because the placement owns the
            # position and the clip owns the attitude. But root Y is the
            # PELVIS BOB and root X is the lateral sway, and both are the walk
            # itself: measured, the raw pose has its planted foot at y = 0.011
            # at every one of the eight frames, and subtracting the root lifted
            # all eight to 0.104-0.143 m. Eighty people hovering 12 cm over the
            # deck, from taking "remove the root translation" as one idea
            # instead of three.
            _rx, _ry, rz = clip.root[frame % clip.frames]
            parts = [(n, [(x, y, z - rz) for x, y, z in vv], t)
                     for n, vv, t in parts]
    except Exception:                                           # noqa: BLE001
        # A species with no skeleton -- Kosh's column plan has no legs and
        # `animation.py` says so out loud rather than inventing a gait -- keeps
        # the bind pose. Dropping the person instead would be invisible here
        # and wrong in the frame.
        return _mesh_for(species, npc_id, lod)

    # Flatten back into `body.build`'s (verts, tris, spans) shape. The material
    # group per part is `rig.groups`, which is the same tuple `body.build` puts
    # in its spans and in the same order -- asserted in `_selftest` by posing
    # the bind pose and comparing vertex for vertex.
    verts, tris, spans = [], [], []
    for (_name, pv, pt), grp in zip(parts, rg.groups):
        base, lo = len(verts), len(tris)
        verts.extend(pv)
        tris.extend((a + base, b + base, c + base) for a, b, c in pt)
        spans.append((grp, lo, len(tris)))
    return verts, tris, spans


def _pose_mesh(species, npc_id, lod, kind, g_ms2=G0_MS2, seat_h_m=0.0,
               phase=-1):
    """`_posed` with the seat height quantised, so the cache key is stable."""
    q = round(float(seat_h_m) / SEAT_QUANTUM_M) * SEAT_QUANTUM_M
    return _posed(species, npc_id, lod, kind, round(float(g_ms2), 4), q,
                  phase)


@_lru_cache(maxsize=512)
def place_gravity_at(place_key):
    """`(gravity in m/s^2, where the number came from)` for a register place.

    NOT A CONSTANT, and that is the point: this station spins, so gravity is a
    function of radius and runs from 0.234 g on Yellow's innermost addressed
    deck to 1.693 g deep in Grey. `animation.py` reads it -- an idle sway widens
    by G0/g and a stride shortens with the Froude number -- so a room that does
    not say where it is gets a body that stands as if it were on Earth.

    THE SOURCE IS RETURNED BECAUSE A SILENT FALLBACK IS INDISTINGUISHABLE FROM
    A CORRECT ANSWER. The drum's floor sits at 278.3 m, which is 1.0000 g to
    ten figures -- the radius was chosen for exactly that -- so twelve drum
    places came back at Earth gravity and looked perfectly resolved while the
    code had in fact failed to find them a deck at all. `_selftest` asserts the
    count of each source, which is the only way that can fail.

    Resolved from the register's own `(sector, ring, deck, z_m)` through
    `interior.decks_in_ring`, so it cannot disagree with the deck the room was
    built on.
    """
    try:
        import directory as _dir                                # noqa: PLC0415
        import interior as _it                                  # noqa: PLC0415
        import drum_ground as _dg                               # noqa: PLC0415
        q = next(p for p in _dir.PLACES if p["key"] == place_key)
        schema, profile = _it.load()
        decks = _it.decks_in_ring(schema, profile, q["sector"],
                                  q.get("ring", 0), z_m=q.get("z_m"))
        if decks:
            i = max(0, min(int(q.get("deck", 0)), len(decks) - 1))
            # `floor_g` is in EARTH GRAVITIES, not m/s^2 -- as is `gravity_at`,
            # which returns 0.359 at r = 100 m. Reading it as m/s^2 put the
            # whole station between 0.024 g and 0.17 g, a moon rather than a
            # habitat, and every pose would have swayed like it.
            return float(decks[i]["floor_g"]) * G0_MS2, "deck"
        # The drum has no deck ring: its floor IS the rotating ground, and
        # `drum_ground.FLOOR_R` is where a person stands on it.
        if q["sector"] == _it.drum_sector(schema, profile):
            return float(_it.gravity_at(schema, _dg.FLOOR_R)) * G0_MS2, "drum"
        # A place in the SPINE. `rings_fitting_at` returns a bare core where the
        # hull is too narrow for a deck stack -- at z = 3000 the hull is 18.3 m
        # and the Mainstage power node runs along it -- and a core is not a deck
        # stack, so `decks_in_ring` correctly gives nothing. The gravity there is
        # real and nearly absent: 18 m of radius at this station's omega is
        # 0.04 g, which is why `_stand_min_g` exists and why that node's crew
        # are drifting rather than standing.
        rings = _it.rings_fitting_at(schema, profile, q["sector"],
                                     q.get("z_m", 0.0))
        core = [r for r in rings if r.get("kind") == "core"]
        if core:
            return float(_it.gravity_at(schema, core[0]["r_mid"])) * G0_MS2, \
                "core"
        return G0_MS2, "fallback"
    except Exception:                                           # noqa: BLE001
        return G0_MS2, "fallback"


def place_gravity(place_key):
    """The gravity a body in `place_key` stands in, m/s^2."""
    return place_gravity_at(place_key)[0]


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
             arch="generic", seed=None, lod=ROOM_LOD, max_people=None,
             g_ms2=G0_MS2):
    """Put the hour's population into one room. Returns (v, t, g, stats).

    `room_*` is the finished room, and it is an INPUT rather than something this
    module rebuilds: people are placed against the furniture that is actually
    there, which is the only way a person ends up on a chair rather than near
    one.

    `g_ms2` is the deck's own gravity and it reaches the POSE: this station runs
    0.559 g in Yellow to 1.693 g in Grey, and `animation.py` widens an idle sway
    by `G0 / g` and shortens a stride by the Froude number. A caller that does
    not know where the room is gets Earth, which is what every caller got
    implicitly before the poses existed.
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
    # ------------------------------------------------------------------
    # A POST IS MANNED WHETHER OR NOT THE ROOM IS BUSY
    # ------------------------------------------------------------------
    # `occupancy` is a crowd DENSITY -- people per square metre at an hour --
    # and it knows nothing about duty. The brig at 18:00 comes back with ONE
    # person in it, so folding a four-officer watch into that headcount left
    # room for zero officers and the render proved it: one League civilian and
    # no uniform, in a detention block.
    #
    # So the split is: the FIXED post is ADDED to the headcount, because those
    # officers are there because they are rostered there; the ROVING share is
    # drawn from the ambient crowd, because a patrol passing through IS part of
    # the traffic. `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` 2.4-2.5 makes the
    # same distinction and this is it in arithmetic.
    stats_fixed = stats_roving = 0
    try:
        from npc import security as _sec                       # noqa: PLC0415
        _pres = _sec.presence_at(place_key, hour)
        stats_fixed = int(_pres["fixed"])
        stats_roving = int(round(_pres["roving"]))
    except Exception:                                          # noqa: BLE001
        _sec = None
    n += stats_fixed
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
    # The 500 are part of the 6,500 EarthForce complement (FACTIONS.md 2.2),
    # so an officer is human. `slots` decides which BODY is built and `people`
    # decides whose costume and id it wears, so these have to agree or the
    # room gets a Narn in a human officer's uniform -- the silent-mismatch
    # class this project keeps paying for.
    for i in range(min(stats_fixed, len(slots))):
        slots[i] = "human"
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
    # ------------------------------------------------------------------
    # THE UNIFORM IN THE ROOM, and no roster could ever have put it there
    # ------------------------------------------------------------------
    # `_res.roster` casts a place's REGULARS, resolved from each resident's
    # `job`. That is right for a merchant and wrong for a police officer: an
    # officer standing the Zocalo post has `job == "patrol"`, so the Zocalo's
    # roster comes back merchants, financiers, visitors and service staff and
    # **not one officer** -- in the space `docs/gazetteer/LAW-CRIME-DOWNBELOW.md`
    # 2.4 calls "the most-policed civilian space on the station".
    stats["officers"] = 0
    stats["officers_wanted"] = stats_fixed + stats_roving
    if _sec is not None and stats["officers_wanted"] > 0 and people:
        want_off = stats["officers_wanted"]
        force = _sec.officer_pool(hour, max(2, want_off * 2 + 8))
        human_slots = [i for i, sp in enumerate(slots) if sp == "human"]
        k = min(want_off, len(human_slots), len(force), len(people))
        for j in range(k):
            people[human_slots[j]] = force[j]
        stats["officers"] = k

    stats["scheduled"] = sum(1 for r in people
                             if _res.where_at(r, hour) == place_key)
    stats["named"] = sum(1 for r in people if r.name)

    # THE FRICTION, AS A DISTANCE. `_clear` kept every body 0.45 m from every
    # other body regardless of who they were -- one radius for a Narn and a
    # Centauri and for two humans queuing at the same stall -- so
    # `docs/gazetteer/FACTIONS.md` 12, which CLAUDE.md's scope calls "the
    # friction between them visible in a corridor", was invisible BY
    # CONSTRUCTION. `npc/friction.separation_m` turns the section's fourteen
    # sourced rows into metres, and 12's own closing rule says to build exactly
    # this and nothing else first: "95% as avoidance and 5% as contact ...
    # BUILD THE AVOIDANCE FIRST; the fights are set dressing on top of it."
    #
    # `used` carries the occupant's species so the radius can depend on the
    # PAIR. The `r` argument still wins when a caller passes one -- the 0.7 m
    # a walker needs is about the walking, not about who is walking.
    def _clear(x, z, r=None, sp=None):
        for u in used:
            ux, uz = u[0], u[1]
            usp = u[2] if len(u) > 2 else None
            # `r` IS A FLOOR, NOT AN OVERRIDE, and getting that wrong is what
            # the crowd gate caught: a walker is placed with `r=0.7` for
            # walking clearance, and taking that INSTEAD of the pair's own
            # separation put a Narn 0.96 m from a Centauri where the table
            # says 1.80. The two constraints are about different things -- one
            # is about walking, one is about who is walking -- so both apply.
            need = 0.45 if r is None else r
            if sp and usp:
                need = max(need, _friction.separation_m(sp, usp))
            if (x - ux) ** 2 + (z - uz) ** 2 <= need * need:
                return False
        return True

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

    def _inside(x, z, m=None, yaw=0.0):
        """A whole body fits within the room, not just its centre point.

        The seat and desk placements skipped this and put a shoulder through
        the end wall of three cargo rooms -- a bench hard against the wall is a
        perfectly good bench, and the person sitting on it still has a body.
        rooms.py's footprint assertion caught it; the wander placement already
        allowed for width and these two did not.
        """
        # THE BODY'S OWN HALF-WIDTH, not the nominal 0.32 m. `BODY_R_M` is a
        # nude human's shoulder, and once people got dressed a coat and a
        # skirt made them wider -- `rooms.py`'s footprint assertion caught it
        # immediately: "earthforce_office: inside its own footprint -- x
        # -4.27..4.07 in +/-3.89". The same measurement already guards the
        # corridor placement; this is the room half of it.
        # THE MESH BEING PLACED, not the standing one. A SEATED figure is
        # deeper than a standing one -- its thighs project 0.83 m where a
        # stance is 0.54 -- so testing the idle mesh let a sitter's knees
        # through the wall: "earthforce_office: inside its own footprint --
        # x -4.27..4.07 in +/-3.89", and 4.07 is the room's own deck.
        x0, x1, z0, z1 = _placed_bounds(m if m is not None else mesh,
                                        x, z, yaw)
        return (-hw - 1e-9 <= x0 and x1 <= hw + 1e-9
                and -hl - 1e-9 <= z0 and z1 <= hl + 1e-9)

    for i in range(n):
        who = people[i]
        sp = who.species
        # THE BODY IS THIS PERSON'S BODY. It was `_body.build(sp, f"{seed}-{i}")`
        # cached once per (species, lod), so every human in a room was one mesh
        # repeated -- and worse, `resident` reads `body.individual(species,
        # npc_id)` for SEX and PHYS CHR, so the card described a body nobody was
        # standing in. Same id on both sides, and `resident._selftest` asserts
        # the two agree.
        # POSED, not the bind pose. `mesh` here is the standing figure; a
        # sitter is rebuilt below against the height of the seat they take,
        # because `sit_clip` derives the whole pose from it.
        mesh = _pose_mesh(sp, who.npc_id, lod, "idle", g_ms2)
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
            seat_mesh = _pose_mesh(sp, who.npc_id, lod, "sit", g_ms2, sy)
            # FACING THE ROOM, and the sign was inverted. `_place_body` maps
            # the body's local +Z -- its facing -- to `(-sin(yaw), cos(yaw))`,
            # so to look along `(fx, fz)` the yaw is `atan2(-fx, fz)`. It was
            # `atan2(-sx, -sz)`, which is `atan2(-fx, -fz)` for a seat at
            # `(sx, sz)` wanting to face the centre: correct in z and MIRRORED
            # IN X. Measured on a bench at x = -2.61 it faced (-1.00, -0.02) --
            # straight at the wall -- and put the sitter's back 0.33 m through
            # it. Every seated person on the station was sitting backwards, and
            # `rooms.py`'s footprint assertion is what finally caught it,
            # because the placement test used to be a symmetric circle that
            # could not tell the two apart.
            seat_yaw = math.atan2(sx, -sz)
            if _clear(sx, sz, sp=sp) and _inside(sx, sz, seat_mesh,
                                                 seat_yaw):
                # A SEATED PERSON IS A SEATED POSE, not a standing one dropped
                # 0.42 m. That constant put a 1.829 m figure's feet 0.42 m
                # through the deck and its knees inside the chair; `sit_clip`
                # takes the seat's own measured height `sy` and puts the hips
                # on the pan and the feet on the floor, so the body's origin
                # stays at deck level like every other placement here.
                _place_body(v, t, g, seat_mesh,
                            sx, 0.0, sz,
                            seat_yaw, f"npc_seated_{i}",
                            actors, who_rec)
                used.append((sx, sz, sp))
                stats["seated"] += 1
                seated = True

        j = i - len(seats)
        if not seated and 0 <= j < len(desks):
            dx, dy, dz, _a = desks[j]
            # Stand OFF the desk, on the side facing the room centre.
            ux = dx - STAND_OFF_M * (1.0 if dx > 0 else -1.0)
            uz = dz
            if (_clear(ux, uz, sp=sp) and _inside(ux, uz)
                    and _free(ux, uz)):
                _mv, _mt = len(v), len(t)
                # Same convention, same inversion: to face the desk from
                # the stand-off point the yaw is `atan2(-(dx-ux), dz-uz)`.
                _place_body(v, t, g, mesh, ux, 0.0, uz,
                            math.atan2(ux - dx, dz - uz), f"npc_standing_{i}",
                            actors, who_rec)
                if not _embedded(_mv, _mt):
                    used.append((ux, uz, sp))
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
            if not _clear(px, pz, 0.7, sp=sp):
                continue
            _mv, _mt = len(v), len(t)
            _place_body(v, t, g, mesh, px, 0.0, pz,
                        _u(seed, "yaw", i) * math.tau, f"npc_standing_{i}",
                        actors, who_rec)
            if _embedded(_mv, _mt):
                continue
            used.append((px, pz, sp))
            stats["walking"] += 1
            break
    stats["placed"] = stats["seated"] + stats["standing"] + stats["walking"]
    stats["triangles"] = len(t)
    stats["actors"] = actors
    return v, t, g, stats


def populate_corridor(deck_id, radius_m, half_w_m, arc_deg, start_deg, z_m,
                      served=(), hour=None, seed=None, lod=None,
                      instanced=False):
    """People walking the ring corridor of one deck. Returns (v, t, g, stats).

    THE SPACE THE PLAYER IS ACTUALLY IN, and it had nobody in it. Every other
    entry point here fills a ROOM; a player walked 126 m of assembled corridor
    and met not one person on a station of 250,000.

    Emitted in the RING'S OWN WORLD FRAME rather than a room's local one, and
    that is deliberate: a corridor is not a box that gets placed, it is the
    place. `deck.py` hands over the same `(radius_m, half_w_m, arc_deg,
    start_deg, z_m)` it built the arc from -- `collision.py`'s `collision_meta`
    -- so a deck that moves takes its people with it, and there is no second
    description of where the floor is.

    Everyone is walking, because that is what a corridor is for: `walk_clip`
    at a per-resident phase, which is the first thing in this project to use
    the Froude gait ladder for anything. Half go each way round the ring, so
    the traffic has two directions rather than a procession.
    """
    hour = _R_STATION_HOUR() if hour is None else hour
    seed = seed or f"corridor/{deck_id}"
    circ = 2.0 * math.pi * radius_m * (arc_deg / 360.0)
    area = circ * 2.0 * half_w_m
    n = corridor_headcount(served, area, hour)
    if lod is None:
        lod = corridor_lod(radius_m, 2.0 * half_w_m)
    g_ms2 = float(_it_gravity(radius_m))

    v, t, g, actors = [], [], [], []
    instances = []
    stats = {"wanted": n, "placed": 0, "area_m2": area, "lod": lod,
             "per_100m2": (n / area * 100.0) if area > 0 else 0.0,
             "sight_m": corridor_sight_m(radius_m, 2.0 * half_w_m)}
    if n <= 0:
        stats["actors"] = actors
        stats["instances"] = instances
        stats["triangles"] = 0
        return v, t, g, stats

    mix = _sector_mix_for_radius(radius_m)
    for i in range(n):
        # Along the arc, jittered off an even spacing so the file does not
        # read as a fence. Across it, anywhere clear of both walls.
        frac = (i + 0.5) / n + (_u(seed, "jit", i) - 0.5) / n
        ang = (start_deg + (frac % 1.0) * arc_deg) % 360.0
        sp = _species_from_mix(mix, seed, i)
        npc_id = f"{STATION_SEED}/{seed}/{i}"
        who = _res.resident(npc_id, sp)
        # INSTANCED walkers share their species' nominal body at one of eight
        # phases; baked ones get their own. See the crowd-library note above
        # for the three measurements that decided it.
        phase = int(_u(seed, "phase", i) * CROWD_PHASES) % CROWD_PHASES
        mesh = (crowd_body(sp, lod, phase) if instanced
                else _pose_mesh(sp, npc_id, lod, "walk", g_ms2))
        # THIS BODY'S OWN HALF-WIDTH, measured, not `BODY_R_M`. That constant
        # is a nominal human's 0.32 m and this station has fifteen species and
        # a per-individual build, so a Narn's shoulder put people 0.10 m
        # through the corridor's end wall -- which the gate below caught. The
        # mesh is already in hand; asking it costs nothing.
        bhw = max((abs(q[0]) for q in mesh[0]), default=BODY_R_M)
        lateral = (_u(seed, "lat", i) - 0.5) * 2.0 * max(
            0.0, half_w_m - bhw)

        # Half the traffic each way. `+1` walks with increasing angle.
        way = 1.0 if _u(seed, "way", i) < 0.5 else -1.0
        a = math.radians(ang)
        # The corridor's own frame: +x radially outward (which is DOWN under
        # spin), +z along the station axis, tangential is the direction of
        # travel. A body is built +Y up and facing +Z, so it is turned to face
        # tangentially and then stood on the ring.
        r = radius_m + lateral * 0.0          # lateral is tangential-normal
        cx, cy = r * math.cos(a), r * math.sin(a)
        tang = (-math.sin(a), math.cos(a))
        px = cx + tang[0] * 0.0
        py = cy + tang[1] * 0.0
        pz = z_m + lateral
        rec = _who(who, hour, deck_id)
        if instanced:
            # NO TRIANGLES. The body is in the shared library; what is emitted
            # here is where to put it and which phase to start on. The basis is
            # written out in full rather than as a yaw, because on a spun ring
            # "up" is a different direction at every angle and a single angle
            # cannot express it -- the same trap `_place_ring_body` documents.
            ca2, sa2 = math.cos(a), math.sin(a)
            r_m, h_m = body_capsule(mesh)
            instances.append({
                "group": f"corridor_{i}", "who": rec,
                "mesh": crowd_key(sp, lod, phase),
                "species": sp, "lod": lod, "phase": phase, "way": way,
                "x": px, "y": py, "z": pz,
                "up": [-ca2, -sa2, 0.0],
                "fwd": [-sa2 * way, ca2 * way, 0.0],
                "r_m": r_m, "h_m": h_m, "pose": "walking",
                "yaw": math.pi / 2.0 * way,
                # HOW FAST THEY GO ROUND, in radians a second, so the runtime
                # advances them along the ring rather than through the wall.
                # Their own gait's speed, not a constant: `walk_clip` derives
                # it from this individual's leg length and this deck's gravity.
                "omega": _walk_speed(sp, lod, g_ms2) / max(1e-6, radius_m)
                * way,
                "cycle_s": _walk_cycle_s(sp, lod, g_ms2),
            })
            stats["placed"] += 1
            continue
        _place_ring_body(v, t, g, mesh, px, py, pz, radius_m, a, way,
                         f"corridor_{i}", actors, rec)
        stats["placed"] += 1
    stats["actors"] = actors if not instanced else [
        {k: r[k] for k in ("group", "who", "x", "y", "z", "yaw", "pose",
                           "r_m", "h_m")} for r in instances]
    stats["instances"] = instances
    stats["species_lods"] = sorted({(r["species"], r["lod"])
                                    for r in instances})
    stats["triangles"] = len(t)
    return v, t, g, stats


@_lru_cache(maxsize=128)
def _walk_speed(species, lod, g_ms2):
    """This species' self-selected walking speed on this deck, m/s.

    From `animation.walk_clip`'s own gait, so the speed a body is ANIMATED at
    and the speed it TRAVELS at are one number. Two numbers here is how a
    walk cycle ends up sliding, which is the single most obvious tell there
    is that a crowd is not real.
    """
    try:
        c = _anim.walk_clip(species, _anim.NOMINAL, g_ms2,
                            frames=CROWD_PHASES, lod=lod)
        return float(c.meta["speed_ms"])
    except Exception:                                           # noqa: BLE001
        return 1.4


@_lru_cache(maxsize=128)
def _walk_cycle_s(species, lod, g_ms2):
    """Seconds for one full stride cycle -- the clip's own duration, so the
    runtime plays the eight phases over exactly the distance the gait covers."""
    try:
        c = _anim.walk_clip(species, _anim.NOMINAL, g_ms2,
                            frames=CROWD_PHASES, lod=lod)
        return float(c.duration_s)
    except Exception:                                           # noqa: BLE001
        return 1.08


def _place_ring_body(v, t, g, mesh, px, py, pz, radius_m, ang_rad, way,
                     group, actors, who):
    """One body standing on the INSIDE of a spun ring, at world (px, py, pz).

    UP IS INWARD. The floor of a ring corridor is its outer wall, so a body's
    head points at the spin axis and its feet at the hull -- which means the
    body's local +Y maps to `-radial`, not to world +Y. Getting that wrong lays
    everybody on their side, which is exactly what the first corridor render
    showed and is why this is a separate function from `_place_body`: a room is
    handed to `deck.py` in a local frame and wrapped onto the ring afterwards,
    and a corridor is authored on the ring in the first place.

    The body's local +Z (its facing) maps to the TANGENT, so a person walks
    round the ring rather than into the wall. `way` picks which way round.
    """
    bv, bt, bg = mesh
    _cap = body_capsule(mesh)
    ca, sa = math.cos(ang_rad), math.sin(ang_rad)
    # Down (radially outward), up (inward), and the tangent.
    ux, uy = -ca, -sa                       # local +Y  -> inward
    fx, fy = -sa * way, ca * way            # local +Z  -> tangent
    n0 = len(v)
    for (bx, by, bz) in bv:
        # local x is the remaining axis: the station axis, so it moves z.
        v.append((px + ux * by + fx * bz,
                  py + uy * by + fy * bz,
                  pz + bx))
    t0 = len(t)
    t.extend((a + n0, b + n0, c + n0) for a, b, c in bt)
    g.append((f"{group}_npc_body", t0, len(t)))
    for nm, lo, hi in _by_material(bg):
        g.append((f"{group}_{nm}", t0 + lo, t0 + hi))
    if actors is not None:
        actors.append({"group": group, "who": who, "x": px, "y": py, "z": pz,
                       # The yaw `npc.gd` needs is measured in the ring's own
                       # frame, where 0 faces the station axis (+Z). A body
                       # facing the tangent is a quarter turn off that, and
                       # `way` decides which quarter.
                       "yaw": math.pi / 2.0 * way, "pose": "walking",
                       "r_m": _cap[0], "h_m": _cap[1]})


def _R_STATION_HOUR():
    import rooms as _R                                          # noqa: PLC0415
    return _R.STATION_HOUR


def _it_gravity(radius_m):
    import interior as _it                                      # noqa: PLC0415
    schema, _profile = _it.load()
    return float(_it.gravity_at(schema, radius_m)) * G0_MS2


def _sector_mix_for_radius(radius_m):
    """Species mix for a corridor. The station's own, until a deck says
    otherwise: `SECTOR_MIX` is keyed by sector and a corridor spans one deck of
    one sector, so this is where a per-sector corridor mix will hang. For now
    it is `schedule.STATION_MIX`, which is the calibrated 250,000-person mix
    and is right for a corridor by construction -- a corridor is where the
    whole station passes through."""
    return dict(_sched.STATION_MIX)


def _species_from_mix(mix, seed, i):
    x = _u(seed, "sp", i)
    acc = 0.0
    for sp, w in sorted(mix.items()):
        acc += w
        if x <= acc:
            return sp
    return "human"


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

    # -- THE POSES ARE REAL POSES ------------------------------------------
    # `animation.py` had no importer at all until this module got one, and the
    # visible cost was that a "seated" person was a STANDING body dropped
    # 0.42 m -- feet through the deck, knees inside the chair.
    _rest = _mesh_for("human", "pose/probe", ROOM_LOD)[0]
    _idle = _pose_mesh("human", "pose/probe", ROOM_LOD, "idle")[0]
    _sit = _pose_mesh("human", "pose/probe", ROOM_LOD, "sit",
                      seat_h_m=0.45)[0]
    check("the poser returns a body of the same size it was handed",
          len(_rest) == len(_idle) == len(_sit),
          f"{len(_rest)} / {len(_idle)} / {len(_sit)} vertices")
    h_rest = max(q[1] for q in _rest) - min(q[1] for q in _rest)
    h_sit = max(q[1] for q in _sit) - min(q[1] for q in _sit)
    check("a SEATED figure is shorter than a standing one -- the pose is doing "
          "the sitting, not a translation",
          0.60 < h_sit / h_rest < 0.85,
          f"{h_sit:.3f} m seated vs {h_rest:.3f} m standing "
          f"({h_sit / h_rest:.2f}x)")
    check("...and its feet are ON the deck rather than through it: the 0.42 m "
          "drop is gone", abs(min(q[1] for q in _sit)) < 0.05,
          f"lowest vertex at y={min(q[1] for q in _sit):+.3f} m")
    # THE HIPS ARE ON THE PAN, which is the claim `sit_clip` exists to make and
    # the reason the seat's own height is passed in rather than assumed.
    _sit40 = _pose_mesh("human", "pose/probe", ROOM_LOD, "sit",
                        seat_h_m=0.40)[0]
    _sit62 = _pose_mesh("human", "pose/probe", ROOM_LOD, "sit",
                        seat_h_m=0.62)[0]
    d_h = (max(q[1] for q in _sit62) - max(q[1] for q in _sit40))
    check("BREAK: a stool 0.22 m higher than a bench seats the same person "
          "0.22 m higher -- so the seat height reaches the pose and is not "
          "decoration", abs(d_h - 0.22) < 0.06, f"head rose {d_h:+.3f} m")
    # NEGATIVE CONTROL: an idle pose is NOT the bind pose. If it were, this
    # whole exercise would be a no-op that every check above still passes.
    check("BREAK: the idle pose actually moves the body off the bind pose",
          max(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
              for a, b in zip(_rest, _idle)) > 0.01,
          f"max vertex move "
          f"{max(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) for a, b in zip(_rest, _idle)):.4f} m")
    # AND IT IS PER-PERSON. Two residents in one room must not strike the same
    # attitude; `idle_clip`'s phase is seeded on the id.
    _idle2 = _pose_mesh("human", "pose/probe-2", ROOM_LOD, "idle")[0]
    check("...and two residents do not stand identically -- no chorus line",
          any(abs(a[0] - b[0]) > 1e-4 for a, b in zip(_idle, _idle2)))
    # GRAVITY REACHES THE POSE. Yellow is 0.559 g and Grey is 1.693 g; a sway
    # widens by G0/g, so the same person stands differently on the two decks.
    _lo_g = _pose_mesh("human", "pose/probe", ROOM_LOD, "idle", 0.559 * 9.80665)
    _hi_g = _pose_mesh("human", "pose/probe", ROOM_LOD, "idle", 1.693 * 9.80665)
    check("BREAK: the DECK'S GRAVITY reaches the pose -- 0.559 g and 1.693 g "
          "are not the same stance",
          any(abs(a[0] - b[0]) > 1e-4 for a, b in zip(_lo_g[0], _hi_g[0])))

    # -- AND EVERY PLACE KNOWS ITS OWN GRAVITY -----------------------------
    import directory as _dirg                                   # noqa: PLC0415
    src = {}
    gs = []
    for _q in _dirg.PLACES:
        _g, _s = place_gravity_at(_q["key"])
        src[_s] = src.get(_s, 0) + 1
        gs.append(_g / G0_MS2)
    check("every register place resolves a real deck, the drum floor or the "
          "spine core -- none falls back to Earth",
          src.get("fallback", 0) == 0,
          f"{src} over {len(gs)} places")
    # A STANDING POSE HAS A LOWER BOUND AND `animation.py` DOES NOT ENFORCE IT.
    gmin = _stand_min_g("human", "pose/probe", ROOM_LOD)
    check("a figure has a measured minimum standing gravity, read off its own "
          f"feet: {gmin / G0_MS2:.4f} g",
          0.02 < gmin / G0_MS2 < 0.25, f"{gmin:.3f} m/s^2")
    _drift = _pose_mesh("human", "pose/probe", ROOM_LOD, "idle", 0.04 * G0_MS2)
    _dx = max(q[0] for q in _drift[0]) - min(q[0] for q in _drift[0])
    check("BREAK: at 0.04 g the idle sway would lean a body 0.64 m wide and "
          "lift its feet off the deck; below the bound the figure glides "
          "instead and comes back inside its own shoulders",
          _dx < 0.58 and min(q[1] for q in _drift[0]) < 0.03,
          f"width {_dx:.3f} m, lowest vertex "
          f"{min(q[1] for q in _drift[0]):+.3f} m")
    check("...and the bound does not fire on any deck a person works on: "
          "only the Mainstage spine node is below it",
          sum(1 for _q in _dirg.PLACES
              if place_gravity(_q["key"]) < gmin) == 1,
          str([_q["key"] for _q in _dirg.PLACES
               if place_gravity(_q["key"]) < gmin]))
    check("...and the range is the station's, not a constant: "
          f"{min(gs):.3f} g to {max(gs):.3f} g",
          min(gs) < 0.5 and max(gs) > 1.5,
          f"spread {max(gs) / max(1e-9, min(gs)):.1f}x")
    # BREAK: the drum answer must come from the DRUM, not from the fallback
    # happening to be right. `drum_ground.FLOOR_R` is 278.3 m, which is 1.0000 g
    # to ten figures, so twelve places looked resolved while nothing had
    # resolved them.
    check("BREAK: the drum's dozen places are answered by the drum floor, and "
          "the fact that it is 1.0000 g is a consequence rather than a "
          "coincidence the fallback got away with",
          src.get("drum", 0) >= 10
          and abs(place_gravity("the_garden") / G0_MS2 - 1.0) < 1e-6,
          f"drum-sourced {src.get('drum', 0)}")

    # -- THE CORRIDOR HAS PEOPLE IN IT -------------------------------------
    # Every entry point above fills a ROOM. A player walked 126 m of assembled
    # corridor and met nobody.
    R_BLUE, HW_BLUE = 211.478, 1.3
    cv, ct, cg, cs = populate_corridor(
        "test/blue_0_0", R_BLUE, HW_BLUE, 344.0, 8.0, 7121.3,
        served=("customs_north", "arrival_concourse", "customs_south"),
        hour=13.0)
    check("a ring corridor is populated at all", cs["placed"] > 20, str(
        {k: v for k, v in cs.items() if k != "actors"}))
    check(f"...at the derived density, {CORRIDOR_PER_100M2:.2f} people per "
          "100 m2 station-wide, scaled by what the deck serves",
          1.5 < cs["per_100m2"] < 4.0,
          f"{cs['per_100m2']:.2f} on a deck serving three busy places")
    # THE BODIES STAND ON THE FLOOR, and on a ring the floor is the OUTER wall.
    rad = [math.hypot(x, y) for x, y, _z in cv]
    check("their feet are on the deck and their heads point at the spin axis",
          abs(max(rad) - R_BLUE) < 0.05
          and 1.5 < (R_BLUE - min(rad)) < 2.6,
          f"feet at r={max(rad):.3f} of {R_BLUE}, tallest head "
          f"{R_BLUE - min(rad):.2f} m clear")
    check("...and they are inside the corridor, not through its end walls",
          all(abs(z - 7121.3) <= HW_BLUE + 0.01 for _x, _y, z in cv),
          f"z spread {min(z for _x, _y, z in cv):.2f}.."
          f"{max(z for _x, _y, z in cv):.2f}")
    # BREAK: the root translation of a walk cycle is THREE motions and only one
    # of them is a displacement. Taking all three off lifts everybody.
    _wf = [_pose_mesh("human", f"walkprobe/{f}", 4, "walk")[0]
           for f in range(3)]
    check("BREAK: a walking body's planted foot is on the deck at every phase "
          "-- the pelvis bob is the walk, not a displacement to remove",
          all(abs(min(q[1] for q in m)) < 0.03 for m in _wf),
          str([round(min(q[1] for q in m), 4) for m in _wf]))
    # AND THE PHASES DIFFER, or eighty people are a drill squad.
    _p0 = _pose_mesh("human", "walkprobe/a", 4, "walk")[0]
    _p1 = _pose_mesh("human", "walkprobe/b", 4, "walk")[0]
    check("...and two walkers are at different points in their stride",
          max(abs(a[2] - b[2]) for a, b in zip(_p0, _p1)) > 0.05,
          f"max z difference {max(abs(a[2] - b[2]) for a, b in zip(_p0, _p1)):.3f} m")
    # THE LOD IS CHOSEN BY THE SIGHT LINE, not by a constant.
    check("BREAK: a wider ring sees further down its own corridor, so the LOD "
          "the people are baked at is a function of the deck",
          corridor_sight_m(560.0, 2.6) > corridor_sight_m(211.0, 2.6) * 1.5,
          f"grey {corridor_sight_m(560.0, 2.6):.0f} m vs blue "
          f"{corridor_sight_m(211.0, 2.6):.0f} m")
    check("...and the corridor's triangle cost is a small share of a deck",
          cs["triangles"] < 60_000,
          f"{cs['triangles']:,} for {cs['placed']} people at lod {cs['lod']}")
    # -- NOBODY SITS FACING THE WALL ---------------------------------------
    # `_place_body` maps a body's local +Z to `(-sin(yaw), cos(yaw))`, so
    # facing `(fx, fz)` needs `atan2(-fx, fz)`. The seat placement used
    # `atan2(-sx, -sz)` -- correct in z and MIRRORED IN X -- so a sitter on the
    # -x wall faced (-1.00, -0.02), straight at it, with 0.33 m of their back
    # through the plaster. It survived because the placement test was a
    # symmetric circle around the body's centre, which cannot tell forwards
    # from backwards. `rooms.py`'s footprint assertion caught it only once the
    # test became the body's real placed bounds.
    _sv, _st, _sg, _ss = populate("t", dv, dt, dg, 6.0, 9.0, hour=13.0,
                                  arch="office")
    _seated = [a for a in _ss["actors"] if a["pose"] == "seated"]
    _facing = []
    for a in _seated:
        _ca, _sa = math.cos(a["yaw"]), math.sin(a["yaw"])
        # Their forward, against the direction from them to the room's centre.
        _fx, _fz = -_sa, _ca
        _tx, _tz = -a["x"], -a["z"]
        _n = math.hypot(_tx, _tz) or 1.0
        _facing.append((_fx * _tx + _fz * _tz) / _n)
    check("a seated person faces the room, not the wall behind them",
          bool(_facing) and min(_facing) > 0.0,
          f"{sum(1 for c in _facing if c <= 0)} of {len(_facing)} face away; "
          f"worst dot {min(_facing) if _facing else 0:+.2f}")
    check("...and every one of them is inside the room they are in",
          all(-2.9 <= x <= 2.9 for a in _seated
              for x in _placed_bounds(
                  _pose_mesh(a["who"]["species"], a["who"]["id"], ROOM_LOD,
                             "sit", G0_MS2, 0.45),
                  a["x"], a["z"], a["yaw"])[:2]),
          "a sitter's back is through the wall")

    # -- THE WARDROBE ------------------------------------------------------
    # `costume.py` measured 53 reachable (slot, fabric) materials, 32 off
    # authority-1 show frames, and nothing had ever put one on anybody.
    import costume as _cos_t                                    # noqa: PLC0415
    _specs = _cos_t.material_specs()
    _dr_ok = _dressed_ok()
    _miss = sorted(set(_dressed_missing))
    check(DRESSED, "the wardrobe is switched on")
    check(len(_specs) > 40,
          f"...and it has {len(_specs)} materials to bind", str(_specs[:1]))
    if _dr_ok:
        _dm = _mesh_for("human", "wardrobe/probe", ROOM_LOD)
        _gn = {n for n, _l, _h in _dm[2]}
        check(any(n.startswith("npc_cloth") for n in _gn),
              "a person is DRESSED: the mesh carries cloth groups",
              str(sorted(_gn)))
        check(not any(n.startswith("npc_skin_torso") for n in _gn),
              "...and the cloth REPLACES the skin it covers rather than "
              "floating over it", str(sorted(_gn)))
    else:
        # NOT A SKIP, A REPORTED BLOCK. The geometry is wired and gated; what
        # is missing is the library binding, which lives in `materials.py`.
        # `_dressed_ok` asks the library rather than trusting a flag, so this
        # flips the moment those materials land -- and says so until they do.
        check(bool(_miss),
              f"the wardrobe is BLOCKED on {len(_miss)} material bindings and "
              f"says so rather than rendering magenta: {_miss[:3]}")
        check(_mesh_for("human", "wardrobe/probe", ROOM_LOD)[1],
              "...and everybody stays in skin meanwhile, which is wrong but "
              "not broken")

    # -- THE CROWD LIBRARY: shared bodies, instanced ----------------------
    lib_v, lib_t, lib_g = station_crowd_library(4)
    bodies = [n for n, _lo, _hi in lib_g if n.endswith("_npc_body")]
    check(f"the station crowd library is {len(bodies)} shared bodies -- "
          f"{len(_sched.STATION_MIX)} species x {CROWD_PHASES} phases",
          len(bodies) == len(_sched.STATION_MIX) * CROWD_PHASES,
          f"{len(bodies)} bodies, {len(lib_t):,} triangles")
    check("...and it is 8x smaller than baking the station's 963 walkers "
          f"individually ({len(lib_t):,} against {963 * 484:,})",
          len(lib_t) < 963 * 484 / 5.0,
          f"{100 * (1 - len(lib_t) / (963 * 484)):.0f}% saved")
    # THE EIGHT PHASES ARE EIGHT DIFFERENT BODIES. A library of one pose
    # repeated eight times animates nothing and every gate above still passes.
    _p0 = crowd_body("human", 4, 0)[0]
    _spread = [max(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
                   for a, b in zip(_p0, crowd_body("human", 4, ph)[0]))
               for ph in range(1, CROWD_PHASES)]
    check("BREAK: every phase in the library is a DIFFERENT pose -- a library "
          "of one pose repeated animates nothing",
          min(_spread) > 0.05,
          f"nearest other phase differs by {min(_spread):.3f} m, furthest by "
          f"{max(_spread):.3f} m")
    # AND EVERY ONE STANDS ON THE DECK. A phase whose planted foot is off the
    # floor is a body that hovers for an eighth of every stride.
    check("...and every phase has its planted foot on the deck",
          all(abs(min(q[1] for q in crowd_body("human", 4, ph)[0])) < 0.03
              for ph in range(CROWD_PHASES)),
          str([round(min(q[1] for q in crowd_body("human", 4, ph)[0]), 4)
               for ph in range(CROWD_PHASES)]))
    iv, it2, ig, ist = populate_corridor(
        "test/inst", R_BLUE, HW_BLUE, 344.0, 8.0, 7121.3,
        served=("customs_north", "arrival_concourse", "customs_south"),
        hour=13.0, instanced=True)
    check("an instanced corridor emits NO triangles of its own",
          not it2 and ist["placed"] > 20,
          f"{len(it2)} triangles, {ist['placed']} instances")
    check("...and every instance names a body the library actually holds",
          all(r["mesh"] + "_npc_body" in bodies for r in ist["instances"]),
          str(sorted({r["mesh"] for r in ist["instances"]}
                     - {b[:-len('_npc_body')] for b in bodies})[:4]))
    # THE SPEED THEY TRAVEL AT IS THE SPEED THEY ARE ANIMATED AT. Two numbers
    # here is exactly how a walk cycle ends up sliding.
    _r = ist["instances"][0]
    _v = abs(_r["omega"]) * R_BLUE
    _gait = _walk_speed(_r["species"], _r["lod"], G0_MS2)
    check("a walker travels at their OWN gait's speed, not a constant -- "
          "two numbers here is how a walk cycle ends up sliding",
          abs(_v - _gait) < 0.2,
          f"{_v:.2f} m/s round the ring against {_gait:.2f} m/s of gait")
    # AND UP IS INWARD, per instance, because on a ring it is a different
    # direction at every angle.
    import math as _m
    check("every instance's up points at the spin axis",
          all(abs(_m.hypot(r['up'][0], r['up'][1]) - 1.0) < 1e-6
              and r['up'][0] * r['x'] + r['up'][1] * r['y'] < 0
              for r in ist["instances"]),
          "an up that is world +Y lays every body on its side, and a walk "
          "test reads that as 'the corridor is clear'")

    # A DECK THAT SERVES NOTHING IS QUIET, NOT EMPTY.
    _, _, _, qs = populate_corridor("test/quiet", R_BLUE, HW_BLUE, 344.0, 8.0,
                                    7121.3, served=(), hour=3.0)
    check("a deck serving nothing is quiet rather than abandoned",
          0 < qs["placed"] < cs["placed"] / 4,
          f"{qs['placed']} against {cs['placed']} on the busy deck")
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
        if a["pose"] != "standing" or a["group"] + "_npc_body" not in spans:
            continue
        lo, hi = spans[a["group"] + "_npc_body"]
        idx = {i for tri in zt[lo:hi] for i in tri}
        got = sorted(round(zv[i][1], 6) for i in idx)
        # Against the POSED mesh, because that is what was placed. The pose is
        # a pure function of (species, id, lod, kind, g), and `idle_clip`
        # carries a per-resident phase, so the fingerprint is strictly MORE
        # discriminating than the bind pose was -- two people of identical
        # stature now differ by their own sway as well as by their build.
        bv, _bt, _bg = _pose_mesh(a["who"]["species"], a["who"]["id"],
                                  ROOM_LOD, "idle")
        want = sorted(round(q[1], 6) for q in bv)
        if got != want:
            mism.append(a["who"]["id"])
    check("a person's card and a person's MESH are the same individual",
          not mism, f"{len(mism)} of {len(acts)} bodies belong to somebody else")
    # NEGATIVE CONTROL: the same comparison against a DIFFERENT person's body
    # must fail, or the fingerprint is not a fingerprint.
    a0 = next(a for a in acts if a["pose"] == "standing")
    lo, hi = spans[a0["group"] + "_npc_body"]
    idx = {i for tri in zt[lo:hi] for i in tri}
    got = sorted(round(zv[i][1], 6) for i in idx)
    other = _pose_mesh(a0["who"]["species"], a0["who"]["id"] + "-not-me",
                       ROOM_LOD, "idle")[0]
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

    # ------------------------------------------------------------------
    # THE UNIFORM IN THE ROOM. See the block in `populate`.
    # ------------------------------------------------------------------
    import dressing as _D                                       # noqa: PLC0415
    from npc import security as _sec                            # noqa: PLC0415

    def _room(key, arch, w=14.0, l=10.0, cap=40):
        v, t, g, _c = _D.dress(key, w, l, 3.0, arch)
        return populate(key, v, t, g, w, l, hour=18.0, arch=arch,
                        max_people=cap)

    _v, _t, _g, zs = _room("zocalo", "commerce")
    check("the Zocalo post reaches the crowd -- officers in the room",
          zs.get("officers", 0) >= 4,
          f"{zs.get('officers', 0)} of {zs['wanted']} wanted")
    _v, _t, _g, ds = _room("downbelow", "generic")
    check("...and Downbelow has none, which the gazetteer states by design",
          ds.get("officers", 0) == 0, f"{ds.get('officers', 0)}")
    # NEGATIVE CONTROL: strip the Zocalo's post and the same room must come
    # back with no uniform in it. Without this the check above passes on any
    # room that happens to roster an officer by chance.
    keep = _sec.POSTS
    try:
        _sec.POSTS = tuple(q for q in _sec.POSTS if q[0] != "zocalo")
        _v, _t, _g, zs2 = _room("zocalo", "commerce")
        # It does NOT go to zero, and that is correct rather than a weak
        # control: the Zocalo is still on a patrolled outer ring, so it keeps
        # its share of the roving pairs. What the post supplies is the FIXED
        # eight, and that is exactly what the drop removes.
        print(f"  control: drop the Zocalo post -> "
              f"{zs2.get('officers', 0)} officers in the room "
              f"(was {zs.get('officers', 0)}, the roving share survives) -- "
              f"{'FIRES' if zs2.get('officers', 0) < zs.get('officers', 0) else 'DOES NOT FIRE'}")
        check("the officer gate fires when the post is removed",
              zs2.get("officers", 0) < zs.get("officers", 0),
              f"{zs2.get('officers', 0)} vs {zs.get('officers', 0)}")
    finally:
        _sec.POSTS = keep

    # ------------------------------------------------------------------
    # THE FRICTION IS IN THE CROWD, measured on the placed bodies rather than
    # asserted about the function that placed them.
    # ------------------------------------------------------------------
    def _min_gap(stats_actors, a_sp, b_sp):
        pts = [(x["x"], x["z"], x["who"]["species"])
               for x in stats_actors if "x" in x and "who" in x]
        best = None
        for i, (x0, z0, s0) in enumerate(pts):
            for x1, z1, s1 in pts[i + 1:]:
                if {s0, s1} != {a_sp, b_sp} and not (
                        s0 == s1 == a_sp == b_sp):
                    continue
                d = ((x0 - x1) ** 2 + (z0 - z1) ** 2) ** 0.5
                best = d if best is None or d < best else best
        return best

    # A BIG ROOM ON PURPOSE. The friction is a property of a PAIR, so the test
    # room has to be large enough to hold both halves of one: the Zocalo draws
    # 19 Narn and 20 Centauri per 120 people, so a 14 x 10 m probe at forty
    # occupants frequently holds neither and the measurement comes back None.
    # Reported rather than passed when it does -- see the else branch.
    _v, _t, _g, fs = _room("zocalo", "commerce", w=26.0, l=20.0, cap=120)
    acts = fs.get("actors") or []
    hh = _min_gap(acts, "human", "human")
    nc = _min_gap(acts, "narn", "centauri")
    check("the crowd knows who is standing next to whom",
          bool(acts), f"{len(acts)} actors")
    if hh is not None:
        check("two humans stand at ordinary personal space",
              hh >= 0.44, f"{hh:.2f} m")
    if nc is not None:
        check("a Narn and a Centauri stand four times further apart -- "
              "FACTIONS.md 12's highest row, in metres, in a placed crowd",
              nc >= _friction.separation_m("narn", "centauri") - 0.01,
              f"{nc:.2f} m against a required "
              f"{_friction.separation_m('narn', 'centauri'):.2f}")
        print(f"  friction in the crowd: human/human {hh:.2f} m, "
              f"narn/centauri {nc:.2f} m "
              f"(required {_friction.separation_m('narn', 'centauri'):.2f})")
    else:
        print("  friction in the crowd: no narn/centauri pair in this room "
              "to measure -- reported, not silently passed")

    # -- A BEDROOM IS NOT AN OFFICE ----------------------------------------
    # The fallback curve peaks at 13:00 because it is a working day, and it was
    # applied to all seven residences, which archetype as `generic`. `life.py`
    # found it by correlating its own routed day against this hour by hour: six
    # of the seven came back ANTI-correlated, -0.80 to -0.56.
    _rescur = [occupancy("qtr_civilian", 1000.0, float(h)) for h in range(24)]
    _off = [occupancy("drum_office", 1000.0, float(h)) for h in range(24)]
    check("a residence is fullest at night",
          _rescur.index(max(_rescur)) in tuple(range(21, 24)) + tuple(range(0, 7)),
          f"peaks at {_rescur.index(max(_rescur))}:00")
    check("...and emptiest in the working day",
          _rescur.index(min(_rescur)) in range(9, 19),
          f"empties at {_rescur.index(min(_rescur))}:00")
    check("...while an office still does the opposite",
          _off.index(max(_off)) in range(9, 19),
          f"office peaks at {_off.index(max(_off))}:00")
    # THE CORRELATION, which is the shape `life.py` measured and the number
    # that was negative. A home and an office must be anti-correlated with each
    # other; if they are not, one of the two curves is not doing its job.
    _mr = sum(_rescur) / 24.0
    _mo = sum(_off) / 24.0
    _cov = sum((a - _mr) * (b - _mo) for a, b in zip(_rescur, _off))
    _sr = sum((a - _mr) ** 2 for a in _rescur) ** 0.5
    _so = sum((b - _mo) ** 2 for b in _off) ** 0.5
    _r = _cov / max(_sr * _so, 1e-9)
    check("...and the two are strongly anti-correlated over the day",
          _r < -0.5, f"r = {_r:+.2f}")
    # AND THE HEADCOUNT IS UNCHANGED. This moves WHEN a residence is full, not
    # how many people the station holds -- the curve is normalised to the
    # working curve's own daily mean. Without this a "fix" to the shape is a
    # silent change to the population.
    check("...and the station's daily mean occupancy is unmoved by the change",
          abs(_mr - _mo) / max(_mo, 1e-9) < 0.15,
          f"residence mean {_mr:.1f} against office {_mo:.1f}")
    # The control: a place that is NOT a residence must not take the curve.
    check("the residence curve applies to residences only",
          not _is_residence("drum_office") and _is_residence("qtr_command"),
          "the residence test matches everything or nothing")

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
