"""Read-only inventory and source-logic checks; Qt is stubbed, not GUI-tested.

Run from repository root with Python + Pillow + PyInstaller.
Writes only analysis/inventory.json and analysis/sprites_overview.png.
"""
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

from PIL import Image, ImageDraw
from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "deskpet" / "deskpet"
OUT = ROOT / "analysis"
sys.dont_write_bytecode = True


def inventory():
    archive = CArchiveReader(str(ROOT / "deskpet" / "芙眠眠桌宠便携版.exe"))
    rows = []
    sheet = Image.new("RGB", (720, 560), "#e8e8ee")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(sorted((SOURCE / "assets" / "sprites").glob("*.png"))):
        img = Image.open(path).convert("RGBA")
        key = "assets\\sprites\\" + path.name
        rows.append({"file": path.name, "size": list(img.size),
                     "alpha_bbox": img.getchannel("A").getbbox(),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "same_as_exe": archive.extract(key) == path.read_bytes()})
        x, y = (index % 3) * 240, (index // 3) * 280
        for cy in range(y + 30, y + 230, 10):
            for cx in range(x + 20, x + 220, 10):
                draw.rectangle((cx, cy, cx + 9, cy + 9),
                               fill="#ffffff" if ((cx-x)//10 + (cy-y)//10) % 2 else "#d4d4df")
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        sheet.paste(img, (x + 20 + (200-img.width)//2, y + 230-img.height), img)
        draw.text((x + 20, y + 240), path.name, fill="#222222")
        draw.text((x + 20, y + 256), str(rows[-1]["size"]) + " -> fit 200x200", fill="#444444")
    sheet.save(OUT / "sprites_overview.png")
    return {"exe_size": (ROOT / "deskpet" / "芙眠眠桌宠便携版.exe").stat().st_size,
            "embedded_python": [n for n in archive.toc if n.startswith("python")],
            "archive_entries": len(archive.toc), "sprites": rows}


class Signal:
    def __init__(self, *args):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


class Timer:
    def __init__(self, *args):
        self.timeout = Signal()

    def start(self, interval):
        self.interval = interval


class Sprites:
    def __init__(self, sequences=None):
        self.sequences = sequences or {}

    def frames(self, name):
        return self.sequences.get(name, [])

    def get(self, name, fallbacks=()):
        return name


def source_checks():
    core = types.ModuleType("PySide6.QtCore")
    core.QObject, core.QRect, core.QTimer, core.Signal = object, object, Timer, Signal
    sprite_module = types.ModuleType("pet.sprites")
    sprite_module.CANVAS_SIZE = 200
    replacements = {"PySide6": types.ModuleType("PySide6"),
                    "PySide6.QtCore": core, "pet.sprites": sprite_module}
    with patch.dict(sys.modules, replacements):
        spec = importlib.util.spec_from_file_location("character_under_analysis", SOURCE / "pet" / "character.py")
        module = importlib.util.module_from_spec(spec)
        # Historical baseline checks use the preserved original after live repairs.
        backup = OUT / "source_before_phase1.zip"
        if backup.exists():
            with ZipFile(backup) as archive:
                code = archive.read("pet/character.py").decode("utf-8-sig")
            exec(compile(code, str(backup) + "/pet/character.py", "exec"), module.__dict__)
        else:
            spec.loader.exec_module(module)
        make = lambda sequences=None: module.Character(Sprites(sequences))
        result = {}
        pet = make()
        pet.pet()
        result["click_state"] = pet.state
        for _ in range(module.HAPPY_TICKS):
            pet._tick()
        result["after_happy_countdown"] = pet.state
        pet.toggle_sleep()
        pet.pet()
        result["click_sleep_state"] = pet.state
        pet.set_dragging(True)
        result["drag_sprite"] = pet.current_sprite()
        pet.set_dragging(False)
        result["release_drag_state"] = pet.state
        pet = make()
        with patch.object(module.random, "random", return_value=1.0):
            for _ in range(module.IDLE_SLEEP_TICKS):
                pet._tick()
        result["sleep_without_wandering"] = pet.state
        pet = make()
        pet._awake_ticks = module.IDLE_SLEEP_TICKS - 1
        pet.state, pet._walk_target = module.State.WALK, 100
        pet._tick_walk()
        result["awake_ticks_after_walking"] = pet._awake_ticks
        pet = make()
        pet._blink = module.BLINK_TICKS
        pet.pet()
        result["sprite_click_during_blink"] = pet.current_sprite()
        pet = make({"sleep": ["sleep_0", "sleep_1"], "happy": ["happy_0", "happy_1"]})
        pet.state, pet._phase = module.State.SLEEP, 1.0
        result["sequence_sleep_scale"] = pet.scale
        pet.state = module.State.HAPPY
        result["sequence_happy_hop"] = pet.hop_offset
        pet._anim_idx = 1
        pet.pet()
        result["sequence_after_enter_happy"] = pet.current_sprite()
        assert result["click_state"] == "happy"
        assert result["after_happy_countdown"] == "idle"
        assert result["click_sleep_state"] == "happy"
        assert result["drag_sprite"] == "idle"
        assert result["sleep_without_wandering"] == "sleep"
        assert result["awake_ticks_after_walking"] == 0
        assert result["sprite_click_during_blink"] == "happy_blink"
        assert result["sequence_sleep_scale"] != 1.0
        assert result["sequence_happy_hop"] != 0.0
        assert result["sequence_after_enter_happy"] == "happy_1"
        return result


if __name__ == "__main__":
    output = inventory()
    output["verification_scope"] = "Historical baseline: original character.py (preserved ZIP if available) with Qt stubs; not current-source Qt validation"
    output["source_logic_checks"] = source_checks()
    (OUT / "inventory.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
