"""Rasmiy manbalar — Claude Help Center.

Google Search grounding pullik bo'lgani uchun biz boshqa yo'ldan boramiz:
bot to'g'ridan-to'g'ri Anthropic'ning rasmiy yordam markazidan o'qiydi.

Bu qidiruvdan ishonchliroq: qidiruv tasodifiy blogga tushishi mumkin,
bu esa faqat rasmiy hujjatni o'qiydi. Va bepul.
"""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AiProBot/1.0)"}
ARTICLE_RE = re.compile(r"^https://support\.claude\.com/en/articles/\d+-")


def _get(url: str, timeout=30) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def list_articles(collections) -> list:
    """Berilgan bo'limlardagi barcha maqolalar ro'yxati: [{url, title, collection}]."""
    seen, out = set(), []
    for name, url in collections:
        try:
            soup = BeautifulSoup(_get(url), "html.parser")
        except Exception as e:
            print(f"[sources] {name} ochilmadi: {e}")
            continue
        for a in soup.select('a[href*="/articles/"]'):
            href = (a.get("href") or "").split("?")[0]
            if not ARTICLE_RE.match(href) or href in seen:
                continue
            title = a.get_text(" ", strip=True).split("\n")[0].strip()
            if not title or len(title) < 6:
                continue
            seen.add(href)
            out.append({"url": href, "title": title, "collection": name})
    print(f"[sources] {len(out)} ta maqola topildi")
    return out


def fetch_article(url: str, max_chars=9000) -> str:
    """Maqolaning toza matni."""
    soup = BeautifulSoup(_get(url), "html.parser")
    node = soup.find("article") or soup.find("main") or soup.body
    for bad in node.select("script, style, nav, footer, header"):
        bad.decompose()
    text = re.sub(r"\n{3,}", "\n\n", node.get_text("\n", strip=True))
    return text[:max_chars]
