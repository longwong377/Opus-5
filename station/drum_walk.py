#!/usr/bin/env python3
"""A walkable surface for the habitat drum -- the one place on this station a
body could not stand.

WHAT THIS ENDS. `station/deck.py --sweep` reports 66 of 66 ring decks assembling
and a body walking them, and defers exactly one ring by name:
`NOT_RING_DECKS[("green", 1)]`, the drum. Twelve gazetteer locations live on it
-- the Garden, the townscape, the terrace, the zen garden, the lake, Earhart's,
Fresh Air, both trams, the spokes, the end caps, the radial tubes -- and the
assembler is the wrong tool for every one of them, because the drum is not a
corridor with rooms off it. It is an open barrel 2,588 m long whose floor is
`drum_ground.py`'s heightfield, and nothing in this project had ever given that
heightfield a collider.

THE COLLISION LESSON SURVIVES, AND IT INVERTS. `station/collision.py` exists
because the corridor's render deck carries a 66 mm lighting channel and 22 mm
proud tiles, and a capsule dropped on that stands still forever while reporting
`on_floor=true`. Its fix was a SMOOTH shell: throw the millimetres away, because
on a corridor they are decoration and a player walks on a flat deck.

**On the drum a smooth shell would be the bug.** The relief here is the content:
a settlement podium stands 7 m over a lake bed 4 m down, and a shell that
flattened them would leave a player hovering over the fields and buried in the
town -- the same class of error that put session 2u's first drum camera five
metres underground. So the rule "a player walks on a surface built for walking
on" is kept and what has to be true of that surface changes:

  corridor:  the collision floor must be FLAT where the render mesh is not
  drum:      the collision ground must be the SAME SHAPE the render ground is,
             cheaper, and free of anything a capsule can catch on

HOW IT CANNOT DRIFT. This module authors no terrain. It calls
`drum_ground.ground_patch`, which is the function the RENDER ground is built
from, on the same lattice, at a stride this module derives by measurement. Not
"measured off the kit by ray casting" as the corridor profile is, but one step
stronger: the same source function, so there is nothing to drift. Hard rule 4.

THE GATE IS SLOPE, NOT LIP, and that is the substantive difference from
`collision.floor_steps`. On a corridor deck the largest step between two
neighbouring samples is exactly the right measure, because the deck is flat by
design and any lip is a defect. Run that measure over terrain and a perfectly
good hill fails it: the drum's ground rises 0.24 m between adjacent lattice
points in places and that is a 3.5 degree slope, which is a field. What a
character controller actually tests is RISE OVER RUN against its own
`floor_max_angle`, so that is what is measured here -- per emitted triangle,
against the local radial, on the mesh rather than on whatever produced it.

WHAT IS MEASURED, over the whole 448 x 640 lattice (`--terrain`):

    steepest slope anywhere on the drum   16.61 deg   (a lake shore)
    steepest along the axis               10.90 deg   (a cap ring road)
    lattice points above 17 deg           0 of 287,168
    height range                          -3.90 .. +8.90 m about the datum

so the ground is walkable in principle at Godot's 45 degree floor angle with a
factor of 2.7 in hand, and the risk was never a cliff -- it was that nothing
sampled it.

WHAT THIS COSTS, stated because it is large. The tile a body needs to walk for
thirty seconds is 5 x 5 ground patches, 51,200 triangles, against 74,044 for the
entire rest of the walkable station. That is not waste: a ring deck is a 2.6 m
tube and the drum is 4.5 million m2 of open country, and the tile is still 8.9%
of the drum's own lod0 ground. It is a streaming unit, not a level.

Run: python3 station/drum_walk.py --selftest
     python3 station/drum_walk.py --terrain          # the slope survey
     python3 station/drum_walk.py --at the_garden --obj OUT.obj
     python3 station/drum_walk.py --at the_garden --walk    # needs Godot
"""
import argparse
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import collision as C                                           # noqa: E402
import directory as dr                                          # noqa: E402
import drum_ground as dg                                        # noqa: E402
import interior as it                                           # noqa: E402
import rooms as R                                               # noqa: E402

# The steepest surface a Godot CharacterBody3D will treat as floor rather than
# wall. This is `CharacterBody3D.floor_max_angle`'s default of 0.785398 rad --
# an ENGINE fact, not a choice made here, and it is the number the walk test's
# `is_on_floor()` is actually deciding against. Written as degrees because that
# is how the survey reads.
FLOOR_MAX_DEG = 45.0

# How far the collision ground may sit from the ground a player can see, in
# metres. NOT a new constant: `rooms.TRIM_MAX_PROUD_M` is this project's own
# definition of a step -- "a step you do not trip on" -- and a disagreement
# between what the eye sees and what the foot rests on is exactly a step, either
# hovering over the field or shin-deep in it. Taken from there rather than
# restated, so there is one definition of a step on this station.
STEP_M = R.TRIM_MAX_PROUD_M

# Where a body's feet start, above the ground. Same 50 mm `collision.stand_at`
# uses, and for the same reason: a spawn is a claim that a person can stand at a
# place, and a claim that needs a metre of falling to resolve is being hoped
# for rather than checked.
SPAWN_ABOVE_M = 0.05


def drum(schema=None, profile=None):
    """The drum sector, its schema and its profile -- bound by GEOMETRY.

    `interior.drum_sector` identifies the drum by its radius rather than by the
    name "green", which is why the naming conflicts C-003/C-004 do not block any
    of this: they decide which label attaches to a volume, not what shape it is.
    """
    if schema is None:
        schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    return schema, profile, sector


# ---------------------------------------------------------------------------
# The stride, which is derived rather than chosen
# ---------------------------------------------------------------------------

_STRIDE = {}


def collision_stride(tol_m=STEP_M):
    """The coarsest LOD stride whose measured error stays under a step.

    DERIVED, and it is the only number in this module that decides what the
    collision ground costs. `drum_ground.lod_error_report` already measures, per
    stride, how far a decimated lattice departs from the true field -- over
    whole patches at full resolution, one per land-use band, so a terrace riser
    is sampled rather than stepped over. That measurement answers a rendering
    question ("when may this level be drawn") and it answers this one unchanged:
    a collision surface that is 0.19 m off the ground the player sees is a
    player standing 0.19 m into a field.

    On the current terrain the answer is **stride 1**, and that is not a
    formality -- stride 2 measures 0.193 m against a 0.100 m step and stride 4
    measures 0.538 m. The whole drum at stride 1 is 573,440 triangles, which is
    why this is a tile and not a level.
    """
    key = round(tol_m, 6)
    if key in _STRIDE:
        return _STRIDE[key]
    rows = dg.lod_error_report()
    best = dg.STRIDES[0]
    for row in rows:
        if row["error_m"] <= tol_m:
            best = max(best, row["stride"])
    _STRIDE[key] = (best, rows)
    return _STRIDE[key]


def stride_report(tol_m=STEP_M):
    """(stride, [rows]) -- the derivation above, for printing and asserting."""
    return collision_stride(tol_m)


# ---------------------------------------------------------------------------
# Where a place is, on the ground's own patch grid
# ---------------------------------------------------------------------------

def patch_of(angle_deg, z_m):
    """The ground patch containing a point. The drum's `deck_index`.

    Collision uses `drum_ground`'s OWN patch grid rather than a grid of its own,
    so the cell that streams the ground a player can see is the cell that
    streams the ground they stand on. Two streaming grids over one surface is
    two descriptions of one thing, which is the defect this project has now been
    bitten by three times.
    """
    u = (angle_deg / 360.0) % 1.0
    w = min(max((z_m - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0 - 1e-12)
    pa = int(u * dg.CELLS_A) // dg.PATCH_A % dg.PATCHES_A
    pz = min(int(w * dg.CELLS_Z) // dg.PATCH_Z, dg.PATCHES_Z - 1)
    return pa, pz


def patch_span_m():
    """(circumferential, axial) size of one ground patch, in metres."""
    return (2.0 * math.pi * dg.FLOOR_R * dg.PATCH_A / dg.CELLS_A,
            (dg.Z1 - dg.Z0) * dg.PATCH_Z / dg.CELLS_Z)


def rings_for(walk_m):
    """How many patch rings around the centre a walk of `walk_m` needs.

    DERIVED FROM THE GATE THAT WILL RUN. `walkable.TRAVERSE_FRAMES` is 1800
    physics frames -- thirty seconds -- and `player.gd` walks at 4.2 m/s, so the
    gate asks a body to cover 126 m in a straight line from the spawn. A tile
    whose nearest edge is closer than that fails the walk for being too small,
    which would be this module marking its own homework: the body would stop at
    a cliff of its own making and the trace would look exactly like terrain.

    A spawn can sit anywhere in its own patch, so the worst case is the spawn on
    a patch corner and `rings` whole patches to the nearest edge.
    """
    a_m, z_m = patch_span_m()
    return max(1, int(math.ceil(walk_m / min(a_m, z_m))))


def walk_distance_m():
    """How far the walk gate will ask a body to go, in metres.

    READ OFF THE GATE, not restated: `walkable.TRAVERSE_FRAMES` is the number of
    physics frames the traverse runs for and 4.2 m/s is `player.gd`'s walking
    speed. A tile sized against a copy of those numbers would stop being big
    enough the moment either moved, and the failure would look like terrain.
    """
    import walkable as W                                        # noqa: PLC0415
    return W.TRAVERSE_FRAMES / 60.0 * 4.2


# ---------------------------------------------------------------------------
# The collision ground
# ---------------------------------------------------------------------------

def _spans(names):
    """[name per triangle] -> [(name, lo, hi)]. `drum_ground` returns one group
    name per triangle and `collision.write_obj` wants runs; converting here
    keeps both conventions intact instead of changing either."""
    out, cur, start = [], None, 0
    for i, n in enumerate(names):
        if n != cur:
            if cur is not None:
                out.append((cur, start, i))
            cur, start = n, i
    if cur is not None:
        out.append((cur, start, len(names)))
    return out


def ground_shell(pa, pz, rings=None, stride=None, walk_m=None):
    """The collision ground around one patch. Returns (verts, tris, groups, meta).

    UNIFORM STRIDE, DELIBERATELY. `drum_ground.ground_patch` takes a
    `neighbours` map and clamps its border vertices onto a coarser neighbour's
    edge, because the render ground mixes levels and a T-junction between a
    32-cell edge and a 4-cell edge is a sawtooth of holes. Collision does not
    mix levels -- every tile is at `collision_stride()` -- so every shared edge
    vertex is computed from the same `_vertex(ia, iz)` call on both sides and
    the seam is exact rather than repaired. That is asserted, not assumed: a
    heightfield with holes in it is a heightfield you fall through, and under
    spin gravity you then accelerate outward for thirty kilometres.

    The circumference WRAPS and the axis does not. `pa` is taken modulo
    `PATCHES_A`, so a tile centred at 350 degrees genuinely contains 10 degrees;
    `pz` is clamped, because past the end cap there is no ground to build.
    """
    stride = stride or collision_stride()[0]
    if rings is None:
        rings = rings_for(walk_m if walk_m is not None else walk_distance_m())
    verts, tris, names = [], [], []
    used = []
    for dz in range(-rings, rings + 1):
        qz = pz + dz
        if not (0 <= qz < dg.PATCHES_Z):
            continue
        for da in range(-rings, rings + 1):
            qa = (pa + da) % dg.PATCHES_A
            v, t, g, _m = dg.ground_patch(qa, qz, stride)
            off = len(verts)
            verts.extend(v)
            tris.extend((a + off, b + off, c + off) for a, b, c in t)
            names.extend(g)
            used.append((qa, qz))

    a_m, z_m = patch_span_m()
    meta = {
        "sector": "drum", "centre_patch": (pa, pz), "patches": used,
        "rings": rings, "stride": stride,
        "floor_r_m": dg.FLOOR_R,
        "triangles": len(tris), "vertices": len(verts),
        "patch_m": (round(a_m, 2), round(z_m, 2)),
        "edge_m": round(rings * min(a_m, z_m), 1),
        "z_range": (round(dg.Z0 + (pz - rings) * z_m, 1),
                    round(dg.Z0 + (pz + rings + 1) * z_m, 1)),
        "open_axial_edge": (pz - rings < 0 or pz + rings >= dg.PATCHES_Z),
    }
    return verts, tris, _spans(names), meta


def render_ground(meta):
    """The ground a player SEES over the same patches, at the LOD that ships.

    `drum_ground.visible_set` assigns every patch a level from its distance to
    the eye and builds only the ones asked for, so this is the actual render
    mesh for this tile rather than a stand-in for it. It is what the collision
    surface is compared against, and comparing against a freshly-built lod0
    instead would be comparing the shell with itself.
    """
    eye = stand_at_patch(meta)
    v, t, g, m = dg.visible_set(eye, patches=meta["patches"])
    return v, t, _spans(g), m


def stand_at_patch(meta, above_m=SPAWN_ABOVE_M):
    """Feet position at the centre of a tile."""
    pa, pz = meta["centre_patch"]
    u = (pa * dg.PATCH_A + dg.PATCH_A / 2.0) / dg.CELLS_A
    w = (pz * dg.PATCH_Z + dg.PATCH_Z / 2.0) / dg.CELLS_Z
    return stand_at(u * 360.0, dg.Z0 + w * (dg.Z1 - dg.Z0), above_m)


def stand_at(angle_deg, z_m, above_m=SPAWN_ABOVE_M, surface=None):
    """Where to put a body's FEET so it starts on the drum ground.

    Not `drum_ground.stand_on_ground`, which returns an EYE at 1.7 m: `walk.gd`
    parents a 1.8 m capsule at (0, 0.9, 0) on the body, so the body's origin is
    at the soles. Handing it an eye position spawns a person 1.7 m into the air
    -- a drop the walk gate correctly calls a floor that is not where the shell
    says it is.

    `surface` IS THE MESH THE BODY WILL ACTUALLY STAND ON, and passing it is the
    difference between a spawn that is right and one that is nearly right. The
    terrain FUNCTION and the emitted MESH are not the same surface between
    lattice points: a facet is a chord and the field is a curve, so at the
    Garden's own angle the field says r = 276.2441 and the triangle a foot rests
    on is at 276.2049 -- 39 mm apart, four times the curvature sagitta, because
    the heightfield bends inside a cell as well. Spawning off the function puts
    a body up to that far into or over its own floor, and on the wrong side of
    it the body starts embedded. Cast, as a foot does.

    UP IS INWARD, so standing 50 mm clear of the ground is 50 mm of SMALLER
    radius. This station spins.
    """
    a = math.radians(angle_deg)
    r = None
    if surface is not None:
        r = _Caster(*surface[:2]).radius_at(angle_deg, z_m)
    if r is None:
        u = (angle_deg / 360.0) % 1.0
        w = min(max((z_m - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
        r = dg.FLOOR_R - dg.sample(u, w)[0]
    r -= above_m
    return (r * math.cos(a), r * math.sin(a), z_m)


def gravity_m_s2(schema):
    """The drum's own spin gravity at the floor, in m/s2, from the schema.

    `interior.gravity_at` returns multiples of standard gravity and the engine
    wants m/s2. Read rather than assumed: the whole station's angular rate is
    derived from this radius being 1.000 g, and hard-coding 9.81 here would put
    a second, unlinked copy of that derivation in the physics.
    """
    return it.gravity_at(schema, dg.FLOOR_R) * 9.80665


# ---------------------------------------------------------------------------
# Measuring an emitted surface
# ---------------------------------------------------------------------------

def slope_report(verts, tris, groups=None):
    """Per-triangle slope against the local radial, in degrees.

    MEASURES THE MESH, not the function that made it -- the same property that
    lets `collision.floor_steps` be run on either the shell or the render
    corridor and give an honest answer about both. Here it means the same call
    scores this module's tile and `interior.drum_interior`'s band shell, which
    is the A/B in `_selftest`.

    A triangle's slope is the angle between its normal and the inward radial at
    its own centroid -- inward, because up is inward on a spun barrel. A
    triangle whose normal points OUTWARD is not a shallow floor, it is a floor
    facing the wrong way, and the arithmetic reports it as more than 90 degrees
    rather than folding it back into a plausible number.
    """
    per = [None] * len(tris)
    for name, lo, hi in (groups or ()):
        for i in range(lo, min(hi, len(tris))):
            per[i] = name
    worst, worst_at, over, total = 0.0, None, 0, 0
    hist = {}
    for i, (ia, ib, ic) in enumerate(tris):
        a, b, c = verts[ia], verts[ib], verts[ic]
        u = [b[k] - a[k] for k in range(3)]
        w = [c[k] - a[k] for k in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0]]
        ln = math.hypot(math.hypot(n[0], n[1]), n[2])
        if ln < 1e-12:
            continue
        mid = [(a[k] + b[k] + c[k]) / 3.0 for k in range(3)]
        rr = math.hypot(mid[0], mid[1]) or 1.0
        up = (-mid[0] / rr, -mid[1] / rr, 0.0)
        cos = sum(n[k] * up[k] for k in range(3)) / ln
        deg = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        total += 1
        hist[int(deg // 5) * 5] = hist.get(int(deg // 5) * 5, 0) + 1
        if deg > FLOOR_MAX_DEG:
            over += 1
        if deg > worst:
            worst, worst_at = deg, (per[i], tuple(round(x, 1) for x in mid))
    return {"max_deg": round(worst, 3), "at": worst_at,
            "over_floor_angle": over, "triangles": total,
            "histogram": dict(sorted(hist.items()))}


class _Caster:
    """Radial ray casts against a mesh, indexed by angle.

    Reuses `collision._down_index` and `collision._ray_tri` rather than growing
    a second intersector: a ring deck and a drum ask the same question -- what
    is under a body at this angle and this z -- and the answer must not depend
    on which module asked.
    """

    def __init__(self, verts, tris):
        self.v, self.t = verts, tris
        self.bins, self.nbin = C._down_index(verts, tris)

    def radius_at(self, angle_deg, z, from_r=None):
        """Radius of the first surface OUTWARD of the axis at (angle, z), or
        None. Cast from above the highest terrain, downhill -- which on a spun
        barrel means from a small radius toward a large one."""
        a = math.radians(angle_deg)
        top = from_r if from_r is not None else dg.FLOOR_R - 40.0
        b = int((math.atan2(math.sin(a), math.cos(a)) + math.pi)
                / (2 * math.pi) * self.nbin) % self.nbin
        o = (top * math.cos(a), top * math.sin(a), z)
        d = (math.cos(a), math.sin(a), 0.0)
        best = None
        for z0, z1, tri in self.bins.get(b, ()):
            if z < z0 - 1e-6 or z > z1 + 1e-6:
                continue
            h = C._ray_tri(o, d, self.v[tri[0]], self.v[tri[1]], self.v[tri[2]])
            if h is not None and (best is None or h < best):
                best = h
        return None if best is None else top + best


def _tile_samples(meta, n_a=40, n_z=40, inset=0.5):
    """(angle_deg, z) points spread over a tile, one cell in from its edges.

    `inset` keeps the samples off the outermost lattice line: a ray cast exactly
    on a mesh boundary can miss by a float and be reported as a hole, which
    would make the hole gate fail for arithmetic rather than for geometry.
    """
    pa, pz = meta["centre_patch"]
    rings = meta["rings"]
    ia0 = (pa - rings) * dg.PATCH_A
    ia1 = (pa + rings + 1) * dg.PATCH_A
    iz0 = max(0, (pz - rings) * dg.PATCH_Z)
    iz1 = min(dg.CELLS_Z, (pz + rings + 1) * dg.PATCH_Z)
    out = []
    for i in range(n_a):
        ia = ia0 + inset + (ia1 - ia0 - 2 * inset) * i / max(1, n_a - 1)
        for j in range(n_z):
            iz = iz0 + inset + (iz1 - iz0 - 2 * inset) * j / max(1, n_z - 1)
            out.append(((ia / dg.CELLS_A) * 360.0,
                        dg.Z0 + (iz / dg.CELLS_Z) * (dg.Z1 - dg.Z0)))
    return out


def holes(verts, tris, meta, **kw):
    """Points inside the tile with no ground under them. The drum's
    `collision.floor_holes`.

    A hole in a corridor deck is a fall of 1.5 m into the sub-floor. A hole in
    the drum ground is a fall out of a habitat at 1 g with 278 m of radius
    under it and nothing to stop at, so it is the more expensive of the two to
    ship and the easier to miss -- there is no wall nearby to make it obvious.
    """
    cast = _Caster(verts, tris)
    out = []
    for ang, z in _tile_samples(meta, **kw):
        if cast.radius_at(ang, z) is None:
            out.append((round(ang, 3), round(z, 1)))
    return out


def deviation(verts, tris, meta, other=None, **kw):
    """How far the collision ground sits from the ground it stands in for.

    With `other`, compares against that mesh -- the LOD-resolved render tile,
    which is the comparison that matters and the one that can fail. Without it,
    compares against `drum_ground.sample` directly, which checks the mesh
    against the field rather than one mesh against another.

    Returns metres, signed toward the axis: POSITIVE means the collision
    surface is INSIDE the render surface, so a player stands proud of the
    visible ground; negative means buried in it.
    """
    mine = _Caster(verts, tris)
    theirs = _Caster(*other[:2]) if other else None
    worst, worst_at, n, sq, miss = 0.0, None, 0, 0.0, 0
    for ang, z in _tile_samples(meta, **kw):
        a = mine.radius_at(ang, z)
        if a is None:
            miss += 1
            continue
        if theirs is not None:
            b = theirs.radius_at(ang, z)
            if b is None:
                miss += 1
                continue
        else:
            u = (ang / 360.0) % 1.0
            w = min(max((z - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
            b = dg.FLOOR_R - dg.sample(u, w)[0]
        d = b - a
        n += 1
        sq += d * d
        if abs(d) > abs(worst):
            worst, worst_at = d, (round(ang, 2), round(z, 1))
    return {"max_m": round(worst, 4), "at": worst_at, "samples": n,
            "rms_m": round(math.sqrt(sq / max(n, 1)), 4), "missed": miss}


def _point_segment_m(p, a, b):
    ab = [b[k] - a[k] for k in range(3)]
    ll = sum(x * x for x in ab)
    if ll < 1e-18:
        return math.dist(p, a)
    tpar = max(0.0, min(1.0, sum((p[k] - a[k]) * ab[k]
                                 for k in range(3)) / ll))
    return math.dist(p, [a[k] + ab[k] * tpar for k in range(3)])


def _patch_edge(v, stride, side):
    """One border polyline of a `ground_patch`, in its own emitted order.

    `ground_patch` fills its grid `ka`-major, `kz`-minor and appends in that
    order, so vertex (ka, kz) is at `ka * (nz + 1) + kz`. Reading it back rather
    than rebuilding it is the point: the seam test has to see the vertices that
    actually shipped.
    """
    na, nz = dg.PATCH_A // stride, dg.PATCH_Z // stride
    if side == "a+":
        return [v[na * (nz + 1) + k] for k in range(nz + 1)]
    if side == "a-":
        return [v[0 * (nz + 1) + k] for k in range(nz + 1)]
    if side == "z+":
        return [v[k * (nz + 1) + nz] for k in range(na + 1)]
    return [v[k * (nz + 1) + 0] for k in range(na + 1)]


def seam_gaps(pa, pz, stride=None, nb_stride=None):
    """The largest hole along the seam between two collision patches, in metres.

    THIS IS WHAT THE RENDER GROUND NEEDS `clamp_edge` FOR AND COLLISION MUST
    NOT. `drum_ground.ground_patch` repairs T-junctions where a fine patch meets
    a coarse one; collision is uniform, so the repair should be unnecessary and
    the seam exactly zero.

    MEASURED AS POINT-TO-EDGE, NOT VERTEX-TO-VERTEX, and the first version got
    that wrong in a way that looked like a pass. A coarse patch's border
    vertices are a SUBSET of a fine one's -- every fourth vertex of a stride-4
    edge is exactly a stride-1 vertex -- so comparing matched vertices reports
    zero for a seam full of holes. The hole is the fine vertex sitting off the
    coarse patch's straight edge SEGMENT, which is the definition of a
    T-junction. Comparing the things that coincide is how a crack test passes on
    a cracked mesh.
    """
    stride = stride or collision_stride()[0]
    nb_stride = nb_stride or stride
    va, _t, _g, _m = dg.ground_patch(pa, pz, stride)
    gap = 0.0
    for side, other, nb in (("a+", ((pa + 1) % dg.PATCHES_A, pz), "a-"),
                            ("z+", (pa, pz + 1), "z-")):
        if other[1] >= dg.PATCHES_Z:
            continue
        vb, _t, _g, _m = dg.ground_patch(other[0], other[1], nb_stride)
        mine = _patch_edge(va, stride, side)
        theirs = _patch_edge(vb, nb_stride, nb)
        for p in mine:
            gap = max(gap, min(_point_segment_m(p, theirs[i], theirs[i + 1])
                               for i in range(len(theirs) - 1)))
    return gap


def terrain_survey(step_a=1, step_z=1):
    """Slope of the whole drum ground, sampled on its own lattice.

    The number this module was written not knowing: whether the heightfield is
    walkable AT ALL. `drum_ground` is careful about steps for an LOD reason --
    "every step in the field is a ramp at least one stride-8 cell wide", written
    to stop the coarse levels aliasing -- and it turns out that rule has been
    doing a second job all along, because a ramp 31 m wide cannot be a cliff.
    Nothing had ever checked.
    """
    na, nz = dg.CELLS_A, dg.CELLS_Z
    da = 2.0 * math.pi * dg.FLOOR_R / na * step_a
    dz = (dg.Z1 - dg.Z0) / nz * step_z
    prev_col = None
    worst_a = worst_z = 0.0
    at_a = at_z = None
    lo = hi = None
    n = over = 0
    first_col = None
    for ia in range(0, na, step_a):
        u = ia / na
        col = []
        for iz in range(0, nz + 1, step_z):
            h, k = dg.sample(u, iz / nz)
            col.append((h, k))
            lo = h if lo is None else min(lo, h)
            hi = h if hi is None else max(hi, h)
        if first_col is None:
            first_col = col
        for i in range(len(col) - 1):
            g = abs(col[i + 1][0] - col[i][0]) / dz
            n += 1
            if math.degrees(math.atan(g)) > FLOOR_MAX_DEG:
                over += 1
            if g > worst_z:
                worst_z, at_z = g, (round(ia * 360.0 / na, 2), col[i][1])
        if prev_col is not None:
            for i, (h, k) in enumerate(col):
                g = abs(h - prev_col[i][0]) / da
                if math.degrees(math.atan(g)) > FLOOR_MAX_DEG:
                    over += 1
                if g > worst_a:
                    worst_a, at_a = g, (round(ia * 360.0 / na, 2), k)
        prev_col = col
    # Close the ring: the wrap-around column is the one a linear sweep misses,
    # and `_value_noise` is periodic precisely so that seam is not a cliff.
    for i, (h, k) in enumerate(first_col):
        g = abs(h - prev_col[i][0]) / da
        if g > worst_a:
            worst_a, at_a = g, (0.0, k)
    return {
        "max_slope_circ_deg": round(math.degrees(math.atan(worst_a)), 3),
        "at_circ": at_a,
        "max_slope_axial_deg": round(math.degrees(math.atan(worst_z)), 3),
        "at_axial": at_z,
        "over_floor_angle": over,
        "samples": n,
        "height_min_m": round(lo, 3), "height_max_m": round(hi, 3),
    }


def places():
    """The twelve gazetteer locations on the drum, with the ground under each."""
    out = []
    for q in dr.PLACES:
        if q.get("sector") != "green" or q.get("ring") != 1:
            continue
        u = (q["angle_deg"] / 360.0) % 1.0
        w = min(max((q["z_m"] - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
        h, kind = dg.sample(u, w)
        out.append({"key": q["key"], "angle_deg": q["angle_deg"],
                    "z_m": q["z_m"], "height_m": round(h, 3), "kind": kind,
                    "patch": patch_of(q["angle_deg"], q["z_m"]),
                    "radius_m": round(dg.FLOOR_R - h, 3)})
    return sorted(out, key=lambda r: r["angle_deg"])


# ---------------------------------------------------------------------------
# The A/B: what a floor is NOT
# ---------------------------------------------------------------------------

def band_shell(schema, profile, sector, meta, seg_deg=2.0):
    """`interior.drum_interior`'s band shell over this tile, for comparison.

    THE CONTROL, and this module needs one for the same reason
    `collision.py`'s self-test asserts that the render corridor's floor is NOT
    smooth: a gate that only ever runs on the artefact it was written for cannot
    show it is measuring anything. The band shell is the drum's ground as it
    existed before the heightfield -- four flat circumferential strips at four
    radii, with a riser wall wherever two of them meet. It is a perfectly good
    thing to look at from 500 m and it is not a floor: neighbouring bands differ
    by up to 9.5 m and the wall between them is vertical.
    """
    pa, pz = meta["centre_patch"]
    rings = meta["rings"]
    a0 = (pa - rings) * dg.PATCH_A / dg.CELLS_A * 360.0
    a1 = (pa + rings + 1) * dg.PATCH_A / dg.CELLS_A * 360.0
    z0 = dg.Z0 + max(0, (pz - rings) * dg.PATCH_Z) / dg.CELLS_Z * (dg.Z1 - dg.Z0)
    z1 = dg.Z0 + min(dg.CELLS_Z, (pz + rings + 1) * dg.PATCH_Z) \
        / dg.CELLS_Z * (dg.Z1 - dg.Z0)
    v, t, m = it.drum_interior(schema, profile, sector, arc_deg=a1 - a0,
                               start_deg=a0, z_span=(z0, z1), seg_deg=seg_deg)
    return v, t, _spans(m.get("groups", []))


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

def build(key=None, angle_deg=None, z_m=None, rings=None, schema=None,
          profile=None):
    """Everything a body needs to stand on the drum at a named place.

    Returns (verts, tris, groups, meta) with `meta["spawn"]` the feet position
    and `meta["gravity_m_s2"]` the field it stands in.
    """
    schema, profile, sector = drum(schema, profile)
    if key is not None:
        q = dr.by_key(key)
        angle_deg, z_m = q["angle_deg"], q["z_m"]
    if angle_deg is None or z_m is None:
        raise ValueError("build() needs a gazetteer key or an (angle, z)")
    pa, pz = patch_of(angle_deg, z_m)
    v, t, g, meta = ground_shell(pa, pz, rings=rings)
    h, kind = dg.sample((angle_deg / 360.0) % 1.0,
                        min(max((z_m - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0))
    meta.update({
        "key": key, "angle_deg": angle_deg, "z_m": z_m,
        "spawn": stand_at(angle_deg, z_m, surface=(v, t)),
        "spawn_kind": kind, "spawn_height_m": round(h, 3),
        "gravity_m_s2": round(gravity_m_s2(schema), 4),
        "drum_lod0_triangles": dg.PATCHES_A * dg.PATCHES_Z * 2
        * dg.PATCH_A * dg.PATCH_Z,
    })
    return v, t, g, meta


def write_obj(path, verts, tris, groups, name="drum_ground"):
    C.write_obj(path, verts, tris, groups, name=name)


# ---------------------------------------------------------------------------
# The walk, in the engine
# ---------------------------------------------------------------------------

def _glb(obj_path, glb_path):
    import export_gltf                                          # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path, "--out", glb_path]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv


def walk(key="the_garden", traverse=None, timeout=1800, rings=None,
         godot=None):
    """Put a body on the drum and walk it, headless, in the real engine.

    Deliberately the same shape as `walkable.walk_deck` -- write the render
    mesh, write the collision mesh, hand BOTH to `walk.tscn`, drive it with
    `--walk-test` and parse the verdict -- with two differences that are the
    drum:

      `--gravity-mode=drum`, so "down" is the outward radial at the body's own
      position and changes as it walks around the barrel, and

      no `--goto`, because there is no door here and nothing to walk into. The
      claim on the drum is the traverse: how far a body actually gets, and
      whether it was ever off the floor.

    This lives here rather than in `walkable.py` because `walkable.walk_deck`
    calls `deck.build_deck`, which raises on `green/1` by name. Wiring it is
    four lines in two files this task does not own; the exact patch is written
    down in STATE.md.
    """
    import walkable as W                                        # noqa: PLC0415
    godot = godot or W.godot_binary()
    if godot is None:
        return {"key": key, "error": "no double-precision Godot binary -- "
                "run `bash tools/build_godot.sh` (see docs/godot-binary.md)"}
    traverse = W.TRAVERSE_FRAMES if traverse is None else traverse

    schema, profile, sector = drum()
    out = os.path.join(ROOT, "station/generated/scene/drum")
    os.makedirs(out, exist_ok=True)
    stem = f"drumwalk_{key}"

    cv, ct, cg, meta = build(key=key, rings=rings, schema=schema,
                             profile=profile)
    write_obj(os.path.join(out, f"{stem}_col.obj"), cv, ct, cg)
    rv, rt, rg, _rm = render_ground(meta)
    write_obj(os.path.join(out, f"{stem}.obj"), rv, rt, rg, name="ground")
    _glb(os.path.join(out, f"{stem}.obj"), os.path.join(out, f"{stem}.glb"))
    _glb(os.path.join(out, f"{stem}_col.obj"),
         os.path.join(out, f"{stem}_col.glb"))

    sx, sy, sz = meta["spawn"]
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--",
           f"--glb={os.path.join(out, stem + '.glb')}",
           f"--collision={os.path.join(out, stem + '_col.glb')}",
           f"--spawn={sx},{sy},{sz}", "--gravity-mode=drum",
           f"--gravity={meta['gravity_m_s2']}",
           "--walk-test", f"--traverse={traverse}"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"key": key, "error": f"timed out after {timeout}s"}
    import re                                                   # noqa: PLC0415
    m = re.search(r"WALKTEST (.+)", res)
    if not m:
        tail = "\n".join(res.strip().splitlines()[-6:])
        return {"key": key, "error": f"no verdict printed; tail: {tail[:400]}"}
    d = {"key": key, "collision_tris": len(ct), "render_tris": len(rt),
         "spawn_kind": meta["spawn_kind"], "patches": len(meta["patches"]),
         "edge_m": meta["edge_m"], "traverse_frames": traverse}
    for tok in m.group(1).split():
        k, _, val = tok.partition("=")
        d[k] = val
    return d


def walk_verdict(d):
    """Pass/fail on the drum, in the same terms and against the same numbers the
    deck walk uses -- imported from `walkable`, not restated, so the drum cannot
    be certified against an easier bar than the corridor."""
    import walkable as W                                        # noqa: PLC0415
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if float(d.get("drop", 0)) > W.MAX_DECK_DROP_M:
        return False, (f"dropped {float(d['drop']):.2f} m from a spawn 50 mm "
                       f"above the ground -- the floor is not where it says")
    if float(d.get("moved_1s", 0)) < W.MIN_WALK_M:
        return False, f"walked {float(d.get('moved_1s', 0)):.2f} m in a second"
    off, tot = (d.get("offfloor", "0/0").split("/") + ["0"])[:2]
    if int(off) > 0:
        return False, (f"left the floor for {off} of {tot} frames -- it walked "
                       f"off the ground")
    got = float(d.get("traverse_m", 0))
    if got < W.MIN_TRAVERSE_M:
        return False, (f"covered {got:.1f} m of drum, under the "
                       f"{W.MIN_TRAVERSE_M:.0f} m bar -- something is snagging")
    return True, (f"a body spawns on {d['spawn_kind']} at {d['key']}, walks "
                  f"{got:.1f} m over {d['patches']} ground patches and never "
                  f"leaves the floor")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

SABOTAGE = {
    "stride": "build the collision ground at stride 4 instead of the derived 1",
    "winding": "reverse every triangle, so the floor faces the void",
    "lift": "raise the collision ground 0.5 m off the ground you can see",
    "cliff": "put a 6 m step in the tile, one lattice cell wide",
    "tiny": "build one ring of patches instead of the derived two",
}


def _sabotage(kind, v, t, g, meta):
    """Break the tile on purpose, so the gates can be seen to bite.

    EVERY GATE IN THIS MODULE HAS TO BE ABLE TO FAIL ON REAL CONTENT, and this
    project has shipped at least four that could not -- an `x == x` determinism
    check, a `hasattr` on a name nothing sets, a density ceiling that forbade
    detail, a walk test that asked whether a body moved and not how far. Three
    of the checks below are written as inverted assertions on real geometry (the
    band shell, a coarse tile, a mixed seam) and that covers the criteria. This
    covers the RIG: same suite, same thresholds, a tile with a known defect in
    it, and a nonzero exit code.
    """
    if kind == "stride":
        pa, pz = meta["centre_patch"]
        v2, t2, g2, m2 = ground_shell(pa, pz, rings=meta["rings"], stride=4)
        return v2, t2, g2, {**meta, **m2}
    if kind == "winding":
        return v, [(a, c, b) for a, b, c in t], g, meta
    if kind == "lift":
        out = []
        for x, y, z in v:
            rr = math.hypot(x, y) or 1.0
            k = (rr - 0.5) / rr
            out.append((x * k, y * k, z))
        return out, t, g, meta
    if kind == "cliff":
        # One lattice column dropped 6 m -- the exact thing `drum_ground`'s
        # step rule ("every step is a ramp at least one stride-8 cell wide")
        # exists to prevent, and the thing a slope gate is for.
        out = []
        for x, y, z in v:
            a = math.atan2(y, x) % (2.0 * math.pi)
            rr = math.hypot(x, y)
            if int(a / (2.0 * math.pi) * dg.CELLS_A) % 8 == 0:
                rr += 6.0
            out.append((rr * math.cos(a), rr * math.sin(a), z))
        return out, t, g, meta
    if kind == "tiny":
        pa, pz = meta["centre_patch"]
        v2, t2, g2, m2 = ground_shell(pa, pz, rings=1)
        return v2, t2, g2, {**meta, **m2}
    raise SystemExit(f"--sabotage: no such defect {kind}; have "
                     f"{sorted(SABOTAGE)}")


def _selftest(full=False, sabotage=None):
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile, sector = drum()
    check("the drum is found by geometry, not by name", sector == "green",
          f"drum_sector says {sector}")

    # --- the stride, and the demonstration that its criterion bites ---------
    stride, rows = stride_report()
    by = {r["stride"]: r for r in rows}
    print(f"collision stride {stride} (cell "
          f"{by[stride]['cell_m']} m, error {by[stride]['error_m']} m "
          f"against a {STEP_M:.3f} m step)")
    for r in rows:
        print(f"   stride {r['stride']:2d}  cell {r['cell_m']:6.2f} m  "
              f"error {r['error_m']:6.3f} m  "
              f"{'USABLE' if r['error_m'] <= STEP_M else 'too coarse'}")
    check("the collision stride is the coarsest that stays inside a step",
          by[stride]["error_m"] <= STEP_M
          and all(r["error_m"] > STEP_M for r in rows if r["stride"] > stride),
          f"stride {stride} at {by[stride]['error_m']} m")
    # THE DEMONSTRATION. If this ever stops failing, the terrain has lost the
    # detail that made a heightfield worth having and this module's whole
    # argument for stride 1 has evaporated -- exactly the shape of
    # `collision._selftest`'s "and the render floor is NOT smooth".
    check("and the next stride out FAILS it -- the reason this is a tile",
          by[2]["error_m"] > STEP_M,
          f"stride 2 measures {by[2]['error_m']} m; if that is under "
          f"{STEP_M} m the ground has flattened")

    # --- the ground itself --------------------------------------------------
    pa, pz = patch_of(60.0, 5100.0)                 # the_garden
    v, t, g, meta = build(key="the_garden")
    if sabotage:
        print(f"SABOTAGE `{sabotage}`: {SABOTAGE[sabotage]}. Every FAIL below "
              f"is this suite working.")
        v, t, g, meta = _sabotage(sabotage, v, t, g, meta)
        meta = dict(meta)
        meta["spawn"] = stand_at(60.0, 5100.0, surface=(v, t))
    check("a collision tile is emitted", len(t) > 0, str(meta)[:120])
    a_m, z_m = patch_span_m()
    print(f"tile: {len(meta['patches'])} patches "
          f"({meta['rings']} rings of {a_m:.1f} x {z_m:.1f} m), "
          f"{len(t):,} triangles, nearest edge {meta['edge_m']:.0f} m from "
          f"the spawn")

    # It has to be much cheaper than the thing it stands in for, which for the
    # drum is not a render corridor but the whole ground at lod0.
    check("the tile is a fraction of the drum's own lod0 ground",
          len(t) * 8 < meta["drum_lod0_triangles"],
          f"{len(t):,} against {meta['drum_lod0_triangles']:,}")

    # --- winding: a floor facing the wrong way is a hole --------------------
    sl = slope_report(v, t, g)
    print(f"slope over the tile: max {sl['max_deg']:.2f} deg, "
          f"{sl['over_floor_angle']} of {sl['triangles']:,} triangles over "
          f"{FLOOR_MAX_DEG:.0f} deg")
    check("every collision triangle faces the player, not the void",
          sl["max_deg"] < 90.0,
          f"worst {sl['max_deg']:.1f} deg at {sl['at']} -- over 90 deg is a "
          f"face wound outward, which Godot lets a body fall through")
    check("the ground is walkable at the controller's own floor angle",
          sl["over_floor_angle"] == 0,
          f"{sl['over_floor_angle']} triangles steeper than "
          f"{FLOOR_MAX_DEG} deg, worst {sl['max_deg']:.1f} at {sl['at']}")

    # --- THE A/B. The same measure, on the surface this replaces ------------
    bv, bt, bg = band_shell(schema, profile, sector, meta)
    bs = slope_report(bv, bt, bg)
    check("and the band shell is NOT a floor -- the reason this module exists",
          bs["over_floor_angle"] > 0,
          f"drum_interior's shell has {bs['over_floor_angle']} triangles over "
          f"{FLOOR_MAX_DEG} deg; if that is zero it has stopped having bands")
    print(f"   control: interior.drum_interior's band shell over the same "
          f"ground -- max {bs['max_deg']:.1f} deg, "
          f"{bs['over_floor_angle']} of {bs['triangles']:,} triangles "
          f"unwalkable")
    bd = deviation(bv, bt, meta, n_a=14, n_z=14)
    check("and it stands metres off the ground a player sees",
          abs(bd["max_m"]) > 1.0,
          f"band shell is {bd['max_m']:+.2f} m from the terrain")
    print(f"   control: and it sits {bd['max_m']:+.2f} m from the heightfield "
          f"(rms {bd['rms_m']:.2f} m)")

    # --- no holes, and the collision surface IS the visible one -------------
    hs = holes(v, t, meta, n_a=24, n_z=24)
    check("there is ground under every point of the tile", not hs,
          f"{len(hs)} sample points over nothing, first {hs[:3]}")

    rv, rt, rg, _rm = render_ground(meta)
    dev = deviation(v, t, meta, other=(rv, rt), n_a=18, n_z=18)
    print(f"collision vs the render ground it ships with: max "
          f"{dev['max_m'] * 1000:+.1f} mm, rms {dev['rms_m'] * 1000:.1f} mm "
          f"over {dev['samples']} casts")
    check("a body stands on the ground it can see",
          dev["missed"] == 0 and abs(dev["max_m"]) <= STEP_M,
          f"{dev['max_m']:+.3f} m at {dev['at']}, {dev['missed']} missed")

    # AND THE STRONG FORM, which is the one that says the two meshes are the
    # SAME surface rather than merely a compatible one. The number above is
    # dominated by the RENDER's own LOD: `drum_ground.lod_table` switches to
    # lod1 at 198 m and the tile reaches 250 m, so its outer ring is drawn at
    # stride 2 while collision is uniform stride 1. Inside the lod0 radius the
    # two are built from identical lattice calls and must agree to nothing.
    lod0_m = dg.lod_table()[1]["switch_distance_m"]
    eye = stand_at_patch(meta)
    near = [(a, z) for a, z in _tile_samples(meta, n_a=18, n_z=18)
            if math.dist((dg.FLOOR_R * math.cos(math.radians(a)),
                          dg.FLOOR_R * math.sin(math.radians(a)), z), eye)
            < lod0_m]
    cm, cr = _Caster(v, t), _Caster(rv, rt)
    worst = max((abs((cr.radius_at(a, z) or 0.0) - (cm.radius_at(a, z) or 0.0))
                 for a, z in near), default=1e9)
    check("and inside the lod0 radius they are the identical surface",
          worst < 1e-9,
          f"{worst * 1000:.4f} mm over {len(near)} casts within {lod0_m:.0f} m")
    print(f"   within the render's own lod0 radius ({lod0_m:.0f} m, "
          f"{len(near)} casts): {worst * 1e6:.3f} um")

    # And the same measure fails on a tile built too coarse, which is what
    # makes the number above mean something.
    cv, ctt, _cg, cmeta = ground_shell(pa, pz, rings=1, stride=4)
    cdev = deviation(cv, ctt, cmeta, other=(rv, rt), n_a=12, n_z=12)
    check("and a coarser tile FAILS that -- the criterion can bite",
          abs(cdev["max_m"]) > STEP_M,
          f"a stride-4 tile is {cdev['max_m']:+.3f} m off the render ground; "
          f"under {STEP_M} m would mean the ground has flattened")
    print(f"   control: the same tile at stride 4 sits {cdev['max_m']:+.3f} m "
          f"off the render ground")

    # --- seams --------------------------------------------------------------
    gap = seam_gaps(pa, pz)
    check("neighbouring collision patches share their edge exactly",
          gap < 1e-9, f"largest seam gap {gap * 1000:.3f} mm")
    mixed = seam_gaps(pa, pz, stride=1, nb_stride=4)
    check("and mixed strides do NOT -- which is why collision is uniform",
          mixed > STEP_M,
          f"a stride-1 patch beside an unclamped stride-4 one leaves "
          f"{mixed * 1000:.1f} mm of T-junction; under a step means the "
          f"terrain has flattened and the seam no longer proves anything")
    print(f"   seam: uniform {gap * 1000:.4f} mm, "
          f"stride 1 against unclamped stride 4 {mixed * 1000:.1f} mm")

    # --- the tile is big enough for the gate that will run ------------------
    want = walk_distance_m()
    check("the tile is bigger than the walk the gate asks for",
          meta["edge_m"] >= want,
          f"nearest edge {meta['edge_m']:.0f} m against a {want:.0f} m walk")
    check("and one ring would NOT be -- the ring count is derived",
          rings_for(want) > 1 and 1 * min(a_m, z_m) < want,
          f"one ring reaches {min(a_m, z_m):.0f} m, the walk is {want:.0f} m")

    # --- the spawn ----------------------------------------------------------
    sp = meta["spawn"]
    r = math.hypot(sp[0], sp[1])
    h, _k = dg.sample(60.0 / 360.0, (5100.0 - dg.Z0) / (dg.Z1 - dg.Z0))
    cast = _Caster(v, t)
    under = cast.radius_at(60.0, 5100.0)
    check("the spawn stands on the MESH, 50 mm clear of it",
          under is not None
          and abs(r - (under - SPAWN_ABOVE_M)) < 1e-9,
          f"spawn r={r:.4f}, the triangle under it is at r={under}")
    # And say how far that is from the field, because it is not zero and the
    # difference is the whole reason the spawn is cast rather than computed.
    print(f"   spawn: mesh r={under:.4f}, field r={dg.FLOOR_R - h:.4f}, "
          f"{(dg.FLOOR_R - h - under) * 1000:+.1f} mm apart -- the spawn "
          f"follows the mesh")
    check("and it is above the ground, not inside it",
          r < under, f"spawn r={r:.4f} against surface r={under:.4f}")
    check("up is INWARD on the drum -- this station spins",
          stand_at(60.0, 5100.0, 2.0, surface=(v, t))[0] ** 2
          + stand_at(60.0, 5100.0, 2.0, surface=(v, t))[1] ** 2
          < sp[0] ** 2 + sp[1] ** 2,
          "a body's head is at a smaller radius than its feet")
    check("gravity is the schema's, not 9.81 written down",
          abs(meta["gravity_m_s2"] - 9.80665) < 0.01,
          f"{meta['gravity_m_s2']} m/s2 at r={dg.FLOOR_R}")

    # --- every location on the drum -----------------------------------------
    rows = places()
    print(f"the {len(rows)} gazetteer locations on the drum:")
    on_water = []
    for row in rows:
        print(f"   {row['key']:16s} {row['angle_deg']:6.1f} deg  "
              f"z={row['z_m']:.0f}  h={row['height_m']:+6.2f} m  "
              f"patch {row['patch']}  {row['kind']}")
        if row["kind"] == "water_surface":
            on_water.append(row["key"])
    check("every drum location has ground under it",
          len(rows) == 12
          and all(dg.Z0 <= r["z_m"] <= dg.Z1 for r in rows),
          f"{len(rows)} rows, z range "
          f"{min(r['z_m'] for r in rows)}..{max(r['z_m'] for r in rows)} "
          f"against ground {dg.Z0:.0f}..{dg.Z1:.0f}")
    check("every drum location's patch is on the ground's own grid",
          all(0 <= r["patch"][0] < dg.PATCHES_A
              and 0 <= r["patch"][1] < dg.PATCHES_Z for r in rows))
    if on_water:
        print(f"   NOTE: {', '.join(on_water)} stands on `water_surface` -- a "
              f"body there walks on the lake. The collision follows the render "
              f"exactly, so this is a CONTENT gap, not a collision one.")

    if full:
        # The whole-drum question, and it takes about a minute.
        sv = terrain_survey()
        print(f"whole-drum slope survey: circumferential max "
              f"{sv['max_slope_circ_deg']:.2f} deg at {sv['at_circ']}, axial "
              f"max {sv['max_slope_axial_deg']:.2f} deg at {sv['at_axial']}, "
              f"{sv['over_floor_angle']} of {sv['samples']:,} over "
              f"{FLOOR_MAX_DEG} deg")
        check("no part of the drum ground is steeper than a floor",
              sv["over_floor_angle"] == 0,
              f"{sv['over_floor_angle']} lattice steps over "
              f"{FLOOR_MAX_DEG} deg")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", default="the_garden",
                    help="gazetteer key on the drum to centre the tile on")
    ap.add_argument("--angle", type=float, default=None)
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--rings", type=int, default=None)
    ap.add_argument("--obj", default="")
    ap.add_argument("--render-obj", default="",
                    help="the ground a player SEES over the same patches")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--full", action="store_true",
                    help="with --selftest, also sweep the whole drum (~70 s)")
    ap.add_argument("--sabotage", default=None, choices=sorted(SABOTAGE),
                    help="with --selftest, break the tile on purpose and show "
                         "the gates fire. A gate that cannot fail is not a "
                         "gate; this is how that is demonstrated rather than "
                         "claimed")
    ap.add_argument("--terrain", action="store_true",
                    help="slope survey of the whole heightfield")
    ap.add_argument("--places", action="store_true")
    ap.add_argument("--walk", action="store_true",
                    help="put a body on the drum in Godot and walk it")
    ap.add_argument("--traverse", type=int, default=None)
    a = ap.parse_args()

    if a.selftest:
        return _selftest(full=a.full, sabotage=a.sabotage)

    drum()
    if a.terrain:
        sv = terrain_survey()
        for k, val in sv.items():
            print(f"  {k}: {val}")
        return 0
    if a.places:
        for row in places():
            print(f"  {row['key']:16s} {row['angle_deg']:6.1f} deg  "
                  f"z={row['z_m']:.0f}  h={row['height_m']:+6.2f} m  "
                  f"r={row['radius_m']:.2f}  patch {row['patch']}  "
                  f"{row['kind']}")
        return 0
    if a.walk:
        d = walk(key=a.at, traverse=a.traverse, rings=a.rings)
        good, why = walk_verdict(d)
        print(f"  {'PASS' if good else 'FAIL'}  drum {a.at}  {why}")
        if "error" not in d:
            print(f"        {d['render_tris']:,} render triangles, "
                  f"{d['collision_tris']:,} collision; spawn on "
                  f"{d['spawn_kind']}; legs "
                  f"{d.get('legs')}  offfloor={d.get('offfloor')}")
        return 0 if good else 1

    v, t, g, meta = build(key=None if a.angle is not None else a.at,
                          angle_deg=a.angle, z_m=a.z, rings=a.rings)
    print(f"drum tile at {meta['angle_deg']:.1f} deg z={meta['z_m']:.0f} "
          f"({meta['spawn_kind']}, {meta['spawn_height_m']:+.2f} m): "
          f"{len(t):,} collision triangles over {len(meta['patches'])} "
          f"patches, nearest edge {meta['edge_m']:.0f} m")
    sl = slope_report(v, t, g)
    print(f"  slope max {sl['max_deg']:.2f} deg, "
          f"{sl['over_floor_angle']} triangles over {FLOOR_MAX_DEG:.0f} deg")
    print(f"  spawn {meta['spawn'][0]:.3f},{meta['spawn'][1]:.3f},"
          f"{meta['spawn'][2]:.3f}  gravity {meta['gravity_m_s2']} m/s2")
    if a.obj:
        write_obj(a.obj, v, t, g)
        print(f"  wrote {a.obj}")
    if a.render_obj:
        rv, rt, rg, _m = render_ground(meta)
        write_obj(a.render_obj, rv, rt, rg, name="ground")
        print(f"  wrote {a.render_obj}: {len(rt):,} render triangles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
