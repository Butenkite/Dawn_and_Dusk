"""Draw flags for countries the mod adds (vanilla has no art for them).

Simple geometric renderings of the national flags as they were in 2000,
drawn from scratch, so they are ours to publish. Writes the three sizes
HOI4 wants: gfx/flags/TAG.tga (82x52), medium/ (41x26), small/ (10x7).

    python tools/countries/make_flags.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MOD  # noqa: E402
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


def star(d, cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.4
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


# The rebel movements of the Second Congo War fought under the Congo's own
# star or under party banners. These are our own designs in that spirit, not
# copies of any real banner.

def rcd_goma():
    """Sky blue over crimson, a gold star in a white hoist band."""
    im = Image.new("RGB", (W, H), (60, 140, 210))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H / 2, W, H], fill=(150, 30, 70))
    d.rectangle([0, 0, W * 0.3, H], fill=(245, 245, 240))
    star(d, W * 0.15, H / 2, H * 0.22, (240, 190, 30))
    return im


def mlc():
    """Green field, a white diagonal, a gold star in the upper hoist."""
    im = Image.new("RGB", (W, H), (30, 120, 70))
    d = ImageDraw.Draw(im)
    d.polygon([(0, H), (W * 0.18, H), (W, H * 0.12), (W, 0), (W * 0.82, 0), (0, H * 0.88)], fill=(245, 245, 240))
    star(d, W * 0.2, H * 0.28, H * 0.18, (240, 190, 30))
    return im


def rcd_ml():
    """Orange over black, a gold star on a white disc."""
    im = Image.new("RGB", (W, H), (225, 120, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.62, W, H], fill=(25, 25, 25))
    cx, cy, r = W / 2, H * 0.5, H * 0.27
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 245, 240))
    star(d, cx, cy, r * 0.8, (230, 170, 20))
    return im


def ruf():
    """Our design for the RUF: dark red and black divided on the diagonal,
    a gold star in the hoist."""
    im = Image.new("RGB", (W, H), (120, 20, 25))
    d = ImageDraw.Draw(im)
    d.polygon([(W, 0), (W, H), (0, H)], fill=(20, 20, 20))
    star(d, W * 0.22, H * 0.33, H * 0.2, (235, 180, 30))
    return im


def splm():
    """The SPLM/A flag: black, red and green with white edging, a blue hoist
    triangle with a gold star."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.31, W, H * 0.69], fill=(255, 255, 255))
    d.rectangle([0, H * 0.36, W, H * 0.64], fill=(200, 16, 46))
    d.rectangle([0, H * 0.69, W, H], fill=(255, 255, 255))
    d.rectangle([0, H * 0.74, W, H], fill=(7, 137, 48))
    d.polygon([(0, 0), (W * 0.36, H / 2), (0, H)], fill=(15, 71, 175))
    star(d, W * 0.12, H / 2, H * 0.14, (252, 221, 9))
    return im


def somaliland():
    """Green, white and red, a black star in the white; the creed on the green
    is drawn as a plain white line."""
    im = Image.new("RGB", (W, H), (0, 153, 72))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H / 3, W, H * 2 / 3], fill=(255, 255, 255))
    d.rectangle([0, H * 2 / 3, W, H], fill=(206, 17, 38))
    star(d, W / 2, H / 2, H * 0.14, (0, 0, 0))
    d.line([(W * 0.3, H * 0.17), (W * 0.7, H * 0.17)], fill=(255, 255, 255), width=5)
    return im


SOMALI_BLUE = (65, 137, 221)


def puntland():
    """Our design for Puntland (it flew the Somali flag in 2000): Somali blue,
    white and green, the white star on the blue."""
    im = Image.new("RGB", (W, H), SOMALI_BLUE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.5, W, H * 0.6], fill=(255, 255, 255))
    d.rectangle([0, H * 0.6, W, H], fill=(0, 140, 70))
    star(d, W / 2, H * 0.25, H * 0.17, (255, 255, 255))
    return im


# The Somali factions fought under the Somali flag or none. These are our own
# designs on its blue and white star, one colour each.

def somali_faction(colour, layout):
    def draw():
        im = Image.new("RGB", (W, H), SOMALI_BLUE)
        d = ImageDraw.Draw(im)
        if layout == "low":
            d.rectangle([0, H * 0.62, W, H], fill=colour)
            star(d, W * 0.25, H * 0.31, H * 0.18, (255, 255, 255))
        elif layout == "hoist":
            d.rectangle([0, 0, W * 0.3, H], fill=colour)
            star(d, W * 0.62, H / 2, H * 0.22, (255, 255, 255))
        elif layout == "field":
            im.paste(colour, [0, 0, W, H])
            d.rectangle([0, H * 0.42, W, H * 0.58], fill=SOMALI_BLUE)
            star(d, W * 0.2, H * 0.22, H * 0.15, (255, 255, 255))
        elif layout == "diagonal":
            im.paste(colour, [0, 0, W, H])
            d.polygon([(0, H), (W * 0.2, H), (W, H * 0.2), (W, 0), (W * 0.8, 0), (0, H * 0.8)], fill=SOMALI_BLUE)
            star(d, W * 0.2, H * 0.25, H * 0.15, (255, 255, 255))
        elif layout == "disc":
            im.paste(colour, [0, 0, W, H])
            r = H * 0.3
            d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=SOMALI_BLUE)
            star(d, W / 2, H / 2, r * 0.75, (255, 255, 255))
        return im
    return draw


def comoros():
    """1996-2001: green, a white crescent and four white stars (the Arabic
    inscriptions are left out)."""
    im = Image.new("RGB", (W, H), (0, 130, 60))
    d = ImageDraw.Draw(im)
    cx, cy, r = W / 2, H / 2, H * 0.3
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    d.ellipse([cx - r * 0.55, cy - r * 1.05, cx + r * 1.45, cy + r * 0.95], fill=(0, 130, 60))
    for i in range(4):
        star(d, cx + r * 0.55, cy - r * 0.75 + i * r * 0.5, H * 0.05, (255, 255, 255))
    return im


def anjouan():
    """Our rendering of the Anjouan banner: red, a white open hand inside a
    white crescent."""
    red = (190, 20, 40)
    im = Image.new("RGB", (W, H), red)
    d = ImageDraw.Draw(im)
    cx, cy, r = W * 0.5, H / 2, H * 0.4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    d.ellipse([cx - r * 0.62, cy - r * 0.9, cx + r * 1.12, cy + r * 0.9], fill=red)
    u = H * 0.045                                  # the hand, palm up
    px, py = cx + r * 0.05, cy + u * 1.5
    d.rounded_rectangle([px - 2.2 * u, py - 1.5 * u, px + 2.2 * u, py + 2.6 * u], radius=u, fill=(255, 255, 255))
    for i, h in enumerate((3.2, 4.0, 3.8, 3.0)):
        x = px - 2.2 * u + i * 1.15 * u
        d.rounded_rectangle([x, py - 1.5 * u - h * u, x + 0.95 * u, py - 1.0 * u], radius=u * 0.45, fill=(255, 255, 255))
    d.polygon([(px + 2.2 * u, py + 0.5 * u), (px + 3.9 * u, py - 1.6 * u), (px + 4.5 * u, py - 1.0 * u),
               (px + 2.2 * u, py + 2.0 * u)], fill=(255, 255, 255))
    return im


def mauritius():
    """Red, blue, yellow and green."""
    im = Image.new("RGB", (W, H), (234, 40, 57))
    d = ImageDraw.Draw(im)
    for i, c in enumerate([(26, 32, 109), (255, 214, 0), (0, 165, 81)], start=1):
        d.rectangle([0, H * i / 4, W, H], fill=c)
    return im


def seychelles():
    """Five bands fanning out from the lower hoist: blue, yellow, red, white,
    green."""
    im = Image.new("RGB", (W, H), (0, 63, 135))
    d = ImageDraw.Draw(im)
    d.polygon([(0, H), (W / 3, 0), (W * 2 / 3, 0)], fill=(252, 216, 86))
    d.polygon([(0, H), (W * 2 / 3, 0), (W, 0), (W, H / 3)], fill=(214, 40, 40))
    d.polygon([(0, H), (W, H / 3), (W, H * 2 / 3)], fill=(255, 255, 255))
    d.polygon([(0, H), (W, H * 2 / 3), (W, H)], fill=(0, 122, 61))
    return im


def crescent_star(d, cx, cy, r, colour, bg, star_scale=0.45, flip=False):
    """A crescent opening to the fly (or the hoist), with a star in its mouth."""
    k = -1 if flip else 1
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)
    d.ellipse([cx - r * 0.8 + k * r * 0.3, cy - r * 0.8, cx + r * 0.8 + k * r * 0.3, cy + r * 0.8], fill=bg)
    star(d, cx + k * r * 1.05, cy, r * star_scale, colour)


def sadr():
    """Black, white and green, a red hoist triangle, a red crescent and star
    on the white."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H / 3, W, H * 2 / 3], fill=(255, 255, 255))
    d.rectangle([0, H * 2 / 3, W, H], fill=(0, 122, 61))
    d.polygon([(0, 0), (W * 0.33, H / 2), (0, H)], fill=(206, 17, 38))
    crescent_star(d, W * 0.5, H / 2, H * 0.13, (206, 17, 38), (255, 255, 255), 0.5, flip=True)
    return im


def sla():
    """Our design for the South Lebanon Army: white between dark green bands,
    a red cedar-like triangle."""
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H * 0.22], fill=(20, 90, 50))
    d.rectangle([0, H * 0.78, W, H], fill=(20, 90, 50))
    d.polygon([(W / 2, H * 0.28), (W * 0.38, H * 0.68), (W * 0.62, H * 0.68)], fill=(200, 30, 40))
    d.rectangle([W * 0.48, H * 0.66, W * 0.52, H * 0.74], fill=(200, 30, 40))
    return im


def sun(d, cx, cy, r, colour, rays=21):
    import math
    pts = []
    for i in range(rays * 2):
        a = i * math.pi / rays
        rr = r if i % 2 == 0 else r * 0.62
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=colour)


def kurdistan():
    """The flag of the Kurdistan Region, which the KDP flew: red, white and
    green with a golden sun."""
    im = Image.new("RGB", (W, H), (237, 28, 36))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H / 3, W, H * 2 / 3], fill=(255, 255, 255))
    d.rectangle([0, H * 2 / 3, W, H], fill=(39, 129, 64))
    sun(d, W / 2, H / 2, H * 0.21, (255, 190, 0))
    return im


def puk():
    """Our design for the PUK administration: green, a white band, the
    golden sun."""
    im = Image.new("RGB", (W, H), (30, 120, 60))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.4, W, H * 0.6], fill=(255, 255, 255))
    sun(d, W * 0.25, H / 2, H * 0.24, (255, 190, 0))
    return im


def north_cyprus():
    """White, two red stripes, a red crescent and star."""
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.1, W, H * 0.2], fill=(227, 10, 23))
    d.rectangle([0, H * 0.8, W, H * 0.9], fill=(227, 10, 23))
    crescent_star(d, W * 0.44, H / 2, H * 0.2, (227, 10, 23), (255, 255, 255), 0.4)
    return im


FLAGS = {"SAH": sadr, "SLA": sla, "KDP": kurdistan, "PUK": puk, "NCY": north_cyprus,
         "LES": lesotho, "SWZ": swaziland, "RCD": rcd_goma, "MLC": mlc, "RML": rcd_ml, "RUF": ruf,
         "SPL": splm, "SML": somaliland, "PNT": puntland,
         "SNA": somali_faction((180, 50, 50), "low"), "SSA": somali_faction((240, 160, 40), "hoist"),
         "HIR": somali_faction((110, 60, 130), "field"), "RRA": somali_faction((120, 160, 50), "low"),
         "JVA": somali_faction((30, 50, 120), "diagonal"), "SNF": somali_faction((200, 175, 110), "disc"),
         "COM": comoros, "ANJ": anjouan, "MUS": mauritius, "SEY": seychelles}


def save(img, path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize(size, Image.LANCZOS).convert("RGBA").save(path)


def main():
    for tag, draw in FLAGS.items():
        img = draw()
        save(img, MOD / f"gfx/flags/{tag}.tga", (82, 52))
        save(img, MOD / f"gfx/flags/medium/{tag}.tga", (41, 26))
        save(img, MOD / f"gfx/flags/small/{tag}.tga", (10, 7))
        print(f"wrote {tag}")


if __name__ == "__main__":
    main()
