from __future__ import annotations

import pathlib
from typing import Any


def read_state(state_path: pathlib.Path | None = None) -> dict[str, Any]:
    raise NotImplementedError


def write_state(state: dict[str, Any], state_path: pathlib.Path | None = None) -> None:
    raise NotImplementedError
