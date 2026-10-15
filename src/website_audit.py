"""Bounded homepage inspection; connections pin a validated public IP."""
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import urllib3
from bs4 import BeautifulSoup
from src.validation import normalize_url, public_destination
from src.scoring import score_findings

AGENT = 'BusinessDiscovery/1.0'
MAX_BYTES = 1_000_000


def fetch(url: str, redirect_check=None) -> tuple[int, str, bytes, str]:
    deadline = time.monotonic() + 20
    for _ in range(5):
        url = normalize_url(url)
        scheme, host, port, ip = public_destination(url)
        p = urlsplit(url)
        cls = urllib3.HTTPSConnectionPool if scheme == 'https' else urllib3.HTTPConnectionPool
        tls = dict(server_hostname=host, assert_hostname=host, cert_reqs='CERT_REQUIRED') if scheme == 'https' else {}
        pool = cls(ip, port=port, **tls)
        response = None
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Request time limit reached')
            response = pool.urlopen('GET', p.path + ('?' + p.query if p.query else ''),
                                    headers={'Host': p.netloc, 'User-Agent': AGENT},
                                    redirect=False, retries=False, preload_content=False,
                                    timeout=urllib3.Timeout(connect=min(5, remaining), read=min(5, remaining)))
            if response.status in (301, 302, 303, 307, 308):
                if not response.headers.get('Location'):
                    raise ValueError('Redirect has no destination')
                url = urljoin(url, response.headers['Location'])
                if redirect_check is not None:
                    redirect_check(url)
                continue
            chunks, size = [], 0
            for chunk in response.stream(16384, decode_content=True):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Response exceeds size limit')
                if time.monotonic() > deadline:
                    raise TimeoutError('Request time limit reached')
                chunks.append(chunk)
            return response.status, response.headers.get('Content-Type', ''), b''.join(chunks), url
        finally:
            if response is not None:
                response.close()
            pool.close()
    raise ValueError('Too many redirects')


def robots_allowed(url: str) -> bool:
    p = urlsplit(url)
    status, _, body, final = fetch(f'{p.scheme}://{p.netloc}/robots.txt')
    if urlsplit(final).netloc != p.netloc:
        raise ValueError('Robots redirected to another host; review manually')
    if status == 404:
        return True
    if status != 200:
        raise ValueError('Robots access could not be established')
    parser = RobotFileParser()
    parser.parse(body.decode('utf-8', errors='replace').splitlines())
    delay = parser.crawl_delay(AGENT)
    if delay and delay > 1:
        raise ValueError('Site requests a longer crawl delay; review manually')
    return parser.can_fetch(AGENT, url)


def parse_html(body: bytes, url: str) -> dict:
    soup = BeautifulSoup(body, 'html.parser')
    title, h1 = soup.find('title'), soup.find('h1')
    meta = soup.find('meta', attrs={'name': re.compile('^description$', re.I)})
    links = [a for a in soup.find_all('a', href=True)
             if re.search(r'contact|reach us|get in touch', a.get_text(' ', strip=True) + ' ' + a['href'], re.I)]
    contact = []
    for a in links:
        try:
            contact.append(normalize_url(urljoin(url, a['href'])))
        except (ValueError, UnicodeError):
            pass
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(' ', strip=True)
    terms = sorted(set(re.findall(r'\b(?:services?|products?|solutions?|shop|menu|appointments?|consulting)\b', text, re.I)))
    return dict(page_title=title.get_text(' ', strip=True)[:500] if title else '',
                meta_description=str(meta.get('content', '')).strip()[:1000] if meta else '',
                h1=h1.get_text(' ', strip=True)[:500] if h1 else '',
                https=urlsplit(url).scheme == 'https', contact_signal=bool(contact),
                service_signal=bool(terms), contact_links=' | '.join(contact[:5]),
                service_terms=', '.join(terms), final_url=url)


def inspect(url: str) -> dict:
    result = dict(inspection_status='Unavailable', opportunity_score=None, observed_issues='',
                  evidence_notes='', http_status=None)
    try:
        p = urlsplit(normalize_url(url))
        homepage = f'{p.scheme}://{p.netloc}/'
        if not robots_allowed(homepage):
            result.update(inspection_status='Blocked by robots', evidence_notes='Homepage inspection disallowed')
            return result
        time.sleep(1)
        # Check each redirect target's robots policy before its page is requested.
        status, content_type, body, final = fetch_homepage(homepage)
        result['http_status'] = status
        if status != 200:
            raise ValueError(f'Homepage returned HTTP {status}')
        if 'text/html' not in content_type.lower() and 'application/xhtml+xml' not in content_type.lower():
            result.update(inspection_status='Non-HTML', evidence_notes='Response is not HTML')
            return result
        result.update(parse_html(body, final), inspection_status='Inspected')
        score, reasons = score_findings(result)
        result.update(opportunity_score=score, observed_issues='; '.join(reasons),
                      evidence_notes='Homepage HTML only. Missing signals require browser verification.')
    except Exception as exc:
        result['evidence_notes'] = f'{type(exc).__name__}: {str(exc)[:250]}'
    return result


def fetch_homepage(url: str):
    def check(target):
        if not robots_allowed(target):
            raise ValueError('Redirected homepage disallowed by robots')
        time.sleep(1)
    return fetch(url, redirect_check=check)
