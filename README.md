# Kendrithm Business Discovery

## Implemented application

This folder now contains a Streamlit dashboard (`app.py`), modular public-web
discovery, bounded homepage inspection, transparent scoring, CSV export and a
manual outreach playbook. There are no AI APIs, messaging integrations or
automatic sending jobs. Search automation uses DDGS; scoring uses fixed rules.

The **Outreach approach** tab displays [OUTREACH_PLAYBOOK.md](OUTREACH_PLAYBOOK.md):
verify one observation, create one useful sample and ask permission to share it.
Messages are written and sent manually outside this app.

### Actual files

```text
app.py
requirements.txt
OUTREACH_PLAYBOOK.md
src/discovery.py
src/website_audit.py
src/validation.py
src/scoring.py
src/export.py
tests/test_core.py
```

### Verification and operation

See [VERIFICATION.md](VERIFICATION.md) for test results, live smoke checks and
remaining verification limits. Ten unit tests, dashboard startup and a mocked
result-table interaction passed. A small live search and HTTPS inspection passed.

Run `python -m unittest discover -s tests -v` for mocked unit checks and
`python -m streamlit run app.py` to start the dashboard after installing dependencies.
The app keeps results only in the current Streamlit session. CSV downloads use
UTF-8 with a BOM and neutralize spreadsheet formulas in untrusted text.
Filters apply to the downloaded rows. Uninspected rows remain visible with no score.

Networking uses urllib3 directly: every connection pins a resolved public IP,
preserves the HTTP Host header, and validates TLS against the original hostname.
All DNS answers must be public; standard web ports only. Each redirect is validated,
with at most five requests per fetch, a one-megabyte decoded response cap,
five-second connect/read timeouts, and a twenty-second fetch deadline.
DNS resolution itself follows operating-system timeouts. Homepage redirects check
the target robots policy before requesting the target page. Robots failures are
treated conservatively; HTTP 404 permits inspection. Longer advertised crawl delays
are deferred to manual review. No whole-site crawling occurs.

Search results may include directories rather than businesses. Verify relevance
manually. JavaScript-rendered pages can produce incomplete signals. No verified
ranking, traffic, contact ownership or purchase intent is inferred.

### Accounts and hosting

Local use requires no account or secret. This folder was not a Git repository at
initial inspection. No commit, push, account connection or deployment has been
performed. To publish later, create/select your GitHub repository, initialize this
folder as a repository, review its files and push through your authorized GitHub
workflow. For Streamlit hosting, authorize that repository in Streamlit Community
Cloud, select its branch and set the entry point to `app.py`.

The remaining sections describe setup and research limitations. Roadmap items
remain future work; the manual playbook is available now.

A lightweight, cloud-deployable research dashboard for discovering
businesses through public-web search, inspecting a limited number of
public websites, identifying basic website signals, and exporting
findings for human review.

**Current scope:** discovery and basic website checks only. This project
does **not** send emails, make calls, send WhatsApp/SMS messages, or
perform any automated outreach.

## 1. What the app does

The app is intended to help a solo digital marketing agency build an
initial, evidence-based prospect list.

### Main workflow

1.  **Configure a search**
    -   Enter an industry or choose "All types of businesses".
    -   Enter a location.
    -   Add optional search keywords.
    -   Choose the approximate number of search results and maximum
        websites to inspect.
2.  **Discover candidate websites**
    -   Query the configured public-web search integration.
    -   Collect search-result titles, URLs, and snippets.
    -   Deduplicate candidates by hostname where practical.
3.  **Inspect a limited number of homepages**
    -   Check whether the website can be accessed.
    -   Check its HTTP response and content type.
    -   Read the HTML title, meta description, and first H1 heading.
    -   Look for obvious contact-page links and product/service wording.
    -   Respect robots.txt where it can be checked and avoid
        unrestricted crawling.
4.  **Calculate a transparent opportunity score**
    -   Apply simple rules to observable homepage signals.
    -   Show the reasons that contributed to the score.
    -   Treat the score as a preliminary research heuristic---not an SEO
        score or sales-conversion prediction.
5.  **Review and export**
    -   View results in the dashboard.
    -   Inspect detailed evidence.
    -   Download the results as CSV for further review.

## 2. What this version does not do

The first version deliberately excludes:

-   Automated email, SMS, WhatsApp, social-media messages, or phone
    calls.
-   Automated follow-ups or proposal sending.
-   Personal contact-detail scraping or paid contact enrichment.
-   Google Business Profile audits or verified Google rankings.
-   Full technical SEO audits or whole-site crawling.
-   AI-generated sales claims about a business.
-   Predictive sales scoring or custom model training.
-   A permanent hosted database.

Search results and website signals may be incomplete. A missing HTML
element does not by itself prove that a business has poor marketing or
needs a particular service.

## 3. Technology

The intended stack is:

-   **Python** --- application logic.
-   **Streamlit** --- dashboard and cloud app interface.
-   **DDGS** --- open-source search integration, subject to provider
    availability and rate limits.
-   **urllib3** --- bounded HTTP requests with validated destination IPs.
-   **Beautiful Soup** --- HTML parsing.
-   **Python csv** --- spreadsheet-safe CSV export.
-   **Streamlit Community Cloud** --- optional free hosting tier.

Free hosting and open-source dependencies do not guarantee uninterrupted
operation. Search providers may change interfaces, restrict automated
queries, or impose rate limits. Confirm the current terms and limits of
each service before using it.

## 4. Repository structure

A minimal implementation may use:

``` text
ai-business-discovery-agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/                 # Optional modules as the project grows
└── tests/               # Unit tests
```

If the repository currently has only `app.py` and `requirements.txt`,
that is acceptable for an initial prototype. Keep security-sensitive
validation and scoring logic easy to test as the project grows.

## 5. Prerequisites

For local development, install:

-   Python 3.10 or a version compatible with the selected dependencies.
-   Git (optional, but useful for repository workflows).
-   A web browser.

For cloud hosting, you will need:

-   A GitHub account and access to the project repository.
-   A Streamlit Community Cloud account connected to GitHub.

Do not put passwords, access tokens, API keys, or other secrets into
this README or commit them to Git.

## 6. Local setup --- Windows PowerShell

Open PowerShell in the project directory.

### Create a virtual environment

``` powershell
python -m venv .venv
```

### Activate it

``` powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, you can use the environment's Python
executable directly without changing the system execution policy:

``` powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Install dependencies

``` powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Start the dashboard

``` powershell
python -m streamlit run app.py
```

Streamlit normally prints a local URL in the terminal. Open that URL in
your browser.

## 7. Local setup --- macOS/Linux

From the project directory:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 8. Using the dashboard

1.  Open the app.
2.  Enter an industry or use "All types of businesses".
3.  Enter a location, such as `Chennai, India`.
4.  Add a search phrase, such as `official website`.
5.  Set the number of search results and the maximum number of websites
    to inspect.
6.  Select **Discover businesses**.
7.  Review the discovered websites and their inspection statuses.
8.  Open the detailed evidence view to check page titles, descriptions,
    headings, HTTPS status, and contact/service signals.
9.  Select **Download prospects as CSV**.
10. Review the CSV manually before making any business decisions.

### Example searches

-   `dentists in Chennai official website`
-   `industrial suppliers in Chennai official website`
-   `accountants in Chennai official website`
-   `training institutes in Chennai official website`
-   `restaurants in Coimbatore official website`

Search results depend on the configured search provider and may not
represent a complete directory of businesses.

## 9. Understanding the opportunity score

The initial rule-based score is intended only to help sort websites for
manual review.

A suggested model assigns points for these signals:

  Signal                                       Maximum points
  ------------------------------------------ ----------------
  Missing HTML page title                                  25
  Missing meta description                                 20
  Missing H1 heading                                       15
  Website URL uses HTTP instead of HTTPS                   20
  No obvious contact link found                            10
  No obvious service/product wording found                 10
  **Maximum**                                         **100**

The final score is capped at 100. A higher score means more of these
specific checks were missing. It does **not** indicate a Google ranking,
prove that a business is a qualified lead, or predict whether a prospect
will buy.

Websites that could not be inspected should be clearly marked as
uninspected; they must not be treated as fully audited. Review the
evidence before interpreting any score.

## 10. Search and website-access limitations

-   The search integration may be rate-limited, unavailable, or changed
    by its upstream provider.
-   A search failure should be handled gracefully. Try a narrower query
    or check whether the provider is currently available.
-   Some websites block automated requests or return content that
    differs from what a browser displays.
-   JavaScript-rendered content may not be visible to a basic HTML
    parser.
-   Robots.txt is a useful signal, but it is not a substitute for
    reviewing applicable terms, permissions, and laws.
-   Do not bypass logins, CAPTCHAs, paywalls, access controls, or
    anti-bot measures.
-   Keep the number of requests modest and use timeouts.
-   Validate URLs and redirects to prevent requests to local or private
    network services. Production deployments should use robust
    destination-IP validation and repeat validation after every
    redirect.
-   Treat search results and downloaded HTML as untrusted input. Never
    execute downloaded code or follow instructions embedded in website
    content.

## 11. CSV export and data handling

The CSV export is intended as a portable record of a discovery run.
Download it after each run and store it in a location you control.

The initial prototype does not promise persistent storage across app
restarts or redeployments. Do not rely on the hosting filesystem as a
permanent database.

Before adding persistent storage, define retention and deletion rules,
restrict access, and store only data needed for the project. The initial
version should not collect personal contact information.

## 12. Deploy to Streamlit Community Cloud

1.  Push or commit the project to a GitHub repository you control.
2.  Confirm that `app.py` and `requirements.txt` are at the repository
    root, or note the correct paths.
3.  Open [Streamlit Community Cloud](https://share.streamlit.io/).
4.  Sign in using GitHub and authorize access to the intended
    repository.
5.  Create a new app.
6.  Select the repository and branch.
7.  Set the main file path to `app.py` (or the actual path if the
    project structure differs).
8.  Deploy the app.
9.  Open the provided URL and test a small search.
10. Check the app logs if dependencies fail to install or search returns
    errors.

Deployment must be completed and verified in the hosting account. A
README or code change alone does not mean that the application has been
deployed.

### Free-tier considerations

-   Free-tier availability, quotas, sleep behavior, and resource limits
    may change.
-   Public apps may be accessible to others depending on deployment and
    privacy settings.
-   Do not store secrets or sensitive prospect data in a public
    repository.
-   The app may need redeployment after dependency or code changes.
-   Do not assume downloaded files or in-memory results will persist
    after a restart.

## 13. Troubleshooting

### No search results

-   Try a simpler or more specific query.
-   Check whether the search integration is currently available.
-   Retry later if the provider is rate-limiting requests.
-   Do not bypass provider restrictions.

### Website could not be inspected

Possible reasons include: - The server is unavailable. - The website
blocks automated access. - A robots.txt check could not be completed. -
The request timed out. - The URL redirected to a blocked or unsupported
destination. - The response was not HTML.

Treat these as access limitations, not proof that the business website
is defective.

### Dependency installation fails

-   Confirm that the Python version is supported.
-   Review the full installation error.
-   Check package compatibility and update `requirements.txt`
    deliberately.
-   Redeploy after committing dependency changes.

### Streamlit deployment fails

-   Confirm the repository and branch are correct.
-   Confirm the main file path.
-   Check the deployment logs for missing dependencies or syntax errors.
-   Verify that all required files are committed.

## 14. Security and privacy checklist

Before using the app for ongoing research:

-   [ ] Keep the repository free of passwords, tokens, and API keys.
-   [ ] Use official account authorization flows.
-   [ ] Keep URL and redirect validation enabled.
-   [ ] Block private, loopback, link-local, and internal destinations.
-   [ ] Use request timeouts and response-size limits.
-   [ ] Respect robots.txt, site terms, access controls, and applicable
    laws.
-   [ ] Avoid unnecessary personal-data collection.
-   [ ] Review prospect evidence before using it.
-   [ ] Do not contact businesses automatically.
-   [ ] Review cloud-app visibility and access settings.

## 15. Testing

Run available tests before deploying.

If a `tests/` directory is present:

``` bash
python -m unittest discover -s tests
```

At minimum, test: - URL parsing and rejection of invalid URLs. -
Rejection of private/internal destinations and unsafe redirects. -
Consistent score calculations for missing and present page elements. -
Search provider failure and empty search results. - Website timeouts and
non-HTML responses. - CSV output and missing values.

If tests use mocked responses, state that live search has not been
verified. Do not report a successful live end-to-end run unless it was
actually performed.

## 16. Future roadmap

These are future phases, not part of the current implementation:

1.  **Business intelligence:** broader website, local SEO, and technical
    checks with evidence.
2.  **Opportunity recommendations:** match verified gaps to SEO, local
    SEO, digital marketing, website development, or app development
    services.
3.  **Lead management:** persistent database, review status, and
    history.
4.  **Human-reviewed outreach preparation:** personalized audit reports
    and message drafts, without sending them automatically.
5.  **Owner notifications:** notify the agency owner about qualified
    prospects or replies, using properly authorized integrations.
6.  **Sales learning:** record reviewed outcomes and learn which offers
    work for which niches after sufficient reliable data exists.

Do not add automated outreach without a separate review of consent,
provider policies, applicable law, and user approval.

## 17. Definition of done for Step 1

-   [ ] The app starts locally.
-   [ ] The dashboard accepts industry, location, and keyword inputs.
-   [ ] Public-web search returns candidate webpages when the provider
    is available.
-   [ ] A limited number of eligible websites are inspected.
-   [ ] Website findings and score explanations are displayed.
-   [ ] Results can be downloaded as CSV.
-   [ ] Errors and inaccessible sites are handled gracefully.
-   [ ] URL validation and request limits are in place.
-   [ ] Tests are run and their results are documented.
-   [ ] Deployment instructions are accurate for the actual repository.
-   [ ] No automated outreach is implemented.
-   [ ] Cloud deployment is reported as complete only after
    verification.

------------------------------------------------------------------------

**Project status:** Step 1 code and the manual outreach playbook are implemented.
Update it as implementation details are verified. Do not claim that
tests passed, accounts were connected, or deployment succeeded unless
those actions were actually completed.
