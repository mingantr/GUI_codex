import sys
from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import apply_theme, get_theme


def main() -> int:
    app = QApplication(sys.argv)
    # Apply saved theme (defaults to dark)
    apply_theme(app, get_theme())
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
