# Critical Review — Iteration 1
**Date:** 2026-04-15
**Reviewer model:** Opus 4.6 (code-reviewer agent)
**Tests at time of review:** 84 passed

## Critical (2)
1. [apply.py:15-25] Path traversal in `_resolve_dest` — write outside target — FIXING
2. [restore.py:31-39] `placed_paths` from state file used without containment check — FIXING

## Important (4)
3. [tests/test_apply_cmd.py:46-52] Idempotent backup test is a timing false positive — FIXING (remove claim)
4. [__main__.py:11,24,81,85] Positional arg still named `bundle` — FIXING
5. [validate.py:8] Imports private `_REQUIRED_FIELDS`, `_SEMVER_RE` — WONTFIX (internal module boundary)
6. [apply.py:106, restore.py:59, validate.py:70] Orphaned backward-compat aliases — FIXING (remove)

## Watch (4)
7. No test for switching packages (apply A then apply B) — TODO
8. [pack.py:43-52] Secret scan doesn't cover CLAUDE.md or settings.json — TODO
9. [pack.py:57-60,79-80] Redundant `.db` checks — FIXING
10. [CHANGELOG.md] Old terminology — FIXING
