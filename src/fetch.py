
from __future__ import annotations
import requests
import xml.etree.ElementTree as ET
import urllib.parse as up

def _build_google_news_rss_url(query: str, hl: str = "pt-BR", ceid: str = "BR:pt-419") -> str:
    q = up.quote(query, safe="()\"' :")
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&ceid={ceid}"

def fetch_news(query: str, max_items: int = 15, hl: str = "pt-BR", ceid: str = "BR:pt-419") -> list[dict]:
    url = _build_google_news_rss_url(query, hl=hl, ceid=ceid)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item")[:max_items]:
            items.append({
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "description": (item.findtext("description") or "").strip(),
                "pubDate": (item.findtext("pubDate") or "").strip(),
            })
        return items
    except Exception:
        return []