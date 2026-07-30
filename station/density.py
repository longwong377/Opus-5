#!/usr/bin/env python3
"""Layer 2's missing exit criterion: is there anything THERE?

WHY THIS EXISTS
---------------
CLAUDE.md's layer-2 test, verbatim: *"Every addressed location has mesh,
closed, correctly wound, inside its own footprint."* Every word of that is
TOPOLOGICAL, and **a cube passes all of it**. So 118 locations of blockout
passed layer 2 legitimately, layer 3 painted the blockout, layer 4 lit the
blockout, and every gate stayed green while the owner looked at the result and
said the buildings are "shitty little cubes" and the trees are a "sad excuse
for a tree".

He is right, and the reason no gate caught it is that no gate measured FORM.
`garden.py` even asserts the opposite -- its self-test checks the townscape is
*below* 0.06 tri/m2 and calls `block_building` "Cheap by design". The only
density number in the repository was a ceiling. This module supplies the floor.

WHAT IT MEASURES, AND WHY NOT TRIANGLES
---------------------------------------
Triangles are a weak metric: subdividing a cube multiplies its triangle count
without changing a thing anybody can see. Whatever is measured has to be
invariant to subdivision, or the first response to the gate will be a
tessellation flag and the gate will go green over the same cube.

The measure here is **visible line density**:

    lambda  =  (length of edges a viewer would see as a LINE)  /  (surface area)

in metres of line per square metre of surface, m^-1. It is what "detailed"
actually looks like -- a detailed surface is one with a lot of line-work on it
-- and it has three properties that matter:

  * **Subdivision cannot move it.** A coplanar split has a dihedral of zero, so
    it contributes no line. `_subdivided_box` in the self-test builds exactly
    that cheat and asserts the number does not budge.
  * **Tessellating a curve cannot move it far enough to matter.** A lathe at
    turn angle tau has one line per R*tau of surface, so its best possible
    lambda is 1/(R*tau_min) -- a hard ceiling well under the floor at every
    scale this station is built at. `_cylinder` demonstrates it.
  * **Sub-pixel greeble cannot move it.** A line only counts if both surfaces
    that meet at it are at least one screen pixel across at the distance the
    location is composed from. Detail finer than that is the normal map's job,
    not the mesh's, and counting it would reward geometry nobody can see.

Reported alongside, not gated (see THE ONE GATE below): triangle count against
the location's budget allotment, triangle density, the octave spread of feature
sizes, and the effective number of distinct surface normals.

THE FLOOR IS DERIVED, THREE WAYS, AND THE LOWEST WINS
-----------------------------------------------------
A floor with no derivation is a guess with a decimal point, so there are three
independent bounds and the gate uses the **smallest** of them. They map onto
three of the four dimensions in `docs/AAA-STANDARD.md`:

  1. **PERFORMANCE -- what the card can draw.** `budget.py` allots a triangle
     count to each scene's visible set. Spend it as relief and the achievable
     line density follows exactly: a grid of raised panels at pitch e over area
     S costs 12 triangles per cell -- a closed box, which is what
     `_relief_box` in the self-test actually builds -- and lays down 2e of line
     per cell, so

         n = 12 S / e^2 ,   lambda = 2 / e   =>   lambda_budget = 0.577 sqrt(n/S)

     Nothing here is chosen; `n` comes straight out of `budget.py` and `S` is
     measured. `lam_budget` and `budget_pitch` are two rearrangements of the
     same equation and the self-test asserts they agree -- the first draft had
     10 in one and 12 in the other, a 9% discrepancy nothing would have caught.

  2. **PERCEPTION -- what the screen can show.** At 1440p (CLAUDE.md's target)
     and the project's own camera FOV (read out of `godot/scenes/*.tscn`, not
     remembered), one pixel subtends theta radians. A feature needs two samples
     to exist at all, so the finest useful pitch is 2p where p = d*theta, and

         lambda_nyquist = 2 / (2p) = 1/p

     Geometry past that is sub-pixel and is waste, not detail.

  3. **FIDELITY -- what the show actually shows.** `REFERENCE` below measures
     Babylon 5's own sets: a Canny edge map at an absolute 4%/2% luminance-step
     threshold, over frames with a human figure in them for scale, giving line
     density in the SAME m^-1 units. Three frames, three sectors, 6.2 to 11.2
     m^-1 at their own resolution. Converted to a per-location floor through
     that location's surface-to-projected-area ratio and its own pixel size.

The three disagree, often by a lot, and taking the minimum means the floor is
whichever constraint genuinely binds. Mostly that is the budget, which is the
answer that needs the least defending: **this is detail the project has already
decided it can afford and has not built.**

`budget.py` currently reports the drum visible set at 51,320 triangles of
300,000, 17% -- so 83% of the budget is unspent. The floor is not ambition. It
is the money already on the table.

THE ONE GATE
------------
One number is gated, and the rest are printed. That is deliberate. A second
gate needs a second floor, and the honest position is that the octave spread
and the normal count have no derivation as good as lambda's -- any floor for
them would be picked, and a picked floor is the thing this file exists to
avoid. They are printed because they are diagnostic (they are what separates
"flat" from "uniformly greebled"), and they are not gated because they are not
derived. If someone later derives one, gate it then.

VIEWING DISTANCE COMES FROM THE FOOTPRINT, NOT FROM THE MESH
-------------------------------------------------------------
The composing distance -- where the location fills the frame -- is computed
from `directory.PLACES[...]["footprint"]` via `rooms.room_extent_m`, which is
the location's real size on the station and is layer-1 data that assertions
already hold. Deriving it from the mesh's bounding box instead would let a
lazier builder lower its own bar: build less, get judged closer, get a coarser
pixel, get an easier floor. A player can always walk closer than the composing
distance, so this floor is the *minimum* bar, not the maximum.

WHAT THIS MEASURE IS NOT HONEST ABOUT
--------------------------------------
  * It counts hidden lines. A window band box sunk into a wall contributes all
    twelve of its edges even though four are buried. That inflates the CURRENT
    content's score, so a failure measured this way is a floor on the failure.
  * The reference bound counts lines a set gets from paint, decals, shadow and
    dressing, not just from form. That makes bound 3 an over-estimate of what
    geometry must supply -- which is why it is one of three and the minimum is
    taken. Where it binds, it is stated in the report.
  * It says nothing about whether the lines are in the right places. A surface
    can hit lambda and still be ugly. This is a floor under blockout, not a
    definition of good.
  * **The exterior's scope stops at the fittings.** `_m_components` builds the
    96 hull fittings, 6,296,778 m2 of surface, and not the hull they sit on.
    Integrating the radius profile puts the hull's own lateral surface at
    14,967,709 m2, so the full exterior assembly is 21,264,487 m2 and the
    exterior floor computed on the fittings alone -- 0.146 m^-1 -- is 1.8x
    harsher than the 0.079 m^-1 the whole assembly would give. The fittings
    measure 0.052 m^-1, so they fail on either scope (36% or 66% of bar) and no
    verdict turns on it. Widening the scope needs `generate_hull` to hand over a
    mesh, which it does not currently do in memory.
  * **The interior floor bottoms out.** Clipping to the 99 m sight line caps the
    visible surface at about 20,900 m2, so every location bigger than that in
    both axes gets the same floor, ~0.98 m^-1 -- a line every metre. Eleven of
    the sixteen locations that currently pass are district-scale rooms scraping
    over that cap by 3% to 21%, and they are the same blockout as the sixty that
    fail. The floor is right (60,000 triangles genuinely cannot articulate
    20,900 m2 more finely than that) and it is also weakest exactly where the
    location is largest. Read the `%show` column for those rows: all eleven sit
    at 5% of what a Babylon 5 set carries. The fix is streaming and LOD raising
    `budget.py`'s interior allotment, not a change here.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# The screen. Sourced, not remembered.
# ---------------------------------------------------------------------------
# CLAUDE.md, "Verification": "Target: RTX 4070 / RX 7800 XT class, 1440p60,
# 12 GB VRAM."
SCREEN_H_PX = 1440

# Godot's Camera3D.fov is the VERTICAL field of view under the default
# keep_aspect (KEEP_HEIGHT). These are read from the project's own scenes so a
# camera change moves the metric with it:
#   godot/scenes/interior.tscn : fov = 55.0
#   godot/scenes/drum.tscn     : fov = 55.0
#   godot/scenes/exterior.tscn : fov = 46.0
SCENE_FOV_DEG = {"interior": 55.0, "drum": 55.0, "exterior": 46.0}
SCENE_TSCN = {"interior": "godot/scenes/interior.tscn",
              "drum": "godot/scenes/drum.tscn",
              "exterior": "godot/scenes/exterior.tscn"}

# ---------------------------------------------------------------------------
# What counts as a visible line
# ---------------------------------------------------------------------------
# The image-space measurement of the reference frames (REFERENCE, below) calls
# a pixel an edge when the luminance step across it is at least 4% (hysteresis
# down to 2%). To measure the same thing on a mesh, ask what normal step
# produces that luminance step.
#
# Lambert: I = cos(alpha) for incidence alpha, so dI = sin(alpha) d(alpha).
# Taking alpha = 45 deg -- the median incidence over a hemisphere of surface
# orientations under a single key light, and the angle every one of this
# project's render scripts actually uses (`--sun-elev 45`, export_scene.py) --
#
#   d(alpha) = 0.04 / sin(45 deg) = 0.0566 rad = 3.24 deg
#
# So an edge whose two faces differ in normal by 3.24 degrees or more draws a
# line a viewer can see, and one below it does not. The same threshold defines
# a FACET: a patch of surface with no visible line inside it.
WEBER_HI = 0.04            # luminance step a Canny "strong" edge needs
WEBER_LO = 0.02            # hysteresis floor
SHADE_INCIDENCE_DEG = 45.0
CREASE_DEG = math.degrees(WEBER_HI / math.sin(math.radians(SHADE_INCIDENCE_DEG)))

# Vertex welding tolerance. Generators emit each primitive with its own
# vertices, so without welding every box would read as six unconnected quads
# with 24 boundary edges and the measure would be meaningless.
WELD_M = 1e-4

# ---------------------------------------------------------------------------
# BOUND 3 -- what a Babylon 5 set actually shows
# ---------------------------------------------------------------------------
# Measured by `measure_reference()` below, which is the same Canny operator at
# the same absolute thresholds used on our own frames. Each entry carries the
# scale anchor that turns pixels into metres, because an edge-pixel fraction
# without a scale is not a line density.
#
# The anchor is a standing human figure, measured off the frame at
# magnification (tools/refzoom.py, and a pixel-column dump). Stature is taken
# at 1.75 m +- 0.05, which is the only number here that is not measured off the
# frame itself -- see INV-071.
#
# HEALTH WARNING, stated because it changes how the number may be used: these
# counts include every line a set gets from paint, decals, cast shadow, dressing
# and costume, not only from form. Bound 3 is therefore an OVER-estimate of what
# geometry has to supply. It is used as one of three bounds with the minimum
# taken, and the report says when it binds.
REFERENCE = (
    # (path, figure height px, stature m, what the frame is, scene it bounds)
    ("reference/10-interiors-generic-kit/more hallway.jpg", 247.0, 1.80,
     "Grey-sector transit tube, one standing figure mid-frame", "interior"),
    ("reference/10-interiors-generic-kit/garden more.jpg", 104.0, 1.70,
     "Garden terrace, standing group mid-frame", "drum"),
    ("reference/09-garden-core-and-transit/garden.png", 70.0, 1.75,
     "Garden civic landmark, two figures on the paving", "drum"),
)

# ---------------------------------------------------------------------------
# Mesh measurement
# ---------------------------------------------------------------------------


def _weld(verts, eps=None):
    """Map vertices onto a shared grid so touching faces share edges.

    `eps` resolves to the module constant AT CALL TIME, not as a default bound
    at definition time. That is not a style preference: `tools/mutation_sweep.py`
    perturbs module constants after import, and a captured default makes the
    constant unreachable, which is how WELD_M came back UNGUARDED on the first
    sweep of this module. The same applies to `crease_deg` below and to
    `edge_fraction`'s thresholds.
    """
    inv = 1.0 / (WELD_M if eps is None else eps)
    seen, out = {}, []
    for x, y, z in verts:
        k = (int(round(x * inv)), int(round(y * inv)), int(round(z * inv)))
        i = seen.get(k)
        if i is None:
            i = seen[k] = len(seen)
        out.append(i)
    return out, len(seen)


def _tri_geometry(verts, tris):
    """Per-triangle area and unit normal, and the total surface area."""
    areas, normals = [], []
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        ln = math.sqrt(nx * nx + ny * ny + nz * nz)
        areas.append(0.5 * ln)
        normals.append((nx / ln, ny / ln, nz / ln) if ln > 1e-18 else (0.0, 0.0, 0.0))
    return areas, normals, sum(areas)


class _DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        p = self.p
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def analyse(verts, tris, min_facet_m=0.0, crease_deg=None):
    """Everything this module measures about one mesh.

    `min_facet_m` is the screen-resolution filter: a line is only counted when
    BOTH facets meeting at it are at least that wide. Pass 0.0 to measure the
    raw mesh with no viewing model at all (the self-test does, so the probes
    are about geometry rather than about the camera).
    """
    crease_deg = CREASE_DEG if crease_deg is None else crease_deg
    if not tris:
        return dict(tris=0, area=0.0, line_m=0.0, lam=0.0, facets=0,
                    octaves=0.0, normals=0.0, proj_ratio=4.0, size_m=0.0)

    widx, _nv = _weld(verts)
    areas, normals, total = _tri_geometry(verts, tris)

    # --- edges -> the faces that share them --------------------------------
    edge_faces = {}
    for fi, (a, b, c) in enumerate(tris):
        ia, ib, ic = widx[a], widx[b], widx[c]
        for u, v in ((ia, ib), (ib, ic), (ic, ia)):
            if u == v:
                continue
            edge_faces.setdefault((u, v) if u < v else (v, u), []).append(fi)

    cos_crease = math.cos(math.radians(crease_deg))

    # --- facets: connected runs of surface with no visible line inside ------
    dsu = _DSU(len(tris))
    for faces in edge_faces.values():
        if len(faces) != 2:
            continue
        f, g = faces
        n0, n1 = normals[f], normals[g]
        if n0[0] * n1[0] + n0[1] * n1[1] + n0[2] * n1[2] >= cos_crease:
            dsu.union(f, g)
    facet_area = {}
    for fi in range(len(tris)):
        r = dsu.find(fi)
        facet_area[r] = facet_area.get(r, 0.0) + areas[fi]
    facet_of = [dsu.find(fi) for fi in range(len(tris))]
    facet_extent = {k: math.sqrt(a) for k, a in facet_area.items()}

    # --- lines --------------------------------------------------------------
    # A welded position pair; its length is the same however many faces meet.
    pos = {}
    for i, w in enumerate(widx):
        pos.setdefault(w, verts[i])
    line_m = 0.0
    for (u, v), faces in edge_faces.items():
        pu, pv = pos[u], pos[v]
        ln = math.dist(pu, pv)
        if len(faces) == 1:
            visible = True                     # an open boundary is a silhouette
        else:
            worst = 1.0
            for i in range(len(faces)):
                for j in range(i + 1, len(faces)):
                    n0, n1 = normals[faces[i]], normals[faces[j]]
                    worst = min(worst, n0[0] * n1[0] + n0[1] * n1[1]
                                + n0[2] * n1[2])
            visible = worst < cos_crease
        if not visible:
            continue
        if min_facet_m > 0.0 and any(
                facet_extent[facet_of[f]] < min_facet_m for f in faces):
            continue                            # finer than one screen pixel
        line_m += ln

    # --- diagnostics --------------------------------------------------------
    # Octave spread of feature size: the area-weighted standard deviation of
    # log2(facet extent), scaled so a distribution spread evenly over N octaves
    # reads N. A single feature size reads 0.
    if total > 0 and facet_area:
        mean = sum(a * math.log2(max(facet_extent[k], 1e-9))
                   for k, a in facet_area.items()) / total
        var = sum(a * (math.log2(max(facet_extent[k], 1e-9)) - mean) ** 2
                  for k, a in facet_area.items()) / total
        octaves = math.sqrt(12.0 * var)
    else:
        octaves = 0.0

    # Effective number of distinct facing directions, area-weighted, over a
    # 15-degree bucketing of the normal sphere. A box reads ~6 whatever its
    # tessellation; a lathe reads its segment count.
    buckets = {}
    for fi, n in enumerate(normals):
        k = (int(round(n[0] * 6)), int(round(n[1] * 6)), int(round(n[2] * 6)))
        buckets[k] = buckets.get(k, 0.0) + areas[fi]
    ent = 0.0
    for a in buckets.values():
        w = a / total
        if w > 0:
            ent -= w * math.log(w)
    n_normals = math.exp(ent)

    # Mean projected area over direction, exactly: 0.5 * sum A_i |n_i . u|,
    # averaged over a Fibonacci set of directions. For a closed convex body
    # this converges on Cauchy's S/4; for an open shell it does not, which is
    # why it is measured rather than assumed.
    proj = 0.0
    K = 32
    for i in range(K):
        z = 1.0 - 2.0 * (i + 0.5) / K
        rad = math.sqrt(max(0.0, 1.0 - z * z))
        phi = math.pi * (1.0 + 5.0 ** 0.5) * i
        u = (rad * math.cos(phi), rad * math.sin(phi), z)
        proj += 0.5 * sum(areas[j] * abs(normals[j][0] * u[0]
                                         + normals[j][1] * u[1]
                                         + normals[j][2] * u[2])
                          for j in range(len(tris)))
    proj /= K

    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    zs = [p[2] for p in verts]
    size = math.dist((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

    return dict(tris=len(tris), area=total, line_m=line_m,
                lam=line_m / total if total > 0 else 0.0,
                facets=len(facet_area), octaves=octaves, normals=n_normals,
                proj_ratio=(total / proj) if proj > 1e-12 else 4.0,
                size_m=size)


# ---------------------------------------------------------------------------
# The floor
# ---------------------------------------------------------------------------
def scene_budget(scene):
    """The triangle allotment for a location that is the subject of the shot.

    Read live from `budget.py` so the two files cannot drift. A location is
    allowed the scene's whole visible-set budget at the distance where it
    fills the frame, because at that distance it IS the visible set -- which
    is the same reading `budget.py` already takes when it prices a corridor
    against a 99 m sight line. Two locations are never both the subject, and
    `station/lod.py` is what makes that consistent with many instances.
    """
    import budget as B                                          # noqa: PLC0415
    return {"interior": B.INTERIOR["visible_set_tris"],
            "drum": B.DRUM["visible_set_tris"],
            "exterior": B.BUDGETS["exterior_triangles"]}[scene]


_SIGHT = [None]


def sight_line_m(schema, profile):
    """Worst-case interior sight line, computed the way `budget.py` computes it.

    A ring corridor is occluded by its own curvature at 2*sqrt(r_o^2 - r_i^2),
    and `budget.py` already takes the worst case over every deck-stack ring in
    every sector -- 99 m, at Grey's outermost ring. Recomputed here rather than
    copied, so a schema change moves both together.
    """
    if _SIGHT[0] is None:
        import interior_kit as ik                               # noqa: PLC0415
        _SIGHT[0] = max(
            it.sight_line(r["r_outer"], ik.PROVISIONAL["corridor_width_m"])
            for sec in schema["sectors"]["extents_m"]
            for r in it.ring_radii(schema, profile, sec)
            if r["kind"] == "deck_stack")
    return _SIGHT[0]


def visible_extent(schema, profile, place, scene):
    """(surface area, diagonal, height) of what a viewer has in front of them.

    WHY NOT THE MESH'S OWN AREA, for an interior. That was the first version
    and it is GAMEABLE, which the content proved within an hour: `plant.py`
    emits seven concentric bays and `quarters.py` seven classes, and
    concatenating them multiplied the area sevenfold, dropped the budget bound
    by sqrt(7), and turned a location sitting at 65% of its floor into one
    reported at 148%. An interior floor must not depend on how a generator
    chose to chunk its output.

    So it comes from the location's FOOTPRINT -- layer-1 data, asserted
    non-overlapping by `directory.collisions()` -- clipped in each axis to the
    sight line, because `budget.py`'s whole premise for interiors is that the
    cost that matters is what is visible at once.

    The drum and the exterior are not clipped, and their budget area is the
    whole assembly rather than a footprint (see `budget_area`). That is not an
    exception invented here; it is what `budget.py` already does. Of the drum:
    *"where everything is visible at once ... no occlusion -- there is no wall
    to hide behind"*. Of the exterior: one 400,000-triangle budget for the
    whole 8 km hull. The principle is the same in all three cases -- the area
    is whatever that scene's triangle budget has to cover simultaneously --
    and it lands on three different quantities because the scenes differ.
    """
    import rooms as R                                           # noqa: PLC0415
    arc, ln, _r = R.room_extent_m(schema, profile, place)
    h = R.ceiling_m(place)
    if scene == "interior":
        s = sight_line_m(schema, profile)
        arc, ln = min(arc, s), min(ln, s)
    area = 2.0 * arc * ln + 2.0 * (arc + ln) * h
    return area, composing_size(scene, arc, ln, h), h


def composing_size(scene, arc_m, len_m, height_m):
    """The extent that fills the frame when the location is the subject.

    THE FIRST VERSION USED THE FOOTPRINT DIAGONAL AND IT WAS WRONG, in a way
    worth recording because the error is invisible in the algebra and obvious
    the moment it is said out loud. A 400 m corridor's diagonal composes at
    390 m -- through four hundred metres of wall. Nobody ever sees that frame.
    You are INSIDE an interior, and what fills your view is its cross-section;
    the dimension that bounds the cross-section is the height. Backing away is
    not on offer in a room.

    So: inside (interior, drum) the composing extent is the HEIGHT. Outside
    (exterior) it is the smaller plan dimension of the footprint, which is the
    closest thing the register offers to the size of one fitting -- the
    register bands 28 cobra bays into one row and does not give their pitch.

    Getting this wrong moved the reference bound by a factor of forty and made
    it bind, which handed the exterior a PASS at 112% of a floor that said a
    line every 21 m was enough.
    """
    if scene == "exterior":
        return min(arc_m, len_m)
    return height_m


def budget_area(scene, vis_area_m2, mesh_area_m2):
    """The surface this scene's triangle budget has to cover at once.

    interior  -- the location's footprint out to the sight line. A wall stops
                 you seeing further, which is exactly the reasoning behind
                 `budget.py`'s "visible structure set".
    drum      -- the whole assembly. budget.py: "no occlusion -- there is no
                 wall to hide behind".
    exterior  -- the whole assembly. budget.py budgets one 400,000-triangle
                 figure for all 8 km of hull, because it is all in frame.
    """
    return vis_area_m2 if scene == "interior" else mesh_area_m2


def pixel_m(size_m, scene):
    """Metres per screen pixel when a thing of this size fills the frame."""
    fov = math.radians(SCENE_FOV_DEG[scene])
    d = size_m / (2.0 * math.tan(fov / 2.0))
    return d * (fov / SCREEN_H_PX), d


TRI_PER_CELL = 12.0        # a raised panel is a closed box: 6 quads, 12 tris


# Triangles actually available to one module, where the module declares a rule.
# `tram`: station/tram.py asserts six exterior cars stay under 5% of the drum's
# allotment, i.e. 15,000, and that is the whole tram in any drum frame.
MODULE_ALLOTMENT = {
    "tram": int(0.05 * 300_000),
}


def lam_of_plain_box(row):
    """Visible line density of a plain box with one location's dimensions.

    The null hypothesis, kept honest: twelve edges over six faces. If this ever
    clears a location's floor, that floor has stopped meaning anything.
    """
    a = max(row["area"], 1e-9)
    side = math.sqrt(a / 6.0)
    return (12.0 * side) / a


def lam_budget(tri_allot, area_m2):
    """Bound 1. Line density a grid of raised panels at this cost lays down.

    Strictly `2 / budget_pitch(tri_allot, area_m2)`, and written that way so the
    two cannot drift. They did drift once: 10 triangles per cell here against 12
    there, which put every floor 9% high.
    """
    if area_m2 <= 0:
        return 0.0
    return 2.0 / budget_pitch(tri_allot, area_m2)


def lam_nyquist(p_m):
    """Bound 2. Two samples per feature is the finest that exists on screen."""
    return 1.0 / p_m if p_m > 0 else float("inf")


def lam_reference(f_edge, proj_ratio, p_m):
    """Bound 3. The show's edge-pixel fraction, converted at our pixel size.

    `f_edge` is DIMENSIONLESS -- the fraction of screen pixels lying on a line
    -- which is what makes it comparable at all: "a frame of ours should carry
    as much line-work as a frame of theirs" needs no assumption about how detail
    scales with distance.

    The conversion. `proj_ratio` is total surface over mean projected area,
    which `analyse` measures and which comes out 4.00 for every mesh in this
    project because they are closed (Cauchy). The surface a viewer can actually
    see is half the total, so the visible surface behind one pixel of projected
    area is `proj_ratio / 2` times that pixel's worth -- the foreshortening
    factor, 2 for a closed body. Line length under one pixel is then
    `lambda * (proj_ratio / 2) * p^2`, which is `lambda * (proj_ratio/2) * p`
    pixels of line. Setting that equal to `f_edge`:

        lambda_ref = 2 * f_edge / (proj_ratio * p)

    The first draft of this returned `f_edge * proj_ratio / p` -- eight times
    too large, from dropping the foreshortening factor and inverting the ratio.
    It made bound 3 bind almost everywhere and gave the corridor kit a
    reference bound of 3.65 /m when the frame it was measured from carries
    5.6 /m at its own scale. Sanity-checking the operator against its own
    source frame is what caught it.
    """
    if p_m <= 0 or proj_ratio <= 0:
        return float("inf")
    return 2.0 * f_edge / (proj_ratio * p_m)


# ---------------------------------------------------------------------------
# Reference measurement -- the same operator we point at our own frames
# ---------------------------------------------------------------------------
def _gauss(img, sigma):
    import numpy as np                                          # noqa: PLC0415
    r = max(1, int(3 * sigma))
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * sigma * sigma))
    k /= k.sum()
    o = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, img)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, o)


def edge_fraction(path, sigma=1.2, hi=None, lo=None):
    """Fraction of pixels on a visible line, at an ABSOLUTE contrast threshold.

    Percentile thresholds were the obvious first draft and are worthless here:
    thresholding at the 90th percentile makes the answer 10% by construction,
    whatever the picture contains. So the thresholds are luminance STEP heights.
    A step of amplitude A blurred by sigma has peak gradient A/(sigma*sqrt(2pi)),
    so gradient magnitude is converted back to step height exactly rather than
    tuned.
    """
    import numpy as np                                          # noqa: PLC0415
    from PIL import Image                                       # noqa: PLC0415
    hi = WEBER_HI if hi is None else hi
    lo = WEBER_LO if lo is None else lo
    a = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255.0
    lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
    g = _gauss(lum, sigma)
    gy, gx = np.gradient(g)
    mag = np.hypot(gx, gy) * (sigma * math.sqrt(2 * math.pi))
    ang = np.arctan2(gy, gx)
    sec = (np.round(ang / (math.pi / 4)) % 4).astype(int)
    m = np.zeros_like(mag)
    shifts = {0: ((0, 1), (0, -1)), 1: ((1, 1), (-1, -1)),
              2: ((1, 0), (-1, 0)), 3: ((1, -1), (-1, 1))}
    for s, (p, q) in shifts.items():
        n1 = np.roll(np.roll(mag, p[0], 0), p[1], 1)
        n2 = np.roll(np.roll(mag, q[0], 0), q[1], 1)
        keep = (sec == s) & (mag >= n1) & (mag >= n2)
        m[keep] = mag[keep]
    strong = m >= hi
    weak = (m >= lo) & ~strong
    out = strong.copy()
    for _ in range(12):
        grow = np.zeros_like(out)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                grow |= np.roll(np.roll(out, dy, 0), dx, 1)
        new = weak & grow & ~out
        if not new.any():
            break
        out |= new
    out[:2, :] = out[-2:, :] = out[:, :2] = out[:, -2:] = False
    return float(out.mean())


_REF_CACHE = None


def measure_reference():
    """{scene: (f_edge, lambda at the frame's own scale, [rows])}."""
    global _REF_CACHE
    if _REF_CACHE is not None:
        return _REF_CACHE
    per = {}
    for rel, fig_px, stature, what, scene in REFERENCE:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        f = edge_fraction(path)
        mpp = stature / fig_px
        per.setdefault(scene, []).append(
            dict(path=rel, f_edge=f, m_per_px=mpp, lam=f / mpp, what=what))
    out = {}
    for scene, rows in per.items():
        out[scene] = (min(r["f_edge"] for r in rows), rows)
    # The exterior has no scale-anchored frame in the reference set: every hull
    # frame is an orthographic sheet or a distant plate with no figure in it, so
    # there is nothing to convert pixels to metres with. Rather than invent one,
    # the exterior inherits the LOWEST measured interior/drum fraction, which is
    # the most conservative available choice and is declared as such.
    if out:
        out.setdefault("exterior",
                       (min(v[0] for v in out.values()), []))
    _REF_CACHE = out
    return out


# ---------------------------------------------------------------------------
# Enumerating the 118
# ---------------------------------------------------------------------------
def _obj_mesh(mod_name):
    """(verts, tris) out of a module that only offers write_obj(path)."""
    def build(_schema, _profile):
        import contextlib                                       # noqa: PLC0415
        import importlib                                        # noqa: PLC0415
        import io                                               # noqa: PLC0415
        import tempfile                                         # noqa: PLC0415
        mod = importlib.import_module(mod_name)
        fd, path = tempfile.mkstemp(suffix=".obj")
        os.close(fd)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mod.write_obj(path)
            v, t = [], []
            with open(path) as f:
                for ln in f:
                    if ln.startswith("v "):
                        v.append(tuple(float(x) for x in ln.split()[1:4]))
                    elif ln.startswith("f "):
                        idx = [int(w.split("/")[0]) - 1 for w in ln.split()[1:]]
                        for k in range(1, len(idx) - 1):
                            t.append((idx[0], idx[k], idx[k + 1]))
            return v, t
        finally:
            os.unlink(path)
    return build


def _cat(parts):
    """Concatenate several (v, t) meshes into one."""
    V, T = [], []
    for v, t in parts:
        off = len(V)
        V.extend(v)
        T.extend((a + off, b + off, c + off) for a, b, c in t)
    return V, T


def _m_alien(s, p):
    import alien_sector                                         # noqa: PLC0415
    v, t, _g = alien_sector.gallery(s, p)
    return v, t


def _m_hospitality(_s, _p):
    import hospitality                                          # noqa: PLC0415
    v, t, _g = hospitality.room()
    return v, t


def _m_quarters(s, p):
    import quarters                                             # noqa: PLC0415
    return _cat([quarters.run(s, p, c["key"])[:2] for c in quarters.CLASSES])


def _m_plant(s, p):
    import plant                                                # noqa: PLC0415
    return _cat([plant.plant_bay(s, p, b, 10.0)[:2] for b in plant.bays(s, p)])


def _m_zocalo(_s, _p):
    import zocalo                                               # noqa: PLC0415
    r = zocalo.zocalo_run(3, cap_ends=True)
    return r[0], r[1]


def _m_customs(s, p):
    import customs                                              # noqa: PLC0415
    v, t, _g = customs.hall(s, p)
    return v, t


def _m_interior_kit(_s, _p):
    import interior_kit as kit                                  # noqa: PLC0415
    kit.reset_tags()
    return _cat([kit.corridor_section(21.6),
                 kit.corridor_junction_section(6.0)])


def _m_core_tube(s, p):
    import core_tube as ct                                      # noqa: PLC0415
    sec = it.drum_sector(s, p)
    parts = [ct.core_tube(s, p, sec)[:2], ct.spoke_node(s, p, sec)[:2]]
    parts += [ct.core_hub(s, p, sec, end=e)[:2] for e in ("fore", "aft")]
    return _cat(parts)


def _m_tram(_s, _p):
    import tram                                                 # noqa: PLC0415
    v, t, _meta = tram.tram_car(interior=True, glazed=True)
    return v, t


def _m_garden(s, p):
    import garden                                               # noqa: PLC0415
    v, t, _g = garden.townscape(s, p)
    return v, t


def _m_interior(s, p):
    sec = it.drum_sector(s, p)
    parts = [it.drum_interior(s, p, sec, arc_deg=360.0, seg_deg=2.0,
                              z_step=40.0)[:2],
             it.drum_spokes(s, p, sec)[:2],
             it.drum_guideways(s, p, sec)[:2]]
    parts += [it.drum_end_cap(s, p, sec, e)[:2] for e in ("fore", "aft")]
    return _cat(parts)


def _m_components(s, p):
    import components                                           # noqa: PLC0415
    return _cat(list(components.build_all(s.get("components", []), p).values()))


MODULE_MESH = {
    "command_control": _obj_mesh("command_control"),
    "council_chamber": _obj_mesh("council_chamber"),
    "docking_bay": _obj_mesh("docking_bay"),
    "signage": _obj_mesh("signage"),
    "alien_sector": _m_alien,
    "hospitality": _m_hospitality,
    "quarters": _m_quarters,
    "plant": _m_plant,
    "zocalo": _m_zocalo,
    "customs": _m_customs,
    "interior_kit": _m_interior_kit,
    "core_tube": _m_core_tube,
    "tram": _m_tram,
    "garden": _m_garden,
    "interior": _m_interior,
    "components": _m_components,
}


def scene_of(module):
    """Which render scene a module's geometry lives in.

    Imported from `test_materials_layer3.BESPOKE_SCENE` rather than restated,
    for the same reason `garden.settlement_arcs()` reads `interior.LAND_USE`:
    a second copy drifts the day someone retunes the first.
    """
    import test_materials_layer3 as gate                        # noqa: PLC0415
    return gate.BESPOKE_SCENE.get(module, "interior")


_MESH_CACHE = {}
_ANALYSIS_CACHE = {}


def module_mesh(schema, profile, module):
    """(verts, tris) for one bespoke module's whole emission, or an error dict.

    Cached, and the caching is not an optimisation detail: 50 of the 118 places
    are bespoke and 9 of them share `components`, so without it the exporter
    for the hull fittings would run nine times and the whole report would take
    the better part of an hour.
    """
    if module in _MESH_CACHE:
        return _MESH_CACHE[module]
    build = MODULE_MESH.get(module)
    if build is None:
        _MESH_CACHE[module] = {"error": "no mesh builder"}
        return _MESH_CACHE[module]
    try:
        _MESH_CACHE[module] = build(schema, profile)
    except Exception as exc:                                    # noqa: BLE001
        _MESH_CACHE[module] = {"error": f"{type(exc).__name__}: {exc}"}
    return _MESH_CACHE[module]


def score(schema, profile, place):
    """The full measurement and verdict for one of the 118 locations.

    GRANULARITY, stated because it is a real limitation. The 68 procedural
    places are measured on their OWN geometry, because `rooms.build` emits per
    place. The 50 bespoke places are measured on their MODULE's geometry: a
    module is one generator emitting one set of surfaces and there is no
    per-place subdivision of it to measure. That is the same granularity
    `directory._materialled_keys` already uses for layers 3 and 4, so the
    numbers line up with the register rather than inventing a second one.
    """
    import rooms as R                                           # noqa: PLC0415
    module = place["module"]
    scene = scene_of(module) if module else "interior"
    gran = "module" if module else "place"
    if module is None:
        mesh = R.build(schema, profile, place)[:2]
    else:
        mesh = module_mesh(schema, profile, module)
    if isinstance(mesh, dict):
        return dict(key=place["key"], name=place["name"], module=module,
                    scene=scene, granularity=gran, error=mesh["error"])

    vis_area, size, ceil = visible_extent(schema, profile, place, scene)
    p_m, d_m = pixel_m(size, scene)
    # Measured WITH the screen filter: lines between facets finer than one
    # pixel at the composing distance are the normal map's job, not the mesh's.
    ck = (module or place["key"], round(p_m, 9))
    if ck not in _ANALYSIS_CACHE:
        _ANALYSIS_CACHE[ck] = analyse(mesh[0], mesh[1], min_facet_m=p_m)
    m = _ANALYSIS_CACHE[ck]

    # A MODULE'S OWN ALLOWANCE BEATS THE SCENE'S, and the tram is why. The
    # budget bound asks "what line density can this triangle allotment buy over
    # this area", and `scene_budget` hands every module the WHOLE scene's
    # allotment as though it were the only thing in it. For a module that is
    # most of its scene -- `interior` is 6.1 of the drum's 6.2 million m2 --
    # that is close enough to true. For a small one it is badly wrong: the tram
    # is 10,892 m2 and gets handed all 300,000 drum triangles, giving a floor of
    # 3.03, while `station/tram.py`'s own cost rule allows it 15,000 triangles,
    # which buy 0.68. The metric was demanding four and a half times what the
    # budget it cites will fund.
    #
    # The entries here are READ FROM THE MODULE THAT OWNS THE RULE, not chosen.
    # A module with no entry falls back to the scene allotment, which is the
    # old behaviour and a known over-estimate for anything small.
    allot = MODULE_ALLOTMENT.get(module or "", scene_budget(scene))
    b_area = budget_area(scene, vis_area, m["area"])
    b1 = lam_budget(allot, b_area)
    b2 = lam_nyquist(p_m)
    ref = measure_reference().get(scene)
    b3 = lam_reference(ref[0], m["proj_ratio"], p_m) if ref else float("inf")
    floor = min(b1, b2, b3)
    binds = {b1: "budget", b2: "nyquist", b3: "reference"}[floor]

    return dict(key=place["key"], name=place["name"], module=module,
                scene=scene, granularity=gran,
                tris=m["tris"], area=m["area"], vis_area=vis_area,
                budget_area=b_area, line_m=m["line_m"],
                lam=m["lam"], facets=m["facets"], octaves=m["octaves"],
                normals=m["normals"], proj_ratio=m["proj_ratio"],
                size_m=size, d_m=d_m, p_m=p_m, ceiling_m=ceil,
                tri_per_m2=m["tris"] / m["area"] if m["area"] else 0.0,
                allot=allot, lam_budget=b1, lam_nyquist=b2, lam_ref=b3,
                floor=floor, binds=binds,
                gdi=(m["lam"] / floor) if floor > 0 else float("inf"),
                fidelity=(m["lam"] / b3) if b3 > 0 else float("inf"),
                passes=m["lam"] >= floor)


def report(schema=None, profile=None):
    """Every one of the 118, measured. Returns the rows."""
    import directory as D                                       # noqa: PLC0415
    if schema is None:
        schema, profile = it.load()
    return [score(schema, profile, q) for q in D.PLACES]


# ---------------------------------------------------------------------------
# Probes: shapes whose answer is known before the code runs
# ---------------------------------------------------------------------------
def _box_mesh(lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t = []
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(a, b, c), (a, c, d)]
    return v, t


def _subdivided_box(lo, hi, n):
    """The cheat this gate exists to be immune to: the same box, n*n per face.

    Coplanar splits, welded, so every interior edge has a dihedral of zero.
    Triangle count goes up by n^2 and there is nothing new to look at.
    """
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    V, T = [], []

    def face(o, du, dv):
        base = len(V)
        for i in range(n + 1):
            for j in range(n + 1):
                V.append(tuple(o[k] + du[k] * i / n + dv[k] * j / n
                               for k in range(3)))
        for i in range(n):
            for j in range(n):
                a = base + i * (n + 1) + j
                b = a + 1
                c = a + (n + 1) + 1
                d = a + (n + 1)
                T.extend([(a, b, c), (a, c, d)])
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    face((x0, y0, z0), (dx, 0, 0), (0, dy, 0))
    face((x0, y0, z1), (0, dy, 0), (dx, 0, 0))
    face((x0, y0, z0), (0, dy, 0), (0, 0, dz))
    face((x1, y0, z0), (0, 0, dz), (0, dy, 0))
    face((x0, y0, z0), (0, 0, dz), (dx, 0, 0))
    face((x0, y1, z0), (dx, 0, 0), (0, 0, dz))
    return V, T


def _cylinder(r, h, seg, cap=True):
    """A lathe. Tessellating a curve is the second obvious way to game a
    triangle count, and the ceiling it can reach is 1/(r*tau_min)."""
    V, T = [], []
    for k in range(seg):
        a = math.tau * k / seg
        V += [(r * math.cos(a), 0.0, r * math.sin(a)),
              (r * math.cos(a), h, r * math.sin(a))]
    for k in range(seg):
        a0, b0 = 2 * k, 2 * ((k + 1) % seg)
        T += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    if cap:
        lo, hi = len(V), len(V) + 1
        V += [(0.0, 0.0, 0.0), (0.0, h, 0.0)]
        for k in range(seg):
            a0, b0 = 2 * k, 2 * ((k + 1) % seg)
            T += [(lo, b0, a0), (hi, a0 + 1, b0 + 1)]
    return V, T


def _relief_box(lo, hi, pitch, depth):
    """A box whose SIX faces carry a grid of raised panels at `pitch`.

    This is the shape the budget bound is derived from, so it is the shape that
    proves the floor is reachable rather than aspirational: if this cannot pass
    on its own budget, the derivation is wrong.

    All six faces, and the first version panelled three. That version came out
    11% under the floor its own budget bound predicted, which reads as the
    derivation being wrong and was in fact three bald faces diluting the
    average -- exactly the defect the metric exists to catch, caught in the
    probe rather than in the content.
    """
    V, T = _box_mesh(lo, hi)
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = [max(1, int((x1 - x0) / pitch)), max(1, int((y1 - y0) / pitch)),
         max(1, int((z1 - z0) / pitch))]
    step = [(x1 - x0) / n[0], (y1 - y0) / n[1], (z1 - z0) / n[2]]
    g = pitch * 0.18                                   # reveal between panels
    lo3, hi3 = list(lo), list(hi)

    def panel(axis, outward):
        """Panels over the face normal to `axis`, raised `depth` outward."""
        u, w = [k for k in (0, 1, 2) if k != axis]
        for i in range(n[u]):
            for j in range(n[w]):
                a, b = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
                a[u] = lo3[u] + i * step[u] + g
                b[u] = lo3[u] + (i + 1) * step[u] - g
                a[w] = lo3[w] + j * step[w] + g
                b[w] = lo3[w] + (j + 1) * step[w] - g
                if outward:
                    a[axis], b[axis] = hi3[axis], hi3[axis] + depth
                else:
                    a[axis], b[axis] = lo3[axis] - depth, lo3[axis]
                v, t = _box_mesh(tuple(a), tuple(b))
                off = len(V)
                V.extend(v)
                T.extend((p + off, q + off, r + off) for p, q, r in t)

    for axis in (0, 1, 2):
        panel(axis, True)
        panel(axis, False)
    return V, T


def budget_pitch(tri_allot, area_m2):
    """Feature pitch a triangle allotment buys over a flat area.

    Twelve triangles per raised panel (a closed box), which is what the
    self-test's `_relief_box` actually costs, so the probe and the bound are
    priced with the same construction rather than one being an idealisation of
    the other.
    """
    if tri_allot <= 0 or area_m2 <= 0:
        return float("inf")
    return math.sqrt(TRI_PER_CELL * area_m2 / tri_allot)


# ---------------------------------------------------------------------------
# Self-test. Every check here has a demonstration that it can fail.
# ---------------------------------------------------------------------------
def _selftest(verbose=True):
    ok = fail = 0
    prove = []

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    def probe(name, cond, detail=""):
        """A check that the check above it can fire."""
        prove.append((name, bool(cond), detail))
        check(f"[probe] {name}", cond, detail)

    # --- the crease threshold is derived, not typed -----------------------
    # Written against the CONSTANTS rather than against 45.0, because the
    # project's own mutation sweep perturbed SHADE_INCIDENCE_DEG by 25% and
    # nothing noticed: the first draft of this line had the 45 inlined, so it
    # asserted the arithmetic and not the model.
    check("a crease at the threshold draws exactly a 4% luminance step",
          abs(math.sin(math.radians(SHADE_INCIDENCE_DEG))
              * math.radians(CREASE_DEG) - WEBER_HI) < 1e-12,
          f"{CREASE_DEG:.3f} deg at {SHADE_INCIDENCE_DEG:.1f} deg incidence "
          f"-> {math.sin(math.radians(SHADE_INCIDENCE_DEG)) * math.radians(CREASE_DEG):.5f}"
          f" against WEBER_HI {WEBER_HI}")
    check("and it is small enough to be a perceptual threshold, not a taste",
          1.0 < CREASE_DEG < 10.0, f"{CREASE_DEG:.2f} deg")

    # --- the screen model, pinned to a consequence ------------------------
    # SCREEN_H_PX and the FOV table only reach a verdict through bounds 2 and 3,
    # which never bind, so the mutation sweep reported the resolution as
    # UNGUARDED. It is not cosmetic -- it is what "one pixel" means -- so it is
    # pinned to the number it produces: one pixel, at conversational distance in
    # a standard 2.9 m room, is 1.86 mm of wall. At 1800p it is 1.49 mm and this
    # fires.
    p_room = pixel_m(2.9, "interior")[0] * 1000.0
    check("one screen pixel in a standard room is 1.86 mm of wall",
          1.80 < p_room < 1.92,
          f"{p_room:.3f} mm at {SCREEN_H_PX}p and "
          f"{SCENE_FOV_DEG['interior']:.0f} deg")

    # --- 1. SUBDIVISION MUST NOT MOVE THE NUMBER --------------------------
    bv, bt = _box_mesh((0, 0, 0), (10, 3, 10))
    plain = analyse(bv, bt)
    sv, st = _subdivided_box((0, 0, 0), (10, 3, 10), 8)
    subd = analyse(sv, st)
    check("a box and the same box subdivided have the same surface area",
          abs(plain["area"] - subd["area"]) < 1e-6,
          f"{plain['area']:.3f} vs {subd['area']:.3f}")
    check("subdividing a box multiplies its triangles",
          subd["tris"] >= 60 * plain["tris"],
          f"{plain['tris']} -> {subd['tris']}")
    check("and moves its line density by nothing",
          abs(plain["lam"] - subd["lam"]) < 1e-9,
          f"{plain['lam']:.6f} vs {subd['lam']:.6f} /m")
    probe("the line measure CAN move -- relief moves it",
          analyse(*_relief_box((0, 0, 0), (10, 3, 10), 0.5, 0.06))["lam"]
          > 8 * plain["lam"],
          f"relief {analyse(*_relief_box((0, 0, 0), (10, 3, 10), 0.5, 0.06))['lam']:.3f}"
          f" vs box {plain['lam']:.3f} /m")

    # --- 2. WELDING, WITHOUT WHICH NOTHING BELOW MEANS ANYTHING -----------
    # Unwelded, every triangle is an island: 3 boundary edges each, and the
    # measure reports a flat cube as the most detailed object in the project.
    unwelded_v = [bv[i] for tri in bt for i in tri]
    unwelded_t = [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(bt))]
    unw = analyse(unwelded_v, unwelded_t, crease_deg=CREASE_DEG)
    check("welding is what makes a shared edge shared",
          abs(plain["lam"] - unw["lam"]) < 1e-9,
          f"welded {plain['lam']:.4f} vs re-welded copy {unw['lam']:.4f}")
    probe("and the weld really merges and really separates",
          _weld([(0.0, 0.0, 0.0), (1e-9, 0.0, 0.0)])[1] == 1
          and _weld([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])[1] == 2)
    # WELD_M was reported UNGUARDED by the mutation sweep, and it is genuinely
    # tolerance-insensitive: the smallest standoff in the content is 6 cm
    # (`garden.py`'s window bands) and coordinates are float64, so anything from
    # a micron to a centimetre gives byte-identical answers. That insensitivity
    # is ASSERTED rather than assumed, together with the point where it stops
    # being true -- a tolerance of half a metre collapses the box.
    saved_weld = globals()["WELD_M"]
    try:
        lams = []
        for w in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2):
            globals()["WELD_M"] = w
            lams.append(analyse(bv, bt)["lam"])
        globals()["WELD_M"] = 6.0
        collapsed = analyse(bv, bt)["lam"]
    finally:
        globals()["WELD_M"] = saved_weld
    check("the weld tolerance is insensitive across four orders of magnitude",
          max(lams) - min(lams) < 1e-12,
          f"{min(lams):.6f}..{max(lams):.6f} /m over 1 um to 1 cm")
    probe("and it does bite once it exceeds the size of a feature",
          abs(collapsed - plain["lam"]) > 1e-6,
          f"at 6 m -- past the 3 m box's own thickness -- it reads "
          f"{collapsed:.4f} instead of {plain['lam']:.4f} /m")

    # --- 3. TESSELLATING A CURVE CANNOT REACH THE FLOOR -------------------
    # A lathe of radius r at turn angle tau lays down one line per r*tau of
    # surface, so lambda <= 1/(r*tau). Below the crease threshold it lays down
    # none at all -- the only lines left are the two rims where the wall meets
    # its caps, which are real features and are supposed to count.
    fine = analyse(*_cylinder(5.0, 4.0, 720))       # 0.5 deg segments
    coarse = analyse(*_cylinder(5.0, 4.0, 24))      # 15 deg segments
    rim = 2 * math.tau * 5.0
    check("a finely tessellated cylinder draws nothing but its two rims",
          abs(fine["line_m"] - rim) < 0.05 * rim,
          f"{fine['line_m']:.1f} m of line against {rim:.1f} m of rim, "
          f"over {fine['tris']:,} triangles")
    check("a coarse one also draws its segment boundaries",
          coarse["line_m"] > 1.5 * rim,
          f"{coarse['line_m']:.1f} m vs {fine['line_m']:.1f} m")
    tau_min = math.radians(CREASE_DEG)
    check("and no lathe can beat the 1/(r*tau) ceiling its geometry allows",
          (coarse["line_m"] - rim) / coarse["area"]
          <= 1.0 / (5.0 * tau_min) + 1e-6,
          f"{(coarse['line_m'] - rim) / coarse['area']:.4f} <= "
          f"{1.0 / (5.0 * tau_min):.4f} /m")
    probe("the lathe ceiling really is below a room's floor",
          1.0 / (5.0 * tau_min) < lam_budget(60_000, coarse["area"]),
          f"ceiling {1.0 / (5.0 * tau_min):.2f} vs floor "
          f"{lam_budget(60_000, coarse['area']):.2f} /m")

    # --- 4. THE ONE-PIXEL FILTER ------------------------------------------
    # Greeble finer than a screen pixel must not count. Same box, same relief,
    # measured with and without a viewing model.
    gv, gt = _relief_box((0, 0, 0), (10, 3, 10), 0.05, 0.01)
    raw = analyse(gv, gt, min_facet_m=0.0)
    filt = analyse(gv, gt, min_facet_m=0.5)
    check("sub-pixel greeble is counted when there is no viewing model",
          raw["lam"] > 20.0, f"{raw['lam']:.2f} /m")
    check("and is thrown away when there is one",
          filt["lam"] < 0.2 * raw["lam"],
          f"{filt['lam']:.2f} vs {raw['lam']:.2f} /m")
    probe("the filter is not simply discarding everything",
          analyse(*_relief_box((0, 0, 0), (10, 3, 10), 2.0, 0.3),
                  min_facet_m=0.5)["lam"] > 1.5 * plain["lam"],
          f"{analyse(*_relief_box((0, 0, 0), (10, 3, 10), 2.0, 0.3), min_facet_m=0.5)['lam']:.3f} /m")

    # --- 5. THE FLOOR IS REACHABLE ----------------------------------------
    # If nothing can pass, the gate is a wall rather than a bar. Build the very
    # shape the budget bound is priced from, at the pitch that allotment buys,
    # and require it to clear the floor ON ITS OWN BUDGET.
    room_area = plain["area"]
    pitch = budget_pitch(60_000, room_area)
    rv, rt = _relief_box((0, 0, 0), (10, 3, 10), pitch, 0.05)
    rich = analyse(rv, rt, min_facet_m=0.0)
    floor = lam_budget(60_000, rich["area"])
    check("a surface built at the pitch its allotment buys clears the floor",
          rich["lam"] >= floor,
          f"{rich['lam']:.2f} /m against a floor of {floor:.2f} at "
          f"pitch {pitch * 100:.0f} cm")
    check("and does it inside the triangle allotment it was priced against",
          rich["tris"] <= 60_000,
          f"{rich['tris']:,} of 60,000")
    check("the plain box does NOT clear it -- this is the gate failing on "
          "blockout", plain["lam"] < lam_budget(60_000, plain["area"]),
          f"{plain['lam']:.3f} /m against "
          f"{lam_budget(60_000, plain['area']):.2f}")
    check("nor does the subdivided box, at 64x the triangles",
          subd["lam"] < lam_budget(60_000, subd["area"]),
          f"{subd['lam']:.3f} /m, {subd['tris']:,} tri")

    # --- 6. THE BOUNDS ARE FUNCTIONS, NOT CONSTANTS -----------------------
    check("the budget bound and the pitch it implies are one equation",
          abs(lam_budget(60_000, 320.0)
              - 2.0 / budget_pitch(60_000, 320.0)) < 1e-12
          and abs(lam_budget(60_000, 320.0)
                  - 2.0 * math.sqrt(60_000 / (TRI_PER_CELL * 320.0))) < 1e-12,
          f"{lam_budget(60_000, 320.0):.6f} /m at pitch "
          f"{budget_pitch(60_000, 320.0) * 100:.2f} cm, "
          f"{TRI_PER_CELL:.0f} triangles a cell")
    check("the budget bound falls as a location gets bigger",
          lam_budget(60_000, 1000.0) < lam_budget(60_000, 100.0))
    check("the budget bound rises with the allotment",
          lam_budget(300_000, 500.0) > lam_budget(60_000, 500.0))
    p_small, d_small = pixel_m(10.0, "interior")
    p_big, d_big = pixel_m(1000.0, "interior")
    check("a bigger location is composed from further away",
          d_big > d_small, f"{d_small:.1f} m vs {d_big:.1f} m")
    check("so its pixel covers more ground and its nyquist bound is lower",
          lam_nyquist(p_big) < lam_nyquist(p_small),
          f"{lam_nyquist(p_big):.3f} vs {lam_nyquist(p_small):.1f} /m")
    # f / (2 tan(f/2)) shrinks as f grows, so a NARROWER lens has to stand
    # further back than the extra reach of its longer focal length buys, and
    # its pixel lands on more metres. Getting this backwards was worth a
    # failing assertion: the first draft asserted the opposite.
    check("a narrower lens composes from far enough back to cost resolution",
          pixel_m(10.0, "exterior")[0] > pixel_m(10.0, "interior")[0],
          f"46 deg {pixel_m(10.0, 'exterior')[0] * 1000:.2f} mm/px vs "
          f"55 deg {pixel_m(10.0, 'interior')[0] * 1000:.2f} mm/px")

    # --- 6b. THE FLOOR MUST NOT DEPEND ON HOW A BUILDER CHUNKS ITS OUTPUT --
    # The defect this guards against was live: `plant.py` emits seven bays and
    # `_m_plant` concatenated them, which multiplied the area sevenfold,
    # divided the budget bound by sqrt(7), and turned a location sitting at 65%
    # of its floor into one reported at 148% -- a false PASS produced by
    # nothing but the shape of a `for` loop.
    schema0, profile0 = it.load()
    import directory as D0                                      # noqa: PLC0415
    import plant as _plant                                      # noqa: PLC0415
    import rooms as R0                                          # noqa: PLC0415
    zone = D0.by_key("plant_zone")
    a1, s1, _h = visible_extent(schema0, profile0, zone, "interior")
    bays = _plant.bays(schema0, profile0)
    m1 = analyse(*_plant.plant_bay(schema0, profile0, bays[0], 10.0)[:2])
    m7 = analyse(*_cat([_plant.plant_bay(schema0, profile0, b, 10.0)[:2]
                        for b in bays]))
    check("concatenating seven bays multiplies the measured mesh area",
          m7["area"] > 6.0 * m1["area"],
          f"{m1['area']:,.0f} -> {m7['area']:,.0f} m2")
    probe("a mesh-area floor WOULD have moved -- which is why it is not used",
          lam_budget(60_000, m1["area"]) > 2.0 * lam_budget(60_000, m7["area"]),
          f"one bay {lam_budget(60_000, m1['area']):.3f} vs seven "
          f"{lam_budget(60_000, m7['area']):.3f} /m")
    check("an INTERIOR floor does not move with the mesh -- it uses the "
          "footprint", score(schema0, profile0, zone)["lam_budget"]
          == lam_budget(60_000, a1),
          f"{lam_budget(60_000, a1):.3f} /m from a {a1:,.0f} m2 extent")
    check("a DRUM floor does use the whole assembly, because nothing occludes it",
          budget_area("drum", 1.0, 5.0) == 5.0
          and budget_area("interior", 1.0, 5.0) == 1.0
          and budget_area("exterior", 1.0, 5.0) == 5.0)
    raw_arc, raw_len, _rr = R0.room_extent_m(schema0, profile0, zone)
    check("the sight line clips a location longer than a viewer can see",
          s1 < math.hypot(raw_arc, raw_len),
          f"{math.hypot(raw_arc, raw_len):.0f} m footprint -> {s1:.0f} m visible")
    check("and leaves a small location alone",
          visible_extent(schema0, profile0, D0.by_key("eclipse_cafe"),
                         "interior")[1] < sight_line_m(schema0, profile0),
          f"{visible_extent(schema0, profile0, D0.by_key('eclipse_cafe'), 'interior')[1]:.1f} m")
    the_garden = D0.by_key("the_garden")
    a_drum = visible_extent(schema0, profile0, the_garden, "drum")[0]
    a_int = visible_extent(schema0, profile0, the_garden, "interior")[0]
    check("the drum is NOT clipped -- budget.py says there is no wall there",
          a_drum > 10.0 * a_int,
          f"{a_drum:,.0f} m2 unclipped vs {a_int:,.0f} m2 if it were a corridor")

    # --- 6c. THE COMPOSING DISTANCE ---------------------------------------
    # Inside a room you cannot back away, so the frame is filled by the
    # cross-section, not by the length. The first version used the footprint
    # diagonal and composed a 400 m corridor from 390 m away -- through the
    # wall -- which moved the reference bound by 40x.
    tall = composing_size("interior", 400.0, 187.0, 3.4)
    check("an interior is composed from its cross-section, not its length",
          tall == 3.4, f"{tall} m")
    check("an exterior fitting is composed from its own plan size",
          composing_size("exterior", 1329.0, 120.0, 2.9) == 120.0)
    check("so a long corridor is judged at arm's length, not from the far end",
          pixel_m(composing_size("interior", 400.0, 187.0, 3.4),
                  "interior")[1] < 5.0,
          f"{pixel_m(3.4, 'interior')[1]:.2f} m composing distance")
    # And the reference conversion has to reproduce its own source frame. The
    # hallway plate is 7.29 mm/px at f_edge 0.0816, which is 5.6 /m; if the
    # conversion does not return that when handed that pixel size, it is wrong
    # -- and the first draft returned 45 /m.
    f_hall = 0.0816
    back = lam_reference(f_hall, 4.0, 1.80 / 247.0)
    check("the reference conversion reproduces the frame it was measured from",
          5.0 < back < 6.5,
          f"{back:.2f} /m -- a line every {100 / back:.0f} cm on a B5 set")

    # --- 7. THE REFERENCE MEASUREMENT -------------------------------------
    # It must be the SHOW that sets it, so the frames have to exist and the
    # operator has to distinguish a detailed set from a flat one.
    missing = [r[0] for r in REFERENCE
               if not os.path.exists(os.path.join(ROOT, r[0]))]
    check("every reference frame the floor cites exists", not missing,
          str(missing))
    try:
        ref = measure_reference()
        check("the reference measures a set as line-dense",
              all(v[0] > 0.03 for k, v in ref.items() if v[1]),
              str({k: round(v[0], 4) for k, v in ref.items()}))
        # The measurement bound 3 rests on, pinned to the value recorded in
        # INV-071 so a change to the operator's thresholds is visible rather
        # than silent. WEBER_LO was reported UNGUARDED by the mutation sweep;
        # raising it to 0.025 takes this to 0.0789 and this line fires.
        f_hallway = edge_fraction(os.path.join(ROOT, REFERENCE[0][0]))
        check("the hallway plate still measures the f_edge INV-071 records",
              0.0800 < f_hallway < 0.0832,
              f"{f_hallway:.5f} against 0.0816 at hi/lo "
              f"{WEBER_HI}/{WEBER_LO}")
        # The operator must be able to say "flat": a synthetic frame with one
        # step in it must come out near zero, or the reference number is an
        # artefact of the detector rather than of the show.
        import numpy as np                                      # noqa: PLC0415
        from PIL import Image                                   # noqa: PLC0415
        import tempfile                                         # noqa: PLC0415
        flat = np.zeros((400, 400, 3), np.uint8)
        flat[:, 200:] = 160
        fd, fp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        Image.fromarray(flat).save(fp)
        f_flat = edge_fraction(fp)
        os.unlink(fp)
        probe("the edge operator reports a nearly-blank frame as nearly blank",
              f_flat < 0.006, f"{f_flat:.5f} of pixels")
    except ImportError:
        check("numpy and PIL are available for the reference measurement",
              False, "install numpy/PIL")

    # --- 8. THE VERDICT MUST BE ABLE TO GO EITHER WAY ---------------------
    schema, profile = it.load()
    rows = [r for r in report(schema, profile) if "error" not in r]
    check("every one of the 118 places was measured",
          len(rows) == 118, f"{len(rows)} rows")
    check("no location is measured with zero surface area",
          all(r["area"] > 0 for r in rows),
          str([r["key"] for r in rows if r["area"] <= 0][:4]))
    check("every location's floor came from one of the three bounds",
          all(r["binds"] in ("budget", "nyquist", "reference") for r in rows))
    check("the floor is the smallest of the three bounds, always",
          all(abs(r["floor"] - min(r["lam_budget"], r["lam_nyquist"],
                                   r["lam_ref"])) < 1e-9 for r in rows))
    # THIS ASSERTION USED TO READ "THE GATE FAILS ON THE CONTENT AS IT STANDS",
    # and it was the right assertion for the session that wrote it: 102 of 118
    # locations were blockout, and the risk worth guarding against was a metric
    # that scored everything green on arrival. It has now done its job -- every
    # location was rebuilt against it and all 118 pass -- so the old form fails
    # for the one reason that is not a defect, and keeping it would mean holding
    # the content permanently broken to satisfy a test.
    #
    # What replaces it tests the property that actually matters and that does
    # NOT expire: the gate must still be able to say no. A plain box at each
    # location's own floor must fail, and the relief box below must pass. If
    # both hold, a green board means the content cleared a bar that still bites.
    plain_at_floor = [r for r in rows
                      if lam_of_plain_box(r) >= r["floor"] - 1e-9]
    check("a plain box would still fail at every location's floor -- the gate "
          "has not gone slack",
          not plain_at_floor,
          f"{len(plain_at_floor)} locations would accept a box: "
          f"{[r['key'] for r in plain_at_floor][:4]}")
    failing = [r for r in rows if not r["passes"]]
    # ... and would not fail on something detailed. Substitute the relief box
    # for a real location's mesh and re-run the verdict end to end.
    victim = rows[0]
    rel = analyse(*_relief_box((0, 0, 0), (10, 3, 10),
                               budget_pitch(victim["allot"], plain["area"]),
                               0.05),
                  min_facet_m=victim["p_m"])
    probe("a genuinely detailed mesh in the same slot PASSES",
          rel["lam"] >= victim["floor"],
          f"{rel['lam']:.2f} /m vs floor {victim['floor']:.2f} "
          f"(the real one is {victim['lam']:.2f})")

    if verbose:
        print(f"\n{ok}/{ok + fail} passed  "
              f"({sum(1 for _n, c, _d in prove if c)}/{len(prove)} probes fired)")
    return 1 if fail else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_report(rows):
    ref = measure_reference()
    print("\nGEOMETRIC DETAIL GATE -- visible line density against a derived floor\n")
    print(f"  screen        {SCREEN_H_PX}p, fov "
          + ", ".join(f"{k} {v:.0f} deg" for k, v in SCENE_FOV_DEG.items()))
    print(f"  crease        {CREASE_DEG:.2f} deg "
          f"(a {WEBER_HI:.0%} luminance step at {SHADE_INCIDENCE_DEG:.0f} deg incidence)")
    for scene, (f, rrows) in sorted(ref.items()):
        src = (", ".join(os.path.basename(r["path"]) for r in rrows)
               or "inherited, no scale-anchored hull frame exists")
        print(f"  reference     {scene:9s} f_edge {f:.4f}  [{src}]")
    print()
    hdr = (f"{'':4s}{'location':36s} {'scene':8s} {'tri':>7s} {'area m2':>10s} "
           f"{'lam':>7s} {'floor':>7s} {'binds':>9s} {'%bar':>6s} {'%show':>6s}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: (x.get("gdi", 0.0))):
        if "error" in r:
            print(f"ERR {r['name'][:36]:36s} {r['scene']:8s} {r['error']}")
            continue
        mark = "PASS" if r["passes"] else "FAIL"
        print(f"{mark:4s}{r['name'][:36]:36s} {r['scene']:8s} "
              f"{r['tris']:7,d} {r['area']:10,.0f} {r['lam']:7.3f} "
              f"{r['floor']:7.3f} {r['binds']:>9s} {r['gdi'] * 100:6.1f} "
              f"{r['fidelity'] * 100:6.1f}")
    good = [r for r in rows if r.get("passes")]
    print(f"\n{len(good)}/{len(rows)} locations at or above the floor")
    fid = [r["fidelity"] for r in rows if "error" not in r]
    print(f"%bar  = line density as a fraction of the DERIVED FLOOR "
          f"(the gate: >= 100)")
    print(f"%show = line density as a fraction of BOUND 3 alone, what a "
          f"Babylon 5 set carries.\n        Range "
          f"{min(fid) * 100:.1f}% to {max(fid) * 100:.1f}%, median "
          f"{sorted(fid)[len(fid) // 2] * 100:.1f}%. Nothing is gated on this "
          f"column -- it is\n        here because it says how conservative the "
          f"floor is: the floor binds on the\n        budget almost everywhere, "
          f"and the budget is far below the show.")
    worst = min((r for r in rows if "error" not in r),
                key=lambda x: x["gdi"], default=None)
    if worst:
        print(f"worst: {worst['name']} at {worst['gdi']:.4f} of its floor "
              f"({worst['lam']:.4f} against {worst['floor']:.3f} /m)")
    return len(rows) - len(good)


def _cli(argv):
    if "--selftest" in argv:
        return _selftest()
    schema, profile = it.load()
    rows = report(schema, profile)
    if "--json" in argv:
        print(json.dumps(rows, indent=1, sort_keys=True))
        return 0
    missing = _print_report(rows)
    if "--modules" in argv:
        print("\nby module\n")
        seen = set()
        for r in sorted(rows, key=lambda x: x.get("gdi", 0.0)):
            m = r.get("module") or "rooms"
            if m in seen or "error" in r:
                continue
            seen.add(m)
            print(f"  {m:18s} {r['tris']:8,d} tri  {r['area']:11,.0f} m2  "
                  f"lam {r['lam']:8.3f}  floor {r['floor']:7.3f}  "
                  f"{r['gdi'] * 100:6.1f}% of bar   octaves {r['octaves']:.2f}"
                  f"  normals {r['normals']:.1f}")
    print("\nThis gate is EXPECTED TO FAIL until the geometry is rebuilt. "
          "The floor is\nderived (budget / nyquist / reference, smallest wins) "
          "and must not be lowered\nto make it green -- see the module "
          "docstring and INV-070.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
