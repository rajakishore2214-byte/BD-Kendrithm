import csv
import io

FIELDS = ['search_title', 'website_url', 'search_snippet', 'search_query', 'discovered_at',
          'inspection_status', 'http_status', 'final_url', 'page_title', 'meta_description',
          'h1', 'https', 'contact_signal', 'contact_links', 'service_signal', 'service_terms',
          'opportunity_score', 'observed_issues', 'evidence_notes']


def export_csv(rows: list[dict]) -> bytes:
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        safe = {}
        for key in FIELDS:
            value = row.get(key, '')
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            safe[key] = value
        writer.writerow(safe)
    return output.getvalue().encode('utf-8-sig')
