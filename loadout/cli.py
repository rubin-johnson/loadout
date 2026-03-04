import argparse
import sys
from pathlib import Path

from loadout.validate import validate_bundle
from loadout.apply import atomic_apply
from loadout.manifest import load_manifest
from loadout.restore import restore_backup
from loadout.capture import capture
from loadout.status import get_status
from loadout import paths


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="loadout",
        description="Manage Claude Code configuration bundles.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    p_validate = subparsers.add_parser("validate", help="Validate a loadout bundle structure")
    p_validate.add_argument("bundle", help="Path to bundle directory")

    p_apply = subparsers.add_parser("apply", help="Apply a loadout bundle to the current environment")
    p_apply.add_argument("bundle", help="Path to bundle directory")
    p_apply.add_argument("--target", metavar="DIR", help="Target directory (overrides LOADOUT_TARGET_ROOT)")
    p_apply.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    subparsers.add_parser("restore", help="Restore previous configuration from a backup")
    subparsers.add_parser("capture", help="Capture current configuration as a loadout bundle")

    status_parser = subparsers.add_parser("status", help="Show what loadout is currently applied")
    status_parser.add_argument("--target", metavar="DIR", help="Target directory (overrides LOADOUT_TARGET_ROOT)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "validate":
            errors = validate_bundle(Path(args.bundle))
            if errors:
                for e in errors:
                    print(e)
                sys.exit(1)
            print("OK")
        elif args.command == "apply":
            bundle_dir = Path(args.bundle)
            target_dir = paths.get_target_root(args.target)
            manifest = load_manifest(bundle_dir)
            atomic_apply(bundle_dir, target_dir, manifest)
        elif args.command == "restore":
            restore_backup()
        elif args.command == "capture":
            capture()
        elif args.command == "status":
            target_dir = paths.get_target_root(args.target)
            state = get_status(target_dir)
            if state is None:
                print("No loadout currently applied.")
            else:
                print(f"Name:    {state['active']}")
                print(f"Version: {state['manifest_version']}")
                print(f"Applied: {state['applied_at']}")
                print(f"Bundle:  {state['bundle_path']}")
    except NotImplementedError:
        print(f"loadout {args.command}: not implemented", file=sys.stderr)
        sys.exit(1)
