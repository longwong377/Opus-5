"""Cut the openings the interior needs into the lathed hull.

WHY THIS EXISTS

`docs/volume-audit.md` §5.1: *"`generate_hull.py::build()` lathes a closed
surface of revolution and caps both ends; there is no subtraction anywhere in
the file. The cobra bays get a modelled recess -- the 24 docking bays get
nothing. This is the owner's rule running the other way: an interior with no
exterior."*

Hard rule 4 says inside and outside come from one schema. A bay you can stand
in, behind a hull with no hole in it, is that rule violated in the direction
nobody was checking. This module is the hole.

WHERE THE MOUTH IS, AND WHY IT IS NOT A HOLE IN THE SIDE OF THE STATION

The single most important fact about a docking bay's geometry, and it took
measuring to see: **the bay's mouth is perpendicular to the station axis.**
`docking_bay.docking_bay()` authors the bay with `+Z running INTO the bay from
the mouth at z = 0`, and `place_bay` maps local +Y to radially inward and local
+X to an arc -- so once placed, the mouth is a rectangle lying in a plane of
constant z, spanning 42 m of arc and 22.2 m of radius, with the deck at the
OUTSIDE (r = 254.2 m) and the ceiling INBOARD of it (r = 232.0 m).

A rectangle perpendicular to the axis cannot be a hole in a cylinder that is
parallel to it. Cutting a radial slot at the bay's angle and z would open onto
14.4 m of solid hull and then hit the bay's FLOOR from underneath -- which is
not a mouth, it is a trapdoor. So the aperture is not where the bay is; it is
where the bay's mouth POINTS, and the mouth points along the axis.

Fore or aft is then decided by the hull rather than by taste, and only one
answer produces an aperture at all:

  - mouth FORE (z = 7185, the register's fore edge): the mouth's radial band
    254.2 .. 232.0 m is inside a hull that is 268.6 m at that z, and the
    docking sphere's forward taper falls through that band at z 7207.7 (254.2)
    to z 7245.1 (232.0). The prism swept fore from the mouth exits the hull
    through a 42 x 37 m rectangle in the taper. **That is the aperture.**
  - mouth AFT (z = 7045): the hull there is 166.2 m -- already inside the
    mouth's radial band. The prism swept aft never meets the hull at all,
    because the bay's aft end is in vacuum before it starts.

So the mouths face fore, out through the docking sphere's forward shoulder,
into the approach C&C watches from Observation Dome 1 (`TRAFFIC-AND-CUSTOMS.md`
§4.4, authority 4). That is INV-100.

WHAT IS CUT AND WHAT IS BUILT

Per bay: the hull cells inside the swept prism are deleted, and the prism's own
four lateral faces are built between the mouth plane and the hull's cut edge --
a throat. The throat's fore boundary REUSES THE HULL'S OWN VERTICES rather than
new ones at the same coordinates, so the weld is by index and cannot drift with
the plating jitter, which moves every hull vertex by up to +/-1.3 m.

CUT THE LATHE, DO NOT SUBTRACT AFTERWARDS

Both were available and the lathe wins on four counts:

1. **Exactness.** The lathe is a grid in (z, theta). If the aperture's own
   boundary angles and its hull-crossing z values are inserted into that grid,
   the cut is a set membership test on whole cells -- no intersection
   arithmetic, no slivers, no T-junctions, and the rim is a set of edges that
   already existed.
2. **No boolean.** A general mesh subtraction is hundreds of lines whose
   failure modes are coplanar faces and near-degenerate triangles, and this
   hull has 1.3 m of pseudo-random plating jitter on every vertex and sits
   7.2 km from the origin. That is the worst input a boolean can get.
3. **It welds by index.** A subtraction produces two surfaces that must be
   stitched by coordinate; cutting produces one surface that was never split.
4. **It stays cheap.** The refined angle set is applied only in a z band around
   the cut, so the whole rest of the 8 km lathe is byte-identical to what it
   was. `generate_hull.py --no-apertures` proves that.

THE COST OF CUTTING THE LATHE, stated because it is real: the lathe's angular
resolution is 5.625 deg and a bay's arc is 9.4667 deg, so the aperture edges do
not fall on lathe columns. They are INSERTED -- 48 extra angles, live only
between z 7178 and z 7275 -- and the two rings where the refined set meets the
base set are stitched by an angle merge rather than by a quad strip.

WHAT IT LOOKS LIKE. `docs/engine-docking-bay-mouths.png` (eye 900,500,7700 ->
0,0,7215, fov 40) is the ring of 24 from a kilometre out, interleaved with the
cobra bays' blisters around the same shoulder;
`docs/engine-docking-bay-mouth-close.png` (eye 470,120,7480 -> 243,0,7215,
fov 38) is three of them at the rubric's half distance, with the chevron lip on
the rim and the throat receding behind it. The standing orbit shot
`--orbit 9200,18,214` shows nothing: a 42 m mouth at 9.2 km is a third of a
pixel, and that is the right answer rather than a defect.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import directory as _directory                                  # noqa: E402
import docking_bay as _db                                       # noqa: E402
import interior as _it                                          # noqa: E402

# The mouth surround, and it is derived rather than chosen: `docking_bay.py`
# gives the bay's overhead box girders a depth of GIRDER_D_M, and the structural
# member framing a mouth is the same member that spans the bay. One girder deep
# is the band that carries the hazard chevron `dock.webp` puts on every edge.
LIP_DEPTH_M = _db.GIRDER_D_M

# Two angles closer than this are the same angle. At the docking sphere's
# 254 m radius, 1e-6 rad is 0.25 mm -- far below the 1.3 m plating jitter, so
# nothing real is ever merged, and a sliver triangle is never emitted.
ANGLE_EPS = 1e-6

GROUP_THROAT = "docking_bay_throat"
GROUP_LIP = "docking_bay_lip"


class Aperture:
    """A rectangular opening swept along the axis until it leaves the hull.

    Fields are all derived; nothing here is written down twice.

      key        the register key this belongs to, plus the bay index
      a0, a1     the arc it spans, radians, a0 < a1 (never wrapped -- see
                 `_unwrap`)
      r_in,r_out its radial band
      z_mouth    the plane the opening's inboard end lies in
      z_out      the z at which the hull's radius equals r_out
      z_in       the z at which the hull's radius equals r_in
    """

    __slots__ = ("key", "index", "a0", "a1", "r_in", "r_out",
                 "z_mouth", "z_out", "z_in")

    def __init__(self, key, index, a0, a1, r_in, r_out, z_mouth, z_out, z_in):
        if not (a0 < a1):
            raise ValueError(f"{key}: arc {a0} .. {a1} is not increasing")
        if not (r_in < r_out):
            raise ValueError(f"{key}: radial band {r_in} .. {r_out}")
        if not (z_mouth < z_out < z_in):
            raise ValueError(
                f"{key}: the mouth must lie inboard of both hull crossings, "
                f"got mouth {z_mouth} out {z_out} in {z_in}")
        self.key, self.index = key, index
        self.a0, self.a1 = a0, a1
        self.r_in, self.r_out = r_in, r_out
        self.z_mouth, self.z_out, self.z_in = z_mouth, z_out, z_in

    def contains_angle(self, a):
        """Is this angle strictly inside the arc? Cyclic, so +/-2pi counts."""
        for k in (-1, 0, 1):
            if self.a0 < a + k * 2.0 * math.pi < self.a1:
                return True
        return False

    def contains_z(self, z):
        return self.z_out < z < self.z_in

    def __repr__(self):
        return (f"<Aperture {self.key}#{self.index} "
                f"arc {math.degrees(self.a0):.3f}..{math.degrees(self.a1):.3f} "
                f"r {self.r_in:.1f}..{self.r_out:.1f} "
                f"z {self.z_mouth:.1f}|{self.z_out:.2f}..{self.z_in:.2f}>")


# ---------------------------------------------------------------------------
# Deriving the apertures
# ---------------------------------------------------------------------------
def _radius_at(profile, z):
    """Hull radius by LINEAR interpolation, not nearest sample.

    `components.radius_at` takes the nearest sample, which is right for hanging
    a 470 m radiator off the hull and wrong here: the crossing z values below
    are inserted into the lathe as new rings, and a ring whose radius disagrees
    with the interpolation the neighbouring quads imply is a 3 m step in the
    hull. Same reason `drum_walk` calls `ground_patch` instead of re-authoring
    the terrain.
    """
    if z <= profile[0]["z_m"]:
        return profile[0]["radius_m"]
    if z >= profile[-1]["z_m"]:
        return profile[-1]["radius_m"]
    lo, hi = 0, len(profile) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if profile[mid]["z_m"] < z:
            lo = mid
        else:
            hi = mid
    z0, r0 = profile[lo]["z_m"], profile[lo]["radius_m"]
    z1, r1 = profile[hi]["z_m"], profile[hi]["radius_m"]
    if z1 == z0:
        return r0
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)


def _first_crossing(profile, radius, z_from):
    """The first z at or fore of `z_from` where the hull radius passes `radius`.

    Returns None if it never does. Linear within a sample interval, so the
    value is exactly the one `_radius_at` reproduces.
    """
    prev = None
    for s in profile:
        z, r = s["z_m"], s["radius_m"]
        if z < z_from:
            prev = s
            continue
        if prev is not None and prev["z_m"] >= z_from:
            a, b = prev["radius_m"], r
            if (a - radius) * (b - radius) <= 0 and a != b:
                t = (radius - a) / (b - a)
                return prev["z_m"] + t * (z - prev["z_m"])
        prev = s
    return None


def docking_bay_apertures(schema=None, profile=None):
    """The 24 docking-bay mouths.

    Every number is read from somewhere else:

      count, width, height, sag, deck radius  `station/docking_bay.py`
      angle of bay i                          `docking_bay.bay_angle_deg`
      the z of the mouth                      `directory.PLACES["docking_bays"]`
      where the hull is                       `station/schema/radius_profile.json`

    Nothing is placed by hand, which is the point: if the register moves the
    bays or the bay gets wider, the holes move with them.
    """
    if schema is None:
        schema, profile = _it.load()
    prof = profile["profile"] if isinstance(profile, dict) else profile

    place = _directory.by_key("docking_bays")
    if place["module"] != "docking_bay":
        raise ValueError("docking_bays no longer names the docking_bay module")
    z_c, (foot_deg, foot_len) = place["z_m"], place["footprint"]
    if abs(foot_len - _db.BAY_LEN_M) > 1e-6:
        raise ValueError(
            f"the register's footprint length {foot_len} m and "
            f"docking_bay.BAY_LEN_M {_db.BAY_LEN_M} m disagree -- one of them "
            f"is not describing the bay")
    z_mouth = z_c + foot_len / 2.0            # INV-100: the mouths face fore

    r_out = _db.bay_radius(schema, prof)
    # The ceiling is an arc, highest on the centreline. The mouth has to clear
    # its highest point or the aperture cuts the roof off.
    ceiling = _db.BAY_H_M + _db.BAY_W_M * 0.10
    r_in = r_out - ceiling

    z_out = _first_crossing(prof, r_out, z_mouth)
    z_in = _first_crossing(prof, r_in, z_mouth)
    if z_out is None or z_in is None:
        raise ValueError(
            f"the hull never falls through the mouth's radial band "
            f"{r_in:.1f}..{r_out:.1f} m fore of z={z_mouth} -- the bays have "
            f"no exterior and this module cannot invent one")

    half = _db.BAY_W_M / 2.0 / r_out          # place_bay's own arc convention
    out = []
    for i in range(_db.BAY_COUNT):
        a = math.radians(_db.bay_angle_deg(i))
        out.append(Aperture("docking_bays", i, a - half, a + half,
                            r_in, r_out, z_mouth, z_out, z_in))
    return tuple(out)


def hull_apertures(schema=None, profile=None):
    """Every aperture the hull carries. One family today."""
    return docking_bay_apertures(schema, profile)


# ---------------------------------------------------------------------------
# What the lathe has to do differently
# ---------------------------------------------------------------------------
def extra_z(aps):
    """Sample z values the lathe must contain for the cut to be exact."""
    return sorted({ap.z_out for ap in aps} | {ap.z_in for ap in aps})


def extra_angles(aps):
    """Angles the lathe must contain, normalised into [0, 2pi)."""
    return sorted({ap.a0 % (2.0 * math.pi) for ap in aps}
                  | {ap.a1 % (2.0 * math.pi) for ap in aps})


def refined_angles(base, aps, eps=ANGLE_EPS):
    """`base` plus the aperture edges, with near-duplicates snapped to `base`.

    An inserted angle a hair off a lathe column would emit a triangle a
    millimetre wide, which is a crack in any renderer that does not use double
    precision for rasterisation -- i.e. all of them.
    """
    out = list(base)
    for a in extra_angles(aps):
        if all(abs(a - b) > eps and abs(a - b - 2.0 * math.pi) > eps
               and abs(a - b + 2.0 * math.pi) > eps for b in out):
            out.append(a)
    return sorted(out)


def collar_band(aps):
    """The z range where the hull carries no plate seams.

    AN OPENING IS A FABRICATED COLLAR, AND A COLLAR IS NOT PLATE. The hull's
    plating jitter moves every vertex radially by up to `hull_plating.depth_m`
    (1.3 m) and changes value every `rows_per_plate` rings, so across one plate
    row boundary the hull can step 2.6 m. The forward taper the bay mouths cut
    through falls at 0.34 m per metre of z -- about 1.4 m per ring -- so a
    plate step LOCALLY REVERSES THE TAPER, and a throat wall welded to two hull
    rings in the wrong order folds back on itself.

    Measured, not supposed: at z 7224.7 -> 7228.8 the profile falls 244.7 ->
    243.3 m and the plated hull RISES 243.723 -> 244.100 m. Twenty-four throat
    triangles came out facing the wrong way, on four bays, and the winding
    check in `_selftest` is what found them.

    So the band the mouths cut through is lathed smooth. It is one machined
    ring around the station rather than 112 plates, which is what a docking
    face is, and it puts a fabrication break line at each end of the collar --
    the same kind of step the plate rows already put every 65 m.
    """
    if not aps:
        return None
    return (min(ap.z_out for ap in aps), max(ap.z_in for ap in aps))


def cut_band(aps, margin=30.0):
    """The z range that needs the refined angle set, with a stitch margin.

    The margin has to be at least one ring on each side so the two stitch
    strips -- where a 64-column ring meets a 112-column one -- are never
    themselves inside a cut. `_selftest` asserts that.
    """
    if not aps:
        return None
    return (min(ap.z_out for ap in aps) - margin,
            max(ap.z_in for ap in aps) + margin)


def is_cut(aps, theta_mid, z_mid):
    """Is this lathe cell inside an aperture?

    A whole-cell test, and it is exact because both boundaries are in the
    lathe's own sample sets -- the midpoint can never straddle one.
    """
    for ap in aps:
        if ap.contains_z(z_mid) and ap.contains_angle(theta_mid):
            return True
    return False


# ---------------------------------------------------------------------------
# The throat
# ---------------------------------------------------------------------------
def build_throats(aps, verts, ring_vertex, ring_zs, angles):
    """The four lateral faces of each aperture's prism, welded to the hull.

    `ring_vertex(k, j)` gives the hull vertex index of ring k at angle index j;
    `ring_zs[k]` its z; `angles` the refined angle list those rings were built
    from. Vertices are APPENDED to `verts`.

    Returns {group: [triangles]}.

    The fore edge of every face is hull vertices, by index. The aft edge is a
    projection of those same vertices onto the mouth plane, so the throat
    inherits the plating jitter exactly and the two surfaces cannot part.
    """
    out = {GROUP_THROAT: [], GROUP_LIP: []}
    if not aps:
        return out

    two_pi = 2.0 * math.pi

    def ang_index(a):
        """Index of `a` in `angles`, cyclically, or None."""
        t = a % two_pi
        for j, b in enumerate(angles):
            if abs(b - t) <= ANGLE_EPS or abs(b - t - two_pi) <= ANGLE_EPS \
                    or abs(b - t + two_pi) <= ANGLE_EPS:
                return j
        return None

    def ring_index(z):
        for k, zz in enumerate(ring_zs):
            if abs(zz - z) <= 1e-6:
                return k
        return None

    for ap in aps:
        j0, j1 = ang_index(ap.a0), ang_index(ap.a1)
        k_out, k_in = ring_index(ap.z_out), ring_index(ap.z_in)
        if None in (j0, j1, k_out, k_in):
            raise ValueError(
                f"{ap!r}: its own boundary is not in the lathe -- "
                f"angles {j0},{j1} rings {k_out},{k_in}. The refinement and "
                f"the aperture list have come apart")

        cols = []                       # angle indices across the mouth
        j = j0
        while True:
            cols.append(j)
            if j == j1:
                break
            j = (j + 1) % len(angles)
        rows = list(range(k_out, k_in + 1))     # rings down the taper

        proj = {}

        def project(vi, z_hull):
            """The mouth-plane and lip-plane twins of a hull vertex.

            Keyed on the hull vertex, so a corner shared by two faces is one
            pair of vertices and the throat is a closed tube rather than four
            panels that happen to touch.
            """
            if vi in proj:
                return proj[vi]
            x, y, _z = verts[vi]
            z_lip = z_hull - LIP_DEPTH_M
            if z_lip <= ap.z_mouth + 1e-6:
                # The lip band would swallow the whole throat, and a zero-depth
                # band is a row of degenerate triangles that `boundary_edges`
                # would then weld away, silently opening the rim.
                raise ValueError(
                    f"{ap!r}: the throat is shorter than its {LIP_DEPTH_M} m "
                    f"lip at z={z_hull:.2f}")
            a = len(verts)
            verts.append((x, y, z_lip))
            verts.append((x, y, ap.z_mouth))
            proj[vi] = (a, a + 1)
            return proj[vi]

        def strip(pairs, flip):
            """Weld a run of hull vertices back to the mouth plane.

            `pairs` is [(hull vertex, its z)] in order along the hole's
            boundary. Two bands come out: the lip nearest the hull, then the
            throat. `flip` reverses the winding for the two faces whose
            boundary runs the other way round the hole.
            """
            proj_v = [project(vi, z) for vi, z in pairs]
            for m in range(len(pairs) - 1):
                h0, h1 = pairs[m][0], pairs[m + 1][0]
                (l0, m0), (l1, m1) = proj_v[m], proj_v[m + 1]
                # Corners in CYCLIC order, split on the p0-q0 diagonal, which
                # is the lathe's own convention (`generate_hull.build`:
                # a,b,c,d -> (a,b,c),(a,c,d)). Splitting on p0-q1 instead put
                # the diagonal along an EDGE of the quad, which leaves two
                # overlapping triangles and an unpaired boundary edge per
                # cell -- 2,432 of them, which is how this was found.
                for group, (p0, p1, q0, q1) in (
                        (GROUP_LIP, (h0, h1, l1, l0)),
                        (GROUP_THROAT, (l0, l1, m1, m0))):
                    if flip:
                        p0, p1, q0, q1 = p1, p0, q1, q0
                    out[group].append((p0, p1, q0))
                    out[group].append((p0, q0, q1))

        # The four faces. The throat's visible side is its INSIDE, so every
        # normal has to point at the prism's centre line -- which is the
        # opposite sense to the hull's own outward winding, and different for
        # each face. Derived rather than guessed: walking `cols` in increasing
        # angle with flip off gives -r, and walking `rows` in increasing z with
        # flip off gives -theta. `_selftest` measures the normals rather than
        # trusting this comment.
        #
        #   r = r_out, ring k_out   the deck, seen from above       -> -r
        #   theta = a1              the far wall, seen from inside   -> -theta
        #   r = r_in,  ring k_in    the roof, seen from below        -> +r
        #   theta = a0              the near wall, seen from inside  -> +theta
        strip([(ring_vertex(k_out, c), ring_zs[k_out]) for c in cols], False)
        strip([(ring_vertex(k, j1), ring_zs[k]) for k in rows], False)
        strip([(ring_vertex(k_in, c), ring_zs[k_in]) for c in cols], True)
        strip([(ring_vertex(k, j0), ring_zs[k]) for k in rows], True)

    return out


# ---------------------------------------------------------------------------
# The closure gate
# ---------------------------------------------------------------------------
def classify_open_edges(aps, verts, open_edges, slack=2.0):
    """Sort measured open edges into the mouths they belong to, or `None`.

    `open_edges` is `interior_kit.boundary_edges`'s first return -- pairs of
    ROUNDED COORDINATE KEYS, not indices. An edge belongs to aperture `ap` when
    both ends lie in its mouth plane and inside its (arc, radius) rectangle.

    The predicate is written from the aperture SPEC, never from the geometry
    that was emitted, so it is an independent statement about where holes are
    allowed to be. `slack` covers the plating jitter, which moves a hull vertex
    by up to hull_plating.depth_m and therefore moves the mouth's corners with
    it.
    """
    two_pi = 2.0 * math.pi
    buckets = {i: [] for i in range(len(aps))}
    stray = []
    for e in open_edges:
        owner = None
        for i, ap in enumerate(aps):
            ok = True
            for p in e:
                x, y, z = p
                if abs(z - ap.z_mouth) > 1e-3:
                    ok = False
                    break
                r = math.hypot(x, y)
                if not (ap.r_in - slack <= r <= ap.r_out + slack):
                    ok = False
                    break
                a = math.atan2(y, x)
                if not any(ap.a0 - 1e-6 <= a + k * two_pi <= ap.a1 + 1e-6
                           for k in (-1, 0, 1)):
                    ok = False
                    break
            if ok:
                owner = i
                break
        if owner is None:
            stray.append(e)
        else:
            buckets[owner].append(e)
    return buckets, stray


def loop_is_closed(edges):
    """Every vertex of this edge set has degree exactly 2.

    A rim that has lost a face, or gained a sliver, fails here. A rim that is
    merely the wrong SIZE does not -- that is what the extent check is for.
    """
    deg = {}
    for a, b in edges:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    return bool(deg) and all(v == 2 for v in deg.values())


def loop_extent(edges):
    """(arc span in radians, radial span in metres) of an edge set."""
    pts = {p for e in edges for p in e}
    rs = [math.hypot(x, y) for x, y, _ in pts]
    angs = [math.atan2(y, x) for x, y, _ in pts]
    # Unwrap about the first point so a mouth straddling 0 deg still measures.
    ref = angs[0]
    angs = [a + round((ref - a) / (2.0 * math.pi)) * 2.0 * math.pi
            for a in angs]
    return max(angs) - min(angs), max(rs) - min(rs)


# ---------------------------------------------------------------------------
def _selftest():
    import interior_kit as ik                                # noqa: PLC0415
    import generate_hull as gh                               # noqa: PLC0415

    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ok    {name}" + (f"  -- {detail}" if detail else ""))
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = _it.load()
    aps = hull_apertures(schema, profile)
    ap0 = aps[0]

    print(f"{len(aps)} apertures; {ap0!r}")

    # -- the derivation is a derivation ------------------------------------
    check("one aperture per bay in the register's count",
          len(aps) == _db.BAY_COUNT,
          f"{len(aps)} against BAY_COUNT {_db.BAY_COUNT}")
    place = _directory.by_key("docking_bays")
    check("the mouth plane is the register's fore edge, not a literal",
          abs(ap0.z_mouth - (place["z_m"] + place["footprint"][1] / 2.0)) < 1e-9,
          f"z_mouth {ap0.z_mouth} from z_m {place['z_m']} "
          f"+ {place['footprint'][1]}/2")
    check("the mouth's outer radius is the bay deck",
          abs(ap0.r_out - _db.bay_radius(schema, profile)) < 1e-9)
    check("the mouth clears the ceiling at its highest",
          abs((ap0.r_out - ap0.r_in) - (_db.BAY_H_M + _db.BAY_W_M * 0.10)) < 1e-9,
          f"{ap0.r_out - ap0.r_in:.2f} m of radial mouth")
    check("the arc is the bay's own width at the bay's own radius",
          abs((ap0.a1 - ap0.a0) * ap0.r_out - _db.BAY_W_M) < 1e-9,
          f"{(ap0.a1 - ap0.a0) * ap0.r_out:.3f} m against "
          f"BAY_W_M {_db.BAY_W_M}")
    prof = profile["profile"] if isinstance(profile, dict) else profile
    check("z_out is where the hull radius really is r_out",
          abs(_radius_at(prof, ap0.z_out) - ap0.r_out) < 1e-6,
          f"hull r({ap0.z_out:.2f}) = {_radius_at(prof, ap0.z_out):.4f}")
    check("z_in is where the hull radius really is r_in",
          abs(_radius_at(prof, ap0.z_in) - ap0.r_in) < 1e-6,
          f"hull r({ap0.z_in:.2f}) = {_radius_at(prof, ap0.z_in):.4f}")
    check("the mouth is INSIDE the hull, so the throat has length",
          _radius_at(prof, ap0.z_mouth) > ap0.r_out,
          f"hull r at the mouth {_radius_at(prof, ap0.z_mouth):.1f} > "
          f"r_out {ap0.r_out:.1f}: a {ap0.z_out - ap0.z_mouth:.1f} m throat "
          f"at the deck, {ap0.z_in - ap0.z_mouth:.1f} m at the roof")

    # Neighbouring apertures must leave hull between them, for the same reason
    # `docking_bay._selftest` insists on hull between neighbouring bays: 24
    # holes that touch is one annulus, not 24 bays.
    spans = sorted((ap.a0, ap.a1) for ap in aps)
    gaps = [spans[(i + 1) % len(spans)][0] + (2.0 * math.pi if i + 1 >= len(spans) else 0.0)
            - spans[i][1] for i in range(len(spans))]
    check("there is hull between neighbouring mouths",
          min(gaps) > 0.0,
          f"{math.degrees(min(gaps)):.3f} deg of hull between "
          f"{math.degrees(spans[0][1] - spans[0][0]):.3f} deg mouths")

    band = cut_band(aps)
    check("no aperture reaches the stitch rings",
          band[0] < min(a.z_out for a in aps) and band[1] > max(a.z_in for a in aps),
          f"refined band {band[0]:.1f}..{band[1]:.1f} around a cut of "
          f"{min(a.z_out for a in aps):.1f}..{max(a.z_in for a in aps):.1f}")

    base = [2.0 * math.pi * i / 64 for i in range(64)]
    ref = refined_angles(base, aps)
    check("refinement is a superset of the lathe's own columns",
          all(any(abs(b - a) <= ANGLE_EPS for a in ref) for b in base),
          f"{len(base)} base -> {len(ref)} refined")
    d = sorted(ref[i + 1] - ref[i] for i in range(len(ref) - 1))
    check("refinement emits no sliver columns",
          d[0] > 1e-4,
          f"narrowest column {math.degrees(d[0]) * 60:.2f} arcmin "
          f"= {d[0] * ap0.r_out:.3f} m at the mouth radius")

    # -- the cut, measured on the real hull --------------------------------
    print("\n  building the hull twice, with and without the cut...")
    v_no, g_no, _r, _d, _c = gh.build(64, 1, apertures=())
    v_yes, g_yes, _r2, _d2, _c2 = gh.build(64, 1, apertures=aps)
    t_no = [t for g in g_no.values() for t in g]
    t_yes = [t for g in g_yes.values() for t in g]

    op_no, nm_no = ik.boundary_edges(v_no, t_no)
    check("the uncut lathe is closed, which is what makes this measurable",
          not op_no and not nm_no,
          f"open {len(op_no)} non-manifold {len(nm_no)}")

    op, nm = ik.boundary_edges(v_yes, t_yes)
    check("the cut hull is still manifold", not nm,
          f"{len(nm)} non-manifold edges")

    buckets, stray = classify_open_edges(aps, v_yes, op)
    check("every open edge is on a bay mouth and nothing else",
          not stray,
          f"{len(op)} open edges, {len(stray)} of them off the mouths"
          + (f" e.g. {stray[0]}" if stray else ""))
    check("every bay mouth is open", all(buckets[i] for i in range(len(aps))),
          f"{sum(1 for i in buckets if not buckets[i])} mouths with no rim")
    check("every rim is a single closed loop",
          all(loop_is_closed(buckets[i]) for i in range(len(aps))),
          f"{sum(1 for i in buckets if not loop_is_closed(buckets[i]))} ragged")

    # A throat is a surface you look at from INSIDE, so every one of its
    # normals has to point at the prism's own centre line. Winding was wrong
    # on two of the four faces in the first build and nothing else could have
    # said so: a reversed face has the same silhouette and the renderer simply
    # shades the far side of the tunnel instead of the near one -- the same
    # defect `components._box` carried for four sessions.
    wrong = 0
    for gid in (GROUP_THROAT, GROUP_LIP):
        for tri in g_yes.get(gid, ()):
            p = [v_yes[i] for i in tri]
            cx = sum(q[0] for q in p) / 3.0
            cy = sum(q[1] for q in p) / 3.0
            u = [p[1][k] - p[0][k] for k in range(3)]
            w = [p[2][k] - p[0][k] for k in range(3)]
            nx = u[1] * w[2] - u[2] * w[1]
            ny = u[2] * w[0] - u[0] * w[2]
            ca = math.atan2(cy, cx)
            ap = min(aps, key=lambda a, ca=ca: min(
                abs(0.5 * (a.a0 + a.a1) - ca - k * 2.0 * math.pi)
                for k in (-1, 0, 1)))
            am, rm = 0.5 * (ap.a0 + ap.a1), 0.5 * (ap.r_in + ap.r_out)
            if nx * (rm * math.cos(am) - cx) + ny * (rm * math.sin(am) - cy) <= 0:
                wrong += 1
    check("every throat face is wound to be seen from inside the tunnel",
          wrong == 0,
          f"{wrong} of {sum(len(g_yes.get(g, ())) for g in (GROUP_THROAT, GROUP_LIP))} "
          f"throat triangles face outward")

    arc, rad = loop_extent(buckets[0])
    want_arc = ap0.a1 - ap0.a0
    jitter = schema.get("hull_plating", {}).get("depth_m", 0.0)
    check("the rim is the size of the mouth it stands for",
          abs(arc - want_arc) < 1e-6
          and abs(rad - (ap0.r_out - ap0.r_in)) <= 2.0 * jitter + 1e-6,
          f"{math.degrees(arc):.4f} deg x {rad:.2f} m against "
          f"{math.degrees(want_arc):.4f} deg x "
          f"{ap0.r_out - ap0.r_in:.2f} m (+/- {2 * jitter:.1f} m of plating)")

    n_no = len(t_no)
    n_yes = len(t_yes)
    print(f"\n  lathe {n_no:,} -> {n_yes:,} triangles "
          f"({n_yes - n_no:+,}), {len(op)} open edges on "
          f"{len(aps)} rims")

    # -- negative controls -------------------------------------------------
    # Every gate above has to be able to fail, and the only proof of that is
    # to break the geometry three different ways and watch each one fire.
    print("\n  negative controls:")

    # NC1: cut the hull and build no throats. The hull's own hole boundary is
    # then open, and it is nowhere near the mouth plane.
    v_a, g_a, _, _, _ = gh.build(64, 1, apertures=aps, throats=False)
    op_a, _ = ik.boundary_edges(v_a, [t for g in g_a.values() for t in g])
    _, stray_a = classify_open_edges(aps, v_a, op_a)
    check("NC1 a cut with no throat is caught",
          len(stray_a) > 0,
          f"{len(op_a)} open edges, {len(stray_a)} off the mouths")

    # NC2: move one aperture half a plate column off its own angle, so the cut
    # no longer lands on the refined columns the throat is welded to. This is
    # the failure a hand-placed hole would have.
    half_col = math.pi / 64
    bad = list(aps)
    bad[0] = Aperture(ap0.key, ap0.index, ap0.a0 + half_col, ap0.a1 + half_col,
                      ap0.r_in, ap0.r_out, ap0.z_mouth, ap0.z_out, ap0.z_in)
    v_b, g_b, _, _, _ = gh.build(64, 1, apertures=aps, cut_with=tuple(bad))
    op_b, _ = ik.boundary_edges(v_b, [t for g in g_b.values() for t in g])
    buck_b, stray_b = classify_open_edges(aps, v_b, op_b)
    check("NC2 a hole cut off its own edges is caught",
          bool(stray_b) or not all(loop_is_closed(buck_b[i])
                                   for i in range(len(aps))),
          f"{len(stray_b)} stray edges, "
          f"{sum(1 for i in buck_b if not loop_is_closed(buck_b[i]))} "
          f"ragged rims")

    # NC3: throats built, hull not cut. Every throat is then buried in solid
    # hull -- no stray open edges, because the rims are still the rims, but the
    # surface is non-manifold where the throat crosses the skin. The gate that
    # catches this is the manifold one, and this proves that gate is not inert.
    v_c, g_c, _, _, _ = gh.build(64, 1, apertures=aps, cut_with=())
    _, nm_c = ik.boundary_edges(v_c, [t for g in g_c.values() for t in g])
    check("NC3 a throat through an uncut hull is caught",
          bool(nm_c), f"{len(nm_c)} non-manifold edges")

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
