#!/usr/bin/env python3
"""Render a named set of engine frames for an AAA review round, and prove the
renderer that produced each one.

WHY THIS EXISTS, and it is not "a convenience wrapper".

Session 4e judged ten frames that came out of **OpenGL 3 Compatibility** rather
than Forward+, because the container had no Vulkan ICD and Godot substitutes a
lesser renderer, prints the warning inside several hundred lines of ALSA noise,
and exits 0 with a PNG. Compatibility has no SSAO, glow, SSIL, volumetric fog
or colour grading, so every craft conclusion drawn from those frames was drawn
from a picture the engine does not make. `tools/render_godot.sh` now checks the
ICD before and greps its own log after -- that fix is upstream of this file and
this file does not repeat it.

What this file adds is the **third end**: the reviewer's own record. A review is
a document that outlives the container it was written in, and "I checked the log"
is exactly the kind of claim that cannot be re-checked six sessions later. So
every frame this driver produces is written down beside

  * the exact command that made it,
  * the `renderer:` line the engine printed,
  * the mesh-instance count and the triangle count,
  * every group the engine reported on the FALLBACK material,

into `docs/judge-4e-frames.json`. A frame with no row is not evidence. A row
whose `renderer` does not contain "Forward+" is refused: the PNG is deleted, for
the same reason render_godot.sh deletes it -- an artefact that exists is an
artefact somebody will score.

THE FALLBACK COLUMN IS THE POINT OF THE OTHER HALF. `tools/export_scene.py`'s
own header says it "assert[s] that every group it emits has a rule, so nothing
lands on the fallback by accident". Read the code: `unmatched_groups()` is
applied to the DRUM shot and *reported* for the exterior, and is not reached at
all by the `deck` shot -- the one that shot's own docstring calls "the build".
So the engine's `fallback material used by N group(s)` line is the only place
that failure surfaces for the walkable station, and it surfaces in a log nobody
keeps. It is kept here.

Read-only with respect to everything but its own outputs: it shells out to
tools/render_godot.sh and writes docs/judge-4e-*.png and docs/judge-4e-frames.json.

Usage:
    python3 tools/judge_sweep.py --list
    python3 tools/judge_sweep.py --only corridor_normal,zocalo_normal
    python3 tools/judge_sweep.py                 # the whole sweep
    python3 tools/judge_sweep.py --report        # re-print the recorded table
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "judge-4e-frames.json")

# THE HALF-DISTANCE LENS, DERIVED RATHER THAN CHOSEN.
#
# The rubric says to judge "at three distances: the distance the player normally
# sees it from, half that, and the distance at which it is one pixel of
# silhouette", and CLAUDE.md records that only the first was ever rendered --
# which is how 118 locations of blockout passed three layers.
#
# Halving the DISTANCE doubles pixels-per-metre on the subject. So does halving
# the tangent of the half field of view, and on a shot whose camera is pinned to
# a standing eye on a corridor floor it is the only one of the two that is
# available: the deck camera stands on the ring at the player's own radius and
# cannot be walked into a wall. From the shipped player lens,
#
#     fov_half = 2 * atan(tan(46/2 deg) / 2) = 23.99 deg
#
# Stated as a limitation, not hidden: a narrower lens resolves the same detail a
# closer camera would and does NOT reproduce the parallax or the occlusion of
# actually walking up to the surface. Where the shot CAN be moved -- an interior
# room, the drum, the exterior orbit -- the frames below move it, and the lens
# trick is used only where the camera is pinned.
FOV_NORMAL = 46.0
FOV_HALF = 24.0

# --------------------------------------------------------------------------
# The sample. Chosen, and the reason recorded beside each row, because a review
# that does not say what it did not look at is a review that claims 128.
#
#   AREA     the archetypes that carry the most floor area a player stands on
#   AUTH1    a location the gazetteer holds an authority-1 frame of -- the ones
#            a viewer can catch us on -- taken in the gazetteer's own rank order
#   PRIOR    a subject an earlier round in docs/aaa-scorecard.json scored, so
#            this round is a before/after and not a fresh opinion
# --------------------------------------------------------------------------
SHOTS = {
    # ---- the corridor: 77% of a ring deck's floor (docs/judge-3w.md) -------
    "corridor_normal": (
        "AREA PRIOR walkable_deck",
        "--shot deck --deck blue/0/0 --at docking_bays --res 1280x720"),
    "corridor_half": (
        "AREA PRIOR walkable_deck -- half distance, by lens",
        f"--shot deck --deck blue/0/0 --at docking_bays --fov {FOV_HALF} "
        "--res 1280x720"),
    "corridor_wall": (
        "AREA -- the wall at arm's length: the rubric's 1 m material test",
        "--shot deck --deck blue/0/0 --at docking_bays --face-offset 0.4,3 "
        "--res 1280x720"),
    "corridor_door": (
        "AREA -- the doorway, the place a player looks closest (session 3x)",
        "--shot deck --deck blue/0/0 --at docking_bays --at-offset 6,0 "
        "--face docking_bays --res 1280x720"),

    # THE CONTROL. Identical to corridor_normal but for the shadow ration.
    # It comes back BYTE-IDENTICAL, and session 4e's lesson is that a
    # byte-identical A/B must be EXPLAINED and not recorded: here the reason is
    # that all 18 shadow-castable lights on this deck are inside rooms and none
    # of the corridor's 822 downlights or 707 soft fills is flagged at all, so
    # no value of --shadow-lights can change this frame. The positive control
    # that fires is the same 0-vs-24 A/B inside `docking_bays`, which moves
    # 15.45% of pixels; it is not in this table because it renders at 960x540
    # to /tmp and is a diff, not a frame to score.
    "corridor_shadow24": (
        "CONTROL for corridor_normal -- 2 vs 18 shadow casters",
        "--shot deck --deck blue/0/0 --at docking_bays --shadow-lights 24 "
        "--res 1280x720"),

    # ---- the generic procedural room: 58% of the station (CLAUDE.md) ------
    "generic_normal": (
        "AREA PRIOR generated_rooms",
        "--shot interior --room hydroponics --res 1280x720"),
    "generic_half": (
        "AREA PRIOR generated_rooms -- half distance, by lens",
        f"--shot interior --room hydroponics --fov {FOV_HALF} --res 1280x720"),
    "industrial_normal": (
        "AREA -- the industrial archetype, EXPOSURE_FRAMES' own member",
        "--shot interior --room fabrication --res 1280x720"),
    "commerce_normal": (
        "AREA -- the commerce archetype, EXPOSURE_FRAMES' own member",
        "--shot interior --room business_center --res 1280x720"),

    # ---- authority-1, in the gazetteer's ranked order (LOCATIONS.md 19) ---
    "zocalo_normal": (
        "AUTH1 rank 1 PRIOR zocalo_interior",
        "--shot interior --room zocalo --res 1280x720"),
    "zocalo_half": (
        "AUTH1 rank 1 PRIOR zocalo_interior -- half distance, by lens",
        f"--shot interior --room zocalo --fov {FOV_HALF} --res 1280x720"),
    "customs_normal": (
        "AUTH1 rank 2 -- the player's first room",
        "--shot interior --room customs_north --res 1280x720"),
    "dockingbay_normal": (
        "AUTH1 rank 3",
        "--shot interior --room docking_bays --res 1280x720"),
    "cnc_normal": (
        "AUTH1 rank 4 -- the most-seen room on the show",
        "--shot interior --room cnc --res 1280x720"),
    "cnc_half": (
        "AUTH1 rank 4 -- half distance, by lens",
        f"--shot interior --room cnc --fov {FOV_HALF} --res 1280x720"),
    "council_normal": (
        "AUTH1 rank 6",
        "--shot interior --room council_chamber --res 1280x720"),

    # ---- the drum: the worst craft score on the board --------------------
    "drum_normal": (
        "PRIOR garden_townscape craft 1 -- the settlement at walking distance",
        "--shot drum --stand 20,4700 --look 20,6300 --res 1280x720"),
    "drum_half": (
        "PRIOR garden_townscape craft 1 -- half distance, by lens",
        f"--shot drum --stand 20,4700 --look 20,6300 --fov {FOV_HALF} "
        "--res 1280x720"),

    # ---- the exterior: what the player sees on approach ------------------
    "exterior_normal": (
        "PRIOR hull_exterior / exterior_components",
        "--shot exterior --orbit 9200,18,214 --res 1280x720"),
    "exterior_half": (
        "PRIOR hull_exterior -- half the orbit distance, by moving the camera",
        "--shot exterior --orbit 4600,18,214 --res 1280x720"),
    "exterior_onepixel": (
        "PRIOR hull_exterior -- the silhouette distance, by moving the camera",
        "--shot exterior --orbit 60000,18,214 --res 1280x720"),
}

RENDERER_RE = re.compile(r"^renderer:\s*(.+)$", re.M)
FALLBACK_RE = re.compile(r"fallback material used by \d+ group\(s\):\s*(.+)$", re.M)
INSTANCES_RE = re.compile(r"(\d+) mesh instances over (\d+) files")
TRIS_RE = re.compile(r'"triangles":\s*(\d+)')
LIGHTS_RE = re.compile(r'"lights":\s*(\d+)')
CAMERA_RE = re.compile(r"^render_shot: camera at (.+)$", re.M)


def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            return json.load(f)
    return {"round": "judge-4e", "frames": {}}


def save_ledger(led):
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1, sort_keys=True)
        f.write("\n")


def run_one(name, why, flags, keep_log=None):
    png = os.path.join(ROOT, "docs", f"judge-4e-{name.replace('_', '-')}.png")
    cmd = ["bash", os.path.join(ROOT, "tools", "render_godot.sh")] + \
        shlex.split(flags) + ["--out", png]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    log = p.stdout + p.stderr
    if keep_log:
        with open(keep_log, "a") as f:
            f.write(f"\n===== {name} =====\n{log}")

    m = RENDERER_RE.search(log)
    renderer = m.group(1).strip() if m else ""
    row = {
        "why": why,
        "command": "tools/render_godot.sh " + flags + " --out " + \
            os.path.relpath(png, ROOT),
        "renderer": renderer,
        "exit": p.returncode,
        "seconds": round(time.time() - t0, 1),
        "png": os.path.relpath(png, ROOT),
    }
    mi = INSTANCES_RE.search(log)
    if mi:
        row["mesh_instances"] = int(mi.group(1))
    mt = TRIS_RE.search(log)
    if mt:
        row["triangles"] = int(mt.group(1))
    ml = LIGHTS_RE.search(log)
    if ml:
        row["lights"] = int(ml.group(1))
    mc = CAMERA_RE.search(log)
    if mc:
        row["camera"] = mc.group(1).strip()
    fb = FALLBACK_RE.search(log)
    row["fallback_groups"] = ([g.strip() for g in fb.group(1).split(",")]
                              if fb else [])

    # THE REFUSAL. A frame whose renderer line does not say Forward+ is not a
    # frame of this engine, and leaving the PNG on disk is how session 4e's ten
    # Compatibility frames got scored. Delete it and say so.
    if "Forward+" not in renderer:
        row["REFUSED"] = ("no 'Forward+' in the renderer line -- "
                          "this is the OpenGL fallback or a failed run")
        if os.path.exists(png):
            os.unlink(png)
    elif p.returncode != 0 or not os.path.exists(png):
        row["REFUSED"] = f"render exited {p.returncode} or wrote no PNG"
    return name, row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated shot names")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--log", default=None, help="append every engine log here")
    args = ap.parse_args()

    if args.list:
        for n, (why, flags) in SHOTS.items():
            print(f"{n:22s} {why}\n{'':22s} {flags}")
        return 0

    led = load_ledger()
    if args.report:
        bad = 0
        for n, r in sorted(led["frames"].items()):
            flag = "REFUSED" if "REFUSED" in r else "ok"
            bad += "REFUSED" in r
            print(f"{n:22s} {flag:8s} {r['renderer'][:46]:46s} "
                  f"fallback={len(r.get('fallback_groups', []))}")
        print(f"{len(led['frames'])} frames, {bad} refused")
        return 1 if bad else 0

    names = args.only.split(",") if args.only else list(SHOTS)
    for n in names:
        if n not in SHOTS:
            print(f"unknown shot {n}", file=sys.stderr)
            return 2
        why, flags = SHOTS[n]
        name, row = run_one(n, why, flags, keep_log=args.log)
        led["frames"][name] = row
        save_ledger(led)
        state = row.get("REFUSED", "ok")
        print(f"{name:22s} {row['seconds']:6.1f}s  {state}  "
              f"fallback={row['fallback_groups']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
