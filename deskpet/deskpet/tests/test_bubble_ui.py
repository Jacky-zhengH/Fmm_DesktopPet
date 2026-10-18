"""Behavioral UI checks using real Qt controls and screen geometry."""
import os
from pathlib import Path
import sys
import time
import tempfile
from datetime import date
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTime, QPropertyAnimation
from PySide6.QtTest import QTest
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QApplication, QCheckBox
from pet.character import Character, State
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.ui_geometry import arc_offsets, menu_placement, panel_placement
from pet.window import PetWindow

APP = QApplication.instance() or QApplication([])


class BubbleGeometryTests(unittest.TestCase):
    def test_menu_flips_at_edges_and_uses_top_in_a_narrow_screen(self):
        work = QRect(0, 0, 1200, 800)
        side, rect = menu_placement(QRect(1000, 580, 170, 200), work)
        self.assertEqual(side, 'left')
        self.assertTrue(work.contains(rect))
        side, rect = menu_placement(QRect(70, 200, 160, 180), QRect(0, 0, 300, 600))
        self.assertIn(side, ('top', 'bottom'))
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
    def test_four_directions_and_arc_offsets(self):
        work = QRect(0, 0, 1200, 800)
        cases = {'right': QRect(0, 300, 170, 180), 'left': QRect(1020, 300, 170, 180),
                 'bottom': QRect(500, 0, 170, 180), 'top': QRect(500, 610, 170, 180)}
        for expected, body in cases.items():
            side, rect = menu_placement(body, work)
            self.assertEqual(side, expected)
            a, b, c = arc_offsets(side)
            self.assertNotEqual(b.x(), a.x()) if side in ('left', 'right') else self.assertNotEqual(b.y(), a.y())
            self.assertTrue(work.contains(rect))



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
        self.assertTrue(self.character._timer.isActive())
        self.assertTrue(self.character.movement_held)
        with patch('pet.bubble_ui.QCursor.pos', return_value=QPoint(-99999, -99999)):
            self.ui.hide_if_away()
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.character._timer.isActive())

    def test_click_bubbles_switches_one_secondary_panel_and_escape_resumes(self):
        self.ui.show_menu()
        self.assertTrue(self.character._timer.isActive())
        self.assertTrue(self.character.movement_held)
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
        QTest.mouseClick(self.ui.next_food, Qt.LeftButton)
        self.assertEqual(self.ui.carousel.animation.state(), QPropertyAnimation.Running)
        QTest.qWait(270)
        for _ in range(5):
            QTest.mouseClick(self.ui.more, Qt.LeftButton)
        self.assertEqual((self.ui.food, self.ui.portions), ('小饼干', 3))
        self.assertFalse(self.ui.more.isEnabled())
        self.ui.preview_food()
        self.assertEqual([b.value() for b in self.ui.food_stats], [84, 92])
        self.assertTrue(self.ui.speech.isVisible())
        self.assertIn('不保存', self.ui.panel.subtitle.text())
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
        self.assertEqual('05:00', self.ui.countdown.digits.text())
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.ui.countdown.isVisible())
        self.ui.hide_all()
        self.assertIsNotNone(self.ui.deadline)
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.assertIsNone(self.ui.deadline)
        self.assertEqual(self.character.state, State.WALK)
        self.assertTrue(self.character.scripted_motion)
        self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
        self.assertFalse(self.character.scripted_motion)
        self.assertIn('时间到', self.ui.speech.text.text())
        center = self.pet.visible_content_rect().translated(self.pet.pos()).center()
        target = self.pet._current_screen().availableGeometry().center()
        self.assertAlmostEqual(center.x(), target.x(), delta=1)
        self.assertAlmostEqual(center.y(), target.y(), delta=1)
        self.ui.speech.hide()
        self.ui.tick()
        self.assertFalse(self.ui.speech.isVisible())

    def test_reminder_returns_to_departure_position_and_restores_docking(self):
        for edge, sleeping in ((None, False), ('bottom', False), ('left', True)):
            with self.subTest(edge=edge, sleeping=sleeping):
                self.pet._dock_edge = edge
                self.pet._dock_screen_name = self.pet._current_screen().name() if edge else None
                self.character._enter_state(State.SLEEP if sleeping else State.IDLE)
                self.pet.move(70, 60)
                self.pet._clamp_to_screen()
                origin = QPoint(self.pet.pos())
                dock_screen = self.pet._dock_screen_name
                self.ui.start_seconds(30)
                # The return location is captured at expiry, not when setting the timer.
                if edge is None:
                    self.pet.move(origin + QPoint(35, 20))
                    origin = QPoint(self.pet.pos())
                self.ui.deadline = time.monotonic() - 1
                self.ui.tick()
                self.assertIsNone(self.pet._dock_edge)
                self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
                self.assertTrue(self.ui._alarm_holding)
                self.assertTrue(self.ui.speech.isVisible())
                self.ui.speech_timer.timeout.emit()
                self.assertFalse(self.ui.speech.isVisible())
                self.assertTrue(self.character.scripted_motion)
                self.assertEqual(self.character.state, State.WALK)
                self.assertEqual(self.ui._arrival_animation.endValue(), origin)
                self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
                self.assertEqual(self.pet.pos(), origin)
                self.assertEqual((self.pet._dock_edge, self.pet._dock_screen_name), (edge, dock_screen))
                self.assertEqual(self.character.state, State.SLEEP if sleeping else State.IDLE)
                self.assertFalse(self.character.scripted_motion)
                self.assertFalse(self.character.movement_held)
                self.assertIsNone(self.ui._alarm_origin)
                self.ui.tick()
                self.assertFalse(self.ui.speech.isVisible())

    def test_drag_after_reminder_or_during_return_overrides_return_position(self):
        for returning in (False, True):
            with self.subTest(returning=returning):
                self.ui.start_seconds(30)
                self.ui.deadline = time.monotonic() - 1
                self.ui.tick()
                self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
                if returning:
                    self.ui.finish_speech()
                QTest.mousePress(self.pet, Qt.LeftButton, pos=QPoint(80, 80))
                QTest.mouseMove(self.pet, QPoint(110, 100))
                QTest.mouseRelease(self.pet, Qt.LeftButton, pos=QPoint(110, 100))
                placed = QPoint(self.pet.pos())
                self.ui.finish_speech()
                self.ui.tick()
                self.assertEqual(self.pet.pos(), placed)
                self.assertFalse(self.ui._pending_alarm)
                self.assertIsNone(self.ui._alarm_origin)
                self.assertFalse(self.character.scripted_motion)

    def test_new_timer_cancels_previous_return_and_closes_menus(self):
        self.ui.start_seconds(30)
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
        self.ui.open_panel('clock')
        self.ui.start_seconds(60)
        self.ui.finish_speech()
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.ui.countdown.isVisible())
        self.assertAlmostEqual(self.ui.remaining_seconds(), 60, delta=1)
        self.assertIsNone(self.ui._alarm_origin)
        self.assertFalse(self.character.scripted_motion)
        self.assertFalse(self.ui._pending_alarm)

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


    def test_menu_keeps_breathing_sleep_motion_and_blink_timer_alive(self):
        self.ui.show_menu()
        self.assertTrue(self.character._timer.isActive())
        self.assertTrue(self.character.movement_held)
        for state in (State.IDLE, State.SLEEP):
            self.character._enter_state(state)
            self.character._phase = 0
            before = self.character.scale
            self.character._last_tick = 1
            with patch.object(self.character, '_clock', return_value=2):
                self.character._tick()
            self.assertNotAlmostEqual(self.character.scale, before)
            self.assertEqual(self.character.state, state)
        self.assertNotEqual(self.character.zzz_offset, 0)
        self.assertTrue(self.character._timer.isActive())

    def test_clock_hover_is_spoken_by_pet_and_does_not_open_panel(self):
        self.ui.show_menu()
        APP.sendEvent(self.ui.ribbon.buttons['clock'], QEvent(QEvent.Enter))
        self.assertTrue(self.ui.clock_hint.isVisible())
        self.assertRegex(self.ui.clock_hint.value, r'^\d{2}:\d{2}$')
        self.assertIsNone(self.ui.panel)
        self.assertEqual(self.ui.clock_hint.grab().toImage().pixelColor(0, 0).alpha(), 0)
        self.assertIs(self.ui.clock_hint.parentWidget(), self.ui.speech)
        self.assertFalse(self.ui.clock_hint.isWindow())
        self.assertTrue(self.ui.speech.isVisible())
        APP.sendEvent(self.ui.ribbon.buttons['clock'], QEvent(QEvent.Leave))
        self.assertTrue(self.ui.speech.isVisible())
        self.ui.finish_speech()
        self.assertFalse(self.ui.clock_hint.isVisible())

    def test_clock_uses_larger_outlined_text_and_fits_screen_edges(self):
        self.pet.move(100, 200)
        self.ui.show_menu()
        self.ui.clock_hover(True)
        self.assertEqual(self.ui.clock_hint.font().pixelSize(), 22)
        image = self.ui.clock_hint.grab().toImage()
        colors = [image.pixelColor(x, y) for x in range(image.width()) for y in range(image.height())]
        self.assertTrue(any(c.alpha() > 200 and c.lightness() > 230 for c in colors))
        self.assertTrue(any(c.alpha() > 200 and c.lightness() < 150 for c in colors))
        self.assertTrue(all(image.pixelColor(x, 0).alpha() == 0 for x in range(image.width())))
        for point in (QPoint(0, 0), QPoint(0, 500), QPoint(600, 0), QPoint(600, 500)):
            self.pet.move(point)
            self.ui.reposition()
            self.assertTrue(self.pet._current_screen().availableGeometry().contains(self.ui.speech.geometry()))
            clock = QRect(self.ui.clock_hint.mapToGlobal(QPoint()), self.ui.clock_hint.size())
            self.assertTrue(self.ui.speech.geometry().contains(clock))

    def test_speech_tail_points_to_pet_from_all_four_sides_and_follows_movement(self):
        speech = self.ui.speech
        self.ui.speak('今天也要好好休息呀。')
        speech.move(300, 200)
        for target, expected in ((QPoint(400, 400), 'bottom'), (QPoint(400, 100), 'top'),
                                 (QPoint(100, 220), 'left'), (QPoint(650, 220), 'right')):
            speech.point_to(target)
            self.assertEqual(speech.tail_side, expected)
            bounds = speech.outline().boundingRect()
            if expected == 'bottom':
                self.assertEqual(bounds.bottom(), speech.height() - 1)
            elif expected == 'top':
                self.assertEqual(bounds.top(), 1)
            elif expected == 'left':
                self.assertEqual(bounds.left(), 1)
            else:
                self.assertEqual(bounds.right(), speech.width() - 1)
        self.pet.move(100, 280)
        self.ui.reposition()
        old = speech.pos()
        self.pet.move(self.pet.pos() + QPoint(80, 0))
        self.ui.reposition()
        self.assertEqual(speech.pos() - old, QPoint(80, 0))

    def test_normal_speech_replaces_clock_header_in_the_same_bubble(self):
        self.ui.show_menu()
        self.ui.clock_hover(True)
        self.assertTrue(self.ui.clock_hint.isVisible())
        self.ui.speak('谢谢你的小点心～')
        self.assertFalse(self.ui.clock_hint.isVisible())
        self.assertTrue(self.ui.speech.isVisible())
        self.assertEqual(self.ui.speech.text.text(), '谢谢你的小点心～')
        self.ui.clock_hover(True)
        self.assertEqual(self.ui.speech.text.text(), '谢谢你的小点心～')

    def test_clock_reports_local_date_without_replacing_active_speech(self):
        self.ui.show_menu()
        for today, text in ((date(2026, 10, 18), '今天是10月18日，星期日。'),
                            (date(2027, 1, 1), '今天是1月1日，星期五。')):
            self.ui.finish_speech()
            with patch('pet.bubble_ui.date') as calendar:
                calendar.today.return_value = today
                self.ui.clock_hover(True)
            self.assertEqual(self.ui.speech.text.text(), text)
            self.assertTrue(self.ui.speech.isVisible())
            self.assertIsNone(self.ui.panel)
        self.ui.speak('正在提醒，请稍等。')
        self.ui.clock_hover(True)
        self.assertEqual(self.ui.speech.text.text(), '正在提醒，请稍等。')

    def test_startup_greeting_persists_across_restart_and_can_run_next_year(self):
        root = Path(__file__).resolve().parent / '.tmp'
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            path = Path(directory) / 'settings.json'
            self.pet.settings_path = path
            with patch('pet.bubble_ui.date') as calendar:
                calendar.today.return_value = date(2026, 10, 24)
                self.ui.startup_greeting()
                self.assertEqual(self.character.state, State.HAPPY)
                self.assertEqual(self.character.current_sprite().cacheKey(), self.character.sprites.get('happy').cacheKey())
                self.assertTrue(self.character.movement_held)
                self.assertTrue(self.ui.speech.isVisible())
                self.assertIn('生日快乐', self.ui.speech.text.text())
                self.assertEqual(PetSettings.load(path).last_greeting_date, '2026-10-24')
                self.ui.finish_speech()
                self.assertFalse(self.character.movement_held)
                self.ui.startup_greeting()
                self.assertFalse(self.ui.speech.isVisible())
                second_character = Character(SpriteLibrary())
                second = PetWindow(second_character, PetSettings.load(path), path)
                try:
                    second.show()
                    second.ui.startup_greeting()
                    self.assertFalse(second.ui.speech.isVisible())
                    calendar.today.return_value = date(2027, 10, 24)
                    second.ui.startup_greeting()
                    self.assertTrue(second.ui.speech.isVisible())
                    self.assertEqual(PetSettings.load(path).last_greeting_date, '2027-10-24')
                finally:
                    second_character.pause()
                    second.close()
                    second.deleteLater()
                    second_character.deleteLater()
            self.pet.settings_path = None

    def test_startup_greeting_skips_other_dates_and_defers_during_interaction(self):
        with patch('pet.bubble_ui.date') as calendar:
            for today in (date(2026, 10, 23), date(2026, 10, 25), date(2027, 1, 1)):
                calendar.today.return_value = today
                self.ui.startup_greeting()
                self.assertFalse(self.ui.speech.isVisible())
                self.assertIsNone(self.pet.settings.last_greeting_date)
            calendar.today.return_value = date(2026, 10, 24)
            self.ui.open_panel('clock')
            self.ui.startup_greeting()
            self.assertTrue(self.ui.startup_timer.isActive())
            self.assertIsNone(self.pet.settings.last_greeting_date)
            self.assertEqual(self.ui.panel_key, 'clock')
            self.ui.hide_all()
            self.ui.startup_greeting()
            self.assertTrue(self.ui.speech.isVisible())
            self.assertIsNone(self.ui.panel)
            self.pet.close()
            self.assertFalse(self.ui.startup_timer.isActive())

    def test_custom_time_zero_validation_and_separate_pause_resume_cancel(self):
        self.ui.open_panel('clock')
        self.ui.custom_time.setTime(QTime(0, 0, 0))
        QTest.mouseClick(self.ui.custom_start, Qt.LeftButton)
        self.assertIsNone(self.ui.deadline)
        self.assertIn('至少', self.ui._remaining_label.text())
        self.assertIsNotNone(self.ui.panel)
        self.assertTrue(self.ui.ribbon.isVisible())
        self.ui.custom_time.setTime(QTime(1, 2, 3))
        QTest.mouseClick(self.ui.custom_start, Qt.LeftButton)
        self.assertAlmostEqual(self.ui.remaining_seconds(), 3723, delta=1)
        self.assertIsNone(self.ui.panel)
        self.assertFalse(self.ui.ribbon.isVisible())
        self.assertTrue(self.ui.countdown.isVisible())
        self.ui.hide_all()
        self.assertTrue(self.ui.countdown.isVisible())
        QTest.mouseClick(self.ui.countdown.pause_button, Qt.LeftButton)
        self.assertIsNone(self.ui.deadline)
        paused = self.ui.remaining_seconds()
        self.ui.tick()
        self.assertEqual(self.ui.remaining_seconds(), paused)
        QTest.mouseClick(self.ui.countdown.pause_button, Qt.LeftButton)
        self.assertIsNotNone(self.ui.deadline)
        self.ui.countdown.close()
        self.assertIsNone(self.ui.deadline)
        self.assertIsNone(self.ui._paused_seconds)
        self.assertFalse(self.ui.countdown.isVisible())

    def test_sleep_food_is_left_for_later_and_timer_returns_to_sleep(self):
        self.character._enter_state(State.SLEEP)
        self.ui.open_panel('food')
        before = [bar.value() for bar in self.ui.food_stats]
        QTest.mouseClick(self.ui.feed_button, Qt.LeftButton)
        self.assertEqual(before, [bar.value() for bar in self.ui.food_stats])
        self.assertEqual(self.character.state, State.SLEEP)
        self.assertIn('醒来', self.ui.speech.text.text())
        self.ui.open_panel('clock')
        self.ui.start_seconds(30)
        self.assertEqual(self.character.state, State.SLEEP)
        self.assertIn('眯', self.ui.speech.text.text())
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.assertEqual(self.character.state, State.WALK)
        self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
        self.assertEqual(self.character.state, State.SLEEP)
        self.assertIn('再眯', self.ui.speech.text.text())

    def test_speech_stays_near_pet_with_large_side_panel(self):
        self.pet.move(400, 300)
        self.ui.open_panel('food')
        self.ui.preview_food()
        speech = self.ui.speech.geometry()
        body = self.pet.visible_content_rect().translated(self.pet.pos()).toAlignedRect()
        gap = min(abs(speech.bottom() - body.top()), abs(speech.right() - body.left()),
                  abs(speech.left() - body.right()), abs(speech.top() - body.bottom()))
        self.assertLessEqual(gap, 12)
        self.assertLess(abs(speech.center().x() - body.center().x()), 250)
        old_size = self.ui.panel.size()
        for _ in range(3):
            self.ui.preview_food()
        APP.processEvents()
        self.assertEqual(self.ui.panel.size(), old_size)

    def test_carousel_keyboard_cycles_and_commits_pending_slide_before_feeding(self):
        self.ui.open_panel('food')
        QTest.keyClick(self.ui.carousel, Qt.Key_Left)
        self.assertEqual(self.ui.carousel.animation.state(), QPropertyAnimation.Running)
        self.ui.preview_food()
        self.assertEqual(self.ui.food, '草莓糕')
        QTest.keyClick(self.ui.carousel, Qt.Key_Right)
        QTest.qWait(270)
        self.assertEqual(self.ui.food, '温牛奶')

    def test_alarm_waits_for_drag_or_size_dialog_and_can_be_cancelled_in_motion(self):
        self.ui.start_seconds(30)
        self.character.set_dragging(True)
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.assertTrue(self.ui._pending_alarm)
        self.assertFalse(self.character.scripted_motion)
        self.character.set_dragging(False)
        self.pet._size_dialog = object()
        self.ui.tick()
        self.assertTrue(self.ui._pending_alarm)
        self.pet._size_dialog = None
        self.ui.tick()
        self.assertTrue(self.character.scripted_motion)
        self.ui.cancel_timer()
        self.assertFalse(self.character.scripted_motion)
        self.assertFalse(self.ui._pending_alarm)
        self.assertEqual(self.ui._arrival_animation.state(), QPropertyAnimation.Stopped)

    def test_dragging_interrupts_alarm_motion_and_reminder_retries_after_release(self):
        self.ui.start_seconds(30)
        self.ui.deadline = time.monotonic() - 1
        self.ui.tick()
        self.assertTrue(self.character.scripted_motion)
        QTest.mousePress(self.pet, Qt.LeftButton, pos=QPoint(80, 80))
        QTest.mouseMove(self.pet, QPoint(110, 100))
        self.ui.tick()
        self.assertTrue(self.ui._pending_alarm)
        self.assertFalse(self.character.scripted_motion)
        QTest.mouseRelease(self.pet, Qt.LeftButton, pos=QPoint(110, 100))
        self.ui.tick()
        self.assertTrue(self.character.scripted_motion)
        self.ui._arrival_animation.setCurrentTime(self.ui._arrival_animation.duration())
        self.assertTrue(self.ui.speech.isVisible())
        self.assertFalse(self.ui._pending_alarm)

    def test_right_click_quick_actions_are_separated_and_keep_animation_running(self):
        menu, sleep, quit_action = self.pet.build_quick_menu()
        self.assertEqual(len(menu.actions()), 3)
        self.assertTrue(menu.actions()[1].isSeparator())
        self.assertIn('睡觉', sleep.text())
        self.assertEqual(quit_action.text(), '退出桌宠')
        fake_menu = SimpleNamespace(exec=lambda point: sleep, deleteLater=lambda: None)
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(80, 80), self.pet.mapToGlobal(QPoint(80, 80)))
        with patch.object(self.pet, 'build_quick_menu', return_value=(fake_menu, sleep, quit_action)):
            self.pet.contextMenuEvent(event)
        self.assertEqual(self.character.state, State.SLEEP)
        self.assertTrue(self.character._timer.isActive())
        second_menu, wake, quit_action = self.pet.build_quick_menu()
        self.assertIn('叫醒', wake.text())
        fake_menu.exec = lambda point: quit_action
        with patch.object(self.pet, 'build_quick_menu', return_value=(fake_menu, wake, quit_action)):
            with patch.object(self.ui, 'quit') as quit_mock:
                self.pet.contextMenuEvent(event)
                quit_mock.assert_called_once()
        menu.deleteLater()
        second_menu.deleteLater()


if __name__ == '__main__':
    unittest.main()
