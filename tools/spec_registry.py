#!/usr/bin/env python3
"""Generate and validate the completion registry from the spec annexes.

THE-STATION.md §1's whole authority rests on this file existing and running:
*"a gate that does not run is not a gate, and today the entire §1 is one"* was
the synthesis judge's verdict on the bible before this existed. This turns four
markdown documents into `docs/spec/completion.yaml` and FAILS on every ambiguity
a future session could exploit:

  * an item with no acceptance check fails the GENERATOR, so the registry cannot
    be produced around it
  * every cross-reference must resolve to a defined item — including the
    lettered SHB sub-rows (`SHB-02.c`), which are validated against the letters
    their parent block actually declares. The panel found seven mis-lettered
    pointers by hand; this makes finding the eighth free and permanent.
  * `INC-*` is deliberately defined TWICE — a vocabulary table in PLACES and a
    mechanics table in SYSTEMS, which the spec requires to be "the same 22 IDs,
    1:1 in both directions". That is not a duplicate to reject; it is a
    BIJECTION TO VERIFY, and this file verifies it in both directions.
  * item text is hashed, so an adopted item edited without a SPEC-CHANGE whose
    `recomputes:` names it can be caught by diffing the emitted registry

THE ID GRAMMAR, as the annexes actually write it (§1.1 of THE-STATION.md):

  heading form   `### PLC-001 \x60cnc\x60 — Command and Control`
                 `## 0.3 GDS-01 — THE GOODS VOCABULARY`
    A heading DEFINES the ID it names only when that ID is followed by a title
    separator (` —` or a backtick). `## 2b. THE PLAYER — PLY-01..08` and
    `## 0.2 INCIDENT CLASSES — (mechanics live in SYS-14)` MENTION ids and
    define nothing; treating those as definitions was this parser's own bug.

  table form     `| INC-LINER | ... | ... |`   `| SHC-01 | ... |`
    The row is the item. Its check lives in the table's own columns, so a table
    row satisfies "has a check" when it carries >= CHECK_CELLS cells, or when a
    sibling definition elsewhere does (the INC case: 3-cell vocabulary here,
    5-cell mechanics there).

  sub-rows       `  c. **Casual-labour muster point** ...` inside an SHB block
    Lettered annexes are registry rows in their own right and green their parent
    only when all of them green (the umbrella rule, §1.1.6).

Numeric IDs canonicalise zero-padded to three digits; alphabetic IDs (INC-LINER)
stay as written. Both forms are accepted anywhere an ID appears.
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = [
    "docs/THE-STATION.md",
    "docs/spec/PLACES.md",
    "docs/spec/PEOPLE.md",
    "docs/spec/SYSTEMS.md",
]
OUT = os.path.join(ROOT, "docs/spec/completion.yaml")

PREFIXES = "PLC|SHB|SHC|INC|FAC|CAST|ROLE|DLG|SYS|SUR|PLY|VRB|GDS"
NUM = r"[A-Z][A-Z0-9]{1,11}|\d{1,3}"

ID_RE = re.compile(rf"\b({PREFIXES})-({NUM})(?:\.([a-z]))?\b")
# A heading defines the id it TITLES: the id must be followed by a title
# separator. Anything else in a heading is a mention.
HEAD_DEF = re.compile(rf"^#{{2,4}}\s+.*?\b({PREFIXES})-({NUM})\b(?=\s+[—`])")
ROW_DEF = re.compile(rf"^\|\s*({PREFIXES})-({NUM})\s*\|")
# `  c. **Name** ...` — a lettered annex inside its parent's block.
# Lettered annexes appear two ways in the annexes as written: on their own
# indented line (SHB-02) and inline after the bullet (SHB-04's
# "- named annexes: a. **4 hotels**"). Both are the same declaration.
LETTER_DEF = re.compile(r"(?:^|\s)([a-z])\.\s+\*\*")
CHECK_RE = re.compile(r"\*\*(CHECK|ACCEPT|Check)\b|^\s*[-*]?\s*CHECK:", re.I | re.M)
HARNESS_RE = re.compile(r"\**harness:\**\s*([^\n|]+)", re.I)
CHECK_CELLS = 4          # a table row carries its own check at >= 4 cells


def canon(pref, num):
    return f"{pref}-{int(num):03d}" if num.isdigit() else f"{pref}-{num}"


def parse(paths):
    """(items, refs, letters, errors).

    items[id] = {file, line, text, cells, kind}
    letters[SHB-nnn] = {'a','b',...}
    refs = [(file, line, id, letter_or_None)]
    """
    items, refs, letters, errors = {}, [], {}, []
    for rel in paths:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            errors.append(f"{rel}: MISSING FILE")
            continue
        cur, buf, cur_shb = None, [], None
        lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
        for n, ln in enumerate(lines, 1):
            hm, rm = HEAD_DEF.match(ln), ROW_DEF.match(ln)
            m = hm or rm
            if m:
                if cur:
                    items[cur]["text"] = "".join(buf)
                iid = canon(m.group(1), m.group(2))
                kind = "heading" if hm else "row"
                cells = len([c for c in ln.split("|") if c.strip()]) if rm else 0
                if iid in items:
                    # INC is defined twice BY DESIGN (vocabulary + mechanics).
                    # Record the richer definition and let validate() prove the
                    # two tables are a bijection.
                    prev = items[iid]
                    if cells > prev["cells"]:
                        prev.update(file=rel, line=n, cells=cells, kind=kind)
                    prev.setdefault("also", []).append(f"{rel}:{n}")
                    if not iid.startswith("INC-"):
                        errors.append(
                            f"{rel}:{n}: DUPLICATE definition of {iid} "
                            f"(first at {prev['file']}:{prev['line']}) — only "
                            f"INC may be defined twice, and only as a bijection")
                    cur, buf = None, []
                    continue
                items[iid] = {"file": rel, "line": n, "text": "",
                              "cells": cells, "kind": kind}
                cur, buf = iid, [ln]
                if iid.startswith("SHB-"):
                    cur_shb = iid
                    letters.setdefault(iid, set())
            else:
                if cur:
                    buf.append(ln)
                if cur_shb:
                    for lm in LETTER_DEF.finditer(ln):
                        letters[cur_shb].add(lm.group(1))
                if ln.startswith("#"):
                    cur_shb = None if not ln.startswith("### SHB-") else cur_shb
            for rf in ID_RE.finditer(ln):
                refs.append((rel, n, canon(rf.group(1), rf.group(2)), rf.group(3)))
        if cur:
            items[cur]["text"] = "".join(buf)
    return items, refs, letters, errors


def validate(items, refs, letters, paths):
    errors = []
    defined = set(items)

    for rel, n, rid, letter in refs:
        if rid not in defined:
            errors.append(f"{rel}:{n}: reference to UNDEFINED item {rid}")
        elif letter is not None:
            have = letters.get(rid, set())
            if letter not in have:
                errors.append(
                    f"{rel}:{n}: {rid}.{letter} — parent declares letters "
                    f"{sorted(have) or '(none)'}; the pointer resolves to nothing")

    for iid, it in items.items():
        if it["kind"] == "row":
            if it["cells"] < CHECK_CELLS and not it.get("also"):
                errors.append(f"{it['file']}:{it['line']}: {iid} is a table row "
                              f"with {it['cells']} cells and no richer sibling "
                              f"— it carries no check")
        elif not CHECK_RE.search(it["text"]):
            errors.append(f"{it['file']}:{it['line']}: {iid} has NO acceptance "
                          f"check — the generator refuses to registry it")

    # THE INC BIJECTION, both directions, as the spec demands in writing.
    def inc_in(doc):
        out = set()
        for ln in open(os.path.join(ROOT, doc), encoding="utf-8"):
            m = ROW_DEF.match(ln)
            if m and m.group(1) == "INC":
                out.add(canon("INC", m.group(2)))
        return out
    voc = inc_in("docs/spec/PLACES.md")
    mech = inc_in("docs/spec/SYSTEMS.md")
    for miss in sorted(voc - mech):
        errors.append(f"INC bijection: {miss} has a vocabulary row in PLACES "
                      f"and NO mechanics row in SYSTEMS")
    for miss in sorted(mech - voc):
        errors.append(f"INC bijection: {miss} has mechanics in SYSTEMS and NO "
                      f"vocabulary row in PLACES")
    return errors


def emit(items, letters):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = []
    for iid in sorted(items):
        it = items[iid]
        hm = HARNESS_RE.search(it["text"])
        harness = hm.group(1).strip().rstrip(".") if hm else "tool-to-build"
        rows.append((iid, it, harness,
                     hashlib.sha256(it["text"].encode()).hexdigest()[:16]))
        for L in sorted(letters.get(iid, ())):
            rows.append((f"{iid}.{L}", it, harness,
                         hashlib.sha256(f"{iid}.{L}".encode()).hexdigest()[:16]))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# GENERATED by tools/spec_registry.py -- do not hand-edit.\n")
        f.write(f"# {len(rows)} rows. A row's state is decided by "
                f"station/spec_check.py, never written here by hand.\n")
        f.write("items:\n")
        for iid, it, harness, digest in rows:
            f.write(f"  - id: {iid}\n")
            f.write(f"    at: {it['file']}:{it['line']}\n")
            f.write(f"    harness: {harness}\n")
            f.write(f"    text_sha: {digest}\n")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="validate only; nonzero exit on any error")
    a = ap.parse_args()
    items, refs, letters, errors = parse(DOCS)
    errors += validate(items, refs, letters, DOCS)
    by = {}
    for iid in items:
        by[iid.split("-")[0]] = by.get(iid.split("-")[0], 0) + 1
    nsub = sum(len(v) for v in letters.values())
    print("registry:", " ".join(f"{k} {v}" for k, v in sorted(by.items())),
          f"= {sum(by.values())} items + {nsub} lettered sub-rows "
          f"= {sum(by.values()) + nsub} rows")
    if errors:
        print(f"\n{len(errors)} ERROR(S) — the registry cannot be produced "
              f"around an ambiguity:")
        for e in errors[:40]:
            print("  ", e)
        if len(errors) > 40:
            print(f"   ... and {len(errors) - 40} more")
        return 1
    if not a.check:
        n = emit(items, letters)
        print(f"wrote {os.path.relpath(OUT, ROOT)} — {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
