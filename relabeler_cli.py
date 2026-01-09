from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from typing import Any, Optional

from engine import build_rename_plan, RenameOptions
from filesystem import apply_rename_plan, undo_rename_mappings
from validation import validate_inputs
from log_utils import maybe_create_log_path


def _eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def _exit_with_errors(errors: list[str], code: int = 2) -> None:
    for msg in errors:
        _eprint(f"Error: {msg}")
    raise SystemExit(code)


def _options_from_args(args: argparse.Namespace) -> RenameOptions:
    return RenameOptions(
        pattern=args.pattern or "",
        include_date=bool(args.date),
        include_time=bool(args.time),
        change_extension=bool(args.ext is not None),
        new_extension=args.ext,
    )


def _print_preview(operations) -> None:
    for op in operations:
        print(f'{op.old_name} -> {op.new_name}')


def _save_mappings(path: str, mappings: list[tuple[str, str]]) -> None:
    # mappings are (new_path, old_path)
    payload = {
        "version": 1,
        "mappings": [{"new_path": n, "old_path": o} for (n, o) in mappings],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _load_mappings(path: str) -> list[tuple[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or "mappings" not in payload:
        raise ValueError("Invalid mappings file format.")

    mappings = payload["mappings"]
    if not isinstance(mappings, list):
        raise ValueError("Invalid mappings file format (mappings must be a list).")

    out: list[tuple[str, str]] = []
    for item in mappings:
        if not isinstance(item, dict):
            raise ValueError("Invalid mappings file format (mapping item must be an object).")
        new_path = item.get("new_path")
        old_path = item.get("old_path")
        if not isinstance(new_path, str) or not isinstance(old_path, str):
            raise ValueError("Invalid mappings file format (paths must be strings).")
        out.append((new_path, old_path))

    return out


def cmd_preview(args: argparse.Namespace) -> int:
    folder = args.folder
    options = _options_from_args(args)

    errors = validate_inputs(folder, options)
    if errors:
        _exit_with_errors(errors)

    ops = build_rename_plan(folder, options)
    _print_preview(ops)
    return 0


def cmd_rename(args: argparse.Namespace) -> int:
    folder = args.folder
    options = _options_from_args(args)

    errors = validate_inputs(folder, options)
    if errors:
        _exit_with_errors(errors)

    ops = build_rename_plan(folder, options)

    log_path: Optional[str] = maybe_create_log_path(args.log)

    # Apply
    result = apply_rename_plan(
        folder,
        ops,
        log_file_path=log_path,
        dry_run=bool(args.dry_run),
    )

    # Print summary
    print(f"Planned: {len(ops)}")
    print(f"Renamed: {len(result.renamed)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Errors: {len(result.errors)}")

    if result.skipped:
        print("\nSkipped targets (already exist):")
        for s in result.skipped:
            print(f"  - {s}")

    if result.errors:
        print("\nErrors:")
        for e in result.errors:
            print(f"  - {e}")

    # Save undo mappings only when real rename occurred
    if not args.dry_run and args.mappings_out:
        _save_mappings(args.mappings_out, result.mappings)
        print(f"\nUndo mappings saved to: {args.mappings_out}")

    # Return non-zero if errors happened (useful for automation)
    return 1 if result.errors else 0


def cmd_undo(args: argparse.Namespace) -> int:
    mappings_path = args.mappings
    try:
        mappings = _load_mappings(mappings_path)
    except Exception as e:
        _exit_with_errors([f"Failed to load mappings file: {e}"])

    errors = undo_rename_mappings(mappings)

    if errors:
        print("Undo completed with errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Undo successful.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="relabeler",
        description="Relabeler CLI - batch file renaming (preview/rename/undo).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # Common args for preview/rename
    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("folder", help="Folder containing files to rename.")
        sp.add_argument("--pattern", required=True, help='Rename pattern, e.g. "File_##"')
        sp.add_argument("--date", action="store_true", help="Append file timestamp date (YYYYMMDD).")
        sp.add_argument("--time", action="store_true", help="Append file timestamp time (HHMMSS). Requires --date.")
        sp.add_argument("--ext", default=None, help='Change extension, e.g. "jpg" or ".jpg".')

    sp_preview = sub.add_parser("preview", help="Print rename preview (no changes).")
    add_common(sp_preview)
    sp_preview.set_defaults(func=cmd_preview)

    sp_rename = sub.add_parser("rename", help="Apply rename operations.")
    add_common(sp_rename)
    sp_rename.add_argument("--log", action="store_true", help="Write a log file in ./logs/")
    sp_rename.add_argument("--dry-run", action="store_true", help="Simulate (no filesystem changes).")
    sp_rename.add_argument(
        "--mappings-out",
        default="undo_mappings.json",
        help="Where to save undo mappings JSON (rename only).",
    )
    sp_rename.set_defaults(func=cmd_rename)

    sp_undo = sub.add_parser("undo", help="Undo a previous rename using a mappings JSON file.")
    sp_undo.add_argument("mappings", help="Path to mappings JSON produced by rename.")
    sp_undo.set_defaults(func=cmd_undo)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
