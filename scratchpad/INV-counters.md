# INV entries for session 4r — the counters. Block INV-560..569.

**DO NOT EDIT `canon/INVENTIONS.md` FROM HERE — these are for the integrator to append.**
Written in that file's format so they can be moved across verbatim.

**All five are already cited by number in `station/economy.py`** — at lines 469/480 (560),
480/… (561), 644 (562), 1321 (563) and 678 (564) — so `tools/inv_check.py` reports them as
DANGLING until these entries are appended. That gate was **already red before this session**
with twelve dangling citations, including three other agents' pending blocks
(INV-530/531/533/534 in `vista.py`, INV-540/541 in `drum_ground.py`, INV-550 in
`enforcement.py`) and four long-standing ones (INV-074, 078, 140, 141, 232). Appending this
file's five entries clears exactly the INV-56x rows and nothing else.

Block used: **INV-560, 561, 562, 563, 564** — 565..569 unused and free.

---

## INV-560 — A station sells SERVICES as well as goods, and their prices are ladder rows verbatim

**What.** `economy.SERVICES` is four things a counter takes money for that are not units of
stock: `passage home` (300.00 cr), `a bunk for the night` (1.00), `a hot meal` (0.00, issued)
and `a stake at the table` (1.00). Each is attached to a place by a **register function** —
`ship_departure`, `informal_residence`, `catering`, `gambling` — never by a place key, so the
list of places that sell passage is derived from `directory.py` exactly as `Good.sold_by` is.

**Why the whole economy was a shop.** `GOODS` is 33 lines of spoo and bearings and every one
of them is a thing you carry away, so `vendors()` was 13 places and the 28 places declaring a
`serve`-verb prop resolved to **9** that could take a credit. On the deck the shipped build
actually boots into (`blue_0_0`) the number was **ZERO**: its one `serve` prop is
`docking_bays__prop_bay_control_booth` and `docking_bays` declares no selling function. Four
of the ladder's own eight rows — command quarters, transient room, dosshouse bunk, passage
home — are not goods at all, so the file could PRINT four prices nobody could pay.

**Why no multipliers.** `SUPPLY_MULT` exists because a good crosses hyperspace, and
`VENUE_MULT` because it pays rent on a shopfront. A berth on a departing hull does neither:
the ladder's 300–800 cr already *is* the fare. So a service price is the ladder row and
nothing is applied to it.

**Why the FLOOR of a band and not a draw inside it.** The first version drew inside the band
the way `price()` does for goods and quoted **618.69 cr** for passage. That number was wrong
for a reason worth keeping: **the project had already decided this price.** `player.py:194`
carries `PASSAGE_HOME_CR = 300.0` — *"a berth on an outbound transport (band floor)"*,
SPEC-CHANGE #1, owner-approved — and `CREDIT_SKEW` is *solved* against it so exactly 1% of
arrivals land under the line, which is the mechanism that produces Downbelow. A desk quoting
618.69 would have refused a player `Player.can_afford_passage()` had just cleared. So the rule
for every row: **a ladder band is the spread of a market and a counter quotes one price, the
cheapest thing the counter has** — a berth in economy, a bunk on the floor, the minimum stake.
`economy.price_check()` asserts identity rather than membership, and `_selftest` asserts
`price("passage home", "docking_bays") == player.PASSAGE_HOME_CR`, with the discarded draw
kept live as the negative control (it fires at +318.69 cr).

**A hot meal at 0.00 cr is a price, not a hole.** `mess_hall` is `("catering", "crew_social")`
— an EarthForce crew mess issues rather than sells. The ladder's `squat` row exists for exactly
this: *"and it is why people are there"*, 0.0, so that free is a price and not a missing entry.

**The stake is the one derived step.** `gambling` has no ladder row, so the minimum stake takes
`meal_cart`'s floor with one stated reason: a table whose minimum excludes the dockers and
lurkers `populace.occupancy` puts in that room is a table with nobody at it, and `meal_cart` is
the smallest discretionary sum the ladder carries. Authority 5.

**Overturned by.** any stated fare, tariff, rent receipt or table minimum from the show or a
production document. Each would replace one row and nothing else — the table is data.

---

## INV-561 — A service's stock is a real count of the thing that limits it, and passage home is berths off the manifest

**What.** `economy.outbound_berths(day)` returns **(free berths, hulls, seats)** sailing during
a station day. Day 0: **22 passenger hulls, 2,108 seats, 445 free**. Day 1: 606 free. Day 2:
1,093.

**How it is derived, with nothing added to the manifest.** A hull leaves when its stay is up,
and `traffic.arrivals()` already carries `hour` and `stay_h`, so the departure is arithmetic
rather than a second table. Its SEATS are its class's own capacity-band top
(`traffic.MANIFEST` column 5 — a `transport` is 86, a `liner` 800), and its outbound LOAD is
what it brought, which is TRAFFIC-AND-CUSTOMS §5.3's steady state: the transient population is
resupplied entirely by arrivals, so over a day out equals in. **Free = capacity − load.** A
hull that came in full leaves full, and on a day when they all did, the shelf is honestly
empty and the desk says so.

**Why this shape.** It is `consignments()`'s own rule applied to people: *"a delivery is a real
container off a real ship"*. A berth invented from a number would be the one thing that rule
exists against.

**The passenger classes are derived too.** `pax_classes()` reads `traffic.MANIFEST` and takes
every row that is not in `CREW_STAYS_ABOARD`, not in `FREIGHT_CLASSES`, and whose soul band
tops out above zero. A class that carries nobody cannot sell a seat.

**Overturned by.** any stated outbound load factor, or a manifest that carries departures in
their own right instead of implying them from `stay_h`. The second would be strictly better
and is a `traffic.py` change, not this one.

---

## INV-562 — A service is sold across ONE counter, and one counter is `COUNTER_M2`

**What.** Where no physical count exists, a service's daily demand is
`counter_covers(place)` — `populace.occupancy` summed over the clock across
`min(floor_m2(place), COUNTER_M2)` rather than across the place's whole footprint.
Measured: `downbelow` **84**/day, `downbelow_arch` and `mess_hall` **106**, `casino` **165**.

**Why, and it is a lesson this file already paid for once.** `economy.py`'s own comment says
*"A COUNTER IS NOT A DISTRICT, and the first version of this file forgot it"* — occupancy over
Downbelow's 654,370 m² footprint gave it 235,572 retail transactions a day. A bunk desk has the
identical shape and would have inherited the identical defect:
`daily_covers("downbelow_arch")` is **4,714**, a district's worth of beds behind one desk.

**No new constant.** `COUNTER_M2 = 225.0` is already solved in this file — `bar_unnamed`'s own
register footprint, the authority-1 bar, one counter — and `MAX_RETAIL_M2` is 44 of them, from
PLACES §0.3's stated 44 Zocalo stalls. A service reuses the smaller figure because it is one
desk and not forty-four.

**Overturned by.** a stated bunk count for any Downbelow squat, or a stated cover count for the
mess. Either would replace the derivation for its own row and leave the rest.

---

## INV-563 — A service is replenished by the day, not by a ship

**What.** `economy._renew_services(led, day)` tops each service line up by one day's demand and
caps it at `RESTOCK_DAYS` (3) of it — the same depth `opening_stock` gives a goods line — and
it runs inside `deliver()`.

**Why it is the goods rule with one word changed.** A goods shelf stands three days deep and is
topped up by what it sold, off a real crate off a real hull. A service shelf stands three days
deep and is topped up by what it sold, because **tomorrow is another night and another ship**.
That is the only difference between the two nouns anywhere in the module, and stating it once
here is what stops it becoming a special case with its own rules. The fourteen-day drift check
did not have to be widened to admit it: 55,757 → 55,822 units, **×1.001**.

**And it is deliberately skipped when `deliver(only=...)` names its consignments**, because that
call exists so `dockwork.py` can prove the crates the player's own gang worked are the crates
that arrived. Renewing berths inside it would put units on a shelf no gang moved.

**Overturned by.** a service whose supply genuinely is a shipment — a bonded line, a licensed
quota — which would want the goods path instead and already has it.

---

## INV-564 — `SELLING_FUNCTIONS` is the union; `GOODS_FUNCTIONS` is what carries stock

**What.** `GOODS_FUNCTIONS` is the old five (`commerce, retail, hospitality, food_service,
black_market`) and `vendors()` reads it. `SELLING_FUNCTIONS` is now
`GOODS_FUNCTIONS | SERVICE_FUNCTIONS`, and it is the union because
`consequence.sells_to` asks it exactly one question — *is this place a counter at all* — and a
desk that takes 300 credits for a berth is a counter by any reading of that word.

**Why the split is load-bearing rather than tidy.** `vendors()` is read by `incident.py`
(*"the thirteen counters that hold stock"*), by `consequence.counters_for` and by
`consignments()`. Widening it would have moved every goods number in the project. Measured
A/B against `git show HEAD:station/economy.py`, run in one process: over fourteen days of real
manifests the opening and closing GOODS stock of all thirteen vendors is **identical**, and the
only tills that move differently are the five places that gained a service. `demand_of()` is
what buys that — a mixed counter (`downbelow` gained a bunk beside its black-market lines)
spreads its `daily_covers` across its **goods** lines exactly as before, instead of dividing
by one line more.

**Overturned by.** nothing factual — this is a code-shape decision, recorded because the two
names are one character apart in use and a future edit that reaches for the wrong one will
silently move thirteen counters' worth of arithmetic.

---

## Unused in this block

**INV-565 … INV-569** — reserved to session 4r and not used. Free.
