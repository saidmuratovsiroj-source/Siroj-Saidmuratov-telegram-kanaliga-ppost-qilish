"""Mini kurs sotuv postlari — "AI Video Creator".

Farqi oddiy postlardan:
  - post oxirida MATNLI havola emas, pastda TUGMA turadi (to'lov botiga)
  - rasm marjon rangda, yuqorida "MINI KURS" yozuvi — lentada darhol tanilади
  - har post boshqa burchakdan (funnel/minikurs.json dagi angles ro'yxati)

Eng muhim qoida: "bu mini kurs, katta kurs emas" deb ochiq aytiladi.
Odam katta kurs kutib, keyin hafsalasi pir bo'lmasin.
"""
import json
import os
from datetime import date, datetime

import config

BRIEF = os.path.join(config.BASE_DIR, "funnel", "minikurs.json")

SYSTEM = """Sen Siroj Saidmuratovning Telegram kanallari uchun kopirayter yozuvchisisan.

AUDITORIYA:
- Obunachilarning 60-80 foizi AYOLLAR: uy bekalari, onalar, o'qituvchilar.
- Kod yozmaydi, texnik emas. Ko'pchiligining puli chegaralangan.
- Misollarni shu hayotdan ol: bolalar uxlagandan keyingi vaqt, uy ishlari orasidagi
  soat, maktabdagi ish, qo'shni do'koni, dugonalar davrasi.
- "Erkaklar klubi" ohangi BO'LMASIN. Kamsituvchi ohang ham yo'q.

USLUB:
- BIRINCHI SHAXSDA: "tayyorladim", "ko'rsataman", "o'rgataman".
- Qisqa xatboshilar. Har xatboshidan keyin BO'SH QATOR.
- Emoji o'rinli va kam, qator oxirida: 🎬 🔥 👇 ⚡️ 📌 🚨 👀
- Eng muhim shart KATTA HARFLAR bilan.
- <b> bilan faqat eng muhim joyni urg'ula. Markdown ISHLATMA.
- Faqat o'zbek tili, lotin yozuvi. Kirill yoki ruscha harf BO'LMASIN.

QAT'IY TAQIQLAR (buzilsa post chiqmaydi):
- ASBOBLAR NARXI haqida BIR OG'IZ ham gapirma. "Bepul asboblar", "pullik
  dastur kerak emas", "qo'shimcha xarajat yo'q" — bularning hech biri YO'Q.
  Asboblarning pullik yoki bepul ekani umuman tilga olinmaydi.
- "Bu kurs pul yig'ish uchun emas", "men pul uchun qilmadim", "daromad
  ko'zlanmagan" kabi gaplar TAQIQLANGAN. Bunday gaplar odamda salbiy
  taassurot qoldiradi. Sirojning moliyaviy niyati haqida umuman yozma.
- Narxni oqlashga urinma. Narx shunchaki aytiladi, tushuntirilmaydi.
- HAVOLA YOZMA. Bot manzilini, @ belgisini, http ni matnga qo'yma.
  Pastda TUGMA bor — odam shuni bosadi. Matnda "pastdagi tugmani bosing" deyish mumkin.
- O'zingdan raqam, statistika, o'quvchi natijasi O'YLAB TOPMA.
  Faqat brifdagi raqamlar: narx, joylar soni, kunlar soni.
- Kafolat berma: "albatta daromad qilasiz" — yo'q.
- Dars nomlari, asbob nomlarini o'ylab topma — brifda yo'q bo'lsa yozma."""

PROMPT = """Mini kurs uchun sotuv posti yoz.

MINI KURS: {name}
NIMA U: {what}
NIMA EMAS: {not_included}
ASL SABAB: {why}

RAQAMLAR (faqat shular, boshqasini o'ylab topma):
- Narx: {price}
- Joylar: {seats} ta — tugagach yopiladi
- Qabul: {open_days} kun ochiq

QABUL HOLATI — POSTDAGI SHOSHILINCHLIK AYNAN SHUNGA MOS BO'LSIN:
{urgency}

KUN VAQTI — faqat OHANG uchun. Bu izohdagi so'zlarni postga KO'CHIRMA:
{daypart}

BUGUNGI BURCHAK (faqat shu haqda yoz):
{angle}

OXIRGI CHIQQAN POSTLAR — BULARNI O'QIB CHIQ:
{recent}

ENG QAT'IY QOIDA: birinchi qator yuqoridagi postlarning birortasiga ham
o'xshamasin. Bir xil manzara bilan boshlash TAQIQLANGAN — kun tartibi,
uy-ro'zg'or manzarasi, telefon qo'lga olish kabi ilgaklar takrorlangan.
Bu safar butunlay boshqa joydan kir: to'g'ridan-to'g'ri savol, bitta qisqa
gap, raqam, qarama-qarshilik yoki aniq hayotiy holat.

TUZILMA:
1. Ilgak — shu burchakka tegishli aniq holat, savol yoki gap
2. Mazmun — 4-8 qisqa qator
3. Bir joyda ochiq aytiladi: bu MINI kurs, katta kurs emas
4. SHOSHILINCHLIK — yuqoridagi "QABUL HOLATI" ohangida, MAJBURIY
5. Oxirgi qator — pastdagi tugmaga ishora

HAR POSTDA odam "keyinroq qarayman" deb qo'ya olmasligi kerak.
Kechiktirishning narxi aniq ko'rinsin: joy tugaydi yoki qabul yopiladi.
Lekin qo'rqitma va yolg'on raqam aytma — faqat brifdagi raqamlar.

Uzunligi 500-800 belgi. Havola yozma.

FAQAT shu JSON qaytar:
{{"caption": "postning to'liq matni HTML bilan",
  "image_big": "rasmga chiqadigan 1-4 so'z (emojisiz)",
  "image_small": "rasm uchun kichik yozuv, 4-7 so'z",
  "audio": "og'zaki variant — emoji, havola va teg yo'q, 250-450 belgi"}}"""


def load_brief():
    with open(BRIEF, encoding="utf-8") as f:
        return json.load(f)


def button(brief) -> list:
    """Post ostidagi tugma — to'lov botiga olib boradi."""
    return [[{"text": brief["button_text"], "url": brief["bot"]}]]


def days_left(b) -> int:
    """Qabul tugashiga necha kun qoldi. Sana berilmagan bo'lsa — to'liq muddat."""
    start = b.get("start_date")
    if not start:
        return b.get("open_days", 7)
    try:
        d0 = date.fromisoformat(start)
    except Exception:
        return b.get("open_days", 7)
    gone = (datetime.now(config.TZ).date() - d0).days
    return max(0, b.get("open_days", 7) - gone)


def urgency_text(b) -> tuple:
    """(matn, bosqich) — qolgan kunga qarab shoshilinchlik ohangi."""
    left = days_left(b)
    if left <= 0:
        return ("QABUL YOPILDI deb yozma. Bugun — eng oxirgi imkoniyat. "
                "Qisqa, qat'iy, ortiqcha gapsiz. Ertaga kech bo'lishini ayt.", "oxirgi")
    if left == 1:
        return (f"Qabulga BIR KUN qoldi. Bu — oxirgi kun. Ohang qat'iy va qisqa. "
                f"Joylar {b['seats']} ta edi, tugab bormoqda.", "1kun")
    if left <= 3:
        return (f"Qabul tugashiga {left} kun qoldi. Joylar tugab bormoqda. "
                f"Ohang tig'iz — kechiktirgan ulgurmaydi.", "sanoq")
    return (f"Qabul {left} kun ochiq, jami {b['seats']} ta joy. Ohang tinch, "
            f"lekin oxirida aniq turtki bo'lsin: joy cheklangan, keyin yopiladi.", "ochiq")


# DIQQAT: bu izohlar faqat OHANGNI belgilaydi. Ilgari bu yerda "bolalar
# uxlagan payt" degan tasvir bor edi va model uni har postning birinchi
# qatoriga ko'chirib yozaverdi. Shuning uchun endi bu yerda ko'chirib
# bo'ladigan manzara yo'q — faqat ohang aytiladi.
DAYPARTS = {
    "fact": "Ertalab o'qiladi. Ohang tetik, ilgak qisqa.",
    "value": "Tushdan oldin o'qiladi. O'ylantiradigan savol yaxshi ishlaydi.",
    "main": "Tushlik payti lentada ko'riladi. Birinchi qatorning o'zi ushlab olsin.",
    "mini": "Kechqurun o'qiladi. Ohang tinchroq va samimiyroq.",
    "closing": "Yopilish posti. Ohang eng qat'iy, gap kam.",
}


def build(gem, slot="mini"):
    """(post, meta) qaytaradi. slot — kun vaqtini belgilaydi."""
    from src import history
    b = load_brief()
    a = history.pick_angle("mini", b["angles"])
    angle = a["angle"] if a else b["angles"][0]["angle"]
    urg, stage = urgency_text(b)
    left = days_left(b)
    print(f"[minikurs] burchak: {a['id'] if a else '—'} | qolgan: {left} kun | "
          f"bosqich: {stage} | slot: {slot}")

    prompt = PROMPT.format(
        name=b["name"], what=b["what_it_is"], not_included=b["not_included"],
        why=b["why"], price=b["price"], seats=b["seats"],
        open_days=b["open_days"], angle=angle, urgency=urg,
        daypart=DAYPARTS.get(slot, DAYPARTS["mini"]),
        recent=history.recent_text(8))

    post = gem.json(config.MODEL_WRITER, prompt, system=SYSTEM, temperature=0.95)
    post["caption"] = _strip_links(post.get("caption", ""))

    tail = f"{left} kun qoldi" if left > 0 else "oxirgi kun"
    meta = {
        "slot": "mini",
        "angle_id": a["id"] if a else "",
        "kicker": "MINI KURS",
        "image_big": post.get("image_big") or "Mini kurs",
        "image_small": post.get("image_small") or f"{b['price']} · {b['seats']} ta joy",
        "lines": [b["price"], f"{b['seats']} ta joy", tail],
    }
    return post, meta


BANNED = [
    "bepul asbob", "asboblar bepul", "pullik emas", "pul to'lash shart emas",
    "qo'shimcha xarajat", "qo'shimcha to'lov", "bepul dasturlar",
    "pul yig'ish uchun emas", "pul uchun emas", "daromad uchun emas",
    "foyda ko'zlanmagan", "pul ishlash uchun emas",
]


def forbidden(cap: str, brief=None) -> str:
    """Taqiqlangan ibora bormi. Bo'lsa sababni qaytaradi."""
    import re
    low = cap.lower()
    for w in BANNED:
        if w in low:
            return f"Taqiqlangan ibora: \"{w}\""

    # Mini kurs postida narx aytiladi — LEKIN faqat brifdagi narx.
    # Katta kurs narxi yoki o'ylab topilgan summa chiqib qolmasin.
    if brief:
        ok = re.sub(r"\D", "", brief.get("price", ""))
        for m in re.findall(r"([\d\s '’.,]{3,})\s*so['’`ʻ]?m", low):
            digits = re.sub(r"\D", "", m)
            if digits and ok and digits != ok:
                return (f"Noto'g'ri summa: {m.strip()} so'm — "
                        f"faqat {brief['price']} aytiladi")
    return ""


def _strip_links(cap: str) -> str:
    """Model havola yozib qo'ysa — o'chiramiz. Havola faqat tugmada."""
    import re
    cap = re.sub(r"https?://\S+", "", cap)
    cap = re.sub(r"@[A-Za-z0-9_]{3,}", "", cap)
    cap = re.sub(r"[ \t]+\n", "\n", cap)
    return re.sub(r"\n{3,}", "\n\n", cap).strip()
