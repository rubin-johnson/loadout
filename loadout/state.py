from __future__ import annotations

import json
import pathlib
from typing import Any

STATE_FILENAME = ".loadout-state.json"


def read_state(target_dir: pathlib.Path) -> dict[str, Any] | None:
    path = pathlib.Path(target_dir) / STATE_FILENAME
    if not path.exists():
        return None
    return json.loads(path.read_text())


def write_state(target_dir: pathlib.Path, state: dict[str, Any]) -> None:
    target_dir = pathlib.Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / STATE_FILENAME).write_text(json.dumps(state, indent=2))


def clear_state(target_dir: pathlib.Path) -> None:
    path = pathlib.Path(target_dir) / STATE_FILENAME
    if path.exists():
        path.unlink()
