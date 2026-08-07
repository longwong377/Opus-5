# THE GAME — what the player wants, who can stop them, what failure costs

**This is P1/G0 of `docs/MASTER-PLAN.md`, which names this file by path and has been waiting for
it since session 4i.** It is the blocking input for G1 (a role loop), G2 (progression and
consequence) and G3 (the incident generator): each of those builds a mechanism, and a mechanism
with no answer to "why would anyone do this" is the thing session 4d's ruling warned about —
*"the project optimises what can be counted, because counts go green and a game cannot be
expressed as a count."*

**Status: extrapolation, authority 5, per hard rule 1.** Almost nothing here is canon — the show
is not a game and never specified one. What *is* canon-constrained is listed in §6 with its
source, and what would overturn each choice is stated beside it. The owner may overrule any of
this; it is cheap to redirect now and expensive once G1 builds against it.

---

## 1. THE ONE-SENTENCE ANSWER

**You are nobody, on a station of 250,000, and the only thing standing between you and being
put back on a transport is a card that says who you are — so the game is the slow, contested
business of becoming somebody the station has a reason to keep.**

That is the whole design. Everything below is that sentence with mechanisms attached.

## 2. WHY THIS AND NOT SOMETHING ELSE

The plan already decided most of it and the decision is better than it looks. `MASTER-PLAN` A2:

> **The progression spine is the identicard — and it already exists** (`player.py`: identicard,
> visas, credits; customs enforces it; the brig is a built place). Tiers: undocumented → visitor
> visa → resident → licensed trader / deputy → docking privileges (the Starfury cert). **Losing
> the card is canon-catastrophic, which makes it the perfect stakes object.**

Three properties make the card the right spine, and they are worth stating because they are why
this design is not arbitrary:

1. **It is already built.** `player.py` carries it, `customs` enforces it, `enforcement.py` can
   take it, and the brig is a real room with a door. The game does not need a new subsystem; it
   needs the existing ones pointed at a person.
2. **It is legible without a tutorial.** Everyone understands papers. A player who is refused
   entry to Blue 3 learns the entire rule set in one sentence from a guard.
3. **It is the show's own subject.** B5 is about displaced people, borders, and who gets to
   stay — Season 2–3 especially, with the Narn–Centauri war *rising* and refugees arriving.
   A game about papers on Babylon 5 is not a mechanic bolted to a licence; it is the licence.

**What was rejected, and why** — so a later session does not re-open it:

| rejected | why |
|---|---|
| a plot campaign following the show's episodes | the station is the product, not a screenplay. It would make 129 places into corridors between cutscenes, and it dates instantly against canon |
| combat as the core loop | one PPG fight is not tens of hours, and `AAA-STANDARD` robustness on ranged combat is a project of its own. FIGHT/RESTRAIN stays as a *consequence*, never a goal |
| open-ended sandbox with no goal | it is what exists today. It is the thing the owner is asking to be fixed |
| "become the commander" | canon-hostile and unreachable. The ceiling is deliberately *docking privileges*, not command |

## 3. WHAT THE PLAYER WANTS — the ladder, and it is the same object five times

Five tiers, each a **state on the identicard**, each with a gate a player can see being enforced
on somebody else before it is enforced on them.

| # | tier | you may | you may not | how you climb |
|---|---|---|---|---|
| 0 | **undocumented** | Downbelow, the grey market, casual labour paid in kind | pass any checkpoint, hold credits at a bank, rent a bunk | reach customs with something to declare, or be sponsored |
| 1 | **visitor visa** | the Zocalo, transient quarters, the concourse; buy and sell openly | work a registered shift, hold a lease | 30 days, or a work sponsor |
| 2 | **resident** | a lease, a registered job, the medical system | trade across the customs line, carry restricted goods | a job that lasts, and no arrests |
| 3 | **licensed trader / deputy** | move goods through customs; or carry a badge and make arrests | fly | a licence bought and kept clean, or a commission earned |
| 4 | **docking privileges** | the Starfury cert — launch, fly, dock | — | hours logged, a clean card, and someone senior signing |

**The ladder is a ratchet with teeth, not a staircase.** Every rung can be lost, and the loss is
the game's only real punishment (§5). Tier 4 exists because the owner's brief names a flyable
Starfury with seamless launch and dock; making it the *top of the ladder* means the flight model
already built becomes a reward instead of a side mode.

**The absence rule.** None of the five is a quest chain. Each is a *status the station computes
about you* from things that were going to happen anyway — shifts worked, fines paid, arrests, who
vouched. That is what makes A2's **absence gate** meaningful: a day you were not there still moves
other people up and down this same ladder.

## 4. WHO CAN STOP YOU — four, and they want incompatible things

Antagonists, not villains. Each is an existing subsystem given a want.

| who | wants | how it obstructs | already exists as |
|---|---|---|---|
| **EarthGov customs & immigration** | the manifest to balance | refuses, fines, revokes, deports | `customs`, `enforcement.py`, C-010 arrival |
| **Nightwatch** | names | rewards denunciation; being *seen* with the wrong person costs standing. Rising through S2–3 | `faction.py` FAC-04, the armband population, `broadcast.py`'s denunciation set |
| **the black market / the Broker** | your dependence | offers the shortcut that works and marks the card | `security.BLACK_MARKET_ROUTE`, the fence, `dialogue.py`'s Broker pool |
| **scarcity** | nothing — it is not a person | rent, food, the ladder's own fees; the reason you take the bad job | `economy.py`, the LADDER, hunger and fatigue (PLY-06) |

**The design load-bearing point: Nightwatch and the Broker are both shortcuts, and taking either
is how you lose tier 2.** The honest path is slower. That is the game.

## 5. WHAT FAILURE COSTS — and why it is never a reload

**There is no death and no game over.** The station is the product; ejecting the player from it
is the one thing the design must not do. Failure is *demotion plus a record*, and the record is
what makes a second day different from the first.

| failure | immediate | what persists |
|---|---|---|
| caught without papers | held, fined, escorted to Downbelow | an entry on the card; the next check is stricter |
| arrested | brig → fine → release (G2's loop, and it must **close**) | tier drops one rung; some NPCs will not be seen with you |
| denounced | questioning; a Nightwatch scene | standing with FAC-04 up, standing with everyone it frightens down |
| debt | the ladder's bottom rung — bunk, dosshouse, casual labour | you are visible to the Broker, who now has an offer |
| **card revoked** | **the catastrophe** — tier 0, everything above forfeit | you are still on the station. You start climbing again, and people remember |

**Losing everything leaves you standing in Downbelow, not at a menu.** That is the whole
argument for the identicard as the stakes object, and it is why "what failure costs" has a
different answer here than in most games: it costs *time and standing*, which are the two things
a simulation of a living station can actually model.

## 6. WHAT IS CANON HERE, AND WHAT IS INVENTED

**Canon-constrained** (see `canon/00-MASTER.md`): the identicard exists and is required; customs
and immigration are EarthGov functions; Nightwatch exists, pays for denunciations, and rises
through Season 2–3; Downbelow holds an undocumented underclass; the brig exists; Starfury flight
requires certification; the Narn–Centauri war is escalating in the era lock.

**Invented here, authority 5** — each gets an `INV` entry when the code that needs it is built,
not before, so the reasoning lands beside the number:

| invention | what would overturn it |
|---|---|
| the five-tier ladder as *discrete card states* | any frame or line establishing a different B5 status taxonomy |
| 30 days as the visitor-visa term | a stated duration anywhere in canon |
| tier 3 splitting into trader **or** deputy | evidence the two are the same clearance |
| tier 4 (Starfury cert) being reachable by a civilian at all | canon requiring military commission — if so, tier 4 becomes contractor/courier flight and the ladder is unchanged |
| demotion-not-death as the failure model | nothing; this is a design choice and the owner may simply prefer otherwise |

## 7. HOW THIS IS GATED — so G0 is not prose

`MASTER-PLAN` A2 already supplies the proxies; this section only binds them to the design above,
and every one must be able to **fail on today's content**:

| claim from this document | gate | red today? |
|---|---|---|
| the ladder is real | all five tiers reachable in one headless run; each rung's gate refuses tier−1 | **yes** — the ladder exists as data, not as a climb |
| failure demotes rather than ends | arrest → brig → fine → release closes, and tier is one lower after | **yes** — G2 unbuilt |
| the antagonists act without you | the **absence gate**: a player-absent day ≠ a player-present day in the same seed | **yes** |
| the station remembers | the **second-day gate**: day N ≠ day N+1 in *derived* facts, not scripts | **yes** |
| shortcuts cost standing | taking the Broker's offer measurably moves FAC standing and closes a tier-2 gate | **yes** — no standing scalar exists (CAST-05) |
| ≥3 roles pay | work → pay → spend closes for three roles | **yes** — 1 of 12 (VRB-07) |

**Every row is red.** That is the correct state for a design document written before its phase,
and it is the point: P1 is now something that can *fail*, which it could not be while it was four
bullet points in a plan. Nothing in §7 may be marked green by editing §7.

---

*Written session 4t, against `MASTER-PLAN` P1/G0 and A2. The owner is hands-off until ship and
has not seen it; §2's rejected list and §6's invention table are where to look first if it is
wrong.*
