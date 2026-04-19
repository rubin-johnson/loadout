"""Pack current config into a loadout package."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

from loadout.secrets import scan_for_secrets

DEFAULT_TARGETS = [
    ("CLAUDE.md", "CLAUDE.md"),
    ("AGENTS.md", "AGENTS.md"),
    ("settings.json", "settings.json"),
    ("hooks", "hooks"),
    ("bin", "bin"),
]

_SKIP_SUFFIXES = {".db"}
_SCAN_DIRS = {"hooks", "bin"}
_SCAN_FILES = {"CLAUDE.md", "AGENTS.md", "settings.json"}


def pack(source: Path, output: Path, yes: bool = False) -> None:
    """Pack source directory into a loadout package at output path."""
    if output.exists() and not yes:
        raise ValueError(f"Output path already exists: {output}. Use --yes to overwrite.")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    targets = []

    for src_name, dest_name in DEFAULT_TARGETS:
        src = source / src_name
        if not src.exists():
            continue
        if src.is_file() and src.suffix in _SKIP_SUFFIXES:
            print(f"Warning: skipping database file (not packable): {src_name}", file=sys.stderr)
            continue
        dest = output / src_name
        if src.is_dir():
            shutil.copytree(src, dest, ignore=_ignore_db)
            if src_name in _SCAN_DIRS:
                for f in dest.rglob("*"):
                    if f.is_file():
                        try:
                            warnings = scan_for_secrets(f)
                            rel = f.relative_to(dest)
                            for w in warnings:
                                print(f"Warning: potential secret in {src_name}/{rel}: {w}", file=sys.stderr)
                        except UnicodeDecodeError:
                            pass
        else:
            shutil.copy2(src, dest)
            if src_name in _SCAN_FILES and dest.is_file():
                try:
                    warnings = scan_for_secrets(dest)
                    for w in warnings:
                        print(f"Warning: potential secret in {src_name}: {w}", file=sys.stderr)
                except UnicodeDecodeError:
                    pass
        targets.append({"path": src_name, "dest": dest_name})

    for item in source.iterdir():
        if item.suffix in _SKIP_SUFFIXES:
            print(f"Warning: skipping database file (not packable): {item.name}", file=sys.stderr)

    if not targets:
        (output / "CLAUDE.md").write_text("# empty loadout\n")
        targets.append({"path": "CLAUDE.md", "dest": "CLAUDE.md"})

    manifest_data = {
        "name": output.name,
        "version": "0.0.1",
        "author": "packed",
        "description": f"Packed from {source}",
        "targets": targets,
    }

    with (output / "manifest.yaml").open("w") as f:
        yaml.dump(manifest_data, f, default_flow_style=False)

    print(f"Packed loadout to {output}")


def _ignore_db(directory: str, contents: list[str]) -> list[str]:
    return [f for f in contents if Path(f).suffix in _SKIP_SUFFIXES]
