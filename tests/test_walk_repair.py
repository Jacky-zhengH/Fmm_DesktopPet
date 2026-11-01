"""Walking repair protects enclosed artwork and colour identity across frames."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from PIL import Image, ImageDraw

SPEC = importlib.util.spec_from_file_location(
    "repair_walk_sprites", Path(__file__).resolve().parents[1] / "tools/art/repair_walk_sprites.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WalkRepairTests(unittest.TestCase):
    def test_thick_exterior_matte_removed_without_entering_closed_ink(self):
        image = Image.new("RGBA", (35, 35))
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 2, 32, 32), fill=(250, 216, 217, 254))
        draw.rectangle((12, 12, 22, 22), fill=(151, 84, 80, 254))
        draw.rectangle((13, 13, 21, 21), fill=(245, 187, 186, 254))
        draw.rectangle((15, 15, 19, 19), fill=(255, 255, 248, 254))
        before = image.tobytes()
        result, removed = MODULE.exterior_matte(image, max_removed_fraction=1)
        self.assertEqual(result.getpixel((10, 15))[3], 0)
        self.assertEqual(result.getpixel((12, 15)), image.getpixel((12, 15)))
        self.assertEqual(result.getpixel((14, 15)), image.getpixel((14, 15)))
        self.assertEqual(result.getpixel((16, 16)), image.getpixel((16, 16)))
        self.assertEqual(result.convert("RGB").tobytes(), image.convert("RGB").tobytes())
        self.assertEqual(image.tobytes(), before)
        self.assertIsNotNone(removed.getbbox())

    def test_grey_costume_outline_protects_enclosed_white(self):
        image = Image.new("RGBA", (15, 15))
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 2, 12, 12), fill=(250, 216, 218, 254))
        draw.rectangle((4, 4, 10, 10), fill=(189, 162, 160, 254))
        draw.rectangle((5, 5, 9, 9), fill=(255, 250, 248, 254))
        result, _ = MODULE.exterior_matte(image, max_removed_fraction=1)
        self.assertEqual(result.getpixel((7, 7)), image.getpixel((7, 7)))
        self.assertEqual(result.getpixel((4, 7)), image.getpixel((4, 7)))

    def test_open_contour_triggers_budget_instead_of_erasing_character(self):
        image = Image.new("RGBA", (20, 20), (245, 187, 186, 254))
        before = image.tobytes()
        with self.assertRaisesRegex(ValueError, "exceeds budget"):
            MODULE.exterior_matte(image)
        self.assertEqual(image.tobytes(), before)

    def test_two_different_source_tones_share_hair_and_eye_colours(self):
        target = MODULE.REFERENCE_SEEDS.astype(np.uint8)
        sources = [MODULE.WALK_SEEDS.astype(np.uint8), np.clip(MODULE.WALK_SEEDS - 2, 0, 255).astype(np.uint8)]
        for colours in sources:
            data = np.concatenate((np.tile(colours, (5, 1)), np.full((len(colours) * 5, 1), 254)), axis=1).astype(np.uint8)
            image = Image.fromarray(data.reshape(5, len(colours), 4))
            result, _ = MODULE.harmonize(image, target)
            for material in ("hair", "outline", "skin", "green_eye", "pink_eye", "white"):
                index = MODULE.MATERIALS.index(material)
                self.assertEqual(result.getpixel((index, 0))[:3], tuple(target[index]))
            self.assertEqual(result.getchannel("A").tobytes(), image.getchannel("A").tobytes())

    def test_local_hair_ink_correction_does_not_recolour_the_eye(self):
        image = Image.new("RGBA", (2, 1), (244, 82, 105, 255))
        mask = np.array([[False, True]])
        palette = MODULE.REFERENCE_SEEDS.astype(np.uint8)
        result, _ = MODULE.harmonize(image, palette, hair_patch_mask=mask)
        self.assertEqual(result.getpixel((0, 0))[:3], tuple(palette[7]))
        self.assertEqual(result.getpixel((1, 0))[:3], tuple(palette[1]))

    def test_empty_palette_and_wrong_legacy_canvas_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.fit_palette(np.empty((0, 3)), MODULE.WALK_SEEDS)
        with self.assertRaisesRegex(ValueError, "512x512"):
            MODULE.repair_pair([Image.new("RGBA", (284, 512))], Image.new("RGBA", (2, 2), "pink"))

    def test_hair_patch_shading_cannot_become_skin_or_costume_speckles(self):
        image = Image.new("RGBA", (3, 1))
        image.putdata([(254, 208, 196, 255), (245, 187, 186, 255), (140, 59, 58, 255)])
        palette = MODULE.REFERENCE_SEEDS.astype(np.uint8)
        result, _ = MODULE.harmonize(image, palette, hair_patch_mask=np.ones((1, 3), dtype=bool))
        self.assertEqual(result.getpixel((0, 0))[:3], tuple(palette[0]))
        self.assertEqual(result.getpixel((1, 0))[:3], tuple(palette[0]))
        self.assertEqual(result.getpixel((2, 0))[:3], tuple(palette[1]))

    def test_body_grey_boundary_corrected_but_enclosed_costume_stays_grey(self):
        image = Image.new("RGBA", (9, 9), (178, 156, 153, 255))
        palette = MODULE.REFERENCE_SEEDS.astype(np.uint8)
        result, _ = MODULE.harmonize(image, palette, body_outline_y=0)
        self.assertEqual(result.getpixel((0, 4))[:3], tuple(palette[1]))
        self.assertEqual(result.getpixel((4, 4))[:3], tuple(palette[4]))
        self.assertEqual(result.getchannel("A").tobytes(), image.getchannel("A").tobytes())


if __name__ == "__main__":
    unittest.main()
