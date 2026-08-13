"""Chiqarilgan mavzular arxivi — takrorlanishning oldini oladi."""
import json
import os
from datetime import datetime


class Archive:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.items = []
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self.items = json.load(f)
            except Exception as e:
                print(f"[archive] o'qishda xato ({e}), bo'sh arxivdan boshlaymiz")

    def recent(self, n: int = 40):
        return self.items[-n:]

    def titles(self, n: int = 40):
        return [it["title"] for it in self.recent(n)]

    def urls(self):
        """Ishlatilgan manba maqolalari — takrorlanmaslik uchun."""
        return {it.get("source_url") for it in self.items if it.get("source_url")}

    def next_level(self, levels):
        """Oxirgi postdan keyingi darajani qaytaradi (navbat bilan)."""
        if not self.items:
            return levels[0]
        last = self.items[-1].get("level")
        if last not in levels:
            return levels[0]
        return levels[(levels.index(last) + 1) % len(levels)]

    def add(self, title: str, level: str, summary: str = "", source_url: str = ""):
        self.items.append({
            "date": datetime.now().isoformat(timespec="seconds"),
            "title": title, "level": level,
            "summary": summary, "source_url": source_url,
        })
        self.save()

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)
