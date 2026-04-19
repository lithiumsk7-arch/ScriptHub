import tkinter as tk
from tkinter import ttk

def make_text_widgets_smart(root):
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
            if hasattr(event.widget, "delete"):
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

root = tk.Tk()
make_text_widgets_smart(root)
e = ttk.Entry(root)
e.pack()
t = tk.Text(root, height=5)
t.pack()
root.mainloop()
