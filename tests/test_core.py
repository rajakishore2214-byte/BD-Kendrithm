import csv
import io
import unittest
from unittest.mock import patch, Mock
from src.discovery import discover
from src.validation import normalize_url, public_destination
from src.scoring import score_findings
from src.website_audit import parse_html, inspect, fetch
from src.export import export_csv


class CoreTests(unittest.TestCase):
    def test_scoring(self):
        self.assertEqual(score_findings({'inspection_status': 'Inspected'})[0], 100)
        self.assertEqual(score_findings({'inspection_status': 'Unavailable'}), (None, []))
        full = parse_html(b'<title>A</title><meta name="description" content="B"><h1>C</h1><a href="/contact">Contact</a>services', 'https://example.com/')
        full['inspection_status'] = 'Inspected'
        self.assertEqual(score_findings(full), (0, []))

    def test_malformed_html(self):
        result = parse_html(b'<h1>Hello', 'http://example.com/')
        self.assertEqual(result['h1'], 'Hello')
        self.assertFalse(result['https'])
        self.assertEqual(result['page_title'], '')

    def test_invalid_urls(self):
        for url in ['file:///etc/passwd', 'https://localhost/', 'https://a.internal/', 'https://user:pass@example.com/', 'https://example.com:8000', 'https://example.com/\n']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_url(url)

    def test_private_dns(self):
        for address in ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1']:
            with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', (address, 80))]):
                with self.assertRaises(ValueError):
                    public_destination('http://example.com/')

    def test_search(self):
        self.assertEqual(discover('Dentists', 'Chennai', '', 5, provider=lambda *a, **k: []), [])
        with self.assertRaises(RuntimeError):
            discover('Dentists', 'Chennai', '', 5, provider=Mock(side_effect=TimeoutError()))
        hits = [{'href': 'https://example.com/a', 'title': 'A'}, {'href': 'https://www.example.com/b'}, {'href': 'javascript:bad'}]
        self.assertEqual(len(discover('Dentists', 'Chennai', '', 5, provider=lambda *a, **k: hits)), 1)

    @patch('src.website_audit.time.sleep')
    @patch('src.website_audit.robots_allowed', return_value=True)
    def test_inspection_failures(self, robots, sleep):
        with patch('src.website_audit.fetch_homepage', side_effect=TimeoutError('timed out')):
            self.assertIsNone(inspect('https://example.com')['opportunity_score'])
        with patch('src.website_audit.fetch_homepage', return_value=(200, 'application/pdf', b'pdf', 'https://example.com/')):
            self.assertEqual(inspect('https://example.com')['inspection_status'], 'Non-HTML')

    def test_unsafe_redirect(self):
        response = Mock(status=302, headers={'Location': 'http://127.0.0.1/'})
        pool = Mock()
        pool.urlopen.return_value = response
        with patch('src.website_audit.public_destination', side_effect=[('https', 'example.com', 443, '93.184.216.34'), ValueError('blocked')]), patch('urllib3.HTTPSConnectionPool', return_value=pool):
            with self.assertRaises(ValueError):
                fetch('https://example.com/')
            self.assertEqual(pool.urlopen.call_count, 1)

    def test_response_size_and_pinned_tls(self):
        response = Mock(status=200, headers={'Content-Type': 'text/html'})
        response.stream.return_value = [b'x' * 1_000_001]
        pool = Mock()
        pool.urlopen.return_value = response
        with patch('src.website_audit.public_destination', return_value=('https', 'example.com', 443, '93.184.216.34')), patch('urllib3.HTTPSConnectionPool', return_value=pool) as factory:
            with self.assertRaises(ValueError):
                fetch('https://example.com/')
            self.assertEqual(factory.call_args.args[0], '93.184.216.34')
            self.assertEqual(factory.call_args.kwargs['assert_hostname'], 'example.com')
            self.assertEqual(pool.urlopen.call_args.kwargs['headers']['Host'], 'example.com')

    def test_redirect_policy_checked_before_fetch(self):
        response = Mock(status=302, headers={'Location': 'https://other.example/'})
        pool = Mock()
        pool.urlopen.return_value = response
        check = Mock(side_effect=ValueError('disallowed'))
        with patch('src.website_audit.public_destination', return_value=('https', 'example.com', 443, '93.184.216.34')), patch('urllib3.HTTPSConnectionPool', return_value=pool):
            with self.assertRaises(ValueError):
                fetch('https://example.com/', redirect_check=check)
            self.assertEqual(pool.urlopen.call_count, 1)
            check.assert_called_once_with('https://other.example/')

    def test_csv(self):
        data = export_csv([{'search_title': '=SUM(1,2)', 'search_snippet': 'Chennai, "தமிழ்"'}])
        row = next(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
        self.assertEqual(row['search_title'], "'=SUM(1,2)")
        self.assertEqual(row['search_snippet'], 'Chennai, "தமிழ்"')


if __name__ == '__main__':
    unittest.main()
