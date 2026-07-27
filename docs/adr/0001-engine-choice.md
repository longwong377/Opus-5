# ADR 0001 — Engine: Godot 4 with double precision

**Status:** Accepted · **Date:** 2026-07-27

## Context

A 1:1 8,047 m station with seamless interior/exterior, spin-gravity physics, Newtonian flight
and large NPC populations, built across many sessions by an agent with no GPU and no editor
GUI, for an owner who is hands-off until ship.

## Options

**Godot 4** — every file is text (`.tscn`, `.tres`, `.gd`, `.cs`). `precision=double` is a
supported build flag, solving 8 km float32 jitter at engine level. Headless mode gives real CI.
Small repository. Open source. No Nanite equivalent; LODs are ours to manage.

**Unreal 5** — Nanite is precisely the technology for hyper-detailed hard-surface greeble, and
Lumen would sell the garden. Large World Coordinates and Mass Entity are directly on point.
But assets are binary `.uasset`, so most of the project becomes blobs that cannot be reviewed
or diffed, and the workflow assumes an editor GUI that is unavailable here.

**Custom (Rust/wgpu, Bevy, C++/Vulkan)** — total control, at the cost of spending the first ten
sessions writing a renderer instead of building Babylon 5.

## Decision

**Godot 4, C#, built from source with `precision=double`.**

Unreal renders better and it is not close. It was viable **only** on the condition that the
owner performed editor passes; the owner has confirmed they will not. Without a human in the
editor, Unreal's advantage is unreachable and its costs — unreviewable binary assets, slow
iteration, enormous repository — remain in full.

The project's bottleneck is not rendering quality. It is content authored across many sessions
by an agent working in text, verified without a GPU. Godot is the only option where 100% of the
project is text that can be authored, verified and diffed.

## Consequences

- LOD, streaming and occlusion are ours to build. Partly true of any engine at this scale.
- Visual ceiling is lower than Nanite/Lumen. Mitigated by procedural detail, trim sheets,
  decal layers and instancing — and B5's industrial aesthetic is unusually well suited to
  procedural generation.
- Godot must be built from source (no official double-precision binaries), ~40 minutes on
  4 cores. Build once, publish as a GitHub Release asset, pull in seconds thereafter.
- Software rendering via Mesa lavapipe (Vulkan 1.4 on CPU, verified) provides the visual
  feedback loop.
