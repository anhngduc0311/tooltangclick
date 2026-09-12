import sys
import os

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
