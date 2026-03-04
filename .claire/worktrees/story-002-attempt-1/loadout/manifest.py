from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass

import yaml

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

_REQUIRED_FIELDS = ("name", "version", "author", "description", "targets")


class ManifestError(ValueError):
    pass


@dataclass
class TargetEntry:
    path: str
    dest: str


@dataclass
class Manifest:
    name: str
    version: str
    author: str
    description: str
    targets: list[TargetEntry]


def load_manifest(bundle_dir: pathlib.Path) -> Manifest:
    manifest_path = bundle_dir / "manifest.yaml"
    if not manifest_path.exists():
        raise ManifestError(f"manifest.yaml not found in {bundle_dir}")

    data = yaml.safe_load(manifest_path.read_text())

    for field in _REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            raise ManifestError(f"missing required field: {field}")

    version = data["version"]
    if not isinstance(version, str) or not _SEMVER_RE.match(version):
        raise ManifestError(f"invalid semver version: {version!r}")

    targets = [
        TargetEntry(path=t["path"], dest=t["dest"])
        for t in data["targets"]
    ]

    return Manifest(
        name=data["name"],
        version=data["version"],
        author=data["author"],
        description=data["description"],
        targets=targets,
    )
