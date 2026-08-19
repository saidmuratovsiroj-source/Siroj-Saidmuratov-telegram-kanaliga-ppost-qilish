"""Post rasmi — toza, minimal, oq fon + yumshoq 3D personaj.

Siroj tanlagan yo'nalish (KSV.DESIGN uslubidagi namunalar):
  - butunlay OQ fon, ko'p bo'sh joy
  - yumshoq 3D (Pixar) personaj — Sirojning o'zi, pastki qismda
  - yupqa, tinch tipografika: Poppins, katta harflar orasi keng
  - pastel urg'u rangi (yalpiz, siyohrang, moviy, shaftoli)

Muhim: MATNNI AI EMAS, SHU KOD CHIZADI. Shuning uchun o'zbekcha o' va g'
har doim toza chiqadi. AI faqat matnsiz illyustratsiya beradi.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

import config

W = H = 1080
MARGIN = 84
TEXT_W = W - MARGIN * 2

# --- Palitra ---
PAPER = (255, 255, 255)
INK = (26, 26, 28)
GREY = (138, 140, 146)
LINE = (228, 228, 232)

# Pastel urg'u ranglari — post turiga qarab navbat bilan
MINT = (122, 197, 164)
LILAC = (150, 138, 204)
BLUE = (110, 158, 214)
PEACH = (214, 148, 112)
ACCENTS = [MINT, LILAC, BLUE, PEACH]

GF = "/usr/share/fonts/truetype/google-fonts"
FONT_DIR = os.path.join(config.BASE_DIR, "fonts")


def _font_path(name, fallback):
    for base in (FONT_DIR, GF):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return fallback


F_BOLD = _font_path("Poppins-Bold.ttf", os.path.join(FONT_DIR, "Oswald-Bold.ttf"))
F_MED = _font_path("Poppins-Medium.ttf", F_BOLD)
F_REG = _font_path("Poppins-Regular.ttf", F_BOLD)
F_LIGHT = _font_path("Poppins-Light.ttf", F_REG)


def clean(text: str) -> str:
    """Emoji va shrift qo'llamaydigan belgilarni olib tashlaydi —
    Telegramda kvadratcha chiqmasin."""
    if not text:
        return ""
    keep = []
    for ch in text:
        if ord(ch) < 0x2000 or ch in "‘’“”–—…":
            keep.append(ch)
        else:
            keep.append(" ")
    return " ".join("".join(keep).split())


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _w(d, text, font):
    return d.textbbox((0, 0), text, font=font)[2]


def _wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if _w(d, test, font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _fit(d, text, path, max_w, max_lines, start, minimum=34):
    size = start
    while size > minimum:
        f = _font(path, size)
        lines = _wrap(d, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 3
    f = _font(path, minimum)
    return f, _wrap(d, text, f, max_w)[:max_lines]


# --------------------------------------------------------------- yordamchi
def _tracked(d, text, font, y, fill, track=6, center=True, x=MARGIN):
    """Harflar orasi keng yozuv — namunalardagi tinch sarlavha."""
    widths = [_w(d, ch, font) for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    cx = (W - total) // 2 if center else x
    for ch, cw in zip(text, widths):
        d.text((cx, y), ch, font=font, fill=fill)
        cx += cw + track
    return total


def _centered(d, lines, font, y, fill, leading=1.28):
    lh = int(font.size * leading)
    for ln in lines:
        d.text(((W - _w(d, ln, font)) // 2, y), ln, font=font, fill=fill)
        y += lh
    return y


ART_SCALE = 0.74   # personaj kvadratning qancha qismini egallaydi


def _base(illustration):
    """Oq lavha + personaj pastda. Yuqorisi matn uchun toza oq qoladi."""
    canvas = Image.new("RGB", (W, H), PAPER)
    if not illustration:
        return canvas
    try:
        im = Image.open(io.BytesIO(illustration)).convert("RGB")
    except Exception as e:
        print(f"[poster] illyustratsiya ochilmadi ({e}) — faqat oq fon")
        return canvas
    side = int(W * ART_SCALE)
    im = im.resize((side, side), Image.LANCZOS)
    # Fonning och-kulrang joylarini toza oqqa aylantiramiz — chetlarida
    # to'rtburchak izi qolmasin
    im = im.point(lambda v: 255 if v >= 242 else int(v * 1.02))
    canvas.paste(im, ((W - side) // 2, H - side))

    # Yumshoq oq parda: matn zonasi har doim toza bo'lsin
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    solid, fade = int(H * 0.34), int(H * 0.46)
    vd.rectangle([0, 0, W, solid], fill=PAPER + (255,))
    for y in range(solid, fade):
        t = 1 - (y - solid) / (fade - solid)
        vd.line([(0, y), (W, y)], fill=PAPER + (int(255 * t),))
    return Image.alpha_composite(canvas.convert("RGBA"), veil).convert("RGB")


def _chrome(d, brand, handle):
    """Yuqori qatordagi ikkita kichik yozuv."""
    f = _font(F_LIGHT, 22)
    if brand:
        _tracked(d, clean(brand).upper(), f, 52, GREY, track=4,
                 center=False, x=MARGIN)
    if handle:
        t = clean(handle)
        d.text((W - MARGIN - _w(d, t, f), 52), t, font=f, fill=GREY)


def _rule(d, y, accent, width=96):
    d.rounded_rectangle([(W - width) // 2, y, (W + width) // 2, y + 5],
                        radius=3, fill=accent)


# ---------------------------------------------------------------- asosiy
def make_poster(title, kicker="", cta="", illustration=None, seed=0, note=""):
    """Oddiy post: kichik rubrika + katta sarlavha + izoh."""
    accent = ACCENTS[seed % len(ACCENTS)]
    canvas = _base(illustration)
    d = ImageDraw.Draw(canvas)

    _chrome(d, "AI PRO ACADEMY", cta)

    y = 150
    if kicker:
        _tracked(d, clean(kicker).upper(), _font(F_MED, 24), y, accent, track=7)
        y += 44
        _rule(d, y, accent)
        y += 40

    f, lines = _fit(d, clean(title), F_BOLD, TEXT_W, max_lines=3, start=76)
    y = _centered(d, lines, f, y, INK) + 10

    if note:
        fn = _font(F_LIGHT, 32)
        y = _centered(d, _wrap(d, clean(note), fn, TEXT_W - 80)[:2], fn, y, GREY)
    return _png(canvas)


def make_stat_poster(big, small="", note="", kicker="", lines=None, cta="", seed=0,
                     illustration=None):
    """Vebinar posti: rubrika + katta sarlavha + bitta qatorli mazmun."""
    accent = ACCENTS[seed % len(ACCENTS)]
    canvas = _base(illustration)
    d = ImageDraw.Draw(canvas)

    _chrome(d, "AI PRO ACADEMY", cta)

    y = 146
    if kicker:
        _tracked(d, clean(kicker).upper(), _font(F_MED, 24), y, accent, track=7)
        y += 44
        _rule(d, y, accent)
        y += 38

    f, blines = _fit(d, clean(big), F_BOLD, TEXT_W, max_lines=2, start=84)
    y = _centered(d, blines, f, y, INK) + 6

    if small:
        fs = _font(F_LIGHT, 34)
        y = _centered(d, _wrap(d, clean(small), fs, TEXT_W - 60)[:2], fs, y, GREY) + 14

    items = [clean(x) for x in (lines or []) if clean(x)]
    if items:
        fl = _font(F_REG, 26)
        joined = "  ·  ".join(items[:3])
        rows = _wrap(d, joined, fl, TEXT_W - 60)[:2]
        y = _centered(d, rows, fl, y, INK, leading=1.45) + 10

    if note:
        fn = _font(F_LIGHT, 26)
        _centered(d, _wrap(d, clean(note), fn, TEXT_W - 80)[:1], fn, y, GREY)
    return _png(canvas)


def _png(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


if __name__ == "__main__":
    open("poster.png", "wb").write(
        make_poster("Claude fayllarni o'zi yaratadi", kicker="Claude maslahatlar",
                    note="Excel, Word, PDF — suhbatning o'zida",
                    cta="@Siroj_aiPro_Academy", seed=0))
    print("poster.png yozildi")
