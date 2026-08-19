"""AI illyustratsiya + yorqin 3D tipografika.

IMAGE_MODE=ai bo'lganda:
  1. Gemini 3D uslubdagi illyustratsiya yasaydi (MATNSIZ)
  2. brand/character.png berilsa — personaj Sirojga o'xshatiladi
  3. Ustiga poster.py tipografikasi qo'yiladi (nishoncha, sarlavha, kartochka)

Matnni AI emas, biz chizamiz — o'zbekcha o' va g' har doim toza chiqadi.
Agar rasm generatsiyasi ishlamasa (limit, xato) — matn plakati bilan davom etadi.
"""
import os
import config
from src import poster

CHARACTER = os.path.join(config.BASE_DIR, "brand", "character.png")

STYLE = (
    "Glossy 3D Pixar-style character illustration, modern animation-film quality. "
    "Vivid hot-pink / magenta / acid lime-green palette, glossy 3D blobs and bubbles, "
    "ultra saturated, very high contrast, clean and modern, strong rim light. "
    "The character stands in the RIGHT half of the frame; the LEFT 45 percent is "
    "clean empty background reserved for a headline. Square 1:1. "
    "STRICTLY FORBIDDEN: any text, letters, words, numbers, captions, slogans, "
    "logos, brand marks, flags, emblems or insignia of any kind."
)

CHARACTER_NOTE = (
    "Use the man from the reference photos as the main character. Keep his face, "
    "hair, beard and build recognisable, restyled as an appealing 3D cartoon character. "
)


def _character_bytes():
    if os.getenv("USE_CHARACTER", "1") != "1":
        return None
    if not os.path.exists(CHARACTER):
        return None
    try:
        with open(CHARACTER, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"[imagegen] personaj rasmi o'qilmadi: {e}")
        return None


def generate(gem, image_prompt: str, title: str) -> bytes:
    ref = _character_bytes()
    prompt = (CHARACTER_NOTE if ref else "") + f"{(image_prompt or '').strip()}. {STYLE}"

    art = None
    try:
        art = gem.image(config.MODEL_IMAGE, prompt, refs=[ref] if ref else None)
        print(f"[imagegen] illyustratsiya tayyor ({len(art)} bayt)"
              + (", personaj bilan" if ref else ""))
    except Exception as e:
        print(f"[imagegen] rasm chiqmadi ({e}) — matn plakati bilan davom etamiz")

    return poster.make_poster(
        title,
        kicker=config.RUBRIC,
        cta=config.CHANNEL_ID,
        illustration=art,
        seed=abs(hash(title)) % 9999,
    )
