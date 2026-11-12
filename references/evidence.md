# Evidence standards

Everything this pipeline trusts rests on evidence. Three tiers, and every report must
label its tier:

| Tier | Definition | Example |
|---|---|---|
| **measured** | observable output of a real command / real path run | response body of `curl -s localhost:3000/api/todos`; verify-<app> screenshot + state assertion |
| **inferred** | derived from measured results, not directly observed | "A returned 200, so module B is fine" |
| **guessed** | no evidence | "should work" |

## Proof standards

Proof standards (real user path, action+result state, side-effect verification, mock
boundaries, dry-run observation, evidence surviving cleanup) follow `create-verification-skill`'s
Evidence section - **the generator's current version is authoritative**; this file does
not duplicate them to avoid drift. This pipeline adds three things the generator does
not have: the tier system, the persistence convention, and the anti-pattern list.

### Pipeline addition: tier labels (every evidence item carries one)

### Persistence convention

- Path: `<repo>/.claude/skills/verify-<app>/evidence/<YYYY-MM-DD>/`;
- Naming: `<criterion-id>-<short>.md` + attachments (png screenshots, txt transcripts);
- Each item records: command/path, key output excerpt, result state, tier label
  (measured/inferred/guessed).

## Anti-patterns (redo when seen)

- "should be fine" verbal completion;
- pasting only the last output line (loses the root cause);
- weakening the test to make it pass (instead of fixing the implementation);
- verification scripts testing only the happy path, never failures;
- an empty evidence directory while the PR claims "tested".
