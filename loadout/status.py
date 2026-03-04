from __future__ import annotations

import pathlib
from typing import Any

from loadout.state import read_state


def get_status(target_dir: pathlib.Path) -> dict[str, Any] | None:
    return read_state(target_dir)
