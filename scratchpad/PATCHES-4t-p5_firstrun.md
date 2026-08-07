# Patches p5_firstrun needs in files it does not own

Round 2, session 4t. Nothing here has been applied. Each is a real defect measured on the
packaged artefact; `tools/package.sh` works around all of them from inside its own launcher
(INV-960) so the tarball is correct today, and the workaround should be deleted when these land.

## 1. SIX SITES OF ONE IDIOM HAVE NO EXPORTED-BUILD BRANCH  (owners: various)

`ProjectSettings.globalize_path("res://")` returns `""` in an exported build. `main.gd:2042` is
the only site in the project that handles that. These six do not:

    godot/scripts/dress_scene.gd:121   godot/scripts/stream.gd:219   (4t owns stream.gd)
    godot/scripts/interact.gd:414      godot/scripts/journal.gd:233
    godot/scripts/enforcement.gd:361   godot/scripts/ragdoll.gd:1021

Measured cost on the round-1 tarball: `dress: 0 light sources` (source tree: **663**);
`walk: gravity -- NO SPIN STATED ... 9.8100 m/s2` (source tree: **omega2=0.03523997**, floor_g
0.7602 at r=211.55 m) — i.e. INV-451's own negative control was the shipped state; and
`journal: 0 kinds, 0 ledgers ... hash MISMATCH` (source tree: **8 kinds, 8 ledgers, 62 timed
calls, hash ok**). All three ran green through `MENUGATE verdict=PASS`.

The fix is one shared function with `main.gd::_root()`'s branch, applied to all six — not to one
of them. CLAUDE.md: *"a fix applied to an instance and not to the rule is a fix that will be
needed again."*

    var base := ProjectSettings.globalize_path("res://")
    if base == "":
        base = OS.get_executable_path().get_base_dir()

Note that `journal.gd:233` additionally resolves ONE LEVEL HIGHER than the other five
(`.rstrip("/").get_base_dir()` rather than `.path_join("..")`) and its `MANIFEST_REL` carries no
`../`. Whoever unifies these must keep that difference or change both halves together.

## 2. `tools/export_scene.py` IS PARSED AT RUNTIME AND IS 426 KB OF SOURCE IN A GAME DOWNLOAD

`dress_scene.gd:63` reads `../tools/export_scene.py` as TEXT to recover `FIXTURE_LIGHTING`, and
`dress_scene.gd:36` already names the clean version: *"four lines in export_scene.py --
`--dump-lighting` writing FIXTURE_LIGHTING to JSON beside the deck"*. Until that exists, a shipped
build carries a Python generator it never runs. `station/budget.py` (136 KB) is the same shape via
`stream.gd::budget_cells`.

Do it, and `package.sh`'s `DATA` table loses two rows and the download loses 560 KB of source.

## 3. NO `crowd_lod*.glb` HAS EVER BEEN GENERATED

`walk.gd::_load_crowd_libs` looks for `crowd_lod*.glb` beside `crowd_path` and finds none, so
`ERROR: walk: could not load any crowd library` and `83 room occupant(s) ... cannot be drawn`.
This is identical in the source tree and in the tarball — it is a content gap, not a packaging
one, and `package.sh` deliberately does not fail on it. Named here so it is not rediscovered as a
packaging bug a third time.
