export const meta = {
  name: 'aaa-4t-every-aspect',
  description: 'Drive every weak subsystem to AAA and every red game system to working, each verified by a hostile critic that must be convinced before the item stops',
  whenToUse: 'The owner asked for a working AAA game in every aspect, with a separate harsh critic per item, looping until it passes',
  phases: [
    { title: 'Build', detail: 'one agent per item: measure BEFORE, rework, measure AFTER, hand it over for judgement' },
    { title: 'Judge', detail: 'a hostile critic — blind frames for craft, a re-run of the acceptance test for systems' },
    { title: 'Synthesis', detail: 'what converged, what did not, and what the critic would not accept' },
  ],
}

// ---------------------------------------------------------------------------
// SESSION 4t. Two kinds of item and therefore two kinds of critic.
//
// CRAFT items are judged the way session 4s proved works: the builder renders
// BEFORE and AFTER at identical cameras, copies both into scratchpad/blind/ as
// left-*/right-* choosing the mapping itself, writes that mapping NOWHERE on
// disk, and a critic forbidden `git log` has to pick the new one without being
// told which it is. A critic that cannot tell which frame is new cannot be
// agreeable, which is the whole point -- every other craft gate in this project
// scores a frame against a descriptor, and a descriptor is a thing an author
// can talk themselves into.
//
// SYSTEM items cannot be judged from a picture. Their critic RUNS THE
// ACCEPTANCE TEST ITSELF and then tries to break it -- because MASTER-PLAN R6
// is that a static scan tells you a caller exists and only running the thing
// tells you the caller runs. It must also try to make the new gate pass on
// content that should fail it. A gate that cannot fail is this project's
// signature defect, nine times over.
//
// THIS SCRIPT LIVES IN THE REPO, not /tmp, because /tmp is wiped by the
// container recycles that have taken four runs so far.
// ---------------------------------------------------------------------------

const BRANCH = 'claude/aaa-game-development-j6y2ml'
const MAX_ROUNDS = 2

// Environment facts established by the main agent before this launched. An
// agent that finds them untrue has been recycled and must redo them.
const ENV = `
THE ENVIRONMENT WAS RESTORED BEFORE YOU STARTED. Verify, do not assume:
  * Godot 4.4 double: /home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
  * Vulkan: /usr/share/vulkan/icd.d/lvp_icd.json (lavapipe). A probe render reported
    "Vulkan 1.4.318 - Forward+ - llvmpipe" — the path is NOT degraded.
  * numpy/pillow/pyyaml installed. 37 spec harnesses were crashing on a missing numpy.
  * station/generated/hull.obj rebuilt from the schema.
IF ANY IS MISSING the container recycled under you. Restore with:
  pip install -r requirements.txt ; bash tools/build_godot.sh ;
  apt-get update -qq && apt-get install -y -qq mesa-vulkan-drivers ;
  cd station && python3 generate_hull.py
and say so in your notes.`

const RULES = `
HOW YOU WORK, and these are not optional — each one is written from a failure this project has already paid for:

1. **Work in a \`git worktree\`** off the current HEAD of \`${BRANCH}\`. Other build agents are live
   in the same repository and the build tools rewrite \`station/generated/scene/*\` on every run.
   CLAUDE.md records a gate timing out at 1800 s and two agents dying mid-flight from exactly this.
   Take your worktree at a NAMED commit you chose, not from live HEAD — HEAD moves while others push.

2. **PUSH, do not merely commit, and push EARLY and OFTEN.** A commit in a container that rolls
   back is a commit that never happened; an agent doing this exact job lost its entire run that way.
   Push a checkpoint the moment you have anything worth keeping, then again on every increment:
     git fetch origin ${BRANCH} && git rebase origin/${BRANCH} && git push origin HEAD:${BRANCH}
   Retry on conflict. Stage paths BY NAME — never \`git add -A\`, several agents share this index
   and one \`add -A\` has already swept another agent's half-written files into a commit.
   Do not open a PR. Do not edit \`docs/aaa-scorecard.json\` — write scores to
   \`scratchpad/aaa-4t-<your key>.json\` instead, or you will collide with every other agent.

3. **Do NOT run the whole-station gates**: \`deck.py --sweep\`, \`rooms.py --footprint\`,
   \`walkable.py\`, \`budget.py\`. Each is minutes to tens of minutes of 100% CPU on a FOUR-core box
   with other agents live, and CLAUDE.md records two agents killed by exactly that contention.
   Run the self-tests your own files own, and the one acceptance gate named in your brief.

4. **Hard rule 1: nothing is built from memory.** Every dimension, name and number either traces to
   \`canon/00-MASTER.md\` or becomes a \`## INV-<n>\` entry in \`canon/INVENTIONS.md\` saying what,
   why, what constrained it, and what would overturn it. Check the highest INV number first and
   leave a gap of at least 20 above it — several agents are allocating at once.

5. **A gate you add must be able to FAIL, and you must SHOW it failing.** Every gate in this
   project that could not fail passed on content that was wrong. Quote the negative control.

6. **IF THE HARNESS BLOCKS YOU, SAY SO AND STOP.** If tool calls are rejected before execution
   ("The permission handler returned updatedInput ... required parameter is missing"), return
   \`ok: false\` with the verbatim error in \`notes\`. Do not burn context retrying an environment
   fault. Manufacturing evidence to fill a required field is worse than returning nothing.`

// ---------------------------------------------------------------------------
// THE ITEMS. File lists are disjoint and were checked for hidden artefact and
// import collisions, not assumed to be separate because the names differ.
// ---------------------------------------------------------------------------
const ITEMS = [
  // ---- SYSTEM items: judged by re-running the acceptance test -------------
  {
    key: 'streaming_reach',
    kind: 'system',
    owns: 'godot/scripts/stream.gd, station/boot.py, tools/bake_station.py, tools/bootstrap.py',
    why: `MASTER-PLAN R5, and it is the single biggest thing between this project and "a working game".
The shipped STREAMED build reaches ONE z-cluster: \`cells_blue_0_0\` is 18 cells spanning 12.9 m of z
of an 8,047 m station. **8 of 129 places overlap it and 121 are unreachable from the spawn.** The
concrete consequence the gate already reports: the nearest window is 838 m along the axis, so the
vista mount is correct and can never fire. Two causes that must NOT be conflated — (a)
cell_manifest.json's deck table lists 251 decks and this container has ONE baked, a recycled-container
artefact; (b) cluster-to-cluster hand-off is genuinely untested (P0.5).`,
    acceptance: `A body walks from the spawn cluster INTO AN ADJACENT ONE AND BACK, with cells loading
and freeing as it goes, and ARRIVES AT A NAMED PLACE in the far cluster. Name the place in the output.
Report cells resident at each step and prove freeing happens (the count must come down, or it is a
leak and not streaming). State the honest denominator for baked decks — 251 in the manifest against 70
recorded baked, and NOTHING in the repository states which is intended; report the fraction, and do not
pick whichever reading makes a number look better.`,
    gate: 'the new cluster-hand-off walk gate you add, plus `python3 tools/bootstrap.py --check`',
  },
  {
    key: 'dialogue_depth',
    kind: 'system',
    owns: 'station/dialogue.py, station/broadcast.py, station/spec_harness/dlg.py',
    why: `The largest content gap on the station, and it is what "the simulation exists around you
rather than in text" fails on first. \`spec_check.py --red\` today, all six DLG rows RED:
  DLG-01 floor is 3,750 lines (75 each x 50 cast); dialogue.py has **69 NPC templates TOTAL**, shared
         by every speaker — so the no-two-identical rule is violated BY CONSTRUCTION.
  DLG-02 a cell draws from 39 shared templates against a floor of 30 per cell (19 role registers x 15
         species voices MODULATE them, they do not multiply them — do not count them as a product).
  DLG-03 no per-counter trade vocabulary exists: serve_response() returns speak(), whose trade line
         comes from a shared PHRASE['trade'] pool of THREE.
  DLG-04 floor 98 broadcast templates; broadcast.py ships 21, and there is no denunciation set.
  DLG-05 dialogue.SAY ships 30 player templates over 10 of 11 topics (refusal missing) against 152.
  DLG-06 no Kosh pool (<=12, never twice a session), no Broker pool (<=20, audience-gated).
Era lock is SEASON 2-3. Write in the show's register, not in generic fantasy-tavern.`,
    acceptance: `\`python3 station/spec_check.py --red\` shows FEWER RED DLG rows than the six it shows
now, and every row you close closes because the content EXISTS and the harness READ it — never because
the harness or the spec was loosened. Quote the before and after line for each row you touch. If you
conclude a spec floor is itself wrong, say so with the arithmetic and DO NOT edit it to pass; that
decision is the owner's and R1's rule is that neither side may be edited to make the other pass.`,
    gate: '`python3 station/spec_check.py --red` (DLG rows) and `python3 station/dialogue.py --coverage`',
  },
  {
    key: 'verbs_economy',
    kind: 'system',
    owns: 'station/economy.py, station/consequence.py, station/spec_harness/vrb.py',
    why: `The verb set is what a player DOES, and half of it is declared and unbuilt. From
\`spec_check.py --red\`:
  VRB-05 BUY/SELL — "credits and stock move BOTH ways": the buy side is consequence.purchase, **the
         sell side is not implemented at all**, no sell/fence entry point exists. MASTER-PLAN R7 lists
         SELL as one of four things the spec enumerates and NO PHASE SCHEDULES.
  VRB-03 TAKE/PLACE — placement does not persist; no player state key records an object placed anywhere.
  VRB-04 SIT — "the seat allocator consults it": will_share_table is called from civic_calendar.py,
         which is not the code that puts a body on a seat.
  VRB-07 WORK — 1 of 12 ROLEs has a clock-on/clock-off loop with pay (dockwork.py).
  PLY-03 the ladder's top tier is hotel/business class and economy.LADDER has no such row; the
         SYS-13 \`player_placements\` save-delta class exists nowhere; no household-goods vendor exists.
  GDS-01 economy.GOODS holds 34 named goods against a floor of >=60.`,
    acceptance: `A player can SELL something and it must be observable in BOTH directions in one run:
credits up, stock down, at a named place, by a named fence or counter — and the same run shows a BUY
so the two are symmetric. Then quote \`spec_check.py --red\` before and after for every VRB/GDS/PLY row
you touch. A verb that exists as a function nobody calls is the defect this project has produced NINE
times; show the call site on the shipped path, not in a selftest.`,
    gate: '`python3 station/spec_check.py --red` (VRB, GDS, PLY rows) plus the economy module selftest',
  },
  {
    key: 'journal_time',
    kind: 'system',
    owns: 'station/journal.py (NEW), godot/scripts/journal.gd (NEW), station/player.py, station/spec_harness/ply.py',
    why: `Three of MASTER-PLAN R7's four unscheduled items, and R7's own argument is why they belong
together: "a condition model with no save is a hunger bar that resets, and a journal with no save is a
notebook that forgets. They are the same problem as persistence and should be built where it is."
P2's save system already exists (\`godot/scripts/save.gd\`, gate \`coldstart.py --g8\`), so these have
somewhere to persist to.
  PLY-07 a journal exists NOWHERE in station/, godot/ or tools/ (searched journal, JOURNAL).
  SYS-16 knowledge items exist NOWHERE (knowledge_item, KNOWLEDGE, known_facts).
  PLY-05 time compression through the running simulation exists NOWHERE (time_compression,
         compress_clock, advance_clock, TIME_COMPRESSION).
  CAST-05 no per-NPC memory slots, no name-given flag, no faction standing scalars — "no memory of
         the player, no persistent world-state" is the row's own premise and it still holds.
The point of a journal here is not a UI list. It is that the station is an INFORMATION LAYER the
player can use — the scope document's words — so a thing learned from a conversation, a broadcast or a
notice must become a thing the player HAS.`,
    acceptance: `Learn a fact in-world, quit, reload, and STILL HAVE IT — with a \`--no-restore\`
control that fails. That is the exact shape \`save.gd\`'s existing gate uses and it is the shape that
makes this real. Separately: compress time through the RUNNING simulation and show the world moved
(a clock advanced AND something in the world changed state as a consequence), not a clock that jumped.`,
    gate: '`python3 station/coldstart.py --g8` extended for the journal, plus `spec_check.py --red` PLY/SYS/CAST rows',
  },
  {
    key: 'shell_fit',
    kind: 'system',
    owns: 'station/collision.py, station/deck.py',
    why: `\`python3 station/deck.py --shell-fit\` is landed and **RED at 20 rooms**: geometry outside
its own collision shell. \`ambassadorial_suites\` has a ±5.25 m shell against a mesh running
−92.28..+8.53 m. A player in one of those twenty rooms walks through the world or falls out of it.
The brief is already written at \`scratchpad/BRIEF-shellfit.md\` — READ IT FIRST. An agent lost its
entire run on this in session 4s because it committed inside a worktree the container then deleted;
you own the same job with the PUSH rule above, so do not repeat it.
NOTE: this collides with \`station/rooms.py\`, which you do NOT own. If the fix needs a rooms.py
change, write the patch into \`scratchpad/PATCHES-4t-shellfit.md\` and report it — do not apply it.`,
    acceptance: `\`python3 station/deck.py --shell-fit\` reports 0 rooms with geometry outside their
shell, down from 20, and the negative control still fires — deliberately break one room's shell and
show the gate catching it. A gate that goes green because it stopped looking is worthless.`,
    gate: '`python3 station/deck.py --shell-fit`',
  },

  // ---- CRAFT items: judged blind, by frames -------------------------------
  {
    key: 'npc_bodies',
    kind: 'craft',
    owns: 'station/npc/body.py, station/npc/costume.py',
    scores: 'craft 2, fidelity 2, performance 2, robustness 2 (2 rounds)',
    why: `THE LOWEST ROW ON THE SCORECARD ON EVERY DIMENSION. These are the people. A station of
250,000 whose inhabitants read as mannequins fails the owner's brief harder than any wall does — the
scope document asks for "NPCs with quarters, jobs, schedules and events — not crowds, *residents*".
Session 4q also found the whole walking crowd was drawn MIRRORED for six sessions (determinant −1),
which no visual gate caught; assume the body is wronger than it looks.`,
    shot: '--shot deck --deck blue/0/0 --at docking_bays',
  },
  {
    key: 'interior_lighting_4b',
    kind: 'craft',
    owns: 'tools/export_scene.py (the interior light rig and ROOM_EXPOSURE)',
    scores: 'craft 2, fidelity 2, performance 4, robustness 4 (1 round)',
    why: `Layer 4b stands at 13 of 23 on the DISTRIBUTION test — the rooms are FLAT, and STATE.md has
already measured why, so do not re-derive it: fixture energy is INERT (0 -> 2.0 moves p5 by x1.0000),
the soft fill nearly so (6 -> 24 moves it x1.11), and **AMBIENT OWNS p5** (1.30 -> 2.60 moves it
x2.35). Ambient buys level and SPENDS CONTRAST. The tonemapper is NOT the cause — AgX gives the lowest
p5 of the five available, so that hypothesis is refuted. And the blown pools are EMISSION, which
\`room_exposure\` does not touch at all. TRAP: \`measure_frame\` censors at FLOOR=0.010, so every
statistic except \`level_p25\` is over the MEASURABLE pixels — always read \`measurable %\` beside any
number from it, or you will judge a room on 7.7% of its own frame as this project once did.`,
    shot: '--shot interior --room zocalo',
  },
  {
    key: 'observation',
    kind: 'craft',
    owns: 'station/observation.py (BOTH observation_domes and observation_rotunda)',
    scores: 'domes craft 2 fid 3 perf 4 rob 4; rotunda craft 2 fid 3 perf 3 rob 4',
    why: `A window onto space that renders BLACK is the single most Babylon 5 thing on the station
failing. Round 1 logged 489 non-manifold edges on the rotunda and a window showing nothing because
\`--shot interior\` has no exterior behind it. Two scorecard rows, ONE source file — which is why this
is one agent and not two; two agents in one file is the stomped-artefact defect.`,
    shot: '--shot interior --room obs_dome_1',
  },
  {
    key: 'drum_interior_engine',
    kind: 'craft',
    owns: 'station/drum_ground.py, station/drum_dressing.py',
    scores: 'craft 2, fidelity 3, performance 4, robustness 3 (1 round)',
    why: `The payoff view of the whole station: ground curving up and away, the far side arching
overhead. It is the shot a player remembers and the one a viewer of the show will recognise instantly.
Its own round-1 note says it works AT DISTANCE, and STATE.md 24.4b says it is "still bare underfoot" —
so the failure is the near field, which is where the rubric's HALF distance looks.
NOTE: the drum inverts the collision rule — \`drum_walk.py\` authors no terrain, it calls
\`drum_ground.ground_patch\`, the same function the render ground is built from. If you change the
ground's shape you change what a body walks on. Its gate is SLOPE, not lip.`,
    shot: '--shot drum --stand 20,4700 --look 20,6300',
  },
]

// REQUIRED IS DELIBERATELY SHORT. Session 4s lost all five agents to a
// nine-field `required`: a blocked agent's every retry failed on nine counts
// instead of letting it say "I am blocked". Only the fields the control flow
// branches on are required.
const BUILD_SCHEMA = {
  type: 'object',
  required: ['key', 'ok'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean', description: 'false if you could not build, render, or change anything' },
    blind_dir: { type: 'string', description: 'CRAFT only: directory holding left-*.png and right-*.png, one pair per distance' },
    after_is: { type: 'string', enum: ['left', 'right'], description: 'CRAFT only: which side is YOUR NEW build. Write this NOWHERE on disk.' },
    forward_plus: { type: 'boolean', description: 'CRAFT only: did EVERY render log say Vulkan ... Forward+ (not OpenGL 3 Compatibility)' },
    distances: { type: 'array', items: { type: 'string' }, description: 'CRAFT only: the distance labels, the metres, and how each was derived' },
    gate_cmd: { type: 'string', description: 'SYSTEM only: the exact command the critic should run to check you' },
    before_result: { type: 'string', description: 'SYSTEM only: that command output BEFORE your change, verbatim summary line' },
    after_result: { type: 'string', description: 'SYSTEM only: that command output AFTER, verbatim summary line' },
    negative_control: { type: 'string', description: 'SYSTEM only: what you broke deliberately and how the gate reported it' },
    changed: { type: 'string', description: 'what you actually changed, concretely, naming files' },
    inv_entries: { type: 'string', description: 'INV numbers you allocated in canon/INVENTIONS.md' },
    pushed: { type: 'string', description: 'the commit sha you pushed to origin, or why you could not' },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['is_aaa', 'score'],
  properties: {
    pick: { type: 'string', enum: ['left', 'right', 'indistinguishable'], description: 'CRAFT only' },
    confidence: { type: 'string', enum: ['certain', 'likely', 'marginal'] },
    why: { type: 'string', description: 'the specific pixels/forms, or the specific command output, that decided it' },
    is_aaa: { type: 'boolean', description: 'would you accept this in a shipped AAA game. Default NO.' },
    score: { type: 'integer', minimum: 0, maximum: 5, description: 'craft score for craft items, robustness score for system items' },
    ran_it: { type: 'string', description: 'SYSTEM only: the command you ran yourself and what it printed' },
    gate_can_fail: { type: 'boolean', description: 'SYSTEM only: did YOU make the new gate fail on content that should fail it' },
    worst_defect: { type: 'string' },
    what_would_fix_it: { type: 'string', description: 'concrete, buildable, naming the file or the parameter' },
    did_not_peek: { type: 'boolean', description: 'CRAFT only: true only if you did NOT read git log/diff or anything naming which side is new' },
  },
}

function buildPrompt(item, round, prior) {
  const head = `You are a BUILD agent on the Babylon 5 station simulation at /home/user/Opus-5, branch \`${BRANCH}\`.

FIRST, read in this order — they override your defaults:
  1. /home/user/Opus-5/CLAUDE.md (the working agreement)
  2. /home/user/Opus-5/docs/AAA-STANDARD.md (the rubric, the three distances, the descriptors, the stopping rule)
  3. the section of /home/user/Opus-5/docs/MASTER-PLAN.md your item names

YOUR ITEM: **${item.key}**
YOU OWN, AND ONLY: ${item.owns}
WHY IT WAS CHOSEN:
${item.why}
${ENV}
${RULES}
`
  const priorBlock = prior ? `
ROUND ${round}. THE CRITIC REJECTED YOUR LAST ROUND. Its verdict — and for craft items it did not know
which frame was yours:
  ${item.kind === 'craft' ? `picked: ${prior.pick} (${prior.confidence || '-'}) — ${prior.correct ? 'that WAS your new build' : 'that was the OLD build, or it could not tell'}` : `it ran your gate itself: ${String(prior.ran_it || '-').slice(0, 400)}`}
  score ${prior.score}, AAA: ${prior.is_aaa}${item.kind === 'system' ? `, gate_can_fail: ${prior.gate_can_fail}` : ''}
  worst defect: ${prior.worst_defect || '-'}
  it says the fix is: ${prior.what_would_fix_it || '-'}
  its reasoning: ${String(prior.why || '-').slice(0, 900)}
ANSWER THAT. Do not re-do what you already did.
` : ''

  if (item.kind === 'craft') {
    return head + priorBlock + `
THE JOB: make this subsystem look AAA, then PROVE it by handing a hostile critic two unlabelled frames
and having it pick yours WITHOUT knowing which is which.

1. **Render the BEFORE frames first, at the rubric's three distances**, before you change a line.
   The subject's own size derives the distances: NORMAL is where the subject fills the frame width,
   HALF is half that, and the third is the one-pixel-of-silhouette test — if that exceeds the station's
   longest sightline, say so WITH THE ARITHMETIC and substitute the longest view a player actually has.
     \`tools/render_godot.sh ${item.shot} --res 1280x720 --out <path>\`
   plus \`--eye x,y,z --target x,y,z\` where the shot takes them.

2. **CHECK THE RENDERER SAID Forward+.** A whole session of visual judgement was lost to a container
   that fell back to OpenGL 3 Compatibility, printed the warning inside several hundred lines of ALSA
   noise, and EXITED 0 WITH A PNG. Grep every render's own stdout for \`Vulkan\` and \`Forward+\`.
   If a run says OpenGL 3, DESTROY the PNG and fix the environment before judging anything.

3. **Rework it** against \`reference/\` and \`canon/00-MASTER.md\`, not memory.

4. **Render the AFTER frames at the IDENTICAL cameras.** Same eye, same target, same resolution, same
   lens. A frame at a different camera is not a comparison.

5. **Hand them over blind.** Copy the pairs into \`scratchpad/blind/${item.key}/r${round}/\` as
   \`left-<distance>.png\` and \`right-<distance>.png\`. YOU choose which side is your new build.
   **Write the mapping NOWHERE on disk** — not in a log, a commit message, a filename or a note. It
   goes back only in your structured return as \`after_is\`. If the mapping leaks, this is worthless.

THE BAR, from the rubric, and it is what you are judged against:
  craft 3 = "reads as the intended object at its normal distance and FALLS APART AT HALF OF IT"
  craft 4 = "holds at every distance the player can reach it from, and the detail is FUNCTIONAL — a
             fitting is where a fitting would be needed. Wear, grime and lighting response VARY across
             the surface rather than being uniform. The composition holds."
  craft 5 = "survives being looked at deliberately. Nothing in frame repeats in a way the eye can
             index. The form is legible from shading alone."
You are aiming for 4 and you will be told if you got 3.

Return the structured object. \`after_is\` decides whether this round counted.`
  }

  return head + priorBlock + `
THE JOB: make this system actually WORK, then hand a hostile verifier a command that proves it — and
that verifier will RUN IT ITSELF rather than believe your report.

ACCEPTANCE, and it is the thing you are being judged on:
${item.acceptance}

1. **Measure BEFORE.** Run \`${item.gate}\` and keep the verbatim output. A diff of two failed runs is
   not a pass — this project once recorded an A/B as IDENTICAL when both halves had died on the same
   IndexError and written empty files. Assert both runs produced output.

2. **Build it.** Read the shape of the failing number before its size: a number that fails evenly is a
   list of jobs; a number that fails 100% on one side of a line and 1% on the other is a STRUCTURAL
   fact and usually one function with one caller. This project closed 84 failures with one extraction
   by reading that split.

3. **Wire it to the SHIPPED path.** Finished, tested machinery with no caller has happened NINE times
   here, and the ninth slipped past the static scan built to catch the eighth — a loader placed in
   \`walk.gd::_load_level\`, which the shipped STREAMED build never runs. Run \`python3 tools/wiring.py
   --selftest\`. Then go one level lower and LAUNCH THE THING and grep for the line your code prints.
   A static scan tells you a caller exists; only running it tells you the caller runs.

4. **Measure AFTER, with the same command**, and break it deliberately to show the gate catching it.

Return the structured object. \`gate_cmd\` must be a command the critic can run from /home/user/Opus-5
with no arguments of its own.`
}

function craftJudgePrompt(item, blindDir) {
  return `You are a HOSTILE ART CRITIC on a Babylon 5 station simulation. You did not build any of this
and you are not here to be encouraging.

In \`/home/user/Opus-5/${blindDir}\` there are pairs of PNG frames: \`left-<distance>.png\` and
\`right-<distance>.png\`, one pair per viewing distance. **One side is an older build of the same
subsystem and one side is a newer one. You are not being told which.** Read every image with the Read
tool and look at them properly, at every distance.

Your job, in this order:

1. **Say which side looks better, and mean it.** \`left\`, \`right\`, or \`indistinguishable\` — and
   \`indistinguishable\` is a real answer you should use when it is true. If the difference is a
   rounding error, say so. A critic who always finds an improvement is as useless as one who never does.

2. **Say WHY, in pixels and forms, per distance.** Not "more detailed". Which surfaces gained
   articulation, which silhouettes changed, where the eye now rests, what is still flat. Name what you
   are looking at.

3. **Then answer the only question that matters: would you accept the better of these two in a shipped
   AAA game?** The bar is \`/home/user/Opus-5/docs/AAA-STANDARD.md\`'s CRAFT descriptors — READ THAT
   FILE. craft 4 is "holds at every distance the player can reach it from, the detail is FUNCTIONAL,
   wear and lighting response VARY across the surface rather than being uniform". craft 3 is "reads as
   the intended object at its normal distance and FALLS APART AT HALF OF IT". **Default to NO.** Most
   things are a 3 and the honest answer is usually 3.

4. **Name the single worst remaining defect and what would fix it** — concretely, naming a file or a
   parameter, so the builder can act on it rather than admire it. The source is \`${item.owns}\`.

RULES, and they are what make your verdict worth anything:
  * **DO NOT PEEK.** Do not run \`git log\`, \`git diff\`, \`git show\`; do not read
    \`scratchpad/aaa-4t-*\`; do not read the build agent's notes; do not look at file mtimes; do not
    search the repo for anything that would tell you which side is new. Decide from the images. Set
    \`did_not_peek: false\` if you looked at anything that could have told you, and say what.
  * Reading \`docs/AAA-STANDARD.md\` and \`reference/\` is REQUIRED and is not peeking — the reference
    is what fidelity is judged against. Era lock is SEASON 2-3.
  * You may not be agreeable. CLAUDE.md: *"The reviewer's job is to be THE REASON this is good, not to
    be agreeable. It assumes a defect is present and goes looking."*
  * Every claim cites what you looked at.

Return the structured verdict.`
}

function systemJudgePrompt(item, built) {
  return `You are a HOSTILE VERIFIER on a Babylon 5 station simulation at /home/user/Opus-5. You did not
build any of this. Your job is to find out whether a claim is TRUE, and this project's entire history
says the claim will be *nearly* true in a way that matters.

THE CLAIM. A build agent says it fixed **${item.key}** and that this proves it:
    ${built.gate_cmd || item.gate}
It reports BEFORE: ${String(built.before_result || '-').slice(0, 700)}
It reports AFTER:  ${String(built.after_result || '-').slice(0, 700)}
It says it changed: ${String(built.changed || '-').slice(0, 900)}
It says its negative control was: ${String(built.negative_control || '-').slice(0, 700)}

THE ACCEPTANCE IT WAS BUILDING AGAINST:
${item.acceptance}

DO THIS, IN THIS ORDER, AND DO NOT TAKE THE REPORT AT FACE VALUE:

1. **RUN THE COMMAND YOURSELF** and put what it actually printed into \`ran_it\`. MASTER-PLAN R6: *"A
   static scan can tell you a caller exists; only running the thing tells you the caller runs."* If the
   output disagrees with the report in any particular, that is your finding and it outranks everything
   else. If the command does not exist or does not run, say exactly that.
   (Do NOT run \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\` or \`budget.py\` unless the
   gate itself is one of them — four cores, other agents live.)

2. **TRY TO MAKE THE GATE PASS ON CONTENT THAT SHOULD FAIL IT.** This is the highest-yield thing you
   can do. Nine times in this project a subsystem was finished, tested, gated and had NO CALLER on the
   shipped path, and every gate passed because *"every gate here scores a PART against a standard, and
   a part with no caller still meets its standard."* So: break the content the gate is supposed to
   protect and check the gate goes red. If it stays green, the gate is decoration. Set
   \`gate_can_fail\` from what YOU observed, not from what the builder reported.

3. **CHECK IT REACHES THE SHIPPED PATH.** Run \`python3 tools/wiring.py --selftest\`. Know its ceiling:
   it finds a REFERENCE in source and cannot see which branch runs — the ninth instance slipped under
   it exactly there, because the loader was added to \`walk.gd::_load_level\` and the shipped scene is
   STREAMED, so \`_load_level\` never runs. Ask specifically: does the code path the player is actually
   on reach this change?

4. **CHECK NOTHING WAS EDITED TO MAKE SOMETHING ELSE PASS.** For spec work, R1's rule is absolute:
   *"is the spec wrong or the station? Neither may be edited to make the other pass."* Use
   \`git diff\` — you are ALLOWED to peek, you are not judging a picture — and if a floor, a tolerance,
   an assertion or a spec row was weakened rather than met, say so plainly. That is a finding, not a nit.

5. **THEN JUDGE.** Would you accept this in a shipped AAA game? The bar is
   \`/home/user/Opus-5/docs/AAA-STANDARD.md\` — READ IT — and for a system the dimension is ROBUSTNESS:
   4 is "handles the cases it will actually meet, fails legibly, and its failure is gated"; 3 is "works
   on the happy path". **Default to NO.** Score 0-5 in \`score\`.

6. **Name the single worst remaining defect and what would fix it**, concretely, naming a file or a
   parameter. The source is \`${item.owns}\`.

You may not be agreeable. Every claim you make cites the command you ran or the line you read.
Return the structured verdict.`
}

// ---------------------------------------------------------------------------
// build -> hostile judge -> loop while the critic is not convinced.
// pipeline(), not parallel(): concurrency here is min(16, nproc-2) = 2, so a
// deep queue drains steadily and every item that finishes is BANKED, whereas a
// wide barrier holds every result hostage to the slowest one and loses all of
// it to a container recycle. This container has recycled four times.
// ---------------------------------------------------------------------------
const results = await pipeline(
  ITEMS,
  async (item) => {
    const rounds = []
    let prior = null
    for (let r = 1; r <= MAX_ROUNDS; r++) {
      const built = await agent(buildPrompt(item, r, prior), {
        label: `build:${item.key}:r${r}`,
        phase: 'Build',
        schema: BUILD_SCHEMA,
        effort: 'high',
      })
      if (!built || !built.ok) {
        rounds.push({ round: r, built, verdict: null, converged: false })
        log(`${item.key} r${r}: build produced nothing judgeable`
          + (built && built.notes ? ` — ${String(built.notes).slice(0, 200)}` : ''))
        break
      }
      if (item.kind === 'craft' && built.forward_plus === false) {
        rounds.push({ round: r, built, verdict: null, converged: false,
                      why: 'renderer fell back off Forward+ — frames are not judgeable' })
        log(`${item.key} r${r}: RENDERER FELL BACK OFF Forward+ — frames not judgeable`)
        break
      }
      const verdict = await agent(
        item.kind === 'craft' ? craftJudgePrompt(item, built.blind_dir) : systemJudgePrompt(item, built),
        { label: `judge:${item.key}:r${r}`, phase: 'Judge', schema: VERDICT_SCHEMA, effort: 'high' },
      )
      // For craft, the critic must pick the new frame blind AND call it AAA.
      // For a system, there is nothing to pick: it must run the thing, accept
      // it, AND have satisfied itself the gate can fail.
      const correct = item.kind === 'craft'
        ? (!!verdict && verdict.pick === built.after_is)
        : (!!verdict && verdict.gate_can_fail === true)
      const converged = !!verdict && verdict.is_aaa === true && correct
      rounds.push({ round: r, built, verdict, correct, converged })
      log(item.kind === 'craft'
        ? `${item.key} r${r}: critic picked ${verdict ? verdict.pick : '?'} (new build was ${built.after_is}) — `
          + `${correct ? 'IT PICKED THE NEW ONE' : 'it did not'}, craft ${verdict ? verdict.score : '?'}, AAA ${verdict ? verdict.is_aaa : '?'}`
        : `${item.key} r${r}: verifier ran it — gate_can_fail ${verdict ? verdict.gate_can_fail : '?'}, `
          + `robustness ${verdict ? verdict.score : '?'}, AAA ${verdict ? verdict.is_aaa : '?'}`)
      if (converged) break
      prior = verdict ? { ...verdict, correct } : null
    }
    return { key: item.key, kind: item.kind, owns: item.owns, rounds }
  },
)

phase('Synthesis')

const done = results.filter(Boolean)
const converged = done.filter(r => r.rounds.some(x => x.converged))
const won = done.filter(r => r.rounds.some(x => x.correct))
const stuck = done.filter(r => !r.rounds.some(x => x.correct))

log(`${converged.length} of ${done.length} convinced the critic AND cleared the AAA bar; `
  + `${won.length} at least satisfied the critic's own check`)

const table = done.map(r => {
  const last = r.rounds[r.rounds.length - 1] || {}
  const v = last.verdict || {}
  const b = last.built || {}
  return {
    key: r.key,
    kind: r.kind,
    rounds: r.rounds.length,
    converged: r.rounds.some(x => x.converged),
    critic_check_passed: !!last.correct,
    pick: v.pick || '-',
    confidence: v.confidence || '-',
    score: v.score === undefined ? null : v.score,
    is_aaa: !!v.is_aaa,
    gate_can_fail: v.gate_can_fail === undefined ? null : v.gate_can_fail,
    did_not_peek: v.did_not_peek === undefined ? null : v.did_not_peek,
    ran_it: String(v.ran_it || '-').slice(0, 500),
    worst_defect: v.worst_defect || '-',
    what_would_fix_it: v.what_would_fix_it || '-',
    changed: String(b.changed || '-').slice(0, 500),
    before_result: String(b.before_result || '-').slice(0, 300),
    after_result: String(b.after_result || '-').slice(0, 300),
    inv_entries: b.inv_entries || '-',
    pushed: b.pushed || '-',
    blind_dir: b.blind_dir || '-',
    notes: String(b.notes || '-').slice(0, 500),
  }
})

return {
  summary: `${converged.length}/${done.length} converged, ${won.length}/${done.length} passed the critic's own check`,
  converged: converged.map(r => r.key),
  still_short: stuck.map(r => r.key),
  table,
}
