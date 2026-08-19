"""Ertangi post navbati.

Nega kerak: 07:00 dagi post Sirojdan tasdiq so'ramasdan chiqishi kerak —
u paytda u tugma bosa olmaydi. Shuning uchun post bir kun oldin, kechqurun
tayyorlanadi va tasdiqlanadi. Ertalab bot faqat saqlanganini chiqaradi.

Fayl DATA_DIR ichida saqlanadi (Railway'da doimiy disk).
"""
import base64
import json
import os
from datetime import date, datetime

import config

PATH = os.path.join(config.DATA_DIR, "queued.json")


def save(caption: str, image: bytes, audio_text: str, meta: dict, for_day: str = ""):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    data = {
        "for_day": for_day or _tomorrow(),
        "saved_at": datetime.now(config.TZ).isoformat(timespec="seconds"),
        "caption": caption,
        "audio": audio_text or "",
        "meta": meta or {},
        "image_b64": base64.b64encode(image).decode() if image else "",
    }
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, PATH)
    print(f"[queue] post saqlandi, chiqish kuni: {data['for_day']}")


def load():
    if not os.path.exists(PATH):
        return None
    try:
        with open(PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print(f"[queue] o'qib bo'lmadi: {e}")
        return None
    d["image"] = base64.b64decode(d.get("image_b64") or "") or None
    return d


def clear():
    if os.path.exists(PATH):
        os.remove(PATH)
        print("[queue] navbat tozalandi")


def _tomorrow():
    from datetime import timedelta
    return (date.today() + timedelta(days=1)).isoformat()
