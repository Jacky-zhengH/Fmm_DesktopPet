"""Disposable local animation preview. Never loads or saves a real pet profile."""
import argparse
from datetime import date
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'deskpet' / 'deskpet'))
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from pet.character import Character, State
from pet.fonts import ensure_fonts
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow


class EventPreview(QWidget):
    def __init__(self, auto_close_seconds=35):
        super().__init__()
        self.setWindowTitle('芙芙 · 演出预览')
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setFixedWidth(360)
        self.setStyleSheet("QWidget { font-family: 'Microsoft YaHei UI'; font-size: 12px; color: #704d5b; background: #fffaf6; } QPushButton { padding: 6px 18px; }")
        self.character = Character(SpriteLibrary())
        self.pet = PetWindow(self.character, PetSettings(wander=False, auto_sleep_seconds=0), None)
        self._origin = None
        self._stopped = False
        self._auto_close_ms = round(auto_close_seconds * 1000)
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.close)
        layout = QVBoxLayout(self)
        self.note = QLabel('临时预览，不影响已打开的桌宠或正式记录。')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        row = QHBoxLayout()
        self.replay_button = QPushButton('再看一次')
        self.replay_button.clicked.connect(self.replay)
        row.addWidget(self.replay_button)
        close_button = QPushButton('关闭预览')
        close_button.clicked.connect(self.close)
        row.addWidget(close_button)
        layout.addLayout(row)

    def start(self):
        work = QApplication.primaryScreen().availableGeometry()
        self.pet.show()
        self._origin = work.bottomLeft() + QPoint(40, -self.pet.height() - 24)
        self.adjustSize()
        self.move(work.center().x() - self.width() // 2, work.top() + 24)
        self.show()
        self.replay()

    def replay(self):
        ui = self.pet.ui
        ui.startup_timer.stop()
        ui.cancel_arrival()
        ui.cancel_timer()
        ui.hide_all()
        self.pet._dock_edge = self.pet._dock_screen_name = None
        self.character._enter_state(State.IDLE)
        if self._origin is not None:
            self.pet.move(self._origin)
            self.pet._clamp_to_screen()
        self.pet.settings.last_greeting_date = None
        # This patched calendar exists only inside this preview process/call.
        # Run the exact production event path, with an in-memory profile.
        with patch('pet.bubble_ui.date') as calendar:
            calendar.today.return_value = date(2026, 10, 24)
            ui.startup_greeting()
        self.note.setText(f'走到中央 → 分段祝福 → 回到原位。\n{self._auto_close_ms / 1000:g} 秒后关闭；重播从起点重新开始。' if self._auto_close_ms
                          else '临时预览，不影响正式记录；可重播或关闭。')
        if self._auto_close_ms:
            self.close_timer.start(self._auto_close_ms)

    def stop(self):
        if not self._stopped:
            self._stopped = True
            self.close_timer.stop()
            self.character.pause()
            self.pet.close()

    def closeEvent(self, event):
        self.stop()
        QApplication.instance().quit()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stay-open', action='store_true', help='keep preview open until explicitly closed')
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    ensure_fonts(app)
    preview = EventPreview(0 if args.stay_open else 35)
    app.aboutToQuit.connect(preview.stop)
    preview.start()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
