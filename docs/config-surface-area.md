# The Full Claude Code Configuration Surface Area

## What loadout captures today

```
CLAUDE.md         →  ~/.claude/CLAUDE.md
settings.json     →  ~/.claude/settings.json
hooks/            →  ~/.claude/hooks/
bin/              →  ~/.claude/bin/
```

Four items. Hardcoded in `DEFAULT_CAPTURES`.

## What actually constitutes "a Claude Code environment"

Claude Code's config surface is split across **4 scope levels** (managed, user, project-shared, project-local) and **~15 distinct config types**. Here's the full inventory:

### Tier 1: Core behavior (changes how Claude thinks and acts)

| Config | User-level location | Project-level location | Format | Currently captured |
|--------|---------------------|----------------------|--------|-------------------|
| **CLAUDE.md** | `~/.claude/CLAUDE.md` | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Markdown | **Yes** (user only) |
| **Settings** | `~/.claude/settings.json` | `.claude/settings.json`, `.claude/settings.local.json` | JSON | **Yes** (user only) |
| **Rules** | `~/.claude/rules/*.md` | `.claude/rules/*.md` | Markdown w/ YAML frontmatter | **No** |
| **MCP servers** | `~/.claude.json` | `.mcp.json` in project root | JSON | **No** |
| **Hooks config** | In settings.json `hooks` key | In project settings.json | JSON + script files | **Partial** (scripts only, not the settings.json hooks config) |

### Tier 2: Capabilities (changes what Claude can do)

| Config | User-level location | Project-level location | Format | Currently captured |
|--------|---------------------|----------------------|--------|-------------------|
| **Skills** | `~/.claude/skills/<name>/SKILL.md` + supporting files | `.claude/skills/<name>/SKILL.md` | Markdown w/ YAML frontmatter + directory tree | **No** |
| **Agents** | `~/.claude/agents/<name>.md` | `.claude/agents/<name>.md` | Markdown w/ YAML frontmatter | **No** |
| **Commands** (legacy) | `~/.claude/commands/<name>.md` | `.claude/commands/<name>.md` | Markdown | **No** |
| **Plugins** | `~/.claude/plugins/<name>/` | (installed, not project-scoped) | Directory with `plugin.json` manifest | **No** |
| **Permissions** | In settings.json `permissions` key | In project settings.json | JSON | **Partial** (inside settings.json) |

### Tier 3: Environment (changes the runtime context)

| Config | Location | Format | Currently captured |
|--------|----------|--------|-------------------|
| **Hook scripts** | `~/.claude/hooks/`, `.claude/hooks/` | Shell scripts | **Yes** (user only) |
| **Bin scripts** | `~/.claude/bin/` | Executables | **Yes** |
| **Keybindings** | `~/.claude/keybindings.json` | JSON | **No** |
| **Status line** | `~/.claude/statusline.json` | JSON | **No** |
| **Auto memory** | `~/.claude/projects/<project>/memory/` | Markdown | **No** (and probably shouldn't be — see below) |
| **Environment vars** | In settings.json `env` key | In project settings.json | JSON | **Partial** (inside settings.json) |

### Tier 4: Managed/system (not loadout's job)

| Config | Location | Why not |
|--------|----------|---------|
| **Managed settings** | `/etc/claude-code/settings.json`, `/Library/Application Support/ClaudeCode/` | IT-deployed, not user-configurable |
| **Managed CLAUDE.md** | Same system dirs | Same |
| **Managed MCP** | `managed-mcp.json` in system dirs | Same |
| **OAuth tokens** | System keychain | Credentials, never bundle these |

### What loadout is missing vs what it should actually capture

**Must capture (Tier 1 — directly affects Claude's behavior):**
- `~/.claude/rules/` — rules are increasingly how teams encode coding standards. Missing these means a loadout bundle gives you the CLAUDE.md but not the conditional rules that fire based on file patterns.
- `~/.claude.json` (MCP config) — MCP servers are the biggest gap. A loadout without MCP config is like shipping a workstation image without the IDE plugins.
- Hook *configuration* (the `hooks` key in settings.json) — loadout captures hook *scripts* but not the settings.json configuration that tells Claude Code when to run them and what matchers to use.

**Should capture (Tier 2 — extends Claude's capabilities):**
- `~/.claude/skills/` — skills are custom slash commands with rich frontmatter (model overrides, tool restrictions, hooks). A power user's loadout without their skills is incomplete.
- `~/.claude/agents/` — custom agent definitions.
- `~/.claude/commands/` — legacy but still supported.
- Plugins — harder (see strategy section below).

**Nice to have (Tier 3 — environmental comfort):**
- `keybindings.json` — minor, but part of "how I work."
- `statusline.json` — minor.

**Should NOT capture:**
- Auto memory (`~/.claude/projects/*/memory/`) — this is per-project learned context, not configuration. It's generated, not authored. Including it in a loadout would leak project-specific knowledge into other projects.
- OAuth tokens, API keys, credentials — security risk. Warn and skip (loadout already does secret scanning).
- Managed/system configs — not user-controlled.

---

## The MCP Problem

MCP is the hardest config type for loadout to handle. Here's why and what to do about it.

### Why MCP is hard

**1. The file isn't where you'd expect.**
MCP config is NOT in `~/.claude/settings.json` or `~/.claude/mcp_servers.json`. It's in `~/.claude.json` — a dot-file in the HOME directory, outside `~/.claude/`. This breaks loadout's assumption that everything lives under `~/.claude/`.

**2. Scoping is complex.**
`~/.claude.json` contains both user-scoped and local-scoped (per-project) MCP servers in the same file. The structure nests project paths as keys. Capturing the whole file would leak project-specific server configs into a "portable" bundle.

**3. Project-level MCP is in `.mcp.json`, not in `~/.claude/`.**
Team-shared MCP servers live in `.mcp.json` at the project root — completely outside the `~/.claude/` tree. This is a project concern, not a user-profile concern. loadout currently only operates on `~/.claude/`.

**4. MCP servers have external dependencies.**
An MCP server config might reference:
- A binary that must be installed (`"command": "/usr/local/bin/mcp-server-github"`)
- Environment variables for auth (`"env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}`)
- OAuth configurations with callback ports
- Docker containers or HTTP endpoints

Capturing the *config* is easy. Making it *work* on another machine requires the server binary, the env vars, and the network access. loadout can't guarantee any of that.

**5. `claude mcp add` writes to `~/.claude.json` programmatically.**
Users don't hand-edit MCP config — they run `claude mcp add <name> --scope user`. This means the canonical config is in a file that Claude Code itself manages. loadout capturing and overwriting it could conflict with Claude Code's own state management.

### Strategy A: Extract-and-embed (recommended for MVP)

Capture the `mcpServers` block from `~/.claude.json` (user-scope only) and store it as `mcp/servers.json` in the bundle. On apply, merge it into the target's `~/.claude.json` rather than overwriting.

```
Bundle structure:
  my-loadout/
    mcp/
      servers.json    # extracted mcpServers block
    manifest.yaml     # target: { path: mcp/servers.json, dest: mcp, strategy: merge }
```

**Pros:** Clean bundle format. Doesn't leak project-scoped servers. Merge-on-apply is safer than overwrite.
**Cons:** Merge logic is non-trivial (what if the target already has a server with the same name?). Need to handle the fact that `~/.claude.json` is outside `~/.claude/`.

**Merge semantics:**
- Bundle server wins if names conflict (bundle is the desired state)
- Existing servers not in the bundle are preserved (don't destroy what's already there)
- `--replace` flag for destructive "only these servers" mode
- `restore` removes the servers that were added and restores any that were overwritten

**Capture logic:**
1. Read `~/.claude.json`
2. Extract `mcpServers` block (user-scope only — filter out project-scoped entries)
3. Strip secrets/tokens from `env` values — replace with `${VAR_NAME}` placeholders
4. Write to `mcp/servers.json` in bundle
5. Warn about required binaries that may not be installed elsewhere

### Strategy B: Reference-only (config as documentation)

Don't try to apply MCP configs. Instead, capture them as a reference document that tells the user what to install.

```
Bundle structure:
  my-loadout/
    mcp/
      servers.yaml    # human-readable, not machine-applied
```

```yaml
# MCP servers required by this loadout
# Run these commands to install:
servers:
  - name: github
    type: http
    install: "claude mcp add github --scope user"
    url: https://api.githubcopilot.com/mcp/
    notes: "Requires GitHub Copilot subscription"
  - name: filesystem
    type: stdio
    install: "claude mcp add filesystem -- npx @anthropic-ai/mcp-filesystem /path"
    notes: "Adjust path for your machine"
```

**Pros:** No merge complexity. No risk of breaking existing MCP setup. Portable across machines.
**Cons:** Not automated. Defeats the purpose of `loadout apply --yes` for token_miser.

### Strategy C: Replay commands (install script)

Store the `claude mcp add` commands that would recreate the MCP setup. On apply, replay them.

```
Bundle structure:
  my-loadout/
    mcp/
      install.sh
```

```bash
#!/bin/bash
claude mcp add github --scope user -- npx @anthropic-ai/mcp-server-github
claude mcp add filesystem --scope user -- npx @anthropic-ai/mcp-filesystem ~/allowed-dir
```

**Pros:** Uses Claude Code's own CLI to manage MCP. No merge logic. Handles OAuth flows correctly (Claude CLI prompts if needed).
**Cons:** Requires `claude` CLI available during apply. Slow (subprocess per server). Can't work non-interactively if OAuth is needed. token_miser can't use this (no Claude CLI in its temp environments — it's the thing being tested).

### Strategy D: Scope-aware file management

Treat `~/.claude.json` as a first-class config file that loadout manages alongside `~/.claude/`. Capture and apply it as a whole, but with scope filtering.

**Pros:** Simple implementation — just another file to copy.
**Cons:** Overwrites all MCP config including project-scoped servers. Dangerous if the user has project-specific MCP setups. `~/.claude.json` is outside `~/.claude/` which breaks the current target-directory model.

### Recommendation

**Phase 1: Strategy A (extract-and-embed) for user-scope MCP servers.** This is the minimum that unblocks token_miser. The merge logic is worth the complexity because it's the only approach that's both automated and safe.

**Phase 2: Strategy C (replay commands) as an optional layer** for full-environment bootstrap on new machines. Store the commands alongside the extracted config. Users can choose `loadout apply` (fast, merge-based) or `loadout bootstrap` (slow, uses Claude CLI, handles OAuth).

**Never do Strategy D.** Overwriting `~/.claude.json` wholesale is too dangerous.

---

## The Skills/Plugins Problem

### Skills

Skills are directory trees, not single files:

```
~/.claude/skills/
  my-skill/
    SKILL.md              # required, has YAML frontmatter
    reference.md          # optional supporting file
    examples.md           # optional
    scripts/
      helper.sh           # optional executables
```

The frontmatter in SKILL.md can contain:
- `allowed-tools` — security-relevant permission grants
- `model` — model override (e.g., force Opus for this skill)
- `hooks` — skill-scoped hooks that activate only when the skill runs
- `context: fork` — isolation mode
- `agent: Explore` — subagent type

**Strategy for skills:**

Skills are just directories. loadout already handles directory capture/apply (`hooks/`, `bin/`). Add `skills/` to the capture list and treat it like any other directory tree.

The wrinkle: skill frontmatter can reference external resources (model names, agent types) that may not exist in all Claude Code versions. loadout should capture skills verbatim and let Claude Code handle validation — don't try to parse SKILL.md frontmatter.

**Capture:**
```python
DEFAULT_CAPTURES = [
    ("CLAUDE.md", "CLAUDE.md"),
    ("settings.json", "settings.json"),
    ("hooks", "hooks"),
    ("bin", "bin"),
    ("skills", "skills"),       # new
    ("agents", "agents"),       # new
    ("commands", "commands"),    # new
    ("rules", "rules"),         # new
]
```

### Agents

Agents are single markdown files with YAML frontmatter. Same treatment as skills but simpler — just files, not directories.

### Commands (legacy)

Same as agents — single markdown files. Include for completeness since they're still supported.

### Plugins

Plugins are the hardest because they're **installed**, not just configured:
- They live in `~/.claude/plugins/<name>/` with a `plugin.json` manifest
- They can contain their own skills, agents, hooks, MCP configs, LSP configs
- They may come from a marketplace and have auto-update semantics
- They can have dependencies (npm packages, binaries)

**Strategy for plugins:**

**Don't try to capture and replay plugin installations.** Instead:

1. **Capture the list** of enabled plugins and their versions (from `settings.json` `enabledPlugins` field)
2. **Store plugin configs** (any plugin-specific settings files)
3. **On apply, warn** about plugins that need to be installed separately
4. **Future: `loadout bootstrap`** command that installs plugins from marketplace

This is analogous to how a `Gemfile.lock` records what's installed but `bundle install` does the actual installation. loadout records the desired plugin state; installing them is a separate concern.

---

## The Claude Code Versioning Problem

### Why it matters

Claude Code is evolving fast. Between its initial release and now:
- `.mcp.json` replaced whatever came before it
- Skills replaced commands (both still work)
- The `hooks` system went from simple scripts to a rich event system with matchers, JSON I/O, and multiple hook types (command, http, prompt, agent)
- Plugin system was introduced
- Rules directory was introduced
- Settings precedence/merge behavior changed
- MCP scope terminology changed ("global" → "user", "project" → "local")

A loadout bundle captured on Claude Code v2.1 might not work on v1.x or v3.x.

### What breaks across versions

| Config type | What can change | Impact |
|------------|----------------|--------|
| **settings.json** | New keys added, old keys deprecated, schema changes | Low — Claude Code ignores unknown keys |
| **hooks** | New hook events added, JSON schema changes, new hook types | Medium — old hooks still work, but new bundles using `agent` type hooks won't work on old versions |
| **MCP** | File location changes, scope model changes | High — if the file moves, loadout applies to the wrong place |
| **Skills** | New frontmatter fields, behavioral changes | Medium — unknown frontmatter is ignored |
| **Plugins** | Plugin API changes, marketplace changes | High — plugins are version-coupled to Claude Code |

### Strategy: Version declaration, not version enforcement

**Don't try to support all Claude Code versions.** Instead:

1. **Add `claude_code_min_version` to manifest.yaml** — the minimum Claude Code version the bundle was tested against. loadout checks `claude --version` on apply and warns (not errors) if the installed version is older.

2. **Add `claude_code_captured_version` to manifest.yaml** — the version that was running when capture happened. Pure metadata for debugging.

3. **Don't transform configs between versions.** If a user captures on v2.1 and tries to apply on v1.8, loadout should warn but not try to downgrade the config format. The config files are Claude Code's problem to parse.

4. **Version the loadout manifest itself** (already in roadmap as `schema_version`). This is separate from Claude Code versioning — it's about loadout's own format evolution.

5. **For token_miser specifically:** Pin Claude Code version in experiments. token_miser already controls the environment — it should install a specific Claude Code version in each experiment to avoid version-induced variance.

### What NOT to do

- Don't build a compatibility matrix of "settings key X was added in Claude Code vY"
- Don't try to migrate configs between Claude Code versions — that's Claude Code's job
- Don't refuse to apply based on version mismatch — warn and let the user decide
- Don't vendor Claude Code's schema — it will go stale immediately

---

## The Scope Problem: User vs Project

loadout currently operates on `~/.claude/` (user-level config). But Claude Code has a rich project-level config surface:

```
.claude/
  settings.json          # project settings (shared)
  settings.local.json    # project settings (local)
  CLAUDE.md              # project instructions
  rules/                 # project rules
  skills/                # project skills
  agents/                # project agents
  commands/              # project commands
  hooks/                 # project hook scripts
.mcp.json                # project MCP servers
```

### Should loadout handle project-level config?

**Not in the current model.** loadout bundles are "user profiles" — they represent how *you* work, not how *a project* is configured. Project config belongs in the project's git repo.

But there's a legitimate use case: **project templates.** "I want to bootstrap a new project with my standard `.claude/` setup." This is a different command:

```bash
# User profile (existing)
loadout apply my-profile          # → ~/.claude/

# Project template (new concept)
loadout init-project my-template  # → ./.claude/ + .mcp.json
```

**Recommendation:** Defer project-level config to a later phase. The current user-profile model is coherent and useful. Adding project scope doubles the surface area and introduces questions about git integration (should `loadout init-project` also add `.gitignore` entries?). Solve user-level first.

### For token_miser

token_miser creates isolated HOME dirs and uses `--target` to point at `<home>/.claude`. This is user-level by definition. Project-level config would need to go into the workspace directory, which is a separate concern from loadout. token_miser could handle this itself by checking for `.claude/` and `.mcp.json` in the loadout bundle and copying them to the workspace. But this is a token_miser feature, not a loadout feature.

---

## Updated Bundle Structure

Based on the full surface area analysis, here's what a complete loadout bundle should look like:

```
my-loadout/
  manifest.yaml
  CLAUDE.md
  settings.json
  rules/                    # NEW
    code-style.md
    testing.md
  hooks/
    post-tool-use.sh
  bin/
    token-log
  skills/                   # NEW
    my-skill/
      SKILL.md
      reference.md
  agents/                   # NEW
    code-reviewer.md
  commands/                 # NEW (legacy support)
    review.md
  mcp/                      # NEW
    servers.json             # extracted user-scope MCP servers
  keybindings.json          # NEW (optional)
  statusline.json           # NEW (optional)
```

And `manifest.yaml` grows:

```yaml
schema_version: 2
name: frugal-v2
version: 0.3.1
author: rubin-johnson
description: Token-optimized config with MCP servers and custom skills
claude_code_min_version: "2.1.0"
claude_code_captured_version: "2.1.74"

targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
  - path: settings.json
    dest: settings.json
  - path: rules/
    dest: rules/
  - path: hooks/
    dest: hooks/
  - path: bin/
    dest: bin/
  - path: skills/
    dest: skills/
  - path: agents/
    dest: agents/
  - path: commands/
    dest: commands/
  - path: mcp/servers.json
    dest: mcp
    strategy: merge          # NEW: merge semantics for MCP
  - path: keybindings.json
    dest: keybindings.json
  - path: statusline.json
    dest: statusline.json

plugins_required:            # NEW: declared but not installed by loadout
  - name: some-plugin
    version: ">=1.0.0"
    install: "claude plugin install some-plugin"
```

---

## The Launch-Flag Model: An Alternative to File Copying

### Discovery: Claude Code has CLI flags for composable config

A conversation among Claude Code power users (consultants, multi-client developers) revealed that Claude Code supports several CLI flags and environment variables that enable config-switching *without touching `~/.claude/` at all*:

| Flag / Env var | What it does | Since |
|---------------|-------------|-------|
| `CLAUDE_CONFIG_DIR` | Redirect all of `~/.claude/` to a different directory | Early versions |
| `--settings <path>` | Load settings from a specific JSON file instead of the default | Pre-2.1 |
| `--plugin-dir <path>` | Load plugins/skills/agents from a specific directory | Pre-2.1 |
| `--mcp-config <path>` | Load MCP server config from a specific file | v2.1.74+ (previously `--settings` merged MCP, now it doesn't) |

### Real-world usage patterns

**Pattern 1: Per-client config directories (Mark Lambert)**
Consultant with multiple clients, each requiring their own Claude account/config:
```bash
# Directory structure
~/.claude-clients/
  acme-corp/          # full ~/.claude equivalent for Acme
  globex/             # full ~/.claude equivalent for Globex

# Shell aliases
alias cc-acme='CLAUDE_CONFIG_DIR=~/.claude-clients/acme-corp claude'
alias cc-globex='CLAUDE_CONFIG_DIR=~/.claude-clients/globex claude'
```
Symlinks shared skills/CLAUDE.md from personal `~/.claude/` into client directories.

**Pattern 2: Composable launch flags (Mike Hanney)**
Multiple "teams" of agents/skills packaged as plugin directories, composed via flags:
```bash
export CLAUDE_DEV="$HOME/dev/claude-plugins"
export CLAUDE_LAUNCH_CONFIGS="$CLAUDE_DEV/launch-configs"

# Each alias composes a settings file + a plugin directory
alias csa="claude --plugin-dir \"$CLAUDE_DEV/claude-sa-team\" --settings \"$CLAUDE_LAUNCH_CONFIGS/csa.json\" --mcp-config \"$CLAUDE_LAUNCH_CONFIGS/csa.json\""
alias cpa="claude --plugin-dir \"$CLAUDE_DEV/claude-pa-team\" --settings \"$CLAUDE_LAUNCH_CONFIGS/personal.json\" --mcp-config \"$CLAUDE_LAUNCH_CONFIGS/personal.json\""
alias cdev="claude --settings \"$CLAUDE_LAUNCH_CONFIGS/developer.json\" --mcp-config \"$CLAUDE_LAUNCH_CONFIGS/developer.json\""
```

Plugin directory is a full agent team:
```
claude-pa-team/
  .claude-plugin/plugin.json
  CLAUDE.md
  agents/
    pa-orchestrator.md
    pa-financial-advisor.md
    pa-life-coach.md
    pa-strategist.md
    pa-travel-agent.md
    pa-wellness-coach.md
  commands/
    pa.md, coach.md, finance.md, goals.md, ...
  skills/
    clarification-protocol/
    decision-framework/
    financial-planning/
    habit-tracker/
    life-planning/
    travel-planning/
    weekly-planning/
    ...
```

### What this means for loadout

This reveals **two fundamentally different models** for config-switching:

**Model A: File-copy (current loadout model)**
- Copy files into `~/.claude/`
- Requires backup/restore
- Mutates shared state
- Only one loadout active at a time
- Works everywhere (including token_miser's temp HOME dirs)

**Model B: Launch-flag (zero-mutation model)**
- Bundle is a directory that stays where it is
- `loadout` generates a launch command or shell alias
- No backup needed — `~/.claude/` is untouched
- Multiple loadouts can coexist (different aliases)
- Switching is instant (use a different alias)
- **Doesn't work for token_miser** (needs actual files in a temp HOME)

### The right answer: support both

loadout should support both models because they serve different users:

**`loadout apply <bundle>`** (Model A — existing behavior)
- Copies files into target directory
- Creates backup, supports restore
- For: token_miser, CI/CD, container injection, anyone who needs actual files on disk

**`loadout launch <bundle>` or `loadout alias <bundle>`** (Model B — new)
- Generates a `claude` launch command with the right `--settings`, `--plugin-dir`, `--mcp-config` flags
- Or generates a shell alias for `.bashrc`/`.zshrc`
- Or sets `CLAUDE_CONFIG_DIR` to point at the bundle directory
- For: developers switching between client configs, team contexts, or personal vs work modes
- No backup, no restore, no mutation, no conflict

```bash
# Model A (existing)
$ loadout apply frugal-v2
Applied frugal-v2 to ~/.claude/. Backup at ~/.claude/.loadout-backups/2024-01-15T10:30:00/

# Model B (new) - generate alias
$ loadout alias frugal-v2
alias claude-frugal='claude --settings "/path/to/frugal-v2/settings.json" --plugin-dir "/path/to/frugal-v2" --mcp-config "/path/to/frugal-v2/mcp-config.json"'

# Model B - generate launch command
$ loadout launch frugal-v2
claude --settings "/path/to/frugal-v2/settings.json" --plugin-dir "/path/to/frugal-v2" --mcp-config "/path/to/frugal-v2/mcp-config.json"

# Model B - run directly
$ loadout run frugal-v2 -- --print "fix the bug in auth.py"
# executes: claude --settings ... --plugin-dir ... --mcp-config ... --print "fix the bug in auth.py"

# Model B - CLAUDE_CONFIG_DIR mode (full isolation)
$ loadout launch --config-dir frugal-v2
CLAUDE_CONFIG_DIR=/path/to/frugal-v2 claude

# Model B - add to shell profile
$ loadout alias frugal-v2 --install
# Appends alias to ~/.bashrc or ~/.zshrc
```

### Bundle format implications

For Model B to work, the bundle directory must be directly usable as a `--plugin-dir` or `CLAUDE_CONFIG_DIR` target. This means:

1. **Plugin-dir mode:** Bundle needs `.claude-plugin/plugin.json` to be a valid plugin directory. Skills go in `skills/`, agents in `agents/`, etc. Settings and MCP are passed via separate `--settings` and `--mcp-config` flags pointing at files in the bundle.

2. **Config-dir mode:** Bundle needs to look like `~/.claude/` — settings.json at root, skills/ dir, etc. This is already how loadout bundles are structured (minus the `manifest.yaml` which Claude Code ignores).

3. **Hybrid:** A bundle could be valid for *both* models. `manifest.yaml` is loadout metadata (ignored by Claude Code). The rest of the files are in the right places for either copy-into-`~/.claude/` or use-as-`CLAUDE_CONFIG_DIR`.

### Impact on MCP strategy

The launch-flag model **completely sidesteps the MCP merge problem** for Model B users:
- `--mcp-config <path>` points Claude Code at the bundle's MCP config file directly
- No need to merge into `~/.claude.json`
- No risk of overwriting existing MCP servers
- Bundle's MCP config is self-contained

This is a strong argument for implementing Model B early — it solves MCP without any of the merge complexity that Strategy A requires.

For Model A (token_miser), the merge strategy is still needed because token_miser needs actual files in a temp HOME directory.

### Impact on the roadmap

Model B (`loadout launch/alias/run`) should be **Phase 1b** — right after the foundation cleanup but before MCP merge logic. It's lower complexity (generate a string, don't mutate the filesystem) and higher value (solves the multi-client use case, sidesteps MCP merge for interactive users).

The full MCP merge strategy (Strategy A) gets pushed to Phase 2, needed only for token_miser and CI/CD. Most interactive users will use Model B instead.
