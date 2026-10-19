"""Forward the legacy unittest command to the canonical suite."""
from pathlib import Path
import unittest
def load_tests(loader, tests, pattern):
    root = Path(__file__).resolve().parents[3]
    return unittest.TestLoader().discover(str(root / "tests"), pattern or "test*.py")
