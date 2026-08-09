#!/usr/bin/env python3
"""Every INV cited in code is defined, and no number means two things.

HARD RULE 2 SAYS *"Log every invention ... Canon and extrapolation must never
blur"*, AND NOTHING ENFORCED IT. `canon/INVENTIONS.md` is the register of every
declared extrapolation in this project -- 272 entries -- and the modules cite it
by number in comments beside the constants those numbers justify. A citation
with nothing behind it looks exactly like a sourced value, which is the one
thing hard rule 1 forbids: *"a number that looks sourced and is not"*.

WHAT IT FOUND ON ITS FIRST RUN, session 4q: **13 dangling citations**, and worse,
**two numbers meaning two different things each** --

    INV-450   the ragdoll's settle threshold      AND  a farm hedge's height
    INV-451   the spin-derived gravity            AND  a clump lattice spacing

THE CAUSE IS WORTH STATING BECAUSE IT WILL RECUR. Two agents worked in one
session. One's entries were appended to `INVENTIONS.md`; the other's module was
integrated from a workflow whose report -- which carried its entries -- had been
destroyed by a container recycle. Each had been given a reserved block, and
nothing checked the blocks against each other. **A number is an index into a
shared namespace, and this project had no gate on that namespace.**

TWO CHECKS, AND THE SECOND IS THE EXPENSIVE ONE.

  * DUPLICATE HEADINGS are the easy half: two `## INV-nnn` lines in the register.
  * A DANGLING CITATION is the half that hurts. INV-458 and INV-459 had been
    cited in a shipped module since the day it was written, and the only reason
    their derivations survived is that the module states them in comments beside
    the constants. Had it not, the reasoning would have been unrecoverable --
    the report that carried them no longer exists.

WHAT IT DELIBERATELY DOES NOT CHECK. An entry in the register that nothing
cites is NOT an error: plenty of entries are decisions about content, canon or
process rather than about a constant in a file, and a gate that demanded a
citation for each would push people to sprinkle numbers into comments to satisfy
it. Unused entries are reported under `--report` and never fail.

Run:
    python3 tools/inv_check.py            # the gate
    python3 tools/inv_check.py --report   # every number, cited and defined
    python3 tools/inv_check.py --selftest # the controls
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTER = os.path.join(ROOT, "canon", "INVENTIONS.md")

# Where a citation may appear. `godot/` is included because GDScript comments
# cite INV numbers too -- `ragdoll.gd` carries INV-440..450 in its header.
SOURCE_DIRS = ("station", "tools", "godot")
SOURCE_EXT = (".py", ".gd", ".gdshader")

# A definition is a level-2 heading. The register uses `## INV-nnn -- title`
# throughout; anything else is prose ABOUT an entry, not the entry.
DEFINE_RE = re.compile(r"^##\s+(INV-\d+)", re.M)
# A citation is the token anywhere in a source file. Deliberately not anchored
# to a comment marker: the whole point is to catch the number wherever a reader
# would take it as a source, and `INV-` in a string literal is still a claim.
# THE NEGATIVE LOOKAHEAD IS NOT OPTIONAL, AND THIS GATE'S FIRST RUN PROVED IT.
# Without it, `INV-\d+` matches the `INV-4` prefix of `INV-4G-001` -- an id in a
# DIFFERENT namespace (`npc/body.py` cites one for an interpupillary figure) --
# and the gate reported a malformed citation that does not exist. A gate that
# invents a finding is worse than no gate: it costs the reader the time to
# disprove it, and it teaches them to discount the next report.
CITE_RE = re.compile(r"INV-\d+(?![\w-])")


def defined():
    """`{number: line}` for every entry in the register, and the duplicates."""
    text = open(REGISTER, errors="replace", encoding="utf-8").read()
    seen, dupes = {}, []
    for m in DEFINE_RE.finditer(text):
        n = m.group(1)
        line = text[: m.start()].count("\n") + 1
        if n in seen:
            dupes.append((n, seen[n], line))
        else:
            seen[n] = line
    return seen, dupes


def cited():
    """`{number: [(path, line), ...]}` for every citation in the source tree."""
    out = {}
    for d in SOURCE_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, dirnames, files in os.walk(base):
            # `generated/` is build output, not source, and it is gitignored --
            # a citation there is a copy of one from the file that wrote it.
            dirnames[:] = [x for x in dirnames
                           if x not in ("generated", "__pycache__", ".git")]
            for f in files:
                if not f.endswith(SOURCE_EXT):
                    continue
                p = os.path.join(dirpath, f)
                # THIS FILE IS SKIPPED, and `station/coldstart.py` set the
                # precedent in as many words: "a gate that reacts to what it
                # says about itself is a gate marking its own homework". This
                # module's docstring quotes INV-450 and INV-451 to explain the
                # collision it was written for, and the comment beside CITE_RE
                # quotes `INV-4` to explain a false positive. Every one of those
                # is PROSE ABOUT a citation, not a citation -- and on the first
                # run the gate duly reported its own explanation as a defect.
                if os.path.abspath(p) == os.path.abspath(__file__):
                    continue
                rel = os.path.relpath(p, ROOT)
                with open(p, errors="replace", encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        for n in CITE_RE.findall(line):
                            out.setdefault(n, []).append((rel, i))
    return out


def check(report=False):
    have, dupes = defined()
    use = cited()

    dangling = {n: v for n, v in use.items() if n not in have}

    ok = not dangling and not dupes
    print("INV REGISTER -- %d entries defined, %d numbers cited across %s/"
          % (len(have), len(use), "/, ".join(SOURCE_DIRS)))

    if dupes:
        print("\n  DUPLICATE ENTRIES -- one number, two definitions:")
        for n, a, b in dupes:
            print("    %s defined at canon/INVENTIONS.md:%d and :%d" % (n, a, b))

    if dangling:
        print("\n  DANGLING CITATIONS -- cited in code, no entry in the register.")
        print("  A number that looks sourced and is not is exactly what hard")
        print("  rule 1 forbids. Write the entry or drop the citation:")
        for n in sorted(dangling, key=lambda s: int(s.split("-")[1])):
            where = dangling[n]
            print("    %-8s %s%s" % (n, where[0][0] + ":" + str(where[0][1]),
                                     "" if len(where) == 1
                                     else "  (+%d more)" % (len(where) - 1)))

    if report:
        unused = sorted(set(have) - set(use), key=lambda s: int(s.split("-")[1]))
        print("\n  %d entries are defined and cited by no source file. THIS IS"
              % len(unused))
        print("  NOT AN ERROR -- many entries are decisions about content, canon")
        print("  or process rather than about a constant in a file, and a gate")
        print("  demanding a citation for each would push people to sprinkle")
        print("  numbers into comments to satisfy it.")
        if unused:
            print("    " + ", ".join(unused[:24])
                  + (" ..." if len(unused) > 24 else ""))

    print("\n  %s" % ("INV REGISTER OK" if ok else "INV REGISTER FAILED"))
    return ok


def _selftest():
    """The controls. Each breaks one property and must be caught."""
    import tempfile
    good = True

    def probe(name, text_md, text_src, want):
        nonlocal good
        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "INVENTIONS.md")
            open(md, "w", encoding="utf-8").write(text_md)
            sub = os.path.join(d, "station")
            os.makedirs(sub)
            open(os.path.join(sub, "m.py"), "w").write(text_src)
            g = globals()
            old_reg, old_root, old_dirs = REGISTER, ROOT, SOURCE_DIRS
            g["REGISTER"], g["ROOT"], g["SOURCE_DIRS"] = md, d, ("station",)
            try:
                got = check()
            finally:
                g["REGISTER"], g["ROOT"], g["SOURCE_DIRS"] = (
                    old_reg, old_root, old_dirs)
        hit = got == want
        good = good and hit
        print("  %s %-34s -> %s (wanted %s)"
              % ("ok  " if hit else "FAIL", name,
                 "OK" if got else "FAILED", "OK" if want else "FAILED"))

    print("INV_CHECK CONTROLS")
    probe("a cited number that is defined",
          "## INV-001 - a thing\n", "# see INV-001\nX = 1\n", True)
    probe("a cited number that is NOT defined",
          "## INV-001 - a thing\n", "# see INV-002\nX = 1\n", False)
    probe("one number defined twice",
          "## INV-001 - a thing\n## INV-001 - another thing\n",
          "# see INV-001\n", False)
    probe("a foreign id is not a citation",
          "## INV-001 - a thing\n", "# see INV-4G-001 and INV-001\n", True)
    probe("an entry nothing cites is NOT an error",
          "## INV-001 - a thing\n## INV-002 - uncited\n", "# see INV-001\n",
          True)
    print("  CONTROLS %s" % ("PASS" if good else "FAIL"))
    return good


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if _selftest() else 1)
    sys.exit(0 if check(report=a.report) else 1)
