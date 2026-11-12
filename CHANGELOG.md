# Changelog

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
