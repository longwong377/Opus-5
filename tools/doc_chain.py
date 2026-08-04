#!/usr/bin/env python3
"""Assert the plan hierarchy in CLAUDE.md is complete and points at real files.

WHY THIS EXISTS. This project has produced five plan documents across many
sessions, and the single most expensive process defect it has had is a plan
nothing pointed at: the session-4i draft was written, reviewed and nearly
adopted while `CLAUDE.md` — the file every session is instructed to read FIRST,
and whose contents override default behaviour — still headlined a ruling from
three sessions earlier. A future context reading `docs/` in file order acts on
whichever plan it happens to open.

Prose cannot fix that, because prose is what failed. So:

  * every plan-shaped document in `docs/` must appear in CLAUDE.md's
    supersession ledger. A new plan cannot appear unplaced — if someone adds
    `docs/MASTER-PLAN-5a.md` and does not place it in the hierarchy, CI fails.
  * every file the read-order table names must exist. A pointer to a file that
    was renamed or deleted is a chain that breaks silently.
  * the ledger must mark exactly one content authority and one ordering
    authority as CURRENT, so "which plan is live" has one answer.

This is `a gate that does not run is not a gate` applied to the plan itself.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(ROOT, "CLAUDE.md")

# A document is plan-shaped if its NAME claims authority over what or when to
# build. Deliberately name-based: a plan announces itself in its filename here,
# and a content-based test would have to parse intent.
PLAN_RE = re.compile(r"(PLAN|THE-STATION|SHIP)", re.I)


def main():
    txt = open(CLAUDE, encoding="utf-8").read()
    if "## START HERE" not in txt:
        print("FAIL: CLAUDE.md has no '## START HERE' read-order section")
        return 1
    ledger = txt[txt.index("## START HERE"):]
    ledger = ledger[:ledger.index("\n## ", 10)] if "\n## " in ledger[10:] else ledger

    errors = []

    # 1. every plan-shaped doc is placed in the ledger
    docs = sorted(f for f in os.listdir(os.path.join(ROOT, "docs"))
                  if f.endswith(".md") and PLAN_RE.search(f))
    for d in docs:
        if d not in ledger:
            errors.append(f"docs/{d} is plan-shaped and is NOT placed in "
                          f"CLAUDE.md's supersession ledger — a plan nobody "
                          f"points at is read after the old rulings")

    # 2. every file the chain names exists
    for m in re.finditer(r"`(docs/[\w./{},-]+\.md|STATE\.md|canon/[\w.-]+\.md|"
                         r"tools/[\w.-]+\.py|station/[\w.-]+\.py)`", ledger):
        ref = m.group(1)
        if "{" in ref:                       # docs/spec/{PLACES,PEOPLE,...}.md
            base, rest = ref.split("{", 1)
            names, suffix = rest.split("}", 1)
            paths = [base + n + suffix for n in names.split(",")]
        else:
            paths = [ref]
        for p in paths:
            if not os.path.exists(os.path.join(ROOT, p)):
                errors.append(f"CLAUDE.md's chain names {p}, which does not exist")

    # 3. exactly one content authority and one ordering authority
    for label, want in (("the content authority", 1), ("the ordering authority", 1)):
        n = ledger.count(label)
        if n != want:
            errors.append(f"the chain marks {n} documents as '{label}' — "
                          f"exactly {want} may be CURRENT, or 'which plan is "
                          f"live' has no single answer")

    print(f"doc chain: {len(docs)} plan-shaped documents, all placed"
          if not errors else f"doc chain: {len(errors)} ERROR(S)")
    for e in errors:
        print("  ", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
