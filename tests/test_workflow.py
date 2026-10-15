import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src import leads


class WorkflowTests(unittest.TestCase):
    def test_lead_save_review_and_audit(self):
        original = leads.connection
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'workflow.db'
            with patch('src.leads.connection', side_effect=lambda *a, **k: original(path)):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
                self.assertFalse(app.exception)
                values = {'Business name':'Workflow Example', 'Record source URL':'https://example.com/about', 'Public business phone':'+919000000002', 'Business phone evidence URL':'https://example.com/contact'}
                for widget in app.text_input:
                    if widget.label in values:
                        widget.set_value(values[widget.label])
                next(w for w in app.selectbox if w.label == 'Website evidence').set_value('No website listed')
                app.button(key='FormSubmitter:add_lead-Save lead').click().run()
                self.assertFalse(app.exception)
                self.assertEqual(len(leads.list_leads(path)), 1)
                next(w for w in app.selectbox if w.label == 'Calling eligibility').set_value('Cleared for business call')
                next(w for w in app.button if w.label == 'Save review').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(leads.call_ready(leads.list_leads(path)[0]))
                app.button(key='FormSubmitter:gbp_audit-Create action plan').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(app.session_state['audit_plan']['actions'])
                next(w for w in app.selectbox if w.label == 'Call outcome').set_value('Do not contact')
                next(w for w in app.button if w.label == 'Save review').click().run()
                self.assertFalse(app.exception)
                self.assertFalse(leads.call_ready(leads.list_leads(path)[0]))

    def test_missing_apollo_key_is_actionable(self):
        with patch.dict('os.environ', {'APOLLO_API_KEY':''}), patch('streamlit.secrets', {'APOLLO_API_KEY':''}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
            app.button(key='FormSubmitter:apollo_search-Search Apollo').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('APOLLO_API_KEY' in e.value for e in app.error))

