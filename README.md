# loadout

CLI tool to manage Claude Code configuration bundles. Capture, apply, restore, version, and share a complete Claude Code setup as a single unit.

## Why

Claude Code configurations (CLAUDE.md, settings.json, hooks, bin scripts) are typically scattered and manually managed. Loadout lets you:

- **Switch profiles** across machines and containers
- **Share** validated configurations with teammates
- **Recover** from bad configs with automatic backups
- **Deploy** in CI/containers with zero home-directory assumptions

## Install

```bash
# From source
uv tool install .

# Or run directly
uv run loadout --help
```

Requires Python 3.11+.

## Quick start

```bash
# Capture your current setup
loadout capture --source ~/.claude --output ./my-loadout

# Validate a bundle
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

Check that a bundle is well-formed. Exits 0 on success, 1 with one error per line on failure. All errors are reported (not fail-fast).

```bash
loadout validate <bundle-dir>
```

### apply

Apply a bundle to a target directory (default: `~/.claude`). Creates a timestamped backup before writing anything.

```bash
loadout apply <bundle-dir> [--target <dir>] [--yes] [--dry-run]
```

| Flag | Purpose |
|------|---------|
| `--target` | Directory to apply into (default: `~/.claude`) |
| `--yes` | Skip confirmation prompts (required for CI/non-TTY) |
| `--dry-run` | Show what would change without writing anything |

Applying the same bundle (name + version) twice is idempotent.

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

### capture

Snapshot a live config directory as a loadout bundle.

```bash
loadout capture [--source <dir>] [--output <dir>] [--yes]
```

| Flag | Purpose |
|------|---------|
| `--source` | Directory to capture from (default: `~/.claude`) |
| `--output` | Output bundle directory (default: `./my-loadout`) |
| `--yes` | Use defaults, skip prompts, overwrite existing output |

Warns about potential secrets in `hooks/` and `bin/`. Skips `.db` files.

## Bundle structure

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
loadout apply ./bundle --target /workspace/.claude --yes
```

Override the default target via environment variable:

```bash
LOADOUT_TARGET_ROOT=/workspace/.claude loadout apply ./my-loadout --yes
```

## Relationship with kanon

[Kanon](https://github.com/caylent-solutions/kanon) is a DevOps package manager that distributes versioned automation packages across teams via git-repo manifests. Loadout and kanon are **complementary**:

- **Kanon** distributes versioned packages (linting rules, security configs, build conventions) across an organization
- **Loadout** manages the active Claude Code configuration on a single machine

A kanon source could distribute loadout bundles as packages. After `kanon install` syncs bundles to `.packages/`, `loadout apply` activates one on the local machine. Kanon handles distribution and versioning; loadout handles the local apply/backup/restore lifecycle.

## Development

```bash
uv sync
uv run pytest tests/ -v
```
