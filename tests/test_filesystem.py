import os

from engine import RenameOperation
from filesystem import apply_rename_plan, undo_rename_mappings


def _create_file(path, text="x"):
    path.write_text(text, encoding="utf-8")


def test_apply_rename_plan_renames_files(tmp_path):
    _create_file(tmp_path / "a.txt")
    _create_file(tmp_path / "b.txt")

    ops = [
        RenameOperation(old_name="a.txt", new_name="File_00001.txt"),
        RenameOperation(old_name="b.txt", new_name="File_00002.txt"),
    ]

    result = apply_rename_plan(str(tmp_path), ops)

    assert result.errors == []
    assert result.skipped == []
    assert (tmp_path / "File_00001.txt").exists()
    assert (tmp_path / "File_00002.txt").exists()
    assert not (tmp_path / "a.txt").exists()
    assert not (tmp_path / "b.txt").exists()
    assert len(result.mappings) == 2


def test_apply_rename_plan_skips_when_target_exists(tmp_path):
    _create_file(tmp_path / "a.txt")
    _create_file(tmp_path / "File_00001.txt")  # collision target

    ops = [
        RenameOperation(old_name="a.txt", new_name="File_00001.txt"),
    ]

    result = apply_rename_plan(str(tmp_path), ops)

    assert result.errors == []
    assert result.skipped == ["File_00001.txt"]
    assert (tmp_path / "a.txt").exists()              # original remains
    assert (tmp_path / "File_00001.txt").exists()     # target remains
    assert result.mappings == []


def test_undo_rename_mappings_restores_originals(tmp_path):
    _create_file(tmp_path / "a.txt")
    _create_file(tmp_path / "b.txt")

    ops = [
        RenameOperation(old_name="a.txt", new_name="X_1.txt"),
        RenameOperation(old_name="b.txt", new_name="X_2.txt"),
    ]

    result = apply_rename_plan(str(tmp_path), ops)
    assert result.errors == []
    assert (tmp_path / "X_1.txt").exists()
    assert (tmp_path / "X_2.txt").exists()

    errors = undo_rename_mappings(result.mappings)
    assert errors == []

    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").exists()
    assert not (tmp_path / "X_1.txt").exists()
    assert not (tmp_path / "X_2.txt").exists()
