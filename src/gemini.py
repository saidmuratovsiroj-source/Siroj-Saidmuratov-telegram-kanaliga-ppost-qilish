"""Gemini API — matn (Google Search grounding bilan) va rasm generatsiyasi."""
import base64
import json
import re
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class Gemini:
    def __init__(self, api_key: str):
        self.key = api_key

    def _post(self, model: str, body: dict) -> dict:
        r = requests.post(
            BASE.format(model=model),
            headers={"x-goog-api-key": self.key, "Content-Type": "application/json"},
            json=body, timeout=180,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Gemini {model} xato {r.status_code}: {r.text[:500]}")
        return r.json()

    # ---------- matn ----------
    def text(self, model: str, prompt: str, system: str = None,
             search: bool = False, json_out: bool = False, temperature: float = 0.8) -> str:
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if search:
            body["tools"] = [{"google_search": {}}]
        elif json_out:
            # grounding va JSON rejimi birga ishlamaydi — shuning uchun faqat search bo'lmasa
            body["generationConfig"]["responseMimeType"] = "application/json"

        data = self._post(model, body)
        cands = data.get("candidates") or []
        if not cands:
            raise RuntimeError(f"Gemini bo'sh javob qaytardi: {json.dumps(data)[:400]}")
        parts = cands[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()

    def json(self, model: str, prompt: str, system: str = None,
             search: bool = False, temperature: float = 0.8) -> dict:
        raw = self.text(model, prompt, system=system, search=search,
                        json_out=not search, temperature=temperature)
        return _parse_json(raw)

    # ---------- rasm ----------
    def image(self, model: str, prompt: str) -> bytes:
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        }
        data = self._post(model, body)
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])
        raise RuntimeError(f"Rasm qaytmadi: {json.dumps(data)[:400]}")


def _parse_json(raw: str) -> dict:
    """Model ba'zan ```json ... ``` ichida qaytaradi — tozalaymiz."""
    s = raw.strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.S)
    if m:
        s = m.group(1)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1:
        s = s[start:end + 1]
    return json.loads(s)
