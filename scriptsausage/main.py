import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
import os
import subprocess
import shlex
import threading
import sys
import datetime

if getattr(sys, 'frozen', False):
    # When packaged as .exe, place in the same folder as .exe (portable mode)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # In development mode, place in the project root directory (next to run.py)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, "ScriptSausage.json")

def make_text_widgets_smart(root):
    """Bind Undo/Redo and clipboard shortcuts for global Entry and Text widgets"""
    def do_copy(event):
        try:
            event.widget.clipboard_clear()
            event.widget.clipboard_append(event.widget.selection_get())
        except tk.TclError: pass
        return "break"
        
    def do_cut(event):
        try:
            event.widget.clipboard_clear()
            event.widget.clipboard_append(event.widget.selection_get())
            if isinstance(event.widget, tk.Text):
                event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: pass
        return "break"
        
    def do_paste(event):
        try:
            text = event.widget.clipboard_get()
            if isinstance(event.widget, tk.Text):
                if event.widget.tag_ranges("sel"):
                    event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                event.widget.insert(tk.INSERT, text)
            else:
                if event.widget.select_present():
                    event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                event.widget.insert(tk.INSERT, text)
        except tk.TclError: pass
        return "break"
        
    def do_select_all(event):
        if isinstance(event.widget, tk.Text):
            event.widget.tag_add(tk.SEL, "1.0", tk.END)
            event.widget.mark_set(tk.INSERT, "1.0")
            event.widget.see(tk.INSERT)
        else:
            event.widget.select_range(0, tk.END)
        return "break"

    for cls in ('Entry', 'TEntry', 'Text'):
        root.bind_class(cls, "<Control-c>", do_copy)
        root.bind_class(cls, "<Control-C>", do_copy)
        root.bind_class(cls, "<Control-x>", do_cut)
        root.bind_class(cls, "<Control-X>", do_cut)
        root.bind_class(cls, "<Control-v>", do_paste)
        root.bind_class(cls, "<Control-V>", do_paste)
        root.bind_class(cls, "<Control-a>", do_select_all)
        root.bind_class(cls, "<Control-A>", do_select_all)

    def on_entry_key(event):
        w = event.widget
        if not hasattr(w, '_undo_stack'):
            w._undo_stack = [w.get()]
            w._redo_stack = []
            w._last_val = w.get()
            
        current = w.get()
        if current != w._last_val:
            w._undo_stack.append(current)
            if len(w._undo_stack) > 50:
                w._undo_stack.pop(0)
            w._redo_stack.clear()
            w._last_val = current
            
    def do_entry_undo(event):
        w = event.widget
        if hasattr(w, '_undo_stack') and len(w._undo_stack) > 1:
            w._redo_stack.append(w._undo_stack.pop())
            val = w._undo_stack[-1]
            w.delete(0, tk.END)
            w.insert(0, val)
            w._last_val = val
        return "break"
        
    def do_entry_redo(event):
        w = event.widget
        if hasattr(w, '_redo_stack') and w._redo_stack:
            val = w._redo_stack.pop()
            w._undo_stack.append(val)
            w.delete(0, tk.END)
            w.insert(0, val)
            w._last_val = val
        return "break"

    for cls in ('Entry', 'TEntry'):
        root.bind_class(cls, "<KeyRelease>", on_entry_key, add="+")
        root.bind_class(cls, "<Control-z>", do_entry_undo)
        root.bind_class(cls, "<Control-Z>", do_entry_undo)
        root.bind_class(cls, "<Control-y>", do_entry_redo)
        root.bind_class(cls, "<Control-Y>", do_entry_redo)
        
    def enable_text_undo(event):
        try:
            if not event.widget.cget("undo"):
                event.widget.config(undo=True, autoseparators=True, maxundo=50)
        except tk.TclError: pass
    root.bind_class("Text", "<FocusIn>", enable_text_undo)
    
    def do_text_undo(event):
        try: event.widget.edit_undo()
        except tk.TclError: pass
        return "break"
        
    def do_text_redo(event):
        try: event.widget.edit_redo()
        except tk.TclError: pass
        return "break"
        
    root.bind_class("Text", "<Control-z>", do_text_undo)
    root.bind_class("Text", "<Control-Z>", do_text_undo)
    root.bind_class("Text", "<Control-y>", do_text_redo)
    root.bind_class("Text", "<Control-Y>", do_text_redo)

import re

class AdvancedParamDialog(tk.Toplevel):
    def __init__(self, parent, initial_text, callback, app):
        super().__init__(parent)
        self.title(app.lang_vars["adv_title"].get())
        self.geometry("400x300")
        self.callback = callback
        
        self.text = tk.Text(self, wrap=tk.WORD, font=("Cascadia Mono", 11))
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text.insert(tk.END, initial_text)
        
        self.text.tag_config("flag", foreground="#0277bd", font=("Cascadia Mono", 11, "bold"))
        self.text.tag_config("string", foreground="#2e7d32")
        
        self.text.bind("<KeyRelease>", self.highlight_syntax)
        self.highlight_syntax()

        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, textvariable=app.lang_vars["save"], command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, textvariable=app.lang_vars["cancel"], command=self.destroy).pack(side=tk.RIGHT)
        
        self.transient(parent)
        self.grab_set()
        
        self.protocol("WM_DELETE_WINDOW", self.save)

    def highlight_syntax(self, event=None):
        self.text.tag_remove("flag", "1.0", tk.END)
        self.text.tag_remove("string", "1.0", tk.END)
        
        content = self.text.get("1.0", tk.END)
        for match in re.finditer(r'(^|\s)(-[a-zA-Z0-9_-]+)', content):
            start = f"1.0 + {match.start(2)} chars"
            end = f"1.0 + {match.end(2)} chars"
            self.text.tag_add("flag", start, end)
            
        for match in re.finditer(r'("[^"]*"|\'[^\']*\')', content):
            start = f"1.0 + {match.start(1)} chars"
            end = f"1.0 + {match.end(1)} chars"
            self.text.tag_add("string", start, end)

    def save(self):
        self.callback(self.text.get("1.0", tk.END).strip())
        self.destroy()

class ScriptRow(ttk.Frame):
    def __init__(self, parent, app, data=None):
        super().__init__(parent)
        self.app = app
        self.data = data or {"name": "New Script", "path": "", "p1": "", "p2": "", "p3": "", "adv_p": "", "pause": False}
        
        self.adv_param_text = self.data.get("adv_p", "")
        
        # Grid layout
        self.grid_columnconfigure(5, weight=1) # Let the path column stretch
        
        # Col 0: Up/Down
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.grid(row=0, column=0, rowspan=2, padx=1, pady=0)
        ttk.Button(ctrl_frame, text="▲", width=2, command=self.move_up).pack()
        ttk.Button(ctrl_frame, text="▼", width=2, command=self.move_down).pack()
        
        # Col 1: Big Run Button
        self.run_btn = ttk.Button(self, textvariable=self.app.lang_vars["run"], command=self.run_script, width=8)
        self.run_btn.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(2, 5), pady=2, ipadx=2, ipady=8)
        
        # Row 0, Col 2-7
        ttk.Label(self, textvariable=self.app.lang_vars["name"]).grid(row=0, column=2, sticky="e", padx=(2,1))
        self.name_var = tk.StringVar(value=self.data.get("name", ""))
        ttk.Entry(self, textvariable=self.name_var, width=15).grid(row=0, column=3, sticky="w", padx=1, pady=1)
        
        ttk.Label(self, textvariable=self.app.lang_vars["path"]).grid(row=0, column=4, sticky="e", padx=(2,1))
        self.path_var = tk.StringVar(value=self.data.get("path", ""))
        self.path_entry = ttk.Entry(self, textvariable=self.path_var, font=("Cascadia Mono", 10))
        self.path_entry.grid(row=0, column=5, sticky="we", padx=1, pady=1)
        
        ttk.Button(self, textvariable=self.app.lang_vars["browse"], width=8, command=self.browse_file).grid(row=0, column=6, padx=1, pady=1)
        ttk.Button(self, textvariable=self.app.lang_vars["delete"], width=6, command=self.delete_self).grid(row=0, column=7, padx=(5,1), pady=1)
        
        # Row 1, Col 2-7
        params_frame = ttk.Frame(self)
        params_frame.grid(row=1, column=2, columnspan=4, sticky="w", pady=0)
        
        ttk.Label(params_frame, textvariable=self.app.lang_vars["p1"]).pack(side=tk.LEFT, padx=(2,1))
        self.p1_var = tk.StringVar(value=self.data.get("p1", ""))
        ttk.Entry(params_frame, textvariable=self.p1_var, width=12, font=("Cascadia Mono", 10)).pack(side=tk.LEFT, padx=1)
        
        ttk.Label(params_frame, textvariable=self.app.lang_vars["p2"]).pack(side=tk.LEFT, padx=(2,1))
        self.p2_var = tk.StringVar(value=self.data.get("p2", ""))
        ttk.Entry(params_frame, textvariable=self.p2_var, width=12, font=("Cascadia Mono", 10)).pack(side=tk.LEFT, padx=1)
        
        ttk.Label(params_frame, textvariable=self.app.lang_vars["p3"]).pack(side=tk.LEFT, padx=(2,1))
        self.p3_var = tk.StringVar(value=self.data.get("p3", ""))
        ttk.Entry(params_frame, textvariable=self.p3_var, width=12, font=("Cascadia Mono", 10)).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(params_frame, textvariable=self.app.lang_vars["adv"], width=8, command=self.open_adv_params).pack(side=tk.LEFT, padx=5)
        
        action_frame = ttk.Frame(self)
        action_frame.grid(row=1, column=6, columnspan=2, sticky="e", pady=0)
        
        self.pause_var = tk.BooleanVar(value=self.data.get("pause", False))
        ttk.Checkbutton(action_frame, textvariable=self.app.lang_vars["keep"], variable=self.pause_var, command=self.app.save_state).pack(side=tk.LEFT, padx=2)
        
        # Add a separator for better visuals
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=8, sticky="we", pady=1)

        self.pack(fill=tk.X, pady=1, padx=2)

        self.name_var.trace_add("write", lambda *args: self.app.save_state())
        self.path_var.trace_add("write", lambda *args: self.app.save_state())
        self.path_var.trace_add("write", self.update_run_btn_state)
        self.p1_var.trace_add("write", lambda *args: self.app.save_state())
        self.p2_var.trace_add("write", lambda *args: self.app.save_state())
        self.p3_var.trace_add("write", lambda *args: self.app.save_state())
        
        self.update_run_btn_state()

    def update_run_btn_state(self, *args):
        path = self.path_var.get().strip()
        expanded_path = os.path.expandvars(path)
        
        if not expanded_path:
            self.run_btn.config(state=tk.DISABLED, style="DefaultRun.TButton")
            self.path_entry.config(foreground="")
        elif not os.path.exists(expanded_path):
            self.run_btn.config(state=tk.DISABLED, style="DefaultRun.TButton")
            self.path_entry.config(foreground="red")
        else:
            ext = os.path.splitext(expanded_path)[1].lower()
            if ext == ".py":
                self.run_btn.config(state=tk.NORMAL, style="Py.TButton")
            elif ext in [".bat", ".cmd"]:
                self.run_btn.config(state=tk.NORMAL, style="Bat.TButton")
            elif ext == ".ps1":
                self.run_btn.config(state=tk.NORMAL, style="Ps1.TButton")
            elif ext == ".exe":
                self.run_btn.config(state=tk.NORMAL, style="Exe.TButton")
            else:
                self.run_btn.config(state=tk.NORMAL, style="DefaultRun.TButton")
            self.path_entry.config(foreground="")

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.path_var.set(os.path.normpath(path))

    def open_adv_params(self):
        def save_adv(text):
            self.adv_param_text = text
            self.app.save_state()
        AdvancedParamDialog(self, self.adv_param_text, save_adv, self.app)

    def delete_self(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this script?"):
            self.destroy()
            self.app.save_state()

    def move_up(self):
        siblings = self.master.pack_slaves()
        idx = siblings.index(self)
        if idx > 0:
            siblings[idx-1].pack(before=self)
            self.pack(before=siblings[idx-1])
            self.app.save_state()

    def move_down(self):
        siblings = self.master.pack_slaves()
        idx = siblings.index(self)
        if idx < len(siblings) - 1:
            siblings[idx+1].pack(before=self)
            self.pack(after=siblings[idx+1])
            self.app.save_state()

    def get_data(self):
        return {
            "name": self.name_var.get(),
            "path": self.path_var.get(),
            "p1": self.p1_var.get(),
            "p2": self.p2_var.get(),
            "p3": self.p3_var.get(),
            "adv_p": self.adv_param_text,
            "pause": self.pause_var.get()
        }

    def run_script(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Script path not specified")
            return
        
        path = os.path.expandvars(path)
        
        if not os.path.exists(path):
            messagebox.showerror("Error", f"File not found: {path}")
            return
            
        ext = os.path.splitext(path)[1].lower()
        cmd_list = []
        
        pause = self.pause_var.get()
        if pause and os.name == 'nt':
            cmd_list.extend(["cmd.exe", "/k"])
            
        if ext == ".py":
            cmd_list.append(self.app.py_interpreter_var.get() or "python")
        elif ext in [".bat", ".cmd"]:
            if not (pause and os.name == 'nt'):
                cmd_list.extend(["cmd.exe", "/c"])
        elif ext == ".ps1":
            cmd_list.extend(["powershell", "-ExecutionPolicy", "Bypass", "-File"])
        elif ext != ".exe":
            messagebox.showwarning("Warning", f"Unknown extension: {ext}, will attempt to run directly")
            
        cmd_list.append(path)
        
        # 避免進階編輯器中的換行符號截斷 cmd.exe 的指令，將所有換行替換為空白 (Convert newlines to spaces to prevent command truncation)
        adv_p_safe = self.adv_param_text.replace('\n', ' ')
        params_str = f"{self.p1_var.get()} {self.p2_var.get()} {self.p3_var.get()} {adv_p_safe}".strip()
        params_str = os.path.expandvars(params_str)
        
        if os.name == 'nt':
            # Windows standard solution: synthesize command directly as string to avoid POSIX conversion breaking quotes
            base_cmd_str = subprocess.list2cmdline(cmd_list)
            final_cmd = f"{base_cmd_str} {params_str}".strip()
        else:
            # Linux/Mac standard solution: use shlex.split to parse args into a list
            try:
                if params_str:
                    args = shlex.split(params_str, posix=True)
                    cmd_list.extend(args)
                final_cmd = cmd_list
            except ValueError as e:
                messagebox.showerror("Parse Error", f"Mismatched quotes in parameters: {e}\nPlease check if you missed a double quote.")
                return

        # Delay execution by 50ms to prevent Tkinter button getting stuck in pressed state
        self.after(50, lambda: self.app.show_log_and_run(final_cmd))

class ScriptTab(ttk.Frame):
    def __init__(self, parent, app, data=None):
        super().__init__(parent)
        self.app = app
        self.data = data or {"name": "New Tab", "scripts": []}
        
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(side="top", fill="x", pady=2)
        ttk.Button(ctrl_frame, textvariable=self.app.lang_vars["script_add"], command=self.add_script).pack(side="left", padx=5)
        
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for s_data in self.data.get("scripts", []):
            ScriptRow(self.scrollable_frame, self.app, s_data)

    def add_script(self):
        ScriptRow(self.scrollable_frame, self.app)
        self.app.save_state()

    def get_data(self):
        scripts = []
        for child in self.scrollable_frame.pack_slaves():
            if isinstance(child, ScriptRow):
                scripts.append(child.get_data())
        return {
            "name": self.data.get("name", "Tab"),
            "scripts": scripts
        }

class ScriptSausageApp(tk.Tk):
    def get_available_pythons(self):
        interpreters = {"python"}
        if os.name == 'nt':
            try:
                out = subprocess.check_output(["where", "python"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                for line in out.splitlines():
                    p = line.strip()
                    if os.path.exists(p) and "WindowsApps" not in p:
                        interpreters.add(p)
            except Exception: pass
            try:
                out = subprocess.check_output(["py", "-0p"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                for line in out.splitlines():
                    for p in line.split():
                        if "python.exe" in p.lower() and os.path.exists(p) and "WindowsApps" not in p:
                            interpreters.add(p)
            except Exception: pass
        return sorted(list(interpreters))

    def __init__(self):
        super().__init__()
        self.title("Script Sausage")
        self.geometry("900x700")
        
        # Enable global smart shortcuts (supports Ctrl+Z, Ctrl+Y, clipboard, etc.)
        make_text_widgets_smart(self)
        
        # Apply a modern theme (clam)
        style = ttk.Style(self)
        
        # UX Improvement: Set a modern default font for all UI elements
        self.option_add("*Font", "{Segoe UI Variable Display} 10")
        style.configure(".", font=("Segoe UI Variable Display", 10))
        
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        # Define high-tech styles for run buttons of different file types
        style.configure("Py.TButton", background="#0277bd", foreground="white", font=("Segoe UI Variable Display", 10, "bold"))
        style.map("Py.TButton", background=[("active", "#039be5"), ("disabled", "#e0e0e0")], foreground=[("disabled", "#9e9e9e")])
        
        style.configure("Bat.TButton", background="#ef6c00", foreground="white", font=("Segoe UI Variable Display", 10, "bold"))
        style.map("Bat.TButton", background=[("active", "#f57c00"), ("disabled", "#e0e0e0")], foreground=[("disabled", "#9e9e9e")])
        
        style.configure("Ps1.TButton", background="#4527a0", foreground="white", font=("Segoe UI Variable Display", 10, "bold"))
        style.map("Ps1.TButton", background=[("active", "#512da8"), ("disabled", "#e0e0e0")], foreground=[("disabled", "#9e9e9e")])
        
        style.configure("Exe.TButton", background="#2e7d32", foreground="white", font=("Segoe UI Variable Display", 10, "bold"))
        style.map("Exe.TButton", background=[("active", "#388e3c"), ("disabled", "#e0e0e0")], foreground=[("disabled", "#9e9e9e")])
        
        style.configure("DefaultRun.TButton", background="#424242", foreground="white", font=("Segoe UI Variable Display", 10, "bold"))
        style.map("DefaultRun.TButton", background=[("active", "#616161"), ("disabled", "#e0e0e0")], foreground=[("disabled", "#9e9e9e")])
            
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # I18N Setup
        self.lang = "en"
        self.texts = {
            "en": {
                "tab_add": "➕ Tab", "script_add": "➕ Script", "debug": "Debug", "py_interp": "Python:",
                "name": "Name:", "path": "Path:", "p1": "P1:", "p2": "P2:", "p3": "P3:",
                "browse": "Browse", "delete": "Delete", "run": "▶ Run", "adv": "...",
                "keep": "Keep Open", "ready": "Ready", "save": "Save", "cancel": "Cancel",
                "adv_title": "Advanced Parameters",
            },
            "zh": {
                "tab_add": "➕ 頁籤", "script_add": "➕ 腳本", "debug": "除錯", "py_interp": "Python:",
                "name": "名稱:", "path": "路徑:", "p1": "P1:", "p2": "P2:", "p3": "P3:",
                "browse": "瀏覽", "delete": "刪除", "run": "▶ 執行", "adv": "...",
                "keep": "保留視窗", "ready": "就緒", "save": "儲存", "cancel": "取消",
                "adv_title": "進階參數編輯",
            }
        }
        self.lang_vars = {k: tk.StringVar(value=self.texts[self.lang][k]) for k in self.texts["en"]}

        
        # Top toolbar
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(top_frame, textvariable=self.lang_vars["tab_add"], command=self.add_tab).pack(side=tk.LEFT, padx=2)
        # Removed manual save button since system auto-saves
        
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_frame, textvariable=self.lang_vars["debug"], variable=self.debug_var, command=self.toggle_debug_panel).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(top_frame, textvariable=self.lang_vars["py_interp"]).pack(side=tk.LEFT, padx=(5, 2))
        self.py_interpreter_var = tk.StringVar(value="python")
        self.py_combobox = ttk.Combobox(top_frame, textvariable=self.py_interpreter_var, values=self.get_available_pythons(), width=35)
        self.py_combobox.pack(side=tk.LEFT, padx=2)
        self.py_combobox.bind("<<ComboboxSelected>>", lambda e: self.save_state())
        self.py_combobox.bind("<FocusOut>", lambda e: self.save_state())

        self.lang_btn = ttk.Button(top_frame, text="EN / 中", command=self.toggle_lang, width=8)
        self.lang_btn.pack(side=tk.RIGHT, padx=5)
        
        # Main layout (PanedWindow top/bottom)
        self.paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.notebook, weight=3)
        
        # Bottom Debug panel
        self.debug_frame = ttk.Frame(self.paned_window)
        self.debug_text = scrolledtext.ScrolledText(self.debug_frame, bg="#1e1e1e", fg="#00ff00", height=8, font=("Cascadia Mono", 11))
        self.debug_text.pack(fill=tk.BOTH, expand=True)
        self.debug_text.insert(tk.END, "--- System Logs and Execution Output ---\n")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.notebook.bind("<Button-3>", self.show_tab_menu) 
        self.notebook.bind("<Double-Button-1>", self.on_tab_double_click)
        self.notebook.bind("<B1-Motion>", self.move_tab)
        self.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Do not save during initialization to avoid overwriting old settings
        self._disable_save = True
        self.load_state()
        self._disable_save = False
        self.toggle_debug_panel() # Decide whether to show panel based on loaded state

    def toggle_lang(self):
        self.lang = "zh" if self.lang == "en" else "en"
        for k, var in self.lang_vars.items():
            var.set(self.texts[self.lang][k])
        self.save_state()

    def toggle_debug_panel(self, *args):
        try:
            if self.debug_var.get():
                self.paned_window.add(self.debug_frame, weight=1)
            else:
                self.paned_window.forget(self.debug_frame)
        except tk.TclError:
            pass
            
        if not getattr(self, '_disable_save', False):
            self.save_state()

    def show_tab_menu(self, event):
        try:
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Rename", command=lambda: self.rename_tab(clicked_tab_index))
            menu.add_command(label="Duplicate", command=lambda: self.duplicate_tab(clicked_tab_index))
            menu.add_command(label="Delete", command=lambda: self.delete_tab(clicked_tab_index))
            menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass

    def on_tab_double_click(self, event):
        try:
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")
            self.rename_tab(clicked_tab_index)
        except tk.TclError:
            pass

    def move_tab(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            self.notebook.insert(index, self.notebook.select())
            self.save_state()
        except tk.TclError:
            pass

    def on_mousewheel(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except Exception:
            return
        if not widget:
            return
        if isinstance(widget, (tk.Text, ttk.Scrollbar, tk.Scrollbar)):
            return
            
        # Handle Notebook tab bar scrolling
        if isinstance(widget, ttk.Notebook):
            try:
                curr = widget.index("current")
                total = widget.index("end")
                if total > 1:
                    if event.delta > 0:
                        next_idx = max(0, curr - 1)
                    else:
                        next_idx = min(total - 1, curr + 1)
                    widget.select(next_idx)
            except tk.TclError:
                pass
            return
            
        while widget:
            if isinstance(widget, tk.Canvas):
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
                break
            widget = getattr(widget, "master", None)

    def rename_tab(self, index):
        current_name = self.notebook.tab(index, "text")
        new_name = tk.simpledialog.askstring("Rename", "Enter new tab name:", initialvalue=current_name)
        if new_name:
            self.notebook.tab(index, text=new_name)
            tab_widget = self.nametowidget(self.notebook.tabs()[index])
            tab_widget.data["name"] = new_name
            self.save_state()

    def duplicate_tab(self, index):
        tab_widget = self.nametowidget(self.notebook.tabs()[index])
        tab_data = json.loads(json.dumps(tab_widget.get_data()))
        tab_data["name"] = f"{tab_data['name']} - Copy"
        self.add_tab(tab_data)
        self.save_state()

    def delete_tab(self, index):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this tab and all its scripts?"):
            self.notebook.forget(index)
            self.save_state()

    def add_tab(self, data=None):
        if not data:
            data = {"name": f"Tab {self.notebook.index('end') + 1}", "scripts": []}
        tab = ScriptTab(self.notebook, self, data)
        self.notebook.add(tab, text=data["name"])

    def load_state(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "lang" in data:
                        self.lang = data["lang"]
                        for k, var in self.lang_vars.items():
                            var.set(self.texts[self.lang][k])
                    if "debug" in data:
                        self.debug_var.set(data["debug"])
                    if "python_interpreter" in data:
                        val = data["python_interpreter"]
                        self.py_interpreter_var.set(val)
                        if val not in self.py_combobox['values']:
                            self.py_combobox['values'] = list(self.py_combobox['values']) + [val]

                    for tab_data in data.get("tabs", []):
                        self.add_tab(tab_data)
                    return
            except Exception as e:
                messagebox.showerror("Read Error", f"Cannot read config file: {e}")
        self.add_tab()

    def save_state(self, *args):
        if getattr(self, '_disable_save', False):
            return
            
        data = {
            "lang": self.lang,
            "debug": self.debug_var.get(),
            "python_interpreter": self.py_interpreter_var.get(),
            "tabs": []
        }
        for tab_id in self.notebook.tabs():
            tab_widget = self.nametowidget(tab_id)
            if isinstance(tab_widget, ScriptTab):
                data["tabs"].append(tab_widget.get_data())
                
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"✔️ Auto-saved ({now})")
        
        if hasattr(self, "_status_timer"):
            self.after_cancel(self._status_timer)
        self._status_timer = self.after(3000, lambda: self.status_var.set("Ready"))

    def on_close(self):
        self.save_state()
        self.destroy()

    def show_log_and_run(self, cmd):
        process = None

        def run_process():
            nonlocal process
            try:
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                process.wait()
                if self.debug_var.get():
                    self.log_debug(f"[Process exited with code {process.returncode}]\n")
            except Exception as e:
                if self.debug_var.get():
                    self.log_debug(f"[Execution Error] {e}\n")
                else:
                    messagebox.showerror("Execution Error", f"Cannot execute command:\n{e}")

        if self.debug_var.get():
            if isinstance(cmd, list):
                raw_cmd = " ".join(shlex.quote(c) for c in cmd)
            else:
                raw_cmd = cmd
            self.log_debug(f"> Executing command: {raw_cmd}\n[Script started in a new independent terminal window...]")
            
        threading.Thread(target=run_process, daemon=True).start()
        
    def log_debug(self, msg):
        self.after(0, lambda: self._log_debug_sync(msg))
        
    def _log_debug_sync(self, msg):
        self.debug_text.insert(tk.END, msg + "\n")
        self.debug_text.see(tk.END)

if __name__ == "__main__":
    app = ScriptSausageApp()
    app.mainloop()
