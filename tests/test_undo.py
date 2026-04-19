import tkinter as tk
from tkinter import ttk

def setup_smart_text_widget(widget):
    if isinstance(widget, (tk.Entry, ttk.Entry)):
        widget._undo_stack = [""]
        widget._redo_stack = []
        widget._last_val = ""
        
        def save_state(event=None):
            current = widget.get()
            if current != widget._last_val:
                widget._undo_stack.append(current)
                if len(widget._undo_stack) > 50:
                    widget._undo_stack.pop(0)
                widget._redo_stack.clear()
                widget._last_val = current
                
        def do_undo(event=None):
            if len(widget._undo_stack) > 1:
                widget._redo_stack.append(widget._undo_stack.pop())
                val = widget._undo_stack[-1]
                widget.delete(0, tk.END)
                widget.insert(0, val)
                widget._last_val = val
            return "break"
            
        def do_redo(event=None):
            if widget._redo_stack:
                val = widget._redo_stack.pop()
                widget._undo_stack.append(val)
                widget.delete(0, tk.END)
                widget.insert(0, val)
                widget._last_val = val
            return "break"
            
        widget.bind("<KeyRelease>", save_state, add="+")
        widget.bind("<Control-z>", do_undo)
        widget.bind("<Control-Z>", do_undo)
        widget.bind("<Control-y>", do_redo)
        widget.bind("<Control-Y>", do_redo)

root = tk.Tk()
e = ttk.Entry(root)
e.pack()
setup_smart_text_widget(e)
root.mainloop()
