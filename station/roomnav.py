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
# A ROOM YOU CAN ENTER AND NOT MOVE IN IS NOT A ROOM YOU CAN ENTER. Reaching
# less than this from the entry point, without reaching the room's own middle,
# is a pocket beside a door rather than the room -- see `approach`. Two square
# metres is a body's own footprint and a step in any direction.
MIN_STAND_M2 = 2.0
# ...and how far from the middle of a room the nearest standable cell may be,
# as a fraction of the room's own half-depth, before "we are in the room" stops
# being true. Measured: a pocket outside the wall lands at 0.97 of it; a room
# entered properly lands well under a third.
POCKET_FRAC = 0.5


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

    def touches_edge(self, prev):
        """Does the REACHABLE set run off the side of the grid?

        NO SILENT CAPS. `s_half` bounds how far along the arc the search looks,
        and a room wider than that is a room searched in part -- which would
        read as "this is the best spot in the room" when it is the best spot in
        the slice that was looked at. A room's own walls normally stop the
        search long before the bound does; this says when they did not.

        REACHABLE, not free, and the difference is the whole point. The grid is
        deliberately wider than most rooms, so its edge columns usually sit
        inside the NEIGHBOURING rooms -- free floor a body in this room can
        never get to. Counting free cells there fired on every room and meant
        nothing. Counting reachable ones fires only when this room's own floor
        was cut off.
        """
        n = 0
        for k in range(self.nh):
            for i in (0, self.nw - 1):
                if prev[k * self.nw + i] != -1:
                    n += 1
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
    # Reported, never silently swallowed: reachable floor running off the side
    # of the grid means this room is wider than the arc that was looked along,
    # so the spot chosen is the best in a SLICE of the room and says so.
    rep["clipped_cells"] = g.touches_edge(prev)
    if not reach:
        rep["why"] = "nothing is reachable from the doorway"
        return [centre]

    # AND IS WHAT WE REACHED THE ROOM, OR A POCKET BESIDE ITS DOOR?
    #
    # THE GATE THIS MODULE SHIPPED WITHOUT, and it is the defect this module
    # exists to stop, committed here. `from_pt` is handed in as
    # `place.z + deck.room_interior_half_m - 0.5` -- a DECLARED depth. For most
    # places it lands in the doorway. For fourteen of the station's it does not:
    # `vorlon_berth`'s centre is 11.5 m from its corridor and its declared
    # half-depth is 4.0 m, so the probe sits against the room's FAR wall, snaps
    # to the 2x2 gap on the wrong side of it, and the search explores that gap.
    # Every one of those fourteen reported `reachable=4` -- 0.16 m2 of standable
    # floor -- and the first version of `--station` passed all 116 places,
    # because its criterion was "is ANYTHING reachable" and a pocket is
    # something. A gate that cannot fail for the thing it is named after.
    #
    # The tell is arithmetic and exact: all fourteen sat at `z_half - 0.1` from
    # their own centre, which is the topmost row of the grid. Identical failures
    # across unrelated places are one cause, not fourteen -- CLAUDE.md's own
    # "read the shape of a failing number before its size".
    #
    # SO THE TEST IS "HOW NEAR THE MIDDLE DID WE GET, RELATIVE TO THE ROOM'S OWN
    # SIZE", and it is deliberately not "is the exact centre cell reachable".
    # That stricter reading fails a genuine room with a table in the middle of
    # it, where the body IS in the room and standing beside the table; the two
    # cases separate cleanly on distance. Measured on the station, a pocket sits
    # at `z_half - 0.1` from the centre -- 97% of the room's own half-depth --
    # while a room entered properly lands within a metre or so of its middle.
    # A tiny reachable area is the second, independent trigger, because a
    # 0.16 m2 answer is a pocket whatever its distance says.
    #
    # Say so, and fall back to the register's centre point, which is what every
    # caller had before this module existed -- A ROUTE MUST NOT GET WORSE
    # BECAUSE A DIAGNOSIS FAILED.
    ci, ck = g.cell_of(0.0, z0)
    centre_reachable = prev[ck * g.nw + ci] != -1 if g.inside(ci, ck) else False
    rep["centre_reachable"] = centre_reachable
    rep["stand_m2"] = round(len(reach) * g.cell * g.cell, 3)

    # THE SPOT: the reachable cell nearest the register's centre. Not the
    # cell with the most clearance -- a body that walks to the emptiest corner
    # of a room is not standing where the room is.
    goal = min(reach, key=lambda n: ((n % g.nw) - ci) ** 2
               + ((n // g.nw) - ck) ** 2)
    gi, gk = goal % g.nw, goal // g.nw
    gc = g.centre_of(gi, gk)
    rep["off_centre_m"] = round(math.hypot(gc[0], gc[1] - z0), 3)
    rep["detour_m"] = 0.0

    if not centre_reachable and (rep["stand_m2"] < MIN_STAND_M2
                                 or rep["off_centre_m"] > POCKET_FRAC * z_half):
        rep["why"] = (f"the entry point is sealed off from this room's own "
                      f"floor -- {rep['stand_m2']:.2f} m2 reachable and the "
                      f"nearest standable cell is {rep['off_centre_m']:.2f} m "
                      f"from the middle of a room {z_half:.1f} m half-deep. The "
                      f"point came in as a DECLARED depth, not off the mesh")
        rep["pocket"] = True
        return [centre]

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
    if exact_centre:
        # The spot IS the register's point, so the cell-centre residue is an
        # artefact of the grid and not a distance anybody stands from anything.
        rep["off_centre_m"] = 0.0

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

    # A DOOR PROBE ON THE WRONG SIDE OF A WALL IS A POCKET, NOT A ROOM, and
    # this is the control for the defect `--station` shipped unable to see. Seal
    # the room off from the entry point with an unbroken partition: the search
    # then reaches a strip beside the probe and not the room, and the answer
    # must be "that is not the room" plus the register's centre -- NOT the best
    # cell in the strip. Fourteen of the station's places were in exactly this
    # state while the sweep reported 116 of 116 fine.
    v2, t2 = list(verts[:n_base_v]), list(tris[:n_base_t])

    def wall(z):
        i = len(v2)
        v2.extend([at(-13, z, 0.0), at(13, z, 0.0),
                   at(13, z, 2.0), at(-13, z, 2.0)])
        t2.append((i, i + 1, i + 2))
        t2.append((i, i + 2, i + 3))

    wall(4.4)                                  # unbroken, between door and room
    rep4 = {}
    path4 = approach(meta, place, v2, t2, groups=[("room", 0, len(t2))],
                     from_pt=door, z_half=6.0, report=rep4)
    check(rep4.get("pocket") is True,
          "CONTROL: an entry point sealed off from the room reads as a POCKET, "
          "not as the room", f"{rep4.get('stand_m2')} m2 reachable, "
          f"centre_reachable={rep4.get('centre_reachable')}")
    check(len(path4) == 1 and abs(path4[0][2] - z0) < 1e-6,
          "and it falls back to the register's centre, so a route cannot get "
          "WORSE because a diagnosis failed")
    # ...and with the same wall pierced by a doorway the room is reachable again,
    # which is what proves the check is about connectivity and not about walls.
    v3, t3 = list(verts[:n_base_v]), list(tris[:n_base_t])

    def pierced(z):
        i = len(v3)
        for s0, s1 in ((-13.0, -1.0), (1.0, 13.0)):
            i = len(v3)
            v3.extend([at(s0, z, 0.0), at(s1, z, 0.0),
                       at(s1, z, 2.0), at(s0, z, 2.0)])
            t3.append((i, i + 1, i + 2))
            t3.append((i, i + 2, i + 3))

    pierced(4.4)
    rep5 = {}
    approach(meta, place, v3, t3, groups=[("room", 0, len(t3))],
             from_pt=door, z_half=6.0, report=rep5)
    check(not rep5.get("pocket") and rep5.get("centre_reachable"),
          "and the SAME wall with a 2 m doorway in it is not a pocket",
          f"{rep5.get('stand_m2')} m2 reachable, "
          f"centre_reachable={rep5.get('centre_reachable')}")

    print(f"\n{'OK' if not fails else 'FAILED: ' + '; '.join(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------------------
# THE WHOLE-STATION QUESTION
# ---------------------------------------------------------------------------

def _at(radius, angle_deg, z):
    """Polar -> world on the ring. Three lines rather than an import, because
    `route_walk._at` is downstream of this module (route_walk -> walkable ->
    roomnav) and importing it back would be a cycle."""
    a = math.radians(angle_deg)
    return (radius * math.cos(a), radius * math.sin(a), z)


def station(limit=None, only=None, verbose=False):
    """Can a body get INTO every named place on the station, and stand up?

    THE ONE-ROOM FIX IS NOT THE FINDING. `business_center`'s doorway-to-desk
    line was fixed by building this module; whether the same defect sits in the
    other 127 places is a different question, and CLAUDE.md's session-4h lesson
    is exactly that a fix applied to an instance and not to the rule is a fix
    that will be needed again. So this asks every place the same question its
    own commute leg asks: from this room's own doorway, over this room's own
    collision, is there anywhere a capsule can stand?

    Two things FAIL, and both are "a player cannot get in":
      * the doorway has no free cell within `SNAP_MAX_M`  -- walled off
      * nothing is reachable from it                      -- a sealed room

    Everything else is REPORTED and not failed, because it is not a defect: a
    room whose middle is furniture legitimately has its standing spot off
    centre, and that number is what says how furnished the station is.
    """
    import deck as D                                             # noqa: PLC0415
    import directory as dr                                       # noqa: PLC0415
    import interior as it                                        # noqa: PLC0415

    schema, profile = it.load()
    if only:
        # Straight to the one cluster. Sweeping to find it builds every deck's
        # collision on the way, which turns a debugging aid into a whole-station
        # gate -- and then nobody uses the debugging aid.
        q = dr.by_key(only)
        decks = [(q["sector"], q["ring"], q["deck"])]
    else:
        decks = sorted({(q["sector"], q["ring"], q["deck"]) for q in dr.PLACES})
    rows, bad, skipped = [], [], []
    seen = set()
    for s, r, dk in decks:
        if (s, r) in getattr(D, "NOT_RING_DECKS", ()):
            skipped.append((s, r, dk, "drum -- a heightfield, not a corridor"))
            continue
        for zc in (D.z_clusters(s, r, dk) or [None]):
            try:
                v, t, meta = D.build_collision(schema, profile, s, r, dk,
                                               z_m=zc, props=True)
            except Exception as e:                               # noqa: BLE001
                skipped.append((s, r, dk, f"{type(e).__name__}: {e}"))
                continue
            groups = meta.get("groups") or ()
            fr = meta["floor_r_m"]
            for room in meta.get("rooms", ()):
                key = room["key"]
                if key in seen or (only and key != only):
                    continue
                seen.add(key)
                place = dr.by_key(key)
                zh = D.room_interior_half_m(schema, profile, place)
                door = _at(fr, room["door_deg"], place["z_m"] + zh - 0.5)
                rep = {}
                approach(meta, place, v, t, groups, from_pt=door, z_half=zh,
                         report=rep)
                row = {"key": key, "deck": f"{s}/{r}/{dk}", **rep}
                rows.append(row)
                if (rep.get("snap_m") is None or not rep.get("reachable")
                        or rep.get("pocket")):
                    bad.append(row)
                if verbose:
                    print(f"  {key:34s} {row['deck']:12s} "
                          f"obst {rep.get('obstacle_tris', 0):5d}  "
                          f"stand {rep.get('stand_m2', 0.0):8.2f} m2  "
                          f"off {rep.get('off_centre_m', 0.0):5.2f} m  "
                          f"snap {rep.get('snap_m')}  "
                          f"wp {rep.get('waypoints', 0)}"
                          + ("  POCKET" if rep.get("pocket") else ""))
                if limit and len(rows) >= limit:
                    break
            if limit and len(rows) >= limit:
                break
        if limit and len(rows) >= limit:
            break

    n = len(rows)
    exact = sum(1 for x in rows if x.get("exact_centre"))
    detoured = sum(1 for x in rows if x.get("waypoints", 1) > 1)
    clipped = [x for x in rows if x.get("clipped_cells")]
    offs = sorted(x.get("off_centre_m", 0.0) for x in rows)
    print(f"\n{n} places asked, {n - len(bad)} a body can get into and stand up "
          f"in, {len(bad)} it cannot")
    print(f"  {exact} stand at the register's own centre point -- the middle "
          f"of the room is standable")
    print(f"  {n - exact} stand somewhere else, because their middle is not")
    print(f"  {detoured} need more than one waypoint to GET there -- a straight "
          f"line from their door would cross their own furniture")
    print(f"  {n - detoured} are one waypoint, unchanged from before this "
          f"module existed")
    if offs:
        print(f"  off-centre: median {offs[len(offs) // 2]:.2f} m, "
              f"p95 {offs[int(0.95 * (len(offs) - 1))]:.2f} m, "
              f"max {offs[-1]:.2f} m")
    # NO SILENT CAPS -- say what was not looked at and what was looked at in
    # part, rather than letting either read as coverage.
    if clipped:
        print(f"  {len(clipped)} searched in part (free floor ran off the arc "
              f"half-span): {', '.join(x['key'] for x in clipped[:6])}"
              + (" ..." if len(clipped) > 6 else ""))
    for s, r, dk, why in skipped:
        print(f"  not asked: {s}/{r}/{dk} -- {why}")
    areas = sorted(x.get("stand_m2", 0.0) for x in rows)
    if areas:
        print(f"  standable floor reached: median {areas[len(areas) // 2]:.1f} "
              f"m2, min {areas[0]:.2f} m2")
    for x in bad:
        print(f"  CANNOT GET IN: {x['key']} ({x['deck']}) -- "
              f"{x.get('why', 'no standable cell reachable from its doorway')}")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--station", action="store_true",
                    help="ask every named place whether a body can get in "
                         "through its own door and stand up (minutes of CPU: "
                         "it builds every cluster's collision)")
    ap.add_argument("--place", default=None, help="just this one")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.station or a.place:
        return station(limit=a.limit or None, only=a.place,
                       verbose=a.verbose or bool(a.place))
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
