#!/usr/bin/env python3
"""The completion checker: decides GREEN / RED / CAPPED per registry row.

THE HONESTY CONTRACT, and it is the entire point of this file: a row is GREEN
only when a check function implemented HERE ran and passed. A row whose harness
is `tool-to-build` is RED *by definition* — the check may be well-written prose,
but prose does not execute, and this project's history is a museum of gates that
were prose. A row whose harness is AUDIT is decided by the filed audit artefact,
not by this process. There is no path to GREEN through this file that does not
run code against the built station.

At adoption nearly everything is RED. That is not a defect; it is the truth the
owner asked for — the registry is the honest distance-to-done, and the number of
GREEN rows can only be moved by building the things.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SPEC-CHANGE #4: one registry path, reconciled with THE-STATION.md §1 and
# tools/spec_registry.py. Two paths for one artefact is hard rule 4's
# failure mode, and here it read as "the registry is missing".
REG = os.path.join(ROOT, "docs/spec/completion.yaml")
sys.path.insert(0, os.path.join(ROOT, "station"))


def rows():
    out, cur = [], {}
    for ln in open(REG, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if re.match(r"^\s+- id: ", ln):
            if cur:
                out.append(cur)
            cur = {"id": ln.split("id:", 1)[1].strip()}
        elif cur and ":" in ln and ln.startswith("    "):
            k, v = ln.strip().split(":", 1)
            cur[k] = v.strip()
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------------------
# Implemented harnesses. Each returns (ok: bool, note: str). Adding one of
# these — and ONLY adding one of these — is how a spec row becomes greenable.
# ---------------------------------------------------------------------------

_SPEC_KEY = re.compile(r"^#+\s*PLC-\d+\s*`([a-z0-9_]+)`")


def _spec_key(at):
    """The place key the spec row's own heading names, e.g. `eva_lock_blue`.

    Read from the document rather than inferred from position, because
    position is exactly what turned out to be wrong.
    """
    if ":" not in at:
        return None
    path, ln = at.rsplit(":", 1)
    try:
        line = open(os.path.join(ROOT, path), encoding="utf-8"
                    ).read().splitlines()[int(ln) - 1]
    except Exception:                                            # noqa: BLE001
        return None
    m = _SPEC_KEY.match(line.strip())
    return m.group(1) if m else None





# INSTANCE ELEVEN, FOUND IN THE FILE WRITTEN TO PREVENT IT, AND THIS IS THE FIX.
#
# This table used to be keyed on the row's `harness:` string, with two entries:
# `"tools/spec_registry.py --check"` and `"register-agreement"`. Measured
# against the live registry, the number of rows carrying either string is
# **ZERO** -- the registry's 300 rows use 37 distinct harness strings, 264 of
# them the literal `tool-to-build`, and not one of them is either key. So both
# harness functions were unreachable: written, docstring'd, and dispatched to
# by nothing.
#
# That is the whole explanation for `0 GREEN / 300 RED`. It was never "two of
# three hundred harnesses are implemented"; it was **no harness could run at
# all**, and the ledger read exactly the same either way -- which is what made
# it invisible. A file whose header says "prose does not execute, and this
# project's history is a museum of gates that were prose" had become a museum
# piece itself.
#
# Dispatch is now on the row's ID PREFIX, which is the thing the registry
# actually guarantees is well-formed, rather than on free text a doc author
# types. `--dispatch` prints the mapping and the row counts, so an entry that
# reaches nothing is visible on demand instead of after a session of wondering
# why the ledger will not move.
def check_by_family(row):
    """Dispatch to `station/spec_harness/<family>.py`, if one has been written.

    ONE MODULE PER FAMILY, and the reason is collision rather than tidiness:
    300 rows in 13 families each ask a different question, and the alternative
    is several people editing this file at once -- which in this repository has
    produced stomped artefacts, half-written imports and a swept commit. Each
    module owns `check(row) -> (ok, note)` and a `SUFFICIENT` flag; see
    `station/spec_harness/__init__.py` for the contract and `plc.py` for a
    worked example that fails on real drift.
    """
    import spec_harness                                          # noqa: PLC0415
    m = spec_harness.module_for(row["id"].split("-")[0])
    if m is None:
        return None
    return m.check(row), bool(getattr(m, "SUFFICIENT", False))


PREFIX_HARNESSES = {}

# Keyed harnesses, for rows whose `harness:` field names a command verbatim.
# EMPTY, AND DELIBERATELY SO. This held one entry keyed on the literal string
# `"tools/spec_registry.py --check"`, and `--dispatch` reported it UNREACHABLE:
# no registry row carries that harness name. It was also redundant -- CI's
# `sspec_gate` step runs `tools/spec_registry.py --check` on its own line,
# before this file is invoked at all, so the check was already happening and
# this was a second way to ask for it that nothing asked.
#
# Kept as an empty dict rather than deleted because the mechanism is right: a
# row whose `harness:` field names a command verbatim should be able to run it.
# When such a row exists, this is where it goes. `--dispatch` will say so if an
# entry here ever reaches nothing again.
HARNESSES = {}


def harness_for(row):
    """The callable that decides this row, and whether it can decide it ALONE.

    Returns (fn, sufficient). `sufficient` is the honesty contract in one
    boolean: `check_place_register_agreement`'s own docstring says it is
    "deliberately NOT sufficient for GREEN on its own", because a place
    existing at the address the spec cites says nothing about whether the place
    contains what the spec describes. So it runs, it can FAIL loudly, and a
    pass leaves the row RED with a stated reason rather than promoting 129
    rows to GREEN on an identity check.

    That distinction is the difference between fixing the dispatch and gaming
    the ledger. The dispatch bug was real and is fixed; the ledger is still
    honest, and it now says WHICH kind of red each row is.
    """
    h = row.get("harness", "tool-to-build")
    if h in HARNESSES:
        return HARNESSES[h], True
    import spec_harness                                          # noqa: PLC0415
    m = spec_harness.module_for(row["id"].split("-")[0])
    if m is not None:
        return m.check, bool(getattr(m, "SUFFICIENT", False))
    return None, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="skip harnesses a family declares SLOW (the CI "
                         "default). A module opts in with `SLOW = True`; "
                         "nothing does today, so --smoke and the full tier "
                         "are currently the same 14 s run -- and the flag "
                         "SAYS SO rather than implying a tier that is not "
                         "there.")
    ap.add_argument("--id", default=None, help="check one row")
    ap.add_argument("--dispatch", action="store_true",
                    help="print which harness each row resolves to, and how "
                         "many rows reach each one. An entry that reaches "
                         "zero rows is how this file spent its whole life "
                         "reporting 0 GREEN.")
    a = ap.parse_args()
    if not os.path.exists(REG):
        print("spec/completion.yaml missing — run tools/spec_registry.py first")
        return 1
    rs = rows()
    # `--smoke` WAS DECLARED AND NEVER READ, found by an adversary reviewing a
    # different file: `grep -n 'a\.smoke' station/spec_check.py` returned only
    # the `add_argument` line, so CI's `--smoke` invocation had always run the
    # full tier. A flag that does nothing is a promise the caller believes --
    # and the CI step's own comment cited the tiering as the reason it was
    # safe to run on every push.
    #
    # It now honours a family's `SLOW` opt-in. No module sets it today, so the
    # two tiers ARE the same run and the `--help` text says exactly that
    # instead of describing a tiering that does not exist. When a harness needs
    # a built station, it sets `SLOW = True` and this starts meaning something.
    if a.smoke:
        import spec_harness                                       # noqa: PLC0415
        rs = [r for r in rs
              if not getattr(spec_harness.module_for(r["id"].split("-")[0]),
                             "SLOW", False)]
    if a.dispatch:
        import collections                                        # noqa: PLC0415
        seen = collections.Counter()
        for r in rs:
            fn, suf = harness_for(r)
            seen[("none" if fn is None else fn.__name__, suf)] += 1
        for (name, suf), n in seen.most_common():
            print("  %5d rows -> %-32s %s" % (
                n, name, "sufficient for GREEN" if suf
                else ("" if name == "none" else "runs, not sufficient alone")))
        for k, fn in HARNESSES.items():
            hit = sum(1 for r in rs if harness_for(r)[0] is fn)
            if hit == 0:
                print("  UNREACHABLE: %r maps to %s and no row dispatches to it"
                      % (k, fn.__name__))
        return 0
    if a.id:
        rs = [r for r in rs if r["id"] == a.id]
    green = red = capped = 0
    passed = failed = unchecked = broke = 0
    for r in rs:
        h = r.get("harness", "tool-to-build")
        if h == "AUDIT":
            # decided by docs/audits/<commit>-<id>.png, checked by the gate
            red += 1
            unchecked += 1
            state = "RED (audit not filed)"
        else:
            fn, sufficient = harness_for(r)
            if fn is None:
                red += 1
                unchecked += 1
                state = "RED (harness not implemented — tool-to-build)"
            else:
                # A HARNESS THAT RAISES MUST NOT TAKE THE LEDGER WITH IT.
                # There was no guard here, and `inc.py` is the first harness
                # that runs station code rather than reading documents: its
                # adversary made one `resolve` raise and `spec_check.py --id
                # INC-ACCIDENT` died with a traceback and printed NO LEDGER AT
                # ALL. One family's bug would have blanked the answer for all
                # 300 rows, which is the shape of the failure this whole file
                # exists to prevent -- a gate that stops reporting is worse
                # than a gate that reports red.
                #
                # The exception is caught, counted separately and printed with
                # its type, so a broken harness is loud and LOCAL. It is NOT
                # folded into "failed": a harness that crashed did not decide
                # anything about the station.
                try:
                    ok, note = fn(r)
                except Exception as e:                           # noqa: BLE001
                    red += 1
                    broke += 1
                    print("%-10s HARNESS RAISED %s: %s"
                          % (r["id"], type(e).__name__, str(e)[:120]))
                    continue
                if not ok:
                    red += 1
                    failed += 1
                    state = f"RED ({note})"
                elif sufficient:
                    green += 1
                    state = f"GREEN ({note})"
                else:
                    red += 1
                    passed += 1
                    state = (f"RED (checks pass, not sufficient alone: {note})")
        if a.id or state.startswith("RED") is False:
            print(f"{r['id']:10} {state}")
    total = len(rs)
    print(f"\n{green} GREEN / {red} RED / {capped} CAPPED of {total}")
    # THREE KINDS OF RED, AND CONFLATING THEM IS HOW A LEDGER LIES. This used
    # to print "N had a harness pass ... the rest nothing checked at all",
    # which was true when only one family had a harness and became FALSE the
    # moment all thirteen did: the remainder are rows that RAN a harness and
    # FAILED it, which is the opposite of unchecked. A summary line that ages
    # into a false statement is exactly the defect this project keeps finding.
    print("  %4d passed their harness but it is not sufficient for GREEN on "
          "its own" % passed)
    print("  %4d RAN a harness and FAILED it -- these are findings about the "
          "station or the spec, not gaps" % failed)
    print("  %4d have no harness at all" % unchecked)
    if broke:
        print("  %4d HARNESS CRASHED -- a bug in the harness, not a verdict "
              "about the row" % broke)
    print("GREEN moves only by implementing a harness in station/spec_harness/ "
          "and building the thing it checks. `--dispatch` shows which rows "
          "reach which harness, and names any that reaches nothing.")
    # The gate never fails CI for REDness — RED is the honest ledger — but it
    # DOES fail if the registry itself cannot be produced (drift/ambiguity).
    return 0


if __name__ == "__main__":
    sys.exit(main())
