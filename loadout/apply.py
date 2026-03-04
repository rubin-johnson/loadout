from __future__ import annotations

import pathlib
import shutil
import tempfile

from loadout.manifest import Manifest


def atomic_apply(
    bundle_dir: pathlib.Path,
    target_dir: pathlib.Path,
    manifest: Manifest,
) -> None:
    """Write bundle files to target_dir using a temp-dir-then-rename strategy.

    Files not listed in manifest.targets are left untouched.
    If any shutil.move raises, already-moved files are rolled back.
    """

    def resolve_dest(dest: str) -> pathlib.Path:
        if dest.startswith("~/") or dest == "~":
            rel = dest[2:] if dest.startswith("~/") else ""
            return target_dir / rel
        return target_dir / dest

    staging = pathlib.Path(tempfile.mkdtemp(dir=target_dir.parent))
    try:
        for entry in manifest.targets:
            src = bundle_dir / entry.path
            dst = staging / entry.path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        moved: list[tuple[pathlib.Path, pathlib.Path]] = []
        try:
            for entry in manifest.targets:
                staged = staging / entry.path
                final = resolve_dest(entry.dest)
                final.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staged), str(final))
                moved.append((staged, final))
        except Exception:
            for _, dest_path in reversed(moved):
                if dest_path.exists():
                    dest_path.unlink()
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
