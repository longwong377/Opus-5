# SYSTEMS AND SURFACE — normative annex to THE-STATION.md §7–§8

Format law: docs/THE-STATION.md §1 (anti-rig + the grammar appendix) and §2 (tiers). Every
item — SYS **and SUR and VRB** — states its **State, Tick, Couples-to, Player surface, and a
Check that names content**, plus a **harness** line naming what runs the check
(existing tool | tool-to-build ⇒ RED | AUDIT). A field an item genuinely lacks is written
`none`, never omitted. Sources: the four-domain research fan-out (systems inventory), cited
inline as file:line where load-bearing. Inventions marked (auth 5). Cross-doc pointers are
row IDs (PLC/SHB/SHC/INC/FAC/CAST/ROLE/DLG/PLY), never line numbers.

---

## SYS-01 — THE ERA CLOCK AND THE CALENDAR
**State:** `station_day` (integer, persists), `hour` (EMT), era position seeded at
ERA_DATUM=(3,5) advancing one episode-equivalent per N station-days (auth 5: N=7, so a
long player month crosses one era beat); **per-event aftermath state**: each of the 8
`costume.ERA_EVENTS` (npc/costume.py:147-168) carries a post-fire state block (what stays
changed: armband share, refugee flow, bulletin set, seat states) rather than firing and
vanishing.
**Tick:** daily rollover; era events fire from `costume.ERA_EVENTS` as the datum passes
them; **each fired event chains ≥1 SYS-14 incident class re-weighting** (markab_extinct →
INC-QUAR retirement + mourning observances; secession beats → INC-DENOUNCE/INC-PSICOP
weighting up) so an era beat is felt in the incident mix, not only on a screen.
**Couples to:** ISN bulletins (5 era-keyed), MiniPax notices, Nightwatch armbands
(NIGHTWATCH_SHARE=175/500), Narn refugee status, dialogue `_topic_era/_topic_news`,
SYS-15's festival calendar, SYS-14 weightings.
**Player surface:** date on HUD and BabCom; the week visibly moves (SYS-08).
**Check:** boot day 1, run to day 8 headless: the era datum has advanced, ≥1 broadcast
element changed *because of it*, ≥1 SYS-14 class weighting changed with it, and a save made
on day 3 reloads as day 3.
harness: headless day-run (exists as the SYS check pattern; wiring tool-to-build ⇒ RED).

## SYS-02 — TRAFFIC AND DOCKING
**State:** the live berth map (24 bays × A/B levels, standoff ring, moorings), per-ship
manifest rows — **the code's own class table, restated 1:1 (traffic.py:132-142), 55.0
arrivals/day exactly**: freighter_bay 20 · transport 14 · shuttle 12 · freighter_standoff
3.7 · **tanker 0.3 (split out of freighter_standoff, berth standoff — the fuel run
PLC-039/120's checks already name; SPEC-CHANGE #3, code pending)** · diplomatic 2 ·
liner 0.5 · ef_transport 2.0 · ef_warship 0.3 · alien_warship 0.2 — **ten classes**;
DAY_BANDS (peak-to-trough 3.12:1), bay-elevator duty cycle (2 units, ~5 min cycle, 62%
peak).
**Tick:** hourly arrivals draw; 8-phase docking state machine per ship (gate transit 20 s →
beacon → 65 km inbound → clearance → roll match → axial entry → elevator → berth).
**Couples to:** customs load (`hall_rate`, liner peak 8.5 souls/min), cargo → SYS-04
deliveries, PA port calls, arrivals boards (live already — signage.py:549-603), SYS-14
classes INC-HOLD, INC-ACCIDENT, INC-LINER; SUR-03 (each class needs its hull).
**Player surface:** watchable from viewpoints and the bays; the boards and PA always agree
with the berth map because they read it.
**Resolves:** C-012 (souls/day ×3.6 conflict) — one number chosen, written into
CONFLICTS.md, all three consumers re-derived from it.
**Check:** across one headless day: every announced arrival exists in the berth map; a named
liner docks at its band; the named tanker's arrival steps up PLC-120's slush wall; the
elevator cycle bounds throughput; boards/PA/berths never disagree (the three-reader
agreement is the check).
harness: traffic.py selftest (exists) + headless day-run (tool-to-build ⇒ RED).

## SYS-03 — CUSTOMS
**State:** per-hall queue depth, 10-station pipeline (arrival.py:440-545), entry classes
(EA_CITIZEN…NO_STATUS, "-- EXPIRED"), outcome routing.
**Tick:** processes SYS-02's disembarkations; **1%/day leak of refused/broke arrivals to
Downbelow, defined as leak = P(credits < 300)** — the 300 cr passage-home FLOOR of
LAW-CRIME:748's 300–800 band (SPEC-CHANGE #1; player.py re-solve pending) — the underclass
is *fed by the port*, not spawned.
**Builds:** `secondary_inspection` and `customs_holding` — both currently
`built=False` in arrival.UNBUILT; **both are built under PLC-003** (its program names
them; no separate rows).
**Couples to:** SYS-02 disembarkations, SYS-05 (custody), SYS-06 (what it misses),
INC-FRAUD/INC-CONTRA/INC-REFUSED.
**Player surface:** the player IS processed on arrival (PLY-01); as a customs-officer role,
works the desk: reads cards, spots forgeries (SYS-06 feeds them through), flags atmospheres,
finds contraband at the real P=0.01/0.04 rates.
**Check:** an arriving NPC with an expired visa is refused, cannot afford the 300 cr
passage floor, and appears in Downbelow with their name intact within 2 station-days.
harness: arrival.py selftest (exists) + headless 2-day run (tool-to-build ⇒ RED).

## SYS-04 — THE ECONOMY
**State:** per-vendor stock lists and prices (anchored to the ONE auth-1 price: command
quarters 30 cr/wk; ladder per LAW-CRIME:739-748 — cart meal 1-2 cr, dock day-labour
8-15 cr, dosshouse bunk 1 cr/night, **passage home 300–800 cr**); per-resident credits
(CREDIT_MIN/MAX exist, player.py:140-174); wages per role per shift; rents (the station's
sourced revenue model); **named goods only — every stock line, menu line and price is a
GDS-01 vocabulary entry** (PLACES §0.3), so "stock" is spoo and bearings, never tokens;
**the contracts ledger** (auth 5): PLC-083's six named research projects, FAC-05's
telepath-witnessed contracts and PLC-012 notary work write here, and contract disputes
land on the Ombuds docket (SYS-05).
**Tick:** wages at shift end; rents weekly; vendor stock **depletes by purchase and
replenishes by delivery** — and a delivery is a real container off a real ship through the
real cargo bays (the full T4 chain: ship → cargo bay → porter route → stallhold restock).
**Sinks (late-game, so tens of hours have somewhere to spend):** (1) the trade ladder
cart → pitch → shopfront lease (ROLE-05 mastery, priced in weeks of margin); (2)
**sponsoring passages home at 300–800 cr a head** — the one purchase that moves a named
lurker OFF the camp roster (FAC-09/FAC-24 standing content); (3) the rent-tier ladder up
to business-class quarters plus furnishing it (PLY-03's placed-prop persistence).
**Couples to:** SYS-02 (a docking strike is a food story — LIFE-SUPPORT:219-253), SYS-05
(debt enforcement), SYS-06 (untaxed goods undercut Zocalo prices), roles (pay), GDS-01.
**Player surface:** BUY/SELL everywhere commerce is declared; the player pays rent or
loses their quarters assignment; prices visibly differ Zocalo vs under-counter.
**Check:** buy the last unit of a named good at a named stall; the stall shows empty; the
restock arrives on a manifest ship within its schedule; save/reload preserves both states.
(This is also PLY-01/PLY-03's save-delta gate.)
harness: economy headless-day + save-delta gate (tool-to-build ⇒ RED).

## SYS-05 — LAW AND CRIME
**State:** 500 officers / ~150 on duty / 3 watches (implemented, npc/security.py); 56
posted at the POSTS table; roving pairs derived; per-district patrol frequencies (Zocalo
continuous … Downbelow ZERO); the offence table (LAW-CRIME:816-838, petty theft
dozens/day → murder single-figures/yr); the brig custody ledger (24-40 cells, ≥3
atmospheres); ombudsman docket (2 named ombudsmen, sessions in `law_courts`).
**Tick:** crime events generated per district per hour at the sourced rates (90% of crime
in Downbelow among 8% of population); detection only where security actually is (the
response-time model: seconds in the Zocalo, 12-20 min far outer ring); escalation ladder
7 rungs, identicard check the commonest interaction; **victim resolution is a sub-row of
every crime event: the victim (NPC or player) resolves {comply | resist | flee} with three
distinct outcomes** — comply feeds the report rate, resist feeds SYS-10 casualties,
flee feeds INC-CONTACT chase texture — so a theft is an event with two parties, not a
stat draw.
**Couples to:** SYS-14 (crimes are incident instances), SYS-03 (identicards), SYS-06,
SYS-08 (a sweep is PA-announced and the camp empties — LAW-CRIME:900-948), SYS-10.
**Player surface:** the player can be checked, moved on, detained, tried, briged, fined;
the 95/5 avoidance/contact rule and the **marked-out mechanic** (clothing/gait/light, not
a hostility radius — the player's wardrobe is the input, PLY-04) govern Downbelow; as
deputy role, the player works a beat.
**Check:** a scripted theft in the Zocalo is detected in seconds and the thief walked to
the brig; the same theft template in Downbelow at 03:00 completes undetected; the brig
ledger shows the first, not the second; the player committing the Zocalo version ends in
the brig with a fine and a record on their card; the Downbelow victim's {comply|resist|
flee} branch each leaves its distinct world state.
harness: npc/security.py selftests (exist) + scripted-event runner (tool-to-build ⇒ RED).

## SYS-06 — THE BLACK MARKET (a route, not a room — LAW-CRIME:858-879)
**State:** the route's five stations (bribed docker → cargo lift → unfinished-deck cache →
fixer → Zocalo under-counter); the Broker as the era's fixer (sealed non-oxygen room,
`ngrath` place exists); forged identicard supply; contraband inventory seeded by what
customs misses (GDS-01 names the goods).
**Tick:** goods move down the route on porter schedules; prices float under Zocalo's.
**Couples to:** SYS-03 (supply = what scanning missed), SYS-04 (price undercut), SYS-05
(reports, INC-FRAUD), FAC-25.
**Player surface:** findable by following a porter or earning lurker trust; buyable
(forged card = a new identity with its own risks); reportable (SYS-05 consequence).
**Check:** an item confiscable at customs, bought under-counter, traces back through the
route's five stations when followed — each station a real place with a real NPC.
harness: route-trace scripted run (tool-to-build ⇒ RED).

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
harness: plant headless-day + in-engine dim A/B (tool-to-build ⇒ RED).

## SYS-08 — THE INFORMATION LAYER
**State:** ISN bulletin queue (5 era-keyed + incident-derived), MiniPax notices, PA
schedule (port calls, watch calls, civic calls — broadcast.py implements all three),
arrivals boards (live), BabCom per-resident directory + messages, **the rumour pool**:
dialogue's news topic drawing on the *incident log*, so what people say happened is what
happened.
**Tick:** "the week has news" — two consecutive days differ in broadcast and rumour content
derived from SYS-02/05/07/14/15 events plus the era clock, never from a script.
**Couples to:** SYS-01/02/05/07/14/15, SYS-16 (public facts), FAC-27.
**Player surface:** BabCom terminals are usable (directory, messages, news); signage is
live; overheard dialogue references real events the player may have been present at.
**Check:** cause an incident with the player present; within one station-day an NPC not
present at it mentions it in overheard dialogue, and the ISN/PA layer carries it iff its
class warrants; a day with no incidents produces visibly quieter news — not recycled lines.
harness: broadcast.py (exists) + rumour-diff headless run (tool-to-build ⇒ RED).

## SYS-09 — TRANSIT, IN THE SHIPPED BUILD
**State:** the four derived timetables (core shuttle 13 stops / drum tram 5 / ground tram
3 / spoke lifts 3 lines — transit.py, all speeds comfort-derived), car positions, lift
cars per shaft (70 shafts). The core shuttle line runs z 3,397–8,047 (4,650 m, stops
@387.5 m) — the register row is corrected by SPEC-CHANGE #2 (PLC-102/113).
**Tick:** vehicles move on schedule in the streamed world (transit_runtime.py proves the
motion; the work is wiring it into the boot path, not inventing it).
**Couples to:** SYS-02 (commutes to shifts), life.py routing, PLC-073/074/102/113/114/116.
**Player surface:** RIDE everything; the honest signage — docking bays → Zocalo genuinely
walks faster than the shuttle (6m38s vs 10m32s) and a route panel says so.
**Check:** board the core shuttle at Red, alight at Grey, total time within ±10% of the
derived timetable, in the shipped streamed build, with NPC co-riders whose commutes
(life.py-routed per the roster — the old "SYS-10" cross-ref here was a typo the
adjudication missed) put them on that car at that hour.
harness: transit_runtime RIDETEST (exists) + shipped-build ride (tool-to-build ⇒ RED).

## SYS-10 — MEDICAL AND HEALTH
**State:** a **condition model, not shooter HP** (auth 5): healthy / hurt / incapacitated /
dead-is-out-of-scope-for-the-player (you wake in medlab, time and credits lost);
**`drunk` is a condition in the same model** (BUY/DRINK past a threshold → gait and
dialogue effects, security public-order interest; ROLE-04's cut-off loop writes it, and it
decays by morning); per-species wrong-atmosphere exposure timers (six atmospheres are real
barriers); Dust as an event drug (S3E06 pattern); quarantine state per the isolation
places; **the gravity-therapy queue**: PLC-084's bookings are clinical state — high-g
natives decompress on schedule and a missed session is a visible welfare fact.
**Builds:** Franklin's free clinic in Downbelow — sourced, **placed at SHB-08.a**
(LAW-CRIME:910-916 says build it before any security post; the spec honours that ordering).
**Couples to:** SYS-11 locks; SYS-05 (assault outcomes, drunk-and-disorderly); SYS-14
(accident and quarantine incidents); SYS-15 (therapy bookings); medlab staffing (2,800
medical role-holders exist in the data).
**Player surface:** injury has consequences (treatment costs, time); wrong-atmosphere entry
without a mask is a hard timer, not a wall; the medlab-assistant role works triage; the
player can be drunk, and it shows.
**Check:** enter the alien sector without a breather: the timer runs, vision degrades, a
security/medical response collects the collapsed player, who wakes in medlab_one debited
the sourced treatment cost; the same event for an NPC generates the same chain; a drunk
patron cut off at `bar_unnamed` is walked out and their condition has decayed by morning.
harness: condition-model selftest + scripted runs (tool-to-build ⇒ RED).

## SYS-11 — ATMOSPHERE AND THE LOCKS
**State:** six standing atmospheres (auth 1); per-place atmosphere class; lock interlock
states; breather-mask inventory at dispensers; encounter-suit NPCs (Gaim, Vorlon — built).
**Tick:** zone atmospheres are simulated state; dispenser stock depletes and reorders
(SYS-04); lock faults are INC-FAULT instances.
**Couples to:** SYS-10 (exposure), SYS-07 (feedstock from PLC-100), PLC-023/024/046/078.
**Player surface:** SHOW-PAPERS + lock cycling to enter alien volumes; suits rentable
(SYS-04); Kosh's door does not open for you.
**Check:** every `atmosphere_containment`/`sealed_environment` place enforces its class:
the lock cycles (both doors never open together — the interlock is the check), the mask
dispenser debits, and an unprotected entry triggers SYS-10's chain.
harness: interlock assert (tool-to-build ⇒ RED) + AUDIT walk.

## SYS-12 — DIALOGUE, MEMORY, STANDING
**State:** the line pools per role×species×topic (targets set in PEOPLE.md §4 — floors
derived from cast sizes, not round numbers); **player utterances exist** (every exchange
offers ≥1 player line with ≥2 choices where a transaction or relationship turns on it);
named-cast memory: tier-1 NPCs remember the player's name, role, standing, and last
significant interaction across saves; faction standing ladders; **bounded tier-2 memory
(auth 5): every member of a place's stable regulars/affiliates pool (resident.py:846-893)
carries K=3 memory slots — last interaction, standing band, one keyed fact (a price, a
favour, a debt)** — so the faces a player actually re-meets remember them, and Tier-3
statistical draws do not (the bound is the honesty).
**Tick:** memory writes on interaction end; standing moves on ledger events; greeting
bands re-derive from standing daily.
**Couples to:** CAST-02/03/05, SYS-16 (facts minted in dialogue), every ROLE.
**Player surface:** TALK everywhere; the difference between a stranger, a face and a name.
**Check:** talk to the dock chief on day 1 as a stranger and on day 9 as a shift-mate with
+standing: different greeting, different topics unlocked, both drawn from pools (not
scripted one-offs), and the day-1 form never reappears once standing has moved; a Zocalo
regular quotes the player the price they haggled to last week (the K-slot fact), and a
Tier-3 stranger does not.
harness: dialogue.py pools (exist) + memory-state selftest (tool-to-build ⇒ RED).

## SYS-13 — PERSISTENCE
**State:** save = the station clock + day, player state, **world deltas** (vendor stock,
brig ledger, incident log, standing, work orders, camp states, **player prop placements —
PLY-03's class**) over the deterministic schedule field.
**Tick:** none (event-driven: save/load).
**Couples to:** every stateful system above; PLY-03.
**Player surface:** save/load that keeps promises.
**Check:** the PLY-01 delta gate (stock still down after reload) PLUS: an incident
mid-flight saves and resumes without duplication or loss; two saves on different days
restore different eras of the news layer; a placed prop is where the player left it.
harness: save-delta gate (tool-to-build ⇒ RED; named in MASTER-PLAN P2).

## SYS-14 — THE INCIDENT GENERATOR
**State:** the class table — **the 22-class union below IS PLACES §0.2's vocabulary, 1:1
in both directions; the generator asserts the two lists are identical** (a class here
without a PLACES ID, or a PLACES ID without mechanics here, fails the gate). Each row:
trigger / actors / escalation / consequence writes.

**Tick:** classes fire from their trigger systems at their sourced rates, weighted by
district and by SYS-01's era position. **Rate floor: ≥2 meaningful incidents per
station-hour inside a fixed probe volume** (the volume is fixed so the rate cannot be
inflated by widening the window); **"meaningful" = the incident writes ≥1 world delta** —
a brig custody row, a standing change, a stock move, a work order, or a card endorsement.
**Couples to:** every SYS above (each row names its trigger), PLACES §0.2's vocabulary,
FAC standing, SYS-13 persistence.
**Player surface:** incidents happen near the player at the rate above and are joinable,
reportable or ignorable; none of them requires the player to exist.
**CHECK:** one headless station-day at ×1 logs the rate inside the probe volume; **one
seeded incident replayed three ways — player-absent / player-helps / player-reports —
yields three world states that differ in NAMED facts** (which ledger row, whose standing,
which stock line, who is in custody), not merely in a log string; and the 22-row union
above matches PLACES §0.2 in both directions (asserted by `tools/spec_registry.py`).
**harness:** `tools/spec_registry.py --check` (bijection half, exists) + incident
headless-day and three-way replay (tool-to-build ⇒ RED).

| ID | trigger (system) | actors | escalation | writes |
|---|---|---|---|---|
| INC-LINER | SYS-02 liner row (0.5/day, ~2/wk) | liner pax 400–800, hall staff, touts | one hall at 8.5 souls/min ~90 min → queue overflow → advisory PA | berth map, hall load, INC-PICK weighting, vendor sales spike |
| INC-ELEV | SYS-02 duty-cycle draw (2 units, 62% peak) | elevator crew, maintenance, waiting gangs | unit down → INC-HOLD forms → guild grievance line | berth delays, work order, grievance board |
| INC-CONTRA | SYS-03 scan (P=0.01, ×4 no-status) | passenger, scanner op, posted security | find → seizure room (PLC-003) → custody or fine | seizure log (item named per GDS-01), custody ledger, SYS-06 supply |
| INC-REFUSED | SYS-03 refusal; credits < 300 (SPEC-CHANGE #1) | refused arrival, aid desk, touts | hall wait → failed passage → Downbelow leak (~15/day) | card state, roster home=camp, camp population |
| INC-SWEEP | SYS-05 sweep scheduler (LAW-CRIME §5.5) | patrol detail, a camp | PA-announced approach → camp empties ahead of it → fruitless → re-forms +6 h | patrol log, camp state timeline, player standing if seen helping either side |
| INC-BRAWL | Drazi cycle switch (OFF at datum, FAC-13) + venue heat | Drazi factions, venue keeper, patrol | shove → melee → RESTRAIN arrests; victims resolve {comply\|resist\|flee} (SYS-05) | custody ledger, medlab records, venue damage state |
| INC-DENOUNCE | FAC-04 box filings | informer, armband pair, merchant, neighbours | box report → 19:00 muster read-out → questioning scene → shutter or changed lines | SYS-05 case, merchant state, informer standing |
| INC-DUST | FAC-25 supply event (rare) | dealer, buyer, security; a Psi Cop follows | deal → seizure → casualty to medlab → Corps follow-up (INC-PSICOP) | seizure log, SYS-10 record, era note |
| INC-PICK | SYS-05 district rates (dozens/day) | thief (roster-drawn), victim {comply\|resist\|flee}, patrol | lift → detection-by-presence → chase/arrest or clean escape | victim inventory, custody or unsolved row, district heat |
| INC-FRAUD | SYS-03/05 reader events (VISA_EXPIRED_P=1/12; SYS-06 forgeries) | card holder, reader, officer | flag → secondary inspection → refusal/custody → docket | card state, docket, SYS-06 vendor heat |
| INC-ACCIDENT | SYS-02 clearance draw (the S1 bad-chip chain) | dock gang, C&C console op, medlab | bad part → dual clearance → casualty → union action (feeds INC-STRIKE) | work order, medlab/morgue record, grievance board, ISN item |
| INC-BROWNOUT | SYS-07 shed event | plant watch, district residents, maintenance | shed → district lights step down → APU pickup (PLC-122) → relight by priority | fixture states, PA advisory, work order |
| INC-QUAR | SYS-02/10 flagged arrival | ship, medical officer, customs supervisor | hold → roped queue → isolation path (PLC-046) → clear/extend | berth hold, SYS-10 records, hall throughput |
| INC-PSICOP | SYS-01 era draw (every few weeks) | Psi Cop pair, corridor crowds | arrival → corridors quieten (audio-measurable) → business call → departure | crowd-audio state, FAC-05 notes, rumour pool |
| INC-NC | friction.py contact draw (0.02/h — rare, severe) | Narn party, Centauri party, bystanders | stand-off, no yield → crowds reroute → rare SYS-05 escalation | friction log, rumour pool, standing if the player intervenes |
| INC-GQE | SYS-01 season + customs hold | Narn celebrant, customs desk, security attending | seizure → argued at the desk → ceremony with/without the plant → sometimes docket | seizure log, ceremony state, docket |
| INC-STRIKE | FAC-06 ballot (grievance board T4 threshold) | guild, casuals, EA liaison | ballot → slowdown/"blue flu" → muster thins → SYS-04 delivery ripple in days → settlement | muster rates, delivery delays, grievance closure |
| INC-FAULT | SYS-07 failure draws + wear | the broken thing, work-order board, assigned tech | fault → order → walk → repair → close | work-order ledger, fixture state |
| INC-HOLD | SYS-02 berth saturation / elevator loss | inbound queue, C&C, standoff ring | stack forms at standoff → PA delay calls → tempers in the arrival hall | berth map, PA queue, arrival lateness |
| INC-CONTACT | security.py DOWNBELOW_CONTACT_PER_HOUR=1.5 (the 5% of 95/5) | lurkers, the marked-out (PLY-04's wardrobe input) | approach → demand/beg/warn → resolve {comply\|resist\|flee} | camp standing, inventory, SYS-10 on resist |
| INC-DEBT | FAC-25 ledger ages past terms | the Collector, debtor, camp watchers | visit → pay/plead/hide → seizure or a beating (SYS-10) → ledger closes or rolls | crime ledger, debtor state, camp fear texture |
| INC-PAKMA | species meal windows 04:00/16:00 + a wrong-seat diner | pak'ma'ra diners, a transient, venue staff | polite translator ask → tables clear → staff resolve → a rumour line | seating state, venue rumour, standing if the player is the diner |

**Tick:** ≥2 meaningful incidents/station-hour **within fixed probe volumes — the district
cell holding the player plus its adjacent cells, fixed at tick start** (never a floating
radius an implementation can shrink); **"meaningful" = writes ≥1 world delta: a ledger
row, a standing change, a stock movement, or a custody entry.** Every class runnable
**absent / player-helps / player-reports** with three distinct world outcomes.
**Couples to:** every SYS above; PLACES rows cite these IDs; SYS-08 carries the news.
**Player surface:** the world happening — and three stances toward any of it.
**Check:** run one headless day; the log shows the rate measured in the probe volumes;
replay one seeded incident three ways and diff the world states — all three differ in
named facts (ledger rows, standing, stock, a body in the brig); the generator's union
assert (this table ↔ PLACES §0.2) passes both directions.
harness: headless day-run + seeded replay differ (tool-to-build ⇒ RED).

## SYS-15 — THE CIVIC CALENDAR
**State:** the station-wide bookings-and-observances ledger: **venue bookings** (PLC-053
function rooms, PLC-058 courts and training bays, PLC-059/060 conference slots, PLC-063
ceremonies, PLC-064 bookable quiet hours, PLC-067 lessons, PLC-068 terrace events, PLC-069
swim lanes, PLC-105 tables); **faith rotas** (PLC-049/075/111/112 + FAC-11's caste rota
and FAC-26's offices); **festival weeks** (per-species calendar, Parliament-of-Dreams
precedent — PLC-025's square dressing and PLC-110's harvest week are its physical states);
**drills** (PLC-031 defence readiness, PLC-096 quarterly disconnect, PLC-128 gunnery,
PLC-002's shutter drills; SYS-07 brownout drills); **invitation-gated receptions**
(FAC-10's social calendar — an invitation is an inventory item with the player's name).
**Tick:** daily assembly from SYS-01 (era + festival dates) and faction calendars;
bookings are held by named residents; events start, run and strike ON TIME with attendance
drawn from rosters; cancellations propagate to SYS-08's boards.
**Couples to:** SYS-01 (dates), SYS-08 (notices), SYS-04 (deposits, catering — a wedding
is a Zocalo order), SYS-05 (a festival is a policing plan), SYS-12 (standing gates),
SYS-14 (a drill is an incident-class exercise); consumer rows: PLC-002/031/053/058/059/
060/063/064/067/068/069/070/096/105/110/112/128, FAC-10/11/26.
**Player surface:** read any booking board; book what standing and credits allow (a
ceremonial room, a court, a table at Fresh Air, a lesson); attend public events; be turned
away from invitation-gated ones until invited.
**Check (named, end-to-end):** across one station-week the calendar holds ≥1 wedding
(PLC-053, a named Tier-2 couple), one species festival week (PLC-025 square dressed +
PLC-110 harvest tie + PLC-070's rigged banner), the Tuesday 17:00 security unarmed-combat
class (PLC-058, real officer NPCs), the quarterly PLC-096 drill with station-wide PA, a
MiniPax public meeting (PLC-053's borrow, P-06), and one Centauri reception (invitation-
gated: the player without an invitation is refused by the named door aide, with the line)
— every event occurs in-room at its posted hour with roster-drawn attendees, and each
surfaced on SYS-08's boards beforehand.
harness: headless week-run + board diff (tool-to-build ⇒ RED).

## SYS-16 — KNOWLEDGE ITEMS AND THE JOURNAL
**State:** typed knowledge facts — name-given, tell-learned (FAC-28's brooch), route-time
(the porter's craft), job-offer, debt, appointment, rumour-with-truth-value — each with
source event and timestamp; **the journal (PLY-07, SUR-09) is the surface; ROLE-10's
tradable commodity IS a knowledge fact with a verification state.**
**Tick:** facts are minted ONLY by real events (a rumour references the incident log; a
route-time references transit.py's derived numbers); a fact about mutable state carries
its as-of day and can go stale.
**Couples to:** SYS-12 (dialogue mints and spends facts), SYS-08 (public facts), SYS-14
(incidents mint facts), CAST-05 (name-given), ROLE-10 (the trade).
**Player surface:** the journal; TALK options that spend or verify facts; SELL per
ROLE-10's four buyers.
**Check:** overhear a ROUTE shipment's timing at `happy_daze` → the fact appears sourced
to that conversation; sell it to the security tip desk → the interception event references
the same fact id; let it go stale (the shipment moved) → verification fails and the
buyer's payout and the standing consequences differ — all three states persisted.
harness: tool-to-build ⇒ RED.

---

## SUR — THE SURFACE, AAA INSIDE AND OUT
*(five-field format; a field an item lacks is `none`.)*

### SUR-01 — The five kits at craft ≥4
**State:** corridor (already 4), lift interior, tram car, doorway assembly, drum ground —
per-kit craft scores in `docs/aaa-scorecard.json`.
**Tick:** none (static content; re-scored on every kit change).
**Couples to:** every place built from the kits (most of the station's walked surface).
**Player surface:** everywhere the player walks.
**Check:** each kit scores craft ≥4 at the rubric's half distance with A/B control frames
filed; no kit regresses below 4 after any change (the scorecard is the memory).
harness: tools/render_godot.sh + panel scoring (exists; every filed frame quotes the
renderer's self-reported mode line per §1.3 — an OpenGL-fallback frame is not evidence).

### SUR-02 — The landmark set at craft ≥4
**State:** Zocalo, customs hall, council chamber, C&C, garden vista, Earhart's,
medlab_one, a docking bay interior — eight named rooms, panel history per room.
**Tick:** none.
**Couples to:** their PLC rows; SUR-05 lighting.
**Player surface:** the rooms a viewer would screenshot.
**Check:** craft ≥4 per room at the rubric's half distance; panel loop with up to three
remediation rounds per room. **Capping: only an owner-signed dated quote in §9 caps a
landmark row, and craft <3 is uncappable — there is no pre-authorized cap here** (this
supersedes the earlier "then CAPPED-with-reason" clause; agents may PROPOSE-CAP and the
row stays RED, per §1).
harness: engine render + adversarial panel (exists); verdicts filed by the NEXT
session's reviewer, never the builder.

### SUR-03 — Civilian ships exist
**State:** today the Starfury is the ONLY hull geometry in the project. The minimum set is
**the union of every hull the spec's own checks name**: EA shuttle · Achilles-type
freighter · transport · liner · **tanker** (PLC-039/120, SPEC-CHANGE #3) · **EF Omega**
(PLC-040/126's moored checks) · **Vree saucer + its lighter** (FAC-16's check) · Minbari
flyer (auth 1) · Vorlon transport (auth 1) — ten hulls plus the Starfury.
**Tick:** SYS-02 instantiates them on the manifest; the standoff saucer never berths.
**Couples to:** SYS-02, PLC-006/035/040/044/126, FAC-16, SUR-07 (seen from viewpoints).
**Player surface:** watchable dockings; canon's own build-next #1: **the arriving hull
rolling on the axis at 1.7926 rpm**, watchable from a viewpoint through the whole 8-phase
dock.
**Check:** every hull named by any PLACES/PEOPLE check resolves to a real hull asset (the
generator extracts the union and asserts it); a rendered berth-map day shows no
placeholder hull; the axial-roll approach shot exists and is filed.
harness: asset-union assert (tool-to-build ⇒ RED) + engine render.

### SUR-04 — Starfury launch → fly → dock, seamless
**State:** cobra bay launch (drum spin is the throw), 6-DOF flight
(`starfury_geometry.py` + `starfury.gd`: mains 55.14 m/s, kill-velocity 0.41 m/s),
recovery roll-match at the corrected berth speeds.
**Tick:** none for the player; NPC sorties ride SYS-02.
**Couples to:** PLC-035, ROLE-12, SYS-02 (the launch slot is a berth-map event).
**Player surface:** PILOT.
**Check:** headless-gated launch→flight→dock cycle passes; a piloted run works in the
shipped build; the launch appears in the berth map as a traffic event other systems see.
harness: starfury.gd pilot test (exists) + shipped-build integration (tool-to-build
⇒ RED).

### SUR-05 — Lighting
**State:** per-room rigs; `measure_frame` distribution windows against show references
(13/23 today).
**Tick:** the drum runs a day cycle; SYS-07 brownouts dim real fixtures.
**Couples to:** SYS-07, SUR-02, every PLC row's mood.
**Player surface:** everywhere.
**Check:** all SUR-02 rooms in `measure_frame` window against their references; the drum's
day cycle renders; a forced brownout visibly dims a named room's own fixtures in-engine
(A/B filed).
harness: tools/measure_frame.py --gate-frames --rerender (exists).

### SUR-06 — Audio completion
**State:** reverb zones per room class; door occlusion; absolute calibration (INV-260..264
close); **performers and diegetic music**: the Dark Star floor show's posted set
(PLC-014), the monastery offices' chant at canonical hours (PLC-111), and **a licensed
Zocalo busker pitch** (PLC-011) — music somebody in the world is making.
**Tick:** every SYS event that should sound, sounds, when it fires.
**Couples to:** every SYS; the event→sound table below is the contract.
**Player surface:** everywhere; a shut door muffles.
**Event→sound table (enumerated, each a distinct emitter):** door open/close per class ·
lock cycle + pressure equalise · PA × {port call, watch call, civic call, sensor sweep} ·
till transaction · stock delivery (cart + crate-drop) · brawl (crowd surge + furniture) ·
arrest (restraint + radio) · sweep approach (boots + PA — the camp hears it coming) ·
brownout (contactor thunk + HVAC pitch fall + APU pickup whine) · elevator fault klaxon ·
Starfury launch (spin-timer count + release) · docking clamp engage · tram/shuttle
arrive/depart + bell · the township waterfall zone (62 dB signature) · the 0.75 Hz
compressor beat · chant at the offices · 06:00 muster call · denunciation-box slot ·
dartboard / wheel / chips · Kosh's transit (spreading silence IS the cue) · the busker's
set · the floor show.
**Check:** a scripted pass fires every table row audibly at its source with its reverb
zone; the INV-260..264 stated gaps (reverb, occlusion, event audio, absolute reference)
are each closed with an A/B; a shut door measurably attenuates the room behind it.
harness: station/audio.py (exists, ambience) + in-engine event audio capture
(tool-to-build ⇒ RED).

### SUR-07 — Viewpoints
**State:** ≥10 viewpoints with true exterior/starfield view, including the garden vista
and both observation domes; visible contents: SUR-03's traffic, the jump gate cycle,
**Epsilon III below, and the day/night terminator moving with SYS-01's clock**; PLC-064's
four sky plaques name true bearings **including planetward (Epsilon III)**.
**Tick:** views track live sim state (gate transits, berth traffic, the planet's phase).
**Couples to:** SYS-01/02, PLC-002/030/049/063/064, SUR-03.
**Player surface:** LOOK, and the reason to ride out to a rotunda.
**Check:** from a named rotunda the player watches a scheduled gate transit on time AND
Epsilon III renders below with its terminator where the clock puts it; all ≥10 viewpoints
show true exterior state, no skybox lies.
harness: engine render + ephemeris assert (tool-to-build ⇒ RED).

### SUR-08 — People look AAA
**State:** species silhouettes pass `body.py --silhouette`; era wardrobe from
`costume.py`; work-loop animations per role (not two clips); crowd LOD chain.
**Tick:** none.
**Couples to:** SYS-12, every FAC block, SUR-02's crowded rooms.
**Player surface:** everyone the player sees.
**Check:** the silhouette gate is green per species; each ROLE's shift renders its own
work loop; the LOD chain shows no visible pop at the corridor's 66 m sight line (A/B
filed). The "mannequin" fix is capped only by an owner-signed panel verdict, not by fiat.
harness: npc/body.py --silhouette (exists) + render panel.

### SUR-09 — The player's UI
**State:** HUD, the in-world station schematic as the map (it already draws from
`profile`), inventory, identicard screen, BabCom interface, **and the journal (PLY-07 —
SYS-16's surface)** — all diegetic where canon shows a screen for it.
**Tick:** every panel reads live state.
**Couples to:** SYS-08/13/16, PLY-07, VRB rows.
**Player surface:** the player's own screens.
**Check:** every UI panel renders live truth — the schematic pages the real sectors, the
identicard shows the player's real card state, the journal holds real learned facts and
nothing unlearned; no panel displays a value the simulation does not hold.
harness: UI state-diff assert (tool-to-build ⇒ RED).

---

## VRB — THE PLAYER'S VERBS, ONE REGISTRY ROW EACH

The closed set (THE-STATION §2). Each verb is a registry row: it exists, it works
everywhere its tier table says, and its check names content. harness for all thirteen:
the per-verb wiring is **tool-to-build ⇒ RED** today (no player verbs are shipped);
existing models named per row.

| ID | verb | the bar | CHECK (names content) |
|---|---|---|---|
| VRB-01 | LOOK | every interactable answers with true, specific text (T1 rule: no two identical strings in a room class) | 20 sampled interactables across 5 rooms yield 20 distinct true strings; PLC-092's stencils and PLC-047's drawer tags among them |
| VRB-02 | USE | T2/T3 operation with visible own-state or remote-state change | a valve turns (state), a lift_call summons a car (remote), PLC-002's shutter master shutters C&C (cross-room) |
| VRB-03 | TAKE/PLACE | inventory exists; placement persists (PLY-03) | take a GDS-01 item from a stall, place it on the player's quarters shelf, reload — still there |
| VRB-04 | SIT | any seat-family token; NPCs use the same seats; friction seating respected | sit at `bar_unnamed`; will_share_table refuses the seat beside the Centauri party correctly |
| VRB-05 | BUY/SELL | credits and stock move both ways, including the fence path | buy the cart meal (1–2 cr); sell a salvage item to Vane (CAST row 41) at fence rates |
| VRB-06 | TALK | choice-bearing dialogue (DLG-05): ≥2 stances where a transaction or relationship turns | the ROLE-05 questioning scene answers three ways, three persisted outcomes |
| VRB-07 | WORK | all 12 ROLE shift loops clock on and off with pay | one full shift of each ROLE passes that ROLE's own ACCEPT |
| VRB-08 | SHOW-PAPERS | the card is presented, read, and reacted to — both directions (player shows; player reads as officer) | the Grey-boundary stop reads the player's real card state and reacts to its visa |
| VRB-09 | FIGHT/RESTRAIN | minimal, two-way: security can restrain YOU; the 7-rung ladder governs | the player's own arrest ends in a brig cell with a readable booking record (PLC-017's check) |
| VRB-10 | PILOT | SUR-04's loop | the ROLE-12 sortie, launch to recovery |
| VRB-11 | RIDE | every SYS-09 vehicle boardable, timetable-true | shuttle Red→Grey inside ±10% of the derived time (SYS-09's check) |
| VRB-12 | SLEEP | PLY-05's rules: advances the clock through the running sim; interruptible | sleep 22:00→05:15, make the 05:40 muster; a sweep event wakes the player |
| VRB-13 | EAT/DRINK | meals debit and feed (PLY-06's signed state); species venues respected | eat at Eclipse at 04:00; the pak'ma'ra area politely ejects the player (INC-PAKMA) |

---

*Item census: SYS-01..16 · SUR-01..09 · VRB-01..13 = **38 registry rows**.*

## SPEC-CHANGE LOG
Entry format (THE-STATION §1/§9): dated · what · why · owner-visible ·
**recomputes: every downstream number touched**. An edit without its recomputes list is
invalid.

- **2026-08-04 — SPEC-CHANGE #1 pending (adoption-blocking, RED): passage-home floor.**
  What: adopt **300–800 cr** (LAW-CRIME:748, the sourced band) station-wide; the Downbelow
  leak is defined **leak = P(credits < 300)**. Code edit pending:
  `station/player.py:164` `PASSAGE_HOME_CR = 250.0` → `300.0` (CREDIT_SKEW self-derives:
  ln(300/5000)/ln(0.01) = ln 0.06/ln 0.01 ≈ 0.6111, replacing 0.6506; update the
  derivation comment) and `arrival.py::_selftest`'s negative control expectation 5% → 6%
  (flat-draw P = 300/5000). Why: three contradictory numbers (250 / <250 / 300–800) in
  four files; the sourced band wins. Owner-visible: yes (this log).
  **recomputes:** SYS-03 check 250→300 (this file) · SYS-04 ladder "250-800"→"300–800"
  (this file) · PLACES §0.2 INC-REFUSED 250→300 · PEOPLE ROLE-08 "<250 cr"→"<300 cr" ·
  PEOPLE §0 money-anchor line (already 300–800; floor annotated) · wage table re-verified
  UNCHANGED (already derived from 300–800: casual 8–15 cr/day, docker exit 4–13 wks,
  casual exit 30–100 days) · player.py constants + selftest (pending, above).
- **2026-08-04 — SPEC-CHANGE #3 pending (adoption-blocking, RED): the tanker class.**
  What: split the fuel run out of `freighter_standoff` as a tenth manifest class. Code
  edit pending: `station/traffic.py` MANIFEST — `("freighter_standoff", 4.0, ...)` →
  `("freighter_standoff", 3.7, ...)` plus new row
  `("tanker", 0.3, "standoff", 3, 8, 12.0, 24.0)` (auth 5 souls/stay; 55.0/day total
  preserved). Why: PLC-039/120's checks name a tanker no manifest class provides; SYS-02
  listed 8 classes against the code's 9. Owner-visible: yes.
  **recomputes:** SYS-02 state restated as ten classes (this file) · DLG-04 PA templates
  9→10 classes ×3 = 27→**30**, DLG-04 total 95→**98** · PEOPLE grand dialogue floor
  6,573→**6,544 + ≤32 scarce-voice ceiling** (DLG-06's ceilings leave the floor) ·
  THE-STATION §5–6 same figure · SUR-03 hull union +tanker (this file) · 55/day
  unchanged (the 0.3 came out of freighter_standoff).

*Post-adoption edits to any SYS/SUR/VRB item land here, dated, with reason and
recomputes, or the registry gate fails.*
