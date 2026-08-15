"""Retro plakat uslubidagi vizual — sovet plakatlari ruhida.

Sirojning tanlagan uslubi: sarg'ish eski qog'oz, qip-qizil geometrik bloklar,
qalin katta shrift, matn rasm ichida, logotipsiz.

Matnni AI emas, biz chizamiz — shuning uchun o'zbekcha o' va g' har doim toza.
"""
import io
import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(BASE, "fonts")

PAPER = (232, 224, 206)     # eski qog'oz
INK = (26, 24, 22)          # deyarli qora
RED = (196, 40, 33)         # plakat qizili
CREAM = (243, 238, 226)
_CACHE = {}


def _font(name: str, size: int):
    key = (name, size)
    if key in _CACHE:
        return _CACHE[key]
    for cand in ([name] if name.endswith(".ttf") else [f"{name}.ttf"]):
        p = os.path.join(FONTS, cand)
        if os.path.exists(p):
            f = ImageFont.truetype(p, size)
            _CACHE[key] = f
            return f
    for d in ("/usr/share/fonts/truetype/google-fonts",
              "/usr/share/fonts/truetype/dejavu"):
        for cand in ("Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"):
            p = os.path.join(d, cand)
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                _CACHE[key] = f
                return f
    return ImageFont.load_default()


def _paper_texture(size, seed=0):
    """Eski qog'oz: iliq fon + mayda don + burchaklarda qorayish."""
    W, H = size
    rnd = random.Random(seed)
    img = Image.new("RGB", size, PAPER)

    noise = Image.new("L", (W // 3, H // 3))
    noise.putdata([rnd.randint(120, 160) for _ in range((W // 3) * (H // 3))])
    noise = noise.resize(size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1))
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.10)

    vig = Image.new("L", size, 0)
    d = ImageDraw.Draw(vig)
    d.ellipse([-W * 0.25, -H * 0.25, W * 1.25, H * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W // 12))
    return Image.composite(img, Image.new("RGB", size, (196, 184, 162)), vig)


def _fit(draw, text, font_name, start, min_size, max_w, max_lines, wrap_at):
    size, wrap = start, wrap_at
    while size > min_size:
        f = _font(font_name, size)
        lines = textwrap.wrap(text, width=wrap)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
        size -= 4
        wrap += 1
    return _font(font_name, min_size), textwrap.wrap(text, width=wrap)[:max_lines]


def _diagonals(img, seed=0):
    """Burchaklardagi qizil geometrik zarbalar."""
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([(0, 0), (W * 0.46, 0), (0, H * 0.30)], fill=RED + (255,))
    d.polygon([(W, H), (W, H * 0.80), (W * 0.62, H)], fill=RED + (210,))
    d.polygon([(W * 0.52, 0), (W * 0.62, 0), (W * 0.10, H * 0.42),
               (0, H * 0.42)], fill=RED + (60,))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def make_poster(title: str, kicker: str = "CLAUDE MASLAHATLAR",
                cta: str = "@Siroj_aiPro_Academy", illustration: bytes = None,
                size=(1080, 1080), seed: int = 0) -> bytes:
    W, H = size
    img = _paper_texture(size, seed)

    # --- illyustratsiya: butun fonni egallaydi ---
    if illustration:
        a = Image.open(io.BytesIO(illustration)).convert("RGB")
        ratio = max(W / a.width, H / a.height)
        a = a.resize((int(a.width * ratio), int(a.height * ratio)), Image.LANCZOS)
        a = a.crop(((a.width - W) // 2, (a.height - H) // 2,
                    (a.width - W) // 2 + W, (a.height - H) // 2 + H))
        warm = Image.new("RGB", (W, H), (238, 220, 192))
        img = Image.blend(a, warm, 0.20)          # eski qog'oz tusi
        img = Image.blend(img, _paper_texture(size, seed), 0.18)  # don va eskilik

        # chap tomonga och parda — sarlavha o'qiladigan bo'lsin
        scrim = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(scrim)
        for x in range(int(W * 0.72)):
            sd.line([(x, 0), (x, H)], fill=int(225 * (1 - x / (W * 0.72)) ** 1.3))
        img = Image.composite(Image.new("RGB", (W, H), CREAM), img,
                              scrim.filter(ImageFilter.GaussianBlur(6)))

    img = _diagonals(img, seed)
    d = ImageDraw.Draw(img)
    pad = int(W * 0.06)
    col_w = int(W * (0.60 if illustration else 0.88))

    # --- kicker: qora plashka ---
    kf = _font("Oswald-Bold", int(W * 0.028))
    kt = " ".join(kicker.upper())
    kw = d.textlength(kt, font=kf)
    d.rectangle([pad, pad, pad + kw + int(W * 0.05), pad + int(W * 0.062)], fill=INK)
    d.text((pad + int(W * 0.025), pad + int(W * 0.014)), kt, font=kf, fill=CREAM)

    # --- sarlavha: Anton, katta, qora ---
    tf, lines = _fit(d, title.upper(), "Anton-Regular",
                     int(W * 0.115), int(W * 0.055), col_w, 5, 13)
    lh = int(tf.size * 0.98)
    y = int(H * 0.20)
    for i, line in enumerate(lines):
        # birinchi qatorning ostiga qizil chiziq
        d.text((pad + 3, y + 4), line, font=tf, fill=(150, 140, 125))
        d.text((pad, y), line, font=tf, fill=INK if i else RED if len(lines) == 1 else INK)
        y += lh

    d.rectangle([pad, y + int(H * 0.02), pad + int(W * 0.16), y + int(H * 0.028)], fill=RED)

    # --- pastki qizil lenta: kanal nomi ---
    cf = _font("Oswald-Bold", int(W * 0.030))
    ct = " ".join(cta.upper())
    cw = d.textlength(ct, font=cf)
    bh = int(W * 0.068)
    d.rectangle([0, H - bh, cw + pad * 2 + int(W * 0.03), H], fill=RED)
    d.text((pad, H - bh + int(W * 0.017)), ct, font=cf, fill=CREAM)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "Har safar noldan boshlamang"
    open("poster.png", "wb").write(make_poster(t))
    print("poster.png yozildi")


def make_stat_poster(big: str, small: str = "", note: str = "",
                     kicker: str = "HAQIQIY VOQEA", lines=None,
                     cta: str = "SUN'IY INTELLEKT BILAN DAROMAD",
                     size=(1080, 1080), seed: int = 0) -> bytes:
    """Katta raqamli plakat — vebinar kanallari uchun.

    big   — eng katta yozuv (masalan "$150 000" yoki "10 KUN")
    small — ustidagi kichikroq (masalan "$185 DAN")
    note  — qizil kichik yozuv (masalan "7 OYDA")
    lines — pastdagi 1-3 qator izoh
    """
    W, H = size
    img = _paper_texture(size, seed)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.polygon([(0, 0), (W * 0.42, 0), (0, H * 0.27)], fill=RED + (255,))
    ld.polygon([(W, H), (W, H * 0.72), (W * 0.52, H)], fill=RED + (230,))
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    d = ImageDraw.Draw(img)
    pad = int(W * 0.07)

    def put(text, font, fill, y, shadow=None):
        if not text:
            return y
        if shadow:
            d.text((pad + 4, y + 5), text, font=font, fill=shadow)
        d.text((pad, y), text, font=font, fill=fill)
        a = font.getbbox(text)
        return y + (a[3] - a[1]) + int(font.size * 0.30)

    kf = _font("Oswald-Bold", int(W * 0.030))
    kt = " ".join(kicker.upper())
    kw = d.textlength(kt, font=kf)
    d.rectangle([pad, pad, pad + kw + int(W * 0.055), pad + int(W * 0.068)], fill=INK)
    d.text((pad + int(W * 0.027), pad + int(W * 0.016)), kt, font=kf, fill=CREAM)

    y = int(H * 0.215)
    y = put(small.upper(), _font("Anton-Regular", int(W * 0.105)), INK, y)
    y = put(note.upper(), _font("Oswald-Bold", int(W * 0.040)), RED, y)
    y += int(H * 0.012)

    bs = int(W * 0.170)
    bf = _font("Anton-Regular", bs)
    while bs > int(W * 0.075) and d.textlength(big.upper(), font=bf) > W - pad * 2:
        bs -= 6
        bf = _font("Anton-Regular", bs)
    y = put(big.upper(), bf, RED, y, shadow=(170, 152, 126))

    y += int(H * 0.015)
    d.rectangle([pad, y, pad + int(W * 0.20), y + int(H * 0.008)], fill=INK)
    y += int(H * 0.048)

    f5 = _font("Oswald-Bold", int(W * 0.033))
    for line in (lines or [])[:3]:
        d.text((pad, y), line, font=f5, fill=(52, 48, 44))
        y += int(W * 0.050)

    cf = _font("Oswald-Bold", int(W * 0.029))
    ct = " ".join(cta.upper())
    cw = d.textlength(ct, font=cf)
    bh = int(W * 0.068)
    d.rectangle([0, H - bh, cw + pad * 2, H], fill=RED)
    d.text((pad, H - bh + int(W * 0.019)), ct, font=cf, fill=CREAM)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
