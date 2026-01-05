from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from engine import build_rename_plan, RenameOptions
from filesystem import apply_rename_plan
from validation import validate_inputs
from log_utils import maybe_create_log_path
from relabeler_cli import _save_mappings  # reuse your JSON writer


def extract_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)


def create_zip(src_folder: Path, zip_out: Path) -> None:
    with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file_path in src_folder.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(src_folder)
                z.write(file_path, arcname.as_posix())


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="ZIP-in/ZIP-out file renaming service helper.")
    p.add_argument("zip_in", help="Input zip file containing files to rename.")
    p.add_argument("zip_out", help="Output zip file path.")
    p.add_argument("--pattern", required=True, help='Rename pattern, e.g. "File_##"')
    p.add_argument("--date", action="store_true", help="Append file timestamp date (YYYYMMDD).")
    p.add_argument("--time", action="store_true", help="Append file timestamp time (HHMMSS). Requires --date.")
    p.add_argument("--ext", default=None, help='Change extension, e.g. "jpg" or ".jpg".')
    p.add_argument("--log", action="store_true", help="Write a log file in ./logs/")
    p.add_argument("--dry-run", action="store_true", help="Simulate (no changes).")
    p.add_argument("--mappings-out", default=None, help="Write undo mappings JSON to this path.")
    args = p.parse_args(argv)

    zip_in = Path(args.zip_in)
    zip_out = Path(args.zip_out)

    if not zip_in.exists() or not zip_in.is_file():
        raise SystemExit(f"Input zip not found: {zip_in}")

    options = RenameOptions(
        pattern=args.pattern,
        include_date=bool(args.date),
        include_time=bool(args.time),
        change_extension=(args.ext is not None),
        new_extension=args.ext,
    )

    log_path = maybe_create_log_path(args.log)

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir)
        extract_dir = work / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        extract_zip(zip_in, extract_dir)

        # IMPORTANT: We only rename files in the root of the extracted folder
        # to match your current app behavior (non-recursive).
        folder_path = str(extract_dir)

        errors = validate_inputs(folder_path, options)
        if errors:
            for e in errors:
                print(f"Error: {e}")
            return 2

        ops = build_rename_plan(folder_path, options)
        result = apply_rename_plan(
            folder_path,
            ops,
            log_file_path=log_path,
            dry_run=bool(args.dry_run),
        )

        if not args.dry_run:
            create_zip(extract_dir, zip_out)

        # Save mappings (useful if you want to undo locally later)
        if args.mappings_out and not args.dry_run:
            _save_mappings(args.mappings_out, result.mappings)

        # Summary
        print(f"Planned: {len(ops)}")
        print(f"Renamed: {len(result.renamed)}")
        print(f"Skipped: {len(result.skipped)}")
        print(f"Errors: {len(result.errors)}")
        if result.errors:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
