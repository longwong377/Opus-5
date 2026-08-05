# PLAYTEST SCRIPT — what to do, what to look at, what is not there yet

**For a human with twenty minutes and a keyboard.** Everything below has been verified headless;
what a headless run cannot tell us is whether it *feels* like anything, and that is the only
question this document exists to answer.

**Read §0 before launching.** Half the value of a playtest is not spending it on something the
repository already knows is missing.

---

## 0. WHAT IS NOT THERE — do not go looking for it

Measured, not guessed. Wasting a session discovering these is the failure this section prevents.

**Four rows of this table were stale when session 4n checked them, and the direction of the
error is the one that costs a playtest most: they said *absent* about things that now work.**
A human who read the old §0 would have skipped the dialogue, the calendar and the Starfury —
the three most interesting things the build does. The rows below are re-verified, and each
says how.

| you will reach for | state |
|---|---|
| **a menu, map or inventory** | none. The only UI is the HUD line and `[E] operate the …`. |
| **the jump gate** | not wired. |
| **arriving as a person** | `--mode arrival` exists and is a sequence, not a character creation. No papers to be checked yet. |
| **the drum from inside** | `--mode drum` walks it, but the Garden is craft 1 — boxes and cylinder trees. Known, logged, not yet reworked. |
| **docking a Starfury** | launch works, docking does not — see below. |

### Corrected — these are IN, go and use them

| you were told | actually |
|---|---|
| *"nobody talks back"* | **157 of 157 exchanges offer a player line**, 69 distinct player utterances, press yields 120 / deflects 37, and the shipped `boot.json` carries 84 rows over four hours. The old row described a real defect with a misdiagnosed cause: `dialogue.gd` was 913 lines that had **never been instantiated on any path**, because `_wire_dialogue` ran above `_spawn_player()` behind an `if _player == null: return`. Fixed in `c59ff4e`. |
| *"a second day: `Clock` has no day index"* | it has one — `Clock.day()`, `day_offset`, `day_hour()` in `life.gd`, with the jump case guarded (without `day_offset` every clock jump silently returned the station to day 0). The verdict line prints `day=%d`. |
| *"nothing flies. Zero references in any `.gd` or `.tscn`"* | **false by grep**: `godot/scripts/starfury.gd` (34 references), `godot/scenes/starfury.tscn`, and 14 in `main.gd`. `godot --path godot -- --mode=starfury` flies one, with a flight model, a chase camera and floating-origin rebasing. |
| *"credits exist; no shop reads them"* | the bar's till debits. Fourteen days of one lurker: 267 → 420.50 cr, the bar's till 3,598.42, station stock 52,720 → 51,518, and `station/generated/economy.json` survives the process — a second run reads back the same purse. |

**The Starfury's honest remainder**: the mission is `ride → coast → transit`. It rides the
rotating cobra bay, is released at the correct phase, coasts, and runs out. **There is no dock
phase.** P4's bar is "launch → fly → dock, seamless" and half of it is built.

---

## 1. LAUNCH IT

```bash
godot --path godot                      # the shipped scene, no arguments
```

**Watch the first four lines of output.** They tell you what you got:

```
main: deck blue_0_0, spawn -19.10,-210.61,7120.94 in corridor, 6 rooms
main: STREAMED -- 18 cells from .../blue_0_0_cells.json, starting in cell 13
stream: 18 cells, radius 66.1 m, free at 73.8 m, budget 180000 tri = 3 cells
walk:  STREAMED level -- start cell 13, primed in 40 ms
```

- `STREAMED` is what you want. **`MONOLITHIC` means the cell set is missing** — run
  `python3 station/boot.py --bake` and relaunch. It will tell you why in the same line.
- A `-- STALE:` suffix means the cells are older than the deck. Harmless to walk; the geometry
  is a build behind.

---

## 2. THE FIVE MINUTES THAT MATTER

**Walk in a straight line down the corridor for a full minute without turning.** This is the
single most informative thing you can do. You are looking for: does the corridor *repeat*
visibly? Does the crowd read as people or as furniture? Do the cells hand over without a hitch
you can feel? *(`stream: +blue_0_0_cNN` appears in the log each time one arrives — glance at
whether you felt it.)*

**Then go into a room.** Any door. 115 of 116 places on the station can be entered and stood up
in; `vorlon_berth` is the one that cannot and is under investigation. What to judge: does the
room have a reason to exist, or is it a shape with props in it?

**Then look at these three specifically**, because they are the range of what the station
currently is:

| place | what it is | expect |
|---|---|---|
| the **core shuttle car** | built this session from an authority-1 frame | **the best interior in the project.** Craft 4. Red-maroon seating, amber plinth panels, grab poles. Side windows render black — a scene limitation, not the room |
| **`docking_bays`** | 140 m, the front door | correct in shape and **badly underlit** — 92% of a render is crushed to black. Three exposure knobs have been tried and characterised; it needs a lighting *design*, not a gain |
| any **generated room** | 58% of the station | craft 1–3. This is the honest middle |

---

## 3. THE COMPLETE LOOPS — there are three now

None are interactive; each runs headless and prints a verdict. Watch them in this order,
because each is built on the one above it.

```bash
python3 station/agenda.py --commute        # somebody goes to work
python3 station/dockwork.py --fortnight    # and gets paid for it, and spends it
python3 station/npc/encounter.py --gate    # and cannot get past a Narn in a corridor
```

**1 — the commute.** Londo Tirenne walks from `qtr_civilian`, rides the lift, and arrives at
his desk in `business_center`, **0.05 m from his post**, at three clock rates, with three
controls firing. The smallest complete thing the simulation does.

**2 — the job.** Anna Allan, human, a lurker with no job aboard, lands with **267 credits and
cannot afford the 300-credit passage home**. She stands the muster at `docking_bays`, works
crates, signs a manifest, drinks at the bar. After fourteen days: **267 → 420.50 cr**, the
bar's till at 3,598.42, station stock 52,720 → 51,518 — and she crossed the passage-home line
on day 4. The ledger survives the process and the engine prints it back:
`hud: purse player:downbelow 420.50 cr`.

**3 — the friction.** Two people pass in a corridor and it costs them metres.
`friction.separation_m("narn","centauri")` is **1.80 m**; a ring corridor's half-width at
blue/0/0 is **1.0806 m**, so the widest gap available is 1.64 m. **A Narn and a Centauri
cannot pass**, and the escalation is not authored — it falls out of the geometry. Over one
station-hour on that deck: 30,250 encounters, 11,157 carrying a grievance, 7,963 producing a
world delta, and **1,400.4 m of displacement** against a frictionless twin run with the same
people and the same seed. Lateral pass distance is the part you would actually see: 0.46 m
with no grievance, 0.64 m with one, **1.14 m for a Narn and a Centauri**.

---

## 4. WHAT TO WRITE DOWN

Not bugs — the gates find those. Write down the things a gate structurally cannot:

1. **Where did you get bored?** Name the metre.
2. **What did you walk up to expecting to use, and could not?** That list is the interaction
   backlog, in priority order, for free.
3. **Did it feel like 250,000 people, or like a corridor with some people in it?** The station
   derives its crowd from that figure; whether it *reads* is not derivable.
4. **Did anything look like Babylon 5 rather than like a sci-fi corridor?** Be specific and be
   harsh. `docs/AAA-STANDARD.md` C1 is "a box primitive standing in for a named object" and the
   project has shipped plenty.
5. **What made you turn around and go back?** Nothing yet should. If something did, it is the
   most valuable line in your notes.

---

## 5. IF IT WILL NOT LAUNCH

| symptom | cause |
|---|---|
| no window, no frames | Godot's `--headless` **disables rendering**. Drop the flag, or use `xvfb-run` as `tools/render_godot.sh` does |
| `MONOLITHIC` | no cell set for the boot deck — `python3 station/boot.py --bake` |
| black frames, no shadows | the renderer fell back to OpenGL 3 Compatibility. Grep the output for `Forward+`; if it says `Compatibility`, **the frames are not evidence** |
| a body standing still | check `main:` printed a `spawn` — a spawn outside the primed cell falls back to the cell's own floor point |

---

*Verified headless as of session 4n: `deck.py --sweep` 90/90 clusters, 128/128 locations,
0 floor holes · `boot.py --gate` 10/10 · `coldstart.py` G1+G3 pass with controls ·
`agenda.py --commute` green at ×1/×10/×60 · `economy.py` 25/25 · `dockwork.py` 23/23 with 5/5
controls · `faction.py --selftest` 27/27 · `friction.py --selftest` 30/30 ·
`encounter.py --gate` 23/23 · CPU frame time 5.48 ms against a 16.67 ms budget, GPU half
unknown · 300,000 frames and 21 km walked with 0 off-floor and no memory drift.*

*§0's four corrections were found by grepping the claims rather than by re-running them, which
is the cheap half of keeping this document honest. **A doc that says a thing is missing goes
stale in the expensive direction** — nobody re-checks an absence, so it silently becomes a
standing instruction not to look. Re-grep §0 before every playtest.*
