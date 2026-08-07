export const meta = {
  name: 'game-4t-round3',
  description: 'Round 3 for the two P1 items whose hostile verifier reproduced the failure: the demotion that does not survive a reload, and the incident deltas nothing consumes',
  whenToUse: 'Continuation of wf-game-4t.js after 0/3 converged and the verifiers named the exact defects',
  phases: [
    { title: 'Build', detail: 'answer the verifier findings verbatim; do not re-do what already works' },
    { title: 'Judge', detail: 'a fresh hostile verifier repeats the reload / the class sweep itself' },
    { title: 'Synthesis', detail: 'what a player can now do that they could not' },
  ],
}

// ---------------------------------------------------------------------------
// ROUND 3. Both items are real work that the verifier could not break on the
// half the builder foregrounded -- and both fail the ACCEPTANCE SENTENCE, which
// is the only thing that counts.
//
// g2 is INSTANCE TEN of this project's signature defect, and the most refined
// one yet: not "no caller" but a correct derivation that the shipped path does
// not make. The gate passed because the gate re-derived the rung IN PYTHON via
// consequence.tier_of, while the engine read a stale stored field. A gate that
// computes the answer itself cannot notice that its subject never computes it.
//
// g3 is the same shape one level out: three world states that genuinely differ,
// diffed by a gate, in a dict nothing downstream reads.
// ---------------------------------------------------------------------------

const BRANCH = 'claude/aaa-game-development-j6y2ml'
const MAX_ROUNDS = 2

const ENV = `
ENVIRONMENT. Verify, do not assume:
  * Godot 4.4 double: /home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
  * Vulkan: /usr/share/vulkan/icd.d/lvp_icd.json. Anything reporting "OpenGL 3 Compatibility" is a
    LIE that exits 0 with a PNG -- destroy the artefact and fix the environment.
  * numpy/pillow/pyyaml installed; station/generated/hull.obj built.
If missing, the container recycled: pip install -r requirements.txt ; bash tools/build_godot.sh ;
apt-get update -qq && apt-get install -y -qq mesa-vulkan-drivers ; cd station && python3 generate_hull.py

**ANOTHER WORKFLOW IS STILL LIVE** (wf-aaa-4t.js). It owns economy.py, consequence.py, player.py,
dialogue.py, broadcast.py, boot.py, stream.gd, bake_station.py, bootstrap.py, collision.py, deck.py,
npc/body.py, npc/costume.py, export_scene.py, observation.py, drum_ground.py, drum_dressing.py and
station/spec_harness/{dlg,vrb,ply}.py. **DO NOT EDIT ANY OF THOSE** -- write needed changes into
\`scratchpad/PATCHES-4t-<key>.md\` and report them.
**EXCEPTION, and it is the crux of g2:** \`godot/scripts/interact.gd\` and \`godot/scripts/player.gd\`
are NOT owned by that workflow and g2 MUST edit them -- that is exactly where its defect lives.`

const RULES = `
RULES -- each written from a failure already paid for here:

1. **Work in a \`git worktree\` off a NAMED commit you chose**, not live HEAD. Other agents push
   continuously; an agent that takes a BEFORE from live HEAD can get its own half-finished work.

2. **PUSH, do not merely commit. Early and often.** A commit in a container that rolls back is a
   commit that never happened; this container has recycled four times.
     git fetch origin ${BRANCH} && git rebase origin/${BRANCH} && git push origin HEAD:${BRANCH}
   Non-fast-forward rejection is NORMAL -- somebody landed first. Retry. Stage paths BY NAME;
   **never \`git add -A\`**. Do not open a PR.

3. **Do NOT run** \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\`, \`budget.py\`.
   Four cores, several agents live; two agents have already died of that contention.

4. **Hard rule 1**: every number traces to \`canon/00-MASTER.md\` or becomes a \`## INV-<n>\` entry.
   Check the highest INV first and leave a gap of 30 -- other agents are allocating and INV-925 is
   already taken.

5. **THE GATE MUST ASSERT AGAINST THE ENGINE, NOT AGAINST ITS OWN RECOMPUTATION.** This is the
   whole lesson of round 2 and it generalises beyond your item: a gate that re-derives the answer in
   Python and compares to the value it just derived cannot notice that the shipped path never
   derives it. Where you assert, assert on **the line the engine itself printed**.

6. **IF THE HARNESS BLOCKS YOU, SAY SO AND STOP** -- return \`ok:false\` with the verbatim error.
   Manufacturing evidence to fill a required field is worse than returning nothing.`

const ITEMS = [
  {
    key: 'g2_progression',
    owns: 'station/enforcement.py, godot/scripts/enforcement.gd, godot/scripts/interact.gd, godot/scripts/player.gd',
    why: `**YOUR ROUND-2 WORK LARGELY SURVIVED A HOSTILE VERIFIER AND ONE HALF OF IT IS EXCELLENT.**
It said so: the person-keyed fine draw is genuinely out of the bake, \`enforcement.json\` carries
\`fine_lo\`/\`fine_hi\`/\`brig_cells\` and no scalar, and *"the gate has teeth beyond its author's
imagination"* -- it armed the CELL with a day-source confusion none of your three controls touch and
check 4 caught it. Do not touch that. Do not re-do it.

**IT FAILS THE ACCEPTANCE SENTENCE, WHICH IS THE ONLY THING THAT COUNTS: "quit, reload, still
demoted." The verifier did it in the engine and it is FALSE.** Session 2 opens the very file session
1 wrote -- 3 convictions, \`visa_revoked=True\`, 619.89 cr gone -- and prints
\`interact: purse player:g2c (IVANOVA, AMIS, transit)\` then
\`ARREST gate=FAIL -- nothing on this deck refuses a tier-2 card\`.
**The money persisted, the record persisted, the punishment did not.** THE-GAME.md §5's entire
argument is that failure is demotion plus a record; what ships is the record without the demotion.

**AND THIS IS INSTANCE TEN OF THIS PROJECT'S SIGNATURE DEFECT, in its most refined form yet.** Not
"machinery with no caller" -- a *correct derivation the shipped path does not make*. Verbatim:
  * \`godot/scripts/interact.gd::_sync_purse\` (lines 475-477) writes only \`credits\` and
    \`carrying\` back to the purse -- **never \`tier\`/\`tier_name\`**.
  * \`godot/scripts/player.gd::set_purse\` line 134 reads \`tier = int(st.get("tier", -99))\`
    verbatim from that stale stored field, **never deriving from \`record.visa_revoked\`**.
  * \`_prog_gate\`'s reload assertion passes anyway **because \`_reload_line\` re-derives the rung in
    Python via \`consequence.tier_of\`** -- a call the shipped Godot path does not make.
So your gate was green on a recomputation of its own.`,
    fix: `THE VERIFIER NAMED THE FIX AND YOU SHOULD TAKE THE SECOND FORM, NOT THE FIRST:

1. The minimal fix is \`_sync_purse\` also writing \`st["tier"]\`/\`st["tier_name"]\`. **It works and
   it is wrong** -- it stores the rung as a fact, which \`station/player.py\` deliberately refuses to
   do.
2. **Do it at the RULE.** Give \`godot/scripts/player.gd::set_purse\` the same treatment
   \`_fine_of\`/\`_cell_of\` just got: **compute the rung from \`st["record"]\`**
   (\`visa_revoked\`, \`revoked_from\`, \`convictions\`) against the baked ladder, and treat
   \`st["tier"]\` as the report it is documented to be. \`enforcement.json\` already carries
   \`tiers\`, \`revoke_on_ordinary\`, \`revoke_on_serious\` and the offence grades. This is the
   *"fix the table, not the entry"* lesson CLAUDE.md records for \`BESPOKE_GEOMETRY\`, where a fix
   applied to one entry left the defect in the other seven.
3. **The assertion that would have caught it**, in \`station/enforcement.py::_prog_gate\`: after the
   subject run, **RELAUNCH THE ENGINE on the ledger the engine just wrote** (\`_run\` already copies
   to a temp path -- return it) and require **the second launch's own
   \`interact: purse %s (%s, %s)\` line** to name the demoted \`tier_name\`. Assert against the
   ENGINE's reload, not \`_reload_line\`'s Python \`tier_of\`. Keep \`_reload_line\` as the control
   beside it: Python says 0, and if the engine says \`transit\` the two disagree and the gate goes red.
4. Cheap, and both real: at \`station/enforcement.py\` ~line 1865 make an absent \`tier=\` a FAILURE
   (\`if cm is None: good = False\`) so a control that aborts before doing the thing it names cannot
   score \`ok\`; and add \`float(d.get("floor", -1)) >= 0.0\` to \`_prog_gate\`, or state in
   \`PROG_CONTROLS\` that the brig hold is address-only until red/2/1 is built, so \`floor=-1.00\`
   stops passing silently.`,
    acceptance: `**Two engine launches on one ledger.** Launch 1 arrests, fines and demotes. Launch 2
opens the same ledger and its OWN printed purse line must name the demoted rung, and a tier-gated
door must refuse the card. Quote both launches' verbatim lines. The control: with the derivation
removed, launch 2 says \`transit\` and the gate must go RED.`,
    gate: '`python3 station/enforcement.py --ensure --gate --progression`',
  },
  {
    key: 'g3_incidents',
    owns: 'station/incident.py, station/friction.py, station/journal.py',
    why: `**YOUR ROUND-2 WORK IS REAL AND THE VERIFIER SAID SO: *"The gate is real and I could not make
it lie."*** It wrote three content breaks itself and each fired a different check with a legible
message. The hermeticity fix is genuine -- it verified independently that standalone \`--absence\`
and the in-process run now agree, and it confirmed the \`_pool\` cache-key defect you found
(\`int(hour)%24\` key against a \`hour%24.0\` value) was the cause. Nothing was weakened to pass.
**Do not re-do any of that.**

**TWO THINGS MAKE THE PLAYER CLAIM FALSE, and both are this project's signature defect:**

1. **"ANY of the 30 incident classes" IS NOT TRUE.** The verifier ran \`stance_report\` over all 30:
   **INC-PSICOP gives 2 of 3** -- helps and reports produce the same fingerprint
   \`ce0a37c60f1e5523\`. It then swept **1,557 class x place x hour combinations: exactly 6 failures,
   all INC-PSICOP, all n=2, at both its places and all three hours -- structural to the resolver,
   not a place or hour fluke.** The module's own \`--three-outcomes INC-PSICOP\` **exits 1** today.
   And the reason the claim was made on one row: **\`accept()\` hardcodes \`cid="INC-CONTRA"\` at
   \`incident.py:4744\`**. *A gate on one entry of a table says nothing about the other 29* -- the
   exact lesson CLAUDE.md records for \`BESPOKE_GEOMETRY\`, where the same bug was fixed twice on
   two entries and left in the other seven.

2. **THE WORLD DELTAS HAVE NO CONSUMER**, so "three world states that differ by name" is three
   states of a throwaway dict. Verbatim: \`station/incident.py::_standing\` writes **15 faction keys
   of which 11 do not exist in \`station/journal.py::STANDING_BLOCKS\`** -- the ledger
   \`player.py\` reads -- and \`earthforce\` is a rename of \`ea_lawful\`; **\`incident.py\` calls
   \`journal.move_standing\` ZERO times**; and the single engine join,
   \`boot.py::_collapses\`, yields \`boot.json["collapses"] == []\` on the shipped deck.`,
    fix: `THE VERIFIER NAMED BOTH FIXES AND BOTH GO RED IMMEDIATELY ON TODAY'S CONTENT:

1. **Assert the interface instead of assuming it.** Make \`_standing(w, whose, faction, delta)\`
   (\`incident.py:2411\`) validate \`faction\` against \`journal.STANDING_BLOCKS\` and **raise on an
   unknown key**. That precondition goes red at once on 11 of the 15 keys and forces the join to be
   *made* rather than described -- the same shape as \`ragdoll.gd::promote\` refusing a determinant
   of -1, which found a bug sitting in the shipped crowd. Then either have the resolvers call
   \`journal.move_standing\` on the player's real ledger, or have \`boot.py\` bake the day's
   meaningful deltas into \`boot.json\` beside \`collapses\` so the engine has something to read.
   **\`boot.py\` is owned by another agent** -- if the fix needs it, write
   \`scratchpad/PATCHES-4t-g3.md\` and prefer the \`journal.move_standing\` route, which is yours.
2. **Gate the table, not the instance.** Change \`accept()\`'s signature at \`incident.py:4744\` from
   \`cid="INC-CONTRA", place="cargo_bays"\` to **a loop over \`CLASSES\`** reusing the
   \`--three-outcomes\` assertion that already exists. **It will fail on INC-PSICOP, which is the
   correct outcome**: either \`_res_psicop\` gains a distinct HELPS branch, or INC-PSICOP becomes a
   **named exemption in the class table with its reason written down**, and the docstring's stale
   "21 of 22" becomes a number **the gate computes** rather than one a session wrote down.`,
    acceptance: `**All 30 classes, or a written exemption list with reasons.** \`--accept\` loops the
whole class table and reports N of 30 resolving into three distinct world states, with any exemption
named and justified in the table itself. AND at least one standing delta must reach the player's real
ledger: move it, read it back through the path \`player.py\` uses, and show it changed. A delta that
only exists inside the incident module's own dict is weather.`,
    gate: '`python3 station/incident.py --accept`',
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  required: ['key', 'ok'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean' },
    gate_cmd: { type: 'string', description: 'exact command the critic runs from /home/user/Opus-5' },
    before_result: { type: 'string' },
    after_result: { type: 'string' },
    negative_control: { type: 'string' },
    player_can_now: { type: 'string', description: 'one honest sentence. The verifier WILL try to do exactly this.' },
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
    ran_it: { type: 'string', description: 'the command YOU ran and what it printed' },
    gate_can_fail: { type: 'boolean', description: 'did YOU make the new gate fail on content that should fail it' },
    player_claim_true: { type: 'boolean', description: 'did YOU reproduce the builder’s player claim' },
    worst_defect: { type: 'string' },
    what_would_fix_it: { type: 'string' },
  },
}

function buildPrompt(item, round, prior) {
  return `You are a BUILD agent on the Babylon 5 station simulation at /home/user/Opus-5, branch \`${BRANCH}\`.

READ FIRST, in order: /home/user/Opus-5/CLAUDE.md · /home/user/Opus-5/docs/THE-GAME.md (P1/G0, the
design you are building) · /home/user/Opus-5/docs/AAA-STANDARD.md.

YOUR ITEM: **${item.key}** — ROUND ${round + 2} overall.
YOU OWN, AND ONLY: ${item.owns}

${item.why}

${item.fix}
${ENV}
${RULES}
${prior ? `
A FURTHER VERIFIER REJECTED YOUR LAST ROUND TOO:
  it ran: ${String(prior.ran_it || '-').slice(0, 600)}
  robustness ${prior.score}, AAA ${prior.is_aaa}, gate_can_fail ${prior.gate_can_fail}, player_claim_true ${prior.player_claim_true}
  worst defect: ${prior.worst_defect || '-'}
  fix it names: ${prior.what_would_fix_it || '-'}
  reasoning: ${String(prior.why || '-').slice(0, 900)}
ANSWER THAT.
` : ''}
ACCEPTANCE — the only thing that counts:
${item.acceptance}

1. **Measure BEFORE** with \`${item.gate}\`, verbatim. A diff of two FAILED runs is not a pass:
   assert both runs produced output.
2. **Fix it at the rule, not at the instance.** Both findings above are the same shape — a fix
   applied to one entry of a table, leaving the defect in the others.
3. **Assert against the engine's own printed line**, never against a value your gate recomputed.
   That is precisely how round 2 shipped green while the player was not demoted.
4. **Measure AFTER**, and break it deliberately to show the gate catching it.
5. **\`player_can_now\` in one honest sentence.** The verifier will try that exact thing; if it
   cannot, the round does not count. Do not claim reach you did not build.

Return the structured object.`
}

function judgePrompt(item, built) {
  return `You are a HOSTILE VERIFIER on a Babylon 5 station simulation at /home/user/Opus-5. You did not
build any of this. A previous verifier already caught this item shipping a green gate over a broken
player experience, twice. Assume it happened again and go looking.

THE CLAIM. A build agent says it fixed **${item.key}** and that this proves it:
    ${built.gate_cmd || item.gate}
BEFORE: ${String(built.before_result || '-').slice(0, 700)}
AFTER:  ${String(built.after_result || '-').slice(0, 700)}
Changed: ${String(built.changed || '-').slice(0, 900)}
Negative control: ${String(built.negative_control || '-').slice(0, 700)}
**Player claim: "${String(built.player_can_now || '-').slice(0, 400)}"**

ACCEPTANCE IT WAS BUILDING AGAINST:
${item.acceptance}

READ \`/home/user/Opus-5/docs/THE-GAME.md\`, especially §5 — failure is demotion plus a record, never
a game over. You may read anything including \`git diff\`; you are judging a system, not a picture.

1. **YOUR CHECKOUT MAY BE STALE.** The last two verifiers both found the command missing at
   /home/user/Opus-5 because agents push continuously and the main checkout was 48 commits behind.
   \`git fetch\` and make your own \`git worktree\` at origin's tip BEFORE concluding anything is
   absent. A stale checkout is not a finding about the work.

2. **RUN THE COMMAND YOURSELF.** Put what it printed in \`ran_it\`. If it disagrees with the report
   in any particular, that is your finding and it outranks everything else. (Do NOT run
   \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\`, \`budget.py\`.)

3. **DO THE PLAYER THING YOURSELF.** ${item.key === 'g2_progression'
    ? 'Run the engine TWICE on ONE ledger. Read launch 2\'s own `interact: purse ...` line. Is the player still demoted? The last verifier found the money and the record persisted and the punishment did not — check whether that is still true.'
    : 'Sweep the WHOLE class table, not the one class the report quotes. The last verifier swept 1,557 class x place x hour combinations and found exactly 6 failures, all INC-PSICOP. Do your own sweep. And check a standing delta actually reaches the player ledger `player.py` reads.'}
   Set \`player_claim_true\` from what happened, not from what you were told.

4. **TRY TO MAKE THE GATE PASS ON CONTENT THAT SHOULD FAIL IT.** Break what it protects; check it
   goes red. Set \`gate_can_fail\` from what YOU observed. Prefer a break the author did NOT
   enumerate — the last verifier armed a code path none of the three shipped controls touched and
   found a real defect that way.

5. **CHECK NOTHING WAS WEAKENED.** \`git diff\` it. A loosened floor, tolerance, assertion or spec
   row is a finding, not a nit. *Neither the spec nor the station may be edited to make the other pass.*

6. **JUDGE.** Robustness per \`docs/AAA-STANDARD.md\`: 4 is "handles the cases it will actually meet,
   fails legibly, and its failure is gated"; 3 is "works on the happy path". **Default to NO.**

7. **Name the worst remaining defect and the concrete fix**, naming a file or parameter. Source:
   \`${item.owns}\`.

You may not be agreeable. Every claim cites the command you ran or the line you read.`
}

const results = await pipeline(
  ITEMS,
  async (item) => {
    const rounds = []
    let prior = null
    for (let r = 1; r <= MAX_ROUNDS; r++) {
      const built = await agent(buildPrompt(item, r, prior), {
        label: `build:${item.key}:r${r + 2}`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high',
      })
      if (!built || !built.ok) {
        rounds.push({ round: r, built, verdict: null, converged: false })
        log(`${item.key} r${r + 2}: build produced nothing judgeable`
          + (built && built.notes ? ` — ${String(built.notes).slice(0, 200)}` : ''))
        break
      }
      const verdict = await agent(judgePrompt(item, built), {
        label: `judge:${item.key}:r${r + 2}`, phase: 'Judge', schema: VERDICT_SCHEMA, effort: 'high',
      })
      const correct = !!verdict && verdict.gate_can_fail === true && verdict.player_claim_true === true
      const converged = !!verdict && verdict.is_aaa === true && correct
      rounds.push({ round: r + 2, built, verdict, correct, converged })
      log(`${item.key} r${r + 2}: gate_can_fail ${verdict ? verdict.gate_can_fail : '?'}, `
        + `player_claim_true ${verdict ? verdict.player_claim_true : '?'}, `
        + `robustness ${verdict ? verdict.score : '?'}, AAA ${verdict ? verdict.is_aaa : '?'}`)
      if (converged) break
      prior = verdict ? { ...verdict, correct } : null
    }
    return { key: item.key, rounds }
  },
)

phase('Synthesis')
const done = results.filter(Boolean)
const converged = done.filter(r => r.rounds.some(x => x.converged))
const playable = done.filter(r => r.rounds.some(x => x.verdict && x.verdict.player_claim_true === true))
log(`${converged.length} of ${done.length} converged; ${playable.length} had the PLAYER claim reproduced`)

return {
  summary: `${converged.length}/${done.length} converged, ${playable.length}/${done.length} player claims reproduced`,
  converged: converged.map(r => r.key),
  still_short: done.filter(r => !r.rounds.some(x => x.correct)).map(r => r.key),
  table: done.map(r => {
    const last = r.rounds[r.rounds.length - 1] || {}
    const v = last.verdict || {}, b = last.built || {}
    return {
      key: r.key, rounds_this_run: r.rounds.length,
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
