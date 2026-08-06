# PATCHES — judge, `docking_bay_interior`, session 4r

I am the judge for this subsystem and I did not edit `station/docking_bay.py`. One change is
owed to it and one comment is wrong. Both are written out here with the measurement that
justifies them, per the agent rules.

---

## 1. The budget assertion's negative control is an assertion that the room is ≥ 30,001 triangles

`station/docking_bay.py:_selftest`, the block headed *WHAT ONE BAY COSTS, AGAINST A DERIVED
SHARE*:

```python
    check(f"one bay fits the interior structure frustum ({len(t):,} tri, "
          f"{100 * len(t) / _allow:.1f}% of {_allow:,})",
          len(t) <= _allow, f"{len(t):,} of {_allow:,}")
    check("...and the bound can fail", not (2 * len(t) <= _allow),
          f"twice this bay ({2 * len(t):,}) is still inside {_allow:,}, so "
          f"the bound is not bounding anything")
```

`_allow` is `budget.INTERIOR['visible_set_tris'] = 60,000`. `not (2 * len(t) <= 60000)` is
`len(t) > 30000`. So the control is arithmetically the sentence **"this room is at least
30,001 triangles"**, and the selftest goes red the moment the room gets smaller.

**Measured, enumerated across the threshold** (`scratchpad/judge-db/prefix_assert.log` and the
run below):

| triangles | `...and the bound can fail` |
|---|---|
| 32,811 — HEAD | PASS |
| 30,001 | PASS |
| 30,000 | **FAIL** |
| 29,999 | **FAIL** |
| 22,571 — the room three commits ago, at `a3d414e` | **FAIL** |

The 22,571 row is the point. That was the shipped room, it was not a defect, it was comfortably
inside the bound, and this control calls it a failure.

**Why it matters now rather than later.** The same round's own `major P3` finding says the way
to P4 is *"a LOD chain whose switch distances are derived from a measurable error"*, and notes
that all 13 girders are drawn in full at 138 m where their 0.24 m web plates are 0.2 px. Any LOD
that takes the room under 30,000 triangles breaks this assertion. The gate that is supposed to
defend the budget currently punishes the work that would defend it.

**And it is the shape of a lesson this file records having just learned**, sixty lines further
down, about the non-manifold count:

> THE PROPERTY, NOT THE COUNT … This read `len(nm) == _INHERITED_NON_MANIFOLD` with the constant
> pegged at 30, and it FAILED at 26 … A second copy of a computed number goes stale in the
> direction of an improvement just as readily as in the direction of a regression.

That is exactly this. The lesson was applied to the instance and not to the rule — which is the
thing `CLAUDE.md` names as *"a fix applied to an instance and not to the rule is a fix that will
be needed again"*.

**The fix — assert the property, not this room's size.** What the control is for is *"the bound
is a real bound and not a tautology"*, and that is provable without referring to `len(t)` at all:
feed the bound a count that must fail it.

```python
    check(f"one bay fits the interior structure frustum ({len(t):,} tri, "
          f"{100 * len(t) / _allow:.1f}% of {_allow:,})",
          len(t) <= _allow, f"{len(t):,} of {_allow:,}")
    # NEGATIVE CONTROL -- the bound has to reject something, and the something
    # must not be "this room, doubled". `not (2 * len(t) <= _allow)` reads as a
    # control and is arithmetically `len(t) > 30,000`: it FAILS on the 22,571
    # triangles this room shipped at a3d414e, and it will fail again on the
    # first LOD level the P3 finding asks for. Hand the predicate a count
    # instead, so the control says something about the BOUND rather than about
    # the room's current size.
    def _fits(n):
        return n <= _allow
    check("...and the bound rejects a count over it",
          _fits(_allow) and not _fits(_allow + 1),
          f"the bound admits {_allow + 1:,} against an allowance of {_allow:,}")
```

That control fires for the right reason, cannot go stale in either direction, and survives every
LOD level the room will ever have. If a *proportion* of the allowance is also wanted — P4 asks
for ≤ 70% — assert it as its own named check against `0.70 * _allow`, where a reduction moves the
number the right way.

---

## 2. `_selftest` says "all 24 girders"; there are 13

Same block:

```
    # eye at the mouth holds all 140 m and all 24 girders in one frustum.
```

`BAY_LEN_M = 140.0`, `GIRDER_PITCH_M = 11.0` → **13** girders. 24 is `BAY_COUNT`, the number of
docking bays on the station, which is a different quantity of the same name — the exact
`AAA-STANDARD.md` F2 failure mode ("a quantity conflated with a different quantity of the same
name — 42 cargo *bays* modelled as 42 external cargo *modules*"). The arithmetic the assertion
performs is unaffected; only the comment is wrong. `GIRDER_BAYS = 10` is a third quantity with a
similar name (panels across the span), which is why this is worth correcting rather than leaving.

Suggested: `all 140 m and all 13 girders`.

---

## Not a patch — recorded so the next reader does not re-derive it

**The half-distance camera is aimed 27.7° above horizontal.** `--eye 0.0,1.70,21.085 --target
0.0,9.0,35.0` is `atan(7.3 / 13.915) = 27.7°` up from a standing eye, so at half distance the
frame is ~90% ceiling and the deck is almost out of shot. The ceiling is the half this session
rebuilt. The derivation that produced it (subject = one 42 m girder bay, half of
`21.0 / tan(37.045°) = 27.83 m`) is arithmetically correct and defensible, and the frame is
genuine — I re-rendered it at HEAD and it reproduces to a maximum channel difference of 9/255.

It is still worth a second camera, and the second camera does not change the score: re-rendered
at the same 13.92 m with a **level** gaze (`--target 0.0,1.70,35.0`,
`docs/judge-4r-dockingbay-half-level.png`), the bottom 45% of the frame is `bay_deck`, which is
**two triangles over 21.6 × 140.0 m** and is the largest unbroken face in the room both before
and after this session's work. A craft frame whose aim point excludes the flattest surface in the
subject is not wrong, but it is not the whole answer either.
