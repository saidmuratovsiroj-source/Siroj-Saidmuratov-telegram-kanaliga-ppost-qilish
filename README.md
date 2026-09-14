# AiPro — avtomatik Telegram post boti

Kuniga 4 marta o'zi uyg'onadi, post yozadi, rasm yasaydi, tekshiradi va
kanallarga chiqaradi. Tasdiq so'ramaydi (`AUTO_PUBLISH=1`), nusxasini
Sirojning shaxsiy chatiga yuboradi.

## Jadval (Toshkent vaqti)

| Soat | Slot | Qayerga | Nima |
|------|------|---------|------|
| 07:00 | `fact` | 4 vebinar kanali | qiziqarli fakt / dajim |
| 10:00 | `value` | 4 vebinar kanali | kurs qiymati |
| 12:00 | `main` | @Siroj_aiPro_Academy | xalqaro AI yangiligi |
| 17:00 | `mini` | 5 kanal | mini kurs sotuv posti (tugma bilan) |

Jadval `.github/workflows/post.yml` da, UTC da yozilgan (Toshkent = UTC + 5).

## Qayerda ishlaydi

**GitHub Actions** — bepul. Railway kerak emas.
Har ishga tushganda yangi konteyner ochiladi, bitta post chiqaradi, o'chadi.

Takrorlanmaslik tarixi (`data/funnel_history.json`) va ishlatilgan faktlar
(`funnel/facts.json`) har safar repozitoriyga qaytarib yoziladi — shuning
uchun bot ertaga nima yozganini eslab qoladi.

## Kerakli Secrets

`Settings → Secrets and variables → Actions → New repository secret`:

| Nomi | Qiymat |
|------|--------|
| `TELEGRAM_TOKEN` | @BotFather bergan token |
| `GEMINI_API_KEY` | aistudio.google.com dan (bepul limit yetarli) |
| `CHANNEL_ID` | `@Siroj_aiPro_Academy` |
| `ADMIN_CHAT_ID` | `5872633589` |
| `ELEVEN_API_KEY` | ElevenLabs (ovoz kerak bo'lmasa bo'sh qoldiring) |

## Qo'lda post chiqarish

`Actions → AiPro post → Run workflow` → slotni tanlang → `Run workflow`.

## Sozlamalar

| Fayl | Nima uchun |
|------|-----------|
| `funnel/campaign.json` | vebinar kanallari, menejer, o'qish sanasi |
| `funnel/angles.json` | 37 ta burchak — postlar takrorlanmasligi uchun |
| `funnel/main_channel.json` | asosiy kanal navbati, har 4-postda taklif |
| `funnel/minikurs.json` | mini kurs: narx, joylar, tugma, 14 burchak |
| `funnel/facts.json` | haqiqiy hikoyalar (faqat tekshirilganini yozing) |
| `images/` | 24 ta illyustratsiya — plakat foni |
| `style/` | yozish qoidalari va namuna postlar |

## Muhim qoidalar (kodga o'rnatilgan)

- Faqat o'zbek tili, lotin yozuvi — kirill bo'lsa post chiqmaydi
- Katta kurs narxi hech qachon aytilmaydi
- "oqim" so'zi taqiqlangan → "yangi guruh" / "o'qish boshlanadi"
- Mini kurs postlarida: asboblar narxi va "pul uchun emas" gaplari taqiqlangan
- Postlar oxirgi 25 ta postga 35% dan ko'p o'xshasa — qayta yoziladi
- Rasmdagi matnni AI emas, `src/poster.py` chizadi (o' va g' toza chiqsin)

## Mahalliy sinov

```bash
pip install -r requirements.txt
export $(cat .env | xargs)
python run.py main
```
