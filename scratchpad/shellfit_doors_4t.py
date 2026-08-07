"""Which rooms get a door, on every z-cluster on the station.

`deck_plan`'s door-fit test reads the room's width, and session 4t changed
where that width comes from. The brief's warning is exact: "widening it changes
which corridor phase wins, which changes which rooms get a door -- `--sweep`
reports `unopened` and it must not go up."

This asks that question and nothing else, so it can be run in a worktree next
to other agents: no geometry is assembled, no artefact is written, and
`station/generated/scene/*` is not touched. Print one line per cluster and a
station total; diff two runs.
"""
import os
import sys

sys.path.insert(0, "station")

import deck as D             # noqa: E402
import directory as dr       # noqa: E402
import interior as it        # noqa: E402

if __name__ == "__main__":
    schema, profile = it.load()
    seen, tot_open, tot_unopen, rows = set(), 0, 0, []
    for p in dr.PLACES:
        if p.get("deferred"):
            continue
        key = (p.get("sector"), p.get("ring"), p.get("deck"))
        if None in key or key in seen:
            continue
        seen.add(key)
        sec, ring, dk = key
        for z in D.z_clusters(sec, ring, dk):
            try:
                dp = D.deck_plan(schema, profile, sec, ring, dk, z_m=z)
            except Exception as e:                              # noqa: BLE001
                rows.append(f"{sec}/{ring}/{dk} z={z:.0f}  RAISED "
                            f"{str(e)[:60]}")
                continue
            opened = sorted(q["key"] for q, _d, _x in dp["rooms"])
            unop = sorted(k for k, _dx, _hw in dp["unopened"])
            mdx = max((abs(dx) for _q, _d, dx in dp["rooms"]), default=0.0)
            tot_open += len(opened)
            tot_unopen += len(unop)
            rows.append(f"{sec}/{ring}/{dk} z={z:.0f}  open={len(opened)} "
                        f"max|dx|={mdx:.2f}  unopened={unop}  {opened}")
    for r in rows:
        print(r)
    print(f"TOTAL {tot_open} rooms opened, {tot_unopen} unopened, "
          f"{len(rows)} clusters")
