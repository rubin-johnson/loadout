# loadout

CLI tool to manage Claude Code configuration bundles. Apply, restore, version, and share
a complete set of Claude configuration as a single unit.

## Install

```bash
uv pip install -e .
```

## Commands

```bash
# Apply a loadout bundle to the current environment
loadout apply <bundle-dir> [--target <dir>] [--yes] [--dry-run]

# Restore previous configuration from a backup
loadout restore [--backup <timestamp>]

# Show what loadout is currently applied
loadout status [--target <dir>]

# Capture current ~/.claude config as a loadout bundle
loadout capture [--output ./my-loadout] [--yes]

# Validate a loadout bundle structure
loadout validate <bundle>
```

Set `LOADOUT_TARGET_ROOT` to override the default target (`~/.claude`):

```bash
LOADOUT_TARGET_ROOT=/workspace/.claude loadout apply ./my-loadout --yes
```

## Development

```bash
uv venv
uv pip install -e .
uv pip install pytest
uv run pytest tests/ -v
```
