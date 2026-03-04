"""Bundle manifest loading and validation."""
from __future__ import annotations

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


REQUIRED_FIELDS = {"name", "version", "author", "description", "targets"}


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
    def load(cls, bundle_path: Path) -> "Manifest":
        manifest_file = bundle_path / "manifest.yaml"
        if not manifest_file.exists():
            raise ValueError(f"manifest.yaml not found in {bundle_path}")
        with manifest_file.open() as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest":
        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ValueError(f"manifest.yaml missing required fields: {missing}")
        targets = [
            TargetEntry(path=t["path"], dest=t["dest"])
            for t in data["targets"]
        ]
        return cls(
            name=data["name"],
            version=data["version"],
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
