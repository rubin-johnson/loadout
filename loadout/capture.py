from __future__ import annotations

import pathlib
import shutil
import sys

import yaml

from loadout.secrets import scan_for_secrets


_SKIP_SUFFIXES = {".db"}
_SKIP_FILES = {".DS_Store", ".loadout-state.json"}
_SKIP_DIRS = {".loadout-backups", "__pycache__"}
_SCAN_DIRS = {"hooks", "bin"}


def capture_command(
    source_dir: pathlib.Path,
    output_dir: pathlib.Path,
    yes: bool = False,
    name: str = "my-loadout",
    description: str = "",
    version: str = "0.0.1",
    author: str = "",
) -> None:
    if output_dir.exists() and not yes:
        raise ValueError(f"Output path already exists: {output_dir}. Use --yes to overwrite.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = []

    for src_path in sorted(source_dir.rglob("*")):
        if src_path.is_dir():
            continue

        rel = src_path.relative_to(source_dir)
        parts = rel.parts

        if any(part in _SKIP_DIRS for part in parts):
            continue
        if rel.name in _SKIP_FILES:
            continue
        if rel.suffix in _SKIP_SUFFIXES or rel.name.endswith(".db"):
            print(f"Warning: skipping database file (non-capturable): {rel}", file=sys.stderr)
            continue

        if parts[0] in _SCAN_DIRS:
            warnings = scan_for_secrets(src_path)
            for w in warnings:
                print(f"Warning: potential secret in {rel}: {w}", file=sys.stderr)

        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)
        targets.append({"path": str(rel), "dest": str(rel)})

    manifest_data = {
        "name": name,
        "version": version,
        "author": author,
        "description": description,
        "targets": targets,
    }

    with (output_dir / "manifest.yaml").open("w") as f:
        yaml.dump(manifest_data, f, default_flow_style=False)

    print(f"Captured loadout to {output_dir}")


def capture(
    output: pathlib.Path | None = None,
    source_root: pathlib.Path | None = None,
    yes: bool = False,
) -> None:
    source = source_root or pathlib.Path.home() / ".claude"
    out = output or pathlib.Path.cwd() / "my-loadout"
    capture_command(source, out, yes=yes)
