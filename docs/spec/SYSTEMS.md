# SYSTEMS AND SURFACE — normative annex to THE-STATION.md §7–§8

Format law: docs/THE-STATION.md §1 (anti-rig) and §2 (tiers). Every SYS item states its
**state variables, its tick, its couplings, its player surface, and an acceptance check that
names content**. Sources: the four-domain research fan-out (systems inventory), cited inline
as file:line where load-bearing. Inventions marked (auth 5).

---

## SYS-01 — THE ERA CLOCK AND THE CALENDAR
**State:** `station_day` (integer, persists), `hour` (EMT), era position seeded at
ERA_DATUM=(3,5) advancing one episode-equivalent per N station-days (auth 5: N=7, so a
long player month crosses one era beat).
**Tick:** daily rollover; era events fire from `costume.ERA_EVENTS` (8 keyed events,
markab_extinct → secession, npc/costume.py:147-168) as the datum passes them.
**Couples to:** ISN bulletins (5 era-keyed), MiniPax notices, Nightwatch armbands
(NIGHTWATCH_SHARE=175/500), Narn refugee status, dialogue `_topic_era/_topic_news`.
**Player surface:** date on HUD and BabCom; the week visibly moves (SYS-08).
**Check:** boot day 1, run to day 8 headless: the era datum has advanced, ≥1 broadcast
element changed *because of it*, and a save made on day 3 reloads as day 3.

## SYS-02 — TRAFFIC AND DOCKING
**State:** the live berth map (24 bays × A/B levels, standoff ring, moorings), per-ship
manifest rows (55 arrivals/day: freighter 20, transport 14, shuttle 12, standoff 4,
diplomatic 2, liner 0.5, EF 2.3, alien warship 0.2 — traffic.py:132-142), DAY_BANDS
(peak-to-trough 3.12:1), bay-elevator duty cycle (2 units, ~5 min cycle, 62% peak).
**Tick:** hourly arrivals draw; 8-phase docking state machine per ship (gate transit 20 s →
beacon → 65 km inbound → clearance → roll match → axial entry → elevator → berth).
**Couples to:** customs load (`hall_rate`, liner peak 8.5 souls/min), cargo → SYS-04
deliveries, PA port calls, arrivals boards (live already — signage.py:549-603), SYS-14
incident classes (hold stack, dual-clearance accident, unannounced warship).
**Player surface:** watchable from viewpoints and the bays; the boards and PA always agree
with the berth map because they read it.
**Resolves:** C-012 (souls/day ×3.6 conflict) — one number chosen, written into
CONFLICTS.md, all three consumers re-derived from it.
**Check:** across one headless day: every announced arrival exists in the berth map; a named
liner docks at its band; the elevator cycle bounds throughput; boards/PA/berths never
disagree (the three-reader agreement is the check).

## SYS-03 — CUSTOMS
**State:** per-hall queue depth, 10-station pipeline (arrival.py:440-545), entry classes
(EA_CITIZEN…NO_STATUS, "-- EXPIRED"), outcome routing.
**Tick:** processes SYS-02's disembarkations; **1%/day leak of refused/broke arrivals to
Downbelow** (LEAK_RATE, player.py) — the underclass is *fed by the port*, not spawned.
**Builds:** `secondary_inspection` and `customs_holding` — both currently
`built=False` in arrival.UNBUILT; both get PLC rows and real interiors.
**Player surface:** the player IS processed on arrival (P2); as a customs-officer role,
works the desk: reads cards, spots forgeries (SYS-06 feeds them through), flags atmospheres,
finds contraband at the real P=0.01/0.04 rates.
**Check:** an arriving NPC with an expired visa is refused, cannot afford 250 cr passage,
and appears in Downbelow with their name intact within 2 station-days.

## SYS-04 — THE ECONOMY
**State:** per-vendor stock lists and prices (anchored to the ONE auth-1 price: command
quarters 30 cr/wk; ladder per LAW-CRIME:739-748 — cart meal 1-2 cr, dock day-labour
8-15 cr, dosshouse bunk 1 cr/night, passage home 250-800 cr); per-resident credits
(CREDIT_MIN/MAX exist, player.py:140-174); wages per role per shift; rents (the station's
sourced revenue model).
**Tick:** wages at shift end; rents weekly; vendor stock **depletes by purchase and
replenishes by delivery** — and a delivery is a real container off a real ship through the
real cargo bays (the full T4 chain: ship → cargo bay → porter route → stallhold restock).
**Couples to:** SYS-02 (a docking strike is a food story — LIFE-SUPPORT:219-253), SYS-05
(debt enforcement), SYS-06 (untaxed goods undercut Zocalo prices), roles (pay).
**Player surface:** BUY/SELL everywhere commerce is declared; the player pays rent or
loses their quarters assignment; prices visibly differ Zocalo vs under-counter.
**Check:** buy the last unit of a named good at a named stall; the stall shows empty; the
restock arrives on a manifest ship within its schedule; save/reload preserves both states.
(This is also P2's save-delta gate.)

## SYS-05 — LAW AND CRIME
**State:** 500 officers / ~150 on duty / 3 watches (implemented, security.py); 56 posted at
the POSTS table; roving pairs derived; per-district patrol frequencies (Zocalo continuous …
Downbelow ZERO); the offence table (LAW-CRIME:816-838, petty theft dozens/day → murder
single-figures/yr); the brig custody ledger (24-40 cells, ≥3 atmospheres); ombudsman
docket (2 named ombudsmen, sessions in `law_courts`).
**Tick:** crime events generated per district per hour at the sourced rates (90% of crime
in Downbelow among 8% of population); detection only where security actually is (the
response-time model: seconds in the Zocalo, 12-20 min far outer ring); escalation ladder
7 rungs, identicard check the commonest interaction.
**Couples to:** SYS-14 (crimes are incident instances), SYS-03 (identicards), SYS-06,
SYS-08 (a sweep is PA-announced and the camp empties — LAW-CRIME:900-948).
**Player surface:** the player can be checked, moved on, detained, tried, briged, fined;
the 95/5 avoidance/contact rule and the **marked-out mechanic** (clothing/gait/light, not
a hostility radius) govern Downbelow; as deputy role, the player works a beat.
**Check:** a scripted theft in the Zocalo is detected in seconds and the thief walked to
the brig; the same theft template in Downbelow at 03:00 completes undetected; the brig
ledger shows the first, not the second; the player committing the Zocalo version ends in
the brig with a fine and a record on their card.

## SYS-06 — THE BLACK MARKET (a route, not a room — LAW-CRIME:858-879)
**State:** the route's five stations (bribed docker → cargo lift → unfinished-deck cache →
fixer → Zocalo under-counter); N'Grath as the era's fixer (sealed non-oxygen room,
`ngrath` place exists); forged identicard supply; contraband inventory seeded by what
customs misses.
**Tick:** goods move down the route on porter schedules; prices float under Zocalo's.
**Player surface:** findable by following a porter or earning lurker trust; buyable
(forged card = a new identity with its own risks); reportable (SYS-05 consequence).
**Check:** an item confiscable at customs, bought under-counter, traces back through the
route's five stations when followed — each station a real place with a real NPC.

## SYS-07 — THE PHYSICAL PLANT, LIVE
**State:** power (≈1.9 GW demand ladder, LIFE-SUPPORT:65-114), water (13,250 m³/day,
30-day reserve, >98% closure), atmosphere (O₂ 210 t/d, six atmospheres held), food
(three-sourced: hydroponics + drum agriculture + imports), waste (37.5 t/d, three rosettes).
**Tick:** daily balances; **scheduled failure events** from the documented set (brownout,
elevator outage, quarantine, waste backup, strike/"blue flu") at low rates — canon says
brownouts are "a plot-grade event the simulation supports but does not schedule"; now it
schedules them.
**Couples to:** everything — a brownout dims real fixtures in real rooms (the lighting rig
is per-fixture already); a dock strike thins SYS-04 deliveries within days; Downbelow IS
the plant zone, so plant work and lurker life share floors.
**Player surface:** maintenance-tech role works the failure queue; everyone else *feels*
outages (lights, PA advisories, queues).
**Check:** force a brownout in one sector: its fixtures dim in-engine, the PA advises, a
work order appears, a maintenance NPC (or the player in role) walks to the site, closes
it, and the lights return — end to end without scripting the walk.

## SYS-08 — THE INFORMATION LAYER
**State:** ISN bulletin queue (5 era-keyed + incident-derived), MiniPax notices, PA
schedule (port calls, watch calls, civic calls — broadcast.py implements all three),
arrivals boards (live), BabCom per-resident directory + messages, **the rumour pool**:
dialogue's news topic drawing on the *incident log*, so what people say happened is what
happened.
**Tick:** "the week has news" — two consecutive days differ in broadcast and rumour content
derived from SYS-02/05/07/14 events plus the era clock, never from a script.
**Player surface:** BabCom terminals are usable (directory, messages, news); signage is
live; overheard dialogue references real events the player may have been present at.
**Check:** cause an incident with the player present; within one station-day an NPC not
present at it mentions it in overheard dialogue, and the ISN/PA layer carries it iff its
class warrants; a day with no incidents produces visibly quieter news — not recycled lines.

## SYS-09 — TRANSIT, IN THE SHIPPED BUILD
**State:** the four derived timetables (core shuttle 13 stops / drum tram 5 / ground tram
3 / spoke lifts 3 lines — transit.py, all speeds comfort-derived), car positions, lift
cars per shaft (70 shafts).
**Tick:** vehicles move on schedule in the streamed world (transit_runtime.py proves the
motion; the work is wiring it into the boot path, not inventing it).
**Player surface:** RIDE everything; the honest signage — docking bays → Zocalo genuinely
walks faster than the shuttle (6m38s vs 10m32s) and a route panel says so.
**Check:** board the core shuttle at Red, alight at Grey, total time within ±10% of the
derived timetable, in the shipped streamed build, with NPC co-riders whose commutes
(SYS-10 of the roster) put them on that car at that hour.

## SYS-10 — MEDICAL AND HEALTH
**State:** a **condition model, not shooter HP** (auth 5): healthy / hurt / incapacitated /
dead-is-out-of-scope-for-the-player (you wake in medlab, time and credits lost);
per-species wrong-atmosphere exposure timers (six atmospheres are real barriers); Dust as
an event drug (S3E06 pattern); quarantine state per the isolation places.
**Builds:** Franklin's free clinic in Downbelow — sourced, currently unplaced
(LAW-CRIME:910-916 says build it before any security post; the spec honours that ordering).
**Couples to:** SYS-11 locks; SYS-05 (assault outcomes); SYS-14 (accident and quarantine
incidents); medlab staffing (2,800 medical role-holders exist in the data).
**Player surface:** injury has consequences (treatment costs, time); wrong-atmosphere entry
without a mask is a hard timer, not a wall; the medlab-assistant role works triage.
**Check:** enter the alien sector without a breather: the timer runs, vision degrades, a
security/medical response collects the collapsed player, who wakes in medlab_one debited
the sourced treatment cost; the same event for an NPC generates the same chain.

## SYS-11 — ATMOSPHERE AND THE LOCKS
**State:** six standing atmospheres (auth 1); per-place atmosphere class; lock interlock
states; breather-mask inventory at dispensers; encounter-suit NPCs (Gaim, Vorlon — built).
**Player surface:** SHOW-PAPERS + lock cycling to enter alien volumes; suits rentable
(SYS-04); Kosh's door does not open for you.
**Check:** every `atmosphere_containment`/`sealed_environment` place enforces its class:
the lock cycles (both doors never open together — the interlock is the check), the mask
dispenser debits, and an unprotected entry triggers SYS-10's chain.

## SYS-12 — DIALOGUE, MEMORY, STANDING
**State:** the line pools per role×species×topic (targets set in PEOPLE.md §4 — floors
derived from cast sizes, not round numbers); **player utterances exist** (every exchange
offers ≥1 player line with ≥2 choices where a transaction or relationship turns on it);
named-cast memory: tier-1 NPCs remember the player's name, role, standing, and last
significant interaction across saves; faction standing ladders.
**Check:** talk to the dock chief on day 1 as a stranger and on day 9 as a shift-mate with
+standing: different greeting, different topics unlocked, both drawn from pools (not
scripted one-offs), and the day-1 form never reappears once standing has moved.

## SYS-13 — PERSISTENCE
**State:** save = the station clock + day, player state, **world deltas** (vendor stock,
brig ledger, incident log, standing, work orders, camp states) over the deterministic
schedule field.
**Check:** the P2 delta gate (stock still down after reload) PLUS: an incident mid-flight
saves and resumes without duplication or loss; two saves on different days restore
different eras of the news layer.

## SYS-14 — THE INCIDENT GENERATOR
**State:** the class table — enumerated, each with trigger system, district weighting,
actors, escalation, outcomes, consequence writes: dock accident chain (the canon S1
pattern: bad part → dual clearance), contraband find, refused-entry-turned-lurker, hold
stack, sensor sweep, Zocalo theft, Downbelow contact event (1-2/hr there, 95/5 rule),
debt enforcement, Drazi episodic feud (green/purple), pak'ma'ra food segregation friction,
quarantine hold, brownout, elevator outage, forged-card discovery, G'Quan Eth seizure.
**Tick:** ≥2 meaningful incidents/station-hour within the player's district-scale
neighbourhood; every class runnable **absent / player-helps / player-reports** with three
distinct world outcomes.
**Check:** run one headless day; the log shows the rate; replay one seeded incident three
ways and diff the world states — all three differ in named facts (ledger rows, standing,
stock, a body in the brig).

---

## SUR — THE SURFACE, AAA INSIDE AND OUT

- **SUR-01 The five kits at craft ≥4** (corridor — already 4, lift interior, tram car,
  doorway assembly, drum ground) at the rubric's half distance with A/B controls.
- **SUR-02 The landmark set at craft ≥4:** Zocalo, customs hall, council chamber, C&C,
  garden vista, one bar (Earhart's), medlab_one, a docking bay interior. Panel loop, three
  remediation rounds, then CAPPED-with-reason per the standard's hard stop.
- **SUR-03 Civilian ships exist.** Today the Starfury is the ONLY hull geometry in the
  project. Minimum set (from the S-1..S-20 table): EA shuttle, Achilles-type freighter,
  transport, liner, plus the two auth-1 star visitors (Minbari flyer, Vorlon transport) —
  and canon's own build-next #1: **the arriving hull rolling on the axis at 1.7926 rpm**,
  watchable from a viewpoint through the whole 8-phase dock.
- **SUR-04 Starfury launch → fly → dock seamless** from cobra bay, headless-gated + piloted.
- **SUR-05 Lighting:** all SUR-02 rooms in `measure_frame` window against their references;
  the drum runs a day cycle; brownouts (SYS-07) visibly dim real fixtures.
- **SUR-06 Audio completion:** reverb zones, door occlusion, event audio (the INV-260..264
  stated gaps), absolute calibration; every SYS event that should sound, sounds.
- **SUR-07 Viewpoints ≥10** with true exterior/starfield view including the garden vista
  and both observation domes; the traffic of SUR-03 visible from them.
- **SUR-08 People look AAA:** species silhouettes pass `body.py --silhouette`; era wardrobe
  from `costume.py`; work-loop animations per role (not two clips); crowd LOD chain with no
  visible pop at the corridor's 66 m sight line. The "mannequin" fix is capped only by the
  panel loop, not by fiat.
- **SUR-09 The player's UI:** HUD, the in-world station schematic as the map (it already
  draws from `profile`), inventory, identicard screen, BabCom interface — all diegetic
  where canon shows a screen for it.

## SPEC-CHANGE LOG
*(empty at adoption — every post-adoption edit to any spec item lands here, dated, with
reason, or the registry gate fails)*
