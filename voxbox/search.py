"""Web search / retrieval layer.

Uses DuckDuckGo's HTML endpoint (no API key required). Best-effort: if the
search fails or returns nothing, callers fall back to a knowledge-only answer
with an uncertainty note. Search results are treated as untrusted external
data (prompt-injection isolation happens in prompt.py).
"""
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config
from .logging import log_event, log_error

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def _fetch(url: str, timeout: float) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def search(query: str, max_results: int = None) -> list:
    """Search the web. Returns a list of {title, url, snippet} dicts."""
    if not config.ENABLE_WEB_SEARCH:
        return []
    max_results = max_results or config.SEARCH_RESULTS
    q = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    start = time.time()
    try:
        page = _fetch(url, config.SEARCH_TIMEOUT)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        log_error("search failed", e, query_len=len(query))
        return []
    results = []
    for block in re.findall(r'<div class="result[^"]*"[^>]*>(.*?)</div>\s*</div>', page, re.DOTALL):
        if len(results) >= max_results:
            break
        title_m = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        snip_m = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not title_m:
            continue
        raw_url = html.unescape(title_m.group(1))
        url_m = re.search(r"uddg=([^&]+)", raw_url)
        target = urllib.parse.unquote(url_m.group(1)) if url_m else raw_url
        title = _clean(title_m.group(2))
        snippet = _clean(snip_m.group(1)) if snip_m else ""
        if title:
            results.append({"title": title[:200], "url": target[:500], "snippet": snippet[:400]})
    log_event("search_ok", query_len=len(query), results=len(results), latency=round(time.time() - start, 2))
    return results


def format_results(results: list) -> str:
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']} - {r['url']}")
        if r.get("snippet"):
            lines.append(f"    {r['snippet']}")
    return "\n".join(lines)