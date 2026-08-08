# Play it

Four steps. About an hour, and nearly all of that is a progress bar you can walk away from.

## Windows

**1. Install Python 3** — [python.org/downloads](https://www.python.org/downloads/).
Tick **"Add python.exe to PATH"** on the first screen of the installer; nothing below works if you miss it.

**2. Install Godot 4.4** — [godotengine.org/download/windows](https://godotengine.org/download/windows/).
The normal one. Not .NET, not any special build. It's a zip with an .exe in it; put it anywhere.

**3. Get the code and build the world.** In PowerShell:

```powershell
git clone -b claude/aaa-game-development-j6y2ml https://github.com/longwong377/opus-5.git
cd opus-5
pip install -r requirements.txt
python tools/build_world.py
```

That last command is the long one — **roughly 45 minutes**. It's generating about 6.2 GB of
corridors, collision, streaming cells, crowds and audio. It prints each step as it finishes and
ends with `DONE`. You only ever do this once.

**4. Play.** Open Godot, click **Import**, point it at the `godot` folder inside `opus-5`, then
press **F5**.

`NEW GAME` puts you on the transport deck at customs with an identicard.

## Mac and Linux

Identical, except step 3 is `python3` instead of `python`. On Linux you can skip straight to
`./play.sh`, which does all four steps including fetching the engine.

## If something goes wrong

**"python is not recognised"** — the PATH box in step 1. Reinstall and tick it.

**The world build fails partway** — run it again. It skips whatever finished, so a second run
picks up where it stopped rather than starting over.

**The title screen says NO WORLD ON DISK** — step 3 didn't finish. Run
`python tools/build_world.py --check`; it'll tell you whether the world is actually there.

**It's slow to walk around** — expected, and it's the one thing I know is unfinished. 242 of the
907 streaming cells are over the triangle budget, the worst by 5.3×. There's no GPU where this
was built, so I could never measure a frame rate. If it's bad on your machine, that's the number
to come back at me with.

## What about the browser?

No, and not for a fixable reason. Godot's web export only runs the Compatibility renderer, so it
loses the lighting this is built around, and it would have to pull 6.2 GB of world into a tab.
A browser version would be a different and much smaller thing — one deck, stripped. Worth doing
only if a shareable link matters more to you than what it looks like.

## One correction

Earlier versions of this file, and `CLAUDE.md`'s hard rule 5, said you needed a special build of
Godot compiled with `precision=double`, because the station is 8 km long and 32-bit floats were
said to wobble at that scale.

**That was never tested and it's wrong.** At 4 km from the centre a 32-bit float resolves to about
half a millimetre. Stock Godot 4.4 runs this fine — 907 cells, 363 residents, correct spin gravity,
the whole arrival sequence. The double-precision engine in `vendor/` still works and is still what
Linux `play.sh` uses, but nobody needs to compile anything.
