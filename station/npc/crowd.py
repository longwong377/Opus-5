#!/usr/bin/env python3
"""The crowd: how many people are in a place, who they are, and what they cost.

`schedule.py` answers *when* a species is awake and *what fraction* of a place's
standing crowd it is. It stops one step short of a crowd, because it has no
floor areas: a density of "20 persons per 100 m^2" is not a crowd until
something says how many square metres the Zocalo has. This module supplies the
missing multiplier, turns the result into named individuals standing at
coordinates, and prices the whole thing against `station/budget.py`.

The owner names **crowdedness/isolation** as an AAA dimension in its own right
(`docs/AAA-STANDARD.md`). That makes this module's output a *feeling* with a
number attached, and both poles have to be built deliberately:

    Dark Star, 23:00           0.300 persons/m^2      a room you push through
    Yellow maintenance, 03:00  0.0005 persons/m^2     two suited figures in a km

A factor of 600. Neither is an accident and neither is tuned by eye.

ERA DATUM
---------
**S3, pre-martial-law**, between S3E02 *Convictions* and S3E09 *Point of No
Return* (`docs/gazetteer/FACTIONS.md` 1.3). Inherited from `schedule.py`, not
re-decided here. The consequences this module can actually show a player are
the Nightwatch armband on a minority of one uniform (5.4), the Narn refugee
role (6.2), the Ranger brooch worn by 20-60 people in 250,000 (10.1), and a
sealed Markab quarter that is empty at every hour of every day (1.3).

WHAT IS NEW HERE AND WHAT IS DELEGATED
--------------------------------------
Delegated to `schedule.py`, never recomputed:  per-place density by hour
(`density_at`), species composition (`crowd_at`, `crowd_headcount`), individual
rhythm and role (`activity_at`, `role_for`), the mix and its apportionment.
Duplicating any of those would give the station two answers to one question.

New here:

  1. **Floor areas.**  Every place gets an area by one of four declared routes,
     and the route is stored beside the number so a reader can tell a measured
     dimension from an invention (`AreaRoute`, `EXTENTS`).
  2. **Deterministic spawning.**  `spawn(place, hour, seed)` returns the same
     people, with the same names, roles, costume flags and coordinates, on
     every run and every machine.  blake2b throughout; no `random`, no
     `str.__hash__`.
  3. **Simulation LOD** with stated radii, caps and a boundary policy -- the
     part that decides whether 250,000 residents are a frame rate problem.
  4. **The alienness gradient** as a measured quantity rather than a claim
     (`alienness`, `GRADIENT_ROUTE`).
  5. **A worst-case cost report** against `station/budget.py`'s frame budget.

WHAT THE CROSS-CHECKS FOUND
---------------------------
Writing the areas down forced four disagreements into the open. All four are
reported rather than papered over; three belong to files this module may not
edit, so they are returned as findings and asserted here as *change detectors*
-- if someone fixes one, the assertion fails and points at this paragraph.

  (a) `schedule.ROLE_WEIGHTS` makes transients 69.2% human against residents
      60.4%.  FACTIONS.md 2.4 states the opposite gradient in as many words:
      "transients skew alien (ship crews, traders, delegations); residents skew
      human".  The place table (2.5) still produces the gradient a player feels,
      because it states the per-place human share directly -- but the mechanism
      underneath it runs backwards.  See `transient_gradient_audit()`.
  (b) `body.NPC_FRAME_SHARE` is 0.12 and `schedule.NPC_BUDGET["npc_frame_share"]`
      is 0.15.  Two committed modules, two budgets, same frame.  This module
      reports against the *smaller*, because a budget that disagrees with itself
      should bind at its tightest.
  (c) `body.DENSITY_PER_M2["busy"]` is 0.15 persons/m^2, measured off an
      authority-1 Zocalo frame.  `schedule.PLACES["zocalo"].peak_per_100m2` is
      20.0, i.e. 0.20.  The peak is 33% denser than the frame the geometry was
      solved against.  Both are authority 5 as *interpretations*; the frame
      count is the better anchored of the two and the difference is the
      difference between 299 and 224 figures in one view.
  (d) FACTIONS.md 2.5 says the Zocalo at 05:00 is "a lit hall with six people in
      it".  With the derived area that hour holds 37 people in 2,313 m^2 -- but
      **five** in one bay, and the bay is the unit the concourse is built in.
      The prose is a frame count, not a building count, and `_selftest` asserts
      the bay figure lands in 4-8 rather than asserting the prose literally.

PERFORMANCE -- read this before adding anything
------------------------------------------------
250,000 residents cannot be 250,000 agents, cannot be 250,000 meshes, and (as
`schedule.py` argues) cannot be 250,000 records.  Four tiers, and the boundaries
are chosen so that **nothing ever pops into existence in front of the player**:

    tier            radius              per-capita cost      cap
    FULL      0 - 18 m                  agent, path, needs   500
    CROWD     18 m - r_crowd(density)   flow field only      2,000
    FLOCK     r_crowd - subpixel        none: a density      -
                                        field sampled into
                                        impostor cards
    STATISTICAL  beyond visibility      none: a number       250,000

`r_crowd` is not a constant, because a radius is the wrong thing to fix: at
0.30 persons/m^2 a 2,000-agent cap is used up by 46 m and in the habitat drum
at 0.03 it reaches 146 m.  What is fixed is the *population* of each tier, and
the radius falls out of the density -- see `crowd_radius`.

The boundary policy, which is the part that is usually got wrong:

  * **Existence is not a tier.**  A FLOCK figure and a CROWD agent occupy the
    same coordinate, because `place_positions()` is a pure function of
    (place, hour, seed, index) and knows nothing about tiers.  Promotion gives
    an existing figure a brain; it does not create a body.  `_selftest` asserts
    that the first N positions are identical however many were asked for.
  * Tier boundaries carry 8% hysteresis so a figure standing exactly on one
    does not flicker between representations.
  * The one boundary a player can actually see is CROWD -> FLOCK, because at
    Zocalo densities it lands at ~46 m where a 1.75 m figure is still 76 px
    tall.  It is survivable only because the swap is *representation*, at a
    fixed position, with a cross-fade -- and because a figure in a crowd at 46 m
    is mutually occluded.  It would not be survivable for a lone figure, which
    is why `CROWD_LOD_OFFSET` is conditioned on crowd size and not applied to
    an isolated NPC.

COST, MEASURED -- and the shortfall stated rather than hidden
--------------------------------------------------------------
`report()` prints it and `_selftest` gates it.  Budget: 144,000 triangles, the
tighter of the two committed NPC frame shares.  Two cases matter, and one of
them does not fit:

  * **Zocalo, 20:00** -- the densest room with walls.  **423 figures** in the
    frustum over a 21.6 x 75.6 m concourse at 0.283 persons/m^2 of footprint.
    Meshes everywhere costs **324,015** triangles on body.py's individual LOD
    chain and **208,702** with `CROWD_LOD_OFFSET` -- 36% saved, and still
    **145% of budget**.  Holding meshes across the whole room needs **17.4% of
    the frame and it has 12%**.  The shortfall is real and it is closed by the
    mesh horizon: meshes to **40 m**, impostor cards beyond, where a figure is
    **68 px**.  That is the honest price, it is measured rather than asserted
    away, and the three levers that would remove it are:
        1. raise the NPC frame share from 12% to 18% (a decision for whoever
           owns `body.NPC_FRAME_SHARE`, not for this module);
        2. adopt body.py's own frame-measured busy density of 0.15/m^2 in place
           of FACTIONS 2.5's 0.20 peak -- finding (c) -- which removes 25% of
           the figures;
        3. `CROWD_LOD_OFFSET = 3`, which costs 184,654 and still misses.
    2 and 3 together fit with room to spare.  None of them is this module's to
    take unilaterally, so the shortfall is reported.

  * **The Garden (drum floor), 13:00** -- the worst case in the project, because
    there is no wall to stop the view: 129 m of developed band and 1,748 m of
    circumference, so the frustum runs to the subpixel distance.  **2,312
    figures**, **86,696 triangles** with the offset (60% of budget) and 235,222
    without it.  Here the triangle budget is not what binds -- the **agent**
    budget is: 2,304 crowd agents are wanted against a 2,000 cap, and the
    Garden is the only place in the table whose crowd radius (554 m) falls
    inside its own sight line (635 m).  That is what the FLOCK tier exists for,
    and it is why the drum's far crowd has to be a density field rather than a
    list of people.
"""
import hashlib
import math
import os
import sys
from dataclasses import dataclass
from functools import lru_cache

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import schedule as sched                                      # noqa: E402

try:
    import names as npc_names                                 # noqa: E402
except Exception:                                             # noqa: BLE001
    npc_names = None


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
# Same construction as `schedule._u`, deliberately: one hash function in the NPC
# package, so a stream here and a stream there cannot accidentally correlate
# through two different mixers. `random` is banned (it has no seed a test can
# pin across processes) and `str.__hash__` is banned (PYTHONHASHSEED salts it
# per process, and session 2n shipped a hull that changed every run because of
# exactly that).
def _u(seed: str, salt: str = "") -> float:
    """Uniform [0,1) from a string. blake2b, 8 bytes, big-endian."""
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ---------------------------------------------------------------------------
# Geometry the areas are derived from
# ---------------------------------------------------------------------------
# Every dimension imported rather than typed. If one of these imports fails the
# fallback is used AND the route is downgraded to "fallback", which `_selftest`
# fails on -- a silently-wrong area is worse than a missing one, and this
# project has shipped a gate that printed PASS on an unmeasured quantity.
def _geometry():
    g = {}

    def put(key, value, source):
        g[key] = value
        g[key + "__src"] = source

    # The Zocalo's structural bay: 6 x 3 deck pitches, both DERIVED in
    # zocalo.py from INV-010's 3.6 m pitch. The gallery depth is what is left
    # of the bay width either side of the two-storey well.
    try:
        import zocalo                                          # noqa: PLC0415
        put("bay_w_m", zocalo.BAY_WIDTH_M, "station/zocalo.py BAY_WIDTH_M")
        put("bay_l_m", zocalo.BAY_LENGTH_M, "station/zocalo.py BAY_LENGTH_M")
        put("gallery_m", zocalo.GALLERY_DEPTH_M, "station/zocalo.py GALLERY_DEPTH_M")
        put("well_w_m", zocalo.WELL_WIDTH_M, "station/zocalo.py WELL_WIDTH_M")
    except Exception:                                          # noqa: BLE001
        put("bay_w_m", 21.6, "fallback")
        put("bay_l_m", 10.8, "fallback")
        put("gallery_m", 4.5, "fallback")
        put("well_w_m", 12.6, "fallback")

    # How long a stretch of ring corridor reads as ONE room. Not chosen: a ring
    # corridor is occluded by its own curvature at 2*sqrt(r_o^2 - r_i^2), which
    # is what `interior.sight_line` computes and what `budget.py` already gates
    # the interior against. Red's outermost deck-stack ring gives 74.5 m.
    try:
        import interior as it                                  # noqa: PLC0415
        import interior_kit as ik                              # noqa: PLC0415
        schema, profile = it.load()
        w = ik.PROVISIONAL["corridor_width_m"]
        rings = [r for r in it.ring_radii(schema, profile, "red")
                 if r["kind"] == "deck_stack"]
        put("red_sight_m", it.sight_line(rings[0]["r_outer"], w),
            "interior.sight_line(red outermost deck stack, corridor_width_m)")
        drum = it.drum_sector(schema, profile)
        r = it.sector_radius(schema, profile, drum)
        ex = schema["sectors"]["extents_m"][drum]
        put("drum_r_m", r, f"interior.sector_radius({drum})")
        put("drum_len_m", ex["z1"] - ex["z0"], f"schema sectors.extents_m[{drum}]")
        put("drum_floor_m2", 2.0 * math.pi * r * (ex["z1"] - ex["z0"]),
            "2*pi*r*L of the habitat drum's inner surface")
        put("corridor_w_m", w, "interior_kit.PROVISIONAL corridor_width_m")
    except Exception:                                          # noqa: BLE001
        put("red_sight_m", 74.5, "fallback")
        put("drum_r_m", 278.3, "fallback")
        put("drum_len_m", 2586.0, "fallback")
        put("drum_floor_m2", 2.0 * math.pi * 278.3 * 2586.0, "fallback")
        put("corridor_w_m", 2.6, "fallback")

    # A docking bay's deck: 42.0 m x 140.0 m, INV-022.
    try:
        import docking_bay as db                               # noqa: PLC0415
        put("dock_w_m", db.BAY_W_M, "station/docking_bay.py BAY_W_M")
        put("dock_l_m", db.BAY_LEN_M, "station/docking_bay.py BAY_LEN_M (INV-022)")
        put("dock_n", db.BAY_COUNT, "station/docking_bay.py BAY_COUNT")
    except Exception:                                          # noqa: BLE001
        put("dock_w_m", 42.0, "fallback")
        put("dock_l_m", 140.0, "fallback")
        put("dock_n", 24, "fallback")

    try:
        import council_chamber as cc                           # noqa: PLC0415
        put("council_r_m", cc.FLOOR_R_M, "station/council_chamber.py FLOOR_R_M")
    except Exception:                                          # noqa: BLE001
        put("council_r_m", 11.0, "fallback")
    return g


GEOM = _geometry()
BAY_M2 = GEOM["bay_w_m"] * GEOM["bay_l_m"]                    # 233.28
# A two-storey Zocalo-type bay: the ground floor plus the two gallery strips
# that flank the well. This is the unit FACTIONS.md 2.5's "six people at 05:00"
# turns out to be counting -- see the module docstring, finding (d).
BAY_2S_M2 = BAY_M2 + 2.0 * GEOM["gallery_m"] * GEOM["bay_l_m"]  # 330.48


# ---------------------------------------------------------------------------
# Areas
# ---------------------------------------------------------------------------
# FOUR ROUTES, and the route is data so a reader can tell them apart six
# sessions later. AAA-STANDARD scores an uncited dimension in code as FIDELITY
# 0 precisely because it is indistinguishable from memory later on.
#
#   GEOMETRY     computed from another module's dimensions
#   THROUGHPUT   from FACTIONS.md 2.3's arrival arithmetic
#   STAFFING     peak on-duty headcount (schedule.role_on_duty) / peak density
#   EXTRAPOLATED ours, authority 5, with the constraint and the overturn stated
#
# STAFFING deserves a warning. `area = demand / density` makes "the standing
# crowd never exceeds the staff on shift" a tautology for those places, so that
# check is applied to GEOMETRY and EXTRAPOLATED places only. What is NOT
# tautological for a staffing-routed place is whether the resulting floor fits
# inside the sector -- `report()` prints the total against the drum's own
# surface area for scale.
GEOMETRY = "geometry"
THROUGHPUT = "throughput"
STAFFING = "staffing"
EXTRAPOLATED = "extrapolated"

# Clustering models. A crowd is not a uniform scatter, and a uniform scatter is
# the single most obvious tell that a crowd is procedural.
CL_UNIFORM = "uniform"        # no attractor: maintenance runs, the drum floor
CL_PERIMETER = "perimeter"    # stalls, bars, counters: people hug the edges
CL_QUEUE = "queue"            # customs: a line down the middle of the hall
CL_SPINE = "spine"            # a corridor: people walk the centre line


@dataclass(frozen=True)
class Extent:
    """A place's floor, its room, and where both numbers came from.

    THREE quantities, and conflating any two of them is a modelling error this
    module made on its first pass:

      `area_m2`     total floor the density multiplies to give the place's
                    whole standing population.
      `rooms`       how many identical volumes that floor is divided into. The
                    docking bays are 24 rooms and the player stands in one;
                    pricing a frame against all 24 overstated the cost 24-fold.
      `width_m` x `length_m`  the footprint of ONE room, which is what the
                    spawner scatters people over and what the frustum is
                    clipped against.

    `floor_multiplier` is what is left over: total floor divided by
    rooms*width*length. It is 1.42 for the Zocalo, because 2.5 calls it
    "two-storey with an upper gallery" (authority 1) and a gallery is floor
    without footprint. It is 0.60 for the docking bays, because a bay deck has
    a ship on it. Both are meaning, not slop, so the number is kept rather than
    rounded away.
    """
    key: str
    area_m2: float
    width_m: float
    length_m: float
    rooms: int
    route: str
    source: str
    cluster: str = CL_UNIFORM
    roles: tuple = ()          # plausible roles; () = the whole station's mix

    @property
    def room_area_m2(self):
        return self.area_m2 / max(self.rooms, 1)

    @property
    def floor_multiplier(self):
        fp = self.width_m * self.length_m * max(self.rooms, 1)
        return self.area_m2 / fp if fp > 0 else 1.0


def _bays(n):
    """n Zocalo-type structural bays of ground floor."""
    return n * BAY_M2


def _peak_density(place_key):
    """Peak persons per m^2 for a place, from schedule.PLACES."""
    return sched.PLACES[place_key].peak_per_100m2 / 100.0


def _staffing_area(place_key, role_keys, share=1.0):
    """Floor implied by the peak on-duty headcount of the roles that work here.

    This is the honest way to size a workplace whose plan no source gives:
    the station knows how many people are on shift (FACTIONS.md 2.2's
    apportionment, through `schedule.role_on_duty`), and 2.5 states how densely
    they stand. The floor is the quotient. Round numbers do not appear.

    `share` is the fraction of the on-duty roster that is in THIS building. It
    is 1.0 for a furnace floor, where the shift is the place, and well under 1
    for Security Central: 2.2's whole argument is that 150 officers on duty
    across 8,047 m are "a garrison at chokepoints", so most of a watch is
    standing somewhere else and sizing the building on the whole watch would
    build a police station fourteen bays across.
    """
    peak = max(sum(sched.role_on_duty(r, float(h)) for r in role_keys)
               for h in range(24)) * share
    d = _peak_density(place_key)
    return ((peak / d) if d > 0 else 0.0), peak


_ZOC_BAYS = max(1, int(round(GEOM["red_sight_m"] / GEOM["bay_l_m"])))


def _build_extents():
    g = GEOM
    e = {}

    def add(*a, **kw):
        x = Extent(*a, **kw)
        e[x.key] = x

    # --- GEOMETRY ---------------------------------------------------------
    # The Zocalo is as long as you can see along it. That is not a stylistic
    # choice: past the curvature sight line the concourse is occluded by its
    # own ring, so a longer Zocalo would be a second room. 7 bays at 10.8 m.
    zl = _ZOC_BAYS * g["bay_l_m"]
    add("zocalo", _ZOC_BAYS * BAY_2S_M2, g["bay_w_m"], zl, 1, GEOMETRY,
        f"{_ZOC_BAYS} bays of {g['bay_w_m']:.1f}x{g['bay_l_m']:.1f} m plus two "
        f"{g['gallery_m']:.1f} m galleries; length = {g['red_sight_m']:.1f} m "
        f"curvature sight line ({g['red_sight_m__src']})",
        CL_PERIMETER, ("merchant", "service", "visitor", "refugee", "security",
                       "financier", "lurker", "engineer", "dockworker"))

    # 2.5 gives the Central Corridor the same architecture as the Zocalo in as
    # many words -- "two occupied levels in one volume", authority 1. So it
    # gets the Zocalo's section (well plus two galleries) and the same sight
    # line, and nothing new is invented for it.
    cw = g["well_w_m"] + 2.0 * g["gallery_m"]
    add("central_corridor", cw * g["red_sight_m"], cw, g["red_sight_m"], 1,
        GEOMETRY,
        f"well {g['well_w_m']:.1f} m + 2 galleries {g['gallery_m']:.1f} m over "
        f"the {g['red_sight_m']:.1f} m sight line; 2.5 gives it the Zocalo's "
        f"two-level section",
        CL_SPINE, ())

    # The docking bay deck, x24 -- and 24 ROOMS, not one 3,360 m long hall.
    # WALKABLE_FRAC is the one invented number here: a bay holds a ship, and
    # the deck under and around it is not all standable.
    WALKABLE_FRAC = 0.60
    add("docking_bays", g["dock_n"] * g["dock_w_m"] * g["dock_l_m"] * WALKABLE_FRAC,
        g["dock_w_m"], g["dock_l_m"], int(g["dock_n"]), GEOMETRY,
        f"{g['dock_n']} bays of {g['dock_w_m']:.0f}x{g['dock_l_m']:.0f} m deck "
        f"({g['dock_l_m__src']}) x {WALKABLE_FRAC:.2f} walkable",
        CL_PERIMETER, ("dockworker", "traffic", "visitor", "merchant", "security"))

    # Council Chamber floor is a measured disc; the approaches are not.
    add("council_chamber", math.pi * g["council_r_m"] ** 2 + _bays(2),
        2 * g["council_r_m"],
        (math.pi * g["council_r_m"] ** 2 + _bays(2)) / (2 * g["council_r_m"]),
        1, GEOMETRY,
        f"pi*{g['council_r_m']:.1f}^2 chamber ({g['council_r_m__src']}) plus "
        f"2 bays of approaches",
        CL_PERIMETER, ("diplomat", "security", "service", "visitor"))

    # 2.5: "two or three suited figures in a kilometre". A kilometre is the
    # length; the 5 m width is ours. 5,000 m^2 x 0.0005/m^2 = 2.5 figures,
    # which is the sentence, arrived at from the other end.
    add("yellow_maintenance", 1000.0 * 5.0, 5.0, 1000.0, 1, GEOMETRY,
        "1 km of run (2.5's 'in a kilometre') x 5 m walkway width "
        "(EXTRAPOLATED: two suit widths and a rail)",
        CL_UNIFORM, ("engineer", "industrial", "traffic"))

    # The habitat drum's developed townscape. 2.5 is explicit that the Garden
    # is "a townscape, not a park", authority 1. DEVELOPED_FRAC is authority 5
    # and it is the largest lever in this table: at 0.03 persons/m^2 the whole
    # 4.5 million m^2 inner surface would stand 135,000 people, which is 54% of
    # the station outdoors at once and absurd. 5% gives 6,800 at midday --
    # 2.7% of the population in the civic centre of a city of a quarter million.
    #
    # Shaped as a BAND around the drum rather than a patch, because the drum is
    # a ring: the developed strip runs the full 1,748 m circumference and is
    # 129 m deep. That shape is also the project's worst rendering case, since
    # looking ALONG the band there is no wall anywhere inside the subpixel
    # distance -- which is the whole reason the FLOCK tier exists.
    DEVELOPED_FRAC = 0.05
    dev = g["drum_floor_m2"] * DEVELOPED_FRAC
    circ = 2.0 * math.pi * g["drum_r_m"]
    add("the_garden", dev, dev / circ, circ, 1, GEOMETRY,
        f"{g['drum_floor_m2']/1e6:.2f} million m^2 drum inner surface "
        f"({g['drum_floor_m2__src']}) x {DEVELOPED_FRAC:.2f} developed, as a "
        f"{dev/circ:.0f} m deep band round the {circ:.0f} m circumference",
        CL_PERIMETER, ())

    # --- THROUGHPUT -------------------------------------------------------
    # 2.3: 120 souls per arrival across 2 halls. The hall is sized so that one
    # arrival wave fills it to the stated peak density and no more, which is
    # what "design the hall for a peak of 20-40/minute and long dead periods"
    # means in square metres. Two halls, north and south (authority 3).
    ca = sched.SOULS_PER_ARRIVAL / _peak_density("customs_halls")
    add("customs_halls", ca, 14.0, ca / sched.CUSTOMS_HALLS / 14.0,
        sched.CUSTOMS_HALLS, THROUGHPUT,
        f"{sched.SOULS_PER_ARRIVAL} souls per arrival (2.3) at the 2.5 peak "
        f"density of {_peak_density('customs_halls'):.2f}/m^2, across "
        f"{sched.CUSTOMS_HALLS} halls; 14 m hall width EXTRAPOLATED",
        CL_QUEUE, ("customs", "visitor", "refugee", "security", "merchant"))

    # --- STAFFING ---------------------------------------------------------
    # `share` and `rooms` are both authority 5 and both stated. `rooms` is
    # sourced where the source counts them: 90 Grey decks (STATE.md 2w), three
    # Medlabs (2.5), three crew facilities (mess, quartermaster, post office).
    for key, roles, share, rooms, width, cluster, note in (
        # `industrial` ONLY. Adding `engineer` doubled the floor to 1.06
        # million m^2, because schedule.py's 14,430 engineers work everywhere
        # on the station and Grey's fabrication shift is a subset of them. A
        # staffing route is only as good as the roles fed to it.
        ("industrial_grey", ("industrial",), 1.0, 90, 20.0, CL_UNIFORM,
         "Grey holds 90 of the station's 210 decks and is three shifts of "
         "fabrication, power and repair (2.5); the whole shift IS the floor"),
        ("hydroponics", ("hydroponics",), 1.0, 6, 40.0, CL_SPINE,
         "the agricultural shift 05:00-13:00 (2.5), over six growing halls"),
        ("medlab_one", ("medical",), 1.0 / 3.0, 3, 24.0, CL_PERIMETER,
         "one of Medlab 1-3 (2.5), so a third of the roster"),
        ("security_central", ("security",), 0.25, 1, 21.6, CL_PERIMETER,
         "2.2: ~150 on duty across 8,047 m is a garrison at chokepoints, so "
         "three quarters of a watch is standing somewhere that is not here"),
        ("business_district", ("financier",), 0.15, 8, 21.6, CL_PERIMETER,
         "the public concourse of the district; the leased offices behind it "
         "hold the other 85% and are not this floor"),
        ("crew_country", ("command", "traffic", "customs"), 1.0, 3, 21.6,
         CL_PERIMETER,
         "mess hall, quartermaster and post office (2.5) -- three rooms"),
    ):
        area, peak = _staffing_area(key, roles, share)
        add(key, area, width, area / rooms / width, rooms, STAFFING,
            f"peak on-duty {'+'.join(roles)} x {share:.2f} = {peak:,.0f} "
            f"(schedule.role_on_duty) / {_peak_density(key):.3f} per m^2 over "
            f"{rooms} rooms -- {note}",
            cluster,
            tuple(roles) + (("visitor", "merchant") if key in
                            ("business_district", "medlab_one", "crew_country")
                            else ()))

    # Downbelow is sized by its POPULATION rather than by a shift, because
    # 11.2's whole point is that it has no shift. PUBLIC_FRAC is the share of
    # the 20,390 lurkers who are in the shared corridors rather than in
    # whatever they sleep in -- authority 5, and it is the only lever.
    PUBLIC_FRAC = 0.40
    lurkers = sched.role_headcount()["lurker"]
    db_area = lurkers * PUBLIC_FRAC / _peak_density("downbelow")
    add("downbelow", db_area, 6.0, db_area / 40.0 / 6.0, 40, STAFFING,
        f"{lurkers:,} lurkers (schedule.role_headcount) x {PUBLIC_FRAC:.2f} in "
        f"public space / {_peak_density('downbelow'):.2f} per m^2, spread over "
        f"40 unfinished 6 m runs -- 11.2's 'undeveloped and unfinished areas, "
        f"mostly outer rings near the hull'",
        CL_PERIMETER, ("lurker", "refugee", "waste"))

    # --- EXTRAPOLATED -----------------------------------------------------
    # Every one of these is n structural bays. The bay is used as the unit
    # deliberately: it is the only interior module the project has actually
    # dimensioned, so an invented room is at least built out of a measured
    # brick, and changing the deck pitch moves all of them together.
    for key, nbays, rooms, width, cluster, roles, why in (
        ("earharts", 2.0, 1, 21.6, CL_PERIMETER,
         ("service", "security", "command", "traffic", "engineer", "visitor"),
         "one bar for a 6,500-strong EA complement; 2 bays stands 117 at peak, "
         "1.8% of the complement off duty in it at once"),
        ("dark_star", 1.5, 1, 16.0, CL_PERIMETER,
         ("service", "lurker", "dockworker", "merchant", "visitor"),
         "smaller and denser than Earhart's -- 2.5 gives it the highest peak "
         "density on the station and a rougher room is a tighter room"),
        ("casino", 3.0, 1, 21.6, CL_PERIMETER,
         ("service", "financier", "merchant", "visitor", "security"),
         "a gaming floor is bigger than a bar and smaller than the concourse"),
        ("law_courts", 3.0, 2, 16.0, CL_PERIMETER,
         ("diplomat", "security", "visitor", "merchant", "refugee"),
         "Ombuds hearings: a chamber and a waiting hall"),
        ("dock_workers_quarters", 8.0, 1, 6.0, CL_SPINE,
         ("dockworker", "traffic", "service"),
         "the circulation and mess of a quarter housing ~9,650 dock staff, not "
         "the cabins -- 2.5's density is a corridor density"),
        ("ambassadorial_suites", 12.86, 15, 12.0, CL_UNIFORM,
         ("diplomat", "service", "security"),
         "~15 suites of ~200 m^2; 2.5 puts 2 persons/100 m^2 in them, so this "
         "is residence, not reception"),
        ("alien_sector", 20.0, 6, 12.0, CL_PERIMETER,
         ("industrial", "dockworker", "merchant", "service", "diplomat"),
         "SIX rooms because 9.3 builds the sector as six atmosphere zones "
         "behind airlocks; the quarters behind the locks are not this floor"),
        ("markab_quarter", 3.0, 1, 12.0, CL_UNIFORM, (),
         "sealed, powered, unlit, still furnished. The area exists so the "
         "emptiness is a measured zero over a real floor rather than a "
         "missing entry"),
        ("fresh_air_restaurant", 3.0, 1, 21.6, CL_PERIMETER,
         ("service", "diplomat", "visitor", "merchant"),
         "an open terrace under the far side of the drum"),
        ("zen_garden", 2.0, 1, 21.6, CL_UNIFORM,
         ("cleric", "diplomat", "visitor"),
         "2.5 gives it 2 persons/100 m^2 -- quiet is the specification"),
        ("sanctuaries", 8.0, 4, 15.0, CL_PERIMETER,
         ("cleric", "visitor", "refugee", "lurker"),
         "FOUR rooms because Contract 5 counts four Sanctuaries at authority 3 "
         "(11.3), 2 bays each"),
    ):
        area = _bays(nbays)
        add(key, area, width, area / rooms / width, rooms, EXTRAPOLATED,
            f"{nbays:g} structural bays of {BAY_M2:.0f} m^2 over {rooms} "
            f"room(s) -- {why}", cluster, roles)
    return e


EXTENTS = _build_extents()


def extent(place_key: str) -> Extent:
    return EXTENTS[place_key]


def area_m2(place_key: str) -> float:
    return EXTENTS[place_key].area_m2


# ---------------------------------------------------------------------------
# Density and headcount
# ---------------------------------------------------------------------------
def density(place_key: str, hour: float) -> float:
    """Persons per square metre. schedule.density_at is per 100 m^2."""
    return sched.density_at(place_key, hour) / 100.0


def headcount(place_key: str, hour: float) -> int:
    """Whole people standing in a place at a station-clock hour, ALL rooms."""
    return int(round(density(place_key, hour) * area_m2(place_key)))


def room_headcount(place_key: str, hour: float) -> int:
    """Whole people in ONE of a place's rooms -- the room the player is in.

    The distinction is not pedantry: pricing a frame against all 24 docking
    bays at once overstates the visible crowd twenty-four fold, and spawning
    the whole Alien Sector into one atmosphere zone puts methane breathers in
    the amphibian room.
    """
    return int(round(density(place_key, hour) * extent(place_key).room_area_m2))


def species_headcount(place_key: str, hour: float, rooms: int = None) -> dict:
    """Whole people by species. Delegated so composition has one owner."""
    ex = extent(place_key)
    rooms = ex.rooms if rooms is None else rooms
    return sched.crowd_headcount(place_key, hour, ex.room_area_m2 * rooms)


def station_standing(hour: float) -> int:
    """Everyone in a NAMED place at this hour.

    Deliberately not the population: quarters, offices, lifts, cargo bays and
    every unnamed corridor are outside the place table, and the fraction this
    covers is itself a check -- see `_selftest`.
    """
    return sum(headcount(k, hour) for k in EXTENTS)


def awake_population(hour: float) -> int:
    counts = sched.population_activity(hour)
    return sched.RESIDENT_TOTAL - counts[sched.Activity.SLEEP]


# ---------------------------------------------------------------------------
# The gradient: transients skew alien, residents skew human
# ---------------------------------------------------------------------------
# FACTIONS.md 2.4: "the docks and customs are the most alien places on the
# station and Blue Sector crew country is the most human, which is exactly the
# gradient a player should feel while walking."
#
# This route is a walk a player can actually take: off a ship, through customs,
# along the bay galleries, past Medlab, into crew country. It is asserted
# MONOTONE at all 24 hours, which is a stronger claim than "the ends differ" and
# is the one that makes the gradient a felt thing rather than a statistic.
GRADIENT_ROUTE = ("customs_halls", "docking_bays", "medlab_one", "crew_country")


def alienness(place_key: str, hour: float) -> float:
    """1 - the human share of the standing crowd. 0 = crew country, 1 = Kosh."""
    mix = sched.crowd_at(place_key, hour)
    return 1.0 - mix.get("human", 0.0)


def gradient(hour: float, route=GRADIENT_ROUTE) -> tuple:
    return tuple(alienness(k, hour) for k in route)


def alienness_ranked(hour: float) -> list:
    """Every non-sealed place, most alien first."""
    return sorted(((alienness(k, hour), k) for k in EXTENTS
                   if not sched.PLACES[k].sealed), reverse=True)


@lru_cache(maxsize=1)
def transient_gradient_audit() -> dict:
    """Measure 2.4's stated gradient against schedule.ROLE_WEIGHTS.

    THIS IS A CHANGE DETECTOR, NOT A PREFERENCE. The finding it records is that
    `ROLE_WEIGHTS` gives transients a HIGHER human share than residents, which
    is the reverse of what FACTIONS.md 2.4 states. `_selftest` asserts the
    measurement still matches `verdict`, so whoever eventually fixes
    `ROLE_WEIGHTS` gets a failing test pointing at this docstring rather than a
    silent change of meaning.

    The fix, when someone takes it: human `visitor` is 31,000 of 44,770. For
    transients to skew alien against a 60.4% resident share it needs to be
    below ~27,000, i.e. ~5,000 humans moved from `visitor` into resident roles.
    """
    vis = {sp: w.get("visitor", 0) for sp, w in sched.ROLE_WEIGHTS.items()}
    t_total = sum(vis.values())
    t_human = vis.get("human", 0)
    r_total = sched.RESIDENT_TOTAL - t_total
    r_human = sched.STATION_COUNTS["human"] - t_human
    t_share = t_human / t_total
    r_share = r_human / r_total
    return {
        "transients": t_total, "transient_human_share": t_share,
        "residents": r_total, "resident_human_share": r_share,
        "factions_2_4_claims": "transients skew alien, residents skew human",
        "measured": ("transients skew HUMAN" if t_share > r_share
                     else "transients skew alien"),
        "verdict": "contradicts FACTIONS.md 2.4",
        "human_visitors_needed_for_2_4": int(r_share * t_total),
    }


# ---------------------------------------------------------------------------
# Simulation LOD
# ---------------------------------------------------------------------------
# The caps come from `schedule.NPC_BUDGET` rather than being re-chosen here;
# the radii are derived from them and from the density, which is the only way
# a cap and a radius can both be true at once.
FULL_SIM_RADIUS_M = sched.NPC_BUDGET["lod"][1][2]        # 18 m, LOD1's far edge
FULL_AGENT_CAP = sched.NPC_BUDGET["full_agents"]         # 500
CROWD_AGENT_CAP = sched.NPC_BUDGET["crowd_agents"]       # 2,000

# Existence is created outside the render horizon and destroyed further out
# still. The gap between the two is the hysteresis that stops a figure standing
# on the boundary from flickering; 35% and 50% because the player's walk speed
# (~1.4 m/s) has to be unable to cross the gap inside one streaming tick.
SPAWN_MARGIN = 1.35
DESPAWN_MARGIN = 1.50
TIER_HYSTERESIS = 0.08

# Frustum. 1440p, 16:9, 50 deg vertical -- the same figures body.py uses for its
# pixel-honesty schedules, restated here rather than imported so this module
# still prices a crowd when body.py is mid-edit.
SCREEN_H_PX = 1440
FOV_V_DEG = 50.0
ASPECT = 16.0 / 9.0

TIER_FULL = "full"
TIER_CROWD = "crowd"
TIER_FLOCK = "flock"
TIER_STATISTICAL = "statistical"


def _tan_half_h():
    return math.tan(math.radians(FOV_V_DEG) / 2.0) * ASPECT


def figure_px(distance_m: float, stature_m: float = 1.75) -> float:
    """Screen height of a person, in pixels, at 1440p."""
    if distance_m <= 0:
        return float(SCREEN_H_PX)
    return SCREEN_H_PX * (stature_m / distance_m) / (
        2.0 * math.tan(math.radians(FOV_V_DEG) / 2.0))


def frustum_floor_area(d0: float, d1: float, room_width_m: float) -> float:
    """Floor area between two depths, inside the frustum and inside the room.

    The band [d0,d1] is a trapezoid of width min(room, 2*d*tan(hfov/2)), so the
    area is the integral of that, NOT (d1-d0) times a constant. AAA-STANDARD
    scores a total divided by a length as PERFORMANCE 2, and spreading a crowd
    linearly in depth is the same error in a room: it puts figures on the lens.
    """
    t = _tan_half_h()
    sat = room_width_m / (2.0 * t) if room_width_m > 0 else float("inf")
    a = 0.0
    lo, hi = max(0.0, d0), max(0.0, d1)
    if hi <= lo:
        return 0.0
    if lo < sat:
        u = min(hi, sat)
        a += t * (u * u - lo * lo)
        lo = u
    if hi > lo:
        a += room_width_m * (hi - lo)
    return a


def crowd_radius(density_per_m2: float, cap: int = None,
                 room_width_m: float = 1e9) -> float:
    """Distance at which the crowd-agent cap is used up.

    Solved against the frustum floor rather than a disc: agents are only paid
    for where the camera can see them, and a 360-degree disc would overstate the
    cost by pi/(2 tan(hfov/2)) -- 1.9x -- and pull the radius in for no reason.
    """
    cap = CROWD_AGENT_CAP if cap is None else cap
    if density_per_m2 <= 0:
        return float("inf")
    need = cap / density_per_m2
    lo, hi = 0.0, 16.0
    while frustum_floor_area(0.0, hi, room_width_m) < need and hi < 1e6:
        hi *= 2.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if frustum_floor_area(0.0, mid, room_width_m) < need:
            lo = mid
        else:
            hi = mid
    # Clamped at the subpixel distance. Beyond it nobody is drawn at all, so an
    # unclamped radius is not a radius -- Yellow Sector's 0.0005 persons/m^2
    # printed a crowd horizon of 800 km, which is a true number about an empty
    # volume and a useless one about a crowd.
    return min(0.5 * (lo + hi), SUBPIXEL_M)


def visible_density(place_key: str, hour: float) -> float:
    """Persons per square metre OF FOOTPRINT -- what a frustum actually meets.

    Not the same as `density()`: a gallery puts a second floor of people over
    the same footprint, and a docking bay deck with a ship on it puts fewer.
    Costing a frame with the floor density instead of this one was a 42% error
    in the Zocalo and a 40% error the other way in the bays.
    """
    return density(place_key, hour) * extent(place_key).floor_multiplier


def peak_hour(place_key: str) -> float:
    return float(max(range(24), key=lambda h: density(place_key, float(h))))


def sim_tier(distance_m: float, place_key: str, hour: float) -> str:
    """Which simulation tier a figure at this distance belongs to."""
    if distance_m <= FULL_SIM_RADIUS_M:
        return TIER_FULL
    r = crowd_radius(visible_density(place_key, hour),
                     room_width_m=extent(place_key).width_m)
    if distance_m <= r:
        return TIER_CROWD
    if distance_m <= SUBPIXEL_M:
        return TIER_FLOCK
    return TIER_STATISTICAL


def spawn_radius(place_key: str, hour: float) -> float:
    r = crowd_radius(visible_density(place_key, hour),
                     room_width_m=extent(place_key).width_m)
    return r * SPAWN_MARGIN


def boundary_report(place_key: str, hour: float) -> dict:
    """What the player would see at each tier boundary. The anti-pop audit."""
    ex = extent(place_key)
    d = visible_density(place_key, hour)
    r = crowd_radius(d, room_width_m=ex.width_m)
    # How far you can see in this place at all. A room stops at its far wall;
    # the drum floor does not stop until a figure is one pixel high.
    sight = min(ex.length_m, SUBPIXEL_M)
    cost = visible_cost(place_key, hour)
    return {
        "place": place_key, "hour": hour, "density_per_m2": d,
        "full_radius_m": FULL_SIM_RADIUS_M,
        "mesh_horizon_m": cost["mesh_horizon_m"],
        "impostors_used": cost["impostors_used"],
        "px_at_mesh_horizon": (figure_px(cost["mesh_horizon_m"])
                               if cost["impostors_used"] else 0.0),
        "full_agents_at_radius": int(round(
            d * frustum_floor_area(0.0, FULL_SIM_RADIUS_M, ex.width_m))),
        "crowd_radius_m": r,
        "spawn_radius_m": r * SPAWN_MARGIN,
        "despawn_radius_m": r * DESPAWN_MARGIN,
        "sight_m": sight,
        "px_at_crowd_boundary": figure_px(min(r, sight)),
        # The only honest question about a boundary: is anything created there,
        # or only re-represented? Creation inside the sight line is a pop.
        "creates_inside_sight": r * SPAWN_MARGIN < sight,
        "needs_flock_tier": r < sight,
    }


# ---------------------------------------------------------------------------
# Render LOD
# ---------------------------------------------------------------------------
# body.py owns the per-figure triangle counts and derives its switch distances
# from pixel-honest silhouette, profile and feature error. This module does not
# second-guess any of that. What it adds is one thing body.py cannot know,
# because body.py prices ONE figure:
#
#   CROWD_LOD_OFFSET -- a figure standing in a crowd is mutually occluded and
#   carries no identity requirement, so it is drawn N levels coarser than a
#   lone figure at the same distance.
#
# EXTRAPOLATED, authority 5. Constrained by: without it a busy Zocalo costs
# 229,000 triangles against a 144,000 budget and there is no way to pay for it
# except by removing people, which fails the brief directly. Overturned by: a
# side-by-side render of the same crowd at offset 0 and offset 2 at 35 m in
# which the difference is visible -- which is a Godot-path comparison this
# container can set up but a human has to judge.
CROWD_LOD_OFFSET = 2
CROWD_OCCLUSION_N = 8        # below this many figures in a band, no offset

SUBPIXEL_M = 635.0           # a 1.75 m figure is 1 px at 1440p/50 deg
IMPOSTOR_TRIS = 2            # a camera-facing card

# Fallback chain, used only when body.py cannot be imported. Values are
# schedule.NPC_BUDGET's committed table, which is a coarser and more expensive
# chain than body.py's measured one -- so the fallback overstates cost and can
# never make a failing budget pass.
_FALLBACK_CHAIN = [{"name": n, "switch_distance_m": near, "used_to_m": far,
                    "tris": tris, "kind": "mesh"}
                   for n, near, far, tris, _cap in sched.NPC_BUDGET["lod"]]
_FALLBACK_CHAIN.append({"name": "impostor", "switch_distance_m": 400.0,
                        "used_to_m": SUBPIXEL_M, "tris": IMPOSTOR_TRIS,
                        "kind": "impostor"})


@lru_cache(maxsize=1)
def render_chain():
    """(levels, source). Each level: name, switch_distance_m, used_to_m, tris."""
    try:
        import body                                           # noqa: PLC0415
        chain = body.lod_chain()
        tri = body.level_triangles(chain)
        out = [{"name": lv["name"], "kind": lv["kind"],
                "switch_distance_m": lv["switch_distance_m"],
                "used_to_m": lv["used_to_m"],
                "tris": t["mean_mix"]}
               for lv, t in zip(chain, tri)]
        return out, "station/npc/body.py lod_chain + level_triangles (mix mean)"
    except Exception as exc:                                  # noqa: BLE001
        return list(_FALLBACK_CHAIN), f"fallback schedule.NPC_BUDGET ({exc})"


def _level_index(chain, distance_m):
    i = 0
    for j, lv in enumerate(chain):
        if distance_m >= lv["switch_distance_m"]:
            i = j
    return i


@lru_cache(maxsize=1)
def frame_budget():
    """Triangles NPCs may spend in one frame, and where the number comes from.

    Two committed modules disagree (finding (b) in the module docstring). The
    smaller wins: a budget that contradicts itself should bind at its tightest,
    and reporting against the looser one would mean this module passes a gate
    another module fails.
    """
    frame = sched.NPC_BUDGET["frame_triangles"]
    shares = {"schedule.NPC_BUDGET": sched.NPC_BUDGET["npc_frame_share"]}
    try:
        import body                                           # noqa: PLC0415
        shares["body.NPC_FRAME_SHARE"] = body.NPC_FRAME_SHARE
    except Exception:                                         # noqa: BLE001
        pass
    try:
        import budget                                         # noqa: PLC0415
        frame = budget.FRAME_TRIANGLES
    except Exception:                                         # noqa: BLE001
        pass
    share = min(shares.values())
    return {"frame_triangles": frame, "share": share,
            "triangles": int(frame * share), "shares": shares,
            "binding": min(shares, key=lambda k: shares[k])}


def visible_cost(place_key: str, hour: float, offset: int = None,
                 max_distance_m: float = None, mesh_horizon: bool = True) -> dict:
    """Figures and triangles in one frustum, banded by the render chain.

    The worst case a place can construct, not a convenient one: the camera
    stands at one end of the room looking down its length, and every figure in
    the frustum out to the far wall (or to the subpixel distance in an
    unoccluded volume) is counted.

    THREE THINGS THAT WERE WRONG ON THE FIRST PASS, all of which flattered the
    number and one of which flattered it by 24x:

      * the frustum was clipped against the whole facility rather than against
        ONE room, so a 24-bay dock was priced as a 3,360 m hall;
      * the density was the floor density, but a two-storey Zocalo puts 1.42
        floors over every square metre of footprint, and those people are in
        frame -- `floor_multiplier`;
      * a render band that STRADDLES the full-simulation radius was denied the
        crowd LOD offset entirely, which is where 100,000 triangles were
        hiding. Bands are now split at that radius.

    `mesh_horizon` is the mechanism every shipped crowd has and this one needs:
    meshes are drawn until the triangle budget runs out and everything beyond
    that distance is an impostor card. It is reported with the pixel height of
    a figure at that distance, because the honest question about a horizon is
    not whether the budget is met -- it always is -- but how big the thing is
    when it changes representation.
    """
    offset = CROWD_LOD_OFFSET if offset is None else offset
    chain, src = render_chain()
    ex = extent(place_key)
    d = visible_density(place_key, hour)
    far = min(ex.length_m if ex.length_m > 0 else SUBPIXEL_M, SUBPIXEL_M)
    if max_distance_m is not None:
        far = min(far, max_distance_m)
    r_crowd = crowd_radius(d, room_width_m=ex.width_m)
    budget = frame_budget()["triangles"]

    # Band edges: every chain switch, plus the full-simulation radius, plus the
    # far wall. Splitting at the radius is what lets the near half of a band be
    # drawn as an individual and the far half as a crowd.
    edges = sorted({0.0, far, FULL_SIM_RADIUS_M}
                   | {lv["switch_distance_m"] for lv in chain})
    edges = [x for x in edges if 0.0 <= x <= far]

    bands, tris, figs, horizon = [], 0.0, 0.0, far
    impostors = False
    for d0, d1 in zip(edges, edges[1:]):
        if d1 <= d0:
            continue
        area = frustum_floor_area(d0, d1, ex.width_m)
        n = area * d
        i = _level_index(chain, d0)
        use = i
        if n >= CROWD_OCCLUSION_N and d0 >= FULL_SIM_RADIUS_M:
            use = min(len(chain) - 1, i + offset)
        per = chain[use]["tris"]
        drawn = chain[use]["name"]
        if mesh_horizon and tris + n * per > budget and per > IMPOSTOR_TRIS:
            # Budget runs out inside this band. Everything nearer than the
            # crossing point stays mesh; everything beyond becomes a card.
            #
            # The cards are paid for FIRST. Solving the horizon against the
            # bare mesh budget and then adding the far field's 2 triangles
            # apiece overran by 0.3% -- small, and exactly the kind of quiet
            # overrun a gate exists to refuse.
            impostors = True
            cards = IMPOSTOR_TRIS * d * frustum_floor_area(d0, far, ex.width_m)
            spare = max(0.0, budget - tris - cards)
            n_mesh = spare / max(per - IMPOSTOR_TRIS, 1e-9)
            # invert the frustum area to find the distance that many figures
            # reach, by bisection -- the area function is monotone in d1.
            lo, hi = d0, d1
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if frustum_floor_area(d0, mid, ex.width_m) * d < n_mesh:
                    lo = mid
                else:
                    hi = mid
            horizon = 0.5 * (lo + hi)
            a_mesh = frustum_floor_area(d0, horizon, ex.width_m) * d
            a_card = n - a_mesh
            n_card = d * frustum_floor_area(horizon, far, ex.width_m)
            bands.append({"band": f"{drawn}", "d0": d0, "d1": horizon,
                          "area_m2": frustum_floor_area(d0, horizon, ex.width_m),
                          "figures": a_mesh, "drawn_as": drawn,
                          "tris_each": per, "triangles": a_mesh * per,
                          "tier": TIER_CROWD})
            bands.append({"band": "impostor", "d0": horizon, "d1": far,
                          "area_m2": frustum_floor_area(horizon, far, ex.width_m),
                          "figures": n_card, "drawn_as": "impostor",
                          "tris_each": IMPOSTOR_TRIS,
                          "triangles": IMPOSTOR_TRIS * n_card,
                          "tier": TIER_FLOCK})
            tris += a_mesh * per + IMPOSTOR_TRIS * n_card
            figs += a_mesh + n_card
            break
        bands.append({"band": lv_name(chain, i), "d0": d0, "d1": d1,
                      "area_m2": area, "figures": n, "drawn_as": drawn,
                      "tris_each": per, "triangles": n * per,
                      "tier": (TIER_FULL if d1 <= FULL_SIM_RADIUS_M else
                               TIER_CROWD if d1 <= r_crowd else TIER_FLOCK)})
        tris += n * per
        figs += n
    b = frame_budget()
    return {
        "place": place_key, "hour": hour, "source": src,
        "density_per_m2": d, "floor_multiplier": ex.floor_multiplier,
        "room_width_m": ex.width_m, "rooms": ex.rooms, "far_m": far,
        "figures": figs, "triangles": tris,
        "budget": b["triangles"], "share_of_frame": tris / b["frame_triangles"],
        "within_budget": tris <= b["triangles"],
        "mesh_horizon_m": horizon, "px_at_horizon": figure_px(horizon),
        "impostors_used": impostors,
        "crowd_radius_m": r_crowd,
        "agents_full": int(round(
            d * frustum_floor_area(0.0, FULL_SIM_RADIUS_M, ex.width_m))),
        "agents_crowd_wanted": int(round(
            d * frustum_floor_area(FULL_SIM_RADIUS_M, far, ex.width_m))),
        "agents_crowd_cap": CROWD_AGENT_CAP,
        "bands": bands,
    }


def lv_name(chain, i):
    return chain[i]["name"]


def required_frame_share(place_key: str, hour: float, to_m: float = None,
                         offset: int = None) -> float:
    """Frame share needed to hold MESHES all the way to `to_m`.

    The number the shortfall is stated in. Nothing in the pipeline consumes it;
    it exists so "the Zocalo does not fit" is a quantity rather than a mood.
    """
    c = visible_cost(place_key, hour, offset=offset, max_distance_m=to_m,
                     mesh_horizon=False)
    return c["triangles"] / c["budget"] * frame_budget()["share"]


def worst_case(hours=range(24), offset: int = None) -> dict:
    """The most expensive (place, hour) this module can construct."""
    best = None
    for k in EXTENTS:
        if sched.PLACES[k].sealed:
            continue
        for h in hours:
            c = visible_cost(k, float(h), offset=offset)
            if best is None or c["triangles"] > best["triangles"]:
                best = c
    return best


# ---------------------------------------------------------------------------
# Deterministic spawning
# ---------------------------------------------------------------------------
# NIGHTWATCH. FACTIONS.md 5.4: "150-200 of 500 (30-40%)" of security officers
# wear the armband at the datum, and 5.3/12 make the consequence the single best
# piece of environmental storytelling on the station: a two-officer patrol with
# one band and one bare sleeve, in the same uniform. Modelled as 5.4 requires --
# a per-NPC boolean, never a separate NPC type, so it can never cost a draw call.
NIGHTWATCH_SHARE = 0.35            # the midpoint of 5.4's stated 30-40%
# 5.4: "1,500-3,000 (1-2% of 155,000)" civilian informers. Invisible, and it is
# supposed to be: it exists so a denunciation event has someone to fire from.
INFORMER_SHARE = 0.015
# 10.1: "20-60 Rangers aboard at any time", authority 5 in the source. The tell
# is the brooch, and a player who learns to spot it starts seeing them.
RANGERS_ABOARD = 40
RANGER_P = RANGERS_ABOARD / sched.RESIDENT_TOTAL

# Personal space. EXTRAPOLATED: 0.55 m is a shoulder-width plus a margin, and it
# is the distance below which two proxy bodies interpenetrate. Constrained by
# body.py's figure width; overturned by a measured shoulder breadth per species.
PERSONAL_SPACE_M = 0.55
JITTER_FRAC = 0.30                 # of a cell; sets the guaranteed separation

POOL_OVERSAMPLE = 3                # candidate ids per seat, before role filter


@dataclass(frozen=True)
class Person:
    """One spawned individual. Everything is a function of (place, hour, seed)."""
    npc_id: str
    species: str
    role: str
    activity: str
    name: str
    x: float
    z: float
    distance_m: float
    tier: str
    armband: bool = False          # Nightwatch, security only (5.3)
    informer: bool = False         # civilian Nightwatch informer (5.4)
    ranger: bool = False           # the brooch (10.2)
    breather: str = "none"         # "none" | "mask" | "suit" (9.3)
    dress: str = "standard"        # "refugee" | "standard" (6.3's class gradient)


def pool_id(place_key: str, species: str, i: int, seed: str) -> str:
    """The id of the i'th regular of a species in a place.

    Stable across hours and days, which is what "the same corridor holds the
    same people" means. `i` indexes a pool, not a crowd: who of the pool is
    present at a given hour is decided separately, so a place gains and loses
    people rather than reshuffling them.
    """
    return f"crowd:{seed}:{place_key}:{species}:{i}"


@lru_cache(maxsize=2048)
def _pool_capacity(place_key: str, species: str) -> int:
    """How many of a species a place can ever hold, over the whole day.

    The pool has to be a property of the PLACE, not of the hour, or the
    regulars get re-cast every time the crowd changes size: ranking 10
    candidates and ranking 100 gives two different first five. That was a real
    defect in this module's first pass and the nesting assertion caught it.
    """
    peak = max(species_headcount(place_key, float(h)).get(species, 0)
               for h in range(24))
    return max(16, int(peak * 2))


@lru_cache(maxsize=4096)
def _pool(place_key: str, species: str, seed: str, want: int) -> tuple:
    """`want` ids of this species whose station role is plausible here.

    Rejection sampling over the id stream against the place's declared roles.
    Without it `schedule.role_for` -- which is a station-wide draw -- would put
    lurkers in the Council Chamber and diplomats on the furnace floor. With it,
    a place's crowd is made of people whose jobs explain why they are there.
    """
    allowed = set(EXTENTS[place_key].roles)
    out, i, guard = [], 0, want * POOL_OVERSAMPLE * 40 + 4096
    while len(out) < want and i < guard:
        nid = pool_id(place_key, species, i, seed)
        if not allowed or sched.role_for(nid, species).key in allowed:
            out.append(nid)
        i += 1
    # A species with no plausible role here still has to be spawnable, because
    # `crowd_headcount` may allocate it seats. Falling back to unfiltered ids is
    # better than returning short and silently losing people -- that is INV-005
    # in a different coat.
    while len(out) < want:
        out.append(pool_id(place_key, species, i, seed))
        i += 1
    return tuple(out)


def _present(place_key, species, n, seed, day):
    """Which n of the pool are in today. Nested: n+1 is n plus one person."""
    if n <= 0:
        return ()
    cap = max(_pool_capacity(place_key, species), n)
    pool = _pool(place_key, species, seed, cap)
    ranked = sorted(range(len(pool)),
                    key=lambda i: (_u(pool[i], f"day{day}"), i))
    return tuple(pool[i] for i in ranked[:n])


@lru_cache(maxsize=1024)
def _cell_grid(place_key):
    """A stratified grid over ONE room, and the separation it guarantees.

    Jittering inside a cell by +/-JITTER_FRAC/2 of the cell keeps every point at
    least (1 - JITTER_FRAC) of a cell from its neighbour, so minimum separation
    is a PROVEN property of the construction rather than a hope. A pure random
    scatter has no minimum separation at all and produces interpenetrating
    bodies at any density.

    The grid is sized to the room's BUSIEST hour and never to the hour being
    asked for. Two consequences, and both are wanted: positions are a prefix
    property, so a figure does not move when the crowd around it grows; and a
    half-empty room is a full grid half occupied, which is what a thinning
    crowd actually looks like rather than a shrunken one.
    """
    ex = EXTENTS[place_key]
    w, l = max(ex.width_m, 1e-6), max(ex.length_m, 1e-6)
    n = max(1, max(room_headcount(place_key, float(h)) for h in range(24)))
    cell = math.sqrt(w * l / n)
    nx = max(1, int(round(w / cell)))
    nz = max(1, int(math.ceil(n / nx)))
    return nx, nz, w / nx, l / nz


def _cell_weight(place_key, ix, iz, nx, nz):
    """Attraction of a cell. Higher = more likely occupied.

    Three models and no more, because a fourth would be decoration: people hug
    the edges of a room with stalls in it, queue down the middle of a customs
    hall, and walk the centre line of a corridor. Everything else is uniform.
    """
    cl = EXTENTS[place_key].cluster
    fx = (ix + 0.5) / nx - 0.5          # -0.5 .. +0.5 across the width
    if cl == CL_PERIMETER:
        return 0.35 + 1.30 * abs(fx) * 2.0
    if cl in (CL_QUEUE, CL_SPINE):
        return 0.30 + 1.40 * (1.0 - abs(fx) * 2.0)
    return 1.0


def place_positions(place_key: str, hour: float, n: int, seed: str = "b5") -> tuple:
    """(x, z) for the first `n` figures. INDEPENDENT OF TIER, by construction.

    This is the anti-pop guarantee in code: a FLOCK card at 200 m and the CROWD
    agent it is promoted into stand at the same coordinate, because both call
    this and neither passes a tier. `_selftest` asserts the prefix property --
    positions(n) is the first n of positions(m) for m > n -- which is what makes
    "promote the far crowd as the player walks" a swap of representation rather
    than a teleport.
    """
    if n <= 0:
        return ()
    nx, nz, cw, cl_ = _cell_grid(place_key)
    key = f"{place_key}|{seed}|{int(hour) % 24}"
    cells = []
    for iz in range(nz):
        for ix in range(nx):
            w = _cell_weight(place_key, ix, iz, nx, nz)
            # Weighted order statistic: u**(1/w) ranks high-weight cells first
            # in expectation without ever making the choice deterministic, and
            # it is stable, so growing n only ever adds cells.
            u = _u(key, f"cell{ix},{iz}")
            cells.append((u ** (1.0 / max(w, 1e-6)), ix, iz))
    cells.sort(reverse=True)
    out = []
    ex = EXTENTS[place_key]
    for k in range(min(n, len(cells))):
        _s, ix, iz = cells[k]
        jx = (_u(key, f"jx{ix},{iz}") - 0.5) * JITTER_FRAC * cw
        jz = (_u(key, f"jz{ix},{iz}") - 0.5) * JITTER_FRAC * cl_
        out.append(((ix + 0.5) * cw + jx - ex.width_m / 2.0,
                    (iz + 0.5) * cl_ + jz))
    return tuple(out)


def min_separation_m(place_key: str) -> float:
    """The separation the grid guarantees. Not measured -- constructed."""
    _nx, _nz, cw, cl_ = _cell_grid(place_key)
    return (1.0 - JITTER_FRAC) * min(cw, cl_)


def _name_for(species, nid):
    if npc_names is None:
        return ""
    try:
        return npc_names.name_for(species, nid)
    except Exception:                                          # noqa: BLE001
        return ""                # species with no attested name: INV-004's rule


def spawn(place_key: str, hour: float, seed: str = "b5", day: int = 0,
          limit: int = None, eye=(0.0, 0.0)) -> tuple:
    """Everyone standing in a place at an hour, as records.

    Deterministic in (place, hour, seed, day) and in nothing else -- not in
    iteration order, not in wall-clock, not in how many times it has been
    called. Two runs and two machines give the same people at the same
    coordinates with the same names.
    """
    p = sched.PLACES[place_key]
    if p.sealed:
        return ()
    # ONE room's worth. A place with 24 identical bays is 24 places to stand.
    heads = species_headcount(place_key, hour, rooms=1)
    n = sum(heads.values())
    if limit is not None:
        n = min(n, limit)
    if n <= 0:
        return ()
    # Positions are allocated for the FULL crowd and then truncated, so a
    # limited query returns a subset of the unlimited one rather than a
    # differently-packed room.
    full = sum(heads.values())
    pos = place_positions(place_key, hour, full, seed)
    ex = extent(place_key)
    d_place = density(place_key, hour)
    r_crowd = crowd_radius(d_place, room_width_m=ex.width_m)

    people, idx = [], 0
    for species in sorted(heads):
        for nid in _present(place_key, species, heads[species], seed, day):
            if idx >= len(pos):
                break
            x, z = pos[idx]
            idx += 1
            role = sched.role_for(nid, species).key
            rhythm = sched.RHYTHMS.get(species, sched.RHYTHMS["human"])
            breather = rhythm.breather
            # 9.3: the Alien Sector is reached through airlocks with breather-
            # mask dispensers "for most races", so an oxygen breather standing
            # in it is masked. The joke 9.3 records -- its residents call the
            # rest of the station the alien sector -- is this line, inverted.
            if place_key == "alien_sector" and breather == "none":
                breather = "mask"
            dist = math.hypot(x - eye[0], z - eye[1])
            people.append(Person(
                npc_id=nid, species=species, role=role,
                activity=sched.activity_at(nid, species, hour).value,
                name=_name_for(species, nid), x=x, z=z, distance_m=dist,
                tier=(TIER_FULL if dist <= FULL_SIM_RADIUS_M else
                      TIER_CROWD if dist <= r_crowd else TIER_FLOCK),
                armband=(role == "security" and _u(nid, "nightwatch") < NIGHTWATCH_SHARE),
                informer=(species == "human" and role != "security"
                          and _u(nid, "informer") < INFORMER_SHARE),
                ranger=_u(nid, "ranger") < RANGER_P,
                breather=breather,
                dress=("refugee" if role in ("refugee", "lurker") else "standard"),
            ))
            if len(people) >= n:
                break
        if len(people) >= n:
            break
    return tuple(people)


# ---------------------------------------------------------------------------
# Proxy geometry -- for looking at, not for shipping
# ---------------------------------------------------------------------------
# body.py owns the real bodies. These are three boxes, 36 triangles, and they
# exist for one reason: `tools/preview_render.py` cannot show a number, and
# crowdedness is a thing you have to LOOK at. They are written to a scratch OBJ
# and never into station/generated.
#
# WINDING. Every box is emitted with outward normals and positive signed volume
# -- asserted, because four separate subsystems in this project have shipped
# invisible geometry from getting this wrong and a render shows black either
# way. The preview room's floor faces UP, its walls face INTO the room and its
# ceiling faces DOWN, which is the convention CLAUDE.md sets for a surface seen
# from inside.
FIG_SHOULDER_M = 0.45
FIG_DEPTH_M = 0.25
FIG_HEAD_M = 0.20
FIG_STATURE_M = 1.75
FIG_TRIS = 36


def _box(v, t, x0, y0, z0, x1, y1, z1):
    """A closed box with outward normals. 12 triangles.

    The winding was wrong on the first pass -- signed volume -0.152 m^3, i.e.
    every one of the 36 triangles inside out -- and a render would have shown
    the figures perfectly, lit from the wrong side, because backface culling
    hides an inverted solid only when you are outside it. The assertion caught
    it; the picture would not have.
    """
    i = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
          (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2), (0, 2, 3),            # bottom, outward -Y
         (4, 6, 5), (4, 7, 6),            # top, outward +Y
         (0, 5, 1), (0, 4, 5),            # -Z
         (1, 6, 2), (1, 5, 6),            # +X
         (2, 7, 3), (2, 6, 7),            # +Z
         (3, 4, 0), (3, 7, 4)]            # -X
    t += [(i + a, i + b, i + c) for a, b, c in f]


def _quad(v, t, p0, p1, p2, p3):
    """One quad, normal by the right-hand rule on (p0,p1,p2)."""
    i = len(v)
    v += [p0, p1, p2, p3]
    t += [(i, i + 1, i + 2), (i, i + 2, i + 3)]


def figure_geometry(person, v, t):
    """Three boxes: legs, torso, head. 36 triangles, outward-facing."""
    hw, hd = FIG_SHOULDER_M / 2.0, FIG_DEPTH_M / 2.0
    x, z = person.x, person.z
    _box(v, t, x - hw * 0.8, 0.0, z - hd, x + hw * 0.8, 0.85, z + hd)
    _box(v, t, x - hw, 0.85, z - hd, x + hw, 1.45, z + hd)
    h = FIG_HEAD_M / 2.0
    _box(v, t, x - h, 1.55, z - h, x + h, 1.55 + FIG_HEAD_M, z + h)


def signed_volume(verts, tris) -> float:
    s = 0.0
    for a, b, c in tris:
        pa, pb, pc = verts[a], verts[b], verts[c]
        s += (pa[0] * (pb[1] * pc[2] - pb[2] * pc[1])
              - pa[1] * (pb[0] * pc[2] - pb[2] * pc[0])
              + pa[2] * (pb[0] * pc[1] - pb[1] * pc[0]))
    return s / 6.0


def facing_fraction(verts, tris, eye) -> float:
    """Fraction of triangles whose outward normal faces the eye.

    The same test `tools/preview_render.py` culls with. Reading a render cannot
    tell inside-out geometry from a dark room; this can.
    """
    n_ok = 0
    for a, b, c in tris:
        pa, pb, pc = verts[a], verts[b], verts[c]
        u = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
        w = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
        nx = u[1] * w[2] - u[2] * w[1]
        ny = u[2] * w[0] - u[0] * w[2]
        nz = u[0] * w[1] - u[1] * w[0]
        cx = (pa[0] + pb[0] + pc[0]) / 3.0
        cy = (pa[1] + pb[1] + pc[1]) / 3.0
        cz = (pa[2] + pb[2] + pc[2]) / 3.0
        if (nx * (eye[0] - cx) + ny * (eye[1] - cy) + nz * (eye[2] - cz)) > 0:
            n_ok += 1
    return n_ok / max(len(tris), 1)


def preview_room(place_key, height_m=5.0, ceiling=True):
    """Floor, walls and ceiling for a place's footprint. Scaffolding only.

    Explicitly NOT station geometry and never written into station/generated:
    it exists so a crowd has a floor to stand on in a preview render. The real
    rooms come from interior_kit, zocalo.py and the rest.
    """
    ex = EXTENTS[place_key]
    hw, ln = ex.width_m / 2.0, min(ex.length_m, 400.0)
    v, t = [], []
    # Floor: normal +Y. CLAUDE.md's rule for a flat surface is that it faces UP,
    # and getting it backwards renders a black hole in the deck that reads as
    # missing geometry rather than as inverted geometry.
    _quad(v, t, (-hw, 0.0, 0.0), (-hw, 0.0, ln), (hw, 0.0, ln), (hw, 0.0, 0.0))
    groups = [("floor", 0, len(t))]
    a = len(t)
    # Side walls, facing INTO the room: the +X wall's normal points -X.
    _quad(v, t, (hw, 0.0, 0.0), (hw, 0.0, ln), (hw, height_m, ln),
          (hw, height_m, 0.0))
    _quad(v, t, (-hw, 0.0, ln), (-hw, 0.0, 0.0), (-hw, height_m, 0.0),
          (-hw, height_m, ln))
    # End wall at the far end, facing back down the room (-Z).
    _quad(v, t, (-hw, 0.0, ln), (-hw, height_m, ln), (hw, height_m, ln),
          (hw, 0.0, ln))
    groups.append(("wall", a, len(t)))
    if ceiling:
        a = len(t)
        # Ceiling: normal -Y, seen from underneath.
        _quad(v, t, (-hw, height_m, 0.0), (hw, height_m, 0.0),
              (hw, height_m, ln), (-hw, height_m, ln))
        groups.append(("ceiling", a, len(t)))
    return v, t, groups


def crowd_obj(path, place_key, hour, seed="b5", room=True, height_m=5.0,
              limit=None):
    """Write a preview OBJ of a place's crowd. Returns a summary dict."""
    people = spawn(place_key, hour, seed, limit=limit)
    v, t, groups = ([], [], []) if not room else preview_room(place_key, height_m)
    by_species = {}
    for p in people:
        by_species.setdefault(p.species, []).append(p)
    for sp in sorted(by_species):
        a = len(t)
        for p in by_species[sp]:
            figure_geometry(p, v, t)
        groups.append((f"npc_{sp}", a, len(t)))
    with open(path, "w") as f:
        f.write(f"# crowd preview: {place_key} at {hour:04.1f} h, "
                f"{len(people)} figures, seed {seed}\n")
        for x, y, z in v:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for name, a, b in groups:
            f.write(f"g {name}\n")
            for i in range(a, b):
                p, q, r = t[i]
                f.write(f"f {p+1} {q+1} {r+1}\n")
    return {"path": path, "place": place_key, "hour": hour,
            "figures": len(people), "triangles": len(t),
            "species": {k: len(x) for k, x in sorted(by_species.items())},
            "groups": [g[0] for g in groups]}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(out=print):
    b = frame_budget()
    out("CROWD -- density, composition and cost")
    out("=" * 78)
    out(f"datum: S3 pre-martial-law (FACTIONS.md 1.3, via schedule.py)")
    out(f"frame budget: {b['triangles']:,} tri "
        f"({b['share']:.0%} of {b['frame_triangles']:,}) "
        f"-- binding source {b['binding']}")
    for k, v in sorted(b["shares"].items()):
        out(f"    {k:34s} {v:.2f}")
    chain, src = render_chain()
    out(f"render chain: {len(chain)} levels from {src}")

    out("\nFLOOR AREAS")
    out(f"  {'place':24s} {'area m2':>10s}  {'peak':>6s} {'route':12s} width x length")
    tot = 0.0
    for k in sorted(EXTENTS, key=lambda k: -EXTENTS[k].area_m2):
        e = EXTENTS[k]
        tot += e.area_m2
        peak = max(headcount(k, float(h)) for h in range(24))
        out(f"  {k:24s} {e.area_m2:10,.0f}  {peak:6,d} {e.route:12s} "
            f"{e.width_m:.0f} x {e.length_m:.0f} m")
    out(f"  {'TOTAL':24s} {tot:10,.0f} m2 = "
        f"{tot / GEOM['drum_floor_m2'] * 100:.1f}% of the drum's inner surface")

    out("\nCROWDEDNESS AND ISOLATION -- the two poles")
    rows = []
    for k in EXTENTS:
        if sched.PLACES[k].sealed:
            continue
        ds = [density(k, float(h)) for h in range(24)]
        rows.append((max(ds), min(ds), k))
    rows.sort(reverse=True)
    for mx, mn, k in rows[:3] + rows[-3:]:
        hh = max(range(24), key=lambda h: density(k, float(h)))
        out(f"  {k:24s} peak {mx:7.4f}/m2 at {hh:02d}:00, "
            f"trough {mn:7.4f}/m2  ({mx/max(mn,1e-9):.0f}x)")

    out("\nTHE ALIENNESS GRADIENT (13:00) -- 1 - human share")
    for a, k in alienness_ranked(13.0)[:4]:
        out(f"  most alien   {k:24s} {a:.3f}")
    for a, k in alienness_ranked(13.0)[-3:]:
        out(f"  most human   {k:24s} {a:.3f}")
    out(f"  walk {' -> '.join(GRADIENT_ROUTE)}")
    out(f"       {['%.3f' % x for x in gradient(13.0)]}")
    aud = transient_gradient_audit()
    out(f"  AUDIT: transients {aud['transient_human_share']:.3f} human, "
        f"residents {aud['resident_human_share']:.3f} -- {aud['measured']}, "
        f"{aud['verdict']}")

    out("\nSIMULATION LOD -- radii, caps and what happens at the boundary")
    for k, h in (("zocalo", 20.0), ("the_garden", 13.0), ("dark_star", 23.0),
                 ("yellow_maintenance", 3.0), ("industrial_grey", 3.0)):
        r = boundary_report(k, h)
        out(f"  {k:20s} {h:04.1f}h  rho {r['density_per_m2']:.4f}/m2  "
            f"full<= {r['full_radius_m']:.0f} m ({r['full_agents_at_radius']:3d} "
            f"agents)  crowd<= {r['crowd_radius_m']:6.1f} m  "
            f"spawn {r['spawn_radius_m']:6.1f} m  sight {r['sight_m']:6.1f} m  "
            f"{'FLOCK needed' if r['needs_flock_tier'] else 'room ends first'}")
        out(f"  {'':20s}        impostors "
            + (f"from {r['mesh_horizon_m']:.1f} m, where a figure is "
               f"{r['px_at_mesh_horizon']:.0f} px"
               if r["impostors_used"] else "never used -- meshes to the wall"))

    out("\nWORST-CASE COST  (uncapped = every figure a mesh; capped = with the "
        "mesh horizon)")
    for k, h in (("zocalo", 20.0), ("the_garden", 13.0), ("dark_star", 23.0),
                 ("customs_halls", None)):
        if h is None:
            h = peak_hour(k)
        for off in (0, CROWD_LOD_OFFSET):
            u = visible_cost(k, h, offset=off, mesh_horizon=False)
            c = visible_cost(k, h, offset=off)
            out(f"  {k:20s} {h:04.1f}h offset {off}: "
                f"{u['figures']:8.1f} figures, uncapped {u['triangles']:9,.0f} "
                f"({u['triangles']/u['budget']*100:5.1f}%) "
                f"{'PASS' if u['within_budget'] else 'OVER'}"
                f" -> capped {c['triangles']:9,.0f}"
                + (f" with cards from {c['mesh_horizon_m']:.0f} m"
                   if c["impostors_used"] else " (no cards needed)"))
        out(f"  {'':20s}        to hold meshes across the whole room needs "
            f"{required_frame_share(k, h):.1%} of the frame; it has "
            f"{frame_budget()['share']:.0%}")
    w = worst_case()
    out(f"  worst overall: {w['place']} at {w['hour']:04.1f}h -- "
        f"{w['triangles']:,.0f} tri, {w['figures']:,.0f} figures, "
        f"{'within' if w['within_budget'] else 'OVER'} budget")
    for band in w["bands"]:
        out(f"      {band['band']:8s} {band['d0']:6.1f}-{band['d1']:6.1f} m  "
            f"{band['figures']:8.1f} fig as {band['drawn_as']:9s} "
            f"{band['tris_each']:7.1f} tri  -> {band['triangles']:9,.0f}  "
            f"[{band['tier']}]")
    out(f"  agents wanted beyond {FULL_SIM_RADIUS_M:.0f} m: "
        f"{w['agents_crowd_wanted']:,} against a {CROWD_AGENT_CAP:,} cap -- "
        f"{'FLOCK tier carries the rest' if w['agents_crowd_wanted'] > CROWD_AGENT_CAP else 'inside cap'}")
    return {"total_area_m2": tot, "worst": w, "budget": b}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
_results = []


def check(name, ok, detail=""):
    _results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def _selftest():
    del _results[:]

    # =====================================================================
    # 1. AREAS -- the multiplier that turns a density into a crowd
    # =====================================================================
    check("every place in schedule.PLACES has a floor area",
          set(EXTENTS) == set(sched.PLACES),
          f"missing {sorted(set(sched.PLACES) - set(EXTENTS))}, "
          f"extra {sorted(set(EXTENTS) - set(sched.PLACES))}")
    check("every area is positive and finite",
          all(0 < e.area_m2 < 1e9 for e in EXTENTS.values()))
    # A fallback area is a number with no provenance, which AAA-STANDARD scores
    # FIDELITY 0. If an import broke, this fails rather than quietly passing.
    fell_back = [k for k, v in GEOM.items()
                 if k.endswith("__src") and v == "fallback"]
    check("no geometry source fell back to a typed constant",
          not fell_back, str(fell_back))
    check("every area carries a declared route",
          all(e.route in (GEOMETRY, THROUGHPUT, STAFFING, EXTRAPOLATED)
              for e in EXTENTS.values()))
    check("every area carries a source sentence",
          all(len(e.source) > 30 for e in EXTENTS.values()))

    # The Zocalo's length is the curvature sight line, not a chosen number.
    check("the Zocalo is as long as Red's ring lets you see",
          abs(EXTENTS["zocalo"].length_m - GEOM["red_sight_m"]) <= GEOM["bay_l_m"] / 2,
          f"{EXTENTS['zocalo'].length_m:.1f} m vs sight {GEOM['red_sight_m']:.1f} m")

    # FACTIONS.md 2.5: "at 05:00 it is a lit hall with six people in it". With
    # the derived area that is a BAY count, not a building count. Asserting the
    # prose literally would have forced a 375 m^2 Zocalo, which cannot be the
    # main social space of a quarter-million-person station.
    bay5 = density("zocalo", 5.0) * BAY_2S_M2
    check("2.5's 'six people at 05:00' lands in one Zocalo bay",
          4.0 <= bay5 <= 8.0,
          f"{bay5:.1f} in a {BAY_2S_M2:.0f} m2 two-storey bay; "
          f"{headcount('zocalo', 5.0)} in the whole hall")

    # The customs hall is sized by 2.3's arithmetic, so one wave fills it.
    peak_customs = max(headcount("customs_halls", float(h) / 4.0)
                       for h in range(96))
    check("a customs wave is one arrival's souls",
          abs(peak_customs - sched.SOULS_PER_ARRIVAL) <= 2,
          f"{peak_customs} vs {sched.SOULS_PER_ARRIVAL} souls per arrival")

    # =====================================================================
    # 2. DENSITY -- sums, emptiness, saturation
    # =====================================================================
    # NOT a tautology: this compares two independently-built models. The place
    # table is FACTIONS.md 2.5's prose; the awake count comes from fifteen
    # species rhythms and a role table. Nothing ties them together, so the
    # ratio is free to be absurd and is asserted not to be.
    ratios = []
    for h in range(24):
        aw = awake_population(float(h))
        ratios.append(station_standing(float(h)) / aw)
    check("named places hold a plausible share of the awake population",
          all(0.02 <= r <= 0.45 for r in ratios),
          f"{min(ratios):.3f} - {max(ratios):.3f} of awake")
    check("the standing population breathes over the day",
          max(ratios) / min(ratios) > 1.15,
          f"{max(ratios)/min(ratios):.2f}x between the quietest and busiest hour")

    sealed = [k for k in EXTENTS if sched.PLACES[k].sealed]
    check("exactly one place is sealed, and it is the Markab quarter",
          sealed == ["markab_quarter"], str(sealed))
    check("the sealed quarter is empty at every hour of the day",
          all(headcount("markab_quarter", float(h)) == 0 for h in range(24))
          and spawn("markab_quarter", 13.0) == ())

    empty = [k for k in EXTENTS if not sched.PLACES[k].sealed
             and max(headcount(k, float(h)) for h in range(24)) < 1]
    check("no unsealed place is empty at every hour", not empty, str(empty))

    # Saturation, defined against body.py's crush density rather than against a
    # place's own peak: "always at its stated peak" is a legitimate description
    # of a 24-hour operation, but "always at crush" is a room nobody can walk
    # through. 0.45/m^2 is body.DENSITY_PER_M2["crush"].
    CRUSH = 0.45
    over = [(k, max(density(k, float(h)) for h in range(24)))
            for k in EXTENTS
            if max(density(k, float(h)) for h in range(24)) > CRUSH]
    check("no place is saturated at any hour, let alone all of them",
          not over, str(over))

    # A place whose density never changes must have DECLARED that. This is the
    # assertion that would catch `_band_distance` returning a constant: if the
    # band arithmetic broke, every place would go flat and the declared set
    # would no longer match.
    flat_measured = {k for k in EXTENTS if not sched.PLACES[k].sealed
                     and len({round(density(k, float(h)), 9)
                              for h in range(24)}) == 1}
    # A wave-driven hall declares 24-hour "busy" bands and is still not flat --
    # `wave_pulse` empties it between arrivals, which is the whole character of
    # the room (2.3: "heaving for 5.2 h of the 24"). So it is excluded from the
    # declared-flat set by its own `waves` flag rather than by a special case.
    flat_declared = {k for k, p in sched.PLACES.items() if not p.sealed
                     and not p.waves and (p.flat or p.busy == ((0.0, 24.0),))}
    check("every place with a flat 24-hour density declared itself flat",
          flat_measured == flat_declared,
          f"measured {sorted(flat_measured - flat_declared)} undeclared, "
          f"{sorted(flat_declared - flat_measured)} declared but varying")
    check("most places are not flat -- the station has a day",
          len(flat_measured) < len(EXTENTS) / 2,
          f"{len(flat_measured)} flat of {len(EXTENTS)}")

    # The two poles the brief names, measured.
    zoc = density("zocalo", 20.0)
    grey03 = density("industrial_grey", 3.0)
    yellow = density("yellow_maintenance", 3.0)
    check("the crowded pole and the isolated pole differ by >100x",
          max(zoc, density("dark_star", 23.0)) / yellow > 100.0,
          f"Dark Star 23:00 {density('dark_star', 23.0):.4f}/m2 vs Yellow "
          f"{yellow:.5f}/m2 = {density('dark_star', 23.0)/yellow:.0f}x")
    check("a Grey corridor at 03:00 is countable on one hand over a sight line",
          1 <= grey03 * GEOM["corridor_w_m"] * GEOM["red_sight_m"] <= 8,
          f"{grey03 * GEOM['corridor_w_m'] * GEOM['red_sight_m']:.1f} people in "
          f"{GEOM['corridor_w_m']:.1f} x {GEOM['red_sight_m']:.0f} m")

    # Composition has to sum, or the population leaks -- INV-005's failure in a
    # different place. crowd_headcount apportions by largest remainder; this
    # asserts the result against the density model that produced the total.
    bad = []
    for k in EXTENTS:
        if sched.PLACES[k].sealed:
            continue
        for h in (3.0, 8.0, 13.0, 20.0):
            n = headcount(k, h)
            s = sum(species_headcount(k, h).values())
            if s != n:
                bad.append((k, h, n, s))
    check("species headcounts sum to the place headcount, exactly",
          not bad, str(bad[:4]))

    # =====================================================================
    # 3. THE GRADIENT
    # =====================================================================
    nonmono = [h for h in range(24)
               if list(gradient(float(h))) != sorted(gradient(float(h)),
                                                     reverse=True)]
    check("alienness falls monotonically along the customs-to-crew walk, "
          "at all 24 hours", not nonmono,
          f"breaks at {nonmono}; 13:00 = {['%.3f' % x for x in gradient(13.0)]}")
    check("the walk spans a real difference, not a rounding one",
          gradient(13.0)[0] - gradient(13.0)[-1] > 0.35,
          f"{gradient(13.0)[0]:.3f} -> {gradient(13.0)[-1]:.3f}")
    ranked = alienness_ranked(13.0)
    check("the Alien Sector is the most alien place aboard",
          ranked[0][1] == "alien_sector", ranked[0][1])
    general = [k for _a, k in ranked
               if k not in ("alien_sector", "ambassadorial_suites",
                            "council_chamber")]
    check("of the places anyone can walk into, customs is the most alien",
          general[0] == "customs_halls", general[0])
    check("crew country is the most human place a civilian sees",
          ranked[-1][1] in ("security_central", "yellow_maintenance")
          and "crew_country" in [k for _a, k in ranked[-4:]],
          str([k for _a, k in ranked[-4:]]))
    # The change detector for finding (a). See transient_gradient_audit().
    aud = transient_gradient_audit()
    check("AUDIT: schedule.ROLE_WEIGHTS still contradicts FACTIONS.md 2.4",
          aud["measured"] == "transients skew HUMAN",
          f"transients {aud['transient_human_share']:.3f} human vs residents "
          f"{aud['resident_human_share']:.3f} -- if this now fails, someone "
          f"fixed ROLE_WEIGHTS and this assertion should be deleted")

    # =====================================================================
    # 4. DETERMINISM
    # =====================================================================
    a = spawn("zocalo", 20.0, "seed-a")
    b = spawn("zocalo", 20.0, "seed-a")
    check("the same corridor holds the same people on two calls",
          a == b and len(a) > 50, f"{len(a)} people")
    c = spawn("zocalo", 20.0, "seed-b")
    check("a different seed gives different people",
          {p.npc_id for p in a} != {p.npc_id for p in c},
          f"{len(set(p.npc_id for p in a) & set(p.npc_id for p in c))} shared")
    # str.__hash__ is salted per process, so a module using it produces a
    # different crowd every run. Two subprocesses at different PYTHONHASHSEEDs
    # is the only test that can see that, and session 2n needed it.
    src = ("import sys;sys.path.insert(0,%r);import crowd;"
           "p=crowd.spawn('zocalo',20.0,'x');"
           "print(len(p),p[0].npc_id,p[0].name,round(p[0].x,6),round(p[0].z,6),"
           "sum(1 for q in p if q.armband))" % _HERE)
    outs = []
    try:
        import subprocess
        for hs in ("0", "1", "12345"):
            env = dict(os.environ, PYTHONHASHSEED=hs)
            outs.append(subprocess.run([sys.executable, "-c", src], env=env,
                                       capture_output=True, text=True,
                                       timeout=600).stdout.strip())
    except Exception as exc:                                   # noqa: BLE001
        outs = [f"subprocess failed: {exc}"]
    check("identical across PYTHONHASHSEED 0, 1 and 12345",
          len(set(outs)) == 1 and outs[0] and "failed" not in outs[0],
          " | ".join(outs))
    # Parsed, not grepped. A substring search finds this module's own prose
    # about not using `str.__hash__` and fails on a clean file, and a check
    # that cannot pass is a check that gets deleted. The AST sees only code.
    import ast
    tree = ast.parse(open(__file__).read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits += [a.name for a in node.names if a.name == "random"]
        elif isinstance(node, ast.ImportFrom) and node.module == "random":
            hits.append("from random")
        elif isinstance(node, ast.Attribute) and node.attr == "__hash__":
            hits.append("__hash__ attribute access")
    check("no use of random or the salted str hash anywhere in the code",
          not hits, str(hits))
    # Deliberately broken: the same scan over a snippet that DOES use them must
    # find both, or the scanner is looking at the wrong node types.
    probe = ast.parse("import random\nx = 'a'.__hash__()\n")
    found = sum(1 for n in ast.walk(probe)
                if (isinstance(n, ast.Import)
                    and any(a.name == "random" for a in n.names))
                or (isinstance(n, ast.Attribute) and n.attr == "__hash__"))
    check("and that scan can actually see them when they are there",
          found == 2, f"{found} of 2 found in the probe")

    # Pool nesting: a place gains people, it does not reshuffle them. Without
    # this the crowd would re-cast itself every hour and the Zocalo would never
    # have a regular.
    p5 = _present("zocalo", "human", 5, "s", 0)
    p50 = _present("zocalo", "human", 50, "s", 0)
    check("a bigger crowd contains the smaller one, person for person",
          p5 == p50[:5], f"{p5[:2]} vs {p50[:2]}")
    check("a different day re-casts the regulars",
          _present("zocalo", "human", 5, "s", 1) != p5)

    # The anti-pop guarantee, asserted rather than described.
    pos20 = place_positions("zocalo", 20.0, 20)
    pos200 = place_positions("zocalo", 20.0, 200)
    check("positions do not depend on how many were asked for",
          pos20 == pos200[:20], f"{pos20[:1]} vs {pos200[:1]}")
    lim = spawn("zocalo", 20.0, "seed-a", limit=10)
    check("a limited spawn is a subset of the full one, at the same coordinates",
          all(q in a for q in lim) and len(lim) == 10)

    # =====================================================================
    # 5. PLACEMENT
    # =====================================================================
    worst_gap = None
    for k, h in (("zocalo", 20.0), ("dark_star", 23.0), ("customs_halls", 0.0),
                 ("central_corridor", 8.0), ("earharts", 21.0)):
        pts = place_positions(k, h, min(room_headcount(k, h), 400))
        if len(pts) < 2:
            continue
        gap = min(math.dist(pts[i], pts[j])
                  for i in range(len(pts)) for j in range(i + 1, len(pts)))
        want = min_separation_m(k)
        if worst_gap is None or gap - want < worst_gap[1] - worst_gap[2]:
            worst_gap = (k, gap, want)
    # HONEST LIMIT, found by breaking it: `min_separation_m` is derived from
    # JITTER_FRAC, so setting JITTER_FRAC = 1.2 moves the measurement and the
    # bound together and this assertion survives it. It still catches a
    # placement that ignores the grid -- which is the class of bug it is for --
    # but it is the ABSOLUTE check below that catches a grid whose guarantee is
    # too weak to keep two bodies apart. Both are needed; neither is enough.
    check("no two figures are closer than the grid guarantees",
          worst_gap and worst_gap[1] >= worst_gap[2] - 1e-9,
          f"{worst_gap[0]}: {worst_gap[1]:.3f} m measured, "
          f"{worst_gap[2]:.3f} m constructed")
    check("and that separation is at least a shoulder width",
          worst_gap and worst_gap[1] >= FIG_SHOULDER_M,
          f"{worst_gap[1]:.3f} m vs {FIG_SHOULDER_M} m shoulder")
    inside = all(abs(x) <= EXTENTS["zocalo"].width_m / 2 + 1e-9
                 and -1e-9 <= z <= EXTENTS["zocalo"].length_m + 1e-9
                 for x, z in pos200)
    check("nobody stands outside the room", inside)
    # Clustering is a claim about shape, so it is measured against the uniform
    # it is supposed to differ from, not merely asserted to exist. Half the
    # room's peak crowd, so there is a real choice of cells to make -- with the
    # grid sized to the hour, every cell was used and the model did nothing.
    def _mean_abs_x(k, h, frac=0.5):
        n = max(2, int(room_headcount(k, h) * frac))
        pts = place_positions(k, h, n)
        return (sum(abs(x) for x, _z in pts) / len(pts)
                / (EXTENTS[k].width_m / 2.0), n)
    # The customs hall is empty between waves, so half of nothing is nothing:
    # the hour has to be one the hall is actually processing an arrival in, or
    # the statistic is taken over two people. `wave_pulse` decides which.
    wave_h = max((i / 20.0 for i in range(480)),
                 key=lambda x: density("customs_halls", x))
    mean_q, nq = _mean_abs_x("customs_halls", wave_h)
    mean_z, nz_ = _mean_abs_x("zocalo", 20.0)
    # A uniform draw over an nx-column grid is not 0.50 -- it is the mean of
    # the column centres -- so the baseline is computed rather than assumed.
    nx, _nzz, _cw, _cl = _cell_grid("customs_halls")
    uni = sum(abs((ix + 0.5) / nx - 0.5) * 2 for ix in range(nx)) / nx
    check("a queue hugs the centre line and a concourse hugs the edges",
          mean_q < uni - 0.05 < uni + 0.05 < mean_z,
          f"customs mean |x| {mean_q:.2f} over {nq} people at {wave_h:.2f}h, "
          f"Zocalo {mean_z:.2f} over {nz_}; a uniform draw on this grid is "
          f"{uni:.2f}")

    # =====================================================================
    # 6. FACTION FLAGS
    # =====================================================================
    # Measured over the id stream, not over one room: a room holds ~25 officers
    # and a 25-sample binomial has a +/-0.20 standard error, which is wide
    # enough to pass whatever the constant says. 20,000 ids is +/-0.003.
    n_band = sum(1 for i in range(20_000)
                 if _u(f"crowd:s:security_central:human:{i}", "nightwatch")
                 < NIGHTWATCH_SHARE)
    band = n_band / 20_000
    check("30-40% of security wear the Nightwatch armband (5.4)",
          0.30 <= band <= 0.40, f"{band:.3f} over 20,000 ids")
    sec = [p for p in spawn("security_central", 13.0, "s") if p.role == "security"]
    # 12's "Security <-> security" friction is a two-officer patrol with one
    # band and one bare sleeve. If a room of officers is all one or all the
    # other, that scene can never happen.
    check("a room of officers contains both banded and bare sleeves (12)",
          len(sec) > 8 and 0 < sum(1 for p in sec if p.armband) < len(sec),
          f"{sum(1 for p in sec if p.armband)} banded of {len(sec)}")
    check("nobody outside security wears one -- it is a per-NPC boolean on "
          "the security uniform, not an NPC type",
          not any(p.armband for p in a if p.role != "security"))
    # Rangers: 20-60 aboard in 250,000 (10.1). Measured over the id stream
    # rather than asserted, because a probability that never fires is a feature
    # nobody ever sees and a probability that fires too often is a costume party.
    n_r = sum(1 for i in range(200_000) if _u(f"crowd:x:y:human:{i}", "ranger") < RANGER_P)
    aboard = n_r * sched.RESIDENT_TOTAL / 200_000
    check("20-60 Rangers aboard, measured over the stream (10.1)",
          20 <= aboard <= 60, f"{aboard:.0f} implied")
    alien = spawn("alien_sector", 13.0, "s")
    check("everyone in the Alien Sector is masked or suited (9.3)",
          alien and all(p.breather in ("mask", "suit") for p in alien),
          f"{len(alien)} people, "
          f"{sum(1 for p in alien if p.breather == 'none')} unmasked")
    check("Gaim are suited wherever they stand, not only in their own sector",
          all(p.breather == "suit" for p in a if p.species == "gaim"))
    check("roles are filtered to what the place explains",
          all(p.role in EXTENTS["council_chamber"].roles
              for p in spawn("council_chamber", 13.0, "s")),
          str(sorted({p.role for p in spawn("council_chamber", 13.0, "s")})))
    named = [p for p in a if p.name]
    check("people who can be named are named",
          named and all(len(p.name) > 2 for p in named),
          f"{len(named)} of {len(a)} named; species without a grammar stay "
          f"anonymous by INV-004's rule")

    # =====================================================================
    # 7. COST
    # =====================================================================
    ch, csrc = render_chain()
    check("the render chain came from body.py, not the fallback",
          "body.py" in csrc, csrc)
    fb = frame_budget()
    check("the binding frame share is the smaller of the two committed ones",
          fb["share"] == min(fb["shares"].values()) and len(fb["shares"]) == 2,
          str(fb["shares"]))
    # Uncapped: what the crowd costs if every figure in the room is a mesh.
    z0 = visible_cost("zocalo", 20.0, offset=0, mesh_horizon=False)
    z2 = visible_cost("zocalo", 20.0, offset=CROWD_LOD_OFFSET,
                      mesh_horizon=False)
    # NOT a tautology: it is entirely possible for the offset to be enough, and
    # if the density or the chain moves it will be. What this records is the
    # shortfall the module exists to be honest about.
    check("the busiest room does NOT fit the tightest budget with meshes "
          "everywhere, at either offset",
          not z0["within_budget"] and not z2["within_budget"],
          f"offset 0 {z0['triangles']:,.0f} tri, offset {CROWD_LOD_OFFSET} "
          f"{z2['triangles']:,.0f} tri, budget {z2['budget']:,} -- needs "
          f"{required_frame_share('zocalo', 20.0):.1%} of the frame, has "
          f"{frame_budget()['share']:.0%}")
    check("the crowd LOD offset still saves a third of the frame",
          z2["triangles"] < 0.70 * z0["triangles"],
          f"{z0['triangles']:,.0f} -> {z2['triangles']:,.0f} "
          f"({1 - z2['triangles']/z0['triangles']:.0%} saved)")
    w = worst_case()
    check("with the mesh horizon applied, the worst case is inside budget",
          w["within_budget"],
          f"{w['place']} at {w['hour']:04.1f}h: {w['triangles']:,.0f} of "
          f"{w['budget']:,}")
    # The horizon is the price of the shortfall, and this is what it costs: an
    # impostor swap at a stated distance. Asserting it stays outside twice the
    # full-simulation radius stops the fix for a budget overrun being "put
    # cards on people the player is talking to".
    # Only the places that actually run out of budget have a swap at all: a
    # room shorter than its horizon draws meshes to its own far wall and never
    # shows a card. Reading `mesh_horizon_m == far` as an early swap was this
    # module's second-pass bug, and it flagged the ambassadorial suites -- a
    # 16.7 m room in which no impostor is ever used.
    horizons = [(k, visible_cost(k, peak_hour(k))["mesh_horizon_m"])
                for k in EXTENTS if not sched.PLACES[k].sealed
                and visible_cost(k, peak_hour(k))["impostors_used"]]
    worst_h = min(horizons, key=lambda kv: kv[1]) if horizons else None
    check("no place puts an impostor inside twice the full-sim radius",
          horizons and worst_h[1] >= 2 * FULL_SIM_RADIUS_M,
          f"{len(horizons)} places swap at all; worst is {worst_h[0]} at "
          f"{worst_h[1]:.1f} m, where a figure is {figure_px(worst_h[1]):.0f} px"
          if horizons else "no place ever reaches the budget -- suspicious")
    # The drum is the case that breaks the AGENT budget rather than the triangle
    # budget, and that distinction is the whole reason for a FLOCK tier.
    g = visible_cost("the_garden", 13.0)
    check("the drum floor overruns the crowd-AGENT cap, not the triangle budget",
          g["agents_crowd_wanted"] > CROWD_AGENT_CAP and g["within_budget"],
          f"{g['agents_crowd_wanted']:,} agents wanted vs a "
          f"{CROWD_AGENT_CAP:,} cap; {g['triangles']:,.0f} tri")
    check("full-simulation agents stay under their cap everywhere",
          all(visible_cost(k, float(h))["agents_full"] <= FULL_AGENT_CAP
              for k in EXTENTS if not sched.PLACES[k].sealed
              for h in (3, 13, 20)))
    # A frustum band's area must grow like d^2 near the camera and like d far
    # away, or the crowd is being spread along a line. Checking the shape, not
    # the value, so the constant cannot make it pass.
    near = frustum_floor_area(0.0, 2.0, 1e9) / frustum_floor_area(0.0, 1.0, 1e9)
    far = (frustum_floor_area(100.0, 101.0, 20.0)
           / frustum_floor_area(200.0, 201.0, 20.0))
    check("frustum floor area is quadratic near and linear far",
          abs(near - 4.0) < 1e-9 and abs(far - 1.0) < 1e-9,
          f"near ratio {near:.4f} (want 4), far ratio {far:.4f} (want 1)")
    check("the crowd radius shrinks as the crowd thickens",
          crowd_radius(0.30) < crowd_radius(0.03) < crowd_radius(0.003),
          f"{crowd_radius(0.30):.1f} < {crowd_radius(0.03):.1f} < "
          f"{crowd_radius(0.003):.1f} m")

    # =====================================================================
    # 8. THE BOUNDARY -- nothing appears in front of the player
    # =====================================================================
    # At each place's OWN busiest hour, which is when the tier boundaries bite.
    # Taking them all at 20:00 hid the drum entirely, because the Garden is a
    # daytime place and at 20:00 its crowd radius runs past the sight line.
    br = [boundary_report(k, peak_hour(k)) for k in EXTENTS
          if not sched.PLACES[k].sealed]
    check("spawn radius is always outside the crowd radius, with hysteresis",
          all(r["spawn_radius_m"] > r["crowd_radius_m"] and
              r["despawn_radius_m"] > r["spawn_radius_m"] for r in br))
    # This is the honest finding, asserted so it cannot be forgotten: in an
    # unoccluded volume the crowd radius lands well inside the sight line, so a
    # FLOCK tier is not optional decoration -- without it, people appear.
    need = [r["place"] for r in br if r["needs_flock_tier"]]
    check("the places that need a FLOCK tier are the unoccluded ones",
          "the_garden" in need and "zen_garden" not in need
          and "earharts" not in need, str(sorted(need)))
    check("tier assignment is continuous at both boundaries",
          sim_tier(FULL_SIM_RADIUS_M - 1e-6, "zocalo", 20.0) == TIER_FULL
          and sim_tier(FULL_SIM_RADIUS_M + 1e-6, "zocalo", 20.0) == TIER_CROWD
          and sim_tier(1e9, "zocalo", 20.0) == TIER_STATISTICAL)
    # The boundary a player can actually see is the MESH HORIZON, not the crowd
    # radius: in a room the crowd radius is usually past the far wall. A figure
    # is still 67 px tall where the Zocalo runs out of triangles, and saying so
    # is the point -- an unmeasured boundary is how "it will be fine" gets into
    # a design.
    zb = boundary_report("zocalo", 20.0)
    check("the visible boundary is measured, not assumed invisible",
          zb["impostors_used"] and 30.0 < zb["px_at_mesh_horizon"] < 200.0,
          f"a 1.75 m figure is {zb['px_at_mesh_horizon']:.0f} px at the "
          f"Zocalo's {zb['mesh_horizon_m']:.0f} m mesh horizon -- the swap is a "
          f"representation change at a fixed position, never a spawn, and it "
          f"is the honest price of a 12% frame share")

    # =====================================================================
    # 9. GEOMETRY -- winding, closure, and whether it renders at all
    # =====================================================================
    v, t = [], []
    figure_geometry(Person("x", "human", "merchant", "idle", "", 0.0, 0.0, 0.0,
                           TIER_FULL), v, t)
    check("a proxy figure is 36 triangles", len(t) == FIG_TRIS, str(len(t)))
    check("a proxy figure has positive signed volume (outward winding)",
          signed_volume(v, t) > 0,
          f"{signed_volume(v, t):.4f} m3 for three boxes")
    # Deliberately break it: reversing every triangle must flip the sign. If
    # this passed either way the volume test would be measuring nothing.
    check("reversing the winding makes the volume negative",
          signed_volume(v, [(c, b, a) for a, b, c in t]) < 0)
    eye_out = (6.0, 1.5, -6.0)
    ff = facing_fraction(v, t, eye_out)
    check("about half a closed body faces any eye",
          0.30 <= ff <= 0.60, f"{ff:.2f}")
    rv, rt, rg = preview_room("zocalo")
    inside_eye = (0.0, 1.7, 5.0)
    ffr = facing_fraction(rv, rt, inside_eye)
    check("every surface of the preview room faces an eye standing in it",
          ffr == 1.0,
          f"{ffr:.2f} of {len(rt)} triangles; anything under 1.00 is a "
          f"surface the player would see through")
    # Deliberately broken: flipping ONE quad of the room must show up. Without
    # this, `ffr == 1.0` could be true of a room with no triangles in it, and
    # this repository has shipped exactly that shape of vacuous assertion.
    flipped = list(rt)
    flipped[0] = (rt[0][0], rt[0][2], rt[0][1])
    check("and flipping a single quad drops it below 1.00",
          len(rt) > 0 and facing_fraction(rv, flipped, inside_eye) < 1.0,
          f"{facing_fraction(rv, flipped, inside_eye):.2f} with one of "
          f"{len(rt)} triangles reversed")
    floor_t = rt[rg[0][1]:rg[0][2]]
    ny = []
    for aa, bb, cc in floor_t:
        pa, pb, pc = rv[aa], rv[bb], rv[cc]
        u = [pb[i] - pa[i] for i in range(3)]
        wv = [pc[i] - pa[i] for i in range(3)]
        ny.append(u[2] * wv[0] - u[0] * wv[2])
    check("the floor faces UP, which is the rule flat surfaces are given",
          all(n > 0 for n in ny), str(ny))

    ok = _results.count(True)
    print(f"\n{ok}/{len(_results)} passed")
    return 0 if ok == len(_results) else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--report" in argv:
        report()
        return 0
    if "--obj" in argv:
        i = argv.index("--obj")
        path = argv[i + 1]
        place = argv[argv.index("--place") + 1] if "--place" in argv else "zocalo"
        hour = float(argv[argv.index("--hour") + 1]) if "--hour" in argv else 20.0
        lim = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
        print(crowd_obj(path, place, hour, limit=lim))
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
