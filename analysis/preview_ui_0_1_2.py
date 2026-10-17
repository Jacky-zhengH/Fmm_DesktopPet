"""Render the real Qt controls; --native opens a temporary test pet."""
import argparse
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--native', action='store_true')
parser.add_argument('--panel', choices=['food', 'clock', 'settings'], default='food')
args = parser.parse_args()
if not args.native:
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'deskpet' / 'deskpet'))
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from pet.character import Character
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
ensure_fonts(app)
pet = PetWindow(Character(SpriteLibrary()), PetSettings(wander=False, auto_sleep_seconds=0), None)
if args.native:
    host = QWidget()
    host.setWindowTitle('fmm 0.1.2 UI 验证')
    host.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    controls = QVBoxLayout(host)
    for key, text in (('food', '喂食面板'), ('clock', '时钟面板'), ('settings', '设置面板')):
        button = QPushButton(text)
        button.clicked.connect(lambda checked=False, k=key: pet.ui.open_panel(k))
        controls.addWidget(button)
    quit_button = QPushButton('结束验证')
    quit_button.clicked.connect(app.quit)
    controls.addWidget(quit_button)
    host.move(40, 80)
    host.show()
    pet.setParent(host, pet.windowFlags())
pet.show()
work = pet._current_screen().availableGeometry()
pet.move(work.center().x() - 230, work.center().y())
pet.ui.show_menu()
pet.ui.open_panel(args.panel)


def render():
    widgets = (pet, pet.ui.ribbon, pet.ui.panel)
    bounds = QRect()
    for widget in widgets:
        bounds = bounds.united(widget.geometry())
    sheet = QPixmap(max(800, bounds.width() + 120), max(620, bounds.height() + 150))
    sheet.fill(QColor('#f0eae7'))
    p = QPainter(sheet)
    p.setPen(QColor('#795562'))
    font = QFont(app.font())
    font.setPixelSize(22)
    p.setFont(font)
    p.drawText(38, 45, '芙眠眠 · 0.1.2 气泡 UI')
    font.setPixelSize(12)
    p.setFont(font)
    p.drawText(38, 69, '角色旁的三个入口 / 同时只打开一个面板 / 喂食为概念预览')
    offset = QPoint((sheet.width() - bounds.width()) // 2 - bounds.left(), 105 - bounds.top())
    for widget in widgets:
        p.drawPixmap(widget.pos() + offset, widget.grab())
    p.end()
    path = ROOT / 'analysis' / ('ui_0_1_2_preview.png' if args.panel == 'food' else f'ui_0_1_2_{args.panel}.png')
    sheet.save(str(path))
    print(path, flush=True)
    if not args.native:
        pet.close()
        app.quit()


QTimer.singleShot(600, render)
QTimer.singleShot(240000, app.quit)
app.aboutToQuit.connect(pet.close)
app.exec()
