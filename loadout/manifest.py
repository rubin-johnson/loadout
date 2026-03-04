from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any


@dataclass
class Manifest:
    name: str
    version: str
    author: str
    description: str
    targets: list[dict[str, str]]


def load_manifest(bundle_path: pathlib.Path) -> Manifest:
    raise NotImplementedError
