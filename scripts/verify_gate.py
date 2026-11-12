#!/usr/bin/env python3
"""verify-first evidence gate.

Blocks commits / PRs in a verify-first project when:
  1. the project has a verify-<app> skill but no evidence at all, or
  2. the newest source change is newer than the newest evidence file
     (implementation changed after last verification -> evidence is stale).

Exit codes:
  0 - evidence present and fresh
  1 - gate FAILED (no evidence, or stale evidence)
  2 - not a verify-first project (no .claude/skills/verify-* found) -> do not block

Usage:
  python verify_gate.py [--repo PATH] [--app NAME] [--ignore GLOB]... [--strict]

--strict turns "not a verify-first project" (exit 2) into exit 1 - for CI on
repos that SHOULD follow the pipeline.
"""
import argparse
import glob
import os
import re
import sys
import time

IGNORE_DIRS = {".git", "node_modules", "__pycache__", "graphify-out"}
# Bookkeeping/community files never invalidate evidence by themselves.
DEFAULT_IGNORES = ["PROGRESS.md", "README*", "LICENSE*", "CHANGELOG*", "CONTRIBUTING*", ".gitignore"]


def find_verify_dirs(repo):
    return sorted(glob.glob(os.path.join(repo, ".claude", "skills", "verify-*")))


def newest_evidence(repo, app=None):
    pattern = os.path.join(repo, ".claude", "skills",
                           ("verify-" + app) if app else "verify-*",
                           "evidence", "**", "*")
    files = [f for f in glob.glob(pattern, recursive=True) if os.path.isfile(f)]
    return files


def newest_source(repo, evidence_files, ignores):
    ev = set(os.path.abspath(f) for f in evidence_files)
    newest = 0.0
    changed = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        # skip the .claude tree entirely: skills/evidence/hooks are not source
        if os.path.basename(root) == ".claude":
            dirs[:] = []
            continue
        for f in files:
            p = os.path.join(root, f)
            if os.path.abspath(p) in ev:
                continue
            if any(fnmatch(p, ig) for ig in ignores):
                continue
            try:
                mt = os.path.getmtime(p)
            except OSError:
                continue
            if mt > newest:
                newest = mt
                changed = [p]
            elif mt == newest:
                changed.append(p)
    return newest, changed


def fnmatch(path, pattern):
    import fnmatch as _fn
    return _fn.fnmatch(os.path.basename(path), pattern) or _fn.fnmatch(path, pattern)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--app", default=None, help="verify-<app> name filter")
    ap.add_argument("--ignore", action="append", default=[],
                    help="glob patterns for source files exempt from the staleness check")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--require-structure", action="store_true",
                    help="require every evidence file to contain a fenced code block "
                         "and a tier keyword (measured/inferred/guessed)")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    verify_dirs = find_verify_dirs(repo)
    if not verify_dirs:
        if args.strict:
            print("VERIFY GATE FAIL: no verify-<app> skill found (--strict).")
            return 1
        print("verify-gate: not a verify-first project (no verify-* skill); passing.")
        return 2

    ev = newest_evidence(repo, args.app)
    if not ev:
        print("VERIFY GATE FAIL: no verification evidence under "
              ".claude/skills/verify-*/evidence/.")
        print("Run the verify-<app> skill (drive the real app, capture evidence) "
              "before committing.")
        return 1

    if args.require_structure:
        tier_re = re.compile(r"measured|inferred|guessed", re.IGNORECASE)
        valid, invalid = [], []
        for f in ev:
            try:
                body = open(f, "r", encoding="utf-8-sig", errors="replace").read()
            except OSError:
                invalid.append((f, "unreadable"))
                continue
            fences = body.count("```")
            has_tier = bool(tier_re.search(body))
            if fences >= 2 and has_tier:
                valid.append(f)
            else:
                reason = []
                if fences < 2:
                    reason.append("no fenced output block")
                if not has_tier:
                    reason.append("no tier label")
                invalid.append((f, ", ".join(reason)))
        if not valid:
            print("VERIFY GATE FAIL: no evidence file passes structure validation.")
            for f, why in invalid[:10]:
                print("  %s: %s" % (os.path.relpath(f, repo), why))
            print("Evidence must contain the captured command output (fenced block) "
                  "and a tier label (measured/inferred/guessed).")
            return 1
        if invalid:
            print("verify-gate: note - %d evidence file(s) failed structure validation "
                  "and were ignored:" % len(invalid))
            for f, why in invalid[:5]:
                print("  %s: %s" % (os.path.relpath(f, repo), why))
        ev = valid

    src_newest, changed = newest_source(repo, ev, DEFAULT_IGNORES + args.ignore)
    ev_newest = max(os.path.getmtime(f) for f in ev)
    # 1 second epsilon for filesystem timestamp granularity
    if src_newest > ev_newest + 1:
        print("VERIFY GATE FAIL: evidence is stale.")
        print("Newest evidence: %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ev_newest)))
        print("Newest source:   %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(src_newest)))
        print("Files changed after last verification (max 10):")
        for p in sorted(set(changed))[:10]:
            print("  " + os.path.relpath(p, repo))
        print("Re-run the verify-<app> skill to refresh evidence, then commit.")
        return 1

    print("verify-gate: OK - %d evidence file(s), freshest %s"
          % (len(ev), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ev_newest))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
