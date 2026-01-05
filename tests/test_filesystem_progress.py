from engine import RenameOperation
from filesystem import apply_rename_plan


def _create_file(path, text="x"):
    path.write_text(text, encoding="utf-8")


def test_progress_callback_called_for_each_operation(tmp_path):
    _create_file(tmp_path / "a.txt")
    _create_file(tmp_path / "b.txt")

    ops = [
        RenameOperation(old_name="a.txt", new_name="X_1.txt"),
        RenameOperation(old_name="b.txt", new_name="X_2.txt"),
    ]

    calls = []

    def on_progress(current, total, op):
        calls.append((current, total, op.old_name, op.new_name))

    result = apply_rename_plan(str(tmp_path), ops, on_progress=on_progress)

    assert result.errors == []
    assert len(calls) == 2
    assert calls[0][0] == 1 and calls[0][1] == 2
    assert calls[1][0] == 2 and calls[1][1] == 2
