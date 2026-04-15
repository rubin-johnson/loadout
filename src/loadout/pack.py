"""Pack current config into a loadout package."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

from loadout.secrets import scan_for_secrets

DEFAULT_CAPTURES = [
    ("CLAUDE.md", "CLAUDE.md"),
    ("settings.json", "settings.json"),
    ("hooks", "hooks"),
    ("bin", "bin"),
]

_SKIP_SUFFIXES = {".db"}
_SCAN_DIRS = {"hooks", "bin"}


def pack(source: Path, output: Path, yes: bool = False) -> None:
    """Pack source directory into a loadout package at output path."""
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
        if src.is_file() and src.suffix in _SKIP_SUFFIXES:
            print(f"Warning: skipping database file (non-capturable): {src_name}", file=sys.stderr)
            continue
        dest = output / src_name
        if src.is_dir():
            shutil.copytree(src, dest, ignore=_ignore_db)
            if src_name in _SCAN_DIRS:
                for f in dest.rglob("*"):
                    if f.is_file():
                        try:
                            warnings = scan_for_secrets(f)
                            for w in warnings:
                                print(f"Warning: potential secret in {src_name}/{f.name}: {w}", file=sys.stderr)
                        except UnicodeDecodeError:
                            pass
        else:
            shutil.copy2(src, dest)
        targets.append({"path": src_name, "dest": dest_name})

    for item in source.iterdir():
        if item.suffix in _SKIP_SUFFIXES or item.name.endswith(".db"):
            print(f"Warning: skipping database file (non-capturable): {item.name}", file=sys.stderr)

    if not targets:
        (output / "CLAUDE.md").write_text("# empty loadout\n")
        targets.append({"path": "CLAUDE.md", "dest": "CLAUDE.md"})

    manifest_data = {
        "name": output.name,
        "version": "0.0.1",
        "author": "captured",
        "description": f"Captured from {source}",
        "targets": targets,
    }

    with (output / "manifest.yaml").open("w") as f:
        yaml.dump(manifest_data, f, default_flow_style=False)

    print(f"Captured loadout to {output}")


def _ignore_db(directory: str, contents: list[str]) -> list[str]:
    return [f for f in contents if Path(f).suffix in _SKIP_SUFFIXES or f.endswith(".db")]
