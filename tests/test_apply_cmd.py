import pathlib, json, yaml, subprocess, sys, os
from loadout.state import read_state
from loadout.backup import list_backups

def _cli(*args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
        env=env or os.environ.copy()
    )

def _make_bundle(path, name="test", version="0.1.0"):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# bundle")
    (path / "manifest.yaml").write_text(yaml.dump({
        "name": name, "version": version, "author": "ci",
        "description": "d",
        "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}]
    }))

def test_apply_writes_state(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    _make_bundle(bundle)
    r = _cli("apply", str(bundle), "--target", str(target), "--yes")
    assert r.returncode == 0
    state = read_state(target)
    assert state["active"] == "test"
    assert state["manifest_version"] == "0.1.0"
    assert state["bundle_path"] == str(bundle.resolve())

def test_apply_creates_backup(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    (target / "CLAUDE.md").write_text("original")
    _make_bundle(bundle)
    _cli("apply", str(bundle), "--target", str(target), "--yes")
    assert len(list_backups(target)) == 1

def test_apply_idempotent_no_duplicate_backup(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    _make_bundle(bundle)
    _cli("apply", str(bundle), "--target", str(target), "--yes")
    _cli("apply", str(bundle), "--target", str(target), "--yes")
    assert len(list_backups(target)) == 1

def test_dry_run_no_changes(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    (target / "CLAUDE.md").write_text("untouched")
    _make_bundle(bundle)
    r = _cli("apply", str(bundle), "--target", str(target), "--dry-run")
    assert r.returncode == 0
    assert (target / "CLAUDE.md").read_text() == "untouched"

def test_invalid_bundle_aborts(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    bundle.mkdir()
    (bundle / "manifest.yaml").write_text("name: t\nversion: bad\n")
    r = _cli("apply", str(bundle), "--target", str(target), "--yes")
    assert r.returncode != 0

def test_dry_run_lists_files(tmp_path):
    bundle, target = tmp_path / "b", tmp_path / "t"
    target.mkdir()
    _make_bundle(bundle)
    r = _cli("apply", str(bundle), "--target", str(target), "--dry-run")
    assert "CLAUDE.md" in r.stdout
