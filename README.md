# ScriptSausage

ScriptSausage is a cross-platform script management and execution tool built with Python and Tkinter. It helps you centrally manage and execute various scripts (`.py`, `.bat`, `.cmd`, `.ps1`, `.exe`) in a single interface, with support for dynamic parameter configuration.

## Example use cases
- Running repetitive local scripts without remembering commands
- Managing small personal utilities in one place
- Quickly testing scripts with different parameters

## Project Structure

```
ScriptSausage/
├── scriptsausage/           # Main application package
│   ├── main.py              # Core UI and execution logic
│   └── ScriptSausage.json   # Auto-saved configuration file (generated after execution)
├── tests/                   # Testing and experimental scripts
│   ├── fixtures/            # Mock scripts for testing (.bat, .py)
│   └── test_*.py            # Underlying experimental scripts for POSIX parsing, Undo/Redo, etc.
├── docs/                    # Project documentation
│   └── spec.md              # Requirements and architecture specification
├── run.py                   # Application entry point
├── .gitignore               # Ignored temporary and compiled files
└── README.md                # Project description
```

## Features
- **Centralized Management**: Manage a large number of scripts through Notebook tabs, supporting mouse wheel scrolling for quick tab switching.
- **Multi-Environment Support**: Automatically identifies `.py`, `.bat`, `.ps1`, and `.exe` files and executes them in independent terminal windows.
- **Visuals and Error Prevention**:
  - A modern UI that dynamically changes the color of the "Run" button based on the file extension.
  - If a path does not exist, it will automatically be highlighted in red, and the run button will be disabled.
- **Robust Shortcut Support**: Global `Ctrl+C/V/X` support for all input fields, along with a 50-step error-proof history for `Ctrl+Z` (Undo) and `Ctrl+Y` (Redo).
- **Advanced Parameter Highlighting**: The advanced editing window features built-in Regex syntax highlighting, automatically coloring `--flags` and `"strings"`.
- **Zero-Friction Auto-Save**: No manual clicking required. Any typing or configuration changes are automatically and silently saved to `ScriptSausage.json` in the background (portable design).

## How to Run
Please ensure that Python 3.11 or above is installed. Execute the following in the project root directory:
```bash
python run.py
```
