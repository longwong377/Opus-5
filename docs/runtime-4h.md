# A PERSON CANNOT TAKE YOUR FLOOR AWAY

Session 4h. `godot/scripts/npc.gd`, `player.gd`, `walk.gd`, `door.gd`,
`station/walkable.py` — the three runtime defects `docs/streaming-doors-4g.md`
§6 isolated and deliberately did not fix, and the gate that now guards them.

---

## 1. THE CROWD SHOVED THE PLAYER — AND THE DIAGNOSIS WAS WRONG

`docs/streaming-doors-4g.md` 4c measured the defect exactly and named the wrong
cause. Its A/B is reproduced here, run again at that commit before anything was
touched:

| | subject (no crowd) | crowd on | crowd on, `--no-npc-collision` |
|---|---|---|---|
| `floor_m` | **270.48** | 312.38 | **270.48** |
| `offfloor` | **0**/16200 | **605**/16200 | **0**/16200 |
| visit 1 | door 1.00, 13 noticed, used | stopped **75 m** short | door 1.00, 13 noticed, used |

Turning the capsules off reproduces the crowd-less subject to the metre, so the
crowd's colliders are the cause. That much was right. The proposed fix was not:

> *"a static body teleported into a `CharacterBody3D` ejects it on the next
> `move_and_slide` rather than pushing it. … the body is thrown sideways out of
> a 2.6 m corridor … The fix is probably `AnimatableBody3D` with
> `sync_to_physics`."*

### 1a. Nobody is thrown anywhere

`walk.gd` now reports the SHAPE of the off-floor frames and not only their
count — how many separate episodes, the longest, and how far above its own last
floor position the body ever got, measured along the body's own up because on a
ring a world axis reads the corridor's curvature as lift.

```
offfloor=2523/16200  offfloor_runs=442  offfloor_longest=17  lift_mm=1.3
```

**1.3 millimetres, over 16,200 frames.** It is not flight, it is flicker: 442
separate episodes, most of them a frame or two, none longer than a quarter of a
second. A body thrown out of a 2.6 m corridor would read in metres.

### 1b. Three mechanisms, three negative results

Each is one run of the visit gate with the corridor crowd on, everything else
identical:

| mechanism | `offfloor` | `lift_mm` | verdict |
|---|---|---|---|
| `StaticBody3D` teleported at 10 Hz (as it shipped) | 1708/16200 | 2.2 | — |
| `AnimatableBody3D` + `sync_to_physics`, swept **every physics frame** | 2523/16200 | 1.3 | **no change** |
| …and its capsule padded so the round end caps are out of the player's reach | 2507/16200 | 1.5 | **no change** |
| …and the controller discarding upward velocity it never asked for | 2520/16200 | 1.5 | **no change** |

Two of the four are still in the tree because they are right on their own terms
and cost nothing: the crowd advances **every physics frame** rather than at
10 Hz — a body redrawn ten times a second is a body animated at 10 fps, and the
old rate's justification bounded position *error* rather than smoothness. The
cost it was traded against is gone: the same 16,200-frame run takes **67 s with
no crowd and 68 s with the crowd drawing at 10 Hz**, so the whole of the 86 s
the crowd used to add was its COLLIDERS, not its draw. And `player.gd` still
discards upward velocity no jump asked for, because only a jump should send a
person up. Both say in their own comments that they are measured negatives for
the shove, so the next context cannot mistake either for the fix. The
`AnimatableBody3D` and the padded capsule were reverted: with people off the
player's collision mask nothing resolves against them, so sweeping a body
nothing collides with buys nothing.

`docs/transport-4g.md` is not contradicted — `AnimatableBody3D` +
`sync_to_physics` is the right body for a lift car, and that document measured
it carrying a rider. A walker is not a platform and nobody stands on one.

### 1c. What it actually is, and it is one line of engine behaviour

`walk.gd` now prints the colliders `move_and_slide` resolved on the frame the
floor is lost:

```
walk: OFF FLOOR f=711 lift=0.7mm v_up=-0.000 wall=true slides=3
      [walker_human_23@n=-0.19,0.55,-0.81, walker_human_23@n=-0.19,0.55,-0.81, …]
```

Every episode is a contact with a person. The normal is horizontal to within a
degree — `n · up = -0.015`, so nothing is pushing the body up and `v_up` is
zero. **And the floor is not in the slide list.**

A `CharacterBody3D` re-attaches to a floor it has drifted a millimetre off using
`floor_snap_length`, and that snap casts down with `recovery_as_collision` set.
While the capsule is touching *anything*, the cast comes back holding the thing
it is touching, whose normal is 89° off the floor, and the snap is refused.

**A body touching a person is a body with no floor, whatever the person is made
of.** Which is exactly why all three mechanisms above changed nothing: every one
of them still touches.

It is not about people, either, and the gate's own controls show it: the
`--no-doors` control walks a crowd-less corridor into a shut pressure door and
stands against it, and reports `offfloor=5/16200`. Five frames of the same
thing, against a wall. People are simply the only obstruction a body leans on
for minutes at a time.

### 1d. The mechanism that fits a walker is not a physics body

People go on their own collision layer with mask 0 — `PEOPLE_LAYER`, beside
`interact.gd`'s proxy boxes, which have been arranged this way since they were
written — so `move_and_slide` never resolves against one and the floor is never
in question. `npc.gd::push_off()` then separates the player from anybody it
overlaps **by hand, across the floor plane only**, after every place `walk.gd`
steps the body.

You still cannot walk through a person: the separation is the full overlap of
the two circles, applied every frame, capped at the player's own walking speed
so a streamed cell that arrives with somebody standing where you are pays the
overlap off over three frames instead of teleporting you 162 mm sideways. And a
person can no longer cost you the ground, because nothing they do has a vertical
component.

| | crowd on |
|---|---|
| people resolved by `move_and_slide` (`--npc-solid=mask`) | **3090**/16200 off the floor, 705 episodes |
| people on their own layer + `push_off` | **0**/16200 |

`push_m=16 m` of separation applied over the run, worst frame at the cap — so
the crowd is demonstrably solid and demonstrably not lifting anybody. Uncapped
the worst frame was **162 mm**, which is a visible sideways pop; the cap is the
player's own `speed_m_s` for the frame, read off the body rather than written
down, so nobody can move you faster than you can walk.

And the walk itself came back. With people resolved by `move_and_slide` the body
covered its arc at 1.9 m/s and stalled six legs of the itinerary; separated by
hand it walks **273.5 m** — three metres more than the crowd-less subject, which
is the distance it spends going round people — and makes every visit claim:

```
v1_door_open=1.00 v1_near_m=1.13 v1_noticed=13 v1_prompted=true v1_presses=1
v1_travel_mm=4.00   v2_… identical   freed=true double_wires=0 stale_parts=0
offfloor=0/16200 offfloor_runs=0 lift_mm=0.0
walkers=12 crowd_travel_m=1735.1 crowd_collider=separate/every_frame
push_m=15.66 push_max_mm=70.0
```

### 1e. THE NUMBER GOT BIGGER BEFORE IT GOT SMALLER, AND THAT IS THE HONEST DIRECTION

The defect measured **605** frames at HEAD and **3,090** with the same
configuration once `player.gd` stopped stepping the body twice a frame (§2).
Nothing got worse: the second step was a zero-wish step whose entire effect was
another `move_and_slide` and another floor snap, and it re-settled the body
after most shoves. It was hiding four fifths of the defect it was standing next
to.

**3,090 → 0 is the fix. 605 was never the size of the problem.**

---

## 2. `player.gd` STEPPED THE BODY TWICE A FRAME

`player.gd` has its own `_physics_process`, which steps the body from a keyboard
that is not there — a zero wish, which still rebuilds the basis from `_yaw`. Every
headless mode in `walk.gd` drives `step()` itself, so the body was stepped twice:
once with its own steer, and once more with a yaw nobody set.

Nothing about walking noticed, because a wish vector needs no facing. The EYE
does: the camera rides the body and `interact.gd` scans a 35° cone about it.

`player.gd::drive_externally()` turns the node's own `_physics_process` off, and
`walk.gd::_spawn_player` calls it whenever `--walk-test`, `--stream-test` or
`--shot` is present. A build with a window and a player at the keyboard is
untouched — none of those three flags is there.

### The control, and it needed the workaround removed to fire

`--self-step` puts the whole pre-fix arrangement back: `player.gd` steps itself
AND `walk.gd::_face` stops maintaining `_yaw` for it. Turning off only the first
measures nothing — with `_face` still running, the two steps agree about the
heading and `eye_err_deg` reads **0.0 either way**. That is a control that
cannot fail, found by running it.

`walk.gd` now reports how far the eye is from the direction the body is walking,
sampled at the TOP of the frame (a reading taken straight after `player.step`
sees the basis this file just set and reports zero however wrong the eye is by
the time anything looks through it — `player.gd`'s own `_physics_process` runs
after this node's):

| | `eye_err_deg` mean / max | `v1_prompted` | `v1_presses` | `ok` |
|---|---|---|---|---|
| subject | **0.2** / 179.9 | true | 1 | **true** |
| `--self-step` | **91.2** / 163.1 | false | 0 | **false** |

The mean is the discriminator; the subject's 179.9° max is one frame at a leg
change, where the steer reverses and the body takes a frame to come round. With
the eye 91° off the walk on average the console is never in the 35° cone, the
prompt never appears, and the visit fails — which is exactly the failure this
was mistaken for in 4g.

### What it moved in `walkable.py --deck`, and which value is now correct

Same command both sides — `python3 station/walkable.py --deck blue/0/0
--deck-only --bump` — run from a worktree at `b024a6d`, the commit the before
numbers were taken at, with only the five files of this session copied over it.

| | before | after |
|---|---|---|
| walked into `docking_bays` | 6.4 m → **0.05 m** | 6.5 m → **0.04 m** |
| `offfloor` | **0**/1800 | **0**/1800 |
| inhabitants turning | 9 noticed, 156° turned, **2°** off facing | 9 noticed, 156° turned, **0.7°** off facing |
| `crowd_travel_m` | 5,966 | 5,982 |
| `--no-doors` control stops the body | 5.04 m short | 5.21 m short |
| `door_open` | **0.00** (printed, never asserted) | **1.00** peak, `door_open_now=0.00` |
| `drop` | under the 0.30 bar | **0.319** — and the bar now fails on it |
| `drop_up` | not measured | **0.043** |

**The after values are the correct ones.** A body stepped twice a frame is a
body integrating gravity twice and applying the floor pin twice; a player at a
keyboard gets one step, and every number above now describes the build a person
plays.

**And the one that changed most was the metric, not the build.** `drop` is
`spawn.distance_to(rest)` — a 3D displacement — while `MAX_DECK_DROP_M`'s own
failure message is *"the floor is not where it says"*, a claim about radius. On
this deck 134 people walk down the corridor, and the body spends its 150 settle
frames standing on their centreline: it fell **43 mm** onto a shell 50 mm below
it, exactly as designed, and was pushed **316 mm along the corridor** by people
walking past. The bound is now on `drop_up`, measured along the body's own up,
which on a ring is radial and different at every angle. `drop` is still printed.

Being jostled 316 mm in two and a half seconds of standing in a busy corridor is
a consequence of people being solid and nobody steering round anybody; see §5c.

---

## 3. `door_open` WAS SAMPLED AT THE LAST FRAME

`walk.gd` reported `door_open` from `_doors.openness(_door_key)` at the frame the
verdict prints, which for a body that walked THROUGH a pressure door is several
seconds after it shut again behind them. **Every passing deck walk reported
`door_open=0.00`** and `walkable.py` asserted nothing on it, because the number
was a lie.

```
before:  … goto_best_m=0.05 door_open=0.00 turned_deg=156.1 …
after:   … goto_best_m=0.04 door_open=1.00 door_open_now=0.00 turned_deg=156.1 …
```

It now reads `door.gd::peak_openness()` — the most open that door was over the
whole run, which is the number that says it opened — and prints the live value
beside it as `door_open_now`. `deck_verdict` asserts on it for the first time:

* `-1.00` — no door of that name was ever assembled (leaves in one place, panel
  in another), which is a different failure and says so;
* `0.00` — the body reached the room and the pressure door never opened, so the
  way in is a hole in a wall;
* the control is `--no-doors`, where `door.gd` is not built at all, the token is
  absent, and the gate fails on the absence.

---

## 4. THE GATE

`station/walkable.py --stream`, and it is in CI as
*A streamed cell has working doors, people and interactables* — with an `id:`,
`continue-on-error: true`, and an entry in the final aggregation step, so it can
fail the build without blinding the gates behind it.

**Two subject runs**, one without the corridor crowd and one with it. The
crowd-less one is the configuration the five wiring controls are controls FOR,
so a difference between the two runs is the crowd and nothing else.

**And the crowd run asserts everything the crowd-less one does, plus its own.**
It could not, at first: with people resolved by `move_and_slide` the crowd cost
the body most of its walking speed — twelve walkers resident and the arc leg
covered 93 m of its 130 m inside the same frame budget — so six legs of the
itinerary stalled and the first visit never happened. That was a property of the
broken mechanism rather than of the crowd, and once people stopped standing in
`move_and_slide`'s way it went: the crowd run now walks **273.4-273.6 m** over three runs, opens the
door, is noticed by thirteen people, presses the console, has the cell freed
under it, comes back and does all of it again. Raising the leg budgets until it
fitted would have been picking the convenient reading; fixing the mechanism made
the budgets irrelevant.

**Six controls, judged against the subject each is a control for**, and each
prints what it actually did rather than only that it failed — a control that
fails for the wrong reason is otherwise indistinguishable from one that works.

The order of the crowd assertions matters and is commented in the file:
`--npc-solid=mask` would fail the "is this the subject's mechanism" check
whatever it did, so that check comes LAST and the control has to fail on the
frames instead.

```
PASS  stream  a body walks 270.5 m ON THE FLOOR, 0/16200 frames off it, into cell
      17 which was streamed in after launch: the pressure door opens to 1.00, 13
      people look up, and docking_bays__prop_bay_control_booth prompts and moves
      4.0 mm. The cell is then FREED and re-entered and all three still work
      (1.00 / 13 / 4.0 mm)
PASS  crowd   a body walks 273.5 m ON THE FLOOR through a corridor with people in
      it, 0/16200 frames off it. 12 walkers resident cover 1,735 m around it and
      push it 16 m out of their way (70 mm in the worst frame) -- so they are
      solid, and not one of those metres is vertical
      control --no-cell-wiring  FAILS as it must: floor_m=262.5 offfloor=4/16200
              v1_door=-1.00 v1_noticed=0  v1_presses=0 people=- push_m=0.00
      control --no-doors        FAILS as it must: floor_m=262.5 offfloor=4/16200
              v1_door=-1.00 v1_noticed=8  v1_presses=0 push_m=0.00
      control --no-people       FAILS as it must: floor_m=270.5 offfloor=0/16200
              v1_door=1.00  v1_noticed=0  v1_presses=1 people=- push_m=0.00
      control --no-interact     FAILS as it must: floor_m=270.5 offfloor=0/16200
              v1_door=1.00  v1_noticed=13 v1_presses=0 push_m=0.00
      control --no-unwire       FAILS as it must: floor_m=267.4 offfloor=0/16200
              v1_door=1.00  v1_noticed=13 v1_presses=1 push_m=0.00
      control --npc-solid=mask  FAILS as it must: floor_m=304.2 offfloor=3070/16200
              v1_door=0.00  v1_noticed=0  v1_presses=0 people=mask/every_frame
```

Eight runs, 11 m 37 s, exit 0. Two of the controls are worth reading closely.
`--no-unwire` walks 267 m, opens the door, is noticed by thirteen people and
presses the console — **a first visit that is flawless** — and fails on the
SECOND, which is the whole reason a single-visit gate would not do.
`--npc-solid=mask` is this session's own defect put back: 3,070 frames off the
floor, and the body never even reaches the door.

### It is not a deterministic gate, and that is worth knowing

`stream.gd` loads cells on `ResourceLoader` worker threads, so which frame a
cell becomes resident depends on wall-clock and the crowd is admitted with it.
The `--npc-solid=mask` control measured **3,090**, **810**, **821** and
**3,070** off-floor frames over four runs, and on two of them the body reached
the console anyway while on two it did not. The subject has measured **0** in
every run of it. The controls are robust to this because they fail by hundreds
of frames; the subject's claim is an exact zero rather than a threshold, which
is the kind of claim that survives a jittery harness.

---

## 5. WHAT I FOUND AND DID NOT FIX

### 5a. `station/deck.py` DROPS THE CAPSULE, SO NO ROOM INHABITANT IS SOLID

The CI step *The inhabitants are solid* fails at HEAD, before anything in this
session:

```
FAIL  inhabitants are not solid -- the body got 0.04 m from somebody with their
      capsule on and 0.04 m with it off. A person you walk through is a hologram.
```

`station/populace.py::body_capsule` measures a person's radius and height off
their own mesh and `_place_body` writes `r_m`/`h_m` into the actor record.
`station/deck.py`, mapping a room's actors into the ring's frame, **rebuilds the
dict from scratch and copies neither**:

```python
stats.setdefault("actors", []).append({
    "group": f"{q['key']}__{act['group']}",
    "place": q["key"], "who": act["who"], "pose": act["pose"],
    "x": wx, "y": wy, "z": wz,
    ...                       # r_m and h_m are not here
```

Measured on `blue_0_0_actors.json`: **0 of 21 actors carry `r_m`**, so
`npc.gd::_give_body` returns early for every one of them and no inhabitant on
the station has ever had a collider. The corridor path two hundred lines below
uses `dict(act, place="corridor")` and keeps them, which is why the crowd's
capsules exist at all. `station/deck.py` is not mine.

### 5b. A WALKING BODY'S MEASURED RADIUS IS ITS STRIDE

`body_capsule`'s docstring argues its own clearance from a standing figure —
*"0.269 m against a 1.081 m half-width leaves 0.81 m of clearance either side"*.
The crowd's meshes are walking, and the widest horizontal extent of a walking
figure is the stride and the arm swing, not the shoulders. Measured over
`blue_0_0_crowd.json`'s 134 walkers: **mean 0.482 m, max 0.624 m** — up to 2.3×
the number that clearance argument was made with, i.e. a person 1.25 m wide.

None of them seals the corridor outright (0 of 134), but the gap left beside the
widest is under a metre, so a body steering down the centreline spends its walk
being pushed past people. That is what made the crowd run cover its 130 m arc at
1.9 m/s while people were still in `move_and_slide`'s way, and it is why a body
standing still in a corridor drifts 316 mm in two and a half seconds. It is a
`station/populace.py` measurement and not mine.

### 5c. NOT DONE

* **The crowd does not get out of your way.** People are solid and separate
  correctly; nobody steers around anybody. That is why a body standing still in a
  busy corridor is shuffled along it, and it is the next thing a corridor needs
  to feel like one.
* **`--npc-solid=mask` is kept deliberately** as the control. It is the build
  before this session and it must go on failing.
* **Dialogue is still not wired per cell** — unchanged from
  `docs/streaming-doors-4g.md` §7.
