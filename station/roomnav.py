#!/usr/bin/env python3
"""Where in a room a person can stand, and the way in from the door.

WHY THIS EXISTS, and it is the L3 blocker stated as geometry. `agenda.py`'s
commute walked a named resident 789 m across two decks and a lift and then
stopped **5.59 m from their post**, deterministically, at x1, x10 and x60. The
number was written up twice as a lift or tracking defect and it is neither.
Measured against the cluster's own collision shell, the last leg of the route --
`in_door -> the register's centre point` -- passes through:

    r=219.06 over 0.8 m of arc, z 6600.7..6605.2   desk tops, 0.72 m up
    r=219.80..217.63 at fixed z                    a partition, floor to head

Clearance along that leg, point-to-triangle rather than centroid-to-point,
never exceeds 0.53 m and is under the 0.35 m capsule for 4.5 of its 5.5 m. The
body walked to the desks, stopped, and the gate read the stop as "did not
arrive". **It had arrived. There was nowhere further to go.**

The cause is one line of geometry inherited from before rooms had furniture:
the point a body is sent to inside a room was the room's ADDRESS -- radius,
angle, z straight out of `directory.PLACES` -- and the route into it was the
straight line from the doorway to that address. Both were correct while a room
was an empty box. V1's form-follows-function pass put real fittings in these
rooms and neither was updated, so the aim point moved inside the furniture and
the approach became a line through a desk rank.

WHAT THIS MODULE DOES, AND WHAT IT REFUSES TO DO. It answers "where can a body
stand" and "how does it get there from the door" **from the collision mesh the
body actually collides with**, and from nothing else. There is no second list
of where the furniture was meant to go, no per-room table of nice spots, no
authored waypoints. Hard rule 4 -- one authority per fact -- is the whole
design: if a generator moves a desk, the standing spot and the path to it move
with it on the next build, because they are derived from the desk.

THE OCCUPANCY MODEL, and its three cases are the entire physics of it. Height
above the deck is `floor_r - r`, because the deck is a cylinder and down is
outward. A triangle is:

    at or below the deck          not an obstacle -- it is the floor
    entirely above `head_m`       not an obstacle -- you walk under it
    anything else                 an obstacle, dilated by the capsule radius

plus one exception with teeth: a triangle in a `doorpanel_*` group is **not an
obstacle**, because the runtime switches that shape off for a body standing at
it (`life.gd::_open_doors`). Treating a door as a wall is how the first version
of this found every room sealed.

The grid is the room's floor unrolled -- `s = floor_r * theta`, `z` axial -- at
`CELL_M`. Unrolling flips handedness (see `interior.py`); nothing here depends
on winding, only on distance, so it does not matter. Cells outside the room's
own z band are not in the grid at all, which is what stops a search that starts
in a doorway from wandering back out into the corridor and calling the corridor
a good place to stand.

THE STANDING SPOT is the reachable free cell nearest the register's centre --
"as close to the middle of the room as a person can actually get" -- and
`approach()` returns the whole way there, string-pulled so that consecutive
waypoints see each other. A caller that wants only the endpoint takes the last
point; a caller laying a route takes all of them.

Run: python3 station/roomnav.py --selftest
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# THE BODY, AND THIS IS NOW THE ONE PLACE IT IS WRITTEN DOWN. `route_walk.py`
# and `agenda.py` each carried their own copy of the capsule radius; a third
# copy here would be the same defect one wider. Both now import these.
CAPSULE_R_M = 0.35
CAPSULE_H_M = 1.80

CELL_M = 0.20            # the grid; a shade over half a capsule diameter
FLOOR_EPS_M = 0.12       # a surface within this of the deck IS the deck
SNAP_MAX_M = 1.50        # how far the search may look for a free cell to start
                         # from when the doorway itself is tight


# ---------------------------------------------------------------------------
# THE ROOM, UNROLLED
# ---------------------------------------------------------------------------

def _unroll(floor_r, th0):
    """(x, y, z) -> (s, z) and back, about the room's own angle.

    `s` is arc length at the floor radius, signed, measured from `th0`, and
    the wrap is taken about `th0` so a room at 0 deg does not tear.
    """
    def fwd(p):
        th = math.atan2(p[1], p[0])
        d = (th - th0 + math.pi) % (2.0 * math.pi) - math.pi
        return (floor_r * d, p[2])

    def inv(s, z, r=None):
        th = th0 + s / floor_r
        rr = floor_r if r is None else r
        return (rr * math.cos(th), rr * math.sin(th), z)

    return fwd, inv


def _door_tris(groups):
    """Triangle indices belonging to a pressure door, which is not a wall.

    `life.gd::_open_doors` disables exactly these shapes for a body standing at
    them. A search that treats them as solid finds every room sealed, which is
    what the first version of this reported.
    """
    out = set()
    for nm, lo, hi in (groups or ()):
        if str(nm).startswith("doorpanel_"):
            out.update(range(lo, hi))
    return out


class Grid:
    """The room's floor, free/blocked, at `CELL_M`."""

    def __init__(self, floor_r, th0, z0, s_half, z_lo, z_hi, cell_m=CELL_M):
        self.floor_r = floor_r
        self.th0 = th0
        self.z0 = z0
        self.cell = cell_m
        self.s_lo = -s_half
        self.z_lo = z_lo
        self.nw = max(1, int(math.ceil(2.0 * s_half / cell_m)))
        self.nh = max(1, int(math.ceil((z_hi - z_lo) / cell_m)))
        self.free = bytearray(b"\x01" * (self.nw * self.nh))
        self.fwd, self.inv = _unroll(floor_r, th0)

    # -- indexing -----------------------------------------------------------
    def cell_of(self, s, z):
        return (int(math.floor((s - self.s_lo) / self.cell)),
                int(math.floor((z - self.z_lo) / self.cell)))

    def centre_of(self, i, k):
        return (self.s_lo + (i + 0.5) * self.cell,
                self.z_lo + (k + 0.5) * self.cell)

    def inside(self, i, k):
        return 0 <= i < self.nw and 0 <= k < self.nh

    def is_free(self, i, k):
        return self.inside(i, k) and self.free[k * self.nw + i]

    def block(self, i, k):
        if self.inside(i, k):
            self.free[k * self.nw + i] = 0

    def free_count(self):
        return sum(self.free)

    def touches_edge(self):
        """Does free floor run off the side of the grid?

        NO SILENT CAPS. `s_half` is a bound on how far along the arc the search
        looks, and a room wider than that is a room searched in part -- which
        would read as "this is the best spot in the room" when it is the best
        spot in the slice that was looked at. A room's own walls normally stop
        the search long before the bound does, and this says when they did not
        so the caller can widen rather than quietly believe a clipped answer.
        """
        n = 0
        for k in range(self.nh):
            n += bool(self.free[k * self.nw]) + bool(
                self.free[k * self.nw + self.nw - 1])
        return n

    # -- rasterising the obstacles ------------------------------------------
    def carve(self, verts, tris, groups=None, clear_r=CAPSULE_R_M,
              head_m=CAPSULE_H_M):
        """Mark every cell a capsule cannot stand in. Triangle-major.

        Triangle-major rather than cell-major on purpose: a room is a few
        hundred triangles and a few thousand cells, and a cell-major loop is
        the product of the two. This is the sum.
        """
        skip = _door_tris(groups)
        blocked_tris = 0
        self.obst = []
        for ti, tri in enumerate(tris):
            if ti in skip:
                continue
            vs = [verts[i] for i in tri]
            hs = [self.floor_r - math.hypot(v[0], v[1]) for v in vs]
            if max(hs) <= FLOOR_EPS_M:          # the deck, or under it
                continue
            if min(hs) >= head_m:               # over your head
                continue
            p2 = [self.fwd(v) for v in vs]
            blocked_tris += 1
            self.obst.append(p2)
            s_lo = min(p[0] for p in p2) - clear_r
            s_hi = max(p[0] for p in p2) + clear_r
            zz_lo = min(p[1] for p in p2) - clear_r
            zz_hi = max(p[1] for p in p2) + clear_r
            i0, k0 = self.cell_of(s_lo, zz_lo)
            i1, k1 = self.cell_of(s_hi, zz_hi)
            for i in range(max(0, i0), min(self.nw - 1, i1) + 1):
                for k in range(max(0, k0), min(self.nh - 1, k1) + 1):
                    if not self.free[k * self.nw + i]:
                        continue
                    c = self.centre_of(i, k)
                    if _pt_tri_2d(c, p2[0], p2[1], p2[2]) <= clear_r:
                        self.free[k * self.nw + i] = 0
        return blocked_tris

    def clear_at(self, s, z):
        """Exact clearance at a point, not at its cell's centre.

        The grid answers to `CELL_M`, so a free cell means its CENTRE has a
        capsule's room and says nothing about a point 0.14 m away inside it.
        That matters in exactly one place and it is the important one: whether
        the register's own centre point is standable, which decides whether
        this module changes a route at all.
        """
        best = 1e30
        for a, b, c in getattr(self, "obst", ()):
            best = min(best, _pt_tri_2d((s, z), a, b, c))
            if best <= 0.0:
                return 0.0
        return best

    # -- searching ----------------------------------------------------------
    def snap(self, s, z, max_m=SNAP_MAX_M):
        """The free cell nearest (s, z), or None. Returns (i, k, distance)."""
        i0, k0 = self.cell_of(s, z)
        if self.is_free(i0, k0):
            return (i0, k0, 0.0)
        rings = int(math.ceil(max_m / self.cell))
        best = None
        for rad in range(1, rings + 1):
            for i in range(i0 - rad, i0 + rad + 1):
                for k in (k0 - rad, k0 + rad):
                    if self.is_free(i, k):
                        c = self.centre_of(i, k)
                        d = math.hypot(c[0] - s, c[1] - z)
                        if best is None or d < best[2]:
                            best = (i, k, d)
            for k in range(k0 - rad + 1, k0 + rad):
                for i in (i0 - rad, i0 + rad):
                    if self.is_free(i, k):
                        c = self.centre_of(i, k)
                        d = math.hypot(c[0] - s, c[1] - z)
                        if best is None or d < best[2]:
                            best = (i, k, d)
            if best is not None:
                return best
        return None

    def bfs(self, start):
        """Every cell reachable from `start`, with parents. 8-connected, and a
        diagonal step requires both of its orthogonal neighbours -- a body does
        not squeeze through the corner between two desks."""
        nw, nh = self.nw, self.nh
        prev = [-1] * (nw * nh)
        si, sk = start
        s0 = sk * nw + si
        prev[s0] = s0
        q = [s0]
        head = 0
        while head < len(q):
            cur = q[head]
            head += 1
            ci, ck = cur % nw, cur // nw
            for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                ni, nk = ci + di, ck + dk
                if not self.is_free(ni, nk):
                    continue
                if di and dk and not (self.is_free(ci + di, ck)
                                      and self.is_free(ci, ck + dk)):
                    continue
                n = nk * nw + ni
                if prev[n] != -1:
                    continue
                prev[n] = cur
                q.append(n)
        return prev

    def clear_line(self, a, b):
        """Is the straight segment from cell `a` to cell `b` free throughout?"""
        (ai, ak), (bi, bk) = a, b
        n = max(abs(bi - ai), abs(bk - ak))
        if n == 0:
            return self.is_free(ai, ak)
        for j in range(n + 1):
            i = int(round(ai + (bi - ai) * j / n))
            k = int(round(ak + (bk - ak) * j / n))
            if not self.is_free(i, k):
                return False
        return True


def _pt_tri_2d(p, a, b, c):
    """Distance from a 2D point to a 2D triangle. Zero inside it."""
    # inside test by sign consistency
    def cross(o, u, v):
        return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])
    d1, d2, d3 = cross(p, a, b), cross(p, b, c), cross(p, c, a)
    if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
        return 0.0
    best = 1e30
    for u, v in ((a, b), (b, c), (c, a)):
        ux, uy = v[0] - u[0], v[1] - u[1]
        l2 = ux * ux + uy * uy
        t = 0.0 if l2 <= 1e-12 else max(0.0, min(
            1.0, ((p[0] - u[0]) * ux + (p[1] - u[1]) * uy) / l2))
        qx, qy = u[0] + ux * t, u[1] + uy * t
        best = min(best, math.hypot(p[0] - qx, p[1] - qy))
    return best


# ---------------------------------------------------------------------------
# THE ANSWER
# ---------------------------------------------------------------------------

def approach(meta, place, verts, tris, groups=None, from_pt=None,
             z_half=None, clear_r=CAPSULE_R_M, head_m=CAPSULE_H_M,
             stand_up_m=0.05, report=None):
    """The way in from the door and the spot at the end of it, in world space.

    Returns a list of points, at least one long. The last is where the body
    stands; anything before it is the way past the furniture to get there. With
    no mesh, or with a room whose middle is already clear, the list is exactly
    the register's centre point and every caller behaves as it did before.

    `report`, if a dict, is filled in with what was measured -- free cells,
    reachable cells, how far the standing spot ended up from the register's
    centre, and whether the doorway had to be snapped. Gates read it; the
    geometry does not depend on it.
    """
    rep = report if report is not None else {}
    floor_r = meta["floor_r_m"]
    th0 = math.radians(place["angle_deg"])
    z0 = float(place["z_m"])
    r_stand = floor_r - stand_up_m
    centre = (r_stand * math.cos(th0), r_stand * math.sin(th0), z0)
    rep["centre"] = centre
    if not verts or not tris:
        rep["why"] = "no mesh"
        return [centre]

    # The room's own z band. `z_half` is the caller's -- `deck.room_interior_
    # half_m` -- because the depth of a room is that module's fact, not this
    # one's. Without it the band is taken from the mesh's own extent about z0.
    if z_half is None:
        zs = [v[2] for v in verts if abs(v[2] - z0) < 60.0]
        z_half = (max(zs) - z0) if zs else 8.0
    z_half = max(1.0, float(z_half))
    # A generous arc half-span: the room's walls stop the search long before
    # this does, and a span that is too small is a room clipped in half.
    s_half = max(6.0, 2.0 * z_half)

    g = Grid(floor_r, th0, z0, s_half, z0 - z_half, z0 + z_half)
    rep["cells"] = (g.nw, g.nh)
    rep["obstacle_tris"] = g.carve(verts, tris, groups, clear_r, head_m)
    rep["free"] = g.free_count()
    # Reported, never silently swallowed: free floor running off the side of
    # the grid means the room is wider than the arc this looked along, so the
    # spot chosen is the best in a SLICE of the room and says so.
    rep["clipped_cells"] = g.touches_edge()

    # WHERE THE BODY COMES IN. The doorway, if the caller said; otherwise the
    # middle of the room, which makes this a "nearest standable spot" query
    # with no reachability claim attached.
    start_sz = g.fwd(from_pt) if from_pt else (0.0, z0)
    snapped = g.snap(*start_sz)
    if snapped is None:
        rep["why"] = ("the doorway is not standable and there is no free cell "
                      f"within {SNAP_MAX_M} m of it")
        return [centre]
    si, sk, snap_m = snapped
    rep["snap_m"] = round(snap_m, 3)

    prev = g.bfs((si, sk))
    reach = [n for n, p in enumerate(prev) if p != -1]
    rep["reachable"] = len(reach)
    if not reach:
        rep["why"] = "nothing is reachable from the doorway"
        return [centre]

    # THE SPOT: the reachable cell nearest the register's centre. Not the
    # cell with the most clearance -- a body that walks to the emptiest corner
    # of a room is not standing where the room is.
    ci, ck = g.cell_of(0.0, z0)
    goal = min(reach, key=lambda n: ((n % g.nw) - ci) ** 2
               + ((n // g.nw) - ck) ** 2)
    gi, gk = goal % g.nw, goal // g.nw
    gc = g.centre_of(gi, gk)
    rep["off_centre_m"] = round(math.hypot(gc[0], gc[1] - z0), 3)

    # The path back out to the door, then string-pulled: keep a waypoint only
    # where the straight line to the next one is not free.
    chain = []
    n = goal
    while True:
        chain.append((n % g.nw, n // g.nw))
        if prev[n] == n:
            break
        n = prev[n]
    chain.reverse()
    pulled = [chain[0]]
    i = 0
    while i < len(chain) - 1:
        j = len(chain) - 1
        while j > i + 1 and not g.clear_line(chain[i], chain[j]):
            j -= 1
        pulled.append(chain[j])
        i = j
    rep["waypoints"] = len(pulled)
    rep["path_cells"] = len(chain)

    # AND IF THE MIDDLE OF THE ROOM IS STANDABLE, THE ANSWER IS THE MIDDLE OF
    # THE ROOM -- the register's own point, to the metre it was written at, not
    # the nearest 0.20 m cell centre. Otherwise this module would shift every
    # route in the station by up to half a cell for no reason, and a change
    # that moves what it was not asked to move cannot be reviewed.
    exact_centre = ((gi, gk) == (ci, ck)
                    and g.clear_at(0.0, z0) >= clear_r)
    rep["exact_centre"] = exact_centre

    out = []
    for (i, k) in pulled:
        s, z = g.centre_of(i, k)
        out.append(g.inv(s, z, r_stand))
    if exact_centre:
        out[-1] = centre
    # The first pulled cell is the snapped doorway; the caller already has a
    # waypoint there, so it is dropped unless it moved.
    if from_pt is not None and len(out) > 1 and math.dist(out[0], from_pt) < 0.5:
        out = out[1:]
    return out


def standpoint(meta, place, verts, tris, groups=None, **kw):
    """Just the spot. `approach(...)[-1]`, and there is no second opinion."""
    return approach(meta, place, verts, tris, groups, **kw)[-1]


# ---------------------------------------------------------------------------
# SELFTEST
# ---------------------------------------------------------------------------

def _selftest():
    fails = []

    def check(ok, name, detail=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}"
              + (f"   -- {detail}" if detail else ""))
        if not ok:
            fails.append(name)
        return ok

    # -- the 2D primitive, on its own ---------------------------------------
    a, b, c = (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)
    check(_pt_tri_2d((0.2, 0.2), a, b, c) == 0.0, "a point inside a triangle "
          "is zero from it")
    check(abs(_pt_tri_2d((-1.0, 0.0), a, b, c) - 1.0) < 1e-9,
          "and a point outside is its distance to the nearest edge")
    check(abs(_pt_tri_2d((2.0, 2.0), a, b, c) - math.hypot(1.5, 1.5)) < 1e-9,
          "including past a vertex", f"{_pt_tri_2d((2.0, 2.0), a, b, c):.4f}")

    # -- a synthetic room, so the model can be checked without a station -----
    # A 12 m x 12 m floor at r=200, a desk bar across the middle with a gap,
    # and a ceiling. The straight line from the door to the centre crosses the
    # bar; the way round it is through the gap.
    floor_r, z0, th0 = 200.0, 0.0, 0.0
    verts, tris = [], []

    def quad(pts):
        i = len(verts)
        verts.extend(pts)
        tris.append((i, i + 1, i + 2))
        tris.append((i, i + 2, i + 3))

    def at(s, z, h):
        th = th0 + s / floor_r
        r = floor_r - h
        return (r * math.cos(th), r * math.sin(th), z0 + z)

    quad([at(-6, -6, 0), at(6, -6, 0), at(6, 6, 0), at(-6, 6, 0)])      # deck
    quad([at(-6, -6, 2.6), at(6, -6, 2.6), at(6, 6, 2.6), at(-6, 6, 2.6)])
    n_base_v, n_base_t = len(verts), len(tris)          # deck + ceiling only
    # a desk bar at z=+2, 0.75 m high, from s=-6 to s=+1 -- gap from 1 to 6.
    # Its underside sits ON the deck and is therefore deck, which is the model
    # working: only the top and the end cap are things you walk into.
    for h in (0.0, 0.75):
        quad([at(-6, 1.7, h), at(1.0, 1.7, h), at(1.0, 2.3, h), at(-6, 2.3, h)])
    quad([at(1.0, 1.7, 0.0), at(1.0, 1.7, 0.75), at(1.0, 2.3, 0.75),
          at(1.0, 2.3, 0.0)])

    meta = {"floor_r_m": floor_r}
    place = {"angle_deg": 0.0, "z_m": z0}
    door = at(0.0, 5.0, 0.05)
    rep = {}
    path = approach(meta, place, verts, tris, groups=[("room", 0, len(tris))],
                    from_pt=door, z_half=6.0, report=rep)
    check(rep.get("obstacle_tris") == 4, "the deck and the ceiling are not "
          "obstacles; the desk bar's top and end cap are",
          f"{rep.get('obstacle_tris')} of {len(tris)} triangles")
    check(len(path) >= 2, "the way in past a desk bar is not a straight line",
          f"{len(path)} waypoints, {rep.get('path_cells')} cells")
    end = path[-1]
    s_end = floor_r * ((math.atan2(end[1], end[0]) - th0 + math.pi)
                       % (2 * math.pi) - math.pi)
    check(abs(s_end) < 1.0 and abs(end[2] - z0) < 1.0,
          "and it ends at the middle of the room",
          f"s={s_end:.2f} z={end[2] - z0:.2f}")
    # every waypoint stands clear of the furniture
    worst = 1e9
    for p in path:
        for tri in tris:
            vs = [verts[i] for i in tri]
            hs = [floor_r - math.hypot(v[0], v[1]) for v in vs]
            if max(hs) <= FLOOR_EPS_M or min(hs) >= CAPSULE_H_M:
                continue
            fwd, _inv = _unroll(floor_r, th0)
            worst = min(worst, _pt_tri_2d(fwd(p), *[fwd(v) for v in vs]))
    check(worst >= CAPSULE_R_M - 1e-9, "and every waypoint on it has a "
          "capsule's clearance", f"worst {worst:.3f} m")

    # THE NEGATIVE CONTROL, and it has to fire. With the desk bar taken out the
    # answer must collapse to the straight line -- one waypoint, dead centre.
    rep2 = {}
    path2 = approach(meta, place, verts[:n_base_v], tris[:n_base_t],
                     groups=[("room", 0, n_base_t)], from_pt=door,
                     z_half=6.0, report=rep2)
    check(rep2.get("obstacle_tris") == 0 and len(path2) == 1,
          "CONTROL: with the desks gone it is one waypoint at the centre",
          f"{rep2.get('obstacle_tris')} obstacles, {len(path2)} waypoints")
    check(abs(path2[0][2] - z0) < 1e-6,
          "and that waypoint is the register's own centre point")

    # AND A DOOR IS NOT A WALL. The same room with the desk bar renamed as a
    # pressure door must read as empty, because the runtime opens it.
    rep3 = {}
    approach(meta, place, verts, tris,
             groups=[("room", 0, n_base_t),
                     ("doorpanel_x", n_base_t, len(tris))],
             from_pt=door, z_half=6.0, report=rep3)
    check(rep3.get("obstacle_tris") == 0,
          "CONTROL: a doorpanel_* group is not an obstacle -- the runtime "
          "opens it", f"{rep3.get('obstacle_tris')} obstacles")

    print(f"\n{'OK' if not fails else 'FAILED: ' + '; '.join(fails)}")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or True:
        return _selftest()


if __name__ == "__main__":
    sys.exit(main())
