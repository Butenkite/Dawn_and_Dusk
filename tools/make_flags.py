"""Draw flags for countries the mod adds (vanilla has no art for them).

Simple geometric renderings of the national flags as they were in 2000,
drawn from scratch, so they are ours to publish. Writes the three sizes
HOI4 wants: gfx/flags/TAG.tga (82x52), medium/ (41x26), small/ (10x7).

    python tools/make_flags.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
W, H = 82 * 4, 52 * 4      # draw large, scale down for clean edges


def lesotho():
    """1987-2006 flag: white hoist triangle with a brown shield, blue
    diagonal band, green fly triangle."""
    im = Image.new("RGB", (W, H), (0, 101, 59))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (W * 0.62, 0), (0, H * 0.95)], fill=(0, 56, 147))
    d.polygon([(0, 0), (W * 0.5, 0), (0, H * 0.77)], fill=(255, 255, 255))
    cx, cy, r = W * 0.17, H * 0.30, H * 0.13
    d.line([(cx - r * 1.4, cy + r * 1.3), (cx + r * 1.4, cy - r * 1.3)], fill=(110, 70, 30), width=6)
    d.line([(cx - r * 1.4, cy - r * 1.3), (cx + r * 1.4, cy + r * 1.3)], fill=(110, 70, 30), width=6)
    d.ellipse([cx - r * 0.75, cy - r, cx + r * 0.75, cy + r], fill=(140, 90, 40), outline=(80, 50, 20), width=4)
    return im


def swaziland():
    """Blue, yellow, crimson, yellow, blue, with a black and white shield."""
    im = Image.new("RGB", (W, H), (62, 94, 166))
    d = ImageDraw.Draw(im)
    u = H / 16
    d.rectangle([0, 3 * u, W, 13 * u], fill=(255, 213, 0))
    d.rectangle([0, 4 * u, W, 12 * u], fill=(177, 16, 39))
    cx, cy = W / 2, H / 2
    d.line([(cx - W * 0.33, cy), (cx + W * 0.33, cy)], fill=(255, 213, 0), width=5)
    d.ellipse([cx - W * 0.17, cy - H * 0.17, cx + W * 0.17, cy + H * 0.17], fill=(0, 0, 0))
    d.chord([cx - W * 0.17, cy - H * 0.17, cx + W * 0.17, cy + H * 0.17], 90, 270, fill=(255, 255, 255))
    return im


FLAGS = {"LES": lesotho, "SWZ": swaziland}


def save(img, path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize(size, Image.LANCZOS).convert("RGBA").save(path)


def main():
    for tag, draw in FLAGS.items():
        img = draw()
        save(img, ROOT / f"gfx/flags/{tag}.tga", (82, 52))
        save(img, ROOT / f"gfx/flags/medium/{tag}.tga", (41, 26))
        save(img, ROOT / f"gfx/flags/small/{tag}.tga", (10, 7))
        print(f"wrote {tag}")


if __name__ == "__main__":
    main()
