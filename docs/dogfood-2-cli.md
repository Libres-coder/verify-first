# Dogfood 2 — CLI tool (`demo-todoctl`)

Second dogfood on a different verification surface: a single-file CLI todo manager
driven as a subprocess, 5 acceptance criteria. Proves the pipeline's stack-agnostic
claim (no browser, no server; evidence = process transcripts and exit codes).

## Stage outputs

| Stage | Artifact |
|---|---|
| Spec | `spec.md`: R1 add, R2 list, R3 done, R4 cross-process persistence, R5 error codes |
| Architect | `ARCHITECTURE.md` written inline (deviation noted: the code-architect agent integration was already proven in dogfood 1; for a single-file CLI the blueprint was written directly) |
| Build | `todoctl.py` (~75 lines, stdlib only); R1-R5 all green including stderr/exit-code paths (2/3/2) |
| Verify | generated `verify-todoctl` skill (subprocess-driven recipe, 5-feature map); 6 measured evidence files |
| Ship | PreToolUse gate wired in the project; commit passed with 6 evidence files |

## Evidence highlights (measured)

- R3: `done 1` → `done #1`; follow-up `list` shows `1. [x] buy milk` (action + state).
- R4: `add` in one process, `list` in a second process → data persisted in
  `todos.json` (true cross-process proof, not same-process memory).
- R5: `add ""` → stderr `error: text is required`, exit 2; `done 99` → exit 3;
  unknown command → exit 2.

## Findings from this run

- CLI verification needs no special tooling: subprocess execution + exit codes are
  sufficient evidence when the spec writes criteria that way.
- The isolated-state requirement (move/backup `todos.json` before driving, restore in
  cleanup) belongs in the generated verify skill's Launch section - recorded and
  applied.
