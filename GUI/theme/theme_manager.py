from pathlib import Path


_THEME_DIR = Path(__file__).resolve().parent


def apply_theme(app, name="light"):
    """Load a QSS theme globally so widgets stay visually consistent."""
    theme_file = _THEME_DIR / f"{name}.qss"
    app.setStyleSheet(theme_file.read_text(encoding="utf-8") if theme_file.exists() else "")
