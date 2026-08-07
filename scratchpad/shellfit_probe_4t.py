"""Does the SHIPPED collision builder put a floor where the room is?

Not a scan and not the gate: this calls `deck.build_collision` -- the same
function `tools/export_station.py` writes `<stem>_collision.glb` from, which is
what `walk.gd` and `stream.gd` load -- and then stands a body in the room and
casts the way a body falls.

`customs_north`'s module is 17.50 m across. Its shell was 12.31 m. So a player
8.0 m from the room's own doorway bearing was, in the build that shipped, over
nothing: the render mesh said floor, the collision said void, and a body there
falls outward under spin gravity forever.

Run it at HEAD and at the commit before the fix. The answer is a distance or
the word MISSING.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "station"))
sys.path.insert(0, "station")

import collision as C        # noqa: E402
import deck as D             # noqa: E402
import interior as it        # noqa: E402

PROBES = [("customs_north", 40.0, x) for x in (0.0, 4.0, 6.0, 8.0, 8.6)]

if __name__ == "__main__":
    schema, profile = it.load()
    v, t, meta = D.build_collision(schema, profile, "blue", 0, 0, props=False)
    print(f"build_collision blue/0/0: {len(t):,} triangles, "
          f"floor r={meta['floor_r_m']:.3f} m")
    r = meta["floor_r_m"]
    import directory as dr
    for key, _b, x in PROBES:
        p = next(q for q in dr.PLACES if q["key"] == key)
        a = math.radians(p["angle_deg"]) + x / r
        top = r - 1.9                     # head height; up is inward
        o = (top * math.cos(a), top * math.sin(a), p["z_m"])
        d = (-math.cos(a), -math.sin(a), 0.0)
        h = C.cast(o, d, v, t)
        print(f"  {key} at x={x:+5.2f} m from its bearing, z={p['z_m']:.0f}: "
              + (f"floor {h:.3f} m below the head" if h is not None
                 else "MISSING -- nothing under the body"))
