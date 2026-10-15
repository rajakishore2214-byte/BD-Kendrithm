"""Owner-facing mission desk for the personal BD worker."""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import urllib3
import streamlit as st
from src.agent import SERVICES, enqueue, launch, missions, activity, cancel, decide, decisions
from src.leads import AREAS, NICHES


def render_agent_desk():
    model_file = Path(__file__).resolve().parents[1] / 'data' / 'agent_model.json'
    model_config = json.loads(model_file.read_text(encoding='utf-8-sig')) if model_file.exists() else {}
    st.subheader('Kishore’s personal business development desk')
    st.write('Give Kendrithm a mission. The worker searches for candidates, reviews saved leads, proposes a relevant service and prepares outreach drafts for your decision.')
    a,b,c = st.columns(3)
    a.metric('Research worker', 'Ready')
    b.metric('AI brain', 'Configured locally' if model_config.get('verified') or st.session_state.get('local_model_names') else model_config.get('status','Needs connection'))
    c.metric('Sending', 'Not connected')
    st.caption('Current authority: research and prepare drafts. Approval records your decision; it does not place a call or send a message. Background runs continue if you switch tabs, while this computer stays on.')
    st.session_state.setdefault('agent_target_areas', AREAS)
    st.session_state.setdefault('agent_target_niches', list(NICHES)[:5])
    with st.form('agent_mission'):
        objective = st.text_area('What should your BD agent achieve?', 'Find interior designers and material dealers in Chennai and Cheyyar, verify their business fit, and prepare useful offers for website development, lead generation and performance marketing.', key='agent_objective')
        areas = st.multiselect('Agent target areas', AREAS, key='agent_target_areas')
        niches = st.multiselect('Agent target niches', list(NICHES), key='agent_target_niches')
        services = st.multiselect('Services to sell', SERVICES, default=SERVICES, key='agent_services')
        with st.expander('Research and model settings'):
            web_search = st.checkbox('Find new candidates through public-web search', value=True, key='agent_web_search')
            inspect_sources = st.checkbox('Inspect up to two candidate source pages',value=True, key='agent_inspect_sources')
            budget = st.slider('Maximum search queries this run', 1, 4, 2, key='agent_query_budget')
            st.caption('Up to five search results per query. Search results are candidates, not verified businesses without websites. Each run drafts for at most five saved businesses.')
            use_model = st.checkbox('Use my local Ollama model to write personalized suggestions', value=bool(model_config.get('verified')), key='agent_use_model')
            model = st.text_input('Exact installed Ollama model name', value=model_config.get('model',''), placeholder='Enter the model installed on this computer', key='agent_model_name')
            st.caption('Local inference uses 127.0.0.1:11434. Without a connected model, the worker uses explicit rules and templates; no AI reasoning is claimed. The objective guides draft context; selected markets, services and query budgets control tool execution.')
        run = st.form_submit_button('Start agent mission', type='primary')
    if run:
        try:
            ident = enqueue(dict(objective=objective,areas=areas,niches=niches,services=services,query_budget=budget,web_search=web_search,inspect_sources=inspect_sources,use_model=use_model,model=model))
            launch(ident)
            st.success('Worker started. Refresh mission progress below to see results.')
        except (ValueError,RuntimeError) as exc:
            st.error(str(exc))
    with st.expander('Professional call approach'):
        st.write('Hello, this is Kishore from Kendrithm. May I speak with the person who handles business enquiries or marketing? Is this a convenient time for a brief business call?')
        st.write('How do new customers usually find you, and what would you like to improve: your website, enquiry quality or marketing results? Listen, confirm the need, and ask for a suitable next step.')
        st.write('For a Tamil callback: ask permission to share the business requirements and contact number with your colleague, confirm a time, then prepare the handoff from the business brief.')
    with st.expander('Connect the agent’s AI brain'):
        st.write('Run Ollama locally and install a model suitable for your computer. Enter its exact model name above, then enable local-model suggestions. The worker sends only the mission objective and selected brief facts to the local model. Model output remains an unverified draft and cannot execute tools or send outreach.')
        st.link_button('Ollama setup', 'https://ollama.com/download')
        if st.button('Check installed local models'):
            http = urllib3.PoolManager()
            response = None
            try:
                response = http.request('GET','http://127.0.0.1:11434/api/tags',redirect=False,retries=False,preload_content=False,timeout=urllib3.Timeout(connect=2,read=3))
                payload = response.read(200001)
                if response.status != 200 or len(payload)>200000:
                    raise ValueError('Model listing unavailable')
                names = [m['name'] for m in json.loads(payload).get('models',[])]
                st.session_state['local_model_names'] = names
                st.rerun()
            except (urllib3.exceptions.HTTPError, ValueError, KeyError, TypeError):
                st.session_state['local_model_names'] = []
                st.info('No usable Ollama connection found at 127.0.0.1:11434.')
            finally:
                if response is not None:
                    response.close()
                http.clear()
    from src.call_prep import render_contact_settings
    render_contact_settings()
    if st.session_state.get('local_model_names'):
        st.caption('Available local models: ' + ', '.join(st.session_state['local_model_names']))
    render_mission_progress()


@st.fragment(run_every=5.0)
def render_mission_progress():
    st.divider()
    st.subheader('Mission history and decisions')
    st.button('Refresh mission progress')
    history = missions()
    if not history:
        st.write('No missions yet. Start a bounded research mission above. No scheduled runs are configured.')
        return
    ident = st.selectbox('Mission', [m['id'] for m in history], format_func=lambda x: next(datetime.fromisoformat(m['created_at']).astimezone(timezone(timedelta(hours=5,minutes=30))).strftime('%d %b %Y %H:%M IST') + ' · ' + m['status'] + ' · ' + m['config']['objective'][:65] for m in history if m['id']==x))
    mission = next(m for m in history if m['id']==ident)
    st.write('**Status:** ' + mission['status'])
    st.caption('Mission and callback times are shown in IST.')
    if mission['status'] in ['Queued','Running','Cancel requested']:
        st.info('Worker is active. Refresh for new progress. Cancellation is checked between tool calls; an in-flight request finishes first.')
        if st.button('Cancel this mission', disabled=mission['status']=='Cancel requested'):
            cancel(ident)
            st.rerun()
    logs = activity(ident)
    for entry in logs:
        entry['time'] = datetime.fromisoformat(entry['time']).astimezone(timezone(timedelta(hours=5,minutes=30))).strftime('%d %b %Y %H:%M:%S IST')
    if logs:
        st.dataframe(logs, hide_index=True, width='stretch')
    result = mission['result']
    a,b,c = st.columns(3)
    a.metric('Source candidates',len(result.get('candidates',[])))
    b.metric('Saved lead briefs',len(result.get('briefs',[])))
    c.metric('Messages sent',0)
    for issue in result.get('issues',[]):
        st.warning(issue)
    candidates = result.get('candidates',[])
    if candidates:
        with st.expander(f'{len(candidates)} discovered web candidates · verification needed',expanded=not result.get('briefs')):
            st.dataframe([{k:v for k,v in candidate.items() if k not in ['suggestion','suggestion_engine','source_page_audit']} for candidate in candidates], column_config={'url':st.column_config.LinkColumn('Source')}, hide_index=True, width='stretch')
            for candidate in candidates:
                if candidate.get('source_page_audit'):
                    st.write('**Source page evidence · ' + candidate['title'] + '**')
                    st.json(candidate['source_page_audit'])
                if candidate.get('suggestion'):
                    st.write('**Candidate suggestion · ' + candidate['title'] + '**')
                    st.write(candidate['suggestion'])
                    st.caption(candidate['suggestion_engine'])
            st.write('Review the source, establish the business identity and capture contact evidence in Local discovery. Search results never establish website absence or inactive social media.')
    saved = decisions(ident)
    for item in result.get('briefs',[]):
        with st.expander(item['business_name'] + ' · ' + item['service'], expanded=True):
            st.write(f"**Why review this business:** {item['reason']}")
            st.caption(f"{item['niche']} · {item['area']} · Workflow priority {item['priority']}/100; not a conversion prediction")
            st.link_button('Review lead evidence',item['source_url'])
            st.write('**Still needs evidence:** ' + '; '.join(item['missing_evidence']))
            st.write('**Offer hypothesis:** ' + item['draft']['offer'])
            st.text_area('Outreach draft',item['draft']['message'],disabled=True,key='draft_'+ident+item['lead_id'])
            st.write('**Next action:** ' + item['draft']['next_action'])
            from src.call_prep import render_call_preparation
            render_call_preparation(item, ident)
            st.caption(item['draft_engine'] + ' · Decision: ' + saved.get(item['lead_id'],'Pending review'))
            a,b = st.columns(2)
            approve = a.button('Approve draft',key='approve_'+ident+item['lead_id'])
            reject = b.button('Reject draft',key='reject_'+ident+item['lead_id'])
            if approve or reject:
                try:
                    decide(ident,item['lead_id'],'Approved draft' if approve else 'Rejected')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    if result:
        st.download_button('Download mission report',json.dumps(mission,indent=2,ensure_ascii=False),'agent_mission.json','application/json')








