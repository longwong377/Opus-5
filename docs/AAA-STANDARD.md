# The AAA Standard

The owner's brief is a feeling: *"utterly perfect, visually beautiful, with every single thing
done at AAA quality — from textures to physics to detail to the npcs to the
crowdedness/isolation to the mood to the ambiance to the alienness to the sound to the scale to
the interactability to the accuracy vs the real thing."*

A feeling cannot be reviewed. This file turns it into four scored dimensions, a bar, a stopping
rule, and a per-subsystem checklist, so that a harsh critic and a build agent can disagree about
a specific descriptor rather than about taste.

## Why a rubric at all — the termination problem

A sufficiently harsh critic always finds something. That is not a flaw in the critic; it is what
harshness means. So "keep going until it is AAA" is a loop with no exit, and on a project that
runs on a 6-hourly trigger with a ~5-agent workflow cap it is the single most expensive failure
mode available: one subsystem consumes unbounded budget and the other forty never get built.

The rubric exists to make three things true:

1. **A finding must name a descriptor.** A critic who cannot point at the written descriptor a
   score drops to has produced a preference, not a finding. Preferences are recorded and never
   block.
2. **There is a defined bar**, and reaching it is a fact about the artefact rather than about the
   reviewer's mood.
3. **There is a hard round cap.** After it, the subsystem is CAPPED with a written reason and the
   shortfall becomes a decision the owner makes once, rather than another review round.

## The four dimensions

Every subsystem is scored 0–5 on each of four dimensions. Scores are integers. The descriptors
below are written for *this* project — most are anchored to something that actually happened in
it, cited by session number from `STATE.md` — because "polished" and "professional" are exactly
the words that let a review round end without a decision.

Two rules apply to all four:

- **Score to the lowest descriptor that is fully true.** If a subsystem satisfies 4 in every
  respect but one clause of 3 is false, it is a 3, and the finding names that clause.
- **A score of 4 or 5 requires evidence**: a render path, a measured number, an assertion name, or
  a reference citation. A 4 with no evidence is a claim, and `tools/aaa_gate.py` rejects it.

---

### CRAFT — does it look and feel shipped

Judged by reading renders, at three distances: the distance the player normally sees it from,
half that, and the distance at which it is one pixel of silhouette.

For a subsystem with no geometry — schedules, naming, flight model — CRAFT is the same question
asked of behaviour: does it read as shipped, at the rates a player experiences it, or does it read
as a table that has not been dressed. The descriptors below still apply; substitute "what the
player observes over a minute" for "what the frame shows".

**0 — absent.** Not built, or a stand-in that nobody intends to keep.

**1 — reads as a placeholder from any distance.** A box primitive standing in for a named object.
The cobra bays, docking ports, observation domes and rotundas are still CRAFT 1 at session 2y: they
are in the right places, at the right sizes, and they are boxes. Also 1: detail that reads as
noise rather than machinery — the first greeble pass (session 2n) scattered 10–20 m fittings on
an even lattice and rendered as confetti at every viewing distance.

**2 — right mass, no articulation.** The silhouette is correct and the surface is undifferentiated.
Two systems that do different jobs still read as the same kind of object — solar arrays and
cooling fins after session 2b. Or the object is a correct skeleton with a missing layer: the
corridor after session 2l had ribs and a deck and no walls, so it read as scaffolding of exactly
the right size.

**3 — reads as the intended object at its normal distance and falls apart at half of it.** There
is a size hierarchy — a primary form, secondary structure, tertiary fittings — which is what took
the greebles from 1 to 3 in session 2n: assemblies of one full-size primary plus satellites,
scaled 15–50 m, so something reads at 200 m and something else reads at 20 km. The tertiary tier
is generic: the same panel, the same hatch, the same light, repeated without regard to what the
part does. Materials exist as groups but carry one flat value each.

**4 — holds at every distance the player can reach it from, and the detail is functional.** A
fitting is where a fitting would be needed: the conduit runs of session 2n do more for the hull
than fifty scattered boxes because a clamped line running 900 m down the flank of the drum is
something the structure would actually have. Wear, grime and lighting response vary across the
surface rather than being uniform. The composition holds — there is somewhere for the eye to rest
and somewhere for it to travel. A specialist looking for the tiling seam finds it; nobody else
does.

**5 — survives being looked at deliberately.** Nothing in frame repeats in a way the eye can
index. The form is legible from shading alone, with textures disabled. The silhouette is
identifiable at one pixel of screen height *and* the material still has something to say with the
camera 1 m from the wall. Nothing is symmetric that would not be built symmetric. The space has a
stated intent — crowded, isolating, industrial, ceremonial — written down before the render, and
the render delivers it to someone who was not told which it was.

---

### FIDELITY — does it match the Babylon 5 reference

Judged against `canon/00-MASTER.md`, `reference/`, `canon/INVENTIONS.md` and `canon/CONFLICTS.md`.
Authority levels are the project's own: **1** on-screen footage, **2** production material, **3**
licensed print, **4** fan reconstruction (`reference/README.md`, quoted in `00-MASTER.md` §head).

**0 — built from memory, or from a quarantined source.** Any geometry, colour, name or dimension
traceable to `reference/21-QUARANTINE-animated-film/` or `reference/22-QUARANTINE-ai-generated/`
is FIDELITY 0 however good it looks, and those folders contain the highest-resolution files in
the tree. Also 0: a dimension appearing inline in code with neither a citation nor an
`INVENTIONS.md` entry, because that is indistinguishable from memory six sessions later.

**1 — sourced, single view, no cross-check, and wrong about the object.** The forward
"swept arrays" of session 2b were four swept wings derived from a top view alone; the side view
shows a **single flat plate-like communications array on a short pylon** (session 2t). Four wings
and one plate look alike in plan and nothing alike in silhouette. The build agreed with its
source and was still wrong.

**2 — sourced from a count or a label rather than a drawing.** The radiators were built as twelve
blades arrayed around the axis from the bare figure "12"; the orthographic sheet shows them
**coplanar, three above the spine and three below** (session 2c, C-007). Everything traces;
nothing is measured. Also 2: a quantity conflated with a different quantity of the same name —
42 cargo *bays* modelled as 42 external cargo *modules*, where the sheet shows six (session 2t).

**3 — every dimension traces to a named file with a stated calibration.** A px/m figure, a scale
bar reading, or a ratio, recorded where the next reader will find it. Every non-traceable choice
has an `INVENTIONS.md` entry with all four fields — what, why, what constrained it, what would
overturn it. Provisional numbers live in a `PROVISIONAL` dict rather than inline. Single source,
authority 3 or better, no independent cross-check.

**4 — as 3, plus one dimension confirmed by a second source that could not have copied the
first.** Miller's tabulated diameters against the independently traced envelope agreeing to 5.7%
and 3.9% (session 1). The core hub cone measured at ~20% of the cap radius against the schema's
0.18 read off an unrelated print diagram — 2% apart, so the cap was built to the schema's number
rather than to a new one (session 2u). Any `CONFLICTS.md` entry touching the subsystem is logged,
and no entry marked BLOCKING has been quietly resolved in whichever direction was convenient.

**5 — as 4, plus the *appearance* has been compared side by side against an authority-1 or -2
frame at matched camera, and every difference is enumerated and either fixed or logged.** Where a
source's scale is unknown or distorted, the figure is stored as a ratio so the distortion cancels
— the core tube radius is measured as a ratio precisely because the sheet carries ~2× vertical
exaggeration (INV-018). Where two authority-1 frames disagree, the disagreement is a
`CONFLICTS.md` entry and not a silent choice: `34b` gives the tram car 3.9 truss bays and `33a`
shows a car 3–4× shorter, and until that is recorded the tram cannot score above 4.

---

### PERFORMANCE — does it fit budget with headroom

Judged by `station/budget.py` and by reading the module that computes the number.

**Read this before scoring 5:** nothing on this scale says anything about framerate. There is no
GPU in the build container and no target hardware anywhere in the loop. PERFORMANCE 5 means every
*proxy* for framerate is measured, gated and defended. See "What this rubric cannot judge".

**0 — no gate.** The quantity is not measured. The habitat drum had no gate at all until session
2v; the interior had none until 2r.

**1 — a gate exists and does not measure the thing it names.** Worse than 0, because it prints
PASS. `budget.py`'s ground-density gate measures the old flat shell at 0.005 tri/m² and will keep
passing whatever the real ground costs, which as of session 2x is 105,920 triangles in the worst
visible set (STATE.md, "still open from the verification", item 7).

**2 — measured, inside budget, from one convenient case.** One standing position, one LOD level,
the nominal configuration. A total divided by a length rather than a marginal rate — the fixed end
caps of a corridor run make a short sample look far more expensive per metre than a long one, which
is why the corridor rate is measured as `(t20 − t1) / 19`.

**3 — worst case measured and inside budget.** Swept over positions or configurations rather than
sampled once; quoted for the worst sector rather than the average. `drum_ground` swept 36 standing
positions to find 105,920 triangles (session 2x). Under 100% of the allowance, with no stated
headroom target.

**4 — worst case at ≤70% of budget, with a LOD chain whose switch distances are derived from a
measurable error rather than chosen.** The error is the silhouette **sagitta**, `r(1 − cos(π/n))`
— 92 m for an 8-gon at r = 1,211 m — not the facet width, which is the mistake `CONTRIBUTING.md`
records and which `drum_ground` asserts against so a retune cannot fall back to it. The cull is a
stable subset, verified: every LOD1 vertex exists in LOD0, so a switch removes detail rather than
rearranging it. Cost scales the way the design claims it does, and the claim is measured.

**5 — as 4, plus the gate has been proven to fail.** Someone introduced the regression and watched
the build go red. The budget *number itself* is defended in the file against the frame budget it
comes out of — the exterior's 400,000 triangles is ~2% of frame because it is always-visible
background competing with interiors, NPCs and effects, and that sentence is in `budget.py`. No
committed number is a second copy of a computed one: the cell manifest stores 210 deck records and
the rule for expanding them, not 2,330 cell records every field of which is derivable
(session 2w).

---

### ROBUSTNESS — determinism, watertightness, assertions that can actually fail

Judged by reading the self-test, running it, and breaking it.

**0 — no self-test, or a self-test that cannot fail.** This is a real and repeated category in
this repository, and it scores below "untested" because it reports PASS:

- the end-cap test that put ribs and rim lights in an `else` branch and scored **every one of 768
  triangles as passing**, on 20% of the cap (session 2y);
- `drum_ground`'s periodicity assertion comparing `sample(0.0, w)` against `sample(1.0, w)` when
  every consumer applies `u % 1.0` first — a value compared against itself, proved vacuous by
  monkeypatching in a 3.295 m seam cliff that it still scored as 0.000 (session 2y);
- `tram`'s "measured proportion" assertions, which are algebraic identities that never touch the
  built geometry and hold for `CAR_BAYS = −3.0`.

Also 0: any use of the `random` module or `str.__hash__` in generation. `str.__hash__` is salted
per process and would have produced a different hull every run (session 2n).

**1 — the self-test asserts real properties and the geometry is not closed.** `drum_end_cap()` had
**4,064 boundary edges out of 7,684**, 3,744 of them nowhere near the rim or the aperture: from
inside the habitat you could see straight through the bulkhead in dozens of places, for four
sessions. Nothing measured closure, so nothing failed.

**2 — deterministic and asserted so; the module runs in CI; primitives assert their winding.**
Assertions are per-instance: they check the thing that broke, not the class it belongs to. The
`_selftest` added in session 2p to make inside-out primitives "un-repeatable" covered `_slab` and
`_prism` and did not cover `ring_frame` or `wall_panel`, both of which were inside-out at the time
the note was written.

**3 — assertions cover a class of error, not an instance.** `boundary_edges()` rather than "the cap
looked closed"; `_inward_fraction()` rather than "the render was not black"; signed volume on
*every* primitive rather than on the two that broke. Determinism verified across at least two
`PYTHONHASHSEED` values byte for byte, not merely intended.

**4 — as 3, plus every assertion has been deliberately broken and observed to fail, and the report
says what the failure looked like.** "Removing the risers reopens 324 edges at eleven z values";
"flipping the cap winding gives 0/1536 facing correctly"; "making a rim light flat again gives 192
non-manifold edges" (session 2y). Interfaces between subsystems are asserted rather than assumed:
the streaming cell seam is compared vertex for vertex in the radial plane, **including the
wrap-around seam a `range(n)` loop never reaches** (session 2w).

**5 — as 4, plus the failure modes the subsystem is *prone to* are enumerated and each has an
assertion, including the ones that have not happened yet.** Cross-subsystem clearance is asserted
wherever two systems occupy the same space. The standing counter-example is the tram: 168 of 3,144
car vertices sit **6.43 m inside** a radial spoke, and both modules' self-tests pass, because
neither module asserts anything about the other. And nothing the module emits can be emitted twice
into one scene without an assertion catching it — the ground heightfield replaces
`drum_interior()`'s shell and does not delete it, and nothing stops both reaching the same scene
to z-fight across the whole drum.

---

## The bar

> **A subsystem is done when all four dimensions are ≥ 4 and the two most recent review rounds
> produced no finding above `minor`.**

`tools/aaa_gate.py` enforces exactly this. Nothing below is advisory.

### Severity ladder

A finding must carry a severity and, unless it is a `note`, the descriptor it points at (`C3`,
`F1`, `P2`, `R0` — dimension letter, then the score the subsystem drops to).

| Severity | Meaning | Effect |
|---|---|---|
| **blocking** | Wrong in a way a player hits, or a gate that lies. A hole they fall through; geometry from a quarantined source; a `PASS` on an unmeasured quantity; an assertion that cannot fail; two solids interpenetrating | Stops the subsystem. Resets the clean-round counter to 0 |
| **major** | A dimension is below 4 and the descriptor says why | Resets the clean-round counter to 0 |
| **minor** | True and specific, and moves no dimension below 4 | Logged and batched. Does **not** reset the counter and does **not** reopen the subsystem |
| **note** | Preference or suggestion with no descriptor behind it | Recorded. Never actionable, never blocks |

The gate refuses a `major` or `blocking` finding on a dimension the same round scored ≥ 4. A
critic who wants to call something major must first say which descriptor it fails.

### Why one clean round is not enough

**Because in this repository a clean round has never once predicted the next one.**

- Session 2p fixed `_box` emitting inside-out solids and wrote that the new `_selftest` had made
  that class of bug un-repeatable. In the same module, `corridor_section` was still laying its
  deck with a negative-determinant remap and no winding reversal, and `ring_frame` and
  `wall_panel` were both still inside-out. The claim was made in the same session as three
  surviving instances of the thing it claimed to have closed.
- Session 2x committed two modules whose self-tests passed **69/69 and 36/36**. The verification
  pass that followed found seven defects, three of them in the code those modules were forbidden
  to touch, one of them BLOCKING.
- Session 2y closed the drum's two holes and, in the process of writing the assertions, found that
  the assertion being replaced had been scoring 768 triangles as passing since it was written.

Three structural reasons, independent of that history:

1. **A round that ends in changes ends with the least-reviewed code in the subsystem.** The fix is
   new code written under the pressure of a finding, and it has had no pass at all. Requiring a
   clean round *after* the round that produced no changes means the last edit has itself been
   reviewed.
2. **One clean round is evidence about the reviewer, not the artefact** — particularly when the
   reviewer just finished producing the fixes and knows where they looked. Two rounds, preferably
   by different agents with different starting viewpoints, decorrelate that.
3. **It terminates.** The second round is bounded because the first round's fixes are bounded.
   Two is the smallest number that distinguishes "the artefact is clean" from "this pass found
   nothing new", and three does not buy information proportional to its cost: the marginal defect
   rate here drops sharply once a fix has been through a full pass, and unbounded review is the
   exact failure this document exists to prevent.

### The hard stop

Without a cap, a harsh critic still wins — they simply keep finding `minor` items and calling them
`major`. So:

- **At most 3 remediation rounds per subsystem after the first review.** If the bar is not met, the
  subsystem is marked `capped` with a written `cap_reason` naming the dimension, the score, and
  what would raise it. The gate requires that reason and will not accept a cap without one.
- A capped subsystem is **not a failure and not a retry**. It is a decision owed to the owner,
  listed as such in the dashboard, and it does not fire another round.
- **Scores move only on evidence**: a render that was read, a number that was measured, an
  assertion that failed, or a citation. "It could be better" moves nothing.
- **Round zero is the build.** A build agent reviewing its own work is not a round.

---

## Per-subsystem checklist

Derived from the dimensions. The letter after each item is the dimension it scores.

### Geometry

- `boundary_edges()` returns zero except at declared openings, and the declared openings are
  listed with their coordinates so a new opening is a diff. **(R)**
- Non-manifold edges: zero. A face used by three triangles is a modelling error that renders
  perfectly. **(R)**
- Normal convention correct for the surface: **inside the habitat drum, normals point toward the
  spin axis; everywhere else outward.** Measured with `_inward_fraction()`, never eyeballed —
  getting it wrong renders black, which reads as a badly placed camera rather than as a bug. **(R)**
- Signed volume positive on every closed primitive, not on the two that broke last time. **(R)**
- **Openings located by rendering the same view against two backgrounds and diffing.** This was
  measured rather than assumed, and the measurement corrected the received version of the rule.
  A hole renders as *exactly* the background colour, so the diff of a black render and a magenta
  render isolates every opening to the pixel — 280 triangles cut from the corridor soffit came out
  as 11,007 pixels, 4.3% of frame, with no reliance on the reviewer's eye. What is **not** reliably
  true is "black hides holes": in both cases tested here — a headlamped corridor and the point-lit
  drum — the darkest *lit* surface was well clear of black (drum minimum luminance 109 of 765), so
  black would have shown the hole. The rule that survives is narrower and more useful: **a
  background is unusable if the shading in that view can produce it, and you cannot know in advance
  which views those are.** Magenta removes the question. **(C, R)**
- The diff also finds *declared* openings — the drum's core aperture and the frame edges accounted
  for all 1,693 background pixels in a closed model — so the check is "reconcile every background
  pixel against the declared opening list", not "expect zero". A render can only ever say a hole is
  visible **from this camera**; `boundary_edges()` says there is no hole at all. Where the two
  disagree, the geometry is right. **(R)**
- Seams compared vertex for vertex on the shared edge, including the wrap-around index. Touching
  bounding boxes prove nothing, and a crack in a ring corridor is a hole a player falls through at
  1 g. **(R)**
- Clearance against every other system occupying the same space, by point-in-volume over actual
  vertices, swept over any phase or animation parameter. **(R)**
- Silhouette read at one pixel, at normal distance, and at arm's length. **(C)**
- Marginal triangle rate, not total over length. LOD switch distances from sagitta or measured
  error. Culled sets are strict subsets. **(P)**
- Every dimension traced to a file with a calibration, or in `INVENTIONS.md` with all four
  fields. **(F)**

### Materials and textures

- One material group per material, not per object; the draw-call count is gated. **(P)**
- Texture memory measured against the subsystem's slice of the 12 GB target, and stated. **(P)**
- Tiling: on a flat-on render of the largest surface, count the repeats. If the eye can index the
  period, it is CRAFT 3 at best. **(C)**
- Two detail tiers minimum: something that reads at the normal distance and something that reads at
  1 m. **(C)**
- Value range: nothing pure black, nothing pure white, checked on the histogram of a flat-lit
  render rather than by eye. **(C)**
- Colour is traced to a **named authority-1 or -2 frame**, and recorded as a *relationship*
  ("warmer than the corridor plates", "darker than the dado") rather than an absolute hex, because
  screencap colour carries the episode's grade and the codec's chroma subsampling. An absolute
  value requires a production source. **(F)**
- Era lock S2–3. A later-season or animated-film palette is FIDELITY 0, not a near miss. **(F)**

### Lighting

- The sources are the ones the reference shows, in the positions it shows them. The habitat drum is
  lit from **longitudinal light runs on the guideway trusses** — `34b` shows the tubes alongside the
  truss, `33a` the rectangular fixtures on its underside, both authority 1 — not from an axial
  sun-strip and not from the end caps. **(F)**
- Form legible from shading alone with textures off. **(C)**
- Nothing blown out; nothing crushed. Measured on the histogram. **(C)**
- Every light has a source that is in frame or plausibly just outside it. **(C, F)**
- Rotation is stated: a fixture mounted on the truss does not sweep relative to the ground; a light
  outside the drum does, at 33.5 s per turn. **(F, R)**
- **Mood is scored under CRAFT and needs a written intent per space before the render** — "Downbelow
  is somewhere you would not linger" — plus a measurable proxy: contrast ratio, source count, and
  the fraction of frame below 15% luminance. Without the intent written first, the review is a
  preference. **(C)**

### Audio

Nothing is built yet; these are the criteria it will be scored against, and they are written now so
that the first build is not scored against criteria invented after it.

- Every sound has a source object in world space, or is explicitly declared non-diegetic. **(C)**
- Reverb parameters derived from the volume's actual dimensions — a 2,586 m drum, a 140 m streaming
  cell and a corridor bay are three different acoustic problems and the numbers exist. **(C, F)**
- Room tone differs measurably between sectors: spectral centroid and level, not "it feels
  different". **(C)**
- Crowd density is audible and agrees with `station/npc/schedule.py` at that hour. A corridor at
  03:00 is not a quieter 13:00 — it holds Minbari and Centauri, which is a different mix, and the
  bed must be a different mix too. **(F, C)**
- Alienness: non-human speech is not human speech pitch-shifted. Phoneme inventories tied to the
  same on-screen evidence that `names.py` records beside each grammar. **(F)**
- Determinism: any procedural audio parameter keyed with `blake2b` or an explicit FNV-1a. **(R)**
- Loudness gated numerically (integrated LUFS, true peak) because the container has no ears —
  the same argument as framerate, with the same limitation. **(P)**

### NPCs

- Names from the fitted per-species grammars with the evidence recorded beside each pattern.
  **Vorlon stays a closed list** — two attested names is not enough to generate from — and a test
  asserts it stays closed. **(F, R)**
- The species mix sums to exactly 1.0. It summed to 0.94 and silently dropped 120 of every 2,000
  residents; that is the population leak the statistical layer exists to prevent. **(R)**
- Sleep resolves against the **shifted** rhythm. Resolving it against the unshifted one put the
  entire night watch to bed and showed zero security on duty at 02:00. **(R)**
- Crowdedness and isolation are stated as an intended figure per space per hour, then checked
  against what the schedule model actually produces. **(C, F)**
- NPC identity is a function of `(seed, id)` and not of iteration order. **(R)**
- Density gated against the visible-set triangle budget: NPCs come out of the same frame as
  structure, and interior structure is already allowed only 5% of it. **(P)**
- Record fields match the on-screen identicard schema — `NAME` (SURNAME, FORENAME), `ORIGIN`,
  `DES/ATMOS`, `SEX`, `DOB`, `PHYS CHR`, `MEDICAL`, `LICENSED PSI`, `VISAS` — with humans as
  atmosphere `02`. Authority 1. **(F)**

### Interaction

- Every interactable is reachable from a standing position **derived from the geometry**, not
  hand-placed. `stand_point()` exists because a hand-placed viewpoint sat five metres inside the
  ground. **(R)**
- Collision geometry matches render geometry within a stated tolerance, and the tolerance is
  asserted. The tram passing 6.43 m through a spoke is what the absence of this looks like. **(R)**
- Anything whose mechanism is unsourced is switchable in one edit. No frame in the reference set
  shows a door leaf, so the two surviving readings are both built and selected by one entry in
  `PROVISIONAL` (INV-008). **(F)**
- Rotating-frame consequences are honoured: anything released at the drum floor inherits **52.2
  m/s**; holding station 200 m off a bay costs **89.8 m/s**, not zero; a rim-to-axis lift is a
  two-minute ride or it pulls more than 0.12 g sideways. **(F, R)**
- **No interaction may assume a level *number*.** C-004 is open. Address by `(sector, ring_index)`
  and let `bind_labels()` attach names later. **(F)**
- Every interaction has a failure state that is legible: a dock that fails on 52.2 m/s of lateral
  drift is a scrape along the hull, and the player must be able to tell that is what happened. **(C)**

---

## Running the gate

```bash
python3 tools/aaa_gate.py                        # self-test: prints "N/N passed"
python3 tools/aaa_gate.py docs/aaa-scorecard.json
python3 tools/aaa_gate.py docs/aaa-scorecard.json --strict   # release gate
python3 tools/aaa_gate.py --template             # skeleton for a new subsystem
```

The scorecard is a JSON file with one entry per subsystem, each holding an ordered list of review
rounds, newest last:

```json
{
  "version": 1,
  "bar": { "min_score": 4, "clean_rounds_required": 2, "max_rounds": 4 },
  "subsystems": {
    "drum_end_caps": {
      "status": "active",
      "rounds": [
        {
          "round": 1,
          "reviewer": "verify-2y",
          "scores": { "craft": 3, "fidelity": 4, "performance": 3, "robustness": 1 },
          "evidence": { "fidelity": "hub cone r/R 0.20 measured vs schema 0.18, INV-011" },
          "broke_assertions": false,
          "findings": [
            { "severity": "blocking", "dimension": "robustness", "descriptor": "R1",
              "where": "station/interior.py:drum_end_cap",
              "text": "4064 boundary edges of 7684; 3744 away from rim or aperture" }
          ]
        }
      ]
    }
  }
}
```

What the gate enforces beyond arithmetic:

- A score of 4 or 5 needs an evidence string. A ROBUSTNESS 5 additionally needs
  `"broke_assertions": true`, because that descriptor *is* the claim that every assertion was
  deliberately broken and observed to fail.
- A finding's `descriptor` must be `[CFPR][0-5]` and its letter must match its `dimension`.
- A dimension scored below the bar must have a `major` or `blocking` finding explaining it, and a
  dimension scored at or above the bar must not.
- Round numbers strictly increase, so re-submitting last round's scorecard is an error rather than
  progress.
- **Regression fails the build.** Any dimension lower than the same dimension in the previous round
  exits non-zero, whether or not the subsystem is still above the bar. This is the thing a rubric
  catches and a critic cannot: a critic sees one snapshot. A drop from 5 to 4 with a good reason is
  still a drop, and it needs a `regression_waiver` with a written reason — and a round carrying a
  waiver can never be a clean round.

---

## What this rubric cannot judge

`CLAUDE.md` is explicit that a software render validates nothing about framerate. The same honesty
is owed to everything else in that category. **None of the following is scoreable by this rubric,
by `aaa_gate.py`, or by any agent working in this container.** Where a dimension appears to cover
one of them, it is covering a proxy, and the proxy is named.

| Cannot be judged here | What the rubric measures instead | What would be needed |
|---|---|---|
| **Framerate, frame time, stutter, hitching** | Triangles, draw calls, vertex bandwidth, texture memory, instance counts against a stated budget | The target card — RTX 4070 / RX 7800 XT class — running the real build at 1440p, with a capture harness. Nothing short of that |
| **Streaming hitches and load spikes** | Cell size, resident-set triangles, manifest structure | Real I/O against real storage; a cell budget says nothing about the time to page one in |
| **Shader cost** | Nothing. There is no measurement of pixel cost anywhere in this project | GPU timing queries on target hardware |
| **How it feels to play** — pacing, sense of scale in motion, whether the drum is awe-inspiring | Static composition, proportion, silhouette, lighting, from stills | A human, at the controls, moving. A still cannot show that a 2 km walk is boring |
| **Motion**: animation quality, gait, crowd flow, door timing, camera feel | Nothing. Every render is one frame | Video capture and a person watching it |
| **Audio, at all** | Numeric properties only — LUFS, spectral centroid, source counts, determinism | Ears. A mix is not gateable numerically past the point of "not clipping and not silent" |
| **Colour accuracy** | Relationships between colours in one frame | A calibrated display and a colour-managed pipeline. Screencaps carry the episode's grade and chroma subsampling; treating a screencap hex as ground truth is a fidelity error dressed as rigour |
| **Whether an alien reads as alien** rather than as a human in makeup | Nothing. This is a design judgement with no numeric proxy | A human reviewer, and a decision about what the target is |
| **Whether the writing, naming and signage sound like Babylon 5** | Grammar conformance to attested names | A human who knows the show |
| **Latency, input feel, network** | Nothing | Target hardware and a player |
| **Whether the bar itself is set correctly** | Nothing. The four dimensions and the "≥ 4, two clean rounds" bar are a design choice recorded here, not a derived result | The owner, looking at a subsystem the rubric passed and saying whether it is good enough |

Two further limits worth stating plainly:

**A render read by an agent is a low-resolution, low-dynamic-range, single-frame, software
rasterisation.** It has caught blown-out lighting, missing material, bad framing, confetti
greebles, a shuttlecock radiator and a mangled deck — it is genuinely the best feedback loop this
project has. It also failed for four sessions to show a bulkhead with 4,064 open edges. Testing
that failure while writing this file showed the mechanism is narrower than the folklore: a hole is
always exactly the background colour, and it disappears only when the shading in that particular
view can also reach that colour. Which means **a render cannot be trusted to have looked at the
thing you think it looked at**, and the fix is never a better render — it is a measurement on the
geometry. Everything a render can miss, it misses silently.

**The rubric scores the artefact, not the reference.** A subsystem can score FIDELITY 5 against a
source that is itself wrong. C-005 exists because the Contract 5 schematic's scale bar is spliced,
and C-001 exists because the only complete dimensional breakdown of the station contradicts show
canon by 2.589×. A perfect score against a bad source is exactly as wrong as a bad score, and the
only defence is the cross-check clause in FIDELITY 4 — two sources that could not have copied each
other.
