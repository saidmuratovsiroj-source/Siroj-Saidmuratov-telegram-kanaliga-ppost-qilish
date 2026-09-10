"""Xalqaro AI yangiliklari — RSS lentalaridan.

Nega RSS: Gemini'ning Google Search grounding'i pullik, biz esa bepul ishlaymiz.
RSS lentalari ochiq, kalit talab qilmaydi va har soatda yangilanadi.

Bot bir nechta lentani o'qiydi, eng yangi va hali ishlatilmagan xabarni tanlaydi,
maqolaning to'liq matnini oladi va yozuvchiga beradi. Matnda yo'q narsa postga
tushmaydi — bu eng muhim qoida.
"""
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests

import config
from src import sources

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AiProBot/1.0)"}
NS = {"atom": "http://www.w3.org/2005/Atom"}


def _text(el):
    return re.sub(r"<[^>]+>", " ", (el.text or "")).strip() if el is not None else ""


def _when(raw: str):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse(xml: str, feed_name: str) -> list:
    out = []
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        print(f"[news] {feed_name} tahlil qilinmadi: {e}")
        return out

    # RSS 2.0
    for it in root.iter("item"):
        link = _text(it.find("link"))
        out.append({"title": _text(it.find("title")), "url": link,
                    "summary": _text(it.find("description"))[:600],
                    "when": _when(_text(it.find("pubDate"))), "feed": feed_name})
    # Atom
    for it in root.findall(".//atom:entry", NS):
        le = it.find("atom:link", NS)
        link = le.get("href") if le is not None else ""
        out.append({"title": _text(it.find("atom:title", NS)), "url": link,
                    "summary": _text(it.find("atom:summary", NS))[:600],
                    "when": _when(_text(it.find("atom:updated", NS))
                                  or _text(it.find("atom:published", NS))),
                    "feed": feed_name})
    return [x for x in out if x["url"] and len(x["title"]) > 12]


def fetch_all(max_age_days=None) -> list:
    """Barcha lentalardan xabarlar, eng yangisi birinchi."""
    max_age_days = max_age_days or config.NEWS_MAX_AGE_DAYS
    limit = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    items, seen = [], set()

    for name, url in config.NEWS_FEEDS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            r.raise_for_status()
        except Exception as e:
            print(f"[news] {name} ochilmadi: {type(e).__name__}")
            continue
        got = 0
        for it in _parse(r.text, name):
            if it["url"] in seen:
                continue
            if it["when"] and it["when"] < limit:
                continue
            seen.add(it["url"])
            items.append(it)
            got += 1
        print(f"[news] {name}: {got} ta yangi xabar")

    items.sort(key=lambda x: x["when"] or datetime.min.replace(tzinfo=timezone.utc),
               reverse=True)
    print(f"[news] jami {len(items)} ta xabar")
    return items


# Zerikarli korporativ/moliyaviy xabarlar — oddiy o'quvchiga qiziq emas
SKIP = ("earnings call", "stock", "shares", "ipo", "lawsuit", "court", "acquires",
        "funding round", "series a", "series b", "series c", "raises $", "layoff",
        "hiring", "valuation", "data center", "chip", "semiconductor", "kubernetes",
        "enterprise", "api ", "sdk", "open source model weights", "benchmark",
        "quarterly", "revenue run rate", "merger", "antitrust", "regulation",
        "policy", "senate", "congress")

# Qiziqarli mavzular — oddiy odam hayotiga tegishli
HOT = ("free", "launch", "launches", "new app", "video", "image", "photo",
       "music", "voice", "phone", "iphone", "android", "whatsapp", "instagram",
       "tiktok", "youtube", "students", "teachers", "parents", "kids", "school",
       "jobs", "job", "salary", "earn", "earned", "income", "hustle", "scam",
       "deepfake", "shocked", "viral", "first time", "banned", "quit",
       "replaced", "robot", "translate", "chatgpt", "gemini", "claude")


def _score(item) -> float:
    """Qanchalik qiziqarli. Yuqori ball = oldinroq chiqadi."""
    low = item["title"].lower()
    score = sum(2 for w in HOT if w in low)
    if re.search(r"\d", item["title"]):        # sarlavhada raqam bor
        score += 2
    if "?" in item["title"]:
        score += 1
    if item.get("when"):
        age_h = (datetime.now(timezone.utc) - item["when"]).total_seconds() / 3600
        score += max(0.0, 6.0 - age_h / 8)     # yangiroq bo'lsa ko'proq ball
    return score


def pick(archive, want=1) -> list:
    """Eng yangi va eng qiziqarli, hali ishlatilmagan xabarlar."""
    used = set(archive.urls())
    cands = []
    for it in fetch_all():
        if it["url"] in used:
            continue
        low = it["title"].lower()
        if any(w in low for w in SKIP):
            continue
        cands.append(it)

    cands.sort(key=_score, reverse=True)
    for it in cands[:5]:
        print(f"[news] nomzod ({_score(it):.1f}): {it['title'][:70]}")
    return cands[:want]


def with_text(item: dict) -> dict:
    """Maqolaning to'liq matnini qo'shadi. Olinmasa — qisqacha bilan qoladi."""
    try:
        item["text"] = sources.fetch_article(item["url"], max_chars=7000)
    except Exception as e:
        print(f"[news] matn olinmadi ({e}) — qisqacha bilan davom etamiz")
        item["text"] = ""
    if len(item["text"]) < 400:
        item["text"] = item.get("summary", "")
    return item
