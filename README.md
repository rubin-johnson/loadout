# loadout

CLI tool to manage Claude Code configuration bundles. Apply, restore, version, and share a complete set of Claude configuration as a single unit.

## Installation

```bash
uv sync
```

## Commands

### validate

Check a bundle is well-formed.

```bash
python -m loadout validate <bundle-dir>
```

### apply

Apply a bundle to a target directory (default: `~/.claude`).

```bash
python -m loadout apply <bundle-dir> [--target <dir>] [--yes] [--dry-run]
```

- `--target`: Directory to apply into (default: `~/.claude`)
- `--yes`: Skip confirmation prompts
- `--dry-run`: Show what would change without writing anything

### status

Show what loadout is currently applied.

```bash
python -m loadout status [--target <dir>]
```

### restore

Restore the previous configuration from a backup created by `apply`.

```bash
python -m loadout restore [--target <dir>] [--backup <timestamp>] [--yes]
```

### capture

Capture the current config directory as a loadout bundle.

```bash
python -m loadout capture --output <dir> [--source <dir>] [--yes]
```

- `--source`: Source directory to capture from (default: `~/.claude`)
- `--output`: Destination bundle directory (required)
- `--yes`: Overwrite if output already exists

## Bundle structure

```
my-loadout/
  manifest.yaml          # name, version, author, description, targets
  CLAUDE.md
  settings.json
  hooks/
  bin/
```

`manifest.yaml` example:

```yaml
name: frugal-v2
version: 0.3.1
author: rubin-johnson
description: Token-optimized configuration
targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
  - path: settings.json
    dest: settings.json
```

## Non-interactive use

All destructive operations accept `--yes` to skip prompts. Suitable for CI and containers:

```bash
loadout apply ./bundle --target /workspace/.claude --yes
```
