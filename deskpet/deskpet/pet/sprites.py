"""素材库：统一负责图片资源的加载与占位图生成。

替换真实素材的方式：把 PNG 放进 assets/sprites/，文件名与状态名一致即可
（idle.png / walk.png / sleep.png / happy.png / drag.png / blink.png），
支持序列帧（idle_0.png、idle_1.png ...）与叠加变体（walk_blink.png）。
代码零改动，重启生效。

占位图是组合式绘制：按名字关键词拼装眼睛/腿/嘴/装饰，
所以任何新状态名（如 "dance"）都能自动得到一个合理的占位形象。
"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
CANVAS_SIZE = 200  # 所有素材统一缩放到 200x200


class SpriteLibrary:
    """按名字取 QPixmap；优先真实图片，缺失则画占位图（带缓存）。"""

    def __init__(self, sprite_dir: Path = SPRITE_DIR):
        self.sprite_dir = Path(sprite_dir)
        self._cache: dict[str, QPixmap] = {}

    def get(self, name: str, fallbacks: tuple = ()) -> QPixmap:
        """取单帧素材。fallbacks：真实文件缺失时的回退链（如 walk_blink → blink）。"""
        if name not in self._cache:
            pix = None
            for cand in (name, *fallbacks):
                path = self.sprite_dir / f"{cand}.png"
                if path.exists():
                    loaded = QPixmap(str(path))
                    if not loaded.isNull():
                        pix = loaded.scaled(
                            CANVAS_SIZE, CANVAS_SIZE,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation,
                        )
                        break
            if pix is None:
                pix = make_placeholder(name)
            self._cache[name] = pix
        return self._cache[name]

    def frames(self, name: str) -> list[QPixmap]:
        """取序列帧素材：name_0.png, name_1.png ... 连续编号，无则返回空列表。"""
        result, i = [], 0
        while (self.sprite_dir / f"{name}_{i}.png").exists():
            result.append(self.get(f"{name}_{i}"))
            i += 1
        return result

    def has_real_sprite(self, name: str) -> bool:
        return (self.sprite_dir / f"{name}.png").exists()


def make_placeholder(name: str, size: int = CANVAS_SIZE) -> QPixmap:
    """组合式占位图：按名字关键词拼装一只圆润小生物。"""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    dark = QColor("#333333")

    lean = 6 if "walk" in name else 0  # 走路时身体前倾

    # 身体
    p.setPen(QPen(QColor("#E5A63D"), 4))
    p.setBrush(QColor("#FFD166"))
    p.drawEllipse(20 + lean, 30, size - 40, size - 50)

    # 腿（走路/被抓起时露出）
    if "walk" in name or "drag" in name:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E5A63D"))
        p.drawEllipse(60 + lean, size - 32, 22, 14)
        p.drawEllipse(size - 82 + lean, size - 32, 22, 14)

    # 腮红
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 150, 150, 120))
    p.drawEllipse(45 + lean, 115, 22, 12)
    p.drawEllipse(size - 67 + lean, 115, 22, 12)

    # 眼睛
    if "happy" in name:  # ^^ 笑眼
        p.setPen(QPen(dark, 4, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(58 + lean, 84, 24, 18, 20 * 16, 140 * 16)
        p.drawArc(size - 82 + lean, 84, 24, 18, 20 * 16, 140 * 16)
    elif "blink" in name or "sleep" in name:  # 闭眼线
        p.setPen(QPen(dark, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(60 + lean, 95, 82 + lean, 95)
        p.drawLine(size - 82 + lean, 95, size - 60 + lean, 95)
    elif "drag" in name:  # >_<
        p.setPen(QPen(dark, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(60, 88, 80, 100)
        p.drawLine(60, 100, 80, 88)
        p.drawLine(size - 80, 88, size - 60, 100)
        p.drawLine(size - 80, 100, size - 60, 88)
    else:  # 圆眼 + 高光
        p.setBrush(dark)
        p.drawEllipse(62 + lean, 82, 18, 26)
        p.drawEllipse(size - 80 + lean, 82, 18, 26)
        p.setBrush(Qt.white)
        p.drawEllipse(66 + lean, 86, 6, 8)
        p.drawEllipse(size - 76 + lean, 86, 6, 8)

    # 嘴
    p.setPen(QPen(dark, 3, Qt.SolidLine, Qt.RoundCap))
    if "drag" in name:  # 张嘴
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(size // 2 - 7 + lean, 108, 14, 12)
    elif "sleep" in name:  # 小 o
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(size // 2 - 4, 112, 8, 8)
    else:  # 微笑
        p.setBrush(Qt.NoBrush)
        p.drawArc(size // 2 - 10 + lean, 105, 20, 15, 200 * 16, 140 * 16)

    # 装饰
    if "happy" in name:  # 爱心
        cx, cy = size - 58, 58
        heart = QPainterPath()
        heart.moveTo(cx, cy + 14)
        heart.cubicTo(cx - 16, cy, cx - 10, cy - 14, cx, cy - 6)
        heart.cubicTo(cx + 10, cy - 14, cx + 16, cy, cx, cy + 14)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FF6B8A"))
        p.drawPath(heart)

    p.end()
    return pix
