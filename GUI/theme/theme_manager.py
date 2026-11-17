"""Load GUI theme files using paths relative to this module."""
from pathlib import Path

_THEME_DIR = Path(__file__).resolve().parent


def apply_theme(app, name="light"):
    """Load a QSS theme bundled beside this module."""
    theme_file = _THEME_DIR / f"{name}.qss"
    try:
        stylesheet = theme_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        stylesheet = ""
    app.setStyleSheet(stylesheet)
