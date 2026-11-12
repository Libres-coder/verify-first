#!/usr/bin/env python3
"""PreToolUse hook wrapper for the verify-first evidence gate.

Reads the hook JSON from stdin; only acts on `git commit` commands.
On gate failure, prints the gate's message to stderr and exits 2 (block the
tool call with feedback). Never blocks anything else; never fails open on
errors - if the gate cannot run, the commit is allowed but a warning is
printed (failing closed on a broken hook would brick the repo).
"""
import json
import os
import re
import subprocess
import sys

COMMIT_RE = re.compile(r"(^|\s)git(\s+-C\s+\S+)?\s+commit\b")

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_gate.py")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = data.get("tool_input", {}).get("command", "")
    if not COMMIT_RE.search(cmd):
        return 0
    try:
        p = subprocess.run([sys.executable, GATE, "--repo", os.getcwd()],
                           capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
    except Exception as e:
        print("verify-gate hook: gate could not run (%s); allowing commit." % e, file=sys.stderr)
        return 0
    if p.returncode == 1:
        print(p.stdout, file=sys.stderr)
        print(p.stderr, file=sys.stderr)
        return 2  # block with feedback
    return 0


if __name__ == "__main__":
    sys.exit(main())
