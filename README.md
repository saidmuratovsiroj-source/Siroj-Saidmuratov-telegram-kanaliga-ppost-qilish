# AiPro — "Claude maslahatlar" avtomatik post boti

Kuniga bir marta ishga tushadi, rasmiy manbadan yangi maslahat topadi,
Sirojning stilida post yozadi, brend kartochkasi yasaydi, sifat nazoratidan
o'tkazadi va **tasdiq so'raydi**. Siz "Chiqsin" bosgandan keyingina kanalga chiqadi.

## Oqim

```
1. Mavzu izlash      Claude Help Center'ning 7 bo'limidan ~350 rasmiy maqola
                     Arxivda bo'lganlari chiqarib tashlanadi, model bittasini tanlaydi
2. Post yozish       Stil qo'llanmasi + 6 namuna post asosida
3. Sifat nazorati    Har bir da'vo RASMIY MAQOLA MATNIGA qarshi tekshiriladi
                     + kirill/emoji/uzunlik/paragraf mexanik tekshiruvi
4. Rasm              Brend kartochkasi (bepul) yoki Gemini rasm (IMAGE_MODE=ai)
5. Tasdiq            Shaxsiy chatga: Chiqsin / Qayta yoz / Bekor
6. Chiqarish         Tasdiqlangach kanalga, manba arxivga yoziladi
```

## Nega Google Search ishlatilmaydi

Google Search grounding pullik (billing kerak). Uning o'rniga bot to'g'ridan-to'g'ri
`support.claude.com` dan o'qiydi. Bu aslida **ishonchliroq** — qidiruv tasodifiy
blogga tushishi mumkin, bu esa faqat rasmiy hujjatni ko'radi. Va bepul.

## Kerakli kalitlar (Railway -> Variables)

| O'zgaruvchi | Qiymat |
|---|---|
| `TELEGRAM_TOKEN` | @BotFather bergan token |
| `GEMINI_API_KEY` | aistudio.google.com dan (bepul limit yetarli) |
| `CHANNEL_ID` | `@Siroj_aiPro_Academy` |
| `ADMIN_CHAT_ID` | `5872633589` |
| `DATA_DIR` | `/data` |
| `IMAGE_MODE` | `card` (bepul) yoki `ai` (billing kerak) |
| `APPROVAL_TIMEOUT_MIN` | `120` |
| `BRAND_ACCENT` | `#E8FF59` |

## Railway'ga o'rnatish

1. Papkani GitHub'ga private repo qilib yuklang.
2. Railway -> **New** -> **Deploy from GitHub repo**.
3. **Variables** -> yuqoridagi qiymatlarni kiriting.
4. **Settings -> Volumes** -> yangi volume, mount path `/data`.
5. **Settings -> Cron Schedule**: `0 4 * * *` (UTC) = Toshkent 09:00.
6. **Settings -> Restart Policy**: `Never`.

## Narx

Bepul Gemini limitida ishlaydi. Railway cron rejimida kuniga ~10-15 daqiqa
(+ tasdiq kutish) ishlaydi — oyiga $1 dan kam, trial $5 krediti bir necha oyga yetadi.

## Stilni sozlash

- `style/style_guide.md` — yozish qoidalari
- `style/examples/*.txt` — namuna postlar

## Mahalliy sinov

```bash
pip install -r requirements.txt
export $(cat .env | xargs)
python main.py
```
