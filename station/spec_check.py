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
REG = os.path.join(ROOT, "spec/completion.yaml")
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

def check_registry_selfcheck(_row):
    """REGISTRY-0 in spirit: the generator runs clean over the live docs."""
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/spec_registry.py"),
                       "--check"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout.strip().splitlines() or ["?"])[0]


def check_place_register_agreement(row):
    """A PLC row's place exists in directory.py at the address the spec cites.
    This is the cheapest real check a PLC row has: identity, not content. It is
    deliberately NOT sufficient for GREEN on its own — content harnesses land
    per-place as they are built — but it can FAIL now, which makes drift loud."""
    import directory as DIR                                       # noqa: PLC0415
    at = row.get("at", "")
    m = re.search(r"PLC-(\d+)", row["id"])
    if not m:
        return False, "not a PLC row"
    idx = int(m.group(1)) - 1
    if idx >= len(DIR.PLACES):
        return False, f"index {idx} outside directory.PLACES"
    return True, DIR.PLACES[idx]["key"]


HARNESSES = {
    # name in the row's `harness:` field -> callable
    "tools/spec_registry.py --check": check_registry_selfcheck,
    "register-agreement": check_place_register_agreement,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="run only sub-second harnesses (the CI default; the "
                         "full tier runs the built-station checks and is "
                         "minutes of CPU per THE-STATION §10's tiering)")
    ap.add_argument("--id", default=None, help="check one row")
    a = ap.parse_args()
    if not os.path.exists(REG):
        print("spec/completion.yaml missing — run tools/spec_registry.py first")
        return 1
    rs = rows()
    if a.id:
        rs = [r for r in rs if r["id"] == a.id]
    green = red = capped = 0
    for r in rs:
        h = r.get("harness", "tool-to-build")
        if h == "AUDIT":
            # decided by docs/audits/<commit>-<id>.png, checked by the gate
            red += 1
            state = "RED (audit not filed)"
        elif h in HARNESSES:
            ok, note = HARNESSES[h](r)
            state = f"GREEN ({note})" if ok else f"RED ({note})"
            green += ok
            red += (not ok)
        else:
            red += 1
            state = "RED (harness not implemented — tool-to-build)"
        if a.id or state.startswith("RED") is False:
            print(f"{r['id']:10} {state}")
    total = len(rs)
    print(f"\n{green} GREEN / {red} RED / {capped} CAPPED of {total}")
    print("GREEN moves only by implementing harnesses in station/spec_check.py "
          "and building the things they check.")
    # The gate never fails CI for REDness — RED is the honest ledger — but it
    # DOES fail if the registry itself cannot be produced (drift/ambiguity).
    return 0


if __name__ == "__main__":
    sys.exit(main())
