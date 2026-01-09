from __future__ import annotations

import json
from pathlib import Path

import pytest

from relabeler_cli import main


def _create_files(folder: Path, names: list[str]) -> None:
    for name in names:
        (folder / name).write_text("x", encoding="utf-8")


def test_cli_preview_prints_plan(tmp_path, capsys):
    _create_files(tmp_path, ["b.txt", "A.txt"])

    code = main(["preview", str(tmp_path), "--pattern", "File_#####"])
    assert code == 0

    out = capsys.readouterr().out.strip().splitlines()
    # Sorted case-insensitive: A then b
    assert out[0].endswith("A.txt -> File_00001.txt")
    assert out[1].endswith("b.txt -> File_00002.txt")


def test_cli_rename_dry_run_does_not_change_files(tmp_path, capsys):
    _create_files(tmp_path, ["a.txt", "b.txt"])

    code = main(["rename", str(tmp_path), "--pattern", "X_##", "--dry-run"])
    # dry-run should still be successful
    assert code == 0

    # Files should remain unchanged
    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").exists()
    assert not (tmp_path / "X_00001.txt").exists()
    assert not (tmp_path / "X_00002.txt").exists()

    out = capsys.readouterr().out
    assert "Planned:" in out
    assert "Renamed:" in out


def test_cli_rename_writes_mappings_and_undo_restores(tmp_path, capsys):
    _create_files(tmp_path, ["a.txt", "b.txt"])

    mappings_path = tmp_path / "undo.json"

    code = main([
        "rename",
        str(tmp_path),
        "--pattern",
        "R_#####",
        "--mappings-out",
        str(mappings_path),
    ])
    # rename should succeed
    assert code == 0

    # Renamed files exist
    assert (tmp_path / "R_00001.txt").exists()
    assert (tmp_path / "R_00002.txt").exists()
    assert not (tmp_path / "a.txt").exists()
    assert not (tmp_path / "b.txt").exists()

    # Mappings file exists and looks sane
    assert mappings_path.exists()
    payload = json.loads(mappings_path.read_text(encoding="utf-8"))
    assert payload.get("version") == 1
    assert isinstance(payload.get("mappings"), list)
    assert len(payload["mappings"]) == 2

    capsys.readouterr()  # clear output

    # Undo
    code = main(["undo", str(mappings_path)])
    assert code == 0

    # Originals restored
    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").exists()
    assert not (tmp_path / "R_00001.txt").exists()
    assert not (tmp_path / "R_00002.txt").exists()


def test_cli_validation_errors_return_nonzero(tmp_path, capsys):
    _create_files(tmp_path, ["a.txt"])

    with pytest.raises(SystemExit) as exc:
        main(["preview", str(tmp_path), "--pattern", "X_##", "--time"])

    assert exc.value.code == 2

    err = capsys.readouterr().err
    assert "Include Time requires Include Date" in err
