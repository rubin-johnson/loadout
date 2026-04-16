# Contributing to Loadout

## Development Setup

```bash
git clone https://github.com/rubin-johnson/loadout.git
cd loadout
uv sync
uv run pytest tests/ -v
```

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Single file
uv run pytest tests/test_apply.py -v
```

Tests operate entirely on temp directories — your `~/.claude/` is never touched.

### Test categories

| File | What it tests |
|------|---------------|
| `test_apply.py` | `atomic_apply` unit logic |
| `test_apply_cmd.py` | `apply` CLI integration (state, backup, dry-run) |
| `test_pack.py` | `pack` CLI (secrets, db skip, output) |
| `test_bt.py` | Roundtrip integration, validation CLI, CI/env-var paths |
| `test_manifest.py` | Manifest loading and semver validation |
| `test_validate.py` | Package validation errors |
| `test_restore.py` | Restore from backup, `placed_paths` cleanup |
| `test_backup.py` | Backup create/list/latest |
| `test_secrets.py` | Secret pattern detection |
| `test_state.py` | State file read/write/clear |
| `test_status.py` | Status display |
| `test_scaffold.py` | CLI help, imports, alias visibility |

## Making Changes

1. Create a branch: `git checkout -b feat/my-change`
2. Write a failing test first
3. Implement the fix/feature
4. Ensure all tests pass: `uv run pytest tests/ -v`
5. Commit with a concise, imperative message: `git commit -m "add foo to bar"`

## Code Style

- No runtime dependencies beyond PyYAML and stdlib
- Simple > clever; match existing patterns
- No excessive comments, docstrings on internals, or type annotations beyond what's already there
- Prefer editing existing files over creating new ones

## Package Structure

A loadout package is a directory containing:
- `manifest.yaml` — name, version, author, description, targets
- Files declared in `targets` (CLAUDE.md, settings.json, hooks/, bin/)

See `examples/token-miser/` for a working example.

## Terminology

| Term | Meaning |
|------|---------|
| **package** | A versioned directory of Claude Code config files with a manifest |
| **pack** | Snapshot a live `~/.claude` directory into a package |
| **apply** | Deploy a package to a target directory |
| **restore** | Roll back to the backup created before the last apply |
| **target** | The directory being written to (default: `~/.claude`) |
