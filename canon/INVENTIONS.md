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

## INV-042 — Aurora-class Starfury airframe dimensions

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

## INV-043 — Station material palette

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

---

## INV-025 — Council chamber dimensions and seat count

**Invented:** The 4.6 m bench radius over a 150° arc, the 1.12 m top height, the fin and
medallion geometry, and `SEATS = 5`.

**Why sourced where it is:** `council chambers.webp` (authority 1) gives the curved bench with a
**perforated mesh front panel lit from within**, high-backed **open lattice** chairs, a radiating
fan of fins, a spoked medallion, a **polygonal mosaic** floor, and a speaking-position fan on the
bench top. Green sector placement is authority 3 (`other map.png` Green rosette).

**The seat count is a LOWER BOUND, not a number.** Five delegations are visible and the arc runs
past both edges of the frame, so five is what can be counted, not what is there. `SEATS` is a
parameter and the self-test asserts only `>= 5`. Asserting equality would be asserting something
the reference does not say. A wider shot or an authority-3 plan would fix it; neither is held.

**Overturned by:** any wider shot of the chamber.

**A winding lesson worth recording, because I got it wrong in both directions.** The medallion's
spokes and its concentric rings are built in the same plane and face the same way, but their
quads are wound differently — spokes go radial-then-tangential, rings go tangential-then-radial,
which flips the cross product. 264 triangles were facing the wall; I "fixed" the spokes as well
as the rings and broke 48 that had been correct. **Two orientations in one function, and assuming
they shared one cost a round trip.** The assertion caught both the original fault and my
overcorrection, which is the argument for asserting orientation per group rather than per module.

---

## INV-026 — The hull allowance is metric, and the shell it measures from is extracted

**Invented:** `HULL_SKIN_M = 6.0` applied to every sector rather than only the drum;
`CORE_HULL_WINDOW_M = 60.0`; and `sector_shell_radius()`, which takes a sector's outermost
deck floor from the longest run of near-constant core-hull radius inside its band.

**What it replaces.** `HULL_ALLOWANCE = 0.86`, a fraction of the mean envelope radius, in place
since the interior model was first written. It was the wrong kind of quantity twice over:

- **A fraction is not a thickness.** It removed 65 m of notional structure in Grey and 22 m in
  Yellow. Pressure hull, frames and services do not scale with how far a sector sits from the
  spin axis; a 6 m shell is 6 m everywhere.
- **The mean of a band describes no surface.** Yellow's band ranges 18–440 m and Blue's
  116–268 m. Multiplying those means is arithmetic *about* a shape rather than a measurement
  *of* one, and there is no point in either sector where the hull is at its own mean.

**How the shell is found.** `radius_profile.json` traces the station's outline, so it reports
whatever stands proud at each z. Session 2b established the separation: a protrusion is local in
z, the hull varies slowly, so a wide running minimum approximates the core hull. A running
minimum alone **erodes at a step** — it reported 428.7 m in Grey, below Grey's own narrowest real
sample of 436.4 m, a radius no point in the sector has. The operator is therefore a morphological
**opening**, erosion then dilation at the same window, which strips features narrower than the
window and restores the edges of those wider than it. Asserted per sector: the opened profile
never falls below the band's own raw minimum.

**What constrained it — and this is the part worth trusting.** Run against the band containing
the habitat cylinder, the generalised extraction returns **314.3 m**. `habitat_hull_radius()`, an
entirely separate derivation written four sessions earlier — a plain mean over one *named schema
feature* — gives **316.8 m**. **2.5 m apart on a 315 m radius, 0.8%, from two methods that share
no arithmetic.** That is the cross-check that justifies applying the method to the four sectors
where no independent measurement exists.

**A second thing it fixed, which was not the target.** `drum_sector()` identified the drum by
matching a *hull* radius against the 278.3 m *floor* radius — a category error, comparing a
surface to something 32 m inside it. On the corrected shell radii that comparison picks **red**,
whose shell sits 274 m out, four metres from where the Garden's ground is. Matched hull-to-hull
the drum wins at 2.5 m with red 42.7 m behind, a 17× margin. The old code got the right answer
for the wrong reason: the drum band's mean was inflated by the aft hull block it happens to
contain. The self-test now asserts the **margin**, not the winner — a test that only checks who
won cannot tell 17× from a coin toss, and this decides which band the entire habitat is built in.

**Consequence.** Every non-drum sector radius moved outward. The station goes from 210 decks and
2,646 cells to **251 decks and 3,414 cells**, 80.5 M → **110.2 M triangles** of interior
structure. Red, Blue and Yellow were all being cut short.

**Overturned by:** any sourced figure for pressure-hull thickness, or a deck plan establishing an
outermost deck radius in a named sector.

---

## INV-027 — The habitable gravity ceiling, and the station's basement

**Invented:** `HABITABLE_G_MAX = 1.25`, and with it the `use` tag — `habitat` or `plant` — on
every deck in the station.

**Why this exists at all.** `STATE.md` recorded Grey's 1.445 g outermost deck as "the visible
symptom" of the fractional `HULL_ALLOWANCE`, to be fixed when the allowance went metric. **That
was wrong, and fixing the allowance is what proved it wrong: Grey got heavier, not lighter —
1.445 g → 1.693 g.** The 0.86 fraction had been quietly deleting 65 m of hull that is really
there. Grey sits on the aft hull block, the widest structure on the station at 478 m envelope
radius — identified in session 1 as the station's widest structure, which Miller's table never
names — and no honest allowance moves it inboard. A rigid body spinning at a rate fixed by the
habitat floor puts 1.7 g on anything 471 m out. That is not a bug to be corrected; it is what the
shape means.

So the premise was wrong rather than the arithmetic. The design response is the one any real
station would make: **you do not put quarters at the bottom of a gravity well, you put mass
there.** Tankage, reservoirs, waste processing, reactor auxiliaries, ballast.

**What constrained the number.**

- **Lower bound, 1.117 g.** The drum's own sub-floor stack runs out to the pressure hull at
  310.8 m, and that space is occupied — it is the service level under the Garden and
  `LAW-CRIME-DOWNBELOW.md` sites people in it. The station demonstrably houses people to at
  least 1.117 g, so the ceiling cannot sit below it without contradicting geometry already
  built. **The self-test asserts exactly this**, and it is the assertion that fails first if
  anyone lowers the constant.
- **Upper bound, ~1.5 g.** Sustained occupancy at 1.5 g is a permanent 50% weight penalty on a
  civilian population, which is not somewhere quarters get sited.

1.25 g sits between them, clear of the drum's demonstrated 1.117 g. Radius **347.9 m**.

**What it produces.** Grey's outer 123 m — **34 of its 105 decks** — become plant. Every other
sector is entirely habitat. That is 26% of the station's interior structure reclassified, and it
is a place the scope asks for by name: *"the physical plant that makes 250,000 people possible:
food, water, air, power, waste."* The fraction was concealing it behind a plausible number.

**It also unmasked a budget error.** The cell gate priced deck 0 of the first deck-stack ring,
which is the outermost deck, which in Grey is plant — charging tankage at the corridor kit's
285 tri/m. That put the worst cell at **94.8% of budget** and implied habitat corridors had 5%
of headroom left for props, signage and NPCs. Split by `use`, the worst *habitat* cell is Grey
ring 2 deck 11 at 1.246 g and **66.2%**. They have 34%. Both are still gated — a plant deck is
not free, and exempting it is how a subsystem grows without anything noticing — but the plant
figure is explicitly a placeholder priced with the wrong kit until plant space has its own.

**Overturned by:** any on-screen statement of gravity in a named sector, or dialogue placing
quarters somewhere the geometry puts above 1.25 g.

---

## INV-028 — The plant kit: bays, tank farms, deep frames and catwalks

**Invented:** everything in `station/plant.py` — `BAY_DECKS = 5`, the frame section and pitches,
`TANK_R_M = 4.5`, the farm lattice (`FARM_PITCH_DEG = 30`, `FARM_PITCH_Z_M = 100`, 2×2 tanks),
`CATWALK_W_M = 1.8` / `CATWALK_CLEAR_M = 2.4`, and the pipe runs.

**Why it exists.** INV-027 tagged Grey's outer 34 decks `plant`, and the manifest was still
pricing them with the corridor kit — **62.3 M triangles, 26% of the station's entire interior**,
for volume that is not rooms.

**The one structural decision, and what constrains it.** Plant space is **not decked at
`DECK_PITCH_M`**. A 3.6 m floor-to-floor pitch is a corridor's pitch and a tank farm wants
height, so the 34 decks regroup into 7 bays of ~17.7 m. `BAY_DECKS = 5` is squeezed from both
sides: fewer than four and a bay is too short for a tank worth plumbing; more than six and 34
stops dividing without a large runt. The 4-deck remainder is kept as a shallower top bay rather
than dropped — a runt bay is real volume, and this project has shipped a "finished" surface with
4,064 open edges by rounding one away.

**What the tankage is constrained by, and why the assertion is not circular.** Tank *count* is
**not** derived from the volume it must hold. It falls out of the farm lattice — how many farms
fit round the circumference and along the sector at a fixed pitch — and the self-test then asserts
the result clears `LIFE-SUPPORT-AND-INDUSTRY.md` L-04's **397,500 m³** thirty-day reserve. A
sparser lattice would fail it. Laid out: **1,232,508 m³, 3.1× the reserve**, which is the right
kind of margin because water is not the only commodity (fuel slush, coolant, greywater, waste
holding all share the farm).

**And a second assertion in the opposite direction**, because the first one alone would reward
filling the zone: tankage must stay **under 10% of the plant volume**. It sits at **0.88%**. The
first implementation tiled the annulus wall-to-wall and produced **65.1 M m³ — 164× the reserve
and 46.6% of the zone**, which is precisely the error the gazetteer warned against. Two
assertions bracketing a quantity from both sides is what caught it.

**Result: 453,528 triangles for the whole zone against the 62,273,664 placeholder — 0.7%.**

**Overturned by:** any on-screen view of the station's machine spaces, of which we hold none.

### Four defects, three found only by rendering it

The self-test passed 21/21 while three of these were live. Recorded because the pattern is the
project's oldest and this is the clearest instance of it.

1. **`_place()` reverses winding.** Its Jacobian is `d/dx = (-sin, cos, 0)`, `d/dy = (cos, sin, 0)`,
   `d/dz = (0, 0, 1)` — determinant **−1**, because local +x becomes tangential and +y becomes
   radial, which is a left-handed pair. Everything through it came out inside-out. Found by
   standing on the catwalk in a render and **seeing the magenta background through the floor**.
   `CONTRIBUTING.md` already records this twice — `_box` emitting inward solids, and
   `corridor_section` laying its deck through a negative-determinant remap. Third instance.
   `_absorb()` now takes an explicit `flip`, and the gate asserts on a **placed** solid, because
   the local test passes either way and that is what let it ship.
2. **The pipes were 457 m in radius.** `_cyl(..., 0.0, 0.0, z0, z1, rr)` passed the pipe's radial
   *position* as its *radius*, building a full station-width cylinder shell whose inside surface
   filled the entire frame. A radius used where an extent was meant.
3. **The frame rings spanned 360°**, so every streaming cell carried a complete ring round the
   whole station. Same family as (2). Replaced by `_arc_band()`.
4. **The catwalk was a 158 m × 120 m plate**, spanning the full arc *and* the full z extent, with
   `CATWALK_W_M` used as a radial offset rather than a width. A catwalk runs **along** the arc —
   the direction a person travels in a ring — and is 1.8 m wide across, in z.

**A gate that failed to catch (3), and why it matters.** A new assertion checks that no piece is
radially larger than its own bay. It missed the 360° ring because it measures **vertex** radii,
and every vertex of a coarse polygon sits at the same radius even though its chords cut far
inside. *Gates that sample vertices cannot see chords.*

**And one assertion that could not object to its own constant.** `CATWALK_CLEAR_M` was 1.8 m —
100 mm of clearance for a 1.7 m person, a crawl space — and the assertion guarding it read
`CATWALK_CLEAR_M >= 1.8`, the value itself. Now 2.4 m against a `>= 2.1` bar.

---

## INV-029 — The customs hall and arrival concourse

**Invented:** every dimension in `station/customs.py` — the 34 × 17 × 7.2 m hall, the screen
gantry, the X-braced brackets, the backlit ceiling grid, the bollards, the light strips and the
customs desks.

**What is sourced.** `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
hub.jpg` (authority 1) establishes the *contents* and their arrangement: three suspended screens
in a row — a talking head, the WELCOME board, and **a green vector wireframe of the whole
station** — carried on rust-brown X-braced brackets, under a backlit coffered ceiling grid, with
heavy cylindrical bollards flanking the approach, ranked vertical light strips along one wall,
and a dense species-mixed crowd. The two blue boards come from `signage.py` and are **reused, not
re-typed**.

**New canon, transcribed here for the first time.** The welcome board's third line has never been
recorded in this project:

> **REMEMBER** — *Smoking permitted in designated areas only*

Verbatim, including the prop's own sentence case under an all-caps header, and asserted as such.
It is a fact about the station rather than a decoration: smoking is *permitted* aboard, in
designated areas, which gives the bars a texture nothing else in the reference set supplies.

**The width is the interesting number, and the first value was wrong.** It was built at the
interior kit's `concourse` width of **9.0 m** and the self-test rejected it: three 3.2 m screens
with gaps span **11.4 m** and do not fit. That is not a screen-sizing problem — **the kit's
"concourse" class describes the Central Corridor** (a two-level corridor with an upper walkway,
INV-020), and an arrival hall is a different kind of space. The reference shows a crowd flowing
*beneath* three side-by-side screens with wall structure well outside them.

So the width is **derived from what the room demonstrably contains**: 3 screens + 2 gaps + 2
bracket bays + a walkable margin at each wall = exactly 16.0 m. That exact sum was adopted first
and put the assertion on a floating-point knife-edge with **zero slack** — a room sized to
precisely its contents is one where adding a single fitting overflows a wall. **17.0 m**, and the
assertion checks the derivation rather than a remembered number, so changing the screens fails
loudly instead of quietly overflowing.

**Height is not free and is not invented:** 7.2 m is two `DECK_PITCH_M` deck pitches, asserted as
a whole number of them, because the hall sits inside a deck stack and cannot exceed the decks it
occupies.

**Placement is uncontested**, which is rare here. Blue Sector's outermost ring, adjacent to the
docking bays — defined by what it adjoins rather than by a name, so **neither C-003 nor C-004 can
move it**. It lands at **0.760 g**, and that is a characterisation rather than a detail: the
player's first experience of the station is being noticeably lighter.

**Overturned by:** any wider shot of the hall, or a frame showing its far wall.

---

## INV-030 — The Garden's townscape

**Invented:** everything in `station/garden.py` except the one measurement below — the civic
landmark's radii and storey heights, the pool, terrace, lawn, flagpoles, waterfall bank, the
red-orange stair, the generic block buildings and the trees.

**Measured, not invented:** the landmark's height. In `garden.png` the two walking figures are
~35 px and the building stands ~330 px from terrace to tower cap; at a 1.7 m stature that is
**16 m, about five storeys**, which agrees with the gazetteer's independent "~6 storeys" read.
Recorded as a measurement with its arithmetic on the page, and everything else is proportioned
against it.

**What the frame establishes** (authority 1, and it is the best interior reference we hold): a
landmark of **stacked cylindrical drums** in warm buff concrete — a tall tower with a
**colonnaded upper storey**, a lower drum beside it colonnaded the same way, **cantilevered slab
terraces** wrapping the base, a **warm-lit glazed ground floor**; a **rectangular reflecting
pool**; paved terraces and mown lawn; a **tall thin waterfall** on a planted bank; **flagpoles
with white banners**; and a **red-orange external stair**, the one saturated accent in an
otherwise buff and green scene. The idiom is streamline-moderne, not the station's industrial
grey, and that contrast is the point: **the Garden is where the station stops looking like a
machine.**

**The constraint that shaped the module.** The drum's inner surface is 4.5 M m² with ~250,000
triangles of headroom — **0.06 tri/m²**. So fields, roads and settlement pattern stay as
heightfield and texture, and only what a person can walk up to gets mesh. The whole townscape
comes in at **2,228 triangles, 0.035 tri/m²**, and both the 0.5 gate and the real 0.06 budget are
asserted.

**Placement is constrained, not chosen.** Buildings may only stand in **settlement bands**, whose
arcs are read from `interior.LAND_USE` rather than restated — 93.6–144° and 259.2–302.4°. Asking
for a building on a field raises, and the self-test checks that it raises. Every footing takes its
ground radius from `drum_ground.terrain_sample()`, so a building follows the heightfield instead
of floating over it; the base-lands-on-terrain error is asserted to under 1 µm.

**A defect found only by rendering against magenta.** The colonnade was a ring of fins with
**nothing behind them**, so the bays were open through the building and the background showed
through the top of the tower — a hole, not a colonnade. The reference shows a dark recessed
interior behind the columns. Fixed with an inner drum, and asserted by group name so it cannot
come back.

**Overturned by:** any other frame of the Garden's architecture, of which we hold three more.

---

## INV-031 — The Alien Sector: galleries, atmosphere locks and the barred screen

**Invented:** every dimension in `station/alien_sector.py` — the gallery, the two-door lock, the
barred screen's bar pitch and stile count, the overhead lattice, the ring fitting, the mask
dispenser, and `QUARTERS_PER_GALLERY = 4`.

**The mechanic is canon, not invented.** The customs board is authority 1 and says *"SIX
DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5"*. Six simultaneous atmospheres is a
life-support architecture: at minimum six independently conditioned volumes **with locks between
them** (`LIFE-SUPPORT-AND-INDUSTRY.md` §2.1). This module is those locks. The atmosphere
*classes* are read from `npc/schedule.py` rather than restated, and that module deliberately
carries **no numbers** for five of the six, because only `DES/ATMOS: HUMAN/02` is numbered on any
prop we hold. An assertion checks that no class here carries a digit — a wrong number printed on a
wall is worse than no number.

**What the frame establishes** (`corridor in alien sector.webp`, authority 1, the only interior
view of the quarter we hold): a heavy chamfered polygonal portal, and beyond it a **horizontal-
barred grille screen across the whole opening**. *You do not walk into a quarter; you look through
bars into it.* That is the single most informative thing in the frame and it is what makes this
containment rather than corridor. Plus amber light falling through an overhead lattice onto the
deck, a dark circular ring fitting, green point lights, and a dark-olive/amber/near-black palette.

**The lock depth is derived, not chosen.** A lock must hold one occupant clear of both leaves at
once, and the occupant this sector exists for is wearing an encounter suit — so
`lock_depth_m()` = suit depth + clearance fore and aft + two door reveals = **2.75 m**. A change
to the body model moves the architecture, which is the direction that dependency should run.
Asserted: **every quarter has two doors, because one door is not a lock.**

### Three defects, each caught by a different gate

1. **The barred screen was invisible** — placed 50 mm behind the inner portal's *near* face, it
   sat inside that portal's own 0.55 m reveal and the jambs occluded it entirely. The render
   showed an empty dark aperture where the frame's headline feature should be. *A screen inside a
   jamb is not a screen.* Found by rendering into the lock.
2. **The containment assertion then failed by 20 mm**, because its limit was built from a padded
   magic `0.25`. That is the assertion doing its job, but a limit made of a magic number cannot
   say *why* it was exceeded. It is now derived from what is actually placed outboard.
3. **The bars opened onto void.** With the screen finally visible, the render showed the magenta
   background *through* it — the quarter interiors are not built in this increment, so there was
   genuinely nothing behind the grille. This project's own rule is that a hole shows the
   background through it, so real void behind a grille is **indistinguishable from a defect** to
   the next session that renders it. A closed `alien_quarter_shell` now backs every screen, and an
   assertion requires one per screen. The room is there; it is simply undressed.

**Also asserted:** the wall placement map has determinant **+1**, checked on a *placed* solid.
`plant.py` passed its local winding test and shipped every surface inside-out because its
placement map was −1.

**Overturned by:** any second interior frame of the Alien Sector, or a source giving the number of
quarters or their sizes.

---

## INV-032 — Residential quarters, by class

**Invented:** every area and dimension in `station/quarters.py` — `UNIT_ASPECT = 1.6`,
`UNIT_H_M = 2.8`, the seven per-class areas, the fittings list and the fitting sizes.

**Sourced:** the *classes* and their *sectors*, from `LOCATIONS.md` §11. Authority is marked per
row in `CLASSES` — "Dock Workers' Quarters" in the Blue rosette is authority 3, most of the rest
is authority 4.

**The design spine is canon and is now a test.** §11 states it in one line: *"Gravity does the
work for free… the people with the least power live where they weigh the most."* This module
asserts that against live geometry instead of restating it:

| rank | class | sector | gravity | unit |
|---|---|---|---|---|
| 0 | command | Blue | 0.760 g | 4.6 × 7.4 m, 34 m² |
| 1 | personnel | Blue | 0.760 g | 3.4 × 5.4 m, 18 m² |
| 2 | diplomatic | Green | 1.000 g | 5.4 × 8.6 m, 46 m² |
| 3 | alien_resident | Green | 1.000 g | 3.7 × 5.9 m, 22 m² |
| 4 | civilian | Red | 0.963 g | 3.2 × 5.1 m, 16 m² |
| 5 | transient | Red | 0.963 g | 2.4 × 3.8 m, 9 m² |
| 6 | **lurker** | Grey | **1.693 g** | **no rooms** |

**2.23× body weight between the top and the bottom of the housing ladder**, and 5.1× floor area
between an ambassador and a transient.

**Being precise about what is true.** Rank and gravity are **not** monotonic across every adjacent
pair — Green's 1.000 g outranks Red's 0.963 g — and my first docstring claimed they were, which is
a docstring lying about its own code, the failure class this project shipped once before as a
comment reading "wound inward" over code winding outward. What is asserted is the claim §11
actually makes: the lowest class lives at the highest gravity, the highest class does not, and
the spread is felt rather than marginal. **Rank orders floor area *within a sector***, which is
what a housing allocation would produce, and that is asserted per sector.

The first area assertion tried to paper over the diplomatic/command inversion with a compound
`or` and failed — the assertion being right and the claim being wrong. **Rank is social order, not
floor area**: ambassadorial suites outrank command quarters on this station.

**`lurker` emits no geometry, deliberately.** §11 is explicit that Downbelow is "corridors and
chambers, **not rooms**", and `plant.py` already builds that architecture — the plant zone is
where `interior.py` tags decks `plant`, meaning *unassigned*, which is exactly what a lurker is.
The class exists in the table, ranks lowest, participates in the gravity assertion and returns
`([], [], [])`. `unit_dims()` returns `(0, 0)` rather than a fake cell, and both are asserted:
handing back a 1 × 1 m room is how Downbelow would quietly become an apartment block.

**Showers are the class marker.** Authority 4 gives them to command quarters and the executive
suites *only*, and `LIFE-SUPPORT-AND-INDUSTRY.md` L-03/L-04 supplies the reason — the water loop
must be >98% closed, so water is rationed. A utility becomes a visible class distinction.
Asserted: exactly `{command, diplomatic}` have one, and a class claiming a shower must actually
build the fitting.

**A stale canon figure, flagged rather than copied.** §11 quotes *"command quarters in Blue at
0.603 g"*. That predates INV-026 — with the fractional `HULL_ALLOWANCE`, Blue's outermost floor
sat at 167.7 m; with the metric skin it is **211.6 m and 0.760 g**. This module reads gravity live
and **asserts the divergence**, so nobody re-copies the old number believing it still holds. §11
needs refreshing.

**Usability is checked, not assumed:** every class must fit a bed across its width, leave a
`WALK_MIN_M` clear path past its fittings, and fit under a deck pitch — an area check alone would
pass a 9 m² cell with a 2.05 m bed jammed across it. Runs of units tile exactly, because a
residual gap between two quarters is a void invisible in any elevation.

**Overturned by:** any on-screen view of quarters with a measurable feature.

---

## INV-033 — The bar/diner

**Invented:** every dimension in `station/hospitality.py`.

**Why it exists.** `npc/schedule.py` makes **hospitality the largest single workplace on the
station** — 734 of 3,000 sampled residents, ahead of the concourse (556) and the Zocalo (488) —
and it had no geometry. Every one of those NPCs was clocking on to nowhere.

**What the frame gives** (`Doug's Dugout.webp`, authority 1; the uploader's caption is **not** a
canon name and this module never uses it, per `LOCATIONS.md` §218): **low pendant cone lamps, one
over each table**, shallow polished shades on slim stems with a bright rim and a hot pool beneath,
and near-zero ambient between them. A cyan neon glyph beside a **vertical tube in four segments
split by three clamp bands** (counted, not chosen, and asserted as counts). An **orange-red
backlit cell matrix ~12 across in a stepped irregular silhouette**. A **regulation 20-segment
dartboard**. An **amber display reading "209"**, carried as data for the same reason
`signage.BOARDS` is.

**The lighting design is the room**, and it is asserted as such: one pendant per table one-to-one,
each with a source inside its shade, hung **below standing eye height** so it pools rather than
lights the room, and **clear of a seated diner's head**. A pendant 200 mm higher stops being this
room.

**The dartboard is a real dartboard.** `DART_SEQUENCE` is the regulation clockwise order and the
self-test checks three things about it: every number 1–20 appears once, the sequence matches, and
**the mean adjacent difference exceeds 5** — the defining property of the real layout is that high
numbers neighbour low ones so a near miss is punished, and a naive 1..20 ring would score ~1.
The board is also asserted at 451 mm across. A plausible-looking ring of numbers is wrong in a way
a player can catch.

**A real-world trademark is excluded by assertion, not by memory.** The frame contains a lit
**ZIMA** panel — genuine 1990s product placement, recorded in the reference index *as observed*
and reproduced nowhere. `_selftest` reads its own source and asserts the string appears at most
once, in the note explaining the exclusion, and that no geometry group carries it. *"I remembered
not to" is not a guarantee, and the next session will not have seen the frame.*

**And it is asserted NOT to be the Zocalo:** under half a concourse's ceiling height and under
120 m² of floor. Building the station's social life out of concourse alone would have made it one
note.

**One defect, found by rendering against magenta.** The deck and soffit spanned only the inner
wall face while the walls sit outboard of it, leaving an open corner at every wall/soffit
junction — visible as a few magenta pixels where the ceiling met the far wall. Both now run to the
outer wall extent. Verified by **counting magenta pixels in the render (0)** rather than by eye,
which is the check that scales: a hole a few pixels across is exactly what an eye skips.

**Overturned by:** any second frame of a station bar.

---

## INV-034 — The procedural room kit: prop dimensions and archetype layout

**Status:** extrapolation, authority 5. `station/rooms.py`.

**What:** every prop dimension in `PROPS` (65 types), the eleven `ARCHETYPES` and the mapping from
a location's declared `functions` onto one, the per-archetype floor `DENSITY` and nominal ceiling
`CEIL_BY_ARCHETYPE`.

**Why it exists at all:** `docs/MASTER-PLAN.md` §3.4 tiers the station at ~12 hero locations, ~30
featured and ~84 procedural. Writing 68 bespoke room modules is the arithmetic the plan says does
not close. So the 68 addressed locations with no bespoke module are generated from the
specification `directory.py` already holds — where they are, how big, what they are FOR, and what
a player can use in them.

**What constrains the numbers.** Not taste. Four properties, each asserted rather than asserted-
in-prose: a prop must be usable by a 1.7 m occupant; it must fit inside its room; no two solids may
occupy the same cubic metre; and a 0.9 m walker must still be able to cross the floor end to end.

**Two sizes were picked instead of derived, and both were wrong.**

*Ceiling height* was a global 2.9 m. A `bay_door` is 5 m tall, so three bay locations could not
contain their own declared props. It is now `ceiling_m()`: the archetype's nominal, raised to hold
the tallest thing the room declares, and deliberately permitted to exceed `DECK_PITCH_M` — a
docking bay spans decks and pretending otherwise is what put a 5 m door in a 2.9 m room.

*Bay span* was a flat 40 m, which rendered a 1,600 m² hall containing six props against one wall.
It is now `bay_span_m()`: as long as the props ranked down its two side walls plus working gaps,
as wide as the deepest prop on each side plus the aisle. A bay READS as furnished by construction,
because it is exactly the room its contents need; the full location is that bay instanced along
its real footprint by `bays_in()`.

**Overturned by:** any frame establishing a real dimension for one of these rooms, which promotes
that room out of the procedural tier and into a bespoke module.

---

## INV-035 — Fixtures: the machinery a room is named for

**Status:** extrapolation, authority 5. `station/rooms.py`, `FIXTURES`.

**What:** per-archetype non-interactable scenery — furnace stacks and plant columns in industrial
space, racking runs in stores, equipment gantries in medlabs, a dais in a sanctuary, stall frames
in a market, service ducts overhead nearly everywhere — plus structural wall ribs at a pitch
derived from the room's height.

**Why, and this is the point:** `interacts` in `directory.py` is *what a player can use*. It is
not an inventory of what is in the room, and building from it alone produced a defect the first
verification render made obvious. **"Fabrication furnaces" came out a grey box containing two
control podiums, a catwalk and a crane — the controls for a furnace, and no furnace.** "Primary
fusion core" declared two interactables and no reactor. A furnace is correctly absent from
`interacts`, because you do not walk up to one and operate it; it is just as correctly required in
the geometry.

**It is a layer 2 defect, not a layer 3 one.** No material and no light makes an absent object
present. That distinction is why this landed here rather than being deferred to the materials pass.

**What constrains the dimensions:** the same four asserted properties as INV-034, plus one more the
fixtures forced into existence — `lateral_stack()`, a single description of what consumes the bay's
width, because the sizing formula and the placement code had each grown their own and disagreed by
260 mm in a fusion core.

**Ribs are excluded from the "is it furnished" metric** on purpose. That metric counts props and
fixtures per square metre; letting a room pass it by growing more wall ribs is exactly how the
measure would go vacuous.

**Overturned by:** any frame of one of these interiors, which fixes what is actually in it.

---

## INV-036 — Habitat windows: the station lit from within

**Status:** extrapolation, authority 5. `station/materials.py`, `FIXTURES`-adjacent but separate:
`WINDOW_*`, `gen_window_sheet`, material `habitat_windows`.

**What:** every aperture dimension (1.10 × 1.35 m at 2.40 m centres, 1.05 m sill), the band layout
(eight decks per repeat, two of them glazed), the 66% lit fraction, and the three colour registers.

**Why it exists:** the standing blocking finding against `exterior_approach` — *"NO EMISSIVE
WINDOWS ANYWHERE. A station housing 250,000 people renders completely unlit from within. It reads
as a derelict, not a city."* It is the first thing the owner's opening beat shows.

**What is sourced and what is not.** No frame in the reference set shows the hull lit from within
at range, so every dimension here is extrapolated. What *is* sourced is **which sections get them**:
`schema/station.yaml` names `green_section` (containing `habitat_cylinder` and `aft_hull_block`) and
`red_section` as the pressurised, inhabited volumes, and `directory.py`'s sector z-extents agree.
The truss spine, the reactor and the deflector spike have nobody in them and stay dark — which is
what makes the lit part read as inhabited rather than as a lightbox.

**Row pitch is not a number here.** It is `interior.DECK_PITCH_M`, imported. CLAUDE.md hard rule 4:
a schema change that moves the decks moves the windows with them. The sheet's repeat is also square
*by derivation* — the column pitch is the row repeat divided by the column count — because `.tres`
writes one scalar `uv1_scale` and a non-square sheet would be silently stretched.

**Two bakes, and the first one was wrong in an instructive way.** Version one glazed *every* deck of
both habitat sections. The engine frame came back reading as rust-coloured static: the drum is 500 m
across, so a 2.4 m pitch puts ~650 apertures round the circumference and they alias into noise long
before they resolve into windows. Worse, the white speckle turned out to be the window *frames* —
modelled as metallic 0.55 standing 0.25 proud, so every aperture threw a sunlit specular highlight.

Both were the wrong building rather than the wrong tuning. A window surround is a shadowed recess,
not a bright ridge; and the reference hull is mostly **plate with window strips in it**. The sheet is
now eight decks tall with two glazed, and the frame is a dark rebate.

**The lit fraction is not 1.0, and that is the whole difference between a city and a lightbox.**
Roughly a third of the population is asleep on a 24 h cycle (`npc/schedule.py`), quarters are empty
while their resident is on shift, and plant volumes have no windows lit at all.

**The mapping is cylindrical, and it had to be.** `export_gltf.py` writes POSITION and NORMAL and
nothing else, so every material in the project relies on Godot's world triplanar. That is right for
plating and greebles — an axis-aligned box of hull looks the same from any of three projections —
and wrong for a pattern with an orientation. Triplanar blended two window grids across the drum's
barrel and drew them as a crosshatch. `godot/materials/hull_window.gdshader` projects about the
station's spin axis instead. Two details in it are load-bearing and neither is obvious:

- **The seam closes by snapping the repeat count.** An arc-length coordinate jumps by a whole
  circumference at ±π. The number of repeats around is rounded to a whole number *at a reference
  radius* — `interior.sector_shell_radius(green)` — so `fract(u)` meets itself. Snapping the
  per-fragment radius instead would close the seam everywhere and put a visible ring wherever the
  whole number steps, which the tapered aft block would show as a stack of bands.
- **Mip selection uses the tangent frame, not the uv.** `dFdx` of a seam-discontinuous uv is the
  width of the whole station and selects the coarsest mip, drawing the seam as a blurred stripe —
  the artefact the mapping exists to remove, reintroduced by how it is sampled. `textureGrad` with
  derivatives projected onto the circumferential and axial tangents fixes it.

**Long-period variation, because 42 identical courses read as ladder rungs.** 28% of blocks — five
repeats square — have no lit windows, which is a section with no quarters behind it. Sized in
repeats rather than metres so a block boundary always lands on a tile boundary and never cuts a
window in half.

**A third value error, found by arithmetic rather than by eye.** The material's albedo was 0.18 and
the sheet's plate value 0.60, so the hull *between* windows rendered at 0.15 against
`hull_exterior`'s 0.60 — **four times darker** — and the habitat sections read as a different
material bolted on. Albedo is now the hull's own and the sheet's plate sits at `TEX_MEAN`, so the
two multiply back to exactly 0.60. Asserted from the values that ship.

**Overturned by:** any frame showing the hull lit from within — which would fix the band spacing,
the lit fraction and the colour mix at once.

---

## INV-037 — Room lighting: which measured fitting each archetype uses

**Authority 5** — the *mapping* is invented. Every colour, temperature, range, spacing and
shadow decision it maps *onto* is measured, and cited.

**What was invented.** `rooms.LIGHTS` gives each of the eleven room archetypes two light
fittings. The archetype→fitting assignment is this entry. Nothing else here is new: the eleven
distinct fittings are the ones three agents measured off the reference frames in session 3n and
recorded in `docs/layer4-lighting/*.json`, with the frame, the region, the balance and the
colour temperature for each.

**Why an invented mapping rather than an invented lamp.** Sixty-eight of the station's 118
locations had no light fitting at all and rendered black — `export_scene.fixture_lights` makes one
real source per tagged `light_*` group and this generator tagged none, so the only things that
glowed in a `rooms.py` room were seventeen terminal screens. The two ways out were to author eleven
new lamp colours by eye, or to decide which *already-measured* fitting each kind of room uses. The
first is unmarked invention wearing a measurement's clothes; the second is one clearly-marked
judgement over a body of sourced values.

**The mapping, and the argument for each:**

| archetype | fitting | why |
|---|---|---|
| industrial | `bay_flood` + `service_wall_tube` | a 7.5 m plant hall is lit like a docking bay: cool high-bay floods, cold blue tube trim |
| store | `bay_flood` + the concourse deck channel | same high bay; the deck run gives a cargo hall its length |
| transit | `concourse_deck_spot` + deck channel | the measured concourse, unchanged |
| hospitality | `bar_pendant_lamp` + `casino_bar_backlight` | Doug's Dugout and the Casino are the two measured hospitality interiors and they agree: warm pendants over the tables, a cyan strip behind the bar, darkness between |
| worship | `cc_dais_key` + `cc_wall_course` | a key on the dais and cold courses on the walls. The dais is the only thing in a chapel that should be lit |
| medical | `fa_batten` + `service_wall_tube` | the only genuinely NEUTRAL source in the measured set (S 0.010, clipping in all three channels) belongs over a medlab bed |
| research | `fa_batten` + `cc_wall_course` | as medical, with the colder trim of an instrumented room |
| detention | `fa_batten`'s register behind a guard + `cc_pit_indicator` | **the one archetype with no reference frame at all** |
| commerce | `zoc_downlight_overhead` + `zoc_stall_light` | the Zocalo, which is what a market on this station is |
| office | `wr_soffit_blade` + `wr_wall_strip_bank` | the War Room is the measured working office and its light is warm, wall-mounted and low. The obvious wrong answer is a cool ceiling grid; the only measured office does not have one |
| generic | `light_downlight` + deck channel | the corridor kit's own fittings, so an unclassified room reads as station fabric |

**What is derived rather than mapped.** Two families of number could not be carried across as
measured and the derivation is on the line in each case:

- **Spacing that scales with mounting height.** A bay flood is measured at 11 m spacing from an
  18 m mount — 0.611 of the height — and a Zocalo downlight at 2.7 m from 7.2 m, 0.375. Carried as
  ratios, because a fixed 11 m spacing in a 7.5 m plant hall is one lamp.
- **Range measured in a volume far larger than the room.** The bay flood's 30 m becomes 12.5 m
  (30 × 7.5/18) and the restaurant batten's 12 m becomes 7.2 m (12 × 3.0/5.0). An unscaled range
  is no falloff at all, which is exactly what made the first lit interior render come back white.

**The exposure is measured, and it had to be, because `energy_rel` could not supply it.** Every
fixture in the JSON carries an energy relative to the brightest fitting *in its own family*, and no
reference frame contains two families, so nothing in the measurement says how a war room's 1.0
compares to a docking bay's. `export_scene.ROOM_EXPOSURE` is that missing number, obtained by
rendering one room per archetype, measuring it and its mapped reference frame with the same code
(`tools/measure_frame.py`), and scaling until the render sits at the same multiple of its reference
that the **corridor already sits at and has been judged good at** — 1.40×. Two passes brought all
eleven from a spread of 0.53–7.75 to 1.32–1.52 against a 1.40 target.

**A negative result worth keeping.** The per-space `ambient.ratio` in the JSON is a *contrast*
figure taken from two hand-picked regions of a grey-world-balanced frame. It is not reproducible as
a whole-frame statistic — `grey level 1.webp`'s entry says 0.300 and the same frame measures 0.086
by percentile — and treating it as a level target drives the corridor to an ambient of 5.6 and a
frame two and a half stops hotter than the show. It is used here only for what it is: the
*relative* fill-to-key of one space against another.

**What would overturn it:** a Season 2–3 frame of any of these interiors. A brig frame would settle
`light_cage_lamp`, which is the weakest row in the table and is declared as such; a medlab frame
would settle whether a medlab really takes the restaurant's neutral batten.

### INV-037 addendum — the bespoke modules

The table above maps the eleven `rooms.py` archetypes. The sixteen bespoke modules were done
separately and three of them needed a judgement rather than a lookup.

**`plant` → the service corridor, plus the docking bay's flood.** Nothing in the show establishes
a plant-room fitting. What is measured is the service corridor's *character*, and it is emphatic:
balanced median luminance 0.060 against a residential corridor's 0.265, "its walls are black except
where a panel or the deck strip reaches them". A plant bay is lit exactly that much and no more —
and Downbelow squats in these frames, which is the same argument twice. The flood is `bay_flood`,
and it is the **one range in this project that transferred with no arithmetic at all**: measured at
30 m in an 18 m bay, and a five-deck plant bay is 5 × `DECK_PITCH_M` = 18.0 m exactly.

**`quarters` → the residential corridor's own kit.** A unit opens off a corridor and is built from
that corridor's kit, so it takes the corridor's fittings and the corridor's split between them:
`light_downlight` casts, `light_portal_head` does not. The mount height transfers **as a ratio, not
a length** — the measurement is "0.35 ± 0.02 of clear deck-to-soffit height on two independent
columns", which is 0.88 m in a corridor and 0.98 m under a 2.8 m quarters ceiling. Carrying the
0.88 m across would have put it at 0.31 of this ceiling and quietly lost the thing measured.

**No per-class lighting, and that is a decision rather than an omission.** Nothing in the reference
distinguishes an ambassador's suite from a transient cell by its fittings. What *does* differ is how
many fittings a unit gets, because the spacing is measured and the unit areas are not — the class
marker doing its own work.

**`council_chamber` → a fitting invented to carry a measured source.** `cc_house_wash` is measured
as the chamber's entire lighting scheme and the measurement says in the same line that its **fitting
is never in frame**. Every light in this rig derives from tagged geometry, so both easy answers are
wrong: a lamp where the frames show none is invention, and no source at all leaves the chamber on
ambient when its measured ratio of 0.210 makes it one of the two brightest spaces on the station.
`house_cove()` is the smallest object that can carry a light and still be concealed — high on the
rear wall, above the fin fan, facing away from the room. **The colour and behaviour are measured;
the geometry is invented.** Overturned by any frame showing this chamber's ceiling.

**One mapping was withdrawn, and the withdrawal is on the record.** The customs hall's ceiling
coffer looked like the obvious next entry — its colour was measured on the fitting itself, and the
same frame ranks its three source families by balanced peak (screens 0.99, wall strips 0.82, grid
0.55 → an `energy_rel` of 0.56). Given a light, `customs.hall()` emits 210 separate coffers, the
render came back at **18.9× its reference frame with 14% of it clipped**, and the exposure needed to
rescue it was 0.07. The answer was already written in that material's own source note: the grid is
*"ambient decoration rather than a task light"*, ranked last of the three. It stays emissive-only,
and customs is therefore recorded as **not at layer 4** rather than counted with a rescued number.


---

## INV-038 — The exterior's night side: the terminator, planetshine and the night exposure

**Status:** extrapolation, authority 5. `godot/scenes/exterior.tscn` (`EnvNight`, `night_lights_off`),
`tools/export_scene.NIGHT_SUN_PHASE_DEG` and `EXTERIOR_CALIBRATION["night"]`.

**What:** the sun's phase angle on a night shot (46°), the planetshine ambient (energy 0.12, colour
(0.30, 0.27, 0.24)), the night exposure (`tonemap_exposure` 3.6) and the decision that the fill and
the rim are dark.

**Why it exists:** the standing blocking finding recorded in session 3k — *"The lighting rig has no
night side... the owner's opening beat is the station coming into view, so that shot cannot be
composed until the rig changes."* INV-036 built the windows; this is the lighting condition that
lets them read.

**What is sourced and what is not.** Nothing here is sourced. No frame in the reference set shows
this station at range on the anti-sun side — INV-036 says the same of the windows themselves. The
one authority-1 broadcast frame of station exterior *out of* sunlight is
`reference/01-station-exterior/Cobra Bays with starfurries.webp`, a close shot of one bay face, and
it is used for exactly one thing: its 0.08% clipped fraction is the anchor for the rule that a night
frame must not blow.

**The phase is derived, and it is the only number here that is.** The sunlit crescent covers
(1 − cos φ)/2 of a convex body's visible face. At the arrival framing the habitat drum is ~90 px
across a 960-wide frame, so φ = 22° gives a 3.3 px crescent that aliases along the barrel, φ = 39°
gives 10 px and is the floor, φ = 46° gives 14 px. **46 is declared; the floor at 39 is derived.**

**Planetshine is a measured trade, not a level.** The station holds station over Epsilon III, which
fills a large solid angle beneath it, so the unlit hull is lit by a planet rather than by nothing.
How much is decided by measuring what it costs, at the arrival framing:

| ambient energy | footprint visible against the starfield | habitat / unlit structure |
|---|---|---|
| 0.00 | 37.9% | unbounded |
| **0.12** | **66.8%** | **30.4** |
| 0.55 | 94.6% | 14.4 — daylight's own ratio |

At 0 the truss and reactor are indistinguishable from space and the station reads as two blocks
rather than an 8 km object. At 0.55 the pressurised sections are no more distinct from the unlit
ones than they are in full sun, which is the whole finding thrown away. 0.12 also happens to put the
unlit habitat hull at 0.0112, just over `tools/measure_frame.py`'s 0.010 floor — the dimmest value
that is still a value.

**The exposure is declared, and it had to be an exposure.** Most of a night frame is EMISSION, and
no light energy scales emission: a `--light-gain 0.0` render at the arrival distance leaves the drum
99.4% below the measurable floor with a p50 of 0.0017. Raising `emission_energy` instead would change
INV-036's *physical* claim about the windows in order to fix a *photographic* one. 3.6 is 8.4× the
day exposure — three and a bit stops, conservative for the difference between a sunlit surface and a
lit window. Four measured constraints bound it and all four are gated: the sheet's mean emission,
the habitat-to-structure ratio, the silhouette against the starfield, and clipping.

**The fill and the rim are dark, and the sun is the rim.** At the arrival framing the three lights
sit at 136°, 49° and 116° off the camera axis: the sun is the backlight and the rim is a
three-quarter frontal key on the hemisphere the condition exists to show dark. Measured with both
left burning, the habitat's median is 5.2× brighter and the visible footprint goes from 67% to 88% —
a dim day side.

**Overturned by:** any Season 2–3 frame of the station at range on the anti-sun side. It would fix
the planetshine level, the exposure and the crescent width at once.

---

## INV-039 — The exterior day exposure, and the statistic it is measured on

**Status:** extrapolation, authority 5 (the *procedure* is the project's; the choice of statistic and
the target are the judgement). `godot/scenes/exterior.tscn` `Env.tonemap_exposure = 0.43`,
derivation in `tools/export_scene.EXTERIOR_CALIBRATION["day"]`.

**What:** the exterior was the last lit volume in the project with no measured exposure. It is now
0.43, verified at ×1.403 of its reference.

**The reference, and what had to be established before it could be used.**
`reference/01-station-exterior/` holds five files and **three are misfiled interiors** — `view.jpg`
is byte-identical to `03-sector-blue/Babylon_5_2-22_34b.jpg`, `welcome to babylon 5.webp` is customs
signage, `sleeping-in-light-05.jpg` is Downbelow; `reference/00-INDEX.md` says so for all three.
That leaves `exterior more.jpg` as the only sunlit whole-station reference, and **measuring it
whole-frame measures a desktop wallpaper's backdrop**: the marbled plate reads median 0.1259 and so
does the whole frame, to four decimals. The comparison is against recorded crops of the habitat drum
in the sheet's two orthographic projections, and against a matched near-orthographic render of ours
(30 km, fov 16, lod0) rather than against the arrival orbit, so lit fractions are comparable.

**It is measured on p95, not the median.** The reference hull is mostly dark blue-purple courses,
mean linear rgb (0.086, 0.086, 0.111), median at 29% of its brightest plate; ours is warm off-white
throughout, (0.395, 0.350, 0.312), median at 76%. That is a *shape* difference and no exposure fixes
it — matching the median would put our sunlit plating at half the show's and would have to be undone
the moment the hull material gains its banding. p95 is the brightest sunlit plating and is the same
white plate in both frames. **The residual median gap of 3.30× is a layer-3 finding against the hull
material and is recorded as one, not tuned away.**

**AgX is not linear here and assuming it was would have cost two thirds of a stop.** Three points
from the calibration shot: exposure 1.00 → p95 0.5117, 0.70 → 0.4251, 0.40 → 0.2943, i.e.
out ≈ exposure^0.62.

**The weakest thing about it, stated plainly.** `exterior more.jpg` is a render of the production
model on a fan-assembled wallpaper sheet, not a broadcast frame, so the ×1.40 offset — whose stated
derivation is "a film frame carries a grade, a stock and chroma subsampling and our render carries
none of them" — is on weaker ground here than anywhere else in the project. ×1.40 is kept anyway:
every other space targets it, the two projections of this one sheet already disagree by 14%, and
changing the project's single calibration constant for one space on an argument that cannot be
measured is picking the convenient reading.

**Overturned by:** one Season 2–3 broadcast frame of the station in sunlight at range. It would
settle both the level and the ×1.40.

---

## INV-040 — The cobra bay: a framed well, and the proportions of one

**Invented:** every proportion in `station/components.py`'s `COBRA_*` block and in
`cobra_bay_ring` / `_cobra_bay` — the bay's axial length, the sill and lintel heights, the
column step, the plinth and capital oversails, the two deck ledges, the stowed launch arm, the
hull-datum construction, and 14 bays per ring.

**Why necessary:** all 28 cobra bays were one box each, 21 m across the hull by 42 m along it,
standing 26 m proud. A blister. `01-station-exterior/Cobra Bays with starfurries.webp` is
authority 1 and shows the opposite — a deep structural well you look *into*. A blister and a
well have the same silhouette from 9 km and nothing in common from 400 m, and 400 m is where
the owner's opening beat ends up. Task #10 has been open since session 1 for this fitting.

**What is sourced, and is not invention:**

| quantity | value | authority | source |
|---|---|---|---|
| bay count | 28 | 3 | Contract 5 "COBRA BAYS (28)"; C-002 provisional, 28 bays / 24 fighters |
| bay unit width | **42 m** | 3 | `station.yaml` `cobra_bay.width_m`; the same figure `docking_bay.py` reads rather than retypes |
| protrusion | **26 m** | 3 | `station.yaml` `cobra_bay.protrusion_m` |
| z band | 6980–7250 | 3 | `station.yaml`; excess zone 7062–7302, peak 102 m |
| the bay is a framed WELL, not a blister | form | 1 | `Cobra Bays with starfurries.webp` |
| heavy chamfered box columns; red beacons at their heads; amber/white marker lights in vertical files down their inner faces; yellow/black chevrons on **every** deck nosing; at least three stepped deck levels; a triangulated lattice launch arm with a pentagonal cradle ring, hinged at a heavy root block, which **swings** | form | 1 | same frame; 00-INDEX session-2r extraction |

**The one measurement, and why a ratio is all that frame can give.** That frame has no scale
anchor: no figure, no caption, and INV-008 already records that `01-station-exterior/` contains
no authority-1 exterior hull frame at all. A *ratio* survives having no scale. Measured at
native 843×474: the two framing columns read **57 px** wide with **136 px** of clear opening
between them, so a column is 57/250 = **0.228** of the bay unit and the clear mouth is
**0.544**. Taken as `COBRA_COLUMN_FRAC = 0.23`, with the clear falling out as 1 − 2(0.23) =
0.54 — the measured 0.544 to within one pixel at that magnification. Against the schema's 42 m
unit: columns **9.66 m**, clear mouth **22.7 m**.

**What is extrapolated, worst first:**

1. **The axial length, 42 m, is the weakest number here and nothing supports it.** No source
   gives a cobra bay's extent along the station's axis. 42 m is inherited from the box this
   replaces, where it was `2 × (width / 2)` — an artefact of that builder's arithmetic, not a
   measurement of anything. It sets the mouth's aspect (22.7 wide × 32.3 long) and, through the
   hull datum below, how much the bay tilts.
2. **The hull datum.** The hull flares from 166 m to 191 m *inside one bay's length* at the aft
   ring. Sizing a bay off the radius at its centre buries its fore end; sizing it off the
   maximum stands its aft end 51 m proud of a hull the schema says it clears by 26. Both are
   wrong for the same reason, so the bay is built on the straight line between the hull radii
   at its own two ends and `protrusion_m` is measured from that. The bay therefore *tilts with
   the hull*, which is what a rigid structure bolted to a flare does. Consequence worth stating
   plainly: where the hull dishes below that line — up to 13.5 m at the aft ring — the bay is
   proud of the hull by more than 26 m, and no rigid bay can avoid that.
3. **Ledges at 0.30 and 0.58 of the well height**, projecting 0.22 of the clear width from
   alternate sides. Sourced: *that* there are at least three stepped levels. Invented: which
   three. The well floor is the third.
4. **`COBRA_BEAM_RISE = 0.58`, `COBRA_SHAFT_RISE = 0.55`, `COBRA_SHAFT_FRAC = 0.82`,
   `COBRA_PLINTH_FRAC` and `COBRA_CAPITAL_FRAC = 1.14`, `COBRA_BEAM_FRAC = 0.50`.** These exist
   because the first build ran columns and beams to the same radius, and face-on that is one
   flat 42 × 42 m plate with a hole in it — no relief anywhere, which is exactly what a box
   primitive looks like. The reference's column heads are the highest thing in frame and the
   beacons sit on them, so the beams became low ties and the columns step in and oversail.
5. **14 bays per ring, two rings.** Inherited from the builder this replaces, where it was an
   undocumented anti-crowding cap. It is now `spec.get("per_ring", 14)` and guarded: 28 in one
   ring needs 1,176 m of arc against 1,049 m available at the aft ring's radius, so two rings is
   not merely tidier, it is the only arrangement that fits at that radius. Weak corroboration:
   the fore barrel in `exterior more.jpg`'s side view carries two separate light-grey bands of
   rectangular cells rather than one.
6. **The launch arm as three boxes.** A lattice truss and a solid boom differ by a few pixels of
   transparency at this range and by ~300 triangles a bay. Stowed rather than extended, because
   an extended arm is a runtime pose and this is hull geometry.

**Overturned by:** any frame showing a cobra bay mouth against something of known size — the
same want INV-022 already lists. Specifically, a Starfury unforeshortened in a bay mouth would
close the absolute scale: a rough read of the cradle ring in the reference against the 6.8 m
across-flats span in `starfury_geometry.py` suggests the bay in *that* frame is nearer 28 m than
42 m, which would make the schema's 42 m the *pitch* rather than the mouth. That read is far too
weak to act on — the ring is oblique and its diameter is guessed — but it is the direction the
evidence leans and it is recorded so it is not rediscovered as a surprise.

**Two defects the new gates caught, both invisible to any render.** The bays were sized off one
radius per ring (above), and the capitals were scaled off `depth`, which now carries however far
the frame reaches down to find the hull — 31 m at the aft ring — putting 34.5 m of column above
a hull the schema says the bay clears by 26. `components._selftest` measures both against a
datum it recomputes from the profile itself, and each was verified by reintroducing the bug and
watching the gate go red at 1.33× and 2.06×.

---

---

## INV-041 — Dome glazing: mullions, ring band and collar, and why the domes still do not glow

**Invented:** the fitting proportions in `station/components.py`'s `_dome_fittings` —
`DOME_BAND_PHI = 0.42`, `DOME_RIB_SEGMENTS = 2`, mullion section 0.055 × 0.045 of the dome
radius, band and collar widths of 0.16 of the dome height, the 0.05 × max(radius, height)
standoff — and every number in the `dome_glazing` material.

**Why necessary:** `domes` served three components and eight instances — `observation_dome`
(Dome 1 is Command and Control), `observation_rotunda` (4) and `docking_port` (2) — and built
all eight as a bare half-ellipsoid with one material. Grey eggs. They are also among the
largest fittings on the hull: the docking ports are 88 m across.

**What is sourced, and is not invention:** `03-sector-blue/comand and contorl.webp` is authority
1, is Observation Dome 1 seen from inside, and shows the glazing as "a large circle carried on
**radial spoke mullions** with a **broad concentric ring band**, set in a flat-panelled
bulkhead" (00-INDEX). That is the whole organising idea of the refit, and 00-INDEX's own entry
says it "should match the exterior `domes` component". Counts, radii, heights and positions are
unchanged from the schema (Contract 5, authority 3).

**The mullion count is measured.** The upper arc of that frame at 5× gives **8 to 9 panes**
across the visible half, closing to **16–18** for a full ring. `DOME_MULLIONS = 16` is taken
because it is inside the counted range *and* divides the shell's segment count, so every rib
lands on a shell seam. A rib crossing a seam has to be pushed further out to stay proud of the
shell, and the further out it goes the more it reads as a cage over the dome rather than as its
glazing bars.

**The mullions stop at the ring band, and that is sourced too.** They ran to the pole in the
first build and the render said no: sixteen 4.8 m bars converging on a point is 77 m of
structure crowding into nothing, and it read as a starburst. The reference does not do it
either — the phrasing is "a **large circle** carried on radial spoke mullions", and inside the
band the frame shows one unbroken pane. Fixing the accuracy fixed the artefact.

**What is extrapolated:** every fitting *dimension*. `DOME_BAND_PHI = 0.42` is the band's
latitude read off the frame's proportions rather than measured; the section sizes are chosen so
a 4.8 m bar on an 88 m dome reads as structure at 400 m without becoming a rib cage; the
standoff of 0.05 × max(radius, height) is derived, not chosen — it is what keeps a straight
chord between two rib nodes clear of the curved shell between them, given a sagitta of 0.034 r
over a 30° chord.

**`dome_glazing` is entirely extrapolated, and it is deliberately the SMALL guess.** INV-008
left these on `hull_exterior` and said why: "they are glazed volumes over lit interiors and
almost certainly should not be opaque hull, but no reference in the set shows them lit from
outside, and a glowing dome is a large, prominent guess." **That caution is kept and no dome
emits light.** What has changed is that the C&C frame establishes the aperture is *glazed*, so
leaving it as hull plating is a claim that is certainly wrong. The material is therefore a dark
dielectric — albedo (0.045, 0.048, 0.055), roughness 0.10, specular 0.85, no emission — which is
what unlit glass does in a Forward+ renderer. It makes the domes read as glass in silhouette and
adds nothing to the frame's light.

`observation_rotunda`'s shell is **not** bound to it and stays on `habitat_windows`, because
00-INDEX's re-examination of `05-sector-green/rotunda.webp` reads the rotunda's window ring as
looking **inward** onto the drum. Two different fittings; one of them is unresolved and this
entry does not resolve it.

**Overturned by:** any exterior frame showing a dome. If the domes are lit from within,
`dome_glazing` becomes an emissive and this entry stands as the record of why it was not one
first. A second frame of the C&C window would also settle the mullion count between 16 and 18.

**A closure defect worth recording, because no render could ever have found it.** `dome_mesh`
was never closed: **56 boundary edges** each on `observation_dome` and `docking_port` and **112**
on `observation_rotunda`, from an open base ring and a top ring of `segs` coincident vertices
forming `segs` degenerate quads at the pole. The base sits inside the hull and the hole faces
away from every camera, so the geometry has been open since the domes were first built. Found by
an edge census, not by looking. Repaired at zero triangle cost — the pole becomes one vertex with
a fan under it, which frees exactly the `segs` triangles the base disc needs — and greeble.py's
blisters, which call the same function, are repaired with it.

---

## INV-050 — The guideway structure gauge, the spoke portal, and the clearances they buy

**Invented:** The volume kept clear of structure along a drum guideway, the aperture cut through
each radial spoke to hold it open, and the clearance the tram car keeps inside it. In
`station/interior.py`: `GUIDEWAY_GAUGE_DEPTH_M = 12.5` radially outward from the bottom chord's
centreline, `GUIDEWAY_GAUGE_HALF_W_M = 7.4` laterally, `GUIDEWAY_SOFFIT_RELIEF_M = 0.15`,
`SPOKE_PORTAL_FRAME_M = 1.6`, `SPOKE_PORTAL_PROUD_M = 1.2`, `SPOKE_PORTAL_COLLAR_M = 4.0`. In
`station/tram.py`: `TRUSS_CLEARANCE_M = SPOKE_CLEARANCE_M = 0.30`.

These were built in session 2y to close the blocking defect where tram cars passed **6.43 m**
through solid spoke structure, and they were never logged. This entry is the record; the numbers
are unchanged by it.

**Why necessary:** The guideway trusses are in the spoke planes because nothing else can carry
them — 2,586 m of truss does not span unsupported and the spokes are the only radial structure
there is (INV-012). A car therefore *has* to cross a spoke, and no placement can avoid it:
`tram.guideway_cars` takes a `phase` that walks the whole train along the run, so whatever static
offset is chosen, every car reaches its own spoke eventually. Either the structure opens or the
simulation contains a vehicle that drives through a girder.

**Constrained by:**

- **The gauge is sized off the INFRASTRUCTURE, not off the vehicle.** The widest thing on a
  guideway is the light run at lateral 6.7 m, nearly twice the car's half width; 7.4 m clears it
  by 0.7 m. The depth is the car's 11.5 m below the chord centreline (INV-017's 0.65 of the truss
  depth, read off `33a`/`34b`) plus a metre. Sizing it off the car would mean re-cutting the spoke
  every time the vehicle changed.
- **The soffit relief is a rendering constraint with a structural reading.** At 0.15 m inboard of
  the chord's running face, the chord and its light runs stand proud of the opening, so a car
  meets the same surfaces inside the portal that it meets everywhere else. Flush would be
  structurally identical and would leave two coplanar faces across the whole opening, which
  z-fights.
- **The portal's net section is solved, not chosen.** Cutting a 14.8 m slot out of a 21.2 m member
  removes 70% of it. `interior.spoke()` sizes the two piers so that pier area plus frame-jamb area
  is at least the gross area removed, which widens the spoke from 21.2 m to 35.7 m where it is
  pierced. A wider gauge therefore buys its width by pushing the spoke wider rather than by
  thinning the piers, and the self-test asserts the net section.
- **The 0.30 m clearance is the suspension gap, and that is the argument.** INV-017 sets a
  non-contact magnetic gap of 0.35 m between the shoe plates and the chords. Requiring the fixed
  structure to clear the car by less than that would mean the spoke, not the running gear, decides
  how close the car may be built. 0.30 m is just inside it, so the running gear stays the binding
  constraint and `tram.py` asserts `spoke_clearance >= truss_clearance`.

**Measured, this session, surface to surface:** the built car clears the built spoke by
**0.500 m** and the built truss by **0.350 m**, the second being exactly the suspension gap. Both
were recomputed from the meshes by an independent script before anything was changed, and both
agree with `tram.py`'s own metrics. The 6.43 m interpenetration is closed and stays closed.

**How it is measured matters as much as the number.** The clearance metrics were vertex loops:
they walked the car's vertices and measured each against the obstacle rectangles. That reports a
comfortable gap for an obstacle lying *wholly inside* the car, because such an obstacle contains
no vertex. Demonstrated: a 1.4 m member placed in the car's underfloor void — where a bearing
beam would go, and `interior.spoke()`'s own docstring discusses letting the truss chord into the
header — returns **0.500 m of clearance** from the vertex loop, the identical number it returns
with no member there at all, while the surface metric returns **−0.831 m**. Both metrics are now
surface tests: the car is projected triangle by triangle into the sweep plane and each projected
triangle is measured against each obstacle rectangle by separating axis and edge-pair distance.
The projection of a closed solid is the union of the projections of its boundary triangles, so
this is the real surface rather than a point cloud sampled from it.

**Overturned by:** any frame showing a guideway crossing a spoke. The whole arrangement — a
framed portal with piers, header and sill — is a structural argument from a rule of thumb, not an
analysis, and nothing in the reference set shows the drum's radial structure at all. A frame
showing the truss simply passing *outboard* of the spokes, or the spokes stopping short of the
guideway radius, would remove the need for a portal entirely.

---

## INV-051 — Windscreen mullion and reveal standoff

**Invented:** The rule that the tram saloon's windscreen mullions and sill/head reveals are set
**entirely behind** the screen surface, with a 10 mm relief, in `station/tram.py:car_saloon()`.

**Why necessary:** `35a` shows the screen divided by grey posts with a red reveal either side of
each pane, and those members read as standing proud *on the inside* — the camera is inside the
car and sees their inboard faces. The mullions were built by `_strut`, which centres its section
on the line through its two endpoints; those endpoints lie *in* the screen, so half of every
member was in front of it. Measured: **74 mm of mullion and 100 mm of reveal protruding through
the nose of the car**, at the one place a car is seen close up from outside (`33a`). Found by
replacing a vacuous triangle-count assertion with a containment one, not by looking at a render —
90 mm on a 96 m car is well under a pixel at any distance the car has been rendered from.

**Constrained by:**

- **The offset direction is derived, not chosen.** It is the screen's own outward normal, taken
  from the two rails of the aperture, so a change to `RAKE_M` carries the members with it instead
  of leaving them stale.
- **The offset distance is measured per member, not predicted.** `_strut` orients its depth axis
  from its endpoints, so a vertical mullion and a lateral sill rail present different amounts of
  themselves to the screen. Each member is built, its own worst projection past the screen plane
  is measured, and it is slid back by that plus the relief.
- **Two constraints, because the screen is not the whole nose.** The raked plane exists only
  between the sill and the cant; below the sill the front cap is flat at the nose plane, and the
  sill reveal is offset 0.11 m below the sill, which is exactly where the extrapolated screen
  plane runs forward of the car. Without the second clamp the reveal still stood 20 mm proud.
- **10 mm of relief rather than flush.** Flush is coplanar with the glass and z-fights across the
  whole screen — the same reason `GUIDEWAY_SOFFIT_RELIEF_M` exists.

**What this does not change:** the members' sections (0.10 × 0.16 for a mullion, 0.13 × 0.20 for a
reveal), their count, or the aperture. The self-test's ray casts confirm the unglazed screen is
still an aperture the camera sees through and the glazed one still closed.

**Overturned by:** a frame showing the screen's *outside*. If the mullions are external members —
which is how a heavy vehicle's screen is often framed — they belong in front of the glass and this
entry is exactly backwards. `35a` is an interior shot and shows only the inboard faces; `33a`
shows the car from below and ahead but not close enough on the screen to settle it.

---

## INV-044 — The Garden's calibrated framing, and why `29a` is not the frame to measure it against

**Invented:** the camera of the `garden` entry in `tools/export_scene.py`'s `DRUM_CALIBRATION` —
eye at world `(-90.144, 246.253, 4956.0)`, aim at `(-95.185, 243.275, 4900.0)`, vertical fov 45,
960×540. In `garden.townscape()`'s own local frame (origin at 112°, z 4900, ground radius
272.234 m) that is an eye at `(x -9, y +10, z +56)` looking at `(x -3, y +11, z 0)` — 56 m out
along the station axis from the civic landmark, 8.0 m above the ground it stands over, looking
back at it.

**Why necessary:** layer 4 counts a location once it has been seen in a frame *measured against
its reference*. Four locations (`garden_town`, `garden_terrace`, `zen_garden`, `water_rec`) hang
off `station/garden.py`, and its geometry had never appeared in a rendered frame — the wide drum
shot builds the townscape and shows exactly 0.00% of it, 92° around the barrel. A camera is not
in canon. One had to be chosen, and the choice decides the measurement, so it is logged.

**What is sourced, and is not invention:** `reference/09-garden-core-and-transit/garden.png`,
authority 1, is the frame `garden.townscape()` was built from — `station/garden.py`'s own
docstring names it as its source and `reference/00-INDEX.md`'s re-examination adds "Do not
colour-match [`The Gardens.webp`] — match `garden.png`, which is clean". The *composition* is
that frame's and not a preference: civic landmark at mid distance, settlement around it, the
drum's far side arching overhead, the guideway crossing the upper frame.

**How the distance and the fov were derived.** `00-INDEX.md`'s re-measure of `garden.png` gives
two independent scales in one frame: the two walking figures at ≈40 px/m at their depth, and the
ground-floor window band at ≈11 px/m at the building. A 1.75 m stature over 70 px of a 507 px
frame implies a vertical fov of **45.8°**, which is why the framing uses 45 rather than the
project's 46 default; and at 11 px/m the building stands **≈56 m** from the camera. Both numbers
are read off the reference, not chosen. The 8.0 m eye height is not: `garden.png` looks *down* on
the reflecting pool's water surface, which a 1.7 m stance on this build does not, and at 1.7 m
the terrace slab fills the lower half of the frame. It is set to the lowest height that puts the
pool and the terrace in the lower third.

**What is NOT matched, stated because a reader can see it in the frame.** Our civic landmark is
**16.45 m** to the cap and `garden.png`'s is **25–30 m**, so the tower subtends 38% of frame
height where the reference's fills 65%. This entry does not fix that — it is layer-2 debt — but it
records the cause, because the number has a bad derivation behind it. `garden.py` sets
`TOWER_H_M = 16.0` from "the two figures are ~35 px tall; the landmark stands ~330 px … at a 1.7 m
stature that is ~16 m". Measured here, the green figure in that frame is **80–103 px** tall
(80 read off a 6× crop, 103 by a luminance threshold that also catches the cast shadow at the
feet) — between 2.3× and 2.9× the 35 px the derivation assumed. And `00-INDEX.md` rejects the
method outright regardless of the pixel count: *"That figure cannot be carried to the building,
which is much further away."* Two independent reasons the 16 m is wrong, and the index's own
window-band ladder gives 25–30 m.

**Why the reference is `garden.png` and not `Babylon_5_2-22_29a.jpg`.** `29a` is authority 1, is
the Garden (`00-INDEX.md` says so, and says the file is misfiled), and is what
`docs/engine-drum-terrace.png` was matched to when the garden was read as 2.5 stops hot at x3.49.
It is the wrong comparison and the numbers say why:

* One volume, one rig, one exposure. The committed wide frame `docs/engine-drum.png`, verified at
  **x1.39** of `34b`, reads **x1.50** of `garden.png`, **x1.81** of `33a` and **x3.77** of `29a`
  from the same pixels. Picking the reference picks the answer.
* `29a` is not a darker garden, it is a different picture. Its own lit paving measures median
  **0.1515** — `34b`'s whole-frame median to four decimal places. What drags its whole-frame
  median to 0.0559 is that **60.1%** of the frame is below linear Y 0.05: clipped hedge at 0.0296
  (78% crushed), timber-slat retaining wall at 0.0263, broadleaf canopy at 0.0569.
  `station/garden.py` builds no hedge, no canopy and no retaining wall, so our frame at that
  camera is 0.28% crushed. This corroborates a finding `station/materials.py` already carries for
  the same file: *"the frame is dominated by dark foliage, so grey-world reads the subject as a
  cast."*
* Shadow coverage cannot close it, and that was tested rather than assumed. At the same camera,
  taking `--shadow-lights` from 2 to all 60 moves the median 0.1952 → 0.1408, which is 28% of the
  way to the 0.0783 that x1.40 of `29a` requires, at 2.45× the render time. With every light at
  zero energy the frame still measures 0.0823 — **above** that target — because what remains is
  the drum's ambient term and the emissive window bands, and a shadow touches neither. Full
  numbers and costs in `docs/layer4-lighting/drum_open_volume.json`.

**Overturned by:** a Season 2–3 frame of the Garden with a recoverable camera, which would replace
this framing rather than corroborate it; or a corrected `TOWER_H_M`, which changes the 56 m,
because the distance was derived to make a landmark of the reference's size read the way the
reference's does. `29a` becomes a usable reference the moment `garden.py` builds the terrace it
shows — cut-and-cover portal, timber-slat retaining walls, hedge banks and canopy — at which point
the content mix matches and the comparison means something.

**Corroboration worth keeping.** Two different cameras on the same module measured against the
same reference: this framing at **x1.49** and `docs/engine-drum-terrace.png`, a 20 m close view of
a block facade, at **x1.39**. 7% apart, both inside the ±25% band. The exposure claim is therefore
not an artefact of one lucky camera, which is the failure mode a single calibrated frame per space
cannot rule out.

---

## INV-045 — The drum tram's calibrated framing: the camera `33a` puts you at, measured against `34b`

**Invented:** the camera of the `tram` entry in `tools/export_scene.py`'s `DRUM_CALIBRATION` —
`--stand 96,4875` (on the drum floor at 96°, z 4875, eye 1.7 m) aimed at
`(-121.5, 210.444, 4916.5)`, vertical fov 45, 960×540. The aim point is the centre of the car on
the 120° guideway at z 4916.5, one of the six `tram.drum_trams` places. The car is 120 m away and
broadside.

**Why necessary:** `drum_tram` is an authority-1 location and `tram.py` is 1,100 lines of measured
vehicle, and the only frame the project had ever measured it in was the wide drum shot, where
`trams` moves **0.01% of the frame — thirteen pixels** at 480×270, at the far end of a 2.6 km
drum. A frame's exposure says nothing about a fitting that small, so the place was correctly
excluded from layer 4 in session 3q and stayed excluded because nobody had pointed a camera at the
car. A camera is not in canon; it had to be chosen and it decides the measurement, so it is logged.

**What is sourced:** `reference/03-sector-blue/Babylon_5_2-22_33a.jpg`, authority 1, is the frame
that shows one car close, and `station/tram.py`'s docstring already names it: *"one car from below
and ahead: white body, maroon window-band framing, dark underside with round ports, two white
lights low on the nose."* The framing reproduces that frame's **relationship**, which
`reference/00-INDEX.md` pins independently: *"The axial truss carries, on its underside, a row of
large bright rectangular light boxes."* You can only see the underside from below it, so 33a's
camera is **outboard of the guideway**, between the truss and the floor, with the far surface of
the drum beyond the car. That is the framing built here.

**Why the camera is on the floor and not near the axis, which is where it was tried first.** The
car hangs 6.5–11.5 m outboard of the truss's bottom chord at the *same* angular position
(`CAR_DEPTH_FRAC = 0.65` of a 16 m truss depth, guideway at r = 236.555 m, car at r = 238.0–248.1
m). So from any camera inboard of the truss, the ray to the car crosses r = 236.555 within about a
degree of the truss's own bearing, and the truss is ±1.2° wide. Computed for the first attempt —
eye at r 150, θ 106°, 135 m from the car — the crossing lands at **119.42°**, 0.58° off the truss
at 120°, and the render came back with the truss across the frame and no car visible at all. This
is a property of the geometry, not of that particular camera: an inboard vantage cannot see this
car except through the Warren lattice. Recorded because it is the kind of thing that gets retried.

**Why 96° and z 4875 out of the five framings rendered.** All five put the car in frame. The
choice is the CONTENT MIX, which is what makes a median comparison mean anything — the same
principle `EXTERIOR_CALIBRATION` states as *"both crops come out with the same proportion of
background… which is the check that the framings really are matched"*. Against `34b`'s 3.74%
crushed and 0.90% clipped:

| framing | crushed | clipped | x of 34b | note |
|---|---|---|---|---|
| `--stand 88,4880` | 0.62% | 2.69% | 1.47 | car small and behind the light run's glare |
| **`--stand 96,4875`** | **2.83%** | **3.08%** | **1.50** | **taken** |
| `--stand 100,4870` | 2.82% | 4.11% | 1.55 | car largest, but over `measure_frame`'s own 4% overexposure verdict |
| `--stand 104,4740` | 0.00% | 2.38% | 1.49 | 33a's oblique, but the car foreshortens to a sliver |
| `--stand 216,5300` (240° guideway, open fields) | 0.00% | 3.52% | 1.86 | the most legible car in the set and the worst measurement: no dark content at all |

**Why it is measured against `34b` and not against `33a`, which is its framing source.** Because
33a disagrees with the drum's own calibration. The committed wide frame `docs/engine-drum.png`,
verified at x1.39 of 34b, reads **x1.81** of 33a from the same pixels — 33a's whole-frame median is
0.1166 against 34b's 0.1515. One volume, one rig, one exposure, so calibrating the tram to 33a
would demand re-exposing the whole drum by 0.55 stops and would break the frame `DRUM_EXPOSURE`
was set on. 34b is also not an arbitrary substitute: it **contains the tram cars**, and
`tram.py`'s `CAR_BAYS = 4.0` was measured off it by projective rectification. The same reasoning
and the same numbers are in INV-044 for `29a` and the garden.

**What this framing does NOT settle.** The car's *colour*: 33a reads white body with maroon
window-band framing, and at 120 m through the drum's fog this frame cannot adjudicate a material.
And the two white nose lights: `tram.py` builds `tram_headlight` and the aspect here is broadside,
so they are edge-on. Both need a nose-on framing, which is a different shot and is not this one.

**Overturned by:** a Season 2–3 frame of the drum tram with a recoverable camera; or any change to
`interior.TRUSS_RADIUS_FRAC`, `TRUSS_DEPTH_M` or `tram.CAR_DEPTH_FRAC`, all of which move the
subject relative to the eye and invalidate both the framing and the 5.47% contribution measured
for it. `tools/export_scene.py --gate-drum` is what says so.

---

## INV-060 — The whole-distribution frame comparison, and the five tolerances derived from the show's own frames

**Authority 5 — declared method.** Every number below is measured off reference frames; what is
*invented* is the shape of the comparison and the five thresholds, and those are logged here.

**What:** `tools/measure_frame.py` now compares a render to its reference frame on **p5, p95, the
p5/p95 ratio, the crushed fraction and the clipped fraction** as well as on the median, with a
per-statistic tolerance and a combined verdict. The reference side is measured at
`gain = RENDER_OFFSET` so that the level offset the median gate already allows is not charged a
second time as a shape difference. The corpus, the pairs, every measurement and the re-verification
table are in `docs/layer4-lighting/frame_distribution.json`;
`python3 tools/measure_frame.py --derive` recomputes the thresholds from that corpus and exits
non-zero if the constants in the module have stopped describing it.

**Why necessary:** every exposure in this project — `ROOM_EXPOSURE`, `BESPOKE_EXPOSURE`,
`DRUM_CALIBRATION`, `EXTERIOR_CALIBRATION` — was set by one test: our frame's median over its
reference's median must land at x1.40 ±25%. The owner looked at the renders and said they read as
blockout while every gate was green, and **both were true**. A median says where the middle of a
picture sits and nothing about how far it reaches. `docs/engine-drum-garden.png` sits at x1.49 of
`garden.png` — inside the band — with p5 at **3.21x** the reference's and **0.01%** of the frame
below the measurable floor against the reference's 2.78% at the same exposure. A frame with no
blacks reads washed out whatever its median is, and the median test cannot see it.

### What is sourced

- **The corpus: 33 deduplicated authority-1 on-screen frames** that depict a lit set or a lit
  exterior — the thing our renders are. Every authority rating comes from
  `reference/00-INDEX.md`. Props on a studio backdrop, schematics, costume stills, authority-2
  production art, authority-4 fan reconstructions and both QUARANTINE folders are excluded.
- **The measurements**: `tools/measure_frame.py`, the same code on both sides, which is the only
  comparison this project has ever accepted (see the module docstring and INV-037).
- **The pair rule is not new.** `DRUM_CALIBRATION` already rules that two references may be used
  interchangeably when their medians agree within `TOL` — it accepts `garden.png` against
  `Babylon_5_2-22_34b.jpg` at *"8% apart, inside the ±25% the gate allows"* and rejects `33a` and
  `29a` on the same ground. Applied to the corpus, **124 of the 528 possible pairs qualify**.

### What is declared, and what constrained each of the five

| statistic | form | value | what constrained it |
|---|---|---|---|
| p5 | ratio to reference-at-offset | **x1.290** | p95 of \|ln(a/b)\| over the 124 pairs (ln 0.2548) |
| p95 | ratio | **x3.266** | same, ln 1.1837 |
| p5/p95 | ratio | **x3.378** | same, ln 1.2172 |
| crushed | ratio | **x11.42** | same, ln 2.4350 |
| crushed | absolute envelope | **0.22%–63.92%** | the min and max the corpus itself occupies at the offset |
| clipped | absolute cap, one-sided | **3.69%** | p95 of the corpus's own clipped fraction at the offset |

**Why the p95 quantile and not the maximum or p90.** The maximum of 124 samples is one pair, not a
tolerance: fitting to it produces an envelope no render could ever fall outside. At p90 the four
ratio bands reject roughly a tenth of matched pairs each, which compounds to about a quarter of the
reference material, and a gate that fails a quarter of the reference material is measuring the
material. At p95 each band admits 95% of the show's disagreement with itself. The 5% excluded per
statistic is the tail where the median test calls two frames equivalent and they are different
*pictures* — `29a` against `34b` is exactly that case and INV-044 already says so.

**And it is validated by running the gate on the show against itself**, both orders, 248 trials, in
exactly the form it is applied to us: per check it admits **85.5%–100%**, and the combined verdict
admits **77.4% (192 of 248)**. Six checks at 85–100% cannot combine to 95%; loosening them until
they did would put every one at its observed maximum. Part of the missing 23% is also real — the 124
pairs include a war room against a residential corridor, which agree on median by coincidence and
are not the same picture at all. One band is measurably looser than its nominal 95%: `crushed`
admits 85.5% because it was estimated at gain 1.0 and is applied to a *gained* reference, and
gaining changes a censored fraction nonlinearly. Stated, not hidden.

**THE ESTIMATE IS NOT STABLE TO ONE FRAME.** `gardens or greenery.jpg` was missed on the first
enumeration of the corpus and adding it — one frame in 33, 26 new pairs — moved the p5 band from
x1.224 to **x1.290**. p95 of a 124-pair sample is its 6th-largest value. These are bands good to
about 5%, not to three figures, and anyone tightening one should re-derive rather than trim.

**Why the reference is re-measured at `gain = RENDER_OFFSET` rather than compared raw.** Our
renders deliberately sit at 1.40x the show's level (INV-037). Comparing raw p5 to raw p5 would
count that offset twice. And scaling the **image** is not the same as multiplying the reference's
**statistics** by 1.40, which is the point: a gain lifts sub-floor pixels into the measurable set
where they arrive at the bottom and hold p5 down. `garden.png`'s p5 goes 0.0180 → **0.0178** under
a x1.40 gain, not to 0.0252. A frame with a black population keeps it when you brighten it, and
that is precisely the property our renders do not have.

**Why crushed needs an absolute envelope as well as a ratio.** The ratio band is blind at both
ends. Against a reference that crushes 30%, x11.52 permits anything from 2.6% to 100%; against one
that crushes 0.22% it permits nothing meaningful. The envelope is the range the show's own frames
occupy and it is what catches `docs/engine-plant.png` at 86.97% — outside anything in the corpus —
and `docs/engine-drum.png` at 0.00%.

**Why clipped is an absolute cap and not a band.** It was tried as a band and the corpus refused
to supply one: over the same 124 pairs the pairwise dispersion of the clipped fraction is x2.78 at
p50, x7.83 at p68 and **x53.7 at p90**. That is no structure at all — clipping is a function of
whether a practical light happens to be in shot. The cap is the corpus's own p95 at the offset, and
the interesting part is that **3.69% lands within 8% of the 4% threshold `report()` already
carried**, which had been derived independently from our own lamp geometry clipping 1.3–3.1%. Two
routes, one number.

### Two of the five results are negative, and that is recorded rather than hidden

**p95 and p5/p95 are nearly inert.** At the corpus's own dispersion the bands are x3.27 and x3.38,
which almost nothing fails. p5/p95 is the statistic that *sounds* like the right one and measures
the least, because it inherits p95's variance. They are kept because they do fire on the frames
where nothing bright is in shot at all — `docs/engine-cnc.png` p95 x0.23, `docs/engine-plant.png`
x0.19 — and because a reader needs to see that they were tried. **p5 is the discriminator**: it is
tight (x1.22) because the show's frames crush, so their 5th measurable percentile sits within 22%
of the 0.010 floor in almost every frame. Ours sit at 1.5–3.2x their references'.

### A measured finding that came with it, and it is not an invention

The median of the measurable pixels **is not proportional to exposure, and on some frames is not
monotonic in it**. Measured by scaling each corpus frame's linear luminance: d(ln median)/d(ln
gain) between x1.0 and x1.4 ranges from **0.97** (`Babylon_5_2-22_34b.jpg`) to **0.01**
(`more zocalo.png`), and **7 of 33 frames go down** somewhere in x0.5..x2.0 — `rotunda.webp`
−0.46, `Starfury.jpg` −0.37, `sleeping-in-light-05.jpg` −0.29,
`babylon 5 welcome sign, instructions, and hub.jpg` −0.16. The cause is the same censoring as
above. The consequence is that `gain *= 1.40 * ref_median / our_median`, the formula every value in
`ROOM_EXPOSURE` and `BESPOKE_EXPOSURE` was obtained from, assumes an exponent of 1 and on the
customs reference the exponent is **negative**. `STATE.md` already records the symptom for one room
— the plant *"sits at 1.59x either way"* — and attributes it to that room's geometry; it is a
property of the statistic. Numbers per frame are in
`docs/layer4-lighting/frame_distribution.json` under `median_exposure_response`.

### What it says about the exposures we already shipped

Every exposure with a committed frame and a recorded reference, re-measured. **Nothing was retuned
to produce this** — the table is the finding.

| family | exposure | old (median) | new | what fails |
|---|---|---|---|---|
| `DRUM_CALIBRATION` | wide | PASS x1.39 | **FAIL** | p5 x1.74, crushed 0.00% vs 2.66% |
| `DRUM_CALIBRATION` | garden | PASS x1.49 | **FAIL** | p5 x3.21, crushed 0.01% vs 2.78% |
| `DRUM_CALIBRATION` | tram | PASS x1.50 | **FAIL** | p5 x1.48 |
| anchor | corridor (defines 1.00) | PASS x1.39 | **FAIL** | p5 x1.64 |
| `ROOM_EXPOSURE` | medical | PASS x1.21 | **FAIL** | p5 x1.54 |
| `ROOM_EXPOSURE` | commerce | PASS x1.28 | **PASS** | — |
| `BESPOKE_EXPOSURE` | zocalo | PASS x1.43 | **FAIL** | p5 x2.81 |
| `BESPOKE_EXPOSURE` | hospitality | PASS x1.46 | **FAIL** | p5 x1.61, p5/p95 x3.67 |
| `BESPOKE_EXPOSURE` | command_control | PASS x1.46 | **FAIL** | p5 x1.44, p95 x0.23, p5/p95 x6.35 |
| `BESPOKE_EXPOSURE` | docking_bay | PASS x1.44 | **FAIL** | p5 x1.53 |
| `BESPOKE_EXPOSURE` | alien_sector | PASS x1.31 | **FAIL** | crushed x29.53 (too MUCH) |
| `BESPOKE_EXPOSURE` | customs | PASS x1.36 | **FAIL** | p5 x1.72, crushed x0.01 |
| `BESPOKE_EXPOSURE` | quarters | PASS x1.26 | **FAIL** | crushed x38.10 (too MUCH) |
| `BESPOKE_EXPOSURE` | council_chamber | PASS x1.41 | **FAIL** | p5 x2.20 |
| `BESPOKE_EXPOSURE` | plant | PASS x1.59 | **FAIL** | p95 x0.19, p5/p95 x4.97, 86.97% crushed |
| `EXTERIOR_CALIBRATION` | day, side box | PASS x1.40 (on p95) | **FAIL** | p5 x2.28, p5/p95 x2.39 |
| `EXTERIOR_CALIBRATION` | day, top box | PASS x1.40 (on p95) | **FAIL** | p5 x1.43 |

**17 of 17 on the old test, 1 of 17 on the new one.** `p5` fails 13 of 17 and it fails in one
direction on eleven of them: our shadows are brighter than the show's. The single pass is
`docs/engine-market.png`, which is the evidence the gate is not merely rejecting everything.

**Two of the failures are the opposite defect and that matters**: `alien_sector` and `quarters`
crush 30x and 38x MORE than their references, which happen to be the two brightest, least-crushed
frames in the whole corpus. The comparison is two-sided and fires both ways.

**Nine `ROOM_EXPOSURE` values cannot be verified at all** — industrial, store, transit, hospitality,
worship, research, detention, office and generic have no committed render. They were each set by
rendering a room, measuring it, and not keeping the render, so they are unfalsifiable until someone
re-renders them. `export_scene.EXPOSURE_FRAMES` records that as data and
`export_scene.py --gate-frames` prints it per row rather than passing them in silence.

**And `EXTERIOR_CALIBRATION['night']` has no reference frame at all**, which `export_scene` already
states and refuses to paper over. The most that can be said is that
`docs/engine-exterior-night.png` is 97.92% crushed against 37.22% for
`Cobra Bays with starfurries.webp` at the same offset — outside the corpus envelope, but the frame
is 9.2 km of mostly empty starfield and at that framing the statistic is content, not exposure.

### What this does NOT settle

- **It cannot separate "our shadows are too bright" from "our scene has nothing dark in it."** Both
  read as too few blacks. INV-044 already establishes that part of the garden frame's shortfall is
  *content*: `29a`'s clipped hedge, timber retaining walls and broadleaf canopy are things
  `garden.py` does not build, and no exposure puts foliage in a frame. A p5 or crushed failure is
  therefore a pointer to one of two different fixes, and the entry cannot say which.
- **It is still a whole-frame statistic on a fixed shot.** Point the camera at a wall and it
  reports the wall. The framing guard is `frame_signature`, not this.
- **The bands were derived from broadcast frames and may not describe a production render.**
  `EXTERIOR_CALIBRATION`'s day reference, `exterior more.jpg`, is authority 2 and is *not* in the
  corpus; its distribution verdict is reported for information only.
- **It says nothing about colour, texture, geometry density or silhouette** — the other things
  "blockout" means. This is one axis of craft, measured.

**Overturned by:** more authority-1 broadcast frames in `reference/`, which would move every band —
`--derive` is what forces the constants to follow. Any change to `FLOOR` or `CLIP` invalidates all
five at once, because every one of them is defined on the censored population those two thresholds
select. Any change to `RENDER_OFFSET` invalidates the offset-referred comparison and the two
absolute thresholds, which are both measured at that gain. And a demonstration that the show's
grade differs systematically between the frames we hold and the frames we do not — the corpus is 33
images from a 110-episode series — would mean the dispersion is being estimated off a biased sample.

---

## INV-070 — The geometric detail floor: visible line density, and the three bounds that derive it

**Invented:** the metric and gate in `station/density.py` — a per-location floor on **visible
line density**, λ = (length of edges a viewer would see as a line) / (surface area), in m⁻¹ — and
the derivation of that floor from three bounds with the smallest taken.

**Why necessary:** CLAUDE.md's layer-2 exit criterion is *"mesh, closed, correctly wound, inside
its own footprint"*, and every word of it is topological. **A cube passes all of it.** So 118
locations of blockout passed layer 2, layer 3 painted the blockout, layer 4 lit the blockout, and
every gate in the repository stayed green while the owner looked at the result and said the
buildings are "shitty little cubes" and the trees are a "sad excuse for a tree". The only density
figure anywhere in the project was a **ceiling** — `garden.py`'s self-test asserts the townscape
is *below* 0.06 tri/m², and `block_building` is documented "Cheap by design". There was no floor,
so there was nothing to fail. This is the floor.

**Constrained by** — and this is the part that matters, because a floor with no derivation is a
guess with a decimal point. Three independent bounds, mapping onto three of the four dimensions
in `docs/AAA-STANDARD.md`, and the gate uses the **least** of them:

1. **PERFORMANCE.** `budget.py` allots a triangle count to each scene's visible set (60,000
   interior, 300,000 drum, 400,000 exterior), read live rather than copied. Spend it as relief and
   the achievable line density follows from the construction: a raised-panel grid of pitch *e* over
   area *S* costs 12 triangles per cell (a closed box) and lays down 2*e* of line per cell, so
   *n* = 12·S/e² and λ = 2/e, giving **λ_budget = 2·√(n / 12S)**. Nothing in that is chosen. The
   self-test builds the very construction it is priced from, at the pitch the allotment buys, and
   asserts it clears the floor *inside* the allotment — so the floor is demonstrably reachable and
   not aspirational.
2. **PERCEPTION.** At 1440p (CLAUDE.md's stated target) and the project's own camera FOV — 55°
   interior and drum, 46° exterior, read out of `godot/scenes/*.tscn` — one pixel subtends
   θ = fov/1440. A feature needs two samples to exist, so the finest useful pitch is 2p where
   p = d·θ, and **λ_nyquist = 1/p**. Geometry past this is sub-pixel and is waste, not detail.
3. **FIDELITY.** Measured off Babylon 5's own frames by `measure_reference()`, with the same Canny
   operator at the same absolute contrast thresholds that `edge_fraction()` would apply to one of
   our renders. See INV-071 for the frames, the scale anchors and their uncertainty.
   **λ_ref = 2·f_edge / (proj_ratio · p)**, where f_edge is the dimensionless fraction of screen
   pixels lying on a line and proj_ratio is total surface over mean projected area, measured per
   mesh and coming out 4.00 everywhere because the meshes are closed (Cauchy).

   Bounds 1 and 2 are **ceilings** — past either, the geometry cannot be drawn or cannot be seen.
   Bound 3 is a **target**. Taking the minimum therefore reads: *match the show, unless the card or
   the screen cannot carry it.*

**Why line density and not triangles:** a subdivided cube is still a cube. Coplanar subdivision
adds edges of zero dihedral, which draw nothing, so λ does not move — asserted directly, on a box
split 8×8 per face at 64× the triangles. Two other cheats are closed the same way: a lathe of
radius *r* at turn angle τ can reach at most 1/(r·τ) and τ cannot fall below the crease threshold
without the segments becoming invisible, which puts every tessellated cylinder below the floor at
every scale the station is built at; and greeble finer than one screen pixel is excluded, because a
line only counts when both facets meeting at it are at least one pixel across at the composing
distance.

**The crease threshold, 3.24°, is derived rather than typed.** The image operator calls a pixel an
edge at a 4% luminance step. Under Lambert shading, dI = sin(α)·dα, and at α = 45° — the median
incidence over a hemisphere and the elevation every one of this project's render scripts actually
uses (`--sun-elev 45`) — a 4% step needs 0.0566 rad = 3.24° of normal change. The same threshold
defines a facet: a patch of surface with no visible line inside it.

**Result on the content as it stands: 11 of 118 locations reach the floor.** The measurement is at
module granularity for the 50 bespoke places (same granularity `directory.py` already uses for
layers 3 and 4) and per place for the 68 procedural ones. All 118 bind on the performance bound,
and on the fidelity bound alone every location sits between **0.2% and 19.7%** of what a Babylon 5
set carries, median 5.0%.

**Overturned by:** a rendering path that carries relief in geometry differently — Nanite-class
micropolygon rendering would move bound 1 by an order of magnitude, and displacement mapping with
correct silhouettes would move the geometry/texture line that bound 2 encodes. A change to
`budget.py`'s visible-set figures moves bound 1 directly and is meant to. A scale-anchored hull
frame would replace the exterior's inherited f_edge with a measured one. And a demonstration that
line density is the wrong proxy for perceived detail — a location that clears λ and still reads as
blockout — would mean the metric measures the wrong thing; λ says nothing about whether the lines
are in the right places, which is the one thing left for a reviewer.

---

## INV-071 — Metres per pixel in three reference frames, and the 1.75 m that sets it

**Invented:** the pixel-to-metre scale of the three frames `density.REFERENCE` measures, and hence
the absolute value of bound 3 above.

**Why necessary:** an edge-pixel fraction is dimensionless. Turning it into a line density in m⁻¹
needs a scale, and none of the reference frames carries one.

**Constrained by:** a standing human figure in each frame, measured at magnification
(`tools/refzoom.py` and a pixel-column dump), against an assumed stature:

| frame | figure | assumed stature | m/px | what it is |
|---|---|---|---|---|
| `10-interiors-generic-kit/more hallway.jpg` | 247 px | 1.80 m | 0.00729 | Grey transit tube, one figure mid-frame |
| `10-interiors-generic-kit/garden more.jpg` | 104 px | 1.70 m | 0.01635 | Garden terrace, standing group mid-frame |
| `09-garden-core-and-transit/garden.png` | 70 px | 1.75 m | 0.02500 | Garden landmark, two figures on the paving |

Stature is the only number here not measured off the frame. 1.70–1.80 m is an ordinary adult range
and the three frames were given values inside it according to whether the figure is male, female or
unresolvable; the resulting λ figures agree to within a factor of 1.8 across three frames from two
sectors, which is the cross-check that makes them usable at all.

**Three things this bound is NOT honest about, stated because they change how it may be used:**

* the counts include every line a set gets from **paint, decals, cast shadow, dressing and
  costume**, not only from form, so bound 3 over-states what geometry must supply;
* **perspective**. m/px is measured at the anchor figure's depth and applied to the whole frame.
  Foreground reads too coarse, background too fine. On `garden.png`, where the far side of the drum
  is half a kilometre behind the figures, this makes the number a **lower** bound;
* our composing framing is **closer** than these plates were shot at (2.8 m for a 2.9 m room,
  against 7.3 mm/px on a 1024 px plate), and requiring an equal screen line fraction at finer
  resolution requires more line per metre. Where that matters the column is labelled `%show` and is
  **not gated**.

Because bound 3 is one of three with the minimum taken, and because the performance bound binds on
all 118 locations, none of these three caveats currently affects a single verdict. They would if
`budget.py`'s allotments rose by 5× or more.

**Overturned by:** any frame with an object of established dimension in it — a Starfury, a
docking-bay door, a cobra-bay well — which would replace an assumed stature with a canon length. A
production still with a slate or a set drawing with a scale bar would close it outright.

**Adjacent finding, not this entry's subject but found while measuring it:** `garden.py`'s docstring
derives `TOWER_H_M = 16.0` from *"the two figures are ~35 px tall"* in `garden.png`. Measured at 11×
magnification and confirmed by a green-channel column dump, **those figures are 70–77 px**, not 35.
The green suit alone spans y = 352–401 and the full figure y ≈ 342–419. Whatever the tower's true
height is — the tower stands behind the figures, so a perspective correction pushes it back up — the
stated derivation is out by a factor of two and does not support the number it is attached to. Not
fixed here: `garden.py` is outside this work's file list, and the correction needs a depth estimate
this entry has no source for.


---

## INV-072 — The Garden's articulation: tree, block, and the hard landscape

**Status:** extrapolation, authority 5, session 3s.

**Invented:** every proportion in `station/garden.py`'s `tree()`, `block_building()` and
`hard_landscape()` — trunk radius 0.26 m, root flare x1.45 over 0.55 m, fork at 0.42 of height,
3–5 limbs; storey 3.2 m, structural bay 4.0 m, pilaster 0.55 x 0.18 m, expressed slab 0.32 m,
cill 0.85 m, window 1.95 m, reveal 0.28 m, cornice 0.45 m projecting 0.34 m, parapet 0.85 m;
kerb 0.15 x 0.12 m, hedge 0.8 x 1.05 m, step 0.16 rise / 0.34 going, planter r 3.1 m, bench
1.8 x 0.45 m, sail 5.2 x 3.4 m on 3.6 m masts, pergola 4.5 m bays at 2.9 m, track gauge 2.1 m.

**What is sourced and is not invented.** `reference/03-sector-blue/Babylon_5_2-22_29a.jpg`
(authority 1) is extracted in `reference/00-INDEX.md` as showing "paved winding paths in small
setts; clipped hedges; a water feature / cascade against a planted bank; a timber bench; a circular
raised planter with a **red-brown coping**; **orange sail canopies** on masts; a **multi-storey
glazed building** behind" and "a streamlined green-and-white transit car on a track".
`Babylon_5_2-22_33a.jpg` reads the drum wall as "landscape with roads and **field boundaries**".
Every object added here appears in that list. **None of them existed in the module.** What is
invented is their dimensions, not their presence.

**Why necessary.** The module scored 16.3% of its detail floor (`station/density.py`, INV-070) and
the owner, shown a render, called the buildings "shitty little cubes" and the trees a "sad excuse
for a tree". `tree()` was 30 triangles — a box trunk and one 6-segment cylinder — and
`block_building()` was 48: a box with proud bands. The module also **asserted `dens < 0.06 tri/m2`**,
so the sparseness was enforced, not accidental.

**The one design rule worth carrying forward.** Line density is metres of visible line per m2, so
what earns it is LENGTH, not triangle count. Measured in this module: a continuous cill band yields
**5.3 m of line per triangle**, a downpipe 2.0, a dwarf boundary wall about 20 — and a panel-relief
grid, which is the construction the budget bound itself is derived from, yields **0.17**. Thirty
times worse. Long thin prisms and continuous bands are how a landscape reaches its floor; panel
relief is how a *wall* does. Choosing the wrong one wastes the budget by an order of magnitude.

**Overturned by:** any frame establishing the Garden's storey heights or planting scale against a
figure of known stature.


---

## INV-073 — Interior articulation: the bands, grids and trim every procedural room carries

**Status:** extrapolation, authority 5, session 3s.

**Invented:** the fit-out proportions added to `station/rooms.py`'s `build()` — skirting 0.14 m
(with a 0.05 m secondary), dado at 0.95 m, picture rail 0.75 m below soffit, cornice 0.16 m
projecting 0.055 m, deck bay joints at 0.40 m, soffit tee grid at 0.40 m with a 0.07 m tee, wall
mullions 6 per bay at 0.06 x 0.035 m, raised panels 0.045 m proud, and up to four 0.11 m conduit
runs at high level.

**What is sourced.** The *language* is `07-sector-grey/grey level 1.webp` and
`03-sector-blue/war room.webp`, already used by `materials.shell_rib_painted`, whose entry records
the pilaster-to-wall relationship this extends. Every new group binds to a material **already
measured** — wall trim to the wall plane, joints to the deck, mullions to the pilaster, conduit to
`plant_valve_metal`. **No new colour is introduced anywhere.**

**Why necessary.** The 68 procedural rooms are 58% of the station and shared one generator that
emitted deck, soffit, four walls, ribs and fixtures — 336 triangles over 384 m², **18.0% of the
detail floor** (`station/density.py`, INV-070). A flat field of wall between ribs is what reads as
a placeholder box.

**The rule this applies, carried from INV-072.** Line density is metres of visible line per m², so
LENGTH earns it. A band round a room's perimeter is twelve triangles laying four lines the length
of that perimeter — roughly 13 m of line per triangle at this room size, against panel relief's
0.17. Bands first, then grids, then panels. The module went 18.0% → 100.7% at 2,592 triangles a
bay, inside a habitat cell budget still at 66%.

**One defect this found, and it is the reason the trim check exists.** The walkability flood fill
treats any non-shell group as an obstacle, so the new trim broke it on all 68 rooms. The tempting
fix — add the trim to the ignore list — is the move this project keeps catching itself at: a gate
found something and the gate gets changed. Instead the exemption is *earned*: a check asserts every
trim group is either thinner than a step (0.10 m) or above head height (2.0 m). It immediately
caught a 0.11 m conduit at chest height in the brig and in security_central, because those cells
have a low soffit. The conduits now stop rather than drop; a low room gets fewer, not lower.

**Overturned by:** any frame establishing B5 interior trim heights against a figure of known
stature.

## INV-080 — The drum's shadow ration, its ambient, and the two post-process terms that were lighting it

**Status:** extrapolation, authority 5, session 3u. Supersedes the exposure half of INV-037 for
the drum only.

**Invented:** `export_scene.DRUM_SHADOW_LIGHTS = 24` (was 2), `drum.tscn`'s
`ambient_light_energy = 0.03` (was 0.15), `glow_bloom = 0.0` (was 0.06), `glow_levels` 1 and 2 in
place of the engine's default 3 and 5, and `DRUM_EXPOSURE = 1.41 x 2.70 = 3.807` (was 1.41).

**What is sourced.** Nothing here is a new claim about the *fittings* — the light runs are still
where `interior.guideway_truss` puts them, still `LAMP_COLOUR`, still authority 1 from
`Babylon_5_2-22_34b.jpg` and `33a`. What is invented is how much of that light is allowed to reach
a surface the fitting cannot see, which the show's frames constrain only through their own
histograms. Three do:

| frame | what it constrains |
|---|---|
| `09-garden-core-and-transit/garden.png` | the whole distribution the garden framing is matched to — p5 0.0180, crushed 5.63% |
| `03-sector-blue/Babylon_5_2-22_34b.jpg` | the drum floor is evenly lit end to end and the truss is a **black silhouette** against it |
| `03-sector-blue/Babylon_5_2-22_33a.jpg` | the truss underside, seen from below, is dark; the tram is slung in that dark |

**Why necessary.** At 2 of 60 lamps casting shadows, 58 light sources passed through every wall in
the volume. The calibrated garden frame had **0.99% of its pixels below the measurable floor
against its reference's 5.63%**, and its p5 sat at **x2.97** of the show's when both were put on the
same median. Nothing in the drum had a dark side. That is the state the owner called blockout, and
no exposure fixes it because exposure moves the whole histogram together.

**How each number was reached.**

* **24 shadow casters.** Measured on the garden framing at matched median: 2 gives p5 x2.92, 24
  gives x0.94, 60 gives x0.84. 24 clears the x1.29 band with 27% of margin, so the last 36 buy
  margin nobody asked for and cost 60 s -> 76 s a frame.
* **Ambient 0.03.** At 24 casters, 0.15 -> 0.03 moves p5 0.0175 -> 0.0158. It is nearly inert at
  **2** casters (0.15 -> 0.02 moves p5 by 0.003, session 3t), and that is the whole point: an
  unoccluded constant fill only matters once the direct light is occluded. SSAO, the only thing
  that occludes ambient in this scene, was measured inert — radius 12 m, intensity 4.0,
  light_affect 0.9 changed **0.23%** of the frame by more than 8/255.
* **glow_bloom 0.0 and the tight levels.** Not a taste judgement and not derived from a frame:
  `copy.glsl:194` computes `feedback = max(smoothstep(threshold, threshold+scale, luminance),
  glow_bloom)`, so 0.06 fed 6% of **every pixel in the frame** into the glow blur regardless of its
  luminance, and Godot's default levels 3 and 5 (`environment.cpp:1605`) blur it at 1/4 and 1/16
  resolution — a halo the width of the picture. Switching glow off entirely took p5 0.0282 ->
  0.0158, so **44% of the drum's shadow floor was bloom rather than light**. Levels 1-2 with
  bloom 0 keep the halo on the light tube, which `34b` shows, and remove the wash.
* **Exposure x2.70.** A compensation, not a new level judgement: the three terms above were
  carrying most of the frame's median and the lamps have to make it up. It is **not** the garden
  framing's own best number (x2.40 would put it at x1.38 against the x1.40 target); it is the value
  that fits all three calibrated framings inside the +/-25% band at once.

**What it costs, stated rather than implied.** 13 s -> 60 s a frame at 960x540 **on lavapipe, a CPU
rasteriser**. That is a bound on how often this project can look at a frame and says nothing about
an RTX 4070, where 24 omni shadow cube maps in a 250k-triangle scene is an ordinary load. Nothing
in `station/budget.py` moves: no triangle, instance or texture changes.

**The residual, and it is content rather than light.** The garden framing passes both tests; its
foreground is still x1.55 brighter than the reference's at matched level. Measured on
`garden.png`'s bottom third: **30.9% of it is below linear Y 0.04 against 0.4% of ours**, and only
**2.8%** of that population is near-neutral — 22.1% is green-dominant and 20.5% blue/teal, mean
chromaticity r/g/b 0.433/0.293/0.266. A grey surface in shadow is neutral. The show's dark
foreground is **foliage, water and dark timber**, which is what INV-044 concluded from `29a` two
sessions earlier: no exposure and no shadow scheme puts foliage in a frame. See
`export_scene.LIGHT_DIRECTIONALITY`.

**Overturned by:** an authority-1 frame of the drum interior showing the guideway light runs
throwing a *visibly bounded* pool rather than a wash, which would make the fittings directional
after all; or a measurement showing that lavapipe's shadow attenuation differs materially from a
hardware Vulkan driver's, which would make every number above a software artefact.

---

## INV-081 — The drum's walkable surface: the stride, the step tolerance and the tile

**Status:** extrapolation, authority 5, session 3w. Engineering, not canon: the show establishes
that people walk in the Garden and constrains nothing about how a simulation gives them a floor.

**Invented:** `drum_walk.STEP_M`'s use as the collision-vs-render tolerance; the rule that the
drum's collision ground is built at the coarsest LOD stride whose *already-measured* error stays
inside that tolerance; and the tile as the unit of drum collision, sized from the walk gate.

**What is sourced, and it is most of it.** No dimension here is new. The floor radius is canon's
278.3 m. The lattice, the patch grid, the LOD strides and their measured errors are
`station/drum_ground.py`'s and were derived in an earlier session from a 1.5-pixel screen-error
budget. The heightfield itself is INV-020/INV-072's terrain. `FLOOR_MAX_DEG = 45.0` is Godot's
`CharacterBody3D.floor_max_angle` default of 0.785398 rad — an engine fact, cited rather than
chosen, and the number `is_on_floor()` actually decides against. What is invented is only how those
existing measurements are *combined* into a decision about what a body stands on.

**The step tolerance, and why it is not a new number.** `rooms.TRIM_MAX_PROUD_M = 0.10 m` already
carries this project's definition of a step — "a step you do not trip on" — and it is imported
rather than restated, so the station has one definition of a step. A disagreement between the ground
a player sees and the ground their feet rest on *is* a step: positive and they hover, negative and
they are shin-deep in a field.

**The stride, derived.** `drum_ground.lod_error_report` already measures, per stride, how far a
decimated lattice departs from the true field — over whole patches at full resolution, one per
land-use band, so a terrace riser is sampled rather than stepped over. That measurement was made to
answer a rendering question and answers this one unchanged:

| stride | cell | measured error | verdict |
|---|---|---|---|
| **1** | 3.90 m | **0.007 m** | usable |
| 2 | 7.81 m | 0.193 m | too coarse |
| 4 | 15.61 m | 0.538 m | too coarse |
| 8 | 31.23 m | 1.048 m | too coarse |
| 16 | 62.45 m | 4.459 m | too coarse |

So stride 1, and that is not a formality — the criterion fails on the very next level, which is what
makes it a criterion rather than a label.

**The tile, derived.** `walkable.TRAVERSE_FRAMES` (1800 frames = 30 s) and `player.gd`'s 4.2 m/s
mean the walk gate asks a body to cover **126 m** in a straight line. A ground patch is
124.9 x 129.4 m, and a spawn can sit on a patch corner, so the nearest tile edge must be at least
`ceil(126 / 124.9) = 2` whole patches away. Two rings is 5 x 5 patches, **51,200 triangles**. One
ring reaches 125 m and fails by a metre — asserted, and demonstrated failing.

**Why not the whole drum.** 573,440 triangles at stride 1, against a station whose entire other
66 walkable decks carry 74,044 between them. The drum is 4.5 million m2 of open country and a ring
deck is a 2.6 m tube; the tile is the streaming unit that difference forces.

**What would overturn it.** A character controller with a different `floor_max_angle`, or a
walk gate that asks for a longer traverse — both change a derived number rather than a chosen one,
which is the point. A terrain change that flattened the field below 0.10 m of stride-2 error would
make stride 2 legal and halve the cost; the self-test asserts that it currently does *not*, so such
a change cannot happen silently.

---

## INV-082 — The frame triangle budget contradicts itself, and this records the contradiction rather than resolving it

**Authority 5 — declared extrapolation. Session 3x.**

`station/budget.py` carries two mutually exclusive figures for how many triangles the target card
affords in one frame at 1440p60, and both are load-bearing:

| where | figure | how it is used |
|---|---|---|
| `BUDGETS` comment | *"a 4070 sustains roughly 20-30 M triangles/frame at 1440p60"* | the exterior's 400,000 is derived as **"2% of frame budget"**, which implies a 20,000,000-triangle frame |
| `FRAME_TRIANGLES` | **1,200,000** | every interior and drum share is a percentage of this |

They differ by **16.7x**. Against `FRAME_TRIANGLES` the exterior's own 400,000 is **33% of frame,
not 2%**. `docs/AAA-STANDARD.md`'s PERFORMANCE-5 descriptor quotes the 2% sentence approvingly as an
example of a budget number defended against the frame it comes out of, so the contradiction is
written into the rubric as well as the gate.

**What constrained the resolution.** Nothing here settles it, deliberately. Session 3x's brief was to
measure what a player renders; moving a frame budget is the single cheapest way to make a gate green
without any content improving, and CLAUDE.md's "the triangle budget is a TARGET, not a ceiling"
warns against the mirror-image error. So **every interior bound is gated against the smaller,
tighter figure (1,200,000)**, because a budget's job is to be the binding constraint, and the
discrepancy is recorded here instead of averaged away.

**What is genuinely known.** Neither number is measured. 1.2 M is conservative for the class of card
(published AAA titles submit several million triangles a frame at 1440p on this hardware); 20 M is
optimistic (it implies a sustained 1.2 G tri/s, which is near the ceiling of what a five-GPC Ada
part reaches with a trivial vertex shader and nothing else running).

**What would overturn it.** One frame capture on an RTX 4070 / RX 7800 XT running the real build at
1440p, reading submitted primitives and frame time. That single measurement replaces both numbers.
If 20 M turns out to be the right reading, every interior bound in `budget.py` has 16x more headroom
than it currently claims and three of the five bounds now failing become comfortable passes — which
is exactly why the question is worth one capture.

---

## INV-083 — The budgeted camera: 70 degrees vertical at 16:9 — CLOSED, the shipped camera now matches

**Authority 5 — declared extrapolation. Session 3x.**

`station/budget.py` measures what a player renders by counting triangles inside a real frustum on an
assembled deck. The frustum needs a field of view and the shipped build does not state one.

**What is sourced from the build, not invented.** `godot/scripts/player.gd` sets `_cam.near = 0.15`,
`_cam.far = 12000.0` and `eye_height_m = 1.7`; all three are read out of that file at run time by
`budget.shipped_camera()` rather than copied, so they cannot drift. `godot/project.godot` opens at
1920x1080 and CLAUDE.md's target is 1440p — the same 16:9, and aspect is what shapes a frustum.
Pixel count changes shading cost, not the triangle set.

**What is declared: 70.0 degrees, VERTICAL.** Godot's `Camera3D.fov` is the vertical field of view
when `keep_aspect` is `KEEP_HEIGHT`, so a vertical figure is the one that can be pasted straight
into the engine. **Verified against the engine rather than remembered** — Godot 4.4 double,
headless, `Camera3D.new()` prints `fov=75.0 keep_aspect=1`, and `Camera3D.KEEP_HEIGHT` is 1. At 16:9,
70 degrees vertical is **102.4 degrees horizontal**, the top of the range PC first-person games ship,
and it is deliberately at the wide end: a budget measured at a narrow view understates by exactly
the geometry the wider view adds.

**What constrained it.** The lower bound is the judge's camera — `docs/judge-3w.md` rendered at 55
degrees vertical, and gating there would flatter the content by 40% (93,618 triangles against
155,018 at the same pose). The upper bound is the shipped camera: `player.gd` sets **no** `fov`, so
a player is given Godot 4's Camera3D default of **75 degrees vertical**, and at that fov the same
pose renders **161,792 triangles, 6,774 more than the budget measures**. `budget.py` therefore gates
that the shipped camera is not wider than the budgeted one.

**CLOSED the same session it was opened.** `player.gd` now sets `_cam.fov = 70.0` explicitly, so the
budget and the build agree by construction rather than by coincidence, and the gate reads
`70 deg / 70 deg, +0 against the budgeted camera`. The alternative — moving `DECK["fov_v_deg"]` to 75
and re-measuring — was rejected because it makes `frustum structure` worse by 6,774 triangles to fix
a bookkeeping mismatch, and the wide bound was already deliberate.

**What would overturn it.** A decision to ship a different fov; the gate names the one line either
way. A `fov` slider in options, which most PC games have, turns this into a bound that must be
measured at the widest setting the slider allows — and note the check is one-sided by design: a
NARROWER shipped camera is fine, because it renders less than the budget priced.

---

## INV-084 — The interior draw-call budget: 1,041 a frame, from CPU time

**Authority 5 — declared extrapolation. Session 3x.**

Before this there was no interior draw-call budget in existence. `BUDGETS["exterior_draw_calls"] =
64` was the only draw-call number on the station and it gates a manifest, not a frame.

**Derived from what a draw call actually costs, which is CPU.** A draw is a submission — state
validation, descriptor binding, a command-buffer write on the render thread — not GPU work. So

    draws <= frame_ms * render_thread_share / per_draw_ms
           = 16.667 * 0.25 / 0.004  =  1,041 draws a frame

| input | value | basis |
|---|---|---|
| `frame_ms` | 16.667 | 1440p**60** is CLAUDE.md's target. Not a choice. |
| `render_thread_share` | 0.25 | the render thread also culls, clusters lights, builds shadow lists and drives the RHI. A quarter of it for submission is the planning split. **Declared.** |
| `per_draw_us` | 4.0 | Vulkan, one uniform set per surface, no GPU-driven pipeline; Godot 4 Forward+ is not bindless. **Declared, and the weakest number here.** |

**The cross-check is the reason to believe 4 us at all.** The break-even batch — the triangle count
at which a draw's GPU work exceeds the CPU cost of submitting it, at the 1.2 G tri/s the
`BUDGETS` comment's own "20-30 M tri/frame at 60" implies — is `1.2e9 * 4e-6` = **4,800 triangles**.
This file's exterior budget, set sessions earlier on a completely unrelated argument, allows 400,000
triangles in 64 draws: **6,250 triangles a draw**. Two independent derivations, 30% apart. That
agreement is printed on every run.

**The cap is per frame, not per subsystem.** Exterior, interior, NPCs and effects submit into the
same 4.17 ms, so the gate reports the combined figure (325 today: 286 interior resident + 39
exterior) as well as the interior's own (139 after frustum culling).

**What would overturn it.** A frame capture on target reading submission time per draw. A move to
`MultiMesh` or GPU-driven submission changes `per_draw_us` by an order of magnitude and makes this
bound irrelevant — which would be a good outcome, since the corridor is 414 identical bays and
instances none of them.

---

## INV-085 — The collision triangle budget: tolerance for density, memory for total

**Authority 5 — declared extrapolation. Session 3x.**

There was no collision budget at all, on any deck, before this. The station carried 75,642 collision
triangles across 66 ring decks (`deck.py --sweep`) and 573,440 more in the drum's ground at lod0,
and none of it was measured against anything. **Bound 1 was red on first measurement and applying
its own remedy took the ring decks to 35,746 — a 53% cut — for a station total of 609,186.**

**Bound 1 — tessellation against tolerance, and it invents nothing.** The only correctness
requirement on a collision surface is that it represent the surface to within the tolerance the walk
gate certifies. Triangles finer than that buy nothing a player can feel and cost memory, BVH build
time and streaming latency. Both generators already claim to derive their density this way, so the
bound is theirs:

* **corridor** — `collision.corridor_shell` sized its angular step from `MAX_SAG_M = 1 mm`, the sag
  of a facet inside the true cylinder, and its own comment said 1 mm "is far below anything a
  character controller reacts to". The tolerance a floor is *certified* against is
  `collision.STEP_TOLERANCE_M = 5 mm`. Sag scales as the square of the step, so 5 mm allows
  `sqrt(5)` times fewer steps: **437 against the 977 built. The shell was 2.24x the size the
  project's own certified tolerance required** — 4,325 triangles a deck, and this bound was red.

  **FIXED, and the fix is the bound's own argument applied.** `MAX_SAG_M = STEP_TOLERANCE_M` now,
  so the two cannot diverge again by anybody editing one of them. The shell builds 437 steps,
  `blue/0/0`'s corridor shell falls 7,824 -> 3,496 triangles and the whole deck 5,150. **What
  changed for a body: nothing measurable.** The shell's own floor lip rose 0.72 mm -> 1.85 mm
  against the 5 mm bar it is certified at, and the same deck re-walked to the same numbers —
  `traverse_m 125.94`, `offfloor 0/1800`, into `docking_bays` from 6.31 m to 0.04 m, 5 inhabitants
  looking up 3 deg off. A collision change that is not re-walked is a collision change nobody
  checked.
* **drum** — `drum_walk.collision_stride` already picks the coarsest LOD stride whose height error
  stays under `drum_walk.STEP_M` (0.10 m, itself `rooms.TRIM_MAX_PROUD_M`). Stride 1 at 0.007 m is
  legal, stride 2 at 0.193 m is not, so the bound is that the tile was *built* at stride 1. It was.

Nothing in bound 1 is a new number: `STEP_TOLERANCE_M`, `MAX_SAG_M` and `STEP_M` are all the
repository's own, and the rest is arithmetic.

**Bound 2 — resident memory, and this one does invent.** Godot's `ConcavePolygonShape3D` keeps its
faces and BVH in system RAM, and this engine is built `precision=double`, so a `Vector3` is 24
bytes. Per triangle: 3 vertices x 24 B = **72 B** of face array, plus a BVH of about 2N nodes each
holding an AABB (2 x Vector3 = 48 B) and three ints, ~64 B a node = **128 B**. **About 200 B a
triangle.** The allowance is **1% of a 16 GB machine = 160 MB = 800,000 triangles**; 16 GB is the
companion figure to CLAUDE.md's stated 12 GB VRAM card and is itself declared. Measured: 609,186
triangles resident if the whole station were loaded at once — **122 MB, 76% of the allowance, and
94% of it is the drum**. (649,082 and 88% before bound 1's fix. Cutting the corridors made the
drum's *share* larger, which is the honest reading: the ring decks were never where the collision
memory was, and the one number worth attacking next is the drum's 573,440.)

**What this bound is actually for, stated because it is not obvious from the number.** The
regression this project has already made once is handing the render mesh to the physics engine
(session 3v: a body wedged on a 66 mm lighting channel). Applied station-wide that is 40.0 M
triangles and this bound goes red by 50x. Applied to **one** deck it is 597,418 triangles — 75% of
the allowance, and this bound does **not** catch it. Bound 1 does, at 59x. Both are exercised by
`budget.py --prove`, which feeds every bound the regression it exists to catch and fails if one
survives.

**What would overturn it.** One RSS measurement on target with and without the shapes loaded settles
`bytes_per_tri`. A machine specification in CLAUDE.md settles the 16 GB. A different character
controller with a different step tolerance moves bound 1, which is the point of deriving it from a
constant rather than choosing it.

---

## INV-086 — The station's signage face: a 5×7 blocky lattice standing in for a serif

**Authority 5 — declared extrapolation. Session 3x.**

`station/signage.py` has held authority-1 transcriptions of the customs boards since session 2q and
had no way to draw them: its own docstring said "a texture generator will later render
`BOARDS[...]['lines']` onto the panel. It does not exist yet and that is fine: the words are the
part that can be lost." The words survived. This is what draws them, and two things about it are
invented.

**What is sourced.** Everything about proportion and colour, measured off
`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg` (authority 1),
linear and sRGB-decoded, regions in normalised coordinates so every figure can be re-measured:

| what | region | measured |
|---|---|---|
| black field | (.320,.250)-(.590,.265) | linear (0.0033, 0.0032, 0.0052), **L 0.0034** |
| gold header | (.345,.275)-(.575,.300) | top-5% (0.594, 0.580, 0.388), L 0.445 p95 |
| notice gold | (.345,.455)-(.580,.500) | top-5% (0.561, 0.541, 0.330), L 0.448 p95 |
| blue bar | (.470,.335)-(.487,.352) | linear (0.1068, 0.1049, 0.6378), L 0.1438 |
| architecture | three independent patches | L 0.031 / 0.0086 / 0.0222 |

The two gold readings normalise to (1.000, 0.976, 0.653) and (1.000, 0.964, 0.588) — **1% apart in
G and 6% in B** — so the mean (1.000, 0.970, 0.620) is one source seen twice rather than an average
of two guesses. Typography likewise: on the 203 px panel the notice caps are 9 px at a 17.5 px line
pitch, so **line pitch is 1.94× cap height**, and the header caps are 13 px, **1.44× the notice
caps**. Both ratios are used verbatim.

**The finding those numbers establish, which is the reason the module exists in this form:** a lit
sign is simultaneously the **brightest and the darkest thing in the frame**. Its text peaks at
**21×** the luminance of the structure around it (0.445 against a 0.021 mean of three patches)
while its own field sits at **6× darker than the wall** (0.0034 against 0.021). Contrast inside one
sign is about **130:1**. An engine frame of our walkable deck measured against the show's corridor
anchor reads p5 ×11.09 against a ×1.29 band with **zero crushed pixels**; signage is the one piece
of content on this station that is black by construction.

**What is invented, and it is one thing: the letterforms.** The show's *display* face is
unmistakably a **serif** — "WELCOME TO" and "BABYLON 5" carry bracketed serifs in the reference
frame — and a 5×7 lattice cannot express a serif at any size. What a 5×7 lattice *can* express is
the coarse bitmap face **the same panel** uses for its notice block ("REMEMBER / Smoking permitted
in designated areas only"), which is visibly a low-resolution face. So the notice face is
substituted for the display face, at the display face's measured proportions. The alternative was
no lettering at all.

Two smaller declared choices ride along. **Tracking** is 0.25 of a 5-wide cell, because the
reference's notice face is tightly set and one cell column is the natural unit of a lattice; it is
not measured, because the frame is too soft at that scale to count inter-letter pixels. **The
address format** `SECTOR RING-DECK BEARING` is derived rather than sourced: it is the coordinate
every other module in this project already addresses a place by, so a player reading a sign and an
agent reading `directory.py` are reading the same thing. A station whose signage used a private
numbering would be one where a sign could not be checked against anything.

**What would overturn it.** Any Season 2–3 frame showing a *corridor* sign at legible resolution —
the reference set has exactly one legible signage frame and it is a customs-hall display board, not
a door plaque, so the door plaque's size, mounting height and layout are all extrapolated from it.
A frame showing an Earth Alliance face at high resolution would replace the letterforms outright.
And a frame showing that door signage on B5 is *engraved* rather than lit would overturn the whole
premise, taking the 130:1 with it.

---

## INV-087 — ORIGIN on the identicard: three attested worlds and twelve polity names

`station/npc/resident.py`, `ORIGIN`.

**What.** Every resident's identicard carries an `ORIGIN`. The prop reads `EARTH` for a human
(authority 1, `reference/11-props-and-technology/identicard readout.webp`). The other fourteen
species aboard need one and the reference set names almost no worlds.

**Why it is not simply looked up.** The homeworld names of Babylon 5's species are well known
outside this repository and are exactly the kind of fact hard rule 1 forbids being written from
memory. What this repository actually attests is three: **EARTH** at authority 1 from the prop,
**NARN** at authority 4 (`docs/gazetteer/FACTIONS.md` §6.1 — "the homeworld was bombed; Narn is a
Centauri protectorate"), and **MINBAR** at authority 4 (§10.1 — Sinclair leads the Rangers "from
Minbar").

**What constrained it.** ORIGIN on a customs record is a *jurisdiction*, not an address — which is
why `EARTH` and not a city. So where no world is attested, the field takes the **polity name from
FACTIONS.md's own section headings** (`CENTAURI REPUBLIC`, §7) or the **species designation as
§9.2 lists it** (`DRAZI`, `BRAKIRI`, `PAK'MA'RA` — the last at authority 3, the only spelling the
reference set holds, from the licensed trading card). Every string therefore traces to a line in
this repository. The tail bucket reads `LEAGUE — UNCLASSIFIED`, because §9.2's "other" is not a
species and cannot have a world.

**A consequence worth stating:** all 155,000 humans read `EARTH`. Earth Alliance colonies exist and
this repository names none of them, so a colonial origin would be unmarked invention. §2.4's
argument for the human share is that the station is EA sovereign territory, which makes `EARTH` the
jurisdiction whether or not the holder was born there.

**What would overturn it.** Any frame showing a second identicard, or any in-repo source naming a
world. A single non-human card would replace up to twelve of these rows at once.

---

## INV-088 — `02` numbers the atmosphere, not the species

`station/npc/resident.py`, `ATMOS_NUMBER`.

**What.** The prop reads `DES/ATMOS: HUMAN/02` and `canon/00-MASTER.md` §1.4 records it as "Human
atmosphere designation **02**". This module reads the field as *designation / atmosphere number*,
so **every species breathing the standard oxygen mix gets `/02`** — a Narn card reads `NARN/02`.

**What constrained it.** The customs board establishes six standing atmospheres and
`station/npc/schedule.py` already refuses to number the other five, for the stated reason that
nothing numbers them and a wrong number printed on a wall is worse than a blank. That refusal is
kept: `ATMOS_HUMID`, `ATMOS_METHANE` and `ATMOS_UNDISCLOSED` render with **no number at all**. The
only question this entry settles is whether `02` travels with the *species* or with the *mix*, and
the alternative reading — a human-only code — would leave fourteen species with no atmosphere
number, which makes the field useless as the customs check `FACTIONS.md` §3.4 describes it as.

**What would overturn it.** One frame of an identicard for a non-human oxygen breather. If it reads
anything other than `/02`, the field is a species code and this is wrong.

---

## INV-089 — The local bias: 0.70 of leisure is taken in a sector you already belong to

`station/npc/resident.py`, `LOCAL_BIAS`.

**What.** A resident's bar, restaurant, market and place of worship are resolved once, at creation,
and 0.70 of the time from the sectors they already live or work in.

**What constrained it.** Both ends, and neither is free. At 1.00 the station is five villages that
never mix, which contradicts `FACTIONS.md` §12's whole friction layer — the Zocalo and the customs
halls are where species meet. At 0.00 everybody crosses 8 km for a drink and the sectors have no
character. 0.70 is the value at which a Red Sector bar is mostly Red Sector's people and roughly
one in three faces is from somewhere else.

**Why it is a property of the person and not of the evening.** A resident who picks a different bar
each night is a random walk wearing a name; a regular is somebody the player can meet twice.

**What would overturn it.** Anything measuring how far residents travel aboard — a transit
frequency, a stated commute, a scene establishing that a named character drinks somewhere outside
their own sector as a matter of course.

---

## INV-090 — The identicard's date format is DD/MM/YY over a 22xx century

`station/npc/resident.py`, `_dob`.

**What.** The prop reads `DOB: 12/10/25`. Two digits of year, and under the 2260 datum that is
2225 — Lyta Alexander at 35. The day/month order is **ambiguous in the only sample**: 12/10 reads
either way.

**What constrained it.** Nothing in the sample. DD/MM is chosen because the field is 2 digits of
each and every other reading is equally unsupported; the choice is recorded here rather than
absorbed so that it can be reversed in one line.

**A consequence the format itself creates, and it is kept:** a two-digit year cannot represent a
Hyach born 240 years before the datum without wrapping. The record therefore stores a full year and
the *card* renders two digits, which is what an Earth Alliance form designed around human lifespans
would actually do to a long-lived species. That is a story about the bureaucracy, not a bug.

**What would overturn it.** One identicard whose first field exceeds 12.

---

## INV-091 — Adult age bands, and the two species that get a longer one

`station/npc/resident.py`, `AGE_BAND`, `AGE_SKEW`.

**What.** Humans are drawn from 18–68 with the mode early; Hyach from 30–240; Minbari from 25–130;
everybody else takes the human band. `AGE_SKEW = 1.64` is **derived, not chosen**: it is
`ln((34−18)/50) / ln(0.5)`, the exponent that puts the median at 34 in an 18–68 band.

**What constrained it.** Exactly one claim in this repository bears on alien lifespan —
`FACTIONS.md` §9.2 calls the Hyach "long-lived" at authority 4. Minbari take a longer band on the
same footing. **Everything else deliberately takes the human band**, because inventing thirteen
lifespans would be thirteen unsourced numbers where one honest default does the same work. The
skew exists because `schedule.ROLE_WEIGHTS` is an apportionment of *jobs*: a working population is
not uniform over its adult range. The first version used an exponent of 3.0 by eye and produced a
median of 24, which is a station staffed entirely by graduates — that is why the exponent is now
derived from the median rather than picked.

**Children.** Only the three roles with no work hours can be a minor, and only 8% of them:
`FACTIONS.md` §11.2 (Downbelow) and §6.2 (13,000 Narn refugees) both describe populations that
plainly contain children, and a visiting family is ordinary. A station of 250,000 adults would be a
garrison.

**What would overturn it.** Any stated lifespan or age for any species.

---

## INV-092 — One conditional status in twelve is expired

`station/npc/resident.py`, `VISA_EXPIRED_P`, `_visa`.

**What.** The `VISAS` field is filled only for somebody whose right to be aboard is conditional —
`TRANSIT nD` for a visitor, `SANCTUARY` for a refugee, `NO STATUS` for a lurker — and 1 in 12 of
the first two reads `EXPIRED`.

**What constrained it.** `FACTIONS.md` §3.4, on this exact field: "**visa fraud, forged identicards
and expired status are the station's most ordinary crimes**, and the reason lurkers avoid readers."
That sentence bounds it from both sides. *Most ordinary crime* cannot be rare, so a rate of 1 in
1,000 would make the customs layer decoration. It is still a crime, so it cannot be most people —
at 1 in 3 the station is not administered at all. 1 in 12 puts several expired cards in any large
room and makes a reader check a real event. The visitor's stay length comes from §2.3's stated mean
of seven days, drawn over twice that.

**What would overturn it.** Any figure for customs enforcement volume or detention numbers.
`FACTIONS.md` §2.3's ~12,600 transactions/day is the right shape of source; it gives throughput but
not a failure rate.

---

## INV-093 — 0.35 of residents eat out

`station/npc/resident.py`, `EAT_OUT_P`.

**What.** `schedule.Activity.EAT` sent every resident to a public eating place. 0.35 of them now
do; the rest eat at home, or in the mess where they work if the meal falls inside their shift.

**Why it exists at all.** The first cast list this module printed put **all 28 of Downbelow's Narn
regulars in Earhart's at 13:00** — because 13:00 is a Narn meal hour in `schedule.RHYTHMS` and the
station's restaurants were the only place a meal could be taken. A quarter of a million people
cannot lunch out; the restaurants would have to seat all of them three times a day.

**What constrained it.** `FACTIONS.md` §2.5 gives the Fresh Air Restaurant, Earhart's, the Eclipse
Café and the Zocalo real peak densities and busy meal windows, so the fraction cannot be near zero
or those windows never fill. Quarters must not be empty at meal times, so it cannot be near one.
It is a property of the person rather than of the meal, for INV-089's reason. Lurkers and refugees
are excluded outright: §3.4 says expired status is why they avoid readers, and a restaurant is a
reader.

**What would overturn it.** Any figure for how many quarters aboard have a galley, or any scene
establishing that station quarters have no cooking facilities at all — which would push this
toward 1.0 and is a real possibility on a station with centralised life support.

---

## INV-094 — Passenger jerk limit: 0.6 m/s³, and the anchor is the ramp time

`station/transit.py`, `JERK_M_S3`.

**What.** Every vehicle on the station ramps its acceleration at no more than 0.6 m/s³, so the
1.2 m/s² cruise acceleration takes **2.0 seconds** to arrive and 2.0 seconds to release.

**Why necessary.** The project had a cruise *acceleration* (`physics/core_shuttle.AxialShuttle`,
1.2 m/s²) and a *lateral* comfort bound (0.12 g) and no statement about how quickly either is
applied. Without a jerk limit the motion profile is two straight ramps meeting at a corner, which
is an infinite jerk at the midpoint of every journey — the thing that throws a standing passenger,
as distinct from the acceleration itself, which they can lean into.

**What constrained it.** The anchor is the **ramp time, not the figure**. A standing passenger who
feels a car move completes a voluntary stance shift in roughly a second; requiring the ramp to
occupy 2.0 s puts a full stance shift plus the same again of margin inside it. 1.2 / 2.0 = 0.6,
which lands in the middle of the 0.3–1.0 m/s³ band transit engineering uses, so the derivation and
the practice agree without either being fitted to the other. It is also the *only* new comfort
bound introduced: 0.12 g and 1.2 m/s² are both read back out of the modules that already own them,
and `transit._selftest` asserts the agreement through `inspect.signature`.

**What it changes.** It makes every ride longer, and that is the test that it is not decoration:
the guideway tram's 646.5 m leg takes 48.5 s against 46.4 s for a jerk-free profile. `transit.py`
asserts the jerk-limited profile is the *slower* of the two, so a regression that dropped the term
would fail rather than quietly speed the station up.

**What would overturn it.** A Season 2–3 frame of a passenger standing unsupported in a moving car
— whether grab poles are in use at the moment a car starts is direct evidence about this number.
`35a` shows stanchions but the car is not visibly accelerating.

---

## INV-095 — The guideway tram's five stops, and why five is forced

`station/transit.py`, `guideway_line()` / `stop_rule()`; `station/tram.py`, `service()`.

**What.** The drum guideway tram stops **five** times, evenly, at z = 3839, 4485.5, 5132, 5778.5
and 6425 — 646.5 m apart. Peak speed 26.68 m/s (96 km/h), leg 48.5 s, end to end 4 m 14 s.

**Why necessary.** `station/tram.py` built a 96 m vehicle, placed six of them on three guideways,
and said nothing about where they stop or how fast they go. `npc/navigation.py` models the *ground*
tram, the core shuttle and the spoke lifts and does not know this line exists — its docstring
asserts "the guideway tram runs along the axis where Coriolis is exactly zero and is fast" and
never gives it a number. A vehicle with no timetable is a prop.

**What constrained it — four things, and together they leave one answer.**

1. **Both termini are structural.** `interior.guideway_truss` runs the drum sector's full extent,
   so the line starts and ends at the end caps. Not a choice.
2. **A stop must land on the spoke crossing.** `interior.drum_spokes` puts its spokes at the
   sector's mid-z, and that is the only place in the drum where this line can interchange with the
   radial tubes or the core shuttle. With even spacing and both ends fixed, this forces an **odd**
   stop count.
3. **The catchment.** A stop is useful if you will walk to it, and five minutes is the standard
   planning figure. Stated as a *time*, it converts through the local gravity: at the drum floor's
   1.000 g the project's own `navigation.walk_speed` gives 1.494 m/s, so the reach is 448 m.
4. **Fewest stops that satisfy 1–3.** Three stops put 1,293 m between them, a 646 m walk, which
   fails the catchment. Five put 646.5 m between them, a 323 m walk, which passes.

Four stops would pass the catchment (862 m spacing, 431 m walk) and **miss the spoke crossing** —
which is exactly why constraint 2 is written down. `transit._selftest` runs both rejections: it
asserts three fails the catchment and that four does not contain mid-z. A rule whose rejections are
not run is not a rule.

**The speed is an output, not an input.** Nothing picks 26.68 m/s. Given 646.5 m, 1.2 m/s² and
INV-094's jerk limit, the fastest comfortable run accelerates until it must brake, and 26.68 m/s is
where that gets to. **Coriolis imposes no cap on this line at all**, because the motion is parallel
to the spin axis and ω × v is then identically zero — which is the whole reason an axial tram is
8.5× faster than the ring tram beside it.

**Cross-check that it is not absurd.** At 26.68 m/s a 7.2 × 8 m car section meets about 10.0 kN of
aerodynamic drag in the drum's air, or 268 kW at cruise — a normal tram motor. A metro runs 80–100
km/h between stops of this spacing.

**What would overturn it.** Any frame showing a tram stop, a platform, or a car stationary against
the drum's landscape; or a Season 2–3 line of dialogue giving a journey time inside the Garden.

---

## INV-096 — The ground tram's three stops are set by interchange, not by walking

`station/transit.py`, `ground_line()`.

**What.** The second, ground-level drum tram is a **ring** line at the floor radius with three
stops, one under each guideway, 582.9 m apart. Capped at 3.13 m/s.

**Why necessary.** `LOCATIONS.md` §9 records the ground tram as authority 1 (`29a` shows a
green-and-yellow car on an elevated track with its own canopy, sharing nothing with the white and
maroon guideway tram) and nothing else about it was ever specified.

**What constrained it.** Not the catchment — three stops on a 1,749 m ring give a 291 m walk, well
inside the 448 m reach, so catchment does not bind. What binds is **interchange**: the point of a
second system is to serve what the first cannot, so it must meet the first. `interior.SPOKE_COUNT`
is 3 and the guideways sit in the spoke planes, so there are exactly three places to meet, and the
stop count is read out of that constant rather than chosen.

**Its speed is not a choice either, and it is the interesting one.** This line runs *across* the
spin, so its Coriolis is radial and it changes what a passenger **weighs**. Holding that inside the
project's 0.12 g bound caps it at 3.13 m/s — 11.3 km/h, barely twice walking pace. That is why the
drum needs two tram systems rather than one fast one, and it is a consequence of the geometry, not
a design decision anybody made.

**What a passenger actually feels, and it is the best physics in the station.** At the cap, riding
**spinward** they weigh **1.1236 g** and riding **anti-spinward 0.8836 g** — a **0.2400 g swing,
27.2% heavier one way than the other, on the same seat in the same vehicle**. The swing is exactly
2× the Coriolis bound; the small `u²/r` term (0.0036 g) adds to *both* directions and so cancels
out of the difference. Is that uncomfortable? A ±12% weight change is roughly a normal lift on
Earth, so it is noticeable rather than unpleasant — but the *reason* it is only that is that the
cap was set to make it so, and a ring tram at 12 m/s would be at 0.46 g of Coriolis, which is not
survivable as a commute. So the answer to "is it uncomfortable" is: it is comfortable **because**
it is slow, and it is slow **because** it must be comfortable.

**AN OPEN QUESTION ABOUT THE BOUND ITSELF, recorded rather than resolved.** The 0.12 g figure was
set in `physics/core_shuttle.comfortable_duration` for a **lift**, where Coriolis is *tangential* —
an unexplained sideways shove, which is the least tolerable kind of acceleration. On this line the
same 0.12 g appears as a *weight change*, which humans tolerate far better; a lift on Earth does
0.12 g routinely and nobody notices. Applying one bound to both is therefore **over-conservative
for the ring tram**, possibly by 2–3×, and it is why this line is only twice walking pace. It is
not changed here, because `npc/navigation.py` applies the same bound to the same line and a
unilateral change would put two modules into disagreement about the same vehicle. **What would
settle it:** a decision to split the bound into a tangential (push) limit and a radial (weight)
limit, which is a one-line change in `core_shuttle` and a re-derivation here. Flagged for the
owner; it would roughly double the ground tram's speed and change no other system.

**What would overturn it.** Any frame showing the ground tram's track running lengthwise down the
drum rather than around it, which would make it a second axial line and remove the cap entirely.

---

## INV-097 — The core shuttle's stop spacing, and the tube stops 1,888 m short of it

`station/transit.py`, `core_shuttle_line()`; `station/core_tube.py`, `tube_coverage()`.

**What.** The core shuttle's **13 stops** are spread evenly over the run from Grey's aft face
(z 3397) to Blue's fore face (z 8047) — 4,650 m, so **387.5 m apart**. Peak speed 20.40 m/s
(73 km/h), leg 38.0 s, end to end 11 m 16 s, headway 3 m 52 s on six cars.

**What is sourced and what is not.** The stop *count* and the Blue-to-Grey run are authority 4 —
the fan source cited in `LOCATIONS.md` §9, already carried by `npc/navigation.CORE_SHUTTLE_STOPS`.
The **spacing is ours**: it is the run divided by twelve. The termini are read off the sector
extents rather than stated, so if C-003/C-004 ever move a sector face the line moves with it.

**What constrained the spacing.** Nothing but the two sourced numbers, which is why this entry is
separate from INV-095 — there the spacing is derived from a catchment and here it is arithmetic on
someone else's figure. Checked rather than assumed: every register place inside the run is within
half a spacing (194 m) of a stop, asserted in `transit._selftest` with a negative control that
thins the stop list and confirms the coverage check fires.

**THE GAP THIS FOUND, and it is a real one.** `core_tube.tube_span()` builds from one drum cap to
the other plus a 40 m overhang — z 3750.5 to 6513.5. The service runs 3397 to 8047. **The tube
covers 59% of the run**: 1,534 m is missing forward through Red and Blue and 354 m aft through
Grey. That is exactly the run `core_tube.py`'s own docstring quotes from the Security Manual
sectional schematic — "running the whole length of the drum *and on forward through Red and Blue*".
The geometry was built for the drum because the drum is what `interior.py` had, and nobody came
back for the rest. `tube_coverage()` measures it and the self-test asserts the built part contains
the whole drum while reporting the shortfall, deliberately without excusing it.

**And the aft half of the station has no transit at all.** The shuttle's aft terminus is Grey, so
Yellow's 3,397 m — 42% of the station's length — must be walked, which is 51 minutes at its 0.559 g
walking speed and is why an end-to-end trip is 1 h 07 m rather than the 20 minutes the shuttle
alone would suggest.

**What would overturn it.** Any frame or source establishing the shuttle's actual termini, a stop
count from a car display, or a wayfinding sign listing the line's stops. A shuttle-car display
would also close C-004, which is why `LOCATIONS.md` calls a lift display the single highest-value
missing reference in the project.

---

## INV-098 — Headway is derived from car count, and one of the four numbers is embarrassing

`station/transit.py`, `line_report()`.

**What.** Every line's headway is its **round trip divided by the cars on it**, and the mean wait
for a passenger who does not consult a timetable is half that. Guideway tram 4 m 34 s (2 cars per
guideway); core shuttle 3 m 52 s (6 cars); ground tram 2 m 38 s (4 cars); **spoke lifts 5 m 13 s
(one car per shaft)**.

**Why necessary.** A transit time that ignores headway is a lie: on the Blue-bays-to-Zocalo trip
the wait is 1 m 56 s against a 1 m 36 s ride, so omitting it would have understated the journey by
more than the riding takes.

**What constrained it.** The car counts are not invented here. `tram.CARS_ON_A_GUIDEWAY` is
`drum_trams`'s own `per_guideway` default — `transit._selftest` reads it back out of the signature
so the vehicle module and the timetable cannot disagree about how many cars exist — and the other
three are `navigation.CORE_SHUTTLE_CARS` / `GROUND_TRAM_CARS` / `SPOKE_LIFT_CARS`. The round trip
is the ride plus a `TRANSIT_DWELL_S` at each intermediate stop and two at the terminus.

**The finding, reported rather than tuned away.** One car per spoke gives a **5 m 13 s headway on
the only route between the drum floor and the axis**, so the mean wait to leave the Garden by spoke
is 2 m 37 s on top of a 2 m 17 s ride. That is the worst wait on the station and it is a statement
about how many cars the spokes need, not about the physics. The self-test asserts the spoke lift
*is* the worst wait and that it exceeds two minutes, so the number cannot be quietly improved
without the assertion noticing.

**What would overturn it.** Any frame showing more than one car in a spoke, or a queue at a lift
door long enough to imply a headway.

---

## INV-099 — Walking distance on the rim is Manhattan, not great-circle

`station/transit.py`, `walk_leg()` / `_sector_walk()`.

**What.** The distance between two places on the rim is the **axial run plus the arc**, and the
walk is timed sector by sector at each sector's own gravity rather than at one average speed.

**Why necessary.** Every journey time in the table rests on it, and both halves change the answer:
the hypotenuse would have understated C&C-to-Medlab by 26.5%, and a single 1.4 m/s walking speed
gives 95.8 minutes end to end against the 103.6 the station's own gravities produce.

**What constrained it.** Corridors in a concentrically decked cylinder run either along the axis
or around a ring — that is what `interior_kit` builds and what `central corridor.webp` shows — so a
diagonal is not walkable and the hypotenuse is not available. Speed comes from
`navigation.walk_speed`, which is the project's existing Froude-number relation, imported rather
than restated. Gravity varies from Yellow's 0.559 g to Grey's 1.693 g, a 3.0× range that changes
walking speed by 1.74×, so a single figure is wrong by minutes over a station-length walk.

**What would overturn it.** A deck plan showing diagonal or spiral circulation, which would make
the Manhattan figure an overestimate. It is deliberately the conservative reading: it can only
overstate a journey, never understate one.

---

## INV-100 — A radial lift shaft runs a bank of cars, sized to a two-dwell headway

`station/npc/navigation.py`, `shaft_cars()` / `SHAFT_TARGET_HEADWAY_S`.

**What.** Each of the three radial shafts in a sector runs **`round_trip / (2 × TRANSIT_DWELL_S)`
cars**, rounded to an integer and never fewer than one. That falls out per sector rather than being
tabulated: Grey's shaft spans 382 m and gets **10**, Red's 213 m gets **6**, Blue's 167 m gets **5**,
Yellow's 122 m gets **4**, Green's 29 m gets **2**. Mean wait lands between 16.9 s and 20.3 s
everywhere.

**Why necessary.** The graph had to price a wait for a lift and could not: `SPOKE_LIFT_CARS = 1`
covers the drum spokes, and nothing covered the sector shafts. Without a fleet the wait is one
car's whole round trip — 203 s in Grey, so a resident crossing three decks would spend three and a
half minutes at the doors of a shaft that 105 decks depend on.

**What constrained it.** `TRANSIT_DWELL_S = 20 s` is already this project's measure of how long a
door stands open with people moving through it, so a headway of two dwells is exactly the point at
which **boarding rather than waiting becomes the cost of using the thing** — tighten it further and
the queue at the door, not the timetable, is what you are waiting for. It is a ratio against a
number already in the file rather than a second invented constant, and it is the only such target
available: nothing in the show counts lift cars. The round trip itself is not invented —
`_lift_headway_s` is 2 × `lift_ride_s(span)` + 2 × dwell, and `lift_ride_s` is the Coriolis-capped
smoothstep that `physics/core_shuttle.comfortable_duration()` independently reproduces.

**What would overturn it.** Any frame showing a lift lobby, because **the number of doors in it IS
the bank**. A single-door lobby on a main deck would put the figure back to one or two and roughly
double every radial wait in the station.

---

## INV-101 — A vehicle is ridden through its intermediate stops, not re-boarded at each

`station/npc/navigation.py`, `_car_layer()` / `NavGraph.add_board()` / `NavGraph.add_ride()`.

**What.** Every scheduled line — the radial shafts, the core shuttle, the drum guideway trams and
the two circumferential ground trams — carries a parallel chain of nodes that live **inside the
car**. Boarding costs **half a wait and half a dwell in each direction**; riding between adjacent
stops costs **ride time alone**. A one-way journey traverses the boarding link exactly twice, so it
pays one whole wait and one whole dwell however many stops it passes through.

**Why necessary.** It is not a refinement, it is a defect fix, and the defect was large. Adjacent
stops were joined directly, so each carried its own wait and its own dwell and the router made a
passenger get out and queue again at every intermediate stop. Measured on Grey's shaft: **72.9
minutes to ride 382 m that takes 3.0 minutes**, a factor of 24. Over a sample of 120 residents the
median home-to-work commute was **44.1 minutes and the worst 110.5**; with the car layer they are
**13.5 and 24.8**. Nothing was wrong with any speed, distance or headway in the module — the ride
times were right the whole time. What was wrong was that the graph had no way to express *being
aboard*.

**What constrained it.** The half-and-half split is arithmetic rather than a fudge: it is the only
division that leaves a **one-stop hop costing exactly what it cost before**, so the change cannot
be a general speed-up hiding a modelling error. `lift_ride_s` is linear in distance
(1.5·dr/v_cap), so summing per-deck rides along the car chain equals one express ride **exactly** —
segmenting the layer introduces no approximation at all. The model is a non-stop express: a car
that halts for another passenger is not charged to this one, which is the optimistic reading and is
stated as such.

**What would overturn it.** A show reference to lift or shuttle journeys being slower than
end-to-end ride time, which would mean intermediate dwells are charged to the through passenger and
would add ~20 s per intervening stop.

---

## INV-102 — A figure has a minimum standing gravity, measured off its own feet

`station/populace.py`, `_stand_min_g()`.

**What.** Below **0.075 g** for a nominal human, a body is posed with `glide_clip` rather than
`idle_clip` or `sit_clip`. The threshold is not a constant: it is computed per figure as
`sway_amp_f · lx · G0 / foot_x`, where `lx` is the hip's own x offset and `foot_x` the outermost
vertex of the feet, both read off `animation.rig()`.

**Why necessary.** `animation.idle_clip` scales its lateral sway by `G0 / g` and has **no lower
bound at all** — nothing had ever asked it for a pose in low gravity. At 0.04 g it leans a human
0.52 m off centre and lifts the feet 25 mm clear of the deck: not a stance, a person falling over.
One register place is below the bound (`mainstage_node`, in the 18.3 m spine at z = 3000, where the
spin gives 0.022 g), and every crewman standing in it would have read as mid-collapse.

**What constrained it.** A standing pose is holdable exactly while the centre of mass stays inside
the **base of support**, and for a standing figure that is the outermost point of its own feet.
Setting the sway equal to it is the definition of the boundary, not a tolerance chosen around it.
Both terms are measured off the rig rather than tabulated, so a broad-stanced individual stays on
their feet in lower gravity than a narrow one — which is also true of people. The clip used below
the bound is not invented either: `glide_clip` already existed because Kosh's column plan has no
legs.

**What would overturn it.** A frame showing crew standing normally in the spine or in a docking
bay's zero-g section, which would mean magnetic boots or handrails are doing the work and the pose
should be a braced stand rather than a drift.
## INV-103 — The docking bay mouths face FORE, and the hull is cut where they leave it

`station/aperture.py`, `station/docking_bay.py::mouth_z_m`, `station/generate_hull.py::build`.

**What.** Each of the 24 docking bays opens through a **42.0 m × 22.2 m rectangular aperture in
the docking sphere's forward taper**, at the bay's own angle, spanning z 7,207.7 – 7,245.1 m. The
mouth plane itself is at **z = 7,185 m**, so the hull overhangs the mouth by 22.7 m at the deck
and 60.1 m at the roof, and the opening is reached down a throat of that depth.

**Why necessary.** `docs/volume-audit.md` §5.1 found that `generate_hull` lathed a closed surface
and the bays therefore had **no exterior at all** — hard rule 4 running the other way. A bay you
can stand in behind a hull with no hole in it is the same defect as hand-authored hull geometry,
and it is worse for being invisible: every gate in the project was green.

**What constrained it, and this is a derivation rather than a choice.** The bay's mouth is
**perpendicular to the station axis** — `docking_bay.docking_bay()` authors +Z running into the
bay from a mouth at local z = 0, and `place_bay` maps local up to radially inward. A rectangle
perpendicular to the axis cannot be a hole in a cylinder parallel to it, so the aperture is not
where the bay is; it is where the bay's mouth *points*. Fore or aft is then decided by the hull:

| mouth faces | hull at the mouth plane | does the swept prism ever meet the hull? |
|---|---|---|
| **fore**, z 7,185 | 266.4 m, outboard of the mouth's 232.0–254.2 m band | **yes** — the taper falls through 254.2 m at z 7,207.7 and 232.0 m at z 7,245.1 |
| aft, z 7,045 | 166.2 m, already inboard of the whole band | **no** — the bay's aft end is in vacuum before it starts |

Only one of the two produces an aperture, so the mouths face fore. Everything else is read from
somewhere that already held it: the count and pitch from `docking_bay.BAY_COUNT`, the width from
`BAY_W_M` (42 m, itself INV-022), the radial band from the deck radius `bay_radius()` minus the
arched ceiling `BAY_H_M + 0.1 × BAY_W_M`, the mouth's z from
`directory.PLACES["docking_bays"]`'s own footprint, and the crossings from
`station/schema/radius_profile.json`. Nothing here is a literal.

It also agrees with the traffic model that was already written down:
`docs/gazetteer/TRAFFIC-AND-CUSTOMS.md` §4.4 has C&C, inside Observation Dome 1 at z 7,000–7,240,
looking *"out along the approach vector for the docking bays"* (authority 4) — which is the
direction these mouths face, from a dome that sits directly over them.

**Two things it does NOT settle, stated because they are live:**

- `reference/03-sector-blue/dock.webp` (authority 1) shows *"the far side of the station visible
  beyond"* the mouth, which reads more like an enclosed cavity than open space. The fore-facing
  mouth looks out at the deflector spike's root, 200 m away and 40 m across the opening, which is
  *a* reading of that frame but not the only one. **Overturned by** any frame showing what is
  actually outside a bay mouth, or any exterior frame of the docking section with the bays visible.
- A ship leaving a bay along the axis at radius 232–237 m re-enters the hull at z 7,367–7,416 m,
  where the deflector spike's root swells back out to 237.2 m. The outer 17 m of the mouth
  (r 237–254) is clear; the inner 5 m is not. That is a **flight-path** finding, not a geometry
  one, and it belongs to whoever writes the approach corridors.

**A second, smaller extrapolation inside the same build.** The mouth surround —
`docking_bay_lip` — is **one girder deep, 2.4 m**, taken from `docking_bay.GIRDER_D_M` rather than
chosen, on the reasoning that the member framing a mouth is the member that spans the bay.
`dock.webp` puts a yellow-and-black chevron on every deck edge in the bay at authority 1, and this
band is where that material lands on the exterior. **Overturned by** any frame showing the outside
of a bay mouth's surround.

**And the band the mouths cut through carries no plate seams.** `hull_plating` moves every hull
vertex radially by up to ±1.3 m and steps between plate rows, so across one row boundary the hull
can move 2.6 m — while the forward taper only falls about 1.4 m per ring. Measured: at
z 7,224.7 → 7,228.8 the profile falls 244.7 → 243.3 m and the *plated* hull rises 243.723 →
244.100 m, which folded 24 throat walls back on themselves. So z 7,207.7 – 7,245.1 is lathed
smooth: an opening is a machined collar, and a collar is not plate. **Overturned by** any frame
showing plate seams running through a bay mouth.
## INV-104 — Ten interiors for exterior systems that had none

`station/directory.py` (ten new PLACES rows), `station/rooms.py` (`PLACE_FIXTURES`,
`PLACE_CEILING`, `PLACE_LIGHTS`), `docs/gazetteer/LOCATIONS.md` (ten new rows).

**What.** Ten rooms, each placed behind an exterior system the schema builds and the register
had left with nothing inside it: a reactor hall and a fuel bunkerage inside `primary_fusion_reactor`,
a coolant manifold gallery wrapping it, a generator torus hall, a heat exchanger hall, a deep
space comms operations room at the pylon root, a cargo transfer deck under the six dorsal cargo
modules, a mooring clamp gallery, an EVA airlock and suit room, and a defence grid fire control.
Every dimension in them — footprint, floor radius, ceiling, and the size of every piece of
machinery — is extrapolation.

**Why necessary.** `docs/volume-audit.md` matched all 28 `exterior_systems` against the interior
each implies and found **7 matched, 21 not**: eleven with no interior at all, five addressed
hundreds or thousands of metres from the geometry the same schema builds, five with a function
somewhere in the register and nothing placed against the system. The owner's session-3y
instruction is that *"everything on the outside has a function on the inside … it can't be a
facade"*, and a 0.0299 km³ reactor feature holding zero addressed places is exactly a facade.
Hard rule 1 forbids leaving the hole: the answer is to extrapolate in style, mark it authority 5,
and say what would overturn it.

**What constrained it.** Not much fixes these, and the ones that do are stated per room in
`directory.py`'s notes. The constraints that applied to all ten:

* **The z came from the schema, not from the register.** Each room sits inside the z extent of
  the component or longitudinal feature it explains — `components.build_all` for the built ones,
  `longitudinal.features` for the lathed ones. `comms_operations` is at the pylon root **as the
  schema builds it** (z 2,515–2,988) rather than at the register's `comms_grid`, which is 5,148 m
  away; that position is contested three ways and volume-audit.md §6 says so.
* **The radius is the outermost deck the pressure hull leaves at that z.** Verified at 401
  samples across each footprint span against `core_hull_profile(z) − HULL_SKIN_M`, on the UNCUT
  deck stack — the one `rooms.room_extent_m` and `interior.ring_cells` actually build at, because
  neither takes `z_m`. Margins run from **+1.0 m** (`generator_hall`) to **+130 m**
  (`coolant_gallery`); `cargo_transfer_deck` at +1.4 m is the thinnest of the wide ones.
* **The ring index had to mean one shell along the whole room.** `ring_radii(z_m=)` drops a ring
  the hull has closed, so "ring 1" is the 93.3–127.5 m shell where four stacks survive and the
  59.1–93.3 m shell where three do. Four of the audit's rows straddled such a boundary and were
  shrunk or moved. `coolant_gallery` moved furthest: at the audit's z 450–950 yellow carries
  **one** deck stack and ring 3 does not exist at all.
* **The deck NUMBER had to be one its ring already carries.** `deck.deck_index` ranks the
  distinct deck numbers on a ring when they exceed the stack depth, so a new number silently
  re-ranks every existing place on that ring. `heat_exchanger_hall` took deck 4 rather than the
  audit's deck 3 for that reason alone.
* **Machinery size is bounded by three things the self-test measures rather than asserts in
  prose:** each piece must fit under its room's ceiling, the room must stay crossable by a 0.9 m
  walker, and no two solids may share a cubic metre. A fourth is arithmetic: `rooms.build`
  repeats a fixture in slots of `room_len / int(room_len / FIXTURE_PITCH_M)`, so nothing may be
  wider than about 4.2 m along the room or it overlaps its own next instance.
* **The fixture NAMES are constrained by material coverage, not by taste.** `materials.resolve`
  matches longest bind fragment, `test_materials_layer3.py` asserts every emitted group resolves,
  and materials.py was not this session's file — so the natural names (`fix_containment_vessel`,
  `fix_suit_locker_bank`) resolve to None and cannot ship. The rule adopted: the bound fragment
  names the MATERIAL, the qualifier names the OBJECT, and the vocabulary is `station/plant.py`'s
  own. The same constraint decided two `interacts`: 33 of the 99 entries in `rooms.PROPS` have no
  bind, including `airlock_door` and `locker`, so the EVA lock's outer door is a `blast_door`.
* **The coolant gallery's 3.20 m ceiling is a correction, not a choice.** It is `industrial` for
  its shell and materials, and `industrial` is 7.5 m, which is a foundry. The audit calls the
  gallery *"a crawlway, not a corridor"* at 0.173 g. The same render that showed the height wrong
  showed the lamps wrong with it: `light_highbay` is measured at an **18 m mount** and its energy
  does not scale with the room, so a 3.2 m gallery came back with the whole ceiling clipped
  white. It is relamped to `light_ceiling_batten`, which is already the 3.6 m-pitch fitting.

**What would overturn it.** Any frame or print source showing a Babylon 5 reactor hall, coolant
gallery, generator hall, heat exchanger hall, cargo transfer deck, mooring gallery, EVA lock or
gunnery control — none is held. Three sharper ones: a frame of the comms pylons against a
recognisable hull section would move `comms_operations` (or confirm it); a resolution of C-004's
level numbering would replace every deck index here; and a decision on the `decks_in_ring`
z-clipping that volume-audit.md §7.1 proposes would change every floor radius, because these are
the outermost decks the hull leaves and they are the first ones such a clip would touch.

---

## INV-105 — A deck's shipped primitive count, and why it is a regression bound

`station/budget.py`, `BUDGETS["deck_primitives"] = 600`, and `populace._by_material`.

**What.** An assembled deck's `.glb` must contain no more than **600 primitives**, measured by
parsing the shipped file rather than by counting anything on the Python side.

**Why necessary.** The draw-call gate that existed measured the **wrong artefact** and had done
since it was written: it counts feature groups in the hull manifest — 41 of 64 — which is right
for the exterior, where a feature group is a lathe or a component. It is not what the exporter
writes. `export_gltf` emits **one mesh, one node and one primitive per OBJ group**, so the number
a renderer sees is the shipped file's group count. Measured on `blue/0/0` the first time anyone
looked: **1,262 primitives, 1,052 of them people** — twelve per inhabitant, because `body.py` tags
twelve parts. `schedule.NPC_BUDGET["max_draw_calls"]` is 32.

**What constrained it, and what did not.** It is **not** a frame draw-call limit and does not
pretend to be. A deck `.glb` is the whole 345° ring and `walk.gd` loads it whole, but a corridor's
sight line is bounded at 66 m (`populace.corridor_sight_m`), which on a 211 m radius is 18° — about
5% of the ring in frame at once, plus what shows through the doors. The in-frame figure is an order
below this. What 600 **is**: above the merged measurement of 376 with room for the station to grow
busier, and far below the 1,262 that was wrong. `check`'s `when=` states the distance in units of
the content — about 250 more inhabitants on one deck, or a body emitting its parts unmerged again.

The fix that made 376 possible is `populace._by_material`: the twelve part names exist so each
binds its own material, and the materials are only ever two or three (skin, hair or crest, suit).
Merging **runs** of the same material family — never reordering, so no triangle moves — drops a
human at lod 4 from twelve spans to one and a Minbari to two, with every material distinction
intact. The family is read off `body.py`'s own naming (the first two tokens of a part name **are**
the bind fragment) rather than from `materials.py`'s table, so the two cannot drift; if they ever
did, `test_materials_layer3.py`'s coverage gate fails, because it resolves every emitted group.

**Negative control, run:** with the merge patched out and the deck rebuilt, the gate reads
**1,262 / 600 FAIL**; restored, **376 / 600 PASS**. `walkable.py --deck blue/0/0` passes either
way and the inhabitants still turn to look, so the merge costs no behaviour.

**What would overturn it.** A MultiMesh or skinned-crowd pipeline, which would make per-person
primitives the wrong unit entirely — a thousand instances of one mesh is one draw call, and this
bound would then be measuring something that no longer costs anything.

---

## INV-106 — An inhabitant's collision capsule, measured off their own body

`station/populace.py`, `body_capsule()`; `godot/scripts/npc.gd`, `_give_body()`.

**What.** Every inhabitant carries a capsule in the actor record: **radius = the widest horizontal
extent of their own posed mesh about its own vertical axis**, height = that mesh's height. A human
measures **0.269 m**, a Narn 0.295, a Minbari 0.276, a Pak'ma'ra 0.312, a Vorlon in an encounter
suit 0.414. It is built at runtime on a node that follows the person, not baked into the deck.

**Why necessary.** A player walked through all 147 of them. `walkable.py --deck blue/0/0 --bump`
measured it: steering straight at a named resident the body reached **0.03 m** — through them.

**Why it is NOT in the static collision, which is the part worth keeping.** `rooms.is_solid`
excludes every `npc_` group deliberately, and the exclusion is right: static collision is generated
**once**, so an inhabitant baked into it is a permanent statue — a person you bump into and who
never moves is worse than one you walk through, and it is permanent. That function's comment ends
"NPCs get their own capsules when they get their own movement"; this is that capsule.

**What constrained it.** The **widest** extent rather than the chest — a human is 0.269 m at the
arms against 0.206 at the chest, and the arms are exactly what a player would otherwise clip
through. Measured per individual off the mesh already in hand, so a Vorlon's suit and a Narn's
build differ without a table saying so, which is hard rule 4 applied to a body. It does not close
the corridor: 0.269 m against the collision shell's own 1.081 m half-width leaves 0.81 m either
side of somebody standing on the centreline, and the deck's walk gate still passes at 6.3 m → 0.04 m.

**Negative control, run, and it is now a CI step:** with `--no-npc-collision` the body reaches
**0.03 m** of Amis Keffer and walks through them; with the capsule on it is stopped **0.71 m**
away, which is their 0.36 m plus the player capsule's own. `BUMP_MARGIN_M = 0.25` is half the
smallest true separation and well outside the ~0.05 m the walker's stopping distance varies by
between runs.

**What would overturn it.** A crowd system with its own avoidance, which would want a smaller
physical capsule and a larger steering radius — the two are different numbers and this is only the
first.

## INV-110 — A bespoke room's doorway is 2.20 m wide and 2.40 m high, derived from the assembler's own probe

`station/bespoke.py`, `DOOR_HALF_W_M` / `DOOR_H_M` / `doorway_wall()`; applied in
`station/hospitality.py` and `station/zocalo.py`.

**What.** Every module that builds a named place in its own frame — the Zocalo, a bar, a docking
bay, C&C — now leaves a clear aperture **2.20 m wide by 2.40 m high** in the face that a ring
corridor arrives at, cut as three closed plates round the hole rather than as a hole punched
through one solid.

**Why necessary.** Not one of the nine bespoke modules authored a doorway, because each was
written to be *rendered* on its own, before `station/deck.py` could assemble one onto a ring.
`deck.build_deck` measures the mouth with `_mouth_clear` and falls back to a generic store bay when
it is walled, so as of session 3z seven module-owned places assembled as grey boxes for this reason
alone: `cnc`, `council_chamber`, `customs_south`, `docking_bays`, `bar_unnamed`, `eclipse_cafe` and
`happy_daze`. A bar with four sealed walls is not a bar.

**What constrained it.** Three measurements, none of them a preference:

* the corridor's pressure door is **1.50 × 2.10 m** (`interior_kit.PROVISIONAL`), so the leaf
  itself wants 0.75 m of half-width;
* `deck._mouth_clear`, which is the assembler's own acceptance test and therefore the thing the
  aperture has to satisfy, probes at **x = dx ± 0.60 m** in five steps and at 0.35/0.60/0.85 of the
  door height — so the highest probe is **1.785 m**;
* `dx` is how far the corridor's bay division moved the door off the room's own centre. Measured
  across every module-owned place the assembler places, **max |dx| = 0.40 m**
  (`customs/arrival_concourse`); `deck.deck_plan.rank`'s phase sweep already drives most to 0.00.

0.60 + 0.40 = 1.00 m is what every probe needs to miss, and 1.10 m of half-width covers that and
the leaf with 0.10 m to spare. 2.40 m of height clears the 1.785 m probe and the 2.10 m leaf and
reads as a door rather than a slot. The three-plate construction is not a taste call either:
`quarters.unit` already records the rule — *"built as plates around the volume, never as a solid
with a hole — the mistake command_control.py shipped when it sealed its own window inside the
wall"* — and here it also keeps the surface closed, where a boolean would leave an unrimmed
aperture facing the one place on the station a player is guaranteed to be looking at.

**What would overturn it.** A corridor door wider than 1.50 m; a change to `_mouth_clear`'s probe
span; or a bay division that lets |dx| exceed 0.70 m. All three are asserted against in
`bespoke._selftest`, which measures the narrowest doorway on the station every run (currently
`qtr_civilian` at 1.70 m) and fails if any composed room's aperture drops below the corridor's own
leaf width — so this number cannot drift silently.

## INV-111 — A doorway keeps a 2.20 × 2.00 m approach zone clear of furniture and of people

`station/bespoke.py`, `APPROACH_DEPTH_M`, and the span filter in `compose()`.

**What.** Inside a composed bespoke room, no piece of `dressing` furniture and no `populace`
inhabitant may stand within **1.10 m either side of the doorway and 2.00 m in from the near face**.
Whole pieces are dropped, never clipped, and a dropped person is dropped from the cast list as well
as from the mesh.

**Why necessary.** Cutting the hole is only half of it. `dressing.dress` fills a room from its
walls inward and its circulation rule reserves a band down the room's **long** axis only —
`abs(cx) - sw/2 < lane_hw` — which says nothing about the **end** wall, and the end wall is the one
the corridor's door is in. Measured this session, three places had an **open shell and a walled
composition**: `cnc`, `council_chamber` and `customs_south` each built a clear mouth and then put a
run of lockers across it. The room the player arrives at is furnished into a wall.

`dress` cannot be asked to fix this: it takes a room's dimensions and knows nothing about where a
corridor met it, and that ignorance is exactly the property that lets it be composed with a bespoke
shell in the first place. So the pieces are dropped after they are built, in the shell's own frame,
which is the only frame in which the aperture's position is known.

**What constrained it.** The half-width is INV-110's, because a doorway you can reach and cannot
walk through is the same defect one step further in. The depth is the argument: `_mouth_clear` only
looks **1.2 m** in, so 1.2 m would satisfy the gate and still leave a crate where the player's
second step lands. The character capsule is **0.35 m** in radius (`station/collision.py`) and a
stride is about 0.75 m, so a body needs roughly 1.5 m past the jamb to be standing *in* the room
rather than in its doorway; 2.00 m is that plus the same 0.5 m of slack the aperture gets.

**What would overturn it.** A change to the capsule radius, or a room whose declared function puts
something at the door on purpose — a customs desk, a maître d' stand, a security checkpoint. The
second is likely and is the reason `compose` takes `door_at` as a parameter rather than reading a
constant: a caller that knows better can say so.

## INV-112 — Local x = 0 in a bespoke room is a DOORWAY, not a centre, and it is measured

`station/bespoke.py`, `near_face_opening()`, used by `room_shell()`.

**What.** When a bespoke module's geometry is recentred onto a ring, the x it is centred on is the
middle of the widest **way in** through its near face — a run of x that is unobstructed at the
corridor's own three probe heights *and* has floor under it — rather than the middle of its
bounding box.

**Why necessary.** `deck._place_local` maps a room's local x = 0 onto the place's own bearing,
which is precisely where `deck_plan` puts the corridor's door. So local x = 0 is not a centre, it
is a doorway, and the bounding box coincides with it only when a module happens to be symmetric.
Two are not, and both were wrong on the shipped build:

* **`alien_sector.gallery`** is a 4.2 m corridor with its quarters hung off the left wall out to
  x = −4.85, so its bounding-box centre is **4.66 m** off the corridor. Measured: with bbox
  centring there is **no floor at all** under the doorway — the door opened onto the 3 m of empty
  air outboard of the gallery wall. `_mouth_clear` reported that as OPEN, because nothing is in the
  way of a probe cast into a void. It is the clearest false pass this project has found.
* **`quarters.run`** is a row of identical cells whose doorways are 4.1 m apart. On four of the
  seven quarters classes the bounding-box centre lands on the wall between two cells;
  `qtr_command` and `qtr_civilian` both measure WALLED with bbox centring and OPEN with this.

**What constrained it.** The obstruction test uses `deck._mouth_clear`'s own **1.2 m** band and its
own three probe heights, so the two agree by construction rather than by being kept in step. The
floor test uses INV-111's **2.00 m**, because a body steps *through* the aperture and lands past it
— `council_chamber` has no floor whatever in the first 1.2 m, its deck starting 1.42 m in behind
the gallery step, and the narrower band called a chamber with a 22 m floor unenterable. Ties are
broken toward the origin, which is what makes the operation a **fixed point**: `room_shell` shifts
by the answer and `_selftest` re-measures and asserts the answer is now zero. With "widest" alone
that round trip does not close, because six identical cells are identical to the millimetre and the
sample grid lands differently once the mesh has moved.

**What would overturn it.** A module whose near face has several equally good doorways and a
*reason* to prefer one — a Zocalo whose concourse should meet the corridor at a named entrance
rather than at whichever gap is widest. That is a layout decision and this is a measurement; the
measurement is the right default and the wrong override.
## INV-130 — Fifteen machines, so that a named object is not a box primitive

`station/dressing.py` (the MACHINERY section: `_tube`, `_dome`, `_perim_band`, `_face_strip`,
`_Parts`, the fifteen `_m_*` builders, `machine`, `machine_bounds_ok`), `station/rooms.py`
(`MACHINE_KIND`, `_fixture`, `machine_escapes`), `station/density.py` (`machinery_rows`,
`--machinery`).

**What.** Every one of the 45 fixture names in `rooms.FIXTURES` and `rooms.PLACE_FIXTURES` is
now built by one of fifteen parametric machines — vessel, furnace, drum, rack, cabinet,
pipe_bank, duct, crane, screen, gantry, console, skid, reel, block, kerb — instead of by a single
call to `_box`. A vessel is a lathe barrel with a domed head, girth flanges, lagging strakes, a
standoff skirt on legs, a bolted manway, radial pipe stubs turning down through elbows, a valve,
a gauge plate, a ladder, an access platform and a hazard band. Every proportion is a RATIO of the
box the fixture already declared, so the same machine in a 3.4 m lock and in a 7.5 m reactor hall
is one object at two sizes rather than two objects. Nothing here traces to a source: the
reference set holds no view of a Babylon 5 machine space at all
(`reference/08-sector-yellow-engineering/` is empty, and INV-104 says the same in its own words).

**Why necessary.** `docs/aaa-scorecard.json` scored `generated_rooms` at CRAFT 1, whose written
descriptor is *"a box primitive standing in for a named object"*, across 58% of the station's
locations. It was literally accurate: a "fusion containment vessel" was a rectangular pier 4 m
across and a "fabrication furnace" was a 2.4 x 2.4 x 4.6 m slab. This is the same defect
CLAUDE.md records under "LAYER 2 WAS UNDER-SPECIFIED", one object smaller — and it survived the
fix for that one, because `density.py` scores a WHOLE LOCATION and 123 of 128 locations passed it
with every machine in the station still a box.

**What constrained it.**
* **The box the fixture already declared.** No part may leave it. That is not tidiness: every
  walkability, collision and interpenetration rule in `rooms.py` reads the fixture's AABB
  (`walkable`, `standpoint`, `_solid_boxes`, `collision.prop_boxes`), so a machine that stays
  inside it cannot make a walkable room impassable. `rooms.machine_escapes` asserts it on every
  instance in every location; `dressing._selftest` asserts it per kind at the SMALLEST declared
  size that uses it. It fired four times on real content after passing on probe boxes.
* **Closed, manifold and outward-wound.** A hole and an inside-out face both render as the
  background. Each kind is measured with `interior_kit.boundary_edges` and signed volume. Three
  defects came out of that: a domed head whose last latitude ring collapsed onto the pole
  (30 non-manifold edges a vessel), a perimeter band whose four members shared their corner posts
  (36 a block), and a stacked-course construction that buried 622.7 m2 of surface inside a mass
  whose outside is 82 m2.
* **Line density has to be spent where it can be SEEN.** A proud band built as one slab spanning
  a body's full depth carries ten times the surface for the same visible line, so bands are four
  thin members (`_perim_band`) and joints are single-face strips (`_face_strip`). This is session
  3x's `portal_frame` finding — *"coincident faces are geometry nobody can see"* — with the trade
  the other way round: four times the triangles for a tenth of the area.
* **The group names are constrained by material coverage, exactly as INV-104's were.** The bound
  fragment names the MATERIAL and the `_mp_` infix marks a machine part, so `fix_mp_plant_frame`
  takes `plant_frame` -> `steel_gantry_oxide` with no edit to `materials.py`. Nine part names and
  no more: each distinct name is a draw call in `budget.py`'s `draw calls, whole frame`, which is
  already over at 1,303 of 1,041.
* **The vessel barrel is 72% of its declared footprint, not 93%.** The remaining quarter is the
  plumbing. A vessel drawn to the edge of its own box has nowhere to put a stub, a ladder or a
  platform, and the first version pushed all three 0.75 m outside it. The declared 4.00 m
  footprint is the machine PLUS its pipework, which is what a real one's footprint is.

**What would overturn it.** Any frame or print source showing a Babylon 5 plant room, reactor
hall, foundry, medlab equipment gantry or market stall frame — none is held. More narrowly: a
frame establishing whether station machinery is CLAD (lagged, banded, smooth) or EXPOSED (open
frames, visible mechanism) would decide the vessel and the cabinet at once, and they are the two
kinds that carry most of the station's fixture instances.

---

## INV-131 — And the declared props are boxes too

`station/rooms.py` (`PROP_KIND`, `_fixture`'s `prefix` argument).

**What.** 92 of the 96 entries in `rooms.PROPS` are routed through the same fifteen machines: a
counter has a kick recess, a nosed top and a panelled front; a door leaf has a reveal built as
four members, a kick plate, a vision panel, a handle and ribs; a bed has a base, a sectioned
deck, side rails and a head unit; a wall terminal has a housing, a bezel, a screen and a keypad.
Four are still a plain box and the list is printed by `rooms._selftest` rather than tolerated
silently: `deck_marking` (10 mm tall), `level_plaque` (30 mm), `path` (40 mm) and anything else
whose smallest declared dimension is under `MACHINE_MIN_M`.

**Why necessary.** With every FIXTURE articulated, `density.py --machinery` still failed the
medlab at 0.75 of its own shell, because a medlab is one gantry (built) plus a diagnostic bed, a
medcabinet, an isolation door and a monitor wall (four slabs). `rooms.PROPS`' own comment says it
outright — *"(width, depth, height, mount)"* — a prop IS a box. `interacts` is what a player can
USE, so these are the objects a player is standing closest to at the moment they use them.

**What constrained it.** The same three as INV-130, plus the prefix: a machine part inherits
`prop_` from its parent because `budget.klass_of` splits its report on exactly that prefix, and a
part of a prop counted as a fixture would move a budget line that is already failing.

**What would overturn it.** The same frames. Additionally, `docs/MASTER-PLAN.md` §3.2 argues
props should be placed against what the simulation needs rather than guessed; when the verb set
exists, a prop's SHAPE may have to follow its behaviour, and this table is the thing that changes.

---

## INV-132 — The furniture goes through the same kit as the machinery

`station/dressing.py` (`_table`, `_locker`, `_console`, `_shelf`, `_crate` now call `machine`).

**What.** The five furniture builders that stand up and read at a distance are the machine kit's
counter, cabinet, console, rack and crate. `_chair`, `_bin` and `_drum_can` are NOT routed: they
are already legs-and-a-back rather than boxes, and a hospitality room carries four chairs per ten
metres of wall, so a cabinet's triangle count on each would buy a silhouette nobody sees.

**Why necessary.** Measured, not assumed. A ray cast across the medlab's half-distance frame
after INV-130 lands on `dress_top` — the locker body — 27 times out of 119, more than any other
group and more than the articulated gantry standing beside it. The fixtures and the declared
props had been raised and the FURNITURE was still the flattest thing in the room.

**What constrained it.** Two invariants inside `dressing.py` had to change because spans now
NEST, and both changes are the correction `rooms._selftest` already carries: "every triangle is
grouped" became a coverage test rather than a sum, and `_surfaces_of` skips part spans, because
the outer span already sees every horizontal face and counting the parts as well puts two mugs on
every shelf. The cabinet additionally gained corner posts and bands on all four faces: the doors
are on one face chosen per instance, and a cabinet articulated on one face only is a slab from
the other three — which is what the medlab frame showed.

**What would overturn it.** A frame establishing what Babylon 5 station furniture actually looks
like. `reference/10-interiors-generic-kit/` shows corridors and a garden terrace, not a room's
casework.

---

## INV-133 — The crowd update rate, and the walk gate's real cost

`godot/scripts/npc.gd`, `crowd_hz = 10.0`; `station/walkable.py`, `CROWD_TRAVEL_MIN_M = 500`.

**What.** The corridor crowd's transforms are rewritten at **10 Hz**, not on every physics frame.
And `deck_verdict` requires a deck with a cast list to report `noticed` — a run that does not is a
failure, not a pass.

**Why necessary.** At 60 Hz every rewrite re-uploads each MultiMesh's whole instance buffer. At
10 Hz a walker moves **0.145 m** between updates — under the 0.22 m grid tile they are stepping on,
and a tenth of the 1.45 m stride the pose is showing — so nothing a player can resolve is dropped.

**And the measurement that made the whole thing legible, because three wrong answers were believed
first.** The walk gate had gone from **10.2 s to over 200 s** for 120 physics frames. Blamed in
turn, and all three wrong: the instanced crowd (an A/B timed out identically with it off), the
collision capsules (`--no-npc-collision` changed nothing), and `npc.gd`'s per-frame transform loop
(an early-out changed nothing). The cause was a **parse error**: `for w in _walkers` over an
untyped `Array` makes `w` a Variant, so `var d := w.omega * delta` could not infer its type, the
script failed to load, and every call from `walk.gd` threw — **23,933 stack traces to stdout**.
With `_walkers: Array[Walker]` the gate is **10.2 s with people on, the same as with them off**.

**What constrained the travel bar.** 134 walkers at their own gaits' 1.45 m/s over 1,800 frames at
1/60 s predicts **5,800 m** between them. Measured: **5,966 m** — a derivation confirmed by
measurement to 3%. The bar sits at 500, a tenth of it, so only a crowd that has genuinely stopped
can fail it.

**What would overturn it.** A profile on the target card showing the buffer upload is cheap enough
to run at frame rate, which would let the crowd move at 60 Hz and remove one approximation.

---

**And the process finding, which is the reusable half.** The NPC assertions in `deck_verdict` were
all guarded by `if "noticed" in d`. When `npc.gd` stopped loading, the tokens simply stopped
appearing and **every deck went on passing** — for six runs, while nobody on the station existed at
runtime. *A gate that disappears when the thing it tests is broken is worse than no gate, because
it prints PASS.* It now fails, and its negative control is run at unit level in one second rather
than through a Godot session that the very defect makes too slow to finish.

---

## INV-134 — A composed room's collision is its dressing, not its whole mesh

`station/deck.py`, `room_geometry()` and `_dress_solid()`.

**What.** One function decides bespoke-versus-generic for a room, and both `build_deck` (what is
drawn) and `build_collision` (what is stood in) call it. For a **composed** room the solids come
from its `dress_*` spans alone; its walls and floor stay represented by `room_shell_for`'s smooth
shell.

**Why necessary.** The bespoke-versus-generic choice lived only in `build_deck`, so
`build_collision` went on calling `rooms.build` for its solids. Since 23 module-owned places began
composing in session 3z, a player **saw** the Zocalo and **walked through** a generic bay's
furniture, standing in places the drawn room has nothing at all. Two descriptions of one room —
hard rule 4's failure mode, and it appeared the moment one of them improved.

**What constrained the predicate, and it is the part that nearly went wrong.** `prop_boxes` finds
objects as **connected components of shared vertices**, which is exactly right for a generic bay,
where every `_box` call is its own island. A composed room's module geometry is **one welded
mesh**, so the same rule collapses the Zocalo's 702,840 triangles into **one solid filling the
room** — measured, 1 box against the generic build's 39. Shipping that would have sealed a room the
player is meant to walk into: worse than the divergence it was meant to fix. Taking `dress_*` alone
gives **41** for the Zocalo, 56 for the Council Chamber, 33 for C&C — against the generic 39, 30
and 31, so the counts are comparable and the positions are the drawn room's.

The shell is deliberately **not** taken from the composed mesh, and that is the
collision-is-not-render rule rather than a shortcut: a smooth shell exists because a capsule
dropped on a 66 mm lighting channel wedges on an internal edge.

**Negative control, in `deck._selftest` and run:** taking the whole composed mesh instead of its
dressing yields **1 solid against 41**, and the gate names it as sealing the room.

**What would overturn it.** A module that emits its furniture welded to its shell — then
`dress_*` would miss it and the room would go back to being furnished only by what `compose` adds.
`bespoke.compose` runs `dressing` itself, so today every composed room has some; a module that
built its own fittings inline would need them tagged.

---

## INV-150 — `level_p25`: the statistic an exposure can be solved from

`tools/measure_frame.py`, `measure()`.

**What.** The 25th percentile of a frame's linear luminance, **uncensored** — taken over every
pixel, not over the `[FLOOR, CLIP)` set every other statistic in that file uses. It is a
**derivation instrument** and nothing is scored against it.

**Why necessary.** Every exposure in `export_scene.ROOM_EXPOSURE` and `BESPOKE_EXPOSURE` was set by
`gain *= 1.40 * ref_median / our_median`, which assumes `d(ln median)/d(ln gain) = 1`. That formula
is an inversion, and the median cannot be inverted, because its **population changes with the
thing being solved for**: raise the gain and sub-floor pixels are recruited into the measurable set,
where they arrive at the bottom and drag the median *down* against the light that lifted them.
`measure_frame.py`'s docstring already recorded the exponent ranging 0.97 to 0.01 over the show's
33 frames. **Measured on our own 21 rooms at gains 0.5 / 1.0 / 2.0:**

| statistic | monotonic in exposure | fitted exponent |
|---|---|---|
| `median`, censored | **15 / 21** | **−0.42 … +1.16** |
| `dark_p5`, censored | 12 / 21 | +0.03 … +1.17 |
| `level_p25`, uncensored | **20 / 21** | +0.04 … +1.40, and **1.08–1.40 on 19 of 21** |

On six of our rooms the median goes **DOWN when the lights go up** — `transit` −0.42,
`alien_sector` −0.12, `hospitality` +0.02 — so the old formula does not merely undershoot there,
it moves the exposure the wrong way.

**What constrained the choice of p25 specifically.** Four uncensored candidates were fitted on the
corridor anchor over a ×6 ambient sweep: p25 +1.15/+1.14/+1.06, p50 +0.85/+0.92/+0.92, the whole-
frame mean +0.43/+0.58/+0.72, p90 +0.15/+0.24/+0.38. p90 sits **on AgX's shoulder** and is nearly
inert; the mean is dragged there by the bright tail; p25 sits in the shadow-to-midtone region where
the transfer is still close to linear, which is why its exponent is the flattest of the four.

**What it is NOT, and this cost one wrong derivation before it was caught.** `level_p25` is **not
comparable between frames**, so `p25_ours / p25_ref` is not a level criterion. It is dominated by
how much of a frame is black: `grey level 1.webp` is 0.0312 and `Doug's Dugout.webp` is 0.0007, a
factor of 45, and that ratio is about crush, not exposure. Solving against it gave gains of 0.15
for four rooms. **The target stays the censored median at ×1.40; p25 only supplies the invertible
leg between a wanted change in median and a change in gain.**

**Negative control, run:** `plant_zone` returns `level_p25` = 0.0012 at gain 0.5, 1.0 **and** 2.0 —
identical to four figures, because 85% of that frame sits at sRGB byte 0–1 and no gain in the swept
range lifts it off the 8-bit floor. The derivation refuses it with "FLAT — no response to invert"
instead of producing a number. That independently explains the note already standing on
`BESPOKE_EXPOSURE["plant"]` ("sits at 1.59× either way"): the cause is quantisation, not geometry.

**What would overturn it.** A tone curve with a lifted toe — ACES, filmic and Reinhardt all lift it
more than AgX does — would move p25 up onto a bend and flatten its exponent. Re-fit after any
change to `tonemap_mode`.

---

## INV-151 — An exposure record must carry the shot that produces its frame

`tools/export_scene.py`, `EXPOSURE_FRAMES`, third field; `--gate-frames --rerender`.

**What.** Every row of `EXPOSURE_FRAMES` gains a `(room key, resolution)` shot, and the gate can
re-take the frame before measuring it.

**Why necessary.** `--gate-frames` re-measured a committed PNG, so it could say whether the FILE
passed. It could never say whether the file still described the CODE. **Eleven of the fourteen
distribution failures this project has been carrying were stale frames.** Every failing frame was
committed 2026-07-29 or 07-30; every frame committed on 07-31 passes; and the two things that
landed in between were the lens fix (c05a877) and the soft fill (7cf9404).

**The anchor is the worst case and it is the reason this is an INV rather than a tidy-up.**
`docs/engine-corridor.png` is the frame `RENDER_OFFSET = 1.40` is defined against, i.e. the origin
of every other exposure on the station. Measured it read p5 ×1.64 and 1.76% clipped and FAILED.
Re-rendered from its own recorded command, with no other change:

| | committed | re-rendered | show |
|---|---|---|---|
| p5 (band ×1.29) | **×1.64 FAIL** | **×0.80 PASS** | — |
| clipped | 1.76% | 0.00% | — |
| soffit ÷ wall | **×1.82** | **×0.214** | 0.23–0.32 |
| deck ÷ wall | **×0.29** | **×2.59** | 2.49 |

The committed frame had the show's own ladder **upside down** — a bright ceiling over a dark floor.
CLAUDE.md's headline for layer 4b, *"p5 … fails 13 of 17, bright on 11 — including the corridor
anchor that defines 1.00 for the entire project (p5 ×1.64)"*, was measured on that file and is a
description of code that no longer exists.

**What constrained the form.** The field is `(room, res)` rather than a full argv because every
interior exposure is a property of ONE ROOM and `--shot interior --room KEY` is the shot that
renders one room in isolation. The two `DECK` rows are `--shot deck` and cannot be expressed in it;
they carry `None` and the self-test asserts that **exactly those two** do, so the exemption cannot
quietly grow.

**Negative control, run:** setting a row's shot to a room key that is not in `directory.PLACES`
fails `export_scene._selftest` by name rather than at render time with a traceback; and the
unverifiable-row assertion was `<= 9` and is now `== 0`, so deleting a frame to dodge a failing
verdict fails the suite.

**What would overturn it.** Two rows — `commerce` and `BESPOKE hospitality` — are NOT re-takes of
what they replace. `docs/engine-market.png` and `docs/engine-dugout.png` were rendered before
session 3o rewrote `open_standpoint`, and **no current room key reproduces either framing**: all
five commerce candidates and all five hospitality candidates were rendered and edge-correlated
against the committed frames and every one of the ten gives |r| < 0.04. Their before/after compares
two different pictures, and if the old cameras are ever recovered those two rows should be re-taken
rather than trusted.
## INV-170 — A docking bay's stepped side ledges climb toward the hull, not toward the bay's middle

`station/docking_bay.py` (`section`, `docking_bay`, `_selftest`).

**What.** The three ledge courses either side of a bay are laid so that the highest tread stands
against the hull at 6.6 m and the lowest steps up 2.2 m from the clear deck, leaving 21.6 m of
flat deck down the middle of a 42 m bay. Until session 4a they were laid the other way: the tread
heights ran `(c + 1) × LEDGE_RISE_M` while the tread spans marched **inward** from the hull, so
the tallest step stood 6.6 m tall in the middle of the bay with a 6.6 m cliff facing the
centreline, and the shortest sat against the wall.

**Why necessary.** It is not a preference; the old arrangement was **not a closed solid and could
not be made into one**. Each course's riser was emitted at its tread's inboard edge, spanning one
rise, and with the courses marching inward the surface below that riser's foot was 2.2 m lower
than the riser reached. Twelve boundary edges — six risers' feet and six treads' outboard noses —
ran the entire 140 m length of the bay with nothing under them. Reversing the course order is the
whole fix: every riser's foot then lands exactly on the outboard edge of the tread below it, and
the innermost riser's foot lands on the deck.

**What constrained it.** `reference/03-sector-blue/Minbari Flyer 969 in docking bay 17.webp`
(authority 1) is the only frame of the ledges and this module's own docstring reads it as
*"stepped side ledges, with chevron nosings on every step ... service gantries and handling
equipment stand on them"*. Gear standing on a ledge is gear standing clear of the flight deck,
which puts the ledge against the hull; a stepped mass in the middle of a 42 m bay is an
obstruction in the one place a Starfury has to be. The dimensions are unchanged — `LEDGE_COURSES`
3, `LEDGE_RISE_M` 2.2, `LEDGE_RUN_M` 3.4 are all INV-022's and none of them moved. Only the order
of the courses did.

**What this cost elsewhere, stated because it is a real consequence.** The clear deck is now
`BAY_W_M/2 − LEDGE_COURSES × LEDGE_RUN_M` = 10.8 m either side of the centreline rather than the
full 21 m. The 10.6 m red deck disc was placed at `−hw × 0.30` = −6.3 m, whose left edge at
−11.6 m now runs 0.8 m up the first tread, so it is placed against the clear deck's half-width
instead: −3.24 m, still off the centreline and still on the walking side, which is all the
reference establishes about its position. Its measured 10.6 m diameter is untouched.

**Negative control, run.** `docking_bay._selftest` asserts the courses are one rise apart with
none skipped, and that the tallest floor point at |x| = hw exceeds the tallest at |x| ≤ the clear
half-width. On the pre-4a arrangement the second of those is false by construction.

**What would overturn it.** Any frame showing a bay's cross-section, or a frame showing handling
equipment standing on a ledge inboard of the parked craft rather than outboard of them.

## INV-171 — Nine thicknesses, because a surface with no thickness is a surface with a hole

`station/interior_kit.py` (`deck_pad`, `plate_solid`), `station/council_chamber.py`
(`FIN_D_M`, `MEDALLION_D_M`, `MEDALLION_RELIEF_M`, `FLOOR_BED_T_M`, `TILE_RISE_M`),
`station/command_control.py` (`WINDOW_MULLION_D_M`, `CONSOLE_BODY_M`),
`station/hospitality.py` (`SHADE_T_M`, `DART_T_M`), `station/docking_bay.py` (`DECK_PAINT_M`),
`station/zocalo.py` (`DECK_SLAB_M`, `SOFFIT_T_M`).

**What.** Twelve declared dimensions, each the body of an object that was previously authored as a
zero-thickness plate:

| value | object | reasoning |
|---|---|---|
| `FIN_D_M` 0.10 | a council chamber wall fin | a 5.2 m architectural fin in sheet metal, deep enough to catch the cove light on an edge and read as a fan |
| `MEDALLION_D_M` 0.03 / `MEDALLION_RELIEF_M` 0.02 | the medallion's backing disc, and how far its spokes and rings stand off it | the frame shows spokes and rings reading in relief against the disc; 20 mm is the smallest relief that shadows at a chamber's light levels |
| `FLOOR_BED_T_M` 0.10 / `TILE_RISE_M` 0.008 | the bed under the mosaic, and the tiles' proud face | a screed bed and an 8 mm tile; the rise is what puts a grout line in the frame |
| `WINDOW_MULLION_D_M` 0.06 | how far a window bar stands off the glass | the module's own docstring already required the bars to "read in front of" the glazing and had no dimension for it |
| `CONSOLE_BODY_M` 0.14 | the wedge under a console's lit face | a console face on two slim legs with nothing behind it has no silhouette from the side of the dais |
| `SHADE_T_M` 0.012 | a pendant shade's material | sheet, so the shade has an underside for the lamp to bounce off |
| `DART_T_M` 0.038 | a dartboard | a regulation board is 38 mm of sisal, which is sourced in the same sentence as its 451 mm diameter |
| `DECK_PAINT_M` 0.004 | a painted deck marking's film | thick enough to catch a highlight at the grazing angles a 140 m bay is lit at, thin enough not to trip on |
| `DECK_SLAB_M` 0.14 / `SOFFIT_T_M` 0.14 | the Zocalo's deck and soffit | matched to the end-cap slabs `zocalo_run` already lays, so the deck does not change thickness where it meets its own bulkhead |

**Why necessary.** Not for looks. **3,693 open boundary edges across eight composed shells**, and
every one of these objects contributed some of them. A surface authored in the plane it is seen in
is a surface whose thickness is invisible, so nobody misses it — and a plate with no thickness is
a plate with a *boundary*, which is a hole in whatever mesh it is merged into. Since session 3z
`deck.build_deck` composes eight of these modules onto a ring deck that asserts watertightness, so
these were holes in the station.

**What constrained them.** Every value is the smallest that makes the object physically coherent
at the distance a player meets it, and none is load-bearing on any measurement: doubling or
halving any of them changes no assertion in this project, because the thing being fixed is the
existence of the surface and not its depth. That is stated plainly rather than dressed up — these
are authority 5 throughout.

**What this is really an instance of.** Two defects this project had already fixed once. A flat
thing with no edge is `interior_kit.downlight_pool`'s missing rim, and a lathe open at one end is
`dressing._cyl`'s missing bottom cap (session 3x). Both reappeared in six new private copies
because each module had written its own primitive. `deck_pad` and `plate_solid` now live in the
kit, once each, with closure gates and negative controls that fire.

**What would overturn it.** Any authority-1 frame giving one of these objects a measurable depth.

---

## INV-210 — The room shell is built to the corridor's plate module, because it was not built to any

`station/rooms.py` (`kit_plate_module`, `_plate_field`, `_plate_deck`, `SHADOW_GAP_M`,
`DECK_TILE_M`, `NOSING_PROUD_M`, `NOSING_H_M`, the wall/deck/soffit sections of `articulate`, and
`articulate`'s `plates` and `near_end` parameters), `station/density.py` (`SHELL_SURFACES`,
`KIT_SURFACES`, `kit_surface_floor`, `kit_like_floor`, `shell_split`, `shell_rows`, `--shell`,
and `analyse`'s `facet_p50_m` / `facet_max_m`).

**What.** Every wall, deck and soffit `rooms.articulate` builds is now plated: proud plates with
recessed seams, in courses, with a lip at the bottom of each course, and the module is the
corridor kit's own. Nothing here is a new dimension. Every one is `interior_kit.PROVISIONAL`,
whose wall build-up is measured off `grey level 1.webp`:

| value | m | where it comes from |
|---|---|---|
| plate length | 1.150 | `wall_plate_l_m`, unchanged |
| course height | 0.446 | **solved**, not copied — see below |
| seam | 0.038 | `wall_seam_m` |
| plate proud | 0.045 | `wall_plate_proud_m` = `PANEL_D_M`, which already agreed |
| nosing proud | 0.055 | `wall_rail_proud_m` − `wall_plate_proud_m`: the corridor's one rail stands this far proud of the plates it interrupts |
| nosing height | 0.094 | half `wall_rail_frac` × the corridor's wall height, halved because this repeats every course where the corridor's happens once |
| deck tile | 0.620 | `interior_kit.deck_grid`'s own default |
| soffit pan | 1.500 | `deck_panel_l_m` — a soffit is a deck seen from below |
| vertical member | 3.600 | `portal_spacing_m`, snapped to the nearest plate seam |
| skirt shadow gap | 0.060 | the only free number here; see below |

**THE COURSE HEIGHT IS SOLVED AND THAT IS THE ONE PIECE OF ARITHMETIC WORTH READING.**
`PROVISIONAL` states `wall_plate_courses = 3`, but 3 is a **count over the corridor's own upper
field**, not a property of a plate. Reproducing the corridor's build-up — `wall_h = 3.0 − 0.5`,
skirt `× 0.05`, dado `× 0.34`, rail `× 0.075` — gives a field of 1.337 m, and 1.337 / 3 = 0.446 m
is the size of one plate. Laid as many times as the room is tall, that is right in a 2.9 m office
and in a 7.5 m foundry. Copying the COUNT is measurably wrong: `interior_kit.wall_assembly(12.8,
7.5)` — the kit's own code at foundry scale — divides that wall into three 2 m courses and reads
**λ 1.93**, against λ 3.42 at its designed 3.6 × 3.0 m. The kit is right at its own size and
degrades at any other; solving the height is what carries it.

**Why necessary.** `docs/aaa-scorecard.json` had carried the words for two sessions — *"the War
Room's wall is one unbroken pale panel across 4 m with a scribed line and no joint, no fitting, no
wear"*, craft 2 — and no gate in this repository could produce them as a number.
`docs/shell/before-office-half.png` is that wall at the rubric's half distance: 2 × 1.5 m pale
rectangles joined by hairline scribes, nothing inside any of them. The cause was one line:
`articulate` emitted the whole field between two ribs as a **single box**, `PANEL_D_M` proud, and
called it a panel.

Three things followed from that one box and all three were measured:

* **The mullions were buried.** `MULLION_D_M` is 0.035 and `PANEL_D_M` is 0.045, so every mullion
  above the panel's bottom edge stood *inside* it — 288 triangles a room of geometry nobody could
  see, and the reason the wall in the frame has vertical division below 1.2 m and none above it.
* **The deck had the construction inverted.** `interior_kit.deck_grid` lays proud tiles over a
  substrate, so the tiles are the surface; `articulate` laid proud ribs across a continuous plane,
  so the plane was the surface. It looked tiled and measured as one 7.25 m facet.
* **The end walls were never panelled at all**, on two walls out of four — and the end wall is the
  one a player walks in facing.

**What constrained it.**

* **The corridor kit, measured this run rather than written down.** `density.kit_surface_floor`
  builds `interior_kit.corridor_section` and measures it, so a change to the kit moves the floor
  with it. The same rule as `collision.corridor_profile` ray-casting the kit instead of restating
  its section.
* **`test_materials_layer3` — no new group names.** The construction reuses `_panel`, `_rail`,
  `_mullion`, `_deck_joint`, `_soffit` and `_conduit`, all of which `materials.py` already binds
  by exact name. Coverage is 495/495 before and after. A new name would have needed an edit to a
  file this work does not own, and would have rendered on the glTF fallback until it got one.
* **The walking surface may not move.** Plate tops sit exactly on y = 0 for a deck and on `ceil`
  for a soffit; the substrate is set back behind them. Every height in every room is what it was,
  and `collision.room_shell` — which builds its own smooth floor and never reads this mesh — is
  untouched.
* **`TRIM_MAX_PROUD_M`, which is 0.10 and is asserted.** The deepest thing this adds is the course
  nosing at 0.100 m from the wall face, which is the limit exactly, and `rooms._selftest`'s trim
  check measures every band on twelve locations against it.
* **THE DOORWAY, and this is the constraint that cost the most.** `articulate` is shared with nine
  bespoke modules that cut their doorway in their *own* geometry, later and elsewhere, and hand
  this function nothing to skip. A continuous plate field walls them up: `bespoke.py` went
  **149/149 → 142/149**, *"walled at the doorway"* on eleven rooms, *"narrowest doorway on the
  station: bar_unnamed at 0.00 m"*. `near_end` is the fix and it is a statement about ownership
  rather than about style — `rooms.build` cuts its own aperture and passes it as `door_at`, so it
  may plate the near (maximum-z) face and anything below door height; a caller that has not said
  where its door is gets the wall it had before. INV-112 already established that a bespoke room's
  near face is where the way in is.

**The one free number is `SHADOW_GAP_M` = 0.06**, the bare strip of substrate between the skirt
and the plate field. It is authority 5. What constrains it: `docs/reference-values.md` §1 fits the
reference's dark horizontals across seven x-bins and finds the affine fit beats the multiplicative
one by ≈3× on both the reveal and the dado — *"no albedo produces a ratio that varies with the
light"* — so the band has to be **geometrically shielded**, and 60 mm is the smallest gap the
field's own 10 mm overhang shades at the grazing incidence these rooms are lit at. Doubling it to
0.12 changes no assertion in this project; it would move the skirt's apparent height, which no
frame establishes.

**What it is worth, measured.** `station/density.py --shell`, whose floor is the kit's own
construction at each room's dimensions:

| | wall facet p50 | deck facet p50 | wall λ |
|---|---|---|---|
| before | 3.94 – 9.51 m | 5.26 – 12.80 m | 2.98 – 5.64 |
| after, over all 78 | 0.83 – 1.21 m | 0.53 – 0.85 m | 4.86 – 5.87 |
| the corridor as built | 0.99 m | 0.57 m | 3.62 |

**77 of 78 locations pass on every surface; 233 of 234 surfaces pass.** The one miss is
`lake_pool`'s deck at 0.85 m against a 0.70 m floor, and its cause is the hidden-substrate effect
`density.kit_like_floor` documents: on the largest decks the substrate slab's own top face — which
is entirely covered by tiles and which `analyse` counts anyway — carries just over half the
measured area, so the area-weighted median tips off the tiles and onto it.

The tile count uses `ceil`, not `round`, and `--shell` is what found it: a module is a CEILING on
coarseness, so rounding the count down makes the tile bigger than the module it came from. Four
decks were failing on exactly that, `lake_pool` at 0.85 m and three more short by 2%.

**What it costs.** 1,206,552 → 1,607,208 triangles over the 78 procedural rooms, +33%: deck
+162,924, wall +208,344, soffit +29,388. On the assembled deck `budget.py`'s `frustum structure`
goes 98,919 → 118,587 against a 60,000 allowance, and `resident triangles` 593,824 → 632,212
against 180,000. **Both readings were already failing before this work** — 165% and 330% — and
`budget.py` names the cause itself: *"walk.gd loads one .glb whole — there is no streaming and no
LOD"*. `station/lod.py` exists and has no importer in the deck path. No gate changed verdict:
18/21 within budget before and after, the same three over.

**What would overturn it.** Any authority-1 frame of a Babylon 5 room — as opposed to a corridor —
showing a wall built to a different module. One specifically: `more hallways.jpg` shows a
Downbelow floor of **large plates roughly 1.5–2 m with recessed joints and an inner recessed panel
in each**, not the corridor's fine 0.62 m tile. If that is the industrial floor rather than a
Downbelow one, `DECK_TILE_M` should become archetype-dependent, and it would take about a third of
the deck's triangles back.

## INV-230 — The crowd's LOD ladder, and why its near rung is capped

`station/populace.py`, `crowd_ladder()`; `godot/scripts/npc.gd`, `_lod_at()`.

**What.** Corridor walkers are drawn at **three** levels chosen by distance —
`(18 m → chain lod 2, 45 m → lod 4, 400 m → lod 8)` — instead of the single level the bake picked.
The libraries are 235,808 + 55,168 + 16,480 = **307,456 triangles**, shared by the whole station.

**Why necessary.** A baked walker has one LOD because a static mesh has no other option:
`corridor_lod` picks for the **mean** distance down a 66 m sight line, so the person two metres in
front of you was a 484-triangle body where `schedule.NPC_BUDGET` allows 2,000. An **instanced**
walker is a transform, so the only thing between us and the right answer was a second library.
Measured on `blue/0/0`: **3 walkers on the near rung, 5 on the middle, 126 on the far**, nearest at
6.2 m — so the figure a player is actually looking at gained **4.3×** its triangles and the other
126 got cheaper.

**What constrained the rungs.** Each is the chain level whose **measured** triangle count is
nearest that band's allowance in `NPC_BUDGET["lod"]` — the same rule `corridor_lod` applies to a
single distance. The two ladders are not indexed alike, and assuming they were is how a body ends
up eight times coarser than its budget.

**THE NEAR BAND IS CAPPED AND THAT IS A STATED COMPROMISE, NOT A DERIVATION.** `NPC_BUDGET`'s
0–6 m band allows 8,000 triangles, which is chain level 0 at 4,560. But the crowd is instanced
against a **shared** library, so shipping level 0 means 14 species × 8 phases × 4,560 = **510,720
triangles resident** to draw the four agents that band ever holds. The runtime cannot build a body
on demand, so the choice is between half a megatriangle for four figures and letting the nearest
band share the 6–18 m level. It shares.

**What would overturn it.** A runtime that can skin a body per frame, which would make the library
unnecessary altogether — or per-species libraries built on demand, which would make level 0
affordable for the one or two species a given corridor's near set actually contains.

**Negative control, in the walk gate and run:** the histogram is the only thing that can show the
ladder is used, because the crowd covers the same distance whatever level it is drawn at —
`crowd_travel_m` reads 5,966 m either way. `deck_verdict` fails a run whose walkers are all on one
rung, and it **did** fail while the parse was wrong, on a working ladder: the rungs are separated
by `/` and the nearest-distance field by `,`.

---

## INV-231 — A plant cell the size of the room the register addresses

`station/plant.py`, `room_cell()`, `bay_for_deck()` and the four `walk_*` / two `farm_*` /
one `frame_at` arguments to `plant_bay()`; `station/bespoke.py`, `BESPOKE_GEOMETRY["plant"]`
and `NEAR_END["plant"]`.

**What.** The five plant places in `docs/gazetteer/LOCATIONS.md` — `plant_zone`, `downbelow`,
`downbelow_arch`, `water_reclamation`, `air_compressors` — are built as **room-sized cells of the
outer stack**, composed onto their own ring decks, instead of being assembled as generic bays.
Three numbers set the cell and none of them is chosen:

| | value | where it comes from |
|---|---|---|
| arc | `2 * (half_w − edge_x) / r_walk` rad | `half_w` is `min(room_extent_m, bay_span_m)/2`, which is what `deck.room_shell_for` sizes the **collision shell** from |
| axis | `min(l_full, bay_l)` about the place's own `z_m` | the same expression `deck.room_interior_half_m` uses |
| walkway radius | `bay["r_outer"]` | which for all five places IS the addressed deck's floor radius to within 50 mm |

**Why necessary.** `bespoke.NEAR_END_UNKNOWN` held `plant` back on a measurement that was correct
and a conclusion that was not: *"the catwalk's floor band is 82.2 m across the arc by 1.80 m along
the axis, and the bay it belongs to is 92 x 442 m"*. 92 × 442 m is not a property of `plant.py`.
It is what `plant_bay` returns when it is handed `arc_deg=10.0` and **no `z_span`**, because the
default z-span is the grey sector's own extent. The registry was asking a bay generator for the
size of a sector and reading the answer as the module's nature. **A measurement taken through a
call describes the call.**

**What constrained each of the placement choices, and each was forced by a measurement:**

* **The walkway is the addressed deck's floor**, not the module's gantry at `r_inner +
  CATWALK_CLEAR_M`. `bespoke.room_shell` puts the walkable floor at y = 0 and `deck._place_local`
  puts y = 0 at the **corridor's** radius, so a gantry 15.6 m inboard of the bay's outer face
  lands the bay's other 15.6 m *outboard* of the corridor floor — and `plant_zone` and `downbelow`
  are addressed to deck 0, whose floor is the outermost radius in the whole stack. Their tank farm
  would have hung through the pressure hull. It is also `deck.build_deck`'s own stated rule: *"a
  step between a corridor and a room is a trip hazard the walk test would find and a player would
  feel."*
* **The floor is the whole cell**, not a 1.8 m catwalk. 1.8 m of gantry down the middle of a
  9.96 m cell leaves `bespoke.near_face_opening` no floor within `APPROACH_DEPTH_M` of the door,
  so the room is not enterable; and `dressing.dress` handed a 1.8 × 14 m strip furnishes a
  corridor.
* **The rail and the service tubes go on the far side only.** A 1.05 m rail across the aperture is
  what `deck._mouth_clear`'s 0.735 m probe calls a wall, and a tube stands `TUBE_PROUD_M` past the
  rail line — 0.12 m outside the plane `room_shell` recentres on, which does not fail, it silently
  moves the whole room up the axis.
* **The frames are the room's side walls.** One frame at the cell's centre — which is what
  `max(1, int(arc_deg / FRAME_PITCH_DEG))` gives a 1.7° cell — is a 1.1 × 18 m column standing
  where the furniture and the people go. The first frame of the room was taken from inside it;
  `docs/engine-4b-plant-room.png` is the same room after the frames moved to its edges.
* **The farm is on the place, not on the station lattice.** `FARM_PITCH_DEG` is 30° and anchored
  to absolute angle, deliberately, so two neighbouring streaming cells cannot each put a farm just
  inside their shared seam. A 1.7° room-sized cell therefore lands between farms about 94 times in
  a hundred, and the water reclamation facility contained no tank — `rooms.FIXTURES`' lesson in a
  new costume.

**AND THEN NOT ONE OF THE FIVE CAN HOLD A TANK, which is a finding rather than a shortfall.**
`TANK_R_M = 4.5` (INV-028) is sized against an 18 m bay; `rooms.bay_span_m` clamps every one of
these places to one representative deck-scale bay. A tank needs `2·TANK_R_M + 2·rooms.WALK_M` =
**10.8 m** each way to be walked round, and the five measure 13.56×9.65, 10.15×11.55, 7.72×10.80,
13.56×9.65 and 9.91×5.70. All five are short in at least one direction. The gazetteer already says
what fills the rest: *"the plant zone is predominantly structure, tankage and void"*, and *"life
support does not need 34 decks, it needs about one"*. The tank farms are the same bay, past the
frames, and `farm_at = None` still builds them for every streaming cell in the outer stack.

**The render is what settled that**, and no assertion would have. The first version asked only
whether 9.0 m of tank fitted inside a 13.56 × 9.65 m cell, which it does; the frame taken from the
player camera at the room's centre was the inside of the tank wall filling it edge to edge.
*"It fits"* is not *"you can walk round it"*.

That frame is **not committed and cannot be, because the fix removed the tank it showed** — the
same session both took it and made it un-retakeable. Recorded properly instead: the command was

```
tools/render_godot.sh --shot deck --deck grey/0/5 --at water_reclamation \
    --at-offset 0,-7 --face water_reclamation --face-offset 4,-9 \
    --ambient 2.2 --res 640x360 --out docs/engine-4b-plant-grey05.png
```

and it reproduces the defect from any tree in which the `fits` test in `plant.room_cell` is forced
`True`. `docs/engine-4b-plant-grey05.png` is that same shot **after** the fix, and
`docs/engine-4b-plant-room.png` is `plant_zone` from inside — a grated deck, the edge frames
standing as side walls, pipe runs, racks and two residents. `docs/engine-4b-plant-door.png` is the
corridor side: a closed pressure door under a lit sign reading THE PLANT ZONE.

**What would overturn it.** A wider footprint or a larger `bay_span_m` for any of the five — the
tank rule is a measurement, so a room that can hold one gets one with nothing else changing, and
the `_selftest` assertion fires the other way. A canon frame of a Babylon 5 plant space showing a
gantry over tankage rather than a floor among it would move the walkway back to `r_inner`, and
would then need the register to address these places to the innermost deck of their bay rather
than the outermost.

**Negative control, run:** uncapping one `plant_pipe` run reopens **48** boundary edges, which is
exactly the defect the same change closed (`plant_pipe` 48 + `plant_conduit` 144 = all 192 of
`plant`'s open edges, `cap_lo=False, cap_hi=False` in both). `station/plant.py` 30/30.

---

## INV-240 — The security force's posts, and how an officer gets into a room

`station/npc/security.py` (`POSTS`, `NO_POST`, `officer_pool`, `presence_at`, `patrol`);
`station/populace.py` (`populate`, the fixed/roving split).

**What.** Where the 500-officer force physically stands, how many of them stand there, and the
arithmetic that decides whether a room gets a uniform in it. Authority 5 for the split; everything
around it is derived or sourced.

**Why necessary.** `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` is 1,181 lines of sourced material and
**nothing in the project read it** — `grep -rl LAW-CRIME-DOWNBELOW station/ tools/` returned
nothing while the other three gazetteer files had 23 readers between them. The owner's scope brief
names "law enforcement, crime, the black market, Downbelow's underclass"; those were written down
and wired to nothing.

### The split, and the three constraints that stop it being ten free numbers

| post | pairs | officers | confidence | auth |
|---|---|---|---|---|
| `security_central` | 4 | 8 | STATED | 3 |
| `security_posts` | 6 | 12 | STATED (that they exist) / PROPOSED (where) | 4 |
| `customs_north` | 3 | 6 | STATED | 1 |
| `customs_south` | 3 | 6 | STATED | 1 |
| `zocalo` | 4 | 8 | PROPOSED (D-03) | 5 |
| `council_chamber` | 2 | 4 | PROPOSED (D-03) | 5 |
| `bay_elevators` | 2 | 4 | PROPOSED (D-03) | 5 |
| `docking_bays` | 2 | 4 | PROPOSED (D-03) | 5 |
| `brig` | 2 | 4 | DERIVED | 5 |
| **total** | **28** | **56** | against §2.5's "~60 of the 150" — **×0.93** | |

1. **A post is manned in PAIRS.** §2.5's "2 officers, always" is a force rule, not a patrol rule:
   it exists so the Nightwatch split is visible in any glance, and a post of one destroys that
   exactly as a lone patrol does.
2. **A post is manned CONTINUOUSLY**, so its cost is charged per shift against the on-duty figure,
   never against the 500.
3. **Every key is a `directory.PLACES` key**, so a post is a place on the station rather than a
   name in a document, and a post whose register row disappears **fails the gate** instead of
   silently vanishing.

`NO_POST` names six places — Downbelow, its arch, the black market, the thieves' guild,
`happy_daze` and `welded_shut` — because §2.4's last row is a *positive design decision*
("Downbelow: **No permanent post**"), and a future session adding one should have to delete a line
with a reason on it rather than merely fail to think of it.

### The fixed/roving arithmetic, and the render that forced it

`populate` adds the **fixed** post to the room's headcount and draws the **roving** share from the
ambient crowd. That is not tidiness: `occupancy` is a crowd density and knows nothing about duty,
so folding a four-officer watch into the brig's headcount left room for **zero** officers — the
brig at 18:00 comes back with **one** person in it. The render proved it: one League civilian, in a
detention block, with no uniform. After the split the same room exports four
`npc_cloth__ef_security_twill` bodies, one of them carrying
`npc_cloth_trim__nightwatch_black`. `docs/engine-brig-security.png`.

### The officer pool is a SEARCH, and the ratio is why

`resident.roster` casts a place's regulars from each resident's `job`, and it does that well — ask
for twelve at `security_central` and seven come back `role == "security"`. **Ask at the Zocalo and
none do**, because an officer standing that post has `job == "patrol"`, and no amount of rostering
will put them there. Asking deeper does not help: a place has a capacity, so
`roster(security_central, ..., 300)` still returns four officers.

So `officer_pool` searches the id space on `schedule.role_for`, which draws a role by hash against
FACTIONS.md's apportionment. Security is 500 of 155,000 humans — **0.32%, one officer in ~270 ids**
— and `role_for` is the cheap half of `resident()`: **120 officers out of 32,406 candidate ids in
0.06 s**, measured, against building 32,406 residents. `OFFICER_SEARCH_CAP = 200,000` bounds it.

### The armband is DELEGATED, and that is the correction worth keeping

The first version of `wears_armband` rolled `_u("security/nightwatch", id) < NIGHTWATCH_SHARE` and
**passed every test in the module** — while `costume.py` was independently rolling
`_u(seed, "nw") < NIGHTWATCH_SECURITY_RATE` to decide whether to hang the armband decal on the
sleeve. Two descriptions of one fact, agreeing only by luck, and **the render is driven by the
other one**: a player would have seen the band on a different officer from the one this module
called banded. Hard rule 4 applied to a boolean. `wears_armband` now asks
`costume.costume_for(...).nightwatch`, which also gets the era right for free —
`era_active("nightwatch_visible")` means no armband exists before *The Fall of Night*, which a bare
hash could not know. The negative control patches **`costume.NIGHTWATCH_SECURITY_RATE`**, a
constant this module does not own, and both the share gate and the one-band-one-sleeve gate move
with it. That is what proves the delegation is live rather than decorative.

Realised share over 300 officers: **36%**, inside FACTIONS.md §5.2's stated 150–200 of 500.

**What would overturn it.** Any frame or source establishing an actual post strength — a wide shot
of the Zocalo with a countable number of uniforms in it would settle that row directly, and the
Zocalo is the row the whole "twenty minutes with no uniform, then four in one glance" effect hangs
on. A source giving Security Central's watch size would settle the first row. Nothing here is
canon; all of it is arithmetic over two sourced numbers (500 officers, ~150 on duty) and a stated
list of post *types*.

---

## INV-241 — Three numbers the gazetteer states that the built station no longer agrees with

`station/npc/security.py` (`GAZETTEER_CLAIMS`, `beat`, `beat_report`, `response`).

**What.** `LAW-CRIME-DOWNBELOW.md` §2.5 and §2.6 compute a patrol beat and a response time. Both
were derived correctly from the station as it stood when they were written. Three of their inputs
have since moved, and this module recomputes rather than repeats. Recorded as an invention because
the *replacement* numbers are now what the simulation uses.

| | gazetteer | recomputed | why |
|---|---|---|---|
| Grey outermost ring radius | 402.2 m | **471.2 m** | the addresses became hull-correct (`interior.rings_fitting_at`, session 3z); the station moved under the number |
| its circumference | 2,527 m | **2,961 m** (×1.17) | follows |
| beat walk speed | 1.3 m/s, flat | **1.94 m/s** in Grey, **1.12 m/s** in Yellow | `navigation.walk_speed(g)` is a Froude gait model, v ∝ √(gL). The **heavy** ring is walked **faster** |
| a 75 kg officer's weight there | 108 kgf | **127 kgf** | 1.69 g, not 1.44 g |
| response to a distant outer ring | 12–20 min | **22.3 min** worst (`atmos_monitor`, Grey) | §2.6 priced three vehicle legs and added the walk in prose; this routes the whole journey on the same graph a resident commutes on, lift waits and dwells included |

**The two speed effects point opposite ways and both are real.** The gazetteer's instinct — that
foot patrol in the heavy outer rings is punishing — is correct, and the recomputation says the
penalty is in the officer's **weight**, not in the clock. A beat there is *faster* and *harder*.

**§2.6's headline survives the recomputation, which is the point of doing it.** *"Realistic
security response to the outer ring of a distant sector is 12–20 minutes. To the Zocalo, from the
standing post already there, it is seconds."* Computed: the Zocalo answers **0 s** because it has
its own post, and Grey's `atmos_monitor` is **22.3 min** from the nearest one — which is the Green
council post, not Security Central, because Green is the sector adjacent to Grey on the axis. The
dramatic geometry is not a design choice; it falls out of an 8 km station.

**What would overturn it.** A re-address of the rings that moves Grey's outermost floor radius
back toward 402 m — in which case the module's staleness assertion (`ratio > 1.10`) fires, which is
deliberate: it is written as a bound rather than an equality so that closing the gap gets looked
at instead of passing silently.

---

## INV-242 — Downbelow's occupied fraction, recomputed against the built rings

`station/npc/security.py` (`SQUAT_M2_PER_PERSON`, `DOWNBELOW_ANCHORS`, `squat_report`, `camps`,
`cell_floor_m2`, `CONTACT_SHARE`, `DOWNBELOW_CONTACT_PER_HOUR`, `hostility`,
`BLACK_MARKET_ROUTE`).

**What.** How much of the station Downbelow physically occupies, where the camps are, and how
dangerous an unpoliced place is — as numbers an NPC director can execute.

**Why necessary.** `LAW-CRIME-DOWNBELOW.md` §5.3 calls its own version of this *"the whole tonal
instruction for the sector, and it is arithmetic, not taste"*. It was arithmetic over a station
whose outermost ring has since moved.

| | gazetteer §5.3 | recomputed | source of the difference |
|---|---|---|---|
| outermost-ring cells | 753 | **1,038** (62 decks) | the hull-correct re-address, same cause as INV-241 |
| its floor area | 94.5 M m² | **115.3 M m²** | follows |
| lurkers | ~20,000 | **20,390** | `schedule.ROLE_WEIGHTS`, summed over ten species — derived, not restated |
| squatted floor at 25 m²/person | 500,000 m² | **509,750 m²** | follows |
| as a share of the ring | 0.53% | **0.44%** | |
| **occupied cells** | **≈8 of 753** | **4.6 of 1,038** | |
| **people per occupied cell** | **≈2,500** | **4,444** | |

**Both halves of the tonal instruction come out MORE true, not less.** §5.3 asks for two things at
once — *"the occupied pockets are dense … it should feel like a refugee camp indoors, not a few
figures in shadow"* and *"everything around them is enormous and empty … the isolation the owner
asked for lives here"*. Recomputed, the pockets are **78% denser** and the emptiness is **38%
larger**. **Five occupied cells inside a thousand.**

**The unit trap that would have produced a ×200 error.** `navigation.cell_nav_area_m2` returns
151–355 m² for a cell — that is the **walkable corridor strip** through it. The gazetteer's "140 m
of arc by 442 m of length" is the whole **footprint**, rooms included, and comes to 34,538–276,516 m²
depending on sector. `cell_floor_m2` computes the second and its docstring names the first, because
using the corridor strip would say Downbelow squats thirty-four times the entire outermost ring.

**The camps are anchored to a SOURCED rule and a PROPOSED count.** §5.3's rule is authority 4 and
thermal, not aesthetic: the camps cluster *"around the waste recycling system, the air compressors
and the water reclamation facility"* — compressors are warm, plant rooms are lit and powered around
the clock, a water plant is water. `DOWNBELOW_ANCHORS` names the three register keys, so a camp
follows its facility if the facility moves. **The register carries one Downbelow and §5.3 proposes
four** (it reads the waste system as distributed, one per pressurised sector); `camps()` reports the
gap rather than closing it, because adding three register rows is placement decision D-04 and
belongs to whoever owns the register.

**Hostility is the 95/5 rule with a denominator.** `FACTIONS.md` §12 sets *"95% as avoidance and 5%
as contact"* for factional friction and §8.5 applies it to crime, with §10 giving 1–2 contact events
per hour of play in Downbelow. `hostility()` scales that by `1/(1 + officers present)`, which is
what makes the policing layer and the crime layer **one system**: Downbelow gets the stated 1.50
events an hour exactly, and the Zocalo — with twelve officers standing in it — gets **0.11**, a
factor of fourteen, from the officers alone.

**The black market is a route, not a room**, and §8.4 says so explicitly. `BLACK_MARKET_ROUTE`
carries six nodes with the authority on each. One of them, `dock_workers_quarters`, exists only in
`schedule.PLACES` and not in `directory.PLACES` — legitimately, because "a bribed docker" is a
person in a district rather than a room you walk into. The gate accepts either vocabulary and
**prints which**, because a node in neither is a typo that reads as content.

**What would overturn it.** A canon figure for the Downbelow population — everything above is
linear in it, and 20,000 is authority 5 bracketed by an authority-4 forum estimate of 13,000 and a
weak upper reading of 50,000. At 13,000 it is three occupied cells; at 50,000, eleven. The
qualitative statement — a handful of camps inside a thousand empty cells — survives the whole
bracket, which is why it is the thing the gate asserts rather than the count.

## INV-243 — A fitting's Godot range is a culling radius, and it was set to the pool's visible extent

`tools/export_scene.py` (`plane_coverage`, `room_reach`, `deck_fixture_reach`, `gate_lighting`,
`REACH_TARGET_D_OVER_R`, `REACH_CAP`, `WORKING_PLANE_M`, `FIXTURE_REACH`, `LIGHTING_COVERAGE`,
`AMBIENT_SOLVED`, and `--gate-lighting` / `--fixture-reach`).

**What.** Every `range_m` in `FIXTURE_LIGHTING` was read off a reference frame as *how far the
visible pool extends* — `cc_wall_course` 3.5 m, `light_downlight` 1.2 m, `zoc_stall_light` 2.5 m.
Godot's `omni_range` is not that quantity. It is a hard cutoff: `get_omni_attenuation` multiplies
the falloff by `(1 - (d/r)^4)^2`, which is exactly 0 at `d = r` and already down to 0.35 at
`d = 0.8 r`. A fitting whose pool measures 3.5 m across was being told to deliver **zero** light
past 3.5 m, in a room 9.4 m tall.

Each room's fitting ranges are now scaled by `3 × p95(d/r)` over its own working plane, clamped
to `[1, 3]` — computed from the room's own mesh and its own fittings, memoised, and shared by the
interior shot and the deck shot so the two cannot describe different rigs.

**Why it is that value.** The 3 is not new. `SOFT_FILL_RANGE_M = 3.0 * SOFT_FILL_HEIGHT_M`
already records the reason: *"Godot's range is a CULLING WINDOW, not a falloff — and at d/r = 1/3
it costs 2.4%"*. A source whose furthest lit surface sits at a third of its range has an
**invisible** cutoff; one whose surface sits at 0.72 of it — `sanctuary_blue` — has lost half its
light to the window before the surface is reached. The clamp at 1.0 below is a rule and not a
convenience: a measured range is never **shortened**, because shortening one invents a dimmer
luminaire, while lengthening one undoes a unit error.

**What constrained it — the corridor anchor, measured rather than exempted.** `--gate-lighting`
reports, per room, the fraction of the working plane inside some source's range:

| room | covered | d/r p95 |
|---|---|---|
| corridor (the anchor, **with** its soft fill) | **100.0%** | 0.31 |
| cnc | **0.0%** | 2.18 |
| qtr_command | 10.3% | 3.59 |
| plant_zone | 11.3% | 7.03 |
| customs_north | 16.9% | 4.73 |
| alien_sector | 30.6% | 2.89 |
| hydroponics | 33.9% | 2.61 |
| eleven others | 100% | 0.34–0.92 |

The anchor comes out at scale 1.00 because it is already covered three times over, so the change
cannot move the frame that `RENDER_OFFSET = 1.40` and `AMBIENT_CALIBRATED_ENERGY = 1.30` are
defined against. That is a measurement, not an exemption — and the **negative control**, which the
self-test runs, is the whole finding in one line: with the soft fill taken out, the corridor covers
**54.4%** of its own plane at d/r p95 **1.59**. What the corridor has that no room has is a
general-service source, not more lamps. Session 3n gave it one and no room ever got one.

**What it explains.** `command_control`'s `cc_light_strip` throws 3.5 m and is mounted 4.36 m and
5.56 m above the deck, so the working plane is 3.51 m and 4.71 m below a 3.5 m luminaire and the
disc it can reach is imaginary. `--fixture-energy 6 → 20` had been measured as inert there and
blamed on the camera; it is inert because the sources deliver nothing to the floor at any energy.

**The A/B that says the cutoff and not the fitting count is what binds**, `sanctuary_blue` at
960×540 against `council chambers.webp`:

| | median | verdict |
|---|---|---|
| `--ambient 0.4 --fixture-energy 90` (30× the shipped energy) | **x0.89** | FAIL, clipping |
| `--fixture-reach 3.0 --ambient 0.4` (shipped energy) | **x1.25** | PASS, every band |

Thirty times the energy cannot reach the level. Three times the reach does at the default energy.

**What would overturn it.** A measurement of a fitting's falloff rather than of its pool — a frame
in which one luminaire's contribution can be traced to where it vanishes — would replace the p95
rule with the real cutoff. So would a Godot release in which `omni_range` stops being a hard
window. And a room that reaches the `REACH_CAP` of 3.0 is telling you it has too few sources or
has them in the wrong place: `LIGHTING_COVERAGE` records the four that do, the count each needs
from `n >= A / (2 R^2)` with `R = sqrt(r^2 - (y - 0.85)^2)`, and the `station/rooms.py` defect
behind three of them — `_lay` repeats a fitting down the z axis only, and a "ceiling" fitting gets
exactly two rows at `chan_c ± (chan_hi - chan_lo)/4`, so `LIGHT_PITCH_M`'s measured spacing is
honoured along one axis and replaced by a geometric fraction along the other. `qtr_command` is
29.6 × 7.5 m and its six downlights sit at a **single z**.

**And the ambient is solved against p5, because that is the statistic it controls.**
`AMBIENT_BY_ARCHETYPE`'s values are the per-space `ambient.ratio` from
`docs/layer4-lighting/*.json`, which CLAUDE.md has flagged since layer 4 opened as *two hand-picked
regions of a balanced frame* — 0.300 against a whole-frame 0.086 on the same image. An ambient is a
constant irradiance whichever way a surface faces, so nothing lit only by it is in shadow, and this
project had already measured the consequence without having a use for it: *"fixture energy is INERT
(0 → 2.0 moves p5 by x1.0000), the soft fill nearly so, and AMBIENT OWNS p5 (1.30 → 2.60 moves it
x2.35)"*. That gives `d(ln p5)/d(ln ambient) = 1.22` against `d(ln median)/d(ln ambient) = 0.84`, so
the shape `p5/median` goes as `ambient^0.38`, and each row of `AMBIENT_SOLVED` is stepped by it and
verified by a re-render.

**`ambient_energy` also stops multiplying by `room_exposure` for a solved row**, and that is the
structural half. The reason recorded for the coupling was true when it was written — *"in those
three rooms the fittings contribute almost nothing to the frame … an exposure that cannot move the
dominant term is not an exposure"* — and the reach fix removed it. With the fittings reaching the
floor the exposure moves the dominant term by itself, so the ambient can be absolute again and a
room's level and its contrast can be set apart, which under the old coupling was impossible.

**FOUR ROWS OF ELEVEN, AND THE SEVEN ABSENCES ARE THE RESULT.** `detention`,
`industrial`, `mod:command_control` and `mod:council_chamber` came out strictly better —
command and control and the council chamber were the two worst p5 misses on the station at x2.20
each and both now pass. The seven that did not all failed the same way: the ambient cut fixed p5
and the fittings could not make the level up, so the frame either left the level window or its
black fraction ran past the x11.42 band (`medical` crushed x16.2, `research` x18.2). That is the
fitting count showing through — a room whose sources cannot carry its level has only the flat term
to carry it, and taking the flat term away leaves a hole rather than a shadow.

---

## INV-247 — The verb set a player uses the station with, and the four numbers behind a prompt

**Invented:** the eight verbs in `station/interact.py::VERBS`, the rule that assigns one to each of
the 99 declared interactables, and the four constants that decide when a prompt appears and what a
press does — `interact.gd::reach_m = 2.4 m`, `look_half_deg = 35°`, `press_travel_m = 4 mm`,
`press_frames = 12`.

**Why necessary:** `station/directory.py` has given every one of the 128 register places an
`interacts` field since layer 1 — the column headed *what a player can use in this room* — and
`STATE.md`'s open findings still read "Nothing is interactable except the door." Both were true.
`interacts` had exactly two readers: `rooms.lateral_stack`, which uses it to decide how much WALL a
room needs, and `rooms.build`, which uses it to decide where to stand a box. Neither is a player
using anything. 357 declarations, 0 verbs. `docs/MASTER-PLAN.md` §3.2 says why the verb set has to
come first — *"Building 71 prop behaviours before knowing the verb set is how you build the wrong
71."*

**Constrained by — the verbs.** Nothing here is chosen from a blank page; both tables are keyed on
something this repository already computes, because a fourth vocabulary alongside `interacts`,
`rooms.PROPS` and `rooms.PROP_KIND` is a fourth thing to drift.

- `_KIND_VERB` has one row per value of `rooms.PROP_KIND` — sixteen — which is the classification
  `dressing.machine()` already builds these objects from. It says what SHAPE a thing is.
- `_HEAD_VERB` has twenty-two rows keyed on the token's HEAD NOUN, the last underscore field, which
  is the register's own word for what the object IS. It overrides the shape where the two disagree:
  a `valve` is a `wallpanel` by shape and a control by name.

Both are asserted **total** (all 99 tokens resolve) and **minimal** (delete any single override and
at least one token changes verb), so a row that decides nothing cannot accumulate. The eight verbs
are an *output* of those tables, not an input: `verb_set()` derives them and the self-test fails a
row of `VERBS` no token reaches. `tread` is the honest bucket and is declared unpressable — a
catwalk, a path, a handhold and a kerb are things you get about ON, and giving them a keypress would
be a lie about what is built.

**Constrained by — the numbers.** Each is derived from something already in the repository:

| | value | derived from |
|---|---|---|
| `look_half_deg` | **35°** | exactly half `player.gd::_cam.fov = 70.0`, which is vertical and is the figure `station/budget.py` counts the frustum at (INV-083). The cone is therefore *"inside the field of view without turning your head"* rather than a number |
| `reach_m` | **2.4 m** | measured to the object's CENTRE, which is what `scan()` compares. The deepest responding prop a player stands at is `baggage_scanner`, 2.2 m deep, so touching it puts the eye 1.10 m from its centre; the player capsule is r = 0.35 m (`walk.gd::_spawn_player`), giving 1.45 m against the object. One step back is `rooms.WALK_M = 0.9`, the clear path a body needs. 1.45 + 0.9 = 2.35 → **2.4**. Checked from above: it must stay under `door.gd::open_range_m = 2.6`, or a door would react before you were told you could use its controls |
| `press_travel_m` | **4 mm** | the acknowledgement a momentary control gives. Bounded below by visibility — a 70° vertical FOV over 1080 px subtends **1.297 mm per pixel at 1 m**, so 4 mm is about three pixels at the distance you use something from. Bounded above by the thinnest responding prop in `rooms.PROPS`, `level_plaque` at 0.03 m: a travel over about a third of that would push an object through its own back face |
| `press_frames` | **12** | 0.2 s at the 60 Hz `station/walkable.py` drives physics at — the dwell of a momentary contact, long enough that a frame taken during a press catches it |

**What is NOT claimed.** `RESPONDS` lists only the four verbs the OBJECT answers — `open`,
`operate`, `read`, `store`. `sit`, `rest` and `serve` are excluded on purpose and the runtime reports
`response=none` for them, because what answers those is a BODY: sitting needs the player's own rig,
which does not exist (`npc/animation.py` has `sit_clip` and only NPCs use it), and being served
needs whoever is behind the counter to turn round and talk. Listing them as responding would make
`use()` return true and nothing happen, which is the failure that looks like success. The gate
prefers a responding verb for exactly this reason: its first run chose a `bay_control_booth`, whose
verb is `serve`, and the pass read "it was used and nothing happened".

**Overturned by:** a show frame in which somebody operates one of these objects — the Zocalo's
babcom terminals and C&C's consoles are on screen repeatedly — would replace a derived verb with an
observed one, and would settle the five head-noun collisions `--verbs` prints (`bench` covers a
`bench` you sit on and a `lab_bench` you work at; `lamp` covers a status lamp you read and a pendant
lamp you switch). A player rig with a sit animation moves `sit` and `rest` into `RESPONDS`. And any
of the four numbers is overturned by the thing it was derived from changing: a different camera FOV
moves the cone, a deeper prop moves the reach, a different render height moves the press.

**Measured against the build, not asserted.** `python3 station/interact.py --audit` builds all 128
places through `deck.room_geometry` — the same entry point the assembler and the collision builder
use — and asks whether each declared interactable resolves to a group the place actually emits.
**259 of 357 do.** Every one of the 259 is on a generic room and **every one of the 98 that do not
is on a bespoke-composed place**: `built generic 259/259, built bespoke 0/98`. Of the 98, twenty-six
ARE built and carry the module's own name instead of the register's (`bar_stool` for `stool`,
`qtr_locker` for `locker`, `cc_console_face` for `console`, `customs_desk` for `customs_desk`,
`plant_catwalk` for `catwalk`) and seventy-two were never built at all — `babcom_terminal` is
declared in nine of those places and built in none of them, `door` in seven, `bunk` in six.

## INV-244 — The port's day: a manifest, a curve with two peaks, and the liner

`station/traffic.py` (`MANIFEST`, `BERTH_TIERS`, `DAY_BANDS`, `day_curve`, `rate_per_hour`,
`arrivals`, `liner_today`, `berths_in_use`, `hall_rate`, `cross_check`).

**What.** What arrives at Babylon 5, when, where it berths, and how many people it lands — as
functions rather than as a table in a document.

**Why necessary.** `docs/gazetteer/TRAFFIC-AND-CUSTOMS.md` is 910 lines including a section titled
*"THE PORT AS A LIVING SYSTEM — what to actually simulate"*, and until this module existed **one
file read it** (`station/aperture.py`, for a hull cut). CLAUDE.md's scope names *"transports and
visitors arriving and departing continuously; the jump gate working"* and *"customs and
immigration"*.

### The one thing that is not extrapolation

**Berths × turnaround against the sourced movement rate.** 24 docking bays (authority 3, the
Security Manual, read from `schema["docking"]["docking_bay"]["count"]` and not restated here) ×
24 hours ÷ a 10-hour mean occupancy = **57.6 movements a day**, against an unrelated authority-4
source's *"over 50 to 60 ships"*. Two numbers from sources that know nothing about each other,
agreeing to within a couple of percent on a quantity neither was computed to match. The negative
control moves the turnaround to 24 h, gets 24.0, and the band gate **fires** — so the agreement is
evidence rather than an identity.

### Three things the arrival stream did not have

Measured against `schedule.arrival_times`, which is what the crowd actually uses:

1. **It was flat.** 52 arrivals spread essentially uniformly. §5.4 gives peak-to-trough **3:1**;
   `day_curve` measures **3.12:1** off `DAY_BANDS`, which are the section's own stated intervals
   (a movement every 25 min at night against one every 8 min at the morning peak *is* 3.1:1)
   rather than a curve fitted to the words "about 3:1".
2. **It had one peak and the day has two.** `schedule.wave_pulse` reads 1.0 at 10:00 and **0.0 at
   18:00**. §5.4's second peak is 17:00–21:00 and it is the interesting one — *"departures; the
   Zocalo is busiest at station-evening and the port empties into it."* Asserted directly.
3. **There was no liner.** §5.2: *"the liner is the event … build the day around it."* Measured
   here: a liner lands **689 aboard at 10.8 h** on day 0 and puts **8.5 people a minute through one
   hall** against a 0.28–0.88/min background — the crowdedness-and-isolation axis the owner named,
   and a uniform stream cannot produce it.

`rate_per_hour` normalises the curve **over the whole day** rather than by scaling its peak, so
shaping the day cannot silently change how many ships come; that is asserted (the curve integrates
to 55.0 ± 1).

### Declared, and what constrains each

* **`MANIFEST`** — §5.2's table, authority 5 (T-05), reasoned there to hit 55 arrivals, the 95/5
  civilian split and §3.3's size tiers. Its arrival-weighted mean stay comes out at **12.2 h**
  against the 10 h the tempo assumes, and `_selftest` bounds that agreement so the two halves
  cannot drift apart.
* **`BERTH_TIERS`** — §3.3, and the ~100 m bay limit is PROPOSED (T-03). Three tiers because the
  station has three kinds of berth for one physical reason: a bay-class hull fits a bay elevator, a
  standoff-class hull does not but can still make hull contact, and a 1,600 m hull cannot contact an
  8,047 m station without becoming a structural load case.
* **`BAND_RAMP_H = 0.75`** — authority 5 and deliberately small. It removes the discontinuity
  between bands so a ship does not appear at 07:59 at the night rate and at 08:01 at three times it.
  Cosmetic; the bands are the measurement.
* **`CREW_STAYS_ABOARD`** — a warship lands nobody through customs (§5.2: *"crew stays aboard;
  liberty parties by shuttle"*), and those liberty parties are already counted as shuttle movements.

**A bug this found in its own gate, worth keeping.** `movements_per_day(berth_h=MEAN_BERTH_HOURS)`
bound the default **at def time**, so the negative control could set the module global to 24.0 and
the function went on returning 57.6. The control printed **DOES NOT FIRE** and was right to. It is
resolved at call time now. A control that reports honestly is worth more than one that passes.

**What would overturn it.** A canon figure for arrivals or passengers. The souls-per-day figure is
already in conflict with `npc/schedule.py` by 3.6× — see **C-012**, which this module exists to make
visible and does not resolve.

---

## INV-245 — Friction as a distance, and the crowd that shows it

`station/npc/friction.py` (`SEVERITY`, `PAIRS`, `LEAGUE`, `separation_m`, `contact_per_hour`,
`will_share_table`); `station/populace.py` (`_clear`).

**What.** How far apart two species stand, as a number a crowd placer uses.

**Why necessary.** CLAUDE.md's scope names *"every major faction present, with the friction between
them visible in a corridor"*. `docs/gazetteer/FACTIONS.md` §12 is fourteen sourced rows answering
exactly that, each with a severity and a described behaviour — and **nothing read it**. Worse,
`populace._clear` kept every body **0.45 m** from every other body regardless of who they were:
one radius for a Narn and a Centauri and for two humans queuing at the same stall. The friction was
invisible **by construction**.

### The rule this is built on, and it is §12's own

> *"Friction should be expressed **95% as avoidance and 5% as contact**. A station where hostile
> species brawl on sight is a cheaper and less believable place than one where two crowds move
> through the same concourse and never once intersect. **Build the avoidance first**; the fights are
> set dressing on top of it."*

So the module produces **distance**, not violence.

### What is sourced and what is declared

§12 states the split and this keeps it: *"Authority for the **fact** of the antagonism is given; the
**behaviours** are authority 5 and are the design."* Every row carries the antagonism's authority
(1 for the Narn/Centauri surrender terms, 1 for the pak'ma'ra, 2+1 for the armband split, 4 for the
Minbari castes); the metres are authority 5 and are here.

**The base is not a new number.** `BASE_SEPARATION_M = 0.45` is `populace._clear`'s own personal
space, and every severity is a **multiple** of it — so changing personal space moves the whole
ladder and the ratios survive. Hard rule 4 applied to a distance.

| severity | × base | contact/h | example |
|---|---|---|---|
| ceremonial | **6.0** | 0.00 | *"when Kosh moves, the corridor clears without being told to"* |
| highest | 4.0 | **0.02** | Narn ↔ Centauri |
| high | 3.0 | 0.08 | the Nightwatch chill; a telepath's empty chair |
| medium-high | 2.4 | 0.05 | warrior-caste Minbari ↔ humans |
| episodic | 2.2 | 0.00 | Drazi ↔ Drazi |
| medium | 1.9 | 0.04 | pak'ma'ra ↔ everyone; lurkers in commerce |
| low | 1.3 | 0.01 | the League ↔ the great powers |
| latent | 1.0 | 0.00 | dockers ↔ management |

**`highest` is the RAREST, not the commonest**, and that inversion is §12's, stated outright: *"the
surrender terms (500 executions for one Centauri death) are why restraint is the ambient state."*
Asserted.

**Ceremonial is the LARGEST distance and has zero contact.** A Vorlon is not dangerous; the corridor
simply empties.

### Three things the gates caught

1. **`*` must not match itself.** `("pakmara", "*")` is pak'ma'ra against everyone — not against
   each other, who share their own eating area perfectly happily. Asserted both ways.
2. **The Nightwatch row swallows the League row on any human pair**, and that is correct rather
   than a bug: §12's Nightwatch behaviour is *"a human talking with **aliens**"*, which does not
   care which alien. So the League's own friction is only observable between a League species and a
   **non-human** great power, and the control that proves the row is the Nightwatch one is that it
   **disappears at S2E01** — `era_active("nightwatch_visible")`, the same clock as the armband.
3. **`r` is a floor, not an override.** `populace` places a walker with `r=0.7` for walking
   clearance; taking that *instead of* the pair's separation put a Narn **0.96 m** from a Centauri
   where the table says 1.80. **The crowd gate fired and printed the number.** The two constraints
   are about different things — one is about walking, one is about who is walking — so both apply.

**Measured on placed bodies**, 112 actors in a 26 × 20 m Zocalo: human/human **0.50 m**,
narn/centauri **2.87 m** against a required 1.80.

**What would overturn it.** Any frame that shows two of these species at a measurable distance in
the same shot. The ratios are the claim, not the metres: a frame showing a Narn and a Centauri
passing at a metre would halve the whole ladder without changing its shape.

---

## INV-246 — A unit lights both its walls, because the kit it inherits from does

`station/quarters.py` (the downlight block in the unit builder);
`tools/export_scene.py` (`AMBIENT_SOLVED["mod:quarters"]`).

**What.** Two corrections to how a residential unit is lit, and a re-solved fill to go with them.

**Why necessary.** `tools/export_scene.py --gate-lighting` measured `qtr_command` at **10.3% of its
own working plane inside any light source**, d/r p95 **3.59** — the worst room on the station bar
the customs hall, and it stayed at 81.2% even after INV-243's per-room reach fix tripled every
range. One wall of practicals cannot light a room wider than twice what they reach, and no amount
of energy changes that, because `omni_range` is a hard cutoff.

**Neither correction invents anything.** The block above the fix already declares that a unit
*"opens off a corridor and is built from the corridor's kit, so it takes the corridor's own MEASURED
fittings … and takes the split with them"*. It was taking half of it:

1. **Both walls.** `interior_kit.corridor_section` loops `for side in (-1, 1)` and calls
   `wall_assembly` with `downlights=True` on **each face** — so the residential kit's measured
   behaviour is a lamp column per wall at the measured 3.6 m spacing. A corridor gets away with
   reading like one column because it is 2.6 m across; a 4.9 m unit does not. The −x wall carries
   the bed (0.55 m, passes under a 0.98 m lamp) and the locker (**2.05 m**, which would swallow one
   whole) — so the locker gets the same guard the shower already had on the +x wall, and for the
   same reason.
2. **As many as fit at the measured spacing**, which is what a measured spacing means.
   `int(run / pitch)` truncates, and on a 7.5 m unit it turned **1.9 into one lamp for the whole
   depth** — half the fittings the 3.6 m measurement calls for, in the deepest units on the station.
   The form is now `rooms._lay`'s own: a fitting at each end plus as many gaps as fit between.

**6 → 14 fittings, 10.3% → 100.0% coverage**, d/r p95 3.59 → 0.75. Station-wide the lighting gate
goes **18 of 21 → 19 of 21**. Cost: **1,224 triangles** across all five quarters places.

### And it blew the blacks out, which is the interesting half

`--gate-frames --rerender` went **14 pass → 13**: `quarters` held its level at median ×1.66 and its
`crushed` fraction collapsed to **0.02% against the show's 0.52% — ×0.03, outside the envelope**.
More light, no shadow.

The fill is what absorbs that, and the sweep is the evidence rather than a choice. Ambient 1.521
(shipped) → 0.150, `qtr_command` at 640×360 against `grey level 1.webp`:

| ambient | p5 | crushed | median | verdict |
|---|---|---|---|---|
| 1.521 | ×1.11 | 0.02% (×0.03) | ×1.66 | level OK, **no blacks** |
| **1.050** | **×0.78** | **0.45% (×0.87)** | **×1.15** | **every band OK, level OK** |
| 0.900 | ×0.72 | 1.81% (×3.47) | ×0.98 | blacks back, **level lost** |
| 0.550 | ×0.77 | 7.75% (×14.86) | ×0.66 | both gone |

**1.050 is the only cell that passes both**, and it is 69% of the shipped fill. That is the whole
sequence `AMBIENT_SOLVED` exists for: fittings that can carry the level are what let the flat
ambient come down, and a flat ambient coming down is what puts the shadows back.
`--gate-frames --rerender` returns to **14 pass / 9 fail** with `quarters` passing on the new
content.

**What would overturn it.** Any authority-1 frame of a Babylon 5 crew cabin showing lamps on one
wall only. `grey level 1.webp` is a corridor, not a cabin; the transfer here is from the kit a unit
is built out of, and a cabin shot would replace that inference with a measurement.

---

## INV-248 — The arriving species mix, and who the player turns out to be

**Invented:** that the species mix of people arriving at Babylon 5 equals the species mix of people
already living on it — `station/player.py::ARRIVING_MIX`, which is a copy of `schedule.STATION_MIX`
less the Vorlon.

**Why necessary:** `station/player.py::random_player` has to draw a species from somewhere, and the
only alternatives are worse. A hard-coded four-species list would make "random" mean "one of the
four we have art for"; a second, hand-weighted arrival table would be a rival census that drifts
from the one `schedule.STATION_COUNTS` states a reason for row by row.

**Constrained by:** `TRAFFIC-AND-CUSTOMS.md` §5.3 and FACTIONS.md 2.3 between them. The transient
population is resupplied entirely by arrivals and turns over on a seven-day mean stay, so at steady
state the two mixes must agree *on whoever stays*. That is a real constraint and it is only half of
one: it says nothing about through-traffic, which is exactly where this is most likely to be wrong.
A Drazi freighter crew ashore for eight hours is over-represented at the gate and absent from the
census.

**Kosh is excluded and that is not a rounding decision.** `schedule.VORLON_SINGLETON` already
records why one person cannot be a proportion — 1/250,000 rounds to zero or one depending on the
sample size. A player who rolled him would be a second Vorlon aboard.

**What would overturn it:** any figure for the species composition of *arrivals* as opposed to
residents. It is deliberately a separate constant from `PLAYABLE_MIX` so that overturning it is one
edit and does not disturb the census.

---

## INV-249 — What an arrival lands with, SOLVED against the leak that makes Downbelow

**Invented:** the credit distribution a new arrival carries —
`station/player.py::CREDIT_MIN = 0`, `CREDIT_MAX = 5000`, `PASSAGE_HOME_CR = 250` — and the shape
parameter `CREDIT_SKEW`.

**Why necessary:** a player needs money for the economy to touch them at all, and more than that,
`TRAFFIC-AND-CUSTOMS.md` §6.6 makes *running out of it* the mechanism that produces the station's
underclass: people came for a better life, did not find it, and **could not afford a ticket home**.
Without a distribution that has a left tail, that paragraph is a story rather than a system.

**Constrained by, and this is the point:** §6.6 states the only per-arrival rate the whole document
gives — about **1%** of arrivals fall out of the bottom, ~15 a day, ~5,500 a year, which it
cross-checks against a 250,000-person station. That is a constraint on the left tail, so the skew
is not chosen, it is **solved** for it:

```
credits = MIN + (MAX - MIN) * u ** SKEW
P(credits < PASSAGE) = ((PASSAGE - MIN) / (MAX - MIN)) ** (1 / SKEW) = LEAK_RATE
SKEW = ln(0.05) / ln(0.01) = 0.6506
```

Three inputs at authority 5; the OUTPUT is the sourced number, which is the right way round.

**How it is gated:** `player.py::_selftest` measures the realised share over 4,000 draws and fails
outside 1% ± 0.5%; it measures **0.80%**. The negative control replaces the skew with a flat draw
and the share goes to **4.4%**, 4.4× the target, which fires the gate. A flat draw would have passed
any test that only asked "do people have different amounts of money".

**What would overturn it:** any figure for the cost of outbound passage, or any figure for arrival
wealth. Either one replaces a solved parameter with a measured one.

---

## INV-250 — Three things the port needed a name for: hulls, berths, and the customs areas

**Invented:** in `station/arrival.py` — hull names (`EA_HULL_NAMES`, and alien hulls through
`npc/names.py`'s existing grammars), the berth letter (`BAY_BERTHS = ("A", "B")`), the numbering of
the customs areas (`area_for`), the contraband detection rate (`CONTRABAND_P = 0.01`), and the
quarters unit label (`UNITS_PER_BLOCK = 60`).

**Why necessary:** `station/traffic.py` gives a ship a type, an hour, a berth tier, a passenger
count and a stay, and no name. TRAFFIC-AND-CUSTOMS §4.4 makes a name compulsory rather than
decorative: comms discipline is that a hull is addressed **by name and type** — "Transport Von
Braun", "Narn cargo ship Tal'Quith" — never by registry alone, and D-11's public announcement, which
is the first line of dialogue a player hears, has a slot for it.

**Constrained by:**

- **Hull names.** Two attested examples, and both fit the rule taken from them. *Von Braun* is a
  twentieth-century rocket engineer, so EA civil hulls are named for explorers and scientists —
  which is also how Earth has actually named ships for four centuries. *Tal'Quith* is Narn-shaped
  and `npc/names.py`'s Narn grammar, fitted to attested names, already produces strings of that
  shape; alien hulls therefore go through the species grammars rather than a new list. Only the five
  species with grammars can name a hull, for INV-004's reason: a grammar fitted to zero examples is
  invention dressed as inference.
- **The berth letter.** D-2 has both "Bay 7" and "Docking Bay 12B", so a bay sometimes carries a
  letter and the show never says what it distinguishes. D-9 gives a bay a **landing pad and a
  parking level below it** — two places a hull can be — so the letter is modelled as which of the
  two: A on the pad, B below.
- **The customs areas.** "…disembark through customs area 7" is authority 4 and constrains only
  that a seventh area exists across the pair of halls. `customs.DESKS` gives the built hall four
  processing positions, so eight across the pair against §T-X1's reasoned seven.
  `arrival.py::area_cross_check()` **prints that gap rather than resolving it**, because neither
  number is canon and area 7 is reachable under both readings.
- **The contraband rate.** §6.5 names Dust and concealed weapons at authority 4 and says outright
  that each item *"wants a detection probability"* and that the document does not supply one.
  Constrained from below by the same section calling the discretionary search *"the power that makes
  customs a CHARACTER"* — a rate near zero makes station 9 of the process set dressing — and from
  above by it being a crime rather than the norm. Deliberately the same order as §6.6's leak, and a
  separate constant so overturning one does not move the other.

**What would overturn it:** any list of B5-era civilian hull names; any line using a bay letter
beyond B or using one for something else; any on-screen count of customs areas; any figure for
customs seizure volume; any on-screen quarters numbering.

---

## INV-260 — The station's noise ladder: what a dwelling, a corridor and a plant deck are allowed to sound like

**Invented:** in `station/audio.py` — `AIR_CLASS_DBA`, the four design levels the air-handling
layer of every bed is built on: **living 35 dBA, quiet 30, circulation 45, working 60**, and
`AIR_CLASS_BY_FUNCTION`, which reads a place's class off `directory.PLACES`' own function
vocabulary rather than from a second list of place keys.

**Why necessary:** layer 7 was zero and the owner's standard names *"the sound"* beside the
textures and the physics. Every relative statement an ambience makes — this room is louder than
that one, this hour is louder than that one — is a difference of levels, and a difference needs an
origin. `reference/` contains no audio of any kind, so the origin cannot be measured and the choice
is between extrapolating it openly and having no sound at all.

**Constrained by:**

- **From above, by a real standard for a real closed habitat.** NASA-STD-3001 caps *continuous*
  noise in a crew habitable volume at **60 dBA over 24 h**. The ISS US Lab measures 60–65 dBA,
  which is a *tolerated* outcome on a six-person research outpost, not a designed one.
- **From below, by what the station is for.** B5 is a civil station where a quarter of a million
  people **live**. Its design target is therefore terrestrial habitability, and the terrestrial
  criterion for a dwelling is NC-30, about **35 dBA**. A concourse is not a bedroom: NC-40, about
  45 dBA, is the ordinary design level for an occupied public space.
- **By a distinction the gazetteer already draws in another medium.**
  `LIFE-SUPPORT-AND-INDUSTRY.md` §3.1 makes water a *class* marker — running water is a privilege
  of rank, and Downbelow lives next to reclamation because proximity to the loop is the only way to
  get water without status. The noise ladder is the same fact arriving through the ear: a plant
  deck is a **working** space and may run at the 60 dBA the standard permits; nobody with a choice
  sleeps there. The two statements are independent and they agree.
- **By the room's own ventilation load.** §2.2 derives ~7 M m³/h through ~3.4 M m³ — about two air
  changes an hour in occupied space — so the design air rate follows the design occupancy and duct
  noise follows the rate. `AIR_RATE_EXPONENT = 10` dB a decade of design density, ±8 dB, against a
  circulation datum of 10 people per 100 m².

**What this rules out, and it fired:** the first version of the machinery table put `service_duct`
at 74 dB Lw as an independent source, which produced **62 dBA in the command staff's bedrooms** —
above the working-space ceiling, in a space this entry classes at 35. The duct *is* the air
handling; counting it twice made the second count answer to nothing. `station/audio.py`'s self-test
now asserts that every living space's air handling is quieter than every working space's, and that
no ventilation fixture appears in both layers.

**What would overturn it:** any dialogue or production note establishing a level; any scene in
which a named space is audibly outside its class — a Zocalo that plays as a library, or quarters
that play as a machine room.

---

## INV-261 — The rotation cannot be heard, and what can be heard instead

**Invented:** in `station/audio.py` — `STRUCTURE_DBA = 28.0`, `STRUCTURE_MOD_DEPTH = 0.35`, and the
decision that the structure layer is **identical in every location on the station** except one.

**Why necessary:** an 8 km rotating body is the single most distinctive acoustic fact about the
place, and the naive treatment — a low tone at the rotation rate — is wrong by twelve octaves.

**Constrained by:**

- **canon/00-MASTER.md's own number.** *"period 33.4716 s, 1.7926 rpm"* is **0.0299 Hz**. The
  bottom of human hearing is about 20 Hz. The rotation is therefore *inaudible*, and no ambience
  should contain it as a tone. This is the load-bearing part of the entry and it is not invented at
  all; it is arithmetic on a canon figure.
- **`interior.SPOKE_COUNT = 3`**, the Green rosette's three spokes at 120°, imported rather than
  retyped. A fixed point on the ring sees a spoke pass three times a revolution: **0.08963 Hz, an
  11.157 s cycle**. What a body can perceive is the structure-borne rumble *breathing* at that
  rate, and that slow swell is the only thing in the mix that says the floor is turning.
  `structure_hull.wav` is exactly one spoke-pass period long — 357,030 samples at 32 kHz, a
  quantisation error of 12.5 µs a cycle — so the swell is whole across the loop.
- **The hull is one continuous body**, so the rumble does not change from room to room. That is the
  point of the layer: a rumble that changed with the room would say *building*, and this is a ship.
  The self-test asserts one distinct value across all 128 places.
- **28 dBA** sits below INV-260's 35 dBA living floor deliberately, so it is a presence rather than
  a noise — audible in quarters at three in the morning and nowhere else.
- **The one exception is a bearing, not a room.** A place whose declared function is `rotation`
  gets +8 dB because it is standing *on* the drive. Keyed on the function, so any place that
  acquires it acquires the noise.

**What would overturn it:** a canon rotation rate other than 1.7926 rpm; a spoke count other than
three; any scene establishing that the rotation is silent, or that it is audible as a pitch.

---

## INV-262 — The compressor beat, at 0.75 Hz

**Invented:** in `station/audio.py` — `COMPRESSOR_BEAT_HZ = 0.75`, the amplitude modulation rate of
`plant_beat.wav` and therefore of every industrial space on the station.

**Why necessary:** `LIFE-SUPPORT-AND-INDUSTRY.md` §2.3 states the effect and not the rate: *"the
compressors are audible from Downbelow — a low beat that is the reason nobody chooses to sleep
there."* That sentence is a specification for a sound and it is unbuildable without a number.

**Constrained by the word *beat*, which bounds it from both ends:**

- it must be **countable rather than pitched** — so below 20 Hz, and below the ~4 Hz flutter rate
  above which a listener stops counting and starts hearing roughness;
- it must be **relentless enough to keep somebody awake**, which rules out anything slower than
  about one every two seconds.

0.75 Hz — 45 strokes a minute — sits in the middle of that 0.5–4 Hz window. The 8.000 s loop is
exactly six strokes, so the beat is whole across the join.

**What would overturn it:** any depiction of the plant zone or the compressor deck with audio; any
line establishing a machinery rate.

---

## INV-263 — What the station's surfaces absorb, and how far a room reaches

**Invented:** in `station/audio.py` — `SURFACE_ALPHA = 0.15`, `PERSON_SABINS = 0.4`,
`ACOUSTIC_EXTENT_M = 60.0`.

**Why necessary:** the crowd and machinery layers both go through the diffuse-field result
`Lp = Lw + 10 log10(4/R)` with `R = S·ᾱ/(1−ᾱ)`. `S` is not invented — it is
`density.budget_area`'s own surface formula, so the room the acoustics describe and the room the
triangle budget describes are the same room. `ᾱ` is.

**Constrained by:**

- **0.15 is a hard-surfaced interior**, which is what `materials.py` actually builds: there is no
  soft surface anywhere in the corridor set. It is deliberately **live** — a station that sounded
  like a carpeted office would be the wrong station.
- **0.4 sabins a standing body** is the standard occupancy figure, and it is what stops the crowd
  layer running away. A room fills, its own absorption rises, and the reverberant level saturates:
  measured at 2,000 m², 1→3 voices gains 4.8 dB while 100→300 gains 2.1. With the term switched
  off the same span gains 14.8 dB instead of 10.5, which is the negative control in the self-test.
- **The 60 m horizon is the same move `density.budget_area` already makes**, for the same reason
  and in a different sense. A diffuse field only exists inside a coupled volume; `plant_zone` is
  360° × 442 m and `downbelow` is 101,950 m², and treating either as one room gives a reverberant
  field over a volume no sound crosses. Beyond the horizon a place is a series of coupled volumes
  rather than a room. It is also what makes the traffic layer honest: the station's berthed ships
  spread over the station's berthing floor, and you hear the ones inside a 60 m patch of it — 0.24
  of them in the bay row with a liner in, not all 24.

**What would overturn it:** any measured reverberation time for a set; a set built from soft
materials the material table does not have; a scene in which a shout crosses a bay row.

---

## INV-264 — 25 dB through a station bulkhead

**Invented:** in `station/audio.py` — `BULKHEAD_TL_DB = 25.0`, the transmission loss applied when
an adjacent industrial place's machinery leaks into a neighbour.

**Why necessary:** `LIFE-SUPPORT-AND-INDUSTRY.md` §2.3 asserts that the compressors *are* audible
from Downbelow. `directory.PLACES` already records `downbelow.adjacent = ('plant_zone',)` and
`plant_zone` is an `industrial` archetype, so the geometry and the register agree that they are
neighbours — but whether the neighbour is audible is a number, and it decides whether the
gazetteer's sentence is true in the build.

**Constrained by:**

- **From above, by what an airborne rating would give.** A pressure-rated station bulkhead is a
  heavy, sealed, double-skinned partition; terrestrial equivalents (200 mm concrete, a sealed steel
  pressure door) sit at Rw 50–55 dB. At that figure nothing next door is ever audible.
- **From below, by the fact that a station is coupled structurally as well as through the air.**
  Low-frequency plant noise travels in the frame, where the airborne rating does not apply, and the
  effective figure for a 0.75 Hz beat is much worse than the airborne one.
- **By having to make §2.3 true.** At 25 dB, Downbelow's machinery layer reads **53.9 dBA against
  its own air handling at 32.8** — the loudest thing in it by 21 dB, and a reason not to sleep
  there. The control is command quarters, which are not next to the plant and have no machinery
  layer at all. Both are asserted, and a further gate requires that **every** dwelling on the
  station over 45 dBA of machinery is inside or beside the plant. That gate is what caught the
  mortuary running at 58 dBA on a mis-rated fixture.

**What would overturn it:** any scene establishing that plant spaces are inaudible from the next
compartment, or a figure for bulkhead construction.

## INV-270 — the dialogue role register table

**What.** `station/dialogue.py::_ROLE_REGISTER`, mapping each of `schedule.ROLES` to a speech
register (formal / plain / blunt).
**Why.** An exchange has to be phrased by somebody, and the alternative to a table keyed on the
register's own roles is a fourth vocabulary. Asserted TOTAL against `schedule.ROLES` (19) and
`ROLE_WEIGHTS` (15), and MINIMAL, so a row that changes nothing cannot accumulate.
**Overturned by.** Any reference frame establishing how a named role actually speaks.
**Authority 5.**

## INV-271 — the personal salience floors and `DRAW_FLOOR`

**What.** The floors that keep a personal topic (meal, home) reachable when a station event
(a liner berthing, an ISN bulletin) is scoring far higher.
**Why.** Topic selection is a competition scored off simulation numbers -- at the north hall
twelve minutes after an Asimov-class liner berths, `port` scores 18.28 against `news` 1.40 --
and without a floor every person on the station talks about the same thing. The control raises
every floor above the events and the liner day and the quiet day read the same, which is what
the floors exist to prevent.
**Overturned by.** A better model of what people actually mention.
**Authority 5.**

## INV-272 — the species voice bands

**What.** Three bands over 15 species in `_SPECIES_VOICE`.
**Why.** Species differ in how they address a stranger and the show supports the direction
without giving numbers. The control flattens the table and the 15 species collapse from 3 bands
to 1, which is how the band is shown to be doing work.
**Overturned by.** Dialogue transcripts per species.
**Authority 5.**

## INV-273 — the phrasings

**What.** The sentence frames each topic is rendered through.
**Why.** Everything inside a phrasing's braces is a number or a name this repository computes --
"17 minutes a circuit, 174 on duty" is `security.beat('blue')` and `security.on_duty(13.0)`. The
frame around them is written and is the invented part, stated as such.
**Overturned by.** Scripted lines from the show for the same situation.
**Authority 5.**

## INV-274 — `talk_m` and the 45-degree cone

**What.** A conversation is offered within 3.0 m and inside a 45 degree cone.
**Why.** `interact.gd`'s reach is 2.4 m (INV-232) and talking should start slightly further out
than touching. The cone stops a prompt appearing for somebody behind you. Measured in the
runtime gate: first offered at 2.75 m, 0/0 range and cone violations over every offer.
**Overturned by.** Play testing.
**Authority 5.**


## INV-275 — The car's clear width is the corridor's, measured

**Invented:** in `station/lift.py::shaft_geometry` — `clear_w = 2 * corridor_profile()['half_w']`
= **2.1612 m**, and `clear_h = ceil_y − floor_y` = **2.8070 m**.

**Why necessary:** the reference set contains **no frame of a Babylon 5 lift car interior at all**.
`canon/00-MASTER.md` §3 says so in as many words — *"the lift-car display is still the single
highest-value gap in the reference set"* — and what it is missing there is the LEVEL numbering, not
the car. There is no width, no height, no plan and no photograph. The alternative to extrapolating
is a station whose decks cannot be walked between, which `routes.py` prices at 38 broken edges.

**Constrained by:** the only thing that has to be true of a lift is that it takes what reaches it.
The corridor's clear cross-section is already MEASURED off the kit by ray casting in
`collision.corridor_profile` — 1.0806 m half-width at the portal pinch, 2.807 m of headroom — and
anything that fits that pinch has to fit the car, or the lift is a bottleneck a player meets by
being unable to bring something through. Taking the same cast rather than a second number is hard
rule 4: if the kit's walls move, the car moves with them.

**What this rules out:** a car sized off a real-world lift standard. A 1.1 × 1.4 m domestic car
would be **narrower than the corridor that feeds it**, and a station moving 250,000 people does not
build one.

**What would overturn it:** one frame of a B5 lift interior with a person in it. It would replace
the value outright.

---

## INV-276 — The car is square in plan

**Invented:** `clear_d = clear_w`. The car is 2.1612 m in both horizontal directions.

**Why necessary:** INV-275 fixes the width from the corridor's own pinch. Nothing fixes the depth:
the corridor constrains what can be *presented* to the door, not how deep the box behind it is.

**Constrained by:** a lift lobby meets a car at 90 degrees. The longest rigid object that can be
brought to the door is set by the corridor's clear width, and a car shallower than it is wide
cannot accept what the corridor delivers — it fails on the diagonal. A square is the smallest plan
that can. It is also the plan that makes the shaft's two pairs of guide faces interchangeable,
which is why real shafts are close to square.

**What this rules out:** the shallow, wide car of a passenger lift in a tower, which is optimised
for a queue and not for freight; and the deep, narrow car of a service lift, which cannot turn a
stretcher. `directory.py` gives the `lifts` place the functions `("transit",)` with no cargo
qualifier, and `bay_elevators` — the only lift the sources describe at all — is explicitly a
**cargo** lift with a stated length limit, so the general case has to pass both people and goods.

**What would overturn it:** any frame showing a car's plan, or a production drawing.

---

## INV-277 — The car shell is two of the kit's own thicknesses

**Invented:** the car's floor and roof are `PROVISIONAL['ceiling_slab_m']` = **0.18 m**; its side
and back panels are `PROVISIONAL['door_leaf_t_m']` = **0.10 m**.

**Why necessary:** the external envelope decides whether the car fits the shaft and whether its
roof fouls the landing above, so it cannot be left unstated.

**Constrained by:** the split is structural rather than stylistic. The floor and roof carry the
car and its load and take the kit's only *slab* figure; the side panels carry nothing and take the
kit's only figure for a **moving** panel, the door leaf. Both are already `PROVISIONAL` and both
move if C-004 moves, so the car inherits whatever resolving that conflict does to the corridor
rather than needing a second correction.

**The consequence is checked, not assumed:** external height = 2.807 + 2 × 0.18 = **3.167 m** in a
**3.600 m** storey, leaving **433 mm** between the car roof and the next floor. If that number went
negative the shaft would be a one-storey lift with extra doors, and `_selftest` gates it.

**What would overturn it:** C-004 resolving to a deck pitch under 3.17 m, which would force a
lower car; or any frame of a car interior.

---

## INV-278 — The running clearance is the guideway's, reused

**Invented:** `RUN_CLEARANCE_M = interior.GUIDEWAY_SOFFIT_RELIEF_M` = **0.15 m** between the car
and every fixed surface of the shaft, and `SILL_GAP_M = PROVISIONAL['wall_seam_m']` = **0.038 m**
between the car's sill and the landing's.

**Why necessary:** a shaft with no stated clearance is a shaft whose car interferes with its own
walls, and the failure is invisible until something moves.

**Constrained by:** this project already states exactly one running clearance between a moving
vehicle and the fixed structure it passes — `GUIDEWAY_SOFFIT_RELIEF_M`, which is why the guideway
soffit sits inboard of the bottom chord's running face so *"a car meets the same surfaces inside
the portal that it meets everywhere else on the run"* (INV-050). A lift car in a shaft is the same
problem at a smaller scale. Taking a second figure would be two descriptions of one thing, which
this repository has now been bitten by twice — the door decision made in the render and again in
the shell, and the corridor profile written down instead of measured.

The sill is deliberately **not** given the running clearance: a sill is the plate a foot crosses
and is meant to run close. The kit already states how wide a gap between two plates that must not
touch is — `wall_seam_m`, the 38 mm recess between deck tiles and between wall plates. 38 mm is
also under `collision.floor_holes`' own 0.35 m sampling pitch, i.e. it is not a hole a body can
fall through, and the threshold walk gate measures the actual widest unsupported run at **40 mm**.

**What would overturn it:** a stated lift specification, or a frame showing the gap at a landing.

---

## INV-279 — The shaft is a rectangular box, and its local frame is orthonormal

**Invented:** the shaft is a straight-sided box of constant section, not a radial wedge; the guide
rails are `interior_kit.pilaster` at `pilaster_proj_m` = 0.17 m off each tangential wall.

**Why necessary:** `deck._place_local` maps room-local coordinates through `a = a0 + x / radius`,
which makes a room's walls **radial planes**. That is right for a room, whose floor follows the
ring. Applied to a shaft 10.7 m deep in radius it would taper the section by 10.7/211 = **5.1%**,
from 2.661 m at the bottom landing to 2.526 m at the top, and a lift car cannot run in a taper.

**Constrained by:** guide rails have to be parallel — that is what a guide rail is. So `place()`
in `lift.py` is a rigid rotation (tangential, inward-radial, axial), right-handed with determinant
+1 so every winding decision made in local coordinates survives the map into world space.

**The price is stated and measured.** The car's floor is then a PLANE and the deck's is a
CYLINDER, so they can agree at only one point. Over the car's own 2.1612 m width at r = 210.9 m the
divergence is **2.77 mm**, against `collision.STEP_TOLERANCE_M` of **5 mm** — the tolerance the
project certifies a floor smooth at, itself set below the 22 mm tile lip that stopped a body in
session 3u. The tangency point is the car's centreline, which is where the doorway is, so the
crossing itself is exact. `_selftest` gates the figure rather than asserting the argument.

The rails being `pilaster` is not a shortcut: it is the kit's own vertical member standing off a
wall, it is already a closed solid whose winding `interior_kit._selftest` asserts, and
`materials.py` already binds both `pilaster` and `light_pilaster_strip` — so a shaft needs no new
material and cannot land on the glTF fallback, which is session 4f's finding applied before the
fact rather than after.

**What would overturn it:** a frame showing a B5 shaft interior; a production note describing the
tubes as bores rather than boxes.

---

## INV-280 — The transit column's angle

**Claim (authority 5):** each sector's lift column and every deck spine on it stand at ONE angle,
and that angle is the one lying inside the most of that sector's cluster corridor arcs.

**Why necessary:** `station/routes.py` measures the station's circulation graph, and the column
has to land on each deck's spine or it joins nothing. One angle per sector is what makes that true
by construction rather than by 71 separate coincidences. Blue resolves to 140.0 deg.

**Constrained by:** it is not free -- `deck_arc(must_cover=)` extends every cluster's corridor the
short way round to reach it, so a badly chosen angle is paid for in corridor metres on every deck
of the sector. Choosing the angle already inside the most arcs minimises exactly that cost.

**In style because:** a station this size does not put a lift beside every room; it has transit
spines you join. B5's core shuttle and its lift cores read that way on screen -- you go TO the
transit, you do not find it at your door.

**Overturned by:** any frame or floor plan establishing a named lift core at a fixed bearing, or
showing two independent lift columns on one sector.


## INV-281 — the eye and the brow, as geometry, in the hair material

**What.** Every humanoid resident carries four small solids on the face that did not
exist before: two eyes and two brows. They are placed off the skull's own interpolated
section (`_face_point`, which reads `_head_profile`), not off a second table, so a Narn's
heavier braincase and every per-individual cranium jitter carry them.

Sizes, in fractions of the figure's own head height (`FIGURE["head_h"] × head_k × H`):

| | half-width | half-height | where |
|---|---|---|---|
| eye aperture | 0.061 | 0.024 | `t = 0.46`, `_head_profile`'s own eye-line row |
| brow | 0.078 | 0.013 | `t = 0.55`, on its brow-ridge row |

and across the face at **0.43 of the skull's half-width** at that ring.

**Both emit into the group `npc_hair`**, which is what makes them visible at all.

**Why.** The owner's words about the render were *"the npcs just being undetailed
featureless blobs"*. Session 4f gave the head nine landmark rings, a nose and a pair of
ears; at the distance a player actually talks to somebody the front of the face was still
blank, and a head with a nose and no eyes reads as a mannequin at every distance a
mannequin can be told from a person. Nothing else on a face reads below about 100 px of
head height.

**What constrained it.**

1. *Anthropometry, for the sizes.* Palpebral fissure 28 × 11 mm on a 231 mm head gives the
   half-extents above; interpupillary 63 mm on a 145 mm head width gives 0.43 of the
   half-width. This is the same class of source `FIGURE`'s own cross-check uses — a
   standard table that could not have copied the photograph.
2. *The material library, for the group.* A body in this project has **no UVs and no
   texture**: `materials.py` binds one material per group, so anything on a face that is
   not skin-coloured must be its own group, and the only groups a body may emit are the
   ones the library already binds. Inventing `npc_eye` would put every eye on the
   fallback — the defect CLAUDE.md records three times this week. `npc_hair` is also the
   *right* one and not merely the available one: an eyebrow **is** hair, and the eye's
   aperture is the darkest thing on a face at any crowd distance. `npc_hair` is measured
   as "matte, at the bottom of the human range", which is what both are.
3. *The draw-call merge, for where they are emitted.* `populace._by_material` merges a
   body's spans into one span per **run** of the same material and only ever joins spans
   already adjacent in the triangle list. Emitted with the nose they would cut the skin
   run in three, at two extra primitives per person against
   `budget.BUDGETS["deck_primitives"] = 600`. They are emitted **last**, beside the hair.
   Measured: a bare body is **2 merged runs at every level of every species**, and a
   dressed one at the corridor bake level is **12**, both unchanged by this work.
4. *Depth, by the rule `_face` already records for the nose.* A shallow blob on a curved
   surface crosses it at a grazing angle over its whole footprint. The first version
   buried the eye 42% of its depth, like the nose, and it emerged as two 3 mm slivers —
   present in the mesh, absent in the picture. It now stands 0.86 of its depth proud,
   which is where a real lid assembly sits relative to the orbital rim, and the crossing
   stays steep because the section is flat (`power` 2.4) rather than round.

**Weakest number.** The 0.86 protrusion. It was set by rendering and looking, not derived,
and it is the one value here that a frame could argue with.

**What would overturn it.** An `npc_eye` material in `materials.py` with a sclera and an
iris — then the eye stops being a dark bead and becomes an eye, and the geometry can be
recessed into a real orbit instead of standing proud of one. That is a `materials.py`
change and `body.py` does not own it.

---

## INV-282 — four fingers, and what the palm gives up to pay for them

**What.** `_hand` was one closed lofted shell from the wrist to the fingertips — a mitten.
It is now a **palm** ending at the metacarpal head plus **four fingers**, each three rings
at its own segment count, with a slight curl toward the thigh and converging tips.

| finger | z across the knuckle ring | length | radius |
|---|---|---|---|
| index | +0.62 | 0.92 | 0.98 |
| middle | +0.21 | 1.00 | 1.00 |
| ring | −0.21 | 0.94 | 0.93 |
| little | −0.62 | 0.78 | 0.80 |

Lengths and radii are fractions of the middle finger's; z is a fraction of the knuckle
ring's own depth. The fingers run `0.045 → 0.100` of stature, which is **96 mm** on a
1.75 m human.

**Why.** A mitten and a hand have the same bounding box and the same front-view outline
and completely different ones from every other angle. The thing that reads as a hand is
the **4 mm of background showing between two fingers** — the same argument the project
already makes about holes: a hole shows the background, and here the background is the
point rather than the bug.

**What constrained it.**

- *Adult hand anthropometry.* Middle finger 85–100 mm; index and ring within 5% of each
  other; little ≈ 0.78 of middle; the four spanning about one palm depth at the knuckle.
  Two sources that could not have copied each other, as INV-281.
- *The hand may not grow.* `FINGER_TIP_F = 0.100` is the old four-ring plan's last ring,
  so total hand length is unchanged and `costume.py`'s cuff and `animation.py`'s wrist
  band see the same object. When `fingers` is culled the palm runs the full length again
  and the mitt comes back — it is the coarse level of the same hand, not a second one.
- *Triangles.* `_small_seg` sizes a 9 mm finger by **its own** sagitta rather than the
  torso's: four fingers at the body's 64 segments would be 1,024 triangles a hand; at 6
  they are 128, and the sagitta is 1.2 mm. That derivation is the general form of the rule
  `costume._att_seg` records paying to learn on a 90 mm collar.

**Weakest number.** The `t²` curl toward the thigh (0.16 of the wrist radius). A hanging
hand's fingers do curl, but nothing in `reference/` shows one at a stated scale.

**What would overturn it.** Any full-figure frame with a hand in it at a stated scale;
`reference/14-characters-and-uniforms/` is twenty-four portraits framed at the shoulders.

---

## INV-283 — the Minbari bone crest is 60% taller and 22% wider

**What.** `_f_minbari_crest` went from **0.46 → 0.74** of head height above where it leaves
the skull and from **1.18 → 1.44** of the skull's half-width across, with the sweep back
raised from 0.45 to 0.58 of head depth. **Zero triangles**: `_blade`'s ring and segment
counts are unchanged.

**Why.** `body.py`'s own note on the species has always read *"a broad upright bone fin
rising behind and above the crown, **WIDER than the skull**"*, sourced to
`reference/05-sector-green/rotunda.webp` (authority 1, ~60 px figures — the frame
establishes the shape and not the size). At 1.18 half-widths it was barely wider than the
skull, and the measurement said so: at the level the corridor crowd is baked at, a Minbari
and a human head band overlapped at **IoU 0.875 front / 0.651 side** — the front view, the
one a player walking a corridor gets, was 87.5% the same picture. After: **0.716 / 0.651**.

**What constrained it.** `_selftest` asserts every species — crest, helmet and all — clears
`interior_kit.PROVISIONAL["door_height_m"]`, and it imports that number rather than copying
it. The crest is measured into the bounding box the door check uses, so the ceiling on this
value is the station's own doors and not an opinion. A Minbari at the +2.5σ stature the
truncated deviate allows still passes.

**Weakest number.** Both of them. The shape is authority 1 and the dimensions are ours.

**What would overturn it.** One Minbari at a stated scale beside a human or a doorway.

---

## INV-284 — the brow ridge is an identity feature, not a detail (and the keel that was thrown out)

**What.** `FEATURE_TIER["brow"]` moved from `detail` to `extremity`, so a Narn, a Drazi and
a Grome keep their supraorbital ridge out to **77 m** instead of losing it at **22 m** —
which includes the level `populace.corridor_lod` bakes the corridor crowd at. 20 triangles
at `seg` 8.

**Why.** The same defect hair had in session 4f, one tier down. An attachment that lies
strictly inside the figure's own bounding box is priced by a measurement that cannot see it,
and the consequence here was that every Narn in a corridor was a bald human with a slightly
heavier braincase. `G'Kar more.jpg` (authority 2) is what the ridge is built from, and
dropping it at the level the crowd actually ships at is dropping the species.

**What was tried and removed, recorded so it is not built again.** A medial crown keel — a
low fore-aft ridge over the crown, riding `_head_at` — was built to give the Narn something
the *front* view could see. It made the number **worse**: human vs Narn went 0.875 → 0.946
in the front head band and 0.816 → 0.832 in the side one, because a ridge standing proud of
the crown occupies exactly the outline region **a human's hair cap occupies**. It cost 32
triangles at the bake level to make a Narn look more like a person with a haircut. Removed.

**The honest residue.** Human vs Narn is the closest of the six pairs the gate measures, at
**0.832**, and that is reported rather than engineered away: a Narn's identity in the
reference is a spotted, reticulated crown — a **texture** on a skull this module already
builds wider, deeper and squarer-jawed than a human's — and not a silhouette.

**What would overturn it.** A Narn skin material with the crown pattern in it, at which
point the pair separates on colour rather than on outline and the gate's ceiling should be
re-derived.

---


## INV-285 — the skull as a displacement field, not a stack of discs

**What.** `_head_profile` goes from 9 rows to **15**, and `_ring` gains a second kind of
displacement. A row now carries a `zoff` list as well as a `lobes` list:

* **`lobes`** scale the radius about the ring's centre — a **width**;
* **`zoff`** displaces **z alone**, by `amount × rz`, after the front squash — a
  **relief**.

The split is the anatomy and it is the whole of why a face is now a face:

| t | landmark | tier | carried by |
|---|---|---|---|
| −0.07 | submental triangle | base | `squash_front` 0.92, `zo` −0.008 (was +0.020) |
| 0.06 | mental protuberance | base | radial lobe, midline |
| 0.115 | mentolabial sulcus | face | `zoff` −0.075, sharp 2.2 |
| 0.165 | lower vermilion | face | `zoff` +0.070 |
| 0.20 | oral fissure + gonial angle | base | `zoff` −0.055 sharp 2.0, lobes at 32.7° |
| 0.255 | upper vermilion + philtrum + nasolabial | face | three `zoff` windows |
| 0.34 | zygomatic arch + submalar hollow | base | lobes at 45.9°, `zoff` −0.035 |
| 0.405 | infraorbital rim | face | `zoff` +0.030 |
| 0.46 | orbit + temporal fossa + nasion | base | `zoff` −0.105 at the eye, lobes −0.045 at the temple |
| 0.515 | supraorbital rim + glabella | face | `zoff` +0.055, −0.070 at the midline |
| 0.57 | supraorbital torus | base | lobe +0.045, `zoff` −0.045 |
| 0.635 | frontal eminences | face | `zoff` +0.022, paired |
| 0.70 | frontal squama | base | slope |
| 0.86 | parietal + occiput | base | lobe at 270° |
| 1.00 | crown | base | — |

**Why the two mechanisms are not interchangeable.** The orbit is the case that proves
it. Built as a negative *lobe* at the eye's azimuth, an 8 mm socket also pulls ~3 mm out
of the temple, because a lobe scales the distance from the ring's single centre. Built
as a `zoff` it is 8 mm straight back and the head is exactly as wide as it was. That is
what lets the eye be **recessed** rather than a bead stuck on a ball, which is what the
owner was looking at. Measured on the built mesh: the eye's front sits at 76.9 mm, the
skull around it at 68.9–71.6 mm and the brow at 83.8 mm — **6 mm proud of a socket
floor, 7 mm behind the brow**, which is where a lid assembly sits relative to an
orbital rim.

**What constrained it.**

1. *Standard adult craniofacial proportion*, the same class of source `FIGURE`'s own
   cross-check uses and the same authority-5 status: eyes at half the head height,
   widest point at the parietal, chin ≈ 0.6 of the parietal width, stomion ≈ 0.19 of
   chin-to-crown, interpupillary 63 mm on a 145 mm head width.
2. *The azimuths are DERIVED, not typed.* `_face_az(xf)` inverts the ring's own
   superellipse: a landmark at fraction `xf` of the half-width lies at
   `acos(xf^(p/2))` from +X. The eye (`EYE_X_F = 0.43`) comes out at 65.7°, the
   zygomatic arch (0.72) at 45.9°, the gonial angle (0.86) at 32.7°. So `EYE_X_F` and
   the orbit cannot drift apart, and the cheekbone lobe is on the cheekbone rather than
   8° off it — which the previous table's 52° was.
3. *One authoritative surface.* `_face_point` used to reconstruct the superellipse by
   hand and knew nothing about the lobes, so cutting an orbit would have moved the skull
   and left the eye floating in front of it. It now solves the azimuth and returns
   `_ring_point`, **the function the ring itself is lofted from**. Hard rule 4 at the
   scale of an eye socket.
4. *`_small_seg` and the sharpness exponent.* A crease and a swell need different window
   shapes, so `lobes`/`zoff` entries take an optional `sharp`: the raised cosine to a
   power narrows the support without narrowing `half`, and `half` has to stay wide
   enough to be SAMPLED — a feature narrower than one azimuth step vanishes rather than
   softens.

**Weakest number.** The orbit's −0.105. It is the one value here set by rendering and
measuring rather than derived, and it is the one a frame could argue with.

**What would overturn it.** An `npc_eye` material in `materials.py` with a sclera and an
iris — then the eye stops being a dark bead and the socket can be cut deeper still.
That is a `materials.py` change and `body.py` does not own it. Also: one square-on
portrait of any species at a stated scale.

---

## INV-286 — the nose is measured from the skull, not from the origin

**What.** Every nose ring's centre used to be an absolute fraction of head depth
(`hd × 0.74`). It is now `_face_point(ind, sp, t, 0.0, ...)` — the midline of the
skull's own surface at that height — plus a stated projection.

| t | ring | projection, in head depths |
|---|---|---|
| 0.235 | buried root | −0.100 |
| 0.290 | alar base (nostril wings, a lobe at ±62°) | +0.150 |
| 0.330 | pronasale — the tip | **+0.240** |
| 0.400 | rhinion | +0.150 |
| 0.480 | nasion | +0.045 |
| 0.560 | buried in the brow | −0.060 |

**Why.** An absolute depth is a second copy of the face's shape. The moment INV-285
gave the maxilla a lip standing 4.4 mm proud, the face plane came out to meet the nose
and the nose lost a fifth of its projection **without a number changing**. Measured on
the built mesh, the tip now stands **24 mm** past the face plane, against an adult nasal
projection of ~20 mm on a 231 mm head.

**What constrained it.** Standard nasal proportion — nasal length (nasion to subnasale)
≈ 0.22 of head height, projection ≈ 20 mm — and the nasion notch cut into the skull by
INV-285, which is what gives the bridge a *root* to emerge from. Before that notch
the skull's face plane at the bridge was 0.871 `hd` and the nose's own bridge 0.860:
the nose had no root at all.

**Weakest number.** The alar lobe amplitude (0.34 of the nose's own radius over ±62°).
Nostril width is not visible in any reference frame in this repository.

**What would overturn it.** Any authority-1 or -2 portrait in profile at a stated scale.

---

## INV-287 — the shoulder is a deltoid over a ribcage, and it is four rings

**What.** `_torso_profile` gains three rows and re-numbers two. Reading up the figure:

| ring | height (of stature) | half-width at the SIDES, in biacromial half-widths | tier |
|---|---|---|---|
| upper_chest | 0.772 | 0.96 | base |
| **deltoid** | **0.798** | **1.01** — the widest ring on the whole figure | body |
| shoulder (acromion) | 0.818 | 0.95 | base |
| **supraspinous** | **0.831** | **0.83** | body |
| trapezius | 0.842 | 0.64 (was 0.44) | base |

and the arm's `bulge_at` moves 0.16 → 0.19 with a lateral lobe blended around the belly.

**Why.** A real shoulder's widest point is the **deltoid**, about 25 mm *below* the
acromion; from there the outline runs up and in over the acromion, then down and in
along the trapezius to the neck. That is an S, and three rings is the fewest that can
carry one. The note that used to stand in the source said *"there is no deltoid lobe
here on purpose: the deltoid belongs to the ARM, whose own bulge already carries it"* —
measured, it did not, for the reason in "the problem" above.

**What constrained it, and this is the entry's real content.**

1. **The biacromial measurement already contains the muscle.** `FIGURE["shoulder_w"] =
   0.235` was read off a standing officer in `more hallway.jpg` — across his shoulders,
   in a uniform, deltoids and all. The first version of this put the deltoid **6.5%
   outside** that number, which double-counts. `populace.py`'s idle-sway control is what
   said so: a dressed figure went 0.549 m across the shoulders to **0.601 m**, through a
   0.58 m bound that exists so a body comes back inside its own shoulders. The group is
   scaled to land the widest ring at **1.012** of biacromial; the S-curve is unchanged.
2. **`contains()`**, which asserts every arm-root vertex is inside the torso solid, is
   the ceiling on the deltoid lobe.
3. **`animation.rigid_track`**, and it caught a second one — see INV-288.

**Weakest number.** The 0.34 lateral lobe on the trapezius. It is what stops the top of
the torso being a small round post, and its amplitude is chosen to make the top ring a
ridge running out toward the joint rather than derived from anything.

**What would overturn it.** One full-figure frame of an S2–3 uniform from the front at a
stated scale. `reference/14-characters-and-uniforms/` is twenty-four portraits framed at
the shoulders.

---

## INV-288 — a muscle belly gets a ring, and it must not be a joint

**What.** `_limb`'s ring plan was `k / (rings - 1)` — five evenly spaced values — and
**no `bulge_at` this module uses is one of them**. An arm authored with a 1.30 deltoid at
t = 0.16 was sampled at 0.25, where the bulge envelope has already fallen to 0.33 of its
peak, so the built bulge was **1.098**. A leg authored with a 1.10 calf at 0.55 was
sampled at 0.50 and built **1.034**. Both muscles existed in the parameters and in no
vertex, for as long as the function has existed — and the docstring claimed the opposite
(*"the joint ring is pinned at bulge_at"*).

`_limb_ts` now snaps the ring nearest the belly onto it. **Nothing is added**: five rings
stay five rings, so no level's triangle count moves.

**And the belly must not land on a joint.** `FIGURE` puts the knee at 0.527–0.572 of the
hip-to-ankle span depending on `leg_k`, so a calf at 0.55 pulled a ring onto the knee.
`animation.rigid_track` — a different module's gate, which fits one rigid transform per
piece for a runtime that cannot skin — went **10.7 mm → 30.3 mm** against a 20 mm bar,
because a piece straddling a joint has to follow one bone while its vertices interpolate
two. The gastrocnemius belly is **below** the knee, at 0.62 of the span: both where the
muscle is and clear of the joint. Back to 10.7 mm.

**What constrained it.** `FIGURE`'s own knee height, and `animation.py`'s 20 mm bar.

**Weakest number.** 0.62. Adult gastrocnemius belly is usually quoted as 0.60–0.65 of
hip-to-ankle; any value in that band clears the knee.

**What would overturn it.** Nothing in `reference/`; this is anatomy, not Babylon 5.

---

## INV-289 — the ring tiers, and the 4.5 m the face tier costs

**What.** A profile row carries a tier: `base`, `face` or `body`. `base` is built at
every level and is **exactly** the ring set that existed before this session, so lod3 and
below do not move by a triangle. `face` and `body` are dropped at their own measured
distances.

`form_schedule()` is a fourth LOD schedule beside silhouette, profile and feature, and it
exists for the reason those three are separate: **two knobs stop being visible at two
distances.** A lip is 13.0 mm of chord error and a deltoid roll-over is 30.7 mm.

| step | error | honest from | dropped at | px at the drop |
|---|---|---|---|---|
| `face_and_body` | 0 | — | — | — |
| `body` (face rings gone) | 13.0 mm | 13.39 m | **8.9 m** | 2.25 |
| `none` | 30.7 mm | 31.59 m | **28.1 m** | 1.69 |

**Neither of the other instruments can see this cull**, and that is the finding worth
more than the feature. `feature_schedule` compares **part names** — a head with fewer
rings is the same part, so it scores zero. The figure's **bounding box** does not move
either: the crown, the soles and the fingertips are all base geometry. That is the exact
blindness session 4e paid for with a bald corridor crowd, one currency along.
`_detail_gate` part 5 (d) constructs both instruments on the two meshes and shows them
both returning zero while the chord error is 30.7 mm.

**The 4.5 m, stated rather than absorbed.** The face tier is dropped at 8.9 m although
its own error is honest only from 13.4 m. Two reasons, in order:

* **Nyquist.** The face tier's whole content is `zoff` windows on the front of the head.
  The narrowest that has to read is the lip vermilion at half 24°, so 48° of arc; at
  seg 16 the azimuth step is 22.5°, which is two samples across a lip and **one** across
  the philtrum. A ring bought to carry a feature the ring cannot sample is a ring bought
  for nothing.
* **Budget, and it is the harder constraint.** Carrying the face rings through seg 16 —
  the 8.9–28.1 m band, which holds most of a busy Zocalo — makes a figure 1,929
  triangles instead of 1,739, and `npc/crowd.py` answered by moving the Zocalo's
  impostor swap from **51.1 m to 33.4 m**, inside the 36 m floor that module sets so
  that "fix the overrun" can never mean "put cards on the people the player is talking
  to".

Between 8.9 m and 13.4 m a figure therefore carries **2.25 px** of deviation against a
1.5 px budget. `_detail_gate` part 5 (c) asserts that number against a declared 2.5 px
ceiling **and asserts it is over the 1.5 px budget**, so the compromise cannot be
quietly removed or quietly grown. It is the same kind of stated compromise
`populace.crowd_ladder` records for its near band.

**Weakest number.** `FACE_FORM_MIN_SEG = 32`. The Nyquist argument gives 15 for the lip
and 40 for the philtrum; 32 is inside that spread and the budget is what actually picks
it.

**What would overturn it.** A larger NPC frame share, or a runtime that can skin a body
per frame (which would remove `populace`'s shared-library constraint and with it the
whole reason the crowd is baked at one level).

---

## INV-265 — What tells five bars apart: a snug, an oche and a shuttered hatch

**Invented:** in `station/hospitality.py` — `bar_program()`, and three fitting sets keyed on the
register's declared functions: the dartboard and its scoreboard on `recreation`, four booths
(`BOOTHS = 4`, `BOOTH_BACK_M = 1.42`) on `rumour`, and a closed roller shutter
(`SHUTTER_W_M = 1.30`, `SHUTTER_H_M = 2.05`, `SHUTTER_SLATS = 14`) on `black_market_fringe`.

**Why necessary:** `room()` took no arguments, so `bespoke.BESPOKE_GEOMETRY["hospitality"]` —
`lambda s, p, q: hospitality.room()` — drew one room for all five named bars. `bar_unnamed`,
`eclipse_cafe`, `earharts`, `fresh_air` and `happy_daze` were byte-identical, which
`deck.py --degeneracy` now fails on. Something has to differ, and the choice is between inventing
five looks and reading the five descriptions the gazetteer already carries.

**Constrained by:** the register, which is why the *footprints* are not invented at all —
`rooms.bay_span_m` gives 18.7 x 14.3, 18.7 x 14.3, 12.3 x 16.0, 12.3 x 16.0 and 11.8 x 14.0 m, and
the table grid is derived from that rather than the module's old fixed 3 x 3. Only the **fittings**
are extrapolated, and each is the most ordinary reading of the function it hangs off: a room the
gazetteer marks for `rumour` needs somewhere you are *not* overheard, which is what a snug is, so
`BOOTH_BACK_M` sits above a seated head or it is a sofa; a `black_market_fringe` room needs a
visible back-of-house that is *closed*, which is a shutter. The dartboard is authority 1 and was
already here — what is new is that it is now conditional, because a cafe with an oche is a pub, and
`eclipse_cafe` and `fresh_air` declare `food_service` without `recreation`.

**What it does NOT claim:** that these are the *right* five characters. They are five *different*
rooms derived from five different declarations, which is the bar `--degeneracy` sets. The measured
result is honest and partial: the geometry differs (5 of 5 distinct fingerprints, 6,584 to 6,956
triangles) and a rendered frame still reads as the same bar at a different size, because the
palette, the fitting density and the table furniture are shared. Character is the next pass.

**Overturned by:** any frame of a named Babylon 5 bar interior other than the unnamed one in
`reference/04-sector-red`. One frame of Earhart's would replace the derived half of this outright.

**Materials:** the new groups take existing measured materials rather than new ones — booths follow
`bar_stool`'s upholstery (the same seat, in the same room, from the same frame) and the shutter
follows `prop_barred_screen`'s unpainted steel. `check_material_coverage` caught all five groups on
the fallback the first time they were rendered, which is exactly what that gate is for.

## INV-266 — Kosh's quarters is one sealed volume behind one lock, not a gallery of four

**Invented:** in `station/alien_sector.py` — `sealed_chamber()` and `alien_place()`, plus the
`frosted_grid()` part (`FROST_COLS = 7`, `FROST_ROWS = 4`) and the material
`light_vorlon_frost`.

**Why necessary:** `bespoke.BESPOKE_GEOMETRY["alien_sector"]` was
`lambda s, p, q: alien_sector.gallery(s, p)` — handed the place and dropping it — so
`kosh_quarters` **drew the public gallery**. A Vorlon ambassador's private compartment and a row of
four rented atmosphere locks were one mesh, and `deck.py --degeneracy` fails on it.

**Constrained by the register, which already said they are different programs:**

    alien_sector     9.7 x  5.7 m   residence multi_environ atmosphere_containment
    kosh_quarters   10.2 x 12.0 m   residence sealed_environment

`multi_environ` + `atmosphere_containment` is a gallery serving many species behind many locks;
`sealed_environment` is one volume behind one. The footprint is not invented — it is
`rooms.bay_span_m` — and neither is the vocabulary, which is this module's own portal, lock,
grating and lamps rearranged to a different program.

**And the room's one distinguishing feature is SOURCED rather than extrapolated.** `LOCATIONS.md`
§238 is authority 1 on the environment: *"Its wall treatment is visible behind Kosh: a frosted grid
wall with backlit panels, in vapour."* `reference/15-races-and-makeup/more vorlon.png` shows it, and
the panel colour is measured off that frame rather than chosen — sRGB (184,192,217), H 225.5,
S 0.152, linear (0.479,0.527,0.694), normalised to emission (0.691,0.760,1.000).

**The finding that came out of measuring it:** the compartment is lit **cool** where everything else
this module owns is amber — `light_alien_lattice` H 39.3, `light_deck_grating` H 39.6, both from the
gallery outside. Kosh's atmosphere is lit the opposite colour to the corridor it opens off, which is
what makes it read as somebody else's air rather than a room with a different lamp.

**What is extrapolated and stated as such:** `emission_energy` 0.55 and the housing albedo, because
**75.6% of the sampled crop is above the lit threshold** — what the frame gives is the panel seen
*through its own vapour*, which survives as hue and does not survive as brightness. The rib colour
is deliberately NOT taken from the frame: the dark population in that crop is 0.1% of it (1,427 px)
and reads H 72, green, which is noise in a near-black region, so `alien_frost_rib` follows
`alien_wall`. The grid counts (7 x 4) are read off the frame's visible cells.

**Not built, and stated rather than assumed:** the vapour itself. It is a volumetric and belongs to
the shot's environment, not to geometry.

**Overturned by:** any clean frame of the compartment, which would replace both the energy and the
grid counts, and would let `tools/measure_frame.py --against` close the lighting half properly.

## INV-267 — What separates two customs halls and a concourse: the desks, the gantry, the map

**Invented:** in `station/customs.py` — `hall(..., place=None)`, the baggage gantry
(`SCANNERS = 2`, 2.20 x 1.60 x 2.60 m) on `contraband_search`, and the station schematic panel
(`SCHEMATIC_W_M = 6.40`) on `wayfinding`.

**Why necessary:** `bespoke.BESPOKE_GEOMETRY["customs"]` was `lambda s, p, q: customs.hall(s, p)`,
dropping the place, so `customs_north`, `customs_south` and `arrival_concourse` drew one hall. Two
of them rendered **byte-identically** — same md5, 0 of 360,000 pixels different — and the concourse
is not a customs hall at all.

**Constrained by the register, which already held three different programs:**

    customs_north      10 x 34   immigration identicard_check contraband_search atmosphere_assignment
    customs_south      10 x 34   immigration identicard_check
    arrival_concourse  12 x 34   arrival public_information wayfinding

So the desks appear on `identicard_check` (the concourse has none — it is where you arrive, not
where you are processed), the gantry on `contraband_search` (north only), the schematic on
`wayfinding` (the concourse only), and the bollards where the register declares one.

**Width is scaled, not replaced, and that is the point.** `HALL_W_M = 17.0` is INV-029 and sourced;
the register's footprint width is 10 m for both halls and 12 for the concourse. The **ratio** is
what the register adds and the **absolute** is what INV-029 already decided, so the halls come out
at exactly HALL_W_M and only the concourse widens. A register footprint used raw would have
silently overwritten a sourced number with a layout figure.

**What is NOT a new description of an old object:** the gantry is `dressing.machine("gantry", ...)`
and `rooms.PROP_KIND` already maps `baggage_scanner` onto that builder, so the bespoke room and the
generic room describe one object — hard rule 4. The same reasoning the customs desks already
followed. Its material follows `steel_gantry_oxide`, the station's existing handling structure.

**Extrapolated:** the gantry's dimensions and the schematic panel's. No frame shows either. The arch
is sized so a loaded trolley passes — the kit's door aperture is the constraint a bag has already
come through — and the schematic is sized to the wall it sits on. Both authority 5.

**Measured result**, against the two frames that were once identical:

    north vs concourse   227,507 of 230,400 pixels differ   98.7%
    north vs south       229,598 of 230,400 pixels differ   99.7%

**Overturned by:** any frame of the south hall or the concourse, which would replace the derived
half outright.

## INV-268 — How many suites, how many bays: a count read off the footprint

**Invented:** in `station/quarters.py` — `units_in(cls, place, cap=24)`; and in
`station/zocalo.py` — `bays_for(place, p=None, cap=6)`.

**Why necessary:** both modules already took the argument that would have separated their places,
and nobody passed it.

* `bespoke.BESPOKE_GEOMETRY["quarters"]` correctly read the CLASS off the place — that was the 3z
  fix — and then let `run()`'s `count` fall back to **6** for everything. `ambassadorial_suites` and
  `league_delegations` are both class `diplomatic`, so both drew six identical units.
* `BESPOKE_GEOMETRY["zocalo"]` called `zocalo_run(3, cap_ends=True)` with **no place at all**, so
  `zocalo` and `shops_kiosks` drew the same three bays with the same stall seed.

**Constrained by the register, and it is not close in either case:**

    ambassadorial_suites  40 x 90    diplomatic_mission residence
    league_delegations    16 x 40    diplomatic_mission residence
    zocalo                70 x 120   commerce crowd_hub public_social
    shops_kiosks          40 x 100   commerce retail

A row of quarters opens off one side of a corridor and a Zocalo bay is `bay_length_m` along the run,
so **both counts are arithmetic rather than choices**: 90 / 5.36 = 16 suites against 40 / 5.36 = 7
delegation offices; 120 / 10.8 = 11 bays against 100 / 10.8 = 9. The Zocalo's seed is the place key,
so two runs of the same length still lay their stalls out differently.

**And the quarters answer is right for a second, independent reason**, which is the check that it is
not merely arithmetic: the League of Non-Aligned Worlds is *many small delegations* and the
ambassadorial wing is *few large suites*. 7 against 16 says that.

**What IS invented, and it is only the caps:** `cap=24` units and `cap=6` bays. Both are triangle
budgets rather than layout opinions — at 5.36 m a unit an uncapped 120 m run of `qtr_civilian` emits
22 units into a shot that shows four, and the Zocalo is already the heaviest interior in the
project. Authority 5. Overturned by a streaming/LOD pass that makes the count cost nothing, at which
point both caps should simply rise.

**Not fixed here, and pre-existing:** `zocalo._selftest` fails its seam assertion (4 non-manifold
edges at 3 bays, 6 at 4). Verified by A/B — it failed identically before this change, on the old
default of 3 — so it is a seam defect in `zocalo_run`, not a consequence of varying the count.

---

## INV-290 — The Central Corridor: what `station/concourse.py` adds to INV-020

**Invented:** the gallery walkway's width and slab (1.80 m, 0.22 m), the fascia beam (0.46 m),
the centre-line paired cell (0.26 m square on a 0.62 m pitch), the emitting floor panel
(1.55 × 0.93 m in a running bond with a 0.055 m joint), the wall blade (0.14 m wide, 1.90 →
3.30 m, 3.0 m pitch) with its 0.11 m surround and 0.075 m red indicator, the vendor front's 4 × 3
backlit panel field, and **the composed run of four rib bays = 24.0 m**.

**Why necessary:** `central_corridor` is owned by `interior_kit` in the register and
`interior_kit` has no builder for it, so `deck.build_deck` assembled Red Sector's grand
circulation spine as a **6.93 × 6.00 m generic store bay**. It is the place with the most
player footfall of anything still unbuilt: the Red rosette names it alongside the Zocalo,
Earhart's and Waste Management, and a player crossing Red crosses it.

**What is sourced, and is NOT invention.** Every primary dimension of this room already
existed and is READ rather than restated — `interior_kit.CORRIDOR_CLASSES["concourse"]`, whose
values INV-020 derived **from this same frame**:

| | value | where it comes from |
|---|---|---|
| clear width | **9.0 m** | INV-020, proportioned against the rib arches in `more hallway.jpg`. INV-020 calls this its weakest figure and says so. |
| height | **7.2 m** | INV-020: the frame shows people standing above people, so the volume is two decks, and 3.6 m is INV-010 |
| rib spacing | **6.0 m** | INV-020 |
| deck strip width | **0.9 m** | INV-020 |
| rib section | **0.55 × 0.42 m** | `interior_kit.rib_arch`'s own defaults, INV-020 |

The frame itself — `reference/09-garden-core-and-transit/central corridor.webp`, authority 1,
extracted in `reference/00-INDEX.md` — establishes, and this module builds, every one of: two or
three concentric circular ring frames in **dark oxide red**; a catwalk *"about two people wide"*
with a two-bar railing on slender posts and a solid fascia beam carrying a light line; a **raked
panelled soffit** in canted rows with dark joints; diagonal bracing and canted panels above; the
centre-line **ladder of paired square cells** in a raised dark kerb; large **pale-blue emitting
floor panels** in a running-bond grid; wall-mounted **vertical white light blades** in chamfered
dark surrounds with small red indicators above; a **vendor front** of backlit orange-red panels
behind vertical mullions over a counter; and a **wheeled trolley with a magenta-lit top**.

**Constrained by:**

- **The gallery's height is not a new number.** It is one INV-010 deck pitch, which is the same
  observation that makes the volume 7.2 m tall in the first place. A gallery at any other height
  would land between decks.
- **The gallery's width is the frame's own words against a measured body.** *"About two people
  wide"*; `station/npc/body.py` puts a shoulder at 0.45–0.60 m, so two abreast plus a hand's
  clearance is 1.80 m.
- **The cell pitch is the deck the station is already laid in.** `rooms.DECK_TILE_M` = 0.62 m, so
  the ladder lands on the existing grid instead of beating against it. The cell is ~⅓ of
  INV-020's 0.9 m kerb.
- **The floor panel is 2.5 × 1.5 of that same tile.** The frame shows roughly two panels between
  a standing figure's feet and the wall over about 3 m, which is 1.55 m — and 1.55 m is 2.5
  tiles, so the field is a bond of tiles rather than a size of its own.
- **The blade runs from above a standing head to the fascia**, 1.90 → 3.30 m, which is the band
  the frame shows lit and is bounded at the top by the gallery, not chosen.
- **The rib is handed `width − 2t, height − t`**, not the room's own section, so its OUTER face
  is the wall and it stands proud inside by its own thickness. Handing it the room's 9.0 × 7.2
  put 0.42 m of steel through both walls and through the soffit; `_selftest` caught it as a
  bounding box 0.48 m wider than the class allows.

**The colour is a material decision this module could not make and had to name around.** The
reference calls the ribs *"dark oxide red … a deliberate note, not grime"*. The archetype's own
`transit_rib` binds `shell_rib_painted`, a flat 0.469 grey. The rib is therefore emitted as
`dress_gantry_rib`, which binds `steel_gantry_oxide` (albedo 0.300 / 0.255 / 0.242, sourced from
`03-sector-blue/dock.webp`) — the closest sourced oxide in the library. **The name also has to
end in `_rib`**, because `rooms.is_solid` treats that suffix as SHELL: an arch named as an object
becomes a collision box spanning the whole 9 m section and walls the spine a player is meant to
walk down. `concourse._selftest` asserts no collision box exceeds 80% of the section.

**What is capped, said out loud:** the place is 187 m of arc by 120 m of axis and PLC-056's
tiling target is **540 bays**. This builds **four rib bays, 24.0 m — 20.0% of its axial extent
and one bay of its arc.** That is STATE.md §13's own rule (*"tile the bay along Z to the
location's real length, dress only the bays within sight, and state the cap loudly"*) and the
tiling itself is unbuilt for every place on the station. `concourse.py --selftest` prints the
ratio on every run so it cannot quietly become the place.

**Overturned by:** any frame with a person against a concourse wall (which would re-derive
INV-020's 9.0 m and with it every proportion here), or a wider shot showing the catwalk's far
side, which would settle whether the gallery runs one side or both.

---

## INV-291 — The observation rotunda

**Invented:** the chamber's interior radius **7.00 m**, its sixteen bays, the sill at 1.20 m,
the head at 3.60 m, the entablature at 4.32 m, the crown at 7.20 m, the slat band at 1.05 m with
seven slats a bay, the three-tier corbel course at 0.30 m a tier, the column's proportions, and
the fittings' sizes.

**Why necessary:** `obs_rotundas` is owned by `components.py`, which builds the EXTERIOR.
Standing under an `observation_dome` at its own base plane, **0 of its 192 triangles face the
viewer** — every surface points out, so a player inside one sees the background, and the
background is black. The register therefore fell back to a generic bay: an 8.4 × 6.0 m store
room where the station's observation lounges are. `bespoke.py`'s own audit block nominated this
place as one of *"the three worth building"* and stated what it needs: *"an observation room is a
FLOOR, a WINDOW RING and a DOME WITH THICKNESS"*.

**What is sourced:** `reference/05-sector-green/rotunda.webp`, **authority 1**, and it is the
richest single interior frame in `reference/00-INDEX.md`. It establishes, and this module builds:
*"at least eight columns across the far arc … a closed ring at that spacing implies roughly
sixteen bays"*; the column order — *"a plain slightly tapered cylindrical shaft carrying a group
of THREE narrow ring collars, then a longer plain shaft, then a short stepped capital under the
entablature"*, an order which **also appears on the Garden's civic building in `garden.png`**, so
it is a station order and not a one-off; *"a corbel course of stepped rectangular blocks in
layered tiers"*; *"a smooth warm gold-bronze dome with broad radial ribs"*; *"two pale conical
elements on the cornice"*; *"a continuous band of narrow pale vertical slats at about waist
height running right around the room"*; *"four hanging banners"*; *"tall blue backlit lattice
panels … at far left and far right"*; *"a flight of about ten pale steps rising to a dark portal,
flanked by piers whose lower ends carry a comb of vertical slots"*; *"a dark plinth lectern with
a sloping cyan-glowing top"*; and *"a radiating sunburst mosaic — triangular radial wedges about
a centre, and a broad concentric band of chevrons at larger radius"*.

**Constrained by — and the radius is derived twice, independently:**

- **From the register.** `obs_rotundas` is a CLASS row for **four** rotundas over 12° at radius
  281.9 m — 59.0 m of arc, so **14.75 m of frontage each**. A chamber of that outside width with
  `rooms.WALL_T_M` walls has an interior radius of **7.00 m**.
- **From the frame.** Sixteen counted bays around a circumference of 2π × 7.00 = 44.0 m is
  **2.75 m a bay**, which is what a colonnade bay reads as against the robed figures and is
  comfortably wider than `rooms.PROPS['viewport']`'s 2.4 m glazed panel.

  Neither derivation was fitted to the other and they agree. That is the strongest evidence in
  this entry and it is the reason the radius is stated without a range.
- **Both heights are INV-010's deck pitch**, which is the same rule INV-020 used on the
  concourse: the window occupies exactly the first deck (head at 3.60 m) and the crown sits at
  exactly the second (7.20 m). The entablature is 1.2 pitches.
- **The slat band is a waist on a 1.75 m body** — 1.05 m, which is also `interior_kit.handrail`'s
  height, so the band and the rails of this station agree by construction.
- **The dome is a CLOSED SOLID with 0.22 m of thickness**, revolved from a closed meridian:
  outer surface up, inner surface back down, rim across. That is the whole difference between a
  room and a blister on a hull, and `observation._selftest` measures it directly — it counts the
  triangles facing an eye at the chamber's centre at standing height and requires more than a
  quarter of them, which is the measurement that failed on `components.dome_mesh` at 0 of 192.

**The one thing the spec and the gazetteer disagree about, carried visibly rather than
resolved:** `LOCATIONS.md` §241 records the rotundas' facing as **unresolved** — *"if the domed
rotunda above is one of these, they face inward across the drum, not outward at space"* — and
`00-INDEX` reads this frame as drum-interior *"with the caveat stated"* (green and khaki terrain
reaching the window head with no sky band). `docs/spec/PLACES.md` PLC-064 is the content
authority and says **"facing OUT at space"**. This module follows **the spec for the glazing and
the auth-1 frame for the architecture**, which is the only split that uses both sources honestly.
Nothing here decides `CONFLICTS.md` C-003.

**Overturned by:** a frame showing a rotunda's exterior, which would fix the diameter directly;
or any shot establishing which way the windows face, which would also close C-003 note 2r.

---

## INV-292 — The observation domes, and their bay module

**Invented:** the dome chamber's radius as **`(viewport width + walking clearance) × the place's
own viewport count ÷ 2π`** — 6.30 m for `obs_dome_1` and 4.20 m for `obs_dome_2` — the ring
wall at one deck pitch, the dome rise at 0.75 R, the gallery well at 0.55 R, and the vestibule
that gives a round room a flat face to be entered through.

**Why necessary:** the same reason as INV-291 — `components.py` builds blisters on a hull and
both domes fell back to generic bays. PLC-002 describes the room `obs_dome_1` actually is: *"the
dome structure holding C&C (PLC-001 `within`); glazing ribs, gallery ring, service crawl"* — the
ring gallery **round** C&C's light well, not a second C&C. PLC-030's function is unstated in
canon; LOCATIONS P-11 adopts a traffic annexe plus public gallery and PLACES.md carries it at
authority 5.

**What is sourced:** `reference/03-sector-blue/comand and contorl.webp`, **authority 1**, is the
dome glazing seen FROM INSIDE, and `LOCATIONS.md` §169 records it: *"a large circle on radial
spoke mullions with a broad concentric ring band, set in a flat-panelled bulkhead with angled
bracing"*. That is this room's window and it is the same glass C&C looks through, so **the
mullion count is READ from `components.DOME_MULLIONS`** rather than restated — the number INV-024
measured off this frame, independently corroborated by `rotunda.webp`'s *"roughly sixteen bays"*.

**Constrained by:**

- **The bay module is derived from two constants that already exist.** A window bay must hold
  `rooms.PROPS['viewport']` (2.4 m wide) and leave a pier a person can pass, `rooms.WALK_M`
  (0.9 m). So a bay is **3.30 m**, and the radius follows from the count. Nothing about the
  radius is chosen; changing either constant re-derives both domes.
- **The counts are the spec's, and they are what makes the two domes two rooms.** PLC-002 lists
  **12 viewports**, PLC-030 lists **8**. Feeding those counts through one bay module gives
  6.30 m and 4.20 m — 125 m² against 55 m² — with different fittings on top: dome 1 has the
  gallery well, its rail, two service ladders, the blast-shutter leaves and the shutter master;
  dome 2 has six benches and two traffic repeater consoles and neither ladders nor shutters.
  `observation._selftest` hashes all three programs' geometry and fails if any two are one
  geometry, **with a control that ignores the place and collapses them** — session 4h's own
  test, applied inside the module.
- **The gallery well is a RECESS, not a hole.** A void in a floor is a void a body falls through
  and `station/collision.py` sweeps a smooth shell that has no way to say so. 0.25 m down with a
  kerb and a rail on its edge reads as a gallery over C&C without being a trap.
- **The vestibule is not a decoration.** A round room has no flat face for a corridor to arrive
  at, and `bespoke.room_shell` puts the near face on the assembler's plane while
  `near_face_opening` measures the widest way in across it. Its half-width is
  `bespoke.DOOR_HALF_W_M` + 0.45 and its length is `bespoke.APPROACH_DEPTH_M` + 1.40, both taken
  from the numbers the assembler itself probes with, so the passage IS the aperture.

**A measurement that changed where a door frame stands, and it generalises.**
`interior_kit.door_frame` carries a sliding leaf's pocket on one side. Standing it in the
vestibule's aperture left **1.20 m clear, centred 0.125 m off** at the three heights
`deck._mouth_clear` probes — narrower than the corridor's own 1.50 m leaf and not symmetric about
it, so a body walking straight at the door meets a jamb. The frame is therefore built at the
CHAMBER end of the vestibule, where it still reads and blocks nothing. `bespoke.near_face_opening`
found this in the module that builds the thing, which is where session 3x said the gate belongs.

**Overturned by:** any frame of a dome interior other than C&C's, or a production drawing giving
the dome's internal deck. Both radii are consequences of a bay module, so a single measured
observation-gallery width would replace all of it.

## INV-293 — How much of a location gets built, and where the detail stops

**Invented:** in `station/rooms.py` — `tiling()`, `bays_along()`, `built_span_m()`.

**Why necessary:** `bay_span_m`'s docstring has always ended *"the full location is then that bay
instanced along its footprint"* and nothing instanced it. `bays_in()` had two callers and both put
the number in a report dict. Measured: the station was built at **1,280 m of 18,790 m** of its own
declared axial footprint — `docking_bays` is 140 m in the gazetteer and a player walked 10.77 m of
it, into a wall that was drawn as well as felt, so nothing looked broken.

Instancing the bay is arithmetic and needs no invention. **What is invented is where it stops**,
because 128 locations at full footprint is 2,338 bays and no frame can draw them.

**Constrained by numbers already committed in `station/budget.py`, not by new ones:**

* **The ceiling is `DECK["visible_all_tris"]` = 300,000** — *"everything in the frame, not just
  structure: props, fittings, doors and people are what the player is looking at"*. A tiled
  location is a straight run with no curvature to occlude it, so from its door every bay of it is
  in frame at once — the same visibility case that file prices the habitat drum on. A place is
  allowed the whole allowance because at the distance where it fills the frame it **is** the frame,
  which is the reading `density.scene_budget` already takes, in its own words, for the same reason.
* **The ladder is distance from the door**, and which layer falls off is measured rather than
  chosen. One `docking_bays` bay is 96,628 triangles: **51% baked NPC bodies, 26% dressing, 19%
  shell and articulation, 5% fixtures and declared props.** Structure, machinery, plan elements,
  declared interactables and light fittings are built in **every** bay — they are what the place is,
  and they are the cheapest fifth of it. `dressing.py`'s furniture and `populace.py`'s baked bodies
  reach `n_dress` and `n_pop` bays back from the door, which is exactly the trade
  `deck.CORRIDOR_INSTANCED` already makes for the corridor crowd at 88% fewer triangles.
* **The per-bay cost is probed, not assumed.** It is a property of the room — 25,740 triangles a
  bay in `docking_bays` against 4,928 in `core_shuttle` — so a global bay count would be a picked
  number, the defect `bay_span_m` was itself written to fix. Three probe builds through `build`
  give the marginal cost of a bay, the fixed cost of the two end walls, and the cost of the two
  falling-off layers. The fixed term matters: `n x cost(1 bay)` over-charged `docking_bays` by 30%
  and cost it four bays — 43 m of room — to an arithmetic error.

**Authority 5 on the ceiling reading.** Charging one location the whole deck frame allowance is
generous in one direction (the corridor and everything through the doors get nothing) and mean in
the other (real occlusion culling and LOD would draw far bays for a fraction). `budget.py` records
that the project *"contradicts itself on the frame figure and always has"* — 1,200,000 against
20,000,000 — and everything here is gated against the smaller one, so if the 20 M reading is right
every capped location has 16x more headroom than it claims.

**What would overturn it:** a frame capture on the target card (which is what INV-082 says settles
the frame figure at all); or engine-side occlusion and distance LOD, at which point the cap should
simply rise and no other line changes — `tiling()` reads the budget live.

**Recorded, not fixed:** `bays_in()` uses `int(l_full / bl)` where `whole_bays` guarantees an exact
division, so floating point truncates 13.000000000000002 to 12 and it under-counts by a whole bay
on most of the station. `bays_along()` uses `round` and is what the tiling builds to.
**`bays_in` is deliberately unchanged** — its 49,265 total is frozen normative in
`docs/spec/PLACES.md` §TILING, where any recompute divergence fails the gate until a SPEC-CHANGE
entry shows the re-derivation, and quietly correcting an off-by-one underneath a frozen number is
the move that annex exists to prevent.

---

## INV-294 — The core shuttle car interior

**What:** every absolute dimension of `station/shuttle.py`'s `car` program — the saloon's
3.94 m interior width, its 2.35 m ceiling, the 0.62 m plinth module, the window band's
0.93–1.80 m sill and head, the 4.0 m body-pillar bay, and the ten of them that make the
register's 40 m car.

**Why it is needed:** `docs/gazetteer/LOCATIONS.md` line 364 records the core shuttle car
interior at **authority 1** from `reference/03-sector-blue/Babylon_5_2-22_35a.jpg`, and
`docs/spec/PLACES.md` PLC-102 adopts the same list as the line's *"auth 1 car dressing"*.
Its `module` column reads **`no`** — nothing in the repository built it, and a player who
boarded the station's trunk line found a generic store bay. The frame is a close interior
with a seated figure and is **cropped on both sides**; `tram.py` says so itself where it
declines to measure a car width off it. So it gives proportions and no metres.

**What constrained it — the two rules, and every number follows one of them.**

*Rule 1 — a proportion off the frame, scaled by a constant this project has already fixed.*
The scale is the seat height, `rooms.PROPS["seat"][2]` = 0.45 m. Read at 2× on the crop of
35a's right-hand bench, the floor line is at y = 590 and the cushion top at y = 300, so
**290 px is 0.45 m** and every other vertical reading is quoted against that:

| element | reading (2× crop px) | metres |
|---|---|---|
| plinth top / cushion underside | 220 above floor (y = 370) | 0.341 |
| seat cushion thickness | 70 | 0.109 |
| back cushion top | 555 above floor (y = 35) | 0.861 |
| amber panel sill | 90 above floor (y = 500) | 0.140 |
| amber panel head | 165 above floor (y = 425) | 0.256 |
| amber panel width | 280 (x = 265..545) | 0.435 |
| red skirting at the foot | 40 | 0.062 |
| red trim rail over the backrest | 46 | 0.071 |

*Rule 2 — derived from a clearance the project already states.* The frame shows **one amber
panel per plinth module** with the plinth's seam falling on the seat division, so the module
is one seated person: `tram.SEAT_PITCH_M` = **0.62 m**, read from that module rather than
restated. The panel is then 0.435 / 0.62 = **0.70 of the module**, which is the frame's own
proportion and is not fitted to anything.

The **interior width** is the seating plan the frame shows and cannot be measured from it:
a bench run against each side wall (`rooms.PROPS["bench"][1]` = 0.45), knee room in front of
each (the same 0.62 seat pitch used the other way), and an aisle two people can pass in
(2 × `rooms.WALK_M` = 1.80). **2 × (0.45 + 0.62) + 1.80 = 3.94 m.**

The **ceiling** is `interior_kit.PROVISIONAL["door_height_m"]` + 0.25 = **2.35 m** — a leaf
and the least lintel that reads as one. The corridor's own ceiling is 3.00 m; a vehicle is
lower and this is the number that says so.

The **window band**'s sill is the frame's (the red trim rail sits directly on the backrest:
0.861 + 0.071 = **0.932 m**) and its head is derived so a STANDING passenger sees out:
`budget.DECK["eye_m"]` + 0.10 = **1.80 m**. A seated eye at ~1.20 m is dead centre of it,
which is what LOCATIONS.md means by *"a continuous window band at seated eye height"*.

The **bay** is `tram.WINDOW_PITCH_M` = 4.0 m, the same measurement off the same episode's
rolling stock; the register's 40 m footprint is exactly ten of them, which is a
corroboration and not the derivation. Body pillar `tram.PILLAR_W_M`, skin `tram.WALL_T`,
windscreen rake 24° — all three read from `tram.py` rather than taken again. `_selftest`
asserts each identity, so a change there fails here instead of drifting.

**Door spacing (auth 5).** Three door pairs a side, at bays 1, 4 and 7 — 12 m centres, so
no seat is more than 6 m from a door. Constrained by the line's own derived numbers
(PLC-102: 20.4 m/s peak, 3m52s headway): a trunk line on that headway has to clear a
platform inside its dwell.

**What would overturn it:** any wider frame of the same car — one showing both side walls,
or the car from outside at the platform — would give the width directly and could move it
by a metre in either direction; the seating plan and everything hung on the bodyside scale
with it. A frame showing a door would settle the door pitch. A second interior frame at a
different focal length would let the 290 px scale be checked rather than assumed.

---

## INV-295 — A core shuttle station, and why there is one rather than 4.65 km of tube

**What:** `station/shuttle.py`'s `station` program — a 44.0 × 4.67 m platform, 7.20 m tall,
beside a 4.38 m berth whose floor is 1.10 m down, behind a glazed screen wall.

**Why ONE station.** `docs/spec/PLACES.md` PLC-102 rules it in a sentence and this module
follows it rather than the register's 4,650 m footprint: *"the running tube between stations
is transit envelope, not walkable rooms — the built product is 13 stations + the tube the
cars traverse."* That is the same reading `rooms.bay_span_m` takes of every other place on
the station, and the reason `bespoke.room_shell` translates a module's geometry rather than
tiling it.

**What constrained the dimensions:**

* **Platform length 44.0 m** = the car's own 40 m (PLC-113's register footprint) plus
  `bespoke.APPROACH_DEPTH_M` at each end — the distance this project already uses for
  "a body is standing IN the room rather than in its doorway", here as stopping overrun.
* **Platform depth 4.67 m** = an alighting stream the width of a car door
  (`rooms.PROPS["shuttle_door"][0]` = 1.80), two people passing behind it (2 × `WALK_M`),
  and a seating bay against the back wall (bench 0.45 + knee 0.62).
* **Berth width 4.38 m** = INV-294's car plus two skins of `tram.WALL_T`.
* **Berth floor −1.10 m**, so a car's own floor arrives level with the platform. That is
  what makes a platform have an *edge* rather than a step, and it is why the edge carries a
  nosing, a tactile band and a fascia rather than a painted line.
* **Hall height 7.20 m** = 2 × INV-010's deck pitch. INV-020 made the concourse two decks
  tall on the argument that a public volume is not a 3 m room; a station on the axis of a
  station of 250,000 people is the same argument.
* **Berth roof 3.60 m** — one deck, so the tube is a tube and the hall above it is one
  volume. The illuminator tubes and the truss's serrated rack hang inside it, which is what
  `Babylon_5_2-22_34b` (authority 1) shows: *"a lattice-girder truss ... carrying long
  cylindrical illuminator tubes; its lower edge is serrated — a rack — which is how the
  cars are driven."*
* **Screen doors at the car's own door centres** — the same `DOOR_BAYS` table drives both
  programs, so a car that berths here opens onto them by construction rather than by two
  modules agreeing about a number.
* **13 stops at 387.5 m** on the line map and the stop board: PLC-102's, not a second copy.

**Authority 5** on the whole of it, and on one content decision worth naming: the platform
is separated from the running way by a **glazed screen wall** rather than by a railing.
34b shows the running way as open structure with cars swinging through it, so a station has
to be separated from it; and 35a's own light — amber panels low, a bright band at eye
height — is a lit interior seen through glass, which is what a platform looks like from a
car and a car looks like from a platform.

**What would overturn it:** any frame of a core-shuttle stop. None exists in `00-INDEX`.
A frame showing passengers boarding would settle the platform depth, the edge treatment and
whether there is a screen wall at all; a frame down the platform would settle its length and
whether one station berths one car or a pair.

**Recorded, not fixed — the group scan and a place key.** `materials._scan_generator_groups`
reads every `core_*` string literal in `station/*.py` as a mesh GROUP name, so the register
key `core_shuttle` cannot be written in a generator: it is a place, not a surface, and it
has no material. `directory.py`, `rooms.py` and `transit.py` are all on that scan's
`NOT_GENERATORS` list for exactly this reason. `bespoke.py` is not, so its
`BESPOKE_PLACES` key is assembled from two literals with the reason written beside it, and
`shuttle._selftest` asserts it is a real register key. **The one-line fix is
`"core_shuttle"` in `materials.NOT_GROUPS`**, and it is reported rather than applied because
`materials.py` was another agent's file this session.

---

## INV-296 — How far a bespoke module builds along its own footprint: two modes, and why there are two

**Authority 5 (extrapolation).** Session 4l.

### What was invented

Every place whose module appears in `bespoke.NEAR_END` now carries a declared **axial mode**
in `bespoke.AXIAL`, and the mode decides how much of the register's declared axial footprint
that place's geometry actually spans:

| mode | what it means | places |
|---|---|---|
| **grow** | the module's subject genuinely repeats along the station's axis, so the module is given its own length as a parameter and lays MORE CONTENT — not more copies | `plant` (4), `quarters` (7), `alien_sector`'s gallery, `interior_kit`'s Central Corridor, `zocalo` (2) |
| **one** | the module's subject is ONE ROOM. Its built length is its own, measured off its own mesh, and the shortfall against the register is REPORTED with its reason | `customs` (3), `hospitality` (5), `command_control`, `council_chamber`, `components`' three observation rooms, `alien_sector`'s sealed chamber |

### Why it is that value

**The measurement that forced it.** The 37 places whose module is in `NEAR_END` were building
**625 m of 3,922 m** declared — 16%. `rooms.tiling` answered `n = 1, built_l = bay_span_m` for
every one of them, on the true observation that `bespoke.room_shell` *translates* a module's
geometry onto the assembler's door plane rather than scaling it, so tiling one would slide the
room down the axis instead of growing it. That is an accurate description of the mechanism and
it is an argument for growing the **module**, which is what `AXIAL` does.

**Why not one mode.** A tank farm, a row of quarters off a corridor, a lock gallery, a transit
spine and a run of market bays are all *the same thing repeated along an axis*; Command &
Control, the Council chamber, an observation dome, a customs hall and a bar are not. Thirteen
copies of C&C is not a bigger C&C, it is a fault that no triangle count, no extent and no
coverage number can see — which is precisely the class of defect `deck.py --degeneracy` was
written for one level up. So the answer for those is a **shorter room that says why**, and
`rooms.py --footprint` prints the sentence next to the metres on every run.

**What constrained the grow modules.** Each takes its own length in its own vocabulary and
snaps to its own quantum, so `n = 1` reproduces the pre-4l geometry exactly:

* `plant.room_cell(span_m=)` — the cell's axial length; the tank count, the catwalk width,
  the frame positions and the walkway centre were already expressions in `z0`/`z1`. Quantum is
  `rooms.bay_span_m`'s representative bay, which is what it clamped to before.
* `quarters.run(rows=)` — `run` lays units along the **ring** and was one unit deep, so a
  120 m residential footprint built 5.22 m of itself. Quantum is `row_pitch_m` = unit depth +
  two walls + the residential corridor width.
* `alien_sector.gallery(length_m=)` — one longer corridor with more locks at their authored
  pitch, not four galleries end to end. Quantum `GALLERY_LEN_M` = 30 m.
* `concourse.central_corridor(bay_mult=)` — `program()['bays']`; quantum
  `rib_spacing_m * RIB_BAYS` = 24 m.
* `zocalo.zocalo_run(bays)` — quantum `params()['bay_length_m']`.

**What decides how far a grow place goes.** `budget.DECK["visible_all_tris"]` = 300,000, the
same frame allowance `rooms.tiling` spends on the generic half and for the same stated reason.
The ladder is `rooms.tiling`'s: **shell, articulation, fixtures and declared interactables run
the WHOLE length** — they are what the place is, and they are the cheapest layer — while
`dressing` and `populace` reach a **band measured from the door**, because those two are the
highest-triangle, lowest-silhouette layers and are exactly what a streaming system instantiates
rather than bakes.

**What would overturn it.** A module moving from `grow` to `one` or back is a content decision
and needs a line in `AXIAL` with its reason; the gate does not care which it is, only that the
declaration and the geometry agree. If room crowds ever become instanced the way
`deck.CORRIDOR_INSTANCED` already makes the corridor crowd instanced — 88% fewer triangles —
the band arithmetic changes by an order of magnitude and every capped place should be
re-derived.

### What it fixed that was not the headline

`deck.room_shell_for` sizes a room's **collision** from `rooms.built_span_m`, which returned
the generic representative bay for every composed place. `council_chamber`'s mesh is 22.38 m
and its collision shell was 15.00 m; `obs_dome_1`'s mesh is 16.55 m and its shell was 6.29 m.
That is render geometry outside its own collision — hard rule 4's failure mode, in the one
direction `deck.room_geometry` had left open. `bespoke.axial_span_m` measures the module's own
mesh, so the two agree by construction, and `rooms.py --footprint --legacy` shows the old
answer failing on exactly those rows.

---

## INV-297 — A baked body is 7,300 triangles, and it is what decides how long a room can be

**Authority 5 (extrapolation, measured).** Session 4l.

### What was invented

`bespoke.BAKED_BODY_TRIS = 7_300` — the triangle cost of one inhabitant placed by
`populace.populate` at `ROOM_LOD`, including their wardrobe and their pose — and
`bespoke.composed_cost`, which prices a candidate room length as
`shell + MAX_DRESS_TRIS + occupancy(area) x BAKED_BODY_TRIS` before a triangle is emitted.

### Why it is that value

Measured on composed rooms rather than on a probe: `council_chamber` emits 529,616 triangles of
`npc_*` over 70 people (7,565 each) and `customs_north` 188,928 over 27 (6,997 each). 7,300 is
the middle and the spread is stated.

**A first probe read 3,515 and was wrong by half, which is the transferable part.** It stood 30
bodies on a bare shell with no furniture in it. A person placed against real furniture SITS, and
a seated clip plus a wardrobe is about twice a standing bare body — so *the probe measured the
probe*. The same trap `bespoke.NEAR_END_UNKNOWN` records for `plant`: **a measurement taken
through a call describes the call.**

### Why it matters

`populace.occupancy` is a crowd **density** — people per square metre at an hour — so a room
grown 32x in area wants 32x the people and 32x their triangles. At 7,300 each that is the whole
frame allowance several times over, and it is the term that decides everything: `plant.room_cell`
is 688 triangles at 13.8 m and 1,736 at 110.5 m, which is 150 triangles for a unit of *room*
against 7,300 for one *person* standing in it. Pricing growth on the shell alone let every place
reach its full footprint and multiplied the station's crowd with its area; pricing the whole room
at full furnishing capped `plant_zone` at 6 units of its 32. Neither is what `rooms.tiling`
does, and its ladder — full length of shell, a door-anchored band of furniture and people — is
what both halves of the station now use.

### What would overturn it

Instanced room crowds. `deck.CORRIDOR_INSTANCED` already makes the corridor's walkers instanced
at 88% fewer triangles and room occupants are still baked; if room occupants join them,
`BAKED_BODY_TRIS` is the wrong constant and every band in `bespoke.axial_units` is
recomputed from the new one. A change to `populace.ROOM_LOD` does the same. `bespoke._selftest`
re-measures the constant against a composed room and fails if it has moved more than 25%, so it
cannot go stale silently.

## INV-298 — the three player stances, and what each is worth

**What.** A player answers a topic with one of three stances -- `ask`, `press`, `let_go` --
and they differ in what they are WORTH rather than in tone: `ask` returns the topic's
qualitative half, `press` returns the number that decided the topic's own salience and can be
refused, `let_go` returns nothing and ends the conversation.
**Why.** `docs/spec/PEOPLE.md` DLG-05 names the three by name and says *"Choices are stances,
not flavour"*; against zero player utterances, the smallest thing that satisfies that is a
choice whose outcomes differ in information rather than in wording. Assigning `press` the
salience input is what makes it non-arbitrary: `_topic_port` chose the liner because
`traffic.hall_rate` reads x9.7, `_topic_beat` chose the beat because `security.on_duty` reads
174, and the first line never says either number. So pressing is *how you learn why they
brought it up*, and dropping it costs you exactly that.
**Overturned by.** DLG-05's remaining terms (role work-lines, SHOW-PAPERS, the buy/sell and
refusal sets) landing, or CAST-05 ledgers existing -- at which point a stance must move a
ledger and not only an answer. Play testing on whether three is the right number.
**Authority 5.**

## INV-299 — a press yields when warmth exceeds terseness

**What.** `dialogue.yields_to_press(reg)` is `reg.warmth > reg.terseness`, and nothing else.
**Why.** Both sides are already derived and neither is new: `warmth` is `friction.SEVERITY`'s
separation ladder inverted (the multiple the crowd already keeps its distance by) and
`terseness` is the `_ROLE_REGISTER` row plus the `_SPECIES_VOICE` delta. A comparison of two
existing numbers introduces no third constant, so there is nothing to tune and nothing to
argue with -- `deck.py --degeneracy`'s argument for a hash over a threshold, applied to a
register. It also lands the right fiction without being asked to: a Narn dock worker at this
datum (0.60 against 1.00) gives you nothing, a Centauri merchant (0.60 against 0.10) gives you
the number, and Kosh (1.00 against 1.00) never yields to anybody.
**The alternative was measured and rejected**, which is the part worth keeping: the first form
was `warmth >= 0.75 AND terseness <= median(_ROLE_REGISTER)`. Both halves were derived and the
AND is multiplicative, so on the shipped deck's own 21-person cast it yielded **1 time in 21**
and on the 73-person customs cast 16 in 73. A stance that pays out 5% of the time is not a
choice a player makes. The comparison gives 120/157 across the three baked casts, with 37
deflections -- a split, which is what a stance needs.
**Overturned by.** A measured yield rate that reads as either free or hopeless in play; or
`friction.SEVERITY`/`_ROLE_REGISTER` being re-derived, since the cut moves with them by
construction. `dialogue.py --converse` fails if the press ever has ONE outcome across a whole
cast, so a table change that collapses it cannot pass silently.
**Authority 5.**

## INV-300 — a register name is rendered for speech

**What.** `dialogue._spoken(name)` drops any parenthetical and any alternative after a slash
before a register place name is put in a mouth: "Transport tubes / lifts (between levels)"
is said as "Transport tubes", "Security posts / checkpoints" as "Security posts".
**Why.** 22 of `directory.PLACES`' 128 rows carry a disambiguating slash or a parenthetical
count, because the register's job is to be unambiguous across 128 places. Spoken verbatim it
reads as a database field -- the same fidelity failure as the era topic naming an episode
number, which this session also found and fixed. The first alternative and no parenthetical is
what a person says. It is a RENDERING of the register value and not a second name, so the two
cannot drift.
**Overturned by.** A row whose meaning lives after the slash rather than before it, which would
make the first alternative the wrong one. Nothing in the current 22 is of that shape.
**Authority 5.**

## INV-301 — the price of a named good, in three factors with one anchor

**What.** `economy.price(good, place)` is `CLASS_BAND[klass] x SUPPLY_MULT[supply] x
VENUE_MULT[sector]`. Two class bands are `LAW-CRIME-DOWNBELOW.md` §7.1's own rows verbatim
(a Zocalo cart meal 1–2 cr, a Downbelow bunk 1 cr/night) and the other ten are one stated
step off them: a staple is HALF the meal band, because a cart selling a 1–2 cr plate cannot
have paid more than about half of that for it and still be a cart; a drink is 60% of the
meal band, bracketed above by the plate and below by the bunk; a liturgical import is 1/40 of
the passage-home band, which is the step that makes G'Quan Eth an event rather than a
grocery; hardware sits under a day's casual pay, or a docker cannot own their own tools.
`SUPPLY_MULT` is 1.00 for anything grown or made aboard and **1.60** for an import, because
§7.4 puts the drum at half the station's food by mass and the other half on a freighter.
`VENUE_MULT` is the CUBE ROOT of the sector's rent tier over Red's, from the same §7.1
ladder — cube-rooted because a drink is mostly the drink and only partly the roof, which
puts the Green-sector houses at ×1.71 of a Red one.
**Why.** Because a price board with numbers nobody can trace is the same defect as a
schematic with no scale bar. Every factor above lands on one published table and the two
rows the table states for goods are asserted, not assumed: `economy.price_check()` fails if
a drum-grown plate at a Zocalo counter leaves the staple band or a house drink leaves the
bunk-to-meal bracket, and its negative control (route multiplier 0.75 → 3.0) fires it.
**What is weakest.** The 60% drink ratio and the cube root are the two free choices; both
are bounded by checks rather than by sources. The 1.60 import multiplier is the strongest of
the three because §7.4's half-and-half split is an explicit sentence.
**Overturned by.** Any on-screen price for a specific good — one Zocalo stall board or one
bar tab would replace a whole class band. Any stated pitch, lease or freight rate would
replace `VENUE_MULT` or `SUPPLY_MULT` outright.
**Authority 5.**

## INV-302 — a counter is a part of a place, and how big a part

**What.** `economy.retail_m2(place)` caps a vendor's selling floor at
**44 × 225 = 9,900 m²** and multiplies by **0.05** for a place whose functions include
`black_market`. `stock_list` carries one line per 12 m² of that, floor 3 and ceiling 14, and
a place whose FIRST declared function is not a selling function gets the floor.
**Why.** `directory`'s footprint is the PLACE, not the counter, and using it directly gave
Downbelow — 654,370 m² of camp — **235,572 retail transactions a day** against 20,000 people
with no money. The cap is solved from the only stated count in the spec: PLACES §0.3 says
the goods vocabulary "feeds the Zocalo's **44 stalls**", and `bar_unnamed`, the authority-1
bar, is one counter with a 225 m² register footprint. 44 × 225 is a quarter of the Zocalo's
own 39,298 m² and the other three quarters are concourse, gallery and circulation — which is
what the Zocalo is. Nothing aboard has more counter than the Zocalo. The 0.05 is SYS-06's
own title made numeric ("**a route, not a room**"): under-counter trade has to be big enough
to be worth LAW-CRIME:858-879's five-station route and small enough that customs is not
visibly failing. The first-function rule needs no new data at all — the register already
orders a row's functions by what the place is for, which is why `post_office`
(`mail`, `commerce`) stops being a grocer.
**Overturned by.** A stall count for any place other than the Zocalo; any figure for
contraband volume; a frame showing a counter run whose length contradicts 225 m².
**Authority 5.**

## INV-303 — a crate, and how much of the day's tonnage is retail

**What.** A container is `rooms.PROPS["container"]`'s own 2.40 × 1.20 × 1.20 m at
**250 kg/m³** = **0.864 t**, holding **960 saleable units** at a nominal 0.9 kg each. A
freight hull lands `5.4545 t/h × its own dwell`; a passenger hull lands `souls × 40 kg` of
baggage; a tanker lands none, because slush is pumped. Retail consignments are sized by
DEMAND — a counter's line is topped up by what it sold — so **0.9% of the day's crates go
behind a counter** and the rest are stores.
**Why.** The volume is the station's own modelled crate rather than a number. 250 kg/m³ is
the low end of mixed general cargo (water is 1,000, packaged dry food 300–500, machinery
800+, and a mixed crate is 40–60% void) and the low end is right because §7.4 says the
import is "food, packaging, supplies, spares". The 5.4545 t/h is not chosen at all: it is
§7.4's own worked example — "across 20 bay-class freighters a day that is ~60 t each" — over
`traffic.MANIFEST`'s own 8–14 h dwell for that row, so the anchor is a rate and every other
freight class is that rate for as long as it is alongside. The 40 kg allowance is bigger
than an airline's and smaller than a household's, for a move between systems.
**AND THE MODEL FALSIFIES ITS OWN SOURCE, which is the useful part.** Summed over the
manifest the station lands **1,757 t/day**. §7.4 states 4,000–5,000 t/day: ~1,200 consumed
plus "2–3× that again" transshipped. The manifest reproduces the CONSUMED figure and has
**no hulls for the transshipment to arrive on** — see C-013. `economy.cargo_check()` reports
the gap on every run rather than closing it by picking a reading.
**Overturned by.** Any stated container mass or ship tonnage; a resolution of C-013.
**Authority 5.**

## INV-304 — what a gang can move, what it is paid, and when it is carded

**What.** A gang of six moves **6.31 crates/h** (`dockwork.CRATES_PER_GANG_H`). Handling
multipliers are containerised 1.00, bulk 0.80, bonded 1.35, perishable 1.00, hazmat 1.80.
The caller's chalked rate maps that mix onto the **stated** 8–15 cr/day casual band. A
casual is carded after `economy.GUILD_SHIFTS_PER_WEEK` = **5** shifts.
**Why.** The crate rate is a CONSTRAINT rather than a choice: a berth is released when the
ship leaves, so a gang must clear a hull inside its own dwell, and the manifest's mean bay
freighter (60 t = 69.4 crates over 11 h) sets the rate. It cross-checks: 69 crates in 11 h is
one crane cycle every 9.5 minutes with a gang of six, which is a hook-lift-traverse-set-scan.
The multipliers are the handling steps ROLE-03 itself names for each class (the customs seal
read into the terminal; the suit-check and the suit worn after it; transshipment that never
leaves the bay) rather than difficulty knobs. **The chalked rate introduces no number at
all** — the caller pays the top of the published band for the jobs nobody wants and the
bottom for the easy ones, so the band's own width finally means something. Five shifts is
one guaranteed week's worth of turning up, which is the shortest span over which a caller
sees a man be reliable and short enough that a player reaches it in a session.
**AND THE WAGE ANCHOR IS TIGHTER THAN THE BAND IT IS QUOTED AS.** LAW-CRIME:748 says the
300–800 cr passage must be 30–100 days of casual labour. Read as a constraint that pins the
rate to **8–10 cr/day**: the published band's FLOOR is reproduced exactly (800/100 = 8) and
its top five credits are not derivable from the anchor. `economy.wage_check()` prints both
and `_selftest` asserts the gap is non-zero, so the discrepancy cannot quietly disappear.
The published 8–15 is what is used, because two documents carry it.
**Overturned by.** Any on-screen dock wage; any figure for gang size or crane cycle; a
resolution of the 8–10 / 8–15 tension in favour of either.
**Authority 5.**

## INV-305 — a lurker's purse is drawn from the left tail

**What.** `player.credits_for(npc_id, role_key)` confines the draw to
`[0, PASSAGE_HOME_CR)` when the role is in `resident.NO_STATUS_ROLES` (lurker, refugee).
**Why.** This is a correction, not an addition. The draw is the ARRIVAL distribution, fitted
to §6.6's 1% leak, and it knew nothing about who the arrival became — so
`player_from({"role": "lurker"})` produced a Downbelow squatter holding **4,666 credits**.
Canon's entire explanation of the underclass is that they "did not have the money to afford
a ticket back home", so somebody in a no-status role is BY DEFINITION under that line. The
left-tail confinement leaves §6.6's solved skew exactly as it was — the leak is a statement
about arrivals and this is a statement about what an arrival has become — and the role set is
imported from `resident` rather than restated, so it cannot drift from `arrival.py`'s.
**Overturned by.** Nothing likely; a canon lurker with money would be the counter-example,
and Jinxo (a skilled lurker who never leaves) is about skill, not solvency.
**Authority 5.**

## INV-306 — the eight corridor verbs, and which side of a grievance takes which

**What.** `npc/faction.VERBS` is a closed list of eight things a body does when it meets
somebody it has a grievance with — `widen`, `cross`, `hold`, `aside`, `reverse`, `clear`,
`quieten`, `none` — and `npc/faction.RESPONSES` assigns **two** of them, one per side, to
every row of `friction.PAIRS`.
**Why.** `friction.py` produces a **distance**, which is the right primitive and is not a
behaviour. FACTIONS.md §12 and `docs/spec/PEOPLE.md`'s FAC blocks describe the behaviours in
sentences, and every verb here is quoted from one: *"The Narn stops, turns, and does not
yield the corridor. The Centauri crosses to the far side"* is `hold`/`cross`, and it is why
the assignment is **per side and asymmetric** — answering that row symmetrically plants the
Centauri in the middle of the corridor, which is the opposite of what the source says. The
list is closed at eight because a ninth would be a movement with no sentence behind it.
Where a source gives no yielder the rule is one line, applied everywhere: **the party on its
own faction's territory does not yield** — `PEOPLE.md` gives every FAC block a Territory line
of register keys, so "whose corridor is this" is already a fact the register can answer, and
a corridor serving `docking_bays` is the Dockers' Guild's ground in a way it is not the Psi
Corps'. One verb is deliberately not geometry: `quieten` is on the list because §12's
Nightwatch sentence is about a voice, and inventing a movement for it would be worse than
carrying a state change.
**A STOPPING VERB IS A HEAD-ON VERB.** Every sentence behind `hold`, `aside`, `reverse` and
`clear` describes two parties coming *at* each other — "does not yield the corridor", "leaves
before the other arrives", "reverse *out of* a corridor a patrol *enters*". Overtaking
somebody walking the same way is not that, so on a same-direction encounter those four
degrade to their walking equivalents and the degradation is recorded, not silent.
**Overturned by.** Any frame showing who gives way in a B5 corridor; a docker giving way to
a passenger on a dock deck would overturn the territory tiebreak specifically.
**Authority 5.** The FACT of each antagonism carries FACTIONS.md's own authority; the verbs
are the design, exactly as §12 says the behaviours are.

## INV-307 — a Narn and a Centauri cannot pass in a ring corridor, and that is arithmetic

**What.** The escalation policy in `npc/encounter._resolve`: a pair whose tabled separation
exceeds what the corridor can physically give does not "try harder", it takes the row's
stopping verb.
**Why.** This is a **derivation before it is an invention** and the derivation is the point.
`collision.corridor_shell` measures blue/0/0's half-width at **1.0806 m**, so the widest two
ordinary bodies can be centre-to-centre with both inside the walls is `2 x 1.0806 - 0.20 -
0.21 =` **1.64 m**. `friction.separation_m("narn", "centauri")` is `4.0 x 0.45 =` **1.80 m**.
Nobody chose those two numbers to disagree and they disagree by 0.16 m, on every ring
corridor on the station. So FACTIONS.md §12's sentence for that row is not a distance at all,
and could not have been: the behaviour in the source **is** the resolution of an impossible
geometry. The same sum ranks the rest of the ladder without a second decision — `ceremonial`
2.70 m is impossible (the corridor clears), `high` 1.35 m fits with 0.29 m to spare,
`medium` 0.855 m is ordinary give-way. That is FACTIONS.md's own 95/5 split falling out of
one measurement rather than being tuned to it. Measured over a station-hour on blue/0/0:
Narn/Centauri pairs pass **1.14 m** apart against **0.46 m** for pairs with no grievance and
**0.47 m** for the same crowd with the table off.
**Overturned by.** A wider measured corridor — `INV-020`'s 9 m concourse *can* hold the pair,
and this predicts that the same two people pass each other normally there and stop in a ring
corridor. A frame of the two passing comfortably in a standard corridor would overturn it.
**Authority 5** for the policy; the two numbers it rests on are measured and tabled.

## INV-308 — how fast somebody side-steps, and how long a stopped walker stands

**What.** `encounter.LATERAL_STRIDES_PER_SHIFT = 0.5`, giving a per-walker lateral rate of
`body half-width / (stride cycle / 2)` — 0.34 to 0.42 m/s on the corridor's own bodies. A
stopped walker stands for `2 x want / closing speed + faction.STOP_RESTART_S`, with
`STOP_RESTART_S = 2.4`.
**Why.** Neither is a new number. The lateral rate is the walker's **own gait**: a person
changing lane moves sideways about half a shoulder per stride, so both terms come from
`animation.walk_clip`'s cycle and the individual's own measured mesh, and a species with
broader shoulders and a longer stride side-steps at its own rate rather than at a constant.
The hold is the time the other party spends inside the distance the row asks for — nothing
else is being waited for — plus what it costs to stop and start again, which at a
comfortable 1.0 m/s² either side of 1.2 m/s is 2 x 1.2 s. On the Narn/Centauri row that is
**3.9 s**: you stop, they pass, you go on. **The first cut of this held from first sight to
last sight and stood a Narn in a corridor for ten minutes**, which is not restraint, it is a
bug, and it is recorded here because the wrong version looked perfectly plausible in a log.
**Overturned by.** Any measured pedestrian lane-change rate; any frame timing a give-way.
**Authority 5.**

## INV-309 — the Guild card is a share of the dockworker role, not a second population

**What.** `faction._flag_guild` draws the 1,500 guild-carded core (`GUILD_CARDED`) as a
deterministic share of the 9,650 dockworker-role heads, off the same `resident._u` hash every
other per-person flag uses.
**Why.** `PEOPLE.md` FAC-06 gives three denominators, each true of a different set — 9,650
role heads, 1,500 carded, ~1,200 on EA payroll — and a card is not a job. A share is the only
honest reading of a population with no stated rule, and drawing it off the id is what
`security.wears_armband` already does for the armband, so a carded docker is the same person
on every run and on every machine. **A card is a SUBSET of a job and not an addition to it**:
`head_count` therefore skips a flag whose `_FLAG_SUBSET_OF` role is already counted, because
the first version added them and reported 11,550 dockers on a station that has 9,650.
**Overturned by.** Any stated rule for who is carded (seniority, sector, species).
**Authority 5.**

## INV-310 — a roving patrol is a duty cycle over ring deck arcs, not a fixture

**What.** `security.patrol_duty_cycle(hour) = roving_pairs(hour) / ring_decks()`, and
`security.corridor_patrol` turns it into timed visits: a two-officer pair enters a named
arc at a seeded second, walks its length, and leaves.
**Why.** LAW-CRIME §2.5 defines the beat as *"one outermost-ring deck arc, out and back"*, so
a roving pair occupies **one** arc at a time. `roving_pairs(13.0)` is 59 and
`navigation.cell_plan` builds **251** ring decks, so any one arc has a patrol on it 23.5% of
the time — and at 03:00, 16.3%. That reproduces the shape LAW-CRIME states in prose
("Zocalo continuous, Red and Blue 30 min, Green 60 min, Grey 3-4 h, Downbelow zero") without
any of those four numbers being typed anywhere, because the Zocalo's continuity comes from
`POSTS` and Downbelow's zero comes from `NO_POST`. **The fractional visit is not rounded
away**: rounding 0.23 to zero is how a real duty cycle becomes "no patrol, ever" on every
deck the station has. The consequence is the content: a patrol is an **event** in a corridor,
and the reason Downbelow is Downbelow is that nobody comes.
**Overturned by.** A stated patrol frequency per district; a resolution of C-011 (the
gazetteer's own 35-vs-45 pairs).
**Authority 5.**

## INV-311 — an encounter begins at the commit distance, not at the sight line

**What.** `encounter.commit_m(want, lat_rate, closing) = (want / 2) / lat_rate * closing` —
10.0 m on blue/0/0 — is the range at which two walkers become an encounter.
**Why.** The first cut used `populace.corridor_sight_m`, which is 60.5 m on a Blue deck, and
with a person every 9.5 m that makes "an encounter" mean *everyone in view*: thirteen
simultaneous encounters per walker and a denominator that measures the crowd's density rather
than anything anybody did. An encounter begins where the **manoeuvre** has to begin — to open
`want` metres of lateral gap before contact each side must travel `want/2` sideways at its
own rate, and in that time the pair closes at `closing`. Wider than that is *seeing*
somebody, which is not an encounter; narrower is too late to avoid them, which is a
collision. It lands at twice the derived earshot (5.6 m, from `audio.py`'s 60 dBA talker
against a 45 dBA circulation space) and a sixth of the sight line.
**Overturned by.** A measured pedestrian avoidance-onset distance.
**Authority 5.**

## INV-312 — the Nightwatch row needs an armband PRESENT, not merely an era

**What.** `friction.strongest(..., witness=)` gates the `("human", "*")` row on an armband
being within earshot. **The default, `witness=None`, keeps the old era-only reading**, and
`npc/encounter.py` is the only caller that passes the new one.
**Why.** FACTIONS.md §12's row reads *"a human talking with aliens lowers his voice **when an
armband passes**"*. That is two conditions and this project had only ever applied the first.
The consequence is not small: `populace._clear` takes `max(need, separation_m(...))` for
every pair in every room, so **85 humans are held 1.35 m off 49 aliens** in the blue/0/0
corridor with no officer within seven kilometres, and on that corridor the row accounted for
**14,286 of 16,683** friction-carrying passes an hour — 86% of all friction on the station,
from a sentence about a passing armband. Who is wearing one is already decided by
`costume.costume_for(...).nightwatch`, which covers the 35% of officers *and* the civilian
informer rate, both era-gated, so the witness costs no new number. **The default is left
alone deliberately**: flipping it moves every human away from every alien on 128 baked decks,
which is a re-bake and not a patch, and doing it silently while other work was in flight
would have been the worse error.
**Overturned by.** A reading of §12 in which the chill is ambient rather than triggered — the
row's own text is the evidence either way. Closing it properly means re-baking the decks and
re-running `deck.py --sweep`.
**Authority 5** for the witness condition; **1 (S2E22)** for the antagonism itself.

## INV-340 — The identicard tier ladder: six rungs, and what each one gates

**What.** A person's standing aboard is one of six rungs — ACCREDITED / CITIZEN / RESIDENT /
TRANSIT / SANCTUARY / NO STATUS — plus a DETAINED custody state. Each rung gates three things:
which of the 128 register places admit you (128/126/116/66/35/33), which of the 13 counters
serve you (13/13/13/10/9/4), and the rent tier of `economy.LADDER` you may take a tenancy at.
**Why.** MASTER-PLAN P1-G2 asks for "the identicard tier ladder". Every rung is a READING of
card state through `arrival.entry_class` — this project's one card reader — plus employment
plus role; there is no second visa parser and no stored tier field.
**Constrained by.** The rungs are not free: five of the six are the five classes
`arrival.entry_class` already distinguishes (auth 1 for the card fields themselves), and the
sixth (ACCREDITED) is LAW-CRIME 4.1's diplomatic immunity at auth 4. What is extrapolated is
only the ORDERING and the gating sets.
**Overturned by.** Any depiction of a station access class the card does not carry; any
footage of a non-EA national in a place this ladder closes to them.
**Authority 5.** `station/consequence.py::TIERS`, gated by `--gate` (34/34).

## INV-341 — Sector access floors, from LOCATIONS.md P-05

**What.** Blue admits TRANSIT and above, Green and Grey admit RESIDENT and above, Red and
Yellow admit the floor rung. An explicitly-open function (`informal_residence`,
`black_market`, `organised_crime`, `immigration`) overrides the sector floor.
**Why.** P-05 states the rule — "Security checkpoints at every sector boundary and at every
lift lobby serving a restricted ring. Blue is explicitly access-restricted, and the Alien
Sector is airlocked" — and gives no per-sector class.
**Constrained by.** Blue cannot be higher than TRANSIT because a lawful visitor arrives
THROUGH Blue and cannot be barred from the hall they are processed in. Green is where
`security.POSTS` already puts a checkpoint pair. Grey's restriction is stated at authority 4.
The override exists because nobody checks a card to get into a squat — LAW-CRIME 2.4's last
row is "Downbelow: NO PERMANENT POST", by design.
**Overturned by.** Footage showing free movement across a sector boundary; any source
placing a checkpoint in Red or Yellow.
**Authority 5.** `station/consequence.py::SECTOR_MIN`.

## INV-342 — A licit counter reads the card, so the floor rung cannot buy

**What.** Every counter whose place does not declare `black_market` / `organised_crime` /
`black_market_fringe` / `crime` refuses a NO STATUS card. Four of the station's 13 vendors
serve the floor rung and all four are unchecked ones.
**Why.** TRAFFIC-AND-CUSTOMS 6.4 (auth 4) makes the identicard simultaneously passport,
licence, medical file AND CREDIT CARD — so paying and being identified are the same act and
cannot be separated. That is what makes the floor rung economically real rather than merely
poorer.
**Constrained by.** `resident.leisure_places` already implements the destination half of this
rule (it adds the crime venues back for `NO_STATUS_ROLES` because FACTIONS 11.4 says the black
market's clientele IS the people a reader turns away). This is the same rule at the till.
Exactly ONE rung is excluded: SANCTUARY holders hold a card that reads, and 7.1 prices them a
1 cr/night dosshouse bunk, which is a business taking money.
**Overturned by.** Any depiction of cash or an anonymous credit chit aboard.
**Authority 5.** `station/consequence.py::COUNTER_MIN`, `sells_to`, `purchase`.

## INV-343 — One discretionary identicard check per officer-hour

**What.** An on-duty officer makes one discretionary card check an hour. Over the ~3,600
officer-hours a station-day that is ~3,600 checks, against the ~12,600 transactions/day the
two customs halls already run — so discretionary checking is 22% on top of the mandatory kind.
**Why.** LAW-CRIME 2.7 calls the identicard check "the commonest security interaction on the
station and the one a player will see most" and gives no rate.
**Constrained by.** FROM ABOVE by the brig: 3.1's 24-40 cells times the median hold is the
steady-state custody population, and checks × P(fail) × P(detained|fail) must fit inside it.
`brig_check()` computes it (12.7 of 40, 32%) and the gate's fifth negative control raises the
rate 100× and shows the brig overflowing to 991. FROM BELOW by 2.7's own sentence: the check
count must exceed the detention count by orders (3,600 against 19).
**Overturned by.** Any figure for stop-and-check volume aboard.
**Authority 5.** `station/consequence.py::CHECKS_PER_OFFICER_HOUR`.

## INV-344 — One hour to book a prisoner into the brig

**What.** Between the escort arriving and the case joining the Ombuds docket, one station-hour.
**Why.** LAW-CRIME 4.3 step 4 makes the jurisdiction check "the station's characteristic legal
event" and places it at Security Central between detention and the hearing, without a duration.
**Constrained by.** Below by 3.1's own fittings list — a reader outside every door, a camera,
and an atmosphere assignment for a non-oxygen prisoner (3.1: "at least three atmospheres") —
each of which is a step. Above by 3.1's "hours to days" bracket being about the HOLD and not
about the booking.
**Overturned by.** Any depiction of a booking-in sequence.
**Authority 5.** `station/consequence.py::BOOKING_H`.

## INV-345 — A conditional permission survives one ordinary conviction, not two

**What.** A TRANSIT visa, a SANCTUARY grant or a job-backed RESIDENCY is withdrawn on the
SECOND grade-2 conviction or on the FIRST grade-3 one. An EA CITIZEN and an ACCREDITED
diplomat cannot be revoked at all.
**Why.** MASTER-PLAN P1-G2 requires that "visa revocation exists and can actually happen to
you" and no source states the grounds.
**Constrained by.** LAW-CRIME 2.7 rung 3 — "Move on. No arrest, no record. The standard
Downbelow-in-a-commercial-area outcome" — so a single ordinary offence cannot be terminal or
the ladder has no middle; and 4.3 step 6 listing "transfer off-station" among the ORDINARY
disposals, so it cannot take many either. The two NON-revocable rungs are the sourced half:
4.1 makes the station EA sovereign territory (a citizen enters by right and has no visa on the
card), and 4.3 step 4 says an ambassador's file dies.
**Overturned by.** Any depicted visa cancellation and its stated grounds.
**Authority 5.** `station/consequence.py::REVOKE_ON_ORDINARY`, `REVOKE_ON_SERIOUS`, `REVOCABLE`.

## INV-346 — One failed identicard check in five ends in detention

**What.** `DETAIN_ON_FAIL = 0.20`. The other four end at 2.7's rung 3, "move on".
**Why.** 2.7's ladder has detention as a distinct rung above the check, and gives no split.
**Constrained by.** 2.7 naming rung 3 "the standard Downbelow-in-a-commercial-area outcome",
so move-on must be the large majority; and detention existing at all as a distinct rung, so it
cannot be zero. `brig_check()` is what stops it drifting upward — raise it and the sourced
24-40 cells overflow.
**Overturned by.** Any figure for arrests per stop.
**Authority 5.** `station/consequence.py::DETAIN_ON_FAIL`.

## INV-347 — The fine ladder is denominated in days of casual labour

**What.** Grade 1 = 1 day (8-10 cr), grade 2 = 7 days (56-70 cr), grade 3 = 21 days
(168-210 cr). Grade 4 is off the ladder: the disposal is transfer off-station.
**Why.** LAW-CRIME 4.3 step 6 lists "fine" as a disposal and no source gives an amount.
Days of casual labour is the only unit 7.1's price table gives for what a person can pay, and
7.1's own load-bearing row is built the same way ("passage home must be 30-100 days of casual
labour with nothing spent").
**Constrained by.** CEILING, hard: a fine at or above the cheapest passage home (300 cr) is
deportation dressed as a fine, by TRAFFIC-AND-CUSTOMS 6.6's exact mechanism — someone who
could pay it could have left, and someone who cannot is now a lurker. At the wage band the
passage anchor itself pins (`economy.casual_constraint()` = 8-10 cr/day), 30 days is the most
that stays a fine; 21 leaves 90 cr of headroom. FLOOR: the smallest fine must exceed the wages
the hold already cost — 8 cr against 6.6 cr over the median 15.4 h hold. The week is FACTIONS
2.3's mean transient stay, so a grade-2 fine costs a visitor the visit.
**KNOWN AND REPORTED, NOT TUNED:** the floor clears the MEDIAN hold and not the MEAN (10.2 cr
over 24.5 h, dragged by the deferral tail) — so for a case that defers, the detention is a
heavier penalty than the sentence. That is 4.2's complaint about deferral arriving as
arithmetic. The gate asserts the median and prints `floor_ok_on_the_mean=False`.
**Overturned by.** Any stated Ombuds fine.
**Authority 5.** `station/consequence.py::FINE_DAYS`, `fine_bounds_check`.

## INV-348 — Deferral: 22% of cases, re-deferring at 0.7884

**What.** 22% of hearings are deferred on jurisdiction; a deferred case defers again with
probability 0.7884, each deferral costing one more 24 h sitting cycle.
**Why.** LAW-CRIME 4.2: "Many of the cases had to be deferred as conflicts of jurisdiction
came up between the humans and aliens." No rate given.
**Constrained by.** The SHARE is derived rather than chosen: applicable law is Earth Alliance
law (4.1), so the conflict is a non-EA defendant, and the arrested population is 6.2's
Downbelow mix at "roughly 78% human" (8.1 puts 90% of crime there) — giving 22%. That this
lands on "many" rather than "a few" is the check. The RE-DEFER probability is SOLVED, not
chosen, against 3.1's two brackets for the same distribution: P(hold >= 14 days) = 0.01 given
the 22% share, i.e. q = (0.01/0.22)^(1/13) = 0.7884. Realised: median 15.4 h ("hours to a few
days") and p99 13.6 days ("weeks"). The gate's fourth control sets q=0 and the p99 falls to
2.0 days, so 3.1's "weeks" becomes unreachable.
**Overturned by.** Any figure for Ombuds docket throughput or deferral rate.
**Authority 5.** `station/consequence.py::DEFER_SHARE`, `DEFER_AGAIN_P`.

## INV-349 — A medlab reads a card, which is why Franklin's clinic existed

**What.** `medical` and `surgery` functions require SANCTUARY or above; `triage` does not.
**Why.** TRAFFIC-AND-CUSTOMS 6.4 (auth 4) makes the identicard the MEDICAL FILE — one of the
nine fields on the authority-1 prop — so a ward draws against it and a card that does not read
cannot be treated on one.
**Constrained by.** LAW-CRIME 7.3 is explicit that Franklin ran a free clinic, "a charitable
service, unofficial, at a doctor's own initiative". This gate is the gap that clinic existed
in, and the derivation runs the right way round: the sourced institution explains the rule
rather than the rule being invented to justify it. `triage` is deliberately excluded —
emergency care is not a border.
**Overturned by.** Any depiction of a stateless patient treated in a station medlab.
**Authority 5.** `station/consequence.py::GATED_FUNCTIONS`.

## INV-350 — The fault rate is bounded by the maintenance roster, not by an invented MTBF

**What.** A declared interactable needs a corrective visit every 365 days. Against the
182,905 instances `rooms.bays_in` tiles across the register (367 declared types × 51,465
bays) that is 501 visible faults/day station-wide, which is 5.92% of what the maintenance
roster can close.
**Why.** THE-STATION §2 T4 wants "a machine breaks; a maintenance job is created and somebody
walks to it" and nothing in canon gives a failure rate.
**Constrained by.** FROM ABOVE by the roster: `schedule.ROLE_WEIGHTS` carries 14,430 engineers
+ 2,500 waste = 16,930 heads; one 8 h watch each, 25% of it corrective, 4 h a job = 8,465
jobs/day of capacity. A station generating more than that degrades without bound, which the
show's station visibly does not. That ceiling puts the shortest survivable MTBF at 21.6 days,
so 365 sits 17× inside it. FROM BELOW by T4 itself: an MTBF of decades makes the maintenance
job a thing a player never sees.
**Overturned by.** Any figure for B5 maintenance volume, work-order throughput, or fitting
reliability.
**Authority 5.** `station/incident.py::MACHINE_MTBF_DAYS`, `CORRECTIVE_SHARE`, `JOB_HOURS`.
*Note: the first draft of this entry used the workforce ceiling AS the fault rate and its own
sanity check refuted it — 357 interactable types over 8,465 jobs/day implies a 0.04-day MTBF.
The types/instances distinction is the correction.*

## INV-351 — Petty theft: three dozen a day, weighted by crowd × density

**What.** 36 thefts a station-day, distributed over the 31 register places theft can happen in
by `people × people per m²`. Downbelow 11.2/day, Downbelow arch 8.5, the Zocalo 7.4, the black
market 3.3.
**Why.** LAW-CRIME-DOWNBELOW.md §8.2 files petty theft as "Constant — dozens/day", authority 4
for the crime and 5 for the frequency, and gives no distribution.
**Constrained by.** "Dozens" read as three dozen — the plural puts it above 24 and the word
puts it below 100. The WEIGHT is constrained by the same sentence's "Everywhere; concentrated
at customs exits, the Zócalo, and *within* the camps": two of those three are the most heavily
policed places aboard, so policing cannot be the driver and density is. Whether the thief is
CAUGHT is where `security.presence_at` belongs, and `_res_pick` puts it there.
**Overturned by.** Any figure for reported thefts aboard, or an on-screen Ombudsman caseload.
**Authority 5.** `station/incident.py::THEFTS_PER_DAY`, `_theft_weight`.

## INV-352 — One denunciation per Nightwatch informer per year

**What.** 2,250 civilian informers each file one box report a year = 6.16 denunciations/day
station-wide, distributed by crowd over public commercial rooms.
**Why.** `docs/spec/PEOPLE.md` FAC-04 gives the informer count (1,500–3,000, "1–2% of 155,000
humans") and no filing rate.
**Constrained by.** FROM ABOVE by FAC-04's own "Present, growing, NOT in control at datum" —
a rate that shuttered a stall a day would be control. FROM BELOW by "enough that a denunciation
is credible in any public room": at 6/day a Zocalo trader knows somebody it has happened to.
**Overturned by.** Any depicted volume of Nightwatch filings.
**Authority 5.** `station/incident.py::INFORMERS`, `FILINGS_PER_INFORMER_YEAR`.

## INV-353 — A resident touches an identicard reader 0.05 times an hour

**What.** Outside the customs halls, a reader event rate of 0.05 per head per hour present.
**Why.** `docs/spec/SYSTEMS.md` SYS-03 puts readers on doors, counters and lifts across the
register and gives throughput only for the halls (`traffic.hall_rate`).
**Constrained by.** One reader touch every 20 hours present is roughly one a day per resident,
which matches a card used to get into your own quarters and one licit counter — the tier
ladder INV-340/342 already assumes. Higher makes the reader the commonest event on the
station; lower makes INV-342's "a licit counter reads the card" decorative.
**Overturned by.** Any depicted card-use frequency for a resident.
**Authority 5.** `station/incident.py::READER_TOUCHES_PER_HEAD_H`.

## INV-354 — One arrival in a hundred with an unnumbered atmosphere is a quarantine

**What.** 1% of the `arrival.checks` station-7 atmosphere flags escalate to a medical hold.
**Why.** TRAFFIC-AND-CUSTOMS §9 lists "a ship arriving with a medical case and triggering
quarantine" among its authority-5 failure modes with no rate; the customs board's own
"MAY BE CREATED BY PRIOR ARANGEMENT" (authority 1) is the flag, not the quarantine.
**Constrained by.** Above by PLACES.md PLC-046's isolation path being a room that is normally
empty (§353: "quiet 03:00–06:00 except INC-QUAR"). Below by the room existing at all. Lands at
~0.03/day, i.e. one a month.
**Overturned by.** Any depicted quarantine frequency.
**Authority 5.** `station/incident.py::QUAR_SHARE`.

## INV-355 — INC-NC is anchored at the Zocalo, and the geography does the rest

**What.** PLACES §0.2's own 0.02/h for a Narn–Centauri contact event is taken as the rate AT
THE ZOCALO, and every other place scales by its own `crowd × narn share × centauri share`
through `audio.species_mix`.
**Why.** The spec states one number for a class that can fire in 21 places, and applying one
number to 21 places would make the rate independent of who is in the room — the opposite of
what FACTIONS §12 describes.
**Constrained by.** The anchor is the spec's, verbatim. The shape is `populace.species_for`'s,
sampled. `security.CONTACT_SHARE` (5%) is already inside the spec's figure, so it is not
applied twice.
**Overturned by.** A per-place figure in the spec, or `encounter.py` measuring the pass rate
in a room rather than a corridor.
**Authority 5.** `station/incident.py::NC_ANCHOR_PER_H`, `NC_ANCHOR_PLACE`.

## INV-356 — A hold stack forms above 70% berth occupancy

**What.** An arriving hull queues at the standoff ring when `traffic.berths_in_use` exceeds
70% of the bay count, at a probability rising linearly to 1.0 at full; with one elevator down,
half of all arrivals queue regardless.
**Why.** TRAFFIC §4.3 gives the elevator bottleneck (24 movements/h, 62% used at peak) and
SYS-02's eight-phase machine, and no saturation threshold.
**Constrained by.** Above by §4.3's own "62% used at peak" — a threshold above that never
fires. Below by the berth map running at 0.71–0.78 through the working day, so a threshold
much under 0.70 would put a stack there permanently. The elevator term is §4.3's arithmetic:
one unit does 12 movements/h against a peak demand of ~15.
**Overturned by.** Any depicted berth-queue frequency.
**Authority 5.** `station/incident.py::HOLD_LOAD`, `ELEVATOR_DOWN_BLOCK`.

## INV-357 — Debts are called on a week's terms, and the Collector visits one camp at a time

**What.** One seventh of the station's debtor pool is called on per day at 10:00, divided
across the six camp places.
**Why.** `docs/spec/PEOPLE.md` FAC-25 puts "the Collector's rounds through the camp at 10:00"
and SYS-14 triggers the class on "FAC-25 ledger ages past terms", without naming the terms.
**Constrained by.** A week is the shortest term that is a term rather than a same-day loan, and
the pool is the STATION's — one Collector, six camps, so a camp gets its share. The first draft
called a quarter of the book in every camp and reached 44 calls an hour, which the module's own
step-size control detected as a rate no one-minute clock can resolve.
**Overturned by.** Any depicted debt-enforcement interval.
**Authority 5.** `station/incident.py::DEBT_TERM_RATE`, `DEBT_ROUND_H`.

## INV-358 — Camp heat, the sweep threshold, and what a day boundary decays

**What.** A Downbelow contact adds 1.5 to a camp's heat, a theft 1.0; at 6.0 a sweep becomes
possible; a strike ballot needs 3.0 on the grievance board; heat and the debtor pool halve
across a day boundary.
**Why.** LAW-CRIME §5.5 says a sweep happens "occasionally, and always for a reason" and
FAC-06 puts the strike ballot behind a "grievance board T4 threshold" — both name a trigger
and neither names a level.
**Constrained by.** The sweep threshold is four contact events in one camp, which is under
three hours of `security.DOWNBELOW_CONTACT_PER_HOUR` — so a camp that is busy gets swept and a
quiet one does not. The strike threshold is one dock fatality (2.0) plus one elevator outage
(0.5) plus one more of either, so a strike needs a bad fortnight rather than a bad day. The
decay exists because a ledger that only grows is not a ledger: without it the debtor pool
compounds every day and INC-DEBT eventually swamps the station.
**Overturned by.** Any depicted sweep or ballot frequency.
**Authority 5.** `station/incident.py::SWEEP_HEAT`, `STRIKE_THRESHOLD`, `HEAT_DECAY`.

## INV-359 — A diner holds a seat for an hour

**What.** Seat turnover of 1.0 per hour in a venue, used to turn `populace.occupancy` into a
flow of diners for INC-PAKMA.
**Why.** SYS-14 triggers the class on "species meal windows 04:00/16:00 + a wrong-seat diner"
and `economy.SERVE_PER_HEAD` prices servings, not seats.
**Constrained by.** `economy.daily_covers` and `SERVE_PER_HEAD = 0.5` together imply a sitting
of the same order; `schedule`'s meal windows are 1 h wide either side of the hour, so a
turnover much faster than this would put two sittings inside one meal.
**Overturned by.** Any depicted service pace in the Zocalo or a bar.
**Authority 5.** `station/incident.py::SEAT_TURNOVER_PER_H`.

## INV-360 — A bay elevator lasts ten thousand cycles

**What.** 10,000 cycles between outages per unit. At 12 movements/h × 62% duty that is ~8
weeks a unit, so one outage across the pair roughly every 28 days.
**Why.** TRAFFIC §4.3 D-8/T-04 gives the pair, the ~90 s each way, the ~5 min full cycle and
the 62% peak use, and calls one elevator down "the cheapest high-value event in this whole
document" — which is a statement about VALUE, not about frequency.
**Constrained by.** The document's own two words. "High value" means it must be an EVENT rather
than routine, so not weekly. "The cheapest" means it must happen often enough to be worth
building, so not annually. A LIFT FAILS ON CYCLES, NOT ON CALENDAR TIME, which is why this is
not INV-350's 365 days: the first draft applied the calendar MTBF to the place's whole
interactable population and produced 18.6 outages a day on two machines.
**Overturned by.** Any statement of bay-elevator reliability or an on-screen outage.
**Authority 5.** `station/incident.py::ELEVATOR_MTBF_CYCLES`.

## INV-361 — A hundred recordable dock accidents to each fatality

**What.** The dual-clearance chain fires at 100× the fatal rate and `_res_accident` draws the
severity, so a dock accident lands every ~6 days and a fatality every ~500.
**Why.** TRAFFIC §9 gives the S1 chain in full (substandard chip → mistaken clearance → two
hulls in one volume → a dock worker killed, authority 4) and treats it as memorable, i.e. rare.
**Constrained by.** The fatal rate is not chosen — it is the product of three things already
modelled: a fault on the clearance console (one declared machine at INV-350's MTBF), a second
hull in the volume (`traffic.berths_in_use` over the bay count), and a gang on shift
(`schedule`'s 06:00–15:00). 100:1 is the industrial recordable-to-fatal ratio and is what turns
one memorable fatality into a stream a player can be present for. Against 9,650 dockworkers the
implied fatality interval is the right order for a heavy trade.
**Overturned by.** Any figure for B5 dock injuries.
**Authority 5.** `station/incident.py::ACCIDENT_RECORDABLE_PER_FATAL`.

## INV-362 — Dust is one fiftieth of petty theft, in the same rooms

**What.** INC-DUST fires at 0.02 × INC-PICK's rate over the black-market route places.
**Why.** LAW-CRIME §8.2's table files petty theft as "Constant — dozens/day" and Dust as
"Rare, and an event when it happens", two rows apart in the same column, with no numbers.
**Constrained by.** The two rows must differ by orders and not by factors, and Dust must still
fire often enough that S3E06's Psi Cop follow-up is reachable in a play session. Lands at one
every ~6.5 days.
**Overturned by.** Any depicted Dust seizure frequency.
**Authority 5.** `station/incident.py::DUST_SHARE`.

## INV-363 — A Psi Cop visits every three weeks

**What.** 21 days between Psi Corps calls aboard.
**Why.** `docs/spec/SYSTEMS.md` SYS-14 gives the trigger as "SYS-01 era draw (every few weeks)".
**Constrained by.** "A few weeks" is two to four; three is its middle. FACTIONS §4.1's
"paperwork-and-badge presence, not a garrison" bounds it from below (a weekly visit is a
posting) and FAC-05's liaison office bounds it from above (an office with no visitors is not a
liaison).
**Overturned by.** Any count of Psi Cop appearances per season.
**Authority 5.** `station/incident.py::PSICOP_DAYS`.

## INV-364 — The Drazi split is even

**What.** When the factional cycle is on, half the Drazi are on each side.
**Why.** FACTIONS §15 and `docs/spec/PEOPLE.md` FAC-13 leave the colours and the cycle
"deliberately unstated".
**Constrained by.** An even split is the only reading that adds nothing to a fact the sources
declined to state. The switch itself ships OFF, which is FAC-13's own datum state.
**Overturned by.** Any depiction of the split.
**Authority 5.** `station/incident.py::DRAZI_SPLIT`.

## INV-365 — The probe volume is the register's adjacency, not a radius

**What.** The fixed probe volume an incident rate is measured in is the register place the
player stands in plus every place `directory.PLACES` lists as `adjacent` to it, resolved once
at construction. At `customs_north` that is 3 places, 392 m of station and 188,851 m² of floor.
**Why.** `docs/spec/SYSTEMS.md` SYS-14 requires "fixed probe volumes — the district cell
holding the player plus its adjacent cells, fixed at tick start (never a floating radius an
implementation can shrink)" without saying what a district cell is in register terms.
**Constrained by.** It must be TOPOLOGICAL rather than metric, or the spec's own anti-cheat
clause is defeated: any metre figure can be chosen after the numbers are in. The metric span
is therefore an OUTPUT of the volume and is printed beside every rate. The witness radius is a
separate number and is not this module's — it is `populace.corridor_sight_m` (60.5 m), read at
call time.
**Overturned by.** A definition of "district cell" in the spec that disagrees with the
register's adjacency.
**Authority 5.** `station/incident.py::Probe`.

## INV-366 — The sealed Markab quarter: Green ring 0 deck 3, beside the Alien Sector

**What.** `markab_quarter` is a register place at green/0/3, angle 279.0°, z 4400 m, footprint
**(2.349°, 58.32 m)**, `functions=("residence", "sealed_volume")`, `interacts=("welded_door",
"atmosphere_status_lamp", "level_plaque")`, adjacent to `alien_sector` in both directions.
Nobody is in it at any hour.
**Why.** The Markab die of the plague in "Confessions and Lamentations" (S2E18) — **authority 1,
and squarely inside the S2–3 datum** — and no source we hold places their quarter. Three modules
already modelled the room: `npc/schedule.py` carries it as a sealed `PlaceCrowd` at density 0.0,
`npc/crowd.py::EXTENTS` gives it a floor and asserts it is **the one place on the station empty
at every hour of the day**, and `npc/navigation.py::EXPECTED_ISLANDS` names it a deliberate
island in the walk graph. The register did not, so there was nothing to stand in front of.
**Constrained by.** THE SECTOR IS NOT A CHOICE — `schedule.PLACES` already puts it in Green's
outer ring, and Green's outer ring is where the Alien Sector and the alien residential quarters
are, so a non-human community's quarter belongs there and nowhere else. The DECK follows the
Alien Sector's (3) for the same reason. The ANGLE is 284.0° because 300.0 and 316.0 are taken by
`alien_sector` (which spans 282–318°) and `kosh_quarters`, and 279.0 clears 282.0 with the
room's own 2.349° to spare. **THE SIZE IS NOT EXTRAPOLATED AT ALL**: 12.0 m of frontage ×
58.32 m of z (699.84 m²) is `crowd.EXTENTS` verbatim, so the register and the crowd model agree
by construction rather than by discipline — hard rule 4 applied to a fourth pair of
descriptions.

**AND THE UNIT CONVERSION IS THE PART WORTH KEEPING, because writing it wrong would have been
invisible.** `footprint[0]` is **degrees of arc, not metres** — `rooms.py` reads it as
`arc = 2πr · (footprint[0]/360)`. The first draft of this row wrote `12.0` straight from
`crowd.EXTENTS`, which at this deck's **292.700 m** radius would have built a **61 m** frontage:
five times the room the crowd model prices, while every document still said the two "agree".
Nothing in `directory.py` can catch that — `collisions()` compares footprints against each other
and never against the floor area another module derives. 12.0 m of arc at r = 292.700 is
**2.3490°**, and that is what is written. *A number copied between two modules must be copied in
the units the destination reads, and "they agree" is a claim about the value after conversion,
not before.* The wrong angle would have been caught (284.0° sits inside `alien_sector`) but only
by a fifteen-minute gate; the wrong unit would not have been caught at all.

`sealed_volume` and `welded_door` are both borrowed from
`welded_shut` in Grey rather than invented, and `welded_door` is an already-BUILT prop
(`rooms.py`: 1.90 × 0.22 × 2.35 m, wall-mounted), so declaring it does not ask
`interact.py --audit` for something nobody made.
**The reason to build a room nobody can enter is that its emptiness IS the content** — a
measured zero over a real floor rather than a missing entry, which is the distinction
`crowd.py`'s own comment draws. It is the one place where the era lock pays for itself: a
station set in S2–3 that does not show this has not noticed its own history.
**Overturned by.** Any source placing the Markab elsewhere aboard, or showing their quarter
reopened or repurposed within the era.
**Authority 1** for the extinction, **5** for the placement. `station/directory.py`,
`docs/gazetteer/LOCATIONS.md` P-14.

## INV-367 — `refugee_reception` is a workplace alias and must NOT become a register place

**What.** A NEGATIVE entry, recorded because the opposite is the obvious-looking move and was
proposed once already. `refugee_reception` stays out of `directory.PLACES`.
**Why.** It surfaces in `npc/schedule.py` as `Role("refugee", …, "refugee_reception", …)` and in
`npc/resident.py`, and a search for it against the register comes back empty — which reads
exactly like a missing row. It is not one.
`npc/resident.py::WORKPLACE_FUNCTIONS` resolves a workplace to **every register place carrying a
set of functions** — for refugees, `residence` + `short_stay` + `arrival` — and that table's
header states the rule: *"the join is by function, not by a second list of keys, because a table
of keys is a copy of a decision and every time this project has kept two copies of one decision
they have drifted."*
**Constrained by.** Measured rather than argued: **14 of the table's 19 keys are aliases rather
than places** — `concourse`, `engineering`, `medlab`, `hospitality`, `sanctuary`,
`customs_hall`, `docking_bay`, `patrol`, `traffic_control`, `business_district`, `green_sector`,
`grey_industrial`, `waste_management`, `refugee_reception` — and only five (`cnc`,
`council_chamber`, `downbelow`, `hydroponics`, `zocalo`) share a name with a register row.
Promoting one alias of fourteen, on no evidence but that somebody grepped for it, would create
the duplicate the table exists to prevent and would leave thirteen identical "gaps" behind it.
**Overturned by.** A source establishing a single, physically distinct Narn reception hall — in
which case it becomes a PLACE with its own key, and the alias stays as it is.
**Authority 5.** `station/npc/resident.py::WORKPLACE_FUNCTIONS`.

## INV-380 — A residence row's dwelling count is its bay count, and the camps are 4.7× overcrowded

**What.** A `residence`/`informal_residence` register row's dwelling count is `rooms.bays_in`,
and its household size is that block's own peak occupancy divided by it. Measured: **3.07
people per unit** in every EA-standard block (`qtr_personnel` 3.07, `qtr_civilian` 3.07,
`qtr_transient` 3.09, `alien_resident_qtr` 3.14), 2.21 in the Alien Sector, **9.23 in
`downbelow` and 14.29 in `downbelow_arch`**. 13 rows, 7,587 units, 60,557 residents at peak.
**Why.** Every domestic incident rate is per HOUSEHOLD — a dispute across a bulkhead, a door
that will not open, a week's rent — and nothing in this project counted households.
**Constrained by.** `docs/spec/PLACES.md` §0.2's staffing rule states the unit rule outright:
"In residence classes every UNIT carries its door/babcom/locker/bunk set, so a class tag there
counts once per unit (a 270-unit block holds 270 T3 babcom terminals)". The bay count IS the
unit count by the spec's own words, for the same reason INV-350 uses it as the machine count.
The household size is then not chosen at all: it is the quotient of two mechanisms that had
never been pointed at each other — `rooms.tiling`'s footprint instancing and
`populace.occupancy`'s density integral — and they agree to two decimal places across four
blocks built by different generators.
**Overturned by.** Any depicted B5 quarters occupancy, or a change to either mechanism that
breaks the agreement — which is why `incident._selftest` asserts the bracket (1.5–7.0 per unit
across tenanted blocks, and >3× that in `downbelow_arch`) rather than recording the number.
**Authority 5** for the reading; the numbers are measured.
`station/incident.py::units_in`, `household_size`, `households_home`.
*Note: the 3.07 : 14.29 ratio is the first quantitative statement of Downbelow's overcrowding
anywhere in this project, and the register produced it rather than anybody authoring it.*
*Second note, and it is a GAP rather than an invention. `resident.home_for` over
`schedule.ROLE_WEIGHTS` houses 250,001 people; the register's built residence rows hold 60,557
at peak — **24.2%**. The rest sleep in quarters the register does not carry. Every rate in
`incident.py` is per household PRESENT, so a player standing in one block sees that block
rather than the station's notional 250,000 — INV-350's denominator lesson the other way round.
Closing the shortfall belongs to `directory.py` and `rooms.tiling`, not to the generator.*

## INV-381 — One dispute per household every two months, and the rent margin that made arrears endogenous

**What.** `DISPUTES_PER_UNIT_YEAR = 6.0`, weighted by the block's own clock mismatch.
`MEALS_PER_DAY = 3.0`, `MUSTER_DAYS_PER_WEEK = 7.0`, `RENT_MISS_SHARE = 1 − 4.7/7 = 0.329`,
`RENT_DAY_H = 9.0`.
**Why.** THE-STATION's scope clause wants "NPCs with quarters, jobs, schedules and events — not
crowds, residents", and before this the only thing that could happen in a home was a fitting
wearing out (INC-FAULT) and a smuggling route crossing the Alien Sector (INC-DUST).
**Constrained by.** FROM ABOVE: LAW-CRIME §8.2's commonest *crime* is petty theft at
"dozens/day", read by INV-351 as 36. At 12/unit/year the station runs 251 disputes a day —
seven times its whole crime rate and more than every other class combined, and a residential
corridor becomes a soap opera. FROM BELOW: at 1/unit/year a player who lives aboard for a
season never hears one. Six measures at **82.1/day**, 2.3× the petty-theft rate — the right
sign as well as the right order, because the commonest thing in a block of flats is not a crime
and should be commoner than the commonest crime.
**The rent margin is DERIVED and it refuted the first draft of INC-ARREARS.** Priced off
`economy.ladder` and `economy.casual_constraint()`: a week's cheapest tenancy is **6.0 cr =
0.75 days** of casual labour; a week's food is **31.5 cr = 3.94 days**. Rent is a fifth of the
food bill, so no working household falls behind on rent alone; a household clears subsistence
on 4.7 of the muster's 7 days, and `RENT_MISS_SHARE` is the 1 − 4.7/7 a stopped earner cannot
cover. INC-ARREARS therefore carries no rate of its own and reads INC-SICK's pool.
**Overturned by.** Any depicted B5 residential complaint procedure; any stated B5 wage or rent
that breaks the 5:1 food-to-rent ratio.
**Authority 5.** `station/incident.py::DISPUTES_PER_UNIT_YEAR`, `RENT_MISS_SHARE`,
`weekly_subsistence_cr`, `clock_mismatch`.

## INV-382 — The camps' own service economy: 136 pitches, one event each per ten days

**What.** `SERVICE_PITCH_HEADS = 12.0` (people one camp kitchen, still, laundry or barber's
chair serves) and `SERVICE_EVENT_PER_PITCH_DAY = 0.10`. Over `schedule.ROLE_WEIGHTS`' 20,390
lurkers and LAW-CRIME §7.2's stated 8% share that is **136 pitches and 13.6 events a
station-day**.
**Why.** LAW-CRIME §7.2's own gloss on that row is the reason the class exists: "This is the
one that makes it a community rather than a pit." Downbelow had eight incident classes and
every one of them was a crime.
**Constrained by.** The 8% is the document's, stated. `SERVICE_PITCH_HEADS` is bracketed by
that same table: at 1 the share means every eighth lurker runs a business for nobody; at 100 a
camp of 39,262 holds sixteen kitchens, which is a queue rather than a community.
`SERVICE_EVENT_PER_PITCH_DAY` is bracketed above by `security.DOWNBELOW_CONTACT_PER_HOUR =
1.5/h` — the camp's kitchens must not be a commoner event than being robbed in it — and below
by the document's own word for the work, "continuous".
**Overturned by.** Any depiction of Downbelow's internal economy.
**Authority 5.** `station/incident.py::SERVICE_PITCH_HEADS`, `SERVICE_EVENT_PER_PITCH_DAY`.

## INV-383 — The clinical presentation rate, bracketed by the built beds and the medical roster, with nothing picked between

**What.** `BED_DAYS = 3.0`, `ADMIT_OCCUPANCY = 0.80`, `CLINICAL_SHARE = 0.25`,
`CONSULT_HOURS = 0.5`, and the presentation rate is the **geometric mean of the two bounds
those produce**: 390.3 presentations a station-day, 0.570 per head per year, 3.5% of capacity.
**Why.** THE-STATION's scope wants the physical plant that makes 250,000 people possible, and
"somebody needs a doctor near you" is the commonest meaningful thing that happens in a
population that size. Nothing in canon gives a morbidity rate.
**Constrained by.** INV-350's shape, reused deliberately rather than reinvented — that entry's
own lesson is that a fix applied to an instance and not to the rule will be needed again.
THE FLOOR: `rooms.bays_in` × the register's `diagnostic_bed` rows = **51 built beds**; held for
`BED_DAYS` at `ADMIT_OCCUPANCY` they need **13.6 admissions a day** to stay full, and a station
whose built beds stand empty is not modelling illness at all. THE CEILING:
`schedule.ROLE_WEIGHTS`' **2,800 `medical`** at `CLINICAL_SHARE` of an 8 h watch and
`CONSULT_HOURS` a case = **11,200 attendances a day**; above it the medlabs are a queue that
never clears. The two are three orders apart (0.0199 to 16.35 episodes/head/year) and canon
puts nothing between them. **When a quantity is bracketed by two DERIVED bounds and nothing
sits inside, the geometric mean is the only value equally far from being refuted by either
end** — so that is what is used, and it is computed rather than transcribed so it moves if
either bound does.
**Overturned by.** Any figure for B5 medlab throughput, bed count or medical staffing.
**Authority 5.** `station/incident.py::presentations_per_day`, `BED_DAYS`, `ADMIT_OCCUPANCY`,
`CLINICAL_SHARE`, `CONSULT_HOURS`.
*Note, and it is a finding rather than a number: 2,800 medical staff against 51 built beds is
**55 staff per bed**. The register's medlabs are a fraction of the medical plant a quarter of a
million people need, exactly as its built dwellings are a fraction of their housing. Both are
printed by `--report` rather than absorbed into a rate.*

## INV-384 — Move-ons per officer-hour, strays per child-year, and the harm share

**What.** `MOVEONS_PER_OFFICER_H = 0.20`, `STRAYS_PER_CHILD_YEAR = 6.0`,
`STRAY_HARM_SHARE = 0.10`.
**Why.** LAW-CRIME §7.2 states that 8% of the lurker workforce beg and busk at "the boundary
between Downbelow and the commercial rings. **Never inside the Zocalo** — they are moved on",
and `resident._age` is the only statement anywhere in this project that children exist aboard.
Neither had a rate.
**Constrained by — MOVE-ONS.** FACTIONS §11.4's enforcement sentence: "~150 officers on duty
across 8 km. Crime is not policed, it is contained at chokepoints" — and a move-on IS
containment at a chokepoint. It is also the one class here where policing is the DRIVER, the
exact inverse of INV-351's recorded lesson: a theft happens despite the officers, a move-on
cannot happen without one, so `security.presence_at`'s officer count IS the rate and the class
is silent in Downbelow (zero officers) without a place list saying so. ABOVE: at 1.0 the
Zocalo's 12.92 officers do nothing else all watch and the whole duty roster is consumed.
BELOW: at 0.05 a busker is moved on once every fifty working days and "never inside the Zocalo"
is not true. 0.20 gives **92.7–98.7 move-ons a station-day** against LAW-CRIME's 1,631-strong
busking workforce — **one per busker per 16.5–17.6 working days**, which is the sanity check
INV-350's `implied_mtbf_days` is for that derivation, and `--report` prints it.
**Constrained by — STRAYS.** `resident._age`'s own 8% minor rule over `schedule.ROLE_WEIGHTS`'
three role-less roles gives **6,253 children at the datum and 5,213 before `narn_surrender`
(2,20)**. ABOVE: at 52/child/year the station runs 893 strays a day, more than every other
class combined, and Downbelow is a playground. BELOW: at 1/year the station never shows one.
Six gives **102.8/day at the datum against 85.7 at S2E01**, a +20.0% era step on a class
nothing era-gates. HARM: bounded above by INC-ACCIDENT's own 100:1 recordable-to-fatal ratio
(INV-361) and below by zero, which would make the adult-only function list a label rather than
a hazard.
**Overturned by.** Any depiction of B5 security's move-on practice, or of children aboard.
**Authority 5.** `station/incident.py::MOVEONS_PER_OFFICER_H`, `STRAYS_PER_CHILD_YEAR`,
`STRAY_HARM_SHARE`.

## INV-370 — An occluder's cross-section is the kit's own VERTEX EXTENT, not what a ray can reach

**What.** `station/occluders.py`'s deep profile — the corridor cross-section every occluder is
swept from — is `min`/`max` over the vertices of `interior_kit.corridor_section`, taken over
both the door-less and the door-bearing variant. On the shipped kit that is **floor_y −0.200 m,
half_w 1.680 m, ceil_y 3.340 m**, against the collision shell's 0.022 / 1.0806 / 2.829.
**Why it is not a ray cast, and this is arithmetic rather than a preference.** A ray hit is
`a + u·(b−a) + v·(c−a)` with `u,v ≥ 0` and `u+v ≤ 1` — a convex combination of the hit
triangle's three vertices — so each coordinate lies between the smallest and largest of the
three. Reduce hits with `min`/`max` and you can never leave the vertex box; you can only fail to
reach it. The module spent three passes refining a lattice (22 mm pitch, a second section with
doors in it, a 192-direction sphere sweep) against a bound that `min()` and `max()` give
exactly, for free.
**Constrained by.** Correctness in one direction only. An occluder that stops short of the kit
stands in front of geometry a player can see, which is a hole in the world rather than a slow
frame; an occluder that reaches past the kit merely blocks slightly less. The ray lattice fell
short on two of three axes — **floor by 116 mm, ceiling by 340 mm** — and that was **209
containment breaches with a worst case of 169 mm**, at the coffer the door head is let into.
`--rays` still runs the lattice and asserts it lands inside the box.
**The price, measured:** `blocked_fraction` on the self-test arc 93.7% → 93.1%. Six tenths of a
point of sphere coverage for a provably safe occluder. **The gain: 5m13s → under a second**,
which is what makes the profile affordable inside `budget.py` and `export_scene.py`.
**Overturned by.** A kit whose vertex extent contains geometry that is genuinely never visible
AND far enough out to matter — a thick back-of-wall volume, say. Then the vertex bound would
cost real occlusion and the right answer would be a per-group extent (walls and soffit only)
rather than a per-section one. The number to watch is `blocked_fraction`: below ~0.85 on a
corridor the bound has become too loose to be worth having.
**Authority 5.** `station/occluders.py::deep_profile`, `ray_extents`.

## INV-371 — Godot 4 culls occlusion per INSTANCE AABB, and that is the granularity budget.py gates

**What.** `station/budget.py`'s occlusion pass models Godot 4's occlusion culling as: rasterise
the scene's `OccluderInstance3D` geometry into a small depth buffer on the render thread, then
reject an instance when its axis-aligned bounding box is entirely behind that buffer. It does
**not** cull triangles.
**Why.** The saving a gate reports depends entirely on this, and reporting the flattering
granularity would be the gate lying about the build.
**Constrained by.** What is SOURCED rather than assumed: that
`rendering/occlusion_culling/use_occlusion_culling` exists and defaults to **false**; that
`ArrayOccluder3D` exposes exactly `vertices` and `indices`; and that a generated `.tscn` of this
shape loads and returns its occluder with the right counts — all measured headless against this
project's own Godot 4.4 double build, with the key present and absent. That `export_gltf` writes
one primitive per OBJ group is read off this repository. What is DECLARED is the AABB test
itself: one world AABB per submitted instance, eight corners projected, culled when the box's
nearest depth exceeds the furthest occluder depth anywhere in its screen rect — the standard
formulation, and conservative (an uncovered pixel holds inf and keeps the instance).
**The consequence is the whole finding.** A pass assuming per-triangle culling would have
reported this occluder saving **58.2%** of the frame. At instance granularity it saves **7.8%
overall and 0.2% of structure**, because a corridor group spans the whole 345° ring and its AABB
contains the camera.
**Overturned by.** A frame capture on the target card showing a different rejection granularity,
or Godot moving to a per-cluster or per-surface test. The tell would be a measured frame cost
between the instance and triangle rows of that table.
**Authority 5.** `station/budget.py::occlusion_chain`, `deck_section`.

## INV-372 — The occlusion depth buffer is 160 × 90, from the doorway's subtense

**What.** `station/budget.py`'s `OCCLUSION["buffer_w"/"buffer_h"]`.
**Why, and the derivation runs the dangerous way round.** A coarse buffer loses a doorway
between two pixel centres; the wall's depth fills the pixel and the room behind it is culled —
**over-occlusion, which is a hole in the world rather than a slow frame**. So the bound is that
the buffer must resolve the narrowest hole in the occluder at the longest range the corridor
offers.
**Constrained by.**

    door_width_m       1.5      interior_kit.PROVISIONAL, read at run time
    sight_m           60.5      the corridor's own measured sight line
    subtense          1.42 deg  = 2*atan(0.75/60.5)
    fov_h            102.4 deg  INV-083's camera
    pixels per door  >= 2       Nyquist on the aperture
    -> w >= 2 * 102.4 / 1.42 = 144

**160 × 90** is the next 16:9 step up and gives **2.22 px** across that door. `deck_section`
recomputes the bound from the deck it is measuring and fails if the buffer is under it, so the
number cannot quietly stop being derived. It goes red at a sight line past 67 m or a narrower
aperture. **Not claimed to be Godot's own buffer size** — Godot derives its from
`occlusion_rays_per_thread` and the viewport; this is the resolution at which the *measurement*
is honest, and if the engine's is coarser then the engine, not this gate, is over-occluding.
**Overturned by.** A frame capture on target.
**Authority 5.** `station/budget.py::OCCLUSION`.

## INV-373 — The occlusion depth bias is 5 mm, the shell's own facet sag

**What.** `station/budget.py`'s `OCCLUSION["bias_m"] = 0.005`. Nothing is culled unless it is
more than this far behind the occluder.
**Why.** Not chosen: **it is `collision.MAX_SAG_M`.** The occluder's cylindrical bands are swept
as flat facets sized so a facet sags at most that far inside the true cylinder, so a point up to
5 mm behind the recorded occluder surface may in fact be in front of the real one.
**Constrained by.** Using the shell's own tessellation tolerance as the bias means the two
cannot drift apart, and it is the same number `collision.floor_steps` certifies a floor smooth
against — one decision in one place rather than two copies.
**Overturned by.** `MAX_SAG_M` changing (it already has once, 1 mm → 5 mm, tied to
`STEP_TOLERANCE_M` in 3x); the bias follows it by construction. A measured over-occlusion at a
distance where 5 mm is not the dominant error — grazing angles down a long arc — would mean the
bias needs to scale with range rather than be constant.
**Authority 5.** `station/budget.py::OCCLUSION["bias_m"]`.

## INV-374 — The containment control's room: 1.2 m behind the corridor wall, 1.4× the aperture wide

**What.** `station/occluders.py`'s `room_stub()` places one plate per doorway at
`half_w + 1.2 m` from the corridor centreline, spanning the door's angular half-width × 1.4 and
from the door head down to the floor.
**Why.** `interior.ring_arc` builds a corridor and **no rooms**, so the self-test's two aperture
controls — "the aperture widening is load-bearing" and "a sealed occluder hides the rooms behind
the doors" — had nothing to hide and **could not fire**. They passed only because the baseline
was itself breaching 209 rays, which every control inherited; with the baseline at 0 they both
read 0. This is the surface a doorway opens onto. *(A second cause, and it is worth its own
sentence: `ring_arc`'s `door_leaves` defaults to `True`, so the self-test's doors were SHUT — a
configuration `deck.build_deck` never builds, since it passes `door_leaves=False`.)*
**Constrained by.** 1.2 m puts the plate outside the occluder's own wall (1.68 m against the
corridor's 1.0806 m) so it is reachable only through the aperture, and inside any plausible room
depth so it is reachable at all. The 1.4× span covers the slant cases the parallax widening
exists for; at 1.0× a ray entering at the worst angle leaves past the plate's edge. With both,
the controls separate cleanly: sealed **34** breaches (worst 1,789 mm), unwidened **2** (worst
1,214 mm, **and 0 at 64 directions** — that resolution is stated in the code rather than left as
a flattering number), widened **0**.
**Overturned by.** A real vestibule builder in `interior`, at which point this fixture should be
deleted and the control run against the geometry the station actually builds. **It is a test
fixture and is not station canon**; no shipped geometry uses it.
**Authority 5.** `station/occluders.py::room_stub`.

## INV-390 — Station day 0 is a Monday

**What.** `civic_calendar.EPOCH_DOW = 0`: the station's day 0 is a Monday, and `DAY_NAMES` runs
Monday-first from there.
**Why.** Nothing in the show or in this repository fixes the epoch's weekday, and the calendar
cannot avoid the question: **`docs/spec/PLACES.md` PLC-058 states the security unarmed-combat
class runs "Tuesdays 17:00"** — a weekday NAME, which requires an origin before it can be
placed on a station day.
**Constrained by.** PLC-058 itself is the whole constraint, read the obvious way: a class on
**Tuesday** is a class on the second day of the working week, not the sixth day of a week that
starts on Sunday. Taking day 0 as Monday makes the station week open with the working week,
which is what a duty roster implies and what every other rota in the rule table then inherits
for free.
**Overturned by.** Any on-screen date, log slate or duty roster fixing a B5 weekday to a
calendar date. It is a one-line change and every dated observance follows it.
**Authority 5.** `station/civic_calendar.py::EPOCH_DOW`.

## INV-391 — Eight swim lanes at the water-recreation venue

**What.** `civic_calendar.SLOTS["water_rec"] = 8` — the number of simultaneously bookable lanes.
**Why.** `docs/spec/PLACES.md` PLC-069 says **"swim lanes"** and states no count. A booking
ledger cannot hold a booking against a venue with no capacity.
**Constrained by.** The plural puts it above one, and the venue's own floor puts it under a
competition hall's ten — eight is the standard municipal lane count and is what a station
recreation deck of this footprint carries. It is a SLOT COUNT and nothing else depends on it
except how many people can book at once, so being wrong costs a booking conflict rather than a
geometry error.
**Overturned by.** Any frame of the B5 recreation deck, or a stated lane count in the spec.
**Authority 5.** `station/civic_calendar.py::SLOTS`.

## INV-398 — The dock reserves 30% of thrust for control, and refuses under 5%

**What.** `docking.CONTROL_RESERVE = 0.30` and `MIN_RESERVE = 0.05`. A docking plan will not
spend more than 70% of the airframe's maximum acceleration merely holding station on the bay's
circle, and it **refuses outright** below a 5% reserve even where `omega² R` is under `a_max`.
**Why.** `formation_cost(omega, radius) = omega² R` is what the geometry costs before any
manoeuvring, and MASTER-PLAN P4 asks for a dock rather than a hold. A plan with nothing left
over cannot correct.
**Constrained by.** The station's own spin sets the whole curve: at the cobra bay's 293.78 m
radius holding costs 10.35 m/s² of the airframe's 18.38, i.e. **56.3%**, so a reserve above ~44%
makes the bay itself unreachable. At the derived **227.8 m** standoff ceiling the cost is 99.9%
and the reserve is nil, which is what MIN_RESERVE is for — the gate's third control asks for
227 m, which is INSIDE the ceiling, and is refused because 0.1% of thrust is not steering. 30%
lands the flown plan at a 71.3 m standoff, 12.86 m/s², **30.0% in hand**, and the measured peak
demand over twelve start phases is 72.7%.
**Overturned by.** Any stated Starfury thrust or docking procedure; a change to the airframe's
`aurora_thrusters` figures, which this reads rather than copies.
**Authority 5.** `station/physics/docking.py::CONTROL_RESERVE`, `MIN_RESERVE`.

## INV-399 — Capture is 20 m and 4 m/s, and the taper is what makes it reachable

**What.** `capture_range = 20.0 m`, `capture_speed = 4.0 m/s`: how near the hold point and how
nearly matched the craft must be before the standoff ramp starts. The commanded closing speed
tapers at 0.15/s.
**Why.** Without a capture test the approach has no phase boundary and the craft ramps in from
wherever it happens to be.
**Constrained by.** THE TAPER AND THE TEST ARE ONE DECISION and the note says why: 0.15/s puts
the commanded closing speed at 3 m/s when the range is `capture_range` — i.e. **inside**
`capture_speed` — so the capture condition can be MET rather than asymptotically approached for
ever. Pick either number without the other and the phase either never triggers or triggers at a
speed the close cannot null. The closing limit itself is not chosen at all: it is
`contact_is_safe`'s own 2.0 m/s buffer with a quarter kept back, so a perfectly flown plan is
not sitting on its own gate.
**Overturned by.** A stated docking procedure, or a change to `contact_is_safe`'s buffer, which
this tracks by construction.
**Authority 5.** `station/physics/docking.py::ApproachPlan`.

## INV-400 — The attitude loop's rate error is measured against the FEEDFORWARD, not zero

**What.** `docking.ATT_KP, ATT_KD = 0.9, 2.2`, proportional on pointing error and derivative on
rate error — where the rate is measured **against the rotating demand**, not against zero.
**Why.** The target is a bay on a spinning station: the demanded attitude is itself rotating at
`omega`. A derivative term that drives body rate to zero fights the tracking it is supposed to
damp, and the craft lags the bay by a constant angle for ever.
**Constrained by.** The station's spin period (33.4716 s, sourced) sets the demand's rate, so
the feedforward is not a tuning choice — it is `omega`. The gains are then bounded by the
manoeuvre: under-damped and the nose oscillates through contact, over-damped and the craft
cannot follow a demand rotating at `omega`. Measured over twelve start phases the worst
misalignment at contact is **3.48 deg**.
**Overturned by.** Any measured Starfury attitude response.
**Authority 5.** `station/physics/docking.py::ATT_KP`, `ATT_KD`.

## INV-401 — Mains are shut above 25 degrees of pointing error

**What.** `docking.THRUST_GATE_DEG = 25.0`.
**Why.** Thrust applied 40 degrees off the demand is **not a weaker correction, it is a
different one** — it adds velocity in a direction nothing asked for and the loop then spends
authority removing it.
**Constrained by.** Above by the useful component: `cos 25° = 0.906`, so at the gate 91% of
thrust is still doing what was asked and the cross-track error is under 42%. Below by the
attitude loop's own settling — a gate tighter than the loop's overshoot chatters the mains on
and off through the manoeuvre. It cannot be zero, or the craft may never fire at all.
**Overturned by.** Any stated Starfury thrust-vectoring authority.
**Authority 5.** `station/physics/docking.py::THRUST_GATE_DEG`.

## INV-402 — The dock is sampled finer than the profile's own control points

**What.** `starfury_scene`'s dock sampler steps finer than the approach profile's control
points.
**Why.** A sampler at the profile's own resolution can only ever confirm the profile; it cannot
find an excursion between two control points, which is exactly where a guidance law overshoots.
**Constrained by.** Fine enough that the peak-demand and hull-clearance figures are measurements
rather than restatements of the plan (the gate reports peak 72.7% and clearance 28.1 m from the
samples, not from the profile), and coarse enough that a twelve-phase sweep stays a fifteen-
second gate.
**Overturned by.** A measured excursion between samples, which would mean the step is still too
coarse.
**Authority 5.** `station/starfury_scene.py`.

## INV-403 — Room occupants are instanced, not baked

**What.** `populace.ROOM_INSTANCED = True`. A room's occupants are placements against
`populace.station_crowd_library`, the same shared-body path the corridor crowd uses, rather than
triangles welded into the deck `.glb`.
**Why.** The owner's words on being shown the old behaviour: *"these need to be real people and
we've come this far and we have fucking humanoid dioramas in rooms?"* A baked body **can only be
shown or hidden** — `life.gd` says so outright — so the entire runtime behaviour of a person in
a room was `npc.gd` rotating their yaw to face the player within 6 m.
**Constrained by.** ABOVE by the corridor crowd's own measured trade, which this repeats rather
than re-derives: a shared body is what every real crowd system ships. BELOW by individuality —
within-species stature range is genuinely lost, up to **352 mm (narn), 297 (centauri), 296
(minbari)**. Name, species, costume, role, home, job and identicard are unchanged. The budget
decides it: 886 glTF primitives for 66 baked occupants against **31–33 draw calls for all 34
people on screen**, versus `schedule.NPC_BUDGET["max_draw_calls"] = 32` — a rout, and still
straddling the line rather than clearing it.
**THE TRADE IS THE OPPOSITE WAY ROUND FROM THE ONE THAT WAS THERE, deliberately.** At two metres
a player judges BEHAVIOUR, not bone structure; a unique face that never stands up reads worse
than a shared face that gets up and leaves. Distance wants silhouette, proximity wants
behaviour.
**Overturned by.** A runtime that can skin a body on demand, which makes the shared library
unnecessary. The hybrid is already affordable and unbuilt: 4 individual bodies inside 6 m cost
**28,848 tri against 475,992** to give all 66 one — what blocks it is the skinning, not the
budget.
**Authority 5.** `station/populace.py::ROOM_INSTANCED`.

## INV-404 — Pose slots share the walk-phase axis

**What.** `POSE_SLOTS = ("idle", "sit", "sleep", "talk")` appended after the 8 walk phases on the
same index; `CROWD_SLOTS = 12`.
**Why.** The runtime's bucket key is `crowd_<species>_<lod>_<n>` and its material names follow
it. Giving poses their own axis would have been a second shape for the same thing.
**Constrained by.** Measured cost: 112 → **168** shared bodies; at lod4 the four poses add
**32,288 tri** to the walk phases' 64,576. Below, fewer slots means a pose a room needs is
missing; above, every extra slot is paid on every species at every rung.
**Overturned by.** A pose a room needs that is not one of the four.
**Authority 5.** `station/populace.py::POSE_SLOTS`.

## INV-405 — `animation.sleep_clip`

**What.** Recline 90°, `leg_reach_f` 0.94, `arm_reach_f` 0.86, `breath_deg` 2.4 at `IDLE`'s own
two breaths per loop, `turn_deg` 2.2.
**Why.** `CLIP_SET` was walk/idle/talk/sit — **no sleep clip at all** — while
`schedule.RHYTHMS` has always known every Narn aboard is asleep at 03:00 and every Centauri
awake. Species sleep was modelled and could not be seen.
**Constrained by.** The 90° is not a choice: a body on a bunk is horizontal. The reach factors
are under 1.0 because a sleeper's joints are not locked. `breath_deg` reuses `IDLE`'s own rate
because recumbent breathing is diaphragmatic and is the ONLY motion a sleeping body has —
without it a room of sleepers is a row of effigies, which `turn_deg` also guards. Arm spread and
pillow rise are **measured off the rig**, not chosen.
**AND IT NEEDED FOUR IK CONTACTS, NOT TWO**, which is the transferable part: posing arms by
rotation put a sleeper's fingers **0.42 m in the air**, because an elbow flexes FORWARD and a
90° recline turns forward into up. Hands are now solved with the same `_leg_ik` the legs use.
Two-pass: build the estimate, measure the lowest vertex, lift the body onto its own mattress.
Across all 14 humanoid species at lod 0: sink **20–27 mm** into a 40 mm panel, trunk tilt
**< 0.83°**, zero interpenetration worse than rest.
**Overturned by.** Any frame showing a B5 bunk occupied.
**Authority 5.** `station/npc/animation.py::sleep_clip`.

## INV-406 — `MATTRESS_SINK_M = 0.02`

**What.** A sleeping body sinks 20 mm into its bedding.
**Why.** Half of `dressing._m_bed`'s 40 mm mattress panel — derived from the furniture, not
picked.
**Constrained by.** A figure floating on its own bedding to the millimetre reads as a figure on
a shelf; a figure sunk through it reads as a bug. Half the panel is the only value that needs no
further argument.
**Overturned by.** A change to `dressing._m_bed`, which this follows by construction.
**Authority 5.** `station/npc/animation.py::MATTRESS_SINK_M`.

## INV-407 — The occupant timetable, and its step

**What.** `populace.occupant_day`, `DAY_STEP_H = 0.25`.
**Why.** An occupant needs to know what they are doing at any hour, and the step decides what
can be stepped over.
**Constrained by.** **Under `schedule.MEAL_HALF_WINDOW_H` (0.3) and `TRANSIT_H` (0.5)**, so a
meal or a commute cannot fall between two samples — the step is derived from the two shortest
things in the schedule, not chosen. Every state traces to `schedule.activity_at`; presence
traces to `resident.where_at` OR the place's own `occupancy` curve. Measured: 66 of 66 occupants
change state over a station-day; at 03:00, 40 away / 12 eat / 7 work / 4 sleep / 2 idle /
1 transit, and at 13:00, 21 idle / 18 work / 16 away / 9 eat / 2 sleep.
**Overturned by.** A shorter activity in `schedule`, which would require a finer step.
**Authority 5.** `station/populace.py::occupant_day`, `DAY_STEP_H`.

## INV-408 — Leaving a room is along `dressing.LANE_M`

**What.** An occupant exits by the nearer end of the reserved circulation band.
**Why.** A room builder does not record where its door is, so "the way out" has to come from
somewhere.
**Constrained by.** `populace._free_spots` **already ranks that band first** as "where a person
crossing a room actually is" — so this reuses an existing answer rather than inventing a second.
**Overturned by.** The room builder recording its door position, which would be better and would
make this obsolete.
**Authority 5.** `station/populace.py`.

## INV-409 — `TALK_M = 1.80 m`

**What.** Two occupants closer than this are talking to each other.
**Why.** A conversation needs a distance and none was stated.
**Constrained by.** **The maximum of `friction.separation_m`** (0.75–1.80 m across the species
table): two people standing closer than the widest avoidance distance the station models are, by
definition, standing together rather than passing. Not a new number at all.
**Overturned by.** A change to `friction.PAIRS`, which this tracks.
**Authority 5.** `station/populace.py::TALK_M`.

## INV-410 — `BED_BAND = (0.22, 0.82)`, `BED_MIN_AREA_M2 = 0.30`

**What.** Which emitted prop surfaces an occupant may sleep on: height band and a minimum area.
**Why.** `sleep_clip` needs a surface, and the room's own mesh is the only honest source.
**Constrained by.** The band covers every `rooms.PROP_KIND` prop whose machine kind is `"bed"`
at `dressing._m_bed`'s 70%-of-box deck. The area floor exists to stop a **rail or a head unit**
being slept on — both sit inside the height band and neither is a bed.
**Overturned by.** A bed outside the band, which would mean the furniture changed.
**Authority 5.** `station/populace.py::BED_BAND`.

## INV-411 — The seated lift is one-sided

**What.** `seat_dy = max(0, actual − fitted)`: a seated occupant is raised when the seat is
higher than the shared pose was built for, and never lowered when it is lower.
**Why.** Instancing introduced a seated-hip error of **87–153 mm** against the 436 mm pan the
shared `sit` pose is built for, because the pose is one body and the seats are many heights.
**Constrained by.** ASYMMETRIC ON PURPOSE. On a higher seat the lift puts the hips on the pan
and the feet clear, which is what a bar stool looks like. On a lower one the same correction
drives the feet **through the deck**, and hips a few centimetres proud is the lesser error. The
runtime lift closes the measured error to **0–0 mm**.
**Overturned by.** A runtime that can scale the pose to the seat.
**Authority 5.** `station/npc/animation.py`.

## INV-412 — `walk.gd`'s fallback crowd ladder is the coarsest rung that shipped

**What.** When the boot manifest does not name a crowd ladder, `walk.gd` derives one and uses
the **coarsest** LOD rung present.
**Why.** THIS EXISTS BECAUSE OF INSTANCE TEN. `main.gd::_configure_walk` set `crowd_path` and
never `crowd_glbs` or `crowd_ladder`, and `walk.gd::_load_crowd_libs` returns false without
them — so **every launch of the shipped build instanced ZERO corridor walkers** while a Python
harness reported 963 walking 5,966 m. The figure was true of `walkable.py --deck`'s command line
and had never reached the game.
**Constrained by.** Copying `NPC_BUDGET`'s distances into GDScript would be a **second
description of a budget that lives in Python** — the defect this repository has paid for three
times. The coarsest rung cannot be over budget, so it is the only choice that is safe without
holding a copy of the table.
**Overturned by.** `boot.py` writing `populace.crowd_ladder()` into the manifest, which replaces
this conservative default with the derived ladder and is the better fix.
**Authority 5.** `godot/scripts/walk.gd`.

## INV-413 — Carry capacity is eight slots

**What.** `station/player.py::CARRY_CAPACITY = 8`.
**Why.** An inventory with no ceiling has no `store` verb, only a `take` one.
**Bounded below by 3.** The player lands holding two — `IDENTICARD` and `KIT_BAG` — and
`dockwork.py`'s fourteen-day loop has them buy a drink on each of those days, so a capacity of 2
makes the shipped loop impossible.
**Bounded above by 14**, which is `economy.MAX_LINES`: a bag that holds more than the widest
counter's entire range is a hold, not a bag. **8** is the middle of that bracket rounded to a
power of two, so the carried list draws as one HUD row at any frame height.
**Overturned by.** Any depiction of a character carrying a countable number of things, or a
per-item mass landing in `economy.GOODS` — the 40 kg/passenger baggage figure already in
`canon/CONFLICTS.md` would then settle it arithmetically and retire this entry.
**Authority 5.** `station/player.py::CARRY_CAPACITY`.

## INV-414 — A container holds the lines its own place trades

**What.** `interact.container_holds(place)` is `economy.stock_list(place)`.
**Why.** A `store` prop needs contents and nothing in canon lists a locker's inventory.
**Constrained by.** The register already says what each place trades through its `functions`, and
`economy.Good.sold_by` names the functions carrying each line — so a crate in the black market
holds contraband and a tray dispenser in `mess_hall` (`catering`, `crew_social`) holds nothing,
without either being written down. It can only ever produce goods `economy.py` already prices
and stocks, so it cannot invent an object.
**Overturned by.** Any depicted contents of a specific container, or a per-place inventory in the
spec.
**Authority 5.** `station/interact.py::container_holds`.

## INV-415 — A seated eye is the standing eye less (hip − seat)

**What.** `player.posture()` and `player.gd::seated_eye`. Lying down puts the eye
`FIGURE["chest_d"] × stature` above the surface.
**Why.** A first-person camera needs a seated height and the skeleton is not available at
runtime.
**Constrained by.** This is `npc/animation.py::sit_clip`'s OWN translation — `dy = seat_h −
hip_rest` moves the whole torso — restated for a camera rather than a rig. Hip and knee come
from `body.FIGURE × sp.leg_k × stature`, the same expression `body._hip_ring` uses, so there is
no second description of a body's proportions. `seat` and `bed` kinds measure the prop's own
measured top; everything else uses the fitted knee height, per `animation.seat_height`'s "a
chair at the sitter's knee" rule.
**AND IT IS GATED AGAINST THE THING IT APPROXIMATES:** `player.py --selftest` fails if the cheap
path drifts more than 20 mm from `animation.rig`'s skeleton. **It fired at 36 mm on the first
run** — `posture()` off `body.FIGURE` alone is wrong for every non-human species, because
`body._hip_ring` applies `sp.leg_k` and a Narn's legs are not a human's.
**Overturned by.** A frame establishing seated eye height against a known-height fixture.
**Authority 5**, derived from an authority-5 module.

## INV-420 — Plant capacity is N+1 against the system's own design peak

**What.** Every system's plant is sized so that it meets its own design peak demand with one producing unit out of service. Per-unit nameplate is peak/(N-1) where N is the count of `directory.PLACES` rows carrying that system's production functions; total capacity is peak*N/(N-1); the margin at design peak is therefore 1/(N-1) and is a fact about the register rather than a number chosen here.
**Why.** Nothing in canon or the gazetteer states any plant capacity, and a system without one is a roster, not a system. L-01 1.1's equipment list is itself an explicitly redundant architecture at authority 3 -- a *primary* fusion core, *auxiliary* fusion cores, and *four* auxiliary power units -- so redundancy is sourced even though its size is not.
**Bounded Above.** N+2 (peak*N/(N-2)): a third of the station's plant permanently idle, refuted by L-05's yield argument, which sizes the drum's growing area to *just* feed the station -- nothing here is built with a third of it spare.
**Bounded Below.** N+0 (capacity = peak): every single outage becomes a deficit, refuted by SYS-14's own INC-BROWNOUT escalation column, which contains the beat "APU pickup (PLC-122)" -- the station is written as having a standby that picks up.
**Overturned by.** any figure for any plant unit's output, or any on-screen statement of how many reactors the station runs. N=1 SYSTEMS have no N+1 available: `water_reclamation` and `rotation_drivers` are single register rows, are sized to their own peak exactly, and carry zero margin at peak. That is reported as a finding, not smoothed.

## INV-421 — The share of interior services that follows occupancy -- 0.5

**What.** Half of L-01's "interior lighting and services" row (250 MW) varies with the awake population; half is corridor lighting that never turns off.
**Why.** The row's own basis is "251 decks, corridor and room lighting, displays, doors, comms", which is two kinds of load in one line.
**Bounded Above.** 1.0: every watt following occupancy means the corridors go dark at 03:00, refuted by the corridor rig that defines this project's exposure anchor, which is lit at a fixed level.
**Bounded Below.** 0.0: no watt following occupancy means 251 decks of displays and doors draw the same at 03:00 as at 13:00, refuted by `schedule.population_activity` -- 160,342 of 250,001 are asleep.
**Overturned by.** any statement of the station's lighting control regime. SENSITIVITY: `--gate` prints the power margin at both bounds. It moves the 13:00 margin by under two points and changes no conclusion.

## INV-422 — THE SLEEPING METABOLIC RATIO -- 0.85 of the 24-hour mean

**What.** A sleeping resident's O2 draw as a fraction of the station's mean per-head draw. The awake rate is then solved so that the day integrates to L-02's sourced 0.84 kg/head/day.
**Why.** Air demand cannot follow the awake fraction -- a sleeping body still breathes -- but it is not flat either.
**Bounded Above.** 1.0 (no diurnal variation), refuted by L-04's own split of 3 L/day of drinking from 50 L/day of hygiene: hygiene does not happen while asleep, so the station's metabolic day is demonstrably not flat.
**Bounded Below.** 0.6: a 40% metabolic drop in sleep is far outside anything a mammal does.
**Overturned by.** any figure for the station's own O2 draw curve.

## INV-423 — THE AIR BUFFER'S LIMITS -- CO2 1% by volume, O2 16%, 100 W per head

**What.** The thresholds the air system's survival clocks are measured against.
**Why.** "How long does the station survive with its air plant off" has no answer without a limit, and the answer is the most useful number in this module: under six hours.
**Bounded.** CO2 0.5% (a conservative habitat set point) to 3% (frank impairment); O2 19.5% (the usual oxygen-deficient trigger) to 16%; metabolic heat 80 W (sleeping) to 120 W (light activity). THE BOX REFUTED THE FIRST CLAIM MADE FROM IT, and the corrected one is narrower. "CO2 binds before O2 at every corner" is FALSE: at CO2 3% with O2 19.5% -- the most permissive CO2 limit against the most conservative O2 limit, taken together -- O2 binds at 7.89 h against CO2's 17.80 h. CO2 binds at the other three corners and at the declared values, by 4.6x. WHAT IS ROBUST is that the air buffer is 3-18 hours over the whole box, two orders under water's 720, so "air is the fastest system on the station" does not depend on the numbers chosen and "it is a scrubber rather than an oxygen supply" does, mildly. Both are printed by `--gate` section G, corner by corner. THE THERMAL CLOCK IS DECLARED AND THEN NOT USED, deliberately. At 0.23 h it is the smallest number in the module and it counts the heat capacity of the air alone; the structure of a habitat outweighs its air by orders of magnitude and is what actually absorbs 25 MW. No mass for that structure exists in this project, so the clock is a lower bound known to be far too short, and letting an unbounded quantity set a bound would be worse than reporting it beside the others with the caveat attached.
**Overturned by.** any statement of the station's atmospheric set points -- the customs board's "SIX DIFFERENT ATMOSPHERES" (authority 1) numbers none of them, which is why these are declared rather than sourced.

## INV-424 — THE SHED LADDER -- life safety, habitation, work, leisure

**What.** The order in which electrical load is shed, expressed over `directory.PLACES`' own function vocabulary rather than as a place list, so a new place joins the ladder by its function.
**Why.** "The lights go out" has to say whose.
**Bounded.** No ordering can put medical below leisure and remain a station; no ordering can shed nothing, or a deficit has no consequence.
**Overturned by.** any on-screen brownout showing which lights went first.

## INV-425 — THE FOOD RESERVE -- 30 days

**What.** The station's larder, as hours of store behind the food system.
**Why.** It is the SAME STANDARD as the water reserve rather than a second guess: L-04 sizes a strategic reserve at 30 days against resupply failure, and L-05's diet is three-sourced with imports as one source.
**Bounded Below.** the resupply interval -- `traffic` lands 55 hulls a day, so a reserve shorter than a few days would be no reserve at all.
**Bounded Above.** the drum's own crop cycle: a reserve longer than the time to grow a replacement is dead mass nobody would carry.
**Overturned by.** any statement of the station's larder or rationing.

## INV-426 — THE WASTE BALANCE TANK -- one day

**What.** How long the waste stream can be held with the plant stopped.
**Why.** It is a different KIND of store from food's, and that is the point: a strategic reserve protects against resupply failing, a balance tank protects against the plant stopping, and a balance tank is sized to one cycle of the stream it balances. The cycle here is the station-day -- L-06's organic stream is what L-05's food becomes, and food is eaten in `schedule`'s three diurnal meal windows.
**Bounded Below.** `incident.JOB_HOURS` = 4 h: a plant that cannot be taken down for one corrective job cannot be maintained.
**Bounded Above.** the 30-day strategic standard, which would be absurd for a stream nobody wants to hold.
**Overturned by.** any figure for the station's waste tankage.

## INV-427 — Rotation's store is not derivable, and that is recorded as a hole

**What.** The rotation system reports an infinite store and a stated reason.
**Why.** L-01 files rotation as "effectively zero in steady state -- a flywheel in vacuum", so the store is the drum's angular momentum and the clock is I*omega/torque. The period (33.4716 s) and the radius are both held; the drum's MASS is not held anywhere in this project, and an inertia invented to fill that hole would be exactly the "number that looks sourced and is not" hard rule 1 forbids.
**What IS derivable instead**, and is reported: the consequence of a rotation outage is not gravity but the loss of docking torque correction, which is `traffic`'s problem and lands in INC-HOLD.
**Overturned by.** any figure for the drum's mass, or any on-screen statement of spin-down time.

## INV-440 — Body density, 746.5 kg/m³

**What.** Every ragdoll segment's mass is its own volume × 746.5 kg/m³.
**Why.** SOLVED, NOT CHOSEN. `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` states "A 75 kg person weighs 108 kgf in Grey ring 1", and `npc/security.py` already computes its patrol-weight column from that officer — so ρ = 75 kg / V(nominal human), recomputed from the mesh on every run rather than written down.
**Why it is BELOW real tissue density (~1000).** `body.py`'s elliptical ring lofts are the convex hull of a section that really has a waist and an armpit: the mesh is **0.1005 m³** against the ~0.075 m³ a 75 kg person displaces, ×1.34. The density absorbs the hull's overestimate so the total mass is right.
**Overturned by.** any canon statement of a species' mass, or a non-convex torso section.

## INV-441 — Spine and chest cones, 25° swing / 25° twist each

**What.** The two torso joints in `npc/ragdoll.py`.
**Bounded below.** `walk_fr14` drives the spine 6.8° and the chest 6.1°.
**Bounded above.** 30° × 2 joints × 2 directions folds a torso double at the waist, which reads as a broken back.
**Overturned by.** a show frame of a body bent further at the waist than 50° total.

## INV-442 — The neck is not declared

**What.** Neck swing 40°, twist 31.5°.
**Why.** READ OFF `animation.LOOK_LIMIT` rather than invented: swing = `pitch_deg` (40), twist = `yaw_deg × neck_share` = 70 × 0.45. Editing LOOK_LIMIT moves both, so a head that can look somewhere can also fall that way and no further.
**Overturned by.** a change to LOOK_LIMIT, which is the point.

## INV-443 — Shoulder 95°/60°, hip 90°/40°

**Bounded below.** the `sit` clip drives the hip 87.2°.
**Bounded above.** a shoulder past ~100° puts the upper arm through the far armpit. The hip is tighter because the pelvis is in the way.
**Overturned by.** a clip that needs more, which is how these two were last corrected.

## INV-444 — Knee hinge −2..145°, elbow −145..2°

**The zero is DERIVED.** `animation._skeleton` puts the knee on the hip–ankle line — measured 0.0 mm off and asserted in `ragdoll.py --gate` — so rest *is* full extension and neither limit needed an offset chosen for it.
**The sign is derived too.** The axis is the figure's own X; a positive rotation about +X carries a point below the joint to −Z, which is backward in a **+Z-facing** body, so a knee flexes positive and an elbow negative.
**Bounded below.** 89.8° (sit), 64.0° (talk).
**Bounded above.** past ~145° the calf passes through the thigh.
**The 2° opposite allowance** exists because a hinge limit sitting exactly on its rest angle chatters.
**Overturned by.** a species whose knee is not on the hip–ankle line.

## INV-445 — Wrist 95°/90°, ankle 70°/30°

**What.** The two distal joints.
**These were WRONG at 70/50 and 60/25 and the clip floor caught them**: `sleep_clip` drives the wrist **90.9°** and the ankle **64.3°**, so a body that can sleep in that pose could not fall into it.
**The wrist number is anatomy in an unusual place.** `PLAN_BONES` goes shoulder→elbow→wrist with **no radioulnar bone**, so forearm pronation has nowhere to live but the wrist joint and the limit has to carry both.
**Overturned by.** adding a forearm bone, which would move ~45° of that back where it belongs.

## INV-446 — Linear damp 0.6, angular damp 3.0, bounce 0, friction 0.9

**Bounded below.** undamped, a body is still above the settle threshold after the whole 6 s window.
**Bounded above.** terminal speed falls as g/damp, and past ~1.5 the descent looks wrong.
**Angular is 5× linear** because the thing that will not stop is spin on a 1.7 kg forearm.
**Checkable.** settle time is printed on every drop — measured 2.02–3.55 s.
**Overturned by.** a video reference of a body falling in ~0.76 g.

## INV-447 — The Vorlon is excluded from ragdolls

**What.** 14 of 15 species have a ragdoll. The Vorlon does not.
**Why.** It is the `column` plan — 5 bones, root/base/column/collar/head, **no legs and no arms**. `animation.PLAN_BONES` already refuses it a walk clip ("Kosh has no gait and it would be an invention to give him one"); a fall would be the same invention with more moving parts.
**Note the brief had this backwards.** `encounter_suit` is the **Gaim**'s plan and is fully humanoid (14 segments; its wrists carry no mesh and fold into the forearms). The suit is not the thing to exclude.
**Scale.** `body.VORLON_SINGLETON = 1` — one on the station.
**Overturned by.** any show frame of a Vorlon out of the encounter suit, or of one falling.

## INV-448 — Segments under 0.2% of the figure's volume fold into their parent

**Bounded below.** a human hand is 0.49% of the figure, and a flopping hand is most of what reads as unconscious.
**Bounded above.** a Gaim's `wrist` owns one ring of `suit_arm` and would fit at **52,960×** its own flesh volume — four orders of magnitude away, with nothing real in between.
**Overturned by.** a species whose hand is under 0.2%, which none of the fifteen is.

## INV-449 — Intra-ragdoll self-collision is off

**Why.** The shapes are solved from the mesh's own volume, so a chest box and a thigh capsule **share the volume the skin blends between them** and overlap at rest by construction. Measured with it on: **peak 500 m/s, 13.1 m of joint separation** — the solver tearing the body apart trying to resolve an overlap that is correct.
**What holds limbs apart instead.** the joint limits, INV-441..445.
**Lost.** an arm can pass through the far thigh in an extreme pose.
**Overturned by.** per-segment shapes fitted to non-overlapping volumes, which would need the skin partition to be a partition.

## INV-450 — "Settled" means displacement over a window, not instantaneous velocity

**What.** Threshold **0.0583 m/s**, averaged over a 20-tick window.
**Why that number.** `body._px_scale(body.PIXEL_BUDGET)` at 1 m — 0.97 mm a frame, i.e. sub-pixel at conversation distance. A body that has stopped moving *visibly* has settled.
**Why a window.** an instantaneous check needs 20 CONSECUTIVE ticks under the bar, and a body whose fastest bone averaged 0.018 m/s never produced twenty in a row while visibly stopped — it reported "settle=NEVER".
**Overturned by.** a change to PIXEL_BUDGET, which is the point.

## INV-451 — A promotion that states no gravity gets the deck's, not Earth's

**What.** `ragdoll.gd::promote` derives `g` and `up` from the body's own world position when the caller does not state them: up is −radial (the floor is the outer wall), g = ω²r with ω² read off `cell_manifest.json`'s deck table.
**Why it is in the DIRECTOR and not in each caller.** It was a default of 9.81 m/s² and +Y, and the only caller that set them correctly was the gate they were written in. `npc.gd::promote_walker` — the one a player's session actually goes through — set neither, so a real collapse would have fallen at Earth gravity straight down on a station whose deck delivers **7.454 m/s² along a radius**. That is a fix applied to the instance rather than to the rule, which is the defect this file's own §4h section is about.
**Checkable.** `--derive-g` withholds both and the run is byte-identical to the one that states them.
**Overturned by.** a place on the station that is not on the rotor — the drum ground and a docked Starfury both need their own answer.

## INV-480 — The player's gravity is g = ω²r along its own radius, never a constant

**What.** `player.gd` derives BOTH halves of its field from the body's own world position when it is told the station's spin: down is the outward radial from the +Z axis, and the magnitude is `omega2 * r`. On the boot deck at r = 211.5 m that is **7.452 m/s² (0.760 g)**, not 9.81.

**Why it is in the BODY and not in each caller.** It was a two-way switch plus a scalar, and both were wrong in the shipped build. `"deck"` mode returned the constant `Vector3(0, -1, 0)` — right only near the bottom of the ring, where the boot spawn happens to sit (ring angle **264.8°**, so −Y is 5.2° off the true radial). And `main.gd::_configure_walk` did set `"drum"`, so the shipped DIRECTION was right — while **nothing anywhere set `gravity_m_s2`**, so the shipped MAGNITUDE was Earth's. Measured in the engine at all eighteen ring angles of blue/0/0: the pre-fix field reads **+31.6% on g and +31.9% on the measured free-fall acceleration**, at every angle. This is INV-451's finding one file over — a default that only the gate it was written in ever sets is an unset default — and the cure is the same: move the derivation into the thing that needs it.

**Where ω² comes from.** `cell_manifest.json`'s deck table, `floor_g × 9.80665 / floor_r_m`, the same rule `main.gd::_spin_omega2` uses; `walk.gd::_derive_omega2` reads the row for the deck the body is actually standing on and prints which one. On a rigid rotor one row fixes the field at every radius, including the ones with no deck on them. Over the 251 rows the implied ω² spreads **0.051%** (0.03522752 to 0.03524550), which is `floor_g` being stored to four places and is the noise floor of the whole method. Period 33.470 s.

**What it does NOT change.** A caller that states a number still wins: `--gravity=` short-circuits the derivation entirely, so `station/drum_walk.py`'s measured drum-floor value is untouched, and any caller that spawns its own body without a spin (`transit.gd`, `route_test.gd`, `life.gd`, `navwalk.gd`, `arrival.gd`) keeps the exact pre-4r behaviour.

**Checkable.** `godot --headless --path godot -- --no-coldstart --gravity-gate` — 18 angles, `up_err_max=0.0000°`, `g_err_max=0.000%`, and a measured free-fall acceleration within **0.053%** of ω² at the fall's own mean radius. Controls `--legacy-field` and `--legacy-deck` both fail.

**Overturned by.** a part of the station that is not on the rotor. The docked Starfury and anything in the zero-g core need their own answer, and `player.gd` returns g = 0 on the axis rather than inventing one.

## INV-481 — The gravity gate's tolerances, all four derived

**up direction — 0.0948°.** The angle the player's OWN capsule radius subtends at the deck's floor radius: `atan(0.35 / 211.555)`. Inside that, the field points at a different part of the same body and no gameplay can tell. Computed at run time from the capsule and the deck, never written down. The defect it catches is up to **179.98°**.

**g — 0.5%.** About ten times the 0.051% spread between the 251 deck rows' own implied ω² (INV-480), and sixty times the ±0.0066% quantisation of a single `floor_g`. The defect it catches is **31.6%**.

**measured acceleration — 1.0%.** Twice the g band, because an acceleration measured off a falling body also carries whatever one frame of contact does to it. Achieved: 0.053%.

**drop — 0.300 m.** The cell spawn's own height above the shell (`r_floor - r_spawn` = **0.200 m**, written by `stream.bake::_floor_point`) plus Godot's default `floor_snap_length` of 0.10 m. Achieved: 0.176 m.

**And one number the gate had to be taught.** Referenced against the FLOOR's g the measured fall came out systematically **−0.33%** at all eighteen angles. That is not error: `g = ω²r` and the body is lifted 0.9 m NEARER the axis to fall, so it genuinely falls more slowly. Referencing against ω² at the mean radius of the fall itself takes the residual to **0.053%** — a factor of six, and a confirmation that the body integrates a radial field rather than a constant, which no read-back of a variable could have given.

**Overturned by.** a deck at a radius where the capsule subtends a materially different angle — Yellow's innermost addressed deck is r = 155.45 m, where the up band would be 0.129°.

## INV-482 — A settled body is separated as capsules, and a box segment as its circumscribing cylinder

**What.** `npc.gd::push_off` separates the player from every physical bone of every promoted ragdoll, using the same across-the-floor-only rule it already uses for walkers and baked people. Each segment is treated as a capsule: `ragdoll.py`'s own capsule shapes exactly, and a BOX shape as a capsule down its longest local axis with the radius that circumscribes the other two half-extents.

**What is lost, measured off `human_ragdoll.json` rather than estimated.** 7 of a human's 16 segments are boxes (pelvis, spine, chest, both wrists, both ankles). At the corners of one the player is held `sqrt(h_i² + h_j²) − max(h_i, h_j)` further out than the box itself would hold them: **33.2 mm at the spine**, 14.1 mm at the chest, 9.2 mm at the pelvis, 7.2 mm at a wrist. Separately, flattening an arbitrary capsule onto the floor plane over-separates by `r(1 − cos tilt)` — a forearm at 45° is 12.7 mm of its 43.3 mm radius, a thigh 23.4 mm of 79.9.

**Why not the exact shape.** The true capsule-capsule separation has a component ALONG the body's up, and a push along up is precisely what costs a `CharacterBody3D` its floor — the whole diagnosis at the top of `npc.gd`. The approximation is not a shortcut, it is the constraint.

**Checkable.** `--corpse-gate`: `clearance_min = −0.0000 m` against a tolerance of one frame of walking (0.070 m at 4.2 m/s and 60 Hz). Control `--no-ragdoll-push`: the player walks the full 10.50 m and ends **0.420 m inside** the body.

**Overturned by.** a segment whose box is far from square in its minor axes, where the circumscribing radius stops being a fair stand-in; or a body posture where two segments' capsules leave a gap the player can stand in, which nothing yet measures.

## INV-452 — The near field is a level BELOW drum_dressing's ladder, numbered -1

**What.** `garden.tree(seed, level)` / `garden.block_building(seed, level)` number
`drum_dressing.LOD_RATIOS` exactly — 0 is that module's LOD0 at 113 m, 1/2/3 its proxies — and add
**level -1**, inside `NEAR_SWITCH_M = 35 m`. The default is **0**, not -1.
**Why a level and not more detail on the existing one.** STATE.md §24.4b against
`docs/engine-4q-drum-dressed.png`: *"The LOD ladder resolves detail by distance; it does not place
more things near the eye."* A ladder whose finest rung is 113 m has no rung for where a player stands.
**Why the default is not the finest.** `drum_dressing._tree_proto` and `_building_proto` call
`gd.tree(seed)` / `gd.block_building(seed)` with no level, and `LOD_SCALE_M = 113.0` was solved by
bisection against `DRESSING_TRIS = 120,000` at that cost, over 1,945 features, landing at 119,868.
A finer bare call silently overruns a budget in a file `garden.py` does not own.
**Why -1 rather than renumbering.** Renumbering makes every `drum_dressing` comment that says
"level 0 IS `garden.tree()`" wrong, silently.
**Checkable.** `garden._selftest` runs `drum_dressing.worst_case_cost(6)` and asserts it fits.
**Overturned by.** A change to `drum_dressing.LOD_SCALE_M`, or a streaming budget for the drum.

## INV-453 — A tree's crown radius is a fraction of its height, not a constant

**What.** `CROWN_FRAC = 0.45`; crown radius = 0.45 × the tree's own height, ×(0.85..1.15).
**Why.** `tree()` drew height from `TREE_H_M * (0.75 + 0.5u)` — 5.25 to 10.5 m — and every canopy
lobe from the **constant** `TREE_R_M = 2.2`. A 10.5 m tree got a 2.2 m crown: a lollipop **by
construction** on the tall half of the population, whatever else was hung on it.
`docs/garden-4q-before-tree.png`, Forward+, eye 11 m away, shows it.
**What constrained it.** A mature open-grown garden broadleaf is about as wide as it is tall.
`garden.png`'s trees behind the landmark read 0.40-0.55 of their own height in radius; 29a's
overhanging broadleaf is wider than tall because it is pruned over a path. Bounded BELOW by 0.30,
under which a broadleaf reads as a conifer; ABOVE by 0.60, at which crowns merge into a roof at
`STREET_TREE_PITCH_M`.
**Checkable.** The lollipop gate measures crown span over height across 40 seeds and needs >= 0.60;
its control asserts the constant it replaced scores 0.42 and FAILS.
**Overturned by.** Any frame of the Garden's planting where a crown and its own trunk base are both
legible.

## INV-454 — Three tree forms, mixed 55 / 25 / 20

**What.** `TREE_FORMS = ("broadleaf", "umbrella", "palm")`, per seed at 55% broadleaf, 25% palm,
20% umbrella.
**Why.** All three are authority 1 and only the first was built. broadleaf: `garden.png`
"deciduous trees and shrubs"; `The Gardens.webp` "dark rounded broadleaf trees"; 29a's overhanging
canopy. palm: `The Gardens.webp` "**Palm trees** lining streets and open ground" — the only frame of
the settlement's own street planting. umbrella: 29a upper left, broad flat-topped canopies on clear
stems, the widest thing in that frame.
**What constrained the mix.** `The Gardens.webp` shows roughly one palm to two broadleaves over the
legible half of the town; 29a's flat-topped trees are four of about fifteen legible canopies.
**Why the form is opt-in.** `drum_dressing` builds its own LOD 1-3 and all of them are rounded
broadleaf blobs. A palm at LOD0 popping into a broadleaf at 113 m is worse than a broadleaf at both,
so the drum scatter keeps the default and only `townscape()` — which owns its whole ladder — asks
for the mix.
**Overturned by.** Any frame of the drum's planting where crowns can be counted by form.

## INV-455 — Terraced massing: setback 1.35 m, batter 0.55 m over 2.20 m, a low wing, recessed bands

**What.** `SETBACK_M = 1.35`, `BATTER_M = 0.55` over `BATTER_H_M = 2.20`, `WING_FRAC = 0.55` ×
`WING_D_M = 5.5` × `WING_H_M = 3.6`, `BAND_RECESS_M = 0.34`, `BAND_H_M = 1.30`, panes 0.95 × 0.90 m
at 1.55 m pitch, 2-3 tiers.
**Why.** The previous version answered "shitty little cubes" with TRIM — pilasters, cills, gutters,
downpipes, balconies, twenty-one times the line density — over a single rectangular prism.
`docs/garden-4q-before-tree.png` shows it reading as a concrete retaining wall from 12 m. **"Cubes"
is a statement about SILHOUETTE and trim does not change one.**
**What constrained each number.** setback and tier count: `talia-winters in gorgeous office.webp`
"low wide grey settlement blocks, **terraced rather than towered**" and `The Gardens.webp` "two to
four storeys". batter: `The Gardens.webp` "three stacked glazed bands over a **solid battered
base**". wing: "**long low linear blocks** with unbroken window strips". recessed band and pane
pitch: "continuous horizontal window banding — **rows of small bright rectangles in dark recessed
bands**"; the old band stood 60 mm PROUD, which draws two lines and reads as a painted stripe —
`docs/judge-4e-drum-half.png`'s "white boxes with window-grid textures". slab caps: `garden.png`
"cantilevered horizontal slab canopies ... wrapping the base in layered tiers".
**What is NOT changed and why.** The (L, W, H) envelope is drawn by the same three `_u` calls in the
same order, because `drum_dressing.prototype_dims()` reads it back to fit 708 town blocks.
**Checkable.** The extrusion gate reads the `garden_block` groups ONLY — the walls, never the trim —
and needs every block's mass plan at 80% of its height to be <= 0.85 of its base plan. As built the
worst is 0.50; with `SETBACK_M` forced to 0 it is 0.70 (the wing still working); with the setback
AND the wing removed it is 1.000 and the gate fires.
**Overturned by.** A frame of the drum settlement in which one block's plan can be traced at two
heights.

## INV-456 — Near-field ground cover: 4.4 tussocks and 2.0 scrub clumps per 100 m², and a sett COURSE

**What.** Inside `NEAR_SWITCH_M`, on ground that is neither paved nor built: tussocks (0.26 m, one
lobe) at 4.4 per 100 m² and scrub clumps (0.62 m, three overlapping lobes) at 2.0 per 100 m², on a
jittered lattice. Paving in courses 0.42 m wide standing 18 mm proud; cross joints only within 10 m.
**Why.** `docs/engine-4q-drum-dressed.png` and `docs/garden-4q-before-tree.png` show the same thing
underfoot: two flat colour fields meeting along a hard straight edge with nothing standing on either.
**What constrained it.** 29a is the only authority-1 frame at eye level in the Garden: "paved
winding paths in **small setts**", "clipped hedges", a circular planter massed with flowering shrub,
"terracing retained by horizontal red-brown timber-slat walls". The 0.42 m sett module is read from
that frame's paving against its standing figures. Densities bounded BELOW by the point at which the
cover stops closing the green/tan edge, ABOVE by the frame allowance: 212 tussocks inside 35 m is
1.4 tri/m² locally, and that density over 4.5 million m² would be 4 million triangles.
**Why courses and not setts.** A 46 × 26 m terrace at 0.42 m is 6,780 setts — 81,000 triangles, more
than the drum's whole remaining allowance for one floor. A course lays the same two lines the length
of the terrace for twelve triangles, and setts are laid in courses anyway.
**Why a jittered lattice.** An even lattice reads as confetti (the session-2n greebles); pure noise
clumps and leaves holes. A jittered lattice has a spacing floor and no visible period.
**Overturned by.** A frame of the drum's open ground at eye level, which the reference set does not
contain — 29a is a designed civic landscape, not a field.

## INV-457 — The townscape's frame allowance is 55,000 triangles, and the street grid inside it

**What.** `TOWNSCAPE_TRIS = 55,000`. `STREET_PITCH_M = 38`, `CROSS_PITCH_M = 52`, `STREET_W_M = 9`,
`NEAR_TOWN_M = 68`, `STREET_TREE_PITCH_M = 26`, `HERO_TREES = 6`.
**Why the allowance is a measurement, not an allocation.** Two engine renders of the drum, both
Forward+ on Vulkan 1.4, report the scene total in their own log: 263,384 with this module at 22,620
(room 59,236) and 293,566 with it at 51,026 (room 56,088), against
`budget.DRUM["visible_set_tris"] = 300,000`. The binding figure is the smaller; 55,000 leaves 1,088.
**What it replaced, and why that gate was wrong.** `garden._selftest` asserted `< 0.5 tri/m²` over
the settlement band, borrowing `budget.DRUM["surface_tris_per_m2"]`. `budget.py` applies that number
to `interior.drum_interior()` — the GROUND HEIGHTFIELD's own mesh density over 4.5 million m² — not
to objects standing on the ground. Same units, different quantity, and near-field content is a
concentration by definition: a rule that forbids 1.4 tri/m² inside 35 m forbids ever standing
anywhere. The old number is still printed every run (0.3554 before, 0.802 after) so the cost of the
change stays visible.
**Why HERO_TREES is a count.** A radius costs whatever happens to fall inside it; a count is stated.
**What constrained the grid.** `The Gardens.webp`: "low-rise flat-roofed blocky buildings, two to
four storeys, in a **dense orthogonal street grid**", "street lighting: bright point sources on
posts along the streets", "palm trees lining streets". The previous placement was one building per
4,400 m², which is not a town.
**Overturned by.** A streaming budget for the drum — everything here is built for one eye at one
instant, exactly as `drum_ground.visible_set` and `drum_dressing.dressing_set` are — or any change
to `budget.DRUM`.

## INV-460 — Where a watch officer sits is derived from how long they have got

**What.** `station/cnc_ops.py` gives C&C nine desks — one per `plant_systems.SYSTEM_KEYS` (power, air, water, food, waste, rotation) plus one per function `directory.PLACES` declares for `cnc` (`station_ops`, `traffic_control`, `defence_command`) — and seats them by `TIME_TO_CONSEQUENCE`: the hours between the thing going wrong and somebody noticing. The five shortest take the dais, fastest at the arc's centre where the reference frame puts the standing officer, alternating outward; the four longest take the pit.
**Why it is derived rather than chosen.** Every value is another module's published number and none of them was written for this: power `plant_systems.survives_h` **0.00 h** (no store — a gigawatt cannot be put in a tank), ops 24 / `incident.visible_faults_per_day` **0.05 h**, defence `npc/security.beat('blue')['period_s']` **0.28 h**, traffic 1 / `traffic.rate_per_hour` at the arrival peak **0.30 h**, air **5.77 h**, waste **24 h**, water and food **720 h** (L-04's 30-day reserve), rotation indefinite (INV-427 says it is not derivable). A seat map somebody liked the look of could not be refuted by anything in the repository; this one changes if any of six modules changes.
**Checkable.** `python3 station/cnc_ops.py --gate` prints the ladder and asserts the dais holds the five fastest and that the officer's own console is the fastest desk on the station, with a control that gives power a day of buffer and watches it lose the centre seat. `6 + 3 == 5 + 4` is asserted against `command_control.CONSOLE_N` and `PIT_CONSOLE_N`, so a seventh system or a re-tagged register fails rather than silently leaving a desk with no console.
**Overturned by.** any show frame that identifies what a named C&C station is for — one legible console legend would replace the whole derivation with a reading.

## INV-461 — The C&C window is four tiers, not sixteen bars

**What.** The window is built as: glazing in three concentric COURSES of trapezoidal panes (12, 24 and 24 divisions, at radius fractions 0.14–0.40, 0.40–0.62 and 0.80–1.00), a broad structural BAND at 0.62–0.80 with forty STUDS along each edge, sixteen primary MULLIONS hub to rim with finer secondaries inside each course, a rim COLLAR, and sixteen radial RIBS running 1.35 m out past the rim across the bulkhead. The bulkhead itself is one plate with a circular 48-gon aperture (`interior_kit._plate_with_hole`), panelled, with two circular BOSSES at ±4.55 m, y 5.15 m.
**Measured, not remembered.** `tools/refzoom.py "reference/03-sector-blue/comand and contorl.webp" --box 0.24 0.05 0.78 0.50 --scale 2`. Radii read off that crop against the header's fitted outer radius of 153 px: hub 21 px, first course to 61, second to 95, band 95–122, outer course 122–153 → 0.14, 0.40, 0.62, 0.80, 1.00.
**Why it had to be rebuilt.** The previous build was sixteen flat bars, one flat ring, one flat hub and a single black disc in a SQUARE hole — `docs/craft-4q-cnc-before-half.png` at the rubric's half distance is a wagon wheel painted on a black rectangle, which is `docs/AAA-STANDARD.md` C1 verbatim, in the one object the whole room is arranged around.
**Checkable.** `command_control._selftest` asserts the glazing is in ≥3 concentric courses, that the band is studded, that a mullion vertex exists past the rim, and that **no bulkhead vertex lies inside the aperture radius** — which is what "the hole is round" means and what the square version fails.
**Overturned by.** a wider or less compressed frame of the same set; the pane counts are the weakest of the five numbers because the outer course is cut by the frame edge on both sides.

## INV-462 — C&C has a ceiling, at `rooms.articulate`'s own height

**What.** A coffered soffit at `DOME_H_M * 0.22` = 7.48 m over the whole 14 × 12 m floor, seven beams 0.34 m deep, with a run of `light_service_tube` battens down the centreline.
**Why that height and not a new one.** This module already passes `DOME_H_M * 0.22` to `rooms.articulate` as the height its dado, rail and cornice bands are laid to, so a ceiling anywhere else leaves the bands ending in air. One constant, two consumers.
**Authority 5, and what is NOT invented.** The reference frame is cropped above the light courses and shows only a dark curved soffit, so what is built is the DARK and the STRUCTURE — no pattern the frame does not carry. Before this the room had nothing above the wall bands at all: every frame ever taken in C&C has a black void over it, which reads as an unroofed set and is why the dais keys appear to hang from nothing.
**Overturned by.** any frame of C&C that tilts up.

## INV-463 — The annunciator over the window

**What.** A status board on the forward bulkhead at y = 6.94 m, 6.20 m wide, carrying one lamp per desk in `cnc_ops.seating()`'s own order, each lit green / amber / red by that desk's state. Group `prop_tactical_display`, which is `cnc`'s own declared interactable and an already-bound material name.
**Why it is over the window.** Sightline: the dais faces the window, so that is the one surface every station on the floor is already looking at. That siting is this module's choice; what constrains its APPEARANCE is the reference's own wall instrument cluster (top left of frame — a dark panel carrying small lit rectangles).
**Why it exists at all.** `directory.PLACES` has given `cnc` a `tactical_display` since layer 1 and `interact.resolve_place` was satisfying it by ALIAS, onto geometry that is not a display. The room declared a thing it did not have.
**Checkable.** `command_control._selftest` asserts the group is present and that the status stacks carry a dark lamp as well as a lit one; `cnc_ops --engine-gate` renders a well station and a broken one and diffs the frames.
**Overturned by.** a frame showing what is actually above C&C's window.

## INV-464 — Four wall courses a side; two of them carry the lamps

**What.** Each side wall carries four horizontal light courses (at y = 1.15, 2.35, 3.55, 4.75 m), each a recessed trough with a reflector cheek above and below, a lens, a divider every ~1.55 m and an end cap. The two middle courses are `cc_light_strip`; the outer two are `light_service_tube`.
**Why the split, and it is a limitation rather than a design.** `materials.py`'s own source line for `light_wall_course` — measured from this room's authority-1 frame — says *"Four horizontal courses per side wall at a measured 1.2 m vertical pitch"*, and this module has built TWO since it was written. But `export_scene.FIXTURE_LIGHTING` hangs one lamp on every connected body of a `cc_light_strip` span and `export_scene._selftest` asserts there are exactly four bodies; emitting four courses a side would put eight lamps in a room whose exposure was solved against four. `light_service_tube` is bound, emissive, and not in `FIXTURE_LIGHTING`, so the other two courses are visible without changing a rig this session does not own.
**Segmentation is measured.** `tools/refzoom.py ... --box 0.0 0.08 0.30 0.72 --scale 3`: the tubes read against the 1.05 m handrail in the same crop at ~1.55 m with ~0.19 m dark breaks.
**Overturned by / closed by.** the patch reported with this session: make all four `cc_light_strip`, change `export_scene._selftest`'s `_courses == [4]` to `[8]`, and re-solve `ROOM_EXPOSURE["mod:command_control"]` against the reference.

## INV-465 — The standing-order log is the station's plant state

**What.** `station/generated/cnc/orders.json` records what C&C has ordered and not undone — today only `{"isolate": [unit, ...]}`. `cnc_ops.apply_orders()` pushes it into `plant_systems.set_offline`, which is the module that calls itself "THE ONLY WRITER" and which had no caller outside its own gate. `command_control.command_control()` reads it when it builds the room, so the consoles, the annunciator and the pit's registers show the state the orders produced.
**Why a file and not an argument.** The bridge between this simulation and the engine is one-way (MASTER-PLAN A4b): Python bakes, GDScript reads, and `tools/export_scene.py` runs in its own process. A standing order that only existed inside one interpreter could not change a rendered frame, and a rendered frame is the only evidence available here that the board reaches a player.
**Absence is nominal, and that is asserted.** With no file every plant desk is NORMAL because `spares == design_spares` is the definition of nominal, so `state_of_room()` short-circuits without importing `plant_systems` at all — which keeps `deck.py --sweep`, `rooms.py --footprint` and `variety.py` at exactly their present cost. `--gate` asserts the short-circuit equals the long way round at 03, 08, 13 and 20, with a control that isolates the station's only water plant and watches the shortcut NOT be taken.
**Overturned by.** a runtime that can call Python, which would make the log a cache rather than the state.

## INV-466 — Three console states, and no threshold was chosen

**What.** Every desk reads NORMAL, CAUTION or ALARM. ALARM is `plant_systems.deficit > 0` — the plant cannot meet the load now. CAUTION is `spares < design_spares` — the redundancy the station was built with has been spent. NORMAL is neither.
**Why there is no number in it.** Those are `plant_systems.wear_at`'s own three states, which already carry a derived multiplier each (1.0, 1/`CORRECTIVE_SHARE`, the roster ceiling). A threshold nobody chose cannot be tuned to make a board look calm, and the alternative — "amber at 80% of capacity" — would have been the first authored rate in a chain that deliberately has none.
**The three non-plant desks take the same shape from their own modules' boundaries.** Traffic is ALARM when `traffic.berths_in_use` leaves no free bay, because a ship with nowhere to go is `INC-HOLD`; defence is ALARM when `security.roving_pairs` reaches zero; ops is ALARM when `plant_systems.fault_arrivals_per_hour` exceeds `corrective_capacity_per_hour`, which is INV-350's own bound.
**Checkable.** `cnc_ops --gate` asserts all six plant desks NORMAL at 13:00 with nothing isolated, then isolates `fusion_core` and `reactor_hall` and measures the effect: INC-BROWNOUT ×2,190 at every power place, INC-FAULT ×16.9 at the plant, station fault arrivals 20.9/h → 113.7/h, and a shed plan naming **61 places with 78,271 people standing in them**.
**Overturned by.** an on-screen brownout showing which lights step down first — S1 "Survivors" and S2's power-loss scenes are the frames to check, and they would test INV-424's ladder at the same time.

## INV-470 — The customs gate line is an arched portal one corridor width inside the mouth

**What.** `customs.gate_wall` builds a transverse wall at z = 2.60 m, 0.90 m deep, 3.90 m tall, pierced by a segmental arch 4.00 m wide springing at 2.20 m and crowning at 3.10 m. Pale piers 0.90 × 0.17 × 2.20 m flank the passage on both faces, each carrying two dark recessed 0.47 m squares; a four-bar red-orange notice panel stands outboard of them; the light course runs through the reveal.

**Why the wall exists at all.** It is authority 1 and the module has recorded it since session 3c without building it: `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg` shows "a gated passage beyond, with vertical white light strips ranked along the left-hand wall, a red-orange sign panel, and a second WELCOME legend on the right-hand wall". Re-read at full size, that passage is an **arch** in a wall, with pale piers carrying dark square insets either side of it and a white legend on the maroon fascia over it.

**Why 2.60 m and not 0.** `bespoke.NEAR_END["customs"]` makes z = 0 the way in from the corridor, and both `bespoke.near_face_opening` and `deck._mouth_clear` measure the near 1.2 m band. A wall on the near face is a wall those two functions have to be argued with; at one corridor width in (`interior_kit.PROVISIONAL["corridor_width_m"]` = 2.60) the band they probe is exactly as open as it was before the wall existed.

**Why 3.90 m tall and not 7.2.** In the reference the suspended screens hang NEARER the camera than the arch; here they are at the far end of the hall, so a full-height wall 2.6 m inside the door would hide the three boards the room exists for from the one place a player is guaranteed to stand. 3.90 m sits under the screens' 4.30 m underside, so the fascia and the boards both read from the doorway.

**Why the arch is one radius.** `R = (rise² + halfspan²) / 2·rise` = 2.672 m from the springing and crown above, so the curve is a circular segment and not a spline anybody chose.

**Checkable.** `python3 station/customs.py` — "no two of this hall's solids stand in the same place" (the arch ring stands 60 mm proud of the fascia so no two faces are coplanar with matching ends), plus the closure and non-manifold gates over the whole mesh.

**Overturned by.** Any frame of this passage that resolves its width against a person, or that shows the wall to be full height.

## INV-471 — The legend over the arch is GENERATED from the register, not transcribed

**What.** `customs._gate_legend(place)` returns two lines built from `directory.py`'s own row — the place's name and the first two functions it declares. `customs_north` reads `CUSTOMS HALL NORTH / IMMIGRATION   IDENTICARD CHECK`; `arrival_concourse` reads `ARRIVAL CONCOURSE / ARRIVAL   WAYFINDING`.

**Why not a transcription.** The authority-1 frame plainly carries a white legend on the fascia over the arch. **Its wording is not recoverable.** At the source's 1262 × 634 it is four unresolved blocks; magnified nine times with `tools/refzoom.py --box 0.40 0.605 0.53 0.65 --scale 9` it is a violet smear with no letterform in it. Transcribing a guess would put invented words on a surface where every other word in this room is authority-1 verbatim — a number that looks sourced and is not, which hard rule 1 forbids by name. Leaving the fascia blank would delete a thing the frame plainly shows.

**What it buys besides honesty.** The three places say three different things, which is `deck.py --degeneracy`'s question answered in the signage as well as in the geometry.

**Authority 5.** **Overturned by** any frame of this fascia at a resolution that resolves a capital.

**Not extrapolated:** the second legend, `WELCOME TO BABYLON 5` on the flank. That one is legible in the wider crop as `WELCOME TO BAB…` before the frame edge, and `WELCOME_BOARD` already carries the wording at authority 1.

## INV-472 — The queue is sized by the station's own arrival wave, not by taste

**What.** `customs.queue_plan` returns 8 switchback legs of 7.20 m at 1.20 m lane pitch on the −X half of the hall, holding 64 people over 57.6 m of lane.

**Derived from.** `docs/gazetteer/FACTIONS.md` §2.3, the traffic model:

    6,300 arrivals/day ÷ 52 movements/day = 121 souls off one movement
    121 ÷ 2 halls (Security Manual, authority 3) = 61 into one hall as a wave
    61 × 0.90 m standing queue pitch = 55 m of lane the hall must hold
    ⌈55 / 7.20 m of clear width⌉ = 8 legs

**Why the wave and not the mean.** The same section gives 4.4 people/minute/hall averaged and then says in as many words that "arrivals come in *waves*, so design the hall for a peak of 20–40/minute and long dead periods". Four desks cannot clear 61 people quickly; the hall's job is to hold them in order while they wait.

**Why the −X half and not the centre.** `deck._place_local` maps this room's local x = 0 onto the corridor's door, and `roomnav` has to walk a body from that door to the register's centre. Barriers are solid (`rooms.is_solid`, `collision.prop_boxes`), so a serpentine across the full width would be a maze the room-reach gate has to solve. Arrivals queue on one side and cleared passengers walk out on the other, which is what a real hall does.

**Extrapolated:** the 0.90 m standing queue pitch and the 1.20 m lane width (a person with a bag between two barriers), authority 5. **Overturned by** any frame that shows queue management in a B5 customs hall, or a correction to FACTIONS.md §2.3's souls-per-arrival.

## INV-473 — The processing booth: what a counter needs to be a place a person is processed AT

**What.** `customs.desk_booth` adds, per desk: two 2.30 m return screens 0.09 m thick running 1.90 m back toward the end wall; a 0.92 × 0.30 m lane plate at 2.62 m facing the queue, lettered `LANE 01`…`LANE 04`; a lamp above it; a 0.19 × 0.13 × 0.16 m identicard reader on the counter's public edge with its own lit register; the officer's 0.42 × 0.30 m monitor on the far edge, turned away from the queue; and a 0.98 m wicket in the gap between two booths.

**Why.** `directory.py` declares `identicard_reader` for both halls and `interact.py --audit` has been resolving it off a mesh-derived alias since session 4d — the reader existed as a NAME and not as an object. Judge-4e's C1 finding on this room is about the boards; the desks were four 48-triangle slabs and are now four `dressing.machine("counter", …)` carcasses with nothing on them.

**Proportions extrapolated** against `DESK_W_M` 2.40 / `DESK_H_M` 1.05, themselves INV-029. Authority 5. **Overturned by** any frame of a B5 customs desk.

**A clamp that is not cosmetic.** `fx` is clamped to ±(hw − 0.10). Unclamped, the outermost desk's outer fin lands 5 mm inside the wall plate — two closed solids in one place, which every closure, winding and manifold test in the module passes. It is the negative control for the clearance gate.

## INV-474 — The search line and the seizure store — gazetteer gap D-12, filled

**What.** On `contraband_search` only: an in-feed and out-feed roller table (1.30 × 0.62 × 0.74 m, seven rollers each) either side of each baggage arch; two 2.30 × 0.80 × 0.88 m inspection benches with a tray rail under them; and a 3.60 × 1.45 × 2.55 m steel cage against the +X wall — thirteen bars, a head and foot rail, and 20 seized-goods lockers in a 5 × 4 rack behind them.

**Declared as a hole in advance.** `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` lists "the customs contraband inspection area" as gap **D-12** — "the customs *halls* are placed at authority 3; the search room is not". So this is hard rule 1's own instruction being followed rather than a silent invention.

**Why a cage and not a room.** Cutting a room into the wall would put a hole in a shell whose `bespoke.SHELL_OPEN_EDGES["customs"]` entry is **0**. A locked steel cage in a public hall is also the more legible object: a player can SEE what has been taken.

**Why its outer face is at hw − 0.14 and not hw − 0.06.** The light course occupies the outer 0.10 m of that wall; at hw − 0.06 the third locker row stands inside a lit cell. Found by the module's own clearance gate.

Authority 5 throughout. **Overturned by** any frame of a B5 customs search area.

## INV-475 — Six atmosphere stations, and the count is read from the board in the same room

**What.** On `atmosphere_assignment` only (declared by `customs_north` alone): a rank of N lamps on the −X wall at 2.05 m, each over a 0.34 m numbered plate at 0.62 m pitch, with a 0.66 × 1.35 × 0.30 m breather dispenser under them. The second station carries a marker bar.

**N is not written down.** `customs.atmosphere_count()` parses it out of `signage.BOARDS["customs_atmosphere"]`, whose authority-1 transcription reads "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5". Two copies of a fact drift; a correction to the board corrects the rank, and the function raises rather than defaulting if the sentence ever stops stating a count.

**Why the second station is marked.** Humans are atmosphere **02** — authority 1, the on-screen identicard schema quoted in `docs/AAA-STANDARD.md`'s NPC checklist ("with humans as atmosphere 02"). So the rank's second station is the one a human arrival is sent to.

**Extrapolated:** that the assignment is done at a marked rank at all, and every dimension. Authority 5. **Overturned by** any frame showing how atmosphere assignment is physically done.

## INV-476 — The backlit ceiling is a circuit pattern, not a lit sheet

**What.** `customs.hall` lights a cell of the 1.6 m coffered lattice when a `blake2b`-keyed test says so, seeded at `CEIL_LIT_FRAC` = 0.34 and grown by a trace rule (a cell is also lit if both its axial neighbours are), so lit cells form runs and corners. Unlit cells are built as a shallower recess in the same plate, so the lattice keeps its depth where it is dark.

**Why.** The module docstring has always said the grid reads "as circuitry at distance", and re-read at full size the reference's ceiling is discrete clusters of yellow-green cells on a dark ground. This module lit **every** cell of a 64%-solid grid, so `docs/engine-4f-customs-normal.png` shows one flat pale slab ~370 m² across.

**The fraction is measured, not chosen.** `materials.light_ceiling_grid`'s own source note counts, on the same authority-1 frame, "7,013 px of dark lattice at V 0.06–0.10, and only 212 px of 14,983 — 1.4% — above V 0.50, with 78% of the lit cells below V 0.34". That is a mostly-dark ceiling with a minority of bright cells. It is also why that material had to be pulled from emission 2.6 to 0.8: 370 m² of it is the largest emissive surface in the room.

**Determinism.** `blake2b`, not `str.__hash__`, which is salted per process — AAA-STANDARD R0 names that failure by name.

**Overturned by** a frame of this ceiling at a resolution that lets the lit fraction be counted directly.

## INV-500 — The drum's triangle budget is charged against the exporter's own part list

**What.** `station/budget.py`'s habitat-drum gate no longer sums a list written in `budget.py`. It calls `tools/export_scene.py::drum_parts()` — the one place the drum shot's contents are enumerated — and charges every triangle in it.

**Why this is an INV entry and not just a fix.** The number the gate reports changed by a factor of 2.6 with no content changing, so every past statement about the drum's cost is superseded. Measured at the exporter's own standing eye (205°, mid-length):

| | old sum | what the shot builds |
|---|---|---|
| shell / ground | `interior.drum_interior()` 88,736 — **not in the shot** | `drum_ground.visible_set()` 94,592 |
| end caps | 15,072 | 15,072 |
| guideways | 11,796 | 11,796 |
| spokes | 516 | 516 |
| core | — | 13,340 |
| trams | — | 12,624 |
| townscape | — | 51,026 |
| dressing | — | 89,094 |
| **total** | **116,120 (38.7% of 300,000, PASS)** | **288,060 (96.0%)** |

**Constrained by** the fact that `drum_parts` replaces the band shell with `drum_ground.visible_set()` — its own comment says emitting both would z-fight across 4.5 million m² — so the old sum charged 88,736 triangles nobody renders while 166,084 triangles that *are* rendered were charged to nothing. `DRUM_CALIBRATION` measures the dressing alone at **39.08 / 32.30 / 47.26%** of the pixels of the three drum framings.

**Overturned by** any change to what `--shot drum` builds, which is now the only thing that can move this number. There is nothing left in `budget.py` to update when the drum grows.

## INV-501 — The drum gate stands on a 4 × 3 lattice, and its own lattice error is 16.2%

**What.** `budget.DRUM["stations"] = 4` angles evenly around the circumference and `DRUM["z_stations"] = 3` axial stations at (j+½)/3 of the drum's open length — twelve standing eyes, worst charged.

**Why a lattice at all.** `drum_ground.visible_set()` and `drum_dressing.dressing_set()` resolve LOD against the eye, so a drum figure is meaningless without one. `docs/AAA-STANDARD.md` scores a single convenient camera **PERFORMANCE 2** and a swept worst case **3**, and `budget.DECK` already sweeps 48 × 24 for that reason. Measured over a 10 × 3 exploratory sweep in session 4q, ground + dressing runs **144,256 to 201,162** across the drum — a factor of 1.39 — so one eye is not a bound.

**Why 4 × 3 and not finer.** ~10 s an eye, all of it in LOD resolution: 12 eyes is 138 s, and `budget.py` goes 4m03s → 6m24s. 6 × 3 would be ~3.5 min for a verdict that does not change (the gate already fails). The lattice is **regular and stated rather than placed on the answer**: it knows nothing about `interior.LAND_USE`, which is where the worst case actually falls (270°, a settlement band), so it will keep finding the worst case if the land use moves.

**What it costs, stated rather than hidden.** The half-resolution sub-lattice finds **256,144 against 305,536 — 16.2% lattice error**, printed on every run. That is large and it is the honest price of twelve eyes; it is reported for the same reason `deck_section` reports its own 10.1%.

**Overturned by** a profile showing the LOD resolution is cheaper than measured, which would buy a finer lattice for the same seconds.

## INV-502 — The drum's surface-density bound is charged on everything standing on the ground, not on the ground alone

**What.** `budget.py`'s `surface density` check divides the **whole** drum visible set by the drum's inner area (0.068 tri/m² against a 0.500 bound), where it previously divided the band shell alone (0.020).

**Why.** The bound's own comment says it "decides whether the ground can be per-object geometry or has to be a heightfield". Since `drum_dressing.py` and `garden.py` began standing objects on that ground the answer is *both*, and charging only the heightfield gated the half that was never in question. Ground alone is still printed beside it (0.021 tri/m²) because the heightfield question is still a real one.

**Overturned by** nothing about the drum; this is a change of divisor, not of limit. The 0.5 tri/m² bound is untouched.

## INV-503 — The eye a density measurement of the drum is taken from

**What.** `station/density.py::DRUM_EYE = (205.0, 0.5)` — 205° of the drum's circumference, half-way along its open length.

**Why not a choice.** It is `tools/export_scene.py::build_drum`'s own default stand, so the mesh `density.py` scores is a mesh somebody has rendered and judged. The value was already inline in `_m_interior`; naming it is what let `_m_interior`, its legacy control and the self-test all take the same one, which is the property that matters — three copies of an eye would put three different meshes behind one number.

**Overturned by** the exporter changing its default stand, which this should then follow.

## INV-458 — The dressing allowance is 120,000, not the 127,712 that was available

**What.** `drum_dressing.DRESSING_TRIS = 120_000`.
**Why.** `budget.DRUM` 300,000 less the fixed parts less the worst-case ground left 127,712. It is set at 120,000 so a small growth in the ground or the tram does not silently push the drum over its allowance.
**DEFINED RETROSPECTIVELY, IN SESSION 4q, AND THAT IS THE POINT.** `drum_dressing.py` has cited this number since it was written and **no entry ever existed** — the workflow that built the module (`station-4q-craft`) was killed mid-flight by a container recycle and its report, which carried the entries, died with it. I integrated the code without them. The derivation survived only because the module states it in a comment beside the constant; a reader who trusted the citation would have found nothing.
**AND ITS ARITHMETIC IS NOW KNOWN TO BE WRONG:** the `fixed = 75_968` it subtracts contained townscape at 22,620, and the true figure is 104,374. The ceiling stands; the subtraction that produced it does not.
**Overturned by.** any change to `budget.DRUM`, or a streaming budget for the drum.

## INV-459 — A person walking the drum sees something within 90 m

**What.** `drum_dressing.NEAREST_FLOOR_M = 90.0`.
**Why it is not a preference.** `drum_ground.PATCH_A × PATCH_Z` is 124.9 × 129.4 m, so 90 m is a little over half a patch diagonal — the distance at which *"there is always something in the patch you are standing in"* becomes true rather than average.
**Defined retrospectively in 4q for the same reason as INV-458**, and it is the load-bearing one: INV-490's near rung is defined as the ground *inside* this guarantee, so the two meet with no gap and no overlap. A citation with nothing behind it was carrying a second entry.
**Overturned by.** any change to `drum_ground`'s patch size.

## INV-495 — A farm hedge is 1.90 m, with a standard every 85 m

*(Renumbered from INV-450 in session 4q. **It collided:** `canon/INVENTIONS.md` defines INV-450 as the ragdoll's settle threshold, and `drum_dressing.py` cited the same number for a hedge. Two different facts, one number — see INV-497.)*

**What.** `HEDGE_H_M = 1.90`, `HEDGE_W_M = 1.40`, `HEDGE_STANDARD_M = 85.0`.
**Why.** Taller than a garden hedge — the park hedge is separately 1.05 m, which is `garden.HEDGE_H_M` read from the same frame — because 1.9 m is a stock-proof farm hedge. Bounded ABOVE by 2.2 m, at which a hedge stops being a hedge and becomes a shelterbelt (a separate class here, with trees in it); BELOW by 1.4 m, under which it stops occluding a person and reads as a kerb. The standard — a full tree left uncut in the hedge line — follows English practice of one per chain-and-a-half; 85 m is the same order and is set so a 323 m parcel edge carries three or four rather than a regular two.
**Authority 5. Overturned by.** any frame showing the arable boundaries at a known scale.

## INV-496 — The clump lattice is 118 m *because* the ground patch is 124.9 m

*(Renumbered from INV-451 in session 4q; it collided with the ragdoll gravity derivation. See INV-497.)*

**What.** `CLUMP_SPACING_M = 118.0`.
**Why that and not the patch size.** `drum_ground.PATCH_A` is 32 cells = 124.9 m, and the clump lattice is **deliberately not** that number, so clumps do not line up with patch boundaries and produce a visible grid at the LOD seams.
**Overturned by.** a change to `PATCH_A`, which would need this moved off it again.

## INV-497 — Every INV cited in code must be defined, and no number may mean two things

**What.** `tools/inv_check.py`, run in CI, asserts that every `INV-nnn` cited anywhere in `station/`, `tools/` or `godot/` has a `## INV-nnn` entry in `canon/INVENTIONS.md`.
**Why it exists.** Hard rule 2 says *"Log every invention … Canon and extrapolation must never blur"*, and nothing enforced it. On its first run, session 4q, it found **13 dangling citations** — and worse, **two numbers meaning two things each**: INV-450 was both the ragdoll's settle threshold and a hedge height, INV-451 both the spin-derived gravity and a lattice spacing.
**The cause is mine and is worth stating.** Two agents worked in one session; one's entries were appended to `INVENTIONS.md` while the other's module was integrated from a workflow whose report had been destroyed by a container recycle. Each had reserved a block; nothing checked the blocks against each other. **A number is an index into a shared namespace, and this project had no gate on that namespace.**
**Why citations and not just uniqueness.** A duplicate `## INV-nnn` heading is the easy half. The expensive half is a citation with nothing behind it: INV-458 and INV-459 had been cited in a shipped module since it was written, and the only reason their derivations survived at all is that the module states them in comments beside the constants.
**Overturned by.** nothing — this is a rule, not a measurement.


## INV-490 — The drum's near-field rung ends where the far field's guarantee begins

**What.** `drum_dressing.NEAR_R_M = NEAREST_FLOOR_M` = 90 m, and its own full/coarse
switch is `NEAR_R_M / LOD_RATIOS[1]` = 28.1 m.

**Why not a chosen radius.** `NEAREST_FLOOR_M` is already derived (INV-459) as the
distance inside which the far field guarantees something to look at — a little over
half a `drum_ground` patch diagonal, so that "there is always something in the patch
you are standing in" is true rather than average. The near rung's job is exactly the
ground *inside* that guarantee, so the two meet with no gap and no overlap. The
full/coarse ratio is the module's own `LOD_RATIOS[1]` = 3.2 rather than a fourth
ratio invented for this rung.

**Constrained by** cost: at the ground lattice's 15.79 m² cell, 90 m is 1,612 cells,
of which the stride-2 coarse rule keeps about 600. Measured worst near-rung cost over
36 standing positions is **19,116 triangles**.

**Overturned by** a change to `NEAREST_FLOOR_M`, which this follows by construction.

## INV-491 — Half of everything below the horizon is ground within 5.39 m of your feet

**What.** `drum_dressing.near_horizon_split()`. Standing at 1.70 m and looking at the
horizon through the player's own 70° vertical lens (`godot/scripts/player.gd` line 279,
Godot `Camera3D.fov` being vertical under the default `KEEP_HEIGHT`), the frame below
the horizon runs from depression 0 (infinitely far) to 35° at the bottom edge. Screen
area is linear in depression because the frame is a rectangle, so:

| | distance |
|---|---|
| bottom edge of the frame | `1.7 / tan(35°)` = **2.43 m** |
| MEDIAN below-horizon ground | `1.7 / tan(17.5°)` = **5.39 m** |
| upper quarter | `1.7 / tan(8.75°)` = **11.05 m** |

**Why it is the floor.** Measured at the eye of `docs/engine-4q-drum-dressed.png`
(`--stand 20,4700`), the nearest thing standing anywhere on the drum was a tree at
**44.3 m** and nothing at all was inside 35 m. The lower half of that frame could not
have been anything but bare ground, whatever else the drum carried. So the floor is
"something within `median_m`", and the companion area floor is
`NEAR_BARE_VIEW_MAX = 0.50` — 0.50 is not a taste parameter, it is what *median* means.

**Three fovs exist in this project and using the wrong one would make this look derived
and be wrong:** the player's 70, `export_scene.SHOT_FOV_DEG` = 46 (every committed
frame), and `drum_ground.FOV_DEG` = 50 (LOD pixel arithmetic only). 70 is both the
strictest — a wider lens puts more very-near ground in frame — and the one a player
looks through. At 46° the same median is 8.36 m, so every committed frame is a
*conservative* view of this defect.

**Overturned by** `player.gd` changing its fov, or by the project standing a person at
something other than 1.7 m.

## INV-492 — The near rung stands on the ground's own lattice, and takes the ground's own material

**What.** One stand of cover per `drum_ground` lattice cell — 3.903 × 4.044 m,
15.79 m². A crop stand in an `arable2` parcel emits the group `ground_arable_2`, taken
from `drum_ground._KIND_GROUP`, which is the group the ground under it is drawn with.

**Why that lattice.** `drum_ground` states its own limit above `HEDGE_W_M`: "the hedge
itself — 2 m tall, 1 m wide — is finer than lod0's 3.9 m cell and belongs in the
material, not the field. A 1 m-wide ridge in a 3.9 m lattice does not render as a hedge
at any level." That is correct, and it is a **delegation** that nothing took delivery of,
which is why the near field is flat. The near rung's resolution is therefore exactly the
resolution the heightfield admits it cannot represent. Worst distance from a standing
position to the nearest cell centre is half a cell diagonal, **2.81 m**, against the
5.39 m INV-491 asks for.

**Why the material comes from the ground.** Hard rule 4 — inside and outside from one
schema — applied to a third thing. A crop whose colour is authored separately would
drift from the parcel it stands in and the drift would be invisible until somebody
looked at a frame. Heights: crop 0.95 m (below a standing eye, so 34b's readable parcel
patchwork survives from above), tussock 0.42 m and scrub 0.85 m from `garden.TUSSOCK_R_M`
/ `SCRUB_R_M`, clipped hedge 0.82 m against 29a's "clipped hedges about head height"
which `garden.HEDGE_H_M` already reads as 1.05 m.

**Overturned by** `drum_ground` changing `CELLS_A`/`CELLS_Z`, which this follows.

## INV-493 — The near field's density is four times the Garden's, and it was solved rather than set

**What.** `drum_dressing.NEAR_DENSITY_GAIN = 4.0`, a multiple of
`garden.TUSSOCK_PER_100M2` = 4.4 and `SCRUB_PER_100M2` = 2.0, read from `garden.py`
rather than restated. The first entry of each recipe is a **primary** and is guaranteed
one per cell.

**Why solved.** `--derive-near` walks a ladder and reports the smallest gain at which
every land-use band passes both floors of INV-491:

```
gain 1.0  worst nearest 3.80 m   worst band water      60.5%  FAIL
gain 2.0  worst nearest 3.80 m   worst band water      55.6%  FAIL
gain 3.0  worst nearest 3.13 m   worst band settlement 50.7%  FAIL
gain 4.0  worst nearest 3.11 m   worst band settlement 48.6%  PASS
gain 8.0  worst nearest 3.11 m   worst band settlement 41.9%  PASS
```

**Two things worth reading off that table rather than just its answer.** The DISTANCE
floor passes at every gain including 1.0 — proximity is bought by the guaranteed
primary and density buys none of it; density buys COVER. And the binding band is never
arable: it is the town and the lake shore, which is exactly where a scatter-density
parameter is no use, and is what sent the settlement to a plot wall instead of more
grass (INV-494).

**Why it is not the Garden's own number.** 4.0 × 4.4 = 17.6 tussocks per 100 m², one
clump every 2.4 m — a meadow. The Garden's 1.0 describes a **mown civic terrace** that
also carries paving, a pool, benches, lamps and a colonnade inside the same 35 m. The
ratio between the two is the finding, not a fudge.

**Overturned by** any change to the floors in INV-491, or by `garden.ground_cover`
re-deriving its own densities — this is a multiple of them and follows.

## INV-494 — A town's near view is bounded by walls, not filled with objects

**What.** `drum_dressing.WALL_H_M = 1.25`, `WALL_W_M = 0.34`. A settlement lattice cell
whose neighbour is an avenue, a verge or a carriageway gets a plot wall along that
frontage instead of a clipped hedge, one lattice cell long plus 6% overlap so
consecutive cells join into a continuous run.

**Why, and it is arithmetic rather than taste.** Solved against the near gate, the
settlement band needed **eight times** the Garden's ground-cover density to get its
below-horizon view under 50% bare, and eight times the grass in a town centre is an
absurd answer to a real number. A 3.6 m clipped hedge at 5 m covers about 3% of the
below-horizon panorama, so seventeen of them are needed; ONE continuous 1.25 m wall
along a frontage at 8 m covers about a third of the band over half the azimuths. With
the wall the band passes at gain 4 and its bare view falls 71.6% → 43.9%.

**And it is what the reference asks for and nothing was building.**
`03-sector-blue/Babylon_5_2-22_33a.jpg` (authority 1) — "rectangular built parcels
carry a fine internal grid". `drum_ground` cuts that grid into the podium as avenues;
the plot boundary standing on it did not exist. 1.25 m is below a 1.7 m eye, so a
player sees over the wall down the street.

**The frontage is read off the ground's own kinds**, never a second street table, so the
wall follows whatever grid `drum_ground` cut.

**Overturned by** a ground-level authority-1 frame of the drum's built half showing open
plots rather than bounded ones. `2-22_33a` is a wide shot and cannot settle it at eye
level.

---

# The measurement, and it fails on the content it was written against

`python3 station/drum_dressing.py --near` / `--near --bare`. 209 standing
positions — a uniform 16-angle sweep **plus three angles inside every land-use
band**, because a uniform sweep of this drum lands no position in the 36°-wide
water band and the first version of this gate reported PASS with the shore
unmeasured.

| | control (`--near --bare`, the drum as 4q left it) | after |
|---|---|---|
| nearest thing standing, median | **32.42 m** | **2.32 m** |
| nearest thing standing, worst | **99.34 m** (parkland) | **3.28 m** (arable) |
| features per hectare within 11.05 m, median | **0** | **1,278** |
| below-horizon view that is bare, drum-wide | **95.2%** | **34.5%** |
| worst band | arable **97.2%** | settlement **43.9%** |
| verdict | **FAIL** | **PASS** |

The control is not a stub: it is the drum exactly as session 4q left it, all
1,945 far-field features present, with only the near rung withheld.

Both floors are in INV-491 and neither was chosen. `drum_dressing._selftest`
carries the gate, the control, and a check that the control fails *for the right
reason* — `nb.nearest_worst_m > 10 × n.nearest_worst_m`, i.e. for having nothing
NEAR rather than nothing at all.

**Self-tests:** `station/drum_dressing.py` **276/277** (the one failure is the
honest drum-budget red below); `station/drum_ground.py` **82/82**.

# Frames — all Forward+ / Vulkan 1.4.318, checked in the render log

| | path |
|---|---|
| before, down the axis (`--stand 20,4700 --look 20,6300`) | `docs/near-4q-before-axis.png` |
| after, same camera | `docs/near-4r-after-axis.png` |
| **before, HALF distance** (eye 262.197,95.432,4700 → target 263.802,96.016,4704, 23.1° down) | `docs/near-4q-before-half.png` |
| **after, same camera** | `docs/near-4r-after-half.png` |

The before frames were rendered from a `git worktree` holding `fdc27bf`'s
`drum_dressing.py` against the *current* `garden.py`, so the only difference
between the pair is this session's module.

**My own craft score at the rubric's half distance: 1 → 2.**

*Before* is `AAA-STANDARD`'s C1 verbatim — two flat colour fields meeting along a
straight-edged polygon boundary, nothing standing on either, and the green
parcel carries no texture at all.

*After* has real relief, row structure that converges on the vanishing point,
a scatter with silhouette, a bank between the two parcels, and four materials
where there were two. It is **not a 3**, and the three reasons are:

1. the near tufts are 6-sided 3-stack domes and read as faceted at 1–2 m;
2. the crop takes its parcel's own `ground_arable_*` material, whose normal map
   is **cracked earth** — so a standing crop reads as ploughed soil at 2 m;
3. the green parcel still has no ground texture between the tufts at all.

(2) and (3) are `materials.py`, not this module — see the patches below.

# Findings — things that are WRONG in the repo or in the brief

**1. `drum_dressing.worst_case_cost` is 104,842, not 119,868.** STATE.md §24.6,
INV-452 and `docs/aaa-scorecard.json` all say it is "**unchanged** at
119,868 / 120,000" after the 4q garden rebuild. Measured on the **committed**
module (`git show fdc27bf:station/drum_dressing.py`) against the **current**
`garden.py`, it is **104,842**. Level 0 of this module's tree and town block IS
`garden.tree()` / `garden.block_building()`, so rebuilding them moved it. The
brief inherits the stale figure ("currently 119,868 used"). The practical
consequence is good news: the whole near rung fits inside the existing
`DRESSING_TRIS` with 5,090 to spare, and `--derive` even offers a *longer*
level-0 reach (118.4 m), which is declined for the reason below.

**2. `drum_dressing._selftest` was asserting the drum's budget with a hard-coded
`fixed = 75_968`, and the true figure is 104,374.** That constant is a copy of
another module's cost: it contains `garden.townscape` at 22,620, which is
**51,026** since 4q. The assertion was passing with 28,406 triangles it could not
see. Now measured from the same parts `export_scene.drum_parts` emits, pinned as
`DRUM_FIXED_TRIS`, and asserted.

**3. The drum is over its own allowance, and it was before this session.**
Priced the way a renderer prices it — one eye at a time, not three worst cases at
three different places — the worst standing position is **315,604** against
`budget.DRUM["visible_set_tris"]` = 300,000: fixed 104,374 + ground 96,320 +
dressing 114,910. Without the near rung the same eye is ~305,700. **`budget.py`
is not this module's file** and another agent is editing it (INV-500..503), so
this is left as an honest RED in `drum_dressing._selftest` with the cause named
in the failure message, rather than absorbed by quietly cutting `DRESSING_TRIS`.

**4. The brief's third bullet is not correct, and being wrong about it is
useful.** *"`drum_ground`'s own half of that boundary is a drawn line rather than
a change in the ground."* Measured over 140 tagged boundaries against a paired
control window in open field at the same z, the boundary carries **0.231 m more
relief than open field (median), 0.536 m at p75**, and at the finding's own eye
it is **1.05 m over 28 m**. The ground does change. What it does not do is change
*visibly*: 0.49 m over a 32 m window is **0.88°**, while the MATERIAL changes
instantaneously at the cell boundary. A hard tonal step on a surface with no
visible geometric step is exactly what "a drawn line" describes — and the cure
is an object on the line, not a sharper heightfield, because `drum_ground`'s step
rule forbids anything under one 31.2 m stride-8 cell and its own history records
what a 3.5 m step cost (a 3.28 m lod1 error, a 3,379 m switch distance, and the
entire 573,440-triangle field at lod0). `drum_ground._selftest` now carries both
halves of that as assertions, and both controls fire.

**5. My own first version of that measurement could not fail.** Written as an
absolute — "the 32 m window across a boundary changes by 0.581 m" — it survives
`PARCEL_RELIEF_M = 0` almost intact (0.269 m), because a 32 m window anywhere on
a six-octave fbm field changes by about that much. It is now a paired
differential and the control drives it to **0.011 m**.

**6. A keep-out radius has to be the footprint, not the circumscribed disc.**
The first version kept near cover out of a disc around every standing thing and
included `gantry`, whose boom is 87.4 m of pipe on two legs — clearing a 44 m
disc of crop and taking the arable band's worst nearest-object distance from
3.30 m to 24.01 m in one run. An irrigation boom is a frame you stand a crop
under. Fixed to oriented rectangles from `prototype_dims` turned through each
block's own placed yaw, and `_KEEPOUT_KINDS` cut to things with a solid footprint.

**7. Three fovs exist in this project.** The player's **70** (`player.gd:279`),
the render shot's **46** (`export_scene.SHOT_FOV_DEG`), and this module's LOD
constant **50** (`drum_ground.FOV_DEG`). A near-field floor derived from the
wrong one looks derived and is wrong. Every committed drum frame is composed at
46, whose below-horizon median is 8.36 m — so the frames are a *conservative*
view of this defect, not an exaggerated one.

# Patches for files I do not own

# INV entries for session 4r — the counters. Block INV-560..569.

**DO NOT EDIT `canon/INVENTIONS.md` FROM HERE — these are for the integrator to append.**
Written in that file's format so they can be moved across verbatim.

**All five are already cited by number in `station/economy.py`** — at lines 469/480 (560),
480/… (561), 644 (562), 1321 (563) and 678 (564) — so `tools/inv_check.py` reports them as
DANGLING until these entries are appended. That gate was **already red before this session**
with twelve dangling citations, including three other agents' pending blocks
(INV-530/531/533/534 in `vista.py`, INV-540/541 in `drum_ground.py`, INV-550 in
`enforcement.py`) and four long-standing ones (INV-074, 078, 140, 141, 232). Appending this
file's five entries clears exactly the INV-56x rows and nothing else.

Block used: **INV-560, 561, 562, 563, 564** — 565..569 unused and free.

---

## INV-560 — A station sells SERVICES as well as goods, and their prices are ladder rows verbatim

**What.** `economy.SERVICES` is four things a counter takes money for that are not units of
stock: `passage home` (300.00 cr), `a bunk for the night` (1.00), `a hot meal` (0.00, issued)
and `a stake at the table` (1.00). Each is attached to a place by a **register function** —
`ship_departure`, `informal_residence`, `catering`, `gambling` — never by a place key, so the
list of places that sell passage is derived from `directory.py` exactly as `Good.sold_by` is.

**Why the whole economy was a shop.** `GOODS` is 33 lines of spoo and bearings and every one
of them is a thing you carry away, so `vendors()` was 13 places and the 28 places declaring a
`serve`-verb prop resolved to **9** that could take a credit. On the deck the shipped build
actually boots into (`blue_0_0`) the number was **ZERO**: its one `serve` prop is
`docking_bays__prop_bay_control_booth` and `docking_bays` declares no selling function. Four
of the ladder's own eight rows — command quarters, transient room, dosshouse bunk, passage
home — are not goods at all, so the file could PRINT four prices nobody could pay.

**Why no multipliers.** `SUPPLY_MULT` exists because a good crosses hyperspace, and
`VENUE_MULT` because it pays rent on a shopfront. A berth on a departing hull does neither:
the ladder's 300–800 cr already *is* the fare. So a service price is the ladder row and
nothing is applied to it.

**Why the FLOOR of a band and not a draw inside it.** The first version drew inside the band
the way `price()` does for goods and quoted **618.69 cr** for passage. That number was wrong
for a reason worth keeping: **the project had already decided this price.** `player.py:194`
carries `PASSAGE_HOME_CR = 300.0` — *"a berth on an outbound transport (band floor)"*,
SPEC-CHANGE #1, owner-approved — and `CREDIT_SKEW` is *solved* against it so exactly 1% of
arrivals land under the line, which is the mechanism that produces Downbelow. A desk quoting
618.69 would have refused a player `Player.can_afford_passage()` had just cleared. So the rule
for every row: **a ladder band is the spread of a market and a counter quotes one price, the
cheapest thing the counter has** — a berth in economy, a bunk on the floor, the minimum stake.
`economy.price_check()` asserts identity rather than membership, and `_selftest` asserts
`price("passage home", "docking_bays") == player.PASSAGE_HOME_CR`, with the discarded draw
kept live as the negative control (it fires at +318.69 cr).

**A hot meal at 0.00 cr is a price, not a hole.** `mess_hall` is `("catering", "crew_social")`
— an EarthForce crew mess issues rather than sells. The ladder's `squat` row exists for exactly
this: *"and it is why people are there"*, 0.0, so that free is a price and not a missing entry.

**The stake is the one derived step.** `gambling` has no ladder row, so the minimum stake takes
`meal_cart`'s floor with one stated reason: a table whose minimum excludes the dockers and
lurkers `populace.occupancy` puts in that room is a table with nobody at it, and `meal_cart` is
the smallest discretionary sum the ladder carries. Authority 5.

**Overturned by.** any stated fare, tariff, rent receipt or table minimum from the show or a
production document. Each would replace one row and nothing else — the table is data.

---

## INV-561 — A service's stock is a real count of the thing that limits it, and passage home is berths off the manifest

**What.** `economy.outbound_berths(day)` returns **(free berths, hulls, seats)** sailing during
a station day. Day 0: **22 passenger hulls, 2,108 seats, 445 free**. Day 1: 606 free. Day 2:
1,093.

**How it is derived, with nothing added to the manifest.** A hull leaves when its stay is up,
and `traffic.arrivals()` already carries `hour` and `stay_h`, so the departure is arithmetic
rather than a second table. Its SEATS are its class's own capacity-band top
(`traffic.MANIFEST` column 5 — a `transport` is 86, a `liner` 800), and its outbound LOAD is
what it brought, which is TRAFFIC-AND-CUSTOMS §5.3's steady state: the transient population is
resupplied entirely by arrivals, so over a day out equals in. **Free = capacity − load.** A
hull that came in full leaves full, and on a day when they all did, the shelf is honestly
empty and the desk says so.

**Why this shape.** It is `consignments()`'s own rule applied to people: *"a delivery is a real
container off a real ship"*. A berth invented from a number would be the one thing that rule
exists against.

**The passenger classes are derived too.** `pax_classes()` reads `traffic.MANIFEST` and takes
every row that is not in `CREW_STAYS_ABOARD`, not in `FREIGHT_CLASSES`, and whose soul band
tops out above zero. A class that carries nobody cannot sell a seat.

**Overturned by.** any stated outbound load factor, or a manifest that carries departures in
their own right instead of implying them from `stay_h`. The second would be strictly better
and is a `traffic.py` change, not this one.

---

## INV-562 — A service is sold across ONE counter, and one counter is `COUNTER_M2`

**What.** Where no physical count exists, a service's daily demand is
`counter_covers(place)` — `populace.occupancy` summed over the clock across
`min(floor_m2(place), COUNTER_M2)` rather than across the place's whole footprint.
Measured: `downbelow` **84**/day, `downbelow_arch` and `mess_hall` **106**, `casino` **165**.

**Why, and it is a lesson this file already paid for once.** `economy.py`'s own comment says
*"A COUNTER IS NOT A DISTRICT, and the first version of this file forgot it"* — occupancy over
Downbelow's 654,370 m² footprint gave it 235,572 retail transactions a day. A bunk desk has the
identical shape and would have inherited the identical defect:
`daily_covers("downbelow_arch")` is **4,714**, a district's worth of beds behind one desk.

**No new constant.** `COUNTER_M2 = 225.0` is already solved in this file — `bar_unnamed`'s own
register footprint, the authority-1 bar, one counter — and `MAX_RETAIL_M2` is 44 of them, from
PLACES §0.3's stated 44 Zocalo stalls. A service reuses the smaller figure because it is one
desk and not forty-four.

**Overturned by.** a stated bunk count for any Downbelow squat, or a stated cover count for the
mess. Either would replace the derivation for its own row and leave the rest.

---

## INV-563 — A service is replenished by the day, not by a ship

**What.** `economy._renew_services(led, day)` tops each service line up by one day's demand and
caps it at `RESTOCK_DAYS` (3) of it — the same depth `opening_stock` gives a goods line — and
it runs inside `deliver()`.

**Why it is the goods rule with one word changed.** A goods shelf stands three days deep and is
topped up by what it sold, off a real crate off a real hull. A service shelf stands three days
deep and is topped up by what it sold, because **tomorrow is another night and another ship**.
That is the only difference between the two nouns anywhere in the module, and stating it once
here is what stops it becoming a special case with its own rules. The fourteen-day drift check
did not have to be widened to admit it: 55,757 → 55,822 units, **×1.001**.

**And it is deliberately skipped when `deliver(only=...)` names its consignments**, because that
call exists so `dockwork.py` can prove the crates the player's own gang worked are the crates
that arrived. Renewing berths inside it would put units on a shelf no gang moved.

**Overturned by.** a service whose supply genuinely is a shipment — a bonded line, a licensed
quota — which would want the goods path instead and already has it.

---

## INV-564 — `SELLING_FUNCTIONS` is the union; `GOODS_FUNCTIONS` is what carries stock

**What.** `GOODS_FUNCTIONS` is the old five (`commerce, retail, hospitality, food_service,
black_market`) and `vendors()` reads it. `SELLING_FUNCTIONS` is now
`GOODS_FUNCTIONS | SERVICE_FUNCTIONS`, and it is the union because
`consequence.sells_to` asks it exactly one question — *is this place a counter at all* — and a
desk that takes 300 credits for a berth is a counter by any reading of that word.

**Why the split is load-bearing rather than tidy.** `vendors()` is read by `incident.py`
(*"the thirteen counters that hold stock"*), by `consequence.counters_for` and by
`consignments()`. Widening it would have moved every goods number in the project. Measured
A/B against `git show HEAD:station/economy.py`, run in one process: over fourteen days of real
manifests the opening and closing GOODS stock of all thirteen vendors is **identical**, and the
only tills that move differently are the five places that gained a service. `demand_of()` is
what buys that — a mixed counter (`downbelow` gained a bunk beside its black-market lines)
spreads its `daily_covers` across its **goods** lines exactly as before, instead of dividing
by one line more.

**Overturned by.** nothing factual — this is a code-shape decision, recorded because the two
names are one character apart in use and a future edit that reaches for the wrong one will
silently move thirteen counters' worth of arithmetic.

---

## Unused in this block

**INV-565 … INV-569** — reserved to session 4r and not used. Free.

**INV-570 … INV-579** — allocated to the session-4r materials agent (garden bark and foliage,
the arable normal map, customs screens, `cc_console_face`). **INV-580 … INV-589** — allocated
to the session-4r exterior-components agent. Written down here rather than held in a brief
because two agents on one day have already made INV-450 and INV-451 mean two things each, and
the register is the only place an allocation survives a context reset.

**Nothing is reserved for the z-awareness work of session 4r, deliberately.** `narrowest_z`,
`place_floor_radius` and `interior.hull_fit` invent no dimension, no layout and no name: they
measure places against the hull the schema already defines, using the limit
`rings_fitting_at` already applied. A gate that asks an existing standard of more subjects is
not an extrapolation, and giving it an INV number would put a method parameter in a register
of claims about the station. The finding is in `STATE.md` where a finding belongs.

# INV-550..559 — WHAT HAPPENS AFTER A REFUSAL (session 4r, agent P2)

**NOT MERGED INTO `canon/INVENTIONS.md` BY THIS AGENT, DELIBERATELY.** Two agents wrote to that
register on the same day and two numbers ended up meaning two different things each (INV-450,
INV-451). The block reserved for this work is **INV-550..559**; `tools/inv_check.py` gates the
merge. Copy these entries in verbatim, in order, at the end of the register.

Owner: `station/enforcement.py`, `godot/scripts/enforcement.gd`,
`godot/scripts/interact.gd::fine/convict`.

---

## INV-550 — A refusal detains one time in five, drawn per event and not per day

**What.** Whether a given refusal ends in detention (LAW-CRIME 2.7 rung 4) or in "move on"
(rung 3) is `consequence._u("detain_on_refusal", npc_id, place, day, nth) < DETAIN_ON_FAIL`,
where `nth` is how many times this person has been stopped at this place today.
**Why.** `DETAIN_ON_FAIL = 0.20` is INV-346 and has existed since P1-G2, but it had only ever
been used as a RATE — inside `day_arrests`, where it prices a station-day of the whole force. A
player meets it exactly once, standing in a doorway, so it has to resolve to a yes or a no for
**this** refusal. Nothing about the number changes; what is new is that it is now drawn.
**Constrained by.** Three things, and they are what stop it being a coin flip in a hat. (1) The
hash is `consequence._u`, the same one every fine amount, every deferral and every discretionary
stop in that module already uses, so the fork sits on one seed line with the rest of the law
layer rather than on a new one. (2) It is keyed on the EVENT — person, place, day, and the stop
count — so reloading a save reproduces the same refusal and walking back in is a fresh draw. A
key without the place and the stop count is one number repeated: measured over the 98 places that
read a card, that control gives **0 of 98**, against **22 of 98 = 0.224** for the real key.
(3) The rate over the register is checked against `DETAIN_ON_FAIL` itself rather than asserted:
0.224 against 0.20 on 98 samples.
**Known limit, and it CYCLES rather than going quiet.** The baked table carries three stops per
place (INV-557's reason) and a player can make a fourth. The engine wraps the index instead of
falling through to "moved on", because a fourth refusal that could never detain is a rule that
switches itself off the moment somebody tests it — which is a worse answer than either branch.
Wrapping reuses the same draws in the same order, so it stays deterministic and holds the
one-in-five over a long session. Baking more rows would push the wrap further out and not remove
it.
**Overturned by.** Any figure for arrests per stop; by anything that says a second refusal at the
same door is treated differently from the first (which would make `nth` a rung rather than an
index).
**Authority 5.** `station/enforcement.py::_detain_draw`, `--selftest` checks 10 and 11 with its
own control.

---

## INV-551 — The responding pair becomes visible at 12 m, or at the last clear metre

**What.** The two officers appear `min(12.0 m, the last clear point of a ray from the player's
chest along the way out)` from the player, on the floor, and walk in a straight line at
1.30 m/s.
**Why.** They have to come from somewhere and the shipped build has no path-finder in GDScript
for a body that is not the player or a scripted commuter. Something has to decide where "coming
from the corridor" starts.
**Constrained by.** **12 m is not a new number**: it is `npc.gd::promote_walker`'s own default
radius, this project's existing answer to *"how far away is somebody who is here with you"* —
the distance inside which a collapsing body is a person who was standing there rather than a
corpse appearing out of the air. The same question, so the same answer. The RAY is what stops the
number being a guess: the officers are placed at the last point of a cast that starts at the
player's chest and ends where the world stops it, so the straight line they then walk has already
been proven clear by the cast that placed them. The speed is `life.gd`'s `walk_speed_ms = 1.30`,
what a commuting resident walks at on this deck, not a second gait.
**Known limit, stated rather than hidden.** The last leg is a straight line and not a route. On a
bay with a single doorway the ray usually places them in the doorway and the walk is honest; in a
room with a partition between the door and the player they will appear on the player's side of
it. Closing that needs `roomnav.py`'s waypoints in the engine, which is `route_walk.py`'s job and
not this one.
**Overturned by.** A GDScript path-finder for non-player bodies; any depiction that fixes how
security enters a room.
**Authority 5.** `godot/scripts/enforcement.gd::APPROACH_MAX_M`, `_spawn`, `_walk_in`.

---

## INV-552 — Arrival is 2.4 m, because that is the distance a thing can be operated at

**What.** The pair has ARRIVED when the horizontal distance from the player is ≤ 2.4 m.
**Why.** A gate needs a moment that is unambiguously "they are here".
**Constrained by.** 2.4 m is `interact.gd::reach_m` and is not re-decided: being close enough to
be handed a citation is the same distance as being close enough to press a console, and a second
constant here would be a second answer to one question. `dialogue.gd` uses its own, wider figure
for a conversation, which is correct for a conversation and wrong for this — a citation is handed
over, not called across a room.
**Overturned by.** Nothing sourced; it is a threshold, and any figure derived from a depicted
stop would replace it.
**Authority 5.** `godot/scripts/enforcement.gd::ARRIVE_M`.

---

## INV-553 — The escort is reported, not walked, and the release is into the corridor

**What.** A detention does not move the player's body to the brig. The chain's legs are reported
one at a time — seizure, escort, booking, hold, court, fine, release — the station clock is
advanced by the routed total, and the player is put back in the corridor outside the place they
were refused from.
**Why.** `consequence.BRIG` is a real place in the register and it is neither on this deck nor in
any streamed cell: teleporting a body into a cell that has not loaded drops it through the world,
and walking it there is 6 km and four decks on a graph the engine cannot yet drive a non-player
body along.
**Constrained by.** Every duration a player reads is the routed one — escort **11.8–15.2 min**
across the six places of the boot deck, hold **0.8 h at 06:00 and 23.8 h at 07:00** because the
Ombuds sit at 08:00, court 1.2 min, total ~19 h — so nothing about the chain is softened, only
the camera. The RELEASE POINT is derived from the same box `hud.gd` will test the player against
on the next frame (place box + `_resolve`'s own 1.5 m of slack + 1 m), ray-verified, and put on
the floor by a second cast: a player escorted to a point that happened to still be inside would
be refused again on the next frame, for ever.
**What would overturn it.** The brig streaming in — at which point the escort becomes a walk and
this entry is replaced rather than amended. That is the right next increment for this subject.
**Authority 5.** `godot/scripts/enforcement.gd::_settle`, `_outside`, `_foot`.

---

## INV-554 — The countdown runs in real seconds, and the compression is printed

**What.** The wait between a refusal and the pair arriving is the routed response time in REAL
seconds. `--arrest-rate=N` divides it; every verdict line prints `rate=xN`.
**Why.** The response time is the most interesting number this subject produces — **0 s in
`docking_bays`, which has a post standing in it, against 227 s in `lowg_bays` from customs
north** — and it is only interesting if a player experiences it. Compressing it by default would
delete LAW-CRIME 2.6's contrast, which is the layer's whole dramatic geometry.
**Constrained by.** The station clock is not used for it, and that is a decision: `life.gd` runs
at 0.017 station-hours per real second (61x), so a 227 s turn-out on the station clock would land
in under four seconds and a player would never learn that the outer ring is a place nobody comes
to. The gate compresses (x40) because a gate that took twelve minutes would not be run.
**Overturned by.** A design ruling that the whole simulation runs on compressed time, in which
case this rides that rate instead of real seconds.
**Authority 5.** `godot/scripts/enforcement.gd::rate`, `LEG_DWELL_S`.

---

## INV-555 — A refusal at a reader is `id_check_fail`, and no new offence was minted for it

**What.** The offence a refused player is stopped for is `consequence.OFFENCES`' existing
`id_check_fail` (grade 1, escalation rung 2), and the non-detention disposal is the existing
`move_on` (grade 0, rung 3).
**Why.** It looks like it wants a new row — "trespass", "entering a restricted area" — and it
does not.
**Constrained by.** The table's own source sentence for `id_check_fail` is *"a card that does not
read. 2.7 rung 2 is the commonest interaction and most of its failures end at rung 3"*, which is
exactly what a refusal at a boundary IS: the card was read and it did not admit you. Minting a
second offence would put two rows in one table describing one event, and the fine ladder would
then have two answers for it. The grade-1 fine is **8–10 cr, one day of casual labour**
(INV-347), which is the right order for the commonest interaction on the station: a citation, not
a catastrophe.
**Overturned by.** Any depiction of a distinct charge for being somewhere you are not cleared
for.
**Authority 5.** `station/enforcement.py::REFUSAL_OFFENCE`, `MOVED_ON_OFFENCE`.

---

## INV-556 — The consequence table is baked per place and per hour, and only the hold moves

**What.** `station/generated/scene/enforcement.json` carries, per place, the response and its
post, the two officers, the fork, the four fixed legs, and **24 values each of hold and total**,
indexed by the hour of arrest.
**Why.** The engine must hold no copy of the rule (hard rule 4), and a rule evaluated at bake
time has to be evaluated at every input the runtime can present. The clock is the only input the
player controls.
**Constrained by.** Measured rather than assumed, and ASSERTED at bake time: for every place and
every one of the 24 hours, `respond + escort + booking + hold[h] + court + release` must equal
the total `consequence.arrest` reports to within 0.2 s, or the bake raises. If any leg but the
hold moved with the clock, indexing the hold alone would be a fiction and the totals would be
wrong. The shape is checked as well as the sum — a table of 24 identical numbers would pass the
sum and mean the hour was inert, so the selftest requires a spread of more than an hour and gets
**0.8 h at 06:00 against 23.8 h at 07:00**, which is the 08:00 Ombuds sitting.
**Overturned by.** A second clock-dependent leg — a night court, a shift change in the escort —
at which point the table gains a second indexed row rather than losing the rule.
**Authority 5.** `station/enforcement.py::place_row`.

---

## INV-557 — The conviction ladder is baked for every rung, not just the one the card reads

**What.** `detention.ladder_by_tier` holds three successive disposals from each of the six rungs.
**Why.** `--tier=N` forces the card in the engine (`main.gd::_check_gate`'s own control, on the
grounds that it is the identicard that changed and not the reader), and `consequence._dispose`
answers differently at every rung: EA citizenship cannot be withdrawn by an Ombuds at all, the
floor rung has nothing left to take and the next disposal is transfer off-station, an accredited
card is immunity and the file dies. A build that showed one of those for all six would be a rule
with its interesting half filed off.

**AND THE HEADLINE THIS ENTRY WAS FIRST WRITTEN WITH WAS WRONG, WHICH IS WORTH KEEPING.** The
first draft said "a transit visa is withdrawn on the second ordinary conviction", and the
selftest that checked it PASSED — because the shipped player stands on the floor rung, where
`REVOCABLE` is `None` and the check took its other branch. **It could not have failed for the
case it was named after.** Asked at all six rungs, the ladder revokes at NONE of them, and the
cause is one line: `Record.ordinary()` counts grade-2 convictions and `id_check_fail` is grade 1.

That is the right answer and it is now asserted as such. INV-347 prices grade 1 at one day of
casual labour — a citation — and a station that withdrew a visa for two citations would have no
middle to its own escalation ladder. **A refusal at a door, on its own, never costs you your
standing.** It costs a day's wages, a night in the brig and a line on the card. Revocation needs a
grade-2 conviction, which is a different verb (carrying, petty theft, expired status) and another
session's work. The selftest carries a POSITIVE CONTROL running the same `_dispose` at the same
rung one grade heavier, so "it never revokes" cannot quietly become "the machinery is absent".
**Constrained by.** It calls `consequence._dispose` — the module's own disposal rule — with a
`Record` accumulating convictions, rather than restating the rule. The fine does not move with
the rung (it is per offence and per person), so it is carried across from the ladder that was
actually routed.
**Overturned by.** Nothing; it is a projection of an existing rule onto an existing axis.
**Authority 5.** `station/enforcement.py::place_row`, `by_tier`.

---

## INV-558 — A fine is a transfer to the court in the ledger a drink moves through

**What.** `interact.gd::fine()` debits the purse, credits `law_courts`' till, appends a row to
`sales` naming the offence, and writes the document. An unpayable fine is not an error: the debt
is recorded as outstanding and the player walks out with it.
**Why.** The money has to be real or the sentence is a caption.
**Constrained by.** It is `consequence._post_fine`'s four numbers and no fifth — that function's
own comment says *"NOT a new wallet and not a new file: `economy.Ledger.till` and `.sales` and
`.purses` are the existing three"*. The rounding follows `_verb_serve`'s, which is load-bearing
rather than tidy: `economy.buy` totals at 2 dp and a purse keeps millicredits, and an `int()`
truncation there once ate 0.20 cr of a 0.80 cr drink. The "walks out with the debt" reading is
LAW-CRIME 4.3's Jinxo precedent read economically — the brig is a remand facility and not a
debtors' prison — which `consequence.arrest` already applies on the Python side.
**Overturned by.** Any depiction of what B5 does about an unpaid Ombuds fine.
**Authority 5.** `godot/scripts/interact.gd::fine`, `_record_fine`.

**AND IT GAVE ITS OWN GATE AN EXPIRY DATE, which is worth recording because the money being real
is exactly what caused it.** Five verification runs took the shipped purse from **420.50 to
372.40 cr** — five detentions at 9.62 cr, each one correct. At that rate the gate stops passing
after about thirty-eight runs, when the purse cannot cover the fine and `paid` becomes
`OUTSTANDING`: a gate that spends its own subject's money is a gate with a countdown on it.
`enforcement.py::_run` now copies the ledger into a temp directory and passes
`--ledger=<copy>` — which `interact.gd::ledger_path` already honoured — and then reads the copy
back off disk, so the verdict rests on **a file having changed** rather than on the runtime saying
it did.

---

## INV-559 — The conviction is written into the purse, because that is what survives

**What.** `interact.gd::convict()` appends the offence to `purses[<player>].record.convictions`,
increments `custody_events`, and on a revocation writes `visa_revoked`, `revoked_from`, a dated
note, and the new rung onto the body.
**Why.** A consequence that does not survive the process is a mood.
**Constrained by.** That is `player.py::state()`'s own sentence, and the key already exists:
`state()` writes `record` when there is one and `restore()` reads it back, so the engine is
filling a channel the simulation already opened rather than inventing a save format. The shape is
`consequence.Record.state()`'s, field for field, so a Python session that loads the purse after
the engine wrote it gets a `Record` and not a dictionary of surprises.
**Overturned by.** Nothing; it is the existing serialisation used from the other end.
**Authority 5.** `godot/scripts/interact.gd::convict`, `_record`, `_put_record`.

# INV-530..539 — what is outside a window (session 4r)

**DO NOT PASTE INTO `canon/INVENTIONS.md` BLIND.** These are written in that file's
format and reserved to the block INV-530..539 assigned to this agent. `tools/inv_check.py`
gates the register; merge them there once, in one commit, after checking no other agent
has claimed the same numbers.

Everything below is authority 5 (declared extrapolation) unless it says otherwise. The
measurements are of `reference/03-sector-blue/comand and contorl.webp`, **authority 1**,
made with `scratchpad/vista_measure.py` (linear Rec.709 luminance on sRGB-decoded pixels,
the same arithmetic `tools/measure_frame.py` uses).

---

## INV-530 — the station fills 0.852 of C&C's window

**What.** `station/vista.STATION_FRAC_REF = 0.852`, tolerance 0.050. The fraction of the
window's vertical field that the station's own hull occupies, as against sky.

**Why.** The single most important fact about the C&C window is the one no gate in this
project could express before: it is **not a starfield**. At 5× magnification
(`tools/refzoom.py --box 0.33 0.11 0.70 0.45 --scale 5`) it is full of the station — a
large curved mass with a hard limb across the upper part of the aperture, pinpoint running
lights over it, and dark sky only in the narrow band beyond the limb.

**What constrained it.** Read off that crop: the aperture circle spans x 170–1320 px, so
its diameter is 1150 px and its top is y 60; the limb crosses the vertical centreline at
y ≈ 230. (230 − 60)/1150 = 0.148 sky, therefore 0.852 station.

**What would overturn it.** A cleaner frame of the same set. The source is 814×610,
compressed and motion-blurred, and the read is worth about ±0.05 and not better — which is
why the tolerance is stated at 0.05 and why `vista.py` gates on the qualitative claim
(*"the station fills most of the window"*, > 0.5) rather than on the arithmetic. A band
fitted to 0.852 would be a number tuned until the content passed.

---

## INV-531 — a window pane transmits 0.840

**What.** `station/vista.PANE_TRANSMITTANCE = 0.840`, applied as `albedo_color.a = 0.160`
on a duplicate of `materials.viewport_glazing`.

**Why.** `viewport_glazing` is **opaque** — albedo 0.040,0.042,0.046, roughness 0.07,
specular 0.92 — and `materials.py`'s `Material` class has no transparency field at all, so
there is nowhere in the library to say "this surface is glass". A window you cannot see
through is a window rendering black, which is the defect this session exists to close.

**What constrained it.** Fresnel at normal incidence for borosilicate, n = 1.52:
R = ((n−1)/(n+1))² = 0.0426 per air–glass interface. A pressure window is two panes, i.e.
four interfaces: T = (1 − 0.0426)⁴ = **0.840**. The remaining 0.160 is what
`viewport_glazing` actually measured — its own source note says the drum "reads through it
unattenuated" and that its 0.042 albedo came from a region its next clause calls
"near-black vertical MULLIONS with a dark SILL", i.e. the frame around the pane and not the
pane. So the entry keeps every value it measured and gains the transmission it never had.

**What would overturn it.** A reference frame showing the same object through and beside
one pane, which would give T directly. Also: an anti-reflection coating would take T to
~0.98, and a heavy tint would take it below 0.5; nothing in the show settles which.

---

## INV-532 — the view through a window is lit at sun energy 4.2

**What.** `station/vista.VISTA_SUN_ENERGY = 4.2`, the `DirectionalLight3D.light_energy` on
the vista's own sun (cull-masked to the vista's visual layer, so it lights the station
outside and nothing in the room).

**Why.** An absolute level cannot be taken from the reference frame: it is uncalibrated and
heavily blue-cast. What survives the cast is a ratio measured **within** the frame — the
glazing against the bulkhead it is set in, both under the same cast and the same lens.

**What constrained it.** Measured on the reference: four pane samples mean linear Y
**0.0431**, bulkhead **0.0190**, so the view is **×2.27** the wall. Measured the same way
on our own frame at sun energy 1.0: pane 0.0138, wall 0.0257, **×0.54**. A directional
light's contribution to a diffuse surface is linear in its energy and no other light
reaches the vista, so the correction is 1.0 × 2.27/0.54 = **4.2**. Verified:
`docs/craft-4r-cnc-half-window-after.png` measures **×1.99**, inside the ±0.60 band, and
the control `docs/craft-4r-cnc-half-window-before.png` measures **×0.11**.

**What would overturn it.** Any change to `materials.hull_exterior`'s albedo or to
`interior.tscn`'s tonemapper moves this ratio without moving this number. Re-measure with
`station/vista.py --selftest`'s FRAMES block, which re-takes the frame from its own
recorded command; do not re-guess.

---

## INV-533 — on this station the view is upside down against the show

**What.** A window on Babylon 5's hull has **the station above it and space below**. The
show's C&C frame has the mass at the bottom of the window and sky above.

**Why it is not a defect to fix.** The ring spins, so `deck._place_local`'s "up" is
**inward**, toward the axis — the centrifugal floor is the outer wall. From any window on
the hull the station's own body is inward and the only direction that leaves the hull is
outward. Measured: a ray from C&C's window running parallel to the axis stays at r = 118 m
while the hull grows to 234 m going aft, so it is inside the station before it has gone
300 m. Hard rule 4 — inside and outside from one schema — decides the tie in the schema's
favour.

**What constrained it.** `station/vista.station_side()` reports it per window by casting
the two extreme centreline rays; C&C reads `inward`. The full 46° render frame is
compatible with the show's *composition* anyway, because over the wider field the aft flank
at larger radius fills the lower half: measured on
`docs/craft-4r-cnc-half-window-after.png`, the lower pane sample is linear Y 0.106 against
the upper's 0.022.

**What would overturn it.** A canon statement that C&C is in a non-rotating section. The
schema has none; `station.rotation` gives one figure for the whole station.

---

## INV-534 — an observation dome's window is gated on geometry, not on composition

**What.** `obs_dome_1` and `obs_dome_2` are not gated against INV-530's 0.852. They are
gated on facing radially outward (outward component > 0.9) with a station fill < 0.05.

**Why.** `reference/03-sector-blue/comand and contorl.webp` is a frame **of C&C's window**.
No frame in this project shows what an observation dome looks out at. A dome is a blister
on the hull whose viewports face radially outward and whose whole job is to look at space,
so its fill is near zero by construction, and asserting 0.852 of it would be asserting a
number no reference supports.

**What would overturn it.** Any authority-1 frame through a dome viewport.

---

## INV-535 — a window's aperture stands off the hull by its component's height

**What.** `station/vista.PLACE_COMPONENT` maps `cnc`, `obs_dome_1`, `obs_dome_2` →
`observation_dome` (height 34 m) and `obs_rotundas`, `domed_rotunda` →
`observation_rotunda` (height 40 m). The aperture sits at the hull's radius at its z **plus
that height**.

**Why.** A window is an aperture in the pressure boundary, so its radius is the hull's — but
a room inside a blister is not flush with the plate. Observation Dome 1 stands 34 m proud
of the hull and C&C is inside it; the register, the schema's `observation_dome` component
(authority 3, Contract 5, *"OB. DOME 1 (COMMAND & CONTROL)"*) and
`command_control.py`'s docstring all say so in their own words.

**What constrained it.** `height_m` is read out of the schema component, not restated;
`--selftest` fails if a named id is not in the schema. The apex is used rather than a
fraction of it because that is the one point on a blister that is defined without a second
free parameter.

**What would overturn it.** A frame or a plan establishing where in the dome the window
sits. A window halfway up the dome's flank would take the standoff to ~17 m and bring the
near hull closer.

---

## INV-536 — the star field a window shows is the exterior's, lifted rather than copied

**What.** `station/vista.star_shader()` generates
`station/generated/scene/vista/vista_stars.gdshader` by lifting `hash33()` and
`star_layer()` **verbatim** out of `godot/scenes/space_sky.gdshader` and wrapping them in a
spatial shader that runs on a shell mesh.

**Why.** `space_sky.gdshader` is `shader_type sky` and can only be mounted on an
Environment. Mounting one on the interior scene would change the ambient and the
reflections of **every** interior frame in the project, and 23 of them are gated on their
distribution by `tools/measure_frame.py`. A second, hand-written star function would be two
descriptions of one thing — the defect this repository has recorded three times.

**What constrained it.** The lift is by regex over the source and **raises** if either
function is renamed, so it fails loudly rather than emitting an empty sky.

**What would overturn it.** Godot growing a way to sample a sky shader from a spatial one,
at which point the wrapper is unnecessary.

---

## INV-537 — the vista is clipped by three geometric facts and no budget

**What.** `station/vista.visible_hull()` keeps a hull triangle when it is in front of the
window plane, front-facing to the aperture, and inside the LOD band the chain itself
declares for its distance. `VIEW_RANGE_M = 12000`.

**Why.** Every one of the three is a fact rather than a saving: a triangle behind the pane
is inside the room's own wall; the hull is a closed surface, so a triangle facing away is
the far side of the station seen from inside it and can never be seen; and
`station/generated/lod_manifest.json` already says which level is honest at which distance.
12 km reaches the far end of an 8,047 m station from any window on it.

**What it costs, measured.** cnc **96,498** triangles (32.2% of the 300,000 visible-set
budget, 25.3% of `hull_lod0`); obs_dome_1 **29,387** (9.8%); obs_dome_2 **26,660** (8.9%).
Back-face culling alone takes cnc's forward view from 6,235 to 778. `station/budget.py` is
honestly RED already — the drum measures 315,604 against 300,000 — so no new bound is
invented here; the number is stated and the existing bounds do the failing.

**What would overturn it.** A measurement showing the window's own solid angle hides most
of it. From the room's deepest standing point the aperture subtends only 12.1° half-angle
(2.73 m radius at 12.77 m), so a camera-aware cone clip would cut this by most of its
value — and it is wrong as a general answer, because a player at the glass sees the whole
hemisphere.

---

## INV-538 — the sky turns at 10.76 deg/s and the hull does not

**What.** `station/vista.sky_basis(ap, phase)` = Bᵀ·R_z(−φ). The hull carries no phase.

**Why.** Stars are fixed in the inertial frame; the station rotates about +Z. This is the
one thing a painted backdrop cannot do and it is why the view is geometry.

**What constrained it.** `station.rotation.omega_rad_s` = 0.187717056 and `period_s` =
33.471574, both already in the schema, both authority 5, read rather than restated. A
quarter turn is **8.37 s** and the sky sweeps **10.76 °/s** — fast enough that a player
standing at a dome window sees it move.

**Measured in the engine.** `docs/craft-4r-obsdome1-phase000.png` against
`docs/craft-4r-obsdome1-phase090.png`: **3.39% of the pixels in the glazing band differ,
max delta 206/255**, while only 0.95% of the whole frame differs — the sky moves and the
room does not. The negative control is real and fired: before the shader took its direction
from the shell's own object space, the same A/B was **0.00% different**.

**What would overturn it.** Canon placing C&C or the domes in a non-rotating section.

---

## INV-539 — C&C's window faces the wrong way along the axis

**What.** `station/vista.aperture()` aims a window along the room's own window normal **or
its half turn about the room's vertical**, whichever sees the station, and reports which.
For `cnc` it chooses the half turn.

**Why.** The room as `command_control.py` builds it puts its window normal along room-local
+Z, which `deck._place_local` maps to the station's axis **forward**. Measured: facing
forward the station fills **0.000** of the window — it looks past the nose at empty space.
Half-turned it fills **0.740**, looking down 8 km of station, which is what the reference
frame shows.

**What constrained it.** A half turn about the vertical is `(x, y, z) → (−x, y, −z)`, the
transform `deck.door_sign` already applies for the side of the corridor a plaque is on. It
is a **rotation**, so it preserves winding; a mirror would point the room the right way
with every face inside-out, which is the defect session 3x found in `dressing._cyl` and
which no render would show.

**What would overturn it.** Fixing the register instead — see the session report's patch 3.
The half turn is this module's *description* of what the build should do; the build still
faces the room forward, and the rendered frames therefore show the room as the patch would
place it. That is stated in the manifest (`yaw_deg`) and printed on every run.

**Honest negative.** A first version solved a continuous outward **tilt** so the fill hit
0.852 exactly. It was deleted: fitting the geometry to a composition is picking the
convenient reading, and the number it produced (−32.5°) had no physical meaning.

# INV-540..549 — the drum's triangle budget, session 4r

**NOT YET IN `canon/INVENTIONS.md`.** Written here because two agents wrote to that
register on the same day and two numbers ended up meaning two things each; the block
INV-540..549 is reserved for this work and `tools/inv_check.py` gates the merge.
Entries are in the register's own format and can be moved across unchanged.

Block used: **INV-540, INV-541, INV-542**. INV-543..549 are unused and free.

---

## INV-540 — The drum ground's LOD error is a property of the PATCH, not of the drum

**What.** `station/drum_ground.py` gains `PATCH_LOD_ERR_MM` — the deviation of each of the
five decimation strides from lod0, measured on each of the 280 ground patches separately, in
millimetres — plus `patch_lod_table()` and `patch_level()`, which `visible_set` and
`visible_cost` now use in place of `level_for_distance`.

**Why it is not a change of standard.** The switch criterion is untouched: still
`_switch_distance(err)`, still 1.5 px of deviation, still the same screen model, still the
same five strides and the same triangle counts per level. Only the DOMAIN of the error
measurement changes. `lod_error_report()` measures whole patches at full resolution — one per
land-use band — and then takes the `max()` and applies it to every patch on the drum, so the
lake pays the settlement podium's error and the parkland pays the arable's finest noise
octave. Measured over all 280 patches, the stride-4 switch distance the drum-wide table
imposes is **554 m** and the per-patch answer ranges **113 to 713 m** — a factor of 6.3.

**What constrained it — the collision contract, not a preference.** `station/drum_walk.py`
builds its collision tile at a uniform stride 1 and then asserts two things against the render
ground: that a body stands on the ground it can see (within `STEP_M` = 0.100 m), and that
inside the render's own lod0 radius the two are the IDENTICAL surface. Both are statements
about the mesh inside that tile, so inside the tile the per-patch table is floored by the
drum-wide one:

    switch[i] = max(per_patch[i], min(drum_wide[i], collision_reach_m()))

`collision_reach_m()` is read from `drum_walk.patch_span_m()` and `rings_for(walk_distance_m())`
— **449.7 m**, the corner of the 5 × 5 patch tile — never restated. Asserted over every patch
at 5 m intervals inside that radius: **0 of 24,920 patch-distance samples go coarser.**
Verified end to end: `drum_walk.py --selftest` reports `max -97.8 mm` before and `max -97.8 mm`
after, and `within the render's own lod0 radius (198 m, 92 casts): 0.000 um` in both. The rms
*improves*, 20.5 → 20.1 mm, because of the second half of this entry.

**AND IT IS ALSO A CORRECTION, WHICH IS WHY THIS IS NOT A BUDGET TRICK.** The representative
sample is one patch per band at mid-length and it MISSES the worst patch: per-patch stride-8
error reaches **1.974 m** where the representative maximum is **1.048 m**. Those patches now
switch LATER — they are drawn FINER than they are today. **360 of the sampled positions inside
the collision tile get more triangles than they have now, not fewer**, and `_selftest` asserts
that count is non-zero, because if the per-patch measurement found nothing the `max()` had
hidden there would be no reason to keep 1,400 numbers.

**Measured worth**, on `budget.DRUM`'s own 4 × 3 lattice, verified through
`export_scene.drum_parts` at the worst eye (270°, 5132 m) rather than through the counting path
alone:

| | before | after |
|---|---|---|
| ground | 96,320 | **70,880** |
| drum visible set | 315,604 = **105.2% FAIL** | 290,164 = **96.7% PASS** |
| drum share of frame | 26.3% FAIL | 24.2% PASS |
| `budget.py` | 21/28 | **23/28** |
| patches per level at the worst eye | 16 / 88 / 134 / 42 / 0 | 16 / 47 / 74 / 143 / 0 |

**Pinned rather than derived at import**, for the reason `drum_dressing.DRUM_FIXED_TRIS` is
pinned: the derivation is 305,000 `sample()` calls and costs **51 s**, and no gate should pay
that to answer a question about a committed terrain. `python3 station/drum_ground.py
--derive-patch-lod` rebuilds it, prints the replacement table and fails on drift;
`_selftest` re-measures four patches (one per land-use band) on **every** run at 0.8 s, so the
pin cannot rot silently, and carries a control that perturbs one pinned value by 40 mm and
requires the check to fire. `PATCH_LOD_DIGEST = "3b42b398bcc5242e"`, blake2b over the table,
the same instrument as `GROUND_DIGEST`.

**Overturned by** any change to `sample()` — which is what the digest and the per-run
re-measurement exist to catch — or by a streaming budget for the drum, which would make the
whole visible-set question a different one.

---

## INV-541 — The habitat drum cannot be occlusion-culled, and the ceiling is 5.3%

**What.** `station/occluders.py --drum` measures what an occluder could buy inside the drum and
the answer is **15,336 of 290,164 triangles — 5.29%**, leaving the drum at 91.6% of its
allowance. No occluder geometry is built for the drum and none should be.

**Why it is geometry rather than engineering.** The drum's inner surface is the boundary of a
CONVEX region, and every point of the boundary of a convex region is visible from every point
inside it. `godot/scenes/drum.tscn`'s own lighting note already states the physical form of
this — *"a closed cavity of 4.5 million m² … every surface can see most of the others"* — and
`budget.DRUM`'s comment states the consequence: *"no occlusion — there is no wall to hide
behind"*. Nothing can hide anything except relief and the objects standing on it, and both are
now measured instead of asserted.

**The control is the convexity itself, and it fires.** Flatten the heightfield to the mean
cylinder and re-cast: **0 of 1,440 targets blocked**. A single blocked target there would mean
the measurement is reading its own arithmetic rather than the terrain.

**What the ceiling is a ceiling OF**, stated because every term is generous: it culls a target
the moment it is hidden, charges nothing for the occluder geometry, nothing for the depth
rasterisation, and tests at a per-feature granularity no renderer in this project works at. It
is weighted by the triangles each hidden thing would have contributed **at the level the LOD
chain would have drawn it** — a copse hidden at 1,200 m is 30 triangles and a farmstead hidden
at 30 m is 800, so a percentage of *features* would have said nothing about a budget.

| | hidden | of | ceiling |
|---|---|---|---|
| ground patches | 6 | 280 | 864 tri of 70,880 = 1.22% |
| dressing features | 179 | 1,945 | 14,472 tri of 114,910 = 12.59% |
| the fixed parts | — | — | 104,374 tri, **not cullable at any granularity** |

**And one level down it is worse than the ceiling.** Godot tests an INSTANCE's axis-aligned
bounding box against a rasterised depth buffer, not a triangle. `render_shot.gd` reports
**147 mesh instances over 9 files** for the whole drum, split by MATERIAL GROUP rather than by
place — `ground.glb` is 13 nodes spanning 4.5 million square metres, and not one of those AABBs
can ever be behind anything. This is CLAUDE.md's own corridor finding (*"Godot culls per
instance AABB and the corridor's OBJ groups span the whole 345° ring"*) one environment along,
with the same conclusion: what would close a drum budget is **spatial submission**, and there is
nothing for an occluder to do until that exists.

**Overturned by** the drum being submitted per patch or per cell rather than per material
group — at which point this measurement should be re-run, because the ground's 1.22% is a
number about *patches*, and a per-cell dressing submission is where the 12.59% would start to
be reachable.

---

## INV-542 — The drum gate's worst eye is a town street, and a 168-eye sweep confirms it

**What.** `budget.DRUM`'s 4 × 3 lattice puts its worst standing eye at **(270.0°, 5132 m)**.
That is inside the second settlement band (`interior.LAND_USE` puts settlement at 259.2–302.4°),
on terrain `drum_ground.sample` tags **`avenue`** at **+6.75 m** — a street in the drum's town,
which is about as unambiguously a standing position as anywhere on the drum.

**Why this needed checking at all.** INV-501 states the lattice's own error as **16.2%**
(13.6% after INV-540), measured against its half-resolution sub-lattice, and the drum now passes
with a margin of **9,836 triangles** — *smaller* than that stated error. A verdict inside its
own sampling error is not a verdict, so the question "is the 4 × 3 worst eye the drum's worst
eye" stopped being academic the moment the gate went green.

**Measured, not argued.** A **24 × 7 = 168-eye** sweep through the same counting paths
(`drum_ground.visible_cost` + `drum_dressing.dressing_cost` + `DRUM_FIXED_TRIS`, 39 s):

| | |
|---|---|
| worst eye of 168 | **(270.0°, 5132 m), 290,164** — the same eye the 4 × 3 lattice finds |
| eyes over the 300,000 bound | **0 of 168** |
| next four | 287,220 (330°, parkland) · 286,960 (285°, avenue) · 286,906 (120°, avenue) · 286,674 (135°, avenue) |
| best eye | 215,830 |

So the 13.6% figure is the sub-lattice's disagreement, not the true uncertainty: **every eye
within 3.3% of the worst is at z = 5132 m**, mid-length, which is where the whole barrel is in
view, and the circumferential station barely matters. The gate's lattice is coarse in the axis
that matters least.

**What constrained the answer.** `budget.py` is not this session's file and the 4d ruling
forbids growing gates, so nothing was added to `drum_eyes`; this is a property of an existing
gate, measured and recorded, and the coarse lattice is left alone precisely because it was
*stated rather than placed on the answer* and it found the answer anyway.

**Overturned by** any change to `interior.LAND_USE`'s band positions or to `drum_dressing`'s
placement, either of which moves where the expensive standing positions are and makes this
sweep stale. Re-run it before quoting the margin.

---

## INV-570 — the library can say "this is glass", and the shim that stood in for it retires

**What.** `materials.Material.transmittance`, a new field defaulting to `0.0`, set to
**0.840** on `viewport_glazing`. `tres()` writes `albedo_color`'s fourth component as
`1 - transmittance` and — only when it is non-zero — `transparency = 1`.

**Why, and it is a MOVE rather than a derivation.** 0.840 is INV-531's number and its
reasoning is unchanged: Fresnel at normal incidence for n = 1.52 gives R = 0.0426 per
air-glass interface, a pressure window is two panes and therefore four interfaces, so
T = (1 - 0.0426)^4 = 0.840. What changes is where it lives. It was
`station/vista.PANE_TRANSMITTANCE`, applied by `godot/scripts/vista.gd::glaze()` to a
per-surface **duplicate** of the bound material at load time — so the pane was transmissive
on the render path and opaque everywhere else, including the streamed build a player
launches, which never calls that script. A property of a surface belongs to the surface.
**INV-531 is retired, not renumbered**: its derivation stands and its implementation is
superseded by this entry.

**What constrained the WRITER, and this is the part that was nearly got wrong.** Godot gates
the whole transparent path behind an enum and discards `albedo_color`'s alpha at
`TRANSPARENCY_DISABLED`, so alpha alone is a silent no-op. The patch this implements asked
for `transparency = 1` **and `depth_draw_mode = 1`**. Printed out of `BaseMaterial3D` in this
project's own double build rather than remembered:

```
TRANSPARENCY_DISABLED=0   TRANSPARENCY_ALPHA=1
DEPTH_DRAW_OPAQUE_ONLY=0  DEPTH_DRAW_ALWAYS=1  DEPTH_DRAW_DISABLED=2
```

`depth_draw_mode = 1` is **DEPTH_DRAW_ALWAYS** — the opposite of the shim it replaces, which
sets `DEPTH_DRAW_OPAQUE_ONLY`, i.e. **0**, i.e. the default. So the correct line is no line
at all, and writing the patch's would have made a pane you look through stamp depth over the
view behind it. `depth_draw_mode` is also absent from `materials.STANDARD_MATERIAL_KEYS`, so
the existing key gate would have caught it as a name and never as a value.

**Measured, three ways, one camera** (`--shot interior --room cnc --eye 0,1.7,4.2 --target
0,3.65,8.42 --res 960x540`, Vulkan 1.4.318 Forward+ throughout, boxes from
`vista.FRAMES`):

| | pane / wall | engine's own readback |
|---|---|---|
| **A** shim only, library opaque | **×1.99** | `1 pane surface(s) made transmissive … 0 already transmissive in the library` |
| **B** library `transmittance=0.840`, shim finds it done | **×1.99** | `0 pane surface(s) made transmissive … 1 already transmissive in the library` |
| **C** neither — `glazing_groups` emptied AND library opaque | **×0.29** | `0 … 0` |

Frames: `docs/mat-4r-glass-transmissive.png` (B) and `docs/mat-4r-glass-opaque-control.png`
(C). A is byte-identical to B and is therefore not committed twice.

**A and B are BYTE-IDENTICAL (md5 `fc97094b…`), and that is the result rather than a failed
test.** The shim already produced this pixel on this path, so equivalence is what a correct
move looks like. What stops that being vacuous is C: 87.6% of pixels differ from A, max
channel delta 147, and the pane collapses to ×0.29 of its wall. And what proves the library
value reached the engine is not a picture at all — it is `vista.gd` reading
`sm.transparency != TRANSPARENCY_DISABLED` back off the loaded material and reporting **1
already transmissive**, which it had never reported before.

**What constrained the split it does NOT do.** `viewport_glazing` binds `prop_viewport` and
`cc_glazing` together, and C-003 is open on whether a given rotunda faces in or out. A
transmissive pane shows whatever is behind it, so the two now differ by their **vista** and
not by their glass; the split becomes unnecessary rather than urgent, and is not made here.

**Overturned by** a reference frame showing the same object through and beside one pane
(which would give T directly), an anti-reflection coating (T ≈ 0.98) or a heavy tint
(T < 0.5) — the same overturning conditions INV-531 recorded, inherited unchanged. Also by
`station/vista.py` learning to read `materials.BY_NAME["viewport_glazing"].transmittance`
instead of keeping `PANE_TRANSMITTANCE`, at which point `materials._selftest`'s
"vista.py's copy of T agrees with the material's" check becomes trivially true and should
go.

---

# BACKFILLED ENTRIES — five citations that predated the register check (session 4r)

`tools/inv_check.py` has been RED since it was written, on five numbers cited in code with no
entry here. The CI step's own comment calls them "pre-existing", which is true and is not a
reason to leave them: **hard rule 2 says a number that looks sourced and is not is exactly what
hard rule 1 forbids**, and a citation pointing at nothing is the purest form of that. Each of
these was already argued, carefully, in the file that cites it — what was missing was the entry
a reader following the number would land on. Written from the code's own reasoning, not
re-derived, and each says where the real argument lives so the two cannot drift.

## INV-074 — the session-3u dressing surfaces are INV-073's painted board, not a new material

**What.** `dress_crate`, `dress_crate_lid`, `dress_door`, `dress_top`, `dress_clutter`,
`dress_soft` and the `alien_*` trim bind to the same painted-board material INV-073 was measured
for. **Why.** Case bodies, cabinet doors and work tops in the show's interiors are the same
painted plane as the wall trim around them, worked into relief rather than finished differently;
introducing a colour for them would be inventing a distinction the reference does not show.
**Constrained by.** `materials.check_material_coverage()` — every emitted group must bind, so the
alternative to reusing this entry is authoring a new one, not leaving them unbound.
**Overturned by.** Any authority-1 frame in which a crate or a work top reads as a different
material from the dado beside it. **Authority 5.** The argument is at `station/materials.py:2253`.

## INV-078 — a radial shaft runs enough cars for a two-dwell headway

**What.** `navigation.shaft_cars(schema, span_m)` = `round(headway / SHAFT_TARGET_HEADWAY_S)`,
with `SHAFT_TARGET_HEADWAY_S = 2.0 × TRANSIT_DWELL_S = 40.0 s`. **Why.** The mean wait is about
one dwell — a car turns up roughly as often as it takes to load one — which is the only
self-consistent target available, because `TRANSIT_DWELL_S` is already this project's measure of
how long a door stands open. Two dwells is the point past which boarding rather than waiting is
the cost of using the thing. **Constrained by.** It falls out per sector rather than being
tabulated: Grey's shaft spans 382 m and gets 10 cars, Green's spans 29 m and gets 2. One constant
could not have been right for all five, which is the check that this is a derivation and not a
number. **Overturned by.** Any frame showing a lift lobby — the number of doors in it IS the
bank. Nothing in the show counts lift cars. **Authority 5.** Argument at
`station/npc/navigation.py:1651`.

## INV-140 — `rooms.PLAN_ELEMENTS`: what is in the middle of a room's floor, by activity

**What.** 114 activity keys mapping a room's declared function to the plan elements on its floor
— a counter you queue at, rows you sit in, cells you sleep in — each with a size and an
arrangement. **Why.** A room built from its declared interactables alone is controls without
machinery; this is the other half, and it is what makes a named activity read as that activity
from the doorway. **Constrained by**, and all four are asserted rather than intended: the element
must leave the room crossable by a 0.9 m walker; must not occupy the same cubic metre as anything
else (by construction, see `place_elements`); must fit under the room's own ceiling; and must be
the arrangement the named activity actually has. `_selftest` also asserts every name resolves to
a real fixture. **Overturned by.** Any reference frame of one of these rooms showing a different
arrangement — this is the table most likely to be wrong in detail and least likely to be wrong in
kind. **Authority 5.** Argument at `station/rooms.py:493`.

## INV-141 — clear height is keyed on FUNCTION, on a ladder of clearance arguments

**What.** `rooms` ceiling heights run on a ladder from 2.40 m (a berth: 1.70 m standing plus
hair, and a bunk you sit up in) upward, each rung a clearance argument rather than a taste.
**Why.** `docs/variety-V0.md` §5 measured the SECTION channel as the worst number in the whole
variety measurement — **47.6% of all 8,128 pairs above the ceiling there**, median 0.699 against
0.269 for plan — and §7 gives the cause in one line: **48 of 128 places shared a 2.90 m ceiling**,
with eleven distinct heights on the entire station, one per archetype.
**Constrained by, and this bounds what the entry can achieve.** A cross-section IoU between two
box rooms is exactly `min(h1,h2)/max(h1,h2)`, so two rooms are told apart on section alone only
if one is **1.37× the height of the other**. This table therefore does NOT break clusters on its
own and is not meant to; it moves the distribution, and moves `rib_pitch_m` and `light_pitch_m`
with it, which are plan. **Overturned by.** A measured floor-to-ceiling in any authority-1
interior frame. **Authority 5.** Argument at `station/rooms.py:99`.

## INV-232 — a walk test's success bar is the engine's own reach, 2.4 m

**What.** `walkable.USE_RANGE_M = 2.4`, the distance a body must end up within for "you walked up
to it" to mean anything. **Why.** It is not a chosen tolerance: `godot/scripts/interact.gd`
declares `@export var reach_m: float = 2.4`, and the bar on the WALK is set AT the engine's reach
so a body that stops outside arm's length fails even if a generous prompt cone happened to light
up. Setting it looser would let the walk gate pass on a body that cannot touch the thing.
**Constrained by.** The two numbers must stay equal; they are in different languages and
different files, which is the drift risk this entry exists to name. **Overturned by.** Any change
to `interact.gd::reach_m` — which must move this constant in the same commit. **Authority 5.**
Argument at `station/walkable.py:294`.

---

## INV-580 — The cargo train's proportions, measured off the orthographic sheet as ratios

**What.** The dorsal cargo modules' spacing and proportions, taken from
`reference/01-station-exterior/exterior more.jpg` (authority 2, production orthographic renders):

| measured | px | ratio to module length |
|---|---|---|
| module length along z | 18.33 | 1.000 — the datum |
| gap between modules | 15.80 | **0.862** |
| module width across | 17.0 | **0.927** |
| module height, side view | 16.0 | **0.873** |

**Why these are ratios and not metres.** The sheet carries no scale bar, so INV-018's rule
applies: store the figure as a ratio and the unknown scale cancels. Calibrating instead against
the station's own 8,047 m over its 1,152 px length gives ~6.99 m/px and a module 128 m long,
but that calibration is soft — the run I measured may not be the station's full extent in that
view — and every use below needs only the ratio.

**How it was measured.** Thresholded on the modules' red against a neutral hull
(45 < r < 200, r − g > 18, r − b > 18) over the top view's rows 176–192 and the side view's
rows 400–450. Six runs at x 639–657, 673–691, 707–724, 742–759, 776–793, 810–827: six modules,
which settles 00-INDEX's "~5–6" at **six**. Grey pixels fill 14 of 15 and 14 of 16 columns in
two of the five gaps and some of every other one — the plinths, measured rather than assumed.

**What it constrains.** The modules occupy **0.537** of their own pitch (18.33 / 34.13).
`station/schema/station.yaml` sets `fill: 0.62`, which is 15% longer than measured. That is a
schema key and not this module's to change; the proposal is in
`scratchpad/PATCHES-4r-exterior.md`.

**The one that is NOT built, stated plainly.** The measured module height is **0.873** of its
length; the schema's `protrusion_m` of 46 m against a built length of 117.8 m is **0.390**, less
than half. Building to the measurement would move the station's silhouette and trip
`validate.py`'s radius envelope, so `station/components.py` builds strictly inside the schema
and the discrepancy is recorded here and proposed in the patch file rather than acted on.

**Overturned by** any authority-1 frame of the dorsal line, or by a scale anchor on this sheet
that fixes the metres rather than the ratios.

---

## INV-581 — The cargo train is a train: rail, plinths, feet and a loader gantry

**What.** `station/components.py::dorsal_line` builds, besides the six modules: a continuous
raised dorsal rail with cross-ties running the whole run, a grey plinth in each of the five
gaps, two feet under every module, and a machinery block closing the fore end.

**Why — and this is a cross-check, not a single reading.** Two authority-2 sources that could
not have copied each other say the same thing:

* `01-station-exterior/exterior more.jpg`, production orthographic renders — "six dark-red
  rectangular modules ... sitting on a continuous **raised dorsal rail** with small grey plinths
  between them. Six, not '5–6'." (00-INDEX)
* `other map 4.jpg`, the Miller print sheet — "A **dorsal row of ~6 small square modules on a
  rail** runs aft-of-centre along the spine, with six blue leader arrows taking them to six
  callout boxes under the heading **AUTO LOADERS SEQUENCE**." (00-INDEX)

The second also says what they are *for*, which is why the run terminates in a gantry rather
than in nothing: these are auto-loader positions.

**What constrained it.** `station.yaml` has carried `rail: True` on this component since the
component was written, and `rail` appeared nowhere in `station/components.py` — a sourced fact,
declared in the schema, that no builder read for eleven sessions. `_selftest`'s
`unread_spec_keys` check now fails on that class of defect rather than on this instance of it.

**What would overturn it.** A frame showing the modules standing directly on hull plate.

---

## INV-582 — The container's own construction: frame, castings, corrugation, hatch

**What.** Each cargo module is built as a welded structural frame with recessed panels between:
four corner posts and perimeter top and bottom rails at 6.5 m section standing 2.4 m proud,
eight corner castings oversailing the posts by 1.45, nine corrugation ribs per wall panel at
1.1 m proud, and a recessed loading hatch inside a raised rim on the top face.

**Why, and it is extrapolation — authority 5.** The sheet resolves a module at 18 px and shows
none of this. What it does establish is *what the object is*: a freight container at an auto
loader position. A container IS a welded frame of corner posts and top and bottom rails with
corrugated panels between them, and the corner castings are the lift points the loader grabs.
So this is the object's own construction rather than decoration applied to a box, which is the
distinction AAA-STANDARD draws between C1's "detail that reads as noise" and C4's "a fitting is
where a fitting would be needed".

**What constrained the numbers.** Three tiers with a stated ratio between them, because
AAA-STANDARD C3 asks for "a primary form, secondary structure, tertiary fittings" and a box
cannot have one: the container at 118 m, the frame at 6.5 m standing 2.4 m proud, the
corrugation at 1.1 m proud — **half** the frame's relief, deliberately, so the frame still reads
as the higher tier rather than as more of the same. The hatch is on the top face because that is
the face an auto loader reaches and the face the arrival framing looks straight down at.

**Cost.** 72 → 5,652 triangles across the six modules and their rail, and the component's
articulation ratio moves from **1.02×** a plain box to **8.61×**.

**Overturned by** any frame resolving a module's surface.

---

## INV-583 — A communications grid is a lattice, and the end views say so

**What.** `pylon_pair` no longer builds a 1,060 m solid strut carrying a solid 893 × 300 m
plate. It builds a three-step root bracket, a mast of six tapering segments with a collar at
each joint, and an open Warren-braced lattice: two booms at the inner and outer radius, two end
posts, nine radial ribs and one diagonal per bay.

**Why.** `01-station-exterior/exterior more.jpg` carries both end views, and in each of them the
grid reads as **a short dark stub arm at the equator carrying a very long hairline-thin mast**
— 2 to 3 px of width against a hull some 370 px across — with **no broad panel anywhere on it**.
00-INDEX records the reading twice and independently: "two very long thin masts run vertically
far beyond the hull silhouette in *both* end views, and two shorter stub arms project laterally
at the equator", and for the Miller sheet "long thin masts extend beyond the hull at spine level
toward the fore end".

An open framework of thin members reads as a thin mast at 100 km; a solid 893 × 300 m plate does
not. The lattice is also what the object's own name says it is.

**What is NOT changed.** `span_m` 1,060.25 and `grid_width_m` 893.2 are untouched — the extent
of the component is exactly what the schema says and only its construction has changed. The span
is corroborated (2,120.5 m tip to tip against masts that visibly overrun the hull in both end
views); the width is ambiguous, see INV-584.

**The bay spacing is biased, and that is structural.** The mast meets the grid at its mid-span,
so that is where the shear is and where a real truss puts its bays closest together; bays are
spaced by |2f − 1|^1.45. It also removes the one thing about this component the eye could index,
which AAA-STANDARD C4 asks for.

**Cost.** 48 → 888 triangles across both pylons; articulation **2.19× → 10.56×** a plain box.

**Overturned by** any authority-1 or -2 view resolving the grid's face.

---

## INV-584 — "Width at communications grid" is ambiguous, and it is not resolved here

**What.** `canon/00-MASTER.md` §1.1 lists, in Miller's rescaled specification table,
`Communications grid span | 819 | 2120.5` and `Width at communications grid | 345 | 893.2`.
`station/schema/station.yaml` uses the second as `grid_width_m`, i.e. as the grid panel's own
width along the station axis. **That reading is not established.**

**The two readings.** Every other row of that table is a *section* dimension — "Blue Section
diameter", "Bio-Habitat interior length" — and "width **at** X" reads naturally as the station's
width at X's location, exactly like "Bio-Habitat interior diameter". Against that: "span" and
"width" paired together are also the two dimensions of one panel.

**What the measurement says, and it does not settle it.** The hull's own profile gives a diameter
of **301.2 m** at the grid's placed z (2,751 m) and **329.6 m** at z 2,515 — nowhere near 893.2.
So the location reading is not satisfied by the current placement either. Either the grid is
placed at the wrong z, or 893.2 is the grid's own width, or the table's row means something
else again.

**Why it is left open.** This is a `CONFLICTS.md`-shaped ambiguity in a canon table, and hard
rule 3 forbids resolving one by picking whichever reading is convenient. `station/components.py`
therefore uses `grid_width_m` exactly as the schema hands it over and changes only the
construction (INV-583), so the component's extent is unmoved whichever reading wins.

**What would settle it.** A scale anchor on `exterior more.jpg`'s end views fixing the masts'
span in metres, or Miller's own text for that table row.

---

## INV-585 — The cargo rail's grey, as a same-frame ratio to the hull

**What.** Albedo **(0.473, 0.453, 0.513)** for the dorsal rail, plinths, feet and gantry —
proposed, not applied; the diff is in `scratchpad/PATCHES-4r-exterior.md` because
`station/materials.py` belongs to another agent this session.

**How it was derived.** Not measured absolutely: `exterior more.jpg` carries the render's own
grade, and INV-010 records that only differences *within* that sheet are trustworthy. The rail
band under the module row (x 639–827, rows 195–201) reads **65.64 / 65.08 / 84.22** against two
independent hull patches at **83.65 / 84.24 / 88.44** and **82.98 / 83.11 / 97.02** — ratios
0.785/0.773/0.952 and 0.791/0.783/0.868, which agree to 1% in R and G. Mean ratio
**0.788 / 0.778 / 0.910** applied to `materials.hull_exterior`'s 0.600/0.582/0.564 gives the
albedo above: the same plated grey as the hull, darker and slightly cooler, which is what an
unpainted structural rail beside a weathered painted hull should be.

**What constrained it.** 00-INDEX says "small **grey** plinths"; the measured saturation is
0.227 against the modules' 0.481, so the band is unambiguously the neutral member of the pair.

**What it costs while unapplied.** `SPLIT_RAIL_GROUP` is False, so the rail ships inside the
`cargo_module` group and takes the red container skin. The A/B is
`docs/craft-4r-ext-cargo-after-railmat.png` (bound) against
`docs/craft-4r-ext-cargo-after.png` (unbound). What is lost is a hue, not a shape.

**Overturned by** a production paint reference, which would replace this differential with an
absolute.

---

## INV-586 — The articulation floor: 3.0× a plain box, derived from its own control

**What.** `station/components.py::ARTICULATION_FLOOR = 3.0`. Every schema component's visible
line density, concatenated over every group it emits and normalised against a plain box of ONE
instance's surface area, must exceed 3.0.

**Why a floor at all.** Every other assertion in that file is topological — closed, wound
outward, inside its envelope, not floating, not interpenetrating — and CLAUDE.md's most
expensive lesson is that **a cube passes every word of a topological test**. Out here it cost
eleven sessions of `cargo_module` being six boxes and `comms_grid_pylon` being four, at 44/44
green throughout.

**Why 3.0, and it is derived from the control rather than chosen.** `boxed_control` rebuilds
every component as its own bounding boxes — which is exactly what the two failing builders WERE
— and that population tops out at **2.02×**. The least articulated real component is `cobra_bay`
at **5.43×**. The log-space midpoint is √(2.02 × 5.43) = **3.31**, taken as 3.0: rounded *down*
rather than up, so that where the derivation is soft the gate errs toward accepting a real
component rather than rejecting one. The self-test prints the control's maximum on every run, so
the number in the file cannot go stale silently.

**Two normalisations, and getting either wrong makes it lie.** Per INSTANCE, because
`lam_of_plain_box` builds its null from the total area handed to it and N instances of one shape
score √N higher — the 28 cobra bays read 20.31× over the group and 3.84× per bay, so a component
could otherwise pass by being numerous. And per schema COMPONENT rather than per emitted group,
because a dome IS its glazing and its mullions, and scoring the glazing alone asks a pane of
glass to carry line-work.

**Shown failing on the pre-fix content**, which is the only evidence that counts. Against
`git show 1982be0:station/components.py`: `reactor_cooling_fin` 34.20×, `forward_comms_plate`
18.46×, `space_traffic_prox_array` 16.65×, `heat_exchange_solar_array` 14.36×,
`observation_dome` 8.39×, `observation_rotunda` 8.34×, `docking_port` 8.31×, `cobra_bay` 5.43×
— and **`comms_grid_pylon` 2.19× FAIL**, **`cargo_module` 1.02× FAIL**. `cargo_module`'s own
boxed control is also **1.02×**, the identical number, because it *was* its bounding boxes.
Eight components pass unchanged, the two the frames showed to be boxes fail, nothing else does.

**What would break if it is wrong.** Too high and a legitimately smooth surface — glazing, a
radiator coating — is forced to carry decoration it should not have, which is C1's "detail that
reads as noise rather than machinery". Too low and it stops separating a box from a built thing,
which is the only job it has.

---

## INV-587 — A schema key no builder reads is a sourced fact that does nothing

**What.** `station/components.py::unread_spec_keys` fails when a component in
`station/schema/station.yaml` declares a key that no builder in that file reads, with
`SPEC_META_KEYS` exempt by kind and `SUPERSEDED_SPEC_KEYS` exempt by name *with a written
reason*.

**Why.** `cargo_module` carried `rail: True` beside a `src` that reads "six dark-red modules
countable on a continuous raised dorsal rail with grey plinths between them", and `rail`
appeared nowhere in `station/components.py`. The rail and the plinths were sourced, declared and
unbuilt, and nothing could say so. This is the same shape as the project's recurring
no-caller defect, one level down: not machinery with no caller, but *evidence* with no consumer.

**Why on the class and not on the instance.** CLAUDE.md: "a fix applied to an instance and not
to the rule is a fix that will be needed again." Building the rail closes `rail`; the check
closes the kind.

**The one live exemption.** `reactor_cooling_fin`'s `root_taper: 0.5`, superseded in session 3s
when `planar_blades` replaced a root-to-tip taper with `PLANFORM`, a seven-point lozenge read
off the same sheet — "tapered lozenges, wide at mid-height and narrowing at both root and tip"
(00-INDEX). A single taper factor cannot express that. The key survives only because
`station.yaml` is not that module's file to edit; its deletion is proposed in
`scratchpad/PATCHES-4r-exterior.md`.

**Its control has a trap in it and the trap fired.** The check scans this file's own source for
the key as a literal, so the negative control's probe key must be BUILT at run time rather than
written out — spelled out, it finds itself and the control passes vacuously. It did exactly that
on the first run. Same shape as `drum_ground`'s periodicity assertion comparing a value against
itself.

---

## INV-588 — The three distances are derived from the lens, and the lens is stated

**What.** The distances every exterior component in session 4r was scored at: **normal** = the
instance spans half the frame height, **half** = half of that, **one pixel** = the instance
spans one row. Per component, from its own longest dimension.

**Why derived rather than chosen.** AAA-STANDARD asks for "the distance the player normally sees
it from, half that, and the distance at which it is one pixel of silhouette", and CLAUDE.md
records that only the first was ever rendered for 118 interior locations — "at 200 m a box reads
as a building". A per-component rule removes the choice from the reviewer's hand and makes a
1,075 m grid and a 42 m cobra bay comparable.

**The lens, because a distance is meaningless without one.** Every frame is
`tools/export_scene.SHOT_FOV_DEG = 46.0` vertical over 720 rows, so D = S / (2·tan(FOV/4)) =
**2.458 S**. The shipped camera is **70.0** (`godot/scripts/player.gd:279`, vertical at Godot's
default `keep_aspect = KEEP_HEIGHT`), which puts the same framing at **1.586 S** — a player
reaches it at **0.645×** these distances. Every score taken here is therefore the *easier* test.

**And the LOD ladder is calibrated for a third lens.** `station/lod.py::FOV_DEG` is **50.0**
with no provenance, which makes every switch distance in the project ~33% too large. Every craft
frame in session 4r forces `--lod lod0`, so the ladder does not enter the judgement and these
scores survive that constant being corrected.

**Overturned by** a change to `SHOT_FOV_DEG` or to the shipped camera, either of which moves
every distance quoted in `docs/aaa-scorecard.json`'s `exterior_components` rows.

---

## INV-600 — the LOD chain's lens is READ off the shipped camera: 50° → 70°

**What.** `station/lod.py::FOV_DEG` stops being the authored constant **50.0** and becomes
`budget.shipped_camera()["fov_deg"]` = **70.0**, read out of `godot/scripts/player.gd:279`
(`_cam.fov = 70.0`). `station/drum_ground.py` and, through it, `station/drum_dressing.py` take
the same value by reference instead of restating it. Every switch distance in the hull chain,
the drum ground chain and the drum dressing chain therefore shortens by
`tan(25°)/tan(35°) = 0.6660`.

**This is not an extrapolation.** The *number* is read off the shipped camera and traces to a
file in this repository; what is extrapolated is the **screen model around it** — 1440 rows,
a 1.5 px deviation budget, a 1.0 px shading sample — and those were already authority 5 and
are unchanged. Authority 1 for the lens (it is the artefact), 5 for the model.

**Why 70 and not 50.** Godot's `Camera3D.fov` is **vertical** at the default
`keep_aspect = KEEP_HEIGHT`; that was verified in the engine (Godot 4.4 double, headless,
`Camera3D.new()` prints `fov=75.0 keep_aspect=1`) and is recorded in `station/budget.py`'s own
docstring. `budget.DECK["fov_v_deg"]` has been 70.0 since INV-083 for exactly this reason, and
`budget.shipped_camera()` re-reads `player.gd` on every run so it cannot drift. `lod.py`'s 50.0
had **no provenance at all** — it appears under the heading "The screen model" with no citation
and no derivation, and INV-588 had already flagged it as making "every switch distance in the
project ~33% too large".

**What it was costing, measured rather than argued.**
`switch_distance(e) = e · SCREEN_H / (2·tan(fov/2)·PIXEL_BUDGET)`. A *narrower* calibration lens
means more pixels per degree, a larger switch distance, and more triangles held for longer. So
calibrating at 50° while shipping 70° delivered

    PIXEL_BUDGET × tan(25°)/tan(35°) = 1.5 × 0.6660 = 1.00 px

of on-screen deviation against a budget that states **1.5 px**. **The chain was spending
triangles on precision nobody asked for and nobody can see.** Correcting it restores the stated
invariant exactly, by definition — it is a correctness fix, not a quality cut.

That 1.00 px is not a rearrangement of the formula. `lod.py::_selftest` measures it end to end:
it takes the silhouette schedule's own 5.831 m sagitta at 32 segments, puts it at 1/100 of the
distance the chain declares it acceptable, and renders it through `tools/preview_render.py` — an
independent rasteriser with its own camera basis and perspective divide — **at the lens read out
of `player.gd`**. At `FOV_DEG = 70` it covers **150.0 px** against the 150 asked for; at the
pre-fix `FOV_DEG = 50` it covers **100.0 px**, i.e. 1.00 px of deviation against a 1.5 px
budget. The control run is quoted in `scratchpad/PATCHES-4r-lodfov.md`.

**What actually moved. The chain's SHAPE does not change** — 8 levels, the same
segments/stride/greeble triple on each, the same triangle count per level — because a uniform
scale on every honest-from distance preserves their order. Only the distances move:

| | 50° (before) | 70° (after) |
|---|---|---|
| lod1 · 32 segments | 6,002 m | **3,997 m** |
| lod2 · 16 segments | 23,950 m | **15,950 m** |
| lod3 · z-stride 2 | 49,204 m | **32,767 m** |
| lod5 · greebles off | 73,249 m | **48,781 m** |
| lod7 · stride 8 | 181,027 m | **120,556 m** |

**The consequences, per consumer, and two of the three are negative results.**

* `tools/export_scene.py::pick_hull_lod` — the exterior shot in `tools/build_and_render.sh`
  (`--orbit 6400,15,208`, nearest hull point **4,271 m**) moves lod0 → lod1: **387,630 →
  261,166 triangles, −32.6%**, and that is *correct*, because 4,271 m is beyond lod1's honest
  distance at the camera a player is given. **`export_scene`'s own default `--orbit 9200,18,214`
  (nearest point 6,320 m) does not move — it was already lod1.** Nor does either camera's
  HALF distance: orbit 3200 puts the near point at 1,518 m and orbit 4600 at 2,425 m, both
  inside lod0 before and after. **The correction does not touch the frame at the rubric's half
  distance, which is where craft is judged.** INV-588 records that every craft frame in 4r
  forces `--lod lod0` in any case, so `docs/aaa-scorecard.json` survives this entry untouched.
* `station/vista.py::lod_bands` — the through-window vista is built band by band out of this
  chain over `VIEW_RANGE_M = 12,000 m`. The lod0/lod1 boundary moves **6,002 m → 3,997 m**, so
  2,005 m more of every window view is drawn at 32 segments instead of 64.
* **Greebles do not move at any distance a shot is taken from.** The greeble schedule's first
  non-trivial rung goes 73,249 → 48,781 m; every camera in this project is under 13 km, so
  `greeble_detail` is 1.0 before and after and no fitting changes. The greeble half of the
  brief this entry answers is a null result.

**AND IT ONLY REACHED THOSE CONSUMERS AFTER `station/generated/lod_manifest.json` WAS
REBUILT.** That file is tracked in git and is what `pick_hull_lod` and `lod_bands` actually
read; neither imports `station/lod.py`. With the code at 70° and the manifest still at 50°,
`--orbit 6400 --lod auto` selected **lod0** and printed *"from 0 m (binding schedule:
silhouette at 1,502 m)"* — the pre-fix number — while the derivation, the report and all 98
self-test checks were green. `python3 station/lod.py --build` regenerates it in **12.8 s** and
is committed alongside the code. CI runs `--build` (`validate.yml:491`) so CI was never wrong;
the checkout was. *A static scan can tell you a caller exists and a self-test can tell you the
derivation is right; only running the shipped path tells you which DATA the caller read.*

**WHAT THE FRAMES SHOW, AND ONE LIMIT OF THE DEVIATION BUDGET THAT THEY FOUND.** Four engine
frames, all confirmed `Vulkan 1.4.318 - Forward+`, at `--orbit …,15,208 --fov 42 --sun-az 238
--sun-elev 24`, 1280×720:

| pair | result |
|---|---|
| orbit 3200, **half distance** (near point 1,518 m) | **byte-identical, md5 `52b3957…`, 0 of 921,600 pixels differ.** Both select lod0 |
| orbit 6400, **normal distance** (near point 4,271 m) | lod0 → lod1. 7.76% of pixels differ at all, **0.43% by more than 16/255**, max channel 129, mean 3.76/255 over the station's own pixels |

Only **15 of the 41 OBJ groups** change between lod0 and lod1 and every one is a lathe group;
`cargo_module`, `cobra_bay`, `comms_grid_pylon`, `docking_port` and every `greeble_*` group are
byte-identical, which is the direct check that `greeble_detail` is 1.0 on both and the
**greeble half of this change is a null result**.

The interesting part is *where* those 0.43% sit. At the normal distance the coarser level makes
the cargo-rail truss under the drum flip from reading as a solid dark plate to reading as open
X-bracing. That is not the truss changing — a close-range control at orbit 2400 shows the
identical lattice in **both** levels — it is the 32-gon's inscribed silhouette pulling the
drum's edge inward by up to its 5.831 m sagitta and uncovering members the 64-gon was
covering. **1.28 px of silhouette movement, inside the 1.5 px budget, changed 2,002 pixels of
occupancy (0.22% of frame), because the budget bounds where the silhouette IS and says nothing
about what it OCCLUDES.** Where a structure lies tangent behind the hull, a sub-pixel edge move
uncovers a feature many pixels long. That limit is a property of the deviation budget itself
and applies equally at 50°; it is recorded here because these frames are where it was first
seen. The close-range control also shows what lod1 costs when it is used too near — visible
flat-facet tonal banding across the cylinder — which is precisely why lod1 starts at 3,997 m.

Frames: `docs/lod-4r-ext-6400-lod0-before.png`, `docs/lod-4r-ext-6400-lod1-after.png`,
`docs/lod-4r-truss-2x.png`.

**THE SCREENSHOT LENSES ARE A SEPARATE JUDGEMENT, AND THAT IS SAID HERE RATHER THAN LEFT FOR A
JUDGE'S FRAME.** This project renders through three lenses: the player's **70°**, the committed
shot's `export_scene.SHOT_FOV_DEG` = **46°**, and **24°** for AAA-STANDARD's half-distance craft
frame (INV-588). A chain calibrated for 70° shows `1.5 × 70/24 = 4.4 px` of deviation through a
24° lens and `1.5 × 70/46 = 2.3 px` through 46°. That is inherent to a **static offline chain
plus a zoom lens** and is not a defect in the calibration. The resolution is a decision, taken
here: **the GAME camera is the authority**, because it is the only lens a player ever looks
through, and a judge's telephoto frame is scored as composition rather than as an LOD acceptance
test — which is why the craft frames force `--lod lod0` and bypass the chain entirely. The
alternative — calibrating for the narrowest lens any tool can ask for — is what was happening
by accident at 50°, and it costs triangles in the shipped build to make a screenshot tool happy.

**What would overturn it.** A change to `_cam.fov` in `player.gd` (the chain follows it
automatically and `_selftest` fails if the read stops landing on that file); a runtime that
gives the player a settable FOV, in which case the chain must be calibrated at the *widest*
value the slider allows, not the default; or per-section hull LOD, which would make the whole
"one level over 8 km of depth" model obsolete — see `lod.py`'s own far-end note.

---

## INV-601 — one read of `player.gd` reaches three chains, and the fourth is still a copy

**What.** `station/drum_ground.py`'s screen model becomes a **reference** rather than a
restatement:

```python
import lod as _hull_lod
FOV_DEG    = _hull_lod.FOV_DEG
SCREEN_H   = _hull_lod.SCREEN_H
PIXEL_BUDGET = _hull_lod.PIXEL_BUDGET
```

`station/drum_dressing.py` already did `FOV_DEG = dg.FOV_DEG`, so one read of `player.gd` now
reaches the hull chain, the drum-ground chain and the drum-dressing chain.

**Why, and it is hard rule 4 applied to a constant.** `lod.py`'s own comment on `PIXEL_BUDGET`
says, in as many words, *"drum_ground.py mirrors the value and says so, so changing it here
silently would desynchronise two chains"* — and INV-600 is precisely that change. Doing it from
the drum end instead would be the same defect from the other side. A comment is not a
constraint; an import is.

**THE FOURTH MIRROR IS `station/npc/body.py` AND IT IS NOT FIXED HERE.** `body.py:200` restates
`FOV_DEG = 50.0` for the NPC LOD chain and `body.py:5240` **asserts** that it equals
`lod.FOV_DEG`. That assertion is correct, its stated reason is correct — *"two chains with two
budgets pop differently in one frame"* — and **it now fails**, together with the
`honest_from_m(0.37)` agreement check one line below it (`380.86 m` against `253.64 m`). This
was not in the brief's list of three things that would break, which enumerated `drum_ground`,
`drum_dressing` and `drum_walk`: **a fourth mirror existed and it is the only one that asserts.**
The one-line fix (`FOV_DEG = _hull_lod.FOV_DEG`) and the reason the NPC chain wants 70° for the
same reason the hull chain does are in `scratchpad/PATCHES-4r-lodfov.md`; that file is owned by
another agent this session and is not touched here.

**Overturned by** a decision that the NPC chain should be calibrated separately from the hull
chain — in which case `body.py:5240`'s assertion is the thing to delete, deliberately and with
a reason, rather than the value to bend.

---

## INV-571 — `garden_bark` stays at 0.135, and the tree is a silhouette because of shadow

**What.** A negative result: `materials.garden_bark`'s albedo (0.148, 0.135, 0.121),
luminance 0.137, is **not changed**, and `garden_bark` is **not** given a trim sheet. The
entry's overturning condition is tightened to say *reference* frame, and the measurement
below is recorded in `materials.NEGATIVE_RESULTS`.

**Why it was opened.** `docs/aaa-scorecard.json` and `STATE.md` carry a finding that the
trunk's fluted section "CANNOT BE SEEN at value 0.135", citing
`docs/garden-4q-after-tree.png` at `crushed 25.49%` — the worst frame in the drum set — and
saying the entry's own overturning condition ("any near-field frame of a tree in the drum")
was now met.

**What constrained it — four renders at one camera** (`garden.HERO_SHOTS["tree"]`, eye 9 m
from a level −1 broadleaf, Vulkan 1.4.318 Forward+ confirmed in every log). The committed
frame was re-rendered at HEAD first and agreed (crushed 25.49% → 25.56%), so none of this
is the stale-frame defect of session 3z.

| trunk box (0.485,0.80)–(0.515,0.99) | linear Y | crushed, trunk | crushed, whole frame |
|---|---|---|---|
| shipped, albedo lum 0.137 | 0.00526 | 95.3% | 25.56% |
| albedo lum 0.900 — a ceiling control, not a proposal | 0.30486 | 0.0% | **21.95%** |
| shipped albedo + a full `stone_agg` trim sheet at 0.35 m | 0.00494 | 95.3% | 25.56% |
| shipped material, shadow casters 24 → 0 | **0.02277** | **0.0%** | — |
| the ground it stands on, shipped | 0.23109 | 0.0% | — |

Frames, in that order: `docs/mat-4r-tree-shipped.png`,
`docs/mat-4r-tree-albedo090-control.png`, `docs/mat-4r-tree-trimsheet-probe.png`,
`docs/mat-4r-tree-noshadow-control.png`. `scratchpad/mat4r/crushmap.py` draws the crushed
population back onto the frame in magenta, which is how the split below was found rather than
argued: the trunk, the canopy, the branches and one shadowed town block, in that order of
area.

**Three things fall out and each kills a candidate explanation.**

*The crushed figure is 86% about something else.* Painting the bark a white no reference
could buy moves the whole frame's crushed fraction by **3.61 points of 25.56**. The bark and
its branches own 3.61; the canopy and the shadowed town block own the rest. A statistic
taken over 518,400 pixels was attributed to one 1,244-triangle object inside it.

*Relief is not the lever either.* A complete trim sheet — albedo variation, normal, ORM and
AO — moves the trunk by **×0.94**, and leaves it 95.3% crushed. A normal map modulates a
quantity that is already ~0. This is why no `bark_flute` sheet was authored: the experiment
that would have justified one was run first, for the price of one render, and came back
negative. (`garden_bark` was also temporarily lifted out of
`UNTEXTURED_BY_DESIGN["foliage"]` for that probe, and the observation that put it there —
"a leaf is not a trim sheet" — is about **leaves** and does not describe bark. It is left in
the list anyway, now for a measured reason instead of an inherited one.)

*Shadow is the lever.* Turning the drum's 24 shadow casters off, one variable, same camera,
takes the trunk from 95.3% crushed to **0.0%** and lifts it **×4.33**, against ×1.50 on the
ground in the same pair — so **×2.9 is shadow on the trunk specifically**. The tree stands in
its own canopy's shade under overhead light, which is what a tree does. The arithmetic
agrees from the other side: summing Godot's own `pow(1 - d/range, attenuation)` over all 60
drum sources (`scratchpad/mat4r/irradiance.py`), direct irradiance on a vertical trunk face
is **80.8** against **102.2** on the ground beside it — ×1.26, nothing like the ×44 the
render shows, so the missing factor is occlusion and not incidence.

**And the premise that opened this was false.** "Any near-field frame of a tree in the drum"
meant, in an entry whose source field opens *"NO FRAME MEASURES THIS"*, an authority-1 or -2
frame from the show. `docs/garden-4q-after-tree.png` is our own render: an albedo cannot be
measured off a picture drawn with that albedo. The wording is tightened so the next reader
cannot make the same reading.

**What would overturn THIS.** A reference frame in which a drum trunk is separable from what
is behind it — which would settle the albedo directly and make all of the above irrelevant.
Or a drum fill light: everything here is measured against the lighting rig as session 4r
shipped it, and a fill on vertical surfaces under canopy moves every number in the table.
The patch for that is in `scratchpad/PATCHES-4r-materials.md`; it belongs to
`tools/export_scene.py` and was not applied here.

---

## INV-572 — the drum's arable floor is textured at 256 texels/m, because a player now stands on it

**What.** `materials.TEX_SIZE["soil_clod"]` 1024 → **2048**, and the `ground_arable` binding's
tile 12.00 m → **8.00 m**. Together: **85.3 → 256 texels per world metre** on the five
`ground_arable*` materials, and 128 → 256 on `ground_shore`, which shares the sheet.

**Why the old number was right when it was written and is not now.** Its own comment said
*"the drum's arable floor, seen from far away"*, and session 4q measured exactly that: the
nearest thing standing anywhere on the drum was **44.3 m** from the eye. `drum_dressing`'s
near rung (INV-490..493) now places one item of cover per 3.90 × 4.04 m ground cell inside
90 m, and reports a **median nearest object of 2.32 m**. The read distance moved by a factor
of 19 and the sheet did not follow it. At 85.3 texels/m `ground_arable` was **tied with
`hull_exterior` for the lowest texel density in the library** — the same sheet density as an
8 km hull seen from 20 km, on ground a player kneels on.

**What constrained the new number — it is solved, not rounded up.** INV-491 already fixes
the read distance without taste: at the player's own **70°** vertical fov (`player.gd`, and
it is the strictest of the three fovs in this project) from a 1.7 m eye, **half** the
below-horizon frame is ground closer than **5.39 m**. Slant range there is
hypot(1.7, 5.39) = 5.65 m; 1440 rows over 70° is 1178.7 px/rad; so one across-track metre of
ground subtends **208.6 px**. One texel per pixel at the median therefore wants **≥ 209
texels/m**. 2048 over an 8 m tile gives 256, clearing it by 1.23×; 2048 over the old 12 m
tile gives 171 and would not.

**And 8.00 m is not a new number in the file** — it is the tile `ground_shore`, the band
next to it, has always used for the same sheet. It carries a second consequence that is
wanted rather than tolerated: `gen_soil_sheet` lays about ten furrows across a repeat, so
12 m spaced crop rows 1.2 m apart and 8 m spaces them **0.8 m**, inside the 0.15–0.75 m a
real row occupies instead of just outside it. The cost is repetition — a 90 m field shows 11
periods where it showed 7.5 — bounded by the parcel breaks `drum_ground` already cuts and by
the near cover standing on top.

**Measured, at the near field's own HALF distance** (eye 262.197,95.432,4700 → target
263.802,96.016,4704, the camera `scratchpad/NEAR-FIELD-4r.md` records; Vulkan 1.4.318
Forward+ on all three):

| | texels/m | vs A |
|---|---|---|
| A `1024 @ 12 m` (shipped) | 85.3 | — |
| B0 `1024 @ 8 m` | 128 | 56.45% of pixels differ |
| B `2048 @ 8 m` (this change) | 256 | 56.44% |
| B0 → B, i.e. **sheet size alone** | | **51.95% differ, max channel 23** |

A and B are committed as `docs/mat-4r-arable-85tex-before.png` and
`docs/mat-4r-arable-256tex-after.png`. B0 is the accidental stale-cache render described at
the end of this entry and lives in `scratchpad/mat4r/`.

At 2× magnification of the near ground the difference is what the numbers predict: A's stones
are large smeared blobs and its furrows are soft; B's stones are smaller, more numerous and
resolved, and the furrow grain is legible. Crops in `scratchpad/mat4r/crop-{A,B0,B}.png`.

**Cost.** Resident texture memory 97.3 → **105.3 MB**, 3.17% → 3.43% of the 3,072 MB budget;
`soil_clod`'s own set 2.67 → 10.67 MB. Export time for the whole texture set is 2m24s.

**Overturned by** `drum_dressing` withdrawing the near rung (which would restore the 44.3 m
read distance and with it the 1024), or by a repetition finding on a wide drum frame — the 8 m
tile is the half of this change that can be argued with, and reverting it alone leaves 171
texels/m, which is 0.82× the derivation rather than 1.23×.

**A HAZARD FOUND WHILE MEASURING THIS, AND IT IS NOT IN A MATERIAL.** The B render was taken
twice. The first one used the **new 8 m tile with the OLD 1024 texture**, because
`godot/.godot/imported/*.s3tc.ctex` still held the previous import: `render_godot.sh` warms
the import cache only when `.godot/imported` is **absent**, and a game-mode Godot does not
rescan the filesystem, so a regenerated texture renders through its previous import
**silently, exit 0, with a plausible PNG**. Caught only by reading the `.ctex` file sizes
(699,116 bytes — a 1024 BC1 with mips — against 2,796,268 after a forced
`godot --path … --import`). This is the same shape as the stale-frame defect of 3z and the
OpenGL-fallback defect of 4e, one level further down: **the frame was fresh, the renderer was
right, and the texture was last session's.** The accidental render is kept above as B0
because it is a real third rung of the ladder. A patch for `render_godot.sh` is in
`scratchpad/PATCHES-4r-materials.md`.

---

# INV-650..659 — THE CLOSURE VOCABULARY (session 4r, main agent)

## INV-650 — Twelve distinct reasons a section of Grey is welded shut

**What.** `station/closures.WELDED_DOORS`: twelve stencils for PLC-092's twelve welded doors,
tagged `G-04` … `G-36`, each naming a different KIND of reason — not funded, settlement crack,
solvent release, pressure boundary unproven, no deck plate, no services run, fire, fatal accident,
reassigned to tankage, route superseded, stripped for salvage, survey overdue.

**Why.** PLC-092's program is *"the honest face of Shell C … every closure REASONED and visible"*
and its CHECK is *"all 12 stencils read distinct real reasons"*. Twelve rewordings of "no money"
would satisfy a distinctness test on the strings and fail what the row means, so `_selftest`
asserts the TEXTS, the TAGS and the REASONS are each twelve-distinct, separately.

**Constrained by.** The era and the fiction the annex already fixes: Contract 5 is the
construction contract, the station opened incomplete and under-funded, EarthGov Facilities and the
Station Engineer are the naming authorities the register already uses, and the dates sit in
2256–2258, before the Season 2–3 era lock. Each is written in ENGINEERING terms rather than
dramatic ones — a stencil that told a story would be one somebody wrote; these are the ones a
contractor leaves. Length is capped at 62 characters, which is what the plate holds.

**Overturned by.** Any frame or script showing the text of a sealed door aboard Babylon 5. None is
known — `docs/spec/PLACES.md` §SHC quotes the eleven *closure* stencils and assigns these twelve to
the place rather than quoting them.

**Authority 5.** Argument at `station/closures.py`.

## INV-651 — A welded door answers instead of opening

**What.** `interact._REFUSES_TO_OPEN` maps `welded_door` to the verb `read`, and
`interact.read_text` serves the closure's reason.

**Why.** `welded_door` is `rooms.PROP_KIND` "leaf", and every leaf gets `open` — so the station's
twelve sealed doors offered to part and let you through. PLC-092 says the opposite in as many
words: *"T2-refused: LOOK/USE answer with the closure's stencil text"*.

**Constrained by.** Named as an exception rather than given a new `PROP_KIND`, because its SHAPE
genuinely is a leaf — a door-sized plate in a doorway — and lying about that would move the error
into the geometry. `interact.verb_set()` still reaches all eight verbs, and the selftest's
totality, minimality and negative controls all hold.

**Overturned by.** Any reading in which a welded section is meant to be openable at all; the
annex's "T2-refused" makes that unlikely.

**Authority 5.** Argument at `station/interact.py::_REFUSES_TO_OPEN`.

**INV-652 … INV-659** — reserved to session 4r's closure work and not used. Free.

## INV-610 — The streaming cell grid gains an axial dimension, one arc-cell long

**What.** `godot/scripts/stream.gd::bake()` cuts a deck into cells of `cell_deg` of arc **by
`cell_length_m` of axis** instead of arc alone. On Blue ring 1 deck 0 that is 20.0° × 73.8 m.
`--z-band=0` reproduces the old one-dimensional grid exactly and is the control.

**Why.** `interior.ring_cells` describes a deck as N angular wedges and records its axial extent as
a single `z0`/`z1` pair — for `blue.ring_1.d0`, 18 cells and z 6794→8047. `_split` binned every
triangle by `atan2(y, x)` and nothing else, so **a cell was a wedge running the deck's whole
1,253 m**. Baked from the whole-deck build, `blue_0_0` came back as 18 cells each spanning
z 6896.85–8005.41, the largest carrying **582,792 triangles — 3.24× the entire 180,000 resident
allowance, in one cell**. And the only route between the deck's six z-clusters, the axial spine at
89°, lies inside one of those wedges: a body walking the 340 m from the docking bays at z 7121 to
customs at z 7460 never crossed a cell boundary, so `loads=0 frees=0` over the whole traverse. The
cluster-to-cluster hand-off `docs/MASTER-PLAN.md` P0.5 called *"untested"* was not untested, it was
**unreachable** — there was no boundary in the direction the station is long.

**Constrained by.** The band length is `cell_length_m` and not a chosen number.
`stream.gd`'s free-radius derivation reads *"the largest deadband that cannot admit a fourth cell,
since a cell two away is never nearer than one cell length"* — a statement about the spacing of
neighbours, true around the arc because arc neighbours are `cell_length_m` apart. Setting the axial
band to exactly `cell_length_m` keeps ONE free radius valid along both axes with the same 7.7 m of
hysteresis (73.8 − 66.1), and makes a cell square on the floor a player walks. Any other band
length needs a second free radius and a second derivation. Bands are anchored at the deck table's
own `z0`, so a band index is a property of the deck rather than of what a particular build happened
to cover — the same rule as the arc grid being measured from 0°.

Measured, whole-deck `blue_0_0`, before → after: 18 → **87 cells** (18 arc × 16 band); longest cell
1,108.6 m → **73.8 m** of z; biggest cell 582,792 → **227,247 tri** (3.24× → 1.26× the resident
budget); triangles conserved exactly both ways (3,702,966 = 3,702,966).

**Overturned by.** A deck where `cell_length_m ≤ sight_line_m` — the deadband would then admit a
further cell along both axes and the free radius would need splitting. Also by any decision to make
axial residency an occlusion question rather than a budget one; see INV-611.

**Authority 5.** Argument and measurement at `godot/scripts/stream.gd`, header §"THE CELL GRID HAD
NO AXIAL DIMENSION". Gated by `station/boot.py --gate` ("no cell runs the deck's whole axial
extent", control at `--z-band=0`) and by `res://scenes/stream_gate.tscn --axial-gate`.

## INV-611 — Along the axis, the residency radius is a BUDGET bound and not an occlusion one

**What.** The residency radius stays `sight_line_m` (66.1 m on this deck) in both directions, and
the manifest now says in as many words that the axial half of it is not justified by the derivation
the arc half is.

**Why.** `interior.sight_line(r_floor, w) = 2·√(r_o² − r_i²)` is the chord past which **the ring's
own curvature** occludes: inside it the player can see the geometry, outside it the corridor wall is
in the way and nothing can pop. An axial corridor is **straight**. It has no curvature and therefore
no such horizon, so a cell arriving 66.1 m ahead down the spine is in principle visible arriving.
Using one radius for both is a budget decision wearing the arc derivation's clothes, and saying so
is cheaper than a future session re-deriving it and finding nothing underneath.

**Constrained by.** 180,000 resident triangles against a 60,000-triangle cell is three cells; three
cells of 73.8 m is 221 m of corridor, which is what the budget will buy along a straight run. The
three ways out are a bigger budget, an axial LOD chain, or a door — none is decided here.

**Overturned by.** A measurement of what a player can actually see down the spine (its 2.16 m width
and any bulkheads in it may occlude far more than assumed), or a triangle budget that makes the
question moot.

**Authority 5.** Argument at `godot/scripts/stream.gd`, header, and in the manifest's
`residency`/`z_band_from` strings.

## INV-612 — A cell's spawn is measured off that cell's own floor

**What.** `stream.gd::_cell_spawn` picks the collision triangle of *this cell* nearest the cell's
own centre at the deck's floor radius, and puts the spawn 0.2 m inward of it. A cell with no floor
carries no spawn and says so, instead of being given a point.

**Why.** The spawn was `_floor_point(corr, arc_centre, 0.2)` — the deck-wide corridor scan's
`z_mid` for every cell. On a single-cluster build that is right. On the whole-deck build of
`blue_0_0` the scan returned min-to-max across five separate ring corridors, `z_mid = 7562.75`, and
**all eighteen spawns were written at that one z** — where the only floor is the 2.16 m-wide spine,
so seventeen of eighteen were in mid-air 440 m from a corridor. This is `boot.py::spawn_from_shell`'s
own rule one level down: *"a point ON a triangle of the floor cannot be in the air"*, learned there
when averaging an arc's vertices put a spawn 214 m from any floor.

**Constrained by.** The deck's floor radius, not the cell's own maximum, so a mezzanine or a duct
run is not mistaken for ground; where a cell reaches no floor at that radius it falls back to its
own outermost collision triangle and records which of the two it used. 0.2 m of clearance matches
the existing spawn convention.

**Measured.** Whole-deck `blue_0_0`: distinct spawn z, 1 → **27** across 87 cells.

**Overturned by.** A deck whose walkable surface is not its outermost radius — the habitat drum,
which `drum_walk.py` handles with its own heightfield and which this bake does not cut.

**Authority 5.** `godot/scripts/stream.gd::_cell_spawn`.

## INV-613 — A ring corridor is a contiguous run of floor, and a deck has several

**What.** `stream.gd::_corridor_z` groups its qualifying z buckets into contiguous runs by merging
the floor triangles' **own z intervals**, reports every run, and returns the busiest by arc coverage
(ties broken on triangle count).

**Why.** It returned the min and max of every qualifying bucket, which assumes a build holds one
corridor. `tools/bake_station.py` bakes whole decks; `blue_0_0` holds ring corridors at z 6900
(164° of arc), 7120 (345°), 7460 (206°), 7960 (225°) and 8000 (360°). Min-to-max across those is
z [7121, 8004.5] and a mid of 7562.75 — 440 m of vacuum, and the value every cell spawn was placed
at (INV-612).

**Constrained by.** Contiguity is the triangles' own extents merged at 0.05 m, not adjacency of
0.5 m centroid buckets — the first version of the fix used buckets and split *this* deck's single
corridor in two, because its floor is a few large triangles spanning z 7185.7–7188.3 whose centroids
land in the 7186.0 and 7187.0 buckets with nothing in 7186.5. Merging intervals needs no tolerance
to argue about.

**Overturned by.** A deck whose corridor floor is not at the outermost radius.

**Authority 5.** `godot/scripts/stream.gd::_corridor_z`.

## INV-614 — The axial spine is `_corridor_z` transposed, and it is what joins one z-cluster to the next

**What.** `stream.gd::_axial_runs` asks which **angle** carries the most z, where `_corridor_z` asks
which z carries the most arc. On the whole-deck `blue_0_0` collision shell exactly one one-degree
bin of 360 carries floor spanning more than 300 m, and it carries **1,101.9 m of it in a single
unbroken run** — an axial corridor at ≈89.2°, 2.16 m wide, from z 6903.6 to z 8005.4, threading
every ring corridor on the deck.

**Why.** Nothing in the project could name the thing a player has to walk along to leave their own
z-cluster, so nothing could test it. The spine is what `--axial-gate` walks and it is read out of
the manifest rather than written down anywhere.

**Constrained by.** The span and run count come from **all** the floor in the winning bin, because
cutting the ring corridors out first splits the spine at each one it threads and reports something
continuous as three runs. The **angle** comes from the same bin with the corridors' z cut out, taken
as the MEDIAN — decided by mass, and a thousand metres of spine outvotes a room's few triangles —
then the extent of everything within one corridor width of it. The window is
`floor_r − √(floor_r² − sight²/4)` = 2.598 m, a number the manifest already derives. Taking the
BIN centre instead gave 89.5° for a spine whose own edge is at 89.46°, and the gate then walked
0.15 m outside its floor and stalled against the wall after 0.7 m.

**Overturned by.** A deck with several axial routes — this reports the longest and would need to
return a list.

**Authority 5.** `godot/scripts/stream.gd::_axial_runs`, cross-checked against an independent
Python glTF reader over the same shell (1,101.9 m, one run, both).

## INV-615 — A fresh cell set beats a nearer stale one

**What.** `station/boot.py::cells_for` evaluates every candidate cell set, prefers one that still
sums to the deck on disk, and records what it looked at in `cells_considered`. Location still breaks
ties among equals.

**Why.** It returned the first candidate that matched the deck by NAME, so a set sitting beside the
deck won however old it was. Measured on this tree: `scene/deck/cells_blue_0_0/` held 18 cells
summing to 735,732 render and 5,270 collision triangles while the deck beside it had 1,263,904 and
15,166 — a set cut from a build two thirds smaller, **covering 12.2 m of a 143 m deck** — and
`build()` named it as `cells_path` regardless, printing STALE as it did so. The shipped scene
streamed a third of its own floor.

**Constrained by.** Freshness has no tolerance to pick: `bake()` assigns whole triangles and asserts
the cells sum to the source exactly, so any difference at all means a different build. The location
ordering is kept for ties for the reason `_cell_candidates` gives — a sibling bake of the same NAME
is a different build of the deck.

**Overturned by.** Nothing yet; a deck with no fresh set anywhere still boots the least-stale one
rather than falling back to the monolith, which is a decision this entry does not settle.

**Authority 5.** `station/boot.py::cells_for`, gated by `--gate` ("a FRESH cell set beats a nearer
stale one").

**INV-616 … INV-619** — allocated to this work and not used. Free.

## INV-620 — C&C has side walls, and enclosure is a property no closure test in this project measures

**What.** `station/command_control.py::side_wall` builds a plated wall at each side of C&C, from
the pit slab's underside to the top of the cornice over the room's whole 12.6 m length, carrying a
panel grid on the deck's own joint pitch and a pilaster under each of `ceiling`'s beams. It
subsumes the two 1.9 m plates that used to wall the pit alone.

**Why.** The room did not have side walls. What stood at x = ±7.00 m was four light-course
housings, a dado, a skirting and a cornice — **trim for a wall that was never built**. Measured by
projecting the room along its own x axis and counting the cells of its cross-section that no
triangle covers: **3,261 of 10,020, i.e. 32.6 m² of 100.2 m² (32.5%) open, each side**. In the
engine at the room's own normal viewing distance, **18.4% of the frame hit no room geometry at
all** — with `station/vista.py` mounted those pixels are the starfield, and without it they are the
background colour, which is black. `docs/AAA-STANDARD.md` C2 names the case verbatim: *"a correct
skeleton with a missing layer: the corridor after session 2l had ribs and a deck and no walls, so
it read as scaffolding of exactly the right size."*

**Constrained by.** Thickness is `cc_pit_face`'s own 0.16 m, because that was the room's only
lateral plate and one number is better than two that must agree. The 4 mm standoff from x = ±hw is
this file's existing idiom (`wall_course`'s end caps, `annunciator`'s cheeks): a plate flush with
the trim it meets shares a whole face with it, which the non-manifold gate reports and is right to.
The panel grid's z pitch is `DECK_BAY_M`, so the wall's joints land over the deck's; its y pitch is
the forward bulkhead's 1.62 m, so the two walls are one grid meeting at a corner. The pilasters
stand at `ceiling`'s own beam z values, so the beams land on something.

**AND THE REASON NO GATE COULD SEE IT.** Every closure test in this project measures a **surface**:
`interior_kit.boundary_edges` counts edges used once (**zero** on this room), `_inward_fraction` counts
facing, the box ledger counts signed volumes, `bespoke.SHELL_OPEN_EDGES["command_control"]` reads 0.
All four were clean and all four were right — every piece of the room is a closed solid.
**Enclosure is a property of the VOLUME, and a room built entirely of closed solids with nothing
between them is watertight and open to space.**

**Overturned by.** A reference frame showing C&C's side walls as something other than plated —
glazed, open to a gallery, or fenestrated. The reference crop shows panelling behind the light
courses and nothing beyond them, so the wall's *surface* is authority 5 while its *existence* is
not a judgement call.

**Authority 5.** `station/command_control.py::side_wall`, gated by `room_enclosure` /
`enclosure_gaps` in the same file, whose control rebuilds the pit-only version and reports
`3261 of 10020 cross-section cells show the background = 32.6 m2 of 100.2 m2`.

## INV-621 — The forward pit had no light, which is why the window read as a silhouette

**What.** `station/command_control.py::pit_soffit` hangs a tray of `light_wall_course` blades from
the last ceiling beam, over the forward pit. `PIT_SOFFIT_BLADES = PIT_CONSOLE_N // 2` — one blade
per pit console pair.

**Why.** Two measurements, and the second explains the first. Inside the window's own aperture the
dark 55% of pixels (mullions, band, hub) averaged linear Y **0.01256** against the bright 45% (the
glass, showing the station through it) at **0.11972** — **×0.105**. The show's frame has it the
other way up: `scratchpad/PATCHES-4r-windows.md` §7 measures pane/mullion at ×0.48 there against
×6.96 here. Ours was a bright hole with a black wheel over it, in the object the room is arranged
around. The cause is not the window: **every one of the room's seven fittings was aft of z = 5.04
m.** Four wall courses stop at `L * 0.42`, and the ceiling battens are `light_service_tube`, which
`export_scene.py`'s `emissive_only` set explicitly excludes from carrying a lamp. The forward pit —
one of the room's two occupied levels, the thing that makes it read as a bridge, and what the
reference frame leads with — was lit by **nothing**, and the window's frame is the surface between
it and the eye. After: **×0.341**, the frame 3.4× brighter and the ratio 3.3× nearer the show's.

**Constrained by.** The z is the last ceiling beam's own centre, so the tray hangs from structure
rather than at a liked height; that puts it 3.28 m from the window's centre, d/r = 0.31 at
`light_wall_course`'s measured 3.5 m range times this room's reach factor. The count is the layer-4
level gate: `fixture_lights` hangs one lamp per connected body, and at THREE blades
`tools/measure_frame.py --against` puts the room's median at ×1.87 of the show's against a ×1.40
±25% target — out of range. Two lands it at **×1.72**, inside, and nearer the target than the
×1.06 it sat at with the pit unlit. `light_wall_course` and not `cc_light_strip` because
`export_scene._selftest` asserts the latter comes in exactly four connected bodies and that
assertion is in a file this module does not own.

**Read `measurable %` beside that median**, which is this project's own warning about this tool:
the frame went 67.9% → 88.9% measurable, so the median moved partly because its population did.
Every distribution statistic improved at the same time — p99 ×0.69 → ×1.03, p5/p95 ×1.14 → ×0.94,
crushed 32.1% → 11.0% — which a merely hotter frame would not do.

**Overturned by.** A reference frame showing the pit lit from its own consoles alone, or showing a
fitting in a different place. ×0.341 is still short of the show's ×2.08 and closing that needs the
frame lit from further into the room than the ceiling allows.

**Authority 5.** `station/command_control.py::pit_soffit`, measured with
`tools/measure_frame.py --against` on `docs/engine-cnc.png` and with a percentile split inside the
aperture on `docs/craft-4r-cnc-r1-half.png` against `docs/craft-4r-cnc-r3-half.png`.

## INV-622 — A concentric window member laps its panes by their own chord sagitta

**What.** In `station/command_control.py::window`, every concentric frame member and the structural
band are built to `r * f − max(0.028, lap[f])`, where `lap` is the amount the course inside dips
below its own cut radius.

**Why.** A pane is a flat trapezoid inscribed in its arc, so its outer edge is a **chord** and dips
`rad × (1 − cos(π/n))` inside the radius it was cut at — 37 mm on the twelve-pane inner course,
15 mm on the twenty-four-pane one. A member built to the nominal radius misses the glass it holds,
and the miss is a hairline annular **slot straight through the only window in the room**, at
r/R = 0.40 and again at 0.62 and 0.80. Measured by projecting the room along +Z: **45 open cell
centres of 13,160**. Nothing else could see it, because every closure test in the file measures one
surface at a time and both surfaces are closed.

**Constrained by.** Only the OUTER boundary of a course needs the lap: a chord at the inner radius
dips *toward* the centre and so covers more, not less. The 0.028 m floor is the frame member's own
existing half-width, so a course fine enough to need less keeps what it had.

**NEGATIVE RESULT, kept.** The first hypothesis was a polygon-phase mismatch — a 40-gon band
against 24 chords — and re-cutting the band at `seg = 24` made it **worse, 45 → 55**, because a
coarser polygon dips further inside its own radius. The gap was construction, not tessellation.

**Overturned by.** Curved panes. If the glazing is ever lathed rather than plated, the lap is zero
and this becomes an overlap.

**Authority 5.** `station/command_control.py::window`, gated by `room_enclosure`'s forward face
with a control that rebuilds the nominal-radius members and reports the leak.

## INV-623 — Which registers a console carries is keyed to the desk, not to a modulus

**What.** `console_unit` picks each cell's lit register with `dressing._pick(live, seed, "cell", b,
c)` — `blake2b`, deterministic, keyed on the desk's own seed — instead of `live[(b + c) % 3]`.

**Why.** The modulus does not depend on the desk at all, so **all nine consoles carried the same
sixteen-cell board**, and nine identical boards on a 150° arc render as a red-and-white
checkerboard laid over the whole desk: `docs/craft-4r-cnc-r1-console-half.png` reads as a picnic
blanket at the rubric's half distance. `docs/AAA-STANDARD.md` C5's *"nothing in frame repeats in a
way the eye can index"* is the clause, with C3's *"the same light, repeated without regard to what
the part does"* one rung below it. Measured: **1 distinct board over nine desks → 9.**

**Constrained by.** `blake2b` and never `random` or `str.__hash__`, which is salted per process —
the project's own determinism rule, verified byte-identical across `PYTHONHASHSEED` 0, 1 and 12345.
The pit's single-register desks are left alone: the reference shows them red-lit.

**Overturned by.** A reading of the reference at magnification that shows a regular register
pattern across the desks.

**Authority 5.** `station/command_control.py::console_unit`, gated in the same file by "no two
consoles carry the same register pattern" with the modular rule as its control.

**INV-624 … INV-629** — allocated to this work and not used. Free.

## INV-630 — The council bench's perforation is unbuildable, so its pitch is set by the frame budget

**What.** `station/council_chamber.MESH_CELL_M = 0.030` — a square-hole web at 30 mm both ways over
the bench's lit panel, 398 vertical webs and 23 horizontal ones, 12,320 triangles.

**Why.** The reference's own pitch cannot be measured from the only frame that shows it. An FFT of
`reference/05-sector-green/council chambers.webp` rows 560–600 over the panel gives a clean peak at
**4.96–5.07 px** horizontally and **4.75–5.0 px** vertically — but folding the signal on that period
shows the profile repeating **five times inside it**, the signature of a pattern near 1 px beating
against the frame's 1 px sampling grid. The beat bounds the true period at **1.0–1.25 source px**,
and the panel is 176–184 px tall at source x 420–520 for 0.7214 m of built panel, i.e. **250 px/m**
— so the perforation is **4–5 mm**. At 12.0 m of bench that is 2,400 columns × 144 rows, roughly
145,000 triangles, for a feature subtending **0.84 px** at the 5.89 m a player stands at.

**Constrained by.** The room's share of the interior frame budget, which is
`budget.INTERIOR["visible_set_tris"]` 60,000 less the corridor behind a standing player
(`corridor_tris_per_m` 400 × the 66 m sight line `budget.py` cites from `populace.corridor_sight_m`)
= **33,600**. The grille costs 12 triangles a vertical web and 324 an arc-swept horizontal one, so
T(p) = 377/p; 30 mm spends 12,570 and leaves the whole chamber at 88% of its share. The web is
6.5 mm in a 30 mm cell — **39% covered**, against the 24 mm bar in a 42 mm pitch it replaces at 57%,
which is the difference between thin dark lines on a bright field and lit slots between dark bars.

**NEGATIVE RESULT, kept.** Tagging the web `council_mesh` so it emits like the sheet it is part of
is the physically right argument and it renders **worse**: at emission 2.0 on web and hole alike the
panel becomes one blown white band with no perforation at all. The contrast has to come from the web
being the bench's own casework.

**Overturned by.** A perforated-sheet colour sheet in `materials.COLOUR_SHEETS` bound to
`council_mesh` at ~0.005 m, which is the only route to `docs/AAA-STANDARD.md`'s tiling clause —
requested in `scratchpad/PATCHES-4r-council.md`. Or by a square-on production still of the bench.

**Authority 5.** `station/council_chamber.py::mesh_grille`, gated in the same file by "the sheet's
cell is square" (398 webs at 30.0 mm across against 23 at 30.1 mm up) and by the budget check.

## INV-631 — The bench's capping rail is riveted at 140 mm, and the reference gives only a bound

**What.** `BENCH_CAP_H_M 0.075`, `BENCH_CAP_D_M 0.055`, `BENCH_STUD_PITCH_M 0.14`,
`BENCH_STUD_R_M 0.011` — a chamfered bullnose along the bench's whole 12.0 m front edge carrying 86
studs.

**Why.** `canon`'s own reading of this frame (`00-INDEX.md`, quoted in `materials.py`) records "a
grey slab top with a chamfered edge", "a riveted bullnose capping rail" and "a recessed plinth", and
the 3× crop shows all three plainly. The bench had none of them: its top met its frame at a bare
arris, which is `docs/AAA-STANDARD.md` C3's "the tertiary tier is generic" with nothing in the tier.

**Constrained by.** The stud pitch is a **lower bound, not a measurement**. On the crop the studs
read at about 0.15 of the lit panel's height along the rail — 0.11 m — but the rail runs in the
strongly foreshortened direction and the panel height does not, so the true spacing is larger by
however much the foreshortening is, and one frame cannot say by how much. 0.14 m is taken.

**Overturned by.** Any square-on frame of the bench front, which would fix both the stud pitch and
the rail's depth in one reading.

**Authority 5.** `station/council_chamber.py::bench`, gated by "the bench has a capping rail proud
of its own face" — scoped to the bench's own triangles, because asked of the whole `council_frame`
group the same check read "reaches r 11.160" and was answering a question about the ceiling.

## INV-632 — The fan's blades are laid in two depth layers so they can overlap

**What.** `FIN_W_M 0.83` (1.25 × the 0.665 m rim pitch), `FIN_LAYER_GAP_M 0.30`, alternating
layers, plus deterministic per-blade jitter: `FIN_R1_JITTER 0.14`, `FIN_R0_JITTER 0.35`,
`FIN_TILT_JITTER 0.55`.

**Why.** `council chambers.webp` at 3× shows the fan as a **stack of plates fanned out over each
other**, each one's end face catching the light, at visibly different rakes and stopping at visibly
different radii. Blades that merely abut cannot do that, and blades that overlap in one plane are
two solids in one place — the defect this module opened session 4p by finding between the bench and
this same fan. Two layers 0.30 m apart give the overlap without the interpenetration.

**Constrained by.** In-layer neighbours are two angular pitches apart, so a blade 1.25 pitches wide
never touches its own layer: width/spacing is 0.55 at the hub and 0.62 at the rim. The layers' world
x ranges are −1.118…−0.882 and −0.818…−0.582, disjoint by 64 mm, and the medallion had to move to
−0.70 authoring depth to stay clear of the front layer.

**Overturned by.** A frame of this wall from off-axis, which would show whether the plates are
stacked in two planes or in a continuous spiral.

**Authority 5.** `station/council_chamber.py::fin_wall`, gated by "the fan's two depth layers are
disjoint" and by "the blades overlap in projection, which is why they need it".

## INV-633 — The medallion is an open wheel, and its outline is built at the ceiling's limit

**What.** `MEDALLION_SPOKES 36`, `MEDALLION_HUB_F 0.22`, `MEDALLION_RIM_W_M 0.075`,
`MEDALLION_OUTLINE_R 1.59`, and **no backing disc**.

**Why.** Built as a solid disc with spokes in relief, the medallion renders as an opaque plate 2.7 m
across, the brightest object in the frame at V 0.611 against the reference's V 0.455, hiding the fan
it stands in front of. The 4× crop shows the opposite: a small plain hub, a dense sunburst of thin
spokes out to a bright rim, and outside that a large thin outline circle you see the blades straight
through.

**Constrained by, and it does not fit.** The outline's radius is measured as a ratio: the bright rim
reads 66 px across (radius 33 px in the 1000×750 source) and a circle fitted through three points on
the faint outline arc — crop (700,25), (1085,300), (640,790) at 4× over box (0.15,0.0)–(0.50,0.28) —
has radius 386 crop px = 96.6 source px. That is **2.9 rim radii, ±10% on eyeballed points**, which
at `MEDALLION_R_M` 1.35 on a centre 4.60 m up is 1.8 m through a 7.00 m ceiling. It is built at the
ceiling's own limit, **1.59**, and the shortfall is recorded rather than rounded away.

**The same frame contradicts this module twice and the two are one contradiction:** the blades
converge on the medallion rather than on a hub at floor level, and a fan radiating *from* the
medallion is exactly the composition in which a 2.9× outline fits. Against it, `00-INDEX.md`'s
reading of this frame puts the medallion "above the fins".

**Overturned by.** A second frame of this wall, which the reference set does not hold.

**Authority 5.** `station/council_chamber.py::medallion`, gated by projected coverage of its own
disc — 32% for the wheel, with the backing plate it replaced measured at 100% as the control.

## INV-634 — A delegation chair's lattice rows are derived so its cells come out square

**What.** `CHAIR_LATTICE = 3` columns, counted off the 3× crop, and
`chair_lattice_down()` = round((back height)/(cell width)) = **7** rows, giving cells of
207 × 211 mm.

**Why.** One count was used for both axes of a back 0.62 m wide and 1.48 m tall, so "4 × 4" is cells
2.4 times taller than wide and at the rubric's half distance the reference's "open black lattice
back" reads as a set of shelves — `docs/craft-4r-council-before-half.png` is the frame. The
reference's cells are square.

**Constrained by.** The chair's own proportions, so moving the seat height or the back height cannot
silently un-square the cell.

**Overturned by.** A frame at magnification showing a different column count; the row count follows.

**Authority 5.** `station/council_chamber.py::chair_lattice_down`, gated by "the chair's lattice
cells are square, not shelves" with one-count-for-both-axes (207 × 493 mm, 2.4:1) as the control.

## INV-635 — The speaking-position fan covers the bench top, with blue only at the blade tips

**What.** `SPEAK_BLADES 21`, `SPEAK_SPREAD_DEG 82.0`, `SPEAK_REACH_M 3.6`, `SPEAK_RISE_M 0.004`,
`SPEAK_BLUE_FROM 0.55`, laid out in the unrolled (arc length, radial depth) plane of the top so an
inlay follows the bench's curve.

**Why.** `council chambers.webp` shows the fan covering most of the visible bench top — an apex at
the speaking position with white blades splaying over 160-odd degrees and bright blue slivers
between their **outer** halves, feathering into jagged blue tips. What was built was 13 lines 22 mm
wide over ±26°, invisible at the normal viewing distance. `materials.py` had already recorded the
gap in its own words: "council_chamber.py tags all thirteen quads council_speak_fan, so a material
cannot express both and the blue …".

**Constrained by.** The top is 0.95 m deep, so a blade near the inward normal runs off the back at
0.81 m while one at 82° runs 3.6 m along the arc — the reach is `depth / cos θ` capped at
`SPEAK_REACH_M`, which is what makes the fan long and flat the way the frame shows. Tips are ragged
by `_u`, never `random`.

**Overturned by.** A frame showing the fan from above, which would fix the spread and the blade
count directly instead of by proportion.

**Authority 5.** `station/council_chamber.py::bench`. The blue is on `signage_panel` until the
material requested in `scratchpad/PATCHES-4r-council.md` exists.

**INV-636 … INV-639** — allocated to this work and not used. Free.

---

## INV-640 — The bay's pendant flood is a spun dome, and its shade has an open crown

**Invented.** `LAMP_SEG = 8`, `LAMP_RISE_F = 0.72`, `LAMP_LENS_F = 0.78`,
`LAMP_LENS_RISE_F = 0.34`, `UPLIGHT_R_F = 0.42` in `station/docking_bay.py::floodlight` — the
proportions of the shade, its rolled rim, the convex lens under it and the aperture on its crown.
`LAMP_R_M = 0.75` and `LAMP_DROP_M = 2.6` are unchanged and remain INV-022's.

**Why.** What the module built was two axis-aligned boxes. At the rubric's HALF distance
(`docs/craft-4r-dockingbay-before-half.png`, 13.9 m — see the round-2 entry in
`scratchpad/craft-4r-docking_bay_interior.json` for the derivation) nine of them fill the top of
the frame as flat white rectangles clipped to 1.0 with a glow halo: the brightest objects in the
shot and `docs/AAA-STANDARD.md` C1 verbatim, "a box primitive standing in for a named object".

**Constrained by.** `reference/03-sector-blue/dock.webp` (authority 1) magnified 2.2× over its
overhead band. Every pendant in that frame is a bowl hanging mouth-down off a short stem, with a
bright arc on its rim and a compact bright source inside the mouth; four of the five visible read
that way and the fifth is the one throwing a shaft. Nothing there is a rectangle. The proportions
are read off that magnification and not measured — the domes are at unknown depth and the frame
contains nothing of known size at that height, which is INV-022's own limitation one object down.
The **crown aperture** is not in the frame and is argued rather than seen: the same frame shows
the truss overhead LIT, the only sources in it are these pendants, and an industrial high bay's
open crown is the standard device that does that. See INV-646 for the measurement that says the
crown is not, by itself, enough.

**Overturned by.** Any frame showing a bay pendant against something of known size, or against a
dock worker on a gantry beside it.

**Authority 5.** `station/docking_bay.py::floodlight`. Asserted: the lens is a revolved solid
(more than two distinct y, where a box has exactly two, with the box as a negative control that
fires), the crown sits above the lens, and the whole fitting hangs clear below the girder soffit.

---

## INV-641 — The bay's transverse girders are X-braced, not a single Warren run

**Invented.** The web pattern in `station/docking_bay.py::girder`: two crossing diagonals per
panel on opposite faces of the truss, a post at every panel point, and `GIRDER_SOFFIT_M = 0.26`, a
bottom flange standing proud of the web.

**Why.** The module's own docstring says "deep box girders spanning the width, carrying a lattice
gantry" and what was built under it was one alternating diagonal — a zig-zag, which is a truss
diagram rather than a truss.

**Constrained by.** `reference/03-sector-blue/dock.webp` (authority 1) at 2.2× over the overhead
band, saved as `scratchpad/db/ref-truss.png`. The deep girder crossing the top of that frame
carries two diagonals per panel that cross, with a post at each panel point, and the light behind
it comes through the triangles either side of each crossing. The same magnification shows the
girder's underside as two steps rather than one slab, which is the flange. `GIRDER_BAYS = 10` is
unchanged (INV-022). The two members of one X are on opposite faces because that is how an
X-braced panel is built, and because butting them into one plane would put four faces on every
edge round the crossing — this module's own non-manifold gate.

**Overturned by.** A frame of a bay girder square-on, which would give the panel count directly
instead of by reading a foreshortened span.

**Authority 5.** `station/docking_bay.py::girder`.

---

## INV-642 — The bay ceiling's stringers stand on the girder's own panel points

**Invented.** `CEIL_RIB_D_M = 0.55`, `CEIL_RIB_W_M = 0.46`, `CEIL_RIB_FLANGE_M = 0.86`, and that
the ribs run ALONG the bay at the girder's panel pitch (4.2 m).

**Why.** Both authority-1 frames say the ceiling is ribbed and the module's own docstring copies
one of them — "the ceiling is the ribbed inner wall of the rotating drum, curving"
(`reference/00-INDEX.md` on `Minbari Flyer 969 in docking bay 17.webp`, whose entire upper-left
quarter is that surface). What was built was the arc plus `rooms.articulate`'s wall grid, which
renders as a flat field of tiles and is the largest single surface in any frame taken looking up
in this room.

**Constrained by.** The DIRECTION is structure, not choice: the bay is cut into a hull spun about
the station's axis, the axis is the bay's local +Z, and the framing visible on the inside of a spun
shell between its ring frames is the longitudinal stringer run. The PITCH is not a new number —
`GIRDER_BAYS` cuts the 42 m span into ten web panels, and a transverse truss lands on the
longitudinal framing at its panel points, so a stringer at every panel point is where the two
systems actually meet and cannot drift when the truss is retuned. The section (0.55 m deep, 0.46 m
web, 0.86 m flange) is proportioned to read at the 27.8 m normal distance and is invented.

**Overturned by.** Any frame of a bay ceiling square-on, which would give the pitch against the
girders directly.

**Authority 5.** `station/docking_bay.py::ceiling_ribs`. Asserted: every stringer vertex lies
within a flange half-width of a girder panel point (a half-pitch is the negative control and
fires), and no stringer stands proud of the shell — which failed on the first build, because
`ceil_y` falls 0.32 m per metre near the springing and a rib seated on its centreline value stood
0.14 m THROUGH the ceiling at its outboard edge.

---

## INV-643 — The deck disc's device is an outline round three bars

**Invented.** `EMBLEM_W_F = 0.52`, `EMBLEM_H_F = 0.62`, `EMBLEM_STROKE_M = 0.42`, and that the
corners are cut at 45° rather than radiused.

**Why.** Not an invention at all in its main claim, and that is the point of the entry.
`reference/00-INDEX.md`'s second pass over `dock.webp` corrects its own first pass in one sentence
— "The disc's device is a **white rounded-rectangle outline containing three white bars**, not an
oval emblem" — and the geometry was still building the first reading, a filled circle 4.66 m
across inside a filled circle 10.6 m across. judge-4e's finding on this room says `bay_emblem`
"is not legible in frame"; a filled disc inside a filled disc has nothing to be legible with.

**Constrained by.** The device is read as occupying roughly the middle half of the 156 px disc,
so its width is 0.52 of `DECK_DISC_D_M` — which is itself the one measured length in this module
(170 px at 16.0 px/m off the dock workers, INV-022). The 0.62 aspect and the 0.42 m stroke are
proportioned off that and are the invention. The corners are cut rather than arced because at 0.42 m
of stroke an arc costs hundreds of triangles to say what four 45° pads say for 48.

**Overturned by.** One frame that resolves the device at more than about 20 px, which would give
the bar count and the aspect directly. `materials.py`'s own entry for `bay_deck_emblem` records
that at 4× the bars are "about 4 px tall" and not clear of the red around them.

**Authority 5.** `station/docking_bay.py::deck_device`. Asserted: the point midway between two of
the three bars carries no paint (the filled disc it replaced is the negative control and fires),
and the middle bar is present, so the first test cannot pass vacuously.

---

## INV-644 — The bay's signage pylon, and that signage on this deck comes in fours

**Invented.** `PYLON_H_M = 2.35`, `PYLON_W_M = 1.95`, `PYLON_D_M = 0.42`, `PYLON_PLAQUE_Y_M = 1.66`,
`PYLON_PITCH_M = 46.0`.

**Why.** `reference/00-INDEX.md`'s second pass over `dock.webp` (authority 1): "A **signage pylon**
stands at the deck edge carrying **four rectangular plaques in a horizontal row** at head height,
with a **green-lit display panel** on its lower flank. A dock worker beside it gives the height.
Signage on this deck comes in **fours**." None of it was built. The bay's whole deck carried twenty
bollards and nothing a person would read.

**Constrained by.** The height is the one number the frame gives and it gives it by comparison: a
dock worker stands beside the pylon, so its head is a little above `DOCK_WORKER_H_M = 1.75` — 2.35 m,
and the module asserts the pylon stays inside `1.0×` to `1.6×` a dock worker. The plaque row is at
1.66 m because "head height" is what the index says and that is standing eye height plus a little.
The plaque COUNT is sourced (four) and the along-bay pitch is invented. The pylon presents its
plaques ACROSS the lane, which is asserted with the wrong-way build as a control, because four
plaques facing a wall is four plaques nobody reads and no still can tell which way they point.

**Overturned by.** Any wider frame of the bay deck showing pylon spacing, or one that resolves the
plaques.

**Authority 5.** `station/docking_bay.py::signage_pylon`. The groups are `bay_panel`,
`prop_level_plaque` and `dress_screen` — all existing binds, because `export_scene.build()` raises
on an unbound group and a new material name would have taken every other agent's renders down.

---

## INV-645 — The ledge railing, at the lane edge the deck's own hazard band is painted on

**Invented.** `RAIL_H_M = 1.06`, `RAIL_POST_PITCH_M = 4.2`, `RAIL_R_M = 0.05`, and the kick plate.

**Why.** `reference/00-INDEX.md` on `Minbari Flyer 969 in docking bay 17.webp` (authority 1):
"service gantries with **railings**". The bay had none, and the fall it protects against is real
geometry in this module: the first ledge tread stands `LEDGE_RISE_M` = 2.2 m over the lane at
exactly the line `lane_edge` paints its hazard band on.

**Constrained by.** The height is a standing hand and the module asserts it lands between 0.95 and
1.20 m above the tread. The post pitch is the girder's panel pitch halved, for INV-642's reason —
a number the module already has rather than a new one. The rail is `bay_girder`, the bay's own
steel, because a new group name is a new material bind in a file this session does not own.

**Overturned by.** A frame showing a bay railing against a person, which would fix the height, or
one showing the ledges unrailed, which would delete it.

**Authority 5.** `station/docking_bay.py::ledge_railing`. Asserted: the railing's feet are on the
tread (y exactly `LEDGE_RISE_M`) and inboard of `clear_half_m()`, so it cannot drift off the ledge
it stands on.

---

## INV-646 — The bay's steel is erased by a cool fog, not by a lack of light — a NEGATIVE RESULT

**Invented.** Nothing. This entry exists because a measurement REFUTED the fix this session was
briefed to build, and the refutation is worth more than the fix would have been.

**Why.** `tools/export_scene.py`'s session-4m note says the bay reads wrong because
"`docking_bay.floodlight` hangs the lamps 2.6 m BELOW the girder soffit and aims them straight down
through a hood that is closed on top, so the red-oxide truss … is lit by nothing but the flat
ambient", and prescribes "an uplight component on the fitting, which is a new emitted group in
`docking_bay.py` and a new FIXTURE_LIGHTING row". Both halves were built and measured in a
`git worktree` — see `scratchpad/PATCHES-4r-dockingbay.md`.

**What was measured**, five frames, one camera, `--shot interior --room docking_bays` at 1280×720,
every run confirmed `Vulkan 1.4.318 - Forward+`; the statistic is the fraction of visible pixels
with R > 1.15 B, against `dock.webp` measured by the same code:

| | truss band R/B | truss/deck luminance | warm px |
|---|---|---|---|
| shipped (fog 0.014, no uplight) | 0.574 | 0.266 | **3.1%** |
| + uplight at 0.30 of the flood | 0.648 | 0.816 | **3.8%** |
| fog 0.005, no uplight | 0.787 | 0.177 | **18.8%** |
| fog 0.0025, no uplight | 0.834 | 0.168 | **28.7%** |
| fog off, no uplight | 0.849 | 0.167 | **32.0%** |
| fog off + uplight 0.30 | 0.886 | 0.601 | 34.5% |
| **`dock.webp`** | **1.157–3.191** | **0.120–0.262** | **39.5%** |

**The uplight buys 0.7 points of warm. Removing the fog buys 28.9.** And the uplight actively
costs: it takes truss/deck from 0.266, at the edge of the reference's own band, to 0.816 — three
times the reference's upper bound — because it lights the ceiling to the level of the deck, and
`dock.webp` is a bright deck under a dark warm roof.

**The mechanism.** `godot/scenes/interior.tscn` carries `volumetric_fog_density = 0.014` with
`volumetric_fog_albedo = Color(0.78, 0.81, 0.88)`, one global value for every interior. That is a
sane number for the 21.6 m corridor it was set on and it is 6.5× the path length in a 140 m bay:
over the 30 m slant to the truss the frame is a third fog, and the fog is blue. Adding light to a
blue medium adds blue in-scatter as fast as it adds warm surface, which is exactly what the second
row of that table is.

**Overturned by.** A per-room fog density — the fog is a property of the volume and the engine is
being told one number for a corridor, a chapel and a hangar. Until that exists this is not a
docking-bay defect, it is a scene defect measured in a docking bay.

**Authority 5** for the reading. The numbers are measurements.

**INV-647 … INV-649** — allocated to this work and not used. Free.

## INV-660 — "~1.5 species-normal intervals" is a multiplier, not an hour count

**What.** `condition.LATE_FACTOR = 1.5`. A person is HUNGRY once `hours_abs - last_meal`
exceeds 1.5 × that species' own mean meal interval, and TIRED once it exceeds 1.5 × a day.

**Why.** `docs/THE-STATION.md` PLY-06 states the threshold as *"no meal for ~1.5
species-normal intervals"* and *"no sleep for ~1.5 species-normal intervals"*. The tilde is
the spec's, so 1.5 is the value the sentence names and this file chooses nothing else.

**Constrained by.** It multiplies an interval `npc/schedule.py` derives, and never an hour
count. 1.5 human meal intervals is 12.0 h (three meals at 07:00/12:30/19:00, mean gap 8.00 h);
1.5 pak'ma'ra intervals is 18.0 h (two meals at 04:00 and 16:00, mean gap 12.0 h). A single
"twelve hours" written here would be right for a human and would starve a pak'ma'ra six hours
early — which is the specific thing PLY-06's own harness clause forbids: *"the species windows
come from `npc/schedule.py`, not from a constant in the condition model."*

A species with `meals: ()` — the Vorlon, whose row records *"nothing has ever shown a Vorlon
eat"* — has an interval of 0.0 and is never rated hungry at all, rather than being rated
hungry immediately. Asserted in `condition._selftest`.

**Overturned by.** Any reading in which the show puts a hunger consequence on a different
clock, or a SPEC-CHANGE to PLY-06's threshold sentence. Changing it moves both thresholds
together, which is correct: they are the same claim about the same tilde.

**Authority 5.**

## INV-661 — the rested pay bonus is 4%, and it is a separate line on the stub

**What.** `economy.RESTED_BONUS = 0.04`. A rested worker's shift adds a second, named
`(rested bonus)` row to the sales log rather than inflating the wage row.

**Why.** PLY-06 gives `rested` exactly one effect — *"work pay-stub bonus on the next shift
(stated in credits on the stub)"* — and gives `tired` exactly its forfeit. The spec states the
effect and not the size, so the size is chosen here, beside the wage table, because how much a
shift is worth is an economic fact rather than a physiological one.

**Constrained by.** Smallness is the constraint, and it comes from the row's own ruling.
PLY-06 is signed **LIGHT** and its effect table ends *"anything worse — nothing. No damage, no
death spiral, no HUD nag, no screen effect."* A bonus large enough to optimise around would
make sleep a resource, which is the failure the enumerated effect list exists to prevent: at
4%, a 50 CR shift pays 52 CR, which a player notices on the stub and does not plan a day
around. It is stated as a rate rather than a flat credit amount so it scales with the wage
bands in `PEOPLE.md` §3 instead of being worth more to a dockworker than to a captain.

**Why a separate line rather than a bigger number.** A forfeited bonus a player cannot see is a
rule that is not in the game. Both arms of `condition._selftest`'s pay check assert the line,
not just the total.

**Overturned by.** A canon pay stub. Nothing in the reference set shows one.

**Authority 5.**

## INV-662 — the compression step is one station-hour

**What.** `compress.STEP_H = 1.0`, and `interact.gd::_sleep` uses the same number.

**Why.** PLY-05 says a sleep advances the clock *"through the running simulation — events
still fire, stocks still move"*, which makes the step size a question about the world's own
tick rate rather than about smoothness. `incident.simulate` takes a window in minutes and
`economy.background_sales` moves a whole day at a time, so **one station-hour is the finest
grain at which either of this station's two world-tick systems has anything to say.**

**Constrained by.** Finer is waste: sixty `incident.simulate` calls to produce the same hour of
events, at sixty times the cost, for a resolution nobody can perceive across a sleep. Coarser
loses the thing the step exists for — PLY-05's own CHECK names *"a scripted 03:00 sweep event
wakes the player camping below"*, and a two-hour step lands on 02:00 and 04:00.

**And it is a resolution, not an event rate — a measured negative result.** The first control
written for `compress.py` asserted that a single-step advance would fire FEWER events than
eight hourly ones. It fired **110 against 95**, because `incident.simulate` honours whatever
window it is handed. Event count is therefore not a proxy for "the world ran". What the step
buys is *how finely the sleep can be stopped*: a one-step advance checks for a waker once, at
the end, so a 03:00 sweep can only wake you at 05:15, which is not being woken.

**Overturned by.** A world-tick system with something to say at a finer grain than an hour —
a per-minute PA schedule or a per-minute stock model would move this straight to 0.25 h.

**Authority 5.**

## INV-663 — which incident classes are loud enough to wake a sleeper

**What.** `compress.WAKING_CLASSES` = INC-SWEEP, INC-BREACH, INC-FIRE, INC-BRAWL, INC-ARREST,
INC-CONTRA. An incident wakes a sleeper when it is one of those **and** it happens in the place
they are sleeping.

**Why.** PLY-05 requires interruptions to be real and names a sweep reaching the player's camp
as its example. Every incident the station produces cannot be an interruption or a night in
Downbelow would be one long wake-up: `--sleep 22.0 --wake 5.25` fires 90 events in seven hours
in that one place alone.

**Constrained by.** Two filters, and the first is the load-bearing one. **PLACE** — a
fabrication fault four sectors away is the world running, not an interruption, and it is
checked before the class. **CLASS** — the six above are the ones that involve people arriving,
shouting, or opening a door, as against a queue forming or a stock delivery.

**What would be better, and why it is not done.** Derived from a severity field on
`incident.CLASSES` rather than listed here. That field does not exist, so a hand-list marked as
an extrapolation is the honest form; the alternative is inventing a severity ordering for all
30 classes as a side effect of building sleep.

**Overturned by.** A severity or loudness field on the incident classes, which should replace
this list entirely rather than validate it.

**Authority 5.**

## INV-690 — The ISN rotation: three phrasings per story, not one

**What.** `broadcast.ISN_ROTATION` gives each of the five era-locked ISN stories three
phrasings — the lead, the follow-up that adds the detail, and the official reaction — and
which one is on screen is the day number (`isn_bulletins(datum, rotation)`), threaded from
`day(day_n)`. `ISN_BULLETINS` is DERIVED from it so there is no second copy of a string.

**Why.** DLG-04's arithmetic is "ISN 5 bulletins × 3 rotation variants = 15". A concourse
screen is on for a whole watch and a player stands under it for minutes; one string per
story is the textual form of a tiling seam the eye can index.

**What constrained it.** FACTIONS.md 11.5's build note — the propaganda layer must read
"official and reasonable … do not make them look like villain posters" — and the customs
board's own register at authority 1 (`reference/01-station-exterior/welcome to babylon
5.webp`). The three variants therefore get drier and more official as they go, never
shriller. Era lock through `costume.ERA_EVENTS`, the same clock as the armband (INV-240).

**What would overturn it.** An authority-1 or -2 ISN screen readable in frame, or a
production script page giving ISN's actual bulletin cadence. Authority 5.

## INV-691 — Three call types per hull class

**What.** `broadcast.SHIP_CALLS` gives each of `traffic.MANIFEST`'s ten classes an
arrival, a departure and a boarding call, written in that class's own terms — a bay hull
names its tier, a standoff hull names the lighterage that has to go out to her, a warship
names her moorage. `CALL_TYPES` names the three. 10 × 3 = 30, DLG-04's PA figure.

**Why.** The module announced every hull with one arrival string and one departure string
with the class name substituted in. `traffic.arrivals` at the datum berths ~51 hulls a
station-day, so a player in the concourse heard two phrasings fifty-one times.

**What constrained it.** The class list is `traffic.MANIFEST`'s and `_selftest` asserts
every manifest class has all three (and that no two classes share a line), so a class added
to the manifest cannot leave a hole. "Achilles-type freighter" and "United Spaceways
transport" are authority 4 and unchanged; the rest are descriptive, as the register's other
alien and utility hulls already were.

**What would overturn it.** An authority-1 port announcement in frame. Authority 5.

## INV-692 — The denunciation scene as content

**What.** `broadcast.DENUNCIATION`, eight lines in scene order — approach, demand,
denouncer, accusation, defence, crowd, disposal, aftermath — each carrying the speaker who
says it, so a runtime can put the line in the right mouth rather than on the tannoy.
Era-locked to `nightwatch_visible`; `denunciation_scene()` returns nothing before it.

**Why.** DLG-04 asks for "the denunciation/questioning scene set 8" as content. FACTIONS.md
5 is that dissent is relabelled treason, and the show stages it in public corridors where
the crowd's job is to not be involved — which is why two of the eight are bystanders.

**What constrained it.** FACTIONS.md 5.1: *"Any armband before The Fall of Night is an
error."* The scene is the armband speaking and takes the same era gate.

**What would overturn it.** A transcript of an on-screen Nightwatch questioning. Authority 5.

## INV-693 — The era-rumour matrix: four speaker classes, not fifteen species

**What.** `broadcast.ERA_RUMOUR`, 8 `costume.ERA_EVENTS` × 4 speaker classes (official,
trader, downbelow, alien) = 32 lines, era-locked through the one clock.

**Why.** DLG-04's "8 ERA_EVENTS × 4 speaker classes = 32". What changes when the news is
the same and the mouth is different is not the species, it is what the speaker stands to
lose: the office that must administer it, the trade that must price it, the people below
who find out last and pay first, and the non-human resident for whom an Earth Alliance
emergency is somebody else's emergency happening to them.

**What constrained it.** Doing it per species would be a second application of
`dialogue._SPECIES_VOICE`, which already modulates register — two descriptions of one fact.

**What would overturn it.** Evidence that the show's aliens react to Earth politics along
species lines rather than interest lines. Authority 5.

## INV-694 — The player's 152 lines, and the 96 that are two lists multiplied

**What.** `dialogue.WORK_LINE` is `PLAYER_ROLES` (the annex's ROLE-01..12) × `SHIFT_VERBS`
(`interact.VERBS`, in order) = 96 lines, plus `PLAYER_OPEN`/`PLAYER_CLOSE` (8),
`PAPERS`/`BUY_SELL`/`PLAYER_REFUSAL` (15) and `SAY`'s 11 × 3 (33). 152, `player_lines()`
counts it.

**Why.** DLG-05's arithmetic, and every multiplicand is a list this repository already
holds rather than a figure chosen to make a total come out.

**What constrained it.** The player has ONE register — no role row, no species row —
because nothing in this repository describes how the player speaks and banding them would
invent a person the simulation does not have. `_selftest` asserts the verb tuple IS
`interact.VERBS` and the role count IS the annex's `### ROLE-` heading count, so a
thirteenth role or a ninth verb shows as a hole rather than as a silent gap.

**What would overturn it.** A design decision that the player has a species and a role.
Authority 5.

## INV-695 — Kosh's twelve, and silence when they are gone

**What.** `dialogue.KOSH_LINES`, twelve utterances, drawn as a session-keyed permutation
indexed by `World.turn`; turn 12 and after produce an ACTION ("the encounter suit does not
move") rather than a repeat.

**Why.** DLG-06 spec's a CEILING, not a floor: *"≤12 lines, each unique, never twice in one
session"*. A Vorlon with fifty lines is not a better Vorlon, he is a different character.

**What constrained it.** FACTIONS.md 12's *"almost never seen"*, and
`_ROLE_REGISTER["envoy"]`'s own note — two public hours a day, and almost nothing said in
them. Twelve is one utterance per hour of audience. `schedule.ROLE_WEIGHTS["vorlon"]` has
exactly one occupied cell, which is why the interception is on the ROLE (`envoy`) rather
than on an npc_id: the ceiling holds for the office.

**What would overturn it.** A count of Kosh's actual utterances per episode at the datum
that is materially different from one an hour of screen presence. Authority 5.

## INV-696 — The Broker is gated on the room, not the clock

**What.** `dialogue.BROKER_LINES`, twenty lines split ten with an audience and ten alone;
`broker_lines(alone)` selects, and `alone` comes from `World.audience`, which `sidecar()`
COUNTS off the baked actor list for that place.

**Why.** DLG-06: *"The Broker: audience-gated, ≤20."* The other shape of scarcity is not
silence, it is who is listening — and a broker who says the same thing in both rooms is not
a broker.

**What constrained it.** CAST-02 row 36's night broker works 18:30–02:30 because
`schedule.species_work_shift` does that to a Brakiri, whose day starts at 16:00. The
audience is derived from the crowd that is already placed rather than from a new parameter,
so it cannot disagree with the bodies in the room.

**What would overturn it.** A scene establishing that the show's fixers price by hour
rather than by audience. Authority 5.

## INV-697 — `SAY["refusal"]`: the eleventh player row

**What.** Three player lines for an exchange whose NPC has refused to speak, and a menu
built in `speak()`'s refusal branch: ask gets nothing back, press gets the band's own
`DEFLECT`, let-go ends it.

**Why.** `TOPICS` has eleven entries and `SAY` had ten, so DLG-05's 11 × 3 was 10 × 3 —
and the missing one was the single exchange in the module a player could not answer.

**What constrained it.** No new NPC content: `DEFLECT` already exists for a person who will
not give up a number, and FACTIONS.md 12's avoidance is allowed to stand when the player
lets it go. Authority 5 for the three phrasings.

**What would overturn it.** Nothing about the show; a design decision that a refusal should
end the exchange without a player turn. Authority 5.

## INV-698 — The tier-2 voice matrix is composed, and its distinctness is structural

**What.** `dialogue.ROLE_CLAUSE` (19 roles × 11 topics = 209 clauses, carrying the topic's
own braces) × `SPECIES_FRAME` (15 species × 2 frames) gives every occupied
(species × role) cell 22 topic lines; a species greeting stem plus a role tag gives 4
greetings and 4 farewells. 30 per cell, 79 cells, **2,370 distinct**. `MINBARI_CASTE` and
`CASTE_ADDRESS` carry the annex's caste-address requirement; pak'ma'ra speak through a
translator and Gaim through an interpreter in every frame.

**Why.** `_ROLE_REGISTER` and `_SPECIES_VOICE` MODULATE a shared phrasing — they choose one
of three bands — so 19 × 15 selects, it does not multiply. Every speaker aboard drew from
39 strings.

**What constrained it.** Distinctness is by construction, not by discipline: every line
contains a string only that role owns and a string only that species owns, so two cells
cannot collide — and the assertion over all 79 found two real collisions anyway (`other`
sharing `human`'s greeting stem; the envoy's `meal` and `worship` clauses being the same
string), which is why the check is an identity test and not an argument. Hand-writing 2,370
lines would be 2,370 strings nobody re-reads and a table that drifts.

**What would overturn it.** Attested species speech patterns that contradict a frame — a
Brakiri who does not reckon by a night clock, a pak'ma'ra who speaks without a translator.
Authority 5 for every phrasing; the register is the customs board's at authority 1.

## INV-699 — The CAST-02 fifty speak from the annex, 75 lines each, none shared

**What.** `dialogue.cast_roster()` PARSES the CAST-02 table in `docs/spec/PEOPLE.md` — name,
species, office, home, schedule anchor, links — and `cast_lines(row)` renders 75 lines for
that person: 33 topic (11 × 3 salience variants), 8 greetings (4 dayparts × 2 acquaintance
bands), 4 farewells, 12 biography/office/links, 9 player-memory, 9 work. 50 × 75 = **3,750
distinct strings, none appearing in two people's sets**. Wired ahead of the tier-2 matrix
in `phrase()`, with the greeting's acquaintance band derived from `World.turn`.

**Why.** DLG-01's rule is not the count, it is *"No string may appear in two NPCs' sets"* —
and with 69 shared templates it was violated by construction.

**What constrained it.** The roster is parsed rather than copied, because a copy of the
fifty would drift from the annex and no gate could see it. Uniqueness is carried by the two
columns that are 50/50 unique — `who` and `anchor`; `office` is only 49/50 (rows 11 and 12
are both "Ombudsman (retained canon office)"), which is exactly why 49 templates had to be
rewritten to name the person after the assertion found 231 collisions. The office column is
spoken as its head clause (`office`) because "publican, `bar_unnamed` — owner-operator
evenings" is correct in a table and unsayable in a bar; `office_full` is kept for the one
biography line entitled to the whole entry.

**What would overturn it.** A CAST-02 revision that gives two rows the same name, or a
ruling that the fifty should be authored by hand rather than generated from their own facts.
Authority 5 for the phrasings; every fact in them is the annex's.

## INV-700 — What is behind each of the thirty counters

**What.** `dialogue.COUNTER_WARES`, one row per `(place, serve token)` in the register,
each naming what it `sells` (GDS-01 names), what it is `short` of at the datum, and what it
will `never` stock. Six shapes over that row — pitch, price, provenance, shortage, refusal,
haggle — give 6 place-specific trade lines per counter, **180 distinct**, appended to the
exchange by `serve_response()`.

**Why.** DLG-03: *"a counter that trades in 'goods' fails the T1 specificity rule"*, and
*"the Quartermaster does not sell spices"* — both now assertions. `serve_response` returned
`speak()`, whose trade line came from a shared pool of three.

**What constrained it.** The ware names are `docs/spec/PLACES.md` §0.3's GDS-01 vocabulary
(spoo, brivari, flarn, G'Quan Eth, Jovian Sunspot, treel, jala, bagna cauda, salvage lots,
breather cartridges, identicard blanks, Dust, aid-ration packs, water containers, pitch-fee
scrip, Nightwatch pamphlets, drum staples, Vree optics, Drazi hardware grades, dock-grade
tools). `short` and `never` are what make a counter a place rather than an inventory: a
person who tells you what they have not got has told you where you are.

**NOTE — AN OPEN DRIFT, DELIBERATELY NOT CLOSED.** DLG-03 says "29 counters across 27
places", citing `interact.py:120–126`. The register today has **30 across 28**. Neither side
may be edited to make the other pass (MASTER-PLAN R1), so this table covers what the
register has, the harness reports both figures, and **DLG-03 remains RED on the drift alone**
— it carries no content complaint any more. The decision is the owner's: adopt a SPEC-CHANGE
moving 29→30 and 27→28 (which recomputes DLG-03's total 174→180 and the grand floor
6,544→6,550), or remove the counter that was added.

**What would overturn it.** A gazetteer entry naming a counter's actual stock. Authority 5.
---

## INV-731 — a walk arrives at a PLACE, and a place is a volume with a footprint

**What.** `stream.gd --axial-gate` chooses where to walk by reading a sidecar of the
register's places (`tools/bake_station.write_places`) rather than by picking a z coordinate,
and "arrived" means the body stood **inside the place's own footprint**: for
`obs_dome_2` that is `|z − 7960.0| ≤ 18.0` with the walk angle inside its 2.71° half-width.
The half-width is `degrees((across_m / 2) / floor_r_m)` — `directory._P`'s `foot` is
(across, along) and across is an **arc**.

**Why.** R5's acceptance is *"arrives at a place in the far cluster"*. Before this the gate
could report 774 m of floor and ten cell hand-offs without anyone being able to say the player
had got **anywhere**; a streamer that pages cells across empty spine is not a station you can
walk across. The distinction is the difference between a statement about a cache and a
statement about the station.

**Constrained by.** Nothing here is chosen. The floor radius comes from
`cell_manifest.json`'s `deck_table`, the angle, z and footprint from `directory.PLACES`, and
the cluster size from `deck.Z_CLUSTER_M`. The selection rule has three clauses, each of which
would exclude a place for a reason: its footprint must straddle the walk angle (the spine is
3.28 m wide and a place 40° round the ring is not somewhere this walk can arrive); its z must
lie inside the spine's own **measured** range; and the start is then the ring-corridor run
furthest from it, so the walk is the longest one this deck's spine supports.

**What it measured.** On `blue/0/0`, of sixteen register places, **exactly one** —
`obs_dome_2`, Observation Dome 2 — has a footprint straddling the measured spine at 89.183°.
`docking_bays` does not, and that is the correction worth recording: 360 m of arc reads as
"spans the ring" and is **±48.75°** at r = 211.55. So the walk R5 asks for begins on a stretch
of spine inside no named place and ends inside exactly one.

**What would overturn it.** A place whose geometry is built somewhere its register row does
not say, or a footprint convention where `across_m` is a chord rather than an arc. Both are
checked by `tools/bake_station.py --selftest`, which asserts the arc inverts exactly and that
the spine lies inside some footprints and outside others — a sidecar every one of whose places
"contains" the walk angle would pass every arrival test ever written and mean nothing.

**Authority 5.**

---

## INV-732 — the goal is the footprint's near edge, and the turn is arrival itself

**What.** On the outbound leg the gate steers at `z_m ∓ half_z_m` — the edge of the target's
footprint facing the start — and it turns round when the **arrival predicate** fires, not when
it is within `reach_m` of a coordinate.

**Why.** Both halves were found by running it. Aiming at the place's **centre** (7960.0), the
body arrived inside `obs_dome_2` at z = 7942.05, kept walking toward the centre, stalled 6.5 m
short of it against something solid, and the run was recorded FAIL — a gate failing on a claim
nobody was making, because a centre is a point that may be inside a wall, a console or a
bulkhead. Moving the goal to the near edge then produced the opposite error: the 3.0 m `reach`
tolerance stopped the body at 7939.04, **2.96 m outside** the place, and the run reported
`legs=2` with `arrived=NO`. A tolerance is the right way to decide "close enough to a
coordinate" and the wrong way to decide "inside a volume", because the volume already has an
exact boundary and the tolerance can only cross it the wrong way.

**Constrained by.** `half_z_m` is `along_m / 2` from the register. `reach_m` keeps its meaning
on the **return** leg, which does go back to a coordinate.

**Why this is not circular.** `arrived` is set by the footprint test alone. A body that never
enters the footprint never turns, and the run ends on the stall detector or the frame cap with
`legs < 2` **and** `arrived=NO` — which is what the pre-change control does.

**Overturned by.** A place whose built geometry does not fill its declared footprint, which
would make the near edge a point in the void. `deck.py --sweep` is the check that would say so.

**Authority 5.**

---

## INV-733 — freeing is measured as DRAWDOWN, because a peak at the end is not a leak

**What.** The gate asserts `drawdown ≥ 1`, where drawdown is the largest fall of the resident
cell count from a running peak, sampled every physics frame.

**Why.** `frees > 0` says a cell was released **once**; it does not say the resident set ever
came **down**. The first version of this check measured "the minimum resident count after the
peak" and failed a run that plainly freed: the peak of 7 happened at the **end** of the
traverse, in the dense cluster the body finished in, so "min after peak" was 7 and the gate
reported *cells are accumulating* about a run whose own step log shows the set going
4 → 2 → 4 → 2 → 4 all the way along, with `loads=35 frees=30`. **A statistic that depends on
where the maximum falls is not measuring the property.**

**Constrained by.** Drawdown does not care where the peak is, and it is still zero — still
failing — for a set that only ever grows, which is the case the check exists for.

**Measured.** The passing run reports `resident_peak=7 resident_drawdown=5`.

**Overturned by.** Nothing about the station; this is a property of the statistic. It would be
strengthened by asserting the resident set is bounded by the nominal three plus in-flight,
which is a different claim and belongs with the triangle budget.

**Authority 5.**

---

## INV-734 — the triangle overage is printed, not failed, and the module's own header says so

**What.** `--axial-gate` reports `peak resident 359,584 tri against a 180,000 budget (2.00×)`
on its own labelled `OVER BUDGET` line, in the PASS text as well, and puts it in the **exit
code only under `--strict-budget`**.

**Why.** `stream.gd`'s header sets the policy explicitly, under *"WHEN THEY DISAGREE,
CORRECTNESS WINS AND IT SAYS SO"*: if the sight line demands more triangles than the budget
allows the streamer keeps the cells and prints `OVER BUDGET`, *"because dropping a cell the
player can see is a pop and going over budget is a frame cost"*, and it states the measured
consequence outright. The gate in the same file then took that printed, expected, deliberate
condition and made it a **FAIL** — so the residency acceptance could never pass on real
content, and the streaming question and the content-cost question were welded into one verdict
where the second always won.

**Constrained by.** This is CLAUDE.md's session-4e lesson: one honestly-red gate must not blind
every answer behind it, and the fix there was **not** to make the red gate pass but to stop it
hiding the others. Nothing here is quieter than it was — the overage is computed identically,
printed on its own line, and repeated inside the PASS text so a PASS cannot be read as "in
budget". `station/budget.py` remains the authority that owns the number.

**What would overturn it.** A ruling that the resident budget is a hard ceiling rather than a
target. `CLAUDE.md` currently says the opposite — *"the triangle budget is a TARGET, not a
ceiling"* — and if that is reversed, `--strict-budget` becomes the default and this entry is
withdrawn.

**Authority 5.**

## INV-721 — The hotel/business rent rung, the top of PLY-03's climbable ladder

**What.** `economy.LADDER` gains `("room_hotel", 30.0, 45.0, "week", 5)`.

**Why.** `docs/THE-STATION.md:172` states the player's own rent ladder as *"transient 4–8
cr/wk → civilian 10–15 → hotel/business class, filed at PLC-032"* and calls it climbable,
and says *"the top tier plus furnishing it is one of SYS-04's three late-game sinks"*. The
first two rungs were rows of `LADDER`; the third was not, so the thing the row says you
climb TO had no price and `spec_check.py --red` said so in PLY-003's own words.

**What constrained it.** Two published rows, one step each, so no free number is
introduced. The FLOOR is `quarters_command` = 30 cr/wk, the only authority-1 price in the
whole table — a commercial let cannot sensibly undercut what the station values its own
senior tenancy at. The SPREAD is the civilian row's own width, 15/10 = ×1.5, applied to
that floor; the table gives exactly one width for a residential rung and re-using it is one
decision rather than two. The result, 30–45 cr/week, is 3–5.6 days of the `labour_casual`
8–15 cr/day band, which is what "late-game sink" has to mean arithmetically: unreachable
for a lurker, ordinary for a trader. `PLACES.md:1957`'s four Red hotels are *"a cut above
qtr_transient"*, which the ordering satisfies.

**What would overturn it.** Any stated hotel tariff or business-let rate anywhere in the
reference; a per-week figure attached to `PLACES.md:1957`'s hotels; any depiction of a
station commercial lease. Also overturned in part by anything establishing that Babylon 5
does not let commercial rooms at all, which would delete the rung rather than reprice it.

## INV-722 — The GDS-01 vocabulary widened from 34 named goods to 65, and two new bands

**What.** Thirty-one lines added to `economy.GOODS` in four labelled blocks — household
goods, what a lurker sells, the route widened, and what 250,000 people of nine species buy
— plus two `CLASS_BAND` rows, `household` and `licence`.

**Why.** `PLACES.md` §0.3 sets the floor at *"≥60 named goods at completion"* and the table
held 34. But the floor is a number and it is not the reason: the reason is `sell()`. A
vocabulary of 34 lines, 27 of them things only a licensed counter carries, gives a player
nothing to dispose of, so a sell verb would have been machinery with no content — this
project's signature defect wearing different clothes. Every block is something somebody
aboard would put on a counter and somebody else would carry away. `pitch-fee scrip` is
named in GDS-01's own seed sentence and had no row at all.

**What constrained it.** The two bands are each one step from a published figure.
`household` IS the `quarters_personnel` row (10–15 cr) on the argument that a durable
furnishing costs about a week of the rent of the unit it furnishes — eight items furnish a
room for 80–120 cr, which against the 8–15 cr/day casual band is the eight days of work
PLY-03's "late-game sink" needs to be. `licence` is not derived at all: `PEOPLE.md:758`
states the Zocalo pitch fee as **4 cr/wk against TRAFFIC:630–643**, so the band is that
figure at both ends and it is the second sourced price in the file after `quarters_command`.
Individual lines are constrained by things already in this repository rather than by memory
— `schedule.STATION_MIX`'s species shares, `rooms.FIXTURES`, `traffic.MANIFEST`'s cargo
classes, `LAW-CRIME` 6.2's 22% on salvage, PEOPLE.md CAST-41's *"Llort suppliers
overnight"*, `incident.PAKMA_MEALS`' 04:00 meal, PLC-026's racks, PLC-036's bonded cage.

**What would overturn it.** Any on-screen stall, menu board or manifest naming a ware this
table does not carry, or contradicting one it does. Any of the four route lines being shown
as licensed trade. A stated price for a furnishing, which would replace the `household`
derivation with a source. Era drift: every line is S2–3 and a later-season ware is FIDELITY
0, not a near miss.

## INV-723 — The bid: what a counter pays, and why the fence pays less

**What.** `economy.BUY_BACK = 0.5` and `economy.FENCE_TAKE = SUPPLY_MULT["route"] = 0.75`.
`bid(good, place) = price(good, place) × BUY_BACK × (FENCE_TAKE if the counter has no
reader)`. So a shopfront pays 50% of its own shelf price and a fence pays 37.5%.

**Why.** VRB-05 is BUY/SELL and only the buy half existed; a sell needs a price, and a
second margin invented here would be a second answer to a question this file had already
answered.

**What constrained it.** Neither factor is new. `CLASS_BAND` derives the `staple` band as
half the `meal` band on a stated argument — *"a cart selling a 1–2 cr plate cannot have
paid more than about half of that for its ingredients or there is no cart"* — and that
sentence **is** a buy-back rate: it says what a counter pays for a unit of what it sells. A
counter taking a line back over its own counter is buying the same thing from a different
supplier. `FENCE_TAKE` is `SUPPLY_MULT["route"]`, which LAW-CRIME:858–879 already fixes at
0.75 because the route undercuts the Zocalo (SYS-06); a fence does not keep what it buys,
it moves it on the route, so its shelf is worth 0.75 of a licit shelf and its bid is 0.75 of
a licit bid. The spread is the mechanic: the fence pays worse **and** is the only buyer for
what a licensed reader will not touch, which is what FACTIONS 11.4 says the black market is
for. Bounded below by `bid > 0` and above by the assertion in `economy.py --trade` that no
counter anywhere pays more than it charges — 0 pairs over 18 counters, and
`--break-margin` sets `BUY_BACK = 1.2` and shows that assertion going red.

**What would overturn it.** Any depicted resale, pawn or fencing transaction with both
numbers visible. Any statement of a retail margin aboard. A stated commission for N'Grath
or for Solly Vane's stall. Also overturned by anything establishing that the route sells at
parity rather than at a discount, which would collapse `FENCE_TAKE` to 1.0 and remove the
reason to prefer a shop.

## INV-724 — Ada Roskoe, the household-goods keeper at PLC-052

**What.** `economy.HOUSEHOLD_KEEPER = ("Ada Roskoe", "shops_kiosks")`.

**Why.** `THE-STATION.md:172` requires that *"a **household-goods vendor** exists (a named
keeper among PLC-052's shops)"* and one existed nowhere in `station/`, `godot/` or `tools/`.

**What constrained it.** PLC-052 is `shops_kiosks` and its register functions are
`("commerce", "retail")`, so the STALL is derived from the register exactly the way
`Good.sold_by` is — `household_vendor()` returns whatever `goods_list` puts on that pitch,
never a hand-written list. PLACES.md:848 gives PLC-052 *"~48 named keepers, two shifts"*, so
one named keeper is inside a stated population rather than an addition to it. The NAME is
the only authored thing: a human forename and surname of the kind `npc/names.py`'s fitted
human grammar draws, fixed as a constant so a save and a nameplate can refer to the same
person across processes.

**What would overturn it.** Any on-screen name for a Zocalo-arcade household trader; any
production list of PLC-052's keepers; a decision to draw the 48 keepers procedurally from
`names.py`, in which case this constant becomes seed 0 of that draw rather than an
invention.

## INV-760 — a knowledge item about mutable state goes stale after 7 station-days

**What.** `station/journal.STALE_AFTER_DAYS = 7`. A SYS-16 fact of a mutable kind (`route_time`,
`job_offer`, `appointment`, `rumour`, `debt`) that has not been re-learned or verified within seven
station-days reads as `stale` rather than as current. The five fixed kinds (`name_given`,
`tell_learned`, `incident_seen`) never expire.

**Why.** SYS-16's own tick clause requires it — *"a fact about mutable state carries its as-of day
and can go stale"* — and gives no number. Seven is the station's own shortest repeating cycle that
a fact could outlive: `docs/spec/PEOPLE.md`'s wage table is quoted **per week** throughout (service
crew 35–50 cr/wk, guild docker 60–75, the 4 cr/wk pitch fee, the 10 cr/wk Nightwatch supplement),
and LAW-CRIME's rent ladder is weekly, so a week is the interval over which a job, a debt or a
berth price is expected to be restated by the world itself. A fact that has survived one full
restatement cycle without being restated is exactly the one a broker should not sell as current.

**Constrained by.** It must be long enough that a player who learns a route time on day 0 can still
use it on day 3 without the journal nagging, and short enough that ROLE-10's verify step has
something to do. It is DERIVED at read time (`Fact.state_on(day)`) and never stored, so changing
this constant re-ages every fact already in every save file rather than leaving stale flags behind.

**What would overturn it.** A spec row naming a different horizon, or a shipped economy whose
prices move on a cadence other than weekly — in which case the horizon should be that cadence.

## INV-761 — a claimed route time more than 1.00 station-minute from `transit.py`'s is refused

**What.** `station/journal.ROUTE_TOL_MIN = 1.0`. `mint_route_time(..., claimed_min=x)` writes the
fact only when `|x − transit.py's derivation| ≤ 1.00 min`; otherwise it raises `Refused` and
nothing is written down.

**Why.** SYS-16 requires that *"a route-time references transit.py's derived numbers"*. Without a
tolerance that clause is decorative: a minter that accepts whatever it is handed and stores the
derivation beside it has recorded a claim, not a reference. One minute is the granularity a person
actually reports a walk in — nobody says "eleven minutes and forty seconds" — and it is comfortably
below the shortest real leg on the boot deck (`customs_north → arrival_concourse`, **0.57 min**) so
a wrong answer about even the shortest walk is caught.

**Constrained by.** It must exceed the arithmetic spread `transit.walk_leg` itself has between two
readings of the same pair (zero — the function is pure) and stay under the smallest difference
between two legs a player could confuse. It must not be so tight that a dialogue line rounding
"about ten minutes" is refused for being round.

**What would overturn it.** Dialogue that quotes route times to the minute rather than
conversationally, which would want a tighter figure; or a transit model with genuine variance
(queueing at a lift), which would want the tolerance derived from that variance instead.

## INV-762 — the three legs the runtime may quote are the boot deck's own rooms

**What.** `station/journal.DEFAULT_ROUTES` is `customs_north → arrival_concourse`,
`arrival_concourse → customs_south`, `customs_north → customs_south`.

**Why.** A `route_time` fact is *"the porter's craft"* — a shortcut the player learned by walking
it. A manifest that offered the runtime a leg on a deck the player cannot reach would mint a fact
about a walk nobody took, which is the same defect as an incident in an unreachable room that
`station/boot.py::_collapses` already refuses to bake. These three are the rooms `boot.json` lists
for the deck the shipped build spawns on, so every quotable leg is one a body can actually cover.

**Constrained by.** The list is data rather than a rule: when streaming reaches more clusters the
right set is every pair of rooms in the resident cell set, and the derivation should move to
`boot.json`'s own `rooms` rather than to a longer literal here.

**What would overturn it.** A boot deck with different rooms — at which point this constant is
stale and should be derived from the manifest instead of edited.

## INV-763 — a clock step over four frames' worth of station-time is a JUMP, not a run

**What.** `godot/scripts/journal.gd::JUMP_TOL = 4.0`, floored by `STEP_FLOOR_H = 0.02` station
hours. A frame in which `Clock.hours_abs()` advanced by more than `rate × delta × 4` is recorded as
a jump: the interval is added to `_jumped_h` and **nothing in it is witnessed**.

**Why.** PLY-05 requires the clock to advance *"through the running simulation"*, and this project
has no other way to tell that apart from a jump — `godot/scripts/life.gd`'s Director is
deliberately pure in the hour (*"nothing integrates, so 03:00 and 13:00 are two reads of the same
expression"*), so the crowd, the ambience and the dialogue takes all read identically after
`Clock.set_hour(h)` and after seven hours of ticking. A gate written against any of them cannot
fail on a jump, which is this repository's signature defect. The journal is the only accumulating
state in the build, so the discrimination has to live in it.

**Constrained by.** One frame advances the clock by exactly `rate × delta` — `Director._process` is
`clock.tick(delta)` and nothing else — so the bound is that quantity, and the only free parameter
is the slack for a frame that hitched. Four is a frame taking four times its budget. The quantity
being discriminated is a **7.25 h** jump against a **0.0667 h** frame at the gate's own ×240
compression, which is 109×: the two are nowhere near the threshold and the gate does not depend on
where in that gap the line is drawn. `STEP_FLOOR_H` exists so the first frames after a scene load,
where `delta` is small and the clock has not started, cannot be read as a jump.

**What would overturn it.** A build in which something other than `tick(delta)` moves the clock
each frame, or a compression rate high enough that one frame legitimately crosses several timed
calls — at which point the discrimination should move to comparing the integral of `rate` over the
frame rather than to a per-frame bound.

## INV-764 — the compression gate sleeps 7.25 station hours

**What.** `godot/scripts/journal.gd::SLEEP_H = 7.25`.

**Why.** It is PLY-05's own scenario read off the row rather than chosen: *"sleep at 22:00 with a
05:15 intent and wake at 05:15 — in time to make the 05:40 muster"*. 22:00 → 05:15 is 7.25 hours.
Using the row's own number means the gate measures the case the spec asks for, and a scenario that
later changes changes the gate with it.

**Constrained by.** It must cross midnight, because a wrapping clock is where this project's last
compression bug lived (`coldstart.py::g8`'s first draft advanced 3,600 hours, which is exactly zero
on a 24-hour ring, and reported the clock as broken when the control was). 22:00 → 05:15 crosses it.

**What would overturn it.** A change to PLY-05's stated scenario.

## INV-765 — a compressed night must have been present for at least 4 timed calls

**What.** `godot/scripts/journal.gd::WITNESS_FLOOR = 4`. A `--phase=compress` run passes only when
the journal minted at least four knowledge items from broadcast calls it passed through.

**Why.** The floor has to be high enough that a single call caught at the boundary cannot pass it
and low enough that it is reachable at any plausible frame rate. `station/journal.timed_calls()`
gives `broadcast.day(0)` **174** timed calls, of which **62** are audible in the boot deck's three
rooms — one every 23 station-minutes — so 7.25 hours contains about **18**. Four is a quarter of
that: a run that witnessed fewer than a quarter of the night's calls was not present for most of
the night, whatever its clock says.

**Constrained by.** It must be > 1, or a single call arriving in the same frame as a jump would
pass; and it must be well under 18, or a slow container that spends fewer frames on the interval
fails for a reason that has nothing to do with the thing being tested.

**What would overturn it.** A different boot deck with a different call density — the honest form
is a fraction of `calls.size()` scaled by the slept interval, and this constant should become that
expression when more than one deck is streamed.

## INV-790 — the Observer: where the player is standing, and what they do about what they see

**What.** `station/incident.py::Observer` — a register place, a `Probe` volume built from it once,
a sight radius taken from `populace.corridor_sight_m()` at call time, an optional set of waking
hours, and a **policy**: `(incident) -> stance`. `simulate(..., observer=...)` consults it at
exactly one point, after the draw and after the cast is named, to choose which of
`absent / helps / reports` the incident is resolved in. Four policies ship: `absent` (present and
does nothing — the null control), `helps`, `reports`, and `citizen`, which reports what the
station would already punish and helps what it would not.

**Why.** `MASTER-PLAN` A2 promises the player *"is drawn into events that would have happened
without them, changes how they end"*, and `docs/THE-GAME.md` §7 lists the absence row red. Before
this, **every incident on the station resolved ABSENT, forever** — `simulate` took no observer and
its docstring justified that with SYS-14's *"none of them requires the player to exist"*. That
clause is about the RATE. Applied to the resolution as well it removed the second half of A2's
sentence: `three_ways` replayed one hand-picked incident into three fresh worlds, which checks the
class table, and **no day the player was in had ever been run**.

**Constrained by.** The separation SYS-14 demands is kept and is asserted rather than claimed: an
Observer may not touch a lambda, so `absence()` checks first that a player-present day fires the
**identical incident stream** — same class, same place, same minute, same named cast — and only
then that the worlds differ. `policy_citizen` is derived from `books_custody(cid)`, which resolves
the class rather than reading a fifth hand-written table of class ids. Witnessing is
`Probe` ∧ sight radius, both of which already existed and neither of which this file chose:
SYS-14 requires a volume *"never a floating radius an implementation can shrink"*.

**What would overturn it.** A ruling that the player's stance should move rates as well as
resolutions — e.g. that a visible uniformed player suppresses petty theft nearby. That is a real
design position and it would make the stream-identity assertion above wrong rather than merely
looser, so it should be taken deliberately if at all.

## INV-791 — a find needs a scanner, not a response time

**What.** `incident._scanned(place)` — true for the register's customs halls, false elsewhere — is
now INC-CONTRA's discriminator in the ABSENT branch, ANDed with the existing `_responded()`. Where
it is false the contraband leaks and `_stock(w, "black_market", item, +1)` fires.

**Why.** `spec_check --red` reported INC-CONTRA as a declared write that cannot happen: SYS-14's
row declares `{custody, seizure, stock}` and 72 resolutions produced `stock` never. The leak limb
was guarded by `_responded()` alone, and `response_s` is **0.0 at both customs halls at all 24
hours**, so it was unreachable by construction. Read the shape before the size: across the register
`_responded` is a genuine discriminator — **1,469 of 3,096 place-hours carry a non-zero wait** —
and a constant TRUE at exactly the two places this class was bound to. A number that fails 100% on
one side of a line is a structural fact, and the structure is that the question was wrong. A
uniform standing in the room is not what finds concealed goods; the scanner is. `customs_north`
declares `baggage_scanner`; `cargo_bays` declares `cargo_crane`, `container` and
`manifest_terminal` and screens nothing — which is exactly why `security.BLACK_MARKET_ROUTE[0]`
names it the route's entry, *"42 bays on a station that is not full, with spare volume nobody
inventories"*.

**Constrained by.** Neither the spec nor the station was edited to make the other pass. The control
is in `_selftest`: at a hall that scans, the same class still ends in a seizure and a custody row
and **nothing** reaches the black market, so the leak is the scanner's absence rather than a
weakened rule.

**What would overturn it.** Any canon establishing routine screening of cargo manifests at B5, or a
frame showing a scan arch on the cargo side.

## INV-813 — a fitting is priced by its VALUE band as well as by its silhouette

**What.** `npc/costume.py::Attachment.honest_from_m` returns
`max(body.honest_from_m(error_m), body.aliases_beyond_m(value_m))`. `value_m` is the width of the
contrasting band the fitting paints and is `0.0` for a fitting that is the same value as what it
sits on. Every band's `value_m` is `2 x <its own half-height constant> x HUMAN_STATURE_M`, and
those constants (`COLLAR_HALF_H_F`, `EPAULETTE_HALF_H_F`, `BELT_HALF_H_F`, `BALDRIC_HALF_W_F` and
the five `CONSTRUCTION` ones) are the same literals `_build_mesh` builds the band from — hoisted
out of the builder so a table entry cannot drift from the geometry.

**Why.** The old rule priced a fitting purely by how far it moves the OUTLINE, against
`body.PIXEL_BUDGET = 1.5 px`. A waist belt moves the outline 8 mm, so it was honest to drop at
5.5 m — and the shipped corridor crowd is baked at chain level 4 (`populace.corridor_lod` returns
4 for a Blue ring, switch distance 23.6 m), so **not one of the forty walkers on `blue/0/0` had a
belt, an epaulette or a baldric.** Measured by group census over
`station/generated/scene/deck/shot_blue_0_0.obj`: four groups a person and nothing else. A dark
leather belt across a coat of albedo 0.06 barely changes the silhouette and is the only horizontal
in forty centimetres of unbroken value; it goes on reading long after it stops being a bulge. The
table's own `armband` note had already made this argument in prose — "the DECAL it carries stays
legible to 16.4 m and visible as a dark band far beyond" — and then priced the strap by silhouette
anyway.

**Constrained by.** `body.aliases_beyond_m` is not a new rule: it is the existing one-pixel shading
rate `body.py` already uses to decide when a whole figure stops being a figure, applied to a band
instead of to a person. It is a CEILING, not a floor — a 56 mm belt survives to 57.6 m and no
further, which is inside the 82 m longest sightline down a Blue ring corridor
(`2*sqrt(R^2-(R-w)^2)`, R = 211.478 m, w = 4 m) but not indefinite. `armband` is deliberately left
at `value_m = 0.0` because its decal is priced separately and covers the same band; giving the
strap a value term would double-count one stripe.

**What would overturn it.** A measurement of how far a same-family value step (0.055 leather on
0.092 cloth, both measured off `more zocalo.png`) actually survives in a rendered frame. The rule
assumes a one-pixel band is worth keeping, which is true for a step of that size and would not be
for a step of 0.005.

## INV-814 — garment construction is PARTS, because a span reaches nobody

**What.** `npc/costume.py::CONSTRUCTION` and `_construct`: the shoulder yoke panel, the front
closure placket, the coat hem, the two sleeve cuffs and the two boot tops, each built as its own
CLOSED SOLID sewn proud of the surface under it, exactly the way `ATTACHMENTS` already builds a
collar. Sized off the part's own extent read back by `_axis_at` / `_front_at`, never off
`body.FIGURE`. Gated by `costume.py --construct`, whose negative control is `--construct --legacy`.

**Why.** The yoke was a *span split* inside the torso part, and its own note was proud of costing
zero triangles. `npc/animation.py::_groups_for_parts` resolves ONE material group per PART, by the
triangle offset the part starts at — its docstring says so — so a second span inside a part is
unreachable through it. Every person on the station is posed, and posing goes through that
function. Measured: **0 of 40 corridor walkers** on the built `blue/0/0` deck carry any
`npc_cloth_trim` group, while `build_dressed` emits the yoke at every chain level including the
coarsest. The gate reports **0/96 figures before, 96/96 after**. This is the tenth instance of the
defect CLAUDE.md enumerates — finished, tested machinery with no caller on the shipped path — and
it survived ninety self-test assertions because every one of them scored the part in isolation.

**Constrained by.** The yoke's placement and fabric are unchanged: `YOKE_TOP_FRACTION = 0.78` and
`civ_collar_yoke` are the existing authority-1 measurements off `more zocalo.png`, and this only
changes what carries them. The CUFF is authority 2 and was already written down in this file and
never built — `ef_command`'s note records, off `Sheridan.jpg` and corroborated on a second subject
in `Zach Allan in security uniform.jpg`, that "the CUFF carries a brown leather band with crimson
piping on BOTH its edges". The PLACKET is authority 5 and its argument is that a closed loft is not
a garment: a coat has to open to be put on. It is suppressed on robed sets and on plastron sets,
which have their own front. Cost, measured by `costume_triangles`: **412 of 7,304 triangles at
LOD0 (5.6%) and 140 of 1,236 at lod3 (11.3%)**; on the shipped corridor level a person goes from
624 to 768 triangles, which on a 40-walker Blue deck is +5,760 against 869,924 — **0.66% of the
deck**. The two self-test caps are now fractions of the body the construction is sewn to rather
than the absolute 260 and 100 they were when clothing was free, and they fail if a sixth piece is
added.

**What would overturn it.** A runtime that resolves materials per span rather than per part would
make the span split reachable again and the panels redundant as *value* — though not as relief,
which is the half of AAA-STANDARD craft 4 ("lighting response varies across the surface") an
albedo split cannot deliver. Any frame that resolves a civilian wrist or hem on this station would
replace the authority-5 extrapolations with measurements.

## INV-815 — one grime material for the whole station, and the first thing `wear` has ever touched

**What.** `FABRICS["garment_soil"]`, declared albedo `(0.048, 0.045, 0.041)`, roughness 0.96,
authority 5. The hem, the cuffs and the boot tops of any resident whose `Costume.wear` is at or
above `WEAR_SOIL_MIN = 0.30` are cut from it instead of from their own garment.

**Why.** `Costume.wear` has been drawn per individual from each costume set's own range since this
file was written and reached **nothing** — no mesh, no material, no group; `grep` finds no consumer
outside `costume.py` itself. AAA-STANDARD's craft 4 asks for wear and grime that "vary across the
surface rather than being uniform", and the round-2 scorecard finding on this subsystem is exactly
"each garment reads as one flat value ... no variation within a garment". This is the cheapest true
answer available: one material, applied to the three places on a garment that touch the world.

**Constrained by.** ONE fabric rather than a soiled twin per garment, and that is a physical claim
rather than a saving: grime is a property of the DECK, not of the coat, so the same dust settles on
a Minbari's black robe and a docker's drab. It also costs the library one material instead of
thirty. The value is the middle of the measured civilian floor — `civ_cool_dark` 0.029 to
`civ_worker_drab` 0.156, four samples off `more zocalo.png` — desaturated, by the same argument
`civ_lurker` already records. `WEAR_SOIL_MIN = 0.30` is set so it separates the crowd rather than
colouring all of it or none: `civ_business` (0.02–0.15) and `ef_command` (0.02–0.10) never reach
it, `civ_worker` (0.35–0.85) and `civ_lurker` (0.65–1.00) always do, and `civ_ordinary`
(0.10–0.40) is split.

**What would overturn it.** Any frame that resolves the bottom 100 mm of a garment on this station.
`Costume.value_jitter` is still unreached and is recorded here as such: it is a per-individual
value multiplier, and reaching it needs a per-instance shader parameter this pipeline does not
have — `materials.py` builds one material per fabric and the renderer draws instances of a shared
library.

## INV-792 — the cargo consignment rate, and 20 t of it

**What.** `incident.cargo_consignments_per_hour` = `CARGO_T_PER_DAY / CONTAINER_T` spread over
`traffic.rate_per_hour`'s own arrival curve and split across the cargo places the register has.
`CARGO_T_PER_DAY = 4500.0`, `CONTAINER_T = 20.0`. INC-CONTRA's rate on the cargo side is that
times `arrival.CONTRABAND_P`, producing ~2.2 leaks a station-day.

**Why.** INC-CONTRA now fires on the cargo side (INV-791) and `hall_souls_per_hour` is a customs
number — souls a minute through one hall, from `traffic.hall_rate`. Borrowing it for a cargo bay
would be a rate on the wrong denominator, which is the defect this module's own MTBF check caught
once already: *a derivation is not checked until its own units are.*

**Constrained by.** The tonnage is the spec's: `docs/spec/PLACES.md` PLC-`cargo_bays` prices the
transshipment ledger at *"4,000–5,000 t/day through SYS-02/04"*. The share that carries something
is `arrival.CONTRABAND_P` **reused** rather than a second constant, exactly as `arrival` itself
reused it for TRAFFIC 6.6's leak — "one in a hundred goes wrong" is the same claim either side of
the hull. Only `CONTAINER_T` is invented, at authority 5, and it is bracketed rather than guessed:
a cargo unit small enough to carry by hand makes the manifest meaningless, one larger than a
shuttle bay does not fit through the mouth, and 20 t is a standard intermodal payload. The output
is bracketed too — under one leak a day would make LAW-CRIME:858's route decorative, dozens would
make smuggling the norm rather than a crime.

**What would overturn it.** Any figure for B5 cargo unit mass, or any seizure volume for the cargo
side, or a stated throughput that replaces the spec's 4,000–5,000 t/day.

## INV-745 — a room's collision box is its MODULE's box, measured, not a representative bay

**What.** `deck.room_box_m` returns `(x0, x1, ceil_m)` for every place, and it is the only
thing `deck.room_shell_for`, `deck.room_half_w_m` and `deck_plan`'s door-fit test are allowed
to ask. For a place `bespoke.compose` draws, all three numbers are MEASURED off the module's
own mesh through `bespoke.room_shell`; for a place `rooms.build` draws they are
`rooms.built_span_m` and `rooms.ceiling_m` unchanged. `collision.room_shell` gains `x_off_m`
so an asymmetric box can be expressed at all.

**Why.** Not an aesthetic choice: 20 of the 33 composed places on the station had render
geometry outside their own collision shell. `ambassadorial_suites` had a +/-5.25 m shell
around a mesh running -92.28..+8.53 m — 87.04 m of room a body could walk out of. Both
call sites carried the pre-4k expression `min(room_extent_m, bay_span_m) / 2`, which is the
width of one generic representative bay; session 4k replaced exactly that expression on the
AXIS, for exactly this reason, and left the width.

**What constrained it.**

* **The measurement, not a number.** There is nothing to invent: the module's mesh is the
  room, and `bespoke.room_shell` is already the call `--shell-fit` scores containment
  against and the call `deck.room_geometry` composes from, so no second description of a
  module's size exists to drift. This is hard rule 4 (inside and outside from one schema)
  applied to a third mesh.
* **The offset is forced by `bespoke.room_shell`'s own frame.** It recentres a module's x on
  its DOORWAY rather than its bounding box — its note says local x = 0 "is not a centre, it
  is a DOORWAY" — so a symmetric half-width about the place's bearing cannot describe
  `arrival_concourse` (-17.37..+3.53 m) at any width. Either containment or the neighbouring
  arc has to give.
* **The ceiling is `max(declared, measured)` and never the measurement alone.** The mesh
  height is what the shell must CONTAIN; `rooms.ceiling_m` is what the place is specified
  at. Taking the mesh alone would let a module that models only its lower storey shrink the
  volume a body may occupy. `council_chamber` goes 3.60 -> 7.42 m, `downbelow_arch`
  3.40 -> 23.57 m.
* **Non-overlap is now asserted rather than inherited.** `directory.collisions()` asserts
  footprints do not overlap, so a shell inside its footprint used to inherit non-overlap by
  construction. Widening the shells spends that: `qtr_transient` builds 69.68 m of module in
  a 58.28 m footprint. `deck.py --shell-fit`'s OVERLAP leg therefore tests the arcs the
  shells actually span, pairwise, on every shared sector/ring/deck with overlapping z bands.
  It reports 0 — measured, not assumed.
* **The 89 generic places do not move.** `built_span_m()[0]` is `min(w_full, bw)` for them,
  which is the number both call sites returned before, and the door-fit test reduces to the
  old `abs(dx) + door_w/2 < hw - WALL_T` whenever `x0 = -x1`. Asserted by `--legacy`.

**What would overturn it.** A composed module that emits geometry it does not intend a body
to reach (an exterior greeble, a skybox card) would inflate its box, and the answer would be
to measure a named subset of its groups rather than its whole mesh. Landing P1 of
`scratchpad/PATCHES-4t-shellfit.md` — `bespoke.axial_plan` returning `bay_w` — makes
`rooms.built_span_m` true for composed places, at which point `room_box_m`'s `module` branch
collapses into its `builder` branch and only `x_off_m` remains.

## INV-770 — which cell of the brig a booking goes into

**What.** `station/enforcement.py::brig_cell(npc_id, day, seed)` returns a cell number in
`1..consequence.BRIG_CELLS` (32, the midpoint of LAW-CRIME's sourced 24–40), drawn through
`consequence._u` on the key `("brig_cell", npc_id, day, seed)`. Authority 5.

**Why.** A booking record has to name a cell, and it has to name the **same** cell every time
that record is read — including after the process has ended and a new one has reopened the
ledger. A real custody desk allocates the next free cell, which needs a brig-occupancy model
across a station-day; `consequence.brig_check` already owns that question and already fails when
a day's arrests overflow the sourced range, so building a second occupancy model here would be
the duplicate-rule defect this repository has paid for four times. What a *player* needs is
weaker and different: stability. A hash on the two things a booking is identified by gives that
for nothing, and puts the draw on the same seed line as every fine, deferral and discretionary
stop in `consequence.py`.

Measured over 64 bookings the draw returns **28 distinct cells in 1..32**, which is the check
that stops a constant wearing a hash from passing — `enforcement.py --selftest`.

**What would overturn it.** An occupancy model that can answer "which cells are free at hour h".
Then this becomes `next_free(hour)`, the booking stores the answer, and this function is
**deleted** rather than kept beside it — a stored cell and a drawn cell in the same build is
exactly the disagreement this entry exists to avoid.

## INV-771 — a place that reads a card also searches the bag

**What.** In `godot/scripts/enforcement.gd`, a stop opens at any place whose baked row has
`reads_card` when the player is carrying a good `economy.GOODS` classes `contraband`, whether or
not the identicard admits them; the offence is then `contraband` (grade 3) instead of
`id_check_fail` (grade 1). Authority 5.

**Why.** Before it, the only thing that could open a stop was a **refusal**, and a refusal is by
construction something that happens to a card that is too *low* for the place. So the only people
the enforcement chain could ever meet were people with nothing left to lose:
`consequence.REVOCABLE[NO_STATUS]` is `None`, and `Record.ordinary()` does not count grade 1, so
**no possible run of the shipped build could demote anybody.** `--selftest`'s own check 4 asserted
that outcome ("a refusal at a door never withdraws a permission, at ANY rung") and was right about
it, which is why nothing failed.

The extrapolation is small and the constraint is the show's: customs is a search as well as a
reader — LAW-CRIME 6.5 names Dust and concealed weapons and `arrival.checks` station 9 already
refers on a hit, and `economy.py` already states that the offence against a customs-sealed good is
`consequence.OFFENCE["contraband"]`. What is invented is only that the search happens *at the same
boundary as the card read* rather than at some separate declared search point, because the register
declares no such point. It is also what makes `docs/THE-GAME.md` §4's load-bearing sentence
mechanical: *"Nightwatch and the Broker are both shortcuts, and taking either is how you lose
tier 2."*

**What would overturn it.** Any depiction placing the search somewhere other than the card reader —
a separate customs hall stage, a random patrol search, a scanner arch — or a register that declares
a `search` function. The rule then moves to those places and nothing else changes, because the
offence, the grade and the disposal are all `consequence.py`'s.

## INV-772 — the brig's world box, and why the stand point is the register's and not a mesh's

**What.** `station/enforcement.py::brig_address()` returns the brig's world point as
`collision.stand_at`'s own formula at `interior.place_floor_radius`, and a world AABB built from
three angular samples (`angle ± half_w/r` and the centre) at the floor and ceiling radii, ±
`deck.room_interior_half_m` in z. Authority 5.

**Why.** The engine has to be able to say "the player is at the brig" on a container where
**red/2/1 has not been built** — and it is not built here, which the run reports in those words
(`floor=NONE`). A bound taken from the deck's mesh would make the claim unavailable in exactly the
case where it is needed, and would also be a second description of where a place is: the register
says (sector, ring, deck, angle, z) and `interior.place_floor_radius` turns that into a radius, so
those are the terms the claim is made in. Three angular samples rather than two because the arc's
extreme x or y can fall at the centre of the span, not only at its ends.

**What would overturn it.** A built and streamed red/2/1: then the mesh bound is available, the
`floor` term becomes a real number instead of `NONE`, and the box should be checked against
`places.gd::boxes` rather than replaced by it — a disagreement between the two would be a finding
about the deck builder, which is the reason to keep both.

## INV-850 — the front door: which launches get a title screen, and what is on it

**What.** `godot/scripts/main_menu.gd` and `main.gd::_front_door`. A launch shows the title
screen if and only if it has a **display and no user arguments at all**; `--menu-gate` forces it
on headlessly and `--no-menu` forces it off. The screen carries four entries in this order —
NEW GAME (mode `arrival`), CONTINUE (slot `auto`), WALK THE STATION (mode `station`), QUIT — and
every entry that cannot run prints the reason on screen instead of being hidden.

**Why.** `docs/MASTER-PLAN.md` A2's definition of done opens *"a stranger downloads ONE FILE, runs
it at 60 fps, arrives at Babylon 5 as a person with papers"*. Measured at the start of session 4t:
`godot/export_presets.cfg` did not exist, `tools/` had no packaging path, and the strings "menu",
"title" and "new game" appeared nowhere in 25,000 lines of GDScript. There was no way for a person
to start this at all, and a stranger who launched the shipped build without the generated world got
`push_error` on a console they cannot see and exit 2 — a black flash and nothing.

**What constrained it.** The predicate is deliberately the narrowest one that captures
double-clicking and nothing else, because every gate in this repository launches the same scene:
`station/coldstart.py --g1` runs it headless with no arguments and must still get a body on a
floor, `tools/render_godot.sh` passes a scene path, and every developer command line passes
`--mode=`. A title screen that appeared for any of those would eat the gates. The ORDER of the
entries is `docs/THE-GAME.md` §1 — the card is the spine, so the entry that issues one comes
first, and the free-walk entry every developer here has used for eight sessions is second and
labelled as what it is. The COLOURS and the drawn-rather-than-assembled construction are
`arrival.gd::Face`'s, taken from that file so the title screen and the identicard a player is
about to be handed read as one object.

**What would overturn it.** A decision that the shipped build should open in the station and
offer arrival as a menu item rather than the reverse; a settings or accessibility surface, which
would make a drawn `_draw()` the wrong construction and force real Control nodes; any evidence
that a player expects CONTINUE first.

## INV-851 — the shipped layout, and why the "one file" is a tarball rather than an executable

**What.** `tools/package.sh` writes

```
Babylon5/
  Babylon5              the launcher a player runs
  game/Babylon5.x86_64  the double-precision engine
  game/Babylon5.pck     scripts, scenes, materials
  station/generated/…   the world
```

and tars it to `dist/Babylon5-linux-x86_64.tar.gz`. **113 MB** as measured, of which 112 MB is the
engine-plus-pack and 66 MB is one deck's world.

**Why.** Two measured facts, not preferences. **(1)** Every mesh, collision shell, interactables
sidecar, arrival sequence, cell set and audio bank is read at runtime from `<root>/station/…`,
which is OUTSIDE `res://`; Godot's exporter walks `res://` and nothing above it, so **no export
preset can pack the world**. The staged layout exists so that `res://..` resolves in the shipped
tree exactly as it does in the source tree. **(2)** There are no export templates on this box, and
the published ones would be wrong anyway: `project.godot` declares `Double Precision` because the
station is 8,047 m long (`docs/adr/0001-engine-choice.md`), and Godot's stock templates are single
precision. So the default is `--export-pack` — which needs no template — plus this project's own
double-precision binary renamed beside the pack, which Godot auto-loads.

**What constrained it.** The rule that a tool which can substitute a lesser mode must say which one
it used, on every run: `package.sh` names `mode=pack+engine` or `mode=export-release` in its own
output, greps the exporter's own `savepack: end` rather than trusting exit 0, and **launches the
finished artefact** and reads its first lines back — deleting the staged build if it does not
reach `MENUGATE … verdict=PASS`. `GODOT_TEMPLATE=<path>` switches it to a single self-contained
binary if a double-precision template ever exists.

**What would overturn it.** A double-precision export template (then the executable really can be
one file, though the world still cannot live in it); moving `station/generated/` reads behind a
`res://` mount or a custom pack, which would make the whole staging step unnecessary; a decision
to ship a launcher/installer instead of an archive.

## INV-852 — `main.gd::_root()` was editor-only, and an exported build looked for its world in the wrong place

**What.** `_root()` now falls back to `OS.get_executable_path().get_base_dir()` when
`ProjectSettings.globalize_path("res://")` is empty, and `--data=<dir>` overrides both.

**Why.** Measured in session 4t on the first packaged build: **`globalize_path("res://")` returns
the EMPTY STRING in an exported game**, because `res://` lives inside a `.pck` and has no
filesystem path. The old body — `globalize_path("res://").path_join("..").simplify_path()` — then
evaluated to the literal `".."`, resolved against the process working directory, so the packaged
game hunted for `station/generated/` one level above wherever the player's shell happened to be
and reported `no boot manifest`.

**What constrained it.** It is the nine-times defect one layer down: the function was correct,
tested and had **never been run on the path that ships**, because until this session nothing had
ever been exported. No static scan could have found it — `tools/wiring.py` asks whether a caller
exists, and this caller existed and ran. What found it was `package.sh` LAUNCHING the artefact and
reading its own output back, on the first run it ever did. The executable's directory is the right
anchor precisely because it does not depend on the working directory, which is what `".."` did.

**What would overturn it.** An embedded-pck build, where the executable and the pack are one file
(the base directory is still right); a platform where `get_executable_path()` is not the install
location — macOS `.app` bundles put the binary two levels down and will need their own case.

## INV-853 — manifest paths are rebased onto the install, not trusted as written

**What.** `main.gd::_rebase` and `_rebased_sidecar`. Any path in `boot.json` or in a
`*_arrival.json` build block that contains `station/generated/` is re-anchored on `_root()`
when the rebased file exists; the arrival sidecar is rewritten to `user://arrival_rebased.json`
because `arrival.gd::_adopt_build` reads it directly. Both are **inert** when nothing changes.

**Why.** `station/boot.py` and `station/arrival.py` write ABSOLUTE paths — correct and
unambiguous on the machine that generates the world, and four files that do not exist anywhere
else. The first packaged build launched, reached customs and issued a card **on the build box,
where the generator's own directory still existed**: the evidence was real and true for the
wrong reason. Untarred into a fresh directory with `scene/deck` hidden, the same build came up,
read all nine identicard fields and had **no player body at all** — the sequence loaded, because
its own path is derived from the already-rebased glb, and the deck under it did not.

**What constrained it.** It cannot be done at package time: the install directory is not known
when the tarball is made. It cannot be done by editing the generators, because an absolute path
is the right answer for every in-tree consumer (`walkable.py`, the render path, the gates). So it
is done at load, on the one fragment every generated artefact shares, with a fallback to the
original when the rebased file is absent — which makes a source-tree run rebase nothing, write
nothing and behave exactly as before. `tools/package.sh` launches the staged tree **from a moved
directory** and fails if the run did not print a rebase, so a build that only works where it was
made cannot pass.

**What would overturn it.** Generators that emit paths relative to the repository root, which
would make the whole function a no-op and is the better long-term answer; a `res://`-mounted or
packed world, which would remove the external tree entirely.

## INV-890 — a memo key quantises exactly once, and the value is built from the key's own value

**What.** `station/incident.py::_pool()`. One local `h = float(int(hour) % 24)` feeds BOTH the
memo key and the `resident.roster` call the value is built from. Authority 5 — a code rule, not
a station fact.

**Why.** The function previously keyed on `int(hour) % 24` and built its value from
`hour % 24.0`. Both are defensible readings of "the cast pool for a place-hour"; holding both at
once is not. Whichever fractional minute reached a place-hour FIRST froze the roster every later
incident there drew its named people from, so `incident.absence()` stopped being a function of
its arguments: measured, running an unrelated register-wide `headless_day(Ctx(day=1, seed="b5"))`
first in the same process moved the same seed's fingerprints from
`('73c2b0b24230d4a9','d7cd07f85eeced99')` to `('673fa4bd36591140','e56cbfa7ebc93561')`. Every
absent-vs-present comparison built on top of that was a comparison of two accidents.

**What constrained it.** `_LAM`/`_bucket_h` in the same module had already answered the question
correctly — key on `int(hour) % 24`, evaluate at `int(hour) % 24 + 0.5`, a pure function of the
same quantisation. `_pool` was the one site of the idiom that broke it, and the fix is the
project's own rule about checking every site of an idiom before deciding which one is wrong.

**What would overturn it.** Evidence that the cast pool should vary WITHIN an hour — that a
16-person roster at 13:05 should differ from the one at 13:55. If so, the fix is the other
direction: put the fraction in the key. What is not permissible is the third state, where the
key and the value disagree.

**How it is held.** `_selftest` asserts the pool for a place-hour is the same roster in either
warming order (13.9-then-13.0 against 13.0-then-13.9; on the broken code 8 of 16 people sit in a
different seat) and asserts it over the memo's KEYS rather than over the one call site, so a
second call site cannot reintroduce it. `--absence` asserts the end-to-end consequence: 576 cast
pools dropped and re-warmed at +0.97 h, then the identical call must return the identical
fingerprints.

## INV-891 — a ten-day horizon for "can a body fall over where the player stands"

**What.** `incident.collapse_gate` asks whether the producer behind `boot.json`'s `collapses`
array is non-empty **somewhere in ten station-days**, not on day 1. Authority 5.

**Why.** The shipped bake is deterministic — `boot.py::_collapses(rooms, day=1, seed="b5")` — and
the shipped deck is three customs rooms whose only reachable ragdoll class is INC-SICK at
**0.2323/day**. P(an empty day) is 0.79, day 1 is one of those, and `main.gd::_fire_collapses`
has therefore never dropped a body on the shipped build. A gate demanding a body on day 1 would
be a gate demanding the content be tuned until a number went green, which is the failure mode
this project has recorded most often. A gate demanding one *ever* is unfalsifiable. Ten days is
the horizon at which P(no body at all) = e^(-2.323) = **0.098** on the shipped deck — under one
run in ten — and it is a span a player plausibly plays.

**What constrained it.** It must be long enough that the current, untuned content passes (the
drawn answer is day 5) and short enough to run inside a gate (7.1 s over three places with the
day-1 caches already warm). Both bounds are measured, not chosen.

**What would overturn it.** A deck whose room set reaches docking_bays — the probe at
customs_north expects **49.620** collapses a day and its first day is day 1, so on that scope the
horizon is irrelevant. The horizon exists for the SHIPPED scope, and if the bake's scope widens
it should shrink.

**What it does NOT claim.** That a player sees a collapse. `main.gd` reads `collapses` and not
`if_helped`, so the stance the simulation resolved is baked and unread; and on the shipped deck
the array is empty. The gate's own output says so in words.
