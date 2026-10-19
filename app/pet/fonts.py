"""Fallback for restricted/offscreen Windows sessions with no enumerated fonts."""
import os
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase


def ensure_fonts(app):
    if QFontDatabase.families():
        return
    directory = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("msyh.ttc", "segoeui.ttf"):
        path = directory / name
        if path.exists():
            identifier = QFontDatabase.addApplicationFont(str(path))
            families = QFontDatabase.applicationFontFamilies(identifier)
            if families:
                app.setFont(QFont(families[0], 10))
                return
