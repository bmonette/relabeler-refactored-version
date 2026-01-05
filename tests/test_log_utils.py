import os
from pathlib import Path

from log_utils import LogConfig, build_timestamped_log_path, maybe_create_log_path


def test_build_timestamped_log_path_creates_directory(tmp_path, monkeypatch):
    # Make it write to a temp directory instead of your real logs/
    config = LogConfig(directory=str(tmp_path / "logs_test"))

    path = build_timestamped_log_path(config)
    assert os.path.isdir(config.directory)
    assert path.startswith(config.directory)
    assert path.endswith(".log")


def test_maybe_create_log_path_disabled_returns_none(tmp_path):
    config = LogConfig(directory=str(tmp_path / "logs_test"))
    assert maybe_create_log_path(False, config) is None


def test_maybe_create_log_path_enabled_returns_path(tmp_path):
    config = LogConfig(directory=str(tmp_path / "logs_test"))
    p = maybe_create_log_path(True, config)
    assert p is not None
    assert os.path.isdir(config.directory)
