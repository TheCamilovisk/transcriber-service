# Vertical Slice Starter Checklist

Quick-reference checklist for starting and implementing a vertical slice
in transcriber-service. Tick each item as you complete it.

## Pre-Flight & Branch

- [ ] If no `.git/` exists yet, stop and ask the user before running
      `git init` — don't assume it
- [ ] `git fetch origin && git status` — confirm `dev` is up to date and clean
      (skip remote check if no remote configured yet)
- [ ] Verify previous slice branch is merged into `dev` (ask user if not)
- [ ] `git checkout -b slice/<NN>-<name> dev`

## Read & Understand

- [ ] Read the slice doc: `read ai/docs/vertical-slices/slice-<NN>-<name>.md`
- [ ] Read referenced functional-spec sections (`ai/docs/functional/*.md`)
- [ ] Read referenced architecture-spec sections (`ai/docs/architecture/*.md`)
- [ ] Identify every file/directory listed under "Tasks"

## Implement

- [ ] Create/modify all files listed in "Tasks"
- [ ] Implement every item in "Acceptance Criteria"
- [ ] Respect "Scope" — do not build ahead of the current slice
- [ ] Respect domain rules from `CLAUDE.md`: job UUID before file save,
      worker claims oldest-pending / list orders newest-first, exact
      failure messages, no `text`/`stored_audio_path` in list responses,
      single-worker assumption, UTC timestamps via `utc_now()`

## Test

- [ ] Write tests matching the slice's "Tests" section, placed under
      `tests/unit/`, `tests/api/`, `tests/worker/`, or `tests/integration/`
- [ ] Use `FakeTranscriber` for unit/API/worker tests — no real Faster
      Whisper model in the default run
- [ ] Mark real-model tests `@pytest.mark.integration`
- [ ] Use in-memory SQLite (unit/API) or temp file-backed SQLite
      (worker/integration) and `tmp_path` for uploads — never the real
      `./data` dir

## Quality Gate

- [ ] `uv run pytest` — all tests pass
- [ ] `uv run ruff check .` — no linting errors
- [ ] `uv run ruff format .` — formatting is clean

## Review

- [ ] Present summary: what was implemented, diff, test results, acceptance criteria
- [ ] **Stop and wait** for user's explicit approval

## Post-Approval

- [ ] `git add -A && git commit -m "slice <NN>: <description>"`
- [ ] `git push -u origin slice/<NN>-<name>` (if a remote is configured)
- [ ] `gh pr create --base dev --head slice/<NN>-<name> --title "Slice <NN>: <description>" --body "Implements slice <NN>."`
- [ ] Present the PR link to the user and stop — do not approve or merge
