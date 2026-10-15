from pathlib import Path
import streamlit as st
from src.discovery import discover
from src.website_audit import inspect
from src.export import export_csv

def render_web_desk():
    st.info('Research and manual outreach planning only. This app never sends messages.')
    with st.container():
        st.header('Find your next prospects')
        with st.form('search'):
            industry = st.text_input('Industry', 'All types of businesses', max_chars=150)
            location = st.text_input('Location', 'Chennai, India', max_chars=150)
            keywords = st.text_input('Search keywords', 'official website', max_chars=200)
            limit = st.slider('Search results', 1, 30, 10)
            inspect_limit = st.slider('Websites to inspect', 0, 10, 5)
            submitted = st.form_submit_button('Discover businesses', type='primary')
    research, outreach = st.tabs(['Discovery desk', 'Outreach approach'])
    if submitted:
        with research:
            try:
                with st.spinner('Searching public websites…'):
                    rows = discover(industry, location, keywords, limit)
                progress = st.progress(0, text='Inspecting limited homepages')
                count = min(inspect_limit, len(rows))
                for index in range(count):
                    rows[index].update(inspect(rows[index]['website_url']))
                    progress.progress((index + 1) / count)
                progress.empty()
                st.session_state['rows'] = rows
                if not rows:
                    st.warning('No eligible websites returned. Try a narrower query.')
            except (ValueError, RuntimeError) as exc:
                st.session_state['rows'] = []
                st.error(str(exc))
    with research:
        rows = st.session_state.get('rows', [])
        if rows:
            a, b, c = st.columns(3)
            a.metric('Discovered websites', len(rows))
            b.metric('Inspected', sum(r['inspection_status'] == 'Inspected' for r in rows))
            c.metric('Awaiting review', len(rows))
            statuses = st.multiselect('Inspection status', sorted({r['inspection_status'] for r in rows}))
            threshold = st.slider('Minimum score for inspected websites', 0, 100, 0)
            filtered = [r for r in rows if (not statuses or r['inspection_status'] in statuses)
                        and (r.get('opportunity_score') is None or r['opportunity_score'] >= threshold)]
            filtered.sort(key=lambda r: (r.get('opportunity_score') is not None, r.get('opportunity_score') or 0), reverse=True)
            st.caption('Score counts missing homepage signals. It does not predict buying interest. Uninspected sites have no score.')
            st.dataframe([{k: r.get(k) for k in ['search_title', 'website_url', 'inspection_status', 'opportunity_score', 'observed_issues']} for r in filtered],
                         column_config={'website_url': st.column_config.LinkColumn('Website')}, hide_index=True, width='stretch')
            for r in filtered:
                with st.expander(r['search_title'] or r['website_url']):
                    st.json(r)
            st.download_button('Download prospects as CSV', export_csv(filtered), 'business_discovery_results.csv', 'text/csv')
        else:
            st.subheader('Build an evidence-based prospect list')
            st.write('Choose an industry and location in the sidebar. Start with five websites, then verify each finding in your browser before selecting a prospect.')
    with outreach:
        st.markdown((Path(__file__).resolve().parents[1] / 'OUTREACH_PLAYBOOK.md').read_text(encoding='utf-8'))
    


