"""Bundle apply logic."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from loadout.manifest import Manifest
from loadout.state import write_state
from loadout.validate import validate_bundle


BACKUP_DIR = ".loadout-backups"


def apply_bundle(bundle_path: Path, target: Path, yes: bool = False, dry_run: bool = False) -> None:
    """Apply a bundle to target directory. Backs up existing files first."""
    errors = validate_bundle(bundle_path)
    if errors:
        raise ValueError("Bundle validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    manifest = Manifest.load(bundle_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    backup_dir = target / BACKUP_DIR / timestamp

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

    for entry in manifest.targets:
        src = bundle_path / entry.path
        # dest is relative if it starts with ~, make it relative to target
        dest_str = entry.dest
        if dest_str.startswith("~/.claude/"):
            dest_str = dest_str[len("~/.claude/"):]
        elif dest_str.startswith("/"):
            # absolute path — not supported in target mode, skip
            continue

        dest = target / dest_str
        backup_dest = backup_dir / dest_str

        if dry_run:
            print(f"  [dry-run] {src} -> {dest}")
            continue

        # Backup existing file/dir if it exists
        if dest.exists():
            backup_dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_dir():
                shutil.copytree(dest, backup_dest)
            else:
                shutil.copy2(dest, backup_dest)

        # Copy from bundle to target
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    if not dry_run:
        write_state(target, {
            "active": manifest.name,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "bundle_path": str(bundle_path.resolve()),
            "manifest_version": manifest.version,
            "backup": timestamp,
        })
