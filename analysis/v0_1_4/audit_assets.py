"""Read-only sprite audit and diagnostic crops; never rewrites source art."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SPRITES = ROOT / "app/assets/sprites"


def inspect():
    rows = []
    for path in sorted(SPRITES.glob("*.png")):
        im = Image.open(path).convert("RGBA")
        h = im.getchannel("A").histogram()
        rows.append({
            "file": path.name, "size": list(im.size),
            "alpha_bbox_exclusive": list(im.getchannel("A").getbbox()),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "alpha_0": h[0], "alpha_255": h[255], "alpha_254": h[254],
            "alpha_1_to_253": sum(h[1:254]),
        })
    return rows


def render():
    canvas = Image.new("RGB", (1000, 824), "#f8f4f1")
    draw = ImageDraw.Draw(canvas)
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    if not font_path.exists():
        font_path = Path("C:/Windows/Fonts/simhei.ttf")
    font = ImageFont.truetype(str(font_path), 19) if font_path.exists() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 16) if font_path.exists() else font
    draw.text((22, 12), "0.1.4 素材检查 · 原图裁剪与背景合成，未修图", font=font, fill="#453a3e")

    def panel(x, y, label, path, crop, size, background="#20242b"):
        draw.text((x, y), label, font=small, fill="#453a3e")
        src = Image.open(path).convert("RGBA").crop(crop)
        src.thumbnail(size, Image.Resampling.NEAREST)
        bg = Image.new("RGBA", size, background)
        bg.alpha_composite(src, ((size[0] - src.width) // 2, (size[1] - src.height) // 2))
        canvas.paste(bg.convert("RGB"), (x, y + 27))

    def enlarged(path, crop, scale):
        im = Image.open(path).convert("RGBA").crop(crop)
        return im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)

    draw.text((22, 52), "母图：呆毛空隙与外部同为粉色", font=small, fill="#453a3e")
    draw.text((512, 52), "idle：同一空隙留有不透明白色", font=small, fill="#453a3e")
    master = enlarged(ROOT / "image/fmm_master_reference.jpg", (410, 190, 640, 340), 2)
    canvas.paste(master.convert("RGB"), (22, 79))
    idle = enlarged(SPRITES / "idle.png", (135, 20, 250, 95), 4)
    bg = Image.new("RGBA", idle.size, "#20242b")
    bg.alpha_composite(idle)
    canvas.paste(bg.convert("RGB"), (512, 79))

    panel(22, 398, "行走：深底检查浅色外轮廓", SPRITES / "walk_0.png", (0, 76, 284, 432), (300, 280))
    panel(348, 398, "同一行走图：浅底对照", SPRITES / "walk_0.png", (0, 76, 284, 432), (300, 280), "#e8e6ef")
    panel(674, 398, "眨眼 / 睡眠：文件字节相同", SPRITES / "sleep.png", (36, 27, 475, 485), (300, 280))
    draw.text((22, 726), "行走的大部分半透明像素其实是 alpha=254，不能按“半透明=脏边”一刀切。", font=small, fill="#453a3e")
    draw.text((22, 757), "本图用于看素材问题，展示尺寸不代表程序里的动作比例；走路缩小此前已修复。", font=small, fill="#453a3e")
    canvas.save(OUT / "asset_review.png")


if __name__ == "__main__":
    before = inspect()
    (OUT / "asset_audit.json").write_text(json.dumps({
        "source": "current app/assets/sprites; read-only inspection",
        "assets": before,
        "identical_files": [[row["file"] for row in before if row["sha256"] == digest]
                            for digest, count in Counter(row["sha256"] for row in before).items() if count > 1],
    }, indent=2) + "\n", encoding="utf-8")
    render()
    assert before == inspect(), "Source sprites changed while auditing"
    print("Audited original sprites; wrote report and diagnostic sheet; source hashes unchanged.")
