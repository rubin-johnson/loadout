import subprocess
import sys

from loadout.state import write_state


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL
    )


def test_status_no_state(tmp_path):
    r = _cli("status", "--target", str(tmp_path))
    assert r.returncode == 0
    assert "no loadout" in r.stdout.lower()


def test_status_with_state(tmp_path):
    write_state(
        tmp_path,
        {
            "active": "frugal-v2",
            "applied_at": "2026-01-15T10:30:00Z",
            "package_path": "/home/user/packages/frugal",
            "manifest_version": "0.3.1",
            "backup": "2026-01-15-103000",
        },
    )
    r = _cli("status", "--target", str(tmp_path))
    assert r.returncode == 0
    assert "frugal-v2" in r.stdout
    assert "0.3.1" in r.stdout
    assert "2026-01-15T10:30:00Z" in r.stdout


def test_status_env_var(tmp_path, monkeypatch):
    import os

    write_state(
        tmp_path, {"active": "test", "applied_at": "t", "package_path": "p", "manifest_version": "1", "backup": "b"}
    )
    env = {**os.environ, "LOADOUT_TARGET_ROOT": str(tmp_path)}
    r = subprocess.run([sys.executable, "-m", "loadout", "status"], capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert "test" in r.stdout
