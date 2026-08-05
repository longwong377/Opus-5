#!/usr/bin/env python3
"""Does the shipped path actually reach the thing that was built?

THE DEFECT THIS GATES HAS NOW HAPPENED SIX TIMES, which is why it is a tool and
not a seventh patch:

  L3's room leg        finished, tested, and `walkable.py` never called it
  `stream.gd`          streamed cells and moved nobody
  the circulation graph  nothing but its own selftest ever saw it
  `dialogue.gd`        913 lines whose node had NEVER been built on any path,
                       because `_wire_dialogue` ran above `_spawn_player()`
                       behind an `if _player == null: return`
  the Starfury         every part built and tested -- flight model, airframe,
                       docking physics, 1,000 lines of `starfury.gd` -- and no
                       CI step rebuilds the data it reads, so the mode works
                       here and dies on a fresh clone
  `--mode=transit`     `main.gd` read `transit/transit_manifest.json`, a name
                       that appeared EXACTLY ONCE in the repository: on the line
                       reading it. Nothing wrote it. `--build` writes
                       `transit/lift.json`. The mode could never have worked and
                       its error message named a command that would not fix it

Every one of those passed every gate in the repository at the time. They had to:
every gate here measures A PART AGAINST A STANDARD, and a part with no caller is
a part that still meets its standard. CLAUDE.md's own rule is that a fix applied
to an instance and not to the rule is a fix that will be needed again -- so this
asks the rule's question instead. The sixth was found by this tool on its first
run, which is the argument for it.

AND IT CORRECTS ITS AUTHOR. Before this tool existed I checked the Starfury data
with `ls station/generated/starfury/`, got "No such file or directory", and wrote
up "the three files do not exist" as a finding. They exist, at
`station/generated/scene/starfury/` -- `main.gd` joins them onto a base of
`station/generated/scene`, which an `ls` of the wrong directory cannot see and a
scan that follows the actual read can. The real Starfury defect is the weaker,
truer one now in the table above.

THE TWO QUESTIONS
-----------------

  --data     Every `station/generated/...` path an engine script reads: does the
             file exist, and is its PRODUCER run by CI? A path that exists on a
             developer's disk because they once ran the builder by hand is
             exactly the Starfury case -- it dies on a fresh clone.

  --callers  Every module under `station/` that has a test or a selftest: does
             anything else in the repository import it -- by `import`, by
             attribute, or by `__import__("name")`? A tested module with no
             importer is a part nobody assembled.

Neither question can be answered by a gate that scores a part, and neither needs
a build, a render or a GPU -- this is file scanning, seconds, and safe to run
while agents are working.

WHAT THIS DELIBERATELY DOES NOT DO. It does not try to prove a code path is
reached at runtime; that needs execution and `coldstart.py` is where this project
does it. It proves the two things a static scan genuinely can: the data is there
and reproducible, and the module is spoken to. Between them they would have
caught four of the five above at the moment they landed.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GODOT = os.path.join(ROOT, "godot")
STATION = os.path.join(ROOT, "station")
GENERATED = os.path.join(STATION, "generated")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "validate.yml")

# A generated path is written in the .gd files three ways and the third is the
# one that hides:
#
#   "generated/navgraph.json"                     a whole literal
#   gen.path_join("starfury/starfury.glb")        a fragment joined to a base
#   d + "_cells.json"                             a suffix built at run time
#
# The third form cannot be resolved statically to a filename and is reported as
# a DYNAMIC row rather than silently dropped -- an unresolvable read is a thing
# a reader should see, not a thing a scanner should decide is fine. This is the
# same principle as `spec_registry.py` refusing to emit around an ambiguity.
_LITERAL = re.compile(r'"([^"\n]*generated/[^"\n]+)"')
_JOINED = re.compile(r'path_join\(\s*"([^"\n]+)"\s*\)')
_SUFFIX = re.compile(r'\+\s*"(_[a-z_]+\.(?:json|glb|tscn|obj))"')

# A MODULE NAME INSIDE A STRING IS INVISIBLE TO AN IMPORT REGEX, and this tool
# fell for exactly the trap CLAUDE.md already records from session 4f (where
# `materials._scan_generator_groups` missed 45 mesh groups named by f-string).
# `bespoke.BESPOKE_GEOMETRY` dispatches with `__import__("shuttle").room(...)`,
# so the first cut of `--callers` reported `shuttle`, `concourse`, `aperture`
# and `observation` as having no importer -- four false orphans out of ten, in a
# list whose whole value is being trustworthy. A gate that cries wolf about
# unreachable code is worse than no gate, because the real ones stop being read.
#
# `%s` is filled with the escaped module name by the caller.
_DYNAMIC_IMPORT = r'(?:__import__|import_module)\(\s*"%s"\s*\)'

# The engine's `generated/` is `station/generated/`, reached through a base the
# scripts build themselves; every literal is relative to it.
_PREFIX = "generated/"


def _gd_files():
    out = []
    for base, _dirs, names in os.walk(GODOT):
        for n in sorted(names):
            if n.endswith((".gd", ".tscn")):
                out.append(os.path.join(base, n))
    return sorted(out)


def _rel(path):
    return os.path.relpath(path, ROOT)


def _strip(p):
    """Reduce a written path to one relative to `station/generated/`."""
    cut = p.rfind(_PREFIX)
    return p[cut + len(_PREFIX):] if cut >= 0 else p


def engine_reads():
    """Every generated-data FILE the engine names, with how it was written.

    Returns (resolved, dynamic). `resolved` maps a path relative to
    `station/generated/` to the list of `file:line` that name it; `dynamic` is
    the list of reads a static scan cannot turn into a filename.

    A read written as `base.path_join("bank.json")` gives up only its leaf --
    the base is a variable and the composition happens at run time. Rather than
    model the chain (which is where a scanner starts guessing), the leaf is kept
    as written and `locate()` resolves it against the tree by basename. That
    keeps the scan honest: it reports what the source says and what the disk
    says, and never invents the join between them.

    Directories are dropped, because "is this directory present" is not the
    question -- an empty `generated/audio/` would pass it while the engine dies
    on the file it wanted.
    """
    resolved, dynamic = {}, []
    for f in _gd_files():
        with open(f, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        for i, line in enumerate(lines, 1):
            where = "%s:%d" % (_rel(f), i)
            for rx, form in ((_LITERAL, "literal"), (_JOINED, "joined")):
                for m in rx.finditer(line):
                    rel = _strip(m.group(1)).strip("/")
                    if not rel or rel == ".." or "." not in os.path.basename(rel):
                        continue                  # a directory, not a file
                    hit = resolved.setdefault(rel, {"where": [], "form": form})
                    hit["where"].append(where)
                    if form == "literal":
                        hit["form"] = "literal"   # the stronger claim wins
            for m in _SUFFIX.finditer(line):
                dynamic.append((m.group(1), where))
    return resolved, dynamic


_TREE = None


def locate(rel, form="literal"):
    """Where this path actually is under `station/generated/`, if anywhere.

    THE DISCRIMINATOR IS HOW THE READ WAS WRITTEN, and getting that wrong broke
    this tool twice in opposite directions, which is why it is spelled out:

      * A basename fallback for everything made the gate LIE. It resolved
        `scene/transit/lift.json` -- genuinely absent -- to an unrelated
        `lift.json` elsewhere in the tree, and the tool printed `0 missing`
        while the engine's file was not there. A gate that matches on leaf alone
        cannot fail for the defect it exists to catch.

      * Then restricting the fallback to bare leaves broke the OTHER case.
        `gen.path_join("starfury/starfury.glb")` carries a directory and is
        still not fully specified, because `gen` is
        `station/generated/scene` -- a run-time variable. The file is at
        `scene/starfury/starfury.glb` and the tool called it missing.

    So: a LITERAL read states its whole path relative to `generated/` and is
    checked exactly. A JOINED fragment is a SUFFIX of the real path, however
    many directories it carries, because its base is decided at run time -- so
    it matches any path ending in that fragment on a component boundary. That
    is strict enough to reject `no/such/dir/bank.json` and loose enough to
    accept `starfury/launch.json` sitting at `scene/starfury/launch.json`.

    Returns the path relative to `generated/`, or None.
    """
    global _TREE
    if os.path.exists(os.path.join(GENERATED, rel)):
        return rel
    if form == "literal":
        return None                       # fully specified, and it is not there
    if _TREE is None:
        _TREE = []
        for base, dirs, names in os.walk(GENERATED):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for n in names:
                _TREE.append(os.path.relpath(os.path.join(base, n), GENERATED))
        _TREE.sort()
    tail = "/" + rel
    hits = [p for p in _TREE if p == rel or p.endswith(tail)]
    return hits[0] if hits else None


def _ci_text():
    if not os.path.exists(WORKFLOW):
        return ""
    with open(WORKFLOW, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def producer_of(rel):
    """Which station module writes this generated path, by name search.

    Deliberately crude and deliberately honest about it: a module that writes
    `starfury/launch.json` names the string `launch.json` somewhere. This finds
    candidates; it does not prove authorship. A path with no candidate is the
    interesting row either way -- either nothing produces it, or it is produced
    by a name built at run time, and both are worth a reader's attention.
    """
    leaf = os.path.basename(rel)
    hits = []
    for base, dirs, names in os.walk(STATION):
        dirs[:] = [d for d in dirs if d not in ("generated", "__pycache__")]
        for n in sorted(names):
            if not n.endswith(".py"):
                continue
            p = os.path.join(base, n)
            with open(p, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            if leaf in body or rel in body:
                hits.append(_rel(p))
    return hits


def ci_runs(module_rel):
    """Does CI invoke this module? Matched on the path as CI would write it."""
    ci = _ci_text()
    leaf = os.path.basename(module_rel)
    # CI writes these two ways: `python3 station/foo.py` and a `cd station` then
    # `python3 foo.py`. Both are just the leaf appearing after a python3.
    return bool(re.search(r"python3\s+\S*" + re.escape(leaf), ci))


def data_report(out=print):
    """--data: every generated path the engine reads, and whether CI makes it."""
    resolved, dynamic = engine_reads()
    rows, missing, unbuilt = [], [], []
    for rel in sorted(resolved):
        found = locate(rel, resolved[rel]["form"])
        prod = producer_of(rel)
        built = any(ci_runs(p) for p in prod)
        rows.append((rel, found, prod, built))
        if found is None:
            missing.append(rel)
        elif not built:
            unbuilt.append(rel)

    out("ENGINE DATA -- %d distinct generated FILES named by %d .gd/.tscn files"
        % (len(resolved), len(_gd_files())))
    out("")
    out("  %-40s %-10s %s" % ("path the engine names", "on disk", "producer in CI"))
    for rel, found, prod, built in rows:
        if found is None:
            tag = "NO"
        elif found == rel:
            tag = "yes"
        else:
            tag = "as " + found[:18]           # resolved by basename search
        if not prod:
            who = "-- no producer found"
        elif built:
            who = "yes  (%s)" % prod[0]
        else:
            who = "NO   (%s)" % prod[0]
        out("  %-40s %-10s %s" % (rel[:40], tag, who))

    if dynamic:
        out("")
        out("  %d read(s) whose filename is built at run time and cannot be"
            " resolved statically:" % len(dynamic))
        for suffix, where in dynamic:
            out("    ...%-24s %s" % (suffix, where))

    out("")
    if missing:
        out("  MISSING FROM DISK -- the engine reads these and they are not there:")
        for rel in missing:
            out("    %s   read by %s"
                % (rel, ", ".join(resolved[rel]["where"][:2])))
    if unbuilt:
        out("  PRESENT BUT NOT REPRODUCIBLE -- on disk, but no CI step rebuilds them,")
        out("  so they die on a fresh clone the moment anybody deletes them:")
        for rel in unbuilt:
            out("    %s" % rel)
    if not missing and not unbuilt:
        out("  every path the engine reads exists and is rebuilt by CI.")
    return rows, missing, unbuilt, dynamic


def _module_dirs():
    out = []
    for base, dirs, names in os.walk(STATION):
        dirs[:] = [d for d in dirs if d not in ("generated", "__pycache__")]
        if any(n.endswith(".py") for n in names):
            out.append(base)
    return sorted(out)


def caller_report(out=print):
    """--callers: a tested module nothing outside its directory imports."""
    # Build the import graph over station/ and tools/, by module basename. A
    # basename collision would make this over-report a caller, which is the safe
    # direction for a gate that is looking for ZERO callers.
    modules = {}
    for d in _module_dirs():
        for n in sorted(os.listdir(d)):
            if n.endswith(".py") and not n.startswith("test_"):
                modules[n[:-3]] = os.path.join(d, n)

    sources = []
    for top in (STATION, os.path.join(ROOT, "tools"), GODOT):
        for base, dirs, names in os.walk(top):
            dirs[:] = [x for x in dirs if x not in ("generated", "__pycache__")]
            for n in sorted(names):
                if n.endswith((".py", ".gd")):
                    sources.append(os.path.join(base, n))

    external = {m: [] for m in modules}
    for src in sources:
        with open(src, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for m, mpath in modules.items():
            # "Does ANYTHING import it", not "does anything outside its own
            # directory". CLAUDE.md's phrasing -- "twelve tested modules with
            # zero importers OUTSIDE THEIR OWN DIRECTORIES" -- was about the
            # `npc/` and `physics/` packages, where the distinction is real.
            # Applied as a general rule it measures nothing, because ~60 of
            # these modules live in `station/` together: it hid `bespoke.py`
            # dispatching to `observation`, `concourse` and `aperture`, and
            # reported all three as unreachable. The module itself and its own
            # `test_` file are the only excluded callers.
            if os.path.abspath(src) == os.path.abspath(mpath):
                continue
            if os.path.basename(src) == "test_%s.py" % m:
                continue
            name = re.escape(m)
            if re.search(r"\b(?:import|from)\s+\S*\b" + name + r"\b", body) \
               or re.search(r"\b" + name + r"\.\w", body) \
               or re.search(_DYNAMIC_IMPORT % name, body):
                external[m].append(_rel(src))

    # "Tested" means the repo asserts something about it -- a test_ file, a
    # --selftest, or a --gate. Those are the modules somebody invested in.
    tested = {}
    for m, mpath in modules.items():
        with open(mpath, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        has_self = "--selftest" in body or "--gate" in body or "def _selftest" in body
        sibling = os.path.join(os.path.dirname(mpath), "test_%s.py" % m)
        if has_self or os.path.exists(sibling):
            tested[m] = mpath

    orphans = sorted(m for m in tested if not external[m])
    out("CALLERS -- %d modules, %d of them tested or self-testing"
        % (len(modules), len(tested)))
    out("")
    if orphans:
        out("  %d tested module(s) that NOTHING else in the repository"
            " imports:" % len(orphans))
        for m in orphans:
            out("    %-28s %s" % (m, _rel(tested[m])))
        out("")
        out("  A module in this list is not necessarily broken -- a top-level"
            " tool or a")
        out("  CI entry point legitimately has no importer. It IS the list to"
            " read when")
        out("  asking why something built and tested does not appear in the"
            " game.")
    else:
        out("  every tested module is imported from outside its own directory.")
    return tested, orphans


_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append("%s %s" % (name, detail))
    return ok


def _selftest(out=print):
    """The gate, plus the controls that show it can fail."""
    out("=" * 72)
    rows, missing, unbuilt, dynamic = data_report(out)
    out("")
    out("=" * 72)
    tested, orphans = caller_report(out)
    out("")
    out("=" * 72)
    out("negative controls:")

    # Control 1: the scanner must actually find the Starfury reads, which are
    # the joined form -- the form a naive literal-only scan misses entirely.
    resolved, _dyn = engine_reads()
    fury = [p for p in resolved if p.startswith("starfury/")]
    check(len(fury) >= 3, "the joined-path form is scanned",
          "found %d starfury/* reads, want >= 3" % len(fury))
    out("  the `path_join(\"starfury/...\")` form is seen: %d read(s) -- %s"
        % (len(fury), ", ".join(sorted(fury))))

    # Control 2: a literal-only scanner would report zero of them. This is the
    # control that proves the joined regex is load-bearing rather than decorative.
    lit_only = set()
    for f in _gd_files():
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                for m in _LITERAL.finditer(line):
                    p = m.group(1)
                    cut = p.find(_PREFIX)
                    if cut >= 0:
                        lit_only.add(p[cut + len(_PREFIX):])
    hidden = sorted(set(resolved) - lit_only)
    check(bool(hidden), "a literal-only scan misses reads",
          "it would have missed %d" % len(hidden))
    out("  a LITERAL-ONLY scan sees %d paths against this tool's %d -- it would"
        % (len(lit_only), len(resolved)))
    out("  miss %d, including %s" % (len(hidden), ", ".join(hidden[:3])))

    # Control 3: an existence check alone is not the gate. Show that the CI
    # question is separable -- some path exists on disk without a CI producer,
    # or the tool says plainly that none does.
    out("  on disk but not rebuilt by CI: %d path(s)%s"
        % (len(unbuilt), (" -- " + ", ".join(unbuilt[:3])) if unbuilt else ""))

    # Control 4: the basename fallback must not resolve a fully-specified path.
    # This control exists because the first cut of `locate` DID, and reported
    # `0 missing` while `scene/transit/lift.json` was absent -- the gate could
    # not fail for the thing it was written to catch. Probe it with a directory
    # path whose leaf certainly exists elsewhere in the tree.
    bait = None
    for rel in sorted(resolved):
        if not os.path.dirname(rel) and locate(rel, "joined"):
            bait = "no/such/dir/" + os.path.basename(rel)
            break
    if bait:
        got_j, got_l = locate(bait, "joined"), locate(bait, "literal")
        check(got_j is None and got_l is None,
              "the suffix fallback does not over-resolve",
              "locate(%r) -> joined %r, literal %r" % (bait, got_j, got_l))
        out("  a WRONG directory whose leaf exists elsewhere still reads as"
            " missing:")
        out("    locate(%r) -> joined %r, literal %r" % (bait, got_j, got_l))
        # and the legitimate joined case, which the strict rule broke once
        real = locate("starfury/launch.json", "joined")
        check(real is not None, "a joined fragment resolves through its base",
              "starfury/launch.json did not resolve")
        out("    locate('starfury/launch.json', 'joined') -> %r" % (real,))

    # Control 5: the dynamic-import form must be seen. `shuttle` is reached ONLY
    # as `__import__("shuttle")` from `bespoke.py`, so if this regresses it
    # reappears in the orphan list -- which is how the false-orphan bug was
    # found in the first place.
    check("shuttle" not in orphans, "a `__import__(\"name\")` caller is seen",
          "shuttle is reported orphaned, but bespoke.py dispatches to it")
    out("  a module reached only as `__import__(\"shuttle\")` is NOT reported"
        " orphaned")

    # Control 6: the caller graph must not be vacuous. If it reports every
    # module as orphaned, the import regex is broken rather than the repo.
    check(len(orphans) < len(tested), "the caller graph resolves imports",
          "%d of %d tested modules look orphaned -- the regex is the suspect"
          % (len(orphans), len(tested)))
    out("  the caller graph is not vacuous: %d of %d tested modules have an"
        " external importer" % (len(tested) - len(orphans), len(tested)))

    # MISSING IS A FAILURE; UNREPRODUCIBLE IS A REPORT, and the asymmetry is
    # deliberate. A path the engine reads that nothing on disk satisfies is a
    # mode that cannot run -- unambiguous, and exactly the defect this tool
    # exists for, so the gate must go red for it and stay red until it is built.
    # "On disk but no CI step rebuilds it" is a weaker claim: the mode works
    # here and would break on a fresh clone. Failing on that today would make
    # the gate red for six paths at once and bury the one that is actually
    # broken -- so it is printed, counted, and left for the CI-coverage work it
    # belongs to rather than folded into this signal.
    check(not missing, "every path the engine reads exists",
          "%d missing: %s" % (len(missing), ", ".join(missing)))

    out("")
    out("wiring: %d engine data paths, %d missing, %d unreproducible,"
        " %d orphaned tested modules" % (len(rows), len(missing), len(unbuilt),
                                         len(orphans)))
    if _FAILED:
        out("")
        out("FAILED:")
        for f in _FAILED:
            out("  " + f)
        return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", action="store_true",
                    help="every generated path the engine reads, and whether "
                         "CI rebuilds it")
    ap.add_argument("--callers", action="store_true",
                    help="tested modules nothing outside their directory imports")
    ap.add_argument("--selftest", action="store_true",
                    help="both, with the negative controls")
    a = ap.parse_args(argv)
    if a.selftest or not (a.data or a.callers):
        return 0 if _selftest() else 1
    if a.data:
        data_report()
    if a.callers:
        caller_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
