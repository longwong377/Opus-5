export const meta = {
  name: 'game-4t-round5',
  description: 'Round 5 for P1-G2 and P1-G3: a postcondition instead of a mid-function print, a savegame a player can reach, and a closed detail vocabulary so a prose clause cannot count as a world state',
  whenToUse: 'Continuation after round 4 reproduced both player claims but both stopped at robustness 3',
  phases: [
    { title: 'Build', detail: 'answer the round-4 findings; do not re-do what the verifier could not break' },
    { title: 'Judge', detail: 'a fresh hostile verifier re-arms the exact break that passed last round' },
    { title: 'Synthesis', detail: 'converged, or CAPPED in writing per AAA-STANDARD' },
  ],
}

// ---------------------------------------------------------------------------
// ROUND 5, AND THE STOPPING RULE IS NOW LIVE.
//
// docs/AAA-STANDARD.md's rule is three rounds, then CAPPED IN WRITING: "a
// sufficiently harsh critic always finds something, so 'keep going until it's
// AAA' without a defined bar never terminates and one item eats unbounded
// budget." Both items have had FOUR build rounds. This round is justified on
// merit rather than on instruction, because both moved materially each time --
// round 2 shipped a green gate over a broken player experience, round 4 had the
// player claim independently reproduced -- and because both remaining defects
// are specific and buildable rather than matters of taste.
//
// IF THIS ROUND DOES NOT CLEAR, THE ANSWER IS A WRITTEN CAP, NOT A ROUND SIX.
// Each agent is told to produce the cap text itself if it cannot close its
// item, so the stop is honest rather than a session running out of patience.
// ---------------------------------------------------------------------------

const BRANCH = 'claude/aaa-game-development-j6y2ml'
const MAX_ROUNDS = 1

const ENV = `
ENVIRONMENT. Verify, do not assume:
  * Godot 4.4 double: /home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
  * Vulkan: /usr/share/vulkan/icd.d/lvp_icd.json. "OpenGL 3 Compatibility" in a render log is a LIE
    that exits 0 with a PNG -- destroy the artefact and fix the environment.
  * numpy/pillow/pyyaml installed; station/generated/hull.obj built.
If missing: pip install -r requirements.txt ; bash tools/build_godot.sh ;
apt-get update -qq && apt-get install -y -qq mesa-vulkan-drivers ; cd station && python3 generate_hull.py

**ANOTHER WORKFLOW MAY STILL BE LIVE** (wf-aaa-4t.js) owning economy.py, consequence.py, player.py,
dialogue.py, broadcast.py, boot.py, stream.gd, bake_station.py, bootstrap.py, collision.py, deck.py,
npc/*, export_scene.py, observation.py, drum_*.py, spec_harness/{dlg,vrb,ply}.py. Do not edit those;
write needed changes to \`scratchpad/PATCHES-4t-<key>.md\`.

**CI NOW HAS AN ENGINE.** The main agent added a \`sgodot\` step running \`tools/build_godot.sh\`
(the binary is vendored, seconds to unpack) after both round-4 verifiers independently found that
*"none of it runs in CI"*. So a CI step you add for an engine gate can now actually execute. Add
one for your item -- \`continue-on-error: true\` plus a line in the roll-up, matching the file's
existing shape.`

const RULES = `
RULES:
1. **\`git worktree\` off a NAMED commit you chose**, not live HEAD -- other agents push constantly.
2. **PUSH, early and often**: \`git fetch origin ${BRANCH} && git rebase origin/${BRANCH} &&
   git push origin HEAD:${BRANCH}\`. Non-fast-forward rejection is NORMAL; retry. Stage BY NAME,
   **never \`git add -A\`**. A commit in a container that rolls back never happened.
3. **Do NOT run** \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\`, \`budget.py\`.
4. **Hard rule 1**: numbers trace to \`canon/00-MASTER.md\` or get a \`## INV-<n>\` entry. Leave a
   gap of 30 above the highest; INV-1091 is already taken.
5. **ASSERT ON A POSTCONDITION, NEVER ON A TRACE.** This is round 4's lesson and it is why you are
   here again.
6. **IF YOU CANNOT CLOSE IT, WRITE THE CAP** -- see below. Do not fake a pass.`

const CAP = `
**IF YOU CANNOT CLOSE THIS, YOUR DELIVERABLE IS THE CAP, NOT A PASS.**
\`docs/AAA-STANDARD.md\`'s stopping rule is three rounds and then CAPPED IN WRITING, and this item
has had four. If at the end of your round the acceptance is still unmet, write
\`scratchpad/CAP-4t-<key>.md\` containing: what is genuinely done and gated; what is NOT, stated as
the specific failing behaviour rather than as a score; the cheapest known fix and who would own it;
and what evidence would reopen it. Then return \`ok: true\` with that path in \`notes\`. A written
cap is a legitimate, valuable outcome. A pass claimed on a gate you weakened is not, and every
verifier here runs \`git diff\` looking for exactly that.`

const ITEMS = [
  {
    key: 'g2_progression',
    owns: 'station/enforcement.py, godot/scripts/main.gd, godot/scripts/player.gd, godot/scripts/interact.gd, godot/scripts/enforcement.gd, .github/workflows/validate.yml',
    why: `**ROUND 4 GOT THE PLAYER CLAIM REPRODUCED BY A HOSTILE VERIFIER.** The rung is no longer a
saveable fact; it is re-derived. That is real and you should not touch it. **Two things stop it
being AAA, and the first is that your new gate cannot see the defect it was written for.**

**(1) \`_prog_save\` ASSERTS ON A TRACE, NOT A POSTCONDITION.** Its only behavioural assertion reads
\`player: rung N NAME RE-DERIVED after load\` -- a print emitted **part way through**
\`player.gd::load_state\` -- and its only artefact assertion is the ABSENCE of the literal key
\`"tier"\` from the savegame. Neither is a statement about the body's FINAL rung. The verifier
appended two lines to the tail of \`load_state\` writing \`tier = tier_stored\` -- a second writer
arriving *after* the print -- and got \`ARREST-PROG PASS\`, exit 0, all six savegame rows green,
while its instrumented probe showed \`VERIFIER PROBE: after load_state returns, tier=2 transit\` on
a card the ledger records as revoked. **That is verbatim the round-3 harm with a green gate over
it.** Your commit's defence was "there is now exactly one writer of \`tier\` in this file" -- but
nothing gates that invariant, and it is **already false repo-wide**:
\`interact.gd:656 _player.tier = tier_after\`, \`enforcement.gd:1415 _player.set("tier", t)\`,
\`main.gd:2104 body.set("tier", forced)\`. A fourth writer is not hypothetical.

**(2) THE SAVEGAME IS UNREACHABLE BY A PLAYER**, which is half of the acceptance sentence.
\`main.gd:281 const MENU_SLOT := "auto"\` is READ at :315 (to enable CONTINUE) and :339 (to restore)
and is **WRITTEN BY NOTHING**. \`save_to()\` has exactly two callers in the repository --
\`main.gd::_save_gate\` (slot "gate", a CI flag) and \`journal.gd:720\` (slot "journal", another CI
flag). Driven headlessly, the front door says \`continue_game CONTINUE unavailable -- No saved
station.\` while gate.json sits on disk. **"Quit and come back by loading a savegame" is gated
machinery with no shipped caller -- this project's signature defect, inside the acceptance
sentence.** \`PATCHES-4t-g2.md\` disclosed the contraband reach gap honestly and did not mention
this one.`,
    fix: `THE VERIFIER NAMED BOTH FIXES:

1. **Replace the trace assertion with a POSTCONDITION on the final state.** In
   \`godot/scripts/main.gd::_save_gate\`, after \`load_from("gate")\` and the settle frames, print a
   line the gate can parse: \`SAVE rung=%d(%s) derived=%d(%s)\` -- the first pair is
   \`body.tier\`/\`body.tier_name\` read **after everything has finished loading**, the second is
   \`body.rung_of(body._purse_doc)\`, the rung the RESTORED ledger implies. Then have
   \`station/enforcement.py::_prog_save\` assert on **that** line (the two equal to each other, and
   equal to 0) instead of on \`_RESTORED_RE\`. A mid-function print is a claim about an instant;
   this is a claim about the state the frame ends in, so **any later writer of \`tier\` -- the exact
   break that passes today -- makes it red.** Add a \`--player-late-write\` control that arms such a
   writer, and show the new row going red under it.
   (This is NOT the perturbation round-trip you correctly declined last round. It is an agreement
   check between the settled field and the restored document.)
2. **One line so CONTINUE can ever be true**: call \`save_to(MENU_SLOT)\` from somewhere a player
   reaches -- an autosave on cell hand-off, or a pause-menu SAVE. **Until then, strike the savegame
   half from your claim rather than gate it.** Claiming reach you did not build is the thing that
   costs a round here.
3. \`senforcement\` in CI still runs only \`--selftest\` and \`--bake\`. CI now has an engine (see
   ENV) -- add the engine half as its own step.`,
    acceptance: `**A late writer of \`tier\` must turn the gate RED, and CONTINUE must be reachable
or explicitly struck from the claim.** Show: the postcondition line from a real engine launch; the
\`--player-late-write\` control making it fail; and either a player-reachable path that writes
MENU_SLOT, or a claim that no longer mentions savegames.`,
    gate: '`python3 station/enforcement.py --ensure --gate --progression`',
  },
  {
    key: 'g3_incidents',
    owns: 'station/incident.py, station/friction.py, station/journal.py, godot/scripts/journal.gd, .github/workflows/validate.yml',
    why: `**ROUND 4's LEDGER ROUND TRIP IS REAL AND THE VERIFIER REPRODUCED IT.** Do not re-do it.
**But the flavour hole was MOVED ONE FIELD DOWN, NOT CLOSED, and a live headline number is 288/290
made of it.**

\`World.delta_fingerprint()\` (\`station/incident.py:2380\`) constrains the **kind** of a fact to
\`MEANINGFUL\` (2321) and leaves the **detail** an unconstrained free-text string. \`World.fact()\`
(2351) validates \`kind\` and does nothing to \`detail\`. So two stances producing an identical world
consequence -- same kind, same subject, same amount -- that differ by **one prose clause inside the
detail** still hash apart, and every DIFFER assertion in the module counts them as distinct worlds.
The verifier armed exactly that on INC-LINER and got \`30 of 30\` with \`stance_table\` check
\`True\`. **The shipped sixth control \`flavour_control\`/\`_flavour_collapsed\` (4489) only arms the
\`news\`-kind version, so it cannot see its own successor.**

**And this is not hypothetical.** The absence gate prints *"differ in MEANINGFUL world deltas ...
and not in a log string"* and reports \`290 MEANINGFUL delta(s) ... ONLY because you were not
there, 298 ONLY because you were\`. **At the (kind, subject) level those numbers are 2 and 7.**
288 of 290 and 288 of 298 are the same \`card\` row on the same named person, differing only in the
words \`flagged, secondary inspection\` against \`refused, docketed\`. Those *are* real different
outcomes -- but they are encoded as prose, so the gate cannot tell them from a rewrite. **The
headline is inflated about 40x by exactly the quantity round 4 said it had excluded.**

**Also:** \`godot/scripts/journal.gd::move_standing\` has **zero callers in the engine**. The engine
check asserts the runtime agrees there are 13 ledgers; nothing in the runtime ever moves one. The
acceptance's own sentence -- *"a delta that only exists inside the incident module's own dict is
weather"* -- applies one level out. And \`gate()\` never calls \`ledger_gate\`, so the marquee half
of round 4 is not in CI at all.`,
    fix: `1. **CLOSE THE DETAIL HOLE AT THE SOURCE.** Give \`World.fact()\` a **closed vocabulary**
   for the detail of a MEANINGFUL kind -- \`card\` becomes
   \`("card", subject, "refused"|"flagged"|"annotated"|"revoked")\`, and the same treatment for the
   other MEANINGFUL kinds -- and **raise on anything outside it**. Prose moves to a separate,
   un-fingerprinted display field. Then re-run the absence gate and **report the honest number**,
   which will be far smaller than 290 and is the one worth having. A headline that shrinks because
   the measurement got honest is a result, not a regression -- say so plainly in the commit.
2. **Make the control see its own successor**: extend \`flavour_control\`/\`_flavour_collapsed\` to
   arm the DETAIL version on a MEANINGFUL kind, not just the \`news\` kind.
3. **Give \`journal.gd::move_standing\` a caller on the shipped path**, or state in writing why the
   engine does not need one.
4. **Put \`ledger_gate\` in \`gate()\`** and add the CI step. CI now has an engine (see ENV).`,
    acceptance: `**The honest absence number, and a control that catches a prose-only difference.**
Report the (kind, subject, detail)-level delta count under the closed vocabulary, state plainly how
far it fell from 290, and show the extended control turning the gate red when two stances differ
only in wording. Plus: \`move_standing\` called from the shipped path or a written exemption.`,
    gate: '`python3 station/incident.py --accept`',
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  required: ['key', 'ok'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean' },
    capped: { type: 'boolean', description: 'true if you wrote scratchpad/CAP-4t-<key>.md instead of closing it' },
    gate_cmd: { type: 'string' },
    before_result: { type: 'string' },
    after_result: { type: 'string' },
    negative_control: { type: 'string', description: 'the break that passed last round -- show it failing now' },
    player_can_now: { type: 'string', description: 'one honest sentence. Claim no reach you did not build.' },
    changed: { type: 'string' },
    inv_entries: { type: 'string' },
    pushed: { type: 'string' },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['is_aaa', 'score'],
  properties: {
    why: { type: 'string' },
    is_aaa: { type: 'boolean', description: 'accept in a shipped AAA game. Default NO.' },
    score: { type: 'integer', minimum: 0, maximum: 5 },
    ran_it: { type: 'string' },
    gate_can_fail: { type: 'boolean', description: 'did the SPECIFIC break that passed last round now turn it red, when YOU armed it' },
    player_claim_true: { type: 'boolean' },
    cap_is_honest: { type: 'boolean', description: 'if the builder capped: does the cap describe the real remaining failure' },
    worst_defect: { type: 'string' },
    what_would_fix_it: { type: 'string' },
  },
}

function buildPrompt(item) {
  return `You are a BUILD agent on the Babylon 5 station simulation at /home/user/Opus-5, branch \`${BRANCH}\`.

READ FIRST: /home/user/Opus-5/CLAUDE.md · docs/THE-GAME.md (P1/G0, the design) ·
docs/AAA-STANDARD.md (the bar AND the stopping rule).

YOUR ITEM: **${item.key}** — ROUND 5. A hostile verifier has already reproduced your player claim
once; this round is about the two defects it found underneath it.
YOU OWN, AND ONLY: ${item.owns}

${item.why}

${item.fix}
${ENV}
${RULES}
${CAP}

ACCEPTANCE:
${item.acceptance}

1. **Measure BEFORE** with \`${item.gate}\`, verbatim. Assert both runs produced output — a diff of
   two FAILED runs is not a pass.
2. **Fix at the rule, not the entry.** Both findings are a check that constrains one field and
   leaves the neighbouring one open.
3. **Arm the exact break that passed last round, yourself, and show it now going red.** That is
   your negative control and the verifier will re-arm it.
4. **Measure AFTER.**
5. **\`player_can_now\` in one honest sentence, claiming no reach you did not build.**

Return the structured object.`
}

function judgePrompt(item, built) {
  return `You are a HOSTILE VERIFIER on a Babylon 5 station simulation at /home/user/Opus-5. You did not
build any of this. Two previous verifiers each caught this item shipping a green gate over a broken
player experience. Assume a third instance and go looking.

THE CLAIM. The builder says it fixed **${item.key}**${built.capped ? ' — OR it CAPPED the item, see below' : ''}:
    ${built.gate_cmd || item.gate}
BEFORE: ${String(built.before_result || '-').slice(0, 700)}
AFTER:  ${String(built.after_result || '-').slice(0, 700)}
Changed: ${String(built.changed || '-').slice(0, 900)}
Negative control it claims: ${String(built.negative_control || '-').slice(0, 700)}
Player claim: "${String(built.player_can_now || '-').slice(0, 400)}"
${built.capped ? `\n**IT CAPPED THE ITEM.** Read \`scratchpad/CAP-4t-${item.key}.md\`. Your job changes: judge whether the cap is HONEST — does it describe the real remaining failure in behavioural terms, or does it minimise it? Set \`cap_is_honest\`. A truthful cap is a legitimate outcome and you should say so; a cap that understates what is broken is worse than no cap. You must still run the gate.\n` : ''}
ACCEPTANCE:
${item.acceptance}

1. **YOUR CHECKOUT IS PROBABLY STALE** — agents push continuously and previous verifiers found the
   main checkout 48 commits behind. \`git fetch\` and make your own \`git worktree\` at origin's tip
   BEFORE concluding anything is missing. A stale checkout is not a finding about the work.

2. **RUN THE GATE YOURSELF**; put the output in \`ran_it\`. (Not \`deck.py --sweep\`,
   \`rooms.py --footprint\`, \`walkable.py\`, \`budget.py\`.)

3. **RE-ARM THE EXACT BREAK THAT PASSED LAST ROUND. This is the whole job.**
${item.key === 'g2_progression'
    ? '   Append a late writer of `tier` to the TAIL of `player.gd::load_state` (after the RE-DERIVED print) and check the gate now goes RED. Last round that break produced `ARREST-PROG PASS`, exit 0, six green rows, on a card the ledger records as revoked. Then check whether a PLAYER can reach a savegame at all: `main.gd:281 MENU_SLOT` was read at :315 and :339 and written by nothing, and the front door said `CONTINUE unavailable -- No saved station.`'
    : '   Make two stances differ ONLY by a prose clause inside a MEANINGFUL fact\'s `detail` — the verifier before you armed this on INC-LINER and got a false `30 of 30`. Check it now collapses. Then recompute the absence delta count at the (kind, subject) level yourself: last round the printed 290 was really 2, inflated ~40x by prose. Report the number YOU measure.'}
   Set \`gate_can_fail\` from what YOU observed, not from the builder's control.

4. **CHECK NOTHING WAS WEAKENED.** \`git diff\`. A loosened floor, tolerance, assertion or spec row
   is a finding. Note: a headline number that FELL because the measurement got honest is the
   opposite of a weakening — credit it.

5. **JUDGE.** Robustness per \`docs/AAA-STANDARD.md\`: 4 is "handles the cases it will actually
   meet, fails legibly, and its failure is gated"; 3 is "works on the happy path". **Default to NO.**

6. **Worst remaining defect + concrete fix**, naming a file or parameter. Source: \`${item.owns}\`.

Every claim cites the command you ran or the line you read. You may not be agreeable.`
}

const results = await pipeline(
  ITEMS,
  async (item) => {
    const rounds = []
    for (let r = 1; r <= MAX_ROUNDS; r++) {
      const built = await agent(buildPrompt(item), {
        label: `build:${item.key}:r5`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high',
      })
      if (!built || !built.ok) {
        rounds.push({ built, verdict: null, converged: false })
        log(`${item.key} r5: build produced nothing judgeable`)
        break
      }
      const verdict = await agent(judgePrompt(item, built), {
        label: `judge:${item.key}:r5`, phase: 'Judge', schema: VERDICT_SCHEMA, effort: 'high',
      })
      const correct = !!verdict && verdict.gate_can_fail === true && verdict.player_claim_true === true
      const converged = !!verdict && verdict.is_aaa === true && correct
      rounds.push({ built, verdict, correct, converged })
      log(`${item.key} r5: ${built.capped ? 'CAPPED — ' : ''}gate_can_fail ${verdict ? verdict.gate_can_fail : '?'}, `
        + `player_claim_true ${verdict ? verdict.player_claim_true : '?'}, robustness ${verdict ? verdict.score : '?'}, `
        + `AAA ${verdict ? verdict.is_aaa : '?'}${built.capped ? `, cap honest ${verdict ? verdict.cap_is_honest : '?'}` : ''}`)
    }
    return { key: item.key, rounds }
  },
)

phase('Synthesis')
const done = results.filter(Boolean)
const converged = done.filter(r => r.rounds.some(x => x.converged))
const capped = done.filter(r => r.rounds.some(x => x.built && x.built.capped))
log(`${converged.length} of ${done.length} converged; ${capped.length} CAPPED in writing per AAA-STANDARD`)

return {
  summary: `${converged.length}/${done.length} converged, ${capped.length} capped`,
  converged: converged.map(r => r.key),
  capped: capped.map(r => r.key),
  table: done.map(r => {
    const last = r.rounds[r.rounds.length - 1] || {}
    const v = last.verdict || {}, b = last.built || {}
    return {
      key: r.key,
      capped: !!b.capped,
      cap_is_honest: v.cap_is_honest === undefined ? null : v.cap_is_honest,
      claim: String(b.player_can_now || '-').slice(0, 400),
      reproduced: v.player_claim_true === undefined ? null : v.player_claim_true,
      gate_can_fail: v.gate_can_fail === undefined ? null : v.gate_can_fail,
      robustness: v.score === undefined ? null : v.score,
      is_aaa: !!v.is_aaa,
      worst_defect: v.worst_defect || '-',
      what_would_fix_it: v.what_would_fix_it || '-',
      pushed: b.pushed || '-',
    }
  }),
}
