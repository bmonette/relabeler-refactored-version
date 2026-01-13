# Relabeler

Relabeler is a robust file renaming toolkit built in Python.
It supports previewing rename operations, batch renaming, undoing changes, logging, and ZIP-based workflows.

What started as a simple script has been refactored into a fully tested, modular application suitable for real-world use and paid services.

---

## Features

- Batch file renaming with preview
- Custom rename patterns with configurable numbering
- Date and time suffixes based on file timestamps
- Optional extension changes
- Undo support via mappings file
- Detailed logging
- CLI interface
- ZIP-in / ZIP-out service mode
- Comprehensive test coverage (pytest)

---

## Rename Pattern Syntax

Relabeler uses `#` characters as a counter placeholder.

The number of `#` defines the zero-padding width:

| Pattern | Result |
|-------|--------|
| `File_##` | `File_01` |
| `File_###` | `File_001` |
| `File_#####` | `File_00001` |

Examples:
- `Vacation_###` → `Vacation_001.jpg`
- `IMG_#####_edited` → `IMG_00012_edited.png`

Rules:
- Exactly one group of `#` is allowed
- Padding width must be between 2 and 6

---

## CLI Usage

Preview a rename plan:
```bash
python relabeler_cli.py preview /path/to/folder --pattern "File_#####"
```

Rename files:
```bash
python relabeler_cli.py rename /path/to/folder --pattern "File_###"
```

Include date and time:
```bash
python relabeler_cli.py rename /path/to/folder \
  --pattern "Photo_###" \
  --date \
  --time
```

Change file extension:
```bash
python relabeler_cli.py rename /path/to/folder \
  --pattern "Image_###" \
  --ext jpg
```

Save undo mappings:
```bash
python relabeler_cli.py rename /path/to/folder \
  --pattern "Doc_###" \
  --mappings-out undo.json
```

Undo a rename:
```bash
python relabeler_cli.py undo /path/to/folder --mappings undo.json
```

---

## ZIP Service Mode

Relabeler can operate as a ZIP-in / ZIP-out service.

```bash
python zip_service.py input.zip output.zip --pattern "File_#####"
```

Options:
- --pattern rename pattern
- --date, --time
- --ext change extension
- --log enable logging
- --dry-run
- --mappings-out undo.json

---

## Logging

When enabled, logs are written to:
./logs/

---

## Project Structure

relabeler-refactored-version/
├── engine.py
├── filesystem.py
├── validation.py
├── log_utils.py
├── relabeler_cli.py
├── zip_service.py
├── tests/
└── README.md

---

## Testing

Run the full test suite:
```bash
pytest -q
```

---

## Requirements

- Python 3.10+
- pytest (for testing)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Status

Relabeler is production-ready and suitable for real-world file renaming workflows.

---

## License

Private / internal use (adjust as needed).
