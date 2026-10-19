import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, QRect, QRectF
from pet.placement import attach, constrain, nearest_surface, surfaces


class PlacementTests(unittest.TestCase):
    def test_all_taskbar_orientations_and_negative_monitor_origin(self):
        full = QRect(-1920, -100, 1920, 1080)
        body = QRectF(30, 30, 170, 180)
        configurations = {
            "bottom": QRect(-1920, -100, 1920, 1040),
            "top": QRect(-1920, -60, 1920, 1040),
            "left": QRect(-1880, -100, 1880, 1080),
            "right": QRect(-1920, -100, 1880, 1080)}
        for edge, available in configurations.items():
            with self.subTest(edge=edge):
                surface = next(s for s in surfaces(full, available) if s.reserved)
                point = attach(QPoint(-1000, 300), body, full, surface)
                world = body.translated(point)
                value = {"bottom": world.bottom(), "top": world.top(),
                         "left": world.left(), "right": world.right()}[edge]
                self.assertAlmostEqual(value, surface.coordinate, delta=0.5)

    def test_taskbar_wins_corner_and_crossed_bar_still_snaps(self):
        full, work = QRect(0, 0, 1920, 1080), QRect(0, 0, 1920, 1040)
        body = QRectF(30, 30, 170, 180)
        for pos in (QPoint(1720, 820), QPoint(1000, 860)):
            surface = nearest_surface(pos, body, full, work)
            self.assertEqual(surface.edge, "bottom")
        self.assertIsNone(nearest_surface(QPoint(500, 300), body, full, work))

    def test_hidden_taskbar_falls_back_to_screen_edge(self):
        full = QRect(0, 0, 1920, 1080)
        body = QRectF(30, 30, 170, 180)
        surface = nearest_surface(QPoint(800, 860), body, full, full)
        self.assertEqual(surface.edge, "bottom")
        self.assertFalse(surface.reserved)
        self.assertEqual(attach(QPoint(800, 860), body, full, surface).y(), 870)

    def test_only_transparent_padding_can_leave_screen(self):
        full = QRect(0, 0, 1920, 1080)
        body = QRectF(30, 30, 170, 180)
        pos = constrain(QPoint(-5000, 5000), body, full)
        self.assertEqual(pos, QPoint(-30, 870))
        self.assertEqual(body.translated(pos).bottom(), 1080)


if __name__ == "__main__":
    unittest.main()
