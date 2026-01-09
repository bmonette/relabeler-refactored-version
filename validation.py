from __future__ import annotations

import os
import re
from typing import List

from engine import RenameOptions


_HASH_RUNS_RE = re.compile(r"(#+)")


def validate_inputs(folder_path: str, options: RenameOptions) -> List[str]:
    """
    Returns a list of human-friendly validation error messages.
    Empty list means inputs are valid.
    """
    errors: List[str] = []

    if not folder_path or not folder_path.strip():
        errors.append("Please select a folder.")
        return errors

    if not os.path.isdir(folder_path):
        errors.append("Selected folder does not exist or is not a folder.")

    if not options.pattern or not options.pattern.strip():
        errors.append("Please enter a rename pattern.")
    else:
        runs = _HASH_RUNS_RE.findall(options.pattern)
        if not runs:
            errors.append("Pattern must include a counter placeholder using # (e.g., Vacation_##).")
        elif len(runs) > 1:
            errors.append("Pattern must contain only one group of # (e.g., Vacation_###).")
        else:
            width = len(runs[0])
            if width < 2 or width > 6:
                errors.append("Counter padding must be between 2 and 6 # characters (## to ######).")

    if options.change_extension:
        if options.new_extension is None or not options.new_extension.strip():
            errors.append("Please enter a new extension (e.g., jpg or .jpg).")

    if options.include_time and not options.include_date:
        errors.append("Include Time requires Include Date (time is based on file timestamp).")

    return errors
