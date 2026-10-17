"""桌宠入口。运行：python main.py（或双击 run.bat）"""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pet.character import Character
from pet.fonts import ensure_fonts
from pet.sprites import SpriteLibrary
from pet.settings import PetSettings, SETTINGS_PATH
from pet.window import PetWindow


def main():
    parser = argparse.ArgumentParser(description="fmm source build")
    parser.add_argument("--smoke-test", action="store_true", help="run the actual Qt event loop briefly without saving settings")
    parser.add_argument("--size-settings", action="store_true", help="open the size panel after startup")
    args = parser.parse_args()
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(SETTINGS_PATH.parent / "runtime.log", maxBytes=524288,
                                  backupCount=2, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler],
                        format="%(asctime)s %(levelname)s %(message)s")
    def report_exception(kind, error, traceback):
        logging.error("Unhandled exception", exc_info=(kind, error, traceback))
        sys.__excepthook__(kind, error, traceback)
    sys.excepthook = report_exception
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)  # Closing a settings panel must not exit the pet.
    ensure_fonts(app)
    app.setApplicationName("fmm-deskpet")
    app.setOrganizationName("fmm")
    sprites = SpriteLibrary()
    character = Character(sprites)
    win = PetWindow(character, PetSettings() if args.smoke_test else PetSettings.load(),
                    None if args.smoke_test else SETTINGS_PATH)
    if args.smoke_test:
        QTimer.singleShot(1200, app.quit)
        print(json.dumps({"platform": app.platformName(), "window_size": [win.width(), win.height()],
                          "states_with_sequences": list(character._frames)}, ensure_ascii=True))
    else:
        app.aboutToQuit.connect(win.save_settings)
    win.show()
    if args.size_settings:
        QTimer.singleShot(0, win.show_size_dialog)
    logging.info("Source build started")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
