import pathlib
import time

from loadout.backup import create_backup, list_backups, get_latest_backup, BACKUP_DIR


def test_create_backup_copies_files(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("original")
    (tmp_path / "settings.json").write_text("{}")
    ts = create_backup(tmp_path)
    backup_path = tmp_path / BACKUP_DIR / ts
    assert (backup_path / "CLAUDE.md").read_text() == "original"
    assert (backup_path / "settings.json").read_text() == "{}"


def test_backup_excludes_backup_dir(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("original")
    ts = create_backup(tmp_path)
    backup_path = tmp_path / BACKUP_DIR / ts
    assert not (backup_path / BACKUP_DIR).exists()


def test_list_backups_sorted(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("x")
    ts1 = create_backup(tmp_path)
    time.sleep(1.1)
    ts2 = create_backup(tmp_path)
    backups = list_backups(tmp_path)
    assert backups == sorted(backups)
    assert backups[0] == ts1
    assert backups[-1] == ts2


def test_get_latest_backup_none_when_empty(tmp_path):
    assert get_latest_backup(tmp_path) is None


def test_get_latest_backup(tmp_path):
    (tmp_path / "f.txt").write_text("x")
    ts1 = create_backup(tmp_path)
    time.sleep(1.1)
    ts2 = create_backup(tmp_path)
    assert get_latest_backup(tmp_path) == ts2


def test_backup_empty_target(tmp_path):
    ts = create_backup(tmp_path)
    backup_path = tmp_path / BACKUP_DIR / ts
    files = list(backup_path.rglob("*"))
    assert files == []
