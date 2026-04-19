# loadout

Claude Code configuration package manager — validate, apply, restore, pack.

## Common Commands
- Install/sync: `uv sync`
- Tests: `uv run pytest -q`
- Lint: `uv run ruff check src tests`
- Format: `uv run ruff format src tests`
- CLI help: `uv run loadout --help`

## Repo Notes
- Main CLI entrypoint: `src/loadout/__main__.py`
- Package format defined in `src/loadout/manifest.py` — changes here ripple to token_miser and kanon
- Backup/restore logic in `src/loadout/backup.py` and `src/loadout/restore.py`
- Secrets filtering in `src/loadout/secrets.py` — security-sensitive, test thoroughly
- `src/loadout/paths.py` resolves target root (`~/.claude/` default)

## Working Rules
- This is a library consumed by token_miser and kanon — breaking changes to public API (`apply_package`, `validate_package`) require coordinated updates
- `manifest.py` defines the package schema; changes need matching test updates in `test_manifest.py`
- Backup tests use temp dirs; never write to real `~/.claude/` in tests
- Keep CLI subcommands thin — delegate to module functions for testability
