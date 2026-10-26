"""Builds the TV mockups used in the README from the raw 960x540 screenshots in this folder.
Run with Pillow installed: python3 docs/screenshots/make-mockups.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / 'mockups'
SCREEN = (1280, 720)


def background(size):
    w, h = size
    bg = Image.new('RGB', size)
    top, bottom = (24, 30, 42), (9, 11, 16)
    px = bg.load()
    for y in range(h):
        t = y / max(1, h - 1)
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = row
    glow = Image.new('L', size, 0)
    ImageDraw.Draw(glow).ellipse((w * 0.15, h * 0.05, w * 0.85, h * 0.75), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(w // 8))
    return Image.composite(Image.new('RGB', size, (52, 66, 92)), bg, glow)


def tv(shot):
    """Returns an RGBA TV with the screenshot on its panel."""
    sw, sh = SCREEN
    bezel, radius = 16, 22
    stand_h = 120
    w, h = sw + bezel * 2, sh + bezel * 2 + stand_h
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Stand: thin neck and a wide, low foot.
    cx = w // 2
    d.rounded_rectangle((cx - 26, sh + bezel * 2 - 10, cx + 26, sh + bezel * 2 + 70), 8, fill=(38, 40, 46, 255))
    d.rounded_rectangle((cx - 230, sh + bezel * 2 + 62, cx + 230, sh + bezel * 2 + 82), 10, fill=(48, 50, 57, 255))
    # Frame with a faint edge highlight.
    d.rounded_rectangle((0, 0, w - 1, sh + bezel * 2 - 1), radius, fill=(14, 15, 18, 255), outline=(70, 74, 84, 255), width=2)
    panel = Image.open(shot).convert('RGB').resize(SCREEN, Image.LANCZOS)
    mask = Image.new('L', SCREEN, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw - 1, sh - 1), 8, fill=255)
    img.paste(panel, (bezel, bezel), mask)
    # Soft reflection across the top of the glass.
    sheen = Image.new('L', SCREEN, 0)
    ImageDraw.Draw(sheen).polygon([(0, 0), (int(sw * 0.55), 0), (int(sw * 0.32), sh), (0, sh)], fill=14)
    img.paste(Image.new('RGBA', SCREEN, (255, 255, 255, 255)), (bezel, bezel), Image.composite(sheen, Image.new('L', SCREEN, 0), mask))
    return img


def place(canvas, item, pos):
    """Pastes item with a soft floor shadow under it."""
    x, y = pos
    w, h = item.size
    shadow = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(shadow).ellipse((x + w * 0.18, y + h - 40, x + w * 0.82, y + h + 6), fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.paste(Image.new('RGB', canvas.size, (0, 0, 0)), (0, 0), shadow)
    canvas.paste(item, pos, item)


def single(name):
    t = tv(HERE / (name + '.jpg'))
    pad = 90
    canvas = background((t.width + pad * 2, t.height + pad * 2))
    place(canvas, t, (pad, pad))
    canvas.save(OUT / (name + '.jpg'), quality=90)


def pair(left, right, name):
    a, b = tv(HERE / (left + '.jpg')), tv(HERE / (right + '.jpg'))
    gap, pad = 120, 90
    canvas = background((a.width + b.width + gap + pad * 2, a.height + pad * 2))
    place(canvas, a, (pad, pad))
    place(canvas, b, (pad + a.width + gap, pad))
    canvas = canvas.resize((canvas.width * 2 // 3, canvas.height * 2 // 3), Image.LANCZOS)
    canvas.save(OUT / (name + '.jpg'), quality=90)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    pair('before', 'after', 'before-after')
    for shot in ('after', 'adhan', 'screensaver', 'settings', 'city-search'):
        single(shot)
    print('mockups written to', OUT)
