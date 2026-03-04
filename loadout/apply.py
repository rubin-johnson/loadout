from __future__ import annotations

import pathlib


def atomic_apply(
    bundle_path: pathlib.Path | None,
    target_root: pathlib.Path | None = None,
    dry_run: bool = False,
    yes: bool = False,
) -> None:
    raise NotImplementedError
