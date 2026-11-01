"""Repair the legacy walking sprites without redrawing, cropping or resizing.

Clear the exterior matte using closed dark outlines, then map both frames to
one semantic palette fitted from idle. NumPy/Pillow are tooling dependencies;
this processing is performed offline, never in the desktop-pet event loop.
"""
import argparse
from collections import deque
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ("hair", "outline", "skin", "white", "headdress_line",
             "headdress_shade", "green_eye", "pink_eye", "fabric_light",
             "fabric_red", "warm_shadow", "line_blend", "hair_shade", "dark_blend")
REFERENCE_SEEDS = np.array([
    [254, 196, 195], [163, 88, 82], [255, 235, 234], [255, 255, 248],
    [191, 164, 159], [225, 204, 200], [163, 205, 141], [245, 71, 109],
    [255, 151, 164], [212, 91, 97], [224, 137, 136], [195, 124, 121],
    [241, 181, 180], [174, 103, 99]], dtype=float)
WALK_SEEDS = np.array([
    [246, 186, 185], [150, 84, 80], [250, 225, 224], [250, 241, 239],
    [183, 156, 153], [221, 197, 193], [150, 200, 137], [244, 82, 105],
    [246, 162, 160], [206, 90, 93], [208, 136, 137], [182, 118, 117],
    [234, 168, 167], [166, 95, 94]], dtype=float)


def exterior_matte(image, *, max_removed_fraction=.15):
    """Remove only visible pixels reachable from outside without crossing ink.

    These ink thresholds describe these legacy sprites, not arbitrary photos.
    A removal budget catches open/damaged contours instead of erasing a body.
    Four-neighbour traversal cannot leak across a diagonal pair of ink pixels.
    """
    if not 0 <= max_removed_fraction <= 1:
        raise ValueError("max_removed_fraction must be between zero and one")
    data = np.array(image.convert("RGBA"))
    rgb, alpha = data[:, :, :3], data[:, :, 3]
    occupied = alpha > 0
    ink = occupied & (rgb[:, :, 0] < 215) & (rgb[:, :, 1] < 165) & (rgb[:, :, 2] < 170)
    height, width = alpha.shape
    exterior = np.zeros((height, width), dtype=bool)
    queue = deque()

    def visit(x, y):
        if not exterior[y, x] and not ink[y, x]:
            exterior[y, x] = True
            queue.append((x, y))

    for x in range(width):
        visit(x, 0)
        visit(x, height - 1)
    for y in range(height):
        visit(0, y)
        visit(width - 1, y)
    while queue:
        x, y = queue.popleft()
        if x:
            visit(x - 1, y)
        if x + 1 < width:
            visit(x + 1, y)
        if y:
            visit(x, y - 1)
        if y + 1 < height:
            visit(x, y + 1)
    removed = exterior & occupied
    if np.count_nonzero(removed) > max_removed_fraction * np.count_nonzero(occupied):
        raise ValueError("Exterior removal exceeds budget; inspect open outlines before proceeding")
    data[removed, 3] = 0
    return Image.fromarray(data), Image.fromarray(removed.astype(np.uint8) * 255)


def rgb_to_lab(rgb):
    srgb = np.asarray(rgb, dtype=float) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    xyz = linear @ np.array([[.4124564, .2126729, .0193339],
                             [.3575761, .7151522, .1191920],
                             [.1804375, .0721750, .9503041]])
    xyz /= np.array([.95047, 1., 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack((116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])), axis=-1)


def nearest_material(pixels, palette):
    points, centres = rgb_to_lab(pixels), rgb_to_lab(palette)
    labels = np.empty(len(points), dtype=np.intp)
    for start in range(0, len(points), 4096):
        block = points[start:start + 4096]
        labels[start:start + len(block)] = ((block[:, None, :] - centres[None, :, :]) ** 2).sum(-1).argmin(-1)
    return labels


def fit_palette(pixels, seeds):
    pixels = np.asarray(pixels)
    if not len(pixels):
        raise ValueError("Palette input must contain visible pixels")
    centres = np.asarray(seeds, dtype=float).copy()
    for _ in range(3):
        labels = nearest_material(pixels, centres)
        centres = np.array([np.median(pixels[labels == index], axis=0)
                            if np.any(labels == index) else centres[index]
                            for index in range(len(centres))])
    return np.rint(centres).astype(np.uint8)


def reference_palette(image):
    data = np.array(image.convert("RGBA"))
    return fit_palette(data[:, :, :3][data[:, :, 3] > 250], REFERENCE_SEEDS)


def repaired_hair_mask(size):
    width, height = size
    yy, xx = np.indices((height, width))
    return (((xx >= 384) & (xx < 445) & (yy >= 315) & (yy < 435)) |
            ((xx >= 390) & (xx < 445) & (yy >= 230) & (yy < 300)))


def harmonize(image, palette, *, hair_patch_mask=None, body_outline_y=None):
    data = np.array(image.convert("RGBA"))
    original = data.copy()
    visible = data[:, :, 3] > 0
    pixels = data[:, :, :3][visible]
    source_palette = fit_palette(pixels, WALK_SEEDS)
    data[:, :, :3][visible] = palette[nearest_material(pixels, source_palette)]
    if hair_patch_mask is not None:
        if hair_patch_mask.shape != visible.shape:
            raise ValueError("Hair patch mask must match the canvas")
        rgb = original[:, :, :3].astype(int)
        # Generated back-hair ink was too red; these regions contain only hair.
        # The same red elsewhere (eye/outfit) must retain its own material.
        patch = hair_patch_mask & visible
        reddish_ink = (rgb[:, :, 0] - rgb[:, :, 1] > 55) & (rgb[:, :, 1] < 150)
        existing_ink = (rgb[:, :, 0] < 215) & (rgb[:, :, 1] < 165) & (rgb[:, :, 2] < 170)
        # These old generated patches contain only back hair. Their uneven
        # shading must not be mistaken for skin or grey costume pixels.
        data[patch, :3] = palette[MATERIALS.index("hair")]
        data[patch & (reddish_ink | existing_ink), :3] = palette[MATERIALS.index("outline")]
    if body_outline_y is not None:
        padded = np.pad(visible, 1)
        interior = (padded[1:-1, :-2] & padded[1:-1, 2:] &
                    padded[:-2, 1:-1] & padded[2:, 1:-1])
        boundary = visible & ~interior
        # Below the headpiece, old grey/pink ink blends belong to the brown
        # character contour. Retain interior whites and the grey headpiece.
        grey = (np.all(data[:, :, :3] == palette[MATERIALS.index("headdress_line")], axis=2) |
                np.all(data[:, :, :3] == palette[MATERIALS.index("headdress_shade")], axis=2))
        yy = np.indices(visible.shape)[0]
        data[boundary & grey & (yy >= body_outline_y), :3] = palette[MATERIALS.index("outline")]
    return Image.fromarray(data), source_palette


def repair_pair(images, reference):
    palette = reference_palette(reference)
    results, records = [], []
    for image in images:
        if image.size != (512, 512):
            raise ValueError("Legacy walking repair requires the complete 512x512 canvas")
        clean, removed = exterior_matte(image)
        result, source_palette = harmonize(clean, palette, hair_patch_mask=repaired_hair_mask(image.size),
                                           body_outline_y=215)
        results.append(result)
        records.append({"removed_exterior_pixels": int(np.count_nonzero(np.array(removed))),
                        "source_palette": source_palette.tolist(), "size": list(result.size)})
    return results, {"materials": list(MATERIALS), "shared_palette": palette.tolist(), "frames": records}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-dir", type=Path)
    source.add_argument("--source-ref", help="Read the old PNGs from this saved Git commit")
    parser.add_argument("--reference", type=Path, default=ROOT / "app/assets/sprites/idle.png")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.is_relative_to(ROOT / "app/assets"):
        parser.error("Write a separate candidate first; runtime assets cannot be the output directory")
    names = ["walk_0.png", "walk_1.png"]
    if any((output / name).exists() for name in [*names, "walk_repair.json"]):
        parser.error("Candidate outputs already exist; select a new empty output location")
    revision = None
    if args.source_ref:
        revision = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options",
                                             args.source_ref + "^{commit}"], cwd=ROOT, text=True).strip()
        inputs = [subprocess.check_output(["git", "show", revision + ":app/assets/sprites/" + name], cwd=ROOT)
                  for name in names]
    else:
        inputs = [(args.source_dir / name).read_bytes() for name in names]
    reference = args.reference.read_bytes()
    images = [Image.open(BytesIO(data)).convert("RGBA") for data in inputs]
    results, record = repair_pair(images, Image.open(BytesIO(reference)))
    record.update({"source_revision": revision, "reference": str(args.reference),
                   "reference_sha256": digest(reference),
                   "method": "four-neighbour exterior flood bounded by original ink, then shared semantic Lab palette"})
    output.mkdir(parents=True, exist_ok=True)
    for index, (name, result) in enumerate(zip(names, results)):
        destination = output / name
        result.save(destination, optimize=True)
        record["frames"][index].update({"file": name, "source_sha256": digest(inputs[index]),
                                        "output_sha256": digest(destination.read_bytes())})
    (output / "walk_repair.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Saved two walking candidates and their shared-palette record to " + str(output))


if __name__ == "__main__":
    main()
