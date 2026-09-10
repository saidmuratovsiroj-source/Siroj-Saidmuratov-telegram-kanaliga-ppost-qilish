"""Asosiy kanal (@Siroj_aiPro_Academy) uchun post generatori.

Oqim: mavzu (yangilik / maslahat / kurs) -> yozish -> rasm -> tasdiq -> kanal.

Mavzu turi `funnel/main_channel.json` dagi navbat bilan aniqlanadi:
  6 ta yangilik -> 1 ta amaliy maslahat -> 1 ta kurs taklifi -> boshidan.
Har 3-postda jamoaga yumshoq chorlov qo'shiladi.
"""
import sys
import traceback
from datetime import datetime

import config
from src.telegram import Telegram
from src.gemini import Gemini
from src.archive import Archive
from src import hype, poster, pool, voice

BTN = [[{"text": "✅ Chiqsin", "callback_data": "post:publish"},
        {"text": "🔄 Qayta yoz", "callback_data": "post:rewrite"},
        {"text": "❌ Bekor", "callback_data": "post:cancel"}]]

KIND_UZ = {"news": "yangilik", "tool": "amaliy maslahat", "offer": "kurs taklifi"}


def log(msg):
    print(f"[{datetime.now(config.TZ).strftime('%H:%M:%S')}] {msg}", flush=True)


def check(cap: str):
    """Mexanik tekshiruv — modelning tipik xatolari."""
    import re
    if not cap:
        return "Post bo'sh"
    if re.search(r"[Ѐ-ӿ]", cap):
        return "Matnda kirill harflari bor — faqat lotin yozuvida yoz"
    if len(cap) > config.CAPTION_LIMIT:
        return f"Uzunlik {len(cap)} > {config.CAPTION_LIMIT} — qisqartir"
    if re.search(r"\boqim", cap, re.I):
        return "'oqim' so'zi ishlatilgan — 'yangi guruh' yoki 'o'qish boshlanadi' deb yoz"
    for w in ("so'm", "narxi", "chegirma"):
        if w in cap.lower():
            return "Narx haqida gapirilgan — narxni umuman tilga olma"
    return None


def main():
    tg = Telegram(config.TELEGRAM_TOKEN)
    gem = Gemini(config.GEMINI_API_KEY)
    archive = Archive(config.ARCHIVE_PATH)

    if not tg.can_post(config.CHANNEL_ID):
        raise SystemExit(f"XATO: bot {config.CHANNEL_ID} kanalida post yoza olmaydi.")
    log(f"Kanal tekshirildi: {config.CHANNEL_ID} | arxivda {len(archive.items)} ta post")
    tg.drain()

    for round_no in range(1, config.MAX_REWRITES + 1):
        post, meta = hype.build(gem, archive)
        cap = (post.get("caption") or "").strip()
        log(f"Tur: {meta['kind']} | {len(cap)} belgi")

        bad = check(cap)
        if bad:
            log(f"Mexanik tekshiruv: {bad} — qayta yozamiz")
            continue

        seed = len(archive.items)
        image = poster.make_poster(
            meta.get("image_big") or post.get("image_title") or "AI",
            kicker=meta.get("kicker", config.RUBRIC),
            note=meta.get("image_small", ""),
            cta=config.CHANNEL_ID,
            illustration=pool.pick(seed),
            seed=seed)

        head = (f"<i>faqat siz ko'rasiz — kanalga chiqmaydi</i>\n"
                f"{config.CHANNEL_ID} · {KIND_UZ.get(meta['kind'], meta['kind'])} "
                f"· urinish {round_no}/{config.MAX_REWRITES}\n")
        if meta.get("source_url"):
            head += f"Manba: {meta['source_url']}\n"
        head += "— — — — —\n"

        if not config.AUTO_PUBLISH:
            tg.send_photo(config.ADMIN_CHAT_ID, image, head + cap, buttons=BTN)
            log(f"Tasdiqqa yuborildi. {config.APPROVAL_TIMEOUT_MIN} daqiqa kutamiz…")

            data, cb = tg.wait_for_callback("post:", config.APPROVAL_TIMEOUT_MIN * 60)
            if data is None:
                log("Javob kelmadi — post chiqarilmadi.")
                tg.send_message(config.ADMIN_CHAT_ID,
                                "⏰ Vaqt tugadi, post chiqmadi.")
                return
            action = data.split(":", 1)[1]
            tg.answer_callback(cb, {"publish": "Chiqarilmoqda…",
                                    "rewrite": "Qayta yozilmoqda…",
                                    "cancel": "Bekor qilindi"}.get(action, ""))
            if action == "cancel":
                log("Bekor qilindi.")
                tg.send_message(config.ADMIN_CHAT_ID, "❌ Bekor qilindi.")
                return
            if action == "rewrite":
                log("Qayta yozilmoqda…")
                continue
        else:
            log("AVTO rejim — tasdiq so'ralmaydi.")

        tg.send_photo(config.CHANNEL_ID, image, cap)
        audio, akind = voice.make(post.get("audio") or "")
        if audio:
            try:
                tg.send_voice(config.CHANNEL_ID, audio, akind)
            except Exception as e:
                log(f"ovoz yuborilmadi: {e}")
        archive.add(meta.get("source_title") or (meta.get("image_big") or "post"),
                    meta["kind"], cap[:160], meta.get("source_url", ""))
        log("Kanalga chiqarildi ✅")
        if config.AUTO_PUBLISH:
            note = (f"📤 <b>Chiqdi</b> · {config.CHANNEL_ID} · "
                    f"{KIND_UZ.get(meta['kind'], meta['kind'])}\n"
                    f"Yoqmasa ayting — o'chiraman.\n— — — — —\n")
            try:
                tg.send_photo(config.ADMIN_CHAT_ID, image, note + cap)
            except Exception as e:
                log(f"nusxa yuborilmadi: {e}")
        else:
            tg.send_message(config.ADMIN_CHAT_ID, "✅ Post kanalga chiqdi.")
        return

    tg.send_message(config.ADMIN_CHAT_ID,
                    f"🔄 {config.MAX_REWRITES} marta qayta yozildi, tasdiqlanmadi. "
                    f"Post chiqmadi.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            Telegram(config.TELEGRAM_TOKEN).send_message(
                config.ADMIN_CHAT_ID,
                f"🔥 Bot xato bilan to'xtadi:\n<code>{traceback.format_exc()[-800:]}</code>")
        except Exception:
            pass
        sys.exit(1)
