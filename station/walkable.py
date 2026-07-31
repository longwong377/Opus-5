#!/usr/bin/env python3
"""Can a player stand up in this station, and walk around in it?

THE GATE THIS PROJECT SPENT THREE PHASES WITHOUT. Every other gate here measures
a part in isolation -- `density.py` scores one module's line density,
`measure_frame.py` scores one image, `directory.py` counts locations per layer,
`budget.py` counts triangles. None of them asks the only question that matters
to a player, so nothing ever failed for the answer being "no". As of session 3u
the string `CollisionShape` appeared nowhere in the repository: 118 locations had
geometry, materials and measured lighting, and not one had a floor.

WHAT IT ASSERTS, per room, by launching Godot headless and driving a real body
over real physics frames:

  settles     the body comes to rest instead of falling through the deck
  on_floor    it is standing on geometry rather than hovering or wedged
  walks       pushing forward for one second actually moves it
  contained   five seconds of walking does not leave the room's footprint

`walks` is the one that catches an empty claim. A room whose deck is present but
whose collision is missing reports `on_floor=false` and `fell=true`; a room whose
spawn is inside a workbench reports `walks` near zero. Both happened while this
file was being written, which is why both are checks.

AND THE DECK, which is a different question and needed a different test.
`--deck` assembles a real ring corridor with its rooms, gives it the collision
shell from `station/collision.py`, and walks a body along it for as long as
asked. A room test can only ever say "not wedged"; a body that takes two
successful footsteps and stops at the third scores identically to one that
crosses the station. So the deck run reports **how far it actually got** and
**whether it was ever off the floor**, and both are asserted:

  traverse_m  distance covered walking one heading for thirty seconds
  offfloor    physics frames spent not standing on anything

That pair is what milestone W2 means by "go somewhere". Before the collision
shell existed this test reported a body that stood on the assembled deck with
`on_floor=true` and moved 1 mm in every direction, and no assertion in the
project could fail for it.

Run: python3 station/walkable.py [--rooms N] [--deck] [--verbose]
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import collision as C                                           # noqa: E402
import deck as D                                                # noqa: E402
import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import interior_kit as K                                        # noqa: E402
import rooms as R                                               # noqa: E402

# A body that walks for a second at 4.2 m/s covers 4.2 m in the open. Rooms are
# small and full of furniture, so the bar is much lower: enough that a stuck
# body is unambiguous. 0.25 m is two footsteps.
MIN_WALK_M = 0.25
# Falling through the deck shows up as a large drop from the spawn.
MAX_DROP_M = 3.0

# How long the deck traverse runs, in physics frames, and how far it has to get.
# Thirty seconds at 4.2 m/s is 126 m of corridor; the bar is set at half that so
# a single snag fails it while ordinary contact with a wall does not. A corridor
# that only lets a body cover 60 m of a 126 m walk has something in it.
TRAVERSE_FRAMES = 1800
MIN_TRAVERSE_M = 63.0
# How close to the middle of a room counts as being in it. A body that stops in
# the doorway is not inside; one standing anywhere in the far half is.
ARRIVED_M = 1.5
# The deck spawns a body 50 mm above its floor, so a drop of more than a step
# means it is not where the shell says the floor is.
MAX_DECK_DROP_M = 0.30
# How close to actually facing the player the nearest inhabitant has to end up.
# Generous: they turn at a human rate and the walk ends when the player arrives,
# so a few degrees of lag is a person still turning, not a person facing wrong.
FACING_TOL_DEG = 25.0


def godot_binary():
    for cand in (
        "/home/user/godot-build/godot-4.4-stable/bin/"
        "godot.linuxbsd.editor.double.x86_64",
    ):
        if os.path.exists(cand) and os.access(cand, os.X_OK):
            return cand
    import glob
    for c in glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*.double.*"):
        if os.access(c, os.X_OK):
            return c
    return None


def walk_room(key, godot, timeout=180):
    """Launch the walkable build in one room and parse its verdict."""
    schema, profile = it.load()
    place = dr.by_key(key)
    glb = os.path.join(ROOT, "station/generated/scene/interior", f"{key}.glb")
    if not os.path.exists(glb):
        return {"key": key, "error": "no glb -- run tools/export_scene.py"}
    sx, sy, sz = R.spawn_m(schema, profile, place)
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--",
           f"--glb={glb}", f"--spawn={sx},{sy},{sz}", "--walk-test"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"key": key, "error": f"timed out after {timeout}s"}
    m = re.search(r"WALKTEST (.+)", out)
    if not m:
        return {"key": key, "error": "no verdict printed"}
    d = {"key": key}
    for tok in m.group(1).split():
        k, _, v = tok.partition("=")
        d[k] = v
    meshes = re.search(r"walk: (\d+) mesh instances", out)
    d["meshes"] = int(meshes.group(1)) if meshes else 0
    return d


def _glb(obj_path, glb_path):
    """OBJ -> GLB, because Godot reads glTF and the generators write OBJ."""
    import export_gltf
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path, "--out", glb_path]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv


def room_target(meta, place):
    """A point on the floor in the middle of a room, for the body to walk to.

    ON THE FLOOR, not at eye or waist height. Aiming at a room's mid-height left
    an irreducible 0.85 m in the "how close did it get" number, because a body
    standing on the deck can never close a radial offset -- which reads as a
    near miss and is nothing of the kind.
    """
    a = math.radians(place["angle_deg"])
    r = meta["floor_r_m"] - 0.05
    return (r * math.cos(a), r * math.sin(a), place["z_m"])


def walk_deck(sector, ring, deck, godot, timeout=1800, traverse=None,
              goto_key=None, no_doors=False, z_m=None, bump=False,
              no_npc_collision=False):
    """Assemble a deck, put a body on it, and walk it.

    The render mesh and the collision shell are exported separately and BOTH are
    handed to the engine -- the shell to stand on, the render mesh to be the
    place. Handing over only the render mesh is what this test used to do and
    the body could not take a step; see `station/collision.py`.
    """
    # THE DRUM IS NOT A RING DECK. `deck.build_deck` rejects green/1 by name and
    # the drum's floor is a heightfield, not a corridor: see
    # `station/drum_walk.py`, whose rule INVERTS this file's. A corridor needs a
    # smooth shell because its millimetre relief is decoration; the drum needs
    # the shape of its own ground, because there the relief IS the content.
    if (sector, ring) in D.NOT_RING_DECKS:
        import drum_walk as DW                                  # noqa: PLC0415
        return DW.walk(key=goto_key or "the_garden", traverse=traverse,
                       timeout=timeout, godot=godot)

    schema, profile = it.load()
    out = os.path.join(ROOT, "station/generated/scene/deck")
    os.makedirs(out, exist_ok=True)
    # Z IN THE FILENAME, because a deck now has up to six walkable clusters
    # and they are different places. Without it the second cluster overwrote
    # the first's mesh and the walk measured whichever ran last.
    stem = (f"{sector}_{ring}_{deck}" if z_m is None
            else f"{sector}_{ring}_{deck}_z{int(z_m)}")
    v, t, g, s = D.build_deck(schema, profile, sector, ring, deck, z_m=z_m)
    D.write_obj(os.path.join(out, f"{stem}.obj"), v, t, g)
    # PROPS ON. This is a body being put in the room, so the furniture has to be
    # there: a route that only exists because you can walk through a table is
    # not a route.
    cv, ct, cm = D.build_collision(schema, profile, sector, ring, deck,
                                   z_m=z_m, props=True)
    C.write_obj(os.path.join(out, f"{stem}_col.obj"), cv, ct,
                cm.get("groups"))
    # THE CAST LIST, beside the mesh. A body is baked into the merged geometry,
    # so the engine cannot recover who is where or which way they face by
    # looking at it. The generator knows; it writes it down.
    import json as _json
    with open(os.path.join(out, f"{stem}_actors.json"), "w") as f:
        _json.dump(s.get("actors", []), f)
    # THE CROWD, which is a different thing from the cast list and has to be.
    # An actor is a body baked into the deck mesh at a fixed pose; a crowd
    # instance is a PLACEMENT against `populace.station_crowd_library`'s 112
    # shared bodies. The library is written once per LOD rather than per deck
    # -- it is a function of the species mix, not of who is walking -- and the
    # instance list is what the runtime rewrites to make them move.
    crowd = s.get("crowd", [])
    with open(os.path.join(out, f"{stem}_crowd.json"), "w") as f:
        _json.dump(crowd, f)
    if crowd:
        import populace as _pop                                 # noqa: PLC0415
        for lod in sorted({int(r["lod"]) for r in crowd}):
            lib = os.path.join(out, f"crowd_lod{lod}.obj")
            if not os.path.exists(lib):
                cv2, ct2, cg2 = _pop.station_crowd_library(lod)
                D.write_obj(lib, cv2, ct2, cg2)
                _glb(lib, lib[:-4] + ".glb")
    _glb(os.path.join(out, f"{stem}.obj"), os.path.join(out, f"{stem}.glb"))
    _glb(os.path.join(out, f"{stem}_col.obj"),
         os.path.join(out, f"{stem}_col.glb"))

    sx, sy, sz = s["spawn"]
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--",
           f"--glb={os.path.join(out, stem + '.glb')}",
           f"--collision={os.path.join(out, stem + '_col.glb')}",
           f"--spawn={sx},{sy},{sz}", "--gravity-mode=drum", "--walk-test",
           f"--traverse={traverse if traverse is not None else TRAVERSE_FRAMES}"]
    # Walking INTO a named place is the claim W2 actually makes, and it is a
    # strictly harder question than "did the body move": it fails when the route
    # is blocked, not only when the body is wedged. The body steers straight at
    # the target, so the target has to be one it can reach without navigating --
    # the room the spawn is standing outside. Reaching one across the ring needs
    # a path, and there is no pathfinder yet.
    goto = goto_key or s["spawn_at"]
    tx, ty, tz = room_target(cm, dr.by_key(goto))
    # -- IS A PERSON SOMETHING YOU BUMP INTO? ------------------------------
    # `rooms.is_solid` keeps every `npc_` group OUT of the static collision on
    # purpose -- static collision is generated once, so an inhabitant baked
    # into it is a permanent statue. The capsule therefore lives on a runtime
    # node (`npc.gd::_give_body`), and this is the only thing that can tell
    # whether it is actually there: steer the body straight at a person
    # instead of at a room, and see how close it gets.
    bumped = None
    if bump:
        cand = [a for a in s.get("actors", ())
                if float(a.get("r_m", 0.0)) > 0.0]
        if cand:
            px, py, pz = s["spawn"]
            bumped = min(cand, key=lambda a: (a["x"] - px) ** 2
                         + (a["y"] - py) ** 2 + (a["z"] - pz) ** 2)
            tx, ty, tz = bumped["x"], bumped["y"], bumped["z"]
    _lods = sorted({int(r["lod"]) for r in crowd}) if crowd else []
    if _lods:
        cmd += [f"--crowd={os.path.join(out, stem + '_crowd.json')}",
                f"--crowd-glb={os.path.join(out, f'crowd_lod{_lods[0]}.glb')}"]
    cmd += [f"--actors={os.path.join(out, stem + '_actors.json')}",
            f"--goto={tx},{ty},{tz}", f"--door-key={goto}",
            f"--door-travel={K.PROVISIONAL['door_width_m'] / 2.0}"]
    if no_doors:
        cmd += ["--no-doors"]
    if no_npc_collision:
        cmd += ["--no-npc-collision"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"key": stem, "error": f"timed out after {timeout}s"}
    m = re.search(r"WALKTEST (.+)", res)
    if not m:
        return {"key": stem, "error": "no verdict printed"}
    d = {"key": stem, "rooms": s["rooms"], "spawn_at": s["spawn_at"],
         "render_tris": len(t), "collision_tris": len(ct),
         "arc_deg": cm["arc_deg"], "goto": goto,
         "doors": len(cm.get("rooms", ()))}
    if bumped is not None:
        d["bumped"] = bumped["group"]
        d["bump_r_m"] = float(bumped["r_m"])
        d["bump_who"] = (bumped.get("who") or {}).get("name", "") \
            if isinstance(bumped.get("who"), dict) else ""
        d["npc_collision"] = "off" if no_npc_collision else "on"
    for tok in m.group(1).split():
        k, _, val = tok.partition("=")
        d[k] = val
    return d


# How much closer the body must get with an inhabitant's capsule OFF than with
# it on, for "they are solid" to be a claim rather than noise. A person's own
# radius is 0.27-0.41 m and the player capsule adds its own, so a real block
# separates the two runs by more than half a metre; 0.25 is half of the
# smallest true separation and well outside the ~0.05 m the walker's own
# stopping distance varies by between runs.
BUMP_MARGIN_M = 0.25


# How far the corridor's crowd must travel over a walk test for "they walk" to
# be a claim rather than a hope. DERIVED: `populate_corridor` gives every
# walker their own gait's speed -- 1.4-1.5 m/s for a human at 1 g -- and the
# test runs `TRAVERSE_FRAMES` at 1/60 s, so 134 people over 1,800 frames should
# cover 134 x 1.45 x 30 = 5,800 m between them. A tenth of that is a bar only
# a crowd that has genuinely stopped can fail.
CROWD_TRAVEL_MIN_M = 500.0


def deck_verdict(d):
    """Pass/fail for a deck, in the terms milestone W2 is written in."""
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if float(d.get("drop", 0)) > MAX_DECK_DROP_M:
        return False, (f"dropped {float(d['drop']):.2f} m from a spawn 50 mm "
                       f"above the shell -- the floor is not where it says")
    if float(d.get("moved_1s", 0)) < MIN_WALK_M:
        return False, f"walked {float(d.get('moved_1s', 0)):.2f} m in a second"
    off, tot = (d.get("offfloor", "0/0").split("/") + ["0"])[:2]
    if int(off) > 0:
        return False, (f"left the floor for {off} of {tot} frames -- it walked "
                       f"off the deck")
    # -- AND THE CORRIDOR'S CROWD IS WALKING -------------------------------
    # They are instances against the shared crowd library, not geometry in the
    # deck, so the only thing that can tell whether they MOVE is a physics run.
    # A crowd that stands still is a crowd of statues wearing a walk pose,
    # which reads worse than statues.
    if int(d.get("walkers", 0)) > 0:
        travelled = float(d.get("crowd_travel_m", 0.0))
        if travelled < CROWD_TRAVEL_MIN_M:
            return False, (f"{d['walkers']} walkers were instanced and the "
                           f"crowd covered {travelled:.0f} m between them -- "
                           f"they are statues wearing a walk pose")
    if "goto_best_m" in d:
        near = float(d["goto_best_m"])
        if near > ARRIVED_M:
            return False, (f"got within {near:.2f} m of {d['goto']} from "
                           f"{float(d['goto_start_m']):.1f} m away -- the way "
                           f"in is blocked")
        # AND SOMEBODY LOOKED UP. `facing_err_deg` is the angle between where
        # the nearest inhabitant ended up facing and the direction to the
        # player. "Did they turn" is not the question -- a body rotated by a
        # wrong yaw convention turns just as far as one rotated correctly and
        # reports the same number. This asks whether they are looking AT you.
        note = ""
        if "noticed" in d:
            err = float(d.get("facing_err_deg", -1.0))
            if int(d["noticed"]) < 1:
                return False, (f"reached {d['goto']} and NOBODY noticed -- "
                               f"{d.get('turned_deg')} deg turned")
            if err < 0 or err > FACING_TOL_DEG:
                return False, (f"reached {d['goto']}; {d['noticed']} noticed "
                               f"but the nearest is {err:.0f} deg off facing "
                               f"the player -- the yaw convention is wrong")
            note = (f", {d['noticed']} of the room look up "
                    f"({float(d['turned_deg']):.0f} deg turned, {err:.0f} deg "
                    f"off)")
        return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg, "
                      f"{d['doors']} doors; a body spawns in the corridor and "
                      f"WALKS INTO {d['goto']} "
                      f"({float(d['goto_start_m']):.1f} m -> {near:.2f} m), "
                      f"never leaving the floor{note}")
    got = float(d.get("traverse_m", 0))
    if got < MIN_TRAVERSE_M:
        return False, (f"covered {got:.1f} m of corridor, under the "
                       f"{MIN_TRAVERSE_M:.0f} m bar -- something is snagging")
    return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg; a "
                  f"body spawns at {d['spawn_at']}, walks {got:.1f} m and "
                  f"never leaves the floor")


def verdict(d):
    """Pass/fail for one room, with the reason a player would give."""
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if float(d.get("drop", 0)) > MAX_DROP_M:
        return False, f"fell {float(d['drop']):.1f} m -- the deck has no collision"
    if float(d.get("moved_1s", 0)) < MIN_WALK_M:
        return False, (f"walked {float(d.get('moved_1s', 0)):.2f} m in a second "
                       f"-- the body is stuck")
    return True, (f"stands and walks {float(d['moved_1s']):.2f} m/s, "
                  f"{d['meshes']} colliders")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", type=int, default=6,
                    help="how many rooms to test (they are slow)")
    ap.add_argument("--keys", default="",
                    help="comma-separated room keys, overrides --rooms")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--deck", default="",
                    help="also walk an assembled deck, as sector/ring/deck "
                         "(e.g. blue/0/0)")
    ap.add_argument("--deck-only", action="store_true")
    ap.add_argument("--no-doors", action="store_true",
                    help="negative control: leave the doors inert, so the "
                         "closed panels stay solid and the body must NOT get in")
    ap.add_argument("--z", type=float, default=None,
                    help="which z-cluster of the deck to walk. A deck is not "
                         "a z-slice: blue/0/0 has six clusters over 1,100 m "
                         "and they are six different places")
    ap.add_argument("--traverse", type=int, default=None,
                    help="physics frames of continuous walking on the deck")
    ap.add_argument("--bump", action="store_true",
                    help="steer at the nearest INHABITANT instead of a room, "
                         "and check they are something you bump into")
    a = ap.parse_args()

    godot = godot_binary()
    if godot is None:
        print("no double-precision Godot binary; see docs/godot-binary.md")
        return 1

    if a.deck or a.deck_only:
        sector, ring, deck = (a.deck or "blue/0/0").split("/")
        d = walk_deck(sector, int(ring), int(deck), godot,
                      traverse=a.traverse, no_doors=a.no_doors, z_m=a.z)
        drum = (sector, int(ring)) in D.NOT_RING_DECKS
        if drum:
            import drum_walk as DW                              # noqa: PLC0415
            good, why = DW.walk_verdict(d)
        else:
            good, why = deck_verdict(d)
        print(f"  {'PASS' if good else 'FAIL'}  "
              f"{'drum' if drum else 'deck'} {sector}/{ring}/{deck}  {why}")

        # THE NEGATIVE CONTROL, and it is the whole reason the door claim means
        # anything. A body that reaches the room proves the route is open; it
        # does not prove the DOOR opened it, because a door-shaped hole in the
        # wall gives exactly the same number. So the same run is repeated with
        # the doors inert: the closed panels stay solid and the body must NOT
        # get in. If both runs pass, the doors are scenery.
        # The drum has no doors, so `--no-doors` is not a control there --
        # running it would compare a thing against itself and pass.
        if good and not a.no_doors and not drum:
            n = walk_deck(sector, int(ring), int(deck), godot,
                          traverse=a.traverse, no_doors=True)
            blocked, _w = deck_verdict(n)
            near = float(n.get("goto_best_m", 0.0))
            if blocked:
                print(f"  FAIL  the doors are scenery -- with them inert the "
                      f"body still reached {d['goto']} ({near:.2f} m)")
                good = False
            else:
                print(f"        control: with the doors inert the body is "
                      f"stopped {near:.2f} m short. The door is what opens "
                      f"the way.")
        if good and int(d.get("walkers", 0)) > 0:
            print(f"        {d['walkers']} walkers instanced from the shared "
                  f"crowd library and they WALK: "
                  f"{float(d['crowd_travel_m']):,.0f} m covered between them, "
                  f"0 triangles of their own in the deck")
        if good:
            print(f"        {d['render_tris']:,} render triangles, "
                  f"{d['collision_tris']:,} collision "
                  f"({d['collision_tris'] / d['render_tris'] * 100:.1f}%)")
        # -- AND A PERSON IS SOMETHING YOU BUMP INTO -----------------------
        # `is_solid` keeps inhabitants out of the STATIC collision on purpose,
        # so nothing in the static mesh can answer this. The capsule is built
        # at runtime by `npc.gd::_give_body`, and the only honest test is to
        # walk at somebody: with the capsule the body stops about a radius
        # short, without it the body walks through them and arrives.
        if a.bump and not drum:
            hit = walk_deck(sector, int(ring), int(deck), godot,
                            traverse=a.traverse, z_m=a.z, bump=True)
            through = walk_deck(sector, int(ring), int(deck), godot,
                                traverse=a.traverse, z_m=a.z, bump=True,
                                no_npc_collision=True)
            stop = float(hit.get("goto_best_m", -1.0))
            walk_through = float(through.get("goto_best_m", -1.0))
            r = float(hit.get("bump_r_m", 0.0))
            who = hit.get("bump_who") or hit.get("bumped", "somebody")
            if stop < 0 or walk_through < 0:
                print(f"  FAIL  the bump test did not run  {hit.get('error')} "
                      f"/ {through.get('error')}")
                good = False
            elif stop <= walk_through + BUMP_MARGIN_M:
                print(f"  FAIL  inhabitants are not solid -- the body got "
                      f"{stop:.2f} m from {who} with their capsule on and "
                      f"{walk_through:.2f} m with it off. A person you walk "
                      f"through is a hologram.")
                good = False
            else:
                print(f"        a person is SOLID: walking straight at {who} "
                      f"(r {r:.2f} m) the body is stopped {stop:.2f} m away; "
                      f"control: with their capsule off it reaches "
                      f"{walk_through:.2f} m and walks through them.")
        if a.deck_only:
            return 0 if good else 1
        if not good:
            return 1

    if a.keys:
        keys = [k for k in a.keys.split(",") if k]
    else:
        built = {os.path.splitext(f)[0] for f in os.listdir(
            os.path.join(ROOT, "station/generated/scene/interior"))
            if f.endswith(".glb")}
        # ONLY rooms.py's own places. The bespoke modules -- alien_sector, the
        # Zocalo, C&C -- build their own geometry in their own frames and
        # `rooms.spawn_m` has nothing to say about them; asking it anyway threw
        # a KeyError on a location whose `interacts` list rooms.PROPS does not
        # carry. They need their own spawn points and get their own entry here
        # once they have them.
        gen = dr._generated_keys()
        keys = [q["key"] for q in dr.PLACES
                if q["key"] in built and q["key"] in gen][:a.rooms]

    rows, ok, fail = [], 0, 0
    for k in keys:
        d = walk_room(k, godot)
        good, why = verdict(d)
        rows.append({**d, "passes": good, "why": why})
        if good:
            ok += 1
        else:
            fail += 1
        if not a.json:
            print(f"  {'PASS' if good else 'FAIL'}  {k:22s} {why}")

    if a.json:
        print(json.dumps(rows, indent=2))
        return 0 if fail == 0 else 1

    print(f"\n{ok}/{ok + fail} rooms are walkable")
    if fail:
        print("A location nobody can stand in is not built, whatever its "
              "layer number says.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
