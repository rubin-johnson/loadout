from __future__ import annotations

import os
import pathlib


def get_target_root(cli_target: str | None = None) -> pathlib.Path:
    if cli_target:
        return pathlib.Path(cli_target)
    env_target = os.environ.get("LOADOUT_TARGET_ROOT")
    if env_target:
        return pathlib.Path(env_target)
    return pathlib.Path.home() / ".claude"
