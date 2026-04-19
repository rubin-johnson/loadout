"""CLI entry point for loadout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_validate(args: argparse.Namespace) -> int:
    from loadout.validate import validate_package

    pkg = Path(args.package)
    errors = validate_package(pkg)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Package {pkg} is valid.")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    from loadout.apply import apply_package
    from loadout.paths import get_target_root

    pkg = Path(args.package)
    target = get_target_root(args.target)
    try:
        apply_package(pkg, target, yes=args.yes, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Applied {pkg} to {target}")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from loadout.paths import get_target_root
    from loadout.status import show_status

    target = get_target_root(args.target)
    show_status(target)
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    from loadout.paths import get_target_root
    from loadout.restore import restore_package

    target = get_target_root(args.target)
    try:
        restore_package(target, backup=args.backup, yes=args.yes)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    from loadout.pack import pack
    from loadout.paths import get_target_root

    source = Path(args.source) if args.source else get_target_root()
    output = Path(args.output) if args.output else Path.cwd() / "my-loadout"
    try:
        pack(source, output, yes=args.yes)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    from loadout import __version__

    parser = argparse.ArgumentParser(
        prog="loadout",
        description="Manage Claude Code configuration packages",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # validate
    p_validate = sub.add_parser("validate", help="Validate a package")
    p_validate.add_argument("package", help="Path to package directory")

    # apply
    p_apply = sub.add_parser("apply", help="Apply a package")
    p_apply.add_argument("package", help="Path to package directory")
    p_apply.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")
    p_apply.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    p_apply.add_argument("--dry-run", action="store_true", help="Show what would change, do nothing")

    # status
    p_status = sub.add_parser("status", help="Show current loadout status")
    p_status.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")

    # restore
    p_restore = sub.add_parser("restore", help="Restore previous configuration")
    p_restore.add_argument("--target", default=None, help="Target directory (default: ~/.claude)")
    p_restore.add_argument("--backup", default=None, help="Backup timestamp to restore")
    p_restore.add_argument("--yes", action="store_true", help="Skip confirmation prompts")

    # pack
    p_pack = sub.add_parser("pack", help="Pack current config into a package")
    p_pack.add_argument("--source", default=None, help="Source directory (default: ~/.claude)")
    p_pack.add_argument("--output", default=None, help="Output package directory")
    p_pack.add_argument("--yes", action="store_true", help="Skip confirmation prompts")

    return parser


def main() -> None:
    # Hidden alias: rewrite "capture" to "pack" before argparse sees it
    if len(sys.argv) > 1 and sys.argv[1] == "capture":
        sys.argv[1] = "pack"

    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "validate": cmd_validate,
        "apply": cmd_apply,
        "status": cmd_status,
        "restore": cmd_restore,
        "pack": cmd_pack,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":
    main()
