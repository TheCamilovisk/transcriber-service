---
name: vertical-slice-workflow
description: >
  Complete workflow for starting and implementing a vertical slice in the
  transcriber-service (Audio Transcription API) project. Covers pre-flight
  git checks, branch creation, reading the slice doc and its references,
  implementation rules, test conventions, the quality gate, review process,
  and post-approval steps. Use whenever the user asks to begin work on a new
  vertical slice (e.g. "start slice 4").
---

# Vertical Slice Workflow

This skill guides you through the full lifecycle of implementing a vertical
slice in the transcriber-service project: from pre-flight checks and branch
creation, through implementation and testing, to review and post-approval
push.

## Key Documents

All paths are relative to the project root
(`/mnt/1fe0b99b-25f1-40a6-b504-e62dffb14c82/Workspace/transcriber-service/`):

| Document | Path |
|---|---|
| Slice order & strategy | `ai/docs/vertical-slice-implementation-plan.md` |
| Slice overview & sequence | `ai/docs/vertical-slices/00-overview.md`, `ai/docs/vertical-slices/99-commit-sequence-and-notes.md` |
| Project instructions & domain rules | `CLAUDE.md` |
| Functional spec (index) | `ai/docs/functional-specification.md` |
| Topic-split functional docs | `ai/docs/functional/*.md` |
| Architecture spec (index) | `ai/docs/architecture-specification.md` |
| Topic-split architecture docs | `ai/docs/architecture/*.md` |
| CI & branching conventions | `ai/docs/architecture/21-ci-and-branching-architecture.md` |
| Slice N's doc | `ai/docs/vertical-slices/slice-<NN>-<name>.md` |
| This checklist | `references/checklist.md` |

## 0. First-Time Git Setup

This repository may not yet be a git repository (check with `git status`).
If `git status` fails or there is no `.git/`, the slice workflow's branching
model (`main`/`dev`, see
`ai/docs/architecture/21-ci-and-branching-architecture.md`) does not exist
yet. **Stop and ask the user** whether to:

- `git init`, make an initial commit, and create a `dev` branch, or
- proceed without git branching for now (not recommended — slices won't be
  isolable or reviewable as PRs).

Do not silently initialize git or pick a default — this is a one-time
project decision the user should make explicitly.

## 1. Pre-Flight Checks

Once the repo exists, before touching any code, establish the starting
state:

```bash
git fetch origin
git status
```

Confirm:
- `dev` is up to date with `origin/dev` (skip the remote check if no
  remote is configured yet — that's expected for a brand-new repo).
- You are on `dev` with no uncommitted changes.
- If there are uncommitted changes, alert the user and ask how to proceed
  (stash? commit? branch from here?) — do not proceed automatically.

## 2. Verify Previous Slice Is Merged

Unless this is Slice 1 (Project Skeleton), check whether the previous
slice's branch has been merged into `dev`:

```bash
git branch -r --merged origin/dev   # or: git branch --merged dev, if no remote yet
```

If the previous slice branch is **not** present in the merged list, **stop
and ask the user** whether to proceed anyway (branching off `dev` as-is)
or wait. This is the Sequencing Rule — never branch off an unmerged slice
branch.

## 3. Create the Branch

Create a new branch from `dev`. The branch name is derived from the slice
doc's filename (minus the `slice-` prefix and `.md` suffix), prefixed with
`slice/`:

```
ai/docs/vertical-slices/slice-04-create-transcription-job-endpoint.md
    → branch: slice/04-create-transcription-job-endpoint
```

```bash
git checkout -b slice/<NN>-<name> dev
```

Never branch off another slice's unmerged branch.

## 4. Read the Slice Doc

Read the slice's self-contained doc:

```bash
read ai/docs/vertical-slices/slice-<NN>-<name>.md
```

Each slice doc contains the following sections — here is what each tells
you and how to act on it:

| Section | What it tells you |
|---|---|
| **Goal** | The one-sentence outcome of the slice. Use it to frame the work. |
| **Scope** | What this increment does and does not cover yet — keep work inside this boundary. |
| **Tasks** | Exact file/directory structure to create, dependencies to add, and concrete code/behavior to implement. Treat file paths and shapes (JSON fields, status codes, error messages) as exact, not illustrative. |
| **Tests** | Which test files to add and what they must assert. |
| **Acceptance Criteria** | Specific, verifiable behaviors. Implement and verify every one before presenting for review. |

Some slices also reference specific functional-spec / architecture-spec
section numbers inline (e.g. "see architecture §9") — follow those
references rather than re-reading the whole spec.

## 5. Follow the References

Where a slice doc cites a spec section number, navigate to the matching
split document instead of the monolithic spec:

- **Functional spec sections**: the topic-split file under
  `ai/docs/functional/` (e.g. `ai/docs/functional/03-create-transcription-job.md`).
- **Architecture spec sections**: the topic-split file under
  `ai/docs/architecture/` (e.g. `ai/docs/architecture/09-repository-architecture.md`).

If a split document and an original spec ever disagree, the original spec
file (`functional-specification.md` / `architecture-specification.md`)
wins — flag the discrepancy to the user rather than silently picking one.

These references contain the design decisions you must implement. Do not
guess or extrapolate beyond what they specify.

## 6. Implementation Rules

The following domain and architectural constraints must be preserved in
every slice (full detail in `CLAUDE.md`); key rules:

- **Layering**: API routes are thin (no business logic); `TranscriptionService`
  owns all use cases and all commit/rollback; repositories receive an active
  session and never commit or touch files/the transcriber.
- **Job UUID before file save**: generate the job UUID before saving the
  uploaded file; filename is `{job_id}.{ext}`. If DB job creation fails
  after the file was saved, delete the saved file. If file save fails, no
  job is created.
- **Ordering differs by endpoint**: the worker claims the **oldest pending**
  job (`created_at ASC`); the list endpoint orders **newest first**
  (`created_at DESC`). Do not unify these.
- **Response shape**: list endpoint returns `TranscriptionJobListItem`
  (never `text` or `stored_audio_path`); only the single-job endpoint
  returns `TranscriptionJobResponse` (includes `text`). `stored_audio_path`
  is never exposed via the API at all.
- **Audio cleanup**: the worker deletes the uploaded audio file after
  processing regardless of success or failure; deletion errors are logged,
  not raised. Storage deletion must be safe to call on a missing file.
- **Exact failure messages**: missing audio file at processing time →
  job `failed` with exactly `Audio file is no longer available.`;
  transcription exceptions → job `failed` with exactly
  `Could not transcribe the audio file.` (full traceback to worker logs
  only, never to the API response).
- **Empty transcript is success**: empty output text is still `completed`
  with `text = ''`, not a failure.
- **Text normalization**: join segment texts, strip, collapse repeated
  whitespace.
- **Language handling**: client-supplied `language` is kept as-is; if null,
  store whatever Faster Whisper detects. Validate with `^[a-z]{2,5}$` at
  upload time.
- **Upload validation** (extensions `mp3`/`wav`/`m4a`/`ogg`/`webm`, 25 MB
  max, reject empty) lives in the service layer / a small helper, never
  scattered across the route.
- **Single worker, single job at a time** is an explicit v1 assumption —
  do not add concurrency or multi-worker safety in any slice.
- **Model loading**: Faster Whisper model loads once at worker startup; if
  loading fails, the worker exits without entering the polling loop (it
  does not mark jobs failed for this).
- **Timestamps**: always via `app/utils/time.py`'s `utc_now()` (UTC-aware),
  never naive datetimes.
- **No extra endpoints**: no retry, cancel, or delete endpoints in v1
  (see `ai/docs/vertical-slices/99-commit-sequence-and-notes.md` §6).

## 7. Test Conventions

All tests must follow these rules (from `CLAUDE.md` and
`ai/docs/architecture/20-testing-architecture.md`):

- **Layout by concern, not by mirrored source path**:
  `tests/unit/`, `tests/api/`, `tests/worker/`, `tests/integration/`.
- **Default `uv run pytest` must never require a real Faster Whisper
  model** — use the `FakeTranscriber` pattern (architecture spec §25.3) in
  unit/API/worker tests.
- **Database**: in-memory SQLite for unit/API tests; temp file-backed
  SQLite for worker/integration tests. Use `tmp_path` for upload
  directories. Never touch the real `./data` dev database or upload dir
  from tests.
- **Real Faster Whisper tests** must be marked `@pytest.mark.integration`
  and are excluded from the default run (`uv run pytest -m "not
  integration"` is the explicit opt-in form; default config already
  excludes them).
- Every slice requires tests matching its own "Tests" section **and**
  passing the full Acceptance Criteria list before being presented for
  review.

## 8. Quality Gate

Before presenting the slice for review, run all three:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

All must pass. If something fails, fix it or clearly report the failure.
**Do not present a slice for review with a known-failing gate.**

## 9. Review Process

Present a summary of the changes including:

1. What was implemented (reference the slice name/number)
2. The diff (files created/modified)
3. Test results (pytest output)
4. How each acceptance criterion from the slice doc was met

Then **stop and wait for the user's explicit approval**. Do not assume
approval from silence, unrelated prior approval, or from the user moving
to a different topic.

If the user requests changes: iterate uncommitted on the same branch,
re-run the quality gate, and re-request review. Do not commit partial or
intermediate states.

## 10. Post-Approval

Only once the user explicitly approves:

```bash
git add -A
git commit -m "slice <NN>: <brief description of what was implemented>"
git push -u origin slice/<NN>-<name>
```

(Skip the push if no remote is configured yet — confirm with the user.)

Then create a pull request to `dev` and give the user the link:

```bash
gh pr create --base dev --head slice/<NN>-<name> --title "Slice <NN>: <description>" --body "Implements slice <NN>."
```

Copy the URL from the output and present it to the user. **Do not** approve,
merge, or take any further action — the user will review and merge the PR
themselves.

## 11. Sequencing Rule (next slice)

If asked to start slice `N+1` before slice `N`'s branch is merged:
point out that `dev` does not yet contain the prior slice and ask whether
to proceed anyway (branching off `dev` as-is) or wait. Reference the
Sequencing Rule in step 2 above and the branching model in
`ai/docs/architecture/21-ci-and-branching-architecture.md`.
