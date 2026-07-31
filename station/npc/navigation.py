#!/usr/bin/env python3
"""Navigation: where an NPC may stand, where it may walk, and what a route costs.

Twelve places are built. Nobody can get between any two of them, because
nothing in the project yet says which surfaces are floor, which floors touch,
and how long it takes to cross one. This module answers those three questions
and nothing else: it produces no rendered geometry, and its output is a graph
plus a set of walkable polygons.

THE ONE RULE THAT SHAPES EVERYTHING HERE
----------------------------------------
`CLAUDE.md` rule 4 -- inside and outside come from the same schema -- applies
to a navmesh with unusual force, because a hand-drawn navmesh is the classic
second source of truth. It drifts silently: the geometry moves, the navmesh
does not, and the first symptom is an NPC walking through a wall six sessions
later. So **every walkable surface in this module is derived from the module
that built the surface**:

    the drum ground        `drum_ground.sample()`            (heightfield)
    ring corridors         `interior.ring_cells()` + the kit's own section
    the docking bay        `docking_bay.docking_bay()`       (mesh)
    C&C                    `command_control.command_control()` (mesh)
    the Council Chamber    `council_chamber.council_chamber()` (mesh)
    the Zocalo             `zocalo.zocalo_bay()`             (mesh)
    the spokes, the axis   `interior.SPOKE_COUNT`, `core_tube`, `physics/`

`nav_from_mesh()` is the general extractor: hand it any module's emitted mesh
and it returns the walkable polygons under this module's criteria. It is used
directly on the four room modules. For the 3,414 streaming cells it would be
ruinous to build 3,414 corridor meshes to measure a footprint that is the same
every time, so the cell footprint is computed from the kit's own constants --
**and `_selftest` cross-checks that analytic footprint against what
`nav_from_mesh` extracts from a real `deck_cell()` mesh.** One measured cell
validates the rule used for 3,414. That is the only place a shortcut is taken
and it is the only place one is checked.

WALKABLE CRITERIA -- DERIVED, NOT CHOSEN
----------------------------------------
Four numbers decide what is floor. Every one of them is read out of something
the station already builds, and `_selftest` asserts each against the bound that
makes it that number rather than a neighbouring one:

    step      0.10 m   = `interior_kit.PROVISIONAL["door_sill_m"]`
                         Every pressure door in the station has a sill. A step
                         limit below it makes every door impassable and the
                         station becomes 3,414 disconnected rooms. Bounded
                         above by the stair riser: 0.20 m would let an agent
                         walk up a flight of stairs as though it were a ramp.
    slope    38.66 deg = atan(stair riser / stair going), from `zocalo.py`'s
                         built flight -- 3.6 m of gallery over 18 risers at a
                         0.25 m going. A stair exists precisely because that
                         pitch cannot be floor, so it is the ceiling on floor.
    headroom  2.10 m   = `interior_kit.PROVISIONAL["door_height_m"]`
                         The clearance the station guarantees at its tightest
                         legal aperture, and the figure `body.py` already
                         asserts all fifteen species clear.
    spacing  15.61 m   = `drum_ground._step_ramp_m() / 2`
                         The ground lattice's sample pitch. The ground's own
                         LOD rule forbids any step narrower than one stride-8
                         cell (31.2 m), so sampling at half that resolves the
                         narrowest legal feature in the field. It also happens
                         to be exactly `drum_ground.STRIDES` level 4, which is
                         asserted rather than assumed.

WHAT THE CRITERIA FOUND, AND IT IS A REAL RESULT
------------------------------------------------
The drum ground's **worst slope anywhere is 13.84 deg**, against a 38.66 deg
limit -- the ground has no unwalkable slope at all, and **not one cell in
17,920 is rejected by the slope test**. That is not luck and it is not a weak
test: `drum_ground`'s step rule ramps every feature over at least 31.2 m *for
LOD reasons*, and the side effect is a landscape with no cliffs in it. The one
thing that stops a walker is **water** -- 1,447 cells, 8.1% of the drum floor
once the shore margin is applied, in a band 175 m wide running the drum's
entire 2,586 m length.

And the lake does not cut the drum in half, which it would on any flat map.
A strip removed from a *closed* surface leaves a connected sheet, because you
walk round the far side. `_selftest` proves that is load-bearing rather than
lucky: flood the entire water band and the ground is still one island; flood
it and drop the wrap link and the drum falls into two pieces.

PATHING COST -- TWO METRICS, AND THEY DISAGREE
----------------------------------------------
A route is not the shortest one, for three separate reasons that this module
prices:

  1. **Walking speed depends on gravity.** Preferred walking speed follows the
     Froude number, v = sqrt(Fr*g*L) with L the leg length -- so Grey's 1.693 g
     basement is *faster* to walk than Yellow's 0.559 g, by 1.74x. The same
     relation makes *climbing* slower at high g, because a climb is power-
     limited rather than pendulum-limited.
  2. **Transit beats walking, but only past a distance.** The ground tram round
     the drum runs at 3.13 m/s against a 1.49 m/s walk -- 2.1x -- so with a
     wait it only wins on long hops, and `path()` picks accordingly.
  3. **Effort is not time.** `metric="effort"` measures weight-metres, which
     scales with local gravity, so the fastest route through Grey is not the
     least tiring one. Both are computed and `_selftest` asserts a pair of
     endpoints where the two metrics choose different routes.

WHY THE GROUND TRAM IS SLOW, AND IT IS THE GEOMETRY THAT SAYS SO
----------------------------------------------------------------
Moving circumferentially in a spun drum is not free: at tangential speed u the
Coriolis term adds 2*omega*u to apparent weight. The project's own bound on an
acceleration with no visible cause is **0.12 g**, the default in
`physics/core_shuttle.comfortable_duration()` and the number that produces the
133 s spoke ride quoted in `LOCATIONS.md` section 9. That bound gives

    u_max = 0.12 * g0 / (2 * omega) = 3.13 m/s

for anything moving around the drum -- and the identical bound on radial motion
gives the lift speed cap, which reproduces `comfortable_duration()`'s 133.2 s
rim-to-axis ride to four figures from a closed form. So the drum's two transit
systems are different because the geometry makes them different: **the guideway
tram runs along the axis where Coriolis is exactly zero and is fast; a ring
line runs across it and cannot be.** `29a` shows two systems (authority 1) and
this is why there are two.

COST AND LOD -- READ THIS BEFORE ADDING NODES
---------------------------------------------
The navmesh renders nothing, so it costs **zero triangles of frame budget**.
What it costs is memory and CPU, and both are gated in `budget_report()`:

    fine graph      19,973 nodes / 37,155 links      2.34 MB resident
    coarse graph    337 nodes                        0.91 MB all-pairs
    per-path        Dijkstra over the coarse graph, not the fine one

250,000 residents cannot each run a search. They do not: `crowd.py` caps
simulated agents at 500 full + 2,000 crowd, everything else is statistical and
has no position to path from. Of the 2,500 that do exist, each replans on an
activity change -- a few times a station-day -- and plans on the **coarse**
graph (places, transit stops, one node per deck). The fine ground lattice is
resolved only inside the player's resident cell set. `budget_report()` prints
the searches-per-second implied and gates it.

WHAT THIS DOES NOT DO, STATED SO IT IS NOT DISCOVERED LATER
-----------------------------------------------------------
  * **The ground navmesh is quantised to 15.61 m.** The shoreline is a curve
    and the lattice renders it as a staircase -- visible in the debug mesh.
    `SHORE_MARGIN_CELLS` retreats one cell so the error lands on the safe
    side, but a finer lattice near band boundaries is the real answer.
  * **No dynamic obstacles.** Doors are links with a cost, not things that
    open; a closed door is still traversable. Crowds do not block each other.
  * **No local avoidance.** This produces a route, not a trajectory. Two NPCs
    on the same link walk through each other.
  * **Sector-to-sector links are one walk of the z gap.** `interior.ring_arc`
    puts every deck at its sector's mid-z, so a sector change is a single
    1.9 km link in Yellow rather than a corridor with things along it. When
    decks acquire longitudinal extent this becomes a chain and nothing else
    here changes.
  * **Stairs are priced, not built.** The only stair geometry in the project
    is the Zocalo's flight; every other level change is a lift or a declared
    stair link with Naismith's ascent cost on it.
  * **The corridor floor under a wall is still floor.** `nav_obstacles` carves
    walls out of ROOM meshes, where the mesh is small enough to raster; the
    3,414 streaming cells use the analytic clear width instead, which is the
    same answer for a straight run and not for a junction.

ERA DATUM
---------
**S3, pre-martial-law** (`FACTIONS.md` 1.3). Inherited from `schedule.py`, not
re-decided here. It reaches navigation in exactly one place: the sealed Markab
quarter is a place with a floor, a door, and no walk link -- it is in the graph
and it is deliberately its own island, which is why `island_report()` reports
an expected-islands list rather than asserting the number is one.

DETERMINISM
-----------
blake2b throughout; no `random`, no `str.__hash__`. Dijkstra breaks ties on the
node id, so a path is a pure function of (graph, endpoints, metric).

Self-test:  python3 station/npc/navigation.py
"""
from __future__ import annotations

import hashlib
import heapq
import math
import os
import sys
from collections import deque
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_STATION)
for _p in (_STATION, _HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import interior as it                                       # noqa: E402
import interior_kit as ik                                   # noqa: E402
import drum_ground as dg                                    # noqa: E402


def _u(seed: str, salt: str = "") -> float:
    """Uniform [0,1) from a string. blake2b, 8 bytes, big-endian.

    Present so that anything this module ever has to break a tie on is broken
    the same way on every machine. `random` is banned project-wide and
    `str.__hash__` is salted per process -- `STATE.md` session 2n records a
    hull that would have differed every run from exactly that.
    """
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


# ===========================================================================
# 1.  Walkable criteria -- every one derived from a module that builds surface
# ===========================================================================

def _stair_pitch():
    """The pitch of the station's one built staircase, in (riser, going).

    `zocalo.stair_flight()` lifts `gallery_y_m` over `stair_risers` treads of
    `stair_going_m`. Read out of the module rather than restated: retuning the
    Zocalo's gallery height moves this module's slope limit with it, which is
    the behaviour rule 4 asks for.
    """
    try:
        import zocalo                                       # noqa: PLC0415
        p = zocalo.params()
        return (p["gallery_y_m"] / p["stair_risers"], p["stair_going_m"],
                "station/zocalo.py stair_flight (gallery_y_m / stair_risers, "
                "stair_going_m)")
    except Exception as exc:                                # noqa: BLE001
        # A fallback that is LOUDER than a wrong number: the route string says
        # "fallback" and `_selftest` fails on it. A silently-wrong criterion is
        # worse than a missing one -- AAA-STANDARD PERFORMANCE 1, the gate that
        # prints PASS on an unmeasured quantity.
        return (0.20, 0.25, f"fallback ({exc})")


_RISER_M, _GOING_M, STAIR_SOURCE = _stair_pitch()

# The largest vertical discontinuity an agent may cross as a step rather than
# as a stair. It is the door sill, and it is the door sill because every
# pressure door in the station has one: set the limit below it and every room
# in the station becomes unreachable through its own door.
STEP_M = ik.PROVISIONAL["door_sill_m"]
STEP_SOURCE = 'interior_kit.PROVISIONAL["door_sill_m"]'

# The stair riser is the upper bound on STEP_M, not a second criterion: if a
# step limit reaches the riser, a flight of stairs classifies as flat ground
# and agents slide up the nosings.
STAIR_RISER_M = _RISER_M
STAIR_GOING_M = _GOING_M

# The pitch at which the station stops building floor and starts building
# treads. Nothing at or above it is a walk surface; a stair is a link of its
# own kind with its own cost.
SLOPE_LIMIT_DEG = math.degrees(math.atan2(STAIR_RISER_M, STAIR_GOING_M))

# Standing clearance. The station's tightest legal aperture, and the number
# `body.py::_selftest` already asserts all fifteen species clear over sixty
# individuals each.
HEADROOM_M = ik.PROVISIONAL["door_height_m"]
HEADROOM_SOURCE = 'interior_kit.PROVISIONAL["door_height_m"]'

# Ground lattice pitch. `drum_ground`'s step rule guarantees no feature in the
# field steps in less than one stride-8 cell, so half a stride-8 cell resolves
# the narrowest legal feature -- two samples across the narrowest ramp.
GROUND_SPACING_M = dg._step_ramp_m() / 2.0
GROUND_SPACING_SOURCE = "drum_ground._step_ramp_m() / 2 (one stride-8 cell, halved)"


def criteria() -> dict:
    """Every walkable-surface criterion with the file it was read out of.

    Returned as data rather than left in constants so a reviewer can diff the
    provenance, and so AAA-STANDARD's FIDELITY 0 -- "a dimension appearing
    inline in code with neither a citation nor an INVENTIONS entry" -- cannot
    apply to any of them.
    """
    return {
        "step_m": {"value": STEP_M, "from": STEP_SOURCE,
                   "bounded_above_by": f"stair riser {STAIR_RISER_M:.3f} m"},
        "slope_limit_deg": {
            "value": SLOPE_LIMIT_DEG,
            "from": f"atan({STAIR_RISER_M:.4f} / {STAIR_GOING_M:.4f}); "
                    + STAIR_SOURCE},
        "headroom_m": {"value": HEADROOM_M, "from": HEADROOM_SOURCE,
                       "cross_check": "body.py asserts 15/15 species clear it"},
        "ground_spacing_m": {"value": GROUND_SPACING_M,
                             "from": GROUND_SPACING_SOURCE},
    }


# ===========================================================================
# 2.  Locomotion -- speed, climb rate and effort, as functions of gravity
# ===========================================================================
#
# Preferred walking speed is set by the pendulum the leg makes, which is the
# Froude number Fr = v^2/(g*L). At Fr ~ 0.25 a human walks; near 0.5 the gait
# breaks into a run. That relation is biomechanics rather than Babylon 5, so it
# is an EXTRAPOLATION (authority 5) -- and it carries its own cross-check:
# fed the project's own measured leg length it returns 1.494 m/s at 1 g,
# against the 1.4 m/s that adult preferred walking speed is independently
# known to sit at. 6.7% from a relation that was not fitted to it.
#
# The consequence is a station property, not a tuning knob: Grey's 1.693 g
# basement is walked 1.74x faster than Yellow's 0.559 g outer ring, and the
# 2.4x weight change LOCATIONS.md section 0.4 calls a headline feature turns
# out to change how fast people move as well as how heavy they feel.
FROUDE_PREFERRED = 0.25

# Naismith's rule, the field standard for walking time in hills: one hour per
# 5 km horizontal plus one hour per 600 m of ascent. The ascent term is what
# makes stairs and ramps cost more than their plan length. EXTRAPOLATION.
CLIMB_RATE_1G_M_S = 600.0 / 3600.0

# Cost of transport for level human walking, expressed in weight-metres per
# metre: a metre of level walking costs about a fifth of what lifting your own
# body a metre costs. EXTRAPOLATION, and it is checked for consistency against
# Naismith rather than left alone -- Naismith's 8.3:1 time ratio and this
# 5:1 effort ratio are the same statement to within the precision either has.
LEVEL_COST_OF_TRANSPORT = 0.20

G0 = 9.80665


def leg_length_m(species: str = "human") -> float:
    """Hip height, from `body.py`'s measured figure table.

    `FIGURE["hip"]` is 0.520 of stature, derived in `body.py` from a belt
    centre measured at 8x on an authority-1 frame. `leg_k` is the species'
    multiplier on hip height at constant stature.
    """
    try:
        import body                                          # noqa: PLC0415
        sp = body.SPECIES[species]
        return body.FIGURE["hip"] * sp.stature_m * sp.leg_k
    except Exception:                                        # noqa: BLE001
        return 0.520 * 1.75


_LEG_HUMAN = leg_length_m("human")


def walk_speed(g: float, species: str = "human") -> float:
    """Preferred walking speed in m/s at local gravity `g` (in g, not m/s^2).

    Rises as sqrt(g). In the drum's 1.0 g Garden this is 1.49 m/s; on Grey's
    1.693 g plant decks it is 1.94 m/s; in Yellow's 0.559 g it is 1.12 m/s.
    """
    if g <= 0.0:
        # Zero g is not walking. The axis is served by the core shuttle and by
        # nothing else, and a walk link is never emitted there -- returning a
        # finite speed here would let a path drift onto the axis and stroll.
        return 0.0
    return math.sqrt(FROUDE_PREFERRED * g * G0 * leg_length_m(species))


def climb_speed(g: float) -> float:
    """Vertical rate on a stair or ramp, m/s. Falls as 1/g: a climb is limited
    by the power available against weight, not by the gait."""
    if g <= 0.0:
        return 0.0
    return CLIMB_RATE_1G_M_S / g


def walk_time_s(distance_m: float, rise_m: float, g: float,
                species: str = "human") -> float:
    """Naismith: plan distance at the Froude speed plus ascent at the climb
    rate. Descent is free, which is what the rule says and is close enough at
    the gradients this station actually contains."""
    v = walk_speed(g, species)
    if v <= 0.0:
        return float("inf")
    t = distance_m / v
    if rise_m > 0.0:
        c = climb_speed(g)
        t += rise_m / c if c > 0 else float("inf")
    return t


def walk_effort(distance_m: float, rise_m: float, g: float) -> float:
    """Traversal cost in WEIGHT-METRES: the work of carrying yourself.

    Level walking costs `LEVEL_COST_OF_TRANSPORT` weight-metres per metre;
    lifting costs one per metre of rise. Both scale with local gravity, which
    is the whole point -- it is why the least-tiring route out of Grey is not
    the fastest one.
    """
    return g * (LEVEL_COST_OF_TRANSPORT * distance_m + max(0.0, rise_m))


# ===========================================================================
# 3.  Transit -- the four systems, and why their speeds are what they are
# ===========================================================================
#
# The station's own comfort bound on an acceleration with no visible cause.
# Not invented here: it is the default of
# `station/physics/core_shuttle.comfortable_duration()`, and it is what
# produces the 133 s rim-to-axis ride LOCATIONS.md section 9 quotes.
MAX_LATERAL_G = 0.12

# Cruise acceleration for anything running along the axis, where Coriolis is
# identically zero. `physics/core_shuttle.AxialShuttle`'s own default, and
# note it is 1.2 m/s^2 = 0.122 g -- the same comfort bound arrived at from the
# other direction, which is a coincidence worth not tidying away.
AXIAL_ACCEL_M_S2 = 1.2

# Stops on the core shuttle: 13, running Blue to Grey. Authority 4
# (oocities fan site, cited in LOCATIONS.md section 9). Their SPACING is ours.
CORE_SHUTTLE_STOPS = 13

# Boarding time. EXTRAPOLATION: a tram car with ~40 seats and two doors.
TRANSIT_DWELL_S = 20.0

# Vehicles per line, used to turn a round trip into a headway. The guideway
# figure is `tram.drum_trams`'s own `per_guideway` default, so the tram module
# and this one cannot disagree about how many cars exist. The others are ours.
CORE_SHUTTLE_CARS = 6
GROUND_TRAM_CARS = 4
SPOKE_LIFT_CARS = 1

# Service target for a radial lift shaft: a car every two dwells. `shaft_cars`
# turns it into a fleet per sector. See that function -- the target is derived
# from TRANSIT_DWELL_S rather than chosen alongside it.
SHAFT_TARGET_HEADWAY_S = 2.0 * TRANSIT_DWELL_S


def omega(schema) -> float:
    return schema["station"]["rotation"]["omega_rad_s"]["value"]


def coriolis_speed_cap(schema, max_lateral_g: float = MAX_LATERAL_G) -> float:
    """The speed cap that 2*omega*v <= max_lateral_g * g0 imposes.

    It applies to BOTH radial motion (a lift) and tangential motion (a ring
    tram), because the Coriolis term does not care which of the two it is --
    which is why the same 3.13 m/s falls out for a lift car and for a tram
    running round the drum, and why the drum needs a second, axial system to
    move anyone quickly.
    """
    return max_lateral_g * G0 / (2.0 * omega(schema))


def lift_ride_s(schema, dr_m: float,
                max_lateral_g: float = MAX_LATERAL_G) -> float:
    """Ride time for a radial move of `dr_m`, in seconds.

    Closed form, and it is a cross-check rather than a restatement: a
    smoothstep profile peaks at 1.5x its mean speed, so holding the peak at the
    Coriolis cap gives T = 1.5 * dr / v_cap. Fed the drum's 278.3 m this
    returns 133.2 s, which is `physics/core_shuttle.comfortable_duration()`'s
    bisection answer to four figures from arithmetic that shares nothing with
    it. `_selftest` asserts the agreement.
    """
    if dr_m <= 0.0:
        return 0.0
    return 1.5 * dr_m / coriolis_speed_cap(schema, max_lateral_g)


def axial_ride_s(distance_m: float, accel: float = AXIAL_ACCEL_M_S2) -> float:
    """Accelerate to the midpoint, decelerate to the stop. No Coriolis term:
    motion parallel to the spin axis produces none at all."""
    if distance_m <= 0.0:
        return 0.0
    return 2.0 * math.sqrt(distance_m / accel)


def ground_tram_ride_s(schema, arc_m: float) -> float:
    """A leg of the circumferential ring line, at the Coriolis speed cap.

    Accelerating to 3.13 m/s takes 2.6 s and 4.1 m at the axial rate, which is
    negligible against a 291 m stop spacing, so this is the constant-speed time
    plus one acceleration.
    """
    v = coriolis_speed_cap(schema)
    return arc_m / v + v / AXIAL_ACCEL_M_S2


# ===========================================================================
# 4.  The general navmesh extractor -- polygons out of any module's mesh
# ===========================================================================

@dataclass
class NavPoly:
    """One walkable triangle, with the numbers the criteria were applied to."""
    verts: tuple            # three (x, y, z) in the mesh's own frame
    normal: tuple
    slope_deg: float
    headroom_m: float
    area_m2: float
    centroid: tuple
    walkable: bool
    reason: str = ""


def _tri_normal(p0, p1, p2):
    u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
    n = (u[1] * v[2] - u[2] * v[1],
         u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
    if ln < 1e-12:
        return (0.0, 0.0, 0.0), 0.0
    return (n[0] / ln, n[1] / ln, n[2] / ln), ln / 2.0


class _RayGrid:
    """Uniform bucket grid over the two axes perpendicular to `up`.

    Headroom is a ray cast per candidate floor triangle against the whole mesh.
    Done naively that is O(n^2) and the Council Chamber's 1,892 triangles turn
    into three million intersection tests. Bucketing by the triangle's plan
    bounding box takes it to a few tens of tests each.
    """

    def __init__(self, verts, tris, ax0, ax1, cell=2.0):
        self.ax0, self.ax1, self.cell = ax0, ax1, cell
        self.b = {}
        for i, (a, b, c) in enumerate(tris):
            p = (verts[a], verts[b], verts[c])
            u0 = min(q[ax0] for q in p)
            u1 = max(q[ax0] for q in p)
            w0 = min(q[ax1] for q in p)
            w1 = max(q[ax1] for q in p)
            for gu in range(int(math.floor(u0 / cell)), int(math.floor(u1 / cell)) + 1):
                for gw in range(int(math.floor(w0 / cell)),
                                int(math.floor(w1 / cell)) + 1):
                    self.b.setdefault((gu, gw), []).append(i)

    def near(self, u, w):
        return self.b.get((int(math.floor(u / self.cell)),
                           int(math.floor(w / self.cell))), ())


def _ray_up_hit(origin, up, verts, tris, cand, eps=1e-4):
    """Nearest hit above `origin` along `up`. Moller-Trumbore, one ray."""
    best = float("inf")
    ox, oy, oz = origin
    dx, dy, dz = up
    for i in cand:
        a, b, c = tris[i]
        p0, p1, p2 = verts[a], verts[b], verts[c]
        e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        h = (dy * e2[2] - dz * e2[1], dz * e2[0] - dx * e2[2],
             dx * e2[1] - dy * e2[0])
        det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
        if abs(det) < 1e-12:
            continue
        inv = 1.0 / det
        s = (ox - p0[0], oy - p0[1], oz - p0[2])
        u = inv * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
        if u < -1e-9 or u > 1.0 + 1e-9:
            continue
        q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
             s[0] * e1[1] - s[1] * e1[0])
        v = inv * (dx * q[0] + dy * q[1] + dz * q[2])
        if v < -1e-9 or u + v > 1.0 + 1e-9:
            continue
        t = inv * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2])
        if t > eps:
            best = min(best, t)
    return best


# Raster cell for plan-projected area. The navmesh has to resolve the
# narrowest passage in the station, which is a door aperture at
# `door_width_m`; half of that puts two cells across a doorway, which is the
# coarsest raster that can still tell a door from a wall.
RASTER_CELL_M = ik.PROVISIONAL["door_width_m"] / 2.0


def _plan_cells(u, w, cell):
    """Plan cells a projected triangle covers.

    Two cases, and the second is the one a floor-only extractor gets wrong: a
    VERTICAL triangle projects to a line, and a point-in-triangle test on a
    degenerate projection returns nothing at all -- so every wall in the
    station would carve no obstacle and NPCs would walk through them. Edge-on
    triangles are therefore rasterised as segments.
    """
    area2 = abs((u[1] - u[0]) * (w[2] - w[0]) - (u[2] - u[0]) * (w[1] - w[0]))
    out = set()
    if area2 > cell * cell * 0.5:
        for gu in range(int(math.floor(min(u) / cell)),
                        int(math.floor(max(u) / cell)) + 1):
            for gw in range(int(math.floor(min(w) / cell)),
                            int(math.floor(max(w) / cell)) + 1):
                if _point_in_tri((gu + 0.5) * cell, (gw + 0.5) * cell, u, w):
                    out.add((gu, gw))
        if out:
            return out
    for i in range(3):
        j = (i + 1) % 3
        du, dw = u[j] - u[i], w[j] - w[i]
        n = max(1, int(math.hypot(du, dw) / (cell * 0.5)) + 1)
        for k in range(n + 1):
            pu, pw = u[i] + du * k / n, w[i] + dw * k / n
            out.add((int(math.floor(pu / cell)), int(math.floor(pw / cell))))
    return out


def nav_obstacles(verts, tris, up=(0.0, 1.0, 0.0), slope_deg=None, cell=None):
    """Plan cells blocked by something too steep to walk on, with the height
    band each blocks. A wall standing ON a deck does not delete the deck under
    it, and without this the deck under every wall in the station is floor."""
    cell = RASTER_CELL_M if cell is None else cell
    slope = SLOPE_LIMIT_DEG if slope_deg is None else slope_deg
    cos_lim = math.cos(math.radians(slope))
    ax = max(range(3), key=lambda i: abs(up[i]))
    ax0, ax1 = [i for i in range(3) if i != ax]
    sign = 1.0 if up[ax] > 0 else -1.0
    blocked = {}
    for a, b, c in tris:
        p = (verts[a], verts[b], verts[c])
        n, area = _tri_normal(*p)
        if area <= 0.0:
            continue
        d = abs(n[0] * up[0] + n[1] * up[1] + n[2] * up[2])
        if d >= cos_lim:
            continue                      # walkable or a ceiling: not a wall
        ys = sorted(q[ax] * sign for q in p)
        for key in _plan_cells([q[ax0] for q in p], [q[ax1] for q in p], cell):
            blocked.setdefault(key, []).append((ys[0], ys[2]))
    return blocked


@dataclass
class NavRegion:
    """A connected walkable region, measured on the plan raster."""
    cells: int
    area_m2: float
    height_m: float
    example: tuple


def nav_regions(polys, up=(0.0, 1.0, 0.0), cell=None, obstacles=None,
                subset=None, step_m=None):
    """Connected walkable regions, built on a plan raster with height spans.

    This replaced a vertex-shared-edge adjacency test, and the Council Chamber
    is why. Its floor is 96 irregular mosaic tiles, each fanned from its own
    centre, so **no two tiles share a vertex** -- edge adjacency reported 193
    components on a floor that is visibly one room, and the largest of them
    was 4.5 m2 of an 11 m disc. A raster does not care how a floor was
    triangulated, which is the whole reason production navmesh builders
    rasterise rather than walk the mesh.

    Surfaces in the same plan cell within STEP_M of each other are one span
    (the bay's red disc and the deck it is painted on); further apart they are
    two (the bay's 2.2 m ledges). Neighbouring cells join when their spans are
    within STEP_M -- which is the step criterion doing its job -- and when no
    obstacle stands in the standing volume above them.
    """
    cell = RASTER_CELL_M if cell is None else cell
    step = STEP_M if step_m is None else step_m
    ax = max(range(3), key=lambda i: abs(up[i]))
    ax0, ax1 = [i for i in range(3) if i != ax]
    sign = 1.0 if up[ax] > 0 else -1.0

    raw = {}
    for i, p in enumerate(polys):
        if not p.walkable or (subset is not None and i not in subset):
            continue
        v = p.verts
        y = p.centroid[ax] * sign
        for key in _plan_cells([q[ax0] for q in v], [q[ax1] for q in v], cell):
            raw.setdefault(key, []).append(y)

    # Collapse each cell's heights into spans, then drop spans an obstacle
    # stands in. `HEADROOM_M` is reused deliberately: a wall is an obstacle
    # exactly when it occupies the volume a person would stand in.
    spans = {}
    for key, hs in raw.items():
        hs.sort()
        runs, cur = [], [hs[0]]
        for a, b in zip(hs, hs[1:]):
            if b - a > step:
                runs.append(cur)
                cur = []
            cur.append(b)
        runs.append(cur)
        keep = []
        for run in runs:
            h = run[0]
            if obstacles:
                hit = False
                for lo, hi in obstacles.get(key, ()):
                    if hi > h + step and lo < h + HEADROOM_M:
                        hit = True
                        break
                if hit:
                    continue
            keep.append(h)
        if keep:
            spans[key] = keep

    nodes = [(k, si, h) for k, hs in spans.items() for si, h in enumerate(hs)]
    index = {(k, si): n for n, (k, si, _h) in enumerate(nodes)}
    seen, regions = set(), []
    for n0 in range(len(nodes)):
        if n0 in seen:
            continue
        q, comp = deque([n0]), []
        seen.add(n0)
        while q:
            n = q.popleft()
            comp.append(n)
            (gu, gw), _si, h = nodes[n]
            for nb in ((gu + 1, gw), (gu - 1, gw), (gu, gw + 1), (gu, gw - 1)):
                for sj, hj in enumerate(spans.get(nb, ())):
                    if abs(hj - h) > step:
                        continue
                    m = index[(nb, sj)]
                    if m not in seen:
                        seen.add(m)
                        q.append(m)
        regions.append(NavRegion(len(comp), len(comp) * cell * cell,
                                 nodes[comp[0]][2], nodes[comp[0]][0]))
    regions.sort(key=lambda r: -r.area_m2)
    return regions


def nav_plan_area_m2(polys, up=(0.0, 1.0, 0.0), cell=None, obstacles=None,
                     subset=None):
    """Total plan-projected walkable area, stacked surfaces counted once."""
    return sum(r.area_m2 for r in nav_regions(polys, up, cell, obstacles,
                                              subset))


def _point_in_tri(px, py, u, w):
    d = ((w[1] - w[2]) * (u[0] - u[2]) + (u[2] - u[1]) * (w[0] - w[2]))
    if abs(d) < 1e-15:
        return False
    a = ((w[1] - w[2]) * (px - u[2]) + (u[2] - u[1]) * (py - w[2])) / d
    b = ((w[2] - w[0]) * (px - u[2]) + (u[0] - u[2]) * (py - w[2])) / d
    return a >= -1e-9 and b >= -1e-9 and a + b <= 1.0 + 1e-9


def nav_from_mesh(verts, tris, up=(0.0, 1.0, 0.0),
                  slope_deg=None, headroom_m=None, min_area_m2=0.02):
    """Walkable polygons extracted from a built mesh.

    THE GENERAL CASE, and the reason this module does not hand-author anything.
    A triangle is floor when its normal is within `slope_deg` of `up` AND there
    is `headroom_m` of clear space above its centroid in the same mesh.

    The headroom half is what catches the interesting geometry. The docking
    bay's stepped side ledges corbel INWARD as they rise, so the outer 3.4 m
    strip of a bay deck has 2.18 m over it -- 0.08 m of margin on the 2.10 m
    criterion, and the tightest standing clearance anywhere in the built
    station. Nothing in a render would have told anyone that.

    `up` is the mesh's own up. The four room modules author in local frames
    with +Y up; station-space meshes in the drum want the radially inward
    direction and get it per-triangle from `nav_from_drum_mesh`.
    """
    slope = SLOPE_LIMIT_DEG if slope_deg is None else slope_deg
    head = HEADROOM_M if headroom_m is None else headroom_m
    cos_lim = math.cos(math.radians(slope))
    ax = max(range(3), key=lambda i: abs(up[i]))
    ax0, ax1 = [i for i in range(3) if i != ax]
    grid = _RayGrid(verts, tris, ax0, ax1)

    out = []
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        n, area = _tri_normal(p0, p1, p2)
        if area < min_area_m2:
            continue
        d = n[0] * up[0] + n[1] * up[1] + n[2] * up[2]
        cen = ((p0[0] + p1[0] + p2[0]) / 3.0,
               (p0[1] + p1[1] + p2[1]) / 3.0,
               (p0[2] + p1[2] + p2[2]) / 3.0)
        slope_here = math.degrees(math.acos(max(-1.0, min(1.0, abs(d)))))
        if d < cos_lim:
            # Faces away from up: a ceiling, a wall, or an upside-down floor.
            # Not recorded -- there are thousands and they carry no information.
            continue
        lift = (cen[0] + up[0] * 0.01, cen[1] + up[1] * 0.01,
                cen[2] + up[2] * 0.01)
        h = _ray_up_hit(lift, up, verts, tris,
                        grid.near(lift[ax0], lift[ax1]))
        ok = h >= head
        out.append(NavPoly((p0, p1, p2), n, slope_here, h, area, cen, ok,
                           "" if ok else f"headroom {h:.2f} m < {head:.2f} m"))
    return out


def nav_area_m2(polys) -> float:
    return sum(p.area_m2 for p in polys if p.walkable)


# ===========================================================================
# 5.  The drum ground -- a heightfield sampled on its own lattice
# ===========================================================================

# Kinds `drum_ground.sample()` returns that are not floor. Exactly one entry,
# and it is not a style choice: `water_surface` is where the module clamps the
# terrain to the lake surface, so it is by construction the set of points that
# are under water rather than beside it.
NON_WALKABLE_KINDS = frozenset({"water_surface"})

# How many lattice cells the navmesh retreats from anything it cannot stand
# on. ONE, and the reason is the lattice itself rather than caution: the
# shoreline is a curve the 15.61 m lattice cannot resolve, so a cell whose own
# sample is dry can still be half under water, and the render of the navmesh
# shows the lake edge as a straight line where the terrain's is not. Erring
# outward puts the error where a player forgives it -- an NPC that stops a
# lattice cell short of the water -- rather than where they do not, which is
# an NPC walking on the lake. It costs 1.8% of the drum floor: 93.7% walkable
# without it, 91.9% with it.
SHORE_MARGIN_CELLS = 1


@dataclass
class GroundNav:
    stride: int
    na: int
    nz: int
    spacing_a_m: float
    spacing_z_m: float
    height: list           # [ia][iz] metres above the floor datum
    kind: list             # [ia][iz]
    slope: list            # [ia][iz] degrees
    walkable: list         # [ia][iz]
    floor_r_m: float
    z0: float
    z1: float

    def u(self, ia):
        return (ia % self.na) / self.na

    def w(self, iz):
        return iz / self.nz

    def xyz(self, ia, iz):
        """Station-space position of a lattice point, on the surface."""
        r = self.floor_r_m - self.height[ia % self.na][iz]
        a = 2.0 * math.pi * self.u(ia)
        return (r * math.cos(a), r * math.sin(a),
                self.z0 + self.w(iz) * (self.z1 - self.z0))

    def angle_deg(self, ia):
        return 360.0 * self.u(ia)

    def z_m(self, iz):
        return self.z0 + self.w(iz) * (self.z1 - self.z0)

    def nearest(self, angle_deg, z_m):
        """Lattice index nearest a station-space (angle, z), snapped to a
        walkable cell -- a spoke foot that lands in the lake is still a spoke
        foot, and the access point has to be the nearest dry ground."""
        ia = int(round((angle_deg % 360.0) / 360.0 * self.na)) % self.na
        iz = min(self.nz - 1, max(0, int(round(
            (z_m - self.z0) / (self.z1 - self.z0) * self.nz))))
        if self.walkable[ia][iz]:
            return ia, iz
        best, bd = None, None
        for da in range(-6, 7):
            for dz in range(-6, 7):
                a2, z2 = (ia + da) % self.na, iz + dz
                if not 0 <= z2 < self.nz or not self.walkable[a2][z2]:
                    continue
                d = da * da + dz * dz
                if bd is None or d < bd:
                    best, bd = (a2, z2), d
        return best if best else (ia, iz)


_GROUND_CACHE = {}


def ground_stride(schema=None) -> int:
    """The lattice decimation that gives GROUND_SPACING_M, as an integer
    stride of `drum_ground`'s own lattice -- and it must be one of that
    module's declared STRIDES, or the nav lattice and the render lattice would
    not share vertices and a nav cell would sit off the ground."""
    circ = 2.0 * math.pi * dg.FLOOR_R
    s = int(round(GROUND_SPACING_M / (circ / dg.CELLS_A)))
    return max(1, s)


def ground_nav(schema=None, profile=None, sector=None, stride=None) -> GroundNav:
    """Sample the drum's ground on the nav lattice and classify every cell.

    Every height here comes from `drum_ground.sample()`, the same function
    `drum_ground._vertex()` uses to place render vertices. There is no second
    heightfield and there is no cached copy: the nav lattice is a decimation
    of the render lattice, so a nav cell corner IS a render vertex.
    """
    if schema is None:
        schema, profile = it.load()
    if sector is None:
        sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    s = ground_stride(schema) if stride is None else stride
    key = (sector, s)
    if key in _GROUND_CACHE:
        return _GROUND_CACHE[key]

    na, nz = dg.CELLS_A // s, dg.CELLS_Z // s
    circ = 2.0 * math.pi * dg.FLOOR_R
    sp_a, sp_z = circ / na, (dg.Z1 - dg.Z0) / nz

    height = [[0.0] * nz for _ in range(na)]
    kind = [[""] * nz for _ in range(na)]
    for ia in range(na):
        for iz in range(nz):
            h, k = dg.sample((ia * s) / dg.CELLS_A, (iz * s) / dg.CELLS_Z)
            height[ia][iz] = h
            kind[ia][iz] = k

    slope = [[0.0] * nz for _ in range(na)]
    walk = [[False] * nz for _ in range(na)]
    lim = SLOPE_LIMIT_DEG
    for ia in range(na):
        for iz in range(nz):
            # Central difference where possible; the drum wraps in angle so the
            # circumferential difference never needs a boundary case -- which
            # is the loop STATE.md session 2w records a range(n) walk missing.
            ga = (height[(ia + 1) % na][iz] - height[(ia - 1) % na][iz]) / (2 * sp_a)
            z1i = min(nz - 1, iz + 1)
            z0i = max(0, iz - 1)
            gz = ((height[ia][z1i] - height[ia][z0i])
                  / max(1e-9, (z1i - z0i) * sp_z))
            slope[ia][iz] = math.degrees(math.atan(math.hypot(ga, gz)))
            walk[ia][iz] = (slope[ia][iz] <= lim
                            and kind[ia][iz] not in NON_WALKABLE_KINDS)

    # Retreat from the shoreline. Erosion, and the wrap is in it: cell 0's
    # circumferential neighbour is cell na-1, which a range(n) walk never
    # reaches and which is where the seam bug in this project always lives.
    for _ in range(SHORE_MARGIN_CELLS):
        keep = [row[:] for row in walk]
        for ia in range(na):
            for iz in range(nz):
                if not keep[ia][iz]:
                    continue
                for ja, jz in (((ia + 1) % na, iz), ((ia - 1) % na, iz),
                               (ia, min(nz - 1, iz + 1)), (ia, max(0, iz - 1))):
                    if not walk[ja][jz]:
                        keep[ia][iz] = False
                        break
        walk = keep

    gn = GroundNav(s, na, nz, sp_a, sp_z, height, kind, slope, walk,
                   dg.FLOOR_R, dg.Z0, dg.Z1)
    _GROUND_CACHE[key] = gn
    return gn


def reset_caches():
    """Drop every cached lattice and graph.

    Needed by `_selftest`, which proves its assertions can fail by monkey-
    patching `drum_ground` and rebuilding. Without this the break test would
    silently re-measure the unbroken cache and pass, which is exactly the
    class of vacuous assertion AAA-STANDARD ROBUSTNESS 0 is about.
    """
    _GROUND_CACHE.clear()
    _GRAPH_CACHE.clear()


# ===========================================================================
# 6.  Interior cells -- the corridor footprint, and its one measured check
# ===========================================================================

def cell_plan(schema, profile):
    """Every streaming cell in the station, as navigation metadata.

    Deliberately does NOT call `interior.deck_cell()`. Building 3,414 corridor
    meshes to learn 3,414 identical footprints costs minutes to produce a
    number `interior_kit.PROVISIONAL` already states. The footprint rule is
    checked once, against one real mesh, in `_selftest`.
    """
    decks, cells = [], []
    for sector in schema["sectors"]["extents_m"]:
        ex = schema["sectors"]["extents_m"][sector]
        z_mid = (ex["z0"] + ex["z1"]) / 2.0
        for ri, ring in enumerate(it.ring_radii(schema, profile, sector)):
            if ring["kind"] != "deck_stack":
                continue
            for deck in it.decks_in_ring(schema, profile, sector, ri):
                di = deck["deck_index"]
                plan = it.ring_cells(schema, profile, sector, ri, di)
                decks.append({
                    "id": f"{sector}.{ring['id']}.d{di}",
                    "sector": sector, "ring": ring["id"], "ring_index": ri,
                    "deck_index": di, "floor_r_m": deck["floor_r_m"],
                    "floor_g": deck["floor_g"], "use": deck["use"],
                    "z_mid": z_mid, "cells": plan["cells"],
                    "cell_deg": plan["cell_deg"],
                    "cell_length_m": plan["cell_length_m"],
                })
                for ci in range(plan["cells"]):
                    cells.append((f"{sector}.{ring['id']}.d{di}", ci))
    return decks, cells


def cell_nav_area_m2(cell_length_m: float, p=None) -> float:
    """Walkable floor of one streaming cell, from the kit's own section.

    A corridor's walkable width is the clear width between the wall faces:
    `corridor_width_m` less the two `wall_thickness_m` reveals the wall
    assembly stands in. Nothing else in the section reduces it -- the chamfer
    is above head height and the deck strip is flush.
    """
    p = ik.PROVISIONAL if p is None else p
    clear = p["corridor_width_m"] - 2.0 * p["wall_thickness_m"]
    return max(0.0, clear) * cell_length_m


def nav_from_ring_mesh(verts, tris, floor_r_m, band_m=None, slope_deg=None):
    """Walkable area of a mesh authored AROUND the spin axis.

    Two things differ from `nav_from_mesh` and both are consequences of the
    station's shape rather than conveniences:

      * **up varies per triangle.** In a ring corridor "up" is radially
        inward, so it is a different vector at every angle. A single up vector
        would classify the far side of the arc as a wall.
      * **a deck has a datum.** A corridor solid has an up-facing surface at
        the deck AND an up-facing surface on top of its ceiling slab, and the
        second is not floor. Restricting to within `band_m` of the deck's own
        radius removes it -- and `band_m` defaults to STEP_M, because anything
        within one step of the datum is the same floor by definition.

    Returns (area_m2, kept, rejected).
    """
    band = STEP_M if band_m is None else band_m
    cos_lim = math.cos(math.radians(SLOPE_LIMIT_DEG if slope_deg is None
                                    else slope_deg))
    area, kept, rejected = 0.0, 0, 0
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        n, tri_a = _tri_normal(p0, p1, p2)
        cx = (p0[0] + p1[0] + p2[0]) / 3.0
        cy = (p0[1] + p1[1] + p2[1]) / 3.0
        rad = math.hypot(cx, cy)
        if rad < 1e-9:
            continue
        up = (-cx / rad, -cy / rad, 0.0)
        if n[0] * up[0] + n[1] * up[1] + n[2] * up[2] <= cos_lim:
            continue
        if abs(rad - floor_r_m) > band:
            rejected += 1
            continue
        area += tri_a
        kept += 1
    return area, kept, rejected


def cell_centre(schema, deck, cell_index):
    """Station-space centre of a cell's floor, on the mid-arc."""
    a = math.radians((cell_index + 0.5) * deck["cell_deg"])
    r = deck["floor_r_m"]
    return (r * math.cos(a), r * math.sin(a), deck["z_mid"])


# ===========================================================================
# 7.  The graph
# ===========================================================================

WALK = "walk"
STAIR = "stair"
LIFT = "lift"
SPOKE = "spoke"
SHUTTLE = "shuttle"
TRAM = "tram"
GROUND_TRAM = "ground_tram"
DOOR = "door"
SEALED = "sealed"

TRANSIT_KINDS = frozenset({LIFT, SPOKE, SHUTTLE, TRAM, GROUND_TRAM})


@dataclass
class NavNode:
    id: str
    kind: str              # cell | ground | place | room | axis | platform
    pos: tuple             # station space, metres
    g: float               # local gravity in g
    area_m2: float = 0.0
    meta: dict = field(default_factory=dict)


@dataclass
class NavLink:
    a: str
    b: str
    kind: str
    distance_m: float
    rise_m: float
    g: float
    time_s: float
    effort: float


class NavGraph:
    """Nodes, links, and the two costs. Undirected except where stated."""

    def __init__(self):
        self.nodes = {}
        self.adj = {}
        self.links = []

    # -- construction ------------------------------------------------------
    def add_node(self, node: NavNode):
        self.nodes[node.id] = node
        self.adj.setdefault(node.id, [])
        return node.id

    def add_walk(self, a, b, distance_m, rise_m, g, kind=WALK, species="human"):
        t = walk_time_s(distance_m, rise_m, g, species)
        e = walk_effort(distance_m, rise_m, g)
        self._link(a, b, kind, distance_m, rise_m, g, t, e)

    def add_transit(self, a, b, kind, distance_m, ride_s, wait_s,
                    rise_m=0.0, g=0.0):
        # Effort of being carried is not zero -- you still walked onto the
        # platform and stood there -- but it is zero WORK, and pricing it as
        # anything else would be an invented constant doing the job of a
        # measured one. The walk to the platform is its own link and carries
        # its own effort.
        self._link(a, b, kind, distance_m, rise_m, g,
                   ride_s + wait_s + TRANSIT_DWELL_S, 0.0)

    def add_board(self, cell, car, wait_s, kind, g=0.0):
        """Step between a platform and the vehicle standing at it.

        HALF the wait and HALF the dwell, in BOTH directions, and that is
        arithmetic rather than a fudge: any one-way ride traverses this link
        exactly twice -- once boarding, once alighting -- so a rider pays one
        whole wait and one whole dwell per journey however many stops the
        vehicle passes through in between. A one-stop hop therefore costs
        precisely what it cost when the shaft was a chain of hops, while a
        ninety-six-stop ride stops paying ninety-six waits for one lift.
        """
        self._link(cell, car, kind, 0.0, 0.0, g,
                   (wait_s + TRANSIT_DWELL_S) / 2.0, 0.0)

    def add_ride(self, a, b, kind, distance_m, ride_s, rise_m=0.0, g=0.0):
        """A leg travelled INSIDE a vehicle: ride time alone. No wait, because
        the rider is already aboard; no dwell, because a car that stops for
        somebody else does not restart the journey."""
        self._link(a, b, kind, distance_m, rise_m, g, ride_s, 0.0)

    def _link(self, a, b, kind, distance_m, rise_m, g, t, e):
        if a not in self.nodes or b not in self.nodes:
            raise KeyError(f"link {a} -> {b}: node missing")
        ln = NavLink(a, b, kind, distance_m, rise_m, g, t, e)
        self.links.append(ln)
        self.adj[a].append((b, ln))
        # Rise reverses. A link that is uphill one way is downhill the other,
        # and pricing both directions off one `rise_m` made a stair free in
        # one direction and free in the other -- a symmetric error that a
        # symmetric graph hides completely.
        rev = NavLink(b, a, kind, distance_m, -rise_m, g,
                      walk_time_s(distance_m, -rise_m, g)
                      if kind in (WALK, STAIR) else t,
                      walk_effort(distance_m, -rise_m, g)
                      if kind in (WALK, STAIR) else e)
        self.links.append(rev)
        self.adj[b].append((a, rev))

    # -- queries -----------------------------------------------------------
    def cost(self, link: NavLink, metric: str):
        return link.time_s if metric == "time" else link.effort

    def path(self, a: str, b: str, metric: str = "time"):
        """Dijkstra. Ties broken on the node id, so a route is a pure function
        of (graph, endpoints, metric) and not of dict iteration order."""
        if a not in self.nodes or b not in self.nodes:
            raise KeyError(f"{a} or {b} not in graph")
        dist = {a: 0.0}
        prev = {}
        seen = set()
        q = [(0.0, a)]
        while q:
            d, u = heapq.heappop(q)
            if u in seen:
                continue
            seen.add(u)
            if u == b:
                break
            for v, ln in self.adj[u]:
                c = self.cost(ln, metric)
                if c == float("inf"):
                    continue
                nd = d + c
                if v not in dist or nd < dist[v] - 1e-12:
                    dist[v] = nd
                    prev[v] = (u, ln)
                    heapq.heappush(q, (nd, v))
        if b not in dist:
            return None
        route, cur = [], b
        while cur != a:
            u, ln = prev[cur]
            route.append(ln)
            cur = u
        route.reverse()
        return {
            "from": a, "to": b, "metric": metric,
            "cost": dist[b],
            "time_s": sum(l.time_s for l in route),
            "effort": sum(l.effort for l in route),
            "distance_m": sum(l.distance_m for l in route),
            "links": route,
            "kinds": tuple(sorted({l.kind for l in route})),
            "hops": len(route),
        }

    def islands(self):
        """Connected components, largest first. Each is (size, sorted ids)."""
        seen, out = set(), []
        for start in sorted(self.nodes):
            if start in seen:
                continue
            comp, q = [], deque([start])
            seen.add(start)
            while q:
                u = q.popleft()
                comp.append(u)
                for v, _ln in self.adj[u]:
                    if v not in seen:
                        seen.add(v)
                        q.append(v)
            out.append((len(comp), sorted(comp)))
        out.sort(key=lambda c: (-c[0], c[1][0]))
        return out

    def memory_bytes(self):
        """Resident cost of the graph itself.

        Counted as the engine would store it, not as CPython does: a node is
        an id, three doubles of position, one of gravity and one of area; a
        link is two node indices, a kind byte and three doubles. CPython's own
        footprint is an order of magnitude larger and says nothing about what
        the runtime pays.
        """
        node_b = len(self.nodes) * (16 + 5 * 8)
        link_b = (len(self.links) // 2) * (4 + 4 + 1 + 3 * 8)
        return node_b + link_b


_GRAPH_CACHE = {}


def build_graph(schema=None, profile=None, ground=True, interior=True,
                rooms=True, transit=True, cache_key=None):
    """The whole station's navigation graph, assembled from the modules.

    Order matters only for readability; every section is independent and the
    flags exist so `_selftest` can isolate one layer's failure from another's.
    """
    if schema is None:
        schema, profile = it.load()
    key = (ground, interior, rooms, transit, cache_key)
    if key in _GRAPH_CACHE:
        return _GRAPH_CACHE[key]

    G = NavGraph()
    drum = it.drum_sector(schema, profile)
    ex_drum = schema["sectors"]["extents_m"][drum]
    v_cap = coriolis_speed_cap(schema)

    # -- 7a. interior cells -------------------------------------------------
    decks, _cells = cell_plan(schema, profile)
    deck_by_id = {d["id"]: d for d in decks}
    if interior:
        for d in decks:
            for ci in range(d["cells"]):
                nid = f"cell:{d['id']}.c{ci}"
                G.add_node(NavNode(
                    nid, "cell", cell_centre(schema, d, ci), d["floor_g"],
                    cell_nav_area_m2(d["cell_length_m"]),
                    {"deck": d["id"], "cell_index": ci, "use": d["use"],
                     "sector": d["sector"], "ring_index": d["ring_index"],
                     "deck_index": d["deck_index"]}))
        # Ring corridors CLOSE. Cell i neighbours (i+1) % n, and the modulo is
        # the wrap: without it every deck in the station is a dead-ended arc
        # and a walk from cell 0 to cell n-1 goes the whole way round.
        for d in decks:
            n = d["cells"]
            for ci in range(n):
                G.add_walk(f"cell:{d['id']}.c{ci}",
                           f"cell:{d['id']}.c{(ci + 1) % n}",
                           d["cell_length_m"], 0.0, d["floor_g"])

    # -- 7b. radial transport tubes: the lift shafts ------------------------
    # THREE per sector, at the spoke angles. Not chosen: `interior.SPOKE_COUNT`
    # is 3 off the Green rosette (authority 3), LOCATIONS.md section 9 records
    # "radial transport tubes as spokes" named in five rosettes, and the Green
    # rosette draws exactly three. A shaft is radial, so it must line up across
    # every deck of every ring in its sector -- which is what makes one shaft
    # a single chain rather than a set of per-ring lifts.
    shaft_angles = tuple(i * 360.0 / it.SPOKE_COUNT for i in range(it.SPOKE_COUNT))
    shafts = {}
    if interior:
        for sector in schema["sectors"]["extents_m"]:
            sd = sorted((d for d in decks if d["sector"] == sector),
                        key=lambda d: -d["floor_r_m"])
            for ang in shaft_angles:
                chain = []
                for d in sd:
                    ci = int((ang % 360.0) // d["cell_deg"]) % d["cells"]
                    chain.append((d, f"cell:{d['id']}.c{ci}"))
                shafts[(sector, ang)] = chain
                if len(chain) < 2:
                    continue
                # A LIFT IS A VEHICLE, NOT A STAIRCASE, and modelling it as a
                # chain of deck-to-deck hops charged a fresh wait at every
                # floor. Measured: one hop is 2.4 s of ride and 22.4 s of
                # wait, so a resident crossing Grey's 105 decks paid 96 waits
                # -- 69.7 minutes, of which 67 were standing at lift doors.
                # Nobody rides a lift like that; you board once and press a
                # button. So the shaft gets a CAR LAYER: `lift:` nodes riding
                # inside the shaft, boarding pays the wait once, and the ride
                # between adjacent decks costs ride time alone. `lift_ride_s`
                # is linear in distance (1.5*dr/v_cap), so summing per-deck
                # rides equals one express ride EXACTLY -- no approximation is
                # introduced by keeping the layer segmented.
                span = chain[0][0]["floor_r_m"] - chain[-1][0]["floor_r_m"]
                wait = _headway_wait(_shaft_headway_s(schema, span))
                car = [f"lift:{sector}.{int(round(ang))}.{i}"
                       for i in range(len(chain))]
                for i, (d, cell) in enumerate(chain):
                    G.add_node(NavNode(car[i], "lift", G.nodes[cell].pos,
                                       d["floor_g"], 0.0,
                                       {"sector": sector, "angle_deg": ang,
                                        "deck": d["id"]}))
                    G.add_board(cell, car[i], wait, LIFT, g=d["floor_g"])
                for i in range(len(chain) - 1):
                    (da, _), (db, _) = chain[i], chain[i + 1]
                    dr = da["floor_r_m"] - db["floor_r_m"]
                    if dr <= 0.0:
                        continue
                    G.add_ride(car[i], car[i + 1], LIFT, dr,
                               lift_ride_s(schema, dr), rise_m=dr,
                               g=(da["floor_g"] + db["floor_g"]) / 2)

    # -- 7c. sector to sector, longitudinally -------------------------------
    # Sectors are longitudinal bands and a deck is a ring at the band's mid-z,
    # so a sector change is a walk along the axis at whatever radius both
    # sectors have a deck. Linked at the shaft angles and only where the two
    # decks are within one deck pitch of each other radially -- otherwise the
    # link would be a walk through 90 m of structure.
    if interior:
        order = sorted(schema["sectors"]["extents_m"],
                       key=lambda s: schema["sectors"]["extents_m"][s]["z0"])
        for s0, s1 in zip(order, order[1:]):
            for ang in shaft_angles:
                a_chain = shafts.get((s0, ang), [])
                b_chain = shafts.get((s1, ang), [])
                if not a_chain or not b_chain:
                    continue
                for da, na in a_chain:
                    db, nb = min(b_chain,
                                 key=lambda p: abs(p[0]["floor_r_m"]
                                                   - da["floor_r_m"]))
                    if abs(db["floor_r_m"] - da["floor_r_m"]) > it.DECK_PITCH_M:
                        continue
                    dz = abs(db["z_mid"] - da["z_mid"])
                    G.add_walk(na, nb, dz + abs(db["floor_r_m"] - da["floor_r_m"]),
                               0.0, (da["floor_g"] + db["floor_g"]) / 2.0)

    # -- 7d. the drum ground ------------------------------------------------
    gn = None
    if ground:
        gn = ground_nav(schema, profile, drum)
        r_floor = it.sector_radius(schema, profile, drum)
        g_ground = it.gravity_at(schema, r_floor)
        for ia in range(gn.na):
            for iz in range(gn.nz):
                if not gn.walkable[ia][iz]:
                    continue
                G.add_node(NavNode(
                    f"ground:{ia}.{iz}", "ground", gn.xyz(ia, iz),
                    it.gravity_at(schema, r_floor - gn.height[ia][iz]),
                    gn.spacing_a_m * gn.spacing_z_m,
                    {"kind": gn.kind[ia][iz], "slope_deg": gn.slope[ia][iz]}))
        # Four-neighbour, and the circumferential neighbour WRAPS. The drum is
        # a cylinder: ia = na-1 and ia = 0 are 15.6 m apart, not 1,733 m.
        for ia in range(gn.na):
            for iz in range(gn.nz):
                if not gn.walkable[ia][iz]:
                    continue
                a = f"ground:{ia}.{iz}"
                for (ja, jz, span) in (((ia + 1) % gn.na, iz, gn.spacing_a_m),
                                       (ia, iz + 1, gn.spacing_z_m)):
                    if not 0 <= jz < gn.nz or not gn.walkable[ja][jz]:
                        continue
                    dh = gn.height[ja][jz] - gn.height[ia][iz]
                    d = math.hypot(span, dh)
                    G.add_walk(a, f"ground:{ja}.{jz}", d, dh, g_ground)

    # -- 7e. the axis: the core shuttle -------------------------------------
    z_lo = min(schema["sectors"]["extents_m"][s]["z0"]
               for s in ("grey",) if s in schema["sectors"]["extents_m"])
    z_hi = max(schema["sectors"]["extents_m"][s]["z1"]
               for s in ("blue",) if s in schema["sectors"]["extents_m"])
    axis_ids = []
    if transit:
        # 13 stops, Blue to Grey (authority 4). The COUNT is sourced; the even
        # spacing over the served run is ours, and it is the only arrangement
        # that does not require a second invented fact per stop.
        leg = (z_hi - z_lo) / (CORE_SHUTTLE_STOPS - 1)
        ride = axial_ride_s(leg)
        # Headway from the round trip: 12 legs each way plus a dwell at every
        # stop, divided by the cars on the line.
        rt = 2 * ((CORE_SHUTTLE_STOPS - 1) * ride
                  + CORE_SHUTTLE_STOPS * TRANSIT_DWELL_S)
        wait = _headway_wait(rt / CORE_SHUTTLE_CARS)
        for i in range(CORE_SHUTTLE_STOPS):
            z = z_lo + i * leg
            nid = f"axis:{i}"
            axis_ids.append(nid)
            G.add_node(NavNode(nid, "axis", (0.0, 0.0, z), 0.0, 0.0,
                               {"z_m": z, "stop": i}))
        _car_layer(G, "shuttlecar", SHUTTLE, axis_ids,
                   [(leg, ride)] * (CORE_SHUTTLE_STOPS - 1), wait)

        # Each stop reaches the rim through the sector it lands in, on the
        # shaft chain's innermost deck. Without this the shuttle is a line
        # nobody can board and every axis node is its own island -- which is
        # precisely what the island test is for.
        if interior:
            for i, nid in enumerate(axis_ids):
                z = z_lo + i * leg
                sector = None
                for s, exs in schema["sectors"]["extents_m"].items():
                    if exs["z0"] <= z <= exs["z1"]:
                        sector = s
                        break
                if sector is None:
                    continue
                ang = shaft_angles[i % len(shaft_angles)]
                chain = shafts.get((sector, ang), [])
                if not chain:
                    continue
                d_in, n_in = chain[-1]
                dr = d_in["floor_r_m"]
                G.add_transit(nid, n_in, SPOKE, dr, lift_ride_s(schema, dr),
                              _headway_wait(_lift_headway_s(schema, dr)),
                              rise_m=-dr, g=d_in["floor_g"] / 2.0)

    # -- 7f. the drum's three spokes and its two tram systems ---------------
    if transit and ground and gn is not None:
        import core_tube as ct                               # noqa: PLC0415
        spoke_z = ct.spoke_z(schema, drum)
        r_floor = it.sector_radius(schema, profile, drum)
        g_ground = it.gravity_at(schema, r_floor)

        # The three radial spokes, at z = spoke_z, 120 degrees apart. They are
        # built geometry: `interior.drum_spokes` emits them and `core_tube`
        # gives their z. A spoke foot lands on the ground; a spoke head lands
        # on the axis at the nearest shuttle stop.
        for k, ang in enumerate(shaft_angles):
            ia, iz = gn.nearest(ang, spoke_z)
            foot = f"ground:{ia}.{iz}"
            if foot not in G.nodes:
                continue
            head = min(axis_ids, key=lambda n: abs(G.nodes[n].pos[2] - spoke_z)) \
                if axis_ids else None
            dr = r_floor - ct.CORE_TUBE_R_M
            if head:
                G.add_transit(foot, head, SPOKE, dr, lift_ride_s(schema, dr),
                              _headway_wait(_spoke_headway_s(schema, dr)),
                              rise_m=-dr, g=g_ground / 2.0)

        # The guideway tram: longitudinal, at TRUSS_RADIUS_FRAC of the floor.
        # Stops where the truss is anchored -- the two end-cap landings and the
        # spoke crossing -- because those are the only three places along 2.6 km
        # where the built structure reaches it.
        r_guide = r_floor * it.TRUSS_RADIUS_FRAC
        stops_z = (dg.cap_plane_z(schema, profile, drum, "aft") + dg.END_FADE_M,
                   spoke_z,
                   dg.cap_plane_z(schema, profile, drum, "fore") - dg.END_FADE_M)
        for k, ang in enumerate(shaft_angles):
            plat = []
            for j, z in enumerate(stops_z):
                nid = f"guideway:{k}.{j}"
                a = math.radians(ang)
                G.add_node(NavNode(nid, "platform",
                                   (r_guide * math.cos(a), r_guide * math.sin(a), z),
                                   it.gravity_at(schema, r_guide), 0.0,
                                   {"guideway": k, "stop": j}))
                plat.append((nid, z))
                # Getting to a platform 41.7 m above the ground: at the spoke
                # plane the spoke passes it; at a cap the landing is reached by
                # a lift in the cap face from the rim ring road.
                ia, iz = gn.nearest(ang, z)
                gid = f"ground:{ia}.{iz}"
                if gid in G.nodes:
                    dr = r_floor - r_guide
                    G.add_transit(gid, nid, LIFT, dr, lift_ride_s(schema, dr),
                                  _headway_wait(_lift_headway_s(schema, dr)),
                                  rise_m=-dr, g=g_ground / 2.0)
            if len(plat) > 1:
                legs = [(abs(plat[j + 1][1] - plat[j][1]),
                         axial_ride_s(abs(plat[j + 1][1] - plat[j][1])))
                        for j in range(len(plat) - 1)]
                rt = 2 * (sum(r for _d, r in legs)
                          + len(plat) * TRANSIT_DWELL_S)
                try:
                    import tram                               # noqa: PLC0415
                    cars = int(tram.drum_trams.__defaults__[0])
                except Exception:                             # noqa: BLE001
                    cars = 2
                _car_layer(G, f"tramcar{k}", TRAM, [p[0] for p in plat],
                           legs, _headway_wait(rt / max(1, cars)),
                           gs=[g_ground] * len(plat))

        # The ground tram: two circumferential loops, one on each rim ring
        # road, with a stop at every land-use band boundary. Both the roads and
        # the boundaries are built geometry -- `drum_ground._road_mask` puts the
        # ring roads at RIM_ROAD_INSET_M from each cap, and `interior.LAND_USE`
        # is the band table. Nothing here is placed by eye.
        bands = dg._bands()
        for loop, z_ring in enumerate((dg.Z0 + dg.RIM_ROAD_INSET_M,
                                       dg.Z1 - dg.RIM_ROAD_INSET_M)):
            stops = []
            for bi, (lo, _hi, _nm, _rel) in enumerate(bands):
                ang = lo * 360.0
                ia, iz = gn.nearest(ang, z_ring)
                gid = f"ground:{ia}.{iz}"
                if gid not in G.nodes:
                    continue
                nid = f"gtram:{loop}.{bi}"
                G.add_node(NavNode(nid, "platform", G.nodes[gid].pos,
                                   g_ground, 0.0,
                                   {"loop": loop, "band": bi, "ground": gid}))
                # Stepping onto a tram is a step, not a journey.
                G.add_walk(gid, nid, 2.0, 0.0, g_ground)
                stops.append((nid, ang))
            circ = 2.0 * math.pi * r_floor
            legs = [abs(((stops[(i + 1) % len(stops)][1] - stops[i][1]) % 360.0))
                    / 360.0 * circ for i in range(len(stops))] if stops else []
            rt = sum(ground_tram_ride_s(schema, a) for a in legs) \
                + len(stops) * TRANSIT_DWELL_S
            wait = _headway_wait(rt / GROUND_TRAM_CARS) if legs else 0.0
            if len(stops) > 1:
                _car_layer(G, f"gtramcar{loop}", GROUND_TRAM,
                           [s[0] for s in stops],
                           [(a, ground_tram_ride_s(schema, a)) for a in legs],
                           wait, gs=[g_ground] * len(stops), closed=True)

        # The Garden's floor has to reach the decks under it. The only nine
        # points where built structure crosses the ground plane are the three
        # spokes at their one z, and the three shaft angles at each cap rim
        # where the ring road runs. Anything else would be an invented stair.
        if interior:
            sub = [d for d in decks if d["sector"] == drum]
            if sub:
                d0 = min(sub, key=lambda d: d["floor_r_m"])
                for ang in shaft_angles:
                    for z in (dg.Z0 + dg.RIM_ROAD_INSET_M, spoke_z,
                              dg.Z1 - dg.RIM_ROAD_INSET_M):
                        ia, iz = gn.nearest(ang, z)
                        gid = f"ground:{ia}.{iz}"
                        ci = int((ang % 360.0) // d0["cell_deg"]) % d0["cells"]
                        cid = f"cell:{d0['id']}.c{ci}"
                        if gid in G.nodes and cid in G.nodes:
                            dr = d0["floor_r_m"] - r_floor
                            G.add_walk(gid, cid, dr * STAIR_GOING_M / STAIR_RISER_M
                                       + dr, dr, g_ground, kind=STAIR)

    # -- 7g. rooms, from their own meshes -----------------------------------
    if rooms and interior:
        for r in room_nav(schema, profile):
            G.add_node(NavNode(r["id"], "room", r["pos"], r["g"],
                               r.get("reachable_m2", 0.0), r))
            host = r.get("host")
            if host and host in G.nodes:
                # A door is a step over a sill, not a journey. Its length is
                # the door frame's own depth.
                G.add_walk(r["id"], host, ik.PROVISIONAL["door_frame_depth_m"],
                           0.0, r["g"], kind=DOOR)

    # -- 7h. named places ---------------------------------------------------
    #
    # TWO VOCABULARIES, ONE STATION. `schedule.PLACES` names 25 crowd regions;
    # `directory.PLACES` is the 118-row register a resident's home and job are
    # drawn from. Only the first was ever in the graph, so 101 register places
    # had no node and most residents had nowhere to walk to. Both go in, and
    # where a key is in both, the REGISTER's address wins: it carries a real
    # `(sector, ring, deck, angle_deg, z_m)` where a schedule entry has no
    # angle at all and `place_nodes` has to invent a deterministic bearing.
    if interior:
        reg = {p["id"]: p for p in register_nodes(schema, profile, G, decks)}
        rows = list(place_nodes(schema, profile, G, gn, decks))
        for p in rows:
            r = reg.pop(p["id"], None)
            if r is not None and r["host"] and not p["sealed"]:
                p = dict(p, host=r["host"], pos=r["pos"], g=r["g"],
                         area_m2=p["area_m2"] or r["area_m2"])
            _add_place(G, p)
        for r in sorted(reg.values(), key=lambda r: r["id"]):
            _add_place(G, r)

    _GRAPH_CACHE[key] = G
    return G


def _car_layer(G, prefix, kind, plats, legs, wait_s, gs=None, closed=False):
    """Put a RIDEABLE VEHICLE on a line of platforms, instead of charging a
    fresh fare at every stop.

    Every scheduled line in this graph was built the same wrong way: adjacent
    stops joined by a transit link that carries one wait and one dwell, so the
    router made a passenger get out, wait for the next car and get back in at
    every intermediate stop. Riding the core shuttle end to end cost twelve
    waits and thirteen dwells -- 39 minutes for an 11-minute journey -- and the
    radial shafts were worse, because Grey has 105 decks on one shaft.

    So each line gets a parallel chain of `prefix:i` nodes that live INSIDE the
    car. `add_board` joins platform to car for half a wait and half a dwell in
    each direction, which totals exactly one of each over any journey however
    many stops it passes; `add_ride` joins car to car for ride time alone.

    `closed` wraps the last stop to the first: a loop line, which the drum's
    circumferential trams are and the linear ones are not.
    """
    ids = [f"{prefix}:{i}" for i in range(len(plats))]
    for i, pid in enumerate(plats):
        g = (gs[i] if gs else 0.0)
        G.add_node(NavNode(ids[i], "car", G.nodes[pid].pos, g, 0.0,
                           {"line": prefix, "stop": i, "platform": pid}))
        G.add_board(pid, ids[i], wait_s, kind, g=g)
    n = len(plats) - (0 if closed else 1)
    for i in range(n):
        j = (i + 1) % len(plats)
        if j == i:
            continue
        dist_m, ride = legs[i]
        G.add_ride(ids[i], ids[j], kind, dist_m, ride,
                   g=(gs[i] if gs else 0.0))
    return ids


def _headway_wait(headway_s: float) -> float:
    """Mean wait for a vehicle on a `headway_s` service: half the headway, for
    a passenger who arrives without consulting a timetable."""
    return max(0.0, headway_s) / 2.0


def _lift_headway_s(schema, dr_m: float) -> float:
    """Round trip of a single lift car over `dr_m`, both ways plus two dwells."""
    return 2.0 * lift_ride_s(schema, dr_m) + 2.0 * TRANSIT_DWELL_S


def shaft_cars(schema, span_m: float) -> int:
    """How many cars a radial shaft runs. DERIVED, and INV-078 records it.

    Sized so the mean wait is about one dwell -- a car turns up roughly as
    often as it takes to load one -- which is the only self-consistent target
    available: `TRANSIT_DWELL_S` is already this project's measure of how long
    a door stands open, so a headway of two dwells is the point past which
    boarding, not waiting, becomes the cost of using the thing. Nothing in the
    show counts lift cars; what would overturn this is any frame showing a
    lift lobby, since the number of doors in it IS the bank.

    It falls out per sector rather than being tabulated: Grey's shaft spans
    382 m and gets 10 cars, Green's spans 29 m and gets 2. A long shaft needs
    more cars for the same service, which is why one constant could not have
    been right for all five.
    """
    return max(1, int(round(_lift_headway_s(schema, span_m)
                            / SHAFT_TARGET_HEADWAY_S)))


def _shaft_headway_s(schema, span_m: float) -> float:
    return _lift_headway_s(schema, span_m) / shaft_cars(schema, span_m)


def _spoke_headway_s(schema, dr_m: float) -> float:
    return _lift_headway_s(schema, dr_m) / max(1, SPOKE_LIFT_CARS)


# ===========================================================================
# 8.  Rooms -- the four built interiors, measured from their own meshes
# ===========================================================================

def _room_meshes():
    """Each built room, as (key, mesh, up, count, radius, angle_fn).

    Imported lazily and individually so that one module failing to import
    costs one room rather than the whole navmesh -- and so `room_nav` can
    report which one it lost instead of returning a short list silently.
    """
    out = []
    try:
        import docking_bay as db                             # noqa: PLC0415
        out.append(("docking_bay", db.docking_bay(), (0.0, 1.0, 0.0),
                    db.BAY_COUNT, "blue", db.bay_angle_deg,
                    "station/docking_bay.py"))
    except Exception as exc:                                 # noqa: BLE001
        out.append(("docking_bay", exc, None, 0, "blue", None, ""))
    try:
        import command_control as cc                         # noqa: PLC0415
        out.append(("command_control", cc.command_control(), (0.0, 1.0, 0.0),
                    1, "blue", lambda i: 0.0, "station/command_control.py"))
    except Exception as exc:                                 # noqa: BLE001
        out.append(("command_control", exc, None, 0, "blue", None, ""))
    try:
        import council_chamber as ccm                        # noqa: PLC0415
        out.append(("council_chamber", ccm.council_chamber(), (0.0, 1.0, 0.0),
                    1, "green", lambda i: 30.0, "station/council_chamber.py"))
    except Exception as exc:                                 # noqa: BLE001
        out.append(("council_chamber", exc, None, 0, "green", None, ""))
    try:
        import zocalo as zc                                  # noqa: PLC0415
        out.append(("zocalo_bay", zc.zocalo_bay(), (0.0, 1.0, 0.0),
                    1, "red", lambda i: 60.0, "station/zocalo.py"))
    except Exception as exc:                                 # noqa: BLE001
        out.append(("zocalo_bay", exc, None, 0, "red", None, ""))
    return out


_ROOM_CACHE = {}


def room_nav(schema=None, profile=None):
    """Walkable floor of every built room, extracted from its own mesh.

    This is the part of the module that is literally "navmesh generation from
    the built geometry": no dimension of any room appears here, only the
    criteria. If `docking_bay.BAY_H_M` changes, the headroom under the ledges
    changes, and this function returns a different answer without being edited.
    """
    if schema is None:
        schema, profile = it.load()
    if "rooms" in _ROOM_CACHE:
        return _ROOM_CACHE["rooms"]

    decks, _ = cell_plan(schema, profile)
    out = []
    for key, mesh, up, count, sector, angle_fn, src in _room_meshes():
        if up is None:
            out.append({"id": f"room:{key}", "error": str(mesh),
                        "walkable_m2": 0.0, "pos": (0.0, 0.0, 0.0),
                        "g": 0.0, "host": None, "source": src})
            continue
        verts, tris = mesh[0], mesh[1]
        polys = nav_from_mesh(verts, tris, up)
        obst = nav_obstacles(verts, tris, up)
        area = nav_area_m2(polys)                    # raw sum, over-counts
        regions = nav_regions(polys, up, obstacles=obst)
        plan = sum(r.area_m2 for r in regions)
        reach = regions[0].area_m2 if regions else 0.0
        tight = min((p.headroom_m for p in polys if p.walkable),
                    default=float("inf"))
        for i in range(max(1, count)):
            ang = angle_fn(i) if angle_fn else 0.0
            # Hosted on the outermost habitat deck of the sector's outer ring:
            # a room opens off a corridor and the corridor is the deck it is
            # cut into.
            cand = [d for d in decks if d["sector"] == sector]
            if not cand:
                host, hd = None, None
            else:
                hd = max((d for d in cand if d["use"] == "habitat"),
                         key=lambda d: d["floor_r_m"], default=None)
                if hd is None:
                    hd = max(cand, key=lambda d: d["floor_r_m"])
                ci = int((ang % 360.0) // hd["cell_deg"]) % hd["cells"]
                host = f"cell:{hd['id']}.c{ci}"
            r = hd["floor_r_m"] if hd else 0.0
            a = math.radians(ang)
            out.append({
                "id": f"room:{key}.{i}" if count > 1 else f"room:{key}",
                "room": key, "index": i, "sector": sector,
                "angle_deg": ang, "host": host, "source": src,
                "pos": (r * math.cos(a), r * math.sin(a),
                        hd["z_mid"] if hd else 0.0),
                "g": hd["floor_g"] if hd else 0.0,
                "walkable_m2": area,
                "plan_area_m2": plan,
                # What an NPC can actually stand on: the largest connected
                # component. The difference between the two is the finding.
                "reachable_m2": reach,
                "regions_n": len(regions),
                "stranded_m2": plan - reach,
                "regions": [(r.area_m2, r.height_m) for r in regions[:6]],
                "polys": len(polys),
                "walkable_polys": sum(1 for p in polys if p.walkable),
                "tightest_headroom_m": tight,
                "steepest_deg": max((p.slope_deg for p in polys if p.walkable),
                                    default=0.0),
            })
    _ROOM_CACHE["rooms"] = out
    return out


# ===========================================================================
# 9.  Named places -- FACTIONS.md 2.5, bound to geometry not to level numbers
# ===========================================================================
#
# C-003 and C-004 are OPEN and BLOCKING, and `FACTIONS.md` 0.2 is explicit that
# a faction bound to a *named facility* survives both closing and one bound to
# "Brown 4" does not. So a place is bound to (sector, ring CLASS), never to a
# level number, and the ring class is resolved to a ring INDEX here in one
# place -- when C-004 closes, this mapping changes and nothing else does.
RING_CLASS_INDEX = {"outer": 0, "middle": 1, "inner": 2, "axis": 3, "": 0}


def _add_place(G, p):
    """A place node and the door that reaches it. One place, one node, one edge.

    A **sealed** place gets the node, the floor and the door frame and NO
    traversable link -- the Markab quarter's quarantine made visible as a graph
    property rather than a comment. `island_report` expects exactly that one
    island; every other island is a defect.
    """
    G.add_node(NavNode(p["id"], "place", p["pos"], p["g"], p["area_m2"], p))
    if p["host"] and p["host"] in G.nodes and not p["sealed"]:
        # A door is a step over a sill, not a journey; its length is the frame.
        G.add_walk(p["id"], p["host"], ik.PROVISIONAL["door_frame_depth_m"],
                   0.0, p["g"], kind=DOOR)


def place_nodes(schema, profile, G, gn, decks):
    """Every `schedule.PLACES` entry, attached to a host cell or ground cell."""
    try:
        import schedule as sched                             # noqa: PLC0415
    except Exception:                                        # noqa: BLE001
        return []
    try:
        import crowd                                         # noqa: PLC0415
        extents = crowd.EXTENTS
    except Exception:                                        # noqa: BLE001
        extents = {}

    drum = it.drum_sector(schema, profile)
    out = []
    for key, pc in sorted(sched.PLACES.items()):
        area = extents[key].area_m2 if key in extents else 0.0
        host, pos, g = None, (0.0, 0.0, 0.0), 1.0

        if key == "the_garden" and gn is not None:
            ia, iz = gn.nearest(0.0, (gn.z0 + gn.z1) / 2.0)
            host = f"ground:{ia}.{iz}"
            if host in G.nodes:
                pos, g = G.nodes[host].pos, G.nodes[host].g
        else:
            sector = pc.sector
            # Downbelow has no sector in the schema: C-003 leaves the Brown
            # band unlabelled and the schema carries five sectors, not six.
            # `interior.py`'s own note on HABITABLE_G_MAX already rules on this
            # -- "use == 'plant' means UNASSIGNED, not uninhabited... the people
            # with no billet live in the outer stack among the machinery" -- so
            # Downbelow binds to plant decks. That is the THING, not the label,
            # and CLAUDE.md rule 5 says build the thing.
            want_use = "habitat"
            if key == "downbelow":
                sector, want_use = None, "plant"
            if key == "sanctuaries":
                # FACTIONS 13 proposes one per major pressurised sector.
                sector = "red"
            if sector == "drum":
                sector = drum
            cand = [d for d in decks
                    if (sector is None or d["sector"] == sector)
                    and d["use"] == want_use]
            if not cand and sector is not None:
                cand = [d for d in decks if d["sector"] == sector]
            if cand:
                ri = RING_CLASS_INDEX.get(pc.ring_class, 0)
                same = [d for d in cand if d["ring_index"] == ri] or cand
                d = max(same, key=lambda d: d["floor_r_m"])
                # Angle: deterministic per place, so a place lands in the same
                # cell on every machine and every run. blake2b, never hash().
                ang = _u("nav/place", key) * 360.0
                ci = int(ang // d["cell_deg"]) % d["cells"]
                host = f"cell:{d['id']}.c{ci}"
                if host in G.nodes:
                    pos, g = G.nodes[host].pos, G.nodes[host].g
        out.append({
            "id": f"place:{key}", "place": key, "host": host,
            "pos": pos, "g": g, "area_m2": area,
            "sector": pc.sector, "ring_class": pc.ring_class,
            "sealed": bool(pc.sealed),
        })
    return out


def register_nodes(schema, profile, G, decks):
    """Every `directory.PLACES` entry, attached at its OWN address.

    TWO VOCABULARIES DESCRIBED ONE STATION AND ONLY ONE OF THEM COULD BE
    ROUTED TO. `place_nodes` above walks `schedule.PLACES` -- 25 entries, of
    which 17 are also register keys -- so **101 of the register's 118 places
    had no node in the navigation graph at all**. A resident's `home` and `job`
    come from `directory.PLACES` (`npc/resident.py` resolves them by function),
    so for most of the station "walk to work" had no destination to walk to.

    It is also strictly better attached. A `schedule.PLACES` entry carries no
    angle, so `place_nodes` puts it at `_u("nav/place", key) * 360.0` -- a
    deterministic but arbitrary bearing. A register entry carries
    `(sector, ring, deck, angle_deg, z_m)`, so it lands in the cell it is
    actually addressed to, and those addresses are hull-correct as of this
    session (`interior.rings_fitting_at`).

    The eight schedule-only names -- `business_district`, `crew_country`,
    `customs_halls`, `dock_workers_quarters`, `fresh_air_restaurant`,
    `industrial_grey`, `markab_quarter`, `yellow_maintenance` -- are crowd
    REGIONS rather than rooms and keep their existing nodes. Nothing is
    removed; this adds what was missing.
    """
    import directory as _dr                                    # noqa: PLC0415

    by_sector = {}
    for d in decks:
        by_sector.setdefault(d["sector"], []).append(d)

    out = []
    for q in _dr.PLACES:
        sec = q.get("sector")
        cand = by_sector.get(sec) or []
        if not cand:
            continue
        # The deck whose ring index and z best match the address. Ring first,
        # because a ring is a radius and getting that wrong puts a person on
        # the wrong floor of the station; z second, to pick within the ring.
        ri = q.get("ring", 0)
        same = [d for d in cand if d["ring_index"] == ri] or cand
        d = min(same, key=lambda d: abs(d["z_mid"] - q.get("z_m", 0.0)))
        ang = q.get("angle_deg", 0.0) % 360.0
        ci = int(ang // d["cell_deg"]) % d["cells"]
        host = f"cell:{d['id']}.c{ci}"
        if host not in G.nodes:
            continue
        pos, g = G.nodes[host].pos, G.nodes[host].g
        out.append({
            "id": f"place:{q['key']}", "place": q["key"], "host": host,
            "pos": pos, "g": g,
            "area_m2": float(q["footprint"][0]) / 360.0
            * 2.0 * math.pi * d["floor_r_m"] * float(q["footprint"][1]),
            "sector": sec, "ring_class": None, "sealed": False,
        })
    return out


# ===========================================================================
# 10.  Reports
# ===========================================================================

# The one island the station is SUPPOSED to have. Everything else is a defect.
EXPECTED_ISLANDS = ("place:markab_quarter",)


def island_report(G=None, schema=None, profile=None):
    """Unreachable islands: how many, how big, and where.

    THE ASSERTION THAT MATTERS MOST in this module, because a navmesh with an
    unreachable island is a crowd standing still and nothing in a render says
    so. Reported rather than merely counted: a bare "1 island" tells a future
    session nothing about which volume nearly fell off.
    """
    if G is None:
        G = build_graph(schema, profile)
    comps = G.islands()
    rows = []
    for rank, (size, ids) in enumerate(comps):
        kinds = {}
        for n in ids:
            kinds[G.nodes[n].kind] = kinds.get(G.nodes[n].kind, 0) + 1
        rows.append({
            "size": size,
            "rank": rank,
            "main": rank == 0,
            "kinds": kinds,
            "example": ids[0],
            "members": ids,
            "places": sorted(n for n in ids if n.startswith("place:")),
            # The main island is the station. Every OTHER component is a
            # defect unless it is on the declared list -- and the declared
            # list has exactly one entry, which is a room that is sealed in
            # canon rather than a hole in the graph.
            "expected": rank == 0 or all(n in EXPECTED_ISLANDS for n in ids),
        })
    unexpected = [r for r in rows[1:] if not r["expected"]]
    return {
        "islands": len(comps),
        "largest": comps[0][0] if comps else 0,
        "nodes": len(G.nodes),
        "rows": rows,
        "unexpected": unexpected,
        "reachable_fraction": (comps[0][0] / max(1, len(G.nodes))) if comps else 0.0,
    }


def ground_report(schema=None, profile=None):
    """What the walkable criteria actually decided about the drum floor."""
    gn = ground_nav(schema, profile)
    n = gn.na * gn.nz
    by_kind = {}
    steep = 0
    worst = (0.0, None)
    for ia in range(gn.na):
        for iz in range(gn.nz):
            k = gn.kind[ia][iz]
            e = by_kind.setdefault(k, [0, 0])
            e[0] += 1
            if gn.walkable[ia][iz]:
                e[1] += 1
            if gn.slope[ia][iz] > SLOPE_LIMIT_DEG:
                steep += 1
            if gn.slope[ia][iz] > worst[0]:
                worst = (gn.slope[ia][iz], (ia, iz, k))
    walkable = sum(v[1] for v in by_kind.values())
    return {
        "stride": gn.stride,
        "lattice": (gn.na, gn.nz),
        "spacing_m": (gn.spacing_a_m, gn.spacing_z_m),
        "cells": n,
        "walkable": walkable,
        "walkable_fraction": walkable / n,
        "rejected_by_slope": steep,
        "rejected_by_kind": n - walkable - steep,
        "worst_slope_deg": worst[0],
        "worst_slope_at": worst[1],
        "slope_limit_deg": SLOPE_LIMIT_DEG,
        "by_kind": {k: tuple(v) for k, v in sorted(by_kind.items())},
        "area_m2": walkable * gn.spacing_a_m * gn.spacing_z_m,
    }


def coarse_graph(G=None, schema=None, profile=None):
    """The graph agents actually plan on: places, platforms, one node per deck.

    250,000 residents cannot each search a 20,000-node lattice, and they do not
    need to: a route is chosen between DISTRICTS and refined locally. This is
    the district graph, and its size is what makes the CPU budget hold.
    """
    if G is None:
        G = build_graph(schema, profile)
    keep = set()
    per_deck = {}
    for nid, node in G.nodes.items():
        if node.kind in ("place", "room", "axis", "platform"):
            keep.add(nid)
        elif node.kind == "cell":
            d = node.meta.get("deck")
            if d is not None and d not in per_deck:
                per_deck[d] = nid
    keep |= set(per_deck.values())
    return {
        "nodes": len(keep),
        "all_pairs_bytes": len(keep) ** 2 * 8,
        "members": sorted(keep),
    }


# CPU gate. 2,500 simulated agents (crowd.py's 500 full + 2,000 crowd) each
# replanning on an activity change. `schedule.activity_at` gives a resident
# about eight activity transitions in a 24 h station-day, and a station-day is
# 86,400 s -- so the steady-state demand is small and the gate exists to keep
# it that way rather than to be tight.
PLAN_BUDGET = {
    "agents": 2_500,
    "transitions_per_day": 8,
    "searches_per_s": 5_000.0,      # a coarse Dijkstra is tens of microseconds
    "fine_graph_mb": 4.0,
    "coarse_all_pairs_mb": 2.0,
}


def budget_report(G=None, schema=None, profile=None, out=print):
    """What navigation costs, in the only two currencies it spends.

    It spends NO triangles: nothing here is drawn. That is worth stating
    plainly because it is the one subsystem in this project whose cost is not
    a triangle count, and reaching for `budget.py`'s frame budget here would
    be a gate that measures the wrong thing -- AAA-STANDARD PERFORMANCE 1.
    """
    if G is None:
        G = build_graph(schema, profile)
    coarse = coarse_graph(G)
    fine_mb = G.memory_bytes() / 1e6
    coarse_mb = coarse["all_pairs_bytes"] / 1e6
    demand = (PLAN_BUDGET["agents"] * PLAN_BUDGET["transitions_per_day"]
              / 86_400.0)
    rows = [
        ("fine graph nodes", len(G.nodes), 40_000, ""),
        ("fine graph links", len(G.links) // 2, 80_000, ""),
        ("fine graph memory", fine_mb, PLAN_BUDGET["fine_graph_mb"], " MB"),
        ("coarse graph nodes", coarse["nodes"], 1_000, ""),
        ("coarse all-pairs", coarse_mb, PLAN_BUDGET["coarse_all_pairs_mb"], " MB"),
        ("searches / s", demand, PLAN_BUDGET["searches_per_s"], ""),
        ("triangles in frame", 0, 0, ""),
    ]
    ok = True
    for name, value, limit, unit in rows:
        good = value <= limit
        ok = ok and good
        out(f"{'PASS' if good else 'FAIL'}  {name:22s} "
            f"{value:>12,.3f}{unit} / {limit:,.3f}{unit}")
    out(f"\n{len(G.nodes):,} nodes, {len(G.links)//2:,} links, "
        f"{fine_mb:.2f} MB resident; agents plan on {coarse['nodes']} coarse "
        f"nodes, not on these.")
    return ok


def digest(G=None, schema=None, profile=None) -> str:
    """blake2b over every node and every link, for byte-for-byte comparison.

    AAA-STANDARD ROBUSTNESS 3 asks for determinism "verified across at least
    two PYTHONHASHSEED values byte for byte, not merely intended". This is the
    thing that gets compared; `_selftest` runs it in a subprocess under a
    different seed.
    """
    if G is None:
        G = build_graph(schema, profile)
    h = hashlib.blake2b(digest_size=16)
    for n in sorted(G.nodes):
        nd = G.nodes[n]
        h.update(f"{n}|{nd.kind}|{nd.pos[0]:.6f},{nd.pos[1]:.6f},"
                 f"{nd.pos[2]:.6f}|{nd.g:.6f}|{nd.area_m2:.4f}".encode())
    for l in sorted((l.a, l.b, l.kind, round(l.time_s, 6),
                     round(l.effort, 6)) for l in G.links):
        h.update(str(l).encode())
    return h.hexdigest()


def report(out=print):
    schema, profile = it.load()
    out("Walkable criteria, and where each was read out of\n")
    for k, v in criteria().items():
        out(f"  {k:18s} {v['value']:>8.3f}   {v['from']}")
    out(f"\n  walk speed at 1.000 g   {walk_speed(1.0):.3f} m/s "
        f"(Froude {FROUDE_PREFERRED}, leg {_LEG_HUMAN:.3f} m)")
    for sec in sorted(schema["sectors"]["extents_m"]):
        r = it.sector_radius(schema, profile, sec)
        g = it.gravity_at(schema, r)
        out(f"  {sec:7s} outermost deck {r:7.1f} m  {g:5.3f} g  "
            f"walk {walk_speed(g):.3f} m/s  climb {climb_speed(g):.3f} m/s")
    out(f"\n  Coriolis speed cap      {coriolis_speed_cap(schema):.3f} m/s "
        f"(2*omega*v <= {MAX_LATERAL_G} g) -- lifts AND the ring tram")
    out(f"  rim-to-axis ride        {lift_ride_s(schema, 278.3):.1f} s")

    gr = ground_report(schema, profile)
    out(f"\nDrum ground: {gr['lattice'][0]}x{gr['lattice'][1]} lattice at "
        f"{gr['spacing_m'][0]:.2f} x {gr['spacing_m'][1]:.2f} m")
    out(f"  walkable {gr['walkable']:,}/{gr['cells']:,} "
        f"({gr['walkable_fraction']*100:.1f}%), "
        f"{gr['area_m2']/1e6:.2f} million m2")
    out(f"  worst slope {gr['worst_slope_deg']:.2f} deg against a "
        f"{gr['slope_limit_deg']:.2f} deg limit; "
        f"{gr['rejected_by_slope']} cells rejected by slope, "
        f"{gr['rejected_by_kind']} by kind")

    out("\nRooms, measured from their own meshes\n")
    for r in room_nav(schema, profile):
        if r.get("error"):
            out(f"  {r['id']:26s} FAILED: {r['error']}")
            continue
        if r.get("index", 0) > 0:
            continue
        out(f"  {r['room']:18s} {r['plan_area_m2']:8.1f} m2 floor, "
            f"{r['reachable_m2']:8.1f} m2 REACHABLE in {r['regions_n']:3d} "
            f"regions, tightest headroom {r['tightest_headroom_m']:.2f} m "
            f"({r['walkable_m2']:.0f} m2 if you sum triangles)")

    G = build_graph(schema, profile)
    isl = island_report(G)
    out(f"\nIslands: {isl['islands']}, largest {isl['largest']:,} of "
        f"{isl['nodes']:,} nodes ({isl['reachable_fraction']*100:.2f}%)")
    for r in isl["rows"][:6]:
        tag = "main" if r["main"] else ("expected" if r["expected"]
                                        else "UNEXPECTED")
        out(f"  {r['size']:>7,}  {r['example']:34s} {tag:10s} "
            f"{r['places'][:3]}")
    out("\nRoutes -- and why the shortest one is not the answer\n")
    for a, b, why in _demo_routes(G):
        pt = G.path(a, b, "time")
        pe = G.path(a, b, "effort")
        if not pt or not pe:
            out(f"  {a} -> {b}: no route")
            continue
        out(f"  {a} -> {b}   {why}")
        out(f"     fastest  {pt['time_s']/60:7.1f} min  "
            f"{pt['distance_m']:8.0f} m  effort {pt['effort']:8.0f}  "
            f"via {'+'.join(sorted(pt['kinds']))}")
        out(f"     easiest  {pe['time_s']/60:7.1f} min  "
            f"{pe['distance_m']:8.0f} m  effort {pe['effort']:8.0f}  "
            f"via {'+'.join(sorted(pe['kinds']))}")
    out("")
    budget_report(G, out=out)
    return G


def _demo_routes(G):
    """A few endpoint pairs that show the cost model doing something.

    Chosen by RULE rather than by hand so the demonstration cannot be tuned:
    the first place node in each of three sectors, the axis, and the two ends
    of a ground-tram loop.
    """
    out = []
    places = sorted(n for n in G.nodes if n.startswith("place:"))
    if "place:zocalo" in G.nodes and "place:downbelow" in G.nodes:
        out.append(("place:zocalo", "place:downbelow",
                    "commercial ring to the 1.7 g basement"))
    if "place:the_garden" in G.nodes and "place:crew_country" in G.nodes:
        out.append(("place:the_garden", "place:crew_country",
                    "drum floor to Blue crew country, 2.6 km of sector"))
    gt = sorted(n for n in G.nodes if n.startswith("gtram:0."))
    if len(gt) >= 4:
        a = G.nodes[gt[0]].meta["ground"]
        b = G.nodes[gt[len(gt) // 2]].meta["ground"]
        out.append((a, b, "half way round the drum on the rim road"))
    if places and "axis:6" in G.nodes:
        out.append((places[0], "axis:6", "a named place to the core shuttle"))
    return out


# ===========================================================================
# 11.  Debug mesh -- so the navmesh can be looked at
# ===========================================================================

def ground_nav_mesh(schema=None, profile=None):
    """The walkable ground as triangles, for `tools/preview_render.py`.

    WINDING: the drum is seen from its concave side, so these faces must point
    toward the spin axis -- the same convention `interior.drum_interior()` uses
    and the same one four subsystems in this project have shipped backwards.
    `_selftest` measures it with `interior._inward_fraction` rather than
    trusting the loop, because an inverted navmesh renders black and a black
    frame reads as a badly placed camera.
    """
    gn = ground_nav(schema, profile)
    verts, tris, groups = [], [], []
    lift = 0.35              # stand the sheet off the ground so it is visible
    for ia in range(gn.na):
        for iz in range(gn.nz - 1):
            ja = (ia + 1) % gn.na
            if not (gn.walkable[ia][iz] and gn.walkable[ja][iz]
                    and gn.walkable[ia][iz + 1] and gn.walkable[ja][iz + 1]):
                continue
            quad = []
            for (a, z) in ((ia, iz), (ja, iz), (ja, iz + 1), (ia, iz + 1)):
                x, y, zz = gn.xyz(a, z)
                r = math.hypot(x, y)
                k = (r - lift) / r
                quad.append((x * k, y * k, zz))
            b = len(verts)
            verts.extend(quad)
            # Radius DECREASES inward, so the ordering that gives an outward
            # normal on a hull gives an inward one here. Checked, not assumed.
            tris.append((b, b + 2, b + 1))
            tris.append((b, b + 3, b + 2))
            groups.extend(["nav_ground"] * 2)
    return verts, tris, groups


def write_obj(path, schema=None, profile=None):
    verts, tris, groups = ground_nav_mesh(schema, profile)
    it.write_grouped_obj(path, verts, tris, groups)
    return len(verts), len(tris)


# ===========================================================================
# 12.  Self-test
# ===========================================================================

_passed = 0
_failed = 0


def check(ok, name, detail=""):
    global _passed, _failed
    if ok:
        _passed += 1
    else:
        _failed += 1
        print(f"  FAIL  {name}" + (f"  --  {detail}" if detail else ""))
    return bool(ok)


def _selftest():
    global _passed, _failed
    _passed = _failed = 0
    schema, profile = it.load()
    drum = it.drum_sector(schema, profile)

    # -- criteria: each one derived, and each one bracketed ----------------
    check("fallback" not in STAIR_SOURCE,
          "the stair pitch was READ from zocalo.py, not fallen back to",
          STAIR_SOURCE)
    check(abs(STEP_M - ik.PROVISIONAL["door_sill_m"]) < 1e-12,
          "STEP_M is the kit's door sill, imported not copied")
    check(STEP_M < STAIR_RISER_M,
          "step limit is below the stair riser -- at or above it a flight of "
          "stairs classifies as flat ground",
          f"{STEP_M} vs {STAIR_RISER_M}")
    check(STEP_M >= ik.PROVISIONAL["door_sill_m"],
          "step limit clears the door sill -- below it every door in the "
          "station is impassable")
    check(abs(HEADROOM_M - ik.PROVISIONAL["door_height_m"]) < 1e-12,
          "headroom is the kit's door height, imported not copied")
    try:
        import body                                          # noqa: PLC0415
        tallest = max(sp.stature_m for sp in body.SPECIES.values())
        check(HEADROOM_M > tallest,
              "headroom clears the tallest species standing",
              f"{HEADROOM_M} vs {tallest}")
    except Exception as exc:                                 # noqa: BLE001
        check(False, "body.py importable for the stature cross-check", str(exc))
    check(30.0 < SLOPE_LIMIT_DEG < 45.0,
          "slope limit is a stair pitch, not a wall or a ramp",
          f"{SLOPE_LIMIT_DEG:.2f}")
    check(ground_stride() in dg.STRIDES,
          "the nav lattice stride is one of drum_ground's own LOD strides, so "
          "a nav corner IS a render vertex",
          f"{ground_stride()} not in {dg.STRIDES}")
    check(abs(GROUND_SPACING_M - dg._step_ramp_m() / 2.0) < 1e-9,
          "nav spacing is half a stride-8 cell -- two samples across the "
          "narrowest step drum_ground permits")

    # -- locomotion --------------------------------------------------------
    v1 = walk_speed(1.0)
    check(1.35 < v1 < 1.60,
          "Froude walk speed at 1 g lands on measured human preferred speed "
          "(~1.4 m/s) from a relation not fitted to it", f"{v1:.3f}")
    check(walk_speed(1.693) > walk_speed(0.559) * 1.5,
          "walking is FASTER in Grey's basement than in Yellow -- sqrt(g)",
          f"{walk_speed(1.693):.3f} vs {walk_speed(0.559):.3f}")
    check(climb_speed(1.693) < climb_speed(0.559),
          "climbing is SLOWER at high g -- a climb is power-limited where a "
          "walk is pendulum-limited")
    check(walk_speed(0.0) == 0.0,
          "zero g is not walking; the axis has no walk link")
    check(walk_effort(100.0, 0.0, 1.693) > walk_effort(100.0, 0.0, 1.0),
          "effort scales with local gravity")
    check(walk_time_s(100.0, 10.0, 1.0) > walk_time_s(100.0, 0.0, 1.0),
          "a rise costs time (Naismith ascent term)")
    check(abs(walk_time_s(100.0, -10.0, 1.0)
              - walk_time_s(100.0, 0.0, 1.0)) < 1e-9,
          "descent is free, which is what Naismith says")

    # -- transit: the closed form against the physics module ---------------
    cap = coriolis_speed_cap(schema)
    check(3.0 < cap < 3.3,
          "the Coriolis speed cap is ~3.13 m/s", f"{cap:.3f}")
    try:
        from physics.core_shuttle import comfortable_duration  # noqa: PLC0415
        from physics.rotating_frame import from_schema         # noqa: PLC0415
        d = from_schema(schema)
        ref = comfortable_duration(d, 278.3, 0.0)
        mine = lift_ride_s(schema, 278.3)
        check(abs(ref - mine) / ref < 0.005,
              "the closed-form lift ride agrees with physics/core_shuttle's "
              "bisection -- two derivations sharing no arithmetic",
              f"{ref:.2f} vs {mine:.2f}")
        check(130.0 < ref < 137.0,
              "and both land on LOCATIONS.md section 9's quoted 133 s",
              f"{ref:.1f}")
    except Exception as exc:                                 # noqa: BLE001
        check(False, "physics/core_shuttle importable", str(exc))
    check(axial_ride_s(1000.0) < 1000.0 / cap,
          "axial transit beats the Coriolis cap, because motion along the "
          "spin axis produces no Coriolis at all -- this is why the drum has "
          "two tram systems")

    # -- the mesh extractor, on the built rooms ----------------------------
    rooms = room_nav(schema, profile)
    bad = [r for r in rooms if r.get("error")]
    check(not bad, "every room module imported and emitted a mesh",
          str([r["id"] for r in bad]))
    by_room = {}
    for r in rooms:
        by_room.setdefault(r.get("room"), r)
    for name in ("docking_bay", "command_control", "council_chamber",
                 "zocalo_bay"):
        r = by_room.get(name)
        check(r is not None and r["walkable_m2"] > 5.0,
              f"{name} has walkable floor extracted from its own mesh",
              f"{r['walkable_m2'] if r else 0:.1f} m2")
        check(r is not None and r["steepest_deg"] <= SLOPE_LIMIT_DEG + 1e-6,
              f"{name} emits no walkable polygon steeper than the limit")
    # The room-scale island test, and it finds three things in built geometry
    # that no render reports and no existing assertion covers.
    dbr = by_room.get("docking_bay")
    check(dbr is not None and dbr["regions_n"] > 1,
          "the docking bay's walkable surfaces are NOT all one piece: the "
          "stepped side ledges are 2.2 m risers and nothing reaches them "
          "from the deck",
          f"{dbr['regions_n'] if dbr else 0} regions, "
          f"{dbr['stranded_m2'] if dbr else 0:.0f} m2 stranded")
    check(dbr is not None and dbr["reachable_m2"] < dbr["plan_area_m2"] * 0.75,
          "and under half the bay's walkable surface is reachable, which is "
          "the distinction the crowd layer has to spawn against",
          f"{dbr['reachable_m2'] if dbr else 0:.0f} of "
          f"{dbr['plan_area_m2'] if dbr else 0:.0f} m2")
    try:
        import docking_bay as _dbm                           # noqa: PLC0415
        # The reachable deck is NOT the full bay width. The first ledge riser
        # stands on the deck at |x| = hw - LEDGE_RUN_M, so the outer 3.4 m
        # each side is an undercroft walled off from the bay floor. That is a
        # finding about built geometry, and it is derived from the module's
        # own constants rather than from this number being observed.
        clear_w = _dbm.BAY_W_M - 2 * _dbm.LEDGE_RUN_M
        want = clear_w * _dbm.BAY_LEN_M
        check(abs(dbr["reachable_m2"] - want) < want * 0.06,
              "the reachable deck is the bay width LESS the two ledge runs -- "
              "the first riser walls off the outer 3.4 m each side",
              f"{dbr['reachable_m2']:.0f} m2 vs "
              f"{clear_w:.1f} x {_dbm.BAY_LEN_M:.0f} = {want:.0f} m2")
        check(dbr["reachable_m2"] < _dbm.BAY_W_M * _dbm.BAY_LEN_M * 0.95,
              "and it is measurably smaller than the nominal bay deck, so the "
              "riser is doing the work rather than the raster")
    except Exception as exc:                                 # noqa: BLE001
        check(False, "docking bay projection check", repr(exc))

    db = by_room.get("docking_bay")
    if db:
        # The corbelled ledges give the outer strip of the bay deck 2.20 m of
        # clearance. That is 0.10 m over the criterion and is the tightest
        # standing headroom in the built station -- a number no render reports.
        check(2.0 < db["tightest_headroom_m"] < 2.6,
              "the docking bay's tightest walkable headroom is the ledge "
              "undercroft, and it clears by a tenth of a metre",
              f"{db['tightest_headroom_m']:.3f}")
        try:
            import docking_bay as dbm                        # noqa: PLC0415
            v, t, _g = dbm.docking_bay()
            tighter = nav_from_mesh(v, t, (0.0, 1.0, 0.0),
                                    headroom_m=db["tightest_headroom_m"] + 0.05)
            check(nav_area_m2(tighter) < db["walkable_m2"],
                  "raising the headroom criterion by 5 cm REMOVES floor from "
                  "the bay -- the criterion is load-bearing, not decorative",
                  f"{nav_area_m2(tighter):.1f} vs {db['walkable_m2']:.1f}")
        except Exception as exc:                             # noqa: BLE001
            check(False, "docking bay re-extraction", str(exc))

    # -- the analytic cell footprint against a REAL cell mesh --------------
    # The one shortcut in the module, and the only one that is checked.
    try:
        decks, _ = cell_plan(schema, profile)
        d = max((x for x in decks if x["sector"] == "red"),
                key=lambda x: x["floor_r_m"])
        v, t, meta = it.deck_cell(schema, profile, d["sector"],
                                  d["ring_index"], d["deck_index"], 0)
        deck_area, kept, rejected = nav_from_ring_mesh(v, t, d["floor_r_m"])
        analytic = cell_nav_area_m2(d["cell_length_m"])
        # The mesh's deck plate runs the FULL nominal corridor width, because
        # the wall assembly stands on it. The analytic figure is the CLEAR
        # width between the wall faces, so it must come out slightly under
        # the measured plate -- and by the ratio of those two widths, not by
        # an arbitrary factor.
        ratio = deck_area / analytic
        want = (ik.PROVISIONAL["corridor_width_m"]
                / (ik.PROVISIONAL["corridor_width_m"]
                   - 2 * ik.PROVISIONAL["wall_thickness_m"]))
        check(0.85 < ratio < want * 1.35,
              "the analytic cell footprint matches what a real deck_cell mesh "
              "measures -- one built cell validating the rule used for 3,414",
              f"analytic {analytic:.1f} m2, measured {deck_area:.1f} m2, "
              f"ratio {ratio:.2f} against a predicted {want:.2f}")
        check(rejected > 0,
              "the deck-datum band rejected something -- a corridor solid has "
              "an up-facing surface on TOP of its ceiling slab and that is "
              "not floor", f"rejected {rejected}, kept {kept}")
        check(analytic > 0.0 and analytic < d["cell_length_m"]
              * ik.PROVISIONAL["corridor_width_m"],
              "the analytic footprint is the CLEAR width, narrower than the "
              "nominal corridor width")
        wide, _k, _r = nav_from_ring_mesh(v, t, d["floor_r_m"], band_m=1e6)
        check(wide > deck_area * 1.2,
              "BREAK: removing the deck-datum band lets ceiling tops in and "
              "inflates the footprint -- the band is load-bearing",
              f"{wide:.1f} m2 unbanded vs {deck_area:.1f} m2 banded")
    except Exception as exc:                                 # noqa: BLE001
        check(False, "deck_cell cross-check", repr(exc))

    # -- the ground -------------------------------------------------------
    gn = ground_nav(schema, profile, drum)
    gr = ground_report(schema, profile)
    check(gn.na * gn.stride == dg.CELLS_A and gn.nz * gn.stride == dg.CELLS_Z,
          "the nav lattice divides drum_ground's lattice exactly")
    check(gr["worst_slope_deg"] < SLOPE_LIMIT_DEG,
          "the drum ground contains no slope the criteria reject -- which is "
          "a consequence of drum_ground's LOD step rule, not of a lenient "
          "limit", f"{gr['worst_slope_deg']:.2f} vs {SLOPE_LIMIT_DEG:.2f}")
    check(gr["rejected_by_kind"] > 500,
          "water IS rejected: the lake is not walkable and the count is real",
          str(gr["rejected_by_kind"]))
    check(0.90 < gr["walkable_fraction"] < 0.98,
          "most of the drum floor is walkable and some of it is not",
          f"{gr['walkable_fraction']:.3f}")
    # The heights are drum_ground's, not a copy: sample the module directly.
    h_ref, k_ref = dg.sample(0.25, 0.5)
    ia = int(0.25 * gn.na)
    iz = int(0.5 * gn.nz)
    check(abs(gn.height[ia][iz] - h_ref) < 1e-9 and gn.kind[ia][iz] == k_ref,
          "the nav lattice holds drum_ground's own heights, not a second "
          "heightfield")

    # -- the graph --------------------------------------------------------
    G = build_graph(schema, profile)
    check(len(G.nodes) > 15_000, "the graph was built", str(len(G.nodes)))
    check(all(l.time_s >= 0.0 for l in G.links), "no negative traversal times")
    check(all(l.time_s < float("inf") for l in G.links),
          "no infinite traversal times -- an infinite link is an unreachable "
          "island wearing a disguise")

    # THE WRAP. A path around the cylinder must go the short way.
    decks, _ = cell_plan(schema, profile)
    d = max((x for x in decks if x["sector"] == "red"),
            key=lambda x: x["floor_r_m"])
    n = d["cells"]
    a0, a1 = f"cell:{d['id']}.c0", f"cell:{d['id']}.c{n-1}"
    p = G.path(a0, a1)
    check(p is not None and p["hops"] == 1,
          "a ring corridor CLOSES: cell 0 and cell n-1 are one hop apart, not "
          f"{n-1}", f"hops={p['hops'] if p else None}, cells={n}")
    check(p is not None and p["distance_m"] < d["cell_length_m"] * 1.01,
          "and the wrap link is one cell long, not the whole circumference")

    # The same, on the ground lattice, where the wrap is 15.6 m against 1,733.
    ia0, iz0 = gn.nearest(2.0, (gn.z0 + gn.z1) / 2.0)
    ia1, iz1 = gn.nearest(358.0, (gn.z0 + gn.z1) / 2.0)
    g0, g1 = f"ground:{ia0}.{iz0}", f"ground:{ia1}.{iz1}"
    if g0 in G.nodes and g1 in G.nodes:
        pw = G.path(g0, g1)
        short = abs(((358.0 - 2.0 + 180.0) % 360.0) - 180.0) / 360.0 \
            * 2 * math.pi * gn.floor_r_m
        long_way = 2 * math.pi * gn.floor_r_m - short
        check(pw is not None and pw["distance_m"] < long_way * 0.5,
              "the drum ground WRAPS: 2 deg to 358 deg goes the short way "
              f"(~{short:.0f} m), not the long way (~{long_way:.0f} m)",
              f"{pw['distance_m'] if pw else None:.0f} m")
    else:
        check(False, "ground wrap endpoints exist")

    # -- ISLANDS ----------------------------------------------------------
    isl = island_report(G)
    check(isl["reachable_fraction"] > 0.999,
          "essentially every node is in the main island",
          f"{isl['reachable_fraction']:.5f}")
    unexpected = [r for r in isl["rows"][1:] if not r["expected"]]
    check(not unexpected,
          "no unexpected island: the only thing cut off from the station is "
          "the sealed Markab quarter",
          str([(r["size"], r["example"]) for r in unexpected[:4]]))
    check(any(r["expected"] and r["size"] == 1 for r in isl["rows"][1:])
          or isl["islands"] == 1,
          "the Markab quarter is sealed and shows up as its own island")

    # Every named place reachable from every other, which is the thing the
    # crowd layer actually needs and the thing an island silently breaks.
    places = [n for n in G.nodes if n.startswith("place:")]
    main = set(isl["rows"][0]["places"])
    stranded = [p for p in places
                if p not in main and p not in EXPECTED_ISLANDS]
    check(not stranded, "every non-sealed named place is reachable",
          str(stranded[:6]))
    rooms_n = [n for n in G.nodes if n.startswith("room:")]
    main_ids = set(isl["rows"][0]["members"])
    check(all(r in main_ids for r in rooms_n),
          "every built room is reachable from the rest of the station",
          str([r for r in rooms_n if r not in main_ids][:5]))
    check(len(rooms_n) >= 27,
          "24 docking bays plus C&C, the Council Chamber and a Zocalo bay are "
          "all in the graph", str(len(rooms_n)))

    # -- THE REGISTER IS IN THE GRAPH --------------------------------------
    # The gate that would have caught a station where 101 of 118 places had no
    # node. A resident's home and job are register keys, so a register key
    # with no node is a person with nowhere to go, and nothing else here
    # notices: the island report was clean throughout, because a node that was
    # never added cannot be stranded.
    import directory as _dr                                    # noqa: PLC0415
    reg_ids = {"place:" + q["key"] for q in _dr.PLACES}
    have = set(places)
    check(reg_ids <= have,
          f"all {len(reg_ids)} register places have a navigation node",
          f"missing {sorted(reg_ids - have)[:6]}")
    sched_only = {p["id"] for p in place_nodes(schema, profile, G, gn, decks)}
    check(len(reg_ids - sched_only) > 90,
          "BREAK: the schedule vocabulary ALONE leaves 90+ register places "
          "with no node -- so the check above passes on `register_nodes` "
          "rather than on what the graph already had",
          f"{len(reg_ids - sched_only)} of {len(reg_ids)} would be missing")

    # -- COMMUTES: can a resident actually get to work? --------------------
    # The product question, and the only one that composes the register, the
    # resident generator and the graph. Not "is the graph connected" -- it was
    # connected while most of it was unaddressable.
    import resident as _rs                                     # noqa: PLC0415
    spec = ("human", "human", "human", "narn", "centauri", "minbari")
    trips, unroutable = [], []
    for i in range(120):
        res = _rs.resident(f"navgate/{i}", spec[i % len(spec)])
        if not res.job:
            continue
        rp = G.path("place:" + res.home, "place:" + res.job, metric="time")
        (trips if rp else unroutable).append(rp or (res.home, res.job))
    check(not unroutable and len(trips) > 50,
          f"every one of {len(trips)} sampled residents can walk from home to "
          "work", f"unroutable {unroutable[:4]}")
    tsec = sorted(t["time_s"] for t in trips)
    med, p95 = tsec[len(tsec) // 2], tsec[int(len(tsec) * 0.95)]
    check(med < 20 * 60.0 and p95 < 45 * 60.0,
          "and the commute is a commute rather than an expedition: median "
          f"{med / 60:.1f} min, p95 {p95 / 60:.1f} min on a station 8 km long",
          f"max {tsec[-1] / 60:.1f} min")

    # -- A LIFT IS A VEHICLE, NOT A STAIRCASE ------------------------------
    # Grey's shaft has 105 decks. Riding it end to end must cost ONE wait.
    grey = sorted((d for d in decks if d["sector"] == "grey"),
                  key=lambda d: -d["floor_r_m"])
    car0 = "lift:grey.0.0"
    carN = f"lift:grey.0.{len(grey) - 1}"
    if car0 in G.nodes and carN in G.nodes:
        span = grey[0]["floor_r_m"] - grey[-1]["floor_r_m"]
        ride = G.path(car0, carN, metric="time")
        pure = lift_ride_s(schema, span)
        check(ride is not None and abs(ride["time_s"] - pure) < 1.0,
              f"riding Grey's whole {span:.0f} m shaft costs its ride time "
              f"and nothing else -- {pure:.0f} s over {len(grey)} decks",
              f"{ride['time_s'] if ride else None:.1f} s in "
              f"{ride['hops'] if ride else 0} hops")
        # And the door-to-door version pays exactly one wait plus one dwell.
        door = G.path(grey[0]["id"] and f"cell:{grey[0]['id']}.c0", carN,
                      metric="time")
        wait1 = _headway_wait(_shaft_headway_s(schema, span))
        # BREAK: the pre-fix model charged a wait and a dwell at every deck.
        staircase = (len(grey) - 1) * (wait1 + TRANSIT_DWELL_S) + pure
        check(ride is not None and ride["time_s"] < staircase / 10.0,
              "BREAK: charging a fresh wait and dwell at every deck -- which "
              f"is what this graph did until now -- costs {staircase / 60:.1f} "
              f"min for the same shaft, {staircase / max(1e-9, pure):.0f}x the "
              "ride", f"express {pure / 60:.1f} min")
        check(door is not None
              and abs(door["time_s"] - (pure + (wait1 + TRANSIT_DWELL_S) / 2))
              < 1.0 + grey[0]["cell_length_m"],
              "and boarding at a deck adds half a wait and half a dwell, so a "
              "round trip pays one of each", f"{door['time_s']:.1f} s")

    # -- pathing: the three reasons a route is not the shortest ------------
    # 1. transit beats walking over distance, and loses over a short hop.
    gt = sorted(n for n in G.nodes if n.startswith("gtram:0."))
    if len(gt) >= 4:
        far = G.path(gt[0], gt[len(gt) // 2])
        check(far is not None and GROUND_TRAM in far["kinds"],
              "a long way round the drum takes the ring tram",
              str(far["kinds"]) if far else "no path")
        # Walking the same span: force it by comparing against the pure walk.
        ga = G.nodes[gt[0]].meta["ground"]
        gb = G.nodes[gt[len(gt) // 2]].meta["ground"]
        walkonly = G.path(ga, gb)
        check(far is not None and walkonly is not None
              and far["time_s"] < walkonly["time_s"] * 1.05,
              "and it is not slower than walking it",
              f"tram {far['time_s']:.0f}s vs walk {walkonly['time_s']:.0f}s")
    else:
        check(False, "ground tram stops exist", str(len(gt)))

    # 2. the two metrics disagree. Find a pair where they do.
    disagree = None
    axis_nodes = sorted(n for n in G.nodes if n.startswith("axis:"))
    grey_cells = sorted(n for n in G.nodes
                        if n.startswith("cell:grey.") and ".d0.c0" in n)
    if axis_nodes and grey_cells:
        a, b = grey_cells[0], axis_nodes[-1]
        pt = G.path(a, b, "time")
        pe = G.path(a, b, "effort")
        if pt and pe:
            if abs(pt["time_s"] - pe["time_s"]) > 1e-6 \
                    or abs(pt["effort"] - pe["effort"]) > 1e-6:
                disagree = (a, b, pt, pe)
    if disagree is None:
        # Fall back to a scan, deterministically ordered.
        cand = sorted(n for n in G.nodes if n.startswith("place:"))
        for i in range(len(cand)):
            for j in range(i + 1, min(i + 5, len(cand))):
                pt = G.path(cand[i], cand[j], "time")
                pe = G.path(cand[i], cand[j], "effort")
                if pt and pe and (abs(pt["effort"] - pe["effort"]) > 1e-6):
                    disagree = (cand[i], cand[j], pt, pe)
                    break
            if disagree:
                break
    check(disagree is not None,
          "somewhere on this station the fastest route and the least-tiring "
          "route are different routes -- which is the whole reason the cost "
          "model carries two metrics")
    if disagree:
        a, b, pt, pe = disagree
        check(pe["effort"] <= pt["effort"] + 1e-9,
              "the effort-optimal route is not more tiring than the "
              "time-optimal one", f"{pe['effort']:.1f} vs {pt['effort']:.1f}")
        check(pt["time_s"] <= pe["time_s"] + 1e-9,
              "and the time-optimal route is not slower than the "
              "effort-optimal one", f"{pt['time_s']:.1f} vs {pe['time_s']:.1f}")

    # 3. gravity actually changes the answer: same distance, different sector.
    t_grey = walk_time_s(1000.0, 0.0, it.gravity_at(schema, 471.2))
    t_yel = walk_time_s(1000.0, 0.0, it.gravity_at(schema, 155.4))
    check(t_yel > t_grey * 1.4,
          "a kilometre in Yellow takes over 40% longer than a kilometre in "
          "Grey, at the same distance", f"{t_yel:.0f}s vs {t_grey:.0f}s")

    # -- determinism ------------------------------------------------------
    check(abs(_u("nav/place", "zocalo") - _u("nav/place", "zocalo")) < 1e-18,
          "the place hash is stable within a process")
    check(_u("nav/place", "zocalo") != _u("nav/place", "casino"),
          "and distinguishes places")
    p1 = G.path(a0, a1)
    p2 = G.path(a0, a1)
    check([l.a for l in p1["links"]] == [l.a for l in p2["links"]],
          "the same query returns the same route")
    # Determinism across processes, not merely within one. A subprocess with
    # a different PYTHONHASHSEED rebuilds the whole graph and must produce the
    # same 128-bit digest; `str.__hash__` anywhere in the chain breaks this
    # and nothing else would notice.
    try:
        import subprocess                                     # noqa: PLC0415
        env = dict(os.environ, PYTHONHASHSEED="4242")
        got = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--digest"],
            capture_output=True, text=True, env=env, timeout=900)
        mine = digest(G)
        check(got.stdout.strip() == mine,
              "the graph is byte-identical in a subprocess under "
              "PYTHONHASHSEED=4242",
              f"{got.stdout.strip()!r} vs {mine!r} {got.stderr[-200:]}")
    except Exception as exc:                                  # noqa: BLE001
        check(False, "cross-process determinism check", repr(exc))

    # Scanned as TOKENS, not as text. The text scan this replaced failed on
    # its own docstring, because the docstring explains why `random` and
    # `str.__hash__` are banned -- an assertion that cannot distinguish a
    # violation from a warning about the violation is worse than none.
    banned, code_names = _banned_names()
    check(not banned,
          "no `random` and no salted str hashing in executable code",
          str(sorted(banned)))
    check("blake2b" in code_names,
          "and blake2b IS used -- the scan reads executable tokens, so it "
          "would have found a violation the same way it found this")

    # -- winding on the debug mesh ----------------------------------------
    v, t, _g = ground_nav_mesh(schema, profile)
    frac = it._inward_fraction(v, t)
    check(frac > 0.999,
          "the nav sheet faces the spin axis -- seen from inside the drum, "
          "which is the convention four subsystems here have shipped backwards",
          f"{frac:.4f}")
    flipped = [(a, c, b) for a, b, c in t]
    check(it._inward_fraction(v, flipped) < 0.001,
          "and the measurement can tell: reversing the winding scores ~0")

    # -- budget -----------------------------------------------------------
    lines = []
    ok = budget_report(G, out=lines.append)
    check(ok, "navigation is inside its memory and CPU budget",
          "\n".join(lines))
    check(G.memory_bytes() / 1e6 < PLAN_BUDGET["fine_graph_mb"],
          "the fine graph fits in its stated megabytes",
          f"{G.memory_bytes()/1e6:.2f} MB")
    coarse = coarse_graph(G)
    check(coarse["nodes"] < len(G.nodes) / 20,
          "the coarse graph agents plan on is at least 20x smaller than the "
          "fine one", f"{coarse['nodes']} vs {len(G.nodes)}")

    # ===================================================================
    # BREAK TESTS. Every assertion above that could be vacuous is broken
    # here on purpose and observed to fail. STATE.md records two assertions
    # in this repository that could not fail; this section is the answer.
    # ===================================================================
    print("\n  -- deliberate breakage --")

    # (a) remove the wrap from a ring: the ring becomes an arc.
    class _NoWrap(NavGraph):
        pass
    Gw = _NoWrap()
    dd = d
    for ci in range(dd["cells"]):
        Gw.add_node(NavNode(f"c{ci}", "cell", (0.0, 0.0, 0.0), 1.0))
    for ci in range(dd["cells"] - 1):          # range(n), no modulo -- the bug
        Gw.add_walk(f"c{ci}", f"c{ci+1}", dd["cell_length_m"], 0.0, 1.0)
    pb = Gw.path("c0", f"c{dd['cells']-1}")
    check(pb is not None and pb["hops"] == dd["cells"] - 1,
          "BREAK: dropping the modulo makes the ring an arc and the same "
          f"journey {dd['cells']-1} hops instead of 1",
          f"hops={pb['hops'] if pb else None}")

    # (b), (c) THE ONE THAT MATTERS. The lake is a 175 m band running the
    # drum's entire 2,586 m length -- on a flat map it would cut the world in
    # half. It does not cut the drum, and the reason is the cylinder: a strip
    # removed from a closed surface leaves a connected sheet, because you can
    # always walk round the far side. That is the wrap doing real work rather
    # than being decorative, so it is proved three ways: flood the band with
    # the wrap in place, flood it with the wrap removed, and add a second
    # barrier. Only the last two disconnect anything.
    gn3 = ground_nav(schema, profile, drum)
    bands = dg._bands()
    wlo, whi = [(a, b) for a, b, nm, _r in bands if nm == "water"][0]

    def _ground_only(mask, wrap=True):
        Gx = NavGraph()
        for ia in range(gn3.na):
            for iz in range(gn3.nz):
                if mask[ia][iz]:
                    Gx.add_node(NavNode(f"g:{ia}.{iz}", "ground",
                                        gn3.xyz(ia, iz), 1.0))
        for ia in range(gn3.na):
            for iz in range(gn3.nz):
                if not mask[ia][iz]:
                    continue
                ja = ia + 1
                if ja < gn3.na or wrap:
                    ja %= gn3.na
                    if mask[ja][iz]:
                        Gx.add_walk(f"g:{ia}.{iz}", f"g:{ja}.{iz}",
                                    gn3.spacing_a_m, 0.0, 1.0)
                if iz + 1 < gn3.nz and mask[ia][iz + 1]:
                    Gx.add_walk(f"g:{ia}.{iz}", f"g:{ia}.{iz+1}",
                                gn3.spacing_z_m, 0.0, 1.0)
        return Gx

    flooded_mask = [row[:] for row in gn3.walkable]
    flooded = 0
    for ia in range(gn3.na):
        if wlo <= ia / gn3.na < whi:
            for iz in range(gn3.nz):
                flooded += 1 if flooded_mask[ia][iz] else 0
                flooded_mask[ia][iz] = False
    c_wrap = _ground_only(flooded_mask, wrap=True).islands()
    check(len(c_wrap) == 1,
          "BREAK: flooding the ENTIRE water band, ends and all, still leaves "
          "one island -- a strip removed from a cylinder cuts nothing, and "
          "you walk round the far side", f"islands={len(c_wrap)}, "
          f"{flooded} cells flooded")
    c_nowrap = _ground_only(flooded_mask, wrap=False).islands()
    check(len(c_nowrap) == 2,
          "BREAK: flood the same band and DROP THE WRAP and the drum falls "
          "into two pieces -- so the cylinder topology is what makes the lake "
          "passable, not luck", f"islands={len(c_nowrap)}")
    two_mask = [row[:] for row in flooded_mask]
    for ia in range(gn3.na):
        if 0.90 <= ia / gn3.na < 0.95:
            for iz in range(gn3.nz):
                two_mask[ia][iz] = False
    c_two = _ground_only(two_mask, wrap=True).islands()
    check(len(c_two) == 2,
          "BREAK: a SECOND full-length barrier does split the drum even with "
          "the wrap, and island_report finds both halves",
          f"islands={len(c_two)}")
    check(_ground_only(gn3.walkable, wrap=True).islands()[0][0]
          > 0.99 * sum(1 for a in range(gn3.na) for z in range(gn3.nz)
                       if gn3.walkable[a][z]),
          "and the UNBROKEN ground is one piece, so the three results above "
          "are about the barriers rather than about the fixture")

    # (d) slacken the slope limit until the lake bed becomes walkable -- proves
    #     the kind test and the slope test are doing different work.
    steep = nav_from_mesh(*_flat_test_mesh(), (0.0, 1.0, 0.0), slope_deg=5.0)
    lax = nav_from_mesh(*_flat_test_mesh(), (0.0, 1.0, 0.0), slope_deg=60.0)
    check(nav_area_m2(steep) < nav_area_m2(lax),
          "BREAK: tightening the slope criterion removes floor from a ramped "
          "test mesh -- the criterion is applied, not carried",
          f"{nav_area_m2(steep):.2f} vs {nav_area_m2(lax):.2f}")

    # (e) step limit below the door sill disconnects a room from its corridor.
    sill = _two_level_polys()
    severed = nav_regions(sill, cell=0.25, step_m=STEP_M / 2.0)
    joined = nav_regions(sill, cell=0.25, step_m=STEP_M * 1.5)
    check(len(severed) == 2 and len(joined) == 1,
          "BREAK: a step limit under the 0.10 m door sill severs the floor "
          "across the sill; a limit over it joins them. STEP_M sits between, "
          "which is why it is the sill and not a round number",
          f"{len(severed)} regions under, {len(joined)} over")
    check(len(nav_regions(sill, cell=0.25)) == 1,
          "and at the SHIPPED step limit the two floors are one region -- so "
          "every door in the station is passable")

    # (f2) a decal laid on a deck must not count as a second floor.
    deck_only = [NavPoly(((0, 0, 0), (4, 0, 0), (4, 0, 4)), (0, 1, 0), 0.0,
                         9.0, 8.0, (2.66, 0.0, 1.33), True),
                 NavPoly(((0, 0, 0), (4, 0, 4), (0, 0, 4)), (0, 1, 0), 0.0,
                         9.0, 8.0, (1.33, 0.0, 2.66), True)]
    decal = list(deck_only) + [
        NavPoly(((0, 0.02, 0), (4, 0.02, 0), (4, 0.02, 4)), (0, 1, 0), 0.0,
                9.0, 8.0, (2.66, 0.02, 1.33), True),
        NavPoly(((0, 0.02, 0), (4, 0.02, 4), (0, 0.02, 4)), (0, 1, 0), 0.0,
                9.0, 8.0, (1.33, 0.02, 2.66), True)]
    check(abs(nav_area_m2(decal) - 2 * nav_area_m2(deck_only)) < 1e-9,
          "BREAK-CHECK: summing triangle areas counts a decal laid 2 cm above "
          "a deck as a SECOND deck -- exactly twice the floor")
    check(abs(nav_plan_area_m2(decal, cell=0.25)
              - nav_plan_area_m2(deck_only, cell=0.25)) < 1e-9,
          "and projecting them counts it once, which is why room areas are "
          "reported from the projection and not from the sum")

    # (f) an inverted headroom criterion deletes the whole navmesh.
    none_ = nav_from_mesh(*_flat_test_mesh(), (0.0, 1.0, 0.0),
                          headroom_m=1e6)
    check(nav_area_m2(none_) == 0.0,
          "BREAK: an impossible headroom criterion leaves zero walkable area, "
          "so the headroom test is reached on every polygon")

    # (f3) a wall standing on a deck must carve the deck.
    try:
        import command_control as _ccm                       # noqa: PLC0415
        _v, _t, _g3 = _ccm.command_control()
        pl = nav_from_mesh(_v, _t, (0.0, 1.0, 0.0))
        with_walls = nav_plan_area_m2(
            pl, obstacles=nav_obstacles(_v, _t, (0.0, 1.0, 0.0)))
        without = nav_plan_area_m2(pl)
        check(with_walls < without,
              "BREAK: dropping obstacle carving leaves the deck under every "
              "wall, console and rail walkable -- C&C grows when the walls "
              "stop counting",
              f"{with_walls:.1f} m2 carved vs {without:.1f} m2 uncarved")
    except Exception as exc:                                 # noqa: BLE001
        check(False, "obstacle carving check", repr(exc))

    # (g) the effort metric must actually differ from the time metric.
    Ge = NavGraph()
    Ge.add_node(NavNode("A", "cell", (0, 0, 0), 1.0))
    Ge.add_node(NavNode("H", "cell", (0, 0, 0), 1.7))
    Ge.add_node(NavNode("L", "cell", (0, 0, 0), 0.6))
    Ge.add_node(NavNode("B", "cell", (0, 0, 0), 1.0))
    Ge.add_walk("A", "H", 500.0, 0.0, 1.7)
    Ge.add_walk("H", "B", 500.0, 0.0, 1.7)
    Ge.add_walk("A", "L", 560.0, 0.0, 0.6)
    Ge.add_walk("L", "B", 560.0, 0.0, 0.6)
    pt = Ge.path("A", "B", "time")
    pe = Ge.path("A", "B", "effort")
    check(pt["links"][0].b == "H" and pe["links"][0].b == "L",
          "BREAK-CHECK: on a two-route toy the fastest way is through the "
          "heavy sector and the least tiring way is through the light one -- "
          "the two metrics are not the same function",
          f"time via {pt['links'][0].b}, effort via {pe['links'][0].b}")

    print(f"\n{_passed}/{_passed + _failed} passed")
    return 1 if _failed else 0


def _banned_names(path=None):
    """Names used in EXECUTABLE code, and which of them are forbidden.

    `tokenize` drops comments and string literals, so prose about a banned
    construct is not a use of it. Returns (violations, all_names).
    """
    import tokenize                                          # noqa: PLC0415
    path = os.path.abspath(__file__) if path is None else path
    names, prev = set(), ""
    with tokenize.open(path) as f:
        for tok in tokenize.generate_tokens(f.readline):
            if tok.type == tokenize.NAME:
                names.add(tok.string)
                if prev == ".":
                    names.add("." + tok.string)
                prev = tok.string
            elif tok.type == tokenize.OP:
                prev = tok.string
            elif tok.type not in (tokenize.COMMENT, tokenize.NL,
                                  tokenize.NEWLINE, tokenize.INDENT,
                                  tokenize.DEDENT):
                prev = ""
    forbidden = {"random", "randint", "shuffle", "__hash__", ".__hash__",
                 "getrandbits", "uniform"}
    return (names & forbidden), names


def _flat_test_mesh():
    """A ramp rising 1 m over 2 m (26.6 deg) beside a flat plate, under a lid.

    A fixture, not station geometry: the break tests need a surface whose
    slope and headroom are known exactly so that a criterion change has a
    predictable effect. Using real station geometry here would make the break
    test depend on the thing it is trying to isolate.
    """
    v = [(0, 0, 0), (2, 0, 0), (2, 0, 2), (0, 0, 2),          # flat plate
         (2, 0, 0), (4, 1, 0), (4, 1, 2), (2, 0, 2),          # 26.6 deg ramp
         (0, 3, 0), (4, 3, 0), (4, 3, 2), (0, 3, 2)]          # lid at y=3
    t = [(0, 2, 1), (0, 3, 2), (4, 6, 5), (4, 7, 6), (8, 9, 10), (8, 10, 11)]
    return v, t


def _two_level_polys():
    """Two floor plates sharing an edge, 0.10 m apart in height -- a door sill.

    Exactly the geometry STEP_M exists to admit, so a step limit below the
    sill must sever them and a limit above must join them.
    """
    a = NavPoly(((0, 0, 0), (1, 0, 0), (1, 0, 1)), (0, 1, 0), 0.0, 9.0, 0.5,
                (0.66, 0, 0.33), True)
    b = NavPoly(((0, 0, 0), (1, 0, 1), (0, 0, 1)), (0, 1, 0), 0.0, 9.0, 0.5,
                (0.33, 0, 0.66), True)
    c = NavPoly(((1, 0.10, 0), (2, 0.10, 0), (1, 0.10, 1)), (0, 1, 0), 0.0,
                9.0, 0.5, (1.33, 0.10, 0.33), True)
    return [a, b, c]


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
        sys.exit(0)
    if "--digest" in sys.argv:
        print(digest())
        sys.exit(0)
    if "--obj" in sys.argv:
        i = sys.argv.index("--obj")
        print(write_obj(sys.argv[i + 1]))
        sys.exit(0)
    sys.exit(_selftest())
