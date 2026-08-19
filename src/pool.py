"""Tayyor illyustratsiyalar bazasi.

Rasmlar Higgsfield'da bir marta yasalgan va manzillari images/sources.txt da.
Bot birinchi ishga tushganda ularni /data ichiga yuklab oladi va keyin
internetga chiqmasdan ishlaydi. Ya'ni manzillar keyin o'chsa ham bot ishlayveradi.

Yangi rasm qo'shish: sources.txt ga yangi qator qo'shish yoki
images/ papkasiga PNG tashlash. Boshqa hech narsa kerak emas.
"""
import os
import glob
import hashlib
import requests
import config

SOURCES = os.path.join(config.BASE_DIR, "images", "sources.txt")
LOCAL_DIR = os.path.join(config.BASE_DIR, "images")
# v2 — 3D personaj uslubi. Eski (sovet plakati) keshi ishlatilmasin.
CACHE_DIR = os.path.join(config.DATA_DIR, "images_v3")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AiProBot/1.0)"}


def _read_sources():
    if not os.path.exists(SOURCES):
        return []
    out = []
    for line in open(SOURCES, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _cache_path(url: str) -> str:
    name = hashlib.sha1(url.encode()).hexdigest()[:16] + ".png"
    return os.path.join(CACHE_DIR, name)


def _ensure_cached():
    """Manzillardagi rasmlarni /data ga yuklab oladi (bir marta)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    for url in _read_sources():
        p = _cache_path(url)
        if os.path.exists(p) and os.path.getsize(p) > 10_000:
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            with open(p, "wb") as f:
                f.write(r.content)
            print(f"[pool] yuklandi: {os.path.basename(p)} ({len(r.content)//1024} KB)")
        except Exception as e:
            print(f"[pool] yuklab bo'lmadi ({url[:60]}…): {e}")


def available() -> list:
    """Barcha mavjud rasmlar: avval repodagilar, keyin yuklab olinganlar."""
    files = sorted(glob.glob(os.path.join(LOCAL_DIR, "*.png")))
    files += sorted(glob.glob(os.path.join(CACHE_DIR, "*.png")))
    return [f for f in files if os.path.getsize(f) > 10_000]


def pick(n: int = 0) -> bytes:
    """n — nechanchi post (arxiv uzunligi). Rasmlar navbat bilan aylanadi."""
    files = available()
    if not files:
        _ensure_cached()
        files = available()
    if not files:
        print("[pool] rasm topilmadi — plakat illyustratsiyasiz chiqadi")
        return None
    path = files[n % len(files)]
    print(f"[pool] tanlandi: {os.path.basename(path)} ({n % len(files) + 1}/{len(files)})")
    with open(path, "rb") as f:
        return f.read()
