# INV-550..559 — WHAT HAPPENS AFTER A REFUSAL (session 4r, agent P2)

**NOT MERGED INTO `canon/INVENTIONS.md` BY THIS AGENT, DELIBERATELY.** Two agents wrote to that
register on the same day and two numbers ended up meaning two different things each (INV-450,
INV-451). The block reserved for this work is **INV-550..559**; `tools/inv_check.py` gates the
merge. Copy these entries in verbatim, in order, at the end of the register.

Owner: `station/enforcement.py`, `godot/scripts/enforcement.gd`,
`godot/scripts/interact.gd::fine/convict`.

---

## INV-550 — A refusal detains one time in five, drawn per event and not per day

**What.** Whether a given refusal ends in detention (LAW-CRIME 2.7 rung 4) or in "move on"
(rung 3) is `consequence._u("detain_on_refusal", npc_id, place, day, nth) < DETAIN_ON_FAIL`,
where `nth` is how many times this person has been stopped at this place today.
**Why.** `DETAIN_ON_FAIL = 0.20` is INV-346 and has existed since P1-G2, but it had only ever
been used as a RATE — inside `day_arrests`, where it prices a station-day of the whole force. A
player meets it exactly once, standing in a doorway, so it has to resolve to a yes or a no for
**this** refusal. Nothing about the number changes; what is new is that it is now drawn.
**Constrained by.** Three things, and they are what stop it being a coin flip in a hat. (1) The
hash is `consequence._u`, the same one every fine amount, every deferral and every discretionary
stop in that module already uses, so the fork sits on one seed line with the rest of the law
layer rather than on a new one. (2) It is keyed on the EVENT — person, place, day, and the stop
count — so reloading a save reproduces the same refusal and walking back in is a fresh draw. A
key without the place and the stop count is one number repeated: measured over the 98 places that
read a card, that control gives **0 of 98**, against **22 of 98 = 0.224** for the real key.
(3) The rate over the register is checked against `DETAIN_ON_FAIL` itself rather than asserted:
0.224 against 0.20 on 98 samples.
**Known limit, and it CYCLES rather than going quiet.** The baked table carries three stops per
place (INV-557's reason) and a player can make a fourth. The engine wraps the index instead of
falling through to "moved on", because a fourth refusal that could never detain is a rule that
switches itself off the moment somebody tests it — which is a worse answer than either branch.
Wrapping reuses the same draws in the same order, so it stays deterministic and holds the
one-in-five over a long session. Baking more rows would push the wrap further out and not remove
it.
**Overturned by.** Any figure for arrests per stop; by anything that says a second refusal at the
same door is treated differently from the first (which would make `nth` a rung rather than an
index).
**Authority 5.** `station/enforcement.py::_detain_draw`, `--selftest` checks 10 and 11 with its
own control.

---

## INV-551 — The responding pair becomes visible at 12 m, or at the last clear metre

**What.** The two officers appear `min(12.0 m, the last clear point of a ray from the player's
chest along the way out)` from the player, on the floor, and walk in a straight line at
1.30 m/s.
**Why.** They have to come from somewhere and the shipped build has no path-finder in GDScript
for a body that is not the player or a scripted commuter. Something has to decide where "coming
from the corridor" starts.
**Constrained by.** **12 m is not a new number**: it is `npc.gd::promote_walker`'s own default
radius, this project's existing answer to *"how far away is somebody who is here with you"* —
the distance inside which a collapsing body is a person who was standing there rather than a
corpse appearing out of the air. The same question, so the same answer. The RAY is what stops the
number being a guess: the officers are placed at the last point of a cast that starts at the
player's chest and ends where the world stops it, so the straight line they then walk has already
been proven clear by the cast that placed them. The speed is `life.gd`'s `walk_speed_ms = 1.30`,
what a commuting resident walks at on this deck, not a second gait.
**Known limit, stated rather than hidden.** The last leg is a straight line and not a route. On a
bay with a single doorway the ray usually places them in the doorway and the walk is honest; in a
room with a partition between the door and the player they will appear on the player's side of
it. Closing that needs `roomnav.py`'s waypoints in the engine, which is `route_walk.py`'s job and
not this one.
**Overturned by.** A GDScript path-finder for non-player bodies; any depiction that fixes how
security enters a room.
**Authority 5.** `godot/scripts/enforcement.gd::APPROACH_MAX_M`, `_spawn`, `_walk_in`.

---

## INV-552 — Arrival is 2.4 m, because that is the distance a thing can be operated at

**What.** The pair has ARRIVED when the horizontal distance from the player is ≤ 2.4 m.
**Why.** A gate needs a moment that is unambiguously "they are here".
**Constrained by.** 2.4 m is `interact.gd::reach_m` and is not re-decided: being close enough to
be handed a citation is the same distance as being close enough to press a console, and a second
constant here would be a second answer to one question. `dialogue.gd` uses its own, wider figure
for a conversation, which is correct for a conversation and wrong for this — a citation is handed
over, not called across a room.
**Overturned by.** Nothing sourced; it is a threshold, and any figure derived from a depicted
stop would replace it.
**Authority 5.** `godot/scripts/enforcement.gd::ARRIVE_M`.

---

## INV-553 — The escort is reported, not walked, and the release is into the corridor

**What.** A detention does not move the player's body to the brig. The chain's legs are reported
one at a time — seizure, escort, booking, hold, court, fine, release — the station clock is
advanced by the routed total, and the player is put back in the corridor outside the place they
were refused from.
**Why.** `consequence.BRIG` is a real place in the register and it is neither on this deck nor in
any streamed cell: teleporting a body into a cell that has not loaded drops it through the world,
and walking it there is 6 km and four decks on a graph the engine cannot yet drive a non-player
body along.
**Constrained by.** Every duration a player reads is the routed one — escort **11.8–15.2 min**
across the six places of the boot deck, hold **0.8 h at 06:00 and 23.8 h at 07:00** because the
Ombuds sit at 08:00, court 1.2 min, total ~19 h — so nothing about the chain is softened, only
the camera. The RELEASE POINT is derived from the same box `hud.gd` will test the player against
on the next frame (place box + `_resolve`'s own 1.5 m of slack + 1 m), ray-verified, and put on
the floor by a second cast: a player escorted to a point that happened to still be inside would
be refused again on the next frame, for ever.
**What would overturn it.** The brig streaming in — at which point the escort becomes a walk and
this entry is replaced rather than amended. That is the right next increment for this subject.
**Authority 5.** `godot/scripts/enforcement.gd::_settle`, `_outside`, `_foot`.

---

## INV-554 — The countdown runs in real seconds, and the compression is printed

**What.** The wait between a refusal and the pair arriving is the routed response time in REAL
seconds. `--arrest-rate=N` divides it; every verdict line prints `rate=xN`.
**Why.** The response time is the most interesting number this subject produces — **0 s in
`docking_bays`, which has a post standing in it, against 227 s in `lowg_bays` from customs
north** — and it is only interesting if a player experiences it. Compressing it by default would
delete LAW-CRIME 2.6's contrast, which is the layer's whole dramatic geometry.
**Constrained by.** The station clock is not used for it, and that is a decision: `life.gd` runs
at 0.017 station-hours per real second (61x), so a 227 s turn-out on the station clock would land
in under four seconds and a player would never learn that the outer ring is a place nobody comes
to. The gate compresses (x40) because a gate that took twelve minutes would not be run.
**Overturned by.** A design ruling that the whole simulation runs on compressed time, in which
case this rides that rate instead of real seconds.
**Authority 5.** `godot/scripts/enforcement.gd::rate`, `LEG_DWELL_S`.

---

## INV-555 — A refusal at a reader is `id_check_fail`, and no new offence was minted for it

**What.** The offence a refused player is stopped for is `consequence.OFFENCES`' existing
`id_check_fail` (grade 1, escalation rung 2), and the non-detention disposal is the existing
`move_on` (grade 0, rung 3).
**Why.** It looks like it wants a new row — "trespass", "entering a restricted area" — and it
does not.
**Constrained by.** The table's own source sentence for `id_check_fail` is *"a card that does not
read. 2.7 rung 2 is the commonest interaction and most of its failures end at rung 3"*, which is
exactly what a refusal at a boundary IS: the card was read and it did not admit you. Minting a
second offence would put two rows in one table describing one event, and the fine ladder would
then have two answers for it. The grade-1 fine is **8–10 cr, one day of casual labour**
(INV-347), which is the right order for the commonest interaction on the station: a citation, not
a catastrophe.
**Overturned by.** Any depiction of a distinct charge for being somewhere you are not cleared
for.
**Authority 5.** `station/enforcement.py::REFUSAL_OFFENCE`, `MOVED_ON_OFFENCE`.

---

## INV-556 — The consequence table is baked per place and per hour, and only the hold moves

**What.** `station/generated/scene/enforcement.json` carries, per place, the response and its
post, the two officers, the fork, the four fixed legs, and **24 values each of hold and total**,
indexed by the hour of arrest.
**Why.** The engine must hold no copy of the rule (hard rule 4), and a rule evaluated at bake
time has to be evaluated at every input the runtime can present. The clock is the only input the
player controls.
**Constrained by.** Measured rather than assumed, and ASSERTED at bake time: for every place and
every one of the 24 hours, `respond + escort + booking + hold[h] + court + release` must equal
the total `consequence.arrest` reports to within 0.2 s, or the bake raises. If any leg but the
hold moved with the clock, indexing the hold alone would be a fiction and the totals would be
wrong. The shape is checked as well as the sum — a table of 24 identical numbers would pass the
sum and mean the hour was inert, so the selftest requires a spread of more than an hour and gets
**0.8 h at 06:00 against 23.8 h at 07:00**, which is the 08:00 Ombuds sitting.
**Overturned by.** A second clock-dependent leg — a night court, a shift change in the escort —
at which point the table gains a second indexed row rather than losing the rule.
**Authority 5.** `station/enforcement.py::place_row`.

---

## INV-557 — The conviction ladder is baked for every rung, not just the one the card reads

**What.** `detention.ladder_by_tier` holds three successive disposals from each of the six rungs.
**Why.** `--tier=N` forces the card in the engine (`main.gd::_check_gate`'s own control, on the
grounds that it is the identicard that changed and not the reader), and `consequence._dispose`
answers differently at every rung: EA citizenship cannot be withdrawn by an Ombuds at all, the
floor rung has nothing left to take and the next disposal is transfer off-station, an accredited
card is immunity and the file dies. A build that showed one of those for all six would be a rule
with its interesting half filed off.

**AND THE HEADLINE THIS ENTRY WAS FIRST WRITTEN WITH WAS WRONG, WHICH IS WORTH KEEPING.** The
first draft said "a transit visa is withdrawn on the second ordinary conviction", and the
selftest that checked it PASSED — because the shipped player stands on the floor rung, where
`REVOCABLE` is `None` and the check took its other branch. **It could not have failed for the
case it was named after.** Asked at all six rungs, the ladder revokes at NONE of them, and the
cause is one line: `Record.ordinary()` counts grade-2 convictions and `id_check_fail` is grade 1.

That is the right answer and it is now asserted as such. INV-347 prices grade 1 at one day of
casual labour — a citation — and a station that withdrew a visa for two citations would have no
middle to its own escalation ladder. **A refusal at a door, on its own, never costs you your
standing.** It costs a day's wages, a night in the brig and a line on the card. Revocation needs a
grade-2 conviction, which is a different verb (carrying, petty theft, expired status) and another
session's work. The selftest carries a POSITIVE CONTROL running the same `_dispose` at the same
rung one grade heavier, so "it never revokes" cannot quietly become "the machinery is absent".
**Constrained by.** It calls `consequence._dispose` — the module's own disposal rule — with a
`Record` accumulating convictions, rather than restating the rule. The fine does not move with
the rung (it is per offence and per person), so it is carried across from the ladder that was
actually routed.
**Overturned by.** Nothing; it is a projection of an existing rule onto an existing axis.
**Authority 5.** `station/enforcement.py::place_row`, `by_tier`.

---

## INV-558 — A fine is a transfer to the court in the ledger a drink moves through

**What.** `interact.gd::fine()` debits the purse, credits `law_courts`' till, appends a row to
`sales` naming the offence, and writes the document. An unpayable fine is not an error: the debt
is recorded as outstanding and the player walks out with it.
**Why.** The money has to be real or the sentence is a caption.
**Constrained by.** It is `consequence._post_fine`'s four numbers and no fifth — that function's
own comment says *"NOT a new wallet and not a new file: `economy.Ledger.till` and `.sales` and
`.purses` are the existing three"*. The rounding follows `_verb_serve`'s, which is load-bearing
rather than tidy: `economy.buy` totals at 2 dp and a purse keeps millicredits, and an `int()`
truncation there once ate 0.20 cr of a 0.80 cr drink. The "walks out with the debt" reading is
LAW-CRIME 4.3's Jinxo precedent read economically — the brig is a remand facility and not a
debtors' prison — which `consequence.arrest` already applies on the Python side.
**Overturned by.** Any depiction of what B5 does about an unpaid Ombuds fine.
**Authority 5.** `godot/scripts/interact.gd::fine`, `_record_fine`.

**AND IT GAVE ITS OWN GATE AN EXPIRY DATE, which is worth recording because the money being real
is exactly what caused it.** Five verification runs took the shipped purse from **420.50 to
372.40 cr** — five detentions at 9.62 cr, each one correct. At that rate the gate stops passing
after about thirty-eight runs, when the purse cannot cover the fine and `paid` becomes
`OUTSTANDING`: a gate that spends its own subject's money is a gate with a countdown on it.
`enforcement.py::_run` now copies the ledger into a temp directory and passes
`--ledger=<copy>` — which `interact.gd::ledger_path` already honoured — and then reads the copy
back off disk, so the verdict rests on **a file having changed** rather than on the runtime saying
it did.

---

## INV-559 — The conviction is written into the purse, because that is what survives

**What.** `interact.gd::convict()` appends the offence to `purses[<player>].record.convictions`,
increments `custody_events`, and on a revocation writes `visa_revoked`, `revoked_from`, a dated
note, and the new rung onto the body.
**Why.** A consequence that does not survive the process is a mood.
**Constrained by.** That is `player.py::state()`'s own sentence, and the key already exists:
`state()` writes `record` when there is one and `restore()` reads it back, so the engine is
filling a channel the simulation already opened rather than inventing a save format. The shape is
`consequence.Record.state()`'s, field for field, so a Python session that loads the purse after
the engine wrote it gets a `Record` and not a dictionary of surprises.
**Overturned by.** Nothing; it is the existing serialisation used from the other end.
**Authority 5.** `godot/scripts/interact.gd::convict`, `_record`, `_put_record`.
