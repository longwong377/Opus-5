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

**Container-local.** It does not survive the container being reclaimed — but since session 4d
it does not need to: run `bash tools/build_godot.sh` and it is restored from `vendor/godot/`
in seconds. Only a container with no vendored copy and no URL pays for a build.

## Getting it

```bash
bash tools/build_godot.sh          # seconds if vendored; ~50 min if it has to build
bash tools/build_godot.sh --check  # report only, exit 1 if absent
bash tools/build_godot.sh --vendor # package the built binary into vendor/godot/
```

**Run this first in any session that will render anything.** It is a no-op when the binary is
already present, so there is no cost to calling it.

The script is idempotent — scons resumes from existing object files, so an interrupted build
picks up where it stopped rather than restarting.

Two things in it are non-obvious and were both learned the hard way:

- **`JOBS` defaults to 2, not `nproc`.** The first attempt at `-j4` was killed part-way with
  no error in the log at all — the OOM killer's signature. Godot's thirdparty C++ peaks at
  multiple GB per compiler process.
- **`lto=none`.** `production=yes` turns on LTO, whose link step needs far more memory than
  this container has. We need a correct binary, not a fast one.
- **Source is fetched by `git clone`, not `curl`.** The agent proxy returns 403 for GitHub
  archive and codeload paths. (Release *assets* are a different host and do work — see below.)
- **`apt-get update` runs first, and its failure is tolerated.** A fresh container has no
  package lists, so `apt-get install` exits 100 without fetching anything. In session 4d this
  killed the script **8 seconds into a 60-minute job**, with the install redirected to
  `/dev/null` and its status unchecked, so the only evidence was `exit 100`. Two third-party
  PPAs baked into the image (deadsnakes, ondrej/php) are 403 through the proxy on every
  `update`; nothing here needs them, which is why that failure is ignored and an `install`
  failure is not.

## It IS cached in the repository now — `vendor/godot/`

Session 4d, and the decision was reversed deliberately rather than drifted into. What this
document used to say — *"deliberately not committed: git history is permanent, and every
future clone would pay for it forever"* — is still true about the cost. What it got wrong is
the comparison. **The container is reclaimed regularly and the binary does not survive it**,
so the alternative to ~50 MB of permanent history was **an hour of compute per container,
forever**, on the one artefact without which no craft claim in this project can be checked.
Session 4d's own container restarted mid-session and lost a build in progress.

So `bash tools/build_godot.sh --vendor` packages the binary into `vendor/godot/` with its
checksum, and step 2 of the script unpacks it. The container clones this repository at session
start, so the artifact arrives **with the code** — no download, no URL, no token, no manual
step. Unpacking is a `tar -xJf` and a `--version` check.

### The right home is still a Release asset, and here is exactly what is missing

Re-measured in 4d rather than assumed, because the earlier note was half wrong:

| | result |
|---|---|
| **Download** a release asset through the agent proxy | **WORKS** — HTTP 200, 102 MB fetched from a Godot release asset via `release-assets.githubusercontent.com` |
| `api.github.com` direct | 403 *"GitHub access is not enabled for this session"* |
| `gh` CLI | not installed |
| GitHub MCP server release calls | `get_latest_release`, `get_release_by_tag`, `list_releases` — **all reads**, no create |

The earlier claim that GitHub downloads are proxy-blocked is true of **archive and codeload**
paths only, which is why the source is still `git clone`d. Release assets are a different host
and they are reachable.

So the fetch half is proven and only the **upload** is missing, and it needs someone with
GitHub access to run two commands once:

```bash
bash tools/build_godot.sh --package        # prints the archive path and its sha256
gh release create godot-4.4-stable-double <archive> \
   --notes "Godot 4.4-stable, precision=double, linuxbsd x86_64"
echo '<asset url>' > tools/godot-binary.url
cut -d' ' -f1 <archive>.sha256            > tools/godot-binary.sha256
```

`tools/godot-binary.url` takes precedence over `vendor/godot/`, so recording it is all that is
needed — after which `vendor/godot/` can be deleted. The history cost is paid either way by
then; deleting it stops future clones carrying the working-tree copy.

### The checksum is not decoration

Both the vendored and the URL path verify sha256 before unpacking, and the vendored path's
control is run: with a deliberately wrong checksum the script prints the mismatch and falls
through to the build rather than unpacking. A truncated 50 MB blob that extracts to a broken
ELF would otherwise present as *"the renderer is mysteriously wrong"*.

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
