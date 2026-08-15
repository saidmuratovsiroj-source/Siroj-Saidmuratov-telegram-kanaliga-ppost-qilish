"""AiPro — yagona kirish nuqtasi.

Soatga qarab qaysi tizim ishlashini hal qiladi (config.SCHEDULE):
  07:00  claude   -> "Claude maslahatlar" posti @Siroj_aiPro_Academy ga
  10:00  fact     -> vebinar kanallariga: tekshirilgan haqiqiy voqea
  16:00  value    -> vebinar kanallariga: kurs qiymati
  20:00  closing  -> vebinar kanallariga: dajim yoki jonli efir triggeri

Nega bitta fayl: Telegram bitta botga faqat BITTA getUpdates tinglovchisiga
ruxsat beradi. Ikkita alohida xizmat bo'lsa, tugmalar ishlamay qoladi.
Bitta jarayon — hech qanday ziddiyat yo'q.

Qo'lda ishga tushirish:  python run.py fact
"""
import sys
import traceback
from datetime import datetime

import config
from src.telegram import Telegram
from src.gemini import Gemini
from src.archive import Archive
from src import funnel, poster, reactions

BTN = [[{"text": "✅ Chiqsin", "callback_data": "post:publish"},
        {"text": "🔄 Qayta yoz", "callback_data": "post:rewrite"},
        {"text": "❌ Bekor", "callback_data": "post:cancel"}]]


def log(msg):
    print(f"[{datetime.now(config.TZ).strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- vebinar
def run_funnel(tg, gem, slot):
    c = funnel.load_campaign()
    chans = c["channels"]
    log(f"Vebinar sloti: {slot} | {len(chans)} kanal | start {c['start_date']}")

    for chan in chans:
        m = tg._call("getChatMember", json={"chat_id": chan["id"], "user_id": tg.me()["id"]})
        if not (m.get("status") == "administrator" and m.get("can_post_messages")):
            log(f"XATO: {chan['title']} — bot admin emas yoki post yoza olmaydi")
            return

    feedback = ""
    for attempt in range(1, config.MAX_REWRITES + 1):
        post, meta = funnel.build(gem, slot)
        cap = post.get("caption", "").strip()
        log(f"Post yozildi ({len(cap)} belgi), slot={meta['slot']}")

        bad = _mech_check(cap)
        if bad:
            log(f"Mexanik tekshiruv: {bad} — qayta yozamiz")
            feedback = bad
            continue

        image = poster.make_stat_poster(
            big=meta.get("image_big") or "AI",
            small=meta.get("image_small", ""),
            note=meta.get("image_note", ""),
            kicker=meta.get("kicker", "AI PRO"),
            lines=_short_lines(cap),
            seed=abs(hash(cap)) % 9999)

        head = (f"<b>Vebinar kanallari · {meta['slot']}</b> · "
                f"{len(chans)} kanal · start gacha {meta['days_left']} kun\n")
        if meta.get("source_url"):
            head += f"Manba: {meta['source_url']}\n"
        head += "— — — — —\n"
        tg.send_photo(config.ADMIN_CHAT_ID, image, head + cap, buttons=BTN)
        log(f"Tasdiqqa yuborildi, {config.FUNNEL_TIMEOUT_MIN} daqiqa kutamiz…")

        data, cb = tg.wait_for_callback("post:", config.FUNNEL_TIMEOUT_MIN * 60)
        if data is None:
            log("Javob kelmadi — post chiqmadi.")
            return
        action = data.split(":", 1)[1]
        tg.answer_callback(cb, {"publish": "Chiqarilmoqda…", "rewrite": "Qayta yozilmoqda…",
                                "cancel": "Bekor"}.get(action, ""))

        if action == "cancel":
            log("Bekor qilindi.")
            return
        if action == "rewrite":
            feedback = "boshqacha yoz"
            continue

        posted = []
        for chan in chans:
            try:
                r = tg.send_photo(chan["id"], image, cap)
                posted.append({"chat_id": chan["id"], "message_id": r["message_id"],
                               "title": chan["title"]})
                log(f"✅ {chan['title']}")
            except Exception as e:
                log(f"❌ {chan['title']}: {e}")

        if meta.get("fact_id"):
            funnel.mark_used(meta["fact_id"])
        if meta.get("watch_reactions") and posted:
            reactions.watch(posted, config.REACTION_GOAL)

        tg.send_message(config.ADMIN_CHAT_ID,
                        f"✅ {len(posted)}/{len(chans)} kanalga chiqdi.")
        return

    tg.send_message(config.ADMIN_CHAT_ID, "🔄 Bir nechta urinishdan keyin ham "
                                          "tasdiqlanmadi. Post chiqmadi.")


def _mech_check(cap: str):
    import re
    if not cap:
        return "Post bo'sh"
    if re.search(r"[Ѐ-ӿ]", cap):
        return "Matnda kirill harflari bor — faqat lotin yozuvida yoz"
    if len(cap) > config.CAPTION_LIMIT:
        return f"Uzunlik {len(cap)} > {config.CAPTION_LIMIT} — qisqartir"
    for w in ("so'm", "dollar kurs", "narxi", "chegirma", "aksiya narx"):
        if w in cap.lower():
            return "Narx haqida gapirilgan — narxni umuman tilga olma"
    return None


def _short_lines(cap: str, n=3):
    """Rasm ostidagi izoh uchun postdan qisqa qatorlar."""
    import re
    plain = re.sub(r"<[^>]+>", "", cap)
    out = []
    for line in plain.split("\n"):
        line = line.strip()
        if 25 <= len(line) <= 52 and not line.startswith("👉"):
            out.append(line)
        if len(out) == n:
            break
    return out


# ---------------------------------------------------------------- asosiy
def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else \
        config.SCHEDULE.get(datetime.now(config.TZ).hour)

    if not slot:
        log(f"Bu soat uchun vazifa yo'q ({datetime.now(config.TZ).hour}:00). Chiqamiz.")
        return

    tg = Telegram(config.TELEGRAM_TOKEN)
    gem = Gemini(config.GEMINI_API_KEY)
    log(f"Bot: @{tg.me()['username']} | slot: {slot}")

    # har ishga tushganda reaksiyalarni tekshiramiz
    try:
        for hit in reactions.check(tg):
            tg.send_message(config.ADMIN_CHAT_ID,
                            f"🔥 <b>Shart bajarildi!</b>\n{hit['title']} — "
                            f"{hit.get('current')} ta {hit['emoji']} "
                            f"(maqsad {hit['goal']}).\n\nJonli efir ochamizmi?")
        reactions.cleanup()
    except Exception as e:
        log(f"Reaksiya tekshiruvi o'tkazib yuborildi: {e}")

    tg.drain()

    if slot == "claude":
        import main as claude_main
        claude_main.main()
    else:
        run_funnel(tg, gem, slot)


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
