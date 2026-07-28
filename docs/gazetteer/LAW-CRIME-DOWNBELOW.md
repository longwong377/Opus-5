# LAW, CRIME AND DOWNBELOW — order, disorder, and the underclass

The station's other half. `LOCATIONS.md` says where the Zócalo is; this file says who moves you
on from it, where you sleep if you cannot afford a room, and what happens between the two.

**Era datum: S3, pre-martial-law — early 2260, between S3E02 (*Convictions*) and S3E09 (*Point
of No Return*).** Adopted unchanged from `docs/gazetteer/FACTIONS.md` §1.3 so the two files
cannot drift. Sheridan commanding, Garibaldi chief of security, Nightwatch present and openly
armbanded, Narn refugees arriving, pre-secession, Earth Alliance law and customs intact.

---

## 0. How to read this file

### 0.1 Authority, and the dagger

Project scale (`reference/README.md`, `canon/00-MASTER.md`):

| | |
|---|---|
| **1** | on-screen footage |
| **2** | production material |
| **3** | licensed print (Contract 5, the two Security Manual sheets) |
| **4** | fan reconstruction — wikis, fan sites, forums |
| **5** | our own extrapolation, with the reasoning given |

**The dagger (†)** is used exactly as `FACTIONS.md` defines it: the ultimate source is on-screen,
but **no frame was viewed during the session that wrote this file** — the claim reaches us
through a web summary. A † row is authority 1 *about the show* and authority 4 *as evidence in
this repository*. It may never outrank a file under `reference/`. Rows citing a `reference/`
path carry no dagger; those were read.

> **Method caveat, stated once, applying to every authority-4 row.** `WebFetch` returned **HTTP
> 403 for every host tried** — `babylon5.fandom.com`, `wikimili.com`, `oocities.org`,
> `babylon-5.org.uk`. This is the same block `LOCATIONS.md` §0.1 records. **No web page was
> read.** Every authority-4 citation below is a *search-engine summary* of the cited URL. A
> summary can drop a qualifier, merge two facts, or attach a claim to the wrong episode, and at
> least one row below (§3, "Blue 5") is visibly ambiguous for exactly that reason. Re-verify
> when fetching works.

**One trap found and avoided, recorded so nobody else falls in it.** A search for the station's
legal status returned a confident description of a "Babylon Treaty ... founded in 2520 ...
between the belligerent **United Systems Federation** and Minbari Federation", with Earth's
sovereignty "limited by the Babylon Treaty". That is from
[horizonsbeyond.fandom.com](https://horizonsbeyond.fandom.com/wiki/Babylon_Treaty_Organization),
**a fan-fiction wiki**, and none of it is Babylon 5. It ranked alongside the real wiki in the
same result set. **Search summaries blend sources; check the host on every claim.**

### 0.2 Placement, and what this file will not do

Same vocabulary as `LOCATIONS.md` §0.2–0.3: **STATED / IMPLIED / PROPOSED**, and sectors are
longitudinal bands while rings are concentric radial zones. **C-003** and **C-004** are OPEN and
BLOCKING, so nothing here asserts a level number of our own. Where an authority-4 source gives
one (`Blue 5`, `Grey 17`) it is recorded **as that source's claim, in its own words**, and §1.7
shows what it would mean under each reading of C-004.

Proposals in this file are tagged **D-01 … D-12** and reasoned in §12. `LOCATIONS.md` uses
`P-nn`; the prefixes are deliberately different so the two sets never collide.

### 0.3 Relationship to the other gazetteer files

| | |
|---|---|
| `FACTIONS.md` | **owns** the force size (500), the Nightwatch layer, the population split, and the friction table. This file does not restate them; it uses them and cites the section. |
| `LOCATIONS.md` | **owns** Security Central, the Law Courts, Downbelow-as-a-place and the Happy Daze Bar as *rows*. This file takes each one and makes it buildable. |
| **This file** | owns the **behaviour**: patrol, response, detention, adjudication, the informal economy, and the security/Downbelow relationship. |

---

## 1. CONTRADICTIONS AND FINDINGS

Reported first because they are the most valuable output. **None is fixed here** — `canon/`,
`station/` and other agents' documents are not this agent's to edit.

### 1.1 The sector Downbelow lives in does not exist in the station schema

`canon/00-MASTER.md` §3: *"Six sectors: **Blue, Red, Green, Brown, Grey, Yellow**."*

`station/schema/station.yaml` line 118: `order_aft_to_fore: [yellow, grey, green, red, blue]`,
and `extents_m` carries **five** keys. Verified by running the model:

```
$ python3 -c "... print(list(schema['sectors']['extents_m'].keys()))"
['yellow', 'grey', 'green', 'red', 'blue']
```

`cell_manifest()` therefore enumerates 210 decks and 2,330 cells across five sectors and **zero
of them are Brown**. The one place any authority-3 source names DOWNBELOW — the Brown rosette in
`other map.png` — is a sector the geometry does not contain.

This is not an oversight: it is `INV-009` ("Brown as a radial designation") applied correctly.
The Security Manual sectional schematic brackets only five sectors, Brown is absent from it, and
"Down-Below" appears there as a label on an **outer band**, so the project reads Brown as *the
outermost ring, station-wide* rather than a length of station. **The finding is that the
consequence has never been written down**: under INV-009, "Brown Sector" is a synonym for
"outermost ring", Downbelow is distributed the whole 8 km, and there is no single Brown volume to
build. Everything downstream — signage, NPC addresses, `schedule.py`'s `"downbelow"` workplace
string — currently has nowhere to resolve to.

### 1.2 INV-009's stated overturn condition has been met — at authority 4

`canon/INVENTIONS.md` INV-009 (Brown), *Overturned by:* **"any source bracketing Brown as a
length of station, or dialogue placing Brown fore or aft of a named sector."**

> "Brown sector houses the industrial work that support the life support and waste reclamation
> facilities. It is **located at the rear of the station's rotating section, aft of Green Sector
> and fore of Grey Sector**."
> — authority 4, https://babylon5.fandom.com/wiki/Brown_Sector

That is a longitudinal placement, fore-and-aft of two named sectors, in the exact form INV-009
names. **It does not overturn INV-009**, because authority 4 cannot outrank two authority-3
sheets, and it is very likely an echo of the same print sources (the identical objection
`LOCATIONS.md` X-3 raises). But INV-009's overturn clause is now *satisfied in form and failing
only on authority*, which is a materially different state from "no such source exists", and the
invention log should say so. It also corroborates `LOCATIONS.md` X-3's ordering a second time,
from a second page.

### 1.3 Two invention numbers are each used twice

`canon/INVENTIONS.md` has **INV-009 at line 259** (Aurora-class Starfury airframe dimensions)
and **INV-009 again at line 436** (Brown as a radial designation); **INV-010 at line 320**
(station material palette) and **INV-010 again at line 455** (deck pitch of 3.6 m). Confirmed by
`grep -n "^## INV-"`. Four documents already cite these numbers, and two of them mean different
things by the same tag: `LOCATIONS.md` §11 cites "INV-009" for the Brown reading, while
`STATE.md` and `station/starfury_geometry.py` mean the airframe. A clean renumber is cheap now
and will not be later.

### 1.4 The station has an order of magnitude more deck area than it has people

Computed from `station/interior.py::cell_manifest()`, summing 2πr × sector length over every
deck record:

| | floor area | per capita at 250,000 |
|---|---|---|
| all five sectors, all rings | **197.7 million m²** | 790 m² |
| pressurised sectors only (Grey, Green sub-floor, Red, Blue) | **146.2 million m²** | **585 m²** |

A dense human habitat runs **30–60 m² per person** across *all* uses — housing, workplace,
circulation, plant, retail. At 60 m² the station's people need ~15 million m², which is **10% of
the pressurised deck area the model generates.**

Read that as a defect and it is one. Read it as the answer to the question this file exists to
answer and it is the strongest thing in the document:

> **Unfinished is the default state of a Babylon 5 deck. Fitted-out is the exception.**

That is exactly what canon says Downbelow physically is — *"the various undeveloped areas ...
they were reduced to squatting and living in the abandoned corridors of those **unfinished
levels***" (authority 4, https://babylon5.fandom.com/wiki/Lurker) — and the project's own
geometry independently demands it. **Nothing was authored to make this true.** It is the same
class of result as session 2v's "Downbelow is heavier than the Garden".

Build consequence, and it is large: the interior kit needs an **unfinished variant** — sealed
bulkhead, capped service stub, primer-grey unclad rib, no deck tile, no dado, no light strip —
and it needs it *before* the finished variant is dressed, because the unfinished one covers
~90% of the station's decks. See §5.1.

### 1.5 An authority-4 source places prisoner holding in Blue, against `LOCATIONS.md` P-04

`LOCATIONS.md` §8 lists the brig as **unplaced** and P-04 proposes **Red, adjacent to Security
Central**. Against that:

> "When Kiron Maray and Aria Tensus were taken into custody in April 2258 after using stolen
> credit chits ... they were **held in Blue 5** to await the Centauri representative."
> — authority 4 †, https://babylon5.fandom.com/wiki/Blue_Sector

**This is weaker than it looks and the weakness is instructive.** The same summary's second
example — Sinclair "tried moving [Jha'dur] **through** Blue 5 to avoid attracting attention" —
uses Blue 5 as a *route*, not a cell. One summary, two sentences, two different senses of the
same address. This is precisely the failure mode §0.1 warns about, and it is why the row is not
being used to close anything. Recorded because P-04's reasoning ("a brig that is not walkable
from Security Central generates prisoner transport every scene") is sound and this is the only
counter-evidence in existence. **See D-01 for a reading that satisfies both.**

### 1.6 The era of the good Downbelow material is S1, not S2–3

The four richest Downbelow sources found are **"Grail" (S1E15)**, **"Survivors" (S1E11)**,
**"The Quality of Mercy" (S1E21)** and **"The Long Dark" (S2E05)**. Only the last is in era, and
`N'Grath` — the one named organised-crime figure — is an S1–S2 fixture whose S3 status is
unestablished (`FACTIONS.md` §11.4 already flags this).

The correct response is not to drop them. It is to separate **institution** from **character**:
the Ombuds bench, the debt-enforcement racket, the free clinic and the skilled-lurker archetype
are structural and persist; Deuce, Jinxo and N'Grath are people and may not. Every row below
that draws on an S1 episode is marked **ERA: institution in, character out**.

### 1.7 Two authority-4 "level 5" addresses land on the same ring — and not the one the code assumes

`station/interior.py` line 700: `LEVEL_NUMBERING = "outermost_is_1"   # C-004: UNCONFIRMED`.

| claim | authority | under `outermost_is_1` | under `innermost_is_1` |
|---|---|---|---|
| Zócalo is in **Red 5** (`LOCATIONS.md` X-5) | 4 | Red core, r = 38.1 m, 0.137 g | **Red ring 1, r = 211.8 m, 0.761 g** |
| Prisoners held in **Blue 5** (§1.5) | 4 † | Blue core, r = 30.2 m, 0.108 g | **Blue ring 1, r = 167.7 m, 0.603 g** |

Authority 3 puts the Zócalo in Red's **outermost** ring (`other map.png`). Under
`outermost_is_1` that is Red **1**, and the authority-4 "Red 5" is wrong by four rings. Under
`innermost_is_1` both authority-4 addresses land on ring 1, the outermost — consistent with the
rosette, and consistent with the third fan source's *"lower numbers are closer to the central
axis"* (`LOCATIONS.md` §1).

**This does not close C-004** — three authority-4 sources agreeing may be one source echoing
three times, and `LOCATIONS.md` §1 raises a fourth reading in which the number is a 10° angular
segment and neither column applies. It is recorded because the code currently carries the
setting these sources *disagree* with, and one line changes it.

---

## 2. STATION SECURITY

### 2.1 Command, at the datum

From `FACTIONS.md` §3.2, which owns this table; repeated in compressed form because a builder
placing a security NPC needs it here.

| Post | Holder | Rank | Station | Note |
|---|---|---|---|---|
| Chief of security | **Michael Garibaldi** | Chief Warrant Officer (4) | Security Central, Red inner ring | **Refuses all association with Nightwatch** (1 †) |
| Deputy / shift lead | **Zack Allan** | Sergeant, later Lieutenant (4) | Security Central and patrol | **Wears the Nightwatch armband at the datum** (auth 2, `reference/14-characters-and-uniforms/Zach Allan in security uniform.jpg`) |
| Line officer | **Lou Welch** | — | patrol | Aboard since the station opened, March 2256 (4 †, https://babylon5.fandom.com/wiki/Lou_Welch) |
| Above them | **Cdr Ivanova**, then **Capt. Sheridan** | Commander / Captain | C&C | Sheridan holds military-governor powers (`FACTIONS.md` §3.1) |

**Security is not EarthForce line.** Authority 4: *"Earthforce uniforms are colour coded
according to branch: **teal for fleet, grey for security, brown for marines**"*, and the grey
security uniform *"lacked the stylised 'EA' pin worn by members of Earthforce proper and had a
**'B5' shoulder patch** instead of an Earthforce division badge"*
(https://babylon5.fandom.com/wiki/Earthforce_Ranks_%26_Insignias, via search summary).
**This is independently corroborated in-repo at authority 2**: both
`Zach Allan in security uniform.jpg` and `security in uniform.jpg` show grey, not teal, and the
index records the crosshair-in-diamond **security** badge on both, not the EarthForce wings.
That agreement — a web claim and a held frame, arrived at separately — is the strongest
uniform row in this file.

### 2.2 Size and shape of the force

**Owned by `FACTIONS.md` §2.2 and not re-derived: 500 officers of the 6,500 EA complement,
≈150 on duty at any moment (authority 5).** No canon figure exists; searches for one returned
nothing (`FACTIONS.md` §15 records the same result). What this file adds is what 150 means once
it is spread over the geometry that now exists:

| | |
|---|---|
| streaming cells in the station | **2,330** (`cell_manifest()`) |
| cells in the outermost ring alone | **753** |
| officers on duty per cell, station-wide | **0.064** |
| officers on duty per outermost-ring cell | **0.20** |

**One officer per sixteen streaming cells.** A cell is 100–140 m of corridor arc by the full
length of its sector. So a uniform patrol is not merely thin, it is arithmetically impossible,
and the force must be a **garrison at chokepoints** — which is the conclusion `FACTIONS.md`
already reaches from the ratio, now confirmed against the built cell grid.

Watch structure (authority 5, derived from `station/npc/schedule.py`'s existing three-shift
rotation for `workplace == "patrol"`):

| Shift | EMT | On duty | Character |
|---|---|---|---|
| A | 00:00–08:00 | ~150 | Thin. The Zócalo is shut. Downbelow is at its most active |
| B | 08:00–16:00 | ~150 | Customs peak, cargo, the Zócalo opening |
| C | 16:00–24:00 | ~150 | **Heaviest real load** — bars, the Casino, station-evening crowds |

`schedule.py` already spreads security across three shifts with `shift_offset()`; INV-005 records
that resolving sleep before work once put the entire night watch to bed and showed **zero
security on duty at 02:00**. Do not undo that.

### 2.3 What an officer wears and carries

Everything in this table is from a file in `reference/` — no daggers.

| Item | Description | Auth | Source |
|---|---|---|---|
| **Service dress** | Medium grey twill jacket; **black (reading dark navy in the second frame) leather standing collar and yoke**; black leather epaulettes; two flapless breast pockets with horizontal welt seams; gold triangular pin at the throat | 2 | `reference/14-characters-and-uniforms/Zach Allan in security uniform.jpg` |
| **Duty rig** | The same grey jacket **with a black tactical vest over it**. **Two distinct silhouettes to model** — background officers in the second frame wear the vest, Zack does not | 1 | `reference/14-characters-and-uniforms/security in uniform.jpg` |
| **Security badge** | Right chest. Gold-outlined diamond with slightly convex sides on black, containing a gold circle crossed by **four tapered spokes** running toward the diamond's points, with a small gold-outlined square ring at the exact centre. Confirmed independently at 8× in **both** frames | 2 / 1 | both files above |
| **The link** | Left wrist, **back of the wrist**. Shield-shaped plate — flat top, straight sides, chamfered lower corners to a shallow point — polished white metal on a dark strap, face carrying a **dark inlaid glyph of nested angle brackets with bars and dots between them** | 2 | `Zach Allan in security uniform.jpg` at 8× |
| **Sidearm — EarthForce PPG** | **Polished nickel** body; plain **polished cylindrical emitter** entering the body through a **collar step ring**; slab side with **five parallel diagonal slots raked forward-and-up** and **four round studs** along the panel's lower edge; boxy rear receiver with a dorsal rail; **black rubber revolver-pattern grip** with finger grooves, stippled field and a **circular medallion boss**; thin curved blade trigger in a squared guard | 2 | `reference/11-props-and-technology/Earthforce issue Auricon PPG Pistol with removable sight.webp` at 8×. Only 304×231 — use `tools/refzoom.py` |
| **Detachable sight** | Long polished cylindrical tube; **ribbed top rail at the front** (five or six ribs); **large knurled circular turret** on top at mid-length; stepped rear collar. A tube-scope with a top turret | 2 | same file, inset at 10× |
| **Identicard reader** | Dark grey wedge on a pistol grip, portrait screen, **three amber indicator lenses** | 1 | `reference/11-props-and-technology/Identicard reader.webp` |
| **Nightwatch armband** (30–40% of officers) | Left forearm. Black band, gold embroidery: **stylised eye inside a swept almond/wing outline with a small triangle above the pupil**, over "NIGHT WATCH" in gold caps | 2 | `Zach Allan in security uniform.jpg` at 6–8× |
| **Do NOT model the PPG from** | `reference/14-characters-and-uniforms/Chief of security Garibaldi.webp` — S1 pattern, 322×480, heavily backlit, and the index explicitly records that the weapon **cannot be confidently identified as the standard PPG** | — | `reference/00-INDEX.md` |

**The civilian PPG is a different weapon and both exist aboard.** Two-tone at 5×: **pale
olive/khaki polymer frame, rear body and underside block** against a **dark blued-steel slide and
barrel**; cylindrical shroud with a large counterbored muzzle; long raised slide rib with a
bright polished top edge; a vertical pair of round-headed bolts on an olive block under the
barrel (authority 1, `reference/11-props-and-technology/civilian PPG.webp`). It matters legally:
see §2.7.

**What the PPG is, and why it is the station's weapon.** *"A small hand-held weapon which
ionises small quantities of hydrogen or helium gas, and suspends the resultant product in a
magnetic bottle, which is then released by a moving electric charge"* — authority 4,
http://www.midwinter.com/lurk/ftp/b5.tech.htm (*Unofficial B5 Technical Manual*). The
in-universe rationale for a plasma weapon rather than a slug-thrower is that **it will not
breach a pressure hull**. On a station that is one skin away from vacuum, that is the whole
argument, and it should govern how the weapon is *depicted*: bright, short-ranged, no ricochet,
scorch marks on bulkheads rather than holes.

### 2.4 Where security physically is

Ordered by how certain the placement is. Ring class, never a level number.

| Post | What it is | Placement | Confidence | Auth | Source |
|---|---|---|---|---|---|
| **Security Central** | Force HQ; *"the central hub for the numerous station houses located throughout the station"* — so the model is **HQ plus substations**, not one office | **Red, inner ring** | STATED | 3, corr. 4 | `other map.png` Red rosette; https://babylon5.fandom.com/wiki/Blue_Sector |
| **Station houses (substations)** | Named at authority 4 as plural and distributed. This is the single most useful security fact found: it means the force is **not** all in one room | one per pressurised sector, outer ring, at the main concourse | STATED (that they exist) / **PROPOSED (where) — D-02** | 4 | ibid. |
| **Customs posts (×2)** | Permanent, doubled, north and south. Contraband, identicards, visas | Blue, outer, with the customs halls | STATED | 1 (the halls), 3 (the count) | `reference/01-station-exterior/welcome to babylon 5.webp`; Security Manual |
| **Zócalo standing post** | The most-policed civilian space on the station | Red, outermost ring | **PROPOSED — D-03** | 5 | — |
| **Council / diplomatic approaches** | Access control to the ambassadorial zone | Green | **PROPOSED — D-03** | 5 | — |
| **Bay-elevator and docking checkpoints** | Where craft, crew and cargo enter the pressurised volume | Blue | **PROPOSED — D-03** | 5 | — |
| **Sector-boundary checkpoints** | `LOCATIONS.md` P-05 already proposes these. Blue access is *"mostly restricted to station personnel and official guests of the Earth Alliance"* (auth 4), and the Alien Sector is airlocked, so at least two controlled boundaries are canon-required | at sector boundaries and restricted-ring lift lobbies | PROPOSED (P-05) | 4 for the restriction | https://babylon5.fandom.com/wiki/Blue_Sector |
| **Grey Sector access control** | *"Grey Sector access was restricted to command, security and maintenance personnel"* | Grey, at the sector boundary | STATED | 4 † | https://babylon5.fandom.com/wiki/Grey_Sector |
| **Downbelow** | **No permanent post.** See §9 — this is a positive design decision, not a gap | — | — | 5 | — |

**The external sensor arrays can be turned inward.** In *Hunter, Prey* (S2E13, in era) the
station's *"massive external sensor arrays [are] recalibrated to scan the interior of the station
for energy emissions"* (authority 4 †,
https://reactormag.com/babylon-5-rewatch-hunter-prey/). This is the station's one
whole-volume search capability, it is slow and exceptional rather than routine, and it is a
superb scripted-event mechanic: a station-wide sweep the player can feel, announced over the
public address, that a hidden NPC must survive.

### 2.5 Patrol patterns

**Authority 5 throughout.** This is design, derived from the force size in §2.2 and the built
cell geometry, and it is written as rules an NPC director can execute.

| Rule | Value | Why |
|---|---|---|
| Patrol unit | **2 officers**, always | `FACTIONS.md` §12 makes the two-officer pair carry the Nightwatch split — one armband, one bare sleeve. A lone officer destroys that |
| Fixed posts | **~60 of the 150 on duty** | Two customs halls, Zócalo, Council approach, bay elevators, Grey boundary, Security Central watch |
| Roving patrols | **~35 pairs** across the four pressurised sectors | The remaining 90 |
| Patrol beat | **one outermost-ring deck arc, out and back** | Grey ring 1's circumference is **2,527 m**; a half-circuit at 1.3 m/s is **16 minutes**, so a there-and-back beat is ~32 min and a pair passes any given point about **twice per shift** |
| Beat frequency, by place | Zócalo **continuous**; Red/Blue outer **every 30 min**; Green residential **every 60 min**; Grey outer **every 3–4 h**; Downbelow **zero** | Follows from 35 pairs against 753 outer cells |
| Effect the player must feel | **Twenty minutes of walking in the outer ring with no uniform in sight, then four officers in one glance in the Zócalo** | `FACTIONS.md` §2.2 names this as the point; the numbers above are what produce it |
| Weight penalty | A 75 kg officer weighs **108 kgf in Grey ring 1**, 84 kgf in the drum sub-floor, **45 kgf in Blue ring 1** | `station/interior.py::sector_report`. Foot patrol in the heavy outer rings is genuinely punishing, and that is a reason the force does not do it |

### 2.6 Response — measured, not asserted

The one thing in this file that is *derived from the project's own physics* rather than
extrapolated. Computed with `station/physics/core_shuttle.py` at the standing comfort limit of
0.12 g lateral (`comfortable_duration`) and `AxialShuttle` at 1.2 m/s²:

| Leg | Time |
|---|---|
| Security Central (Red inner, r = 127.1 m) → axis | **43 s** |
| Axial run Red → Grey (3,000 m) | **100 s**, peak 60 m/s |
| Axis → Grey ring 1 (r = 402.2 m) | **158 s** |
| **Vehicle transit, door to door** | **300 s = 5.0 minutes** |
| Same to the drum sub-floor (Green, r = 310.8 m) | **238 s = 4.0 minutes** |

Add call-out, waiting for a car, and the walk at the far end — a Grey ring 1 cell is 140 m of arc
by 442 m of length, and half a deck circumference is another 16 minutes — and:

> **Realistic security response to the outer ring of a distant sector is 12–20 minutes.
> To the Zócalo, from the standing post already there, it is seconds.**

That single contrast is the law-and-order layer's entire dramatic geometry, and **it is not a
design choice.** It falls out of an 8 km station, a 402 m radius, and a Coriolis comfort limit
that was solved for in session 2h before anyone thought about policing.

### 2.7 Powers, weapons law, and the escalation ladder

| Rule | Detail | Auth | Source |
|---|---|---|---|
| **Civilians may not carry** | *"Civilians aren't 'supposed' to have weapons on the station and this is reasonably well enforced"*; security *"unlike the civilian population, are allowed to carry weaponry in the line of duty"* | 4 | http://www.midwinter.com/lurk/ftp/b5.tech.htm |
| **But a civilian PPG exists and is obtainable** | Officers stripped of military-issue sidearms are told to *"use civilian channels"* instead (*Conflicts of Interest*, S5 — **out of era for the plot, in era for the mechanism**) | 4 † | https://babylon5.fandom.com/wiki/Conflicts_of_Interest |
| **So the offence is carrying, not owning** | The in-repo two-tone civilian PPG (§2.3) is the physical evidence that a parallel civilian market exists | 5, from an authority-1 prop | `reference/11-props-and-technology/civilian PPG.webp` |
| **Identicard check is the routine power** | The reader is a held prop; `VISAS` and `LICENSED PSI` are fields on the record | 1 | `reference/11-props-and-technology/Identicard reader.webp`, `identicard readout.webp`; `00-MASTER.md` §1.4 |
| **Sheridan holds military-governor powers** | Which is what let him grant G'Kar sanctuary | 1 † | `FACTIONS.md` §3.1 |
| **Diplomatic immunity** | *"Each ambassador and his staff have diplomatic immunity, and the quarters of each ambassador are considered to be part of their world's territory"* | 4 | https://babylon5.fandom.com/wiki/Ombudsmen (via summary) |

**The escalation ladder (authority 5, design).** Each rung is a distinct NPC behaviour set:

1. **Presence.** A pair walks through. Conversation volume drops. Lurkers drift out of the space.
2. **Identicard check.** Reader out, three amber lenses, portrait on the screen. The commonest
   security interaction on the station and the one a player will see most.
3. **Move on.** No arrest, no record. The standard Downbelow-in-a-commercial-area outcome.
4. **Detention.** Restrained, walked to a station house, then to the brig.
5. **Weapons drawn.** PPGs out. Rare — bright, loud, and the corridor empties.
6. **Sector lockdown / sensor sweep.** Scripted event only (§2.4).
7. **Marine or Starfury support.** Off the corridor scale entirely.

### 2.8 Nightwatch inside the force

Owned by `FACTIONS.md` §5, which places 150–200 of the 500 in armbands at the datum. The only
thing added here is where it *bites* on this file's subject matter: Nightwatch reports on
**speech**, not crime, so it **does not increase the policing of Downbelow** and may reduce it —
an officer chasing sedition reports in the Zócalo is not walking a beat in the outer ring. The
two enforcement layers compete for the same 150 people.

---

## 3. THE BRIG

Almost nothing about detention is sourced. This section says so, then makes it buildable.

| Question | What is actually known | Auth |
|---|---|---|
| Does the station have a brig? | Yes — prisoners are taken into custody, held, tried and transferred throughout the series | 1 † |
| Where? | **Unplaced.** `LOCATIONS.md` §8 lists it as unplaced. One authority-4 summary says prisoners were *"held in Blue 5 to await the Centauri representative"*, and the same summary uses Blue 5 as a transit route in a second example — see §1.5 | 4 † |
| Capacity? | **No source. None found.** | — |
| How long are people held? | **No source states a limit.** What *is* attested is the shape of it: held *"to await the Centauri representative"*; Jha'dur held pending an ordered transfer *"back to Earth"*; Jinxo held pending an Ombuds hearing and then **released into a private citizen's custody** by the judge | 4 † |
| Sentences served aboard? | **No.** Every attested disposal is a hearing, a fine, a release, a mind-wipe, or a transfer off-station. Nothing suggests B5 runs a prison | 5, from the absence |

### 3.1 What follows, and it is enough to build

**The brig is a remand facility, not a prison.** That single reading explains every attested use
and it sizes the room. Consequences:

| Property | Value | Reasoning (authority 5) |
|---|---|---|
| **Function** | Hold pending hearing, pending a consular representative, or pending an outbound transfer | All three attested uses, §3 |
| **Typical hold** | **Hours to a few days** | An Ombuds hearing is a same-week event; a consular collection is one ship cycle; `FACTIONS.md` §2.3 gives **52 departures per station-day**, so an outbound berth is never more than hours away |
| **Longest hold** | **Weeks**, for a transfer to Earth awaiting a specific escort, or a jurisdiction dispute (§4.3) that nobody will resolve | The Jha'dur case |
| **Capacity** | **24–40 individual cells plus 2 group holds** | ~250,000 people; a real remand population runs ~50–150 per 100,000, but almost all B5 offending is dealt with by "move on" (§2.7 rung 3) and most serious offenders are transferred out fast. 24–40 keeps it credible and keeps it a *room* rather than a wing |
| **Cell variety — this is the interesting part** | **At least three atmospheres.** Six standing atmospheres are canon (`00-MASTER.md` §1.4); humans are `02`. A station that arrests methane-breathers needs sealed cells with their own supply, and N'Grath's species *"breathes a combination of gases that are apparently toxic to humans"* (auth 4) | The atmosphere system already exists as canon; detention is where it becomes a *mechanic* |
| **Fittings** | Force-field or barred front (unestablished — see §13), a bench, no fixtures a prisoner can remove, a single ceiling luminaire, an identicard reader outside every door, and a **camera** | 5 |
| **Where** | **PROPOSED — D-01** | §12 |

---

## 4. LAW

### 4.1 Whose law

| Fact | Detail | Auth | Source |
|---|---|---|---|
| Sovereign | **Earth Alliance.** The station is EA territory at the datum, pre-secession | 1 †, 4 | `FACTIONS.md` §3.1 |
| Applicable law | **Earth Alliance law**, administered by Ombudsmen who are *"Earth Alliance judges appointed by the higher courts and ... responsible for the districts under their jurisdiction"* | 4 | https://babylon5.fandom.com/wiki/Ombudsmen |
| Neutral ground | The station is a diplomatic forum on neutral territory *for the purpose of diplomacy*. **It is not extraterritorial.** Do not confuse the two | 4 | ibid., and see the fan-fiction trap in §0.1 |
| Ambassadorial territory | Ambassadors and their staff hold **diplomatic immunity**, and **an ambassador's quarters are treated as their world's territory** | 4 | ibid. |
| The commander's reserve power | Sheridan holds **military-governor** powers and can override the civil process — the mechanism by which G'Kar was granted sanctuary | 1 † | `FACTIONS.md` §3.1 |
| **Babylon Treaty — OUT OF ERA** | Signed **July 2260**, between the *already-independent* station and the League. **After the datum and after secession.** It must not appear | 4 | https://babylon5.fandom.com/wiki/Babylon_Treaty |

### 4.2 The court

| Element | Detail | Auth | Source |
|---|---|---|---|
| **The bench** | **Ombudsmen** (singular "Ombuds"). **At least two aboard**: Wellington and Zimmerman | 4, on screen from S1E15 (1 †) | https://babylon5.fandom.com/wiki/Ombudsmen, /Wellington |
| **Jurisdiction** | Both **civil suits and criminal trials** | 4 | ibid. |
| **The recurring problem** | *"Many of the cases had to be **deferred as conflicts of jurisdiction came up between the humans and aliens**"* | 4 | ibid. |
| **Appeal chain** | Ombuds → **appeals courts** → **Final Appeal** → in serious cases a **Senate Appeal Board** | 4 | ibid. |
| **Sentencing power** | *"Fully authorised to hand down any sentence permitted by Earth Alliance law, including **death of personality** and even **capital punishment in the form of spacing** for mutiny or treason"* | 4 † | ibid. |
| **Where** | **Law Courts / the Judiciary, Red inner ring** | 3, corr. 4 | `other map.png` Red rosette; `LOCATIONS.md` §8 |

**A worked case, and it is the model for the whole system** (*The Quality of Mercy*, S1E21 —
**ERA: institution in, character out**). Karl Mueller is tried by an Ombuds and *"sentenced to
death of personality, sentence to be carried out as soon as a **telepath could be secured** to
perform the **initial and terminal scans**, as well as the **mindwipe machinery** checked out by
**Medlab** personnel"* (authority 4 †, https://babylon5.fandom.com/wiki/Ombudsmen). Read what
that requires physically:

- a **telepath** must be present or brought — so a capital case is gated on Psi Corps
  availability, which is an *event*, not a routine;
- **mindwipe machinery** exists aboard and is certified by **Medlab**, so it lives in or beside
  Medlab, not in the courtroom;
- there are **two scans**, before and after — the personality is read out, then written over.

**Death of personality is Earth's substitute for execution**, described as *"more humane than the
death penalty"*: the convict is mind-wiped and *"a new personality determined to serve society"*
is implanted (authority 4 †, https://reactormag.com/babylon-5-rewatch-passing-through-gethsemane/,
of *Passing Through Gethsemane*, **S3E04 — squarely in era**). The same episode establishes that
a wiped convict may be living aboard **under the new identity, working, and not knowing** —
which is the single best NPC hook in the entire law layer and costs no geometry at all.

### 4.3 What happens in a serious crime — the pipeline, end to end

Authority 5 as a *sequence*; every stage is individually sourced above. This is the state machine.

| # | Stage | Where | Notes |
|---|---|---|---|
| 1 | Report or observation | anywhere | 90% of it originates in Downbelow (§8) and most of it is never reported at all |
| 2 | Response | §2.6 | 12–20 min to the outer ring; seconds in the Zócalo |
| 3 | Detention | station house → brig | §3 |
| 4 | **Jurisdiction check** | Security Central | **The station's characteristic legal event.** Human ↔ human: straightforward. Human ↔ alien: *"frequently deferred"*. Ambassador or staff: **immunity, and the file dies** |
| 5 | Ombuds hearing | Law Courts, Red inner | Days, not months |
| 6 | Disposal | | Fine · release · release into custody (the Jinxo precedent) · **transfer off-station** · **death of personality** · **spacing**, for mutiny or treason only |
| 7 | Where the sentence is served | **not aboard** | §3 |

**Two era notes a builder must honour.** (a) The datum is *after* the Ministry of Peace has
introduced *"relaxed standards of evidence"* and made *"past associations admissible"*
(`FACTIONS.md` §3.1, auth 4) — so the court is procedurally correct and substantively
compromised, and that is a **tone**, not a mechanic. (b) A Nightwatch denunciation for
**sedition** does not enter this pipeline at step 4 in the ordinary way; the depicted outcome in
*The Fall of Night* is a shopkeeper *"physically dragged away and imprisoned"* (`FACTIONS.md`
§5.1). **The parallel process is the point.**

---

## 5. DOWNBELOW — THE PLACE

### 5.1 What it physically is

The most important sourced sentence in this file, and it reframes everything:

> "[Brown Sector] was **originally intended to be a secondary commercial area like Red Sector,
> but went unfinished in the rush to complete construction**."
> — authority 4, https://babylon5.fandom.com/wiki/Brown_Sector

Downbelow is therefore **not** a purpose-built slum, a maintenance crawlspace, or a machine deck.
It is **an unbuilt shopping district.** Concourses at Zócalo scale with no shops in them.
Corridors with the structure done and the fit-out missing. Service risers capped and labelled and
never connected. That is why the only Downbelow-class frame in the reference set —
`reference/01-station-exterior/sleeping-in-light-05.jpg` — reads as *a wide commercial-industrial
street with a neon shopfront in it*: because that is exactly what it is.

The corroborating description says the same from the other end:

> "The various **undeveloped** areas ... mostly in the **lower levels, near the outer hull**,
> around the **waste recycling system, the air compressors and the water reclamation facility**"
> ... squatters *"scrounging through the **refuse of the hurried construction process** for
> anything they could eat, wear or sell."*
> — authority 4, https://babylon5.fandom.com/wiki/Downbelow, /Lurker

**The build consequence is a kit, and it is a big one.** `station/interior_kit.py` currently
builds one finished corridor. Downbelow needs an **unfinished variant of the same kit** —
identical structure, subtracted dressing:

| Finished (built, INV-007) | Unfinished (needed) |
|---|---|
| projecting skirt, set-back dado, hip rail band | **absent** — bare rib and plate |
| courses of large plates with recessed seams | **primer-grey unclad frame**, plates on pallets or missing |
| bullnose pilasters with segmented vertical light strips | pilaster **structure only**, light channel empty or a bare tube |
| warm downlights low on the wall | **temporary festoon**, clip lamps, work lights on stands |
| fine deck tile grid | **bare deck plate**, no tile; the illuminated centre strip present but **checkerboarded live/dead** |
| soffit | **none** — open girder truss, pipes and cable runs overhead |
| finished portal frames with doors | **capped openings**, sheeted-over apertures, **welded-shut doors** |

Every one of those "unfinished" cells is authority-1 supported by
`sleeping-in-light-05.jpg`, whose extracted architecture is *exactly* this list (overhead
**repeating portal truss** of paired chords with diagonal webbing, five frames countable, **no
ceiling plane at all**; **vertical white light bars** on wall pilasters; **illuminated centre
grating strip lit in a checkerboard of live and dead cells**; deck in three courses of large
recessed panels in running bond). **ERA CAVEAT, and it is important:** that frame is S5 with the
station derelict. **The set architecture is in era; the debris, the darkness and the dead panels
are the finale state, not normal operation.** In S2–3 Downbelow is *unfinished*, not *ruined* —
dim, not black; occupied, not abandoned; grubby, not smashed.

The `welded shut` detail is separately sourced and is a gift to level design: sealed doors with a
canon reason (`LOCATIONS.md` §11, and https://babylon5.fandom.com/wiki/Brown_Sector).

### 5.2 Where it is — both readings, with numbers

C-003 is open. Both readings are given because Downbelow is buildable under either, and the
*character* of the space differs between them.

**Reading A — INV-009: Brown is the outermost ring, station-wide.** The project's current
working reading, and what the geometry implements (§1.1).

| Sector | outermost ring | floor r | gravity | decks | cells | floor area |
|---|---|---|---|---|---|---|
| **Grey** | ring 1 | **402.2 m** | **1.445 g** | 20 | 343 | 20.4 M m² |
| Green (drum) | sub-floor | **310.8 m** | **1.117 g** | 9 | 138 | 43.3 M m² |
| Blue | ring 1 | 167.7 m | 0.603 g | 8 | 88 | 9.8 M m² |
| Red | ring 1 | 211.8 m | 0.761 g | 10 | 124 | 4.5 M m² |
| Yellow | ring 1 | 137.1 m | 0.492 g | 6 | 60 | 16.4 M m² (mostly non-pressurised spine) |
| | | | | | **753 cells** | **94.5 M m²** |

**Reading B — the sixth band: Brown is a length of station.** Under the Security Manual bracket
the unlabelled sixth band spans **z ≈ 3,997–6,037 m** (`CONFLICTS.md` C-003 UPDATE 2), i.e.
**2,040 m carved out of what `station.yaml` currently calls Green** — which is the drum. Under
this reading Downbelow is **the drum's sub-floor stack**: 9 decks, 278.3 → 310.8 m, 1.013 →
1.117 g, 138 cells, 43.3 million m².

**One piece of authority-1 evidence discriminates between them, and it favours the drum.**
In *The Long Dark* (**S2E05, in era**) the lurker Amis *"looks out a **porthole** and sees an
ancient ship approaching the station"* (authority 4 † of authority-1 footage,
https://tvtropes.org/pmwiki/pmwiki.php/Recap/Babylon5S02E05TheLongDark). A rewatch of the same
episode observes: *"seems that slums are **wrapped around the outermost floors of the cylinder**,
making it as far down as you can get"* (authority 4,
https://reactormag.com/babylon-5-rewatch-the-long-dark/).

**Downbelow has windows onto space.** Check that against the geometry:

| Ring | floor r | hull envelope at that z | structure outboard |
|---|---|---|---|
| **Green / drum sub-floor** | **310.8 m** | **316.8 m** (`HULL_SKIN_M` = 6.0, INV-013) | **6 m — the pressure hull itself** |
| Grey ring 1 | 402.2 m | ~467.7 m (`HULL_ALLOWANCE` 0.86) | **65 m** |
| Blue ring 1 | 167.7 m | ~195.0 m | 27 m |
| Red ring 1 | 211.8 m | ~246.3 m | 34 m |

**The drum sub-floor is the only habitable deck in the entire model that sits directly against
the pressure hull.** Everywhere else a porthole needs a 27–65 m light well through structure.
So if Downbelow has portholes — and one in-era episode says it does — Downbelow is the drum
sub-floor, and the drum sector is Brown.

**This does not close C-003 and must not be recorded as if it did.** The chain has three weak
links: the porthole reaches us at authority 4; `HULL_ALLOWANCE` is a *fraction* standing in for a
hull skin and `STATE.md` already lists making it metric as outstanding work (its symptom is
Grey's implausible 1.445 g); and a station can put a viewport at the end of a light well if it
wants to. It is logged as **a new pointer for C-003, of a kind C-003 is short of** — an
*observational* discriminator rather than another reading of a draughtsman's intent.

**And there is a real payoff either way.** The drum sub-floor is **1.117 g**, and the Garden
directly inboard of it is **1.000 g**. Session 2v's finding — *Downbelow is heavier than the
Garden* — is not a curiosity: it means a lurker sleeping against the hull is, at that moment,
lying **thirty-two metres and one deck** below a wheat field, weighing 12% more than the people
walking on it. Nothing was authored to make that true.

### 5.3 The arithmetic of emptiness — how much of it is occupied

This is the number that turns "there are lurkers in Downbelow" into geometry.

| | |
|---|---|
| Downbelow population (`FACTIONS.md` §2.2, auth 5, bracketed by an auth-4 forum estimate of ~13,000 and a ~50,000 upper reading) | **~20,000**, of which ~13,500 human |
| Squatted floor area at 25 m²/person (a squat is a sleeping pitch plus shared circulation, not an apartment) | **500,000 m²** |
| As a share of the outermost ring (94.5 M m²) | **0.53%** |
| At 10 m²/person (packed) / 50 m²/person (spread) | 0.21% / 1.06% |
| Expressed in streaming cells, at Grey ring 1's cell size of **62,050 m²** | **≈ 8 cells** |
| Out of the outermost ring's | **753 cells** |
| Lurkers per occupied cell | **≈ 2,500** |

> **Downbelow is about eight occupied cells inside seven hundred and fifty empty ones.**

That is the whole tonal instruction for the sector, and it is arithmetic, not taste. Two
consequences:

- **The occupied pockets are dense.** 2,500 people in a 140 m × 442 m cell is a crowd — bodies
  against every wall, no privacy, constant noise. It should feel like a refugee camp indoors, not
  like a few figures in shadow.
- **Everything around them is enormous and empty.** Walk five minutes off a camp in any direction
  and there is no one, and the lighting is whatever still works. **The isolation the owner asked
  for lives here**, and it is the same sector as the crowding.

**Where the pockets are (authority 4 for the rule, 5 for the placement — D-04).** The rule is
sourced: they cluster *"around the waste recycling system, the **air compressors** and the water
reclamation facility"*. That is a **thermal and utility** rule, not an aesthetic one — compressors
are warm, plant rooms are lit and powered around the clock, and a water plant is water. So:

| Anchor | Placed at authority 3 by | Result |
|---|---|---|
| **Waste Management Systems ("Down-Below")** | Red, Green and Brown rosettes **plus twice on the sectional schematic** — a *distributed* system, one per sector | **One camp per pressurised sector.** Four camps, not one Downbelow |
| **Waste Management Control** | Brown rosette | The largest camp is next to this |
| **Water reclamation** | outer hull, with waste (auth 4) | |
| **Air compressors** | outer hull (auth 4) | |
| **Happy Daze Bar** | named beside DOWNBELOW on the Brown rosette | The camp has a pub. Put it at the camp's edge |

### 5.4 Light, sound, temperature — the sensory brief

Authority 5 except where marked; assembled from the held frame and the physics.

| Channel | Downbelow | Contrast with |
|---|---|---|
| **Light** | Practical-only. The **illuminated deck centre strip in a live/dead checkerboard** is the primary source and it organises the whole perspective (auth 1, `sleeping-in-light-05.jpg`). **Vertical white light bars** on wall pilasters, four on one wall and two on the other — asymmetric, because half were never commissioned. Elsewhere: clip lamps, festoon, the glow off an equipment bank's **blue backlit displays** | The Zócalo's warm fairy-lit stalls and even downlight pools |
| **Colour** | Cold — the deck strip and the wall bars are white/blue; the only warm light is a **green-yellow neon shopfront in alien script** and whatever people have rigged (auth 1, same frame) | Red Sector's warm amber |
| **Overhead** | **No ceiling.** Repeating portal truss of paired chords with diagonal webbing, pipes and cable runs passing over the top chord (auth 1) | The finished soffit of `grey level 1.webp` |
| **Sound** | The plant. Compressors, pumps, fans, the waste system — **continuous low-frequency machine noise**, because the camps are sited on that machinery by definition. Human sound on top: coughing, a child, an argument, a radio | Corridor quiet elsewhere |
| **Temperature cue** | Warm at the compressors, cold away from them. This is *why* people are where they are, and it should be legible as steam, condensation, and people sleeping in specific spots | — |
| **Gravity** | 1.117 g (drum) or 1.445 g (Grey). Everyone moves a little more heavily. **A 75 kg person weighs 108 kgf in Grey ring 1** | Blue's 0.603 g, where the officers live |
| **Smell** | Not modellable, but it drives dressing: this is the waste plant. Ventilation grilles, drip staining, sealed drums | — |

### 5.5 Named places in and around Downbelow

| Place | What | Sector | Auth | Source | Era |
|---|---|---|---|---|---|
| **Happy Daze Bar** | *"A very low key bar."* Garibaldi hid there while on the run and *"crawled back into the bottle"* | **Brown**, named beside DOWNBELOW on the rosette | 3 (the rosette), 4 (the description) | `other map.png`; https://babylon5.fandom.com/wiki/Happy_Daze_Bar | Incident is 2258 (S1); **the venue is the only Downbelow interior placed at authority 3** |
| **Wet Rock** | A Downbelow bar, *"owned and run by Irene Hardesty; the greasy food is even worse than the drink"* | Downbelow | 4 | search summary of https://babylon5.fandom.com/wiki/Category:Bars_and_Restaurants | **Era unverified** — likely tie-in fiction. Build the *type*, treat the name as optional |
| **Eight to the Bar** | A Downbelow bar *"run by Josephina Quarte that often features performances by live bands"* | Downbelow | 4 | ibid. | Its named singer dies in **2261 (S5)** — so the venue exists by then; in-era status **unverified** |
| **Franklin's free clinic** | Dr Franklin ran an **unofficial free clinic in Downbelow** for people who could not afford Medlab; through 2258–2259 it doubled as cover for the **telepath underground railroad** | Downbelow | 4 †, and 1 † for the railroad (S2E08) | https://babylon5.fandom.com/wiki/Stephen_Franklin | **In era and the single most important building in Downbelow** — see §9 |
| **A second, unlicensed clinic** | Dr Laura Rosen treating people with an alien healing device, *"another unauthorised clinic operating in Downbelow"* | Downbelow | 4 † | *The Quality of Mercy*, S1E21 | **ERA: institution in, character out.** The *type* — an unlicensed practitioner competing with the free clinic — is permanent |
| **The unfinished street** | The held frame: wide industrial street, centre light strip, neon shopfront, steel stair, equipment banks | Brown | 1, with era caveat | `reference/01-station-exterior/sleeping-in-light-05.jpg` | Set in era, dressing not |
| **The hidden level ("Grey 17")** | An **entire unnumbered level** between Grey 16 and 17, *"a disarrayed, incomplete corridor"*, inhabited in secret by a cult who believed escape impossible; found by **timing elevator rides** | Grey | 4 † | https://babylon5.fandom.com/wiki/Grey_17_is_Missing | **S3E19 — just after the datum.** The *level* exists before it is found, so an unfindable inhabited deck is in era even if the episode is not |

---

## 6. DOWNBELOW — THE POPULATION

### 6.1 Who they are

> "A **lurker** is a term used for the homeless living in Downbelow. Lurkers are **mostly human
> although alien lurkers are not unheard of**. They began settling on the station **as soon as it
> was opened**, beginning simply as people **searching for new lives and opportunities**. When
> they did not succeed, they often **did not have the money to afford a ticket back home**, so
> they ended up moving into the undeveloped parts of Downbelow."
> — authority 4, https://babylon5.fandom.com/wiki/Lurker

Two more sourced facts from the same page, both of which are behaviour:

- *"They often become **victims of the criminal underworld** that calls Downbelow their turf."*
  Lurkers are the *prey* of Downbelow crime as well as its cover. They are not the criminals.
- *"There are those that hide among the nameless in Downbelow because they are **on the run from
  something or someone, like the Psi Corps or the law**."*

### 6.2 The composition — 20,000 people, broken down

**Authority 5 apportionment of an authority-5 total**, but every stream is individually sourced.
This is what `station/npc/schedule.py`'s `lurker` role needs in order to stop being one flat
archetype.

| Stream | Count | Share | Why they are here | Source of the stream |
|---|---|---|---|---|
| **Economic strandees** | **11,000** | 55% | Came for work, failed, cannot buy passage home. The canonical lurker | 4, https://babylon5.fandom.com/wiki/Lurker |
| **Narn refugees** | **3,500** | 18% | The datum is **after** the Centauri attacks that *"caused the deaths of 5,000 Narns and forced the evacuations of several thousand others"*; the station is *"inundated by Narn refugees"* in S3 | 4 †, https://babylon5.fandom.com/wiki/Narn-Centauri_War; `FACTIONS.md` §6 |
| **Working poor with no quarters** | **2,500** | 13% | Day labour at the docks and in the plant. **They have jobs and no address.** The most important stream for making the place feel like a city rather than a pit | 5, from the dock/cargo labour figures in `FACTIONS.md` §11.1 |
| **Fugitives and the undocumented** | **1,500** | 8% | Rogue telepaths avoiding Psi Corps, people avoiding the law, expired visas, forged identicards | 4, https://babylon5.fandom.com/wiki/Lurker |
| **Alien lurkers** | **1,000** | 5% | *"Not unheard of."* Mostly League species — Drazi, Brakiri, pak'ma'ra. **Not** Minbari, Centauri or Vorlon | 4, ibid.; species set from `FACTIONS.md` §2.4 |
| **The sick, the addicted, the mentally ill** | **500** | 3% | Franklin's clinic exists because of this stream; *The Long Dark*'s Amis is one (a war veteran, sole survivor of 47) | 4 † |
| | **20,000** | | | |

**Species mix, and it matters for crowd rendering.** ~13,500 human (`FACTIONS.md` §2.2) + 3,500
Narn + ~1,000 other + ~2,000 human working poor ⇒ Downbelow is **roughly 78% human and 17.5%
Narn** at the datum. That is a *completely different* mix from the Zócalo's galactic-port blend,
and the Narn fraction is a direct visual record of the war. **The crowd in Downbelow should look
wrong compared to everywhere else on the station**, and a player who notices that has read the
politics off the geometry.

### 6.3 Where and how they sleep

Authority 5, derived from §5.1 and §5.3. Written as placement rules.

| Rule | Detail |
|---|---|
| **Not in rooms** | The unfinished decks have almost no rooms. Canon says *"squatting and living in the **abandoned corridors**"*. A lurker's home is **a marked-out patch of corridor floor**, a niche in a service alcove, or a capped-off side passage |
| **Against the warm wall** | Camps form on the plant side. Sleeping positions cluster within a few metres of compressor and pump runs |
| **Off the through-route** | The illuminated centre strip is the street; people sleep in the recessed deck panels either side of it, backs to the wall. **The strip stays clear** — that is the visual grammar of the space and it reads instantly |
| **Vertically stacked where structure allows** | The concourse-class volumes are **two decks with an upper walkway** (auth 1, `central corridor.webp`). The walkway is prime real estate: defensible, above the traffic, harder to be robbed on |
| **Pitch size** | ~2 × 1 m of floor per person, plus shared circulation ⇒ the 25 m²/person of §5.3 |
| **Possessions** | Bedroll, one container, a heat source, a light. **Everything a lurker owns is portable**, because everything not portable is stolen or cleared in a sweep |
| **Density gradient** | Densest at the plant, thinning outward over ~150 m, then nothing at all for a kilometre |

---

## 7. THE ECONOMY OF DOWNBELOW

### 7.1 The one hard price anchor

**Command-grade quarters cost 30 credits/week** (authority 1 †, S2E08 *A Race Through Dark
Places*, in `FACTIONS.md` §2.1 — Earth Central bills Sheridan and Ivanova for oversized rooms).
Currency is **credits**, with **millicredits** below 1 credit; exchange is through the **Business
Center** (authority 1, the customs board). *"A substantial source of income for the station was
the **rent** paid both by individuals for their living quarters and by businesses for the spaces
they utilised"* (authority 4, https://babylon5.fandom.com/wiki/Babylon_5).

Everything below is **authority 5, scaled off that single anchor.** It is offered because a
builder needs numbers on a price board, and a stated-and-reasoned scale is worth more than blank
props.

| Item | Price | Reasoning |
|---|---|---|
| Command / senior quarters | **30 cr/week** | **Sourced** |
| Standard station personnel quarters | 10–15 cr/week | Below the oversized-quarters surcharge that triggered the billing |
| Cheap transient room, Red | 4–8 cr/week | The layer between a hotel and Downbelow (`LOCATIONS.md` §11) |
| A bunk in a Downbelow dosshouse | **1 cr/night** | The floor of the market |
| A squat | **0** | And it is why people are there |
| A meal at a Zócalo cart | 1–2 cr | |
| A day's casual dock labour | **8–15 cr** | Enough to eat and sleep indoors that night, not enough to accumulate |
| **Passage home, economy** | **300–800 cr** | **The load-bearing number of the whole underclass.** It must be 30–100 days of casual labour *with nothing spent*, because canon's entire explanation for lurkers is that they *"did not have the money to afford a ticket back home"*. If it were 50 credits there would be no lurkers |

### 7.2 The informal jobs — what people actually do all day

`station/npc/schedule.py` gives the `lurker` role **`work_start 0.0, work_hours 0.0`** — no
schedule at all. That was right as a first cut and it is wrong as a final state: **most lurkers
work, they just do not have jobs.** This table is the replacement, and it is written to be
implementable as a weighted activity table.

**Authority 5 throughout**, anchored on two sourced facts: canon says lurkers survive by
*"scrounging through the refuse of the hurried construction process for anything they could
**eat, wear, or sell**"*, and that *"the only work for Lurkers is often on the shady side"*
(https://babylon5.fandom.com/wiki/Lurker).

| Work | Share of the 20,000 | Where | Rhythm |
|---|---|---|---|
| **Salvage and strip-out** | 22% | The unfinished decks themselves — cable, fittings, panel, anything the constructors left | All hours. **The single most characteristic Downbelow activity**, and it is *literally* what canon describes |
| **Casual dock and cargo labour** | 18% | Blue, at the bay elevators; hired at a muster point at shift change | **06:00 and 14:00 EMT muster** — a crowd forms and thins on a clock, which is the cheapest possible way to make the sector feel scheduled |
| **Waste and plant hand-work** | 12% | The waste plant they already live on. Sorting, hauling, cleaning | Continuous |
| **Fetch-and-carry, portering, queuing for others** | 12% | Zócalo margins, customs hall exits | Follows arrival waves — `FACTIONS.md` §2.3 gives **52 arrivals/day**, peaking at **20–40 people/minute** through a customs hall |
| **Begging and busking** | 8% | The boundary between Downbelow and the commercial rings. **Never inside the Zócalo** — they are moved on (`FACTIONS.md` §12) | Station-evening |
| **Cooking, brewing, laundry, barbering *for other lurkers*** | 8% | Inside the camps | **This is the one that makes it a community rather than a pit.** An internal service economy with no currency worth the name |
| **Sex work** | 5% | Camp edges and the cheap bars | Named at authority 4 among the ordinary crimes (`FACTIONS.md` §11.4) |
| **Lookout, courier, muscle, fence** | 8% | For the criminal layer (§8) | *"The only work ... is often on the shady side"* |
| **Nothing — sick, injured, addicted, too old** | 7% | Where they sleep | The stream Franklin's clinic exists for |

**And one attested exception worth building as an NPC archetype.** Jinxo, in *Grail*, is
*"odd among criminal Lurkers because he has a valuable and marketable skillset: **deep-space
construction**"* (authority 4 †, https://tvtropes.org/pmwiki/pmwiki.php/Recap/BabylonFiveS01E15Grail).
**ERA: institution in, character out.** The archetype — *a lurker who built this station and now
sleeps in the part of it he never finished* — is the best single piece of characterisation the
underclass has, and it is free.

### 7.3 Work-for-food, and an honest correction

The brief asks about "work-for-food". **No source found states such a system exists on Babylon 5,
and this file will not invent one and dress it as canon.** What *is* sourced is (a) scrounging
for *"anything they could eat"*, (b) that lurker work is *"often on the shady side"*, and (c)
that Franklin ran a **free clinic** — a charitable service, unofficial, at a doctor's own
initiative. The pattern those three imply is **informal patronage, not an institution**: a
merchant feeds a lurker for unloading a crate, the clinic gives out what it has, a bar owner
keeps a man in soup for keeping the doorway clear. **Model it as thousands of individual
transactions, not as a soup kitchen with a queue** — unless a source is found, in which case
promote it. Logged as **D-05**.

---

## 8. CRIME

### 8.1 The headline number, and what it does and does not mean

> "Downbelow ... **accounts for as much as 90% of the station's crime rate**."
> — authority 4, https://babylon5.fandom.com/wiki/Downbelow

**Read it carefully.** It says 90% of crime *happens there*, among 8% of the population. It does
**not** say lurkers commit it — the same wiki says lurkers *"often become victims of the criminal
underworld that calls Downbelow their turf."* The correct model is:

> **Downbelow is where crime is *safe*, not where criminals live.** It is unpoliced (§2.5, zero
> patrol), unlit (§5.4), unmonitored, and full of people with no legal standing to complain.
> The organised criminals live in the Alien Sector and the commercial rings; they *operate*
> in Downbelow.

That is exactly N'Grath's depicted arrangement: *"rarely left his quarters in the **alien
sector**"* while *"operating out of Babylon 5's **Down Below**"* (authority 4,
https://babylon5.fandom.com/wiki/N%27Grath) — the two-address structure `LOCATIONS.md` §15
already flags.

### 8.2 What is common and what is rare

**Frequencies are authority 5**, derived from a 250,000 population, ~20,000 in Downbelow, and 150
officers on duty. They exist so a director can fire events at the right rate rather than making
every corridor a crime scene.

| Crime | Frequency | Where | Auth for the crime | Source |
|---|---|---|---|---|
| **Petty theft** | **Constant** — dozens/day | Everywhere; concentrated at customs exits, the Zócalo, and *within* the camps | 4 | https://babylon5.fandom.com/wiki/Ombudsmen |
| **Identicard and visa fraud** | **Very common** — the station's signature crime | Downbelow, forged by fixers | 5 from an authority-1 prop; N'Grath's services explicitly include **"forged identicards"** (4) | `identicard readout.webp`; https://babylon5.fandom.com/wiki/N%27Grath |
| **Unlicensed trade / smuggling** | **Very common** | Cargo bays → Downbelow → the Zócalo's back rooms | 4 + 1 † | ibid. |
| **Robbery with a weapon (usually a knife)** | **Common in Downbelow, rare elsewhere** | *Hunter, Prey*: two thugs mark a man out because he *"obviously stands out in Downbelow"*, **draw a knife**, and search his coat | 4 † of in-era footage | https://reactormag.com/babylon-5-rewatch-hunter-prey/ |
| **Debt enforcement / protection** | **Common** | *Grail*: a crime boss *"demanded his debts be paid with interest"* and threatened to feed the debtor to a creature | 4 † — **ERA: institution in, character out** | https://tvtropes.org/pmwiki/pmwiki.php/Recap/BabylonFiveS01E15Grail |
| **Contraband: controlled substances** | **Common** | The **G'Quan Eth** plant is required for Narn ritual and *"contains substances controlled under Earth law"* — a religion/jurisdiction collision built into a prop | 1 † | `FACTIONS.md` §11.3 |
| **Dust** | **Rare, and an event when it happens** | See §8.3 | 1 † | S3E06 |
| **Prostitution** | Common | Camp edges | 4 | https://babylon5.fandom.com/wiki/Ombudsmen |
| **Weapons offences (carrying)** | Uncommon — enforcement is *"reasonably well enforced"* | Chokepoints | 4 | midwinter tech manual |
| **Weapons *smuggling* (military-scale)** | Rare, enormous | G'Kar runs weapons to the Narn resistance **through Babylon 5** | 4 | https://babylon5.fandom.com/wiki/Narn_Resistance |
| **Assault** | Common in Downbelow, uncommon elsewhere | | 4 | Ombudsmen |
| **Murder** | **Rare — single figures per year** | Overwhelmingly Downbelow, and **most of it never reported**, because the victim had no identicard record | 5 | — |
| **Fraud on visitors** | Common | Zócalo, arrival concourse. Stolen **credit chits** are an attested offence | 4 † | https://babylon5.fandom.com/wiki/Blue_Sector |
| **Sedition (Nightwatch)** | **Rising, and it is not really crime** | Zócalo, bars, merchants | 4 + 1 † | `FACTIONS.md` §5 |
| **Raider activity** | Off-station | A traffic-control and docking concern, not a corridor one | 1 † | `FACTIONS.md` §11.4 |

### 8.3 Dust — the in-era set piece

**S3E06 *Dust to Dust*, squarely in era, and the only named narcotic on the station.**

| Fact | Detail | Auth |
|---|---|---|
| What it does | *"Stimulates the latent telepath gene in most humans"*, letting a user *"take a joyride in someone else's mind"* — living out another person's experiences | 4 †, https://babylon5.fandom.com/wiki/Dust_to_Dust |
| Effect on victims | *"Normals assaulted by a Dust user usually **recover in a few days**, but ... telepaths made the victims of Dust users **rarely recover at all**"* | 4 † |
| Origin | *"Dust was the [Psi] Corps' attempt to create telepaths from mundanes"* | 4 † |
| Why Psi Corps comes | **Bester arrives personally to stop the flow.** The distributors are trying *"to break out into alien markets"* | 4 † |
| In-era consequence | A **Psi Cop aboard** is a station-wide event: `FACTIONS.md` §12 says a Psi Cop visit *clears corridors* and drives unregistered telepaths deeper into Downbelow | 1 †/5 |

**Why this matters more than a drug plot.** Dust makes **assault** out of **telepathy**, which
makes the identicard's `LICENSED PSI` field a *safety* record rather than an administrative one,
and it gives Downbelow's fugitive-telepath stream (§6.2) a reason to be terrified of both the
dealers and the police. One narcotic ties the underclass, the Psi Corps, the identicard system
and the black market into one mechanic.

### 8.4 The black market — what it physically is

**It needs no dedicated room** (`LOCATIONS.md` §15 says so, and that is right). What it needs is
a *route*, and the route is placeable:

```
cargo bay (Blue/Yellow)  →  a bribed docker  →  cargo lift  →  the unfinished decks
   →  a fixer's back room  →  a Zócalo stall's under-counter  →  a customer
```

| Node | Placement | Auth |
|---|---|---|
| **Entry** | 42 cargo bays, 28 rotating + 14 support. A station that is *"not full"* (session 2t: 42 bays, 6 external modules) has spare volume nobody inventories | 3/4 |
| **The bribed docker** | Dock Workers' Quarters, Blue — a **named authority-3 facility**. The Dockers' Guild is organised and has already struck over conditions (`FACTIONS.md` §11.1); an underpaid organised workforce at the only entry point is where the leak is | 3 + 1 † |
| **Storage** | The unfinished decks. **This is what 146 million m² of unaudited floor is for** (§1.4) | 5 |
| **The fixer** | N'Grath's model: a sealed non-oxygen room in the Alien Sector, reached by appointment, business comes to him | 4 |
| **Retail** | Under a Zócalo counter, in a Downbelow bar, or a private cabin | 5 |
| **Where it is visible to a player** | The **margin** — the two or three cells where the finished commercial ring meets the unfinished one. Stalls with no licence plate, goods with no customs seal, buyers who do not want to be seen | 5 |

**The Thieves Guild** is attested aboard as a network with branches *"practically everywhere"* —
a faction, not a building (authority 4, https://babylon5.fandom.com/wiki/Thieves_Guild,
via `LOCATIONS.md` §15).

### 8.5 Violence — how much, and how it should read

**Authority 5, and it is a deliberate correction to the obvious build.** `FACTIONS.md` §12 sets
the rule for factional friction: *"95% as avoidance and 5% as contact."* The same rule governs
crime, for the same reason:

- **A station where a fight happens every time the player walks through Downbelow is a cheaper
  place than one where nothing happens and it still feels dangerous.**
- Danger reads as **attention**: people stop talking, someone follows for twenty metres and turns
  away, a group blocks a route without touching anyone, a lookout speaks into nothing.
- **Being marked out is the mechanic.** *Hunter, Prey* is explicit — the victim was selected
  because he *"obviously stands out."* So clothing, cleanliness, gait and light should drive
  hostile attention, and a player who dresses down and moves like a resident should be left
  alone. That is a far better system than a hostility radius.
- Actual violence: **one or two contact events per hour of play in Downbelow**, and each one
  should be short, ugly, and over before security exists.

---

## 9. SECURITY AND DOWNBELOW — HOW THEY ACTUALLY INTERACT

The brief says this "is not simply enforcement", and the sources agree. Five modes, and the
first two are not policing at all.

**1. Absence — the default.** Zero permanent posts, zero routine patrol (§2.4, §2.5). 12–20
minute response (§2.6). *"Downbelow, the obvious place for a fugitive"* (authority 4 † of
*Hunter, Prey*). **The absence is the relationship**, and 90% of the station's crime is a
description of it.

**2. Medicine before enforcement.** *"Dr Stephen Franklin set up a **free clinic in Downbelow** to
help treat those in need that couldn't afford to go to Medlab"* (authority 4 †,
https://babylon5.fandom.com/wiki/Stephen_Franklin). The station's actual, functioning presence in
Downbelow at the datum is **a doctor, not a policeman** — and the same clinic is knowingly
sheltering fugitives from Psi Corps. **Franklin's clinic should be built before any security
post in Downbelow**, because it is the only sourced institutional presence there and it is where
a player's Downbelow story naturally starts.

**3. Entry with a guide, not a patrol.** When security *does* go in, the depicted method is
**Garibaldi taking Franklin** because Franklin knows the ground and the people (*Hunter, Prey*,
in era). That is the shape of every Downbelow operation: **two officers and a local**, asking,
not sweeping. Build it as an NPC pattern — a security pair moving slowly, talking to specific
individuals, with a civilian walking ahead of them.

**4. Informants and tolerance — authority 5, and it is the load-bearing invention.** No source
states it. It is nonetheless what a 150-officer force with a 20-minute response *must* do, and it
is what the depicted behaviour implies:

- Security **knows** where the camps are and does not clear them. Clearing 20,000 people to
  nowhere is not an option; there is nowhere.
- Security **trades**: a lurker's information for not being moved on. Franklin's clinic is a
  parallel trade in the same currency.
- There is a **line**, and it is geographic: what happens in Downbelow stays in Downbelow.
  Crime that reaches the Zócalo or a docking bay draws a response that crime three decks out
  never does. **Enforcement is a boundary, not a volume.**

**5. The sweep — the exception that proves it.** Occasionally, and always for a reason (a
fugitive, a Dust seizure, a political order), security floods a section. `FACTIONS.md` §11.2
already names dispersal-during-sweeps as the behaviour to build. It should be:

- **Announced by its own approach** — lights, movement, word running ahead faster than the
  officers walk;
- **Preceded by evacuation** — the camp empties into the unfinished dark before contact;
- **Fruitless** — the sweep finds an abandoned camp, and the camp is back in six hours.

**And one thing that must not be built.** Do not give Downbelow a police station. Nothing sources
one, the arithmetic forbids it, and a permanent post there would destroy the exact contrast —
diplomatic marble at 0.6 g against unlit unfinished deck at 1.4 g — that `LOCATIONS.md` §19
identifies as the emotional core of the whole simulation.

---

## 10. NUMBERS TO BUILD TO

Every figure with its authority. This is the section a builder copies.

| Quantity | Value | Auth |
|---|---|---|
| Security force, total | 500 | 5 (`FACTIONS.md` §2.2) |
| Security on duty at any moment | ~150 | 5 |
| Officers per streaming cell, station-wide | **0.064** | 5, over `cell_manifest()` |
| Patrol unit | 2 officers | 5 |
| Nightwatch armband fraction of the force | 30–40% | 5 (`FACTIONS.md` §5.4) |
| Response, Security Central → Grey ring 1, vehicle only | **300 s** | **derived** (`core_shuttle.py`) |
| Response, realistic, door to door | 12–20 min | 5 on top of the derived leg |
| Grey ring 1 deck circumference / half-circuit on foot | **2,527 m / 16 min** | derived |
| Apparent weight, 75 kg person, Grey ring 1 | **108 kgf** | derived (`sector_report`) |
| Brig capacity | 24–40 cells + 2 group holds | 5 |
| Typical detention | hours to days | 5, from three attested uses |
| Ombuds aboard | ≥ 2 | 4 |
| Downbelow population | **~20,000** (8%) | 5, bracketed 13,000–50,000 |
| — human / Narn share | ~78% / ~17.5% | 5 |
| Downbelow squatted floor area | **~500,000 m²** at 25 m²/person | 5 |
| — as a share of the outermost ring | **0.53%** | derived |
| — expressed in cells | **≈ 8 of 753** | derived |
| Lurkers per occupied cell | **~2,500** | derived |
| Pressurised deck area per capita | **585 m²** | derived — see §1.4 |
| Drum sub-floor: radius / gravity / decks / cells | 310.8 m / **1.117 g** / 9 / 138 | derived |
| Grey ring 1: radius / gravity / decks / cells | 402.2 m / **1.445 g** / 20 / 343 | derived |
| Command quarters rent | **30 cr/week** | 1 † |
| Passage home | 300–800 cr | 5 |
| Day labour | 8–15 cr | 5 |
| Contact-violence rate in Downbelow | 1–2 per hour of play | 5 |
| Downbelow share of station crime | **90%** | 4 |

---

## 11. UNPLACED — known, wanted, never located

| Thing | Why unplaced | Proposal |
|---|---|---|
| **The brig** | One ambiguous authority-4 address (§1.5); `LOCATIONS.md` P-04 proposes Red | **D-01** |
| **Security station houses** | Attested as plural and distributed at authority 4; none is located | **D-02** |
| **Fixed security posts** | Never enumerated by any source | **D-03** |
| **The Downbelow camps** | The *rule* is sourced (waste, air, water); no specific location is | **D-04** |
| **Any work-for-food institution** | **Not attested at all.** See §7.3 | **D-05** |
| **Franklin's free clinic** | Attested as being *"in Downbelow"*; no ring, no deck | **D-06** |
| **The mindwipe facility** | Implied to be Medlab-certified; never located | **D-07** |
| **Evidence store / property office** | Never mentioned by any source. A station that seizes contraband has one | **D-08** |
| **The morgue** | `LOCATIONS.md` P-03; unchanged here, but see D-09 for the Downbelow variant | **D-09** |
| **Muster point for casual dock labour** | Implied by dock labour existing; never shown | **D-10** |
| **N'Grath's premises (or a successor's)** | Two addresses, neither placed within its sector | **D-11** |
| **The customs contraband inspection area** | The customs *halls* are placed at authority 3; the search room is not | **D-12** |
| **Where a lurker gets water** | Genuinely unknown. Water reclamation is placed at authority 3/4; nothing says whether there is a standpipe | — |
| **Whether Downbelow has children** | `LOCATIONS.md` §18 item 8 records that no source found mentions children anywhere on the station. This is a **real hole in the "living thing" brief** and it is at its sharpest here — a 20,000-strong stranded underclass with no children is not a population, it is a set | — |

---

## 12. PROPOSED PLACEMENTS — the reasoning

**Every one is authority 5.** If built, each goes in `canon/INVENTIONS.md` with its overturn
condition. None may be recorded as canon.

**D-01 — The brig: attached to Security Central in Red's inner ring, *and* a small remand annexe
in Blue beside the customs halls.** This satisfies both §1.5's evidence and `LOCATIONS.md` P-04
instead of choosing between them, and it is what a real port does: a **dockside holding room**
where people are detained at the border, and a **main remand block** at headquarters where they
are held for court. The Blue annexe is where "held in Blue 5 to await the Centauri
representative" happens — a consular collection is a *docking* event, so holding the prisoner
next to the docks is correct, not lazy. *Overturned by:* any frame showing the brig with a
recognisable sector's wall treatment.

**D-02 — Station houses: one per pressurised sector, on the outermost ring, on the main
concourse.** The authority-4 phrase is *"the central hub for the numerous station houses located
throughout the station"*, which specifies a hub-and-spoke force and nothing else. Outermost ring
because that is where the concourses and the crowds are (Zócalo, Central Corridor), and because a
substation inboard would be further from every incident. Four of them (Grey, Green, Red, Blue).
*Overturned by:* any source locating one.

**D-03 — Fixed posts at the seven chokepoints named in §2.4.** These are not chosen for
flavour; each is a place where the station's own canon already requires control — two customs
halls (authority 1 signage), the bay elevators (authority 3), the Grey boundary (authority 4
restriction), Blue's access restriction (authority 4), the Alien Sector airlocks (authority 4),
plus the Zócalo and the Council approach, which are where the crowds and the ambassadors are.
*Overturned by:* footage showing free movement across a restricted boundary.

**D-04 — Four camps, one per pressurised sector, each pinned to that sector's waste-management
plant, with the largest beside Waste Management Control.** The clustering rule is sourced (waste,
air compressors, water reclamation); the sectoral distribution is forced by the fact that
"Waste Management Systems ('Down-Below')" is named in **three rosettes and twice on the sectional
schematic** — it is a distributed system, so its slums are distributed too. This also solves a
build problem: four camps of 5,000 are four authorable places, where one camp of 20,000 is a
crowd-rendering problem with no interior. *Overturned by:* any source describing Downbelow as a
single contiguous district.

**D-05 — No work-for-food institution. Model informal patronage instead.** See §7.3. Build
individual transactions — a merchant, a crate, a meal — not a soup kitchen. *Overturned by:*
any source naming a relief programme, in which case build it, because a queue is excellent
content.

**D-06 — Franklin's clinic: at the boundary cell, where the finished commercial ring meets the
unfinished decks.** It has to be findable by people who cannot read a directory and reachable by
a doctor who has a day job in Medlab, and it has to have power and water — so it takes over a
**shell unit of the unbuilt commercial fit-out**, on the last deck that still has services. That
single placement makes the boundary between the two worlds a *place* rather than a line.
*Overturned by:* any frame showing the clinic with the drum curve or a porthole visible.

**D-07 — The mindwipe facility: Medlab One, Blue, in a dedicated sealed suite.** Sourced
requirements: Medlab personnel certify the machinery, and a telepath performs scans before and
after. Both point at the medical estate rather than the judicial one, and the sentence is rare
enough that the room is normally dark. *Overturned by:* any source placing it with the courts.

**D-08 — Evidence and property store: attached to the main brig, Red inner.** Chain of custody
runs detention → court, so it belongs on that axis. It also gives the contraband layer a physical
destination, which turns a seizure into an object with a location. *Overturned by:* nothing
likely. Low risk.

**D-09 — A second, unofficial mortuary function in Downbelow.** `LOCATIONS.md` P-03 places the
morgue in Blue by Medlab and notes that placing it in Downbelow *"would be equally plausible
dramatically and would change the tone completely."* **Propose both.** Deaths among 20,000
undocumented people do not enter the medical chain of custody — there is no identicard to file
against. So there is a place in Downbelow where bodies go, run by the residents, and it is not
the station's morgue. Cheap to build and it says more about the sector than any amount of
graffiti. *Overturned by:* any source describing how a lurker death is handled.

**D-10 — Casual labour muster: outside the bay-elevator security post, Blue outer ring, 06:00
and 14:00 EMT.** Hiring happens where the work is and where the gangers can see who turned up; it
happens at shift change; and it happens *outside* the checkpoint because the people queuing are
not cleared to be inside it. **The queue that forms and dissolves twice a day on a clock is one
of the cheapest and most convincing pieces of "living station" in this document.**
*Overturned by:* any source describing how dock labour is engaged.

**D-11 — The fixer's premises: a sealed non-oxygen suite on the Alien Sector's outer ring, with a
separate Downbelow back office reached by a service route.** This is N'Grath's depicted
arrangement generalised so it survives the era question in §1.6 — build the **role**, an insectoid
methane-breathing fixer with reach into Downbelow, and let the name be optional. The two rooms
must be **connected by a route the player can trace**, because that route is the black market.
*Overturned by:* an S3 source confirming or replacing N'Grath.

**D-12 — Customs search and seizure rooms: immediately behind each of the two customs halls,
north and south.** The halls are placed at authority 3 and their signage is authority 1
(*"FOLLOW ALL CUSTOMS PROCEDURES"*). A hall that processes **~12,600 transactions a day**
(`FACTIONS.md` §2.3) needs a place to take people out of the line, and that room — a table, a
scanner, two officers, a locked hatch to the evidence store — is where the station's most common
serious offence (§8.2) is actually detected. *Overturned by:* nothing likely.

---

## 13. WHAT THIS FILE COULD NOT DETERMINE

| Question | What would settle it |
|---|---|
| **The size of the security force** | Nothing found. `FACTIONS.md` §15 reports the same null. **The most likely source is the licensed *Babylon 5 Security Manual* itself** — see the acquisition note below |
| **Where the brig is** | One frame of a cell with a legible sector wall treatment, or a lift display |
| **Brig capacity, and cell construction (bars? force field?)** | Any interior frame. **Zero held** |
| **How long anyone is held** | Dialogue giving a period, or a charge sheet prop |
| **Downbelow's population** | Never stated. The 20,000 is bracketed by a **forum estimate** and a forum upper bound, which is the weakest evidence in this file |
| **Whether Downbelow has children** | Anything at all |
| **How a lurker gets water** | Anything at all |
| **Whether N'Grath is still operating at the datum** | His last appearance, or a named successor |
| **Whether "Wet Rock" and "Eight to the Bar" are in era** | Their source publication — both may be tie-in novels |
| **What a Downbelow camp actually looks like in S2–3** | **The reference set contains zero in-era Downbelow frames.** `reference/06-sector-brown-downbelow/` is **empty**, and the one Downbelow-class frame is S5 and derelict, filed in `01-station-exterior/` |
| **Whether Downbelow has portholes** | One frame. It would materially move C-003 (§5.2) |

### The single highest-value acquisition this research identified

The project already treats two sheets *from the Security Manual* as its best authority-3 sources.
The book they came from is:

> **Jim Mortimore & Roger Clark, *Babylon 5 Security Manual*, Del Rey / Boxtree, 1998, 160 pp.**
> Its own description: *"complete knowledge of Babylon 5's structure, technical operations,
> **personnel and population**; ... full technical illustrations of **weapons, crafts, uniforms
> and accessories**; **detailed maps of every deck, level and section of Babylon 5**; proper
> **protocol, laws, combat and emergency procedures**; and deep background on key personnel and
> **dangerous inhabitants**."*
> — authority 4 (bookseller and search summaries),
> https://www.amazon.com/Babylon-Security-Manual-James-Mortimore/dp/0345424530

Read that list against this project's open problems. *"Detailed maps of every deck, level and
section"* is **exactly what C-004 has been blocked on for six sessions** — `STATE.md` calls one
lift-car display "the single highest-value gap in the reference set", and this is a 160-page
licensed book of deck maps, written in-universe by the chief of security, covering laws,
procedures, personnel numbers and weapons. **It is authority 3, it is the source of two files the
project already owns, and nobody has looked for the rest of it.**

`docs/REFERENCE-GAPS.md` is the channel for asking the owner. **This should go to the top of it.**
A secondary target is the **Mongoose *Babylon 5 Roleplaying Game* (2003)**, whose station chapter
reportedly carries *"the cost of housing in the various sections and **Security Response
Times**"* plus stat blocks for *"the dockworker, security officer and thug"* (authority 4,
https://www.rpg.net/reviews/archive/9/9578.phtml) — which is, almost line for line, the data
§2.6, §7.1 and §8.2 had to derive.

---

## 14. WHAT TO BUILD NEXT, RANKED

Ranked by value delivered per unit of C-003/C-004 risk.

1. **The unfinished corridor kit** (§5.1). Highest value in the entire document and **zero
   blocking-conflict risk** — it is a material and dressing variant of `interior_kit.py`, not a
   placement. It covers ~90% of the station's decks (§1.4), it is what Downbelow *is*, and every
   element of it is authority-1 supported by a held frame. Nothing else in this file can be built
   convincingly until it exists.
2. **One Downbelow camp, at one waste plant** (D-04). 5,000 people in one cell, against the
   plant, with the lit centre strip kept clear. It makes crowding and isolation legible in the
   same volume, and it is the owner's "slums" request delivered.
3. **The lurker schedule** (§7.2). `schedule.py`'s `lurker` role has zero work hours and needs the
   nine-activity table. Pure data, no geometry, and it turns 20,000 static bodies into a
   population. **Do the 06:00/14:00 labour muster (D-10) first** — it is one queue and it makes
   the whole sector look scheduled.
4. **The security post set and the patrol director** (§2.4, §2.5). Seven fixed posts, 35 roving
   pairs, the beat frequencies, and the armband boolean `FACTIONS.md` §16 already asks for. The
   *contrast* is the deliverable: four officers in the Zócalo, none for a kilometre.
5. **Franklin's free clinic** (D-06). One room, at the boundary between the two worlds, and the
   only sourced institution inside Downbelow. It is also where a player's story starts.
6. **The escalation ladder and the identicard check** (§2.7). Seven rungs, one prop, and it is
   the security interaction a player will see a hundred times.
7. **The Ombuds courtroom** (§4.2). Placed at authority 3 in Red's inner ring, low risk, and it
   makes the law layer visible. But it is one room seen rarely, so it ranks below the systems.
8. **The brig** (D-01, §3). Lowest confidence in the file — unplaced, uncounted, and with zero
   interior reference. Build it last, or build it when a frame turns up.

**Three decisions that should be taken before any of it is dressed:**

- **Renumber INV-009 and INV-010** (§1.3). Four documents already cite the ambiguous tags.
- **Decide what "Brown" resolves to in code** (§1.1). `schedule.py` has a `"downbelow"` workplace
  string with nothing to bind it to, and `bind_labels()` cannot produce a Brown address because
  the schema has no Brown sector. Whichever way C-003 goes, *something* has to answer
  `where_is("Brown")`.
- **Put the *Security Manual* book at the top of `REFERENCE-GAPS.md`** (§13). It is the only
  identified source that could close C-004 outright, and it is the source two of this project's
  best files already came from.
