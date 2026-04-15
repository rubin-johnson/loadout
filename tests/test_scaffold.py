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
    for cmd in ("validate", "apply", "restore", "capture", "status"):
        assert cmd in r.stdout


def test_imports():
    pass
