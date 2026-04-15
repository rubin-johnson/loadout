"""Bundle restore logic."""
from __future__ import annotations

import shutil
from pathlib import Path

from loadout.backup import BACKUP_DIR
from loadout.state import clear_state, read_state


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
                raise ValueError("No backups found. Nothing to restore.")
            backups = sorted(backup_root.iterdir())
            if not backups:
                raise ValueError("No backups found. Nothing to restore.")
            backup = backups[-1].name

    backup_dir = target / BACKUP_DIR / backup
    if not backup_dir.exists():
        raise ValueError(f"Backup not found: {backup_dir}")

    # Remove only files/dirs that apply placed (from state), not unrelated files.
    placed_paths = (state or {}).get("placed_paths", [])
    if placed_paths:
        for path_str in placed_paths:
            p = Path(path_str)
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
    else:
        # Legacy: no placed_paths in state — clear everything except backups dir
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

# Alias for backward compatibility with tests
restore_command = restore_bundle
