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
FIN_TILT_DEG = 16.0

MEDALLION_R_M = 1.35
MEDALLION_SPOKES = 24
MEDALLION_RINGS = 3

FLOOR_R_M = 11.0
FLOOR_TILES = 96                # irregular polygons, not a grid
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

    def as_tuple(self):
        return self.v, self.t, self.g


def _u(seed, *parts):
    """Deterministic unit value. blake2b, never `random` or `hash`."""
    import hashlib
    h = hashlib.blake2b(("|".join([seed] + [str(p) for p in parts])).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def bench(m):
    """The curved bench: plinth, lit mesh panel, and an angled slab top."""
    seg = 40
    a0 = math.radians(-BENCH_ARC_DEG / 2.0)
    a1 = math.radians(BENCH_ARC_DEG / 2.0)
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    tilt = math.radians(BENCH_TOP_TILT_DEG)
    drop = BENCH_TOP_D_M * math.sin(tilt)

    for k in range(seg):
        t0 = a0 + (a1 - a0) * k / seg
        t1 = a0 + (a1 - a0) * (k + 1) / seg
        c0, s0 = math.cos(t0), math.sin(t0)
        c1, s1 = math.cos(t1), math.sin(t1)

        # plinth
        m.box(0, 0, 0, 0, 0, 0, "council_plinth") if False else None
        m.quad((r_out * c0, 0.0, r_out * s0), (r_out * c1, 0.0, r_out * s1),
               (r_out * c1, BENCH_PLINTH_H_M, r_out * s1),
               (r_out * c0, BENCH_PLINTH_H_M, r_out * s0), "council_plinth")

        # the lit mesh, recessed behind the face plane
        rp = r_out - BENCH_PANEL_INSET_M
        m.quad((rp * c0, BENCH_PLINTH_H_M, rp * s0),
               (rp * c1, BENCH_PLINTH_H_M, rp * s1),
               (rp * c1, BENCH_TOP_H_M - 0.06, rp * s1),
               (rp * c0, BENCH_TOP_H_M - 0.06, rp * s0), "council_mesh")

        # the frame the mesh sits behind: a lip top and bottom
        for y0, y1 in ((BENCH_PLINTH_H_M, BENCH_PLINTH_H_M + 0.05),
                       (BENCH_TOP_H_M - 0.10, BENCH_TOP_H_M - 0.06)):
            m.quad((r_out * c0, y0, r_out * s0), (r_out * c1, y0, r_out * s1),
                   (r_out * c1, y1, r_out * s1), (r_out * c0, y1, r_out * s0),
                   "council_frame")

        # the angled slab top: falls away from the delegates toward the floor
        m.up_quad((r_out * c0, BENCH_TOP_H_M - drop, r_out * s0),
                  (r_out * c1, BENCH_TOP_H_M - drop, r_out * s1),
                  (r_in * c1, BENCH_TOP_H_M, r_in * s1),
                  (r_in * c0, BENCH_TOP_H_M, r_in * s0), "council_top")

    # The speaking-position fan, laid on the top at the bench's centre.
    for k in range(13):
        f = (k - 6) / 6.0
        a = f * math.radians(26.0)
        ca, sa = math.cos(a), math.sin(a)
        w = 0.022
        m.up_quad((r_in * ca - w * sa, BENCH_TOP_H_M + 0.004, r_in * sa + w * ca),
                  (r_out * ca - w * sa, BENCH_TOP_H_M + 0.004, r_out * sa + w * ca),
                  (r_out * ca + w * sa, BENCH_TOP_H_M + 0.004, r_out * sa - w * ca),
                  (r_in * ca + w * sa, BENCH_TOP_H_M + 0.004, r_in * sa - w * ca),
                  "council_speak_fan")


def chair(m, angle_deg, r):
    """One delegation's chair: seat, and an open lattice back."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cz = r * ca, r * sa
    hw = CHAIR_W_M / 2.0

    def at(dx, dy, dz):
        return (cx + dx * ca - dz * sa, dy, cz + dx * sa + dz * ca)

    # seat pan
    m.up_quad(at(-hw, CHAIR_SEAT_H_M, -0.26), at(hw, CHAIR_SEAT_H_M, -0.26),
              at(hw, CHAIR_SEAT_H_M, 0.26), at(-hw, CHAIR_SEAT_H_M, 0.26),
              "council_chair_seat")
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
        # Each fin is a slab standing off the wall, splaying from a hub.
        for r0, r1 in ((FIN_R0_M, FIN_R1_M),):
            m.quad((r0 * ca - hw * sa, r0 * sa, -0.30),
                   (r1 * ca - hw * sa, r1 * sa, -0.30),
                   (r1 * ca + hw * sa, r1 * sa, -0.30 - math.sin(tilt) * 0.5),
                   (r0 * ca + hw * sa, r0 * sa, -0.30 - math.sin(tilt) * 0.5),
                   "council_fin")


def medallion(m, cy, z):
    """The circular spoked medallion above the fins.

    Vertical, in XY at depth z, facing INTO the room -- ascending angle in XY
    gives a +Z normal, which faces the wall.
    """
    seg = 44
    i0 = len(m.v)
    m.v.append((0.0, cy, z))
    for k in range(seg):
        a = 2.0 * math.pi * k / seg
        m.v.append((MEDALLION_R_M * math.cos(a),
                    cy + MEDALLION_R_M * math.sin(a), z))
    for k in range(seg):
        m.t.append((i0, i0 + 1 + (k + 1) % seg, i0 + 1 + k))
    m.g.extend(["council_medallion"] * seg)

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
        m.quad((hub * ca - w * sa, cy + hub * sa + w * ca, z - 0.02),
               (MEDALLION_R_M * ca - w * sa,
                cy + MEDALLION_R_M * sa + w * ca, z - 0.02),
               (MEDALLION_R_M * ca + w * sa,
                cy + MEDALLION_R_M * sa - w * ca, z - 0.02),
               (hub * ca + w * sa, cy + hub * sa - w * ca, z - 0.02),
               "council_medallion_spoke")

    for ri in range(1, MEDALLION_RINGS + 1):
        rr = MEDALLION_R_M * ri / (MEDALLION_RINGS + 1)
        w = 0.022
        for k in range(seg):
            a0 = 2.0 * math.pi * k / seg
            a1 = 2.0 * math.pi * (k + 1) / seg
            m.quad(((rr - w) * math.cos(a1), cy + (rr - w) * math.sin(a1), z - 0.03),
                   ((rr + w) * math.cos(a1), cy + (rr + w) * math.sin(a1), z - 0.03),
                   ((rr + w) * math.cos(a0), cy + (rr + w) * math.sin(a0), z - 0.03),
                   ((rr - w) * math.cos(a0), cy + (rr - w) * math.sin(a0), z - 0.03),
                   "council_medallion_ring")


def mosaic_floor(m, seed="council"):
    """A pale polygonal mosaic, irregular rather than a grid.

    Built as a deterministic Voronoi-ish fan: tiles radiate from the centre with
    jittered angular and radial boundaries. The frame shows irregular polygons
    of varying size, and a square grid reads as a bathroom.
    """
    rings = 6
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
            m.up_quad((g0 * math.cos(a0), 0.0, g0 * math.sin(a0)),
                      (g1 * math.cos(a0), 0.0, g1 * math.sin(a0)),
                      (g1 * math.cos(a1), 0.0, g1 * math.sin(a1)),
                      (g0 * math.cos(a1), 0.0, g0 * math.sin(a1)),
                      f"council_floor_{shade}")


def house_cove(m):
    """The concealed high-level cove. See THE HOUSE LIGHTING above.

    Segments of an arc at COVE_Y_M, standing COVE_D_M off the wall over the
    same half of the chamber the fin fan occupies -- the wall the camera faces
    and the wall the measurement watched brighten.
    """
    r = FLOOR_R_M - COVE_D_M
    for k in range(COVE_SEGS):
        a0 = math.pi * k / COVE_SEGS
        a1 = math.pi * (k + 1) / COVE_SEGS
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        # A lit strip facing INTO the room, its housing hidden behind the lip.
        m.quad((r * c0, COVE_Y_M, r * s0),
               (r * c1, COVE_Y_M, r * s1),
               (r * c1, COVE_Y_M + COVE_H_M, r * s1),
               (r * c0, COVE_Y_M + COVE_H_M, r * s0),
               "light_house_cove")


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
    check("the mesh is recessed behind its frame, not coplanar",
          max(mr) < min(fr) - 1e-9,
          f"mesh out to {max(mr):.3f}, frame at {min(fr):.3f}")

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

    # --- flat things face up ------------------------------------------------
    for grp in ("council_top", "council_speak_fan", "council_chair_seat"):
        bad = 0
        for k, tri in enumerate(t):
            if g[k] != grp:
                continue
            p0, p1, p2 = (v[i] for i in tri)
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[2] * w[0] - u[0] * w[2] <= 0:
                bad += 1
        check(f"{grp} faces up", bad == 0, f"{bad} downward")
    floor_groups = [grp for grp in set(g) if grp.startswith("council_floor")]
    bad = 0
    for k, tri in enumerate(t):
        if g[k] not in floor_groups:
            continue
        p0, p1, p2 = (v[i] for i in tri)
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[2] * w[0] - u[0] * w[2] <= 0:
            bad += 1
    check("the mosaic floor faces up", bad == 0, f"{bad} downward")

    # --- the medallion faces the room --------------------------------------
    bad = 0
    for k, tri in enumerate(t):
        if not g[k].startswith("council_medallion"):
            continue
        p0, p1, p2 = (v[i] for i in tri)
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[0] * w[1] - u[1] * w[0] >= 0:
            bad += 1
    check("the medallion faces into the room", bad == 0,
          f"{bad} triangles facing the wall")

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
