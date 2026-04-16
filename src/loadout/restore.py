"""Package restore logic."""
from __future__ import annotations

import shutil
from pathlib import Path

from loadout.apply import _confirm
from loadout.backup import BACKUP_DIR, list_backups
from loadout.state import clear_state, read_state


def restore_package(target: Path, backup: str | None = None, yes: bool = False) -> None:
    """Restore target from the most recent backup (or named backup)."""
    state = read_state(target)

    if backup is None:
        if state is not None and state.get("backup"):
            backup = state["backup"]
        else:
            backups = list_backups(target)
            if not backups:
                raise ValueError("No backups found. Nothing to restore.")
            backup = backups[-1]

    backup_dir = target / BACKUP_DIR / backup
    if not backup_dir.exists():
        raise ValueError(f"Backup not found: {backup_dir}")

    if not yes:
        if not _confirm(f"Restore {target} from backup {backup}?"):
            raise ValueError("Aborted (use --yes to skip confirmation)")

    placed_paths = (state or {}).get("placed_paths", [])
    target_resolved = target.resolve()
    if placed_paths:
        for path_str in placed_paths:
            p = Path(path_str).resolve()
            if not p.is_relative_to(target_resolved):
                continue
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
    else:
        for item in target.iterdir():
            if item.name == BACKUP_DIR:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    for item in backup_dir.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    clear_state(target)
    print(f"Restored from backup: {backup}")
