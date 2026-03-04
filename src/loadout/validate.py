"""Bundle validation logic."""
from __future__ import annotations

from pathlib import Path
from loadout.manifest import Manifest


def validate_bundle(bundle_path: Path) -> list[str]:
    """Return a list of validation errors; empty list means valid."""
    errors: list[str] = []

    if not bundle_path.exists():
        errors.append(f"Bundle path does not exist: {bundle_path}")
        return errors

    if not bundle_path.is_dir():
        errors.append(f"Bundle path is not a directory: {bundle_path}")
        return errors

    try:
        manifest = Manifest.load(bundle_path)
    except (ValueError, Exception) as e:
        errors.append(f"Invalid manifest.yaml: {e}")
        return errors

    for target in manifest.targets:
        src = bundle_path / target.path
        if not src.exists():
            errors.append(f"Target source not found in bundle: {target.path}")

    return errors
