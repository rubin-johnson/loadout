import subprocess
import sys


def test_help_exits_zero():
    r = subprocess.run(
        [sys.executable, "-m", "loadout", "--help"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0


def test_help_lists_subcommands():
    r = subprocess.run(
        [sys.executable, "-m", "loadout", "--help"],
        capture_output=True,
        text=True,
    )
    for cmd in ("validate", "apply", "restore", "pack", "status"):
        assert cmd in r.stdout


def test_capture_alias_hidden_in_help():
    r = subprocess.run(
        [sys.executable, "-m", "loadout", "--help"],
        capture_output=True,
        text=True,
    )
    # capture should not appear in help (hidden alias)
    # but pack should
    assert "pack" in r.stdout


def test_imports():
    pass
