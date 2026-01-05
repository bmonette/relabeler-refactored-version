import pytest

from engine import RenameOptions
from validation import validate_inputs


def _opts(**overrides):
    base = dict(
        pattern="File_##",
        include_date=False,
        include_time=False,
        change_extension=False,
        new_extension=None,
    )
    base.update(overrides)
    return RenameOptions(**base)


def test_requires_folder():
    errors = validate_inputs("", _opts())
    assert "Please select a folder." in errors


def test_requires_pattern(tmp_path):
    errors = validate_inputs(str(tmp_path), _opts(pattern=""))
    assert "Please enter a rename pattern." in errors


def test_extension_required_when_change_extension_enabled(tmp_path):
    errors = validate_inputs(str(tmp_path), _opts(change_extension=True, new_extension=""))
    assert "Please enter a new extension (e.g., jpg or .jpg)." in errors


def test_time_requires_date(tmp_path):
    errors = validate_inputs(str(tmp_path), _opts(include_time=True, include_date=False))
    assert "Include Time requires Include Date (time is based on file timestamp)." in errors


def test_valid_inputs_ok(tmp_path):
    errors = validate_inputs(str(tmp_path), _opts())
    assert errors == []
