"""CPU frame time on a real deck, measured as a DIFFERENCE so start-up cancels.

MEASURED 4l, blue/0/0 z7120 -- 1,542,960 triangles, 657 meshes, 84 baked bodies:

    1800 frames   129.7 s wall   125.93 m traversed   offfloor 0/1800
    5400 frames   149.4 s wall   377.94 m traversed   offfloor 0/5400
    -> (149.4 - 129.7) / 3600 = 5.48 ms/frame

Against `budget.DRAW["frame_ms"]` = 16.667 (1440p60) that is **3.0x headroom on
the CPU half**. P0a asked for exactly this number "with the GPU half unknown in
the same line", and it is: --headless is a NULL RENDERING DRIVER, so nothing
here touches rasterisation, shadows, SSAO or glow. A GPU number needs target
hardware and this container has none.

Both runs walked at 4.2 m/s (125.93/30 s and 377.94/90 s), which is
`player.gd`'s exported speed -- so the 1.46 m/s measured on the 960 m
`plantroom_bay` walk earlier in 4l was route-specific (turns, waypoint
tolerances, or the corridor crowd) and NOT the body's base speed. The far-room
frame budgets in docs/room-reach-4k.md section 7 are pessimistic by up to 2.9x
because of it.


One timed run measures build + engine start + N frames, and the build alone is
minutes -- so a single run divided by N is mostly not frame time. Two runs at
different frame counts, same deck, same crowd: the difference is the frames and
nothing else.

HEADLESS MEASURES THE CPU HALF ONLY. Godot's --headless is a null rendering
driver, so this is physics, script, NPC and collision cost per frame with the
GPU half UNKNOWN. Said here rather than implied.
"""
import sys, time
sys.path.insert(0, "/home/user/Opus-5/station")
import walkable as W

g = W.godot_binary()
runs = []
for frames in (1800, 5400):
    t0 = time.time()
    d = W.walk_deck("blue", 0, 0, g, timeout=3000, z_m=7120.0, traverse=frames)
    dt = time.time() - t0
    runs.append((frames, dt, d))
    print(f"  {frames:6d} frames   {dt:7.1f} s wall   "
          f"traverse_m={d.get('traverse_m')}  offfloor={d.get('offfloor')}  "
          f"actors={d.get('actors') or d.get('bodies') or '?'}", flush=True)

(f1, t1, d1), (f2, t2, d2) = runs
per = (t2 - t1) / (f2 - f1) * 1000.0
print(f"\n  CPU frame time = ({t2:.1f} - {t1:.1f}) s / ({f2} - {f1}) frames "
      f"= {per:.2f} ms/frame")
print(f"  budget is 16.67 ms (1440p60). CPU half only -- GPU half UNKNOWN.")
print(f"  headroom: {16.667/per:.1f}x" if per > 0 else "")
