#!/usr/bin/env bash
# BUILD SOMETHING A STRANGER CAN RUN. One command, one artefact, one launcher.
#
#   bash tools/package.sh              # build dist/Babylon5-linux-x86_64.tar.gz
#   bash tools/package.sh --check      # say what is present and what is missing;
#                                      #   build nothing, exit non-zero if the
#                                      #   result would not be runnable
#   bash tools/package.sh --readers    # the DERIVED list of every out-of-res
#                                      #   path an engine script reads, and
#                                      #   whether the staging table covers it.
#                                      #   Seconds, no engine, no build.
#   bash tools/package.sh --no-diff    # skip the source-tree differential (~25 s
#                                      #   faster; the named assertions still hold)
#   bash tools/package.sh --no-data    # engine + scripts only (fast; NOT playable)
#   bash tools/package.sh --no-tar     # leave the tree in dist/, skip the tarball
#
# WHY THIS EXISTS. `docs/MASTER-PLAN.md` A2's definition of done opens: *"a
# stranger downloads ONE FILE, runs it at 60 fps, arrives at Babylon 5 as a
# person with papers."* Measured at the start of session 4t:
# `godot/export_presets.cfg` did not exist, there was no title screen, and
# `tools/` had no packaging path. **There was no way for a person to start
# this.** Every other item in every batch improved something a player could not
# reach.
#
# ---------------------------------------------------------------------------
# THE THREE FACTS THAT SHAPE THIS SCRIPT. Each one is measured on this box, and
# each one is a trap that a naive `godot --export-release` walks straight into.
# ---------------------------------------------------------------------------
#
# 1. THE WORLD IS NOT INSIDE res://, SO NO PRESET CAN PACK IT.
#    `godot/scripts/main.gd::_root()` is `globalize_path("res://") + ".."`, and
#    every deck mesh, collision shell, interactables sidecar, arrival sequence,
#    cell set, audio bank and vista manifest is read from
#    `<root>/station/generated/...`. Godot's exporter walks `res://` and nothing
#    above it, so an export of this project is the ENGINE plus the SCRIPTS and
#    nothing else -- 112 MB of a game whose world is 669 MB. This script stages
#    the data tree beside the binary so that `res://..` resolves in the shipped
#    layout exactly as it does in the source tree:
#
#        Babylon5/
#          game/Babylon5.x86_64      the engine
#          game/Babylon5.pck         the scripts, scenes and materials
#          station/generated/...     the world       <- res://.. finds this
#          Babylon5                  the launcher
#
#    Verified rather than assumed: an export staged WITHOUT the data tree boots
#    to `ERROR: main: no boot manifest` and exits 2, which is `--no-data`, which
#    is this script's own negative control.
#
# 2. THERE ARE NO EXPORT TEMPLATES ON THIS BOX, AND THE STOCK ONES WOULD BE
#    WRONG ANYWAY. `~/.local/share/godot/export_templates/` is empty, so
#    `--export-release` cannot produce a binary. It would not be the right
#    binary if it could: `project.godot` declares `config/features=... "Double
#    Precision"` because the station is 8,047 m long and float32 jitters
#    visibly at that scale (`docs/adr/0001-engine-choice.md`), and Godot's
#    published templates are single precision. So the default path here is
#    `--export-pack`, which needs no template at all, plus the double-precision
#    engine binary this project already builds, renamed beside the pack --
#    Godot loads `<exe_basename>.pck` automatically and runs it as a game.
#    Measured: it does, and it reaches `main.gd::_ready`.
#
#    If a double-precision template ever appears, set GODOT_TEMPLATE=<path> and
#    this script exports a single self-contained binary instead. It reports
#    which of the two it did, on every run, in its own output -- CLAUDE.md's
#    render-fallback rule: *"any tool that can substitute a lesser mode for the
#    one asked for must say which one it used, in its output, on every run."*
#
# 3. A PACKAGING STEP THAT SILENTLY PRODUCES NOTHING IS THE FAILURE MODE THIS
#    PROJECT ALREADY PAID FOR. `tools/render_godot.sh` fell back to OpenGL 3
#    Compatibility, printed a warning inside several hundred lines of ALSA
#    noise, and exited 0 with a PNG; ten frames were judged through it. So every
#    step below is checked for its OUTPUT rather than its exit code, the export
#    log is grepped for the engine's own "savepack: end", and the finished
#    artefact is LAUNCHED headlessly and its first lines are read back. If the
#    launch does not print the menu's own banner, this script deletes the
#    tarball and fails.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
NAME="Babylon5"
STAGE="$DIST/$NAME"
PRESET="Linux"
TARBALL="$DIST/$NAME-linux-x86_64.tar.gz"

CHECK=0
WITH_DATA=1
WITH_TAR=1
READERS=0
WITH_DIFF=1
while [ $# -gt 0 ]; do
  case "$1" in
    --check)   CHECK=1 ;;
    --readers) READERS=1 ;;
    --no-diff) WITH_DIFF=0 ;;
    --no-data) WITH_DATA=0 ;;
    --no-tar)  WITH_TAR=0 ;;
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "package: unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done

# ---------------------------------------------------------------------------
# The engine. Same search order as tools/render_godot.sh, and the same hard
# error with the one command that fixes it -- a missing binary otherwise
# surfaces as an exec failure with the cause buried.
# ---------------------------------------------------------------------------
GODOT="${GODOT:-}"
if [ -z "$GODOT" ]; then
  for cand in \
    "/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64" \
    "$(ls -1 /home/user/godot-build/*/bin/godot.linuxbsd.*.double.* 2>/dev/null | head -1)"
  do
    if [ -n "$cand" ] && [ -x "$cand" ]; then GODOT="$cand"; break; fi
  done
fi

# ---------------------------------------------------------------------------
# WHAT THE WORLD IS. Named here as a list rather than "copy station/generated",
# because that tree is 669 MB and most of it is intermediate: .obj files the
# .glb was converted from, per-room renders, scratch. A shipped build carries
# what `main.gd` and `walk.gd` actually open.
#
# EVERY ENTRY IS A PATH SOMETHING IN godot/scripts/ READS, and the comment says
# which file reads it. An entry nobody reads is dead weight in a download; a
# reader with no entry is a build that boots to an error, which is the failure
# this script exists to stop happening silently.
#
# THAT SENTENCE WAS FALSE WHEN IT WAS FIRST WRITTEN, AND THE WAY IT WAS FALSE IS
# THE WHOLE REASON THE GATE BELOW EXISTS. Round 1 of this file hand-wrote eight
# rows, asserted in this very comment that they were every reader, and shipped a
# tarball missing THREE. None of the three boots to an error. All three degrade
# in silence, which is worse:
#
#   tools/export_scene.py     dress_scene.gd parses it for FIXTURE_LIGHTING.
#                             Measured: the packaged customs hall had **0 light
#                             sources** against the source tree's **663**. Every
#                             lamp of layer 4's work, absent from the download,
#                             and the build says `dress: 0 light sources` and
#                             carries on.
#   cell_manifest.json        walk.gd::_derive_omega2 -> stream.gd::deck_row.
#                             Without it branch 4 fires and the body runs at
#                             **9.81 m/s2 with no spin** instead of the ring's
#                             measured **7.455** (floor_g 0.7602 at r=211.55 m).
#                             That is precisely the state walk.gd's own
#                             `--legacy-field` control calls "what the shipped
#                             build did" -- session 4r/INV-451's NEGATIVE CONTROL
#                             was what the tarball actually shipped.
#   station/budget.py         stream.gd::budget_cells.
#
# So the table below is no longer trusted to be complete. `--readers` DERIVES
# the reader list from the engine source -- `tools/wiring.py::engine_reads` for
# the `generated/` half, plus a scan for every other path literal that escapes
# res:// -- and `_reader_gate` refuses to package a build in which any derived
# reader that EXISTS on disk has no staging entry. The table keeps the prose
# (what each absence costs a player, which no scanner can know); the scan keeps
# the table honest. A second hand-maintained copy of a list is exactly the drift
# this project keeps paying for, and this is one list checked against its source
# rather than two lists hoping to agree.
# ---------------------------------------------------------------------------
# AND EACH ONE SAYS WHETHER THE BUILD IS RUNNABLE WITHOUT IT, plus what a
# player loses when it is absent. A flat required-list would refuse to package a
# perfectly playable build over `scene/vista`, which only three places on the
# station consult; a flat optional-list would happily ship a build with no deck.
# The distinction is the whole value of the table -- a precondition that cannot
# distinguish "broken" from "diminished" gets switched off.
#
# "required" NOW MEANS "the build is unrunnable without it", NOT "the build is
# whole without it" -- the two silent readers above are marked `yes` because
# what they cost is not a missing feature, it is a build that lies about being
# complete, and the runlog assertions after the launch enforce both by name.
#
#   path | required | what its absence costs
DATA=(
  "station/generated/scene/boot.json|yes|main.gd::_boot_manifest -- without it the game cannot start at all"
  "station/generated/scene/station|yes|the deck mesh, collision shell, 103 streaming cells, 408 actors, 444 crowd placements, the shared crowd library, dialogue and the arrival sequence"
  "station/generated/scene/deck|no|the single-cluster walk-test deck. NOT what the game boots any more -- boot.json names scene/station -- but walkable.py writes here and a stale boot.json would point at it"
  "tools/export_scene.py|yes|dress_scene.gd's FIXTURE_LIGHTING parse -- without it the build has 0 light sources against 663"
  "station/generated/cell_manifest.json|yes|walk.gd::_derive_omega2 -- without it the body runs at 9.81 m/s2 instead of the ring's 7.455"
  "station/budget.py|no|stream.gd::budget_cells -- the streamer loses its per-cell triangle allowance"
  "station/generated/audio|no|ambience.gd's 13 loops -- the station is silent"
  "station/generated/navgraph.json|no|navgraph.gd -- NPCs cannot route"
  "station/generated/economy.json|no|player.gd::has_purse is false, so tier stays at its sentinel"
  "station/generated/scene/enforcement.json|no|enforcement.gd -- a refusal is reported and NOTHING follows it: no arrest, no fine, no brig"
  "station/generated/scene/npc|no|ragdoll.gd's 14 species bodies -- nobody falls over"
  "station/generated/scene/exterior|no|main.gd::_build_starfury's hull_glb -- the station has no outside to launch from or look at. Marked optional by the rule above (the build still RUNS without it) and it is 32 MB, but it was READ BY main.gd:616 AND STAGED BY NOTHING, which is the exact shape of the defect that shipped an empty station: present on the build box, absent on a stranger's"
  "station/generated/scene/vista|no|vista.gd -- the three windowed rooms show background instead of the station"
  "station/generated/journal.json|no|journal.gd -- nothing is learned or remembered"
)

# ---------------------------------------------------------------------------
# THE DERIVED READER LIST. Printed by `--readers`, consumed by `_reader_gate`.
#
# Two halves, because the engine names an out-of-res path two different ways and
# a scan that knows only one of them is the eight-row table again:
#
#   "…generated/foo.json"      `tools/wiring.py` already resolves these, joined
#                              fragments and all, and is the repository's answer
#                              to "which generated path does an engine script
#                              read". Reusing it is the point: one scanner.
#   "../tools/export_scene.py" wiring.py's regex requires the literal
#   "res://../station/budget.py"  `generated/` in the string, so it cannot see a
#                              read that escapes res:// into `tools/` or into
#                              `station/` above `generated/`. Both of round 1's
#                              worst misses were this form. This half catches
#                              anything shaped `"../…"` or `"res://../…"`.
#
# Comment lines are skipped -- `##` docstrings in these files quote paths as
# prose, and a doc mention is not a read.
#
# Emits one row per reader: <root-relative path>|<0|1 exists>|<file:line>
# ---------------------------------------------------------------------------
readers_scan() {
  python3 - "$ROOT" <<'PY'
import os, re, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "tools"))
import wiring                                    # noqa: E402

rows = {}   # path -> (exists, where)


def add(path, where):
    path = path.strip("/")
    if not path or "." not in os.path.basename(path):
        return                                   # a directory, not a file
    if path in rows:
        return
    rows[path] = (1 if os.path.exists(os.path.join(root, path)) else 0, where)


# --- half one: every generated read, through the repository's own scanner ----
resolved, _dyn = wiring.engine_reads()
for rel in sorted(resolved):
    found = wiring.locate(rel, resolved[rel]["form"])
    add("station/generated/" + (found if found else rel),
        resolved[rel]["where"][0])

# --- half two: every other literal that escapes res:// -----------------------
OUT = re.compile(r'"(?:res://)?\.\./([^"\n]+)"')
for base, dirs, names in os.walk(os.path.join(root, "godot")):
    dirs[:] = [d for d in dirs if d != ".godot"]
    for n in sorted(names):
        if not n.endswith((".gd", ".tscn")):
            continue
        p = os.path.join(base, n)
        rel_f = os.path.relpath(p, root)
        with open(p, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh.read().splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                for m in OUT.finditer(line):
                    add(m.group(1), "%s:%d" % (rel_f, i))

for path in sorted(rows):
    exists, where = rows[path]
    print("%s|%d|%s" % (path, exists, where))
PY
}

# Is this derived reader inside something the DATA table stages? Exact match or
# a directory prefix -- `station/generated/scene/deck` covers every file under
# it, which is how one row stages seven.
_covered() {
  local p="$1" row d
  for row in "${DATA[@]}"; do
    d="${row%%|*}"
    [ "$p" = "$d" ] && return 0
    case "$p" in "$d"/*) return 0 ;; esac
  done
  return 1
}

# THE GATE. A reader that exists on disk and is staged by nothing is a build
# that will degrade silently on a stranger's machine, and this refuses to make
# one. A reader that does NOT exist on disk is reported and not fatal: that is
# `tools/wiring.py`'s question (nothing generates it), not this script's, and
# conflating the two would make a packaging step fail for a content gap it
# cannot fix.
_reader_gate() {
  local line p ex where n_ok=0 n_ungen=0
  UNCOVERED=0
  while IFS='|' read -r p ex where; do
    [ -n "$p" ] || continue
    if [ "$ex" = "0" ]; then
      n_ungen=$((n_ungen + 1))
      continue
    fi
    if _covered "$p"; then
      n_ok=$((n_ok + 1))
    else
      UNCOVERED=$((UNCOVERED + 1))
      miss "reader      $p -- READ BY $where AND STAGED BY NOTHING."
      note "            It exists here, so this build would work on THIS box"
      note "            and degrade silently on a stranger's. Add it to DATA."
    fi
  done <<<"$(readers_scan)"
  note "readers     $n_ok of $((n_ok + UNCOVERED)) engine reads that exist on"
  note "            disk are staged; $n_ungen more are read and never generated"
  note "            (tools/wiring.py's question, not this script's)"
}

say() { printf '%s\n' "$*"; }
bad=0
note() { say "  $1"; }
miss() { say "  MISSING  $1"; bad=1; }

say "package: Babylon 5 -- what a stranger would download"
say ""

# --- preconditions, reported as a table so a missing one is legible ---------
if [ -n "$GODOT" ] && [ -x "$GODOT" ]; then
  note "engine      $GODOT"
else
  miss "engine      no double-precision Godot -- run: bash tools/build_godot.sh"
fi
if [ -f "$ROOT/godot/export_presets.cfg" ]; then
  note "preset      godot/export_presets.cfg [$PRESET]"
else
  miss "preset      godot/export_presets.cfg"
fi
if [ -f "$ROOT/godot/scripts/main_menu.gd" ]; then
  note "front door  godot/scripts/main_menu.gd"
else
  miss "front door  godot/scripts/main_menu.gd -- nothing to launch INTO"
fi

# The export template, and the honest report of which mode this run will use.
MODE="pack+engine"
TEMPLATE="${GODOT_TEMPLATE:-}"
if [ -n "$TEMPLATE" ] && [ -f "$TEMPLATE" ]; then
  MODE="export-release"
  note "template    $TEMPLATE  (self-contained binary)"
else
  TPL_DIR="${HOME}/.local/share/godot/export_templates"
  n_tpl=$(ls -1 "$TPL_DIR" 2>/dev/null | wc -l)
  note "template    none ($n_tpl in $TPL_DIR) -- using --export-pack plus the"
  note "            project's own double-precision engine binary. Godot's stock"
  note "            templates are SINGLE precision and would be wrong here."
  note "SUBSTITUTION  mode=pack+engine ships the EDITOR binary as the game."
  note "            game/Babylon5.x86_64 is byte-identical to"
  note "            $(basename "${GODOT:-<none>}"), so \`./Babylon5 -e\` opens the"
  note "            Godot editor on the shipped project. That is not shippable"
  note "            for a title and it is stated here, on every run, rather than"
  note "            discovered by whoever downloads it -- CLAUDE.md's rule that"
  note "            a tool substituting a lesser mode must say which one it used."
  note "            WHAT REMOVES IT: a template_release build of THIS engine at"
  note "            precision=double (\`scons target=template_release\`, ~40 min"
  note "            on 4 cores), then GODOT_TEMPLATE=<path> bash tools/package.sh"
  note "            -- which takes the export-release branch above and produces a"
  note "            single self-contained binary with no editor in it."
fi

if [ "$READERS" -eq 1 ]; then
  say ""
  say "package: every out-of-res path an engine script reads, DERIVED from the"
  say "         engine source rather than read off the table below it."
  say ""
  printf '  %-6s %-8s %-46s %s\n' state staged path "read by"
  while IFS='|' read -r p ex where; do
    [ -n "$p" ] || continue
    st=$([ "$ex" = "1" ] && echo on-disk || echo ABSENT)
    sg=$(_covered "$p" && echo yes || echo "NO")
    printf '  %-6s %-8s %-46s %s\n' "$st" "$sg" "$p" "$where"
  done <<<"$(readers_scan)"
  say ""
  _reader_gate >/dev/null
  say "package: $UNCOVERED reader(s) exist on disk and are staged by nothing."
  [ "$UNCOVERED" -eq 0 ] || exit 1
  exit 0
fi

DIMINISHED=0
if [ "$WITH_DATA" -eq 1 ]; then
  for row in "${DATA[@]}"; do
    d="${row%%|*}"; rest="${row#*|}"; req="${rest%%|*}"; cost="${rest#*|}"
    if [ -e "$ROOT/$d" ]; then
      note "world       $d ($(du -sh "$ROOT/$d" 2>/dev/null | cut -f1))"
    elif [ "$req" = "yes" ]; then
      miss "world       $d -- REQUIRED: $cost"
    else
      DIMINISHED=$((DIMINISHED + 1))
      note "world       $d  ABSENT (optional) -- $cost"
    fi
  done
  # AND THE TABLE ABOVE IS CHECKED AGAINST THE ENGINE RATHER THAN BELIEVED.
  # `miss` sets `bad`, so an unstaged reader refuses the build on the same
  # footing as a missing deck.
  _reader_gate
else
  note "world       SKIPPED (--no-data) -- this build will NOT be playable."
  note "            It is the negative control: it must boot to 'no boot"
  note "            manifest' and exit 2, and package.sh asserts that it does."
fi

say ""
say "package: mode=$MODE  data=$([ "$WITH_DATA" -eq 1 ] && echo yes || echo NO)  diminished_by=$DIMINISHED"

if [ "$CHECK" -eq 1 ]; then
  if [ "$bad" -ne 0 ]; then
    say "package: --check FAILED -- the build above would not be runnable"
    exit 1
  fi
  # SINGLE QUOTES, DELIBERATELY. The first draft of this line used backticks
  # inside a double-quoted string, which is command substitution: --check ran
  # the whole packager as a side effect of describing it.
  say 'package: --check ok -- `bash tools/package.sh` would produce a runnable build'
  exit 0
fi
if [ "$bad" -ne 0 ] && [ "$WITH_DATA" -eq 1 ]; then
  say "package: refusing to build -- see MISSING above"
  exit 1
fi

# ---------------------------------------------------------------------------
# Build.
# ---------------------------------------------------------------------------
rm -rf "$STAGE"
mkdir -p "$STAGE/game"
LOG="$DIST/export.log"

say ""
say "package: exporting res:// ..."
if [ "$MODE" = "export-release" ]; then
  # A template was supplied. The preset's custom_template/release is written
  # into a throwaway copy rather than into the committed file, because an
  # absolute path to somebody's home directory is wrong on every other machine.
  CFG="$ROOT/godot/export_presets.cfg"
  cp "$CFG" "$CFG.pkgbak"
  # shellcheck disable=SC2016
  sed -i "s#^custom_template/release=\"\"#custom_template/release=\"$TEMPLATE\"#" "$CFG"
  set +e
  "$GODOT" --headless --path "$ROOT/godot" \
      --export-release "$PRESET" "$STAGE/game/$NAME.x86_64" >"$LOG" 2>&1
  rc=$?
  set -e
  mv "$CFG.pkgbak" "$CFG"
  [ $rc -eq 0 ] || { say "package: export-release exited $rc -- see $LOG"; exit 1; }
else
  set +e
  "$GODOT" --headless --path "$ROOT/godot" \
      --export-pack "$PRESET" "$STAGE/game/$NAME.pck" >"$LOG" 2>&1
  rc=$?
  set -e
  [ $rc -eq 0 ] || { say "package: export-pack exited $rc -- see $LOG"; exit 1; }
  # THE ENGINE'S OWN REPORT, not this script's opinion of it. An exporter that
  # exited 0 having written nothing is exactly the shape of the render fallback
  # this project spent a session judging frames through.
  grep -q "savepack: end" "$LOG" || {
    say "package: the exporter exited 0 but never said 'savepack: end'."
    say "         That is a silent no-op. See $LOG"
    exit 1
  }
  cp "$GODOT" "$STAGE/game/$NAME.x86_64"
fi
chmod +x "$STAGE/game/$NAME.x86_64"
[ -s "$STAGE/game/$NAME.x86_64" ] || { say "package: no binary produced"; exit 1; }

# --- the world -------------------------------------------------------------
if [ "$WITH_DATA" -eq 1 ]; then
  say "package: staging the world ..."
  for row in "${DATA[@]}"; do
    d="${row%%|*}"
    [ -e "$ROOT/$d" ] || continue
    mkdir -p "$STAGE/$(dirname "$d")"
    cp -r "$ROOT/$d" "$STAGE/$d"
  done
  # AND THE SAME TREE SEEN FROM ONE LEVEL DOWN, because the six raw
  # `globalize_path("res://")` readers do not agree with each other about where
  # the root is, and no single working directory satisfies both forms:
  #
  #   stream.gd, dress_scene.gd, interact.gd, enforcement.gd, ragdoll.gd write
  #     "../station/…"  -> wants cwd = game/
  #   journal.gd:233 computes its root with `.get_base_dir()` -- one level UP --
  #     and then writes "station/generated/journal.json" with no `../` at all
  #     -> wants cwd = the stage root.
  #
  # Found by diffing the packaged run against a source-tree run of the same
  # command, which is the gate below; the named dress/gravity assertions would
  # have shipped this one, because it is a THIRD reader nobody had thought of.
  # Measured: `journal: 8 kinds, 8 ledgers, 62 timed calls ... hash ok` in the
  # source tree against `journal: 0 kinds, 0 ledgers, 0 timed calls ... hash
  # MISMATCH` in the tarball.
  #
  # Two relative symlinks cost nothing, survive `tar`, and make both readings of
  # the root land on one tree. The alternative is a second copy of 324 MB.
  ln -sfn ../station "$STAGE/game/station"
  ln -sfn ../tools   "$STAGE/game/tools"
fi

# --- the launcher ----------------------------------------------------------
# A player runs THIS, not the binary in game/. It passes NO user arguments --
# `main.gd::_front_door` shows the title screen only on a launch with a display
# and no arguments at all, which is precisely what double-clicking is and what
# every developer command line is not.
#
# AND IT `cd`s INTO game/ FIRST, WHICH IS LOAD-BEARING AND WAS THE WHOLE BUG.
# Round 1's launcher said in this comment that it "keeps the working directory
# off the equation". That sentence was the opposite of the truth, and it cost
# the tarball its lighting and its gravity.
#
# `ProjectSettings.globalize_path("res://")` returns "" IN AN EXPORTED BUILD --
# res:// is inside the .pck and has no place on disk. Seven scripts here build
# an out-of-res path from it. **One** of them handles that:
#
#   main.gd:2042        `if base == "": base = OS.get_executable_path()...`
#   dress_scene.gd:121  raw -- so FIXTURE_LIGHTING resolved to the literal
#                       string "../tools/export_scene.py"
#   stream.gd:219       raw -- cell_manifest.json, hence `walk: gravity --
#                       NO SPIN STATED`, hence 9.81 m/s2
#   interact.gd:414     raw -- the economy ledger
#   journal.gd:233      raw -- the journal manifest
#   enforcement.gd:361  raw -- enforcement.json
#   ragdoll.gd:1021     raw -- the ragdoll root
#
# That is 6 of 7 wrong and the 1 that is right is the one anybody ever launched
# from source, which is CLAUDE.md's own "check every site of an idiom" lesson
# arriving by a new route. What all six degrade TO is a path relative to the
# PROCESS WORKING DIRECTORY: `"" .path_join("../tools/x")` is `../tools/x`.
#
# In the source tree res:// IS `<root>/godot/`, so `../tools/x` means
# `<root>/tools/x`. The staged layout mirrors that exactly -- `game/` where
# `godot/` was. So starting the process in `game/` makes all six degraded paths
# land on the staged tree, and the artefact reads the same files the source tree
# does. One `cd` closes six readers without touching a file this agent does not
# own. The proper fix -- a shared `_root()` with main.gd's exported branch, in
# all six -- is written up in `scratchpad/PATCHES-4t-p5_firstrun.md`; it belongs
# to whoever owns those files, and this script's dress/gravity assertions below
# are what will notice if either fix regresses.
cat >"$STAGE/$NAME" <<'LAUNCH'
#!/usr/bin/env bash
# Babylon 5. Run this.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The cd is REQUIRED, not tidiness. See tools/package.sh's launcher comment:
# six scripts resolve their out-of-pack data relative to this directory.
cd "$HERE/game"
exec "$HERE/game/Babylon5.x86_64" "$@"
LAUNCH
chmod +x "$STAGE/$NAME"

cat >"$STAGE/README.txt" <<'DOC'
BABYLON 5 -- a 1:1 simulation of the station. 8,047 m. Season 2-3.

    ./Babylon5

That is the whole of it. You get a title screen; NEW GAME puts you on the
transport deck at customs with an identicard, which is the only thing standing
between you and being put back on a ship.

Layout, and it is not the usual one:

    game/       the engine and the code
    station/    the world -- meshes, collision, the arrival sequence, audio

The world lives OUTSIDE the engine's pack because it is generated rather than
authored, and it is read from disk at runtime. Moving `game/` away from
`station/` breaks the build; keep the folder together.

If the title screen says NO WORLD ON DISK, the `station/` folder did not come
with this copy.
DOC

# ---------------------------------------------------------------------------
# LAUNCH IT. The whole point of the file. A static check that the files exist
# proves nothing: this project has shipped finished machinery with no caller
# nine times, and the ninth slipped under the static scan built to catch the
# eighth. So the artefact is started, headlessly, and its own first lines are
# read back.
# ---------------------------------------------------------------------------
say ""
#
# AND IT IS LAUNCHED FROM A DIFFERENT DIRECTORY THAN THE ONE IT WAS BUILT IN.
# `station/boot.py` writes ABSOLUTE paths into boot.json, which is the right
# answer on the machine that generates the world and the wrong answer on a
# stranger's. The first packaged build here launched, reached customs and issued
# a card -- because the generator's own directory still existed on the build
# box. The evidence was real and true for the wrong reason. Moving the tree
# before launching it is what tells the two apart, and it costs one `mv`.
say "package: launching the artefact (from a moved directory, so a build that"
say "         only works where it was made fails) ..."
RUNLOG="$DIST/firstrun.log"
MOVED="$DIST/_relocated_$$"
mv "$STAGE" "$MOVED"
set +e
( cd "$MOVED" && timeout 900 ./"$NAME" --headless -- --menu-gate ) \
    >"$RUNLOG" 2>&1
run_rc=$?
set -e
mv "$MOVED" "$STAGE"
# THE FILTER IS PART OF THE GATE, AND ROUND 1's WAS THE GATE'S BLIND SPOT.
# It matched `^(menu:|MENUGATE|main:|arrival:)` and therefore showed a clean,
# passing launch of a build whose very next lines read
# `ERROR: walk: dress FAILED` and `dress: 0 light sources`. The AFTER that was
# quoted as evidence was the filtered view of the defect. `walk:`, `dress:` and
# every `ERROR` are in the report now, because a report that omits the failing
# lines is the render-fallback defect wearing a grep.
grep -E "^(menu:|MENUGATE|main:|arrival:|walk:|dress:|ERROR)" "$RUNLOG" \
  | head -40 | sed 's/^/  | /'

if [ "$WITH_DATA" -eq 0 ]; then
  # THE NEGATIVE CONTROL. With no world staged the build must refuse, loudly,
  # at the front door -- and the front door must still have come up, because a
  # title screen that cannot appear without a world is a title screen that
  # cannot tell a player what is wrong.
  if grep -q "^menu:" "$RUNLOG" && grep -q "NO WORLD" "$RUNLOG" \
     && grep -q "verdict=FAIL" "$RUNLOG"; then
    say ""
    say "package: --no-data CONTROL FIRED as it must -- the title screen came up"
    say "         and NEW GAME refused. rc=$run_rc"
    exit 0
  fi
  say ""
  say "package: --no-data control did NOT fire. A build with no world reported"
  say "         success, which means this script cannot tell the two apart."
  exit 1
fi

# AND IT MUST HAVE REBASED. `station/boot.py` and `station/arrival.py` write
# ABSOLUTE paths from the machine that generated the world; on any other machine
# those files do not exist. The staged build therefore has to move them onto its
# own directory at load, and `main.gd` prints when it does. If that line is
# absent, this run resolved the BUILD MACHINE's own paths -- it would pass here
# and fail for everybody else, which is the worst kind of green.
if ! grep -q "rebased onto" "$RUNLOG"; then
  say ""
  say "package: the artefact started WITHOUT rebasing any path. That means it"
  say "         read the build machine's own directories, and it will not run"
  say "         anywhere else. Destroying the staged build. See $RUNLOG"
  rm -rf "$STAGE"
  exit 1
fi

if [ $run_rc -ne 0 ] || ! grep -q "MENUGATE .* verdict=PASS" "$RUNLOG"; then
  say ""
  say "package: THE ARTEFACT DOES NOT START. rc=$run_rc, see $RUNLOG"
  say "         Destroying the staged build rather than shipping it."
  rm -rf "$STAGE"
  exit 1
fi

# ---------------------------------------------------------------------------
# AND IT MUST NOT BE DIMINISHED. `verdict=PASS` says the front door works and
# the player got a card; it says NOTHING about whether the world they walked
# into is the world that was built. Round 1 shipped a tarball that passed
# MENUGATE with every lamp missing and the player at Earth gravity.
#
# So two assertions on the artefact's OWN OUTPUT, each naming a specific silent
# degradation with a specific staged file behind it. Both failed on round 1's
# tarball; the negative control for each is deleting its DATA row and watching
# the line change (recorded in the commit message).
#
# WHY NAMED ASSERTIONS AND NOT A GENERAL "no ERROR lines". Because an error the
# SOURCE TREE prints too is not something packaging caused or can fix, and a
# gate that fails for it gets switched off. These fail only for a difference
# between the source tree and the download.
#
# THAT REASONING WAS RIGHT AND ITS ONE WORKED EXAMPLE WAS A REAL DEFECT. This
# comment used to name `walk: could not load any crowd library` as the standing
# error to be tolerated, on the true grounds that the source tree printed it as
# well. It printed it because NO BUILD PATH HAD EVER GENERATED THE CROWD
# LIBRARY -- so the tolerated line was the whole cast of the game being absent,
# on both sides, invisible to a differential precisely BECAUSE it was broken
# equally in both. `tools/bake_crowd.py` closes it and there is now a named
# assertion above that destroys the build for it.
#
# The lesson is not "assert on every error". It is that a differential is blind
# to anything broken identically on both sides, so a line excused as "the
# source does it too" needs the second question asked out loud: is the source
# tree right? Here it was not, for nine sessions.
# ---------------------------------------------------------------------------
diminish() {
  say ""
  say "package: THE BUILD IS DIMINISHED -- $1"
  say "         It starts, it reaches customs, and it is not the game that was"
  say "         built. Destroying the staged build rather than shipping it."
  say "         See $RUNLOG"
  rm -rf "$STAGE"
  rm -f "$TARBALL"
  exit 1
}

# ---------------------------------------------------------------------------
# THE GENERAL FORM, AND IT IS THE ONE THAT FINDS THE NEXT ONE.
#
# The two assertions below name two degradations somebody already knew about.
# That is the shape of every gate this project has had to write twice: it can
# only fail for a defect its author had in mind. `journal.gd` was a THIRD silent
# degradation, in a file nobody had looked at, and no named assertion would have
# caught it.
#
# So: run the SOURCE TREE through the identical command, and diff. The packaged
# build and the source tree are the same code over the same data; every line
# that differs is something packaging did. It needs no list, it cannot go stale
# against the source, and it fails for defects nobody has thought of yet.
#
# NORMALISED, because two things legitimately differ and neither is a defect:
# absolute paths (the whole point of the relocation test) and elapsed times.
#
# AND BOTH HALVES ARE ASSERTED TO HAVE PRODUCED OUTPUT. CLAUDE.md records this
# project recording an A/B as IDENTICAL when both halves had died on the same
# IndexError and written empty files. Two empty logs diff clean.
#
# `--no-diff` skips it (it costs a second engine run, ~25 s); the named
# assertions still hold. It is not a way to ship a red build -- it is for a box
# where the source tree cannot run.
# NORMALISING A PATH MEANS NORMALISING BOTH FORMS OF IT. The first cut mapped
# absolutes to <ROOT> and left `../station/…` alone, so the identical
# "enforcement.json is absent" message read as a difference on the strength of
# how the path was spelled. Both spellings collapse here.
#
# ONE EXEMPTION, and it is the only one, and it is package-only BY CONSTRUCTION
# rather than by convenience: `main: the arrival sidecar names N path(s) …
# rebased onto …` cannot appear in a source-tree run, because in the source tree
# the sidecar's absolute paths still resolve and there is nothing to rebase.
# Exempting it loses no coverage -- the assertion above REQUIRES that line in
# the packaged run and destroys the build without it, which is strictly stronger
# than "it differs". Any second exemption should be argued as hard as this one;
# a growing exemption list is how a differential becomes decoration.
_norm() {
  sed -E 's#/[A-Za-z0-9_./ -]*/(station|tools|godot|dist)/#<ROOT>/\1/#g;
          s#(^|[^A-Za-z0-9_/.])\.\./(station|tools|godot)/#\1<ROOT>/\2/#g;
          s#[0-9]+\.[0-9]+ ?(ms|s)\b#<T>#g' "$1" \
    | grep -vE '^$|^main: the arrival sidecar names '
}
_differential() {
  local src="$DIST/sourcerun.log"
  say ""
  say "package: running the SOURCE TREE through the identical command, so any"
  say "         line the download does not match is something packaging did ..."
  set +e
  ( cd "$ROOT/godot" && timeout 900 "$GODOT" --headless --path . -- --menu-gate ) \
      >"$src" 2>&1
  local src_rc=$?
  set -e
  # BOTH HALVES PRODUCED OUTPUT, asserted before either is compared.
  local n_src n_pkg
  n_src=$(wc -l <"$src"); n_pkg=$(wc -l <"$RUNLOG")
  if [ "$n_src" -lt 20 ] || [ "$n_pkg" -lt 20 ]; then
    say "package: the differential is VACUOUS -- source produced $n_src lines"
    say "         (rc=$src_rc), package produced $n_pkg. A diff of two failed"
    say "         runs is not a pass. Destroying the staged build."
    rm -rf "$STAGE"; rm -f "$TARBALL"; exit 1
  fi
  local only_src only_pkg
  only_src=$(comm -23 <(_norm "$src" | sort -u) <(_norm "$RUNLOG" | sort -u))
  only_pkg=$(comm -13 <(_norm "$src" | sort -u) <(_norm "$RUNLOG" | sort -u))
  if [ -z "$only_src" ] && [ -z "$only_pkg" ]; then
    say "package: DIFFERENTIAL CLEAN -- $n_src source lines, $n_pkg packaged,"
    say "         and after normalising paths and timings they say the same"
    say "         thing. The download is the game that was built."
    return 0
  fi
  say ""
  say "package: THE DOWNLOAD IS NOT THE GAME THAT WAS BUILT."
  [ -n "$only_src" ] && { say "  the source tree says, and the download does not:"
    printf '%s\n' "$only_src" | head -12 | sed 's/^/    - /'; }
  [ -n "$only_pkg" ] && { say "  the download says, and the source tree does not:"
    printf '%s\n' "$only_pkg" | head -12 | sed 's/^/    + /'; }
  say "  Destroying the staged build. Full logs: $RUNLOG and $src"
  rm -rf "$STAGE"; rm -f "$TARBALL"
  exit 1
}

# `dress: 0 light sources` is the exact line a build with no `export_scene.py`
# prints. Source tree, same command: `dress: 663 light sources at energy 3.00`.
if ! grep -qE "^dress: [1-9][0-9]* light sources" "$RUNLOG"; then
  diminish "no light sources. $(grep -m1 '^dress: .* light sources' "$RUNLOG" \
    || echo 'the dresser never reported at all')"
fi
# Branch 3 of `walk.gd::_derive_omega2` -- the deck's own measured spin. Any
# other branch means the body is on some other planet's gravity, and branch 4 is
# specifically the pre-4r defect INV-451 was written to close.
if ! grep -q "^walk: gravity -- omega2=" "$RUNLOG"; then
  diminish "the body fell through to a stated gravity instead of deriving the
         deck's own. $(grep -m1 '^walk: gravity' "$RUNLOG" \
    || echo 'nothing reported the field at all')"
fi
# ---------------------------------------------------------------------------
# IS ANYBODY IN IT. The assertion this file most needed and did not have.
#
# The round-1 tarball started, reached customs, passed MENUGATE, satisfied both
# assertions above -- and contained NO PEOPLE. `crowd_lod*.glb` had never been
# generated by any build path, so `walk.gd` printed `could not load any crowd
# library` and drew none of the cast. A 325 MB download of an empty station,
# and every gate green.
#
# The comment above `_differential` used to excuse exactly this, and it is
# worth quoting because it is how the hole stayed open:
#
#     "there IS a standing error on both sides of the A/B -- `walk: could not
#      load any crowd library` -- because no crowd_lod*.glb has ever been
#      generated. A gate that failed on any error would fail for a content gap
#      packaging did not cause and cannot fix"
#
# Every clause was true. The conclusion -- therefore do not assert on it --
# turned a known missing feature into a permanent exemption, and the
# differential could not see it because the source tree was broken the same
# way. `tools/bake_crowd.py` closed the content gap, so the exemption is spent
# and this is the assertion it was standing in for.
#
# THE CAST IS ASSERTED NON-ZERO RATHER THAN "PRESENT", because the failure mode
# is a build that names an empty actors list and reports `cast of 0` cheerfully.
if grep -q "could not load any crowd library" "$RUNLOG"; then
  diminish "the crowd library did not load, so the station has NOBODY in it.
         $(grep -m1 '^walk: .* room occupant' "$RUNLOG" \
    || echo 'no crowd_lod*.glb beside the placement list') --
         run: python3 tools/bake_crowd.py --out <the deck dir>"
fi
if ! grep -qE "^walk: cast of [1-9][0-9]*" "$RUNLOG"; then
  diminish "the deck carries no cast. $(grep -m1 '^walk: cast of' "$RUNLOG" \
    || echo 'nothing reported a cast at all')"
fi

[ "$WITH_DIFF" -eq 1 ] && _differential

# --- the one file ----------------------------------------------------------
if [ "$WITH_TAR" -eq 1 ]; then
  say ""
  say "package: taring ..."
  rm -f "$TARBALL"
  tar -C "$DIST" -czf "$TARBALL" "$NAME"
fi

say ""
say "package: DONE -- mode=$MODE"
say "  staged   $STAGE  ($(du -sh "$STAGE" | cut -f1))"
[ "$WITH_TAR" -eq 1 ] && \
  say "  one file $TARBALL  ($(du -h "$TARBALL" | cut -f1))"
say "  run it   cd $STAGE && ./$NAME"
say "  lit      $(grep -m1 -oE '^dress: [0-9]+ light sources at energy [0-9.]+' \
    "$RUNLOG" || echo 'dress: -')"
say "  gravity  $(grep -m1 -oE 'omega2=[0-9.]+ rad2/s2 from [^,]*' "$RUNLOG" \
    || echo '-')"
if [ "$MODE" = "pack+engine" ]; then
  say ""
  say "  CAVEAT   this artefact's game/$NAME.x86_64 IS the Godot editor binary"
  say "           ($(md5sum "$STAGE/game/$NAME.x86_64" | cut -c1-12) ="
  say "            $(md5sum "$GODOT" | cut -c1-12) $(basename "$GODOT")),"
  say "           so \`./$NAME -e\` opens an editor. Ship an export-release"
  say "           build (see 'SUBSTITUTION' above) before this is a title."
fi
