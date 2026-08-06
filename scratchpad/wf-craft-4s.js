export const meta = {
  name: 'craft-4s-blind-loop',
  description: 'Rework the five lowest-craft subsystems and prove each improved by BLIND side-by-side judgement, looping until the critic picks the new frame',
  whenToUse: 'Owner asked for AAA craft on every subsystem, verified by a harsh critic comparing frames blind',
  phases: [
    { title: 'Build', detail: 'one agent per subsystem: render BEFORE at three distances, rework, render AFTER, hand both over blind' },
    { title: 'Judge', detail: 'a hostile critic sees two unlabelled frames and must say which is better and whether it is AAA' },
    { title: 'Synthesis', detail: 'what converged, what did not, and what the critic would not accept' },
  ],
}

// ---------------------------------------------------------------------------
// THE FIVE, AND WHY FIVE RATHER THAN THE SIX THE SCORECARD RANKS.
// `observation_domes` and `observation_rotunda` are two scorecard rows and ONE
// source file, so they are one agent: two agents in station/observation.py at
// once is the stomped-artefact defect CLAUDE.md records three times.
// File lists below are disjoint and were checked for that, not assumed.
//
// THIS SCRIPT LIVES IN THE REPO, not in /tmp, because the container recycled
// twice today and wiped /tmp both times along with the first copy of it.
// ---------------------------------------------------------------------------
const ITEMS = [
  {
    key: 'generated_rooms',
    owns: 'station/rooms.py, station/dressing.py',
    scores: 'craft 3, fidelity 2, performance 4, robustness 4 (3 rounds)',
    why: 'IT IS 58% OF THE STATION. Session 3r scored it craft 1 with "flat panels, blown-out lights, a counter slab"; it is 3 now and its FIDELITY is 2, the joint-lowest on the board. Every generic room a player walks into is this file.',
    shot: '--shot deck --deck blue/0/0 --at docking_bays',
  },
  {
    key: 'npc_bodies',
    owns: 'station/npc/body.py, station/npc/costume.py',
    scores: 'craft 2, fidelity 2, performance 2, robustness 2 (2 rounds)',
    why: 'THE LOWEST ROW ON THE BOARD ON EVERY DIMENSION. These are the people. A station of 250,000 whose inhabitants read as mannequins fails the owner brief harder than any wall does.',
    shot: '--shot deck --deck blue/0/0 --at docking_bays',
  },
  {
    key: 'interior_lighting_4b',
    owns: 'station/export_scene.py (the interior light rig and ROOM_EXPOSURE)',
    scores: 'craft 2, fidelity 2, performance 4, robustness 4 (1 round)',
    why: 'Layer 4b stands at 13 of 23 on the DISTRIBUTION test. STATE.md records what the shadows actually are, measured: fixture energy is INERT (0 -> 2.0 moves p5 by x1.0000), the soft fill nearly so, and AMBIENT OWNS p5 (1.30 -> 2.60 moves it x2.35). Ambient buys level and spends contrast. The rooms are FLAT and that is a rig problem, not a geometry problem.',
    shot: '--shot interior --room zocalo',
  },
  {
    key: 'observation',
    owns: 'station/observation.py (BOTH observation_domes and observation_rotunda)',
    scores: 'domes craft 2 fid 3 perf 4 rob 4; rotunda craft 2 fid 3 perf 3 rob 4',
    why: 'The rotunda round 1 logged 489 non-manifold edges and a window that renders BLACK because --shot interior has no exterior behind it. A window onto space that shows nothing is the single most Babylon 5 thing on the station failing.',
    shot: '--shot interior --room obs_dome_1',
  },
  {
    key: 'drum_interior_engine',
    owns: 'station/drum_ground.py, station/drum_dressing.py',
    scores: 'craft 2, fidelity 3, performance 4, robustness 3 (1 round)',
    why: 'The payoff view of the whole station: ground curving up and away, the far side arching overhead. Its own round-1 note says it works AT DISTANCE and STATE.md 24.4b says it is "still bare underfoot". It is the shot a player remembers.',
    shot: '--shot drum --stand 20,4700 --look 20,6300',
  },
]

// REQUIRED IS DELIBERATELY SHORT. The first run of this workflow died with all
// five agents unable to return anything: a misconfigured permission layer
// stripped the parameters off every tool call including StructuredOutput, and a
// nine-field `required` meant every retry failed on nine counts instead of
// letting a blocked agent say "I am blocked". Only the fields the control flow
// actually branches on are required.
const BUILD_SCHEMA = {
  type: 'object',
  required: ['key', 'ok', 'after_is', 'blind_dir', 'forward_plus'],
  properties: {
    key: { type: 'string' },
    ok: { type: 'boolean', description: 'false if you could not render or could not change anything' },
    blind_dir: { type: 'string', description: 'directory holding left-*.png and right-*.png, one pair per distance' },
    after_is: { type: 'string', enum: ['left', 'right'], description: 'which side is YOUR NEW build. Do not write this anywhere on disk.' },
    distances: { type: 'array', items: { type: 'string' }, description: 'the distance labels with the metres and how each was derived' },
    changed: { type: 'string', description: 'what you actually changed, concretely' },
    forward_plus: { type: 'boolean', description: 'did EVERY render log say Vulkan ... Forward+ (not OpenGL 3 Compatibility)' },
    gates: { type: 'string', description: 'the self-tests you ran and their before/after counts' },
    tris_before: { type: 'number' },
    tris_after: { type: 'number' },
    pushed: { type: 'string', description: 'the commit sha you pushed to origin, or why you could not' },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['pick', 'is_aaa', 'craft_score'],
  properties: {
    pick: { type: 'string', enum: ['left', 'right', 'indistinguishable'] },
    confidence: { type: 'string', enum: ['certain', 'likely', 'marginal'] },
    why: { type: 'string', description: 'the specific pixels/forms that decided it, per distance' },
    is_aaa: { type: 'boolean', description: 'would you accept the better of these two in a shipped AAA game. Default NO.' },
    craft_score: { type: 'integer', minimum: 0, maximum: 5 },
    worst_defect: { type: 'string' },
    what_would_fix_it: { type: 'string', description: 'concrete, buildable, naming the file or the parameter' },
    did_not_peek: { type: 'boolean', description: 'true only if you did NOT read git log/diff, the build agent notes, or anything naming which side is new' },
  },
}

const MAX_ROUNDS = 2

function buildPrompt(item, round, prior) {
  return `You are a BUILD agent on the Babylon 5 station simulation at /home/user/Opus-5, branch \`claude/continue-full-steam-rrzn0t\`.

FIRST, read in this order and follow them — they override your defaults:
  1. /home/user/Opus-5/CLAUDE.md (the working agreement)
  2. /home/user/Opus-5/docs/AAA-STANDARD.md (the rubric, the three distances, the descriptors)

YOUR SUBSYSTEM: **${item.key}**
YOU OWN, AND ONLY: ${item.owns}
Current scorecard: ${item.scores}
Why it was chosen: ${item.why}
${prior ? `\nROUND ${round}. THE CRITIC REJECTED YOUR LAST ROUND. Its verdict, and it did not know which frame was yours:\n  picked: ${prior.pick} (${prior.confidence || '-'}) — ${prior.correct ? 'that WAS your new build' : 'that was the OLD build, or it could not tell'}\n  craft ${prior.craft_score}, AAA: ${prior.is_aaa}\n  worst defect: ${prior.worst_defect || '-'}\n  it says the fix is: ${prior.what_would_fix_it || '-'}\n  its reasoning: ${prior.why || '-'}\nAnswer that. Do not re-do what you already did.\n` : ''}
THE JOB: make this subsystem look AAA, then PROVE it by handing a hostile critic two unlabelled frames and having it pick yours without knowing which is which.

HOW, exactly:

1. **Work in a \`git worktree\`** off the current HEAD of \`claude/continue-full-steam-rrzn0t\`. Four other build agents are live in the same repository and \`tools/render_godot.sh\` rewrites \`station/generated/scene/*\` on every run. This is not optional — CLAUDE.md records a gate timing out at 1800 s and an agent dying mid-flight from exactly this.

2. **Render the BEFORE frames first, at the rubric's three distances**, before you change a line. The subject's own size derives the distances: NORMAL is where the subject fills the frame width, HALF is half that, and the third is the one-pixel-of-silhouette test — if that distance exceeds the station's own longest sightline, say so with the arithmetic and substitute the longest view a player actually has. Command shape:
     \`tools/render_godot.sh ${item.shot} --res 1280x720 --out <path>\`
   plus \`--eye x,y,z --target x,y,z\` (passed through to tools/export_scene.py) where the shot takes them.

3. **CHECK THE RENDERER SAID Forward+.** CLAUDE.md records a whole session of visual judgement lost because the container fell back to OpenGL 3 Compatibility, printed a warning inside several hundred lines of ALSA noise, and exited 0 with a PNG. Grep every render's own stdout for \`Vulkan\` and \`Forward+\`. If a run says OpenGL 3, DESTROY the PNG and fix the environment before judging anything.

4. **Rework it.** Read the reference material the subsystem cites (\`reference/\`, \`canon/00-MASTER.md\`) and build against measurements, not memory. Hard rule 1: every number traces to a source or gets a \`## INV-<n>\` entry in \`canon/INVENTIONS.md\` with what/why/what-constrained-it/what-would-overturn-it. Check the highest INV number first and leave a gap of at least 10 above it — four other agents are allocating.

5. **Render the AFTER frames at the IDENTICAL cameras.** Same eye, same target, same resolution, same lens. A frame at a different camera is not a comparison.

6. **Hand them over blind.** Copy the pairs into \`scratchpad/blind/${item.key}/r${round}/\` as \`left-<distance>.png\` and \`right-<distance>.png\`. YOU choose which side is your new build. **Write the mapping NOWHERE on disk** — not in a log, not in a commit message, not in a filename, not in a note. It goes back only in your structured return value as \`after_is\`. If the mapping leaks, the whole exercise is worthless.

7. **Run the gates** your files own (the module's own \`--selftest\`, plus \`python3 tools/inv_check.py\`) and quote before/after counts. Do NOT run \`deck.py --sweep\`, \`rooms.py --footprint\`, \`walkable.py\` or \`budget.py\` — four agents on a four-core box, and CLAUDE.md records two agents dying of exactly that contention.

8. **PUSH to \`origin claude/continue-full-steam-rrzn0t\` — do not merely commit, and push EARLY and OFTEN rather than once at the end.** This container has recycled twice today; each recycle rolled the checkout back hours and deleted every worktree. An agent doing exactly your job lost its entire run that way this morning, because it had committed inside a worktree that then ceased to exist. **A commit in a container that rolls back is a commit that never happened.** Push a checkpoint as soon as you have anything worth keeping, then again whenever you land something. Stage paths BY NAME — never \`git add -A\`, four agents share this index. Do not open a PR. Do not write to \`docs/aaa-scorecard.json\` — put any scores in \`scratchpad/craft-4s-${item.key}.json\` instead.

9. **IF THE HARNESS BLOCKS YOU, SAY SO AND STOP.** The previous run of this exact workflow died with every tool call rejected before execution by a misconfigured permission layer (\`The permission handler returned updatedInput for <Tool> that failed schema validation ... The required parameter is missing ... The tool input from the model was valid\`). If that happens to you, return \`ok: false\` with the verbatim error in \`notes\` and do not burn context retrying — it is an environment fault and not yours to fix.

WHAT AAA MEANS HERE, from the rubric, and it is the bar you are being judged against:
  craft 3 = "reads as the intended object at its normal distance and FALLS APART AT HALF OF IT"
  craft 4 = "holds at every distance the player can reach it from, and the detail is FUNCTIONAL — a fitting is where a fitting would be needed. Wear, grime and lighting response VARY across the surface rather than being uniform. The composition holds."
  craft 5 = "survives being looked at deliberately. Nothing in frame repeats in a way the eye can index. The form is legible from shading alone."
You are aiming for 4 and you will be told if you got 3.

Return the structured object. \`after_is\` decides whether this round counted.`
}

function judgePrompt(item, blindDir) {
  return `You are a HOSTILE ART CRITIC on a Babylon 5 station simulation. You did not build any of this and you are not here to be encouraging.

In \`/home/user/Opus-5/${blindDir}\` there are pairs of PNG frames: \`left-<distance>.png\` and \`right-<distance>.png\`, one pair per viewing distance. **One side is an older build of the same subsystem and one side is a newer one. You are not being told which.** Read every image with the Read tool and look at them properly, at every distance.

Your job, in this order:

1. **Say which side looks better, and mean it.** \`left\`, \`right\`, or \`indistinguishable\` — and \`indistinguishable\` is a real answer you should use when it is true. If the difference is a rounding error, say so; a critic who always finds an improvement is as useless as one who never does.

2. **Say WHY, in pixels and forms, per distance.** Not "more detailed". Which surfaces gained articulation, which silhouettes changed, where the eye now rests, what is still flat. Name what you are looking at.

3. **Then answer the only question that matters: would you accept the better of these two in a shipped AAA game?** The bar is \`/home/user/Opus-5/docs/AAA-STANDARD.md\`'s CRAFT descriptors — READ THAT FILE. craft 4 is "holds at every distance the player can reach it from, the detail is FUNCTIONAL, wear and lighting response VARY across the surface rather than being uniform". craft 3 is "reads as the intended object at its normal distance and FALLS APART AT HALF OF IT". **Default to NO.** Most things are a 3 and the honest answer is usually 3.

4. **Name the single worst remaining defect and what would fix it** — concretely, naming a file or a parameter, so the builder can act on it rather than admire it. The relevant source is \`${item.owns}\`.

RULES, and they are what make your verdict worth anything:
  * **DO NOT PEEK.** Do not run \`git log\`, \`git diff\`, \`git show\`, do not read \`scratchpad/craft-4s-*\`, do not read the build agent's notes, do not look at file mtimes, do not search the repo for anything that would tell you which side is new. Decide from the images. Set \`did_not_peek: false\` if you looked at anything that could have told you, and say what.
  * Reading \`docs/AAA-STANDARD.md\` and the \`reference/\` folder is REQUIRED and does not count as peeking — the reference is what fidelity is judged against.
  * You may not be agreeable. CLAUDE.md: *"The reviewer's job is to be THE REASON this is good, not to be agreeable. It assumes a defect is present and goes looking."*
  * Every claim cites what you looked at.

Return the structured verdict.`
}

// ---------------------------------------------------------------------------
// build -> blind judge -> loop while the critic is not convinced
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
        log(`${item.key} r${r}: build did not produce a comparison`
          + (built && built.notes ? ` — ${String(built.notes).slice(0, 160)}` : ''))
        break
      }
      if (built.forward_plus === false) {
        rounds.push({ round: r, built, verdict: null, converged: false,
                      why: 'renderer fell back off Forward+ — frames are not judgeable' })
        log(`${item.key} r${r}: RENDERER FELL BACK — frames not judgeable`)
        break
      }
      const verdict = await agent(judgePrompt(item, built.blind_dir), {
        label: `judge:${item.key}:r${r}`,
        phase: 'Judge',
        schema: VERDICT_SCHEMA,
        effort: 'high',
      })
      const correct = !!verdict && verdict.pick === built.after_is
      const converged = correct && !!verdict.is_aaa
      rounds.push({ round: r, built, verdict, correct, converged })
      log(`${item.key} r${r}: critic picked ${verdict ? verdict.pick : '?'} `
        + `(new build was ${built.after_is}) — ${correct ? 'IT PICKED THE NEW ONE' : 'it did not'}`
        + `, craft ${verdict ? verdict.craft_score : '?'}, AAA ${verdict ? verdict.is_aaa : '?'}`)
      if (converged) break
      prior = verdict ? { ...verdict, correct } : null
    }
    return { key: item.key, owns: item.owns, rounds }
  },
)

phase('Synthesis')

const done = results.filter(Boolean)
const converged = done.filter(r => r.rounds.some(x => x.converged))
const improved = done.filter(r => r.rounds.some(x => x.correct))
const stuck = done.filter(r => !r.rounds.some(x => x.correct))

log(`${converged.length} of ${done.length} convinced the critic AND cleared AAA; `
  + `${improved.length} were picked out blind as the better frame`)

const table = done.map(r => {
  const last = r.rounds[r.rounds.length - 1] || {}
  const v = last.verdict || {}
  const b = last.built || {}
  return {
    key: r.key,
    rounds: r.rounds.length,
    critic_picked_the_new_build: !!last.correct,
    confidence: v.confidence || '-',
    craft: v.craft_score === undefined ? null : v.craft_score,
    is_aaa: !!v.is_aaa,
    did_not_peek: v.did_not_peek === undefined ? null : v.did_not_peek,
    worst_defect: v.worst_defect || '-',
    what_would_fix_it: v.what_would_fix_it || '-',
    changed: b.changed || '-',
    pushed: b.pushed || '-',
    blind_dir: b.blind_dir || '-',
    notes: b.notes || '-',
  }
})

return {
  summary: `${converged.length}/${done.length} converged, ${improved.length}/${done.length} won the blind pick`,
  converged: converged.map(r => r.key),
  still_short: stuck.map(r => r.key),
  table,
}
