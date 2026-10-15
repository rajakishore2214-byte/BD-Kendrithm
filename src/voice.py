"""Allowlisted voice operations; no arbitrary code, calls or messaging."""
import json
import re
import uuid
from pathlib import Path
from src.leads import AREAS, NICHES

TABS = {'agent':'My BD agent','discovery':'Local discovery','leads':'Call pipeline','apollo':'Apollo · B2B','strategy':'GBP & search strategy','website':'Website research','connections':'Connections','whatsapp':'WhatsApp outreach'}


def parse_command(text):
    text = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', str(text).casefold(), flags=re.UNICODE)
    text = ' '.join(text.split())
    if not text or len(text)>500:
        return {'action':'help'}
    if any(phrase in text for phrase in ["don t", 'do not', 'never ', 'வேண்டாம்']):
        return {'action':'unsupported'}
    if re.search(r'\b(send|dial|delete|remove|call|message|publish|approve)\b',text) and not any(p in text for p in ['call pipeline','show my calls','show calls','show messages']):
        return {'action':'unsupported'}
    if text in ['help','voice help','what can i say','உதவி']:
        return {'action':'help'}
    if any(p in text for p in ['stop mission','cancel mission','stop the mission','cancel the mission','பணியை நிறுத்து']):
        return {'action':'cancel'}
    if any(p in text for p in ['mission status','read summary','research status','show status','என்ன நிலை']):
        return {'action':'status'}

    area = next((a for words,a in [('chennai',AREAS[0]),('சென்னை',AREAS[0]),('cheyyar',AREAS[1]),('செய்யாறு',AREAS[1])] if words in text),None)
    niche_map = {'interior':'Interior designers','laminate':'Laminate sellers','veneer':'Veneer sellers','louver':'Louver sellers','plywood':'Plywood stores','education':'Education','catering':'Catering services','wedding':'Wedding venues / open gardens'}
    niche = next((v for k,v in niche_map.items() if k in text),None)
    if any(p in text for p in ['start mission','start research','start a mission','start a research mission','run mission','run research','ஆராய்ச்சியை தொடங்கு']) or ((area or niche) and any(p in text for p in ['find ','search ','discover '])):
        return {'action':'start','area':area,'niche':niche}
    if (area or niche) and any(p in text for p in ['set ','select ','choose ','focus ','use ','தேர்வு','மாற்று']):
        return {'action':'select','area':area,'niche':niche}
    aliases = {'whatsapp':'whatsapp','outreach':'whatsapp','apollo':'apollo','b2b':'apollo','strategy':'strategy','ranking':'strategy','website research':'website','connections':'connections','settings':'connections','call pipeline':'leads','leads':'leads','pipeline':'leads','discovery':'discovery','agent':'agent','முகவர்':'agent','வணிகங்கள்':'leads'}
    if any(p in text for p in ['show','open','go to','take me','பார்க்க','திற']):
        target = next((target for label,target in aliases.items() if label in text),None)
        if target:
            return {'action':'navigate','tab':TABS[target]}
    return {'action':'unsupported'}


def execute_command(command, state, enqueue_fn=None, launch_fn=None, missions_fn=None, cancel_fn=None):
    from src.agent import enqueue, launch, missions, cancel, SERVICES
    enqueue_fn,launch_fn,missions_fn,cancel_fn = enqueue_fn or enqueue,launch_fn or launch,missions_fn or missions,cancel_fn or cancel
    action = command['action']
    if action=='navigate':
        state['main_navigation']=command['tab']
        return 'Opened ' + command['tab'] + '.'
    if action=='select':
        if command.get('area'):
            state['research_area']=command['area']
            state['agent_target_areas']=[command['area']]
        if command.get('niche'):
            state['research_niche']=command['niche']
            state['agent_target_niches']=[command['niche']]
        return 'Selected ' + ', '.join(v for v in [command.get('niche'),command.get('area')] if v) + '.'
    if action=='start':
        if command.get('area'):
            state['research_area']=command['area']
            state['agent_target_areas']=[command['area']]
        if command.get('niche'):
            state['research_niche']=command['niche']
            state['agent_target_niches']=[command['niche']]
        model_file = Path(__file__).resolve().parents[1]/'data'/'agent_model.json'
        model = json.loads(model_file.read_text(encoding='utf-8-sig')) if model_file.exists() else {}
        config = dict(objective=state.get('agent_objective','Research suitable businesses and prepare evidence-based offers for Kendrithm.'),areas=state.get('agent_target_areas',AREAS),niches=state.get('agent_target_niches',list(NICHES)[:5]),services=state.get('agent_services',SERVICES),query_budget=int(state.get('agent_query_budget',2)),web_search=state.get('agent_web_search',True),inspect_sources=state.get('agent_inspect_sources',True),use_model=state.get('agent_use_model',bool(model.get('verified'))),model=state.get('agent_model_name',model.get('model','')))
        ident=enqueue_fn(config)
        launch_fn(ident)
        state['main_navigation']='My BD agent'
        return 'Started a bounded research mission for your selected markets. No calls or messages will be sent.'
    if action in ['status','cancel']:
        history=missions_fn()
        if action=='cancel':
            active=next((m for m in history if m['status'] in ['Queued','Running']),None)
            if not active:
                return 'No active mission to cancel.'
            cancel_fn(active['id'])
            return 'Cancellation requested. An in-flight tool call may finish first.'
        if not history:
            return 'No missions yet. Say start research to begin.'
        result=history[0]['result']
        return f"Latest mission: {history[0]['status']}. {len(result.get('candidates',[]))} source candidates and {len(result.get('briefs',[]))} saved lead briefs. No messages sent."
    if action=='help':
        return 'Try: show my leads; open agent; select Chennai; select plywood stores; start research; mission status; cancel mission; open WhatsApp outreach.'
    return 'Command not recognised or outside voice controls. Say help. Voice controls cannot call, send, delete or approve outreach.'


def render_voice_controls():
    import streamlit as st
    widget=_voice_component()
    with st.expander('🎙 Operate Kendrithm by voice',expanded=True):
        st.caption('Push to talk. Your browser’s speech service may process audio online. Microphone permission is requested only when you press Listen. Recognition support varies by browser; Chrome or Edge may be needed. Commands support English and a small set of Tamil phrases.')
        event=widget(data={'feedback':st.session_state.get('voice_feedback',''),'feedbackId':st.session_state.get('voice_feedback_id','')},key='voice_controls',on_command_change=lambda:None)
        payload=getattr(event,'command',None)
        if isinstance(payload,dict) and payload.get('id') and payload.get('id') != st.session_state.get('voice_processed'):
            st.session_state['voice_processed']=payload['id']
            text=str(payload.get('text',''))[:501]
            _run_command(text)
            st.rerun()
        if st.session_state.get('voice_transcript'):
            st.write('Heard: ' + st.session_state['voice_transcript'])
        if st.session_state.get('voice_feedback'):
            st.info(st.session_state['voice_feedback'])
        with st.form('typed_voice_command',clear_on_submit=True):
            text=st.text_input('Type a command if speech is unavailable',placeholder='show my leads')
            submit=st.form_submit_button('Run command')
        if submit:
            _run_command(text)
            st.rerun()
        st.caption('Examples: “select Chennai”, “select plywood stores”, “start research”, “mission status”, “show my leads”, “open WhatsApp outreach”. Say “cancel mission” to stop research; use Stop listening to stop the microphone.')


def _run_command(text):
    import streamlit as st
    st.session_state['voice_transcript']=text
    try:
        st.session_state['voice_feedback']=execute_command(parse_command(text),st.session_state)
    except (ValueError,RuntimeError,OSError) as exc:
        st.session_state['voice_feedback']=str(exc)
    st.session_state['voice_feedback_id']=str(uuid.uuid4())


def _voice_component():
    # Registration belongs to the current Streamlit runtime, including fresh sessions.
    from streamlit.components.v2 import component
    assets=Path(__file__).with_name('voice_assets')
    return component('kendrithm_voice_commands',html=assets.joinpath('control.html').read_text(encoding='utf-8-sig'),css=assets.joinpath('control.css').read_text(encoding='utf-8-sig'),js=assets.joinpath('control.js').read_text(encoding='utf-8-sig'))

