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
    from loadout.manifest import Manifest, load_manifest
    from loadout.state import read_state, write_state
    from loadout.backup import create_backup
    from loadout.apply import atomic_apply
    from loadout.restore import restore_command
    from loadout.capture import capture
    from loadout.validate import validate_bundle
    from loadout.secrets import scan_for_secrets
    from loadout.status import get_status
