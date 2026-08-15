"""AiPro — Claude maslahatlar rubrikasi uchun avtomatik post generatori.

Oqim: mavzu izlash -> yozish -> sifat nazorati -> rasm -> tasdiq -> kanalga chiqarish.
Railway'da cron xizmati sifatida kuniga bir marta ishga tushadi.
"""
import sys
import traceback
from datetime import datetime

import config
from src.telegram import Telegram
from src.gemini import Gemini
from src.archive import Archive
from src import research, writer, qc, cardgen

BTN = [[{"text": "✅ Chiqsin", "callback_data": "post:publish"},
        {"text": "🔄 Qayta yoz", "callback_data": "post:rewrite"},
        {"text": "❌ Bekor", "callback_data": "post:cancel"}]]


def log(msg):
    print(f"[{datetime.now(config.TZ).strftime('%H:%M:%S')}] {msg}", flush=True)


def preflight(tg: Telegram):
    me = tg.me()
    log(f"Bot: @{me['username']}")
    if not tg.can_post(config.CHANNEL_ID):
        raise SystemExit(f"XATO: bot {config.CHANNEL_ID} kanalida admin emas yoki "
                         f"'post messages' huquqi yo'q.")
    log(f"Kanal tekshirildi: {config.CHANNEL_ID}")


def build_post(gem, archive, level, feedback=""):
    """Mavzu -> post -> QC. Sifat nazoratidan o'tguncha qayta yozadi."""
    topic = research.find_topic(gem, archive, level)
    log(f"Mavzu: {topic.get('title')}")

    for attempt in range(1, config.QC_MAX_ATTEMPTS + 1):
        post = writer.write_post(gem, topic, feedback)
        log(f"Post yozildi ({len(post.get('caption',''))} belgi), tekshirilmoqda…")
        result = qc.check(gem, topic, post)
        log(f"QC: {result.get('verdict')} ({result.get('score')}/10)")
        if result.get("verdict") == "pass":
            return topic, post, result
        log(f"QC muammolari: {result.get('problems')}")
        feedback = result.get("fix_instruction") or "; ".join(result.get("problems", []))
        if attempt == config.QC_MAX_ATTEMPTS:
            log("QC bir necha marta o'tmadi — baribir tasdiqqa yuboramiz, belgi bilan")
            return topic, post, result
    return topic, post, result


def main():
    tg = Telegram(config.TELEGRAM_TOKEN)
    gem = Gemini(config.GEMINI_API_KEY)
    archive = Archive(config.ARCHIVE_PATH)

    preflight(tg)
    tg.drain()

    level = archive.next_level(config.LEVELS)
    log(f"Bugungi daraja: {level}")

    feedback = ""
    for round_no in range(1, config.MAX_REWRITES + 1):
        topic, post, qcr = build_post(gem, archive, level, feedback)

        log(f"Rasm tayyorlanmoqda ({config.IMAGE_MODE})…")
        card_title = post.get("image_title") or topic.get("title", "")
        if config.IMAGE_MODE == "ai":
            from src import imagegen
            image = imagegen.generate(gem, post.get("image_prompt", ""), card_title)
        elif config.IMAGE_MODE == "pool":
            from src import pool, poster
            image = poster.make_poster(card_title, kicker=config.RUBRIC,
                                       cta=config.CHANNEL_ID,
                                       illustration=pool.pick(len(archive.items)),
                                       seed=len(archive.items))
        else:
            image = cardgen.make_card(card_title, handle=config.CHANNEL_ID,
                                      accent=config.BRAND_ACCENT)

        warn = ""
        if qcr.get("verdict") != "pass":
            warn = "⚠️ <b>Sifat nazoratidan to'liq o'tmadi:</b>\n" + \
                   "\n".join(f"• {p}" for p in qcr.get("problems", [])[:4]) + "\n\n"

        header = (f"{warn}<b>Tasdiq kutilmoqda</b> · {level} · QC {qcr.get('score')}/10 "
                  f"· urinish {round_no}/{config.MAX_REWRITES}\n"
                  f"Manba: <a href=\"{topic.get('source_url','')}\">"
                  f"{topic.get('source_title','')}</a>\n"
                  f"— — — — —\n")
        tg.send_photo(config.ADMIN_CHAT_ID, image, header + post["caption"], buttons=BTN)
        log(f"Tasdiqqa yuborildi. {config.APPROVAL_TIMEOUT_MIN} daqiqa kutamiz…")

        data, cb_id = tg.wait_for_callback("post:", config.APPROVAL_TIMEOUT_MIN * 60)

        if data is None:
            log("Javob kelmadi — post chiqarilmadi.")
            tg.send_message(config.ADMIN_CHAT_ID,
                            "⏰ Vaqt tugadi, post chiqarilmadi. Ertaga yangisi keladi.")
            return

        action = data.split(":", 1)[1]
        tg.answer_callback(cb_id, {"publish": "Chiqarilmoqda…",
                                   "rewrite": "Qayta yozilmoqda…",
                                   "cancel": "Bekor qilindi"}.get(action, ""))

        if action == "publish":
            tg.send_photo(config.CHANNEL_ID, image, post["caption"])
            archive.add(topic.get("title", ""), level,
                        topic.get("tip", ""), topic.get("source_url", ""))
            log("Kanalga chiqarildi ✅")
            tg.send_message(config.ADMIN_CHAT_ID, "✅ Post kanalga chiqdi.")
            return

        if action == "cancel":
            log("Bekor qilindi.")
            tg.send_message(config.ADMIN_CHAT_ID, "❌ Bekor qilindi, post chiqmadi.")
            return

        feedback = ("Oldingi variant muallifga yoqmadi. Butunlay boshqa burchakdan, "
                    "boshqa ilgak va boshqa tuzilma bilan yoz.")
        log("Qayta yozilmoqda…")

    tg.send_message(config.ADMIN_CHAT_ID,
                    f"🔄 {config.MAX_REWRITES} marta qayta yozildi, hech biri tasdiqlanmadi. "
                    f"Bugun post chiqmadi.")


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
