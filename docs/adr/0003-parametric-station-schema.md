# ADR 0003 — One parametric schema generates interior and exterior

**Status:** Accepted · **Date:** 2026-07-27

## Context

Requirement: "the station all being one seamless model", inside and outside consistent.

The naive approach — model the hull, separately model interiors, keep them aligned by care —
fails predictably. At 8 km with multiple sectors and levels, hand-maintained consistency
between two representations drifts, and every drift is a visible seam or a window looking at
the wrong thing.

## Decision

A single declarative **station schema** describes the station: sections, radii, decks, rings,
spokes, corridors, apertures, level boundaries. From it, generators produce:

1. Exterior hull mesh
2. Interior shell geometry
3. Collision geometry
4. Navigation mesh
5. Occlusion portals and streaming cells
6. Canon-assertion test fixtures

Interior and exterior are then consistent **by construction**. A window is a hole in one
surface that is necessarily a hole in the other, because both derive from the same aperture
record. There is no second representation to drift.

## Consequences

- The schema is the highest-value artifact in the project. It is the thing that must be right.
- Generation is offline and deterministic in Python, unit-testable with no engine and no GPU.
- Changing a station dimension is a one-line edit that regenerates hull, interior, collision
  and navmesh together. This is what makes iteration across many sessions affordable.
- Schema errors propagate everywhere at once. Mitigated by canon-assertion tests that check
  generated geometry against `canon/00-MASTER.md` — airtightness, aperture correspondence,
  navmesh connectivity, dimensional agreement.
- Hero areas needing bespoke treatment (C&C, the Council Chambers) are authored as schema
  *overrides* that still participate in generation, never as detached hand-built meshes.
