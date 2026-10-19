"""Temporary native Qt test panel; user preferences are never loaded or saved."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from pet.character import Character, State
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
ensure_fonts(app)
character = Character(SpriteLibrary())
pet = PetWindow(character, PetSettings(wander=False, auto_sleep_seconds=0), None)
pet.show()
pet.move(pet.x(), round(pet._current_screen().availableGeometry().bottom() + 1
                        - pet.visible_content_rect().bottom() - 10))
pet.finish_drag()
panel = QWidget()
panel.setWindowTitle("fmm 0.1.x 修复验证")
panel.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
panel.setMinimumWidth(390)
layout = QVBoxLayout(panel)
status = QLabel()
layout.addWidget(status)
for label, callback in (
    ("待机", lambda: character._enter_state(State.IDLE)),
    ("走路", character._start_wander),
    ("睡觉", lambda: character._enter_state(State.SLEEP)),
    ("大小 100%", lambda: pet.set_pet_size(200)),
    ("大小 150%", lambda: pet.set_pet_size(300)),
    ("结束测试", app.quit)):
    button = QPushButton(label)
    button.clicked.connect(callback)
    layout.addWidget(button)
panel.move(100, 180)
panel.show()
last = {}


def refresh():
    screen = pet._current_screen()
    body = pet.visible_content_rect().translated(pet.pos())
    last.update(state=character.state, dock_edge=pet._dock_edge, size=pet.settings.size,
                visible_height=round(body.height(), 3), feet_y=round(body.bottom(), 3),
                taskbar_top=screen.availableGeometry().bottom() + 1,
                input_bottom=pet.y() + pet._input_rect.bottom() + 1,
                native_mask_bottom=pet.y() + pet.mask().boundingRect().bottom() + 1)
    status.setText(f"动作：{last['state']}\n吸附：{last['dock_edge']}\n"
                   f"可见高度：{last['visible_height']}\n脚底：{last['feet_y']}\n"
                   f"任务栏上沿：{last['taskbar_top']}\n输入区域下沿：{last['input_bottom']}")


timer = QTimer()
timer.timeout.connect(refresh)
timer.start(100)
QTimer.singleShot(240000, app.quit)
refresh()
app.exec()
character.pause()
pet.close()
panel.close()
(ROOT / "analysis" / "docking_desktop_result.json").write_text(json.dumps(last, indent=2), encoding="utf-8")
