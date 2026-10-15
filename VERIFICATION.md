# Verification — 11 October 2026

- Python 3.12.10; dependencies installed in `.venv` using the available global
  installer after the initial venv pip bootstrap failed.
- `python -m compileall -q app.py src tests`: passed.
- `.venv\Scripts\python.exe -m unittest discover -s tests -v`: ten tests passed.
  Covers scoring, malformed HTML, URL rejection, private addresses, search errors,
  empty results, deduplication, timeouts, non-HTML, redirects, response size,
  pinned TLS hostname and spreadsheet-safe Unicode CSV.
- Streamlit AppTest initial dashboard rendering: passed.
- Streamlit AppTest mocked discovery button and result table: passed with a
  sixty-second test timeout. An earlier twenty-second attempt timed out during
  first result rendering. Restricted-environment startup attempts also hung;
  successful UI tests were executed with approved broader execution access.
- Live DDGS search: industrial suppliers in Chennai, three requested results;
  two deduplicated eligible candidates returned.
- Live `inspect('https://example.com/')`: HTTP 200, inspected, score 45.
  This is a connectivity smoke check, not a real prospect audit.
- Application source/playbook attribution scan: no generated-by or co-author markers.
- No sending integrations, AI API keys, database, push or deployment implemented.

Network availability varies; the live smoke checks do not guarantee future provider
availability. Browser-based visual layout review and cloud deployment remain unverified.

Start the app from this folder with:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
