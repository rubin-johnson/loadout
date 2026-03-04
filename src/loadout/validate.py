"""Bundle validation logic."""
from __future__ import annotations

import yaml
from pathlib import Path

from loadout.manifest import _REQUIRED_FIELDS, _SEMVER_RE


def validate_bundle(bundle_path: Path | None) -> list[str]:
    """Return a list of validation errors; empty list means valid."""
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

    manifest_path = bundle_path / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("manifest.yaml not found in bundle")
        return errors

    try:
        data = yaml.safe_load(manifest_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"manifest.yaml is not valid YAML: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append("manifest.yaml must be a YAML mapping")
        return errors

    for f in _REQUIRED_FIELDS:
        if f not in data or data[f] is None:
            errors.append(f"missing required field: {f}")

    version = data.get("version")
    if version and (not isinstance(version, str) or not _SEMVER_RE.match(str(version))):
        errors.append(f"invalid semver version: {version!r}")

    targets = data.get("targets") or []
    declared_paths = []
    for i, t in enumerate(targets):
        if not isinstance(t, dict):
            errors.append(f"target {i} is not a mapping")
            continue
        if "path" not in t:
            errors.append(f"target {i} missing 'path'")
        if "dest" not in t:
            errors.append(f"target {i} missing 'dest'")
        if "path" in t:
            declared_paths.append(t["path"])

    for path in declared_paths:
        src = bundle_path / path
        if not src.exists():
            errors.append(f"Target source not found in bundle: {path}")

    return errors
