# naukri-auto-update

This repository contains a Playwright-based automation script for:

- logging in to Naukri
- searching jobs based on saved local attributes
- applying to matching jobs automatically

## Files

- `save_session.py` - saves a browser session to `auth.json` after manual login
- `apply_naukri_jobs.py` - locates Recommended Jobs, prints a markdown table, and saves results to JSON
- `list_saved_jobs.py` - prints a markdown table from a saved jobs JSON file (no browser needed)
- `job_filter.json` - local criteria for experience, skills, tools, and other filters
- `auth.json` - optional saved session state (not checked in automatically)

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
playwright install
```

2. Save your Naukri session:

```bash
python save_session.py
```

   Log in manually in the browser window, then press ENTER to save `auth.json`.

3. Update `job_filter.json` with your desired experience, skills, tools, locations, and keywords.

4. Run the automation:

```bash
python apply_naukri_jobs.py
```

This prints a markdown table and saves:

- `recommended_jobs_apply_classification.json`
- `recommended_jobs_direct_apply.json`
- `recommended_jobs_apply_on_site.json`

To print the saved files later:

```bash
python list_saved_jobs.py recommended_jobs_apply_classification.json
```

## Notes

- If `auth.json` exists, the script will use it to avoid re-login.
- If `auth.json` is missing, the script will use `NAUKRI_EMAIL` and `NAUKRI_PASSWORD` from environment variables and save a new `auth.json`.
- The selectors may need adjustment if Naukri changes page structure. Update `apply_naukri_jobs.py` as needed.

