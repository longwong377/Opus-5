# Layer 7 — Audio

`station/audio.py`, `godot/scripts/ambience.gd`, `station/generated/audio/`.

CLAUDE.md's layer table read **`7  Audio  Ambience and event audio per location  0`** from the day
it was written, and session 4d's audit put it in one phrase: **no audio at all**. The string
`AudioStream` appeared nowhere in the project and there was not one `.wav` or `.ogg` in the tree.
The owner's standard names *"the sound"* in the same breath as the textures and the physics.

**This is `station/broadcast.py`'s move applied to sound.** An ambience is not a library of loops
somebody chose; it is a **view of a simulation that already exists**. Every level below is a
function of modules that were already here, so the ambience cannot drift from the station — it has
no content of its own to drift with.

---

## 1. What a bed is made of

Seven layers. Each carries a level in dBA **and the reason it is that level**;
`python3 station/audio.py --bed zocalo --hour 13` prints both.

| layer | derived from | varies with |
|---|---|---|
| **air** | INV-260's design ladder + the room's own design occupancy | archetype, declared functions, peak crowd |
| **structure** | `interior.SPOKE_COUNT` and canon's 33.4716 s rotation period | nothing — it is the same everywhere, on purpose |
| **machinery** | `rooms.FIXTURES[archetype]`, counted the way `rooms` lays them out | archetype, room length, plant next door |
| **crowd** | `populace.occupancy` × `schedule.awake_fraction` weighted by the place's own species mix | hour, species, occupancy |
| **water** | the place's own declared water props | `directory.PLACES["interacts"]` |
| **traffic** | `traffic.berths_in_use` and `traffic.hall_rate` | hour, day, whether a liner is in |
| **pa** | `broadcast.audible_at` — the same era-locked lines the signage layer uses | hour, day, `costume.ERA_DATUM` |

### The acoustics are one equation, used twice

Crowd and machinery are both incoherent sources in a room, so both go through the classical
diffuse-field result

```
Lp = Lw + 10·log10(4 / R)          R = S·ᾱ / (1 − ᾱ)
```

`S` comes from `density.budget_area`'s own surface formula, so **the room the acoustics describe
and the room the triangle budget describes are the same room**. A large, absorbent, sparsely
populated hall comes out quiet for both layers without either being told to.

And **the crowd absorbs itself** — `ᾱ` rises with occupancy at 0.4 sabins a standing body — so the
murmur saturates instead of growing at 10·log10(N) for ever. Measured, at 2,000 m²:

| voices | 1 | 3 | 10 | 30 | 100 | 300 |
|---|---|---|---|---|---|---|
| dBA | 51.5 | 56.3 | 61.3 | 65.7 | 69.8 | 71.9 |

1 → 3 gains 4.8 dB; 100 → 300 gains 2.1. With the occupancy term switched off the same span gains
**14.8 dB instead of 10.5** — that is the negative control, and it is in the self-test.

---

## 2. A day is not a night

The whole claim of the layer, and the number that answers *"has any ambience been added?"*.
Steady bed only — an announcement is an event, see §5.

### The Zocalo, itemised

| layer | 03:00 | 13:00 | why it moved |
|---|---|---|---|
| air | 48.0 | 48.0 | design ventilation, so it does not |
| structure | 28.0 | 28.0 | one hull, one rumble |
| machinery | 30.4 | 30.4 | 26 stall frames and 13 awning rails, all night |
| **crowd** | **62.0** | **67.5** | `populace.occupancy` **324 → 720 bodies**, awake share **0.43 → 0.83** |
| water | 20.5 | 20.5 | a planter |
| pa (idle horn) | 26.0 | 26.0 | a live tannoy is never silent |
| **total steady** | **62.1** | **67.6** | **+5.47 dB** |

324 bodies × 0.43 awake × 0.33 talking = **46.4 voices** at 03:00 against **198.5** at 13:00. The
level does not move by the 6.3 dB that ratio implies because the extra 274 bodies are also 110 m²
of extra absorption.

### Across the station

| place | 03:00 | 08:00 | 13:00 | 19:00 | 23:00 | day − night |
|---|---|---|---|---|---|---|
| central_corridor | 53.0 | 66.8 | 63.8 | 63.7 | 61.7 | **+10.77** |
| customs_north | 52.5 | 59.3 | 61.4 | 58.3 | 54.3 | +8.97 |
| qtr_civilian | 52.4 | 59.0 | 61.2 | 58.1 | 54.2 | +8.84 |
| the_garden | 55.5 | 59.1 | 61.6 | 59.2 | 57.5 | +6.10 |
| **zocalo** | **62.1** | 64.2 | **67.6** | 68.0 | 66.8 | **+5.47** |
| sanctuaries | 56.9 | 61.2 | 61.3 | 61.4 | 57.9 | +4.39 |
| alien_sector | 57.8 | 61.8 | 61.7 | 61.1 | 59.2 | +3.82 |
| downbelow | 59.9 | 63.5 | 63.5 | 63.7 | 62.2 | +3.59 |
| docking_bays | 65.5 | 66.4 | 67.0 | 67.3 | 67.1 | +1.50 |
| **reactor_hall** | **79.0** | 79.0 | 79.0 | 79.0 | 79.0 | **+0.05** |

The corridor's 08:00 peak is the shift change, off `schedule`'s own rotation. **The reactor hall is
the control**: a room whose sound is plant rather than people has no day and no night.

`docs/audio-day.png` plots this against the hour, with the human sleep block shaded.

### The species clock, which is the sharpest part

`awake_share` weights `schedule.awake_fraction` by the place's own mix, sampled through
`populace.species_for` — the same function that decides which body gets placed.
`RHYTHMS["brakiri"]` is flagged **NIGHT DWELLERS at authority 4**, so:

| | human | brakiri |
|---|---|---|
| awake at 03:00 | **0.26** | **0.97** |

None of that is written down in `audio.py`. It arrives from the rhythm table, and it is why
different places keep different fractions of their crowd overnight — awake(03:00)/awake(13:00) is
0.31 in crew country, 0.40 in the Alien Sector, 0.52 in the Zocalo.

**And `downbelow` swings +3.59 dB although `schedule.PLACES` marks its headcount FLAT.** That is
not a defect; its *residents* sleep on their own clocks. It was the first choice of control for the
day/night gate and had to be replaced, because it swings more than the Zocalo.

---

## 3. The port

`traffic.berths_in_use` and `traffic.hall_rate`, on the day the manifest actually lands a liner.

| | hour | traffic layer | derived from |
|---|---|---|---|
| customs hall, background | 06.80 | **45.9 dBA** | 0.62 people/min, ×1.0 |
| customs hall, liner clearing | 11.30 | **57.3 dBA** | **8.53 people/min, ×9.7** |
| the same hour, a day with no liner | 11.30 | **47.4 dBA** | the control — the surge is the ship, not the hour |

**+11.4 dB while a liner clears, and −9.9 dB of that goes away on a linerless day.**

The docking bay moves less (62.7 → 64.0 dBA) for a reason worth stating: the manifest keeps
18–24 berths occupied at every hour, so the bay row is never quiet. What changes is *how many*.

---

## 4. The gazetteer's own sentence

`LIFE-SUPPORT-AND-INDUSTRY.md` §2.3: *"the compressors are audible from Downbelow — a low beat that
is the reason nobody chooses to sleep there."*

That is not asserted anywhere in `audio.py`. `directory.PLACES` already records
`downbelow.adjacent = ('plant_zone',)`, `plant_zone` is an `industrial` archetype, and INV-264 puts
25 dB between them:

```
downbelow 03:00: machinery 53.9 dBA over its own air handling at 32.8 dBA  (+21.1 dB)
control qtr_command 03:00: no machinery layer at all, air 31.0 dBA
```

The self-test asserts both — that the plant IS audible in Downbelow, and that it is NOT in command
quarters — and asserts the gazetteer sentence is still in the file the rule was built from.

**Every dwelling on the station over 45 dBA of machinery is inside or beside the plant.** That gate
is what found the mortuary; see §6.

---

## 5. Steady and event

An ambience is the steady bed. A tannoy call is an event on top of it, at 68 dBA.

This was not a tidiness decision; it was found twice, by two different gates.

1. **In the beds.** With the announcement folded into one total, the Zocalo's day/night
   difference read **+1.82 dB while the crowd layer itself was moving +6.3** — the gate was
   measuring whether the tannoy happened to fire in that quarter-hour. `bed()` now reports
   `steady_dba` and `event_dba` separately.
2. **In the manifest, by the runtime test.** `beds.json` is hourly; `broadcast`'s audibility
   window is a quarter of an hour. A chime that fires once therefore appeared in the bed at
   **03:00 and 13:00 alike** and read as a tannoy that never stops. Announcements are now a
   separate list in `bank.json` with their real times and their real text, fired as one-shots by
   `_speak()` — so the horn goes off at the minute the ship berths and says the era-correct thing.

The PA layer inherits `broadcast.py` whole, including its isolation rule: the concourse hears
announcements, **ordinary civilian quarters hear nothing at all**, and both are asserted.

---

## 6. What the gates found

Every gate here can fail and did. In order of what they cost:

1. **62 dBA of duct noise in the command staff's bedrooms.** `service_duct` was in the machinery
   fixture table at 74 dB Lw, thirteen of them a room. The duct *is* the air handling: the air
   layer already models the whole ventilation system by design class, so counting it again was
   the same plant counted twice with the second count answering to nothing. Removed from the
   machinery layer, kept as a point emitter — which is exactly right, since the room's ventilation
   is the air layer and standing under the duct is the duct. `AIR_SYSTEM_FIXTURES` names them and
   an assertion checks none has leaked back.
2. **A single Vorlon berth hearing all 32 of the station's ships — 88.8 dBA, the loudest bed in
   the manifest.** `traffic.berths_in_use` is a station-wide count and every berth was being handed
   all of it. **The master trim is derived from the loudest bed**, so one wrong room was setting
   the gain for everywhere. Now the station's berthed ships are spread over the station's berthing
   floor and the answer is the expected number inside a 60 m patch of it: 0.24 ships in the bay row
   with a liner in. Loudest steady bed on the station is now `waste_red` at **79.7 dBA**. The
   control reverts the share and reads 87.6 dBA, and fires.
3. **58 dBA of refrigeration plant in the mortuary**, a space INV-260 classes `quiet` at 30 dBA.
   `equipment_gantry` was rated 66 dB Lw — a fan-coil unit — where a medical monitoring gantry is
   small-appliance class. The whole light end of `FIXTURE_LW_DB` was 12–14 dB hot and was rescaled
   against one reference: 40 dB Lw is a thing that is technically not silent, 55 is a thing with a
   fan in it, 85+ is plant.
4. **The chime was not silent at sample zero.** Its envelope was centred at 0.25 s with a 0.32 s
   half-width, so it began at 0.055 amplitude — a click every time the tannoy fires, which is the
   most-triggered sound in the station. Caught by the pump gate at **+33.3 dB**.
5. **Three streams' measured spectral centroid missed the band they claimed** — `crowd_babble` at
   1,683 Hz against a speech long-term average spectrum that sits near 700. **The builds were
   changed, not the bands.** Widening a band to admit the stream you happened to build is the
   "grow the gate" move this repository has a rule against.

---

## 7. The waveforms

**Loop-exact by construction, not by editing.** Every stream is synthesised in a length-N circular
buffer and every filter is a multiply in the frequency domain, which is a *circular* convolution. A
signal built that way is exactly periodic with period N: the loop seam is an ordinary sample
boundary, and there is no crossfade anywhere in the file. Periodic components go through `_cycles`,
which rounds to a whole number of cycles in the buffer.

`docs/audio-spectra.png` is every stream's third-octave spectrum on one log axis.
`docs/audio-seam.png` is the join itself, shipped above and the broken control below.

| stream | s | RMS dBFS | centroid Hz | declared band | click | pump dB | what it is |
|---|---|---|---|---|---|---|---|
| air_plenum | 6.000 | −20.0 | 128 | 90–700 | 0.36 | +2.40 | the same air two rooms away — a dwelling |
| air_duct | 6.000 | −20.0 | 1339 | 700–2400 | 0.30 | +0.27 | a supply duct near its diffuser |
| air_alien | 6.000 | −20.0 | 1715 | 1500–4000 | 0.02 | +0.26 | §2.3's *"change the ambience track … before any sign says so"* |
| structure_hull | **11.157** | −20.0 | 27 | 18–120 | 0.36 | +2.28 | the hull, breathing at the spoke pass |
| plant_beat | 8.000 | −20.0 | 73 | 35–260 | 0.74 | −0.02 | INV-262's beat over a 58 Hz shaft line |
| machine_hum | 6.000 | −20.0 | 113 | 90–900 | 0.33 | +0.01 | 100 Hz and harmonics — fittings and cabinets |
| dock_machinery | 8.000 | −28.1 | 164 | 60–600 | 0.07 | +1.49 | clamps and cranes; the bay is not steady |
| crowd_babble | 8.000 | −20.0 | 599 | 450–1200 | 0.12 | +1.03 | speech LTAS under five syllable rates |
| crowd_sparse | 8.000 | −36.9 | 964 | 450–1900 | 0.40 | −1.15 | the same band, gated — you hear *people* |
| water_run | 6.000 | −20.0 | 3345 | 2200–5500 | 0.25 | −0.33 | §3.3's standpipe |
| water_pool | 6.000 | −31.7 | 2228 | 700–5000 | 0.01 | +0.57 | the Garden's pool and forty drips |
| pa_horn | 4.000 | −20.0 | 2988 | 400–4000 | 0.21 | +0.72 | the horn's own hiss |
| pa_chime | 2.000 | −20.0 | 1029 | 500–1800 | 0.00 | +0.00 | two tones, A5 and D6 |

**32 kHz, 16-bit, mono. 13 streams, 5.86 MB total** including both JSON manifests —
`bank.json` (the stream bank, the emitter rules, the master trim and the day's **118
announcements** with their real times and era-locked text) and `beds.json` (128 places × 24 hours
× up to 7 steady layers, 361 KiB).

The **master trim is +8.33 dB, derived rather than chosen**: it is whatever puts the loudest
steady bed on the station — `waste_red` at **79.7 dBA**, at 15:00 — at −6 dBFS.

The structure loop is **357,030 samples = 11.157187 s**, one spoke-pass period, against the exact
11.157200 s — a quantisation error of **12.5 µs a cycle**, which is 0.04 s over a ten-minute
session and is phase-locked to nothing.

### Two seam gates, because one is not enough

| | measures | passes at |
|---|---|---|
| **click** | step across the join ÷ 99.9th percentile of the steps inside it | ≤ 1.0 |
| **pump** | short-term level of the head against the tail | ≤ 3 dB |

| control | click | pump | which fires |
|---|---|---|---|
| shipped `crowd_babble` | 0.12 | +1.03 | — |
| a time-domain one-pole IIR instead of a spectral multiply | **6.32** | −2.79 | click |
| a modulator at a non-integer number of cycles | 0.10 | **−5.73** | pump |

**Neither subsumes the other, and that is asserted.** The click gate alone reads **0.10 — a
comfortable pass — on a stream whose envelope jumps 6 dB across the join**, because for broadband
noise adjacent samples are already nearly uncorrelated and no sample-level statistic can see an
envelope discontinuity in it. What a listener hears there is not a click, it is a surge once a
loop.

The pump gate's window is **derived from the signal**: at a fixed 20 ms it failed `structure_hull`
and `air_plenum`, which are perfectly continuous — 20 ms is a quarter-cycle at 14 Hz, so "the RMS
of the first 20 ms" was really "where in the bass cycle the buffer happens to start". It is now at
least four periods of the stream's own 5th-percentile frequency, measured off its spectrum.

---

## 8. The runtime

`godot/scripts/ambience.gd`. It **mixes, it does not choose** — every level comes from
`beds.json`.

- **WAVs are parsed by hand** into `AudioStreamWAV.data`. Godot's `.wav` import needs an editor to
  write the `.import` sidecar and everything here is generated headlessly; a build step that only
  works in a GUI is a build step that rots. Chunk-walked rather than assumed to start at byte 44.
- **The player's location is read off the geometry.** `rooms.py` already names room content
  `<place_key>__<group>`, so `bind()` merges an AABB per place from the mesh names. There is no
  second table of room bounds. Smallest containing box wins, and every box is grown 1.5 m so the
  beds are already mixing in the doorway.
- **Cross-fade is exponential in dB**, 2.5 s: you hear the next room before you are in it and the
  one behind you after you have left. A layer absent from the target bed fades out, which is what
  makes walking from a bar into a corridor sound like leaving a bar.
- **Point emitters** hang on `fix_*` and `prop_*` meshes by name match — ducts, furnace stacks,
  standpipes, the Garden's pool edge, intercoms. An emitter's level is the **direct** field at 1 m;
  the bed is the **reverberant** field, so the two do not double-count. Walk up to a duct and the
  duct gets louder while the room does not. Nearest 24 play, re-sorted twice a second.
- `describe()` prints one parseable line — place, hour, live layers with their **effective** level,
  emitters playing, last thing the tannoy said — because there is no way to listen to this build
  and a level that never moves between two rooms is a defect only the ear or that line can catch.
  It prints the effective level rather than the fader because a stream normalised to a lower RMS
  carries a positive trim: printing the fader alone made the sparse night crowd look 4 dB *louder*
  than the busy afternoon one when it is 13 dB quieter.

### It has been run

`godot --headless --script ambience_test.gd` against the assembled Blue 0/0 deck, in a
`git worktree` so it could not collide with the other agents:

```
ambience: 13/13 streams, 128 places, master trim 8.33 dB
ambience: bound 3 places, 6 emitters (cap 24)
PLACES 3 arrival_concourse, customs_north, customs_south
AMBIENCE place=customs_north     hour=03.00 layers=5 emitters=6
    pa="IN-SYSTEM SHUTTLE NOW ARRIVING, docking …"
    [air:air_duct -64.7, crowd:crowd_sparse -54.1, pa:pa_horn -79.7,
     structure:structure_hull -77.7, traffic:crowd_babble -63.2]
AMBIENCE place=customs_north     hour=13.00 layers=5 emitters=6
    [air:air_duct -64.7, crowd:crowd_babble -44.4, …, traffic:crowd_babble -59.7]
AMBIENCE place=arrival_concourse hour=03.00 layers=4 emitters=6
AMBIENCE place=arrival_concourse hour=13.00 layers=4 emitters=6
DISTINCT 4 of 4 — OK
```

A body **stood in each room** and `place_at` found it off the mesh names; the harness fails if it
does not. The crowd layer moves **+9.7 dB** across the night in the customs hall and switches
stream from `crowd_sparse` to `crowd_babble`. The concourse has no `traffic` layer and the customs
hall does, because only one of them declares `immigration`. The tannoy fires as a one-shot and
carries the line `broadcast.py` wrote for the ship `traffic.py` actually berthed.

The arithmetic chain is verifiable end to end from that line: `pa_horn` at −79.7 dBFS is
26 dBA − 94 (the 0 dBFS reference) + 8.33 (master trim) − 20 (the stream's own RMS).

Two things it caught, both now fixed: the harness's first version did everything inside
`_initialize`, so **nothing ever entered the scene tree** and every player refused to play; and it
forced `_here` instead of moving a body, which bypassed the one part of this that reads the
geometry and made four identical corridor beds look like a bug in the beds.

---

## 9. What is invented

Everything absolute. No frame of the show measures a sound pressure level and `reference/` has no
audio at all, so every dB here is authority 5. What is **not** invented is the shape: which place
is louder than which, and at what hour, falls out of modules that already existed.

| | what | anchored on |
|---|---|---|
| **INV-260** | the level ladder — living 35, quiet 30, circulation 45, working 60 dBA | NASA-STD-3001's 60 dBA continuous limit; NC-30 for a dwelling; the class distinction §3.1 already draws about water |
| **INV-261** | the structure layer and the spoke-pass modulation | canon's 33.4716 s period and `interior.SPOKE_COUNT = 3` |
| **INV-262** | the 0.75 Hz compressor beat | §2.3 says *beat*, which bounds it 0.5–4 Hz from both ends |
| **INV-263** | ᾱ = 0.15, 0.4 sabins a person, a 60 m acoustic horizon | a hard-surfaced interior; the same clamp `density.budget_area` makes for sight |
| **INV-264** | 25 dB through a station bulkhead | what makes §2.3's own sentence true |

Full entries in `canon/INVENTIONS.md`.

---

## 10. Running it

```bash
python3 station/audio.py --selftest     # 100 assertions, 6 negative controls
python3 station/audio.py --report       # every bed, itemised, with its reasons
python3 station/audio.py --write        # the WAVs, bank.json and beds.json
python3 station/audio.py --plots        # the three PNGs in this directory
python3 station/audio.py --bed zocalo --hour 3
```

## 11. What is not done

- **Nothing is mixed against a reference**, because there is no reference. Every level is
  internally consistent and externally unvalidated, and that is the honest state of it.
- **No event audio beyond the PA chime.** A door, a footstep, a till, a Starfury launch are all
  absent; `interact.py`'s eight verbs have no sound.
- **No occlusion or reverb zones.** The bed is a diffuse field per room and the cross-fade stands
  in for the transition; a closed pressure door does not currently muffle the room behind it,
  although `door.gd` knows exactly when it is shut.
- **The bed manifest is quantised to the hour** and the runtime does not interpolate between two
  hours, so a crowd that builds over twenty minutes arrives as a step. `populace.occupancy`'s own
  `_hour_factor` is a step function too, which is visible as the square edges in
  `docs/audio-day.png` — the corridor drops 11 dB at 02:00 and comes back at 05:00. Both are worth
  smoothing and neither is dishonest about what it is.
- **The runtime is verified headlessly and has never been heard.** `describe()` proves the beds
  reach the mixer, that `place_at` finds the room off the geometry, and that four cases give four
  different mixes. It proves nothing about whether it sounds good.
