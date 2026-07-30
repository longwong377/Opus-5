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
