"""Brend vizuali.

Ikki rejimda ishlaydi:
  - background=None  -> to'liq o'zi chizadi (bepul brend kartochkasi)
  - background=bytes -> AI rasmni fon qilib oladi, ustiga brend qatlamini qo'yadi

Ikkala holatda ham sarlavhani PIL chizadi — shuning uchun o'zbekcha o'/g' toza chiqadi.
"""
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"),
    "/usr/share/fonts/truetype/google-fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/freefont",
    "/nix/store",
]
FONT_CANDIDATES = {
    "bold": ["Poppins-Bold.ttf", "Inter-Bold.ttf", "Montserrat-Bold.ttf",
             "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "FreeSansBold.ttf"],
    "regular": ["Poppins-Regular.ttf", "Inter-Regular.ttf", "Montserrat-Regular.ttf",
                "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf"],
}

BG = (11, 14, 18)
FG = (255, 255, 255)
MUTED = (170, 178, 190)
_FONT_CACHE = {}


def _font(kind: str, size: int):
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    for d in FONT_DIRS[:-1]:
        for name in FONT_CANDIDATES[kind]:
            p = os.path.join(d, name)
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                _FONT_CACHE[key] = f
                return f
    # nixpacks muhitida shriftlar boshqa joyda bo'lishi mumkin — qidiramiz
    for root, _, files in os.walk("/nix/store"):
        for name in FONT_CANDIDATES[kind]:
            if name in files:
                f = ImageFont.truetype(os.path.join(root, name), size)
                _FONT_CACHE[key] = f
                return f
        if root.count(os.sep) > 5:
            break
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def _hex(c: str):
    """Rangni o'qiydi. Bo'sh yoki noto'g'ri bo'lsa — standart aksent."""
    c = (c or "").strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in c):
        c = "E8FF59"
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _fit_square(img: Image.Image, size) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2,
                    (w - side) // 2 + side, (h - side) // 2 + side))
    return img.resize(size, Image.LANCZOS)


def _darken_bottom(img: Image.Image) -> Image.Image:
    """Pastki yarmini qoraytiradi — matn har qanday rasmda o'qiladigan bo'lsin."""
    W, H = img.size
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.30) / (H * 0.70))
        grad.putpixel((0, y), int(240 * (t ** 1.25)))
    grad = grad.resize((W, H)).filter(ImageFilter.GaussianBlur(3))
    return Image.composite(Image.new("RGB", (W, H), (6, 8, 11)), img, grad)


def _glow(img, accent, size):
    W, H = size
    layer = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(layer)
    cx, cy, r = int(W * 0.86), int(H * 0.16), int(W * 0.34)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
    layer = layer.filter(ImageFilter.GaussianBlur(int(W * 0.12)))
    return Image.blend(img, layer, 0.13)


def _grid(draw, size):
    W, H = size
    step = int(W / 18)
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=(20, 25, 32), width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=(20, 25, 32), width=1)


def _fit_text(draw, text, start, min_size, max_w, max_lines, wrap_at):
    size, wrap = start, wrap_at
    while size > min_size:
        f = _font("bold", size)
        lines = textwrap.wrap(text, width=wrap)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
        size -= 4
        wrap += 1
    f = _font("bold", min_size)
    return f, textwrap.wrap(text, width=wrap)[:max_lines]


def make_card(title: str, label: str = "CLAUDE MASLAHATLAR",
              handle: str = "@Siroj_aiPro_Academy", accent: str = "#E8FF59",
              size=(1080, 1080), background: bytes = None) -> bytes:
    W, H = size
    acc = _hex(accent)

    if background:
        img = _fit_square(Image.open(io.BytesIO(background)).convert("RGB"), size)
        img = _darken_bottom(img)
    else:
        img = Image.new("RGB", size, BG)
        _grid(ImageDraw.Draw(img), size)
        img = _glow(img, acc, size)

    d = ImageDraw.Draw(img)
    pad = int(W * 0.085)

    # yuqori yorliq — aksent rangli plashka ichida (har qanday fonda o'qiladi)
    lf = _font("bold", int(W * 0.026))
    ltext = " ".join(label.upper())
    lw = d.textlength(ltext, font=lf)
    px, py = int(W * 0.022), int(W * 0.016)
    d.rounded_rectangle([pad, pad, pad + lw + px * 2, pad + lf.size + py * 2],
                        radius=int(W * 0.008), fill=acc)
    d.text((pad + px, pad + py - int(lf.size * 0.08)), ltext, font=lf, fill=(10, 12, 16))

    # sarlavha
    tf, lines = _fit_text(d, title, int(W * 0.105), int(W * 0.05), W - pad * 2, 4, 16)
    lh = int(tf.size * 1.16)
    y = int(H * (0.68 if background else 0.60)) - (lh * len(lines)) // 2

    bar_top = y - int(H * 0.05)
    d.rounded_rectangle([pad, bar_top, pad + int(W * 0.10), bar_top + int(H * 0.010)],
                        radius=int(H * 0.005), fill=acc)
    for line in lines:
        d.text((pad + 2, y + 3), line, font=tf, fill=(0, 0, 0))
        d.text((pad, y), line, font=tf, fill=FG)
        y += lh

    # pastki qator
    hf = _font("regular", int(W * 0.025))
    d.text((pad, H - pad - int(W * 0.025)), handle, font=hf, fill=MUTED)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "Har safar noldan boshlamang"
    open("card.png", "wb").write(make_card(t))
    print("card.png yozildi")
