"""Small animated food selector and independent countdown surface."""
from PySide6.QtCore import (Property, QEasingCurve, QPoint, QRect, QRectF, Qt,
                            QPropertyAnimation, Signal)
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)
from pet.ui_geometry import inside

FOODS = ('温牛奶', '小饼干', '草莓糕')


class FoodCarousel(QWidget):
    selected = Signal(str)

    def __init__(self, icon_factory, parent=None):
        super().__init__(parent)
        self.icons = {name: icon_factory(name) for name in FOODS}
        self.index = 0
        self.direction = 0
        self._offset = 0.0
        self.setFixedHeight(84)
        self.setMinimumWidth(180)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName('点心选择：温牛奶；左右键切换')
        self.animation = QPropertyAnimation(self, b'offset', self)
        self.animation.setDuration(230)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.finished.connect(self.finish_pending)

    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(float, get_offset, set_offset)

    @property
    def current(self):
        return FOODS[self.index]

    def step(self, direction):
        self.finish_pending()
        self.direction = 1 if direction > 0 else -1
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(float(self.direction))
        self.animation.start()

    def finish_pending(self):
        if not self.direction:
            return
        self.animation.stop()
        self.index = (self.index + self.direction) % len(FOODS)
        self.direction = 0
        self._offset = 0.0
        self.setAccessibleName('点心选择：' + self.current + '；左右键切换')
        self.selected.emit(self.current)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setClipRect(self.rect())
        for relative in range(-2, 3):
            name = FOODS[(self.index + relative) % len(FOODS)]
            shift = relative - self._offset
            x = self.width() / 2 - 48 + shift * 108
            active = abs(shift) < .5
            p.setOpacity(.48 + .52 * max(0.0, 1.0 - abs(shift)))
            p.setPen(QPen(QColor('#d99bad' if active else '#ead5dc'), 1))
            p.setBrush(QColor('#f8e4eb' if active else '#fff7f4'))
            p.drawRoundedRect(QRectF(x, 3, 96, 77), 13, 13)
            self.icons[name].paint(p, QRect(round(x + 28), 10, 40, 38))
            p.setPen(QColor('#704d5b'))
            p.drawText(QRectF(x, 52, 96, 22), Qt.AlignCenter, name)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.step(-1 if event.key() == Qt.Key_Left else 1)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.position().x() < self.width() / 2 - 48:
            self.step(-1)
        elif event.position().x() > self.width() / 2 + 48:
            self.step(1)
        event.accept()


class TextClock(QWidget):
    def __init__(self, owner):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedSize(96, 36)
        font = QFont('Segoe UI')
        font.setPixelSize(22)
        font.setWeight(QFont.DemiBold)
        self.setFont(font)
        self.value = ''

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        path = QPainterPath()
        path.addText(0, 0, self.font(), self.value)
        bounds = path.boundingRect()
        p.translate(round(self.rect().center().x() - bounds.center().x()),
                    round(self.rect().center().y() - bounds.center().y()))
        p.strokePath(path, QPen(QColor('#704d5b'), 2.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.fillPath(path, QColor('#fffaf6'))


class CountdownWindow(QWidget):
    def __init__(self, owner, pause, cancel, style):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle('芙芙 · 独立计时器')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(style)
        self.setFixedSize(210, 120)
        self.cancel_callback = cancel
        self._drag = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 11, 16, 12)
        layout.setSpacing(4)
        heading = QHBoxLayout()
        self.caption = QLabel('小计时 · 可拖动')
        self.caption.setStyleSheet('font-size: 10px; color: #a08791;')
        heading.addWidget(self.caption, 1)
        close = QPushButton('×')
        close.setAccessibleName('取消并关闭计时器')
        close.setFixedSize(22, 22)
        close.setStyleSheet('padding: 0; border: none; background: transparent;')
        close.clicked.connect(cancel)
        heading.addWidget(close)
        layout.addLayout(heading)
        row = QHBoxLayout()
        self.digits = QLabel('00:00')
        self.digits.setStyleSheet('font-size: 26px; font-weight: 600;')
        row.addWidget(self.digits, 1)
        self.pause_button = QPushButton('暂停')
        self.pause_button.setStyleSheet('font-size: 11px; padding: 5px 8px;')
        self.pause_button.clicked.connect(pause)
        row.addWidget(self.pause_button)
        layout.addLayout(row)
        self.note = QLabel('芙芙会到屏幕中间提醒你。')
        self.note.setStyleSheet('font-size: 10px; color: #a08791;')
        layout.addWidget(self.note)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor('#e5c7d1'), 1))
        p.setBrush(QColor('#fffaf6'))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 16, 16)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag = None
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        self.move(inside(self.pos(), self.size(), screen.availableGeometry()))
        event.accept()

    def closeEvent(self, event):
        self.cancel_callback()
        event.accept()


def quick_action_icon(kind):
    pix = QPixmap(18, 18)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    if kind == 'sleep':
        outer, inner = QPainterPath(), QPainterPath()
        outer.addEllipse(QRectF(2, 2, 14, 14))
        inner.addEllipse(QRectF(7, 0, 13, 13))
        painter.fillPath(outer.subtracted(inner), QColor('#7b96b9'))
    else:
        painter.setPen(QPen(QColor('#c46b7b'), 1.8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(QRectF(3, 4, 12, 12), 45 * 16, 270 * 16)
        painter.drawLine(9, 2, 9, 9)
    painter.end()
    return QIcon(pix)
