# ADR 0002 — Geometry representation: polygonal, not voxel

**Status:** Accepted · **Date:** 2026-07-27

## Context

The owner asked whether hyper-detailed voxels or something else should represent the station.

## Analysis

**Voxels fail on capacity.** The station's bounding volume at 1 cm resolution, dense, is
~5 × 10¹⁴ voxels. Sparse surface-only storage helps enormously, but a structure housing
250,000 people has well over 50 km² of interior surface once walls and ceilings are counted.
At 1 cm that is on the order of **10¹² surface voxels** — terabytes before any texture data.
Dropping to 10 cm (Teardown's regime) still leaves ~10¹⁰ *and* forfeits the ability to
represent a door frame, a handrail, a panel line, or hull curvature.

**Voxels fail on aesthetics, independently.** Babylon 5's design language is thin hard edges
and long smooth curves — Foundation Imaging's crisp LightWave hard-surface modelling. That is
precisely what voxels represent worst. The result would read as Minecraft.

Either objection alone is fatal. Together they are not close.

## Decision

**Modular polygonal geometry with PBR materials**: kit-bashed modules, trim sheets, decal
layers, procedural greebling, heavy GPU instancing.

Detail comes from baked high-frequency normal and height data, parallax occlusion on flat
surfaces, rule-scattered instanced greeble meshes, and displacement on hero surfaces — not
from hand-sculpted uniqueness, which is unavailable at this scale without an art team.

Voxel-adjacent techniques keep the roles where they are genuinely correct: volumetric fog and
atmosphere in the garden, GI probe volumes. Signed distance fields are worth using as a
*modelling* representation for the hull's smooth-with-hard-edge forms, polygonised before it
reaches the renderer.

## Consequences

- Detail density is a function of generator sophistication, and improves every session without
  re-authoring anything. This is what makes "hyper detailed" reachable by an agent.
- The B5 aesthetic — repeated hull segmentation, panel lines, industrial greeble — is unusually
  well suited to procedural generation. The style and the method are aligned.
- No runtime destruction of arbitrary geometry. Not a requirement.
