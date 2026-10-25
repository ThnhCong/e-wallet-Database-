import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from GUI.main_window import MainWindow
from GUI.theme.theme_manager import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("E-Wallet Management System")
    app.setFont(QFont("Segoe UI", 10))
    apply_theme(app, "light")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
