# Kendrithm Personal BD Agent

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

## WhatsApp outreach HTML

The WhatsApp outreach tab accepts CSV files using its downloadable template. It filters verified website absence and verified absent or inactive social presence, requires evidence checked within 30 days, and defaults to a 90-day inactivity window. It does not crawl or independently verify social media. Saved opt-outs are excluded. The HTML export contains Business Name, Phone Number and Open WhatsApp buttons with URL-encoded personalized draft messages. The original message and a shorter permission-first option are editable. Opening a link does not send the message or verify WhatsApp membership.


## Personal BD agent

The **My BD agent** desk starts a separate background worker for a bounded mission. Each mission records its objective, selected markets/niches/services, progress events, candidate sources, saved-lead briefs and review decisions in the ignored `data/agent.sqlite3` database. Runs continue when switching tabs while the computer remains on. This is an on-demand worker, not a scheduled or always-on service.

A mission executes at most four public-web search queries, five results per query, reviews at most five saved leads and makes at most three local-model calls for those briefs (or two candidate suggestions when no saved leads exist). Search results remain unverified candidates and never establish website absence, inactive social media or contact ownership. A workflow priority score is not a conversion prediction. Approvals do not send messages. Failed model calls retain clearly labelled template drafts.

Local AI uses Ollama at `http://127.0.0.1:11434/api/chat`, non-streaming structured output and a 2,048-token context setting. The selected lightweight model is Qwen3 1.7B. Model-generated recommendations remain suggestions requiring evidence review. Web content cannot issue tool actions; the worker chooses from fixed research tools. Without a connected model, the worker uses rules and templates and labels this explicitly.

Business and owner handoff contacts are private local settings in `data/agent_contacts.json`; real numbers are not bundled with the repository. Manual call preparation uses a professional opening and discovery questions. When a client agrees to a Tamil callback, the operator records their needs and agreed time; the worker prepares an owner WhatsApp draft and saves callback notes. No outbound calling, automatic WhatsApp delivery, voice agent, call recording or paid telephony service is connected.


### Free local model setup

Install Ollama from its official Windows distribution, then download the model:

```powershell
ollama pull qwen3:1.7b
```

Run Ollama with local-only settings if its background app is not already running:

```powershell
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
ollama serve
```

Enter `qwen3:1.7b` in the agent's model settings and enable local suggestions. This uses local inference rather than a paid API. Runtime/model downloads, storage and computer resources are still required. The worker rejects cloud-labelled model names. Installation binaries, weights, local model settings, contacts and research records are excluded from Git.

The supplied desktop setup was checked with approximately 8 GB RAM and a 4 GB discrete Radeon GPU. The live structured-output adapter test completed in about 10 seconds; performance and output quality vary. Human review remains necessary, particularly for unverified directory search results.

## Operate by voice

Use the expanded **Operate Kendrithm by voice** control at the top. Press **Listen for a command**, grant microphone permission and speak one command. Stop listening ends microphone capture. Optional spoken feedback uses the browser's speech synthesis. English (India) and Tamil recognition settings are available; the command grammar supports English and selected Tamil phrases, rather than unrestricted conversation.

Examples: `show my leads`, `open WhatsApp outreach`, `select Chennai`, `select plywood stores`, `find plywood stores in Cheyyar`, `start research`, `mission status`, `cancel mission`, and `help`. Research uses the current mission settings and fixed worker limits. Voice cannot dial, send messages, delete records or approve outreach. Transcripts and feedback appear in the current session. The command is processed once per recognition event.

Speech recognition uses the browser's Web Speech service, which may process audio online and may require Chrome or Edge. Browser/API availability does not guarantee a working speech backend in an embedded browser. Clear error messages and a typed-command fallback are provided. The local Qwen model and all existing model storage remain on D:. No new speech model download or paid speech API is configured.
