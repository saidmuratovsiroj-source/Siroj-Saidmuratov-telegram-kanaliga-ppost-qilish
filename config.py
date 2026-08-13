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
# "card" = brend kartochkasi (bepul, barqaror) | "ai" = Gemini rasm (billing kerak)
IMAGE_MODE = os.getenv("IMAGE_MODE", "card")

# --- Rubrika ---
RUBRIC = "Claude maslahatlar"
LEVELS = ["boshlangich", "orta"]  # navbat bilan almashadi

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
