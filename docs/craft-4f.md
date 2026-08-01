# The four landmarks that scored CRAFT 1 — what was built, and what it costs

**Session 4f. Builder, not reviewer.** Everything below is a claim about four files —
`station/command_control.py`, `station/council_chamber.py`, `station/customs.py`,
`station/docking_bay.py` — and the frames that back it.

**Renderer, stated on every frame because session 4e's whole visual pass was invalidated for
want of this line:** every frame in this document was produced by
`Vulkan 1.4.318 - Forward+ - llvmpipe`, from a detached `git worktree` at the session's own
HEAD so that nothing another actor was mid-editing could land in a frame. The render helper
greps the engine's own `renderer:` line and refuses to copy the PNG out if it does not say
`Forward+`.

---

## The finding this comes out of

`docs/judge-4e.md` scored four authority-1 locations at **CRAFT 1**, which
`docs/AAA-STANDARD.md` defines as *"a box primitive standing in for a named object"*:

| subject | craft | the judge's one-line reason |
|---|---|---|
| `command_control` | 1 | the station's bridge console is a flat orange plate, 24 triangles an instance |
| `council_chamber` | 1 | the form is right and every colour and light behaviour in the authority-1 frame is absent |
| `customs_arrival` | 1 | the three information boards whose text is authority-1 verbatim are blank 12-triangle slabs |
| `docking_bay_interior` | 1 | none of the reference's girders, chevrons, gantry or deck emblem read |

Its sharpest sentence is structural rather than aesthetic, and it is the reason this work is
worth doing rather than deferring: **`interact.py` resolves the register's declared `console` to
`cc_console_leg`, a 24-triangle box, and counts it in "357/357 declared interactables resolve",
because layer 5's criterion is "the declared interactable types exist" and a box passes every
word of it** — the same sentence, structurally, as layer 2's topological criterion.

---

## Triangle cost, per module, before and after

| module | before | after | ×  | what the increase bought |
|---|---:|---:|---:|---|
| `command_control` | 2,064 | **5,664** | 2.74 | nine articulated consoles, a key light, a balustrade, a working pit |
| `council_chamber` | 5,950 | **11,382** | 1.91 | a perforated lit panel, five delegate stations, an enclosure with pilasters |
| `customs` (one hall) | 7,296 | **22,988** | 3.15 | three framed screens with legible text, two lettered boards, four counters, a schematic |
| `docking_bay` (one bay) | 3,943 | **13,347** | 3.39 | thirteen lattice trusses, 39 flood fittings, ledge equipment, a bollard row |
| **total** | **19,253** | **53,381** | 2.77 | |

**Two thirds of the customs increase is lettering, and it is the expensive kind on purpose.**
`signage.letter_mesh` emits single-sided decal quads — 4,824 triangles for the five surfaces in
this room — and `deck.py` blesses that convention with a two-part exemption. `bespoke.py` does
not: `SHELL_OPEN_EDGES["customs"]` is **0**, and `bespoke._selftest` measures this module's raw
output including its lettering, so 4,824 decal quads would take that ledger from 0 to 9,648 and
turn a gate in a file this session does not own **red, for content that is correct**.
`customs.solidify_lettering` turns each glyph quad into a closed six-triangle pyramid instead:
14,472 triangles, **zero open edges**, no cross-file edit, and a rim that catches the panel's own
light at a grazing angle. The alternative — keep the decals and change one line in `bespoke.py` —
is recorded here because it is the cheaper option and it was not taken for a stated reason.

### What this does to `station/budget.py`

`budget.py` is honestly over budget and the failing gates are on the **assembled `blue/0/0`
deck**, not on any single room. Three of the four modules land on that deck and one does not:

- `cnc` and `customs_north` / `customs_south` / `arrival_concourse` are all on `blue/0/0` and all
  compose as **bespoke**, so their increase is resident on that deck.
- `docking_bays` is on `blue/0/0` and composes as **generic** (`interact.resolve_place` reports
  `built=generic`), so **none** of this session's docking-bay work reaches the walkable deck. It
  is visible only in `--shot interior --room docking_bays`. That is a pre-existing fact about
  `bespoke.NOT_COMPOSED` and it is stated here because it bounds what the frames below prove.
- `council_chamber` is on a different deck entirely (Green, z 4,100).

**Measured: `station/budget.py` is byte-for-byte unchanged by this session, and the reason is a
limitation of the gate rather than a property of the work.**

```
before: subject blue/0/0: 6 rooms over 345 deg, 736,412 triangles, 386 groups
after : subject blue/0/0: 6 rooms over 345 deg, 736,412 triangles, 386 groups
        FAIL frustum structure   123,279 / 60,000   (205.5%)   <- identical
        FAIL resident triangles  736,412 / 180,000  (409.1%)   <- identical
        18/21 within budget, over: frustum structure, structure share, resident
```

`deck.z_clusters("blue", 0, 0)` returns **six** clusters — 6880, 7120, 7440, 7920, 7960, 8000 —
and `budget.py`'s standing frame builds the first one it is given. That cluster is z ≈ 7120: the
docking bays and their neighbours, where `docking_bays` composes **generic**. `cnc` is on the
7960 cluster and the three `customs` places on 7440, and **`budget.py` measures neither**. This
is the same shape of limitation CLAUDE.md already records against `deck.py --sweep`
(*"it once read 99 of 118 because it built `z_clusters(...)[0]` alone"*), still live in the
budget gate.

So the honest figures are arithmetic rather than a measurement, and they are stated as such:
the 7440 cluster gains **3 × 15,692 = 47,076** triangles (customs is instanced as
`customs_north`, `customs_south` and `arrival_concourse`, all `module=customs`) and the 7960
cluster gains **3,600**. Against blue/0/0's own 736,412-triangle resident set those are +6.4%
and +0.5%. Neither is measured by a gate today and neither is claimed to be free.

---

## 1 — Command & Control: the console

**Frames: `docs/engine-4f-cnc-half.png` (half distance, lens 46° → 24°, the judge's own method)
and `docs/engine-4f-cnc-normal.png`.** Camera pinned to `judge-4e`'s exact eye and target so the
before/after is the same view.

Read at 4× off `reference/03-sector-blue/comand and contorl.webp`
(`tools/refzoom.py --box 0.36 0.35 0.72 0.58`), the console is **five tiers** and the module had
one of them:

1. slim round **splayed legs** with a cross-tie, and clear air under the desk
2. a dark **under-valance**
3. an **apron of backlit panes**, three to a unit, recessed in a frame
4. a **raked bed** behind a raised bezel lip
5. dense **blocks of control cells** on the bed — the green, amber and red the docstring has
   always named — in three banks, each bank a recessed sub-panel carrying its own cells

All five are built, in `console_unit`, and the same builder makes the **forward pit's red-lit
consoles** — which the docstring has described since it was written and which had never existed:
the pit was a floor, two side walls and nothing else, on one of the room's two occupied levels.

Two things came out of building it that are worth more than the object:

- **`CONSOLE_W_M` was a written 1.15 m against an arc pitch of 1.026 m**, so all five consoles
  interpenetrated their neighbours by 12%. Nothing could see it because a plate has no volume to
  share. The width is now derived from the arc and a gate asserts the two.
- **`light_dais_key` is a `FIXTURE_LIGHTING` entry measured in this room's own frame** — *"a
  hard-edged pool with a body-shaped hole in it"* — and the only geometry on the station carrying
  the name was in `rooms.py`'s worship archetype. C&C had no key light at all, which is why
  `--gate-lighting` reads `cnc 0.0%` of its working plane inside any source's range, the worst row
  in the table. It has one now, at the 3.5 m the measurement states.

**The key light was A/B'd against the layer-4 gate before it was kept**, because adding light to a
room with a committed exposure frame is exactly how a craft fix breaks a lighting gate. Measured
by `tools/measure_frame.py --against` at the exposure shot's own 640×360:

| | committed `engine-cnc.png` | **new, with the key** | new, key suppressed (control) |
|---|---|---|---|
| median vs reference | ×1.06 **OK** | **×1.16 OK** | ×0.96 **OUT OF RANGE** |
| p99 (band ×2.58) | ×0.69 | **×1.06** | ×0.68 |
| crushed | 32.07% | 26.33% | 34.66% |
| distribution | PASS | **PASS** | PASS |

The control is the interesting column: **the new geometry without the key would have taken the
room's level out of window**, because articulation is mostly dark casework. With it the level
improves and p99 goes from ×0.69 to ×1.06 against the show.

**Honest craft score: 3.** It reads as the intended object at its normal distance and it holds at
half. It is not 4: the cell blocks are the same three-bank pattern on all nine units, the bed
carries no wear, and the green register is `device_screen_glass`'s green-**white** because a
saturated green indicator does not exist in `materials.py` and that file is not this session's to
edit.

---

## 2 — Customs: the boards say it on a surface

**Frames: `docs/engine-4f-customs-half.png` and `docs/engine-4f-customs-normal.png`.** Camera
pinned to `judge-4e`'s.

Three defects, all closed:

- **`board_pair()` is `board()` twice, and `board()` is the UNLETTERED constructor.** The two blue
  wall boards carried the most-quoted signage in the show as blank panels. They now go through
  `board_lit`, which reads `signage.BOARDS` — misspellings (`ARANGEMENT`, `ATMOCHEMICAL`) and all.
- **The three suspended screens were 12-triangle slabs.** They are now bezel, recessed lit face,
  status strip and content: the WELCOME board **verbatim, including the smoking line this module
  transcribed and nothing had ever rendered**; the header and badge under a bust silhouette on the
  left; and the station's own schematic on the right.
- **`customs_desk` was four 48-triangle slabs** at the one point on the station where a player is
  processed by another person. They are `dressing.machine(..., "counter", ...)` now — the same
  builder `rooms.PROP_KIND` already maps `customs_desk` onto for the generic path, so the bespoke
  room and the generic one cannot describe one object two ways.

Two things the frames caught that no gate would have:

1. **The text rendered and could not be seen.** `customs_screen_*` binds `device_screen_glass` at
   emission (0.93, 1.00, 0.92) × 0.8 and `sign_text` binds `sign_text_lit` at (1.00, 0.97, 0.62) ×
   0.9 — 5% of luminance apart. `signage.py` states the rule this file should have read first:
   *"A LIT SIGN IS BOTH THE BRIGHTEST AND THE DARKEST THING IN THE FRAME."* The field is
   `sign_face` now, which is what every door plaque on the station already uses.
2. **`signage.fit_cap_m` clamps caps at 0.060 m**, which is right for a 1.1 m door plaque and
   means a 3.2 m board hung 26 m up a hall is lettered at a twentieth of its own panel.
   `_lettering` fits the block into a face *k* times smaller and scales the result back by *k* —
   a uniform positive scale, determinant *k*² — where *k* is derived as the smallest factor that
   lifts the natural fit clear of the clamp. With `sg.wrap` at 22 columns the welcome board's caps
   are **134 mm, readable to 33 m in a 34 m hall**; the unwrapped 42-character smoking line gives
   67 mm and 17 m.

**The right-hand screen is the station.** `schematic_lines` reads `interior.load()`'s hull profile
at 26 stations across 8,046.9 m and draws it at **true aspect** on the screen's diagonal — hard
rule 4 applied to a prop, so a hull change redraws the arrival hall's map of itself with no edit
here. The first version scaled the radius to fill the panel and the render came back as a lumpy
white continent; the station is 17:1 and a drawing of it that is 2:1 is a drawing of something
else. There is a gate on the aspect now.

**Honest craft score: 3.** The boards are the thing the room exists for and they read, at both
distances. It is not 4: the hall itself is unchanged and still very dark (`judge-4e` measured
53.01% of the frame below the measurable floor and that is a rig question, not a geometry one),
the desks read as dark slabs at hall distance, and the bust is a dome and a box.

---

## 3 — The docking bay: the overhead steel is a lattice

**Frames: `docs/engine-4f-dockingbay-normal.png` and `docs/engine-4f-dockingbay-half.png` at the
shipped exposure, and `docs/engine-4f-dockingbay-gain.png` at `--light-gain 6.0`.**

**The gain frame is a diagnostic and is labelled as one.** The bay renders at 63.95% below the
measurable floor and no amount of geometry changes that — it is `FIXTURE_LIGHTING`'s two shadow
casters and `bay_lamp`'s 30 m range in a 140 m bay. The shipped-exposure frames are the craft
evidence; the gain frame is how the geometry can be checked at all.

The module's own docstring has always said the overhead steel is *"deep box girders spanning the
width, **carrying a lattice gantry**"*. The lattice was never built and each girder was **one
solid box, 12 triangles for a 42 m span**. The reference's ceiling is open — two chords with a
zig-zag web and the light showing through every panel — and a closed box cannot express any of it.
Thirteen Warren trusses now, plus the longitudinal runners they carry.

Also built, all of it absent before:

- **Floodlights as fittings** — a stem, a yoke, a hood, and a lens. The lens keeps the `bay_lamp`
  name and the housing deliberately does not, because `fixture_lights` hangs one lamp per tagged
  body and tagging the hood would silently double the bay's 39 measured floods. The render
  confirms **39 sources before and after**.
- **Service gantries and handling equipment on the ledges**, which the second authority-1 frame
  describes in as many words and which the bay had none of — six `dressing.machine` kinds on the
  tread the reference stands them on.
- **The bollard row** — "about twenty small white bollards", `reference/00-INDEX.md`'s own reading.

**Honest craft score: 2, rising to 3 in the gain frame.** At the shipped exposure the truss reads
as a silhouette and the ledge equipment reads as mass; that is CRAFT 2's *"right mass, no
articulation"* and it is a lighting-limited score rather than a geometry-limited one. The
chevrons are still a continuous painted band rather than alternating blocks — 700 chevron pads at
12 triangles each is 8,400 triangles for a stripe a material already carries, and that trade was
declined rather than forgotten.

---

## 4 — The council chamber: the panel is perforated

**Frames: `docs/engine-4f-council-normal.png` and `docs/engine-4f-council-half.png`.**

**The camera is NOT `judge-4e`'s, and that is a finding rather than a convenience.** Its eye sits
at r = 14.2 m, *outside* the chamber's own 11 m floor — `open_standpoint` put it there because
the room had no walls to stand inside. With the enclosure built, that camera looks at the back of
a wall. The frames here are taken from inside, and the eye and target are in the commands below.

The room's one defining sentence, quoted at the top of the module since it was written, is *"a
perforated gold mesh front panel lit from within: the furniture is the light source"*. What was
built was a smooth 80-triangle emissive band. **A material can make a band gold; only geometry can
make it perforated**, and the difference is what the eye uses to tell a lit panel from a light
*behind* a panel. `mesh_grille` puts a bar grille in the 55 mm recess the bench profile already
cuts — 105 bars at a 115 mm pitch, crossed by two rails. It is the strongest single thing in this
session's frames.

Also: **five delegate stations** — pad, nameplate, screen, microphone — on twelve metres of bench
that carried nothing anywhere, on a location whose register entry declares `delegate_bench` and
`speaking_position`. And an **enclosure**: a plate behind the fin fan and an arc outside the
mosaic's rim, both inside the room's existing extent, so the fan stops radiating against black.

**The enclosure had to be articulated and a gate is what said so.** Built as two plain surfaces it
added ~410 m² of blank wall and `density.py` took the chamber from **93.7% of its floor to 85.2%**
— it was already the one location of these four that FAILS layer 2b, and a bare wall made the
number worse while making the frame better. That is exactly the trade the criterion exists to
refuse. Pilasters at 1.85 m, a cornice, a dado, a skirt and a 100 mm mid-bay reveal took it to
**108.8% — the chamber now PASSES layer 2b for the first time.** The reveal is the cheapest line
on the station: 372 triangles across both walls, and it is the difference between 96.9 and 108.8.

**Honest craft score: 3 at the bench, 2 elsewhere, so 2 for the room.** Score to the lowest
descriptor that is fully true: the fins are flat slabs at half distance, the bench top is an
undifferentiated white surface, the chair lattice is a perfectly regular grid the eye can index,
and every *colour* finding in `judge-4e` is still open because it lives in `materials.py`.

---

## Gates: what was run, and what changed

```
station/command_control.py   43/43     (was 29/30 — see below)
station/council_chamber.py   39/39     (was 28/28)
station/customs.py           51/51     (was 35/36 — see below)
station/docking_bay.py       36/36     (was 36/36)
station/test_materials_layer3.py       bespoke 384/384 groups over 16 of 16 modules
station/interact.py                    cnc 4/4 · council_chamber 3/3 · customs_north 5/5 ·
                                       customs_south 3/3 · docking_bays 5/5, all unchanged
```

**Two of the four modules were already RED when this session opened them, for the same reason.**
`command_control` asserted `len(nm) == 48` and measured 44; `customs` asserted `== 54` and measured
50. Both are pegged copies of a computed number that improved upstream — `rooms.articulate`'s
proud bands got better and nobody re-pegged a constant living in a file the change did not touch.
`docking_bay.py` had already recorded this exact defect and its cure, and both modules now use it:
**attribute every non-manifold edge to the groups whose triangles use it, and require each to be
explained** by an `articulate` band or by a named, declared contact. A new group interpenetrating
anything fails at any count; an upstream improvement cannot fail it at all. Both carry a negative
control that duplicates one of the module's *own* solids and fires.

**Defects the new gates caught during this session, each on its first run:**

| gate | what it caught |
|---|---|
| `council_top faces up` | the delegate pads were wound with a negative y normal — desk pads facing the deck |
| `nothing but the declared contacts is non-manifold` (customs) | 36 edges where the screen bezels' rails butted their lit face, and 12 more where the four rails butted each other |
| the same gate, again | 8 pre-existing edges where the X-brace's head member butted the diagonals' own end points, which the pegged-count version could never have separated from the bands |
| `no edge carries more than two faces` (council) | the backing wall's skirt band sharing the plate's bottom edge exactly |
| the engine's own `fallback material used by` line | `cc_key_housing`, a group name that resolved to nothing |
| `neighbouring consoles butt, they do not interpenetrate` | five consoles overlapping by 12% since the room was written |

### Layer 2b, before and after

`station/density.py`, whole-location line density. `%bar` is the gate; `%show` is the same row's
ungated comparison against a Babylon 5 set.

| location | `%bar` before | `%bar` after | `%show` before | `%show` after |
|---|---:|---:|---:|---:|
| Command & Control | 170.9 PASS | **213.0 PASS** | 12.6 | **15.7** |
| Customs hall, north / south | 108.7 PASS | **112.7 PASS** | 12.9 | **13.4** |
| Docking bays (24) | 155.3 PASS | **179.8 PASS** | 15.0 | **17.4** |
| Council chamber | **93.7 FAIL** | **108.8 PASS** | 9.5 | **11.0** |

The council chamber is a gate that **flips from FAIL to PASS**, and it flipped twice on the way:
93.7 FAIL → 85.2 FAIL when the bare enclosure went in → 96.9 FAIL with pilasters, cornice and
skirt → 108.8 PASS with a mid-bay panel joint. The whole-station line now reads
**123/128 at or above the floor, with all five remaining failures in the drum.**

The judge's point about `%show` stands and this session does not close it: **the median location
still carries about a seventh of a Babylon 5 set's line density**, the gate binds on a triangle
budget rather than on the reference, and four rooms going from 9–15% to 11–17% does not change
that. It is the next under-specified criterion and it is already written down.

---

## Reproducing every frame

Rendered from a detached worktree at the session's own HEAD, with these four files copied in.

```bash
tools/render_godot.sh --shot interior --room cnc \
    --eye=-5.535,1.7,-1.825 --target=5.965,1.7,2.25 --res 1280x720 \
    --out docs/engine-4f-cnc-normal.png
tools/render_godot.sh --shot interior --room cnc \
    --eye=-5.535,1.7,-1.825 --target=5.965,1.7,2.25 --fov 24.0 --res 1280x720 \
    --out docs/engine-4f-cnc-half.png

tools/render_godot.sh --shot interior --room customs_north \
    --eye=-0.125,1.7,1.125 --target=0,1.7,33.125 --res 1280x720 \
    --out docs/engine-4f-customs-normal.png
tools/render_godot.sh --shot interior --room customs_north \
    --eye=-0.125,1.7,1.125 --target=0,1.7,33.125 --fov 24.0 --res 1280x720 \
    --out docs/engine-4f-customs-half.png

tools/render_godot.sh --shot interior --room docking_bays \
    --eye=-0.125,1.7,1.125 --target=0,1.7,139.125 --res 1280x720 \
    --out docs/engine-4f-dockingbay-normal.png
tools/render_godot.sh --shot interior --room docking_bays \
    --eye=-0.125,1.7,1.125 --target=0,1.7,139.125 --fov 24.0 --res 1280x720 \
    --out docs/engine-4f-dockingbay-half.png
tools/render_godot.sh --shot interior --room docking_bays \
    --eye=8.0,2.0,24.0 --target=-4.0,15.0,62.0 --light-gain 6.0 --res 1280x720 \
    --out docs/engine-4f-dockingbay-gain.png      # DIAGNOSTIC, not the shipped exposure

tools/render_godot.sh --shot interior --room council_chamber \
    --eye=0,1.7,9.0 --target=0,3.0,-3.0 --res 1280x720 \
    --out docs/engine-4f-council-normal.png
tools/render_godot.sh --shot interior --room council_chamber \
    --eye=0,1.7,9.0 --target=3.6,1.15,1.4 --fov 24.0 --res 1280x720 \
    --out docs/engine-4f-council-half.png
```

---

## What is still open, and owned by nobody in this session

1. **The chevrons are a painted band, not chevrons.** Declined on cost, above.
2. **Every colour finding in `judge-4e`'s council paragraph** — the pale blue-green mosaic, the
   deep blue behind the medallion, gold rather than white on the lit panel. All `materials.py`.
3. **`--gate-lighting` still reads badly for these rooms.** C&C now has its measured key; the
   docking bay's 39 floods still cannot reach a 42 m width at a 30 m range, and customs' one cast
   fitting reaches 3.5 m into a 17 m hall.
4. **The green console register is a green-white.** One indicator material in `materials.py`
   closes it.
5. **`docking_bay.py`'s work does not reach the walkable deck**, because `docking_bays` composes
   generic. Closing that is `bespoke.NOT_COMPOSED` and `docs/deck-mouth-exemption.md`.
