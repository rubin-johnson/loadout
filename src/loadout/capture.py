"""Capture current config as a loadout bundle."""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from loadout.manifest import Manifest


DEFAULT_CAPTURES = [
    ("CLAUDE.md", "CLAUDE.md"),
    ("settings.json", "settings.json"),
    ("hooks", "hooks"),
    ("bin", "bin"),
]


def capture_bundle(source: Path, output: Path, yes: bool = False) -> None:
    """Capture source directory as a loadout bundle at output path."""
    if output.exists() and not yes:
        raise ValueError(f"Output path already exists: {output}. Use --yes to overwrite.")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    targets = []

    for src_name, dest_name in DEFAULT_CAPTURES:
        src = source / src_name
        if not src.exists():
            continue
        dest = output / src_name
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        targets.append({"path": src_name, "dest": dest_name})

    if not targets:
        # Nothing found — create an empty bundle with a placeholder
        (output / "CLAUDE.md").write_text("# empty loadout\n")
        targets.append({"path": "CLAUDE.md", "dest": "CLAUDE.md"})

    manifest_data = {
        "name": output.name,
        "version": "0.0.1",
        "author": "captured",
        "description": f"Captured from {source}",
        "targets": targets,
    }

    manifest_file = output / "manifest.yaml"
    with manifest_file.open("w") as f:
        yaml.dump(manifest_data, f, default_flow_style=False)

    print(f"Captured loadout to {output}")
