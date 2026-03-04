# loadout — Design Notes

**What it is**: A CLI tool to manage Claude Code configuration bundles. Apply, restore,
version, and share a complete set of Claude configuration as a single unit.

**Why it exists**: No tool currently does this. The closest thing is people manually
managing `~/.claude/` inside chezmoi/dotfiles repos — no tooling for profile switching,
sharing, or disaster recovery.

---

## What a "loadout" bundle contains

A loadout is a versioned directory with a defined structure:

```
my-loadout/
  manifest.yaml          # declares contents, version, author, description
  CLAUDE.md              # global instructions
  settings.json          # ~/.claude/settings.json
  hooks/                 # hook scripts (PostToolUse, PreToolUse, etc.)
    post-tool-use.sh
  mcp/                   # MCP server configs
    servers.json
  plugins/               # claude-mem config, skill bundles, etc.
    claude-mem.yaml
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
    dest: ~/.claude/CLAUDE.md
  - path: settings.json
    dest: ~/.claude/settings.json
  - path: hooks/
    dest: ~/.claude/hooks/
  - path: bin/
    dest: ~/.claude/bin/
```

---

## CLI surface

```bash
# Apply a loadout to the current environment
loadout apply <bundle-dir> [--target <dir>] [--yes] [--dry-run]

# Restore previous configuration (backup is created automatically on apply)
loadout restore [--backup <timestamp>]

# Show what is currently applied
loadout status

# Capture current ~/.claude config as a loadout bundle
loadout capture [--output ./my-loadout] [--yes]

# Validate a loadout bundle structure
loadout validate <bundle>
```

**Not in MVP**: `loadout diff`, `loadout list`, git URL support, registry syntax, multi-loadout composition.

---

## Critical requirement: programmatic execution in two contexts

**Global context** (applying to a workstation):
```bash
loadout apply ./frugal-v2
# Copies files to ~/.claude/, backs up existing config, symlinks scripts
```

**Target context** (inside a Docker container or CI environment):
```bash
# The container has no home dir or a clean one — loadout must accept an explicit
# target root so it doesn't assume ~/.claude/
loadout apply ./frugal-v2 --target /workspace/.claude
# or via env var:
LOADOUT_TARGET_ROOT=/workspace/.claude loadout apply ./frugal-v2
```

This is how token_miser uses loadout: it mounts a bundle into each experiment
container and runs `loadout apply --target /home/claude/.claude ./bundle`.

Non-interactive mode must work fully — no TTY prompts. All destructive operations
must be overridable via `--yes` / `--force` flags.

---

## Onramp: getting your current setup into a loadout

`loadout export` is the primary onramp. It:

1. Reads `~/.claude/CLAUDE.md`, `settings.json`, `hooks/`, `bin/`, and any MCP
   config it can discover
2. Copies them into a new bundle directory with a generated `manifest.yaml`
3. Prompts for a name, description, and initial version (`0.0.1`)
4. Optionally initializes a git repo in the bundle dir

Secondary onramp: `loadout init` creates an empty scaffold with commented-out
examples in each file, for users starting from scratch.

The export command should also warn about things it can't capture automatically:
- claude-mem database (separate tool, not a config file)
- Secrets or API keys referenced in hooks/scripts (scan and warn, never copy)
- MCP server credentials

---

## Distribution formats

A loadout bundle can be:
- A local directory (always works, no dependencies)
- A `.tar.gz` archive (for sharing/storage)
- A git repository URL (`loadout apply https://github.com/user/my-loadout`)
- Eventually: a registry entry (`loadout apply @rubin-johnson/frugal-v2`) — not MVP

---

## Implementation notes

- **Language**: Python (uv for packaging, pyenv for version management)
- **Target Python version**: 3.11+
- **No runtime dependencies** beyond stdlib for the core apply/restore/export commands;
  optional deps for git URL support
- **Backup strategy**: Before any apply, snapshot `~/.claude/` to
  `~/.claude/.loadout-backups/YYYY-MM-DD-HHMMSS/`; `restore` picks the most recent
  unless `--backup <timestamp>` is specified
- **Idempotent**: applying the same loadout twice is safe
- **Atomic**: use temp dir + rename pattern so partial applies don't corrupt state

---

## MVP scope

1. `loadout capture [--output] [--yes]` — snapshot current setup into a bundle
2. `loadout apply <bundle> [--target <dir>] [--yes] [--dry-run]` — apply a bundle
3. `loadout restore [--backup <timestamp>]` — undo the last apply
4. `loadout validate <bundle>` — check a bundle is well-formed (also called internally by apply)
5. `loadout status` — show what is currently applied
6. `manifest.yaml` schema finalized

Not in MVP:
- Registry / `@user/name` syntax
- Git URL support (local dirs only)
- `loadout diff`, `loadout list`
- Multi-loadout composition (load/unload individual loadouts simultaneously)
- GUI / TUI

## State file

`~/.claude/.loadout-state.json` tracks what is currently applied:
```json
{
  "active": "frugal-v2",
  "applied_at": "2026-03-04T18:00:00Z",
  "bundle_path": "/path/to/frugal-v2",
  "manifest_version": "0.3.1",
  "backup": "2026-03-04-180000"
}
```
`restore` reads this to find the right backup. `status` reads it to display current state.
Data model is designed to support multi-loadout later (active becomes a list) without schema breakage.

## Testing strategy

- All tests operate on temp dirs — real `~/.claude/` is never touched
- Fixtures: a populated "organic setup" temp dir that mimics a real messy config
- `capture` tests: verify bundle structure/contents against fixture
- `apply` tests: apply a known bundle to a clean temp dir, assert files landed correctly
- Roundtrip integration test: `capture` → `apply` → assert file tree matches original
- Smoke test: subprocess invocation of actual CLI binary against a temp dir
- `--dry-run` on apply: prints what would change, touches nothing — testing surface and safety feature

## Warnings and safety

- `apply` always backs up before touching anything
- `capture` warns about things it cannot capture: claude-mem database, secrets/API keys in hooks (scan and warn, never copy), MCP credentials
- `--dry-run` available on apply for pre-flight review
- All destructive operations require `--yes` in interactive mode or fail with a clear message
- Non-interactive mode (`--yes`) must work fully — no TTY required (CI/container use)

---

## Relationship to token_miser

token_miser depends on loadout. In experiments:

```python
# token_miser experiment runner (pseudocode)
for config in [control_loadout, best_loadout, candidate_loadout]:
    container = spawn_claude_container()
    container.run(f"loadout apply --target /home/claude/.claude --yes {config.bundle_path}")
    result = container.run_task(experiment.task)
    results.append(evaluate(result, experiment.rubric))
```

loadout has no dependency on token_miser.
