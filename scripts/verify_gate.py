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
import json
import os
import re
import subprocess
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


def _git(repo, *args):
    try:
        p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True,
                           text=True, timeout=30, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout
    except Exception:
        return 1, ""


def git_head(repo):
    rc, out = _git(repo, "rev-parse", "HEAD")
    return out.strip() if rc == 0 and out.strip() else None


def pick_verify_dir(repo, app=None):
    dirs = find_verify_dirs(repo)
    if app:
        dirs = [d for d in dirs if os.path.basename(d) == "verify-" + app]
    return sorted(dirs)[0] if dirs else None


def find_stamp(repo, app=None):
    d = pick_verify_dir(repo, app)
    if not d:
        return None
    try:
        with open(os.path.join(d, "verified.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def changed_since(repo, sha, ignores):
    """Repo-relative source files changed since <sha> (tracked + untracked,
    excluding .claude/ and ignore globs). None when git cannot answer."""
    if not sha:
        return None
    rc, out = _git(repo, "diff", "--name-only", sha, "--", ".")
    if rc != 0:
        return None
    files = [f for f in out.splitlines() if f.strip()]
    rc2, out2 = _git(repo, "ls-files", "--others", "--exclude-standard")
    if rc2 == 0:
        files += [f for f in out2.splitlines() if f.strip()]
    return [f for f in files
            if not f.startswith(".claude/") and not any(fnmatch(f, ig) for ig in ignores)]


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
    ap.add_argument("--stamp", action="store_true",
                    help="after a successful verification run, record the current git "
                         "HEAD as the verified commit (verified.json in the verify dir)")
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

    if args.stamp:
        head = git_head(repo)
        target = pick_verify_dir(repo, args.app)
        if not head or not target:
            print("VERIFY GATE FAIL: --stamp requires a git repository and a verify-<app> dir.")
            return 1
        stamp = {"commit": head,
                 "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "evidence_files": len(ev)}
        with open(os.path.join(target, "verified.json"), "w", encoding="utf-8") as f:
            json.dump(stamp, f, ensure_ascii=False, indent=2)
        print("verify-gate: stamped %s at commit %s (%d evidence file(s))"
              % (os.path.relpath(target, repo), head[:12], len(ev)))
        return 0

    # ---- freshness: git-aware when a verified stamp exists, else mtime ----
    stamp = find_stamp(repo, args.app)
    head = git_head(repo)
    if stamp and head:
        changed = changed_since(repo, stamp.get("commit", ""),
                                DEFAULT_IGNORES + args.ignore)
        if changed is not None:
            if changed:
                print("VERIFY GATE FAIL: evidence is stale - source changed since the "
                      "verified commit %s." % str(stamp.get("commit", "?"))[:12])
                print("Files changed since verification (max 10):")
                for f in changed[:10]:
                    print("  " + f)
                print("Re-run the verify-<app> skill, then run this gate with --stamp, "
                      "before committing.")
                return 1
            print("verify-gate: OK - %d evidence file(s); no source changes since "
                  "verified commit %s." % (len(ev), str(stamp.get("commit", "?"))[:12]))
            return 0
        # git could not answer (unknown sha, detached, etc.) -> fall back to mtime

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
