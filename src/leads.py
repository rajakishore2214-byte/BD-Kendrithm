"""Lead normalization, local CRM storage, and outreach eligibility."""
from contextlib import contextmanager
import csv
import io
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, quote
from src.validation import normalize_url

AREAS = ['Chennai, Tamil Nadu', 'Cheyyar, Tiruvannamalai, Tamil Nadu']
NICHES = {
    'Interior designers': ('interior designers', 'Project portfolio, consultation enquiries, service-area pages', 'Owner, Founder, Principal Designer'),
    'Laminate sellers': ('laminate dealers', 'Product catalogue, brand ranges, contractor enquiries', 'Owner, Sales Manager, Director'),
    'Veneer sellers': ('veneer dealers', 'Finish samples, catalogue enquiries, designer partnerships', 'Owner, Sales Manager, Director'),
    'Louver sellers': ('louvers dealers', 'Product applications, installation examples, quote requests', 'Owner, Sales Manager, Director'),
    'Plywood stores': ('plywood dealers', 'Brand and grade catalogue, directions, contractor enquiries', 'Owner, Sales Manager, Director'),
    'Education': ('training institutes', 'Course and admission pages, enquiry tracking, genuine outcomes', 'Founder, Director, Admissions Manager'),
    'Catering services': ('catering services', 'Menus, event capacity, tasting and quotation enquiries', 'Owner, Founder, Operations Manager'),
    'Wedding venues / open gardens': ('outdoor wedding venues', 'Capacity, amenities, event gallery, site visits and availability enquiries', 'Owner, General Manager, Sales Manager'),
}
STATUSES = ['New', 'Verified', 'Called - no answer', 'Callback requested', 'Interested', 'Meeting booked', 'Won', 'Not interested', 'Do not contact']
WEBSITE = ['Unknown', 'No website listed', 'No website verified', 'Website present']
FIELDS = ['id', 'business_name', 'niche', 'area', 'address', 'phone', 'phone_source_url', 'whatsapp', 'whatsapp_source_url', 'website_url', 'website_status', 'profile_url', 'source_url', 'source_type', 'source_record_id', 'contact_name', 'contact_title', 'status', 'call_permission', 'follow_up', 'notes', 'updated_at']
DB = Path(__file__).resolve().parents[1] / 'data' / 'leads.sqlite3'


def clean_phone(value):
    value = str(value or '').strip().lstrip("'")
    if not value:
        return ''
    if re.search(r'[^+\d\s().-]', value):
        raise ValueError('Phone must contain only digits and common phone punctuation')
    digits = re.sub(r'\D', '', value)
    if not 7 <= len(digits) <= 15:
        raise ValueError('Phone must contain 7 to 15 digits, including country code where available')
    return ('+' if value.startswith('+') else '') + digits


def safe_url(value):
    return normalize_url(str(value).strip()) if value else ''


def normalize_lead(raw):
    row = {key: str(raw.get(key, '') or '').strip() for key in FIELDS}
    if not row['business_name']:
        raise ValueError('Business name is required')
    if row['niche'] not in NICHES:
        raise ValueError('Choose a supported niche')
    if not row['area']:
        raise ValueError('Area is required')
    row['website_status'] = row['website_status'] or 'Unknown'
    if row['website_status'] not in WEBSITE:
        raise ValueError('Invalid website status')
    for key in ['website_url', 'profile_url', 'source_url', 'phone_source_url', 'whatsapp_source_url']:
        row[key] = safe_url(row[key])
    if not row['source_url']:
        raise ValueError('A source URL is required for every lead')
    row['phone'], row['whatsapp'] = clean_phone(row['phone']), clean_phone(row['whatsapp'])
    if row['phone'] and not row['phone_source_url']:
        raise ValueError('Provide the public business phone source URL')
    if row['whatsapp'] and not row['whatsapp_source_url']:
        raise ValueError('WhatsApp needs its own explicitly published or confirmed source URL')
    if row['website_url']:
        row['website_status'] = 'Website present'
    if row['website_status'] == 'No website verified' and not row['notes']:
        raise ValueError('Record how the lack of a website was verified in notes')
    row['status'] = row['status'] or 'New'
    if row['status'] not in STATUSES:
        raise ValueError('Invalid call status')
    row['call_permission'] = row['call_permission'] or 'Not reviewed'
    if row['call_permission'] not in ['Not reviewed', 'Cleared for business call', 'Do not contact']:
        raise ValueError('Invalid call permission')
    if row['status'] == 'Do not contact' or row['call_permission'] == 'Do not contact':
        row['status'] = row['call_permission'] = 'Do not contact'
    row['id'] = row['id'] or str(uuid.uuid4())
    row['source_type'] = row['source_type'] or 'Manual research'
    row['updated_at'] = datetime.now(timezone.utc).isoformat()
    if any(len(v) > 10000 for v in row.values()):
        raise ValueError('A field exceeds the 10,000 character limit')
    return row


@contextmanager
def connection(path=DB):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.execute('CREATE TABLE IF NOT EXISTS leads (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    try:
        with con:
            yield con
    finally:
        con.close()


def list_leads(path=DB):
    with connection(path) as con:
        return [json.loads(r[0]) for r in con.execute('SELECT payload FROM leads ORDER BY rowid DESC')]


def save_lead(raw, path=DB):
    row = normalize_lead(raw)
    with connection(path) as con:
        existing = [json.loads(r[0]) for r in con.execute('SELECT payload FROM leads')]
        for old in existing:
            same = old['id'] == row['id'] or (old['business_name'].casefold() == row['business_name'].casefold() and old['area'].casefold() == row['area'].casefold() and old['address'].casefold() == row['address'].casefold())
            if same:
                if row['id'] != old['id']:
                    for field in ['status', 'call_permission', 'follow_up', 'contact_name', 'contact_title']:
                        row[field] = old[field]
                    row['notes'] = '\n'.join(dict.fromkeys(n for n in [old['notes'], row['notes']] if n))
                    for field in ['phone', 'phone_source_url', 'whatsapp', 'whatsapp_source_url', 'website_url', 'profile_url']:
                        row[field] = row[field] or old[field]
                    if row['website_status'] == 'Unknown':
                        row['website_status'] = old['website_status']
                row['id'] = old['id']
                if old['status'] == 'Do not contact' or old['call_permission'] == 'Do not contact':
                    row['status'] = row['call_permission'] = 'Do not contact'
                break
        # Suppression follows a telephone number across records and reimports.
        suppressed = {p for old in existing if old['status'] == 'Do not contact' for p in [old['phone'], old['whatsapp']] if p}
        if suppressed.intersection({row['phone'], row['whatsapp']} - {''}):
            row['status'] = row['call_permission'] = 'Do not contact'
        con.execute('INSERT OR REPLACE INTO leads VALUES (?, ?)', (row['id'], json.dumps(row)))
        if row['status'] == 'Do not contact':
            numbers = {row['phone'], row['whatsapp']} - {''}
            for old in existing:
                if numbers.intersection({old['phone'], old['whatsapp']}):
                    old['status'] = old['call_permission'] = 'Do not contact'
                    con.execute('UPDATE leads SET payload=? WHERE id=?', (json.dumps(old), old['id']))
    return row


def call_ready(row):
    return bool(row['phone'] and row['phone_source_url'] and row['call_permission'] == 'Cleared for business call' and row['status'] not in ['Do not contact', 'Not interested', 'Won'] and row['website_status'] in ['No website listed', 'No website verified'])


def research_links(niche, area):
    query = NICHES[niche][0] + ' in ' + area
    return {'Google Maps': 'https://www.google.com/maps/search/?api=1&query=' + quote(query), 'Google Search': 'https://www.google.com/search?q=' + quote(query)}


def lead_csv(rows):
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=FIELDS, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("'" + str(row.get(k, '')) if str(row.get(k, '')).lstrip().startswith(('=', '+', '-', '@')) else row.get(k, '')) for k in FIELDS})
    return buf.getvalue().encode('utf-8-sig')


def preview_import(data):
    if len(data) > 2_000_000:
        raise ValueError('CSV must be smaller than 2 MB')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    if not {'business_name', 'niche', 'area', 'source_url'}.issubset(reader.fieldnames or []):
        raise ValueError('CSV requires business_name, niche, area and source_url columns')
    valid, errors = [], []
    for index, raw in enumerate(reader, 2):
        if index > 501:
            raise ValueError('Import at most 500 records at a time')
        try:
            # Imports never restore ids or permissions from another database.
            raw.pop('id', None)
            if raw.get('call_permission') != 'Do not contact':
                raw['call_permission'] = 'Not reviewed'
            valid.append(normalize_lead(raw))
        except (ValueError, TypeError) as exc:
            errors.append(f'Row {index}: {exc}')
    return valid, errors


