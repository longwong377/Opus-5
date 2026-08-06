# Two edits the council-chamber judge could not make itself

Judge for `council_chamber`, session 4r. I do not own `station/council_chamber.py`
(the craft agent does) so these are written out rather than applied. Both are
measured, not preferences. Frames: `docs/judge-4r-council-verify-{half,entry,
before-half}.png`, re-rendered by me at HEAD `b13554f` and at the parent
`7b449c9` from a `git worktree`, every run confirming
`Vulkan 1.4.318 - Forward+ - llvmpipe`.

---

## 1 — `station/council_chamber.py:_selftest`, the budget check's own diagnostic
## under-reports the perforated sheet by 153x

The check that is cited as the P3 evidence prints

    f"({100 * len(t) / share:.0f}%), of which the perforated sheet is "
    f"{sum(1 for x in g if x == 'council_mesh'):,}"

`council_mesh` is **80** triangles in the assembled room — it is the lit face
behind the sheet. `mesh_grille()` emits **12,240** triangles and tags every one
of them `council_frame`:

    $ python3 -c "...; m=cc._M(); cc.mesh_grille(m); print(Counter(m.g))"
    {'council_frame': 12240}      total 12240
    council_mesh in the full room: 80

So the string reads "of which the perforated sheet is 80" for an object that is
41.2% of the room. This is the third instance this session of the defect the
same file names two assertions above it — *a group name is not a location* — and
it is in an assertion written this session. Suggested:

```diff
-          f"({100 * len(t) / share:.0f}%), of which the perforated sheet is "
-          f"{sum(1 for x in g if x == 'council_mesh'):,}"
+          f"({100 * len(t) / share:.0f}%), of which the perforated sheet is "
+          f"{_grille_tris():,}")
```

with `_grille_tris()` building `mesh_grille` into a scratch `_M()` and returning
`len(.t)`, which cannot drift from what the room actually emits. Three different
figures for this one object are in circulation — 12,320 (the round-3 JSON),
12,570 (the module comment at line 321), 80 (what the gate prints) — against a
measured **12,240**.

## 2 — `station/council_chamber.py:766` and `station/materials.py`: the blue
## speaking-fan slivers took the material that was already diagnosed as wrong

`wedge(..., "signage_panel__council_speak_blue", ...)` is new this session (252
triangles; the group does not exist at `7b449c9`). It resolves through the
longest-fragment rule to `signage_panel` — **the backlit sign at emission 3.0**
— which is the exact substitution `screen_wall`'s own docstring spends fourteen
lines explaining is wrong for the wall field, and which round 3 lists as a C3
finding *for the wall only*. The bench top got the same material and no finding.

Measured on my own before/after half frames, same camera, in the band the bench
top occupies (y 545–615 px): strong blue **1.75% -> 5.60%** of the band. At the
rubric's half distance (2.943 m) it reads as saturated emissive confetti lying
on a grey slab — see `docs/judge-4r-council-verify-half.png`, bench top.

There is no non-emissive blue bound in the interior scene today, which is why
this is a `materials.py` request and not a one-line fix here: an inlay 4 mm
proud of a bench top wants an albedo-blue with a specular response, not an
emitter. Until that exists, the honest interim is to drop the slivers to
`council_speak_inlay` (already bound, already the fan's own material) and record
the colour loss, rather than ship a light where the reference shows paint.

## 3 — not a patch, a correction to the record

`ee84605`'s message and the module comments at lines 154–156 and 1673–1676 say
the pre-fix fan was measured at *"the narrowest 32 mm against a nominal 620 mm
(5%), and the widest was 19.1x the narrowest"*. The built mesh does not produce
that. Measured on the **actual parent-commit module** with the new gate's own
method:

    narrowest 0.1017 m   widest 0.6401 m   widest/narrowest 6.29   22 of 30 short

32 mm is `2*hw*sin(a)` — the algebraic model in the comment — and the model is
itself wrong twice over: the true perpendicular width of the old quad is
`2*hw*sin^2(a)` = 1.7 mm at the narrowest blade, and the 102 mm actually
measured is mostly the blade's own 100 mm thickness seen edge-on. The file's
own negative control prints the right number (0.101 m), so the comment
contradicts the assertion beside it. **22 of 30 is correct and the fix is
correct**; only the two quoted figures are not.
