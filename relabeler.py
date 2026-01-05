import tkinter
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os

from tkinterdnd2 import TkinterDnD, DND_FILES

from engine import build_rename_plan, RenameOptions
from filesystem import apply_rename_plan, undo_rename_mappings
from validation import validate_inputs
from log_utils import build_timestamped_log_path

# Global variables and settings
file_mappings = []  # Stores (new_path, old_path) for undo functionality.


def browse_folder():
    """
    Opens a folder selection dialog and inserts the selected path
    into the entry_folder_path entry field.
    """
    folder_path = filedialog.askdirectory()
    entry_folder_path.delete(0, tkinter.END)
    entry_folder_path.insert(0, folder_path)


def _build_options_from_ui() -> RenameOptions:
    """
    Build RenameOptions from the UI state (single source of truth).
    """
    pattern = entry_pattern.get()

    new_ext = None
    if change_extension_var.get():
        new_ext = entry_extension.get().strip()

    return RenameOptions(
        pattern=pattern,
        include_date=date_var.get(),
        include_time=time_var.get(),
        change_extension=change_extension_var.get(),
        new_extension=new_ext,
    )


def _set_status(text: str) -> None:
    status_label.config(text=text)
    mainwindow.update_idletasks()


def rename_files():
    """
    Renames all files in the selected folder according to the pattern and options
    provided by the user.
    """
    folder_path = entry_folder_path.get()
    options = _build_options_from_ui()

    errors = validate_inputs(folder_path, options)
    if errors:
        messagebox.showerror("Error", "\n".join(errors))
        return

    # Create a log file path (logic moved out to log_utils)
    log_file_path = build_timestamped_log_path()

    # Build operations via engine (tested)
    try:
        operations = build_rename_plan(folder_path, options)
    except Exception as e:
        messagebox.showerror("Error", f"Error building rename plan: {e}")
        return

    total = len(operations)
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    _set_status("Starting rename...")

    def on_progress(current: int, total: int, op):
        progress_bar["value"] = current
        _set_status(f"Renaming file {current} of {total}: {op.old_name}")

    # Apply plan via filesystem (tested)
    result = apply_rename_plan(
        folder_path,
        operations,
        log_file_path=log_file_path,
        on_progress=on_progress,
    )

    # Save mappings for undo
    file_mappings.clear()
    file_mappings.extend(result.mappings)

    # Final UI state
    if result.errors:
        messagebox.showerror("Error", "Some files failed to rename:\n\n" + "\n".join(result.errors))

    if result.skipped:
        messagebox.showwarning(
            "Warning",
            "The following files were skipped because they already exist:\n\n" + "\n".join(result.skipped)
        )

    _set_status("Renaming complete!")
    messagebox.showinfo("Success", "Rename operation finished!")

    button_undo.config(state="normal" if file_mappings else "disabled")


def preview_files():
    """
    Displays a preview of the renamed files in the listbox.
    Uses the engine (tested) and validation (logic).
    """
    folder_path = entry_folder_path.get()
    options = _build_options_from_ui()

    preview_listbox.delete(0, tkinter.END)

    errors = validate_inputs(folder_path, options)
    if errors:
        messagebox.showerror("Error", "\n".join(errors))
        return

    try:
        operations = build_rename_plan(folder_path, options)
    except Exception as e:
        messagebox.showerror("Error", f"Error generating preview: {e}")
        return

    for op in operations:
        preview_listbox.insert(tkinter.END, f'{op.old_name} "->" {op.new_name}')

    _set_status(f"Preview ready: {len(operations)} file(s).")


def undo_rename():
    """
    Reverts the last rename operation by renaming files back to their original names.
    Uses the filesystem undo function (tested).
    """
    if not file_mappings:
        return

    total = len(file_mappings)
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    _set_status("Starting undo...")

    def on_undo_progress(current: int, total: int, filename: str):
        progress_bar["value"] = current
        _set_status(f"Undoing {current} of {total}: {filename}")

    errors = undo_rename_mappings(file_mappings, on_progress=on_undo_progress)

    if errors:
        messagebox.showerror("Error", "Undo had issues:\n\n" + "\n".join(errors))
        _set_status("Undo completed with errors.")
    else:
        messagebox.showinfo("Success", "Undo successful!")
        _set_status("Undo complete.")

    file_mappings.clear()
    button_undo.config(state="disabled")


def handle_drag_and_drop(event):
    """
    Allows user to drag and drop a folder onto the entry to select it.
    """
    dropped_path = event.data.strip()

    if dropped_path.startswith("{") and dropped_path.endswith("}"):
        dropped_path = dropped_path[1:-1]

    if os.path.isdir(dropped_path):
        entry_folder_path.delete(0, tkinter.END)
        entry_folder_path.insert(0, dropped_path)
        _set_status("Folder selected via drag-and-drop.")
    else:
        messagebox.showerror("Error", "Please drop a valid folder.")


def toggle_extension_entry():
    """
    Toggles the extension entry field based on the state of the checkbox.
    """
    if change_extension_var.get():
        entry_extension.config(state="normal")
    else:
        entry_extension.delete(0, tkinter.END)
        entry_extension.config(state="disabled")


def show_about():
    """
    Displays information about the Relabeler application.
    """
    messagebox.showinfo(
        "About Relabeler",
        "Relabeler Version 1.0\n\nDeveloped by Benoit Monette\n\nA batch file renaming tool with preview, undo, drag-and-drop, and more!"
    )


# Main window setup
mainwindow = TkinterDnD.Tk()
mainwindow.title("Relabeler Version 1.0")
mainwindow.resizable(True, True)
mainwindow.geometry("600x400")
mainwindow.minsize(780, 400)
mainwindow.maxsize(800, 600)

# Boolean variables tied to checkboxes.
date_var = tkinter.BooleanVar()
time_var = tkinter.BooleanVar()
change_extension_var = tkinter.BooleanVar()

# Folder selection widgets
label_select_folder = tkinter.Label(mainwindow, text="Select a folder:")
label_select_folder.grid(row=0, column=0, padx=5, pady=5, sticky="w")

entry_folder_path = tkinter.Entry(mainwindow)
entry_folder_path.grid(row=0, column=1, padx=5, pady=5)
entry_folder_path.drop_target_register(DND_FILES)
entry_folder_path.dnd_bind("<<Drop>>", handle_drag_and_drop)

button_browse = tkinter.Button(mainwindow, text="Browse", command=browse_folder)
button_browse.grid(row=0, column=2, padx=5, pady=5)

checkbox_extension = tkinter.Checkbutton(
    mainwindow,
    text="Change File Extension",
    variable=change_extension_var,
    command=toggle_extension_entry
)
checkbox_extension.grid(row=0, column=3, padx=5, pady=5)

entry_extension = tkinter.Entry(mainwindow, state="disabled")
entry_extension.grid(row=0, column=4, padx=5, pady=5)

# Rename pattern widgets
label_pattern = tkinter.Label(mainwindow, text="Rename pattern (e.g., File_##):")
label_pattern.grid(row=1, column=0, padx=5, pady=5, sticky="w")

entry_pattern = tkinter.Entry(mainwindow)
entry_pattern.grid(row=1, column=1, padx=5, pady=5)

checkbox_date = tkinter.Checkbutton(mainwindow, text="Include Date", variable=date_var)
checkbox_date.grid(row=1, column=2, padx=5, pady=5)

checkbox_time = tkinter.Checkbutton(mainwindow, text="Include Time", variable=time_var)
checkbox_time.grid(row=1, column=3, padx=5, pady=5)

# Preview listbox
label_preview = tkinter.Label(mainwindow, text="Preview of renamed files:")
label_preview.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="w")

preview_listbox = tkinter.Listbox(mainwindow, width=105, height=10)
preview_listbox.grid(row=3, column=0, columnspan=4, padx=5, pady=5)

# Buttons frame
button_frame = tkinter.Frame(mainwindow)
button_frame.grid(row=3, column=4, padx=10, pady=5, sticky="n")

button_preview = tkinter.Button(button_frame, text="Preview", command=preview_files, width=15)
button_preview.pack(pady=5)

button_rename = tkinter.Button(button_frame, text="Rename Files", command=rename_files, width=15)
button_rename.pack(pady=5)

button_undo = tkinter.Button(button_frame, text="Undo", command=undo_rename, state="disabled", width=15)
button_undo.pack(pady=5)

button_about = tkinter.Button(button_frame, text="About", command=show_about, width=15)
button_about.pack(pady=5)

# Progress bar and status label
progress_bar = ttk.Progressbar(mainwindow, orient="horizontal", length=600, mode="determinate")
progress_bar.grid(row=4, column=0, columnspan=5, padx=10, pady=10, sticky="we")

status_label = tkinter.Label(mainwindow, text="")
status_label.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="w")

# Start the application loop
mainwindow.mainloop()
