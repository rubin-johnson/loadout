import yaml

from loadout.validate import validate_bundle


def _bundle(tmp_path, **overrides):
    d = tmp_path / "bundle"
    d.mkdir()
    data = {
        "name": "t", "version": "0.1.0", "author": "a",
        "description": "d",
        "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}]
    }
    data.update(overrides)
    (d / "CLAUDE.md").write_text("x")
    (d / "manifest.yaml").write_text(yaml.dump(data))
    return d


def test_valid_bundle_returns_empty(tmp_path):
    b = _bundle(tmp_path)
    assert validate_bundle(b) == []


def test_missing_manifest(tmp_path):
    d = tmp_path / "bundle"
    d.mkdir()
    errors = validate_bundle(d)
    assert len(errors) == 1
    assert "manifest.yaml" in errors[0]


def test_missing_target_file(tmp_path):
    b = _bundle(tmp_path)
    (b / "CLAUDE.md").unlink()
    errors = validate_bundle(b)
    assert any("CLAUDE.md" in e for e in errors)


def test_invalid_semver(tmp_path):
    b = _bundle(tmp_path, version="bad")
    errors = validate_bundle(b)
    assert len(errors) >= 1


def test_multiple_errors_reported(tmp_path):
    b = _bundle(tmp_path, version="bad")
    (b / "CLAUDE.md").unlink()
    errors = validate_bundle(b)
    assert len(errors) >= 2


def test_targets_missing_dest_field(tmp_path):
    b = _bundle(tmp_path)
    (b / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "0.1.0", "author": "a", "description": "d",
        "targets": [{"path": "CLAUDE.md"}]  # no dest
    }))
    errors = validate_bundle(b)
    assert any("dest" in e for e in errors)
