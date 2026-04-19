"""Package manifest loading and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REQUIRED_FIELDS = {"name", "version", "author", "description", "targets"}

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


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
    targets: list[TargetEntry] = field(default_factory=list)

    @classmethod
    def load(cls, package_path: Path) -> "Manifest":
        return load_manifest(package_path)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest":
        missing = _REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ManifestError(f"manifest.yaml missing required fields: {sorted(missing)}")
        version = data["version"]
        if not isinstance(version, str) or not _SEMVER_RE.match(str(version)):
            raise ManifestError(f"invalid semver version: {version!r}")
        targets = [TargetEntry(path=t["path"], dest=t["dest"]) for t in data["targets"]]
        return cls(
            name=data["name"],
            version=str(version),
            author=data["author"],
            description=data["description"],
            targets=targets,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "targets": [{"path": t.path, "dest": t.dest} for t in self.targets],
        }


def load_manifest(package_path: Path) -> Manifest:
    manifest_file = Path(package_path) / "manifest.yaml"
    if not manifest_file.exists():
        raise ManifestError(f"manifest.yaml not found in {package_path}")
    with manifest_file.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ManifestError("manifest.yaml must be a YAML mapping")
    return Manifest.from_dict(data)
