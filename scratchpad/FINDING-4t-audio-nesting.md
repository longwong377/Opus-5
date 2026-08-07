# A 5.7 MB byte-duplicate audio tree appeared in the SOURCE tree during 4t

**Found by the stop hook, not by a gate** — `station/generated/audio/audio/` held 15 files, every
one `cmp`-identical to its parent in `station/generated/audio/`, which is *tracked*. Removed after
verifying byte-identity; nothing was lost.

**It is not proven which agent wrote it**, and that matters more than the 5.7 MB. Two candidates,
both worth checking before the next packaging round:

1. `tools/package.sh:465` is `cp -r "$ROOT/$d" "$STAGE/$d"`. `cp -r src dst` **copies src INTO dst
   when dst already exists** — so a second run over the same stage, or any row in `DATA[]` whose
   parent was staged by an earlier row, produces exactly this nesting. That path writes to `$STAGE`
   rather than `$ROOT`, so it does not explain a duplicate in the source tree on its own — but it is
   the same defect shape one directory over, and it will bite on a re-run.
2. A relative-path writer resolving one level off, which is the defect `package.sh`'s own comment
   block documents at length for `journal.gd:233` (`.get_base_dir()` lands one level UP) and for the
   six raw `globalize_path("res://")` readers that return `""` in an exported build.

**Why it is worth a note rather than a silent delete:** a duplicate of a *tracked* artefact is
invisible to every gate this project has. `wiring.py` asks whether each engine path EXISTS; a second
copy one directory down satisfies that. Nothing counts files. The only reason it surfaced is that a
git hook noticed untracked paths — which is not a gate, it is luck.

**The cheap assertion, if somebody wants one:** `station/generated/` should contain no directory
whose name equals its parent's. One line, and it can fail today by re-creating the path.
