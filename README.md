# Kendrithm Business Discovery Network

A local Streamlit workspace for business research, manual calling and evidence-based local visibility plans.

## Initial markets

Chennai and Cheyyar (Tiruvannamalai district), Tamil Nadu.

Priority niches: interior designers, laminate dealers, veneer dealers, louver dealers and plywood stores. Additional niches: education, catering services and outdoor wedding venues / open gardens.

## Workflows

- Local discovery: niche/area research links, manual source-backed lead entry, and reviewed CSV import (up to 500 records / 2 MB).
- Lead records: public business phone and source, explicitly evidenced WhatsApp, branch address, profile reference, website evidence, call outcome, callback notes and contact role.
- Website states distinguish unknown, no website listed, verified absence and an existing website. No website listed does not prove absence.
- Call pipeline: local SQLite persistence, filters, CSV export and durable do-not-contact suppression across duplicate records and matching phone numbers. Imports reset calling clearance for review. Clearing a business for calls is a human determination, not a compliance check performed by the app.
- Apollo: API-backed decision-maker search by title, company HQ location and keywords, with pagination. Contact availability is not contact disclosure. Phone/email enrichment and sending are not connected.
- GBP and search strategy: evidence checklist, downloadable action plan, niche offers and a 90-day programme. Unknown observations create verification tasks. No live ranking collection or rank guarantees.
- Website research: existing bounded homepage inspection and spreadsheet-safe export.

## Run

Python 3.12 is recommended. Create a working virtual environment and install the pinned dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501. Bind to loopback for local use; this application has no multi-user authentication.

## API setup

Copy the following into `.streamlit/secrets.toml` locally:

```toml
APOLLO_API_KEY = "your-key"
```

Alternatively set `APOLLO_API_KEY` in the server environment. Never commit a real key. Apollo endpoint access depends on account eligibility and key permissions. Search uses `POST /api/v1/mixed_people/api_search`, returns up to 25 records per page and does not retrieve email addresses or telephone numbers. Error responses and credentials are not displayed or stored.

Google research links are available; Google Maps scraping, Places API lead exports, and owner profile management are not connected. Google Maps Platform terms restrict extraction and storage for external use. Use business-owned publications or a lead provider whose licence explicitly permits the intended CRM workflow. A Google API key alone does not grant export rights.

## Data

`data/leads.sqlite3` stores lead records locally and is ignored by Git. Keep backups privately. Exported CSVs contain business contact data and protect spreadsheet formulas. All records require source URLs; phone and WhatsApp fields require evidence URLs. WhatsApp availability is never inferred from a phone number. No contact is called or messaged automatically.

Import requires `business_name,niche,area,source_url`; download the complete template from the app. Use one of the exact niche and area options shown in the UI. Include the country code when known. Duplicate matching uses business name + area + branch address; different branches remain separate.

## Verification

```powershell
python -m unittest discover -s tests -v
```

See VERIFICATION.md for the actual validation scope and remaining connection requirements.

## Strategy references

- [Google local ranking guidance](https://support.google.com/business/answer/7091): relevance, distance and prominence; maintain accurate information and useful business evidence.
- [Google Maps Platform terms](https://cloud.google.com/maps-platform/terms)
- [Places data policies](https://developers.google.com/maps/documentation/places/web-service/policies)
- [Apollo People API Search](https://docs.apollo.io/reference/people-api-search)

Maps/local-pack results and organic website rankings are separate. Measure location and query consistently, alongside qualified calls, enquiries and booked meetings. No top-position promise is made.
