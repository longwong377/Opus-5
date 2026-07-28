# Gazetteer — Factions, Population and Friction

Who is aboard Babylon 5, how many, where they live and work, what they wear, what they do
in a day, and what happens when two of them pass each other in a corridor.

This file exists because `station/npc/` models names, species, roles and schedules but has no
basis for **faction composition**, and `canon/INVENTIONS.md` INV-005 flags the species mix as
the weakest part of that entry. Everything here is written to be consumed by a build agent with
no memory of the show.

---

## 0. How to read this file

### 0.1 Authority

The project's scale (`reference/README.md`, `canon/00-MASTER.md`):

| | |
|---|---|
| **1** | on-screen footage |
| **2** | production material (blueprints, production-model renders, publicity stills shot on set) |
| **3** | licensed print (technical manuals, official guides) |
| **4** | fan reconstruction (wikis, fan sites, forums, episode transcripts on fan sites) |
| **5** | our own extrapolation |

Every row carries an authority and a citation. **No row is written from unsourced memory.**

**The dagger, and why it matters.** A row marked **†** states a fact whose ultimate source is
on-screen (authority 1) or production material (authority 2), but which **was not verified
against footage or against a file in `reference/` during the session that wrote this file.**
The citation names the episode, and where a web source was used to corroborate it that source is
given at its own authority (4). A future session with footage access can promote a † row by
deleting the dagger; a session that checks one and finds it wrong should say so loudly.
Rows citing a file under `reference/` carry no dagger — those were read.

**Known weakness of this file's web evidence.** `WebFetch` is blocked by this container's egress
policy for every host tried (fandom, wikipedia, midwinter, reactormag, and a control host), so
**no web page was actually read.** Every authority-4 web citation below comes from a search
engine's *summary* of the page, not the page. Summaries can compress two facts into one and can
attach a claim to the wrong episode. Treat authority-4 web rows here as one notch weaker than a
normal authority-4 row and re-check them when fetching works.

### 0.2 What this file does not decide

`canon/CONFLICTS.md` **C-003** (which longitudinal band is the habitat drum) and **C-004**
(which concentric ring is level 1) are OPEN and BLOCKING. This file therefore places factions by
**sector name and ring *class*** — outer / middle / inner / axis — and by **named facility**,
never by level number. That is deliberate: `STATE.md` records that interior geometry is
generated against `(sector, ring_index)` and labelled afterwards by `bind_labels()`, so a
faction bound to a *named facility* survives both conflicts closing, and a faction bound to
"Brown 4" does not.

Where a row says **"unplaced"** the show never establishes the location. Those are collected in
§13 rather than being quietly dropped, because a known unplaced thing is worth more than a gap.

---

## 1. The era datum — and a contradiction inside the era lock

**This section is the most consequential thing in the file. Read it before using any number
below.**

`canon/00-MASTER.md` line 5 sets the lock as:

> **Era lock: Season 2–3.** Sheridan in command, defence grid installed, Kosh present,
> all League ambassadors resident, Zócalo at full operation, pre-secession, pre-war-damage.

Season 2 is the year **2259** and Season 3 is **2260**, both stated in the opening narration
(authority 1 †; narration text corroborated at
[ajbaker.force9.co.uk/b5titlequotes.html](http://www.ajbaker.force9.co.uk/b5titlequotes.html)
and [everything2.com](https://everything2.com/title/Babylon+5+Opening+Credits), authority 4).
The S2 narration also restates the population canon already in `00-MASTER.md` §1 verbatim:
*"A place of commerce and diplomacy for a quarter of a million humans and aliens."*

### 1.1 The events that bound the window

| # | Event | When | Authority | Source |
|---|---|---|---|---|
| E1 | Sheridan takes command | S2E01 *Points of Departure*, early 2259 | 1 † | Episode; `00-MASTER.md` era lock already assumes it |
| E2 | Narn–Centauri war opens (Centauri strike Quadrant 37) | S2E09 *The Coming of Shadows* | 1 † | Episode |
| E3 | ISN news crew embeds aboard for 36 hours | S2E15 *And Now For a Word* | 1 † | Episode; [astro.umd.edu review](https://www.astro.umd.edu/~avondale/Reviews/B5/s2-andnowforaword.html) (4) |
| E4 | **The Markab die.** Drafa plague; the species is effectively extinct, homeworld and colonies | S2E18 *Confessions and Lamentations* | 1 † | Episode; [TV Tropes recap](https://tvtropes.org/pmwiki/pmwiki.php/Recap/Babylon5S02E18ConfessionsAndLamentations) (4) |
| E5 | Talia Winters removed from the station; no resident Psi Corps commercial telepath after this | S2E19 *Divided Loyalties* | 1 † | Episode; [TVmaze 2x19](https://www.tvmaze.com/episodes/43466/babylon-5-2x19-divided-loyalties) (4) |
| E6 | **Narn surrenders.** G'Kar loses the Narn seat on the Advisory Council, is granted sanctuary aboard by Sheridan as military governor | S2E20 *The Long, Twilight Struggle*, late 2259 | 1 † | Episode; [AV Club](https://www.avclub.com/babylon-5-the-long-twilight-struggle-1798177070) and [fandom](https://babylon5.fandom.com/wiki/The_Long,_Twilight_Struggle) (4) |
| E7 | **Nightwatch surfaces aboard.** Ministry of Peace envoy Frederick Lantze and Mr Welles arrive; a shopkeeper is dragged away for sedition | S2E22 *The Fall of Night*, end of 2259 | 1 † | Episode; [fandom Nightwatch](https://babylon5.fandom.com/wiki/Nightwatch) (4) |
| E8 | Marcus Cole arrives; Rangers become a visible presence aboard | S3E01 *Matters of Honor*, 2260 | 1 | `reference/14-characters-and-uniforms/Marcus Cole in uniform.jpeg` — index entry states "In era for Season 3. Marcus is introduced in S3" |
| E9 | Brother Theo's monastic order takes up **permanent residence** | S3E02 *Convictions* | 1 † | Episode; [Reactor rewatch](https://reactormag.com/babylon-5-rewatch-convictions/) (4) |
| E10 | A Ministry of Peace political officer is posted aboard | S3E05 *Voices of Authority* | 1 † | Episode |
| E11 | **Martial law. Nightwatch attempts to take station security and is broken** | S3E09 *Point of No Return* | 1 † | Episode; [TVmaze 3x09](https://www.tvmaze.com/episodes/43478/babylon-5-3x09-point-of-no-return) (4) |
| E12 | **Babylon 5 secedes from the Earth Alliance** | S3E10 *Severed Dreams* | 1 † | Episode; [Wikipedia](https://en.wikipedia.org/wiki/Severed_Dreams) (4) |
| E13 | Kosh (the first) is killed; replaced by a second Vorlon who keeps the name | S3E15 *Interludes and Examinations* | 1 † | Episode; [fandom Ulkesh](https://babylon5.fandom.com/wiki/Ulkesh) (4) |

### 1.2 The contradiction

Read strictly, the lock's clauses cannot all be true at once:

- *"all League ambassadors resident"* requires **before E4** (S2E18) — after that the Markab do
  not exist.
- *Nightwatch present*, which the brief calls era-critical and which is a major S2–3 political
  layer, requires **after E7** (S2E22).
- *"pre-secession"* requires **before E12** (S3E10).
- *"Kosh present"* requires **before E13** (S3E15) — not binding, since E12 is earlier.

**E4 and E7 are mutually exclusive.** A station with Markab ambassadors and Nightwatch armbands
in the same frame never existed. `00-MASTER.md`'s era lock as written asks for one.

### 1.3 Recommendation — pick a datum, and pick this one

> **Station datum: early 2260, between E9 (*Convictions*, S3E02) and E11 (*Point of No Return*,
> S3E09).** Call it **"S3, pre-martial-law"**.

Everything in this file is written to that datum unless a row says otherwise.

Why this window and not the alternative — every cell below is decision support derived from the
authority-tagged events E1–E13 in §1.1, not a new claim:

| Wanted | S3 pre-martial-law | Pre-E4 (early-mid S2) |
|---|---|---|
| Nightwatch present and visible | **yes, at maximum** | no — does not exist yet |
| Narn refugee population, G'Kar in exile | **yes** | no — Narn is a great power, G'Kar is an ambassador |
| Narn/Centauri corridor friction | **maximum** | present but abstract; the war has not happened |
| Rangers aboard | **yes, semi-covert** | barely |
| Brother Theo's monks | **yes** | no |
| Kosh alive | yes | yes |
| Pre-secession, EA law and customs intact | **yes** | yes |
| All League ambassadors incl. Markab | **no — Markab extinct** | yes |
| Resident Psi Corps commercial telepath | **no — see §3** | yes (Talia Winters) |

The datum costs two things and buys six. It also converts the Markab loss from a hole into
content: **a sealed, dark, still-furnished Markab quarter in the Alien Sector** is a specific,
buildable, mournful place that a player can find, and it is the only monument on the station to
an entire species.

**Action required outside this file (do not do it here — `canon/` is not this agent's to edit):**
`00-MASTER.md`'s era-lock line needs "all League ambassadors resident" replaced with a datum, or
this contradiction will be rediscovered every few sessions. Logged in §14.

---

## 2. The population, top down

### 2.1 The hard numbers we have

| Quantity | Value | Authority | Source |
|---|---|---|---|
| Typical population | **250,000** | 1 | `00-MASTER.md` §1, S1/S2/S3 opening narration |
| "Crew" | **6,500** | 4 | `00-MASTER.md` §1, `other map 2.jpg`. **Ambiguous** — see §2.2 |
| Standing atmospheres available | **six**, numbered; others by prior arrangement | 1 | `00-MASTER.md` §1.4, `reference/01-station-exterior/welcome to babylon 5.webp` |
| Human atmosphere designation | **02** | 1 | Identicard field `DES/ATMOS: HUMAN/02` |
| Docking bays | **24**, plus low-g bays | 3 | `00-MASTER.md` §1.3, Security Manual sectional schematic |
| Bay elevators | **2** | 3 | Security Manual sectional schematic |
| Cargo bays | 28 rotating + 14 support = **42** | 4 | `00-MASTER.md` §1.3 |
| Sanctuaries | **4** | 3 | `00-MASTER.md` §1.3, Contract 5 |
| Starfury squadrons | **two** (≈24 fighters) | 1/4 | `00-MASTER.md` §1, C-002 reading |
| Species in the Alien Sector | **14** | 4 | [fandom Green Sector](https://babylon5.fandom.com/wiki/Green_Sector). See §14 for the conflict this creates |
| League members assigning ambassadors | all of them; **ten sit in Assembly at a time** | 4 | [fandom League of Non-Aligned Worlds](https://babylon5.fandom.com/wiki/League_of_Non-Aligned_Worlds) |
| Command-quarters rent | **30 credits/week** | 1 † | S2E08 *A Race Through Dark Places* — Earthforce bills Sheridan and Ivanova for oversized quarters |

There is **no canon figure anywhere for species proportions.** That is the gap INV-005 names,
and §2.4 fills it at authority 5 with reasoning rather than vibes.

### 2.2 The 250,000: resident, staff, transient

"Typical population" for a port is not a resident count — it is *residents plus whoever is in
port*. Splitting it is the single most useful thing that can be done to the number, because the
two populations behave completely differently: residents have homes, jobs and routes, and
transients have luggage, a hotel and about a week.

| Block | Count | Share | Authority | Reasoning |
|---|---|---|---|---|
| EarthForce and station staff | 6,500 | 2.6% | 4 | `other map 2.jpg` "crew 6,500". Read as **the whole EarthForce-employed complement**, military and uniformed civil service, not just line military — see the caveat below |
| Registered civilian residents | ~178,500 | 71.4% | 5 | Balance. Shopkeepers, traders, restaurateurs, contractors, medical, dependants, embassy staff, the whole commercial city |
| Transients in port | ~45,000 | 18.0% | 5 | Derived in §2.3 from bay count and turnaround; cross-checks against mean stay |
| Downbelow / unregistered | ~20,000 | 8.0% | 5 | Bracketed by an authority-4 estimate of ~13,000 lurkers and an upper reading of ~50,000 for all of Brown Sector ([b5tv.com forum thread](https://www.b5tv.com/threads/downbelow.6410/), authority 4 and *weak* — a forum estimate, not a source) |
| **Total** | **250,000** | 100% | | |

**Caveat on 6,500.** `other map 2.jpg` says "crew" without defining it. If it means line
EarthForce only, then the uniformed civil service (customs, quartermaster, post, judiciary,
environmental) sits inside the 178,500 civilian block instead and the military complement is
smaller. Both readings are buildable; this file takes the broad one because it puts a single
number against every EA-employed job the sourced facility list implies. Flagged in §14.

**Apportionment of the 6,500 (authority 5, but it produces the felt consequences below):**

| Branch | Heads | Why |
|---|---|---|
| Command and C&C | 120 | Three watches in Observation Dome 1 plus staff |
| **Security** | **500** | See the consequence below — this is the most load-bearing invented number in the file |
| Medical (Medlab 1–3) | 300 | |
| Flight ops: pilots, deck, ordnance | 350 | Two squadrons ≈24 craft, ~12 ground crew per craft plus ops |
| Engineering, power, environmental, fabrication | 1,800 | Grey and Yellow sectors are almost entirely this |
| Docking, cargo, traffic control | 1,200 | 28 bays on three shifts plus 42 cargo bays |
| Hydroponics, water, waste | 700 | |
| Administration, customs, quartermaster, post, supply | 900 | Two customs halls on three shifts is most of it |
| Maintenance, repair, EVA | 630 | |
| **Total** | **6,500** | |

**The consequence of 500, and it is worth building the station around.** 500 officers over
250,000 people is roughly one per 500 — comparable to a real city force — but spread across
three shifts and **8,047 metres**, so roughly **150 officers are on duty at any moment across
five pressurised sectors and 210 decks.** That is not a police presence; it is a *garrison at
chokepoints*. It means, concretely:

- Security is **visible and doubled** at the two customs halls, the Zocalo, the council
  approaches, the Business District and the bay elevators.
- Security is **absent** through most of the outer rings, and *entirely* absent in Downbelow
  except during a sweep.
- A player should be able to walk twenty minutes in Brown Sector and see no uniform at all,
  then turn into the Zocalo and see four.

That contrast — enforcement as a set of islands in an unpoliced volume — is what makes the crime
layer credible, and it falls out of one number.

### 2.3 Arrivals — the station as a working port

The owner asked for "transports and visitors constantly arriving, the jump gate working". This
is the traffic model, derived from the sourced bay counts. **Authority 5 throughout**, but every
assumption is stated so a builder can dial it.

Given: **24 docking bays + 4 low-gravity bays = 28** (authority 3, `00-MASTER.md` §1.3 and the
sectional schematic's "LOW-G DOCKING BAYS").

| Step | Assumption | Result |
|---|---|---|
| Mean bay occupancy | 70% | 19.6 bays occupied |
| Mean berth-to-berth cycle | 9 h (approach, unload, service, load, depart) | **2.18 arrivals/hour** |
| | | **≈ 52 arrivals + 52 departures per station-day** |
| Mean souls disembarking per arrival | 120 (liners 300–800; freighters 8–25 crew; shuttles 20–60; diplomatic craft 5–20) | **≈ 6,300 arrivals/day** |
| Customs transactions | in + out | **≈ 12,600/day** across two halls |
| Averaged customs rate | | **≈ 4.4 people/minute/hall** — but arrivals come in *waves*, so design the hall for a **peak of 20–40/minute** and long dead periods |
| Mean visitor stay | 7 days | **standing transient population ≈ 44,100** |

That last line closes the loop: 6,300/day × 7 days ≈ 44,100, which is the ~45,000 transient
block in §2.2, derived independently. The model is self-consistent.

**Traffic composition per station-day (authority 5):**

| Class | Movements/day | Notes |
|---|---|---|
| Passenger liners and packets | 6 | The big arrivals. One liner is a visible event: the concourse fills |
| Bulk freighters | 18 | Cargo bays, not passenger bays. Crew of 8–25, ashore for a day |
| Short-haul shuttles and tenders | 16 | Local runs, jump-gate transfers, ship-to-station |
| Diplomatic and government craft | 4 | Escorted, priority berth, customs waived or expedited |
| Military (EarthForce, and alien warship visits) | 3 | Alien warship arrivals are a security event in their own right |
| Unscheduled: distressed, refugee, contraband, unidentified | 5 | **The interesting five.** Refugee hulls in this era are usually Narn |
| **Total** | **52** | |

**The jump gate is a separate structure, not part of the station.** It sits in the Epsilon
Eridani system near Babylon 5 and every arrival and departure passes through it (authority 1 †,
seen in most episodes). A builder must not attach it to the hull. Traffic behaviour: a ship
appears at the gate, runs in on approach, is handed to Command and Control in Observation Dome 1
and **surrenders shipboard control to C&C on entering the main dock** (authority 4,
[visitbabylon5 fan site](https://sites.google.com/view/visitbabylon5/home/customs/blue-sector/observation-dome/babcom-station-map);
consistent with authority-1 C&C footage in `reference/03-sector-blue/comand and contorl.webp`).

### 2.4 The species mix — replacing `STATION_MIX`

`station/npc/schedule.py` currently carries six species summing to 1.0. Six species cannot
produce a crowd that reads as a galactic port, and three of the six shares are too high for what
those species actually are.

**Proposed mix. Authority 5 throughout — no source states any of it — but each row's reasoning
is given, and the whole thing sums to exactly 250,000 and exactly 1.000.**

| Species | Count | Share | Was | Reasoning |
|---|---|---|---|---|
| **Human** | 155,000 | 0.620 | 0.62 | **Unchanged, and defensible on structure rather than headcount.** The station is Earth Alliance sovereign territory: EA law, EA judiciary (Ombuds), EA customs, EA currency, Earth Mean Time, and human atmosphere as 02 of six. Every service function — docks, power, environmental, medical, security, administration — is contracted through EA and therefore staffed by EA citizens. The employed resident population is human by construction, not by preference |
| **Narn** | 22,500 | 0.090 | 0.10 | Second largest, and **the fastest-growing and fastest-impoverishing population on the station in this era.** Pre-war they were traders and shipping agents from an aggressive commercial power; after E6 they are a stateless refugee influx. 9% is *earned by the datum* |
| **Centauri** | 17,500 | 0.070 | 0.09 | **Reduced.** A contracting aristocratic power whose depicted presence is a diplomatic mission plus a merchant and financier class. 22,500 Centauri implies a settler population the Republic does not have. They are also *more conspicuous* post-war, not more numerous |
| **Minbari** | 12,500 | 0.050 | 0.07 | **Reduced.** Eleven years after the Earth–Minbari War, Minbari do not settle among humans in numbers. What is aboard is the mission, religious-caste scholars and pilgrims, and worker-caste technicians |
| **Drazi** | 12,500 | 0.050 | 0.07 | **Reduced slightly but kept as the largest League species.** On screen the Drazi are the League species most often in the background doing physical work |
| **Brakiri** | 7,500 | 0.030 | — | **New.** A commercial power; traders and financiers. Described as night-dwellers (authority 4, [fandom](https://babylon5.fandom.com/wiki/League_of_Non-Aligned_Worlds)), which gives the station-night a specific crowd |
| **pak'ma'ra** | 6,250 | 0.025 | 0.05 | **Halved.** 12,500 is far too many for a species treated as a marginal League power. Kept visible because they anchor the waste/carrion layer and the segregated food areas |
| **Vree** | 5,000 | 0.020 | — | **New.** Traders; saucer craft; League members |
| **Abbai** | 3,750 | 0.015 | — | **New.** League founders and mediators (authority 4, fandom). Amphibian — ties directly to the numbered-atmosphere and humidity system |
| **Gaim** | 2,500 | 0.010 | — | **New, and structurally important.** Methane breathers in encounter suits (authority 4, [fandom Gaim](https://babylon5.fandom.com/wiki/Gaim)). **They are the visible reason the Alien Sector exists** |
| **Hyach** | 1,750 | 0.007 | — | **New.** League members; long-lived, formal |
| **Llort** | 1,250 | 0.005 | — | **New.** Reputation as scavengers and thieves — useful for the crime layer |
| **Grome** | 750 | 0.003 | — | **New.** League members |
| **Other / unclassified** | 1,250 | 0.005 | — | The tail: rare League species, unidentified traders, one-off visitors. Give this bucket a *rotating* model set so the tail never looks like the same six aliens |
| **Vorlon** | **1** | — | — | **Kosh. A singleton, and it must not be a share.** `int(250000 × share)` for one person is a rounding artefact waiting to become zero or three. Hard-code it |
| **Total** | **250,000** | **1.000** | | |

Verified: the counts sum to 250,000 exactly and the shares to 1.000 exactly. INV-005 records
that the previous mix summed to 0.94 and silently dropped 120 residents per 2,000 — **any
replacement must be asserted to sum to 1.0 in a test, not checked by eye.**

**Markab: zero.** Extinct at the datum (E4). If a future session moves the datum before S2E18,
add Markab at ~0.008 and take it off the "other" bucket and Brakiri.

**The mix is a *standing* mix, and it is not uniform across the station.** Transients skew alien
(ship crews, traders, delegations); residents skew human (EA employment). The consequence is
that **the docks and customs are the most alien places on the station and Blue Sector crew
country is the most human**, which is exactly the gradient a player should feel while walking.

### 2.5 Where the crowd is — per-place composition

This is the table the NPC spawner wants. Human share is the fraction of the standing crowd;
"dominant non-humans" is ranked. Hours are Earth Mean Time (authority 1, `00-MASTER.md` §1.4).
**Facility names are authority 3** from the `other map.png` rosettes and the Security Manual
sectional schematic unless noted; **crowd composition and hours are authority 5.**

| Place | Sector · ring class | Human share | Dominant non-humans | Busy | Dead | Character |
|---|---|---|---|---|---|---|
| **Zocalo** | Red · outer | 0.45 | Narn, Drazi, Centauri, Brakiri | 11:00–15:00, 18:00–24:00 | 04:00–07:00 | The station's main social space; two-storey with an upper gallery (authority 1, `reference/04-sector-red/more zocalo.png`). Never empty, but at 05:00 it is a lit hall with six people in it |
| **Customs halls (×2, north and south)** | Blue · outer | 0.40 | everything, in waves | arrival waves | between waves | The most species-diverse space on the station. Queues, encounter suits, breather-mask dispensers |
| **Central Corridor** | Red · outer | 0.55 | Drazi, Narn, pak'ma'ra | 07:00–09:00, 17:00–19:00 | 02:00–05:00 | Commuting artery. Two occupied levels in one volume (authority 1, `reference/09-garden-core-and-transit/central corridor.webp`) |
| **Earhart's** | Red · outer, in the drum | 0.80 | Centauri, Minbari | 19:00–02:00 | daytime | EarthForce bar. Off-duty uniforms. Stands on the drum floor under the far side (authority 1, `reference/04-sector-red/Earhart's.webp`) |
| **Dark Star** | Red | 0.50 | Drazi, Narn, Llort | 21:00–04:00 | daytime | Rougher venue; planted entrance (authority 1, `reference/04-sector-red/Darkstar_logo.webp`) |
| **Casino** | Red · inner | 0.50 | Centauri, Brakiri, Drazi | 20:00–04:00 | 06:00–11:00 | Centauri over-represented — gambling is culturally theirs |
| **Business District / Business Center** | Red · inner | 0.65 | Brakiri, Centauri, Hyach | 09:00–17:00 | nights | Currency exchange (authority 1, customs board), banking, brokerage, guild offices. **Rigid human office hours in a station with no day** |
| **Law Courts** | Red · inner | 0.75 | Narn, Centauri, Drazi | 09:00–16:00 | nights | Ombuds hearings. Jurisdiction disputes are routine |
| **Security Central** | Red · inner | 0.95 | — | 24 h | — | Three shifts. **At the datum, a visible split in one uniform — see §4** |
| **Docking bays 1–24, bay elevators** | Blue · outer | 0.60 | Drazi, Narn, pak'ma'ra, Vree | 24 h, peaked | — | Dockers' Guild territory. Heavy work; the Drazi share is highest here |
| **Dock Workers' Quarters** | Blue | 0.70 | Drazi, Narn | 06:00–08:00, 15:00–17:00 | — | Shift-change surges. Cramped, functional |
| **Medlab One** | Blue · inner | 0.70 | all | 24 h | — | Six atmospheres means six kinds of emergency |
| **Mess Hall, Quartermaster, Post Office** | Blue | 0.90 | — | mealtimes / 09:00–17:00 | — | Crew country. The most human place aboard |
| **Council Chamber and approaches** | Green · outer | 0.35 | Minbari, Centauri, Drazi, Brakiri, Abbai | session hours | otherwise | Delegations, aides, guards, press. Restricted access |
| **Ambassadorial suites** | Green | 0.30 | Minbari, Centauri, League | 24 h | — | Each suite is its own culture, atmosphere and gravity preference |
| **Alien Sector** | Green · outer | **0.05** | Gaim, Abbai, non-oxygen species | 24 h | — | Airlocks, breather-mask dispensers, **non-standard atmospheres**. Its residents call the rest of the station the alien sector |
| **Fresh Air Restaurant** | Green, open to the drum | 0.60 | Minbari, Centauri | 12:00–14:00, 19:00–22:00 | — | Open terrace under the far side of the drum (authority 1, `reference/11-props-and-technology/fresh air resturant signage with view.webp`) |
| **Zen Garden** | Green | 0.50 | Minbari (religious caste) | 06:00–08:00, 21:00–23:00 | midday | Quiet. The Minbari over-representation is the point |
| **Hydroponics** | Green | 0.85 | Abbai, Grome | 05:00–13:00 | nights | Agricultural shift, not an office shift |
| **The Garden (drum floor)** | Green (contested, C-003) | 0.65 | Minbari, all | 09:00–18:00 | night | A **townscape**, not a park — buildings, surface transit, civic landscaping (authority 1, `reference/03-sector-blue/Babylon_5_2-22_29a.jpg`, `garden.png`) |
| **Downbelow** | Brown · outer | 0.68 | Narn, Drazi, pak'ma'ra, Llort | 24 h, no rhythm | — | **The one place with no schedule.** See §11.2 |
| **Sanctuaries (4)** | unplaced | 0.60 | Minbari, Narn, all | varies by faith | — | The home of `Activity.WORSHIP`. See §11.3 |
| **Fabrication furnaces, power, repair** | Grey · outer | 0.90 | Drazi, Gaim | 24 h, 3 shifts | — | Industrial. Grey holds 90 of the station's 210 decks (`STATE.md` session 2w) |
| **Zero-G maintenance, coolant, holding tanks** | Yellow | 0.95 | — | 24 h, thin | — | Almost nobody. Two or three suited figures in a kilometre |

---

## 3. Earth Alliance

The station's sovereign. Every other faction aboard is a guest of this one, and at the datum
that fact is becoming coercive rather than administrative.

### 3.1 EarthGov — the political layer

| Fact | Detail | Authority | Source |
|---|---|---|---|
| Head of state | **President Morgan Clark**, in office since the assassination of President Santiago at the end of S1 | 1 † | Episodes; [fandom Ministry of Peace](https://babylon5.fandom.com/wiki/Ministry_of_Peace) (4) |
| Ministries renamed | Ministry of Defense → **Ministry of Peace** (MiniPax); Ministry of Information → **Ministry of Truth** | 4 | [fandom Ministry of Peace](https://babylon5.fandom.com/wiki/Ministry_of_Peace) |
| Ministry of Peace stated purpose | internal security and safety; peace between humans and other races | 4 | ibid. |
| Ministry of Peace actual function | propaganda instrument; dissent relabelled treason; relaxed standards of evidence; past associations admissible | 4 | ibid. |
| Political officer posted aboard | from S3E05 | 1 † | S3E05 *Voices of Authority* |
| Station's legal status at the datum | **Earth Alliance territory**, pre-secession. Sheridan holds the powers of a **military governor** — this is what let him grant G'Kar sanctuary | 1 † | S2E20; [AV Club](https://www.avclub.com/babylon-5-the-long-twilight-struggle-1798177070) (4) |

**Visible expression.** EarthGov is not a costume, it is a *set of surfaces*: ISN on the public
screens, Ministry of Peace notices in the customs halls, the Earth Alliance seal, and the fact
that the recruiting stall in the Zocalo is not selling anything.

### 3.2 EarthForce — the command structure aboard

At the datum. All roles authority 1 †; the ranks marked (4) are corroborated only from a wiki.

| Post | Holder | Rank | Where | Note |
|---|---|---|---|---|
| Commanding officer / military governor | **John Sheridan** | Captain | C&C (Observation Dome 1); station commander's administration complex | Took command S2E01 |
| Executive officer | **Susan Ivanova** | Commander | C&C | Also runs C&C watch and flies Starfuries |
| Chief of security | **Michael Garibaldi** | Chief Warrant Officer (4, [Wikipedia](https://en.wikipedia.org/wiki/Michael_Garibaldi)) | Security Central | **Refuses all association with Nightwatch** |
| Chief medical officer | **Stephen Franklin** | Doctor (Lt Cdr equivalent) | Medlab One | Ran a telepath underground railroad in S2E08 — an officer with a secret |
| Second in security | **Zack Allan** | Sergeant, later Lieutenant (4, [fandom](https://babylon5.fandom.com/wiki/Zack_Allan)) | Security Central, patrol | **Wears the Nightwatch armband at the datum** |
| Security officer | **Lou Welch** | — | patrol | |
| C&C watch officer | **David Corwin** | Lieutenant | C&C | |
| Zeta Squadron leader | *(vacant at the datum)* | — | cobra bays | **Warren Keffer held it in S2 and is killed in S2E22. Out of era for an S3 datum** — do not place him |

**Squadrons.** Two (authority 1/4, `00-MASTER.md` §1). **Zeta Squadron** is named on screen
(authority 1 †); "Delta Wing" is attested at authority 4
([fandom Starfury Squadrons](https://babylon5.fandom.com/wiki/Starfury_Squadrons)). Twenty-four
fighters reconciles C-002's 28 bays with 24 craft — `00-MASTER.md` already carries that reading.

### 3.3 EarthForce uniform — the definitive in-era description

The project holds a **very good in-repo reference** for this, and it includes the discriminator
that tells S2–3 from S1. Do not dress NPCs from the vector sheets: those are the S1 pattern.

| Item | Description | Authority | Source |
|---|---|---|---|
| **Command, S2–3** | Slate blue-grey wool body. **Brown leather plastron/bib** covering the whole centre front from the standing leather collar down, edged with **crimson piping**. Crimson piping on both collar edges and as a welt along the top of each shoulder. Leather epaulette straps carrying a **flat gold trapezoidal wedge** near the neck; matching gold wedge on a black collar tab at the throat. Left upper sleeve: embroidered **EarthForce wings badge** — gold outspread wings flanking a red-and-white device on a blue ground. Right chest: plain gold name bar under a dark blue rectangular device | **2** | `reference/14-characters-and-uniforms/Sheridan.jpg` |
| **The S1/S2–3 discriminator** | S2–3 has **crimson piping and a leather bib**. S1 has **neither** — cloth panels, no piping | **2** | ibid.; contrast `Chief of security Garibaldi.webp` (S1) |
| **Security, S2–3, service dress** | Medium grey twill jacket; **black leather standing collar and yoke**; black leather epaulettes; two flapless breast pockets with horizontal welt seams; gold triangular pin at the throat | **2** | `reference/14-characters-and-uniforms/Zach Allan in security uniform.jpg` |
| **Security, S2–3, duty rig** | The same grey jacket **with a black tactical vest over it**. Two distinct security silhouettes to model | **1** | `reference/14-characters-and-uniforms/security in uniform.jpg` |
| **Security badge** | Right chest. Gold-outlined diamond with slightly convex sides on a black field, containing a gold circle crossed by **four tapered spokes** running out toward the diamond's points, with a small gold-outlined square ring at the exact centre. A crosshair in a diamond | **2/1** | Both files above, independently |
| **The link** | Left wrist, **on the back of the wrist**. Small shield-shaped plate — flat top, straight sides, chamfered lower corners to a shallow point — in polished white metal on a dark strap, face carrying a dark inlaid glyph of nested angle brackets | **2** | `Zach Allan in security uniform.jpg` at 8× |
| **Sidearm** | EarthForce-issue PPG. **Do not model it from `Chief of security Garibaldi.webp`** — the index explicitly rules that frame out | 1 | `reference/11-props-and-technology/Earthforce issue Auricon PPG Pistol with removable sight.webp` |
| **Station patch** | Red-outlined shield split diagonally, grey lower-left / blue upper-right, **seven white stars (four on grey, three on blue)**, yellow-and-black "5" on a vertical sword. Corroborated at two independent authority-4 sources | 4 | `reference/16-signage-typography-ui/babylon 5 shield.webp`; `uniform-army-of-light.jpg` |

**Out of era, do not build:** the **Army of Light** uniform and its insignia (S4 formation) and
the **Interstellar Alliance** seal (S4–5). Both are present in
`reference/16-signage-typography-ui/faction symbols.png` and both are flagged there.

### 3.4 The civilian administration

Everything here is bound to a **named facility from an authority-3 plan**, which is why this
section is unusually safe to build.

| Body | Facility (authority 3) | What it does daily | Authority for the body |
|---|---|---|---|
| **Judiciary — the Ombuds** | **Law Courts**, Red rosette | Adjudicators administering Earth Alliance law over civil suits and criminal trials; **jurisdiction conflicts between humans and aliens are routine and are frequently deferred**. Above them: appeals courts, then Final Appeal, then in serious cases a Senate Appeal Board. At least two Ombuds aboard (Wellington, Zimmerman) | 4 — [fandom Ombudsmen](https://babylon5.fandom.com/wiki/Ombudsmen), [Wellington](https://babylon5.fandom.com/wiki/Wellington). On screen from S1E15 *Grail* (1 †) |
| **Customs** | **Customs (×2, north and south)**, sectional schematic; "**Customs Sector**" used as an area label | Identicard check, atmosphere declaration, visa check, contraband. The information boards are authority-1 in-repo | 1 — `00-MASTER.md` §1.4 |
| **Currency and exchange** | **Business Center** / **Business District** | Monetary exchange "through Business Center" — verbatim from an authority-1 board. Currency is **credits** | 1 — `reference/01-station-exterior/welcome to babylon 5.webp` |
| **Quartermaster's Office** | Blue rosette | Berthing, stores, allocation of quarters by class | 3 |
| **Post Office** | Blue rosette | Physical mail and package handling, station-wide | 3 |
| **Traffic control** | **Observation Dome 1 = Command & Control** | All ship traffic; arriving ships surrender shipboard control | 3 + 1 |
| **Atmosphere Monitoring Station** | Grey rosette | Manages the **six standing atmospheres** and bespoke mixes | 3 |
| **Waste Management Control** | Brown rosette; "Waste Management Systems ('Down-Below')" on the sectional schematic | The physical and social bottom of the station — see §11.2 | 3 |

**Identicard, and why it is the spine of the civil layer.** The record schema is authority 1
(`reference/11-props-and-technology/identicard readout.webp`, in `00-MASTER.md` §1.4):
`NAME` · `ORIGIN` · `DES/ATMOS` · `SEX` · `DOB` · `PHYS CHR` · `MEDICAL` · `LICENSED PSI` (flag)
· `VISAS`. Two fields in that list are whole gameplay systems:

- **`LICENSED PSI`** — the station knows, on a card, whether you are a registered telepath. That
  is Psi Corps registration made physical (§4).
- **`VISAS`** — therefore **visa fraud, forged identicards and expired status are the station's
  most ordinary crimes**, and the reason lurkers avoid readers.

---

## 4. Psi Corps

### 4.1 Standing

| Fact | Detail | Authority | Source |
|---|---|---|---|
| Registration is on the identicard | `LICENSED PSI` is a field on every resident's card | **1** | `reference/11-props-and-technology/identicard readout.webp` |
| Commercial telepaths | Hired out for business negotiation and contract work. **Babylon 5 had a resident commercial telepath (Talia Winters) through S1–S2** | 1 † | Episodes |
| **At the datum there is no resident Psi Corps commercial telepath** | Talia is removed in S2E19 and is not replaced by the Corps | 1 † | S2E19; [TVmaze 2x19](https://www.tvmaze.com/episodes/43466/babylon-5-2x19-divided-loyalties) (4) |
| Lyta Alexander is aboard in S3 | Returns in S2E19; recurring through S3. **She is not working for the Corps** | 1 † | ibid. |
| Psi Cops visit, they do not reside | Bester comes aboard on operations (S2E08) and leaves. A Psi Cop arrival is a station-wide event | 1 † | S2E08 *A Race Through Dark Places* |
| Rogue telepaths and the underground railroad | An underground railroad moving rogue telepaths runs **through Babylon 5**; a station officer is complicit | 1 † | ibid. |
| How they are regarded | Feared by mundanes, hated by rogues, needed by business | 1 † | Series-wide |

**The buildable consequence.** The Corps is present aboard as **paperwork, a badge and a
threat**, not as a garrison. At the datum, model:

- a small **Psi Corps liaison office** (unplaced — see §13) with 3–8 staff, mostly clerical,
  handling registration, licences and hiring;
- **10–40 registered commercial telepaths** aboard at any time, most of them freelancers passing
  through rather than Corps-resident, hired by hour for negotiations in the Business District;
- an unknown number of **unregistered telepaths hiding in Downbelow** — deliberately unknowable,
  which is the correct way to model it (they do not appear in the census);
- a **Psi Cop visit every few weeks** as a scheduled world-event: corridors quieten, security
  escorts, the Zocalo's volume drops.

### 4.2 Dress — and an unresolved contradiction inside this repository

| Item | Description | Authority | Source |
|---|---|---|---|
| **Badge** | A **downward-pointing cut-diamond/pentagon in polished silver-chrome**, bearing a raised Greek **Ψ**, three tines rising from a stem. Worn high on the left chest. Buildable as one small decal or mesh | **1** | `reference/14-characters-and-uniforms/Talia Winters in uniform.webp`, resolved at 8× |
| **Gloves** | Black gloves — telepaths avoid skin contact | 1 † | Series-wide; asserted in `reference/22-QUARANTINE-ai-generated/README.md` |
| **Suit, reading A** | Structured jacket and pencil skirt in **warm mustard-tan / gold-ochre**, black inset panels forming a deep V at the front and running down sides and sleeves, strong squared shoulders | **1** | `reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp`, session-2s entry |
| **Suit, reading B** | Jacket **dark olive-green/black** with a shawl-style asymmetric wrap collar crossing right over left, black inset panel over the right shoulder | **1** | `reference/14-characters-and-uniforms/Talia Winters in uniform.webp`, session-2s entry |
| **Suit, reading C** | "**pale grey** Psi Corps suit with black gloves" | 1 (asserted) | `reference/22-QUARANTINE-ai-generated/README.md` |

**The contradiction, stated plainly.** `reference/22-QUARANTINE-ai-generated/README.md`
quarantines an AI turnaround *specifically because* it puts Talia in mustard/ochre, and cites
`talia-winters in gorgeous office.webp` as the genuine screencap that proves it wrong. The
session-2s index entry **for that exact file** describes her in "the Psi Corps **gold/ochre**
suit — structured jacket and pencil skirt in a warm mustard-tan". The repository's own two
records of the same image disagree, and the later one was made at magnification.

**Proposed resolution, offered for a canon session to rule on rather than taken here.** The
quarantine *decision* stands — an AI turnaround is untrustworthy whatever colour it picks — but
the *reason given* for it is wrong. The likeliest reading is that there is no single Psi Corps
uniform colour: the costume varies by episode across grey, olive-black and tan/ochre. Therefore:

> **Build the Psi Corps identity from the invariants — the silver Ψ badge, the black gloves, the
> squared shoulders and the black inset panelling — and treat body colour as a per-NPC variant
> drawn from {pale grey, olive-black, tan-ochre}.** Do not hard-code one colour.

Logged in §14 as a contradiction for `canon/` to adjudicate.

---

## 5. Nightwatch — the era-critical layer

**Getting this wrong misplaces an entire political dimension, so the timing is stated first.**

### 5.1 Timing — what is true when

| Window | Nightwatch state | Build |
|---|---|---|
| S2E01 – S2E21 (most of 2259) | **Does not exist aboard.** Not founded, not recruiting, no armbands | Nothing. Any armband before *The Fall of Night* is an error |
| **S2E22 (*The Fall of Night*), end of 2259** | Surfaces. Ministry of Peace envoy Frederick Lantze and **Mr Welles** arrive; Welles meets members already recruited aboard "informally" and singles out Zack Allan for filing no reports; **a shopkeeper accused of sedition is physically dragged away and imprisoned by Nightwatch officers** | The moment the layer switches on |
| **S3E01 – S3E08 (early 2260) — THE DATUM** | **Present, growing, openly wearing armbands, and not yet in control.** Reporting, denunciations, pressure on merchants and on officers | **This is what to build** |
| **S3E09 (*Point of No Return*)** | Martial law declared. Nightwatch attempts to take over station security and is broken | A scripted event, outside the ambient state |
| S3E10 onward | Out of era — secession | Do not build |

Authority for the above: episodes (1 †), corroborated at
[fandom Nightwatch](https://babylon5.fandom.com/wiki/Nightwatch) and
[fandom Ministry of Peace](https://babylon5.fandom.com/wiki/Ministry_of_Peace) (4).

### 5.2 What it is

| Fact | Detail | Authority |
|---|---|---|
| Parent body | A paramilitary division of the **Ministry of Peace**, set up under President Clark, **2259** | 4 |
| Membership | Civilians, law enforcement and military personnel recruited to report on activity seen as a threat to the regime | 4 |
| What counts as reportable | Criticism of Clark; **being too friendly with aliens**; anything else the regime dislikes | 4 |
| Motive for joining, as depicted | **Money.** Zack Allan joined for the bonus pay and became progressively more disturbed by what followed | 4, and 1 † on screen |
| Method | Reports filed on neighbours, colleagues and customers; arrest for "sedition"; relaxed evidentiary standards | 4 |

### 5.3 The armband — a precise, in-repo, authority-2 asset

> **Left forearm. Black band, gold embroidery: a stylised eye inside a swept almond/wing outline
> with a small triangle above the pupil, over the words "NIGHT WATCH" in gold caps.**
>
> — `reference/14-characters-and-uniforms/Zach Allan in security uniform.jpg`, read at 6–8×
> (authority **2**). The index entry notes the armband is what dates the still to the late-S2 /
> S3 window.

This is one decal and one strap mesh, and it is the entire visual signature of the layer. Worn
**over the ordinary uniform or civilian clothes** — there is no Nightwatch costume, which is the
point: anyone might be wearing one under a coat.

### 5.4 Strength aboard, and the visible consequence

**Authority 5**, reasoned:

| Group | Count | Reasoning |
|---|---|---|
| Security officers wearing the armband | **150–200 of 500 (30–40%)** | Recruitment was by cash bonus into a modestly-paid force. For the S3E09 takeover attempt to be plausible they must already be a large minority of security before reinforcement |
| Civilian informers among the human population | **1,500–3,000** (1–2% of 155,000) | Enough that a denunciation is credible in any public room; too few to be a crowd |
| Ministry of Peace staff posted aboard | 5–15 | Political officer, aides, clerks |

**The single best piece of environmental storytelling on the station falls out of this:**

> **One in three security officers wears the armband. The other two do not. It is the same
> uniform.**

A player walking past a two-officer patrol at the datum should be able to see one band and one
bare sleeve, and understand from that alone that the force is split. Garibaldi, the chief,
refuses all association (1 †); Zack, his second, wears one (authority 2, the still). Model the
armband as a **per-NPC boolean on the security uniform**, not as a separate NPC type.

Ambient behaviours to build: a denunciation box or reporting terminal in the Zocalo and the
customs halls; two armbanded officers questioning a merchant while the merchant's neighbours
find something else to look at; conversation volume dropping when an armband enters a bar.

---

## 6. Narn Regime

### 6.1 The situation, and it changes completely mid-era

Periods and Narn status are **authority 1 †** (events E2 and E6 in §1.1); "Narn aboard" is
**authority 5**, being this file's reading of what those events do to a resident population.

| Period | Narn status | Narn aboard |
|---|---|---|
| S2E01 – S2E08 | A great power. Aggressive commercial and military expansion | Ambassador G'Kar with a full mission; traders, shipping agents, mercenaries |
| S2E09 – S2E19 | **At war with the Centauri**, losing | The mission is a wartime legation; merchants begin losing routes |
| **S2E20 onward — THE DATUM** | **Defeated and occupied.** The Kha'Ri surrendered; the homeworld was bombed; Narn is a Centauri protectorate | **A stateless refugee population.** G'Kar is a private citizen in sanctuary and leads a government-in-exile |

Terms of the surrender include the Kha'Ri surrendering for trial, and **any murder of a Centauri
by a Narn punished by the execution of five hundred Narns including the murderer and his family**
(authority 1 †, S2E20; corroborated
[fandom](https://babylon5.fandom.com/wiki/The_Long,_Twilight_Struggle), authority 4). That single
provision is why a Narn in a corridor at the datum does not start a fight no matter how much he
wants to — and why the tension reads as *restraint*, not brawling.

Under the occupation, millions on Narn were put into work farms, construction gangs and
relocation camps as slave labour (authority 4,
[fandom Second Centauri Occupation of Narn](https://babylon5.fandom.com/wiki/Second_Centauri_Occupation_of_Narn)).
G'Kar leads the resistance and the government-in-exile **from Babylon 5**, and with Garibaldi's
help establishes a route for smuggling weapons to Narn (authority 4,
[fandom Narn Resistance](https://babylon5.fandom.com/wiki/Narn_Resistance)).

### 6.2 Who and how many

**Counts are authority 5**, apportioning §2.4's 22,500 Narn. The apportionment is what the datum
implies: a merchant community that has lost its home ports, plus a refugee influx that did not
exist eighteen months earlier.

| Group | Count | Where | Doing what |
|---|---|---|---|
| **G'Kar and his household** | 30, of whom **1 is G'Kar** | His former ambassadorial suite, retained as a private residence (Green sector, ambassadorial suites) | Government-in-exile; resistance coordination; **no council seat**. The household are couriers and aides, no longer accredited diplomats |
| Resident Narn traders and shipping agents | 6,000 | Red and Blue outer rings; Zocalo stalls; the docks | A trade network with its home ports occupied — many are now buying rather than selling, and many are broke |
| **Refugees** | **13,000** | Wherever there is space: converted cargo volume, Brown outer rings, Downbelow margins | Queuing, waiting, working illegally, sending money that cannot arrive |
| Narn in Downbelow | 2,470 | Brown · outer | Destitute |
| Transient Narn | 1,000 | docks, customs | Crews of the few hulls still running |
| **Total** | **22,500** | | |

**The refugee population is the most important *new* geometry any faction implies in this file.**
It needs: a reception point near the customs halls; overspill accommodation that is visibly not
accommodation (a cargo volume with partitions); an aid queue; and a Narn shrine or mourning
space. None of those are established locations — see §13.

### 6.3 Dress

| Item | Description | Authority | Source |
|---|---|---|---|
| **Formal / ambassadorial** | Layered **tan/ochre suede panels with fringed edges**; vertical dark strap bands with brass studs; a tall stiff **fluted standing collar**; a chainmail-mesh bib at the throat; **iridescent purple-blue trim** on shoulder yokes and front apron edge; a large pebbled reptile-hide apron panel; black leather gloves with gold-edged studded cuffs; quilted studded pauldrons | **2** | `reference/15-races-and-makeup/G'Kar more.jpg` |
| **Physiology** | Hairless; **tan/ochre skin with dark brown leopard spotting** over crown and temples; deep vertical brow furrows; **red irises**; broad flat nose bridge; reptilian neck scaling | **2** | ibid. |
| **Refugee / poor** | Authority 5. Take the same silhouette down: no pauldrons, no trim, no gloves; worn leather, salvaged EA-issue coveralls over Narn undergarments. **The class gradient inside a species is what sells a refugee population** | 5 | — |
| **Script** | Rectilinear and angular; large incised glyphs in **rectangular cartouche cells framed by raised borders**. Distinct from the curvilinear family used for the Zocalo wordmark | **2** | ibid.; note the index's caution that this backdrop may be homeworld rather than station signage |

---

## 7. Centauri Republic

### 7.1 Trajectory across the same span

| Period | Centauri status |
|---|---|
| S2E01–E08 | A decayed empire, humiliated, trading on former glory. Londo is a joke at court |
| **S2E09** | Emperor Turhan visits Babylon 5 and dies aboard; the Centauri strike Quadrant 37; **the war begins** |
| S2E20 | **Victory.** Narn surrenders. The Republic is ascendant for the first time in a century |
| **S3 — THE DATUM** | **Ascendant, occupying, and rotten.** Centauri aboard are citizens of a winning power. Londo is influential and increasingly trapped |

Authority 1 † throughout; Londo is Centauri ambassador to Babylon 5 from 2256 to 2262 and Vir
Cotto is his attaché from early 2258 (authority 4,
[fandom Londo Mollari](https://babylon5.fandom.com/wiki/Londo_Mollari),
[fandom Vir Cotto](https://babylon5.fandom.com/wiki/Vir_Cotto)).

### 7.2 Who and how many

**Counts are authority 5**, apportioning §2.4's 17,500 Centauri. Londo's and Vir's posts are
authority 1 †.

| Group | Count | Where | Doing what |
|---|---|---|---|
| **The mission** | **150**, including **Londo Mollari** (ambassador) and **Vir Cotto** (diplomatic attaché) | Ambassadorial suites, Green; Council Chamber; the Casino; the Zocalo bars | Londo holds the Centauri council seat — publicly expansive, privately compromised. Vir is the mission's conscience and its paperwork. A Centauri legation is a household, not an office: guards, servants, cooks |
| Resident merchants, shippers, financiers | 11,000 | Red inner and outer; Business District; Casino | Trading, lending, and profiting from the occupation |
| Transients: nobles, officers, contractors | 5,000 | hotels, the Casino, diplomatic berths | Passing through on occupation business. **Loud, well-dressed, and unpopular** |
| Centauri in Downbelow | 1,350 | Brown · outer | **A fallen Centauri is a specific tragedy** — a status culture has no vocabulary for it. Build a handful, conspicuous, still wearing the remains of good clothes |
| **Total** | **17,500** | | |

### 7.3 Dress

| Item | Description | Authority | Source |
|---|---|---|---|
| **Court dress** | Present in-repo, in era: a passenger in Centauri court dress in a core shuttle car | **1** | `reference/03-sector-blue/Babylon_5_2-22_35a.jpg` (S2E22) |
| Male silhouette | Heavy brocaded coats, high collars, wide shoulders; **the hair crest fanned upward and outward** — crest breadth signals rank | 1 † | Series-wide |
| Female silhouette | Shaven head, elaborate gowns | 1 † | Series-wide |
| Emblem | **Coral/purple plume of tapered rays with two eye-spots** | 4 | `reference/16-signage-typography-ui/faction symbols.png` |
| Script | Third row of the script sheet, per the uploader's caption — **treat the row assignment as the uploader's claim, not a reading** | 4 | `reference/11-props-and-technology/Vorlon, Narn,and  Centauri script examples.jpg`; the index flags this |

---

## 8. Minbari Federation

### 8.1 The castes, and which are aboard

Three castes: **Religious, Warrior, Worker**. Each Minbari is born into one but may change if
called (authority 4, [fandom Minbari Castes](https://babylon5.fandom.com/wiki/Minbari_Castes)).
Worker caste are the engineers, architects, technicians and labourers; Warrior caste protect the
Federation; Religious caste handle spiritual and intellectual life and teach.

The caste descriptions are **authority 4** (the fandom page cited above); **which castes are
aboard, in what numbers and where, is authority 5**, apportioning §2.4's 12,500 Minbari.

| Caste | Aboard? | Count | Where | Character |
|---|---|---|---|---|
| **Religious** | **Dominant** | ~7,000 | Green: Zen Garden, Sanctuaries, ambassadorial approaches, the Garden terraces; a Minbari quarter | Scholars, observers, pilgrims, temple staff. **Delenn and Lennier are religious caste** |
| **Worker** | Present | ~4,000 | Grey and Blue: fabrication, repair, contracted engineering; the docks | Technicians and contractors. The least remarked-on Minbari and the most numerous after religious |
| **Warrior** | **Rare and conspicuous** | ~600, mostly transient | Docks, diplomatic berths, escort duty | Cold, formal, contemptuous. **A warrior-caste Minbari in a corridor is an event**, not background |
| Mission staff | | ~80 | Green, ambassadorial suites | |
| Transient | | ~800 | | |
| In Downbelow | | **~20** | | **Near zero, and this is characterful.** Minbari do not become lurkers; their own take them in. A Minbari in Downbelow is a story |
| **Total** | | **12,500** | | |

**Delenn** is the ambassador and holds the Minbari council seat; **Lennier** is her attaché
(authority 1 †). Delenn is, at the datum, a Minbari–human hybrid following her transformation at
the start of S2 — a build-relevant fact, since her head bone crest and hair are unlike any other
Minbari aboard.

### 8.2 Dress

| Item | Description | Authority | Source |
|---|---|---|---|
| **Ceremonial / religious** | **Cream and pale-gold layered robes**; and a second group in **long black robes with a metal-buckled belt** — roughly ten to twelve of the first and three of the second in one chamber | **1** | `reference/05-sector-green/rotunda.webp` |
| Everyday religious caste | Robed; present in the Garden terraces | **1** | `reference/03-sector-blue/Babylon_5_2-22_29a.jpg` — "Robed Minbari present" |
| **Bone crest** | The head crest is the species' silhouette and must read at distance | 1 † | Series-wide |
| **Denn'bok (fighting pike)** | A plain polished-metal cylindrical staff of uniform diameter, ~5–6 ft, with a knurled grip band about a third down and a narrow dark collar band below it — the telescoping joint. No taper, no head, no ornament | **2** | `reference/14-characters-and-uniforms/Marcus Cole with Minbari denn'bok.jpg` |
| Emblem | Blue triangle with a hooked crescent | 4 | `reference/16-signage-typography-ui/faction symbols.png` |
| Interior style | Minbari-styled rooms use **violet and warm light mixed**, tall arched alcoves in deep dark reveals, ribbed mauve upholstery on chrome — **not** the standard EA corridor kit | **1** | `reference/14-characters-and-uniforms/Marcus Cole in uniform.jpeg`, room description |

---

## 9. League of Non-Aligned Worlds

### 9.1 What it is

An alliance of minor powers formed around the Abbai, none of them individually able to face the
Centauri, Narn or Minbari. **All member worlds assign ambassadors to Babylon 5, but only ten sit
in Assembly at any one time** (authority 4,
[fandom League of Non-Aligned Worlds](https://babylon5.fandom.com/wiki/League_of_Non-Aligned_Worlds)).
Emblem: an orange triangle in a ring of teal stars (authority 4,
`reference/16-signage-typography-ui/faction symbols.png`).

That "ten of many" rule is directly buildable: **the Council Chamber has a fixed number of League
seats and a rotation**, so a delegation in the anteroom that is not sitting today is a normal
sight, and there is a politics of whose turn it is.

### 9.2 Species aboard, with relative numbers

Counts are §2.4's. Every species-identity row is authority 4 unless it cites a reference file.

| Species | Count | Character | Where they cluster | Source |
|---|---|---|---|---|
| **Drazi** | 12,500 | Physically robust, blunt, factional. **The League species most often doing the physical work** | Docks, cargo, Grey industrial, Dark Star, Downbelow | 4 |
| **Brakiri** | 7,500 | Traders and financiers; **night dwellers** | Business District, Zocalo, Casino — and they populate the station-*night* | 4 |
| **pak'ma'ra** | 6,250 | **Carrion eaters**, marginal, poor. **Four thick tapering tendrils** hanging from below eye level past the chin, outer two longest, fleshy and ringed with fine transverse creases — **not** a two-lobed trunk | Waste management, cargo, Downbelow, their own eating areas | **3** — `reference/15-races-and-makeup/Pak'ma'ra even more.jpg` (a licensed trading card, read at 5×); the two-lobed-trunk error is flagged in `reference/22-QUARANTINE-ai-generated/README.md` |
| **Vree** | 5,000 | Traders; saucer craft | Docks, Zocalo | 4 |
| **Abbai** | 3,750 | League founders; mediators; amphibian | Council anteroom, Hydroponics, humid quarters in the Alien Sector | 4 |
| **Gaim** | 2,500 | **Methane breathers in encounter suits**; hive-caste insectoids | **Alien Sector** — non-oxygen atmosphere. Also cargo and labour, suited | 4 — [fandom Gaim](https://babylon5.fandom.com/wiki/Gaim) |
| **Hyach** | 1,750 | Long-lived, formal | Council, Business District | 4 |
| **Llort** | 1,250 | Reputation as scavengers and thieves | Downbelow, docks, markets | 4 |
| **Grome** | 750 | | Hydroponics, labour | 4 |
| Other / unclassified | 1,250 | Rare species and one-off visitors | everywhere, thinly | 5 |
| **Markab** | **0** | **Extinct at the datum** (E4) | A **sealed quarter** in the Alien Sector | 1 † |

**A naming note worth carrying into `station/npc/names.py`.** The only authority-3 spelling the
reference set holds is "**Pak'ma'ra**", capitalised, from the licensed trading card
(`reference/15-races-and-makeup/Pak'ma'ra even more.jpg`). `schedule.py`'s key is `pakmara` and
the show's own usage is generally lowercase `pak'ma'ra`. Recorded, not ruled on: the *code key*
should stay ASCII, but anything the player reads should use the authority-3 form.

### 9.3 The Alien Sector — the League's physical home

| Fact | Detail | Authority | Source |
|---|---|---|---|
| Named on an authority-3 plan | "**Alien Sector**" appears in the **Green rosette's outer ring**, alongside Council Chamber, Fresh Air Restaurant, Earthforce Office, Zen Garden, Hydroponics | **3** | `reference/02-station-cutaways-and-plans/other map.png` |
| Named on a second authority-3 plan | "**multi-environ 'alien' sector**" is a callout on the Security Manual sectional schematic | **3** | ibid. folder |
| Accommodates | **14 different species** with different atmospheric needs | 4 | [fandom Green Sector](https://babylon5.fandom.com/wiki/Green_Sector) |
| Access | Through a series of **airlocks**, with **breather-mask dispensers** for most races | 4 | ibid. |
| The joke worth building | Its residents call the oxygen-rich rest of the station "the alien sector" | 4 | ibid. |
| Six atmospheres | The station offers **six standing atmospheres**, numbered; others by prior arrangement | **1** | `00-MASTER.md` §1.4 |
| In-repo interior | `reference/05-sector-green/corridor in alien sector.webp` is authority-1 and already mined for the interior kit | **1** | index |

**14 species and 6 atmospheres are not in conflict** — most oxygen breathers share atmosphere 02
and its variants, and the six standing mixes cover the common cases with bespoke mixes for the
rest. Build the sector as **six atmosphere zones behind airlocks**, with signage naming the
number, and put the Gaim behind the methane one.

---

## 10. The Rangers (Anla'shok)

### 10.1 Status at the datum: present, and semi-covert

| Fact | Detail | Authority | Source |
|---|---|---|---|
| Leadership | Jeffrey Sinclair leads them as **Ranger One (Anla'shok Na)** and **Entil'Zha**, from Minbar — **not from Babylon 5** | 4 | [worldsofjms Sinclair profile](https://worldsofjms.com/b5/characters/sinclair.htm) |
| Humans admitted | Sinclair opened membership to humans; Marcus Cole is among the first generation | 4 | ibid.; [fandom Marcus Cole](https://babylon5.fandom.com/wiki/Marcus_Cole) |
| Station division | Sheridan gains **co-control of the Babylon 5 division of Rangers with Delenn by October 2259** | 4 | [Multiversal Omnipedia](http://moa.omnimulti.com/Rangers_(Babylon_5)) |
| Visibility in S2 | Rangers exist and pass through; **they are not a visible aboard-station presence** | 5, from the absence of in-era reference | — |
| **Visibility in S3 — the datum** | **Marcus Cole is aboard from S3E01**, in Ranger dress, and Rangers use the station as a base and a message hub | **1** | `reference/14-characters-and-uniforms/Marcus Cole in uniform.jpeg` — the index states "In era for Season 3. Marcus is introduced in S3, so the Ranger costume is inside the lock — but only for S3, not S2" |

**How to build the visibility.** They are not secret from the audience and not advertised to the
station. Model **20–60 Rangers aboard at any time**, human and Minbari, mostly transient, with a
handful resident (authority 5). They do not wear a uniform in public unless they intend to be
recognised — **the tell is the brooch**, and a player who learns to spot it starts seeing them
everywhere. That is a genuinely good discovery mechanic and it comes straight from the costume.

**The date matters for the era gate:** if a future session moves the datum back into S2, the
Ranger costume must come off every NPC. The index says so explicitly.

### 10.2 Dress

| Item | Description | Authority | Source |
|---|---|---|---|
| **Tabard** | Brown/tan **sleeveless tabard-tunic** over a black long-sleeved undershirt with quilted leather sleeves; black high roll-neck | **1** | `reference/14-characters-and-uniforms/Marcus Cole in uniform.jpeg` |
| **Baldric** | Broad dark diagonal baldric across the chest with a braided/embroidered edge | **1** | ibid. |
| **Belt** | Wide black waist belt, large ornate gold-bronze buckle in a stylised bird/leaf form with scrollwork; a long thin dark cord hanging from it | **1** | ibid. |
| **The badge — the tell** | An **oval pale blue-green cabochon** (aquamarine or jade) in an **ornate gold bezel**, mounted high on the left chest on an embossed dark strap | **1** | ibid. at 3×; confirmed at authority 2 in `Marcus Cole with Minbari denn'bok.jpg` |
| **Cloak** | Long, **black outer with a bright yellow-gold lining** | **2** | `Marcus Cole with Minbari denn'bok.jpg` |
| **Weapon** | The Minbari **denn'bok** — see §8.2. Carried collapsed; a Ranger with a plain metal cylinder at the belt is armed | **2** | ibid. |
| Underlayers | Grey-brown windowpane-check fabric panels, leather bib, dark braided scarf, black fingerless gloves | **2** | ibid. |

---

## 11. Non-state factions — the parts that make it a city

### 11.1 Commerce, guilds and labour

| Body | Detail | Authority | Source |
|---|---|---|---|
| **Dockers' Guild** | The dock workers are **organised**, and have struck. In S1E12 *By Any Means Necessary* the union (led by Neeoma Connally) runs a "blue flu" action after equipment failure kills a worker; the Senate invokes the Rush Act; the resolution is money reallocated **from the station's military appropriation** to working conditions | 1 † | Episode; [Wikipedia](https://en.wikipedia.org/wiki/By_Any_Means_Necessary_(Babylon_5)) and [fandom Docker's Guild](https://babylon5.fandom.com/wiki/Docker's_Guild) (4) |
| **Dock Workers' Quarters** | A named facility on an authority-3 plan | **3** | Blue rosette, `other map.png` |
| Guild strength aboard | ~1,200 EA dock/cargo/traffic staff plus contracted alien labour; **the Drazi share of dock labour is the highest of any species** | 5 | derived from §2.2 |
| **Merchants of the Zocalo** | Stalls, bars, cafés, an upper gallery. Vendors are of every species; the neon reads **"Zocalo"** in stylised Latin letterforms, and genuine alien-script neon appears alongside it | **1** | `reference/04-sector-red/more zocalo.png`, `reference/11-props-and-technology/Zocalo neon signage in background.jpg` |
| Currency | **Credits**; exchange through the **Business Center** | **1** | customs board |
| Named venues with in-repo authority-1 signage | **Zocalo · Earhart's · Dark Star · the Casino · Fresh Air Restaurant** — and all five are also named on authority-3 rosettes | 1 + 3 | index; `other map.png` |

### 11.2 Downbelow and the underclass

| Fact | Detail | Authority | Source |
|---|---|---|---|
| Named on an authority-3 plan | "**DOWNBELOW**" marked with a double-headed arrow spanning an **outer annular band** of the **Brown** rosette, with "Happy Daze" and "Waste Management Control" alongside | **3** | `reference/02-station-cutaways-and-plans/other map.png` |
| Named on a second authority-3 plan | "**WASTE MANAGEMENT SYSTEMS ('DOWN-BELOW')**" callout | **3** | Security Manual sectional schematic |
| What it physically is | Undeveloped and unfinished areas, mostly outer rings near the hull, around **waste recycling, air compressors and water reclamation** | 4 | [fandom Downbelow](https://babylon5.fandom.com/wiki/Downbelow) |
| Who lives there | People who came for a better life, ran out of money, and squat in unfinished corridors, scrounging construction refuse for anything edible, wearable or sellable | 4 | [fandom Lurker](https://babylon5.fandom.com/wiki/Lurker) |
| Population | **~20,000 (8%)**, of which ~13,500 human | 5 | bracketed by an authority-4 forum estimate of ~13,000 lurkers and a ~50,000 upper reading |
| Only in-repo visual | `reference/01-station-exterior/sleeping-in-light-05.jpg` — a wide Downbelow-class corridor. **S5 and derelict: set architecture in era, dressing not** | 1, flagged | index |

**Gravity makes Downbelow worse, and the project already proved it.** `STATE.md` session 2v:
the habitable stack runs *outward* from the drum floor, so **Downbelow is heavier than the
Garden** — 1.117 g against 1.000 g at the drum, and Grey's outermost deck reaches 1.445 g. The
poorest people on the station live at the highest gravity, in the noisiest place, next to the
waste plant. **None of that was authored; it fell out of the geometry**, and it is the single
strongest piece of unearned characterisation the project has.

Behaviour to build: no schedule (the `lurker` role in `schedule.py` already has zero work hours);
avoidance of identicard readers; clustering near heat and light sources; dispersal during
security sweeps; a black market in the margins between Downbelow and the commercial rings.

### 11.3 Religion

| Fact | Detail | Authority | Source |
|---|---|---|---|
| **Sanctuaries (4)** | Four, counted on an authority-3 production sheet, never located | **3** | `00-MASTER.md` §1.3, Contract 5 |
| **Brother Theo's order** | A group of human monks takes up **permanent residence** in S3E02, to learn what other races call the creator; they chose Babylon 5 because its traffic volume compresses the work. They are technically skilled and are engaged to analyse station records | 1 † | S3E02 *Convictions*; [Reactor](https://reactormag.com/babylon-5-rewatch-convictions/) (4) |
| Size of the order | **15–25** | 5 | Depicted as a working community, not a congregation |
| Minbari religious observance | Robed ceremonial gatherings of ten to fifteen in a domed chamber | **1** | `reference/05-sector-green/rotunda.webp` |
| Narn religious practice | G'Quan; the **G'Quan Eth** plant is required for ritual and **contains substances controlled under Earth law** — a religion/jurisdiction collision built into a prop | 1 † | S1E12 |

Four Sanctuaries and a resident monastic order give `Activity.WORSHIP` in `schedule.py` an actual
destination, which it currently lacks.

### 11.4 Crime

| Element | Detail | Authority | Source |
|---|---|---|---|
| **Ordinary crime** | Theft, assault, fraud, smuggling, prostitution, unlicensed trade. Adjudicated by the Ombuds under EA law with constant jurisdiction disputes | 4 + 1 † | [fandom Ombudsmen](https://babylon5.fandom.com/wiki/Ombudsmen) |
| **Identicard and visa fraud** | Follows directly from the authority-1 record schema having a `VISAS` field. Forged cards, expired status, stolen identities | 5, from an authority-1 prop | `identicard readout.webp` |
| **Contraband and controlled substances** | Established in era: the **G'Quan Eth** is seized as a controlled substance | 1 † | S1E12 |
| **Dust** | An illegal telepathy-inducing narcotic trafficked aboard in S3 | 1 † | S3E06 *Dust to Dust* |
| **Weapons smuggling** | G'Kar runs weapons to the Narn resistance **through Babylon 5**, with Garibaldi's quiet help | 4 | [fandom Narn Resistance](https://babylon5.fandom.com/wiki/Narn_Resistance) |
| **Organised crime** | **N'Grath**, a non-oxygen-breathing insectoid crime boss operating out of Downbelow, rarely leaving his quarters in the Alien Sector | 4 | [fandom N'Grath](https://babylon5.fandom.com/wiki/N%27Grath) |
| **Raiders** | Pirate groups preying on transports in the sector; a docking-bay and traffic-control concern more than a corridor one | 1 † | S1–S2 |
| Enforcement reality | ~150 officers on duty across 8 km. **Crime is not policed, it is contained at chokepoints** | 5 | §2.2 |

**Era caution on N'Grath:** he is an S1–S2 fixture and stops appearing after S2. Whether he is
still in business at an S3 datum is **not established** — build the *role* (an insectoid fixer in
the Alien Sector with reach into Downbelow) and treat the name as optional. Logged in §15.

### 11.5 News, propaganda and comms

| System | Detail | Authority | Source |
|---|---|---|---|
| **ISN (Interstellar Network News)** | The news network. Initially genuine journalism; **after Clark's consolidation it becomes a propaganda organ** defending the government's xenophobic policies and attacking dissidents | 4 | [fandom ISN](https://babylon5.fandom.com/wiki/Interstellar_Network_News) |
| ISN aboard | Crews embed rather than reside — an ISN reporter spent **36 hours** aboard for a broadcast built entirely from station footage | 1 † | S2E15 *And Now For a Word* |
| **In-repo authority-1 anchor** | The arrival concourse carries a **wall monitor showing a talking head** — a news screen, on screen, in the customs area | **1** | `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg` |
| **BabCom** | The station's internal communications network — intrastation, ship-to-station and long-range tachyon. **Public terminals in passenger lounges and the Zocalo**; better quarters have BabCom and datanet terminals | 4 | [fandom Babcom](https://babylon5.fandom.com/wiki/Babcom) |
| **StellarCom** | Long-range service reached through BabCom; the tachyon spectrum is divided into assigned channels, with priority channels reserved — **Gold Channel One for the Office of the President** | 4 | [fandom StellarCom](https://babylon5.fandom.com/wiki/StellarCom) |
| **Tachyon transmitter** | A physical exterior system already in the model | 3 | `00-MASTER.md` §2 item 18 |
| **The link** | Personal wrist communicator; described precisely in §3.3 | **2** | in-repo |
| **Station signage as voice** | The customs boards are the station talking to you: *"FOLLOW ALL CUSTOMS PROCEDURES"*, *"TIME ON B-5 IS EARTH MEAN TIME (EMT)"*, the atmosphere caution | **1** | `reference/01-station-exterior/welcome to babylon 5.webp` |

**Build note on propaganda.** At the datum the propaganda layer is **three surfaces**: ISN on
public screens, Ministry of Peace notices, and Nightwatch recruitment. They should read as
*official and reasonable* — clean typography in the same register as the customs boards — because
that is what makes them sinister. Do not make them look like villain posters.

---

## 12. Friction — what happens when two of them pass each other

The brief is right that this matters most. Each row is a **behaviour to implement**, with the
severity that governs how often it fires. Authority for the *fact* of the antagonism is given;
the **behaviours are authority 5** and are the design.

| Pair | Severity | What a player sees | Authority for the antagonism |
|---|---|---|---|
| **Narn ↔ Centauri** | **Highest** | The Narn stops, turns, and does not yield the corridor. The Centauri crosses to the far side or keeps walking with an escort. Neither speaks. Groups reroute around each other entirely; a Narn will not enter a Centauri-run venue and is not served if he does. Security posts extra officers where the two territories abut. **Violence is rare and enormous when it happens** — the surrender terms (500 executions for one Centauri death) are why restraint is the ambient state | 1 †, S2E20 |
| **Human ↔ alien, under Nightwatch** | High | A human talking with aliens lowers his voice when an armband passes. Merchants who trade heavily with aliens get visited. A shopkeeper is taken away and the neighbouring stalls look elsewhere | 4 + 1 †, S2E22 |
| **Security ↔ security** | High | **One officer in a two-officer patrol wears the armband and the other does not.** They do not talk much | 2 (the still) + 1 † |
| **Mundane ↔ telepath** | High | Conversation stops when someone with the Ψ badge enters. Nobody sits at the adjacent table. Business people seek them out and then dislike them | 1 † |
| **Psi Corps ↔ rogue telepaths** | High, rare | A Psi Cop visit clears corridors. Unregistered telepaths in Downbelow disappear deeper | 1 †, S2E08 |
| **Warrior-caste Minbari ↔ humans** | Medium-high | Cold formality on the Minbari side; older humans stare. The Earth–Minbari War is eleven years back and everyone in the corridor remembers it | 1 † |
| **Minbari religious ↔ warrior caste** | Medium | Two Minbari groups that do not mix, sharing a Sanctuary schedule by rota | 4 |
| **pak'ma'ra ↔ everyone** | Medium | Their eating areas are their own and other species do not sit there. Tables clear around them. **They are the only species with a segregated food economy** | 1 † (the friction is depicted); the rhythm inference is already logged in INV-005 |
| **Drazi ↔ Drazi** | Episodic | A Drazi factional split — one colour against another — turning into open brawling in public areas on a multi-year cycle. **Recurs on a fixed cycle rather than continuously; a builder may switch it on or off for the datum** | 1 †, S2E03 *The Geometry of Shadows*. **Cycle length and colours need confirmation — see §15** |
| **Lurkers ↔ commercial areas** | Medium | Moved on from the Zocalo. Conspicuous by clothing before anything else. Avoid identicard readers | 4 |
| **Narn ↔ EarthGov** | Medium, cold | Earth signed a non-aggression pact with the Centauri; the Narn regard EA neutrality as complicity. G'Kar's warmth toward Sheridan is **personal and does not extend to the uniform** | 1 † |
| **League ↔ the great powers** | Low, constant | League delegations caucus together in the Council anteroom, and are visibly not being consulted. Their ships are the ones raiders take | 1 † |
| **Vorlon ↔ everyone** | Ceremonial | Kosh is almost never seen. When he moves, the corridor clears without being told to | 1 † |
| **Dockers ↔ management** | Latent | Grievance boards, notices, the memory of the strike. Flashes up as an event rather than ambient | 1 †, S1E12 |

**A rule for the whole system.** Friction should be expressed **95% as avoidance and 5% as
contact**. A station where hostile species brawl on sight is a cheaper and less believable place
than one where two crowds move through the same concourse and never once intersect. Build the
avoidance first; the fights are set dressing on top of it.

---

## 13. Unplaced — known things the show never locates

Every one of these is a real thing that belongs aboard and that **no source places**. They are
listed so a future session proposes a location deliberately rather than inventing one silently.
A proposal is offered where the reasoning is strong; each would be an `INVENTIONS.md` entry.

| Thing | Why it is unplaced | Proposed placement (authority 5) |
|---|---|---|
| **Psi Corps liaison office** | Never shown as a located facility | Business District, Red inner — it is a commercial-services function and sits with brokers and exchange |
| **Nightwatch muster room / reporting terminal** | Never located | A repurposed room adjacent to Security Central, Red inner; public reporting terminals in the Zocalo and both customs halls |
| **Narn refugee reception and accommodation** | Post-dates every plan in the reference set | Reception adjacent to the customs halls, Blue outer; accommodation in converted cargo volume, Brown outer, adjoining Downbelow |
| **Narn shrine / mourning space** | Never located | Within the Narn quarter; or one of the four Sanctuaries reassigned |
| **The four Sanctuaries** | Counted at authority 3, never located on any plan | One per major pressurised sector (Blue, Red, Green, Brown), each multi-faith with a rota |
| **Brother Theo's monastery** | Never located | Green or Red middle ring; a converted block of quarters, not a purpose-built abbey |
| **Rangers' safe house / message drop** | Deliberately never shown | Brown, at the Downbelow margin; deliberately unmarked |
| **ISN bureau** | Crews embed, no permanent bureau established | A hired suite in the Business District, occupied only when a crew is aboard |
| **The brig / holding cells** | Security Central is placed at authority 3; the cells are not | Directly attached to Security Central, Red inner |
| **Kosh's quarters** | Implied to be a sealed non-standard environment; never precisely located | Alien Sector, Green outer, with its own atmosphere plant. The in-repo frosted-grid-wall environment is the visual reference |
| **The sealed Markab quarter** | Consequence of the datum; no source | Alien Sector, adjacent to Kosh's environment; sealed, powered, unlit |
| **Ambassadorial suites** | Named on the sectional schematic band and implied in Green; **no ring and no deck** | Blocked by C-003/C-004 — bind to the facility name, not a number |
| **Customs halls** | "customs (×2, north and south)" gives the *lateral* placement at authority 3 but no ring | North and South per the `00-MASTER.md` §2 convention; ring class outer, Blue |
| **Dockers' Guild hall** | Dock Workers' *Quarters* is placed at authority 3; the guild hall is not | Adjacent to the quarters, Blue |
| **The morgue / cryo storage** | Never located | Attached to Medlab One, Blue inner |
| **Zocalo's level** | Placed in Red's outermost ring at authority 3; **the ring index is blocked by C-004** | Do not number it |

---

## 14. Contradictions found

Recorded here because contradictions are findings. **None of these were fixed** — `canon/` and
`reference/` belong to other agents.

### 14.1 The era lock is internally inconsistent

`canon/00-MASTER.md` line 5 requires simultaneously *"all League ambassadors resident"*
(true only before S2E18, when the Markab die) and, implicitly, the Nightwatch political layer the
brief calls era-critical (true only after S2E22). **These cannot both hold.** Full argument in
§1.2. Recommended fix: replace the clause with an explicit datum. This file uses **S3
pre-martial-law (between S3E02 and S3E09)** and everything in it is written to that.

### 14.2 The repository contradicts itself about the Psi Corps costume

`reference/22-QUARANTINE-ai-generated/README.md` quarantines an AI turnaround **because** it
puts Talia Winters in mustard/ochre, and names `talia-winters in gorgeous office.webp` as the
genuine screencap that disproves it. The session-2s entry in `reference/00-INDEX.md` **for that
same file** describes "the Psi Corps **gold/ochre** suit ... warm mustard-tan". A third entry
describes a **dark olive-green/black** jacket in a different frame.

The quarantine *decision* is unaffected — AI turnarounds stay out regardless — but its stated
*reason* is contradicted by the repository's own later, magnified read. Proposed resolution in
§4.2: there is no single Psi Corps colour; build from the invariants (silver Ψ badge, black
gloves, squared shoulders, black inset panels) and vary the body colour per NPC.

### 14.3 An authority-4 source places the Alien Sector where two authority-3 sources do not

[fandom Green Sector](https://babylon5.fandom.com/wiki/Green_Sector) (authority 4) says the
Alien Sector is "located **between the docking bays and Red Sector**". Docking is Blue. Both
authority-3 orderings in `CONFLICTS.md` C-003 put **Red between Green and Blue**, so "between
Blue and Red" is not where Green is under either. Yet the same authority-4 source calls it part
of Green, and the **Green rosette itself names "Alien Sector" in its outer ring at authority 3**.

**Authority 3 wins and the Alien Sector goes in Green.** Recorded because it is a third
independent data point touching the sector ordering, and C-003 is short of those. It does not
resolve C-003 and must not be used as if it did.

### 14.4 "Crew 6,500" is undefined

`other map 2.jpg` (authority 4) gives "crew 6,500" without saying whether that is line EarthForce
or all EA-employed staff. §2.2 takes the broad reading and says so. A narrow reading moves ~2,000
people from the military block to the civilian block and changes nothing else.

### 14.5 A note on `station/npc/schedule.py`

Not a contradiction, but the mix there (six species, `narn` 0.10, `centauri` 0.09, `minbari`
0.07, `pakmara` 0.05) is superseded by §2.4. INV-005 already calls it the weakest part of the
entry. Any replacement **must be asserted to sum to 1.0 in a test** — INV-005 records that a sum
of 0.94 silently dropped 120 residents per 2,000.

---

## 15. Open questions this file could not settle

Listed with what would close each.

| Question | What would settle it |
|---|---|
| Species proportions | Nothing will — no source states any. §2.4 is authority 5 and should be labelled so forever |
| Nightwatch strength aboard | Dialogue in S3E09 giving a number; or a visible muster |
| Security force size | Dialogue; or a duty roster prop |
| Is "crew 6,500" military or total? | A second source giving either figure separately |
| The Narn Advisory Council seat after S2E20 | Whether it was left vacant, refilled by a Centauri-approved Narn, or abolished. Council-chamber footage from S3 would show an empty chair or a filled one |
| Was the Markab quarter sealed or reallocated? | Any S3 dialogue or footage referring to Markab property |
| Is N'Grath still operating in S3? | His last appearance; a successor named |
| The Drazi factional cycle | Colours and cycle length from S2E03; this file deliberately does not state them |
| Ranger numbers aboard | Never stated; 20–60 is authority 5 |
| Refugee intake rate | Never stated; would let the Narn population be a *curve* rather than a number |
| Every authority-4 web row in this file | `WebFetch` was blocked for every host tried, so nothing was read directly — only search-engine summaries. Re-verify when fetching works |

---

## 16. What to build first

Ranked by how much other work each unblocks.

1. **Fix the era datum in `canon/`.** One line. Until it is fixed, every faction decision is
   provisional and this contradiction will be rediscovered.
2. **Replace `STATION_MIX`** with §2.4 — 14 species plus a hard-coded Vorlon singleton, with a
   test asserting the shares sum to 1.0 and the counts to 250,000.
3. **The faction → named-facility binding table** (§2.5, §13). It is designed to survive C-003
   and C-004 closing, so it can be written now.
4. **The Nightwatch armband as a per-NPC boolean on the security uniform.** One decal, one strap,
   and it produces the highest-value visible politics on the station for almost no geometry.
5. **The arrivals system** (§2.3): 52 ship movements a day, ~6,300 arrivals, two customs halls,
   peak 20–40 people a minute. This is what makes the station read as a working port.
6. **The friction behaviour layer** (§12), avoidance first. Narn/Centauri is the headline and
   should be built before any other pair.
7. **Costume archetypes.** Nine are specified well enough here to build now: EarthForce command
   S2–3, EarthForce security service dress, EarthForce security duty rig, Nightwatch armband
   overlay, Psi Corps, Narn formal, Narn refugee, Minbari religious robes, Ranger. Five badge
   decals: EarthForce wings, security crosshair-diamond, Psi Corps Ψ, Ranger cabochon, station
   shield.
8. **Downbelow as a population, not a place** — 20,000 people with no schedule, at 1.117–1.445 g,
   next to the waste plant.
9. **The sealed Markab quarter.** Cheap, memorable, and the only monument on the station to a
   species that no longer exists.
