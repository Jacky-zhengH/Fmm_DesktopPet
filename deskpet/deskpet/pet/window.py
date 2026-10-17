"""桌宠窗口：透明背景、无边框、置顶；左键拖动/点击互动；右键菜单（睡觉/退出）。"""
from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from pet.character import SPRITE_FACING, WALK_SPRITE_FACING, State
from pet.sprites import CANVAS_SIZE

CLICK_THRESHOLD = 6  # 位移超过此像素算拖动，否则算点击


class PetWindow(QWidget):
    def __init__(self, character, size: int = CANVAS_SIZE):
        super().__init__()
        self.character = character
        self.setFixedSize(size, size)
        self.setWindowFlags(
            Qt.FramelessWindowHint      # 无边框
            | Qt.WindowStaysOnTopHint   # 置顶
            | Qt.Tool                   # 不出现在任务栏
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景

        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._dragging = False

        character.frame_changed.connect(self.update)
        character.walk_step.connect(self._on_walk_step)

        # 初始位置：屏幕右下角；同步给角色用于漫游边界
        screen = QApplication.primaryScreen().availableGeometry()
        character.set_screen_rect(screen)
        self.move(screen.right() - size - 60, screen.bottom() - size - 60)
        character.set_position(self.x())

    # -------------------------------------------------------------- paint
    def paintEvent(self, event):
        ch = self.character
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        pix = ch.current_sprite()
        if pix is None:  # DRAG_MODE="none"：拖拽时不绘制任何内容
            p.end()
            return
        # 走路素材带方向性（单独朝向配置）；其他状态默认不镜像（正面素材）
        facing_ref = WALK_SPRITE_FACING if ch.state == State.WALK else SPRITE_FACING
        if facing_ref != 0 and ch.facing != facing_ref:
            pix = pix.transformed(QTransform().scale(-1, 1))

        s = ch.scale
        w, h = pix.width() * s, pix.height() * s
        # 底部对齐 + 跳跃/颠簸位移
        y = self.height() - h + ch.hop_offset
        p.drawPixmap(QRectF((self.width() - w) / 2, y, w, h),
                     pix, QRectF(pix.rect()))

        if ch.state == State.SLEEP:  # 漂浮 Zzz
            off = ch.zzz_offset
            p.setPen(QColor(120, 120, 160, 220))
            f = QFont()
            f.setBold(True)
            f.setPixelSize(22)
            p.setFont(f)
            p.drawText(self.width() - 64, 56 - off, "Z")
            f.setPixelSize(15)
            p.setFont(f)
            p.drawText(self.width() - 44, 66 - off * 0.55, "z")

        p.end()

    # -------------------------------------------------------------- mouse
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._dragging = False
            e.accept()

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton):
            return
        gp = e.globalPosition().toPoint()
        if not self._dragging and (gp - self._press_pos).manhattanLength() > CLICK_THRESHOLD:
            self._dragging = True
            self.character.set_dragging(True)
        if self._dragging:
            self.move(gp - self._drag_offset)
            self.character.notify_x(self.x())
        e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self._dragging:
                self.character.set_dragging(False)
            else:
                self.character.pet()  # 未拖动的点击 = 互动/唤醒
            self._dragging = False
            e.accept()

    # -------------------------------------------------------------- walk
    def _on_walk_step(self, dx: int):
        g = QApplication.primaryScreen().availableGeometry()
        nx = max(g.left(), min(self.x() + dx, g.right() - self.width()))
        self.move(nx, self.y())
        self.character.notify_x(nx)

    # -------------------------------------------------------------- menu
    def contextMenuEvent(self, e):
        ch = self.character
        menu = QMenu(self)
        act_sleep = menu.addAction("叫醒" if ch.state == State.SLEEP else "睡觉")
        menu.addSeparator()
        act_quit = menu.addAction("退出")

        act = menu.exec(e.globalPos())
        if act == act_sleep:
            ch.toggle_sleep()
        elif act == act_quit:
            QApplication.quit()
