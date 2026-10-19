"""素材库：统一负责图片资源的加载与占位图生成。

替换真实素材的方式：把 PNG 放进 assets/sprites/，文件名与状态名一致即可
（idle.png / walk.png / sleep.png / happy.png / drag.png / blink.png），
支持序列帧（idle_0.png、idle_1.png ...）与完整替换图（walk_blink.png）。
动画选项位于 assets/animations.json；可在菜单重新加载。

占位图是组合式绘制：按名字关键词拼装眼睛/腿/嘴/装饰，
所以任何新状态名（如 "dance"）都能自动得到一个合理的占位形象。
"""
import json
import logging
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
CANVAS_SIZE = 200  # 默认显示尺寸；加载时保留原图分辨率


class SpriteLibrary:
    """按名字取 QPixmap；优先真实图片，缺失则画占位图（带缓存）。"""

    def __init__(self, sprite_dir: Path = SPRITE_DIR):
        self.sprite_dir = Path(sprite_dir)
        self._cache: dict[tuple, QPixmap] = {}
        self._animations = {}
        self.reload()

    def reload(self):
        self._cache.clear()
        self._pixel_bounds = {}
        self._clip_bounds = {}
        self._reference_ratio = None
        self._animations = {}
        path = self.sprite_dir.parent / "animations.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") != 1:
                raise ValueError("unsupported animation manifest")
            states = data.get("states", {})
            if not isinstance(states, dict):
                raise ValueError("states must be an object")
            for name, options in states.items():
                if not isinstance(options, dict):
                    continue
                fps = options.get("fps", 12)
                if type(fps) not in (int, float) or not 1 <= fps <= 60:
                    continue
                clean = {"fps": float(fps)}
                for key in ("loop", "procedural"):
                    if type(options.get(key)) is bool:
                        clean[key] = options[key]
                if type(options.get("facing")) is int and options["facing"] in (-1, 0, 1):
                    clean["facing"] = options["facing"]
                self._animations[name] = clean
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            logging.warning("Cannot load animation manifest %s: %s", path, exc)

    def animation_options(self, name):
        return {"fps": 12.0, "loop": True, "procedural": False,
                **self._animations.get(name, {})}

    def get(self, name: str, fallbacks: tuple = ()) -> QPixmap:
        """取单帧素材。fallbacks：真实文件缺失时的回退链（如 walk_blink → blink）。"""
        key = (name, tuple(fallbacks))
        if key not in self._cache:
            pix = None
            for cand in (name, *fallbacks):
                path = self.sprite_dir / f"{cand}.png"
                if path.exists():
                    loaded = QPixmap(str(path))
                    if not loaded.isNull():
                        pix = loaded
                        break
            if pix is None:
                pix = make_placeholder(name)
            self._cache[key] = pix
        return self._cache[key]

    def frames(self, name: str) -> list[QPixmap]:
        """取序列帧素材：name_0.png, name_1.png ... 连续编号，无则返回空列表。"""
        result, i = [], 0
        while (self.sprite_dir / f"{name}_{i}.png").exists():
            result.append(self.get(f"{name}_{i}"))
            i += 1
        return result

    def has_real_sprite(self, name: str) -> bool:
        return (self.sprite_dir / f"{name}.png").exists()

    def pixel_bounds(self, pix):
        """Exact nonzero alpha bounds, including semitransparent pixels."""
        key = pix.cacheKey()
        if key not in self._pixel_bounds:
            image = pix.toImage().convertToFormat(QImage.Format_RGBA8888)
            width, height, stride = image.width(), image.height(), image.bytesPerLine()
            data = image.constBits()
            left, top, right, bottom = width, height, 0, 0
            for y in range(height):
                row = bytes(data[y * stride + 3:y * stride + width * 4:4])
                start = width - len(row.lstrip(b"\0"))
                if start == width:
                    continue
                left, right = min(left, start), max(right, len(row.rstrip(b"\0")))
                top, bottom = min(top, y), y + 1
            self._pixel_bounds[key] = QRect(left, top, right - left, bottom - top) if bottom else QRect()
        return QRect(self._pixel_bounds[key])

    def content_bounds(self, state):
        """A shared union for a clip, so individual frames cannot resize the pet."""
        if state not in self._clip_bounds:
            frames = self.frames(state)
            if not frames:
                frames = [self.get(state, fallbacks=("idle",) if state == "drag" else ())]
            bounds = QRect()
            for pix in frames:
                bounds = bounds.united(self.pixel_bounds(pix))
            self._clip_bounds[state] = bounds if not bounds.isEmpty() else frames[0].rect()
        return QRect(self._clip_bounds[state])

    def reference_height_ratio(self):
        if self._reference_ratio is None:
            pix = (self.frames("idle") or [self.get("idle")])[0]
            self._reference_ratio = min(1.0, self.content_bounds("idle").height() / max(pix.width(), pix.height(), 1))
        return self._reference_ratio


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
