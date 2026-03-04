from __future__ import annotations

import pathlib

import yaml

from loadout.manifest import load_manifest, ManifestError


def validate_bundle(bundle_dir: pathlib.Path) -> list[str]:
    """Return a list of validation errors; empty list means valid."""
    errors: list[str] = []

    manifest_path = bundle_dir / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("manifest.yaml not found")
        return errors

    try:
        raw = yaml.safe_load(manifest_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"manifest.yaml parse error: {e}")
        return errors

    if not isinstance(raw, dict):
        errors.append("manifest.yaml is not a valid YAML mapping")
        return errors

    try:
        load_manifest(bundle_dir)
    except ManifestError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(str(e))

    for target in raw.get("targets") or []:
        if not isinstance(target, dict):
            errors.append(f"invalid target entry: {target!r}")
            continue
        if "dest" not in target:
            errors.append(f"target missing required 'dest' field: {target.get('path', '?')}")
        path = target.get("path")
        if path and not (bundle_dir / path).exists():
            errors.append(f"target file not found in bundle: {path}")

    return errors
