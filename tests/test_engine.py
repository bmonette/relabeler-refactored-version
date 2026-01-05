import os
import datetime
from types import SimpleNamespace

import pytest

from engine import build_rename_plan, RenameOptions


def _create_files(folder, names):
    for name in names:
        (folder / name).write_text("x", encoding="utf-8")


def test_numbering_and_pattern_replacement(tmp_path):
    _create_files(tmp_path, ["a.txt", "b.txt", "c.txt"])

    options = RenameOptions(
        pattern="File_##",
        include_date=False,
        include_time=False,
        change_extension=False,
        new_extension=None,
    )

    ops = build_rename_plan(str(tmp_path), options)

    assert [op.old_name for op in ops] == ["a.txt", "b.txt", "c.txt"]
    assert [op.new_name for op in ops] == [
        "File_00001.txt",
        "File_00002.txt",
        "File_00003.txt",
    ]


def test_case_insensitive_sort(tmp_path):
    # Intentionally mixed case to verify sorting uses .lower()
    _create_files(tmp_path, ["b.txt", "A.txt", "c.txt"])

    options = RenameOptions(
        pattern="X_##",
        include_date=False,
        include_time=False,
        change_extension=False,
        new_extension=None,
    )

    ops = build_rename_plan(str(tmp_path), options)

    # Sorted case-insensitive: A, b, c
    assert [op.old_name for op in ops] == ["A.txt", "b.txt", "c.txt"]
    assert [op.new_name for op in ops] == [
        "X_00001.txt",
        "X_00002.txt",
        "X_00003.txt",
    ]


def test_change_extension_adds_dot_when_missing(tmp_path):
    _create_files(tmp_path, ["one.JPG", "two.png"])

    options = RenameOptions(
        pattern="Img_##",
        include_date=False,
        include_time=False,
        change_extension=True,
        new_extension="webp",  # missing dot on purpose
    )

    ops = build_rename_plan(str(tmp_path), options)

    assert [op.new_name for op in ops] == [
        "Img_00001.webp",
        "Img_00002.webp",
    ]


def test_change_extension_keeps_dot_when_present(tmp_path):
    _create_files(tmp_path, ["one.txt"])

    options = RenameOptions(
        pattern="Doc_##",
        include_date=False,
        include_time=False,
        change_extension=True,
        new_extension=".md",
    )

    ops = build_rename_plan(str(tmp_path), options)

    assert ops[0].new_name == "Doc_00001.md"


def test_include_date_appends_yyyymmdd(monkeypatch, tmp_path):
    _create_files(tmp_path, ["a.txt"])

    # Freeze time to 2026-01-05 09:08:07 local time
    fixed_dt = datetime.datetime(2026, 1, 5, 9, 8, 7)
    fixed_ts = fixed_dt.timestamp()

    real_stat = os.stat

    def fake_stat(path):
        st = real_stat(path)
        # return an object with everything real + forced st_ctime
        return SimpleNamespace(**{**st.__dict__, "st_ctime": fixed_ts})

    # os.stat returns an os.stat_result, which doesn't have __dict__ on all platforms,
    # so safer approach: just wrap the attribute we use with a simple object.
    # We'll instead monkeypatch os.stat to return a SimpleNamespace with st_ctime only,
    # and let engine ignore other fields.
    def fake_stat_minimal(path):
        return SimpleNamespace(st_ctime=fixed_ts)

    monkeypatch.setattr(os, "stat", fake_stat_minimal)

    options = RenameOptions(
        pattern="File_##",
        include_date=True,
        include_time=False,
        change_extension=False,
        new_extension=None,
    )

    ops = build_rename_plan(str(tmp_path), options)

    assert ops[0].new_name == "File_00001_20260105.txt"


def test_include_date_and_time_appends_yyyymmdd_hhmmss(monkeypatch, tmp_path):
    _create_files(tmp_path, ["a.txt"])

    fixed_dt = datetime.datetime(2026, 1, 5, 9, 8, 7)
    fixed_ts = fixed_dt.timestamp()

    monkeypatch.setattr(os, "stat", lambda path: SimpleNamespace(st_ctime=fixed_ts))

    options = RenameOptions(
        pattern="File_##",
        include_date=True,
        include_time=True,
        change_extension=False,
        new_extension=None,
    )

    ops = build_rename_plan(str(tmp_path), options)

    assert ops[0].new_name == "File_00001_20260105_090807.txt"


def test_ignores_directories(tmp_path):
    _create_files(tmp_path, ["a.txt"])
    (tmp_path / "subfolder").mkdir()
    (tmp_path / "subfolder" / "inside.txt").write_text("x", encoding="utf-8")

    options = RenameOptions(
        pattern="X_##",
        include_date=False,
        include_time=False,
        change_extension=False,
        new_extension=None,
    )

    ops = build_rename_plan(str(tmp_path), options)

    # Only the file in root folder should be included
    assert [op.old_name for op in ops] == ["a.txt"]
    assert [op.new_name for op in ops] == ["X_00001.txt"]
