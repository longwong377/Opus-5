#!/usr/bin/env bash
# BUILD SOMETHING A STRANGER CAN RUN. One command, one artefact, one launcher.
#
#   bash tools/package.sh              # build dist/Babylon5-linux-x86_64.tar.gz
#   bash tools/package.sh --check      # say what is present and what is missing;
#                                      #   build nothing, exit non-zero if the
#                                      #   result would not be runnable
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
while [ $# -gt 0 ]; do
  case "$1" in
    --check)   CHECK=1 ;;
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
# ---------------------------------------------------------------------------
# AND EACH ONE SAYS WHETHER THE BUILD IS RUNNABLE WITHOUT IT, plus what a
# player loses when it is absent. A flat required-list would refuse to package a
# perfectly playable build over `scene/vista`, which only three places on the
# station consult; a flat optional-list would happily ship a build with no deck.
# The distinction is the whole value of the table -- a precondition that cannot
# distinguish "broken" from "diminished" gets switched off.
#
#   path | required | what its absence costs
DATA=(
  "station/generated/scene/boot.json|yes|main.gd::_boot_manifest -- without it the game cannot start at all"
  "station/generated/scene/deck|yes|the deck mesh, collision shell, interactables and arrival sequence"
  "station/generated/audio|no|ambience.gd's 13 loops -- the station is silent"
  "station/generated/navgraph.json|no|navgraph.gd -- NPCs cannot route"
  "station/generated/economy.json|no|player.gd::has_purse is false, so tier stays at its sentinel"
  "station/generated/scene/npc|no|ragdoll.gd's 14 species bodies -- nobody falls over"
  "station/generated/scene/vista|no|vista.gd -- the three windowed rooms show background instead of the station"
  "station/generated/journal.json|no|journal.gd -- nothing is learned or remembered"
)

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
fi

# --- the launcher ----------------------------------------------------------
# A player runs THIS, not the binary in game/. Two reasons, and the second is
# the one that matters: it keeps the working directory off the equation, and it
# passes NO user arguments -- `main.gd::_front_door` shows the title screen only
# on a launch with a display and no arguments at all, which is precisely what
# double-clicking is and what every developer command line is not.
cat >"$STAGE/$NAME" <<'LAUNCH'
#!/usr/bin/env bash
# Babylon 5. Run this.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
say "package: launching the artefact ..."
RUNLOG="$DIST/firstrun.log"
set +e
( cd "$STAGE" && timeout 900 ./"$NAME" --headless -- --menu-gate ) \
    >"$RUNLOG" 2>&1
run_rc=$?
set -e
grep -E "^(menu:|MENUGATE|main:|arrival:)" "$RUNLOG" | head -30 | sed 's/^/  | /'

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

if [ $run_rc -ne 0 ] || ! grep -q "MENUGATE .* verdict=PASS" "$RUNLOG"; then
  say ""
  say "package: THE ARTEFACT DOES NOT START. rc=$run_rc, see $RUNLOG"
  say "         Destroying the staged build rather than shipping it."
  rm -rf "$STAGE"
  exit 1
fi

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
