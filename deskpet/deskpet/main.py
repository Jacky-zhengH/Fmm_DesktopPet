"""Compatibility launcher; the maintained application lives in app/."""
from pathlib import Path
import runpy
import sys
APP = Path(__file__).resolve().parents[2] / "app"
sys.path.insert(0, str(APP))
if __name__ == "__main__":
    runpy.run_path(str(APP / "main.py"), run_name="__main__")
