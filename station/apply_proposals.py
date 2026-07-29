"""Turn `docs/layer3-proposals/*.json` into Material(...) source for materials.py.

WHY A SCRIPT AND NOT HAND-TRANSCRIPTION
---------------------------------------
Four agents proposed roughly forty materials with eleven fields each. Typing
those in is four hundred opportunities to transpose a digit, and a transposed
roughness is invisible in every gate this project has: it is in range, it is
plausible, and it is not what the proposer measured. The proposals are
committed as data; this renders them, so the file on disk and the file that was
reviewed are provably the same numbers.

It also means a proposal can be re-rendered after an edit, rather than merged
once and then diverging from its own record.

WHAT IT REFUSES TO DO
---------------------
It is not a merge tool and it does not touch `materials.py`. It prints the
block, and a human -- or the next context -- pastes it into `_build()`. The
reason is the one this session already learned the hard way in the other
direction: a generator that rewrites a file it does not own is fine when the
file is generated output (`.tres`, the scene rules table) and wrong when the
file is authored source. `materials.py` is authored. Its ordering, its section
comments and its prose are the record of why each value is what it is, and a
script that reflows them destroys exactly the thing that makes the library
reviewable.

Run:  python3 station/apply_proposals.py            # print the block
      python3 station/apply_proposals.py --check    # validate only
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import materials as M                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPOSALS = os.path.join(ROOT, "docs", "layer3-proposals")


def load():
    out = []
    for path in sorted(glob.glob(os.path.join(PROPOSALS, "*.json"))):
        with open(path) as f:
            d = json.load(f)
        out.append((d.get("_family", os.path.basename(path)[:-5]),
                    d.get("materials", []), d.get("coverage_note", "")))
    return out


def validate(family, mats, seen_names, seen_frags):
    """Everything that can be wrong before a line of source is written.

    Deliberately overlapping with `test_materials_layer3.py`: that file gates
    the library AFTER application, this one refuses to emit source that would
    fail it. Catching it here means the failure names the proposal rather than
    the library.
    """
    bad = []
    for m in mats:
        n = m.get("name", "?")
        if n in M.BY_NAME:
            bad.append(f"{family}/{n}: name already in the library")
        if n in seen_names:
            bad.append(f"{family}/{n}: name proposed twice")
        seen_names.add(n)
        for frag in m.get("binds", ()):
            if frag in seen_frags:
                bad.append(f"{family}/{n}: fragment {frag!r} claimed twice")
            seen_frags.add(frag)
            for other in M.MATERIALS:
                if frag in other.binds:
                    bad.append(f"{family}/{n}: fragment {frag!r} is already "
                               f"{other.name}'s")
        tex = m.get("texture")
        if tex and tex not in M.TEX_SIZE:
            bad.append(f"{family}/{n}: unknown texture {tex!r}")
        if tex and not m.get("uv_scale_denom"):
            bad.append(f"{family}/{n}: textured but no uv_scale_denom")
        for k in ("roughness", "metallic", "specular"):
            v = m.get(k)
            if not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
                bad.append(f"{family}/{n}: {k}={v!r} outside [0, 1]")
        alb = m.get("albedo") or []
        if len(alb) != 3 or any(not 0.0 <= c <= 1.0 for c in alb):
            bad.append(f"{family}/{n}: albedo {alb!r} is not three values in "
                       f"[0, 1]")
        if not (m.get("source") or "").strip():
            bad.append(f"{family}/{n}: no source")
        if not (m.get("reasoning") or "").strip():
            bad.append(f"{family}/{n}: no reasoning")
    return bad


def _wrap(text, width, indent):
    """Comment-wrap prose to the project's 79 columns."""
    words, lines, cur = text.split(), [], indent
    for w in words:
        if len(cur) + len(w) + 1 > width and cur.strip() != indent.strip():
            lines.append(cur.rstrip())
            cur = indent + w
        else:
            cur = (cur + " " + w) if cur.strip() != indent.strip() else cur + w
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def render(family, mats):
    out = [f"    # ---- {family} " + "-" * (62 - len(family))]
    for m in mats:
        n, alb = m["name"], m["albedo"]
        out.append("")
        for ln in _wrap(m["reasoning"], 79, "        # "):
            out.append(ln)
        out.append("    a(Material(")
        out.append(f'        "{n}", "{m["title"]}",')
        out.append(f"        albedo=({alb[0]:.3f}, {alb[1]:.3f}, {alb[2]:.3f}),"
                   f" roughness={m['roughness']}, metallic={m['metallic']},")
        line = f"        specular={m['specular']}"
        if m.get("texture"):
            line += (f', texture="{m["texture"]}", '
                     f"uv_scale=1.0 / {m['uv_scale_denom']}")
        out.append(line + ",")
        if m.get("emission"):
            e = m["emission"]
            out.append(f"        emission=({e[0]:.3f}, {e[1]:.3f}, {e[2]:.3f}),"
                       f" emission_energy={m.get('emission_energy') or 1.0},")
        binds = ", ".join(f'"{b}"' for b in m["binds"])
        out.append(f"        binds=({binds}{',' if len(m['binds']) == 1 else ''}),"
                   f' scenes=("interior",),')
        out.append(f'        source="{m["source"].replace(chr(34), chr(39))}",')
        out.append(f'        extrapolated="'
                   f'{m["extrapolated"].replace(chr(34), chr(39))}"))')
    return out


def main(argv):
    families = load()
    if not families:
        print(f"no proposals in {PROPOSALS}")
        return 1
    seen_names, seen_frags, bad = set(), set(), []
    total = 0
    for family, mats, note in families:
        bad += validate(family, mats, seen_names, seen_frags)
        total += len(mats)
        if note.strip():
            print(f"; {family} coverage note: {note}", file=sys.stderr)
    if bad:
        print(f"{len(bad)} problems, nothing emitted:", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        return 1
    print(f"; {len(families)} families, {total} materials, validated",
          file=sys.stderr)
    if "--check" in argv:
        return 0
    for family, mats, _note in families:
        for ln in render(family, mats):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
