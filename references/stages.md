# Stage details

## Stage 1: Spec - criteria written down

**Tool**: mattpocock `to-spec`. Note: to-spec is `disable-model-invocation` - **only
the user can trigger it via `/to-spec`**; an executing agent cannot. Ask the user to run
it, or (no tracker / user unavailable) write a lightweight `spec.md` directly. Product
trade-offs are still confirmed with the user per SKILL.md rule 3 (to-spec's "do not
interview the user" only constrains its own synthesis, not this pipeline's product
decisions).

**Output**: `spec.md` (or issues), each requirement shaped like:

```markdown
## Requirement: users can create a todo
- Accept: after POST /api/todos, GET /api/todos returns the item (command-judgeable)
- Accept: after the form submits, the list shows the new row (UI-path judgeable)
- Non-goals: drag sorting (not this iteration)
```

**Exit condition**: every requirement has >= 1 judgeable acceptance criterion;
`non-goals` are explicit. Each criterion names its **judging method** (command / URL /
UI path / observable state) - subjective words like "looks nice" are not allowed;
subjective requirements are marked "manual acceptance" and **must have the user's sign-off
before stage 5 or they count as unverified**. Update `PROGRESS.md` (what was done /
evidence paths / next step).

**Weak-model note**: re-read the spec and rewrite every criterion that cannot be judged
by a command/URL into one that can, or mark it manual.

## Stage 2: Architect - blueprint first

**Tool**: feature-dev `code-architect` agent (subagent).

**Output**: architecture blueprint - component breakdown, key type/interface
signatures, file list (new/modified), data flow, tech-choice rationale. If the blueprint
conflicts with the spec, resolve one or the other explicitly; never start with a live
conflict.

**Exit condition**: blueprint covers every spec requirement; each component's job fits
in one sentence; file list is path-specific. Update `PROGRESS.md`.

## Stage 3: Build - implement criteria incrementally

**Tool**: ds-plan-loop (step plan) + ds-verify-loop (per-change check loop).

**Flow**:
1. Break acceptance criteria into steps (one criterion = one or a few steps, each with a
   checkable artifact);
2. Per step: smallest implementation -> run the real check (tests if they exist;
   otherwise write the smallest failing check first) -> record the evidence;
3. A step passes before the next one starts; the same step failing twice -> ds-unstick.

**Exit condition**: every spec criterion has an implementation; **each has check
evidence (command + output excerpt) OR is explicitly listed in the "deferred to stage 4"
list** (typically UI criteria - the verification harness only exists after stage 4; do
not pretend stage 3 verified them); unimplemented items listed with reasons (confirmed
with the user). Update `PROGRESS.md` (including the deferral list).

## Stage 4: Verify - drive the real app (mandatory gate)

**Tool**: pstack `create-verification-skill` (generates a project-local verify-<app>).

**Flow**:
1. No `verify-<app>` yet -> run create-verification-skill: interview the repo (surface /
   run / drive / observe / isolate) -> generate the skill (Launch/Doctor/Drive/Evidence/
   Cleanup + feature map) -> **prove the generated skill itself first** (its own
   requirement: run it end to end once, cleanup, confirm evidence survives);
2. Drive the feature map with verify-<app>; **coverage = every item deferred from stage
   3 + other criteria the change touches** ("touches" = criteria corresponding to the
   files/interfaces this change modified, plus new feature-map entries);
3. Persist evidence to `verify-<app>/evidence/<date>/` (screenshots, terminal
   transcripts, response bodies, logs).

**Exit condition**: every deferred item and every touched criterion has real-app
evidence; evidence paths listed in PROGRESS.md and carried into stage 5. **This stage is
the hard requirement of the pipeline: stage 5 does not start without it.** If the app
genuinely cannot be driven locally (production-only dependency), use the minimal drivable
stand-in (container/local stack) and **list every difference from the real target**
(those differences count as unverified). Update `PROGRESS.md`.

## Stage 5: Ship - evidence table into the PR

**Tool**: ds-review-loop (author + fresh-context reviewer) + commit-commands + this
skill's `scripts/verify_gate.py`.

**Pre-commit gate (production mechanism)**: `python <verify-first>/scripts/verify_gate.py
--repo <repo>` - exit 1 when evidence is missing or stale (source newer than evidence).
Recommended: wire into the project's `.claude/settings.json` PreToolUse hook (blocks `git
commit`; setup example in `references/gate-setup.md`); run it in CI with `--strict`.

**PR description template**:

```markdown
## Acceptance criteria and evidence
| Criterion | Evidence | Status |
|---|---|---|
| POST /api/todos creates | verify-todo/evidence/.../todos.md | OK real-app |
| ... | ... | ... |

## Unverified items and risks
- (items not covered in stage 4 and why)
```

**Exit condition**: PR evidence table complete; unverified items labeled; ds-review-loop
agreement (or round cap recorded with the disagreement); one evidence-tier spot check
done. Update `PROGRESS.md`.
