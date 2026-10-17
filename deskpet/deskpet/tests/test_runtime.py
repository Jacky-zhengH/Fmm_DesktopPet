"""Regression tests using real Qt; no desktop input or global settings."""
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QPixmap, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pet.character import Character, State
from pet.settings import PetSettings
from pet.sprites import SpriteLibrary
from pet.window import PetWindow

APP = QApplication.instance() or QApplication([])


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(__file__).resolve().parent / ".tmp"
        self.temp_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.temp_root)
        self.directory = Path(self.temp.name)
        self.clock = Clock()
        self.library = SpriteLibrary()
        self.character = Character(self.library, clock=self.clock, rng=random.Random(17))
        self.character.pause()
        self.character.wander_enabled = False
        self.window = None

    def tearDown(self):
        self.character.pause()
        if self.window is not None:
            self.window.close()
            self.window.deleteLater()
        self.character.deleteLater()
        APP.processEvents()
        assert self.directory.resolve().is_relative_to(self.temp_root.resolve())
        self.temp.cleanup()

    def make_window(self):
        self.window = PetWindow(self.character, PetSettings(wander=False), self.directory / "settings.json")
        self.window.show()
        APP.processEvents()
        return self.window

    def test_sleep_clock_survives_autonomous_walk(self):
        self.clock.advance(89)
        self.character._enter_state(State.WALK)
        self.character._walk_target = 500
        self.clock.advance(1)
        self.character._tick()
        self.assertEqual(self.character.state, State.SLEEP)

    def test_human_interaction_resets_sleep_and_wakes_to_idle(self):
        self.clock.advance(89)
        self.character.interact()
        self.clock.advance(2)
        self.character._tick()
        self.assertEqual(self.character.state, State.IDLE)
        self.character.toggle_sleep()
        self.character.pet()
        self.assertEqual(self.character.state, State.IDLE)

    def test_click_clears_blink_and_happy_duration_is_real_time(self):
        self.character._blink_until = self.clock() + 1
        self.character.pet()
        self.assertEqual(self.character._blink_until, 0)
        self.assertEqual(self.character.current_sprite().cacheKey(), self.library.get("happy").cacheKey())
        self.clock.advance(1.49)
        self.character._tick()
        self.assertEqual(self.character.state, State.HAPPY)
        self.clock.advance(0.02)
        self.character._tick()
        self.assertEqual(self.character.state, State.IDLE)

    def test_walk_speed_is_independent_of_tick_count(self):
        for frequency in (30, 60):
            with self.subTest(frequency=frequency):
                character = Character(self.library, clock=self.clock)
                character.pause()
                character.auto_sleep_seconds = 0
                character.set_position(0)
                character._enter_state(State.WALK)
                character._walk_target = 200
                character.walk_step.connect(lambda dx, c=character: c.notify_x(c._x + dx))
                for _ in range(frequency):
                    self.clock.advance(1 / frequency)
                    character._tick()
                self.assertAlmostEqual(character._x, 90, places=5)
                character.deleteLater()

    def test_sequences_restart_and_disable_added_motion(self):
        for state in (State.IDLE, State.WALK, State.SLEEP, State.HAPPY, State.DRAG):
            with self.subTest(state=state):
                self.character._frames[state] = [self.library.get("idle"), self.library.get("happy")]
                self.character._enter_state(state)
                self.assertEqual(self.character.current_sprite().cacheKey(), self.library.get("idle").cacheKey())
                self.assertEqual(self.character.scale, 1)
                self.assertEqual(self.character.hop_offset, 0)
                self.clock.advance(0.15)
                self.assertEqual(self.character.current_sprite().cacheKey(), self.library.get("happy").cacheKey())

    def test_manifest_loop_and_reload(self):
        sprite_dir = self.directory / "sprites"
        sprite_dir.mkdir()
        for index, color in enumerate(("red", "blue")):
            image = QPixmap(16, 16)
            image.fill(QColor(color))
            image.save(str(sprite_dir / f"happy_{index}.png"))
        manifest = self.directory / "animations.json"
        manifest.write_text(json.dumps({"version": 1, "states": {"happy": {"fps": 10, "loop": False}}}))
        library = SpriteLibrary(sprite_dir)
        character = Character(library, clock=self.clock)
        character.pause()
        character.pet()
        self.clock.advance(0.5)
        self.assertEqual(character.current_sprite().toImage().pixelColor(0, 0), QColor("blue"))
        manifest.write_text(json.dumps({"version": 1, "states": {"happy": {"fps": 20, "loop": True}}}))
        library.reload()
        self.assertEqual(library.animation_options("happy")["fps"], 20)
        character.deleteLater()

    def test_resize_wheel_limits_save_and_restore(self):
        window = self.make_window()
        window.set_pet_size(400)
        self.assertEqual(window.settings.size, 400)
        event = QWheelEvent(QPointF(50, 50), QPointF(window.mapToGlobal(QPoint(50, 50))),
                            QPoint(), QPoint(0, -120), Qt.NoButton, Qt.ControlModifier, Qt.ScrollUpdate, False)
        APP.sendEvent(window, event)
        self.assertEqual(window.settings.size, 380)
        window.set_pet_size(9999)
        self.assertEqual(window.settings.size, 400)
        window.set_pet_size(-5)
        self.assertEqual(window.settings.size, 160)
        window.move(-5000, -5000)
        window._clamp_to_screen()
        self.assertGreaterEqual(window.x(), 0)
        self.assertGreaterEqual(window.y(), 0)
        self.assertTrue(window.save_settings())
        loaded = PetSettings.load(self.directory / "settings.json")
        self.assertEqual((loaded.size, loaded.x, loaded.y), (160, window.x(), window.y()))

    def test_normal_wheel_does_not_resize_or_accumulate(self):
        window = self.make_window()
        for delta in (60, 120, -120):
            event = QWheelEvent(QPointF(50, 50), QPointF(window.mapToGlobal(QPoint(50, 50))),
                                QPoint(), QPoint(0, delta), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
            APP.sendEvent(window, event)
            self.assertEqual(window.settings.size, 200)
            self.assertEqual(window._wheel_remainder, 0)

    def test_size_panel_preview_cancel_accept_and_bounds(self):
        window = self.make_window()
        original_position = window.pos()
        window.show_size_dialog()
        dialog = window._size_dialog
        self.assertFalse(self.character._timer.isActive())
        self.assertEqual((dialog.slider.minimum(), dialog.slider.maximum()), (80, 200))
        dialog.slider.setValue(150)
        self.assertEqual(window.settings.size, 300)
        dialog.reject()
        self.assertEqual(window.settings.size, 200)
        self.assertEqual(window.pos(), original_position)
        self.assertIsNone(window._size_dialog)
        self.assertTrue(self.character._timer.isActive())
        window.show_size_dialog()
        dialog = window._size_dialog
        dialog.slider.setValue(80)
        self.assertFalse(dialog.smaller.isEnabled())
        QTest.mouseClick(dialog.larger, Qt.LeftButton)
        self.assertEqual(window.settings.size, 180)
        dialog.slider.setValue(200)
        self.assertFalse(dialog.larger.isEnabled())
        QTest.mouseClick(dialog.reset_button, Qt.LeftButton)
        self.assertEqual(window.settings.size, 200)
        dialog.slider.setValue(140)
        dialog.accept()
        self.assertEqual(PetSettings.load(self.directory / "settings.json").size, 280)

    def test_qt_mouse_click_drag_release_and_paint(self):
        window = self.make_window()
        QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(100, 100))
        self.assertEqual(self.character.state, State.HAPPY)
        QTest.mousePress(window, Qt.LeftButton, pos=QPoint(100, 100))
        QTest.mouseMove(window, QPoint(125, 110))
        self.assertEqual(self.character.state, State.DRAG)
        QTest.mouseRelease(window, Qt.LeftButton, pos=QPoint(125, 110))
        self.assertEqual(self.character.state, State.IDLE)
        for size in (160, 200, 300, 400):
            window.set_pet_size(size)
            for state in (State.IDLE, State.WALK, State.SLEEP, State.HAPPY, State.DRAG):
                self.character._enter_state(state)
                APP.processEvents()
                rendered = window.grab().toImage()
                self.assertFalse(rendered.isNull())
                self.assertEqual(rendered.pixelColor(0, 0).alpha(), 0)

    def test_bad_settings_and_manifest_do_not_break_startup(self):
        path = self.directory / "settings.json"
        path.write_text('{"size": 9000, "wander": "false", "x": true}')
        loaded = PetSettings.load(path)
        self.assertEqual(loaded.size, 400)
        self.assertTrue(loaded.wander)
        self.assertIsNone(loaded.x)
        path.write_text('not json')
        self.assertEqual(PetSettings.load(path).size, 200)
        sprites = self.directory / "sprites"
        sprites.mkdir()
        (self.directory / "animations.json").write_text('{"version": 1, "states": []}')
        self.assertEqual(SpriteLibrary(sprites).animation_options("idle")["fps"], 12)


if __name__ == "__main__":
    unittest.main()
