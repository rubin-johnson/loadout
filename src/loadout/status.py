"""Status display logic."""
from __future__ import annotations

from pathlib import Path

from loadout.state import read_state


def show_status(target: Path) -> None:
    """Print current loadout status."""
    state = read_state(target)
    if state is None:
        print(f"No loadout applied at {target}")
        return

    print(f"Active loadout: {state.get('active', 'unknown')}")
    print(f"  Version:    {state.get('manifest_version', 'unknown')}")
    print(f"  Applied at: {state.get('applied_at', 'unknown')}")
    print(f"  Bundle:     {state.get('bundle_path', 'unknown')}")
    print(f"  Backup:     {state.get('backup', 'none')}")

get_status = show_status
