#!/usr/bin/env python3
"""Can anybody START this thing, and is any of it dead code?

TWO GATES, AND THEY ARE THE DELIVERABLE RATHER THAN THE CODE THEY GUARD.

G1 COLD START
    Launch the scene `godot/project.godot` actually ships -- with NO arguments
    at all, the way a person double-clicking it would -- and assert that a
    player exists, is standing on a floor, has a HUD, and that the station
    clock is advancing. Within a stated number of seconds, and it prints what
    it found.

    Every other launch path in this repository is a developer typing
    `--glb=<path>`. `station/walkable.py` passes eleven arguments; the render
    harness passes a scene path and a shot name. **Nothing tested the shipped
    entry point**, and as of session 4g the shipped entry point was
    `scenes/exterior.tscn`, whose only script is `render_shot.gd` -- a
    screenshot tool. There was no way to start the game because there was no
    game to start, and no gate could fail for it.

G3 NOTHING UNREACHABLE
    Static reachability over `godot/scripts/*.gd` from `run/main_scene`. A game
    script that nothing reachable references is dead code, however well tested
    it is.

    This is the third recurrence of one failure. `station/npc/`'s twelve
    modules had zero importers; `npc/animation.py` had no importer; and then
    2,630 lines of finished GDScript -- the station clock (`life.gd`), all of
    layer 7's audio (`ambience.gd`) and the flyable Starfury (`starfury.gd`) --
    sat with zero inbound references from anything. It survives because **every
    other gate here is a module self-test, and a module self-test passes
    whether or not anything calls it.** `audio.py` reads 100/100 and no sound
    had ever played.

WHY THE TOOL EXEMPTION IS NAMED IN CODE RATHER THAN SKIPPED QUIETLY.
`render_shot.gd` and `verify_materials.gd` are offline harnesses -- one takes
the frames every craft claim in this project cites, the other checks material
binding -- and both are launched by a tool with an explicit scene or `--script`
argument. They are not part of the game and being unreachable from `main_scene`
is correct for them. That is a decision, so it is written down here with its
reason and printed in the report; a silent `continue` would be a gate quietly
choosing what it is allowed to fail on.

Run:
    python3 station/coldstart.py            # both gates
    python3 station/coldstart.py --g3       # reachability only, no engine
    python3 station/coldstart.py --g1       # cold start only
    python3 station/coldstart.py --g3 --verbose
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GODOT_DIR = os.path.join(ROOT, "godot")

# ---------------------------------------------------------------------------
# G3 -- static reachability
# ---------------------------------------------------------------------------

# Offline harnesses, not game code. See the module docstring: each is launched
# by a driver that names its own scene or script, so having no inbound reference
# from `main_scene` is the correct state for them and not a defect.
#
# WRITTEN OUT, ONE ENTRY PER SCRIPT, AND DELIBERATELY NOT DERIVED. The obvious
# improvement is to exempt anything a Python driver launches -- `route_walk.py`
# names `route_test.tscn`, `materials.py` names `verify_materials.gd`, so the
# rule would never go stale. It was written that way first and then struck,
# because `station/starfury_scene.py` names `res://scenes/starfury.tscn` and
# `station/walkable.py` names `res://scenes/walk.tscn`: under that rule the
# flyable Starfury and the entire walkable build become exempt, and G3 goes
# green on **exactly the defect it was written to catch**. A derived rule that
# is blind to the original bug is worse than a list somebody has to update,
# because the list going stale turns the gate RED and costs a two-minute
# decision -- which is what happened here, within one session, when another
# agent landed `route_test.gd`.
#
# So: an exemption is a decision, it is made here by name, and it carries its
# reason. `harness_drivers()` below only ANNOTATES a failure with the driver
# that launches the script, so the next reader can make that decision in one
# line instead of going looking.
TOOL_SCRIPTS = {
    "render_shot.gd": "the frame harness every craft claim in this project "
                      "cites -- tools/render_godot.sh names its scene",
    "verify_materials.gd": "material-binding check, run with --script",
    "route_test.gd": "the G2 ROUTE WALKED harness -- station/route_walk.py "
                     "writes its manifest and launches scenes/route_test.tscn, "
                     "a rig no game scene references",
}


def harness_drivers():
    """Every Godot resource a Python or shell driver in this repo launches.

    DIAGNOSTIC ONLY -- see TOOL_SCRIPTS for why this does not grant exemptions.
    Returns {res path: driver path} so an unreachable script can be reported
    with the thing that does launch it.

    `coldstart.py` is skipped: this file names `res://scenes/exterior.tscn` as
    its own negative control, and a gate that reacts to what it says about
    itself is a gate marking its own homework.
    """
    out = {}
    pats = ("station/*.py", "tools/*.py", "tools/*.sh")
    for pat in pats:
        for p in sorted(glob.glob(os.path.join(ROOT, pat))):
            if os.path.basename(p) == "coldstart.py":
                continue
            with open(p, "r", errors="replace") as f:
                text = f.read()
            if "godot" not in text.lower():
                continue
            for r in RES_RE.findall(text):
                out.setdefault(r, os.path.relpath(p, ROOT))
    # One hop through the scene: `route_walk.py` names route_test.tscn, and the
    # script is what has to be exempted.
    for res, driver in list(out.items()):
        if res.endswith(".tscn") and os.path.exists(res_path(res)):
            for r in references(res_path(res)):
                out.setdefault(r, driver)
    return out

# A reference to a Godot resource, anywhere in a file: `preload(...)`,
# `load(...)`, `extends "..."`, an `ext_resource` row, a const holding a path.
# Matching the PATH rather than the call is deliberate -- there are five ways to
# name a script in GDScript and one regex over the string catches all of them.
RES_RE = re.compile(r"res://[A-Za-z0-9_./\-]+\.(?:gd|tscn)")


def strip_comments(text, marker):
    """Remove comments, respecting string literals.

    A DOCSTRING IS NOT A REFERENCE, and this gate is worthless without that
    distinction: `life.gd`'s own header contains
    `var L := preload("res://scripts/life.gd")` as usage documentation, and
    `arrival.tscn` carries the command line that runs it. A grep over raw
    source calls both of those live edges and reports a wired station.
    """
    out = []
    for line in text.splitlines():
        quote = None
        cut = len(line)
        i = 0
        while i < len(line):
            c = line[i]
            if quote:
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif c in "\"'":
                quote = c
            elif line.startswith(marker, i):
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


def references(path):
    """Every res:// resource this file names, outside comments."""
    with open(path, "r", errors="replace") as f:
        text = f.read()
    marker = ";" if path.endswith((".tscn", ".godot")) else "#"
    return sorted(set(RES_RE.findall(strip_comments(text, marker))))


def res_path(res):
    return os.path.join(GODOT_DIR, res[len("res://"):])


def main_scene():
    """What `project.godot` actually ships, read rather than assumed."""
    with open(os.path.join(GODOT_DIR, "project.godot")) as f:
        for line in f:
            m = re.match(r'\s*run/main_scene\s*=\s*"([^"]+)"', line)
            if m:
                return m.group(1)
    return None


def line_count(path):
    with open(path, "r", errors="replace") as f:
        return sum(1 for _ in f)


# The scene this project shipped before session 4g. `g3(from_scene=...)` runs
# the identical walk from it and MUST come back red -- it is the negative
# control, kept in the repository rather than in a session log, because the only
# thing that makes a reachability gate real is that a scene which reaches
# nothing still reads as reaching nothing. Its only script is `render_shot.gd`.
CONTROL_SCENE = "res://scenes/exterior.tscn"


def g3(verbose=False, from_scene=None, quiet=False):
    start = from_scene or main_scene()
    scripts = sorted(glob.glob(os.path.join(GODOT_DIR, "scripts", "*.gd")))
    report = {"main_scene": start, "scripts": len(scripts)}
    if start is None:
        print("G3 FAIL -- project.godot declares no run/main_scene")
        report["ok"] = False
        return report

    # BFS from the shipped scene over "this file names that file".
    seen, queue, edges = set(), [start], {}
    while queue:
        res = queue.pop(0)
        if res in seen:
            continue
        seen.add(res)
        p = res_path(res)
        if not os.path.exists(p):
            continue
        refs = references(p)
        edges[res] = refs
        for r in refs:
            if r not in seen:
                queue.append(r)

    # Inbound counts over EVERY file, reachable or not. Reachability is the
    # gate; inbound count is what says whether an unreachable script is
    # orphaned outright or merely stranded behind another orphan -- which is a
    # different repair and worth knowing without a second run.
    inbound = {}
    for p in scripts + sorted(glob.glob(os.path.join(GODOT_DIR, "scenes",
                                                     "*.tscn"))):
        res = "res://" + os.path.relpath(p, GODOT_DIR).replace(os.sep, "/")
        inbound.setdefault(res, 0)
        for r in references(p):
            inbound[r] = inbound.get(r, 0) + 1

    drivers = harness_drivers()
    dead, tools, live = [], [], []
    for p in scripts:
        name = os.path.basename(p)
        res = "res://scripts/" + name
        row = {"script": name, "lines": line_count(p),
               "inbound": inbound.get(res, 0)}
        if res in seen:
            live.append(row)
        elif name in TOOL_SCRIPTS:
            row["why"] = TOOL_SCRIPTS[name]
            tools.append(row)
        else:
            if res in drivers:
                row["driver"] = drivers[res]
            dead.append(row)

    report.update(reachable=len(live), dead=len(dead), tools=len(tools),
                  dead_lines=sum(r["lines"] for r in dead),
                  dead_list=[r["script"] for r in dead],
                  ok=not dead)

    if quiet:
        return report
    print("G3 NOTHING UNREACHABLE -- static reachability from %s" % start)
    print("  %d scripts: %d reachable, %d exempt tools, %d UNREACHABLE"
          % (len(scripts), len(live), len(tools), len(dead)))
    for r in tools:
        print("    exempt  %-22s %5d lines  -- %s"
              % (r["script"], r["lines"], r["why"]))
    if verbose:
        for r in sorted(live, key=lambda r: -r["lines"]):
            print("    live    %-22s %5d lines, %d inbound"
                  % (r["script"], r["lines"], r["inbound"]))
    for r in sorted(dead, key=lambda r: -r["lines"]):
        print("    DEAD    %-22s %5d lines, %d inbound reference(s)%s"
              % (r["script"], r["lines"], r["inbound"],
                 ("  -- but %s launches it; if that is a harness rather than "
                  "game code, add it to TOOL_SCRIPTS with a reason"
                  % r["driver"]) if "driver" in r else ""))
    if dead:
        print("  G3 FAIL -- %d script(s), %d lines, cannot be reached from the "
              "scene this project ships" % (len(dead), report["dead_lines"]))
    else:
        print("  G3 PASS -- every game script is reachable from %s" % start)
    if from_scene is None:
        ctrl = g3(from_scene=CONTROL_SCENE, quiet=True)
        good = not ctrl.get("ok")
        print("  %s control: from %s -- %d unreachable, %d lines %s"
              % ("ok  " if good else "FAIL", CONTROL_SCENE, ctrl["dead"],
                 ctrl["dead_lines"],
                 "(this is the scene that shipped before session 4g)"
                 if good else "-- THE CONTROL DID NOT FIRE"))
        report["ok"] = report["ok"] and good
    if verbose:
        print("  edges:")
        for k in sorted(edges):
            for r in edges[k]:
                print("    %s -> %s" % (k, r))
    return report


# ---------------------------------------------------------------------------
# G1 -- cold start
# ---------------------------------------------------------------------------

# How long a cold start may take, wall clock, from `exec` to the verdict line.
# This is the number a person waits at a black screen. It is DERIVED rather than
# discovered: the shipped boot measured 6.3 s on this four-core box -- 65 MB of
# glTF parsed, 509 mesh groups materialled out of `interior.tscn`, 561 lights
# made, a collision proxy trimeshed, 73 residents bound and 13 audio streams
# loaded -- and the budget is 5x that, which absorbs a loaded machine and still
# fails the regression that matters. Trimeshing the 509 VISUAL meshes instead of
# the 4-mesh proxy is the obvious way to break this, and it costs minutes, not
# seconds. A budget set to "whatever it measured" cannot fail; one set to 150 s
# could not fail either, which is the same defect wearing a bigger number.
BOOT_BUDGET_S = 30.0
# The body is spawned 50 mm over the shell and settles. More than a step means
# it is not where the floor is. Same bar as `walkable.py::MAX_DECK_DROP_M`.
MAX_DROP_M = 0.30


def godot_binary():
    cand = ("/home/user/godot-build/godot-4.4-stable/bin/"
            "godot.linuxbsd.editor.double.x86_64")
    if os.path.exists(cand) and os.access(cand, os.X_OK):
        return cand
    for c in glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*double*"):
        if os.access(c, os.X_OK):
            return c
    return None


def parse_verdict(text, tag):
    m = re.search(tag + r" (.+)", text)
    if not m:
        return None
    out = {}
    for tok in m.group(1).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def g1(timeout=None, verbose=False, budget=BOOT_BUDGET_S, extra=()):
    godot = godot_binary()
    if godot is None:
        print("G1 FAIL -- no double-precision Godot binary found")
        return {"ok": False}
    # NO ARGUMENTS. Not a scene path, not a `--`, not one `--glb=`. That is the
    # entire point of this gate: what a person gets when they launch the thing.
    # `--headless` is the container having no display, not a mode -- `main.gd`
    # sees a headless display server, runs its own check and quits, because a
    # build nobody can start is exactly what this is here to catch.
    cmd = [godot, "--headless", "--path", GODOT_DIR]
    if extra:
        cmd += ["--"] + list(extra)
    t0 = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout or (budget * 2))
    except subprocess.TimeoutExpired:
        print("G1 FAIL -- the shipped scene did not reach a verdict in %.0f s"
              % (timeout or budget * 2))
        return {"ok": False}
    wall = time.time() - t0
    out = res.stdout + res.stderr
    if verbose:
        print(out)
    d = parse_verdict(out, "COLDSTART")
    print("G1 COLD START -- `%s --headless --path godot%s`%s"
          % (os.path.basename(godot),
             (" -- " + " ".join(extra)) if extra else "",
             "" if extra else ", no arguments"))
    if d is None:
        print("  no COLDSTART verdict printed (exit %d, %.1f s)"
              % (res.returncode, wall))
        for line in out.splitlines()[-25:]:
            print("    | " + line)
        print("  G1 FAIL -- the shipped main_scene printed no verdict")
        return {"ok": False, "wall_s": wall}

    for line in out.splitlines():
        if line.startswith(("COLDSTART ", "AMBIENCE ", "HUD ", "CLOCK ",
                            "main:")):
            print("  " + line)

    def num(k, default=0.0):
        try:
            return float(d.get(k, default))
        except ValueError:
            return default

    checks = [
        ("player", "a player exists", d.get("player") == "1"),
        ("on_floor", "it is standing on a floor",
         d.get("on_floor") == "true"),
        ("drop", "it did not fall through (%.3f m <= %.2f m)"
         % (num("drop_m"), MAX_DROP_M), num("drop_m", 9.9) <= MAX_DROP_M),
        ("hud", "there is a HUD", d.get("hud") == "1"),
        ("hud_reads", "the HUD reads the world",
         d.get("hud_place", "") not in ("", "-")),
        ("clock", "the clock is advancing (%s -> %s)"
         % (d.get("h0", "?"), d.get("h1", "?")),
         d.get("clock_advanced") == "true"),
        ("bodies", "the crowd is bound to it (%s bodies)"
         % d.get("bodies", "0"), num("bodies") > 0),
        ("day", "03:00 and 13:00 differ (%s vs %s present)"
         % (d.get("present_0300", "?"), d.get("present_1300", "?")),
         d.get("present_0300") != d.get("present_1300")),
        ("audio", "the station is audible (%s layers)"
         % d.get("audio_layers", "0"), num("audio_layers") > 0),
        ("budget", "cold in %.1f s (budget %.0f s)" % (wall, budget),
         wall <= budget),
    ]
    ok = True
    got = {}
    for key, name, good in checks:
        print("    %s %s" % ("ok  " if good else "FAIL", name))
        got[key] = bool(good)
        ok = ok and good
    print("  G1 %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok, "wall_s": wall, "verdict": d, "checks": got}


# Each control removes ONE thing and must break exactly the check that names it.
# `--no-hud` is `walk.gd`'s own flag, not one written for this file, so the
# control exercises the same switch a developer already had.
CONTROLS = [
    (["--no-hud"], ["hud", "hud_reads"], "no interface is built"),
    (["--no-clock"], ["clock", "bodies", "day"], "no clock, nobody keeps a day"),
    (["--no-sound"], ["audio"], "the station is silent"),
]


def controls(verbose=False, budget=BOOT_BUDGET_S):
    """Show that G1 can fail, one removed thing at a time.

    A GATE THAT CANNOT FAIL IS A PRINTOUT. This project has been caught by that
    twice at plan scale -- layer 2's exit criterion that a cube passed, and
    layer 4's median that a washed-out frame matched -- so the cold start is
    made to fail three times, on purpose, and each failure has to land on the
    check that names the missing thing and not somewhere else.
    """
    print("G1 CONTROLS -- each removes one thing and must fail on it")
    ok = True
    for flags, expect, why in CONTROLS:
        r = g1(verbose=verbose, budget=budget, extra=flags)
        got = r.get("checks", {})
        fired = sorted(k for k, v in got.items() if not v)
        good = (not r.get("ok")) and set(fired) == set(expect)
        print("  %s %-12s %s -- failed on [%s], expected [%s]"
              % ("ok  " if good else "FAIL", " ".join(flags), why,
                 ", ".join(fired), ", ".join(expect)))
        ok = ok and good
    print("  CONTROLS %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g1", action="store_true", help="cold start only")
    ap.add_argument("--g3", action="store_true", help="reachability only")
    ap.add_argument("--controls", action="store_true",
                    help="only the negative controls on G1")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--budget-s", type=float, default=BOOT_BUDGET_S)
    a = ap.parse_args()
    run_all = not (a.g1 or a.g3 or a.controls)
    bad = 0
    if a.g3 or run_all:
        if not g3(a.verbose).get("ok"):
            bad += 1
    if a.g1 or run_all:
        if run_all:
            print()
        if not g1(verbose=a.verbose, budget=a.budget_s).get("ok"):
            bad += 1
    # THE CONTROLS RUN IN THE DEFAULT PASS, not behind an opt-in flag. Three
    # extra launches at ~7 s each is what it costs to know the gate above can
    # still fail, and "a gate that does not run is not a gate" is written into
    # CLAUDE.md at the cost of thirty red CI runs that reported nothing.
    if a.controls or run_all:
        print()
        if not controls(verbose=a.verbose, budget=a.budget_s).get("ok"):
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
