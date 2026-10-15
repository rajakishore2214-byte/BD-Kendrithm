from pathlib import Path
import os
import streamlit as st
from src.leads import AREAS, NICHES, STATUSES, WEBSITE, FIELDS, list_leads, save_lead, call_ready, research_links, lead_csv, preview_import
from src.apollo import search_people
from src.strategy import CHECKS, action_plan, niche_offer

st.set_page_config(page_title='Kendrithm | Personal BD Agent', page_icon='◎', layout='wide')
st.title('Kendrithm · Personal BD Agent')
st.caption('Find a business. Verify the opportunity. Reach the right person.')
with st.sidebar:
    st.header('Your market')
    area = st.selectbox('Research area', AREAS)
    niche = st.selectbox('Business niche', list(NICHES))
    st.caption('Start with interiors and material dealers; expand after measuring call-to-meeting results.')
    st.divider()
    st.caption('Local lead records persist on this computer. API keys and lead data are excluded from Git.')

agent_desk, research, pipeline, b2b, strategy, website, setup, outreach_html = st.tabs(['My BD agent', 'Local discovery', 'Call pipeline', 'Apollo · B2B', 'GBP & search strategy', 'Website research', 'Connections', 'WhatsApp outreach'])

with research:
    st.subheader('Find businesses with no listed website')
    st.write(f'Current focus: **{niche}** in **{area}**. Offer: {niche_offer(niche)}.')
    a, b = st.columns(2)
    links = research_links(niche, area)
    a.link_button('Research Google Maps profiles', links['Google Maps'])
    b.link_button('Cross-check business web presence', links['Google Search'])
    st.caption('Research links open Google. Automatic Google Maps extraction is not connected. Use independently sourced business contacts or a provider licensed for CRM use. No website listed is a lead signal, not proof that a website does not exist.')
    with st.expander('Add a verified source record', expanded=True):
        with st.form('add_lead', clear_on_submit=True):
            business_name = st.text_input('Business name')
            address = st.text_input('Branch address / locality')
            source_url = st.text_input('Record source URL', help='Business-owned page, directory or licensed provider record that supports this lead.')
            profile_url = st.text_input('Google Business Profile URL (optional reference)')
            source_type = st.selectbox('Source type', ['Manual research', 'Business-owned publication', 'Licensed provider', 'Business confirmed'])
            c1, c2 = st.columns(2)
            phone = c1.text_input('Public business phone')
            phone_source_url = c2.text_input('Business phone evidence URL')
            whatsapp = c1.text_input('Explicitly listed WhatsApp number (optional)')
            whatsapp_source_url = c2.text_input('WhatsApp evidence URL (optional)')
            website_url = st.text_input('Website URL (leave empty when unknown / not listed)')
            website_status = st.selectbox('Website evidence', WEBSITE)
            notes = st.text_area('Verification notes', help='Record when and how you checked the website and contact details.')
            add = st.form_submit_button('Save lead', type='primary')
        if add:
            try:
                save_lead(dict(business_name=business_name, niche=niche, area=area, address=address, source_url=source_url, profile_url=profile_url, source_type=source_type, phone=phone, phone_source_url=phone_source_url, whatsapp=whatsapp, whatsapp_source_url=whatsapp_source_url, website_url=website_url, website_status=website_status, notes=notes))
                st.success('Lead saved. Review calling eligibility in the pipeline.')
            except ValueError as exc:
                st.error(str(exc))
    with st.expander('Import business contacts from CSV'):
        st.download_button('Download blank CSV template', lead_csv([]), 'kendrithm_lead_template.csv', 'text/csv')
        upload = st.file_uploader('Lead CSV', type=['csv'])
        rights = st.checkbox('These records are independently sourced or licensed for storage and outreach.')
        if upload:
            try:
                valid, errors = preview_import(upload.getvalue())
                st.write(f'{len(valid)} valid records · {len(errors)} rows need correction')
                st.dataframe(valid, hide_index=True)
                for error in errors[:20]:
                    st.error(error)
                if st.button('Import reviewed rows', disabled=not rights or not valid or bool(errors)):
                    for row in valid:
                        save_lead(row)
                    st.success(f'Imported {len(valid)} rows; duplicates merged and suppression retained.')
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))

with pipeline:
    st.subheader('Manual business calling desk')
    rows = list_leads()
    a, b, c = st.columns(3)
    a.metric('Saved businesses', len(rows))
    b.metric('Ready for business call', sum(call_ready(r) for r in rows))
    c.metric('Meetings booked', sum(r['status'] == 'Meeting booked' for r in rows))
    scope = st.checkbox('Only the selected niche and area', value=True)
    ready_only = st.checkbox('Only call-ready businesses')
    filtered = [r for r in rows if (not scope or (r['niche'] == niche and r['area'] == area)) and (not ready_only or call_ready(r))]
    st.dataframe([{k:r[k] for k in ['business_name','niche','area','phone','whatsapp','website_status','status','follow_up']} for r in filtered], hide_index=True, width='stretch')
    st.download_button('Export visible leads', lead_csv(filtered), 'kendrithm_leads.csv', 'text/csv')
    if filtered:
        selected_id = st.selectbox('Review a business', [r['id'] for r in filtered], format_func=lambda ident: next(r['business_name'] + ' · ' + r['address'] for r in filtered if r['id'] == ident))
        row = next(r for r in filtered if r['id'] == selected_id)
        st.write(f"**Phone:** {row['phone'] or 'Not available'} · **WhatsApp:** {row['whatsapp'] or 'Not verified'}")
        for label, field in [('Record source','source_url'),('Phone source','phone_source_url'),('WhatsApp source','whatsapp_source_url'),('Profile','profile_url')]:
            if row[field]:
                st.link_button(label, row[field])
        st.info('Opening: “Hello, I’m calling from Kendrithm. Do you handle marketing or enquiries for the business? Is this a suitable time for a brief business call?” Verify the website observation before pitching. Ask permission before any WhatsApp follow-up.')
        with st.form('update_' + selected_id):
            new_status = st.selectbox('Call outcome', STATUSES, index=STATUSES.index(row['status']))
            permissions = ['Not reviewed', 'Cleared for business call', 'Do not contact']
            permission = st.selectbox('Calling eligibility', permissions, index=permissions.index(row['call_permission']), help='Clear only after checking the business contact, applicable calling rules and opt-out status.')
            new_website = st.selectbox('Website verification', WEBSITE, index=WEBSITE.index(row['website_status']))
            new_website_url = st.text_input('Confirmed website URL', row['website_url'])
            follow_up = st.text_input('Agreed callback date/time (IST)', row['follow_up'])
            notes_update = st.text_area('Call notes and verification evidence', row['notes'])
            contact_name = st.text_input('Business contact name', row['contact_name'])
            contact_title = st.text_input('Business contact role', row['contact_title'])
            update = st.form_submit_button('Save review')
        if update:
            try:
                save_lead({**row, 'status':new_status,'call_permission':permission,'website_status':new_website,'website_url':new_website_url,'follow_up':follow_up,'notes':notes_update,'contact_name':contact_name,'contact_title':contact_title})
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if row['status'] == 'Do not contact':
            st.warning('Suppressed. This contact will stay suppressed on reimport, including matching telephone numbers.')
    else:
        st.write('Save or import a business to start your call queue.')

with b2b:
    st.subheader('Find the business decision-maker')
    st.write('Use company location, business keywords and job titles. Apollo search may show obfuscated names and contact-availability flags; it does not reveal phone numbers or email addresses.')
    with st.form('apollo_search'):
        titles_text = st.text_input('Job titles (comma separated)', NICHES[niche][2])
        company_location = st.text_input('Company headquarters location', area)
        business_keywords = st.text_input('Business keywords', NICHES[niche][0])
        page = st.number_input('Results page', min_value=1, max_value=500, value=1)
        search = st.form_submit_button('Search Apollo', type='primary')
    if search:
        key = os.environ.get('APOLLO_API_KEY', '')
        if not key:
            try:
                key = st.secrets.get('APOLLO_API_KEY', '')
            except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
                pass
        try:
            with st.spinner('Finding matching decision-makers…'):
                people, total = search_people(key, titles_text.split(','), company_location, business_keywords, int(page))
            st.session_state['apollo_results'] = people
            st.session_state['apollo_total'] = total
            st.success(f'{len(people)} prospects returned; {total} reported matches.')
        except (ValueError, RuntimeError) as exc:
            st.session_state.pop('apollo_results', None)
            st.error(str(exc))
    if 'apollo_results' in st.session_state:
        st.dataframe(st.session_state['apollo_results'], hide_index=True, width='stretch')
        st.caption('Search results stay in this session. Enrichment, CRM sync and sending are not connected.')
    st.link_button('Apollo API setup', 'https://docs.apollo.io/docs/create-api-key')

with strategy:
    st.subheader('Build visibility around real business evidence')
    st.write(f'**{niche}:** {niche_offer(niche)}.')
    st.caption('Google Maps/local pack and organic website results are separate measurements. No rank is measured by this app.')
    with st.form('gbp_audit'):
        business = st.text_input('Business being audited')
        evidence = {label: st.selectbox(label, ['Unknown', 'Needs work', 'Verified complete'], key='audit_' + label) for label in CHECKS}
        audit_notes = st.text_area('Evidence URLs, owner confirmation and audit date')
        plan = st.form_submit_button('Create action plan')
    if plan:
        actions = action_plan(niche, evidence)
        st.session_state['audit_plan'] = {'business':business, 'area':area, 'niche':niche, 'evidence':audit_notes, 'actions':actions}
    if 'audit_plan' in st.session_state:
        audit = st.session_state['audit_plan']
        st.write(f"Plan for **{audit['business'] or 'Unnamed business'}** · {audit['niche']} · {audit['area']}")
        st.dataframe(audit['actions'], hide_index=True, width='stretch')
        report = f"# Local visibility plan: {audit['business']}\n\nArea: {audit['area']}\nNiche: {audit['niche']}\nEvidence: {audit['evidence']}\n\n" + '\n\n'.join(f"- {a['check']} [{a['evidence']}] — {a['phase']}: {a['next_action']}" for a in audit['actions'])
        st.download_button('Download audit plan', report, 'local_visibility_plan.md', 'text/markdown')
    st.markdown('''**Days 1–14:** verify the profile and contact details; document baseline visibility and enquiries; fix evidenced information gaps.

**Days 15–45:** publish original project or product evidence, complete relevant services, build useful website pages and establish honest review requests.

**Days 46–90:** compare qualified enquiries and bookings against baseline. Repeat the same searches from the same locations; record query, date, location, Maps/local-pack position and organic position separately. Treat listing position changes as observations, not proof of causation.

**Interior network:** interior designers ↔ material dealers ↔ contractors. Track the buyer's role and actual project requirements. For education use course enquiries; for catering use menu/tasting enquiries; for wedding gardens use site visits and availability enquiries.''')
    st.link_button('Google local ranking guidance', 'https://support.google.com/business/answer/7091')

with website:
    from src.web_desk import render_web_desk
    render_web_desk()

with setup:
    st.subheader('Connections and local storage')
    st.markdown('''**Apollo:** set `APOLLO_API_KEY` in `.streamlit/secrets.toml` or the server environment. Restart after changing environment variables. API eligibility depends on your account. No key is bundled with the app.

**Google Business Profiles:** research links are available. Google profile scraping, Places-to-CRM exports and owner profile changes are not connected. A licensed lead source must explicitly support storing contacts for this workflow; an API key alone does not establish those rights.

**Contacts:** the local SQLite database is `data/leads.sqlite3`. It persists across app restarts and is excluded from Git. Back it up privately. CSV exports contain business contact information. WhatsApp is recorded only with explicit evidence; a telephone number alone does not prove WhatsApp availability.

**Calls:** this version provides a manual call queue, outcome tracking and durable do-not-contact suppression. It does not dial, send messages, enrich contact details or run scheduled follow-ups.''')
    st.link_button('Google Maps data-use terms', 'https://cloud.google.com/maps-platform/terms')
    st.link_button('Apollo search reference', 'https://docs.apollo.io/reference/people-api-search')

with outreach_html:
    from src.outreach import render_outreach_tab
    render_outreach_tab()


with agent_desk:
    from src.agent_ui import render_agent_desk
    render_agent_desk()


