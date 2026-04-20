import sys
import os

# Add the project root directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scriptsausage.main import ScriptSausageApp

if __name__ == "__main__":
    app = ScriptSausageApp()
    app.mainloop()
