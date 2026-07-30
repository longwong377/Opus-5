# The plan to a playable, populated station — session 3u

## The one fact this plan is built on

Every hard part is already written and **nothing calls it**.

| module | what it already does | importers outside its own directory |
|---|---|---|
| `npc/body.py` | `build(species, id)` → **a 4,560-triangle body, 1.72 m tall** | **0** |
| `npc/schedule.py` | `census(species, hour)` → who is working, resting, eating, *by hour* | **0** |
| `npc/crowd.py` | `Person`, density, `alienness` ranking | **0** |
| `npc/navigation.py` | `NavGraph`, `NavPoly`, `GroundNav` | **0** |
| `npc/animation.py` | `Rig`, `Skeleton`, `Clip`, `apply_pose` | **0** |
| `npc/costume.py` | `Costume`, `Fabric`, `Decal` per role | **0** |
| `physics/rotating_frame.py`, `floating_origin.py` | the drum's spin frame, 8 km precision | **0** |

Seven modules, 226 callables, ~3,000 passing assertions, wired to nothing. **Today is an
integration sprint, not a build sprint.** That is why a populated station is achievable in a day
when "AAA quality" is not.

## What changed in the plan, and why

The old rule — one layer at a time across all 118 locations — is eight horizontal slices, and a
horizontal slice cannot be walked in. It has been replaced (`CLAUDE.md`) by: **the build is always
walkable, and integration is a gate rather than a phase.**

The second change is the unit of work. **The deck, not the room.** 118 separate `.glb` files is a
museum of rooms; a deck is a ring corridor with rooms off it, and that is a place. Shipping decks
is what turns a location list into a station.

## The four builds, each playable

### B1 — POPULATED (the explicit ask)
`station/populace.py`, built exactly like `station/dressing.py` and for the same reason: one
generator, all 118 locations.

**The inventive part, and it reuses machinery that already exists.** `dressing.py` finds surfaces
by *reading them back off the geometry* — that is how clutter lands on tabletops without a second
list to keep in step. The same read finds **seats and consoles**, so people are placed AT things:
seated at a table, standing at a console, leaning on a counter, waiting in the lane. That is the
difference between "a room with people in it" and "people using a room", and it costs one function.

- `schedule.census(species, hour)` decides *how many* and *doing what* — so **the same generator
  gives a different station at 0300 than at 1300, for free.** A shift change is a parameter.
- `body.build(species, id)` gives the mesh; `costume.py` gives the role's clothing.
- Poses first, walk cycles later: `animation.apply_pose` on a static rig reads as a populated
  station in a frame and costs nothing at runtime.
- Density from `crowd.py`, capped by the same walkability trial the dressing uses — **an NPC that
  blocks a doorway is a bug, and `walkable.py` already fails on it.**

### B2 — CONNECTED
`interior.deck_cell()` already generates ring corridors and nothing assembles them. Emit **one
`.glb` per deck**: the ring, the rooms opening off it, doorways cut where they meet. Then
`walkable.py` gets its second question — not "can I walk in this room" but **"can I walk from this
room to that one"**, which is the assertion that makes it a station.

### B3 — LAUNCHABLE
One command, one window, spawn on a real deck. `walk.tscn` already loads any `.glb` at runtime with
trimesh collision, so this is a manifest and a spawn point, not an engine.

### B4 — ALIVE
The cheapest possible loop that is a simulation rather than a diorama: NPCs walking the nav graph
between the places their schedule sends them. `navigation.py` is written. The station stops being a
photograph.

## What I will not claim

A day does not produce Starfield. That is a studio-decade, and the honest gap is not geometry — it
is **art direction, signage, wear, and hand-authored moments**, none of which a generator invents.

What a day *can* produce, and what these four builds are aimed at: **a station you launch, spawn
in, walk through, and find full of objects and people who are doing things.** That is the thing
that does not exist yet, and everything needed for it is already written.

## The standing correction

The craft review scored **craft 1, performance 1** — "a gate exists and does not measure the thing
it names. Worse than 0, because it prints PASS." Two gates were certifying geometry the exporter
discards; one is fixed and layer 2 honestly reads 113/118, not 118. **Populating a station whose
gates lie is how the last three days happened.** Every build above lands with the gate that can
fail on it, and no number gets reported that a render does not support.
