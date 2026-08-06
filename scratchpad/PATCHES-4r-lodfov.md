# Session 4r — the LOD chain's lens (INV-600/601): patches for files I do not own

I own `station/lod.py` and `station/drum_ground.py`. Both are changed and committed:
`lod.py::FOV_DEG` is now read off `godot/scripts/player.gd` through
`budget.shipped_camera()` (**50.0 → 70.0**), and `drum_ground.py` takes its whole screen
model from `lod.py` by reference instead of restating it. `drum_dressing.py` already took
`FOV_DEG` from `drum_ground`, so it follows automatically and needs no code change.

Everything below is in a file I do not own. Item 1 is **required to keep CI green** — it is
not a suggestion.

---

## 1. `station/npc/body.py` — REQUIRED. A CI gate is red until this lands

**This is the fourth mirror of the screen model and it is the only one that asserts.** The
brief for this work listed three things that would break — the other LOD ladders,
the screenshot lenses, and `drum_walk.py`'s stale comment. `station/npc/body.py` was not on
that list and it is the one that actually fails.

`body.py:200` restates the screen model:

```python
FOV_DEG = 50.0
SCREEN_H = 1440
SCREEN_W = 2560
PIXEL_BUDGET = 1.5
SHADING_SAMPLE_PX = 1.0
```

and `body.py:5240` asserts it against `station/lod.py`:

```python
check(hull_lod.PIXEL_BUDGET == PIXEL_BUDGET
      and hull_lod.SCREEN_H == SCREEN_H
      and hull_lod.FOV_DEG == FOV_DEG
      and hull_lod.SHADING_SAMPLE_PX == SHADING_SAMPLE_PX,
      "the screen model matches station/lod.py -- two chains with two "
      "budgets pop differently in one frame")
check(abs(hull_lod.honest_from_m(0.37) - honest_from_m(0.37)) < 1e-9,
      "honest_from_m agrees with station/lod.py's")
```

**Measured, on the tree as committed:**

```
body.py FOV_DEG literal = 50.0
lod.py  FOV_DEG          = 70.0
body.py:5240 mirror check  hull_lod.FOV_DEG == FOV_DEG  -> False
body.honest_from_m(0.37) = 380.8644290824976
lod .honest_from_m(0.37) = 253.63908599739952
```

Both checks fail. `.github/workflows/validate.yml:668` runs `python3 body.py`, so the
`sbodies` step is red until this is applied.

**The assertion is right and its reason is right** — *"two chains with two budgets pop
differently in one frame"* is exactly the invariant INV-601 preserves. Do not delete it. The
value is what is wrong, and it is wrong for the same reason `lod.py`'s was: the NPC LOD chain
resolves NPC detail for a 50° camera while the player is given 70°, so it too holds a finer
body for ~50% further than its own 1.5 px budget entitles it to.

**The patch** — replace the five constants at `body.py:200`:

```python
# ---------------------------------------------------------------------------
# The screen model. TAKEN FROM station/lod.py, not restated. It used to be five
# literals held in agreement with lod.py's five by _selftest alone, which is a
# gate that reports the desync rather than one that prevents it -- and in 4r it
# duly went red the moment lod.py stopped choosing its lens and started reading
# it off godot/scripts/player.gd (50 -> 70; INV-600, INV-601). The NPC chain
# wants the shipped lens for exactly the reason the hull chain does: calibrating
# at 50 while shipping 70 delivers 1.5 x tan(25)/tan(35) = 1.00 px of deviation
# against a stated 1.5 px budget, so every body was held at a finer level ~50%
# further out than its own budget entitles it to.
# ---------------------------------------------------------------------------
import sys as _sys, os as _os                                  # if not already
if _STATION not in _sys.path:
    _sys.path.insert(0, _STATION)
import lod as _hull_lod                                        # noqa: E402

FOV_DEG = _hull_lod.FOV_DEG
SCREEN_H = _hull_lod.SCREEN_H
SCREEN_W = 2560           # 1440p is 16:9; used only for the horizontal FOV
PIXEL_BUDGET = _hull_lod.PIXEL_BUDGET
SHADING_SAMPLE_PX = _hull_lod.SHADING_SAMPLE_PX
```

`_STATION` already exists in `body.py` (it is used at line 5238 to import `lod` for the
mirror check itself), so the import is available; move it to module scope or repeat the
`sys.path` insert. `SCREEN_W` stays a literal here because `lod.py` does not carry one.

**What this costs.** Every NPC switch distance shortens by `tan(25)/tan(35) = 0.6660`, the
same factor as the hull chain, and for the same reason. **It has not been measured** — I do
not own the file and did not run its schedules. Whoever applies it should re-run
`python3 station/npc/body.py` and record what moved in the silhouette / profile / feature
tables, because that is a real content change to the crowd and it deserves the same
before/after treatment INV-600 gives the hull.

**If it cannot be applied this session**, the honest alternative is to delete the two mirror
checks *with a written reason saying the NPC chain is deliberately calibrated separately* —
never to put 50.0 back in `lod.py`, which is the value with no provenance.

---

## 2. `station/drum_walk.py:998` — a comment goes stale, and the claim it guards shrinks

```python
    # dominated by the RENDER's own LOD: `drum_ground.lod_table` switches to
    # lod1 at 198 m and the tile reaches 250 m, so its outer ring is drawn at
    # stride 2 while collision is uniform stride 1. Inside the lod0 radius the
    # two are built from identical lattice calls and must agree to nothing.
    lod0_m = dg.lod_table()[1]["switch_distance_m"]
```

The code needs no change — it reads the radius out of `drum_ground` rather than restating it,
which is why it keeps working. **Only the comment's "198 m" is now wrong: at 70° it is
132 m.** The strong identical-surface check therefore covers a smaller radius, which is a
weaker claim but still a true one, and the number of casts inside it drops.

**Patch:**

```python
    # dominated by the RENDER's own LOD: `drum_ground.lod_table` switches to
    # lod1 at 132 m (198 m before 4r moved the chain's calibration lens onto
    # the shipped camera -- INV-600) and the tile reaches 250 m, so its outer
    # ring is drawn at stride 2 while collision is uniform stride 1. Inside the
    # lod0 radius the two are built from identical lattice calls and must agree
    # to nothing.
```

Print the cast count beside it when re-running, since the sample the strong check runs over
shrinks with the radius.

---

## 3. `station/drum_dressing.py:2005` — a comment that names the old number

No code change: `FOV_DEG = dg.FOV_DEG` at line 223 already follows. But lines 2005–2007 say:

```python
# NOTE THE THREE FOVs THIS PROJECT HAS, because using the wrong one here would
# make the floor look derived and be wrong: the player's 70, the render shot's
# `export_scene.SHOT_FOV_DEG` = 46, and this module's own screen constant
# `drum_ground.FOV_DEG` = 50 (used for LOD pixel arithmetic only). 70 is the
# strictest of the three for this question -- a wider lens puts MORE very-near
# ground in the frame -- and it is the one a player actually looks through.
```

There are now **two** FOVs in this project, not three: the player's 70 (which
`drum_ground.FOV_DEG` now *is*) and the render shot's 46. **Patch:**

```python
# NOTE THE TWO FOVs THIS PROJECT HAS, because using the wrong one here would
# make the floor look derived and be wrong: the player's 70 and the render
# shot's `export_scene.SHOT_FOV_DEG` = 46. `drum_ground.FOV_DEG` used to be a
# third, an unsourced 50 used for LOD pixel arithmetic only; since 4r it is
# read off `player.gd` and is the same 70 as `NEAR_FOV_DEG` below (INV-600).
# 70 is the stricter of the two for this question -- a wider lens puts MORE
# very-near ground in the frame -- and it is the one a player looks through.
```

Also worth doing while in there: `NEAR_FOV_DEG = 70.0` at line 2009 is now a *third* copy of
the shipped lens in the same file that already imports it. It could become
`NEAR_FOV_DEG = FOV_DEG` with a note that the two questions — LOD pixel arithmetic and how
much near ground is in frame — happen to want the same lens because both are about the
player's screen. That is a judgement for the module's owner, not a defect.

---

## 4. `tools/export_scene.py` — `--orbit 6400,15,208` now renders lod1, and one committed frame is affected

No code change. `pick_hull_lod` reads the manifest and follows the chain, which is why it
needs none. But `tools/build_and_render.sh:37` takes the exterior frame at
`--orbit 6400,15,208`, whose nearest hull point is **4,271 m**, and that crosses lod1's new
switch distance of 3,997 m:

| | level | triangles |
|---|---|---|
| before | lod0 | 387,630 |
| after | **lod1** | **261,166** (−32.6%) |

`export_scene`'s own default `--orbit 9200,18,214` (near point 6,320 m) is **unchanged** — it
was already lod1 — and so is either camera's half distance (orbit 3200 → 1,518 m; orbit
4600 → 2,425 m), both inside lod0 before and after.

Any committed exterior frame taken at orbit 6400 is now a frame of a different mesh and should
be re-rendered or re-labelled. `--lod lod0` forces the old behaviour for a like-for-like
comparison, and INV-588 records that every craft frame in 4r already does so, which is why
`docs/aaa-scorecard.json` is unaffected.

---

## 5. Not a patch — two `lod.py` self-test failures that predate this work AND SURVIVE A REBUILD

`python3 station/lod.py` reports **96/98** on the tree as committed and **92/94** on
`fe83ca3` before any of my edits (the 4 extra checks are mine and all pass). The same two
fail in both:

```
FAIL: the chain's triangle model matches what the generator wrote (worst disagreement 4.268%)
FAIL: hull cost is 2 triangles per segment per ring gap at every level
      (ratios [2.0291, 2.0602, 2.1254, 2.1375, 2.1697, 2.1697, 2.3354, 2.506])
```

**My first reading of these was wrong and is recorded because the correction is the useful
part.** I wrote them up as a stale-artefact condition — the self-test compares against the
committed `lod_manifest.json`, and a gate that reads a committed file it cannot rebuild is
this project's own recorded defect (3z, `--gate-frames`). Then I ran `station/lod.py --build`
for an unrelated reason and **both still fail, on a manifest thirty seconds old**, with the
identical numbers. So it is a genuine divergence between `predicted_triangles()`'s model of
the generator and the generator, not a stale file. The ratios rising monotonically 2.029 →
2.506 along the chain is the signature of a fixed cost — end caps, components — becoming a
larger share of a shrinking lathe, which is exactly what `predicted_triangles`'s comment says
it accounts for and evidently under-counts.

Not mine to fix in this session, and it is pre-existing, but it should not be written off as
staleness a second time. Whoever picks it up: the disagreement is 4.268% at its worst and the
model is in `lod.predicted_triangles`.

---

## 6. Not a patch, but READ THIS BEFORE BELIEVING ANY LOD CHANGE — the chain reaches its consumers through a committed artefact

`station/generated/lod_manifest.json` is **tracked in git**, and it is what
`export_scene.pick_hull_lod` and `vista.lod_bands` actually read. `station/lod.py` is not
imported by either.

So after changing `FOV_DEG` and confirming the derivation, the report, and every self-test,
I rendered the exterior at `--orbit 6400,15,208` with `--lod auto` and it selected **lod0**,
citing `"from 0 m (binding schedule: silhouette at 1,502 m)"` — the *pre-fix* 50° number.
The committed manifest still said `"fov_deg": 50.0`. **The change was inert in the checkout
and nothing in the repository could have told me so**: `tools/wiring.py` would have found a
caller, the self-test was green, the report printed 70°.

I regenerated it (`python3 station/lod.py --build`, 12.8 s — it is *not* minutes, contrary to
what I assumed) and committed it, after which the same command selects lod1. CI runs
`--build` at `validate.yml:491` so CI was never wrong; the *checkout* was.

**The transferable rule, and it is the ninth-instance rule one level along:** a static scan
can tell you a caller exists and a self-test can tell you the derivation is right; only
running the shipped path tells you which *data* the caller read. When a derived constant feeds
a committed artefact, changing the constant is half the change.
