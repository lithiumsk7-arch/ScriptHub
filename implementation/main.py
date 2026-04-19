import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
import os
import subprocess
import shlex
import threading

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

class AdvancedParamDialog(tk.Toplevel):
    def __init__(self, parent, initial_text, callback):
        super().__init__(parent)
        self.title("進階參數編輯")
        self.geometry("400x300")
        self.callback = callback
        
        self.text = tk.Text(self, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text.insert(tk.END, initial_text)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="儲存", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        
        self.transient(parent)
        self.grab_set()
        
        # 確保按右上角 X 關閉時也會儲存
        self.protocol("WM_DELETE_WINDOW", self.save)

    def save(self):
        self.callback(self.text.get("1.0", tk.END).strip())
        self.destroy()

class ScriptRow(ttk.Frame):
    def __init__(self, parent, app, data=None):
        super().__init__(parent)
        self.app = app
        self.data = data or {"name": "New Script", "path": "", "p1": "", "p2": "", "p3": "", "adv_p": ""}
        
        self.adv_param_text = self.data.get("adv_p", "")
        
        # 拖拉排序替代方案：上下移動按鈕
        # (原生 Tkinter 實作全域 Drag & Drop 較肥大，此處以按鈕達到精準排序)
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="▲", width=2, command=self.move_up).pack()
        ttk.Button(ctrl_frame, text="▼", width=2, command=self.move_down).pack()
        
        # 名稱
        self.name_var = tk.StringVar(value=self.data.get("name", ""))
        tk.Entry(self, textvariable=self.name_var, width=15).pack(side=tk.LEFT, padx=2)
        
        # 路徑
        self.path_var = tk.StringVar(value=self.data.get("path", ""))
        tk.Entry(self, textvariable=self.path_var, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(self, text="📁", width=3, command=self.browse_file).pack(side=tk.LEFT, padx=2)
        
        # 參數 1, 2, 3
        self.p1_var = tk.StringVar(value=self.data.get("p1", ""))
        self.p2_var = tk.StringVar(value=self.data.get("p2", ""))
        self.p3_var = tk.StringVar(value=self.data.get("p3", ""))
        tk.Entry(self, textvariable=self.p1_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Entry(self, textvariable=self.p2_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Entry(self, textvariable=self.p3_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # 進階參數
        ttk.Button(self, text="...", width=3, command=self.open_adv_params).pack(side=tk.LEFT, padx=2)
        
        # 執行與刪除
        ttk.Button(self, text="執行", command=self.run_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(self, text="❌", width=3, command=self.delete_self).pack(side=tk.LEFT, padx=2)

        self.pack(fill=tk.X, pady=2)

        # 任何修改都觸發自動儲存的簡單綁定
        self.name_var.trace_add("write", lambda *args: self.app.save_state())
        self.path_var.trace_add("write", lambda *args: self.app.save_state())
        self.p1_var.trace_add("write", lambda *args: self.app.save_state())
        self.p2_var.trace_add("write", lambda *args: self.app.save_state())
        self.p3_var.trace_add("write", lambda *args: self.app.save_state())

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.path_var.set(os.path.normpath(path))

    def open_adv_params(self):
        def save_adv(text):
            self.adv_param_text = text
            self.app.save_state()
        AdvancedParamDialog(self, self.adv_param_text, save_adv)

    def delete_self(self):
        if messagebox.askyesno("確認", "確定要刪除這個腳本設定嗎？"):
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
            "adv_p": self.adv_param_text
        }

    def run_script(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("錯誤", "尚未指定腳本路徑")
            return
        
        # 展開環境變數
        path = os.path.expandvars(path)
        
        if not os.path.exists(path):
            messagebox.showerror("錯誤", f"找不到檔案: {path}")
            return
            
        ext = os.path.splitext(path)[1].lower()
        cmd_list = []
        if ext == ".py":
            cmd_list.append("python")
        elif ext in [".bat", ".cmd"]:
            cmd_list.append("cmd.exe")
            cmd_list.append("/c")
        elif ext == ".ps1":
            cmd_list.extend(["powershell", "-ExecutionPolicy", "Bypass", "-File"])
        elif ext != ".exe":
            messagebox.showwarning("警告", f"未知的副檔名: {ext}，將嘗試直接執行")
            
        cmd_list.append(path)
        
        # 參數合併與解析
        params_str = f"{self.p1_var.get()} {self.p2_var.get()} {self.p3_var.get()} {self.adv_param_text}".strip()
        params_str = os.path.expandvars(params_str)
        try:
            if params_str:
                args = shlex.split(params_str, posix=(os.name != 'nt'))
                cmd_list.extend(args)
        except ValueError as e:
            messagebox.showerror("解析錯誤", f"參數引號不匹配: {e}\n請檢查是否漏打了雙引號。")
            return

        self.app.show_log_and_run(cmd_list)

class ScriptTab(ttk.Frame):
    def __init__(self, parent, app, data=None):
        super().__init__(parent)
        self.app = app
        self.data = data or {"name": "New Tab", "scripts": []}
        
        # 控制區
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(side="top", fill="x", pady=5)
        ttk.Button(ctrl_frame, text="➕ 新增腳本", command=self.add_script).pack(side="left", padx=5)
        
        # 滾動區域
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
        
        # 讀取腳本
        for s_data in self.data.get("scripts", []):
            ScriptRow(self.scrollable_frame, self.app, s_data)

    def add_script(self):
        ScriptRow(self.scrollable_frame, self.app)
        self.app.save_state()

    def get_data(self):
        scripts = []
        # 注意: pack_slaves 確保抓到的是目前畫面上的實際順序
        for child in self.scrollable_frame.pack_slaves():
            if isinstance(child, ScriptRow):
                scripts.append(child.get_data())
        return {
            "name": self.data.get("name", "Tab"),
            "scripts": scripts
        }

class ScriptHubApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Script Hub")
        self.geometry("900x600")
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 頂部工具列
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(top_frame, text="➕ 新增頁籤", command=self.add_tab).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="💾 儲存設定", command=self.save_state).pack(side=tk.LEFT, padx=2)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 頁籤操作綁定
        self.notebook.bind("<Button-3>", self.show_tab_menu) # 右鍵選單
        self.notebook.bind("<Double-Button-1>", self.on_tab_double_click) # 雙擊改名
        self.notebook.bind("<B1-Motion>", self.move_tab) # 拖拉排序
        
        self.load_state()

    def show_tab_menu(self, event):
        try:
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="重新命名此頁籤", command=lambda: self.rename_tab(clicked_tab_index))
            menu.add_command(label="刪除此頁籤", command=lambda: self.delete_tab(clicked_tab_index))
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

    def rename_tab(self, index):
        current_name = self.notebook.tab(index, "text")
        new_name = tk.simpledialog.askstring("重新命名", "請輸入新頁籤名稱:", initialvalue=current_name)
        if new_name:
            self.notebook.tab(index, text=new_name)
            # 更新背後的資料物件
            tab_widget = self.nametowidget(self.notebook.tabs()[index])
            tab_widget.data["name"] = new_name
            self.save_state()

    def delete_tab(self, index):
        if messagebox.askyesno("確認", "確定要刪除此頁籤與其包含的所有腳本嗎？"):
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
                    for tab_data in data.get("tabs", []):
                        self.add_tab(tab_data)
                    return
            except Exception as e:
                messagebox.showerror("讀取錯誤", f"無法讀取設定檔: {e}")
        self.add_tab() # 預設給一個空頁籤

    def save_state(self):
        data = {"tabs": []}
        for tab_id in self.notebook.tabs():
            tab_widget = self.nametowidget(tab_id)
            if isinstance(tab_widget, ScriptTab):
                data["tabs"].append(tab_widget.get_data())
                
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def on_close(self):
        self.save_state()
        self.destroy()

    def show_log_and_run(self, cmd_list):
        log_win = tk.Toplevel(self)
        log_win.title("執行輸出")
        log_win.geometry("800x500")
        
        # 顯示安全且精準還原的最終指令
        raw_cmd = " ".join(shlex.quote(c) for c in cmd_list)
        tk.Label(log_win, text="最終送給 Shell 的指令:").pack(anchor="w", padx=5)
        cmd_text = tk.Text(log_win, height=3, bg="black", fg="lime")
        cmd_text.insert("1.0", raw_cmd)
        cmd_text.config(state=tk.DISABLED)
        cmd_text.pack(fill=tk.X, padx=5)
        
        tk.Label(log_win, text="執行輸出 (stdout/stderr):").pack(anchor="w", padx=5, pady=(5,0))
        output_text = scrolledtext.ScrolledText(log_win, bg="black", fg="white")
        output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        process = None
        
        def run_thread():
            nonlocal process
            try:
                # 使用 shell=False 阻絕命令注入
                process = subprocess.Popen(
                    cmd_list, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    errors="replace",
                    bufsize=1,
                    # Windows特有：隱藏執行時彈出的黑色 Console 視窗
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                for line in iter(process.stdout.readline, ''):
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
                process.stdout.close()
                process.wait()
                output_text.insert(tk.END, f"\n[Process exited with code {process.returncode}]\n")
            except Exception as e:
                output_text.insert(tk.END, f"\n[執行發生錯誤] {e}\n")

        threading.Thread(target=run_thread, daemon=True).start()
        
        def kill_process():
            if process and process.poll() is None:
                process.terminate()
                output_text.insert(tk.END, "\n[Force Terminated 由使用者強制中斷]\n")
                
        ttk.Button(log_win, text="🛑 強制停止", command=kill_process).pack(pady=5)

if __name__ == "__main__":
    app = ScriptHubApp()
    app.mainloop()
