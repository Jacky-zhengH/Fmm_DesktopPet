"""Small companion controls; food values are an explicit, in-memory UI demo."""
import math
import time
from PySide6.QtCore import QEvent, QObject, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap, QRegion
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox,
                              QHBoxLayout, QLabel, QPushButton, QProgressBar,
                              QScrollArea, QSystemTrayIcon, QToolButton, QVBoxLayout, QWidget)
from pet.character import State
from pet.ui_geometry import menu_placement, panel_placement

INK = "#704d5b"
STYLE = """
QWidget { color: #704d5b; font-family: 'Microsoft YaHei UI', 'Microsoft YaHei'; font-size: 12px; }
QLabel { background: transparent; border: none; }
QPushButton, QToolButton { background: #fff5f3; border: 1px solid #ead1d6; border-radius: 11px; padding: 8px 12px; }
QPushButton:hover, QToolButton:hover { background: #fbe5e9; border-color: #d995aa; }
QPushButton:pressed, QPushButton:checked, QToolButton:checked { background: #f5d7e0; border-color: #d995aa; }
QPushButton:disabled { color: #b8a9ae; }
QPushButton[primary="true"] { color: white; background: #bd748d; border: none; font-weight: bold; }
QPushButton[primary="true"]:hover { background: #aa607b; }
QCheckBox { spacing: 9px; padding: 5px 0; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #d9a9b8; border-radius: 5px; background: #fffaf5; }
QCheckBox::indicator:checked { background: #bd748d; border: 3px solid #f5dce4; }
QProgressBar { border: none; border-radius: 4px; background: #eee5e3; height: 8px; }
QProgressBar::chunk { border-radius: 4px; background: #d695aa; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { width: 5px; background: transparent; }
QScrollBar::handle:vertical { background: #dfc1cc; border-radius: 2px; min-height: 18px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def draw_symbol(p, kind, rect, color=INK):
    p.save()
    p.translate(rect.x(), rect.y())
    p.scale(rect.width() / 24, rect.height() / 24)
    p.setPen(QPen(QColor(color), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    if kind == "clock":
        p.drawEllipse(QRectF(3, 3, 18, 18))
        p.drawLine(12, 7, 12, 12)
        p.drawLine(12, 12, 16, 14)
    elif kind == "food":
        p.drawArc(QRectF(3, 8, 18, 12), 180 * 16, 180 * 16)
        p.drawLine(3, 14, 21, 14)
        p.drawLine(8, 21, 16, 21)
        p.drawLine(10, 4, 9, 8)
        p.drawLine(15, 3, 14, 7)
    else:
        p.drawEllipse(QRectF(5, 5, 14, 14))
        p.drawEllipse(QRectF(9, 9, 6, 6))
        for angle in range(0, 360, 45):
            p.save()
            p.translate(12, 12)
            p.rotate(angle)
            p.drawLine(0, -8, 0, -11)
            p.restore()
    p.restore()


class RowCheckBox(QCheckBox):
    def hitButton(self, point):
        return self.rect().contains(point)


class BubbleButton(QAbstractButton):
    def __init__(self, kind, text, tint, parent):
        super().__init__(parent)
        self.kind, self.tint = kind, tint
        self.setText(text)
        self.setAccessibleName(text)
        self.setToolTip(text)
        self.setFixedSize(68, 76)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#d69bad" if self.underMouse() or self.hasFocus() else "#ead1d6"), 1.4))
        p.setBrush(QColor("#f6dce5" if self.isDown() else self.tint))
        p.drawEllipse(QRectF(10, 3, 48, 48))
        draw_symbol(p, self.kind, QRectF(22, 15, 24, 24))
        p.setPen(QColor(INK))
        p.drawText(QRectF(0, 55, 68, 19), Qt.AlignCenter, self.text())


def food_icon(kind):
    pix = QPixmap(40, 38)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#9f7181"), 1.4))
    if kind == "温牛奶":
        p.setBrush(QColor("#fffaf4"))
        p.drawRoundedRect(QRectF(10, 11, 20, 24), 4, 4)
        p.setBrush(QColor("#b9d8cf"))
        p.drawRoundedRect(QRectF(13, 3, 14, 9), 2, 2)
        p.setBrush(QColor("#f0d9de"))
        p.drawEllipse(QRectF(16, 20, 8, 8))
    elif kind == "小饼干":
        p.setBrush(QColor("#f3d59b"))
        p.drawEllipse(QRectF(5, 4, 30, 30))
        p.setBrush(QColor("#a97766"))
        for x, y in ((12, 12), (24, 10), (18, 21), (26, 25), (10, 26)):
            p.drawEllipse(QRectF(x, y, 3, 3))
    else:
        p.setBrush(QColor("#f7cbd4"))
        p.drawRoundedRect(QRectF(5, 14, 30, 20), 3, 3)
        p.setBrush(QColor("#fff8ec"))
        p.drawRoundedRect(QRectF(5, 12, 30, 9), 3, 3)
        p.setBrush(QColor("#d88d9d"))
        p.drawEllipse(QRectF(15, 3, 10, 10))
    p.end()
    return QIcon(pix)


class Ribbon(QWidget):
    def __init__(self, owner, callback):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("芙眠眠 · 气泡菜单")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(STYLE)
        self.buttons = {}
        for key, text, color in (("clock", "时钟", "#fff3dc"), ("food", "喂食", "#eaf4ef"),
                                 ("settings", "设置", "#f9eaf0")):
            button = BubbleButton(key, text, color, self)
            button.clicked.connect(lambda checked=False, k=key: callback(k))
            self.buttons[key] = button

    def arrange(self, side, rect):
        self.setGeometry(rect)
        mask = QRegion()
        for index, button in enumerate(self.buttons.values()):
            button.move(index * 80 if side in ("top", "bottom") else 0,
                        0 if side in ("top", "bottom") else index * 76)
            mask |= QRegion(button.geometry())
        if QApplication.platformName() != "offscreen":
            self.setMask(mask)


def label(text, size=None, muted=False):
    widget = QLabel(text)
    widget.setWordWrap(True)
    widget.setStyleSheet(f"color: {'#a08791' if muted else INK};" + (f"font-size: {size}px;" if size else ""))
    return widget


class Panel(QWidget):
    def __init__(self, owner, title, subtitle, close):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("芙眠眠 · " + title)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        outer.addWidget(scroll)
        self.content = QWidget()
        scroll.setWidget(self.content)
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(20, 16, 20, 18)
        self.body.setSpacing(12)
        heading = QHBoxLayout()
        heading.addWidget(label(title, 20), 1)
        button = QPushButton("×")
        button.setAccessibleName("关闭面板")
        button.setFixedSize(30, 30)
        button.setStyleSheet("padding: 0; border: none; font-size: 20px; background: transparent;")
        button.clicked.connect(close)
        heading.addWidget(button)
        self.body.addLayout(heading)
        self.body.addWidget(label(subtitle, muted=True))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(90, 50, 65, 16))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(4, 5, -4, -2), 23, 23)
        p.setPen(QPen(QColor("#e5c7d1"), 1))
        p.setBrush(QColor("#fffaf6"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(8, 8, -8, -8), 20, 20)


class Speech(QWidget):
    def __init__(self, owner):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet(STYLE)
        self.text = label("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 13, 18, 20)
        layout.addWidget(self.text)
        self.setFixedWidth(230)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#e5c7d1"), 1))
        p.setBrush(QColor("#fffaf6"))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 10), 15, 15)


class BubbleUI(QObject):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.ribbon = Ribbon(pet, self.open_panel)
        self.panel = None
        self.panel_key = None
        self.speech = Speech(pet)
        self.deadline = None
        self._clock_label = self._remaining_label = None
        self._paused_here = False
        self._closed = False
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(350)
        self.hover_timer.timeout.connect(self.show_menu)
        self.leave_timer = QTimer(self)
        self.leave_timer.setSingleShot(True)
        self.leave_timer.setInterval(900)
        self.leave_timer.timeout.connect(self.hide_if_away)
        self.speech_timer = QTimer(self)
        self.speech_timer.setSingleShot(True)
        self.speech_timer.timeout.connect(self.speech.hide)
        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self.application_state)
        self.tray = None
        if QApplication.platformName() != "offscreen" and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(QIcon(pet.character.sprites.get("idle")), self)
            self.tray.setToolTip("芙眠眠 · 点击打开气泡菜单")
            self.tray.activated.connect(lambda reason: self.show_menu() if reason in (
                QSystemTrayIcon.Trigger, QSystemTrayIcon.Context, QSystemTrayIcon.DoubleClick) else None)
            self.tray.show()

    def application_state(self, state):
        if state == Qt.ApplicationInactive and self.panel is not None:
            self.hide_all()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if self.ribbon.isVisible() or self.panel is not None:
                self.hide_all()
                return True
        if event.type() == QEvent.MouseButtonPress and (self.ribbon.isVisible() or self.panel is not None):
            point = event.globalPosition().toPoint()
            if not self.contains(point):
                self.hide_all()
        return False

    def contains(self, point):
        return any(w is not None and w.isVisible() and w.frameGeometry().contains(point)
                   for w in (self.pet, self.ribbon, self.panel))

    def hover(self):
        if not self.pet._dragging and not self.ribbon.isVisible():
            self.hover_timer.start()

    def leave(self):
        self.hover_timer.stop()
        self.leave_timer.start()

    def hide_if_away(self):
        if self.panel is None and not self.contains(QCursor.pos()):
            self.hide_all()

    def show_menu(self):
        if self._closed or self.pet._dragging or not self.pet.isVisible() or self.pet._size_dialog:
            return
        self.hover_timer.stop()
        self.speech.hide()
        self.pet.character.interact()
        if not self._paused_here:
            self._paused_here = self.pet.character._timer.isActive()
            self.pet.character.pause()
        self.ribbon.show()
        self.reposition()
        self.ribbon.raise_()

    def close_panel(self):
        panel, self.panel = self.panel, None
        self.panel_key = None
        self._clock_label = self._remaining_label = None
        if panel:
            panel.hide()
            panel.deleteLater()

    def hide_all(self):
        self.speech.hide()
        self.speech_timer.stop()
        self.hover_timer.stop()
        self.leave_timer.stop()
        self.close_panel()
        self.ribbon.hide()
        if self._paused_here:
            self._paused_here = False
            if not self.pet._size_dialog and not self._closed:
                self.pet.character.interact()
                self.pet.character.resume()

    def open_panel(self, key):
        if key == self.panel_key:
            self.close_panel()
            return
        self.close_panel()
        self.show_menu()
        self.panel_key = key
        titles = {"food": ("点心时间", "概念预览 · 数值只在本次面板中演示"),
                  "clock": ("慢慢来", "看看时间，也给自己留一段休息。"),
                  "settings": ("陪伴设置", "调整成你喜欢的样子。")}
        self.panel = Panel(self.pet, *titles[key], self.close_panel)
        {"food": self.build_food, "clock": self.build_clock, "settings": self.build_settings}[key]()
        self.panel.body.addStretch()
        work = self.pet._current_screen().availableGeometry()
        self.panel.resize(min(306, work.width() - 16), min({"settings": 480, "food": 452, "clock": 340}[key], work.height() - 16))
        self.reposition()
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()
        self.tick()

    def build_food(self):
        body = self.panel.body
        self.food = "温牛奶"
        self.portions = 1
        body.addWidget(label("今天想吃点什么？", 14))
        choices = QHBoxLayout()
        self.food_buttons = {}
        for name in ("温牛奶", "小饼干", "草莓糕"):
            button = QToolButton()
            button.setText(name)
            button.setIcon(food_icon(name))
            button.setIconSize(QSize(40, 38))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setCheckable(True)
            button.setMinimumHeight(62)
            button.setStyleSheet("padding: 6px 3px;")
            button.setChecked(name == self.food)
            button.clicked.connect(lambda checked=False, n=name: self.select_food(n))
            self.food_buttons[name] = button
            choices.addWidget(button)
        body.addLayout(choices)
        self.portion_label = label("1 份", 16)
        self.portion_label.setAlignment(Qt.AlignCenter)
        row = QHBoxLayout()
        self.less, self.more = QPushButton("−"), QPushButton("＋")
        self.less.setAccessibleName("减少份数")
        self.more.setAccessibleName("增加份数")
        self.less.clicked.connect(lambda: self.change_portions(-1))
        self.more.clicked.connect(lambda: self.change_portions(1))
        row.addWidget(self.less)
        row.addWidget(self.portion_label, 1)
        row.addWidget(self.more)
        body.addLayout(row)
        self.change_portions(0)
        self.food_stats = []
        for name, value in (("饱腹感", 60), ("好心情", 80)):
            body.addWidget(label(name + " · 演示"))
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(value)
            progress.setTextVisible(False)
            progress.setFixedHeight(8)
            self.food_stats.append(progress)
            body.addWidget(progress)
        self.food_note = label("先选一份小点心吧。", muted=True)
        body.addWidget(self.food_note)
        preview = QPushButton("预览投喂")
        preview.setProperty("primary", True)
        preview.clicked.connect(self.preview_food)
        body.addWidget(preview)

    def select_food(self, name):
        self.food = name
        for key, button in self.food_buttons.items():
            button.setChecked(key == name)

    def change_portions(self, delta):
        self.portions = max(1, min(3, self.portions + delta))
        self.portion_label.setText(f"{self.portions} 份")
        self.less.setEnabled(self.portions > 1)
        self.more.setEnabled(self.portions < 3)

    def preview_food(self):
        for bar, increase in zip(self.food_stats, (8, 4)):
            bar.setValue(min(100, bar.value() + increase * self.portions))
        self.food_note.setText(f"{self.portions} 份{self.food}，收到啦。这里只演示效果，不保存养成数值。")
        self.speak("谢谢你的小点心～", 2600)

    def build_clock(self):
        body = self.panel.body
        self._clock_label = label("", 38)
        self._clock_label.setAlignment(Qt.AlignCenter)
        body.addWidget(self._clock_label)
        self._remaining_label = label("")
        self._remaining_label.setAlignment(Qt.AlignCenter)
        body.addWidget(self._remaining_label)
        row = QHBoxLayout()
        for minutes in (5, 15, 30):
            button = QPushButton(f"{minutes} 分钟")
            button.clicked.connect(lambda checked=False, n=minutes: self.start_timer(n))
            row.addWidget(button)
        body.addLayout(row)
        cancel = QPushButton("取消计时")
        cancel.clicked.connect(self.cancel_timer)
        body.addWidget(cancel)
        body.addWidget(label("到时会用气泡提醒。关闭面板后计时仍继续；退出桌宠后结束。", muted=True))

    def start_timer(self, minutes):
        self.deadline = time.monotonic() + minutes * 60
        self.tick()

    def cancel_timer(self):
        self.deadline = None
        self.tick()

    def build_settings(self):
        pet, body = self.pet, self.panel.body
        self.sleep_button = QPushButton("叫醒芙眠眠" if pet.character.state == State.SLEEP else "让她睡一会儿")
        self.sleep_button.clicked.connect(self.toggle_sleep)
        body.addWidget(self.sleep_button)
        size = QPushButton(f"调整大小 · {pet.settings.size // 2}%")
        size.clicked.connect(self.open_size)
        body.addWidget(size)
        for text, checked, callback in (
            ("像素清晰显示", pet.settings.pixelated, self.set_pixelated),
            ("自主走动", pet.character.wander_enabled, self.set_wander),
            ("靠近边缘时吸附", pet.settings.snap_to_edges, pet.set_snapping)):
            box = RowCheckBox(text)
            box.setChecked(checked)
            box.toggled.connect(callback)
            body.addWidget(box)
        reload_button = QPushButton("重新加载素材")
        reload_button.clicked.connect(self.reload_sprites)
        body.addWidget(reload_button)
        body.addWidget(label("芙眠眠 nemu · 0.1.2 试用版", muted=True))
        quit_button = QPushButton("退出桌宠")
        quit_button.clicked.connect(self.quit)
        body.addWidget(quit_button)

    def toggle_sleep(self):
        self.pet.character.toggle_sleep()
        self.sleep_button.setText("叫醒芙眠眠" if self.pet.character.state == State.SLEEP else "让她睡一会儿")

    def open_size(self):
        self.hide_all()
        self.pet.show_size_dialog()

    def set_pixelated(self, enabled):
        self.pet.settings.pixelated = enabled
        self.pet.update()
        self.pet.save_settings()

    def set_wander(self, enabled):
        self.pet.character.set_wandering(enabled)
        self.pet.save_settings()

    def reload_sprites(self):
        self.pet.reload_sprites()
        self.speak("素材重新读好啦。")

    def quit(self):
        self.pet.close()
        QApplication.quit()

    def speak(self, text, duration=2400):
        self.speech.text.setText(text)
        self.speech.adjustSize()
        self.position_speech()
        self.speech.show()
        self.speech.raise_()
        self.speech_timer.start(duration)

    def position_speech(self):
        body = self.pet.visible_content_rect().translated(self.pet.pos()).toAlignedRect()
        work = self.pet._current_screen().availableGeometry()
        # Try the free side when a secondary panel or ribbon occupies the top.
        menu = self.ribbon.geometry() if self.ribbon.isVisible() else body
        self.speech.move(panel_placement(body, menu.united(self.panel.geometry()) if self.panel else menu,
                                         self.speech.size(), work))

    def reposition(self):
        if self._closed:
            return
        body = self.pet.visible_content_rect().translated(self.pet.pos()).toAlignedRect()
        work = self.pet._current_screen().availableGeometry()
        side, rect = menu_placement(body, work)
        self.ribbon.arrange(side, rect)
        if self.panel:
            self.panel.resize(min(self.panel.width(), work.width() - 16),
                              min(self.panel.height(), work.height() - 16))
            self.panel.move(panel_placement(body, rect, self.panel.size(), work))
        if self.speech.isVisible():
            self.position_speech()

    def tick(self):
        if self._closed:
            return
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.deadline = None
            self.speak("时间到啦，休息一下吧。", 6500)
        if self._clock_label:
            self._clock_label.setText(time.strftime("%H:%M"))
            seconds = max(0, math.ceil(self.deadline - time.monotonic())) if self.deadline else None
            self._remaining_label.setText(f"还剩 {seconds // 60:02d}:{seconds % 60:02d}" if seconds is not None else "暂时没有计时")
        if self.ribbon.isVisible() and self.panel is None:
            if self.contains(QCursor.pos()):
                self.leave_timer.stop()
            elif not self.leave_timer.isActive():
                self.leave_timer.start()

    def shutdown(self):
        self._closed = True
        self.timer.stop()
        self.speech_timer.stop()
        self.hide_all()
        self.speech.hide()
        QApplication.instance().removeEventFilter(self)
        if self.tray:
            self.tray.hide()
