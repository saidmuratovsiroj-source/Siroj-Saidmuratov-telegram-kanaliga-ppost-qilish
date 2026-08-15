"""🔥 reaksiyalarni kuzatish.

Trigger post chiqqanda ("100 ta olov yig'ilsa efir ochaman") bot reaksiyalarni
kuzatib boradi va shart bajarilganda Sirojga xabar beradi. Avtomatik hech narsa
qilmaydi — qarorni Siroj qabul qiladi.

Telegram reaksiya sonini `message_reaction_count` update orqali beradi.
Buning uchun bot kanalda admin bo'lishi va allowed_updates ichida
"message_reaction_count" bo'lishi shart.
"""
import json
import os
import time

import config

STATE = os.path.join(config.DATA_DIR, "watch.json")


def _load():
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save(items):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)


def watch(posted, goal: int, emoji: str = "🔥"):
    """posted: [{chat_id, message_id, title}] — kuzatuvga qo'shadi."""
    items = _load()
    for p in posted:
        items.append({"chat_id": p["chat_id"], "message_id": p["message_id"],
                      "title": p.get("title", ""), "goal": goal, "emoji": emoji,
                      "notified": False, "added": int(time.time())})
    _save(items)
    print(f"[reactions] {len(posted)} ta post kuzatuvga qo'shildi (maqsad {goal} {emoji})")


def check(tg):
    """Kelgan reaksiya update'larini o'qib, shart bajarilganini tekshiradi.

    Qaytaradi: xabar berilishi kerak bo'lgan postlar ro'yxati.
    """
    items = _load()
    if not items:
        return []

    counts = {}
    try:
        updates = tg._call("getUpdates", json={
            "offset": tg._offset, "timeout": 0,
            "allowed_updates": ["message_reaction_count", "callback_query", "channel_post"],
        })
    except Exception as e:
        print(f"[reactions] getUpdates xato: {e}")
        return []

    for u in updates:
        tg._offset = u["update_id"] + 1
        rc = u.get("message_reaction_count")
        if not rc:
            continue
        key = (rc["chat"]["id"], rc["message_id"])
        for r in rc.get("reactions", []):
            em = (r.get("type") or {}).get("emoji")
            if em:
                counts[(key, em)] = r.get("total_count", 0)

    hits, changed = [], False
    for it in items:
        if it["notified"]:
            continue
        n = counts.get(((it["chat_id"], it["message_id"]), it["emoji"]))
        if n is None:
            continue
        it["current"] = n
        if n >= it["goal"]:
            it["notified"] = True
            changed = True
            hits.append(dict(it))
    if changed or counts:
        _save(items)
    return hits


def cleanup(max_age_hours: int = 48):
    """Eski kuzatuvlarni tozalaydi."""
    cut = int(time.time()) - max_age_hours * 3600
    items = [i for i in _load() if i.get("added", 0) > cut]
    _save(items)
