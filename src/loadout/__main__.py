"""CLI entry point for loadout."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _default_target() -> Path:
    return Path.home() / ".claude"


def cmd_validate(args: argparse.Namespace) -> int:
    from loadout.validate import validate_bundle
    bundle = Path(args.bundle)
    errors = validate_bundle(bundle)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Bundle {bundle} is valid.")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    from loadout.apply import apply_bundle
    bundle = Path(args.bundle)
    target = Path(args.target) if args.target else _default_target()
    try:
        apply_bundle(bundle, target, yes=args.yes, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Applied {bundle} to {target}")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from loadout.status import show_status
    target = Path(args.target) if args.target else _default_target()
    show_status(target)
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    from loadout.restore import restore_bundle
    target = Path(args.target) if args.target else _default_target()
    try:
        restore_bundle(target, backup=args.backup, yes=args.yes)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    from loadout.capture import capture_bundle
    source = Path(args.source) if args.source else _default_target()
    output = Path(args.output)
    try:
        capture_bundle(source, output, yes=args.yes)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loadout",
        description="Manage Claude Code configuration bundles",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # validate
    p_validate = sub.add_parser("validate", help="Validate a bundle")
    p_validate.add_argument("bundle", help="Path to bundle directory")

    # apply
    p_apply = sub.add_parser("apply", help="Apply a bundle")
    p_apply.add_argument("bundle", help="Path to bundle directory")
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

    # capture
    p_capture = sub.add_parser("capture", help="Capture current config as a bundle")
    p_capture.add_argument("--source", default=None, help="Source directory (default: ~/.claude)")
    p_capture.add_argument("--output", required=True, help="Output bundle directory")
    p_capture.add_argument("--yes", action="store_true", help="Skip confirmation prompts")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "validate": cmd_validate,
        "apply": cmd_apply,
        "status": cmd_status,
        "restore": cmd_restore,
        "capture": cmd_capture,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":
    main()
