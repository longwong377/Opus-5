# LAYER 8, ROUND 1 — the first frames of this station ever scored against the rubric

**Reviewer:** judging agent, session 4e. Builder of none of it.
**Revision judged:** `88155f5`, in a detached `git worktree` at `/home/user/judge4e` so that
nothing another actor was writing could land in a frame mid-edit (CLAUDE.md, session 4e:
*"before believing a render taken while an agent is running, check whether it imports anything
that agent owns"*).

**Renderer, stated on every frame because session 4e's whole visual pass was invalidated for
want of this line:** every one of the 21 frames below was produced by
`Vulkan 1.4.318 - Forward+ - llvmpipe`. `tools/judge_sweep.py` records the `renderer:` line the
engine printed for each shot into `docs/judge-4e-frames.json` and **deletes the PNG if it does
not contain `Forward+`**. `python3 tools/judge_sweep.py --report` re-prints the table:
**21 frames, 0 refused.** No frame in this round came from OpenGL 3 Compatibility.

---

## The headline, and it is not about a picture

**`station/budget.py` exits 1. It is CI step 7 of 41. The other 34 steps are SKIPPED.**

GitHub Actions run [30689612155](https://github.com/longwong377/Opus-5/actions/runs/30689612155),
today at 07:22 on this branch, head `4895c098`:

| step | conclusion |
|---|---|
| 7 · Performance budgets | **failure** |
| 8 · Whole-station collision total has not drifted | skipped |
| 9 · Canon assertions | skipped |
| 11 · Interior kit self-test | skipped |
| 18 · Layer 3 coverage and material plausibility | skipped |
| 19 · Geometric detail metric | skipped |
| **20 · The station is walkable** | **skipped** |
| 21 · The inhabitants are solid | skipped |
| **22 · How much of the station can be walked in** | **skipped** |
| 23 · The habitat drum is walkable | skipped |
| 39 · NPC bodies, costume and crowd | skipped |
| 41 · Confirm the schema still parses and is fully sourced | skipped |
| *…and 22 more* | skipped |

**The 30 most recent runs of `validate.yml` all failed. Not one succeeded**, over the whole span
the API returns (2026-08-01 01:47 → 07:22).

`validate.yml` has no `continue-on-error` anywhere — `grep -c` returns 0 — and the job is one
linear list, so a failure at step 7 aborts every step after it. The workflow's own comment says
of that step *"THIS STEP IS EXPECTED RED, and saying so here is the point"*, which is an honest
and correct thing to write about a budget gate whose remedy is to move the content. What nobody
noticed is what the honesty costs: **an intentionally-red step at position 7 of 41 silently
disables the other 34.**

CLAUDE.md's second structural rule is *"Integration is a gate, not a phase. `station/walkable.py`
asserts the player can spawn, stand, walk, and reach the neighbouring location. **It runs in
CI.**"* It does not run in CI. It has not run in CI on any of the last thirty pushes. Neither has
`deck.py --sweep`, which the same document calls *"the only gate here that asks a whole-station
question"*.

This is the same failure this repository keeps writing down, one level further out. Session 3u:
gates that measure a part and never the whole. Session 3z: a gate that reads a committed artefact
it cannot rebuild. Session 4e: a tool that substitutes a lesser mode and exits 0. **Here: gates
that are neither green nor red, because they are never reached.** The absence of a result reads
exactly like a pass, and for thirty runs it has been read that way.

Two smaller members of the same family, found the same way:

- **`tools/aaa_gate.py` — the gate `docs/AAA-STANDARD.md` says "enforces exactly this. Nothing
  below is advisory" — appears zero times in `validate.yml`.** Run by hand,
  `python3 tools/aaa_gate.py docs/aaa-scorecard.json` exits 1 with **52 errors** against rounds
  committed in earlier sessions. The rubric's own enforcement has never been enforced.
- **`station/density.py`'s layer-2b report is not in CI either** — the workflow runs
  `density.py --selftest`, and the comment says the bare report *"exits 1 BY DESIGN"*. Correct,
  and it means the 122/128 articulation number is never computed by anything but a human.

---

## The sample, and what I did not look at

128 locations cannot be judged in one round. The sample is 12 subjects over 21 frames, chosen on
three stated rules and nothing else:

| rule | why | subjects |
|---|---|---|
| **AREA** | the surfaces a player actually stands on, weighted by floor area | the ring corridor (77% of a ring deck, `docs/judge-3w.md`); the `generic` procedural room archetype (58% of the station, CLAUDE.md); `commerce`; `industrial` |
| **AUTH1** | the locations a viewer can catch us on, taken in the gazetteer's *own* ranked order (`LOCATIONS.md` §19) | 1 Zócalo · 2 customs & arrival · 3 docking bay · 4 C&C · 6 Council Chamber |
| **PRIOR** | the worst-scoring subjects in `docs/aaa-scorecard.json`, so this is a before/after and not a fresh opinion | `walkable_deck` 1/1/1/1 · `npc_bodies` 1/2/0/2 · `garden_townscape` 1/2/4/3 · `generated_rooms` · `zocalo_interior` · `hull_exterior` |

**Distances.** Every craft claim below cites a frame at the rubric's **half** distance, because
judging only at the normal one is the documented cause of 118 locations of blockout passing three
layers. Where the camera can be moved it was moved (the exterior orbits at 9,200 m / 4,600 m /
60,000 m; the corridor eye turns to face its own wall at 1.3 m). Where the camera is pinned — the
deck shot stands on the ring at the player's own radius and cannot be walked into a wall — half
distance is taken by halving the tangent of the half field of view, 46° → 24°, which doubles
pixels-per-metre exactly as walking to half the distance does. **Stated as a limitation:** a
narrower lens resolves the detail a closer camera would and does not reproduce its parallax or
occlusion. The derivation is in `tools/judge_sweep.py`.

**NOT looked at, and it is most of the station.** 116 of 128 locations. Specifically: all of
Downbelow, the alien sector and Kosh's quarters, the four residential classes, medlab, the brig
and Security Central, the casino and every named bar, the observation domes, worship, the tram
and every transit location, the whole industrial and life-support set except `fabrication`, and
the entire drum townscape except the one documented `--stand 20,4700` viewpoint. Audio (layer 7)
was not judged at all — there are no ears in this container and the rubric says so. Nothing in
this round says anything about framerate, motion, or how any of it feels to play.

---

## Scores

Full rounds are appended to `docs/aaa-scorecard.json`. Nothing earlier was rewritten.

| subject | craft | fid | perf | rob | the one-line reason |
|---|---|---|---|---|---|
| `walkable_deck` | **3** ↑2 | **2** ↑1 | **2** ↑1 | **2** ↑1 | materialled, lit, peopled and walkable now — and the wall a player stands 1.3 m from has nothing on it, and 34 of its 41 CI steps do not run |
| `generated_rooms` | 3 = | 2 = | 4 = | 4 = | `hydroponics` is a plated box with no growing equipment: `rooms.FIXTURES` is keyed by 11 archetypes and has no entry for it |
| `zocalo_interior` | 3 = | 3 = | 4 = | 4 = | the concourse reads; the back wall is blank across its whole width, the centre strip is fully clipped, and there is not one person in the station's principal social space |
| `garden_townscape` | 1 = | 2 = | 4 = | 3 = | two flat colour fields with a straight-edged boundary and nothing standing on them, at 3.9% of the ground triangle allowance |
| `npc_bodies` | **2** ↑1 | 2 = | **2** ↑2 | 2 = | dressed, posed, and on the floor to ±12.5 mm — with no face, stump hands and a shoulder joint that reads as detached |
| `hull_exterior` | 3 = | 4 = | 4 = | 3 = | the silhouette is Babylon 5 at 60 km; nine of 41 hull groups render on the glTF fallback and no window on an 8 km station is lit |
| `command_control` **new** | **1** | 2 | 2 | 2 | the station's bridge console is a flat orange plate, 24 triangles an instance |
| `council_chamber` **new** | **1** | 2 | 2 | 2 | the form is right and every colour and light behaviour in the authority-1 frame is absent |
| `customs_arrival` **new** | **1** | 2 | 2 | 2 | the three information boards whose text is authority-1 verbatim are blank 12-triangle slabs |
| `docking_bay_interior` **new** | **1** | 2 | 2 | 3 | none of the reference's girders, chevrons, gantry or deck emblem read; 63.95% of the frame is below the measurable floor |

Nothing reaches the bar. No subsystem is done.

**The quality is uneven and that is the finding, again.** `industrial` (`fabrication`,
`docs/judge-4e-industrial-normal.png`) is a genuinely good frame — furnaces, pipes, stanchions,
crates, four people, a wall pool with warm/cool separation. Four locations the show is *famous
for* are 1s. The bulk got articulated and the landmarks did not.

---

## THE THREE WORST THINGS

### 1 — C&C is a flat orange plate, and three green gates say it is fine

**Frame: `docs/judge-4e-cnc-half.png`** (half distance) and `docs/judge-4e-cnc-normal.png`.

The station's bridge. The most-seen room in the show. At half distance the console — the object
the room exists for — is **one uniform orange polygon on four black sticks**: no screens, no
keys, no bezel, no material break, no second detail tier of any kind. `docs/AAA-STANDARD.md`
C1 is *"a box primitive standing in for a named object"*, and it is literally that:

```
station/generated/scene/interior/cnc.obj
  cc_console_leg   120 tri over 5 instances   =  24 tri each
  cc_console_face   60 tri
  cc_floor           2 tri
  cc_pit             2 tri
  cnc.obj total  2,064 tri for a 941 m2 room
```

**Now the three gates:**

- `station/interact.py --audit` → `[1/128] cnc bespoke 4/4 resolved`, part of **357/357**.
  `interact.resolve_place` reports `alias: {'console': 'cc_console_leg'}` — the declared
  interactable `console` resolves to a **24-triangle box**, and the audit is correct to say so,
  because it tests *existence* and nothing else.
- `station/density.py` → `PASS Command & Control … 170.9% of its floor`. The same row's `%show`
  column reads **12.6%** — the line density of a Babylon 5 set is eight times what the room
  carries — and the module's own footer says `%show` is *"not gated"*.
- `tools/export_scene.py --gate-lighting`/`measure_frame` → the frame is 0.11% clipped, inside
  the 3.69% cap, and 36.35% crushed, inside the derived 0.22–63.92% envelope.

**Layer 5's exit criterion is "the declared interactable types exist".** A 24-triangle box
satisfies every word of it. That is the same sentence, structurally, as layer 2's *"mesh, closed,
correctly wound, inside its own footprint"* — the criterion CLAUDE.md calls the most expensive
lesson in the file, because *a cube passes every word of it*. **The next under-specified
criterion has already been written and it is layer 5's.**

### 2 — nothing in the corridor casts a shadow, and no render flag can change that

**Frames: `docs/judge-4e-corridor-normal.png` and `docs/judge-4e-corridor-shadow24.png`.**

The corridor is 77% of a ring deck's floor. Every body in it reads pasted on. The obvious
hypothesis — that this is `INTERIOR_SHADOW_LIGHTS = 2`, a render economy — is **wrong**, and the
A/B says so:

```
--shadow-lights 2  -> render_shot: 1557 light-run sources (725 spot),  2 casting shadows
--shadow-lights 24 -> render_shot: 1557 light-run sources (725 spot), 18 casting shadows
diff: 0.00% of pixels differ, mean 0.000/255, max 0    BYTE-IDENTICAL
```

Session 4e's lesson is that a byte-identical A/B must be explained, not recorded. Explained, from
`station/generated/scene/deck/scene.json`:

| light group | n | omni range | shadow-castable |
|---|---|---|---|
| `light_downlight` (the corridor) | **822** | **1.20 m** | **no** |
| `corridor_soft_fill` | **707** | 30.00 m | **no** |
| `*__light_highbay` (inside the six rooms) | 18 | 19–22 m | yes |

**All 18 castable lights are inside rooms. Not one of the corridor's 1,529 is.** So the A/B is
byte-identical at *any* value of `--shadow-lights`, and the flatness is a property of the rig, not
of a flag. **The control fires:** the same 0-vs-24 A/B inside `docking_bays` moves **15.45% of
pixels** — the pipeline casts shadows perfectly well where it is asked to.

Two consequences. The corridor is lit by 822 point sources with a **1.2 m reach** — a lamp that
cannot light the far side of a 2.6 m corridor — over an ambient term of 1.30 that CLAUDE.md has
already measured as owning p5. And **every interior craft score in `docs/aaa-scorecard.json`,
including this round's, was taken with two shadow casters**, on a constant `export_scene.py` says
plainly *"has not been re-derived"*. That is a measurement-validity problem of the same shape as
the OpenGL fallback: the frame is not the game.

### 3 — the customs boards are blank slabs, and the text for them is already in the repository

**Frame: `docs/judge-4e-customs-normal.png`.** The player's first room.

Three information boards hang across the hall. In the show they are the authority-1 signage that
*is* the room's purpose — the gazetteer quotes them verbatim: *"ATMOSPHERE CAUTION — SIX
DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5…"*, *"…TIME ON B-5 IS EARTH MEAN TIME
(EMT). MONETARY EXCHANGE RATES THROUGH BUSINESS CENTER"*. In the frame all three are featureless
pale rectangles.

```
customs_screen_welcome    12 tri     customs_screen_schematic  12 tri
customs_screen_head       12 tri     customs_desk              48 tri
```

Twelve triangles is exactly a cuboid. And **the text exists**: `station/signage.py:48-68` carries
`"ATMOSPHERE CAUTION"`, `"SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5."` and
`"TIME ON B-5 IS EARTH MEAN TIME (EMT)"` as data, and `station/customs.py` imports `signage`. The
corridor eight metres away renders legible signage — `docs/judge-4e-corridor-normal.png` shows a
lit board reading `…ING BAYS (24) / BLUE 0 0 000`. So the capability is built, the content is
authored, and the room that most needs it has three blank boxes.

Meanwhile `interact.py --audit` reports `customs_north bespoke 5/5 resolved`, `info_board`
included, and 53.01% of the frame is below the measurable floor.

---

## GREEN IN A GATE, BAD IN A FRAME — the whole list

This is the section this project asked for. Six, ordered by how much they hide.

**1. 34 of 41 CI steps are skipped, not passed.** Above. The gates that ask the whole-station
questions are the ones downstream of the red step.

**2. `density.py` passes 122/128 on articulation and prints, in the same table, that the median
location carries 27.9% of a Babylon 5 set's line density.** Its own footer: *"the floor binds on
the budget almost everywhere, and the budget is far below the show."* For the five authority-1
locations in this sample:

| location | `%bar` (the gate: ≥100) | `%show` (not gated) | triangles |
|---|---|---|---|
| Command & Control | **170.9 PASS** | **12.6%** | 2,064 for 941 m² |
| The Zócalo | **177.0 PASS** | **9.2%** | 46,668 for 8,074 m² |
| Docking bays (24) | **155.3 PASS** | **15.0%** | 3,943 for 33,289 m² |
| Customs hall, north | **108.7 PASS** | **12.9%** | 7,296 for 6,041 m² |
| Council chamber | 93.7 FAIL | 9.5% | 5,950 for 1,683 m² |

Layer 2b was re-derived *because* of "shitty little cubes". The re-derived criterion still cannot
fail on a room at a tenth of the show's articulation, because it binds on a budget rather than on
the reference.

**3. `density.py --machinery` prints its own documented signature of failure in a column it does
not check.** The module's footer: *"norm = effective distinct facing directions… **A BOX READS
~6 whatever its tessellation**… a column of 5-6 across a whole room is this gate's signature
failure and **is not itself gated**."* Counted off the gate's own output:

```
68/78 locations pass the gate
50 of 78 have norm <= 7.0  ("a box reads ~6")   -- 44 of those 50 PASS
median norm across all 78: 6.425
```

Worst: Transport tubes 5.03, Concentric personnel transfer 5.05, Security Central 5.25,
Nightwatch 5.41, the brig 5.57, the commander's administration complex 5.59 — all PASS.

*(CLAUDE.md records this gate at 74/78. Measured at `88155f5` it is **68/78**. I did not chase
the difference; another actor may have been mid-edit. Stated so the next reader checks rather
than inherits.)*

**4. `tools/export_scene.py`'s header claims a coverage assertion the `deck` shot never runs.**
Line 19, verbatim: *"What it DOES do is assert that every group it emits has a rule, so nothing
lands on the fallback by accident."* `unmatched_groups()` is called in exactly two places —
`drum.tscn` (asserted) and `exterior.tscn` (**printed as a note**). The `deck` shot, which the
same file calls *"the build"*, reaches neither. The engine reports the truth on every deck render
and nothing reads it:

```
render_shot: fallback material used by 2 group(s): dress_post, dress_skid      2,208 tri
exterior:    9 of 41 hull groups unbound --  aft_terminus, docking_bay_throat,
             docking_sphere, forward_deflector_spike, forward_taper, forward_waist,
             generator_torus_housing, hull_flare_aft, primary_fusion_reactor
```

Those nine are visible as smooth untextured plastic against the greebled cylinders beside them in
`docs/judge-4e-exterior-half.png` — the nose, the waist and the aft terminus. The file's own
comment predicted this: *"It should BECOME a check the moment the .tscn binds them — a note that
nobody promotes is how this stayed invisible for two sessions."* It is three now.

**5. The distribution gate cannot see the brightest object in a composition.** `measure_frame.py`
scores the Zócalo at **2.11% clipped against a 3.69% cap — a pass** — and the clipped pixels are
one contiguous, fully-blown white strip running down the middle of the floor from the camera to
the back wall, the single most eye-catching thing in `docs/judge-4e-zocalo-normal.png`. A
fraction of pixels has no notion of contiguity or of composition. CLAUDE.md already records that
these pools are `emission_energy`, which `room_exposure` does not scale; the gate cannot say so
because 2% is 2%.

**6. `tools/aaa_gate.py` is not wired to anything.** 52 errors on the committed scorecard, exit
1, and zero references in `validate.yml`. `docs/AAA-STANDARD.md` says of it: *"Nothing below is
advisory."*

---

## Two claims I checked and withdrew

Recorded because *"a reviewer may be wrong"* is in the working agreement and a review with no
retractions has not tested itself.

**"The bodies are floating."** They read that way in every frame. Measured off the deck's own
exported mesh against the camera-derived floor radius of 211.528 m (up is inward, so a foot is at
maximum radius): **155 bodies, min −12.3 mm, median +10.5 mm, max +12.5 mm.** Nobody floats. The
appearance is finding 2 — no contact shadow — and the two are easy to confuse by eye.

**"The Zócalo has 18,296 open boundary edges."** An unwelded edge count over `zocalo.obj` says
so, 23% of its edges. **Welding by position (1 × 10⁻⁵ m) takes it to 0**, and the same weld takes
`cnc.obj` from 656 to 0. The count was duplicated seam vertices, not holes. Note also that welding
*introduces* apparent non-manifold edges wherever two closed solids merely touch, so **neither of
my counts is a finding** — this is what `interior_kit.boundary_edges()` exists for and I did not
run it over the room path. `docking_bays.obj` is the one survivor at 31 open edges, and located,
they are all coplanar at z = 0 spanning x −21..21 and y 0..22.2 — the bay mouth, i.e. the declared
opening, reconciled as the rubric asks. Not a defect.

---

## The rest of what the frames show

**The corridor** (`judge-4e-corridor-normal`, `-half`, `-wall`, `-door`). At normal distance it
is the best generic content in the project: pilasters, dado, rail band, shelf, deck channel,
downlights, legible signage, a moving crowd. At **1.3 m** (`-wall`) the panel is a smooth
gradient carrying a handful of faint rivet dots and one low-contrast grime smear — no normal-map
response, no edge wear, no second tier. The light pilaster's glyph strip is **the same rounded
rectangle repeated seven times**, indexable at a glance. That is C3's *"tertiary tier is generic:
the same panel, the same hatch, the same light, repeated without regard to what the part does"*,
exactly.

**The people** (`judge-4e-commerce-normal` is the clearest). Dressed from the measured wardrobe,
posed standing/sitting/walking, on the floor to ±12.5 mm — a real advance on 3w's black
silhouettes. At the distance a player meets them across a room: **no face** (a smooth ovoid, a
hair cap and a pale band where the eyes go), **stump or three-prong hands**, a **neck that reads
as a separate white cylinder**, and an **upper arm that reads as detached from the shoulder** with
a visible gap — most legible on the near figure in `judge-4e-corridor-door.png`. C2 is *"right
mass, no articulation… a correct skeleton with a missing layer"*, and the missing layer is the
head and hands.

**Composition of the walkable deck**, measured off its own 816,188-triangle export:

```
architecture + corridor  664,300  81.4%
people                   137,368  16.8%   (596 groups)
fixtures                   7,264   0.9%   (42 groups)
props                      7,256   0.9%   (54 groups)
```

CLAUDE.md's session-3u split was 95.9 / 1.7 / 2.5 and the note beside it reads *"Props and
inhabitants are not polish. They are most of the remaining product."* The inhabitants arrived.
**Props and fixtures together are now 1.8% of the deck, against 4.2% in 3u** — the half of that
sentence about props went backwards in relative terms. Eight prop groups on the deck are exactly
12 triangles, including `docking_bays__prop_cargo_crane` (a crane) and four `prop_bay_door`.

**The drum** (`judge-4e-drum-normal`, `-half`). The scale is the best thing in the project — the
ground curving up to a core tube 1.2 km away is genuinely arresting. On it: **nothing.** Two flat
colour fields meeting along a straight-edged polygon boundary with the terrain lattice showing in
the zigzag, no vegetation, no props, no people, no relief. The buildings visible around the curve
are white boxes with window-grid textures. `budget.py` says the ground runs at **0.020 tri/m²
against an allowance of 0.500 — 3.9% — with 183,880 triangles of headroom unspent.** CLAUDE.md's
own rule: *"The triangle budget is a TARGET, not a ceiling."*

**The exterior** (`judge-4e-exterior-normal`, `-half`, `-onepixel`). The silhouette is
unmistakably Babylon 5 at 60,000 m — long spine, drum, fin cluster, aft terminus, ~90 px across.
At half distance the drum and ribbed sections carry conduit runs and greebles with real relief and
self-shadowing. Against that: nine unbound groups rendering as smooth plastic, and **not one lit
window, running light or beacon anywhere on an 8 km structure housing 250,000 people** — the
single largest fidelity gap on the hull and the cheapest to close.

**The Council Chamber** (`judge-4e-council-normal`). The fin fan, the medallion, the curved bench,
the lattice chair backs and the stepped floor are all there and the silhouette reads. Every
*value* in the authority-1 frame is absent: the bench is a plain white slab where the reference's
defining feature is *"a perforated gold mesh front panel lit from within — **the furniture is the
light source**"*; the floor is grey where the reference is *"pale blue-green polygonal mosaic"*;
the medallion sits on grey, not *"deep blue"*. 54.05% of the frame is below the measurable floor
and the chamber stands in an unenclosed void. It is one of only six locations to FAIL layer 2b
(93.7% of its floor).

---

## Severity ledger

| # | severity | dimension | where | one line |
|---|---|---|---|---|
| F-1 | **blocking** | robustness | `.github/workflows/validate.yml` | step 7 fails by design and skips steps 8–41, including every walkability and whole-station gate; 30/30 recent runs failed |
| F-2 | **blocking** | robustness | `tools/export_scene.py:19` | the header advertises a material-coverage assertion the `deck` shot never runs; 2 groups / 2,208 tri on the fallback in every deck frame |
| F-3 | major | craft | `station/bespoke.py` C&C | the bridge console is 24 triangles an instance and reads as a flat plate at half distance |
| F-4 | major | craft | `station/customs.py` | the three authority-1 information boards are 12-triangle blank slabs while their text sits in `station/signage.py` |
| F-5 | major | craft | `tools/export_scene.py` light rig | no corridor light is shadow-castable; 2→18 casters is byte-identical; control in `docking_bays` moves 15.45% |
| F-6 | major | fidelity | `station/rooms.py:FIXTURES` | keyed by 11 archetypes, so `hydroponics` gets no growing equipment and reads as a plated box |
| F-7 | major | craft | `station/garden.py`, `drum_ground` | the habitat floor carries no objects at all, at 3.9% of its own triangle allowance |
| F-8 | major | craft | `godot/scenes/exterior.tscn` | 9 of 41 hull groups unbound and visibly untextured at half distance |
| F-9 | major | craft | `station/npc/body.py` | no face, stump hands, shoulder joint reads detached at room distance |
| F-10 | major | fidelity | `station/zocalo.py` | the neon wordmark is `zoc_neon_face`, 12 triangles; no planting, no backlit shopfronts, no crowd in the station's principal social space |
| F-11 | minor | craft | `interior_kit` light pilaster | the same glyph repeated seven times, indexable at 1.3 m |
| F-12 | note | — | `docs/AAA-STANDARD.md` | the PERFORMANCE ladder has no rung for *well measured and over budget* — every descriptor from 2 up contains "inside budget", so `budget.py`'s honest 205% cannot be scored without misdescribing the gate. `walkable_deck` is scored 2 for that reason and the reason is here rather than buried |
| F-13 | note | — | `tools/aaa_gate.py` | not referenced in CI; 52 errors on the committed scorecard |

---

## What I would do next, in order

Not a decision — the owner rules on direction, and session 4d's ruling is *the player's
experience, not more coverage*. Everything below is compatible with that reading.

1. **Put `continue-on-error: true` on the Performance budgets step, or move it to the end.** One
   line. It restores 34 assertions that this repository spent five sessions writing and has not
   run for thirty pushes. Nothing else on this list is worth doing first.
2. **Call `unmatched_groups()` on the deck shot** and promote the exterior note to a check. Two
   call sites; the function already exists and is already tested.
3. **Give the corridor a shadow-casting light.** One `_shadow=True` on the downlight class and a
   range that reaches the far wall. The single largest craft return in the project, and the
   control that proves it works is already written above.
4. **C&C's console, the customs boards, the Zócalo wordmark.** Three objects. They are the three
   most-recognised surfaces on the station and between them they are 84 triangles.
5. **Add a `%show` floor to layer 2b, or say out loud that the layer does not measure
   articulation against the reference.** Whichever — but a criterion that passes a room at 9.2%
   of the show while being *named* articulation is the next "shitty little cubes", and it is
   already written.

---

## Reproducing every frame in this report

```bash
python3 tools/judge_sweep.py --list          # the sample, with why each shot is in it
python3 tools/judge_sweep.py                 # re-render all 21; refuses anything not Forward+
python3 tools/judge_sweep.py --report        # renderer, exit and fallback groups per frame
```

`docs/judge-4e-frames.json` carries, for every frame: the exact `render_godot.sh` command, the
`renderer:` line the engine printed, the camera, the triangle and light counts, the mesh-instance
count, and every group the engine put on the fallback material. A frame with no row in that file
is not evidence from this round.
