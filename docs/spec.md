# Script Sausage Unified Script Interface Specification

## 1. Project Overview
- **Objective**: Provide a unified UI with multi-tab functionality to solve the problem of scattered `.py`, `.exe`, `.bat` scripts across multiple projects, making them hard to find and manage.
- **Target OS**: Windows.

## 2. Core Functional Requirements

### 2.1 Tab Management
- **Multi-Tab Mode**: Users can create multiple tabs to categorize and manage scripts.
- **Tab Operations**:
  - **Add**: Create a new blank tab.
  - **Modify/Rename**: Support double-clicking the tab label or right-clicking to open a menu for renaming.
  - **Duplicate**: Completely clone an existing tab (including all scripts and parameter settings inside).
  - **Delete**: Remove the specified tab (also accessible via right-click menu).
  - **Sort**: Support Drag & Drop using the left mouse button to adjust the display order of tabs.
  - **Switch**: In addition to clicking, hovering the mouse over the tab bar and using the "mouse wheel" allows quick switching between tabs.

### 2.2 Script Management
- **Script List**: Manage multiple scripts within each tab. The interface must display the "Name" of the script.
- **Add/Modify Script**:
  - Support using a "File Picker" to specify local file locations.
  - Support direct "text input/editing" of file paths (with monospaced Consolas font and full Undo/Redo).
- **Script Operations**: Users can freely add, delete, and edit scripts in the list.
- **Sort**: Support clicking "Up/Down arrow buttons" to adjust the arrangement of scripts within the tab.
- **List Scrolling**: When the number of scripts exceeds the window height, global mouse wheel scrolling is supported, featuring an intelligent mechanism to avoid scroll conflicts with text input fields and built-in scrollbars.

### 2.3 Parameter Handling
- **Parameter Input Block**: After clicking a script, its parameters can be edited. Each script is equipped with **3 independent text input fields** and **1 `...` (Advanced Edit) button**.
- **Parameter Input Logic**:
  - Text input fields: Allow strings containing spaces, supporting global editing shortcuts like `Ctrl+Z`.
  - `...` Advanced Edit Window: Pops up an independent text editing window. As a foolproof design, whether clicking the save button or closing the window via the top-right `X`, the input content will automatically be returned and trigger a save.
- **Parameter Merging & Protection**: 
  - During execution, the content of the 3 text input fields will be "merged" with the parameters in the `...` editing window as the final input for the script.
  - **Newline Protection**: Newlines inside the advanced editor are permitted for formatting readability. Right before execution, all newlines are internally replaced with spaces to prevent `cmd.exe` from interpreting them as command delimiters, avoiding parameter truncation.
- **Path and Compatibility Handling**:
  - **Environment Variable Expansion**: Supports inputs like `%APPDATA%`, which will be expanded to physical paths via `os.path.expandvars()` before execution.
  - **Windows Standard Parsing**: On Windows, to prevent `shlex` from breaking complex double-quote structures, the system directly converts the base command to a string, appends raw parameters, and hands it over to the underlying `CreateProcess` for the most authentic parsing. Ensures syntax like `--par1 "00"` is passed perfectly.

### 2.4 Execution & Feedback
- **Visual Run Button**: A large run button on the far left of each row dynamically changes to high-tech colors based on the file extension (e.g., Python blue, Batch orange, PS1 purple, etc.).
- **Execute Script**: Clicking the "Run" button directly invokes the script, passing in the pre-edited merged parameters. A 50ms delay is added to prevent Tkinter UI focus locking.
- **Command Confirmation**: After pressing the run button, the hacker-style (green text on black background) log panel at the bottom UI must display the **final Raw Command passed to the Shell**.

### 2.5 State Persistence
- **Zero-Friction Auto-Save**: No need to manually click a save button. Any text field change, sorting change, or checkbox state change automatically overwrites the config file in the background, achieving a zero-friction UX.
- **Save Location**: The configuration file (`ScriptSausage.json`) adopts a "Portable strategy", strictly bound to the project root directory (or the same directory as the packaged `.exe`), ensuring software portability.

### 2.6 Error Handling & Parameter Validation
- **Reject Shell Injection Implementation**:
  - The underlying layer strictly uses `subprocess.Popen(..., shell=False)`. Parameters are passed as a safe array (Linux) or protected string (Windows) to block malicious execution from special characters.
- **File Existence and Extension Validation**:
  - Real-time dynamic checking: When entering a path, if the file doesn't exist, the path text immediately turns "red", and the "Run" button is forcefully disabled (grayed out). If the extension is unknown, a warning is given.
- **Advanced Input Area Syntax Highlighting**:
  - In the `...` `Text` editing area, regular expressions (Regex) are applied in real-time to highlight: Flags starting with `--` or `-` (blue bold), and strings wrapped in `""` or `''` (green).
- **Global Smart Shortcuts**:
  - Intercepts and enhances default Tkinter behaviors, perfectly supporting `Ctrl+C/V/X/A` and a 50-step error-proof history for `Ctrl+Z` (Undo) and `Ctrl+Y` (Redo) across all input fields.
- **Execution State Capture**:
  - If a script execution crashes or throws an error, the main program catches the Exception and logs it to the bottom Debug panel.
  - *(Note: A button to forcibly stop a running script is not currently implemented; it relies on manually closing the independent terminal window for now).*
- **Terminal Output and Encoding Validation**:
  - For Windows environments, the `creationflags=subprocess.CREATE_NEW_CONSOLE` parameter is added to ensure each script runs in a clean, independent new terminal window, avoiding stdout interference.

### 2.7 UI & UX Modernization
- **Bilingual Support (EN/中)**: The application features a real-time, zero-restart toggle button allowing users to switch between English and Traditional Chinese UI instantly using Tkinter's `StringVar` reactive data binding.
- **Modern Typography**: Utilizes `Segoe UI Variable Display` (Windows 11 standard fallback to Segoe UI) for all global UI labels and buttons to ensure a clean, airy, and modern aesthetic. Code input fields and the debug log use `Cascadia Mono` for a professional developer-tool feel.
- **Concise Terminology**: UI labels are designed to be as short and actionable as possible (e.g. `P1:`, `...`, `Rename`) to reduce visual clutter while remaining intuitive.

## 3. UX Flow
1. **Launch Program**: Start via `run.py` or the packaged EXE, automatically reading and restoring state from `ScriptSausage.json` in the same directory.
2. **Setup Script**: Add a script in a specific tab -> load `run_task.bat` via the file picker or input box -> fill in parameter fields -> if needed, click `...` to paste advanced config strings with syntax highlighting.
3. **Drag & Drop Organization**: Click up/down arrows to adjust script order; drag tab labels to adjust horizontal order.
4. **Execute and View**: Click the prominent colored run button on the left -> the log at the bottom displays the full CLI command -> an independent terminal window pops up and begins execution.
5. **Real-time Save**: All actions are instantly saved in the background; you can close the program anytime without fear of data loss.
