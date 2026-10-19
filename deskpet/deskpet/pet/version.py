"""Compatibility export; version is defined only in app/pet/version.py."""
from pathlib import Path
import runpy
_info = runpy.run_path(str(Path(__file__).resolve().parents[3] / "app/pet/version.py"))
VERSION = _info["VERSION"]
PACKAGE_NAME = _info["PACKAGE_NAME"]
