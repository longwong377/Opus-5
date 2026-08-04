# spec/ — the completion registry

`completion.yaml` is GENERATED from `docs/THE-STATION.md` by `tools/spec_registry.py`
(to be written when §4–§8 are filled). One entry per spec item:

    - id: PLC-017            # stable, never reused
      title: "Earhart's, full program"
      section: "4"           # where in THE-STATION.md the prose lives
      shell: A               # A named-place | B connective | C fabric | S system/people/role
      tier_floor: T3         # minimum depth tier the item's interactables must reach
      check: "python3 station/spec_check.py PLC-017"
      state: RED             # RED | GREEN | CAPPED
      cap_reason: null       # required iff CAPPED, owner-visible

Rules enforced by the CI step (`spec gate`):
  * every item's `check` runs; its exit code IS the state (0 GREEN, else RED unless CAPPED)
  * CAPPED requires `cap_reason` and appears in the build summary every run — caps are
    loud, permanent lines, not archived exceptions
  * an item present in THE-STATION.md §4–§8 but absent here fails the gate (the generator
    asserts bijection), so items cannot be dropped by not registering them
  * editing an existing item's `check` or `title` without a SPEC-CHANGE entry in
    THE-STATION.md §9 fails the gate (the generator hashes prior entries)

`spec_check.py` implements one function per item class, and the function must reference the
ENUMERATED content (names, counts, positions from the spec row), never a statistic. The
statistics stay in their own gates as floors.
