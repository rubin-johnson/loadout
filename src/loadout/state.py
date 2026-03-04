"""Loadout state file management."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_FILENAME = ".loadout-state.json"


def state_path(target: Path) -> Path:
    return target / STATE_FILENAME


def read_state(target: Path) -> dict[str, Any] | None:
    path = state_path(target)
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def write_state(target: Path, data: dict[str, Any]) -> None:
    path = state_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def clear_state(target: Path) -> None:
    path = state_path(target)
    if path.exists():
        path.unlink()
