# Changelog

## [1.2.0] - 2026-11-13

### Added
- Git-aware evidence freshness: `verify_gate.py --stamp` records the verified commit
  (`verify-<app>/verified.json`); the gate then compares the working tree against that
  commit (tracked diff + untracked files, excluding `.claude/` and bookkeeping files).
  Fixes mtime misjudgment on fresh clones and git checkouts; mtime remains the fallback
  when no stamp exists or git cannot answer.
- `test_fresh_clone_passes`: clones a stamped repo and asserts the gate passes
  (regression pin for the mtime flaw).

## [1.1.0] - 2026-11-13

### Added
- `--require-structure` evidence validation: every evidence file must contain a fenced
  code block (captured output) and a tier label (measured/inferred/guessed); files
  failing this are ignored, and the gate fails when none remain. The PreToolUse hook
  enables it by default - closes the "empty/fake evidence file" hole.
- Default ignores for bookkeeping files (PROGRESS.md, README*, LICENSE*, CHANGELOG*,
  CONTRIBUTING*, .gitignore): they never invalidate evidence by themselves (found by
  dogfooding: a PROGRESS.md update had marked evidence stale).

### Changed
- All skill docs translated to English (SKILL.md + references); Chinese trigger words
  kept in the description for CJK users. README.zh-CN.md retained.

## [1.0.0] - 2026-11-13

### Added
- Five-stage evidence-gated pipeline (spec / architecture / build / verify / ship)
  as a Claude Code skill, delegating to installed tools instead of reimplementing.
- Evidence gate: `scripts/verify_gate.py` (missing/stale evidence detection, exit
  codes 0/1/2, `--strict`, `--ignore`) and `scripts/gate_hook.py` (PreToolUse hook
  blocking `git commit` only).
- Weak-model compensation rules (short loops, hard caps, single-variable changes,
  PROGRESS.md drift control).
- Two field-tested dogfood runs with per-criterion evidence (web UI + API; CLI).

### Changed (post-review fixes)
- Stage 3 exit now allows an explicit "defer to stage 4" list for UI criteria.
- PROGRESS.md is a mandated artifact of every stage (recovery path wired).
- Trigger description narrowed + negative domain; evidence standards reference the
  generator instead of duplicating it.

### Testing
- 8 gate tests covering exit codes, strict mode, ignore patterns, hook commit matching
  (including `git -C`), fresh/stale evidence, malformed hook input.
