# THE CONNECTED STATION — the plan that replaces every plan in this repository

---

## SESSION 4g — WHAT WILL EXIST WHEN THIS SESSION ENDS

Set by the owner: *"I want the entire station built and walkable and connected with working
transport … all the decks and all the levels and all the transports and all the locations,
actually built in Godot not theoretical."* This is the commitment, and each line is a thing that
either exists or does not — no partial credit, no coverage percentage.

| # | Deliverable | Gate that proves it | Owner |
|---|---|---|---|
| **1** | **`routes.py` components 85 → 1.** The station is ONE walkable piece | `routes.py --selftest` goes green | main |
| **2** | **The corridor arc comes from the RING, not from where the rooms happen to be** — this alone unblocks 18 of the 25 axial joins | axial buildable 7/25 → ~25/25 | main |
| **3** | **Transit nodes.** The graph gets nodes on decks that carry no location, because a route passes through places nobody lives | components with every edge 23 → 1 | main |
| **4** | **`station/lift.py`** — shaft, car, landing doors, collision. The vertical connection that has never existed in this project. 38 missing edges | 0 open edges; a floor in the car at every deck; landing aperture crossable, with the sealed control firing | agent |
| **5** | **Walkable spoke passages** — the radial connection between rings, inside the gauge `spoke_portal` already cuts | spoke buildable 0/7 → 7/7 | main |
| **6** | **Axial trunks between sectors** | trunk 4/4, and the sectors are one component | main |
| **7** | **Streaming in `walk.gd`** — cells load and free by player position, no loading screen | a body walks across a cell boundary, metres traversed reported, `offfloor=0`, and a control with streaming off that FAILS at the boundary | agent |
| **8** | **Transport that moves and can be ridden** — the guideway tram and the core shuttle. `tram.guideway_cars` already takes a `phase` that walks the train along the run; `transit.py` already owns every ride time. What is missing is motion at runtime and a floor to stand on inside the car | a body boards, rides, and alights in a different cluster without leaving the floor | main |
| **9** | **The whole station exported** — every deck, every cluster, as streamable cells | the count of cells written, against the 251 decks the schema declares | main |
| **10** | **AAA on the surfaces you see everywhere** — the corridor kit, the lift interior, the transit car interior | craft scored at the rubric's HALF distance in a Vulkan Forward+ frame | main |

### Why 10 is the honest lever on "it must not look like bare garbage"

**Every one of the 251 decks is built from ONE corridor kit.** A craft pass on
`interior_kit.corridor_section` is a craft pass on the entire station at once — the same is true of
the lift interior and the transit car, which is what a player looks at for most of any journey.
That is where the craft budget buys the most surface per hour by an enormous margin, and it is why
it is on this list rather than a per-location sweep.

### Stated plainly, because pretending otherwise is what this project keeps being punished for

**Bespoke craft on all 128 locations is not a one-session job and will not be claimed as one.** The
measured rate is four landmarks raised from craft 1 to craft 2–3 in one 70-minute agent session.
What this session delivers is a station you can walk end to end, with working transport, whose
*shared* surfaces are at the standard; the per-location passes continue after it, ordered by the
routes, exactly as PART 3 sets out. Any other claim would be another coverage number that means
nothing to a player.

---

**Session 4g. Written on the owner's instruction to override every plan here, audit them, and
replace them — then corrected by the owner's second instruction, which was right and which this
document now takes as its objective:**

> *"a 1:1 babylon 5 station, not the intro to a game that takes place all in one hallway … I feel
> like we should have made the entire goddamn ship walkable by now with every deck and everything
> already built and I just don't understand why I can't walk the whole ship yet."*

The first draft of this document scoped down to a twenty-minute slice. That was wrong for this
project and it is struck. **The objective is the whole ship, walkable.** What follows is why it
isn't, what it costs from here, and the order.

---

## PART 1 — THE NUMBER THAT SHOULD HAVE BEEN THE HEADLINE ALL ALONG

    128 locations  ->  96 foot-connected components
       74 components hold exactly ONE location
       the largest walkable piece of Babylon 5 holds SIX

That is the honest replacement for *"128 of 128 locations"*. Both are computed from the same data.
One of them is what a player experiences.

**A component is a set of places you can walk between.** Today a component is exactly one
z-cluster — one 40 m slice of one deck of one ring of one sector — because nothing joins two of
them. 251 decks exist. 96 islands.

### Why. Four mechanical reasons, in order of cost.

**1. Every corridor on this station was a run at FIXED z.** `interior.ring_arc` sweeps a corridor
around the axis at one z and that is the only corridor generator this project had. A deck spans
1,120 m of axis — `blue/0/0` carries six clusters over that span — and its ring serves one 40 m
slice. **`interior.axial_run`, the first corridor that runs along the ship, was written this
session.** Until today there was no geometry in the project capable of connecting two clusters, and
`build_deck_clusters` said so in as many words.

**2. There is no lift, stair or shaft anywhere in the project.** Not one. Meanwhile:

* `station/transit.py` computes how long a lift ride takes;
* `station/npc/navigation.py` derives the lift ride, the axial ride and the dwell for pathfinding;
* `station/core_tube.py` and `station/tram.py` build a transit tube and a tram car **with no motion
  in them at all**.

**The simulation has lift rides and the station has no lift you can walk into.** A ring is a dozen
decks stacked in radius; there is no way between two of them.

**3. `walk.gd` loads one `.glb` whole, and nothing ever asked it to load two.** No streaming, no
cell residency, no hand-off.

**4. No gate could ever fail for any of the above.** `directory.py` counts places. `deck.py
--sweep` counts places-on-clusters. `walkable.py` walks *within* one build. **There is no object in
this codebase that represents "you can get from here to there."** Every plan document in `docs/`
has a table of places; not one has a table of connections. The gazetteer is a list of
*destinations*, the plans were organised around it, and the *routes* were never anybody's job.

### The reframe that makes this tractable

**"Walk the whole ship" is not "furnish 73,635 bays." It is "the circulation network is complete
and streamed."**

A station is mostly corridor. Corridors are procedural and this project generates them well and
cheaply — 400 tri/m, a collision shell at 0.56–1.5% of that. The expensive content is the *rooms*,
and rooms are behind doors. **You can walk the whole ship the moment the corridors join and the
doors lead somewhere**, with the 128 built locations opening off them and the rest opening onto
generic bays. Furnishing continues behind that, forever, along the routes people actually walk.

This is why the 0.17%-of-footprint number, while true, is not the blocker it looks like. It is a
statement about *interiors*. Connectivity is a statement about *corridors*.

---

## PART 2 — THE OBJECTIVE, AND THE ONE NUMBER IT IS MEASURED BY

> **One continuous walkable station. Any point to any other point, on foot, without a loading
> screen.**

    FOOT-CONNECTED COMPONENTS:  96  ->  1

That is the gate. It is cheap to compute, it cannot be gamed by coverage, it fails today, and it
reaches 1 only when the ship is genuinely one place. **It replaces `deck.py --sweep`'s 128/128 as
this project's headline number**, and `--sweep` stays as a report.

### The R-track. Each milestone is a drop in that number.

| R | Milestone | Done when | Components |
|---|---|---|---|
| **R0** | **The number exists** | `station/routes.py` builds the station's circulation graph and reports components; it runs in CI and it is red | **96**, baseline |
| **R1** | **A deck is one place** | every z-cluster of a deck joined by an axial spine. The generator landed this session; this is rolling it over all 251 decks | ~96 → ~70 |
| **R2** | **A ring is one place** | decks within a ring joined vertically. **This needs a generator that does not exist: a lift shaft, its car, its landing doors, and its collision** | ~70 → ~30 |
| **R3** | **A sector is one place** | rings joined radially through the spokes. `interior.spoke` already builds the structure and `spoke_portal` already cuts an opening for the tram — a walkable passage goes in the same gauge | ~30 → 5 |
| **R4** | **The station is one place** | sectors joined along the axis; the drum reached through its spoke transit | 5 → **1** |
| **R5** | **And you can actually walk it** | streaming: cells load and free by player position, `walk.gd` holds more than one file, no loading screen | **1, continuously** |
| **R6** | **At frame rate** | LOD and occlusion so a streamed world holds 60 fps. Occlusion is half built (`occluders.py`); LOD exists for the crowd and not for structure | 1, at 60 |

**R5 and R6 are not "after" — they run alongside from R2 onward**, because a station that is one
component and cannot be loaded is the same lie in a different denominator.

### What each R actually costs, honestly

| R | Work | Exists already | Estimate |
|---|---|---|---|
| R0 | the graph + the gate | nothing — but it is a graph over `directory.PLACES`, not geometry | **2 hours** |
| R1 | batch the axial spine over 251 decks; handle decks whose cluster arcs do not overlap | `interior.axial_run`, `collision.axial_shell`, `build_deck_clusters(join=True)` — all landed today | **half a day** |
| R2 | lift shaft + car + landing doors + collision + the deck apertures | nothing. `DECK_PITCH_M` sets the rise; `transit.py` already owns the ride time | **a day** |
| R3 | walkable passage inside the spokes | `interior.spoke`, `spoke_portal`, `GUIDEWAY_GAUGE_*` | **half a day** |
| R4 | axial trunks across sector boundaries | same generator as R1 | **2 hours** |
| R5 | cell residency in GDScript; export every cell | `walk.gd` already loads a glb at runtime; `navigation` already has a cell notion | **a day**, plus hours of machine time |
| R6 | finish `occluders.py`; structure LOD | occluders red at 6/7 with the diagnosis written; crowd LOD ships | **a day** |

**That is four to five days of focused work, not two.** Saying so is the point of an estimate. The
ordering below is arranged so that whatever lands is the most valuable subset, and so that the
component count drops every single day.

---

## PART 3 — WHAT IS *NOT* DROPPED, AND HOW IT RUNS ALONGSIDE

The first draft of this plan cut the station down to one slice. That was the wrong instinct and the
owner overruled it. The 1:1 station **is** the project. But the ordering rule changes:

> **A room nobody can walk to is a screenshot. Connect first; furnish along the route.**

So the craft, materials, props, NPC and audio work all continue — **ordered by the routes**, not by
the gazetteer's index. A location gets its craft pass when it is on a walkable route, in the order
a player would meet it. That is the same instinct as the show's own ranked list and it replaces
"iterate the 128 in order".

**The three tracks, running together:**

| track | what it is | ordering rule |
|---|---|---|
| **R — routes** | the circulation network, streamed, at frame rate | the component count, 96 → 1 |
| **C — craft** | materials, lighting, props, density, judged frames | **along the routes**, authority-1 first |
| **L — life** | the clock, crowds, dialogue, interaction, audio, the player | **whatever the player meets on the routes** |

### And the L-track has a debt to pay off first, which is nearly free

**2,630 lines of finished, tested GDScript are unreachable from anything.**

| script | lines | what it is | referenced by |
|---|---|---|---|
| `life.gd` | 917 | the station clock and the people who live by it — **and it `extends SceneTree`**, so it is a headless tool, not a runtime system | nothing |
| `ambience.gd` | 437 | all of layer 7's audio, 13 loop-exact WAVs, `audio.py` 100/100 | nothing |
| `starfury.gd` | 1,276 | the flyable Starfury | its own scene, which nothing references |

And `project.godot` ships `main_scene = exterior.tscn`, a scene whose only script is
`render_shot.gd` — **a screenshot tool. Every game script in the project, 7,534 lines, is
unreachable from the scene it ships.** There is no build to hand anybody; everything playable is
launched by a developer typing a `--glb=` path.

This is the **third** recurrence of a failure already written up twice in this repository
(`station/npc/`'s twelve modules with zero importers; `npc/animation.py` with no importer). It
survives because **every gate here is a module self-test, and a module self-test passes whether or
not anything calls it.**

Wiring these is hours, not days, and it turns the station's clock, its crowds and its sound on.

---

## PART 4 — THE ORDER OF WORK

Arranged so the component count falls every day and nothing already built stays dark.

**Day 1 — make the failure visible, then halve it.**
* **R0** `station/routes.py`: the circulation graph, the component count, in CI, red at 96.
* **R1** roll the axial spine over every multi-cluster deck.
* **L-debt** wire `life.gd` (recast from `SceneTree` to a runtime node) and `ambience.gd`; give the
  project a `main_scene` that is a game and not a screenshot tool. A few hours, and the station
  gains a clock, a moving crowd and sound.

**Day 2 — the missing generator.**
* **R2** the lift: shaft, car, landing doors, collision, deck apertures. This is the single largest
  hole in the station and the one nothing else can route around. A ring becomes one place.

**Day 3 — close the graph.**
* **R3** walkable spoke passages; **R4** axial trunks across sectors and the drum's spoke transit.
* **Components reach 1.** At the end of this day the answer to *"can I walk the whole ship"* is yes
  in geometry, and no in the engine, and the gate says which.

**Day 4 — make the engine able to hold it.**
* **R5** streaming: cell residency in `walk.gd`, export every cell.
* **R6** finish `occluders.py`, structure LOD.
* This is where *"walk the whole ship"* becomes literally true.

**Continuously, alongside, never blocking the above:**
* **C-track** craft passes along the routes, authority-1 first.
* **L-track** dialogue, interaction and NPC behaviour on what the routes pass through.

---

## PART 5 — THE GATES

Four new gates. Every one **fails today**, which is the test of whether a gate is real.

| | gate | asserts | fails today |
|---|---|---|---|
| **G1 CONNECTED** | `routes.py` | the station's circulation graph; components must reach 1 | **96 components, 74 of them singletons** |
| **G2 ROUTE WALKED** | `walkable.py --route A B` | a body walks from A to B, metres covered, frames off-floor, and **fails if it stops** | no route between any two clusters exists to walk |
| **G3 NOTHING UNREACHABLE** | static reachability over `godot/scripts/*.gd` from `main_scene` | any game script with zero inbound references fails | **11 scripts, 7,534 lines** |
| **G4 THE FRAME ON A ROUTE** | budget measured at the eye positions a route actually visits, with streaming residency | never measured | — |

**This deliberately overrides session 4d's "no new gates" ruling, and here is why that ruling was
right and this still overrides it:** 4d was refusing *coverage* gates — more things counted. These
four are *integration* gates. They exist precisely because 36 green module self-tests sit on a
station in 96 pieces that cannot be started.

---

## PART 6 — WHAT THIS SUPERSEDES

1. **The eight-layer plan is struck as an ordering rule.** Demoted twice already and still steering
   work. Its layer *definitions* survive as vocabulary for describing one location's state; the
   table of counts does not.
2. **The W-track is closed and W6 is marked FALSE.** *"Roll W3–W5 outward across the 128"* was
   satisfied by a coverage count over a station in 96 pieces.
3. **`MASTER-PLAN` M0–M11 becomes the post-connection backlog.** It is a good document about the
   eventual game and it is not an ordering rule.
4. **`SHIP-PLAN`'s own first draft — the twenty-minute slice — is struck.** The slice is a useful
   *proof* of R5 and it is not the product.
5. **A plan item is a player minute or a route, never a subsystem.** *"Build X"* gets rewritten as
   *"the player can get from A to B"* or *"the player does Y"*, or it is not in the plan.
6. **A module is not done until something reachable from `main_scene` calls it.** G3 enforces it —
   the one rule that would have prevented the 2,630 dead lines all three times it has happened.
