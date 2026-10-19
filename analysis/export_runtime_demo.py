"""Run real Qt widgets and export their own render frames, not a desktop recording."""
import os
from pathlib import Path
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from PIL import Image
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from pet.character import Character, State
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
ensure_fonts(app)
character = Character(SpriteLibrary())
window = PetWindow(character, PetSettings(wander=False, auto_sleep_seconds=0), None)
window.show()
frames = []
started = time.monotonic()
done = set()
snapshot = None


def capture():
    global snapshot
    elapsed = time.monotonic() - started
    if elapsed >= 10.8:
        app.quit()
        return
    if elapsed >= 1.5 and "pet" not in done:
        done.add("pet")
        QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(100, 100))
    if elapsed >= 3.3 and "sleep" not in done:
        done.add("sleep")
        character.toggle_sleep()
    if elapsed >= 5.0 and "wake" not in done:
        done.add("wake")
        QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(100, 100))
    if elapsed >= 5.8 and "walk" not in done:
        done.add("walk")
        character._enter_state(State.WALK)
        character._walk_target = character._x + 100
    if elapsed >= 7.3 and "panel" not in done:
        done.add("panel")
        character._enter_state(State.IDLE)
        window.show_size_dialog()
    if elapsed >= 8.1 and "resize" not in done:
        done.add("resize")
        window._size_dialog.slider.setValue(150)
    if elapsed >= 9.2 and "limit" not in done:
        done.add("limit")
        window._size_dialog.slider.setValue(80)
    if elapsed >= 10.0 and "restore" not in done:
        done.add("restore")
        window._size_dialog.slider.setValue(100)

    sheet = QPixmap(640, 920)
    sheet.fill(QColor("#22262f"))
    painter = QPainter(sheet)
    painter.setPen(QColor("#fff1f3"))
    font = QFont(app.font())
    font.setPixelSize(25)
    painter.setFont(font)
    painter.drawText(28, 44, "fmm 桌宠 · 源码运行演示")
    font.setPixelSize(18)
    painter.setFont(font)
    labels = {State.IDLE: "待机 / 呼吸", State.HAPPY: "单击：开心互动", State.SLEEP: "睡觉：呼吸与 Zzz", State.WALK: "自主走路（现有两帧）"}
    painter.drawText(28, 80, "调整大小：实时预览" if window._size_dialog else labels.get(character.state, character.state))
    pet = window.grab()
    painter.drawPixmap(QPoint((640 - pet.width()) // 2, 440 - pet.height()), pet)
    if window._size_dialog:
        panel = window._size_dialog.grab()
        painter.drawPixmap(QPoint((640 - panel.width()) // 2, 470), panel)
    else:
        painter.setPen(QColor("#e2c7d0"))
        painter.drawText(28, 550, "普通滚轮不缩放，避免误触")
        painter.drawText(28, 590, "右键 → 调整大小：滑条 / 加减按钮")
        painter.drawText(28, 630, "快捷方式：Ctrl + 滚轮")
        painter.drawText(28, 670, "范围 80%～200%，默认 100%")
    painter.setPen(QColor("#c2c6ce"))
    font.setPixelSize(15)
    painter.setFont(font)
    painter.drawText(28, 880, "Qt 实际绘制导出 · 非桌面录屏 · 原始素材未更改")
    painter.end()
    qt_image = sheet.toImage().convertToFormat(QImage.Format_RGBA8888)
    frame = Image.frombytes("RGBA", (qt_image.width(), qt_image.height()), bytes(qt_image.bits())).convert("RGB")
    frames.append(frame)
    if 8.3 < elapsed < 8.6:
        snapshot = frame.copy()


timer = QTimer()
timer.timeout.connect(capture)
timer.start(100)
app.exec()
character.pause()
if window._size_dialog:
    window._size_dialog.reject()
character.pause()
window.close()
if not frames:
    raise RuntimeError("No Qt frames captured")
palette = frames[0].quantize(colors=128)
converted = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
path = ROOT / "analysis" / "runtime_demo.gif"
converted[0].save(path, save_all=True, append_images=converted[1:], duration=100, loop=0, optimize=True)
(snapshot or frames[-1]).save(ROOT / "analysis" / "size_panel_preview.png")
print(f"Rendered {len(frames)} real Qt frames to {path}")
