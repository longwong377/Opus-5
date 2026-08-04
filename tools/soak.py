#!/usr/bin/env python3
"""A long walk with RSS sampled from outside, to answer: does it leak?

WHY FROM OUTSIDE. The engine reporting its own memory is the engine's opinion
of its memory; `ps` on the process is the number the operating system will kill
it for. This samples RSS of the Godot child every SAMPLE_S and reports the
trend, so a slow leak shows as a rising floor rather than as a crash an hour in.

WHY A LONG WALK RATHER THAN AN IDLE SCENE. An idle scene allocates nothing and
soaks nothing. This drives a real body over real physics frames on a real deck
with its crowd, streaming nothing -- so what grows here is physics, script and
node churn, which is the half a monolithic build can leak.

P0a asks for sixty minutes. At the 5.48 ms/frame measured by tools/frametime.py
that is ~660,000 physics frames.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "station"))
import walkable as W                                             # noqa: E402

SAMPLE_S = 20.0
FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 660_000


def rss_kb(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for ln in f:
                if ln.startswith("VmRSS:"):
                    return int(ln.split()[1])
    except OSError:
        return None
    return None


# A GODOT PROCESS HOLDING A STATION IS HUNDREDS OF MEGABYTES. Anything smaller
# is a wrapper, a shell or `nice` -- and the first run of this tool sampled
# exactly that: 274 samples, "peak 6 MB, drift +0.0%", which reads as a clean
# bill of health and is a measurement of /bin/sh. A floor makes that failure
# loud instead of plausible.
MIN_PLAUSIBLE_KB = 50 * 1024


def godot_pid():
    """The Godot process, chosen by LARGEST RSS rather than by pgrep order.

    `pgrep -f godot.linuxbsd` matches the wrapper as well as the engine, and
    taking [0] takes whichever the kernel lists first. The engine is the big
    one, always, by two orders of magnitude.
    """
    out = subprocess.run(["pgrep", "-f", "godot.linuxbsd"],
                         capture_output=True, text=True).stdout
    best, best_kb = None, 0
    for x in out.split():
        if not x.strip().isdigit():
            continue
        kb = rss_kb(int(x)) or 0
        if kb > best_kb:
            best, best_kb = int(x), kb
    return best, best_kb


def main():
    import threading
    samples = []
    stop = threading.Event()

    def sampler():
        t0 = time.time()
        while not stop.is_set():
            pid, kb = godot_pid()
            if pid and kb >= MIN_PLAUSIBLE_KB:
                samples.append((time.time() - t0, pid, kb))
            stop.wait(SAMPLE_S)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    t0 = time.time()
    d = W.walk_deck("blue", 0, 0, W.godot_binary(), timeout=5400,
                    z_m=7120.0, traverse=FRAMES)
    stop.set()
    wall = time.time() - t0

    print(f"\nsoak: {FRAMES:,} frames, {wall / 60.0:.1f} min wall")
    print(f"  traverse_m={d.get('traverse_m')} offfloor={d.get('offfloor')} "
          f"fell={d.get('fell')} error={d.get('error', '-')}")
    if d.get("error"):
        print(f"  THE WALK DID NOT FINISH: {d['error']}")
        print("  RSS below is over however long it DID run, and the soak's own "
              "claim -- that an hour of walking does not leak -- is NOT made.")
    if not samples:
        print(f"  NO RSS SAMPLES ABOVE {MIN_PLAUSIBLE_KB // 1024} MB -- the "
              f"engine was never seen. THIS PROVES NOTHING; do not read the "
              f"absence of drift as the absence of a leak.")
        return 1
    ts = [s[0] for s in samples]
    kb = [s[2] for s in samples]
    n = len(kb)
    first, last = kb[: max(1, n // 10)], kb[-max(1, n // 10):]
    f_avg, l_avg = sum(first) / len(first), sum(last) / len(last)
    print(f"  {n} RSS samples over {ts[-1] / 60.0:.1f} min")
    print(f"  peak {max(kb) / 1024.0:,.0f} MB   min {min(kb) / 1024.0:,.0f} MB")
    print(f"  first decile avg {f_avg / 1024.0:,.0f} MB   "
          f"last decile avg {l_avg / 1024.0:,.0f} MB   "
          f"drift {(l_avg - f_avg) / 1024.0:+,.0f} MB "
          f"({100.0 * (l_avg - f_avg) / max(f_avg, 1):+.1f}%)")
    print("  A LEAK IS A RISING FLOOR, not a high peak. Judge the drift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
