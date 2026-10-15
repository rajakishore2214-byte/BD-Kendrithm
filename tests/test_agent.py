import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from src.agent import enqueue, missions, run_mission, cancel, decide, local_chat, brief
from src.call_prep import save_settings, settings, handoff_message
from src.leads import AREAS


def config(**overrides):
    value = dict(objective='Find suitable interior businesses',areas=AREAS,niches=['Interior designers'],services=['Website development','Lead generation'],web_search=True,query_budget=2,use_model=False,model='')
    value.update(overrides)
    return value


def record():
    return dict(id='lead-1',business_name='Example studio',niche='Interior designers',area=AREAS[0],source_url='https://example.com/',website_status='No website verified',status='Verified',call_permission='Not reviewed',phone='+919000000001')


class AgentTests(unittest.TestCase):
    def test_persistent_mission_bounded_search_and_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'agent.db'
            ident = enqueue(config(),path)
            with self.assertRaises(ValueError):
                enqueue(config(),path)
            searcher = Mock(return_value=[dict(search_title='A source',website_url='https://example.com/',search_snippet='Candidate only')])
            run_mission(ident,path,searcher=searcher,lead_reader=lambda:[record()])
            result = missions(path)[0]
            self.assertEqual(result['status'],'Needs review')
            self.assertEqual(searcher.call_count,2)
            self.assertIn(AREAS[1],searcher.call_args.args)
            self.assertEqual(len(result['result']['candidates']),1)
            self.assertEqual(result['result']['briefs'][0]['draft_engine'],'Template; no model used')
            run_mission(ident,path,searcher=searcher)
            self.assertEqual(searcher.call_count,2)
            decide(ident,'lead-1','Approved draft',path,lead_reader=lambda:[record()])
            suppressed = {**record(),'status':'Do not contact'}
            with self.assertRaises(ValueError):
                decide(ident,'lead-1','Approved draft',path,lead_reader=lambda:[suppressed])

    def test_cancel_prevents_tool_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'agent.db'
            ident = enqueue(config(),path)
            cancel(ident,path)
            searcher = Mock()
            run_mission(ident,path,searcher=searcher)
            searcher.assert_not_called()
            self.assertEqual(missions(path)[0]['status'],'Cancelled')

    def test_model_failure_is_not_reported_as_ai_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'agent.db'
            ident = enqueue(config(use_model=True,model='test-model',web_search=False),path)
            run_mission(ident,path,lead_reader=lambda:[record()],drafter=Mock(side_effect=RuntimeError('Model unavailable')))
            result = missions(path)[0]['result']
            self.assertTrue(result['issues'])
            self.assertEqual(result['briefs'][0]['draft_engine'],'Template; no model used')

    def test_model_is_local_and_cannot_supply_actions(self):
        response = Mock(status=200)
        response.read.return_value = json.dumps({'message':{'content':json.dumps(dict(offer='Offer',message='Draft',next_action='Review'))}}).encode()
        http = Mock()
        http.request.return_value = response
        result = local_chat('test-model',{'business_name':'Example'},'Objective',http)
        self.assertEqual(result['message'],'Draft')
        self.assertEqual(http.request.call_args.args[1],'http://127.0.0.1:11434/api/chat')
        response.read.return_value = b'{"message":{"content":"{\\"action\\":\\"send\\"}"}}'
        with self.assertRaises(RuntimeError):
            local_chat('test-model',{},'Objective',http)

    def test_source_inspection_is_bounded_and_not_qualification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'agent.db'
            ident = enqueue(config(query_budget=1,inspect_sources=True),path)
            hits = [dict(search_title='Candidate',website_url=f'https://example{i}.com/',search_snippet='Source') for i in range(4)]
            inspector = Mock(return_value={'inspection_status':'Inspected','page_title':'Directory'})
            run_mission(ident,path,searcher=Mock(return_value=hits),lead_reader=lambda:[],inspector=inspector)
            self.assertEqual(inspector.call_count,2)
            result = missions(path)[0]['result']
            self.assertEqual(result['briefs'],[])
            self.assertEqual(result['candidates'][0]['source_page_audit']['page_title'],'Directory')

    def test_candidate_ai_context_stays_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'agent.db'
            ident = enqueue(config(use_model=True,model='test-model',query_budget=1),path)
            searcher = Mock(return_value=[dict(search_title='Directory result',website_url='https://example.com/',search_snippet='Unverified listing')])
            drafter = Mock(return_value=dict(offer='Research hypothesis',message='Permission-first draft',next_action='Verify identity'))
            run_mission(ident,path,searcher=searcher,lead_reader=lambda:[],drafter=drafter)
            context = drafter.call_args.args[1]
            self.assertEqual(context['website_status'],'Unknown')
            self.assertEqual(context['contact_details'],'Unknown')
            self.assertEqual(missions(path)[0]['result']['briefs'],[])
            self.assertIn('suggestion',missions(path)[0]['result']['candidates'][0])

    def test_brief_and_tamil_handoff_render_end_to_end(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from src import leads
        original = leads.connection
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('src.leads.connection', side_effect=lambda *a,**k: original(root/'leads.db')), patch('src.agent.DATABASE',root/'agent.db'), patch('src.call_prep.settings',return_value={'business_phone':'919000000001','owner_phone':'919000000002'}):
                row = leads.save_lead(dict(business_name='Example studio',niche='Interior designers',area=AREAS[0],source_url='https://example.com/',website_status='No website verified',notes='Business confirmed no website',phone='+919000000001',phone_source_url='https://example.com/contact'))
                ident = enqueue(config(web_search=False))
                run_mission(ident)
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
                self.assertFalse(app.exception)
                next(w for w in app.text_area if w.label=='Client’s stated needs and relevant context').set_value('Needs a product catalogue and enquiry form')
                next(w for w in app.text_input if w.label=='Agreed callback time (IST)').set_value('Today at 2 PM IST')
                next(w for w in app.checkbox if w.label=='Client agreed to a Tamil callback and to sharing this summary with my colleague').check()
                next(w for w in app.button if w.label=='Prepare Tamil handoff').click().run()
                self.assertFalse(app.exception)
                current = leads.list_leads()[0]
                self.assertEqual(current['status'],'Callback requested')
                self.assertIn('Needs a product catalogue',current['notes'])
                self.assertIn('Preferred language: Tamil',current['notes'])

    def test_private_contacts_and_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'private.json'
            save_settings('9000000001','9000000002',path)
            self.assertEqual(settings(path)['owner_phone'],'919000000002')
            with self.assertRaises(ValueError):
                handoff_message('Example','','','')
            text = handoff_message('Example','+919000000001','Wants a product catalogue','Tomorrow at 11 AM IST')
            self.assertIn('Preferred language: Tamil',text)
            self.assertIn('Wants a product catalogue',text)
            self.assertNotIn('message sent',text.lower())



