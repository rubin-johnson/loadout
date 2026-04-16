## 2026-04-14 — v0.1.0 release and token_miser Python rewrite

### loadout
- Merged feature/loadout-clone-implementation to main
- Tagged v0.1.0
- Scrapped Go rewrite, Python only now
- Fixed: _default_target() undefined, datetime.utcnow() deprecation, BACKUP_DIR duplication
- Added: LICENSE (Apache 2.0), CHANGELOG.md, GitHub Actions CI, ruff linting, example bundle, --version flag
- All 82 tests pass, lint clean

### token_miser
- Complete rewrite from Go to Python (python-rewrite branch merged to main, pushed)
- 10 modules in src/token_miser/, 46 tests pass, lint clean
- Fixed Go bugs: added subprocess timeout (600s default), quality scoring warns instead of silently failing
- Task YAML files now use ${EXPERIMENT_REPO} env var instead of hardcoded paths
- README documents the loadout + kanon + token_miser pipeline story

### token_miser continued — loadout+kanon integration
- Created 3 loadout bundles: token-miser (terse), thorough (verbose), tdd-strict (tests first)
- All validate clean with `loadout validate`
- Demonstrated loadout swap workflow: apply -> status -> swap -> restore
- Added `.kanon` config file showing kanon distribution story
- Added docs/kanon-integration.md explaining the full pipeline
- Created quick-001 task for fast demo experiments
- Ran 3 real experiments (6 runs), all 100% criteria pass
- Results: tdd-strict cheapest (-5.8%), thorough +2.1% but 2x tokens, token-miser +12.6% (ironic)
- Added LICENSE, CHANGELOG, GitHub Actions CI
- All pushed to main

## 2026-04-15 — token_miser tune workflow + kanon terminology alignment

### token_miser — tune workflow
- Added 7 new modules: config_manager, suite, repos, recommend, profile_builder, tune, digest
- 15 benchmark tasks across 5 categories (feature, bugfix, refactor, test, sequential)
- 2 fixture repos (tiny-cli, tiny-api) shipped as git bundles
- Quick suite (8 tasks, no network) and standard suite (15 tasks incl Flask/httpx)
- Tune workflow: baseline→analyze→recommend→generate→rerun→compare
- Recommendation engine: 6 rule-based heuristics
- Digest export for git-trackable session summaries
- Bedrock support via ~/.token_miser/claude.env (separate creds from parent session)
- --bare flag for cheap iteration (skips hooks/plugins), default is full fidelity
- End-to-end Bedrock run: +46% efficiency index on tuned package

### Terminology alignment (bundle→package, capture→pack)
- loadout: renamed bundle→package, capture→pack across all code and tests (84 tests)
- token_miser: renamed arm→PackageRef, profile→package, config_manager→package_adapter
- DB migration for existing results.db (arm→package_name columns)
- CLI: --control→--baseline, --treatment→--package (old flags as hidden aliases)
- New: `publish` subcommand (push tuned package to git for kanon distribution)
- New: `packages` subcommand (list kanon-distributed packages)
- Pipeline speaks one language: kanon installs packages → loadout applies → token_miser benchmarks → publishes
- 144 tests pass in both projects, lint clean

### Review-fix loop
- Critical: path traversal in apply.py/_resolve_dest and restore.py/placed_paths — added is_relative_to containment
- Critical: SQL injection prevention in token_miser update_tune_session — column allowlist
- Fixed quality score parsing (list format was silently dropped), __import__ hack, stale repo cache, shallow clone tags
- Removed orphaned backward-compat aliases, false-positive idempotent backup test

### Continued improvements
- 4 new recommendation rules (10 total): high output ratio, no parallel guidance, high cache miss, excessive tokens per criterion
- Kanon manifest repo live: github.com/rubin-johnson/loadout-packages (3 packages, tagged 0.1.0)
- Fixed --bare: user CLAUDE.md now copied into isolated HOME; shallow clones use --branch for tags
- Standard suite Bedrock run: 56% baseline pass rate on 15 tasks, $5.08 cost. Hard tasks (httpx retry, Flask integration) need prompt tuning.

### What's next
- Tune benchmark task prompts — Flask/httpx tasks failing consistently, prompts may be too vague or setup incomplete
- Run repeated experiments for statistical significance (3+ runs per task)
- Add LLM-powered recommendation layer (use Claude to analyze results beyond heuristic rules)
- Show the pipeline to kanon creators

<!-- session: 2026-04-15T18:43:28Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:43:39Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:44:00Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:44:12Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

## 2026-04-15 — Created loadout-packages kanon manifest repo

- Created `/home/rujohnson/code/personal/loadout-packages/` as a kanon manifest repository
- Copied 3 packages from token_miser/loadouts: token-miser, thorough, tdd-strict
- Added repo-specs/ with remote.xml, packages.xml, meta.xml (kanon manifest format)
- Published as public GitHub repo: https://github.com/rubin-johnson/loadout-packages
- Tagged 0.1.0
- Updated token_miser/.kanon to point to the new repo (was loadout-bundles, now loadout-packages)
- This closes the symbiotic loop: kanon distributes -> loadout applies -> token_miser measures
