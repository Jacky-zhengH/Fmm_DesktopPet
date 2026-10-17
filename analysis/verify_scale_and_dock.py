"""Render a source-art comparison using Qt, without editing any PNG files."""
import os
from pathlib import Path
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deskpet" / "deskpet"))
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from pet.character import Character, State
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

app = QApplication([])
ensure_fonts(app)
library = SpriteLibrary()
character = Character(library)
character.pause()
window = PetWindow(character, PetSettings(wander=False), None)
window.show()
sheet = QPixmap(800, 720)
sheet.fill(QColor("#22262f"))
painter = QPainter(sheet)
font = QFont(app.font())
font.setPixelSize(22)
painter.setFont(font)
painter.setPen(Qt.white)
painter.drawText(28, 40, "走路大小修复 · 100% 对照")
font.setPixelSize(17)
painter.setFont(font)
painter.drawText(28, 78, "旧版：按整张画布缩放，人物变小且脚底上移")
for index, state in enumerate((State.IDLE, State.WALK)):
    pix = library.get("idle" if state == State.IDLE else "walk_0")
    factor = 200 / max(pix.width(), pix.height())
    x = 200 + 350 * index - pix.width() * factor / 2
    painter.drawPixmap(QRectF(x, 300 - pix.height() * factor, pix.width() * factor, pix.height() * factor), pix, QRectF(pix.rect()))
    painter.drawText(125 + 350 * index, 328, "待机：约 179 px" if not index else "走路：约 139 px")
painter.setPen(QColor("#6fdaa8"))
painter.drawLine(28, 300, 770, 300)
painter.setPen(Qt.white)
painter.drawText(28, 390, "修复后：统一可见高度，脚底贴同一基线")
for index, state in enumerate((State.IDLE, State.WALK)):
    character._enter_state(state)
    app.processEvents()
    pix = window.grab()
    baseline = window.visible_content_rect().bottom()
    painter.drawPixmap(QPointF(200 + 350 * index - pix.width() / 2, 610 - baseline), pix)
    painter.drawText(125 + 350 * index, 648, "待机：约 179 px" if not index else "走路：约 179 px")
painter.setPen(QColor("#6fdaa8"))
painter.drawLine(28, 610, 770, 610)
painter.setPen(QColor("#c2c6ce"))
painter.drawText(28, 695, "原始素材未改动；下排为实际 Qt 窗口绘制。")
painter.end()
path = ROOT / "analysis" / "ver0_1_scale_comparison.png"
assert sheet.save(str(path))
window.close()
print(path)
