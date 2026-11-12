# Contributing

- Keep the skill an **integration layer**: delegate to installed tools, do not
  reimplement their capabilities.
- Every stage's exit condition must be checkable; if you add one, write how it is
  verified.
- Gate changes need tests (`tests/test_gate.py`); run before opening a PR.
- Be honest in docs: state limits (heuristic proxies, stand-in environments) explicitly.
