"""Small companion controls; food values are an explicit, in-memory UI demo."""
import math
import time
from datetime import date
from PySide6.QtCore import (QEvent, QObject, QPoint, QRectF, QSize, Qt, QTimer,
                            QPropertyAnimation, QEasingCurve, QTime, Signal)
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRegion
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox,
                              QHBoxLayout, QLabel, QPushButton, QProgressBar,
                              QScrollArea, QSystemTrayIcon, QToolButton, QTimeEdit, QVBoxLayout, QWidget)
from pet.character import State
from pet.version import VERSION
from pet.ui_geometry import arc_offsets, inside, menu_placement, panel_placement, speech_placement
from pet.ui_widgets import CountdownWindow, FoodCarousel, TextClock

INK = "#704d5b"
STYLE = """
QWidget { color: #704d5b; font-family: 'Microsoft YaHei UI', 'Microsoft YaHei'; font-size: 12px; }
QLabel { background: transparent; border: none; }
QPushButton, QToolButton { background: #fff5f3; border: 1px solid #ead1d6; border-radius: 11px; padding: 8px 12px; }
QPushButton:hover, QToolButton:hover { background: #fbe5e9; border-color: #d995aa; }
QPushButton:pressed, QPushButton:checked, QToolButton:checked { background: #f5d7e0; border-color: #d995aa; }
QPushButton:disabled { color: #b8a9ae; }
QTimeEdit { background: #fff5f3; border: 1px solid #ead1d6; border-radius: 8px; padding: 5px; }
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
    hovered = Signal(bool)

    def __init__(self, kind, text, tint, parent):
        super().__init__(parent)
        self.kind, self.tint = kind, tint
        self.setText(text)
        self.setAccessibleName(text)
        self.setToolTip("" if kind == "clock" else text)
        self.setFixedSize(50, 58)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#d69bad" if self.underMouse() or self.hasFocus() else "#ead1d6"), 1.4))
        p.setBrush(QColor("#f6dce5" if self.isDown() else self.tint))
        p.drawEllipse(QRectF(7, 2, 36, 36))
        draw_symbol(p, self.kind, QRectF(15, 10, 20, 20))
        p.setPen(QColor(INK))
        font = p.font()
        font.setPixelSize(10)
        p.setFont(font)
        p.drawText(QRectF(0, 40, 50, 17), Qt.AlignCenter, self.text())

    def enterEvent(self, event):
        self.hovered.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered.emit(False)
        super().leaveEvent(event)


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
            button.move(arc_offsets(side)[index])
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
        self.subtitle = label(subtitle, muted=True)
        self.body.addWidget(self.subtitle)

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
        self.compact = False
        self.tail_side = 'bottom'
        self.tail_offset = 102
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 17, 22, 20)
        layout.setSpacing(2)
        layout.addWidget(self.text)
        self.setFixedWidth(216)

    def set_message(self, text, compact=False):
        self.compact = compact
        self.text.setText(text)
        self.text.ensurePolished()
        if compact:
            self.layout().setContentsMargins(18, 13, 18, 16)
            width = max(160, min(216, self.text.fontMetrics().horizontalAdvance(text) + 40))
        else:
            self.layout().setContentsMargins(22, 17, 22, 20)
            width = 216
        self.setFixedWidth(width)
        self.adjustSize()

    def point_to(self, target):
        point = target - self.pos()
        body = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        if point.y() >= self.height():
            self.tail_side = 'bottom'
        elif point.y() < 0:
            self.tail_side = 'top'
        elif point.x() < self.width() / 2:
            self.tail_side = 'left'
        else:
            self.tail_side = 'right'
        if self.tail_side in ('top', 'bottom'):
            self.tail_offset = max(body.left() + 23, min(point.x(), body.right() - 23))
        else:
            self.tail_offset = max(body.top() + 19, min(point.y(), body.bottom() - 19))
        self.update()

    def outline(self):
        body = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        shape, tail = QPainterPath(), QPainterPath()
        shape.addRoundedRect(body, 15, 15)
        offset = self.tail_offset
        if self.tail_side in ('top', 'bottom'):
            edge = body.top() if self.tail_side == 'top' else body.bottom()
            tip = 1 if self.tail_side == 'top' else self.height() - 1
            tail.moveTo(offset - 7, edge)
            tail.lineTo(offset, tip)
            tail.lineTo(offset + 7, edge)
        else:
            edge = body.left() if self.tail_side == 'left' else body.right()
            tip = 1 if self.tail_side == 'left' else self.width() - 1
            tail.moveTo(edge, offset - 7)
            tail.lineTo(tip, offset)
            tail.lineTo(edge, offset + 7)
        tail.closeSubpath()
        return shape.united(tail)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#e5c7d1"), 1))
        p.setBrush(QColor("#fffaf6"))
        p.drawPath(self.outline())


class BubbleUI(QObject):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.ribbon = Ribbon(pet, self.open_panel)
        self.panel = None
        self.panel_key = None
        self.speech = Speech(pet)
        self.deadline = None
        self._remaining_label = None
        self._paused_seconds = None
        self._pending_alarm = False
        self._alarm_sleeping = False
        self._alarm_holding = False
        self._greeting_holding = False
        self._alarm_origin = None
        self._alarm_returning = False
        self._countdown_positioned = False
        self._quick_menu = False
        self._arrival_animation = QPropertyAnimation(pet, b'pos', self)
        self._arrival_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._arrival_animation.finished.connect(self.finish_alarm)
        self.clock_hint = TextClock(pet)
        self._clock_hovered = False
        self.ribbon.buttons['clock'].hovered.connect(self.clock_hover)
        self.countdown = CountdownWindow(pet, self.pause_timer, self.cancel_timer, STYLE)
        pet.character.state_changed.connect(self.refresh_context)
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
        self.speech_timer.timeout.connect(self.finish_speech)
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self.startup_greeting)
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
        if event.type() == QEvent.KeyPress:
            if self.panel_key == 'food' and event.key() in (Qt.Key_Left, Qt.Key_Right):
                self.carousel.step(-1 if event.key() == Qt.Key_Left else 1)
                return True
            if event.key() == Qt.Key_Escape and (self.ribbon.isVisible() or self.panel is not None):
                self.hide_all()
                return True
        if event.type() == QEvent.MouseButtonPress and (self.ribbon.isVisible() or self.panel is not None):
            if not self.contains(event.globalPosition().toPoint()):
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
        if (self._closed or self.pet._dragging or not self.pet.isVisible() or self.pet._size_dialog
                or self._arrival_animation.state() == QPropertyAnimation.Running):
            return
        self.hover_timer.stop()
        self.pet.character.interact()
        self.ribbon.show()
        self.sync_hold()
        self.reposition()
        self.ribbon.raise_()

    def close_panel(self):
        panel, self.panel = self.panel, None
        self.panel_key = None
        self._remaining_label = None
        if panel:
            panel.hide()
            panel.deleteLater()

    def hide_all(self):
        self._clock_hovered = False
        self.finish_speech()
        self.speech_timer.stop()
        self.clock_hint.hide()
        self.hover_timer.stop()
        self.leave_timer.stop()
        self.close_panel()
        self.ribbon.hide()
        self.sync_hold()

    def open_panel(self, key):
        if key == self.panel_key:
            self.close_panel()
            return
        self.close_panel()
        self.show_menu()
        self.panel_key = key
        titles = {'food': ('点心时间', '概念预览 · 不保存数据'),
                  'clock': ('定时器', '我来替你记着时间。'),
                  'settings': ('陪伴设置', '调整成你喜欢的样子。')}
        self.panel = Panel(self.pet, *titles[key], self.close_panel)
        if key != 'settings':
            self.panel.body.setContentsMargins(14, 12, 14, 12)
            self.panel.body.setSpacing(8)
            self.panel.subtitle.setStyleSheet('font-size: 10px; color: #a08791;')
        {'food': self.build_food, 'clock': self.build_clock, 'settings': self.build_settings}[key]()
        self.panel.body.addStretch()
        self.refresh_context()
        work = self.pet._current_screen().availableGeometry()
        widths = {'food': 250, 'clock': 264, 'settings': 306}
        heights = {'food': 360, 'clock': 300, 'settings': 480}
        self.panel.resize(min(widths[key], work.width() - 16), min(heights[key], work.height() - 16))
        self.reposition()
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()
        self.tick()

    def build_food(self):
        body = self.panel.body
        self.food = '温牛奶'
        self.portions = 1
        self.carousel = FoodCarousel(food_icon)
        self.carousel.selected.connect(self.select_food)
        body.addWidget(self.carousel)
        row = QHBoxLayout()
        self.previous_food, self.next_food = QPushButton('‹'), QPushButton('›')
        self.previous_food.setAccessibleName('上一种点心')
        self.next_food.setAccessibleName('下一种点心')
        self.previous_food.clicked.connect(lambda: self.carousel.step(-1))
        self.next_food.clicked.connect(lambda: self.carousel.step(1))
        self.less, self.more = QPushButton('−'), QPushButton('＋')
        self.less.setAccessibleName('减少份数')
        self.more.setAccessibleName('增加份数')
        self.less.clicked.connect(lambda: self.change_portions(-1))
        self.more.clicked.connect(lambda: self.change_portions(1))
        self.portion_label = label('1 份')
        self.portion_label.setAlignment(Qt.AlignCenter)
        for widget in (self.previous_food, self.less, self.portion_label, self.more, self.next_food):
            if isinstance(widget, QPushButton):
                widget.setFixedSize(28, 28)
                widget.setStyleSheet('padding: 0; font-size: 15px;')
            row.addWidget(widget)
        body.addLayout(row)
        self.change_portions(0)
        self.food_stats = []
        for name, value in (('饱腹感', 60), ('好心情', 80)):
            row = QHBoxLayout()
            title = label(name + ' · 预览', muted=True)
            title.setStyleSheet('font-size: 10px; color: #a08791;')
            row.addWidget(title)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(value)
            progress.setTextVisible(False)
            progress.setFixedHeight(5)
            self.food_stats.append(progress)
            row.addWidget(progress, 1)
            body.addLayout(row)
        self.food_note = label('选一份小点心吧。', muted=True)
        self.food_note.setFixedHeight(28)
        self.food_note.setStyleSheet('font-size: 11px; color: #a08791;')
        body.addWidget(self.food_note)
        self.feed_button = QPushButton('预览投喂')
        self.feed_button.setProperty('primary', True)
        self.feed_button.clicked.connect(self.preview_food)
        body.addWidget(self.feed_button)

    def select_food(self, name):
        self.food = name

    def change_portions(self, delta):
        self.portions = max(1, min(3, self.portions + delta))
        self.portion_label.setText(f"{self.portions} 份")
        self.less.setEnabled(self.portions > 1)
        self.more.setEnabled(self.portions < 3)

    def preview_food(self):
        self.carousel.finish_pending()
        sleeping = self.pet.character.state == State.SLEEP
        if sleeping:
            self.food_note.setText('先替她留着这份' + self.food + '。')
            self.speak('呼…点心留到醒来再吃吧。', 3200)
        else:
            for bar, increase in zip(self.food_stats, (8, 4)):
                bar.setValue(min(100, bar.value() + increase * self.portions))
            self.food_note.setText(f'收到 {self.portions} 份{self.food}啦。')
            self.speak('谢谢你的小点心～', 2600)

    def build_clock(self):
        body = self.panel.body
        self._remaining_label = label('')
        body.addWidget(self._remaining_label)
        row = QHBoxLayout()
        for minutes in (5, 15, 30):
            button = QPushButton(f'{minutes} 分钟')
            button.setStyleSheet('padding: 6px 8px; font-size: 11px;')
            button.clicked.connect(lambda checked=False, n=minutes: self.start_timer(n))
            row.addWidget(button)
        body.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label('自定义'))
        self.custom_time = QTimeEdit(QTime(0, 10, 0))
        self.custom_time.setDisplayFormat('HH:mm:ss')
        self.custom_time.setAccessibleName('自定义时分秒')
        row.addWidget(self.custom_time, 1)
        self.custom_start = QPushButton('开始')
        self.custom_start.setStyleSheet('padding: 6px 8px;')
        self.custom_start.clicked.connect(self.start_custom_timer)
        row.addWidget(self.custom_start)
        body.addLayout(row)
        cancel = QPushButton('取消计时')
        cancel.clicked.connect(self.cancel_timer)
        body.addWidget(cancel)
        body.addWidget(label('启动后菜单自动收起。到时芙芙来到中央提醒，再走回原位。', muted=True))

    def start_timer(self, minutes):
        self.start_seconds(minutes * 60)

    def cancel_timer(self):
        self.deadline = None
        self._paused_seconds = None
        self._pending_alarm = False
        self.cancel_arrival()
        self.countdown.hide()
        if self._alarm_holding:
            self.finish_speech()
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
        body.addWidget(label(f"芙眠眠 nemu · {VERSION}", muted=True))
        quit_button = QPushButton("退出桌宠")
        quit_button.clicked.connect(self.quit)
        body.addWidget(quit_button)

    def toggle_sleep(self):
        self.pet.character.toggle_sleep()

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

    def speak(self, text, duration=2400, *, compact=False):
        self.speech.set_message(text, compact)
        self.position_speech()
        self.speech.show()
        self.speech.raise_()
        self.speech_timer.start(duration)

    def position_speech(self):
        body = self.pet.visible_content_rect().translated(self.pet.pos()).toAlignedRect()
        work = self.pet._current_screen().availableGeometry()
        obstacles = [self.panel.geometry()] if self.panel else []
        if self.clock_hint.isVisible():
            obstacles.append(self.clock_hint.geometry())
        if self.ribbon.isVisible():
            obstacles.extend(button.geometry().translated(self.ribbon.pos()) for button in self.ribbon.buttons.values())
        self.speech.move(speech_placement(body, self.speech.size(), work, obstacles, allow_distant=self.speech.compact))
        self.speech.point_to(QPoint(body.center().x(), body.top() + round(body.height() * .3)))

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
        if self.clock_hint.isVisible():
            self.position_clock()
        if self.speech.isVisible():
            self.position_speech()

    def tick(self):
        if self._closed:
            return
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.deadline = None
            self._alarm_sleeping = self.pet.character.state == State.SLEEP
            self._pending_alarm = True
        if (self._pending_alarm and not self._quick_menu and self.pet.character.state != State.DRAG and not self.pet._size_dialog
                and QApplication.mouseButtons() == Qt.NoButton):
            self.begin_alarm()
        seconds = self.remaining_seconds()
        text = self.format_seconds(seconds)
        if self.countdown.isVisible():
            self.countdown.digits.setText(text)
            self.countdown.pause_button.setText('继续' if self._paused_seconds is not None else '暂停')
        if self._remaining_label:
            self._remaining_label.setText(('已暂停 · ' if self._paused_seconds is not None else '还剩 ') + text
                                          if self.deadline is not None or self._paused_seconds is not None else '选择一段时间')
        if self.clock_hint.isVisible():
            self.clock_hint.value = time.strftime('%H:%M')
            self.clock_hint.update()
        if self.ribbon.isVisible() and self.panel is None:
            if self.contains(QCursor.pos()):
                self.leave_timer.stop()
            elif not self.leave_timer.isActive():
                self.leave_timer.start()

    def shutdown(self):
        self._closed = True
        self.timer.stop()
        self.startup_timer.stop()
        self.cancel_arrival()
        self.hide_all()
        self.countdown.hide()
        self.clock_hint.hide()
        QApplication.instance().removeEventFilter(self)
        if self.tray:
            self.tray.hide()

    def sync_hold(self):
        held = (self.ribbon.isVisible() or self._quick_menu or self._alarm_holding or self._greeting_holding
                or self._arrival_animation.state() == QPropertyAnimation.Running)
        self.pet.character.hold_movement(held and not self._closed)

    def finish_speech(self):
        self.speech_timer.stop()
        self.speech.hide()
        self._greeting_holding = False
        returning = self._alarm_holding and self._alarm_origin is not None and not self._closed
        self._alarm_holding = False
        if returning:
            self._alarm_returning = True
            self.start_alarm_motion(self._alarm_origin[0])
        else:
            self.sync_hold()

    def refresh_context(self, *_):
        sleeping = self.pet.character.state == State.SLEEP
        if self.panel_key == 'food':
            self.feed_button.setText('先留一份（预览）' if sleeping else '预览投喂')
            self.panel.subtitle.setText('睡着啦 · 点心留到醒来' if sleeping else '概念预览 · 不保存数据')
        elif self.panel_key == 'clock':
            self.panel.subtitle.setText('她先眯一会儿，到点再来提醒。' if sleeping else '我来替你记着时间。')
        elif self.panel_key == 'settings':
            self.sleep_button.setText('叫醒芙眠眠' if sleeping else '让她睡一会儿')
        self.countdown.note.setText('她先眯着，到点会来提醒。' if sleeping else '芙芙会到屏幕中间提醒你。')

    def startup_greeting(self):
        if self._closed:
            return
        today = date.today()
        if (today.month, today.day) != (10, 24) or self.pet.settings.last_greeting_date == today.isoformat():
            return
        if (self.pet._dragging or self.pet.character.state == State.DRAG or self.pet._size_dialog
                or self._quick_menu or self.ribbon.isVisible() or self.panel is not None
                or self.speech.isVisible() or self._pending_alarm or self._alarm_holding
                or self._arrival_animation.state() == QPropertyAnimation.Running):
            self.startup_timer.start(1000)
            return
        # Save before showing, so closing and reopening does not repeat the greeting.
        self.pet.settings.last_greeting_date = today.isoformat()
        self.pet.save_settings()
        self._greeting_holding = True
        self.pet.character.interact()
        self.pet.character._enter_state(State.HAPPY)
        self.sync_hold()
        self.speak('芙眠眠nemu，生日快乐！愿新的一岁，天天开心、夜夜好梦～', 7500)

    def clock_hover(self, visible):
        if not visible or not self.ribbon.isVisible():
            self._clock_hovered = False
            self.clock_hint.hide()
            return
        self.clock_hint.value = time.strftime('%H:%M')
        self.clock_hint.setAccessibleName('当前时间 ' + self.clock_hint.value)
        self.position_clock()
        self.clock_hint.show()
        self.clock_hint.raise_()
        if self._clock_hovered:
            return
        self._clock_hovered = True
        if self.speech.isVisible() or self._alarm_holding:
            return
        self.pet.character.interact()
        today = date.today()
        weekday = '一二三四五六日'[today.weekday()]
        self.speak(f'今天是{today.month}月{today.day}日，星期{weekday}。', compact=True)

    def position_clock(self):
        button = self.ribbon.buttons['clock']
        anchor = button.geometry().translated(self.ribbon.pos())
        size = self.clock_hint.size()
        work = self.pet._current_screen().availableGeometry()
        candidates = [QPoint(anchor.center().x() - size.width() // 2, anchor.top() - size.height() - 6),
                      QPoint(anchor.center().x() - size.width() // 2, anchor.bottom() + 6),
                      QPoint(anchor.right() + 8, anchor.center().y() - size.height() // 2),
                      QPoint(anchor.left() - size.width() - 8, anchor.center().y() - size.height() // 2),
                      QPoint(anchor.center().x() - size.width() // 2, self.ribbon.y() - size.height() - 6),
                      QPoint(anchor.center().x() - size.width() // 2, self.ribbon.geometry().bottom() + 6)]
        body = self.pet.visible_content_rect().translated(self.pet.pos()).toAlignedRect()
        obstacles = [b.geometry().translated(self.ribbon.pos()) for b in self.ribbon.buttons.values()]
        if self.panel:
            obstacles.append(self.panel.geometry())
        def score(point):
            rect = QRectF(point.x(), point.y(), size.width(), size.height()).toAlignedRect()
            overlap = rect.intersected(body)
            area = overlap.width() * overlap.height() * 10
            for obstacle in obstacles:
                overlap = rect.intersected(obstacle)
                area += overlap.width() * overlap.height()
            return area
        self.clock_hint.move(min((inside(p, size, work) for p in candidates), key=score))

    @staticmethod
    def format_seconds(seconds):
        # Windows clock subtraction can land a few ulps above a whole second.
        seconds = max(0, math.ceil(round(seconds, 6)))
        return (f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}' if seconds >= 3600
                else f'{seconds // 60:02d}:{seconds % 60:02d}')

    def remaining_seconds(self):
        return max(0, self.deadline - time.monotonic()) if self.deadline is not None else (self._paused_seconds or 0)

    def start_custom_timer(self):
        value = self.custom_time.time()
        seconds = value.hour() * 3600 + value.minute() * 60 + value.second()
        if seconds == 0:
            self._remaining_label.setText('请设置至少 1 秒。')
            return
        self.start_seconds(seconds)

    def start_seconds(self, seconds):
        self.cancel_timer()
        self.hide_all()
        self.deadline = time.monotonic() + max(1, seconds)
        work = self.pet._current_screen().availableGeometry()
        if not self._countdown_positioned or not work.contains(self.countdown.geometry()):
            self._countdown_positioned = True
            self.countdown.move(work.right() - self.countdown.width() - 20, work.top() + 24)
        self.countdown.show()
        self.countdown.raise_()
        sleeping = self.pet.character.state == State.SLEEP
        self.speak('呼…我先眯着，到点再来提醒你。' if sleeping else '好，计时开始啦。', 2800)
        self.tick()

    def pause_timer(self):
        if self.deadline is not None:
            self._paused_seconds = self.remaining_seconds()
            self.deadline = None
        elif self._paused_seconds is not None:
            self.deadline = time.monotonic() + self._paused_seconds
            self._paused_seconds = None
        self.tick()

    def begin_alarm(self):
        self._pending_alarm = False
        self.hide_all()
        self.countdown.hide()
        self._alarm_sleeping = self.pet.character.state == State.SLEEP
        # Capture the departure location, including taskbar/screen docking.
        self._alarm_origin = (QPoint(self.pet.pos()), self.pet._dock_edge, self.pet._dock_screen_name)
        self._alarm_returning = False
        work = self.pet._current_screen().availableGeometry()
        self.pet._dock_edge = self.pet._dock_screen_name = None
        self.pet.character._enter_state(State.WALK)
        body = self.pet.visible_content_rect()
        target = work.center() - QPoint(round(body.center().x()), round(body.center().y()))
        self.start_alarm_motion(target)

    def start_alarm_motion(self, target):
        ch = self.pet.character
        ch.scripted_motion = True
        ch.hold_movement(True)
        ch._enter_state(State.WALK)
        distance = math.hypot(target.x() - self.pet.x(), target.y() - self.pet.y())
        ch.facing = 1 if target.x() >= self.pet.x() else -1
        self._arrival_animation.setStartValue(self.pet.pos())
        self._arrival_animation.setEndValue(target)
        self._arrival_animation.setDuration(max(700, min(3500, round(distance / 260 * 1000))))
        self._arrival_animation.start()

    def finish_alarm(self):
        self.pet.character.scripted_motion = False
        if self._alarm_returning:
            _, self.pet._dock_edge, self.pet._dock_screen_name = self._alarm_origin
            self._alarm_origin = None
            self._alarm_returning = False
            self.pet.character._enter_state(State.SLEEP if self._alarm_sleeping else State.IDLE)
            # Recheck bounds in case display geometry changed during the reminder.
            self.pet._clamp_to_screen()
            self.sync_hold()
            return
        self._alarm_holding = True
        self.pet.character._enter_state(State.SLEEP if self._alarm_sleeping else State.IDLE)
        self.sync_hold()
        self.speak('唔…时间到了，提醒完我再眯一会儿。' if self._alarm_sleeping else '时间到啦，起来活动一下吧。', 6500)

    def cancel_arrival(self, retry=False):
        moving = self._arrival_animation.state() == QPropertyAnimation.Running
        if not moving and not self._alarm_holding:
            return
        # Retry an interrupted outbound reminder. Once delivered, manual movement wins.
        self._pending_alarm = retry and moving and not self._alarm_returning
        self._arrival_animation.stop()
        self.speech_timer.stop()
        self.speech.hide()
        self._alarm_holding = False
        self._alarm_returning = False
        self._alarm_origin = None
        self.pet.character.scripted_motion = False
        self.pet.character._enter_state(State.SLEEP if self._alarm_sleeping else State.IDLE)
        self.sync_hold()
