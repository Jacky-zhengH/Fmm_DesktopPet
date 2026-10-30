"""Edge cleanup must preserve colour, protected art and explicit canvas offsets."""
import importlib.util
from pathlib import Path
import unittest

from PIL import Image

SPEC = importlib.util.spec_from_file_location(
    "clean_sprite_edges", Path(__file__).resolve().parents[1] / "tools/clean_sprite_edges.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SpriteEdgeTests(unittest.TestCase):
    def test_removes_exterior_matte_but_preserves_contour_and_inner_white(self):
        image = Image.new("RGBA", (9, 9))
        for y in range(1, 8):
            for x in range(1, 8):
                image.putpixel((x, y), (249, 216, 216, 254))
        for y in range(2, 7):
            for x in range(2, 7):
                image.putpixel((x, y), (160, 85, 80, 254))
        image.putpixel((4, 4), (255, 255, 255, 254))
        before = image.tobytes()
        result, removed = MODULE.cleanup(image, rim=4)
        self.assertEqual(result.getpixel((1, 1))[3], 0)
        self.assertEqual(result.getpixel((2, 2)), (160, 85, 80, 254))
        self.assertEqual(result.getpixel((4, 4)), (255, 255, 255, 254))
        self.assertEqual(image.tobytes(), before)
        self.assertEqual(result.convert("RGB").tobytes(), image.convert("RGB").tobytes())
        self.assertIsNotNone(removed.getbbox())

    def test_protection_keeps_legitimate_white_costume_at_edge(self):
        image = Image.new("RGBA", (8, 8))
        for y in range(2, 6):
            for x in range(2, 6):
                image.putpixel((x, y), (245, 220, 219, 254))
        result, removed = MODULE.cleanup(
            image, rim=4, protect_polygons=[[(2, 2), (5, 2), (5, 5), (2, 5)]])
        self.assertEqual(result.tobytes(), image.tobytes())
        self.assertIsNone(removed.getbbox())

    def test_rim_budget_does_not_erase_thick_pale_art_in_one_pass(self):
        image = Image.new("RGBA", (11, 11), (250, 220, 220, 254))
        result, _ = MODULE.cleanup(image, rim=2)
        self.assertEqual(result.getpixel((1, 5))[3], 0)
        self.assertEqual(result.getpixel((2, 5))[3], 254)
        self.assertEqual(result.getpixel((5, 5))[3], 254)

    def test_canvas_placement_preserves_alpha_and_exact_pixel_position(self):
        image = Image.new("RGBA", (2, 2), (170, 80, 90, 128))
        result = MODULE.place_on_canvas(image, (6, 7), (3, 4))
        self.assertEqual(result.getpixel((3, 4)), (170, 80, 90, 128))
        self.assertEqual(result.crop((3, 4, 5, 6)).tobytes(), image.tobytes())
        self.assertEqual(result.getpixel((2, 4))[3], 0)
        self.assertEqual(result.getpixel((5, 6))[3], 0)

    def test_canvas_rejects_cropping_or_negative_offsets(self):
        image = Image.new("RGBA", (2, 2))
        for offset in [(-1, 0), (0, -1), (2, 0), (0, 2)]:
            with self.assertRaises(ValueError):
                MODULE.place_on_canvas(image, (3, 3), offset)


if __name__ == "__main__":
    unittest.main()
