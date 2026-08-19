"""Vebinar kanallari uchun dajim tizimi.

Kuniga 3 ta post, uchalasi ham sotuv EMAS:
  10:00 "fact"    — tekshirilgan haqiqiy voqea (funnel/facts.json dan)
  16:00 "value"   — kurs ichidagi yo'nalish, foyda
  20:00 "closing" — dajim yoki jonli efir triggeri

Eng muhim qoida: postdagi HAR BIR RAQAM VA SANA brifda yoki fakt bazasida
bo'lishi shart. Bot statistika o'ylab topmaydi — bir marta yolg'on chiqsa,
10 000 obunachi oldida ishonch yo'qoladi.
"""
import json
import os
import random
from datetime import date, datetime

import config

BASE = os.path.join(config.BASE_DIR, "funnel")
CAMPAIGN = os.path.join(BASE, "campaign.json")
FACTS = os.path.join(BASE, "facts.json")

SYSTEM = """Sen Siroj Saidmuratovning Telegram kanallari uchun kopirayter yozuvchisisan.
Auditoriya: O'zbekistonlik odamlar, sun'iy intellekt bilan daromad qilishni o'rganmoqchi.

ENG MUHIM: post TIRIK ODAM yozganday o'qilsin — Sirojning o'zi yozganday.
Quyida uning HAQIQIY posti. Uslubni shundan ol:

---
Tepadagi videoni albatta ko'ring! 👆

O'quvchilarimiz Sun'iy Intellekt yordamida yaratgan realistik va ajoyib
videolarni ko'rib turibsiz! 🔥

Juda ko'pchilik darslarga kira olmaganini va video yaratishni boshidan
o'rganishni xohlayotganini yozishmoqda.

Shuning uchun ertaga soat 21:00 da jonli efir o'tib bermoqchiman! Efirda
videolarni noldan yaratishning aniq qadam-baqadam ketma-ketligini ko'rsatib
beraman. 🎥⚡️

🚨 LEKIN BIZDA BITTA SHART BOR: Efir bo'lishi uchun ushbu post ostida kamida
100 TA OLOVCHA (🔥) yig'ilishi kerak!

Olovchani bosing va jonli efirga kirish uchun hoziroq yozing:
---

USLUB QOIDALARI (qat'iy):
- BIRINCHI SHAXSDA yoz: "ko'rsatib beraman", "o'tkazmoqchiman", "aytib beraman".
- Qisqa xatboshilar. Har xatboshidan keyin BO'SH QATOR.
- Emoji qator oxirida ishlatiladi: 🔥 👆 🎥 ⚡️ 🚨 😍 ✅ 📌 👉
- Eng muhim shart yoki raqam KATTA HARFLAR bilan: "BITTA SHART BOR".
- <b> bilan faqat eng muhim joyni urg'ula. Markdown ISHLATMA.
- Jonli, baquvvat, samimiy ohang. Rasmiyatchilik yo'q.
- Faqat o'zbek tili, lotin yozuvi. Kirill yoki ruscha so'z BO'LMASIN.

QAT'IY TAQIQLAR:
- Narx haqida BIR OG'IZ ham gapirma. Narx yo'q, tarif yo'q, chegirma yo'q.
- "oqim" so'zini ISHLATMA. Uning o'rniga: "yangi guruh", "o'qish boshlanadi".
- O'zingdan raqam, statistika, foiz, o'quvchi natijasi yoki "shuncha odam yozdi"
  kabi da'vo O'YLAB TOPMA. Faqat senga berilgan faktlardagi ma'lumotni ishlat.
  Reaksiya sharti (100 ta olovcha) — bundan mustasno, u haqiqiy shart.
- Aniq sana va soat va'da qilma (masalan "ertaga 21:00 da") — bunga ruxsat yo'q.
  Efirni shart bilan bog'la: "olovcha yig'ilsa efir ochaman".
- Va'da berma: "albatta daromad qilasiz" kabi kafolatlar yo'q."""

FACT_PROMPT = """Quyidagi TEKSHIRILGAN haqiqiy voqea asosida informativ post yoz.
Bu post SOTUV EMAS — odam o'qib "menda ham bo'lishi mumkin ekan" deb o'ylasin.

SARLAVHA: {headline}

FAKTLAR (faqat shulardan foydalan, boshqa raqam qo'shma):
{facts}

XULOSA: {lesson}

TUZILMA:
1. Ilgak — birinchi qator: kuzatuv, raqam yoki savol
2. Voqea qisqa qatorlarda, har biri alohida qatorda
3. Burilish: "Qiziq tomoni shunda:" / "Aslida esa," / "Demak,"
4. Xulosa — eng kuchli, qisqa qator
5. Oxirida o'quvchiga savol — izohga chorlov

MUHIM: bu postda kurs, muddat va menejer haqida GAPIRMA. Faqat voqea va savol.
Uzunligi 700-900 belgi.

FAQAT shu JSON qaytar:
{{"caption": "postning to'liq matni HTML bilan",
  "audio": "shu postning OG'ZAKI varianti — emoji yo'q, havola yo'q, teg yo'q. Tirik gapiradigan odam kabi, 300-500 belgi"}}"""

VALUE_PROMPT = """Kurs ichidagi qiymat haqida post yoz. Bu yumshoq qizdirish posti.

KURS MODULLARI:
{modules}

BUGUN URG'U BERILADIGAN MODUL: {focus}

TUZILMA:
1. Ilgak — savol yoki kuzatuv
2. Shu yo'nalishda nimalar o'rganilishi — har biri alohida qisqa qatorda
3. Nega bu ish beradi
4. {start_human}dan yangi guruhda o'qish boshlanadi
5. Menejerga chorlov

MUHIM: narx aytma. "Qiziqqanlar yozing" de.
Uzunligi 500-750 belgi.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga chiqadigan 1-3 so'z (emojisiz)", "image_small": "kichik yozuv",
  "audio": "og'zaki variant — emoji va havolasiz, 250-450 belgi"}}"""

CLOSING_PROMPT = """Dajim (yakuniy chorlov) posti yoz.

KAMPANIYA: {start_human}dan yangi guruhda o'qish boshlanadi.
BUGUN {days_left} kun qoldi.
MENEJER: {manager}

TUR: {kind}

Agar TUR = "trigger": jonli efir taklifi. Odamlarning haqiqiy savollarini
sanab o't ("0 dan boshlasam uddalaymanmi?", "yoshim katta emasmi?",
"telefonda bo'ladimi?"), keyin shart qo'y: post {reaction_goal} ta olov reaksiyasi yig'sa
jonli efir ochiladi. Izohlarda savol qoldirishga chorla.

Agar TUR = "dajim": kelajakka ko'chirish (Tasavvur qiling...), afsus ramkasi
("keyin 'nega vaqtliroq boshlamadim' demang"), aniq muddat, menejerga chorlov.

TUZILMA: ilgak -> mazmun -> muddat -> menejerga chorlov -> oxirgi qator.
Uzunligi 450-700 belgi. Narx AYTMA.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga 1-3 so'z (emojisiz)", "image_small": "kichik yozuv",
  "audio": "og'zaki variant — emoji va havolasiz, 250-450 belgi"}}"""

MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
          "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def load_campaign():
    with open(CAMPAIGN, encoding="utf-8") as f:
        return json.load(f)


def _facts():
    if not os.path.exists(FACTS):
        return []
    with open(FACTS, encoding="utf-8") as f:
        return json.load(f)


def _save_facts(items):
    tmp = FACTS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FACTS)


def next_fact():
    """Ishlatilmagan birinchi fakt. Hammasi ishlatilgan bo'lsa — None."""
    for it in _facts():
        if not it.get("used"):
            return it
    return None


def mark_used(fact_id):
    items = _facts()
    for it in items:
        if it.get("id") == fact_id:
            it["used"] = True
    _save_facts(items)


def _human_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return f"{d.day}-{MONTHS[d.month - 1]}"


def days_left(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return (d - date.today()).days


def build(gem, slot: str):
    """slot: fact | value | closing -> (post, meta)"""
    c = load_campaign()
    start_human = _human_date(c["start_date"])
    left = days_left(c["start_date"])
    meta = {"slot": slot, "days_left": left, "fact_id": None}

    if slot == "fact":
        f = next_fact()
        if not f:
            print("[funnel] yangi fakt qolmadi — 'value' postiga o'tamiz")
            return build(gem, "value")
        meta["fact_id"] = f["id"]
        meta["source_url"] = f.get("source_url", "")
        meta["image_big"] = f.get("image_big", "")
        meta["image_small"] = f.get("image_small", "")
        meta["image_note"] = f.get("image_note", "")
        meta["kicker"] = "HAQIQIY VOQEA"
        prompt = FACT_PROMPT.format(
            headline=f["headline"],
            facts="\n".join("• " + x for x in f["facts"]),
            lesson=f["lesson"])
        post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.85)
        return post, meta

    if slot == "value":
        focus = random.choice(c["modules"])
        mods = "\n".join(
            f"{i+1}. {m['name']}: " + ", ".join(m["points"])
            for i, m in enumerate(c["modules"]))
        prompt = VALUE_PROMPT.format(modules=mods, focus=focus["name"],
                                     start_human=start_human)
        post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.9)
        post["caption"] = _append_manager(post.get("caption", ""), c)
        meta["kicker"] = focus["name"].upper()
        meta["image_big"] = post.get("image_big") or focus["name"]
        meta["image_small"] = post.get("image_small") or f"{start_human} — o'qish boshlanadi"
        return post, meta

    # closing
    kind = "trigger" if date.today().day % 2 == 0 else "dajim"
    prompt = CLOSING_PROMPT.format(start_human=start_human, days_left=max(left, 0),
                                   manager=c["manager"], kind=kind,
                                   reaction_goal=config.REACTION_GOAL)
    post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.9)
    post["caption"] = _append_manager(post.get("caption", ""), c)
    meta["kicker"] = "JONLI EFIR" if kind == "trigger" else "YANGI GURUH"
    meta["kind"] = kind
    meta["image_big"] = post.get("image_big") or (f"{max(left,0)} KUN")
    meta["image_small"] = post.get("image_small") or f"{start_human} — o'qish boshlanadi"
    meta["watch_reactions"] = (kind == "trigger")
    return post, meta


def _append_manager(caption: str, c) -> str:
    """Menejer havolasi har doim oxirida, takrorlangan holda.

    Model ba'zan o'zidan "@menejer_link", "@manager" kabi TO'QIMA havola yozadi.
    Shuning uchun matndagi HAR QANDAY @username o'chiriladi va faqat
    campaign.json dagi haqiqiy menejer havolasi qo'yiladi.
    """
    import re
    handle = c["manager"]
    # 1) matn ichidagi barcha @username larni olib tashlaymiz
    caption = re.sub(r"[\U0001F440-\U0001F450]?\s*@[A-Za-z0-9_]{3,}", "", caption)
    caption = re.sub(r"@[A-Za-z0-9_]{3,}", "", caption)
    # 2) ular ketgandan keyin qolgan bo'sh qatorlarni tozalaymiz
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption).rstrip().rstrip("👉").rstrip()
    # Emoji yo'q — Sirojning uslubida "👉" kabi ko'rsatkichlar ishlatilmaydi
    block = "\n\n" + "\n".join(handle for _ in range(c.get("manager_repeat", 3)))
    return caption + block
