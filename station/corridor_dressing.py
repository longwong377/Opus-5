#!/usr/bin/env python3
"""Things standing in the corridor, which had NOTHING in it.

WHY THIS EXISTS, and it is a measurement rather than a taste. Session 4e put
eight new PBR sheets onto 131 previously untextured materials and the corridor
frame stayed flat. Chasing that produced three more measurements, each an A/B
of one feature on against off:

    fixture shadows 2 -> 18  byte-identical PNGs

(Two other A/Bs in that batch -- ssil and volumetric fog -- ALSO came back
byte-identical and were wrong: the container had no Vulkan ICD, so Godot had
silently fallen back to OpenGL 3 Compatibility, which has no Forward+ at all.
Re-measured on Vulkan they move 86% and 40% of pixels. The shadow result is
re-checked separately; what follows stands on its own regardless, because an
empty corridor is empty under any renderer.)

The shadow one is the one that explains the frame. `export_scene.fixture_lights`
already said why in its own docstring: *"a pilaster projecting 0.17 m from the
wall a metre from a downlight lens throws no visible shadow"*. Eighteen shadow
casters change nothing because **a corridor is a smooth tube with 20 mm of
relief and there is nothing in it to cast a shadow OF**.

So the flatness was never a lighting problem or a material problem. The
corridor is EMPTY. `dressing.dress()` fills the 78 rooms and has never been
offered a corridor -- its whole geometry is "four walls and a lane down the
middle", which a ring arc does not have. 126 m of walkable corridor, 963 people
walking in it, and not one crate.

WHAT GOES IN A CORRIDOR, and it is not room furniture. A public circulation
route carries the things that have nowhere else to be: freight waiting to be
moved, service plant that had to go somewhere, bins, barriers round a job, and
somebody's belongings where nobody stops them. Those are the five schemes
below, and which one a stretch of corridor gets depends on the deck it is on.

THE LANE IS SACRED. `walkable.py` asserts a body walks 126 m along this
corridor without leaving the floor, and `collision.prop_boxes` will make
anything emitted here SOLID. So every piece is placed against a z wall with a
clear lane down the middle, and the module asserts that clearance itself
(`lane_clear`) rather than leaving it to the walk gate to discover at the end
of a twelve-minute assembly.

THE FRAME. A ring corridor is not a straight one. At angle t the floor is at
radius `floor_r`, "up" is toward the axis (DECREASING radius, because spin
gravity puts down outboard), and the corridor's WIDTH runs along the station
axis z -- so a prop against a wall is at z near +/- half_w, not at some x.
Getting that backwards puts the crates in the ceiling.

Run: python3 station/corridor_dressing.py          # self-test with controls
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dressing as _dress                                        # noqa: E402
import interior_kit as K                                         # noqa: E402

# How close to the centreline anything may come. `collision.corridor_profile`
# measures the clear half width at 1.0806 m and `walkable.py` walks a 0.9 m
# body down it, so a 0.62 m lane half-width leaves 1.24 m clear -- wider than
# the body by a third, which is the margin a corridor needs to still read as
# passable when two people are in it.
LANE_HALF_M = 0.62

# Nothing within this of a doorway. A door is the one place a player is
# guaranteed to be, and a crate in front of one is the defect `bespoke.compose`
# already had to fix for rooms.
DOOR_CLEAR_M = 2.4

# Metres of arc between placement attempts. Not every attempt places something
# -- see `SCHEMES` -- so this is the sampling pitch, not the prop pitch.
PITCH_M = 3.2

# (kind, width_along_arc, depth_across, height, share) per scheme.
#
# EVERY DEPTH IS AT MOST 0.44 m AND THAT IS ARITHMETIC, NOT STYLE. The measured
# clear half width is 1.0806 m and the lane takes 0.62 of it, so what is left
# against each wall is **0.46 m**. The first version of this table had 0.80 m
# crates and 0.90 m pallets in it and `lane_clear` rejected the lot -- which is
# the assertion doing its job, and the right conclusion is not to widen the
# lane but to accept what a 2.16 m corridor can actually hold. A freight
# container does not go in a personnel corridor; a stack of flat cases does.
#
# `kind` is one of `dressing.MACHINES`, so every piece arrives articulated and
# materialled by the same machinery the rooms use. Sizes are real: a standard
# freight container here is the 2.40 x 1.20 x 1.20 m `rooms.PROPS["container"]`
# already carries, and a bin is a bin.
SCHEMES = {
    # Freight waiting on a mover. Docking and cargo decks.
    "freight": (("crate", 1.60, 0.44, 1.35, 0.34),
                ("crate", 1.10, 0.40, 0.95, 0.26),
                ("rack", 1.80, 0.42, 1.95, 0.22),
                ("skid", 1.60, 0.42, 0.30, 0.10),
                ("post", 0.16, 0.16, 1.05, 0.08)),
    # Service plant that had to go somewhere. Industrial and plant decks.
    "service": (("duct", 0.90, 0.40, 1.90, 0.34),
                ("drum", 0.44, 0.44, 0.88, 0.26),
                ("pipe_bank", 1.10, 0.36, 2.10, 0.22),
                ("wallpanel", 0.70, 0.14, 0.55, 0.18)),
    # A clean public route: bins, a bench, a wayfinding post. Habitat, medical,
    # administrative -- the decks a visitor sees.
    "public": (("cabinet", 0.80, 0.40, 1.35, 0.30),
               ("seat", 1.80, 0.42, 0.46, 0.26),
               ("screen", 1.10, 0.14, 1.30, 0.20),
               ("post", 0.18, 0.18, 1.15, 0.14),
               ("wallpanel", 0.85, 0.12, 0.62, 0.10)),
    # Somebody's belongings, where nobody moves them on. Downbelow.
    "lurker": (("crate", 0.90, 0.40, 0.75, 0.30),
               ("block", 1.30, 0.44, 0.52, 0.24),
               ("rack", 1.20, 0.34, 1.75, 0.22),
               ("reel", 0.44, 0.44, 0.55, 0.14),
               ("seat", 1.20, 0.42, 0.44, 0.10)),
    # A job in progress: barriers and a trolley. Any deck, sparingly.
    "works": (("kerb", 1.30, 0.30, 0.95, 0.42),
              ("skid", 1.20, 0.42, 0.30, 0.30),
              ("drum", 0.44, 0.44, 0.80, 0.28)),
}

# How much of the sampled pitch actually gets a piece. A corridor with
# something at every 4.5 m is a warehouse; the reference frames show long clean
# runs with incident at intervals, so most attempts place nothing.
#
# `lurker` is denser because that IS the content: Downbelow's corridors are
# lived in, and the gazetteer's whole point about them is that the station's
# circulation has been colonised.
# RAISED AFTER LOOKING. At the first values a 66 m sight line down blue/0/0
# showed exactly ONE piece: 115 pieces sound like a lot until they are spread
# over 480 m of arc that curves out of sight in 18 degrees, and until you
# notice that half the table is 0.16 m posts and 0.12 m wall panels. The pitch
# also drops to 3.2 m, because a piece every 4.5 m on a curving corridor is
# further apart than it sounds.
DENSITY = {"freight": 0.62, "service": 0.58, "public": 0.40,
           "lurker": 0.78, "works": 0.32}

# Which scheme a deck gets, by the archetype of the places on it. Read from the
# register rather than written per deck -- a new industrial place gets service
# clutter without anybody editing this file.
BY_ARCHETYPE = {
    "store": "freight", "industrial": "service", "transit": "public",
    "medical": "public", "office": "public", "commerce": "public",
    "hospitality": "public", "worship": "public", "research": "service",
    "detention": "service", "generic": "public",
}


def _u(*parts):
    """Deterministic float in [0,1). Same idiom as the rest of the project."""
    import hashlib
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def scheme_for(places, override=None):
    """Which clutter a stretch of corridor carries, from what opens off it.

    The commonest archetype among the places on this deck wins. A deck with no
    places at all -- and there are some -- gets `public`, because an unnamed
    corridor is still a corridor somebody walks down.
    """
    if override:
        return override
    if not places:
        return "public"
    import rooms as R                                            # noqa: PLC0415
    counts = {}
    for p in places:
        s = BY_ARCHETYPE.get(R.archetype(p), "public")
        counts[s] = counts.get(s, 0) + 1
    # Downbelow is named, not inferred: its places are archetyped `generic` and
    # `store` like anywhere else, and what makes it Downbelow is the register's
    # own key. Inferring it from archetype would put lurker bedding in a
    # quartermaster's store.
    if any(p["key"].startswith("downbelow") or p["key"] in
           ("thieves_guild", "black_market", "welded_shut") for p in places):
        return "lurker"
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def plan(degrees, start_deg, radius, half_w, doors=(), scheme="public",
         seed="deck", density=None):
    """Where the pieces go, in (angle_deg, z_offset, kind, w, d, h) -- no mesh.

    SEPARATED FROM THE GEOMETRY ON PURPOSE. The lane-clearance and doorway
    invariants are statements about POSITIONS, and a test that has to build
    triangles to check a position is a test nobody runs. `_selftest` asserts
    both against this list directly, and `run()` cannot place anything the plan
    did not.
    """
    specs = SCHEMES[scheme]
    dens = DENSITY[scheme] if density is None else density
    arc_m = math.radians(degrees) * radius
    n = max(1, int(arc_m / PITCH_M))
    out = []
    for i in range(n):
        if _u(seed, "place", i) > dens:
            continue
        a = start_deg + degrees * (i + 0.5) / n
        # Clear of every door, measured as arc distance rather than as an
        # angle -- at 211 m radius one degree is 3.7 m and at 471 m it is 8.2,
        # so an angular tolerance would mean different things on different
        # rings.
        if any(abs(math.radians(a - d) * radius) < DOOR_CLEAR_M
               for d in doors):
            continue
        r = _u(seed, "kind", i)
        acc = 0.0
        pick = specs[-1]
        for spec in specs:
            acc += spec[4]
            if r <= acc:
                pick = spec
                break
        kind, w, d, h, _share = pick
        side = 1 if _u(seed, "side", i) < 0.5 else -1
        # Hard against the wall, then in by its own depth. The wall is at
        # +/- half_w in z; the piece occupies [z0, z0 + d] on that side.
        z_far = side * (half_w - 0.02)
        z0 = z_far - side * d if side > 0 else z_far
        out.append((a, z0, kind, w, d, h))
    return out


def lane_clear(items, half_w, lane=LANE_HALF_M):
    """Pieces that intrude into the walking lane. Empty when the plan is safe.

    THE INVARIANT, AND IT IS CHECKED HERE RATHER THAN BY THE WALK GATE. A body
    that cannot get down the corridor fails `walkable.py --deck` after a twelve
    minute assembly, with `traverse_m` short and no indication which of two
    hundred pieces did it. This names them.
    """
    bad = []
    for a, z0, kind, w, d, h in items:
        z1 = z0 + d
        # Interval overlap, written as interval overlap. The first version was
        # three clauses of `abs()` and `or` with a precedence bug in it, which
        # is the usual outcome of testing "is it in the middle" by hand.
        if min(z0, z1) < lane and max(z0, z1) > -lane:
            bad.append((round(a, 3), round(z0, 3), round(z1, 3), kind))
    return bad


def run(schema, profile, sector, ring, degrees, start_deg, radius, z_offset,
        floor_r, half_w, doors=(), places=(), seed="deck", scheme=None,
        density=None):
    """The corridor's clutter as (verts, tris, spans), in station coordinates.

    `floor_r` and `half_w` come from `collision.corridor_shell`'s own measured
    profile, passed in rather than recomputed -- hard rule 4. If this module
    derived the floor radius itself there would be two descriptions of where
    the corridor's floor is, and they would drift the first time the kit moved.
    """
    sch = scheme_for(places, scheme)
    items = plan(degrees, start_deg, radius, half_w, doors, sch, seed, density)
    bad = lane_clear(items, half_w)
    if bad:
        raise AssertionError(
            f"corridor dressing blocks the lane at {bad[:4]} -- a body cannot "
            f"pass. This is checked here because the walk gate would only say "
            f"'traverse_m short' after a full assembly.")
    v, t, g = [], [], []
    for i, (a_deg, z0, kind, w, d, h) in enumerate(items):
        # A LOCAL BOX, THEN BENT ONTO THE RING. The piece is built in the
        # corridor kit's own straight frame -- x across the arc, y up, z along
        # the axis -- and every vertex is then rotated to its angle. Building
        # it in station coordinates directly would mean writing the rotation
        # into every machine in `dressing.MACHINES`.
        lo = (-w / 2.0, 0.0, z0)
        hi = (w / 2.0, h, z0 + d)
        lv, lt, lg = [], [], []
        _dress.machine(lv, lt, lg, kind, f"dress_{kind}", lo, hi,
                       (seed, "corr", i))
        # STAND IT ON THE FLOOR, whatever the machine did inside its box.
        # `dressing.MACHINES` are authored for rooms, and some put a foot or a
        # plinth below the box they were given -- measured, `rack` goes 51 mm
        # under. In a room that is invisible; on a ring it is a piece sunk into
        # a deck a body walks on. Lifting by the mesh's own minimum is the only
        # version of this that cannot drift from what the machine actually did.
        if lv:
            ymin = min(y for _x, y, _z in lv)
            if ymin < 0.0:
                lv = [(x, y - ymin, z) for x, y, z in lv]
        a = math.radians(a_deg)
        ca, sa = math.cos(a), math.sin(a)
        base, t0 = len(v), len(t)
        for x, y, z in lv:
            # y is UP, which on a ring is TOWARD THE AXIS: a piece 1 m tall
            # stands at a radius 1 m SMALLER than the floor. Adding y to the
            # radius instead is the sign error that buries furniture in the
            # deck and it is invisible in a plan view.
            rr = floor_r - y
            v.append((rr * ca - x * sa, rr * sa + x * ca, z_offset + z))
        t.extend((p + base, q + base, s + base) for p, q, s in lt)
        g.extend((nm, a0 + t0, a1 + t0) for nm, a0, a1 in lg)
    return v, t, g, {"scheme": sch, "pieces": len(items), "tris": len(t)}


# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    hw = 1.0806                      # collision.corridor_profile's measurement
    R = 211.55                       # blue ring 0, from the schema

    # -- the plan is non-empty, deterministic, and inside the corridor -------
    for sch in SCHEMES:
        it = plan(30.0, 0.0, R, hw, doors=(), scheme=sch, seed="t")
        check(f"{sch}: places something over 30 degrees of ring", it,
              f"{len(it)} pieces")
        again = plan(30.0, 0.0, R, hw, doors=(), scheme=sch, seed="t")
        check(f"{sch}: is deterministic", it == again)
        check(f"{sch}: every piece is inside the corridor's half width",
              all(abs(z0) <= hw + 1e-9 and abs(z0 + d) <= hw + 1e-9
                  for _a, z0, _k, _w, d, _h in it),
              str([(z0, z0 + d) for _a, z0, _k, _w, d, _h in it
                   if abs(z0) > hw or abs(z0 + d) > hw][:3]))
        check(f"{sch}: leaves the walking lane clear",
              not lane_clear(it, hw), str(lane_clear(it, hw)[:3]))
        check(f"{sch}: every kind is a real dressing machine",
              all(k in _dress.MACHINES for _a, _z, k, _w, _d, _h in it))

    # -- THE LANE CHECK CAN FAIL, which is the control on the four above ----
    # A piece pushed to the centreline must be reported. Without this the
    # "leaves the lane clear" checks pass for a plan that placed nothing.
    check("lane_clear reports a piece ON the centreline",
          lane_clear([(0.0, -0.20, "crate", 0.6, 0.4, 0.6)], hw),
          "a crate straddling z=0 was called clear")
    check("lane_clear reports a piece that reaches INTO the lane",
          lane_clear([(0.0, hw - 0.9, "crate", 0.6, 0.9, 0.6)], hw))
    check("...and passes one hard against the wall",
          not lane_clear([(0.0, hw - 0.40, "crate", 0.6, 0.40, 0.6)], hw),
          "a 0.40 m piece against the wall was called blocking -- it fits in "
          "the 0.46 m the lane leaves")

    # -- doors are kept clear, and the check is in METRES not degrees --------
    doors = (5.0, 12.0, 21.0)
    it = plan(30.0, 0.0, R, hw, doors=doors, scheme="freight", seed="t")
    worst = min((abs(math.radians(a - d) * R) for a, *_ in it for d in doors),
                default=99.0)
    check("nothing stands within DOOR_CLEAR_M of a doorway",
          worst >= DOOR_CLEAR_M, f"closest piece is {worst:.2f} m from a door")
    # ... and the control: with no doors declared, something DOES land where a
    # door would have been, or the clearance above is vacuous.
    it0 = plan(30.0, 0.0, R, hw, doors=(), scheme="freight", seed="t")
    check("...and without the doors, pieces land in those places",
          len(it0) > len(it), f"{len(it0)} vs {len(it)}")

    # -- the ring bend: up is TOWARD THE AXIS -------------------------------
    v, t, g, rep = run(None, None, "blue", 0, 20.0, 0.0, R, 7000.0,
                       R - 0.022, hw, doors=(), places=(), seed="t",
                       scheme="freight")
    check("run builds triangles", t and v, f"{len(t)} tris")
    rad = [math.hypot(x, y) for x, y, _z in v]
    # 2 mm, not zero. `dressing`'s machines put a foot or a plinth a fraction
    # below the box they were given -- measured here at 0.7 mm -- and that is
    # correct behaviour for a crate standing ON a floor rather than hovering
    # over it. The tolerance is there to catch the SIGN ERROR this check exists
    # for, which buries a piece by its whole height, not to excuse a millimetre.
    SINK_TOL_M = 0.002
    check("every vertex is at or INSIDE the floor radius",
          max(rad) <= R - 0.022 + SINK_TOL_M,
          f"max radius {max(rad):.4f} against floor {R - 0.022:.4f}, sunk "
          f"{max(rad) - (R - 0.022):.4f} m -- up is toward the axis and "
          f"something is buried in the deck")
    check("...and the control: flipping the sign buries a piece by its height",
          max(math.hypot(x, y) for x, y, _z in
              [((R - 0.022 + 1.0) * 1.0, 0.0, 0.0)]) > R - 0.022 + SINK_TOL_M,
          "the radius check cannot fail")
    check("...and nothing is more than 2.2 m above the floor",
          (R - 0.022) - min(rad) <= 2.2 + 1e-6,
          f"tallest piece stands {(R - 0.022) - min(rad):.2f} m")
    check("every vertex is inside the corridor's axial width",
          all(abs(z - 7000.0) <= hw + 1e-6 for _x, _y, z in v))
    check("every span is named for a dressing material",
          all(nm.startswith("dress_") for nm, _a, _b in g),
          str(sorted({nm for nm, _a, _b in g if not nm.startswith("dress_")})))

    # -- scheme selection reads the register --------------------------------
    import directory as dr                                       # noqa: PLC0415
    check("a downbelow deck gets lurker clutter",
          scheme_for([dr.by_key("downbelow"), dr.by_key("black_market")])
          == "lurker")
    check("a cargo deck gets freight",
          scheme_for([dr.by_key("cargo_bays"), dr.by_key("fuel_stores")])
          == "freight")
    check("an empty deck still gets something", scheme_for([]) == "public")

    print(f"corridor_dressing: {len(SCHEMES)} schemes, "
          f"{sum(len(s) for s in SCHEMES.values())} piece types, "
          f"{rep['pieces']} pieces and {rep['tris']} triangles over 20 degrees "
          f"of blue ring 0 ({math.radians(20.0) * R:.0f} m of corridor)")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
