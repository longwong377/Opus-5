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

## 2b. THE FALSE RED, AND WHAT IT WAS HIDING

The coordinator caught `station/coldstart.py` reporting `audio_layers=0` in a
full run and `audio_layers=3` in `--g1` alone, on the same code and the same
box. **A gate that reports a false red is worse than no gate** — it trains a
reader to disbelieve every other number it prints — so this took priority over
everything else in this section.

### What I could and could not reproduce

**I could not reproduce it: 15 launches, all healthy** — 8 raw, 4 under an
attempted CPU load, 3 more via the same `subprocess.run` path the gate uses. The
`g3()`-runs-first correlation does not survive: `g3()` opens files read-only,
writes nothing, touches neither `godot/.godot/` nor the import cache, and a full
run passed on the next attempt. Saying so plainly rather than claiming a fix I
cannot demonstrate.

### What the arithmetic says, which is more useful than the repro

Every ambience layer started **20 dB below `silence_db`** and approached its
level with a 2.5 s time constant. `describe()` counts a layer only once its
fader is above `silence_db`, so at this deck's own bed levels:

| layer | target (fader dB) | crosses audibility at |
|---|---|---|
| crowd | −9.55 | **0.84 s** |
| traffic | −38.44 | **1.64 s** |
| air | −44.67 | **2.09 s** |
| structure | −57.67 | **5.65 s** |

`_coldstart()` sampled once at `settle_frames + clock_frames` = 180 physics
frames ≈ 3.0 s. So the verdict had **0.9 s of margin on `air`** and was reporting
a fader mid-fade as though it were a level. That is a race by construction
whatever perturbs it, which is exactly what the coordinator said.

**And it was not only a flaky gate — every audio number in §3 below was wrong.**
Sampling mid-fade meant the build reported **3 layers when the bed has 5**, and
the crowd layer 21 dB below its derived level. `structure` and `pa` were missing
from every measurement this session has published. The corrected table is in §3.

### Three fixes, in order of how much they matter

1. **`ambience.gd` no longer fades in from silence at boot.** The crossfade
   exists so that walking out of a bar into a corridor is smooth; at boot there
   is nothing to fade *from*, and a mixer that is measurably silent for the
   first two seconds of a build is wrong on its own terms. `_started` is false
   only on the first pass, so a bed learned later — a room you walk into — still
   arrives over `crossfade_s`. Snapping on scene entry is what a mixer does.
2. **The gate polls until the mixer settles instead of sampling once**, with a
   300-frame deadline, and reports `audio_ready_s`. It now reads **0.00 s**. A
   gate that is correct only because of a property of the thing it is gating is
   one refactor from lying again.
3. **A half-built mixer no longer looks like a switched-off one.** `load_bank`
   returning false used to leave the node in the tree with an empty bank:
   `_process` bailed on its first line, `_here` stayed `""`, and the verdict read
   `audio_layers=0 audio_place=-` — character for character what `--no-sound`
   prints. Two very different failures with one signature is how a reader spends
   an afternoon on the wrong hypothesis. It is freed, and `audio_why=` carries
   the reason into the verdict.

### And the gate now prints the engine's own account of a failure

This is the part I would keep if I could keep only one. `g1()` printed five
whitelisted line prefixes and dropped everything else, so a red run said
`FAIL the station is audible` and **nothing at all** about the
`ERROR: ambience: ...` line sitting in output it had already captured. `--verbose`
existed; needing a second run to find out what happened is exactly the friction
that stops anyone doing it. Any failed check now dumps the engine's `ERROR`,
`SCRIPT ERROR`, `ambience:`, `life:` and `hud:` lines automatically — visible in
all three control runs in §4.

---

## 2c. THE BOOT MANIFEST IS ITS OWN ARTEFACT NOW — `station/boot.py`

`main.gd` read its world out of `<deck>_arrival.json`, the sidecar
`station/arrival.py --build` writes for the player's first ten minutes. That made
the game's entry point a property of a narrative artefact: change which ship the
player arrives on and you change what `godot --path godot` opens, and deleting an
arrival sequence stopped the game booting at all.

`python3 station/boot.py` writes `station/generated/scene/boot.json`, and
**the spawn is derived from the floor rather than copied from anywhere.** That is
`station/collision.py`'s own rule one level up — it measures the corridor's
walking profile off the kit by ray casting "so it cannot drift from what it
stands in for". The shell's `collision` group is the surface a body walks on; a
ring deck is spun, so its floor is the outermost radius in that group; the body
stands `STAND_IN_M` inside it.

    boot: blue_0_0_z7440 -- spawn -53.200,204.672,7464.120 in corridor, 3 rooms;
          standing on 1 of 1122 floor triangles (of 4384 in the shell)
          at r=211.550, 105 deg
      derived   -53.200  204.672 7464.120   r=211.474
      arrival   162.002  135.935 7464.480   r=211.478
      they differ by 225.913 m along the corridor and 0.004 m in radius
      ok   the two agree on where the floor is

The cross-check is **evidence, not a source**: the two numbers are computed by
different code from different inputs, so agreeing to **4 mm in radius** is
meaningful and differing by 226 m *along* the corridor is not a disagreement —
where along an arc you stand is a choice, and the two make it differently on
purpose.

**The first version of this put the body in space, and the gate caught it in six
seconds.** It averaged the floor's vertices — but the centroid of an arc is
inside the circle it bends around, so the spawn landed 214 m from any built
floor. `coldstart.py --g1` came back `on_floor=false, drop_m=19.456` with the
radius climbing as the body fell outward. The fix is that a point ON a triangle
of the floor cannot be in the air, so the answer is now the real floor triangle
nearest the middle of the built arc. `boot.py` also asserts it, so the next
occurrence costs milliseconds instead of a build and a launch.

`main.gd` tries `--boot=` → `boot.json` → `*_arrival.json`, and says out loud
when it falls back. `station/generated/scene/` is gitignored, so **CI must run
`python3 station/boot.py` before `coldstart.py`** — or accept the fallback, which
still works. See §5.1.

---

## 2d. THE STARFURY IS NOT WHITE PLASTIC ANY MORE

All 16 sections of the airframe — `fuselage`, `nose`, `cockpit_glazing`,
`engine_bell`, every visible surface of the only flyable thing in the project —
resolved to no material and took `exterior.tscn`'s glTF fallback.

`starfury.gd` borrows `exterior.tscn`'s rules and calls its `_apply_materials` on
the fighter, so the fury's sections are exterior groups like any other. They now
bind to materials that already exist, rather than to new ones invented for them:

| sections | material | why |
|---|---|---|
| fuselage, dorsal_deck, nose, root_fairing, boom, boom_tip, engine_pod, gun_pod, rcs_sponson, tip_vane | `hull_exterior` | painted composite over structure, weathered — what the station's own plate is |
| engine_bell, retro_nozzle, rcs_nozzle | `structural_truss` | unpainted scorched metal, the darkest thing in the exterior set (V 0.204 against hull 0.44). A nozzle as bright as the airframe is the tell that a fighter was modelled as one lump |
| cockpit_glazing | `dome_glazing` | the same question this material already answers for the observation dome |
| cockpit_canopy, canopy_frame | `dome_structure` | the fighter's mullions: a pale plated collar around glazing |

`render_shot: fallback material used by 16 group(s)` → **the line is gone.**

**The structural half matters more than the binds.** `materials._selftest`'s
derived vocabulary is built from `rooms.FIXTURES`/`PLACE_FIXTURES`/`PROPS` ×
`dressing.MACHINES` — all interior — so it could only ever fail for something
*inside* the pressure hull, and the fighter was invisible to it. It now also
derives from `starfury_geometry.SECTIONS`, the airframe's own table, checked
against the `exterior` scene:

```
check("every Starfury airframe section resolves to an exterior material", ...)
```

Adding a section to the fighter now fails that rather than shipping a white one.
Verified with its control: all 16 resolve, and a name that does not exist
resolves to `None`. This is the same shape of miss as session 4f's 45 unbound
`dress_*` groups — **a coverage check is only as wide as its vocabulary, and the
part nobody wrote down is the part that breaks.**

---

## 3. WHAT YOU CAN HEAR

`station/audio.py` derives seven layers per place per hour, each with a level in
dBA and the reason it is that level, and writes 13 loop-exact WAVs (5.7 MB). The
gate reads 100/100. **None of it had ever played**, because `ambience.gd` had
zero inbound references.

Standing in the customs hall, one line per hour, same build. **These are the
corrected numbers** — everything published earlier in this session was a fader
caught mid-fade, three layers instead of five and the crowd 21 dB light. See
§2b.

```
[hour=03] layers=5 emitters=6 pa="IN-SYSTEM SHUTTLE NOW ARRIVING, docking "
   [air:air_duct -64.7, crowd:crowd_sparse -54.1, pa:pa_horn -79.7,
    structure:structure_hull -77.7, traffic:crowd_babble -63.2]
[hour=09] layers=5 emitters=6 pa="ACHILLES-TYPE FREIGHTER NOW ARRIVING, do"
   [air:air_duct -64.7, crowd:crowd_sparse -45.8, pa:pa_horn -79.7,
    structure:structure_hull -77.7, traffic:crowd_babble -58.2]
[hour=13] layers=5 emitters=6 pa="IN-SYSTEM SHUTTLE NOW ARRIVING, docking "
   [air:air_duct -64.7, crowd:crowd_babble -44.4, pa:pa_horn -79.7,
    structure:structure_hull -77.7, traffic:crowd_babble -59.6]
[hour=20] layers=5 emitters=6 pa="UNITED SPACEWAYS TRANSPORT NOW ARRIVING,"
   [air:air_duct -64.7, crowd:crowd_sparse -50.0, pa:pa_horn -79.7,
    structure:structure_hull -77.7, traffic:crowd_babble -58.4]
```

Three things in that table are worth reading:

1. **The crowd layer swings 9.7 dB** across the day, 03:00 to 13:00, and at
   13:00 the *stream itself changes* — the sparse night murmur becomes
   `crowd_babble`. That is the customs hall filling up, mixed from
   `populace.occupancy` × `schedule.awake_fraction`. Traffic swings ~5 dB with
   it.
2. **Three layers are flat at every hour** — `air` −64.7, `structure` −77.7,
   `pa` −79.7. Those are the controls, and there are three of them rather than
   the one this document claimed before. Air, hull and tannoy trim do not care
   what time it is, and a bed that moved everything at once would be a gain
   rather than a simulation.
3. **The tannoy speaks a different arrival each hour**, era-locked through
   `costume.ERA_EVENTS`, fired as a one-shot inside `broadcast`'s own
   quarter-hour audibility window.

Since `boot.py` moved the spawn to the middle of the built arc, a bare cold start
now begins in the **corridor** rather than in the customs hall, and reports its
own bed: `place=central_corridor layers=4 [air −58.9, crowd:crowd_babble −42.0,
machinery:dock_machinery −60.8, structure −77.7]`. Different room, different mix,
same table.

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
        run: |
          python3 station/boot.py     # derives the spawn off the collision shell
          python3 station/coldstart.py
```

`station/generated/scene/` is gitignored, so `boot.json` is not in the
repository and `boot.py` must run first. If it does not, `main.gd` falls back to
the arrival sidecar and says so — the build still starts, on a spawn nobody
derived.

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

1. ~~**Two different answers to "which place am I standing in", and they
   disagree by 31.6 m.**~~ **CLOSED.** The coordinator extracted the mesh-derived
   rule into `godot/scripts/places.gd` and wired `hud.gd` and `walk.gd` to it;
   `ambience.gd` now reads it too, so `bind()` and `place_at()` are no longer a
   second copy. `DOORWAY_GROW_M` and the smallest-containing-box rule live in
   one file. Note for anyone extending it: `preload`, never `class_name` — a
   global class name resolves through the project's script-class list, which a
   fresh headless run has not scanned, so the identifier does not parse,
   `set_script` fails, and the cold start comes back `hud=0, audio_layers=0`
   with nothing obviously wrong.

2. ~~**The Starfury airframe has no materials.**~~ **CLOSED** — see §2d. All 16
   sections bind, and `materials._selftest`'s vocabulary now reaches outside the
   pressure hull so it can fail for the next one.

3. **`life.gd`'s `Director` and `npc.gd` compose on the same transforms, and the
   file says so.** `Director.process_priority = 100` runs it after `npc.gd` and
   it writes origins while `npc.gd` writes its meshes' transforms to turn a body
   toward the player. A body that is both walking and being looked at turns about
   a pivot that lags its feet. Recorded in `life.gd`'s own header as a known
   interaction; it is now reachable in a live build, so it can actually happen.

4. **`ObjectDB instances leaked at exit`** on every headless quit. Pre-existing —
   the same warning appears on the walk tests — and cosmetic, but it is the kind
   of line that hides a real one.

5. **`hud.gd` prints a line every time its report changes, and a falling body
   changes it every frame.** While the bad spawn was being diagnosed the log was
   ~150 `hud:` lines of a body accelerating outward. The report-on-change rule is
   right; a rate limit, or suppressing it while `is_on_floor()` is false, would
   make the one interesting line findable. Not fixed — `hud.gd` is not mine.
