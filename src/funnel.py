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
ANGLES = os.path.join(BASE, "angles.json")

SYSTEM = """Sen Siroj Saidmuratovning Telegram kanallari uchun kopirayter yozuvchisisan.
Auditoriya: O'zbekistonlik odamlar, sun'iy intellekt bilan daromad qilishni o'rganmoqchi.

AUDITORIYA — ENG MUHIM MA'LUMOT:
- Obunachilarning 60-80 foizi AYOLLAR.
- Ko'pchiligi uy bekalari, onalar, o'qituvchilar. Kod yozmaydi, texnik emas.
- Ular uchun ahamiyatli: uydan turib ishlash, bolalarni tashlab ketmaslik,
  moslashuvchan vaqt, o'z daromadiga ega bo'lish, o'zini rivojlantirish.
- Misol va obrazlarni shu hayotdan ol: bolalar uxlagandan keyingi vaqt, uy ishlari
  orasidagi bo'sh soat, maktabdagi ish, qo'shni va dugonalar davrasi, oilaviy byudjet.
- "Erkaklar klubi" ohangi BO'LMASIN: "biznes akula", "grind", "milliarder bo'l" — yo'q.
- Ayollarga hurmat bilan murojaat. Kamsituvchi yoki "sizga baribir qiyin" ohang YO'Q.
- Erkak o'quvchilar ham bor — ularni ham chetlab o'tma, lekin asosiy obraz ayol.

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

ASOSIY MAQSAD: bu kanallar oxir-oqibat KURSNI SOTADI. Shuning uchun ko'p
postning oxirida bitta fikr turishi kerak: <b>o'rganish uchun ayni vaqti,
ertaga emas — bugun</b>. Qiziqqan odam menejerga yozadi.
Lekin bu qo'pol sotuv emas: avval foyda, keyin chorlov.

QAT'IY TAQIQLAR:
- Narx haqida BIR OG'IZ ham gapirma. Narx yo'q, tarif yo'q, chegirma yo'q.
- "oqim" so'zini ISHLATMA. Uning o'rniga: "yangi guruh", "o'qish boshlanadi".
- O'zingdan raqam, statistika, foiz, o'quvchi natijasi yoki "shuncha odam yozdi"
  kabi da'vo O'YLAB TOPMA. Faqat senga berilgan faktlardagi ma'lumotni ishlat.
  Reaksiya sharti (100 ta olovcha) — bundan mustasno, u haqiqiy shart.
- Aniq sana va soat va'da qilma (masalan "ertaga 21:00 da") — bunga ruxsat yo'q.
- MUDDAT HOLATI da "sana aytma" deyilgan bo'lsa — hech qanday sana yozma.
  Efirni shart bilan bog'la: "olovcha yig'ilsa efir ochaman".
- Va'da berma: "albatta daromad qilasiz" kabi kafolatlar yo'q."""

FACT_PROMPT = """Quyidagi TEKSHIRILGAN haqiqiy voqea asosida informativ post yoz.
Bu post SOTUV EMAS — odam o'qib "menda ham bo'lishi mumkin ekan" deb o'ylasin.

SARLAVHA: {headline}

FAKTLAR (faqat shulardan foydalan, boshqa raqam qo'shma):
{facts}

XULOSA: {lesson}

OXIRGI CHIQQAN POSTLAR — bularni TAKRORLAMA:
{recent}

TUZILMA:
1. Ilgak — birinchi qator: kuzatuv, raqam yoki savol
2. Voqea qisqa qatorlarda, har biri alohida qatorda
3. Burilish: "Qiziq tomoni shunda:" / "Aslida esa," / "Demak,"
4. Xulosa — eng kuchli, qisqa qator

5. Oxirgi qator — o'quvchiga savol, izohga chorlov
6. Undan keyin BITTA qator: bu odam ham noldan boshlagan, siz ham
   o'rganishingiz mumkin — va buning vaqti ayni hozir, ertaga emas.

MUHIM: menejer havolasini O'ZING yozma — kod oxiriga o'zi qo'shadi.
Kurs nomi va narxni tilga olma. Uzunligi 700-900 belgi.

FAQAT shu JSON qaytar:
{{"caption": "postning to'liq matni HTML bilan",
  "audio": "shu postning OG'ZAKI varianti — emoji yo'q, havola yo'q, teg yo'q. Tirik gapiradigan odam kabi, 300-500 belgi"}}"""

VALUE_PROMPT = """Kurs qiymati haqida post yoz. Bu yumshoq qizdirish posti.

BUGUNGI BURCHAK (faqat shu haqda yoz, boshqa yo'nalishlarni sanab o'tma):
{angle}

KURS YO'NALISHLARI (fon uchun, hammasini yozma):
{modules}

OXIRGI CHIQQAN POSTLAR — bularni TAKRORLAMA. Boshqa ilgak, boshqa misol,
boshqa gap tuzilishi ishlat:
{recent}

TUZILMA:
1. Ilgak — shu burchakka tegishli aniq holat yoki savol
2. Nima o'rganiladi — 2-3 qisqa qator
3. Nega bu ish beradi
4. Muddat: {deadline}
5. Menejerga chorlov

MUHIM: narx aytma. Umumiy gap yozma — aniq misol ber.
Uzunligi 500-750 belgi.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga chiqadigan 1-4 so'z (emojisiz)",
  "image_small": "kichik yozuv, 3-6 so'z",
  "audio": "og'zaki variant — emoji va havolasiz, 250-450 belgi"}}"""

CLOSING_PROMPT = """Yakuniy chorlov posti yoz.

MUDDAT HOLATI: {deadline}

BUGUNGI BURCHAK (faqat shu haqda yoz):
{angle}

TUR: {kind}
Agar TUR = "trigger": oxirida shart qo'y — post ostida {reaction_goal} ta olovcha
yig'ilsa va'da qilingan narsa bo'ladi. Izohga chorla.
Agar TUR = "dajim": muddat va menejerga chorlov bilan tugat.

OXIRGI CHIQQAN POSTLAR — bularni TAKRORLAMA. Boshqa ilgak, boshqa obraz,
boshqa gap tuzilishi ishlat:
{recent}

TUZILMA: ilgak -> mazmun -> muddat -> chorlov -> oxirgi qator.
Uzunligi 450-700 belgi. Narx AYTMA. Aniq sana va soat va'da qilma.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga 1-4 so'z (emojisiz)",
  "image_small": "kichik yozuv, 3-6 so'z",
  "audio": "og'zaki variant — emoji va havolasiz, 250-450 belgi"}}"""

MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
          "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def load_campaign():
    with open(CAMPAIGN, encoding="utf-8") as f:
        return json.load(f)


def load_angles(slot: str) -> list:
    if not os.path.exists(ANGLES):
        return []
    with open(ANGLES, encoding="utf-8") as f:
        return json.load(f).get(slot) or []


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
    from src import history
    c = load_campaign()
    start_human = _human_date(c["start_date"])
    left = days_left(c["start_date"])
    recent = history.recent_text(8)
    if left > 0:
        deadline = (f"{start_human}dan yangi guruhda o'qish boshlanadi, "
                    f"{left} kun qoldi. Shu sanani ayt.")
    else:
        deadline = ("Joriy guruhda darslar ALLAQACHON boshlangan. "
                    "ANIQ SANA AYTMA. 'Yangi guruh to'planyapti', "
                    "'keyingi guruhga yozilib qo'yish mumkin' de.")
    meta = {"slot": slot, "days_left": left, "fact_id": None, "angle_id": ""}

    if slot == "fact":
        f = next_fact()
        if not f:
            print("[funnel] yangi fakt qolmadi — 'value' postiga o'tamiz")
            return build(gem, "value")
        meta["fact_id"] = f["id"]
        meta["angle_id"] = "fact:" + f["id"]
        meta["source_url"] = f.get("source_url", "")
        meta["image_big"] = f.get("image_big", "")
        meta["image_small"] = f.get("image_small", "")
        meta["image_note"] = f.get("image_note", "")
        meta["kicker"] = "HAQIQIY VOQEA"
        prompt = FACT_PROMPT.format(
            headline=f["headline"],
            facts="\n".join("• " + x for x in f["facts"]),
            lesson=f["lesson"], recent=recent)
        post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.9)
        post["caption"] = _append_manager(post.get("caption", ""), c)
        return post, meta

    if slot == "value":
        a = history.pick_angle("value", load_angles("value"))
        angle = a["angle"] if a else random.choice(c["modules"])["name"]
        meta["angle_id"] = a["id"] if a else ""
        mods = "\n".join(
            f"{i+1}. {m['name']}: " + ", ".join(m["points"])
            for i, m in enumerate(c["modules"]))
        print(f"[funnel] burchak: {meta['angle_id']} — {angle[:60]}")
        prompt = VALUE_PROMPT.format(angle=angle, modules=mods,
                                     deadline=deadline, recent=recent)
        post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.95)
        post["caption"] = _append_manager(post.get("caption", ""), c)
        meta["kicker"] = "AI PRO"
        meta["image_big"] = post.get("image_big") or "Yangi guruh"
        meta["image_small"] = (post.get("image_small")
                               or (f"{start_human} — o'qish boshlanadi" if left > 0
                                   else "Yangi guruh to'planyapti"))
        return post, meta

    # closing
    a = history.pick_angle("closing", load_angles("closing"))
    angle = a["angle"] if a else "Muddat yaqinlashdi"
    kind = (a or {}).get("kind", "dajim")
    meta["angle_id"] = (a or {}).get("id", "")
    print(f"[funnel] burchak: {meta['angle_id']} ({kind}) — {angle[:60]}")
    prompt = CLOSING_PROMPT.format(deadline=deadline, angle=angle, kind=kind,
                                   recent=recent,
                                   reaction_goal=config.REACTION_GOAL)
    post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.95)
    post["caption"] = _append_manager(post.get("caption", ""), c)
    meta["kicker"] = "JONLI EFIR" if kind == "trigger" else "YANGI GURUH"
    meta["kind"] = kind
    meta["image_big"] = post.get("image_big") or ("Yangi guruh" if left <= 0
                                                  else f"{left} kun qoldi")
    meta["image_small"] = (post.get("image_small")
                           or (f"{start_human} — o'qish boshlanadi" if left > 0
                               else "To'planyapti"))
    meta["watch_reactions"] = (kind == "trigger")
    return post, meta


# Menejer blokidan oldingi chorlov — takrorlanmasligi uchun navbat bilan
CTA_LINES = [
    "Buni o'rganish uchun ayni vaqti. Ertaga emas, bugun.",
    "Kutib o'tirishning ma'nosi yo'q — vaqt baribir o'tadi.",
    "Boshlash uchun eng yaxshi kun — bugun.",
    "Bir yildan keyin \"nega o'shanda boshlamadim\" demang.",
    "O'rganish uchun kech emas. Kechikish uchun esa hali erta.",
    "Hozir boshlaganlar bir oydan keyin natija ko'rsatadi.",
    "Qaror bugun qabul qilinadi, natija keyin ko'rinadi.",
]


def _cta_line(caption: str) -> str:
    return CTA_LINES[abs(hash(caption)) % len(CTA_LINES)]


def _append_manager(caption: str, c) -> str:
    """Chorlov + menejer havolasi. Har doim oxirida.

    Model ba'zan o'zidan "@menejer_link" kabi TO'QIMA havola yozadi.
    Shuning uchun matndagi HAR QANDAY @username o'chiriladi va faqat
    campaign.json dagi haqiqiy menejer havolasi qo'yiladi.
    """
    import re
    handle = c["manager"]
    caption = re.sub(r"[\U0001F440-\U0001F450]?\s*@[A-Za-z0-9_]{3,}", "", caption)
    caption = re.sub(r"@[A-Za-z0-9_]{3,}", "", caption)
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption).rstrip().rstrip("\U0001F449").rstrip()

    block = f"\n\n<b>{_cta_line(caption)}</b>\n\nQiziqsangiz, menejerga yozing:\n"
    block += "\n".join(handle for _ in range(c.get("manager_repeat", 3)))
    return caption + block
