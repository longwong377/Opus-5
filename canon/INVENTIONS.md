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
