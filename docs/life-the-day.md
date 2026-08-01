# The station has a clock — property C, and what it cost to get it

Session 4e. `docs/MASTER-PLAN.md` §0 lists four properties the deliverable must have.
Property C is *"it is alive: the station behaves identically whether or not it is observed;
leaving and returning is consistent; 03:00 differs visibly from 13:00."* Before this session
it was the one with nothing behind it.

Not for want of a model. `station/npc/schedule.py` knows fifteen species' sleep blocks, meal
hours, shift rosters and leisure weightings. `station/npc/resident.py` gives every one of
250,000 people a name, a role, a home, a job, a canteen, a market, a bar, a chapel and a
transit facility they commute through. **None of it ran.** `station/populace.py` evaluated
`resident.where_at(res, 13.0)` exactly once, baked the bodies it got into the room mesh, and
that was the station for ever — a diorama with a timestamp.

Two files close it:

| file | what it is |
|---|---|
| `station/npc/life.py` | the simulation: a resident's DAY, and the station-wide consequence |
| `godot/scripts/life.gd` | the runtime: the clock, and people who move on it |

---

## 1. The gap was narrow and specific

`where_at(res, h)` answers *where is this person at hour h* and it is a **teleport**. At `h`
they are at home; at `h + eps` they are at work; the corridor between the two is never
occupied by them. `schedule.activity_at` does emit `Activity.TRANSIT` — but for a **flat half
hour** either side of a shift and for nothing else, so a meal out, a trip to the Zócalo and a
walk to the sanctuary all happen instantaneously.

And nothing anywhere turned a *sequence of hourly answers* into a **day**: an ordered,
bounded, gapless partition of 24 hours into things a person is doing and journeys between the
places they do them in.

### The day

`life.day(npc_id, species)` returns a tuple of `Span`, summing to exactly 24.000000 hours,
with no gaps and no overlaps — asserted over 384 residents and 9,167 spans. A resident has a
**mean of 23.9 spans a day**, about half of them journeys.

The edges are derived, not sampled: `activity_at` is piecewise constant and its pieces are
knowable — the sleep block, three meal windows, a shift, two commute windows, and the leisure
draw which re-rolls on the integer hour. That is at most 36 breakpoints, against the 1,440
minute-samples a grid would need. **The edge list is a copy of another module's internals and
is therefore not trusted**: `_check_breakpoints` walks a minute grid over a sample of six
species and asserts the reconstruction equals `activity_at` everywhere. *0 of 1440 minutes
disagree on the worst resident.*

### Where a journey sits

One rule: **work has hard edges; everything else absorbs the travel.**

A shift starts when it starts, so somebody due at 08:00 leaves home early enough to arrive at
08:00 and the journey lands *before* the boundary. A shift ends when it ends, so the walk to
the bar lands *after* it. A trip between two soft activities straddles the boundary evenly.

That is not invented to be tidy — it is the shape `schedule.activity_at` already emits, which
puts TRANSIT in `[w0 − 0.5, w0]` and `[w_end, w_end + 0.5]`. One rule, applied in two places,
rather than two rules that happen to agree.

### The journeys are routed

Every journey is priced on `station/npc/navigation.py`'s graph — **20,871 nodes, 76,106
links** over the real decks, ring corridors, spoke lifts, core shuttle and both tram systems,
with walking speed from the Froude gait model at the local gravity. Two numbers come back and
they are different questions:

* `travel_s` — the whole journey, doors to doors, including waiting for a lift
* `foot_s` — only the `walk`, `stair` and `door` legs

The split is the reason `foot_s` exists: **a resident standing in a spoke lift is in transit
and is not in a corridor**, and the corridor is the space this project has to populate.

*Example: `qtr_civilian → business_center` is 7.7 minutes, all of it on foot.*

### One person's day

`python3 station/npc/life.py --day agg-human-7` — a plant technician on the evening watch:

```
agg-human-7  (human)
  Aisha Ivanova   role industrial   home qtr_personnel   job maintenance
  00.29-00.86  recreation garden_town
  00.86-01.14  TRAVEL  garden_town -> qtr_personnel   (17 min, 4 on foot)
  01.14-02.70  idle       qtr_personnel
  02.70-03.30  eat        qtr_personnel
  ...
  07.06-14.45  sleep      qtr_personnel
  14.45-14.54  TRAVEL  qtr_personnel -> post_office   (5 min, 5 on foot)
  ...
  15.69-16.00  TRAVEL  post_office -> maintenance     (19 min, 3 on foot)
  16.00-20.20  work       maintenance
  20.20-20.80  eat        maintenance
  20.80-24.00  work       maintenance
  24.00-00.29  TRAVEL  maintenance -> garden_town     (18 min, 3 on foot)
  travel 109 min/day, on foot 38 min/day
```

Three things in there are the model working rather than the model being written down. Her
shift starts at **16.00 exactly** and the 19-minute walk to it lands *before* the boundary,
because work has hard edges. Her meal at 20.20 is taken **at work**, because
`schedule.activity_at` resolves EAT before WORK, so a meal inside a shift is a break rather
than an absence. And the 17-minute trip out to `garden_town` is mostly **not on foot** — the
drum is a tram ride and a spoke lift from Blue Sector's personnel quarters, and the graph
knows that.

---

## 2. The headline

    hour     in transit    on foot     asleep     at work
    03:00         9,898      5,092    165,959      32,356
    08:00        24,064     12,646     47,073      68,733
    13:00        23,858     11,312     32,050      78,360

**×2.48 more people on their feet in the corridors at the morning shift change than at three
in the morning**, and **×4.09** between the station's quietest corridor hour (02:00, 3,750 on
foot) and its busiest (19:00, 15,321). Derived, not chosen: nothing was tuned to produce it.
It falls out of `schedule.ROLES`' start times, `RHYTHMS`' fifteen sleep blocks and the routed
length of every resident's own journeys.

The two hours are visibly different stations, and not only in headcount:

| | 03:00 | 08:00 |
|---|---|---|
| busiest journeys | `mess_hall → happy_daze` (327), `bar_unnamed → qtr_civilian` (271), `business_center → qtr_civilian` (237), `interfaith_chapel → qtr_civilian` (198) | `qtr_civilian → business_center` (613), `qtr_civilian → eclipse_cafe` (611), `qtr_civilian → post_office` (580), `qtr_civilian → bar_unnamed` (509) |
| busiest places | `qtr_civilian` 85,320, `qtr_transient` 51,278, `subfloor_stack` 7,123, `downbelow_arch` 5,950 | `qtr_civilian` 55,610, `zocalo` 10,095, `shops_kiosks` 8,955, `bar_unnamed` 8,189 |

At 03:00 the traffic is people *leaving* — bars, the business district, the chapel — and
almost all of it ends at somebody's quarters. At 08:00 every one of the eight busiest journeys
*starts* at somebody's quarters.

### The commute is not the biggest part of it

Only three of the eight busiest 08:00 journeys go to a workplace; the rest go to the Eclipse
Cafe, a bar, the Zócalo and the kiosks. A resident makes about **13 journeys a day**, because
`schedule.activity_at` re-rolls its leisure choice on every integer hour — so the corridors
are dominated by people going *out* rather than people going *to work*. Worth **116.8 minutes
a day** of travel per resident, of which **58.0** are on foot.

Whether that much churn is right is `schedule.py`'s question, not this file's. What this file
can say is what it costs.

---

## 3. Two defects the gates found

### 3.1 The sampler was measuring its own grid

The first version of `station()` asked every resident what they were doing at exactly `h:00`
and counted the answers. It reported **66,469 people in transit** on the 24-hour mean — 26.6%
of the station, at every hour of the day and night — while the same residents' own days sum to
116.8 minutes of travel each, which is 8.1% and **20,271 people**. A factor of **3.28**, from
the sampler alone, on the module's headline number.

The cause: `schedule.activity_at` re-rolls its leisure choice on the **integer hour**, so an
off-shift resident changes place at `h:00` and at no other time. A journey between two soft
activities straddles the boundary it crosses. **So `h:00` is the instant at which every
leisure journey is at its midpoint.** Sampling there does not measure the station at 08:00; it
measures the station's moment of maximum motion, 24 times a day.

An hour is now an hour: `station(h)` is the expectation over a uniformly random instant in
`[h − 0.5, h + 0.5)`, computed exactly from the span intervals rather than sampled in time.

> **A statistic sampled on the same grid the model changes state on measures the change, not
> the state.**

The gate that catches the whole class is one line — *the 24-hour mean of the hourly table must
equal the residents' own mean travel time*, two independent routes to one number, agreeing at
20,271 against 20,271 — and **the old sampler is kept as its control**, where it fails by 3.3×.

### 3.2 `populace.occupancy` fills the quarters in the afternoon

Correlating both models' 24-hour curves per place, normalised to their own peaks, gives a mean
of **+0.32** over 66 places. That reads as weak agreement and is not one. Sorted, the bottom
of the table is:

    -0.80  qtr_civilian        -0.71  downbelow_arch     -0.69  qtr_personnel
    -0.68  qtr_transient       -0.67  subfloor_stack     -0.58  morgue
    -0.56  alien_resident_qtr

**Six of the seven places people live are in the bottom seven, and the only thing sharing the
band with them is the morgue.** Split on it:

| | places | mean r |
|---|---|---|
| non-residential | 59 | **+0.42** (median +0.62) |
| residences | 7 | **−0.56**; the one exception, `league_delegations` at +0.16, is still below the median room |

That is not 66 places each drifting a little. It is one mechanism, and CLAUDE.md's session-4d
rule — *"a number that fails 100% on one side of a line and 1% on the other is a structural
fact"* — says to go and find it rather than widen the tolerance.

It is `populace.occupancy`'s fallback curve, and the peak densities confirm it: every one of
those seven comes back at **4 per 100 m²**, the `generic` archetype rate, so none has a
`PlaceCrowd` entry of its own and all take

    day = 0.25 + 0.75 * sin(pi * (hour - 6) / 14)

which peaks at 13:00. A reasonable shape for an office and exactly backwards for a bedroom. So
the placement model puts the most bodies in `qtr_civilian` at one in the afternoon and the
fewest at three in the morning, while this model has **85,320 residents asleep in there at
03:00** and 55,610 at 08:00.

**The consequence is not small: the quarters hold a third of the station at any hour and today
they are populated on an office's clock.** The fix is a residential entry in
`populace.FALLBACK_PER_100M2` with a night-weighted curve, or a `PlaceCrowd` per quarters
block. That file is not this session's, so the self-test asserts the anomaly is exactly where
this note says it is — **and will fail the day it is fixed**, which is the point.

---

## 4. Two models, one population

`populace.occupancy` is a **density** — how many bodies a room holds, from a calibrated
peak-per-100 m² and a busy/dead window. `life.presence` is a **headcount of people**, from
250,000 individual days. They are different mechanisms describing one station, so they are
checked against each other three ways:

| check | result | control |
|---|---|---|
| time on foot vs `populace.WALK_MIN_PER_DAY` | 58.01 min/day here against 50.8 there = **14.2%** | doubling every route → 91.56 min/day = 80.2% off |
| non-travel census vs `schedule.population_activity` | total variation **2.22%** over the seven non-travel activities | against `schedule.py` at 20:00 instead → 21.12%, ×9.5 |
| per-place 24-hour shape vs `occupancy` | mean r = **+0.42** over 59 non-residential places | rotating the day 12 h → −0.43 |

The 14.2% on time-on-foot is explained rather than tolerated. `populace.WALK_MIN_PER_DAY` was
measured by sampling `where_at` **hour by hour**, which is at most 24 changes a day; this
module uses the exact breakpoints, which finds 23.9 spans — including sub-hour changes like
*meal → back on shift*. More changes, more walking.

**The second check needed its own fix before it meant anything.** It first compared this
module's hour-*mean* against an *instantaneous* `population_activity(8.0)` and reported a
2,563-person discrepancy that was entirely the sampler of §3.1. The reference has to be
integrated the same way the subject is, or the comparison measures the integrator.

### One number the model refuses to hide

`JOURNEY_MAX_F` caps a journey at 45% of the shorter anchor it borders, so an anchor always
keeps a tenth of itself and the 24-hour sum stays an identity. **It fires on 26.5% of
journeys**, and the first version of the gate counted journeys and failed — which reads as
this module being broken. Counting the *time* says what is happening: the clamp removes
**14.9% of the travel hours the routes ask for**, so a quarter of journeys are trimmed and
they are the short ones.

The cause is upstream and is worth writing down: the hourly leisure re-roll gives an off-shift
resident **one-hour anchors**, and 45% of an hour is 27 minutes — less than a cross-station
route. The model is saying, correctly, that a resident cannot spend an hour in a bar 8 km away
and another hour somewhere else an hour later.

---

## 5. The runtime, and why it is written the way it is

`godot/scripts/life.gd`. The architecture *is* property C, in one sentence:

> **An inhabitant's state is a pure function of the station clock.**

Nothing integrates, accumulates or steps. `Director.apply(h)` computes where everybody is from
`h` alone. Three consequences, and they are the three clauses of §0's property C:

* **behaves identically whether or not it is observed** — there is no state to diverge. A room
  nobody is looking at is not being simulated wrongly; it is not being simulated at all, and
  the answer when you walk in is the answer it would have had.
* **leaving and returning is consistent** — measured, not asserted: 03:00 → 08:00 → 13:00 →
  03:00 returns every body with a **worst drift of 0.000000000000 m over 73 transforms**. The
  control is an `Integrator` class in the same file — what a naive crowd runtime does — which
  accumulates 12.48 m on the same trip and has no way to undo it.
* **03:00 differs visibly from 13:00** — on the real deck's cast, **29 bodies present at
  03:00, 48 at 08:00, 73 at 13:00**.

It drives two things, because they are the two kinds of person the generator makes:

1. **Corridor walkers move.** A body on a ring deck has a radius and a bearing; `apply`
   advances the bearing at the walking speed as a function of the clock. Nobody is on a
   treadmill — a corridor's crowd is a *flow*, and the flow at 03:00 is the same people moving
   as at 08:00, there are just 2.48× fewer of them. One station minute covers **77.6 m against
   the 78.0 m** the speed demands.
2. **Rooms fill and empty.** `PRESENCE` carries a 24-hour curve for **71 places**, normalised
   to each place's own peak. *Which* people are present is a deterministic function of their
   ids, so the same regulars are in the Zócalo at 14:00 today and tomorrow.

### Cost

2,000 bodies — more than the whole station's baked crowd of 2,028 — update in **2,812 µs**
against a **3,167 µs** ceiling, which is 1.41 µs a body; the 73 on the loaded deck cost 103 µs.

**The ceiling is borrowed and that is said out loud.** `body.NPC_FRAME_SHARE = 0.19` is a
*mesh* budget — how much of a frame the crowd may spend holding triangles. The project has no
CPU budget for a crowd director because it has never had one, so the gate borrows the only
number that exists, which is the conservative direction: the drawing still has to come out of
the same 19%.

Two things were measured rather than assumed on the way there, and both were in the docstring
as claims before they were true:

* **"no per-frame string work" was false.** Looking a body's place up by string key hashes a
  string per body per frame: **4,771 µs** against a 3,167 µs budget. The place key becomes an
  index at `bind()`.
* **A `find()` in the frame loop is O(n) inside O(n).** At 2,000 bodies that is four million
  comparisons a frame spent on a linear search. Each person caches its own rank within its
  place.

### Integration note

`npc.gd` turns a body to look at the player by writing its meshes' transforms; this script
writes their origins, at `process_priority = 100` so it runs afterwards and composes on
whatever basis `npc.gd` left. A body that is *both* walking *and* being looked at is the only
case where the two meet, and `npc.gd` caches its pivot from the rest pose, so such a body turns
about a point that lags its feet. Fixing that means `npc.gd` recomputing its pivot, which is
not this session's file.

---

## 6. Running it

```bash
python3 station/npc/life.py --selftest       # every gate, with its controls (~5 min)
python3 station/npc/life.py --derive         # recompute the recorded tables from the graph
python3 station/npc/life.py --hour 3         # the whole station at 03:00
python3 station/npc/life.py --day <id>       # one person's day, span by span
python3 station/npc/life.py --gd             # the const block life.gd embeds

GODOT=/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
$GODOT --path godot --headless --script res://scripts/life.gd -- --life-test
$GODOT --path godot --headless --script res://scripts/life.gd -- --life-hours

# the frames. NOT --headless: headless disables rendering, so a virtual display
# and the lavapipe ICD are both required, exactly as tools/render_godot.sh says.
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json \
  xvfb-run -a --server-args="-screen 0 1280x720x24" \
  $GODOT --path godot --rendering-driver vulkan --resolution 1280x720 \
  --script res://scripts/life.gd -- --life-shot --hour=13 \
  --out=$PWD/docs/engine-4e-life-1300.png
```

`life.py --selftest` §8 re-derives the const block and asserts `life.gd` embeds exactly it —
**78 of 78 const lines match** — so the runtime and the model cannot drift apart silently.
That is CLAUDE.md's rule about a gate that reads a committed artefact having to be able to
rebuild it, applied before it could be broken.

### The frames

`docs/engine-4e-life-1300.png` and `docs/engine-4e-life-0300.png`: **the same camera, on the
same deck, at two hours**, driven by `life.gd --life-shot`. Blue Sector's north customs hall,
looking down its 30 m, from the eye height of somebody standing on the floor. At 13:00 there
are people queueing in it. At 03:00 it is empty — because `PRESENCE["customs_north"]` is 1.00
at 13:00 and **0.00** from 17:00 to 08:00, which is `schedule.py` saying customs closes for the
night. The bodies did not move: the same 73 are bound in both frames, and 73 are present in
one and 0 in this view of the other.

```
Vulkan 1.4.318 - Forward+ - Using Device #0: llvmpipe (LLVM 20.1.2, 256 bits)
bound 73 of 73 actors; 73 present at 13.00   -> docs/engine-4e-life-1300.png
bound 73 of 73 actors; 29 present at 03.00   -> docs/engine-4e-life-0300.png
```

(29 present at 03:00 is the whole deck cluster: `arrival_concourse` keeps a tenth of its people
overnight and `customs_south` runs its own rota. `customs_north`, which is what the camera is
looking at, is empty.)

**These are not craft frames and no craft claim is made from them.**
`station/generated/scene/deck/*.glb` carries POSITION and NORMAL and no materials; the `.tres`
assignment pass that makes a deck look like anything lives in `tools/export_scene.py` and
`godot/scripts/render_shot.gd`, neither of which this session owns. They are clay renders —
Forward+ on lavapipe, so the renderer is the real one, but the surfaces are the glTF default.
The only claim they support is the one they can: **the same view, two hours, a different number
of people in it.**

---

## 7. What is not done

* **Room occupants do not walk.** `life.gd` moves corridor walkers along the ring and gates
  everyone else's presence. A body leaving a room at the end of its shift blinks out when the
  player is not looking at it (`hold_radius_m`) rather than walking to the door — because the
  actor record carries no door and no route. The honest next step is `deck.py` writing each
  actor's `life.day()` alongside its position, at which point `life.gd` can walk a person
  along a real path instead of scaling a curve.
* **The graph is human-gaited.** `navigation.walk_speed(g, species)` takes a species and
  `build_graph` does not thread one through, so a Gaim and a Centauri walk a corridor at the
  same speed here. Closing it means a graph per species — 32 s and 20,871 nodes each.
* **`walk_speed_ms` in the runtime is the human 1-g figure.** `populace._walk_speed` derives
  it per species at the deck's own gravity and bakes the pose, but nothing carries the number
  out to the runtime. The fix is one field in the actor record.
* **The residential occupancy curve** of §3.2 is measured and asserted, not fixed.
* **Nothing has wired `life.gd` into a shipped scene** — `tools/export_scene.py` decides what a
  shot contains and it is not this session's file. `--life-shot` builds its own scene to prove
  the director drives the real cast; the two-line integration is in the script's header.
