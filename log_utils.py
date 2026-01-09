from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogConfig:
    directory: str = "logs"
    prefix: str = "log_file_"
    extension: str = ".log"


def ensure_log_dir(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


def build_timestamped_log_path(config: LogConfig = LogConfig()) -> str:
    """
    Creates logs/ if needed and returns a timestamped log file path.
    Example: logs/log_file_20260105_093012.log
    """
    ensure_log_dir(config.directory)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{config.prefix}{ts}{config.extension}"
    return os.path.join(config.directory, filename)


def maybe_create_log_path(enabled: bool, config: LogConfig = LogConfig()) -> Optional[str]:
    """
    Convenience helper: if enabled is False, returns None.
    If True, returns a timestamped log file path.
    """
    if not enabled:
        return None
    return build_timestamped_log_path(config)
