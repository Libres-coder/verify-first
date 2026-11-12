# Dogfood 1 — Web UI + JSON API (`demo-todo`)

Pipeline run on a zero-dependency todo app (Python `http.server` + static frontend),
4 acceptance criteria. Full artifacts live in the private demo repo; this record keeps
the method and evidence excerpts.

## Stage outputs

| Stage | Artifact |
|---|---|
| Spec | `spec.md`: R1 create, R2 list, R3 toggle, R4 UI+refresh persistence - all command/UI-judgeable |
| Architect | `ARCHITECTURE.md` produced by feature-dev `code-architect` (endpoint table, data flow, storage decision, startup contract) |
| Build | `server.py` + `index.html` + `app.js`; R1-R3 verified by curl (201/200/200, error paths 400/405) |
| Verify | generated `verify-demo` skill (Launch/Doctor/Drive/Evidence/Cleanup + 4-feature map); 5 measured evidence files incl. browser three-state snapshots |
| Ship | commit gated by the evidence hook; PROGRESS.md as stage artifact |

## Evidence highlights (measured)

- R1: `curl -X POST /api/todos -d '{"text":"buy milk"}'` → `HTTP 201` + JSON body.
- R3: PATCH → 200 `done:true`; follow-up GET shows `done:true` persisted.
- R4: Chrome DevTools MCP drove the real page: fill → Enter → snapshot shows the new
  row; **reload → snapshot shows both rows** (persistence). Evidence survived cleanup
  (5/5 files after server stop).

## Findings from this run

- The gate blocked a commit after `app.js` was touched post-verification (stale
  evidence listed by name), then passed after re-verification refreshed evidence.
- The architect agent failed once on an upstream billing error; recovery rule
  (re-dispatch stage 2) worked as written.
