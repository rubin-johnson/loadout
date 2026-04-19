"""Package validation logic."""

from __future__ import annotations

from pathlib import Path

import yaml

from loadout.manifest import _REQUIRED_FIELDS, _SEMVER_RE


def validate_package(package_path: Path | None) -> list[str]:
    """Return a list of validation errors; empty list means valid."""
    errors: list[str] = []

    if package_path is None:
        errors.append("No package path provided")
        return errors

    if not package_path.exists():
        errors.append(f"Package path does not exist: {package_path}")
        return errors

    if not package_path.is_dir():
        errors.append(f"Package path is not a directory: {package_path}")
        return errors

    manifest_path = package_path / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("manifest.yaml not found in package")
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
        src = (package_path / path).resolve()
        if not src.is_relative_to(package_path.resolve()):
            errors.append(f"Target source escapes package directory: {path}")
            continue
        if not src.exists():
            errors.append(f"Target source not found in package: {path}")

    return errors
