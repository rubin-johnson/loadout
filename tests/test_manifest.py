import pathlib

import pytest
import yaml

from loadout.manifest import ManifestError, load_manifest


def _write_manifest(path: pathlib.Path, data: dict):
    (path / "manifest.yaml").write_text(yaml.dump(data))


VALID = {
    "name": "my-loadout",
    "version": "1.2.3",
    "author": "me",
    "description": "desc",
    "targets": [{"path": "CLAUDE.md", "dest": "~/.claude/CLAUDE.md"}],
}


def test_load_valid(tmp_path):
    _write_manifest(tmp_path, VALID)
    m = load_manifest(tmp_path)
    assert m.name == "my-loadout"
    assert m.version == "1.2.3"
    assert len(m.targets) == 1
    assert m.targets[0].path == "CLAUDE.md"
    assert m.targets[0].dest == "~/.claude/CLAUDE.md"


def test_missing_manifest_file(tmp_path):
    with pytest.raises(ManifestError, match="manifest.yaml"):
        load_manifest(tmp_path)


@pytest.mark.parametrize("field", ["name", "version", "author", "description", "targets"])
def test_missing_required_field(tmp_path, field):
    data = {k: v for k, v in VALID.items() if k != field}
    _write_manifest(tmp_path, data)
    with pytest.raises(ManifestError, match=field):
        load_manifest(tmp_path)


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "not-semver", "1.2.3.4", ""])
def test_invalid_semver(tmp_path, bad):
    data = {**VALID, "version": bad}
    _write_manifest(tmp_path, data)
    with pytest.raises(ManifestError):
        load_manifest(tmp_path)


@pytest.mark.parametrize("good", ["0.0.1", "1.0.0", "1.2.3-alpha.1", "2.0.0+build.1"])
def test_valid_semver(tmp_path, good):
    data = {**VALID, "version": good}
    _write_manifest(tmp_path, data)
    m = load_manifest(tmp_path)
    assert m.version == good
