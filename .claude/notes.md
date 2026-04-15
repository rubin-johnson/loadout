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

### What's next
- Run full standard suite (15 tasks) on Bedrock for comprehensive baseline
- Add more recommendation rules (token efficiency, planning discipline)
- Set up a real kanon manifest repo for loadout packages
- Show the pipeline to kanon creators

<!-- session: 2026-04-15T18:43:28Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:43:39Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:44:00Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->

<!-- session: 2026-04-15T18:44:12Z | cost: $0.0000 | tokens: 0 | model:  | sha: d6174a8 -->
