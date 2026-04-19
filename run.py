import sys
import os

# 將專案根目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scriptsausage.main import ScriptSausageApp

if __name__ == "__main__":
    app = ScriptSausageApp()
    app.mainloop()
