import argparse
import sys

from loadout.validate import validate_bundle
from loadout.apply import atomic_apply
from loadout.restore import restore_backup
from loadout.capture import capture
from loadout.status import get_status


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="loadout",
        description="Manage Claude Code configuration bundles.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser("validate", help="Validate a loadout bundle structure")
    subparsers.add_parser("apply", help="Apply a loadout bundle to the current environment")
    subparsers.add_parser("restore", help="Restore previous configuration from a backup")
    subparsers.add_parser("capture", help="Capture current configuration as a loadout bundle")
    subparsers.add_parser("status", help="Show what loadout is currently applied")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "validate":
            validate_bundle(None)
        elif args.command == "apply":
            atomic_apply(None)
        elif args.command == "restore":
            restore_backup()
        elif args.command == "capture":
            capture()
        elif args.command == "status":
            get_status()
    except NotImplementedError:
        print(f"loadout {args.command}: not implemented", file=sys.stderr)
        sys.exit(1)
