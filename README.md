> **Retired.** This project has been retired. Its functionality has been inlined into token_miser. Use kanon for package distribution.

---

# loadout

CLI tool to manage Claude Code configuration packages. Pack, apply, restore, version, and share a complete Claude Code setup as a single unit.

## Why

Claude Code configurations (CLAUDE.md, settings.json, hooks, bin scripts) are typically scattered and manually managed. Loadout lets you:

- **Switch profiles** across machines and containers
- **Share** validated configurations with teammates
- **Recover** from bad configs with automatic backups
- **Deploy** in CI/containers with zero home-directory assumptions

## Install

```bash
# From source (recommended)
git clone https://github.com/rubin-johnson/loadout.git
cd loadout
uv tool install .

# Or run directly without installing
uv run loadout --help
```

Requires Python 3.11+.

> **Note:** There is an unrelated package named `loadout` on PyPI. Do not run
> `pip install loadout` — it will install the wrong package. Install from this
> repository instead.

## Quick start

```bash
# Pack your current setup
loadout pack --source ~/.claude --output ./my-loadout

# Validate a package
loadout validate ./my-loadout

# Apply to a target
loadout apply ./my-loadout --target ~/.claude --yes

# Check what's active
loadout status

# Roll back
loadout restore --yes
```

## Commands

### validate

Check that a package is well-formed. Exits 0 on success, 1 with one error per line on failure. All errors are reported (not fail-fast).

```bash
loadout validate <package-dir>
```

### apply

Apply a package to a target directory (default: `~/.claude`). Creates a timestamped backup before writing anything.

```bash
loadout apply <package-dir> [--target <dir>] [--yes] [--dry-run]
```

| Flag | Purpose |
|------|---------|
| `--target` | Directory to apply into (default: `~/.claude`) |
| `--yes` | Skip confirmation prompts (required for CI/non-TTY) |
| `--dry-run` | Show what would change without writing anything |

### status

Show the currently applied loadout.

```bash
loadout status [--target <dir>]
```

### restore

Restore from a backup created by `apply`.

```bash
loadout restore [--target <dir>] [--backup <timestamp>] [--yes]
```

### pack

Snapshot a live config directory as a loadout package.

```bash
loadout pack [--source <dir>] [--output <dir>] [--yes]
```

| Flag | Purpose |
|------|---------|
| `--source` | Directory to pack from (default: `~/.claude`) |
| `--output` | Output package directory (default: `./my-loadout`) |
| `--yes` | Use defaults, skip prompts, overwrite existing output |

Warns about potential secrets in `hooks/` and `bin/`. Skips `.db` files.

## Package structure

```
my-loadout/
  manifest.yaml          # name, version, author, description, targets
  CLAUDE.md
  settings.json
  hooks/
  bin/
```

### manifest.yaml

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
  - path: hooks
    dest: hooks
```

## Non-interactive use

All destructive operations accept `--yes` to skip prompts:

```bash
loadout apply ./my-package --target /workspace/.claude --yes
```

Override the default target via environment variable:

```bash
LOADOUT_TARGET_ROOT=/workspace/.claude loadout apply ./my-loadout --yes
```

## Development

```bash
uv sync
uv run pytest tests/ -v
```

## Ecosystem

### kanon

A loadout package is the local form of what kanon distributes. After `kanon install`, packages appear in `.packages/` ready for `loadout apply`.

### token_miser

token_miser benchmarks packages to measure their impact on Claude Code token usage, quality, and cost. It can tune a package and publish the result back to kanon.
