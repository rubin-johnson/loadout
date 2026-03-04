from __future__ import annotations

import pathlib

from loadout.manifest import load_manifest, ManifestError


def validate_bundle(bundle_path: pathlib.Path | None) -> list[str]:
    errors: list[str] = []

    if bundle_path is None:
        errors.append("No bundle path provided")
        return errors

    if not bundle_path.exists():
        errors.append(f"Bundle path does not exist: {bundle_path}")
        return errors

    if not bundle_path.is_dir():
        errors.append(f"Bundle path is not a directory: {bundle_path}")
        return errors

    try:
        manifest = load_manifest(bundle_path)
    except ManifestError as e:
        errors.append(f"Invalid manifest.yaml: {e}")
        return errors

    for target in manifest.targets:
        src = bundle_path / target.path
        if not src.exists():
            errors.append(f"Target source not found in bundle: {target.path}")

    return errors
