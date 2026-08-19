"""AiPro — yagona kirish nuqtasi.

Soatga qarab qaysi vazifa bajarilishini hal qiladi (config.SCHEDULE, Toshkent):

  07:00  queued   -> kecha tasdiqlangan post 4 vebinar kanaliga CHIQADI (so'ramasdan)
  10:00  value    -> vebinar kanallariga: kurs qiymati (tasdiq so'raladi)
  12:00  main     -> asosiy kanalga: AI yangiligi / maslahat / taklif (tasdiq so'raladi)
  17:00  closing  -> vebinar kanallariga: dajim yoki trigger (tasdiq so'raladi)
  19:00  prepare  -> ERTANGI 07:00 posti yoziladi va tasdiqqa yuboriladi

Nega 19:00: ertalab soat 7 da Siroj tugma bosa olmaydi. Shuning uchun ertangi
post kechqurun tasdiqlanadi va navbatga saqlanadi (src/queue.py).

Nega bitta fayl: Telegram bitta botga faqat BITTA getUpdates tinglovchisiga
ruxsat beradi. Ikkita alohida xizmat bo'lsa, tugmalar ishlamay qoladi.

Qo'lda ishga tushirish:  python run.py value
"""
import re
import sys
import traceback
from datetime import date, datetime

import config
from src.telegram import Telegram
from src.gemini import Gemini
from src import funnel, poster, pool, queue, reactions, voice

BTN = [[{"text": "✅ Chiqsin", "callback_data": "post:publish"},
        {"text": "🔄 Qayta yoz", "callback_data": "post:rewrite"},
        {"text": "❌ Bekor", "callback_data": "post:cancel"}]]

# 19:00 da tayyorlanadigan ertangi post qaysi turda bo'ladi
PREPARE_SLOT = "fact"


def log(msg):
    print(f"[{datetime.now(config.TZ).strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------- yordamchilar
def _mech_check(cap: str):
    if not cap:
        return "Post bo'sh"
    if re.search(r"[Ѐ-ӿ]", cap):
        return "Matnda kirill harflari bor — faqat lotin yozuvida yoz"
    if len(cap) > config.CAPTION_LIMIT:
        return f"Uzunlik {len(cap)} > {config.CAPTION_LIMIT} — qisqartir"
    for w in ("so'm", "dollar kurs", "narxi", "chegirma", "aksiya narx"):
        if w in cap.lower():
            return "Narx haqida gapirilgan — narxni umuman tilga olma"
    if re.search(r"\boqim", cap, re.I):
        return "'oqim' so'zi ishlatilgan — 'yangi guruh' yoki 'o'qish boshlanadi' deb yoz"
    if re.search(r"(ertaga|bugun|indinga)[^.\n]{0,20}\d{1,2}[:.]\d{2}", cap, re.I):
        return "Aniq sana/soat va'da qilingan — efirni faqat shart bilan bog'la"
    bad = [h for h in re.findall(r"@[A-Za-z0-9_]{3,}", cap)
           if h.lower() != funnel.load_campaign()["manager"].lower()]
    if bad:
        return f"Yolg'on havola: {', '.join(bad[:3])} — havola yozma"
    if re.search(r"[\[{](havola|link|menejer|manager)[\]}]", cap, re.I):
        return "Matnda joy tutuvchi qolgan — to'liq yoz"
    return None


def _short_lines(cap: str, n=3):
    plain = re.sub(r"<[^>]+>", "", cap)
    out = []
    for line in plain.split("\n"):
        line = line.strip()
        if 25 <= len(line) <= 52 and not line.startswith("@"):
            out.append(line)
        if len(out) == n:
            break
    return out


def _make_image(cap, meta, manager):
    seed = abs(hash(cap)) % 9999
    return poster.make_stat_poster(
        big=meta.get("image_big") or "AI",
        small=meta.get("image_small", ""),
        note=meta.get("image_note", ""),
        kicker=meta.get("kicker", "AI PRO"),
        lines=_short_lines(cap),
        cta=manager,
        illustration=pool.pick(seed),
        seed=seed)


def _admins_ok(tg, chans):
    for chan in chans:
        m = tg._call("getChatMember",
                     json={"chat_id": chan["id"], "user_id": tg.me()["id"]})
        if not (m.get("status") == "administrator" and m.get("can_post_messages")):
            log(f"XATO: {chan['title']} — bot admin emas yoki post yoza olmaydi")
            return False
    return True


def _send_to_channels(tg, chans, image, cap, audio_text):
    audio, kind = voice.make(audio_text or "")
    posted = []
    for chan in chans:
        try:
            r = tg.send_photo(chan["id"], image, cap)
            posted.append({"chat_id": chan["id"], "message_id": r["message_id"],
                           "title": chan["title"]})
            if audio:
                try:
                    tg.send_voice(chan["id"], audio, kind)
                except Exception as e:
                    log(f"   ovoz yuborilmadi ({chan['title']}): {e}")
            log(f"✅ {chan['title']}" + (" + ovoz" if audio else ""))
        except Exception as e:
            log(f"❌ {chan['title']}: {e}")
    return posted


# ---------------------------------------------------------------- vebinar
def run_funnel(tg, gem, slot, mode="now"):
    """mode='now'  — tasdiqdan keyin darhol chiqaradi
       mode='queue' — tasdiqdan keyin ertangi kunga saqlaydi"""
    c = funnel.load_campaign()
    chans = c["channels"]
    log(f"Vebinar sloti: {slot} ({mode}) | {len(chans)} kanal | start {c['start_date']}")

    if not _admins_ok(tg, chans):
        return

    for attempt in range(1, config.MAX_REWRITES + 1):
        post, meta = funnel.build(gem, slot)
        cap = (post.get("caption") or "").strip()
        log(f"Post yozildi ({len(cap)} belgi), slot={meta['slot']}")

        bad = _mech_check(cap)
        if bad:
            log(f"Mexanik tekshiruv: {bad} — qayta yozamiz")
            continue

        image = _make_image(cap, meta, c["manager"])

        # Bu sarlavha FAQAT Sirojning shaxsiy chatida ko'rinadi.
        when = "ERTAGA 07:00 da chiqadi" if mode == "queue" else "tasdiqdan keyin chiqadi"
        head = (f"<i>faqat siz ko'rasiz — kanalga chiqmaydi</i>\n"
                f"{len(chans)} kanal · {when} · o'qishgacha {meta['days_left']} kun\n")
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
        tg.answer_callback(cb, {"publish": "Qabul qilindi…", "rewrite": "Qayta yozilmoqda…",
                                "cancel": "Bekor"}.get(action, ""))

        if action == "cancel":
            log("Bekor qilindi.")
            return
        if action == "rewrite":
            continue

        if mode == "queue":
            queue.save(cap, image, post.get("audio") or "", meta)
            tg.send_message(config.ADMIN_CHAT_ID,
                            "📌 Saqlandi. Ertaga soat 07:00 da 4 kanalga o'zi chiqadi.")
            return

        posted = _send_to_channels(tg, chans, image, cap, post.get("audio"))
        if meta.get("fact_id"):
            funnel.mark_used(meta["fact_id"])
        if meta.get("watch_reactions") and posted:
            reactions.watch(posted, config.REACTION_GOAL)
        tg.send_message(config.ADMIN_CHAT_ID,
                        f"✅ {len(posted)}/{len(chans)} kanalga chiqdi.")
        return

    tg.send_message(config.ADMIN_CHAT_ID,
                    "🔄 Bir nechta urinishdan keyin ham tasdiqlanmadi. Post chiqmadi.")


def publish_queued(tg):
    """07:00 — kecha tasdiqlangan postni so'ramasdan chiqaradi."""
    q = queue.load()
    if not q:
        log("Navbatda post yo'q — bugun ertalabki post chiqmaydi.")
        tg.send_message(config.ADMIN_CHAT_ID,
                        "⚠️ Ertalabki post navbatda yo'q edi — bugun 07:00 da hech "
                        "narsa chiqmadi. Kechqurun tasdiqlab qo'ying.")
        return
    if q.get("for_day") and q["for_day"] > date.today().isoformat():
        log(f"Navbatdagi post {q['for_day']} uchun — bugun emas. Tegmaymiz.")
        return

    c = funnel.load_campaign()
    chans = c["channels"]
    log(f"Navbatdagi post chiqarilmoqda ({len(chans)} kanal)")
    posted = _send_to_channels(tg, chans, q["image"], q["caption"], q.get("audio"))

    meta = q.get("meta") or {}
    if meta.get("fact_id"):
        funnel.mark_used(meta["fact_id"])
    if meta.get("watch_reactions") and posted:
        reactions.watch(posted, config.REACTION_GOAL)

    queue.clear()
    tg.send_message(config.ADMIN_CHAT_ID,
                    f"🌅 Ertalabki post {len(posted)}/{len(chans)} kanalga chiqdi.")


# ---------------------------------------------------------------- asosiy
def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else \
        config.SCHEDULE.get(datetime.now(config.TZ).hour)

    if not slot:
        log(f"Bu soat uchun vazifa yo'q ({datetime.now(config.TZ).hour}:00). Chiqamiz.")
        return

    tg = Telegram(config.TELEGRAM_TOKEN)
    log(f"Bot: @{tg.me()['username']} | slot: {slot}")

    try:
        for hit in reactions.check(tg):
            tg.send_message(config.ADMIN_CHAT_ID,
                            f"🔥 <b>Shart bajarildi!</b>\n{hit['title']} — "
                            f"{hit.get('current')} ta {hit['emoji']} "
                            f"(maqsad {hit['goal']}).\n\nJonli efir ochamizmi?")
        reactions.cleanup()
    except Exception as e:
        log(f"Reaksiya tekshiruvi o'tkazib yuborildi: {e}")

    # 07:00 — tasdiq so'ralmaydi, getUpdates ham kerak emas
    if slot == "queued":
        publish_queued(tg)
        return

    tg.drain()
    gem = Gemini(config.GEMINI_API_KEY)

    if slot in ("main", "claude"):
        import main as main_channel
        main_channel.main()
    elif slot == "prepare":
        run_funnel(tg, gem, PREPARE_SLOT, mode="queue")
    else:
        run_funnel(tg, gem, slot, mode="now")


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
