"""视频 -> 桌宠序列帧：拆帧 + 去背景 + 统一裁剪框 + 缩放，输出 assets/sprites/<name>_<i>.png

用法：
    python tools/video_to_frames.py <视频文件> <状态名> [--step 2] [--pixel] [--remove-shadow]
                                    [--max-frames 12] [--size 512]

    --step N：每 N 帧抽 1 帧（视频 24fps 时 step 2~3 抽出 8~12 帧循环正合适）
    关键：所有帧使用**同一个裁剪框**（全帧 bbox 并集），保证帧间缩放/位置一致不抖动。

输出：<状态名>_0.png、<状态名>_1.png ...（会覆盖同名旧帧）
"""
import argparse
import sys
from pathlib import Path

import imageio.v3 as iio
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sprite_from_photo import (SPRITE_DIR, detect_mode,  # noqa: E402
                               remove_shadow, white_to_alpha, SPRITE_DIR as _SD)


def _white_to_alpha_thresh(img, thresh, refine):
    """带自定义容差的 white_to_alpha。"""
    from PIL import ImageDraw, ImageFilter
    img = img.copy()
    w, h = img.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(img, seed, (0, 0, 0, 0), thresh=thresh)
    if refine:
        a = img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
        img.putalpha(a)
    return img

FRAME_TMP = Path(__file__).resolve().parent.parent / ".frames_tmp"


def extract(src: Path, step: int, limit: int | None) -> list[Image.Image]:
    imgs = []
    for idx, frame in enumerate(iio.imiter(str(src))):
        if idx % step:
            continue
        if limit and len(imgs) >= limit:
            break
        imgs.append(Image.fromarray(frame).convert("RGBA"))
    return imgs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("name", help="状态名，如 walk")
    ap.add_argument("--step", type=int, default=2, help="每 N 帧抽 1 帧")
    ap.add_argument("--max-frames", type=int, default=12)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--mode", default="auto", choices=["auto", "alpha", "white"])
    ap.add_argument("--pixel", action="store_true")
    ap.add_argument("--remove-shadow", action="store_true")
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--thresh", type=int, default=40,
                    help="背景 floodfill 容差；视频压缩导致背景色调分区时提高到 60~70（像素风有描边保护，角色安全）")
    args = ap.parse_args()

    imgs = extract(args.src, args.step, args.max_frames)
    print(f"extracted {len(imgs)} frames")

    # 1) 逐帧去背景
    cuts = []
    for i, img in enumerate(imgs):
        mode = detect_mode(img) if args.mode == "auto" else args.mode
        cut = img if mode == "alpha" else _white_to_alpha_thresh(img, args.thresh, refine=not args.pixel)
        if args.remove_shadow:
            cut = remove_shadow(cut)
        cuts.append(cut)
    if not cuts:
        sys.exit("no frames extracted")

    # 2) 全帧统一裁剪框（bbox 并集），保证帧间构图一致
    boxes = [c.getchannel("A").getbbox() for c in cuts]
    union = (min(b[0] for b in boxes), min(b[1] for b in boxes),
             max(b[2] for b in boxes), max(b[3] for b in boxes))
    print(f"union bbox: {union}")

    # 3) 统一裁剪 -> 正方形画布 -> 缩放
    pad = int(max(union[2] - union[0], union[3] - union[1]) * args.pad)
    side = max(union[2] - union[0], union[3] - union[1]) + pad * 2
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    for i, cut in enumerate(cuts):
        cc = cut.crop(union)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(cc, ((side - cc.width) // 2, (side - cc.height) // 2), cc)
        canvas = canvas.resize((args.size, args.size),
                               Image.NEAREST if args.pixel else Image.LANCZOS)
        out = SPRITE_DIR / f"{args.name}_{i}.png"
        canvas.save(out)
        print(f"  -> {out.name}")

    print(f"done: {len(cuts)} frames")
