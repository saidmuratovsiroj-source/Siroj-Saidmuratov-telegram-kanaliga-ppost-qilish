"""1-bosqich: rasmiy manbalardan bugungi mavzuni tanlash va maslahatni ajratib olish."""
import random
import config
from src import sources

PICK_SYSTEM = """Sen O'zbekistonlik auditoriya uchun Telegram kanaliga kontent tanlaydigan
muharrirsan. Auditoriya: ko'pchiligi o'qituvchilar va uy bekalari, kod yozmaydi,
Claude'ni ish va kundalik hayotda ishlatishni o'rganmoqda.

Vazifang: berilgan rasmiy maqolalar ro'yxatidan BITTA eng foydali mavzuni tanlash."""

PICK_PROMPT = """DARAJA: {level}
{level_desc}

MAQOLALAR RO'YXATI (raqam bilan tanlaysan):
{listing}

QOIDALAR:
- Dasturchilar uchun texnik mavzularni tanlama (API, SDK, Bedrock, SSO, billing, admin).
- Kundalik foydalanuvchiga darhol foyda beradigan mavzuni tanla.
- Auditoriya darajasiga mos bo'lsin.

FAQAT shu JSON qaytar:
{{"index": tanlangan raqam, "reason": "nega shu — bir gap"}}"""

EXTRACT_SYSTEM = """Sen fakt-ajratuvchisan. Senga Anthropic'ning RASMIY yordam maqolasi
beriladi. Sen faqat SHU MATNDA yozilgan narsani ishlatasan.

QAT'IY: matnda yo'q narsani o'ylab topma. Eslab qolgan bilimingga tayanma —
Claude tez o'zgaradi, sening xotirang eskirgan bo'lishi mumkin. Faqat matn."""

EXTRACT_PROMPT = """Quyidagi rasmiy maqoladan Telegram posti uchun BITTA amaliy maslahat ajrat.

MAQOLA SARLAVHASI: {title}
MANBA: {url}

MAQOLA MATNI:
---
{text}
---

FAQAT shu JSON qaytar:
{{
  "title": "maslahat sarlavhasi, 3-6 so'z, o'zbekcha",
  "tip": "maslahatning mohiyati, 2-3 gap, o'zbekcha",
  "why": "o'quvchiga nima beradi — 1 gap",
  "how": ["aniq qadam 1", "aniq qadam 2", "aniq qadam 3"],
  "example": "aniq misol yoki tayyor prompt (bo'lmasa bo'sh satr)",
  "facts": ["maqoladan olingan aniq faktlar — keyin tekshiriladi"]
}}"""

LEVEL_DESC = {
    "boshlangich": "Claude'ni endi ochgan odam uchun: interfeys, birinchi qadamlar, "
                   "fayl yuklash, suhbatni tashkil qilish, oddiy sozlamalar.",
    "orta": "Kundalik ishlatadigan odam uchun: Projects, Skills, connectors, "
            "uzun hujjatlar, ish oqimini avtomatlashtirish.",
}

SKIP_WORDS = ("api", "bedrock", "sso", "scim", "vertex", "billing", "invoice",
              "admin", "enterprise", "compliance", "sdk", "webhook")


def find_topic(gem, archive, level: str) -> dict:
    articles = sources.list_articles(config.COLLECTIONS)
    if not articles:
        raise RuntimeError("Manbalardan bitta ham maqola olinmadi")

    used = set(archive.urls())
    fresh = [a for a in articles
             if a["url"] not in used
             and not any(w in a["title"].lower() for w in SKIP_WORDS)]
    if not fresh:
        print("[research] hamma maqola ishlatilgan — arxivning eng eskisidan qayta boshlaymiz")
        fresh = articles

    random.shuffle(fresh)
    shortlist = fresh[:config.SHORTLIST_SIZE]
    listing = "\n".join(f"{i}. [{a['collection']}] {a['title']}"
                        for i, a in enumerate(shortlist))

    pick = gem.json(config.MODEL_RESEARCH,
                    PICK_PROMPT.format(level=level, level_desc=LEVEL_DESC.get(level, ""),
                                       listing=listing),
                    system=PICK_SYSTEM, temperature=1.0)
    idx = int(pick.get("index", 0))
    if not (0 <= idx < len(shortlist)):
        idx = 0
    print(f"[research] tanlandi: {shortlist[idx]['title']} — {pick.get('reason','')}")

    # Ba'zi maqolalarning matni bo'sh chiqadi (sahifa JS bilan yuklanadi).
    # Shunday bo'lsa to'xtamaymiz — navbatdagi maqolaga o'tamiz.
    order = [shortlist[idx]] + [a for i, a in enumerate(shortlist) if i != idx]
    chosen, text = None, ""
    for cand in order[:12]:
        try:
            t = sources.fetch_article(cand["url"])
        except Exception as e:
            print(f"[research] o'qib bo'lmadi ({cand['title'][:40]}): {e}")
            continue
        if len(t) >= 400:
            chosen, text = cand, t
            break
        print(f"[research] matni qisqa ({len(t)} belgi), keyingisiga o'tamiz: {cand['title'][:45]}")
    if not chosen:
        raise RuntimeError("Hech qaysi maqoladan yetarli matn olinmadi")
    if chosen is not shortlist[idx]:
        print(f"[research] yakuniy tanlov: {chosen['title']}")

    topic = gem.json(config.MODEL_RESEARCH,
                     EXTRACT_PROMPT.format(title=chosen["title"], url=chosen["url"], text=text),
                     system=EXTRACT_SYSTEM, temperature=0.6)
    topic["level"] = level
    topic["source_url"] = chosen["url"]
    topic["source_title"] = chosen["title"]
    topic["source_text"] = text
    return topic
