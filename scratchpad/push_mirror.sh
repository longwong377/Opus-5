#!/bin/sh
# Mirror local commits to the remote as they land.
#
# THE CONTAINER RECYCLED TWICE IN ONE TURN and rolled the checkout back both
# times. CLAUDE.md records the same hazard three times in an earlier session.
# The shell-fit agent's whole run was lost to it: it committed in a worktree,
# the container recycled, and nothing had reached the remote.
#
# This NEVER creates a commit. It only pushes what is already there, so the
# worst it can do is publish a build agent's own checkpoint -- which is exactly
# what we want to survive a recycle.
cd /home/user/Opus-5 || exit 1
B=claude/aaa-game-development-j6y2ml
last=""
while true; do
  head=$(git rev-parse HEAD 2>/dev/null)
  if [ -n "$head" ] && [ "$head" != "$last" ]; then
    if git push -q origin "$B" 2>/dev/null; then
      echo "$(date -u +%H:%M:%S) mirrored $head"
      last="$head"
    fi
  fi
  sleep 120
done
