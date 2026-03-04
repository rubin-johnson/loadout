"""Bundle restore logic."""
from __future__ import annotations

import shutil
from pathlib import Path

from loadout.state import read_state, clear_state


BACKUP_DIR = ".loadout-backups"


def restore_bundle(target: Path, backup: str | None = None, yes: bool = False) -> None:
    """Restore target from the most recent backup (or named backup)."""
    state = read_state(target)

    if backup is None:
        if state is not None and state.get("backup"):
            backup = state["backup"]
        else:
            # Find the most recent backup by directory name
            backup_root = target / BACKUP_DIR
            if not backup_root.exists():
                print("No backups found. Nothing to restore.")
                return
            backups = sorted(backup_root.iterdir())
            if not backups:
                print("No backups found. Nothing to restore.")
                return
            backup = backups[-1].name

    backup_dir = target / BACKUP_DIR / backup
    if not backup_dir.exists():
        raise ValueError(f"Backup not found: {backup_dir}")

    # Clear current target contents (except backups dir) before restoring
    for item in target.iterdir():
        if item.name == BACKUP_DIR:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Restore each file/dir from backup
    for item in backup_dir.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    clear_state(target)
    print(f"Restored from backup: {backup}")
