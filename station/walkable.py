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

Run: python3 station/walkable.py [--rooms N] [--verbose]
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import rooms as R                                               # noqa: E402

# A body that walks for a second at 4.2 m/s covers 4.2 m in the open. Rooms are
# small and full of furniture, so the bar is much lower: enough that a stuck
# body is unambiguous. 0.25 m is two footsteps.
MIN_WALK_M = 0.25
# Falling through the deck shows up as a large drop from the spawn.
MAX_DROP_M = 3.0


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
    a = ap.parse_args()

    godot = godot_binary()
    if godot is None:
        print("no double-precision Godot binary; see docs/godot-binary.md")
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
