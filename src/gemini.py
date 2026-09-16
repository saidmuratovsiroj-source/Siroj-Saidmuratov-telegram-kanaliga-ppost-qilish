"""Gemini API — matn va rasm generatsiyasi."""
import base64
import json
import re
import time
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRY_CODES = (429, 500, 502, 503, 504)

# Asosiy model band bo'lsa (503 "high demand") shu ro'yxat bo'yicha pastga
# tushamiz. Post chiqmay qolgandan ko'ra zaxira modelda chiqqani yaxshi.
FALLBACKS = {
    "gemini-3.5-flash": ["gemini-3.1-flash", "gemini-3.1-flash-lite"],
    "gemini-3.1-flash": ["gemini-3.1-flash-lite"],
}


class Gemini:
    def __init__(self, api_key: str):
        self.key = api_key

    def _once(self, model: str, body: dict, tries: int = 4):
        """(javob, xato) — bitta model bo'yicha urinadi."""
        last = None
        for attempt in range(1, tries + 1):
            try:
                r = requests.post(
                    BASE.format(model=model),
                    headers={"x-goog-api-key": self.key,
                             "Content-Type": "application/json"},
                    json=body, timeout=180,
                )
            except Exception as e:
                last = f"tarmoq xatosi: {type(e).__name__}"
                if attempt < tries:
                    time.sleep(5 * attempt)
                    continue
                break
            if r.status_code < 400:
                return r.json(), None
            last = f"{r.status_code}: {r.text[:300]}"
            if r.status_code in RETRY_CODES and attempt < tries:
                wait = 8 * attempt          # 8s, 16s, 24s — band model bo'shashiga vaqt
                print(f"[gemini] {model} {r.status_code} — {wait}s kutib qayta urinamiz")
                time.sleep(wait)
                continue
            break
        return None, last

    def _post(self, model: str, body: dict, tries: int = 4) -> dict:
        data, err = self._once(model, body, tries)
        if data is not None:
            return data
        for spare in FALLBACKS.get(model, []):
            print(f"[gemini] {model} javob bermadi ({err}) — {spare} ga o'tamiz")
            data, err2 = self._once(spare, body, tries=2)
            if data is not None:
                print(f"[gemini] {spare} ishladi")
                return data
            err = err2 or err
        raise RuntimeError(f"Gemini {model} xato {err}")

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
            body["generationConfig"]["responseMimeType"] = "application/json"

        data = self._post(model, body)
        cands = data.get("candidates") or []
        if not cands:
            raise RuntimeError(f"Gemini bo'sh javob qaytardi: {json.dumps(data)[:300]}")

        # MUHIM: Gemini 3 modellari "thought" (o'ylash) qismlarini ham qaytaradi.
        # Ularni qo'shib yuborsak JSON buziladi — shuning uchun faqat haqiqiy javob.
        parts = cands[0].get("content", {}).get("parts", [])
        real = [p.get("text", "") for p in parts
                if p.get("text") and not (p.get("thought") or p.get("thoughtSignature"))]
        if not real:  # hamma qism "thought" bo'lsa, baribir nimadir qaytaramiz
            real = [p.get("text", "") for p in parts if p.get("text")]
        return "".join(real).strip()

    def json(self, model: str, prompt: str, system: str = None,
             search: bool = False, temperature: float = 0.8, tries: int = 3) -> dict:
        strict = ("\n\nESLATMA: javobingda FAQAT JSON obyekti bo'lsin. "
                  "Izoh, sarlavha, ```json belgilari va boshqa matn qo'shma.")
        err = None
        for attempt in range(1, tries + 1):
            raw = self.text(model, prompt + (strict if attempt > 1 else ""),
                            system=system, json_out=not search, search=search,
                            temperature=temperature if attempt == 1 else 0.3)
            try:
                return _parse_json(raw)
            except Exception as e:
                err = e
                print(f"[gemini] JSON o'qilmadi ({attempt}/{tries}): {e}")
                print(f"[gemini] javob boshi: {raw[:200]!r}")
                time.sleep(2)
        raise RuntimeError(f"Gemini JSON qaytarmadi ({tries} urinish): {err}")

    # ---------- rasm ----------
    def image(self, model: str, prompt: str, refs=None) -> bytes:
        """refs — namuna rasmlar (bytes ro'yxati). Personaj o'xshashligi uchun."""
        parts = []
        for r in (refs or []):
            parts.append({"inlineData": {"mimeType": "image/png",
                                         "data": base64.b64encode(r).decode()}})
        parts.append({"text": prompt})
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        }
        data = self._post(model, body)
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])
        raise RuntimeError(f"Rasm qaytmadi: {json.dumps(data)[:300]}")


def _parse_json(raw: str) -> dict:
    """Matndan birinchi to'liq JSON obyektini ajratib oladi.

    Model oldiga izoh, orqasiga qo'shimcha matn qo'shsa ham ishlaydi.
    """
    s = raw.strip()

    m = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.S)
    if m:
        s = m.group(1).strip()

    # 1-usul: to'g'ridan-to'g'ri
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2-usul: birinchi "{" dan boshlab birinchi TO'LIQ obyektni o'qiymiz,
    # qolgan matnni e'tiborsiz qoldiramiz (raw_decode aynan shuni qiladi).
    dec = json.JSONDecoder()
    for i, ch in enumerate(s):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(s[i:])
            if isinstance(obj, dict) and obj:
                return obj
        except Exception:
            continue

    raise ValueError(f"JSON topilmadi. Javob boshi: {s[:200]!r}")
