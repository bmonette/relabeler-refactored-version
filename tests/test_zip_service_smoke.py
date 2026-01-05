from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from zip_service import main as zip_main


def _make_zip(zip_path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)


def _list_zip_names(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as z:
        return sorted(z.namelist())


def test_zip_service_renames_and_outputs_zip(tmp_path):
    zip_in = tmp_path / "input.zip"
    zip_out = tmp_path / "output.zip"

    _make_zip(zip_in, {"b.txt": "b", "A.txt": "a"})

    code = zip_main([str(zip_in), str(zip_out), "--pattern", "File_##"])
    assert code == 0
    assert zip_out.exists()

    names = _list_zip_names(zip_out)
    # case-insensitive sort: A then b => 00001 then 00002
    assert names == ["File_00001.txt", "File_00002.txt"]


def test_zip_service_dry_run_does_not_create_output_zip(tmp_path):
    zip_in = tmp_path / "input.zip"
    zip_out = tmp_path / "output.zip"

    _make_zip(zip_in, {"a.txt": "x"})

    code = zip_main([str(zip_in), str(zip_out), "--pattern", "X_##", "--dry-run"])
    assert code == 0
    assert not zip_out.exists()


def test_zip_service_writes_mappings_file(tmp_path):
    zip_in = tmp_path / "input.zip"
    zip_out = tmp_path / "output.zip"
    mappings_out = tmp_path / "undo.json"

    _make_zip(zip_in, {"a.txt": "x", "b.txt": "y"})

    code = zip_main([
        str(zip_in),
        str(zip_out),
        "--pattern",
        "R_##",
        "--mappings-out",
        str(mappings_out),
    ])
    assert code == 0
    assert zip_out.exists()
    assert mappings_out.exists()
