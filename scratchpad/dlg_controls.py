"""Negative controls for the hardened DLG harness.

Each one removes exactly one mechanism and must change exactly the row that
names it. Run from the repo root: python3 scratchpad/dlg_controls.py
"""
import os
import sys

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "station"))

import dialogue as dlg                                            # noqa: E402
from spec_harness import dlg as H                                 # noqa: E402

ROWS = {n: {"id": "DLG-%03d" % n, "at": "docs/spec/PEOPLE.md:%d" % ln}
        for n, ln in ((1, 1022), (2, 1032))}


def run(n):
    ok, msg = H.check(ROWS[n])
    return ok, msg


def show(label, n):
    ok, msg = run(n)
    print("  %-58s %s" % (label, "GREEN" if ok else "RED"))
    print("      %s" % msg[:400])


print("baseline:")
show("DLG-01 as built", 1)
show("DLG-02 as built", 2)

print("\ncontrol 1 -- the critic's filler, which the OLD harness passed:")
_keep = dlg.cast_lines
dlg.cast_lines = lambda row: tuple(
    "%s says thing number %d." % (
        (row if isinstance(row, str) else row["who"]), i) for i in range(75))
show("cast_lines -> '<name> says thing number i.'", 1)
dlg.cast_lines = _keep

print("\ncontrol 2 -- the same content with the MASK disabled (the old count):")
_m = H._mask
H._mask = lambda d, r, l: l
show("_mask is the identity, i.e. count renderings", 1)
H._mask = _m

print("\ncontrol 3 -- the second clause removed, so the x2 is the affix again:")
_b = dlg.ROLE_CLAUSE_B
dlg.ROLE_CLAUSE_B = {}
show("ROLE_CLAUSE_B emptied", 2)
dlg.ROLE_CLAUSE_B = _b

print("\ncontrol 4 -- a THIRD species frame, which must buy nothing:")
_f = dict(dlg.SPECIES_FRAME)
dlg.SPECIES_FRAME = {k: tuple(v) + ("Put it this way, %s: {say}" % k,)
                     for k, v in _f.items()}
show("SPECIES_FRAME padded 2 -> 3 per species", 2)
dlg.SPECIES_FRAME = _f

print("\ncontrol 5 -- the Tier-1 wiring removed from the shipped path:")
_bc = dlg.behind_counter
_ch = dlg.cast_here
def _reach():
    seen = set()
    for pk in dlg.cast_at():
        for h in (3.0, 9.0, 13.0, 21.0):
            w = dlg.behind_counter(pk, dlg.World(hour=h))
            if w is not None and dlg.cast_by_name(w.name) is not None:
                seen.add(w.name)
    return len(seen)


print("      with the wiring:    behind_counter casts %d of the 50" % _reach())
dlg.cast_here = lambda *a, **k: None
print("      wiring withheld:    behind_counter casts %d of the 50" % _reach())
show("cast_here -> None, so behind_counter casts nobody named", 1)
dlg.cast_here = _ch
dlg.behind_counter = _bc
