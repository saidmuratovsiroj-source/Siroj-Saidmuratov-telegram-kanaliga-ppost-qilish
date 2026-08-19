"""ElevenLabs ovozi — post ostiga ovozli xabar.

Siroj tanlagan: George ovozi + eleven_v3 modeli.

Telegram "voice message" (ovozli xabar) uchun OGG/Opus kerak. ElevenLabs to'g'ridan
to'g'ri opus qaytara oladi, uni ffmpeg bilan OGG konteynerga o'raymiz. ffmpeg bo'lmasa
MP3 sifatida audio fayl yuboriladi — baribir ishlaydi, faqat ko'rinishi boshqacha.
"""
import os
import shutil
import subprocess
import tempfile

import requests
import config

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"


def enabled() -> bool:
    return bool(config.ELEVEN_API_KEY) and config.VOICE_ENABLED


def synth(text: str, fmt: str = "opus_48000_128") -> bytes:
    """Matndan ovoz qaytaradi. opus_48000_128 -> tayyor OGG konteyner."""
    r = requests.post(
        API.format(voice=config.ELEVEN_VOICE_ID),
        params={"output_format": fmt},
        headers={"xi-api-key": config.ELEVEN_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "model_id": config.ELEVEN_MODEL,
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 0.95}},
        timeout=180)
    if r.status_code >= 400:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    return r.content


def to_voice_ogg(mp3: bytes):
    """MP3 -> OGG/Opus. ffmpeg bo'lmasa None qaytaradi."""
    if not shutil.which("ffmpeg"):
        return None
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "a.mp3"), os.path.join(d, "a.ogg")
        with open(src, "wb") as f:
            f.write(mp3)
        p = subprocess.run(
            ["ffmpeg", "-y", "-i", src, "-c:a", "libopus", "-b:a", "48k",
             "-ar", "48000", "-ac", "1", dst],
            capture_output=True)
        if p.returncode != 0 or not os.path.exists(dst):
            print(f"[voice] ffmpeg xato: {p.stderr[-200:]!r}")
            return None
        with open(dst, "rb") as f:
            return f.read()


def make(text: str):
    """(bytes, 'voice'|'audio') yoki (None, None)."""
    if not enabled():
        return None, None
    text = (text or "").strip()
    if len(text) < 40:
        return None, None
    if len(text) > config.VOICE_MAX_CHARS:
        text = text[:config.VOICE_MAX_CHARS].rsplit(".", 1)[0] + "."
    # 1-yo'l: ElevenLabs o'zi OGG/Opus qaytaradi — ffmpeg kerak emas
    try:
        data = synth(text, "opus_48000_128")
        if data[:4] == b"OggS":
            print(f"[voice] ovozli xabar tayyor ({len(data)//1024} KB)")
            return data, "voice"
    except Exception as e:
        print(f"[voice] opus olinmadi ({e}) — mp3 ga o'tamiz")

    # 2-yo'l: MP3 + ffmpeg bo'lsa aylantiramiz, bo'lmasa audio fayl
    try:
        mp3 = synth(text, "mp3_44100_128")
    except Exception as e:
        print(f"[voice] ovoz yasalmadi: {e}")
        return None, None
    ogg = to_voice_ogg(mp3)
    if ogg:
        print(f"[voice] ovozli xabar tayyor ({len(ogg)//1024} KB)")
        return ogg, "voice"
    print(f"[voice] MP3 audio sifatida ({len(mp3)//1024} KB)")
    return mp3, "audio"
