"""3-bosqich: rasm generatsiyasi (Gemini / nano banana) + o'zbekcha sarlavha overlay."""
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import config

STYLE_SUFFIX = (
    "Editorial tech illustration, clean modern composition, soft studio lighting, "
    "shallow depth of field, muted dark background with one bright accent color, "
    "premium minimal aesthetic, square 1:1 format. "
    "IMPORTANT: absolutely no text, no letters, no words, no numbers, no UI labels in the image."
)


def generate(gem, image_prompt: str, title: str) -> bytes:
    prompt = f"{image_prompt.strip()}. {STYLE_SUFFIX}"
    raw = gem.image(config.MODEL_IMAGE, prompt)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = _fit_square(img, config.IMAGE_SIZE)
    if config.OVERLAY_TITLE and title:
        img = _overlay(img, title)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _fit_square(img: Image.Image, size) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2,
                    (w - side) // 2 + side, (h - side) // 2 + side))
    return img.resize(size, Image.LANCZOS)


def _font(size: int):
    for path in (config.FONT_BOLD,
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _overlay(img: Image.Image, title: str) -> Image.Image:
    """Pastki qismga qorong'i gradient va o'zbekcha sarlavha qo'yadi.
    Matnni Gemini emas, biz chizamiz — shuning uchun o'/g' harflari toza chiqadi."""
    W, H = img.size

    # pastdan yuqoriga qorayish
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.42) / (H * 0.58))
        grad.putpixel((0, y), int(235 * (t ** 1.5)))
    grad = grad.resize((W, H))
    shade = Image.new("RGB", (W, H), (8, 10, 14))
    img = Image.composite(shade, img, grad.filter(ImageFilter.GaussianBlur(2)))

    draw = ImageDraw.Draw(img)
    size = int(W * 0.075)
    font = _font(size)
    words = title.strip().split()
    wrap = 18 if len(words) > 3 else 14
    lines = textwrap.wrap(title.strip(), width=wrap)[:3]

    # sig'masa shriftni kichraytiramiz
    while size > 28 and max(draw.textlength(l, font=font) for l in lines) > W * 0.84:
        size -= 4
        font = _font(size)

    lh = int(size * 1.22)
    y = H - int(H * 0.085) - lh * len(lines)
    for line in lines:
        x = int(W * 0.08)
        draw.text((x + 2, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += lh

    # brend aksent chizig'i
    accent = config.BRAND_ACCENT.lstrip("#")
    rgb = tuple(int(accent[i:i + 2], 16) for i in (0, 2, 4))
    bar_y = H - int(H * 0.085) - lh * len(lines) - int(H * 0.035)
    draw.rounded_rectangle(
        [int(W * 0.08), bar_y, int(W * 0.08) + int(W * 0.11), bar_y + int(H * 0.011)],
        radius=int(H * 0.006), fill=rgb)
    return img
