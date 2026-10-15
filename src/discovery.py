from datetime import datetime, timezone
from urllib.parse import urlsplit
from src.validation import normalize_url


def discover(industry: str, location: str, keywords: str, limit: int, provider=None) -> list[dict]:
    if not location.strip() or not industry.strip():
        raise ValueError('Enter an industry and location')
    if not 1 <= limit <= 30:
        raise ValueError('Result limit must be between 1 and 30')
    category = 'businesses' if industry == 'All types of businesses' else industry.strip()
    query = ' '.join([category, 'in', location.strip(), keywords.strip()]).strip()
    if provider is None:
        from ddgs import DDGS
        provider = DDGS(timeout=10).text
    try:
        hits = list(provider(query, max_results=limit))[:limit]
    except Exception as exc:
        raise RuntimeError('Search provider unavailable. Try a narrower query or retry later.') from exc
    rows, seen = [], set()
    for hit in hits:
        try:
            url = normalize_url(hit.get('href', ''))
        except (ValueError, UnicodeError):
            continue
        host = urlsplit(url).hostname.removeprefix('www.')
        if host in seen:
            continue
        seen.add(host)
        rows.append(dict(search_title=hit.get('title', ''), website_url=url,
                         search_snippet=hit.get('body', ''), search_query=query,
                         discovered_at=datetime.now(timezone.utc).isoformat(),
                         inspection_status='Not inspected', opportunity_score=None))
    return rows
