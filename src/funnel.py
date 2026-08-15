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

USLUB QOIDALARI (qat'iy):
- Ultra-qisqa. Telefon ekranida bir qarashda o'qilsin.
- Har 1-2 gapdan keyin BO'SH QATOR. Zich blok bo'lmasin.
- Emoji o'rinli ishlatiladi: 🔥 🚀 😱 ⏰ 🎁 👉 🤯 💡 😍
- Muhim so'zlar <b>bold</b> qilinadi. Faqat HTML: <b>, <i>. Markdown ISHLATMA.
- Samimiy, baquvvat, ekspert ohang. Rasmiyatchilik yo'q.
- Faqat o'zbek tili, lotin yozuvi. Kirill yoki ruscha so'z BO'LMASIN.

QAT'IY TAQIQLAR:
- Narx haqida BIR OG'IZ ham gapirma. Narx yo'q, tarif yo'q, chegirma yo'q.
- O'zingdan raqam, statistika, foiz, o'quvchi natijasi O'YLAB TOPMA.
  Faqat senga berilgan faktlardagi raqamlarni ishlat.
- Va'da berma: "albatta daromad qilasiz" kabi kafolatlar yo'q."""

FACT_PROMPT = """Quyidagi TEKSHIRILGAN haqiqiy voqea asosida informativ post yoz.
Bu post SOTUV EMAS — odam o'qib "menda ham bo'lishi mumkin ekan" deb o'ylasin.

SARLAVHA: {headline}

FAKTLAR (faqat shulardan foydalan, boshqa raqam qo'shma):
{facts}

XULOSA: {lesson}

TUZILMA:
1. Raqamli ilmoq — birinchi qator
2. Voqea qisqa qatorlarda
3. Eng qiziq detal (🤯 bilan)
4. Xulosa (bold)
5. Oxirida o'quvchiga savol — izohga chorlov

MUHIM: bu postda kurs, muddat va menejer haqida GAPIRMA. Faqat voqea va savol.
Uzunligi 700-900 belgi.

FAQAT shu JSON qaytar:
{{"caption": "postning to'liq matni HTML bilan"}}"""

VALUE_PROMPT = """Kurs ichidagi qiymat haqida post yoz. Bu yumshoq qizdirish posti.

KURS MODULLARI:
{modules}

BUGUN URG'U BERILADIGAN MODUL: {focus}

TUZILMA:
1. Ilmoq — savol yoki kuzatuv
2. Shu modulda nimalar o'rganilishi (qisqa punktlar)
3. Nega bu daromadga olib boradi
4. ⏰ Yangi guruh {start_human} da boshlanadi
5. Menejer havolasi

MUHIM: narx aytma. "Qiziqqanlar yozing" de.
Uzunligi 500-750 belgi.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga chiqadigan 1-3 so'z", "image_small": "kichik yozuv"}}"""

CLOSING_PROMPT = """Dajim (yakuniy chorlov) posti yoz.

KAMPANIYA: yangi oqim {start_human} da boshlanadi.
BUGUN {days_left} kun qoldi.
MENEJER: {manager}

TUR: {kind}

Agar TUR = "trigger": jonli efir taklifi. Odamlarning haqiqiy savollarini
sanab o't ("0 dan boshlasam uddalaymanmi?", "yoshim katta emasmi?",
"telefonda bo'ladimi?"), keyin shart qo'y: post {reaction_goal} ta 🔥 yig'sa
jonli efir ochiladi. Izohlarda savol qoldirishga chorla.

Agar TUR = "dajim": kelajakka ko'chirish (Tasavvur qiling...), afsus ramkasi
("keyin 'nega vaqtliroq boshlamadim' demang"), aniq muddat, menejerga chorlov.

TUZILMA: ilmoq -> mazmun -> muddat -> menejer havolasi -> oxirgi turtki.
Uzunligi 450-700 belgi. Narx AYTMA.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "rasmga 1-3 so'z", "image_small": "kichik yozuv"}}"""

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
        meta["image_small"] = post.get("image_small") or f"START {start_human.upper()}"
        return post, meta

    # closing
    kind = "trigger" if date.today().day % 2 == 0 else "dajim"
    prompt = CLOSING_PROMPT.format(start_human=start_human, days_left=max(left, 0),
                                   manager=c["manager"], kind=kind,
                                   reaction_goal=config.REACTION_GOAL)
    post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.9)
    post["caption"] = _append_manager(post.get("caption", ""), c)
    meta["kicker"] = "JONLI EFIR" if kind == "trigger" else "OXIRGI CHAQIRUV"
    meta["kind"] = kind
    meta["image_big"] = post.get("image_big") or (f"{max(left,0)} KUN")
    meta["image_small"] = post.get("image_small") or f"START {start_human.upper()}"
    meta["watch_reactions"] = (kind == "trigger")
    return post, meta


def _append_manager(caption: str, c) -> str:
    """Menejer havolasi har doim oxirida, takrorlangan holda."""
    handle = c["manager"]
    if handle in caption:
        # model o'zi qo'ygan bo'lsa, oxiridan kesib qayta yozamiz
        caption = caption.split(handle)[0].rstrip()
        caption = caption.rstrip("👉").rstrip()
    block = "\n\n" + "\n".join(f"👉 {handle}" for _ in range(c.get("manager_repeat", 3)))
    return caption.rstrip() + block
