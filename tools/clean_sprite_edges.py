"""Conservative alpha-only rim cleanup; always writes a separate candidate PNG.

Only pale pixels connected to transparency can be removed. Caller-supplied
protection polygons preserve white costume details. This is not an art
reconstruction tool and does not repair a silhouette already cut by its canvas.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


def place_on_canvas(image, size, offset=(0, 0)):
    image = image.convert("RGBA")
    x, y = offset
    if x < 0 or y < 0 or x + image.width > size[0] or y + image.height > size[1]:
        raise ValueError("Input must fit entirely inside the requested canvas")
    canvas = Image.new("RGBA", size)
    # No mask argument: copy RGBA values exactly, without squaring alpha.
    canvas.paste(image, offset)
    return canvas


def cleanup(image, *, rim=2, min_red=225, min_green=200, min_blue=200,
            protect_polygons=()):
    if not 0 <= rim <= 8:
        raise ValueError("rim must be in 0..8 original-image pixels")
    source = image.convert("RGBA")
    protected = Image.new("L", source.size)
    draw = ImageDraw.Draw(protected)
    for polygon in protect_polygons:
        draw.polygon([tuple(point) for point in polygon], fill=255)
    eligible = Image.new("L", source.size)
    eligible.putdata([
        255 if a > 0 and r >= min_red and g >= min_green and b >= min_blue
        else 0 for r, g, b, a in source.get_flattened_data()
    ])
    eligible = ImageChops.subtract(eligible, protected)
    alpha = source.getchannel("A")
    removed = Image.new("L", source.size)
    for _ in range(rim):
        occupied = alpha.point(lambda value: 255 if value else 0)
        padded = Image.new("L", (source.width + 2, source.height + 2))
        padded.paste(occupied, (1, 1))
        width, height = source.size
        # Four-neighbour connectivity avoids crossing a diagonal contour corner.
        interior = ImageChops.darker(
            ImageChops.darker(padded.crop((0, 1, width, height + 1)),
                              padded.crop((2, 1, width + 2, height + 1))),
            ImageChops.darker(padded.crop((1, 0, width + 1, height)),
                              padded.crop((1, 2, width + 1, height + 2))))
        boundary = ImageChops.subtract(occupied, interior)
        layer = ImageChops.multiply(boundary, eligible)
        if layer.getbbox() is None:
            break
        removed = ImageChops.lighter(removed, layer)
        alpha = ImageChops.subtract(alpha, layer)
    candidate = source.copy()
    candidate.putalpha(alpha)
    return candidate, removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rim", type=int, default=2)
    parser.add_argument("--protect-mask", type=Path,
                        help="White protects: optional same-size L mask")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new file, never the source or an existing candidate")
    image = Image.open(args.source).convert("RGBA")
    result, removed = cleanup(image, rim=args.rim)
    if args.protect_mask:
        protection = Image.open(args.protect_mask).convert("L")
        if protection.size != image.size:
            parser.error("Protection mask dimensions must match input")
        alpha = Image.composite(image.getchannel("A"), result.getchannel("A"), protection)
        result.putalpha(alpha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    print(f"Saved alpha-only candidate: {args.output}")


if __name__ == "__main__":
    main()
