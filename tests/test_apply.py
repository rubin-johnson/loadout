from unittest.mock import patch

import pytest
import yaml

from loadout.apply import atomic_apply
from loadout.manifest import load_manifest


def _make_package(tmp_path, files: dict, targets_override=None):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    for name, content in files.items():
        p = pkg / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    targets = targets_override or [
        {"path": name, "dest": name} for name in files
    ]
    (pkg / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "0.1.0", "author": "a",
        "description": "d", "targets": targets
    }))
    return pkg


def test_files_land_at_correct_paths(tmp_path):
    pkg = _make_package(tmp_path, {"CLAUDE.md": "new"})
    target = tmp_path / "target"
    target.mkdir()
    manifest = load_manifest(pkg)
    atomic_apply(pkg, target, manifest)
    assert (target / "CLAUDE.md").read_text() == "new"


def test_unrelated_files_untouched(tmp_path):
    pkg = _make_package(tmp_path, {"CLAUDE.md": "new"})
    target = tmp_path / "target"
    target.mkdir()
    (target / "unrelated.txt").write_text("keep")
    manifest = load_manifest(pkg)
    atomic_apply(pkg, target, manifest)
    assert (target / "unrelated.txt").read_text() == "keep"


def test_nested_dest_created(tmp_path):
    targets = [{"path": "hook.sh", "dest": "hooks/hook.sh"}]
    pkg = _make_package(tmp_path, {"hook.sh": "#!/bin/bash"}, targets)
    target = tmp_path / "target"
    target.mkdir()
    manifest = load_manifest(pkg)
    atomic_apply(pkg, target, manifest)
    assert (target / "hooks" / "hook.sh").read_text() == "#!/bin/bash"


def test_tilde_dest_resolves_to_target(tmp_path):
    targets = [{"path": "CLAUDE.md", "dest": "~/CLAUDE.md"}]
    pkg = _make_package(tmp_path, {"CLAUDE.md": "tilde"}, targets)
    target = tmp_path / "target"
    target.mkdir()
    manifest = load_manifest(pkg)
    atomic_apply(pkg, target, manifest)
    assert (target / "CLAUDE.md").read_text() == "tilde"


def test_atomic_apply_ignores_source_path_traversal(tmp_path):
    from loadout.manifest import Manifest, TargetEntry
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    # Manifest entry with path traversal in source
    manifest = Manifest(
        name="test", version="0.1.0", author="test",
        description="test",
        targets=[TargetEntry(path="../escape.txt", dest="escape.txt")],
    )
    (tmp_path / "escape.txt").write_text("should not be copied")
    atomic_apply(pkg, target, manifest)
    assert not (target / "escape.txt").exists()


def test_atomic_on_move_failure(tmp_path):
    pkg = _make_package(tmp_path, {"a.txt": "new"})
    target = tmp_path / "target"
    target.mkdir()
    (target / "a.txt").write_text("original")
    manifest = load_manifest(pkg)
    with patch("loadout.apply.shutil.move", side_effect=OSError("fail")):
        with pytest.raises(OSError):
            atomic_apply(pkg, target, manifest)
    assert (target / "a.txt").read_text() == "original"
