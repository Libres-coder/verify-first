# Weak-model compensation rules (DeepSeek et al.)

Extra discipline for running this pipeline on weaker models. Trigger: the session model
is deepseek-* / another non-Claude model, or symptoms are observed (skipped steps, fake
completion, fix-looping, long-run drift).

## Rules (always on)

1. **Short loops**: <= 3 actions per step (change one thing, run one check, read the
   output); split anything larger;
2. **Hard caps**: two failed attempts at the same fix -> ds-unstick (change the premise,
   test the assumption); no third micro-variation;
3. **One variable at a time**: otherwise attribution is impossible;
4. **Drift control**: for multi-stage work keep PROGRESS.md (per stage: what was done /
   where the evidence is / next step) and read it at the start of every round;
5. **Context hygiene**: read files in ranges, excerpt logs, delegate wide searches to
   subagents;
6. **Declare tiers**: label every conclusion measured/inferred/guessed (see evidence.md);
   weaker models love to promote inferred to measured - re-check your own labels.

## Common weak-model failures and counters

| Failure | Counter |
|---|---|
| Skips stage 4, declares done | Gate: no evidence directory = not done (an execution-discipline rule in SKILL.md; the skill cannot literally prevent violations) |
| Invents APIs/parameters | Stage 3 runs the real check after every change; look up unsure library APIs via context7 |
| Verification tests only happy paths | evidence.md anti-pattern list; a dedicated check in the review stage |
| Forgets the spec in long tasks | PROGRESS.md + stage-1 criteria list reviewed at every step |
| Verbose output bloating context | Report format = conclusion + evidence path, not raw dumps |

## Division of labor (no duplication)

- ds-mode / ds-principles: working style and engineering rules within a task;
- ds-plan-loop / ds-verify-loop / ds-unstick: this pipeline's stage-3 execution engine;
- This file: only what is pipeline-specific about compensating weak models.
