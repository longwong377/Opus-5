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


def godot_pids():
    out = subprocess.run(["pgrep", "-f", "godot.linuxbsd"],
                         capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.strip().isdigit()]


def main():
    import threading
    samples = []
    stop = threading.Event()

    def sampler():
        t0 = time.time()
        while not stop.is_set():
            for pid in godot_pids():
                kb = rss_kb(pid)
                if kb:
                    samples.append((time.time() - t0, pid, kb))
                    break
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
    if not samples:
        print("  NO RSS SAMPLES -- the child was never seen; this proves nothing")
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
