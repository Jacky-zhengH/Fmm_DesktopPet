"""Build a source+assets Windows test package. No user settings are copied."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
if sys.platform != "win32":
    raise SystemExit("Build the Windows package on Windows.")
subprocess.run([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
    "--name", "fmm-desktop-pet", "--distpath", str(ROOT / "dist"),
    "--workpath", str(ROOT / "build" / "pyinstaller"),
    "--specpath", str(ROOT / "build"),
    "--add-data", f"{ROOT / 'deskpet' / 'deskpet' / 'assets'};assets",
    str(ROOT / "deskpet" / "deskpet" / "main.py"),
], cwd=ROOT, check=True)
