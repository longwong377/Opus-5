#!/usr/bin/env bash
# THE WHOLE STATION, FROM SOURCE TO A LAUNCHED PACKAGE, IN ORDER.
#
# Every fix from the judging panel and the two fix rounds lives in SOURCE;
# station/generated/ is gitignored, so none of it is in the artefact until this
# runs. Order matters and is not alphabetical:
#
#   decks+columns -> drum -> cells -> column cells -> merge(renumber)
#   -> sidecars -> crowd library -> boot manifest -> gates -> package
#
# boot.py is LAST before the gates because it reads crowd_ladder, dialogue and
# the merged manifest off disk and names only what exists; a boot manifest
# written earlier is a manifest with no crowd in it.
set -u
cd /home/user/Opus-5
log() { echo; echo "=================== $* ==================="; date -u +%H:%M:%S; }
FAIL=0
step() {  # step <name> <cmd...>
  local n="$1"; shift
  log "$n"
  if "$@"; then echo "OK: $n"; else echo "FAILED($?): $n"; FAIL=1; fi
}

step "1/10 export the 70 ring decks and 5 columns"  python3 tools/export_station.py
step "2/10 export the habitat drum"                 python3 tools/export_drum.py
step "3/10 bake every deck into streaming cells"    python3 tools/bake_station.py
# THE DRUM IS NOT CUT BY bake_station AND THE REASON IS A ROW I WROTE.
# `stream.gd::bake()` takes its axial band from
# cell_manifest.json deck_table[<deck>].cell_length_m, and the drum's row --
# added in this session to give the drum a gravity row it never had -- carries
# cell_length_m 0.0, because interior.ring_cells derives that from a ring
# corridor and the drum has none. A zero band is one cell: 1,585,762 triangles,
# 26x the per-cell budget.
#
# bake_drum.py is the cutter, and its band and axis are MEASURED rather than
# chosen (it refuses an axis that would leave an open shaft). It must run AFTER
# bake_station, which would otherwise overwrite the 85 cells with one.
step "3b/10 cut the drum into its own cells"        python3 tools/bake_drum.py --bake

step "4/10 bake the transit columns"                python3 tools/bake_columns.py --force
step "5/10 merge into one manifest and renumber"    python3 tools/merge_cells.py
step "6/10 dialogue and arrival sidecars"           python3 tools/bake_sidecars.py --stale
step "7/10 the shared crowd library"                python3 tools/bake_crowd.py --out station/generated/scene/station --force
step "8/10 the boot manifest"                       python3 station/boot.py

log "9/10 GATES"
for g in "tools/reach_gate.py" "tools/merge_cells.py --selftest" \
         "tools/cell_identity.py" "tools/cast_gate.py" \
         "tools/crowd_material_gate.py --wiring" "tools/column_site.py --gate" \
         "station/populace.py --lod-gate" "tools/bake_sidecars.py --check" \
         "tools/bake_crowd.py --selftest --out station/generated/scene/station"; do
  printf '%-62s ' "$g"
  if python3 $g >/dev/null 2>&1; then echo "PASS"; else echo "FAIL($?)"; FAIL=1; fi
done

step "10/10 package"  bash tools/package.sh --no-tar

log "LAUNCH THE PACKAGED BUILD"
if [ -x dist/Babylon5/Babylon5 ]; then
  ( cd dist/Babylon5 && timeout 300 ./Babylon5 --headless --quit-after 90 ) \
    > /tmp/rebuild_launch.log 2>&1
  echo "launch exit=$?"
  grep -iE "stream: [0-9]+ cells|cast of|can speak|gravity --|light sources|could not|interactable" \
    /tmp/rebuild_launch.log | head -8
else
  echo "no packaged build to launch"; FAIL=1
fi

log "DONE -- overall $( [ $FAIL -eq 0 ] && echo ALL-GREEN || echo 'SOMETHING FAILED, see above' )"
exit $FAIL
