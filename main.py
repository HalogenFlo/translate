import sys
from src.ui.app import ToolListenApp

def main():
    app = ToolListenApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
