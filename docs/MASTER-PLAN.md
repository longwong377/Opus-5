# MASTER PLAN — Babylon 5, alive

**Session 4h. This replaces every previous plan as the ordering rule.** The session-3k document —
three tracks, twelve milestones M0–M11 — is preserved as `docs/MASTER-PLAN-3k.md` because its audit
is still the best analysis in the repository; it is no longer what decides what to work on.
`docs/SHIP-PLAN.md`'s audit of the four contradictory plans stands as the record of *why* this
rewrite happened, and its connectivity work is finished. Set by the owner after a strategic
reassessment, with two rulings recorded in §1.

---

## 0. WHAT THIS IS AT THE END

A 1:1, canon-accurate Babylon 5 you can walk end to end and fly out of, era-locked to Season 2–3,
in which **250,000 people live by their own schedules** — and you can watch them do it. The owner's
words, still binding: *"a living thing rather than a building"*, *"the simulation exists around you
rather than in text"*, and the friction between factions **visible in a corridor**.

## 1. THE STRATEGIC RULING — LIFE FIRST

### The fact that decides it

**We reinvented Starfield's worst feature and were trying to beat Starfield with it.** Starfield's
hand-built cities are its best work — hundreds of artists, years — and its *procedurally generated*
content is the single most criticised thing in the game: the same lab, over and over. That is
exactly our **78 of 128 places built from one generic kit**, and it has the same cause.

And the constraint that settles the argument: **one agent authors everything, with no artists.**
Measured rate is four landmarks from craft 1 to craft 3 in a 70-minute agent session. 128 places at
that rate is roughly thirty sessions for **one pass**, and they would still be craft 3.
**Hand-authoring our way to AAA surface is not reachable — not slowly, not at all.**

### The two rulings

> **1. LIFE FIRST.** Roughly **60% life, 30% variety, 10% surface**. Surface quality is hard-capped
> by having no artists; **simulation depth has no ceiling**, and it is the thing an agent is
> actually good at building. Babylon 5 is a story setting: what people love is Downbelow and the
> Zocalo being *alive with factions*, not the polygon count. **A living craft-3 station is far more
> like Babylon 5 than a beautiful empty one.** Compete where Starfield failed, not where it won.
>
> **2. THE SHELL STAYS 1:1; ONLY THE NAMED PLACES GET INTERIORS.** The 8,047 m hull, its 70 ring
> decks, the drum and the whole circulation network remain exactly 1:1 and walkable end to end. The
> ~128 named places plus their connective corridors get real interiors. The other 73,507 bays are
> sealed or generic-but-varied, and **that is stated rather than counted as a shortfall**. 0.17% of
> footprint was never the blocker; identical rooms were.

### What this does NOT mean

It is not an abandonment of AAA. It is a decision about *where* the quality goes: into a station
that is **consistent, characterful and alive** rather than one that is beautiful in twelve rooms
and empty everywhere. Surface work continues — but only at the **kit** level, where one pass
multiplies across all 70 decks at once, which is how the corridor went 3 → 4 in a single session.

---

## 2. THE THREE TRACKS, AND THEIR SHARE

| | track | why this share | measured by |
|---|---|---|---|
| **60%** | **L — LIFE** | uncapped, differentiating, and code rather than art | **AGENCY**: residents executing a schedule *by moving*; verbs with world-state consequence; lines of dialogue heard |
| **30%** | **V — VARIETY** | the credibility floor. Fixes "every corridor looks the same" at its root | **VARIETY**: pairwise distinguishability between places, using the instrument `body.py --silhouette` already proves works |
| **10%** | **S — SURFACE** | capped, but kit work multiplies across everything | the existing craft rubric, at the half distance, **kit-level only** |

**Both new gates fail today and neither is a coverage count.** That is the point: every gate this
project has ever had measures *coverage* or *correctness*, and both are perfectly satisfied by one
generic thing repeated seventy-eight times.

---

## 3. THE L-TRACK — the ladder, and every rung is player-visible

Today: **zero** residents move, **zero** verbs change world state, **zero** lines of dialogue. All
the *data* exists — `populace` knows every resident's name, species, home, job, role, faction and
species-specific meal and sleep times; `npc/schedule.py` derives the day; `transit.py` costs every
journey; `routes.py` can path between any two places. **None of it runs.** `life.gd`'s own comment:
*"the runtime cannot create a person, so a room busier than its bake hour is capped"* — it shows and
hides pre-baked bodies by the hour.

| L | milestone | done when | today |
|---|---|---|---|
| **L1** | **Someone goes to work** | one named resident leaves their quarters at their own start hour, walks a `routes.py` path, and is at their post. Asserted headlessly | 0 |
| **L2** | **They eat and they sleep** | the species-specific meal and sleep times in `schedule.py` move bodies to a mess, a bar, a bunk | 0 |
| **L3** | **They use the transit** | a resident takes the lift to another deck, or the tram along the drum, and arrives. The vehicles already move | 0 |
| **L4** | **They talk** | `dialogue.gd` is 912 lines with **no content**. Lines keyed on who they are, what they are doing, their faction and the era | 0 lines |
| **L5** | **They react to you** | `npc.gd` already notices. Make it mean something: they move aside, they greet, they refuse | partial |
| **L6** | **The factions act** | Psi Corps, Narn–Centauri friction, security patrols, Downbelow's underclass. **The friction visible in a corridor**, which is the owner's own test | 0 |
| **L7** | **The economy turns** | a bar's stock falls when somebody buys. Money exists — a till is a till because there is money | 0 |
| **L8** | **Crime and law** | a theft happens, is reported, security responds, the brig fills | 0 |
| **L9** | **The information layer** | ISN, PA and signage report **what actually happened**, not a script | ambience only |

**L1 is the whole track in miniature and is the next thing built.** Everything above it is the same
machinery with more verbs.

## 4. THE V-TRACK — variety, generated rather than hand-authored

The register already knows what every place **is**: its functions, its declared interactables, its
fixtures, its faction, its species mix, its authority. **That has never driven form — only which
props get dropped in.** A generic room is generic because one generator with ten archetypes serves
seventy-eight places.

| V | milestone | done when |
|---|---|---|
| **V0** | **The gate exists and is red** | pairwise place distinguishability measured and reported, with the one-parameter-block control that must read 1.000 |
| **V1** | **Form follows function** | a medlab's *plan* differs from an office's because a medlab is not an office — bay rhythm, ceiling height, servicing, circulation, all keyed on the register |
| **V2** | **A corridor is not one corridor** | sector palette, deck age, traffic wear, faction presence. One kit, many readings |
| **V3** | **No two visited places are indistinguishable** | the gate goes green on everything a route passes through |

## 5. THE S-TRACK — surface, kit-level only

**A craft pass on a kit multiplies; a craft pass on a room does not.** `interior_kit.corridor_section`
is every one of the 70 decks at once — that is how the corridor went craft 3 → 4 in one session.
The lift interior and the transit car are the same lever: they are what a player looks at for most
of any journey.

Per-location craft passes are **not** in the 10%. They come after L and V, ordered by the routes,
authority-1 first — and a *generic* place still has to be **unidentifiable as generic**, which is
V's job, not S's.

---

## 6. WHAT IS EXPLICITLY OUT

* instancing the 73,507 unnamed bays
* hand-authored AAA interiors for all 128 places
* beating Starfield on surface fidelity — stated plainly so nobody spends a session trying
* the old M0–M11 milestones, layer numbers 0–8 as an ordering rule, and the W-track

## 7. THE RULES THAT SURVIVE, AND ONE THAT IS NEW

All of `CLAUDE.md`'s hard rules stand — nothing from memory, log every invention, blocking
conflicts block, inside and outside from one schema, double precision, update `STATE.md`. So does
the negative-control discipline, which is the highest-yield thing in this project.

**New, and it is what this session cost to learn:**

> **A GENERATOR IS FINISHED WHEN ITS OUTPUT IS VARIOUS, NOT WHEN ITS OUTPUT IS CORRECT.**
> One kit passing every closure, winding, budget and material gate while producing seventy
> identical decks is the disease, not the cure. And **do not send agents at defects** — defects are
> what gates find, so gates are what keep getting fed. Point them at content and behaviour.
