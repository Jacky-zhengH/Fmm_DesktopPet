"""Compatibility package path for tools using the former source directory."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[3] / "app" / "pet")]
