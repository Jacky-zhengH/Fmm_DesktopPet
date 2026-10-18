"""Render the real Qt controls; --native opens a temporary test pet."""
import argparse
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--native', action='store_true')
parser.add_argument('--exit-after-render', action='store_true')
parser.add_argument('--sleep', action='store_true')
parser.add_argument('--feedback', action='store_true')
parser.add_argument('--timer', type=int, default=0)
parser.add_argument('--alarm', action='store_true')
parser.add_argument('--panel', choices=['food', 'clock', 'settings'], default='food')
args = parser.parse_args()
if not args.native:
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'deskpet' / 'deskpet'))
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from pet.character import Character, State
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
if args.sleep:
    pet.character._enter_state(State.SLEEP)
pet.show()
work = pet._current_screen().availableGeometry()
pet.move(work.center().x() - 230, work.center().y())
pet.ui.show_menu()
pet.ui.open_panel(args.panel)
if args.feedback and args.panel == 'food':
    pet.ui.preview_food()
if args.timer:
    pet.ui.start_seconds(args.timer)
if args.alarm:
    import time
    pet.ui.deadline = time.monotonic() - 1
    pet.ui.tick()



def render():
    widgets = [w for w in (pet, pet.ui.ribbon, pet.ui.panel, pet.ui.speech, pet.ui.countdown)
               if w is not None and w.isVisible()]
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
    p.drawText(38, 69, '弧形小菜单 / 点心滑动切换 / 计时器独立显示')
    offset = QPoint((sheet.width() - bounds.width()) // 2 - bounds.left(), 105 - bounds.top())
    for widget in widgets:
        p.drawPixmap(widget.pos() + offset, widget.grab())
    p.end()
    name = 'ui_0_1_2_preview' if args.panel == 'food' else f'ui_0_1_2_{args.panel}'
    name += '_feedback' if args.feedback else ''
    name += '_timer' if args.timer else ''
    name += '_alarm' if args.alarm else ''
    name += '_sleep' if args.sleep else ''
    path = ROOT / 'analysis' / (name + '.png')
    sheet.save(str(path))
    print(path, flush=True)
    if not args.native or args.exit_after_render:
        pet.close()
        app.quit()


QTimer.singleShot(pet.ui._arrival_animation.duration() + 220 if args.alarm else 600, render)
QTimer.singleShot(240000, app.quit)
app.aboutToQuit.connect(pet.close)
app.exec()
