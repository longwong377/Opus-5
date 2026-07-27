# The Godot binary

The engine is Godot 4.4 built from source with `precision=double`. **No official
double-precision binaries exist**, so it has to be built. See
`docs/adr/0001-engine-choice.md` for why double precision is required — short version: not
for the station, which survives float32 marginally, but for the Starfury's 50 km flight
envelope, where float32 spacing reaches 3.9 mm and reads as shimmer.

## Where it is

```
/home/user/godot-build/godot-4.4-stable/bin/godot.linuxbsd.editor.double.x86_64
```

**Container-local.** It does not survive the container being reclaimed.

## Rebuilding

```bash
bash tools/build_godot.sh          # ~61 minutes on 4 cores
```

The script is idempotent — scons resumes from existing object files, so an interrupted build
picks up where it stopped rather than restarting.

Two things in it are non-obvious and were both learned the hard way:

- **`JOBS` defaults to 2, not `nproc`.** The first attempt at `-j4` was killed part-way with
  no error in the log at all — the OOM killer's signature. Godot's thirdparty C++ peaks at
  multiple GB per compiler process.
- **`lto=none`.** `production=yes` turns on LTO, whose link step needs far more memory than
  this container has. We need a correct binary, not a fast one.
- **Source is fetched by `git clone`, not `curl`.** The agent proxy returns 403 for GitHub
  archive and codeload paths.

## Why it is not cached in the repository

Stripped and `xz -9` compressed it is **52 MB** — under GitHub's 100 MB file limit, so it
would fit. It is deliberately not committed: it is a reproducible build artifact, git history
is permanent, and every future clone would pay for it forever.

If a cached copy is wanted, the right home is a **GitHub Release asset**, which this session
cannot create (the available GitHub tooling is read-only for releases). To do it by hand:

```bash
strip --strip-unneeded godot.linuxbsd.editor.double.x86_64
xz -9 -T0 godot.linuxbsd.editor.double.x86_64        # -> 52 MB
# then attach to a release and record the URL here
```

## Rendering with it

There is no GPU. Rendering goes through Mesa lavapipe, which provides **Vulkan 1.4 on CPU**:

```bash
bash tools/build_and_render.sh
```

`--headless` disables rendering entirely, so frames need a virtual display. The script runs
Godot under `xvfb-run` with `VK_ICD_FILENAMES` pointed at the lavapipe ICD. Godot reports
`Vulkan 1.4.318 - Forward+ - llvmpipe`, doing real Forward+ rendering in software.

Slow — minutes per frame. `tools/preview_render.py` is the fast path for judging proportion
and silhouette; the Godot path is for material and lighting.
