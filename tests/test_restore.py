import subprocess
import sys

from loadout.backup import create_backup
from loadout.state import read_state, write_state


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args],
        capture_output=True, text=True, stdin=subprocess.DEVNULL
    )

def _setup_target_with_backup(tmp_path, original_content="original"):
    target = tmp_path / "target"
    target.mkdir()
    (target / "CLAUDE.md").write_text(original_content)
    ts = create_backup(target)
    write_state(target, {
        "active": "test", "applied_at": "2026-01-01T00:00:00Z",
        "package_path": "/tmp/p", "manifest_version": "0.1.0", "backup": ts
    })
    (target / "CLAUDE.md").write_text("modified by apply")
    return target, ts

def test_restore_from_state(tmp_path):
    target, ts = _setup_target_with_backup(tmp_path)
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr
    assert (target / "CLAUDE.md").read_text() == "original"

def test_restore_clears_state(tmp_path):
    target, ts = _setup_target_with_backup(tmp_path)
    _cli("restore", "--target", str(target), "--yes")
    assert read_state(target) is None

def test_restore_explicit_backup(tmp_path):
    target, ts = _setup_target_with_backup(tmp_path)
    r = _cli("restore", "--target", str(target), "--backup", ts, "--yes")
    assert r.returncode == 0, r.stderr
    assert (target / "CLAUDE.md").read_text() == "original"

def test_restore_no_state_no_backup_flag(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode != 0

def test_restore_bad_backup_timestamp(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    r = _cli("restore", "--target", str(target), "--backup", "9999-99-99-999999", "--yes")
    assert r.returncode != 0


def test_restore_with_placed_paths_only_removes_tracked(tmp_path):
    """Restore with placed_paths deletes only tracked files, not unrelated ones."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "CLAUDE.md").write_text("original")
    (target / "untracked.txt").write_text("keep me")
    ts = create_backup(target)
    write_state(target, {
        "active": "test", "applied_at": "2026-01-01T00:00:00Z",
        "package_path": "/tmp/p", "manifest_version": "0.1.0", "backup": ts,
        "placed_paths": [str(target / "CLAUDE.md")],
    })
    (target / "CLAUDE.md").write_text("modified by apply")
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr
    assert (target / "CLAUDE.md").read_text() == "original"
    assert (target / "untracked.txt").read_text() == "keep me"


def test_restore_with_placed_paths_directory_entry(tmp_path):
    """Restore with a directory in placed_paths works even if dir partially remains."""
    target = tmp_path / "target"
    target.mkdir()
    hooks = target / "hooks"
    hooks.mkdir()
    (hooks / "pre.sh").write_text("original hook")
    ts = create_backup(target)
    write_state(target, {
        "active": "test", "applied_at": "2026-01-01T00:00:00Z",
        "package_path": "/tmp/p", "manifest_version": "0.1.0", "backup": ts,
        "placed_paths": [str(hooks)],
    })
    (hooks / "pre.sh").write_text("modified hook")
    (hooks / "extra.sh").write_text("new file from apply")
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr
    assert (hooks / "pre.sh").read_text() == "original hook"


def test_restore_surgical_leaves_untracked_files(tmp_path):
    """Surgical restore (placed_paths present) must not touch unrelated files."""
    target = tmp_path / "target"
    target.mkdir()
    # Create an untracked file
    untracked = target / "untracked.txt"
    untracked.write_text("keep me")
    # Create a backup
    backup_dir = target / ".loadout-backups" / "2026-01-01-000000"
    backup_dir.mkdir(parents=True)
    (backup_dir / "CLAUDE.md").write_text("restored content")
    # Write state with placed_paths that does NOT include untracked.txt
    write_state(target, {
        "backup": "2026-01-01-000000",
        "placed_paths": [str(target / "CLAUDE.md")],
    })
    from loadout.restore import restore_package
    restore_package(target, yes=True)
    assert untracked.exists(), "untracked file must survive surgical restore"


def test_apply_without_yes_aborts_in_non_tty(tmp_path):
    """Apply without --yes and with stdin=DEVNULL (non-TTY) should abort."""
    import yaml
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "CLAUDE.md").write_text("# test")
    (pkg / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "0.1.0", "author": "a",
        "description": "d",
        "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}]
    }))
    target = tmp_path / "target"
    target.mkdir()
    r = _cli("apply", str(pkg), "--target", str(target))
    assert r.returncode != 0
    assert "aborted" in r.stderr.lower() or "yes" in r.stderr.lower()
