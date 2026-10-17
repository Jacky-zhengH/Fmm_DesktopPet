"""Project-local settings; no registry or global Python changes."""
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

def default_settings_path():
    # One-file builds unpack modules to a temporary folder; keep saves beside the EXE.
    root = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent)
    return root / ".user" / "settings.json"


SETTINGS_PATH = default_settings_path()
MIN_SIZE = 160
MAX_SIZE = 400


@dataclass
class PetSettings:
    size: int = 200
    pixelated: bool = True
    wander: bool = True
    auto_sleep_seconds: float = 90.0
    snap_to_edges: bool = True
    dock_edge: str | None = None
    dock_screen: str | None = None
    x: int | None = None
    y: int | None = None

    @classmethod
    def load(cls, path=SETTINGS_PATH):
        result = cls()
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("settings must be an object")
            if type(data.get("size")) is int:
                result.size = max(MIN_SIZE, min(MAX_SIZE, data["size"]))
            for name in ("pixelated", "wander", "snap_to_edges"):
                if type(data.get(name)) is bool:
                    setattr(result, name, data[name])
            seconds = data.get("auto_sleep_seconds")
            if type(seconds) in (int, float) and 0 <= seconds <= 86400:
                result.auto_sleep_seconds = float(seconds)
            for name in ("x", "y"):
                if type(data.get(name)) is int and abs(data[name]) < 100000:
                    setattr(result, name, data[name])
            if data.get("dock_edge") in ("bottom", "top", "left", "right"):
                result.dock_edge = data["dock_edge"]
            if isinstance(data.get("dock_screen"), str) and len(data["dock_screen"]) < 256:
                result.dock_screen = data["dock_screen"]
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            logging.warning("Cannot load settings %s: %s", path, exc)
        return result

    def save(self, path=SETTINGS_PATH):
        path = Path(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            pending = path.with_suffix(".tmp")
            pending.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
            pending.replace(path)
            return True
        except OSError as exc:
            logging.warning("Cannot save settings %s: %s", path, exc)
            return False
