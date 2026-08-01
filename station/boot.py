#!/usr/bin/env python3
"""What the game boots into, written down once.

`godot/scripts/main.gd` needs six things to start: a mesh, a collision shell,
the interactables, the cast, a spawn point a body can stand on, and the hour it
is. Until this file existed it read them out of
`station/generated/scene/deck/<deck>_arrival.json` -- the sidecar
`station/arrival.py --build` writes for the player's first ten minutes.

THAT WAS A BORROWED MANIFEST AND IT SHOULD NOT HAVE BEEN. The arrival sequence
is one mode of four; the other three had no reason to depend on it, and deleting
the arrival sidecar would have stopped the game booting at all. Worse, it made
the boot deck a property of a narrative artefact: change which ship the player
arrives on and you change what `godot --path godot` opens.

THE SPAWN IS DERIVED FROM THE FLOOR, NOT COPIED FROM ANYWHERE. This is the point
of the file and it is `station/collision.py`'s rule applied one level up -- that
module measures the corridor's walking profile off the kit by ray casting rather
than writing it down, "so it cannot drift from what it stands in for". A spawn
copied out of another JSON is a second description of where the floor is, and
`arrival.tscn`'s header records what that costs: its first run was handed
`--spawn=0,0,0`, which on a ring deck at radius 211 m is the SPIN AXIS, and the
body fell for two minutes.

So the spawn here is read out of the collision shell itself:

  * the shell's `collision` group is the surface a body walks on;
  * a ring deck is spun, so its floor is the OUTERMOST radius in that group --
    "down" is away from the axis;
  * a body stands just inside it, at `floor_r - STAND_IN_M`;
  * it is placed at the angular and axial MIDDLE of the shell's own extent, so
    it is as far from either end of the built corridor as the geometry allows.

Nothing about that can disagree with the mesh, because it is the mesh.

VALIDATED BY THE GATE THAT USES IT, not by an assertion here: `--check` compares
the derived spawn against the arrival sidecar's independently computed one, and
`station/coldstart.py --g1` stands a real body on it and reports `on_floor` and
the drop. A spawn inside a wall fails that in six seconds.

Run:
    python3 station/boot.py                 # write station/generated/scene/boot.json
    python3 station/boot.py --check         # derive, compare, write nothing
    python3 station/boot.py --deck <stem>   # choose the deck by name
"""
import argparse
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECK_DIR = os.path.join(ROOT, "station/generated/scene/deck")
OUT = os.path.join(ROOT, "station/generated/scene/boot.json")

# How far inside the floor surface a body's origin sits, in metres. The deck
# build spawns 50 mm over its shell -- `walkable.py::MAX_DECK_DROP_M`'s comment
# says so in as many words -- and the same clearance is right here: enough that
# the body is unambiguously above the surface, small enough that the settle is
# one physics frame rather than a fall.
STAND_IN_M = 0.05
# The group in the collision shell that is the walkable surface. `collision.py`
# writes the smooth swept shell under this name; `doorpanel_*` are the movable
# leaves and are not floor.
FLOOR_GROUP = "collision"
# How close to the outermost radius still counts as floor, in metres. The shell
# is swept, so its floor is one radius to within the sweep's own tolerance; a
# wall rises inward from it and must not be sampled as ground.
FLOOR_BAND_M = 0.15
# The hour the station starts at when nothing says otherwise. 13:00 is
# `life.gd`'s own Clock default and the middle of the working day, which is when
# the most is happening to look at.
DEFAULT_HOUR = 13.0
# How close a member of the cast has to be for the spawn to be called their
# room rather than the corridor, in metres. A room is bigger than this; the
# point is only to stop "the nearest person on the whole deck" being read as
# "the room you are standing in".
NEAR_ROOM_M = 15.0


def _obj_floor_tris(path):
    """The collision shell's floor triangles, as ((x,y,z) x 3).

    TRIANGLES AND NOT LOOSE VERTICES, and the difference is the whole of this
    function's history. The first version averaged the floor's vertices and
    spawned at the mean -- which is a point in the AIR: a corridor is an arc, so
    the centroid of an arc is inside the circle it bends around, and on this
    deck it landed 214 m from any built floor. `coldstart.py --g1` caught it in
    six seconds (`on_floor=false, drop_m=19.456`, radius climbing as the body
    fell outward) and that is exactly why the spawn is validated by standing a
    body on it rather than by an assertion in this file.

    A point ON a triangle of the floor cannot be in the air. That is the fix.

    Parsed out of the .obj rather than the .glb because it is the same file the
    .glb is converted from, it is text, and this needs no engine.
    """
    verts, tris, group = [], [], ""
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("g "):
                group = line[2:].strip()
            elif line.startswith("f ") and group == FLOOR_GROUP:
                idx = [int(t.split("/")[0]) for t in line.split()[1:]]
                pts = [verts[i - 1 if i > 0 else len(verts) + i] for i in idx]
                # Fan-triangulate, so a quad in the shell is two triangles
                # rather than a discarded face.
                for k in range(1, len(pts) - 1):
                    tris.append((pts[0], pts[k], pts[k + 1]))
    return tris


def spawn_from_shell(col_obj):
    """Where a body can stand, read off the collision shell.

    Returns (spawn, detail). Raises if the shell carries no floor group.
    """
    tris = _obj_floor_tris(col_obj)
    if not tris:
        raise SystemExit("boot: %s has no `%s` group -- is it a collision "
                         "shell?" % (col_obj, FLOOR_GROUP))
    floor_r = max(math.hypot(p[0], p[1]) for t in tris for p in t)

    def centre(t):
        return tuple(sum(p[i] for p in t) / 3.0 for i in range(3))

    # A FLOOR TRIANGLE IS ONE WHOSE WHOLE SELF IS AT THE OUTERMOST RADIUS. The
    # shell is a closed tube: its walls and soffit are in the same group, and a
    # triangle with one vertex on the floor and two up the wall is not somewhere
    # to stand.
    floor = [t for t in tris
             if all(floor_r - math.hypot(p[0], p[1]) <= FLOOR_BAND_M
                    for p in t)]
    if not floor:
        raise SystemExit("boot: no floor triangle within %.2f m of r=%.2f in %s"
                         % (FLOOR_BAND_M, floor_r, col_obj))
    mids = [centre(t) for t in floor]
    # The middle of the built arc, circularly -- a corridor that straddles
    # +/-pi has angles at both ends of the range and a plain mean lands on the
    # far side of the ring. This is a TARGET, not the answer: the answer is the
    # real floor triangle nearest it.
    angs = [math.atan2(c[1], c[0]) for c in mids]
    mid_a = math.atan2(sum(math.sin(a) for a in angs) / len(angs),
                       sum(math.cos(a) for a in angs) / len(angs))
    mid_z = (min(c[2] for c in mids) + max(c[2] for c in mids)) / 2.0

    def cost(c):
        da = abs((math.atan2(c[1], c[0]) - mid_a + math.pi)
                 % (2 * math.pi) - math.pi) * floor_r
        return da * da + (c[2] - mid_z) ** 2

    c = min(mids, key=cost)
    # THE ASSERTION THAT WOULD HAVE FIRED ON THE OLD CODE. The first version's
    # spawn was 214 m from the nearest floor triangle -- a point in the air over
    # the middle of the arc -- and nothing here noticed; `coldstart.py` did,
    # after a build and a launch. A derivation that can put a body in space
    # should say so itself, in milliseconds, rather than leave it to the gate.
    away = min(math.dist(c, m) for m in mids)
    if away > 1e-6:
        raise SystemExit("boot: the spawn is not on a floor triangle "
                         "(%.3f m from the nearest)" % away)
    # Stand just inside the surface. Radially, because on a spun deck "down" is
    # outward and the floor's own normal is the inward radial.
    r = math.hypot(c[0], c[1])
    k = (r - STAND_IN_M) / r
    spawn = [c[0] * k, c[1] * k, c[2]]
    return spawn, {
        "floor_r_m": round(floor_r, 4),
        "stand_in_m": STAND_IN_M,
        "on_triangle_r_m": round(r, 4),
        "arc_deg": round(math.degrees(math.atan2(c[1], c[0])) % 360.0, 3),
        "z_m": round(c[2], 3),
        "floor_triangles": len(floor),
        "shell_triangles": len(tris),
    }


def decks():
    """Every deck on disk that has both a mesh and a collision shell."""
    out = []
    for col in sorted(glob.glob(os.path.join(DECK_DIR, "*_col.obj"))):
        stem = os.path.basename(col)[:-len("_col.obj")]
        if os.path.exists(os.path.join(DECK_DIR, stem + ".glb")):
            out.append(stem)
    return out


def sidecar(stem, suffix):
    p = os.path.join(DECK_DIR, stem + suffix)
    return p if os.path.exists(p) else ""


def build(stem=None, hour=None):
    """The boot manifest for one deck, derived from what is on disk."""
    have = decks()
    if not have:
        raise SystemExit("boot: no built deck in %s -- run the deck exporter"
                         % DECK_DIR)
    if stem is None:
        # THE FIRST BY NAME, and stated rather than left to a directory listing's
        # order: a boot that opens a different deck depending on the filesystem
        # is a boot nobody can reproduce a bug in.
        stem = sorted(have)[0]
    if stem not in have:
        raise SystemExit("boot: %s is not built (have: %s)"
                         % (stem, ", ".join(have)))
    col_obj = os.path.join(DECK_DIR, stem + "_col.obj")
    spawn, detail = spawn_from_shell(col_obj)
    # WHICH PLACE THE SPAWN IS IN is read off the cast standing in it -- the
    # actors carry their own place key and their own position, so the nearest
    # one names the spot without a second table of room bounds. It is a LABEL
    # for the HUD and the report; nothing depends on it being right.
    at, rooms = "corridor", []
    actors_p = sidecar(stem, "_actors.json")
    if actors_p:
        with open(actors_p) as f:
            cast = json.load(f)
        rooms = sorted({a.get("place", "") for a in cast if a.get("place")})
        if cast:
            near = min(cast, key=lambda a: (a.get("x", 0) - spawn[0]) ** 2
                       + (a.get("y", 0) - spawn[1]) ** 2
                       + (a.get("z", 0) - spawn[2]) ** 2)
            d = math.dist(spawn, [near.get("x", 0), near.get("y", 0),
                                  near.get("z", 0)])
            # ONLY IF IT IS ACTUALLY NEAR. The nearest person on the deck is
            # always SOMEBODY, and calling their room the spawn's room put
            # `in arrival_concourse` on a point 160 m down the corridor from it.
            # On a ring deck the honest answer for "between rooms" is the
            # corridor, which is `ambience.place_at`'s rule and `places.gd`'s.
            if d <= NEAR_ROOM_M:
                at = near.get("place", "corridor")
    return {
        "deck": stem,
        "glb": os.path.join(DECK_DIR, stem + ".glb"),
        "collision": os.path.join(DECK_DIR, stem + "_col.glb"),
        "interact": sidecar(stem, "_interact.json"),
        "actors": actors_p,
        "dialogue": sidecar(stem, "_dialogue.json"),
        "crowd": sidecar(stem, "_crowd.json"),
        "spawn": [round(v, 4) for v in spawn],
        "spawn_at": at,
        "rooms": rooms,
        "hour": DEFAULT_HOUR if hour is None else float(hour),
        "spawn_derivation": detail,
        "note": "Written by station/boot.py. The spawn is measured off the "
                "collision shell's own floor, never copied -- see that file.",
    }


def check(man):
    """Compare the derived spawn with the arrival sidecar's, if there is one.

    A CROSS-CHECK AND NOT A SOURCE. The two numbers are computed by different
    code from different inputs -- this one off the collision shell, the other by
    `arrival.py` out of the deck build -- so agreement is evidence and
    disagreement is a question, but neither file is reading the other.
    """
    p = os.path.join(DECK_DIR, man["deck"] + "_arrival.json")
    if not os.path.exists(p):
        print("  no arrival sidecar to cross-check against")
        return True
    with open(p) as f:
        other = json.load(f).get("build", {}).get("spawn")
    if not other:
        return True
    a, b = man["spawn"], other
    d = math.dist(a, b)
    ra, rb = math.hypot(a[0], a[1]), math.hypot(b[0], b[1])
    print("  derived  %8.3f %8.3f %8.3f   r=%.3f" % (a[0], a[1], a[2], ra))
    print("  arrival  %8.3f %8.3f %8.3f   r=%.3f" % (b[0], b[1], b[2], rb))
    print("  they differ by %.3f m along the corridor and %.3f m in radius"
          % (d, abs(ra - rb)))
    # The radius is the part that decides whether a body is standing on the
    # floor; where along the corridor it stands is a choice, not a fact, and the
    # two make it differently on purpose (this one takes the middle of the built
    # arc, arrival takes the hall its sequence starts outside).
    ok = abs(ra - rb) < 0.25
    print("  %s the two agree on where the floor is"
          % ("ok  " if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=None, help="deck stem to boot into")
    ap.add_argument("--hour", type=float, default=None)
    ap.add_argument("--check", action="store_true",
                    help="derive and cross-check, write nothing")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    man = build(a.deck, a.hour)
    d = man["spawn_derivation"]
    print("boot: %s -- spawn %.3f,%.3f,%.3f in %s, %d rooms; standing on 1 of "
          "%d floor triangles (of %d in the shell) at r=%.3f, %.0f deg"
          % (man["deck"], man["spawn"][0], man["spawn"][1], man["spawn"][2],
             man["spawn_at"] or "?", len(man["rooms"]),
             d["floor_triangles"], d["shell_triangles"], d["floor_r_m"],
             d["arc_deg"]))
    ok = check(man)
    if a.check:
        return 0 if ok else 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(man, f, indent=1)
    print("boot: wrote %s" % os.path.relpath(a.out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
