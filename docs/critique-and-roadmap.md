# loadout — Critique & Roadmap

## Preamble: Should loadout and token_miser Be One Tool?

No. They're a clear separation of concerns:

**loadout** = config management. It answers: "What Claude Code setup do I want active right now?" It packages, applies, restores, and distributes configuration bundles. It's a noun — the thing you equip.

**token_miser** = experiment runner. It answers: "Which configuration makes Claude most efficient for this task?" It orchestrates isolated environments, invokes Claude, evaluates quality, stores results. It's a verb — the thing you measure.

The relationship is one-directional: token_miser calls `loadout apply` as a subprocess to inject configs into experiment environments. loadout knows nothing about token_miser. This is correct and should stay this way.

The temptation to merge them comes from the fact that they share a user (you) and a domain (Claude Code optimization). But merging would mean:
- loadout gains SQLite, the Anthropic SDK, and an experiment orchestrator — bloating a simple config tool
- token_miser embeds config management logic — tying experiment infrastructure to one config format
- Testing becomes entangled — loadout's pure filesystem tests would need to coexist with token_miser's subprocess/API tests

The correct integration path is making loadout a better subprocess citizen for token_miser (and any other consumer), not absorbing token_miser into it. The roadmap below reflects this.

---

## Part 1: Critique

### What loadout is

A CLI tool that packages Claude Code configuration (`~/.claude/`) into versioned, portable bundles — apply, restore, capture, validate. Designed for two audiences: developers switching between Claude Code "profiles" and token_miser injecting controlled configs into experiment environments.

### Similar tools that already exist

| Tool | What it does | How it compares |
|------|-------------|-----------------|
| **chezmoi** | Dotfile manager with templates, secrets, multi-machine support | General-purpose. Templates handle machine differences. No concept of "bundles" or profile-switching — you have one desired state, not N swappable profiles. |
| **GNU Stow** | Symlink farm manager | Simplest approach. Just symlinks dirs into `~`. No versioning, no rollback, no secrets awareness. |
| **Nix Home Manager** | Declarative home-directory configuration | Powerful but requires the entire Nix ecosystem. Overkill for "I want to swap my CLAUDE.md." |
| **yadm** | Git-based dotfile manager with encrypt/template support | Closer to chezmoi than to loadout. Single desired state, not swappable bundles. |
| **rcm** | Thoughtbot's dotfile management suite | Symlink-based, no rollback, no bundling. |
| **dotdrop** | Dotfile manager with profiles and Jinja templates | Closest analog — has explicit profiles, templating, comparison. But it's a general dotfile tool, not purpose-built for Claude Code. |

**The gap loadout fills**: None of these tools are designed for swapping entire configuration profiles atomically with rollback. They manage a single desired state that evolves over time. loadout's model — "I have 5 different Claude configs and I want to slot one in" — is genuinely novel for this domain. The container-injection use case (token_miser) has no analog at all in the dotfile world.

### What it's doing well

1. **Clear mental model.** Bundle = directory with manifest. Apply/restore/capture is intuitive.
2. **Non-interactive mode.** `--yes` and `LOADOUT_TARGET_ROOT` make CI/container use work without hacks.
3. **Backup-on-apply.** Every apply snapshots the previous state. This is the right default.
4. **Atomic staging.** Files are staged to a temp dir before being moved into place, preventing half-applied states for files (directories are still non-atomic, but that's an OS limitation).
5. **Test coverage.** ~350 tests across unit, integration, behavioral, and smoke levels for a small tool — well above average.
6. **Minimal dependencies.** stdlib + PyYAML. Easy to install anywhere.

### What it's lacking

#### 1. No MCP server configuration support
The design notes list `mcp/` and `plugins/` as bundle contents, but capture only knows about `CLAUDE.md`, `settings.json`, `hooks/`, and `bin/`. MCP server configs (`~/.claude/mcp_servers.json` or wherever Claude Code stores them) are invisible to capture and untested in apply. This is a significant gap — MCP servers are increasingly central to Claude Code workflows.

#### 2. No `loadout init` (scaffold from scratch)
The design notes describe an `init` command that creates an empty bundle with commented examples. Not implemented. Users who want to build a config from scratch (rather than capturing an existing one) have no guided path.

#### 3. No `loadout diff`
You can't compare two bundles, or compare a bundle against the current state. This makes it hard to understand what `apply` will change before running it. `--dry-run` shows file paths but not content differences.

#### 4. No `loadout list`
No way to enumerate available bundles or see history of applied bundles. You have `status` for the current one and that's it.

#### 5. Hardcoded capture paths
`DEFAULT_CAPTURES` in `capture.py` is a hardcoded list of 4 entries. If Claude Code adds new config locations (and it will — it's evolving rapidly), loadout silently ignores them. There's no way for users to add custom capture paths.

#### 6. No archive/distribution support
Design notes describe `.tar.gz` and git URL support. Neither is implemented. Bundles can only be local directories. This limits shareability — you can't `loadout apply https://github.com/user/my-config` or even `loadout apply ./bundle.tar.gz`.

#### 7. No manifest schema versioning
There's no `schema_version` field in `manifest.yaml`. When the manifest format changes (and it will), there's no way to distinguish v1 manifests from v2 manifests. This will force ugly heuristics later.

#### 8. Backup accumulation
Backups are created on every apply but never cleaned up. Over time `~/.claude/.loadout-backups/` will grow without bound. No `--keep N` option, no automatic pruning.

#### 9. Silently skips absolute dest paths
If a manifest has `dest: /etc/something`, `_resolve_dest` returns `None` and the file is silently ignored. No warning, no error. This will confuse users.

#### 10. No integrity verification
No checksums, no signatures, no way to verify a bundle hasn't been tampered with. For a tool designed to inject configuration into CI environments, this is a security concern.

### What it's doing that it shouldn't

#### 1. `backup.py` is dead code
The `backup.py` module exists, is imported in tests, but is completely unused by the actual apply/restore flow. Backup logic is duplicated directly in `apply.py` and `restore.py`. This is confusing — it looks like an abstraction that was abandoned mid-implementation.

#### 2. `REQUIRED_FIELDS` backward-compat export
`manifest.py` exports both `_REQUIRED_FIELDS` (private) and `REQUIRED_FIELDS` (public, with a `# Keep for backward compat` comment). This is an MVP with no external consumers — there's nothing to be backward-compatible with. Delete it.

#### 3. Over-engineering the atomic apply for the current feature set
The temp-dir staging strategy in `atomic_apply()` protects against partial file writes, but directory replacement still does `rmtree + move` which isn't atomic. The protection is real for files but illusory for directories. The code comment acknowledges this but the function name `atomic_apply` oversells the guarantee.

#### 4. Capture creates a placeholder CLAUDE.md when empty
If no capturable files are found, `capture_bundle()` creates a dummy `# empty loadout\n` CLAUDE.md. This means `capture` never fails — it always produces a "valid" bundle even when the source directory is empty or doesn't contain Claude Code config. It should warn or error instead of silently producing a useless bundle.

---

## Part 2: Relationship to token_miser

### How token_miser actually works (from the source)

token_miser is a Go CLI (`github.com/rubin-johnson/token_miser`) that A/B tests Claude Code configurations. The full pipeline:

1. **Task definition** (`tasks/synth-001.yaml`): declares a repo, starting commit, prompt, success criteria, and quality rubric
2. **Arm parsing** (`internal/arm/`): "vanilla" = no config; any directory path = a loadout bundle
3. **Environment setup** (`internal/environment/`): creates temp HOME dir, `git clone --shared` the target repo, `git checkout` the starting commit, then calls `loadout apply --target <home>/.claude --yes <bundle>` for non-vanilla arms
4. **Claude execution** (`internal/executor/`): runs `claude --print --dangerously-skip-permissions --output-format json` with `HOME` overridden and `CLAUDECODE` stripped from env
5. **Success checking** (`internal/checker/`): runs file_exists, command_exits_zero, output_contains checks against the workspace
6. **Quality scoring** (`internal/evaluator/`): LLM-as-judge via Anthropic SDK (Haiku), per-rubric-dimension 0.0-1.0 scores
7. **Storage** (`internal/db/`): SQLite at `~/.token_miser/results.db`
8. **Reporting** (`internal/report/`): side-by-side comparison of arms by token usage, cost, criteria pass rate

### What loadout must do better for token_miser

These are not speculative — they come directly from reading token_miser's source code.

| Need | Evidence in token_miser source | Loadout gap |
|------|-------------------------------|-------------|
| **`--no-backup`** | `environment.go:56-62` — applies to a temp HOME dir that gets `os.RemoveAll`'d immediately. Backups are pure waste. | No flag exists. Every apply creates a backup even in ephemeral contexts. |
| **`--json` output** | `cli.go:143-144` — quality scoring errors silently dropped (`qualityScores, _ := ...`). token_miser can't parse loadout's human-readable apply output either; it just ignores it. | No machine-readable output mode. Programmatic consumers must either ignore output or fragile-parse it. |
| **Exit code contract** | `environment.go:58` — loadout failure is wrapped into `fmt.Errorf("loadout apply: %w", err)` and aborts the arm. token_miser trusts exit codes. | Undocumented which exit codes mean what. |
| **Fast apply for temp dirs** | `environment.go:57` — creates `<home>/.claude` then immediately applies into it. The `--target` dir is always clean. | loadout still runs full backup + atomic staging for clean targets. Could skip all safety for `--target` on empty dirs. |
| **Bundle identity/hash** | `db.go:19` — `loadout_name TEXT` stores `arm.LoadoutPath`. Two bundles with the same name but different content are indistinguishable in results. | No content hash. `manifest.yaml` has name + version but no integrity check. |
| **MCP config** | `environment.go` only calls `loadout apply` — whatever loadout manages is what lands in the experiment. MCP-heavy configs can't be tested because loadout doesn't capture/apply them. | No MCP support. |
| **Metadata attachment** | `db.go` Run struct has `loadout_name` but no experiment-level metadata. token_miser stores its own metadata but can't round-trip loadout state. | State file has no metadata extension point. |

### What token_miser itself needs to fix (not loadout's problem, but context)

For completeness — these are token_miser issues that don't change the loadout roadmap but explain the broader picture:

- **No `--repeat N`**: Single run per arm, can't establish statistical significance
- **No execution timeout**: `context.Background()` means Claude can hang forever
- **Silent error swallowing**: `qualityScores, _ := evaluator.ScoreQuality(...)` — if the Anthropic API fails, quality data is silently lost
- **Hardcoded absolute paths in task YAML**: `repo: /home/rujohnson/code/personal/loadout` — not portable
- **Alphabetical file selection for judge**: `readWorkspaceFiles` reads the first 5 files by walk order, not the most relevant ones
- **No stderr capture**: `cmd.Output()` only gets stdout; Claude errors are lost
- **Report doesn't show quality scores**: stored in DB but never surfaced in `compare` output
- **No delta calculation**: reports show each arm's numbers but not the diff between them
- **Sequential arm execution**: no parallelism
- **No schema migrations**: adding any DB column requires recreating the database
- **Single-shot mode doesn't test what matters**: `claude --print` is non-agentic; the real value (how CLAUDE.md affects exploration strategy) only appears in multi-turn mode, which is unimplemented

---

## Part 3: Roadmap

See also: [docs/config-surface-area.md](config-surface-area.md) for the full analysis of Claude Code's configuration surface, MCP strategies, skills/plugins handling, and versioning considerations that inform this roadmap.

### Phase 1: Solidify the foundation

**Goal:** Fix the gaps that make the MVP unreliable, make loadout a proper subprocess citizen, and expand capture to cover the real config surface.

**Cleanup & correctness:**
- [ ] **Add manifest `schema_version` field** — default `1`, validate on load, error on unknown versions.
- [ ] **Delete `backup.py`** — move any needed logic into apply/restore, remove dead code.
- [ ] **Remove `REQUIRED_FIELDS` compat export** — no consumers to break.
- [ ] **Warn on silently-skipped absolute dest paths** — print to stderr instead of swallowing.
- [ ] **Error on empty capture** — don't create placeholder bundles.

**Subprocess citizenship (for token_miser):**
- [ ] **Add `--json` output mode** — for `status`, `validate`, and `apply`. Structured output with applied files, skipped files, errors.
- [ ] **Add `--no-backup` flag to `apply`** — for container/ephemeral contexts where backups are waste.
- [ ] **Document exit code contract** — 0 = success, 1 = validation error, 2 = apply error, etc.
- [ ] **Add backup pruning** — `--keep N` on apply, or `loadout prune-backups --keep 3`.

**Expand capture surface (the big one):**
- [ ] **Make DEFAULT_CAPTURES configurable** — stop hardcoding. Allow manifest.yaml to declare additional capture paths.
- [ ] **Capture `rules/`** — `~/.claude/rules/*.md` with YAML frontmatter. These are increasingly how teams encode conditional coding standards. Treat as a directory like `hooks/`.
- [ ] **Capture `skills/`** — `~/.claude/skills/<name>/` directory trees. Each skill is a SKILL.md with optional supporting files and scripts. Capture verbatim — don't parse frontmatter.
- [ ] **Capture `agents/`** — `~/.claude/agents/<name>.md` files. Simple markdown with YAML frontmatter.
- [ ] **Capture `commands/`** — `~/.claude/commands/<name>.md` (legacy, still supported). Simple markdown files.
- [ ] **Capture `keybindings.json`** — `~/.claude/keybindings.json`. Optional, minor, but part of a complete environment.
- [ ] **Capture `statusline.json`** — `~/.claude/statusline.json`. Optional.
- [ ] **MCP server capture/apply (Strategy A: extract-and-embed)** — extract `mcpServers` from `~/.claude.json` (user-scope only), strip secrets, store as `mcp/servers.json` in bundle. On apply, merge into target's `~/.claude.json` rather than overwrite. See [config-surface-area.md](config-surface-area.md) for full strategy analysis.

**Claude Code versioning:**
- [ ] **Add `claude_code_min_version` to manifest.yaml** — minimum Claude Code version the bundle was tested against. Check `claude --version` on apply and warn (not error) if too old.
- [ ] **Add `claude_code_captured_version` to manifest.yaml** — version running during capture. Pure metadata for debugging and reproducibility.

### Phase 2: Distribution & sharing

**Goal:** Bundles can be shared without manual file copying.

- [ ] **`loadout apply ./bundle.tar.gz`** — support archived bundles (extract to temp, validate, apply).
- [ ] **`loadout pack`** — create a `.tar.gz` from a bundle directory.
- [ ] **`loadout apply <git-url>`** — clone to temp, validate, apply. Support branch/tag/ref syntax.
- [ ] **`loadout init`** — scaffold an empty bundle with commented examples for all config types (CLAUDE.md, settings, rules, skills, MCP, hooks, agents).
- [ ] **Bundle checksums** — SHA-256 content hash in manifest or state file. Verify on apply. Supports token_miser's need to distinguish bundles by content.

### Phase 3: Comparison, composition & plugins

**Goal:** Users can understand differences, compose configurations, and declare plugin requirements.

- [ ] **`loadout diff <bundleA> <bundleB>`** — content-level diff of two bundles.
- [ ] **`loadout diff --current <bundle>`** — compare bundle against applied state.
- [ ] **`loadout list`** — list known/recently-applied bundles from state history.
- [ ] **Multi-loadout composition** — apply base + overlay bundles with defined merge semantics. State tracks a stack. Merge rules: files overwrite (last wins), MCP servers merge by name, settings.json deep-merges, skills/agents/rules directories union. This unlocks testing config combinations in token_miser.
- [ ] **Conflict detection** — warn when two bundles touch the same file or define the same MCP server/skill name.
- [ ] **Plugin declarations** — `plugins_required` field in manifest.yaml lists plugins by name and version constraint. On apply, warn about plugins that aren't installed. Don't try to install them — that's `claude plugin install`'s job.
- [ ] **`loadout bootstrap`** — optional command that runs `claude mcp add` for each MCP server and `claude plugin install` for each plugin. Slow, interactive, for new-machine setup (not token_miser).

### Phase 4: token_miser integration hooks

**Goal:** loadout becomes a first-class primitive for experiment infrastructure.

- [ ] **`loadout hash <bundle>`** — print content-addressable hash of a bundle for cache keys, experiment dedup, and result correlation.
- [ ] **Experiment metadata in state** — `loadout apply --meta '{"run_id": "...", "variant": "..."}'` stores arbitrary metadata in state file.
- [ ] **`loadout apply --read-only`** — symlink or bind-mount mode for faster container injection (no copy).
- [ ] **Event hooks** — `pre-apply`, `post-apply`, `pre-restore` hooks for experiment orchestrators.
- [ ] **Bulk validation** — `loadout validate dir-of-bundles/` for validating a full experiment suite.
- [ ] **`loadout apply --skip-safety`** — combined flag for `--no-backup --yes` that also skips idempotency checks. Optimized for token_miser's fresh temp dir fast path.

### Phase 5: Registry & ecosystem

**Goal:** Bundles are discoverable and installable from a shared registry.

- [ ] **`loadout apply @user/bundle-name`** — registry syntax with GitHub-backed resolution.
- [ ] **`loadout publish`** — push a bundle to the registry.
- [ ] **`loadout search`** — discover community bundles.
- [ ] **Dependency declarations** — bundles can declare they require specific Claude Code versions, MCP servers, or plugins.
- [ ] **CI/CD integration** — GitHub Action and Docker image for loadout in pipelines.

---

## Summary

loadout and token_miser are correctly separate tools. loadout manages what you deploy; token_miser measures whether it was worth deploying. The integration point is `loadout apply --target ... --yes` called from `environment.go`.

The loadout MVP captures 4 of ~15 config types that constitute a Claude Code environment. The biggest gaps are MCP servers (`~/.claude.json` — outside the `~/.claude/` tree, requires merge-on-apply semantics), skills/agents/rules (directory trees that are straightforward to capture but weren't in the original hardcoded list), and plugins (can't be captured/replayed — need a declaration + bootstrap model instead). Claude Code versioning is a real concern but the right strategy is declaration-and-warn, not transformation — loadout should record which version a bundle was captured on and warn on version mismatch, but never try to migrate config formats between versions.

Phase 1 is the largest phase because it combines the original cleanup/subprocess-citizenship work with the expanded capture surface. MCP is the hardest part — the extract-and-merge strategy (Strategy A in the config surface area doc) is recommended for Phase 1, with the replay-commands approach (Strategy C / `loadout bootstrap`) deferred to Phase 3 for new-machine setup scenarios.

See [docs/config-surface-area.md](config-surface-area.md) for the complete analysis.
