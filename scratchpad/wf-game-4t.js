export const meta = {
  name: 'game-4t-p1-exists',
  description: 'Build P1 -- the phase titled THE GAME EXISTS -- and P5 packaging, so a stranger can start it and lose something',
  whenToUse: 'The owner asked for a WORKING game and the batch chosen off the red lists did not contain P1, because P1 has no gate and appears red on no list',
  phases: [
    { title: 'Build', detail: 'one agent per P1/P5 item: measure BEFORE, build, wire to the shipped path, measure AFTER' },
    { title: 'Judge', detail: 'a hostile verifier runs the acceptance test itself and tries to make the new gate pass on bad content' },
    { title: 'Synthesis', detail: 'what a player can now do that they could not' },
  ],
}

// ---------------------------------------------------------------------------
// WHY THIS EXISTS, AND IT IS A CORRECTION.
//
// The owner asked for "a working AAA game in every aspect". Batch 1
// (wf-aaa-4t.js) was selected off the red lists -- spec_check --red, the AAA
// scorecard, MASTER-PLAN R1-R7 -- and every item on it is real work. But P1,
// the phase LITERALLY TITLED "THE GAME EXISTS", was not on it, because P1 has
// no gate and therefore appears red on no list that a batch gets chosen from.
//
// That is session 4d's ruling operating at plan scale: "the project optimises
// what can be counted, because counts go green and a game cannot be expressed
// as a count." Following the instruments selected against the instruction.
//
// docs/THE-GAME.md (G0) was written first, in the main agent's own turn,
// because G1-G3 all build against it and it was the blocking input. Its §7
// binds six claims to gates that can fail, and ALL SIX ARE RED. Those are
// what these agents close.
//
// FILE LISTS ARE DISJOINT FROM BATCH 1's, and that was checked rather than
// assumed. Batch 1 owns economy.py, consequence.py, player.py, dialogue.py,
// boot.py, stream.gd, collision.py, deck.py, npc/*, export_scene.py,
// observation.py, drum_*.py. NOTHING below touches any of them. G1 (the role
// loop) is deliberately NOT here despite being P1, because it needs economy.py
// and would collide -- it goes in batch 3 when verbs_economy returns.
// ---------------------------------------------------------------------------

const BRANCH = 'claude/aaa-game-development-j6y2ml'
const MAX_ROUNDS = 2

const ENV = `
ENVIRONMENT, restored by the main agent before you started. Verify, do not assume:
  * Godot 4.4 double: /home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
  * Vulkan: /usr/share/vulkan/icd.d/lvp_icd.json (lavapipe). A probe reported
    "Vulkan 1.4.318 - Forward+ - llvmpipe". Anything reporting OpenGL 3 Compatibility is a LIE
    that exits 0 with a PNG -- destroy the artefact and fix the environment.
  * numpy/pillow/pyyaml installed; station/generated/hull.obj rebuilt.
IF ANY IS MISSING the container recycled under you. Restore with:
  pip install -r requirements.txt ; bash tools/build_godot.sh ;
  apt-get update -qq && apt-get install -y -qq mesa-vulkan-drivers ;
  cd station && python3 generate_hull.py
and say so in your notes.

**ANOTHER WORKFLOW IS LIVE IN THIS REPOSITORY RIGHT NOW** (wf-aaa-4t.js, nine items). It owns
economy.py, consequence.py, player.py, dialogue.py, broadcast.py, boot.py, stream.gd,
bake_station.py, bootstrap.py, collision.py, deck.py, npc/body.py, npc/costume.py,
export_scene.py, observation.py, drum_ground.py, drum_dressing.py and station/spec_harness/{dlg,vrb,ply}.py.
**DO NOT EDIT ANY OF THOSE.** If your work needs a change in one, write the patch into
\`scratchpad/PATCHES-4t-<your key>.md\` and report it -- do not apply it. Two agents in one file
is the stomped-artefact defect CLAUDE.md records three times.`

const RULES = `
HOW YOU WORK -- each rule is written from a failure this project has already paid for:

1. **Work in a \`git worktree\`** off a NAMED commit you chose, not live HEAD -- other agents are
   pushing to this branch continuously and HEAD moves under you. An agent that computes a BEFORE
   from live HEAD can get a HEAD containing its own half-finished work, and then its A/B is a diff
   of a thing against itself.

2. **PUSH, do not merely commit, and push EARLY and OFTEN.** A commit in a container that rolls
   back is a commit that never happened; this container has recycled four times and an agent doing
   exactly your job lost its entire run that way. Several agents share this branch, so:
     git fetch origin ${BRANCH} && git rebase origin/${BRANCH} && git push origin HEAD:${BRANCH}
   Retry on rejection -- non-fast-forward is NORMAL here, it means somebody else landed first.
   Stage paths BY NAME. **Never \`git add -A\`** -- it has already swept another agent's
   half-written files into an unrelated commit. Do not open a PR.

3. **Do NOT run the whole-station gates** (\`deck.py --sweep\`, \`rooms.py --footprint\`,
   \`walkable.py\`, \`budget.py\`). Four cores, and up to four agents live. Two agents have already
   died of exactly this contention. Run your own module's selftest and your one acceptance gate.

4. **Hard rule 1: nothing from memory.** Every number traces to \`canon/00-MASTER.md\` or becomes a
   \`## INV-<n>\` entry in \`canon/INVENTIONS.md\` -- what, why, what constrained it, what would
   overturn it. Check the highest INV number first and leave a gap of at least 30; several agents
   are allocating at once and batch 1 has already reached INV-724.

5. **A gate you add must be able to FAIL, and you must SHOW it failing.** Every gate in this
   project that could not fail passed on content that was wrong. Quote the negative control.

6. **WIRE IT TO THE SHIPPED PATH.** Finished, tested machinery with no caller has happened NINE
   times here, and the ninth slipped under the static scan built to catch the eighth -- a loader
   added to \`walk.gd::_load_level\` when the shipped scene is STREAMED, so that function never
   runs. Run \`python3 tools/wiring.py --selftest\`, then LAUNCH THE THING and grep for the line
   your own code prints. A static scan says a caller exists; only running it says the caller runs.

7. **IF THE HARNESS BLOCKS YOU, SAY SO AND STOP.** If tool calls are rejected before execution
   ("The permission handler returned updatedInput ... required parameter is missing"), return
   \`ok: false\` with the verbatim error in \`notes\`. Manufacturing evidence to fill a required
   field is worse than returning nothing.`

const GAME_DOC = `
**READ \`docs/THE-GAME.md\` FIRST.** It is P1/G0, written this session, and it is the design you
are building. The one-sentence version: *"You are nobody, on a station of 250,000, and the only
thing standing between you and being put back on a transport is a card that says who you are --
so the game is the slow, contested business of becoming somebody the station has a reason to
keep."* The spine is the identicard, which \`player.py\` already carries, \`customs\` already
enforces, and the brig already exists as a built room. Five tiers, each a card state, each
LOSABLE. Failure is demotion plus a record, **never a game over** -- ejecting the player from the
station is the one thing this design must not do, because the station is the product.
§7 of that file lists six claims bound to gates, ALL RED. Yours are named below.`

const ITEMS = [
  {
    key: 'g2_progression',
    owns: 'station/enforcement.py, godot/scripts/enforcement.gd',
    why: `**P1/G2 — PROGRESSION & CONSEQUENCE.** MASTER-PLAN: *"the identicard tier ladder; arrest →
brig → fine → release closes; visa revocation exists and can actually happen to you."*
THE-GAME.md §5 makes this the entire punishment model: there is no death and no game over, so
**demotion plus a record is the only thing failure can cost**, and if this loop does not close the
game has no stakes at all. §3's ladder is five card states — undocumented → visitor visa →
resident → licensed trader/deputy → docking privileges — and every rung must be LOSABLE.
Today: \`spec_check --red\` VRB-08 says there is *no read-a-card-as-officer entry point in
enforcement.py, player.py or enforcement.gd*, and VRB-09 says PLC-017 \`brig\` declares
('cell_door','bunk','intercom') and **0 of them answer LOOK with anything**. The brig is a room
with no booking record. CAST-05's premise — "no memory of the player, no persistent world-state" —
is what makes the *record* half hard, and it is the half that matters.
NOTE: \`player.py\` is owned by another agent. Read it, do not edit it; write any needed change to
\`scratchpad/PATCHES-4t-g2.md\`.`,
    acceptance: `**The loop closes and the demotion persists.** In ONE run: a player at tier ≥2 is
arrested, held in the brig as a *place they are actually in*, fined against real credits, released
— and afterwards their tier is one rung LOWER and a readable booking record exists naming them,
the offence and the fine. Then prove the record survives: quit, reload, still demoted, still on
file, with a \`--no-restore\` control that fails. Report the tier before and after as numbers.
A loop that returns the player to where they started is not consequence, it is a cutscene.`,
    gate: '`python3 station/enforcement.py --selftest` plus the new arrest-to-release gate you add',
  },
  {
    key: 'g3_incidents',
    owns: 'station/incident.py, station/friction.py',
    why: `**P1/G3 — THE INCIDENT GENERATOR (not one incident).** MASTER-PLAN: *"classes seeded from
friction.py, security.py, customs contraband, dock accidents; rate denominator ≥2/station-hour near
the player; each class run **absent / helps / reports** produces 3 distinct world states."*
This is what makes A2's promise true — *"is drawn into events that would have happened without
them, changes how they end"*. The absence half already half-exists: 30 incident classes and 2,011
incidents a station-day are generated. **What does not exist is the player mattering to one.**
Three runs of the same class from the same seed — player absent, player helps, player reports —
must end in three world states you can name and diff, or the incidents are weather.
\`spec_check --red\` also has a real finding to fix or refute here: **INC-CONTRA is a declared
write that CANNOT HAPPEN** — \`response_s\` is 0.0 at both customs halls at all 48 half-hours
against a 300 s window, so the \`_stock(w,"black_market",…)\` write at \`incident.py:2308\` is
unreachable. Decide it honestly: is the spec wrong or the station? Neither may be edited to make
the other pass.`,
    acceptance: `**Same seed, same class, three outcomes.** Run one incident class three ways —
absent, helps, reports — and diff the resulting world state, showing the three differ in ways you
can name (stock, standing, a person's location, a record). Then the rate: ≥2 meaningful incidents
per station-hour *near the player*, measured over a headless day, with the denominator stated —
"near" must be defined in metres or in places, not felt. And the **absence gate**: a
player-absent day must differ from a player-present day in the same seed.`,
    gate: '`python3 station/incident.py --selftest` plus the new three-outcome gate you add',
  },
  {
    key: 'p5_firstrun',
    owns: 'godot/export_presets.cfg (NEW), godot/scripts/main_menu.gd (NEW), tools/package.sh (NEW), godot/scripts/main.gd',
    why: `**P5 — SHIP, and the reason it is in this batch rather than last.** MASTER-PLAN A2's
definition of done opens: *"a stranger downloads ONE FILE, runs it at 60 fps, arrives at Babylon 5
as a person with papers."* Measured this session: \`godot/export_presets.cfg\` **does not exist**,
there is **no main menu, no new-game, no title screen**, and \`tools/\` has no packaging path.
**There is currently no way for a person to start this.** Every other item in every batch improves
something a player cannot reach.
This is not polish and it is not last: it is the thing that converts 178,000 lines of Python and
25,000 of GDScript into an artefact somebody can open. It also makes P0h possible — the plan's two
human sittings, which have never happened, because there has never been anything to sit at.
\`arrival.gd\` (592 lines) and C-010 already implement arriving at customs; wire the front door to
it rather than building a new one.
NOTE: \`main.gd\` is the shipped entry point and is NOT owned by batch 1 — but read
\`godot/scripts/stream.gd\`'s owner's work before assuming how the scene boots, and do not edit
stream.gd. The shipped scene is STREAMED; \`walk.gd::_load_level\` is the monolithic path and the
shipped build never runs it. Getting that backwards is instance nine of this project's signature
defect.`,
    acceptance: `**One command produces a build, and the build starts.** \`bash tools/package.sh\`
(or whatever you name it) exports a runnable artefact headlessly, and launching it reaches a title
screen with NEW GAME, and NEW GAME reaches the arrival sequence with the player holding a card.
Report the artefact's size and the exact command. If a full export template is unavailable in this
container, say so **with the error**, and deliver the presets plus a verified headless
\`--export-release\` dry run rather than claiming a build you did not produce — a packaging step
that silently produces nothing is exactly the failure mode CLAUDE.md records for render fallback.`,
    gate: '`bash tools/package.sh --check` plus a headless launch of the exported artefact',
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  required: ['key', 'ok'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean', description: 'false if you could not build or verify anything' },
    gate_cmd: { type: 'string', description: 'the exact command the critic should run to check you, from /home/user/Opus-5' },
    before_result: { type: 'string', description: 'that command BEFORE your change, verbatim summary line' },
    after_result: { type: 'string', description: 'that command AFTER, verbatim summary line' },
    negative_control: { type: 'string', description: 'what you broke deliberately and how the gate reported it' },
    player_can_now: { type: 'string', description: 'in one sentence: what a PLAYER can now do that they could not before' },
    changed: { type: 'string', description: 'what you changed, concretely, naming files' },
    inv_entries: { type: 'string' },
    pushed: { type: 'string', description: 'the commit sha you pushed to origin, or why you could not' },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['is_aaa', 'score'],
  properties: {
    why: { type: 'string' },
    is_aaa: { type: 'boolean', description: 'would you accept this in a shipped AAA game. Default NO.' },
    score: { type: 'integer', minimum: 0, maximum: 5, description: 'robustness 0-5' },
    ran_it: { type: 'string', description: 'the command YOU ran and what it printed' },
    gate_can_fail: { type: 'boolean', description: 'did YOU make the new gate fail on content that should fail it' },
    player_claim_true: { type: 'boolean', description: 'is the builder’s "a player can now..." claim actually true when you try it' },
    worst_defect: { type: 'string' },
    what_would_fix_it: { type: 'string', description: 'concrete, naming a file or a parameter' },
  },
}

function buildPrompt(item, round, prior) {
  return `You are a BUILD agent on the Babylon 5 station simulation at /home/user/Opus-5, branch \`${BRANCH}\`.

FIRST, read in this order — they override your defaults:
  1. /home/user/Opus-5/CLAUDE.md (the working agreement)
  2. /home/user/Opus-5/docs/THE-GAME.md (P1/G0 — the design you are building)
  3. /home/user/Opus-5/docs/MASTER-PLAN.md §A2 and §P1 (the target and the phase)
  4. /home/user/Opus-5/docs/AAA-STANDARD.md (the bar, and the stopping rule)

YOUR ITEM: **${item.key}**
YOU OWN, AND ONLY: ${item.owns}
${GAME_DOC}

WHY IT WAS CHOSEN:
${item.why}
${ENV}
${RULES}
${prior ? `
ROUND ${round}. THE VERIFIER REJECTED YOUR LAST ROUND. It ran your gate itself:
  ${String(prior.ran_it || '-').slice(0, 500)}
  robustness ${prior.score}, AAA ${prior.is_aaa}, gate_can_fail ${prior.gate_can_fail}, player_claim_true ${prior.player_claim_true}
  worst defect: ${prior.worst_defect || '-'}
  it says the fix is: ${prior.what_would_fix_it || '-'}
  its reasoning: ${String(prior.why || '-').slice(0, 900)}
ANSWER THAT. Do not re-do what you already did.
` : ''}
THE JOB: make this part of the game actually WORK, then hand a hostile verifier a command that
proves it — and that verifier will RUN IT ITSELF rather than believe your report.

ACCEPTANCE, and it is what you are judged on:
${item.acceptance}

1. **Measure BEFORE.** Run \`${item.gate}\` and keep the verbatim output. A diff of two FAILED runs
   is not a pass — this project once recorded an A/B as IDENTICAL when both halves had died on the
   same IndexError and written empty files. Assert both runs produced output.

2. **Read the shape of the failing number before its size.** A number that fails evenly is a list
   of jobs; a number that fails 100% on one side of a line and 1% on the other is a STRUCTURAL fact
   and usually one function with one caller. This project closed 84 failures with one extraction by
   reading that split.

3. **Build it, and wire it to the shipped path** (rule 6 above — this is the one that has caught
   this project out nine times).

4. **Measure AFTER with the same command**, and break it deliberately to show the gate catching it.

5. **Answer \`player_can_now\` in one honest sentence.** The verifier will try to do that exact
   thing. If it cannot, your round does not count — so do not claim reach you did not build.

Return the structured object.`
}

function judgePrompt(item, built) {
  return `You are a HOSTILE VERIFIER on a Babylon 5 station simulation at /home/user/Opus-5. You did
not build any of this. Your job is to find out whether a claim is TRUE, and this project's entire
history says the claim will be *nearly* true in a way that matters.

THE CLAIM. A build agent says it built **${item.key}** and that this proves it:
    ${built.gate_cmd || item.gate}
BEFORE: ${String(built.before_result || '-').slice(0, 700)}
AFTER:  ${String(built.after_result || '-').slice(0, 700)}
It changed: ${String(built.changed || '-').slice(0, 900)}
Its negative control: ${String(built.negative_control || '-').slice(0, 700)}
**And it claims a player can now: "${String(built.player_can_now || '-').slice(0, 400)}"**

THE ACCEPTANCE IT WAS BUILDING AGAINST:
${item.acceptance}

The design it is meant to serve is \`/home/user/Opus-5/docs/THE-GAME.md\` — **READ IT**, especially
§5 (failure is demotion plus a record, never a game over) and §7 (six claims bound to gates, all
red before this batch). You are ALLOWED to read anything, including \`git diff\` — you are judging
a system, not a picture.

DO THIS, IN THIS ORDER, AND DO NOT TAKE THE REPORT AT FACE VALUE:

1. **RUN THE COMMAND YOURSELF.** Put what it actually printed in \`ran_it\`. MASTER-PLAN R6: *"A
   static scan can tell you a caller exists; only running the thing tells you the caller runs."* If
   the output disagrees with the report in any particular, that is your finding and it outranks
   everything else. If the command does not exist or does not run, say exactly that.
   (Do NOT run \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\` or \`budget.py\` unless
   the gate itself is one of them — four cores, several agents live.)

2. **TRY THE PLAYER CLAIM YOURSELF.** The builder said a player can now do a specific thing. Go and
   do it. Set \`player_claim_true\` from what happened, not from what you were told. This is the
   single most valuable thing you can do, because every other check in this project scores a PART
   and a part with no caller still meets its standard.

3. **TRY TO MAKE THE GATE PASS ON CONTENT THAT SHOULD FAIL IT.** Break the content the gate is
   supposed to protect and check it goes red. If it stays green, the gate is decoration. Set
   \`gate_can_fail\` from what YOU observed. Nine times in this project a subsystem was finished,
   tested, gated and had no caller on the shipped path, and every gate passed.

4. **CHECK NOTHING WAS WEAKENED TO PASS.** \`git diff\` the change. If a floor, a tolerance, an
   assertion or a spec row was loosened rather than met, say so plainly — that is a finding, not a
   nit. R1's rule is absolute: *is the spec wrong or the station? Neither may be edited to make the
   other pass.*

5. **THEN JUDGE.** Would you accept this in a shipped AAA game? The dimension is ROBUSTNESS per
   \`docs/AAA-STANDARD.md\` — READ IT — where 4 is "handles the cases it will actually meet, fails
   legibly, and its failure is gated" and 3 is "works on the happy path". **Default to NO.**

6. **Name the single worst remaining defect and what would fix it**, concretely, naming a file or a
   parameter. The source is \`${item.owns}\`.

You may not be agreeable. CLAUDE.md: *"The reviewer's job is to be THE REASON this is good, not to
be agreeable. It assumes a defect is present and goes looking."* Every claim cites the command you
ran or the line you read. Return the structured verdict.`
}

const results = await pipeline(
  ITEMS,
  async (item) => {
    const rounds = []
    let prior = null
    for (let r = 1; r <= MAX_ROUNDS; r++) {
      const built = await agent(buildPrompt(item, r, prior), {
        label: `build:${item.key}:r${r}`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high',
      })
      if (!built || !built.ok) {
        rounds.push({ round: r, built, verdict: null, converged: false })
        log(`${item.key} r${r}: build produced nothing judgeable`
          + (built && built.notes ? ` — ${String(built.notes).slice(0, 200)}` : ''))
        break
      }
      const verdict = await agent(judgePrompt(item, built), {
        label: `judge:${item.key}:r${r}`, phase: 'Judge', schema: VERDICT_SCHEMA, effort: 'high',
      })
      // A P1 item converges only when the verifier ran it, could make the gate
      // fail, AND could itself do the thing the builder said a player can do.
      const correct = !!verdict && verdict.gate_can_fail === true && verdict.player_claim_true === true
      const converged = !!verdict && verdict.is_aaa === true && correct
      rounds.push({ round: r, built, verdict, correct, converged })
      log(`${item.key} r${r}: verifier ran it — gate_can_fail ${verdict ? verdict.gate_can_fail : '?'}, `
        + `player_claim_true ${verdict ? verdict.player_claim_true : '?'}, `
        + `robustness ${verdict ? verdict.score : '?'}, AAA ${verdict ? verdict.is_aaa : '?'}`)
      if (converged) break
      prior = verdict ? { ...verdict, correct } : null
    }
    return { key: item.key, owns: item.owns, rounds }
  },
)

phase('Synthesis')

const done = results.filter(Boolean)
const converged = done.filter(r => r.rounds.some(x => x.converged))
const playable = done.filter(r => r.rounds.some(x => x.verdict && x.verdict.player_claim_true === true))
const stuck = done.filter(r => !r.rounds.some(x => x.correct))

log(`${converged.length} of ${done.length} converged; ${playable.length} had their PLAYER claim `
  + `independently reproduced by the verifier`)

return {
  summary: `${converged.length}/${done.length} converged, ${playable.length}/${done.length} player claims reproduced`,
  converged: converged.map(r => r.key),
  still_short: stuck.map(r => r.key),
  what_a_player_can_now_do: done.map(r => {
    const last = r.rounds[r.rounds.length - 1] || {}
    return {
      key: r.key,
      claim: String((last.built || {}).player_can_now || '-').slice(0, 400),
      reproduced_by_verifier: last.verdict ? last.verdict.player_claim_true : null,
      robustness: last.verdict ? last.verdict.score : null,
      is_aaa: last.verdict ? !!last.verdict.is_aaa : null,
      gate_can_fail: last.verdict ? last.verdict.gate_can_fail : null,
      worst_defect: (last.verdict || {}).worst_defect || '-',
      what_would_fix_it: (last.verdict || {}).what_would_fix_it || '-',
      pushed: (last.built || {}).pushed || '-',
    }
  }),
}
