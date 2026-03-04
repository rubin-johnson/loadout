"""pytest configuration: ensure src/ is on PYTHONPATH for subprocess tests."""
import os
import sys
from pathlib import Path

# Add src/ to PYTHONPATH so subprocess invocations of sys.executable can find
# the loadout package even when sys.executable resolves to the base interpreter.
src = str(Path(__file__).parent / "src")
if src not in sys.path:
    sys.path.insert(0, src)

existing = os.environ.get("PYTHONPATH", "")
if src not in existing.split(os.pathsep):
    os.environ["PYTHONPATH"] = src + (os.pathsep + existing if existing else "")
