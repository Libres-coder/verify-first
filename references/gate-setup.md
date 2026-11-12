# Evidence gate deployment (verify_gate)

## Local hook (blocks git commit)

Project `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<verify-first install path>/scripts/gate_hook.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

gate_hook.py matches only `git commit` (including `git -C <path> commit`); every other
command passes through untouched. On gate failure it exits 2, blocking the commit and
showing the reason. If the gate itself crashes, the commit is allowed with a warning
(never brick a repo because the hook broke).

## CI gate (PR level)

`.github/workflows/verify.yml`:

```yaml
name: verify-gate
on:
  pull_request:
jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Evidence gate
        run: |
          curl -fsSL -o /tmp/verify_gate.py <verify-first release URL>/scripts/verify_gate.py
          python /tmp/verify_gate.py --repo . --strict --require-structure
```

Note: evidence lives inside the repository (`verify-<app>/evidence/`), so CI sees it -
evidence travels with the code by design. `--strict` makes repos that claim verify-first
fail when the verify skill is missing.

## Gate semantics

| State | exit | Behavior |
|---|---|---|
| evidence exists and is newer than newest source | 0 | pass |
| no evidence / evidence stale | 1 | block, list stale files |
| no verify-<app> skill (not a verify-first project) | 2 | pass (with --strict: fail) |

## Git-aware freshness (v1.2, preferred)

After a successful verification run, record the verified commit:

```bash
python scripts/verify_gate.py --repo . --stamp   # writes verify-<app>/verified.json
```

With a stamp present, the gate compares the working tree against that commit:
`git diff --name-only <sha> -- .` plus untracked files (`git ls-files --others`),
excluding `.claude/` and bookkeeping files (PROGRESS.md, README*, LICENSE*, CHANGELOG*,
CONTRIBUTING*, .gitignore). Any tracked or untracked source change -> stale.
This replaces mtime comparison wherever git can answer; **mtime misjudges fresh clones
and `git checkout`** (all files appear new), which is the exact regression the
`test_fresh_clone_passes` test pins down. Without a stamp (or outside git) the gate
falls back to mtime comparison.

Exemption: `--ignore GLOB` excludes files that need no verification (docs only).
`.claude/` and .git, node_modules etc. never count as source.

## Structure validation (anti-fake-evidence, v1.1)

`--require-structure` adds a content check on every evidence file:

- must contain at least one fenced code block (```) - the captured output;
- must contain at least one tier keyword (measured / inferred / guessed).

Files failing this count as missing evidence. This blocks empty placeholder files and
narrative-only notes; it cannot prove the output is genuine (a human review stage still
spot-checks tiers, per stages.md stage 5).
