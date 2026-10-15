"""Evidence-filtered, escaped HTML outreach exports."""
import csv
import io
import re
from datetime import date, timedelta
from html import escape
from urllib.parse import quote

COLUMNS = ['business_name', 'phone', 'whatsapp', 'website_url', 'website_status', 'website_evidence_url', 'social_status', 'social_evidence_url', 'social_last_post_date', 'checked_at', 'status']
MESSAGE = "Hi, this is kishore. I came across {Business Name} and it looks like you have really good potential. But I noticed there's not much online presence right now. With a small setup using Instagram and ads, you can attract more local customers. If you're open, I can share a quick idea for {Business Name}."
SHORT_MESSAGE = "Hi, this is Kishore from Kendrithm. I came across {Business Name} while researching local businesses. Would it be useful if I shared one practical idea for presenting your work online and making local enquiries easier? If this isn't relevant, let me know and I won't follow up."


def template_csv():
    output = io.StringIO()
    csv.writer(output).writerow(COLUMNS)
    return output.getvalue().encode('utf-8-sig')


def international_number(value, country='91'):
    value = str(value or '').strip().lstrip("'")
    if re.search(r'[^+\d\s().-]', value):
        raise ValueError('Invalid phone characters')
    digits = re.sub(r'\D', '', value)
    if value.startswith('00'):
        digits = digits[2:]
    elif not value.startswith('+') and country == '91' and len(digits) == 10:
        digits = '91' + digits
    if not 8 <= len(digits) <= 15 or digits.startswith('0'):
        raise ValueError('Use a complete international phone number')
    return digits


def filter_contacts(data, inactive_days=90, freshness_days=30, today=None, suppressed=()):
    if len(data) > 2_000_000:
        raise ValueError('Upload a CSV smaller than 2 MB')
    today = today or date.today()
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    required = {'business_name', 'phone', 'website_status', 'website_evidence_url', 'social_status', 'social_evidence_url', 'checked_at'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Use the template headers: ' + ', '.join(sorted(required)))
    blocked = set()
    for number in suppressed:
        try:
            blocked.add(international_number(number))
        except ValueError:
            pass
    selected, excluded, seen = [], [], set()
    from src.validation import normalize_url
    for index, raw in enumerate(reader, 2):
        if index > 501:
            raise ValueError('Upload at most 500 businesses')
        row = {k: str(raw.get(k, '') or '').strip() for k in COLUMNS}
        try:
            if not row['business_name']:
                raise ValueError('Missing business name')
            if row['status'].lower() in ['do not contact', 'not interested']:
                raise ValueError('Contact suppressed')
            if row['website_url'] or row['website_status'].lower() != 'no website verified':
                raise ValueError('No-website status must be verified; blank or unlisted is insufficient')
            normalize_url(row['website_evidence_url'])
            normalize_url(row['social_evidence_url'])
            checked = date.fromisoformat(row['checked_at'])
            if not today - timedelta(days=freshness_days) <= checked <= today:
                raise ValueError('Evidence check is stale or in the future')
            state = row['social_status'].lower()
            if state == 'inactive verified':
                last_post = date.fromisoformat(row['social_last_post_date'])
                if last_post > checked - timedelta(days=inactive_days):
                    raise ValueError('Social media was active inside the selected inactivity period')
            elif state != 'no profiles verified':
                raise ValueError('Social media absence or inactivity must be verified')
            number = international_number(row['whatsapp'] or row['phone'])
            phone = international_number(row['phone']) if row['phone'] else number
            if number in blocked or phone in blocked:
                raise ValueError('Number is in your saved suppression list')
            if number in seen:
                raise ValueError('Duplicate recipient number')
            seen.add(number)
            row['recipient'] = number
            row['phone'] = '+' + phone
            selected.append(row)
        except (ValueError, TypeError) as exc:
            excluded.append({'row': index, 'business_name': row['business_name'], 'reason': str(exc)})
    return selected, excluded


def render_html(rows, message=MESSAGE):
    table_rows = []
    for row in rows:
        text = message.replace('{Business Name}', row['business_name'])
        recipient = international_number(row['recipient'])
        url = 'https://wa.me/' + recipient + '?text=' + quote(text, safe='')
        table_rows.append('<tr><td>' + escape(row['business_name']) + '</td><td>' + escape(row['phone']) + '</td><td><a class="button" target="_blank" rel="noopener noreferrer" href="' + escape(url, quote=True) + '">Open WhatsApp</a></td></tr>')
    return '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Business Outreach</title>
<style>body{font-family:Arial,sans-serif;background:#f5f7fa;color:#172033;margin:0;padding:32px}main{max-width:1100px;margin:auto;background:white;padding:24px;border-radius:12px;overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:16px;border-bottom:1px solid #e2e8f0}th{background:#eef3f8}.button{display:inline-block;background:#137b3b;color:white;text-decoration:none;padding:10px 16px;border-radius:6px;white-space:nowrap}.button:focus,.button:hover{background:#0b5c2b}</style></head><body><main><table><thead><tr><th scope="col">Business Name</th><th scope="col">Phone Number</th><th scope="col">WhatsApp Button</th></tr></thead><tbody>''' + ''.join(table_rows) + '</tbody></table></main></body></html>'


def render_outreach_tab():
    import streamlit as st
    from src.leads import list_leads
    st.subheader('Filter a lead file and create WhatsApp outreach HTML')
    st.write('Include only businesses with verified absence of a website and verified absent or inactive social media. Unknown information is excluded.')
    st.download_button('Download outreach CSV template', template_csv(), 'outreach_template.csv', 'text/csv')
    with st.expander('File fields and verification'):
        st.write('Use website_status = No website verified. Use social_status = No profiles verified or Inactive verified. Supply evidence URLs and checked_at in YYYY-MM-DD format; inactive profiles also need social_last_post_date. Verify all relevant profiles, not just one account. Evidence checks must be within the last 30 days. Local 10-digit Indian numbers receive country code 91; other numbers must include their country code.')
        st.caption('The file supplies the evidence; this tool does not independently inspect websites or social profiles. A phone number does not establish WhatsApp availability or permission to message.')
    upload = st.file_uploader('Upload outreach CSV', type=['csv'], key='outreach_csv')
    inactive_days = st.number_input('Social inactivity window (days)', min_value=30, max_value=730, value=90)
    choice = st.radio('Message format', ['Your original message', 'Short permission-first message'])
    message = st.text_area('Editable message · {Business Name} inserts the business name', MESSAGE if choice == 'Your original message' else SHORT_MESSAGE, height=150)
    if upload:
        try:
            from datetime import datetime, timezone
            today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
            suppressed = [number for r in list_leads() if r['status'] in ['Do not contact', 'Not interested'] or r['call_permission'] == 'Do not contact' for number in [r['phone'], r['whatsapp']] if number]
            selected, excluded = filter_contacts(upload.getvalue(), int(inactive_days), today=today, suppressed=suppressed)
            st.write(f'{len(selected)} eligible businesses · {len(excluded)} excluded')
            st.dataframe([{k:r[k] for k in ['business_name', 'phone', 'social_status']} for r in selected], hide_index=True)
            if excluded:
                with st.expander('Excluded records and reasons'):
                    st.dataframe(excluded, hide_index=True)
            if not message.strip():
                st.error('Enter a message before generating HTML.')
            elif selected:
                html = render_html(selected, message)
                st.download_button('Download HTML outreach table', html, 'business_outreach.html', 'text/html', type='primary')
                with st.expander('Preview generated HTML code'):
                    st.code(html, language='html')
        except (ValueError, UnicodeError) as exc:
            st.error(str(exc))
    st.markdown('''**Outreach strategy:** verify one specific observation, offer one relevant sample, then ask permission to share it. For designers, use a project showcase; for material dealers, a product enquiry page; for catering and venues, an event enquiry example. Avoid unsupported claims about the business.

**Measure the funnel:** delivered messages → replies → qualified enquiries → booked meetings → customers. Track each denominator separately. Test a small reviewed batch with the original and shorter message; compare qualified enquiries before increasing volume. A 30% result is a hypothesis to measure, not a promised conversion rate.

**Follow-up:** agree on the next step and channel. Honour opt-outs in the call pipeline. Opening WhatsApp prepares a draft; you review and send it yourself.''')
