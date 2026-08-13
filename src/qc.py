"""5-bosqich: sifat nazorati.

Fakt tekshirish rasmiy maqola matniga qarshi qilinadi — internetga chiqmaydi.
Ya'ni "post manbadan chetga chiqdimi?" degan savolga javob beradi.
Bu qidiruvdan qat'iyroq: manba aniq, taxmin yo'q.
"""
import re
import config

SYSTEM = """Sen qattiqqo'l muharrir va fakt-tekshiruvchisan. Yaxshi post uchun maqtov
kerak emas — faqat xatolarni top.

Sening oldingda ikkita narsa bor: RASMIY MANBA matni va yozilgan POST.
Postdagi har bir texnik da'vo manbada bormi — shuni tekshirasan.
Manbada yo'q da'vo = jiddiy xato."""

PROMPT = """RASMIY MANBA ({source_title}):
---
{source}
---

TEKSHIRILADIGAN POST:
---
{caption}
---

TEKSHIRUV RO'YXATI:
1. FAKT: postdagi har bir texnik da'vo manbada bormi? Manbada yo'q narsa aytilganmi?
   (Tugma nomlari, limitlar, qaysi tarifda ishlashi — hammasi tekshiriladi.)
2. TIL: faqat o'zbek lotin yozuvi. Kirill yoki ruscha so'z bormi? Grammatik xato?
3. STIL: har bir gap alohida qatordami? Uzun paragraf yo'qmi? Emoji yo'qmi?
4. AMALIYLIK: o'quvchi o'qib, aniq nima qilishini tushunadimi?
5. TUZILMA: birinchi qator ilgak bo'la oladimi? Oxirida chorlov bormi?

FAQAT shu JSON qaytar:
{{
  "verdict": "pass" yoki "fail",
  "score": 0 dan 10 gacha son,
  "problems": ["topilgan aniq muammolar"],
  "fix_instruction": "fail bo'lsa — yozuvchiga aniq ko'rsatma, aks holda bo'sh satr"
}}"""

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def check(gem, topic: dict, post: dict) -> dict:
    cap = post.get("caption", "")

    # --- arzon mexanik tekshiruvlar (modelga bormasdan) ---
    if not cap:
        return _fail(0, ["Post bo'sh"], "Postni qaytadan yoz")
    if CYRILLIC.search(cap):
        return _fail(2, ["Matnda kirill harflari bor"],
                     "Butun matnni faqat o'zbek lotin yozuvida qayta yoz")
    if EMOJI.search(cap):
        return _fail(4, ["Matnda emoji bor — stil qoidasi buni taqiqlaydi"],
                     "Barcha emojilarni olib tashla")
    if len(cap) > config.CAPTION_LIMIT:
        return _fail(3, [f"Uzunlik {len(cap)} > {config.CAPTION_LIMIT}"],
                     f"Matnni {config.CAPTION_LIMIT} belgidan qisqartir")
    longest = max((len(p) for p in cap.split("\n") if p.strip()), default=0)
    if longest > 220:
        return _fail(5, [f"Juda uzun paragraf ({longest} belgi)"],
                     "Uzun paragrafni bo'lib tashla — bitta fikr bitta qatorda")

    # --- manbaga qarshi fakt tekshiruvi ---
    prompt = PROMPT.format(source_title=topic.get("source_title", ""),
                           source=topic.get("source_text", "")[:9000], caption=cap)
    try:
        return gem.json(config.MODEL_QC, prompt, system=SYSTEM, temperature=0.2)
    except Exception as e:
        print(f"[qc] tekshirishda xato: {e} — tasdiq baribir sizda qoladi")
        return {"verdict": "pass", "score": 6,
                "problems": [f"QC ishlamadi: {e}"], "fix_instruction": ""}


def _fail(score, problems, fix):
    return {"verdict": "fail", "score": score, "problems": problems, "fix_instruction": fix}
