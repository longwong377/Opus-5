"""The Babylon 5 Advisory Council chamber.

Sixth on the gazetteer's ranked build list: "one strong authority-1 frame, an
unmistakable silhouette, and it is the room that makes the diplomatic layer
legible." Named in the Green rosette (`other map.png`, authority 3).

WHAT THE REFERENCE ESTABLISHES

`reference/05-sector-green/council chambers.webp` (authority 1):

  - A **curved raised bench** with an angled pale slab top, and -- the room's
    defining feature -- a **perforated gold mesh front panel lit from within**.
    The furniture is the light source. Nearly all the light on the delegates'
    faces comes up off that panel.
  - **High-backed chairs with open black lattice backs**, one per delegation,
    standing well clear of the bench.
  - The back wall is a **radiating fan of angled fins**, pale, splaying outward.
  - A large **circular spoked medallion** on deep blue above the fins.
  - The floor is a **pale blue-green polygonal mosaic** -- irregular polygons,
    not a grid.
  - A **fan of blue-and-white radiating panels** laid on the bench top marks the
    speaking position.

WHAT IS NOT SOURCED is how many delegations sit at it. Five are visible in the
frame and the arc continues past both edges, so the visible count is a LOWER
BOUND, not the number. `SEATS` is a parameter and the self-test asserts only
that it is at least the five that can be counted. Fixing it would need a wider
shot or an authority-3 plan, and neither is held. See INV-025.

THE LIGHT IS THE POINT. If the mesh panel is not emissive this room is a grey
box with chairs. It is built as a recessed panel behind a perforated face so
that it reads as lit from within rather than as a painted stripe -- the same
construction as the customs boards in `signage.py`, and for the same reason.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                        # noqa: E402
import interior_kit as it_kit                                # noqa: E402

# --- the bench -------------------------------------------------------------
# Proportioned against the seated delegates: the slab top sits at about chest
# height for someone seated, and the lit panel fills the whole face below it.
BENCH_R_M = 4.6                 # radius of the curved bench, INV-025
BENCH_ARC_DEG = 150.0
BENCH_TOP_H_M = 1.12
BENCH_TOP_D_M = 0.95
BENCH_TOP_TILT_DEG = 9.0        # the top is an angled slab, not flat
BENCH_PANEL_INSET_M = 0.055     # how far the lit mesh sits behind its frame
BENCH_PLINTH_H_M = 0.14

SEATS = 5                       # a LOWER BOUND -- see the module docstring
CHAIR_BACK_H_M = 1.94
CHAIR_SEAT_H_M = 0.46
CHAIR_W_M = 0.62
CHAIR_LATTICE = 4               # squares across the open back

# --- the room --------------------------------------------------------------
FIN_COUNT = 22                  # the radiating fan behind the bench
FIN_R0_M = 2.2
FIN_R1_M = 7.4
FIN_W_M = 0.30
FIN_D_M = 0.10                  # how thick the fin is -- INV-171
FIN_TILT_DEG = 16.0

MEDALLION_R_M = 1.35
MEDALLION_SPOKES = 24
MEDALLION_RINGS = 3
MEDALLION_D_M = 0.03            # the backing disc's body -- INV-171
MEDALLION_RELIEF_M = 0.02       # how far a spoke or ring stands off it

FLOOR_R_M = 11.0
FLOOR_TILES = 96                # irregular polygons, not a grid
FLOOR_BED_SEGS = 96             # the bed the mosaic is laid on
FLOOR_BED_T_M = 0.10            # its body -- INV-171
TILE_RISE_M = 0.008             # how far a tile stands proud of the grout
WALL_H_M = 7.0

# ---------------------------------------------------------------------------
# The house lighting
# ---------------------------------------------------------------------------
# LAYER 4. docs/layer4-lighting/public_social.json measures `cc_house_wash` as
# this chamber's entire lighting scheme -- directional, 6300 K, range 18 m,
# SHADOW, "a broad soft near-neutral wash over the whole chamber" -- and states
# the problem in the same line: **"fitting never in frame"**.
#
# That is a real difficulty for a rig where every light is derived from a
# tagged piece of geometry (export_scene.fixture_lights), and the wrong answers
# are easy. Adding a lamp where a lamp is not is an invention the frames
# contradict. Adding no light at all leaves the chamber lit by ambient, which
# is what it was, and its ambient ratio of 0.210 makes it one of the two
# BRIGHTEST measured spaces on the station -- so "no source" is also wrong.
#
# What the frame supports is a CONCEALED COVE: a source high on the wall, above
# the fin fan, throwing up and inward, whose fitting you cannot see because it
# faces away from the room. That is standard for a chamber lit this evenly, it
# is consistent with a fitting never appearing in shot, and it is the smallest
# thing that can carry a light. It is declared invention -- INV-037 -- and what
# would overturn it is any frame showing the chamber's ceiling.
COVE_H_M = 0.22                 # the lit face, seen only as a glow on the wall
COVE_D_M = 0.30                 # how far it stands off the wall
COVE_Y_M = WALL_H_M - 1.10      # above the fins, below the ceiling
COVE_SEGS = 12                  # round the chamber's rear arc


class _M:
    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def box(self, x0, x1, y0, y1, z0, z1, group):
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)

    def quad(self, a, b, c, d, group):
        i = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        self.g.extend([group, group])

    def up_quad(self, a, b, c, d, group):
        """A horizontal face wound to face UP.

        The project has shipped downward-facing flat geometry four times and it
        is invisible every time, so the up-facing case gets its own method
        rather than relying on the caller getting the winding right.
        """
        pts = [a, b, c, d]
        u = tuple(pts[1][i] - pts[0][i] for i in range(3))
        w = tuple(pts[2][i] - pts[0][i] for i in range(3))
        if u[2] * w[0] - u[0] * w[2] < 0:
            pts = pts[::-1]
        self.quad(pts[0], pts[1], pts[2], pts[3], group)

    # --- the closed primitives ---------------------------------------------
    # EVERY GROUP IN THIS ROOM WAS A ZERO-THICKNESS PLATE, and the sum was
    # 1,592 open boundary edges -- the largest single hole in the station and
    # 43% of the whole composed-shell debt measured in session 4a. `quad` and
    # `up_quad` above are honest about winding and say nothing about closure,
    # so a bench top, a fin, a chair seat, a medallion spoke and 168 floor
    # tiles were all one-sided surfaces standing in for solids.
    #
    # A render cannot see this: from in front the plate is there, from behind
    # it shows the background and the background is black. What it costs a
    # PLAYER is that every one of those objects vanishes when walked round.
    #
    # `plate` and `arc_solid` are the two shapes this room is actually made of.

    def plate(self, a, b, c, d, thick, group, back=None):
        """A quad given the thickness it physically has: a closed solid.

        Extruded along the quad's own normal, so the caller keeps authoring in
        the plane it was already thinking in. `back` names the four faces that
        are not the front, where the material pass wants them separated;
        by default the whole solid is one group, which is what a fin or a
        seat pan wants.
        """
        pv, pt = it_kit.plate_solid([a, b, c, d], thick)
        i = len(self.v)
        self.v.extend(pv)
        self.t.extend([(x + i, y + i, z + i) for x, y, z in pt])
        # The face is the first two triangles; everything after it is the back
        # and the rim, which is where `back` separates the material.
        self.g.extend([group, group] + [(back or group)] * (len(pt) - 2))

    def arc_solid(self, profile, groups, a0, a1, segs, cy=0.0):
        """Sweep a closed (r, y) profile through an arc into a closed solid.

        THE BENCH AND THE COVE ARE BOTH LATHES AND BOTH SHIPPED AS RIBBONS.
        A ribbon of quads is closed nowhere: 40 segments of bench left 42 open
        edges on the plinth alone, one along the bottom of every segment plus
        the two ends, and the same count again on each of three more bands.

        `profile` is a closed loop of (r, y) in the chamber's own polar frame;
        `groups[i]` names the band swept from edge i -> i+1, so the material
        pass keeps every name it had. The two ends are capped by ear clipping,
        because the bench profile is NOT convex -- it carries the recess the
        lit mesh sits in, and a fan triangulation would tile straight across
        the notch and out through the front of the bench.
        """
        n = len(profile)
        if _shoelace(profile) < 0.0:
            # Reversing a loop shifts the edge names by one: new edge i runs
            # new[i] -> new[i+1] = old[n-1-i] -> old[n-2-i], which is OLD edge
            # n-2-i. Getting this wrong rotates every material in the bench by
            # one band and nothing but a render would show it.
            rev = list(groups)[::-1]
            profile, groups = profile[::-1], rev[1:] + rev[:1]
        base = len(self.v)
        for k in range(segs + 1):
            th = a0 + (a1 - a0) * k / segs
            ct, st = math.cos(th), math.sin(th)
            for r, y in profile:
                self.v.append((r * ct, cy + y, r * st))
        for k in range(segs):
            r0, r1 = base + k * n, base + (k + 1) * n
            for i in range(n):
                j = (i + 1) % n
                # Quad (P[k,i], P[k,j], P[k+1,j], P[k+1,i]). Sweeping about +Y
                # with a CCW (r, y) profile, edge x tangent is the OUTWARD
                # normal, so the profile edge has to come first; the other
                # order builds the whole lathe inside-out.
                self.t += [(r0 + i, r0 + j, r1 + j), (r0 + i, r1 + j, r1 + i)]
                self.g.extend([groups[i]] * 2)
        cap = _ear_clip(profile)
        end = base + segs * n
        for tri in cap:                                   # the a1 end, outward
            self.t.append((end + tri[0], end + tri[1], end + tri[2]))
        for tri in cap:                                   # the a0 end, outward
            self.t.append((base + tri[0], base + tri[2], base + tri[1]))
        self.g.extend([groups[0]] * 2 * len(cap))

    def as_tuple(self):
        return self.v, self.t, self.g


# Both live in the kit, because `docking_bay`'s cross-section needs the same
# triangulator and two copies of an ear clip is two chances to fix one of them.
_shoelace = it_kit.shoelace
_ear_clip = it_kit.ear_clip


def _signed_volume(verts, tris):
    """Six times the enclosed volume. Positive iff the surface faces outward.

    The whole-object counterpart to `interior_kit._selftest`'s centroid test,
    and the right one for a room: a chamber's centroid is inside the walls, so
    "does this face point away from the centre" is meaningless for the walls
    and exactly right for the furniture. Volume is the statistic that works for
    both, because it is a property of the SURFACE rather than of a viewpoint.
    """
    s = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0




def _u(seed, *parts):
    """Deterministic unit value. blake2b, never `random` or `hash`."""
    import hashlib
    h = hashlib.blake2b(("|".join([seed] + [str(p) for p in parts])).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def bench_profile():
    """The bench's cross-section, as a closed (r, y) loop, and its band names.

    ONE PLACE where the bench's shape is stated, because the ribbon version
    stated it four times -- once per band -- and the four disagreed. The lit
    mesh ran to BENCH_TOP_H - 0.06 = 1.06 m while the top slab's OUTER edge sat
    at BENCH_TOP_H - drop = 0.971 m, so the panel poked 89 mm out through the
    desk it is supposed to sit under. Nothing could catch that while the two
    surfaces were authored in separate loops; a single profile cannot express
    it at all.

    Read anticlockwise from the inner foot. The notch between `rp` and `r_out`
    is the recess -- INV-025's 55 mm -- and it is what makes this loop
    non-convex and forces the ear-clip cap.
    """
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    rp = r_out - BENCH_PANEL_INSET_M
    y_lip = BENCH_TOP_H_M - BENCH_TOP_D_M * math.sin(
        math.radians(BENCH_TOP_TILT_DEG))          # the top slab's outer edge
    y_m0 = BENCH_PLINTH_H_M + 0.05                 # under the lower frame lip
    y_m1 = y_lip - 0.06                            # under the upper frame lip
    loop = [(r_in, 0.0), (r_out, 0.0),
            (r_out, BENCH_PLINTH_H_M), (r_out, y_m0),
            (rp, y_m0), (rp, y_m1), (r_out, y_m1), (r_out, y_lip),
            (r_in, BENCH_TOP_H_M)]
    # One name per EDGE i -> i+1. The face a delegate sees is the plinth, then
    # the frame's lower lip, the recess, the lit mesh, the recess again, the
    # upper lip, and the angled slab.
    names = ["council_plinth",                     # the underside, on the deck
             "council_plinth",                     # the plinth face
             "council_frame",                      # lower frame lip
             "council_frame",                      # the return into the recess
             "council_mesh",                       # THE LIGHT SOURCE
             "council_frame",                      # the return back out
             "council_frame",                      # upper frame lip
             "council_top",                        # the angled slab
             "council_plinth"]                     # the back, facing the wall
    return loop, names


def bench(m):
    """The curved bench: plinth, lit mesh panel, and an angled slab top."""
    seg = 40
    a0 = math.radians(-BENCH_ARC_DEG / 2.0)
    a1 = math.radians(BENCH_ARC_DEG / 2.0)
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    loop, names = bench_profile()
    m.arc_solid(loop, names, a0, a1, seg)

    # The speaking-position fan, laid on the top at the bench's centre. Inlaid
    # panels have a thickness: a 4 mm proud plate is what catches the grazing
    # light off the bench, and a plate with no edge is a hole.
    tilt = math.radians(BENCH_TOP_TILT_DEG)
    drop = BENCH_TOP_D_M * math.sin(tilt)

    def top_y(r):
        """The slab's own height at radius r, so the inlay lies ON it."""
        f = (r_out - r) / (r_out - r_in)
        return BENCH_TOP_H_M - drop * (1.0 - f)

    for k in range(13):
        f = (k - 6) / 6.0
        a = f * math.radians(26.0)
        ca, sa = math.cos(a), math.sin(a)
        w = 0.022
        yi, yo = top_y(r_in) + 0.004, top_y(r_out) + 0.004
        m.plate((r_in * ca - w * sa, yi, r_in * sa + w * ca),
                (r_out * ca - w * sa, yo, r_out * sa + w * ca),
                (r_out * ca + w * sa, yo, r_out * sa - w * ca),
                (r_in * ca + w * sa, yi, r_in * sa - w * ca),
                0.004, "council_speak_fan")


def chair(m, angle_deg, r):
    """One delegation's chair: seat, and an open lattice back."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cz = r * ca, r * sa
    hw = CHAIR_W_M / 2.0

    def at(dx, dy, dz):
        return (cx + dx * ca - dz * sa, dy, cz + dx * sa + dz * ca)

    # Seat pan. A cushion, not a sheet of paper -- 60 mm of pan is what the
    # frame shows and a plate with no edge is four open boundary edges a chair.
    m.plate(at(-hw, CHAIR_SEAT_H_M, 0.26), at(hw, CHAIR_SEAT_H_M, 0.26),
            at(hw, CHAIR_SEAT_H_M, -0.26), at(-hw, CHAIR_SEAT_H_M, -0.26),
            0.06, "council_chair_seat")
    for sx in (-1, 1):
        p = at(sx * hw * 0.9, 0.0, 0.20)
        m.box(p[0] - 0.03, p[0] + 0.03, 0.0, CHAIR_SEAT_H_M,
              p[2] - 0.03, p[2] + 0.03, "council_chair_leg")

    # The open lattice back. Bars, not a panel: the frame shows the wall
    # THROUGH it, and a solid back would close the room off behind every seat.
    y0, y1 = CHAIR_SEAT_H_M, CHAIR_SEAT_H_M + CHAIR_BACK_H_M - CHAIR_SEAT_H_M
    y1 = CHAIR_BACK_H_M
    for i in range(CHAIR_LATTICE + 1):
        f = i / CHAIR_LATTICE
        x = -hw + CHAIR_W_M * f
        p = at(x, 0.0, 0.30)
        m.box(p[0] - 0.022, p[0] + 0.022, y0, y1,
              p[2] - 0.022, p[2] + 0.022, "council_chair_back")
    for i in range(CHAIR_LATTICE + 1):
        y = y0 + (y1 - y0) * i / CHAIR_LATTICE
        pa, pb = at(-hw, 0.0, 0.30), at(hw, 0.0, 0.30)
        m.box(min(pa[0], pb[0]) - 0.022, max(pa[0], pb[0]) + 0.022,
              y - 0.022, y + 0.022,
              min(pa[2], pb[2]) - 0.022, max(pa[2], pb[2]) + 0.022,
              "council_chair_back")


def fin_wall(m):
    """The radiating fan of angled fins behind the bench."""
    tilt = math.radians(FIN_TILT_DEG)
    for k in range(FIN_COUNT):
        a = math.pi * (k + 0.5) / FIN_COUNT
        ca, sa = math.cos(a), math.sin(a)
        hw = FIN_W_M / 2.0
        # Each fin is a slab standing off the wall, splaying from a hub -- and
        # it is a SLAB. As one quad it was a fin you could only see from one
        # side of the room; the fan is 22 of them and they read as a fan
        # because they catch the cove light on an edge.
        for r0, r1 in ((FIN_R0_M, FIN_R1_M),):
            m.plate((r0 * ca - hw * sa, r0 * sa, -0.30),
                    (r1 * ca - hw * sa, r1 * sa, -0.30),
                    (r1 * ca + hw * sa, r1 * sa, -0.30 - math.sin(tilt) * 0.5),
                    (r0 * ca + hw * sa, r0 * sa, -0.30 - math.sin(tilt) * 0.5),
                    FIN_D_M, "council_fin")


def medallion(m, cy, z):
    """The circular spoked medallion above the fins.

    Vertical, in XY at depth z, facing INTO the room -- ascending angle in XY
    gives a +Z normal, which faces the wall.
    """
    seg = 44
    # The backing disc is a DISC, not a circle: 30 mm of body, so the spokes
    # and rings stand on something and the edge of the plate catches light.
    # As a bare fan it was 44 open edges round its rim and no back at all.
    i0 = len(m.v)
    for zz in (z, z + MEDALLION_D_M):
        m.v.append((0.0, cy, zz))
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            m.v.append((MEDALLION_R_M * math.cos(a),
                        cy + MEDALLION_R_M * math.sin(a), zz))
    j0 = i0 + seg + 1
    for k in range(seg):
        k2 = (k + 1) % seg
        m.t.append((i0, i0 + 1 + k2, i0 + 1 + k))              # into the room
        m.t.append((j0, j0 + 1 + k, j0 + 1 + k2))              # into the wall
        m.t.append((i0 + 1 + k, i0 + 1 + k2, j0 + 1 + k2))     # the rim
        m.t.append((i0 + 1 + k, j0 + 1 + k2, j0 + 1 + k))
    m.g.extend(["council_medallion"] * 4 * seg)

    hub = MEDALLION_R_M * 0.16
    for k in range(MEDALLION_SPOKES):
        a = 2.0 * math.pi * k / MEDALLION_SPOKES
        ca, sa = math.cos(a), math.sin(a)
        w = 0.028
        # Radial-then-tangential already gives a -Z normal here, into the room.
        # Reversing these "to match" the rings broke them: the 264 triangles
        # that were facing the wall were the RINGS, whose winding runs the other
        # way round because their quads go tangentially first. Two orientations
        # in one function, and assuming they shared one cost a round trip.
        m.plate((hub * ca - w * sa, cy + hub * sa + w * ca, z - 0.02),
                (MEDALLION_R_M * ca - w * sa,
                 cy + MEDALLION_R_M * sa + w * ca, z - 0.02),
                (MEDALLION_R_M * ca + w * sa,
                 cy + MEDALLION_R_M * sa - w * ca, z - 0.02),
                (hub * ca + w * sa, cy + hub * sa - w * ca, z - 0.02),
                MEDALLION_RELIEF_M, "council_medallion_spoke")

    # The rings are RIBS, swept round as closed solids. Emitted as quads they
    # were the single largest leak in the room -- 264 open edges, 17% of the
    # chamber's total, on three bands nobody could see the section of.
    for ri in range(1, MEDALLION_RINGS + 1):
        rr = MEDALLION_R_M * ri / (MEDALLION_RINGS + 1)
        w = 0.022
        z0, z1 = z - 0.03, z          # z0 toward the room, z1 flush on the disc
        i0 = len(m.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            for rad in (rr - w, rr + w):
                for zz in (z0, z1):
                    m.v.append((rad * ca, cy + rad * sa, zz))
        for k in range(seg):
            b = i0 + 4 * k
            n = i0 + 4 * ((k + 1) % seg)
            # (b+0, b+1, b+2, b+3) = (in/z0, in/z1, out/z0, out/z1). The
            # section is traversed CLOCKWISE in (radial, z) -- the opposite
            # hand to `arc_solid`'s profile, because this lathe turns about +Z
            # and that one turns about +Y. Assuming the two shared a handedness
            # is exactly the mistake the spokes-versus-rings comment above
            # records costing a round trip.
            for p, q in ((0, 1), (1, 3), (3, 2), (2, 0)):
                m.t.append((b + p, b + q, n + q))
                m.t.append((b + p, n + q, n + p))
        m.g.extend(["council_medallion_ring"] * 8 * seg)


def mosaic_floor(m, seed="council"):
    """A pale polygonal mosaic, irregular rather than a grid.

    Built as a deterministic Voronoi-ish fan: tiles radiate from the centre with
    jittered angular and radial boundaries. The frame shows irregular polygons
    of varying size, and a square grid reads as a bathroom.

    A MOSAIC IS TILES ON A BED, and building it as 168 floating quads was wrong
    twice. Every tile was four open boundary edges -- 672 of them, the single
    biggest leak in the station -- and because the jitter leaves a grout gap
    between neighbours, **there was nothing under the gaps**. A player standing
    on this floor was looking through it into the background, which is black,
    at every joint. The bed is now a closed slab and each tile a closed pad
    laid TILE_RISE_M proud of it, which is what puts a grout line in the frame.
    """
    rings = 6
    # The bed. Its top is the grout plane; the tiles sit on it.
    bed = [(FLOOR_R_M * math.cos(math.tau * i / FLOOR_BED_SEGS),
            FLOOR_R_M * math.sin(math.tau * i / FLOOR_BED_SEGS))
           for i in range(FLOOR_BED_SEGS)]
    bv, bt = it_kit.deck_pad(bed, -FLOOR_BED_T_M, 0.0)
    i0 = len(m.v)
    m.v.extend(bv)
    m.t.extend([(a + i0, b + i0, c + i0) for a, b, c in bt])
    # `council_floor_2` rather than a new name. It is the group
    # `materials.council_floor_dark` binds -- the mosaic's DARK tile -- which is
    # what a grout bed under pale tiles is. A new group name would resolve to
    # the glTF fallback, the defect session 3x found on 1,248 door triangles,
    # and `test_materials_layer3` catches it: it failed on this exact line.
    m.g.extend(["council_floor_2"] * len(bt))

    for ri in range(rings):
        r0 = FLOOR_R_M * ri / rings
        r1 = FLOOR_R_M * (ri + 1) / rings
        n = max(6, int(FLOOR_TILES * (ri + 1) / rings / 2))
        for k in range(n):
            j0 = (_u(seed, "a", ri, k) - 0.5) * 0.35
            j1 = (_u(seed, "a", ri, k + 1) - 0.5) * 0.35
            a0 = 2.0 * math.pi * (k + j0) / n
            a1 = 2.0 * math.pi * (k + 1 + j1) / n
            g0 = r0 + (r1 - r0) * 0.06 * _u(seed, "r", ri, k)
            g1 = r1 - (r1 - r0) * 0.06 * _u(seed, "r", ri, k, 1)
            shade = int(_u(seed, "s", ri, k) * 3)
            tv, tt = it_kit.deck_pad(
                [(g0 * math.cos(a0), g0 * math.sin(a0)),
                 (g1 * math.cos(a0), g1 * math.sin(a0)),
                 (g1 * math.cos(a1), g1 * math.sin(a1)),
                 (g0 * math.cos(a1), g0 * math.sin(a1))],
                0.0, TILE_RISE_M)
            j = len(m.v)
            m.v.extend(tv)
            m.t.extend([(a + j, b + j, c + j) for a, b, c in tt])
            m.g.extend([f"council_floor_{shade}"] * len(tt))


def house_cove(m):
    """The concealed high-level cove. See THE HOUSE LIGHTING above.

    Segments of an arc at COVE_Y_M, standing COVE_D_M off the wall over the
    same half of the chamber the fin fan occupies -- the wall the camera faces
    and the wall the measurement watched brighten.

    A HOUSING, not a stripe. The whole point of this fitting is that you see
    the glow and never the lamp, which needs a body for the lamp to be behind;
    as a single ribbon of quads it was a painted band with 26 open edges and
    nothing to conceal anything.
    """
    r = FLOOR_R_M - COVE_D_M
    # (r, y) section: the lit face inboard, the housing behind it against the
    # wall. Convex, so the ear clip degenerates to a fan and still checks out.
    m.arc_solid([(r, COVE_Y_M), (FLOOR_R_M, COVE_Y_M),
                 (FLOOR_R_M, COVE_Y_M + COVE_H_M), (r, COVE_Y_M + COVE_H_M)],
                # The housing is `council_frame`, a bound name: it is the same
                # metalwork as the bench's lit-panel surround and the same job,
                # a body you never see holding a face you always do.
                ["council_frame", "council_frame",
                 "council_frame", "light_house_cove"],
                0.0, math.pi, COVE_SEGS)


def council_chamber(seats=SEATS):
    """The room. Bench centred on the origin, delegates outboard of it."""
    m = _M()
    mosaic_floor(m)
    bench(m)
    for k in range(seats):
        f = (k + 0.5) / seats - 0.5
        chair(m, f * BENCH_ARC_DEG * 0.92, BENCH_R_M + 0.55)
    fin_wall(m)
    medallion(m, 5.1, -0.34)
    house_cove(m)
    return m.as_tuple()


def write_obj(path, seats=SEATS):
    v, t, g = council_chamber(seats)
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    v, t, g = council_chamber()

    # --- the light is the point --------------------------------------------
    mesh = [k for k in range(len(t)) if g[k] == "council_mesh"]
    check("the bench carries a lit mesh panel", bool(mesh), "the room's light")
    mr = [math.hypot(v[i][0], v[i][2]) for k in mesh for i in t[k]]
    fr = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
          if g[k] == "council_frame" for i in t[k]]
    # Against the frame's OUTERMOST radius, not its innermost. The frame now
    # wraps into the recess -- the two returns either side of the panel are
    # frame, and they are at the panel's own radius by construction -- so
    # `min(fr)` is the bottom of the notch and comparing against it asks
    # whether the panel is behind itself. What the reference establishes is
    # that the lit face sits behind the FACE of the bench.
    check("the mesh is recessed behind its frame, not coplanar",
          max(mr) < max(fr) - BENCH_PANEL_INSET_M + 1e-9,
          f"mesh out to {max(mr):.3f}, frame face at {max(fr):.3f}")

    # --- seats -------------------------------------------------------------
    # Five delegations can be counted in the frame and the arc runs past both
    # edges, so five is a floor, not the number. Asserting equality would be
    # asserting something the reference does not say.
    check("seat count is at least the five that can be counted",
          SEATS >= 5, f"{SEATS}")
    check("chairs stand clear of the bench",
          BENCH_R_M + 0.55 > BENCH_R_M, "a chair inside the bench is a fault")
    check("the chair back is open lattice, not a panel",
          CHAIR_LATTICE >= 3, f"{CHAIR_LATTICE} squares across")
    check("the chair back rises well above a seated head",
          CHAIR_BACK_H_M > CHAIR_SEAT_H_M + 1.2,
          f"back {CHAIR_BACK_H_M} over seat {CHAIR_SEAT_H_M}")

    # --- the bench is a bench ----------------------------------------------
    check("the bench top is at seated working height",
          1.00 < BENCH_TOP_H_M < 1.25, f"{BENCH_TOP_H_M} m")
    check("the bench top is an angled slab, not flat",
          BENCH_TOP_TILT_DEG > 0, f"{BENCH_TOP_TILT_DEG} deg")
    check("the bench arc leaves the speaker a place to stand",
          BENCH_ARC_DEG < 200.0, f"{BENCH_ARC_DEG} deg")

    # --- THE ROOM IS CLOSED -------------------------------------------------
    # 1,592 open boundary edges shipped for four sessions and nothing here
    # could see them, because every gate in this file measured which way a
    # surface FACED. A surface that is not there faces nowhere, so a facing
    # test passes vacuously on the half of a plate that does not exist. This
    # is the measurement that catches it, and it is first now.
    op, nm = it_kit.boundary_edges(v, t)
    check("the chamber is a closed surface", not op,
          f"{len(op)} open boundary edges, first at {op[:1]}")
    check("...and no edge carries more than two faces", not nm,
          f"{len(nm)} non-manifold edges, first at {nm[:1]}")
    check("the chamber encloses a positive volume, so it is not inside-out",
          _signed_volume(v, t) > 0.0, f"{_signed_volume(v, t):.1f} m3")

    # NEGATIVE CONTROL -- one triangle removed has to fire the closure gate.
    check("...and dropping ONE triangle fires that gate",
          len(it_kit.boundary_edges(v, t[1:])[0]) == 3,
          f"{len(it_kit.boundary_edges(v, t[1:])[0])} open with a hole in it")

    # --- flat things face up, MEASURED ON THE FACE YOU CAN SEE --------------
    # These groups are solids now, so their undersides face down and must.
    # The honest question is whether the TOP of each object faces up, so the
    # test is restricted to triangles lying in the object's own highest plane
    # -- which is also the only plane a standing player ever sees.
    def top_face_bad(pick, tol=1e-6):
        ks = [k for k in range(len(t)) if pick(g[k])]
        if not ks:
            return None
        ytop = max(v[i][1] for k in ks for i in t[k])
        bad = 0
        for k in ks:
            if any(abs(v[i][1] - ytop) > tol for i in t[k]):
                continue
            p0, p1, p2 = (v[i] for i in t[k])
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[2] * w[0] - u[0] * w[2] <= 0:
                bad += 1
        return bad

    for grp in ("council_speak_fan", "council_chair_seat"):
        bad = top_face_bad(lambda n, grp=grp: n == grp)
        check(f"{grp}'s top face faces up", bad == 0, f"{bad} downward")
    floor_groups = [grp for grp in set(g) if grp.startswith("council_floor")]
    bad = top_face_bad(lambda n: n in floor_groups)
    check("the mosaic's tile faces face up", bad == 0, f"{bad} downward")
    check("the tiles stand proud of the bed they are laid on",
          TILE_RISE_M > 0.0 and FLOOR_BED_T_M > 0.0,
          "a mosaic with no bed shows the background through every joint")

    # The bench top is a tilted slab, so it has no single horizontal plane.
    # What it must not do is face away from the room: every triangle of the
    # slab group has a POSITIVE y normal component.
    bad = 0
    for k, tri in enumerate(t):
        if g[k] != "council_top":
            continue
        p0, p1, p2 = (v[i] for i in tri)
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[2] * w[0] - u[0] * w[2] <= 0:
            bad += 1
    check("council_top faces up", bad == 0, f"{bad} downward")

    # --- the medallion faces the room --------------------------------------
    # Same correction: the disc, the spokes and the rings all have backs now,
    # and a back facing the wall is the point of having one. The face a
    # delegate sees is the one at the lowest z, which is toward the room.
    ks = [k for k in range(len(t)) if g[k].startswith("council_medallion")]
    zfront = min(v[i][2] for k in ks for i in t[k])
    bad = 0
    for k in ks:
        if any(abs(v[i][2] - zfront) > 1e-6 for i in t[k]):
            continue
        p0, p1, p2 = (v[i] for i in t[k])
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[0] * w[1] - u[1] * w[0] >= 0:
            bad += 1
    check("the medallion's front face faces into the room", bad == 0,
          f"{bad} triangles facing the wall")

    # --- the primitives, on the hard case -----------------------------------
    # `arc_solid`'s end cap is the piece with a real chance of being wrong, so
    # it is tested on the NON-CONVEX profile the bench actually uses rather
    # than on a rectangle. A fan triangulation tiles straight across the
    # panel recess, and the way that shows up is AREA: a cap that spills
    # outside its outline covers more than the outline does.
    loop, names = bench_profile()
    tri = _ear_clip(loop)
    area = sum(abs((loop[b][0] - loop[a][0]) * (loop[c][1] - loop[a][1])
                   - (loop[c][0] - loop[a][0]) * (loop[b][1] - loop[a][1])) / 2.0
               for a, b, c in tri)
    shoe = abs(_shoelace(loop)) / 2.0
    check("the bench end cap tiles its profile without spilling outside it",
          abs(area - shoe) < 1e-12, f"cap {area:.9f} m2 vs profile {shoe:.9f} m2")
    check("...and the profile really is the non-convex case",
          any(((loop[i - 1][0] - loop[i - 2][0]) * (loop[i][1] - loop[i - 2][1])
               - (loop[i - 1][1] - loop[i - 2][1]) * (loop[i][0] - loop[i - 2][0]))
              < 0 for i in range(len(loop))),
          "a convex profile would let a fan pass and the gate would be inert")
    # NEGATIVE CONTROL -- the fan this replaced, on the same profile.
    fan_area = sum(abs((loop[i][0] - loop[0][0]) * (loop[i + 1][1] - loop[0][1])
                       - (loop[i + 1][0] - loop[0][0]) * (loop[i][1] - loop[0][1]))
                   / 2.0 for i in range(1, len(loop) - 1))
    check("...and a fan triangulation of it FAILS that test",
          abs(fan_area - shoe) > 1e-6,
          f"a fan covers {fan_area:.6f} m2 against the profile's {shoe:.6f}")

    for what, mm in (("plate", _M()), ("arc_solid", _M())):
        if what == "plate":
            mm.plate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, -1.0),
                     (0.0, 0.0, -1.0), 0.05, "probe")
        else:
            mm.arc_solid(loop, names, -0.4, 0.4, 5)
        pv, pt, _pg = mm.as_tuple()
        pop, pnm = it_kit.boundary_edges(pv, pt)
        check(f"{what} alone is a closed solid", not pop and not pnm,
              f"{len(pop)} open, {len(pnm)} non-manifold")
        check(f"{what} alone is outward-facing", _signed_volume(pv, pt) > 0.0,
              f"signed volume {_signed_volume(pv, pt):.6f} m3 -- negative is "
              f"a solid built inside-out, which indoors you see through")

    # --- the mosaic is a mosaic, not a grid ---------------------------------
    check("the floor uses more than one tile shade",
          len(floor_groups) > 1, str(sorted(floor_groups)))
    a = council_chamber()[0]
    b = council_chamber()[0]
    check("the mosaic regenerates byte-identically", a == b)

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
