"""Chiqarilgan vebinar postlari tarixi — TAKRORLANISHNING oldini oladi.

Muammo shu edi: bot har safar bir xil mazmunni boshqa so'zlar bilan yozardi.
Sabab — u avval nima yozganini bilmasdi.

Endi har chiqqan post shu yerga yoziladi: qaysi slot, qaysi burchak, qaysi
sarlavha. Yangi post yozilishidan oldin bu ro'yxat modelga ko'rsatiladi
("bularni TAKRORLAMA") va eng uzoq ishlatilmagan burchak tanlanadi.
"""
import json
import os
import re
from datetime import datetime

import config

PATH = os.path.join(config.DATA_DIR, "funnel_history.json")
KEEP = 60


def load():
    if not os.path.exists(PATH):
        return []
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[history] o'qib bo'lmadi ({e}) — bo'sh tarixdan boshlaymiz")
        return []


def _save(items):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items[-KEEP:], f, ensure_ascii=False, indent=2)
    os.replace(tmp, PATH)


def add(slot: str, angle_id: str, caption: str):
    items = load()
    items.append({
        "date": datetime.now(config.TZ).strftime("%Y-%m-%d %H:%M"),
        "slot": slot,
        "angle_id": angle_id or "",
        "opening": _plain(caption)[:120],
        "words": sorted(_keywords(caption))[:40],
    })
    _save(items)
    print(f"[history] yozildi: {slot} / {angle_id}")


def used_angles(slot: str) -> list:
    """Shu slot uchun ishlatilgan burchaklar — eng eskisi birinchi."""
    return [it.get("angle_id") for it in load()
            if it.get("slot") == slot and it.get("angle_id")]


def pick_angle(slot: str, angles: list):
    """Eng uzoq vaqt ishlatilmagan burchakni qaytaradi."""
    if not angles:
        return None
    used = used_angles(slot)
    fresh = [a for a in angles if a["id"] not in used]
    if fresh:
        return fresh[0]
    # hammasi ishlatilgan — eng eskisidan qayta boshlaymiz
    order = {aid: i for i, aid in enumerate(used)}
    return min(angles, key=lambda a: order.get(a["id"], 0))


def recent_text(n: int = 8) -> str:
    """Modelga ko'rsatiladigan ro'yxat: oxirgi postlarning boshlanishi."""
    items = load()[-n:]
    if not items:
        return "(hali post chiqmagan)"
    return "\n".join(f"- [{it['slot']}] {it['opening']}" for it in items)


# ------------------------------------------------------------ o'xshashlik
STOP = {"va", "bu", "shu", "uchun", "bilan", "ham", "yoki", "lekin", "emas",
        "kerak", "mumkin", "bor", "yo'q", "men", "siz", "biz", "u", "o'z",
        "har", "eng", "juda", "faqat", "keyin", "hozir", "ya'ni", "deb"}


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _keywords(text: str) -> set:
    words = re.findall(r"[a-zA-Z'ʻ‘’]{4,}", _plain(text).lower())
    return {w for w in words if w not in STOP}


def similarity(caption: str, n: int = 25) -> float:
    """Yangi post oxirgi postlarga qanchalik o'xshash (0..1)."""
    new = _keywords(caption)
    if not new:
        return 0.0
    best = 0.0
    for it in load()[-n:]:
        old = set(it.get("words") or [])
        if not old:
            continue
        overlap = len(new & old) / max(len(old), 1)
        best = max(best, overlap)
    return best


def opening_repeats(caption: str, n: int = 25) -> str:
    """Birinchi qator avval ishlatilganmi. Ishlatilgan bo'lsa sababni qaytaradi."""
    first = _plain(caption).split(".")[0][:60].lower().strip()
    if len(first) < 12:
        return ""
    new = set(re.findall(r"[a-z'ʻ‘’]{4,}", first))
    for it in load()[-n:]:
        old_open = (it.get("opening") or "").split(".")[0][:60].lower()
        old = set(re.findall(r"[a-z'ʻ‘’]{4,}", old_open))
        if not old or not new:
            continue
        if len(new & old) / max(1, min(len(new), len(old))) >= 0.6:
            return f"Ilgak avvalgi postga o'xshash: \"{old_open[:40]}…\""
    return ""
