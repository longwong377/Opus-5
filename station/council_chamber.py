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

import dressing as _dress                                    # noqa: E402
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
# INBOARD of the bench, which is where the reference puts the delegates -- see
# `council_chamber`. 0.72 m of clearance behind `r_in`, so a chair back at
# -0.30 radial still stands 0.42 m clear of the bench it is drawn up to.
CHAIR_R_M = BENCH_R_M - BENCH_TOP_D_M - 0.72
CHAIR_BACK_H_M = 1.94
CHAIR_SEAT_H_M = 0.46
CHAIR_W_M = 0.62
CHAIR_LATTICE = 4               # squares across the open back

# --- the room --------------------------------------------------------------
# THE FAN AND THE MEDALLION WERE IN A PLANE NO CAMERA CAN SEE THEM FROM, and
# that is why this room could not be photographed. Measured off the built mesh
# in session 4p, before anything was changed:
#
#     council_fin          x -7.39..7.40  y 0.06..7.38  z -0.44..-0.21
#     council_plinth       x  0.94..4.60  y 0.00..1.12  z -4.44.. 4.44
#     council_fin_backing  x -11.60..11.60 y 0.00..7.00 z -0.91..11.38
#
# The fan is a vertical fan in the plane z = -0.3 radiating from the ORIGIN,
# which is the centre of the bench's arc -- so it stands in the middle of the
# room rather than behind anybody, and the bench, which sweeps +/-75 degrees
# about that same origin, passes STRAIGHT THROUGH IT: both solids occupy
# x 0.94..4.60, y 0.06..1.12, z -0.44..-0.21. So does the flat backing plate at
# z = -0.75. Two interpenetrations, which AAA-STANDARD calls blocking, and
# neither module gate could see them because every assertion in this file
# measures ONE object against ITSELF -- closure, winding, signed volume -- and
# `docs/AAA-STANDARD.md` R5 names exactly this: "cross-subsystem clearance is
# asserted wherever two systems occupy the same space", the tram-through-spoke
# defect, one file down.
#
# It also made the reference unreproducible. `council chambers.webp` is taken
# from the chamber floor: the bench is convex toward the lens, the delegates
# are BEHIND it, and the fan and the medallion are behind THEM. A fan in the
# plane z = -0.3 is edge-on from every point on the +x axis, so the composition
# the room exists for could not be framed from anywhere.
#
# The fan now stands on a flat SCREEN WALL behind the delegates -- the plane
# x = FAN_X_M, facing +x, hub on the floor at z = 0 -- which is what the frame
# shows and which is clear of the bench (min x 0.94) by 2.0 m.
FAN_X_M = -1.05                 # the screen wall's face, behind the chairs
FAN_WALL_T_M = 0.34
FAN_WALL_HZ_M = 9.20            # half-length of the screen wall along z
FAN_FIELD_T_M = 0.024           # the blue field's own body -- INV-171

FIN_COUNT = 30                  # the radiating fan behind the bench
# 0.9, not 2.2. The blades converge on the hub in the reference; at 2.2 m they
# leave a 4.4 m disc of bare field in the middle of the fan, which in the
# render is the single largest patch of blue in the frame. Pitch at the hub is
# pi*0.9/30 = 94 mm, so FIN_TAPER is set so a blade is 87 mm there and the
# blades nearly touch WITHOUT overlapping -- two solids sharing space is the
# defect this session opened by finding the bench inside the fan.
FIN_R0_M = 0.9
# 6.35, not 7.4. The fan radiates from a hub on the floor, so its outer radius
# IS its height, and the chamber now has a ceiling at WALL_H_M. A fin reaching
# 7.4 m through a 7.0 m ceiling is the same defect one line up.
FIN_R1_M = 6.35
FIN_W_M = 0.62                  # at the rim; FIN_TAPER of that at the hub
FIN_TAPER = 0.14
FIN_D_M = 0.10                  # how thick the fin is -- INV-171
FIN_TILT_DEG = 16.0
FIN_STANDOFF_M = 0.03           # how far a fin stands off the blue field

MEDALLION_R_M = 1.35
MEDALLION_Y_M = 4.60            # centre height, on the fan and under the cove
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

# THE PANEL IS PERFORATED AND IT WAS A SMOOTH BAND. The reference's one
# defining sentence about this room -- quoted at the top of this file since it
# was written -- is "a perforated gold mesh front panel lit from within: the
# furniture is the light source", and what was built is a flat emissive strip
# in the bench profile. `docs/judge-4e.md`: "the bench is a plain white slab
# where the reference's defining feature is a perforated gold mesh front
# panel". A material can make a band gold; only geometry can make it
# perforated, and the difference is what the eye uses to tell a lit panel from
# a light BEHIND a panel.
#
# Built as a grille standing in the 55 mm recess the panel already sits in:
# vertical bars at a pitch read off the frame as roughly one bar per 90 mm of
# a 12 m bench, crossed by two horizontal rails. It is `signage.board()`'s own
# construction -- "the frame casts a shadow onto the face, and a decal cannot"
# -- applied to the object this room exists for.
# PITCH MEASURED OFF THE FRAME RATHER THAN CHOSEN. In `council chambers.webp`
# (1000x750) the lit panel spans x 200..550 px for about 4.0 m of bench at that
# depth, i.e. 88 px/m, and the perforation reads as roughly 3 px -- 34 mm. The
# first pass used 115 mm, which at 4.0 m of bench is 35 openings and reads as a
# PICKET FENCE rather than as mesh: the eye indexes the period, which is
# AAA-STANDARD's own tiling test ("if the eye can index the period, it is CRAFT
# 3 at best"). 42 mm at a 24 mm bar is 43% open and 287 bars over the arc.
MESH_BAR_PITCH_M = 0.042
MESH_BAR_W_M = 0.024
MESH_RAILS = 6
MESH_RAIL_SEGS = 96             # the rails need arc, not the bars' resolution
MESH_STANDOFF_M = 0.018         # in front of the lit face, inside the recess

# One station per delegation. `directory.py` declares `delegate_bench` and
# `speaking_position` as this room's interactables and the bench carried
# neither: 12 m of continuous desk with nothing on it anywhere. Each station
# gets the four things a seat at a council table has -- a working pad, a
# nameplate facing the chamber, a screen, and a microphone.
STATION_PAD_W_M = 0.86
STATION_PLATE_H_M = 0.13
STATION_MIC_H_M = 0.36

# The chamber's own enclosure. `docs/judge-4e.md`: "54.05% of the frame is
# below the measurable floor and the chamber stands in an unenclosed void."
# Half of that is lighting and half is that there is genuinely nothing there:
# the fin fan radiates against black and the mosaic ends at a rim with no wall
# beyond it. Both surfaces below stay INSIDE the room's own existing extent --
# the floor disc is already FLOOR_R_M across and the fan already sits at
# z = -0.30 -- so nothing new can clash with what `deck.compose` puts around
# the room that the floor did not already clash with.
# AND IT ENCLOSED HALF A ROOM. `arc_solid(..., 0.0, math.pi, ...)` walls the
# +z semicircle only; the -z half of an 11 m floor disc had nothing round it
# and nothing over it, so at the shot this module's own registry hands the
# judge, **27.65% of the frame is below sRGB 0.01** -- measured on
# docs/craft-4p-council-before-half.png. That is the same 54% judge-4e
# reported, halved by the frame's own framing rather than by any fix.
#
# So the arc runs the whole way round, MINUS a doorway, and there is a ceiling.
# The doorway is not decoration: `bespoke.near_face_opening` measures the
# widest unobstructed run across the shell's near face at the three heights
# `deck._mouth_clear` probes, and a sealed arc returns None, which is the
# signal that the assembler cannot put a body in the room. Before this change
# that function returned a 6.61 m opening at x = 7.67 -- an accident of where
# the half-arc happened to stop, 7.67 m off the bearing `_place_local` maps
# local x = 0 onto. It is now a doorway at x = 0 because that is where the
# corridor's door is.
ARC_WALL_T_M = 0.36
ARC_WALL_SEGS = 40
WALL_PIER_PITCH_M = 1.85        # pilasters -- see the note in `enclosure`
WALL_PIER_W_M = 0.44
WALL_PIER_D_M = 0.14
WALL_JOINT_W_M = 0.10         # the mid-bay reveal -- see `enclosure`
DOOR_W_M = 4.20               # the gallery door, on the near face at x = 0
DOOR_H_M = 3.00
CEIL_T_M = 0.34
CEIL_COFFER_RINGS = 4         # so a 380 m2 ceiling is not one blank disc
CEIL_COFFER_SPOKES = 24

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
        # A FULL TURN IS A TORUS AND HAS NO ENDS. Swept 0..tau and capped like
        # an open arc, the last ring lands exactly on the first and the two ear
        # clips land on each other: 27 non-manifold edges, which this file's own
        # gate caught the first time the house cove was run right round. So the
        # closed case welds the seam and emits no caps -- and it is detected
        # from the ANGLES rather than passed in, because a caller that has to
        # remember to say `closed=True` is a caller that will forget.
        closed = abs(abs(a1 - a0) - math.tau) < 1e-9
        base = len(self.v)
        for k in range(segs if closed else segs + 1):
            th = a0 + (a1 - a0) * k / segs
            ct, st = math.cos(th), math.sin(th)
            for r, y in profile:
                self.v.append((r * ct, cy + y, r * st))
        for k in range(segs):
            r0 = base + k * n
            r1 = base + ((k + 1) % segs) * n if closed else base + (k + 1) * n
            for i in range(n):
                j = (i + 1) % n
                # Quad (P[k,i], P[k,j], P[k+1,j], P[k+1,i]). Sweeping about +Y
                # with a CCW (r, y) profile, edge x tangent is the OUTWARD
                # normal, so the profile edge has to come first; the other
                # order builds the whole lathe inside-out.
                self.t += [(r0 + i, r0 + j, r1 + j), (r0 + i, r1 + j, r1 + i)]
                self.g.extend([groups[i]] * 2)
        if closed:
            return
        cap = _ear_clip(profile)
        end = base + segs * n
        for tri in cap:                                   # the a1 end, outward
            self.t.append((end + tri[0], end + tri[1], end + tri[2]))
        for tri in cap:                                   # the a0 end, outward
            self.t.append((base + tri[0], base + tri[2], base + tri[1]))
        self.g.extend([groups[0]] * 2 * len(cap))

    def merge_xform(self, sub, fn):
        """Append another `_M`, mapping every vertex through `fn`.

        `fn` must be a PROPER rotation or the winding of everything it carries
        inverts silently -- which indoors is a surface you see through, the
        defect `_signed_volume` exists for. `_to_wall` is the only caller and
        it is a rotation by construction.
        """
        off = len(self.v)
        self.v.extend(fn(p) for p in sub.v)
        self.t.extend((a + off, b + off, c + off) for a, b, c in sub.t)
        self.g.extend(sub.g)

    def merge_spans(self, verts, tris, spans):
        """Take a `dressing`-style (verts, tris, SPANS) build into this mesh.

        `_M` tags per triangle and `dressing` tags by span. Four lines, and
        the alternative is a second vocabulary for the same nine surfaces.
        """
        off = len(self.v)
        per = [None] * len(tris)
        for nm, lo, hi in spans:
            for i in range(lo, hi):
                per[i] = nm
        self.v.extend(verts)
        self.t.extend((a + off, b + off, c + off) for a, b, c in tris)
        self.g.extend(per)

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


def mesh_grille(m):
    """The perforated screen over the lit panel. See MESH_BAR_PITCH_M.

    Bars stand in the recess `bench_profile` already cuts, at
    MESH_STANDOFF_M in front of the lit face -- so they are between the light
    and the room, which is what makes the panel read as lit from WITHIN rather
    than painted. Anything proud of `r_out` would stand outside the bench.
    """
    a0 = math.radians(-BENCH_ARC_DEG / 2.0)
    a1 = math.radians(BENCH_ARC_DEG / 2.0)
    r_out = BENCH_R_M
    rp = r_out - BENCH_PANEL_INSET_M
    rb = rp + MESH_STANDOFF_M
    y_lip = BENCH_TOP_H_M - BENCH_TOP_D_M * math.sin(
        math.radians(BENCH_TOP_TILT_DEG))
    y0 = BENCH_PLINTH_H_M + 0.05
    y1 = y_lip - 0.06
    n = max(4, int((a1 - a0) * rb / MESH_BAR_PITCH_M))
    hw = MESH_BAR_W_M / 2.0
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        ca, sa = math.cos(a), math.sin(a)
        # a bar is a plate in the tangential plane, facing OUT of the bench
        tx, tz = -sa * hw, ca * hw
        m.plate((rb * ca + tx, y1, rb * sa + tz),
                (rb * ca + tx, y0, rb * sa + tz),
                (rb * ca - tx, y0, rb * sa - tz),
                (rb * ca - tx, y1, rb * sa - tz),
                MESH_STANDOFF_M * 0.7, "council_frame")
    for j in range(MESH_RAILS):
        yy = y0 + (y1 - y0) * (j + 1) / (MESH_RAILS + 1)
        m.arc_solid([(rb - 0.006, yy - 0.012), (rb + 0.008, yy - 0.012),
                     (rb + 0.008, yy + 0.012), (rb - 0.006, yy + 0.012)],
                    ["council_frame"] * 4, a0, a1, MESH_RAIL_SEGS)


def delegate_stations(m, seats):
    """A working position for each delegation, on the bench top.

    `directory.py` declares `delegate_bench` and `speaking_position` for this
    room and the bench had neither: twelve metres of continuous desk with
    nothing on it. Pad, nameplate, screen, microphone -- which is what a seat
    at a council table has, and what `docs/judge-4e.md` means by machinery.
    """
    P = _dress._Parts("fix_")
    tilt = math.radians(BENCH_TOP_TILT_DEG)
    drop = BENCH_TOP_D_M * math.sin(tilt)
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M

    def top_y(r):
        f = (r_out - r) / (r_out - r_in)
        return BENCH_TOP_H_M - drop * (1.0 - f)

    for k in range(seats):
        f = (k + 0.5) / seats - 0.5
        a = math.radians(f * BENCH_ARC_DEG * 0.92)
        ca, sa = math.cos(a), math.sin(a)
        hw = STATION_PAD_W_M / 2.0
        ra, rb = r_in + 0.10, r_out - 0.14
        ya, yb = top_y(ra) + 0.004, top_y(rb) + 0.004

        def at(r, y, w):
            return (r * ca - w * sa, y, r * sa + w * ca)

        # The working pad, laid on the slab. Wound +w first: the other order
        # has a NEGATIVE y normal, i.e. a desk pad facing the floor, and this
        # file's own `council_top faces up` gate caught it on the first run --
        # which is the fifth time this project has authored a flat surface
        # upside down and the first time a gate said so before a render did.
        # `council_top_pad`, NOT `council_top`, and it resolves to the same
        # material because `materials.resolve` matches the longest bind
        # FRAGMENT as a substring. The distinct name is what keeps this file's
        # existing `council_top faces up` gate meaningful: that gate was
        # written for the bench slab, which is a swept ribbon whose every
        # triangle faces up, and a `plate_solid` has a back and a rim that
        # legitimately do not. Folding a solid into a ribbon's gate would have
        # forced the gate to be weakened for every surface it covers.
        m.plate(at(ra, ya, hw), at(rb, yb, hw), at(rb, yb, -hw),
                at(ra, ya, -hw), 0.006, "council_top_pad")
        # THE SCREEN AND THE NAMEPLATE SWAPPED SIDES, because the delegates
        # did -- see `council_chamber`. A screen is raked toward the person
        # who reads it, which is now the INNER edge; a nameplate faces the
        # chamber, which is now the OUTER one. Built the other way round they
        # were a screen the audience reads and a nameplate the delegate reads.
        m.plate(at(ra + 0.02, ya + 0.30, hw * 0.62),
                at(ra - 0.10, ya + 0.02, hw * 0.62),
                at(ra - 0.10, ya + 0.02, -hw * 0.62),
                at(ra + 0.02, ya + 0.30, -hw * 0.62), 0.022, P.screen)
        # the nameplate, facing the chamber across the bench's outer edge
        m.plate(at(rb + 0.06, ya + STATION_PLATE_H_M, -hw * 0.70),
                at(rb + 0.06, ya + 0.004, -hw * 0.70),
                at(rb + 0.06, ya + 0.004, hw * 0.70),
                at(rb + 0.06, ya + STATION_PLATE_H_M, hw * 0.70),
                0.018, "council_frame")
        # a microphone on a stalk, which is the one object that says the
        # people at this desk are here to speak
        rm = (ra + rb) * 0.5
        ym = top_y(rm) + 0.004
        sv, st, ss = [], [], []
        _dress._tube(sv, st, ss, P.rail, at(rm, ym, hw * 0.55),
                     at(rm - 0.05, ym + STATION_MIC_H_M, hw * 0.55),
                     0.011, _dress.SEG_BOLT)
        _dress._tube(sv, st, ss, P.rail, at(rm, ym, hw * 0.55),
                     at(rm, ym + 0.030, hw * 0.55), 0.055, _dress.SEG_PIPE)
        m.merge_spans(sv, st, ss)


def door_span():
    """(a0, a1) of the gallery doorway, in the arc wall's own polar frame.

    The near face of this shell is +z, because `bespoke._place_local` maps the
    room's local x = 0 onto the place's bearing and the corridor's door onto
    the largest z. So the doorway is centred at a = pi/2 and its width is a
    CHORD converted to an angle rather than an angle chosen to look right.
    """
    r0 = FLOOR_R_M + 0.02
    half = math.asin(min(0.98, (DOOR_W_M / 2.0) / r0))
    return math.pi / 2.0 - half, math.pi / 2.0 + half


def screen_wall(m):
    """The flat wall the fan and the medallion stand on, behind the delegates.

    See FAN_X_M. It is a slab in the plane x = FAN_X_M with a DEEP BLUE FIELD
    on its face, which is the reference's own word: "a large circular spoked
    medallion on deep blue". judge-4e logged its absence as F2 -- "the 'deep
    blue' field behind the circular spoked medallion, which is black here".

    THE FIELD'S GROUP NAME IS A MEASUREMENT, NOT A NAME MATCH, and it is worth
    being explicit because `materials.py` is not this module's to edit.
    `render_shot._material_for` takes the LONGEST rule fragment contained in a
    group name, so `signage_panel__council_field` resolves to `signage_panel`
    -- albedo (0.06, 0.062, 0.14), emission (0.151, 0.156, 0.434) at 3.0. That
    material is the backlit blue field of `signage.py`'s customs boards, and
    the construction here is the same object: a dark blue panel lit from behind
    its own frame. `materials.py` makes the same kind of bind for the same kind
    of reason on `prop_deck_marking`, and records it in the same words.
    """
    x1 = FAN_X_M
    x0 = x1 - FAN_WALL_T_M
    hz = FAN_WALL_HZ_M
    m.box(x0, x1, 0.0, WALL_H_M, -hz, hz, "council_fin_backing")
    # the field, standing proud of the wall face the way a mosaic tile stands
    # proud of its bed -- so the join is a line rather than a coincident face
    # THE FIELD IS BOUNDED BY THE FAN IT BACKS, not by the wall. Run to the
    # wall's own edges it is 17 m of lit blue and takes 32% of the frame;
    # `council chambers.webp` shows the blue as a field the fan sits in, framed
    # by structure. 0.55 m of margin outside FIN_R1_M is what the frame shows.
    fz = min(hz - 0.42, FIN_R1_M + 0.55)
    fy0, fy1 = 0.42, min(WALL_H_M - 0.34, FIN_R1_M + 0.55)
    m.plate((x1, fy1, -fz), (x1, fy0, -fz), (x1, fy0, fz), (x1, fy1, fz),
            FAN_FIELD_T_M, "signage_panel__council_field")
    # a surround, so the field is a panel set into a wall rather than paint
    for za, zb in ((-hz + 0.06, -fz - 0.03), (fz + 0.03, hz - 0.06)):
        m.box(x1, x1 + 0.06, 0.30, WALL_H_M - 0.20, za, zb, "council_frame")
    m.box(x1, x1 + 0.06, fy1 + 0.03, fy1 + 0.19, -fz - 0.03, fz + 0.03,
          "council_frame")


def ceiling(m):
    """A coffered ceiling, because a chamber with no lid renders as sky.

    A FLAT DISC WOULD HAVE MADE THE GATE WORSE WHILE MAKING THE FRAME BETTER,
    which is the trade `enclosure`'s own note below records this file already
    losing once: `station/density.py` scores VISIBLE LINE over AREA, so 380 m2
    of blank ceiling is 380 m2 of denominator. The coffers are the numerator --
    four concentric ribs and twenty-four radial ones, which is what a
    ceremonial ceiling has anyway.
    """
    # THE SLAB BEARS ON THE WALL rather than meeting it exactly. Its rim at
    # r0 = FLOOR_R_M + 0.02 and its soffit at y = WALL_H_M land on the arc
    # wall's own inner face and top, and two of those vertices coincided to the
    # micron: 2 non-manifold edges, found by this file's gate and not by a
    # render. 140 mm of bearing into a 360 mm wall is how a slab meets a wall
    # anyway.
    y0, y1 = WALL_H_M - 0.02, WALL_H_M - 0.02 + CEIL_T_M
    r = FLOOR_R_M + 0.16
    loop = [(r * math.cos(math.tau * i / FLOOR_BED_SEGS),
             r * math.sin(math.tau * i / FLOOR_BED_SEGS))
            for i in range(FLOOR_BED_SEGS)]
    cv, ct = it_kit.deck_pad(loop, y0, y1)
    i0 = len(m.v)
    m.v.extend(cv)
    m.t.extend([(a + i0, b + i0, c + i0) for a, b, c in ct])
    m.g.extend(["council_fin_backing"] * len(ct))

    # concentric ribs, hanging below the soffit
    for k in range(1, CEIL_COFFER_RINGS + 1):
        rr = r * k / (CEIL_COFFER_RINGS + 1)
        w = 0.11
        m.arc_solid([(rr - w, y0 - 0.16), (rr + w, y0 - 0.16),
                     (rr + w, y0), (rr - w, y0)],
                    ["council_frame"] * 4, 0.0, math.tau, 48)
    # radial ribs, from the inner ring out to the wall
    for k in range(CEIL_COFFER_SPOKES):
        a = math.tau * k / CEIL_COFFER_SPOKES
        ca, sa = math.cos(a), math.sin(a)
        w = 0.09
        ra = r / (CEIL_COFFER_RINGS + 1) * 0.5
        m.plate((ra * ca - w * sa, y0 - 0.13, ra * sa + w * ca),
                (r * ca - w * sa, y0 - 0.13, r * sa + w * ca),
                (r * ca + w * sa, y0 - 0.13, r * sa - w * ca),
                (ra * ca + w * sa, y0 - 0.13, ra * sa - w * ca),
                0.13, "council_frame")


def enclosure(m):
    """The surfaces that stop this chamber standing in a void, ARTICULATED.

    The arc runs the WHOLE way round now, minus the gallery doorway -- see the
    block above ARC_WALL_T_M for the measurement that forced it and for why
    the doorway is at x = 0 rather than wherever the wall happened to stop. It
    adds no extent: the arc stands 20 mm outside the mosaic's own rim and
    clear of `house_cove` at r = FLOOR_R_M.

    THE PILASTERS ARE NOT DECORATION AND THE GATE SAID SO. Built as two plain
    surfaces, this enclosure added roughly 410 m2 of blank wall and
    `station/density.py` -- which scores VISIBLE LINE over AREA -- took the
    chamber from 93.7% of its floor to 85.2%. It was already the one location
    in this session's four that FAILS layer 2b, and a bare wall made the
    number worse while making the frame better, which is exactly the trade
    that criterion exists to refuse. A 7 m wall in a ceremonial chamber has
    pilasters, a cornice and a skirt whether or not a gate is watching.
    """
    r0 = FLOOR_R_M + 0.02
    d0, d1 = door_span()
    # ONE sweep, starting and ending at the doorway, so `arc_solid`'s ear-clip
    # caps become the two jambs and the opening is closed by construction.
    a0, a1 = d1, d0 + math.tau
    segs = max(8, int(ARC_WALL_SEGS * (a1 - a0) / math.pi))
    m.arc_solid([(r0, 0.0), (r0 + ARC_WALL_T_M, 0.0),
                 (r0 + ARC_WALL_T_M, WALL_H_M), (r0, WALL_H_M)],
                ["council_fin_backing"] * 4, a0, a1, segs)
    # The head over the doorway, spanning the gap the sweep leaves. It BEARS
    # INTO THE JAMBS by half a degree at each end and stands 90 mm proud of the
    # wall face, and both of those are load-bearing on the geometry rather than
    # taste: built flush and butted, its two end caps are coincident with the
    # sweep's own caps -- "coincident faces are geometry nobody can see",
    # session 3x -- and its top edge (r0+T, WALL_H)-(r0, WALL_H) is EXACTLY the
    # sweep's, so that edge carries four faces. This file's gate reported it as
    # 2 non-manifold edges and nothing else could have.
    m.arc_solid([(r0 - 0.09, DOOR_H_M), (r0 + ARC_WALL_T_M, DOOR_H_M),
                 (r0 + ARC_WALL_T_M, WALL_H_M), (r0 - 0.09, WALL_H_M)],
                ["council_fin_backing"] * 4,
                d0 - math.radians(0.5), d1 + math.radians(0.5), 6)

    # --- pilasters on the arc, standing proud INTO the room ----------------
    n = max(8, int((a1 - a0) * r0 / WALL_PIER_PITCH_M))
    hw = WALL_PIER_W_M / 2.0
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa * hw, ca * hw
        rp = r0 - WALL_PIER_D_M
        m.plate((rp * ca + tx, WALL_H_M - 0.10, rp * sa + tz),
                (rp * ca + tx, 0.0, rp * sa + tz),
                (rp * ca - tx, 0.0, rp * sa - tz),
                (rp * ca - tx, WALL_H_M - 0.10, rp * sa - tz),
                WALL_PIER_D_M + 0.02, "council_fin_backing")
    # --- a panel joint between every pair of piers --------------------------
    # `docs/AAA-STANDARD.md` C3's tertiary tier, and the cheapest line on the
    # station: a 100 mm reveal at mid-bay is 372 triangles across both walls
    # and it is what took this room from 96.9% of its layer-2b floor back over
    # 100. A 1.85 m panel with nothing between its piers is a 1.85 m panel.
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa * WALL_JOINT_W_M / 2.0, ca * WALL_JOINT_W_M / 2.0
        rp = r0 - 0.045
        m.plate((rp * ca + tx, WALL_H_M - 0.50, rp * sa + tz),
                (rp * ca + tx, 0.30, rp * sa + tz),
                (rp * ca - tx, 0.30, rp * sa - tz),
                (rp * ca - tx, WALL_H_M - 0.50, rp * sa - tz),
                0.055, "council_fin_backing")

    # --- cornice, dado and skirt, where a wall meets a ceiling and a floor --
    # Swept over the SAME arc as the wall, so none of them crosses the doorway.
    # A dado rail across a 2.10 m opening is what `bespoke.near_face_opening`'s
    # own docstring records `hospitality` doing, and it reads as a blockage.
    for y0, y1, d in ((WALL_H_M - 0.46, WALL_H_M - 0.10, 0.20),
                      (1.34, 1.52, 0.16),
                      (0.0, 0.26, 0.13)):
        m.arc_solid([(r0 - d, y0), (r0 + 0.01, y0),
                     (r0 + 0.01, y1), (r0 - d, y1)],
                    ["council_fin_backing"] * 4, a0, a1, segs)


def chair(m, angle_deg, r):
    """One delegation's chair: seat, and an open lattice back.

    IT FACED ALONG THE ARC. `at(dx, dy, dz)` is (radial, up, tangential) and
    every piece of the back was authored at dz = +0.30 -- tangential -- so a
    delegate in it sat sideways to the bench, looking at the next delegation's
    ear. The lattice back also spanned the RADIAL direction, i.e. the chair was
    turned through ninety degrees as a whole. Nothing could catch it: this
    file's gates ask about closure, winding and signed volume, and a chair is
    all three of those whichever way it points.

    The chairs are also INBOARD of the bench now (see `council_chamber`), so
    "behind the delegate" is -radial and that is where the back goes.
    """
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cz = r * ca, r * sa
    hw = CHAIR_W_M / 2.0
    back_dx = -0.30                       # behind the sitter, radially

    def at(dx, dy, dz):
        return (cx + dx * ca - dz * sa, dy, cz + dx * sa + dz * ca)

    # Seat pan. A cushion, not a sheet of paper -- 60 mm of pan is what the
    # frame shows and a plate with no edge is four open boundary edges a chair.
    # Wound so the pan faces UP: this file's `council_chair_seat's top face
    # faces up` gate is the one that says so.
    m.plate(at(0.26, CHAIR_SEAT_H_M, -hw), at(0.26, CHAIR_SEAT_H_M, hw),
            at(-0.26, CHAIR_SEAT_H_M, hw), at(-0.26, CHAIR_SEAT_H_M, -hw),
            0.06, "council_chair_seat")
    for sz in (-1, 1):
        p = at(0.20, 0.0, sz * hw * 0.9)
        m.box(p[0] - 0.03, p[0] + 0.03, 0.0, CHAIR_SEAT_H_M,
              p[2] - 0.03, p[2] + 0.03, "council_chair_leg")

    # The open lattice back. Bars, not a panel: the frame shows the wall
    # THROUGH it, and a solid back would close the room off behind every seat.
    # `m.box` IS AXIS-ALIGNED AND A CHAIR IS NOT. Every rail here used to be a
    # box spanning the BOUNDING BOX of its two ends, which is right only for a
    # chair at angle zero: at +/-60 degrees a 44 mm rail became a 0.55 m slab,
    # and at half distance the "open black lattice back" read as a set of
    # SHELVES. `docs/craft-4p-council-mid-half.png` is the frame that showed it.
    # A `plate` is a quad extruded along its own normal, so it turns with the
    # chair.
    y0, y1 = CHAIR_SEAT_H_M, CHAIR_BACK_H_M
    w = 0.022
    for i in range(CHAIR_LATTICE + 1):
        zc = -hw + CHAIR_W_M * i / CHAIR_LATTICE
        m.plate(at(back_dx, y1, zc - w), at(back_dx, y0, zc - w),
                at(back_dx, y0, zc + w), at(back_dx, y1, zc + w),
                2.0 * w, "council_chair_back")
    for i in range(CHAIR_LATTICE + 1):
        y = y0 + (y1 - y0) * i / CHAIR_LATTICE
        m.plate(at(back_dx, y + w, -hw), at(back_dx, y - w, -hw),
                at(back_dx, y - w, hw), at(back_dx, y + w, hw),
                2.0 * w, "council_chair_back")


def _to_wall(p, x0=None):
    """Rotate the fan and the medallion onto the screen wall.

    Both are authored in the XY plane facing -z, which is the frame every
    winding assertion in this file was written against. A proper rotation of
    -90 degrees about +Y maps (x, y, z) -> (-z, y, x) and carries the normal
    (0, 0, -1) to (+1, 0, 0), which is the wall's face. Rotating is the cheap
    way and re-authoring is the expensive one: the medallion alone is four
    hand-wound sections whose two handednesses this file's own comments record
    costing a round trip to get right once.
    """
    return ((FAN_X_M if x0 is None else x0) - p[2], p[1], p[0])


def fin_wall(m):
    """The radiating fan of angled fins, on the screen wall behind the bench.

    See FAN_X_M for the measurement that moved it. The hub is on the floor at
    z = 0 and the blades splay up and out through 180 degrees, so the fan's
    outer radius IS its height above the floor.
    """
    sub = _M()
    tilt = math.radians(FIN_TILT_DEG)
    z0 = -FIN_STANDOFF_M
    z1 = z0 - math.sin(tilt) * 0.5
    for k in range(FIN_COUNT):
        a = math.pi * (k + 0.5) / FIN_COUNT
        ca, sa = math.cos(a), math.sin(a)
        # THE BLADES TAPER, which is what the frame shows and what a constant
        # -width bar cannot be: in `council chambers.webp` each blade is a long
        # wedge, narrow at the hub and wide at the rim, and the blades nearly
        # touch at their outer ends. A parallel bar reads as a radiator grille.
        hw0 = FIN_W_M * 0.5 * FIN_TAPER
        hw1 = FIN_W_M * 0.5
        sub.plate((FIN_R0_M * ca - hw0 * sa, FIN_R0_M * sa, z0),
                  (FIN_R1_M * ca - hw1 * sa, FIN_R1_M * sa, z0),
                  (FIN_R1_M * ca + hw1 * sa, FIN_R1_M * sa, z1),
                  (FIN_R0_M * ca + hw0 * sa, FIN_R0_M * sa, z1),
                  FIN_D_M, "council_fin")
    m.merge_xform(sub, _to_wall)


def medallion(_outer, cy, z):
    """The circular spoked medallion above the fins.

    Authored vertical in XY at depth z, facing -z, then rotated onto the screen
    wall by `_to_wall` -- see that function. Every winding comment below is
    written in the authoring frame and stays true, because a rotation cannot
    change which side of a triangle is the front.
    """
    m, seg = _M(), 44
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

    _outer.merge_xform(m, _to_wall)


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
    # THE BED IS SUBDIVIDED, AND THAT IS NOT A TESSELLATION PREFERENCE. As one
    # `deck_pad` its top face was an ear clip of a 96-gon, so single triangles
    # ran the whole 22 m across the disc -- and `bespoke.near_face_opening`
    # classifies any horizontal triangle at y = 0 whose z reaches the approach
    # band as FLOOR AT EVERY X IT SPANS. One such triangle told the assembler
    # there was standing room at x = 7.9 m, out where the arc wall's own
    # curvature has taken it out of the near band, and the room was centred on
    # that phantom rather than on its doorway: the function returned
    # (7.87, 6.21) with a real 4.2 m door sitting at x = 0.
    #
    # Subdivided into rings x segments the same face states where the floor
    # actually is, and the same call returns the doorway. It is also better
    # geometry -- a 22 m triangle takes one vertex normal for a whole room.
    # THE CENTRE IS ONE VERTEX, not 96 at the same point. Built as a ring of
    # radius zero it is 96 coincident vertices, every triangle touching it is
    # degenerate, and `boundary_edges` welds by position -- 194 non-manifold
    # edges, AND the file's negative control went silent, because a degenerate
    # triangle removed leaves no hole. A gate that stops firing is the louder
    # of those two symptoms.
    tau = math.tau
    S = FLOOR_BED_SEGS
    i0 = len(m.v)
    bt = []
    m.v.append((0.0, 0.0, 0.0))                                   # top centre
    for ri in range(1, rings + 1):
        rr = FLOOR_R_M * ri / rings
        for k in range(S):
            a = tau * k / S
            m.v.append((rr * math.cos(a), 0.0, rr * math.sin(a)))
    nb = 1 + rings * S                                            # top block
    m.v.append((0.0, -FLOOR_BED_T_M, 0.0))                        # low centre
    for ri in range(1, rings + 1):
        rr = FLOOR_R_M * ri / rings
        for k in range(S):
            a = tau * k / S
            m.v.append((rr * math.cos(a), -FLOOR_BED_T_M, rr * math.sin(a)))

    def top(ri, k):
        return 0 if ri == 0 else 1 + (ri - 1) * S + k % S

    def low(ri, k):
        return nb + top(ri, k)

    for k in range(S):                                            # centre fan
        bt += [(top(0, 0), top(1, k + 1), top(1, k)),
               (low(0, 0), low(1, k), low(1, k + 1))]
    for ri in range(1, rings):
        for k in range(S):
            bt += [(top(ri, k), top(ri + 1, k + 1), top(ri, k + 1)),
                   (top(ri, k), top(ri + 1, k), top(ri + 1, k + 1))]
            bt += [(low(ri, k), low(ri, k + 1), low(ri + 1, k + 1)),
                   (low(ri, k), low(ri + 1, k + 1), low(ri + 1, k))]
    for k in range(S):                                            # the rim
        bt += [(top(rings, k), low(rings, k), low(rings, k + 1)),
               (top(rings, k), low(rings, k + 1), top(rings, k + 1))]
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
    # THE WHOLE ARC, not half of it. The cove used to run 0..pi because the
    # WALL ran 0..pi; with the chamber enclosed the whole way round, a
    # half-cove leaves the other half of a ceremonial room in the dark, which
    # is the defect this change set out to close wearing a different hat.
    # `export_scene.fixture_lights` hangs one lamp per connected tagged body,
    # so this doubles the room's sources -- which is a lighting change and is
    # measured as one below rather than asserted to be harmless.
    m.arc_solid([(r, COVE_Y_M), (FLOOR_R_M, COVE_Y_M),
                 (FLOOR_R_M, COVE_Y_M + COVE_H_M), (r, COVE_Y_M + COVE_H_M)],
                # The housing is `council_frame`, a bound name: it is the same
                # metalwork as the bench's lit-panel surround and the same job,
                # a body you never see holding a face you always do.
                ["council_frame", "council_frame",
                 "council_frame", "light_house_cove"],
                0.0, math.tau, COVE_SEGS * 2)


def council_chamber(seats=SEATS):
    """The room. Bench centred on the origin, delegates INBOARD of it.

    THE BENCH WAS INSIDE-OUT, and it is the reason the room's one defining
    feature could not be seen. `council chambers.webp` shows the lit gold mesh
    facing the CHAMBER -- it is what lights the petitioner standing in front of
    it -- with the delegates behind the bench. This module put the chairs at
    `BENCH_R_M + 0.55`, i.e. OUTBOARD, on the same side as the lit face, so the
    panel faced the delegates' knees and everything the room has to say faced
    a wall. `bench_profile`'s own comment recorded the intent as built: "the
    face a delegate sees is the plinth, then the frame's lower lip, the recess,
    the lit mesh". The reference says the opposite.

    Nothing about the bench moves. The chairs move to CHAIR_R_M, inboard of
    `r_in`, and the screen wall goes behind THEM -- which is also what puts the
    fan and the medallion where a camera in the chamber can see them.
    """
    m = _M()
    mosaic_floor(m)
    bench(m)
    mesh_grille(m)
    delegate_stations(m, seats)
    for k in range(seats):
        f = (k + 0.5) / seats - 0.5
        chair(m, f * BENCH_ARC_DEG * 0.92, CHAIR_R_M)
    screen_wall(m)
    fin_wall(m)
    # STANDING CLEAR OF THE FAN, and the number is measured off the fan rather
    # than chosen. A fin occupies x = FAN_X + 0.03 out to FAN_X + 0.27 (the
    # 30 mm standoff, the 100 mm slab, and the 0.5 m tilt), and the medallion
    # was authored at z = -0.05, i.e. x = FAN_X + 0.02..0.07 -- INSIDE the
    # blades. Thirty blades through a spoked disc renders as shredded metal,
    # which is exactly what docs/craft-4p-council-normal.png showed before this
    # line, and it is the SAME defect as the bench through the fan that opened
    # this session: two solids in one place, invisible to every per-object gate.
    medallion(m, MEDALLION_Y_M, -0.42)
    house_cove(m)
    enclosure(m)
    ceiling(m)
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

    # --- THE PANEL IS PERFORATED, which is the room's one defining sentence --
    # Every check here fails on the version `docs/judge-4e.md` scored, where
    # `council_mesh` was a smooth 80-triangle band and nothing stood in front
    # of it.
    grille = [k for k in range(len(t)) if g[k] == "council_frame"]
    mr = [math.hypot(v[i][0], v[i][2]) for k in mesh for i in t[k]]
    bars = [k for k in grille
            if all(max(mr) < math.hypot(v[i][0], v[i][2]) < BENCH_R_M + 1e-9
                   for i in t[k])]
    check("the lit panel is screened by a perforated grille",
          len(bars) > 400,
          f"{len(bars)} triangles of bar between the light and the room")
    check("...and the grille stands in the recess, not proud of the bench",
          not bars or max(math.hypot(v[i][0], v[i][2])
                          for k in bars for i in t[k]) <= BENCH_R_M + 1e-9,
          "a bar outside r_out is a bar a delegate's knee meets")
    n_bar = int(math.radians(BENCH_ARC_DEG)
                * (BENCH_R_M - BENCH_PANEL_INSET_M + MESH_STANDOFF_M)
                / MESH_BAR_PITCH_M)
    check("...at a pitch a viewer reads as mesh rather than as a fence",
          20 <= MESH_BAR_PITCH_M * 1000 <= 200 and n_bar > 80,
          f"{n_bar} bars at {MESH_BAR_PITCH_M * 1000:.0f} mm over "
          f"{math.radians(BENCH_ARC_DEG) * BENCH_R_M:.1f} m of bench")

    # --- every delegation has a working position ---------------------------
    pads = [k for k in range(len(t)) if g[k] == "council_top_pad"]
    check("each delegation has a working pad on the bench",
          len(pads) == 12 * SEATS, f"{len(pads)} triangles over {SEATS} seats")
    scr = [k for k in range(len(t)) if g[k] == "fix_mp_dress_screen"]
    check("...a screen at it", len(scr) == 12 * SEATS, f"{len(scr)}")
    mics = [k for k in range(len(t)) if g[k] == "fix_mp_plant_rail"]
    check("...and a microphone, which is what the room is for", bool(mics),
          f"{len(mics)} triangles")
    pad_y = [v[i][1] for k in pads for i in t[k]]
    check("the stations sit ON the bench top, not through it",
          min(pad_y) > BENCH_TOP_H_M - BENCH_TOP_D_M
          * math.sin(math.radians(BENCH_TOP_TILT_DEG)) - 0.02,
          f"lowest pad vertex at {min(pad_y):.3f} m")

    # --- the chamber is enclosed, and adds no extent doing it --------------
    back = [k for k in range(len(t)) if g[k] == "council_fin_backing"]
    check("the fin fan has something behind it", bool(back),
          "54% of the judged frame was below the measurable floor and the fan "
          "radiated against nothing")
    rr = [math.hypot(v[i][0], v[i][2]) for k in back for i in t[k]]
    check("...and the enclosure stays within the room's own footprint",
          max(rr) <= FLOOR_R_M + ARC_WALL_T_M + 0.42 + 1e-6,
          f"reaches r {max(rr):.2f} against a {FLOOR_R_M} m floor")
    # The arc stands OUTSIDE the cove, and the number is the thing to check
    # rather than the intent: `house_cove` reaches r = FLOOR_R_M and a wall
    # that started at FLOOR_R_M would share a face with it -- the coincident
    # face this file's zero-non-manifold gate exists to catch.
    cove_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
              if g[k] == "light_house_cove" for i in t[k]]
    check("...and stands clear of the house cove rather than in it",
          FLOOR_R_M + 0.02 > max(cove_r) + 1e-9,
          f"arc wall inner face r {FLOOR_R_M + 0.02:.3f} against a cove "
          f"reaching r {max(cove_r):.3f}")

    # --- seats -------------------------------------------------------------
    # Five delegations can be counted in the frame and the arc runs past both
    # edges, so five is a floor, not the number. Asserting equality would be
    # asserting something the reference does not say.
    check("seat count is at least the five that can be counted",
          SEATS >= 5, f"{SEATS}")
    # MEASURED ON THE BUILT MESH, not on the constants. This read
    # `BENCH_R_M + 0.55 > BENCH_R_M`, which is `x + 0.55 > x`: an assertion
    # that cannot fail, which `docs/AAA-STANDARD.md` scores R0 -- "below
    # untested, because it reports PASS". It also could not have noticed that
    # the chairs were on the WRONG SIDE of the bench, which is what they were.
    ch_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
            if g[k].startswith("council_chair") for i in t[k]]
    bench_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
               if g[k] in ("council_plinth", "council_top", "council_mesh")
               for i in t[k]]
    check("chairs stand clear of the bench, INBOARD of it",
          ch_r and bench_r and max(ch_r) < min(bench_r) - 0.20,
          f"chairs reach r {max(ch_r):.2f}, the bench starts at "
          f"r {min(bench_r):.2f}")
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

    for grp in ("council_speak_fan", "council_chair_seat", "council_top_pad"):
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

    # --- NOTHING IS INSIDE ANYTHING ELSE ------------------------------------
    # THE GATE THIS ROOM DID NOT HAVE, and the reason it shipped a bench
    # through a fan, a bench through a backing plate and thirty fin blades
    # through a spoked medallion, all at once. Every other assertion in this
    # file measures ONE object against ITSELF -- closure, winding, signed
    # volume, which way a face points -- and two solids in the same cubic metre
    # are all four of those. `docs/AAA-STANDARD.md` R5 names it: "cross-subsystem
    # clearance is asserted wherever two systems occupy the same space", and the
    # standing counter-example it cites is the tram 6.43 m inside a spoke.
    #
    # Stated as the separation it actually is: the rear composition lives on the
    # screen wall, the furniture lives out in the chamber, and there is a gap.
    def xrange_of(pred):
        ks = [k for k in range(len(t)) if pred(g[k])]
        xs = [v[i][0] for k in ks for i in t[k]]
        return (min(xs), max(xs)) if xs else None

    rear = xrange_of(lambda n: n == "council_fin"
                     or n.startswith("council_medallion")
                     or n.startswith("signage_panel"))
    furn = xrange_of(lambda n: n in ("council_plinth", "council_top",
                                     "council_mesh", "council_speak_fan")
                     or n.startswith("council_chair"))
    check("the rear composition and the furniture do not share space",
          rear and furn and furn[0] > rear[1] + 0.50,
          f"rear reaches x {rear[1]:.2f}, furniture starts at x {furn[0]:.2f}")
    fins = xrange_of(lambda n: n == "council_fin")
    meda = xrange_of(lambda n: n.startswith("council_medallion"))
    check("the medallion stands clear of the fan rather than inside it",
          meda and fins and meda[0] > fins[1] + 1e-9,
          f"fins reach x {fins[1]:.3f}, medallion starts at x {meda[0]:.3f}")

    # NEGATIVE CONTROL -- put the medallion back where it was and the gate has
    # to fire. Built through the same `_M` the room is, so this is the real
    # geometry and not a restatement of the constants.
    _probe = _M()
    fin_wall(_probe)
    medallion(_probe, MEDALLION_Y_M, -0.05)
    pv, pt, pg = _probe.as_tuple()
    _fx = max(pv[i][0] for k in range(len(pt))
              if pg[k] == "council_fin" for i in pt[k])
    _mx = min(pv[i][0] for k in range(len(pt))
              if pg[k].startswith("council_medallion") for i in pt[k])
    check("...and the placement it replaced FAILS that gate",
          _mx < _fx, f"old medallion x {_mx:.3f} against fins to {_fx:.3f}")

    # --- the medallion faces the room --------------------------------------
    # Same correction: the disc, the spokes and the rings all have backs now,
    # and a back facing the wall is the point of having one. The face a
    # delegate sees is the one at the lowest z, which is toward the room.
    # IN X, NOT IN Z. The medallion is authored in XY facing -z and rotated
    # onto the screen wall by `_to_wall`, so the face a delegate sees is the
    # one at the GREATEST x. Left testing z this gate picked the disc's rim at
    # z = -1.35 and asked a question about it that means nothing -- it kept
    # passing, which is the worse outcome.
    ks = [k for k in range(len(t)) if g[k].startswith("council_medallion")]
    xfront = max(v[i][0] for k in ks for i in t[k])
    bad = 0
    for k in ks:
        if any(abs(v[i][0] - xfront) > 1e-6 for i in t[k]):
            continue
        p0, p1, p2 = (v[i] for i in t[k])
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[1] * w[2] - u[2] * w[1] <= 0:
            bad += 1
    check("the medallion's front face faces into the room", bad == 0,
          f"{bad} of the front-plane triangles face the wall")

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
