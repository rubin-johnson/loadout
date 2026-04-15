"""Package apply logic."""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from loadout.backup import BACKUP_DIR
from loadout.manifest import Manifest
from loadout.state import write_state
from loadout.validate import validate_package


def _resolve_dest(dest_str: str, target: Path) -> Path | None:
    """Resolve a manifest dest string to an absolute path under target.
    Returns None for absolute paths or paths that escape target.
    """
    if dest_str.startswith("~/.claude/"):
        dest_str = dest_str[len("~/.claude/"):]
    elif dest_str in ("~/.claude", "~"):
        return None
    elif dest_str.startswith("~/"):
        dest_str = dest_str[2:]
    elif dest_str.startswith("/"):
        return None
    if not dest_str:
        return None
    resolved = (target / dest_str).resolve()
    if not resolved.is_relative_to(target.resolve()):
        return None
    return resolved


def atomic_apply(bundle_path: Path, target: Path, manifest: Manifest) -> None:
    """Copy manifest targets from package to target atomically.

    Uses a temp dir + move strategy so a failure mid-copy leaves existing
    files untouched. Does not back up, does not write state -- callers handle that.
    """
    with tempfile.TemporaryDirectory(dir=target.parent) as staging_str:
        staging = Path(staging_str)

        staged: list[tuple[Path, Path]] = []
        for entry in manifest.targets:
            src = bundle_path / entry.path
            dest = _resolve_dest(entry.dest, target)
            if dest is None:
                continue
            staged_dest = staging / entry.path
            staged_dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, staged_dest)
            else:
                shutil.copy2(src, staged_dest)
            staged.append((staged_dest, dest))

        for staged_path, final_dest in staged:
            final_dest.parent.mkdir(parents=True, exist_ok=True)
            if final_dest.exists() and final_dest.is_dir():
                shutil.rmtree(final_dest)
            shutil.move(str(staged_path), final_dest)


def apply_package(bundle_path: Path, target: Path, yes: bool = False, dry_run: bool = False) -> None:
    """Apply a package to target directory. Backs up existing files first."""
    errors = validate_package(bundle_path)
    if errors:
        raise ValueError("Package validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    manifest = Manifest.load(bundle_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    backup_dir = target / BACKUP_DIR / timestamp

    if dry_run:
        for entry in manifest.targets:
            dest = _resolve_dest(entry.dest, target)
            if dest is not None:
                print(f"  [dry-run] {bundle_path / entry.path} -> {dest}")
        return

    target.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    for entry in manifest.targets:
        dest = _resolve_dest(entry.dest, target)
        if dest is None or not dest.exists():
            continue
        backup_dest = backup_dir / entry.path
        backup_dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_dir():
            shutil.copytree(dest, backup_dest)
        else:
            shutil.copy2(dest, backup_dest)

    placed_paths = [
        str(_resolve_dest(e.dest, target))
        for e in manifest.targets
        if _resolve_dest(e.dest, target) is not None
    ]

    atomic_apply(bundle_path, target, manifest)

    write_state(target, {
        "active": manifest.name,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "bundle_path": str(bundle_path.resolve()),
        "manifest_version": manifest.version,
        "backup": timestamp,
        "placed_paths": placed_paths,
    })
