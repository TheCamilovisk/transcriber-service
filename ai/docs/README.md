# Specification Index

This project follows spec-driven development. The three original specifications remain the source of truth and are unchanged:

- [functional-specification.md](functional-specification.md)
- [architecture-specification.md](architecture-specification.md)
- [vertical-slice-implementation-plan.md](vertical-slice-implementation-plan.md)

Each has also been split into small, self-contained documents so a single vertical slice can be implemented by referencing only the sections relevant to it, without loading the entire spec:

- [`functional/`](functional/) — one document per functional requirement area (see `functional/01-purpose-and-scope.md` onward, numbered to match the source spec's section order).
- [`architecture/`](architecture/) — one document per architectural concern (layering, database, storage, worker, Docker, testing, etc.), numbered to match the source spec's section order.
- [`vertical-slices/`](vertical-slices/) — one document per implementation slice (`slice-01-...` through `slice-14-...`), plus an [overview](vertical-slices/00-overview.md) and [commit sequence / definition of done](vertical-slices/99-commit-sequence-and-notes.md).

## How to use this when implementing a slice

1. Open the matching `vertical-slices/slice-NN-*.md` file for the slice you're building — it has the Goal, Scope, Tasks, Tests, and Acceptance Criteria for that increment.
2. Cross-reference the linked `architecture/` and `functional/` documents named in its tasks for the precise contract (exact field names, status codes, error messages, file layout) rather than re-reading the full specs.
3. Treat the split documents as a navigation layer only — if a split document and an original spec ever disagree, the original spec file wins.
