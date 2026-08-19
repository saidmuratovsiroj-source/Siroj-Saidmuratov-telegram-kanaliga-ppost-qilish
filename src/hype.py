"""Asosiy kanal (@Siroj_aiPro_Academy) uchun post generatori.

Siroj tanlagan yo'nalish (2026-08-19):
  - Kanal faqat Claude haqida EMAS. Asosiysi — hayp mavzular:
    xalqaro AI yangiliklari, kim AI bilan qancha ishlayapti, global voqealar.
  - Har postning tagida bitta fikr turadi: "AI'ni o'rganish vaqti ayni hozir,
    hali kech emas, bugun noldan boshlash mumkin".
  - Har 3-postda yumshoq chorlov: bizning jamoamizga qo'shilish mumkin.
  - 8 postdan bittasi — kurslar haqida (video, audio/musiqa, vayb-kodlash,
    Amerika YouTube). Bittasi — asbob bo'yicha amaliy maslahat.

Navbat `funnel/main_channel.json` dagi `rotation` ro'yxati bilan boshqariladi.
"""
import json
import os

import config

BRIEF = os.path.join(config.BASE_DIR, "funnel", "main_channel.json")

SYSTEM = """Sen Siroj Saidmuratovning Telegram kanali uchun kopirayter yozuvchisisan.
Auditoriya: O'zbekistonlik odamlar — o'qituvchilar, uy bekalari, talabalar.
Kod yozmaydi. Sun'iy intellekt bilan nima qilish mumkinligini bilmoqchi.

ENG MUHIM: post TIRIK ODAM yozganday o'qilsin. Siroj o'zi yozganday.

USLUB QOIDALARI (qat'iy):
- Birinchi qator — ILGAK. Raqam, hayratlanarli fakt yoki savol.
- Bitta fikr — bitta qator. Har qatordan keyin BO'SH QATOR.
- Qisqa gaplar. Qo'shma gap yo'q.
- Emoji o'rinli va kam: 🔥 🤯 👀 💡 ⚡️ 📌 👇 — har qatorga emas, qator oxirida.
- <b> bilan faqat eng muhim joyni urg'ula. Markdown ISHLATMA.
- Birinchi shaxsda: "o'qidim", "ko'rdim", "o'ylab qoldim".
- Faqat o'zbek tili, lotin yozuvi. Kirill yoki ruscha so'z BO'LMASIN.
- Chet el nomlari va raqamlarni o'zgartirma.

QAT'IY TAQIQLAR:
- Narx haqida BIR OG'IZ ham gapirma.
- "oqim" so'zini ISHLATMA — "yangi guruh", "o'qish boshlanadi" de.
- Senga berilgan matnda YO'Q raqam, sana, ism yoki natijani O'YLAB TOPMA.
  Bir marta yolg'on chiqsa, ishonch yo'qoladi.
- "Sun'iy intellekt hayotingizni o'zgartiradi" kabi quruq umumiy gap — yo'q.
- Kafolat berma."""

NEWS_PROMPT = """Quyidagi xalqaro yangilik asosida post yoz.

SARLAVHA: {title}
MANBA: {feed}

MAQOLA MATNI (faqat shu matndagi faktlarni ishlat):
---
{text}
---

TUZILMA:
1. Ilgak — eng hayratlanarli fakt yoki raqam, birinchi qator
2. Voqea nima — 3-6 qisqa qator
3. "Bu bizga nima beradi?" — O'zbekistondagi oddiy odam uchun ma'nosi
4. Yakun: {core}
   Buni o'z so'zing bilan, tabiiy qilib ayt. So'zma-so'z ko'chirma.
5. Oxirgi qator — o'quvchiga savol, izohga chorlov

MUHIM: matnda bo'lmagan raqam yoki ismni yozma. Tushunarsiz texnik atamalarni
soddalashtir. Uzunligi 600-900 belgi.

FAQAT shu JSON qaytar:
{{"caption": "postning to'liq matni HTML bilan",
  "image_big": "rasm uchun 1-4 so'z — eng kuchli fakt yoki raqam",
  "image_small": "rasm uchun kichik yozuv, 3-6 so'z",
  "audio": "og'zaki variant — emoji, havola va teg yo'q, 300-500 belgi"}}"""

TOOL_PROMPT = """Sun'iy intellekt asboblari bo'yicha BITTA amaliy maslahat posti yoz.

MANBA MAQOLA: {title}
MATN:
---
{text}
---

TUZILMA:
1. Ilgak — odam duch keladigan real muammo
2. Yechim: 2-4 aniq qadam, har biri alohida qatorda
3. Tayyor misol yoki prompt (agar matnda bo'lsa)
4. Yakun: {core}
5. Savol — izohga chorlov

MUHIM: faqat matndagi ma'lumot. Dasturchi atamalarini ishlatma.
Uzunligi 500-800 belgi.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "1-4 so'z", "image_small": "3-6 so'z",
  "audio": "og'zaki variant, 250-450 belgi"}}"""

OFFER_PROMPT = """Kurs haqida yumshoq taklif posti yoz. Bu qattiq sotuv EMAS.

KURS: {name}
KIMGA: {who}
NIMALAR BOR: {points}

TUZILMA:
1. Ilgak — shu yo'nalishga qiziqqan odamning haqiqiy savoli yoki orzusi
2. Shu kursda nimalar bor — qisqa punktlar, har biri alohida qatorda
3. Nega ayni hozir: {core}
4. "Qiziqqanlar menejerga yozing" — narx AYTMA
5. Oxirgi qator — turtki

Uzunligi 450-700 belgi.

FAQAT shu JSON qaytar:
{{"caption": "matn", "image_big": "1-4 so'z", "image_small": "3-6 so'z",
  "audio": "og'zaki variant, 250-450 belgi"}}"""

INVITE = ("\n\nSun'iy intellektni o'rganayotganlar uchun jamoamiz bor. "
          "Qo'shilmoqchi bo'lsangiz, yozing:\n{manager}")


def load_brief():
    with open(BRIEF, encoding="utf-8") as f:
        return json.load(f)


def kind_for(n: int, brief) -> str:
    rot = brief.get("rotation") or ["news"]
    return rot[n % len(rot)]


def build(gem, archive):
    """(post, meta) qaytaradi. meta: kind, source_url, image_* , kicker."""
    brief = load_brief()
    n = len(archive.items)
    kind = kind_for(n, brief)
    core = brief["core_message"]
    meta = {"kind": kind, "source_url": "", "source_title": ""}

    if kind == "news":
        from src import news
        picked = news.pick(archive, want=1)
        if not picked:
            print("[hype] yangi xabar topilmadi — kurs taklifiga o'tamiz")
            kind = "offer"
        else:
            item = news.with_text(picked[0])
            if len(item["text"]) < 200:
                print("[hype] matn juda qisqa — kurs taklifiga o'tamiz")
                kind = "offer"
            else:
                meta.update(source_url=item["url"], source_title=item["title"],
                            kicker="AI YANGILIKLARI", kind="news")
                post = gem.json(config.MODEL_WRITER,
                                NEWS_PROMPT.format(title=item["title"], feed=item["feed"],
                                                   text=item["text"], core=core),
                                system=SYSTEM, temperature=0.85)
                return _finish(post, meta, brief, n)

    if kind == "tool":
        from src import research, sources
        arts = sources.list_articles(config.COLLECTIONS)
        used = set(archive.urls())
        fresh = [a for a in arts if a["url"] not in used
                 and not any(w in a["title"].lower() for w in research.SKIP_WORDS)]
        text, chosen = "", None
        for cand in fresh[:12]:
            try:
                t = sources.fetch_article(cand["url"])
            except Exception:
                continue
            if len(t) >= 400:
                chosen, text = cand, t
                break
        if chosen:
            meta.update(source_url=chosen["url"], source_title=chosen["title"],
                        kicker="AMALIY MASLAHAT", kind="tool")
            post = gem.json(config.MODEL_WRITER,
                            TOOL_PROMPT.format(title=chosen["title"], text=text, core=core),
                            system=SYSTEM, temperature=0.8)
            return _finish(post, meta, brief, n)
        print("[hype] maslahat uchun maqola topilmadi — kurs taklifiga o'tamiz")
        kind = "offer"

    # offer
    courses = brief["courses"]
    c = courses[(n // len(brief.get("rotation", [1]))) % len(courses)]
    meta.update(kicker=c["name"].upper(), kind="offer")
    post = gem.json(config.MODEL_WRITER,
                    OFFER_PROMPT.format(name=c["name"], who=c["for"],
                                        points=", ".join(c["points"]), core=core),
                    system=SYSTEM, temperature=0.85)
    return _finish(post, meta, brief, n)


def _finish(post, meta, brief, n):
    cap = (post.get("caption") or "").strip()
    every = int(brief.get("invite_every", 3))
    # har 3-postda jamoaga yumshoq chorlov (kurs taklifida takrorlanmasin)
    if meta["kind"] != "offer" and every and (n + 1) % every == 0:
        cap += INVITE.format(manager=brief["manager"])
    post["caption"] = cap
    meta["image_big"] = post.get("image_big") or ""
    meta["image_small"] = post.get("image_small") or ""
    return post, meta
