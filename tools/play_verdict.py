#!/usr/bin/env python3
"""Is the build PLAYABLE? Read a launch log and say so, in terms that can fail.

WHAT THIS EXISTS TO STOP. Every gate in this project measures a part in
isolation, and `station/walkable.py` -- the one that asks a whole-station
question -- drives the engine through six command-line arguments naming files a
fresh clone does not have. It answers "can a body be made to walk here", which
is not the same question as "can a person press Play and be in the station".
Between sessions 3u and 4d the answer to the first was yes on 128 locations and
the answer to the second was no, everywhere, and nothing could fail for it.

So this reads the log of a launch made with NO ARGUMENTS AT ALL -- the
configuration a person is actually in -- and asserts, in order:

  the manifest resolved            somebody built a deck and the engine found it
  a collision proxy loaded         there is a floor, and it is not the render mesh
  materials bound                  it is the dressed station, not grey geometry
  interactables wired              the things the register declares are there
  the build said PLAYABLE          it took the human branch, not the test branch
  a body is standing               on_floor, on the LAST report and not just one
  it is where the spawn claimed    within MAX_DROP_M of it, so it did not fall in
  the crowd is moving              travel_m > 0, so the corridor is not statues

Usage:  tools/play_verdict.py <logfile> [--manifest godot/play.json]
Exit 0 if the build is playable, 1 if it is not. Every failure prints what it
measured and what it wanted.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# How far the body may end up from the spawn the generator claimed. The spawn
# puts feet 50 mm above the shell and the body settles onto it, so anything past
# a single step means the floor is not where the collision mesh says it is --
# the same number and the same reasoning as `walkable.MAX_DECK_DROP_M`.
MAX_DROP_M = 0.30

# How fast a body that is doing nothing may be moving. Nobody is at the
# keyboard during a verify run, so the only thing that can move the player is
# the world -- and the world moving you at a walking pace, in a corridor with
# 134 people in it, is the crowd carrying you off. 0.05 m/s is well under the
# slowest walker (1.4 m/s) and well over the millimetre-scale settling of a
# capsule finding its floor.
MAX_IDLE_SPEED_M_S = 0.05

PLAY_RE = re.compile(
    r"PLAY frame=(\d+) feet=([-\d.]+),([-\d.]+),([-\d.]+) r=([-\d.]+) "
    r"on_floor=(\w+) speed=([\d.]+) fn=([-\d.]+),([-\d.]+),([-\d.]+) "
    r"crowd=(\d+) travel_m=([\d.]+) yielding=(\d+) prompt=(\S+)")


def parse(log_text):
    """Everything the verdict needs, pulled out of one launch's output."""
    d = {"play": []}
    m = re.search(r"walk: PLAYING (\S+) -- (\S+?), (\d+) room\(s\), (\d+) "
                  r"actors, (\d+) in the crowd, (\d+) interactables", log_text)
    if m:
        d["deck"], d["spawn_at"] = m.group(1), m.group(2)
        d["rooms"], d["actors"] = int(m.group(3)), int(m.group(4))
        d["crowd_declared"], d["interacts"] = int(m.group(5)), int(m.group(6))
    m = re.search(r"walk: (\d+) collision meshes \(proxy\), (\d+) visual",
                  log_text)
    if m:
        d["collision_meshes"], d["visual_meshes"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"dress: (\d+)/(\d+) meshes MATERIALLED, (\d+) group", log_text)
    if m:
        d["bound"], d["meshes"], d["fallback"] = (int(m.group(1)),
                                                  int(m.group(2)),
                                                  int(m.group(3)))
    d["dress_null"] = "MATCHED A RULE THAT IS NULL" in log_text
    d["dress_failed"] = "dress: FAILED" in log_text
    m = re.search(r"walk: (\d+) interactables wired, (\d+) pressable", log_text)
    if m:
        d["wired"], d["pressable"] = int(m.group(1)), int(m.group(2))
    d["playable_line"] = "walk: PLAYABLE." in log_text
    d["nothing_to_play"] = "walk: NOTHING TO PLAY" in log_text
    for m in PLAY_RE.finditer(log_text):
        d["play"].append({
            "frame": int(m.group(1)),
            "feet": (float(m.group(2)), float(m.group(3)), float(m.group(4))),
            "r": float(m.group(5)), "on_floor": m.group(6) == "true",
            "speed": float(m.group(7)),
            "fn": (float(m.group(8)), float(m.group(9)), float(m.group(10))),
            "crowd": int(m.group(11)), "travel_m": float(m.group(12)),
            "yielding": int(m.group(13)), "prompt": m.group(14)})
    return d


def verdict(d, manifest=None):
    """(ok, [lines]) -- the claim, itemised, each one able to fail."""
    out, ok = [], True

    def check(good, msg):
        nonlocal ok
        out.append(("  ok  " if good else "  FAIL") + "  " + msg)
        if not good:
            ok = False

    if d.get("nothing_to_play"):
        return False, ["  FAIL  there is no godot/play.json -- nothing was "
                       "built, so there is nothing to stand in"]

    check("deck" in d,
          f"the manifest resolved: {d.get('deck', '(none)')}, spawn "
          f"{d.get('spawn_at', '?')}, {d.get('rooms', 0)} room(s), "
          f"{d.get('actors', 0)} actors, {d.get('interacts', 0)} interactables"
          if "deck" in d else
          "the manifest did NOT resolve -- the engine had no deck to load")
    check(d.get("collision_meshes", 0) > 0,
          f"{d.get('collision_meshes', 0)} collision mesh(es) as a proxy, "
          f"{d.get('visual_meshes', 0)} visual with none -- a player walks on a "
          f"surface built for walking on")
    check(d.get("bound", 0) > 0 and not d.get("dress_null")
          and not d.get("dress_failed"),
          f"{d.get('bound', 0)}/{d.get('meshes', 0)} meshes materialled, "
          f"{d.get('fallback', 0)} on the glTF fallback"
          + (" -- BUT A RULE RESOLVED TO NULL" if d.get("dress_null") else "")
          + (" -- BUT DRESSING FAILED" if d.get("dress_failed") else ""))
    check(d.get("wired", 0) > 0,
          f"{d.get('wired', 0)} interactables wired, "
          f"{d.get('pressable', 0)} pressable")
    check(d.get("playable_line"),
          "the build took the PLAYABLE branch (no --walk-test, no --shot)"
          if d.get("playable_line") else
          "the build never printed PLAYABLE -- it did not take the human branch")

    play = d.get("play", [])
    check(bool(play),
          f"{len(play)} heartbeat(s) from the playable build"
          if play else
          "the playable build never reported -- it never reached a physics frame")
    if not play:
        return ok, out

    # EVERY REPORT, NOT THE LAST ONE. The failure this gate was written against
    # was intermittent -- the player was shoved off the floor, fell, landed,
    # was shoved again -- so a body sampled at the wrong instant looks fine.
    # "It never left the floor" is the claim; "it is on the floor now" is not.
    last = play[-1]
    air = [p for p in play if not p["on_floor"]]
    check(not air,
          f"a body STOOD for all {len(play)} reports, to frame {last['frame']} "
          f"({last['frame'] / 60.0:.0f} s), r={last['r']:.2f} m"
          if not air else
          f"the body was off the floor at {len(air)} of {len(play)} reports "
          f"(first frame {air[0]['frame']}) -- it is being pushed off, falling "
          f"or wedged")

    if manifest and "spawn" in manifest:
        sx, sy, sz = manifest["spawn"]
        far = max(play, key=lambda p: (p["feet"][0] - sx) ** 2
                  + (p["feet"][1] - sy) ** 2 + (p["feet"][2] - sz) ** 2)
        fx, fy, fz = far["feet"]
        drift = ((fx - sx) ** 2 + (fy - sy) ** 2 + (fz - sz) ** 2) ** 0.5
        check(drift <= MAX_DROP_M,
              f"it never got further than {drift:.3f} m from the spawn the "
              f"generator claimed (bar {MAX_DROP_M} m, worst at frame "
              f"{far['frame']}) -- nothing carried it off and the floor is "
              f"where the shell says")

    # AND IT IS NOT BEING CARRIED. Nobody is at the keyboard, so any speed at
    # all comes from the world moving the player -- which is how 134 walking
    # capsules bulldozed a standing body 66 km in the first run of this gate.
    fast = [p for p in play if p["speed"] > MAX_IDLE_SPEED_M_S]
    check(not fast,
          f"and it is STILL: peak speed {max(p['speed'] for p in play):.3f} m/s "
          f"with nobody at the keyboard (bar {MAX_IDLE_SPEED_M_S})"
          if not fast else
          f"the body is MOVING on its own -- {len(fast)} of {len(play)} reports "
          f"above {MAX_IDLE_SPEED_M_S} m/s, peak "
          f"{max(p['speed'] for p in fast):.3f} m/s. Something in the world is "
          f"carrying it")

    if last["crowd"] > 0:
        check(last["travel_m"] > 0.0,
              f"{last['crowd']} people in the corridor have covered "
              f"{last['travel_m']:.0f} m between them by frame {last['frame']}"
              if last["travel_m"] > 0 else
              f"{last['crowd']} people were instanced and have covered 0 m -- "
              f"the crowd only moves for the gate")
        yielded = max(p["yielding"] for p in play)
        out.append(f"        {yielded} of them stopped for the player at the "
                   f"busiest moment rather than walk through")
    else:
        out.append("        (no crowd on this cluster)")
    seen = [p["prompt"] for p in play if p["prompt"] != "-"]
    if seen:
        out.append(f"        prompted with {seen[0]} while standing still")
    return ok, out


def main():
    args = [a for a in sys.argv[1:]]
    man_path = os.path.join(ROOT, "godot", "play.json")
    if "--manifest" in args:
        i = args.index("--manifest")
        man_path = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    with open(args[0], errors="replace") as f:
        text = f.read()
    manifest = None
    if os.path.exists(man_path):
        try:
            manifest = json.load(open(man_path))
        except (ValueError, OSError):
            manifest = None
    ok, lines = verdict(parse(text), manifest)
    print("\n".join(lines))
    print(f"  {'PLAYABLE' if ok else 'NOT PLAYABLE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
