"""Render the actual Qt widget offscreen; does not automate the desktop."""
import os
from pathlib import Path
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from pet.character import Character, State
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

app = QApplication([])
ensure_fonts(app)
character = Character(SpriteLibrary())
character.pause()
window = PetWindow(character, PetSettings(wander=False), None)
window.show()
sheet = QPixmap(1200, 720)
sheet.fill(QColor("#22262f"))
painter = QPainter(sheet)
painter.setPen(Qt.white)
font = QFont()
font.setPixelSize(18)
painter.setFont(font)
for index, size in enumerate((100, 200, 400)):
    window.set_pet_size(size)
    character._enter_state(State.IDLE)
    app.processEvents()
    pixmap = window.grab()
    x = index * 400 + (400 - pixmap.width()) // 2
    painter.drawPixmap(QPoint(x, 500 - pixmap.height()), pixmap)
    painter.drawText(index * 400 + 30, 540, f"{size / 2:g}% / sprite canvas {size}px")
    painter.drawText(index * 400 + 30, 570, f"window {window.width()} x {window.height()} (padding)")
painter.drawText(30, 650, "Actual Qt offscreen render. Original PNG files are unchanged.")
painter.end()
result = ROOT / "analysis" / "phase1_qt_render.png"
if not sheet.save(str(result)):
    raise RuntimeError("Could not save Qt render")
window.close()
print(result)
