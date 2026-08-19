"""Telegram Bot API bilan ishlash — minimal, kutubxonasiz."""
import time
import requests

API = "https://api.telegram.org/bot{token}/{method}"


class Telegram:
    def __init__(self, token: str):
        self.token = token
        self._offset = None

    def _call(self, method: str, **kwargs):
        r = requests.post(API.format(token=self.token, method=method), timeout=60, **kwargs)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} xato: {data}")
        return data["result"]

    # --- tekshiruv ---
    def me(self):
        return self._call("getMe")

    def chat(self, chat_id):
        return self._call("getChat", json={"chat_id": chat_id})

    def can_post(self, chat_id) -> bool:
        """Bot kanalga post yoza oladimi?"""
        me = self.me()
        m = self._call("getChatMember", json={"chat_id": chat_id, "user_id": me["id"]})
        return m.get("status") == "administrator" and m.get("can_post_messages", False)

    # --- yuborish ---
    def send_message(self, chat_id, text, buttons=None, parse_mode="HTML"):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode,
                   "disable_web_page_preview": True}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        return self._call("sendMessage", json=payload)

    def send_photo(self, chat_id, image_bytes, caption, buttons=None, parse_mode="HTML"):
        payload = {"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode}
        if buttons:
            import json as _json
            payload["reply_markup"] = _json.dumps({"inline_keyboard": buttons})
        files = {"photo": ("post.png", image_bytes, "image/png")}
        return self._call("sendPhoto", data=payload, files=files)

    def send_voice(self, chat_id, data, kind="voice", caption=None):
        """kind: 'voice' (OGG/Opus) yoki 'audio' (MP3)."""
        payload = {"chat_id": chat_id}
        if caption:
            payload["caption"] = caption
            payload["parse_mode"] = "HTML"
        if kind == "voice":
            files = {"voice": ("post.ogg", data, "audio/ogg")}
            return self._call("sendVoice", data=payload, files=files)
        payload["title"] = "Post"
        files = {"audio": ("post.mp3", data, "audio/mpeg")}
        return self._call("sendAudio", data=payload, files=files)

    def edit_caption(self, chat_id, message_id, caption, parse_mode="HTML"):
        return self._call("editMessageCaption", json={
            "chat_id": chat_id, "message_id": message_id,
            "caption": caption, "parse_mode": parse_mode, "reply_markup": {"inline_keyboard": []},
        })

    def answer_callback(self, callback_id, text=""):
        return self._call("answerCallbackQuery", json={"callback_query_id": callback_id, "text": text})

    # --- qabul qilish ---
    def wait_for_callback(self, expected_prefix: str, timeout_sec: int):
        """Tugma bosilishini kutadi. Qaytaradi: (data, callback_id) yoki (None, None)."""
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                updates = self._call("getUpdates", json={
                    "offset": self._offset, "timeout": 50,
                    "allowed_updates": ["callback_query", "message"],
                })
            except Exception as e:
                print(f"[telegram] getUpdates xato: {e}")
                time.sleep(5)
                continue
            for u in updates:
                self._offset = u["update_id"] + 1
                cq = u.get("callback_query")
                if cq and cq.get("data", "").startswith(expected_prefix):
                    return cq["data"], cq["id"]
        return None, None

    def drain(self):
        """Eski update'larni tozalaydi (oldingi ishga tushishdan qolganlari)."""
        try:
            updates = self._call("getUpdates", json={"timeout": 0})
            if updates:
                self._offset = updates[-1]["update_id"] + 1
        except Exception as e:
            print(f"[telegram] drain xato: {e}")
