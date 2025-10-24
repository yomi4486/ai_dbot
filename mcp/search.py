import os
import requests
from typing import List, Dict

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

class SerpApiError(RuntimeError):
    pass

def serpapi_search(query: str, num: int = 3, timeout: int = 15) -> List[Dict]:
    """Perform a SerpAPI search and return simplified organic results.

    Requires SERPAPI_KEY in environment. Returns list of {title, link, snippet}.
    """
    if not SERPAPI_KEY:
        raise SerpApiError("SERPAPI_KEY not set in environment")
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num,
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=timeout)
    print(resp)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("organic_results", [])[:num]:
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet") or item.get("rich_snippet", {}).get("top", {}).get("text"),
        })
    return results
