from loadout.state import STATE_FILENAME, read_state, write_state


def test_read_state_missing_returns_none(tmp_path):
    assert read_state(tmp_path) is None

def test_write_then_read(tmp_path):
    state = {
        "active": "my-loadout",
        "applied_at": "2026-01-01T00:00:00Z",
        "package_path": "/tmp/pkg",
        "manifest_version": "0.1.0",
        "backup": "2026-01-01-000000",
    }
    write_state(tmp_path, state)
    result = read_state(tmp_path)
    assert result == state

def test_write_creates_target_dir(tmp_path):
    nested = tmp_path / "a" / "b"
    write_state(nested, {"active": "x", "applied_at": "t",
                          "package_path": "p", "manifest_version": "1",
                          "backup": "b"})
    assert read_state(nested) is not None

def test_state_file_is_named_correctly(tmp_path):
    write_state(tmp_path, {"active": "x", "applied_at": "t",
                            "package_path": "p", "manifest_version": "1",
                            "backup": "b"})
    assert (tmp_path / STATE_FILENAME).exists()

def test_clear_state(tmp_path):
    from loadout.state import clear_state
    write_state(tmp_path, {"active": "x", "applied_at": "t",
                            "package_path": "p", "manifest_version": "1",
                            "backup": "b"})
    clear_state(tmp_path)
    assert read_state(tmp_path) is None
