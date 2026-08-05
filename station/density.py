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
                    octaves=0.0, normals=0.0, facet_max_m=0.0,
                    facet_p50_m=0.0, proj_ratio=4.0, size_m=0.0)

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

    # HOW BIG IS THE BIGGEST UNBROKEN PIECE. `lam` says how much line-work a
    # surface carries; it does NOT say whether that line-work is spread over
    # the surface or bunched into a trim ladder with a flat field beside it. A
    # wall with a dense mullion run and one 4 m unbroken panel scores well on
    # `lam` and is exactly what `docs/engine-4a-office.png` shows. So the facet
    # sizes come out too -- see THE SHELL GATE at the foot of this file.
    #
    # SUBDIVISION CANNOT MOVE THESE EITHER, for the same reason it cannot move
    # `lam`: a coplanar split has a zero dihedral, so the two halves are unioned
    # back into one facet. The only way to shrink a facet is a real crease, and
    # a real crease is a reveal, a joint or a step -- construction, not
    # tessellation. `_selftest` asserts it against `_subdivided_box`.
    _fx = sorted(facet_extent.values())                     # small -> large
    facet_max = _fx[-1] if _fx else 0.0
    _acc, facet_p50 = 0.0, facet_max
    for k in sorted(facet_area, key=lambda q: facet_extent[q]):
        _acc += facet_area[k]
        if _acc >= 0.5 * total:
            facet_p50 = facet_extent[k]
            break

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
                facet_max_m=facet_max, facet_p50_m=facet_p50,
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


# The eye the drum is measured from. `export_scene.build_drum` resolves the
# ground's and the dressing's LOD against a standing eye, so a drum measurement
# has to name one; 205 deg at mid-length is the exporter's own default stand and
# is used here so the measured mesh is a mesh somebody has rendered.
DRUM_EYE = (205.0, 0.5)


def _drum_eye(s, p, sec):
    import drum_ground as dg                                    # noqa: PLC0415
    dg.configure(s, p, sec)
    ang, f = DRUM_EYE
    return dg.stand_on_ground(s, p, sec, ang, dg.Z0 + f * (dg.Z1 - dg.Z0))[0]


def _m_interior(s, p):
    """The drum as the EXPORTER emits it, not as this module used to imagine it.

    THIS MEASURED DISCARDED GEOMETRY, and an adversarial review caught it. The
    old version scored `it.drum_interior()`'s band shell -- and
    `export_scene.drum_parts` REPLACES that shell with
    `drum_ground.visible_set()`, because emitting both would z-fight across four
    and a half million square metres. Its own comment says so.

    So five gazetteer rows were certified COMPLETE on a mesh nobody renders:
    lambda 0.1320 measured (103.4%, PASS) against 0.1105 as actually rendered
    (86.3%, FAIL), with the ground alone at 30.4% of its floor. I found the
    substitution myself in session 3s, measured it at 0.09% of the frame, wrote
    it into STATE.md as "one caveat" -- and flipped the layer green anyway.
    A gate that scores something the player never sees is worse than no gate,
    because it prints PASS.

    AND THE FIX WAS APPLIED TO THIS FUNCTION INSTEAD OF TO THE RULE, so it
    started drifting the same day. Session 3s hand-copied the exporter's part
    list into the body below -- ground, spokes, guideways, two end caps -- and
    `drum_parts` has since grown FOUR MORE PARTS that this never learned about.
    Measured in 4q at the same eye:

        ground     94,592     <- both lists
        endcaps    15,072     <- both lists
        guideways  11,796     <- both lists
        spokes        516     <- both lists
        core       13,340     <- exporter only
        trams      12,624     <- exporter only
        townscape  51,026     <- exporter only, and it is `garden.py`'s output
        dressing   89,094     <- exporter only, and `DRUM_CALIBRATION` measures
                                 it at 39.08 / 32.30 / 47.26% of the PIXELS of
                                 the three drum framings

    121,976 measured against 288,060 rendered: the measurement saw 42.3% of the
    frame. CLAUDE.md's session-4h finding, word for word -- *"A fix applied to
    an instance and not to the rule is a fix that will be needed again."*

    So the list is no longer here. `tools/export_scene.py::drum_parts` is the
    one place the drum shot's contents are enumerated and its own docstring
    says why; this asks it. A part added to the drum is now measured by the
    fact of being added.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_scene as es                                   # noqa: PLC0415
    sec = it.drum_sector(s, p)
    eye = _drum_eye(s, p, sec)
    return _cat([(v, t) for _nm, v, t, _g in es.drum_parts(s, p, sec, eye)])


def _m_interior_legacy(s, p):
    """The pre-4q hand-copied list. THE CONTROL for `_m_interior`, kept live.

    Not dead code and not history: `_selftest` runs both and requires the new
    one to be strictly bigger, which is the only way to show that asking the
    exporter changed what is measured rather than merely where the list lives.
    Deleting it would leave the fix unfalsifiable.
    """
    import drum_ground as dg                                    # noqa: PLC0415
    sec = it.drum_sector(s, p)
    eye = _drum_eye(s, p, sec)
    gv, gt, _gg, _gm = dg.visible_set(eye)
    parts = [(gv, gt),
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
    # THE TWO REGISTRIES MUST AGREE ABOUT WHAT THE DRUM IS. This is the
    # structural fix for the defect above: it is not enough to point
    # `_m_interior` at the right mesh once, because nothing stopped it drifting
    # the first time. `export_scene.drum_parts` is the one list of what the drum
    # shot contains; if this module scores a part that list does not carry, or
    # misses one it does, the scores describe a station nobody renders.
    #
    # AND THE VERSION OF THIS CHECK THAT SHIPPED WAS ITSELF A THIRD COPY OF THE
    # LIST, ASSERTED WITH THE WRONG OPERATOR. It read:
    #
    #     _scored = {"ground", "spokes", "guideways", "endcap_fore",
    #                "endcap_aft"}
    #     check(..., _scored <= _shot, ...)
    #
    # A LITERAL SET, not derived from `_m_interior`, tested for SUBSET. Adding a
    # part to the drum shot leaves a subset relation true, so the one gate
    # written to stop `_m_interior` drifting could only ever fail if a part were
    # REMOVED -- and the exporter grew four (core, trams, townscape, dressing,
    # 181,832 triangles) while it printed PASS. It was also blind by
    # construction to any change in `_m_interior` itself, because it never asked
    # `_m_interior` anything.
    #
    # So the question is asked in TRIANGLES, of the function itself, with
    # equality: what this module scores IS what the shot contains, or it is not.
    # `_m_interior_legacy` is the control, and it has to come back short.
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import export_scene as _X                               # noqa: PLC0415
        _s, _p = it.load()
        _sec = it.drum_sector(_s, _p)
        _eye = _drum_eye(_s, _p, _sec)
        _parts = _X.drum_parts(_s, _p, _sec, _eye)
        _shot = {n for n, _v, _t, _g in _parts}
        _shot_tris = sum(len(t) for _n, _v, t, _g in _parts)
        _mine = module_mesh(_s, _p, "interior")
        check("the drum this module scores is the drum the exporter emits",
              not isinstance(_mine, dict) and len(_mine[1]) == _shot_tris,
              f"{'error' if isinstance(_mine, dict) else len(_mine[1]):,} "
              f"scored against {_shot_tris:,} in the shot "
              f"({', '.join(sorted(_shot))})")
        _old = _m_interior_legacy(_s, _p)
        probe("...and the pre-4q hand-copied list did NOT, which is the "
              "control for the line above",
              len(_old[1]) < _shot_tris,
              f"the old list scored {len(_old[1]):,} of {_shot_tris:,} -- "
              f"{100 * len(_old[1]) / _shot_tris:.1f}% of the frame, missing "
              f"{_shot_tris - len(_old[1]):,} triangles of core, trams, "
              f"townscape and dressing")
        check("...and the shell it used to score is NOT in the shot, which is "
              "why scoring it certified geometry nobody renders",
              "drum_interior" not in _shot and "shell" not in _shot)
    except Exception as _e:                                     # noqa: BLE001
        check("the drum registries can be compared at all", False, str(_e))

    # THE DENOMINATOR IS THE REGISTER'S, NOT A NUMBER WRITTEN HERE. This read
    # `== 118` and had been red since the gazetteer grew to 128 places, which
    # is a gate failing for the one reason that is not a defect -- and a gate
    # that is red for a stale reason is a gate nobody reads. `directory.PLACES`
    # is the register; asking it cannot go stale.
    import directory as _D                                      # noqa: PLC0415
    check("every place in the register was measured",
          len(rows) == len(_D.PLACES), f"{len(rows)} of {len(_D.PLACES)} rows")

    # --- THE MACHINERY GATE, INV-130, AND ITS NEGATIVE CONTROL ------------
    # The whole-location number above passes 123 of 128 with every machine in
    # the station a box, so this gate exists to measure the object rather than
    # the room. It has to be able to say no, and the control is exact: empty
    # `rooms.MACHINE_KIND` and `rooms.PROP_KIND` and every fixture and prop
    # falls back to the single `_box` it was before INV-130.
    import rooms as _R                                          # noqa: PLC0415
    probe_keys = ["fabrication", "reactor_hall", "medlab_one",
                  "business_center"]
    live = machinery_rows(schema, profile, keys=probe_keys)
    saved = _R.MACHINE_KIND, _R.PROP_KIND
    try:
        _R.MACHINE_KIND, _R.PROP_KIND = {}, {}
        boxed = machinery_rows(schema, profile, keys=probe_keys)
    finally:
        _R.MACHINE_KIND, _R.PROP_KIND = saved
    check("the machinery gate FAILS when every machine is a box",
          all(not r["passes"] for r in boxed),
          f"{sum(1 for r in boxed if r['passes'])} of {len(boxed)} still pass; "
          f"ratios {[round(r['ratio'], 2) for r in boxed]}")
    check("...and passes on the machines as shipped",
          all(r["passes"] for r in live),
          f"{[(r['key'], round(r['ratio'], 2)) for r in live if not r['passes']]}")
    lift = (sum(r["lam"] for r in live)
            / max(sum(r["lam"] for r in boxed), 1e-9))
    check("the articulated machines carry more line than the boxes did",
          lift > 2.0, f"{lift:.2f}x over {len(live)} locations")
    print(f"  machinery line density, articulated / boxed, over "
          f"{len(live)} locations: {lift:.2f}x")
    # --- THE SHELL GATE, INV-210, AND ITS NEGATIVE CONTROLS ---------------
    # The machinery gate above measures the objects in the room; this one
    # measures the room. Its control is exact in the same way `--no-apertures`
    # is for the hull: `rooms.articulate(plates=False)` rebuilds the whole
    # pre-INV-210 shell, and the first assertion here is that the rebuild IS
    # the old shell rather than an approximation of it.
    shell_keys = ["war_room", "cargo_bays", "fabrication", "transfer_systems"]
    kit_std = kit_surface_floor()
    live_s = shell_rows(schema, profile, keys=shell_keys)
    old_s = []
    for r in live_s:
        p = _D.by_key(r["key"])
        v, t, g = _R.build(schema, profile, p, plates=False)
        # THE REFERENCE FLOOR IS THE FLOOR THAT WAS BUILT. `min(room_extent_m,
        # bay_span_m)` was that until 4k tiled the bay along the footprint;
        # since then it is one bay of a room up to thirteen bays long, so the
        # comparison floor for a 140 m room was 10.77 m of it. `built_span_m`
        # is the one function that knows which reading applies.
        bw, bl = _R.built_span_m(schema, profile, p)
        same = kit_like_floor(bw, bl, _R.ceiling_m(p))
        surfs = {}
        for surf, tris in shell_split(v, t, g).items():
            a = analyse(v, tris, min_facet_m=0.0)
            surfs[surf] = {
                "lam_x": a["lam"] / same[surf]["lam"],
                "facet_x": same[surf]["facet_p50_m"] / a["facet_p50_m"],
                "facet_p50": a["facet_p50_m"],
            }
        old_s.append({"key": r["key"], "surfaces": surfs,
                      "passes": all(s["lam_x"] >= 1.0 and s["facet_x"] >= 1.0
                                    for s in surfs.values())})
    check("the shell gate FAILS on the pre-INV-210 shell",
          all(not r["passes"] for r in old_s),
          f"{sum(1 for r in old_s if r['passes'])} of {len(old_s)} still pass")
    check("...and it is the WALL and the DECK that fail there, which is what "
          "the frames show",
          all(not r["surfaces"]["wall"]["passes"] if "passes" in
              r["surfaces"]["wall"] else r["surfaces"]["wall"]["facet_x"] < 1.0
              for r in old_s)
          and all(r["surfaces"]["deck"]["facet_x"] < 1.0 for r in old_s),
          str([(r["key"], round(r["surfaces"]["wall"]["facet_p50"], 2))
               for r in old_s]))
    check("...and passes on the shell as shipped",
          all(r["passes"] for r in live_s),
          f"{[(r['key'], round(r['worst'], 2)) for r in live_s if not r['passes']]}")
    shrink = (sum(r["surfaces"]["wall"]["facet_p50"] for r in old_s)
              / max(sum(r["surfaces"]["wall"]["facet_p50"]
                        for r in live_s), 1e-9))
    check("the plated wall is broken into far smaller pieces than the boxed "
          "one", shrink > 3.0, f"{shrink:.2f}x")
    print(f"  wall facet p50, boxed / plated, over {len(live_s)} locations: "
          f"{shrink:.2f}x smaller")
    # AND THE FLOOR CANNOT BE LOWERED BY EDITING THE KIT. The corridor's own
    # measured wall facet has to stay inside the plate module `PROVISIONAL`
    # declares, so widening the kit's plates to make the rooms pass would have
    # to move a number sourced to `grey level 1.webp`.
    import interior_kit as _ik                                  # noqa: PLC0415
    check("the corridor's measured wall facet is bounded by its own declared "
          "plate module",
          kit_std["wall"]["facet_p50_m"] <= _ik.PROVISIONAL["wall_plate_l_m"],
          f"{kit_std['wall']['facet_p50_m']:.3f} m against a declared "
          f"{_ik.PROVISIONAL['wall_plate_l_m']:.3f} m plate")
    # SUBDIVISION CANNOT MOVE THE FACET EITHER -- the property that stops the
    # gate being answered with a tessellation flag instead of construction.
    # `subd` is `plain` split 8 x 8 per face, from section 1 above, so this is
    # the same box measured twice rather than two boxes compared -- which is
    # what the first draft of this check did, and it duly reported a 4 x 3 x 5
    # box as "the subdivision of" a 10 x 3 x 10 one and failed.
    check("a coplanar split does not move the facet size",
          abs(subd["facet_p50_m"] - plain["facet_p50_m"]) < 1e-9
          and abs(subd["facet_max_m"] - plain["facet_max_m"]) < 1e-9,
          f"plain p50 {plain['facet_p50_m']:.4f} / max "
          f"{plain['facet_max_m']:.4f} vs subdivided "
          f"{subd['facet_p50_m']:.4f} / {subd['facet_max_m']:.4f}")
    relief_facet = analyse(*_relief_box((0, 0, 0), (10, 3, 10), 0.5,
                                        0.06))["facet_p50_m"]
    probe("a REAL crease DOES move the facet -- so the check above can fire",
          relief_facet < plain["facet_p50_m"] * 0.5,
          f"relief at 0.5 m pitch reads {relief_facet:.3f} m against the "
          f"plain box's {plain['facet_p50_m']:.3f} m")

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


# ---------------------------------------------------------------------------
# THE MACHINERY GATE -- the half of a room this file could not see
# ---------------------------------------------------------------------------
# `report()` above scores a WHOLE LOCATION and 123 of 128 pass it. Every one of
# those rooms had a "containment vessel" that was a rectangular pier and a
# "fabrication furnace" that was a slab, so the whole-room number cannot be
# what says whether the machinery is built. Measured on the pre-INV-130 mesh:
#
#     location          room lambda   machinery lambda   machinery normals
#     fabrication           4.23            1.04               5.95
#     reactor_hall          4.02            0.66               5.83
#     medlab_one            5.76            1.89               5.84
#     business_center       6.20            2.19               5.07
#
# THE ARITHMETIC OF WHY THE AVERAGE HIDES IT. `rooms.build` emits 95%+ of a
# room's surface as SHELL -- deck, soffit, walls, ribs, bands, mullions,
# panels, deck joints -- and the shell was articulated in session 3s. The
# machinery is a few percent of the area, so a machine at a sixth of the
# shell's line density moves the room average by less than the gate's own
# margin. This is `CLAUDE.md`'s "every gate measured the case without the
# defect in it", one level down: the gate measured the room and the defect was
# in the object.
#
# THE FLOOR IS THE ROOM'S OWN SHELL, and it is derived rather than chosen for
# the same reason the three bounds above are:
#
#     lambda_machinery  >=  lambda_shell   of the same location
#
# In words: *the machine may not be less articulated than the wall behind it.*
# Nothing is picked -- the bar is whatever that room's own architecture already
# carries, so a coarse hall gets a coarse bar and a tight office a tight one,
# and no constant can go stale. It is a floor, not a target: a machine SHOULD
# beat its shell, because a machine is the thing a player walks up to.
#
# `normals` and `octaves` are printed and NOT gated, exactly as in the report
# above and for the same stated reason: their floors would have to be picked.
# They are diagnostic, and the one worth reading is `normals` -- density.py's
# own docstring says a box reads ~6 whatever its tessellation, and every row of
# the table above sits at 5.1 to 6.0.
SHELL_SUFFIXES = None            # resolved from rooms.py at call time


def _owner_names(tris_n, spans):
    """Per-triangle group name, LAST SPAN WINS.

    The same rule `export_scene.per_triangle`, `budget.Frustum` and
    `collision.prop_boxes` all use. It has to be the same rule: since INV-130 a
    fixture's span CONTAINS its parts' spans, so a rule that took the first
    owner would score every machine as its outer name and see none of the
    parts -- and a rule that disagreed with the exporter would be scoring a
    different mesh than the one that renders.
    """
    own = [None] * tris_n
    for name, lo, hi in spans:
        for i in range(lo, min(hi, tris_n)):
            own[i] = name
    return own


def machinery_split(v, t, g):
    """(machinery triangles, shell triangles) for one built room.

    SHELL is `rooms`' own definition -- the suffixes `is_solid` uses to decide
    what is the room itself as opposed to a thing standing in it -- so the two
    modules cannot drift about what a wall is.
    """
    import rooms as R                                           # noqa: PLC0415
    own = _owner_names(len(t), g)
    mach, shell = [], []
    for i, tri in enumerate(t):
        n = own[i]
        if n is None:
            continue
        if n.startswith(("fix_", "prop_")):
            mach.append(tri)
        elif n.endswith(R._SHELL_SUFFIXES):
            shell.append(tri)
    return mach, shell


def machinery_rows(schema=None, profile=None, keys=None):
    """Score the machinery of every procedural location against its own shell."""
    import rooms as R                                           # noqa: PLC0415
    if schema is None:
        schema, profile = it.load()
    places = R.unbuilt(schema, profile)
    if keys:
        want = set(keys)
        places = [p for p in places if p["key"] in want]
    out = []
    for p in places:
        v, t, g = R.build(schema, profile, p)
        mach, shell = machinery_split(v, t, g)
        am = analyse(v, mach, min_facet_m=0.0)
        ash = analyse(v, shell, min_facet_m=0.0)
        n_inst = sum(1 for n, _l, _h in g
                     if n.startswith(("fix_", "prop_"))
                     and R._MACH not in n)
        out.append({
            "key": p["key"], "name": p["name"], "arch": R.archetype(p),
            "tris": len(t), "mach_tris": len(mach), "shell_tris": len(shell),
            "instances": n_inst,
            "lam": am["lam"], "floor": ash["lam"], "area": am["area"],
            "normals": am["normals"], "octaves": am["octaves"],
            "ratio": (am["lam"] / ash["lam"]) if ash["lam"] > 0 else 0.0,
            "passes": am["lam"] >= ash["lam"],
        })
    return out


def _print_machinery(rows):
    print("\nMACHINERY DETAIL GATE -- is the machine as built as the wall "
          "behind it?\n")
    print(f"    {'location':34s} {'arch':12s} {'inst':>4s} {'mach tri':>8s} "
          f"{'area m2':>8s} {'lam':>7s} {'shell':>7s} {'x':>6s} "
          f"{'norm':>6s} {'oct':>5s}")
    print("-" * 116)
    for r in sorted(rows, key=lambda x: x["ratio"]):
        print(f"{'PASS' if r['passes'] else 'FAIL'}"
              f"{r['name'][:34]:34s} {r['arch']:12s} {r['instances']:4d} "
              f"{r['mach_tris']:8,d} {r['area']:8,.0f} {r['lam']:7.3f} "
              f"{r['floor']:7.3f} {r['ratio']:6.2f} {r['normals']:6.2f} "
              f"{r['octaves']:5.2f}")
    bad = [r for r in rows if not r["passes"]]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} locations have machinery at "
          f"or above their own shell's line density")
    print("x     = machinery line density / shell line density. The gate is "
          ">= 1.00.\nnorm  = effective distinct facing directions, area "
          "weighted. A BOX READS ~6\n        whatever its tessellation "
          "(see `analyse`), so a column of 5-6 across a\n        whole room is "
          "this gate's signature failure and is not itself gated.")
    return len(bad)


# ---------------------------------------------------------------------------
# THE SHELL GATE -- the mirror of the machinery gate, and the half BOTH of the
# gates above are blind to
# ---------------------------------------------------------------------------
# `report()` scores a WHOLE LOCATION; `machinery_rows()` scores the objects in
# it against the shell they stand in front of. Between them they left the
# largest surface in the station -- the shell itself -- measured only inside an
# average. Measured here, before anything was changed:
#
#     location      surface   area m2   lam    facet p50   the frame
#     war_room      wall        306    5.48      4.33 m    one pale panel
#     cargo_bays    wall        671    3.48      6.43 m    the same, bigger
#     fabrication   wall      1,251    2.98      9.51 m    the same, bigger still
#     the kit       wall        664    3.62      0.99 m    plate courses
#
# `docs/shell/before-office-half.png` is what those numbers look like: a wall
# divided by four dark lines into 2.5 x 2 m rectangles, and inside each
# rectangle nothing at all. `docs/aaa-scorecard.json` had already written the
# words -- *"one unbroken pale panel across 4 m with a scribed line and no
# joint"* -- and no gate in this repository could produce them as a number.
#
# WHY `lam` ALONE CANNOT SAY IT, which is the reusable half. Line density is
# metres of line over square metres of surface, and it does not care WHERE the
# line is. `rooms.articulate` runs a skirt, a dado, a rail, a cornice, six
# mullions a bay and four conduits down every wall on the station: continuous
# elements, enormous line, negligible area. They carry the wall's `lam` to
# x1.51 of the corridor's while the field between them stays one 4 m rectangle.
# The average hid the machinery in `report()`; here the TRIM hides the FIELD.
# Same defect, one level further in.
#
# So the shell is scored on two numbers and both are floored by the SAME
# reference:
#
#     lam        >=  the corridor kit's own, surface for surface
#     facet p50  <=  the corridor kit's own, surface for surface
#
# in words: *a room's wall may be neither less line-worked NOR more coarsely
# divided than the corridor wall outside its door.* The second is the one that
# fails today, and it is the one a player sees.
#
# THE FLOOR IS THE CORRIDOR KIT, and it is derived rather than chosen for three
# reasons. It is measured: every proportion in `interior_kit.PROVISIONAL`'s
# wall build-up is read off `grey level 1.webp`, the authority-1 frame that
# defines 1.00 for this project, and `docs/reference-values.md` §1 measures the
# same wall's tonal ladder rung by rung. It is the same station: `articulate()`
# already argues in its own docstring that "there is no reason a bar, a
# quarters unit or a customs hall should be articulated differently -- they are
# the same station, built by the same people". And it cannot go stale, because
# it is recomputed from the kit on every run rather than written down here.
#
# IT IS A FLOOR AND NOT A TARGET. The kit is itself at 29% of what
# `measure_reference()` reads off a Babylon 5 set (the `%show` column in
# `report()`), so a room that exactly matches the corridor is not finished --
# it has merely stopped being coarser than the surface it opens onto.
#
# AND THE FLOOR CANNOT BE LOWERED BY EDITING THE KIT. `_selftest` asserts the
# kit's own measured wall facet against `PROVISIONAL["wall_plate_l_m"]`, which
# is the sourced plate module; widening the kit's plates to make the rooms pass
# would have to move a number that traces to the frame.
#
# WHAT IS PRINTED AND NOT GATED: `facet max`, `normals`, `octaves`. Same reason
# as everywhere else in this file -- their floors would have to be picked.
# `facet max` is the single biggest unbroken piece and it is the more dramatic
# number, but one legitimately large service panel would fail a location on it,
# whereas `facet p50` says *half this surface is in pieces at least this big*,
# which is what a frame shows and what the complaint was about.

# A room's shell, split into the three surfaces a player can actually see.
# The suffixes are `rooms._TRIM_SUFFIXES` and `rooms._SHELL_SUFFIXES` sorted
# onto the surface each element belongs to -- a mullion is part of the wall it
# stands on, a soffit tee part of the ceiling it divides -- because the
# question "is this wall flat" is about the wall AND everything applied to it.
# Scoring the bare `_wall` box alone would be scoring a box and would say
# nothing about whether the room was articulated.
SHELL_SURFACES = {
    "deck": ("_deck", "_deck_joint"),
    "soffit": ("_soffit", "_soffit_tee"),
    "wall": ("_wall", "_rib", "_panel", "_mullion", "_skirt", "_dado",
             "_rail", "_cornice", "_conduit"),
}
# The corridor kit's own tags, surface for surface. These are exact names, not
# suffixes: `interior_kit` tags by piece rather than by suffix.
KIT_SURFACES = {
    "deck": ("deck_panel", "deck_grid"),
    "soffit": ("ceiling_slab",),
    "wall": ("wall_panel", "wall_assembly", "rail_band", "skirt",
             "wall_reveal", "pilaster", "portal_frame"),
}
_KIT_FLOOR = {}


def kit_surface_floor(length_m=21.6, force=False):
    """Measure the corridor kit's deck, soffit and wall. Cached.

    The kit is built here rather than imported as numbers, so a change to
    `interior_kit` moves the floor with it and the two cannot drift -- the same
    reason `collision.corridor_profile` ray-casts the kit instead of writing
    its section down.
    """
    if _KIT_FLOOR and not force:
        return _KIT_FLOOR
    import interior_kit as ik                                  # noqa: PLC0415
    ik.reset_tags()
    v, t = ik.corridor_section(length_m)
    spans = ik.tagged_spans(t)
    own = _owner_names(len(t), spans)
    parts = {k: [] for k in KIT_SURFACES}
    for i, tri in enumerate(t):
        n = own[i]
        for surf, names in KIT_SURFACES.items():
            if n in names:
                parts[surf].append(tri)
                break
    _KIT_FLOOR.clear()
    for surf, tris in parts.items():
        _KIT_FLOOR[surf] = analyse(v, tris, min_facet_m=0.0)
    return _KIT_FLOOR


# THE FLOOR HAS TO BE SIZE-MATCHED, AND THAT IS A MEASURED FINDING RATHER THAN
# A CONCESSION. `analyse` counts hidden surface -- the module docstring says so
# under WHAT THIS MEASURE IS NOT HONEST ABOUT -- and a plated wall's substrate
# is hidden behind its own plates. The substrate is ONE slab however long the
# run is, so its facet grows with the run while the plates do not. Measured on
# `interior_kit.wall_assembly` itself, the same construction at four sizes:
#
#     wall_assembly( 3.6 x 3.0)   lam 3.42   facet p50 0.99 m
#     wall_assembly( 7.2 x 3.0)   lam 3.27   facet p50 1.41 m
#     wall_assembly(12.8 x 3.0)   lam 3.21   facet p50 2.02 m
#     wall_assembly(12.8 x 7.5)   lam 1.93   facet p50 2.12 m
#
# Nothing about the construction changed across those four rows. So gating a
# 12.8 m foundry wall against the 3.6 m corridor's 0.99 m would fail it for
# being 12.8 m long, which is a fact about the room and not about how it was
# built -- and a gate that cannot be passed by correct construction is a
# target, not a floor.
#
# The gate is therefore the kit's own construction at THIS ROOM'S dimensions,
# and the corridor as built is reported beside it as the standard. Both are
# printed; only the size-matched one is gated. It still fails hard on the
# pre-INV-210 content -- 9.51 m against 2.12 -- which is the property that
# matters.
#
# Note the fourth row, because it is the reason this is a floor and not a
# ceiling: at 7.5 m the KIT ITSELF drops to lam 1.93, because
# `wall_plate_courses` is a fixed count of 3 and a 7.5 m wall divided into 3
# gives 2 m courses. `rooms.kit_plate_module` solves the course HEIGHT out of
# that same table instead of copying the count, so a room built to this
# vocabulary now beats a naive scaling of the kit on a tall wall. Where that
# happens it is stated in the report rather than being quietly enjoyed.
def kit_like_floor(w_m, l_m, ceil_m):
    """The kit's own construction, built at one room's width, length, height."""
    import interior_kit as ik                                  # noqa: PLC0415
    p = ik.PROVISIONAL
    out = {}
    # WALL -- the longest run the room actually has, which is the hardest case
    # and so the strictest floor the size-matching rule allows.
    ik.reset_tags()
    v, t = ik.wall_assembly(max(w_m, l_m), ceil_m, p)
    out["wall"] = analyse(v, t, min_facet_m=0.0)
    # DECK -- `corridor_section`'s own two calls: substrate panels every
    # `deck_panel_l_m`, then the tile grid over them.
    ik.reset_tags()
    v, t = [], []
    n = max(1, int(round(l_m / p["deck_panel_l_m"])))
    for i in range(n):
        pv, pt = ik.deck_panel(l_m / n, w_m)
        ik._merge(v, t, pv, pt, lambda x, y, z: (y, z, x),
                  (0.0, -0.12, l_m * (i + 0.5) / n))
    ik._merge(v, t, *ik.deck_grid(l_m, w_m, p))
    out["deck"] = analyse(v, t, min_facet_m=0.0)
    # SOFFIT -- the kit's ceiling slab, which is a plain plate and is therefore
    # the loosest of the three floors. Said plainly rather than hidden: the
    # corridor's ceiling IS flat, and `docs/reference-values.md` §1 rung 1-3
    # measures it as one of the darkest surfaces in the frame.
    ik.reset_tags()
    v, t = [], []
    ik._slab(v, t, -w_m / 2, w_m / 2, ceil_m, ceil_m + p["ceiling_slab_m"],
             0.0, l_m)
    out["soffit"] = analyse(v, t, min_facet_m=0.0)
    return out


def shell_split(v, t, g):
    """{surface: [triangles]} for one built room, by `SHELL_SURFACES`.

    LAST SPAN WINS, exactly as `machinery_split` does and for the same stated
    reason: a rule that disagreed with `export_scene.per_triangle` would be
    scoring a different mesh than the one that renders.
    """
    own = _owner_names(len(t), g)
    out = {k: [] for k in SHELL_SURFACES}
    for i, tri in enumerate(t):
        n = own[i]
        if n is None:
            continue
        for surf, sufs in SHELL_SURFACES.items():
            if n.endswith(sufs):
                out[surf].append(tri)
                break
    return out


def shell_rows(schema=None, profile=None, keys=None, floor=None):
    """Score every procedural location's shell, surface by surface."""
    import rooms as R                                           # noqa: PLC0415
    if schema is None:
        schema, profile = it.load()
    kit = floor or kit_surface_floor()
    places = R.unbuilt(schema, profile)
    if keys:
        want = set(keys)
        places = [p for p in places if p["key"] in want]
    out = []
    for p in places:
        v, t, g = R.build(schema, profile, p)
        # Built span, not the one-bay clamp -- see the note at the other site.
        bw, bl = R.built_span_m(schema, profile, p)
        same = kit_like_floor(bw, bl, R.ceiling_m(p))
        row = {"key": p["key"], "name": p["name"], "arch": R.archetype(p),
               "tris": len(t), "surfaces": {}}
        worst = 1.0
        for surf, tris in shell_split(v, t, g).items():
            a = analyse(v, tris, min_facet_m=0.0)
            k, s = kit[surf], same[surf]
            lam_x = (a["lam"] / s["lam"]) if s["lam"] > 0 else 0.0
            # Facet is a CEILING, so its "how well are we doing" number is the
            # floor over the measurement, not the other way round.
            fac_x = (s["facet_p50_m"] / a["facet_p50_m"]
                     if a["facet_p50_m"] > 0 else 0.0)
            row["surfaces"][surf] = {
                "tris": a["tris"], "area": a["area"], "lam": a["lam"],
                "lam_floor": s["lam"], "lam_x": lam_x,
                "facet_p50": a["facet_p50_m"], "facet_max": a["facet_max_m"],
                "facet_floor": s["facet_p50_m"], "facet_x": fac_x,
                # The corridor AS BUILT -- reported, never gated. See the
                # comment above `kit_like_floor`.
                "kit_lam_x": (a["lam"] / k["lam"]) if k["lam"] > 0 else 0.0,
                "kit_facet_x": (k["facet_p50_m"] / a["facet_p50_m"]
                                if a["facet_p50_m"] > 0 else 0.0),
                "normals": a["normals"], "octaves": a["octaves"],
                "passes": lam_x >= 1.0 and fac_x >= 1.0,
            }
            worst = min(worst, lam_x, fac_x)
        row["worst"] = worst
        row["passes"] = all(s["passes"] for s in row["surfaces"].values())
        out.append(row)
    return out


def _print_shell(rows, kit=None):
    kit = kit or kit_surface_floor()
    print("\nSHELL DETAIL GATE -- is the room's own wall as built as the "
          "corridor wall outside its door?\n")
    print("  the floor, measured off interior_kit.corridor_section this run:")
    for surf in ("deck", "soffit", "wall"):
        k = kit[surf]
        print(f"    {surf:7s} {k['area']:8,.1f} m2   lam {k['lam']:6.3f} /m   "
              f"facet p50 {k['facet_p50_m']:5.2f} m   max "
              f"{k['facet_max_m']:5.2f} m")
    print()
    print(f"    {'location':30s} {'arch':11s} {'surface':7s} {'area m2':>9s} "
          f"{'lam':>6s} {'x':>5s} {'p50 m':>6s} {'x':>5s} {'xkit':>5s} "
          f"{'max m':>6s} {'norm':>5s}")
    print("-" * 114)
    for r in sorted(rows, key=lambda x: x["worst"]):
        for surf in ("wall", "deck", "soffit"):
            s = r["surfaces"][surf]
            print(f"{'PASS' if s['passes'] else 'FAIL'}"
                  f"{r['name'][:30]:30s} {r['arch']:11s} {surf:7s} "
                  f"{s['area']:9,.0f} {s['lam']:6.2f} {s['lam_x']:5.2f} "
                  f"{s['facet_p50']:6.2f} {s['facet_x']:5.2f} "
                  f"{s['kit_facet_x']:5.2f} "
                  f"{s['facet_max']:6.2f} {s['normals']:5.2f}")
    bad = [r for r in rows if not r["passes"]]
    n_surf = sum(1 for r in rows for s in r["surfaces"].values())
    n_good = sum(1 for r in rows for s in r["surfaces"].values()
                 if s["passes"])
    print(f"\n{len(rows) - len(bad)}/{len(rows)} locations have a shell at or "
          f"above the corridor's on every surface\n"
          f"{n_good}/{n_surf} surfaces pass")
    for surf in ("wall", "deck", "soffit"):
        ok = sum(1 for r in rows if r["surfaces"][surf]["passes"])
        lo = min(r["surfaces"][surf]["facet_p50"] for r in rows)
        hi = max(r["surfaces"][surf]["facet_p50"] for r in rows)
        kx = [r["surfaces"][surf]["kit_facet_x"] for r in rows]
        print(f"  {surf:7s} {ok:3d}/{len(rows)}   facet p50 {lo:5.2f}-"
              f"{hi:5.2f} m   against the corridor AS BUILT "
              f"({kit[surf]['facet_p50_m']:.2f} m): "
              f"x{min(kx):.2f}-{max(kx):.2f}, "
              f"{sum(1 for q in kx if q >= 1.0)}/{len(rows)} at or better")
    print("\nlam x, p50 x = against the KIT'S OWN CONSTRUCTION AT THIS ROOM'S "
          "SIZE, and both\ngate at >= 1.00. xkit = the same facet against the "
          "corridor AS BUILT, which is\nreported and NOT gated: the same kit "
          "construction measures 0.99 m at a 3.6 m bay\nand 2.02 m at 12.8 m, "
          "so that column is partly a fact about room size. See the\nblock "
          "above `kit_like_floor`. `max` and `norm` are printed, not gated. "
          "A BOX\nREADS ~6 NORMALS whatever its tessellation.")
    return len(bad)


def _cli(argv):
    if "--selftest" in argv:
        return _selftest()
    if "--shell" in argv:
        i = argv.index("--shell")
        keys = [a for a in argv[i + 1:] if not a.startswith("-")]
        return 1 if _print_shell(shell_rows(keys=keys or None)) else 0
    if "--machinery" in argv:
        i = argv.index("--machinery")
        keys = [a for a in argv[i + 1:] if not a.startswith("-")]
        return 1 if _print_machinery(machinery_rows(keys=keys or None)) else 0
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
