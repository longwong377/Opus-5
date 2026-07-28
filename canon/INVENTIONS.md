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

---

## INV-010 — Deck pitch of 3.6 m

**Invented:** Floor-to-floor deck spacing of 3.6 m inside a ring zone
(`station/interior.py`, `DECK_PITCH_M`).

**Why necessary:** The rosette rings are 38–61 m deep, so they are zones rather than decks
(see `CONFLICTS.md` C-004 note). Nothing can be placed inside one without a deck pitch, and
level numbering indexes decks, not rings.

**Constrained by:** No reference states it. 3.6 m is chosen so that the ceiling height the
interior kit already carries — itself provisional, from `grey level 1.webp` proportions — sits
inside a floor-to-floor with a plausible service void above it. Deck counts that fall out are
sane against canon: Grey reaches 110 decks, which comfortably contains the on-screen "Grey 17";
Green reaches 75.

**Overturned by:** any frame where a deck's floor-to-floor can be measured against a person or
a door, or any plan giving a deck height. Changing `DECK_PITCH_M` re-derives every deck in
every ring; nothing else needs editing.

**Consequence worth keeping:** gravity is quoted per deck rather than per ring because it
genuinely differs across one. Ring 1's outermost and innermost decks differ by **0.155 g**,
which is felt walking down a single stair — 1.0000 g on deck 0 against 0.8448 g on deck 12.

---

## INV-011 — Drum end-cap relief: dish depth, rib size, plate segmentation

**Invented:** Three numbers in `station/interior.py`'s `drum_end_cap()` that the footage
constrains in kind but not in magnitude:

- `ENDCAP_DISH = 0.18` — the cap's sagitta as a fraction of drum radius, i.e. **50.1 m** of
  dish over a 278.3 m radius.
- `ENDCAP_RIB_W_M = 1.6`, `ENDCAP_RIB_H_M = 0.9`, `ENDCAP_STEP_M = 1.2` — radial rib width,
  how far a rib stands proud of its plates, and the axial depth of the step between courses.
- The **plate segmentation rule**: each course is divided into the number of plates that makes
  that course's plates closest to square, snapped to a multiple of four and clamped to 16–96.

**Why necessary:** The cap was measured off authority-1 footage in session 2r — rib radii,
eight to nine concentric courses, 48 rim lights at 7.4° ± 0.3°, a dished radially ribbed hub
cone over the inner ~20%, plates "roughly square", two courses checker-plated. Every one of
those is a **proportion or a count**. None of them is a depth, and a bulkhead with no relief
renders as a painted disc. Something had to be chosen to turn the measurements into geometry.

**Constrained by:**

- The dish is *observed to exist* — the concentric bands curve in both `Babylon_5_2-22_34b` and
  `33a` rather than reading as a flat plate — and 0.18 is a shallow torispherical head, the
  ordinary form for a pressure bulkhead closing a cylinder. It is the profile family that is
  sourced; the sagitta is not.
- The segmentation rule is a **derivation from a measurement, not a free choice**: "radial depth
  ≈ circumferential width" is what was recorded, and no single segment count can satisfy it
  across courses whose depths differ fourfold. Per-course counts are the only way to honour it.
  The rule reproduces the footage's most distinctive quality — fine plating at the rim, coarse
  toward the hub, and a cog-like ring of fine radial teeth inboard, which the Blue rosette
  description independently records in the same words.
- Rib and step sizes are set at human scale so the cap is walkable structure rather than
  ornament, and small enough (0.3–0.4% of radius) not to disturb the measured rib radii.

**Overturned by:** any frame giving the cap's depth against a known length — the core shuttle
tube's diameter where it passes through the hub would do it, and so would a profile view of the
drum's end in a cutaway. Changing `ENDCAP_DISH` re-derives the whole cap; nothing else edits.

**Not an invention, and worth separating out:** the cap's *aperture* is not chosen. The measured
hub cone fills the inner ~20% of the cap radius; the schema's core ring, read independently off
an authority-3 print diagram, sits at r/R = 0.18. Two unrelated sources landing 2% apart is a
corroboration, so the cap is built down to the schema's core radius rather than to a new number.
`interior.py`'s self-test asserts the two stay within 0.03 of each other, so a future edit to
either has to confront the other.

---

## INV-012 — Guideway truss: scale, height and count

**Invented:** The dimensions and placement of the drum's longitudinal guideway trusses in
`station/interior.py` — bay length 24 m, depth 16 m, chord section 2.2 m, web section 1.3 m,
chord radius at 0.85 of the drum floor radius (**41.7 m above the ground**), and **three of
them**, one per spoke plane.

**Why necessary:** The truss is the drum's most prominent interior structure and, as of the
`33a`/`34b`/`35a` reading, its **light source** — so nothing about the habitat's appearance can
be settled without it. The footage establishes what it *is* in considerable detail and gives no
absolute scale at all: there is nothing of known size in frame with it.

**What is sourced, and is not invention:**

- It is a **Warren truss** — parallel top and bottom chords, diagonal web members alternating
  up and down, no verticals. `Babylon_5_2-22_34b` shows the web unmistakably.
- Tram cars are **slung beneath the bottom chord** (`33a`, `34b`).
- A bright cylindrical **light run travels alongside**, with rectangular fixtures on the
  underside (`33a`, `34b`). This is what lights the habitat.
- It runs **longitudinally** and lands in a heavy collar on the **end cap hub** (`34b`).
- The web's proportions: measured off `34b`, the triangles are wider than tall. **The figure is
  the zigzag pitch to depth, roughly 1.2–1.5**, and the built bay-to-depth is 1.5.

  > **Corrected wording.** This bullet originally read "bay to depth roughly 1.2–1.5". A Warren
  > triangle's base spans **two** bays, so taken literally that sentence gives a bay-to-depth of
  > 0.6–0.75 — half what is built — and the next reader to trust it would have halved the truss.
  > Measured naively off the near end of `34b` the apparent zigzag-to-depth is 1.33 and the
  > apparent bay-to-depth is 0.67, so the recorded figure was the zigzag, uncorrected for
  > foreshortening. The **built 1.5 is not in doubt**: INV-017's rectification of the same frame
  > gives a car of 3.9 bays and 0.65 truss depths, and that only yields `34b`'s slender ~9 : 1
  > car silhouette if bay-to-depth is near 1.5. Only the sentence was wrong. Caught by the agent
  > that built the tram against this entry — which is the argument for writing inventions down
  > with their reasoning rather than only their values.

**Constrained by:**

- **The count is a structural argument, not a preference.** The Green truss is 2,586 m long.
  Nothing spans that unsupported, and the radial spokes are the only structure in the drum that
  could carry it. Placing the trusses in the spoke planes means each is held wherever it crosses
  one. The Green rosette draws **three spokes at 120°**, so there are three trusses.
  `SPOKE_COUNT` is now the single source of truth and `TRUSS_COUNT` derives from it; the
  self-test asserts they stay equal.
- **The height has a floor and a ceiling.** Below, it must clear the tallest land-use relief —
  the 7 m settlement terraces — with room for a tram, and it must not be so low that its light
  run illuminates a stripe rather than the ground. Above, a truss near the axis is in free fall
  and cannot be a guideway. 0.85 R sits between those, and the self-test asserts the lower bound.
- Bay and section sizes are set so a bay is a walkable span and the chords are structure a
  person could stand on, since the trams stop along it.

**Overturned by:** any frame putting something of known size against the truss — a person on it,
a docked tram whose door height can be read, or the drum wall behind it at a measurable radius.
Bay, depth and radius are single constants; changing them re-derives every truss.

**Consequence worth flagging:** the trusses now determine where the habitat's light comes from,
so their radius sets the drum's entire lighting geometry. If this number moves, every interior
lighting judgement made before the move has to be re-looked at rather than merely re-rendered.

---

## INV-013 — Pressure hull skin of 6.0 m

**Invented:** `HULL_SKIN_M = 6.0` in `station/interior.py` — the radial thickness of pressure
hull, frames and services between the outer envelope the radius profile reports and the
innermost radius an interior deck can use.

**Why necessary:** The drum's habitable volume is the deck stack **beneath** the habitat floor,
running outward from the canon 278.3 m to the pressure hull. Its depth is therefore
`hull − skin − 278.3`, and without a skin figure it is not computable.

**Constrained by:**

- Measured against the `habitat_cylinder` feature specifically, whose envelope runs **307.3 to
  327.7 m** — tight enough to be a real shell, unlike the whole Green sector, which ranges over
  128–480 m and averages to a number describing no surface that exists.
- 6.0 m over a 316.8 m mean leaves **32.5 m** of sub-floor stack, which is **9 decks** at the
  INV-010 pitch. Fewer than about 4 m of skin gives a hull thinner than the deck structure it
  carries; much more than 8 m and the sub-floor stack drops below eight decks, which is too few
  to hold the machinery a spun 2.5-million-ton habitat needs under its ground.

**Overturned by:** any cutaway showing hull thickness against a deck, or a frame in the
sub-floor levels from which a deck count to the hull can be read.

**Related weakness, recorded rather than fixed:** the existing `HULL_ALLOWANCE = 0.86` is a
*fractional* allowance and is still what every non-drum sector uses. A fraction is the wrong
kind of quantity for a skin — at the habitat cylinder it implies 44 m of hull, which is why it
could not be reused here. It should become metric everywhere, which would re-derive every
non-drum sector radius, so it is deliberately left for its own change rather than folded into
this one.

---

## INV-014 — The drum's land-use band table

**Logged retroactively.** `interior.LAND_USE` has driven the drum's appearance since the shell
was first generated and was never written up. Found by the agent that built the heightfield on
top of it, which is the right way round but a session too late.

**Invented:** The circumferential division of the drum's ground into six bands
(`station/interior.py`, `LAND_USE`) — fractions of circumference, land use, and relief in metres
against the 278.3 m floor:

| fraction | use | relief |
|---|---|---|
| 0.26 | arable | +1.2 m |
| 0.14 | settlement | +7.0 m |
| 0.10 | water | −2.5 m |
| 0.22 | arable | +1.2 m |
| 0.12 | settlement | +7.0 m |
| 0.16 | parkland | +2.4 m |

**Why necessary:** The drum's inner surface is 4.5 million m². A uniform cylinder reads as a
pipe, and nothing can be placed on the ground without knowing what kind of ground it is.

**Constrained by:** The *character* is authority 1 and is not invented — `Earhart's.webp` and
the far side through Talia Winters' window both show long continuous **longitudinal** strips,
greys and olive-greens with one broad orange-red band; `34b` shows an agricultural half and
`33a` a built-up half; `29a` shows the parkland at ground level as a designed park. The
**arrangement into six bands with these particular fractions** is not sourced, and neither are
the reliefs. What constrains them is that the sequence must put water at the lowest point of a
band group so it drains, must not put a settlement terrace where the guideway trusses fly
(41.7 m above the floor, so 7 m is safe by a wide margin), and must sum to exactly 1.0 —
asserted, after a species mix in this project once summed to 0.94 and silently dropped 6% of
the population.

**Overturned by:** Any frame establishing the drum's land use as a *map* rather than as a
texture — a production plan of the habitat, or enough of the circumference in one shot to count
the bands. Note the fractions are the parent of INV-015 and INV-016: changing them re-derives
the whole ground.

---

## INV-015 — Drum ground terrain spectrum

**Invented:** The heightfield's amplitude spectrum in `station/drum_ground.py` — six octaves of
value noise on a 437 × 431 m fundamental at 6.0 m amplitude, halving per octave, band-limited
to the 7.8 m Nyquist of the finest LOD — plus the within-band relief: arable gets the spectrum
at half amplitude with a ±0.55 m per-parcel level and a 0.22 m hedge bank; settlement gets a
2.0 m podium step per block cut by a 1.5 m avenue trench; water is a channel 5.0 m deep with the
surface clamped flat; parkland is three octaves at 0.33 amplitude.

**Why necessary:** No source gives a single elevation anywhere in the drum. The reference gives
tone, layout and character and gives no heights at all. The item is a heightfield; a heightfield
cannot exist without an amplitude spectrum.

**Constrained by:** Two of the three constraints are hard and neither is aesthetic.

1. **Amplitude proportional to wavelength is forced by the LOD budget, not chosen.** The error a
   stride-*s* decimation introduces is bounded by the amplitude of the octaves it drops. A flat
   spectrum — the naive "add some noise" — puts metres of error into the coarsest level and
   forces the finest LOD across the whole drum. That was measured, not argued.
2. **Every step is ramped over at least one coarse cell (31.2 m)** for the same reason: a step of
   height *H* costs roughly 514·*H* metres of switch distance.
3. The band datums are INV-014's and are not touched. The self-test asserts each band's mean
   tracks its table relief within 2.6 m — which is the file's weakest assertion, set from
   measured spread rather than from a principle, and recorded here as such.

**Overturned by:** Any frame in which a person, a vehicle or a building of known size stands
against drum terrain, giving an absolute vertical scale. A production elevation of the habitat
interior. Failing both, a steadier shot of the ground from a tram, from which relative relief
could be read against the known 41.7 m truss height.

---

## INV-016 — Drum ground parcels and roads

**Invented:** Arable parcels of 87.4 × 323.3 m — **elongated 3.7 : 1 along the axis** — warped by
34 m of noise so boundaries are irregular quadrilaterals, carrying one of four crops; settlement
blocks of 62.4 × 64.6 m with 62.4 m avenues; trunk roads 20 m wide with a 31.2 m verge on each
land-use boundary that does not touch water; ring roads 16 m wide, 28 m inboard of each cap rim.

**Why necessary:** Parcel size and road width are the two numbers that decide whether the ground
reads as farmland or as a lawn.

**Constrained by:**

- **Parcel size is counted, not measured**, and that limit is worth stating plainly: the only
  object of known size in any ground frame is the end cap at 278.3 m radius, and it is never at
  comparable depth to the fields in the same shot, so no absolute calibration is available. The
  agricultural half of `34b` reads as roughly ten parcels across the visible arc and the built-up
  half of `33a` as twenty or more, which against the 1,748.6 m circumference gives 100–200 m for
  farmland and 30–60 m for built parcels.
- **The 3.7 : 1 elongation along the axis is separately forced and is not a style choice.**
  `Earhart's` and the Talia Winters frame both show long continuous *longitudinal* strips, and a
  furrow ploughed across the drum climbs a 278 m hill that never ends.
- **Block and avenue sizes are not free at all**: they are exactly one and two coarse cells,
  because a feature narrower than the coarsest cell renders as a *different shape* at every LOD
  level.
- Road width from `33a`, where the trunk road carries a dashed centre line — so at least two
  lanes each way — and is about a third the width of the small parcels beside it. The ring road's
  existence and position are sourced from the cap zoom of the same frame; its width is not.
- No trunk road on a water boundary, because that is a road through a lake — and because it was
  measurably the largest LOD error in the field before it was removed.

**Overturned by:** Any near-overhead frame of the drum ground with an object of known size in it,
which would fix both parcel size and road width directly. A frame showing a bridge over the water
band would overturn the no-road-on-water rule specifically.

---

## INV-017 — Tram car: length, width, depth apportionment and suspension

**Invented:** The guideway tram's dimensions in `station/tram.py` — car length stored as
`CAR_BAYS = 4.0` truss bays (**96.0 m** at INV-012's 24 m bay), width 7.2 m, a vertical
apportionment of the measured depth into a 0.35 m suspension gap, 0.50 m shoe plate and 9.55 m
body, and a **non-contact magnetic suspension** of two dorsal shoe plates running under the
truss chords.

**Why necessary:** The guideway existed and the vehicle did not. Nothing in the reference set
puts a person, a door or any human-scaled object against the car or the truss.

**Constrained by:**

- **The length ratio is measured, and the measurement validates itself.** Projective
  rectification of `34b` about the drum-axis vanishing point makes the Warren zigzag uniform
  (78 ± 3 px) across a 4 : 1 range of depth, and under that rectification the near car spans
  **3.9 ± 0.25 bays**. Independently, the car measures 0.65 of the truss depth with no scale
  needed at all, and those two together only produce the slender ~9 : 1 silhouette `34b` plainly
  shows if the truss's bay-to-depth ratio really is about 1.5 — which is what is built. The
  measurements corroborate each other *and* the truss.
- **The metres are only as sound as INV-012**, which is why `CAR_BAYS` is the stored quantity: if
  the truss bay is ever corrected to 12 m the car becomes 48 m with no code change.
- **The suspension is geometry, not taste.** A mechanical bogie has nowhere to run — the truss's
  centre gap is crossed by a transverse tie every second bay, its outboard flanks carry the light
  runs, and wheels bearing on the chord undersides are upside down. A non-contact gap is the only
  reading that does not require inventing a hole in a truss already built and asserted.

**Overturned by:** Any frame putting something of known size on or in the car — a person in a
doorway, a platform, a door leaf — or a head-on or plan view, or a stop with a car stationary
against a platform.

**Recorded weaknesses, in the builder's own assessment:**

- **`CAR_WIDTH_M = 7.2` has essentially no evidential support.** No frame shows the car end-on or
  from above and `35a` is cropped both sides. It is 6% of the length and it sets the entire read
  of the interior. This is the softest number in the module.
- The second car in `34b` measures **5.4 bays** under the same rectification — a 30% disagreement
  attributed to its tail being occluded by a spoke, which could not be *proved*. Solving for a
  vanishing point that equalises the two cars gives x_v = 1350 against the chord-line fit's 991.5;
  the fit does not support it, but it could not be decisively ruled out either. If the vanishing
  point is wrong, both cars are wrong together.
- The apportionment leaves **6 m of dead depth** below the saloon floor. The alternative reading —
  that the dark band under the car in `34b` is partly the car's own shadow — is plausible and could
  not be distinguished at 118 px of car. A double-deck car would resolve the proportions neatly and
  is contradicted only by `33a` showing a single window band.

---

## INV-018 — Core shuttle tube radius

**Invented:** `CORE_TUBE_R_M = 19.5` in `station/core_tube.py` — the axial shuttle duct's outer
radius, stored as `CORE_TUBE_R_FRAC = 0.070` of the canon 278.3 m habitat floor radius.

**Why necessary:** The core shuttle's *ride* has been modelled since session 2h
(`physics/test_core_shuttle.py`, 18 tests) and the drum's end caps have carried a 50.1 m
aperture for it since session 2u, but the duct itself had no thickness. A tube needs one.

**Constrained by:** Measured as a **ratio**, off the Security Manual sectional schematic, at
seven columns through the drum: the duct's walls sit at y = 165–166 and 171–172 with its
centreline at 168–169, against the drum's innermost long deck lines at 121–122 and 215–216 —
giving a tube half-thickness of 3.0–3.5 px against a drum half-height of 47.0 px, i.e.
**0.064–0.075**. 0.070 is the middle.

Taking a *ratio of two vertical quantities* is the whole point: `00-MASTER.md`'s "Radial
spacing" ruling and C-004 UPDATE item 3 hold that this sheet's vertical scale is exaggerated
about 2× and no radial dimension may be read off it, and a **uniform vertical exaggeration
cancels in a ratio**. What does not cancel is resolution — a 7 px duct on a 339 px scan is
three or four pen widths — so the reading is coarse and is quoted as a range rather than a
figure.

*(An adversarial review caught the module citing **C-005** for this, which is a different defect
entirely — a horizontal splice in the Contract 5 scale bar. The argument was always aimed at the
vertical ruling; the citation was wrong, and a reader checking it would have verified the wrong
thing and concluded the defence held. Corrected in the module.)*

**Corroboration, not assumed:** 19.5 m passes through the end cap's 50.1 m aperture with 30.6 m
of clearance, and sits inside the schema's core ring (0 → 50.1 m) rather than redefining it. The
duct is the shuttle's running tube; the core *ring* is the zone containing it.

**Overturned by:** Any frame showing the shuttle car against the tube, or a docking collar of
known size on it, or a plan of the axis at a stated scale.

---

## INV-019 — Core tube articulation, hub and spoke ports

**Invented:** How the axial tube is broken up and how it lands at each end — collar groups of
4 fine rings every 130 m section, a 60 m hub flare of 4 stepped flanges carried 18 m past the
cap plane, 24 hub fins, and spoke ports of 27 m reach.

**Why necessary:** A 2.8 km unbroken cylinder reads as a pipe, and the trusses and spokes have to
land on *something* at each end.

**Constrained by:**

- **Articulation is sourced in kind**, from `33a`: the tube shows groups of six to nine fine
  rings at what read as section joints, spaced one and a half to three tube diameters apart, with
  smooth barrel between. The built 4 rings at 130 m is **3.3 diameters** — inside the observed
  spacing band, at the sparse end, which is what the drum's triangle budget affords across 2.8 km.
  The ring *count* is reduced from the observed 6–9 for the same reason and that is a budget
  decision, not a reading.
- **The hub's fin count is not free**: 24 is exactly half the end cap's measured 48-fold rim-light
  symmetry, so fins land on alternate cap segments rather than beating against them.
- **The port count is not free either**: the hub receives exactly `SPOKE_COUNT` trusses and
  `SPOKE_COUNT` spokes at the angles `interior.py` already uses, and the self-test asserts the
  match rather than restating the number.

**Overturned by:** Any frame giving the hub a scale against a known object, or showing the spoke
landing in detail. Note the whole entry is downstream of INV-018: change the tube radius and every
figure here re-derives.

---

## INV-020 — Corridor classes, and the concourse's dimensions

**Invented:** The three-class corridor taxonomy in `station/interior_kit.py`
(`CORRIDOR_CLASSES`), and the concourse class's width of **9.0 m** and rib spacing of **6.0 m**.

**Why necessary:** The kit modelled **one** corridor. The reference shows at least three, and
they are not variations on a width — they are different kinds of space, with different structure,
lighting and finish. Building 210 decks out of a single corridor profile would make the whole
interior read as one endless hallway, which is the opposite of what the footage shows.

**What is sourced, and is not invention:**

| class | frame | what it establishes |
|---|---|---|
| residential | `grey level 1.webp` | pale grey-tan, pilasters, horizontal wall banding, vertical light strips, chequered deck, portal frames. Narrow and finished. Already what the kit built. |
| concourse | `central corridor.webp`, `more hallway.jpg` | a tall volume framed by large **elliptical ribs**, lit strip down the deck centre, circular downlight pools, wall screens, and an **upper walkway** carrying pedestrians over the lower deck |
| service | `more hallways.jpg` | overhead truss instead of a soffit, vertical light tubes, a chequered lit strip in deck grating running the full length, warm backlit panels, litter on the deck |

The **elliptical rib arch** is the signature element of a Babylon 5 interior and the kit did not
have it at all — `ring_frame_spacing_m` existed as a constant with a comment pointing at
`central corridor.webp`, and nothing ever built one.

**Constrained by:**

- **One absolute length is measured, not chosen.** In `more hallway.jpg` an EarthForce officer
  stands in a circular downlight pool. At 1.75 m he is 261 px, giving **149 px/m** at his depth;
  the pool spans 234 px, so the pools are **1.57 m** across. `DOWNLIGHT_POOL_M` is that figure,
  and the self-test asserts the built geometry still matches it.
- **The concourse height is derived, not picked.** `central corridor.webp` shows an upper walkway
  with people standing on it above people on the lower deck, so the volume is **two decks** tall
  by observation. At the INV-010 pitch of 3.6 m that is **7.2 m**, and the self-test asserts it
  stays a whole multiple — a fractional height would land the walkway between decks.
- **The width is the weakest figure here.** 9.0 m is proportioned against the rib arches in
  `more hallway.jpg`, whose span reads as somewhat wider than the volume is tall. No frame gives
  a concourse width against a known length, because the officer stands in the middle of the space
  rather than against a wall.

**Overturned by:** any frame with a person against a concourse wall, or two people at known
separation across one. The width is a single constant; changing it re-derives every concourse.

**A winding bug worth recording, because it is the third of its kind.** `downlight_pool` and
`deck_strip` lie flat and must face **up**; ascending angle in the XZ plane with +Y up gives a
**downward** normal, so both were invisible from the only place they are ever seen. Caught by
rendering and seeing 836 of 2,100 triangles survive culling. The self-test now asserts upward
facing for every flat deck element, and the assertion was verified by reverting the fix and
watching it fail.

---

## INV-021 — Street and verge widths in the drum's settlement bands

**Invented:** `AVENUE_W_M = 10.0` and `VERGE_W_M = 4.0` in `station/drum_ground.py` — the made
width of a street between settlement blocks, and of the shoulder either side of a street or a
carriageway.

**Why necessary:** They existed implicitly and wrongly. Both the street's width and the road
kind-tag's width were taken from `_step_ramp_m()` — **one stride-8 cell, 31.2 m** — which is not
a width at all. It is a *constraint the LOD imposes on how sharply the heightfield may step*, and
using it as a feature size made:

- streets **31.2 m wide on 62.5 × 64.7 m blocks**, so about **74% of the settlement band was
  street** and the blocks were islands in it;
- trunk roads tag **51.2 m** against their own stated `TRUNK_ROAD_W_M = 20.0`.

**Constrained by:**

- **Neither number is free of the geometry.** The surface still ramps over the full 31.2 m,
  because it must; what changed is that the *kind tag* stops at the made width. A carriageway is
  now flat at its own width, then a verge, then untouched band.
- **10 m** is a two-lane street with footways on a 62.5 m block — a dense urban grid, which is
  what `33a`'s built parcels show: fine internal subdivision, not boulevards. It yields **29%**
  street by area, and the self-test asserts the measured coverage against that geometric
  prediction rather than against a remembered number.
- **4 m** is a kerb, gutter and planting strip. It is asserted to be less than a quarter of the
  LOD ramp, so the two can never silently re-merge.
- Trunk roads now measure **4.51%** of the drum's surface against **4.58%** predicted from four
  band boundaries at 20 m on a 1,748.6 m circumference — i.e. the stated width is now the
  rendered width.

**Overturned by:** any frame where a street's width can be read against a building or a person.
`33a` shows the built parcels from too far away to measure one.

**Two measurement traps recorded, because both produced confident wrong numbers:**

1. The block grid is 40 cells along the drum, so **w = 0.5 lands exactly on a block boundary**,
   where `d_edge` is 0 by construction. Sampling there reports *every* settlement cell as street.
   The original review's "62% street" and my own first re-measurement both hit this.
2. A first attempt at the fix set the verge tag to one full LOD ramp. Since that is half a
   block, it tagged **every** settlement cell as either avenue or verge and plain settlement
   vanished entirely. A width must be a width at both ends of the fix.

---

## INV-022 — Docking bay dimensions

**Invented:** `BAY_W_M = 42.0`, `BAY_H_M = 18.0`, `BAY_LEN_M = 140.0` in
`station/docking_bay.py`, plus the ledge, girder and floodlight pitches.

**Why necessary:** The bay is the hinge of the seamless launch-and-dock requirement — the flight
model and the docking solver have both existed since session 2g and had no room to arrive in. No
frame gives the bay an absolute size.

**What is sourced, and is not invention:**

- **24 bays** — Security Manual sectional schematic (authority 3), cross-checked on screen by
  "docking bay 17".
- **Blue Section is 520.4 m in diameter** — `00-MASTER.md` §1.1. The deck radius is that less the
  INV-013 hull skin: **254.2 m**, which puts the bay at **0.913 g**.
- **A long low slot, not a hangar box**; red-orange box girders overhead carrying pendant
  floodlights; stepped side ledges with chevron nosings on *every* step; a large red deck disc
  with a white oval emblem; the ceiling is the ribbed, curving inner wall of the rotating hull.
  All authority 1, `dock.webp` and `Minbari Flyer 969 in docking bay 17.webp`.

**Constrained by:**

- **The width is not a free number.** 42 m is the schema's own `cobra_bay` `width_m`, authority 3
  off Contract 5 — the width that document gives *this station* for *this class of structure*, a
  bay cut into a rotating hull to take a craft. Adopting it keeps one number rather than
  inventing a second, and the self-test asserts the bay fits its allotted arc: at 254.2 m radius
  each of 24 bays gets **66.5 m**, so a 42 m bay leaves 24.5 m of structure between neighbours.
- **The one measured length is the deck disc.** `dock.webp` is 1000×750; a dock worker stands
  ~28 px, giving **16.0 px/m** at that depth; the disc spans 170 px → **10.6 m**. The file of
  eleven workers then reads 19.4 m long, i.e. 1.94 m apart — a walking file, which is the
  consistency check that the scale is sane. The gazetteer is explicit that markings must be sized
  against the workers, **not** against the Starfuries, whose own size is itself derived.
- **Height and length are proportioned**, not measured: 18 m is low enough that the frame's
  flat-topped mouth reads as a slot, and 140 m holds the row of parked craft the frame shows.

**Overturned by:** any frame with a person against a bay wall, or a craft of known length parked
across the bay rather than along it.

**A geometric consequence worth keeping.** The bay is cut into a *rotating* hull, so its deck
follows an arc rather than a chord. The first placement mapped the bay's width along a **tangent**
and pushed both walls 0.9 m *outside* the pressure hull. Corrected, the deck cambers **0.87 m**
across its 42 m width — small, but enough that a craft parked across the bay sits measurably
nose-down relative to one parked along it, and it is the reason a bay is not a hangar.

---

## INV-023 — Signage board dimensions

**Invented:** `BOARD_W_M = 1.10`, `BOARD_H_M = 1.48`, and the frame, inset and mounting heights
in `station/signage.py`.

**Why necessary:** `reference/01-station-exterior/welcome to babylon 5.webp` is the **only frame
in the entire reference set showing readable station signage**, and it is cropped to the boards
themselves — there is nothing of known size in it. The proportions are sourced; the scale is not.

**Constrained by:**

- The frame shows the panel **markedly taller than wide**, with a wide flat frame and the lit
  face set back inside it. The 3:4 ratio is measured off the frame; only the absolute size is
  chosen.
- **The mounting height is bounded at both ends and asserted.** The board must span standing eye
  height (1.7 m) or it cannot be read, and its underside must clear a walking crowd. 1.35 m to
  1.35 + 1.48 = 2.83 m satisfies both.
- **The size is checked against legibility rather than taste.** A capital stays readable to about
  250× its height when looked for and half that at a glance. This board's body text gives a
  ~57 mm capital, so it serves **6.4 m at a glance and 12.8 m if sought** — which is what decides
  how many boards a concourse needs, and says one board covers a bay of a hall, not the hall.

**Overturned by:** any wider shot of the customs hall showing a board against a person or a door.

**Not an invention, and the more important half of the module:** the board **text is transcribed
verbatim at authority 1**, including the prop's own spelling — `ARANGEMENT` with one R and
`ATMOCHEMICAL`. Both are on the screen-used board and both are reproduced; the self-test asserts
they survive, because a well-meaning correction is exactly how a transcription rots.

**Three facts these boards establish that are not signage at all**, and that nothing else in the
project held:

| | |
|---|---|
| **Six atmospheres** available simultaneously, others to order | a life-support requirement with a number in it, and the mechanic behind the alien sector and Kosh's encounter suit |
| The station runs on **Earth Mean Time (EMT)** | every NPC schedule in `station/npc/schedule.py` was implicitly on some clock; this names it |
| There is a **Business Center**, handling currency exchange | a sourced location the gazetteer can place |

---

## INV-024 — Command & Control room dimensions

**Invented:** The room's plan in `station/command_control.py` — a 14 × 12 m upper floor, a 4.6 m
stepped command dais, five standing consoles over a 150° arc, a 1.9 m drop to the forward pit,
and light strips at 2.35 m and 3.55 m.

**Why necessary:** C&C is the most-seen room in the show and the gazetteer ranks it fourth. It
also pays a structural debt: the exterior `observation_dome` component is a box primitive, and
C&C's window is that dome's glazing seen from inside — the two must agree or the station has a
window looking out at nothing.

**What is sourced:** a great circular window on radial spoke mullions crossed by a concentric
ring band; a raised circular dais on a stepped plinth; wedge consoles on slim legs, lit; two
courses of horizontal light strips; stairs down at the right; a lower forward pit of red-lit
consoles; **two occupied levels in one volume**, which is what makes it read as a bridge.

**Constrained by:**

- **Dome dimensions are read from the schema, not restated** — radius 46 m, height 34 m,
  Contract 5 authority 3 — and the self-test asserts they match and that the window fits inside.
- **The window is measured, and the measurement needed a correction I first omitted.** The
  officer stands 175 px in an 816×616 frame → 100 px/m *at his depth*. Fitting the window's arc
  (chord 280 px, sagitta 215 px) gives 306 px across. Dividing those directly gives **3.1 m and
  is wrong**: the window is in the bulkhead *behind* him, and pixels-per-metre falls with
  distance. At ~5 m to the officer and ~4 m more to the bulkhead the scale there is 56 px/m, so
  the window is **5.5 m**. A factor of 1.8, and the same trap that put the tram car length in
  dispute in C-008.

**Overturned by:** a wider shot of C&C, or any frame showing the dome's glazing from outside.

**Five defects the assertions caught while building it**, all invisible in a render and each
found by a test rather than by looking:

1. **The glazing was laid flat.** `disc()` builds in XZ at a height; the window needed XY at a
   depth. The glass ended up on the ceiling while the mullions stood correctly in the bulkhead.
2. **The measurement above**, uncorrected for depth.
3. **The mullions were full-diameter bars**, so sixteen of them piled up at the centre into a
   solid starburst with no glass between them. A spoked window has a hub; they now run from it
   to the rim.
4. **The bulkhead had no aperture.** It was one solid slab with the glazing laid on it, so the
   glass was sealed inside 0.30 m of steel. An opening is a hole in something, and the something
   has to be built with the hole already in it — four panels around it, not a slab.
5. **The glazing faced out of the room.** Ascending angle in XY gives a +Z normal, which points
   through the bulkhead and is culled from the only side anyone stands on. Fourth instance of
   this family in the project.

The assertion that caught (4) was itself wrong first time round: it required the glass to stand
*proud of* the bulkhead, which fails a correctly glazed window. Glass sits **in** an opening. It
now checks that the glazing fits the aperture and lies within the bulkhead's depth.
