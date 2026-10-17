"""Behavioral UI checks using real Qt controls and screen geometry."""
import os
from pathlib import Path
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox
from pet.character import Character, State
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.ui_geometry import menu_placement, panel_placement
from pet.window import PetWindow

APP = QApplication.instance() or QApplication([])


class BubbleGeometryTests(unittest.TestCase):
    def test_menu_flips_at_edges_and_uses_top_in_a_narrow_screen(self):
        work = QRect(0, 0, 1200, 800)
        side, rect = menu_placement(QRect(1000, 580, 170, 200), work)
        self.assertEqual(side, 'left')
        self.assertTrue(work.contains(rect))
        side, rect = menu_placement(QRect(70, 200, 160, 180), QRect(0, 0, 300, 600))
        self.assertEqual(side, 'top')
        self.assertTrue(QRect(0, 0, 300, 600).contains(rect))

    def test_corners_and_negative_coordinates_keep_controls_visible(self):
        for origin in (QPoint(), QPoint(-1920, -120)):
            work = QRect(origin, QSize(1200, 800))
            for point in (QPoint(0, 0), QPoint(1000, 0), QPoint(0, 600), QPoint(1000, 600)):
                body = QRect(point + origin, QSize(170, 200))
                with self.subTest(origin=origin, point=point):
                    side, menu = menu_placement(body, work)
                    self.assertTrue(work.contains(menu))
                    self.assertFalse(menu.intersects(body))
                    panel = QRect(panel_placement(body, menu, QSize(306, 452), work), QSize(306, 452))
                    self.assertTrue(work.contains(panel))
                    self.assertFalse(panel.intersects(body))
                    self.assertFalse(panel.intersects(menu))


class BubbleUITests(unittest.TestCase):
    def setUp(self):
        self.character = Character(SpriteLibrary())
        self.pet = PetWindow(self.character, PetSettings(wander=False, auto_sleep_seconds=0), None)
        self.pet.show()
        self.ui = self.pet.ui
        APP.processEvents()

    def tearDown(self):
        self.character.pause()
        self.pet.close()
        self.pet.deleteLater()
        self.character.deleteLater()
        APP.processEvents()

    def test_hover_opens_without_right_click_and_leaving_resumes(self):
        APP.sendEvent(self.pet, QEvent(QEvent.Enter))
        QTest.qWait(420)
        self.assertTrue(self.ui.ribbon.isVisible())
        self.assertFalse(self.character._timer.isActive())
        with patch('pet.bubble_ui.QCursor.pos', return_value=QPoint(-99999, -99999)):
            self.ui.hide_if_away()
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.character._timer.isActive())

    def test_click_bubbles_switches_one_secondary_panel_and_escape_resumes(self):
        self.ui.show_menu()
        self.assertFalse(self.character._timer.isActive())
        QTest.mouseClick(self.ui.ribbon.buttons['food'], Qt.LeftButton)
        first = self.ui.panel
        self.assertTrue(first.isVisible())
        QTest.mouseClick(self.ui.ribbon.buttons['clock'], Qt.LeftButton)
        self.assertFalse(first.isVisible())
        self.assertEqual(self.ui.panel_key, 'clock')
        QTest.keyClick(self.ui.panel, Qt.Key_Escape)
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.character._timer.isActive())

    def test_food_selection_limits_preview_and_reset_without_saving_pet_values(self):
        self.ui.open_panel('food')
        QTest.mouseClick(self.ui.food_buttons['小饼干'], Qt.LeftButton)
        for _ in range(5):
            QTest.mouseClick(self.ui.more, Qt.LeftButton)
        self.assertEqual((self.ui.food, self.ui.portions), ('小饼干', 3))
        self.assertFalse(self.ui.more.isEnabled())
        self.ui.preview_food()
        self.assertEqual([b.value() for b in self.ui.food_stats], [84, 92])
        self.assertTrue(self.ui.speech.isVisible())
        self.assertIn('不保存', self.ui.food_note.text())
        self.ui.open_panel('settings')
        self.ui.open_panel('food')
        self.assertEqual([b.value() for b in self.ui.food_stats], [60, 80])
        self.assertEqual(self.ui.portions, 1)
        self.assertFalse(hasattr(self.pet.settings, 'hunger'))

    def test_settings_operate_original_controls_and_open_size_panel(self):
        self.ui.open_panel('settings')
        boxes = {box.text(): box for box in self.ui.panel.findChildren(QCheckBox)}
        for name in ('像素清晰显示', '自主走动', '靠近边缘时吸附'):
            QTest.mouseClick(boxes[name], Qt.LeftButton)
        self.assertFalse(self.pet.settings.pixelated)
        self.assertTrue(self.character.wander_enabled)
        self.assertFalse(self.pet.settings.snap_to_edges)
        self.ui.toggle_sleep()
        self.assertEqual(self.character.state, State.SLEEP)
        self.ui.open_size()
        self.assertIsNotNone(self.pet._size_dialog)
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        self.pet._size_dialog.reject()
        self.assertTrue(self.character._timer.isActive())

    def test_timer_continues_after_closing_panel_and_expires_once(self):
        self.ui.open_panel('clock')
        self.ui.start_timer(5)
        self.assertIn('05:00', self.ui._remaining_label.text())
        self.ui.hide_all()
        self.assertIsNotNone(self.ui.deadline)
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.assertIsNone(self.ui.deadline)
        self.assertIn('时间到', self.ui.speech.text.text())
        self.ui.speech.hide()
        self.ui.tick()
        self.assertFalse(self.ui.speech.isVisible())

    def test_drag_hides_controls_and_keeps_original_drag_and_snap_behavior(self):
        self.ui.open_panel('food')
        QTest.mousePress(self.pet, Qt.LeftButton, pos=QPoint(100, 100))
        QTest.mouseMove(self.pet, QPoint(130, 120))
        self.assertTrue(self.pet._dragging)
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        QTest.mouseRelease(self.pet, Qt.LeftButton, pos=QPoint(130, 120))
        self.assertFalse(self.pet._dragging)
        self.assertEqual(self.character.state, State.IDLE)

    def test_panels_fit_small_screen_and_move_when_monitor_changes(self):
        full = QRect(-640, 0, 640, 480)
        monitor = SimpleNamespace(geometry=lambda:full, availableGeometry=lambda:full,
                                  name=lambda:'small-monitor')
        with patch.object(self.pet, '_current_screen', return_value=monitor):
            self.pet.move(-230, 240)
            self.ui.open_panel('settings')
            APP.processEvents()
            self.assertTrue(full.contains(self.ui.panel.geometry()))
            self.assertTrue(full.contains(self.ui.ribbon.geometry()))
            self.pet.set_pet_size(400)
            self.assertTrue(full.contains(self.ui.panel.geometry()))
            self.assertTrue(full.contains(self.ui.ribbon.geometry()))


if __name__ == '__main__':
    unittest.main()
