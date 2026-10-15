"""Public destination validation for every network request."""
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    if any(ord(c) < 33 for c in url) or '\\' in url:
        raise ValueError('Invalid URL characters')
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('Only public HTTP/HTTPS URLs without credentials are accepted')
    if p.port not in (None, 80, 443):
        raise ValueError('Only standard web ports are accepted')
    host = p.hostname.rstrip('.').encode('idna').decode('ascii').lower()
    if host == 'localhost' or host.endswith(('.local', '.internal', '.localhost')):
        raise ValueError('Internal destinations are blocked')
    authority = f'[{host}]' if ':' in host else host
    if p.port:
        authority += f':{p.port}'
    return urlunsplit((p.scheme, authority, p.path or '/', p.query, ''))


def public_destination(url: str) -> tuple[str, str, int, str]:
    p = urlsplit(normalize_url(url))
    port = p.port or (443 if p.scheme == 'https' else 80)
    addresses = {entry[4][0] for entry in socket.getaddrinfo(p.hostname, port, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('Non-public destination address blocked')
    return p.scheme, p.hostname, port, sorted(addresses)[0]
