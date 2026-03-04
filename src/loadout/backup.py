from __future__ import annotations

import datetime
import pathlib
import re
import shutil

BACKUP_DIR = ".loadout-backups"
_TS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")


def create_backup(target_dir: pathlib.Path) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    dest = target_dir / BACKUP_DIR / ts
    dest.mkdir(parents=True, exist_ok=True)
    for item in target_dir.iterdir():
        if item.name == BACKUP_DIR:
            continue
        if item.is_dir():
            shutil.copytree(item, dest / item.name)
        else:
            shutil.copy2(item, dest / item.name)
    return ts


def list_backups(target_dir: pathlib.Path) -> list[str]:
    backup_root = target_dir / BACKUP_DIR
    if not backup_root.exists():
        return []
    return sorted(
        entry.name
        for entry in backup_root.iterdir()
        if entry.is_dir() and _TS_PATTERN.match(entry.name)
    )


def get_latest_backup(target_dir: pathlib.Path) -> str | None:
    backups = list_backups(target_dir)
    return backups[-1] if backups else None
