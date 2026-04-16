# Critical Review — Iteration 2
**Date:** 2026-04-15
**Reviewer model:** Opus 4.6 (code-reviewer agent)
**Tests at time of review:** 84 passed

## Critical (0)
None.

## Important (4)
1. [apply.py:65, restore.py:11] `yes` param accepted but never used — no confirmation guard — FIXING
2. [backup.py:12] `create_backup` never called from production code, test-only — FIXING (remove)
3. [tests/test_restore.py] `placed_paths` restore path only tested by roundtrip, not unit — FIXING (add test)
4. [tests/test_status.py:21] State fixture used stale `bundle_path` key — FIXED (naming pass)

## Watch (4)
5. [apply.py:23] `~/` path stripping maps to target, not home — WONTFIX (by design)
6. [apply.py:96-100] `_resolve_dest` called twice per entry — FIXED (walrus)
7. [pack.py:50] Secret scan warning loses subdirectory path — FIXED
8. [__main__.py:107-110] `capture` alias duplicates subparser — FIXED (removed subparser, alias via argv rewrite)

## Verification Review (Iteration 2 follow-up)

### Additional finding
9. [test_scaffold.py:31] `test_capture_alias_hidden_in_help` never asserted the negative — FIXED (added assert, caught real argparse bug, fixed alias approach)
