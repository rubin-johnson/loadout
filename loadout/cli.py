import argparse
import sys
import pathlib

from loadout.validate import validate_bundle
from loadout.apply import apply_command
from loadout.manifest import load_manifest
from loadout.restore import restore_command
from loadout.capture import capture_command
from loadout.status import get_status
from loadout import paths


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
                    print(e)
                sys.exit(1)
            print("OK")
        elif args.command == "apply":
            bundle_dir = pathlib.Path(args.bundle)
            target_dir = paths.get_target_root(args.target)
            apply_command(bundle_dir, target_dir, yes=args.yes, dry_run=args.dry_run)
        elif args.command == "restore":
            target_dir = paths.get_target_root(args.target)
            restore_command(target_dir, backup_ts=args.backup, yes=args.yes)
        elif args.command == "capture":
            source = pathlib.Path(args.source) if args.source else pathlib.Path.home() / ".claude"
            output = pathlib.Path(args.output) if args.output else pathlib.Path.cwd() / "my-loadout"
            capture_command(
                source,
                output,
                yes=args.yes,
                name=args.name or "my-loadout",
                description=args.description or "",
                version=args.version or "0.0.1",
            )
        elif args.command == "status":
            target_dir = paths.get_target_root(args.target)
            state = get_status(target_dir)
            if state:
                print(state)
            else:
                print("No loadout applied.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
