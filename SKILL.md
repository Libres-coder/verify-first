---
name: verify-first
description: "Evidence-gated full-stack development pipeline: spec, architecture, incremental build, real-app verification, and shipping - every stage produces proof, no stage claims done without it. Use when the user asks to build a new app, feature or service end-to-end (frontend + backend), when they ask for production-quality delivery, when an end-to-end build's project has no verification harness yet, or when they say verify-first / evidence-first / 证据闭环 / 全栈流水线 / 按验收标准交付. Not for single-file fixes, small scope changes, or throwaway prototypes - use ds-plan-loop or mattpocock prototype directly."
---

# Verify-First

A five-stage pipeline. One iron rule: **no stage may claim completion without evidence.**
Every stage has an explicit exit condition (its evidence); evidence standards live in
`references/evidence.md`.

## Stage overview

| Stage | Tool (installed) | Exit condition |
|---|---|---|
| 1. Spec | mattpocock to-spec or a lightweight spec.md | Acceptance criteria list, each judgeable pass/fail |
| 2. Architect | feature-dev code-architect agent | Component blueprint + file list + data flow |
| 3. Build | ds-plan-loop + ds-verify-loop | Implementation per criterion + check evidence (or explicit stage-4 deferral) |
| 4. Verify | create-verification-skill (generates verify-<app>) | Real-app verification: feature map driven + evidence persisted |
| 5. Ship | ds-review-loop + commit-commands + verify-gate | PR description with the evidence table |

## Execution rules

1. **Spec first, criteria written down.** Every requirement must have judgeable
   acceptance criteria (command, URL, UI path, observable state). "Feature description"
   without criteria is sent back for rewrite (see `references/stages.md` stage 1). If
   superpowers brainstorming is active, finish its clarification first - brainstorming
   clarifies the need, this pipeline delivers it.
2. **Architecture before code, blueprint before files.** Stage 2 produces a blueprint
   down to files and types; no implementation starts without it.
3. **Build criteria one at a time.** One criterion = one ds-plan-loop step; every change
   passes through ds-verify-loop (run the tests; if none exist, write the smallest
   failing check first). Do NOT implement everything then verify at the end.
4. **Verification gate (execution discipline).** After stage 3, if the project has no
   verification skill, run `create-verification-skill` to generate verify-<app>; then
   drive the feature map (coverage = everything deferred from stage 3 plus criteria the
   change touches - see stages.md) and persist evidence per `references/evidence.md`.
   After a successful run, record the verified commit: `verify_gate.py --stamp` (git
   repos; mtime fallback applies otherwise). **A "done" without verification evidence
   is not done.**
5. **Ship with evidence.** Before committing run `scripts/verify_gate.py` (blocks when
   evidence is missing/stale; hook and CI wiring in references/gate-setup.md); use
   commit-commands `/commit-push-pr` (PR must carry: criteria -> evidence paths;
   unverified items listed with risk); small changes without a PR use `/commit`.
   Run ds-review-loop first, and include one evidence-tier spot check
   (measured/inferred/guessed must match the content).

## Interruption and recovery

- If a stage is interrupted: read the repo's spec.md / PROGRESS.md / evidence directory
  and resume from the matching stage; if absent, rebuild context with ds-context-reset.
- The stage-4 verification skill and feature map are **repository assets** - once
  generated they live in `<repo>/.claude/skills/verify-<app>/` and are reused and
  maintained for later tasks (maintain-verification-skill).

## Hard rules

- Don't skip stage 4: even under time pressure, run the minimum verification (one
  real-app proof for one criterion) and label the rest unverified.
- Don't fabricate evidence: verification must be a real user path + observable state
  change, not internal setters or test-only endpoints (see evidence.md).
- Don't make product decisions for the user: stage-1 criteria and stage-2 trade-offs
  are confirmed with the user.
