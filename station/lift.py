#!/usr/bin/env python3
"""THE LIFT -- a walkable vertical connection between two decks of one ring.

WHY THIS FILE EXISTS, and it is the shape of failure this project keeps finding.
`station/routes.py --report` measures the station's circulation and prints:

    lift     0 buildable of   38   <- 38 with NO GENERATOR

Meanwhile `station/transit.py` computes what a lift ride costs, its
`spoke_line()` returns a `spoke_lift` line with a headway and a mean wait,
`npc/navigation.py` has `lift_ride_s()` and threads NPC journeys through
`lift:` nodes with boarding and dwell, and `docs/gazetteer/LOCATIONS.md`
registers *Transport tubes / lifts (between levels)* as a location. Four
modules model a lift. **Nothing in this project had a lift you could walk
into.** The string `shaft` appeared nowhere as geometry; a ring is a dozen
decks stacked in RADIUS at `interior.DECK_PITCH_M` and there was no way from
one to the next.

That is the same defect as the corridor that had no doors and the deck that had
no collision: a number computed about a thing that does not exist. The
simulation was costing rides on it.

WHAT UP IS. On a spun ring the floor is the OUTSIDE of a barrel, so "up" points
at the station axis and a lift RISES TOWARD SMALLER RADIUS. `station/collision.py`
and `station/deck.py::_place_local` both state it; every radius in this file
follows them. `interior.decks_in_ring` returns a stack whose `floor_r_m`
DECREASES as you go up in a normal ring and INCREASES in the drum's outward
sub-floor stack, so the landings here are sorted by radius, never by index.

WHAT IS MEASURED AND WHAT IS EXTRAPOLATED. Everything dimensional in this file
comes from something else:

  rise per storey        `interior.decks_in_ring` -- the DIFFERENCE between two
                         landings' own floor radii, not `DECK_PITCH_M` restated
  car clear width/depth  `collision.corridor_profile()['half_w']` x 2 -- what
                         the corridor's narrowest pinch passes, the car passes
  car clear height       the same cast's `ceil_y - floor_y`
  landing aperture       `interior_kit.PROVISIONAL['door_width_m']` /
                         `['door_height_m']`, through `interior_kit.door_assembly`
                         -- the corridor's own door, not a second one
  running clearance      `interior.GUIDEWAY_SOFFIT_RELIEF_M` -- the only gap
                         this project states between a moving vehicle and the
                         fixed structure it passes
  sill running gap       `interior_kit.PROVISIONAL['wall_seam_m']`
  ride time              asserted against `npc/navigation.lift_ride_s` AND
                         `transit.climb_leg`, from a rise read off the mesh

The three genuinely unestablished decisions -- that the car is square in plan,
that its shell is built of the kit's own two plate thicknesses, and that the
shaft is a rectangular box rather than a bore -- are authority 5 and are written
up in `docs/lift-4g.md` (LIFT-1 .. LIFT-5).

THE LOCAL FRAME IS ORTHONORMAL AND THAT IS DELIBERATE. `deck._place_local` maps
a room through `a = a0 + x / radius`, which makes its walls RADIAL planes --
right for a room, because a room's floor follows the ring. A shaft is 7 m deep
in radius and its guide rails have to be PARALLEL, so `place()` here is a rigid
rotation: x tangential, y radially inward, z axial, with (x, y, z) right-handed
so winding survives untouched. The price is that the car's flat floor and the
deck's cylindrical one differ across the car's own width -- MEASURED at 2.8 mm
against `collision.STEP_TOLERANCE_M` of 5 mm, and gated, because a step at the
threshold is exactly what `collision.py` exists to prevent.

THE FIRST VERSION OF THIS FILE GATED 2, 3 AND 4 LANDINGS, AND THE STATION HAS
NO SUCH SHAFT. `interior.decks_in_ring` gives 7 to 28 decks a ring; only blue
ring 0 is as short as ten. So every closure, clearance and walk gate here ran on
the one case that does not ship, and at six landings the shaft opened -- 6 open
edges, appearing there and never growing. That is this repository's most-repeated
lesson arriving through a new door: `interior_kit._tag_coverage`'s `doors`
defaulted to nothing, so its coverage assertion ran on a corridor without the
pieces the defect was in; `interior_kit`'s closure gate cast rays UPWARD, which
cannot see a hole in a vertical surface. **A gate must build the case that
ships**, and `_selftest` now sweeps every landing count up to 28, the tallest
stack the station actually has.

AND THE DEFECT UNDERNEATH IT IS WORSE THAN A HOLE: IT IS A GATE THAT ANSWERS
DIFFERENTLY FOR THE SAME CODE. The shaft was closed all along and not WELDED --
`interior_kit._shell_from_pieces` leaves two vertices 42 nm apart where there
should be one (see `weld`), on every `bulkhead` and every `door_frame` on the
station, not just here. `interior.boundary_edges` keys on coordinates rounded to
4 decimals, so that crack reads as a hole exactly when the pair straddles a
0.1 mm grid line -- which depends on where in the station the geometry sits and
on nothing else. Measured: the identical unwelded mesh, 2,464 near-duplicate
pairs either way, gives 6 open edges at blue ring 1 / 140 deg / z 6880 and 0 at
grey ring 1 / 40 deg / z 3618. `weld` closes it at the source and
`near_duplicates` gates it in the frame the geometry was authored in, where the
answer does not depend on position.

Run: python3 station/lift.py --selftest
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import collision as C                                            # noqa: E402
import interior as it                                            # noqa: E402
import interior_kit as K                                         # noqa: E402
from npc import navigation as NAV                                # noqa: E402

# The gap between a moving vehicle and the fixed structure it passes.
# NOT A NEW NUMBER. `interior.GUIDEWAY_SOFFIT_RELIEF_M` is the only running
# clearance this project states -- it is why the guideway soffit sits inboard of
# the bottom chord's running face -- and a lift car in a shaft is the same
# problem at a smaller scale. Taking a second figure here would be two
# descriptions of one thing, which this repository has now been bitten by twice
# (the door decision made in the render and again in the shell; the corridor
# profile written down instead of measured).
RUN_CLEARANCE_M = it.GUIDEWAY_SOFFIT_RELIEF_M

# The gap between the car's sill and the landing sill. A sill is MEANT to run
# close -- it is the plate a foot crosses -- so it does not get the full running
# clearance, and the kit already states how wide a gap between two plates that
# must not touch is: `wall_seam_m`, the 38 mm recess between deck tiles and
# between wall plates. A 38 mm slot is not a hole a body falls through:
# `collision.floor_holes` samples at 0.35 m, a capsule diameter.
SILL_GAP_M = K.PROVISIONAL["wall_seam_m"]


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
# `_quad` is COPIED FROM `station/collision.py::_quad`, with attribution, rather
# than imported: that module is owned elsewhere and reaching into its private
# surface would couple this file to a name its owner never promised. The rule it
# encodes is not cosmetic -- Godot's ConcavePolygonShape3D has
# `backface_collision` off by default, so a floor wound the wrong way is a floor
# a body falls straight through.

def _quad(verts, tris, pts, want):
    """One quad, wound so its faces point the way `want` says."""
    base = len(verts)
    verts.extend(pts)
    for tri in ((base, base + 1, base + 2), (base, base + 2, base + 3)):
        p, q, s = (verts[j] for j in tri)
        u = [q[k] - p[k] for k in range(3)]
        w = [s[k] - p[k] for k in range(3)]
        nrm = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
               u[0] * w[1] - u[1] * w[0]]
        tris.append(tri if sum(nrm[k] * want[k] for k in range(3)) > 0
                    else (tri[0], tri[2], tri[1]))


def _rect(verts, tris, axis, at, u0, u1, v0, v1, want):
    """An axis-aligned rectangle in a plane of constant `axis` (0=x, 1=y, 2=z).

    `u`/`v` are the two remaining axes in cyclic order. Degenerate rectangles
    are dropped rather than emitted: a zero-area triangle has no normal, and
    they are a nuisance in every downstream count.
    """
    if u1 - u0 <= 1e-9 or v1 - v0 <= 1e-9:
        return
    au, av = (axis + 1) % 3, (axis + 2) % 3
    pts = []
    for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        p = [0.0, 0.0, 0.0]
        p[axis], p[au], p[av] = at, u, v
        pts.append(tuple(p))
    _quad(verts, tris, pts, want)


def _basis(angle_deg):
    """(origin-free) tangential, inward-radial and axial unit vectors at `angle`.

    RIGHT-HANDED, and it matters: ux X uy = uz exactly, so `place()` is a proper
    rotation of determinant +1 and every winding decision made in local
    coordinates survives the map into world space. The alternative -- deciding
    winding after placement -- is what `interior_kit._merge` needs its `flip`
    argument for, and it is a flag that gets forgotten.
    """
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return (-sa, ca, 0.0), (-ca, -sa, 0.0), (0.0, 0.0, 1.0)


def place(g, pts):
    """Shaft-local (x across, y inward/up, z along the ship) -> station world."""
    ux, uy, _uz = _basis(g["angle_deg"])
    ox, oy, oz = g["origin"]
    return [(ox + x * ux[0] + y * uy[0],
             oy + x * ux[1] + y * uy[1],
             oz + z) for x, y, z in pts]


# How near two vertices have to be before they are the same vertex. ONE
# MICROMETRE, and it is chosen against the two things it sits between rather
# than picked: the divergence it has to close is 4.2e-8 m (see `weld`), and the
# smallest real feature anywhere in this kit is `wall_seam_m` at 0.038 m. A
# micrometre is 24x the first and 38,000x the second, so there is no value in
# between that behaves differently. `weld`'s own gate is that it drops ZERO
# triangles: merging two vertices that are genuinely distinct must collapse a
# triangle, so a dropped triangle is the tolerance being too big, said by the
# data rather than by argument.
WELD_TOL_M = 1e-6


def weld(verts, tris, tol=WELD_TOL_M):
    """Merge vertices closer than `tol`. -> (verts, tris, merged, dropped)

    THE FIX FOR A CRACK THIS MODULE'S CLOSURE GATE COULD NOT SEE, and the
    defect is `interior_kit`'s rather than this file's -- see docs/lift-4g.md
    section 2.5 for the one-line patch. In short:

      `_shell_from_pieces` builds its T-junction point set as
      `pts = {_pkey(p) ...}`, i.e. coordinates ROUNDED TO 7 DECIMALS, and hands
      them to `_insert_collinear`, which appends them verbatim into loops whose
      own vertices are NOT rounded, guarded only by `dist(out[-1], q) > 1e-9`.
      `_pkey`'s granularity is 5e-8 and that guard is 1e-9 -- fifty times
      tighter -- so any vertex further than 1e-9 from its own rounding is
      inserted a second time, 4.2e-8 m from the first.

    The surface is genuinely closed; it is not welded. Two vertices stand where
    there should be one, so the two triangles either side of that seam do not
    share an edge, and `interior.boundary_edges` -- which keys on coordinates
    rounded to 4 decimals -- reports a hole exactly when the 42-nanometre pair
    happens to straddle a 0.1 mm grid line in world space. That is why the
    count was 0 at five landings, 6 at six, and 6 for ever after: **the geometry
    never changed, only where in space it sat.**

    A gate that answers differently for the same code depending on position is
    worse than one that fails, so this closes it at the source rather than
    widening the tolerance the gate measures at.

    NOT ROUNDING -- snapping to the first vertex seen within `tol`, through a
    spatial hash. Rounding has the identical failure one decimal down: two
    points 4.2e-8 apart still land in different buckets whenever they straddle a
    boundary, which is the whole bug. It moves no vertex more than `tol`,
    changes no silhouette, and drops no triangle.

    This is measured on 16 near-duplicate vertices in EVERY `bulkhead` on the
    station and 16 in every `door_frame`, so it is not a lift problem; it is a
    lift-shaped view of a station-wide one.
    """
    grid, out, index = {}, [], []
    for p in verts:
        c = (int(math.floor(p[0] / tol)), int(math.floor(p[1] / tol)),
             int(math.floor(p[2] / tol)))
        hit = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        q = out[j]
                        if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                                + (p[2] - q[2]) ** 2) <= tol * tol:
                            hit = j
                            break
                    if hit is not None:
                        break
                if hit is not None:
                    break
            if hit is not None:
                break
        if hit is None:
            hit = len(out)
            out.append(p)
            grid.setdefault(c, []).append(hit)
        index.append(hit)
    keep = []
    for a, b, c in tris:
        A, B, C = index[a], index[b], index[c]
        if A == B or B == C or C == A:
            continue
        keep.append((A, B, C))
    return out, keep, len(verts) - len(out), len(tris) - len(keep)


def near_duplicates(verts, lo=1e-12, hi=1e-4):
    """Pairs of vertices closer than `hi` and further apart than `lo`.

    THE GATE THAT DOES NOT DEPEND ON WHERE THE GEOMETRY SITS.
    `interior.boundary_edges` finds this crack only when the pair straddles its
    own rounding grid, which is a coin toss; this asks the question directly,
    in the frame the geometry was authored in, and fires on a two-landing shaft
    where the open-edge count needed six.
    """
    grid, out = {}, []
    cell = hi
    for p in verts:
        c = (int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)),
             int(math.floor(p[2] / cell)))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for q in grid.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        d = math.dist(p, q)
                        if lo < d < hi:
                            out.append((q, p, d))
        grid.setdefault(c, []).append(p)
    return out


def _to_world(g, verts, tris):
    """Weld in the frame the geometry was authored in, then place it.

    THE ORDER MATTERS. Welding after placement would run the tolerance against
    world coordinates 150 m from the axis and 6.9 km down the ship, where the
    seam is the same 42 nm but every neighbour lookup carries the round-off of
    a rotation. Local first, then one rigid map.
    """
    v, t, merged, dropped = weld(verts, tris)
    return place(g, v), t, merged, dropped


# ---------------------------------------------------------------------------
# The geometry, computed once and read by all three builders
# ---------------------------------------------------------------------------

def shaft_geometry(schema, profile, sector, ring_index, decks, angle_deg, z_m,
                   landing_side=1, p=None, prof=None, relief_m=None,
                   stack=None):
    """Every dimension of one lift, DERIVED, in one dict.

    ONE DICT AND NOT THREE FUNCTIONS' WORTH OF ARITHMETIC. `lift_shaft`,
    `lift_car` and `lift_collision` all read this, so the car cannot be built to
    one width and the shaft to another, and the collision cannot land on a floor
    the render does not have. It is hard rule 4 -- inside and outside from one
    schema -- applied inside a module rather than across two.

    `decks` are indices into `interior.decks_in_ring` at this z. They are sorted
    HERE, by floor radius descending, so the bottom landing is first whichever
    way the ring's stack happens to be numbered: a normal ring counts outward-in
    and the drum's sub-floor stack counts inward-out, and an index-ordered list
    would silently build one of them upside down.

    `landing_side` is +1 or -1 -- which of the two axial faces the doors are in.
    Same convention as `interior.ring_arc`'s door `side` and
    `collision.room_shell`'s `door_angle_deg`: a ring corridor runs at constant
    z, so a lift lobby off it sits beside it in z and its doors face along the
    ship.

    `relief_m` overrides the running clearance. It exists so the fit gate can
    have a NEGATIVE CONTROL that fires -- a shaft built tighter than its car has
    to be caught -- and it is a real parameter besides: a service shaft in a
    plant deck has no reason to carry the guideway's clearance.
    """
    p = p or K.PROVISIONAL
    q = prof or C.corridor_profile(None if p is K.PROVISIONAL else p)
    relief = RUN_CLEARANCE_M if relief_m is None else relief_m

    # `stack` OVERRIDES WHICH LANDINGS EXIST, and it is what lets one shaft
    # cross a ring boundary. A ring is a nested shell; `decks_in_ring` knows
    # only its own. `station/spoke_way.py` hands in two rings' decks sorted by
    # radius so a single column serves both, which is the difference between a
    # station in 8 pieces and a station in 1. Everything downstream reads
    # `floor_r_m` off these dicts and never asks which ring they came from.
    stack = (it.decks_in_ring(schema, profile, sector, ring_index, z_m=z_m)
             if stack is None else list(stack))
    if not stack:
        raise ValueError(f"{sector} ring {ring_index} carries no decks at "
                         f"z={z_m}: nothing for a lift to join")
    idx = sorted({int(d) for d in decks})
    for i in idx:
        if i < 0 or i >= len(stack):
            raise ValueError(f"deck {i} is not in {sector} ring {ring_index} "
                             f"at z={z_m} ({len(stack)} decks)")
    if len(idx) < 2:
        raise ValueError("a lift joins at least two decks; got "
                         f"{sorted(idx)}")

    # BOTTOM FIRST, BY RADIUS. Down is outward, so the largest floor radius is
    # the lowest landing.
    served = sorted((stack[i] for i in idx),
                    key=lambda d: -d["floor_r_m"])
    r0 = served[0]["floor_r_m"]
    walk0 = r0 - q["floor_y"]

    landings = []
    for n_, d in enumerate(served):
        landings.append({
            # `index` IS THE ONLY UNIQUE KEY A LANDING HAS, and `deck` is not
            # one. `deck_index` restarts at 0 in every ring, so the moment
            # `stack=` crosses a ring boundary the deck numbers repeat: blue
            # rings 0+1 at z=6880 gives [0..5, 0..11] over eighteen landings,
            # six of them addressed by a key that already means something else.
            # Counted from the BOTTOM, so it is stable under `stack=` and under
            # the drum's inverted numbering both.
            "index": n_,
            "deck": d["deck_index"],
            "floor_r_m": d["floor_r_m"],
            # The surface a boot rests on, which is NOT the deck datum: the grid
            # tiles stand 22 mm proud and `corridor_profile` takes the highest
            # thing underfoot. Up is inward, so proud is a SMALLER radius.
            "walk_r_m": d["floor_r_m"] - q["floor_y"],
            "y_m": r0 - d["floor_r_m"],
            "floor_g": d["floor_g"],
            "use": d["use"],
        })
    # The storey heights, MEASURED off the stack rather than restated from
    # `interior.DECK_PITCH_M`. If a caller serves decks 0 and 3 the storey is
    # three pitches and the shaft has to be that tall; asserting the constant
    # would build a shaft 7.2 m short and nothing downstream would notice.
    storeys = [landings[i + 1]["y_m"] - landings[i]["y_m"]
               for i in range(len(landings) - 1)]
    rise = landings[-1]["y_m"] - landings[0]["y_m"]

    # --- the car ---------------------------------------------------------
    # Clear width: the corridor's own measured clear width. Anything that fits
    # the corridor's narrowest pinch fits the car, which is the only property a
    # lift has to have -- a car narrower than the corridor is a bottleneck a
    # player meets by being unable to bring something through, and there is no
    # frame in the reference set that fixes a car's size (LIFT-1).
    clear_w = 2.0 * q["half_w"]
    # Depth: square in plan. EXTRAPOLATION, LIFT-2. A lobby meets a car at 90
    # degrees, so the longest rigid thing that can be presented to the door is
    # set by the corridor's clear width; a car shallower than it is wide cannot
    # take what the corridor delivers, and a square is the smallest plan that
    # can.
    clear_d = clear_w
    # Height: the corridor's measured headroom, for the same reason as the
    # width. A person who can stand in a corridor can stand in the car.
    clear_h = q["ceil_y"] - q["floor_y"]
    # Shell. Two thicknesses, both the kit's own and neither invented here: the
    # floor and roof carry load and take `ceiling_slab_m`, the side panels do
    # not and take `door_leaf_t_m`, the only sheet thickness the kit states for
    # a moving assembly (LIFT-3).
    slab_t = p["ceiling_slab_m"]
    wall_t = p["door_leaf_t_m"]
    ext_w = clear_w + 2.0 * wall_t
    ext_d = clear_d + 2.0 * wall_t
    ext_h = clear_h + 2.0 * slab_t

    # --- the shaft -------------------------------------------------------
    # The clear bore is the car plus the running clearance on every face.
    # NOTHING the shaft is made of may enter it; the walls are set back behind
    # whatever stands proud of them, so the guide rails' bullnose faces and the
    # wall plates' proud faces all land on or outside this line. `_selftest`
    # asserts it against the emitted vertices rather than against this comment.
    bore_hw = ext_w / 2.0 + relief
    bore_hd = ext_d / 2.0 + relief
    rail_proj = p["pilaster_proj_m"]
    plate_proud = p["wall_plate_proud_m"]
    wall_th = p["wall_thickness_m"]
    # Substrate faces, i.e. where the wall actually is.
    sub_hw = bore_hw + rail_proj          # the rails stand off it into the bore
    sub_hd_back = bore_hd + plate_proud   # the proud plates land on the bore
    sub_hd_door = bore_hd                 # a landing wall is flat; it is a door

    # The pit and the overhead. Both are the car's own overhang plus one
    # running clearance, so they follow the car and cannot be set independently.
    y_pit = -(slab_t + relief)
    y_top = landings[-1]["y_m"] + clear_h + slab_t + relief

    g = {
        "sector": sector,
        "ring_index": ring_index,
        # WHETHER `at_deck` MEANS ANYTHING ON THIS SHAFT. False as soon as a
        # `stack=` crosses a ring boundary, because `deck_index` restarts at 0
        # in every ring; `_landing` raises rather than guessing, and a caller
        # can read this ahead of time instead of finding out by exception.
        "deck_keys_unique": len({d["deck_index"] for d in served})
                            == len(served),
        "angle_deg": angle_deg,
        "z_m": z_m,
        "landing_side": 1 if landing_side >= 0 else -1,
        "origin": (walk0 * math.cos(math.radians(angle_deg)),
                   walk0 * math.sin(math.radians(angle_deg)), z_m),
        "datum_r_m": walk0,
        "landings": landings,
        "storeys_m": storeys,
        "rise_m": rise,
        "pitch_m": min(storeys) if storeys else 0.0,
        "car": {"clear_w": clear_w, "clear_d": clear_d, "clear_h": clear_h,
                "ext_w": ext_w, "ext_d": ext_d, "ext_h": ext_h,
                "wall_t": wall_t, "slab_t": slab_t},
        "shaft": {"bore_hw": bore_hw, "bore_hd": bore_hd,
                  "sub_hw": sub_hw, "sub_hd_back": sub_hd_back,
                  "sub_hd_door": sub_hd_door, "wall_t": wall_th,
                  "rail_proj": rail_proj, "plate_proud": plate_proud,
                  "y_pit": y_pit, "y_top": y_top,
                  "depth_m": y_top - y_pit},
        "door": {"w": p["door_width_m"], "h": p["door_height_m"],
                 "frame_m": p["door_frame_m"],
                 "frame_depth_m": p["door_frame_depth_m"],
                 "sill_m": p["door_sill_m"]},
        "relief_m": relief,
        "sill_gap_m": SILL_GAP_M,
        "profile": q,
        "p": p,
        # Asserted against `transit.climb_leg` in `_selftest`, from a rise read
        # off the emitted collision rather than off this dict.
        "ride_s": NAV.lift_ride_s(schema, rise),
        "v_cap_m_s": NAV.coriolis_speed_cap(schema),
    }
    return g


def car_fit(g):
    """What the car actually clears, in metres, per face. All must be > 0.

    Reported as numbers rather than a boolean because a fit gate that says
    "yes" tells you nothing about how close it came, and because the sill is
    DELIBERATELY tight and has to be visible as its own figure rather than
    dragging the minimum down and reading as a defect.
    """
    car, sh = g["car"], g["shaft"]
    return {
        "tangential_m": sh["bore_hw"] - car["ext_w"] / 2.0,
        "axial_m": sh["bore_hd"] - car["ext_d"] / 2.0,
        "pit_m": -sh["y_pit"] - car["slab_t"],
        "overhead_m": sh["y_top"] - (g["landings"][-1]["y_m"] + car["clear_h"]
                                     + car["slab_t"]),
        # The one that decides whether a car can stop at the landing ABOVE the
        # one it is at: if the car is taller than a storey its roof fouls the
        # next floor slab and the shaft is a one-storey lift with extra doors.
        "storey_headroom_m": (min(g["storeys_m"]) - car["ext_h"]
                              if g["storeys_m"] else 0.0),
        "sill_m": g["sill_gap_m"],
    }


# ---------------------------------------------------------------------------
# Render geometry
# ---------------------------------------------------------------------------

def lift_shaft(schema, profile, sector, ring_index, decks, angle_deg, z_m,
               landing_side=1, p=None, prof=None, relief_m=None, g=None,
               door_leaves=True, landings=True, stack=None, weld_mesh=True):
    """The shaft and its landings, spanning `decks`. -> (verts, tris, meta)

    Same argument shape as `interior.ring_arc` / `interior.axial_run`,
    deliberately: they are the three corridors of this station -- one bent round
    the axis, one run along it, one stood on end -- and a divergence between
    their signatures is a divergence waiting to happen.

    BUILT OF CLOSED SOLIDS, NOT OF SURFACES, which is the kit's own idiom and
    the reason `interior.boundary_edges` reads 0 on it. A shaft modelled as a
    tube would be a surface with a hole at every landing, and a hole in a
    surface is an open edge unless it is rimmed -- the defect that shipped on
    every door on this station for four sessions. Here the landings are
    `interior_kit.door_assembly`, the same closed plate-with-a-hole the corridor
    uses, so the aperture a player walks through is closed by the same code that
    closes the corridor's.

    NOTHING IS COINCIDENT. Adjacent pieces OVERLAP rather than butting -- the
    trick `door_frame` states in its own comment, "so the two rings overlap
    rather than meeting on a shared face; coincident faces are a depth-sort coin
    toss". Two solids that touch exactly share edges, which `boundary_edges`
    reports as non-manifold and a renderer reports as z-fighting.

    `landings=False` SUPPRESSES THE APERTURES and is the negative control for
    the gate that says a landing is a hole a body can cross. It is a parameter
    rather than a test fixture because a blind shaft -- one that passes a deck
    without serving it -- is a real thing a station has.
    """
    if g is None:
        g = shaft_geometry(schema, profile, sector, ring_index, decks,
                           angle_deg, z_m, landing_side=landing_side, p=p,
                           prof=prof, relief_m=relief_m, stack=stack)
    p = g["p"]
    sh, door = g["shaft"], g["door"]
    ls = g["landing_side"]
    t = sh["wall_t"]
    y0, y1 = sh["y_pit"], sh["y_top"]
    seam = p["wall_seam_m"]

    verts, tris = [], []
    K.reset_tags()

    # --- the four walls' substrate ---------------------------------------
    # The two tangential walls own the corners and run the full section; the two
    # axial walls stop half a thickness inside them, so every join is an
    # interpenetration and never a shared face.
    # WRITTEN IN SIGNED POSITIONS, not in "back" and "front", because the two
    # hands are a real parameter and an axis written as though the door were
    # always on +z leaves a sliver of unbuilt corner on the other one.
    z_door = ls * sh["sub_hd_door"]
    z_back = -ls * sh["sub_hd_back"]
    z_lo, z_hi = min(z_door, z_back), max(z_door, z_back)
    proud = sh["plate_proud"]
    with K.tag('wall_panel'):
        for sx in (-1.0, 1.0):
            x_in, x_out = sx * sh["sub_hw"], sx * (sh["sub_hw"] + t)
            K._slab(verts, tris, min(x_in, x_out), max(x_in, x_out),
                    y0 - t, y1 + t, z_lo - t, z_hi + t)
        # The blind wall -- the one with no doors in it.
        zb2 = z_back - ls * t
        K._slab(verts, tris, -(sh["sub_hw"] + t / 2.0), sh["sub_hw"] + t / 2.0,
                y0 - t, y1 + t, min(z_back, zb2), max(z_back, zb2))

    # --- proud wall plates on the three blind faces ----------------------
    # The corridor's own wall language, applied to a shaft: plates standing
    # `wall_plate_proud_m` off the substrate with `wall_seam_m` recessed joints.
    # A 10 m unbroken plane is the blankest surface a frame can have and it is
    # the one the eye lands on; this is what `deck_grid` exists for on the deck
    # and `wall_panel` on the wall.
    plate_l = p["wall_plate_l_m"]
    ny = max(1, int(round((y1 - y0) / plate_l)))
    nz = max(1, int(round((z_hi - z_lo) / plate_l)))
    nx = max(1, int(round(2.0 * sh["sub_hw"] / plate_l)))
    with K.tag('wall_panel'):
        for k in range(ny):
            ya = y0 + (y1 - y0) * k / ny + seam / 2.0
            yb = y0 + (y1 - y0) * (k + 1) / ny - seam / 2.0
            for sx in (-1.0, 1.0):
                xa, xb = sx * sh["sub_hw"], sx * (sh["sub_hw"] - proud)
                for j in range(nz):
                    za = z_lo + (z_hi - z_lo) * j / nz
                    zb = z_lo + (z_hi - z_lo) * (j + 1) / nz
                    K._slab(verts, tris, min(xa, xb), max(xa, xb), ya, yb,
                            za + seam / 2.0, zb - seam / 2.0)
            za, zb = z_back, z_back + ls * proud
            for j in range(nx):
                xa = -sh["sub_hw"] + 2.0 * sh["sub_hw"] * j / nx
                xb = -sh["sub_hw"] + 2.0 * sh["sub_hw"] * (j + 1) / nx
                K._slab(verts, tris, xa + seam / 2.0, xb - seam / 2.0, ya, yb,
                        min(za, zb), max(za, zb))

    # --- guide rails -----------------------------------------------------
    # `interior_kit.pilaster`, unmodified: a bullnose column standing off a wall
    # with a segmented light strip in its face. That is exactly what a guide
    # rail in a lit shaft is, it is already a closed solid the kit's own
    # selftest asserts the winding of, and `materials.py` already binds
    # `pilaster` and `light_pilaster_strip` -- so a shaft takes no new material
    # and cannot land on the glTF fallback (session 4f's finding).
    rail_h = (y1 + t) - (y0 - t)
    for sx in (-1.0, 1.0):
        rv, rt = K.pilaster(rail_h, p)
        # authored bulging toward +x, width along z, standing at y = 0
        if sx < 0:
            K._merge(verts, tris, rv, rt,
                     offset=(-sh["sub_hw"], y0 - t, 0.0))
        else:
            K._merge(verts, tris, rv, rt, K._rot_y(180.0),
                     (sh["sub_hw"], y0 - t, 0.0))

    # --- the pit floor and the overhead cap -------------------------------
    # Both reach half a wall thickness into the walls, so their edges are inside
    # solid rather than coplanar with it.
    with K.tag('deck_panel'):
        K._slab(verts, tris, -(sh["sub_hw"] + t / 2.0), sh["sub_hw"] + t / 2.0,
                y0 - t / 2.0, y0, z_lo - t / 2.0, z_hi + t / 2.0)
    with K.tag('ceiling_slab'):
        K._slab(verts, tris, -(sh["sub_hw"] + t / 2.0), sh["sub_hw"] + t / 2.0,
                y1, y1 + t / 2.0, z_lo - t / 2.0, z_hi + t / 2.0)

    # --- the landing wall, storey by storey -------------------------------
    # Each storey's plate is `interior_kit.door_assembly` -- bulkhead, frame and
    # leaves -- placed so the bulkhead occupies exactly the wall thickness and
    # the frame stands proud on the LOBBY side, which is where it is seen from
    # and is what keeps the bore clear for the car. `corridor_section` does the
    # same thing with the same numbers on a corridor wall.
    #
    # THE ASSEMBLY IS TURNED TO FACE THE LOBBY, AND THE FIRST VERSION WAS NOT.
    # `door_frame` carries a head indicator and a control panel that stand 50 mm
    # PROUD of its -z face; placed the other way up they sat 50 mm inside the
    # bore, which is 12 vertices in the volume the car runs through. The bore
    # gate below found it, which is the whole reason that gate asks about
    # emitted vertices rather than about the arithmetic that produced them.
    fd = door["frame_depth_m"]
    off = ls * (sh["sub_hd_door"] + fd / 2.0)
    placed = []
    n = len(g["landings"])
    for i, lg in enumerate(g["landings"]):
        lo = (y0 - t) - lg["y_m"] if i == 0 else -door["frame_m"]
        hi = ((y1 + t) - lg["y_m"] if i == n - 1
              else g["landings"][i + 1]["y_m"] - lg["y_m"])
        hw = sh["sub_hw"] + t / 2.0
        rect = [(-hw, lo), (hw, lo), (hw, hi), (-hw, hi)]
        if landings:
            v, tt = K.door_assembly(p, section=rect, depth=(0.0, t),
                                    leaves=door_leaves)
            placed.append({"deck": lg["deck"], "y_m": lg["y_m"],
                           "walk_r_m": lg["walk_r_m"],
                           "z_m": z_m + off, "side": ls})
        else:
            # THE CONTROL. A blind storey: the same plate with no hole in it.
            v, tt = [], []
            with K.tag('bulkhead'):
                K._slab(v, tt, -hw, hw, lo, hi, 0.0, t)
        if ls > 0:
            K._merge(verts, tris, v, tt, K._rot_y(180.0),
                     (0.0, lg["y_m"], off))
        else:
            K._merge(verts, tris, v, tt, offset=(0.0, lg["y_m"], off))

        # The landing sill: the plate a foot crosses, from the bore line out
        # past the frame into the lobby. Fixed, unlike the car's own sill.
        with K.tag('deck_panel'):
            sw = door["w"] / 2.0 + door["frame_m"]
            za = ls * sh["bore_hd"]
            zb = ls * (sh["sub_hd_door"] + t + fd / 2.0)
            K._slab(verts, tris, -sw, sw,
                    lg["y_m"] - p["ceiling_slab_m"], lg["y_m"],
                    min(za, zb), max(za, zb))

    meta = {
        "sector": sector, "ring_index": ring_index,
        "angle_deg": angle_deg, "z_m": z_m,
        "landing_side": ls,
        "decks": [lg["deck"] for lg in g["landings"]],
        "landings_at": placed,
        "rise_m": round(g["rise_m"], 4),
        "depth_m": round(sh["depth_m"], 4),
        "bore_m": (round(2 * sh["bore_hw"], 4), round(2 * sh["bore_hd"], 4)),
        "radius_m": (round(g["landings"][0]["floor_r_m"], 3),
                     round(g["landings"][-1]["floor_r_m"], 3)),
        "gravity_g": (g["landings"][0]["floor_g"], g["landings"][-1]["floor_g"]),
        "ride_s": round(g["ride_s"], 4),
        "triangles": len(tris),
        "groups": K.tagged_spans(tris),
        "geometry": g,
    }
    # `weld_mesh=False` IS THE NEGATIVE CONTROL, and it is a parameter rather
    # than a test fixture because the raw output is what the kit hands back and
    # a reader is entitled to see it. Unwelded, this mesh carries 102 pairs of
    # vertices 42 nm apart per landing and `interior.boundary_edges` reports
    # them as holes at some heights and not others.
    if not weld_mesh:
        return place(g, verts), tris, dict(meta, welded_verts=0,
                                           welded_dropped_tris=0)
    wv, wt, merged, dropped = _to_world(g, verts, tris)
    meta["welded_verts"] = merged
    meta["welded_dropped_tris"] = dropped
    return wv, wt, meta


def lift_car(schema, profile, sector=None, ring_index=None, decks=None,
             angle_deg=None, z_m=None, g=None, at_deck=None,
             open_fraction=0.0, p=None, prof=None, relief_m=None,
             landing_side=1, stack=None):
    """The car, as its own group so the engine can move it.

    ITS OWN MESH, ON PURPOSE, and for the reason `collision.door_panel` states:
    the piece that moves has to be separate or the runtime cannot move it
    without touching the shaft. The car is emitted parked at `at_deck` --
    defaulting to the bottom landing -- and travelling is a translation along
    the shaft's own inward-radial axis, which is `_basis(angle_deg)[1]`.

    `open_fraction` drives the car's own leaves through
    `interior_kit.door_leaf`, so a car door and a corridor door are the same
    mechanism at the same fraction and cannot drift.
    """
    if g is None:
        g = shaft_geometry(schema, profile, sector, ring_index, decks,
                           angle_deg, z_m, landing_side=landing_side, p=p,
                           prof=prof, relief_m=relief_m, stack=stack)
    p = g["p"]
    car, sh, door = g["car"], g["shaft"], g["door"]
    ls = g["landing_side"]
    y_at = _landing(g, at_deck)["y_m"]
    hw, hd = car["clear_w"] / 2.0, car["clear_d"] / 2.0
    wt, st = car["wall_t"], car["slab_t"]
    ch = car["clear_h"]

    verts, tris = [], []
    K.reset_tags()

    # Floor. On the door side it runs out past the car's own skin to within
    # `SILL_GAP_M` of the landing sill -- that overhang IS the car sill, the
    # plate a foot crosses, and building it as part of the floor is what stops
    # it being a second object that can drift away from the floor it belongs to.
    z_sill = ls * (sh["bore_hd"] - g["sill_gap_m"])
    z_back = -ls * (hd + wt)
    with K.tag('deck_panel'):
        K._slab(verts, tris, -(hw + wt), hw + wt, -st, 0.0,
                min(z_back, z_sill), max(z_back, z_sill))
    with K.tag('deck_grid'):
        # The corridor's own tile grid, so the floor of a car and the floor of
        # the corridor it opens onto are the same surface.
        v, t2 = K.deck_grid(2.0 * hd, 2.0 * hw, p)
        K._merge(verts, tris, v, t2, lambda x, y, z: (x, y, z),
                 (0.0, 0.0, -hd))
    with K.tag('ceiling_slab'):
        K._slab(verts, tris, -(hw + wt), hw + wt, ch, ch + st,
                -(hd + wt), hd + wt)

    # Walls. The tangential pair own the corners and run the full depth; the
    # back wall stops half a thickness inside them. Both overlap the floor and
    # roof slabs rather than sitting on them.
    with K.tag('wall_panel'):
        for sx in (-1.0, 1.0):
            K._slab(verts, tris, min(sx * hw, sx * (hw + wt)),
                    max(sx * hw, sx * (hw + wt)), -st / 2.0, ch + st / 2.0,
                    -(hd + wt), hd + wt)
        zb, zb2 = -ls * hd, -ls * (hd + wt)
        K._slab(verts, tris, -(hw + wt / 2.0), hw + wt / 2.0,
                -st / 2.0, ch + st / 2.0, min(zb, zb2), max(zb, zb2))

    # The car's door wall: the same `door_assembly` the shaft's landings use,
    # set so its outermost face is flush with the car's skin and its deep reveal
    # falls INSIDE the car, which is the side it is looked at from.
    fd = door["frame_depth_m"]
    off = ls * (hd + wt - fd / 2.0)
    rect = [(-(hw + wt / 2.0), -st / 2.0), (hw + wt / 2.0, -st / 2.0),
            (hw + wt / 2.0, ch + st / 2.0), (-(hw + wt / 2.0), ch + st / 2.0)]
    v, t2 = K.door_assembly(p, section=rect, depth=(fd / 2.0 - wt, fd / 2.0),
                            open_fraction=open_fraction)
    if ls > 0:
        K._merge(verts, tris, v, t2, offset=(0.0, 0.0, off))
    else:
        K._merge(verts, tris, v, t2, K._rot_y(180.0), (0.0, 0.0, off))

    # Handrail on the three blind faces -- the kit's own, and the dominant warm
    # accent in every interior frame in the reference set.
    #
    # EVERY REMAP HERE IS A PROPER ROTATION, det +1, and the first version's
    # were not: `(x, y, z) -> (x, z, y)` is an axis SWAP, determinant -1, which
    # turns a closed solid inside-out and would have needed `_merge`'s `flip` to
    # undo. `handrail` is authored with **Z up** and +Y as its wall normal (read
    # off its `bar()` calls, not assumed), so each face below gets the rotation
    # that carries handrail-Z to car-Y and handrail-Y to the car's interior.
    #
    # AND THEY STOP 250 mm SHORT OF EACH CORNER. At 100 mm the back rail's end
    # post and the side rail's end post shared an exact vertical edge -- one
    # non-manifold edge in the car, found by the closure gate below and not by
    # looking at it. A rail that dies into a corner post is also simply what a
    # rail does; the defect and the detail have the same fix.
    ret = 0.25
    if ls > 0:
        back_map = (lambda x, y, z: (-x, z, y))     # +y -> +z, +z -> up
        back_x = hw - ret
    else:
        back_map = (lambda x, y, z: (x, z, -y))     # +y -> -z, +z -> up
        back_x = -(hw - ret)
    K._merge(verts, tris, *K.handrail(2.0 * (hw - ret)), back_map,
             (back_x, 0.0, -ls * (hd - 0.03)))
    for sx, smap in ((-1.0, lambda x, y, z: (y, z, x)),
                     (1.0, lambda x, y, z: (-y, z, -x))):
        rv, rt = K.handrail(2.0 * (hd - ret))
        K._merge(verts, tris, rv, rt, smap,
                 (sx * (hw - 0.03), 0.0, sx * (hd - ret)))

    # Ceiling light. `light_downlight` is a bound material; a new name would
    # take the glTF fallback and no scan over source would see it (session 4f).
    with K.tag('light_downlight'):
        K._slab(verts, tris, -hw * 0.55, hw * 0.55, ch - 0.06, ch - 0.01,
                -hd * 0.55, hd * 0.55)
    # Car operating panel -- the floor buttons. ON THE SIDE WALL BESIDE THE
    # DOOR, not on the door wall: the aperture is 1.5 m of a 2.16 m wall, so
    # anything mounted on that wall within reach of the door is inside the
    # doorway. `door_frame` already carries the door's own control panel.
    with K.tag('wall_reveal'):
        K._slab(verts, tris, hw - 0.05, hw, 0.95, 1.62,
                min(ls * (hd - 0.75), ls * (hd - 0.18)),
                max(ls * (hd - 0.75), ls * (hd - 0.18)))

    _at = _landing(g, at_deck)
    meta = {
        "at_deck": _at["deck"],
        "at_landing": _at["index"],
        "y_m": y_at,
        "walk_r_m": _at["walk_r_m"],
        "clear_w_m": round(car["clear_w"], 4),
        "clear_d_m": round(car["clear_d"], 4),
        "clear_h_m": round(car["clear_h"], 4),
        "ext_h_m": round(car["ext_h"], 4),
        "open_fraction": open_fraction,
        "travel_axis": _basis(g["angle_deg"])[1],
        "triangles": len(tris),
        "groups": K.tagged_spans(tris),
        "geometry": g,
    }
    # Emitted PARKED: every local y is shifted by the landing's own y before the
    # rigid map into world space.
    wv, wt, merged, dropped = _to_world(
        g, [(x, y + y_at, z) for x, y, z in verts], tris)
    meta["welded_verts"] = merged
    meta["welded_dropped_tris"] = dropped
    return wv, wt, meta


def _landing(g, at_deck):
    """Which landing `at_deck` means. -> a landing dict.

    A SHAFT'S ADDRESS SPACE IS ITS LANDINGS, and a deck number is only a NAME
    for one of them -- a name that stops working the moment `stack=` crosses a
    ring boundary. `deck_index` restarts at 0 in every ring, so blue rings 0+1
    at z=6880 gives eighteen landings numbered [0..5, 0..11] and six of them
    share a name with a landing 21.6 m below. The first version returned
    `hits[0]` and parked the car on the wrong floor for six of eighteen,
    SILENTLY -- and no gate could fail for it, because a car parked at the
    wrong landing is a perfectly good car at a perfectly good landing. It took
    building the two-ring case to see it.

    So the resolution order is: the canonical key first, the derived one only
    while it is still a key.

      * a landing dict out of `g["landings"]` -- always unambiguous, and what
        to pass when the shaft crosses a ring;
      * an int, while `g["deck_keys_unique"]` -- the deck number, unchanged for
        every single-ring caller and for the drum's inverted numbering both;
      * an int, when it is NOT -- the landing `index`, counted from the bottom,
        because when deck numbers repeat they are not a naming of the landings
        at all and `index` is the only naming left. This is stated rather than
        silent: `g["deck_keys_unique"]` says which reading is in force before
        the call, and both builders report `meta["at_landing"]` after it.

    The two readings AGREE wherever deck numbers are unique, which is every
    shaft this module built before `stack=` existed, so nothing moved under an
    existing caller.
    """
    if at_deck is None:
        return g["landings"][0]
    if isinstance(at_deck, dict):
        for lg in g["landings"]:
            if lg["index"] == at_deck.get("index"):
                return lg
        raise ValueError(
            f"landing {at_deck.get('index')} is not on this shaft "
            f"({len(g['landings'])} landings)")
    if g.get("deck_keys_unique", True):
        for lg in g["landings"]:
            if lg["deck"] == at_deck:
                return lg
        raise ValueError(f"deck {at_deck} is not served by this shaft "
                         f"({[lg['deck'] for lg in g['landings']]})")
    for lg in g["landings"]:
        if lg["index"] == at_deck:
            return lg
    raise ValueError(
        f"landing {at_deck} is not on this shaft. Its deck numbers repeat "
        f"({[lg['deck'] for lg in g['landings']]}) because `stack=` crosses a "
        f"ring boundary, so an int addresses the landing INDEX here, 0 to "
        f"{len(g['landings']) - 1} from the bottom. Pass g['landings'][i] to "
        f"be explicit.")


# ---------------------------------------------------------------------------
# Collision
# ---------------------------------------------------------------------------

def lift_collision(schema, profile, sector=None, ring_index=None, decks=None,
                   angle_deg=None, z_m=None, g=None, at_deck=None,
                   landings=True, car=True, p=None, prof=None, relief_m=None,
                   landing_side=1, stack=None):
    """The smooth shell a body stands in. -> (verts, tris, meta)

    COLLISION IS NOT RENDER GEOMETRY -- `station/collision.py`'s whole subject,
    and it applies here twice over. The shaft's render walls carry 45 mm proud
    plates and a 170 mm bullnose rail; a capsule brushing those catches on an
    internal edge exactly as it did on the corridor's 22 mm tile seams. So the
    collision bore is the CLEAR box the geometry dict already defines, at
    `bore_hw` x `bore_hd`, which is the line every solid piece was set back
    behind. The shell is measured off the same dict the render is, so the two
    cannot drift.

    THE CAR IS ITS OWN GROUP, `lift_car`, for the same reason
    `collision.door_panel` is: it moves, and the runtime has to be able to move
    exactly that and nothing else.

    `landings=False` seals every aperture. It is the negative control for the
    gate that says a landing is a hole a body can cross, and the same control
    the render builder takes.

    `car=False` omits the car, which is what the shaft looks like when the car
    is somewhere else -- and is the control for the gate that says there is a
    floor to stand on.
    """
    if g is None:
        g = shaft_geometry(schema, profile, sector, ring_index, decks,
                           angle_deg, z_m, landing_side=landing_side, p=p,
                           prof=prof, relief_m=relief_m, stack=stack)
    sh, cr, door = g["shaft"], g["car"], g["door"]
    ls = g["landing_side"]
    hw, hd = sh["bore_hw"], sh["bore_hd"]
    y0, y1 = sh["y_pit"], sh["y_top"]
    dw, dh = door["w"] / 2.0, door["h"]

    verts, tris, groups = [], [], []

    def group(name, fn):
        lo = len(tris)
        fn()
        if len(tris) > lo:
            groups.append((name, lo, len(tris)))

    def shell():
        # Tangential walls, facing into the bore.
        for sx in (-1.0, 1.0):
            _rect(verts, tris, 0, sx * hw, y0, y1, -hd, hd,
                  (-sx, 0.0, 0.0))
        # The blind axial wall, facing into the bore.
        _rect(verts, tris, 2, -ls * hd, -hw, hw, y0, y1, (0.0, 0.0, ls))
        # The pit floor: faces INWARD, which is up. A body that gets into the
        # shaft with the car elsewhere lands here rather than falling outward
        # under spin gravity for 30 km, which is what happened at the first
        # doorway this project built (`collision.floor_holes`).
        _rect(verts, tris, 1, y0, -hd, hd, -hw, hw, (0.0, 1.0, 0.0))
        # The overhead, facing back down.
        _rect(verts, tris, 1, y1, -hd, hd, -hw, hw, (0.0, -1.0, 0.0))

        # The landing wall, broken at each landing by the aperture. NO SILL in
        # the collision: the visible door has a 100 mm one and a 100 mm
        # vertical face is a wall to a capsule, not a step -- `corridor_shell`
        # makes the identical decision for the identical reason.
        face = (0.0, 0.0, -ls)
        cuts = []
        if landings:
            cuts = sorted((lg["y_m"], lg["y_m"] + dh) for lg in g["landings"])
        at = y0
        for c0, c1 in cuts:
            c0, c1 = max(c0, y0), min(c1, y1)
            if c1 <= at:
                continue
            if c0 > at:
                _rect(verts, tris, 2, ls * hd, -hw, hw, at, c0, face)
            # Beside the aperture, full height of the band.
            _rect(verts, tris, 2, ls * hd, -hw, -dw, c0, c1, face)
            _rect(verts, tris, 2, ls * hd, dw, hw, c0, c1, face)
            at = c1
        if at < y1:
            _rect(verts, tris, 2, ls * hd, -hw, hw, at, y1, face)

    def sills():
        # The fixed landing threshold, from the bore line out past the frame.
        z_out = ls * (sh["sub_hd_door"] + sh["wall_t"]
                      + door["frame_depth_m"] / 2.0)
        for lg in g["landings"]:
            _rect(verts, tris, 1, lg["y_m"],
                  min(ls * hd, z_out), max(ls * hd, z_out), -dw, dw,
                  (0.0, 1.0, 0.0))

    def carbox():
        y_at = _landing(g, at_deck)["y_m"]
        chw, chd, ch = cr["clear_w"] / 2.0, cr["clear_d"] / 2.0, cr["clear_h"]
        z_sill = ls * (hd - g["sill_gap_m"])
        z_back = -ls * chd
        # THE FLOOR, and it is the one surface this whole module exists to put
        # under a player. Faces inward, which is up on a spun ring.
        _rect(verts, tris, 1, y_at, min(z_back, z_sill), max(z_back, z_sill),
              -chw, chw, (0.0, 1.0, 0.0))
        _rect(verts, tris, 1, y_at + ch, -chd, chd, -chw, chw,
              (0.0, -1.0, 0.0))
        for sx in (-1.0, 1.0):
            _rect(verts, tris, 0, sx * chw, y_at, y_at + ch, -chd, chd,
                  (-sx, 0.0, 0.0))
        _rect(verts, tris, 2, z_back, -chw, chw, y_at, y_at + ch,
              (0.0, 0.0, ls))
        # The door face: jambs either side and a header over, so the aperture
        # is genuinely open when the car is at a landing and the car is
        # otherwise a closed box.
        zf = ls * chd
        face = (0.0, 0.0, -ls)
        _rect(verts, tris, 2, zf, -chw, -dw, y_at, y_at + ch, face)
        _rect(verts, tris, 2, zf, dw, chw, y_at, y_at + ch, face)
        _rect(verts, tris, 2, zf, -dw, dw, y_at + dh, y_at + ch, face)

    group("lift_shaft", shell)
    group("lift_sill", sills)
    if car:
        group("lift_car", carbox)

    meta = {
        "sector": g["sector"], "ring_index": g["ring_index"],
        "angle_deg": g["angle_deg"], "z_m": g["z_m"],
        "landing_side": ls,
        "at_deck": _landing(g, at_deck)["deck"] if car else None,
        "at_landing": _landing(g, at_deck)["index"] if car else None,
        "bore_hw_m": round(hw, 4), "bore_hd_m": round(hd, 4),
        "y_pit_m": round(y0, 4), "y_top_m": round(y1, 4),
        "landings": [{"index": lg["index"], "deck": lg["deck"],
                      "y_m": round(lg["y_m"], 4),
                      "walk_r_m": round(lg["walk_r_m"], 4)}
                     for lg in g["landings"]],
        "groups": groups,
        "triangles": len(tris),
        "geometry": g,
    }
    # THE COLLISION SHELL IS NOT WELDED, and that is deliberate. It is an open
    # surface of independent single-sided quads -- `corridor_shell` is the same
    # -- so it has no seams to close, and welding it would join the car group
    # to the shaft group at any vertex they happened to share, which is exactly
    # the thing the runtime has to be able to move apart.
    return place(g, verts), tris, meta


def stand_in_car(g, at_deck=None, above_m=0.05, x_m=0.0, z_m=0.0):
    """Where to put a body so it starts on the car's floor.

    `above_m` is small ON PURPOSE, and the reason is `collision.stand_at`'s:
    a spawn is a claim that a person can stand at a place, and a claim that
    needs a metre of falling to resolve is being hoped for, not checked.
    """
    y = _landing(g, at_deck)["y_m"] + above_m
    return place(g, [(x_m, y, z_m)])[0]


def ride_s(schema, g, from_deck=None, to_deck=None):
    """Seconds for the car to go from one landing to another.

    NOT A SECOND FORMULA. `npc/navigation.lift_ride_s` owns the physics -- a
    smoothstep whose peak is held at the Coriolis cap -- and this converts a
    pair of landings into the radial distance it takes. `_selftest` checks the
    answer against `transit.climb_leg`, which recomputes it through a code path
    that shares nothing with either.
    """
    # THE DEFAULTS PASS THE LANDING DICTS, not their deck numbers. Reading
    # `g["landings"][0]["deck"]` and handing it back to `_landing` looks like a
    # round trip and is not one the moment a `stack=` crosses a ring boundary
    # and two landings share a deck number -- it would raise on its own default.
    a = _landing(g, from_deck if from_deck is not None else g["landings"][0])
    b = _landing(g, to_deck if to_deck is not None else g["landings"][-1])
    return NAV.lift_ride_s(schema, abs(a["walk_r_m"] - b["walk_r_m"]))


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def _cast(o, d, verts, tris):
    return C.cast(o, d, verts, tris)


def unplace(g, pts):
    """World -> shaft-local. `place` is a rotation, so this is its transpose."""
    ux, uy, _uz = _basis(g["angle_deg"])
    ox, oy, oz = g["origin"]
    out = []
    for X, Y, Z in pts:
        dx, dy = X - ox, Y - oy
        out.append((dx * ux[0] + dy * ux[1],
                    dx * uy[0] + dy * uy[1], Z - oz))
    return out


def swept_volume(g):
    """The box the car body sweeps over its whole travel, in local coordinates.

    The car's structural box only -- NOT its sill, which overhangs on the door
    side by design and runs within `SILL_GAP_M` of the landing threshold.
    """
    car = g["car"]
    return {
        "hx": car["ext_w"] / 2.0,
        "hz": car["ext_d"] / 2.0,
        "y0": g["landings"][0]["y_m"] - car["slab_t"],
        "y1": g["landings"][-1]["y_m"] + car["clear_h"] + car["slab_t"],
    }


def swept_intruders(g, verts, eps=1e-6):
    """How many of `verts` (world space) stand in the car's path.

    THE QUESTION ASKED OF THE MESH RATHER THAN OF THE ARITHMETIC. `car_fit`
    compares two numbers that were computed from a third; this reads the
    geometry that actually got emitted. The two are not the same check, and the
    difference is not academic -- it is what caught the landing door assembly
    placed back to front, whose head indicator stood 50 mm into the car's path
    at every landing while every dimensional figure still said 150 mm clear.
    """
    sw = swept_volume(g)
    n = 0
    for lx, ly, lz in unplace(g, verts):
        if (abs(lx) < sw["hx"] - eps and abs(lz) < sw["hz"] - eps
                and sw["y0"] + eps < ly < sw["y1"] - eps):
            n += 1
    return n


def _selftest():
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (f"  {note}" if note else ""))

    import transit as T                                        # noqa: PLC0415

    schema, profile = it.load()
    sector, ring, ang, z = "blue", 0, 80.0, 7500.0
    decks = (0, 1, 2)
    g = shaft_geometry(schema, profile, sector, ring, decks, ang, z)

    print("\nTHE LIFT -- every dimension and where it came from\n")
    q = g["profile"]
    print(f"  corridor cast    floor_y {q['floor_y']:+.4f}  "
          f"half_w {q['half_w']:.4f}  ceil_y {q['ceil_y']:.3f}")
    print(f"  car clear        {g['car']['clear_w']:.4f} w x "
          f"{g['car']['clear_d']:.4f} d x {g['car']['clear_h']:.4f} h   "
          f"(2*half_w, square in plan, ceil_y-floor_y)")
    print(f"  car external     {g['car']['ext_w']:.4f} x "
          f"{g['car']['ext_d']:.4f} x {g['car']['ext_h']:.4f}   "
          f"(+2*{g['car']['wall_t']} panel, +2*{g['car']['slab_t']} slab)")
    print(f"  shaft bore       {2*g['shaft']['bore_hw']:.4f} x "
          f"{2*g['shaft']['bore_hd']:.4f}   "
          f"(car + 2*{g['relief_m']} running clearance)")
    print(f"  storeys          {[round(s, 4) for s in g['storeys_m']]} m, "
          f"rise {g['rise_m']:.4f} m over {len(g['landings'])} landings")
    print(f"  radii            {g['landings'][0]['floor_r_m']:.2f} m "
          f"({g['landings'][0]['floor_g']:.3f} g) -> "
          f"{g['landings'][-1]['floor_r_m']:.2f} m "
          f"({g['landings'][-1]['floor_g']:.3f} g)")
    _over = (g["shaft"]["y_top"] - g["landings"][-1]["y_m"]
             - g["car"]["clear_h"] - g["car"]["slab_t"])
    print(f"  shaft depth      {g['shaft']['depth_m']:.4f} m "
          f"(pit {-g['shaft']['y_pit']:.3f}, overhead {_over:.3f})")
    print(f"  ride             {g['ride_s']:.3f} s at a "
          f"{g['v_cap_m_s']:.4f} m/s Coriolis cap\n")

    # --- the rise is MEASURED, not restated ------------------------------
    check("the storey height comes off the deck stack, not off DECK_PITCH_M",
          all(abs(s - it.DECK_PITCH_M) < 1e-9 for s in g["storeys_m"])
          and abs(g["rise_m"] - (len(g["landings"]) - 1) * it.DECK_PITCH_M)
          < 1e-9,
          f"{g['storeys_m']} m")
    # ... and the control: a shaft over non-adjacent decks must be taller.
    g_skip = shaft_geometry(schema, profile, sector, ring, (0, 3), ang, z)
    check("and a shaft over non-adjacent decks is taller for it",
          abs(g_skip["rise_m"] - 3.0 * it.DECK_PITCH_M) < 1e-9
          and g_skip["shaft"]["depth_m"] > g["shaft"]["depth_m"],
          f"decks 0-3 rise {g_skip['rise_m']:.2f} m, depth "
          f"{g_skip['shaft']['depth_m']:.3f} vs {g['shaft']['depth_m']:.3f}")

    # --- 1. the shaft is closed ------------------------------------------
    v, t, m = lift_shaft(schema, profile, sector, ring, decks, ang, z, g=g)
    openx, nonman = it.boundary_edges(v, t)
    print(f"  shaft mesh       {len(t):,} triangles, {len(v):,} vertices, "
          f"{len(m['groups'])} tagged spans")
    check("the shaft has no open edges", len(openx) == 0,
          f"{len(openx)} open edges")

    # NEGATIVE CONTROL, and it has to fire: `boundary_edges` must be live on
    # THIS mesh. Punch one triangle out and it has to report the hole. A
    # closure gate that cannot see a hole it was handed is a closure gate that
    # is passing for the wrong reason -- the vertex-key rounding could be
    # welding everything to nothing and the count would still read zero.
    punched = t[:1000] + t[1001:]
    o2, _n2 = it.boundary_edges(v, punched)
    check("and with one triangle removed the measurement fires",
          len(o2) == 3, f"{len(o2)} open edges after removing one triangle")

    # NON-MANIFOLD IS THE OTHER HALF OF THE PAIR AND NOTHING IN THIS PROJECT
    # GATES IT. Session 3x rebuilt `portal_frame` because five prisms sharing
    # coincident faces gave 828 non-manifold edges a deck, fixed exactly the
    # three pieces it was looking at, and the audit was never re-run over the
    # rest of the kit. Measured here, per piece, on pieces this module did not
    # write (see docs/lift-4g.md):
    #
    #     ring_frame 64,  wall_assembly 5,  deck_panel 2,  door_leaf(shut) 4
    #     portal_frame 0, door_frame 0, bulkhead 0, pilaster 0, deck_grid 0
    #
    # So the shaft's own count is asserted against the kit's contribution
    # rather than against zero: everything THIS FILE builds is manifold, and
    # the residue is `door_leaf`'s two shut leaves meeting on an exactly
    # coincident face -- four edges a door, at 0.0 open fraction only.
    nl_v, nl_t, _nl = lift_shaft(schema, profile, sector, ring, decks, ang, z,
                                 g=g, door_leaves=False)
    _no, nl_nm = it.boundary_edges(nl_v, nl_t)
    leaf_v, leaf_t = K.door_leaf(open_fraction=0.0)
    _lo, leaf_nm = it.boundary_edges(leaf_v, leaf_t)
    check("everything this module builds is manifold",
          len(nl_nm) == 0,
          f"{len(nl_nm)} non-manifold edges with the kit's leaves omitted")
    check("and the residue with leaves is exactly the kit's own shut-leaf "
          "defect, four edges a door",
          len(nonman) == len(g["landings"]) * len(leaf_nm)
          and len(leaf_nm) == 4,
          f"shaft {len(nonman)}, {len(g['landings'])} doors x "
          f"{len(leaf_nm)} from interior_kit.door_leaf(0.0)")
    # ... and the control that identifies the cause: crack the leaves open and
    # the coincident face is gone. A finding without a control is a guess.
    _ao, ajar_nm = it.boundary_edges(*K.door_leaf(open_fraction=0.25))
    check("and it is the SHUT leaves that do it -- ajar, the defect is gone",
          len(ajar_nm) == 0 and len(leaf_nm) > 0,
          f"door_leaf(0.0) {len(leaf_nm)}, door_leaf(0.25) {len(ajar_nm)}")

    # The car, closed on the same test.
    cv, ct, _cm = lift_car(schema, profile, g=g)
    co, cn = it.boundary_edges(cv, ct)
    print(f"  car mesh         {len(ct):,} triangles, {len(cv):,} vertices")
    check("the car has no open edges", len(co) == 0, f"{len(co)} open")
    check("and its non-manifold count is the one shut door in it",
          len(cn) == len(leaf_nm), f"{len(cn)} against {len(leaf_nm)}")

    # --- 2. a floor under a body in the car, at every deck ----------------
    # CAST OUTWARD, because outward is down on a spun ring, exactly as
    # `collision.axial_shell`'s own test does.
    _ux, uy, _uz = _basis(ang)
    down = tuple(-c for c in uy)
    misses, drops = [], []
    for lg in g["landings"]:
        kv, kt, _km = lift_collision(schema, profile, g=g, at_deck=lg["deck"])
        for dx in (-0.8, 0.0, 0.8):
            for dz in (-0.8, 0.0, 0.8):
                o = place(g, [(dx, lg["y_m"] + 1.0, dz)])[0]
                h = _cast(o, down, kv, kt)
                if h is None:
                    misses.append((lg["deck"], dx, dz))
                else:
                    drops.append(h)
    check("a body standing in the car has a floor under it at every deck",
          not misses and drops,
          f"{len(misses)} of {len(g['landings']) * 9} probes found nothing"
          + (f" -- {misses[:3]}" if misses else ""))
    check("and it is flat to under the step tolerance",
          bool(drops) and max(drops) - min(drops) < C.STEP_TOLERANCE_M,
          f"{(max(drops) - min(drops)) * 1000:.2f} mm across the car floor"
          if drops else "no probes landed")

    # NEGATIVE CONTROL: with the car omitted the same probes must fall through
    # to the pit -- if they still stop at 1.0 m the "floor" was something else.
    nv, nt, _nm = lift_collision(schema, profile, g=g, at_deck=1, car=False)
    o = place(g, [(0.0, g["landings"][1]["y_m"] + 1.0, 0.0)])[0]
    h_nocar = _cast(o, down, nv, nt)
    check("and with the car taken out the body falls to the pit",
          h_nocar is not None
          and h_nocar > g["landings"][1]["y_m"] + 1.0 - g["shaft"]["y_pit"] - 0.01,
          f"stopped after {h_nocar} m, pit is "
          f"{g['landings'][1]['y_m'] + 1.0 - g['shaft']['y_pit']:.3f} m down")

    # THE THRESHOLD. A step where a player crosses from the deck into the car
    # is precisely what `collision.py` exists to prevent, and the car's floor
    # is a PLANE while the deck's is a CYLINDER, so they can only agree at one
    # point. Measured over the car's own half width.
    R = g["landings"][0]["walk_r_m"]
    sag = R - math.sqrt(max(0.0, R * R - (g["car"]["clear_w"] / 2.0) ** 2))
    check("the car's flat floor meets the deck's curved one inside tolerance",
          sag < C.STEP_TOLERANCE_M,
          f"{sag * 1000:.2f} mm over the car's {g['car']['clear_w']:.2f} m "
          f"width at r = {R:.1f} m, against "
          f"{C.STEP_TOLERANCE_M * 1000:.0f} mm")
    # And the car floor is where the CORRIDOR's floor is, so a player crossing
    # the threshold takes no step at all. `collision.corridor_shell` puts its
    # floor at `deck_radius - profile.floor_y`; this asserts the car's emitted
    # floor lands on the same radius, measured off the mesh by the same cast.
    kv0, kt0, _km0 = lift_collision(schema, profile, g=g, at_deck=0)
    o0 = place(g, [(0.0, g["landings"][0]["y_m"] + 1.0, 0.0)])[0]
    h0 = _cast(o0, down, kv0, kt0)
    r_car = math.hypot(o0[0], o0[1]) + (h0 or 0.0)
    r_corr = g["landings"][0]["floor_r_m"] - q["floor_y"]
    check("the car floor lands on the corridor's own walking radius",
          h0 is not None and abs(r_car - r_corr) < 1e-6,
          f"car floor r={r_car:.6f} m, corridor floor r={r_corr:.6f} m "
          f"(deck {g['landings'][0]['floor_r_m']} - floor_y {q['floor_y']:.3f})")

    # THE THRESHOLD WALK, and it is the gate this whole module exists to pass.
    # The other checks say the car has a floor and the landing has a hole; this
    # one says a body can get from one to the other. It is
    # `collision.floor_holes` applied to the one route a lift has: from the
    # lobby, across the fixed landing sill, over the running gap, onto the car
    # floor. Sampled at 0.35 m, the capsule diameter `floor_holes` itself uses,
    # because a slot narrower than a body is not a hole a body falls through --
    # and the widest unsupported run is REPORTED, not just compared, since a
    # pass that does not say how close it came says nothing.
    ls = g["landing_side"]
    walk_z0 = ls * (g["shaft"]["sub_hd_door"] + g["shaft"]["wall_t"] + 0.1)
    walk_z1 = -ls * (g["car"]["clear_d"] / 2.0 - 0.1)

    def widest_hole(verts_, tris_, y_at):
        """The longest run along the threshold with nothing underfoot."""
        n_, run, worst = 400, 0.0, 0.0
        step = abs(walk_z1 - walk_z0) / (n_ - 1)
        for i in range(n_):
            zz = walk_z0 + (walk_z1 - walk_z0) * i / (n_ - 1)
            o = place(g, [(0.0, y_at + 1.0, zz)])[0]
            h = _cast(o, down, verts_, tris_)
            if h is None or abs(h - 1.0) > 0.02:
                run += step
                worst = max(worst, run)
            else:
                run = 0.0
        return worst

    worst_all = 0.0
    for lg in g["landings"]:
        kvw, ktw, _kmw = lift_collision(schema, profile, g=g,
                                        at_deck=lg["deck"])
        worst_all = max(worst_all, widest_hole(kvw, ktw, lg["y_m"]))
    check("a body walks from the landing into the car without leaving the "
          "floor",
          worst_all < 0.35,
          f"widest unsupported run {worst_all * 1000:.0f} mm across the "
          f"threshold at every landing, against a 350 mm capsule; the car and "
          f"landing sills run {g['sill_gap_m'] * 1000:.0f} mm apart by design")
    # NEGATIVE CONTROL: with the car at a DIFFERENT deck the same walk has to
    # fall through, or the floor being found was never the car's.
    kvn, ktn, _kmn = lift_collision(schema, profile, g=g,
                                    at_deck=g["landings"][-1]["deck"])
    worst_n = widest_hole(kvn, ktn, g["landings"][0]["y_m"])
    check("and with the car at another deck that walk falls into the shaft",
          worst_n > 0.35,
          f"{worst_n * 1000:.0f} mm unsupported with the car "
          f"{g['rise_m']:.1f} m up")

    # --- 3. the landing is a hole a body can cross ------------------------
    ls = g["landing_side"]
    out = (0.0, 0.0, float(ls))
    kv, kt, _km = lift_collision(schema, profile, g=g, at_deck=0)
    sv, st_, _sm = lift_collision(schema, profile, g=g, at_deck=0,
                                  landings=False)
    crossed, sealed = [], []
    for lg in g["landings"]:
        o = place(g, [(0.0, lg["y_m"] + 1.0, 0.0)])[0]
        crossed.append(_cast(o, out, kv, kt))
        sealed.append(_cast(o, out, sv, st_))
    check("every landing aperture is a hole a body can cross",
          all(h is None for h in crossed),
          f"{sum(h is None for h in crossed)}/{len(crossed)} rays crossed; "
          f"hits {crossed}")
    check("and with the landings suppressed the same rays are stopped",
          all(h is not None and h < g["shaft"]["bore_hd"] + 0.01
              for h in sealed),
          f"sealed shaft let rays through: {sealed}")
    # The same control on the RENDER, because the door in the mesh and the hole
    # in the shell are two decisions about one doorway and this project has
    # been bitten by exactly that pair drifting apart.
    bv, bt, _bm = lift_shaft(schema, profile, sector, ring, decks, ang, z, g=g,
                             landings=False, door_leaves=False)
    ov_, ot_, _om = lift_shaft(schema, profile, sector, ring, decks, ang, z,
                               g=g, door_leaves=False)
    o = place(g, [(0.0, g["landings"][0]["y_m"] + 1.0, 0.0)])[0]
    r_open = _cast(o, out, ov_, ot_)
    r_blind = _cast(o, out, bv, bt)
    check("the rendered aperture is open where the shell's is",
          r_open is None, f"{r_open} (None = crossed)")
    check("and a blind storey in the render stops it",
          r_blind is not None, f"the blind wall let a ray through: {r_blind}")

    # --- 4. the car fits the shaft ---------------------------------------
    fit = car_fit(g)
    print(f"  clearances       tangential {fit['tangential_m'] * 1000:.0f} mm, "
          f"axial {fit['axial_m'] * 1000:.0f} mm, pit "
          f"{fit['pit_m'] * 1000:.0f} mm, overhead "
          f"{fit['overhead_m'] * 1000:.0f} mm, sill "
          f"{fit['sill_m'] * 1000:.0f} mm")
    check("the car fits the shaft on every face",
          all(fit[k] > 0.0 for k in ("tangential_m", "axial_m", "pit_m",
                                     "overhead_m")),
          str({k: round(x, 4) for k, x in fit.items()}))
    check("and its roof clears the landing above, so it can serve both",
          fit["storey_headroom_m"] > 0.0,
          f"{fit['storey_headroom_m'] * 1000:.0f} mm between the car roof and "
          f"the next floor, car {g['car']['ext_h']:.3f} m in a "
          f"{min(g['storeys_m']):.3f} m storey")

    # NEGATIVE CONTROL: shrink the shaft and the fit gate must fire. Not a
    # mutated dict -- the bore is rebuilt from a smaller running clearance, so
    # the control exercises the same arithmetic the real call does.
    g_tight = shaft_geometry(schema, profile, sector, ring, decks, ang, z,
                             relief_m=-0.20)
    tight = car_fit(g_tight)
    check("and a shaft built 200 mm tighter than its car FAILS that check",
          not all(tight[k] > 0.0 for k in ("tangential_m", "axial_m",
                                           "pit_m", "overhead_m")),
          f"tangential {tight['tangential_m']:+.3f}, axial "
          f"{tight['axial_m']:+.3f}, pit {tight['pit_m']:+.3f}")

    # THE STRONGER FORM OF THE SAME QUESTION, asked of the EMITTED GEOMETRY
    # rather than of the arithmetic: does anything the shaft is made of stand
    # inside the volume the car SWEEPS? A number that agrees with itself is not
    # evidence; a vertex in the car's path is. This is the check that found the
    # landing door assembly placed back to front -- its head indicator and
    # control panel stand 50 mm proud of the frame's front face, and turned the
    # wrong way that is 12 vertices in the car's path at every landing.
    sw = swept_volume(g)
    intruders = swept_intruders(g, v)
    print(f"  swept check      {len(v):,} shaft vertices against the car's "
          f"{2 * sw['hx']:.3f} x {2 * sw['hz']:.3f} m path over "
          f"{sw['y1'] - sw['y0']:.3f} m of travel")
    check("nothing the shaft is made of stands in the car's path",
          intruders == 0,
          f"{intruders} of {len(v):,} shaft vertices inside the swept volume")
    # NEGATIVE CONTROL: the same test on a shaft built 200 mm tighter than its
    # car has to find the intrusion, or the test is passing because the loop
    # never fires rather than because the geometry is clear.
    vt_, _tt, _mt = lift_shaft(schema, profile, sector, ring, decks, ang, z,
                               g=g_tight)
    intr_t = swept_intruders(g_tight, vt_)
    check("and on the 200 mm-tight shaft the same test finds the intrusion",
          intr_t > 0,
          f"{intr_t} of {len(vt_):,} vertices in the car's path")

    # --- 5. the ride time -------------------------------------------------
    # FROM THE MESH, not from the dict: the rise is read off the two extreme
    # landings' collision floors, so a shaft built to the wrong depth would
    # produce the wrong ride time and this would catch it.
    bot = lift_collision(schema, profile, g=g, at_deck=g["landings"][0]["deck"])
    top = lift_collision(schema, profile, g=g, at_deck=g["landings"][-1]["deck"])
    r_bot = _floor_radius(bot[0], bot[1], g, down)
    r_top = _floor_radius(top[0], top[1], g, down)
    rise_measured = r_bot - r_top
    t_nav = NAV.lift_ride_s(schema, rise_measured)
    t_mod = ride_s(schema, g)
    t_transit = T.climb_leg(schema, rise_measured, "lift")["seconds"]
    print(f"  ride time        mesh rise {rise_measured:.4f} m -> "
          f"{t_nav:.4f} s (navigation), {t_transit:.4f} s (transit), "
          f"{t_mod:.4f} s (lift.ride_s)")
    check("the rise measured off the car's own floors is the rise built",
          abs(rise_measured - g["rise_m"]) < 1e-6,
          f"{rise_measured:.6f} m measured against {g['rise_m']:.6f} built")
    check("the ride time agrees with navigation.lift_ride_s",
          abs(t_mod - t_nav) < 1e-9, f"{t_mod:.6f} vs {t_nav:.6f} s")
    check("and with transit.climb_leg, which recomputes it independently",
          abs(t_mod - t_transit) < 1e-6,
          f"{t_mod:.6f} vs {t_transit:.6f} s")
    # NEGATIVE CONTROL: a taller shaft must take longer, or the ride time is
    # not a function of the thing it claims to be.
    t_skip = ride_s(schema, g_skip)
    check("and a three-storey rise takes longer than a two-storey one",
          t_skip > t_mod * 1.4,
          f"{t_skip:.3f} s over {g_skip['rise_m']:.1f} m against "
          f"{t_mod:.3f} s over {g['rise_m']:.1f} m")

    # --- the landing side, both hands -------------------------------------
    gL = shaft_geometry(schema, profile, sector, ring, decks, ang, z,
                        landing_side=-1)
    lv, lt, _lm = lift_shaft(schema, profile, sector, ring, decks, ang, z,
                             g=gL, door_leaves=False)
    lo_, hi_ = it.boundary_edges(lv, lt)
    kvL, ktL, _ = lift_collision(schema, profile, g=gL, at_deck=0)
    oL = place(gL, [(0.0, gL["landings"][0]["y_m"] + 1.0, 0.0)])[0]
    hL = _cast(oL, (0.0, 0.0, -1.0), kvL, ktL)
    check("a shaft with its doors on the other hand is closed too",
          len(lo_) == 0 and len(hi_) == 0,
          f"{len(lo_)} open, {len(hi_)} non-manifold")
    check("and its landings open the other way",
          hL is None, f"ray through the -1 landing: {hL} (None = crossed)")
    check("and nothing on that hand stands in the car's path either",
          swept_intruders(gL, lv) == 0,
          f"{swept_intruders(gL, lv)} vertices in the car's path")

    # --- the drum, whose deck stack is numbered the other way round -------
    # `decks_in_ring` returns the drum's sub-floor stack growing OUTWARD, so
    # deck 0 is the highest there and lowest everywhere else. A builder that
    # sorted by index would build one of the two upside down.
    drum = it.drum_sector(schema, profile)
    gd = shaft_geometry(schema, profile, drum, 0, (0, 1), 30.0, 5200.0)
    check("the drum's stack is numbered the other way and still builds up",
          gd["landings"][0]["deck"] == 1 and gd["landings"][-1]["deck"] == 0
          and gd["landings"][0]["floor_r_m"] > gd["landings"][-1]["floor_r_m"],
          f"bottom deck {gd['landings'][0]['deck']} at "
          f"{gd['landings'][0]['floor_r_m']:.1f} m, top deck "
          f"{gd['landings'][-1]['deck']} at "
          f"{gd['landings'][-1]['floor_r_m']:.1f} m")
    dv, dt, _dm = lift_shaft(schema, profile, drum, 0, (0, 1), 30.0, 5200.0,
                             g=gd, door_leaves=False)
    do, dn = it.boundary_edges(dv, dt)
    check("and a drum shaft is closed as well",
          len(do) == 0 and len(dn) == 0, f"{len(do)} open, {len(dn)} nonman")
    d_hits = [_cast(place(gd, [(0.0, lg["y_m"] + 1.0, 0.0)])[0],
                    tuple(-c for c in _basis(30.0)[1]),
                    *lift_collision(schema, profile, g=gd,
                                    at_deck=lg["deck"])[:2])
              for lg in gd["landings"]]
    check("and the drum's car has a floor at both its landings",
          all(h is not None and abs(h - 1.0) < 0.02 for h in d_hits),
          f"drops {[None if h is None else round(h, 4) for h in d_hits]} m "
          f"from a 1.0 m probe")

    # --- winding, which decides floor from hole ---------------------------
    kv2, kt2, km2 = lift_collision(schema, profile, g=g, at_deck=0)
    span = dict((n, (a, b)) for n, a, b in km2["groups"])["lift_car"]
    bad = 0
    for tri in kt2[span[0]:span[1]]:
        a, b, c = (kv2[j] for j in tri)
        if not all(abs(math.hypot(P[0], P[1])
                       - g["landings"][0]["walk_r_m"]) < 1e-6
                   for P in (a, b, c)):
            continue
        u = [b[k] - a[k] for k in range(3)]
        w = [c[k] - a[k] for k in range(3)]
        nrm = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
               u[0] * w[1] - u[1] * w[0])
        mid = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
        rr = math.hypot(*mid) or 1.0
        if nrm[0] * -mid[0] / rr + nrm[1] * -mid[1] / rr <= 0:
            bad += 1
    check("every triangle of the car floor faces the player, not the void",
          bad == 0, f"{bad} wound outward -- those are holes")

    # ====================================================================
    # THE CASE THE GATES ABOVE DID NOT BUILD
    # ====================================================================
    # Every check above ran on 2, 3 and 4 landings. `interior.decks_in_ring`
    # says the station's rings carry 7 to 28 decks and only blue ring 0 is as
    # short as ten -- so the shaft as gated was the case that does not ship.
    # That is this repository's most-repeated lesson (`interior_kit`'s tag gate
    # ran on a corridor with no doors; `_tag_coverage`'s `doors` defaulted to
    # nothing) arriving through a different door, and the sweep below is the
    # cure: build the TALLEST STACK THE STATION ACTUALLY HAS, at every height
    # up to it.
    tall_sec, tall_ring, tall_z = "grey", 1, 3618.0
    tall = it.decks_in_ring(schema, profile, tall_sec, tall_ring, z_m=tall_z)
    print(f"\n  tallest stack    {tall_sec} ring {tall_ring} carries "
          f"{len(tall)} decks over "
          f"{tall[0]['floor_r_m'] - tall[-1]['floor_r_m']:.1f} m of radius")
    sweep_bad, sweep_dup, sweep_drop, biggest = [], 0, 0, (0, 0)
    for n in range(2, len(tall) + 1):
        sv, st_, sm = lift_shaft(schema, profile, tall_sec, tall_ring,
                                 tuple(range(n)), 40.0, tall_z)
        so, _sn = it.boundary_edges(sv, st_)
        if so:
            sweep_bad.append((n, len(so)))
        sweep_drop += sm["welded_dropped_tris"]
        sg = sm["geometry"]
        sweep_dup += len(near_duplicates(unplace(sg, sv)))
        biggest = max(biggest, (len(st_), n))
    check(f"the shaft is closed at every landing count up to "
          f"{len(tall)}, the tallest stack on the station",
          not sweep_bad,
          f"open edges at {sweep_bad}" if sweep_bad else
          f"2..{len(tall)} landings, 0 open edges throughout, biggest "
          f"{biggest[0]:,} tri at {biggest[1]} landings")
    check("and no two of its vertices stand 42 nm apart pretending to be one",
          sweep_dup == 0, f"{sweep_dup} near-duplicate vertex pairs")
    check("and the weld that closes it drops no triangle, so it merges "
          "nothing real",
          sweep_drop == 0, f"{sweep_drop} triangles dropped over the sweep")

    # NEGATIVE CONTROL, AND IT IS THE ONE THAT MATTERS. Unwelded, the same
    # shaft has to open up -- and it has to open up AT ONE POSITION AND NOT
    # ANOTHER, because that is the diagnosis. `boundary_edges` keys on
    # coordinates rounded to 4 decimals, so a 42 nm pair reads as a hole only
    # when it straddles that 0.1 mm grid, and where it falls depends on where
    # in the station the shaft was placed. A control that fired everywhere
    # would mean the diagnosis was wrong.
    #
    # Two positions, the same code, the same landing counts:
    #   blue ring 1 at 140 deg, z 6880  -- the reported repro
    #   grey ring 1 at  40 deg, z 3618  -- the tallest stack, swept above
    raw = {}
    for lbl, (rs, rr, ra, rz) in (("blue r1 @140", ("blue", 1, 140.0, 6880.0)),
                                  ("grey r1 @40", ("grey", 1, 40.0, 3618.0))):
        fired, dups = [], 0
        for n in range(2, 13):
            rg = shaft_geometry(schema, profile, rs, rr, tuple(range(n)),
                                ra, rz)
            uv, ut, _um = lift_shaft(schema, profile, rs, rr, tuple(range(n)),
                                     ra, rz, g=rg, weld_mesh=False)
            uo, _un = it.boundary_edges(uv, ut)
            dups += len(near_duplicates(unplace(rg, uv)))
            if uo:
                fired.append((n, len(uo)))
        raw[lbl] = (fired, dups)
    a_fired, a_dup = raw["blue r1 @140"]
    b_fired, b_dup = raw["grey r1 @40"]
    print(f"  unwelded         blue r1 @140: open at {a_fired[:3]}"
          f"{'...' if len(a_fired) > 3 else ''}, {a_dup} near-dup pairs")
    print(f"                   grey r1 @40 : open at {b_fired}, "
          f"{b_dup} near-dup pairs")
    check("and WITHOUT the weld the reported case opens up, from 6 landings on",
          [n for n, _ in a_fired] == list(range(6, 13))
          and {c for _, c in a_fired} == {6},
          f"open edges at {a_fired}")
    check("and the SAME unwelded code at another position does not, which is "
          "the diagnosis: a 42 nm crack is a hole only when it straddles "
          "boundary_edges' 0.1 mm grid",
          not b_fired and a_dup == b_dup and a_dup > 0,
          f"{len(a_fired)} heights open at one position and {len(b_fired)} at "
          f"the other, on the identical {a_dup} near-duplicate pairs")
    check("and welding removes the pairs rather than hiding them",
          sweep_dup == 0 and a_dup > 0,
          f"{a_dup} pairs unwelded, {sweep_dup} welded")

    # ====================================================================
    # `stack=` -- ONE SHAFT ACROSS TWO RINGS, WITH A STOREY 1.7x THE REST
    # ====================================================================
    # The override `spoke_way.py` uses. A ring is a nested shell and
    # `decks_in_ring` knows only its own, so a column serving both is handed
    # the two stacks sorted by radius. The question this section answers is
    # whether anything here assumed a uniform storey.
    z2 = 6880.0
    two = sorted(it.decks_in_ring(schema, profile, "blue", 0, z_m=z2)
                 + it.decks_in_ring(schema, profile, "blue", 1, z_m=z2),
                 key=lambda d: -d["floor_r_m"])
    g2 = shaft_geometry(schema, profile, "blue", 0, tuple(range(len(two))),
                        140.0, z2, stack=two)
    st = g2["storeys_m"]
    print(f"\n  two rings        {len(g2['landings'])} landings over "
          f"{g2['rise_m']:.2f} m; storeys {min(st):.2f}-{max(st):.2f} m, "
          f"the boundary one {max(st) / min(st):.2f}x the rest")
    check("a stack= across two rings has a storey that is not the pitch",
          max(st) > min(st) * 1.5,
          f"{sorted({round(s, 3) for s in st})} m")

    # THE DEFECT THIS CASE FOUND, and it is the reason to build it. `deck_index`
    # restarts at 0 in every ring, so eighteen landings are numbered
    # [0..5, 0..11] and `at_deck` names two of them at once.
    check("and its deck numbers are NOT unique, which the geometry says out "
          "loud",
          g2["deck_keys_unique"] is False
          and len({lg["deck"] for lg in g2["landings"]})
          < len(g2["landings"]),
          f"{len(g2['landings'])} landings, "
          f"{len({lg['deck'] for lg in g2['landings']})} distinct deck numbers")
    # AND AN INT NOW ADDRESSES THE LANDING, NOT THE DECK, EXACTLY HERE.
    # `_landing`'s two readings agree wherever deck numbers are unique -- which
    # is every shaft this module built before `stack=` existed -- and where
    # they are not, the deck number is not a naming of the landings at all and
    # the index is the only one left. Asserted as a BIJECTION: eighteen ints
    # reach eighteen distinct landings. Under the old rule six of them reached
    # a landing that was already spoken for.
    reached = [_landing(g2, i)["index"] for i in range(len(g2["landings"]))]
    check("an int addresses every one of the 18 landings, one for one",
          reached == list(range(len(g2["landings"]))),
          f"{len(set(reached))} distinct landings reached by "
          f"{len(g2['landings'])} ints")
    by_deck = [next(lg["index"] for lg in g2["landings"] if lg["deck"] == i)
               for i in range(len(g2["landings"])) if
               any(lg["deck"] == i for lg in g2["landings"])]
    check("and the OLD first-match-by-deck rule would have reached only 12 of "
          "them, which is the defect this case was built to find",
          len(set(by_deck)) < len(g2["landings"]),
          f"first-match-by-deck reaches {len(set(by_deck))} of "
          f"{len(g2['landings'])} landings")
    try:
        _landing(g2, len(g2["landings"]) + 5)
        oor = None
    except ValueError as e:                                     # noqa: BLE001
        oor = str(e)
    check("and an address off the end of the shaft still raises",
          oor is not None and "not on this shaft" in oor,
          (oor or "it returned a landing")[:88])
    # THE CONTROL THAT THE FALLBACK CHANGED NOTHING FOR ANYONE ELSE: on a
    # single-ring shaft the two readings have to give the same answer for
    # every landing, or every caller that predates `stack=` has just moved.
    same = all(_landing(g, d)["index"] == _landing(g, g["landings"][d])["index"]
               for d in range(len(g["landings"])))
    check("and on a single-ring shaft the deck reading and the index reading "
          "are the same answer, so no existing caller moved",
          same and g["deck_keys_unique"] is True,
          f"deck_keys_unique={g['deck_keys_unique']}, all "
          f"{len(g['landings'])} agree")

    # Now the invariants, on the two-ring shaft, with the boundary storey in it.
    v2, t2, _m2 = lift_shaft(schema, profile, "blue", 0,
                             tuple(range(len(two))), 140.0, z2, g=g2)
    o2, n2 = it.boundary_edges(v2, t2)
    check("the two-ring shaft is closed",
          not o2 and len(n2) == 4 * len(g2["landings"]),
          f"{len(o2)} open, {len(n2)} non-manifold against "
          f"{4 * len(g2['landings'])} shut leaves")
    check("and nothing stands in its car's 63 m path",
          swept_intruders(g2, v2) == 0,
          f"{swept_intruders(g2, v2)} vertices")
    f2 = car_fit(g2)
    check("car_fit still reduces over the SMALLEST storey, so the 6 m gap "
          "cannot flatter it",
          abs(f2["storey_headroom_m"] - (min(st) - g2["car"]["ext_h"])) < 1e-12
          and f2["storey_headroom_m"] > 0.0,
          f"headroom {f2['storey_headroom_m'] * 1000:.0f} mm off the "
          f"{min(st):.2f} m storey, not the {max(st):.2f} m one")
    d2, miss2 = [], 0
    down2 = tuple(-c for c in _basis(140.0)[1])
    for lg in g2["landings"]:
        kv2_, kt2_, _ = lift_collision(schema, profile, g=g2, at_deck=lg)
        h = _cast(place(g2, [(0.0, lg["y_m"] + 1.0, 0.0)])[0], down2,
                  kv2_, kt2_)
        if h is None or abs(h - 1.0) > 0.02:
            miss2 += 1
        else:
            d2.append(h)
    check("and there is a floor under the car at all "
          f"{len(g2['landings'])} of them, the boundary landing included",
          miss2 == 0,
          f"{miss2} landings with nothing underfoot"
          if miss2 else f"{len(d2)} probes, all at 1.000 m")
    # The ride is linear in rise, so a 63.6 m column is one continuous move and
    # the boundary storey costs exactly its own metres -- no more.
    r2 = ride_s(schema, g2)
    check("the ride over two rings is the rise, whatever the storeys do",
          abs(r2 - NAV.lift_ride_s(schema, g2["rise_m"])) < 1e-9
          and abs(r2 - sum(NAV.lift_ride_s(schema, s) for s in st)) < 1e-9,
          f"{r2:.3f} s over {g2['rise_m']:.2f} m = the sum of "
          f"{len(st)} per-storey rides to 1e-9")

    # --- what it costs ----------------------------------------------------
    kvT = sum(len(lift_collision(schema, profile, g=g, at_deck=d["deck"])[1])
              for d in g["landings"][:1])
    print(f"\n  cost             render shaft {len(t):,} tri + car "
          f"{len(ct):,} tri = {len(t) + len(ct):,};  collision {kvT:,} tri "
          f"({kvT / max(1, len(t) + len(ct)) * 100:.1f}% of render)")
    check("the collision shell is far cheaper than the render mesh",
          kvT * 8 < len(t) + len(ct),
          f"{kvT:,} shell vs {len(t) + len(ct):,} render")

    print(f"\n{ok[1]}/{ok[0]} passed")
    return 0 if ok[1] == ok[0] else 1


def _floor_radius(verts, tris, g, down):
    """The radius of the first surface under a body standing at the car's
    centre. The measurement the ride time is derived from.

    Probes from a metre above each landing in turn and takes the one where a
    surface is exactly a metre down: with the car parked at one landing, the
    others have nothing under them but the pit, so the hit distance identifies
    which landing the car is at without being told.
    """
    at = None
    for lg in g["landings"]:
        o = place(g, [(0.0, lg["y_m"] + 1.0, 0.0)])[0]
        h = C.cast(o, down, verts, tris)
        if h is not None and abs(h - 1.0) < 0.02:
            at = math.hypot(o[0], o[1]) + h
            break
    if at is None:
        raise AssertionError("no car floor found under any landing")
    return at


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="blue")
    ap.add_argument("--ring", type=int, default=0)
    ap.add_argument("--decks", default="0,1,2")
    ap.add_argument("--angle", type=float, default=80.0)
    ap.add_argument("--z", type=float, default=7500.0)
    ap.add_argument("--side", type=int, default=1)
    ap.add_argument("--obj", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()

    schema, profile = it.load()
    decks = tuple(int(x) for x in a.decks.split(","))
    g = shaft_geometry(schema, profile, a.sector, a.ring, decks, a.angle, a.z,
                       landing_side=a.side)
    v, t, m = lift_shaft(schema, profile, a.sector, a.ring, decks, a.angle,
                         a.z, g=g)
    cv, ct, cm = lift_car(schema, profile, g=g)
    _kv, kt, _km = lift_collision(schema, profile, g=g)
    print(f"{a.sector} ring {a.ring} decks {decks} at {a.angle} deg, "
          f"z={a.z}: rise {m['rise_m']:.2f} m over "
          f"{len(g['landings'])} landings, shaft {m['depth_m']:.2f} m deep")
    print(f"  bore {m['bore_m'][0]:.3f} x {m['bore_m'][1]:.3f} m, car "
          f"{cm['clear_w_m']:.3f} x {cm['clear_d_m']:.3f} x "
          f"{cm['clear_h_m']:.3f} m clear")
    print(f"  {len(t):,} shaft tri + {len(ct):,} car tri, "
          f"{len(kt):,} collision tri, ride {m['ride_s']:.2f} s")
    if a.obj:
        C.write_obj(a.obj, v + cv,
                    list(t) + [(x + len(v), y + len(v), z2 + len(v))
                               for x, y, z2 in ct])
        print(f"  wrote {a.obj}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
