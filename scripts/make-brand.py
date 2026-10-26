"""Render the Xee Launcher splash screen and app icons from the bundled open fonts.

Run: .venv/bin/python scripts/make-brand.py  (needs Pillow, arabic-reshaper, python-bidi)
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / 'launcher' / 'fonts'
GOLD = (217, 180, 106)
INK = (6, 9, 12)


def outfit(size, weight):
    font = ImageFont.truetype(str(FONTS / 'outfit.ttf'), size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass
    return font


def arabic(size):
    return ImageFont.truetype(str(FONTS / 'NotoSansArabic.ttf'), size)


def shaped(text):
    # Pillow without libraqm draws glyphs left to right: shape and reorder first.
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def background(w, h):
    img = Image.new('RGB', (w, h), INK)
    glow = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(glow)
    for i in range(60, 0, -1):
        r = int(min(w, h) * 0.9 * i / 60)
        d.ellipse((w // 2 - r * 1.4, h // 2 - r, w // 2 + r * 1.4, h // 2 + r), fill=int(70 * (1 - i / 60) ** 1.6))
    tint = Image.new('RGB', (w, h), (20, 46, 38))
    img = Image.composite(tint, img, glow.filter(ImageFilter.GaussianBlur(40)))
    return img


def star_pattern(w, h, step, alpha):
    """A faint eight-pointed star lattice, the classic girih motif."""
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(-step, h + step, step):
        for x in range(-step, w + step, step):
            cx, cy, r = x + step / 2, y + step / 2, step * 0.36
            for rot in (0, math.pi / 4):
                pts = [(cx + r * math.cos(rot + k * math.pi / 2), cy + r * math.sin(rot + k * math.pi / 2)) for k in range(4)]
                d.polygon(pts, outline=GOLD + (alpha,))
    return layer


def crescent(draw, cx, cy, r, width, color):
    draw.arc((cx - r, cy - r, cx + r, cy + r), 40, 320, fill=color, width=width)
    draw.ellipse((cx + r * 0.62 - width * 1.3, cy - r * 0.42 - width * 1.3, cx + r * 0.62 + width * 1.3, cy - r * 0.42 + width * 1.3), fill=color)


def splash():
    w, h = 1920, 1080
    img = background(w, h).convert('RGBA')
    pattern = star_pattern(w, h, 120, 16)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).ellipse((w / 2 - 900, h / 2 - 620, w / 2 + 900, h / 2 + 620), fill=255)
    pattern.putalpha(Image.composite(pattern.getchannel('A'), Image.new('L', (w, h), 0), mask.filter(ImageFilter.GaussianBlur(160))))
    img.alpha_composite(pattern)
    d = ImageDraw.Draw(img)
    crescent(d, w // 2, 330, 56, 5, GOLD)
    big, light = outfit(170, 600), outfit(170, 200)
    xee, launcher = 'Xee', 'Launcher'
    gap = 34
    wx = d.textlength(xee, font=big)
    wl = d.textlength(launcher, font=light)
    x0 = (w - wx - gap - wl) / 2
    d.text((x0, 420), xee, font=big, fill=(255, 255, 255))
    d.text((x0 + wx + gap, 420), launcher, font=light, fill=GOLD)
    d.line((w / 2 - 70, 650, w / 2 + 70, 650), fill=GOLD + (160,), width=2)
    sub = arabic(40)
    text = shaped('واجهة إسلامية عربية لشاشتك')
    tw = d.textlength(text, font=sub)
    d.text(((w - tw) / 2, 680), text, font=sub, fill=(255, 255, 255, 170))
    img.convert('RGB').save(ROOT / 'launcher' / 'splash.jpg', quality=90)


def icon(size, path):
    img = background(size * 4, size * 4).convert('RGBA')
    d = ImageDraw.Draw(img)
    s = size * 4
    crescent(d, s // 2, s // 2 - s * 0.02, int(s * 0.3), max(4, s // 22), GOLD)
    f = outfit(int(s * 0.34), 600)
    tw = d.textlength('X', font=f)
    d.text(((s - tw) / 2 - s * 0.03, s * 0.29), 'X', font=f, fill=(255, 255, 255))
    rounded = Image.new('L', (s, s), 0)
    ImageDraw.Draw(rounded).rounded_rectangle((0, 0, s - 1, s - 1), radius=s // 5, fill=255)
    img.putalpha(rounded)
    img.resize((size, size), Image.LANCZOS).save(path)


if __name__ == '__main__':
    splash()
    icon(80, ROOT / 'launcher' / 'brand-v2-icon.png')
    icon(130, ROOT / 'launcher' / 'brand-v2-largeIcon.png')
    icon(192, ROOT / 'native' / 'app' / 'remote-ui' / 'icon-192.png')
    icon(512, ROOT / 'native' / 'app' / 'remote-ui' / 'icon-512.png')
    print('splash and icons written')
