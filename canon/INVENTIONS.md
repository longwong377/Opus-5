# Invention Log

Everything built without reference backing, recorded permanently so that "what the show
established" and "what we extrapolated" never blur together.

Each entry states what was invented, why it was necessary, what constrained the choice, and
what evidence would overturn it.

---

## INV-001 — Section proportions rescaled from a contradicted source

**Invented:** All section dimensions in `00-MASTER.md` §1.1 — Blue/Red/Green section diameters
and lengths, bio-habitat interior dimensions.

**Why necessary:** Only one source (`other map 4.jpg`) gives a complete dimensional breakdown,
and its overall length contradicts show canon by 2.589×.

**Constrained by:** Miller's proportions are internally consistent and cross-check correctly
(π × D × L reproduces his stated surface area). Rescaling preserves every ratio and changes
only the absolute scale, which show canon fixes independently at 8,047 m.

**Overturned by:** any production drawing with dimensions, or a frame allowing a section to be
measured against a known-size object (a Starfury, a docking bay, a human figure).

---

## INV-002 — Rotation rate of 1.79 rpm

**Invented:** Station rotation period of 33.5 s (ω = 0.18775 rad/s).

**Why necessary:** No rotation rate is stated on screen, but spin gravity cannot be simulated
without one, and it determines Coriolis magnitude everywhere.

**Constrained by:** The show depicts normal human gait and unremarkable gravity in habitation
sections → 1.0 g at the habitat floor. With r = 278.3 m fixed by INV-001, the rate follows
exactly. The result (1.79 rpm) lands comfortably below the ~2–3 rpm human tolerance threshold,
which is a meaningful independent sanity check rather than a coincidence.

**Overturned by:** dialogue or a display stating a rotation rate or gravity value; or a shot
of the drum interior long enough to time the rotation against a fixed feature.

---

## INV-003 — Adoption of the longitudinal sector model

**Invented:** Treating sectors as longitudinal ranges rather than nested radial layers.

**Why necessary:** Hull geometry must be built before interiors, and only the longitudinal
model constrains hull geometry. See `CONFLICTS.md` §C-003.

**Constrained by:** `other map 2.jpg` ties each sector name to a visible hull position.

**Overturned by:** resolution of C-003. **NOW OVERTURNED — see CONFLICTS.md C-003 UPDATE.**

Completing the longitudinal framework showed that only 50% of the station is pressurised, that
the habitable volume is four separated regions, and that the Green section alone accounts for
73% of it. Six sectors cannot be laid out as longitudinal slices across that, because Grey and
Brown would land on unpressurised truss spine. The longitudinal model is retained only as
exterior labelling; interiors must use a nested model.

This invention did its job: it was adopted provisionally to unblock hull geometry, it was
logged rather than assumed, and the geometry it produced is what disproved it.

---

## INV-004 — Per-species name grammars

**Invented:** Generative naming patterns for Narn, Centauri, Minbari, human, Drazi, pak'ma'ra
and Vorlon residents (`station/npc/names.py`).

**Why necessary:** Canon population is 250,000 (authority 1). Hand-authoring that many names
is not possible, and a shared syllable pool would be immediately wrong — a Narn name and a
Centauri name are never mistakable for each other on screen.

**Constrained by:** Each grammar is fitted to names actually spoken on screen, and each records
its evidence in the code. Narn from G'Kar, Na'Toth, Ta'Lon, G'Quan, Na'Far, Du'Rog. Centauri
from Londo Mollari, Vir Cotto, Urza Jaddo, Carn Mollari — where Londo and Carn sharing Mollari
is what establishes that the second element is a *house*, not a surname. Minbari from Delenn,
Lennier, Neroon, Draal, Dukhat, Rathenn. Human surnames span several real-world traditions
because Earth Alliance is explicitly multinational.

**Evidence quality varies and is flagged in the code:**

- **Vorlon has two attested names** (Kosh, Ulkesh). A generator on two data points would be
  invention dressed as inference, so Vorlon is a **closed list**, not a generator, and a test
  asserts it stays one.
- **Drazi are usually addressed by title on screen**, so their pattern is inferred from
  phonetics rather than from attested names. Marked THIN EVIDENCE.
- **pak'ma'ra** rests mainly on the species name itself, which carries the pattern:
  three short elements, apostrophe-separated, lowercase.

**Overturned by:** any further attested names, particularly for Vorlon or Drazi, which would
convert inference into evidence. Adding an attested name to a grammar's `attested` tuple and
re-running the tests is the intended workflow.

---

## INV-005 — Species rhythms, roles and population mix

**Invented:** Per-species sleep/meal rhythms, the role roster, shift rotation, and the
station's species mix (`station/npc/schedule.py`).

**Why necessary:** Canon population is 250,000 with a stated species variety, but no source
gives proportions or daily rhythms. NPCs cannot have schedules without them.

**Constrained by:**

- **Minbari broken sleep is canon** — the show establishes they wake for a period mid-rest.
  Modelled directly, and it produces a real visible effect: Minbari abroad in corridors at
  hours nobody else is.
- **Centauri social life is depicted as nocturnal and drink-centred**, so they retire near
  dawn rather than merely late. A first pass had them asleep from 01:30, which left them
  asleep through the small hours — not what nocturnal means.
- **Narn discipline** follows the Regime's depicted military character.
- **Downbelow's unemployed** are a canon population, so `lurker` is a role with zero work hours.
- **Species mix is inferred from on-screen crowd composition** — humans dominant, Narn and
  Centauri the most visible non-humans, League species filling the remainder. Not stated
  anywhere; this is the weakest part of the entry.
- **pak'ma'ra feeding hours** are inferred from the depicted friction over their carrion diet,
  and marked INFERRED in the code.

**Overturned by:** any stated population proportion, or dialogue establishing a species'
sleep habits. The `RHYTHMS` and `STATION_MIX` tables are the only things that need editing.

**Two bugs this caught, worth recording because they are the failure modes of the design:**

1. **Resolving sleep before work against an unshifted rhythm put the entire night watch to
   bed.** Security showed *zero on duty at 02:00* — the station was unguarded from midnight to
   morning. Sleep now follows the shift offset, so a night-shift worker sleeps during the day.
2. **The species mix summed to 0.94**, so the aggregate layer silently dropped 120 of every
   2,000 residents. Exactly the quiet population leak the statistical layer exists to prevent.

---

## INV-006 — Exterior surface machinery: what it looks like and where it is dense

**Invented:** The whole procedural greebling pass — `station/greeble.py` plus the `greebles:`
block in `station/schema/station.yaml`. Three separable claims:

1. **The vocabulary.** That the hull carries access panels in short rows, louvred vent banks,
   octagonal hatches, sensor blisters on plinths, antenna stubs, magnetic cleats and marker
   light housings, at the sizes given (fittings 15–50 m across, standing 3–11 m proud).
2. **The density tiers.** Assemblies per km² of hull: minimal 8, clean 26, standard 42,
   cluttered 88, industrial 105 — a 13× spread from the finished drum skin to the reactor spine.
3. **The zone assignment.** Which longitudinal feature is finished skin and which is exposed
   plant, including the `cluttered` tier on `aft_hull_block`.

**Why necessary:** ADR 0002 commits the project to rule-scattered instanced detail rather than
hand modelling, and 12.7 km² of hull cannot be detailed any other way by an agent. Uniform
density would have been an invention too, and a worse one: the reference shows the contrast
between sections is the most legible thing about the model's surface treatment.

**Constrained by:**

- `reference/01-station-exterior/exterior more.jpg` (orthographic production sheet, auth 2) at
  5× magnification. It shows a clamped conduit running the full flank of the habitat drum,
  comb-like grille banks on the reactor and forward structures, large flat plate breakup on the
  drum, and small blisters and drums riding the dorsal ridge. Every kind in the vocabulary
  traces to something visible there; nothing was added that is not.
- **Size** is constrained from below by legibility, not chosen freely. The first implementation
  used 10–20 m fittings; rendered and inspected, they read as noise at any range beyond ~100 m.
  Sizes were raised until the detail read as installed machinery.
- **The `cluttered` tier on `aft_hull_block`** is the one placement claim with a canon hook:
  canon exterior system 11, *raw material storage bays (5)*, sits immediately aft of the habitat
  cylinder, which puts bulk-handling plant in that section; and `other map 2.jpg`'s exterior
  labelling runs Grey then Brown at the aft end. It is *not* a claim that Downbelow is there —
  C-003 rejected the longitudinal sector model for interiors and this makes no interior claim.
- The **triangle budget**, which caps the whole pass at 18% of the exterior allowance.

**Overturned by:** any high-resolution photograph of the physical production model or a
sufficiently close exterior shot from the show, either of which would replace the tier
assignment with observation. Resolution of C-003 would also move the `cluttered` zone if it
places the service and industrial functions elsewhere on the hull.

**Deliberately not claimed:** greebles carry no dimensions of their own into the schema. They
read the same radius profile the lathe does and sit on whatever surface it reports, so nothing
downstream can build on a greeble position. Deleting the entire pass would change nothing but
the look.

---

## INV-007 — Corridor section and wall build-up

**Invented:** The corridor's cross-section proportions and the wall's course heights in
`station/interior_kit.py` — chamfer size, skirt / dado / rail-band / plate-course fractions,
portal spacing and depth, pilaster size, deck tile pitch.

**Why necessary:** The kit cannot be modelled without a section, and the absolute dimensions
that would fix one (corridor width, ceiling height, deck spacing) are blocked on C-004.

**Constrained by:** Two authority-1 frames, and only those two:

- `reference/07-sector-grey/grey level 1.webp` — the only frame showing a corridor wall
  square-on. It fixes the *build-up*: a projecting skirt, a set-back dado, a heavy rail band
  at roughly hip height throwing a deep shadow reveal, then courses of large plates with
  recessed seams; bullnose pilasters at the portal jambs carrying segmented vertical light
  strips; warm downlights low on the wall; a deck of fine tiles.
- `reference/05-sector-green/corridor in alien sector.webp` — an **aperture** shaped as a
  chamfered polygon, corners at roughly 45°, in a heavy frame with a pronounced reveal. It is
  unambiguous and it is the strongest single observation behind the kit.

Neither frame is a circular bore, so `ring_frame` is wrong for a corridor. That much is
observed: the first assembly used it and read as a pipe, and `central corridor.webp`'s circular
ribs belong to a two-storey volume, not a corridor.

**Carrying the chamfer from the aperture to the corridor's own section is an inference, not an
observation, and it is the weakest link in this entry.** What the alien-sector frame shows is a
doorway seen head-on; nothing in it establishes that the passage behind has the same profile.
The one frame that does show a corridor's head — `grey level 1.webp` — shows a **rectangular
portal header**, which if anything argues the other way, though it is oblique, motion-blurred
and shows no wall/ceiling junction cleanly enough to settle it. The chamfer is adopted because
one sourced profile beats none and because a doorway is usually cut to the section it sits in;
that is reasoning, not footage.

Everything invented here is recorded as a **proportion**, not a metre value, and lives in
`PROVISIONAL`. The proportions are what the footage establishes; the height they multiply is
not, so resolving C-004 should change the table and nothing else.

**Overturned by:** a production floor plan or set drawing; or any frame in which a corridor can
be measured against a known-size object. A frame showing a corridor of visibly different
section would narrow the claim to the sectors it covers rather than overturn it. **Any frame
showing a corridor's wall-to-ceiling junction square-on overturns the chamfer directly** — it
is the cheapest part of this entry to settle and currently the least evidenced.

---

## INV-008 — Pressure door leaf mechanism

**Invented:** That a pressure door's leaves part on a vertical centreline and slide into the
jambs (`"bi_parting"`).

**Why necessary:** A door has to open, and the kit has to say how.

**Constrained by:** The aperture is sourced and the mechanism is not. **No frame in the
reference set shows a door leaf at all** — open, closed or moving. What
`corridor in alien sector.webp` does fix is the opening: a chamfered polygon, taller than
wide, with straight vertical jambs and a threshold you step over.

That geometry **rules out an iris**, and on geometry rather than taste: an iris sweeps a disc,
and a disc inscribed in this aperture leaves all four chamfered corners unswept. It cannot
seal the opening that is actually there.

Two readings survive, and both are built — `"bi_parting"` and `"horizontal_split"` — selected
by one entry in `PROVISIONAL`. The straight vertical jambs are what favour the bi-parting
default: they are the surface a leaf would seal against and retract into.

**Overturned by:** one frame of a B5 door operating. This is the cheapest invention in the log
to overturn and the most likely to be, so it is deliberately a table lookup rather than a
shape: changing the default is a one-word edit, not a remodel.

**Also invented, and smaller:** the door's control panel is a plain plate beside the frame at
the height the hand-held identicard reader is used at. The reference set contains the hand-held
reader (`11-props-and-technology/Identicard reader.webp`) but no wall-mounted one, so nothing
more specific than a plate is claimed.

---

## INV-009 — Aurora-class Starfury airframe dimensions

**Invented:** Every dimension in `station/starfury_geometry.py` — overall length 6.0 m, span
9.26 m, fuselage and canopy sections, boom sweep and bow, nacelle profile, engine bell size,
root fairing planform, tip vane comb, RCS outrigger struts and the ventral gun pod.

**Why necessary:** `canon/00-MASTER.md` fixes the station at 8,047 m and names the Starfury
only as a defence asset ("two Starfury squadrons"). It gives the fighter **no dimensions at
all**, and `reference/12-starfury/` contains no orthographic sheet and no scale bar. The craft
is flyable and enterable in this simulation, so it has to have a size.

**Constrained by, in descending order of force:**

1. **The flight model, which was here first.** `station/physics/starfury.py` already places
   four mains at (±3.4, ±3.4, −2.1) m, lateral and vertical RCS at 3.4 m on the cardinal
   meridians, and a retro at (0, 0, +2.4) m. Those are not adjustable here — the mesh is built
   around them, and `station/test_starfury_geometry.py` fails if the two stop agreeing. They
   are what makes the craft **markedly wider than it is long** (9.26 × 6.0 m): the mains and
   the retro are only 4.5 m apart, while the X spans nearly 10 m.
2. **A pilot has to fit.** The canopy is sized from a *reclined* seated human — Burg draws the
   seat raked, and a craft pulling 1.87 g along its own long axis wants the load through the
   seat back rather than head to foot. `cockpit_volume()` derives the clear volume from the
   canopy loft and the test asserts 1.85 × 0.90 × 0.95 m minimum; it comes out
   1.92 × 0.98 × 1.02 m at 15.3° nose-down.
3. **Arrangement, from reference.** Compact fuselage under a flat arrowhead deck; long faceted
   canopy raking forward and *down* out from under it; four booms in an X; an axial nacelle at
   each boom tip with the main bell projecting aft; forward-facing nozzle mouths at the nose
   and at each nacelle tip; vaned plate structures outboard. All four files in
   `reference/12-starfury/` agree on this — two scans of Burg's 1993 sheet (authority 2), one
   on-screen frame (authority 1), one community model (authority 4).
4. **The design premise: no lift surfaces.** Every plate on the craft — root fairings and tip
   vanes — lies in the plane containing its own boom's radial direction and the roll axis. The
   test measures this as the fraction of plate area whose normal is tangential (88% and 77%);
   a horizontal wing would score near zero.

**Overturned by:** any production drawing, model sheet or licensed manual giving Starfury
dimensions; or a frame showing a Starfury against something of known size — a cobra bay mouth,
the docking sphere, a human on a hangar deck. Any of those would replace the whole parameter
block, though the thruster anchors would still have to move in `station/physics/starfury.py`
first, and the test would force the mesh to follow.

**Two things worth recording because they shaped the result:**

- **The four RCS mount radii are physically inert.** In the flight model each lateral and
  vertical RCS thrust vector is parallel to its own position vector, so `cross(position,
  force)` is exactly zero and none of them produces torque. Their 3.4 m radius therefore
  changes nothing about how the craft flies; it is pure geometry. It is honoured exactly
  anyway, on slender struts rather than the plates a first pass used — with plates the craft
  read from dead ahead as an **eight-armed asterisk** instead of an X, which is the one
  silhouette a Starfury must never have.
- **The nacelle runs along the roll axis, not along its boom.** The first version ran it along
  the boom, which put the bell's cavity inside the nacelle's own body and left the craft with
  **no visible engines at all from dead astern**. Caught by rendering that view specifically,
  which is worth doing for any craft whose aft aspect is its signature.

**Deliberately not claimed:** mass, thrust, inertia and performance all stay where they already
were, in `station/physics/starfury.py`. This file adds no physical properties — only a shell
around the ones that existed.

---

## INV-010 — Station material palette

**Invented:** The surface properties of every material in `godot/materials/` — metallic,
roughness, specular, emission energy — plus the decision that the exterior hull albedo carries
a slight warm bias, plus the procedural weathering on `hull_exterior`.

**Not invented — measured.** Every *colour* here was sampled off reference rather than chosen.
The measurements are recorded below so a later session can re-run them rather than trust them.

| Material | Sampled from | Authority | Reading |
|---|---|---|---|
| `hull_exterior` | `01-station-exterior/exterior more.jpg`, lit plating | 2 | rgb (0.390, 0.390, 0.391) — **S = 0.00, exactly neutral** |
| | `01-station-exterior/Cobra Bays with starfurries.webp`, lit hull | 1 | H 20°, S 0.21 — warm, but that is the key light |
| `structural_truss` | same sheet, truss spine | 2 | V 0.23 against hull's 0.44 — the darkest thing on the station |
| `radiator` | same sheet, blade panel | 2 | H 221°, S 0.43–0.78, V 0.29 — deep blue, the most saturated element |
| `cargo_module` | same sheet, dorsal boxes | 2 | H 351–5°, S 0.25–0.47, V 0.29 — red-brown |
| `swept_array` | same sheet, top-view swept blades | 2 | V 0.34, near-neutral — darker than hull, not white |
| `hull_banding_red` | same sheet, forward waist banding | 2 | H 357°, S 0.81, V 0.34–0.54 |
| `accent_warning` | `more zocalo.png`, `Cobra Bays…`, `sleeping-in-light-05.jpg` | 1 | H 12–20°, S ~0.68 — mean rgb (0.667, 0.306, 0.215) |
| `emissive_signage` | `zocalo.webp`, `Zocalo neon signage in background.jpg` | 1 | bright cyan (0.42, 0.98, 1.00) |
| `emissive_floor` | `sleeping-in-light-05.jpg` deck strip; `central corridor.webp` | 1 | blows to white; lower half reads (0.83, 0.83, 0.87) cool-white |
| `marker_light_*` | `Cobra Bays with starfurries.webp` | 1 | "red and white marker lights on the columns"; 96% of the frame's saturated-bright pixels are H 15–20° |
| `hull_interior` | `07-sector-grey/grey level 1.webp` | 1 | plate clusters S 0.09–0.19, V 0.20–0.42 |

**The one finding worth carrying forward: the hull is neutral, and the blue was the lighting.**
Before this session every surface used one material at `metallic = 0.72`, and the render came
out steel blue against a reference set that is warm in every single frame. A near-fully
metallic surface takes almost all of its colour from what it reflects, and the only thing to
reflect was a blue ambient. Dropping metallic to 0.34 and giving the albedo a small warm bias
fixed it. **The albedo was never the problem and tinting it warmer would have been the wrong
fix.**

**Two red accents, not one.** They were nearly conflated:

- **H 357°, S 0.81** — exterior structural banding at the forward waist, authority 2. Applied
  to `cobra_bay` (z 6980–7250) on the strength of that position.

  **Corrected in adversarial verification: the overlap is partial, not exact.** Isolating the
  red pixels on the sheet and mapping them against the drawn station extent (side view spans
  px 91→1195 of 1280, 7.29 m/px) puts the forward-waist red at **z ≈ 6630–7120**. It therefore
  begins ~350 m aft of the bays and stops ~130 m short of their forward end — about half the
  bays' length is covered and about half the red falls on `forward_taper` instead. The binding
  is a weaker positional coincidence than this entry first claimed, not a stronger one.

  The second half of the correction matters more for how it looks: on the sheet the red is a
  **thin longitudinal line**, the width of a rail or a conduit run, on otherwise grey structure.
  `hull_banding_red` paints the *whole* `cobra_bay` solid, so the render puts 28 saturated red
  blocks where the source has a hairline. Right register, wrong area — the fix is a banding
  strip in `components.py`, not a different colour.
- **H 12–20°, S 0.68** — the interior red-orange of handrails and hazard framing, authority 1,
  three independent frames. `docs/interior-kit-spec.md` §3.

Same mistake shape as the Zocalo neon in session 2q, where a cyan wordmark and orange alien
script were being treated as one signage colour. Two registers that look alike at a glance are
worth measuring separately before assuming they are the same paint.

**Constrained by:**

1. **`exterior more.jpg` has a blue cast over the whole sheet** — its background plate measures
   H 219°, S 0.26. Absolute hue off it is worthless. Only *differences within the image* were
   used: truss darker than hull, radiators more saturated than hull, cargo warmer than hull.
   That is why the neutral hull reading (S = 0.00 against a background at S 0.26) is trustworthy
   and is the strongest single number in the table.

   **Re-derived under adversarial verification, because a single patch is a weak basis for the
   headline claim, and it survives on a better argument.** Sampled as a population instead —
   every lit pixel of the drum in the side view, 23,051 of them — the hull is *not* neutral on
   average: median S 0.165 at H 240°, and only 27% of pixels sit below S 0.03. Taken alone that
   would refute the entry. What settles it is that **saturation falls monotonically with
   brightness** and R and G stay equal to three decimals at every level:

   | V band | mean S | mean rgb |
   |---|---|---|
   | 0.25–0.35 | 0.250 | 0.231, 0.231, 0.304 |
   | 0.35–0.45 | 0.165 | 0.333, 0.333, 0.395 |
   | 0.45–0.55 | 0.104 | 0.447, 0.447, 0.493 |
   | 0.55–0.70 | 0.087 | 0.557, 0.556, 0.602 |
   | 0.70–1.00 | 0.052 | 0.783, 0.783, 0.818 |

   Only the blue channel moves; the ramp is an additive lift that the key light washes out. A
   blue *albedo* would hold roughly constant saturation from shadow to highlight, and this does
   the opposite. So the neutral reading stands, and the reason it stands is the gradient rather
   than the one patch. Worth keeping because the same test — does saturation survive being lit —
   separates paint from lighting on any reference frame.
2. **Metallic and roughness have no source at all.** No reference frame lets a specular lobe be
   measured. They were tuned by rendering and looking, against the constraint that the rendered
   luminance distribution should sit near the authority-1 frame's rather than three stops above
   it. Final render median luminance 0.344 against a reference median of 0.122; still brighter,
   because the reference frame is a shadowed close-up and this is a fully-lit beauty shot.

   **Verification note.** Both figures reproduce independently — 0.343 and 0.118. The problem is
   the reference, not the arithmetic: that frame is `Cobra Bays with starfurries.webp`, a **bay
   interior at night**, and `01-station-exterior/` holds **no authority-1 exterior hull frame at
   all** — its other four files are the production sheet, a Downbelow corridor, a signage
   close-up and a duplicate of the drum interior. Nothing anywhere else in `reference/` is an
   exterior either. So `tonemap_exposure = 0.45` is anchored to a frame that cannot calibrate an
   exterior, and it now governs every future render. The image is well exposed on its own terms
   — 1 clipped pixel in 1.44 M, p95 luminance 0.618 — so this is a **reference gap rather than a
   tuning error**, and it belongs on the reference wants list beside the deck plans.
3. **Weathering is procedural, not sourced.** `hull_exterior` carries two `NoiseTexture2D`
   layers — albedo mottling at 0.74–1.0 and roughness breakup — triplanar at a 180 m world
   period, because the export has no UVs to sample any other way. Nothing in the reference
   establishes a weathering pattern; what it establishes is that the hull is not uniform.

**Overturned by:** any authority-1 or authority-2 exterior frame with a neutral reference in it,
or a licensed paint-scheme sheet. Specifically, a frame showing the cobra bay surrounds in plain
hull grey would overturn `hull_banding_red`'s binding to `cobra_bay` — that binding rests on the
banding being drawn at the same z as the bays, which is coincidence of position, not a caption.

**Deliberately not claimed:** `observation_dome`, `observation_rotunda` and `docking_sphere` are
left on `hull_exterior`. They are glazed volumes over lit interiors and almost certainly should
not be opaque hull, but no reference in the set shows them lit from outside, and a glowing dome
is a large, prominent guess.

---

## INV-009 — Brown as a radial designation

**Invented:** Treating Brown Sector / Downbelow as the outermost annular ring spanning other
sectors, rather than as a longitudinal length of station.

**Why necessary:** The Security Manual sectional schematic brackets only five sectors —
Yellow, Grey, Green, Red, Blue. Brown is absent. But Brown is spoken of constantly on screen
as a place people go, so it has to be somewhere.

**Constrained by:** On the same sheet, "Down-Below" appears as a label on the **outer band**
in the Green region rather than as a bracket. The Brown rosette in `other map.png` independently
marks DOWNBELOW with a double-headed arrow spanning an **outer annular band**. Two sources
place it radially outward rather than longitudinally.

**Overturned by:** any source bracketing Brown as a length of station, or dialogue placing
Brown fore or aft of a named sector rather than above or below one.
