#!/usr/bin/env python3
"""Tests for verify_gate.py + gate_hook.py. Run: python tests/test_gate.py"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "..", "scripts", "verify_gate.py")
HOOK = os.path.join(HERE, "..", "scripts", "gate_hook.py")

T0 = time.time() - 1000  # baseline seconds


def touch(path, mtime, content="x\n"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    os.utime(path, (mtime, mtime))


EVIDENCE = "```\nHTTP 200 OK\n```\nmeasured\n"


def run_gate(args):
    return subprocess.run([sys.executable, GATE] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def run_hook(payload, cwd):
    return subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=cwd)


class GateTests(unittest.TestCase):
    def _repo(self, tmp):
        return os.path.join(tmp, "repo")

    def test_not_a_verify_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            os.makedirs(repo)
            p = run_gate(["--repo", repo])
            self.assertEqual(p.returncode, 2, p.stdout)
            p = run_gate(["--repo", repo, "--strict"])
            self.assertEqual(p.returncode, 1, p.stdout)

    def test_no_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            os.makedirs(os.path.join(repo, ".claude", "skills", "verify-app"))
            p = run_gate(["--repo", repo])
            self.assertEqual(p.returncode, 1, p.stdout)
            self.assertIn("no verification evidence", p.stdout)

    def test_fresh_evidence_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            touch(os.path.join(repo, "src", "app.py"), T0)
            touch(os.path.join(repo, ".claude", "skills", "verify-app",
                               "evidence", "d1", "e.md"), T0 + 500, EVIDENCE)
            p = run_gate(["--repo", repo])
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_stale_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            touch(os.path.join(repo, ".claude", "skills", "verify-app",
                               "evidence", "d1", "e.md"), T0, EVIDENCE)
            touch(os.path.join(repo, "src", "app.py"), T0 + 500)
            p = run_gate(["--repo", repo])
            self.assertEqual(p.returncode, 1, p.stdout)
            self.assertIn("stale", p.stdout)
            self.assertIn("app.py", p.stdout)

    def test_ignore_exempts_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            touch(os.path.join(repo, ".claude", "skills", "verify-app",
                               "evidence", "d1", "e.md"), T0, EVIDENCE)
            touch(os.path.join(repo, "docs", "notes.md"), T0 + 500)
            p = run_gate(["--repo", repo, "--ignore", "*.md"])
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_hook_only_blocks_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            touch(os.path.join(repo, ".claude", "skills", "verify-app",
                               "evidence", "d1", "e.md"), T0, EVIDENCE)
            touch(os.path.join(repo, "src", "app.py"), T0 + 500)
            # non-commit command -> allow
            p = run_hook({"tool_input": {"command": "git status"}}, repo)
            self.assertEqual(p.returncode, 0)
            # commit with stale evidence -> block (exit 2 + message)
            p = run_hook({"tool_input": {"command": "git commit -m x"}}, repo)
            self.assertEqual(p.returncode, 2)
            self.assertIn("stale", p.stderr)
            # -C form also matched
            p = run_hook({"tool_input": {"command": "git -C . commit -m x"}}, repo)
            self.assertEqual(p.returncode, 2)

    def test_hook_allows_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            touch(os.path.join(repo, "src", "app.py"), T0)
            touch(os.path.join(repo, ".claude", "skills", "verify-app",
                               "evidence", "d1", "e.md"), T0 + 500, EVIDENCE)
            p = run_hook({"tool_input": {"command": "git commit -m x"}}, repo)
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_hook_malformed_input_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            os.makedirs(repo)
            p = subprocess.run([sys.executable, HOOK], input="not json",
                               capture_output=True, text=True, cwd=repo)
            self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
