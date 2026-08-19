"""AiPro bot — barcha sozlamalar shu yerda."""
import os
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")

# --- Maxfiy kalitlar (Railway Variables orqali beriladi) ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHANNEL_ID = os.environ["CHANNEL_ID"]        # masalan: @aipro_kanal
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]  # Sirojning shaxsiy chat ID si

# --- Gemini modellari ---
MODEL_RESEARCH = os.getenv("MODEL_RESEARCH", "gemini-3.5-flash")
MODEL_WRITER = os.getenv("MODEL_WRITER", "gemini-3.5-flash")
MODEL_QC = os.getenv("MODEL_QC", "gemini-3.1-flash-lite")
MODEL_IMAGE = os.getenv("MODEL_IMAGE", "gemini-3.1-flash-image")  # faqat IMAGE_MODE=ai bo'lsa

# --- Rasm rejimi ---
#   "pool" = tayyor illyustratsiyalar bazasi + plakat tipografikasi (bepul, tavsiya)
#   "ai"   = Gemini har post uchun yangi rasm yasaydi (billing kerak)
#   "card" = eski brend kartochkasi (illyustratsiyasiz)
IMAGE_MODE = os.getenv("IMAGE_MODE", "pool")

# --- Asosiy kanal rubrikasi ---
# Endi faqat Claude emas: xalqaro AI yangiliklari, daromad hikoyalari, hayp
# mavzular. 8 postdan bittasi kurs taklifi, bittasi amaliy maslahat.
# Navbat funnel/main_channel.json dagi "rotation" bilan boshqariladi.
RUBRIC = "AI yangiliklari"
LEVELS = ["boshlangich", "orta"]  # eski tizim uchun qoldirildi

# --- Xalqaro AI yangiliklari (RSS, bepul, kalitsiz) ---
NEWS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Google News AI", "https://news.google.com/rss/search?q=artificial+intelligence"
                       "+when:3d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News: AI daromad", "https://news.google.com/rss/search?q=%22AI%22+"
                                "%28side+hustle+OR+freelancer+OR+earned%29+when:7d"
                                "&hl=en-US&gl=US&ceid=US:en"),
]
NEWS_MAX_AGE_DAYS = int(os.getenv("NEWS_MAX_AGE_DAYS", "5"))

# --- Rasmiy manbalar: Claude Help Center bo'limlari ---
# Bot mavzularni shulardan oladi va faktlarni shularga qarshi tekshiradi.
_HC = "https://support.claude.com/en/collections/"
COLLECTIONS = [
    ("Claude", _HC + "4078531-claude"),
    ("Cowork", _HC + "19667525-claude-cowork"),
    ("Desktop", _HC + "16163169-claude-desktop"),
    ("Mobile", _HC + "9387080-claude-mobile-apps"),
    ("Connectors", _HC + "15399129-connectors"),
    ("Chrome", _HC + "18031491-claude-in-chrome"),
    ("Pro/Max", _HC + "5953830-pro-and-max-plans"),
]
SHORTLIST_SIZE = 40  # modelga nechta sarlavha ko'rsatiladi

# --- Ovoz (ElevenLabs) ---
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George
ELEVEN_MODEL = os.getenv("ELEVEN_MODEL", "eleven_v3")
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "1") == "1"
VOICE_MAX_CHARS = int(os.getenv("VOICE_MAX_CHARS", "700"))

# --- Vebinar dajim tizimi ---
FUNNEL_CAMPAIGN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "funnel", "campaign.json")
REACTION_GOAL = int(os.getenv("REACTION_GOAL", "100"))
FUNNEL_TIMEOUT_MIN = int(os.getenv("FUNNEL_TIMEOUT_MIN", "90"))

# Soat -> qaysi vazifa (Toshkent vaqti)
#   07 -> queued : kecha tasdiqlangan post 4 kanalga CHIQADI (so'ramasdan)
#   10 -> value  : vebinar kanallariga, tasdiq so'raladi
#   12 -> main   : asosiy kanalga, tasdiq so'raladi
#   17 -> closing: vebinar kanallariga, tasdiq so'raladi
#   19 -> prepare: ERTANGI 07:00 posti yoziladi va tasdiqqa yuboriladi
# Railway cron (UTC):  0 2,5,7,12,14 * * *
SCHEDULE = {7: "queued", 10: "value", 12: "main", 17: "closing", 19: "prepare"}

# --- Tasdiq ---
APPROVAL_TIMEOUT_MIN = int(os.getenv("APPROVAL_TIMEOUT_MIN", "120"))
MAX_REWRITES = 3

# --- Sifat nazorati ---
QC_MAX_ATTEMPTS = 2

# --- Post cheklovlari (Telegram: rasm caption = 1024 belgi) ---
CAPTION_LIMIT = 1024
TARGET_LENGTH = (400, 800)  # maqbul oraliq

# --- Fayllar ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
ARCHIVE_PATH = os.path.join(DATA_DIR, "archive.json")
STYLE_GUIDE_PATH = os.path.join(BASE_DIR, "style", "style_guide.md")
EXAMPLES_DIR = os.path.join(BASE_DIR, "style", "examples")
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "bold.ttf")

# --- Rasm ---
IMAGE_SIZE = (1080, 1080)
OVERLAY_TITLE = os.getenv("OVERLAY_TITLE", "1") == "1"  # sarlavhani rasm ustiga qo'yish
BRAND_ACCENT = os.getenv("BRAND_ACCENT", "#E8FF59")
