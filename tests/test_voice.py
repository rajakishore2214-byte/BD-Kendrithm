import unittest
from unittest.mock import Mock
from src.voice import parse_command,execute_command
from src.leads import AREAS


class VoiceTests(unittest.TestCase):
    def test_navigation_and_market_commands(self):
        state={}
        execute_command(parse_command('show my leads'),state)
        self.assertEqual(state['main_navigation'],'Call pipeline')
        execute_command(parse_command('select Chennai and plywood stores'),state)
        self.assertEqual(state['agent_target_areas'],[AREAS[0]])
        self.assertEqual(state['agent_target_niches'],['Plywood stores'])
        self.assertEqual(parse_command('open WhatsApp outreach')['tab'],'WhatsApp outreach')
        self.assertEqual(parse_command('find plywood stores in Cheyyar'), {'action':'start','area':AREAS[1],'niche':'Plywood stores'})
        self.assertEqual(parse_command('சென்னை தேர்வு')['area'],AREAS[0])

    def test_start_is_bounded_and_uses_selected_settings(self):
        enqueue,launch=Mock(return_value='job-1'),Mock()
        state={'agent_target_areas':[AREAS[1]],'agent_target_niches':['Plywood stores'],'agent_query_budget':1}
        feedback=execute_command(parse_command('start research'),state,enqueue_fn=enqueue,launch_fn=launch)
        config=enqueue.call_args.args[0]
        self.assertEqual(config['query_budget'],1)
        self.assertEqual(config['areas'],[AREAS[1]])
        launch.assert_called_once_with('job-1')
        self.assertIn('No calls or messages',feedback)

    def test_external_actions_and_negations_are_not_executed(self):
        for text in ['send WhatsApp message','call this business','delete leads',"don't start research",'do not start mission','approve outreach','start mission then send a message']:
            self.assertEqual(parse_command(text)['action'],'unsupported',text)

    def test_cancel_targets_only_active_mission(self):
        cancel=Mock()
        execute_command(parse_command('cancel mission'),{},missions_fn=lambda:[{'id':'finished','status':'Needs review'},{'id':'running','status':'Running'}],cancel_fn=cancel)
        cancel.assert_called_once_with('running')

    def test_wake_word_and_dictated_objective(self):
        self.assertEqual(parse_command('Kendrithm, show my leads')['tab'],'Call pipeline')
        command=parse_command('Set my mission to Find plywood stores and prepare professional call briefs')
        state={}
        execute_command(command,state)
        self.assertEqual(state['agent_objective'],'Find plywood stores and prepare professional call briefs')

    def test_spoken_service_selection(self):
        state={}
        execute_command(parse_command('select services website development and performance marketing'),state)
        self.assertEqual(state['agent_services'],['Website development','Performance marketing'])
    def test_typed_voice_path_navigates_and_selects(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        next(w for w in app.text_input if w.label=='Type a command if speech is unavailable').set_value('select Cheyyar')
        app.button(key='FormSubmitter:typed_voice_command-Run command').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['research_area'],AREAS[1])
        next(w for w in app.text_input if w.label=='Type a command if speech is unavailable').set_value('show my leads')
        app.button(key='FormSubmitter:typed_voice_command-Run command').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['main_navigation'],'Call pipeline')


