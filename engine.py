import os
import datetime
from dataclasses import dataclass
from typing import List, Tuple


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
        number = str(index + 1).zfill(5)
        base, ext = os.path.splitext(file_name)

        new_name = options.pattern.replace("##", number)

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
                final_name = f"{new_name}_{date_str}_{time_str}{ext}"
            else:
                final_name = f"{new_name}_{date_str}{ext}"
        else:
            final_name = new_name + ext

        operations.append(
            RenameOperation(
                old_name=file_name,
                new_name=final_name
            )
        )

    return operations
