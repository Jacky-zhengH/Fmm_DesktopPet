"""Transparent window with resizing, reload and current-monitor boundaries."""
import math
from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QRegion
from PySide6.QtWidgets import QApplication, QMenu, QWidget
from pet.character import State
from pet.bubble_ui import BubbleUI
from pet.ui_widgets import quick_action_icon
from pet.settings import MAX_SIZE, MIN_SIZE, SETTINGS_PATH, PetSettings
from pet.size_dialog import SizeDialog
from pet.placement import attach, constrain, nearest_surface, surfaces

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
        self._dock_edge = self.settings.dock_edge if self.settings.snap_to_edges else None
        self._dock_screen_name = self.settings.dock_screen
        self._input_rect = None
        self.setWindowTitle("芙眠眠 · 桌宠补完计划")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip("停留片刻打开气泡菜单 · 点击互动 · 拖动移动 · Ctrl+滚轮缩放")
        self._resize_canvas()
        character.wander_enabled = self.settings.wander
        character.auto_sleep_seconds = self.settings.auto_sleep_seconds
        character.frame_changed.connect(self._on_frame_changed)
        character.state_changed.connect(self._on_state_changed)
        character.walk_step.connect(self._on_walk_step)
        screen = QApplication.primaryScreen().availableGeometry()
        if self.settings.x is not None and self.settings.y is not None:
            self.move(self.settings.x, self.settings.y)
        else:
            self.move(screen.left() + screen.width() - self.width() - 60,
                      screen.top() + screen.height() - self.height() - 60)
        self._clamp_to_screen()
        for monitor in QApplication.screens():
            self._screen_added(monitor)
        QApplication.instance().screenRemoved.connect(self._clamp_to_screen)
        QApplication.instance().screenAdded.connect(self._screen_added)
        self._on_frame_changed()
        self.ui = BubbleUI(self)

    def _screen_added(self, screen):
        screen.availableGeometryChanged.connect(self._clamp_to_screen)
        screen.geometryChanged.connect(self._clamp_to_screen)
        screen.logicalDotsPerInchChanged.connect(self._clamp_to_screen)

    def _resize_canvas(self):
        self._padding = math.ceil(self._sprite_size * 0.08)
        side = self._sprite_size + self._padding * 2
        self.setFixedSize(side, side)

    def _current_screen(self):
        if self._dock_edge and not self._dragging and self._dock_screen_name:
            matches = [s for s in QApplication.screens() if s.name() == self._dock_screen_name]
            if len(matches) == 1:
                return matches[0]
        return QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()

    def _sync_bounds(self):
        rect = self._current_screen().geometry()
        visible = self.visible_content_rect()
        left, right = rect.left() - visible.left(), rect.right() + 1 - visible.right()
        if self._dock_edge in ("left", "right"):
            left = right = self.x()
        self.character.set_movement_bounds(left, right)
        self._walk_x = float(self.x())
        self.character.notify_x(self._walk_x)

    def _clamp_to_screen(self, *_):
        screen = self._current_screen()
        visible = self.visible_content_rect()
        self.move(constrain(self.pos(), visible, screen.geometry()))
        if self._dock_edge and not self._dragging:
            surface = next(item for item in surfaces(screen.geometry(), screen.availableGeometry())
                           if item.edge == self._dock_edge)
            self.move(attach(self.pos(), visible, screen.geometry(), surface))
            self._dock_screen_name = screen.name()
        self._sync_bounds()

    def _drawing_geometry(self, animated=True):
        ch = self.character
        pix = ch.current_sprite()
        bounds = ch.sprites.content_bounds(ch.state)
        desired_height = self._sprite_size * ch.sprites.reference_height_ratio()
        factor = min(desired_height / max(1, bounds.height()), self._sprite_size / max(1, bounds.width()))
        if animated:
            factor *= ch.scale
        x = self.width() / 2 - (bounds.left() + bounds.width() / 2) * factor
        hop = ch.hop_offset * self._sprite_size / 200 if animated else 0
        y = self.height() - self._padding - (bounds.top() + bounds.height()) * factor + hop
        return pix, QRectF(x, y, pix.width() * factor, pix.height() * factor), factor, bounds

    def visible_content_rect(self):
        _, target, factor, bounds = self._drawing_geometry(animated=False)
        return QRectF(target.x() + bounds.x() * factor, target.y() + bounds.y() * factor,
                      bounds.width() * factor, bounds.height() * factor)

    def _on_frame_changed(self):
        pix, target, factor, _ = self._drawing_geometry()
        actual = self.character.sprites.pixel_bounds(pix)
        visible = QRectF(target.x() + actual.x() * factor, target.y() + actual.y() * factor,
                         actual.width() * factor, actual.height() * factor)
        if self.character.sprite_facing and self.character.facing != self.character.sprite_facing:
            visible.moveLeft(self.width() - visible.right())
        # Restrict the native input/clip rectangle to the visible body. In
        # particular the transparent padding below the feet cannot eat taskbar clicks.
        region = visible.adjusted(1e-7, 1e-7, -1e-7, -1e-7).toAlignedRect().intersected(self.rect())
        if self.character.state == State.SLEEP:
            scale = self._sprite_size / 200
            zzz = QRectF(self.width() - self._padding - 80 * scale, 0, 80 * scale, 110 * scale)
            region = region.united(zzz.toAlignedRect().intersected(self.rect()))
        if region != self._input_rect:
            self._input_rect = region
            if QApplication.platformName() != "offscreen":
                self.setMask(QRegion(region))
        self.update()

    def _on_state_changed(self, _):
        if not self._dragging:
            self._clamp_to_screen()
        self._on_frame_changed()

    def finish_drag(self):
        self._dock_edge = None
        self._dock_screen_name = None
        self._clamp_to_screen()
        screen = self._current_screen()
        if self.settings.snap_to_edges:
            surface = nearest_surface(self.pos(), self.visible_content_rect(),
                                      screen.geometry(), screen.availableGeometry())
            if surface:
                self._dock_edge, self._dock_screen_name = surface.edge, screen.name()
                self._clamp_to_screen()
        self._on_frame_changed()
        self.save_settings()

    def set_snapping(self, enabled):
        self.settings.snap_to_edges = bool(enabled)
        if not enabled:
            self._dock_edge = self._dock_screen_name = None
        self.character.interact()
        self._clamp_to_screen()
        self.save_settings()

    def set_pet_size(self, size):
        size = max(MIN_SIZE, min(MAX_SIZE, int(size)))
        anchor = self.pos() + QPoint(self.width() // 2, self.height() - self._padding)
        self._sprite_size = self.settings.size = size
        self._resize_canvas()
        self.move(anchor - QPoint(self.width() // 2, self.height() - self._padding))
        self.character.interact()
        self._clamp_to_screen()
        self._on_frame_changed()

    def paintEvent(self, event):
        ch = self.character
        pix, target, _, _ = self._drawing_geometry()
        if pix is None or pix.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, not self.settings.pixelated)
        painter.save()
        if ch.sprite_facing and ch.facing != ch.sprite_facing:
            painter.translate(self.width(), 0)
            painter.scale(-1, 1)
        painter.drawPixmap(target, pix, QRectF(pix.rect()))
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
            self.ui.cancel_arrival(retry=True)
            self.ui.hide_all()
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
            self._dock_edge = self._dock_screen_name = None
            self.character.set_dragging(True)
        if self._dragging:
            self.move(position - self._drag_offset)
            self._sync_bounds()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self.character.set_dragging(False)
                self._dragging = False
                self.finish_drag()
            else:
                self.character.pet()
                self.ui.speak("嗯？我在这里呀。")
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
        rect = self._current_screen().geometry()
        visible = self.visible_content_rect()
        self._walk_x = max(rect.left() - visible.left(), min(self._walk_x + dx,
                           rect.right() + 1 - visible.right()))
        self.move(round(self._walk_x), self.y())
        self.character.notify_x(self._walk_x)

    def reload_sprites(self):
        self.character.sprites.reload()
        self.character.reload_sprites()
        self.character.interact()
        self._clamp_to_screen()
        self._on_frame_changed()

    def save_settings(self):
        if self.settings_path is None:
            return True
        self.settings.x, self.settings.y = self.x(), self.y()
        self.settings.wander = self.character.wander_enabled
        self.settings.auto_sleep_seconds = self.character.auto_sleep_seconds
        self.settings.dock_edge = self._dock_edge
        self.settings.dock_screen = self._dock_screen_name
        return self.settings.save(self.settings_path)

    def enterEvent(self, event):
        if hasattr(self, "ui"):
            self.ui.hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, "ui"):
            self.ui.leave()
        super().leaveEvent(event)

    def moveEvent(self, event):
        if hasattr(self, "ui"):
            self.ui.reposition()
        super().moveEvent(event)

    def resizeEvent(self, event):
        if hasattr(self, "ui"):
            self.ui.reposition()
        super().resizeEvent(event)

    def build_quick_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet('QMenu { background: #fffaf6; color: #704d5b; border: 1px solid #e5c7d1; padding: 4px; }'
                           'QMenu::item { padding: 7px 18px 7px 8px; }'
                           'QMenu::separator { height: 1px; background: #ead1d6; margin: 4px; }'
                           'QMenu::item:selected { background: #f5d7e0; }')
        sleep = menu.addAction(quick_action_icon('sleep'), '叫醒芙芙' if self.character.state == State.SLEEP else '让芙芙睡觉')
        menu.addSeparator()
        quit_action = menu.addAction(quick_action_icon('quit'), '退出桌宠')
        return menu, sleep, quit_action

    def contextMenuEvent(self, event):
        self.ui.cancel_arrival(retry=True)
        self.ui.hide_all()
        self.ui._quick_menu = True
        self.character.interact()
        sleeping = self.character.state == State.SLEEP
        self.ui.sync_hold()
        menu, sleep, quit_action = self.build_quick_menu()
        try:
            selected = menu.exec(event.globalPos())
            if selected == sleep:
                self.character.interact()
                self.character._enter_state(State.IDLE if sleeping else State.SLEEP)
            elif selected == quit_action:
                self.ui.quit()
        finally:
            self.ui._quick_menu = False
            self.ui.sync_hold()
            menu.deleteLater()
        event.accept()

    def closeEvent(self, event):
        self.ui.shutdown()
        self.save_settings()
        super().closeEvent(event)
