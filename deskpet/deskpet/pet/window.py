"""Transparent window with resizing, reload and current-monitor boundaries."""
import math
from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget
from pet.character import State
from pet.settings import MAX_SIZE, MIN_SIZE, SETTINGS_PATH, PetSettings
from pet.size_dialog import SizeDialog

CLICK_THRESHOLD = 6


class PetWindow(QWidget):
    def __init__(self, character, settings=None, settings_path=SETTINGS_PATH):
        super().__init__()
        self.character = character
        self.settings = settings or PetSettings()
        self.settings_path = settings_path
        self._sprite_size = self.settings.size = max(MIN_SIZE, min(MAX_SIZE, self.settings.size))
        self._size_dialog = None
        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._dragging = False
        self._wheel_remainder = 0
        self._walk_x = 0.0
        self.setWindowTitle("芙眠眠 · 桌宠补完计划")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip("左键互动 · 拖动移动 · 右键调整大小 · Ctrl+滚轮快捷缩放")
        self._resize_canvas()
        character.wander_enabled = self.settings.wander
        character.auto_sleep_seconds = self.settings.auto_sleep_seconds
        character.frame_changed.connect(self.update)
        character.walk_step.connect(self._on_walk_step)
        screen = QApplication.primaryScreen().availableGeometry()
        if self.settings.x is not None and self.settings.y is not None:
            self.move(self.settings.x, self.settings.y)
        else:
            self.move(screen.left() + screen.width() - self.width() - 60,
                      screen.top() + screen.height() - self.height() - 60)
        self._clamp_to_screen()
        for monitor in QApplication.screens():
            monitor.availableGeometryChanged.connect(self._clamp_to_screen)
        QApplication.instance().screenRemoved.connect(self._clamp_to_screen)
        QApplication.instance().screenAdded.connect(self._screen_added)

    def _screen_added(self, screen):
        screen.availableGeometryChanged.connect(self._clamp_to_screen)

    def _resize_canvas(self):
        self._padding = math.ceil(self._sprite_size * 0.08)
        side = self._sprite_size + self._padding * 2
        self.setFixedSize(side, side)

    def _current_screen(self):
        return QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()

    def _sync_bounds(self):
        self.character.set_screen_rect(self._current_screen().availableGeometry(), self.width())
        self._walk_x = float(self.x())
        self.character.notify_x(self._walk_x)

    def _clamp_to_screen(self, *_):
        rect = self._current_screen().availableGeometry()
        x = max(rect.left(), min(self.x(), rect.left() + max(0, rect.width() - self.width())))
        y = max(rect.top(), min(self.y(), rect.top() + max(0, rect.height() - self.height())))
        self.move(x, y)
        self._sync_bounds()

    def set_pet_size(self, size):
        size = max(MIN_SIZE, min(MAX_SIZE, int(size)))
        anchor = self.pos() + QPoint(self.width() // 2, self.height())
        self._sprite_size = self.settings.size = size
        self._resize_canvas()
        self.move(anchor - QPoint(self.width() // 2, self.height()))
        self.character.interact()
        self._clamp_to_screen()
        self.update()

    def paintEvent(self, event):
        ch = self.character
        pix = ch.current_sprite()
        if pix is None or pix.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, not self.settings.pixelated)
        factor = self._sprite_size / max(pix.width(), pix.height())
        width, height = pix.width() * factor * ch.scale, pix.height() * factor * ch.scale
        y = self.height() - self._padding - height + ch.hop_offset * self._sprite_size / 200
        painter.save()
        if ch.sprite_facing and ch.facing != ch.sprite_facing:
            painter.translate(self.width(), 0)
            painter.scale(-1, 1)
        painter.drawPixmap(QRectF((self.width() - width) / 2, y, width, height), pix, QRectF(pix.rect()))
        painter.restore()
        if ch.state == State.SLEEP:
            factor = self._sprite_size / 200
            offset = ch.zzz_offset
            painter.setPen(QColor(120, 120, 160, 220))
            font = QFont()
            font.setBold(True)
            font.setPixelSize(max(8, round(22 * factor)))
            painter.setFont(font)
            painter.drawText(round(self.width() - self._padding - 64 * factor),
                             round(self._padding + (56 - offset) * factor), "Z")
            font.setPixelSize(max(6, round(15 * factor)))
            painter.setFont(font)
            painter.drawText(round(self.width() - self._padding - 44 * factor),
                             round(self._padding + (66 - offset * 0.55) * factor), "z")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.character.interact()
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            return
        position = event.globalPosition().toPoint()
        if not self._dragging and (position - self._press_pos).manhattanLength() > CLICK_THRESHOLD:
            self._dragging = True
            self.character.set_dragging(True)
        if self._dragging:
            self.move(position - self._drag_offset)
            self._sync_bounds()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._clamp_to_screen()
                self.character.set_dragging(False)
            else:
                self.character.pet()
            self._dragging = False
            event.accept()

    def wheelEvent(self, event):
        if not event.modifiers() & Qt.ControlModifier:
            self._wheel_remainder = 0
            event.ignore()
            return
        self._wheel_remainder += event.angleDelta().y()
        steps = math.trunc(self._wheel_remainder / 120)
        self._wheel_remainder -= steps * 120
        if steps:
            self.set_pet_size(self._sprite_size + steps * 20)
        event.accept()

    def show_size_dialog(self):
        if self._size_dialog is not None:
            self._size_dialog.raise_()
            self._size_dialog.activateWindow()
            return
        previous_size = self.settings.size
        previous_position = self.pos()
        self.character.interact()
        self.character.pause()
        dialog = self._size_dialog = SizeDialog(previous_size, self)
        dialog.preview_size.connect(self.set_pet_size)

        def rollback():
            self.set_pet_size(previous_size)
            self.move(previous_position)
            self._clamp_to_screen()

        def finished(_):
            self._size_dialog = None
            self.character.interact()
            self.character.resume()
            dialog.deleteLater()

        dialog.rejected.connect(rollback)
        dialog.accepted.connect(self.save_settings)
        dialog.finished.connect(finished)
        dialog.open()
        # Keep the controls away from the always-on-top pet, reserving room for
        # the largest live preview so a slider drag never moves its own panel.
        dialog.adjustSize()
        screen = self._current_screen().availableGeometry()
        maximum_canvas = MAX_SIZE + 2 * math.ceil(MAX_SIZE * 0.08)
        anchor_x = self.x() + self.width() // 2
        left = anchor_x - maximum_canvas // 2 - dialog.frameGeometry().width() - 16
        if left < screen.left():
            left = anchor_x + maximum_canvas // 2 + 16
        left = max(screen.left(), min(left, screen.right() - dialog.frameGeometry().width() + 1))
        top = max(screen.top(), min(self.y(), screen.bottom() - dialog.frameGeometry().height() + 1))
        dialog.move(left, top)
        dialog.raise_()
        dialog.activateWindow()

    def _on_walk_step(self, dx):
        rect = self._current_screen().availableGeometry()
        self._walk_x = max(rect.left(), min(self._walk_x + dx,
                           rect.left() + max(0, rect.width() - self.width())))
        self.move(round(self._walk_x), self.y())
        self.character.notify_x(self._walk_x)

    def reload_sprites(self):
        self.character.sprites.reload()
        self.character.reload_sprites()
        self.character.interact()
        self.update()

    def save_settings(self):
        if self.settings_path is None:
            return True
        self.settings.x, self.settings.y = self.x(), self.y()
        self.settings.wander = self.character.wander_enabled
        self.settings.auto_sleep_seconds = self.character.auto_sleep_seconds
        return self.settings.save(self.settings_path)

    def contextMenuEvent(self, event):
        ch = self.character
        ch.interact()
        ch.pause()
        menu = QMenu(self)
        sleep = menu.addAction("叫醒" if ch.state == State.SLEEP else "睡觉")
        size_action = menu.addAction("调整大小…")
        pixelated = menu.addAction("像素清晰显示")
        pixelated.setCheckable(True)
        pixelated.setChecked(self.settings.pixelated)
        wander = menu.addAction("自主走动")
        wander.setCheckable(True)
        wander.setChecked(ch.wander_enabled)
        reload_action = menu.addAction("重新加载素材")
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        try:
            selected = menu.exec(event.globalPos())
            if selected == sleep:
                ch.toggle_sleep()
            elif selected == size_action:
                self.show_size_dialog()
            elif selected == pixelated:
                self.settings.pixelated = pixelated.isChecked()
                self.update()
            elif selected == wander:
                ch.set_wandering(wander.isChecked())
            elif selected == reload_action:
                self.reload_sprites()
            elif selected == quit_action:
                self.close()
                QApplication.quit()
        finally:
            ch.interact()
            if self._size_dialog is None:
                ch.resume()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
