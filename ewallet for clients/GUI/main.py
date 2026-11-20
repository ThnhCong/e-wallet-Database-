"""Application entry point for the E-Wallet desktop client."""
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


def project_root() -> Path:
    """Return the bundle/source root without depending on the current directory."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller one-file extracts bundled files under _MEIPASS.
        return Path(sys._MEIPASS).resolve()
    # Source layout: project_root/GUI/main.py
    return Path(__file__).resolve().parent.parent


ROOT = project_root()
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
