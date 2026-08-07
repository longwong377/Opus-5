"""Does the SHIPPED collision builder put a floor where the room is?

Not a scan and not the gate: this calls `deck.build_collision` -- the same
function `tools/export_station.py` writes `<stem>_collision.glb` from, which is
what `walk.gd` and `stream.gd` load -- and then stands a body in the room and
casts the way a body falls.

`customs_north`'s module is 17.50 m across. Its shell was 12.31 m. So a player
8.0 m from the room's own doorway bearing was, in the build that shipped, over
nothing: the render mesh said floor, the collision said void, and a body there
falls outward under spin gravity for as long as it likes.

THE FIRST VERSION OF THIS SCRIPT MEASURED THE WRONG DECK AND SAID SO CLEARLY,
which is the only reason it was caught: `build_collision` with `z_m=None` takes
`z_clusters(...)[0]`, the BUSIEST cluster, which on blue/0/0 is z = 7115 --
the docking bays. `customs_north` is at 7460. Every probe came back MISSING and
the before/after triangle counts were identical, because neither build
contained the room at all. A probe that reports "nothing there" for a reason
that has nothing to do with the change is the vacuous A/B this project already
has a rule about. The cluster is now passed explicitly.

Run it at HEAD and at the commit before the fix. `git diff` the two logs.
"""
import math
import os
import sys

sys.path.insert(0, "station")

import collision as C        # noqa: E402
import deck as D             # noqa: E402
import directory as dr       # noqa: E402
import interior as it        # noqa: E402

KEY = "customs_north"
XS = (0.0, 4.0, 6.0, 7.0, 8.0, 8.6)


def _floor_under(v, t, r, a, z):
    """A body's head at `r - 1.9` on bearing `a`, casting the way it falls.

    UP IS INWARD on a spun ring, so "down" is +radial. Both directions are cast
    and both are reported: a probe that only looks one way cannot tell "there
    is no floor" from "I aimed at the ceiling".
    """
    top = r - 1.9
    o = (top * math.cos(a), top * math.sin(a), z)
    out = C.cast(o, (math.cos(a), math.sin(a), 0.0), v, t)
    inw = C.cast(o, (-math.cos(a), -math.sin(a), 0.0), v, t)
    return out, inw


if __name__ == "__main__":
    schema, profile = it.load()
    p = next(q for q in dr.PLACES if q["key"] == KEY)
    z = p["z_m"]
    v, t, meta = D.build_collision(schema, profile, p["sector"], p["ring"],
                                   p["deck"], z_m=z, props=False)
    r = meta["floor_r_m"]
    print(f"build_collision {p['sector']}/{p['ring']}/{p['deck']} at z={z:.0f}"
          f": {len(t):,} triangles, floor r={r:.3f} m")

    # NO BOUNDING BOX OF THE EMITTED MESH HERE, DELIBERATELY. The first
    # version printed one and it read "-664.02 .. +663.55 m, 1327.57 m wide"
    # in BOTH builds -- which is 2*pi*211.5, the whole ring corridor, because
    # the corridor runs THROUGH the room's z band and no filter over z can
    # separate the two. It was identical before and after and looked like a
    # measurement. The casts below are the measurement; the room's own arc is
    # what `deck.py --shell-fit` prints, per room, from the same builder.
    a0 = math.radians(p["angle_deg"])
    for x in XS:
        a = a0 + x / r
        out, inw = _floor_under(v, t, r, a, z)
        print(f"  {KEY} at x={x:+5.2f} m, z={z:.0f}: "
              + (f"floor {out:.3f} m below the head" if out is not None
                 else "NO FLOOR")
              + (f", ceiling {inw:.3f} m above" if inw is not None
                 else ", no ceiling either -- outside the shell"))
