"""Brend tipografik kartochka — AI rasm generatsiyasisiz, mutlaqo bepul va barqaror.

Nega bu yaxshi:
- Har bir post bir xil brend ko'rinishida bo'ladi (AI rasm har safar boshqacha chiqadi)
- O'zbekcha matn 100% toza chiqadi
- Pul turmaydi, API limitiga bog'liq emas, hech qachon "xato" bermaydi
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
]
FONT_CANDIDATES = {
    "bold": ["Poppins-Bold.ttf", "Inter-Bold.ttf", "Montserrat-Bold.ttf",
             "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "regular": ["Poppins-Regular.ttf", "Inter-Regular.ttf", "Montserrat-Regular.ttf",
                "DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
}

BG = (11, 14, 18)
FG = (255, 255, 255)
MUTED = (138, 148, 163)


def _font(kind: str, size: int):
    for d in FONT_DIRS:
        for name in FONT_CANDIDATES[kind]:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _glow(img, accent, size):
    """Yumshoq rangli yorug'lik — o'ng yuqori burchakda."""
    W, H = size
    layer = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(layer)
    cx, cy, r = int(W * 0.86), int(H * 0.16), int(W * 0.34)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
    layer = layer.filter(ImageFilter.GaussianBlur(int(W * 0.12)))
    return Image.blend(img, layer, 0.13)


def _grid(draw, size):
    """Sezilar-sezilmas to'r — fon jonli ko'rinishi uchun."""
    W, H = size
    step = int(W / 18)
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=(20, 25, 32), width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=(20, 25, 32), width=1)


def _fit(draw, text, kind, start, min_size, max_w, max_lines, wrap_at):
    """Sarlavha maydonga sig'guncha shriftni kichraytiradi."""
    size = start
    while size > min_size:
        f = _font(kind, size)
        lines = textwrap.wrap(text, width=wrap_at)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
        size -= 4
        wrap_at += 1
    f = _font(kind, min_size)
    return f, textwrap.wrap(text, width=wrap_at)[:max_lines]


def make_card(title: str, label: str = "CLAUDE MASLAHATLAR",
              handle: str = "@Siroj_aiPro_Academy",
              accent: str = "#E8FF59", size=(1080, 1080)) -> bytes:
    W, H = size
    acc = _hex(accent)

    img = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(img)
    _grid(d, size)
    img = _glow(img, acc, size)
    d = ImageDraw.Draw(img)

    pad = int(W * 0.085)

    # --- yuqori yorliq ---
    lf = _font("bold", int(W * 0.026))
    spaced = " ".join(label.upper())
    d.text((pad, pad), spaced, font=lf, fill=acc)

    # --- sarlavha ---
    tf, lines = _fit(d, title, "bold", int(W * 0.105), int(W * 0.05),
                     W - pad * 2, 4, 16)
    lh = int(tf.size * 1.16)
    block_h = lh * len(lines)
    y = int(H * 0.60) - block_h // 2
    bar_top = y - int(H * 0.05)
    d.rounded_rectangle([pad, bar_top, pad + int(W * 0.10), bar_top + int(H * 0.010)],
                        radius=int(H * 0.005), fill=acc)
    for line in lines:
        d.text((pad, y), line, font=tf, fill=FG)
        y += lh

    # --- pastki qator ---
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
