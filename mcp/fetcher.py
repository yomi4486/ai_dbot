import os
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai_dbot/1.0)"}

def fetch_text_from_url(url: str, timeout: int = 10) -> Dict[str, Optional[str]]:
    """Fetch a URL and extract main textual content simply.

    Returns dict with keys: url, text, error
    """
    try:
        # honor global network-disable setting via env var
        if os.getenv("DISABLE_NETWORK", "").lower() in ("1", "true", "yes"):
            return {"url": url, "text": None, "error": "network disabled by configuration"}
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        return {"url": url, "text": None, "error": str(e)}
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        # Prefer <article>
        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            paragraphs = soup.find_all("p")
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        if text and len(text) > 20000:
            text = text[:20000]
        return {"url": url, "text": text, "error": None}
    except Exception as e:
        return {"url": url, "text": None, "error": str(e)}
