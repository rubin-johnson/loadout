from __future__ import annotations

import datetime
import pathlib
import shutil
import sys
import tempfile

from loadout.manifest import Manifest, load_manifest
from loadout.state import read_state, write_state
from loadout.validate import validate_bundle


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


def apply_command(
    bundle_dir: pathlib.Path,
    target_dir: pathlib.Path,
    yes: bool,
    dry_run: bool,
) -> None:
    """Orchestrate validate → idempotency check → prompt → backup → apply → state."""
    from loadout.backup import create_backup

    errors = validate_bundle(bundle_dir)
    if errors:
        raise ValueError("Bundle validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    manifest = load_manifest(bundle_dir)

    state = read_state(target_dir)
    if (
        state is not None
        and state.get("active") == manifest.name
        and state.get("manifest_version") == manifest.version
    ):
        print("Already applied.")
        return

    if dry_run:
        for entry in manifest.targets:
            dest = target_dir / entry.dest
            tag = "[OVERWRITE]" if dest.exists() else "[CREATE]"
            print(f"{tag} {entry.dest}")
        return

    if sys.stdin.isatty() and not yes:
        would_overwrite = any((target_dir / e.dest).exists() for e in manifest.targets)
        if would_overwrite:
            ans = input("Overwrite existing files? [y/N] ")
            if ans.strip().lower() not in ("y", "yes"):
                print("Aborted.")
                return

    target_dir.mkdir(parents=True, exist_ok=True)
    ts = create_backup(target_dir)
    atomic_apply(bundle_dir, target_dir, manifest)
    write_state(target_dir, {
        "active": manifest.name,
        "manifest_version": manifest.version,
        "backup": ts,
        "bundle_path": str(bundle_dir.resolve()),
        "applied_at": datetime.datetime.utcnow().isoformat() + "Z",
    })
