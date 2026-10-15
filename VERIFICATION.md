# Verification — 15 October 2026

## Passed in this workspace

- 21 automated tests: existing website/network/export tests; lead validation; unknown vs absent website; explicit WhatsApp evidence; persistence and deduplication; durable opt-out suppression; CSV import review reset; mocked Apollo requests and errors; evidence-based planning.
- Streamlit integration test: load dashboard, save a source-backed lead, clear it for a call, generate an audit plan and suppress the contact. Test records use a temporary database.
- Missing Apollo key displays a setup instruction without crashing.
- Local dashboard served at http://127.0.0.1:8501 and was inspected in the browser.

The existing virtual environment points at a missing Python installation. Validation and the current server use the bundled Python 3.12 runtime with the existing dependency directory. A fresh checkout should create its own virtual environment following README.md.

## Not verified / not connected

- No live Apollo request: no configured account key was supplied for this task. API access, real result quality and account eligibility remain unverified.
- No live business leads collected, called or messaged in this task.
- No Google Maps scraper, Google Places lead exporter, owner-profile API edits or live rank tracker.
- No automatic contact enrichment, dialler, WhatsApp sending, campaigns or scheduled follow-ups.
- Google API access alone does not establish storage/export rights. Connect a source licensed for the intended lead workflow before automated acquisition.
- Call clearance is a user review state, not automated verification of calling permissions.
- Ranking plans are based on user-entered evidence. Unknown fields stay verification tasks; no rank prediction or guarantee.
- Local database has no multi-user access control; server binds to loopback.

## Outreach HTML update

24 automated tests passed, including HTML escaping, exact message URL-encoding round trip, India number normalization, absent/inactive filtering, stale/unknown/active exclusions and saved contact suppression. CSV upload is supported; Excel files must first be exported as CSV. No actual source file or live social verification was supplied for this update.


## Personal agent update

29 automated tests pass for the initial agent implementation, covering persistent mission state, one-worker claims, bounded queries, cancellation, saved-lead review decisions, local-model schema validation, model-failure labelling, private contacts and callback summaries. Existing UI workflow tests also pass with mission history present.

A real independent worker searched interior designers in Chennai and Cheyyar and saved seven public-web source candidates. Some are directory results. There were no eligible saved lead records, so no qualified-lead briefs were produced. No call, WhatsApp message or notification was sent. Local-model installation and live inference are tracked separately and must be verified before reporting AI availability.

The expanded suite now has 33 passing tests, including bounded source-page inspection, model analysis preserving unknown facts, international/local telephone suppression and an end-to-end saved-lead brief → Tamil callback summary test. A form-state conflict found by that integration test was corrected. Manual-call preparation and WhatsApp owner draft generation are implemented; automatic delivery remains disconnected.

## Live local-model verification

Ollama 0.40.4 was installed from the digitally signed official Ollama Inc. installer. Qwen3 1.7B was downloaded and verified by the runtime. A direct local structured-output test completed in approximately 9.5 seconds. Cloud features are disabled in the local runtime configuration; the agent also rejects cloud-labelled model names.

The complete independent worker was then exercised with two public-web queries, two bounded source-page inspections and local-model suggestions. The latest successful run saved eight web candidates and two model-generated research suggestions. It had no eligible saved business records and produced no qualified-lead briefs. Directory sources remain unverified and model suggestions require human review. No outbound call, WhatsApp message, automatic owner alert or external AI API call was made.

An earlier full run encountered a model connection failure while the service was being separated from its installer. That failed model attempt is retained in mission history; the later successful run is the verified result. Private contacts and real mission data remain outside version control.
