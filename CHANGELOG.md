# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-04-14

First public release.

### Added

- `loadout validate` - check bundle structure and manifest
- `loadout apply` - apply a bundle to a target directory with automatic backup
- `loadout status` - show the currently applied loadout
- `loadout restore` - roll back to a previous backup
- `loadout capture` - snapshot a live `~/.claude` directory as a bundle
- `--target` flag and `LOADOUT_TARGET_ROOT` env var for non-default targets
- `--dry-run` on apply to preview changes
- `--yes` on destructive operations for CI/non-interactive use
- Automatic backup before every apply
- Secret scanning on capture (warns about credentials in hooks/bin)
- Atomic file placement (staging + move) to prevent partial applies
- State tracking via `.loadout-state.json`

## [0.0.1] - 2026-03-04

Internal development release.
