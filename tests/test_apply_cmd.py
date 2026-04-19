import os
import subprocess
import sys

import yaml

from loadout.backup import list_backups
from loadout.state import read_state


def _cli(*args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env or os.environ.copy(),
    )


def _make_package(path, name="test", version="0.1.0"):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# package")
    (path / "manifest.yaml").write_text(
        yaml.dump(
            {
                "name": name,
                "version": version,
                "author": "ci",
                "description": "d",
                "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}],
            }
        )
    )


def test_apply_writes_state(tmp_path):
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    _make_package(pkg)
    r = _cli("apply", str(pkg), "--target", str(target), "--yes")
    assert r.returncode == 0
    state = read_state(target)
    assert state["active"] == "test"
    assert state["manifest_version"] == "0.1.0"
    assert state["package_path"] == str(pkg.resolve())


def test_apply_creates_backup(tmp_path):
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    (target / "CLAUDE.md").write_text("original")
    _make_package(pkg)
    _cli("apply", str(pkg), "--target", str(target), "--yes")
    assert len(list_backups(target)) == 1


def test_apply_second_run_updates_state(tmp_path):
    """Re-applying the same package updates state to reflect latest apply."""
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    _make_package(pkg)
    _cli("apply", str(pkg), "--target", str(target), "--yes")
    first_state = read_state(target)
    _make_package(pkg, version="0.2.0")
    _cli("apply", str(pkg), "--target", str(target), "--yes")
    second_state = read_state(target)
    assert second_state["manifest_version"] == "0.2.0"
    assert second_state["applied_at"] >= first_state["applied_at"]


def test_dry_run_no_changes(tmp_path):
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    (target / "CLAUDE.md").write_text("untouched")
    _make_package(pkg)
    r = _cli("apply", str(pkg), "--target", str(target), "--dry-run")
    assert r.returncode == 0
    assert (target / "CLAUDE.md").read_text() == "untouched"


def test_invalid_package_aborts(tmp_path):
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text("name: t\nversion: bad\n")
    r = _cli("apply", str(pkg), "--target", str(target), "--yes")
    assert r.returncode != 0


def test_dry_run_lists_files(tmp_path):
    pkg, target = tmp_path / "p", tmp_path / "t"
    target.mkdir()
    _make_package(pkg)
    r = _cli("apply", str(pkg), "--target", str(target), "--dry-run")
    assert "CLAUDE.md" in r.stdout
