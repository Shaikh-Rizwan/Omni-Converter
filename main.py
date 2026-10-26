import ctypes
import os
import sys

# High DPI awareness for crisp rendering on Windows 10/11
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Ensure working directory is application directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()

