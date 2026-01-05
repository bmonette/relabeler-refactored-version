# filesystem.py
from __future__ import annotations

import datetime
import os
from dataclasses import dataclass, field
from typing import Optional

from engine import RenameOperation


@dataclass
class ApplyResult:
    renamed: list[tuple[str, str]] = field(default_factory=list)    # (old_name, new_name)
    skipped: list[str] = field(default_factory=list)               # new_name values skipped due to collision
    errors: list[str] = field(default_factory=list)                # error messages
    mappings: list[tuple[str, str]] = field(default_factory=list)  # (new_path, old_path) for undo


def _log_line(log_file_path: Optional[str], message: str) -> None:
    if not log_file_path:
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def apply_rename_plan(
    folder_path: str,
    operations: list[RenameOperation],
    log_file_path: Optional[str] = None,
) -> ApplyResult:
    """
    Applies a rename plan to the filesystem.

    - Skips any operation where the target already exists.
    - Returns mappings suitable for undo: (new_path, old_path).
    - Does NOT raise on per-file errors (collects them instead).
    """
    result = ApplyResult()

    for op in operations:
        old_path = os.path.join(folder_path, op.old_name)
        new_path = os.path.join(folder_path, op.new_name)

        # Safety: old file might be missing (user edited folder mid-run)
        if not os.path.exists(old_path):
            msg = f"Missing source file: {op.old_name}"
            result.errors.append(msg)
            _log_line(log_file_path, f"Error: {msg}")
            continue

        # Skip collisions (matches your current behavior)
        if os.path.exists(new_path):
            result.skipped.append(op.new_name)
            _log_line(log_file_path, f"Skipped (already exists): {op.new_name}")
            continue

        try:
            os.rename(old_path, new_path)
            result.renamed.append((op.old_name, op.new_name))
            result.mappings.append((new_path, old_path))  # new -> old (for undo)
            _log_line(log_file_path, f"Renamed: {op.old_name} -> {op.new_name}")
        except Exception as e:
            msg = f"Error renaming {op.old_name} -> {op.new_name}: {e}"
            result.errors.append(msg)
            _log_line(log_file_path, msg)

    return result


def undo_rename_mappings(mappings: list[tuple[str, str]]) -> list[str]:
    """
    Undo a previous rename using mappings: (new_path, old_path).
    Returns a list of error strings (empty if success).
    """
    errors: list[str] = []

    for new_path, old_path in reversed(mappings):
        try:
            if os.path.exists(new_path):
                os.rename(new_path, old_path)
            else:
                errors.append(f"Missing during undo: {os.path.basename(new_path)}")
        except Exception as e:
            errors.append(f"Error undoing {os.path.basename(new_path)}: {e}")

    return errors
