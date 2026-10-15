import csv
import io
import unittest
from datetime import date
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
from src.outreach import COLUMNS, MESSAGE, filter_contacts, render_html


def data(**overrides):
    row = dict(business_name='Studio & Sons <design>', phone='9000000001', website_status='No website verified', website_evidence_url='https://example.com/check', social_status='Inactive verified', social_evidence_url='https://example.com/profile', social_last_post_date='2026-06-01', checked_at='2026-10-15')
    row.update(overrides)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue().encode()


class OutreachTests(unittest.TestCase):
    def test_html_message_roundtrip_and_escape(self):
        rows, excluded = filter_contacts(data(), today=date(2026, 10, 15))
        self.assertFalse(excluded)
        html = render_html(rows)
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual([h.text for h in soup.select('th')], ['Business Name', 'Phone Number', 'WhatsApp Button'])
        self.assertEqual(soup.select('td')[0].text, 'Studio & Sons <design>')
        link = soup.select_one('a')
        self.assertEqual(urlsplit(link['href']).path, '/919000000001')
        self.assertEqual(parse_qs(urlsplit(link['href']).query)['text'][0], MESSAGE.replace('{Business Name}', rows[0]['business_name']))
        self.assertNotIn('<design>', html)

    def test_unknown_active_stale_and_suppressed_are_excluded(self):
        for overrides in [dict(website_status='No website listed'), dict(website_url='https://example.com'), dict(social_status='Unknown'), dict(social_last_post_date='2026-10-01'), dict(checked_at='2026-08-01'), dict(status='Do not contact')]:
            with self.subTest(overrides=overrides):
                rows, excluded = filter_contacts(data(**overrides), today=date(2026,10,15))
                self.assertEqual(rows, [])
                self.assertEqual(len(excluded), 1)
        rows, excluded = filter_contacts(data(), today=date(2026,10,15), suppressed=['+91 90000 00001'])
        self.assertFalse(rows)
        self.assertTrue(excluded)

    def test_absent_social_and_published_whatsapp(self):
        rows, excluded = filter_contacts(data(social_status='No profiles verified', social_last_post_date='', whatsapp='+919000000009'), today=date(2026,10,15))
        self.assertFalse(excluded)
        self.assertEqual(rows[0]['recipient'], '919000000009')
