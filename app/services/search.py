"""
Lightweight web-search helper.

Default: DuckDuckGo (no key).  
Optional: SerpAPI → set SERP_API_KEY in env, otomatis switch.

Functions
─────────
search_web(q: str, k=5)  -> List[str]   # list of result snippets/URLs
"""

from __future__ import annotations

import os
import requests
from typing import List

from app.services.logger import logger

_SERP_KEY = os.getenv("SERP_API_KEY")


# ──────────────────── public helper ────────────────────
def search_web(query: str, k: int = 5) -> List[str]:
    if _SERP_KEY:
        return _search_serpapi(query, k)
    return _search_duckduckgo(query, k)


# ─────────────────── internal engines ──────────────────
def _search_duckduckgo(query: str, k: int) -> List[str]:
    url = "https://duckduckgo.com/html/"
    resp = requests.post(url, data={"q": query}, timeout=8)
    resp.raise_for_status()

    # Sangat ringkas: ambil <a class="result__a"…> titles
    import re, html
    links = re.findall(r'class=\"result__a\"[^>]*href=\"([^\"]+)\"', resp.text)
    results = [html.unescape(l) for l in links][:k]
    logger.debug("DDG results", total=len(results))
    return results


def _search_serpapi(query: str, k: int) -> List[str]:
    params = {"api_key": _SERP_KEY, "q": query, "num": k, "engine": "google"}
    resp = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
    results = [item["link"] for item in resp.get("organic_results", [])][:k]
    logger.debug("SerpAPI results", total=len(results))
    return results
