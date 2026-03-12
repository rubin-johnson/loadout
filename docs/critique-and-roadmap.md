# loadout — Critique & Roadmap

## Part 1: Critique

### What loadout is

A CLI tool that packages Claude Code configuration (`~/.claude/`) into versioned, portable bundles — apply, restore, capture, validate. Designed for two audiences: developers switching between Claude Code "profiles" and token_miser injecting controlled configs into experiment containers.

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

Based on the design notes, token_miser is an experiment runner that:
1. Spins up isolated containers
2. Uses `loadout apply --target ... --yes` to inject different configs
3. Runs the same task under each config
4. Compares results (token usage, quality, latency)

### What loadout needs to better support token_miser

| Need | Current state | Gap |
|------|--------------|-----|
| **Fast container injection** | Works, but copies files. | Symlink mode or bind-mount-friendly layout would be faster for repeated experiments. |
| **Bundle identity verification** | Checks name + version for idempotency. | No hash/checksum — can't verify the bundle content is actually what the manifest claims. Two bundles with same name+version but different content are treated as identical. |
| **Experiment metadata** | State file tracks `active`, `applied_at`, `bundle_path`. | No hook for token_miser to attach experiment metadata (run_id, experiment_name, variant_label). |
| **Multi-loadout composition** | Single-loadout model. | token_miser might want to compose a base config + experimental overlay. Currently requires pre-merging bundles externally. |
| **Machine-readable output** | Human-readable stdout. | No `--json` flag for programmatic consumers. token_miser has to parse human text or read the state file directly. |
| **Cleanup** | Backups accumulate. | In container contexts backups are pointless waste. Need `--no-backup` flag or container-aware mode. |

---

## Part 3: Roadmap

### Phase 1: Solidify the foundation (next)

**Goal:** Fix the gaps that make the MVP unreliable or confusing.

- [ ] **Add manifest `schema_version` field** — default `1`, validate on load, error on unknown versions.
- [ ] **Add `--json` output mode** — for `status`, `validate`, and `apply`. Critical for token_miser integration.
- [ ] **Add `--no-backup` flag to `apply`** — for container/ephemeral contexts where backups are waste.
- [ ] **Delete `backup.py`** — move any needed logic into apply/restore, remove dead code.
- [ ] **Remove `REQUIRED_FIELDS` compat export** — no consumers to break.
- [ ] **Warn on silently-skipped absolute dest paths** — print to stderr instead of swallowing.
- [ ] **Error on empty capture** — don't create placeholder bundles.
- [ ] **Add backup pruning** — `--keep N` on apply, or `loadout prune-backups --keep 3`.
- [ ] **Add MCP config capture/apply** — discover and manage `mcp_servers.json` or equivalent.
- [ ] **Configurable capture paths** — allow `manifest.yaml` or a capture config to declare additional paths.

### Phase 2: Distribution & sharing

**Goal:** Bundles can be shared without manual file copying.

- [ ] **`loadout apply ./bundle.tar.gz`** — support archived bundles (extract to temp, validate, apply).
- [ ] **`loadout pack`** — create a `.tar.gz` from a bundle directory.
- [ ] **`loadout apply <git-url>`** — clone to temp, validate, apply. Support branch/tag/ref syntax.
- [ ] **`loadout init`** — scaffold an empty bundle with commented examples.
- [ ] **Bundle checksums** — SHA-256 manifest digest in state file. Verify on apply.

### Phase 3: Comparison & multi-bundle

**Goal:** Users can understand differences and compose configurations.

- [ ] **`loadout diff <bundleA> <bundleB>`** — content-level diff of two bundles.
- [ ] **`loadout diff --current <bundle>`** — compare bundle against applied state.
- [ ] **`loadout list`** — list known/recently-applied bundles from state history.
- [ ] **Multi-loadout composition** — apply base + overlay bundles with defined merge semantics. State tracks a stack of applied bundles.
- [ ] **Conflict detection** — warn when two bundles touch the same file.

### Phase 4: token_miser integration hooks

**Goal:** loadout becomes a first-class primitive for experiment infrastructure.

- [ ] **Experiment metadata in state** — `loadout apply --meta '{"run_id": "...", "variant": "..."}'` stores arbitrary metadata in state file.
- [ ] **`loadout apply --read-only`** — symlink or bind-mount mode for faster container injection (no copy).
- [ ] **Event hooks** — `pre-apply`, `post-apply`, `pre-restore` hooks for experiment orchestrators.
- [ ] **`loadout hash <bundle>`** — print content-addressable hash of a bundle for cache keys and experiment dedup.
- [ ] **Bulk validation** — `loadout validate dir-of-bundles/` for validating an experiment's full bundle set.

### Phase 5: Registry & ecosystem

**Goal:** Bundles are discoverable and installable from a shared registry.

- [ ] **`loadout apply @user/bundle-name`** — registry syntax with GitHub-backed resolution.
- [ ] **`loadout publish`** — push a bundle to the registry.
- [ ] **`loadout search`** — discover community bundles.
- [ ] **Dependency declarations** — bundles can declare they require specific Claude Code versions or MCP servers.
- [ ] **CI/CD integration** — GitHub Action and Docker image for loadout in pipelines.

---

## Summary

loadout fills a real gap — no existing tool does atomic profile-switching for Claude Code with rollback. The MVP is solid and well-tested. But it has dead code (`backup.py`), missing features that the design notes already describe (MCP, init, diff, archives), and lacks the machine-readable output that token_miser will need. The hardcoded capture paths and absent schema versioning will become painful as Claude Code evolves. The roadmap prioritizes fixing these foundation issues first, then distribution, then the composition and experiment-infrastructure features that make loadout genuinely powerful as token_miser's configuration layer.
