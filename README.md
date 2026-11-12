# verify-first

An evidence-gated full-stack development pipeline for Claude Code (and any agent that
reads SKILL.md). Five stages - **spec, architecture, build, verify, ship** - where every
stage has a provable exit condition and nothing is "done" without evidence.

Built for the real failure mode of AI coding: **claiming a fix works without running
it**. Instructions alone don't stop that reliably; mechanisms do. verify-first adds a
gate that blocks commits when verification evidence is missing or stale.

## What it composes (nothing reinvented)

| Stage | Tool it delegates to |
|---|---|
| Spec | mattpocock-skills `to-spec`, or a lightweight spec.md |
| Architecture | feature-dev `code-architect` agent |
| Build | deepseek-stack `ds-plan-loop` / `ds-verify-loop` / `ds-unstick` |
| Verify | pstack `create-verification-skill` (generates a project-local `verify-<app>` harness) |
| Ship | `ds-review-loop` + commit-commands `/commit-push-pr` + **this repo's evidence gate** |

## The evidence gate

```bash
python scripts/verify_gate.py --repo .          # exit 1 when evidence missing/stale
python scripts/verify_gate.py --repo . --strict # for CI on verify-first repos
```

- **exit 0**: evidence exists and is newer than the newest source change;
- **exit 1**: no evidence, or source changed after the last verification (stale);
- **exit 2**: not a verify-first project -> pass through.

`--require-structure` (on by default in the hook) additionally requires every evidence
file to carry a fenced output block and a tier label - empty or narrative-only evidence
is ignored, and the gate fails when nothing structured remains.

Wire it as a Claude Code PreToolUse hook to block `git commit`
(see `references/gate-setup.md`), or run it in CI on pull requests. Evidence lives in
`.claude/skills/verify-<app>/evidence/<date>/` and **travels with the code**.

## Install

```bash
cp -r verify-first ~/.claude/skills/
```

Then say "build X end-to-end, verify-first" - or just ask for production-quality
delivery. The skill activates on end-to-end builds, not on single-file fixes.

## Status: field-tested twice

Both dogfood runs are documented in `docs/` with per-criterion evidence:

1. **Web UI + JSON API** (`demo-todo`): 4 acceptance criteria, real browser driven via
   Chrome DevTools MCP, evidence survived cleanup, commit gated;
2. **CLI tool** (`demo-todoctl`): 5 acceptance criteria, subprocess-driven, cross-process
   persistence proof, gate blocked a stale-evidence commit then passed after re-verify.

## Testing

```bash
python tests/test_gate.py   # 8 tests: exit codes, strict, ignore, hook commit matching
```

## License

MIT
