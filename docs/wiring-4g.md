# Session 4g — THE PROJECT NOW HAS A FRONT DOOR

    before:  godot --path godot   ->  "render_shot: --scene-json is required", exit 2
    after:   godot --path godot   ->  a player standing in Blue 0 deck 0, HUD up,
                                      clock running, 73 residents keeping a day,
                                      the customs hall audible, in 6.3 seconds

`project.godot` shipped `run/main_scene="res://scenes/exterior.tscn"`. That scene
references exactly one script — `render_shot.gd`, a **screenshot tool**. Every
game script in the project was unreachable from the scene it shipped: **15
scripts, 10,170 lines**, including the station clock, all of layer 7's audio and
the flyable Starfury. There was no way to start it.

This is the **third** recurrence of one failure already written up twice in
`CLAUDE.md` (`station/npc/`'s twelve modules with zero importers;
`npc/animation.py` with no importer). It survives because **every gate in this
repository is a module self-test, and a module self-test passes whether or not
anything calls it.** `station/audio.py` scored 100/100 and no sound had ever
played.

---

## 1. WHAT WAS BUILT

| file | what it is |
|---|---|
| `godot/scenes/main.tscn` | the scene this project ships. As empty as `walk.tscn` and for the same reason |
| `godot/scripts/main.gd` | the entry point. Drives `walk.tscn`, starts the clock, starts the sound, and verifies itself when headless |
| `godot/project.godot` | `run/main_scene` → `res://scenes/main.tscn` |
| `station/coldstart.py` | **G1 COLD START** and **G3 NOTHING UNREACHABLE**, both headless, both with controls that fire |

`main.gd` **drives, it does not duplicate.** Loading a deck, colliding it,
dressing it out of `interior.tscn`, wiring the doors, the crowd, the
interactables, the dialogue and the HUD, and standing a `player.gd` body on the
floor is all `walk.gd`'s job and none of it is repeated: `main.gd` instantiates
`res://scenes/walk.tscn` and sets its exported properties, exactly as a
developer's command line does. Four modes:

    godot --path godot                      # station  -- the walkable build
    godot --path godot -- --mode=arrival    # arrival  -- the player's first ten minutes
    godot --path godot -- --mode=starfury   # starfury -- fly one
    godot --path godot -- --mode=transit    # transit  -- the lift and the tram

All four were run headless and all four boot. `--mode=transit` reports
`no transit manifest ... run python3 station/transit_runtime.py --build` and
exits 2, which is the honest state and not a silent empty scene.

### The world it boots into is not written down in `main.gd`

`station/arrival.py --build` already writes a sidecar carrying the mesh, the
collision shell, the interactables, the cast **and a spawn point a body can
stand on**, together, because they are one decision:

```json
"build": {"glb": ".../blue_0_0_z7440.glb", "collision": ".../blue_0_0_z7440_col.glb",
          "interact": "...", "actors": "...",
          "spawn": [162.0015, 135.9354, 7464.48], "spawn_at": "customs_north",
          "rooms": ["customs_north", "arrival_concourse", "customs_south"]}
```

`main.gd` reads that block. A spawn constant in `main.gd` would be a second
description of where the floor is, and `arrival.tscn`'s own header records what
that costs: its first run was handed `--spawn=0,0,0`, which on a ring deck at
radius 211 m is the **spin axis**, and the body fell for two minutes.

**This is a borrowed manifest and it should eventually be its own.** The boot
block belongs beside the deck the exporter writes, not inside an arrival
sequence. `--boot=<json>` takes any file of the same shape, so the fix is one
generator writing `build` into a `boot.json`; nothing in `main.gd` changes.

---

## 2. WHAT THE CLOCK DOES IN A LIVE BUILD

`life.gd` is `extends SceneTree` — a headless harness launched with `--script`,
which is exactly why 917 lines had no importer. It is **not recast**, and that is
deliberate: `--script res://scripts/life.gd -- --life-test` is the purity gate
(03:00 → 08:00 → 13:00 → 03:00, compared transform by transform against an
integrating control that drifts and cannot get back), and rewriting the file to
be a Node would have taken that gate with it. Its `Director` and `Clock` are
inner classes and its own header documents this exact call sequence; what was
missing was a node in a live build to make it. `main.gd::_start_clock` is that
node.

Measured in the shipped build, not in a harness:

```
life: clock started at 18.18 EMT, 0.017 station hours per real second; 73 of 73 residents bound
life: 03:00 -> 29 present, 13:00 -> 73 present, of 73 bound (the same cast, read at two hours)
```

The 29-vs-73 read is taken **before** `Director.watch(player)` is attached, on
purpose: `_may_pop` holds a presence change back inside the player's hold radius,
which is right in front of a person and wrong for a measurement.

**The clock also drives the sound.** `ambience.gd` reads its own `hour` property
and *nothing advanced it* — the mixer would have held the boot hour for ever
while the crowd thinned out around the player. `main.gd::_process` pushes
`clock.hour()` into it every frame. Proof, same build, one flag apart:

| | `--hour=11 --rate=0` | `--hour=11 --rate=1.0` |
|---|---|---|
| clock | 11.00 → 11.00, `clock_advanced=false` | 12.99 → **13.99** |
| traffic layer | −63.9 dBFS | **−67.7 dBFS** |
| tannoy | "ACHILLES-TYPE FREIGHTER NOW ARRIVING" | "TIME ON B-5 IS EARTH MEAN TIME (EMT)" |

### What does NOT run yet

* **Nobody walks.** All 73 residents baked into `blue_0_0_z7440` are `pose:
  standing`; there is no `_crowd.json` beside this deck, so the corridor flow
  `Director.apply` implements (bearing advanced at the body's own walking speed)
  has nothing bound to it here. The code path is live and untested on this deck.
  Rebuilding the deck with a crowd needs `deck.py`, which this session was told
  not to run.
* **Presence changes are the only visible response.** People appear and vanish as
  their place's 24-hour curve crosses their rank. Nobody walks to work.

---

## 3. WHAT YOU CAN HEAR

`station/audio.py` derives seven layers per place per hour, each with a level in
dBA and the reason it is that level, and writes 13 loop-exact WAVs (5.7 MB). The
gate reads 100/100. **None of it had ever played**, because `ambience.gd` had
zero inbound references.

Standing at the boot spawn, customs hall north, one line per hour, same build:

```
[hour=03] layers=3 emitters=6 pa="IN-SYSTEM SHUTTLE NOW ARRIVING, docking "
          [air:air_duct -75.3, crowd:crowd_sparse -73.0, traffic:crowd_babble -74.3]
[hour=09] layers=3 emitters=6 pa="ACHILLES-TYPE FREIGHTER NOW ARRIVING, do"
          [air:air_duct -75.3, crowd:crowd_sparse -67.2, traffic:crowd_babble -70.8]
[hour=13] layers=3 emitters=6 pa="IN-SYSTEM SHUTTLE NOW ARRIVING, docking "
          [air:air_duct -75.3, crowd:crowd_babble -61.2, traffic:crowd_babble -71.8]
[hour=20] layers=3 emitters=6 pa="UNITED SPACEWAYS TRANSPORT NOW ARRIVING,"
          [air:air_duct -75.3, crowd:crowd_sparse -70.2, traffic:crowd_babble -71.0]
```

Three things in that table are worth reading:

1. **The crowd layer swings 11.8 dB** across the day, 03:00 to 13:00, and at
   13:00 the *stream itself changes* — the sparse night murmur becomes
   `crowd_babble`. That is the customs hall filling up, mixed from
   `populace.occupancy` × `schedule.awake_fraction`.
2. **`air:air_duct` is −75.3 dB at every hour.** That is the control. Air does
   not care what time it is, and a bed that moved everything at once would be a
   gain, not a simulation.
3. **The tannoy speaks a different arrival each hour**, era-locked through
   `costume.ERA_EVENTS`, fired as a one-shot inside `broadcast`'s own
   quarter-hour audibility window.

Six 3D emitters are placed off the geometry (`fix_*` matches from the bank's own
rules) and capped at the nearest 24.

**Not done, and none of it is this session's:** reverb zones, occlusion (a shut
door does not muffle), event audio beyond the chime, and no absolute level is
referenced to anything — INV-260..264, all authority 5.

---

## 4. THE GATES

`python3 station/coldstart.py` runs both, plus three controls. **Exit 1 if either
fails.** ~30 s total, four engine launches.

### G1 COLD START

Launches the shipped scene with **no arguments at all** — not a scene path, not a
`--`, not one `--glb=`. `--headless` is the container having no display, not a
mode: `main.gd` sees a headless display server, checks itself and quits, because
nobody is at the keyboard and a build nobody can start is the thing being caught.

```
COLDSTART scene=res://scenes/main.tscn mode=station player=1 on_floor=true
  drop_m=0.043 hud=1 hud_place=corridor h0=18.21 h1=18.22 clock_advanced=true
  bodies=73 present_0300=29 present_1300=73 audio_layers=3
  audio_place=customs_north boot_s=5.2
```

Ten assertions: a player exists, it is standing on a floor, it did not fall
through (0.043 m ≤ 0.30 m, measured **radially** because on a spun deck "down" is
outward), there is a HUD, the HUD reads the world, the clock is advancing, the
crowd is bound, 03:00 and 13:00 differ, the station is audible, and it was cold
in 6.2 s.

**`BOOT_BUDGET_S = 30`, and the number is derived rather than discovered.** The
boot measures 6.3 s on this four-core box — 65 MB of glTF parsed, 509 mesh groups
materialled, 561 lights made, a collision proxy trimeshed, 73 residents bound, 13
audio streams loaded — and the budget is 5×, which absorbs a loaded machine and
still fails the regression that matters. Trimeshing the 509 *visual* meshes
instead of the 4-mesh proxy is the obvious way to break this and it costs
minutes, not seconds. A budget of 150 s could not fail, which is the same defect
wearing a bigger number.

**Three controls, run in the default pass, each must fail on exactly its own
check:**

| flag | fails on | whose flag |
|---|---|---|
| `--no-hud` | `hud`, `hud_reads` | `walk.gd`'s own, not one written for this gate |
| `--no-clock` | `clock`, `bodies`, `day` | `main.gd` |
| `--no-sound` | `audio` | `main.gd` |

All three fire on exactly the expected set and nothing else. `--rate=0` is a
fourth: it freezes the clock and `clock_advanced` goes false.

### G3 NOTHING UNREACHABLE

Static reachability over `godot/scripts/*.gd` from `run/main_scene`, comments
stripped — **a docstring is not a reference**, and this gate is worthless without
that distinction: `life.gd`'s own header contains
`var L := preload("res://scripts/life.gd")` as usage documentation and
`arrival.tscn` carries the command line that runs it, so a grep over raw source
calls both of those live edges and reports a wired station.

    BEFORE   16 scripts:  1 reachable, 1 exempt, 14 UNREACHABLE  (9,630 lines)
    AFTER    18 scripts: 16 reachable, 2 exempt,  0 UNREACHABLE

The BEFORE list, verbatim, from `res://scenes/exterior.tscn`:

    starfury.gd 1276, walk.gd 1100, stream.gd 983, life.gd 917, dialogue.gd 912,
    transit.gd 845, hud.gd 608, arrival.gd 592, interact.gd 574, npc.gd 570,
    dress_scene.gd 499, ambience.gd 437, player.gd 180, door.gd 137

That walk is kept as G3's **permanent negative control**: `g3(from_scene=
CONTROL_SCENE)` re-runs it from the scene that shipped before this session and
must come back red. It does — 15 scripts, 10,170 lines — so the evidence lives in
the repository rather than in a session log.

#### The exemption list is written out by name, and that is a decision

`render_shot.gd`, `verify_materials.gd` and `route_test.gd` are offline
harnesses: each is launched by a driver that names its own scene or script, so
being unreachable from `main_scene` is correct for them.

**The obvious improvement — exempt anything a Python driver launches — was
written first and then struck.** `station/starfury_scene.py` names
`res://scenes/starfury.tscn` and `station/walkable.py` names
`res://scenes/walk.tscn`, so under that rule the flyable Starfury and the entire
walkable build become exempt and G3 goes green on **exactly the defect it exists
to catch**. A derived rule blind to the original bug is worse than a list
somebody has to update: the list going stale turns the gate RED and costs a
two-minute decision. That happened within this session — another agent landed
`route_test.gd` (731 lines, the G2 harness) while G3 was being written, and the
gate correctly called it dead until the decision was made and written down.

`harness_drivers()` survives as a **diagnostic**: an unreachable script is
reported with the driver that does launch it, so the next reader makes that
decision in one line instead of going looking.

---

## 5. CHANGES I NEED IN FILES I DO NOT OWN

### 5.1 `.github/workflows/validate.yml` — add the two gates (nobody owns this; apply at integration)

Session 4e's finding stands: this workflow is a chain of steps and one failing
step used to blind the 34 behind it. Add these **with `continue-on-error: true`
and an outcome record**, exactly like the steps around them:

```yaml
      - name: Can anybody start it, and is any of it dead code
        id: coldstart
        continue-on-error: true
        run: python3 station/coldstart.py
```

`coldstart.py` exits 1 if either gate fails and 0 otherwise. It needs the Godot
binary the other engine steps already use; with no binary, G1 prints
`no double-precision Godot binary found` and fails rather than passing quietly.
G3 alone needs no engine at all — `python3 station/coldstart.py --g3` is ~0.2 s
and can run on any box:

```yaml
      - name: Nothing unreachable (no engine needed)
        id: reachable
        continue-on-error: true
        run: python3 station/coldstart.py --g3
```

### 5.2 `godot/scripts/walk.gd` — no change needed, and this is worth recording

`main.gd` drives `walk.tscn` entirely through its existing `@export`s
(`glb_path`, `collision_path`, `spawn`, `gravity_mode`, `actors_path`,
`dialogue_path`, `crowd_path`, `interact_path`) and its existing `--no-hud`
control. **Nothing in `walk.gd` had to change to make the project startable**,
which says the file was always right and only ever lacked a caller.

One thing to be aware of if you touch `_wire_hud`: it returns early on
`walk-test` and `stream-test`, so G1 deliberately does **not** use either — the
cold start is a real boot, not a test mode, and that is what makes "there is a
HUD" checkable at all.

### 5.3 `STATE.md` — a section for the handoff (owned by the main agent)

Suggested text:

> **Session 4g — the project has a front door.** `run/main_scene` is
> `res://scenes/main.tscn`. `godot --path godot` with no arguments puts a player
> in Blue 0 deck 0 with a HUD, a running station clock and audible ambience, in
> 6.3 s. `station/coldstart.py` gates it: **G1** boots the shipped scene with no
> arguments and asserts player/floor/HUD/clock (three negative controls, all
> firing); **G3** is static reachability from `main_scene` and went **14
> unreachable scripts / 9,630 lines → 0**, with the old shipped scene kept as a
> permanent control. `life.gd` and `ambience.gd` are wired and running.
> Not done: no crowd walks on this deck (all 73 baked actors are `standing` and
> there is no `_crowd.json` beside it), and `--mode=transit` waits on
> `station/transit_runtime.py --build`.

---

## 6. THINGS FOUND IN READ-ONLY FILES

**None of these were fixed — they are in files this session does not own.**

1. **Two different answers to "which place am I standing in", and they disagree
   by 31.6 m.** At the boot spawn, `hud.gd` says `CORRIDOR (near CUSTOMS NORTH
   31.6 m)` and `ambience.gd` says `place=customs_north`. Neither is wrong on its
   own terms and that is the problem: `hud.gd::_where` builds its boxes from the
   **interact sidecar** (the extent of a place's usable props, ±1.5 m), while
   `ambience.gd::place_at` builds them from **every mesh named `<place>__*`**
   merged and grown 1.5 m. A customs hall's geometry reaches 30 m further than
   its props do. A player is therefore told they are in the corridor while
   hearing the room. One of these should derive from the other, or both from
   `directory.PLACES`' footprints.

2. **The Starfury airframe has no materials.** `--mode=starfury` prints
   `render_shot: fallback material used by 16 group(s): boom, boom_tip,
   canopy_frame, cockpit_canopy, cockpit_glazing, dorsal_deck, engine_bell,
   engine_pod, fuselage, gun_pod, nose, rcs_nozzle, rcs_sponson, retro_nozzle,
   root_fairing, tip_vane` — every visible surface of the fighter. The station
   hull beside it binds fine (41 instances). This is the same class of defect as
   session 4f's 45 unbound `dress_*` groups, and `materials.check_material_
   coverage()`'s derived vocabulary does not cover `starfury_scene.py`'s names.

3. **`life.gd`'s `Director` and `npc.gd` compose on the same transforms, and the
   file says so.** `Director.process_priority = 100` runs it after `npc.gd` and
   it writes origins while `npc.gd` writes its meshes' transforms to turn a body
   toward the player. A body that is both walking and being looked at turns about
   a pivot that lags its feet. Recorded in `life.gd`'s own header as a known
   interaction; it is now reachable in a live build, so it can actually happen.

4. **`ObjectDB instances leaked at exit`** on every headless quit. Pre-existing —
   the same warning appears on the walk tests — and cosmetic, but it is the kind
   of line that hides a real one.
