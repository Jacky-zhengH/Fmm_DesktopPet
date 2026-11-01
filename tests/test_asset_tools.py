"""Synthetic images only: check asset conversion without touching original art."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import imageio.v3 as iio
import numpy as np
from PIL import Image

TOOLS = Path(__file__).resolve().parents[1] / "tools" / "art"
TEST_TEMP_ROOT = Path(__file__).resolve().parent / ".tmp"
TEST_TEMP_ROOT.mkdir(exist_ok=True)
sys.path.insert(0, str(TOOLS))
import sprite_from_photo as photo


class AssetToolTests(unittest.TestCase):
    def test_alpha_not_multiplied_by_own_mask(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as folder:
            root = Path(folder)
            source = root / "half.png"
            Image.new("RGBA", (16, 16), (200, 100, 100, 128)).save(source)
            with patch.object(photo, "SPRITE_DIR", root / "out"), contextlib.redirect_stdout(io.StringIO()):
                result = photo.make_sprite(source, "idle", 16, "alpha", "unused", 0, pixel=True)
            self.assertEqual(Image.open(result).getpixel((8, 8))[3], 128)

    def test_video_transparent_frames_and_stale_tail(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as folder:
            root = Path(folder)
            output = root / "sprites"
            output.mkdir()
            for name in ("walk_2.png", "walk_blink.png", "happy_0.png"):
                Image.new("RGBA", (16, 16)).save(output / name)
            empty = np.zeros((16, 16, 4), dtype=np.uint8)
            frame = empty.copy()
            frame[4:12, 4:12] = (255, 0, 0, 128)
            argv = [str(TOOLS / "video_to_frames.py"), "unused.mov", "walk", "--step", "1",
                    "--mode", "alpha", "--pixel", "--size", "16", "--pad", "0"]
            with patch.object(photo, "SPRITE_DIR", output), patch.object(iio, "imiter", return_value=iter([empty, frame])), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(TOOLS / "video_to_frames.py"), run_name="__main__")
            self.assertTrue((output / "walk_0.png").exists())
            self.assertTrue((output / "walk_1.png").exists())
            self.assertFalse((output / "walk_2.png").exists())
            self.assertTrue((output / "walk_blink.png").exists())
            self.assertTrue((output / "happy_0.png").exists())
            self.assertEqual(Image.open(output / "walk_1.png").getpixel((8, 8))[3], 128)

    def test_video_complex_background_does_not_silently_use_white_mode(self):
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        argv = [str(TOOLS / "video_to_frames.py"), "unused.mov", "walk", "--step", "1"]
        with patch.object(iio, "imiter", return_value=iter([frame])), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(SystemExit, "Complex background"):
            runpy.run_path(str(TOOLS / "video_to_frames.py"), run_name="__main__")


if __name__ == "__main__":
    unittest.main()
