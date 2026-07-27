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
- `reference/05-sector-green/corridor in alien sector.webp` — the section is a **chamfered
  polygon**, corners at roughly 45°, in a heavy frame with a pronounced reveal.

Both agree the section is a chamfered box with a flat deck and a flat soffit, **not a circular
bore.** That is a correction: the first assembly used `ring_frame` and read as a pipe.
`central corridor.webp` does show circular ribs, but of a two-storey volume, not a corridor.

Everything invented here is recorded as a **proportion**, not a metre value, and lives in
`PROVISIONAL`. The proportions are what the footage establishes; the height they multiply is
not, so resolving C-004 should change the table and nothing else.

**Overturned by:** a production floor plan or set drawing; or any frame in which a corridor can
be measured against a known-size object. A frame showing a corridor of visibly different
section would narrow the claim to the sectors it covers rather than overturn it.

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
