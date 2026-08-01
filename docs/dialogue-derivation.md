# Dialogue — a line is a view of the simulation

Session 4e. `station/dialogue.py`, `godot/scripts/dialogue.gd`.

## What this closed

`STATE.md`'s capability table read *"talk to anyone | **no** — there is no dialogue system
anywhere in the repository"*, and `station/interact.py` documented the hole from the other end.
It defines eight verbs and excludes three of them from `RESPONDS`, with the reason written out:

> `sit`, `rest` and `serve` are deliberately NOT here … being served needs whoever is behind the
> counter to turn round and **talk, which needs dialogue**.

So the station had 2,028 bodies, each with a name, a species, an origin, an age, a role, a job, a
home, a schedule, a costume and a nine-field identicard — and the whole player-facing consequence
of all of it was `npc.gd` turning their heads.

## The rule: derived, not written

This module is `station/broadcast.py` pointed at a person instead of a tannoy. It holds no
content of its own, so it cannot drift from the station.

| what a line knows | where it comes from |
|---|---|
| who they are — name, species, origin, role, job, home, visa | `npc/resident.py` |
| what they are doing at this hour, and **whose** hour it is | `npc/schedule.py` (`activity_at`, `RHYTHMS`, `work_window`) |
| whether they will speak to you at all | `npc/friction.py` + `docs/gazetteer/FACTIONS.md` §12 |
| an officer's own beat, and the force on duty | `npc/security.py` (`beat`, `on_duty`, `POSTS`) |
| which ship is in and how hard the hall is running | `station/traffic.py` (`arrivals`, `hall_rate`) |
| what the screens and the tannoy are saying here | `station/broadcast.py` (`audible_at`) |
| what has and has not happened yet | `npc/costume.py::ERA_EVENTS` |
| where a counter is and what verb it takes | `station/directory.py` + `station/interact.py` |

Every emitted `Line` carries a `source` string naming the call that produced its facts.
`--report` prints them under each line.

## Topic selection is a competition, scored off the simulation

Eleven topic functions read the world, return `None` when they do not apply, and score their own
salience. Where a number exists in the simulation, it **is** the salience:

```
   18.28  port     traffic.arrivals(0) + traffic.hall_rate(11.00) x9.7 + broadcast.SHIP_CALL['liner']
    1.40  news     broadcast.audible_at('customs_north', 11.00) -> minipax
    1.10  meal     npc/schedule.activity_at -> eat; RHYTHMS['human'].meals=(7.0, 12.5, 19.0)
    1.00  home     resident.home_for -> 'qtr_personnel'
    0.90  era      costume.ERA_EVENTS['markab_extinct'] active at (3, 5)
  -> drew [port]
```

That 18.28 is the customs hall running at **×9.7** the background rate because an Asimov-class
liner berthed twelve minutes ago with 689 aboard. On the same day of the week with no liner the
same officers at the same hour draw a different topic, and the control for it is in the self-test.

Where no simulation number exists, the topic takes a declared floor from `PERSONAL` (authority 5,
`INV-271`) — deliberately low, so anything happening on the station outranks anything happening in
a life. `DRAW_FLOOR = 0.55` admits the near-equals to a hash-weighted draw, so two people in one
room pick differently and both picks are deterministic.

## Phrasing is a register, from two tables asserted total and minimal

`_ROLE_REGISTER` has one row per `schedule.ROLES` key (19). `_SPECIES_VOICE` has one row per
species in `schedule.ROLE_WEIGHTS` (15). They give `formality` and `terseness`; the **voice band**
is a function of both — `formality − 0.5·terseness` — so a role and a species pulling in opposite
directions land in the middle instead of needing a row of their own. Three bands: formal, plain,
blunt.

Both tables are asserted the way `interact.py` asserts its verb tables:

* **TOTAL** — every key has a row, and no row names a key that does not exist.
* **MINIMAL** — neutralise any single row and a speaker in that cell speaks differently. 19/19
  role rows and 13/15 species rows. The two that do not are `human` and `other`, which carry
  `(0, 0)` **by design** — the human register is the reference the other fourteen are offsets
  from, and FACTIONS.md 9.2's tail bucket is not a species. The gate is `set(dead) <= {"human",
  "other"}`, so a *third* inert row fails it.

The minimality test runs against `_probe()`, a synthetic speaker in every cell of both tables.
The first version measured a sixteen-person roster sample and reported 18 of 19 role rows inert;
what it had actually measured was that fifteen roles never appeared in it. Security is 500 people
in 155,000.

## The five things it must vary by, and the control for each

| varies by | gate | control that fires |
|---|---|---|
| **species** | one id as five species gives ≥4 distinct exchanges | flatten `_SPECIES_VOICE` → 15 species in one role fall from 3 bands to 1 |
| **role** | different roles in one room give different lines | the minimality sweep, per row |
| **faction standing** | a Narn speaks to a human and **refuses** a Centauri | empty `friction.PAIRS` → the refusal stops |
| **era** | the same Narn differs at S2E01 and S3E05, and the ranking contains an `era` topic at the datum and none before it | the same datum twice → byte-identical |
| **what the station is doing** | the same officers at the same hour differ on a liner day | raise every `PERSONAL` floor above the events → the two days read the same |

Plus determinism: the module is re-run under `PYTHONHASHSEED=0` and `1` in a subprocess and the
outputs diffed. `blake2b` throughout, never `str.__hash__`.

**36/36, `python3 station/dialogue.py --selftest`, about 7 s.**

## What FACTIONS.md §12 actually says about silence

Two rows, and only two, describe **not speaking**: Narn ↔ Centauri (*"Neither speaks"*) and
Vorlon ↔ everyone (*"the corridor clears without being told to"*). Those produce a `refusal` —
an **action** line whose text is the gazetteer row's own `why` field, because inventing words for
a silence the source is explicit about is inventing the opposite of what is attested.

Everything milder is a **withheld greeting**: `warmth = 1 − (severity − 1)/5` off
`friction.SEVERITY`'s own separation ladder, and below 0.75 the hello does not happen and the
row's described behaviour appears in its place. That is §12's *"95% avoidance, 5% contact"* rule
expressed in a conversation.

### Two defects the join produced, both now commented in place

1. **The wildcard matched a job.** `("human", "*", "high", …)` is the human ↔ **alien** row.
   Offered `("human", "visitor")` it matches, because `visitor` is not `human` — so every human
   in the Zocalo refused to speak to a human player, sourced to a row about aliens. A `*` side
   must be filled by a **species**.
2. **`friction.pair` collapses before the filter can run.** It returns the strongest row, so a
   human meeting a telepath got the `("human", "*")` row — same severity, earlier in the table —
   and filtering it out afterwards left nothing. The Psi badge row FACTIONS.md calls High could
   never fire. `_rows()` scans `friction.PAIRS` with `friction._match` and filters *before*
   choosing, which is `pair()` minus the collapse.

## `serve` — the verb `interact.py` could not close

29 declared interactables across **27 register places** resolve to the verb `serve`.
`behind_counter()` answers who is standing behind one, from `resident.roster` — the same regulars
the room is already built with, filtered to the roles that serve — and `serve_response()` returns
their exchange.

```
zocalo           Nadia Sinclair  (merchant, market_stall)
earharts         Elizabeth Okoro (service,  bar_counter)
customs_north    Susan Alexander (customs,  customs_desk)
post_office      David Ramirez   (merchant, counter)
```

`interact.RESPONDS` still excludes `serve`, and the self-test asserts that it does — adding the
word is one edit in a file this session did not own, and this module is what earns it.

## The runtime

`godot/scripts/dialogue.gd`. Walk within `talk_m = 3.0` of somebody, look within 45° of them,
`[T]` opens the exchange and steps through it. `E` is `interact.gd`'s and is left alone: two
systems on one key would race each other in front of a manned counter, which is exactly where
both are true.

It holds **no line, no topic rule and no register table** — it reads `<deck>_dialogue.json`, joined
to `<deck>_actors.json` on the mesh group. The palette, the fade and the tracked-capitals
treatment are `load()`ed off `scripts/hud.gd`'s own constants rather than copied, and the gate
asserts the load succeeded, so a fallback to local colour literals fails the run.

### The headless gate, and the two defects it caught

`python3 station/dialogue.py --runtime-test` assembles a throwaway Godot project holding nothing
but the two scripts (**symlinked**, so a stale copy cannot pass for the shipped file) and a
one-node scene, runs it headless against the real deck's actors, and reads a verdict line:

```
live: people=73 opened=1 open_lines=2 shown=2 distinct=57 prompt_m=2.75
      far_prompt=false behind=false bad_range=0 bad_cone=0
      palette=res://scripts/hud.gd topic=era name=Amis_Alexander
control (--no-dialogue): people=0 opened=0 distinct=0 prompt_m=-1.00
```

It runs in its own project rather than in `godot/` for two reasons: in `godot/` the engine scans
and imports the whole project, which on the session this was written meant racing another agent's
`materials.py --export` through the same import cache — disjoint source files, one shared
artefact — and it takes minutes. The cost is stated: **this proves the script in isolation against
real data, not that it loads under the main project's settings.**

On its first run it found `class Panel extends Control` — `Panel` is a native Godot class, the
whole file failed to parse, and every call into it would have thrown. That is the same defect
CLAUDE.md records costing a session in `npc.gd`, and it is the entire argument for the harness.

Two further failures were the **harness's own** and are worth keeping:

* `prompt_m=12.00`, `behind=true` — the deck holds 73 people in two customs halls, so the approach
  path passed inside `talk_m` of somebody else the whole way. The scan was right; the harness was
  measuring the crowd. It now walks at the **most isolated** person and separately asserts the
  invariant (`bad_range`, `bad_cone`) over *every* offer made on the way in.
* the "facing away" control was aiming at `target − toward·40` while standing at `target +
  toward·1.2` — straight **through** the person.

## Frames

| file | what it is |
|---|---|
| `docs/engine-4e-dialogue.png` | the deck at the Zocalo, Vulkan 1.4 Forward+ / lavapipe, from `tools/render_godot.sh --shot deck --deck blue/0/0 --at zocalo`. No interface on it |
| `docs/engine-4e-dialogue-prompt.png` | the `[T] TALK TO BO ROSSI` offer |
| `docs/engine-4e-dialogue-panel.png` | the exchange, line 2 of 3 |

The two interface frames are **composites and are labelled as such**: the panel is drawn by Godot,
by `dialogue.gd`, through the same `CanvasItem` calls a player would see, at 1280×720, over a real
engine frame of the deck as a backdrop. Nothing in the shipped scene tree builds this node, because
`godot/scripts/walk.gd` was not this session's file to edit. They are evidence about the interface
and about nothing else.

## What is not done

* **Nothing instantiates `dialogue.gd` in the shipped build.** Wiring it is three lines in
  `walk.gd`, in the shape `_wire_people` already has:

  ```gdscript
  _talk = Node3D.new()
  _talk.set_script(load("res://scripts/dialogue.gd"))
  add_child(_talk); _talk.collect(actors, rows); _talk.watch(_player)
  ```

  plus `--dialogue=` alongside `--actors=` in `station/walkable.py`, which writes the actor
  sidecar and would write this one from `dialogue.write_sidecar`.
* **`interact.RESPONDS` does not list `serve`** — one word, same reason.
* The exchange is greeting / topic / farewell. There is no branching, no player choice and no
  memory between conversations. That is deliberate for now: `MASTER-PLAN.md` §3.2's warning about
  building behaviours before the verb set is known applies to conversation at least as hard.
* **`traffic.arrivals` has no memo and it costs 1.7 s a call.** Six exchanges took 7.06 s, of
  which the profile attributed 31 s of 31 s to `_inverse_curve` summing a 2,880-sample curve once
  per arrival. The proper fix is one `@lru_cache` in `station/traffic.py`; this module applies a
  caller-side memo instead, because that file was not this session's either. Six exchanges now
  take 0.75 s cold and 0.01 s warm.

## Inventions

`INV-270` the role register table · `INV-271` the personal salience floors and `DRAW_FLOOR` ·
`INV-272` the voice bands · `INV-273` the phrasings · `INV-274` `talk_m` and the 45° cone.
All authority 5. Everything inside a phrasing's braces is a number or a name this repository
computes.
