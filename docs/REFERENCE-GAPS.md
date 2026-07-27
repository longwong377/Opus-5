# Reference gaps — what to send, ranked by what it unblocks

The owner is hands-off until ship and has offered to supply more reference. This document is the
only channel for asking, so a vague ask wastes it. Every entry states what is missing in terms
specific enough to *search for*, what it unblocks, what we are doing instead, and how much would
be enough.

Counts verified against the folders on 2026-07-27, not assumed.

**The honest summary:** the exterior is well covered and the drum interior is covered by four
excellent frames. Everything a player would spend most of their time *inside* is not.

---

## 1. Generic interior corridors — **0 files**

`reference/10-interiors-generic-kit/` is **empty**.

**Why this is first.** The corridor kit is 210 decks and 2,330 streaming cells — the large
majority of the walkable station. It is the single most-seen surface in the finished simulation
and it currently has **no reference at all**. Every dimension in `station/interior_kit.py` —
corridor width 2.6 m, ceiling height, door width 1.50 m, pilaster spacing, the deck grid — was
extrapolated from proportions in `grey level 1.webp`, which is one frame of one sector.

**What to send:** straight corridor shots showing the full cross-section — floor to ceiling, wall
to wall — with a person in frame for scale. Ideally several, in different sectors, including a
junction and a corridor with doors along it. Corridor lighting is as important as the geometry:
where the fittings are, what they light, how much of the wall is in shadow.

**Enough:** six to ten frames. Two with a person standing against a wall would settle the width
and ceiling height on their own.

**Cost of not having it:** the most-seen surface in the game is built from a single frame's
proportions, and if the width is wrong every one of the 2,330 cells is wrong with it.

---

## 2. Level numbering — **C-004, OPEN and BLOCKING**

`reference/16-signage-typography-ui/` holds **three files, and all three are logos** (Babylon 5
shield, Earthforce logo, faction symbols). There is no signage reference in the project.

**What to send:** anything that ties a level number to a place —

- a **lift car interior** showing the level indicator or button panel;
- a corridor **wall sign** giving a level or section designation;
- a **deck plan with numbers on it** (the deck plans we have number nothing);
- or dialogue naming a level alongside something placeable ("Grey 17" alone does not do it — we
  need to know which *ring* level 17 is, counting from where).

**What it unblocks:** the human name of every one of the **210 decks**. Geometry is generated
against `(sector, ring_index)` and labelled afterwards by `bind_labels()`, so building is not
blocked — but nothing in the station can be correctly *signposted* until this closes, and signage
is everywhere in a real interior.

**Enough:** one lift panel. One legible corridor sign would also do it.

---

## 3. Starfury cockpit — **0 interior files**

`reference/12-starfury/` has four files, all **exterior** views.

**What to send:** the cockpit from the pilot's seat — instrument panel, canopy framing, the
control grips, and the pilot's view out. The Starfury's cockpit is distinctive (the pilot flies
standing/prone rather than seated, which changes everything about the layout) and getting that
wrong would be immediately visible.

**What it unblocks:** *"you will be able to fly around the station on a Starfury (cockpit and
Starfury view)"* — from the opening brief. The flight model is built and tested (18 assertions);
the airframe is built (31 assertions). The cockpit cannot be started.

**Enough:** two or three frames from inside, plus one over-the-shoulder showing how the pilot is
positioned relative to the canopy.

---

## 4. Audio — **0 files**

`reference/18-audio-notes/` and `reference/19-video-clips/` are both **empty**.

**What to send:** video clips rather than stills — anything with the station's ambient bed
audible. Specifically useful: a busy Zocalo, a quiet corridor at night, the docking bay during an
operation, the Garden, and a Starfury launch.

**What it unblocks:** ambience was an explicit requirement in the opening brief and **no audio
work exists at all**. It is also the cheapest large gain in "mood" available — a room with the
right hum feels twice as real.

**Enough:** four or five clips of ten seconds each. What matters is the ambient bed, not dialogue.

---

## 5. Crowds and civilian clothing

`reference/14-characters-and-uniforms/` has 12 files and `15-races-and-makeup/` has 12, which is
good coverage of **named characters, mostly in uniform**. What is missing is everybody else.

**What to send:**

- **Wide shots of the Zocalo or a busy corridor** where crowd *density* can be counted — how many
  people per square metre, how they distribute, how much of the crowd is non-human.
- **The same locations when empty or near-empty**, at a quiet hour.
- **Civilian and worker clothing** — traders, dockworkers, Downbelow residents. We have uniforms;
  we have very little of what an ordinary resident wears.

**What it unblocks:** the owner named *"crowdedness/isolation"* as an AAA dimension in its own
right. The NPC system has names, species, roles and schedules for 250,000 residents
(`station/npc/`), and no basis whatever for how full a given space looks at a given hour. That is
currently pure invention and it is the kind of invention a viewer notices instantly.

**Enough:** three or four wide crowd shots with countable people, three or four matching quiet
shots, and half a dozen civilian costume references.

---

## 6. Grey, Brown and Yellow sector interiors

| folder | files |
|---|---|
| `07-sector-grey` | **1** (`grey level 1.webp`) |
| `06-sector-brown-downbelow` | **0** |
| `08-sector-yellow-engineering` | **0** |

**Why this matters more than it looks.** Grey is **90 of the station's 210 decks** — more than
half the interior — because it sits at the widest part of the hull. It has one reference frame.
Brown is Downbelow, which is a *character* in the show as much as a place, and we have nothing.

**What to send:** any interior shot in these sectors. For Downbelow specifically, what makes it
read as Downbelow — the improvised shelters, the lighting, how the space differs from a
maintained corridor.

**Enough:** three or four frames each would take these from "invented" to "grounded".

---

## 7. Sector naming — **C-003, OPEN and BLOCKING**

Two authority-3 sheets disagree about which longitudinal band is the habitat drum (the
Green/Brown transposition).

**What to send:** any source placing **the Garden or Downbelow in a named sector at a
longitudinal position** — a labelled cutaway, a plan with sector names against hull positions, or
dialogue that ties a sector name to a place we can locate.

**What it unblocks:** the same labelling as C-004. `drum_sector()` identifies the drum by
*geometry* precisely so that building proceeds without this — but the sector names on 8 km of
station are guesses until it closes.

**Enough:** one labelled diagram.

---

## 8. Tram car length — two authority-1 frames disagree by 3–4×

Not a missing reference; a **contradiction between two we already have**, and it needs a third to
break the tie.

- `Babylon_5_2-22_34b.jpg`, rectified against the truss bays, gives a car of **3.9 bays ≈ 96 m**.
- `Babylon_5_2-22_33a.jpg` shows a **whole car** in three-quarter view with about five window
  bays and a length-to-height ratio near **1.8:1**, against the built model's 21 window bays and
  ~9:1 — i.e. **three to four times shorter**.

**What to send:** any other shot of a drum tram, especially one with people boarding or standing
beside it, which would settle the length against a known height immediately.

**Enough:** one frame with a person next to a car.

---

## What we do *not* need

Worth saying, so the ask stays credible:

- **Exterior hull.** Well covered. `01-station-exterior/` plus the orthographic production sheets
  and the Miller cutaway have carried the entire exterior build.
- **The drum interior's large-scale form.** `Babylon_5_2-22_33a / 34b / 35a` and `29a` are
  excellent and have carried the ground, the end caps, the guideway trusses and the tram interior.
- **Named characters and alien makeup.** 24 files across the two folders is enough for the species
  we need to build.
- **Props.** `11-props-and-technology/` has 14 files including identicards, PPGs and readers —
  enough for the interaction layer when it comes.
