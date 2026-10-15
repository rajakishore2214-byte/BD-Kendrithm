"""Private local contact settings and manual call handoff preparation."""
import json
from pathlib import Path
from urllib.parse import quote
from src.outreach import international_number

SETTINGS = Path(__file__).resolve().parents[1] / 'data' / 'agent_contacts.json'


def settings(path=None):
    target = Path(path or SETTINGS)
    return json.loads(target.read_text(encoding='utf-8-sig')) if target.exists() else {'business_phone':'','owner_phone':''}


def save_settings(business_phone, owner_phone, path=None):
    value = {'business_phone':international_number(business_phone),'owner_phone':international_number(owner_phone)}
    target = Path(path or SETTINGS)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value),encoding='utf-8')


def handoff_message(name, phone, needs, callback, language='Tamil', waiting_now=False):
    if not needs.strip() or not callback.strip():
        raise ValueError('Record the client’s needs and agreed callback time first')
    phone = '+' + international_number(phone)
    availability = 'Client confirmed they are waiting for your call now.' if waiting_now else 'Callback agreed; use the stated time.'
    return f"Kendrithm call handoff\nBusiness: {name}\nClient phone: {phone or 'Not recorded'}\nPreferred language: {language}\nClient needs: {needs.strip()}\nAgreed callback (IST): {callback.strip()}\nClient status: {availability}\nAction: Please call the client at the agreed time."


def render_call_preparation(item, mission_id):
    import streamlit as st
    from src.leads import list_leads, save_lead
    contacts = settings()
    lead = next((r for r in list_leads() if r['id']==item['lead_id']),None)
    if not lead:
        return
    st.markdown('**Professional call preparation**')
    st.write('“Hello, this is Kishore from Kendrithm. May I speak with the person who handles business enquiries or marketing? Is now a convenient time for a brief business call?”')
    st.write('“We help businesses with websites, lead generation and performance marketing. Before I suggest anything, how are most new enquiries reaching you today, and what would you most like to improve?”')
    st.write('Ask about their priority, current enquiry process, who decides and a suitable next step. Listen before discussing an offer. Do not promise results or claim an unverified gap.')
    st.write('If they prefer Tamil: “Certainly. I can ask my colleague to call you in Tamil. May I share your business requirements and number with him, and what time would suit you?”')
    st.caption('Manual calls only. Use your own phone to call; the agent does not dial or record conversations.')
    if contacts['business_phone']:
        st.write('Kendrithm business contact: +' + contacts['business_phone'])
    suffix = mission_id + item['lead_id']
    with st.form('handoff_'+suffix):
        needs = st.text_area('Client’s stated needs and relevant context')
        callback = st.text_input('Agreed callback time (IST)')
        waiting_now = st.checkbox('Client explicitly confirmed they are waiting for a call now')
        permission = st.checkbox('Client agreed to a Tamil callback and to sharing this summary with my colleague')
        prepared = st.form_submit_button('Prepare Tamil handoff')
    if prepared:
        try:
            current = next((r for r in list_leads() if r['id']==item['lead_id']), None)
            if not current or current['status'] in ['Do not contact','Not interested','Won'] or current['call_permission']=='Do not contact':
                raise ValueError('This lead is no longer eligible for follow-up')
            if not permission:
                raise ValueError('Confirm the client’s agreed callback before preparing a handoff')
            message = handoff_message(current['business_name'], current['phone'], needs, callback, waiting_now=waiting_now)
            save_lead({**current,'status':'Callback requested','follow_up':callback,'notes':current['notes']+'\n'+message})
            st.session_state['handoff_result_'+suffix] = message
        except ValueError as exc:
            st.error(str(exc))
    if 'handoff_result_'+suffix in st.session_state:
        message = st.session_state['handoff_result_'+suffix]
        st.code(message,language=None)
        if contacts['owner_phone']:
            st.link_button('Open owner WhatsApp handoff draft', 'https://wa.me/'+contacts['owner_phone']+'?text='+quote(message,safe=''))
            st.caption('Opens a draft addressed to your saved owner contact. Review and send it yourself. No notification has been sent automatically.')
        else:
            st.info('Save your owner contact below to prepare a WhatsApp link.')


def render_contact_settings():
    import streamlit as st
    contact = settings()
    with st.expander('Private calling and Tamil handoff contacts'):
        with st.form('agent_private_contacts'):
            business = st.text_input('Kendrithm business phone with country code', contact['business_phone'])
            owner = st.text_input('Owner’s Tamil callback / handoff number with country code', contact['owner_phone'])
            saved = st.form_submit_button('Save private contacts')
        if saved:
            try:
                save_settings(business,owner)
                st.success('Saved locally. These numbers are excluded from Git.')
            except ValueError as exc:
                st.error(str(exc))
        st.caption('Contact configuration does not register a WhatsApp Business sender or enable outbound calling.')


