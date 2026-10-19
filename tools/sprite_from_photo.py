"""图片 -> 桌宠素材：去背景 + 裁边 + 正方形居中 + 缩放，输出 assets/sprites/<name>.png

用法：
    python tools/sprite_from_photo.py <输入图片> <状态名> [输出边长] [--mode auto|alpha|white|ai]

去背景模式（auto 自动判断）：
    alpha  图本身带透明通道，直接用
    white  纯白底（如 ComfyUI 出图存成 JPG），从边缘 floodfill 去白
    ai     复杂背景，用 rembg AI 抠图（需 pip install "rembg[cpu]"，动漫用 isnet-anime）

例：
    python tools/sprite_from_photo.py C:/path/pic.jpg idle
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SPRITE_DIR = Path(__file__).resolve().parent.parent / "app" / "assets" / "sprites"


def detect_mode(img: Image.Image) -> str:
    if img.getchannel("A").getextrema()[0] < 250:
        return "alpha"
    w, h = img.size
    corners = [img.getpixel(p)[:3] for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
    if all(min(px) > 235 for px in corners):
        return "white"
    return "ai"


def white_to_alpha(img: Image.Image, thresh: int = 40, refine: bool = True) -> Image.Image:
    """从四角 floodfill，把与边缘连通的近白区域变透明。
    refine：收边（腐蚀+模糊去白边）——像素画必须关掉，否则硬边被破坏。"""
    img = img.copy()
    w, h = img.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(img, seed, (0, 0, 0, 0), thresh=thresh)
    if refine:
        a = img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
        img.putalpha(a)
    return img


def ai_cutout(img: Image.Image, model: str) -> Image.Image:
    from rembg import new_session, remove  # 延迟加载，未安装时不影响其他模式
    return remove(img, session=new_session(model))


def remove_shadow(img: Image.Image, br_delta: int = 6, min_lum: int = 170) -> Image.Image:
    """去掉淡紫色地面影子（特征：B 明显高于 R 且整体明亮）。"""
    img = img.copy()
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and b - r >= br_delta and r >= min_lum and b >= min_lum:
                px[x, y] = (0, 0, 0, 0)
    return img


def make_sprite(src: Path, name: str, size: int, mode: str, model: str, pad_ratio: float,
                anchor: str = "center", lift: float = 0.0, pixel: bool = False,
                drop_shadow: bool = False) -> Path:
    img = Image.open(src).convert("RGBA")
    if mode == "auto":
        mode = detect_mode(img)
    print(f"mode: {mode}, pixel: {pixel}")

    if mode == "alpha":
        cut = img
    elif mode == "white":
        cut = white_to_alpha(img, refine=not pixel)
    else:
        cut = ai_cutout(img, model)
    if drop_shadow:
        cut = remove_shadow(cut)

    bbox = cut.getchannel("A").getbbox()
    if not bbox:
        sys.exit("去背景结果为空，换模式试试（--mode ai）")
    cut = cut.crop(bbox)

    pad = int(max(cut.size) * pad_ratio)
    side = max(cut.width, cut.height) + pad * 2
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    x = (side - cut.width) // 2
    y = side - cut.height - pad if anchor == "bottom" else (side - cut.height) // 2
    y -= int(side * lift)  # lift：人物在画布内上移（悬空感，如被拎起）
    # RGBA already carries alpha. Using it again as a paste mask squares alpha.
    canvas.alpha_composite(cut, (x, y))

    canvas = canvas.resize((size, size), Image.NEAREST if pixel else Image.LANCZOS)
    out = SPRITE_DIR / f"{name}.png"
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("name", help="状态名：idle/walk/sleep/happy/drag/blink ...")
    ap.add_argument("size", type=int, nargs="?", default=512)
    ap.add_argument("--mode", default="auto", choices=["auto", "alpha", "white", "ai"])
    ap.add_argument("--model", default="isnet-anime", help="ai 模式用模型")
    ap.add_argument("--pad", type=float, default=0.06, help="四周留白比例")
    ap.add_argument("--anchor", default="center", choices=["center", "bottom"],
                    help="bottom：脚底对齐（走路/序列帧用，逐帧不跳）")
    ap.add_argument("--lift", type=float, default=0.0,
                    help="人物在画布内垂直上移比例（悬空感，如 0.1；过大可能切到头顶）")
    ap.add_argument("--pixel", action="store_true",
                    help="像素画模式：最近邻缩放 + 跳过收边，保持像素硬边锐利")
    ap.add_argument("--remove-shadow", action="store_true",
                    help="去掉淡紫色地面影子")
    args = ap.parse_args()

    out = make_sprite(args.src, args.name, args.size, args.mode, args.model, args.pad,
                      args.anchor, args.lift, args.pixel, args.remove_shadow)
    print(f"saved: {out}")
