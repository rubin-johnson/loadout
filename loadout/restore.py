from __future__ import annotations

import pathlib
import shutil
import sys

from loadout.backup import BACKUP_DIR
from loadout.state import clear_state, read_state


def restore_command(
    target_dir: pathlib.Path,
    backup_ts: str | None,
    yes: bool,
) -> None:
    """Restore target_dir from a backup, then clear the state file."""
    if backup_ts is None:
        state = read_state(target_dir)
        if state is None:
            raise ValueError(
                "No .loadout-state.json found and no --backup specified. "
                "Cannot determine which backup to restore."
            )
        backup_ts = state["backup"]

    backup_dir = target_dir / BACKUP_DIR / backup_ts
    if not backup_dir.exists():
        raise ValueError(f"Backup not found: {backup_dir}")

    if sys.stdin.isatty() and not yes:
        ans = input(f"Restore from backup {backup_ts}? [y/N] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return

    shutil.copytree(backup_dir, target_dir, dirs_exist_ok=True)
    clear_state(target_dir)
