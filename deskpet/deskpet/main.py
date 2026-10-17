"""桌宠入口。运行：python main.py（或双击 run.bat）"""
import sys

from PySide6.QtWidgets import QApplication

from pet.character import Character
from pet.sprites import SpriteLibrary
from pet.window import PetWindow


def main():
    app = QApplication(sys.argv)
    sprites = SpriteLibrary()
    character = Character(sprites)
    win = PetWindow(character)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
