
import re
import html
from bs4 import BeautifulSoup
from unidecode import unidecode

TAG_RE = re.compile(r"<[^>]+>")

def strip_html_keep_text(s: str) -> str:
    if not s:
        return ""
    try:
        text = BeautifulSoup(s, "lxml").get_text(separator=" ")
    except Exception:
        text = TAG_RE.sub(" ", s)
    return html.unescape(text)

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = unidecode(s)
    s = re.sub(r"\s+", " ", s)
    return s