"""Inspect source canvas edges and render diagnostic crops, without editing art."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "0.1.4"
REVIEW = ROOT / "image" / "review" / "0.1.4"
SPRITES = ROOT / "app/assets/sprites"


def runs(values):
    result = []
    for value in values:
        if result and value == result[-1][1] + 1:
            result[-1][1] = value
        else:
            result.append([value, value])
    return result


def inspect(path):
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    width, height = image.size
    edges = {}
    for side, x in (("left", 0), ("right", width - 1)):
        edges[side] = {}
        for threshold in (1, 128, 250):
            rows = [y for y in range(height) if alpha.getpixel((x, y)) >= threshold]
            edges[side][f"alpha_ge_{threshold}"] = {
                "pixel_count": len(rows), "y_runs_inclusive": runs(rows),
            }
    return {
        "file": path.name, "size": list(image.size),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "edge_contact": edges,
        "top_contact": sum(alpha.getpixel((x, 0)) > 0 for x in range(width)),
        "bottom_contact": sum(alpha.getpixel((x, height - 1)) > 0 for x in range(width)),
    }


def render(paths):
    canvas = Image.new("RGB", (1100, 1040), "#f8f4f1")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    draw.text((24, 15), "走路原图截边排查 · 红线为 PNG 画布左右边界", font=font, fill="#453a3e")
    draw.text((24, 50), "仅合成背景与最近邻放大；没有补画、去边或改动原图。裁剪坐标采用原图像素。", font=small, fill="#453a3e")

    def panel(path, crop, origin, scale, label, edge_sides):
        image = Image.open(path).convert("RGBA").crop(crop)
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        x, y = origin
        draw.text((x, y), label, font=small, fill="#453a3e")
        y += 32
        margin = 16
        bg = Image.new("RGBA", (image.width + margin * 2, image.height + margin * 2), "#20242b")
        bg.alpha_composite(image, (margin, margin))
        canvas.paste(bg.convert("RGB"), (x, y))
        for side in edge_sides:
            edge_x = x + margin - 2 if side == "left" else x + margin + image.width + 1
            draw.line((edge_x, y + margin, edge_x, y + margin + image.height - 1), fill="#e45e73", width=2)

    for index, path in enumerate(paths):
        y = 100 + index * 440
        panel(path, (0, 76, 284, 432), (24, y), 1, path.name + " · 全部非透明高度", ("left", "right"))
        panel(path, (0, 192, 62, 300), (365, y), 3, "左侧发梢 · x=0～61", ("left",))
        panel(path, (218, 322, 284, 432), (680, y), 3, "右下长发 · x=218～283", ("right",))
    draw.text((24, 991), "结论：源图已有平直截边，右下最明显。缺失轮廓需要补画；单纯增加透明留白不能恢复。", font=small, fill="#453a3e")
    REVIEW.mkdir(parents=True, exist_ok=True)
    canvas.save(REVIEW / "walk_edge_review.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [SPRITES / f"walk_{index}.png" for index in (0, 1)]
    before = [inspect(path) for path in paths]
    render(paths)
    assert before == [inspect(path) for path in paths], "Source images changed during inspection"
    (OUT / "walk_edge_audit.json").write_text(json.dumps({
        "coordinate_system": "Original PNG pixels; runs include both endpoints",
        "source_images_unchanged": True, "assets": before,
        "interpretation": "Edge contact alone does not prove clipping. Visual inspection also shows flat cut-off hair, strongest at the lower-right source boundary. Missing contours cannot be recovered by padding alone.",
    }, indent=2) + "\n", encoding="utf-8")
    print("Inspected both walking images; wrote edge diagnostics; source hashes unchanged.")
