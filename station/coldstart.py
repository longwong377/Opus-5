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

G4 THE CARD IS READ ON THE WAY IN
    Walk a body across every place boundary the shipped build actually has and
    assert the reader said something, and that what it said agrees with the
    arithmetic `consequence.certain_check` did at bake time.

    Same failure again, the eleventh time. `consequence.py` has carried the
    six-rung identicard ladder, the arrest chain and visa revocation since
    P1-G2. All of it was reachable from Python and NONE of it from the game: a
    player could walk into the command deck of a military station unchallenged,
    and no gate could fail for it because every gate here scores a part against
    a standard and a part with no caller still meets its standard.

    A static scan can tell you a caller exists. Only running the thing tells you
    the caller runs -- and the first version of this gate proved the point by
    failing with "this build named no place boxes": the check had been wired
    into `hud.gd`'s mesh-name place resolution, and the shipped build STREAMS,
    so it uses the sidecar path instead. It would have been unreachable in the
    only build a player launches.

    What it does NOT claim: the arrest chain behind a refusal is still Python. A
    refused player is TOLD they are refused and is not yet detained.

G5 SOMEBODY COLLAPSES AND A PLAYER IS THERE
    The same failure a fourth way, and this one had it on BOTH sides at once.
    `station/incident.py` has decided who collapses, where and at what hour
    since P1-G3 -- with a named resident as the subject -- and wrote it into a
    ledger nothing read. `godot/scripts/ragdoll.gd` can drop a 16-segment body
    at the deck's own 7.454 m/s^2 along its own radius, and the only thing that
    had ever asked for one was `--ragdoll-gate`, a flag no player passes. Two
    finished halves, no join.

    G5 asserts the join in the shipped scene: `boot.py` bakes the day's
    ragdoll-bearing incidents over this deck's own rooms, `main.gd` fires them
    as the clock passes their hour, and the body that falls comes OUT OF THE
    CROWD -- a walker who was standing there, matched to the incident's species
    where the crowd has one.

    It found a defect on its first real run that six sessions of rendering had
    not: `npc.gd::_walker_xform` built `Basis(fwd.cross(up), up, fwd)`, whose
    determinant is exactly -1, so every walker in the corridor was drawn as
    their own reflection. `ragdoll.gd` refuses a mirrored transform, which is
    how it surfaced.

G6 THE FIELD IS RIGHT ALL THE WAY ROUND THE RING
    THE DEFECT IT CLOSES SHIPPED, and it is not the one that was written down.
    `STATE.md` §24.5 recorded that `player.gd` returned `-Y` at 9.81 in "deck"
    mode and that `walk.gd` shipped that mode. Half wrong: `main.gd` line 305
    sets `gravity_mode` to "drum", so the DIRECTION was already radial. What
    shipped broken was the MAGNITUDE -- nothing anywhere set `gravity_m_s2`, so
    the 9.81 export default stood and a player fell **31.6% too fast at every
    angle**, on a deck that delivers 7.4523 m/s^2.

    Two controls, because there are two wrong answers: `--legacy-field` is what
    shipped (radial, 9.81); `--legacy-deck` is the default nobody was using
    (-Y at 9.81), which keeps the floor at only 5 of 18 angles and puts the body
    179.98 deg from up -- standing on the ceiling -- at 90 deg.

    It does not read a variable back: it lifts the body into ray-cast headroom,
    drops it, and measures acceleration off the velocity.

G7 A PLAYER WALKS AROUND A BODY, NOT THROUGH IT
    `ragdoll.gd` excepts the player's RID from every physical bone deliberately,
    so a settled casualty could not separate a player the way a standing person
    does. Control: with the push off, the player ends 0.420 m INSIDE the body.

Run:
    python3 station/coldstart.py            # all gates
    python3 station/coldstart.py --g3       # reachability only, no engine
    python3 station/coldstart.py --g1       # cold start only
    python3 station/coldstart.py --g4       # the card check and its controls
    python3 station/coldstart.py --g5       # an incident puts a body down
    python3 station/coldstart.py --g6       # the field, at 18 ring angles
    python3 station/coldstart.py --g7       # walking around a body
    python3 station/coldstart.py --g3 --verbose
"""
import argparse
import glob
import json
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
        ("audio", "the station is audible (%s layers, ready in %s s%s)"
         % (d.get("audio_layers", "0"), d.get("audio_ready_s", "?"),
            "" if d.get("audio_why", "-") == "-"
            else ", " + d.get("audio_why", "").replace("_", " ")),
         num("audio_layers") > 0),
        ("budget", "cold in %.1f s (budget %.0f s)" % (wall, budget),
         wall <= budget),
    ]
    ok = True
    got = {}
    for key, name, good in checks:
        print("    %s %s" % ("ok  " if good else "FAIL", name))
        got[key] = bool(good)
        ok = ok and good
    if not ok:
        # PRINT THE ENGINE'S OWN ACCOUNT OF WHY, and do it without being asked.
        # This gate used to show five whitelisted prefixes and drop everything
        # else, so a red run said "FAIL the station is audible" and nothing at
        # all about the `ERROR: ambience: ...` line sitting three lines above it
        # in the output it had already captured. A reader then has a failure
        # with no cause and reasonably starts to disbelieve the gate -- which is
        # worse than no gate. `--verbose` existed and needing a second run to
        # find out what happened is exactly the friction that stops anyone
        # doing it.
        diag = [ln for ln in out.splitlines()
                if ln.startswith(("ERROR", "SCRIPT ERROR", "USER ERROR",
                                  "WARNING: ambience", "ambience:", "life:",
                                  "hud:", "dress: FAILED"))
                or " at: " in ln]
        if diag:
            print("  what the engine said, verbatim:")
            for ln in diag[:20]:
                print("    | " + ln[:160])
        else:
            print("  the engine printed no error -- rerun with --verbose for "
                  "its full output")
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


# WHO MAY STAND WHERE -- the subject and its four controls.
#
# `consequence.certain_check` has decided who may enter a place since P1-G2 and
# had NO RUNTIME CALLER: the six-rung ladder, the whole arrest chain and visa
# revocation were reachable from Python and a player could walk into the command
# deck of a military station unchallenged. That is this project's ELEVENTH
# built-but-unreachable defect, and every one of them shares a shape -- a static
# scan finds the reference and the thing never runs.
#
# So this does not scan. `main.gd --check-gate` walks a body across every place
# boundary the shipped build actually has and reports what the reader said. The
# controls are what make the readings mean anything: each removes or changes one
# input and the verdict has to move with it.
CHECK_CONTROLS = (
    (("--no-checks",), "the table is empty",
     lambda d: d is not None and d.get("gate") == "FAIL"
     and d.get("readings") == "0"),
    (("--tier=0",), "the card reads no_status",
     lambda d: d is not None and int(d.get("refuse", 0)) > 0
     and int(d.get("admit", 0)) == 0),
    (("--tier=5",), "the card reads accredited",
     lambda d: d is not None and int(d.get("admit", 0)) > 0
     and int(d.get("refuse", 0)) == 0),
    (("--no-hud",), "there is no reader",
     lambda d: d is None or d.get("gate") == "FAIL"),
)


def _parse_check(out):
    """The `CHECK gate=` line, or None.

    NOT `parse_verdict`. Its regex is `tag + " (.+)"`, which needs a space after
    the tag -- so `CHECK gate=` never matched, and `CHECK` alone matches the
    first `CHECK place=` line instead of the verdict. The gate reported "no
    verdict printed" on a run whose verdict was three lines up. The tag here is
    anchored to the start of a line and the pass word is read as the pass word.
    """
    m = re.search(r"^CHECK gate=(\S+)(.*)$", out, re.M)
    if not m:
        return None
    d = {"gate": m.group(1)}
    for tok in m.group(2).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d


def _check_run(extra, verbose=False, timeout=300):
    """Launch the shipped scene with `--check-gate` and parse its verdict."""
    godot = godot_binary()
    if godot is None:
        return None, ""
    cmd = [godot, "--headless", "--path", GODOT_DIR, "--",
           "--check-gate"] + list(extra)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    out = res.stdout + res.stderr
    if verbose:
        print(out)
    return _parse_check(out), out


def built_deck(*required):
    """`(ok, why)` -- can an engine gate run here at all?

    WHY THIS EXISTS, AND IT COST A CONTAINER RESTART TO NOTICE. Every gate below
    that launches the shipped scene needs a BUILT deck: `boot.json`, the deck
    GLBs it names, and -- for G5 -- the per-species ragdoll bodies. All of that
    lives under `station/generated/`, which is **gitignored**, so a fresh clone
    or a recycled container has none of it. CI never builds a real deck either.

    A gate that fails because its input is absent looks exactly like a gate that
    failed because the content is wrong, and this repository has been bitten by
    that reading twice at plan scale. So the two are DIFFERENT WORDS: a missing
    input is `SKIP -- <what is missing>` and does not claim a pass, and a real
    failure is `FAIL`. Neither is silent, because "a tool that silently degrades
    and exits 0 manufactures evidence".

    Rebuild with `python3 station/boot.py --bake` and, for G5,
    `python3 station/npc/ragdoll.py --emit station/generated/scene/npc`.
    """
    gen = os.path.join(ROOT, "station", "generated", "scene")
    boot = os.path.join(gen, "boot.json")
    rel = os.path.relpath(boot, ROOT)
    if not os.path.exists(boot):
        return False, "no %s -- run `python3 station/boot.py --bake`" % rel
    # AND THE FILE EXISTING IS NOT THE FILE BEING CURRENT. The first version of
    # this check tested only for the path, and a container recycle proved that
    # too weak within the hour: `boot.json` was present and PREDATED the keys
    # these gates read, so G4 would have run, found `table=0`, and reported a
    # content failure. That is the "a gate that reads a committed artefact must
    # be able to rebuild it" defect wearing a precondition as a disguise.
    #
    # Named per key rather than by a version stamp, because a stamp is a second
    # description of what the file contains and would go stale on its own.
    try:
        with open(boot) as f:
            d = json.load(f)
    except Exception as e:                                      # noqa: BLE001
        return False, "%s does not parse (%s) -- re-bake" % (rel, e)
    for key in required:
        if not d.get(key):
            return False, ("%s has no `%s` -- it predates the gate that reads "
                           "it. Run `python3 station/boot.py --bake`" % (rel, key))
    return True, ""


def purse_ledger():
    """`(ok, why)` -- is there an economy ledger with a purse in it?

    THE THIRD INPUT, AND I MISSED IT NAMING THE FIRST TWO. G4 compares the
    player's RUNG against what a place wants, and the rung comes off a purse in
    `station/generated/economy.json` -- which is gitignored like everything else
    under `generated/`. With no ledger `player.gd::has_purse()` is false, `tier`
    stays at its -99 sentinel, and every boundary correctly declines to read a
    card that does not exist: `readings=0 silent=6 tier=-99`, which reads as a
    dead check and is a missing file.

    Enumerating inputs one bug at a time is how a precondition becomes the thing
    it was written to prevent. This is the last of the three G4 touches; G5 adds
    the ragdoll bodies.
    """
    p = os.path.join(ROOT, "station", "generated", "economy.json")
    rel = os.path.relpath(p, ROOT)
    if not os.path.exists(p):
        return False, ("no %s -- run `python3 station/dockwork.py --loop "
                       "--days 14 --role lurker --seed downbelow --save %s`"
                       % (rel, rel))
    try:
        with open(p) as f:
            if not json.load(f).get("purses"):
                return False, "%s holds no purse -- re-run the ledger" % rel
    except Exception as e:                                      # noqa: BLE001
        return False, "%s does not parse (%s)" % (rel, e)
    return True, ""


def ragdoll_bodies():
    """`(ok, why)` -- are the per-species ragdoll bodies on disk? See above."""
    d = os.path.join(ROOT, "station", "generated", "scene", "npc")
    n = len(glob.glob(os.path.join(d, "*_ragdoll.json")))
    if n == 0:
        return False, ("no *_ragdoll.json in %s -- run `python3 "
                       "station/npc/ragdoll.py --emit station/generated/"
                       "scene/npc`" % os.path.relpath(d, ROOT))
    return True, ""


def g4(verbose=False):
    """G4 -- the card is read on the way in, in the shipped scene.

    WHAT IT DOES NOT CLAIM, stated rather than implied: the arrest chain behind
    a refusal (`consequence.arrest` -> brig -> fine -> release) is still Python.
    A refused player is TOLD they are refused and is not yet detained. P2 owns
    closing that. Reporting the reading is still the difference between a rule
    that exists and a rule a player meets.
    """
    godot = godot_binary()
    if godot is None:
        print("G4 FAIL -- no double-precision Godot binary found")
        return {"ok": False}
    for probe in (lambda: built_deck("checks"), purse_ledger):
        good, why = probe()
        if not good:
            print("G4 SKIP -- %s" % why)
            return {"ok": True, "skipped": why}
    print("G4 THE CARD IS READ ON THE WAY IN -- "
          "`godot --headless --path godot -- --check-gate`")
    # `parse_verdict` splits on the token after the tag, so `gate=` is consumed
    # by the tag itself and comes back under a key of its own.
    d, out = _check_run((), verbose=verbose)
    if d is None:
        print("  no CHECK verdict printed")
        for line in out.splitlines()[-20:]:
            print("    | " + line)
        print("  G4 FAIL -- the shipped scene printed no verdict")
        return {"ok": False}
    ok = d.get("gate") == "PASS"
    print("  %s crossed=%s of which checked=%s, readings=%s "
          "(admit %s, refuse %s), silent=%s wrong=%s, card=tier %s, "
          "table=%s places"
          % (d["gate"], d.get("crossed"), d.get("checked"), d.get("readings"),
             d.get("admit"), d.get("refuse"), d.get("silent"), d.get("wrong"),
             d.get("tier"), d.get("table")))
    for line in out.splitlines():
        if line.startswith("CHECK place="):
            print("    | " + line[6:])
    # WHOSE CARD THE SUBJECT IS HOLDING, AND WHETHER THAT COSTS A CONTROL.
    # The subject's rung comes from whatever purse `economy.json` happens to
    # hold, and that file is a REGENERATED side artefact -- rebuild it with
    # `--role lurker` and the player is a Downbelow no_status who is refused
    # everywhere, which makes the subject run byte-for-byte the `--tier=0`
    # control. The gate still discriminates, because `--tier=5` goes the other
    # way, but it is running on three controls rather than four and nothing
    # said so. A control that has silently become a duplicate of the subject is
    # the same defect as an assertion that cannot fail, one level out.
    subj_tier = str(d.get("tier", ""))
    dup = [f for f, _w, _p in CHECK_CONTROLS
           if any(a == "--tier=%s" % subj_tier.split("(")[0] for a in f)]
    if dup:
        print("  NOTE the subject holds tier %s, which is also control %s -- "
              % (subj_tier, " ".join(dup[0]))
              + "that control is a duplicate on this build and proves nothing "
                "the subject did not. Re-seed `economy.json` for a fourth.")
    print("  G4 CONTROLS -- each changes one input and must move the verdict")
    for flags, why, want in CHECK_CONTROLS:
        cd, _cout = _check_run(flags, verbose=verbose)
        good = bool(want(cd))
        said = ("no verdict" if cd is None else
                "%s readings=%s admit=%s refuse=%s"
                % (cd.get("gate"), cd.get("readings"), cd.get("admit"),
                   cd.get("refuse")))
        print("    %s %-12s %-28s -- %s"
              % ("ok  " if good else "FAIL", " ".join(flags), why, said))
        ok = ok and good
    print("  G4 %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok, "verdict": d}


def _walk_gate(verbose, tag, flag, cases, extra_probes=(), timeout=420,
               echo=()):
    """One engine gate over the shipped scene: run the subject and its controls.

    FACTORED OUT OF G5 RATHER THAN COPIED THREE TIMES. G6 and G7 have exactly
    G5's shape -- launch `main.gd` with one flag, parse one `<TAG> gate=` line,
    require the subject to PASS and each control to FAIL -- and this file's own
    history says what copying it would cost: `parse_verdict`'s regex was wrong
    for `CHECK gate=` and the copy would have carried the fix to one caller.

    `--no-coldstart` is not optional. Without it `_coldstart()` reaches its
    `get_tree().quit(0)` first and the gate never finishes.
    """
    godot = godot_binary()
    if godot is None:
        print("%s FAIL -- no double-precision Godot binary found" % tag)
        return {"ok": False}
    for probe in extra_probes:
        good, why = probe()
        if not good:
            print("%s SKIP -- %s" % (tag, why))
            return {"ok": True, "skipped": why}
    ok = True
    for flags, want, why in cases:
        cmd = [godot, "--headless", "--path", GODOT_DIR, "--",
               "--no-coldstart", flag] + list(flags)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=timeout)
        except subprocess.TimeoutExpired:
            print("  FAIL %-18s timed out" % " ".join(flags))
            ok = False
            continue
        out = res.stdout + res.stderr
        if verbose:
            print(out)
        m = re.search(r"^%s gate=(\w+)(.*)$" % tag, out, re.M)
        got = (m.group(1) == "PASS") if m else False
        good = got == want
        ok = ok and good
        said = m.group(0)[len(tag) + 6:].strip() if m else "no verdict"
        print("  %s %-18s %-46s -- %s"
              % ("ok  " if good else "FAIL",
                 (" ".join(flags) if flags else "(subject)"), why, said))
        if not flags and echo:
            for line in out.splitlines():
                if any(k in line for k in echo):
                    print("    | " + line.strip())
    print("  %s %s" % (tag, "PASS" if ok else "FAIL"))
    return {"ok": ok}


def g6(verbose=False):
    """G6 -- the field is right ALL THE WAY ROUND the ring, not just at spawn.

    THE DEFECT THIS CLOSES SHIPPED, and it is not the one that was written down.
    `STATE.md` §24.5 recorded (from the ragdoll agent) that `player.gd` returned
    `-Y` at 9.81 in `"deck"` mode and that `walk.gd` shipped that mode. Half of
    that was wrong: `main.gd::_configure_walk` line 305 sets `gravity_mode` to
    `"drum"`, so the DIRECTION was already radial. What actually shipped broken
    was the MAGNITUDE -- **nothing anywhere set `gravity_m_s2`**, so the export
    default of 9.81 stood, and a player fell **31.6% too fast at every angle on
    the ring**, on a deck that delivers 7.4523 m/s^2.

    The `-Y` constant is real and is a latent trap on the export default, which
    is why there are two controls rather than one: `--legacy-field` reproduces
    what shipped (radial, 9.81), `--legacy-deck` reproduces the default nobody
    was using (-Y at 9.81, which keeps the floor at only 5 of 18 angles and puts
    the body 179.98 deg from up -- standing on the ceiling -- at 90 deg).

    IT DOES NOT READ A VARIABLE BACK. It lifts the body into headroom it RAY
    CASTS for, drops it, and measures the acceleration off the velocity: a
    constant cannot fake `g = omega^2 r`.
    """
    return _walk_gate(verbose, "GRAVITY", "--gravity-gate", (
        ((), True, "the shipped build"),
        (("--legacy-field",), False,
         "radial at 9.81 -> +31.6% on g at every angle (what shipped)"),
        (("--legacy-deck",), False,
         "-Y at 9.81 -> 5 of 18 angles keep the floor"),
    ), extra_probes=(built_deck,), echo=("walk: gravity --", "GRAVITY gate:"))


def g7(verbose=False):
    """G7 -- a player walks AROUND a body on the deck, not through it.

    `ragdoll.gd` excepts the player's RID from every physical bone deliberately,
    so a settled body could not separate a player the way a standing person
    does -- you walked through the casualty. `npc.gd::push_off` now does it in
    the same loop, with the same across-the-floor-only rule and the same
    per-frame cap read off the body's own speed.
    """
    return _walk_gate(verbose, "CORPSE", "--corpse-gate", (
        ((), True, "the shipped build"),
        (("--no-ragdoll-push",), False,
         "the corpse is a hologram -> the player ends 0.42 m inside it"),
    ), extra_probes=(built_deck, ragdoll_bodies), echo=("CORPSE gate:",))


def g5(verbose=False):
    """G5 -- the station knocks somebody down and a player is there to see it.

    TWO FINISHED HALVES WITH NOTHING BETWEEN THEM, which is the shape this
    project keeps producing. `station/incident.py` has decided who collapses,
    where and at what hour since P1-G3 -- 380 INC-SICK a station-day, each with
    a NAMED resident as its subject -- and wrote them into a ledger nothing
    read. `station/npc/ragdoll.py` and `godot/scripts/ragdoll.gd` can drop a
    16-segment body at the deck's own gravity, and the only caller either had
    was `--ragdoll-gate`, a flag no player passes.

    So this asserts the JOIN: `boot.py` bakes the day's four ragdoll-bearing
    classes over the boot deck's own rooms, `main.gd::_fire_collapses` fires
    them as the clock passes their hour, and `npc.gd::promote_walker` takes the
    body out of the crowd -- a walker who was standing there, of the incident's
    species where the crowd has one.

    `--ragdoll-gate` (G6) proves the BODY. This proves the game asks for one.
    """
    godot = godot_binary()
    if godot is None:
        print("G5 FAIL -- no double-precision Godot binary found")
        return {"ok": False}
    # TWO INPUTS, TWO DIFFERENT MISSING-INPUT MESSAGES. See `built_deck`.
    for probe in (lambda: built_deck("collapses"), ragdoll_bodies):
        good, why = probe()
        if not good:
            print("G5 SKIP -- %s" % why)
            return {"ok": True, "skipped": why}
    print("G5 SOMEBODY COLLAPSES -- "
          "`godot --headless --path godot -- --collapse-gate`")
    ok = True
    for flags, want, why in (
            ((), True, "the shipped build"),
            (("--no-collapses",), False, "no schedule -> nobody falls"),
            (("--no-ragdoll",), False, "the director refuses -> nobody falls"),
    ):
        cmd = [godot, "--headless", "--path", GODOT_DIR, "--",
               "--collapse-gate"] + list(flags)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=420)
        except subprocess.TimeoutExpired:
            print("  FAIL %-16s timed out" % " ".join(flags))
            ok = False
            continue
        out = res.stdout + res.stderr
        if verbose:
            print(out)
        m = re.search(r"^COLLAPSE gate=(\w+)(.*)$", out, re.M)
        got = (m.group(1) == "PASS") if m else False
        good = got == want
        ok = ok and good
        said = m.group(0)[len("COLLAPSE gate="):].strip() if m else "no verdict"
        print("  %s %-16s %-38s -- %s"
              % ("ok  " if good else "FAIL",
                 (" ".join(flags) if flags else "(subject)"), why, said))
        if not flags:
            for line in out.splitlines():
                if line.startswith("collapse: INC") or "PROMOTED" in line:
                    print("    | " + line.strip())
    print("  G5 %s" % ("PASS" if ok else "FAIL"))
    return {"ok": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g1", action="store_true", help="cold start only")
    ap.add_argument("--g3", action="store_true", help="reachability only")
    ap.add_argument("--g4", action="store_true",
                    help="the card check on a place boundary only")
    ap.add_argument("--g5", action="store_true",
                    help="an incident puts a body on the deck")
    ap.add_argument("--g6", action="store_true",
                    help="the field is right all the way round the ring")
    ap.add_argument("--g7", action="store_true",
                    help="a player walks around a body, not through it")
    ap.add_argument("--controls", action="store_true",
                    help="only the negative controls on G1")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--budget-s", type=float, default=BOOT_BUDGET_S)
    a = ap.parse_args()
    run_all = not (a.g1 or a.g3 or a.g4 or a.g5 or a.g6 or a.g7
                   or a.controls)
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
    if a.g4 or run_all:
        print()
        if not g4(a.verbose).get("ok"):
            bad += 1
    if a.g5 or run_all:
        print()
        if not g5(a.verbose).get("ok"):
            bad += 1
    if a.g6 or run_all:
        print()
        if not g6(a.verbose).get("ok"):
            bad += 1
    if a.g7 or run_all:
        print()
        if not g7(a.verbose).get("ok"):
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
