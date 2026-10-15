"""Apollo decision-maker search. No enrichment or outreach is triggered."""
import json
from urllib.parse import urlencode
import urllib3

ENDPOINT = 'https://api.apollo.io/api/v1/mixed_people/api_search'


def search_people(api_key, titles, location, keywords='', page=1, transport=None):
    if not api_key.strip():
        raise ValueError('Configure APOLLO_API_KEY in local secrets first')
    if not titles or not location.strip() or not 1 <= page <= 500:
        raise ValueError('Titles, company location and a valid page are required')
    params = [('person_titles[]', t.strip()) for t in titles if t.strip()]
    params += [('organization_locations[]', location), ('q_keywords', keywords), ('page', page), ('per_page', 25)]
    http = transport or urllib3.PoolManager()
    response = None
    try:
        response = http.request('POST', ENDPOINT + '?' + urlencode(params), headers={'x-api-key': api_key, 'Accept': 'application/json'}, redirect=False, retries=False, preload_content=False, timeout=urllib3.Timeout(connect=5, read=20))
        if response.status != 200:
            hints = {401: 'API key rejected', 403: 'API access unavailable for this account or key', 429: 'Rate limited; retry later'}
            raise RuntimeError(hints.get(response.status, f'Apollo request failed (HTTP {response.status})'))
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise RuntimeError('Apollo response exceeds size limit')
        body = json.loads(payload)
        rows = []
        for person in body.get('people', [])[:25]:
            org = person.get('organization') or {}
            rows.append({'apollo_id': person.get('id', ''), 'first_name': person.get('first_name', ''), 'last_name': person.get('last_name_obfuscated', ''), 'title': person.get('title', ''), 'company': org.get('name', ''), 'company_domain': org.get('primary_domain', ''), 'email_available': person.get('has_email', False), 'phone_available': person.get('has_direct_phone', False), 'contact_access': 'Separate enrichment required'})
        return rows, body.get('total_entries', len(rows))
    except (urllib3.exceptions.HTTPError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError('Apollo could not be reached or returned invalid data; retry later') from exc
    finally:
        if response is not None:
            response.close()
        if transport is None:
            http.clear()
