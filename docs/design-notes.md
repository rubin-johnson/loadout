# loadout — Design Notes

**What it is**: A CLI tool to manage Claude Code configuration packages. Apply, restore,
version, and share a complete Claude Code setup as a single unit.

**Why it exists**: No tool currently does this. The closest thing is people manually
managing `~/.claude/` inside chezmoi/dotfiles repos — no tooling for profile switching,
sharing, or disaster recovery.

---

## What a loadout package contains

A loadout is a versioned directory with a defined structure:

```
my-loadout/
  manifest.yaml          # declares contents, version, author, description
  CLAUDE.md              # global instructions
  settings.json          # ~/.claude/settings.json
  hooks/                 # hook scripts (PostToolUse, PreToolUse, etc.)
    post-tool-use.sh
  bin/                   # scripts that go in PATH (~/.claude/bin/)
    token-log
    token-report
```

`manifest.yaml` example:
```yaml
name: frugal-v2
version: 0.3.1
author: rubin-johnson
description: Token-optimized configuration with claude-mem and haiku-first model selection
targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
  - path: settings.json
    dest: settings.json
  - path: hooks/
    dest: hooks/
  - path: bin/
    dest: bin/
```

---

## CLI surface

```bash
# Pack current ~/.claude config as a loadout package
loadout pack [--source <dir>] [--output <dir>] [--yes]

# Validate a package structure
loadout validate <package-dir>

# Apply a package to the current environment
loadout apply <package-dir> [--target <dir>] [--yes] [--dry-run]

# Show what is currently applied
loadout status [--target <dir>]

# Restore previous configuration (backup is created automatically on apply)
loadout restore [--target <dir>] [--backup <timestamp>] [--yes]
```

**Not in MVP**: `loadout diff`, `loadout list`, git URL support, registry syntax, multi-loadout composition.

---

## Critical requirement: programmatic execution in two contexts

**Global context** (applying to a workstation):
```bash
loadout apply ./frugal-v2
# Copies files to ~/.claude/, backs up existing config
```

**Target context** (inside a Docker container or CI environment):
```bash
# The container has no home dir or a clean one — loadout must accept an explicit
# target root so it doesn't assume ~/.claude/
loadout apply ./frugal-v2 --target /workspace/.claude
# or via env var:
LOADOUT_TARGET_ROOT=/workspace/.claude loadout apply ./frugal-v2
```

This is how token_miser uses loadout: it mounts a package into each experiment
container and runs `loadout apply --target /home/claude/.claude ./my-package`.

Non-interactive mode must work fully — no TTY prompts. All destructive operations
must be overridable via `--yes` flags.

---

## Onramp: getting your current setup into a loadout

`loadout pack` is the primary onramp. It:

1. Reads `~/.claude/CLAUDE.md`, `settings.json`, `hooks/`, `bin/`
2. Copies them into a new package directory with a generated `manifest.yaml`
3. Skips database files (`.db`)
4. Scans `hooks/` and `bin/` for potential secrets and warns (never copies secrets)

---

## Distribution formats

A loadout package can be:
- A local directory (always works, no dependencies)
- Eventually: a `.tar.gz` archive, git URL, or registry entry — not MVP

---

## Implementation notes

- **Language**: Python (uv for packaging, pyenv for version management)
- **Target Python version**: 3.11+
- **Runtime dependency**: PyYAML only; everything else is stdlib
- **Backup strategy**: Before any apply, snapshot existing files to
  `<target>/.loadout-backups/YYYY-MM-DD-HHMMSS/`; `restore` picks the most recent
  unless `--backup <timestamp>` is specified
- **Atomic**: use temp dir + move pattern so partial applies don't corrupt state
- **Path safety**: dest paths are validated against the target root to prevent traversal

---

## MVP scope

1. `loadout pack [--source] [--output] [--yes]` — snapshot current setup into a package
2. `loadout validate <package>` — check a package is well-formed (also called internally by apply)
3. `loadout apply <package> [--target <dir>] [--yes] [--dry-run]` — apply a package
4. `loadout restore [--backup <timestamp>] [--yes]` — undo the last apply
5. `loadout status` — show what is currently applied
6. `manifest.yaml` schema finalized

Not in MVP:
- Registry / `@user/name` syntax
- Git URL support (local dirs only)
- `loadout diff`, `loadout list`
- Multi-loadout composition (load/unload individual loadouts simultaneously)
- GUI / TUI

## State file

`<target>/.loadout-state.json` tracks what is currently applied:
```json
{
  "active": "frugal-v2",
  "applied_at": "2026-03-04T18:00:00Z",
  "package_path": "/path/to/frugal-v2",
  "manifest_version": "0.3.1",
  "backup": "2026-03-04-180000",
  "placed_paths": ["/home/user/.claude/CLAUDE.md"]
}
```
`restore` reads this to find the right backup and clean up placed files.
`status` reads it to display current state.
Data model is designed to support multi-loadout later (active becomes a list) without schema breakage.

## Testing strategy

- All tests operate on temp dirs — real `~/.claude/` is never touched
- Unit tests: individual modules (apply, manifest, validate, restore, backup, state, secrets, status)
- CLI integration tests: subprocess invocation of the actual CLI (`test_apply_cmd.py`, `test_pack.py`)
- Roundtrip integration tests (`test_bt.py`): pack → apply → restore → verify file tree matches original
- Atomicity tests: verify partial failures leave existing files untouched
- `--dry-run` on apply: prints what would change, touches nothing

## Warnings and safety

- `apply` always backs up before touching anything
- `pack` warns about secrets in hooks/bin and skips database files
- `--dry-run` available on apply for pre-flight review
- All destructive operations require `--yes` or fail with a clear message
- Non-interactive mode (`--yes`) works fully — no TTY required (CI/container use)
- Dest paths are validated to stay within the target root (no path traversal)

---

## Relationship to token_miser

token_miser depends on loadout. In experiments:

```python
# token_miser experiment runner (pseudocode)
for config in [control_loadout, best_loadout, candidate_loadout]:
    container = spawn_claude_container()
    container.run(f"loadout apply --target /home/claude/.claude --yes {config.package_path}")
    result = container.run_task(experiment.task)
    results.append(evaluate(result, experiment.rubric))
```

loadout has no dependency on token_miser.
