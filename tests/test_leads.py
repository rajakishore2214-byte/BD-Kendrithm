import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from src.leads import normalize_lead, save_lead, list_leads, call_ready, lead_csv, preview_import
from src.apollo import search_people
from src.strategy import action_plan


def lead(**kwargs):
    return dict(business_name='Example Interior Studio', niche='Interior designers', area='Chennai, Tamil Nadu', source_url='https://example.com/contact', phone='+91 90000 00001', phone_source_url='https://example.com/contact', website_status='No website listed', **kwargs)


class LeadTests(unittest.TestCase):
    def test_unknown_is_not_no_website(self):
        row = lead()
        row.pop('website_status')
        self.assertEqual(normalize_lead(row)['website_status'], 'Unknown')
        row = normalize_lead(lead(call_permission='Cleared for business call'))
        self.assertTrue(call_ready(row))
        row['website_status'] = 'Unknown'
        self.assertFalse(call_ready(row))

    def test_whatsapp_requires_independent_evidence(self):
        with self.assertRaises(ValueError):
            normalize_lead(lead(whatsapp='+919000000001'))
        self.assertEqual(normalize_lead(lead())['whatsapp'], '')

    def test_verified_absence_requires_notes(self):
        raw = lead()
        raw['website_status'] = 'No website verified'
        with self.assertRaises(ValueError):
            normalize_lead(raw)

    def test_suppression_survives_duplicate_and_new_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'leads.db'
            saved = save_lead(lead(status='Do not contact'), path)
            again = save_lead(lead(status='New', call_permission='Cleared for business call'), path)
            self.assertEqual(saved['id'], again['id'])
            self.assertEqual(len(list_leads(path)), 1)
            other = lead(call_permission='Cleared for business call')
            other['business_name'] = 'Another branch'
            row = save_lead(other, path)
            self.assertEqual(row['status'], 'Do not contact')
            self.assertFalse(call_ready(row))

    def test_csv_round_trip_and_permission_reset(self):
        row = normalize_lead(lead(call_permission='Cleared for business call'))
        row['business_name'] = '=Business'
        valid, errors = preview_import(lead_csv([row]))
        self.assertFalse(errors)
        self.assertEqual(valid[0]['phone'], '+919000000001')
        self.assertTrue(valid[0]['business_name'].startswith("'="))
        self.assertEqual(valid[0]['call_permission'], 'Not reviewed')

    def test_csv_errors_do_not_become_records(self):
        valid, errors = preview_import(b'business_name,niche,area,source_url\nX,Invalid,Chennai,https://example.com\n')
        self.assertEqual(valid, [])
        self.assertEqual(len(errors), 1)

    def test_apollo_request_and_unavailable_contacts(self):
        response = Mock(status=200)
        response.read.return_value = b'{"people":[{"id":"1","first_name":"A","last_name_obfuscated":"B***","has_email":true,"organization":{"name":"Studio"}}]}'
        transport = Mock()
        transport.request.return_value = response
        rows, total = search_people('test-key', ['Owner'], 'Chennai', transport=transport)
        self.assertEqual(total, 1)
        self.assertNotIn('phone', rows[0])
        self.assertEqual(transport.request.call_args.kwargs['headers']['x-api-key'], 'test-key')
        self.assertIn('organization_locations%5B%5D=Chennai', transport.request.call_args.args[1])
        self.assertFalse(transport.request.call_args.kwargs['redirect'])
        response.close.assert_called_once()

    def test_apollo_error_does_not_expose_response(self):
        response = Mock(status=401)
        transport = Mock()
        transport.request.return_value = response
        with self.assertRaisesRegex(RuntimeError, 'API key rejected'):
            search_people('secret-key', ['Owner'], 'Chennai', transport=transport)
        response.read.assert_not_called()

    def test_unknown_audit_is_verification_task(self):
        plan = action_plan('Interior designers', {})
        self.assertTrue(all(a['evidence'] == 'Unknown' for a in plan))
        self.assertTrue(all(a['next_action'].startswith('Verify') for a in plan))


if __name__ == '__main__':
    unittest.main()
