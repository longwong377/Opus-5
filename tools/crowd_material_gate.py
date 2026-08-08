#!/usr/bin/env python3
"""Does every person in the station wear the wardrobe, or the glTF default?

WHY THIS IS NOT A RENDER GATE, and the reason is written down in CLAUDE.md
before this file existed. Session 4f bound 45 unmaterialled groups and the
before/after frame at the judge's own camera was **0.000% different**, because
a frame shows the groups that happen to be in shot and says nothing about the
group-to-material binding of the ones that are not. This asks the binding
question directly.

WHAT IT FOUND, session 4t -- instance ten of this project's signature defect,
finished machinery with no caller on the shipped path:

  * `station/npc/costume.py` derives a 53-material measured wardrobe and
    `materials.py` exports every one of it into `godot/materials/*.tres`.
  * `npc.gd::_index_library` names every crowd MultiMesh after its material key
    and carries a ten-line comment saying the name exists FOR THE BINDER.
  * `dress_scene.gd::bind` is the binder and NOTHING EVER CALLED IT ON THE
    CROWD. Its two shipped callers each pass a root that cannot contain one --
    `walk.gd` the level scene, `stream.gd` a cell's visual root -- while the
    buckets hang off the NPC node. And `_mesh_instances` collected only
    MeshInstance3D, so even a correct call would have bound nothing:
    MultiMeshInstance3D does not derive from MeshInstance3D.

  Measured in the packaged build at dist/Babylon5: `walk: 0 people wired of 0
  in the cast list`, `444 walkers`, `363 room occupant(s)`, `draws=297/2148`.
  Every human being in the station is drawn from `crowd_lod*.glb`, and those
  three files carry **0 glTF materials**. 807 people, all white.

THE TRAP THIS GATE EXISTS TO AVOID, and it caught the author first. Asking
"does the bucket have a material" reports **504 of 504 on an unfixed build**,
because Godot's glTF importer manufactures a default StandardMaterial3D per
surface. That default is `albedo_color = (1,1,1,1)` with no textures -- an
untextured white mannequin is not a mesh with no material, it is a mesh with
the WRONG material, and the only question worth asking is whether the material
is the one `material_rules` binds to the bucket's own name.

TWO LAYERS, AND THE FIRST ONE CANNOT SEE THE DEFECT. Say so rather than let a
green line imply otherwise:

  --data    the libraries and the rule table only. Asserts every crowd group
            name resolves to a rule, every rule's .tres is on disk, and the
            libraries carry no materials of their own so binding is mandatory.
            NECESSARY AND NOT SUFFICIENT: all of that PASSED throughout the
            six sessions the crowd shipped white.
  --engine  builds the buckets through `npc.gd`'s own code path in headless
            Godot and asks what material each one would actually render with.
            THIS is the layer that catches instance ten.

  --legacy  the negative control. Passes `--no-dress`, which is the flag that
            reproduces the pre-fix state exactly, and INVERTS the assertion:
            the run FAILS if the crowd comes back dressed. A gate whose failing
            case cannot be produced on demand is not a gate.

Exit 1 on a real failure. A layer that CANNOT RUN -- no Godot binary, no
crowd library (station/generated is gitignored), no import cache -- says so on
its own line and does not count as a pass or a failure, which is the rule
`tools/reach_gate.py` learned in 4s.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "godot")
INTERIOR = os.path.join(PROJECT, "scenes", "interior.tscn")
GEN = os.path.join(ROOT, "station", "generated", "scene")

# Where a Godot that can run this might be. The packaged runtime is not one:
# it has no project directory, only a .pck.
GODOT_CANDIDATES = (
    os.environ.get("GODOT", ""),
    "/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64",
    "/usr/local/bin/godot",
    "/usr/bin/godot",
)


# ---------------------------------------------------------------------------
# The library
# ---------------------------------------------------------------------------

def glb_json(path: str) -> dict:
    """The JSON chunk of a .glb. No dependency; the format is 20 bytes of header."""
    with open(path, "rb") as f:
        magic, _ver, _total = struct.unpack("<III", f.read(12))
        if magic != 0x46546C67:
            raise ValueError("%s is not a .glb" % path)
        clen, _ctype = struct.unpack("<II", f.read(8))
        return json.loads(f.read(clen).decode("utf-8"))


def crowd_libraries(where: str | None = None) -> list[str]:
    """Every shared body library on disk, newest scene dir first.

    NOT A HARD-CODED LIST. `deck.py` writes these beside the crowd placement
    list and `walk.gd::_derived_crowd_glbs` finds them by exactly this rule --
    a second list here would be a second description of where the crowd lives.
    """
    out = []
    for base in ([where] if where else
                 [os.path.join(GEN, "station"), os.path.join(GEN, "deck")]):
        if not os.path.isdir(base):
            continue
        for f in sorted(os.listdir(base)):
            if f.startswith("crowd_lod") and f.endswith(".glb"):
                out.append(os.path.join(base, f))
        if out:
            break
    return out


# ---------------------------------------------------------------------------
# The rule table
# ---------------------------------------------------------------------------

def material_rules(tscn: str = INTERIOR) -> tuple[dict, dict]:
    """(fragment -> ext id, ext id -> res:// path) out of the shipped scene.

    Read rather than restated. `station/materials.py --export` writes this
    block and asserts it against the library; a copy of 685 rules in this file
    would be correct on the day it was written.
    """
    text = open(tscn, encoding="utf-8").read()
    i = text.index("\nmaterial_rules = {")
    j = text.index("\n}", i)
    block = text[i:j + 2]
    rules = dict(re.findall(r'"([^"]+)"\s*:\s*ExtResource\("([^"]+)"\)', block))
    paths = {rid: p for p, rid in re.findall(
        r'\[ext_resource type="Material" path="([^"]+)" id="([^"]+)"\]', text)}
    return rules, paths


def resolve(name: str, rules: dict) -> str | None:
    """LONGEST SUBSTRING WINS -- `render_shot.gd::_material_for`'s own rule.

    Restating it is the one duplication this file accepts, and only because the
    alternative is starting an engine to answer a question about two text files.
    The --engine layer runs the real matcher, so the two are checked against
    each other on every full run.
    """
    best, best_len = None, -1
    for frag in rules:
        if frag in name and len(frag) > best_len:
            best, best_len = frag, len(frag)
    return best


# ---------------------------------------------------------------------------
# Layer 1 -- the data
# ---------------------------------------------------------------------------

def data_layer(libs: list[str]) -> tuple[bool, list[str]]:
    lines, ok = [], True
    rules, paths = material_rules()
    lines.append("rule table: %d fragments, %d distinct materials"
                 % (len(rules), len(set(rules.values()))))
    for lib in libs:
        js = glb_json(lib)
        n_mat = len(js.get("materials", []))
        carried = sum(1 for m in js.get("meshes", [])
                      for p in m.get("primitives", [])
                      if p.get("material") is not None)
        names = [n["name"] for n in js.get("nodes", []) if "mesh" in n]
        unresolved = [n for n in names if resolve(n, rules) is None]
        wanted = {rules[resolve(n, rules)] for n in names if resolve(n, rules)}
        absent = sorted(paths[w].replace("res://", "") for w in wanted
                        if w in paths and not os.path.exists(
                            os.path.join(PROJECT, paths[w].replace("res://", ""))))
        base = os.path.basename(lib)
        lines.append("%s: %d body meshes, %d glTF material(s), %d primitive(s) "
                     "carrying one -> the engine default covers every surface"
                     % (base, len(names), n_mat, carried))
        lines.append("   %d name(s) match NO rule, %d wanted material(s), "
                     "%d file(s) absent" % (len(unresolved), len(wanted), len(absent)))
        if unresolved:
            ok = False
            lines.append("   FAIL unmatched: %s" % ", ".join(sorted(unresolved)[:6]))
        if absent:
            ok = False
            lines.append("   FAIL absent: %s" % ", ".join(absent[:6]))
    lines.append("NOTE this layer PASSED throughout the six sessions the crowd "
                 "shipped white. It proves the wardrobe is reachable, never "
                 "that anything reached for it -- that is --engine.")
    return ok, lines


# ---------------------------------------------------------------------------
# Layer 2 -- the engine
# ---------------------------------------------------------------------------

PROBE = r'''
extends SceneTree
## Written by tools/crowd_material_gate.py. Not committed, not in the project.

func _initialize() -> void:
	var libs: Array = []
	for a in OS.get_cmdline_user_args():
		if String(a).ends_with(".glb"):
			libs.append(String(a))
	var loaded: Array = []
	var species := {}
	var lods := {}
	for p in libs:
		if not FileAccess.file_exists(p):
			continue
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		if doc.append_from_file(p, st) != OK:
			continue
		var n := doc.generate_scene(st)
		loaded.append(n)
		for m in _meshes(n):
			var nm := String(m.name)
			var cut := nm.find("_npc_")
			if cut <= 0 or not nm.begins_with("crowd_"):
				continue
			var bits := nm.substr(6, cut - 6).split("_")
			if bits.size() < 3:
				continue
			lods[int(bits[bits.size() - 2])] = true
			species["_".join(Array(bits).slice(0, bits.size() - 2))] = true
	if loaded.is_empty():
		print("CROWDMAT cannot_run=no_library_loaded")
		quit(0)
		return

	var ls := lods.keys()
	ls.sort()
	var ladder := []
	for l in ls:
		ladder.append("1e9:%d" % int(l))
	var rows := []
	for sp in species:
		for l in ls:
			rows.append({"species": sp, "lod": int(l), "phase": 0,
				"x": 0.0, "y": 0.0, "z": 0.0, "cycle_s": 1.0})

	var people := Node3D.new()
	people.name = "People"
	people.set_script(load("res://scripts/npc.gd"))
	root.add_child(people)
	people.call("set_crowd_ladder", ",".join(ladder))
	people.call("prepare_crowd", loaded, rows)

	# THE SHIPPING MATCHER, not a copy of it -- interior.tscn's own
	# `_material_for`. If this and the gate's Python disagree the run says so.
	var ps := load("res://scenes/interior.tscn") as PackedScene
	if ps == null:
		print("CROWDMAT cannot_run=no_interior_scene")
		quit(0)
		return
	var table = ps.instantiate()
	var total := 0
	var wardrobe := 0
	var wrong := 0
	var naked := 0
	var no_rule := 0
	var sample: Array = []
	for c in people.get_children():
		if not (c is MultiMeshInstance3D):
			continue
		var mm := c as MultiMeshInstance3D
		if mm.multimesh == null or mm.multimesh.mesh == null:
			continue
		total += 1
		# THE ORDER THE RENDERER ASKS IN: override first, then the surface.
		var got: Material = mm.material_override
		if got == null:
			for i in range(mm.multimesh.mesh.get_surface_count()):
				var s: Material = mm.multimesh.mesh.surface_get_material(i)
				if s != null:
					got = s
					break
		var want: Material = table._material_for(String(mm.name))
		if want == null:
			# No rule, or a rule whose ExtResource did not load. Not the
			# defect this gate is for -- reported separately so a missing
			# import cache cannot masquerade as a white crowd.
			no_rule += 1
		elif got == null:
			naked += 1
		elif got == want:
			wardrobe += 1
		else:
			wrong += 1
			if sample.size() < 4:
				var d := "%s path='%s'" % [got.get_class(), got.resource_path]
				if got is StandardMaterial3D:
					var sm := got as StandardMaterial3D
					d += " albedo=%s tex=%s" % [str(sm.albedo_color),
						("none" if sm.albedo_texture == null else "yes")]
				sample.append("%s -> %s" % [String(mm.name), d])
	print("CROWDMAT buckets=%d wardrobe=%d wrong=%d naked=%d no_rule=%d"
		% [total, wardrobe, wrong, naked, no_rule])
	for s in sample:
		print("CROWDMATDETAIL %s" % s)
	# THE COUNTERS MAY NOT EXIST, and that is the case this gate is FOR: an
	# npc.gd with no `dress_crowd` has no counters either. `int(null)` is
	# `Invalid call. Nonexistent 'int' constructor.`, which aborts _initialize
	# BEFORE quit(0) and leaves a headless SceneTree spinning forever -- so the
	# unguarded version hung on exactly the input it was written to catch, and
	# the gate reported CANNOT RUN instead of FAIL. Measured, session 4t.
	var said := "absent (npc.gd has no dress_crowd counters)"
	var b = people.get("crowd_mm_bound")
	if b != null:
		said = "npc_reports=%d/%d why=%s" % [int(b),
			int(people.get("crowd_mm_total")),
			String(people.get("crowd_dress_why"))]
	print("CROWDMATSAY %s" % said)
	quit(0)


func _meshes(n: Node, out: Array = []) -> Array:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		out.append(n)
	for c in n.get_children():
		_meshes(c, out)
	return out
'''


def find_godot() -> str | None:
    for c in GODOT_CANDIDATES:
        if c and os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return None


def engine_layer(libs: list[str], legacy: bool,
                 timeout_s: int = 1800) -> tuple[str, list[str]]:
    """('pass'|'fail'|'cannot_run', report lines)."""
    lines = []
    godot = find_godot()
    if godot is None:
        return "cannot_run", ["engine: CANNOT RUN -- no Godot binary "
                              "(set $GODOT); the data layer above still ran"]
    if not os.path.isdir(os.path.join(PROJECT, ".godot")):
        # Materials are ext_resources with textures. Without the import cache
        # every one resolves to null, `want` is null everywhere, and the run
        # would report no_rule=N -- true, and nothing to do with the crowd.
        return "cannot_run", ["engine: CANNOT RUN -- godot/.godot is absent "
                              "(it is gitignored). Let Godot import once, or "
                              "run `station/materials.py --export` then import."]
    with tempfile.TemporaryDirectory() as td:
        probe = os.path.join(td, "crowd_material_probe.gd")
        with open(probe, "w", encoding="utf-8") as f:
            f.write(PROBE.lstrip("\n"))
        # `--quit-after 1` IS A BACKSTOP, NOT A PREFERENCE. A GDScript error
        # inside `_initialize` does not stop the main loop, so a probe that
        # dies one line before `quit(0)` leaves a headless Godot spinning until
        # this timeout -- which turns a FAIL into a CANNOT RUN, silently, on
        # the very input the gate exists for. One frame is plenty: all the work
        # is in `_initialize` and the null renderer draws nothing.
        cmd = [godot, "--headless", "--quit-after", "1",
               "--path", PROJECT, "--script", probe, "--"]
        cmd += libs
        if legacy:
            cmd.append("--no-dress")
        lines.append("engine: %s" % " ".join(
            [os.path.basename(godot), "--headless", "--quit-after", "1",
             "--path", "godot", "--script", "<tmp>", "--"]
            + [os.path.basename(x) for x in libs]
            + (["--no-dress"] if legacy else [])))
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout_s)
            out = p.stdout + p.stderr
        except subprocess.TimeoutExpired as e:
            # A TIMEOUT MUST NOT THROW AWAY EVIDENCE ALREADY PRINTED. The
            # finding is on stdout long before the process ends; discarding it
            # is how the first version of this file reported CANNOT RUN on a
            # run that had already measured 504 white bodies.
            out = ((e.stdout or b"").decode("utf-8", "replace")
                   + (e.stderr or b"").decode("utf-8", "replace")
                   if isinstance(e.stdout, (bytes, bytearray))
                   else (e.stdout or "") + (e.stderr or ""))
            lines.append("engine: the probe TIMED OUT after %d s -- reading "
                         "whatever it had already printed" % timeout_s)

    # GREP THE TOOL'S OWN REPORT OF WHAT IT DID. CLAUDE.md, session 4e: a tool
    # that can silently substitute a lesser mode must be made to say which one
    # it used, and the caller must check. Godot --headless is the null renderer
    # by design here (no frame is wanted), but a probe that crashed before
    # printing would otherwise read as a clean run with no findings.
    m = re.search(r"^CROWDMAT (.*)$", out, re.M)
    if m is None:
        return "cannot_run", lines + [
            "engine: CANNOT RUN -- the probe printed no CROWDMAT line; "
            "last 5 lines of its output:",
            *["   " + l for l in out.strip().splitlines()[-5:]]]
    body = m.group(1)
    if body.startswith("cannot_run="):
        return "cannot_run", lines + ["engine: CANNOT RUN -- " + body]
    got = dict(kv.split("=") for kv in body.split())
    n = {k: int(v) for k, v in got.items()}
    for extra in re.findall(r"^CROWDMATDETAIL (.*)$", out, re.M):
        lines.append("   " + extra)
    say = re.search(r"^CROWDMATSAY (.*)$", out, re.M)
    lines.append("   buckets=%(buckets)d wardrobe=%(wardrobe)d "
                 "wrong=%(wrong)d naked=%(naked)d no_rule=%(no_rule)d" % n)
    if say:
        lines.append("   npc.gd says: " + say.group(1))

    if n["no_rule"] and n["no_rule"] == n["buckets"]:
        return "cannot_run", lines + [
            "engine: CANNOT RUN -- every rule resolved to null, which is a "
            "material library that did not load rather than a naked crowd"]
    if legacy:
        # INVERTED. The control has to fire.
        if n["wardrobe"] == 0 and n["wrong"] + n["naked"] == n["buckets"]:
            lines.append("engine: CONTROL FIRED -- with --no-dress all %d "
                         "bucket(s) render on the glTF default. This is the "
                         "state the shipped build was in." % n["buckets"])
            return "pass", lines
        lines.append("engine: CONTROL DID NOT FIRE -- --no-dress left %d "
                     "bucket(s) dressed, so the gate cannot fail and proves "
                     "nothing." % n["wardrobe"])
        return "fail", lines
    if n["wrong"] or n["naked"] or n["wardrobe"] != n["buckets"] - n["no_rule"]:
        lines.append("engine: FAIL -- %d of %d crowd bucket(s) do NOT render "
                     "with the material material_rules binds to their name."
                     % (n["wrong"] + n["naked"], n["buckets"]))
        return "fail", lines
    lines.append("engine: PASS -- %d of %d crowd bucket(s) render with the "
                 "wardrobe material bound to their own group name."
                 % (n["wardrobe"], n["buckets"]))
    return "pass", lines


# ---------------------------------------------------------------------------
# Layer 0 -- the tripwire, and its ceiling
# ---------------------------------------------------------------------------

def wiring_layer() -> tuple[bool, list[str]]:
    """Is there a caller, and can the callee see a MultiMeshInstance3D?

    A STATIC SCAN, WITH THE CEILING CLAUDE.md ALREADY NAMED: it can tell you a
    caller exists and never that the caller runs. `budget.occlusion_chain`
    reported applied=True while the shipped build loaded nothing. Kept anyway
    because it costs milliseconds and fails on the exact shape of instance ten
    -- a binder with no call site -- in a checkout with no engine and no
    generated data, which is where CI usually stands.
    """
    lines, ok = [], True
    npc = open(os.path.join(PROJECT, "scripts", "npc.gd"), encoding="utf-8").read()
    dress = open(os.path.join(PROJECT, "scripts", "dress_scene.gd"),
                 encoding="utf-8").read()
    body = re.sub(r"(?m)^\s*#.*$", "", npc)
    calls = len(re.findall(r"^\s*dress_crowd\(\)", body, re.M))
    if calls == 0:
        ok = False
        lines.append("wiring: FAIL -- npc.gd never calls dress_crowd(); the "
                     "buckets are named for a binder nothing invokes")
    else:
        lines.append("wiring: npc.gd calls dress_crowd() from %d site(s)" % calls)
    if "MultiMeshInstance3D" not in dress:
        ok = False
        lines.append("wiring: FAIL -- dress_scene.gd cannot see a "
                     "MultiMeshInstance3D, so a call to it would bind nothing")
    else:
        lines.append("wiring: dress_scene.gd collects MultiMeshInstance3D")
    lines.append("NOTE a static scan cannot tell you the caller RUNS. "
                 "--engine is the layer that can.")
    return ok, lines


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", action="store_true", help="library/rule layer only")
    ap.add_argument("--engine", action="store_true", help="headless Godot layer only")
    ap.add_argument("--wiring", action="store_true", help="static tripwire only")
    ap.add_argument("--legacy", action="store_true",
                    help="negative control: run the engine layer with "
                         "--no-dress and require the crowd to come back WHITE")
    ap.add_argument("--libs", default="",
                    help="comma-separated crowd_lod*.glb; default is whatever "
                         "deck.py wrote under station/generated/scene")
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args(argv)
    pick = a.data or a.engine or a.wiring
    run_data = a.data or not pick
    run_engine = a.engine or a.legacy or not pick
    run_wiring = a.wiring or not pick

    libs = ([x for x in a.libs.split(",") if x] if a.libs
            else crowd_libraries())
    print("crowd material gate -- %d shared body librar%s"
          % (len(libs), "y" if len(libs) == 1 else "ies"))
    for l in libs:
        print("   " + os.path.relpath(l, ROOT))

    bad, cannot = [], []
    if run_wiring:
        ok, lines = wiring_layer()
        print("\n".join(lines))
        if not ok:
            bad.append("wiring")
    if run_data:
        if not libs:
            cannot.append("data")
            print("data: CANNOT RUN -- no crowd_lod*.glb under "
                  "station/generated/scene (it is gitignored; run deck.py)")
        else:
            ok, lines = data_layer(libs)
            print("\n".join(lines))
            if not ok:
                bad.append("data")
    if run_engine:
        if not libs:
            cannot.append("engine")
            print("engine: CANNOT RUN -- no crowd library to build from")
        else:
            state, lines = engine_layer(libs, a.legacy, a.timeout)
            print("\n".join(lines))
            if state == "fail":
                bad.append("engine")
            elif state == "cannot_run":
                cannot.append("engine")

    if cannot:
        print("CANNOT RUN: %s -- neither passed nor failed" % ", ".join(cannot))
    if bad:
        print("FAILED: %s" % ", ".join(bad))
        return 1
    print("OK%s" % ("" if not cannot else " (for the layers that could run)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
