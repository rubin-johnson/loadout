import argparse
import sys
import pathlib

from loadout.validate import validate_bundle
from loadout.apply import atomic_apply
from loadout.restore import restore_backup
from loadout.capture import capture_command
from loadout.status import get_status


def _default_target() -> pathlib.Path:
    return pathlib.Path.home() / ".claude"


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
    p_apply.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")
    p_apply.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    p_apply.add_argument("--dry-run", action="store_true", help="Show what would change without writing")

    p_restore = subparsers.add_parser("restore", help="Restore previous configuration from a backup")
    p_restore.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")
    p_restore.add_argument("--backup", default=None, help="Backup timestamp to restore")
    p_restore.add_argument("--yes", action="store_true", help="Skip confirmation prompts")

    p_capture = subparsers.add_parser("capture", help="Capture current configuration as a loadout bundle")
    p_capture.add_argument("--source", default=None, help="Source directory (default: ~/.claude)")
    p_capture.add_argument("--output", default=None, help="Output bundle directory (default: ./my-loadout)")
    p_capture.add_argument("--yes", action="store_true", help="Skip confirmation prompts, use defaults")
    p_capture.add_argument("--name", default=None, help="Bundle name")
    p_capture.add_argument("--description", default=None, help="Bundle description")
    p_capture.add_argument("--version", default=None, help="Bundle version")

    p_status = subparsers.add_parser("status", help="Show what loadout is currently applied")
    p_status.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "validate":
            errors = validate_bundle(pathlib.Path(args.bundle))
            if errors:
                for e in errors:
                    print(f"ERROR: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"Bundle {args.bundle} is valid.")

        elif args.command == "apply":
            atomic_apply(None)

        elif args.command == "restore":
            restore_backup()

        elif args.command == "capture":
            source = pathlib.Path(args.source) if args.source else _default_target()
            output = pathlib.Path(args.output) if args.output else pathlib.Path.cwd() / "my-loadout"

            if args.yes:
                name = args.name or "my-loadout"
                description = args.description or ""
                version = args.version or "0.0.1"
                author = ""
            else:
                name = args.name or input("Bundle name [my-loadout]: ").strip() or "my-loadout"
                description = args.description or input("Description []: ").strip()
                version = args.version or input("Version [0.0.1]: ").strip() or "0.0.1"
                author = input("Author []: ").strip()

            try:
                capture_command(source, output, yes=args.yes, name=name,
                                description=description, version=version, author=author)
            except ValueError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "status":
            get_status()

    except NotImplementedError:
        print(f"loadout {args.command}: not implemented", file=sys.stderr)
        sys.exit(1)
