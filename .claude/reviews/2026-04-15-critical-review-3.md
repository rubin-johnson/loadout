# Critical Review — Iteration 3 (review-fix-loop-0, iteration 1)
**Date:** 2026-04-15
**Reviewer model:** Opus 4.6 (code-reviewer agent)
**Tests at time of review:** 85 passed

## Critical (0)
None.

## Important (2)
1. [restore.py:60] `shutil.copytree` raises `FileExistsError` on selective restore with subdirectory entries — FIXING
2. [secrets.py:12] `export VAR=VALUE` pattern is unconditional false positive generator — FIXING

## Watch (2)
3. [tests/test_restore.py] No test for restore with directory-level entry in placed_paths — FIXING (with #1)
4. [tests/test_apply_cmd.py] No test for apply without --yes in non-TTY returning exit 1 — FIXING
