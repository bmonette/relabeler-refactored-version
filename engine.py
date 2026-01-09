import os
import datetime
import re
from dataclasses import dataclass
from typing import List


_HASH_RUN_RE = re.compile(r"(#+)")


@dataclass
class RenameOptions:
    pattern: str
    include_date: bool
    include_time: bool
    change_extension: bool
    new_extension: str | None


@dataclass
class RenameOperation:
    old_name: str
    new_name: str


def _apply_counter_pattern(pattern: str, counter: int) -> str:
    """
    Replace the first run of # with a zero-padded counter.
    Example:
      "Vacation_##"    + 1 -> "Vacation_01"
      "Vacation_###"   + 1 -> "Vacation_001"
      "Vacation_####"  + 1 -> "Vacation_0001"
    """
    match = _HASH_RUN_RE.search(pattern)
    if not match:
        raise ValueError("Pattern must contain at least one '#' group (e.g., Vacation_###).")

    run = match.group(1)
    width = len(run)
    number = f"{counter:0{width}d}"

    start, end = match.span(1)
    return pattern[:start] + number + pattern[end:]


def build_rename_plan(
    folder_path: str,
    options: RenameOptions,
) -> List[RenameOperation]:
    files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    files.sort(key=lambda s: s.lower())

    operations: List[RenameOperation] = []

    for index, file_name in enumerate(files):
        base, ext = os.path.splitext(file_name)

        # Counter is 1-based
        new_base = _apply_counter_pattern(options.pattern, index + 1)

        if options.change_extension and options.new_extension:
            ext = options.new_extension
            if not ext.startswith("."):
                ext = "." + ext

        if options.include_date:
            stats = os.stat(os.path.join(folder_path, file_name))
            created = datetime.datetime.fromtimestamp(stats.st_ctime)
            date_str = created.strftime("%Y%m%d")
            time_str = created.strftime("%H%M%S")

            if options.include_time:
                final_name = f"{new_base}_{date_str}_{time_str}{ext}"
            else:
                final_name = f"{new_base}_{date_str}{ext}"
        else:
            final_name = new_base + ext

        operations.append(
            RenameOperation(
                old_name=file_name,
                new_name=final_name
            )
        )

    return operations
