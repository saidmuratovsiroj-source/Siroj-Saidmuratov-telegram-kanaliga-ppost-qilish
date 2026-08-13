"""2-bosqich: mavzuni Sirojning stilida postga aylantirish."""
import glob
import os
import config

SYSTEM = """Sen — Siroj Saidmuratovning shaxsiy kontent-yozuvchisisan. U O'zbekistonda
sun'iy intellekt o'rgatadi. Sen uning Telegram kanali uchun post yozasan va uning
OVOZIDA yozasan — o'zingnikida emas.

TIL: faqat o'zbek tili, lotin yozuvida. Rus yoki kirill harflari MUTLAQO bo'lmasin.
Ortiqcha "sun'iy intellekt yordamchisi" ohangi bo'lmasin — tirik, sodda, do'stona.

STIL QO'LLANMASI:
{style_guide}

MUALLIFNING HAQIQIY POSTLARI (ohang, ritm, tuzilma shulardan olinadi):
{examples}"""

PROMPT = """Quyidagi maslahat asosida bitta Telegram post yoz.

MAVZU: {title}
MASLAHAT: {tip}
NEGA FOYDALI: {why}
QADAMLAR: {how}
MISOL: {example}
DARAJA: {level}

TEXNIK TALABLAR:
- Uzunligi {lo}-{hi} belgi (Telegram rasm caption chegarasi {cap} belgi — undan oshma).
- HTML formatlash: faqat <b>, <i>, <code> teglari. Markdown ISHLATMA.
- Birinchi qator — e'tiborni ushlaydigan ilgak (hook), 1 gap.
- Oxirida qisqa harakatga chorlov (masalan: "Bugun sinab ko'ring").
{feedback}

JAVOBNI FAQAT shu JSON formatda qaytar:

{{
  "caption": "postning to'liq matni, HTML bilan",
  "image_prompt": "rasm uchun ingliz tilidagi tavsif — matnsiz, faqat vizual sahna",
  "image_title": "rasm ustiga yoziladigan qisqa sarlavha, 2-5 so'z, o'zbekcha"
}}"""


def _load_style():
    guide = "(stil qo'llanmasi hali to'ldirilmagan)"
    if os.path.exists(config.STYLE_GUIDE_PATH):
        guide = open(config.STYLE_GUIDE_PATH, encoding="utf-8").read().strip()

    files = sorted(glob.glob(os.path.join(config.EXAMPLES_DIR, "*.txt")))
    if not files:
        return guide, "(namuna postlar hali qo'shilmagan)"
    blocks = []
    for i, f in enumerate(files[:6], 1):
        blocks.append(f"--- NAMUNA {i} ---\n{open(f, encoding='utf-8').read().strip()}")
    return guide, "\n\n".join(blocks)


def write_post(gem, topic: dict, feedback: str = "") -> dict:
    guide, examples = _load_style()
    fb = f"\nQAYTA YOZISH SABABI (albatta hisobga ol): {feedback}" if feedback else ""

    prompt = PROMPT.format(
        title=topic.get("title", ""),
        tip=topic.get("tip", ""),
        why=topic.get("why", ""),
        how=" | ".join(topic.get("how", [])),
        example=topic.get("example", ""),
        level=topic.get("level", ""),
        lo=config.TARGET_LENGTH[0], hi=config.TARGET_LENGTH[1],
        cap=config.CAPTION_LIMIT, feedback=fb,
    )
    system = SYSTEM.format(style_guide=guide, examples=examples)
    post = gem.json(config.MODEL_WRITER, prompt, system=system, temperature=0.9)

    cap = post.get("caption", "").strip()
    if len(cap) > config.CAPTION_LIMIT:
        cap = cap[:config.CAPTION_LIMIT - 1].rsplit(" ", 1)[0] + "…"
    post["caption"] = cap
    return post
