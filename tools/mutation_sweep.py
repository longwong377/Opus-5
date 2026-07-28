#!/usr/bin/env python3
"""Find assertions that cannot fail, by making them fail.

This project's single most expensive recurring defect is not a wrong number --
it is a *guarded-looking* number. `CONTRIBUTING.md` records the pattern twice
already: `TRUSS_COUNT == sm.get("count", TRUSS_COUNT)` defaulted to the value
under test, and the tram's "measured proportion" checks were algebraic
identities restating their own inputs. Both read as coverage. Neither could
ever have failed. A suite of 448 assertions is worth exactly as much as the
subset of it that a defect can trip, and nothing in a passing run distinguishes
the two.

So this is the empirical version of the question "is my test suite real?".
For every module-level numeric constant in every module that carries a
`_selftest()`, it perturbs the constant, re-runs that module's suite in a fresh
subprocess, and asks whether anything noticed. A constant nothing notices is
either unguarded, or guarded only by assertions that restate it.

WHAT A FINDING MEANS -- and it is not always a defect:

  UNGUARDED   perturbing it produced no new failure and no error. Either the
              constant is load-bearing and untested, or it is genuinely
              cosmetic. The tool cannot tell those apart and does not try; it
              names them so a human decides.
  GUARDED     at least one assertion failed. What you want.
  CRASH       the mutant raised. That counts as guarded -- an exception is a
              louder failure than an assertion -- but it is reported separately
              because a crash usually means an unvalidated input rather than a
              deliberate check.

The sweep is deliberately NOT a CI gate. It costs about fifty minutes of CPU
and its output needs judgement, both of which are wrong for a per-push hook.
Run it when a module's assertions have been rewritten, or when a suite has
grown a lot without finding anything.

Usage:
    python3 tools/mutation_sweep.py                  # everything
    python3 tools/mutation_sweep.py interior tram    # named modules only
    python3 tools/mutation_sweep.py --factor 1.5     # harsher perturbation
"""
import argparse
import concurrent.futures as cf
import importlib
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATION = os.path.join(os.path.dirname(HERE), "station")

# Modules carrying a `_selftest()` that returns a failure count as its exit
# code. `interior_kit` is excluded: its self-test prints a mesh summary rather
# than a pass count, so the harness cannot read a verdict off it.
MODULES = (
    "interior", "drum_ground", "tram", "core_tube", "zocalo",
    "docking_bay", "signage", "command_control", "council_chamber",
)

# Constants that are knobs on the harness rather than facts about the station.
# Perturbing them changes how finely something is sampled, not what it is, so
# an unchanged verdict is the correct answer rather than a finding. Every entry
# needs a reason; this list is where a real defect goes to hide.
EXEMPT = {
    # Tessellation and sampling rates. A coarser mesh of the same shape should
    # still pass every assertion about the shape, and if it does not, that is a
    # separate bug about assertions being tuned to a sample count.
    "SEG_DEG", "Z_STEP", "SAMPLES", "PREVIEW_W", "PREVIEW_H",
}


def _worker(payload):
    """Run one mutant. Separate process, because a module's constants are
    module state and 150 mutants in one interpreter would contaminate."""
    mod, const, value, timeout = payload
    driver = (
        "import io,contextlib,sys,json\n"
        f"import {mod} as M\n"
        f"setattr(M,{const!r},{value!r})\n"
        "buf=io.StringIO()\n"
        "try:\n"
        "    with contextlib.redirect_stdout(buf): M._selftest()\n"
        "    out=buf.getvalue()\n"
        "    line=[l for l in out.splitlines() if 'passed' in l]\n"
        "    n=line[-1].split('/') if line else None\n"
        "    ok=int(n[0]) if n else -1\n"
        "    tot=int(n[1].split()[0]) if n else -1\n"
        "    print(json.dumps({'ok':ok,'total':tot,'crash':None}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':-1,'total':-1,'crash':f'{type(e).__name__}: {e}'}))\n"
    )
    try:
        r = subprocess.run([sys.executable, "-c", driver], cwd=STATION,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(module=mod, const=const, value=value, verdict="TIMEOUT",
                    detail=f"exceeded {timeout}s")
    tail = [l for l in r.stdout.strip().splitlines() if l.startswith("{")]
    if not tail:
        # A mutant that kills the interpreter outright still counts as noticed.
        return dict(module=mod, const=const, value=value, verdict="CRASH",
                    detail=(r.stderr.strip().splitlines() or ["no output"])[-1][:200])
    d = json.loads(tail[-1])
    if d["crash"]:
        return dict(module=mod, const=const, value=value, verdict="CRASH",
                    detail=d["crash"][:200])
    return dict(module=mod, const=const, value=value, verdict=None,
                ok=d["ok"], total=d["total"])


def baseline(mod, timeout):
    r = _worker((mod, "__name__", mod, timeout))
    return r


def constants(mod):
    sys.path.insert(0, STATION)
    cwd = os.getcwd()
    os.chdir(STATION)
    try:
        M = importlib.import_module(mod)
    finally:
        os.chdir(cwd)
    out = []
    for k, v in vars(M).items():
        if not k.isupper() or k in EXEMPT:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        if v == 0:
            continue          # no multiplicative perturbation exists
        out.append((k, v))
    return sorted(out)


def perturb(v, factor):
    """Ints move by at least one whole unit; a count of 3 scaled by 1.25 and
    floored is still 3, which would report every count in the project as
    unguarded."""
    if isinstance(v, int):
        return max(1, int(round(v * factor))) if abs(v * (factor - 1)) >= 1 else v + 1
    return v * factor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules", nargs="*", default=None)
    ap.add_argument("--factor", type=float, default=1.25,
                    help="multiplicative perturbation (default 1.25)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()

    mods = args.modules or list(MODULES)
    t0 = time.time()

    print(f"baselines for {len(mods)} modules")
    base = {}
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for m, r in zip(mods, ex.map(lambda m: baseline(m, args.timeout), mods)):
            if r.get("verdict"):
                print(f"  {m}: BASELINE {r['verdict']} -- {r['detail']}")
                continue
            base[m] = r
            print(f"  {m}: {r['ok']}/{r['total']}")

    jobs = []
    for m in base:
        for k, v in constants(m):
            jobs.append((m, k, perturb(v, args.factor), args.timeout))
    print(f"\n{len(jobs)} mutants at x{args.factor}, {args.jobs} at a time\n")

    rows = []
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for i, r in enumerate(ex.map(_worker, jobs), 1):
            b = base[r["module"]]
            if r["verdict"] is None:
                # Fewer total assertions can mean a mutant changed how many
                # ran (a count constant drives a per-item loop). Compare
                # FAILURES, not passes, or that reads as an improvement.
                mf = r["total"] - r["ok"]
                bf = b["total"] - b["ok"]
                r["verdict"] = "GUARDED" if mf > bf else "UNGUARDED"
                r["detail"] = f"{r['ok']}/{r['total']} (baseline {b['ok']}/{b['total']})"
            rows.append(r)
            print(f"  [{i:3d}/{len(jobs)}] {r['module']}.{r['const']} "
                  f"-> {r['verdict']}")

    print(f"\n{'=' * 72}\nmutation sweep: {len(rows)} mutants in "
          f"{time.time() - t0:.0f}s\n{'=' * 72}")
    by = {}
    for r in rows:
        by.setdefault(r["verdict"], []).append(r)
    for v in ("UNGUARDED", "TIMEOUT", "CRASH", "GUARDED"):
        rs = by.get(v, [])
        print(f"\n{v}: {len(rs)}")
        if v == "GUARDED":
            continue          # the ones that work need no listing
        for r in sorted(rs, key=lambda r: (r["module"], r["const"])):
            print(f"  {r['module']}.{r['const']} = {r['value']!r}"
                  f"  -- {r.get('detail', '')}")

    n_un = len(by.get("UNGUARDED", []))
    print(f"\n{len(rows) - n_un}/{len(rows)} constants are noticed by their "
          f"own module's assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
